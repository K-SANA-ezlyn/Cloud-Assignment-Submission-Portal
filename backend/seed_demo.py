"""
seed_demo.py — populate the portal with DUMMY demo data.

Run:  python -m backend.seed_demo

Creates (if missing):
  * 1 teacher  teacher@demo.edu    / Teacher@12345
  * 6 students student1..6@demo.edu / Student@12345
  * 1 course   "Cloud Computing (CS-402)"
  * enrollments for all students
  * 4 assignments (one already past deadline, one resubmission-enabled)

Passwords come from env vars when set (SEED_TEACHER_PASSWORD /
SEED_STUDENT_PASSWORD) so no secret is hardcoded into history.
"""

import logging

from backend.cloud.auth_service import hash_password
from backend.config import settings
from backend.database import Base, SessionLocal, engine
from backend.models import Assignment, Course, Enrollment, User, UserRole
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portal.seed")

TEACHER_EMAIL = "teacher@demo.edu"
STUDENT_EMAILS = [f"student{i}@demo.edu" for i in range(1, 7)]


def seed() -> None:
    import backend.models  # noqa: F401 — ensure tables exist

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ---- Teacher ----
        teacher = db.query(User).filter(User.email == TEACHER_EMAIL).first()
        if teacher is None:
            teacher = User(
                name="Dr. Ada Metrics",
                email=TEACHER_EMAIL,
                password_hash=hash_password(settings.SEED_TEACHER_PASSWORD),
                role=UserRole.TEACHER,
            )
            db.add(teacher)
            db.flush()

        # ---- Students ----
        students: list[User] = []
        for email in STUDENT_EMAILS:
            s = db.query(User).filter(User.email == email).first()
            if s is None:
                s = User(
                    name=email.split("@")[0].replace("student", "Student "),
                    email=email,
                    password_hash=hash_password(settings.SEED_STUDENT_PASSWORD),
                    role=UserRole.STUDENT,
                )
                db.add(s)
            students.append(s)
        db.flush()

        # ---- Course ----
        course = db.query(Course).filter(Course.name == "Cloud Computing (CS-402)").first()
        if course is None:
            course = Course(name="Cloud Computing (CS-402)", teacher_id=teacher.id)
            db.add(course)
            db.flush()

        # ---- Enrollments ----
        for s in students:
            exists = (
                db.query(Enrollment)
                .filter(Enrollment.course_id == course.id, Enrollment.student_id == s.id)
                .first()
            )
            if not exists:
                db.add(Enrollment(course_id=course.id, student_id=s.id))

        # ---- Assignments ----
        now = datetime.now(timezone.utc)
        demo_assignments = [
            dict(
                title="Lab 1 — Deploy a Static Site to Object Storage",
                description=(
                    "Upload a static website to a cloud object-storage bucket, enable "
                    "public read via signed URLs, and submit a 2-page PDF report plus "
                    "the bucket URL. Demonstrates object storage + static hosting."
                ),
                deadline=now + timedelta(days=7),
                max_marks=20,
                allowed_extensions="pdf,zip",
                max_file_size_mb=10,
                allow_resubmission=True,
                allow_late=True,
            ),
            dict(
                title="Lab 2 — Serverless Function for File Validation",
                description=(
                    "Write a serverless function that validates uploaded files "
                    "(extension + magic bytes) and returns JSON. Submit the code as a "
                    "ZIP and a short PDF write-up. Demonstrates serverless computing."
                ),
                deadline=now + timedelta(days=14),
                max_marks=25,
                allowed_extensions="pdf,zip",
                max_file_size_mb=15,
                allow_resubmission=True,
                allow_late=True,
            ),
            dict(
                title="Assignment 1 — Cloud Security Report",
                description=(
                    "A 4-page report covering IAM, encryption at rest/in transit and "
                    "signed URLs. PDF only, strict deadline (no late submissions)."
                ),
                deadline=now + timedelta(days=3),
                max_marks=30,
                allowed_extensions="pdf",
                max_file_size_mb=5,
                allow_resubmission=False,
                allow_late=False,
            ),
            dict(
                title="Quiz 0 — Cloud Concepts Warm-up (CLOSED)",
                description=(
                    "Legacy quiz whose deadline has already passed with late uploads "
                    "disabled. Used to demo the 'deadline passed' error path."
                ),
                deadline=now - timedelta(days=2),
                max_marks=10,
                allowed_extensions="pdf",
                max_file_size_mb=5,
                allow_resubmission=False,
                allow_late=False,
            ),
        ]
        for spec in demo_assignments:
            exists = db.query(Assignment).filter(Assignment.title == spec["title"]).first()
            if exists:
                continue
            db.add(Assignment(course_id=course.id, created_by=teacher.id, **spec))

        db.commit()
        logger.info("Demo data ready:")
        logger.info("  Teacher : %s (role TEACHER)", TEACHER_EMAIL)
        for email in STUDENT_EMAILS:
            logger.info("  Student : %s (role STUDENT)", email)
        logger.info("  Course  : Cloud Computing (CS-402) with 4 assignments")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
