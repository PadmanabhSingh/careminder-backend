from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any


class DeviceRegisterRequest(BaseModel):
    user_id: UUID
    device_name: str
    vendor: str
    model: str | None = None
    status: str = "active"
    battery_percent: int | None = None


class DeviceIngestRequest(BaseModel):
    user_id: UUID
    device_id: UUID | None = None
    vendor: str
    payload: dict[str, Any]