from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database import Base


class HospitalResource(Base):
    __tablename__ = "hospital_resources"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)
    total = Column(Integer, nullable=False)
    available = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)