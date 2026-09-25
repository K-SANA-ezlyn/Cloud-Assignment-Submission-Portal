# System Architecture

## 1. Logical architecture (this repository)

```
STUDENT / TEACHER  (browser)
        │  HTTPS + JWT Bearer token
        ▼
React SPA (Vite)                       frontend/
        │  JSON + multipart/form-data
        ▼
FastAPI REST API                       backend/app.py
   ├── CORS allowlist                  (browser security)
   ├── Request logging middleware      (observability / audit trail)
   ├── Rate-limit middleware           (brute-force / abuse protection)
   ├── Error handlers                  (415 / 409 / 413 / 503 contracts)
   ├── RBAC dependencies               backend/utils/security.py
   ├── Business routes                 backend/routes/*.py
   │      │
   │      ├── cloud/database_service.py ── SQLAlchemy ORM ──► DATABASE
   │          (SQLite local  |  Supabase Postgres cloud)
   │
   │      └── cloud/storage_service.py  ── StorageProvider ──► OBJECT STORAGE
   │          (uploads/ folder  |  Supabase Storage private bucket)
   │
   └── Health probes  /api/health, /api/health/db, /api/health/storage
```

## 2. Provider abstraction — one codebase, two clouds

```
                    ┌────────────────────────────┐
                    │   application code (same)   │
                    └─────────────┬──────────────┘
              STORAGE_PROVIDER=   │   DATABASE_URL=
              ┌───────────────────┴────────────────────┐
              ▼                                        ▼
     LOCAL MODE                                CLOUD MODE
   sqlite:///./portal.db          postgresql+psycopg2://…supabase…
   uploads/ folder                Supabase Storage private bucket
   bcrypt + own JWT               (optional) Supabase Auth JWT verify
```

Only environment variables change. No business module imports a vendor SDK
directly — `storage_service.py` is the only place that knows about Supabase.

## 3. Complete request/data flows

### 3.1 Student submits an assignment

```
1. Browser  POST /api/assignments/{id}/submit  (multipart, Bearer token)
2. CORS check → rate-limit check → JWT verified → role=STUDENT checked
3. Assignment fetched; enrollment verified (visibility rule)
4. Deadline gate:  now > deadline and not allow_late  → 409
5. Resubmission policy checked (attempt counter, GRADED lock)
6. File validated: extension whitelist → size cap → magic-byte sniff
7. StorageProvider.upload(bytes, submissions/{a}/{s}/{n}_{uuid}_{name})
8. Metadata row upserted in DB with status SUBMITTED or LATE (server UTC now)
9. 201 Created returned; SPA shows confirmation + refreshes status
```

### 3.2 Teacher grades

```
1. GET /api/assignments/{id}/submissions   (teacher of the course only)
2. GET /api/submissions/{sid}/download     (bytes stream, role-checked)
3. POST /api/submissions/{sid}/grade       marks ≤ max_marks enforced
4. Row updated: marks, feedback, graded_at, graded_by, status=GRADED
5. Student's dashboard + feedback endpoint instantly reflect it
```

### 3.3 Failure flow (storage outage)

```
upload → StorageError → error handler → 503 + "retry later"
       → transactional guarantee: NO metadata row is written
```

## 4. Advanced cloud architecture (free-tier deployment)

```
Users
  ▼
CDN / edge          (Vercel edge network serves the SPA assets)
  ▼
Static hosting      (Vercel — frontend build output)
  ▼
API Gateway role    (Render proxy: TLS termination, routing)
  ▼
FastAPI on Render   (container; scale-to-zero after idle = elasticity demo)
  ▼
Managed Postgres    (Supabase, pooled connections)   Object Storage (Supabase)
  ▼
Logs & monitoring   (Render log stream + UptimeRobot heartbeat)
```

## 5. Production-grade equivalent (AWS reference)

```
Route53 → CloudFront (CDN) → S3 static SPA
        → API Gateway (auth, throttling) → Lambda / App Runner (FastAPI)
        → RDS Postgres (Multi-AZ) / DynamoDB
        → S3 private bucket + signed URLs
        → Cognito user pools (JWT)
        → CloudWatch logs/alarms; SQS + workers for async pipelines
```

Azure and GCP mappings are in `cloud-deployment.md`.
