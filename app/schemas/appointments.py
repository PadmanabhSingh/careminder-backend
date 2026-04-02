from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date as dt_date

class CreateAppointmentRequest(BaseModel):
    specialist_id: str = Field(..., min_length=1)
    date: dt_date
    time: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)


class UpdateAppointmentRequest(BaseModel):
    status: Optional[Literal["confirmed", "cancelled", "completed"]] = None
    date: Optional[dt_date] = None
    time: Optional[str] = None
    location: Optional[str] = None