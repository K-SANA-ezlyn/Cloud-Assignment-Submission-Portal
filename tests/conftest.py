"""
conftest.py — pytest fixtures for the portal test suite.

Test environment strategy:
  * ENVIRONMENT=test        -> rate limiting disabled
  * temp SQLite database    -> same code path as cloud Postgres
  * temp uploads folder     -> same code path as cloud object storage
  * fresh schema per test   -> full isolation between tests
"""

import os
import tempfile
import uuid

# ---------------------------------------------------------------------------
# Configure environment BEFORE any backend import (settings are cached).
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/test_portal_{os.getpid()}.db"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="portal_uploads_")
os.environ["STORAGE_PROVIDER"] = "local"
os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["TEACHER_INVITE_CODE"] = "TEST-INVITE-2026"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["SEED_TEACHER_PASSWORD"] = "Teacher@12345"
os.environ["SEED_STUDENT_PASSWORD"] = "Student@12345"

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import Base, engine


@pytest.fixture()
def client():
    """Fresh database + TestClient for every test (full isolation)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helper functions shared by tests
# ---------------------------------------------------------------------------
TEACHER = {"password": "Teacher@12345", "name": "Dr. Test"}
STUDENT = {"password": "Student@12345", "name": "Test Student"}


def register(client, *, email, password, name, role="STUDENT", invite_code=None):
    payload = {"email": email, "password": password, "name": name, "role": role}
    if invite_code:
        payload["invite_code"] = invite_code
    return client.post("/api/auth/register", json=payload)


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def unique_email(base="user"):
    return f"{base}-{uuid.uuid4().hex[:8]}@test.edu"


@pytest.fixture()
def teacher(client):
    """Registered + logged-in teacher. Returns (headers, user_dict)."""
    email = unique_email("teacher")
    r = register(client, email=email, password=TEACHER["password"], name="Dr. Tester", role="TEACHER", invite_code="TEST-INVITE-2026")
    assert r.status_code == 201, r.text
    token = login(client, email, TEACHER["password"]).json()["access_token"]
    return auth_headers(token), r.json()


@pytest.fixture()
def student(client):
    """Registered + logged-in student. Returns (headers, user_dict)."""
    email = unique_email("student")
    r = register(client, email=email, password=STUDENT["password"], name="Testy Student")
    assert r.status_code == 201, r.text
    token = login(client, email, STUDENT["password"]).json()["access_token"]
    return auth_headers(token), r.json()


def make_course(client, teacher_headers, name="Cloud Computing 101"):
    r = client.post("/api/courses", json={"name": name}, headers=teacher_headers)
    assert r.status_code == 201, r.text
    return r.json()


def enroll(client, teacher_headers, course_id, student_email):
    return client.post(
        f"/api/courses/{course_id}/enroll",
        json={"student_email": student_email},
        headers=teacher_headers,
    )


def make_assignment(client, teacher_headers, course_id, **overrides):
    from datetime import datetime, timedelta, timezone

    payload = {
        "course_id": course_id,
        "title": "Test Assignment",
        "description": "Demo description",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        "max_marks": 20,
        "allowed_extensions": "pdf",
        "max_file_size_mb": 5,
        "allow_resubmission": False,
        "allow_late": True,
    }
    payload.update(overrides)
    r = client.post("/api/assignments", json=payload, headers=teacher_headers)
    assert r.status_code == 201, r.text
    return r.json()


def fake_pdf(bytes_extra: bytes = b"") -> bytes:
    """Minimal byte sequence that passes PDF magic-byte validation."""
    return b"%PDF-1.4\n" + bytes_extra
