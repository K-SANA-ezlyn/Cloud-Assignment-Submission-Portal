# Cloud Computing Concepts — Where Each One Lives in This Project

Every claim below maps to a concrete file, endpoint, or observable behavior —
use the "how to demo" column when presenting the project.

| # | Concept | Where it appears | How to demo / evidence |
|---|---------|------------------|------------------------|
| 1 | **Cloud-hosted application** | Deployed API (Render) + SPA (Vercel) — `docs/cloud-deployment.md` | open the public HTTPS URL from any device |
| 2 | **SaaS** | The portal itself: users consume a finished app over the internet, nothing installed locally | log in from any browser; no setup |
| 3 | **PaaS** | Render runs the FastAPI container without us managing the OS/runtime | push to GitHub → auto-deploy dashboard |
| 4 | **IaaS concepts** | Your laptop in local mode plays the "infrastructure" role; the docs map it to VMs/EC2 | compare local vs cloud run of same image/code |
| 5 | **Cloud database (DBaaS)** | `DATABASE_URL` swap: SQLite locally ⇄ Supabase Postgres free tier | `GET /api/health/db` in both modes |
| 6 | **Object storage** | `backend/cloud/storage_service.py` — uploads/ folder ⇄ Supabase Storage private bucket | upload a file, inspect `storage_path` in DB |
| 7 | **Authentication** | `backend/cloud/auth_service.py` — bcrypt + JWT (local) / Supabase Auth (cloud) | login issues token; `/api/auth/me` validates it |
| 8 | **Authorization / RBAC** | `backend/utils/security.py` — `require_roles()` dependencies on every route | student token on teacher endpoint → 403 |
| 9 | **REST API** | 21 endpoints under `/api/*` — `docs/api-reference.md` | show FastAPI docs UI at `/docs` |
| 10 | **Client–server architecture** | React SPA (client) ⇄ FastAPI (server), stateless JSON over HTTP | two browsers, one server, same data |
| 11 | **Serverless (concept + readiness)** | Business logic is stateless & container-ready; deploy path to Lambda/Cloud Run documented | `docs/cloud-deployment.md` Approach B |
| 12 | **Scalability** | Stateless API + externalized state (DB/storage) → horizontal scaling | `docs/scalability.md` 10 → 100k analysis |
| 13 | **Elasticity** | Render free tier scale-to-zero / scale-out; autoscaling mapping in docs | idle service spins down, wakes on request |
| 14 | **Availability** | Managed Postgres (daily backups), stateless replicas, health probes | kill one instance → another serves |
| 15 | **Load balancing (concept)** | Render/Vercel edge routing in front of instances; mapping to LB + ASG in docs | architecture diagram in `architecture.md` |
| 16 | **CDN** | Vercel/CloudFront serving static SPA from edge locations | `curl -I` shows edge cache headers |
| 17 | **API Gateway (role)** | Rate-limit middleware + CORS + TLS proxy mirror gateway behavior | send 15 logins/min → 429 |
| 18 | **Environment variables** | `backend/config.py` (pydantic-settings), `.env.example` templates | grep repo: no secrets in code |
| 19 | **Secrets management** | `.env` gitignored; provider dashboard secrets on Render/Supabase | `git log -p` shows no key ever committed |
| 20 | **Logging** | `logging_middleware.py` — method, path, status, latency per request | read the uvicorn/Render log stream |
| 21 | **Monitoring** | `/api/health`, `/api/health/db`, `/api/health/storage` + UptimeRobot | probe returns 503 when DB is down |
| 22 | **Backup** | SQLite file copy locally; Supabase daily backups in cloud mode | restore a `.db` file; dashboard evidence |
| 23 | **CI/CD** | `.github/workflows/ci.yml` — pytest + frontend build on every push | green checks on GitHub commits |
| 24 | **Cloud deployment** | Approach A (Render + Vercel + Supabase) and AWS/Azure/GCP mapping | live URL + deployment dashboard screenshot |
| 25 | **Rate limiting** | `middleware/rate_limit.py` per-IP sliding window on auth routes | hammer `/api/auth/login` → HTTP 429 |
| 26 | **Encryption in transit** | HTTPS/TLS everywhere on cloud hosting; localhost dev exception | browser padlock on deployed URL |
| 27 | **Signed URLs (private storage)** | Supabase `create_signed_url()` — 300 s expiring links | anonymous bucket URL → 400/404 |
| 28 | **Idempotency & transactions** | Storage-first-then-DB ordering; unique constraint on (assignment, student) | storage failure leaves no orphan metadata row |

## Service-model summary

- **SaaS delivered**: the working portal for end users.
- **PaaS consumed**: Render (API hosting), Vercel (frontend hosting), Supabase (DB+storage+auth).
- **IaaS understanding**: the docs map every managed piece back to its raw IaaS equivalent (VMs, disks, networks), and local mode simulates owning the infrastructure yourself.
