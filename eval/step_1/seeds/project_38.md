# Project Specification: Project Halcyon
**Document Version:** 1.0.4  
**Status:** Draft/Internal Review  
**Last Updated:** October 24, 2023  
**Project Lead:** Esme Kim (VP of Product)  
**Company:** Crosswind Labs  
**Confidentiality Level:** High

---

## 1. Executive Summary

Project Halcyon is the strategic initiative by Crosswind Labs to modernize the core operational infrastructure of our real estate portfolio management system. For fifteen years, the company has relied on a monolithic legacy system—a "black box" of COBOL and early Java—that manages the entirety of our property valuations, client lease agreements, and transaction processing. While stable, this system has become a catastrophic bottleneck; it is incapable of supporting modern machine learning (ML) inference for predictive real estate pricing, cannot scale to meet current market volatility, and requires specialized knowledge that is rapidly disappearing from the workforce.

The business justification for Halcyon is rooted in operational survival and competitive dominance. Currently, our cost per transaction is inflated by legacy maintenance fees and inefficient manual data entry. By deploying a modern ML-driven architecture, we aim to automate the valuation process, reducing the "time-to-quote" from 48 hours to under 200 milliseconds. The ROI projection is centered on two primary drivers: a projected 35% reduction in cost per transaction through the elimination of manual auditing and a significant increase in capture rate due to real-time pricing agility.

The project is uniquely constrained by a "zero downtime" mandate. Because the legacy system is the heartbeat of Crosswind Labs, any interruption in service during the transition would result in immediate revenue loss and breach of contract with several Tier-1 institutional investors. Consequently, Halcyon is not a "rip and replace" project but a phased strangler-pattern migration.

Financially, Project Halcyon is currently unfunded in terms of a dedicated capital expenditure (CapEx) budget. We are bootstrapping the project using existing team capacity across three departments: Product, Engineering, and UX. This approach minimizes immediate financial risk but increases the risk of burnout and resource contention. The success of Halcyon will be measured by its ability to maintain 100% system availability while achieving a p95 API response time of under 200ms at peak load, ensuring that our ML models provide instantaneous value to the end user without the latency inherent in the old system.

---

## 2. Technical Architecture

Project Halcyon adopts a traditional three-tier architecture to ensure stability, maintainability, and clear separation of concerns. This structure is designed to facilitate the gradual migration of services from the legacy system to the new TypeScript-based stack.

### 2.1 Tier Definitions
1.  **Presentation Tier:** A responsive web application built with **Next.js** and **TypeScript**. This tier handles user interaction, client-side state management, and the visual rule builder for workflow automation. It is deployed via **Vercel** to leverage Edge Functions for low-latency delivery.
2.  **Business Logic Tier:** A series of serverless functions and API routes (Next.js API routes and dedicated Node.js services) that implement the core real estate logic, ML model orchestration, and integration with the legacy database. This layer utilizes **Prisma** as the ORM to ensure type-safety across the data boundary.
3.  **Data Tier:** A robust **PostgreSQL** cluster hosted on AWS RDS. This tier stores the new system's state, user profiles, and the cached outputs of the ML models, while maintaining a synchronized bridge to the legacy COBOL-based data store.

### 2.2 Architectural Diagram (ASCII)

```text
[ USER BROWSER ] 
       |
       v
[ VERCEL EDGE NETWORK ] <--- (CDN & Routing)
       |
       v
[ NEXT.JS APPLICATION ] <--- (Presentation Tier)
       |
       +--- [ API ROUTES / SERVERLESS ] <--- (Business Logic Tier)
       |             |
       |             +---> [ ML INFERENCE ENGINE ] (Python/Triton)
       |             |
       |             +---> [ AUTH SERVICE ] (SAML/OIDC)
       |
       v
[ PRISMA ORM ] <--- (Data Access Layer)
       |
       v
[ POSTGRESQL DB ] <--- (Data Tier)
       |
       +--- [ LEGACY BRIDGE ] ---> [ 15-YEAR-OLD LEGACY SYSTEM ]
```

### 2.3 Tech Stack Versioning
- **TypeScript:** v5.2.2
- **Next.js:** v14.0.1 (App Router)
- **Prisma:** v5.3.0
- **PostgreSQL:** v15.4
- **Node.js:** v20.x (LTS)
- **Vercel:** Enterprise Plan

---

## 3. Detailed Feature Specifications

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** In Progress

The Workflow Automation Engine is designed to allow non-technical real estate analysts to create complex logic chains for property processing without writing code. In the legacy system, these rules were hard-coded into the backend, requiring a full deployment for any change. 

The "Visual Rule Builder" is a drag-and-drop interface where users can define "Triggers" (e.g., *Property Value > $1M*), "Conditions" (e.g., *Location == 'New York'*), and "Actions" (e.g., *Send notification to Senior Broker*). 

**Technical Specifications:**
- **Logic Engine:** The system will use a JSON-based logic tree stored in PostgreSQL. When a transaction occurs, the engine parses this tree to determine the execution path.
- **State Machine:** We are implementing a finite state machine (FSM) to track the progress of a property through the workflow (e.g., `Draft` -> `Pending Review` -> `Approved` -> `Closed`).
- **Conflict Handling:** Since multiple users may edit rules, the engine must implement a locking mechanism to prevent concurrent modifications to the same rule-set.

The goal is to reduce the time it takes to update a business rule from two weeks (legacy cycle) to five minutes (real-time update).

### 3.2 SSO Integration (SAML and OIDC)
**Priority:** Critical (Launch Blocker) | **Status:** In Design

Crosswind Labs operates in a high-security corporate environment. To replace the legacy system, Halcyon must integrate with the company's existing identity providers (IdP). This is a launch blocker; without SSO, the 20+ person team and the wider company cannot access the system securely.

**Technical Specifications:**
- **SAML 2.0:** Implementation for institutional clients who use Active Directory (ADFS). The system must support Service Provider-initiated (SP-initiated) and Identity Provider-initiated (IdP-initiated) SSO.
- **OIDC (OpenID Connect):** Implementation for modern internal tools and Google Workspace integration. 
- **JWT Management:** Upon successful authentication, the system will issue a signed JSON Web Token (JWT) with a 15-minute expiration, refreshed via a rotating refresh token stored in an `httpOnly` cookie.
- **Role-Based Access Control (RBAC):** The SSO payload must map to internal roles: `Admin`, `Broker`, `Analyst`, and `Read-Only`.

The design must ensure that if the IdP is unavailable, there is a break-glass emergency admin account managed by Esme Kim.

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low (Nice to Have) | **Status:** In Design

The legacy system generated monolithic reports every Friday at 5:00 PM. Halcyon will modernize this by providing on-demand and scheduled reports.

**Technical Specifications:**
- **Engine:** Use of `Puppeteer` for PDF generation (rendering HTML templates to PDF) and `csv-stringify` for data exports.
- **Scheduling:** A cron-job system managed via Vercel Cron or an external trigger (e.g., GitHub Actions) that polls the database for reports due for delivery.
- **Delivery:** Integration with SendGrid for email delivery. Reports will be uploaded to an S3 bucket with a pre-signed URL sent to the user, rather than attaching large files to emails.
- **Templating:** A system of Liquid templates that allow the Product team to change report layouts without engineering intervention.

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Progress

Real estate deal sheets often require input from brokers, lawyers, and analysts simultaneously. The legacy system used "pessimistic locking" (only one person could edit a record at a time), which crippled productivity.

**Technical Specifications:**
- **CRDTs (Conflict-free Replicated Data Types):** We are implementing `Yjs` to allow multiple users to edit the same field simultaneously without overwriting each other's changes.
- **WebSockets:** Connection via Socket.io to provide real-time cursor tracking and "User X is typing..." indicators.
- **Persistence:** Every 5 seconds, the current state of the CRDT document is flushed to the PostgreSQL database via Prisma to ensure no data loss.
- **Versioning:** A full audit log of changes (who changed what and when) will be stored in a `version_history` table.

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** In Review

Property dossiers contain thousands of PDFs, images, and spreadsheets. The legacy system stored these on a local network drive, which was slow and prone to corruption.

**Technical Specifications:**
- **Upload Pipeline:** Files are uploaded to a temporary S3 bucket via a pre-signed URL to avoid overloading the Next.js server.
- **Virus Scanning:** An asynchronous trigger invokes a ClamAV scanning service. If a file is flagged as malicious, it is immediately quarantined and the user is notified.
- **CDN Distribution:** Once scanned and cleared, files are moved to a production bucket integrated with CloudFront (CDN) to ensure global low-latency access.
- **Metadata:** File metadata (size, hash, uploader, timestamp) is stored in the `files` table in PostgreSQL.

---

## 4. API Endpoint Documentation

All endpoints follow REST conventions and return JSON. Base URL: `https://api.halcyon.crosswindlabs.com/v1`

### 4.1 `POST /auth/login`
- **Description:** Authenticates user via OIDC/SAML flow.
- **Request:** `{ "provider": "saml", "token": "string" }`
- **Response:** `200 OK { "accessToken": "jwt_string", "expiresIn": 900 }`

### 4.2 `GET /properties`
- **Description:** Retrieves a paginated list of properties.
- **Query Params:** `page=1`, `limit=20`, `status=active`
- **Response:** `200 OK { "data": [...], "total": 1500, "nextPage": 2 }`

### 4.3 `POST /properties/{id}/valuation`
- **Description:** Triggers the ML model to calculate current property value.
- **Request:** `{ "market_trend": "bullish", "comparables": ["id1", "id2"] }`
- **Response:** `202 Accepted { "jobId": "job_abc123", "eta": "200ms" }`

### 4.4 `GET /properties/{id}/valuation`
- **Description:** Fetches the result of the valuation job.
- **Response:** `200 OK { "valuation": 1250000, "confidence": 0.94, "timestamp": "2026-01-01T10:00:00Z" }`

### 4.5 `PUT /workflow/rules/{ruleId}`
- **Description:** Updates a specific automation rule.
- **Request:** `{ "trigger": "ValueChange", "condition": ">', "threshold": 50000 }`
- **Response:** `200 OK { "status": "updated", "version": 4 }`

### 4.6 `POST /reports/schedule`
- **Description:** Schedules a PDF report for delivery.
- **Request:** `{ "reportType": "QuarterlyAudit", "email": "user@crosswind.com", "cron": "0 0 1 * *" }`
- **Response:** `201 Created { "scheduleId": "sched_99" }`

### 4.7 `POST /files/upload-url`
- **Description:** Requests a pre-signed S3 URL for file upload.
- **Request:** `{ "fileName": "deal_doc.pdf", "fileSize": 1048576 }`
- **Response:** `200 OK { "uploadUrl": "https://s3...", "fileId": "file_xyz" }`

### 4.8 `GET /billing/summary`
- **Description:** Fetches transaction cost metrics.
- **Response:** `200 OK { "costPerTransaction": 1.42, "legacyComparison": 2.18, "savings": "35%" }`

---

## 5. Database Schema

The system uses a PostgreSQL relational schema managed by Prisma.

### 5.1 Table Definitions

1.  **`Users`**
    - `id`: UUID (PK)
    - `email`: String (Unique)
    - `role`: Enum (`ADMIN`, `BROKER`, `ANALYST`)
    - `last_login`: Timestamp
2.  **`Properties`**
    - `id`: UUID (PK)
    - `address`: String
    - `legacy_id`: Integer (Index - links to old system)
    - `current_value`: Decimal
    - `status`: String
3.  **`Valuations`**
    - `id`: UUID (PK)
    - `property_id`: UUID (FK -> Properties)
    - `value`: Decimal
    - `confidence_score`: Float
    - `created_at`: Timestamp
4.  **`WorkflowRules`**
    - `id`: UUID (PK)
    - `name`: String
    - `logic_json`: JSONB
    - `is_active`: Boolean
5.  **`WorkflowLogs`**
    - `id`: UUID (PK)
    - `rule_id`: UUID (FK -> WorkflowRules)
    - `property_id`: UUID (FK -> Properties)
    - `outcome`: String
6.  **`Files`**
    - `id`: UUID (PK)
    - `storage_key`: String
    - `mime_type`: String
    - `virus_scan_status`: Enum (`PENDING`, `CLEAN`, `INFECTED`)
7.  **`PropertyFiles`** (Join Table)
    - `property_id`: UUID (FK -> Properties)
    - `file_id`: UUID (FK -> Files)
8.  **`CollaborativeSessions`**
    - `id`: UUID (PK)
    - `document_id`: UUID
    - `active_users`: Integer
    - `last_sync`: Timestamp
9.  **`ReportSchedules`**
    - `id`: UUID (PK)
    - `user_id`: UUID (FK -> Users)
    - `cron_expression`: String
    - `template_id`: String
10. **`BillingTransactions`**
    - `id`: UUID (PK)
    - `property_id`: UUID (FK -> Properties)
    - `cost`: Decimal
    - `processed_at`: Timestamp

### 5.2 Relationships
- `Users` has a one-to-many relationship with `ReportSchedules`.
- `Properties` has a one-to-many relationship with `Valuations`.
- `Properties` and `Files` share a many-to-many relationship via `PropertyFiles`.
- `WorkflowRules` triggers entries in `WorkflowLogs` linked to `Properties`.

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
We utilize a three-tier environment strategy to ensure that no breaking changes reach the legacy-integrated production system.

- **Development (dev):**
    - **Purpose:** Feature development and unit testing.
    - **Database:** Local Dockerized PostgreSQL or shared dev-db.
    - **Deployments:** Triggered on every push to feature branches.
- **Staging (staging):**
    - **Purpose:** Integration testing and UAT (User Acceptance Testing).
    - **Database:** A mirrored copy of production (anonymized).
    - **Deployments:** Triggered on merge to `develop` branch. This environment is the only one with a "read-only" connection to the legacy system for verification.
- **Production (prod):**
    - **Purpose:** Live business operations.
    - **Database:** High-availability AWS RDS Cluster.
    - **Deployments:** Strictly via the Weekly Release Train.

### 6.2 The Weekly Release Train
To maintain zero downtime and system stability, Project Halcyon follows a rigid release cadence:
- **Cut-off:** Wednesday 12:00 PM. All PRs must be merged to `release` branch.
- **Testing:** Wednesday PM to Friday AM (Full regression in Staging).
- **Deployment:** Friday 10:00 PM.
- **Hotfixes:** Prohibited. Any critical bug must wait for the next Friday train unless it causes a total system outage, in which case the VP of Product (Esme Kim) must sign off manually.

### 6.3 Infrastructure Components
- **Vercel:** Hosting for Next.js frontend and serverless functions.
- **AWS S3:** Object storage for property documents.
- **AWS CloudFront:** CDN for global file distribution.
- **AWS RDS:** Managed PostgreSQL.
- **Redis:** Used for caching ML inference results to meet the <200ms p95 requirement.

---

## 7. Testing Strategy

Given the "zero downtime" requirement and the existing technical debt in the billing module, a multi-layered testing strategy is mandatory.

### 7.1 Unit Testing
- **Scope:** Individual functions, Prisma hooks, and UI components.
- **Tooling:** Vitest / Jest.
- **Requirement:** 80% coverage for all new features. 
- **Focus:** Edge cases in the Workflow Automation Engine's logic parser.

### 7.2 Integration Testing
- **Scope:** API endpoint to database flow, SSO handshake, and S3 upload pipeline.
- **Tooling:** Supertest and Playwright.
- **Focus:** Ensuring that the "Legacy Bridge" correctly maps data between the PostgreSQL and the 15-year-old system without data corruption.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "User logs in via SSO -> selects property -> triggers valuation -> downloads PDF report").
- **Tooling:** Playwright.
- **Frequency:** Run on every release train candidate.

### 7.4 Performance Testing
- **Scope:** API response times and ML inference latency.
- **Tooling:** k6.
- **Success Metric:** p95 < 200ms at a simulated load of 500 concurrent requests per second.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Key Architect leaving in 3 months | High | Critical | **Parallel-Path:** Implementing a prototype of the system using an alternative architecture simultaneously to ensure knowledge transfer and redundancy. |
| R2 | Competitor is 2 months ahead | Medium | High | **Board Escalation:** Raise as a critical blocker in the next board meeting to secure additional resources or pivot priority. |
| R3 | Legacy system failure during migration | Low | Catastrophic | **Strangler Pattern:** Move one module at a time. Keep the legacy system as the primary "Source of Truth" until Halcyon is proven. |
| R4 | SSO integration delays | Medium | High | **Mocking:** Use a mock OIDC provider in Dev/Staging to allow feature development to continue while design is finalized. |
| R5 | Technical Debt (Billing Module) | High | Medium | **Retroactive Testing:** Priority shift to implement test coverage for the core billing module before the MVP release. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required (R1).
- **Medium/High:** Active monitoring (R2, R4).
- **High/Medium:** Scheduled remediation (R5).

---

## 9. Timeline and Phases

Project Halcyon is divided into three primary phases. Due to the "unfunded" nature of the project, timelines are based on the capacity of the 20+ person cross-functional team.

### Phase 1: Foundation and Core Infrastructure (Current - March 2026)
- **Focus:** SSO Integration, File Upload Pipeline, Database Schema Setup.
- **Key Dependency:** Completion of the "Legacy Bridge" by the external data team (currently 3 weeks behind).
- **Milestone 1:** **Performance benchmarks met (Target: 2026-03-15).** We must prove the p95 < 200ms response time before moving to Alpha.

### Phase 2: Feature Expansion and Alpha (March 2026 - May 2026)
- **Focus:** Collaborative Editing, Workflow Engine (Visual Builder), and initial ML model integration.
- **Milestone 2:** **Internal alpha release (Target: 2026-05-15).** Release to a small group of internal power users.

### Phase 3: Hardening and MVP (May 2026 - July 2026)
- **Focus:** Report Generation, Billing Module Test Coverage, Final Security Pen-Testing.
- **Milestone 3:** **MVP feature-complete (Target: 2026-07-15).** Full parity with legacy system functions.

---

## 10. Meeting Notes

### Meeting 1: Weekly Status Update (2023-10-12)
- **Attendees:** Esme Kim, Thiago Moreau, Cleo Costa, Uri Oduya.
- **Notes:**
    - SSO is still "in design."
    - Thiago warns about legacy bridge latency.
    - Uri struggling with Prisma schema migrations.
    - **Decision:** Move SSO to "Critical" priority. It is now a launch blocker.

### Meeting 2: Tech Debt Sync (2023-10-19)
- **Attendees:** Esme Kim, Thiago Moreau.
- **Notes:**
    - Billing module has zero tests.
    - Deployed under pressure last quarter.
    - High risk of regression.
    - **Decision:** Allocate Uri to write basic unit tests for billing before the next release train.

### Meeting 3: Risk Assessment (2023-10-26)
- **Attendees:** Esme Kim, Leadership Team.
- **Notes:**
    - Architect leaving in 3 months.
    - Competitor "PropTech AI" is 2 months ahead.
    - Dependency on Data Team is 3 weeks behind.
    - **Decision:** Esme to bring this to the board. Prototype the "Alternative Path" for architecture immediately.

---

## 11. Budget Breakdown

As the project is bootstrapping with existing team capacity, the budget reflects operational costs and resource allocation rather than new capital spend.

| Category | Annual Allocated Cost (Est.) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $2,400,000 | 20+ staff across 3 departments (Salary split) |
| **Infrastructure** | $45,000 | Vercel Enterprise, AWS RDS, S3, CloudFront |
| **Tools** | $12,000 | JIRA, GitHub Enterprise, SendGrid, Sentry |
| **Security** | $25,000 | Quarterly external penetration testing |
| **Contingency** | $0 | No unfunded buffer; requires board approval |
| **Total** | **$2,482,000** | **Operating Expense (OpEx)** |

---

## 12. Appendices

### Appendix A: ML Model Inference Pipeline
The ML model is hosted on a separate Python-based Triton Inference Server. When a valuation request hits the Next.js API:
1. Next.js checks Redis for a cached valuation (TTL: 24 hours).
2. If not cached, it sends a gRPC request to the Triton server.
3. Triton processes the property features against the current real estate model.
4. The result is returned to Next.js, stored in PostgreSQL, cached in Redis, and served to the user.

### Appendix B: Legacy Data Mapping Table
To ensure zero downtime, we use a mapping table to synchronize the 15-year-old system and Halcyon.

| Legacy Field (COBOL) | Halcyon Field (Postgres) | Transformation Logic |
| :--- | :--- | :--- |
| `PROP-VAL-01` | `current_value` | `Decimal(10,2)` |
| `CUST-ID-NUM` | `user_id` | `UUID` cast from `Integer` |
| `ADDR-STR-99` | `address` | Trim whitespace, uppercase |
| `STATUS-CD` | `status` | Map `1`->`Active`, `2`->`Pending`, `3`->`Closed` |