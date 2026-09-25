# Cloud Security

## 1. Controls implemented in this repository

| Control | Implementation |
|---|---|
| Password hashing | bcrypt via passlib (`cloud/auth_service.py`) — plaintext never stored/logged |
| Token auth | HS256 JWT with `exp`, `jti`, `iss`; 401 on missing/expired/tampered tokens |
| RBAC | `require_roles()` FastAPI dependencies; role enforced server-side on every route |
| Row-level authorization | `_get_authorized_submission()` — 404 (not 403) hides other users' resources |
| Invite-gated role assignment | teacher signup requires `TEACHER_INVITE_CODE` (roles are never client-chosen) |
| File-type validation | extension whitelist **+ magic-byte sniffing** (renamed `.exe` → `.pdf` rejected, TC test) |
| File-size validation | per-assignment cap, checked **before** storage write → 413 |
| Path safety | UUID-based object keys; local provider blocks `..` traversal escapes |
| Private storage | bucket/folder not publicly readable; downloads only via authorized endpoint / signed URL |
| Signed URLs | 300-second expiring links in cloud mode |
| CORS | explicit origin allowlist (`CORS_ORIGINS`) — no wildcard with credentials |
| Rate limiting | per-IP sliding window on auth endpoints → 429 |
| Input validation | Pydantic schemas on every request body; typed query/path params |
| Secrets management | only via environment variables; `.env` gitignored; no key in git history |
| Logging / audit trail | every request logged (method, path, status, latency); security denials logged with user + reason |
| Health probes | DB and storage readiness endpoints for monitoring |
| No user enumeration | login returns identical 401 for unknown email and wrong password |

## 2. Encryption

- **In transit**: HTTPS/TLS terminated at the hosting edge (Render/Vercel/Supabase all
  enforce TLS). Local development uses plain HTTP on loopback only.
- **At rest**: Supabase Postgres and Storage encrypt at rest by default (AES-256,
  provider-managed keys). Local mode: disk-level encryption is the OS's job (BitLocker).

## 3. Malware scanning (concept → production path)

Current validation is structural (magic bytes, size). A production system adds an
async scan stage: upload lands in a `quarantine/` prefix → SQS/Cloud Task triggers a
ClamAV scan function → clean objects are promoted to `submissions/`, infected ones
deleted + admins alerted. The provider-abstraction in `storage_service.py` is where
this hook would live.

## 4. Database & storage permissions

- Application connects with a **single least-privilege role** — not the provider's root/admin key.
- Supabase service key is used **only** server-side and is never shipped to the browser.
- Row-level security (Supabase RLS) can add a second defense layer; this API already
  enforces the same rules in application code and never exposes the DB to clients.

## 5. Common cloud-security mistakes (and how this project avoids them)

| Mistake | Avoided by |
|---|---|
| Committing `.env` / API keys | `.gitignore` + `.env.example` placeholders only |
| Trusting the client clock for deadlines | server UTC `datetime.now(timezone.utc)` only |
| Client-side-only authorization | every route re-checks role + ownership server-side |
| Serving uploads from a public static folder | uploads are never static; all access via authorized endpoint |
| `allow_origins=["*"]` with credentials | explicit origin allowlist |
| Storing plaintext passwords | bcrypt (salted, slow) |
| Unlimited upload sizes | per-assignment caps + validation before storage |
| Verbose errors leaking internals | generic messages; details only in server logs |

## 6. Hardening roadmap (beyond course scope)

- Refresh tokens + server-side revocation list (proper logout)
- WAF / bot protection in front of auth endpoints
- MFA for teacher accounts via the auth provider
- Structured audit log table (who graded what, when) with export
- Pre-signed direct uploads + post-upload verification scan
