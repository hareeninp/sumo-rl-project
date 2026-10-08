from sqlalchemy.orm import Session

from models import HospitalResource


def rank_hospitals(
    db: Session,
    hospital_ids: list[str],
    required_resources: dict
):
    results = []

    for hospital_id in hospital_ids:

        can_handle = True
        resource_score = 0

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
                can_handle = False
                break

            if resource.available < required_amount:
                can_handle = False
                break

            resource_score += resource.available

        if can_handle:
            results.append({
                "hospital_id": hospital_id,
                "resource_score": resource_score
            })

    results.sort(
        key=lambda hospital: hospital["resource_score"],
        reverse=True
    )

    return results