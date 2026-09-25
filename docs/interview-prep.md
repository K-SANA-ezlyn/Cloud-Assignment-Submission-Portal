# Interview Preparation — 10 Predicted Questions & Strong Answers

**Q1. "Explain your project."**

> I built a cloud-based assignment submission and feedback portal — a two-role
> system where students upload coursework and teachers review, grade, and give
> feedback. I deliberately designed it to demonstrate cloud computing concepts,
> not just CRUD. The three pillars: assignment files live in **object storage**
> as private objects accessed through short-lived signed URLs; all structured
> data — users, assignments, marks, feedback — lives in a **managed cloud
> database**; and a stateless **REST API** sits between them, enforcing
> authentication and role-based access on every route. The interesting design
> decision is a provider-abstraction layer: the same codebase runs fully
> offline with SQLite and a local uploads folder, or on free-tier cloud
> services with Supabase Postgres and Storage, by changing only environment
> variables. So "switching clouds" is configuration, not a rewrite. I also
> shipped 49 automated tests, a CI pipeline, health probes, and full
> deployment docs.

**Q2. Why store files in object storage instead of the database?**

> Databases are optimized for structured queries and transactions, not for
> streaming multi-megabyte binaries. If I stored PDFs as BLOBs, my database
> size and backup windows would grow unboundedly with file traffic, every
> download would flow through the DB process, and I'd lose the storage-tier
> features object stores give me for free — petabyte scale, lifecycle rules,
> CDN delivery, and signed-URL access control. So the database keeps only
> metadata — who submitted what, the storage key, status, marks — and the
> object store keeps bytes. The `storage_path` column is the deliberate join
> between those two worlds, and my download endpoint re-checks authorization
> before handing out any bytes or a 5-minute signed URL.

**Q3. How do authentication and authorization differ in your system?**

> Authentication answers *who are you* — that's my `/api/auth/login`: bcrypt
> verifies the password, then the server issues a signed JWT carrying the
> user id, role and expiry. Authorization answers *what may you do* — that's
> FastAPI dependencies: every route declares the roles it accepts, and beyond
> role checks I enforce row-level ownership, so a student can't read another
> student's submission even with a valid token — they get a 404 that doesn't
> leak existence. The key principle: the client never decides anything; the
> SPA hides teacher links, but the server would still reject the request.

**Q4. Why shouldn't you trust the client clock for deadlines? Give your design.**

> Because users control their devices — anyone can set their clock back to
> dodge a deadline. So deadline comparison happens only on the server with
> UTC `datetime.now`. Deadlines are stored in UTC, per assignment I have two
> policy flags — allow_late and allow_resubmission — and the server stamps
> submitted_at. On-time gives status SUBMITTED; late-with-permission gives
> LATE; late-without-permission gets a 409 before the file is even stored.
> The browser clock is used purely to render a friendly countdown.

**Q5. Walk me through your upload pipeline and its security checks.**

> First validation, then storage, then metadata — in that order, so failures
> never leave half-written state. Validation is three layers: extension
> whitelist, size cap compared before I touch storage — that returns 413, and
> magic-byte sniffing, so a virus renamed to .pdf is rejected with 415 because
> its bytes don't start with %PDF. Then the file goes to object storage under
> a collision-proof key — assignment id, student id, attempt number, a UUID
> — and only then do I write the metadata row. The bucket stays private;
> clients never get credentials; downloads flow through an authorized
> endpoint that returns bytes locally or a 300-second signed URL in cloud mode.

**Q6. What happens if object storage goes down mid-submission?**

> The upload call raises a StorageError, my global error handler converts it
> to a 503 with a retry-friendly message, and — because I upload before
> writing the database row — no submission metadata exists, so there's no
> phantom record and a retry is clean. It's the reverse order that's
> dangerous: a DB row pointing at bytes that never landed. I also expose
> /api/health/storage so monitoring catches the outage before users do. My
> test suite simulates exactly this with a broken provider and asserts the
> 503 and the empty submissions list.

**Q7. How would this architecture scale to 100,000 students uploading near a deadline?**

> The API is stateless and all heavy state is externalized, so I scale the
> web tier horizontally behind a load balancer with autoscaling — deadline
> storms are predictable, so you can schedule capacity ahead. Uploads are the
> bursty part; at scale I'd hand clients pre-signed PUT URLs so files go
> straight to object storage and my pods stay tiny. Dashboards become
> cache-friendly via Redis, and the database gets read replicas for all those
> teacher rosters. Slow side-effects — virus scanning, notifications — move
> behind a message queue with workers, so the user gets a fast 201 while work
> happens asynchronously. Object storage itself is effectively infinite, and
> the CDN keeps the SPA off my origin entirely.

**Q8. How is secrets management handled?**

> No secret lives in code or git history. Everything comes from environment
> variables through a pydantic-settings config object — which also validates
> types at startup. The repo contains only .env.example templates with
> placeholders, .env is gitignored, and on the cloud host — Render — secrets
> are set in the dashboard and injected at runtime. The Supabase service key
> is used strictly server-side; the browser only ever talks to my API.
> Rotating a key means updating one env var and redeploying — no code change.

**Q9. What does your CI/CD look like?**

> Every push runs GitHub Actions: pytest with a fresh test database and a
> disposable uploads folder for the backend, and a production Vite build for
> the frontend. If green, Render auto-deploys the API and Vercel the SPA
> from main — so main is always releasable. At runtime, three health
> endpoints — app, database, storage — report readiness; I point a free
> uptime monitor at them, and deployment logs plus my request-logging
> middleware give observability. The whole loop is: commit → tests → deploy
> → probe, with zero paid infrastructure.

**Q10. What's the weakest part of your project, and how would you fix it?**

> Three honest ones. First, JWT logout is stateless — the client discards the
> token but a stolen token is valid until expiry; the fix is short-lived
> access tokens plus refresh tokens with a server-side revocation list.
> Second, rate limiting is in-memory, which only works per-instance; at
> scale it moves to Redis or the API gateway. Third, file scanning is
> structural, not antivirus; production adds an async ClamAV stage — upload
> to quarantine, scan via a queued worker, promote to the private prefix when
> clean. All three fixes slot into seams the architecture already has —
> auth provider, middleware, and storage provider respectively.
