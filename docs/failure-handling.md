# Failure Handling — What Breaks, What the User Sees, How It Recovers

Design principle: **fail loudly to the log, gracefully to the user, and never
leave the system in a half-written state.**

## 1. Failure catalogue

| Failure | Detected by | User sees | System behavior / recovery |
|---|---|---|---|
| **File upload fails (validation)** | `validate_file` | 415/413 with a plain-language reason | nothing written — no object, no DB row; student fixes the file |
| **Object storage outage** | `StorageError` → handler | 503 "Storage service unavailable, retry" | metadata row is **not** created (storage-first ordering); retry works when storage returns; logged as ERROR |
| **Database unavailable** | SQLAlchemy errors / health probe | 500 on writes, `/api/health/db` → 503 | app stays up for probes; on reconnect, `pool_pre_ping` revalidates connections automatically |
| **Auth token expired** | JWT `exp` check → 401 | SPA redirects to `/login?expired=1` with a notice | user re-authenticates; no data lost (forms keep state client-side) |
| **Duplicate submission request** | unique `(assignment_id, student_id)` + resubmission policy | first request 201; duplicates become resubmission (202-style update) or 409 | DB constraint is the arbiter; attempt counter increments; no double rows |
| **Internet drops mid-upload** | browser fetch rejects | "Cannot reach the server…" banner | server either received nothing (clean) or the request timed out before commit — client simply retries; resubmission policy governs |
| **Backend process crash** | hosting platform health checks | brief 5xx / connection reset | platform restarts the container (Render auto-heal); state is external (DB/storage) so nothing is lost |
| **Signed URL expired** | provider 400/403 on direct URL | user clicks download again → fresh URL | 5-minute TTL bounds the exposure window |

## 2. Transactional workflow (upload consistency)

```
1. validate file            (pure function — no side effects)
2. upload to storage        (idempotent-ish: unique key per attempt)
3. write metadata row       (only reached if 2 succeeded)
```

If step 2 fails → no row (clean retry).
If step 3 fails after a successful 2 → an orphaned object exists but is
unreachable through the API and is garbage-collected by lifecycle rules;
**the user-visible state stays correct** (no phantom submission). Reversing
the order would be worse: a DB row pointing at a file that was never stored.

## 3. Retry strategy

| Operation | Retry? | Policy |
|---|---|---|
| GET requests (idempotent) | yes, automatically in the SPA (future) | 2 retries, exponential backoff 0.5 s → 1 s |
| Upload (POST) | only **after** failure response | user-triggered; new attempt governed by resubmission rules |
| Login | user-triggered | rate-limited server-side (429) to prevent hammering |
| Storage internal ops | yes for read probes | 1 retry, then fail to 503 |

Client rule of thumb taught by this project: **auto-retry only idempotent
reads; make writes explicit and policy-checked.**

## 4. Idempotency

- **Natural keys**: one live submission per `(assignment, student)` enforced by
  a DB unique constraint — the strongest possible idempotency guard.
- **Resubmission = upsert**: the row is updated in place (attempt_no+1) rather
  than duplicated.
- **Idempotency-key header** (production extension): accept `Idempotency-Key`
  on POST submit and return the stored response for replays within 24 h —
  standard pattern for flaky mobile networks.

## 5. Graceful degradation ladder

| Severity | Behavior |
|---|---|
| Storage down | submissions pause; browsing/grading of existing work continues (grading needs no new uploads) |
| DB down | full 5xx on dynamic routes; static SPA still loads; probes alert ops |
| One API pod down | LB drains it; other replicas absorb (stateless) |
| CDN down | SPA unreachable via edge; API stays healthy; direct origin fallback |
