from pydantic import BaseModel, Field
from uuid import UUID


class ThresholdRequest(BaseModel):
    user_id: UUID
    type: str = Field(..., min_length=1)
    min_value: float | None = None
    max_value: float | None = None
    severity: str = Field(default="medium", min_length=1)