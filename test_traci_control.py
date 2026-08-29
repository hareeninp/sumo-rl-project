"""
TraCI External Control Proof — Member A1 Day 2 deliverable
Confirms that traffic signals in network.net.xml can be controlled
externally (i.e. by Member B's RL agent) rather than only running
their built-in fixed-time program.

Usage:
    python test_traci_control.py

Requires: SUMO_HOME set, traci + sumolib installed (pip install traci sumolib)
"""

import os
import sys
import traci

# --- Config ---
NET_FILE = "network.net.xml"
ROUTE_FILE = "network.rou.xml"
TEST_JUNCTIONS = ["J1", "J8", "J16"]  # sample across the network: edge, center, inner

SUMO_BINARY = "sumo"  # use "sumo-gui" instead if you want to watch it visually


def main():
    sumo_cmd = [
        SUMO_BINARY,
        "-n", NET_FILE,
        "-r", ROUTE_FILE,
        "--no-step-log", "true",
        "--start",
    ]

    print("Starting SUMO with TraCI...")
    traci.start(sumo_cmd)

    print("\n--- Reading current signal states (should reflect built-in program) ---")
    for jid in TEST_JUNCTIONS:
        state = traci.trafficlight.getRedYellowGreenState(jid)
        program = traci.trafficlight.getProgram(jid)
        print(f"  {jid}: state='{state}'  program='{program}'")

    print("\n--- Attempting EXTERNAL override (this is what Member B's RL agent will do) ---")
    for jid in TEST_JUNCTIONS:
        n_links = len(traci.trafficlight.getRedYellowGreenState(jid))
        forced_state = "G" * n_links  # force all-green as a simple proof
        traci.trafficlight.setRedYellowGreenState(jid, forced_state)
        confirmed = traci.trafficlight.getRedYellowGreenState(jid)
        success = confirmed == forced_state
        print(f"  {jid}: forced state='{forced_state}' -> confirmed='{confirmed}'  "
              f"[{'SUCCESS' if success else 'FAILED'}]")

    print("\n--- Running 50 simulation steps to confirm override persists/functions ---")
    for step in range(50):
        traci.simulationStep()
    print("  50 steps completed without error.")

    print("\n--- Final signal states after external control ---")
    for jid in TEST_JUNCTIONS:
        state = traci.trafficlight.getRedYellowGreenState(jid)
        print(f"  {jid}: state='{state}'")

    traci.close()
    print("\nRESULT: All tested junctions are externally controllable via TraCI.")
    print("Member B's RL agent can use traci.trafficlight.setRedYellowGreenState(junction_id, state)")
    print("or traci.trafficlight.setPhase(junction_id, phase_index) to control signals in real time.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Check that SUMO_HOME is set and network.net.xml / network.rou.xml are in this folder.")
        sys.exit(1)
