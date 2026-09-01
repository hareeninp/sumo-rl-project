"""
evaluate.py - Evaluation & Configurable Fixed-Timer Baseline Benchmarking

Evaluates a trained Tabular Q-Learning policy (epsilon=0) and provides
a Fixed-Timer Baseline controller cycling through junction-specific green phases
via the decoupled TraCI adapter.
"""

import os
import sys
import argparse
from typing import Dict, List, Any, Optional

# Import Team 2 modules
from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_junction_config,
    is_rl_enabled,
    get_valid_green_phases,
    map_action_index_to_sumo_phase,
)
from rl_agent.team2.state import get_rl_state, get_total_queue
from rl_agent.team2.q_learning import QLearningAgent
from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter


class FixedTimerController:
    """
    Fixed-Timer Baseline controller cycling sequentially through a junction's
    configured green phases (e.g. 0 -> 3 -> 6 -> 8 -> 11 -> 0).
    """

    def __init__(self, green_phases: List[int], switch_interval_steps: int = 30):
        self.green_phases = green_phases if green_phases else [0]
        self.switch_interval_steps = switch_interval_steps
        self.steps_in_current_phase = 0
        self.current_idx = 0

    def get_action_index(self) -> int:
        self.steps_in_current_phase += 5  # assuming decision interval = 5
        if self.steps_in_current_phase >= self.switch_interval_steps:
            self.steps_in_current_phase = 0
            self.current_idx = (self.current_idx + 1) % len(self.green_phases)
        return self.current_idx


def evaluate_policy(
    sumocfg_path: str,
    junction_key: str = "J1",
    model_path: str = "team2_q_table.json",
    steps_per_episode: int = 3600,
    decision_interval: int = 5,
    mode: str = "qlearning",
    fixed_green_duration: int = 30,
    traci_interface: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Evaluates either a trained Q-learning policy or a fixed-timer baseline controller.
    """
    adapter: TraCIAdapter = get_traci_adapter(traci_interface)

    j_config = get_junction_config(junction_key)
    if not j_config:
        raise KeyError(f"Junction '{junction_key}' not found in JUNCTION_PHASE_CONFIG.")

    tls_id = j_config.get("tls_id", junction_key)
    green_phases = get_valid_green_phases(junction_key)
    traffic_groups = j_config.get("traffic_groups", {})
    rl_enabled = is_rl_enabled(junction_key)

    all_lanes: List[str] = []
    for lane_list in traffic_groups.values():
        all_lanes.extend(lane_list)

    print(f"=== Starting Evaluation ({mode.upper()} mode) ===")
    print(f"Junction: {junction_key} | Green Phases: {green_phases} | RL Enabled: {rl_enabled}")

    if mode == "qlearning":
        agent = QLearningAgent(action_space=len(green_phases))
        if os.path.exists(model_path):
            agent.load(model_path)
            print(f"Loaded trained model from: {model_path}")
        else:
            print(f"WARNING: Model file {model_path} not found. Running with un-trained agent.")
        agent.epsilon = 0.0  # Exploitation only
        controller = agent
    elif mode == "fixed":
        controller = FixedTimerController(green_phases=green_phases, switch_interval_steps=fixed_green_duration)
        print(f"Running Fixed-Timer Baseline (Green Duration = {fixed_green_duration}s)")
    else:
        raise ValueError(f"Unknown evaluation mode '{mode}'. Choose 'qlearning' or 'fixed'.")

    queue_history: List[int] = []
    step_counter = 0

    adapter.start_sim(sumocfg_path)

    raw_state = adapter.get_junction_state(junction_key, tls_id, all_lanes)
    current_rl_state = get_rl_state(raw_state, traffic_groups=traffic_groups, valid_green_phases=green_phases)

    while step_counter < steps_per_episode:
        current_queue = get_total_queue(raw_state, all_lanes)
        queue_history.append(current_queue)

        if rl_enabled:
            if mode == "qlearning":
                action_idx = controller.choose_action(current_rl_state)
            else:
                action_idx = controller.get_action_index()

            target_sumo_phase = map_action_index_to_sumo_phase(junction_key, action_idx)
            adapter.force_phase_change(tls_id, target_sumo_phase)

        for _ in range(decision_interval):
            adapter.step()
            step_counter += 1
            if step_counter >= steps_per_episode:
                break

        raw_state = adapter.get_junction_state(junction_key, tls_id, all_lanes)
        current_rl_state = get_rl_state(raw_state, traffic_groups=traffic_groups, valid_green_phases=green_phases)

    adapter.close_sim()

    total_queue = sum(queue_history)
    avg_queue = total_queue / len(queue_history) if queue_history else 0.0
    max_queue = max(queue_history) if queue_history else 0

    metrics = {
        "mode": mode,
        "total_steps": step_counter,
        "decision_points": len(queue_history),
        "total_queue": total_queue,
        "average_queue": avg_queue,
        "max_queue": max_queue,
    }

    print("\n" + "=" * 45)
    print(f" EVALUATION SUMMARY ({mode.upper()} MODE)")
    print("=" * 45)
    print(f" Total Simulation Steps : {step_counter}")
    print(f" Total Decision Points  : {len(queue_history)}")
    print(f" Accumulated Queue      : {total_queue}")
    print(f" Average Queue / Step   : {avg_queue:.2f} vehicles")
    print(f" Maximum Queue Observed : {max_queue} vehicles")
    print("=" * 45 + "\n")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Q-Learning Policy vs Fixed-Timer Baseline")
    parser.add_argument("--sumocfg", type=str, default="scenario.sumocfg", help="Path to .sumocfg file")
    parser.add_argument("--junction", type=str, default="J1", help="Junction configuration key")
    parser.add_argument("--model-path", type=str, default="team2_q_table.json", help="Path to trained Q-table model")
    parser.add_argument("--mode", type=str, choices=["qlearning", "fixed"], default="qlearning", help="Evaluation mode")
    parser.add_argument("--steps", type=int, default=3600, help="Simulation steps to evaluate")
    parser.add_argument("--interval", type=int, default=5, help="Decision interval in simulation steps")
    parser.add_argument("--fixed-duration", type=int, default=30, help="Fixed green phase duration in seconds/steps")

    args = parser.parse_args()

    evaluate_policy(
        sumocfg_path=args.sumocfg,
        junction_key=args.junction,
        model_path=args.model_path,
        steps_per_episode=args.steps,
        decision_interval=args.interval,
        mode=args.mode,
        fixed_green_duration=args.fixed_duration,
    )
