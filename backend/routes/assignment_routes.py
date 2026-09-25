"""
assignment_routes.py — ASSIGNMENT MANAGEMENT (teacher CRUD + student views).

POST   /api/assignments          teacher creates
GET    /api/assignments          role-aware listing
GET    /api/assignments/{id}     role-aware detail (includes my_submission)
PUT    /api/assignments/{id}     teacher updates (owner only)
DELETE /api/assignments/{id}     teacher deletes (owner only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models import Assignment, Course, Enrollment, Submission, SubmissionStatus, User, UserRole
from backend.schemas.schemas import AssignmentCreate, AssignmentOut, AssignmentUpdate
from backend.utils.security import CurrentUser, TeacherUser

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, teacher: TeacherUser, db: Session = Depends(get_db)):
    """Create an assignment in one of the teacher's own courses."""
    course = db.get(Course, payload.course_id)
    if course is None or course.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")

    assignment = Assignment(
        course_id=course.id,
        title=payload.title.strip(),
        description=payload.description,
        deadline=payload.deadline,
        max_marks=payload.max_marks,
        allowed_extensions=payload.allowed_extensions,
        max_file_size_mb=payload.max_file_size_mb,
        allow_resubmission=payload.allow_resubmission,
        allow_late=payload.allow_late,
        created_by=teacher.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return _assignment_out(db, assignment, None)


@router.get("", response_model=list[AssignmentOut])
def list_assignments(current: CurrentUser, db: Session = Depends(get_db)):
    """
    Role-aware listing:
      teacher -> assignments across their courses
      student -> assignments of courses they are enrolled in
    """
    role = current.role if isinstance(current.role, UserRole) else UserRole(current.role)
    if role is UserRole.TEACHER:
        course_ids = [c.id for c in db.query(Course).filter(Course.teacher_id == current.id).all()]
    else:
        course_ids = [
            e.course_id for e in db.query(Enrollment).filter(Enrollment.student_id == current.id).all()
        ]
    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.course))
        .filter(Assignment.course_id.in_(course_ids or ["-"]))
        .order_by(Assignment.deadline.asc())
        .all()
    )
    my_submissions = {
        s.assignment_id: s
        for s in db.query(Submission).filter(Submission.student_id == current.id).all()
    }
    return [_assignment_out(db, a, my_submissions.get(a.id)) for a in assignments]


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """Detail view — also returns THIS student's submission state."""
    assignment, course = _get_visible_assignment(db, assignment_id, current)
    my_submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == current.id)
        .first()
    )
    return _assignment_out(db, assignment, my_submission)


@router.put("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    teacher: TeacherUser,
    db: Session = Depends(get_db),
):
    """Update an assignment (teacher must own its course)."""
    assignment = _get_own_assignment(db, assignment_id, teacher)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return _assignment_out(db, assignment, None)


@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
def delete_assignment(assignment_id: str, teacher: TeacherUser, db: Session = Depends(get_db)):
    """Delete an assignment and (cascading) its submissions metadata."""
    assignment = _get_own_assignment(db, assignment_id, teacher)
    db.delete(assignment)
    db.commit()
    return {"detail": "Assignment deleted", "id": assignment_id}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _get_own_assignment(db: Session, assignment_id: str, teacher: User) -> Assignment:
    """Owner-or-404 fetch used by PUT/DELETE (no data leak across teachers)."""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    course = db.get(Course, assignment.course_id)
    if course is None or course.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return assignment


def _get_visible_assignment(db: Session, assignment_id: str, user: User) -> tuple[Assignment, Course]:
    """Fetch an assignment the user is allowed to SEE (student must be enrolled)."""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    course = db.get(Course, assignment.course_id)

    role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
    if role is UserRole.TEACHER:
        if course is None or course.teacher_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    else:
        enrolled = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == assignment.course_id, Enrollment.student_id == user.id)
            .first()
        )
        if not enrolled:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return assignment, course


def _assignment_out(
    db: Session,
    a: Assignment,
    my_submission: Submission | None,
) -> AssignmentOut:
    """Serialize an assignment; embeds the student's own status when known."""
    data = {
        "id": a.id,
        "course_id": a.course_id,
        "course_name": a.course.name if a.course else "",
        "title": a.title,
        "description": a.description,
        "deadline": a.deadline,
        "max_marks": a.max_marks,
        "allowed_extensions": a.allowed_extensions,
        "max_file_size_mb": a.max_file_size_mb,
        "allow_resubmission": a.allow_resubmission,
        "allow_late": a.allow_late,
        "created_by": a.created_by,
        "created_at": a.created_at,
        "submitted_count": db.query(Submission).filter(Submission.assignment_id == a.id).count(),
    }
    if my_submission is not None:
        data["my_status"] = (
            my_submission.status.value
            if isinstance(my_submission.status, SubmissionStatus)
            else str(my_submission.status)
        )
        data["my_marks"] = my_submission.marks
        data["my_feedback"] = my_submission.feedback
    else:
        data["my_status"] = "NOT_SUBMITTED"
    return AssignmentOut(**data)
