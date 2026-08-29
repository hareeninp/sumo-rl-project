"""
run_sumo_emergency.py - Real SUMO Multi-EV Integration Script for Team 2 B1/B2

Executes multi-emergency vehicle priority control in SUMO simulation using cfg_multi_ev.sumocfg:
  1. Detects live emergency vehicles from SUMO (ambulance_1, firetruck_1, police_1, etc.)
  2. Reads vehicle telemetry (edge, position, speed) via TraCIAdapter
  3. Registers & verifies B2 emergency requests with secure tokens
  4. Pauses B1 Q-learning and grants B2 signal preemption on TLS IDs (J1..J16)
  5. Executes safe signal transitions (B1_SAFE_TRANSITIONS.csv) & dynamic green corridor
  6. Flushes cross-traffic queues during RECOVERY mode
  7. Hands control back to B1 Q-learning when route is cleared (NORMAL mode)
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
from rl_agent.team2.phase_config import JUNCTION_PHASE_CONFIG

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
    max_sim_seconds: float = 300.0,
) -> None:
    """
    Runs live SUMO simulation using cfg_multi_ev.sumocfg and manages
    multi-emergency vehicle preemption and B1/B2 handoffs.
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
        try:
            import traci
            print("[INIT] Connected standard TraCI module.")
        except ImportError:
            print("[INIT] Running with MockTraCIAdapter fallback.")

    adapter: TraCIAdapter = get_traci_adapter()
    master = MasterSystemController()

    # Start SUMO simulation
    resolved_cfg = os.path.abspath(sumocfg_path) if not os.path.isabs(sumocfg_path) else sumocfg_path
    adapter.start_sim(resolved_cfg)

    processed_vehicles: Set[str] = set()

    try:
        while True:
            # Step SUMO simulation by 1 second
            adapter.step()

            # Read current simulation time from TraCI
            try:
                import traci
                if traci.isLoaded():
                    current_time = float(traci.simulation.getTime())
                else:
                    current_time += 1.0
            except Exception:
                current_time += 1.0

            if current_time >= max_sim_seconds:
                print(f"\n[SIMULATION] Reached target duration of {max_sim_seconds:.0f}s. Finishing.")
                break

            # 1. Detect live active vehicles in SUMO simulation
            active_vehs = adapter.get_active_vehicles()

            # Filter for emergency vehicles (ambulance, firetruck, policecar)
            ev_candidates = [
                v for v in active_vehs
                if v.startswith(("ambulance", "firetruck", "police", "AMB", "EMERG"))
            ]

            # 2. Check for new emergency vehicle detection if system is in NORMAL mode
            if ev_candidates and master.system_mode == "NORMAL":
                for veh_id in ev_candidates:
                    if veh_id not in processed_vehicles:
                        processed_vehicles.add(veh_id)

                        # Read vehicle telemetry from TraCI
                        curr_edge = adapter.get_vehicle_edge(veh_id)
                        pos = adapter.get_vehicle_position(veh_id)
                        speed = adapter.get_vehicle_speed(veh_id)

                        # Extract route edges from TraCI if available
                        route_edges: List[str] = []
                        try:
                            import traci
                            if traci.isLoaded():
                                route_edges = list(traci.vehicle.getRoute(veh_id))
                        except Exception:
                            pass

                        if not route_edges:
                            route_edges = [curr_edge] if curr_edge else ["HOME1_J1", "J1_J2", "J2_J3"]

                        junction_seq = extract_junction_sequence_from_edges(route_edges)
                        if not junction_seq:
                            junction_seq = ["J1", "J2", "J3"]

                        # Determine emergency type based on vehicle ID
                        if "fire" in veh_id.lower():
                            e_type = "FIRE_RESPONSE"
                        elif "police" in veh_id.lower():
                            e_type = "LAW_ENFORCEMENT"
                        else:
                            e_type = "TRAUMA"

                        # Generate & register secure verification token
                        token = generate_verification_token()
                        register_token(token)

                        request_payload = {
                            "vehicleId": veh_id,
                            "vehicleType": "EMERGENCY_VEHICLE",
                            "emergencyType": e_type,
                            "priority": 1,
                            "verificationToken": token,
                        }

                        team3_response = {
                            "hospital": {
                                "hospitalId": "H001",
                                "name": "City Emergency Hospital",
                                "speciality": e_type,
                            },
                            "route": {
                                "routeId": f"R_{veh_id}",
                                "edgeIds": route_edges,
                                "junctionIds": junction_seq,
                                "etaMinutes": 5.0,
                            }
                        }

                        print(f"\n[TIME {current_time:.0f}s] DETECTED EMERGENCY VEHICLE: {veh_id} on edge {curr_edge}")
                        master.request_emergency(request_payload, team3_response, current_time=current_time)
                        break

            # 3. Update telemetry for active emergency vehicle
            if master.b2_controller.active_vehicle:
                active_vid = master.b2_controller.active_vehicle.vehicle_id
                try:
                    c_edge = adapter.get_vehicle_edge(active_vid)
                    c_pos = adapter.get_vehicle_position(active_vid)
                    c_spd = adapter.get_vehicle_speed(active_vid)
                    master.b2_controller.active_vehicle.update_telemetry(c_edge, c_pos, c_spd)
                except Exception:
                    pass

            # 4. Advance Master System Controller if in EMERGENCY or RECOVERY mode
            if master.system_mode in ("EMERGENCY", "RECOVERY"):
                primary_j = master.b2_controller.route[master.b2_controller.current_junction_idx] if (
                    master.b2_controller.route and master.b2_controller.current_junction_idx < len(master.b2_controller.route)
                ) else "J1"

                tls_id = JUNCTION_PHASE_CONFIG.get(primary_j, {}).get("tls_id", primary_j)
                dummy_j_state = {"current_phase": adapter.get_signal_phase(tls_id), "queues": {}}
                master.step(
                    junction_id=primary_j,
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
        print("\n" + "=" * 75)
        print(" SIMULATION COMPLETE & CLOSED SAFELY")
        print(" Total processed emergency vehicles:", len(processed_vehicles))
        print(" Processed vehicles list:", list(processed_vehicles))
        print("=" * 75 + "\n")


if __name__ == "__main__":
    run_sumo_multi_ev_simulation(max_sim_seconds=300.0)
