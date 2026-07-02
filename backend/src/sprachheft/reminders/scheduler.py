"""Daily reminder job (APScheduler).

Computes how many items are due at the configured time. In-app dashboard +
browser notifications are the primary delivery (frontend polls /review/stats);
this job is the hook for optional OS/email delivery later.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func
from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.models import SRState, utcnow

logger = logging.getLogger("sprachheft.reminders")

_scheduler: BackgroundScheduler | None = None


def _due_count() -> int:
    from sprachheft.db import engine

    with Session(engine) as session:
        return int(
            session.exec(select(func.count(SRState.id)).where(SRState.due <= utcnow())).one()
        )


def _reminder_job() -> None:
    logger.info("Daily reminder: %d item(s) due for review.", _due_count())


def start_reminders() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_reminders or _scheduler is not None:
        return
    try:
        hour, minute = (int(part) for part in settings.reminder_time.split(":", 1))
    except ValueError:
        hour, minute = 18, 0
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_reminder_job, "cron", hour=hour, minute=minute, id="daily_reminder")
    _scheduler.start()
    logger.info("Reminder scheduler started for %02d:%02d.", hour, minute)


def shutdown_reminders() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
