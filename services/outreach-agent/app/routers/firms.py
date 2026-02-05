"""Firm and contact management endpoints — CRUD + bulk upload."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.firm import (
    BulkUploadResponse,
    FirmCreate,
    FirmListItem,
    FirmResponse,
    FirmUpdate,
    ContactResponse,
)
from app.services import firm_service

router = APIRouter(prefix="/firms", tags=["firms"])


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_firms(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV or XLSX file of firms and contacts.

    Required columns: firm_name, contact_name, contact_email
    Optional columns: firm_website, industry_focus, firm_location, firm_notes,
                      contact_title, contact_phone, is_primary
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.lower().split(".")[-1]
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(status_code=400, detail="File must be .csv, .xlsx, or .xls")

    if file.size and file.size > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    content = await file.read()
    result = await firm_service.bulk_upload(db, content, file.filename)
    return BulkUploadResponse(**result)


@router.post("", response_model=FirmResponse, status_code=201)
async def create_firm(
    firm_data: FirmCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a single firm with optional contacts."""
    from app.models.firm import OutreachFirm
    from app.models.contact import OutreachContact

    firm = OutreachFirm(
        name=firm_data.name,
        website=firm_data.website,
        industry_focus=firm_data.industry_focus,
        location=firm_data.location,
        notes=firm_data.notes,
    )
    db.add(firm)
    await db.flush()

    for c in firm_data.contacts:
        contact = OutreachContact(
            firm_id=firm.id,
            name=c.name,
            email=c.email,
            title=c.title,
            phone=c.phone,
            is_primary=c.is_primary,
        )
        db.add(contact)

    await db.commit()
    await db.refresh(firm)

    # Re-fetch with contacts loaded
    firm_full = await firm_service.get_firm_by_id(db, firm.id)
    return firm_full


@router.get("", response_model=list[FirmListItem])
async def list_firms(
    search: Optional[str] = Query(None, description="Search firm name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all firms with optional search and filtering."""
    firms = await firm_service.get_firms(db, search=search, status=status, limit=limit, offset=offset)
    return firms


@router.get("/{firm_id}", response_model=FirmResponse)
async def get_firm(
    firm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single firm with all contacts."""
    firm = await firm_service.get_firm_by_id(db, firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    return firm


@router.patch("/{firm_id}", response_model=FirmResponse)
async def update_firm(
    firm_id: uuid.UUID,
    updates: FirmUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update firm details."""
    firm = await firm_service.update_firm(db, firm_id, updates.model_dump(exclude_unset=True))
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    # Re-fetch with contacts
    return await firm_service.get_firm_by_id(db, firm_id)


@router.delete("/{firm_id}", status_code=204)
async def delete_firm(
    firm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a firm and all associated data."""
    deleted = await firm_service.delete_firm(db, firm_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Firm not found")
