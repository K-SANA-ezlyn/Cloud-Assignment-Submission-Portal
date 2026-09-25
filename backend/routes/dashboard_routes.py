"""
dashboard_routes.py — role-aware dashboard endpoints.

GET /api/dashboard/student  -> STUDENT role only
GET /api/dashboard/teacher  -> TEACHER role only
(RBAC dependencies return 403 for the wrong role.)
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import StudentDashboard, TeacherDashboard
from backend.services import dashboard_service
from backend.utils.security import StudentUser, TeacherUser

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/student", response_model=StudentDashboard)
def student_dashboard(current: StudentUser, db: Annotated[Session, Depends(get_db)]):
    """Stats for the logged-in student across all enrolled courses."""
    return dashboard_service.student_dashboard(db, current)


@router.get("/teacher", response_model=TeacherDashboard)
def teacher_dashboard(current: TeacherUser, db: Annotated[Session, Depends(get_db)]):
    """Workload overview for the logged-in teacher across their courses."""
    return dashboard_service.teacher_dashboard(db, current)
