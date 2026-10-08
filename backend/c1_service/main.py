import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import HospitalResource
from matching import check_hospital_capability
from diversion import find_diversion_hospital
from schemas import HospitalResourceUpdate
from a1_service.auth import get_current_session
from access import validate_hospital_access


app = FastAPI(title="C1 Hospital Service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/hospitals/{hospital_id}/resources")
def get_hospital_resources(
    hospital_id: str,
    db: Session = Depends(get_db)
):
    resources = (
        db.query(HospitalResource)
        .filter(HospitalResource.hospital_id == hospital_id)
        .all()
    )

    return resources


@app.put("/hospitals/{hospital_id}/resources/{resource_id}")
def update_hospital_resource(
    hospital_id: str,
    resource_id: int,
    resource: HospitalResourceUpdate,
    db: Session = Depends(get_db),
    session=Depends(get_current_session)
):
    validate_hospital_access(
        session.hospital_id,
        hospital_id
    )

    hospital_resource = (
        db.query(HospitalResource)
        .filter(
            HospitalResource.id == resource_id,
            HospitalResource.hospital_id == hospital_id
        )
        .first()
    )

    if hospital_resource is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital resource not found"
        )

    hospital_resource.total = resource.total
    hospital_resource.available = resource.available

    db.commit()
    db.refresh(hospital_resource)

    return hospital_resource


@app.post("/hospitals/{hospital_id}/capability-check")
def capability_check(
    hospital_id: str,
    required_resources: dict,
    db: Session = Depends(get_db)
):
    can_handle = check_hospital_capability(
        db,
        hospital_id,
        required_resources
    )

    return {
        "hospital_id": hospital_id,
        "can_handle": can_handle
    }


@app.post("/hospitals/{hospital_id}/diversion")
def diversion_check(
    hospital_id: str,
    hospital_ids: list[str],
    required_resources: dict,
    db: Session = Depends(get_db)
):
    diversion_hospital = find_diversion_hospital(
        db,
        hospital_id,
        hospital_ids,
        required_resources
    )

    if diversion_hospital is None:
        return {
            "current_hospital_id": hospital_id,
            "diversion_available": False,
            "diversion_hospital": None
        }

    return {
        "current_hospital_id": hospital_id,
        "diversion_available": True,
        "diversion_hospital": diversion_hospital
    }