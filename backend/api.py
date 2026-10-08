from flask import Flask, jsonify
from flask_cors import CORS

import traci
import os
import atexit
import threading


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# SUMO CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)


SUMO_CONFIG = os.path.join(
    BASE_DIR,
    "simulation",
    "Network",
    "network.sumocfg"
)


# ------------------------------------------------------------
# SUMO executable
# ------------------------------------------------------------

SUMO_BINARY = (
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
)


# ============================================================
# GLOBAL SUMO STATE
# ============================================================

sumo_running = False


# ------------------------------------------------------------
# IMPORTANT
#
# TraCI should not be accessed by multiple Flask requests
# simultaneously.
#
# This lock prevents:
#
# React request 1
# React request 2
# React request 3
#
# from accessing SUMO at exactly the same time.
# ------------------------------------------------------------

sumo_lock = threading.RLock()


# ============================================================
# NETWORK CACHE
# ============================================================

cached_network = None


# ============================================================
# START SUMO
# ============================================================

def start_sumo():

    global sumo_running

    with sumo_lock:

        # ----------------------------------------------------
        # Already running?
        # ----------------------------------------------------

        if sumo_running:

            return True


        # ----------------------------------------------------
        # Check SUMO config
        # ----------------------------------------------------

        if not os.path.exists(SUMO_CONFIG):

            raise FileNotFoundError(
                "SUMO configuration file not found:\n"
                + SUMO_CONFIG
            )


        # ----------------------------------------------------
        # Check SUMO executable
        # ----------------------------------------------------

        if not os.path.exists(SUMO_BINARY):

            raise FileNotFoundError(
                "SUMO executable not found:\n"
                + SUMO_BINARY
            )


        print()
        print("=" * 70)
        print("              RESQROUTE SUMO BACKEND")
        print("=" * 70)

        print()
        print("Starting SUMO...")
        print()

        print("SUMO CONFIG:")
        print(SUMO_CONFIG)

        print()

        print("SUMO BINARY:")
        print(SUMO_BINARY)

        print()


        # ----------------------------------------------------
        # START SUMO
        # ----------------------------------------------------

        traci.start(
            [
                SUMO_BINARY,

                "-c",
                SUMO_CONFIG,

                # Reduce unnecessary SUMO console output
                "--no-step-log",
                "true",

                # Don't write unnecessary warnings
                "--duration-log.disable",
                "true",
            ]
        )


        sumo_running = True


        print()
        print("SUMO CONNECTED SUCCESSFULLY")
        print()


        return True


# ============================================================
# CLOSE SUMO
# ============================================================

def close_sumo():

    global sumo_running

    with sumo_lock:

        if not sumo_running:

            return


        try:

            traci.close(False)

        except Exception:

            pass


        sumo_running = False


        print()
        print("SUMO CLOSED")
        print()


# ============================================================
# CLOSE SUMO WHEN PYTHON EXITS
# ============================================================

atexit.register(close_sumo)


# ============================================================
# HELPER
# ============================================================

def ensure_sumo():

    if not sumo_running:

        start_sumo()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return jsonify({

        "success": True,

        "message":
            "ResQRoute backend is running",

        "sumoRunning":
            sumo_running

    })


# ============================================================
# BUILD NETWORK CACHE
#
# This runs ONLY ONCE after SUMO starts.
#
# React doesn't have to rebuild the entire network every time
# it asks for /api/network.
# ============================================================

def build_network_cache():

    global cached_network


    with sumo_lock:

        ensure_sumo()


        # ----------------------------------------------------
        # If already cached, return immediately
        # ----------------------------------------------------

        if cached_network is not None:

            return cached_network


        print()
        print("=" * 70)
        print("BUILDING SUMO NETWORK CACHE")
        print("=" * 70)
        print()


        # ====================================================
        # JUNCTIONS
        # ====================================================

        all_junction_ids = (
            traci.junction.getIDList()
        )


        junctions = []

        main_junctions = []


        for junction_id in all_junction_ids:

            # ------------------------------------------------
            # Ignore internal SUMO junctions
            # ------------------------------------------------

            if junction_id.startswith(":"):

                continue


            try:

                x, y = (
                    traci.junction
                    .getPosition(
                        junction_id
                    )
                )


                # --------------------------------------------
                # Detect J1-J16
                # --------------------------------------------

                is_main_junction = (

                    junction_id.startswith("J")

                    and
                    junction_id[1:].isdigit()

                    and
                    1 <= int(
                        junction_id[1:]
                    ) <= 16

                )


                junction_data = {

                    "id":
                        junction_id,

                    "x":
                        float(x),

                    "y":
                        float(y),

                    "isMainJunction":
                        is_main_junction

                }


                junctions.append(
                    junction_data
                )


                if is_main_junction:

                    main_junctions.append(
                        junction_data
                    )


            except Exception as e:

                print(
                    "JUNCTION ERROR:",
                    junction_id,
                    e
                )


        # ----------------------------------------------------
        # Sort J1, J2, J3...
        # ----------------------------------------------------

        main_junctions.sort(

            key=lambda item:
                int(
                    item["id"][1:]
                )

        )


        # ====================================================
        # ROADS
        # ====================================================

        edge_ids = (
            traci.edge.getIDList()
        )


        roads = []


        for edge_id in edge_ids:

            # ------------------------------------------------
            # Ignore SUMO internal edges
            # ------------------------------------------------

            if edge_id.startswith(":"):

                continue


            try:

                # --------------------------------------------
                # REAL FROM JUNCTION
                # --------------------------------------------

                from_junction = (

                    traci.edge
                    .getFromJunction(
                        edge_id
                    )

                )


                # --------------------------------------------
                # REAL TO JUNCTION
                # --------------------------------------------

                to_junction = (

                    traci.edge
                    .getToJunction(
                        edge_id
                    )

                )


                if not from_junction:

                    continue


                if not to_junction:

                    continue


                # --------------------------------------------
                # LANE COUNT
                # --------------------------------------------

                lane_count = 0


                try:

                    lane_count = int(

                        traci.edge
                        .getLaneNumber(
                            edge_id
                        )

                    )

                except Exception:

                    lane_count = 0


                # --------------------------------------------
                # FIRST LANE
                # --------------------------------------------

                first_lane_id = (

                    f"{edge_id}_0"

                )


                # --------------------------------------------
                # LENGTH
                # --------------------------------------------

                length_meters = 0.0


                try:

                    length_meters = float(

                        traci.lane
                        .getLength(
                            first_lane_id
                        )

                    )

                except Exception:

                    length_meters = 0.0


                # --------------------------------------------
                # SPEED LIMIT
                # --------------------------------------------

                speed_limit_ms = 0.0


                try:

                    speed_limit_ms = float(

                        traci.lane
                        .getMaxSpeed(
                            first_lane_id
                        )

                    )

                except Exception:

                    speed_limit_ms = 0.0


                # --------------------------------------------
                # ROAD SHAPE
                # --------------------------------------------

                shape = []


                try:

                    lane_shape = (

                        traci.lane
                        .getShape(
                            first_lane_id
                        )

                    )


                    shape = [

                        {

                            "x":
                                float(point[0]),

                            "y":
                                float(point[1])

                        }

                        for point in lane_shape

                    ]


                except Exception:

                    shape = []


                # --------------------------------------------
                # ROAD OBJECT
                # --------------------------------------------

                road_data = {

                    "id":
                        edge_id,

                    "fromJunction":
                        from_junction,

                    "toJunction":
                        to_junction,

                    "laneCount":
                        lane_count,

                    "lengthMeters":
                        round(
                            length_meters,
                            2
                        ),

                    "speedLimitMs":
                        round(
                            speed_limit_ms,
                            2
                        ),

                    "speedLimitKmh":
                        round(
                            speed_limit_ms * 3.6,
                            2
                        ),

                    "shape":
                        shape

                }


                roads.append(
                    road_data
                )


            except Exception as e:

                print(
                    "ROAD ERROR:",
                    edge_id,
                    e
                )


        # ====================================================
        # TRAFFIC LIGHTS
        # ====================================================

        traffic_light_ids = (

            traci.trafficlight
            .getIDList()

        )


        traffic_lights = []


        for tls_id in traffic_light_ids:

            try:

                x = None

                y = None


                # --------------------------------------------
                # Try junction position
                # --------------------------------------------

                try:

                    x, y = (

                        traci.junction
                        .getPosition(
                            tls_id
                        )

                    )

                except Exception:

                    pass


                # --------------------------------------------
                # If no junction position,
                # use controlled lane shape.
                # --------------------------------------------

                if (
                    x is None
                    or
                    y is None
                ):

                    try:

                        controlled_lanes = (

                            traci.trafficlight
                            .getControlledLanes(
                                tls_id
                            )

                        )


                        if controlled_lanes:

                            first_lane = (
                                controlled_lanes[0]
                            )


                            lane_shape = (

                                traci.lane
                                .getShape(
                                    first_lane
                                )

                            )


                            if lane_shape:

                                x, y = (
                                    lane_shape[-1]
                                )


                    except Exception:

                        pass


                # --------------------------------------------
                # Signal state
                # --------------------------------------------

                try:

                    signal_state = (

                        traci.trafficlight
                        .getRedYellowGreenState(
                            tls_id
                        )

                    )

                except Exception:

                    signal_state = ""


                # --------------------------------------------
                # Current phase
                # --------------------------------------------

                try:

                    phase = (

                        traci.trafficlight
                        .getPhase(
                            tls_id
                        )

                    )

                except Exception:

                    phase = 0


                # --------------------------------------------
                # Phase duration
                # --------------------------------------------

                try:

                    phase_duration = (

                        traci.trafficlight
                        .getPhaseDuration(
                            tls_id
                        )

                    )

                except Exception:

                    phase_duration = 0.0


                # --------------------------------------------
                # Next switch
                # --------------------------------------------

                try:

                    next_switch = (

                        traci.trafficlight
                        .getNextSwitch(
                            tls_id
                        )

                    )

                except Exception:

                    next_switch = 0.0


                # --------------------------------------------
                # Controlled lanes
                # --------------------------------------------

                try:

                    controlled_lanes = list(

                        set(

                            traci
                            .trafficlight
                            .getControlledLanes(
                                tls_id
                            )

                        )

                    )

                except Exception:

                    controlled_lanes = []


                # --------------------------------------------
                # Controlled links
                # --------------------------------------------

                try:

                    controlled_links = (

                        traci
                        .trafficlight
                        .getControlledLinks(
                            tls_id
                        )

                    )


                    controlled_link_count = (

                        len(
                            controlled_links
                        )

                        if controlled_links

                        else 0

                    )

                except Exception:

                    controlled_link_count = 0


                # --------------------------------------------
                # STATE SUMMARY
                # --------------------------------------------

                state_lower = (

                    signal_state.lower()

                    if signal_state

                    else ""

                )


                if "y" in state_lower:

                    state_summary = "yellow"

                elif "g" in state_lower:

                    state_summary = "green"

                else:

                    state_summary = "red"


                # --------------------------------------------
                # TRAFFIC LIGHT OBJECT
                # --------------------------------------------

                traffic_light_data = {

                    "id":
                        tls_id,

                    "junctionId":
                        tls_id,

                    "x":
                        float(x)
                        if x is not None
                        else None,

                    "y":
                        float(y)
                        if y is not None
                        else None,

                    "state":
                        signal_state,

                    "stateSummary":
                        state_summary,

                    "phase":
                        phase,

                    "phaseDuration":
                        round(
                            phase_duration,
                            2
                        ),

                    "nextSwitch":
                        round(
                            next_switch,
                            2
                        ),

                    "controlledLanes":
                        controlled_lanes,

                    "controlledLaneCount":
                        len(
                            controlled_lanes
                        ),

                    "controlledLinkCount":
                        controlled_link_count

                }


                traffic_lights.append(
                    traffic_light_data
                )


            except Exception as e:

                print(
                    "TRAFFIC LIGHT ERROR:",
                    tls_id,
                    e
                )


        # ====================================================
        # FINAL NETWORK CACHE
        # ====================================================

        cached_network = {

            "success":
                True,

            "junctions":
                junctions,

            "roads":
                roads,

            "mainJunctions":
                main_junctions,

            "mainJunctionCount":
                len(main_junctions),

            "junctionCount":
                len(junctions),

            "roadCount":
                len(roads),

            "trafficLights":
                traffic_lights,

            "trafficLightCount":
                len(traffic_lights)

        }


        print()
        print("=" * 70)
        print("SUMO NETWORK CACHE READY")
        print("=" * 70)

        print(
            "JUNCTIONS      :",
            len(junctions)
        )

        print(
            "ROADS          :",
            len(roads)
        )

        print(
            "TRAFFIC LIGHTS :",
            len(traffic_lights)
        )

        print("=" * 70)
        print()


        return cached_network


# ============================================================
# NETWORK API
#
# IMPORTANT:
#
# This no longer starts SUMO during route calculation.
#
# SUMO was already started when api.py started.
#
# ============================================================

@app.get("/api/network")
def get_network():

    try:

        network = build_network_cache()


        return jsonify(
            network
        )


    except Exception as e:

        print()
        print("NETWORK ERROR:")
        print(e)
        print()


        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# LIVE TRAFFIC DATA
# ============================================================

@app.get("/api/traffic")
def get_traffic():

    try:

        with sumo_lock:

            ensure_sumo()


            # ------------------------------------------------
            # ADVANCE SUMO BY ONE STEP
            #
            # This is what makes traffic and signals change.
            # ------------------------------------------------

            traci.simulationStep()


            # ------------------------------------------------
            # Current simulation time
            # ------------------------------------------------

            simulation_time = (

                traci.simulation
                .getTime()

            )


            # ------------------------------------------------
            # Traffic lights
            # ------------------------------------------------

            traffic_light_ids = (

                traci.trafficlight
                .getIDList()

            )


            traffic_data = []


            for junction_id in traffic_light_ids:

                try:

                    # ----------------------------------------
                    # CONTROLLED LANES
                    # ----------------------------------------

                    controlled_lanes = list(

                        set(

                            traci
                            .trafficlight
                            .getControlledLanes(
                                junction_id
                            )

                        )

                    )


                    # ----------------------------------------
                    # Counters
                    # ----------------------------------------

                    vehicle_count = 0

                    queue_length = 0

                    total_speed = 0.0

                    speed_count = 0


                    # ----------------------------------------
                    # LANE DATA
                    # ----------------------------------------

                    for lane_id in controlled_lanes:

                        try:

                            vehicle_count += (

                                traci.lane
                                .getLastStepVehicleNumber(
                                    lane_id
                                )

                            )


                            queue_length += (

                                traci.lane
                                .getLastStepHaltingNumber(
                                    lane_id
                                )

                            )


                            speed = (

                                traci.lane
                                .getLastStepMeanSpeed(
                                    lane_id
                                )

                            )


                            if speed > 0:

                                total_speed += speed

                                speed_count += 1


                        except Exception:

                            continue


                    # ----------------------------------------
                    # Average speed
                    # ----------------------------------------

                    average_speed = (

                        total_speed
                        /
                        speed_count

                        if speed_count > 0

                        else 0.0

                    )


                    # ----------------------------------------
                    # Signal phase
                    # ----------------------------------------

                    try:

                        signal_phase = (

                            traci
                            .trafficlight
                            .getPhase(
                                junction_id
                            )

                        )

                    except Exception:

                        signal_phase = 0


                    # ----------------------------------------
                    # Signal state
                    # ----------------------------------------

                    try:

                        signal_state = (

                            traci
                            .trafficlight
                            .getRedYellowGreenState(
                                junction_id
                            )

                        )

                    except Exception:

                        signal_state = ""


                    # ----------------------------------------
                    # State summary
                    # ----------------------------------------

                    state_lower = (

                        signal_state.lower()

                        if signal_state

                        else ""

                    )


                    if "y" in state_lower:

                        state_summary = "yellow"

                    elif "g" in state_lower:

                        state_summary = "green"

                    else:

                        state_summary = "red"


                    # ----------------------------------------
                    # Phase duration
                    # ----------------------------------------

                    try:

                        phase_duration = (

                            traci
                            .trafficlight
                            .getPhaseDuration(
                                junction_id
                            )

                        )

                    except Exception:

                        phase_duration = 0.0


                    # ----------------------------------------
                    # Next switch
                    # ----------------------------------------

                    try:

                        next_switch = (

                            traci
                            .trafficlight
                            .getNextSwitch(
                                junction_id
                            )

                        )

                    except Exception:

                        next_switch = 0.0


                    # ----------------------------------------
                    # TRAFFIC OBJECT
                    # ----------------------------------------

                    traffic_data.append({

                        "junctionId":
                            junction_id,

                        "vehicleCount":
                            vehicle_count,

                        "queueLength":
                            queue_length,

                        "averageSpeed":
                            round(
                                average_speed,
                                2
                            ),

                        "averageSpeedKmh":
                            round(
                                average_speed * 3.6,
                                2
                            ),

                        "signalPhase":
                            signal_phase,

                        "signalState":
                            signal_state,

                        "stateSummary":
                            state_summary,

                        "phaseDuration":
                            round(
                                phase_duration,
                                2
                            ),

                        "nextSwitch":
                            round(
                                next_switch,
                                2
                            ),

                        "controlledLanes":
                            controlled_lanes,

                        "controlledLaneCount":
                            len(
                                controlled_lanes
                            )

                    })


                except Exception as e:

                    print(
                        "TRAFFIC ERROR:",
                        junction_id,
                        e
                    )


            return jsonify({

                "success":
                    True,

                "simulationTime":
                    simulation_time,

                "data":
                    traffic_data,

                "trafficLightCount":
                    len(
                        traffic_data
                    )

            })


    except Exception as e:

        print()
        print("TRAFFIC API ERROR:")
        print(e)
        print()


        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# LIVE SUMO VEHICLE POSITIONS
# ============================================================

@app.get("/api/vehicles")
def get_vehicles():

    try:

        with sumo_lock:

            ensure_sumo()


            # ------------------------------------------------
            # IMPORTANT:
            #
            # DO NOT call simulationStep() here.
            #
            # /api/traffic already advances SUMO.
            #
            # This endpoint simply reads the latest position.
            #
            # This prevents multiple frontend polling requests
            # from advancing SUMO too quickly.
            # ------------------------------------------------

            vehicle_ids = (

                traci.vehicle
                .getIDList()

            )


            vehicles = []


            for vehicle_id in vehicle_ids:

                try:

                    # ----------------------------------------
                    # POSITION
                    # ----------------------------------------

                    x, y = (

                        traci.vehicle
                        .getPosition(
                            vehicle_id
                        )

                    )


                    # ----------------------------------------
                    # SPEED
                    # ----------------------------------------

                    speed_ms = (

                        traci.vehicle
                        .getSpeed(
                            vehicle_id
                        )

                    )


                    # ----------------------------------------
                    # HEADING
                    # ----------------------------------------

                    angle = (

                        traci.vehicle
                        .getAngle(
                            vehicle_id
                        )

                    )


                    # ----------------------------------------
                    # ROAD
                    # ----------------------------------------

                    road_id = (

                        traci.vehicle
                        .getRoadID(
                            vehicle_id
                        )

                    )


                    # ----------------------------------------
                    # LANE
                    # ----------------------------------------

                    lane_id = (

                        traci.vehicle
                        .getLaneID(
                            vehicle_id
                        )

                    )


                    # ----------------------------------------
                    # CURRENT JUNCTION
                    # ----------------------------------------

                    current_junction = None


                    try:

                        if (

                            road_id

                            and

                            not road_id.startswith(
                                ":"
                            )

                        ):

                            from_junction = (

                                traci.edge
                                .getFromJunction(
                                    road_id
                                )

                            )


                            to_junction = (

                                traci.edge
                                .getToJunction(
                                    road_id
                                )

                            )


                            current_junction = {

                                "from":
                                    from_junction,

                                "to":
                                    to_junction

                            }


                    except Exception:

                        current_junction = None


                    # ----------------------------------------
                    # VEHICLE OBJECT
                    # ----------------------------------------

                    vehicles.append({

                        "id":
                            vehicle_id,

                        "x":
                            float(x),

                        "y":
                            float(y),

                        "speedKmh":
                            round(
                                speed_ms * 3.6,
                                2
                            ),

                        "headingDeg":
                            round(
                                angle,
                                2
                            ),

                        "roadId":
                            road_id,

                        "laneId":
                            lane_id,

                        "junction":
                            current_junction

                    })


                except Exception as e:

                    print(
                        "VEHICLE ERROR:",
                        vehicle_id,
                        e
                    )


            return jsonify({

                "success":
                    True,

                "simulationTime":
                    traci.simulation
                    .getTime(),

                "vehicles":
                    vehicles

            })


    except Exception as e:

        print()
        print("VEHICLE API ERROR:")
        print(e)
        print()


        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# START SIMULATION MANUALLY
#
# Useful if SUMO ever gets closed.
# ============================================================

@app.post("/api/simulation/start")
def simulation_start():

    try:

        with sumo_lock:

            start_sumo()


            return jsonify({

                "success":
                    True,

                "message":
                    "SUMO started",

                "simulationTime":
                    traci.simulation
                    .getTime()

            })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# ADVANCE SIMULATION MANUALLY
# ============================================================

@app.post("/api/simulation/step")
def simulation_step():

    try:

        with sumo_lock:

            ensure_sumo()


            traci.simulationStep()


            return jsonify({

                "success":
                    True,

                "simulationTime":
                    traci.simulation
                    .getTime()

            })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# CLOSE SIMULATION
# ============================================================

@app.post("/api/simulation/close")
def simulation_close():

    try:

        close_sumo()


        return jsonify({

            "success":
                True,

            "message":
                "SUMO closed"

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# START SUMO BEFORE FLASK
#
# THIS IS THE MAIN SPEED IMPROVEMENT.
#
# SUMO is connected BEFORE React asks for /api/network.
#
# Therefore:
#
# React opens
#      ↓
# /api/network
#      ↓
# cached network
#      ↓
# FAST RESPONSE
#
# Instead of:
#
# React opens
#      ↓
# /api/network
#      ↓
# START SUMO
#      ↓
# WAIT
#      ↓
# NETWORK
#
# ============================================================

print()
print("=" * 70)
print("RESQROUTE BACKEND INITIALIZING")
print("=" * 70)
print()


try:

    start_sumo()

    # Build the network immediately.
    #
    # This means the first React request does not have to wait
    # for the network to be constructed.

    build_network_cache()


except Exception as e:

    print()
    print("=" * 70)
    print("WARNING: SUMO COULD NOT START")
    print("=" * 70)

    print()
    print(e)

    print()
    print(
        "The Flask server will still start."
    )

    print(
        "Fix the SUMO path/config and restart api.py."
    )

    print("=" * 70)
    print()


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("              RESQROUTE SUMO BACKEND")
    print("=" * 70)

    print()

    print(
        "API      : http://127.0.0.1:5000"
    )

    print(
        "HEALTH   : /api/health"
    )

    print(
        "NETWORK  : /api/network"
    )

    print(
        "TRAFFIC  : /api/traffic"
    )

    print(
        "VEHICLES : /api/vehicles"
    )

    print()

    print(
        "SUMO RUNNING:",
        sumo_running
    )

    print()

    print("=" * 70)
    print()


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # debug=False
    #
    # Flask's debug reloader can start the Python program twice.
    # That can cause SUMO/TraCI to be started twice.
    #
    # So we intentionally keep debug=False here.
    # --------------------------------------------------------

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False,

        threaded=True

    )