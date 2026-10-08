from database import SessionLocal
from matching import check_hospital_capability


db = SessionLocal()

result = check_hospital_capability(
    db,
    "H1",
    {
        "BLOOD_BANK": 1
    }
)

print("Capability match:", result)

db.close()