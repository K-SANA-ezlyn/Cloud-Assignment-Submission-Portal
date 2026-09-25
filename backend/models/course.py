"""
Course + Enrollment models.

Relationship chain demonstrated:
    Teacher -> Course -> Assignment -> Submission <- Student
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(150))
    # Teacher owns the course — used for "teacher may only touch own courses".
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    teacher = relationship("User", foreign_keys=[teacher_id])
    assignments = relationship(
        "Assignment", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    """Join table: a student enrolled in a course (drives visibility rules)."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_course_student"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    course = relationship("Course", back_populates="enrollments")
