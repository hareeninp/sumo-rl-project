"""
models.py - A1 data model.

Roles: police | hospital | disaster_authority
Hospital-role users carry a hospital_id claim (baked in now per team decision -
C1's "hospital can only touch its own stock" requirement depends on this).

Incident lifecycle (fixed, per project spec - do not rename states later):
    reported -> verified -> active -> cleared -> archived

Only incidents in the 'active' state should affect routing/closures downstream.
'reported' and 'verified' are pre-confirmation states and must NOT block a road
or influence B3's routing yet - that's an explicit, deliberate rule, not an
oversight, so B3 can safely ignore anything not 'active'.
"""

import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from .database import Base


def gen_id():
    return str(uuid.uuid4())


def now():
    return datetime.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'police' | 'hospital' | 'disaster_authority'
    hospital_id = Column(String, nullable=True)  # required if role == 'hospital'
    created_at = Column(DateTime, default=now)


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    hospital_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)
    expires_at = Column(DateTime, nullable=False)


class Closure(Base):
    __tablename__ = "closures"

    id = Column(String, primary_key=True, default=gen_id)
    edge_id = Column(String, nullable=False)          # SUMO edge ID, e.g. "J2_J3"
    reason = Column(String, nullable=False)
    status = Column(String, default="open")           # 'open' | 'released'
    created_by = Column(String, nullable=False)        # user_id
    created_by_role = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)
    released_at = Column(DateTime, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=gen_id)
    edge_id = Column(String, nullable=True)            # nullable: incident may not be edge-specific yet
    incident_type = Column(String, nullable=False)      # accident | congestion | blockage | breakdown | flood | construction | other
    description = Column(String, nullable=True)
    state = Column(String, default="reported")          # reported -> verified -> active -> cleared -> archived
    created_by = Column(String, nullable=False)
    created_by_role = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now)
