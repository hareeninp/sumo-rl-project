from database import SessionLocal
from ranking import rank_hospitals


db = SessionLocal()

results = rank_hospitals(
    db,
    ["H1", "H2"],
    {
        "ICU_BED": 2,
        "VENTILATOR": 1
    }
)

print("Ranked hospitals:")

for hospital in results:
    print(hospital)

db.close()