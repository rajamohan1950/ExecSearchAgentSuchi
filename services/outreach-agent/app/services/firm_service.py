"""Service for firm/contact CRUD and bulk CSV/XLSX import."""

import io
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.firm import OutreachFirm
from app.models.contact import OutreachContact
from app.services.task_scheduler import schedule_initial_tasks_for_contacts

logger = logging.getLogger(__name__)

# Expected CSV/XLSX columns (case-insensitive matching)
REQUIRED_COLUMNS = {"firm_name", "contact_name", "contact_email"}
OPTIONAL_COLUMNS = {
    "firm_website", "industry_focus", "firm_location", "firm_notes",
    "contact_title", "contact_phone", "is_primary",
}


async def bulk_upload(db: AsyncSession, file_bytes: bytes, filename: str) -> dict:
    """Parse CSV or XLSX and insert firms + contacts. Returns summary stats."""
    errors: list[str] = []
    firms_created = 0
    contacts_created = 0
    new_contact_ids: list = []

    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            return {"firms_created": 0, "contacts_created": 0, "errors": ["Unsupported file type. Use .csv or .xlsx"]}
    except Exception as e:
        logger.error(f"Failed to parse upload file: {e}")
        return {"firms_created": 0, "contacts_created": 0, "errors": [f"Failed to parse file: {str(e)}"]}

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return {
            "firms_created": 0,
            "contacts_created": 0,
            "errors": [f"Missing required columns: {', '.join(missing)}. Required: firm_name, contact_name, contact_email"],
        }

    # Group by firm_name to de-duplicate firms
    firm_cache: dict[str, OutreachFirm] = {}

    for idx, row in df.iterrows():
        try:
            firm_name = str(row.get("firm_name", "")).strip()
            contact_name = str(row.get("contact_name", "")).strip()
            contact_email = str(row.get("contact_email", "")).strip()

            if not firm_name or not contact_name or not contact_email:
                errors.append(f"Row {idx + 2}: Missing required field(s)")
                continue

            # Get or create firm
            if firm_name not in firm_cache:
                # Check if firm already exists in DB
                result = await db.execute(
                    select(OutreachFirm).where(OutreachFirm.name == firm_name)
                )
                existing_firm = result.scalar_one_or_none()

                if existing_firm:
                    firm_cache[firm_name] = existing_firm
                else:
                    firm = OutreachFirm(
                        name=firm_name,
                        website=_safe_str(row.get("firm_website")),
                        industry_focus=_safe_str(row.get("industry_focus")),
                        location=_safe_str(row.get("firm_location")),
                        notes=_safe_str(row.get("firm_notes")),
                    )
                    db.add(firm)
                    await db.flush()
                    firm_cache[firm_name] = firm
                    firms_created += 1

            firm = firm_cache[firm_name]

            # Check if contact already exists for this firm
            result = await db.execute(
                select(OutreachContact).where(
                    OutreachContact.firm_id == firm.id,
                    OutreachContact.email == contact_email,
                )
            )
            if result.scalar_one_or_none():
                errors.append(f"Row {idx + 2}: Contact {contact_email} already exists for {firm_name}")
                continue

            contact = OutreachContact(
                firm_id=firm.id,
                name=contact_name,
                email=contact_email,
                title=_safe_str(row.get("contact_title")),
                phone=_safe_str(row.get("contact_phone")),
                is_primary=bool(row.get("is_primary", False)),
            )
            db.add(contact)
            await db.flush()  # Ensure contact.id is populated
            new_contact_ids.append(contact.id)
            contacts_created += 1

        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")

    await db.commit()
    logger.info(f"Bulk upload: {firms_created} firms, {contacts_created} contacts, {len(errors)} errors")

    # Auto-schedule initial outreach tasks for all new contacts
    tasks_scheduled = 0
    if new_contact_ids:
        try:
            tasks_scheduled = await schedule_initial_tasks_for_contacts(db, new_contact_ids)
            await db.commit()
            logger.info(f"Bulk upload: auto-scheduled {tasks_scheduled} initial outreach tasks")
        except Exception as e:
            logger.error(f"Failed to schedule initial tasks (safety-net will catch): {e}")
            try:
                await db.rollback()
            except Exception:
                pass

    return {
        "firms_created": firms_created,
        "contacts_created": contacts_created,
        "tasks_scheduled": tasks_scheduled,
        "errors": errors,
    }


async def get_firms(
    db: AsyncSession,
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List firms with optional search and status filter."""
    query = select(OutreachFirm).options(selectinload(OutreachFirm.contacts))

    if search:
        query = query.where(OutreachFirm.name.ilike(f"%{search}%"))
    if status:
        query = query.where(OutreachFirm.status == status)

    query = query.order_by(OutreachFirm.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    firms = result.scalars().unique().all()

    return [
        {
            **_firm_to_dict(f),
            "contact_count": len(f.contacts),
        }
        for f in firms
    ]


async def get_firm_by_id(db: AsyncSession, firm_id) -> Optional[OutreachFirm]:
    """Get a single firm with contacts."""
    result = await db.execute(
        select(OutreachFirm)
        .options(selectinload(OutreachFirm.contacts))
        .where(OutreachFirm.id == firm_id)
    )
    return result.scalar_one_or_none()


async def update_firm(db: AsyncSession, firm_id, updates: dict) -> Optional[OutreachFirm]:
    """Update firm fields."""
    result = await db.execute(select(OutreachFirm).where(OutreachFirm.id == firm_id))
    firm = result.scalar_one_or_none()
    if not firm:
        return None
    for key, value in updates.items():
        if value is not None and hasattr(firm, key):
            setattr(firm, key, value)
    await db.commit()
    await db.refresh(firm)
    return firm


async def delete_firm(db: AsyncSession, firm_id) -> bool:
    """Delete a firm and all its contacts/threads."""
    result = await db.execute(select(OutreachFirm).where(OutreachFirm.id == firm_id))
    firm = result.scalar_one_or_none()
    if not firm:
        return False
    await db.delete(firm)
    await db.commit()
    return True


def _safe_str(val) -> Optional[str]:
    """Convert pandas value to string, handling NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val).strip() or None


def _firm_to_dict(firm: OutreachFirm) -> dict:
    return {
        "id": firm.id,
        "name": firm.name,
        "website": firm.website,
        "industry_focus": firm.industry_focus,
        "location": firm.location,
        "notes": firm.notes,
        "status": firm.status,
        "created_at": firm.created_at,
        "updated_at": firm.updated_at,
    }
