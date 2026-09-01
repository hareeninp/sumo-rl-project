"""
run_sumo_emergency.py - Real SUMO Multi-EV Integration Script for Team 2 B1/B2

Executes multi-emergency vehicle priority control in SUMO simulation using cfg_multi_ev.sumocfg:
  1. Detects live emergency vehicles from SUMO (ambulance_1, firetruck_1, police_1, etc.)
  2. Reads vehicle telemetry (edge, position, speed) via TraCIAdapter
  3. Registers & verifies B2 emergency requests with secure tokens
  4. Pauses B1 Q-learning and grants B2 signal preemption on TLS IDs (J1..J16)
  5. Processes emergency vehicles sequentially (ensuring strict B1/B2 ownership protection)
  6. Executes safe signal transitions (B1_SAFE_TRANSITIONS.csv) & dynamic green corridor
  7. Flushes cross-traffic queues during RECOVERY mode
  8. Completes HAND_BACK and resumes B1 Q-learning control after each emergency vehicle passes
"""

import os
import sys
import logging
from typing import Set, List, Dict, Any

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter, set_traci_provider
from rl_agent.team2.token_service import generate_verification_token
from rl_agent.team2.verification import register_token
from rl_agent.team2.handoff import MasterSystemController
from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_green_phase_for_movement,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_junction_sequence_from_edges(edges: List[str]) -> List[str]:
    """Extracts ordered list of junction IDs from SUMO route edge IDs."""
    junctions: List[str] = []
    for edge in edges:
        parts = edge.split("_")
        for part in parts:
            if part.startswith("J") and part[1:].isdigit():
                if not junctions or junctions[-1] != part:
                    junctions.append(part)
    return junctions


def run_sumo_multi_ev_simulation(
    sumocfg_path: str = "A1_network/cfg_multi_ev.sumocfg",
    max_sim_seconds: float = 650.0,
) -> None:
    """
    Runs live SUMO simulation using cfg_multi_ev.sumocfg and manages
    sequential multi-emergency vehicle preemption and B1/B2 handoffs.
    """
    print("\n" + "=" * 75)
    print(" REAL SUMO INTEGRATION: MULTI-EV EMERGENCY PREEMPTION & HANDOFF DEMO")
    print(" Config File: ", sumocfg_path)
    print(" Duration:    ", max_sim_seconds, "simulation seconds")
    print("=" * 75 + "\n")

    # Connect Team 1's traci_interface provider
    try:
        from traci_interface import traci_interface
        set_traci_provider(traci_interface)
        print("[INIT] Connected Team 1 traci_interface provider.")
    except ImportError:
        print("[INIT] Running with MockTraCIAdapter fallback.")

    adapter: TraCIAdapter = get_traci_adapter()
    master = MasterSystemController()

    # Start SUMO simulation
    resolved_cfg = os.path.abspath(sumocfg_path) if not os.path.isabs(sumocfg_path) else sumocfg_path
    adapter.start_sim(resolved_cfg,gui=True)

    detected_vehicles: Set[str] = set()
    registered_vehicles: Set[str] = set()
    queued_vehicles: Set[str] = set()
    preempted_junctions_map: Dict[str, List[str]] = {}
    recovery_completed_count: int = 0
    handback_completed_count: int = 0
    b1_resumed_count: int = 0

    try:
        while True:
            # Step SUMO simulation by 1 step
            adapter.step()

            # Read current simulation time via A2 TraCIAdapter interface
            current_time = float(adapter.get_simulation_time())

            # 1. CONTINUOUS DETECTION: Detect live active emergency vehicles in SUMO simulation at EVERY step
            active_vehs = adapter.get_all_active_evs() or adapter.get_active_vehicles()

            # Filter for emergency vehicles (ambulance, firetruck, policecar, etc.)
            ev_candidates = [
                v for v in active_vehs
                if v.lower().startswith(("ambulance", "firetruck", "police", "amb", "emerg")) or
                   any(kw in v.lower() for kw in ("ambulance", "firetruck", "police"))
            ]

            for ev in ev_candidates:
                detected_vehicles.add(ev)

            # 2. CONTINUOUS REGISTRATION: Process EVERY newly detected vehicle without system_mode restrictions
            if ev_candidates and current_time < max_sim_seconds:
                for veh_id in ev_candidates:
                    if veh_id not in registered_vehicles:
                        registered_vehicles.add(veh_id)

                        # Read vehicle telemetry via A2 TraCIAdapter interface
                        curr_edge = adapter.get_vehicle_edge(veh_id)
                        pos = adapter.get_vehicle_position(veh_id)
                        speed = adapter.get_vehicle_speed(veh_id)

                        # Obtain actual assigned SUMO route from TraCI (do NOT call findRoute to dynamically reroute)
                        route_edges = adapter.get_vehicle_route(veh_id)
                        if not route_edges:
                            try:
                                import traci
                                if traci.isLoaded() and veh_id in traci.vehicle.getIDList():
                                    route_edges = list(traci.vehicle.getRoute(veh_id))
                            except Exception:
                                pass

                        junction_seq = extract_junction_sequence_from_edges(route_edges)
                        preempted_junctions_map[veh_id] = junction_seq

                        print(f"\n[EV ROUTE]\n{veh_id}:\n{' -> '.join(route_edges)}", flush=True)

                        # Determine vehicle type, severity (Tier 1), and priority (Tier 2)
                        if "fire" in veh_id.lower():
                            v_type = "FIRE TRUCK"
                            sev = "HIGH"
                            prio = 2
                        elif "police" in veh_id.lower():
                            v_type = "POLICE"
                            sev = "NORMAL"
                            prio = 3
                        else:
                            v_type = "AMBULANCE"
                            sev = "CRITICAL" if ("1" in veh_id or "4" in veh_id) else "HIGH"
                            prio = 1

                        # Generate & register secure verification token
                        token = generate_verification_token()
                        register_token(token)

                        request_payload = {
                            "vehicleId": veh_id,
                            "vehicleType": v_type,
                            "emergencyType": v_type,
                            "severity": sev,
                            "priority": prio,
                            "verificationToken": token,
                        }

                        team3_response = {
                            "hospital": {
                                "hospitalId": "H001",
                                "name": "City Emergency Hospital",
                                "speciality": v_type,
                            },
                            "route": {
                                "routeId": f"R_{veh_id}",
                                "edgeIds": route_edges,
                                "junctionIds": junction_seq,
                                "etaMinutes": 5.0,
                            }
                        }

                        print(f"\n[TIME {current_time:.0f}s] CONTINUOUS DETECTION: {veh_id} (Severity: {sev}, Type: {v_type}) detected on edge {curr_edge}", flush=True)
                        master.request_emergency(request_payload, team3_response, current_time=current_time)

                        # SUMO-GUI Camera Tracking for ambulance_1
                        if veh_id == "ambulance_1":
                            try:
                                import traci
                                if traci.isLoaded():
                                    traci.gui.trackVehicle("View #0", "ambulance_1")
                                    traci.gui.setZoom("View #0", 1000)
                            except Exception:
                                pass

            # Track queued vehicles from controller
            for q_veh in master.b2_controller.pending_queue:
                queued_vehicles.add(q_veh.vehicle_id)

            # 3. Exit condition: Max duration reached AND all registered emergency vehicles processed AND system in NORMAL
            if current_time >= max_sim_seconds and master.system_mode == "NORMAL":
                if registered_vehicles and len(master.b2_controller.processed_vehicles) >= len(registered_vehicles):
                    print(f"\n[SIMULATION] Target duration of {max_sim_seconds:.0f}s reached and all {len(registered_vehicles)} detected emergency vehicles processed & handed back.", flush=True)
                    break

            # 4. Update telemetry for active and queued emergency vehicles
            all_tracked_evs = []
            if master.b2_controller.active_vehicle:
                all_tracked_evs.append(master.b2_controller.active_vehicle)
            all_tracked_evs.extend(master.b2_controller.pending_queue)

            for ev in all_tracked_evs:
                try:
                    c_edge = adapter.get_vehicle_edge(ev.vehicle_id)
                    c_pos = adapter.get_vehicle_position(ev.vehicle_id)
                    c_spd = adapter.get_vehicle_speed(ev.vehicle_id)
                    ev.update_telemetry(c_edge, c_pos, c_spd)
                except Exception:
                    pass

            # 5. Advance Master System Controller across network junctions
            j_list = list(JUNCTION_PHASE_CONFIG.keys())
            for j_id in j_list:
                tls_id = JUNCTION_PHASE_CONFIG[j_id].get("tls_id", j_id)
                dummy_j_state = {"current_phase": adapter.get_signal_phase(tls_id), "queues": {}}
                master.step(
                    junction_id=j_id,
                    tls_id=tls_id,
                    junction_state=dummy_j_state,
                    current_time=current_time,
                    traci_interface=adapter._active_interface
                )

    except KeyboardInterrupt:
        print("\n[SIMULATION] Simulation stopped by user.")
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
    finally:
        adapter.close_sim()

        processed_list = list(master.b2_controller.processed_vehicles)
        print("\n" + "=" * 75)
        print(" SUMMARY OF REAL SUMO EMERGENCY PREEMPTION & HANDBACK DEMO")
        print("=" * 75)
        print(f" Emergency Vehicles Detected:            {len(detected_vehicles)} ({list(detected_vehicles)})")
        print(f" Emergency Vehicles Registered:          {len(registered_vehicles)} ({list(registered_vehicles)})")
        print(f" Emergency Vehicles Queued:              {len(queued_vehicles)} ({list(queued_vehicles)})")
        print(f" Emergency Vehicles Actually Processed:  {len(processed_list)} ({processed_list})")
        print(" Junctions Preempted per Vehicle:")
        for v_id, j_list in preempted_junctions_map.items():
            print(f"   - {v_id}: {' -> '.join(j_list)}")
        print(f" Recovery Completed:                     {recovery_completed_count} corridor(s)")
        print(f" Final Handbacks:                        {handback_completed_count} time(s)")
        print(f" B1 Q-Learning Control Resumed:          {b1_resumed_count} time(s)")
        print("=" * 75 + "\n", flush=True)


if __name__ == "__main__":
    run_sumo_multi_ev_simulation(max_sim_seconds=650.0)
