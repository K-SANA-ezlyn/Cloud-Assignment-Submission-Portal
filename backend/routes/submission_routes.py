"""
submission_routes.py — SUBMISSIONS, FILE DOWNLOAD and GRADING.

Endpoints
---------
POST /api/assignments/{id}/submit        student uploads a file (multipart)
GET  /api/submissions/me                 student's own submission history
GET  /api/assignments/{id}/submissions   teacher's roster for an assignment
GET  /api/submissions/{id}               single submission (role-checked)
GET  /api/submissions/{id}/download      secure file download
POST /api/submissions/{id}/grade         teacher awards marks + feedback
GET  /api/submissions/{id}/feedback      student reads marks + feedback
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.cloud.storage_service import (
    StorageError,
    build_storage_path,
    get_storage_provider,
)
from backend.database import get_db
from backend.models import (
    Assignment,
    Course,
    Enrollment,
    Submission,
    SubmissionStatus,
    User,
    UserRole,
)
from backend.schemas.schemas import FeedbackOut, GradeRequest, SubmissionOut
from backend.utils.deadline import classify_submission, enforce_deadline, ensure_deadline_aware, utc_now
from backend.utils.security import CurrentUser, TeacherUser
from backend.utils.validators import FileValidationError, validate_file, validate_marks

logger = logging.getLogger("portal.submissions")
router = APIRouter(tags=["submissions"])


# --------------------------------------------------------------------------
# STUDENT: submit / resubmit
# --------------------------------------------------------------------------
@router.post(
    "/api/assignments/{assignment_id}/submit",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assignment(
    assignment_id: str,
    file: UploadFile,
    current: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Full upload pipeline (all steps server-side):

        authn -> enrollment check -> assignment lookup -> deadline gate
        -> resubmission policy -> file validation (type/size/magic bytes)
        -> object-storage upload -> metadata row -> status (SUBMITTED/LATE)
    """
    role = current.role if isinstance(current.role, UserRole) else UserRole(current.role)
    if role is not UserRole.STUDENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students submit assignments")

    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")

    # Visibility rule: the student must be enrolled in the assignment's course.
    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == assignment.course_id, Enrollment.student_id == current.id)
        .first()
    )
    if not enrolled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")

    # ---- Deadline gate (server clock only) ----
    # raises DeadlineError -> handled globally as HTTP 409
    enforce_deadline(assignment.deadline, assignment.allow_late)

    # ---- Resubmission policy ----
    existing = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == current.id)
        .first()
    )
    attempt_no = 1
    if existing is not None:
        if not assignment.allow_resubmission:
            raise HTTPException(status.HTTP_409_CONFLICT, "Resubmission is not allowed for this assignment")
        if existing.status == SubmissionStatus.GRADED:
            raise HTTPException(status.HTTP_409_CONFLICT, "Already graded — resubmission closed")
        attempt_no = existing.attempt_no + 1

    # ---- Read + validate file BEFORE touching storage ----
    # validate_file raises FileValidationError -> handled globally as HTTP 415
    data = await file.read()
    await file.close()
    validate_file(
        filename=file.filename or "upload",
        data=data,
        allowed_extensions=[
            e.strip().lower().lstrip(".")
            for e in (assignment.allowed_extensions or "").split(",")
            if e.strip()
        ],
        max_size_mb=assignment.max_file_size_mb,
    )

    # ---- Upload to object storage (local folder or Supabase) ----
    storage_path = build_storage_path(assignment.id, current.id, attempt_no, file.filename or "upload")
    try:
        get_storage_provider().upload(data, storage_path)
    except StorageError:
        logger.error("Storage upload failed; metadata NOT saved (transactional workflow)")
        raise

    # ---- Save metadata to the cloud database ----
    status_value = classify_submission(utc_now(), assignment.deadline)
    if existing is not None:
        # Resubmission: replace the old object and update the row.
        get_storage_provider().delete(existing.storage_path)
        existing.file_name = file.filename
        existing.storage_path = storage_path
        existing.file_size = len(data)
        existing.mime_type = file.content_type or ""
        existing.attempt_no = attempt_no
        existing.submitted_at = utc_now()
        existing.status = SubmissionStatus(status_value)
        existing.marks = None
        existing.feedback = None
        existing.graded_at = None
        existing.graded_by = None
        db.commit()
        db.refresh(existing)
        logger.info("Resubmission #%d by %s for %s", attempt_no, current.email, assignment.title)
        return _submission_out(existing, current.name)

    submission = Submission(
        assignment_id=assignment.id,
        student_id=current.id,
        file_name=file.filename,
        storage_path=storage_path,
        file_size=len(data),
        mime_type=file.content_type or "",
        attempt_no=attempt_no,
        status=SubmissionStatus(status_value),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    logger.info("Submission created: %s -> %s (%s)", current.email, assignment.title, status_value)
    return _submission_out(submission, current.name)


# --------------------------------------------------------------------------
# STUDENT: my submissions
# --------------------------------------------------------------------------
@router.get("/api/submissions/me", response_model=list[SubmissionOut])
def my_submissions(current: CurrentUser, db: Session = Depends(get_db)):
    """Student's own submission history (never anyone else's)."""
    rows = (
        db.query(Submission)
        .filter(Submission.student_id == current.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return [_submission_out(s, current.name) for s in rows]


# --------------------------------------------------------------------------
# TEACHER: roster of submissions for an assignment
# --------------------------------------------------------------------------
@router.get("/api/assignments/{assignment_id}/submissions", response_model=list[SubmissionOut])
def assignment_submissions(assignment_id: str, teacher: TeacherUser, db: Session = Depends(get_db)):
    """Teacher sees all submissions for assignments in their own courses."""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    course = db.get(Course, assignment.course_id)
    if course is None or course.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")

    rows = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id)
        .order_by(Submission.submitted_at.asc())
        .all()
    )
    student_names = _student_name_map(db, rows)
    return [_submission_out(s, student_names.get(s.student_id, "Unknown")) for s in rows]


# --------------------------------------------------------------------------
# SINGLE SUBMISSION (role-aware)
# --------------------------------------------------------------------------
@router.get("/api/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """
    Authorization matrix:
      student -> only their own submission
      teacher -> only submissions for assignments in their courses
    """
    submission, student_name = _get_authorized_submission(db, submission_id, current)
    return _submission_out(submission, student_name)


# --------------------------------------------------------------------------
# FILE DOWNLOAD (secure)
# --------------------------------------------------------------------------
@router.get("/api/submissions/{submission_id}/download")
def download_submission(submission_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """
    Secure download. The uploads/ folder is NEVER served statically —
    every byte passes through this authorization checkpoint.
    Cloud mode returns a short-lived signed URL instead of the bytes.
    """
    submission, _ = _get_authorized_submission(db, submission_id, current)

    provider = get_storage_provider()
    if hasattr(provider, "create_signed_url"):  # Supabase (private bucket)
        return {"download_url": provider.create_signed_url(submission.storage_path)}

    try:
        data = provider.download(submission.storage_path)
    except StorageError:
        logger.error("Download failed: object missing at %s", submission.storage_path)
        raise
    return Response(
        content=data,
        media_type=submission.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{submission.file_name}"'},
    )


# --------------------------------------------------------------------------
# GRADING & FEEDBACK
# --------------------------------------------------------------------------
@router.post("/api/submissions/{submission_id}/grade", response_model=SubmissionOut)
def grade_submission(
    submission_id: str,
    payload: GradeRequest,
    teacher: TeacherUser,
    db: Session = Depends(get_db),
):
    """
    Teacher awards marks + feedback.

    Validations: owns the course, marks within 0..max_marks, resubmission
    after grading is closed automatically (status is GRADED).
    """
    submission, student_name = _get_authorized_submission(db, submission_id, teacher)
    assignment = db.get(Assignment, submission.assignment_id)
    validate_marks(payload.marks, assignment.max_marks)

    submission.marks = payload.marks
    submission.feedback = payload.feedback.strip()
    submission.graded_at = utc_now()
    submission.graded_by = teacher.id
    submission.status = SubmissionStatus.GRADED
    db.commit()
    db.refresh(submission)
    logger.info("Graded submission %s: %s/%s", submission.id, payload.marks, assignment.max_marks)
    return _submission_out(submission, student_name)


@router.get("/api/submissions/{submission_id}/feedback", response_model=FeedbackOut)
def get_feedback(submission_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """Student (or owning teacher) reads marks + written feedback."""
    submission, student_name = _get_authorized_submission(db, submission_id, current)
    assignment = db.get(Assignment, submission.assignment_id)
    graded_by_name = None
    if submission.graded_by:
        grader = db.get(User, submission.graded_by)
        graded_by_name = grader.name if grader else None
    return FeedbackOut(
        submission_id=submission.id,
        marks=submission.marks,
        max_marks=assignment.max_marks,
        feedback=submission.feedback,
        graded_at=submission.graded_at,
        graded_by_name=graded_by_name,
    )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _get_authorized_submission(db: Session, submission_id: str, user: User) -> tuple[Submission, str]:
    """Central row-level authorization for every submission-related route."""
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")

    role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
    if role is UserRole.STUDENT:
        if submission.student_id != user.id:
            # 404 hides the existence of other students' submissions.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
        return submission, user.name

    # Teacher path: must own the course the assignment belongs to.
    assignment = db.get(Assignment, submission.assignment_id)
    course = db.get(Course, assignment.course_id) if assignment else None
    if course is None or course.teacher_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    student = db.get(User, submission.student_id)
    return submission, student.name if student else "Unknown"


def _student_name_map(db: Session, rows: list[Submission]) -> dict[str, str]:
    names: dict[str, str] = {}
    for s in rows:
        if s.student_id not in names:
            u = db.get(User, s.student_id)
            names[s.student_id] = u.name if u else "Unknown"
    return names


def _submission_out(s: Submission, student_name: str) -> SubmissionOut:
    return SubmissionOut(
        id=s.id,
        assignment_id=s.assignment_id,
        student_id=s.student_id,
        student_name=student_name,
        file_name=s.file_name,
        file_size=s.file_size,
        mime_type=s.mime_type,
        attempt_no=s.attempt_no,
        submitted_at=ensure_deadline_aware(s.submitted_at),
        status=s.status.value if isinstance(s.status, SubmissionStatus) else str(s.status),
        marks=s.marks,
        feedback=s.feedback,
        graded_at=ensure_deadline_aware(s.graded_at),
    )
