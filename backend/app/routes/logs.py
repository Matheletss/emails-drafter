"""
Activity logs API routes.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityLog
from ..schemas import ActivityLogOut

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/", response_model=List[ActivityLogOut])
def list_logs(limit: int = 100, db: Session = Depends(get_db)):
    """Get the most recent activity logs."""
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return logs
