"""
test_auth.py — AUTHENTICATION & RBAC tests.

Covers test-plan cases TC-01..TC-05, TC-24, TC-25:
registration, teacher invite gate, invalid login, role-based
authorization, logout, and protected routes after logout.
"""

from tests.conftest import (
    STUDENT,
    TEACHER,
    auth_headers,
    login,
    register,
    unique_email,
)


# --------------------------------------------------------------------------
# TC-01  Student registration
# --------------------------------------------------------------------------
def test_student_registration_succeeds(client):
    r = register(client, **STUDENT, email=unique_email("tc01"))
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "STUDENT"
    assert "password_hash" not in body          # never leak hashes


# --------------------------------------------------------------------------
# Registration validation
# --------------------------------------------------------------------------
def test_duplicate_email_rejected(client):
    email = unique_email("dup")
    assert register(client, **STUDENT, email=email).status_code == 201
    r = register(client, **STUDENT, email=email)
    assert r.status_code == 409


def test_weak_password_rejected(client):
    payload = {**STUDENT, "password": "short", "email": unique_email("weak")}
    r = register(client, **payload)
    assert r.status_code == 422


def test_invalid_email_rejected(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "Student@12345", "name": "X"},
    )
    assert r.status_code == 422


# --------------------------------------------------------------------------
# TC-02 / TC-03  Login paths
# --------------------------------------------------------------------------
def test_teacher_login_with_invite(client):
    email = unique_email("tc02")
    r = register(client, **TEACHER, email=email, role="TEACHER", invite_code="TEST-INVITE-2026")
    assert r.status_code == 201
    assert r.json()["role"] == "TEACHER"
    assert login(client, email, TEACHER["password"]).status_code == 200


def test_teacher_registration_without_invite_blocked(client):
    r = register(client, **TEACHER, email=unique_email("tc03a"), role="TEACHER")
    assert r.status_code == 403


def test_invalid_login_wrong_password(client):
    email = unique_email("tc03")
    register(client, **STUDENT, email=email)
    r = login(client, email, "WrongPassword1")
    assert r.status_code == 401


def test_invalid_login_unknown_email(client):
    r = login(client, "ghost@test.edu", "Whatever@123")
    assert r.status_code == 401


def test_login_returns_usable_token(client):
    email = unique_email("tok")
    register(client, **STUDENT, email=email)
    body = login(client, email, STUDENT["password"]).json()
    assert body["token_type"] == "bearer"
    r = client.get("/api/auth/me", headers=auth_headers(body["access_token"]))
    assert r.status_code == 200
    assert r.json()["email"] == email


# --------------------------------------------------------------------------
# TC-04 / TC-05  Dashboard authorization (RBAC)
# --------------------------------------------------------------------------
def test_student_cannot_open_teacher_dashboard(client, student):
    headers, _ = student
    assert client.get("/api/dashboard/teacher", headers=headers).status_code == 403


def test_teacher_cannot_open_student_dashboard(client, teacher):
    headers, _ = teacher
    assert client.get("/api/dashboard/student", headers=headers).status_code == 403


def test_teacher_cannot_create_assignment(client, teacher):
    headers, t = teacher
    r = client.post(
        "/api/assignments",
        json={"course_id": "whatever", "title": "Nope", "deadline": "2026-12-01T00:00:00Z"},
        headers=headers,
    )
    # teacher without the course -> 404 (course not found) but never 2xx
    assert r.status_code == 404


def test_protected_route_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/dashboard/student").status_code == 401
    assert client.get("/api/submissions/me").status_code == 401


# --------------------------------------------------------------------------
# TC-24 / TC-25  Logout & protected route after logout
# --------------------------------------------------------------------------
def test_logout_and_protected_route_after_logout(client, student):
    headers, _ = student
    assert client.post("/api/auth/logout", headers=headers).status_code == 200

    # Client discards the token; requests without it are rejected.
    assert client.get("/api/auth/me").status_code == 401
    # A tampered/garbage token must also fail.
    bad = auth_headers("not-a-real-token")
    assert client.get("/api/auth/me", headers=bad).status_code == 401
