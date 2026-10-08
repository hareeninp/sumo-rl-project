from database import SessionLocal
from diversion import find_diversion_hospital


db = SessionLocal()

result = find_diversion_hospital(
    db,
    "H1",
    ["H1", "H2"],
    {
        "ICU_BED": 2,
        "VENTILATOR": 1
    }
)

print("Diversion hospital:", result)

db.close()