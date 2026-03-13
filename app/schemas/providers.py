from pydantic import BaseModel
from uuid import UUID


class ClinicalNoteRequest(BaseModel):
    user_id: UUID
    note: str