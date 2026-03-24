from pydantic import BaseModel, Field
from uuid import UUID
from typing import Literal


class CreateAppointmentRequest(BaseModel):
    specialist_id: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1)   # YYYY-MM-DD
    time: str = Field(..., min_length=1)   # HH:MM
    location: str = Field(..., min_length=1)


class UpdateAppointmentRequest(BaseModel):
    status: Literal["confirmed", "cancelled", "completed"] | None = None
    date: str | None = None
    time: str | None = None
    location: str | None = None