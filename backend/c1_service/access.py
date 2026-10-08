from fastapi import HTTPException


def validate_hospital_access(
    session_hospital_id: str,
    requested_hospital_id: str
):
    if session_hospital_id != requested_hospital_id:
        raise HTTPException(
            status_code=403,
            detail="Hospital is not authorized to access this resource"
        )

    return True