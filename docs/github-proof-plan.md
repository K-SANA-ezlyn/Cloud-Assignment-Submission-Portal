# GitHub Proof-Building Plan (13 Days) + Screenshot Checklist

> The repository was built incrementally — use this plan to schedule the
> commits day-by-day so your GitHub history tells the real story.

## 1. Day-by-day plan

**DAY 1 — Architecture + repository**
Files: `.gitignore`, `.env.example`, `requirements.txt`, folder tree, `docs/architecture.md`.
Commit: `Initialize cloud assignment portal`
Screenshot: repo home (`01-github-repo-home.png`).

**DAY 2 — Authentication**
Files: `cloud/auth_service.py`, `routes/auth_routes.py`, `utils/security.py` (get_current_user).
Commit: `Implement authentication with JWT and bcrypt password hashing`
Screenshot: Swagger login → token (`04-login-page.png`, `21-api-response.png`).

**DAY 3 — Role-based access**
Files: `require_roles`, StudentUser/TeacherUser deps; RBAC tests.
Commit: `Add role-based authorization for student and teacher routes`
Screenshot: 403 response (`20-authorization-error-demo.png`).

**DAY 4 — Assignment management**
Files: `models/assignment.py`, `routes/assignment_routes.py`, teacher UI form.
Commit: `Add assignment management module with validation`
Screenshot: creation form (`06-assignment-creation-form.png`).

**DAY 5 — Cloud database**
Files: `database.py`, `cloud/database_service.py`, models, health probe.
Commit: `Integrate cloud database with provider abstraction (SQLite/Postgres)`
Screenshot: `/api/health/db` (`13-database-submission-record.png`).

**DAY 6 — Cloud object storage**
Files: `cloud/storage_service.py` (both providers), storage docs.
Commit: `Implement cloud object storage with local and Supabase providers`
Screenshot: object key listing (`12-cloud-storage-file.png`).

**DAY 7 — Student submission**
Files: `routes/submission_routes.py` (submit/download), upload UI.
Commit: `Add student assignment submission workflow with secure downloads`
Screenshot: upload success (`11-successful-upload-confirmation.png`).

**DAY 8 — Deadline logic**
Files: `utils/deadline.py`, policy fields, late/blocked tests.
Commit: `Implement server-side deadline validation with late policy`
Screenshots: LATE badge + 409 (`15-late-submission-demo.png`).

**DAY 9 — Teacher feedback & grading**
Files: grade endpoint, marks bounds, ReviewSubmissions UI.
Commit: `Add teacher grading and feedback with marks validation`
Screenshot: grading card (`18-teacher-grading-marks-feedback.png`).

**DAY 10 — Dashboards**
Files: `services/dashboard_service.py`, dashboard routes + pages.
Commit: `Build student and teacher dashboards with aggregate statistics`
Screenshots: both dashboards (`05-teacher-dashboard.png`, `07-student-dashboard.png`).

**DAY 11 — Testing & security**
Files: full pytest suite, smoke script, security docs.
Commit: `Add automated tests and security hardening`
Screenshot: `pytest` output (`22-automated-tests-pass.png`).

**DAY 12 — Cloud deployment**
Files: `.env.cloud.example`, deployment docs, CI workflow.
Commit: `Deploy application to cloud (Render + Vercel + Supabase)`
Screenshots: dashboards (`23-cloud-deployment-dashboard.png`, `24-live-application.png`).

**DAY 13 — README & documentation**
Files: README, docs suite, screenshots folder.
Commit: `Complete README and project documentation`
Screenshot: README preview (`27-readme-preview.png`).

**Suggested commit flow (recommended order)**
```
git add <files> && git commit -m "<message above>"
```
Small, single-purpose commits beat one giant commit for reviewer trust.

## 2. Screenshot / proof checklist (27 items)

Save into `screenshots/` with these exact names:

| File name | Proves |
|---|---|
| `01-project-folder-structure.png` | repo layout, modular design |
| `02-architecture-diagram.png` | system design understanding |
| `03-login-page.png` | auth entry point |
| `04-student-registration.png` | self-registration flow |
| `05-teacher-dashboard.png` | role-based UI + aggregates |
| `06-assignment-creation-form.png` | teacher workflow + policy fields |
| `07-student-dashboard.png` | role-based UI + stats |
| `08-assignment-list.png` | visibility rules per role |
| `09-assignment-details.png` | brief + status + policies |
| `10-file-selection-screen.png` | upload widget with constraints |
| `11-successful-upload-confirmation.png` | end-to-end write path |
| `12-cloud-storage-file.png` | object exists in storage (folder or Supabase UI) |
| `13-database-submission-record.png` | metadata row (SQL or Supabase table editor) |
| `14-on-time-submission-status.png` | deadline logic (SUBMITTED) |
| `15-late-submission-demo.png` | deadline logic (LATE / 409) |
| `16-teacher-submission-list.png` | roster + statuses |
| `17-teacher-reviewing-file.png` | downloaded/viewed submission |
| `18-teacher-grading-marks-feedback.png` | grading + feedback entry |
| `19-student-feedback-page.png` | marks + feedback visibility |
| `20-authorization-error-demo.png` | RBAC denial (403 UI/API) |
| `21-api-response.png` | Swagger/Postman JSON response |
| `22-automated-tests-pass.png` | pytest 49/49 green |
| `23-cloud-deployment-dashboard.png` | Render service live |
| `24-live-application.png` | public URL working |
| `25-github-commits.png` | incremental history |
| `26-github-repository.png` | repo home with topics/description |
| `27-readme-preview.png` | rendered README |

## 3. Repository metadata

- **Name**: `Cloud-Assignment-Submission-Portal`
- **Description**: "Cloud-based student assignment submission and feedback platform featuring role-based authentication, cloud database integration, object storage, assignment management, secure file submission, grading, and feedback workflows."
- **Topics**: `cloud-computing` `edtech` `python` `fastapi` `react` `cloud-storage` `supabase` `database` `rest-api` `full-stack` `authentication` `rbac`
- **Features image**: pin the architecture diagram at the top of the README.
