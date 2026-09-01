"""
handoff.py - Integration & Handoff Adapter Between B1 (RL) and B2 (Emergency)

Ensures strict mutual exclusion between B1 Tabular Q-Learning and B2 Emergency Controller:
  - NORMAL mode: B1 controls signals via Q-learning.
  - EMERGENCY mode: B1 is paused; B2 handles signal preemption & green corridor.
  - RECOVERY mode: B2 flushes cross-traffic queues safely.
  - HANDOFF: B2 releases control, system_mode resets to NORMAL, and B1 resumes.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from rl_agent.team2.phase_config import is_rl_enabled, map_action_index_to_sumo_phase, get_valid_green_phases
from rl_agent.team2.q_learning import QLearningAgent
from rl_agent.team2.emergency_controller import EmergencyController, EmergencyState
from rl_agent.team2.emergency_vehicle import EmergencyVehicle
from rl_agent.team2.state import get_rl_state, get_total_queue

logger = logging.getLogger(__name__)


class MasterSystemController:
    """
    Master Integration Controller governing mode handoffs between B1 (RL) and B2 (Emergency).
    """

    def __init__(
        self,
        b1_agent: Optional[QLearningAgent] = None,
        b2_controller: Optional[EmergencyController] = None,
    ):
        self.b1_agent = b1_agent if b1_agent is not None else QLearningAgent()
        self.b2_controller = b2_controller if b2_controller is not None else EmergencyController()

        # Operational modes: "NORMAL", "EMERGENCY", "RECOVERY"
        self.system_mode: str = "NORMAL"
        self.log_history: List[str] = []

    def _log(self, message: str) -> None:
        formatted = f"[{self.system_mode}] {message}"
        self.log_history.append(formatted)
        logger.info(formatted)
        print(formatted, flush=True)

    def request_emergency(
        self,
        request_payload: Dict[str, Any],
        team3_response: Dict[str, Any],
        current_time: float = 0.0
    ) -> bool:
        """
        Receives an emergency request and Team 3 routing response, pauses B1,
        and initiates B2 emergency mode.

        Args:
            request_payload: Emergency request dict containing verificationToken.
            team3_response: Team 3 response dict containing hospital and route.
            current_time: Current simulation timestamp.

        Returns:
            True if emergency mode successfully initiated, False otherwise.
        """
        vehicle = EmergencyVehicle.from_request_and_team3_response(request_payload, team3_response)
        self.system_mode = "EMERGENCY"
        self._log(f"Emergency priority requested for {vehicle.vehicle_id}. Pausing B1 Q-learning.")
        return self.b2_controller.register_emergency(vehicle, request_payload, current_time)

    def step(
        self,
        junction_id: str,
        tls_id: str,
        junction_state: Dict[str, Any],
        traffic_groups: Optional[Dict[str, List[str]]] = None,
        ns_lanes: Optional[List[str]] = None,
        ew_lanes: Optional[List[str]] = None,
        current_time: float = 0.0,
        traci_interface: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes one decision step, selecting either B1 (Q-learning) or B2 (Emergency) control.
        """
        if traffic_groups is None:
            traffic_groups = {
                "group_1": ns_lanes or [],
                "group_2": ew_lanes or []
            }

        all_lanes: List[str] = []
        for lane_list in traffic_groups.values():
            all_lanes.extend(lane_list)

        # ========================================================
        # MODE 1: EMERGENCY / RECOVERY (B2 Control)
        # ========================================================
        if self.system_mode in ("EMERGENCY", "RECOVERY"):
            b2_state = self.b2_controller.step(
                current_time=current_time,
                junction_states={junction_id: junction_state},
                traci_interface=traci_interface
            )

            # Update system mode based on B2 state
            if b2_state == EmergencyState.RECOVERY:
                self.system_mode = "RECOVERY"
            elif b2_state == EmergencyState.NORMAL:
                # B2 completed recovery and handback -> Resume NORMAL mode
                self.system_mode = "NORMAL"
                self._log("B2 handback completed. Resuming B1 Q-learning control.")

            return {
                "active_controller": "B2",
                "system_mode": self.system_mode,
                "emergency_state": b2_state.name,
                "action": "EMERGENCY_PREEMPTION",
            }

        # ========================================================
        # MODE 2: NORMAL (B1 Q-Learning Control)
        # ========================================================
        if not is_rl_enabled(junction_id):
            # Single-phase junction (J5): skip signal changes
            return {
                "active_controller": "B1",
                "system_mode": "NORMAL",
                "action": "SKIPPED_SINGLE_PHASE",
            }

        green_phases = get_valid_green_phases(junction_id)
        rl_state = get_rl_state(
            junction_state,
            traffic_groups=traffic_groups,
            valid_green_phases=green_phases
        )

        action_idx = self.b1_agent.choose_action(rl_state)
        target_sumo_phase = map_action_index_to_sumo_phase(junction_id, action_idx)

        if traci_interface and hasattr(traci_interface, "force_phase_change"):
            traci_interface.force_phase_change(tls_id, target_sumo_phase)

        self._log(f"B1 controlling {junction_id} (RL State: {rl_state}, Action Index: {action_idx} -> Phase: {target_sumo_phase})")

        return {
            "active_controller": "B1",
            "system_mode": "NORMAL",
            "rl_state": rl_state,
            "action_index": action_idx,
            "target_phase": target_sumo_phase,
        }
