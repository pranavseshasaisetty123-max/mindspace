import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.settings import UserSettings
from app.schemas.settings import UserSettingsUpdate

logger = logging.getLogger("mindspace.settings")

async def get_user_settings(db: AsyncSession, user_id: int) -> UserSettings:
    """Fetch preferences from the database, or automatically seed defaults if missing."""
    query = select(UserSettings).filter(UserSettings.user_id == user_id)
    res = await db.execute(query)
    settings = res.scalars().first()

    if not settings:
        logger.info(f"Automatically seeding default preferences for user ID {user_id}")
        settings = UserSettings(
            user_id=user_id,
            reminder_enabled=False,
            reminder_time="21:00",
            timezone="UTC",
            theme="dark"
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings

async def update_user_settings(db: AsyncSession, user_id: int, settings_data: UserSettingsUpdate) -> UserSettings:
    """Update user configuration parameters."""
    settings = await get_user_settings(db, user_id)

    update_dict = settings_data.model_dump(exclude_unset=True)
    for key, val in update_dict.items():
        setattr(settings, key, val)

    await db.commit()
    await db.refresh(settings)
    logger.info(f"Saved preferences updates for user ID {user_id}: {update_dict}")
    return settings
