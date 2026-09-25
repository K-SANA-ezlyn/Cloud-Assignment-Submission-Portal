# Cloud Deployment — Approach A (free tier) and Approach B (big-cloud mapping)

## Approach A — Student-friendly, 100% free tier (recommended)

Target: **API on Render · SPA on Vercel · DB+Storage+Auth on Supabase**.
No credit card anywhere.

### A.1 Supabase (database + storage, 10 minutes)

1. Create account → **New project** (free tier).
2. Save the DB password. Project Settings → Database → Connection string (URI, **pooler**, port 6543):
   `postgresql+psycopg2://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres`
3. Storage → **New private bucket** named `submissions` (no public access).
4. Project Settings → API: copy `Project URL`, `service_role` key (server-only!), `anon` key.

### A.2 Backend on Render (15 minutes)

1. Push this repo to GitHub.
2. Render → **New → Web Service** → connect the repo.
3. Settings:
   - Runtime: Python 3 · Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
4. Environment (from `.env.cloud.example`):
   `DATABASE_URL=<A.1 step 2>` · `STORAGE_PROVIDER=supabase` · `SUPABASE_URL=…` ·
   `SUPABASE_SERVICE_KEY=…` · `SUPABASE_STORAGE_BUCKET=submissions` ·
   `SECRET_KEY=<fresh random>` · `TEACHER_INVITE_CODE=<your own>` ·
   `CORS_ORIGINS=https://<your-app>.vercel.app` · `ENVIRONMENT=cloud`
5. Deploy → then run the schema bootstrap once via Render Shell:
   `python -c "import backend.models; from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"`
   (or temporarily add it to startup — `create_all` is idempotent).
6. Verify: `https://<service>.onrender.com/api/health` and `/api/health/db`, `/api/health/storage` → all 200.

### A.3 Frontend on Vercel (10 minutes)

1. Vercel → **Add New Project** → import the repo, **Root Directory: `frontend`**.
2. Build `npm run build`, output `dist`, and env var:
   `VITE_API_URL=https://<service>.onrender.com`
3. Deploy. Add the Vercel URL to Render's `CORS_ORIGINS` and redeploy the API once.

### A.4 Optional — Supabase Auth mode

Set `AUTH_PROVIDER=supabase`, `SUPABASE_ANON_KEY=…`. Login/register proxy to
Supabase Auth; JWTs are verified against the service key. Document the trade-offs
in your report (managed user lifecycle vs simple local JWTs).

### A.5 Monitoring

- Render log stream = your logging dashboard (errors, latency lines from the middleware).
- UptimeRobot free monitor on `/api/health` → uptime %. Expect cold starts on the
  free tier (first request after 15 idle minutes wakes the service — a live
  elasticity demonstration).

### A.6 CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs pytest + frontend build on every
push. Render and Vercel auto-deploy `main` on green — a complete push-to-production
pipeline with zero configuration cost.

---

## Approach B — Public-cloud architecture mapping

| Layer | AWS | Azure | GCP |
|---|---|---|---|
| CDN / edge | CloudFront | Front Door | Cloud CDN |
| Frontend hosting | S3 + CloudFront (OAC) | Static Web Apps | Firebase Hosting / Cloud Storage |
| API Gateway | API Gateway (HTTP API) | API Management | API Gateway |
| Backend compute | App Runner / Lambda + Fargate | Container Apps / Functions | Cloud Run / Cloud Functions |
| Database | RDS Postgres (Multi-AZ) / DynamoDB | Azure Database for PostgreSQL / Cosmos DB | Cloud SQL / Firestore |
| Object storage | S3 (private + signed URLs) | Blob Storage (SAS tokens) | Cloud Storage (signed URLs) |
| Auth | Cognito user pools | Entra External ID (B2C) | Firebase Auth / Identity Platform |
| Secrets | Secrets Manager / SSM Parameter Store | Key Vault | Secret Manager |
| Logs & monitoring | CloudWatch Logs/Alarms | Azure Monitor / App Insights | Cloud Logging / Monitoring |
| Queue + workers | SQS + Lambda workers | Service Bus + Functions | Pub/Sub + Cloud Run jobs |
| IaC | CloudFormation / CDK | Bicep | Terraform |

**Request path (AWS example)**: Route53 → CloudFront (SPA) → API Gateway
(throttling, JWT authorizer via Cognito) → App Runner (FastAPI) → S3 (files)
+ RDS (metadata) → CloudWatch (logs/alarms) → SQS (scan/notify workers).

This project maps 1-to-1 onto that topology: `storage_service.py` would gain an
`S3StorageProvider`, `auth_service.py` a Cognito verifier, and only env vars
would change — the whole point of the provider-abstraction design.

## Local development vs cloud deployment

| Aspect | Local mode | Cloud (Approach A) |
|---|---|---|
| Database | SQLite file | Supabase Postgres (backups, pooling) |
| Storage | `uploads/` folder | private bucket + signed URLs |
| Auth | own bcrypt+JWT | same code path (or Supabase Auth) |
| TLS | no (localhost) | automatic HTTPS |
| Scaling | 1 process | platform-managed instances |
| Cost | ₹0 / $0 | free tier |
| Failure demo | kill the process | service restarts, probes alert |

Same code, same endpoints, same tests — only the environment differs.
That portability *is* the cloud-native lesson of this project.
