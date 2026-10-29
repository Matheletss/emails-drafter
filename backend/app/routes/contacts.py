"""
Contact routes — upload, list, preview, retry.
"""

import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Contact, ContactStatus
from ..schemas import ContactOut, ContactPreview, UploadStats
from ..spreadsheet import parse_spreadsheet
from ..template_engine import generate_subject, generate_body, generate_body_plain

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@router.post("/upload", response_model=UploadStats)
async def upload_spreadsheet(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an Excel or CSV file and parse contacts."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(400, f"Unsupported file type: {ext}. Use .xlsx or .csv")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{file.filename}")

    # Save uploaded file
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        stats, errors = parse_spreadsheet(filepath, db, UPLOAD_DIR)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return UploadStats(
        total_contacts=stats["total_contacts"],
        valid_contacts=stats["valid_contacts"],
        already_processed=stats["already_processed"],
        ready_to_process=stats["ready_to_process"],
        invalid_contacts=stats["invalid_contacts"],
        errors=errors,
        batch_id=stats["batch_id"],
    )


@router.get("/", response_model=List[ContactOut])
def list_contacts(
    batch_id: str = None,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List contacts, optionally filtered by batch or status."""
    q = db.query(Contact)
    if batch_id:
        q = q.filter(Contact.batch_id == batch_id)
    if status:
        q = q.filter(Contact.status == status)
    return q.order_by(Contact.row_index).all()


@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    """List all upload batches with summary stats."""
    batches = (
        db.query(Contact.batch_id)
        .filter(Contact.batch_id.isnot(None))
        .distinct()
        .all()
    )
    result = []
    for (batch_id,) in batches:
        contacts = db.query(Contact).filter(Contact.batch_id == batch_id).all()
        total = len(contacts)
        ready = sum(1 for c in contacts if c.status == ContactStatus.NOT_SENT.value)
        scheduled = sum(1 for c in contacts if c.status == ContactStatus.SCHEDULED.value)
        completed = sum(1 for c in contacts if c.status == ContactStatus.DRAFT_CREATED.value)
        failed = sum(1 for c in contacts if c.status == ContactStatus.FAILED.value)
        skipped = sum(1 for c in contacts if c.status == ContactStatus.SKIPPED.value)
        created = contacts[0].created_at.isoformat() if contacts else None
        result.append({
            "batch_id": batch_id,
            "total": total,
            "ready": ready,
            "scheduled": scheduled,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "created_at": created,
        })
    return result


@router.get("/{contact_id}/preview", response_model=ContactPreview)
def preview_contact(contact_id: int, db: Session = Depends(get_db)):
    """Preview the generated email for a specific contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(404, "Contact not found")

    return ContactPreview(
        id=contact.id,
        email=contact.email,
        company=contact.company,
        contact_name=contact.contact_name,
        subject=generate_subject(contact.company),
        body=generate_body_plain(contact.contact_name, contact.company),
    )


@router.post("/{contact_id}/retry")
def retry_contact(contact_id: int, db: Session = Depends(get_db)):
    """Reset a failed contact for reprocessing."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(404, "Contact not found")

    contact.status = ContactStatus.NOT_SENT.value
    contact.error = None
    contact.attempt_count = 0
    contact.gmail_draft_id = None
    db.commit()
    return {"message": f"Contact {contact_id} reset for reprocessing"}


@router.get("/stats")
def contact_stats(batch_id: str = None, db: Session = Depends(get_db)):
    """Return aggregate stats for contacts."""
    q = db.query(Contact)
    if batch_id:
        q = q.filter(Contact.batch_id == batch_id)
    contacts = q.all()
    return {
        "total": len(contacts),
        "not_sent": sum(1 for c in contacts if c.status == ContactStatus.NOT_SENT.value),
        "scheduled": sum(1 for c in contacts if c.status == ContactStatus.SCHEDULED.value),
        "processing": sum(1 for c in contacts if c.status == ContactStatus.PROCESSING.value),
        "draft_created": sum(1 for c in contacts if c.status == ContactStatus.DRAFT_CREATED.value),
        "failed": sum(1 for c in contacts if c.status == ContactStatus.FAILED.value),
        "skipped": sum(1 for c in contacts if c.status == ContactStatus.SKIPPED.value),
        "sent": sum(1 for c in contacts if c.status == ContactStatus.SENT.value),
    }
