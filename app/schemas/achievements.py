from pydantic import BaseModel

class ShareAchievementRequest(BaseModel):
    platform:str | None = None