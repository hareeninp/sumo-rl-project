from database import SessionLocal
from models import HospitalResource


db = SessionLocal()

resources = db.query(HospitalResource).all()

for resource in resources:
    print(
        resource.hospital_id,
        resource.resource_type,
        resource.total,
        resource.available
    )

db.close()