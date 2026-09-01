"""
scratch/investigate_ev_red_crossing.py - Comprehensive Red Light Crossing Investigation across all 9 EVs
"""
import os
import sys
import csv
import traci

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rl_agent.team2.traci_adapter import get_traci_adapter
from rl_agent.team2.handoff import MasterSystemController
from rl_agent.team2.token_service import generate_verification_token
from rl_agent.team2.verification import register_token
from rl_agent.team2.phase_config import JUNCTION_PHASE_CONFIG, get_green_phase_for_movement
from rl_agent.team2.diagnose_tls_synchronization import extract_junction_sequence_from_edges, get_edges_for_j

def run_investigation():
    adapter = get_traci_adapter()
    master = MasterSystemController()
    master.b2_controller._log = lambda msg: None

    sumocfg_path = os.path.abspath("A1_network/cfg_multi_ev.sumocfg")
    adapter.start_sim(sumocfg_path, gui=False)

    registered_vehicles = set()
    ev_routes = {}
    ev_junction_seqs = {}

    # Telemetry history for tracking entry transitions:
    # key: (ev_id, junction) -> history of records
    history = {}
    
    # Track junction crossings:
    # key: (ev_id, junction) -> status dict
    crossing_events = []

    cat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

    try:
        while True:
            adapter.step()
            current_time = float(adapter.get_simulation_time())

            active_vehs = adapter.get_all_active_evs() or adapter.get_active_vehicles()
            ev_candidates = [
                v for v in active_vehs
                if v.lower().startswith(("ambulance", "firetruck", "police", "amb", "emerg"))
            ]

            for veh_id in ev_candidates:
                if veh_id not in registered_vehicles:
                    registered_vehicles.add(veh_id)
                    route_edges = list(traci.vehicle.getRoute(veh_id))
                    junction_seq = extract_junction_sequence_from_edges(route_edges)
                    ev_routes[veh_id] = route_edges
                    ev_junction_seqs[veh_id] = junction_seq

                    v_type = "FIRE TRUCK" if "fire" in veh_id.lower() else ("POLICE" if "police" in veh_id.lower() else "AMBULANCE")
                    sev = "CRITICAL" if ("1" in veh_id or "4" in veh_id) else "HIGH"
                    prio = 1 if v_type == "AMBULANCE" else 2

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
                        "hospital": {"hospitalId": "H001", "name": "City Emergency Hospital", "speciality": v_type},
                        "route": {"routeId": f"R_{veh_id}", "edgeIds": route_edges, "junctionIds": junction_seq, "etaMinutes": 5.0}
                    }
                    master.request_emergency(request_payload, team3_response, current_time=current_time)

            # Step master controller for each junction
            for j_id in JUNCTION_PHASE_CONFIG.keys():
                tls_id = JUNCTION_PHASE_CONFIG[j_id].get("tls_id", j_id)
                dummy_j_state = {"current_phase": adapter.get_signal_phase(tls_id), "queues": {}}
                master.step(
                    junction_id=j_id,
                    tls_id=tls_id,
                    junction_state=dummy_j_state,
                    current_time=current_time,
                    traci_interface=adapter._active_interface
                )

            # Telemetry check for registered EVs
            for veh_id in sorted(registered_vehicles):
                if veh_id in active_vehs and traci.isLoaded() and veh_id in traci.vehicle.getIDList():
                    c_road = traci.vehicle.getRoadID(veh_id)
                    r_edges = ev_routes.get(veh_id, [])
                    r_idx = traci.vehicle.getRouteIndex(veh_id)
                    c_spd_ms = traci.vehicle.getSpeed(veh_id)
                    c_spd_kmh = round(c_spd_ms * 3.6, 1)
                    c_pos = round(traci.vehicle.getLanePosition(veh_id), 2)

                    next_tls = traci.vehicle.getNextTLS(veh_id)

                    if next_tls:
                        tls_id = next_tls[0][0]
                        link_idx = next_tls[0][1]
                        dist_m = round(float(next_tls[0][2]), 2)
                        sig_st = next_tls[0][3]

                        actual_phase = traci.trafficlight.getPhase(tls_id)
                        in_e, out_e = get_edges_for_j(r_edges, tls_id)
                        target_phase = get_green_phase_for_movement(tls_id, in_e, out_e) if (in_e and out_e) else -1
                        owner = master.b2_controller.junction_ownership.get(tls_id, "None")
                        b2_st = master.b2_controller.ev_state_map.get(veh_id, "N/A")
                        b2_st_name = b2_st.name if hasattr(b2_st, "name") else str(b2_st)

                        rec = {
                            "time": current_time,
                            "ev_id": veh_id,
                            "junction": tls_id,
                            "c_road": c_road,
                            "next_edge": out_e,
                            "r_idx": r_idx,
                            "pos_m": c_pos,
                            "dist_m": dist_m,
                            "speed_kmh": c_spd_kmh,
                            "b2_state": b2_st_name,
                            "owner": owner,
                            "target_phase": target_phase,
                            "actual_phase": actual_phase,
                            "link_idx": link_idx,
                            "sig_st": sig_st,
                        }

                        hk = (veh_id, tls_id)
                        if hk not in history:
                            history[hk] = []
                        history[hk].append(rec)

                        # Detect junction entry event: dist_m was > 0 and now dist_m <= 0.5 or c_road.startswith(":")
                        prev_rec = history[hk][-2] if len(history[hk]) >= 2 else None
                        
                        if prev_rec:
                            prev_dist = prev_rec["dist_m"]
                            prev_sig = prev_rec["sig_st"]
                            prev_spd = prev_rec["speed_kmh"]

                            # Detect entry moment: vehicle was before junction (prev_dist > 0) and now entering/inside (c_road.startswith(":") or dist_m < 0.5)
                            is_entering_now = (prev_dist > 0.0 and (c_road.startswith(":") or dist_m <= 0.5) and c_spd_kmh > 0.1)

                            if is_entering_now:
                                # Determine category for this entry event
                                cat = None
                                if prev_sig in ("r", "R") and sig_st in ("r", "R"):
                                    # Vehicle was BEFORE junction when link was RED, and entered while link was RED!
                                    cat = "D"
                                elif prev_sig in ("G", "g") and sig_st in ("r", "R"):
                                    # Entered on GREEN, signal changed to RED while clearing
                                    cat = "A"
                                elif prev_sig in ("r", "R") and prev_spd < 0.5 and sig_st in ("G", "g"):
                                    # Stopped on RED and correctly waited for GREEN
                                    cat = "C"
                                elif sig_st in ("G", "g"):
                                    cat = "B"
                                else:
                                    cat = "E"

                                cat_counts[cat] += 1
                                crossing_events.append({
                                    "entry_time": current_time,
                                    "ev_id": veh_id,
                                    "junction": tls_id,
                                    "category": cat,
                                    "prev_sig": prev_sig,
                                    "entry_sig": sig_st,
                                    "prev_dist": prev_dist,
                                    "curr_road": c_road,
                                    "speed": c_spd_kmh,
                                    "history_snippet": history[hk][-5:]
                                })

            if current_time >= 650.0:
                break

    finally:
        adapter.close_sim()

    print("\n" + "=" * 120)
    print(" RED LIGHT CROSSING INVESTIGATION REPORT")
    print("=" * 120)

    print("\n--- CATEGORY SUMMARY COUNTS (ALL 9 EVs) ---")
    print(f"Category A (Entered on GREEN, signal changed RED while clearing): {cat_counts['A']}")
    print(f"Category B (Exact movement GREEN, another signal head red):        {cat_counts['B']}")
    print(f"Category C (Stopped on RED, waited for GREEN before entry):        {cat_counts['C']}")
    print(f"Category D (ACTUALLY ENTERED/CROSSED ON RED):                     {cat_counts['D']}")
    print(f"Category E (Telemetry ambiguity):                                 {cat_counts['E']}")

    # Breakdown for police_2 and firetruck_3
    p2_events = [e for e in crossing_events if e["ev_id"] == "police_2"]
    ft3_events = [e for e in crossing_events if e["ev_id"] == "firetruck_3"]

    print("\n--- SPECIFIC EV BREAKDOWN: police_2 ---")
    print(f"Total Junction Crossings: {len(p2_events)}")
    for e in p2_events:
        print(f"  t={e['entry_time']:.1f}s | Junction: {e['junction']} | Entry Sig: {e['entry_sig']} | Category: {e['category']}")

    print("\n--- SPECIFIC EV BREAKDOWN: firetruck_3 ---")
    print(f"Total Junction Crossings: {len(ft3_events)}")
    for e in ft3_events:
        print(f"  t={e['entry_time']:.1f}s | Junction: {e['junction']} | Entry Sig: {e['entry_sig']} | Category: {e['category']}")

    # Category D Evidence Listing
    d_events = [e for e in crossing_events if e["category"] == "D"]
    print("\n" + "=" * 120)
    print(f" CATEGORY D (ACTUAL RED CROSSING) EVIDENCE LISTING: {len(d_events)} EVENTS FOUND")
    print("=" * 120)

    if not d_events:
        print("RESULT: ZERO (0) Category D events found! No emergency vehicle entered any junction on RED.")
    else:
        for idx, dev in enumerate(d_events, 1):
            print(f"\n[EVENT {idx}] EV: {dev['ev_id']} | Junction: {dev['junction']} | Time: {dev['entry_time']}s")
            print(f"{'Time(s)':<8} | {'EV ID':<12} | {'Junct':<6} | {'Road':<12} | {'Dist(m)':<8} | {'Spd(kmh)':<8} | {'Sig':<4} | {'ActP':<4} | {'TgtP':<4} | {'Owner':<12} | {'B2 State':<16}")
            print("-" * 110)
            for r in dev["history_snippet"]:
                print(f"{r['time']:<8.1f} | {r['ev_id']:<12} | {r['junction']:<6} | {r['c_road']:<12} | {r['dist_m']:<8.1f} | {r['speed_kmh']:<8.1f} | {r['sig_st']:<4} | {r['actual_phase']:<4} | {r['target_phase']:<4} | {r['owner']:<12} | {r['b2_state']:<16}")

    print("=" * 120 + "\n")

if __name__ == "__main__":
    run_investigation()
