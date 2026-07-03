import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, func
from app.models.journal import JournalEntry, Tag
from app.schemas.journal import JournalCreate, JournalUpdate
from fastapi import HTTPException, status

logger = logging.getLogger("mindspace.journal")

async def _get_or_create_tag(db: AsyncSession, user_id: int, name: str) -> Tag:
    """Helper to fetch an existing user-scoped tag or create one if it is new."""
    normalized_name = name.strip().lower()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name cannot be empty"
        )
    
    result = await db.execute(
        select(Tag).filter(Tag.user_id == user_id, Tag.name == normalized_name)
    )
    tag = result.scalars().first()
    if not tag:
        tag = Tag(user_id=user_id, name=normalized_name)
        db.add(tag)
        await db.flush()  # Flush to populate the tag's ID
        logger.info(f"Created new user-scoped tag: '{normalized_name}' for user ID {user_id}")
    return tag

async def create_journal_entry(db: AsyncSession, user_id: int, entry_data: JournalCreate) -> JournalEntry:
    """Create a new journal entry, associate tags, and save to the database."""
    tag_objects = []
    unique_tag_names = list(set(entry_data.tags))
    
    for tag_name in unique_tag_names:
        tag = await _get_or_create_tag(db, user_id, tag_name)
        tag_objects.append(tag)
        
    db_entry = JournalEntry(
        user_id=user_id,
        title=entry_data.title,
        content=entry_data.content,
        mood=entry_data.mood,
        stress_level=entry_data.stress_level,
        energy_level=entry_data.energy_level,
        sleep_hours=entry_data.sleep_hours,
        tags=tag_objects
    )
    
    db.add(db_entry)
    await db.commit()
    
    # Eagerly load the tags and reflection relationships to prevent lazy-load errors during serialization
    result = await db.execute(
        select(JournalEntry)
        .filter(JournalEntry.id == db_entry.id)
        .options(selectinload(JournalEntry.tags), selectinload(JournalEntry.reflection))
    )
    refreshed_entry = result.scalars().first()
    logger.info(f"User ID {user_id} created journal entry ID {refreshed_entry.id} with {len(tag_objects)} tags.")
    return refreshed_entry

async def get_journal_entries(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 10,
    mood: Optional[int] = None,
    tag: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None
) -> List[JournalEntry]:
    """Retrieve all active journal entries for a user, applying filters and pagination."""
    query = select(JournalEntry).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.deleted_at == None
    ).options(selectinload(JournalEntry.tags), selectinload(JournalEntry.reflection))

    if mood is not None:
        query = query.filter(JournalEntry.mood == mood)

    if tag is not None:
        normalized_tag = tag.strip().lower()
        query = query.filter(JournalEntry.tags.any(Tag.name == normalized_tag))

    if start_date is not None:
        query = query.filter(JournalEntry.created_at >= start_date)
    if end_date is not None:
        query = query.filter(JournalEntry.created_at <= end_date)

    if search is not None and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JournalEntry.title.ilike(search_term),
                JournalEntry.content.ilike(search_term)
            )
        )

    query = query.order_by(JournalEntry.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_journal_entry_by_id(db: AsyncSession, user_id: int, entry_id: int) -> JournalEntry:
    """Fetch an active journal entry by ID, confirming user ownership."""
    query = select(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.deleted_at == None
    ).options(selectinload(JournalEntry.tags), selectinload(JournalEntry.reflection))
    
    result = await db.execute(query)
    entry = result.scalars().first()
    
    if not entry:
        logger.warning(f"Journal entry ID {entry_id} not found or has been soft-deleted.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
        
    if entry.user_id != user_id:
        logger.warning(f"Ownership validation failed: User ID {user_id} unauthorized to access entry ID {entry_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this entry"
        )
    return entry

async def update_journal_entry(
    db: AsyncSession, 
    user_id: int, 
    entry_id: int, 
    update_data: JournalUpdate
) -> JournalEntry:
    """Update active journal entry fields and rebuild tag associations if provided."""
    db_entry = await get_journal_entry_by_id(db, user_id, entry_id)
    
    if update_data.title is not None:
        db_entry.title = update_data.title
    if update_data.content is not None:
        db_entry.content = update_data.content
    if update_data.mood is not None:
        db_entry.mood = update_data.mood
    if update_data.stress_level is not None:
        db_entry.stress_level = update_data.stress_level
    if update_data.energy_level is not None:
        db_entry.energy_level = update_data.energy_level
    if update_data.sleep_hours is not None:
        db_entry.sleep_hours = update_data.sleep_hours
        
    if update_data.tags is not None:
        tag_objects = []
        unique_tag_names = list(set(update_data.tags))
        for tag_name in unique_tag_names:
            tag = await _get_or_create_tag(db, user_id, tag_name)
            tag_objects.append(tag)
        db_entry.tags = tag_objects
        
    db_entry.updated_at = datetime.now()

    await db.commit()
    
    # Eagerly load relationship fields before returning to caller context
    result = await db.execute(
        select(JournalEntry)
        .filter(JournalEntry.id == db_entry.id)
        .options(selectinload(JournalEntry.tags))
    )
    refreshed_entry = result.scalars().first()
    logger.info(f"User ID {user_id} updated journal entry ID {refreshed_entry.id}.")
    return refreshed_entry

async def delete_journal_entry(db: AsyncSession, user_id: int, entry_id: int) -> JournalEntry:
    """Soft delete a journal entry by setting its deleted_at timestamp."""
    db_entry = await get_journal_entry_by_id(db, user_id, entry_id)
    db_entry.deleted_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Eagerly load relationship fields before returning to caller context
    result = await db.execute(
        select(JournalEntry)
        .filter(JournalEntry.id == db_entry.id)
        .options(selectinload(JournalEntry.tags))
    )
    refreshed_entry = result.scalars().first()
    logger.info(f"User ID {user_id} soft-deleted journal entry ID {refreshed_entry.id}.")
    return refreshed_entry
