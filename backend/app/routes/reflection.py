import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.schemas.reflection import AIReflectionResponse
from app.services import reflection as reflection_service

logger = logging.getLogger("mindspace.reflection")
router = APIRouter(prefix="/api/v1/journals", tags=["reflections"])

@router.post(
    "/{id}/generate-reflection", 
    response_model=AIReflectionResponse,
    responses={
        200: {"description": "AI reflection successfully generated (or loaded from cache if valid)."},
        401: {"description": "Authentication credentials missing or invalid."},
        403: {"description": "Access forbidden: You do not own this entry."},
        404: {"description": "Journal entry not found or has been soft-deleted."},
        502: {"description": "Gemini API gateway connection error or parsing failure."}
    }
)
async def generate_reflection(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger Google Gemini reflection generation for a specific journal entry, saving findings to database."""
    return await reflection_service.generate_or_update_reflection(db, current_user.id, id)

@router.get(
    "/{id}/reflection", 
    response_model=AIReflectionResponse,
    responses={
        200: {"description": "AI reflection retrieved successfully from database cache."},
        401: {"description": "Authentication credentials missing or invalid."},
        403: {"description": "Access forbidden: You do not own this entry."},
        404: {"description": "Stale or missing reflection cache. Client should trigger generate-reflection."}
    }
)
async def get_reflection(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the cached AI reflection from database storage, verifying user ownership. Returns 404 on cache miss."""
    reflection = await reflection_service.get_cached_reflection(db, current_user.id, id)
    if not reflection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid cached reflection exists for this journal entry."
        )
    return reflection
