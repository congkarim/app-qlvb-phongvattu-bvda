from pydantic import BaseModel


class HealthComponentRead(BaseModel):
    status: str
    error: str | None = None


class HealthLivenessRead(BaseModel):
    status: str


class HealthReadinessRead(BaseModel):
    status: str
    components: dict[str, HealthComponentRead]
