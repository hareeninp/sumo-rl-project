from typing import Optional, Literal
from pydantic import BaseModel, model_validator

Role = Literal["police", "hospital", "disaster_authority"]
IncidentState = Literal["reported", "verified", "active", "cleared", "archived"]
IncidentType = Literal["accident", "congestion", "blockage", "breakdown", "flood", "construction", "other"]

# Valid forward transitions only - no skipping, no going backward.
VALID_TRANSITIONS = {
    "reported": {"verified"},
    "verified": {"active"},
    "active": {"cleared"},
    "cleared": {"archived"},
    "archived": set(),
}


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Role
    hospital_id: Optional[str] = None

    @model_validator(mode="after")
    def hospital_requires_id(self):
        # Cross-field check via model_validator (not field_validator): a field_validator
        # does NOT run when a field is left at its default (hospital_id=None omitted from
        # the request) unless validate_default=True is set - model_validator always runs
        # after the whole model is built, regardless of which fields used defaults.
        if self.role == "hospital" and not self.hospital_id:
            raise ValueError("hospital_id is required when role is 'hospital'")
        return self


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: Role
    hospital_id: Optional[str] = None
    expires_at: str


class ClosureCreate(BaseModel):
    edge_id: str
    reason: str


class ClosureOut(BaseModel):
    id: str
    edge_id: str
    reason: str
    status: str
    created_by_role: str
    created_at: str
    released_at: Optional[str] = None


class IncidentCreate(BaseModel):
    incident_type: IncidentType
    description: Optional[str] = None
    edge_id: Optional[str] = None


class IncidentUpdateState(BaseModel):
    new_state: IncidentState


class IncidentOut(BaseModel):
    id: str
    edge_id: Optional[str]
    incident_type: str
    description: Optional[str]
    state: str
    created_by_role: str
    created_at: str
    updated_at: str
