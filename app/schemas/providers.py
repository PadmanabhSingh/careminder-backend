from pydantic import BaseModel, Field
from uuid import UUID


class ClinicalNoteRequest(BaseModel):
    user_id: UUID
    note: str = Field(..., min_length=3)