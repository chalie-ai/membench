Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. To maintain the required depth and technical rigor, it is structured as a living technical manual for the Silverthread AI development team.

***

# PROJECT SPECIFICATION: LATTICE
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / Board-Approved  
**Classification:** Confidential / ISO 27001 Restricted  
**Project Lead:** Asha Gupta (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Lattice** is a high-stakes strategic initiative by Silverthread AI to penetrate the aerospace industry by providing a specialized healthcare records platform. Unlike general-purpose Electronic Health Records (EHR), Lattice is engineered specifically for the unique physiological and psychological monitoring requirements of aerospace personnel—pilots, astronauts, and ground crew—where health data directly impacts flight safety and mission viability.

The project is driven by a cornerstone enterprise agreement with a primary aerospace client who has committed to an annual recurring revenue (ARR) of **$2,000,000**. Given the criticality of the industry, Lattice must adhere to the most stringent data integrity and availability standards, utilizing a cutting-edge stack of Rust, React, and Cloudflare Workers to ensure near-zero latency and absolute type safety.

### 1.2 Business Justification
The aerospace sector currently relies on fragmented, legacy systems for medical record-keeping that do not integrate with real-time telemetry or modern diagnostic tools. By introducing a high-performance, offline-first healthcare platform, Silverthread AI positions itself as the indispensable infrastructure provider for aerospace health management. 

The business justification rests on three pillars:
1.  **Immediate Revenue:** A guaranteed $2M ARR from the anchor client.
2.  **Strategic Verticalization:** Establishing a footprint in the aerospace sector allows Silverthread AI to expand into defense and high-altitude commercial travel.
3.  **Technological Moat:** By implementing a CQRS architecture with event sourcing, Silverthread AI creates an audit trail that exceeds FAA and EASA regulatory requirements, making it difficult for competitors to displace the product once integrated.

### 1.3 ROI Projection and Financial Goals
With a total project budget exceeding **$5,000,000**, the ROI is calculated based on the initial contract and projected market expansion. 

*   **Year 1 Projection:** The primary goal is the stabilization of the anchor account ($2M) and the acquisition of an additional $500K in new revenue through secondary aerospace contracts.
*   **Cost Recovery:** Based on personnel costs and infrastructure, the project is expected to reach a break-even point within 30 months of the Internal Alpha release.
*   **Success Metrics:** 
    *   **NPS Target:** >40 within Q1 post-launch.
    *   **Revenue Target:** $500K in new, non-anchor revenue within 12 months of Milestone 2.

### 1.4 Strategic Alignment
Lattice is a "flagship initiative," meaning it reports directly to the board of Silverthread AI. The project serves as a proof-of-concept for the company's ability to deploy high-reliability Rust-based systems in regulated environments.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level System Design
Lattice utilizes a **Command Query Responsibility Segregation (CQRS)** pattern. This is non-negotiable due to the "audit-critical" nature of aerospace healthcare records; every change to a medical record must be immutable and traceable to a specific timestamp and actor.

#### 2.1.1 The Event Store
The "Source of Truth" is an Event Store. When a doctor updates a record, the system does not overwrite the row in a database. Instead, it appends an event (e.g., `MedicalRecordUpdatedEvent`) to the stream. The "Read Model" (Projected State) is then updated asynchronously.

#### 2.1.2 Tech Stack Breakdown
*   **Backend:** Rust (Axum framework). Chosen for memory safety, concurrency, and performance.
*   **Frontend:** React 18+ with TypeScript.
*   **Edge Layer:** Cloudflare Workers. This ensures that health records are served from the edge, reducing latency for global aerospace teams.
*   **Local Storage:** SQLite (via WASM) for the "Offline-First" capability, allowing medics to record data in aircraft or remote sites without internet.

### 2.2 Architecture Diagram (ASCII)

```text
[ Client Browser/App ] <------> [ Cloudflare Workers (Edge) ]
       |                               |
       | (Offline Sync)                | (API Requests)
       v                               v
 [ SQLite (Local) ]            [ Rust Backend (Axum) ]
                                      |
          _____________________________|_____________________________
         |                            |                              |
   [ Command Bus ]             [ Query Bus ]                [ Event Store ]
         |                            |                             |
  (Write Action)               (Read Projection)             (Immutable Log)
         |                            |                             |
         v                            v                            v
 [ Event Sourcing ] ---------> [ Read-Optimized DB ] <------- [ Audit Trail ]
                                (PostgreSQL/KV)
```

### 2.3 Data Flow Logic
1.  **Command Path:** User submits a change $\rightarrow$ Rust Backend validates $\rightarrow$ Event is persisted to Event Store $\rightarrow$ Event is dispatched to projection engine.
2.  **Query Path:** User requests a record $\rightarrow$ Cloudflare Worker checks cache $\rightarrow$ Query Bus fetches the pre-computed "Read Model" $\rightarrow$ Data returned.
3.  **Sync Path:** Local SQLite changes $\rightarrow$ Background worker detects connectivity $\rightarrow$ Batched events pushed to Rust Backend $\rightarrow$ Conflict resolution via vector clocks.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 SSO Integration with SAML and OIDC (Priority: High)
**Status:** In Design | **Lead:** Anders Costa

#### 3.1.1 Functional Requirements
The platform must integrate with existing aerospace corporate directories. Because the client uses a mix of Azure AD and custom Okta implementations, Lattice must support both Security Assertion Markup Language (SAML 2.0) and OpenID Connect (OIDC).

*   **Identity Provider (IdP) Configuration:** Administrators must be able to configure metadata URLs, Entity IDs, and X.509 certificates within the Lattice Admin Panel.
*   **Just-In-Time (JIT) Provisioning:** When a user authenticates via SSO for the first time, the system should automatically create a user profile based on the SAML assertions (Name, Email, Role, Department).
*   **Session Management:** JWTs (JSON Web Tokens) will be used for session persistence, with a maximum TTL of 8 hours for medical staff and 24 hours for administrative staff.
*   **Multi-Factor Authentication (MFA):** While the IdP handles MFA, Lattice must be able to request "step-up" authentication for critical actions (e.g., deleting a record).

#### 3.1.2 Technical Implementation
The Rust backend will implement a middleware layer that intercepts requests to `/api/v1/auth`. The `saml-rs` crate will be used for parsing assertions. For OIDC, the system will utilize a standard OAuth2 flow with PKCE (Proof Key for Code Exchange) to ensure security on the frontend.

#### 3.1.3 Acceptance Criteria
*   Successful login using the client's Azure AD tenant.
*   Automatic mapping of "Chief Medical Officer" group in Okta to "Admin" role in Lattice.
*   Logout from Lattice triggers a global sign-out from the IdP.

---

### 3.2 Offline-First Mode with Background Sync (Priority: Medium)
**Status:** Not Started | **Lead:** Vera Jensen

#### 3.2.1 Functional Requirements
Aerospace environments often include "dark zones" (e.g., flight decks, remote hangers) where internet connectivity is intermittent. Lattice must allow full read/write access to assigned records while offline.

*   **Local Cache:** The application will use SQLite compiled to WebAssembly (WASM) to store a subset of the user's assigned patient records.
*   **Optimistic UI:** When a user saves a record offline, the UI must immediately reflect the change and mark the record with a "Pending Sync" icon.
*   **Conflict Resolution:** Since multiple medics might edit a record, the system will use **Last-Write-Wins (LWW)** for non-critical fields and **Semantic Merging** for clinical notes.
*   **Background Synchronization:** Using the Service Worker API, the app will detect the `online` event and initiate a batch upload of all pending events in the local SQLite queue.

#### 3.2.2 Technical Implementation
The frontend will implement a "Sync Manager" that queues all mutating actions as "Command Objects." These objects are stored in a local SQLite table `sync_queue`. Upon reconnection, the manager performs a `POST /api/v1/sync` request containing the array of events.

#### 3.2.3 Acceptance Criteria
*   User can create a new medical entry while in Airplane Mode.
*   Data persists after a browser refresh while still offline.
*   Data is successfully pushed to the server within 5 seconds of regaining connectivity.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder (Priority: Low)
**Status:** In Review | **Lead:** Asha Gupta

#### 3.3.1 Functional Requirements
This feature allows administrators to automate healthcare alerts. For example: "If Blood Pressure > 140/90 AND Pilot Age > 45, trigger an immediate review by the Flight Surgeon."

*   **Visual Rule Builder:** A drag-and-drop interface using React Flow to define triggers, conditions, and actions.
*   **Triggers:** Events such as `RecordCreated`, `ValueUpdated`, or `ScheduledTime`.
*   **Conditions:** Boolean logic gates (AND, OR, NOT) comparing record values against thresholds.
*   **Actions:** Sending an email, pushing a notification, or flagging a record for "Urgent Review."

#### 3.3.2 Technical Implementation
The engine will utilize a "Rule Engine" written in Rust. Rules will be stored as JSON-logic trees in the database. When an event is fired in the CQRS stream, the Rule Engine evaluates all active rules against the event payload.

#### 3.3.3 Acceptance Criteria
*   Admin can create a rule that sends a notification when a specific health metric exceeds a threshold.
*   The rule triggers within 60 seconds of the data being entered.

---

### 3.4 PDF/CSV Report Generation with Scheduled Delivery (Priority: Low)
**Status:** Not Started | **Lead:** Ines Kim (QA)

#### 3.4.1 Functional Requirements
The aerospace client requires monthly health compliance reports for regulatory bodies.

*   **Template Engine:** Support for custom HTML/CSS templates that are converted to PDF via a headless browser (Chromium).
*   **Scheduled Delivery:** A cron-like scheduler where admins can set reports to be emailed to stakeholders on the 1st of every month.
*   **CSV Export:** Raw data export for use in external statistical software (e.g., R or SPSS).
*   **Secure Delivery:** PDFs must be encrypted with AES-256 and delivered via a secure link rather than as an email attachment.

#### 3.4.2 Technical Implementation
A dedicated "Reporting Service" will be spun up as a separate worker. It will query the "Read Model" database, populate the template, and upload the resulting file to an encrypted S3 bucket.

#### 3.4.3 Acceptance Criteria
*   Generate a PDF report for a single pilot that matches the regulatory layout.
*   Successfully schedule a report to fire at a specific UTC timestamp.

---

### 3.5 Data Import/Export with Format Auto-Detection (Priority: Low)
**Status:** Not Started | **Lead:** Anders Costa

#### 3.5.1 Functional Requirements
The client has legacy data in various formats (HL7, FHIR, custom CSVs). Lattice must facilitate the migration of this data.

*   **Format Auto-Detection:** The system should analyze the first 100 lines of an uploaded file to determine if it is CSV, JSON, or HL7.
*   **Mapping Interface:** A UI that allows the user to map columns from the uploaded file to the Lattice database fields.
*   **Validation Step:** A "Dry Run" mode that flags errors (e.g., invalid date formats) before committing the data to the Event Store.
*   **Bulk Export:** Ability to export all patient records in FHIR (Fast Healthcare Interoperability Resources) format.

#### 3.5.2 Technical Implementation
The Rust backend will use a "Parser Factory" pattern. Based on the detected file type, the system instantiates a specific parser (`Hl7Parser`, `CsvParser`) that transforms the input into a standardized `InternalRecord` struct.

#### 3.5.3 Acceptance Criteria
*   Upload a CSV file and have the system correctly identify it as "CSV".
*   Successfully import 1,000 records without data loss or corruption.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1`. Authentication requires a Bearer JWT in the header.

### 4.1 Authentication & Session
**`POST /api/v1/auth/login`**
*   **Description:** Exchanges credentials or SSO tokens for a session JWT.
*   **Request:** `{ "provider": "saml", "token": "SAML_RESPONSE_STRING" }`
*   **Response:** `200 OK { "token": "eyJ...", "expires_at": "2023-10-25T10:00:00Z" }`

**`POST /api/v1/auth/logout`**
*   **Description:** Invalidates the current session.
*   **Response:** `204 No Content`

### 4.2 Patient Records (Command Side)
**`POST /api/v1/records`**
*   **Description:** Creates a new medical record event.
*   **Request:** `{ "patient_id": "P-102", "metric": "blood_pressure", "value": "120/80", "timestamp": "2023-10-24T12:00:00Z" }`
*   **Response:** `201 Created { "event_id": "ev_99823", "status": "pending_projection" }`

**`PUT /api/v1/records/{record_id}`**
*   **Description:** Updates an existing record (creates a new event in the stream).
*   **Request:** `{ "value": "130/85", "reason": "Correction of typo" }`
*   **Response:** `200 OK { "version": 2, "event_id": "ev_99824" }`

### 4.3 Patient Records (Query Side)
**`GET /api/v1/records/{patient_id}`**
*   **Description:** Fetches the current state of a patient's health record.
*   **Response:** `200 OK { "patient_id": "P-102", "current_metrics": { "blood_pressure": "130/85", "heart_rate": "72" }, "history": [...] }`

**`GET /api/v1/records/search?q={query}`**
*   **Description:** Searches for patients by name or ID.
*   **Response:** `200 OK { "results": [ { "id": "P-102", "name": "John Doe" } ] }`

### 4.4 System & Administration
**`GET /api/v1/system/health`**
*   **Description:** Checks the health of the backend and database connections.
*   **Response:** `200 OK { "status": "healthy", "uptime": "45d", "db_connection": "ok" }`

**`POST /api/v1/sync/batch`**
*   **Description:** Endpoint for offline-first background synchronization.
*   **Request:** `{ "batch_id": "b-552", "events": [ { "type": "UPDATE", "payload": {...} }, { "type": "CREATE", "payload": {...} } ] }`
*   **Response:** `200 OK { "synced_count": 12, "conflicts": 0 }`

---

## 5. DATABASE SCHEMA

Lattice uses a polyglot persistence strategy: **Event Store (Append-only)** and **Read Model (Relational)**.

### 5.1 Event Store (The Source of Truth)
**Table: `event_log`**
*   `event_id` (UUID, PK): Unique identifier for the event.
*   `aggregate_id` (UUID, Index): The ID of the patient or entity.
*   `event_type` (String): e.g., `RECORD_CREATED`, `METRIC_UPDATED`.
*   `payload` (JSONB): The actual data of the change.
*   `timestamp` (DateTime, Index): When the event occurred.
*   `version` (Integer): Sequence number for the aggregate.
*   `user_id` (UUID): Who performed the action.

### 5.2 Read Model (Optimized for Queries)
**Table: `patients`**
*   `patient_id` (UUID, PK)
*   `full_name` (String)
*   `dob` (Date)
*   `aerospace_role` (String): e.g., "Pilot", "Engineer".
*   `created_at` (DateTime)

**Table: `medical_metrics`**
*   `metric_id` (UUID, PK)
*   `patient_id` (FK $\rightarrow$ patients.patient_id)
*   `metric_name` (String): e.g., "Oxygen Saturation".
*   `last_value` (String)
*   `last_updated` (DateTime)

**Table: `clinical_notes`**
*   `note_id` (UUID, PK)
*   `patient_id` (FK $\rightarrow$ patients.patient_id)
*   `content` (Text)
*   `author_id` (FK $\rightarrow$ users.user_id)
*   `timestamp` (DateTime)

**Table: `users`**
*   `user_id` (UUID, PK)
*   `email` (String, Unique)
*   `role` (Enum): `ADMIN`, `MEDIC`, `VIEWER`.
*   `sso_provider_id` (String)

**Table: `user_roles`**
*   `user_id` (FK $\rightarrow$ users.user_id)
*   `role_id` (String)

**Table: `workflow_rules`**
*   `rule_id` (UUID, PK)
*   `rule_name` (String)
*   `logic_tree` (JSONB)
*   `is_active` (Boolean)

**Table: `workflow_triggers`**
*   `trigger_id` (UUID, PK)
*   `rule_id` (FK $\rightarrow$ workflow_rules.rule_id)
*   `event_type` (String)

**Table: `sync_sessions`**
*   `session_id` (UUID, PK)
*   `device_id` (String)
*   `last_sync_timestamp` (DateTime)

**Table: `audit_logs`**
*   `log_id` (UUID, PK)
*   `action` (String)
*   `actor_id` (FK $\rightarrow$ users.user_id)
*   `ip_address` (String)
*   `timestamp` (DateTime)

### 5.1 Relationships
*   **One-to-Many:** `patients` $\rightarrow$ `medical_metrics` (A patient has many metrics).
*   **One-to-Many:** `patients` $\rightarrow$ `clinical_notes` (A patient has many notes).
*   **One-to-Many:** `workflow_rules` $\rightarrow$ `workflow_triggers` (A rule can be triggered by multiple events).
*   **Many-to-Many:** `users` $\rightarrow$ `roles` (via `user_roles`).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lattice utilizes a **Continuous Deployment (CD)** pipeline. Every pull request merged into the `main` branch is automatically deployed to production after passing all automated tests.

#### 6.1.1 Development (Dev)
*   **Purpose:** Individual feature development.
*   **Infrastructure:** Local Docker containers for Rust/PostgreSQL; Cloudflare Tunnel for edge testing.
*   **Data:** Mock data only.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Integration testing and stakeholder review.
*   **Infrastructure:** Mirror of Production. Cloudflare Workers (Staging Environment), managed PostgreSQL.
*   **Data:** Anonymized subset of production data.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live healthcare records for the aerospace client.
*   **Infrastructure:** ISO 27001 certified cloud environment. Global distribution via Cloudflare Workers.
*   **Data:** Highly encrypted, PII-compliant data.

### 6.2 CI/CD Pipeline
1.  **Commit:** Developer pushes code to GitHub.
2.  **CI Stage:** GitHub Actions runs `cargo test` and `npm test`.
3.  **Security Scan:** Snyk scans for vulnerabilities in Rust crates and NPM packages.
4.  **Build:** Rust binary is compiled to WASM for Cloudflare Workers.
5.  **Deploy:** `wrangler deploy` pushes the update to the edge.
6.  **Smoke Test:** Automated Playwright tests run against the live endpoint.

### 6.3 ISO 27001 Compliance
To meet the ISO 27001 requirement, the following controls are implemented:
*   **Encryption at Rest:** AES-256 for all database volumes.
*   **Encryption in Transit:** TLS 1.3 for all API calls.
*   **Access Control:** Role-Based Access Control (RBAC) integrated with SSO.
*   **Audit Trails:** Immutable event store ensures no data can be deleted without a trace.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Backend:** Every Rust module must have $>\text{80\%}$ test coverage. Focus on the Event Sourcing logic and the Rule Engine.
*   **Frontend:** Jest/React Testing Library for individual components (e.g., the Visual Rule Builder nodes).

### 7.2 Integration Testing
*   **API Testing:** Postman collections integrated into the CI pipeline to verify endpoint contracts.
*   **Database Integrity:** Tests to ensure the Projection Engine correctly transforms events into the Read Model.
*   **SSO Flow:** Automated tests using a mock SAML provider to verify authentication handshakes.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Critical Paths:** 
    *   User Login $\rightarrow$ Patient Search $\rightarrow$ Record Update $\rightarrow$ Logout.
    *   Offline Mode: Simulating network loss $\rightarrow$ Data entry $\rightarrow$ Network restoration $\rightarrow$ Sync verification.
    *   Report Generation: Triggering a scheduled report $\rightarrow$ Verifying PDF content.

### 7.4 QA Lead Oversight
Ines Kim will oversee the "Quality Gate." No PR can be merged unless the "QA Verified" label is applied, ensuring that functional requirements are met beyond just the passing of automated tests.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor EOL (End-of-Life) for core dependency | High | High | **Parallel-Path:** Prototype alternative approach (e.g., migrating from the legacy vendor to a native Rust implementation) simultaneously. |
| **R-02** | Budget cut by 30% in next fiscal quarter | Medium | High | **Escalation:** Raise as a board-level blocker in the next meeting to secure funding locks. |
| **R-03** | Data leakage of sensitive healthcare records | Low | Critical | ISO 27001 certification and strict AES-256 encryption. |
| **R-04** | Sync conflicts in offline-first mode | Medium | Medium | Implementation of vector clocks and semantic merging for clinical notes. |
| **R-05** | Project timeline slippage due to external dependencies | High | Medium | Identify critical path dependencies early and use "stub" APIs to prevent blockers. |

### 8.1 Probability/Impact Matrix
*   **Critical:** R-03 (Low Prob / Critical Impact)
*   **High Priority:** R-01, R-02 (High Prob / High Impact)
*   **Medium Priority:** R-04, R-05 (Med Prob / Med Impact)

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
*   **Phase 1: Foundation (Current - 2026-03)**
    *   Core CQRS architecture setup.
    *   SSO integration design and initial implementation.
    *   ISO 27001 environment hardening.
*   **Phase 2: Feature Build-out (2026-03 - 2026-08)**
    *   Implementation of Offline-First sync.
    *   Development of the Visual Rule Builder.
    *   Report generation engine.
*   **Phase 3: Validation & Pilot (2026-08 - 2026-12)**
    *   Beta testing with external users.
    *   Performance tuning and bug fixing.
    *   Final stakeholder sign-off.

### 9.2 Gantt-Chart Logic
*   **SAML/OIDC Design** $\rightarrow$ (Dependency) $\rightarrow$ **Internal Alpha**
*   **Offline Mode Sync** $\rightarrow$ (Dependency) $\rightarrow$ **External Beta**
*   **External Beta (2026-08-15)** $\rightarrow$ (Dependency) $\rightarrow$ **Stakeholder Demo (2026-10-15)**
*   **Stakeholder Demo** $\rightarrow$ (Dependency) $\rightarrow$ **Internal Alpha Release (2026-12-15)**

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per company policy, formal meeting minutes are not kept. Decisions are captured in Slack threads. Below are the synthesized results of key decision-making threads.*

### 10.1 Thread: #lattice-arch-decisions (Nov 12, 2023)
**Participants:** Asha Gupta, Anders Costa, Vera Jensen
**Discussion:** Debate over whether to use a standard relational database or a full event store for patient records.
**Decision:** Anders argued that for aerospace medical records, we cannot risk "lost updates" or lack of auditability. The team agreed to go with **CQRS with Event Sourcing**.
**Outcome:** All data changes must be modeled as events. Read models will be rebuilt from the event log if the database is corrupted.

### 10.2 Thread: #lattice-security (Jan 15, 2024)
**Participants:** Asha Gupta, Ines Kim
**Discussion:** The primary client requested a specific SAML implementation for their legacy portal.
**Decision:** Asha decided that we will not build a custom "one-off" bridge for the client. Instead, we will implement a generic SAML 2.0 compliant interface and require the client to provide the metadata.
**Outcome:** SSO integration remains "High Priority" and will be the first feature completed after the core architecture.

### 10.3 Thread: #lattice-blockers (Mar 02, 2024)
**Participants:** Asha Gupta, Anders Costa
**Discussion:** The "Identity Team" (external to Lattice) is 3 weeks behind on providing the OIDC discovery endpoints.
**Decision:** Anders will implement a "Mock Identity Provider" so the Lattice team can continue developing the auth flow without waiting for the other team.
**Outcome:** Current blocker identified; mitigation in place via mocking.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+ (Flagship Initiative)

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | 20+ members across 3 departments (Engineering, Product, QA) over 24 months. |
| **Infrastructure** | $600,000 | Cloudflare Enterprise, Managed PostgreSQL, S3 Encrypted Buckets. |
| **Security & Compliance** | $400,000 | ISO 27001 certification audits, penetration testing, Snyk Enterprise. |
| **Tooling & Licenses** | $200,000 | IDEs, Project Management software, CI/CD runners. |
| **Contingency** | $600,000 | Buffer for the 30% potential budget cut and vendor replacement. |

---

## 12. APPENDICES

### Appendix A: Data Synchronization Conflict Matrix
To handle the "Offline-First" requirement, the following resolution matrix is applied during the `/api/v1/sync/batch` process:

| Field Type | Conflict Strategy | Logic |
| :--- | :--- | :--- |
| **Vital Signs** | LWW (Last Write Wins) | The latest timestamp takes precedence. |
| **Clinical Notes** | Semantic Merge | Both entries are kept and appended as "Version A" and "Version B". |
| **Patient Demographics**| Admin Overwrite | Only users with `ADMIN` role can resolve conflicts. |
| **Workflow Rules** | Version Locking | The update is rejected if the base version is outdated. |

### Appendix B: Rust Crate Dependencies
The following crates are mandated for the Lattice backend to ensure stability and security:
*   `tokio`: Asynchronous runtime for high-concurrency handling.
*   `axum`: Web framework for the API layer.
*   `serde`: For high-performance JSON serialization/deserialization.
*   `sqlx`: For type-safe SQL queries to the Read Model.
*   `chrono`: For nanosecond-precision timestamping in the Event Store.
*   `jsonwebtoken`: For secure session management.
*   `saml-rs`: For SAML assertion parsing.