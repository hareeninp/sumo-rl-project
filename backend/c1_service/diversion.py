from sqlalchemy.orm import Session

from ranking import rank_hospitals


def find_diversion_hospital(
    db: Session,
    current_hospital_id: str,
    hospital_ids: list[str],
    required_resources: dict
):
    candidate_hospitals = [
        hospital_id
        for hospital_id in hospital_ids
        if hospital_id != current_hospital_id
    ]

    ranked_hospitals = rank_hospitals(
        db,
        candidate_hospitals,
        required_resources
    )

    if not ranked_hospitals:
        return None

    return ranked_hospitals[0]