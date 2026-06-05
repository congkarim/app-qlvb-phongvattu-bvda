from datetime import datetime

from pydantic import BaseModel, Field


class AuditActorRead(BaseModel):
    id: str
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: str
    actor_user_id: str | None = None
    actor: AuditActorRead | None = None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True}
