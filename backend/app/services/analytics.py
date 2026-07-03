import logging
from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.models.journal import JournalEntry, Tag, journal_tags
from app.models.reflection import AIReflection
from app.schemas.analytics import (
    DashboardAnalyticsResponse, 
    TrendData, 
    TagCount, 
    SummaryAnalytics,
    RecentReflectionResponse
)

logger = logging.getLogger("mindspace.analytics")

async def get_parsed_dates(db: AsyncSession, user_id: int) -> List[date]:
    """Retrieve and parse unique journal entry dates (sorted descending)."""
    query = (
        select(func.date(JournalEntry.created_at).label("entry_date"))
        .filter(JournalEntry.user_id == user_id, JournalEntry.deleted_at == None)
        .group_by(func.date(JournalEntry.created_at))
        .order_by(func.date(JournalEntry.created_at).desc())
    )
    result = await db.execute(query)
    raw_dates = [row.entry_date for row in result.all()]
    
    parsed_dates = []
    for d in raw_dates:
        if isinstance(d, str):
            try:
                parsed_dates.append(datetime.strptime(d, "%Y-%m-%d").date())
            except ValueError:
                parsed_dates.append(datetime.strptime(d.split()[0], "%Y-%m-%d").date())
        elif isinstance(d, date):
            parsed_dates.append(d)
        elif isinstance(d, datetime):
            parsed_dates.append(d.date())

    return sorted(list(set(parsed_dates)), reverse=True)

async def get_writing_streak(db: AsyncSession, user_id: int) -> int:
    """Calculate the current consecutive days streak for a user."""
    parsed_dates = await get_parsed_dates(db, user_id)
    if not parsed_dates:
        return 0

    today = date.today()
    yesterday = today - timedelta(days=1)

    # If the latest entry is older than yesterday, the streak is currently broken
    if parsed_dates[0] < yesterday:
        return 0

    streak = 1
    for i in range(len(parsed_dates) - 1):
        diff = parsed_dates[i] - parsed_dates[i+1]
        if diff.days == 1:
            streak += 1
        elif diff.days > 1:
            break
            
    return streak

async def get_longest_writing_streak(db: AsyncSession, user_id: int) -> int:
    """Calculate the longest consecutive days writing streak historically."""
    parsed_dates = await get_parsed_dates(db, user_id)
    if not parsed_dates:
        return 0

    # Sort ascending for forward chronological traversal
    dates = sorted(parsed_dates)
    
    max_streak = 1
    current_streak = 1
    
    for i in range(len(dates) - 1):
        diff = dates[i+1] - dates[i]
        if diff.days == 1:
            current_streak += 1
        elif diff.days > 1:
            max_streak = max(max_streak, current_streak)
            current_streak = 1
            
    return max(max_streak, current_streak)

async def get_tag_distribution(db: AsyncSession, user_id: int) -> List[TagCount]:
    """Retrieve frequency distribution counts for tags mapped to user journal entries."""
    query = (
        select(Tag.name.label("tag"), func.count(journal_tags.c.entry_id).label("count"))
        .join(journal_tags, Tag.id == journal_tags.c.tag_id)
        .join(JournalEntry, JournalEntry.id == journal_tags.c.entry_id)
        .filter(JournalEntry.user_id == user_id, JournalEntry.deleted_at == None)
        .group_by(Tag.name)
        .order_by(func.count(journal_tags.c.entry_id).desc())
    )
    result = await db.execute(query)
    return [TagCount(tag=row.tag, count=row.count) for row in result.all()]

async def get_trends(db: AsyncSession, user_id: int, days_limit: int, interval: str) -> List[TrendData]:
    """Compute average metrics (mood, stress, energy, sleep) grouped by time intervals."""
    is_sqlite = db.bind.dialect.name == "sqlite"
    
    if interval == "weekly":
        date_func = func.strftime("%Y-%W", JournalEntry.created_at) if is_sqlite else func.date_format(JournalEntry.created_at, "%Y-%u")
    elif interval == "monthly":
        date_func = func.strftime("%Y-%m", JournalEntry.created_at) if is_sqlite else func.date_format(JournalEntry.created_at, "%Y-%m")
    else: # daily
        date_func = func.date(JournalEntry.created_at)

    query = (
        select(
            date_func.label("date_label"),
            func.avg(JournalEntry.mood).label("avg_mood"),
            func.avg(JournalEntry.stress_level).label("avg_stress"),
            func.avg(JournalEntry.energy_level).label("avg_energy"),
            func.avg(JournalEntry.sleep_hours).label("avg_sleep")
        )
        .filter(JournalEntry.user_id == user_id, JournalEntry.deleted_at == None)
    )

    if days_limit:
        cutoff = date.today() - timedelta(days=days_limit)
        query = query.filter(JournalEntry.created_at >= cutoff)

    query = query.group_by(date_func).order_by("date_label")
    result = await db.execute(query)
    
    trends = []
    for row in result.all():
        trends.append(TrendData(
            date=str(row.date_label),
            avg_mood=float(round(row.avg_mood or 0, 1)),
            avg_stress=float(round(row.avg_stress or 0, 1)),
            avg_energy=float(round(row.avg_energy or 0, 1)),
            avg_sleep=float(round(row.avg_sleep or 0, 1))
        ))
    return trends

async def get_dashboard_analytics(db: AsyncSession, user_id: int, days_limit: int = 30, interval: str = "daily") -> DashboardAnalyticsResponse:
    """Consolidate total counts, streaks, trends, and tags into a single response payload."""
    # 1. Total reflections (active journals count)
    count_query = select(func.count(JournalEntry.id)).filter(
        JournalEntry.user_id == user_id, 
        JournalEntry.deleted_at == None
    )
    count_res = await db.execute(count_query)
    total_reflections = count_res.scalar() or 0

    # 2. Overall Averages
    avg_query = select(
        func.avg(JournalEntry.mood).label("mood"),
        func.avg(JournalEntry.sleep_hours).label("sleep")
    ).filter(
        JournalEntry.user_id == user_id, 
        JournalEntry.deleted_at == None
    )
    avg_res = await db.execute(avg_query)
    avg_row = avg_res.first()
    
    average_mood = float(round(avg_row.mood or 0, 1)) if avg_row else 0.0
    average_sleep = float(round(avg_row.sleep or 0, 1)) if avg_row else 0.0

    # 3. Streak days
    streak_days = await get_writing_streak(db, user_id)
    longest_writing_streak = await get_longest_writing_streak(db, user_id)

    # 4. Word Counts (Total and Average) - Dialect Safe
    content_query = select(JournalEntry.content).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.deleted_at == None
    )
    content_res = await db.execute(content_query)
    contents = content_res.scalars().all()
    
    total_words_written = 0
    for text in contents:
        if text:
            total_words_written += len(text.split())
            
    average_words_per_journal = (
        float(round(total_words_written / total_reflections, 1)) 
        if total_reflections > 0 
        else 0.0
    )

    # 5. Entries this week (Monday to Sunday)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_datetime = datetime.combine(start_of_week, datetime.min.time())
    
    week_query = select(func.count(JournalEntry.id)).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.deleted_at == None,
        JournalEntry.created_at >= start_datetime
    )
    week_res = await db.execute(week_query)
    entries_this_week = week_res.scalar() or 0

    # 6. Total AI Reflections
    ai_query = (
        select(func.count(AIReflection.id))
        .join(JournalEntry, JournalEntry.id == AIReflection.journal_id)
        .filter(JournalEntry.user_id == user_id, JournalEntry.deleted_at == None)
    )
    ai_res = await db.execute(ai_query)
    total_ai_reflections = ai_res.scalar() or 0

    summary = SummaryAnalytics(
        total_reflections=total_reflections,
        streak_days=streak_days,
        average_mood=average_mood,
        average_sleep=average_sleep,
        longest_writing_streak=longest_writing_streak,
        total_words_written=total_words_written,
        average_words_per_journal=average_words_per_journal,
        entries_this_week=entries_this_week,
        total_ai_reflections=total_ai_reflections
    )

    # 7. Fetch trends & tag frequencies
    trends = await get_trends(db, user_id, days_limit, interval)
    tag_distribution = await get_tag_distribution(db, user_id)

    # 8. Fetch top 3 recent AI reflections
    reflections_query = (
        select(AIReflection)
        .join(JournalEntry, JournalEntry.id == AIReflection.journal_id)
        .filter(JournalEntry.user_id == user_id, JournalEntry.deleted_at == None)
        .order_by(AIReflection.generated_at.desc())
        .limit(3)
        .options(selectinload(AIReflection.journal))
    )
    reflections_res = await db.execute(reflections_query)
    recent_reflections = []
    for ref in reflections_res.scalars().all():
        recent_reflections.append(RecentReflectionResponse(
            journal_id=ref.journal_id,
            title=ref.journal.title if ref.journal else "Untitled Reflection",
            summary=ref.summary,
            reflection_question=ref.reflection_question
        ))

    return DashboardAnalyticsResponse(
        summary=summary,
        trends=trends,
        tag_distribution=tag_distribution,
        recent_reflections=recent_reflections
    )
