# Cloud Object Storage Design

## 1. Database vs object storage — division of responsibility

| Stored in CLOUD DATABASE | Stored in OBJECT STORAGE |
|---|---|
| users, courses, enrollments | assignment PDFs / DOCX / PPTX |
| assignment definitions, deadlines | ZIP code bundles |
| submission metadata (who/when/status) | images, diagrams, datasets |
| marks, feedback, graded_at | any supporting documents |

## 2. Bucket / folder layout

```
submissions/
    {assignment_id}/
        {student_id}/
            1_3f9c2a41_lab1-report.pdf
            2_7b81de05_lab1-report-final.pdf   ← resubmission, attempt 2
```

- **Grouping by assignment** mirrors the teacher's review mental model.
- **Per-student prefix** keeps each learner's attempts together.
- **`attempt_no` + 8-char UUID + safe filename** — collisions impossible,
  overwrite risk zero, humans can still eyeball what a file is.
- The full key is stored in `submissions.storage_path` — the DB is the
  source of truth mapping a submission to its object.

## 3. Upload flow (server-side only)

```
client → POST /api/assignments/{id}/submit (multipart)
       → validated (ext / size / magic bytes)
       → StorageProvider.upload(bytes, key)      ← private write with server credentials
       → INSERT/UPDATE submissions metadata row
```

Clients **never** receive storage credentials and never talk to the bucket
directly. In a scaled variant you would issue pre-signed PUT URLs to upload
straight from the browser — the server still performs validation and
metadata write (documented trade-off in security.md).

## 4. Download flow — private by default

```
client → GET /api/submissions/{id}/download   (Bearer token)
       → authorization check (owner student or course teacher)
       → local mode:  stream bytes through the API
         cloud mode:  300-second signed URL → browser downloads directly
```

There is **no public URL** for any submission. Signed URLs expire; leaking
one exposes the file only briefly. Anonymous requests get 401 before any
storage interaction.

## 5. Operations

| Operation | Local provider | Supabase provider |
|---|---|---|
| Upload | write file under `uploads/` (path-traversal-guarded) | POST to bucket with service key |
| Download | read file | GET object (or signed URL) |
| Delete | unlink (used on resubmission) | DELETE object (best effort) |
| Health | write/delete probe file | upload/delete probe object |
| Failure mode | `StorageError` → HTTP 503 | `StorageError` → HTTP 503 |

## 6. Access-permission matrix

| Principal | Read object | Write object | Delete object |
|---|---|---|---|
| Anonymous | ✗ (401) | ✗ | ✗ |
| Student (other's file) | ✗ (404) | ✗ | ✗ |
| Student (own file) | ✓ via API | ✓ (submit endpoint only) | ✗ (server-managed) |
| Teacher (own course) | ✓ via API | ✗ | ✗ |
| Backend (service key) | ✓ | ✓ | ✓ |

## 7. Retention & lifecycle (design notes)

- Resubmission deletes the previous object → storage only keeps the latest attempt.
- In production, add lifecycle rules (e.g. expire `submissions/` objects 12 months
  after grading) and versioning for audit if required by policy.
