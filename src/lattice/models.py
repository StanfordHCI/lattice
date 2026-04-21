from pydantic import BaseModel, Field, field_validator
from typing import List, Optional



class Interaction(BaseModel):
    interaction: str
    metadata: Optional[dict] = None

class Session(BaseModel):
    interactions: List[Interaction]
    time: Optional[str] = None

class Observation(BaseModel):
    think_feel: str
    actions: str
    confidence: int
    time: Optional[str] = None

class Insight(BaseModel):
    title: str
    tagline: str
    insight: str
    context: str
    supporting_evidence: List[str]
    merged: Optional[List[str]] = None    

    @field_validator("supporting_evidence", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

class Insights(BaseModel):
    insights: List[Insight]


class FinalInsight(BaseModel):
    title: str
    tagline: str
    insight: str
    context: str
    merged: List[str]
    reasoning: str


class FinalInsights(BaseModel):
    insights: List[FinalInsight]

class InsightSupportResponse(BaseModel):
    evidence: List[str]
    confidence: int
    reasoning: str

class SupportingObservationsResponse(BaseModel):
    supporting_ids: List[int]