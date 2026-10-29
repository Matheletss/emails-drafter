"""
SQLAlchemy models for contacts, schedule config, and activity logs.
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SAEnum
from .database import Base
import enum


# ── Status enum ──────────────────────────────────────────────────────────────

class ContactStatus(str, enum.Enum):
    NOT_SENT = "NOT_SENT"
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    DRAFT_CREATED = "DRAFT_CREATED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    SENT = "SENT"  # informational — set only by the user


# ── Contact model ────────────────────────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    status = Column(String, default=ContactStatus.NOT_SENT.value, nullable=False)
    scheduled_time = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    gmail_draft_id = Column(String, nullable=True)
    attempt_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    row_index = Column(Integer, nullable=True)  # original spreadsheet row
    batch_id = Column(String, nullable=True, index=True)  # groups an upload batch
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Schedule config ──────────────────────────────────────────────────────────

class ScheduleConfig(Base):
    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(String, nullable=False)          # ISO date
    start_time = Column(String, nullable=False)          # HH:MM
    interval_minutes = Column(Integer, default=10)
    daily_limit = Column(Integer, default=20)
    daily_start_time = Column(String, nullable=True)     # HH:MM
    daily_end_time = Column(String, nullable=True)       # HH:MM
    is_active = Column(Integer, default=0)               # 0/1
    is_paused = Column(Integer, default=0)               # 0/1
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Activity log ─────────────────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, nullable=True)
    company = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    gmail_draft_id = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
