"""
emergency_vehicle.py - Emergency Vehicle Data Model

Data structure representing an emergency vehicle (ambulance) requesting
signal priority across a target route of junctions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmergencyVehicle:
    """
    Data model for an emergency vehicle.
    """
    vehicle_id: str
    vehicle_type: str = "AMBULANCE"
    emergency_type: str = "GENERAL"   # e.g., "TRAUMA", "CARDIAC", "GENERAL"
    severity: str = "NORMAL"          # Tier 1 priority: "CRITICAL", "HIGH", "NORMAL"
    priority: int = 1                  # e.g., 1 for critical (backward compatible)
    verified: bool = False
    verification_token: Optional[str] = None
    start_location: Optional[Dict[str, float]] = None

    current_edge: Optional[str] = None
    current_position: float = 0.0      # Distance along current edge (meters)
    speed: float = 15.0                # Current speed (m/s)

    # Route & Destination details (populated from Team 3 response)
    destination: str = ""              # Target hospital ID (e.g., 'H001')
    hospital_id: str = ""
    hospital_name: str = ""
    route_id: str = ""
    edge_ids: List[str] = field(default_factory=list)      # SUMO edge IDs
    junction_ids: List[str] = field(default_factory=list)  # Target junction sequence
    overall_eta_minutes: float = 0.0
    request_time: float = 0.0          # Simulation timestamp when request was made

    @property
    def severity_rank(self) -> int:
        """
        Tier 1 priority rank:
            CRITICAL = 3
            HIGH     = 2
            NORMAL   = 1
        """
        s = (self.severity or "").upper()
        if s == "CRITICAL":
            return 3
        elif s == "HIGH":
            return 2
        return 1

    @property
    def vehicle_type_rank(self) -> int:
        """
        Tier 2 priority rank (used when severity is equal):
            FIRE TRUCK = 3
            AMBULANCE  = 2
            POLICE     = 1
        """
        v = (self.vehicle_type or "").upper()
        if any(k in v for k in ("FIRE", "TRUCK", "FIREBRIGADE")):
            return 3
        elif any(k in v for k in ("AMBULANCE", "AMB", "TRAUMA", "CARDIAC", "EMERGENCY")):
            return 2
        elif any(k in v for k in ("POLICE", "LAW_ENFORCEMENT")):
            return 1
        return 2

    @property
    def route(self) -> List[str]:
        """Alias property mapping route to junction_ids for backward compatibility."""
        return self.junction_ids

    @route.setter
    def route(self, value: List[str]) -> None:
        self.junction_ids = list(value)

    def set_route(self, route: List[str], edge_ids: Optional[List[str]] = None) -> None:
        """
        Updates the vehicle's assigned junction route and edge route.
        """
        self.junction_ids = list(route)
        if edge_ids:
            self.edge_ids = list(edge_ids)

    def update_route(self, junction_ids: List[str], edge_ids: Optional[List[str]] = None) -> None:
        """
        Supports dynamic route updates from Team 3 live optimization.
        """
        self.set_route(junction_ids, edge_ids)

    def update_telemetry(self, current_edge: str, position: float = 0.0, speed: float = 15.0) -> None:
        """
        Updates the vehicle's telemetry data from TraCI.
        """
        self.current_edge = current_edge
        self.current_position = position
        if speed > 0:
            self.speed = speed

    def is_verified(self) -> bool:
        """
        Returns whether the emergency vehicle authorization is verified.
        """
        return self.verified

    @classmethod
    def from_request_and_team3_response(
        cls,
        request_payload: Dict[str, Any],
        team3_response: Dict[str, Any]
    ) -> "EmergencyVehicle":
        """
        Factory method constructing an EmergencyVehicle instance from an emergency request payload
        and Team 3 API response. Safely defaults missing severity/priority to NORMAL.
        """
        hospital_info = team3_response.get("hospital", {})
        route_info = team3_response.get("route", {})

        junction_ids = route_info.get("junctionIds", [])
        edge_ids = route_info.get("edgeIds", [])

        # Parse severity safely (accepting severity string, priority int/string, or defaulting to NORMAL)
        raw_sev = request_payload.get("severity")
        raw_prio = request_payload.get("priority")

        severity = "NORMAL"
        if isinstance(raw_sev, str) and raw_sev.upper() in ("CRITICAL", "HIGH", "NORMAL"):
            severity = raw_sev.upper()
        elif isinstance(raw_prio, str) and raw_prio.upper() in ("CRITICAL", "HIGH", "NORMAL"):
            severity = raw_prio.upper()
        elif isinstance(raw_prio, int):
            if raw_prio == 1:
                severity = "CRITICAL"
            elif raw_prio == 2:
                severity = "HIGH"
            else:
                severity = "NORMAL"

        # Determine vehicle type string
        v_type = request_payload.get("vehicleType") or request_payload.get("vehicle_type") or "AMBULANCE"

        vehicle = cls(
            vehicle_id=request_payload.get("vehicleId", "AMB-001"),
            vehicle_type=v_type,
            emergency_type=request_payload.get("emergencyType", "TRAUMA"),
            severity=severity,
            priority=raw_prio if isinstance(raw_prio, int) else (1 if severity == "CRITICAL" else (2 if severity == "HIGH" else 3)),
            verified=False,
            verification_token=request_payload.get("verificationToken"),
            start_location=request_payload.get("startLocation"),
            destination=hospital_info.get("hospitalId", ""),
            hospital_id=hospital_info.get("hospitalId", ""),
            hospital_name=hospital_info.get("name", ""),
            route_id=route_info.get("routeId", ""),
            edge_ids=edge_ids,
            junction_ids=junction_ids,
            overall_eta_minutes=float(route_info.get("etaMinutes", 0.0)),
        )

        return vehicle
