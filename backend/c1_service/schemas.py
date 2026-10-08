from pydantic import BaseModel, Field, model_validator


class HospitalResourceCreate(BaseModel):
    hospital_id: str
    resource_type: str
    total: int = Field(ge=0)
    available: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_available(self):
        if self.available > self.total:
            raise ValueError("Available resources cannot exceed total resources")
        return self


class HospitalResourceUpdate(BaseModel):
    total: int = Field(ge=0)
    available: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_available(self):
        if self.available > self.total:
            raise ValueError("Available resources cannot exceed total resources")
        return self


class HospitalResourceResponse(BaseModel):
    id: int
    hospital_id: str
    resource_type: str
    total: int
    available: int

    class Config:
        from_attributes = True