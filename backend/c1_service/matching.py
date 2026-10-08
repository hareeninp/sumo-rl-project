from sqlalchemy.orm import Session

from models import HospitalResource


def check_hospital_capability(
    db: Session,
    hospital_id: str,
    required_resources: dict
):
    for resource_type, required_amount in required_resources.items():

        resource = (
            db.query(HospitalResource)
            .filter(
                HospitalResource.hospital_id == hospital_id,
                HospitalResource.resource_type == resource_type
            )
            .first()
        )

        if resource is None:
            return False

        if resource.available < required_amount:
            return False

    return True