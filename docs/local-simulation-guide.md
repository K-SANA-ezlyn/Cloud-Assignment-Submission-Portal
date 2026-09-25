# Local Simulation Guide — Zero Cloud, Zero Cost

Run the entire "cloud" system on your laptop. Every service is a local
stand-in for its cloud counterpart, and switching to the real cloud later is
an environment-variable change (see `cloud-deployment.md`).

## Step 0 — Install required software (once)

1. **Python 3.11+** — https://www.python.org/downloads/ (tick "Add to PATH" on Windows)
2. **Node.js 18+** (includes npm) — https://nodejs.org
3. **Git** — https://git-scm.com

Verify (any terminal):
```bash
python --version     # Python 3.13.x  (3.11+ is fine)
node --version       # v20+ or v24+
npm --version        # 10+
git --version        # 2.40+
```

## Step 1 — Open the project folder

```bash
cd Cloud-Assignment-Submission-Portal
```

## Step 2 — Create a virtual environment

```bash
python -m venv .venv
```
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Expected: your prompt gains a `(.venv)` prefix.

## Step 3 — Install backend dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```
Expected: ~15 packages install; ends with no errors.

## Step 4 — Configure environment

```bash
cp .env.example .env        # Windows: copy .env.example .env
```
The defaults are perfect for local mode. Optionally generate a real secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
# paste the output into SECRET_KEY in .env
```

## Step 5 — Start the backend (Terminal 1)

```bash
uvicorn backend.app:app --reload --port 8000
```
Expected output:
```
INFO:     portal.app: Portal API started | env=local | storage=local | auth=local | db=sqlite
INFO:     Uvicorn running on http://0.0.0.0:8000
```
Open http://localhost:8000/docs — the Swagger UI lists all 21 endpoints.

## Step 6 — Install frontend dependencies (Terminal 2)

```bash
cd frontend
npm install
```
Expected: ~150 packages, `added … packages` with 0 vulnerabilities blocking.

## Step 7 — Start the frontend

```bash
npm run dev
```
Expected:
```
VITE v6.x  ready in ~500 ms
➜  Local:  http://localhost:5173/
```
Open http://localhost:5173 — you should see the login page.

## Step 8 — Seed dummy accounts (Terminal 3)

```bash
# in project root, venv active
python -m backend.seed_demo
```
Expected:
```
INFO portal.seed: Demo data ready:
INFO portal.seed:   Teacher : teacher@demo.edu (role TEACHER)
INFO portal.seed:   Student : student1@demo.edu (role STUDENT)   … student2..6
INFO portal.seed:   Course  : Cloud Computing (CS-402) with 4 assignments
```
Passwords: teacher `Teacher@12345`, students `Student@12345`
(override in `.env` via `SEED_TEACHER_PASSWORD` / `SEED_STUDENT_PASSWORD`).

## Step 9 — Log in as teacher

At http://localhost:5173: `teacher@demo.edu` / `Teacher@12345`.
Expected: redirect to **Teacher Dashboard** with stats (4 assignments, 6 students).

## Step 10 — Teacher creates an assignment

Dashboard → **+ New assignment** → choose course, title
("Lab 5 — Signed URLs"), description, deadline (future date/time),
max marks 20, allowed types `pdf`, max size 5 MB, tick *Allow resubmission*.
Expected: redirect to the assignment page; it appears in the list.

## Step 11 — Log in as student

Logout → login `student1@demo.edu` / `Student@12345`.
Expected: **Student Dashboard** — "Total assignments: 4/5", pending count, upcoming deadline listed.

## Step 12 — Student views the assignment

**Assignments** → open the new assignment. Expected: description, deadline
countdown badge, "Your status: Not submitted", upload widget with allowed types.

## Step 13 — Student uploads a sample PDF

Pick any small PDF (create `sample_files/demo-submission.pdf` content or use any PDF)
→ **Upload submission**.
Expected: green banner `Uploaded as … — status: SUBMITTED`, status badge flips to **Submitted**.

## Step 14 — Verify file storage on disk

```bash
# from project root
ls uploads/submissions/<assignment_id>/<student_id>/
```
Expected: something like `1_9f2c43ab_demo-submission.pdf` — the object the
DB row points at. (This folder *is* your local "object storage".)

## Step 15 — Verify submission metadata in the database

```bash
python - <<'PY'
import sqlite3
db = sqlite3.connect("portal.db")
for row in db.execute("SELECT file_name, storage_path, status, attempt_no FROM submissions"):
    print(row)
PY
```
Expected: one row — file name, object key, `SUBMITTED`, attempt 1.

## Step 16 — Teacher reviews the submission

Logout → teacher login → **Assignments** → **Review** on the assignment.
Expected: one submission card with student name, file, size, attempt, and a
**Download file** button (opens/saves the PDF).

## Step 17 — Teacher grades

Enter **18** and feedback: "Excellent — clear explanation of signed URLs." → **Submit grade**.
Expected: card status flips to **GRADED**; dashboard "Pending reviews" decreases.

## Step 18 — Student views marks and feedback

Logout → student login → **My Submissions**.
Expected: row with **Graded** badge, `18` marks and the feedback text; the
student dashboard's *Recent feedback* card shows it too. **Download** re-fetches
your own file (404 for anyone else's — try swapping tokens to prove it).

## Bonus verifications for screenshots

- Late demo: set an assignment deadline in the past (edit as teacher) with
  "Accept late" on → student upload shows **LATE**.
- Deadline block: same but "Accept late" off → red 409 banner.
- RBAC demo: as student, browse `http://localhost:5173/teacher` → bounced to
  your dashboard; call `curl http://localhost:8000/api/dashboard/teacher -H "Authorization: Bearer <student-token>"` → `403`.
- Rate limit: hammer login 11× quickly → 429 after the 10th.
- Storage failure: `GET /api/health/storage` while renaming `uploads/` away → 503.

## Run the automated end-to-end proof

```bash
# Terminal 1: uvicorn running as in Step 5
python scripts/smoke_test.py
# Expected final line: 17/17 smoke checks passed
```
