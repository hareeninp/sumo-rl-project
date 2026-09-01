"""
test_reward_signal.py - Diagnostic Script Verifying Real SUMO State & Reward Generation

Verifies that raw SUMO queue measurements, discrete RL state tuples, and reward signals
are correctly calculated during live TraCI simulation steps.
"""

import os
import sys

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rl_agent.team2.phase_config import get_junction_config, get_valid_green_phases
from rl_agent.team2.state import get_rl_state, get_total_queue
from rl_agent.team2.reward import calculate_reward
from rl_agent.team2.traci_adapter import get_traci_adapter, set_traci_provider, TraCIAdapter


def run_reward_signal_test(
    sumocfg_path: str = "A1_network/network.sumocfg",
    junction_key: str = "J1",
    total_steps: int = 200,
    interval: int = 5
) -> None:
    print("\n" + "=" * 70)
    print(" DIAGNOSTIC TEST: SUMO STATE & REWARD SIGNAL PIPELINE")
    print(f" Junction: {junction_key} | Config: {sumocfg_path} | Steps: {total_steps}")
    print("=" * 70 + "\n")

    # Connect Team 1's traci_interface if available
    try:
        from traci_interface import traci_interface
        set_traci_provider(traci_interface)
        print("[INIT] Connected Team 1 traci_interface provider.")
    except ImportError:
        print("[INIT] Running with MockTraCIAdapter fallback.")

    adapter: TraCIAdapter = get_traci_adapter()

    # Load junction configuration
    j_config = get_junction_config(junction_key)
    if not j_config:
        raise KeyError(f"Junction '{junction_key}' not found in phase configuration.")

    tls_id = j_config.get("tls_id", junction_key)
    green_phases = get_valid_green_phases(junction_key)
    traffic_groups = j_config.get("traffic_groups", {})

    all_lanes = []
    for lane_list in traffic_groups.values():
        all_lanes.extend(lane_list)

    print(f"[CONFIG] Controlled Lanes for {junction_key}: {all_lanes}")
    print(f"[CONFIG] Green Phases: {green_phases}\n")

    # Start simulation
    resolved_cfg = os.path.abspath(sumocfg_path) if not os.path.isabs(sumocfg_path) else sumocfg_path
    adapter.start_sim(resolved_cfg)

    prev_total_queue = 0
    non_zero_queues_count = 0
    non_zero_rewards_count = 0

    try:
        # Step simulation and evaluate every interval steps
        for step in range(1, total_steps + 1):
            adapter.step()

            if step % interval == 0:
                raw_state = adapter.get_junction_state(junction_key, tls_id, all_lanes)
                current_phase = raw_state.get("current_phase", 0)

                current_total_queue = get_total_queue(raw_state, all_lanes)
                rl_state = get_rl_state(
                    raw_state,
                    traffic_groups=traffic_groups,
                    valid_green_phases=green_phases
                )

                if step == interval:
                    # Initial step baseline
                    reward = 0.0
                else:
                    reward = calculate_reward(prev_total_queue, current_total_queue)

                if current_total_queue > 0:
                    non_zero_queues_count += 1
                if reward != 0.0:
                    non_zero_rewards_count += 1

                print(
                    f"Time: {step:3d}s | "
                    f"Phase: {current_phase:2d} | "
                    f"Total Queue: {current_total_queue:2d} | "
                    f"RL State: {rl_state} | "
                    f"Reward: {reward:+5.1f}"
                )

                prev_total_queue = current_total_queue

    finally:
        adapter.close_sim()
        print("\n" + "=" * 70)
        print(" DIAGNOSTIC TEST COMPLETE")
        print(f" Steps with Non-Zero Queues:  {non_zero_queues_count}")
        print(f" Steps with Non-Zero Rewards: {non_zero_rewards_count}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    run_reward_signal_test()
