import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.schemas.journal import JournalCreate, JournalUpdate, JournalResponse
from app.services import journal as journal_service

logger = logging.getLogger("mindspace.journal")
router = APIRouter(prefix="/api/v1/journals", tags=["journals"])

@router.post(
    "", 
    response_model=JournalResponse, 
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Journal entry successfully created and returned."},
        400: {"description": "Invalid metrics or empty tags parameters."},
        401: {"description": "Authentication credentials missing or invalid."},
        422: {"description": "Request validation failed (unacceptable ranges)."}
    }
)
async def create_entry(
    entry: JournalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new journal entry with metric ratings and tag listings."""
    return await journal_service.create_journal_entry(db, current_user.id, entry)

@router.get(
    "", 
    response_model=List[JournalResponse],
    responses={
        200: {"description": "List of journal entries returned matching user and filters."},
        401: {"description": "Authentication credentials missing or invalid."}
    }
)
async def get_entries(
    skip: int = Query(0, ge=0, description="Offset pagination index"),
    limit: int = Query(10, ge=1, le=100, description="Max result count limit"),
    mood: Optional[int] = Query(None, ge=1, le=5, description="Filter by mood score"),
    tag: Optional[str] = Query(None, description="Filter by tag keyword"),
    start_date: Optional[datetime] = Query(None, description="Filter entries starting from timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter entries up to timestamp"),
    search: Optional[str] = Query(None, description="Keyword text search on title/content"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all active (non-soft-deleted) journal entries for the authenticated user, supporting search and filters."""
    return await journal_service.get_journal_entries(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        mood=mood,
        tag=tag,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

@router.get(
    "/{id}", 
    response_model=JournalResponse,
    responses={
        200: {"description": "Individual active journal entry returned."},
        401: {"description": "Authentication credentials missing or invalid."},
        403: {"description": "Access forbidden: You do not own this entry."},
        404: {"description": "Journal entry not found or has been soft-deleted."}
    }
)
async def get_entry(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details of a specific journal entry by its primary key ID (confirms ownership)."""
    return await journal_service.get_journal_entry_by_id(db, current_user.id, id)

@router.put(
    "/{id}", 
    response_model=JournalResponse,
    responses={
        200: {"description": "Journal entry successfully updated and returned."},
        401: {"description": "Authentication credentials missing or invalid."},
        403: {"description": "Access forbidden: You do not own this entry."},
        404: {"description": "Journal entry not found or has been soft-deleted."},
        422: {"description": "Validation failed."}
    }
)
async def update_entry(
    id: int,
    entry: JournalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify text parameters or metrics of a specific journal entry."""
    return await journal_service.update_journal_entry(db, current_user.id, id, entry)

@router.delete(
    "/{id}", 
    response_model=JournalResponse,
    responses={
        200: {"description": "Journal entry successfully soft-deleted."},
        401: {"description": "Authentication credentials missing or invalid."},
        403: {"description": "Access forbidden: You do not own this entry."},
        404: {"description": "Journal entry not found."}
    }
)
async def delete_entry(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a journal entry by flagging its deleted_at timestamp (retains records)."""
    return await journal_service.delete_journal_entry(db, current_user.id, id)
