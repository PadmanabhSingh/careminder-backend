from pydantic import BaseModel, Field
from uuid import UUID
from typing import Literal
from datetime import datetime

class CreateAppointmentRequest(BaseModel):
    specialist_id: str = Field(..., min_length=1)
    date: date
    time: str = Field(...,min_length=1)
    location: str = Field(..., min_length=1)


class UpdateAppointmentRequest(BaseModel):
    status: Literal["confirmed", "cancelled", "completed"] | None = None
    date: datetime | None = None
    time: datetime | None = None
    location: str | None = None