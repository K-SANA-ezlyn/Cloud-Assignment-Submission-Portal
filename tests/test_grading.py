"""
test_grading.py — GRADING & FEEDBACK tests (TC-16..TC-20).

Teacher reviews, marks boundaries, feedback visibility, and
authorization rules (students can never grade).
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
    t_email = unique_email("grd_t")
    register(client, **TEACHER, email=t_email, role="TEACHER", invite_code="TEST-INVITE-2026")
    t_headers = auth_headers(login(client, t_email, TEACHER["password"]).json()["access_token"])

    s_email = unique_email("grd_s")
    register(client, **STUDENT, email=s_email)
    s_headers = auth_headers(login(client, s_email, STUDENT["password"]).json()["access_token"])

    course = make_course(client, t_headers)
    assert enroll(client, t_headers, course["id"], s_email).status_code == 200
    a = make_assignment(client, t_headers, course["id"], max_marks=20)
    return t_headers, s_headers, a


def _submit(client, s_headers, assignment_id):
    r = client.post(
        f"/api/assignments/{assignment_id}/submit",
        files={"file": ("sub.pdf", fake_pdf(b"essay"), "application/pdf")},
        headers=s_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --------------------------------------------------------------------------
# TC-16 / TC-17  Teacher views & grades
# --------------------------------------------------------------------------
def test_teacher_views_assignment_submissions(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    r = client.get(f"/api/assignments/{a['id']}/submissions", headers=t)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["id"] == sub_id
    assert rows[0]["student_name"]


def test_teacher_grades_submission(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 18, "feedback": "Excellent analysis of object storage."},
        headers=t,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["marks"] == 18
    assert body["status"] == "GRADED"


def test_grade_marks_zero_is_valid(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 0, "feedback": "Nothing submitted of value."},
        headers=t,
    )
    assert r.status_code == 200


# --------------------------------------------------------------------------
# TC-18  Marks boundary validation
# --------------------------------------------------------------------------
def test_marks_above_maximum_rejected(client):
    t, s, a = _setup(client)      # max_marks = 20
    sub_id = _submit(client, s, a["id"])
    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 25, "feedback": "Too generous"},
        headers=t,
    )
    assert r.status_code == 400


def test_negative_marks_rejected(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": -3, "feedback": "Negative"},
        headers=t,
    )
    assert r.status_code in (400, 422)


# --------------------------------------------------------------------------
# TC-20  Unauthorized grading
# --------------------------------------------------------------------------
def test_student_cannot_grade(client, student):
    headers, _ = student
    r = client.post(
        "/api/submissions/00000000-0000-0000-0000-000000000000/grade",
        json={"marks": 5, "feedback": "self-grade attempt"},
        headers=headers,
    )
    assert r.status_code == 403


def test_other_teacher_cannot_grade(client):
    t1, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])

    email2 = unique_email("intruder")
    register(client, **TEACHER, email=email2, role="TEACHER", invite_code="TEST-INVITE-2026")
    t2 = auth_headers(login(client, email2, TEACHER["password"]).json()["access_token"])

    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 10, "feedback": "not my course"},
        headers=t2,
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------
# TC-19  Student reads feedback
# --------------------------------------------------------------------------
def test_student_views_marks_and_feedback(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    assert (
        client.post(
            f"/api/submissions/{sub_id}/grade",
            json={"marks": 16, "feedback": "Solid; add a scalability section."},
            headers=t,
        ).status_code
        == 200
    )

    fb = client.get(f"/api/submissions/{sub_id}/feedback", headers=s)
    assert fb.status_code == 200
    body = fb.json()
    assert body["marks"] == 16
    assert body["max_marks"] == 20
    assert "scalability" in body["feedback"]

    # grading record is immutable from the student side:
    # there is simply no student-writable endpoint for marks/feedback.
    me = client.get("/api/submissions/me", headers=s).json()[0]
    assert me["status"] == "GRADED"
    assert me["marks"] == 16


def test_feedback_page_for_ungraded_is_empty_not_error(client):
    t, s, a = _setup(client)
    sub_id = _submit(client, s, a["id"])
    fb = client.get(f"/api/submissions/{sub_id}/feedback", headers=s)
    assert fb.status_code == 200
    assert fb.json()["marks"] is None
