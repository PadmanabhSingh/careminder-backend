from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class BiomarkerIngestRequest(BaseModel):
    user_id: UUID
    type: str
    value: float
    unit: str
    recorded_at: datetime


class BiomarkerResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_id: UUID | None = None
    type: str
    value: float
    unit: str | None = None
    recorded_at: datetime
    created_at: datetime