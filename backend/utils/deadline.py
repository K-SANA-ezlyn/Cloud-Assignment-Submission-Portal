"""
deadline.py — server-side deadline decisioning.

RULES
-----
* The CLIENT clock is never trusted (users can change it).
* All deadlines are stored in UTC; comparisons use server UTC time.
* Per-assignment policy decides WHAT HAPPENS when a submission is late:
      allow_late=True  -> accept it, mark status LATE
      allow_late=False -> reject with HTTP 409
"""

from datetime import datetime, timezone


class DeadlineError(Exception):
    """Raised when a late submission is not allowed (mapped to HTTP 409)."""

    def __init__(self, deadline: datetime):
        self.deadline = deadline
        super().__init__("Submission deadline has passed")


def utc_now() -> datetime:
    """Single source of truth for 'now' across the backend."""
    return datetime.now(timezone.utc)


def ensure_deadline_aware(dt: datetime | None) -> datetime | None:
    """Treat naive datetimes as UTC (SQLite returns naive datetimes)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def classify_submission(submitted_at: datetime, deadline: datetime) -> str:
    """
    Return 'SUBMITTED' (on time) or 'LATE'.

    submitted_at <= deadline  -> SUBMITTED
    submitted_at  > deadline  -> LATE
    """
    submitted_at = ensure_deadline_aware(submitted_at)
    deadline = ensure_deadline_aware(deadline)
    return "SUBMITTED" if submitted_at <= deadline else "LATE"


def enforce_deadline(deadline: datetime, allow_late: bool) -> None:
    """
    Gate the submission endpoint.

    * before deadline            -> pass
    * after deadline, allow_late -> pass (caller marks LATE)
    * after deadline, no late    -> raise DeadlineError (HTTP 409)
    """
    now = utc_now()
    deadline = ensure_deadline_aware(deadline)
    if now > deadline and not allow_late:
        raise DeadlineError(deadline)


def is_past(deadline: datetime) -> bool:
    return utc_now() > ensure_deadline_aware(deadline)
