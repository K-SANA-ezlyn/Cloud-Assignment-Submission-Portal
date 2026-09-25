"""
course_routes.py — course management and enrollment.

A teacher may only see/modify their own courses (row-level authorization).
Students see only courses they are enrolled in.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Course, Enrollment, User, UserRole
from backend.schemas.schemas import CourseCreate, CourseOut, EnrollRequest
from backend.utils.security import CurrentUser, TeacherUser

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    teacher: TeacherUser,
    db: Session = Depends(get_db),
):
    """Teachers create courses; students are rejected with 403 by RBAC."""
    course = Course(name=payload.name.strip(), teacher_id=teacher.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return _course_out(db, course)


@router.get("", response_model=list[CourseOut])
def list_courses(current: CurrentUser, db: Session = Depends(get_db)):
    """Teachers see their courses; students see their enrollments."""
    role = current.role if isinstance(current.role, UserRole) else UserRole(current.role)
    if role is UserRole.TEACHER:
        courses = db.query(Course).filter(Course.teacher_id == current.id).order_by(Course.created_at.desc()).all()
    else:
        course_ids = [
            e.course_id
            for e in db.query(Enrollment).filter(Enrollment.student_id == current.id).all()
        ]
        courses = db.query(Course).filter(Course.id.in_(course_ids or ["-"])).all()
    return [_course_out(db, c) for c in courses]


@router.post("/{course_id}/enroll", response_model=CourseOut)
def enroll(
    course_id: str,
    payload: EnrollRequest,
    teacher: TeacherUser,
    db: Session = Depends(get_db),
):
    """Teacher enrolls a student by email into their own course."""
    course = _get_own_course(db, course_id, teacher)
    student = db.query(User).filter(User.email == payload.student_email.lower().strip()).first()
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No student with that email")
    if (student.role if isinstance(student.role, UserRole) else UserRole(student.role)) is not UserRole.STUDENT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is not a student")

    exists = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course.id, Enrollment.student_id == student.id)
        .first()
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Student already enrolled")

    db.add(Enrollment(course_id=course.id, student_id=student.id))
    db.commit()
    db.refresh(course)
    return _course_out(db, course)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _get_own_course(db: Session, course_id: str, teacher: User) -> Course:
    """Fetch a course and enforce that it belongs to this teacher (404 vs 403)."""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    if course.teacher_id != teacher.id:
        # 404 (not 403) avoids leaking other teachers' course IDs.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    return course


def _course_out(db: Session, course: Course) -> CourseOut:
    return CourseOut(
        id=course.id,
        name=course.name,
        teacher_id=course.teacher_id,
        created_at=course.created_at,
        student_count=db.query(Enrollment).filter(Enrollment.course_id == course.id).count(),
        assignment_count=len(course.assignments),
    )
