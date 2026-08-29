"""
test_b1_variable_actions.py - Unit Tests for Authoritative CSV Phase Mapping & B1 Controller

Tests all 13 core requirements for variable action space signal control:
  1. CSV loads successfully.
  2. All 16 junctions are discovered (155 total phase records).
  3. Each junction receives its correct green-phase list from CSV.
  4. Yellow phases are excluded from RL actions.
  5. All-red phases are excluded from RL actions.
  6. Mixed(green+yellow) phases are handled according to CSV classification and excluded from RL green targets.
  7. J5 is detected as a single-phase / no-RL junction.
  8. Action index maps correctly to actual SUMO phase ID.
  9. Different junctions can have different action counts (2, 3, 4, 5, 6, 7 actions).
  10. next_phase information is preserved and programmed transition sequences are traced.
  11. Existing B1 variable-action tests pass with authoritative CSV values.
  12. Existing B2 tests pass.
  13. TraCI adapter tests pass.
"""

import os
import tempfile
import unittest

from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    load_phase_config_from_csv,
    get_junction_config,
    get_valid_green_phases,
    is_rl_enabled,
    map_action_index_to_sumo_phase,
    map_sumo_phase_to_action_index,
    get_programmed_transition_sequence,
)
from rl_agent.team2.q_learning import QLearningAgent
from rl_agent.team2.state import get_rl_state, discretize_queue, get_total_queue
from rl_agent.team2.reward import calculate_reward


class TestVariableActionB1Controller(unittest.TestCase):

    def test_01_csv_loads_successfully(self):
        config = load_phase_config_from_csv()
        self.assertIsNotNone(config)
        self.assertIn("J1", config)
        self.assertIn("J16", config)

    def test_02_all_junctions_discovered(self):
        # 16 junctions across 155 phase records
        expected_junctions = [
            "J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8",
            "J9", "J10", "J11", "J12", "J13", "J14", "J15", "J16"
        ]
        discovered_set = set(JUNCTION_PHASE_CONFIG.keys())
        self.assertEqual(discovered_set, set(expected_junctions))
        self.assertEqual(len(discovered_set), 16)

        # Check total phase records = 155
        total_phases = sum(len(cfg["phase_details"]) for cfg in JUNCTION_PHASE_CONFIG.values())
        self.assertEqual(total_phases, 155)

    def test_03_junction_green_phase_lists(self):
        # Verify exact green phases for all junctions according to CSV
        expected_greens = {
            "J1": [0, 2, 4, 6],
            "J2": [0, 3, 6, 8, 11],
            "J3": [0, 2, 4, 6],
            "J4": [0, 3, 5],
            "J5": [0],
            "J6": [0, 2, 4, 6, 8, 10],
            "J7": [0, 2, 4, 6, 8, 10],
            "J8": [0, 2, 4, 6, 8, 10],
            "J9": [0, 2, 4, 6, 8, 10, 12],
            "J10": [0, 2, 4, 6, 9],
            "J11": [0, 2, 5],
            "J12": [0, 2, 5, 8, 11],
            "J13": [0, 2, 4, 6, 8, 10],
            "J14": [0, 2],
            "J15": [0, 3, 5],
            "J16": [0, 2, 5, 8],
        }

        for jid, greens in expected_greens.items():
            self.assertEqual(
                get_valid_green_phases(jid),
                greens,
                f"Green phase mismatch for junction {jid}"
            )

    def test_04_yellow_phases_excluded_from_rl(self):
        for jid, cfg in JUNCTION_PHASE_CONFIG.items():
            greens = set(cfg["green_phases"])
            yellows = set(cfg["yellow_phases"])
            # Ensure no yellow phase is in green_phases
            intersection = greens.intersection(yellows)
            self.assertEqual(
                len(intersection), 0,
                f"Junction {jid} has yellow phases in green target actions: {intersection}"
            )

    def test_05_all_red_phases_excluded_from_rl(self):
        for jid, cfg in JUNCTION_PHASE_CONFIG.items():
            greens = set(cfg["green_phases"])
            all_reds = set(cfg["all_red_phases"])
            intersection = greens.intersection(all_reds)
            self.assertEqual(
                len(intersection), 0,
                f"Junction {jid} has all-red phases in green target actions: {intersection}"
            )

    def test_06_mixed_green_yellow_phases_handled(self):
        # CSV contains mixed(green+yellow) classification (e.g. J1 phase 1 & 5, J14 phase 1 & 3)
        # Verify that mixed(green+yellow) phases are excluded from green RL target actions
        j1_mixed = JUNCTION_PHASE_CONFIG["J1"]["mixed_phases"]
        self.assertEqual(j1_mixed, [1, 5])
        j1_greens = get_valid_green_phases("J1")
        self.assertNotIn(1, j1_greens)
        self.assertNotIn(5, j1_greens)

        j14_mixed = JUNCTION_PHASE_CONFIG["J14"]["mixed_phases"]
        self.assertEqual(j14_mixed, [1, 3])
        j14_greens = get_valid_green_phases("J14")
        self.assertEqual(j14_greens, [0, 2])

    def test_07_j5_single_phase_no_rl_junction(self):
        self.assertFalse(is_rl_enabled("J5"))
        self.assertEqual(get_valid_green_phases("J5"), [0])

        agent_j5 = QLearningAgent(action_space=len(get_valid_green_phases("J5")))
        self.assertEqual(agent_j5.num_actions, 1)
        action_idx = agent_j5.choose_action((0, 1))
        self.assertEqual(action_idx, 0)
        self.assertEqual(map_action_index_to_sumo_phase("J5", action_idx), 0)

        # Count total RL-enabled junctions
        rl_enabled_count = sum(1 for jid in JUNCTION_PHASE_CONFIG if is_rl_enabled(jid))
        self.assertEqual(rl_enabled_count, 15)

    def test_08_action_index_mapping(self):
        # J2 green phases: [0, 3, 6, 8, 11]
        self.assertEqual(map_action_index_to_sumo_phase("J2", 0), 0)
        self.assertEqual(map_action_index_to_sumo_phase("J2", 1), 3)
        self.assertEqual(map_action_index_to_sumo_phase("J2", 2), 6)
        self.assertEqual(map_action_index_to_sumo_phase("J2", 3), 8)
        self.assertEqual(map_action_index_to_sumo_phase("J2", 4), 11)

        # Reverse mapping
        self.assertEqual(map_sumo_phase_to_action_index("J2", 8), 3)
        self.assertEqual(map_sumo_phase_to_action_index("J2", 11), 4)

        # Non-green phase reverse mapping fallback
        self.assertEqual(map_sumo_phase_to_action_index("J2", 1), 0)  # phase 1 is yellow

    def test_09_different_junction_action_counts(self):
        # J14: 2 actions, J4: 3 actions, J1: 4 actions, J2: 5 actions, J6: 6 actions, J9: 7 actions
        self.assertEqual(len(get_valid_green_phases("J14")), 2)
        self.assertEqual(len(get_valid_green_phases("J4")), 3)
        self.assertEqual(len(get_valid_green_phases("J1")), 4)
        self.assertEqual(len(get_valid_green_phases("J2")), 5)
        self.assertEqual(len(get_valid_green_phases("J6")), 6)
        self.assertEqual(len(get_valid_green_phases("J9")), 7)

    def test_10_next_phase_and_programmed_transitions(self):
        # J1 sequence: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 0
        j1_next = JUNCTION_PHASE_CONFIG["J1"]["next_phase"]
        self.assertEqual(j1_next[0], 1)
        self.assertEqual(j1_next[1], 2)
        self.assertEqual(j1_next[7], 0)

        # Check transition sequence from green phase 0 to green phase 4
        seq = get_programmed_transition_sequence("J1", 0, 4)
        self.assertEqual(seq, [1, 2, 3, 4])

        # Check transition sequence from 4 to 0
        seq2 = get_programmed_transition_sequence("J1", 4, 0)
        self.assertEqual(seq2, [5, 6, 7, 0])

    def test_11_epsilon_greedy_bounds(self):
        agent = QLearningAgent(action_space=7, epsilon=1.0)
        state = (0, 1, 2)
        for _ in range(100):
            action_idx = agent.choose_action(state)
            self.assertIn(action_idx, list(range(7)))

    def test_12_qtable_save_and_load(self):
        agent = QLearningAgent(action_space=5, learning_rate=0.1, discount_factor=0.95)
        state_a = (0, 2, 1)
        state_b = (3, 0, 2)

        agent.update(state_a, action_idx=3, reward=5.0, next_state=state_b)
        self.assertEqual(len(agent.q_table[state_a]), 5)
        self.assertEqual(agent.q_table[state_a][3], 0.5)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        try:
            agent.save(tmp_file)

            loaded_agent = QLearningAgent()
            loaded_agent.load(tmp_file)

            self.assertEqual(loaded_agent.num_actions, 5)
            self.assertEqual(len(loaded_agent.q_table[state_a]), 5)
            self.assertEqual(loaded_agent.q_table[state_a][3], 0.5)
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def test_13_safe_transition_lookup(self):
        # J1 transition from green phase 0 to green phase 4: 1(mixed) -> 2(green) -> 3(yellow) -> 4(green)
        seq_0_4 = get_programmed_transition_sequence("J1", 0, 4)
        self.assertEqual(seq_0_4, [1, 2, 3, 4])

        # J2 transition from green phase 0 to green phase 3: 1(yellow) -> 2(all-red) -> 3(green)
        seq_j2 = get_programmed_transition_sequence("J2", 0, 3)
        self.assertEqual(seq_j2, [1, 2, 3])

    def test_14_movement_group_state_construction(self):
        j1_config = get_junction_config("J1")
        traffic_groups = j1_config.get("traffic_groups", {})
        self.assertTrue(len(traffic_groups) > 0)

        # Mock raw junction state keyed by lane queues
        mock_raw_state = {
            "current_phase": 0,
            "queues": {
                "HOSP1_J1_0": 3,
                "J6_J1_0": 6,
                "J6_J1_1": 12,
                "HOME1_J1_0": 1,
                "J2_J1_0": 0,
                "J2_J1_1": 5,
            }
        }

        rl_state = get_rl_state(
            mock_raw_state,
            traffic_groups=traffic_groups,
            valid_green_phases=get_valid_green_phases("J1")
        )

        self.assertEqual(rl_state[0], 0)  # Current green phase
        self.assertEqual(len(rl_state), 1 + len(traffic_groups))  # phase + discrete levels


if __name__ == "__main__":
    unittest.main(verbosity=2)

