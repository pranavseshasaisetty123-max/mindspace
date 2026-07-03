from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate
from app.services import settings as settings_service

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get(
    "", 
    response_model=UserSettingsResponse,
    responses={
        200: {"description": "Preferences loaded successfully."},
        401: {"description": "Authentication required."}
    }
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve preferences configuration settings for current user."""
    return await settings_service.get_user_settings(db, current_user.id)

@router.put(
    "", 
    response_model=UserSettingsResponse,
    responses={
        200: {"description": "Preferences saved successfully."},
        401: {"description": "Authentication required."},
        422: {"description": "Validation error for HH:MM inputs."}
    }
)
async def update_settings(
    settings_data: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify preferences configuration settings for current user."""
    return await settings_service.update_user_settings(db, current_user.id, settings_data)
