# PROJECT SPECIFICATION DOCUMENT: PROJECT JUNIPER
**Version:** 1.0.4  
**Status:** Draft / Internal Reference  
**Date:** October 24, 2025  
**Company:** Iron Bay Technologies  
**Project Lead:** Malik Liu (CTO)

---

## 1. EXECUTIVE SUMMARY

**Project Overview**
Project "Juniper" is a strategic SaaS platform initiative commissioned by Iron Bay Technologies. The primary objective is a cost-reduction consolidation effort designed to merge four redundant internal fintech tools into a single, unified ecosystem. Currently, Iron Bay Technologies operates four disparate legacy systems—each with its own licensing costs, maintenance overhead, and fragmented data silos. Juniper aims to eliminate these redundancies, reducing operational expenditure (OpEx) while increasing developer velocity and system reliability.

**Business Justification**
The current fragmentation of internal tools has led to "tooling fatigue" and significant technical inefficiency. Maintenance of these four legacy systems requires separate security patches, distinct database backups, and divergent API protocols, costing the company an estimated $420,000 annually in licensing and developer hours spent on "keep-the-lights-on" (KTLO) activity. By consolidating into Juniper, the organization will centralize its business logic, standardize its data models, and reduce the surface area for security vulnerabilities. 

**ROI Projection**
The projected Return on Investment (ROI) for Juniper is calculated over a 36-month horizon. 
1. **Direct Cost Savings:** By decommissioning the four legacy tools, the company expects to save $110,000 per year in third-party SaaS licenses.
2. **Engineering Efficiency:** Consolidation is estimated to recover 15% of the backend team's capacity, representing a value of approximately $200,000 in regained productivity.
3. **Infrastructure Optimization:** Moving to a unified Next.js/Vercel stack allows for better resource utilization, reducing cloud spend by an estimated 12% annually.
4. **Total Estimated 3-Year Savings:** $780,000.

The project is funded via a variable, milestone-based tranche system. Funding is released upon the successful completion of predefined technical hurdles (e.g., passing the security audit, onboarding the first customer), ensuring that capital is deployed only as the product proves its viability.

**Strategic Alignment**
Juniper aligns with Iron Bay Technologies' goal of becoming a "lean-first" organization. By streamlining the fintech toolset, the company can pivot faster to market demands without being bogged down by legacy maintenance. The platform will serve as the foundational layer for all future fintech internal services, ensuring that any new functionality is built on a standardized, scalable architecture.

---

## 2. TECHNICAL ARCHITECTURE

Juniper utilizes a traditional three-tier architecture designed for high availability, scalability, and rapid deployment cycles.

### 2.1 The Three-Tier Model
1. **Presentation Tier (Frontend):** Built using **Next.js** and **TypeScript**. This layer handles the user interface, client-side routing, and state management. It is deployed on **Vercel**, leveraging Edge Functions for low-latency delivery of the frontend assets and server-side rendering (SSR) for performance.
2. **Business Logic Tier (Backend):** This layer consists of Next.js API routes and serverless functions. It processes requests, enforces business rules (such as rate limiting and API versioning), and manages the flow of data between the presentation tier and the data tier. TypeScript is used throughout to ensure type safety across the network boundary.
3. **Data Tier (Persistence):** A **PostgreSQL** database managed via **Prisma ORM**. This layer ensures ACID compliance and provides a structured environment for the complex relational data inherent in fintech applications.

### 2.2 Architecture Diagram Description (ASCII)
Because this is a text-based specification, the architecture is visualized as follows:

```text
[ USER BROWSER ] 
       |
       v
[ VERCEL EDGE NETWORK ] <--- (CDN / Global Distribution)
       |
       v
[ NEXT.JS APPLICATION LAYER ] <--- (Business Logic / API Routes)
       |       |
       |       +------> [ REDIS CACHE ] (Rate Limiting/Session)
       |
       v
[ PRISMA ORM ] <--- (Type-safe Database Access)
       |
       v
[ POSTGRESQL DATABASE ] <--- (Persistent Storage / Audit Logs)
       |
       +------> [ S3 BUCKET / STORAGE ] (File Uploads - Pending)
```

### 2.3 Deployment Pipeline
The project utilizes a robust CI/CD pipeline via **GitHub Actions**. 
- **Continuous Integration:** Every push to the `develop` or `main` branch triggers a suite of linting, type-checking, and unit tests.
- **Blue-Green Deployment:** Vercel’s deployment model is leveraged to implement blue-green strategies. New versions are deployed to "Preview" environments. Once validated by the QA process and the 12-person cross-functional team, the traffic is shifted from the "Blue" (current) environment to the "Green" (new) environment via a DNS switch.
- **Environment Parity:** Strict parity is maintained between `dev`, `staging`, and `prod` using environment variables managed via Vercel’s Project Settings.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** Critical (Launch Blocker) | **Status:** In Design

This feature is the cornerstone of Juniper's external utility. The goal is to provide a robust, developer-friendly API that allows external clients to integrate with Iron Bay's consolidated services.

**Technical Requirements:**
- **Versioning:** The API must support semantic versioning via the URL path (e.g., `/api/v1/resource` and `/api/v2/resource`). A deprecation policy will be implemented where old versions are supported for six months after a new version is released.
- **Sandbox Environment:** A completely isolated environment (`sandbox.juniper.ironbay.tech`) where customers can test API calls without impacting production data. The sandbox will use a mirrored schema of the production database but with mocked financial data.
- **Authentication:** Implementation of OAuth2 and API Key-based authentication. Keys will be hashed in the database and rotated every 90 days.
- **Documentation:** Integration of Swagger/OpenAPI 3.0 to provide auto-generated, interactive documentation.

**User Workflow:**
1. A customer signs up and generates an API key from the Juniper Dashboard.
2. The customer switches their environment toggle to "Sandbox."
3. They execute a `POST` request to the sandbox endpoint to validate their integration.
4. Upon successful testing, they switch to "Production" and update their base URL.

**Success Metrics:**
- Ability to spin up a new sandbox instance in under 5 minutes.
- 100% uptime for the `/v1/` endpoints during the alpha phase.

---

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** Complete

To prevent abuse and ensure fair resource distribution, Juniper implements a strict rate-limiting mechanism and a comprehensive analytics engine.

**Technical Requirements:**
- **Mechanism:** A sliding-window algorithm implemented using Redis. This prevents "bursting" at the edge of a time window.
- **Tiers:** Three tiers of rate limits: `Basic` (100 req/min), `Professional` (1,000 req/min), and `Enterprise` (Unlimited/Custom).
- **Headers:** Every API response must include standard rate-limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Pipeline:** Every single API call is logged to a `UsageLogs` table. A background worker aggregates these logs every hour to generate usage reports.

**Implementation Details:**
The rate limiter is implemented as a Next.js Middleware function. Before a request reaches the business logic tier, the middleware checks the API key against the Redis store. If the quota is exceeded, a `429 Too Many Requests` response is returned immediately.

**Usage Analytics Dashboard:**
The internal team has access to a dashboard showing:
- Peak request times (per hour).
- Most frequently called endpoints.
- Error rate distribution (4xx vs 5xx).

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** In Review

In a fintech environment, accountability is paramount. This feature ensures that every administrative action and data modification is recorded in a way that cannot be silently altered.

**Technical Requirements:**
- **Logging Scope:** Every `UPDATE`, `DELETE`, and `SENSITIVE_READ` operation is captured.
- **Tamper-Evidence:** Each log entry contains a SHA-256 hash of the current record concatenated with the hash of the previous record (a hash-chain). This ensures that if a record in the middle of the chain is altered, all subsequent hashes become invalid.
- **Storage:** Logs are stored in a dedicated `AuditLogs` table with "append-only" permissions at the database user level.

**Log Schema:**
- `timestamp`: ISO 8601 format.
- `actor_id`: The ID of the user or system process performing the action.
- `action`: The specific event (e.g., `USER_PERMISSION_CHANGE`).
- `payload_before`: JSON snapshot of the record before the change.
- `payload_after`: JSON snapshot of the record after the change.
- `checksum`: The resulting hash for the chain.

**Review Criteria:**
Currently, the security team is reviewing whether the hash-chain is sufficient or if a third-party immutable ledger (like AWS QLDB) is required.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** In Design

This "nice-to-have" feature allows users to upload documents (e.g., KYC documents, invoices) and serves them globally via a CDN.

**Technical Requirements:**
- **Upload Flow:** Frontend $\rightarrow$ Pre-signed URL (S3) $\rightarrow$ Virus Scanner $\rightarrow$ Permanent Storage.
- **Virus Scanning:** Integration with a scanning engine (e.g., ClamAV or a cloud-native equivalent). Files are uploaded to a "quarantine" bucket first. Only after a "Clean" signal is received are they moved to the "Production" bucket.
- **CDN Distribution:** Integration with Amazon CloudFront or Vercel Blob to ensure that files are cached at edge locations, reducing latency for global users.
- **Security:** All files must be encrypted at rest (AES-256) and served via HTTPS.

**Design Considerations:**
The team is deciding between a synchronous scan (where the user waits for the result) and an asynchronous scan (where the user is notified via webhook when the file is "Ready"). Given the fintech context, asynchronous is preferred to avoid blocking the UI.

---

### 3.5 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** Complete

To support users in low-connectivity environments, Juniper implements an offline-first capability for specific dashboard modules.

**Technical Requirements:**
- **Local Storage:** Use of **IndexedDB** via the `idb` library to cache application state and pending mutations.
- **Service Workers:** Implementation of a Service Worker to intercept network requests. If the network is unavailable, the worker serves the cached version of the page.
- **Background Sync API:** Using the `sync` event in the Service Worker, the application queues mutations (e.g., updating a user profile) while offline. Once the browser detects a restored connection, the queue is flushed to the server.
- **Conflict Resolution:** A "Last-Write-Wins" strategy is employed for simple fields, while a manual merge is required for complex financial records.

**User Experience:**
A small "Offline" indicator appears in the bottom right of the UI. When the user performs an action while offline, the action is marked as "Pending Sync" with a clock icon.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base URL: `https://api.juniper.ironbay.tech/v1`

### 4.1 GET /accounts
- **Description:** Retrieves a list of all accounts associated with the authenticated user.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
```json
[
  { "id": "acc_123", "name": "Operating Account", "balance": 5000.00, "currency": "USD" },
  { "id": "acc_456", "name": "Savings", "balance": 12000.50, "currency": "USD" }
]
```

### 4.2 POST /transactions
- **Description:** Creates a new financial transaction.
- **Request:**
```json
{
  "amount": 150.00,
  "currency": "USD",
  "recipient_id": "usr_987",
  "memo": "Monthly Subscription"
}
```
- **Response (201 Created):**
```json
{ "transaction_id": "tx_abc123", "status": "pending", "timestamp": "2026-01-01T10:00:00Z" }
```

### 4.3 GET /analytics/usage
- **Description:** Returns the API usage stats for the current billing cycle.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
```json
{
  "total_requests": 4500,
  "limit": 10000,
  "remaining": 5500,
  "period_end": "2026-01-31T23:59:59Z"
}
```

### 4.4 PATCH /user/settings
- **Description:** Updates the user's profile settings.
- **Request:**
```json
{ "notification_email": "new-email@example.com", "mfa_enabled": true }
```
- **Response (200 OK):**
```json
{ "status": "success", "updated_at": "2026-01-01T12:00:00Z" }
```

### 4.5 GET /audit/logs
- **Description:** Retrieves a paginated list of audit logs (Admin only).
- **Request:** `?page=1&limit=50`
- **Response (200 OK):**
```json
{
  "logs": [
    { "id": "log_001", "action": "LOGIN", "user": "admin_1", "timestamp": "..." }
  ],
  "meta": { "total_pages": 5, "current_page": 1 }
}
```

### 4.6 DELETE /api-keys/{key_id}
- **Description:** Revokes a specific API key.
- **Request:** `DELETE /api-keys/key_888`
- **Response (204 No Content):** Empty body.

### 4.7 POST /sandbox/reset
- **Description:** Wipes all data in the sandbox environment and restores the seed state.
- **Request:** `Authorization: Bearer <sandbox_token>`
- **Response (200 OK):**
```json
{ "message": "Sandbox environment successfully reset." }
```

### 4.8 GET /health
- **Description:** System health check for monitoring tools.
- **Request:** No auth required.
- **Response (200 OK):**
```json
{ "status": "healthy", "database": "connected", "redis": "connected", "version": "1.0.4" }
```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL instance managed by Prisma. All tables use UUIDs for primary keys to ensure uniqueness across distributed systems.

### 5.1 Table Definitions

1. **`Users`**: Stores identity and authentication data.
   - `id` (UUID, PK)
   - `email` (String, Unique)
   - `password_hash` (String)
   - `mfa_secret` (String, Nullable)
   - `created_at` (Timestamp)

2. **`Accounts`**: Financial account details.
   - `id` (UUID, PK)
   - `user_id` (UUID, FK $\rightarrow$ Users.id)
   - `account_name` (String)
   - `balance` (Decimal)
   - `currency` (String, 3 chars)

3. **`Transactions`**: Ledger of all money movements.
   - `id` (UUID, PK)
   - `sender_id` (UUID, FK $\rightarrow$ Accounts.id)
   - `receiver_id` (UUID, FK $\rightarrow$ Accounts.id)
   - `amount` (Decimal)
   - `status` (Enum: PENDING, COMPLETED, FAILED)
   - `created_at` (Timestamp)

4. **`ApiKeys`**: Management of external access.
   - `id` (UUID, PK)
   - `user_id` (UUID, FK $\rightarrow$ Users.id)
   - `key_hash` (String)
   - `environment` (Enum: PRODUCTION, SANDBOX)
   - `last_used_at` (Timestamp)

5. **`RateLimits`**: Current quotas for users.
   - `id` (UUID, PK)
   - `user_id` (UUID, FK $\rightarrow$ Users.id)
   - `tier` (Enum: BASIC, PRO, ENT)
   - `request_limit` (Integer)

6. **`AuditLogs`**: Tamper-evident system logs.
   - `id` (UUID, PK)
   - `actor_id` (UUID, FK $\rightarrow$ Users.id)
   - `action` (String)
   - `payload_before` (JSONB)
   - `payload_after` (JSONB)
   - `checksum` (String)
   - `timestamp` (Timestamp)

7. **`UsageLogs`**: High-frequency API hit tracking.
   - `id` (BigInt, PK)
   - `api_key_id` (UUID, FK $\rightarrow$ ApiKeys.id)
   - `endpoint` (String)
   - `response_code` (Integer)
   - `latency_ms` (Integer)
   - `timestamp` (Timestamp)

8. **`Files`**: Metadata for uploaded documents.
   - `id` (UUID, PK)
   - `user_id` (UUID, FK $\rightarrow$ Users.id)
   - `s3_path` (String)
   - `mime_type` (String)
   - `scan_status` (Enum: PENDING, CLEAN, INFECTED)

9. **`Organizations`**: Grouping for Enterprise clients.
   - `id` (UUID, PK)
   - `org_name` (String)
   - `billing_email` (String)
   - `created_at` (Timestamp)

10. **`OrgMembers`**: Join table for Users and Organizations.
    - `org_id` (UUID, FK $\rightarrow$ Organizations.id)
    - `user_id` (UUID, FK $\rightarrow$ Users.id)
    - `role` (Enum: ADMIN, MEMBER, VIEWER)

### 5.2 Relationships
- **User $\rightarrow$ Account:** One-to-Many.
- **Account $\rightarrow$ Transaction:** One-to-Many (as both sender and receiver).
- **User $\rightarrow$ ApiKey:** One-to-Many.
- **Organization $\rightarrow$ User:** Many-to-Many via `OrgMembers`.
- **User $\rightarrow$ AuditLog:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Juniper maintains three distinct environments to ensure that no untested code ever reaches a paying customer.

**1. Development (`dev`)**
- **Purpose:** Sandbox for developers to iterate on new features.
- **Database:** Shared development PostgreSQL instance with mocked data.
- **Deployment:** Triggered on every push to the `develop` branch.
- **Access:** Limited to the 12-person cross-functional team.

**2. Staging (`staging`)**
- **Purpose:** Pre-production validation and internal alpha testing.
- **Database:** A restored snapshot of production data (anonymized) to ensure scale testing.
- **Deployment:** Triggered on merges from `develop` to `release` branches.
- **Access:** Project Lead (Malik Liu) and Security Engineer (Ayo Nakamura).

**3. Production (`prod`)**
- **Purpose:** Live environment for paying customers.
- **Database:** High-availability PostgreSQL cluster with multi-region replication.
- **Deployment:** Manual trigger from the `main` branch following a successful staging sign-off.
- **Access:** Restricted; automated deployment via GitHub Actions.

### 6.2 Infrastructure Component Table

| Component | Service | Configuration |
| :--- | :--- | :--- |
| Frontend / API | Vercel | Next.js 14+, Edge Runtime enabled |
| Database | Supabase / Postgres | v15, 4 vCPU, 16GB RAM |
| Cache/Rate Limit | Redis | Managed Redis Cloud (Standard Tier) |
| CI/CD | GitHub Actions | Self-hosted runners for security |
| Version Control | GitHub | Enterprise Cloud |
| Monitoring | Sentry / Datadog | Error tracking and APM |

---

## 7. TESTING STRATEGY

To ensure a "zero critical security incidents" success metric, Juniper employs a pyramidal testing strategy.

### 7.1 Unit Testing
- **Focus:** Individual functions, utility helpers, and Prisma hooks.
- **Tooling:** Jest and Vitest.
- **Requirement:** 80% code coverage is mandatory for all new business logic.
- **Execution:** Runs on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** API endpoint flows, database migrations, and third-party service integrations (e.g., Redis connectivity).
- **Tooling:** Supertest and Playwright.
- **Approach:** Tests are run against a temporary PostgreSQL Docker container that is spun up and torn down for each test suite to ensure a clean state.
- **Example:** Verifying that a transaction correctly debits one account and credits another in a single atomic transaction.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "User signs up $\rightarrow$ Generates API Key $\rightarrow$ Makes first request").
- **Tooling:** Playwright.
- **Execution:** Runs once per day on the `staging` environment.
- **Coverage:** Covers the top 10 most frequent user paths.

### 7.4 Security Testing
- **Internal Audit:** Since no external compliance is needed, Ayo Nakamura (Security Engineer) performs weekly manual penetration tests and dependency audits using `npm audit` and Snyk.
- **Static Analysis:** Integration of SonarQube to detect "code smells" and potential security vulnerabilities (e.g., SQL injection risks) during the CI process.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotation (Loss of executive support) | High | Critical | Escalate to the steering committee immediately to secure a new sponsor and lock in milestone funding. |
| **R-02** | Competitor is 2 months ahead in feature parity | Medium | High | Document competitor workarounds and feature gaps; pivot focus to the "Sandbox Environment" as a unique selling point. |
| **R-03** | Technical debt: Hardcoded configs in 40+ files | High | Medium | Implement a phased migration to a centralized `.env` and `config.ts` system; allocate 10% of every sprint to refactoring. |
| **R-04** | Delay in Legal review of Data Processing Agreement (DPA) | High | Critical | **CURRENT BLOCKER.** Malik Liu to schedule a daily sync with the legal team until the DPA is signed. |
| **R-05** | Database migration failure during consolidation | Low | High | Implement blue-green database deployments with a 24-hour rollback window. |

### Probability/Impact Matrix
- **Critical:** High Probability + High Impact $\rightarrow$ Immediate Action.
- **High:** Medium Probability + High Impact $\rightarrow$ Constant Monitoring.
- **Medium:** High Probability + Low Impact $\rightarrow$ Scheduled Mitigation.
- **Low:** Low Probability + Low Impact $\rightarrow$ Accept Risk.

---

## 9. TIMELINE AND PHASES

The project follows a milestone-driven timeline. Each phase is dependent on the successful closure of the previous phase's "Definition of Done" (DoD).

### Phase 1: Infrastructure & Core Logic (Now – 2026-08-15)
- **Focus:** Setting up the Vercel/Postgres stack and completing the Rate Limiting and Audit systems.
- **Key Dependency:** Completion of the `UsageLogs` schema.
- **Target Milestone 1:** **Security Audit Passed (2026-08-15).**

### Phase 2: External Interface & Alpha (2026-08-16 – 2026-10-15)
- **Focus:** Developing the Customer-Facing API, Versioning, and the Sandbox environment.
- **Key Dependency:** Finalization of the API documentation (Swagger).
- **Target Milestone 2:** **Internal Alpha Release (2026-10-15).**

### Phase 3: Beta & Monetization (2026-10-16 – 2026-12-15)
- **Focus:** Onboarding external testers and refining the billing integration.
- **Key Dependency:** Legal approval of the Data Processing Agreement (DPA).
- **Target Milestone 3:** **First Paying Customer Onboarded (2026-12-15).**

### Phase 4: Optimization & "Nice-to-Haves" (2027-01-01 – Ongoing)
- **Focus:** File upload scanning, CDN distribution, and Offline-first mode.
- **Key Dependency:** Stability of the core API.

---

## 10. MEETING NOTES

*Note: Per company policy, these are summaries of recorded video calls (which the team does not rewatch).*

### Meeting 1: Architecture Alignment (Date: 2025-11-05)
- **Attendees:** Malik, Nadira, Ayo, Callum.
- **Discussion:** Callum suggested using a NoSQL database for the usage logs to handle high write volume. Nadira countered that keeping everything in PostgreSQL using a partitioned table would reduce architectural complexity and maintain consistency.
- **Decision:** Stick with PostgreSQL. Use `BigInt` for the `UsageLogs` primary key to prevent overflow.
- **Action Item:** Nadira to implement table partitioning by month for `UsageLogs`.

### Meeting 2: The "Competitor Panic" Sync (Date: 2025-12-12)
- **Attendees:** Malik, Nadira, Ayo.
- **Discussion:** Malik shared a demo of a competitor's product that has a more intuitive onboarding flow. The team discussed whether to pivot the roadmap to prioritize the UI.
- **Decision:** No pivot. We will focus on the "Sandbox Environment" and "Tamper-Evident Audit Logs" as these are critical for fintech enterprise clients and are currently missing from the competitor's offering.
- **Action Item:** Malik to document the competitor's shortcomings and share a "Gap Analysis" document on Slack.

### Meeting 3: Legal Blockage Sync (Date: 2026-02-20)
- **Attendees:** Malik, Ayo.
- **Discussion:** Discussion on the current blocker: The Data Processing Agreement (DPA) is stalled in legal review. Ayo expressed concern that we cannot onboard alpha users without the DPA.
- **Decision:** Malik will escalate the issue to the steering committee. In the meantime, the team will focus on the "Offline-First" mode since it is a purely technical task.
- **Action Item:** Malik to email the General Counsel by EOD.

---

## 11. BUDGET BREAKDOWN

The budget is released in tranches. Total estimated budget for the consolidation phase: **$1,250,000**.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $850,000 | 12-person team (Salaries, benefits, bonuses) |
| **Infrastructure** | $120,000 | Vercel Enterprise, Supabase, Redis Cloud, AWS S3 |
| **Tools & Licenses** | $60,000 | Sentry, Datadog, GitHub Enterprise, Snyk |
| **Contingency** | $220,000 | Reserved for emergency scaling or legal fees |
| **TOTAL** | **$1,250,000** | |

**Tranche Release Schedule:**
- **Tranche 1 (30%):** Released at project kick-off.
- **Tranche 2 (30%):** Released upon completion of Milestone 1 (Security Audit).
- **Tranche 3 (20%):** Released upon completion of Milestone 2 (Internal Alpha).
- **Tranche 4 (20%):** Released upon completion of Milestone 3 (First Paying Customer).

---

## 12. APPENDICES

### Appendix A: Configuration Debt Map
As noted in the Risk Register, there are hardcoded values across 40+ files. The following is the priority list for the "Config Cleanup" sprint:
- `src/lib/db.ts` $\rightarrow$ Move `DATABASE_URL` to Vercel Env.
- `src/api/rate-limit.ts` $\rightarrow$ Move `REDIS_URL` and `DEFAULT_LIMIT` to config file.
- `src/utils/auth.ts` $\rightarrow$ Move `JWT_SECRET` and `COOKIE_NAME` to env.
- `src/api/v1/transactions.ts` $\rightarrow$ Move `CURRENCY_PRECISION` to a global constant file.

### Appendix B: Hash-Chain Algorithm Specification
For the Audit Trail, the `checksum` for record $N$ is calculated as:
`Hash_N = SHA256(Timestamp + ActorID + Action + PayloadAfter + Hash_{N-1})`

**Verification Process:**
To verify the integrity of the audit log:
1. Start at the first record (where `Hash_{N-1}` is a seed value).
2. Recompute the hash using the record data and the previous hash.
3. If the computed hash does not match the stored `checksum`, the chain is compromised.
4. This process is repeated sequentially for all records in the `AuditLogs` table.