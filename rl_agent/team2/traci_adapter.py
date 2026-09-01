"""
traci_adapter.py - Decoupled Injectable TraCI Adapter & Mock Provider

Decouples Team 2 code from any physical file location of Team 1's TraCI implementation.
Provides an injectable interface (TraCIAdapter) and a mock fallback (MockTraCIAdapter)
for offline testing without requiring SUMO or local traci files.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MockTraCIAdapter:
    """
    Mock implementation of Team 1's TraCI interface functions for offline testing without SUMO.
    """

    def __init__(self):
        self.step_counter: int = 0
        self.sim_running: bool = False
        self.active_phases: Dict[str, int] = {}
        self.mock_queue_lengths: Dict[str, int] = {}

    def start_sim(self, sumocfg_path: str = "", gui: bool = False) -> None:
        self.sim_running = True
        self.step_counter = 0
        logger.info(f"[MOCK TraCI] Simulation started with config: '{sumocfg_path}'")

    def step(self) -> None:
        if self.sim_running:
            self.step_counter += 1

    def close_sim(self) -> None:
        self.sim_running = False
        logger.info("[MOCK TraCI] Simulation closed.")

    def get_lane_vehicle_count(self, lane_id: str) -> int:
        return self.mock_queue_lengths.get(lane_id, 3)

    def get_lane_mean_speed(self, lane_id: str) -> float:
        return 12.5

    def get_queue_length(self, lane_id: str) -> int:
        return self.mock_queue_lengths.get(lane_id, 2)

    def get_signal_phase(self, tls_id: str) -> int:
        return self.active_phases.get(tls_id, 0)

    def set_signal_phase(self, tls_id: str, phase_id: int) -> bool:
        self.active_phases[tls_id] = phase_id
        return True

    def can_change_phase(self, tls_id: str, current_time: float) -> bool:
        return True

    def force_phase_change(self, tls_id: str, target_phase: int) -> None:
        self.active_phases[tls_id] = target_phase
        logger.info(f"[MOCK TraCI] Forced phase change on TLS '{tls_id}' to Phase {target_phase}.")

    def get_vehicle_position(self, vehicle_id: str) -> float:
        return 150.0

    def get_vehicle_speed(self, vehicle_id: str) -> float:
        return 15.0

    def get_vehicle_edge(self, vehicle_id: str) -> str:
        return "edge_01"

    def get_vehicle_ids(self) -> List[str]:
        return ["ambulance_1", "firetruck_1", "police_1"]

    def get_active_vehicles(self) -> List[str]:
        return self.get_vehicle_ids()

    def get_all_active_evs(self) -> List[str]:
        return ["ambulance_1", "firetruck_1", "police_1"]

    def vehicle_exists(self, vehicle_id: str) -> bool:
        return True

    def get_simulation_time(self) -> float:
        return float(self.step_counter)

    def get_route_to_target(self, vehicle_id: str, target_edge_id: str) -> tuple:
        return (["edge_01", "edge_05", "edge_08"], 120.0)

    def get_emergency_vehicle_junction(self, vehicle_id: str = "ev_1") -> Optional[str]:
        return "J1"

    def get_ev_state(self, vehicle_id: str) -> Dict[str, Any]:
        return {
            "vehicle_id": vehicle_id,
            "active": True,
            "type": "ambulance",
            "phase": "dispatch",
            "condition": None,
            "target": "J9_HOSP3",
            "priority_weight": 2.5,
            "position": (150.0, 150.0),
            "speed": 15.0,
            "current_edge": "edge_01"
        }

    def get_ev_priority(self, vehicle_id: str) -> float:
        return 2.5

    def get_junction_state(self, junction_id: str, tls_id: str, lanes: List[str]) -> Dict[str, Any]:
        queues = {lane: self.get_queue_length(lane) for lane in lanes}
        speeds = {lane: self.get_lane_mean_speed(lane) for lane in lanes}
        return {
            "junction_id": junction_id,
            "tls_id": tls_id,
            "current_phase": self.get_signal_phase(tls_id),
            "queues": queues,
            "speeds": speeds,
            "sim_step": self.step_counter,
        }


# Global injected provider instance or module reference
_INJECTED_PROVIDER: Optional[Any] = None
_PROVIDER_EXPLICITLY_SET: bool = False


def _get_default_provider() -> Optional[Any]:
    """Attempts to auto-detect Team 1's traci_interface if available in system path."""
    try:
        from traci_interface import traci_interface as mod
        return mod
    except ImportError:
        try:
            import traci_interface
            return traci_interface
        except ImportError:
            return None


def set_traci_provider(provider: Optional[Any]) -> None:
    """
    Injects Team 1's actual TraCI module or adapter instance at runtime.

    Args:
        provider: Module or object implementing the TraCI public interface functions.
    """
    global _INJECTED_PROVIDER, _PROVIDER_EXPLICITLY_SET
    _INJECTED_PROVIDER = provider
    _PROVIDER_EXPLICITLY_SET = True
    if provider:
        logger.info(f"[TraCI ADAPTER] Injecting external TraCI provider: {provider}")
    else:
        logger.info("[TraCI ADAPTER] Provider cleared. Falling back to MockTraCIAdapter.")


class TraCIAdapter:
    """
    Unified TraCI Adapter interface. Delegates calls to injected provider if available,
    otherwise falls back to MockTraCIAdapter.
    """

    def __init__(self, provider: Optional[Any] = None):
        self._provider = provider
        self._mock_fallback = MockTraCIAdapter()

    @property
    def _active_interface(self) -> Any:
        if self._provider is not None:
            return self._provider
        if _INJECTED_PROVIDER is not None:
            return _INJECTED_PROVIDER
        if not _PROVIDER_EXPLICITLY_SET:
            default_p = _get_default_provider()
            if default_p is not None:
                return default_p
        return self._mock_fallback

    def start_sim(self, sumocfg_path: str = "", gui: bool = False) -> None:
        target = self._active_interface
        if hasattr(target, "start_sim"):
            try:
                target.start_sim(sumocfg_path, gui=gui)
            except TypeError:
                target.start_sim(sumocfg_path)

    def step(self) -> None:
        target = self._active_interface
        if hasattr(target, "step"):
            target.step()

    def close_sim(self) -> None:
        target = self._active_interface
        if hasattr(target, "close_sim"):
            target.close_sim()

    def get_lane_vehicle_count(self, lane_id: str) -> int:
        target = self._active_interface
        if hasattr(target, "get_lane_vehicle_count"):
            return target.get_lane_vehicle_count(lane_id)
        return 0

    def get_lane_mean_speed(self, lane_id: str) -> float:
        target = self._active_interface
        if hasattr(target, "get_lane_mean_speed"):
            return target.get_lane_mean_speed(lane_id)
        return 0.0

    def get_queue_length(self, lane_id: str) -> int:
        target = self._active_interface
        if hasattr(target, "get_queue_length"):
            return target.get_queue_length(lane_id)
        return 0

    def get_signal_phase(self, tls_id: str) -> int:
        target = self._active_interface
        if hasattr(target, "get_signal_phase"):
            return target.get_signal_phase(tls_id)
        return 0

    def set_signal_phase(self, tls_id: str, phase_id: int) -> bool:
        target = self._active_interface
        if hasattr(target, "set_signal_phase"):
            return target.set_signal_phase(tls_id, phase_id)
        return False

    def can_change_phase(self, tls_id: str, current_time: float) -> bool:
        target = self._active_interface
        if hasattr(target, "can_change_phase"):
            return target.can_change_phase(tls_id, current_time)
        return True

    def force_phase_change(self, tls_id: str, target_phase: int) -> None:
        target = self._active_interface
        if hasattr(target, "force_phase_change"):
            target.force_phase_change(tls_id, target_phase)

    def get_vehicle_position(self, vehicle_id: str) -> float:
        target = self._active_interface
        if hasattr(target, "get_vehicle_position"):
            val = target.get_vehicle_position(vehicle_id)
            if isinstance(val, (int, float)):
                return float(val)
            elif isinstance(val, (tuple, list)):
                return float(val[0]) if len(val) > 0 else 0.0
        return 0.0

    def get_vehicle_speed(self, vehicle_id: str) -> float:
        target = self._active_interface
        if hasattr(target, "get_vehicle_speed"):
            return target.get_vehicle_speed(vehicle_id)
        return 15.0

    def get_vehicle_edge(self, vehicle_id: str) -> str:
        target = self._active_interface
        if hasattr(target, "get_vehicle_edge"):
            return target.get_vehicle_edge(vehicle_id)
        return ""

    def get_vehicle_ids(self) -> List[str]:
        target = self._active_interface
        if hasattr(target, "get_vehicle_ids"):
            return target.get_vehicle_ids()
        return []

    def get_active_vehicles(self) -> List[str]:
        target = self._active_interface
        if hasattr(target, "get_vehicle_ids"):
            return target.get_vehicle_ids()
        elif hasattr(target, "get_active_vehicles"):
            return target.get_active_vehicles()
        return []

    def get_all_active_evs(self) -> List[str]:
        target = self._active_interface
        if hasattr(target, "get_all_active_evs"):
            return target.get_all_active_evs()
        return []

    def vehicle_exists(self, vehicle_id: str) -> bool:
        target = self._active_interface
        if hasattr(target, "vehicle_exists"):
            return target.vehicle_exists(vehicle_id)
        return False

    def get_simulation_time(self) -> float:
        target = self._active_interface
        if hasattr(target, "get_simulation_time"):
            return target.get_simulation_time()
        return 0.0

    def get_route_to_target(self, vehicle_id: str, target_edge_id: str) -> tuple:
        target = self._active_interface
        if hasattr(target, "get_route_to_target"):
            return target.get_route_to_target(vehicle_id, target_edge_id)
        return ([], float("inf"))

    def get_vehicle_route(self, vehicle_id: str) -> List[str]:
        target = self._active_interface
        if hasattr(target, "get_vehicle_route"):
            res = target.get_vehicle_route(vehicle_id)
            if res:
                return list(res)
        try:
            import traci
            if traci.isLoaded() and vehicle_id in traci.vehicle.getIDList():
                return list(traci.vehicle.getRoute(vehicle_id))
        except Exception:
            pass
        return []

    def get_emergency_vehicle_junction(self, vehicle_id: str = "ev_1") -> Optional[str]:
        target = self._active_interface
        if hasattr(target, "get_emergency_vehicle_junction"):
            return target.get_emergency_vehicle_junction(vehicle_id)
        return None

    def get_ev_state(self, vehicle_id: str) -> Dict[str, Any]:
        target = self._active_interface
        if hasattr(target, "get_ev_state"):
            return target.get_ev_state(vehicle_id)
        return {}

    def get_ev_priority(self, vehicle_id: str) -> float:
        target = self._active_interface
        if hasattr(target, "get_ev_priority"):
            return target.get_ev_priority(vehicle_id)
        return 1.0

    def get_junction_state(self, junction_id: str, tls_id: str, lanes: List[str]) -> Dict[str, Any]:
        target = self._active_interface
        if hasattr(target, "get_junction_state"):
            return target.get_junction_state(junction_id, tls_id, lanes)
        return {"current_phase": 0, "queues": {lane: 0 for lane in lanes}}


def get_traci_adapter(provider: Optional[Any] = None) -> TraCIAdapter:
    """
    Factory function returning a TraCIAdapter instance.
    """
    return TraCIAdapter(provider)
