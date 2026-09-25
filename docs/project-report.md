# Project Report — Cloud-Based Student Assignment Submission & Feedback Portal

## Abstract
This project designs, implements, tests and deploys a cloud-based portal for
student assignment submission and teacher feedback. The system separates
unstructured content (assignment files) in cloud object storage from structured
state (users, assignments, marks, feedback) in a managed cloud database, and
exposes both through a stateless REST API guarded by role-based access control.
A provider-abstraction layer lets the identical codebase run entirely offline
(SQLite + local disk) or on free-tier cloud services (Supabase Postgres +
Storage) by changing environment variables only. The system implements
deadline enforcement from server-side clocks, configurable late and
resubmission policies, secure upload validation (extension, size, magic
bytes), signed-URL downloads, aggregate dashboards, 49 automated tests, a CI
pipeline and complete deployment documentation.

## 1. Introduction
Educational assessment workflows are fundamentally information-management
problems: distributing coursework, collecting files, tracking who submitted
what, and returning evaluation. Cloud computing fits naturally — the audience
is distributed, deadlines create bursty demand, files demand cheap durable
storage, and availability must span student schedules. This project uses that
everyday workflow to demonstrate cloud architecture with production discipline:
12-factor configuration, least-privilege storage, observability and CI/CD.

## 2. Problem Statement
Manual submission channels (email, chat, physical media) provide no auditable
central state: submissions are lost, deadlines are disputable, feedback is
scattered across inboxes, and teachers lack any aggregate view. Heavy
institutional LMS products exist, but small institutions and course projects
need a minimal, transparent, cloud-native alternative that still demonstrates
correct security and storage architecture.

## 3. Objectives
Deliver a working two-role portal that demonstrates: cloud-hosted application,
cloud database, object storage, authentication, RBAC, REST API design,
server-side deadline logic, secure file handling, dashboards, testing,
deployment and documentation — at zero monetary cost.

## 4. Existing System
Email/chat submissions: no deadline enforcement, no status tracking, no
central feedback store, mailbox storage limits, no access control beyond
recipients. Desktop LMS deployments: heavy to host and operate, rarely
free-tier friendly, poor demonstrability of individual cloud concepts.

## 5. Proposed System
A React SPA calling a stateless FastAPI REST API. JWT authentication with
bcrypt credential storage; role and row-level authorization enforced
server-side. Files land in private object storage (folder or Supabase bucket)
via validated, server-mediated uploads; metadata, marks and feedback live in
SQLite/Postgres behind a provider abstraction. Deadline decisions use server
UTC time with per-assignment late/resubmission policies. Dashboards aggregate
per-role statistics. Health probes, logging and CI complete the operational
story.

## 6. User Roles
STUDENT: register/login, view enrolled coursework, submit/resubmit files,
track status, download own work, read marks/feedback.
TEACHER: invite-gated signup, manage courses/enrollment, manage assignments
with full policy control, review rosters, download files, grade within
mark ceilings, view workload statistics.

## 7. Cloud Computing Concepts
SaaS delivery; PaaS consumption (Render/Vercel/Supabase); IaaS mappings
documented; DBaaS via DATABASE_URL swap; object storage with signed URLs;
JWT authN + dependency-based authZ; stateless horizontally scalable API;
CDN-fronted SPA; gateway-role middleware (CORS, rate limiting); environment-
based secrets; logging and health monitoring; backup practices; CI/CD.
Complete mapping with evidence: docs/cloud-concepts-mapping.md.

## 8. Technology Stack
React 18/Vite/React Router · FastAPI/SQLAlchemy 2/Pydantic v2 · SQLite or
Supabase Postgres · folder or Supabase Storage · bcrypt + PyJWT · pytest ·
GitHub Actions · Render + Vercel hosting.

## 9. System Architecture
See docs/architecture.md — logical diagram, provider abstraction, three
complete request flows (submit, grade, storage failure) and the public-cloud
reference topology.

## 10. Database Design
Five entities (users, courses, enrollments, assignments, submissions) with
UUID PKs, indexed FKs, uniqueness constraints, and the computed
NOT_SUBMITTED status. ERD + rationale: docs/database-design.md.

## 11. Cloud Storage Design
submissions/{assignment}/{student}/{attempt}_{uuid}_{name} layout, server-only
credentials, authorized downloads / 300-second signed URLs, provider parity
table. docs/storage-design.md.

## 12. Authentication
bcrypt hashes, HS256 JWTs (sub/role/exp/jti), stateless logout, generic login
errors to prevent user enumeration, optional Supabase Auth mode.

## 13. Assignment Management
Full CRUD owned by course teachers; policy fields (allowed extensions, size
cap, resubmission, late acceptance) validated server-side and surfaced in UI.

## 14. Submission Workflow
Authn → role → enrollment → deadline gate → resubmission policy → file
validation → storage upload → metadata write → 201. Status derived from the
server clock: SUBMITTED or LATE.

## 15. Deadline Management
UTC storage, naive-datetime normalization, per-assignment allow_late and
allow_resubmission; 409 when late uploads are disabled. Client clocks are
displayed only, never trusted.

## 16. Feedback & Grading
Teacher-of-course-only grading, marks bounded by 0..max_marks (400 otherwise),
feedback text, graded_at/graded_by audit fields, student read-only access.

## 17. API Design
21 endpoints; full contract with status codes in docs/api-reference.md;
interactive /docs UI generated by FastAPI.

## 18. Implementation
~30 backend modules, 20 frontend files; every external dependency behind a
provider interface; comments aimed at teaching the concepts they implement.

## 19. Testing
49 pytest cases (authn, authz, CRUD, uploads, deadlines, resubmission,
isolation, grading, dashboards, storage failure, health) plus a 17-check live
smoke script and a 25-case manual matrix. docs/test-plan.md.

## 20. Cloud Deployment
Free-tier approach: Render + Vercel + Supabase; push-to-deploy CI.
Public-cloud mapping: AWS/Azure/GCP table. docs/cloud-deployment.md.

## 21. Security
Controls: hashing, JWT expiry, RBAC, row-level 404s, invite-gated roles,
magic-byte + size validation, private storage, path guards, CORS allowlist,
rate limiting, env secrets, logging, no user enumeration.
docs/security.md.

## 22. Scalability
Stateless design + externalized state; concrete plans at 10/1k/100k students
with LB, autoscaling, replicas, cache, queues, workers.
docs/scalability.md.

## 23. Results
All automated and live tests pass; the full workflow operates end-to-end in
both local and cloud modes; RBAC denials are demonstrably enforced at every
boundary; deployment requires no paid services.

## 24. Advantages
Centralized, auditable state; remote accessibility; elastic storage;
automated tracking; reduced paperwork; consistent feedback records; secure
role-scoped access; low/no cost operation.

## 25. Limitations
Free-tier cold starts; single-instance rate limiting; no native notifications;
structural (not AV) file scanning; stateless logout; single-grader model.

## 26. Future Scope
Refresh-token revocation, pre-signed direct uploads, AV pipeline, queued
notifications, plagiarism heuristics, rubric grading, group work, audit
exports, IaC, multi-tenancy.

## 27. Conclusion
The project shows that a course-sized system can embody real cloud-native
practice: provider abstraction, correct storage separation, server-side
policy enforcement, observable operations and automated delivery — and that
"cloud" is an architecture discipline, not just where the VM lives.

## 28. References
FastAPI documentation · SQLAlchemy 2.0 · Supabase docs (Postgres, Storage,
Auth) · Render & Vercel deployment docs · OWASP Application Security
Verification Standard · RFC 7519 (JWT) · MDN HTTP security docs.
