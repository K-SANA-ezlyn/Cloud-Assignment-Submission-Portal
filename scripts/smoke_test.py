"""
smoke_test.py — END-TO-END SMOKE TEST against a LIVE server.

Start the API, then run:
    python scripts/smoke_test.py            (defaults to http://localhost:8000)
    python scripts/smoke_test.py http://localhost:8765

It walks the complete user story over real HTTP:
  health -> register teacher/student -> login -> course -> enrollment ->
  assignment -> upload -> download -> review -> grade -> feedback ->
  dashboards -> negative authorization checks.

Exit code 0 = all steps passed.
"""

import re
import sys
import uuid
from datetime import datetime, timedelta, timezone

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=30)

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail and not ok else ""))


run = uuid.uuid4().hex[:6]
TEACHER = {"email": f"smoke.teacher.{run}@demo.edu", "password": "Teacher@12345", "name": "Dr. Smoke"}
STUDENT = {"email": f"smoke.student.{run}@demo.edu", "password": "Student@12345", "name": "Smokey Student"}


def main() -> None:
    # 0. liveness
    r = client.get("/api/health")
    check("health endpoint", r.status_code == 200, f"{r.status_code} {r.text[:120]}")

    # 1. register + login both roles
    r = client.post("/api/auth/register", json={**TEACHER, "role": "TEACHER", "invite_code": "TEACHER-2026-DEMO"})
    check("teacher registration (invite code)", r.status_code == 201, f"{r.status_code} {r.text[:150]}")
    r = client.post("/api/auth/register", json={**STUDENT, "role": "STUDENT"})
    check("student registration", r.status_code == 201, f"{r.status_code} {r.text[:150]}")

    t_token = client.post("/api/auth/login", json={"email": TEACHER["email"], "password": TEACHER["password"]}).json()["access_token"]
    s_token = client.post("/api/auth/login", json={"email": STUDENT["email"], "password": STUDENT["password"]}).json()["access_token"]
    t = {"Authorization": f"Bearer {t_token}"}
    s = {"Authorization": f"Bearer {s_token}"}
    check("login issues JWTs for both roles", bool(t_token) and bool(s_token))

    # 2. course + enrollment
    course = client.post("/api/courses", json={"name": f"Smoke Course {run}"}, headers=t).json()
    check("teacher creates course", "id" in course, str(course)[:150])
    r = client.post(f"/api/courses/{course['id']}/enroll", json={"student_email": STUDENT["email"]}, headers=t)
    check("teacher enrolls student", r.status_code == 200, f"{r.status_code} {r.text[:150]}")

    # 3. assignment
    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    r = client.post(
        "/api/assignments",
        json={
            "course_id": course["id"],
            "title": f"Smoke Assignment {run}",
            "description": "Upload a PDF report on cloud object storage.",
            "deadline": deadline,
            "max_marks": 20,
            "allowed_extensions": "pdf",
            "max_file_size_mb": 5,
            "allow_resubmission": True,
            "allow_late": True,
        },
        headers=t,
    )
    assignment = r.json()
    check("teacher creates assignment", r.status_code == 201, f"{r.status_code} {r.text[:200]}")

    # 4. student upload
    pdf_bytes = b"%PDF-1.4 smoke-test-file " + run.encode()
    r = client.post(
        f"/api/assignments/{assignment['id']}/submit",
        files={"file": ("smoke_report.pdf", pdf_bytes, "application/pdf")},
        headers=s,
    )
    submission = r.json()
    check("student uploads PDF (201, SUBMITTED)", r.status_code == 201 and submission.get("status") == "SUBMITTED",
          f"{r.status_code} {r.text[:200]}")

    # 5. download round-trip
    r = client.get(f"/api/submissions/{submission['id']}/download", headers=s)
    check("student downloads own file (bytes match)", r.status_code == 200 and r.content == pdf_bytes,
          f"{r.status_code} len={len(r.content)}")

    # 6. negative: bad extension
    r = client.post(
        f"/api/assignments/{assignment['id']}/submit",
        files={"file": ("virus.exe", b"MZ\x90\x00", "application/octet-stream")},
        headers=s,
    )
    check("upload with .exe rejected (415)", r.status_code == 415, str(r.status_code))

    # 7. negative: student cannot open teacher dashboard
    r = client.get("/api/dashboard/teacher", headers=s)
    check("student blocked from teacher dashboard (403)", r.status_code == 403, str(r.status_code))

    # 8. teacher reviews + grades
    rows = client.get(f"/api/assignments/{assignment['id']}/submissions", headers=t).json()
    check("teacher lists submissions", len(rows) == 1 and rows[0]["student_name"] == STUDENT["name"])
    r = client.post(
        f"/api/submissions/{submission['id']}/grade",
        json={"marks": 18, "feedback": "Excellent report — clear explanation of signed URLs."},
        headers=t,
    )
    check("teacher grades (GRADED)", r.status_code == 200 and r.json().get("status") == "GRADED", f"{r.status_code} {r.text[:150]}")

    # 9. student reads feedback
    fb = client.get(f"/api/submissions/{submission['id']}/feedback", headers=s).json()
    check("student reads marks + feedback", fb.get("marks") == 18 and "signed URLs" in (fb.get("feedback") or ""))

    # 10. dashboards
    sd = client.get("/api/dashboard/student", headers=s).json()
    td = client.get("/api/dashboard/teacher", headers=t).json()
    check("student dashboard aggregates", sd.get("graded") == 1 and sd.get("total_assignments") == 1)
    check("teacher dashboard aggregates", td.get("total_submissions") == 1 and td.get("graded_submissions") == 1)

    # 11. unauthenticated download blocked
    r = client.get(f"/api/submissions/{submission['id']}/download")
    check("anonymous download blocked (401)", r.status_code == 401, str(r.status_code))

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"{passed}/{len(results)} smoke checks passed")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
