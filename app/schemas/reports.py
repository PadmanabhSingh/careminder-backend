from pydantic import BaseModel
from datetime import date


class GenerateSummaryRequest(BaseModel):
    summary_date: date


class GenerateReportRequest(BaseModel):
    title: str