import logging
import json
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.reflection import AIReflection
from app.services.journal import get_journal_entry_by_id
from app.services.gemini import (
    generate_reflection_with_retry,
    generate_local_fallback,
    check_crisis_language, 
    CRISIS_RESPONSE
)

logger = logging.getLogger("mindspace.reflection")

async def get_cached_reflection(db: AsyncSession, user_id: int, journal_id: int) -> Optional[AIReflection]:
    """Retrieve the cached AI reflection for a journal entry if it is up-to-date, otherwise return None."""
    # This checks ownership of the journal entry
    journal = await get_journal_entry_by_id(db, user_id, journal_id)
    
    # 1. Crisis Safety pre-scan: if crisis language is present in the journal text,
    # bypass cache lookup completely so that we generate/display the crisis banner.
    if check_crisis_language(journal.content):
        logger.warning(f"Crisis safety triggers matched on GET for journal ID {journal_id}. Bypassing cache.")
        return None

    result = await db.execute(
        select(AIReflection).filter(AIReflection.journal_id == journal_id)
    )
    reflection = result.scalars().first()
    
    if reflection:
        # Cache Validation: Check if the reflection was generated after the journal was last updated
        journal_updated_naive = journal.updated_at.replace(tzinfo=None)
        reflection_generated_naive = reflection.generated_at.replace(tzinfo=None)
        
        if reflection_generated_naive >= journal_updated_naive:
            logger.info(f"Cache hit: Reusing up-to-date AI reflection for journal ID {journal_id}")
            reflection.is_outdated = False
            return reflection
        else:
            logger.info(f"Cache stale: Journal ID {journal_id} was updated since the last reflection.")
            
    return None

async def generate_or_update_reflection(db: AsyncSession, user_id: int, journal_id: int) -> AIReflection:
    """Generate a new AI reflection (using Gemini with retries) or load fallback configurations on failure."""
    journal = await get_journal_entry_by_id(db, user_id, journal_id)
    
    # 1. Crisis safety check BEFORE cache check and BEFORE Gemini API call
    if check_crisis_language(journal.content):
        logger.warning(f"Crisis safety triggers matched on POST for journal ID {journal_id}. Overwriting cache and skipping Gemini.")
        serialized_patterns = json.dumps(CRISIS_RESPONSE["detected_patterns"])
        
        result = await db.execute(
            select(AIReflection).filter(AIReflection.journal_id == journal_id)
        )
        db_reflection = result.scalars().first()
        
        if db_reflection:
            db_reflection.summary = CRISIS_RESPONSE["summary"]
            db_reflection.detected_patterns = serialized_patterns
            db_reflection.reflection_question = CRISIS_RESPONSE["reflection_question"]
            db_reflection.generated_at = datetime.now()
            db_reflection.model_used = CRISIS_RESPONSE["model_used"]
        else:
            db_reflection = AIReflection(
                journal_id=journal_id,
                summary=CRISIS_RESPONSE["summary"],
                detected_patterns=serialized_patterns,
                reflection_question=CRISIS_RESPONSE["reflection_question"],
                model_used=CRISIS_RESPONSE["model_used"]
            )
            db.add(db_reflection)
            
        await db.commit()
        await db.refresh(db_reflection)
        db_reflection.is_outdated = False
        return db_reflection

    # 2. If not crisis, check cache
    cached = await get_cached_reflection(db, user_id, journal_id)
    if cached:
        return cached

    # 3. Trigger Gemini generator with backoff retries and fallback options
    ai_response = None
    fallback_mode = False
    stale_cache_recovered = False
    
    start_time = time.perf_counter()
    try:
        ai_response = await generate_reflection_with_retry(journal.content)
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Gemini API request failed after all retries. Duration: {duration:.3f}s. Entering fallback mode. Error: {e}")
        
        # Check if any cached reflection exists for this journal (even if stale)
        result = await db.execute(
            select(AIReflection).filter(AIReflection.journal_id == journal_id)
        )
        stale_reflection = result.scalars().first()
        
        if stale_reflection:
            logger.warning(f"Resilience Fallback: Returning stale cached reflection for journal ID {journal_id}")
            stale_reflection.is_outdated = True
            return stale_reflection
            
        # No cached reflection exists, generate a deterministic python fallback reflection
        logger.warning(f"Resilience Fallback: Generating local fallback reflection for journal ID {journal_id}")
        ai_response = generate_local_fallback(journal.content)
        fallback_mode = True

    # Serialize patterns list as JSON string for DB storage
    serialized_patterns = json.dumps(ai_response["detected_patterns"])
    
    # Check if a stale reflection exists to update
    result = await db.execute(
        select(AIReflection).filter(AIReflection.journal_id == journal_id)
    )
    db_reflection = result.scalars().first()
    
    if db_reflection:
        # Update existing record
        db_reflection.summary = ai_response["summary"]
        db_reflection.detected_patterns = serialized_patterns
        db_reflection.reflection_question = ai_response["reflection_question"]
        db_reflection.generated_at = datetime.now()
        db_reflection.model_used = ai_response["model_used"]
        logger.info(f"Updated cached reflection for journal ID {journal_id} (fallback={fallback_mode})")
    else:
        # Create new record
        db_reflection = AIReflection(
            journal_id=journal_id,
            summary=ai_response["summary"],
            detected_patterns=serialized_patterns,
            reflection_question=ai_response["reflection_question"],
            model_used=ai_response["model_used"]
        )
        db.add(db_reflection)
        logger.info(f"Created new AI reflection record for journal ID {journal_id} (fallback={fallback_mode})")
        
    await db.commit()
    await db.refresh(db_reflection)
    
    # Freshly generated entries (or fallbacks) are not considered outdated
    db_reflection.is_outdated = False
    return db_reflection
