"""
Submission model — one student's uploaded file + grading record.

The FILE lives in object storage (local folder / Supabase Storage).
This row stores only METADATA: who submitted what, where the object
lives, when, with which status, and later the marks + feedback.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"   # on time, awaiting grading
    LATE = "LATE"             # accepted after deadline
    GRADED = "GRADED"         # teacher has graded


class Submission(Base):
    __tablename__ = "submissions"
    # One submission row per (assignment, student); resubmission UPDATES it.
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assignments.id"), index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )

    # ---- Object-storage metadata ----
    file_name: Mapped[str] = mapped_column(String(255))          # original filename
    storage_path: Mapped[str] = mapped_column(String(500))       # key inside the bucket
    file_size: Mapped[int] = mapped_column(Integer, default=0)   # bytes
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status", native_enum=False),
        default=SubmissionStatus.SUBMITTED,
    )

    # ---- Grading & feedback (teacher writes, student read-only) ----
    marks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    graded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])

    def public_dict(self, include_grading: bool = True) -> dict:
        data = {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "attempt_no": self.attempt_no,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "status": self.status.value if isinstance(self.status, SubmissionStatus) else self.status,
        }
        if include_grading:
            data.update(
                {
                    "marks": self.marks,
                    "feedback": self.feedback,
                    "graded_at": self.graded_at.isoformat() if self.graded_at else None,
                    "graded_by": self.graded_by,
                }
            )
        return data
