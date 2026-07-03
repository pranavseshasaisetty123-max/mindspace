import time
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.config import settings

logger = logging.getLogger("mindspace.diagnostics")
router = APIRouter(tags=["diagnostics"])

START_TIME = time.time()
VERSION = "1.0.0"

@router.get(
    "/health",
    responses={
        200: {"description": "Server diagnostics retrieved successfully."},
        500: {"description": "Server diagnostics failed."}
    }
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Diagnose the server health, database connectivity, and Gemini config status."""
    db_status = "connected"
    try:
        # Ping database with SELECT 1
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health Check Database Failure: {e}")
        db_status = "disconnected"

    # Check Gemini config status
    gemini_configured = (
        settings.GEMINI_API_KEY is not None 
        and settings.GEMINI_API_KEY.strip() != ""
        and settings.GEMINI_API_KEY != "mock-key-for-local-testing"
    )

    uptime = int(time.time() - START_TIME)

    health_data = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": VERSION,
        "uptime_seconds": uptime,
        "database": db_status,
        "gemini_configured": gemini_configured
    }

    if db_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=health_data
        )
    return health_data

@router.get(
    "/ready",
    responses={
        200: {"description": "Server is ready for traffic."},
        503: {"description": "Server is not ready for traffic."}
    }
)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Assert database connection readiness to accept API traffic."""
    try:
        # Assert DB connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.critical(f"Readiness Check Failure: Database disconnected! Detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
