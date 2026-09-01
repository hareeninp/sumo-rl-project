"""
api_server.py - Flask REST API Server for Team 3 Dashboard Integration

Exposes HTTP REST JSON endpoints at http://127.0.0.1:5000 for Team 3's web dashboard:
  GET  /api/health            - Server & simulation status
  GET  /api/network           - Junction topology, roads, and traffic light configs
  GET  /api/traffic           - Junction queue lengths, vehicle counts, and signal phases
  GET  /api/vehicles          - Live vehicle telemetry (ID, x/y, speed, heading, edge, EV info)
  POST /api/simulation/start  - Starts SUMO simulation session
  POST /api/simulation/step   - Steps SUMO simulation & evaluates B1/B2 Master System Controller
  POST /api/simulation/stop   - Terminates active SUMO simulation session

Designed as a non-disruptive wrapper around existing Team 2 components (TraCIAdapter,
MasterSystemController, phase_config.py). Does NOT alter any B1 or B2 algorithms.
"""

import os
import sys
import logging
from typing import Dict, Any, List

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter, set_traci_provider
from rl_agent.team2.handoff import MasterSystemController
from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_junction_config,
    get_valid_green_phases,
)
from traci_interface.config import INCOMING_LANES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Initialize Flask Application with CORS
app = Flask(__name__)
CORS(app)

# Auto-detect and connect Team 1's traci_interface if available
try:
    from traci_interface import traci_interface
    set_traci_provider(traci_interface)
    logger.info("[API SERVER] Connected Team 1 traci_interface provider.")
except ImportError:
    logger.info("[API SERVER] Running with MockTraCIAdapter fallback.")

# Shared Singleton Instances
adapter: TraCIAdapter = get_traci_adapter()
master: MasterSystemController = MasterSystemController()


def is_traci_connected() -> bool:
    """Safely checks if TraCI is currently connected to an active SUMO simulation."""
    try:
        import traci
        if hasattr(traci, "isLoaded"):
            return bool(traci.isLoaded())
        _ = traci.simulation.getTime()
        return True
    except Exception:
        return False


@app.route("/api/health", methods=["GET"])
def get_health() -> Any:
    """Returns server and simulation status."""
    is_running = is_traci_connected()
    sim_time = 0.0
    if is_running:
        try:
            sim_time = float(adapter.get_simulation_time())
        except Exception:
            sim_time = 0.0

    active_controller = "B2" if master.system_mode in ("EMERGENCY", "RECOVERY") else "B1"
    emergency_state = master.b2_controller.state.name if hasattr(master, "b2_controller") else "NORMAL"

    return jsonify({
        "success": True,
        "status": "online",
        "simulationRunning": is_running,
        "simulationTime": sim_time,
        "systemMode": master.system_mode,
        "activeController": active_controller,
        "emergencyState": emergency_state,
    })


@app.route("/api/network", methods=["GET"])
def get_network() -> Any:
    """Returns static network topology, junction configs, and roads."""
    junctions = []
    traffic_lights = []
    roads_set = set()

    for jid, cfg in JUNCTION_PHASE_CONFIG.items():
        tls_id = cfg.get("tls_id", jid)
        green_phases = cfg.get("green_phases", [])
        lanes = INCOMING_LANES.get(jid, [])

        for lane in lanes:
            parts = lane.split("_")
            if len(parts) >= 2:
                road_id = "_".join(parts[:-1])
                roads_set.add(road_id)

        junctions.append({
            "junctionId": jid,
            "tlsId": tls_id,
            "greenPhases": green_phases,
            "incomingLanes": lanes,
            "trafficGroups": cfg.get("traffic_groups", {}),
            "rlEnabled": len(green_phases) > 1,
        })

        traffic_lights.append({
            "tlsId": tls_id,
            "junctionId": jid,
            "numPhases": len(cfg.get("phase_details", {})),
            "greenPhases": green_phases,
        })

    return jsonify({
        "success": True,
        "junctions": junctions,
        "roads": sorted(list(roads_set)),
        "trafficLights": traffic_lights,
    })


@app.route("/api/traffic", methods=["GET"])
def get_traffic() -> Any:
    """Returns per-junction traffic state, queue lengths, vehicle counts, and signal phases."""
    if not is_traci_connected():
        default_traffic = []
        for jid, cfg in JUNCTION_PHASE_CONFIG.items():
            tls_id = cfg.get("tls_id", jid)
            lanes = INCOMING_LANES.get(jid, [])
            phase_details = cfg.get("phase_details", {}).get(0, {})
            state_str = phase_details.get("state_string", "G" * max(1, len(lanes)))
            default_traffic.append({
                "junctionId": jid,
                "tlsId": tls_id,
                "signalPhase": 0,
                "signalState": state_str,
                "nextSwitch": 31.0,
                "vehicleCount": 0,
                "queueLength": 0,
                "laneQueues": {l: 0 for l in lanes},
                "laneCounts": {l: 0 for l in lanes},
            })
        return jsonify({
            "success": True,
            "simulationRunning": False,
            "simulationTime": 0.0,
            "traffic": default_traffic,
        })

    sim_time = float(adapter.get_simulation_time())
    traffic_data = []

    for jid, cfg in JUNCTION_PHASE_CONFIG.items():
        tls_id = cfg.get("tls_id", jid)
        lanes = INCOMING_LANES.get(jid, [])

        try:
            raw_state = adapter.get_junction_state(jid, tls_id, lanes)
            curr_phase = adapter.get_signal_phase(tls_id) if tls_id else 0
        except Exception:
            raw_state = {"current_phase": 0, "queues": {}, "vehicle_counts": {}}
            curr_phase = 0

        queues_dict = raw_state.get("queue_lengths", raw_state.get("queues", {}))
        counts_dict = raw_state.get("vehicle_counts", {})

        total_queue = sum(int(queues_dict.get(l, 0)) for l in lanes) if isinstance(queues_dict, dict) else 0
        total_count = sum(int(counts_dict.get(l, 0)) for l in lanes) if isinstance(counts_dict, dict) else 0

        phase_details = cfg.get("phase_details", {}).get(curr_phase, {})
        state_str = phase_details.get("state_string", "G" * max(1, len(lanes)))

        # Query actual SUMO next-switch time via TraCI if connected
        next_switch = 0.0
        try:
            import traci
            next_switch = round(float(traci.trafficlight.getNextSwitch(tls_id)), 1)
        except Exception:
            duration = float(phase_details.get("duration_sec", 31))
            next_switch = round(sim_time + duration, 1)

        traffic_data.append({
            "junctionId": jid,
            "tlsId": tls_id,
            "signalPhase": curr_phase,
            "signalState": state_str,
            "nextSwitch": next_switch,
            "vehicleCount": total_count,
            "queueLength": total_queue,
            "laneQueues": queues_dict if isinstance(queues_dict, dict) else {},
            "laneCounts": counts_dict if isinstance(counts_dict, dict) else {},
        })

    return jsonify({
        "success": True,
        "simulationRunning": True,
        "simulationTime": sim_time,
        "traffic": traffic_data,
    })


@app.route("/api/vehicles", methods=["GET"])
def get_vehicles() -> Any:
    """Returns live vehicle telemetry including position, speed, road, and EV state."""
    if not is_traci_connected():
        return jsonify({
            "success": True,
            "simulationRunning": False,
            "simulationTime": 0.0,
            "count": 0,
            "vehicles": [],
        })
    vehicle_list = []

    try:
        active_ids = adapter.get_active_vehicles() or adapter.get_vehicle_ids()
    except Exception:
        active_ids = []

    for veh_id in active_ids:
        try:
            pos_raw = adapter.get_vehicle_position(veh_id)
            if isinstance(pos_raw, (tuple, list)):
                x = float(pos_raw[0]) if len(pos_raw) > 0 else 0.0
                y = float(pos_raw[1]) if len(pos_raw) > 1 else 0.0
            else:
                x = float(pos_raw)
                y = 0.0

            spd_ms = float(adapter.get_vehicle_speed(veh_id))
            speed_kmh = round(spd_ms * 3.6, 1)

            road_id = adapter.get_vehicle_edge(veh_id)
            lane_id = f"{road_id}_0" if road_id else ""

            heading_deg = 90.0
            active_interface = adapter._active_interface
            if hasattr(active_interface, "traci"):
                try:
                    import traci
                    heading_deg = float(traci.vehicle.getAngle(veh_id))
                    lane_id = traci.vehicle.getLaneID(veh_id)
                except Exception:
                    pass

            is_ev = veh_id.lower().startswith(("ambulance", "firetruck", "police", "amb", "emerg")) or \
                    any(kw in veh_id.lower() for kw in ("ambulance", "firetruck", "police"))

            veh_data = {
                "id": veh_id,
                "x": round(x, 2),
                "y": round(y, 2),
                "headingDeg": round(heading_deg, 1),
                "speedKmh": speed_kmh,
                "speedMs": round(spd_ms, 2),
                "roadId": road_id,
                "laneId": lane_id,
                "isEmergency": is_ev,
            }

            if is_ev:
                ev_info = adapter.get_ev_state(veh_id)
                if ev_info:
                    veh_data["evDetails"] = {
                        "type": ev_info.get("type", "AMBULANCE"),
                        "phase": ev_info.get("phase", "dispatch"),
                        "target": ev_info.get("target", ""),
                        "priorityWeight": ev_info.get("priority_weight", 1.0),
                    }

            vehicle_list.append(veh_data)
        except Exception:
            continue

    return jsonify({
        "success": True,
        "simulationRunning": True,
        "simulationTime": float(adapter.get_simulation_time()),
        "count": len(vehicle_list),
        "vehicles": vehicle_list,
    })


@app.route("/api/simulation/start", methods=["POST"])
def start_simulation() -> Any:
    """Starts SUMO simulation session."""
    body = request.get_json(silent=True) or {}
    sumocfg = body.get("sumocfg", "A1_network/cfg_multi_ev.sumocfg")
    gui = body.get("gui", False)

    try:
        resolved_cfg = os.path.abspath(sumocfg) if not os.path.isabs(sumocfg) else sumocfg
        adapter.start_sim(resolved_cfg, gui=gui)
        logger.info(f"[API] Simulation started with config: '{resolved_cfg}' (gui={gui})")
        return jsonify({
            "success": True,
            "message": "Simulation started successfully.",
            "sumocfg": sumocfg,
            "gui": gui,
        })
    except Exception as e:
        logger.error(f"[API] Failed to start simulation: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/simulation/step", methods=["POST"])
def step_simulation() -> Any:
    """Steps SUMO simulation and evaluates B1/B2 MasterSystemController."""
    body = request.get_json(silent=True) or {}
    steps = int(body.get("steps", 1))
    j_key = body.get("junctionId", "J1")

    results = []
    try:
        for _ in range(steps):
            adapter.step()
            sim_time = float(adapter.get_simulation_time())

            j_cfg = get_junction_config(j_key)
            tls_id = j_cfg.get("tls_id", j_key) if j_cfg else j_key
            lanes = INCOMING_LANES.get(j_key, [])

            raw_state = adapter.get_junction_state(j_key, tls_id, lanes)
            traffic_groups = j_cfg.get("traffic_groups", {}) if j_cfg else None

            res = master.step(
                junction_id=j_key,
                tls_id=tls_id,
                junction_state=raw_state,
                traffic_groups=traffic_groups,
                current_time=sim_time,
                traci_interface=adapter._active_interface
            )
            results.append(res)

        return jsonify({
            "success": True,
            "simulationTime": float(adapter.get_simulation_time()),
            "systemMode": master.system_mode,
            "lastResult": results[-1] if results else {},
        })
    except Exception as e:
        logger.error(f"[API] Failed to step simulation: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/simulation/stop", methods=["POST"])
def stop_simulation() -> Any:
    """Closes SUMO simulation session."""
    try:
        adapter.close_sim()
        logger.info("[API] Simulation closed successfully.")
        return jsonify({
            "success": True,
            "message": "Simulation closed successfully.",
        })
    except Exception as e:
        logger.error(f"[API] Failed to stop simulation: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Team 2 Flask REST API Server for Team 3 Dashboard Integration")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" TEAM 2 FLASK REST API SERVER FOR TEAM 3 DASHBOARD INTEGRATION")
    print(f" Server URL: http://{args.host}:{args.port}")
    print(" Endpoints:")
    print("   GET  /api/health")
    print("   GET  /api/network")
    print("   GET  /api/traffic")
    print("   GET  /api/vehicles")
    print("   POST /api/simulation/start")
    print("   POST /api/simulation/step")
    print("   POST /api/simulation/stop")
    print("=" * 65 + "\n", flush=True)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
