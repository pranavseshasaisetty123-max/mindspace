from pydantic import BaseModel
from typing import List

class SummaryAnalytics(BaseModel):
    total_reflections: int
    streak_days: int
    average_mood: float
    average_sleep: float

class TrendData(BaseModel):
    date: str
    avg_mood: float
    avg_stress: float
    avg_energy: float
    avg_sleep: float

class TagCount(BaseModel):
    tag: str
    count: int

class RecentReflectionResponse(BaseModel):
    journal_id: int
    title: str
    summary: str
    reflection_question: str

class DashboardAnalyticsResponse(BaseModel):
    summary: SummaryAnalytics
    trends: List[TrendData]
    tag_distribution: List[TagCount]
    recent_reflections: List[RecentReflectionResponse]
