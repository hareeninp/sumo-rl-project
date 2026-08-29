"""
preemption.py - Emergency Signal Preemption Logic

Handles calculation of required movement green phases and triggers signal preemption
using safe phase changes through the decoupled TraCI adapter.
"""

import logging
from typing import Optional, Dict, Any, List
from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_green_phase_for_movement,
    get_safe_transition_sequence,
)
from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter

logger = logging.getLogger(__name__)


def determine_required_phase(
    junction_id: str,
    vehicle_approach_edge: str = "",
    to_edge: str = "",
    phase_config: Optional[Dict[str, Any]] = None
) -> int:
    """
    Determines the required green phase for an approaching emergency vehicle
    using Team 1's authoritative movement mapping.
    """
    return get_green_phase_for_movement(
        junction_id=junction_id,
        from_edge=vehicle_approach_edge,
        to_edge=to_edge
    )


def execute_preemption(
    junction_id: str,
    tls_id: str,
    target_phase: int,
    traci_interface: Optional[Any] = None
) -> bool:
    """
    Executes emergency signal preemption safely by stepping through intermediate
    yellow / clearance phases specified in Team 1's B1_SAFE_TRANSITIONS.csv.
    """
    adapter: TraCIAdapter = get_traci_adapter(traci_interface)

    try:
        current_phase = adapter.get_signal_phase(tls_id)
        if current_phase == target_phase:
            logger.debug(f"Junction {junction_id} already in target phase {target_phase}. Holding green.")
            return True

        # Retrieve full safe transition sequence (intermediates + target_phase)
        transition_path = get_safe_transition_sequence(junction_id, current_phase, target_phase)

        # Execute safe transition path step-by-step
        for step_phase in transition_path:
            adapter.force_phase_change(tls_id, step_phase)

        logger.info(
            f"[PREEMPTION] Junction {junction_id} (TLS: {tls_id}) safely transitioned "
            f"from Phase {current_phase} to Phase {target_phase} via path {transition_path}."
        )
        return True
    except Exception as e:
        logger.error(f"Failed to execute preemption on junction {junction_id}: {e}")
        return False

