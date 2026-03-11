from pydantic import BaseModel
from uuid import UUID


class ThresholdRequest(BaseModel):
    user_id: UUID
    type: str
    min_value: float | None = None
    max_value: float | None = None
    severity: str = "medium"