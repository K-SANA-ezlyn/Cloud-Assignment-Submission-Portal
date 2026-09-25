"""
test_submissions.py — SUBMISSION WORKFLOW tests (TC-08..TC-15, TC-21, TC-22).

Upload validation, deadline logic, resubmission policy, cross-student
isolation and storage-failure handling.
"""

from datetime import datetime, timedelta, timezone

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


def _setup(client, **assignment_overrides):
    t_email = unique_email("sub_t")
    register(client, **TEACHER, email=t_email, role="TEACHER", invite_code="TEST-INVITE-2026")
    t_headers = auth_headers(login(client, t_email, TEACHER["password"]).json()["access_token"])

    s_email = unique_email("sub_s")
    register(client, **STUDENT, email=s_email)
    s_headers = auth_headers(login(client, s_email, STUDENT["password"]).json()["access_token"])

    course = make_course(client, t_headers)
    assert enroll(client, t_headers, course["id"], s_email).status_code == 200
    assignment = make_assignment(client, t_headers, course["id"], **assignment_overrides)
    return t_headers, s_headers, assignment


def submit(client, s_headers, assignment_id, name="work.pdf", content=None, mime="application/pdf"):
    content = fake_pdf() if content is None else content
    return client.post(
        f"/api/assignments/{assignment_id}/submit",
        files={"file": (name, content, mime)},
        headers=s_headers,
    )


# --------------------------------------------------------------------------
# TC-08  Valid upload
# --------------------------------------------------------------------------
def test_valid_pdf_upload(client):
    t, s, a = _setup(client)
    r = submit(client, s, a["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] in ("SUBMITTED", "LATE")
    assert body["attempt_no"] == 1
    assert body["file_name"] == "work.pdf"


def test_upload_status_is_on_time_before_deadline(client):
    t, s, a = _setup(client)  # deadline 3 days out
    r = submit(client, s, a["id"])
    assert r.json()["status"] == "SUBMITTED"


# --------------------------------------------------------------------------
# TC-09 / TC-10  Validation failures
# --------------------------------------------------------------------------
def test_invalid_extension_rejected(client):
    t, s, a = _setup(client)
    r = submit(client, s, a["id"], name="evil.exe", content=b"MZ\x90\x00", mime="application/octet-stream")
    assert r.status_code == 415


def test_fake_pdf_rejected_by_magic_bytes(client):
    t, s, a = _setup(client)
    # .exe renamed to .pdf — extension passes, content does not
    r = submit(client, s, a["id"], name="fake.pdf", content=b"MZ\x90\x00fake")
    assert r.status_code == 415


def test_oversized_file_rejected(client):
    t, s, a = _setup(client, max_file_size_mb=1)
    big = fake_pdf(b"x" * (1024 * 1024 + 100))   # just over 1 MB
    r = submit(client, s, a["id"], content=big)
    assert r.status_code == 413


def test_empty_file_rejected(client):
    t, s, a = _setup(client)
    r = submit(client, s, a["id"], content=b"")
    assert r.status_code == 415


def test_unenrolled_student_cannot_submit(client):
    t_email = unique_email("noenr_t")
    register(client, **TEACHER, email=t_email, role="TEACHER", invite_code="TEST-INVITE-2026")
    t_headers = auth_headers(login(client, t_email, TEACHER["password"]).json()["access_token"])
    s_email = unique_email("noenr_s")
    register(client, **STUDENT, email=s_email)
    s_headers = auth_headers(login(client, s_email, STUDENT["password"]).json()["access_token"])
    course = make_course(client, t_headers)
    a = make_assignment(client, t_headers, course["id"])
    r = submit(client, s_headers, a["id"])   # NOT enrolled
    assert r.status_code == 404


# --------------------------------------------------------------------------
# TC-11 / TC-12  Deadline logic
# --------------------------------------------------------------------------
def test_late_submission_marked_late(client):
    t, s, a = _setup(client, allow_late=True)
    # move the deadline into the past directly in the DB
    from backend.database import SessionLocal
    from backend.models import Assignment

    db = SessionLocal()
    try:
        row = db.get(Assignment, a["id"])
        row.deadline = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    r = submit(client, s, a["id"])
    assert r.status_code == 201
    assert r.json()["status"] == "LATE"


def test_late_submission_blocked_when_disallowed(client):
    t, s, a = _setup(client, allow_late=False)
    from backend.database import SessionLocal
    from backend.models import Assignment

    db = SessionLocal()
    try:
        row = db.get(Assignment, a["id"])
        row.deadline = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    r = submit(client, s, a["id"])
    assert r.status_code == 409


# --------------------------------------------------------------------------
# TC-13  Resubmission policy
# --------------------------------------------------------------------------
def test_resubmission_blocked_when_disallowed(client):
    t, s, a = _setup(client, allow_resubmission=False)
    assert submit(client, s, a["id"]).status_code == 201
    r = submit(client, s, a["id"])
    assert r.status_code == 409


def test_resubmission_replaces_file_and_increments_attempt(client):
    t, s, a = _setup(client, allow_resubmission=True)
    r1 = submit(client, s, a["id"], name="v1.pdf")
    assert r1.status_code == 201
    r2 = submit(client, s, a["id"], name="v2.pdf")
    assert r2.status_code == 201
    body = r2.json()
    assert body["attempt_no"] == 2
    assert body["file_name"] == "v2.pdf"
    # history endpoint reflects the latest attempt
    mine = client.get("/api/submissions/me", headers=s).json()
    assert len(mine) == 1 and mine[0]["attempt_no"] == 2


def test_resubmission_after_grading_blocked(client):
    t, s, a = _setup(client, allow_resubmission=True)
    assert submit(client, s, a["id"]).status_code == 201
    # grade it
    sub_id = client.get("/api/submissions/me", headers=s).json()[0]["id"]
    r = client.post(
        f"/api/submissions/{sub_id}/grade",
        json={"marks": 18, "feedback": "Good work"},
        headers=t,
    )
    assert r.status_code == 200
    assert submit(client, s, a["id"]).status_code == 409


# --------------------------------------------------------------------------
# TC-14 / TC-15  Ownership isolation
# --------------------------------------------------------------------------
def test_student_sees_only_own_submissions(client):
    t, s1, a = _setup(client, allow_resubmission=True)
    # second student, same course
    s2_email = unique_email("peer")
    register(client, **STUDENT, email=s2_email)
    s2_headers = auth_headers(login(client, s2_email, STUDENT["password"]).json()["access_token"])
    # enroll student 2 (teacher knows their email)
    from tests.conftest import enroll as _enroll
    course_id = a["course_id"]
    assert _enroll(client, t, course_id, s2_email).status_code == 200

    assert submit(client, s1, a["id"]).status_code == 201
    mine = client.get("/api/submissions/me", headers=s1).json()
    assert len(mine) == 1 and mine[0]["student_id"] != s2_email
    theirs = client.get("/api/submissions/me", headers=s2_headers).json()
    assert theirs == []


def test_student_cannot_view_other_students_submission(client):
    t, s1, a = _setup(client)
    s2_email = unique_email("peer2")
    register(client, **STUDENT, email=s2_email)
    s2_headers = auth_headers(login(client, s2_email, STUDENT["password"]).json()["access_token"])

    sub_id = submit(client, s1, a["id"]).json()["id"]
    # student 2 tries to read/download student 1's submission
    assert client.get(f"/api/submissions/{sub_id}", headers=s2_headers).status_code == 404
    assert client.get(f"/api/submissions/{sub_id}/download", headers=s2_headers).status_code == 404
    # and cannot grade it either (RBAC)
    r = client.post(f"/api/submissions/{sub_id}/grade", json={"marks": 5, "feedback": "hi"}, headers=s2_headers)
    assert r.status_code == 403


# --------------------------------------------------------------------------
# TC-21  File retrieval
# --------------------------------------------------------------------------
def test_download_returns_original_file(client):
    t, s, a = _setup(client)
    payload = b"%PDF-1.4 special-bytes-12345"
    sub_id = submit(client, s, a["id"], name="answer.pdf", content=payload).json()["id"]

    r = client.get(f"/api/submissions/{sub_id}/download", headers=s)
    assert r.status_code == 200
    assert r.content == payload
    assert "attachment" in r.headers["content-disposition"]

    # teacher can download too
    assert client.get(f"/api/submissions/{sub_id}/download", headers=t).status_code == 200


# --------------------------------------------------------------------------
# TC-22  Cloud-storage failure handling
# --------------------------------------------------------------------------
def test_storage_failure_returns_503(client, monkeypatch):
    from backend.cloud import storage_service

    t, s, a = _setup(client)

    class BrokenProvider:
        def upload(self, data, path):
            raise storage_service.StorageError("simulated outage")

    monkeypatch.setattr(storage_service, "_provider", BrokenProvider())
    r = submit(client, s, a["id"])
    assert r.status_code == 503
    # transactional workflow: no metadata saved when storage fails
    assert client.get("/api/submissions/me", headers=s).json() == []


def test_health_endpoints(client):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health/db").status_code == 200
    assert client.get("/api/health/storage").status_code == 200
