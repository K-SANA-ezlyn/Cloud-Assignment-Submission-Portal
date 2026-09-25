"""Import all models here so Base.metadata knows the full schema."""

from backend.models.user import User, UserRole
from backend.models.course import Course, Enrollment
from backend.models.assignment import Assignment
from backend.models.submission import Submission, SubmissionStatus

__all__ = [
    "User",
    "UserRole",
    "Course",
    "Enrollment",
    "Assignment",
    "Submission",
    "SubmissionStatus",
]
