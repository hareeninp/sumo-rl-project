from rl_agent.team2.q_learning import QLearningAgent
import tempfile
import os

print("=" * 60)
print("Q-LEARNING TEST")
print("=" * 60)

# TC1: Correct action space
agent = QLearningAgent(action_space=4)

assert agent.num_actions == 4
assert agent.action_space == [0, 1, 2, 3]

print("TC1 PASSED - Action space")

# TC2: Action selection
state = (0, 1, 2)

action = agent.choose_action(state)

assert action in [0, 1, 2, 3]

print("TC2 PASSED - Action selection:", action)

# TC3: Q-learning update
agent.epsilon = 0.0

next_state = (2, 0, 1)

old_q = agent.q_table.get(state, [0.0] * 4)[0]

new_q = agent.update(
    state,
    0,
    10.0,
    next_state
)

assert new_q > old_q
assert agent.q_table[state][0] == new_q

print("TC3 PASSED - Q-value update:", new_q)

# TC4: Epsilon decay
old_epsilon = agent.epsilon
agent.epsilon = 1.0

new_epsilon = agent.decay_epsilon()

assert new_epsilon < 1.0

print("TC4 PASSED - Epsilon decay:", new_epsilon)

# TC5: Save and load Q-table
with tempfile.TemporaryDirectory() as temp_dir:

    filepath = os.path.join(
        temp_dir,
        "test_q_table.json"
    )

    agent.save(filepath)

    assert os.path.exists(filepath)

    loaded_agent = QLearningAgent(action_space=2)
    loaded_agent.load(filepath)

    assert loaded_agent.num_actions == agent.num_actions
    assert loaded_agent.q_table == agent.q_table

print("TC5 PASSED - Save/load")

print("\nALL Q-LEARNING TESTS PASSED")
