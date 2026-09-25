"""
dashboard_service.py — aggregate queries for the two dashboards.

Keeps SQL out of the route layer. Each function runs a handful of
COUNT/GROUP BY style queries — exactly the kind of read-pattern that a
caching layer (Redis/CDN) would serve in a scaled deployment.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models import Assignment, Course, Enrollment, Submission, SubmissionStatus, User, UserRole
from backend.utils.deadline import ensure_deadline_aware


def _role(user: User) -> UserRole:
    return user.role if isinstance(user.role, UserRole) else UserRole(user.role)


# --------------------------------------------------------------------------
# STUDENT DASHBOARD
# --------------------------------------------------------------------------
def student_dashboard(db: Session, user: User) -> dict:
    """
    Totals over the courses the student is enrolled in:
    pending / submitted / late / graded, upcoming deadlines, recent feedback.
    """
    course_ids = [
        e.course_id for e in db.query(Enrollment).filter(Enrollment.student_id == user.id).all()
    ]
    assignments = (
        db.query(Assignment).filter(Assignment.course_id.in_(course_ids or ["-"])).all()
    )
    assignment_ids = [a.id for a in assignments]
    my_subs = {
        s.assignment_id: s
        for s in db.query(Submission)
        .filter(Submission.student_id == user.id, Submission.assignment_id.in_(assignment_ids or ["-"]))
        .all()
    }

    now = datetime.now().astimezone()
    pending = submitted = late = graded = 0
    upcoming: list[dict] = []
    for a in assignments:
        sub = my_subs.get(a.id)
        deadline = ensure_deadline_aware(a.deadline)
        if sub is None:
            pending += 1
        elif sub.status == SubmissionStatus.GRADED:
            graded += 1
        elif sub.status == SubmissionStatus.LATE:
            late += 1
        else:
            submitted += 1
        if sub is None and deadline > now and deadline <= now + timedelta(days=14):
            upcoming.append(
                {
                    "assignment_id": a.id,
                    "title": a.title,
                    "course": a.course.name if a.course else "",
                    "deadline": deadline.isoformat(),
                    "max_marks": a.max_marks,
                }
            )

    recent_feedback = [
        {
            "submission_id": s.id,
            "assignment_title": (db.get(Assignment, s.assignment_id).title if db.get(Assignment, s.assignment_id) else ""),
            "marks": s.marks,
            "feedback": s.feedback,
            "graded_at": ensure_deadline_aware(s.graded_at).isoformat() if s.graded_at else None,
        }
        for s in sorted(
            [s for s in my_subs.values() if s.status == SubmissionStatus.GRADED and s.graded_at],
            key=lambda s: s.graded_at,
            reverse=True,
        )[:5]
    ]

    return {
        "welcome_name": user.name,
        "total_assignments": len(assignments),
        "pending": pending,
        "submitted": submitted,
        "late": late,
        "graded": graded,
        "upcoming_deadlines": sorted(upcoming, key=lambda x: x["deadline"])[:6],
        "recent_feedback": recent_feedback,
    }


# --------------------------------------------------------------------------
# TEACHER DASHBOARD
# --------------------------------------------------------------------------
def teacher_dashboard(db: Session, user: User) -> dict:
    """Workload overview across every course the teacher owns."""
    courses = db.query(Course).filter(Course.teacher_id == user.id).all()
    course_ids = [c.id for c in courses]
    assignments = (
        db.query(Assignment).filter(Assignment.course_id.in_(course_ids or ["-"])).all()
    )
    assignment_ids = [a.id for a in assignments]
    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id.in_(assignment_ids or ["-"]))
        .all()
    )

    student_ids = {
        e.student_id
        for e in db.query(Enrollment).filter(Enrollment.course_id.in_(course_ids or ["-"])).all()
    }

    now = datetime.now().astimezone()
    pending_reviews = [s for s in submissions if s.status != SubmissionStatus.GRADED]
    late = [s for s in submissions if s.status == SubmissionStatus.LATE]
    graded = [s for s in submissions if s.status == SubmissionStatus.GRADED]

    recent_uploads = sorted(submissions, key=lambda s: s.submitted_at or now, reverse=True)[:5]
    names: dict[str, str] = {}
    for s in recent_uploads:
        if s.student_id not in names:
            u = db.get(User, s.student_id)
            names[s.student_id] = u.name if u else "Unknown"

    upcoming = [
        {
            "assignment_id": a.id,
            "title": a.title,
            "course": a.course.name if a.course else "",
            "deadline": ensure_deadline_aware(a.deadline).isoformat(),
            "submitted_count": sum(1 for s in submissions if s.assignment_id == a.id),
        }
        for a in assignments
        if ensure_deadline_aware(a.deadline) > now
    ]

    return {
        "welcome_name": user.name,
        "total_assignments": len(assignments),
        "total_students": len(student_ids),
        "total_submissions": len(submissions),
        "pending_reviews": len(pending_reviews),
        "late_submissions": len(late),
        "graded_submissions": len(graded),
        "recent_uploads": [
            {
                "submission_id": s.id,
                "assignment_title": db.get(Assignment, s.assignment_id).title,
                "student_name": names.get(s.student_id, "Unknown"),
                "file_name": s.file_name,
                "status": s.status.value if isinstance(s.status, SubmissionStatus) else str(s.status),
                "submitted_at": ensure_deadline_aware(s.submitted_at).isoformat()
                if s.submitted_at
                else None,
            }
            for s in recent_uploads
        ],
        "upcoming_deadlines": sorted(upcoming, key=lambda x: x["deadline"])[:6],
    }
