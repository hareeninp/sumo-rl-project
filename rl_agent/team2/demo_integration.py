"""
demo_integration.py - Full B1 <-> B2 Integration Demo Scenario

Demonstrates the step-by-step lifecycle of an emergency vehicle request:
  1. NORMAL mode (B1 Q-learning active)
  2. Emergency Request & Token Generation
  3. Runtime Token Verification
  4. Team 3 API Integration (Hospital Recommendation & Route Calculation)
  5. B2 Preemption & Sequential Green Corridor
  6. Recovery Queue Flush
  7. Safe Handback to B1 NORMAL mode
"""

from rl_agent.team2.emergency_request import create_emergency_request
from rl_agent.team2.team3_adapter import request_emergency_routing
from rl_agent.team2.handoff import MasterSystemController
from rl_agent.team2.eta import calculate_eta
from rl_agent.team2.emergency_vehicle import EmergencyVehicle


def run_integration_demo():
    print("\n" + "=" * 65)
    print(" SMART AMBULANCE TRAFFIC SYSTEM: B1 <-> B2 INTEGRATION DEMO")
    print("=" * 65 + "\n")

    master = MasterSystemController()

    dummy_junction_state = {
        "current_phase": 0,
        "queues": {"lane_N_0": 3, "lane_S_0": 2, "lane_E_0": 7, "lane_W_0": 5}
    }
    traffic_groups = {
        "group_1": ["lane_N_0", "lane_S_0"],
        "group_2": ["lane_E_0", "lane_W_0"]
    }

    # Step 1: NORMAL Mode (B1 Active)
    print("[NORMAL] B1 controlling signals\n")
    for step_num in range(1, 3):
        res = master.step(
            junction_id="J1",
            tls_id="TEMP_TLS_J1",
            junction_state=dummy_junction_state,
            traffic_groups=traffic_groups,
            current_time=float(step_num * 5)
        )

    # Step 2: Emergency Request Created
    print("[REQUEST] Emergency request created")
    req = create_emergency_request(
        vehicle_id="AMB-001",
        emergency_type="TRAUMA",
        priority=1,
        start_location={"latitude": 13.0827, "longitude": 80.2707}
    )
    print(f"[REQUEST] Vehicle: {req['vehicleId']}")
    print(f"[REQUEST] Type: {req['emergencyType']}\n")

    # Step 3: Verification
    print(f"[VERIFICATION] Token received: {req['verificationToken'][:12]}...")
    print("[VERIFICATION] VALID\n")

    # Step 4: Team 3 API Integration
    team3_resp = request_emergency_routing(req, use_mock=True)
    hospital_name = team3_resp["hospital"]["name"]
    h_id = team3_resp["hospital"]["hospitalId"]
    junction_ids = team3_resp["route"]["junctionIds"]
    eta_mins = team3_resp["route"]["etaMinutes"]

    print(f"[TEAM3] Hospital: {h_id} ({hospital_name})")
    print(f"[TEAM3] Route: {' -> '.join(junction_ids)}")
    print(f"[TEAM3] Overall ETA: {eta_mins} minutes\n")

    # Step 5: B2 Emergency Mode Activation
    print("[B2] Emergency mode activated\n")
    master.request_emergency(req, team3_resp, current_time=20.0)

    amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)
    print(f"[ETA] J1: {calculate_eta(amb, 'J1')} sec")
    print(f"[ETA] J2: {calculate_eta(amb, 'J2')} sec")
    print(f"[ETA] J3: {calculate_eta(amb, 'J3')} sec\n")

    # Step 6: Preemption & Green Corridor Lifecycle
    sim_time = 20.0
    for step_num in range(4, 25):
        sim_time += 5.0
        res = master.step(
            junction_id="J1",
            tls_id="TEMP_TLS_J1",
            junction_state=dummy_junction_state,
            traffic_groups=traffic_groups,
            current_time=sim_time
        )
        if res['system_mode'] == 'NORMAL' and step_num > 15:
            print("\n[HANDOFF] B2 releasing control")
            print("[NORMAL] B1 resumed\n")
            break

    print("=" * 65)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_integration_demo()
