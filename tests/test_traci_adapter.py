"""
test_traci_adapter.py - Unit Tests for Decoupled TraCI Adapter

Tests:
  1. MockTraCIAdapter fallback functions
  2. TraCIAdapter unified interface
  3. External provider injection (set_traci_provider)
  4. Isolation of Team 2 from physical traci.py location
"""

import unittest
from rl_agent.team2.traci_adapter import (
    TraCIAdapter,
    MockTraCIAdapter,
    set_traci_provider,
    get_traci_adapter,
)


class DummyCustomProvider:
    """Mock external provider simulating Team 1's TraCI implementation."""

    def __init__(self):
        self.started = False
        self.forced_phase = -1

    def start_sim(self, sumocfg_path: str = ""):
        self.started = True

    def force_phase_change(self, tls_id: str, target_phase: int):
        self.forced_phase = target_phase

    def get_signal_phase(self, tls_id: str) -> int:
        return 5

    def get_vehicle_speed(self, vehicle_id: str) -> float:
        return 22.0


class TestTraCIAdapter(unittest.TestCase):

    def setUp(self):
        # Reset injected provider before each test
        set_traci_provider(None)

    def tearDown(self):
        set_traci_provider(None)

    def test_01_mock_adapter_fallback(self):
        adapter = get_traci_adapter()
        self.assertTrue(isinstance(adapter._mock_fallback, MockTraCIAdapter))

        adapter.start_sim("scenario.sumocfg")
        self.assertTrue(adapter._mock_fallback.sim_running)

        adapter.force_phase_change("TLS_J1", 4)
        self.assertEqual(adapter.get_signal_phase("TLS_J1"), 4)

        state = adapter.get_junction_state("J1", "TLS_J1", ["lane_1", "lane_2"])
        self.assertEqual(state["junction_id"], "J1")
        self.assertIn("queues", state)

        adapter.close_sim()
        self.assertFalse(adapter._mock_fallback.sim_running)

    def test_02_external_provider_injection(self):
        custom_provider = DummyCustomProvider()
        set_traci_provider(custom_provider)

        adapter = get_traci_adapter()
        adapter.start_sim("test.sumocfg")
        self.assertTrue(custom_provider.started)

        adapter.force_phase_change("TLS_J1", 8)
        self.assertEqual(custom_provider.forced_phase, 8)

        phase = adapter.get_signal_phase("TLS_J1")
        self.assertEqual(phase, 5)

        speed = adapter.get_vehicle_speed("AMB-001")
        self.assertEqual(speed, 22.0)

    def test_03_instance_override_injection(self):
        custom_provider = DummyCustomProvider()
        adapter = TraCIAdapter(provider=custom_provider)

        adapter.force_phase_change("TLS_J2", 3)
        self.assertEqual(custom_provider.forced_phase, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
