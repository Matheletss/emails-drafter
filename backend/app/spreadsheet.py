"""
Spreadsheet parser — reads .xlsx / .csv and normalises column names.
"""

import os
import re
import uuid
import shutil
import pandas as pd
from typing import Tuple, List
from sqlalchemy.orm import Session
from .models import Contact, ContactStatus


# ── Column-name aliases ─────────────────────────────────────────────────────

_COLUMN_MAP = {
    "company": "company",
    "company name": "company",
    "company_name": "company",
    "startup": "company",
    "founder / contact name": "contact_name",
    "founder/contact name": "contact_name",
    "founder name": "contact_name",
    "contact name": "contact_name",
    "contact_name": "contact_name",
    "name": "contact_name",
    "founder": "contact_name",
    "email": "email",
    "email address": "email",
    "email_address": "email",
    "mail": "email",
    "email sent?": "email_sent",
    "email sent": "email_sent",
    "email_sent": "email_sent",
    "status": "email_sent",
}

_REQUIRED = {"company", "contact_name", "email"}

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw column names to canonical names."""
    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in _COLUMN_MAP:
            rename[col] = _COLUMN_MAP[key]
    return df.rename(columns=rename)


def parse_spreadsheet(
    filepath: str,
    db: Session,
    upload_dir: str,
) -> Tuple[dict, List[str]]:
    """
    Parse an uploaded spreadsheet, validate rows, and insert contacts into the DB.

    Returns (stats_dict, error_list).
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    df = _normalise_columns(df)

    # Check required columns exist
    missing_cols = _REQUIRED - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    batch_id = uuid.uuid4().hex[:12]
    errors: List[str] = []
    valid = 0
    invalid = 0
    already_processed = 0

    # Keep a backup of the original file
    backup_path = os.path.join(upload_dir, f"backup_{os.path.basename(filepath)}")
    shutil.copy2(filepath, backup_path)

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed header + data

        company = str(row.get("company", "")).strip() if pd.notna(row.get("company")) else ""
        contact_name = str(row.get("contact_name", "")).strip() if pd.notna(row.get("contact_name")) else ""
        email = str(row.get("email", "")).strip() if pd.notna(row.get("email")) else ""
        email_sent = str(row.get("email_sent", "")).strip().lower() if pd.notna(row.get("email_sent")) else ""

        if not contact_name and email and "@" in email:
            # Extract name from email prefix (e.g. sagar@... -> Sagar)
            contact_name = email.split("@")[0].capitalize()

        # ── Validation ───────────────────────────────────────────────────
        row_errors = []
        if not email:
            row_errors.append("Missing email")
        elif not _EMAIL_RE.match(email):
            row_errors.append(f"Invalid email syntax: {email}")
        if not company:
            row_errors.append("Missing company name")
        if not contact_name:
            row_errors.append("Missing contact name")

        if row_errors:
            error_msg = f"Row {row_num}: {'; '.join(row_errors)}"
            errors.append(error_msg)
            # Still insert so the user can see it in the dashboard
            db.add(Contact(
                email=email or f"invalid-row-{row_num}",
                company=company or "—",
                contact_name=contact_name or "—",
                status=ContactStatus.FAILED.value,
                error="; ".join(row_errors),
                row_index=row_num,
                batch_id=batch_id,
            ))
            invalid += 1
            continue

        # ── Duplicate / already-processed check ──────────────────────────
        existing = db.query(Contact).filter(
            Contact.email == email,
            Contact.status.in_([
                ContactStatus.DRAFT_CREATED.value,
                ContactStatus.SENT.value,
                ContactStatus.PROCESSING.value,
                ContactStatus.SCHEDULED.value,
            ]),
        ).first()

        if existing:
            already_processed += 1
            db.add(Contact(
                email=email,
                company=company,
                contact_name=contact_name,
                status=ContactStatus.SKIPPED.value,
                error="Already processed in a previous batch",
                row_index=row_num,
                batch_id=batch_id,
            ))
            continue

        # Also skip if spreadsheet already says "draft created" / "sent"
        if email_sent in ("draft created", "sent"):
            already_processed += 1
            db.add(Contact(
                email=email,
                company=company,
                contact_name=contact_name,
                status=ContactStatus.SKIPPED.value,
                error=f"Spreadsheet status: {email_sent}",
                row_index=row_num,
                batch_id=batch_id,
            ))
            continue

        # ── Valid contact ─────────────────────────────────────────────────
        db.add(Contact(
            email=email,
            company=company,
            contact_name=contact_name,
            status=ContactStatus.NOT_SENT.value,
            row_index=row_num,
            batch_id=batch_id,
        ))
        valid += 1

    db.commit()

    stats = {
        "total_contacts": len(df),
        "valid_contacts": valid,
        "already_processed": already_processed,
        "ready_to_process": valid,
        "invalid_contacts": invalid,
        "batch_id": batch_id,
    }
    return stats, errors
