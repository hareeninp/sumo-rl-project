"""
test_multi_ev_arbitration.py - Unit Tests for 3-Tier Multi-EV Priority Arbitration & Queueing

Tests:
  1. 3-Tier Priority Ordering:
     - Tier 1: Emergency severity (CRITICAL > HIGH > NORMAL)
     - Tier 2: Vehicle type (FIRE TRUCK > AMBULANCE > POLICE)
     - Tier 3: ETA / Request time (lower ETA / earlier request time)
  2. Examples:
     - CRITICAL AMBULANCE > HIGH FIRE TRUCK
     - HIGH FIRE TRUCK > HIGH AMBULANCE
     - HIGH AMBULANCE > HIGH POLICE
  3. Safe default to NORMAL when severity/priority is missing or invalid.
  4. Continuous detection & pending queue ordering in EmergencyController.
"""

import unittest
from rl_agent.team2.emergency_vehicle import EmergencyVehicle
from rl_agent.team2.emergency_request import create_emergency_request
from rl_agent.team2.emergency_controller import EmergencyController, EmergencyState
from rl_agent.team2.verification import clear_token_registry


class TestMultiEVArbitration(unittest.TestCase):

    def setUp(self):
        clear_token_registry()

    def test_01_tier1_severity_ordering(self):
        v1 = EmergencyVehicle(vehicle_id="AMB-CRIT", vehicle_type="AMBULANCE", severity="CRITICAL")
        v2 = EmergencyVehicle(vehicle_id="FIRE-HIGH", vehicle_type="FIRE TRUCK", severity="HIGH")

        # CRITICAL AMBULANCE > HIGH FIRE TRUCK
        key1 = (-v1.severity_rank, -v1.vehicle_type_rank, v1.request_time)
        key2 = (-v2.severity_rank, -v2.vehicle_type_rank, v2.request_time)
        self.assertLess(key1, key2)

    def test_02_tier2_vehicle_type_ordering(self):
        v1 = EmergencyVehicle(vehicle_id="FIRE-HIGH", vehicle_type="FIRE TRUCK", severity="HIGH")
        v2 = EmergencyVehicle(vehicle_id="AMB-HIGH", vehicle_type="AMBULANCE", severity="HIGH")
        v3 = EmergencyVehicle(vehicle_id="POLICE-HIGH", vehicle_type="POLICE", severity="HIGH")

        key_fire = (-v1.severity_rank, -v1.vehicle_type_rank, v1.request_time)
        key_amb = (-v2.severity_rank, -v2.vehicle_type_rank, v2.request_time)
        key_police = (-v3.severity_rank, -v3.vehicle_type_rank, v3.request_time)

        # HIGH FIRE TRUCK > HIGH AMBULANCE > HIGH POLICE
        self.assertLess(key_fire, key_amb)
        self.assertLess(key_amb, key_police)

    def test_03_tier3_eta_ordering(self):
        v1 = EmergencyVehicle(vehicle_id="AMB-EARLY", vehicle_type="AMBULANCE", severity="HIGH", overall_eta_minutes=2.0)
        v2 = EmergencyVehicle(vehicle_id="AMB-LATE", vehicle_type="AMBULANCE", severity="HIGH", overall_eta_minutes=8.0)

        key1 = (-v1.severity_rank, -v1.vehicle_type_rank, v1.overall_eta_minutes)
        key2 = (-v2.severity_rank, -v2.vehicle_type_rank, v2.overall_eta_minutes)

        self.assertLess(key1, key2)

    def test_04_missing_severity_default(self):
        req = {"vehicleId": "UNK-001"}
        team3_resp = {"hospital": {}, "route": {}}
        v = EmergencyVehicle.from_request_and_team3_response(req, team3_resp)

        self.assertEqual(v.severity, "NORMAL")
        self.assertEqual(v.severity_rank, 1)

    def test_05_controller_queue_sorting(self):
        ctrl = EmergencyController()
        
        v_active = EmergencyVehicle(vehicle_id="V_ACTIVE", junction_ids=["J1"], severity="NORMAL", vehicle_type="POLICE")
        v_crit_amb = EmergencyVehicle(vehicle_id="V_CRIT_AMB", junction_ids=["J1"], severity="CRITICAL", vehicle_type="AMBULANCE")
        v_high_fire = EmergencyVehicle(vehicle_id="V_HIGH_FIRE", junction_ids=["J1"], severity="HIGH", vehicle_type="FIRE TRUCK")

        ctrl.register_emergency(v_active)
        ctrl.register_emergency(v_high_fire)
        ctrl.register_emergency(v_crit_amb)

        # Active vehicle is V_ACTIVE
        self.assertEqual(ctrl.active_vehicle.vehicle_id, "V_ACTIVE")

        # Queue should be sorted: V_CRIT_AMB (Tier 1 CRITICAL) before V_HIGH_FIRE (Tier 1 HIGH)
        self.assertEqual(len(ctrl.pending_queue), 2)
        self.assertEqual(ctrl.pending_queue[0].vehicle_id, "V_CRIT_AMB")
        self.assertEqual(ctrl.pending_queue[1].vehicle_id, "V_HIGH_FIRE")


if __name__ == "__main__":
    unittest.main()
