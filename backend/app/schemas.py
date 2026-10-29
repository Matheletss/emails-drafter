"""
Pydantic schemas for API request / response validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Contact schemas ──────────────────────────────────────────────────────────

class ContactBase(BaseModel):
    email: str
    company: str
    contact_name: str


class ContactOut(ContactBase):
    id: int
    status: str
    scheduled_time: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    gmail_draft_id: Optional[str] = None
    attempt_count: int = 0
    error: Optional[str] = None
    row_index: Optional[int] = None
    batch_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactPreview(BaseModel):
    id: int
    email: str
    company: str
    contact_name: str
    subject: str
    body: str


# ── Upload response ──────────────────────────────────────────────────────────

class UploadStats(BaseModel):
    total_contacts: int
    valid_contacts: int
    already_processed: int
    ready_to_process: int
    invalid_contacts: int
    errors: List[str] = []
    batch_id: str


# ── Schedule schemas ─────────────────────────────────────────────────────────

class ScheduleConfigIn(BaseModel):
    start_date: str          # YYYY-MM-DD
    start_time: str          # HH:MM
    interval_minutes: int = 10
    daily_limit: int = 20
    daily_start_time: Optional[str] = None
    daily_end_time: Optional[str] = None


class ScheduleConfigOut(ScheduleConfigIn):
    id: int
    is_active: int = 0
    is_paused: int = 0

    class Config:
        from_attributes = True


# ── Scheduler status ─────────────────────────────────────────────────────────

class SchedulerStatus(BaseModel):
    is_active: bool
    is_paused: bool
    total_scheduled: int
    completed: int
    pending: int
    failed: int
    current_contact: Optional[str] = None
    next_run_time: Optional[str] = None
    mode: str = "live"  # "live" or "preview"


# ── Activity log schema ─────────────────────────────────────────────────────

class ActivityLogOut(BaseModel):
    id: int
    contact_id: Optional[int] = None
    company: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    status: str
    gmail_draft_id: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Gmail auth ───────────────────────────────────────────────────────────────

class GmailAuthStatus(BaseModel):
    authenticated: bool
    email: Optional[str] = None
    message: str = ""
