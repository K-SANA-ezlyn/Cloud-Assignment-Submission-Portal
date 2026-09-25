# Scalability — 10 → 1,000 → 100,000 Students

## Why this architecture scales at all

Two decisions make every later step possible:

1. **Stateless API** — no sessions stored in the process; any instance can serve
   any request (state lives in the DB, storage, and the client's JWT).
2. **Externalized heavy state** — bytes in object storage, structured data in a
   managed database. The app tier is small, dumb, and horizontally cloneable.

---

## 10 students (classroom)

- **Running**: 1 API instance + SQLite/local storage is already sufficient.
- **Bottleneck**: none. Latency dominated by bcrypt (~100 ms) at login.
- **Cloud shape**: still fine on a free PaaS tier; DB is the only piece worth
  managed-hosting for durability.

## 1,000 students (department)

| Pressure point | Answer |
|---|---|
| SQLite concurrency | move to **managed Postgres** (Supabase/RDS) with connection pooling (PgBouncer / Supabase pooler) |
| Single-instance limits | **2+ API replicas behind a load balancer** (Render autoscaling, ECS, App Runner) |
| Slow dashboard aggregates | add **cache** (Redis) for dashboard counts with 30–60 s TTL |
| Upload bursts | keep request small; object storage absorbs the bytes |
| Static assets | CDN already in front of the SPA |

Approximate load: 1,000 students × (5 requests + 1 upload) per week — trivial
for 2 small instances; the real work is in the DB, which Postgres handles
without breaking a sweat at this scale.

## 100,000 students (university-wide / deadline crunch)

**The scenario**: 100,000 students, 20% upload in the final hour before a
shared deadline → ~5,500 uploads/minute, plus thousands of status refreshes.

```
                 ┌──────────── CDN (SPA assets, no API traffic) ────────────┐
 100k browsers ──┤                                                           │
                 └──► Load balancer ──► N × API pods (HPA: CPU + RPS)
                          │                      │
                          │                      ├──► Managed Postgres
                          │                      │     (read replicas for dashboards,
                          │                      │      PgBouncer, partitioned tables)
                          │                      └──► Object storage (S3 class)
                          │                            (multi-part uploads, unbounded)
                          └──► Redis (rate limits, session-less cache, queues)
                          └──► SQS/Cloud Tasks ──► workers (post-upload AV scan,
                                                     notifications, grading exports)
```

| Mechanism | Role in the crunch |
|---|---|
| **Load balancer + autoscaling** | pods scale 4 → 60 on RPS; deadline storms are predictable (cron-scaled ahead of known deadlines) |
| **Serverless functions** | upload-adjacent tasks (validation, thumbnails, scan) burst to zero-to-thousands without managing pods |
| **Managed DB** | vertical headroom + read replicas for dashboards; writes partitioned by assignment |
| **Object storage** | effectively infinite; multi-part upload handles large files on flaky links |
| **CDN** | serves the SPA so user-side latency stays low even when APIs are busy |
| **Caching** | dashboard counts from Redis; submission status via ETag/If-None-Match |
| **Message queues** | decouple "accept upload" (fast 201) from slow work (scan, email "graded" notifications) |
| **Background workers** | deadline sweepers mark windows closed; retry queues for failed storage ops |
| **Backpressure** | pre-signed direct-to-storage uploads keep API pods tiny under burst |

**Result**: uploads stay seconds-fast; the expensive parts are asynchronous.
Cost scales with usage (scale-to-zero between terms), which is precisely the
cloud economic argument.

---

## Load-balancing & autoscaling summary

| Tier | 10 | 1,000 | 100,000 |
|---|---|---|---|
| App instances | 1 | 2–4 | 10s–100s (HPA) |
| Database | SQLite | managed Postgres, 1 primary | primary + replicas, partitioning |
| Storage | local disk | single bucket | bucket + lifecycle + multipart |
| Caching | — | Redis (dashboards) | Redis everywhere + CDN |
| Async | — | — | queues + workers |
| Deploy shape | PaaS free tier | PaaS standard | k8s / serverless hybrid |
