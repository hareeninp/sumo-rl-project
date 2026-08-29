"""
test_b2.py - Comprehensive Offline Unit Tests for Team 2 - B2 Emergency System

Runs offline unit verification tests (no SUMO required) for all 18 requirements:
  1. Emergency request creation
  2. Token generation
  3. Token verification
  4. Invalid token rejection
  5. Hospital recommendation mock
  6. Route calculation mock
  7. Team 3 response parsing
  8. Emergency vehicle creation
  9. Route extraction (edgeIds)
  10. Junction sequence extraction (junctionIds)
  11. ETA calculation using mocked telemetry
  12. Emergency controller state machine transitions
  13. Emergency mode activation
  14. Green corridor sequence (J1 -> J2 -> J3)
  15. Dynamic route update (update_emergency_route)
  16. Recovery management (RecoveryManager)
  17. B1 handback logic
  18. B1/B2 ownership conflict prevention
"""

import unittest
from rl_agent.team2.token_service import generate_verification_token
from rl_agent.team2.verification import (
    register_token,
    verify_emergency_request,
    clear_token_registry,
    is_token_registered,
)
from rl_agent.team2.emergency_request import create_emergency_request
from rl_agent.team2.team3_adapter import (
    request_hospital_recommendation,
    request_route_calculation,
    request_emergency_routing,
)
from rl_agent.team2.emergency_vehicle import EmergencyVehicle
from rl_agent.team2.eta import calculate_eta
from rl_agent.team2.preemption import determine_required_phase, execute_preemption
from rl_agent.team2.recovery import RecoveryManager
from rl_agent.team2.emergency_controller import EmergencyController, EmergencyState
from rl_agent.team2.handoff import MasterSystemController
from rl_agent.team2.phase_config import JUNCTION_PHASE_CONFIG
from rl_agent.team2.traci_adapter import MockTraCIAdapter


class TestB2EmergencySystem(unittest.TestCase):

    def setUp(self):
        clear_token_registry()

    def test_01_emergency_request_creation(self):
        req = create_emergency_request(
            vehicle_id="AMB-001",
            emergency_type="TRAUMA",
            priority=1,
            start_location={"latitude": 13.0827, "longitude": 80.2707}
        )
        self.assertEqual(req["vehicleId"], "AMB-001")
        self.assertEqual(req["vehicleType"], "AMBULANCE")
        self.assertEqual(req["emergencyType"], "TRAUMA")
        self.assertEqual(req["priority"], 1)
        self.assertIn("verificationToken", req)
        self.assertTrue(len(req["verificationToken"]) > 10)

    def test_02_token_generation(self):
        tok1 = generate_verification_token()
        tok2 = generate_verification_token()
        self.assertNotEqual(tok1, tok2)
        self.assertTrue(isinstance(tok1, str))

    def test_03_token_verification(self):
        req = create_emergency_request("AMB-001")
        valid = verify_emergency_request(req)
        self.assertTrue(valid)

    def test_04_invalid_token_rejection(self):
        fake_req = {
            "vehicleId": "AMB-999",
            "verificationToken": "invalid-unregistered-token-12345"
        }
        valid = verify_emergency_request(fake_req)
        self.assertFalse(valid)

    def test_05_hospital_recommendation_mock(self):
        req = create_emergency_request("AMB-001", emergency_type="TRAUMA")
        resp = request_hospital_recommendation(req, use_mock=True)
        self.assertTrue(resp["success"])
        hosp = resp["data"]["recommendedHospital"]
        self.assertEqual(hosp["hospitalId"], "H001")
        self.assertEqual(hosp["speciality"], "TRAUMA")

    def test_06_route_calculation_mock(self):
        req = create_emergency_request("AMB-001")
        resp = request_route_calculation(req, hospital_id="H001", use_mock=True)
        self.assertTrue(resp["success"])
        data = resp["data"]
        self.assertEqual(data["routeId"], "R001")
        self.assertEqual(data["junctionIds"], ["J1", "J2", "J3"])

    def test_07_team3_response_parsing(self):
        req = create_emergency_request("AMB-001", emergency_type="CARDIAC")
        team3_resp = request_emergency_routing(req, use_mock=True)

        self.assertIn("hospital", team3_resp)
        self.assertIn("route", team3_resp)
        self.assertEqual(team3_resp["hospital"]["hospitalId"], "H001")
        self.assertEqual(team3_resp["route"]["junctionIds"], ["J1", "J2", "J3"])

    def test_08_emergency_vehicle_creation(self):
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)

        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)
        self.assertEqual(amb.vehicle_id, "AMB-001")
        self.assertEqual(amb.hospital_id, "H001")
        self.assertEqual(amb.verification_token, req["verificationToken"])

    def test_09_route_extraction_edge_ids(self):
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)
        self.assertEqual(amb.edge_ids, ["edge_01", "edge_05", "edge_08"])

    def test_10_junction_sequence_extraction(self):
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)
        self.assertEqual(amb.junction_ids, ["J1", "J2", "J3"])
        self.assertEqual(amb.route, ["J1", "J2", "J3"])

    def test_11_eta_calculation(self):
        amb = EmergencyVehicle(vehicle_id="AMB-001", junction_ids=["J1", "J2", "J3"], speed=15.0)
        eta1 = calculate_eta(amb, "J1")
        eta2 = calculate_eta(amb, "J2")
        eta3 = calculate_eta(amb, "J3")

        self.assertGreater(eta1, 0)
        self.assertGreater(eta2, eta1)
        self.assertGreater(eta3, eta2)

    def test_12_state_machine_transitions(self):
        ctrl = EmergencyController(phase_config=JUNCTION_PHASE_CONFIG)
        self.assertEqual(ctrl.state, EmergencyState.NORMAL)

        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)

        ctrl.register_emergency(amb, req, current_time=0.0)
        self.assertEqual(ctrl.state, EmergencyState.EMERGENCY_DETECTED)

        # Step 1 -> VERIFICATION
        state = ctrl.step(1.0)
        self.assertEqual(state, EmergencyState.VERIFICATION)

        # Step 2 -> PREEMPTION
        state = ctrl.step(2.0)
        self.assertEqual(state, EmergencyState.PREEMPTION)

        # Step 3 -> GREEN_CORRIDOR
        state = ctrl.step(3.0)
        self.assertEqual(state, EmergencyState.GREEN_CORRIDOR)

    def test_13_emergency_mode_activation(self):
        master = MasterSystemController()
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)

        res = master.request_emergency(req, team3_resp, current_time=0.0)
        self.assertTrue(res)
        self.assertEqual(master.system_mode, "EMERGENCY")

    def test_14_green_corridor_sequence(self):
        ctrl = EmergencyController(phase_config=JUNCTION_PHASE_CONFIG)
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)

        ctrl.register_emergency(amb, req, current_time=0.0)
        ctrl.step(1.0)  # VERIFICATION
        ctrl.step(2.0)  # PREEMPTION J1
        ctrl.step(3.0)  # GREEN_CORRIDOR J1

        self.assertEqual(ctrl.route, ["J1", "J2", "J3"])

    def test_15_dynamic_route_update(self):
        ctrl = EmergencyController(phase_config=JUNCTION_PHASE_CONFIG)
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        amb = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)

        ctrl.register_emergency(amb, req, current_time=0.0)
        updated = ctrl.update_emergency_route("AMB-001", ["J1", "J4", "J7"], ["edge_01", "edge_04", "edge_07"])
        self.assertTrue(updated)
        self.assertEqual(ctrl.route, ["J1", "J4", "J7"])
        self.assertEqual(amb.edge_ids, ["edge_01", "edge_04", "edge_07"])

    def test_16_recovery_manager(self):
        rec_mgr = RecoveryManager()
        flush_time = rec_mgr.calculate_flush_time({"cross_1": 10, "cross_2": 5})
        self.assertGreaterEqual(flush_time, 10.0)

    def test_17_b1_handback(self):
        master = MasterSystemController()
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)

        master.request_emergency(req, team3_resp, current_time=0.0)
        dummy_state = {"current_phase": 0, "queues": {"lane_N_0": 2, "lane_E_0": 4}}

        # Simulate steps through emergency lifecycle until handback
        for t in range(1, 20):
            master.step("J1", "TEMP_TLS_J1", dummy_state, current_time=float(t * 5))

        self.assertEqual(master.system_mode, "NORMAL")

    def test_18_ownership_conflict_prevention(self):
        master = MasterSystemController()
        dummy_state = {"current_phase": 0, "queues": {"lane_N_0": 2, "lane_E_0": 4}}

        # In NORMAL mode -> active controller is B1
        res_normal = master.step("J1", "TEMP_TLS_J1", dummy_state)
        self.assertEqual(res_normal["active_controller"], "B1")

        # Initiate EMERGENCY mode
        req = create_emergency_request("AMB-001")
        team3_resp = request_emergency_routing(req, use_mock=True)
        master.request_emergency(req, team3_resp)

        # In EMERGENCY mode -> active controller is strictly B2
        res_emerg = master.step("J1", "TEMP_TLS_J1", dummy_state, current_time=1.0)
        self.assertEqual(res_emerg["active_controller"], "B2")

    def test_19_movement_to_green_phase_lookup(self):
        phase_hosp1 = determine_required_phase("J1", vehicle_approach_edge="HOSP1_J1", to_edge="J1_J6")
        self.assertEqual(phase_hosp1, 0)

        phase_home1 = determine_required_phase("J1", vehicle_approach_edge="HOME1_J1", to_edge="J1_J2")
        self.assertEqual(phase_home1, 4)

    def test_20_safe_preemption_transition_execution(self):
        mock_provider = MockTraCIAdapter()
        res = execute_preemption("J1", "TLS_J1", target_phase=4, traci_interface=mock_provider)
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
