from pydantic import BaseModel, Field
from datetime import date


class GenerateSummaryRequest(BaseModel):
    summary_date: date


class GenerateReportRequest(BaseModel):
    title: str = Field(..., min_length=3)