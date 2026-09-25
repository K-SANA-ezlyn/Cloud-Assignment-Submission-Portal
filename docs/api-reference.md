# REST API Reference

Base URL (dev): `http://localhost:8000` · Interactive docs: `/docs` (Swagger) · Schema: `/openapi.json`

All protected endpoints require header `Authorization: Bearer <access_token>`.
Errors are JSON: `{"detail": "..."}`. Common codes: **400** bad request · **401** unauthenticated · **403** wrong role/forbidden · **404** not found or not yours · **409** conflict · **413** file too large · **415** unsupported file type · **422** validation error · **429** rate limited · **500** server error · **503** storage/database down.

---

## AUTH

### POST /api/auth/register — create an account
- **Auth**: none. **Rate limit**: 10/min/IP.
- **Request**: `{"name": "Sana", "email": "sana@edu.dev", "password": "min8chars", "role": "STUDENT"|"TEACHER", "invite_code": "required if TEACHER"}`
- **201**: `UserOut` — `{id, name, email, role, created_at}`
- **Errors**: 409 email exists · 403 teacher without/with bad invite code · 422 validation.

### POST /api/auth/login — exchange credentials for a token
- **Auth**: none. **Rate limit**: 10/min/IP.
- **Request**: `{"email": "...", "password": "..."}`
- **200**: `{"access_token": "<jwt>", "token_type": "bearer", "user": UserOut}`
- **Errors**: 401 invalid credentials (same message for unknown email & wrong password — no user enumeration).

### POST /api/auth/logout — stateless logout
- **Auth**: Bearer. **200**: `{"detail": "Logged out..."}`. Client discards the token.

### GET /api/auth/me — who am I
- **Auth**: Bearer. **200**: `UserOut`. **Errors**: 401 missing/expired/invalid token.

---

## COURSES

### POST /api/courses — create course (TEACHER)
- **Request**: `{"name": "Cloud Computing (CS-402)"}` · **201**: CourseOut `{id, name, teacher_id, created_at, student_count, assignment_count}`
- **Errors**: 403 student.

### GET /api/courses — list my courses
- **Auth**: any. Teachers get their courses; students get their enrollments. **200**: `[CourseOut]`

### POST /api/courses/{course_id}/enroll — enroll a student (TEACHER, owner)
- **Request**: `{"student_email": "s@edu.dev"}` · **200**: CourseOut
- **Errors**: 404 course not yours / student missing · 400 user not a student · 409 already enrolled.

---

## ASSIGNMENTS

### POST /api/assignments — create (TEACHER, course owner)
- **Request**:
```json
{
  "course_id": "uuid",
  "title": "Lab 1 — Object Storage",
  "description": "…",
  "deadline": "2026-10-05T18:00:00Z",
  "max_marks": 20,
  "allowed_extensions": "pdf,zip",
  "max_file_size_mb": 10,
  "allow_resubmission": true,
  "allow_late": false
}
```
- **201**: AssignmentOut (includes `submitted_count`; for students also `my_status/my_marks/my_feedback`).
- **Errors**: 403 student · 404 course not found/not yours · 422 validation.

### GET /api/assignments — role-aware list
- Teacher: across their courses · Student: courses they are enrolled in. **200**: `[AssignmentOut]`

### GET /api/assignments/{id} — detail (must be visible to you)
- **200**: AssignmentOut with embedded `my_status` for students.
- **Errors**: 404 not found / not enrolled / not your course.

### PUT /api/assignments/{id} — partial update (TEACHER, owner)
- Any subset of create fields. **200**: AssignmentOut. **Errors**: 403/404.

### DELETE /api/assignments/{id} — delete + cascade submissions (TEACHER, owner)
- **200**: `{"detail": "Assignment deleted", "id": "..."}`.

---

## SUBMISSIONS

### POST /api/assignments/{id}/submit — upload (STUDENT, enrolled)
- **Content-Type**: `multipart/form-data`, field `file`.
- **Server pipeline**: authn → role → enrollment → deadline (`allow_late` decides 409 vs LATE) → resubmission policy → extension + size + magic-byte validation → storage upload → metadata row.
- **201**: SubmissionOut `{id, assignment_id, student_id, student_name, file_name, file_size, mime_type, attempt_no, submitted_at, status: SUBMITTED|LATE|GRADED, marks, feedback, graded_at}`
- **Errors**: 403 non-student · 404 not found/not enrolled · 409 deadline passed & late disabled / resubmission blocked / graded lock · 413 too large · 415 type/content mismatch · 503 storage outage (no metadata written).

### GET /api/submissions/me — my history (STUDENT)
- **200**: `[SubmissionOut]` — only the caller's rows, newest first.

### GET /api/assignments/{id}/submissions — roster (TEACHER, owner)
- **200**: `[SubmissionOut]` with `student_name`.

### GET /api/submissions/{id} — one submission
- Student: own only · Teacher: own-course only. **Errors**: 404 otherwise.

### GET /api/submissions/{id}/download — secure file retrieval
- Local mode: streams bytes (`Content-Disposition: attachment`). Supabase mode: returns `{"download_url": "<signed-url, 300s>"}`.
- **Errors**: 401 anonymous · 404 not yours/not your course · 503 storage failure.

---

## GRADING & FEEDBACK

### POST /api/submissions/{id}/grade — marks + feedback (TEACHER, owner)
- **Request**: `{"marks": 18, "feedback": "Strong analysis; cite the storage classes."}`
- **200**: SubmissionOut with `status=GRADED`, `graded_at`, `graded_by`.
- **Errors**: 400 marks > max_marks or negative · 403 student/self-grade · 404 not your course.

### GET /api/submissions/{id}/feedback — read feedback
- Student (own) or course teacher. **200**: `{submission_id, marks, max_marks, feedback, graded_at, graded_by_name}`.

---

## DASHBOARDS

### GET /api/dashboard/student (STUDENT)
**200**:
```json
{
  "welcome_name": "Sana", "total_assignments": 4, "pending": 2,
  "submitted": 1, "late": 0, "graded": 1,
  "upcoming_deadlines": [{"assignment_id": "…", "title": "…", "course": "…", "deadline": "…", "max_marks": 20}],
  "recent_feedback": [{"submission_id": "…", "assignment_title": "…", "marks": 18, "feedback": "…", "graded_at": "…"}]
}
```

### GET /api/dashboard/teacher (TEACHER)
**200**:
```json
{
  "welcome_name": "Dr. Ada", "total_assignments": 4, "total_students": 6,
  "total_submissions": 12, "pending_reviews": 7, "late_submissions": 2, "graded_submissions": 5,
  "recent_uploads": [{"submission_id": "…", "assignment_title": "…", "student_name": "…", "file_name": "…", "status": "SUBMITTED", "submitted_at": "…"}],
  "upcoming_deadlines": [{"assignment_id": "…", "title": "…", "course": "…", "deadline": "…", "submitted_count": 3}]
}
```
**Errors**: 403 wrong role · 401 anonymous.

---

## HEALTH

| Endpoint | Purpose | 200 when | 503 when |
|---|---|---|---|
| `GET /api/health` | liveness | always (process up) | — |
| `GET /api/health/db` | database readiness | `SELECT 1` works | DB unreachable |
| `GET /api/health/storage` | storage readiness | write+delete probe OK | storage outage |
