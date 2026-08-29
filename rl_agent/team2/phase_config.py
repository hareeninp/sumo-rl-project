import csv
import os
import re
from typing import Dict, List, Any, Optional, Tuple

# Pre-defined traffic movement groups for legacy/known junctions.
# Movement groups remain configurable per junction.
DEFAULT_TRAFFIC_GROUPS: Dict[str, Dict[str, List[str]]] = {
    "J1": {
        "group_1": ["lane_N_0", "lane_S_0"],
        "group_2": ["lane_E_0", "lane_W_0"]
    },
    "J2": {
        "group_1": ["lane_J2_N_0", "lane_J2_S_0"],
        "group_2": ["lane_J2_E_0", "lane_J2_W_0"]
    },
    "J3": {
        "group_1": ["lane_J3_N_0"],
        "group_2": ["lane_J3_E_0"]
    },
    "J5": {
        "group_1": ["lane_J5_0"]
    }
}


def _resolve_csv_path(filename: str, custom_path: Optional[str] = None) -> str:
    """Finds absolute path to a CSV file across candidate locations."""
    candidate_paths: List[str] = []
    if custom_path:
        candidate_paths.append(custom_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths.extend([
        os.path.join(base_dir, filename),
        os.path.join(base_dir, "..", filename),
        os.path.join(base_dir, "..", "..", filename),
        os.path.join(base_dir, "..", "..", "network", filename),
        os.path.join(base_dir, "..", "..", "A1_network", filename),
        filename,
        f"network/{filename}",
        f"rl_agent/team2/{filename}",
        f"A1_network/{filename}",
        f"team2/{filename}",
        f"e:/B1/{filename}",
        f"e:/B1/network/{filename}",
        f"e:/B1/rl_agent/team2/{filename}",
        f"e:/from other team]/Network/{filename}",
    ])

    for path in candidate_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Required file '{filename}' not found in candidate paths: {candidate_paths}")


def load_phase_config_from_csv(csv_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Parses the authoritative Team 1 B1_TLS_PHASE_MAPPING.csv / tls_phases.csv file
    and generates the internal JUNCTION_PHASE_CONFIG dictionary.
    """
    target_csv = None
    for name in ["B1_TLS_PHASE_MAPPING.csv", "tls_phases.csv"]:
        try:
            target_csv = _resolve_csv_path(name, csv_path)
            break
        except FileNotFoundError:
            continue

    if not target_csv:
        target_csv = _resolve_csv_path("B1_TLS_PHASE_MAPPING.csv", csv_path)

    junctions: Dict[str, Dict[str, Any]] = {}

    with open(target_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            junction_id = row["junction_id"].strip()
            tls_id = row["tls_id"].strip()

            # Handle phase_index (Team 1 authoritative header) or phase_id (legacy header)
            p_val = row.get("phase_index", row.get("phase_id", "0")).strip()
            phase_id = int(p_val) if p_val else 0

            d_val = row.get("duration_sec", "0").strip()
            duration_sec = int(d_val) if d_val else 0

            classification = row.get("classification", "").strip().lower()
            state_string = row.get("state_string", "").strip()

            # Support optional or derived boolean classification fields
            is_green = (row["is_green"].strip().upper() == "TRUE") if "is_green" in row else (classification == "green")
            is_yellow = (row["is_yellow"].strip().upper() == "TRUE") if "is_yellow" in row else (classification == "yellow")
            is_all_red = (row["is_all_red"].strip().upper() == "TRUE") if "is_all_red" in row else (classification == "all-red")

            n_val = row.get("next_phase", "").strip()
            next_phase = int(n_val) if (n_val.isdigit() or (n_val.startswith('-') and n_val[1:].isdigit())) else -1

            g_val = str(row.get("num_green_links", "")).strip()
            num_green_links = int(g_val) if g_val.isdigit() else 0

            if junction_id not in junctions:
                traffic_groups = DEFAULT_TRAFFIC_GROUPS.get(
                    junction_id,
                    {
                        "group_1": [f"lane_{junction_id}_1"],
                        "group_2": [f"lane_{junction_id}_2"],
                    }
                )
                junctions[junction_id] = {
                    "junction_id": junction_id,
                    "tls_id": tls_id,
                    "green_phases": [],
                    "yellow_phases": [],
                    "all_red_phases": [],
                    "mixed_phases": [],
                    "phase_durations": {},
                    "next_phase": {},
                    "phase_details": {},
                    "traffic_groups": traffic_groups,
                    "transitions": {},
                    "phases_in_order": [],
                }

            j_data = junctions[junction_id]
            j_data["phases_in_order"].append(phase_id)
            j_data["phase_durations"][phase_id] = duration_sec
            j_data["next_phase"][phase_id] = next_phase
            j_data["phase_details"][phase_id] = {
                "classification": classification,
                "state_string": state_string,
                "duration_sec": duration_sec,
                "is_green": is_green,
                "is_yellow": is_yellow,
                "is_all_red": is_all_red,
                "next_phase": next_phase,
                "num_green_links": num_green_links,
            }

            if classification == "green" and is_green:
                j_data["green_phases"].append(phase_id)
            elif classification == "yellow" or is_yellow:
                j_data["yellow_phases"].append(phase_id)
            elif classification == "all-red" or is_all_red:
                j_data["all_red_phases"].append(phase_id)
            elif classification == "mixed(green+yellow)":
                j_data["mixed_phases"].append(phase_id)
                if phase_id not in j_data["yellow_phases"]:
                    j_data["yellow_phases"].append(phase_id)

    # Post-process next_phase transitions if next_phase was not explicitly in CSV
    for jid, j_data in junctions.items():
        p_list = j_data["phases_in_order"]
        for idx, p_id in enumerate(p_list):
            if j_data["next_phase"][p_id] == -1:
                nxt = p_list[(idx + 1) % len(p_list)]
                j_data["next_phase"][p_id] = nxt
                j_data["phase_details"][p_id]["next_phase"] = nxt

        j_data["green_phases"] = sorted(list(set(j_data["green_phases"])))
        j_data["yellow_phases"] = sorted(list(set(j_data["yellow_phases"])))
        j_data["all_red_phases"] = sorted(list(set(j_data["all_red_phases"])))
        j_data["mixed_phases"] = sorted(list(set(j_data["mixed_phases"])))
        j_data["enabled_for_rl"] = len(j_data["green_phases"]) > 1

    return junctions


def load_safe_transitions_from_csv(csv_path: Optional[str] = None) -> Dict[Tuple[str, int, int], List[int]]:
    """
    Parses Team 1's B1_SAFE_TRANSITIONS.csv / tls_safe_transitions.csv file.

    Returns:
        Dict mapping (junction_id, from_green_phase, to_green_phase) -> list of intermediate phase IDs.
    """
    target_csv = None
    for name in ["B1_SAFE_TRANSITIONS.csv", "tls_safe_transitions.csv"]:
        try:
            target_csv = _resolve_csv_path(name, csv_path)
            break
        except FileNotFoundError:
            continue

    if not target_csv:
        return {}

    transitions: Dict[Tuple[str, int, int], List[int]] = {}

    with open(target_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            junction_id = row["junction_id"].strip()
            from_phase = int(row["from_green_phase"])
            to_phase = int(row["to_green_phase"])
            inter_str = str(row["intermediate_phases_in_order"])

            # Extract phase numbers from format "1(mixed(green+yellow)) -> 2(green) -> 3(yellow)"
            phase_nums = [int(p) for p in re.findall(r"(\d+)\(", inter_str)]
            transitions[(junction_id, from_phase, to_phase)] = phase_nums

    return transitions


def load_lane_movement_mapping_from_csv(csv_path: Optional[str] = None) -> Tuple[
    Dict[Tuple[str, str, str], int],
    Dict[Tuple[str, str], int],
    Dict[str, Dict[str, List[str]]]
]:
    """
    Parses Team 1's B1_LANE_MOVEMENT_MAPPING.csv / tls_green_movements.csv file.

    Returns:
        1. movement_to_phase_map: (junction_id, from_edge, to_edge) -> green_phase_index
        2. from_edge_to_phase_map: (junction_id, from_edge) -> green_phase_index
        3. movement_traffic_groups: junction_id -> {approach_edge: [lane_id_1, lane_id_2, ...]}
    """
    target_csv = None
    for name in ["tls_green_movements.csv", "B1_LANE_MOVEMENT_MAPPING.csv"]:
        try:
            target_csv = _resolve_csv_path(name, csv_path)
            break
        except FileNotFoundError:
            continue

    if not target_csv:
        return {}, {}, {}

    mov_exact_map: Dict[Tuple[str, str, str], int] = {}
    from_edge_map: Dict[Tuple[str, str], int] = {}
    traffic_groups_map: Dict[str, Dict[str, List[str]]] = {}

    with open(target_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            junction_id = row["junction_id"].strip()
            green_phase = int(row["green_phase_index"])
            from_edge = row["from_edge"].strip()
            to_edge = row["to_edge"].strip()
            from_lane = int(row["from_lane"])

            lane_id = f"{from_edge}_{from_lane}"

            # Exact movement mapping (from_edge, to_edge) -> green_phase
            if (junction_id, from_edge, to_edge) not in mov_exact_map:
                mov_exact_map[(junction_id, from_edge, to_edge)] = green_phase

            # Approach edge fallback mapping
            if (junction_id, from_edge) not in from_edge_map:
                from_edge_map[(junction_id, from_edge)] = green_phase

            # Build approach-edge based traffic groups for state discretization
            if junction_id not in traffic_groups_map:
                traffic_groups_map[junction_id] = {}

            group_key = f"group_{from_edge}"
            if group_key not in traffic_groups_map[junction_id]:
                traffic_groups_map[junction_id][group_key] = []

            if lane_id not in traffic_groups_map[junction_id][group_key]:
                traffic_groups_map[junction_id][group_key].append(lane_id)

    return mov_exact_map, from_edge_map, traffic_groups_map


# Load authoritative phase configs, safe transitions, and lane movement mappings
JUNCTION_PHASE_CONFIG: Dict[str, Dict[str, Any]] = load_phase_config_from_csv()
SAFE_TRANSITIONS_MAP: Dict[Tuple[str, int, int], List[int]] = load_safe_transitions_from_csv()
MOVEMENT_EXACT_MAP, FROM_EDGE_MAP, MOVEMENT_TRAFFIC_GROUPS = load_lane_movement_mapping_from_csv()

# Update traffic_groups in JUNCTION_PHASE_CONFIG with real movement groups where available
for jid, groups in MOVEMENT_TRAFFIC_GROUPS.items():
    if jid in JUNCTION_PHASE_CONFIG and groups:
        JUNCTION_PHASE_CONFIG[jid]["traffic_groups"] = groups


def get_junction_config(junction_id: str) -> Dict[str, Any]:
    """Retrieves full configuration dictionary for a given junction."""
    return JUNCTION_PHASE_CONFIG.get(junction_id, {})


def is_rl_enabled(junction_id: str) -> bool:
    """
    Checks whether RL signal control is enabled for a given junction.
    Returns False for single-phase junctions (such as J5).
    """
    config = get_junction_config(junction_id)
    return config.get("enabled_for_rl", True) and len(config.get("green_phases", [])) > 1


def get_valid_green_phases(junction_id: str) -> List[int]:
    """Returns the list of valid GREEN SUMO phase IDs for a given junction."""
    return get_junction_config(junction_id).get("green_phases", [0])


def map_action_index_to_sumo_phase(junction_id: str, action_index: int) -> int:
    """
    Maps an RL action index (0 .. N-1) to the corresponding actual SUMO green phase ID.
    """
    green_phases = get_valid_green_phases(junction_id)
    if 0 <= action_index < len(green_phases):
        return green_phases[action_index]
    return green_phases[0]


def map_sumo_phase_to_action_index(junction_id: str, sumo_phase: int) -> int:
    """
    Maps an actual SUMO phase ID to the corresponding RL action index (0 .. N-1).
    """
    green_phases = get_valid_green_phases(junction_id)
    if sumo_phase in green_phases:
        return green_phases.index(sumo_phase)
    return 0


def get_programmed_transition_sequence(
    junction_id: str,
    current_phase: int,
    target_phase: int
) -> List[int]:
    """
    Returns the sequence of phase IDs required to transition from
    current_phase to target_phase using next_phase links.
    """
    j_config = get_junction_config(junction_id)
    next_map = j_config.get("next_phase", {})

    if not next_map or current_phase == target_phase:
        return []

    sequence: List[int] = []
    curr = current_phase
    max_steps = len(next_map) + 1

    for _ in range(max_steps):
        if curr not in next_map:
            break
        curr = next_map[curr]
        sequence.append(curr)
        if curr == target_phase:
            break

    return sequence


def get_safe_transition_sequence(
    junction_id: str,
    current_phase: int,
    target_phase: int
) -> List[int]:
    """
    Returns the complete safe phase sequence (intermediates + target_phase)
    required to transition from current_phase to target_phase according to
    Team 1's B1_SAFE_TRANSITIONS.csv mapping.

    Args:
        junction_id: Target junction ID.
        current_phase: Current active phase ID.
        target_phase: Desired target green phase ID.

    Returns:
        List of phase IDs to execute in order.
    """
    if current_phase == target_phase:
        return [target_phase]

    key = (junction_id, current_phase, target_phase)
    if key in SAFE_TRANSITIONS_MAP:
        intermediates = SAFE_TRANSITIONS_MAP[key]
        full_path = list(intermediates)
        if not full_path or full_path[-1] != target_phase:
            full_path.append(target_phase)
        return full_path

    # Fallback to programmed transition sequence if exact pair not in safe transitions map
    seq = get_programmed_transition_sequence(junction_id, current_phase, target_phase)
    if not seq or seq[-1] != target_phase:
        seq.append(target_phase)
    return seq


def get_green_phase_for_movement(
    junction_id: str,
    from_edge: str = "",
    to_edge: str = "",
    approach_lane: str = ""
) -> int:
    """
    Looks up the authoritative target green phase for a vehicle movement
    (from_edge -> to_edge) from Team 1's B1_LANE_MOVEMENT_MAPPING.csv data.

    Args:
        junction_id: Target junction ID.
        from_edge: Approaching edge ID.
        to_edge: Destination edge ID.
        approach_lane: Optional approach lane ID.

    Returns:
        Valid SUMO green phase ID integer.
    """
    valid_greens = get_valid_green_phases(junction_id)

    # 1. Try exact movement match: (junction_id, from_edge, to_edge)
    exact_key = (junction_id, from_edge.strip(), to_edge.strip())
    if exact_key in MOVEMENT_EXACT_MAP:
        phase = MOVEMENT_EXACT_MAP[exact_key]
        if phase in valid_greens:
            return phase

    # 2. Fallback to approach edge match: (junction_id, from_edge)
    from_key = (junction_id, from_edge.strip())
    if from_key in FROM_EDGE_MAP:
        phase = FROM_EDGE_MAP[from_key]
        if phase in valid_greens:
            return phase

    # 3. Default fallback to first valid green phase for junction
    return valid_greens[0]


