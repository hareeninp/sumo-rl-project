"""
q_learning.py - Tabular Q-Learning Agent with Variable Action Space Support

Implements a reusable, standard tabular Q-Learning agent supporting junction-specific
action counts (e.g., 1, 3, 4, 5, 8, 10, 14 actions).

Distinguishes between:
  - ACTION INDEX (0 .. N-1): Internal Q-table column indices selected by RL.
  - ACTUAL SUMO PHASE ID: Mapped externally via phase_config.py.
"""

import json
import os
import random
from typing import Dict, List, Tuple, Union, Any, Optional


class QLearningAgent:
    """
    Tabular Q-Learning agent for traffic signal control supporting variable action spaces.
    """

    def __init__(
        self,
        action_space: Union[int, List[int]] = 2,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
    ):
        """
        Args:
            action_space: Integer specifying number of actions (e.g. 5) OR list of action indices [0, 1, 2, ...].
            learning_rate: Alpha (α) parameter for Q-update.
            discount_factor: Gamma (γ) discount factor for future rewards.
            epsilon: Initial exploration rate (ε).
            epsilon_min: Minimum bound for exploration rate.
            epsilon_decay: Multiplicative decay factor applied to epsilon.
        """
        if isinstance(action_space, int):
            self.action_space = list(range(action_space))
        else:
            self.action_space = list(action_space) if action_space else [0, 1]

        self.num_actions = len(self.action_space)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Q-table stored as Python dictionary:
        # Key: state tuple (green_phase, level_1, level_2, ...)
        # Value: List of floats [Q_action_0, Q_action_1, ..., Q_action_N-1]
        self.q_table: Dict[Tuple[int, ...], List[float]] = {}

    def _get_q_values(self, state: Tuple[int, ...]) -> List[float]:
        """
        Retrieves Q-values for a given state, automatically initializing unseen states.
        """
        if state not in self.q_table:
            # Initialize unseen states with zeros for each available action index
            self.q_table[state] = [0.0 for _ in range(self.num_actions)]
        return self.q_table[state]

    def choose_action(self, state: Tuple[int, ...]) -> int:
        """
        Selects an action index using epsilon-greedy policy with random tie-breaking.

        Args:
            state: Discrete state tuple.

        Returns:
            Selected action INDEX integer (0 .. N-1).
        """
        # Single action space (e.g., J5 single phase)
        if self.num_actions <= 1:
            return 0

        # Exploration: choose random action index
        if random.random() < self.epsilon:
            return random.choice(self.action_space)

        # Exploitation: select action index with highest Q-value
        q_values = self._get_q_values(state)
        max_q = max(q_values)

        # Identify all action indices that share the maximum Q-value (random tie-breaking)
        best_actions = [
            action_idx for action_idx, q_val in enumerate(q_values)
            if q_val == max_q
        ]

        return random.choice(best_actions)

    def update(
        self,
        state: Tuple[int, ...],
        action_idx: int,
        reward: float,
        next_state: Tuple[int, ...]
    ) -> float:
        """
        Performs standard tabular Q-learning update.

        Args:
            state: Current state tuple.
            action_idx: Action INDEX executed (0 .. N-1).
            reward: Reward received from transition.
            next_state: Resulting state tuple.

        Returns:
            Updated Q-value for Q(state, action_idx).
        """
        if self.num_actions <= 1:
            return 0.0

        current_q_values = self._get_q_values(state)
        next_q_values = self._get_q_values(next_state)

        # Q-learning target: reward + gamma * max_a'(Q(next_state, a'))
        max_next_q = max(next_q_values) if next_q_values else 0.0
        target = reward + self.discount_factor * max_next_q

        # Q-value update formula: Q(s,a) <- Q(s,a) + alpha * [target - Q(s,a)]
        old_q = current_q_values[action_idx]
        new_q = old_q + self.learning_rate * (target - old_q)
        current_q_values[action_idx] = new_q

        return new_q

    def decay_epsilon(self) -> float:
        """
        Decays epsilon exploration rate after an episode.
        """
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return self.epsilon

    def save(self, filepath: str) -> None:
        """
        Saves the Q-table and agent configuration to a JSON file.
        """
        serialized_q_table = {
            str(list(state_key)): q_vals
            for state_key, q_vals in self.q_table.items()
        }

        data = {
            "hyperparameters": {
                "num_actions": self.num_actions,
                "learning_rate": self.learning_rate,
                "discount_factor": self.discount_factor,
                "epsilon": self.epsilon,
                "epsilon_min": self.epsilon_min,
                "epsilon_decay": self.epsilon_decay,
                "action_space": self.action_space,
            },
            "q_table": serialized_q_table
        }

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> None:
        """
        Loads Q-table and agent configuration from a JSON file.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        hyperparams = data.get("hyperparameters", {})
        self.learning_rate = hyperparams.get("learning_rate", self.learning_rate)
        self.discount_factor = hyperparams.get("discount_factor", self.discount_factor)
        self.epsilon = hyperparams.get("epsilon", self.epsilon)
        self.epsilon_min = hyperparams.get("epsilon_min", self.epsilon_min)
        self.epsilon_decay = hyperparams.get("epsilon_decay", self.epsilon_decay)
        self.action_space = hyperparams.get("action_space", self.action_space)
        self.num_actions = len(self.action_space)

        raw_q_table = data.get("q_table", {})
        self.q_table = {}

        for key_str, q_vals in raw_q_table.items():
            parsed_list = json.loads(key_str)
            state_tuple = tuple(int(x) for x in parsed_list)
            self.q_table[state_tuple] = [float(v) for v in q_vals]
