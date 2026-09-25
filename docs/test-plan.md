# Test Plan & Test-Case Matrix

## 1. Strategy

- **Automated** (pytest, run in CI): 49 tests in `tests/` cover functional,
  authorization, validation, deadline, storage-failure and dashboard cases.
  Run: `pytest -v` (or `python -m pytest tests/ -v`).
- **End-to-end smoke** (live server): `python scripts/smoke_test.py` — 17 checks
  over real HTTP.
- **Manual** (UI walkthrough): matrix below — record Actual + Pass/Fail during
  your demo and paste into `reports/manual-test-results.md`.

Automated mapping: TC-01..TC-03, TC-06..TC-25 → pytest functions
(`test_auth.py`, `test_assignments.py`, `test_submissions.py`,
`test_grading.py`, `test_dashboards.py`).

## 2. Manual test-case matrix (fill "Actual/Result" during your demo)

| ID | Scenario | Input | Expected result | Actual | Pass/Fail |
|---|---|---|---|---|---|
| TC-01 | Student registration | valid name/email/password (8+), role STUDENT | 201; account listed in users; auto role STUDENT | | |
| TC-02 | Teacher login | teacher@demo.edu / Teacher@12345 | 200 token; Teacher Dashboard opens | | |
| TC-03 | Invalid login | registered email + wrong password | 401 "Invalid email or password"; no token | | |
| TC-04 | Student dashboard authorization | student token → GET /api/dashboard/teacher | 403 "Requires role: TEACHER"; UI bounces student | | |
| TC-05 | Teacher dashboard authorization | teacher token → GET /api/dashboard/student | 403 "Requires role: STUDENT" | | |
| TC-06 | Teacher creates assignment | title, course, future deadline, max marks 20 | 201; appears in list; teacher dashboard count +1 | | |
| TC-07 | Student views assignment | enrolled student opens Assignments | assignment visible with deadline & status NOT_SUBMITTED | | |
| TC-08 | Valid PDF upload | sample_files/demo-submission.pdf | 201; status SUBMITTED; file in uploads/ | | |
| TC-09 | Invalid file extension | notes.exe | 415; error banner; nothing stored | | |
| TC-10 | Oversized file | 12 MB PDF vs 10 MB cap | 413 "File too large…"; nothing stored | | |
| TC-11 | On-time submission | upload before deadline | status SUBMITTED | | |
| TC-12 | Late submission | deadline edited to past, allow_late ON | status LATE; accepted | | |
| TC-12b | Late blocked | allow_late OFF, past deadline | 409 "deadline has passed" | | |
| TC-13 | Resubmission | allow_resubmission ON; upload twice | attempt #2 stored; old object replaced | | |
| TC-13b | Resubmission blocked | allow_resubmission OFF, 2nd upload | 409 "not allowed" | | |
| TC-14 | Student views own submission | My Submissions | row with file, status, attempt | | |
| TC-15 | Cross-student isolation | student B opens student A's submission URL | 404; download 404 | | |
| TC-16 | Teacher views submissions | Review page | roster with names, files, statuses | | |
| TC-17 | Teacher grades | marks 18 + feedback | 200; status GRADED; student sees it | | |
| TC-18 | Marks above maximum | 25/20 | 400 "exceed maximum" | | |
| TC-19 | Student views feedback | My Submissions / feedback endpoint | marks + text + graded_at visible | | |
| TC-20 | Unauthorized grading | student token → grade endpoint | 403; no change to marks | | |
| TC-21 | File retrieval | download own submission | bytes match original; opens as PDF | | |
| TC-22 | Cloud-storage failure | rename uploads/ away; probe/upload | 503; no metadata row; UI graceful banner | | |
| TC-23 | Database failure | stop DB / bad DATABASE_URL | /api/health/db → 503; errors logged, no crash loop | | |
| TC-24 | Logout | logout button | token cleared; dashboard redirects to login | | |
| TC-25 | Protected route after logout | GET /api/auth/me without token | 401; SPA redirects to /login?expired=1 | | |

## 3. What CI proves to a reviewer

```yaml
# .github/workflows/ci.yml (in repo)
- backend: pip install → pytest (49 tests) on every push
- frontend: npm ci → vite build (type/import safety) on every push
```
Green badges on the README are the fastest "this project actually works" signal.
