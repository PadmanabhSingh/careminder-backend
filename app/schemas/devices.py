from pydantic import BaseModel, Field
from uuid import UUID
from typing import Any


class DeviceRegisterRequest(BaseModel):
    user_id: UUID
    device_name: str = Field(..., min_length=1)
    device_type: str = Field(..., min_length=1)
    vendor: str = Field(..., min_length=1)
    model: str | None = None
    status: str = "active"
    battery_percent: int | None = None


class DeviceIngestRequest(BaseModel):
    user_id: UUID
    device_id: UUID | None = None
    vendor: str
    payload: dict[str, Any]