from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class BiomarkerIngestRequest(BaseModel):
    user_id: UUID
    type: str = Field(..., min_length=1)
    value: float
    unit: str = Field(..., min_length=1)
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