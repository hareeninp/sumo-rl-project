"""
test_team3_api_integration.py - Integration Test for Team 3 REST API Endpoints

Verifies all 7 REST API endpoints exposed by Team 2's Flask API server (rl_agent/team2/api_server.py):
  1. GET  /api/health
  2. GET  /api/network
  3. POST /api/simulation/start
  4. POST /api/simulation/step
  5. GET  /api/traffic
  6. GET  /api/vehicles
  7. POST /api/simulation/stop

Verifies:
  - Simulation time increases after stepping
  - Live traffic & vehicle telemetry are returned while running
  - /api/traffic returns HTTP 200 after simulation stops
"""

import os
import sys
import time
import json
import unittest
import threading
import urllib.request
import urllib.error

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rl_agent.team2.api_server import app

API_HOST = "127.0.0.1"
API_PORT = 5000
BASE_URL = f"http://{API_HOST}:{API_PORT}"


class TestTeam3APIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Starts Flask API server on a background daemon thread."""
        cls.server_thread = threading.Thread(
            target=app.run,
            kwargs={"host": API_HOST, "port": API_PORT, "debug": False, "use_reloader": False},
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1.0)  # Wait for Flask server to initialize

    def _get(self, endpoint: str):
        url = BASE_URL + endpoint
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            return data

    def _post(self, endpoint: str, payload: dict = None):
        url = BASE_URL + endpoint
        data_bytes = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            return data

    def test_full_team3_api_workflow(self):
        # 1. Check Health (Stopped State)
        health_stopped = self._get("/api/health")
        print("\n[TEST 1] GET /api/health (Stopped):", health_stopped)
        self.assertTrue(health_stopped.get("success"))
        self.assertEqual(health_stopped.get("status"), "online")
        self.assertFalse(health_stopped.get("simulationRunning"))

        # 2. Get Network Topology
        network_data = self._get("/api/network")
        print("[TEST 2] GET /api/network:", f"Junctions={len(network_data.get('junctions', []))}, Roads={len(network_data.get('roads', []))}")
        self.assertTrue(network_data.get("success"))
        self.assertGreater(len(network_data.get("junctions", [])), 0)
        self.assertIn("junctions", network_data)
        self.assertIn("roads", network_data)
        self.assertIn("trafficLights", network_data)

        # 3. Start SUMO Simulation
        start_res = self._post("/api/simulation/start", {"gui": False, "sumocfg": "A1_network/cfg_multi_ev.sumocfg"})
        print("[TEST 3] POST /api/simulation/start:", start_res)
        self.assertTrue(start_res.get("success"))

        # 4. Check Health (Running State)
        health_running = self._get("/api/health")
        print("[TEST 4] GET /api/health (Running):", health_running)
        self.assertTrue(health_running.get("success"))
        self.assertTrue(health_running.get("simulationRunning"))

        # 5. Step Simulation & Verify Time Increases
        initial_time = health_running.get("simulationTime", 0.0)
        step_res = self._post("/api/simulation/step", {"steps": 5, "junctionId": "J1"})
        print("[TEST 5] POST /api/simulation/step:", step_res)
        self.assertTrue(step_res.get("success"))
        stepped_time = step_res.get("simulationTime", 0.0)
        self.assertGreater(stepped_time, initial_time)
        print(f"         Verified simulation time increased: {initial_time}s -> {stepped_time}s")

        # 6. Get Traffic (Running State)
        traffic_running = self._get("/api/traffic")
        print("[TEST 6] GET /api/traffic (Running):", f"Count={len(traffic_running.get('traffic', []))}, J1 nextSwitch={traffic_running['traffic'][0]['nextSwitch']}")
        self.assertTrue(traffic_running.get("success"))
        self.assertTrue(traffic_running.get("simulationRunning"))
        self.assertGreater(len(traffic_running.get("traffic", [])), 0)
        j1_traffic = traffic_running["traffic"][0]
        self.assertIn("signalPhase", j1_traffic)
        self.assertIn("signalState", j1_traffic)
        self.assertIn("nextSwitch", j1_traffic)
        self.assertIn("vehicleCount", j1_traffic)
        self.assertIn("queueLength", j1_traffic)

        # 7. Get Vehicles (Running State)
        vehicles_running = self._get("/api/vehicles")
        print("[TEST 7] GET /api/vehicles (Running):", f"Active Vehicles Count={vehicles_running.get('count')}")
        self.assertTrue(vehicles_running.get("success"))
        self.assertTrue(vehicles_running.get("simulationRunning"))
        self.assertIn("vehicles", vehicles_running)

        # 8. Stop SUMO Simulation
        stop_res = self._post("/api/simulation/stop", {})
        print("[TEST 8] POST /api/simulation/stop:", stop_res)
        self.assertTrue(stop_res.get("success"))

        # 9. Verify /api/traffic still returns HTTP 200 after SUMO stops
        traffic_stopped = self._get("/api/traffic")
        print("[TEST 9] GET /api/traffic (Stopped):", f"HTTP 200 OK, success={traffic_stopped.get('success')}, simRunning={traffic_stopped.get('simulationRunning')}")
        self.assertTrue(traffic_stopped.get("success"))
        self.assertFalse(traffic_stopped.get("simulationRunning"))
        self.assertGreater(len(traffic_stopped.get("traffic", [])), 0)

        print("\nALL 9 TEAM 3 API INTEGRATION VERIFICATIONS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    unittest.main()
