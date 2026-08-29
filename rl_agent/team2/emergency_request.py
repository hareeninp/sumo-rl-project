"""
emergency_request.py - Emergency Request Generator

Generates complete emergency request dictionaries, attaches a secure verification
token, and registers the token with the runtime verification service.
"""

from typing import Dict, Any, Optional
from rl_agent.team2.token_service import generate_verification_token
from rl_agent.team2.verification import register_token


def create_emergency_request(
    vehicle_id: str,
    emergency_type: str = "TRAUMA",
    priority: int = 1,
    start_location: Optional[Dict[str, float]] = None,
    vehicle_type: str = "AMBULANCE"
) -> Dict[str, Any]:
    """
    Creates a new emergency request with an automatically generated and registered verification token.

    Args:
        vehicle_id: ID string for the vehicle (e.g., 'AMB-001').
        emergency_type: Type of emergency (e.g., 'TRAUMA', 'CARDIAC').
        priority: Priority integer (e.g., 1 for critical).
        start_location: Dict with 'latitude' and 'longitude'.
        vehicle_type: Vehicle type string (default 'AMBULANCE').

    Returns:
        JSON-serializable emergency request dictionary.
    """
    if start_location is None:
        start_location = {"latitude": 13.0827, "longitude": 80.2707}

    token = generate_verification_token()
    register_token(token)

    request_payload = {
        "vehicleId": vehicle_id,
        "vehicleType": vehicle_type,
        "emergencyType": emergency_type,
        "priority": priority,
        "startLocation": start_location,
        "verificationToken": token,
    }

    return request_payload
