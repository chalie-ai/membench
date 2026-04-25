Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, industrial-grade Technical Specification Document (TSD). It expands every provided constraint into a granular operational framework.

***

# PROJECT CANOPY: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4-RC1  
**Status:** Draft for Engineering Review  
**Last Updated:** 2024-10-24  
**Classification:** Internal / Confidential / FedRAMP-Candidate  
**Company:** Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Canopy** is a strategic cybersecurity monitoring dashboard designed specifically for the logistics and shipping vertical. Coral Reef Solutions currently operates four redundant internal monitoring tools—*SentryLog, PortWatch, CargoShield, and NexusSentry*—each with overlapping functionality, separate licensing costs, and disparate data silos. Canopy is a cost-reduction initiative aimed at consolidating these four legacy tools into a single, unified "glass pane" for security operations.

The primary business driver is the reduction of operational overhead. By eliminating four separate maintenance streams and converging them into a Rust-based monolith, Coral Reef Solutions expects to reduce the total cost of ownership (TCO) for its monitoring infrastructure by 40% annually.

### 1.2 Business Justification
In the logistics industry, downtime at a single port or a breach in a shipping manifesto can result in millions of dollars in losses. The current fragmented toolset leads to "alert fatigue" and delayed response times due to context switching between tools. Canopy addresses this by providing a centralized hub for real-time threat detection, automated response, and collaborative incident management.

Furthermore, the project is designed to facilitate entry into government-contracted shipping lanes, which require **FedRAMP authorization**. The current legacy tools do not meet these stringent federal security standards; Canopy is being built from the ground up to ensure compliance, thereby unlocking previously inaccessible revenue streams.

### 1.3 ROI Projection
The financial goals for Canopy are aggressive given the "shoestring" budget of $150,000.
- **Direct Cost Savings:** Elimination of $60,000/year in legacy licensing and server maintenance.
- **Revenue Growth:** The primary success metric is the attribution of **$500,000 in new revenue** within 12 months post-launch, driven by the ability to bid on FedRAMP-compliant government logistics contracts.
- **Efficiency Gain:** Expected reduction in Mean Time to Resolution (MTTR) for security incidents by 35% due to the unified interface and automated workflow engine.

### 1.4 Project Constraints
The project is operating under extreme financial scrutiny. With a total budget of $150,000, there is zero margin for infrastructure over-provisioning. The team is distributed across five countries (USA, Switzerland, India, Poland, and Brazil), necessitating a high-trust, low-ceremony communication model focused on Slack-driven decision-making to avoid the latency of formal bureaucratic approvals.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Canopy is architected as a **Clean Monolith**. While the industry trend leans toward microservices, the budget and team size make a distributed system untenable. Instead, Canopy uses a modular monolithic approach where the Rust backend is divided into strictly bounded contexts (Auth, Automation, Scanning, Integration) to allow for potential future splitting without rewriting the core logic.

**The Stack:**
- **Backend:** Rust (Tokio runtime, Axum framework) for memory safety and high performance.
- **Frontend:** React 18 (TypeScript) with Tailwind CSS for a responsive, low-latency dashboard.
- **Edge Layer:** Cloudflare Workers for global request routing and caching.
- **Database:** SQLite for edge caching and local state, with a centralized PostgreSQL instance (referenced in schema) for the primary system of record.

### 2.2 Architecture Diagram (ASCII)
```text
[ USER BROWSER ] <------> [ CLOUDFLARE WORKERS (Edge) ]
                                     |
                                     v
                          [ REACT FRONTEND (SPA) ]
                                     |
                                     v
                          [ RUST BACKEND (Monolith) ]
                               /     |     \
       _______________________/      |      \_______________________
      |                              |                              |
 [ AUTH MODULE ]             [ WORKFLOW ENGINE ]           [ INTEGRATION HUB ]
 (RBAC/FedRAMP)              (Visual Rule Builder)         (Webhooks/Third-Party)
      |                              |                              |
      \______________________________v______________________________/
                                     |
                          [ SQLITE EDGE CACHE ] <---> [ PRIMARY DB (Postgres) ]
                                     |
                          [ FILE SYSTEM / S3 BUCKET ]
                          (Virus Scanning / CDN Dist)
```

### 2.3 Design Philosophy
- **Performance First:** Due to the 10x capacity requirement (see Risks), Rust was chosen to minimize CPU and memory overhead.
- **Manual QA Gates:** To ensure FedRAMP compliance and stability, no code reaches production without a manual sign-off from Renzo Vasquez-Okafor. This creates a 2-day turnaround for deployments.
- **Data Locality:** Using SQLite at the edge allows for rapid read-access to common dashboard metrics without hitting the primary database for every request.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
This feature is the bedrock of the system's security. Because Canopy handles sensitive shipping and security data, it must implement a strict RBAC model that satisfies FedRAMP requirements. The system must support Multi-Factor Authentication (MFA) and integrate with existing corporate identity providers via SAML/OIDC.

**Functional Requirements:**
- **Granular Permissions:** Permissions must be defined at the action level (e.g., `view_logs`, `edit_workflow`, `delete_user`).
- **Role Hierarchy:** Roles include `SuperAdmin`, `SecurityAnalyst`, `Auditor`, and `ReadOnly`.
- **Session Management:** JWT-based authentication with short-lived access tokens (15 mins) and longer-lived refresh tokens (7 days) stored in HttpOnly cookies.
- **Audit Logging:** Every authentication event and permission change must be logged to an immutable audit table for compliance.

**Technical Constraints:**
- Password hashing must utilize Argon2id.
- All authentication requests must be routed through the Cloudflare Worker edge to mitigate brute-force attacks via rate limiting.

### 3.2 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Complete

**Description:**
The automation engine allows users to define "If-This-Then-That" (IFTTT) logic to handle security threats automatically. For example, "If a login is detected from an unauthorized IP in the Port of Singapore AND the user is not on the whitelist, THEN block the IP and alert the on-call analyst."

**Functional Requirements:**
- **Visual Builder:** A drag-and-drop interface where users can connect "Triggers" (e.g., Webhook, Scheduled Time, Log Event) to "Actions" (e.g., Send Email, Block IP, Trigger Webhook).
- **Logic Gates:** Support for AND/OR/NOT operators within the rule builder.
- **Execution Sandbox:** Rules are executed in a restricted Rust environment to prevent a malicious or poorly written rule from crashing the monolith.
- **Version Control:** Each workflow version must be saved, allowing users to roll back to a previous version of a rule.

**Technical Constraints:**
- The engine uses a Directed Acyclic Graph (DAG) to represent the workflow, ensuring no infinite loops occur during execution.

### 3.3 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Blocked

**Description:**
Security analysts often work in teams during a "War Room" scenario. This feature allows multiple users to edit an incident report or a workflow rule simultaneously, with changes reflecting in real-time across all screens.

**Functional Requirements:**
- **Operational Transformation (OT) or CRDT:** The system must implement Conflict-free Replicated Data Types (CRDTs) to ensure that concurrent edits merge without data loss.
- **Presence Indicators:** Users must see who else is currently editing the document (cursors and avatars).
- **Latency Compensation:** Local changes must be applied immediately to the UI, with background synchronization to the Rust backend.

**Technical Constraints:**
- **Blocking Issue:** Currently blocked due to a fundamental design disagreement between the Product Lead and Engineering Lead regarding the use of WebSockets vs. Server-Sent Events (SSE) for the synchronization layer.
- **Performance:** Must support up to 50 concurrent editors per document without noticeable lag.

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low (Nice to have) | **Status:** In Progress

**Description:**
Users need to upload evidence files (PCAP files, logs, screenshots) related to security incidents. To prevent the dashboard from becoming a vector for malware, all uploads must be scanned before being made available to other users.

**Functional Requirements:**
- **Scanning Pipeline:** Integration with an antivirus API (e.g., ClamAV or Virustotal) to scan files upon upload.
- **Quarantine Zone:** Files are uploaded to a "quarantine" S3 bucket and moved to the "clean" bucket only after a positive scan result.
- **CDN Distribution:** Once cleaned, files are distributed via Cloudflare R2/CDN for low-latency retrieval by analysts globally.
- **File Type Validation:** Strict MIME type checking to prevent execution of malicious scripts on the frontend.

**Technical Constraints:**
- Maximum file size limit: 50MB.
- Scanning must happen asynchronously to avoid blocking the main request thread.

### 3.5 Webhook Integration Framework for Third-Party Tools
**Priority:** Low (Nice to have) | **Status:** In Design

**Description:**
To avoid being a silo, Canopy must communicate with other tools (Slack, Jira, PagerDuty). The webhook framework allows Canopy to push alerts to external systems and receive triggers from them.

**Functional Requirements:**
- **Outgoing Webhooks:** Customizable JSON payloads that can be sent to any HTTPS endpoint when a specific workflow trigger is met.
- **Incoming Webhooks:** Dedicated endpoints for third-party tools to push data into Canopy, which then triggers the Workflow Automation Engine.
- **Secret Management:** Support for HMAC signatures to verify that incoming webhooks actually originate from the trusted third-party provider.
- **Retry Logic:** Exponential backoff for failed webhook deliveries to ensure reliability.

**Technical Constraints:**
- Must implement a queue-based system (using an internal Rust channel or Redis) to handle bursts of incoming webhooks without impacting dashboard performance.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /auth/login`
- **Description:** Authenticates a user and returns a session token.
- **Request Body:**
  ```json
  {
    "username": "j.doe@coralreef.com",
    "password": "hashed_password_here",
    "mfa_token": "123456"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGci...",
    "refresh_token": "def456...",
    "expires_in": 900
  }
  ```

### 4.2 `GET /dashboard/metrics`
- **Description:** Retrieves real-time security metrics for the main dashboard view.
- **Query Params:** `timeframe=1h` or `timeframe=24h`.
- **Response (200 OK):**
  ```json
  {
    "active_threats": 12,
    "system_load": "14%",
    "blocked_ips": 450,
    "pending_alerts": 8
  }
  ```

### 4.3 `POST /workflows/create`
- **Description:** Saves a new automation rule defined in the visual builder.
- **Request Body:**
  ```json
  {
    "name": "Port-SNG-Block",
    "trigger": { "type": "log_event", "pattern": "Unauthorized-SNG" },
    "actions": [ { "type": "block_ip", "scope": "global" } ]
  }
  ```
- **Response (201 Created):**
  ```json
  { "workflow_id": "wf_99821", "status": "active" }
  ```

### 4.4 `GET /workflows/{id}`
- **Description:** Retrieves the configuration for a specific workflow.
- **Response (200 OK):**
  ```json
  {
    "id": "wf_99821",
    "version": 2,
    "config": { ... }
  }
  ```

### 4.5 `POST /files/upload`
- **Description:** Uploads a file for virus scanning.
- **Request:** Multipart/form-data.
- **Response (202 Accepted):**
  ```json
  {
    "file_id": "file_abc123",
    "scan_status": "pending",
    "polling_url": "/api/v1/files/status/file_abc123"
  }
  ```

### 4.6 `GET /files/status/{id}`
- **Description:** Checks if the uploaded file has passed the virus scan.
- **Response (200 OK):**
  ```json
  {
    "file_id": "file_abc123",
    "status": "clean",
    "url": "https://cdn.coralreef.com/files/abc123"
  }
  ```

### 4.7 `POST /webhooks/register`
- **Description:** Registers a third-party URL to receive Canopy alerts.
- **Request Body:**
  ```json
  {
    "target_url": "https://hooks.slack.com/services/...",
    "event_types": ["critical_alert", "user_login"]
  }
  ```
- **Response (201 Created):**
  ```json
  { "webhook_id": "wh_772", "secret": "shhh_secret_key" }
  ```

### 4.8 `DELETE /auth/logout`
- **Description:** Invalidates the current session and refresh token.
- **Response (204 No Content):** Empty.

---

## 5. DATABASE SCHEMA

The system utilizes a relational structure. While SQLite is used at the edge for caching, the source of truth is a PostgreSQL database.

### 5.1 Tables and Relationships

1.  **`users`**: Stores identity and credential metadata.
    - `user_id` (UUID, PK)
    - `username` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `mfa_secret` (TEXT)
    - `created_at` (Timestamp)
2.  **`roles`**: Definition of available roles.
    - `role_id` (INT, PK)
    - `role_name` (VARCHAR) - e.g., 'SuperAdmin'
3.  **`user_roles`**: Junction table mapping users to roles.
    - `user_id` (UUID, FK)
    - `role_id` (INT, FK)
4.  **`permissions`**: List of all granular actions.
    - `perm_id` (INT, PK)
    - `perm_key` (VARCHAR) - e.g., 'edit_workflow'
5.  **`role_permissions`**: Maps roles to their specific permissions.
    - `role_id` (INT, FK)
    - `perm_id` (INT, FK)
6.  **`workflows`**: Stores the DAG configuration for automation.
    - `workflow_id` (UUID, PK)
    - `name` (VARCHAR)
    - `definition` (JSONB)
    - `is_active` (BOOLEAN)
    - `created_by` (UUID, FK)
7.  **`workflow_versions`**: History of rule changes for audit/rollback.
    - `version_id` (INT, PK)
    - `workflow_id` (UUID, FK)
    - `definition` (JSONB)
    - `created_at` (Timestamp)
8.  **`security_events`**: The primary log of all intercepted threats.
    - `event_id` (BIGINT, PK)
    - `severity` (ENUM: Low, Med, High, Critical)
    - `source_ip` (INET)
    - `payload` (JSONB)
    - `timestamp` (Timestamp)
9.  **`files`**: Metadata for uploaded evidence files.
    - `file_id` (UUID, PK)
    - `filename` (VARCHAR)
    - `scan_result` (ENUM: Pending, Clean, Infected)
    - `s3_path` (TEXT)
    - `uploaded_by` (UUID, FK)
10. **`audit_logs`**: Immutable record of all system changes.
    - `log_id` (BIGINT, PK)
    - `user_id` (UUID, FK)
    - `action` (TEXT)
    - `timestamp` (Timestamp)
    - `ip_address` (INET)

### 5.2 Schema Notes
- **Technical Debt Warning:** Approximately 30% of queries currently bypass the ORM and use **raw SQL** for performance optimization. This is specifically present in the `security_events` and `audit_logs` tables due to high ingestion rates. Migrations on these tables are high-risk and require manual verification by Uri Kowalski-Nair.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Canopy uses a three-tier environment strategy to ensure stability before reaching government clients.

**1. Development (Dev):**
- **Purpose:** Feature development and iterative testing.
- **Host:** Local Docker containers and a shared staging server in AWS (US-East-1).
- **Database:** SQLite for rapid prototyping.
- **Deployment:** Continuous integration via GitHub Actions; auto-deploys on merge to `develop`.

**2. Staging (QA):**
- **Purpose:** Final validation, FedRAMP compliance checks, and User Acceptance Testing (UAT).
- **Host:** Dedicated instance mirroring production hardware.
- **Database:** PostgreSQL (Staging instance).
- **Deployment:** Triggered after `develop` is merged to `release`. This environment has the **Manual QA Gate**. Renzo Vasquez-Okafor must sign off on all tickets before they are promoted.

**3. Production (Prod):**
- **Purpose:** Live monitoring for Coral Reef Solutions.
- **Host:** Hardened instances with strict network isolation.
- **Database:** PostgreSQL (Production cluster with failover).
- **Deployment:** Manual deployment process. 2-day turnaround window to allow for final sanity checks and stakeholder notification.

### 6.2 Infrastructure Details
- **Edge:** Cloudflare Workers handle SSL termination and initial request filtering.
- **Caching:** SQLite is deployed at the edge to cache the last 100 critical alerts for immediate dashboard loading.
- **Storage:** Files are stored in Cloudflare R2 (S3 compatible) to avoid high egress fees.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** All Rust backend logic, specifically the Workflow Engine's DAG parser and the RBAC permission checker.
- **Tooling:** `cargo test`.
- **Requirement:** 80% code coverage for core business logic.

### 7.2 Integration Testing
- **Scope:** API endpoints and database interactions.
- **Approach:** Spinning up a temporary PostgreSQL container to test the 30% of queries that use raw SQL, ensuring that schema changes do not break these queries.
- **Focus:** Validating the flow from `POST /auth/login` $\rightarrow$ `GET /dashboard/metrics`.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., creating a workflow, uploading a file and seeing it marked as "Clean").
- **Tooling:** Playwright/Cypress.
- **Environment:** Run exclusively in the Staging environment.

### 7.4 Compliance Testing (FedRAMP)
- **Scope:** Vulnerability scanning, penetration testing, and audit log verification.
- **Frequency:** Monthly.
- **Requirement:** Must pass an external security audit on the first attempt to meet the success criteria.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements are 10x current system capacity with no extra budget. | High | Critical | Escalate to steering committee for additional funding; optimize Rust code via `SIMD` and raw SQL. |
| R-02 | Key Architect is leaving the company in 3 months. | Certain | High | Raise as a blocker in the next board meeting; prioritize knowledge transfer and documentation. |
| R-03 | Design disagreement between Product and Engineering leads. | Medium | Medium | Resolve via a time-boxed "technical spike" and a final decision by Arjun Vasquez-Okafor. |
| R-04 | Raw SQL bypass makes migrations dangerous. | High | Medium | Implement strict manual review for all migrations; write specialized integration tests for raw SQL queries. |
| R-05 | FedRAMP audit failure. | Low | Critical | Weekly compliance reviews and internal "pre-audits" by Beau Blackwood-Diallo. |

---

## 9. TIMELINE & MILESTONES

The project follows a phased approach with strict dependencies.

### 9.1 Phase 1: Core Infrastructure (Now - Feb 2025)
- **Focus:** RBAC completion, Backend Monolith stabilization, and Database schema finalization.
- **Dependency:** User Auth must be complete before Workflow Engine can be fully tested in Staging.

### 9.2 Phase 2: Beta & Hardening (Feb 2025 - April 2025)
- **Focus:** Solving the Collaborative Editing blocker and finalizing the File Upload pipeline.
- **Milestone 1: Post-launch stability confirmed (Target: 2025-04-15).**

### 9.3 Phase 3: Compliance & UAT (April 2025 - June 2025)
- **Focus:** External audit preparation and Stakeholder walkthroughs.
- **Milestone 2: Stakeholder demo and sign-off (Target: 2025-06-15).**

### 9.4 Phase 4: Production Rollout (June 2025 - August 2025)
- **Focus:** Gradual migration of users from the 4 legacy tools to Canopy.
- **Milestone 3: Production launch (Target: 2025-08-15).**

---

## 10. MEETING NOTES (EXCERPTS)

*Note: These are extracted from the shared running document (200+ pages, unsearchable).*

### Meeting 1: "The Architecture Brawl" (Date: 2024-08-12)
- **Attendees:** Arjun, Uri, Beau.
- **Discussion:** Beau (Consultant from Zürich) argued that the 10x performance requirement cannot be met with the current PostgreSQL indexing strategy. Uri suggested bypassing the ORM for the `security_events` table to save milliseconds.
- **Decision:** Arjun approved the raw SQL approach for high-traffic tables.
- **Action Item:** Uri to document all raw SQL queries in the schema section to prevent migration disasters.

### Meeting 2: "The Collaborative Editing Deadlock" (Date: 2024-09-05)
- **Attendees:** Arjun, Uri, Renzo.
- **Discussion:** Huge disagreement on the sync layer. Product wants the simplicity of SSE (Server-Sent Events), but Engineering (Uri) insists on WebSockets for true bi-directional real-time editing.
- **Outcome:** No decision reached. Feature marked as **BLOCKED**.
- **Note:** Arjun mentioned he has to leave early for a paramedic shift.

### Meeting 3: "Budget Panic & FedRAMP" (Date: 2024-10-01)
- **Attendees:** Arjun, Beau, Corporate Finance.
- **Discussion:** Finance questioned why the budget is $150k when the expected revenue is $500k. Beau explained that the "shoestring" budget is due to the consolidation nature of the project (cost-reduction).
- **Decision:** Budget remains capped at $150k. Any one-time overages for FedRAMP certification must be fought for at the board level.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $90,000 | Distributed team (15 members). Lower cost due to regional salary variances. |
| **Infrastructure** | $25,000 | Cloudflare Workers, R2 Storage, and AWS PostgreSQL instances. |
| **Security Tools** | $15,000 | Virus scanning API licenses and FedRAMP pre-audit consulting. |
| **Tooling/Software** | $10,000 | IDE licenses, Slack Pro, GitHub Enterprise. |
| **Contingency** | $10,000 | Emergency buffer for critical hardware failures or legal fees. |

**Financial Note:** Every dollar is scrutinized. Any expenditure over $500 requires direct approval from Arjun Vasquez-Okafor via Slack.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (CRDT Specification)
For the blocked Collaborative Editing feature, the team will evaluate the **LWW-Element-Set (Last-Write-Wins)** approach.
- **State:** Each character/block in a document will be assigned a timestamp and a unique author ID.
- **Merge:** When two versions of a document arrive at the server, the one with the higher timestamp wins.
- **Complexity:** $O(n)$ for merge operations, where $n$ is the number of concurrent edits.

### Appendix B: FedRAMP Controls Mapping
To achieve authorization, Canopy must implement the following NIST 800-53 controls:
- **AC-2 (Account Management):** Handled by the RBAC module and the `users` table.
- **AU-2 (Event Logging):** Handled by the `audit_logs` table, which must be write-once, read-many.
- **SC-8 (Transmission Confidentiality):** All traffic enforced via TLS 1.3 through Cloudflare Workers.
- **SI-2 (Flaw Remediation):** Handled by the 2-day manual QA gate and patching cycle.