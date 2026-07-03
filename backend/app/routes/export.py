from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.journal import JournalEntry
from app.services.journal import get_journal_entry_by_id
from app.services import export as export_service

router = APIRouter(prefix="/api/v1/export", tags=["export"])

@router.get(
    "/journals/all",
    responses={
        200: {"description": "Download stream initiated successfully."},
        401: {"description": "Authentication credentials required."},
        404: {"description": "No entries found to download."}
    }
)
async def export_all_journals(
    format: str = Query("md", description="Export format: 'md' or 'pdf'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the user's complete journal history as a streaming file attachment."""
    fmt = format.lower().strip()
    if fmt not in ["md", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format parameters. Supported formats: 'md', 'pdf'")

    # Query all active journal entries ordered chronologically, eager loading tags
    query = (
        select(JournalEntry)
        .filter(JournalEntry.user_id == current_user.id, JournalEntry.deleted_at == None)
        .order_by(JournalEntry.created_at.asc())
        .options(selectinload(JournalEntry.tags))
    )
    res = await db.execute(query)
    entries = res.scalars().all()

    if not entries:
        raise HTTPException(status_code=404, detail="No active journal logs found to compile for export.")

    if fmt == "md":
        stream = export_service.generate_markdown_stream(entries)
        filename = f"mindspace_history_{datetime.now().strftime('%Y%m%d')}.md"
        media_type = "text/markdown"
    else:
        stream = export_service.generate_pdf_stream(entries)
        filename = f"mindspace_history_{datetime.now().strftime('%Y%m%d')}.pdf"
        media_type = "application/pdf"

    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get(
    "/journals/{id}",
    responses={
        200: {"description": "Download stream initiated successfully."},
        401: {"description": "Authentication credentials required."},
        403: {"description": "Request denied: ownership validation failed."},
        404: {"description": "Journal entry not found."}
    }
)
async def export_single_journal(
    id: int,
    format: str = Query("md", description="Export format: 'md' or 'pdf'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a single target journal entry as a streaming file attachment."""
    fmt = format.lower().strip()
    if fmt not in ["md", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format parameters. Supported formats: 'md', 'pdf'")

    # Retrieve entry and verify ownership
    await get_journal_entry_by_id(db, current_user.id, id)

    # Re-query entry eager loading the tags relationship
    query = (
        select(JournalEntry)
        .filter(JournalEntry.id == id)
        .options(selectinload(JournalEntry.tags))
    )
    res = await db.execute(query)
    entry = res.scalars().first()

    if fmt == "md":
        stream = export_service.generate_markdown_stream([entry])
        filename = f"journal_draft_{id}_{datetime.now().strftime('%Y%m%d')}.md"
        media_type = "text/markdown"
    else:
        stream = export_service.generate_pdf_stream([entry])
        filename = f"journal_draft_{id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        media_type = "application/pdf"

    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
