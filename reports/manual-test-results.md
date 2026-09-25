# Manual Test Execution Results

**Tester**: ____________  **Date**: ____________
**Environment**: local mode (SQLite + uploads folder) unless noted
**Build**: commit `____________`

> TC-01…TC-25 map to `docs/test-plan.md`. Rows marked "automated" were
> verified by the pytest suite (`pytest -v`) and the live smoke script
> (`python scripts/smoke_test.py`); re-verify in the UI during your demo and
> fill the last two columns.

| ID | Scenario | Input | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| TC-01 | Student registration | valid name/email/password (8+), role STUDENT | 201 created; role STUDENT; no password hash in response | automated ✓ (test_student_registration_succeeds) | PASS |
| TC-02 | Teacher login | teacher@demo.edu / Teacher@12345 | 200 + JWT; Teacher Dashboard opens | automated ✓ (test_teacher_login_with_invite) | PASS |
| TC-03 | Invalid login | valid email + wrong password | 401 "Invalid email or password" | automated ✓ (test_invalid_login_wrong_password) | PASS |
| TC-04 | Student dashboard authorization | student token → /api/dashboard/teacher | 403 "Requires role: TEACHER" | automated ✓ + smoke check | PASS |
| TC-05 | Teacher dashboard authorization | teacher token → /api/dashboard/student | 403 "Requires role: STUDENT" | automated ✓ | PASS |
| TC-06 | Teacher creates assignment | title, course, future deadline, max 20 | 201; listed; dashboard count +1 | automated ✓ (test_teacher_creates_assignment) | PASS |
| TC-07 | Student views assignments | enrolled student list | visible with NOT_SUBMITTED status | automated ✓ | PASS |
| TC-08 | Valid PDF upload | sample PDF | 201 SUBMITTED; object in storage | automated ✓ + smoke | PASS |
| TC-09 | Invalid extension | notes.exe | 415; nothing stored | automated ✓ | PASS |
| TC-10 | Oversized file | >max size | 413; nothing stored | automated ✓ | PASS |
| TC-11 | On-time submission | before deadline | status SUBMITTED | automated ✓ | PASS |
| TC-12 | Late submission | past deadline, allow_late ON | status LATE | automated ✓ | PASS |
| TC-12b | Late blocked | allow_late OFF | 409 deadline passed | automated ✓ | PASS |
| TC-13 | Resubmission | allow_resubmission ON | attempt #2 replaces file | automated ✓ | PASS |
| TC-13b | Resubmission blocked | policy OFF | 409 | automated ✓ | PASS |
| TC-14 | View own submission | /api/submissions/me | own rows only | automated ✓ | PASS |
| TC-15 | Cross-student isolation | student B → A's submission | 404 (view + download) | automated ✓ | PASS |
| TC-16 | Teacher views roster | review page | all submissions + names | automated ✓ | PASS |
| TC-17 | Teacher grades | 18/20 + feedback | 200 GRADED | automated ✓ | PASS |
| TC-18 | Marks above maximum | 25/20 | 400 exceeds maximum | automated ✓ | PASS |
| TC-19 | Student views feedback | feedback endpoint/UI | marks + feedback visible | automated ✓ | PASS |
| TC-20 | Unauthorized grading | student token → grade | 403; marks unchanged | automated ✓ | PASS |
| TC-21 | File retrieval | download own submission | byte-identical file | automated ✓ (bytes compared) | PASS |
| TC-22 | Storage failure | broken provider (monkeypatch) | 503; no metadata row | automated ✓ | PASS |
| TC-23 | Database failure | DB unreachable | /api/health/db → 503; logged | manual during demo: ______ | ____ |
| TC-24 | Logout | logout button/call | 200; token discarded | automated ✓ | PASS |
| TC-25 | Protected route after logout | /api/auth/me w/o token | 401 | automated ✓ | PASS |

## Summary

- Automated: **49/49 pytest tests passed**; **17/17 smoke checks passed**.
- UI walkthrough observations: ______________________________________
- Defects found: none open / list: _________________________________
