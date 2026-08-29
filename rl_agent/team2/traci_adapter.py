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
    Mock implementation of Team 1's 14 TraCI functions for offline testing without SUMO.
    """

    def __init__(self):
        self.step_counter: int = 0
        self.sim_running: bool = False
        self.active_phases: Dict[str, int] = {}
        self.mock_queue_lengths: Dict[str, int] = {}

    def start_sim(self, sumocfg_path: str = "") -> None:
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

    def set_signal_phase(self, tls_id: str, phase_id: int) -> None:
        self.active_phases[tls_id] = phase_id

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


def set_traci_provider(provider: Optional[Any]) -> None:
    """
    Injects Team 1's actual TraCI module or adapter instance at runtime.

    Args:
        provider: Module or object implementing the 14 TraCI functions.
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
        return self._mock_fallback

    def start_sim(self, sumocfg_path: str = "") -> None:
        target = self._active_interface
        if hasattr(target, "start_sim"):
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

    def set_signal_phase(self, tls_id: str, phase_id: int) -> None:
        target = self._active_interface
        if hasattr(target, "set_signal_phase"):
            target.set_signal_phase(tls_id, phase_id)

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
            return target.get_vehicle_position(vehicle_id)
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
