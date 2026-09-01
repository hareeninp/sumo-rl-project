import traci
from traci_interface.config import INCOMING_LANES
# ============================================================
# EMERGENCY VEHICLE REGISTRY
# ============================================================

ev_registry = {}
def register_ev(
    vehicle_id,
    vehicle_type="ambulance",
    phase="dispatch",
    target=None,
    priority_class=2.5
):
    """
    Register an emergency vehicle in the EV registry.
    """

    ev_registry[vehicle_id] = {
        "type": vehicle_type,
        "phase": phase,
        "condition": None,
        "target": target,
        "priority_weight": priority_class
    }

def update_ev_phase_automatically(vehicle_id):
    """
    Automatically switch an EV from dispatch to transport
    when it reaches its configured target edge.
    """

    if vehicle_id not in ev_registry:
        return None

    # Already in transport
    if ev_registry[vehicle_id]["phase"] != "dispatch":
        return ev_registry[vehicle_id]["phase"]

    target = ev_registry[vehicle_id]["target"]

    # No target configured
    if target is None:
        return ev_registry[vehicle_id]["phase"]

    # EV has left the simulation
    if not vehicle_exists(vehicle_id):
        return ev_registry[vehicle_id]["phase"]

    current_edge = get_vehicle_edge(vehicle_id)

    # Reached target edge
    if current_edge == target:
        update_ev_phase(vehicle_id, "transport")

    return ev_registry[vehicle_id]["phase"]
def update_ev_phase(vehicle_id, phase):
    """
    Update the operational phase of an emergency vehicle.
    Valid phases: dispatch, transport.
    """

    if vehicle_id not in ev_registry:
        raise ValueError(
            f"Emergency vehicle '{vehicle_id}' is not registered."
        )

    if phase not in ("dispatch", "transport"):
        raise ValueError(
            f"Invalid phase '{phase}'. "
            "Use 'dispatch' or 'transport'."
        )

    ev_registry[vehicle_id]["phase"] = phase

def get_ev_priority(vehicle_id):
    """
    Return the priority weight of a registered emergency vehicle.
    """

    if vehicle_id not in ev_registry:
        raise ValueError(
            f"Emergency vehicle '{vehicle_id}' is not registered."
        )

    return ev_registry[vehicle_id]["priority_weight"]
def get_ev_state(vehicle_id):
    """
    Return the current physical and operational state
    of a registered emergency vehicle.

    B1 interface:
        type
        phase
        condition
        target
        priority_weight
        position
        speed
        current_edge
    """

    if vehicle_id not in ev_registry:
        raise ValueError(
            f"Emergency vehicle '{vehicle_id}' is not registered."
        )

    registry = ev_registry[vehicle_id]

    # EV has left the simulation
    if not vehicle_exists(vehicle_id):
        return {
            "vehicle_id": vehicle_id,
            "active": False,
            "type": registry["type"],
            "phase": registry["phase"],
            "condition": registry["condition"],
            "target": registry["target"],
            "priority_weight": registry["priority_class"],
            "position": None,
            "speed": 0.0,
            "current_edge": None
        }

    return {
        "vehicle_id": vehicle_id,
        "active": True,
        "type": registry["type"],
        "phase": registry["phase"],
        "condition": registry["condition"],
        "target": registry["target"],
        "priority_weight": registry["priority_weight"],
        "position": get_vehicle_position(vehicle_id),
        "speed": get_vehicle_speed(vehicle_id),
        "current_edge": get_vehicle_edge(vehicle_id)
    }
def log_specialty_gap(vehicle_id, required_specialty, selected_hospital):
    """
    Log when the selected hospital does not match
    the emergency vehicle's required specialty.
    """

    message = (
        f"SPECIALTY GAP: vehicle={vehicle_id}, "
        f"required={required_specialty}, "
        f"selected_hospital={selected_hospital}"
    )

    print(message)

    return {
        "vehicle_id": vehicle_id,
        "required_specialty": required_specialty,
        "selected_hospital": selected_hospital,
        "message": message
    }

# ============================================================
# SAFETY CONFIGURATION
# ============================================================

MIN_ACTION_INTERVAL = 5

last_change_time = {}


# ============================================================
# SIMULATION CONTROL
# ============================================================

def start_sim(sumocfg_path, gui=False):
    binary = "sumo-gui" if gui else "sumo"
    cmd = [binary, "-c", sumocfg_path, "--start"]
    if gui:
        cmd.extend(["--delay", "100"])
    traci.start(cmd)

def step():
    traci.simulationStep()

    # Automatically register and update all active EVs
    for vehicle_id in get_all_active_evs():

        if vehicle_id not in ev_registry:
            register_ev(
                vehicle_id,
                vehicle_type=traci.vehicle.getTypeID(vehicle_id)
            )

        # Automatically handle dispatch -> transport transition
        update_ev_phase_automatically(vehicle_id)

def close_sim():
    traci.close()


# ============================================================
# LANE INFORMATION
# ============================================================

def get_lane_vehicle_count(lane_id):
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_mean_speed(lane_id):
    return traci.lane.getLastStepMeanSpeed(lane_id)


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


# ============================================================
# TRAFFIC SIGNAL INFORMATION
# ============================================================

def get_signal_phase(tls_id):
    return traci.trafficlight.getPhase(tls_id)


def set_signal_phase(tls_id, phase_id):

    current_time = traci.simulation.getTime()

    if not can_change_phase(tls_id, current_time):
        return False

    traci.trafficlight.setPhase(tls_id, phase_id)

    last_change_time[tls_id] = current_time

    return True


def can_change_phase(tls_id, current_time):

    last_time = last_change_time.get(tls_id, -999)

    return current_time - last_time >= MIN_ACTION_INTERVAL


def force_phase_change(tls_id, target_phase):
    """
    Request a traffic-light phase change without advancing
    the SUMO simulation.

    SUMO simulation time is advanced only by the caller through
    simulationStep().
    """

    current_phase = traci.trafficlight.getPhase(tls_id)

    if current_phase == target_phase:
        print(f"{tls_id}: already at phase {target_phase}")
        return

    # Get the complete TLS program to validate the target phase.
    logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
    phases = logic.phases
    num_phases = len(phases)

    if target_phase < 0 or target_phase >= num_phases:
        raise ValueError(
            f"Invalid target phase {target_phase} for {tls_id}. "
            f"Valid phases: 0-{num_phases - 1}"
        )

    print(
        f"{tls_id}: changing phase "
        f"{current_phase} -> {target_phase}"
    )

    # Request the target phase.
    # Do NOT call simulationStep() here.
    traci.trafficlight.setPhase(tls_id, target_phase)

    current_time = traci.simulation.getTime()
    last_change_time[tls_id] = current_time

    print(
        f"{tls_id}: requested phase {target_phase}"
    )

# ============================================================
# VEHICLE INFORMATION
# ============================================================
def get_route_to_target(vehicle_id, target_edge_id):
    """
    Calculate a route from the emergency vehicle's current edge
    to the target edge.

    Returns:
        (route_edges, travel_time)

    If no valid route exists, returns:
        ([], float("inf"))
    """

    if not vehicle_exists(vehicle_id):
        return [], float("inf")

    current_edge = traci.vehicle.getRoadID(vehicle_id)

    if not current_edge or current_edge.startswith(":"):
        return [], float("inf")

    try:
        route = traci.simulation.findRoute(
            current_edge,
            target_edge_id
        )

        if not route.edges:
            return [], float("inf")

        return route.edges, route.travelTime

    except traci.TraCIException:
        return [], float("inf")
def get_vehicle_position(vehicle_id):
    return traci.vehicle.getPosition(vehicle_id)


def get_vehicle_speed(vehicle_id):
    return traci.vehicle.getSpeed(vehicle_id)


def get_vehicle_edge(vehicle_id):
    return traci.vehicle.getRoadID(vehicle_id)

def get_vehicle_ids():
    return traci.vehicle.getIDList()
def is_emergency_vehicle(vehicle_id):
    """
    Check whether a vehicle is an emergency vehicle
    based on its vehicle type.
    """
    emergency_types = {
        "ambulance",
        "firetruck",
        "policecar"
    }

    try:
        vehicle_type = traci.vehicle.getTypeID(vehicle_id)
        return vehicle_type.lower() in emergency_types
    except traci.TraCIException:
        return False


def get_all_active_evs():
    """
    Return all currently active emergency vehicles.
    """
    return [
        vehicle_id
        for vehicle_id in traci.vehicle.getIDList()
        if is_emergency_vehicle(vehicle_id)
    ]

def get_simulation_time():
    return traci.simulation.getTime()

def get_emergency_vehicle_state(vehicle_id="ev_1"):
    """
    Return the current state of the emergency vehicle.
    """

    if not vehicle_exists(vehicle_id):
        return {
            "active": False,
            "vehicle_id": vehicle_id
        }

    return {
        "active": True,
        "vehicle_id": vehicle_id,
        "edge": get_vehicle_edge(vehicle_id),
        "position": traci.vehicle.getLanePosition(vehicle_id),
        "speed": get_vehicle_speed(vehicle_id),
    }
# ============================================================
# JUNCTION STATE
# ============================================================

def get_junction_state(junction_id, tls_id, lanes):

    state = {
        "junction_id": junction_id,
        "queue_lengths": {},
        "vehicle_counts": {},
        "mean_speeds": {},
        "current_phase": None
    }

    for lane_id in lanes:

        state["queue_lengths"][lane_id] = (
            get_queue_length(lane_id)
        )

        state["vehicle_counts"][lane_id] = (
            get_lane_vehicle_count(lane_id)
        )

        state["mean_speeds"][lane_id] = (
            get_lane_mean_speed(lane_id)
        )

    # Get traffic-light phase if this junction has a TLS
    if tls_id is not None:

        state["current_phase"] = (
            get_signal_phase(tls_id)
        )

    return state
def vehicle_exists(vehicle_id):
    return vehicle_id in traci.vehicle.getIDList()
def get_emergency_vehicle_junction(vehicle_id="ev_1"):
    """
    Determine which junction the emergency vehicle
    is approaching based on its current road/edge.
    """

    if not vehicle_exists(vehicle_id):
        return None

    edge_id = get_vehicle_edge(vehicle_id)

    for junction_id, lanes in INCOMING_LANES.items():
        for lane_id in lanes:
            if lane_id.startswith(edge_id + "_"):
                return junction_id

    return None
