"""
Scheduler — APScheduler-based engine for timed draft creation.

Supports start / pause / resume / stop.
Persistent job state via SQLite contact records.
"""

import logging
import time
import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Contact, ContactStatus, ScheduleConfig, ActivityLog
from .template_engine import generate_subject, generate_body
from . import gmail_service

logger = logging.getLogger(__name__)

# ── Module-level scheduler ───────────────────────────────────────────────────

_scheduler: Optional[BackgroundScheduler] = None
_is_paused = False
_is_active = False
_mode = "live"  # "live" | "preview"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 5  # seconds


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            job_defaults={
                'misfire_grace_time': 3600,  # allow jobs to run up to 1 hour late
                'coalesce': False,           # don't merge missed runs
                'max_instances': 1,
            }
        )
        _scheduler.start()
    return _scheduler


# ── Core draft-processing job ────────────────────────────────────────────────

def _process_contact(contact_id: int):
    """Process a single contact — create a Gmail draft."""
    global _is_paused

    if _is_paused:
        logger.info(f"Scheduler paused — skipping contact {contact_id}")
        return

    db: Session = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            logger.warning(f"Contact {contact_id} not found")
            return

        # Re-check state (idempotency)
        if contact.status in (
            ContactStatus.DRAFT_CREATED.value,
            ContactStatus.SENT.value,
            ContactStatus.SKIPPED.value,
        ):
            logger.info(f"Contact {contact_id} already processed ({contact.status}) — skipping")
            return

        contact.status = ContactStatus.PROCESSING.value
        contact.attempt_count += 1
        db.commit()

        subject = generate_subject(contact.company)
        body = generate_body(contact.contact_name, contact.company)

        if _mode == "preview":
            # Preview mode — don't call Gmail
            contact.status = ContactStatus.DRAFT_CREATED.value
            contact.processed_at = datetime.datetime.utcnow()
            contact.gmail_draft_id = "PREVIEW-MODE"
            db.commit()
            _log_activity(db, contact, "Draft Created (Preview)")
            logger.info(f"[PREVIEW] Draft for {contact.email}")
            return

        # Live mode — create Gmail draft
        success, draft_id, error = gmail_service.create_draft(
            to_email=contact.email,
            subject=subject,
            body=body,
        )

        if success:
            contact.status = ContactStatus.DRAFT_CREATED.value
            contact.processed_at = datetime.datetime.utcnow()
            contact.gmail_draft_id = draft_id
            contact.error = None
            db.commit()
            _log_activity(db, contact, "Draft Created")
            logger.info(f"Draft created for {contact.email} — ID: {draft_id}")
        else:
            # Retry with exponential backoff
            if contact.attempt_count < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (contact.attempt_count - 1))
                contact.status = ContactStatus.SCHEDULED.value
                contact.error = f"Attempt {contact.attempt_count} failed: {error}"
                db.commit()

                scheduler = get_scheduler()
                run_time = datetime.datetime.now() + datetime.timedelta(seconds=delay)
                scheduler.add_job(
                    _process_contact,
                    trigger=DateTrigger(run_date=run_time),
                    args=[contact_id],
                    id=f"retry-{contact_id}-{contact.attempt_count}",
                    replace_existing=True,
                )
                logger.warning(f"Retrying contact {contact_id} in {delay}s (attempt {contact.attempt_count})")
            else:
                contact.status = ContactStatus.FAILED.value
                contact.error = f"Failed after {_MAX_RETRIES} attempts: {error}"
                db.commit()
                _log_activity(db, contact, "Failed", error=contact.error)
                logger.error(f"Contact {contact_id} failed permanently: {error}")

    except Exception as e:
        logger.exception(f"Unexpected error processing contact {contact_id}")
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if contact:
                contact.status = ContactStatus.FAILED.value
                contact.error = str(e)
                db.commit()
                _log_activity(db, contact, "Failed", error=str(e))
        except Exception:
            pass
    finally:
        db.close()


def _log_activity(db: Session, contact: Contact, status: str, error: Optional[str] = None):
    """Write an activity log entry."""
    db.add(ActivityLog(
        contact_id=contact.id,
        company=contact.company,
        contact_name=contact.contact_name,
        email=contact.email,
        scheduled_time=contact.scheduled_time,
        status=status,
        gmail_draft_id=contact.gmail_draft_id,
        error=error,
        message=f"{status} for {contact.contact_name} at {contact.company}",
    ))
    db.commit()


# ── Schedule contacts ────────────────────────────────────────────────────────

def schedule_contacts(batch_id: str, config: ScheduleConfig, mode: str = "live"):
    """
    Schedule all NOT_SENT contacts from a batch according to the config.
    """
    global _is_active, _is_paused, _mode

    _mode = mode
    _is_active = True
    _is_paused = False

    db: Session = SessionLocal()
    try:
        contacts = (
            db.query(Contact)
            .filter(
                Contact.batch_id == batch_id,
                Contact.status == ContactStatus.NOT_SENT.value,
            )
            .order_by(Contact.row_index)
            .all()
        )

        if not contacts:
            logger.info("No contacts to schedule")
            return 0

        scheduler = get_scheduler()

        # Parse start date/time
        start_dt = datetime.datetime.strptime(
            f"{config.start_date} {config.start_time}",
            "%Y-%m-%d %H:%M",
        )
        # ── If the configured start time is already in the past, snap to now+5s
        #    so APScheduler doesn't silently drop all jobs.
        now = datetime.datetime.now()
        if start_dt < now:
            logger.warning(
                f"Configured start time {start_dt} is in the past — "
                f"snapping to now+5s ({now})"
            )
            start_dt = now + datetime.timedelta(seconds=5)

        # Enforce a minimum 5-second gap between jobs so APScheduler is stable
        interval_seconds = max(config.interval_minutes * 60, 5)
        interval = datetime.timedelta(seconds=interval_seconds)

        daily_start = None
        daily_end = None
        if config.daily_start_time:
            h, m = map(int, config.daily_start_time.split(":"))
            daily_start = datetime.time(h, m)
        if config.daily_end_time:
            h, m = map(int, config.daily_end_time.split(":"))
            daily_end = datetime.time(h, m)

        current_time = start_dt
        daily_count = 0
        current_day = current_time.date()
        scheduled = 0

        for contact in contacts:
            # Daily limit check
            if current_time.date() != current_day:
                current_day = current_time.date()
                daily_count = 0

            if daily_count >= config.daily_limit:
                # Move to next day
                next_day = current_day + datetime.timedelta(days=1)
                if daily_start:
                    current_time = datetime.datetime.combine(next_day, daily_start)
                else:
                    current_time = datetime.datetime.combine(
                        next_day, start_dt.time()
                    )
                current_day = next_day
                daily_count = 0

            # Daily window check
            if daily_end and current_time.time() >= daily_end:
                next_day = current_day + datetime.timedelta(days=1)
                if daily_start:
                    current_time = datetime.datetime.combine(next_day, daily_start)
                else:
                    current_time = datetime.datetime.combine(
                        next_day, start_dt.time()
                    )
                current_day = next_day
                daily_count = 0

            # Schedule the job
            contact.status = ContactStatus.SCHEDULED.value
            contact.scheduled_time = current_time

            scheduler.add_job(
                _process_contact,
                trigger=DateTrigger(run_date=current_time),
                args=[contact.id],
                id=f"contact-{contact.id}",
                replace_existing=True,
            )

            daily_count += 1
            scheduled += 1
            current_time += interval

        db.commit()

        # Log the scheduling event
        db.add(ActivityLog(
            status="Batch Scheduled",
            message=f"Scheduled {scheduled} contacts from batch {batch_id} in {mode} mode",
        ))
        db.commit()

        logger.info(f"Scheduled {scheduled} contacts from batch {batch_id}")
        return scheduled

    finally:
        db.close()


# ── Controls ─────────────────────────────────────────────────────────────────

def pause():
    global _is_paused
    _is_paused = True
    scheduler = get_scheduler()
    scheduler.pause()
    logger.info("Scheduler paused")


def resume():
    global _is_paused
    _is_paused = False
    scheduler = get_scheduler()
    scheduler.resume()
    logger.info("Scheduler resumed")


def stop():
    global _is_active, _is_paused
    _is_active = False
    _is_paused = False
    scheduler = get_scheduler()
    # Remove all pending jobs
    for job in scheduler.get_jobs():
        job.remove()
    logger.info("Scheduler stopped — all pending jobs removed")

    # Mark SCHEDULED contacts back to NOT_SENT
    db: Session = SessionLocal()
    try:
        db.query(Contact).filter(
            Contact.status == ContactStatus.SCHEDULED.value
        ).update({Contact.status: ContactStatus.NOT_SENT.value, Contact.scheduled_time: None})
        db.commit()
    finally:
        db.close()


def get_status() -> dict:
    """Return current scheduler status."""
    db: Session = SessionLocal()
    try:
        total = db.query(Contact).filter(Contact.status == ContactStatus.SCHEDULED.value).count()
        completed = db.query(Contact).filter(Contact.status == ContactStatus.DRAFT_CREATED.value).count()
        failed = db.query(Contact).filter(Contact.status == ContactStatus.FAILED.value).count()
        pending = db.query(Contact).filter(
            Contact.status.in_([ContactStatus.SCHEDULED.value, ContactStatus.NOT_SENT.value])
        ).count()

        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        next_run = None
        if jobs:
            next_runs = [j.next_run_time for j in jobs if j.next_run_time]
            if next_runs:
                next_run = min(next_runs).isoformat()

        return {
            "is_active": _is_active,
            "is_paused": _is_paused,
            "total_scheduled": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "next_run_time": next_run,
            "mode": _mode,
        }
    finally:
        db.close()


def resume_pending_on_startup():
    """
    On application start, check for contacts that were SCHEDULED or PROCESSING
    but never completed (crash recovery).
    """
    db: Session = SessionLocal()
    try:
        stuck = db.query(Contact).filter(
            Contact.status.in_([
                ContactStatus.SCHEDULED.value,
                ContactStatus.PROCESSING.value,
            ]),
            Contact.scheduled_time.isnot(None),
        ).all()

        if not stuck:
            return

        scheduler = get_scheduler()
        now = datetime.datetime.now()
        recovered = 0

        for contact in stuck:
            # If the scheduled time has passed, run immediately
            run_time = max(contact.scheduled_time, now + datetime.timedelta(seconds=5))
            contact.status = ContactStatus.SCHEDULED.value
            scheduler.add_job(
                _process_contact,
                trigger=DateTrigger(run_date=run_time),
                args=[contact.id],
                id=f"recover-{contact.id}",
                replace_existing=True,
            )
            recovered += 1

        db.commit()
        if recovered:
            logger.info(f"Recovered {recovered} pending contacts from previous session")
            db.add(ActivityLog(
                status="Recovery",
                message=f"Recovered {recovered} pending contacts on startup",
            ))
            db.commit()

    finally:
        db.close()
