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
    Calculates estimated time of arrival (ETA in seconds) for an emergency vehicle at a target junction.
    """
    route_junctions = vehicle.junction_ids or vehicle.route
    if not route_junctions or target_junction_id not in route_junctions:
        return 9999.0

    adapter: TraCIAdapter = get_traci_adapter(traci_interface)
    speed = vehicle.speed if vehicle.speed > 0 else DEFAULT_AMBULANCE_SPEED

    try:
        live_speed = adapter.get_vehicle_speed(vehicle.vehicle_id)
        if live_speed and live_speed > 0:
            speed = live_speed

        curr_edge = adapter.get_vehicle_edge(vehicle.vehicle_id)
        if curr_edge and vehicle.edge_ids and curr_edge in vehicle.edge_ids:
            curr_edge_idx = vehicle.edge_ids.index(curr_edge)
            target_j_idx = route_junctions.index(target_junction_id)
            # If vehicle is on an edge past the target junction, ETA is 0.0s (already reached/passed)
            if curr_edge_idx > target_j_idx:
                return 0.0
    except Exception:
        pass

    target_idx = route_junctions.index(target_junction_id)
    pos_val = vehicle.current_position
    if isinstance(pos_val, (tuple, list)):
        pos_float = float(pos_val[0]) if len(pos_val) > 0 else 0.0
    else:
        pos_float = float(pos_val)

    # Dynamic distance calculation based on remaining route index
    if vehicle.current_edge and vehicle.edge_ids and vehicle.current_edge in vehicle.edge_ids:
        c_idx = vehicle.edge_ids.index(vehicle.current_edge)
        t_idx = route_junctions.index(target_junction_id)
        remaining_edges = max(0, t_idx - c_idx)
        effective_distance = max(0.0, remaining_edges * 150.0 - pos_float)
    else:
        base_distance = (target_idx + 1) * DEFAULT_JUNCTION_DISTANCE - pos_float
        effective_distance = max(0.0, base_distance)

    eta_seconds = effective_distance / speed
    return round(eta_seconds, 1)
