from pydantic import BaseModel, Field
from typing import List 

class SpecialistSummary(BaseModel):
    id: int
    name: str
    speciality: str
    imagePath: str

class SpecialistDetail(SpecialistSummary):  
    id: int
    name: str
    speciality: str
    imagePath: str
    bio: str
    experienceYears : int
    careerPath: List[str]
    highlights: List[str]
