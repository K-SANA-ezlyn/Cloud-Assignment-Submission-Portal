"""
Assignment model — coursework created by a teacher inside a course.

Upload policy fields (allowed extensions, max size, resubmission, late
policy) make every rule configurable per assignment, which the submission
workflow enforces server-side.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    # Deadlines are stored in UTC; the frontend renders them in local time.
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_marks: Mapped[int] = mapped_column(Integer, default=100)
    # Upload policy (comma separated, e.g. "pdf,docx,zip")
    allowed_extensions: Mapped[str] = mapped_column(String(200), default="pdf")
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=10)
    # Resubmission policy
    allow_resubmission: Mapped[bool] = mapped_column(Boolean, default=False)
    # Late policy: True -> late uploads accepted with status LATE
    allow_late: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "max_marks": self.max_marks,
            "allowed_extensions": [
                e.strip().lower().lstrip(".")
                for e in (self.allowed_extensions or "").split(",")
                if e.strip()
            ],
            "max_file_size_mb": self.max_file_size_mb,
            "allow_resubmission": self.allow_resubmission,
            "allow_late": self.allow_late,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
