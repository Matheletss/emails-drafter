"""
Schedule routes — configure, start, pause, resume, stop.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ScheduleConfig
from ..schemas import ScheduleConfigIn, ScheduleConfigOut, SchedulerStatus
from .. import scheduler as sched_engine

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/config", response_model=ScheduleConfigOut)
def save_config(config: ScheduleConfigIn, db: Session = Depends(get_db)):
    """Save or update the scheduling configuration."""
    # Upsert — keep only one active config
    existing = db.query(ScheduleConfig).first()
    if existing:
        existing.start_date = config.start_date
        existing.start_time = config.start_time
        existing.interval_minutes = config.interval_minutes
        existing.daily_limit = config.daily_limit
        existing.daily_start_time = config.daily_start_time
        existing.daily_end_time = config.daily_end_time
        db.commit()
        db.refresh(existing)
        return existing
    else:
        sc = ScheduleConfig(
            start_date=config.start_date,
            start_time=config.start_time,
            interval_minutes=config.interval_minutes,
            daily_limit=config.daily_limit,
            daily_start_time=config.daily_start_time,
            daily_end_time=config.daily_end_time,
        )
        db.add(sc)
        db.commit()
        db.refresh(sc)
        return sc


@router.get("/config", response_model=ScheduleConfigOut)
def get_config(db: Session = Depends(get_db)):
    """Get the current scheduling configuration."""
    config = db.query(ScheduleConfig).first()
    if not config:
        raise HTTPException(404, "No schedule configuration found")
    return config


@router.post("/start")
def start_scheduler(batch_id: str, mode: str = "live", db: Session = Depends(get_db)):
    """Start scheduling contacts from the given batch."""
    config = db.query(ScheduleConfig).first()
    if not config:
        raise HTTPException(400, "No schedule configuration. Please configure first.")

    count = sched_engine.schedule_contacts(batch_id, config, mode=mode)
    return {"message": f"Scheduled {count} contacts in {mode} mode", "scheduled": count}


@router.post("/pause")
def pause_scheduler():
    """Pause the scheduler."""
    sched_engine.pause()
    return {"message": "Scheduler paused"}


@router.post("/resume")
def resume_scheduler():
    """Resume the scheduler."""
    sched_engine.resume()
    return {"message": "Scheduler resumed"}


@router.post("/stop")
def stop_scheduler():
    """Stop the scheduler and remove all pending jobs."""
    sched_engine.stop()
    return {"message": "Scheduler stopped"}


@router.get("/status", response_model=SchedulerStatus)
def scheduler_status():
    """Get current scheduler status."""
    status = sched_engine.get_status()
    return SchedulerStatus(**status)
