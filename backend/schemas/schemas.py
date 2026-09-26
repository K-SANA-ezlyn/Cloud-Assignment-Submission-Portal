"""
Pydantic schemas — request/response contracts for the REST API.

Every input is validated here BEFORE reaching business logic:
wrong types, missing fields, or out-of-range values return a clean
HTTP 422 with details instead of a 500 crash.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --------------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, examples=["min 8 chars"])
    role: Literal["STUDENT", "TEACHER"] = "STUDENT"
    # Required only when role=TEACHER (invite-only teacher registration).
    invite_code: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime


TokenResponse.model_rebuild()


# --------------------------------------------------------------------------
# COURSES
# --------------------------------------------------------------------------
class CourseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class CourseOut(BaseModel):
    id: str
    name: str
    teacher_id: str
    created_at: datetime
    student_count: int = 0
    assignment_count: int = 0


class EnrollRequest(BaseModel):
    student_email: EmailStr


# --------------------------------------------------------------------------
# ASSIGNMENTS
# --------------------------------------------------------------------------
class AssignmentCreate(BaseModel):
    course_id: str
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    # ISO-8601 datetime; the frontend sends UTC or an offset-aware string.
    deadline: datetime
    max_marks: int = Field(default=100, ge=1, le=1000)
    allowed_extensions: str = Field(default="pdf", max_length=200)
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    allow_resubmission: bool = False
    allow_late: bool = True


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    deadline: datetime | None = None
    max_marks: int | None = Field(default=None, ge=1, le=1000)
    allowed_extensions: str | None = Field(default=None, max_length=200)
    max_file_size_mb: int | None = Field(default=None, ge=1, le=100)
    allow_resubmission: bool | None = None
    allow_late: bool | None = None


class AssignmentOut(AssignmentCreate):
    id: str
    created_by: str
    created_at: datetime
    course_name: str = ""
    submitted_count: int = 0
    # Filled for STUDENTS in list/detail views ("my" submission status):
    my_status: str | None = None
    my_marks: int | None = None
    my_feedback: str | None = None


# --------------------------------------------------------------------------
# SUBMISSIONS & GRADING
# --------------------------------------------------------------------------
class SubmissionOut(BaseModel):
    id: str
    assignment_id: str
    assignment_title: str = ""
    student_id: str
    student_name: str = ""
    file_name: str
    file_size: int
    mime_type: str
    attempt_no: int
    submitted_at: datetime
    status: str
    marks: int | None = None
    feedback: str | None = None
    graded_at: datetime | None = None


class GradeRequest(BaseModel):
    marks: int = Field(ge=0, le=1000)
    feedback: str = Field(min_length=3, max_length=5000)


class FeedbackOut(BaseModel):
    submission_id: str
    marks: int | None
    max_marks: int
    feedback: str | None
    graded_at: datetime | None
    graded_by_name: str | None = None


# --------------------------------------------------------------------------
# DASHBOARDS
# --------------------------------------------------------------------------
class StudentDashboard(BaseModel):
    welcome_name: str
    total_assignments: int
    pending: int
    submitted: int
    late: int
    graded: int
    upcoming_deadlines: list[dict]
    recent_feedback: list[dict]


class TeacherDashboard(BaseModel):
    welcome_name: str
    total_assignments: int
    total_students: int
    total_submissions: int
    pending_reviews: int
    late_submissions: int
    graded_submissions: int
    recent_uploads: list[dict]
    upcoming_deadlines: list[dict]
