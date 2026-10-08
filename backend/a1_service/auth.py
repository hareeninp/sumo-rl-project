import secrets
import hashlib
import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session as DBSession

from .database import get_db
from .models import User, Session

TOKEN_TTL_HOURS = 12
PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Salted PBKDF2-SHA256, stdlib only - avoids passlib/bcrypt version-compat issues.
    Adequate for a hackathon Day-1 stub; format: 'salt_hex$hash_hex'."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest_hex = password_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return secrets.compare_digest(check.hex(), digest_hex)


def create_session(db: DBSession, user: User) -> Session:
    token = secrets.token_hex(32)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_TTL_HOURS)
    session = Session(
        token=token,
        user_id=user.id,
        role=user.role,
        hospital_id=user.hospital_id,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_session(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db),
) -> Session:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.split(" ", 1)[1]
    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if session.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expired")
    return session


def require_role(*allowed_roles: str):
    def dependency(session: Session = Depends(get_current_session)) -> Session:
        if session.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{session.role}' not permitted; requires one of {allowed_roles}",
            )
        return session
    return dependency
