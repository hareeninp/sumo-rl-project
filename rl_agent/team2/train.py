"""
train.py - Training Loop for Configurable Variable-Action Q-Learning Controller

Controls simulation advancement, action index selection, SUMO phase mapping,
state transitions, reward calculations, and Q-table updates via the decoupled TraCI adapter.

Supports:
  - Variable number of green phases per junction (e.g. 1, 3, 4, 5, 8, 10, 14).
  - Single-phase junction skipping (e.g., J5 where enabled_for_rl = False).
  - Explicit distinction between ACTION INDEX and ACTUAL SUMO PHASE ID.
"""

import os
import sys
import argparse
from typing import Dict, Any, List, Optional

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
from rl_agent.team2.reward import calculate_reward
from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter


def run_training(
    sumocfg_path: str,
    junction_key: str = "J1",
    num_episodes: int = 50,
    steps_per_episode: int = 3600,
    decision_interval: int = 5,
    model_save_path: str = "models/team2_q_table.json",
    learning_rate: float = 0.1,
    discount_factor: float = 0.95,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.995,
    traci_interface: Optional[Any] = None
) -> QLearningAgent:
    """
    Executes the main Q-learning training loop over SUMO simulation episodes.

    Args:
        sumocfg_path: Path to SUMO configuration (.sumocfg) file.
        junction_key: Key in JUNCTION_PHASE_CONFIG specifying target junction.
        num_episodes: Total number of training episodes.
        steps_per_episode: Maximum simulation steps per episode.
        decision_interval: Number of simulation steps between RL decisions.
        model_save_path: File path to save trained Q-table model.
        traci_interface: Optional external TraCI provider or adapter instance.

    Returns:
        Trained QLearningAgent instance.
    """
    adapter: TraCIAdapter = get_traci_adapter(traci_interface)

    j_config = get_junction_config(junction_key)
    if not j_config:
        raise KeyError(f"Junction '{junction_key}' not found in JUNCTION_PHASE_CONFIG.")

    tls_id = j_config.get("tls_id", junction_key)
    green_phases = get_valid_green_phases(junction_key)
    traffic_groups = j_config.get("traffic_groups", {})
    rl_enabled = is_rl_enabled(junction_key)

    # Aggregate all lanes across traffic groups for total queue monitoring
    all_lanes: List[str] = []
    for lane_list in traffic_groups.values():
        all_lanes.extend(lane_list)

    print(f"=== Starting Q-Learning Training ===")
    print(f"Target Junction: {junction_key} (TLS: {tls_id})")
    print(f"Valid Green Phases ({len(green_phases)}): {green_phases}")
    print(f"RL Enabled: {rl_enabled}")
    print(f"Episodes: {num_episodes} | Steps/Episode: {steps_per_episode} | Decision Interval: {decision_interval}")

    # Handle J5 / single-phase junctions where RL is disabled
    if not rl_enabled:
        print(f"INFO: Junction '{junction_key}' has only 1 green phase or RL disabled. Skipping RL training.")
        return QLearningAgent(action_space=[0])

    # Initialize Q-learning Agent with action count matching valid green phases
    agent = QLearningAgent(
        action_space=len(green_phases),
        learning_rate=learning_rate,
        discount_factor=discount_factor,
        epsilon=epsilon_start,
        epsilon_min=epsilon_min,
        epsilon_decay=epsilon_decay,
    )

    for episode in range(1, num_episodes + 1):
        # 1. Start SUMO simulation
        adapter.start_sim(sumocfg_path)

        episode_reward = 0.0
        decisions_made = 0
        step_counter = 0

        # 2. Get initial raw junction state and convert to RL state
        raw_state = adapter.get_junction_state(junction_key, tls_id, all_lanes)
        current_rl_state = get_rl_state(
            raw_state,
            traffic_groups=traffic_groups,
            valid_green_phases=green_phases
        )
        previous_total_queue = get_total_queue(raw_state, all_lanes)

        # Main episode decision loop
        while step_counter < steps_per_episode:
            # 3. Choose Q-learning ACTION INDEX (0 .. N-1)
            action_idx = agent.choose_action(current_rl_state)

            # 4. Map action index to actual SUMO green phase ID
            target_sumo_phase = map_action_index_to_sumo_phase(junction_key, action_idx)

            # 5. Request safe phase change
            adapter.force_phase_change(tls_id, target_sumo_phase)

            # 6. Advance SUMO for DECISION_INTERVAL steps
            for _ in range(decision_interval):
                adapter.step()
                step_counter += 1
                if step_counter >= steps_per_episode:
                    break

            # 7. Obtain next junction state and discrete RL state
            next_raw_state = adapter.get_junction_state(junction_key, tls_id, all_lanes)
            next_rl_state = get_rl_state(
                next_raw_state,
                traffic_groups=traffic_groups,
                valid_green_phases=green_phases
            )
            current_total_queue = get_total_queue(next_raw_state, all_lanes)

            # 8. Calculate reward and update Q-table
            reward = calculate_reward(previous_total_queue, current_total_queue)
            agent.update(current_rl_state, action_idx, reward, next_rl_state)

            episode_reward += reward
            decisions_made += 1

            # Update tracking variables
            current_rl_state = next_rl_state
            previous_total_queue = current_total_queue

        # 9. End episode and close SUMO
        adapter.close_sim()

        # 10. Decay exploration rate epsilon
        current_epsilon = agent.decay_epsilon()

        print(
            f"Episode {episode:03d}/{num_episodes:03d} | "
            f"Total Reward: {episode_reward:+.2f} | "
            f"Decisions: {decisions_made} | "
            f"Epsilon: {current_epsilon:.4f} | "
            f"Q-table States: {len(agent.q_table)}"
        )

    # 11. Save trained model Q-table
    agent.save(model_save_path)
    print(f"Training Complete. Q-table saved to: {model_save_path}")
    return agent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Tabular Q-Learning Traffic Signal Controller")
    parser.add_argument("--sumocfg", type=str, default="scenario.sumocfg", help="Path to .sumocfg file")
    parser.add_argument("--junction", type=str, default="J1", help="Junction configuration key")
    parser.add_argument("--episodes", type=int, default=50, help="Number of training episodes")
    parser.add_argument("--steps", type=int, default=3600, help="Simulation steps per episode")
    parser.add_argument("--interval", type=int, default=5, help="Decision interval in simulation steps")
    parser.add_argument("--save-path", type=str, default="team2_q_table.json", help="Path to save Q-table")

    args = parser.parse_args()

    run_training(
        sumocfg_path=args.sumocfg,
        junction_key=args.junction,
        num_episodes=args.episodes,
        steps_per_episode=args.steps,
        decision_interval=args.interval,
        model_save_path=args.save_path,
    )
