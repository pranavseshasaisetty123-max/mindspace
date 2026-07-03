from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.schemas.analytics import DashboardAnalyticsResponse, SummaryAnalytics, TagCount, TrendData
from app.services import analytics as analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get(
    "/dashboard", 
    response_model=DashboardAnalyticsResponse,
    responses={
        200: {"description": "Analytics aggregated dashboard payload retrieved successfully."},
        401: {"description": "Authentication credentials missing or invalid."}
    }
)
async def get_dashboard_data(
    days_limit: int = Query(30, description="Range of days to query (e.g. 30, 90, 365, or 0 for all time)"),
    interval: str = Query("daily", description="Time binning interval (daily, weekly, monthly)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch the consolidated analytics dashboard dataset in a single network query."""
    return await analytics_service.get_dashboard_analytics(db, current_user.id, days_limit, interval)

@router.get("/summary", response_model=SummaryAnalytics)
async def get_summary_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve summary KPIs like streaks, total count, and mood averages."""
    res = await analytics_service.get_dashboard_analytics(db, current_user.id)
    return res.summary

@router.get("/tag-distribution", response_model=List[TagCount])
async def get_tags_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve frequency counts of tags mapped to active journal reflections."""
    return await analytics_service.get_tag_distribution(db, current_user.id)

@router.get("/mood-trend", response_model=List[TrendData])
async def get_mood_trend(
    days_limit: int = Query(30),
    interval: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve mood averages grouped by time intervals."""
    return await analytics_service.get_trends(db, current_user.id, days_limit, interval)

@router.get("/stress-trend", response_model=List[TrendData])
async def get_stress_trend(
    days_limit: int = Query(30),
    interval: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve stress averages grouped by time intervals."""
    return await analytics_service.get_trends(db, current_user.id, days_limit, interval)

@router.get("/energy-trend", response_model=List[TrendData])
async def get_energy_trend(
    days_limit: int = Query(30),
    interval: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve energy averages grouped by time intervals."""
    return await analytics_service.get_trends(db, current_user.id, days_limit, interval)

@router.get("/sleep-trend", response_model=List[TrendData])
async def get_sleep_trend(
    days_limit: int = Query(30),
    interval: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve sleep averages grouped by time intervals."""
    return await analytics_service.get_trends(db, current_user.id, days_limit, interval)
