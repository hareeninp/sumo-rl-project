"""
state.py - Configurable State Discretization for Tabular Q-Learning

Converts raw SUMO junction state dictionary into a compact discrete state tuple:
    state = (current_green_phase_index_or_id, traffic_level_group_1, traffic_level_group_2, ...)

Traffic Levels:
    0 -> LOW    (0 - 4 vehicles)
    1 -> MEDIUM (5 - 9 vehicles)
    2 -> HIGH   (10+ vehicles)
"""

from typing import Dict, List, Tuple, Any, Optional

DEFAULT_THRESHOLDS = {
    "LOW_MAX": 4,      # 0 to 4 vehicles
    "MEDIUM_MAX": 9,   # 5 to 9 vehicles
}


def discretize_queue(queue_length: int, thresholds: Optional[Dict[str, int]] = None) -> int:
    """
    Discretizes a raw numerical queue length into discrete traffic levels.

    Args:
        queue_length: Total number of queued vehicles on target lanes.
        thresholds: Custom dictionary containing 'LOW_MAX' and 'MEDIUM_MAX'.

    Returns:
        0 for LOW, 1 for MEDIUM, 2 for HIGH.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    low_max = thresholds.get("LOW_MAX", 4)
    med_max = thresholds.get("MEDIUM_MAX", 9)

    if queue_length <= low_max:
        return 0  # LOW
    elif queue_length <= med_max:
        return 1  # MEDIUM
    else:
        return 2  # HIGH


def get_total_queue(junction_state: Dict[str, Any], lane_list: List[str]) -> int:
    """
    Calculates the total queue length across a specific list of lanes.

    Args:
        junction_state: Dictionary containing raw SUMO junction metric data.
        lane_list: List of lane IDs to aggregate.

    Returns:
        Integer sum of vehicle queues on the given lanes.
    """
    if not junction_state or not lane_list:
        return 0

    total = 0

    # Case 1: junction_state contains a "queue_lengths", "queues", or "lane_queues" sub-dictionary
    queues_dict = (
        junction_state.get("queue_lengths")
        or junction_state.get("queues")
        or junction_state.get("lane_queues")
    )
    if isinstance(queues_dict, dict):
        for lane_id in lane_list:
            total += int(queues_dict.get(lane_id, 0))
        return total

    # Case 2: junction_state is keyed directly by lane_id
    for lane_id in lane_list:
        if lane_id in junction_state:
            val = junction_state[lane_id]
            if isinstance(val, dict):
                total += int(val.get("queue_length", val.get("queue", val.get("halting", 0))))
            elif isinstance(val, (int, float)):
                total += int(val)

    return total


def get_rl_state(
    junction_state: Dict[str, Any],
    ns_lanes: Optional[List[str]] = None,
    ew_lanes: Optional[List[str]] = None,
    traffic_groups: Optional[Dict[str, List[str]]] = None,
    valid_green_phases: Optional[List[int]] = None,
    thresholds: Optional[Dict[str, int]] = None
) -> Tuple[int, ...]:
    """
    Transforms the raw SUMO junction state into a discrete RL state tuple.

    Supports both:
      1. Legacy NS/EW lane signatures (backward compatibility).
      2. Flexible traffic_groups dictionary for arbitrary junction lane groups.

    Returns:
        Tuple: (current_green_phase, group_1_level, group_2_level, ...)
    """
    raw_phase = junction_state.get("current_phase", junction_state.get("phase", 0))

    # Normalize raw phase to valid green phase if provided
    if valid_green_phases:
        if raw_phase in valid_green_phases:
            green_phase = raw_phase
        else:
            # Map yellow/all-red phase to nearest valid green phase
            green_phase = valid_green_phases[0]
    else:
        # Legacy fallback
        green_phase = 0 if raw_phase in (0, 1) else 2

    # Determine traffic groups to evaluate
    if traffic_groups is None:
        traffic_groups = {
            "group_1": ns_lanes or [],
            "group_2": ew_lanes or []
        }

    discrete_levels = []
    for group_name, lane_list in traffic_groups.items():
        queue_val = get_total_queue(junction_state, lane_list)
        level = discretize_queue(queue_val, thresholds)
        discrete_levels.append(level)

    return (green_phase, *discrete_levels)
