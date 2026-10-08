from database import Base, engine, SessionLocal
from models import HospitalResource


Base.metadata.create_all(bind=engine)


db = SessionLocal()


resources = [
    HospitalResource(
        hospital_id="H1",
        resource_type="EMERGENCY_ROOM",
        total=10,
        available=10
    ),
    HospitalResource(
        hospital_id="H1",
        resource_type="ICU_BED",
        total=20,
        available=8
    ),
    HospitalResource(
        hospital_id="H1",
        resource_type="VENTILATOR",
        total=10,
        available=5
    ),
    HospitalResource(
        hospital_id="H2",
        resource_type="EMERGENCY_ROOM",
        total=8,
        available=6
    ),
    HospitalResource(
        hospital_id="H2",
        resource_type="ICU_BED",
        total=15,
        available=5
    ),
    HospitalResource(
        hospital_id="H2",
        resource_type="VENTILATOR",
        total=8,
        available=4
    ),
]


db.add_all(resources)
db.commit()
db.close()


print("Initial hospital resources added successfully.")