"""
emergency_controller.py - B2 Emergency Controller & State Machine

Implements the deterministic rule-based emergency signal preemption state machine:
    NORMAL -> EMERGENCY_DETECTED -> VERIFICATION -> PREEMPTION ->
    GREEN_CORRIDOR -> AMBULANCE_PASSING -> RECOVERY -> HAND_BACK -> NORMAL

Coordinates multi-junction green corridor preparation based on predicted ETAs
and supports dynamic route updates from Team 3.
"""

import logging
from enum import Enum, auto
from typing import Dict, List, Optional, Any

from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_valid_green_phases,
    map_action_index_to_sumo_phase,
)
from rl_agent.team2.emergency_config import (
    CORRIDOR_PREPARATION_ETA_THRESHOLD,
    MAX_EMERGENCY_GREEN_DURATION,
)
from rl_agent.team2.emergency_vehicle import EmergencyVehicle
from rl_agent.team2.verification import verify_emergency_request
from rl_agent.team2.eta import calculate_eta
from rl_agent.team2.preemption import determine_required_phase, execute_preemption
from rl_agent.team2.recovery import RecoveryManager

logger = logging.getLogger(__name__)


class EmergencyState(Enum):
    NORMAL = auto()
    EMERGENCY_DETECTED = auto()
    VERIFICATION = auto()
    PREEMPTION = auto()
    GREEN_CORRIDOR = auto()
    AMBULANCE_PASSING = auto()
    RECOVERY = auto()
    HAND_BACK = auto()


class EmergencyController:
    """
    Rule-based Emergency Signal Controller and Green Corridor Coordinator.
    Supports multi-EV priority queuing and 3-tier arbitration:
      Tier 1: Emergency severity (CRITICAL > HIGH > NORMAL)
      Tier 2: Vehicle type (FIRE TRUCK > AMBULANCE > POLICE)
      Tier 3: ETA / waiting time
    """

    def __init__(self, phase_config: Optional[Dict[str, Any]] = None):
        self.phase_config = phase_config if phase_config is not None else JUNCTION_PHASE_CONFIG
        self.state = EmergencyState.NORMAL
        self.active_vehicle: Optional[EmergencyVehicle] = None
        self.raw_request: Optional[Dict[str, Any]] = None
        self.route: List[str] = []
        self.current_junction_idx: int = 0
        self.recovery_manager = RecoveryManager()

        self.pending_queue: List[EmergencyVehicle] = []
        self.processed_vehicles: List[str] = []
        self.request_payload_map: Dict[str, Dict[str, Any]] = {}

        self.state_start_time: float = 0.0
        self.log_history: List[str] = []

    def _log(self, message: str) -> None:
        formatted = f"[{self.state.name}] {message}"
        self.log_history.append(formatted)
        logger.info(formatted)
        print(formatted, flush=True)

    def _sort_pending_queue(self) -> None:
        """
        Sorts pending_queue using 3-Tier priority:
          Tier 1: Emergency severity (CRITICAL = 3 > HIGH = 2 > NORMAL = 1)
          Tier 2: Vehicle type (FIRE TRUCK = 3 > AMBULANCE = 2 > POLICE = 1)
          Tier 3: ETA / waiting time (lower ETA / earlier request time)
        """
        self.pending_queue.sort(
            key=lambda v: (
                -v.severity_rank,
                -v.vehicle_type_rank,
                v.overall_eta_minutes if v.overall_eta_minutes > 0 else v.request_time
            )
        )

    def register_emergency(
        self,
        vehicle: EmergencyVehicle,
        request_payload: Optional[Dict[str, Any]] = None,
        current_time: float = 0.0
    ) -> bool:
        """
        Receives an emergency request and registers the emergency vehicle.
        If another emergency vehicle is currently active, enqueues the vehicle
        in the pending queue sorted by 3-Tier priority.
        """
        payload = request_payload or {
            "vehicleId": vehicle.vehicle_id,
            "verificationToken": vehicle.verification_token,
            "priority": vehicle.priority,
            "severity": vehicle.severity,
            "emergencyType": vehicle.emergency_type,
            "vehicleType": vehicle.vehicle_type,
        }
        self.request_payload_map[vehicle.vehicle_id] = payload

        # Check if vehicle is already processed or registered
        if vehicle.vehicle_id in self.processed_vehicles:
            return False

        if self.active_vehicle and self.active_vehicle.vehicle_id == vehicle.vehicle_id:
            return True

        if any(v.vehicle_id == vehicle.vehicle_id for v in self.pending_queue):
            return True

        # If no active vehicle is currently being served
        if self.active_vehicle is None:
            self.active_vehicle = vehicle
            self.raw_request = payload
            self.route = list(vehicle.junction_ids)
            self.current_junction_idx = 0
            self.state_start_time = current_time
            self.state = EmergencyState.EMERGENCY_DETECTED
            self._log(
                f"[B2 ARBITRATION]\n"
                f"Vehicle: {vehicle.vehicle_id}\n"
                f"Severity: {vehicle.severity}\n"
                f"Vehicle Type: {vehicle.vehicle_type}\n"
                f"Decision: SELECTED"
            )
            return True
        else:
            # Active vehicle exists -> Enqueue in pending_queue sorted by 3-Tier priority
            vehicle.request_time = current_time
            self.pending_queue.append(vehicle)
            self._sort_pending_queue()
            self._log(
                f"[B2 ARBITRATION]\n"
                f"Waiting: {vehicle.vehicle_id}\n"
                f"Severity: {vehicle.severity}\n"
                f"Vehicle Type: {vehicle.vehicle_type}\n"
                f"Decision: QUEUED"
            )
            return True

    def update_emergency_route(
        self,
        vehicle_id: str,
        new_junction_ids: List[str],
        new_edge_ids: Optional[List[str]] = None
    ) -> bool:
        """
        Supports receiving dynamic route updates when Team 3 recalculates optimal routes.
        """
        if self.active_vehicle and self.active_vehicle.vehicle_id == vehicle_id:
            self.active_vehicle.update_route(new_junction_ids, new_edge_ids)
            self.route = list(new_junction_ids)
            self._log(f"Dynamic route update received for active EV {vehicle_id}: {' -> '.join(new_junction_ids)}")
            return True
        for queued_veh in self.pending_queue:
            if queued_veh.vehicle_id == vehicle_id:
                queued_veh.update_route(new_junction_ids, new_edge_ids)
                self._log(f"Dynamic route update received for queued EV {vehicle_id}: {' -> '.join(new_junction_ids)}")
                return True
        return False

    def step(
        self,
        current_time: float,
        junction_states: Optional[Dict[str, Any]] = None,
        traci_interface: Optional[Any] = None
    ) -> EmergencyState:
        """
        Advances the emergency state machine per simulation decision step.
        """
        if self.state == EmergencyState.NORMAL:
            return self.state

        # 1. EMERGENCY_DETECTED -> VERIFICATION
        if self.state == EmergencyState.EMERGENCY_DETECTED:
            self.state = EmergencyState.VERIFICATION
            self._log(f"Proceeding to token verification for {self.active_vehicle.vehicle_id}.")
            return self.state

        # 2. VERIFICATION -> PREEMPTION or Next Queue / NORMAL
        if self.state == EmergencyState.VERIFICATION:
            verified = verify_emergency_request(self.raw_request)
            if verified:
                self.active_vehicle.verified = True
                self._log(f"Token verification PASSED for {self.active_vehicle.vehicle_id}.")
                self.state = EmergencyState.PREEMPTION
                self.state_start_time = current_time
            else:
                self.active_vehicle.verified = False
                self._log(f"Token verification FAILED for {self.active_vehicle.vehicle_id}. Emergency preemption REJECTED.")
                self.processed_vehicles.append(self.active_vehicle.vehicle_id)
                self.active_vehicle = None
                self.raw_request = None
                self.state = EmergencyState.HAND_BACK
            return self.state

        # 3. PREEMPTION -> GREEN_CORRIDOR
        if self.state == EmergencyState.PREEMPTION:
            if self.current_junction_idx < len(self.route):
                target_j = self.route[self.current_junction_idx]
                tls_id = self.phase_config.get(target_j, {}).get("tls_id", target_j)
                approach_edge = self.active_vehicle.current_edge or ""

                # Extract destination to_edge along ambulance route
                to_edge = ""
                if self.active_vehicle and self.active_vehicle.edge_ids:
                    if approach_edge in self.active_vehicle.edge_ids:
                        idx = self.active_vehicle.edge_ids.index(approach_edge)
                        if idx + 1 < len(self.active_vehicle.edge_ids):
                            to_edge = self.active_vehicle.edge_ids[idx + 1]

                req_phase = determine_required_phase(
                    target_j,
                    vehicle_approach_edge=approach_edge,
                    to_edge=to_edge,
                    phase_config=self.phase_config
                )
                execute_preemption(target_j, tls_id, req_phase, traci_interface)

                self._log(f"Junction {target_j} green phase {req_phase} activated for {self.active_vehicle.vehicle_id}.")
                self.state = EmergencyState.GREEN_CORRIDOR
                self.state_start_time = current_time
            else:
                self.state = EmergencyState.RECOVERY
            return self.state

        # 4. GREEN_CORRIDOR
        if self.state == EmergencyState.GREEN_CORRIDOR:
            if self.current_junction_idx < len(self.route):
                curr_j = self.route[self.current_junction_idx]
                eta = calculate_eta(self.active_vehicle, curr_j, traci_interface, current_time)

                # Check downstream junction preparation
                if self.current_junction_idx + 1 < len(self.route):
                    next_j = self.route[self.current_junction_idx + 1]
                    next_eta = calculate_eta(self.active_vehicle, next_j, traci_interface, current_time)
                    if next_eta <= CORRIDOR_PREPARATION_ETA_THRESHOLD:
                        self._log(f"Downstream junction {next_j} preparing priority (ETA: {next_eta}s).")

                # Check if ambulance has reached/passed current junction
                if eta <= 2.0 or (current_time - self.state_start_time) >= 3.0:  # Dynamic passing condition
                    self.state = EmergencyState.AMBULANCE_PASSING
            return self.state

        # 5. AMBULANCE_PASSING
        if self.state == EmergencyState.AMBULANCE_PASSING:
            cleared_j = self.route[self.current_junction_idx]
            self._log(f"Ambulance cleared junction {cleared_j}.")
            self.current_junction_idx += 1

            if self.current_junction_idx < len(self.route):
                # Move to preemption for next junction in corridor
                self.state = EmergencyState.PREEMPTION
            else:
                # All corridor junctions cleared -> proceed to RECOVERY
                self._log("Route cleared. Transitioning to RECOVERY mode.")
                self.state = EmergencyState.RECOVERY
                self.state_start_time = current_time
                for j_id in self.route:
                    tls_id = self.phase_config.get(j_id, {}).get("tls_id", j_id)
                    self.recovery_manager.start_recovery(j_id, tls_id, {}, current_time, traci_interface)
            return self.state

        # 6. RECOVERY -> HAND_BACK
        if self.state == EmergencyState.RECOVERY:
            all_complete = True
            for j_id in self.route:
                if not self.recovery_manager.is_recovery_complete(j_id, current_time):
                    all_complete = False
                    break

            if all_complete or (current_time - self.state_start_time) >= 3.0:
                self.state = EmergencyState.HAND_BACK
            return self.state

        # 7. HAND_BACK -> Next Vehicle in Queue OR NORMAL
        if self.state == EmergencyState.HAND_BACK:
            if self.active_vehicle:
                self.processed_vehicles.append(self.active_vehicle.vehicle_id)
                self._log(f"Completed emergency preemption & recovery for {self.active_vehicle.vehicle_id}.")

            # Filter pending queue to ensure no already processed vehicles remain
            self.pending_queue = [v for v in self.pending_queue if v.vehicle_id not in self.processed_vehicles]
            self._sort_pending_queue()

            if self.pending_queue:
                # Pop next highest priority emergency vehicle from queue
                next_veh = self.pending_queue.pop(0)
                self.active_vehicle = next_veh
                self.raw_request = self.request_payload_map.get(next_veh.vehicle_id)
                self.route = list(next_veh.junction_ids)
                self.current_junction_idx = 0
                self.state_start_time = current_time
                self.state = EmergencyState.EMERGENCY_DETECTED
                self._log(
                    f"[B2 ARBITRATION]\n"
                    f"Vehicle: {next_veh.vehicle_id}\n"
                    f"Severity: {next_veh.severity}\n"
                    f"Vehicle Type: {next_veh.vehicle_type}\n"
                    f"Decision: SELECTED"
                )
                return self.state
            else:
                self._log("All emergency vehicles in queue processed. B2 releasing signal control. Handing back to B1.")
                self.state = EmergencyState.NORMAL
                self.active_vehicle = None
                self.raw_request = None
                self.route = []
                self.current_junction_idx = 0
                return self.state

        return self.state
