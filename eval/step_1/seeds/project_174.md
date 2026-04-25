# PROJECT SPECIFICATION: PROJECT NEXUS
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 24, 2024  
**Project Lead:** Kamau Jensen  
**Company:** Bellweather Technologies  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
**Nexus** is a high-performance, real-time collaboration tool specifically engineered for the agriculture technology (AgTech) sector. Developed by Bellweather Technologies, Nexus is designed to bridge the gap between field-level data collection and corporate regulatory reporting. The project is categorized as an urgent regulatory compliance initiative, driven by upcoming federal mandates regarding agricultural runoff and soil carbon reporting. 

The project carries a hard legal deadline exactly six months from the current project start date. Failure to deploy a compliant, audited system by this date would result in significant legal penalties for Bellweather's government contracts and a loss of market eligibility for its core client base.

### 1.2 Business Justification
The AgTech industry currently lacks a unified tool that allows field agents, environmental consultants, and regulatory officers to collaborate in real-time on sensitive compliance documents while maintaining a tamper-proof audit trail. Current workflows rely on fragmented email chains and static spreadsheets, which are prone to versioning errors and lack the transparency required for FedRAMP-compliant government audits.

Nexus solves this by implementing a "Single Source of Truth" (SSOT) architecture using Elixir/Phoenix and LiveView. By providing real-time synchronization and offline capabilities, Nexus ensures that data captured in remote rural areas (with intermittent connectivity) is synchronized immediately upon regaining signal, preventing data loss and ensuring that regulatory deadlines are met.

### 1.3 ROI Projection
The budget for Nexus is set at $1.5 million. The projected Return on Investment (ROI) is calculated across three primary vectors:
1. **Risk Mitigation:** Avoiding potential regulatory fines estimated at $2.5M per annum for non-compliance across the Bellweather client portfolio.
2. **Operational Efficiency:** Reducing the "reporting cycle" from 14 days to 48 hours through automated PDF/CSV report generation and real-time collaboration, estimated to save 4,000 man-hours per year.
3. **Market Expansion:** By achieving FedRAMP authorization, Bellweather opens a new revenue stream targeting federal land management agencies, with a projected Year 1 Contract Value (ACV) of $4.2M.

The project is well-funded, allowing for an aggressive DevOps posture and a comprehensive QA strategy to ensure the p95 response time remains under 200ms, ensuring a seamless user experience for high-volume government users.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Nexus is built on a modern, highly concurrent stack designed for low latency and high availability:
- **Language/Framework:** Elixir / Phoenix (Version 1.7+)
- **Real-time Engine:** Phoenix LiveView (utilizing WebSockets for stateful connections)
- **Database:** PostgreSQL 15 (with PostGIS extension for agricultural mapping)
- **Infrastructure:** Fly.io (Global edge deployment)
- **Authentication:** OAuth2 / OpenID Connect with mandatory MFA
- **Security Standard:** FedRAMP Moderate Baseline

### 2.2 Architectural Pattern: The Transitioning Monolith
Nexus currently employs a **Modular Monolith** architecture. To ensure speed of delivery for the 6-month deadline, we are avoiding the premature complexity of microservices. However, the code is organized into "Contexts" (Bounded Contexts in Domain-Driven Design) to allow for incremental extraction into microservices as the user base grows.

**Current Module Boundaries:**
- `Nexus.Accounts`: User management, RBAC, and session handling.
- `Nexus.Collaboration`: LiveView state management and real-time synchronization.
- `Nexus.Audit`: Tamper-evident logging and hashing.
- `Nexus.Integration`: Webhook dispatchers and API gateways.
- `Nexus.Reporting`: Async PDF/CSV generation.

### 2.3 ASCII Architecture Diagram
```text
[ Client Layer ]             [ Transport ]            [ Application Layer (Fly.io) ]
+-------------------+        +------------+        +----------------------------------+
| Web Browser       | <----> | WebSockets | <----> | Phoenix LiveView (Stateful Proc)  |
| (LiveView Client) |        +------------+        |----------------------------------|
+-------------------+                              |  Modular Monolith (Elixir/OTP)    |
                                                   |  +------------------------------+ |
[ Mobile App ]               [ API/REST ]          |  |  Contexts: Accounts, Audit,  | |
| (Offline-First)   | <----> | HTTPS/TLS  | <----> |  |  Reporting, Integration       | |
+-------------------+        +------------+        |  +------------------------------+ |
                                                   +----------------------------------+
                                                                   ^
                                                                   |
                                                         [ Data Persistence Layer ]
                                                   +----------------------------------+
                                                   | PostgreSQL (Primary/Replica)       |
                                                   |  - Audit Log (Append-only)         |
                                                   |  - App Data (Relational)            |
                                                   +----------------------------------+
                                                                   ^
                                                                   |
                                                         [ External Services ]
                                                   +----------------------------------+
                                                   | Webhook Targets | SMS/Email Gateways|
                                                   +----------------------------------+
```

### 2.4 Deployment Pipeline
We utilize a **Continuous Deployment (CD)** model. 
1. **Local Dev:** Developers work on feature branches.
2. **CI:** GitHub Actions run `mix test` and `mix format`.
3. **Staging:** Automated deploy to `staging.nexus.bellweather.tech` for QA validation.
4. **Production:** Every merged PR to the `main` branch is deployed instantly to Fly.io across multiple regions using Blue-Green deployment to ensure zero downtime.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review  
**Requirement:** All changes to regulatory data must be logged in a way that cannot be retroactively altered without detection. This is a core requirement for FedRAMP compliance.

**Detailed Specification:**
The audit trail will implement a "hash-chain" mechanism. Every entry in the `audit_logs` table will contain a SHA-256 hash of the current record concatenated with the hash of the previous record. This creates a cryptographic chain. If a record is deleted or modified, the chain is broken, and the system will trigger a "Compliance Alert" to the security officer.

- **Logging Scope:** Any `INSERT`, `UPDATE`, or `DELETE` operation on tables marked as `compliance_critical`.
- **Storage:** Data is stored in a PostgreSQL table with `INSERT` only permissions for the application user; `UPDATE` and `DELETE` are prohibited at the DB level via triggers.
- **Verification:** A nightly background job (Oban worker) will re-calculate the hashes across the chain to ensure integrity.
- **User Interface:** A read-only "Audit Viewer" will allow regulators to see exactly who changed what field, at what time, from which IP address, and what the previous value was.

### 3.2 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** Complete  
**Requirement:** Third-party agricultural tools (e.g., soil sensors, drone telemetry) must be able to push data into Nexus and receive notifications when compliance states change.

**Detailed Specification:**
The framework consists of a subscription manager and a reliable delivery engine. Users can define "Webhook Subscriptions" where they specify a target URL and a set of "Trigger Events" (e.g., `report.submitted`, `audit.failure`).

- **Delivery Guarantees:** To prevent data loss, Nexus uses an internal queue. If a third-party endpoint is down (5xx error), Nexus implements an exponential backoff retry strategy (1m, 5m, 30m, 2h).
- **Security:** Each webhook payload includes an `X-Nexus-Signature` header, which is an HMAC-SHA256 signature of the payload using a secret shared between Bellweather and the client.
- **Payload Format:** Standard JSON following the CloudEvents specification to ensure interoperability.
- **Rate Limiting:** Outgoing webhooks are throttled to 50 requests per second per client to prevent overloading third-party servers.

### 3.3 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Complete  
**Requirement:** Field agents must be able to enter data in areas with zero cellular connectivity. Data must sync automatically once a connection is re-established.

**Detailed Specification:**
Nexus utilizes a "Local-First" approach leveraging IndexedDB in the browser and a synchronization engine in Elixir.

- **Client-Side Storage:** When the app detects `navigator.onLine === false`, it redirects all write operations to an IndexedDB store. Each record is assigned a temporary UUID and a timestamp.
- **Sync Protocol:** Upon regaining connectivity, the client initiates a "Sync Session." It sends a batch of pending changes to the `/api/v1/sync` endpoint.
- **Conflict Resolution:** Nexus uses a "Last-Write-Wins" (LWW) strategy by default, but for critical regulatory fields, it employs a "Semantic Merge" where the user is prompted to choose between the local version and the server version if the timestamps are within a 5-minute window.
- **Background Process:** The sync occurs in a Web Worker to ensure the UI remains responsive while large datasets are uploaded.

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** In Progress  
**Requirement:** Generate official compliance reports for government submission.

**Detailed Specification:**
The reporting engine is designed as an asynchronous pipeline to avoid blocking the Phoenix request-response cycle.

- **Generation Pipeline:**
    1. User requests a report $\rightarrow$ Request is queued via Oban.
    2. Worker fetches data from PostgreSQL and maps it to a LaTeX template (for PDF) or a CSV stream.
    3. The resulting file is uploaded to an encrypted S3 bucket.
    4. A signed, time-limited URL is generated.
- **Scheduled Delivery:** Users can set "Reporting Cadences" (Weekly, Monthly, Quarterly). The system uses a cron-like scheduler to generate these reports and email them to specified stakeholders.
- **Formatting:** PDF reports must strictly adhere to the USDA-702 formatting guidelines, including specific margins, font sizes, and mandatory headers.
- **CSV Export:** CSVs are streamed using the `csv` Elixir library to handle datasets exceeding 100k rows without causing Out-Of-Memory (OOM) errors.

### 3.5 Notification System
**Priority:** Low (Nice to Have) | **Status:** In Design  
**Requirement:** Multi-channel notifications to alert users of urgent compliance failures.

**Detailed Specification:**
The system will use a "Notification Dispatcher" pattern to decouple the event trigger from the delivery method.

- **Channels:**
    - **In-App:** Real-time toasts via Phoenix LiveView.
    - **Email:** Integration with SendGrid for formal notifications.
    - **SMS:** Integration with Twilio for urgent field alerts.
    - **Push:** Web Push API for browser-level alerts.
- **Preference Center:** Users can toggle which channels they wish to use for specific categories of alerts (e.g., "Urgent" $\rightarrow$ SMS/Push; "Informational" $\rightarrow$ Email).
- **Aggregation:** To avoid "notification fatigue," the system will batch non-urgent notifications into a daily digest.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Authorization header. Base URL: `https://api.nexus.bellweather.tech/v1`

### 4.1 `GET /collaboration/documents`
- **Description:** Retrieves a list of all active collaboration documents the user has access to.
- **Request Params:** `?limit=20&offset=0`
- **Response:**
  ```json
  {
    "data": [
      { "id": "doc_123", "title": "2025 Soil Audit", "status": "draft", "last_modified": "2024-10-20T14:00:00Z" }
    ],
    "meta": { "total": 45, "limit": 20 }
  }
  ```

### 4.2 `POST /collaboration/documents`
- **Description:** Creates a new collaboration session.
- **Request Body:** `{ "title": "New Audit", "template_id": "tmpl_88" }`
- **Response:** `201 Created` `{ "id": "doc_456", "url": "/docs/doc_456" }`

### 4.3 `PATCH /collaboration/documents/{id}`
- **Description:** Updates document content.
- **Request Body:** `{ "content": { "field_a": "Value B" }, "version": 12 }`
- **Response:** `200 OK` `{ "version": 13, "status": "synced" }`

### 4.4 `POST /integrations/webhooks/subscribe`
- **Description:** Registers a third-party URL for event notifications.
- **Request Body:** `{ "target_url": "https://client.com/webhook", "events": ["report.complete"] }`
- **Response:** `201 Created` `{ "subscription_id": "sub_999", "secret": "whsec_..." }`

### 4.5 `GET /audit/logs`
- **Description:** Fetches the tamper-evident log for a specific entity.
- **Request Params:** `?entity_id=doc_123&start_date=2024-01-01`
- **Response:**
  ```json
  {
    "logs": [
      { "id": 1, "user": "user_1", "action": "UPDATE", "hash": "a1b2c3...", "prev_hash": "f9e8d7..." }
    ]
  }
  ```

### 4.6 `POST /reports/generate`
- **Description:** Triggers an immediate report generation.
- **Request Body:** `{ "document_id": "doc_123", "format": "pdf" }`
- **Response:** `202 Accepted` `{ "job_id": "job_abc", "status": "queued" }`

### 4.7 `GET /reports/status/{job_id}`
- **Description:** Checks the status of a background report job.
- **Response:** `{ "status": "completed", "download_url": "https://s3.bellweather.tech/file.pdf" }`

### 4.8 `POST /sync/batch`
- **Description:** Bulk upload of offline-captured data.
- **Request Body:** `{ "changes": [{ "id": "tmp_1", "action": "CREATE", "data": {...} }] }`
- **Response:** `200 OK` `{ "synced_count": 12, "conflicts": [] }`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15. All tables utilize `uuid` as the primary key.

### 5.1 Tables and Relationships

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `id(PK), email, password_hash, role_id` | $\text{Many} \rightarrow \text{One}$ `roles` | User account details. |
| `roles` | `id(PK), name, permissions_json` | $\text{One} \rightarrow \text{Many}$ `users` | RBAC role definitions. |
| `documents` | `id(PK), title, created_at, owner_id` | $\text{Many} \rightarrow \text{One}$ `users` | Collaboration docs. |
| `document_versions` | `id(PK), doc_id, data_json, version_num` | $\text{Many} \rightarrow \text{One}$ `documents` | Version history. |
| `audit_logs` | `id(PK), entity_id, user_id, hash, prev_hash` | $\text{Many} \rightarrow \text{One}$ `users` | Tamper-evident log. |
| `webhook_subs` | `id(PK), client_id, target_url, secret` | $\text{Many} \rightarrow \text{One}$ `users` | Webhook configs. |
| `report_jobs` | `id(PK), doc_id, status, file_path` | $\text{Many} \rightarrow \text{One}$ `documents` | Async report tracking. |
| `schedules` | `id(PK), user_id, frequency, last_run` | $\text{Many} \rightarrow \text{One}$ `users` | Report delivery timing. |
| `offline_syncs` | `id(PK), user_id, synced_at, device_id` | $\text{Many} \rightarrow \text{One}$ `users` | Sync session history. |
| `notifications` | `id(PK), user_id, channel, read_status` | $\text{Many} \rightarrow \text{One}$ `users` | User alert history. |

### 5.2 Key Schema Details
- **`audit_logs.hash`**: Computed as $\text{SHA256}(\text{record\_data} + \text{prev\_hash})$.
- **`document_versions.data_json`**: Uses the `JSONB` type for efficient querying of nested agricultural data.
- **Indexing:** B-Tree indexes on `audit_logs.entity_id` and `document_versions.doc_id` to maintain sub-200ms read speeds.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Nexus operates across three distinct environments to ensure stability and security.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature iteration and unit testing.
- **Infrastructure:** Local Docker containers and a shared Fly.io "dev" app.
- **Database:** Ephemeral PostgreSQL instances.
- **Access:** All 12 team members.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Integration testing and QA. This environment is a mirror of production.
- **Infrastructure:** Fly.io staging cluster with limited resources.
- **Database:** Persistent PostgreSQL instance with anonymized production data.
- **Access:** Developers and Tala Moreau (QA Lead).

#### 6.1.3 Production (`prod`)
- **Purpose:** End-user live traffic.
- **Infrastructure:** Multi-region Fly.io deployment (US-East, US-West, EU-West) to minimize latency.
- **Database:** High-availability PostgreSQL cluster with synchronous replication.
- **Access:** Restricted. Only automated CD pipelines and Kamau Jensen (Tech Lead) have access.

### 6.2 FedRAMP Security Implementation
To meet government requirements:
- **Data at Rest:** AES-256 encryption for all PostgreSQL volumes.
- **Data in Transit:** TLS 1.3 mandatory for all endpoints.
- **Identity:** Integration with Okta for centralized identity management.
- **Logging:** All administrative actions are mirrored to an external, read-only S3 bucket for federal auditors.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Pure functions and individual module logic.
- **Tooling:** `ExUnit` (built-in Elixir).
- **Target:** 80% code coverage.
- **Execution:** Run on every PR via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** Communication between modules (e.g., `Nexus.Collaboration` $\rightarrow$ `Nexus.Audit`).
- **Method:** Using `Mox` for mocking external API calls (Twilio, SendGrid) and real database tests using `Ecto.Adapters.SQL`.
- **Scenario:** Testing the full flow of an offline sync $\rightarrow$ database update $\rightarrow$ audit log entry.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (The "Happy Path").
- **Tooling:** Wallaby (for LiveView) and Playwright.
- **Scenarios:** 
    1. User logs in $\rightarrow$ Creates document $\rightarrow$ Edits in offline mode $\rightarrow$ Syncs $\rightarrow$ Generates PDF.
    2. Webhook trigger $\rightarrow$ External system receives notification within 5 seconds.
- **Frequency:** Full suite run before every production deploy.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance requirements are 10x current capacity with no extra budget. | High | High | Accept the risk. Monitor weekly using Prometheus/Grafana. Optimize hot-paths in Elixir/OTP. |
| **R2** | Competitor is 2 months ahead with a similar product. | Medium | High | De-scope non-essential features (e.g., the Notification System) if unresolved by Milestone 2. |
| **R3** | Dependency on external team deliverable (3 weeks behind). | High | Medium | Establish daily sync with the other team; create mock interfaces to continue development. |
| **R4** | Technical debt: 3 different date formats in codebase. | High | Low | Implement a normalization layer in the `Nexus.Utils` module; migrate data during a planned maintenance window. |

### 8.1 Probability/Impact Matrix
- **Critical:** High Prob / High Impact (R1, R2) $\rightarrow$ Immediate attention required.
- **Major:** High Prob / Med Impact (R3, R4) $\rightarrow$ Managed via weekly sprint planning.

---

## 9. TIMELINE AND MILESTONES

The project follows an aggressive 6-month trajectory. All dates are fixed due to legal requirements.

### 9.1 Phases
1. **Phase 1: Core Infrastructure (Months 1-2):** Focus on the Modular Monolith setup, Webhook framework, and Offline-first logic.
2. **Phase 2: Compliance & Reporting (Months 3-4):** Implementation of the Tamper-evident audit trail and PDF generation.
3. **Phase 3: Hardening & Audit (Months 5-6):** FedRAMP authorization process, load testing, and final QA.

### 9.2 Key Milestones
- **Milestone 1: Performance Benchmarks Met**
  - **Target Date:** 2025-05-15
  - **Criteria:** p95 response time $< 200$ms for all API endpoints under 1,000 concurrent users.
- **Milestone 2: Internal Alpha Release**
  - **Target Date:** 2025-07-15
  - **Criteria:** Full end-to-end flow (Sync $\rightarrow$ Audit $\rightarrow$ Report) working in Staging.
- **Milestone 3: MVP Feature-Complete**
  - **Target Date:** 2025-09-15
  - **Criteria:** All "Critical" and "High" priority features verified by QA.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Baseline
**Date:** 2024-11-01 | **Attendees:** Kamau, Renzo, Tala, Kaia
**Discussion:**
- Kamau proposed the Modular Monolith. Kaia suggested jumping straight to Microservices for scalability. Kamau vetoed, citing the 6-month legal deadline; we cannot afford the network overhead and deployment complexity of 5+ services right now.
- Renzo confirmed Fly.io is the best fit for regional low-latency needs.
- Decision: Proceed with Modular Monolith.

**Action Items:**
- Kamau: Finalize Context boundaries (Done).
- Renzo: Setup Fly.io staging environment (Owner: Renzo).

### Meeting 2: Offline Sync Conflict Resolution
**Date:** 2024-12-15 | **Attendees:** Kamau, Kaia, Tala
**Discussion:**
- Kaia raised concerns about "Last-Write-Wins" (LWW) causing data loss in regulatory fields.
- Tala pointed out that for federal audits, the system must prove *who* changed *what* and *when*.
- Decision: Implement "Semantic Merging" for critical fields. If a conflict occurs on a compliance field, the system will flag the record and force a manual resolution by the project lead.

**Action Items:**
- Kaia: Implement the conflict flag in the `offline_syncs` table (Owner: Kaia).

### Meeting 3: Performance Crisis Sync
**Date:** 2025-02-10 | **Attendees:** Kamau, Renzo, Tala
**Discussion:**
- Current benchmarks show p95 at 450ms under load, failing the 200ms requirement.
- Renzo noted that the PostgreSQL indices are not optimized for the `JSONB` queries in the reporting module.
- Kamau decided that instead of adding more hardware (which is budget-prohibited), they will rewrite the reporting queries to use a materialized view updated every 15 minutes.

**Action Items:**
- Renzo: Create materialized views for the Top 5 most used reports (Owner: Renzo).
- Tala: Re-run load tests on 2025-02-17.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $1,050,000 | 12-person cross-functional team (Salaries, Contractor fees for Kaia). |
| **Infrastructure**| 15% | $225,000 | Fly.io hosting, PostgreSQL Managed DB, S3 Storage, SendGrid/Twilio. |
| **Tools & Licenses**| 5% | $75,000 | GitHub Enterprise, Okta, Datadog Monitoring, FedRAMP Audit Tooling. |
| **Contingency** | 10% | $150,000 | Emergency scaling or external security auditors for FedRAMP. |

---

## 12. APPENDICES

### Appendix A: Date Normalization Plan
Due to the technical debt of three different date formats (ISO 8601, RFC 2822, and Epoch), the team will implement the following:
1. **Normalization Layer:** All date inputs will pass through `Nexus.Utils.normalize_date/1`.
2. **Internal Standard:** All internal processing and DB storage will use `UTC` in `ISO 8601` format.
3. **Presentation Layer:** The UI will handle localization and formatting based on the user's profile settings.

### Appendix B: FedRAMP Authorization Checklist
To achieve authorization, the following must be verified during Milestone 3:
- [ ] FIPS 140-2 validated encryption modules.
- [ ] Continuous monitoring via Datadog with alerts sent to the Security Officer.
- [ ] Monthly vulnerability scans of the Fly.io environment.
- [ ] Strict RBAC (Role-Based Access Control) implementation with "Least Privilege" principle.
- [ ] Documented System Security Plan (SSP).