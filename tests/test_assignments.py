"""
test_assignments.py — ASSIGNMENT MANAGEMENT tests (TC-06, TC-07).

Assignment CRUD authorization: teachers manage their own courses,
students can view but not modify, deadlines/policies are enforced.
"""

from datetime import datetime, timedelta, timezone

from tests.conftest import (
    auth_headers,
    enroll,
    fake_pdf,
    login,
    make_assignment,
    make_course,
    register,
    unique_email,
)


def _setup(client):
    """teacher + course + enrolled student -> returns handles."""
    t_headers, t = teacher = None, None
    from tests.conftest import TEACHER, STUDENT

    t_email = unique_email("tc06t")
    r = register(client, **TEACHER, email=t_email, role="TEACHER", invite_code="TEST-INVITE-2026")
    assert r.status_code == 201
    t_headers = auth_headers(login(client, t_email, TEACHER["password"]).json()["access_token"])

    s_email = unique_email("tc06s")
    register(client, **STUDENT, email=s_email)
    s_headers = auth_headers(login(client, s_email, STUDENT["password"]).json()["access_token"])

    course = make_course(client, t_headers)
    assert enroll(client, t_headers, course["id"], s_email).status_code == 200
    return t_headers, s_headers, course


def test_teacher_creates_assignment(client):
    t_headers, _, course = _setup(client)
    a = make_assignment(client, t_headers, course["id"], title="TC-06 Assignment")
    assert a["title"] == "TC-06 Assignment"
    assert a["max_marks"] == 20


def test_student_views_assignments_of_enrolled_course(client):
    t_headers, s_headers, course = _setup(client)
    make_assignment(client, t_headers, course["id"], title="TC-07 Assignment")
    r = client.get("/api/assignments", headers=s_headers)
    assert r.status_code == 200
    titles = [a["title"] for a in r.json()]
    assert "TC-07 Assignment" in titles
    assert r.json()[0]["my_status"] == "NOT_SUBMITTED"


def test_student_cannot_create_assignment(client, student):
    headers, _ = student
    r = client.post(
        "/api/assignments",
        json={"course_id": "x", "title": "Hack", "deadline": "2026-12-01T00:00:00Z"},
        headers=headers,
    )
    assert r.status_code == 403


def test_teacher_cannot_see_other_teachers_course(client):
    t1_headers, _, course = _setup(client)
    # second teacher
    from tests.conftest import TEACHER
    email2 = unique_email("other")
    register(client, **TEACHER, email=email2, role="TEACHER", invite_code="TEST-INVITE-2026")
    h2 = auth_headers(login(client, email2, TEACHER["password"]).json()["access_token"])
    r = client.put(
        f"/api/assignments/{course['id']}",
        json={"title": "Hijack"},
        headers=h2,
    )
    assert r.status_code in (403, 404)


def test_update_assignment(client):
    t_headers, _, course = _setup(client)
    a = make_assignment(client, t_headers, course["id"])
    r = client.put(
        f"/api/assignments/{a['id']}",
        json={"title": "Renamed", "max_marks": 50},
        headers=t_headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed"
    assert r.json()["max_marks"] == 50


def test_delete_assignment(client):
    t_headers, _, course = _setup(client)
    a = make_assignment(client, t_headers, course["id"])
    r = client.delete(f"/api/assignments/{a['id']}", headers=t_headers)
    assert r.status_code == 200
    assert client.get(f"/api/assignments/{a['id']}", headers=t_headers).status_code == 404


def test_assignment_detail_embeds_student_status(client):
    t_headers, s_headers, course = _setup(client)
    a = make_assignment(client, t_headers, course["id"], allow_resubmission=True)
    # student uploads
    r = client.post(
        f"/api/assignments/{a['id']}/submit",
        files={"file": ("work.pdf", fake_pdf(b"hello"), "application/pdf")},
        headers=s_headers,
    )
    assert r.status_code == 201
    detail = client.get(f"/api/assignments/{a['id']}", headers=s_headers).json()
    assert detail["my_status"] in ("SUBMITTED", "LATE")
    assert detail["submitted_count"] == 1
