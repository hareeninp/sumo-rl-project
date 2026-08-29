"""
eta.py - Arrival Time Prediction for Emergency Vehicles

Estimates the arrival time (ETA in seconds) of an emergency vehicle at each target
junction along its route using the TraCI adapter or configurable route distance fallbacks.
"""

import logging
from typing import Optional, Any
from rl_agent.team2.emergency_vehicle import EmergencyVehicle
from rl_agent.team2.emergency_config import DEFAULT_AMBULANCE_SPEED, DEFAULT_JUNCTION_DISTANCE
from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter

logger = logging.getLogger(__name__)


def calculate_eta(
    vehicle: EmergencyVehicle,
    target_junction_id: str,
    traci_interface: Optional[Any] = None,
    current_time: float = 0.0
) -> float:
    """
    Calculates estimated time of arrival (ETA in seconds) for an ambulance at a target junction.
    """
    route_junctions = vehicle.junction_ids or vehicle.route
    if not route_junctions or target_junction_id not in route_junctions:
        logger.warning(f"Target junction '{target_junction_id}' not found in route for vehicle '{vehicle.vehicle_id}'.")
        return 9999.0

    adapter: TraCIAdapter = get_traci_adapter(traci_interface)
    speed = vehicle.speed if vehicle.speed > 0 else DEFAULT_AMBULANCE_SPEED

    try:
        live_speed = adapter.get_vehicle_speed(vehicle.vehicle_id)
        if live_speed and live_speed > 0:
            speed = live_speed
    except Exception:
        pass

    target_idx = route_junctions.index(target_junction_id)
    base_distance = (target_idx + 1) * DEFAULT_JUNCTION_DISTANCE - vehicle.current_position
    effective_distance = max(0.0, base_distance)

    eta_seconds = effective_distance / speed
    logger.debug(
        f"ETA for {vehicle.vehicle_id} to {target_junction_id}: "
        f"{eta_seconds:.1f}s (Distance: {effective_distance:.0f}m, Speed: {speed:.1f}m/s)"
    )

    return round(eta_seconds, 1)
