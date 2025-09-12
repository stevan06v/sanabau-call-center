from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Call(BaseModel):
    id: str


class Customer(BaseModel):
    number: str


class StructuredDate(BaseModel):
    name: Optional[str] = "Nicht angegeben"
    fax: Optional[str] = "Nicht angegeben"
    email: Optional[str] = "Nicht angegeben"
    notes: Optional[str] = "Nicht angegeben"
    status: Optional[str] = "Nicht angegeben"
    branche: Optional[str] = "Nicht angegeben"


class Analysis(BaseModel):
    structuredData: Optional[StructuredDate] = None
    successEvaluation: Optional[bool] = None


class VapiCallReport(BaseModel):
    stereoRecordingUrl: Optional[str] = None
    customer: Optional[Customer] = None
    startedAt: Optional[datetime] = None
    durationMinutes: float = 0.0
    call: Optional[Call] = None
    endedReason: Optional[str] = None
    analysis: Optional[Analysis] = None
    summary: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
