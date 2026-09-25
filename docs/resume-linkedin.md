# Resume / LinkedIn Proof Pack

## A. Three strong resume bullet points

- Architected a cloud-based assignment submission portal (FastAPI + React) with
  a **provider-abstraction layer** enabling one codebase to run on SQLite/local
  storage or **Supabase Postgres + object storage** via environment variables
  only, demonstrating cloud portability and 12-factor design.
- Implemented **role-based access control**, JWT authentication with bcrypt,
  private object storage with signed-URL downloads, and server-side deadline
  enforcement; validated uploads via extension, size and **magic-byte
  inspection**, reducing common cloud-security misconfigurations to zero by design.
- Shipped **49 automated pytest cases**, a 17-check live smoke suite and a
  GitHub Actions CI/CD pipeline; deployed the stack on free-tier cloud services
  (Render, Vercel, Supabase) with health probes, request logging and monitoring.

## B. Two-line resume project description

> Cloud-Based Student Assignment Submission & Feedback Portal — a cloud-native
> web application demonstrating object storage, managed cloud databases,
> role-based security, scalable stateless architecture, and CI/CD deployment,
> built and tested entirely on free-tier services.

## C. LinkedIn project description

☁️ **Cloud-Based Student Assignment Submission & Feedback Portal**

As my Cloud Computing course project, I built and deployed a full platform
where students submit assignments and teachers review, grade, and return
feedback — designed from day one to demonstrate real cloud architecture:

🔹 **Object storage** for assignment files (private bucket + time-limited
signed URLs) — never blobs in the database
🔹 **Managed cloud database** for users, assignments, marks and feedback
🔹 **Role-based access control** — students, teachers, and invite-gated role
assignment, enforced server-side on every API route
🔹 **A provider-abstraction layer**: the same codebase runs offline
(SQLite + local storage) or on **Supabase cloud (free tier)** by changing
environment variables — vendor portability by design
🔹 **Server-side deadline logic** with configurable late/resubmission policies
🔹 **Security**: bcrypt + JWT, upload validation (type/size/magic bytes),
CORS allowlist, rate limiting, secrets via environment variables
🔹 **DevOps**: 49 automated tests, live smoke suite, GitHub Actions CI/CD,
health probes, logging and free-tier deployment (Render + Vercel + Supabase)

The biggest lesson: cloud computing is an *architecture discipline* —
stateless services, externalized state, least-privilege access and observable
operations — not just "where the server lives."

#CloudComputing #FastAPI #React #Supabase #ObjectStorage #RBAC #CI/CD #EdTech

## D. Technical skills demonstrated

| Area | Evidence in project |
|---|---|
| Cloud service models (SaaS/PaaS/IaaS) | portal delivery; Render/Vercel/Supabase; IaaS mappings |
| Cloud storage | private buckets, signed URLs, storage-path design |
| Cloud databases | SQLite→Postgres portability, connection pooling, health probes |
| Authentication | bcrypt, JWT claims/expiry, auth-provider abstraction |
| Authorization / RBAC | dependency-based roles, row-level ownership checks |
| REST API design | 21 documented endpoints, precise status-code contracts |
| Secure uploads | whitelist + magic bytes + size caps, path-traversal guards |
| Scalability & elasticity | stateless design, autoscaling/queue/cache architecture docs |
| Reliability | storage-first transactions, retries, idempotency, graceful 5xx |
| Observability | logging middleware, health/readiness endpoints |
| CI/CD | GitHub Actions (tests + build), push-to-deploy hosting |
| Configuration & secrets | env-driven settings, template files, no secrets in VCS |
| Testing | pytest suite, live E2E smoke tests, manual matrix |
| Frontend engineering | React SPA, role-aware routing, guarded routes |
| Technical writing | architecture/API/security docs, report, runbooks |

## E. GitHub project description

**Repository**: `Cloud-Assignment-Submission-Portal`
**About**: "Cloud-based student assignment submission and feedback platform
featuring role-based authentication, cloud database integration, object
storage, assignment management, secure file submission, grading, and feedback
workflows."
**Topics**: `cloud-computing` `edtech` `python` `fastapi` `react`
`cloud-storage` `supabase` `database` `rest-api` `full-stack`
`authentication` `rbac`
