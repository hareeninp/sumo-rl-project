"""
emergency_config.py - Configuration Parameters for Emergency Preemption & Recovery (B2)

Maintains configurable phase mappings, timing safety limits, and thresholds.
The final Team 1 phase-to-movement mappings will be plugged in here when ready.
"""

from typing import Dict, List, Any

# Configurable Phase Mapping per Junction
# Placeholder configuration: maps approach directions / edges to required green phases
PHASE_CONFIG: Dict[str, Dict[str, Any]] = {
    "J1": {
        "green_phases": {"NS": 0, "EW": 2},
        "yellow_phases": {"NS": 1, "EW": 3},
        "all_red_phases": [4],
        "edge_to_phase": {
            "edge_N_in": 0,
            "edge_S_in": 0,
            "edge_E_in": 2,
            "edge_W_in": 2,
            "default": 0,
        },
    },
    "J2": {
        "green_phases": {"NS": 0, "EW": 2},
        "yellow_phases": {"NS": 1, "EW": 3},
        "all_red_phases": [4],
        "edge_to_phase": {
            "edge_J1_J2": 2,
            "edge_J2_J3": 2,
            "edge_N2_in": 0,
            "edge_S2_in": 0,
            "default": 2,
        },
    },
    "J3": {
        "green_phases": {"NS": 0, "EW": 2},
        "yellow_phases": {"NS": 1, "EW": 3},
        "all_red_phases": [4],
        "edge_to_phase": {
            "edge_J2_J3": 2,
            "edge_N3_in": 0,
            "edge_S3_in": 0,
            "default": 2,
        },
    },
}

# Safety & Timing Constraints
MAX_EMERGENCY_GREEN_DURATION: float = 60.0    # Maximum seconds to hold green for preemption
MIN_GREEN_DURATION: float = 10.0              # Minimum green duration before phase change
MIN_ACTION_INTERVAL: float = 3.0               # Safety interval between signal actions
CORRIDOR_PREPARATION_ETA_THRESHOLD: float = 30.0 # ETA (seconds) to trigger preemption on downstream junction
FLUSH_TIME_PER_LANE: float = 15.0              # Recovery flush time (seconds) per cross-traffic lane
DEFAULT_AMBULANCE_SPEED: float = 15.0          # Default assumed speed (m/s) if telemetry unavailable
DEFAULT_JUNCTION_DISTANCE: float = 300.0       # Default distance (meters) between adjacent junctions
