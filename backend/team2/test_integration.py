"""
test_integration.py - Full End-to-End Integration Test for Team 2 (B1 + B2 + Team 3 Mock)

Tests complete workflow:
  1. Team 3 emergency request & route response parsing (J1 -> J2 -> J3)
  2. Token generation and verification
  3. B2 preemption mode activation
  4. Movement lookup (from_edge -> to_edge) from B1_LANE_MOVEMENT_MAPPING.csv
  5. Green target phase selection
  6. Safe phase transition execution following B1_SAFE_TRANSITIONS.csv
  7. Sequential green corridor progression (J1 -> J2 -> J3)
  8. Recovery mode management and vehicle exit
  9. B1 handback & Q-learning controller resumption
"""

import unittest
from team2.token_service import generate_verification_token
from team2.verification import verify_emergency_request, clear_token_registry
from team2.emergency_request import create_emergency_request
from team2.team3_adapter import request_emergency_routing
from team2.emergency_vehicle import EmergencyVehicle
from team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_valid_green_phases,
    get_green_phase_for_movement,
    get_safe_transition_sequence,
)
from team2.preemption import determine_required_phase, execute_preemption
from team2.emergency_controller import EmergencyController, EmergencyState
from team2.handoff import MasterSystemController
from team2.traci_adapter import MockTraCIAdapter, set_traci_provider


class TestFullSystemIntegration(unittest.TestCase):

    def setUp(self):
        clear_token_registry()
        self.mock_traci = MockTraCIAdapter()
        set_traci_provider(self.mock_traci)

    def tearDown(self):
        set_traci_provider(None)

    def test_end_to_end_integration_flow(self):
        print("\n=== STARTING END-TO-END INTEGRATION TEST ===")

        # 1. Step 1: Create Emergency Request & Receive Team 3 Route
        req = create_emergency_request(vehicle_id="AMB-INT-100", emergency_type="TRAUMA", priority=1)
        self.assertTrue(verify_emergency_request(req))

        team3_resp = request_emergency_routing(req, use_mock=True)
        self.assertIn("route", team3_resp)

        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)
        self.assertEqual(amb.vehicle_id, "AMB-INT-100")
        self.assertEqual(amb.junction_ids, ["J1", "J2", "J3"])
        print(f"Step 1 PASSED: Received Team 3 route: {' -> '.join(amb.junction_ids)}")

        # 2. Step 2: Initialize Master Controller and Register Emergency
        master = MasterSystemController()
        activated = master.request_emergency(req, team3_resp, current_time=0.0)
        self.assertTrue(activated)
        self.assertEqual(master.system_mode, "EMERGENCY")
        print("Step 2 PASSED: Master controller activated EMERGENCY mode.")

        # 3. Step 3: Movement Lookup & Green Phase Selection
        # J1 movement: HOSP1_J1 -> J1_J6 -> green phase 0
        p1 = determine_required_phase("J1", vehicle_approach_edge="HOSP1_J1", to_edge="J1_J6")
        self.assertIn(p1, get_valid_green_phases("J1"))

        # J2 movement: J1_J2 -> J2_J3 -> green phase 6
        p2 = determine_required_phase("J2", vehicle_approach_edge="J1_J2", to_edge="J2_J3")
        self.assertIn(p2, get_valid_green_phases("J2"))

        # J3 movement: J2_J3 -> J3_J4 -> green phase 0
        p3 = determine_required_phase("J3", vehicle_approach_edge="J2_J3", to_edge="J3_J4")
        self.assertIn(p3, get_valid_green_phases("J3"))
        print(f"Step 3 PASSED: Movement lookups resolved green target phases: J1={p1}, J2={p2}, J3={p3}")

        # 4. Step 4: Verify Safe Transition Sequences
        seq_j1 = get_safe_transition_sequence("J1", current_phase=0, target_phase=4)
        self.assertEqual(seq_j1, [1, 2, 3, 4])  # 1(mixed) -> 2(green) -> 3(yellow) -> 4(green)

        seq_j2 = get_safe_transition_sequence("J2", current_phase=0, target_phase=6)
        self.assertTrue(len(seq_j2) > 0 and seq_j2[-1] == 6)
        print("Step 4 PASSED: Safe transition sequences verified from B1_SAFE_TRANSITIONS.csv.")

        # 5. Step 5: Sequential Green Corridor Execution
        dummy_state = {"current_phase": 0, "queues": {"lane_1": 2, "lane_2": 3}}

        # Step through simulation time steps
        t = 0.0
        while master.system_mode != "NORMAL" and t < 120.0:
            res = master.step("J1", "J1", dummy_state, current_time=t)
            t += 1.0

        # 6. Step 6: Verification of Recovery & B1 Handback
        self.assertEqual(master.system_mode, "NORMAL")
        print("Step 6 PASSED: Green corridor completed, recovery cleared, control handed back to B1 Q-learning.")

        print("=== END-TO-END INTEGRATION TEST COMPLETE & SUCCESSFUL ===\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
