"""
team3_adapter.py - Team 3 Hospital Recommendation & Route Optimization Adapter

Provides a clean interface to Team 3's API endpoints:
  - POST /api/hospitals/recommend
  - POST /api/route/calculate

Supports live HTTP requests with configurable TEAM3_BASE_URL and built-in
offline mock fallbacks for unit testing without requiring Team 3 backend running.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configurable Base URL for Team 3 Backend API
TEAM3_BASE_URL: str = "http://localhost:3000"


def _get_mock_hospital_recommendation(emergency_type: str = "TRAUMA") -> Dict[str, Any]:
    """Returns realistic mock hospital recommendation response."""
    return {
        "success": True,
        "data": {
            "recommendedHospital": {
                "hospitalId": "H001",
                "name": "City General Hospital",
                "speciality": emergency_type.upper(),
                "medicalFitScore": 0.92
            },
            "reason": f"Best medical suitability for {emergency_type} and estimated travel time."
        }
    }


def _get_mock_route_calculation(vehicle_id: str, hospital_id: str) -> Dict[str, Any]:
    """Returns realistic mock route calculation response."""
    return {
        "success": True,
        "data": {
            "routeId": "R001",
            "edgeIds": ["edge_01", "edge_05", "edge_08"],
            "junctionIds": ["J1", "J2", "J3"],
            "distanceKm": 7.2,
            "etaMinutes": 9,
            "trafficLevel": "MODERATE",
            "optimization": "LIVE_ETA"
        }
    }


def request_hospital_recommendation(
    request_payload: Dict[str, Any],
    base_url: Optional[str] = None,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Calls Team 3 hospital recommendation API endpoint or returns mock fallback.

    Args:
        request_payload: Dict containing emergencyType, vehicleId, startLocation.
        base_url: Optional base URL override.
        use_mock: Force offline mock response.

    Returns:
        Recommendation payload dictionary.
    """
    if use_mock:
        return _get_mock_hospital_recommendation(request_payload.get("emergencyType", "TRAUMA"))

    target_url = (base_url or TEAM3_BASE_URL).rstrip("/") + "/api/hospitals/recommend"
    payload = {
        "emergencyType": request_payload.get("emergencyType", "TRAUMA"),
        "vehicleId": request_payload.get("vehicleId"),
        "startLocation": request_payload.get("startLocation", {})
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        logger.info(f"Team 3 live API call to {target_url} unavailable ({e}). Using offline mock response.")
        return _get_mock_hospital_recommendation(request_payload.get("emergencyType", "TRAUMA"))


def request_route_calculation(
    request_payload: Dict[str, Any],
    hospital_id: str,
    base_url: Optional[str] = None,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Calls Team 3 route calculation API endpoint or returns mock fallback.

    Args:
        request_payload: Dict containing vehicleId, startLocation, vehicleType.
        hospital_id: Target hospital ID.
        base_url: Optional base URL override.
        use_mock: Force offline mock response.

    Returns:
        Route calculation payload dictionary.
    """
    if use_mock:
        return _get_mock_route_calculation(request_payload.get("vehicleId", "AMB-001"), hospital_id)

    target_url = (base_url or TEAM3_BASE_URL).rstrip("/") + "/api/route/calculate"
    payload = {
        "vehicleId": request_payload.get("vehicleId"),
        "vehicleType": request_payload.get("vehicleType", "AMBULANCE"),
        "startLocation": request_payload.get("startLocation", {}),
        "hospitalId": hospital_id
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        logger.info(f"Team 3 live API call to {target_url} unavailable ({e}). Using offline mock response.")
        return _get_mock_route_calculation(request_payload.get("vehicleId", "AMB-001"), hospital_id)


def request_emergency_routing(
    request_payload: Dict[str, Any],
    base_url: Optional[str] = None,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Executes full Team 3 workflow (Hospital Recommendation -> Route Calculation) and
    combines results into unified Team 3 API response format.

    Args:
        request_payload: Dict containing vehicleId, emergencyType, startLocation, etc.
        base_url: Optional base URL override.
        use_mock: Force offline mock response.

    Returns:
        Combined response dictionary containing hospital, route, and traffic metrics.
    """
    rec_resp = request_hospital_recommendation(request_payload, base_url, use_mock)
    hospital_data = rec_resp.get("data", {}).get("recommendedHospital", {})
    hospital_id = hospital_data.get("hospitalId", "H001")
    reason = rec_resp.get("data", {}).get("reason", "Selected based on suitability.")

    route_resp = request_route_calculation(request_payload, hospital_id, base_url, use_mock)
    route_data = route_resp.get("data", {})

    combined_response = {
        "hospital": hospital_data,
        "route": {
            "routeId": route_data.get("routeId", "R001"),
            "edgeIds": route_data.get("edgeIds", []),
            "junctionIds": route_data.get("junctionIds", []),
            "distanceKm": route_data.get("distanceKm", 0.0),
            "etaMinutes": route_data.get("etaMinutes", 0),
        },
        "trafficLevel": route_data.get("trafficLevel", "MODERATE"),
        "optimization": route_data.get("optimization", "LIVE_ETA"),
        "reason": reason
    }

    return combined_response
