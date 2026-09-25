"""
test_dashboards.py — DASHBOARD aggregate tests.

Verifies the counts and lists returned by /api/dashboard/student and
/api/dashboard/teacher after a realistic submit + grade flow.
"""

from tests.conftest import (
    STUDENT,
    TEACHER,
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
    t_email = unique_email("dash_t")
    register(client, **TEACHER, email=t_email, role="TEACHER", invite_code="TEST-INVITE-2026")
    t_headers = auth_headers(login(client, t_email, TEACHER["password"]).json()["access_token"])

    s_email = unique_email("dash_s")
    register(client, **STUDENT, email=s_email)
    s_headers = auth_headers(login(client, s_email, STUDENT["password"]).json()["access_token"])

    course = make_course(client, t_headers)
    assert enroll(client, t_headers, course["id"], s_email).status_code == 200
    a1 = make_assignment(client, t_headers, course["id"], title="Pending Task", max_marks=10)
    a2 = make_assignment(client, t_headers, course["id"], title="Grade Me", max_marks=10)
    return t_headers, s_headers, a1, a2


def test_student_dashboard_counts(client):
    t, s, a1, a2 = _setup(client)

    # submit a2, leave a1 pending
    r = client.post(
        f"/api/assignments/{a2['id']}/submit",
        files={"file": ("a2.pdf", fake_pdf(), "application/pdf")},
        headers=s,
    )
    assert r.status_code == 201

    # grade a2
    sub_id = r.json()["id"]
    assert (
        client.post(
            f"/api/submissions/{sub_id}/grade",
            json={"marks": 9, "feedback": "Nice."},
            headers=t,
        ).status_code
        == 200
    )

    dash = client.get("/api/dashboard/student", headers=s)
    assert dash.status_code == 200
    body = dash.json()
    assert body["total_assignments"] == 2
    assert body["pending"] == 1
    assert body["graded"] == 1
    assert body["submitted"] == 0
    # only PENDING work appears under upcoming deadlines (a2 is graded)
    assert len(body["upcoming_deadlines"]) == 1
    assert body["upcoming_deadlines"][0]["title"] == "Pending Task"
    assert len(body["recent_feedback"]) == 1
    assert body["recent_feedback"][0]["marks"] == 9


def test_teacher_dashboard_counts(client):
    t, s, a1, a2 = _setup(client)
    r = client.post(
        f"/api/assignments/{a2['id']}/submit",
        files={"file": ("a2.pdf", fake_pdf(), "application/pdf")},
        headers=s,
    )
    sub_id = r.json()["id"]

    dash = client.get("/api/dashboard/teacher", headers=t)
    assert dash.status_code == 200
    body = dash.json()
    assert body["total_assignments"] == 2
    assert body["total_students"] == 1
    assert body["total_submissions"] == 1
    assert body["pending_reviews"] == 1
    assert body["graded_submissions"] == 0
    assert body["recent_uploads"][0]["student_name"]

    # grade -> pending_reviews drops
    client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 8, "feedback": "Good."},
        headers=t,
    )
    body = client.get("/api/dashboard/teacher", headers=t).json()
    assert body["pending_reviews"] == 0
    assert body["graded_submissions"] == 1
