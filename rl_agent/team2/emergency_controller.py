"""
emergency_controller.py - Dynamic Single-Next-Junction B2 Multi-EV Controller & Arbitration Engine

Implements deterministic rule-based emergency signal preemption with strict dynamic junction-level ownership:
    - Ownership requested ONLY for each EV's immediate current/next junction (current edge -> next route edge -> junction)
    - Strict invariant verification: owned junction must be on the EV's actual route and be its current/next target
    - 3-Tier priority arbitration for overlapping junction requests (Severity > Vehicle Type > ETA)
    - Immediate re-arbitration upon physical clearance and recovery completion
    - Full telemetry sync, exact route-based movement mapping, and physical clearance confirmation
"""

import logging
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple

from rl_agent.team2.phase_config import (
    JUNCTION_PHASE_CONFIG,
    get_valid_green_phases,
    map_action_index_to_sumo_phase,
    get_green_phase_for_movement,
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
    Junction-Aware Rule-Based Emergency Signal Controller and Coordinator.
    Tracks junction-level signal ownership (junction_id -> owner_ev_id)
    and enforces dynamic single-next-junction ownership across network junctions.
    """

    def __init__(self, phase_config: Optional[Dict[str, Any]] = None):
        self.phase_config = phase_config if phase_config is not None else JUNCTION_PHASE_CONFIG

        # Multi-EV tracking structures
        self.active_vehicles: Dict[str, EmergencyVehicle] = {}     # veh_id -> EmergencyVehicle
        self.junction_ownership: Dict[str, str] = {}               # junction_id -> owner_ev_id
        self.ev_current_j_idx: Dict[str, int] = {}                 # veh_id -> int index in junction_ids
        self.ev_state_map: Dict[str, EmergencyState] = {}          # veh_id -> EmergencyState
        self.ev_state_start_time: Dict[str, float] = {}             # veh_id -> timestamp

        self.pending_queue: List[EmergencyVehicle] = []
        self.processed_vehicles: List[str] = []
        self.request_payload_map: Dict[str, Dict[str, Any]] = {}

        self.recovery_manager = RecoveryManager()
        self.log_history: List[str] = []

    @property
    def active_vehicle(self) -> Optional[EmergencyVehicle]:
        """Backward compatibility: returns first active vehicle if any exists."""
        if self.active_vehicles:
            return next(iter(self.active_vehicles.values()))
        return None

    @active_vehicle.setter
    def active_vehicle(self, vehicle: Optional[EmergencyVehicle]) -> None:
        if vehicle is None:
            self.active_vehicles.clear()
        else:
            self.active_vehicles[vehicle.vehicle_id] = vehicle
            self.ev_state_map[vehicle.vehicle_id] = EmergencyState.EMERGENCY_DETECTED
            self.ev_current_j_idx[vehicle.vehicle_id] = 0

    @property
    def state(self) -> EmergencyState:
        """Backward compatibility: returns state of active vehicle or NORMAL."""
        av = self.active_vehicle
        if av:
            return self.ev_state_map.get(av.vehicle_id, EmergencyState.NORMAL)
        return EmergencyState.NORMAL

    @state.setter
    def state(self, new_state: EmergencyState) -> None:
        av = self.active_vehicle
        if av:
            self.ev_state_map[av.vehicle_id] = new_state

    @property
    def route(self) -> List[str]:
        av = self.active_vehicle
        return list(av.junction_ids) if av else []

    @route.setter
    def route(self, r: List[str]) -> None:
        av = self.active_vehicle
        if av:
            av.junction_ids = list(r)

    @property
    def current_junction_idx(self) -> int:
        av = self.active_vehicle
        return self.ev_current_j_idx.get(av.vehicle_id, 0) if av else 0

    @current_junction_idx.setter
    def current_junction_idx(self, idx: int) -> None:
        av = self.active_vehicle
        if av:
            self.ev_current_j_idx[av.vehicle_id] = idx

    @property
    def state_start_time(self) -> float:
        av = self.active_vehicle
        return self.ev_state_start_time.get(av.vehicle_id, 0.0) if av else 0.0

    @state_start_time.setter
    def state_start_time(self, st: float) -> None:
        av = self.active_vehicle
        if av:
            self.ev_state_start_time[av.vehicle_id] = st

    def _log(self, message: str) -> None:
        self.log_history.append(message)
        logger.info(message)
        print(message, flush=True)

    def _sort_pending_queue(self) -> None:
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
        payload = request_payload or {
            "vehicleId": vehicle.vehicle_id,
            "verificationToken": vehicle.verification_token,
            "priority": vehicle.priority,
            "severity": vehicle.severity,
            "emergencyType": vehicle.emergency_type,
            "vehicleType": vehicle.vehicle_type,
        }
        self.request_payload_map[vehicle.vehicle_id] = payload

        if vehicle.vehicle_id in self.processed_vehicles:
            return False

        if vehicle.vehicle_id in self.active_vehicles or any(v.vehicle_id == vehicle.vehicle_id for v in self.pending_queue):
            return True

        vehicle.request_time = current_time

        if not self.active_vehicles:
            self.active_vehicles[vehicle.vehicle_id] = vehicle
            self.ev_state_map[vehicle.vehicle_id] = EmergencyState.EMERGENCY_DETECTED
            self.ev_current_j_idx[vehicle.vehicle_id] = 0
            self.ev_state_start_time[vehicle.vehicle_id] = current_time
            self._log(
                f"[B2 ARBITRATION]\n"
                f"Vehicle: {vehicle.vehicle_id}\n"
                f"Severity: {vehicle.severity}\n"
                f"Vehicle Type: {vehicle.vehicle_type}\n"
                f"Decision: SELECTED"
            )
        else:
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
        if vehicle_id in self.active_vehicles:
            self.active_vehicles[vehicle_id].update_route(new_junction_ids, new_edge_ids)
            self._log(f"Dynamic route update received for active EV {vehicle_id}: {' -> '.join(new_junction_ids)}")
            return True
        for queued_veh in self.pending_queue:
            if queued_veh.vehicle_id == vehicle_id:
                queued_veh.update_route(new_junction_ids, new_edge_ids)
                self._log(f"Dynamic route update received for queued EV {vehicle_id}: {' -> '.join(new_junction_ids)}")
                return True
        return False

    def _get_current_next_junction(self, veh: EmergencyVehicle) -> str:
        """
        Dynamically determines ONLY the next immediate junction relevant to the EV's actual SUMO route position.
        """
        v_id = veh.vehicle_id
        route_edges = veh.edge_ids
        j_ids = veh.junction_ids
        j_idx = self.ev_current_j_idx.get(v_id, 0)

        try:
            import traci
            if traci.isLoaded() and v_id in traci.vehicle.getIDList():
                c_road = traci.vehicle.getRoadID(v_id)
                r_edges = list(traci.vehicle.getRoute(v_id)) or route_edges

                if c_road.startswith(":"):
                    j_name = c_road.split("_")[0][1:]
                    if j_name in j_ids:
                        return j_name

                if c_road in r_edges:
                    idx = r_edges.index(c_road)
                    if idx + 1 < len(r_edges):
                        next_e = r_edges[idx + 1]
                        for j in j_ids:
                            if c_road.endswith(f"_{j}") or next_e.startswith(f"{j}_"):
                                return j
        except Exception:
            pass

        if j_idx < len(j_ids):
            return j_ids[j_idx]
        return ""

    def _validate_ownership_invariants(self, current_time: float = 0.0) -> None:
        """
        Invariant Check:
        For every junction in junction_ownership, owner EV's actual route must contain that junction,
        and the junction must be the EV's current/next relevant junction.
        """
        for j_id, owner_id in list(self.junction_ownership.items()):
            owner_veh = self.active_vehicles.get(owner_id)
            if not owner_veh:
                print(f"[B2 ERROR] INVALID JUNCTION OWNERSHIP: junction={j_id} owner={owner_id} (Vehicle not active)", flush=True)
                continue

            if j_id not in owner_veh.junction_ids:
                print(f"[B2 ERROR] INVALID JUNCTION OWNERSHIP: junction={j_id} owner={owner_id} (Junction not in EV route)", flush=True)
                continue

            target_j = self._get_current_next_junction(owner_veh)
            is_recovering_j = self.recovery_manager.is_recovering(j_id, current_time)
            if j_id != target_j and not (owner_veh.current_edge and owner_veh.current_edge.startswith(f":{j_id}")) and not is_recovering_j:
                print(f"[B2 ERROR] INVALID JUNCTION OWNERSHIP: junction={j_id} owner={owner_id} target_j={target_j}", flush=True)

    def _arbitrate_junctions(self, current_time: float, traci_interface: Optional[Any] = None) -> None:
        """
        Junction-Aware Arbitration:
        Evaluates junction preemption requests for all active/pending EVs in 3-Tier priority order.
        Grants ONLY each EV's immediate target junction dynamically.
        """
        candidates = list(self.active_vehicles.values()) + list(self.pending_queue)
        candidates.sort(
            key=lambda v: (
                -v.severity_rank,
                -v.vehicle_type_rank,
                v.overall_eta_minutes if v.overall_eta_minutes > 0 else v.request_time
            )
        )

        for veh in candidates:
            v_id = veh.vehicle_id
            st = self.ev_state_map.get(v_id, EmergencyState.EMERGENCY_DETECTED)
            if st in (EmergencyState.RECOVERY, EmergencyState.HAND_BACK):
                continue

            if v_id not in self.active_vehicles:
                self.active_vehicles[v_id] = veh
                self.ev_state_map[v_id] = EmergencyState.EMERGENCY_DETECTED
                self.ev_current_j_idx[v_id] = 0
                self.ev_state_start_time[v_id] = current_time
                if veh in self.pending_queue:
                    self.pending_queue.remove(veh)

            target_j = self._get_current_next_junction(veh)
            if not target_j:
                continue

            # Release any previously owned junction by this EV that is no longer its target_j
            for j_id, owner_id in list(self.junction_ownership.items()):
                if owner_id == v_id and j_id != target_j and not self.recovery_manager.is_recovering(j_id, current_time):
                    self.junction_ownership.pop(j_id, None)
                    self._log(f"[B2 RELEASE] junction={j_id} owner={v_id} reason=STALE_TARGET_TRANSITION")

            in_e, out_e = veh.get_edges_for_junction(target_j)
            target_p = get_green_phase_for_movement(target_j, in_e, out_e)
            r_idx = self.ev_current_j_idx.get(v_id, 0)

            self._log(
                f"[B2 ROUTE REQUEST] EV={v_id} current_edge={veh.current_edge} next_edge={out_e} "
                f"route_index={r_idx} requested_junction={target_j}"
            )

            current_owner = self.junction_ownership.get(target_j)
            if current_owner is None:
                self.junction_ownership[target_j] = v_id
                self._log(
                    f"[B2 OWNERSHIP] junction={target_j} owner={v_id} "
                    f"reason=UNOWNED_GRANT (target_phase={target_p})"
                )
            elif current_owner != v_id:
                owner_veh = self.active_vehicles.get(current_owner)
                if owner_veh:
                    prio_veh = (-veh.severity_rank, -veh.vehicle_type_rank, veh.overall_eta_minutes)
                    prio_owner = (-owner_veh.severity_rank, -owner_veh.vehicle_type_rank, owner_veh.overall_eta_minutes)
                    if prio_veh < prio_owner:
                        self.junction_ownership[target_j] = v_id
                        self._log(
                            f"[B2 OWNERSHIP] junction={target_j} owner={v_id} "
                            f"reason=HIGHER_PRIORITY_PREEMPTION_OVER_{current_owner} (target_phase={target_p})"
                        )
                    else:
                        self._log(
                            f"[B2 QUEUE] EV={v_id} junction={target_j} owner={current_owner} "
                            f"reason=HIGHER_PRIORITY_EV"
                        )

        self._validate_ownership_invariants(current_time)

    def step(
        self,
        current_time: float,
        junction_states: Optional[Dict[str, Any]] = None,
        traci_interface: Optional[Any] = None
    ) -> EmergencyState:
        """
        Advances the emergency state machine per simulation step across all active vehicles.
        """
        # Clean up completed recoveries
        for j_id in list(self.recovery_manager.active_recoveries.keys()):
            self.recovery_manager.is_recovery_complete(j_id, current_time)

        # Arbitrate junction ownerships
        self._arbitrate_junctions(current_time, traci_interface)

        if not self.active_vehicles and not self.pending_queue and not self.junction_ownership:
            return EmergencyState.NORMAL

        # Advance state machine per active vehicle
        for v_id, veh in list(self.active_vehicles.items()):
            st = self.ev_state_map.get(v_id, EmergencyState.NORMAL)

            # Telemetry sync & vehicle existence check
            if traci_interface:
                try:
                    c_edge = ""
                    c_pos = 0.0
                    c_spd = 15.0
                    if hasattr(traci_interface, "get_vehicle_edge"):
                        c_edge = traci_interface.get_vehicle_edge(v_id) or ""
                        c_spd = traci_interface.get_vehicle_speed(v_id) or 15.0

                    import traci
                    if traci.isLoaded():
                        if v_id not in traci.vehicle.getIDList():
                            self._log(f"[EV EXITED SUMO] EV={v_id} completed assigned route and exited simulation.")
                            for j_id, o_id in list(self.junction_ownership.items()):
                                if o_id == v_id:
                                    self.junction_ownership.pop(j_id, None)
                                    self._log(f"[B2 RELEASE] junction={j_id} owner={v_id} reason=EV_EXITED_SUMO")
                                    self.recovery_manager.start_recovery(
                                        j_id, JUNCTION_PHASE_CONFIG.get(j_id, {}).get("tls_id", j_id), {}, current_time, traci_interface
                                    )
                            self.processed_vehicles.append(v_id)
                            self.active_vehicles.pop(v_id, None)
                            continue

                        if not c_edge:
                            c_edge = traci.vehicle.getRoadID(v_id)
                            c_pos = traci.vehicle.getLanePosition(v_id)
                            c_spd = traci.vehicle.getSpeed(v_id)

                    if c_edge:
                        veh.update_telemetry(c_edge, c_pos, c_spd)
                except Exception:
                    pass

            # State Machine Transitions
            if st == EmergencyState.EMERGENCY_DETECTED:
                self.ev_state_map[v_id] = EmergencyState.VERIFICATION
                self._log(f"Proceeding to token verification for {v_id}.")

            elif st == EmergencyState.VERIFICATION:
                payload = self.request_payload_map.get(v_id, {})
                if verify_emergency_request(payload):
                    veh.verified = True
                    self._log(f"Token verification PASSED for {v_id}.")
                    self.ev_state_map[v_id] = EmergencyState.PREEMPTION
                    self.ev_state_start_time[v_id] = current_time
                else:
                    veh.verified = False
                    self._log(f"Token verification FAILED for {v_id}. Emergency preemption REJECTED.")
                    self.processed_vehicles.append(v_id)
                    self.active_vehicles.pop(v_id, None)

            elif st == EmergencyState.PREEMPTION:
                target_j = self._get_current_next_junction(veh)
                if target_j and self.junction_ownership.get(target_j) == v_id:
                    in_e, out_e = veh.get_edges_for_junction(target_j)
                    req_phase = determine_required_phase(target_j, vehicle_approach_edge=in_e, to_edge=out_e, phase_config=self.phase_config)
                    tls_id = self.phase_config.get(target_j, {}).get("tls_id", target_j)
                    execute_preemption(target_j, tls_id, req_phase, traci_interface)

                    self._log(f"[EV ROUTE MAPPING] EV={v_id} | junction={target_j} | approach={in_e} | to_edge={out_e} | target_phase={req_phase}")
                    self._log(f"[B2 OWNERSHIP] junction={target_j} owner={v_id} reason=PREEMPTION_ACTIVATED (target_phase={req_phase})")
                    self._log(f"Junction {target_j} green phase {req_phase} activated for {v_id}.")
                    self.ev_state_map[v_id] = EmergencyState.GREEN_CORRIDOR
                    self.ev_state_start_time[v_id] = current_time

            elif st == EmergencyState.GREEN_CORRIDOR:
                curr_j = self._get_current_next_junction(veh)
                if curr_j and self.junction_ownership.get(curr_j) == v_id:
                    in_e, out_e = veh.get_edges_for_junction(curr_j)
                    req_phase = determine_required_phase(curr_j, vehicle_approach_edge=in_e, to_edge=out_e, phase_config=self.phase_config)
                    tls_id = self.phase_config.get(curr_j, {}).get("tls_id", curr_j)

                    try:
                        if traci_interface and hasattr(traci_interface, "get_signal_phase"):
                            actual_p = traci_interface.get_signal_phase(tls_id)
                            if actual_p != req_phase:
                                execute_preemption(curr_j, tls_id, req_phase, traci_interface)
                            else:
                                import traci
                                if traci.isLoaded():
                                    traci.trafficlight.setPhaseDuration(tls_id, 999.0)

                                    leader_info = traci.vehicle.getLeader(v_id, dist=15.0)
                                    if leader_info:
                                        leader_id = leader_info[0]
                                        if leader_id and not leader_id.lower().startswith(("ambulance", "firetruck", "police")):
                                            traci.vehicle.setSpeedMode(leader_id, 31)
                                            traci.vehicle.setSpeed(leader_id, -1)
                    except Exception:
                        pass

                    # Physical Clearance Check
                    has_cleared = False
                    curr_e = veh.current_edge or ""
                    try:
                        import traci
                        if traci.isLoaded() and v_id not in traci.vehicle.getIDList():
                            has_cleared = True
                        elif curr_e and curr_e != in_e:
                            if curr_e.startswith(":") or curr_e == out_e or (
                                veh.edge_ids and curr_e in veh.edge_ids and
                                (in_e not in veh.edge_ids or veh.edge_ids.index(curr_e) > veh.edge_ids.index(in_e))
                            ):
                                if not curr_e.startswith(":"):
                                    has_cleared = True
                    except Exception:
                        pass

                    elapsed = current_time - self.ev_state_start_time.get(v_id, current_time)
                    timeout = 5.0 if not (traci_interface and hasattr(traci_interface, "get_signal_phase")) else 30.0
                    if not has_cleared and elapsed >= timeout:
                        has_cleared = True

                    if has_cleared:
                        self._log(f"[B2 RELEASE] junction={curr_j} owner={v_id} reason=PHYSICAL_CLEARANCE")
                        self._log(f"[PHYSICAL CLEARANCE CONFIRMED] EV={v_id} junction={curr_j} from_edge={in_e} to_edge={out_e} time={current_time:.1f}s")
                        self.junction_ownership.pop(curr_j, None)
                        self.recovery_manager.start_recovery(curr_j, tls_id, {}, current_time, traci_interface)
                        self.ev_current_j_idx[v_id] = self.ev_current_j_idx.get(v_id, 0) + 1
                        self.ev_state_map[v_id] = EmergencyState.AMBULANCE_PASSING

            elif st == EmergencyState.AMBULANCE_PASSING:
                j_idx = self.ev_current_j_idx.get(v_id, 0)
                cleared_j = veh.junction_ids[j_idx - 1] if (j_idx > 0 and j_idx - 1 < len(veh.junction_ids)) else ""
                self._log(f"Ambulance cleared junction {cleared_j}.")

                if j_idx < len(veh.junction_ids):
                    self.ev_state_map[v_id] = EmergencyState.PREEMPTION
                else:
                    self._log(f"Route cleared for {v_id}. Transitioning to RECOVERY mode.")
                    self.ev_state_map[v_id] = EmergencyState.RECOVERY
                    self.ev_state_start_time[v_id] = current_time

            elif st == EmergencyState.RECOVERY:
                all_recovered = True
                for j_id in veh.junction_ids:
                    if not self.recovery_manager.is_recovery_complete(j_id, current_time):
                        all_recovered = False
                        break
                if all_recovered or (current_time - self.ev_state_start_time.get(v_id, current_time)) >= 3.0:
                    self.ev_state_map[v_id] = EmergencyState.HAND_BACK

            elif st == EmergencyState.HAND_BACK:
                for j_id, o_id in list(self.junction_ownership.items()):
                    if o_id == v_id:
                        self.junction_ownership.pop(j_id, None)
                        self._log(f"[B2 RELEASE] junction={j_id} owner={v_id} reason=HAND_BACK_CLEANUP")
                self.processed_vehicles.append(v_id)
                self.active_vehicles.pop(v_id, None)
                self._log(f"[HAND_BACK] Completed emergency preemption & recovery for {v_id}.")

        return self.state
