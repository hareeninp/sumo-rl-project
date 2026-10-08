"""
main.py - A1: Login/Role Service + Closure Interface (F1) + Incident Lifecycle

Day 1 stub, per team decision:
  - Stack: FastAPI (Python) - matches SUMO/TraCI and B1's RL stack, one language across the team.
  - Storage: SQLite file (a1_service.db) - real persistence across restarts, zero setup.
  - Closure <-> SUMO wiring: deliberately NOT connected yet. This service only writes closure
    state; A2 consumes it on their own timeline (Day 4 cross-feature wiring). Do not import
    traci/team2 code here.
  - Roles: police | hospital | disaster_authority. Hospital sessions carry hospital_id so
    C1's hospital-scoped access control has something to check against from day one.
  - Incident lifecycle: reported -> verified -> active -> cleared -> archived (fixed states,
    forward-only transitions). Only 'active' incidents are meant to affect routing/closures
    downstream - reported/verified are pre-confirmation and must not block anything yet.

Run:
    uvicorn a1_service.main:app --reload --port 8001

This runs on its own port (8001), separate from team1's SUMO backend (port 5000 / api.py),
since login/closures/incidents are a distinct concern from the SUMO simulation itself.
"""

import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession

from .database import Base, engine, get_db
from .models import User, Closure, Incident
from .schemas import (
    RegisterRequest, LoginRequest, LoginResponse,
    ClosureCreate, ClosureOut,
    IncidentCreate, IncidentUpdateState, IncidentOut,
    VALID_TRANSITIONS,
)
from .auth import hash_password, verify_password, create_session, get_current_session, require_role

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ResQRoute A1 Service", version="0.1.0-stub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before final submission
    allow_methods=["*"],
    allow_headers=["*"],
)


def iso(dt):
    return dt.isoformat() if dt else None


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/a1/health")
def health():
    return {"status": "ok", "service": "a1_service"}


# ============================================================
# AUTH / ROLES
# ============================================================

@app.post("/api/a1/auth/register", status_code=201)
def register(req: RegisterRequest, db: DBSession = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        hospital_id=req.hospital_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role, "hospital_id": user.hospital_id}


@app.post("/api/a1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    session = create_session(db, user)
    return LoginResponse(
        token=session.token,
        role=session.role,
        hospital_id=session.hospital_id,
        expires_at=iso(session.expires_at),
    )


@app.get("/api/a1/auth/me")
def me(session=Depends(get_current_session)):
    return {"role": session.role, "hospital_id": session.hospital_id, "expires_at": iso(session.expires_at)}


# ============================================================
# CLOSURE INTERFACE (F1)
# Any authenticated role may create a closure request in this stub;
# tighten to police/disaster_authority only once real rules are confirmed.
# NOTE: writing here does NOT touch SUMO. A2 reads this table/endpoint on their own schedule.
# ============================================================

@app.post("/api/a1/closures", response_model=ClosureOut, status_code=201)
def create_closure(
    req: ClosureCreate,
    db: DBSession = Depends(get_db),
    session=Depends(require_role("police", "disaster_authority")),
):
    closure = Closure(
        edge_id=req.edge_id,
        reason=req.reason,
        created_by=session.user_id,
        created_by_role=session.role,
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)
    return ClosureOut(
        id=closure.id, edge_id=closure.edge_id, reason=closure.reason, status=closure.status,
        created_by_role=closure.created_by_role, created_at=iso(closure.created_at),
        released_at=iso(closure.released_at),
    )


@app.get("/api/a1/closures", response_model=list[ClosureOut])
def list_closures(status: str | None = None, db: DBSession = Depends(get_db)):
    """Public read (no auth) - A2 and the frontend both need to poll this freely."""
    q = db.query(Closure)
    if status:
        q = q.filter(Closure.status == status)
    return [
        ClosureOut(
            id=c.id, edge_id=c.edge_id, reason=c.reason, status=c.status,
            created_by_role=c.created_by_role, created_at=iso(c.created_at), released_at=iso(c.released_at),
        )
        for c in q.all()
    ]


@app.post("/api/a1/closures/{closure_id}/release", response_model=ClosureOut)
def release_closure(
    closure_id: str,
    db: DBSession = Depends(get_db),
    session=Depends(require_role("police", "disaster_authority")),
):
    closure = db.query(Closure).filter(Closure.id == closure_id).first()
    if closure is None:
        raise HTTPException(status_code=404, detail="Closure not found")
    closure.status = "released"
    closure.released_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(closure)
    return ClosureOut(
        id=closure.id, edge_id=closure.edge_id, reason=closure.reason, status=closure.status,
        created_by_role=closure.created_by_role, created_at=iso(closure.created_at),
        released_at=iso(closure.released_at),
    )


# ============================================================
# INCIDENT LIFECYCLE
# reported -> verified -> active -> cleared -> archived (forward-only)
# ============================================================

@app.post("/api/a1/incidents", response_model=IncidentOut, status_code=201)
def create_incident(
    req: IncidentCreate,
    db: DBSession = Depends(get_db),
    session=Depends(get_current_session),  # any authenticated role can report
):
    incident = Incident(
        incident_type=req.incident_type,
        description=req.description,
        edge_id=req.edge_id,
        created_by=session.user_id,
        created_by_role=session.role,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return IncidentOut(
        id=incident.id, edge_id=incident.edge_id, incident_type=incident.incident_type,
        description=incident.description, state=incident.state, created_by_role=incident.created_by_role,
        created_at=iso(incident.created_at), updated_at=iso(incident.updated_at),
    )


@app.get("/api/a1/incidents", response_model=list[IncidentOut])
def list_incidents(state: str | None = None, db: DBSession = Depends(get_db)):
    """Public read - B3 polls this to know which incidents are 'active' and affect routing."""
    q = db.query(Incident)
    if state:
        q = q.filter(Incident.state == state)
    return [
        IncidentOut(
            id=i.id, edge_id=i.edge_id, incident_type=i.incident_type, description=i.description,
            state=i.state, created_by_role=i.created_by_role, created_at=iso(i.created_at),
            updated_at=iso(i.updated_at),
        )
        for i in q.all()
    ]


@app.patch("/api/a1/incidents/{incident_id}/state", response_model=IncidentOut)
def update_incident_state(
    incident_id: str,
    req: IncidentUpdateState,
    db: DBSession = Depends(get_db),
    session=Depends(require_role("police", "disaster_authority", "hospital")),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    allowed_next = VALID_TRANSITIONS.get(incident.state, set())
    if req.new_state not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition '{incident.state}' -> '{req.new_state}'. "
                   f"Allowed from '{incident.state}': {sorted(allowed_next) or 'none (terminal state)'}",
        )

    incident.state = req.new_state
    incident.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(incident)
    return IncidentOut(
        id=incident.id, edge_id=incident.edge_id, incident_type=incident.incident_type,
        description=incident.description, state=incident.state, created_by_role=incident.created_by_role,
        created_at=iso(incident.created_at), updated_at=iso(incident.updated_at),
    )
