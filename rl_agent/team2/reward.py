"""
reward.py - Reward Calculation for Tabular Q-Learning

Calculates the reward based on queue reduction between decision steps:
    reward = previous_total_queue - current_total_queue

Queue decreases -> positive reward
Queue increases -> negative reward
Queue unchanged -> zero reward
"""


def calculate_reward(previous_total_queue: int, current_total_queue: int) -> float:
    """
    Computes the queue reduction reward.

    Args:
        previous_total_queue: Total queue length across controlled lanes at previous decision step.
        current_total_queue: Total queue length across controlled lanes at current decision step.

    Returns:
        Float reward value representing change in total queue length.
    """
    return float(previous_total_queue - current_total_queue)
