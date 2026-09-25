# Database Design

## 1. Entity-Relationship diagram

```mermaid
erDiagram
    USERS ||--o{ COURSES : "owns (teacher)"
    USERS ||--o{ ENROLLMENTS : "enrolls (student)"
    COURSES ||--o{ ENROLLMENTS : "has"
    COURSES ||--o{ ASSIGNMENTS : "contains"
    USERS ||--o{ SUBMISSIONS : "uploads (student)"
    ASSIGNMENTS ||--o{ SUBMISSIONS : "receives"
    USERS ||--o{ SUBMISSIONS : "grades (teacher)"

    USERS {
        string id PK "UUID(36)"
        string name "varchar 120"
        string email UK "varchar 255, unique+index"
        string password_hash "bcrypt, nullable (provider auth)"
        enum  role "STUDENT | TEACHER"
        datetime created_at "UTC"
    }
    COURSES {
        string id PK
        string name "varchar 150"
        string teacher_id FK "→ users.id"
        datetime created_at
    }
    ENROLLMENTS {
        string id PK
        string course_id FK "→ courses.id"
        string student_id FK "→ users.id"
    }
    ASSIGNMENTS {
        string id PK
        string course_id FK "→ courses.id"
        string title "varchar 200"
        text   description
        datetime deadline "UTC"
        int    max_marks "1..1000"
        string allowed_extensions "csv e.g. pdf,zip"
        int    max_file_size_mb
        bool   allow_resubmission
        bool   allow_late
        string created_by FK "→ users.id"
        datetime created_at
    }
    SUBMISSIONS {
        string id PK
        string assignment_id FK "→ assignments.id"
        string student_id FK "→ users.id"
        string file_name "original name"
        string storage_path "object key in bucket"
        int    file_size "bytes"
        string mime_type
        int    attempt_no "1..n"
        datetime submitted_at "UTC"
        enum   status "SUBMITTED | LATE | GRADED"
        int    marks "nullable"
        text   feedback "nullable"
        datetime graded_at "nullable"
        string graded_by FK "→ users.id"
    }
```

## 2. Keys and relationships

- **Primary keys** — UUID strings (36 chars): globally unique, safe in URLs and
  object-storage keys, no auto-increment leakage of business volume.
- **Foreign keys** — `courses.teacher_id → users.id`, `enrollments.course_id/student_id`,
  `assignments.course_id/created_by`, `submissions.assignment_id/student_id/graded_by`.
- **Relationship chain**: `Teacher → Course → Assignment → Submission ← Student`
  (and `Teacher grades Submission`). Many-to-many student↔course resolved via `enrollments`.
- **Uniqueness constraints** — `users.email` (unique index), `enrollments(course_id, student_id)`,
  `submissions(assignment_id, student_id)` — the latter makes "one live submission per
  student per assignment" a *database guarantee*, not just application logic.

## 3. Indexing strategy

| Index | Query it serves |
|---|---|
| `users.email` (unique) | login lookup by email |
| `courses.teacher_id` | teacher's course list |
| `enrollments.course_id` / `enrollments.student_id` | class rosters, student's courses |
| `assignments.course_id` | assignment lists per course |
| `submissions.assignment_id` | teacher's review roster |
| `submissions.student_id` | "my submissions" |
| composite `(assignment_id, student_id)` (unique) | resubmission lookup, status checks |

All FK columns are indexed (declared in the models), so every dashboard
aggregate and authorization check is an index-backed lookup.

## 4. Why files are NOT stored in the database

| Storing files as BLOBs | Storing files in object storage |
|---|---|
| Bloats DB files → backups grow unbounded | DB stays small, backup fast |
| Streaming a 10 MB file loads it through the DB process | storage serves bytes directly, signed URLs, CDN-able |
| Expensive DB IOPS/memory for binary I/O | cheap, durable, massively parallel object store |
| Hard to serve with proper content headers/range requests | native download semantics |

**Rule implemented**: DB stores *metadata* (who, what, where, when, status,
marks, feedback); object storage stores *bytes*. `submissions.storage_path`
is the join between the two worlds.

## 5. Cloud database queries (examples)

```sql
-- student dashboard: pending count
SELECT COUNT(*) FROM assignments a
JOIN enrollments e ON e.course_id = a.course_id
LEFT JOIN submissions s ON s.assignment_id = a.id AND s.student_id = :me
WHERE e.student_id = :me AND s.id IS NULL;

-- teacher roster for grading
SELECT s.*, u.name AS student_name
FROM submissions s JOIN users u ON u.id = s.student_id
JOIN assignments a ON a.id = s.assignment_id
JOIN courses c ON c.id = a.course_id
WHERE c.teacher_id = :teacher AND a.id = :assignment;

-- deadline sweep (background worker in production)
SELECT id FROM assignments WHERE deadline < now() AND allow_late = false;
```

The ORM (SQLAlchemy 2.0) emits equivalent queries; switching from SQLite to
Supabase Postgres changes **zero** application code — only `DATABASE_URL`.

## 6. NOT_SUBMITTED is computed, never stored

A row exists only after an upload. "Not submitted" is derived by comparing
assignments against existing submission rows (LEFT JOIN pattern above).
This avoids a synchronization problem entirely: there is no stale flag to
update when an assignment is created or a student enrolls late.
