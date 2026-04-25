Due to the extreme length requirements (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). To maintain the professional rigor required for a development team, this document utilizes a formal engineering style, exhaustive detail on endpoints and schemas, and an expansive narrative for each feature specification.

***

# PROJECT SPECIFICATION: PROJECT JUNIPER
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Classification:** Confidential – Stormfront Consulting Internal  
**Project Status:** Active / In-Development  
**Lead Engineer:** Astrid Moreau

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Juniper is a critical infrastructure overhaul for Stormfront Consulting. For the past 15 years, the company has relied on a monolithic legacy system for its core media and entertainment operations. This legacy system, while stable in its prime, has become a liability. It is built on deprecated frameworks that no longer receive security patches, lacks the scalability to handle current media asset volumes, and possesses a codebase that is virtually undocumented, creating a "knowledge silo" risk.

The primary driver for Project Juniper is the absolute necessity to modernize the company's operational backbone without disrupting current revenue streams. Because the legacy system is the "single source of truth" for all client engagements and media assets, any downtime during the transition would result in immediate financial loss and catastrophic damage to Stormfront Consulting's reputation in the media and entertainment industry.

### 1.2 Project Scope and Objectives
The objective is to build a mobile-first application that replicates and enhances the functionality of the legacy system. This includes the implementation of a modern CQRS (Command Query Responsibility Segregation) architecture to ensure auditability and high-performance data retrieval. The system must be HIPAA compliant, as Stormfront Consulting handles sensitive talent medical records and contractual data that falls under protected health information (PHI) guidelines.

### 1.3 ROI Projection and Success Metrics
Stormfront Consulting has allocated a budget of $3,000,000 for this initiative. The Return on Investment (ROI) is projected based on three primary levers:
1. **Operational Efficiency:** The legacy system requires manual reconciliation of data across three disparate databases. Juniper’s automated workflow engine is expected to reduce manual data entry by 60%.
2. **Transaction Cost Reduction:** By migrating from expensive on-premise legacy servers to a streamlined, cloud-native architecture, the company targets a **35% reduction in cost per transaction**.
3. **Risk Mitigation:** The elimination of legacy "dark debt" (unmaintained code) reduces the probability of a catastrophic system failure, which is estimated to cost the company $250,000 per hour of downtime.

**Primary Success Criteria:**
- **Uptime:** 99.9% availability during the first 90 days post-launch.
- **Performance:** Average API response time $< 200\text{ms}$ for 95% of requests.
- **Compliance:** 100% pass rate on the third-party HIPAA security audit.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: CQRS and Event Sourcing
Given the "audit-critical" nature of the media and entertainment industry—where contractual changes must be tracked to the millisecond—Project Juniper utilizes **Command Query Responsibility Segregation (CQRS)**.

In this architecture, the "Write" side (Commands) and the "Read" side (Queries) are decoupled. Every change to the system state is stored as an immutable event in an **Event Store**. 

**The Flow:**
1. A user submits a request (Command).
2. The Command Handler validates the request and persists an event to the Event Store.
3. A Projection Engine listens to these events and updates the Read Database (Materialized Views).
4. The Mobile Application queries the Read Database for high-speed data retrieval.

### 2.2 The "Mixed Stack" Interoperability
Stormfront Consulting is inheriting three disparate legacy stacks that Juniper must interoperate with during the transition phase:
- **Stack A (Legacy Core):** Java 6 / Oracle 11g (The primary data source).
- **Stack B (Asset Management):** .NET Framework 4.5 / SQL Server 2012.
- **Stack C (Client Portal):** PHP 5.4 / MySQL 5.5.

Juniper acts as the orchestration layer, utilizing an **Anti-Corruption Layer (ACL)** to translate legacy data formats into the new domain model, preventing the "rot" of the old systems from leaking into the new architecture.

### 2.3 ASCII Architectural Diagram
```text
[ Mobile Client (iOS/Android) ]
            |
            v
    [ API Gateway / Rate Limiter ] <--- (HIPAA Encrypted TLS 1.3)
            |
    -------------------------------------------------------
    |                  Business Logic Layer               |
    |  [ Command API ] <-----------> [ Query API ]         |
    |        |                           ^                  |
    |        v                           |                  |
    |  [ Event Store ] ------> [ Projection Engine ]        |
    |  (Immutable Log)                 |                    |
    -------------------------------------------------------
            |                           |
            v                           v
    [ Legacy ACL Layer ] <------> [ Read DB (PostgreSQL) ]
            |
    -------------------------------------------------------
    |  [ Stack A ]  |  [ Stack B ]  |  [ Stack C ]         |
    |  (Java/Ora)   |  (.NET/SQL)   |  (PHP/MySQL)         |
    -------------------------------------------------------
```

### 2.4 Security Implementation
All data is encrypted at rest using AES-256 and in transit using TLS 1.3. To meet HIPAA compliance:
- **BoringSSL** is utilized for the mobile client.
- **Hardware Security Modules (HSM)** are used for key rotation.
- **Audit Logs** are immutable and stored in a separate, write-once-read-many (WORM) storage bucket.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low | **Status:** Complete | **Version:** v1.0.2

**Description:**
To satisfy the high-security requirements of executive-level users in the media industry, Juniper implements a multi-tiered 2FA system. While standard TOTP (Time-based One-Time Password) is supported, the system specifically integrates WebAuthn for hardware security keys (e.g., Yubikeys).

**Functional Requirements:**
- **Hardware Key Integration:** Users can register multiple FIDO2/WebAuthn keys. Upon login, the system triggers a challenge-response handshake.
- **Fallback Mechanisms:** In the event of a lost hardware key, users can utilize a set of one-time recovery codes generated during the initial setup.
- **Session Management:** 2FA must be re-validated every 24 hours for administrative accounts and every 7 days for standard users.
- **Hardware Attestation:** The system verifies the authenticity of the hardware key to ensure it is from a trusted vendor.

**Technical Implementation:**
The implementation uses a `/auth/2fa/verify` endpoint. The hardware key provides a cryptographic signature of the challenge, which is verified against the public key stored in the `UserSecurity` table.

**User Experience (UX):**
The mobile app utilizes a biometric prompt (FaceID/TouchID) as a "convenience layer" on top of the 2FA, meaning the hardware key is required for the initial device binding, and biometrics are used for subsequent session renewals.

---

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** In Review | **Version:** v0.8.5

**Description:**
Moving data from 15-year-old legacy systems is the project's highest risk. This feature allows administrators to upload bulk data files (CSV, XML, JSON, and proprietary legacy .DAT files) and have the system automatically determine the schema and map it to the Juniper domain model.

**Functional Requirements:**
- **Auto-Detection Engine:** The system must analyze the first 1,000 lines of any uploaded file to determine the delimiter, encoding (UTF-8 vs. Latin-1), and structural format.
- **Mapping Interface:** A visual "Drag-and-Drop" mapper allows users to link legacy columns (e.g., `CUST_NAME_01`) to Juniper fields (e.g., `client_full_name`).
- **Validation Pass:** Before committing to the Event Store, the system performs a "dry run" validation, flagging rows that violate data integrity constraints (e.g., nulls in non-nullable fields).
- **Export Versatility:** Users can export any filtered view of the data into five different formats, including a "Legacy Compatible" format to allow data to flow back into the old system during the transition.

**Technical Implementation:**
The system utilizes a worker-queue pattern. The file is uploaded to an S3 bucket, and a Celery worker processes the file using a series of "Detectors." If the detector identifies a `.DAT` file, it invokes the `LegacyParser` class.

**Performance Constraints:**
The import engine must support files up to 2GB without timing out the mobile client. This is achieved via multipart uploads and asynchronous processing with a progress WebSocket.

---

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Design | **Version:** v0.4.0

**Description:**
The media industry relies on heavy assets (scripts, contracts, headshots). This feature provides a secure pipeline for uploading these assets, ensuring they are clean of malware before being distributed globally via a Content Delivery Network (CDN).

**Functional Requirements:**
- **Asynchronous Scanning:** Files are uploaded to a "Quarantine" bucket. A ClamAV-based scanning service analyzes the file. Only upon a "Clean" result is the file moved to the "Production" bucket.
- **CDN Integration:** Once cleaned, the file is cached across 12 global edge locations using Amazon CloudFront to ensure low-latency access for international talent agencies.
- **Virus Quarantine:** Any file flagged as malicious is immediately deleted, and an alert is sent to Rosa Santos (Security Engineer) via the internal security dashboard.
- **Chunked Uploads:** To support large media files, the system implements an upload protocol that breaks files into 5MB chunks, allowing for resumes in case of network failure.

**Technical Implementation:**
The pipeline follows this path: `Mobile Client` $\rightarrow$ `S3 Quarantine` $\rightarrow$ `Lambda Trigger` $\rightarrow$ `ClamAV Scanner` $\rightarrow$ `S3 Production` $\rightarrow$ `CloudFront`.

**Security Considerations:**
To prevent "Zip Bombs" and other denial-of-service attacks, the system enforces a strict 500MB limit per file and a maximum decompression ratio of 100:1.

---

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Critical | **Status:** In Review | **Version:** v0.9.1

**Description:**
As a "launch blocker," this feature protects the new infrastructure from being overwhelmed by legacy scripts that may attempt to poll the API too frequently. It also provides the executive team with visibility into which modules are being used most.

**Functional Requirements:**
- **Tiered Rate Limits:** Different limits are applied based on the user role. (e.g., Admin: 5,000 req/hr; Standard: 1,000 req/hr; Legacy Bot: 100 req/hr).
- **Sliding Window Algorithm:** The system uses a sliding window log implemented in Redis to prevent "burst" traffic at the turn of the hour.
- **Analytics Dashboard:** A real-time dashboard tracking "Top 10 Most Used Endpoints," "Average Latency per Region," and "Error Rate by Version."
- **Header Feedback:** The API must return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers in every response.

**Technical Implementation:**
A middleware layer sits in front of the API. For every request, the middleware checks the user's API key against a Redis key with a TTL. If the count exceeds the threshold, it returns a `429 Too Many Requests` response.

**Business Impact:**
This feature is critical for calculating the "Cost per Transaction" success metric. By tracking exactly how many API calls are made per business action, the team can optimize the infrastructure to meet the 35% cost reduction goal.

---

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical | **Status:** In Progress | **Version:** v0.6.2

**Description:**
The crown jewel of Project Juniper, this engine replaces the hard-coded business logic of the legacy system with a flexible, user-definable rule set. It allows non-technical managers to create "If-This-Then-That" (IFTTT) workflows for media production.

**Functional Requirements:**
- **Visual Rule Builder:** A node-based UI (implemented via React Flow) where users can drag "Triggers" (e.g., "Contract Signed") and connect them to "Actions" (e.g., "Notify Accounting").
- **Conditional Logic:** Support for complex AND/OR logic and nested "If" statements (e.g., "If Contract Signed AND Value > $10,000 $\rightarrow$ Send to VP Approval").
- **Event-Driven Execution:** The engine hooks into the CQRS event stream. When a `ContractSignedEvent` is published, the engine evaluates all active rules associated with that event.
- **Versioned Rules:** Rules are versioned. An administrator can "Roll Back" a workflow to a previous version if a new rule causes an operational loop.

**Technical Implementation:**
The engine uses a **Rete Algorithm** for efficient pattern matching. Rules are stored as JSON graphs in the database and compiled into a bytecode format for rapid execution by the workflow runner.

**Operational Risk:**
Because this is a launch blocker, the team is focusing on "Infinite Loop Detection," ensuring that a rule cannot trigger itself in a way that crashes the system.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a Bearer Token in the header.

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns a session token.
- **Request:**
  ```json
  {
    "username": "astride_m",
    "password": "hashed_password_here",
    "device_id": "device_abc_123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "jwt_token_string",
    "expires_at": "2023-10-24T23:59:59Z",
    "requires_2fa": true
  }
  ```

### 4.2 `GET /assets/list`
- **Description:** Retrieves a paginated list of media assets.
- **Parameters:** `page` (int), `limit` (int), `filter` (string).
- **Response (200 OK):**
  ```json
  {
    "data": [
      {"id": "asset_001", "name": "Script_Final.pdf", "url": "cdn.juniper.com/asset_001"},
      {"id": "asset_002", "name": "Headshot_Lead.jpg", "url": "cdn.juniper.com/asset_002"}
    ],
    "total": 1450,
    "next_page": 2
  }
  ```

### 4.3 `POST /assets/upload`
- **Description:** Initiates a chunked upload process.
- **Request:** `multipart/form-data` (File chunk, upload_id, chunk_index).
- **Response (202 Accepted):**
  ```json
  {
    "upload_id": "up_998877",
    "status": "uploading",
    "next_expected_chunk": 5
  }
  ```

### 4.4 `POST /workflow/rules`
- **Description:** Creates a new automation rule from the visual builder.
- **Request:**
  ```json
  {
    "rule_name": "VP Approval Path",
    "trigger_event": "CONTRACT_SIGNED",
    "conditions": [{"field": "value", "operator": ">", "value": 10000}],
    "actions": [{"type": "EMAIL_NOTIFICATION", "recipient": "vp_office"}]
  }
  ```
- **Response (201 Created):**
  ```json
  { "rule_id": "rule_5544", "status": "active" }
  ```

### 4.5 `GET /analytics/usage`
- **Description:** Returns usage metrics for the current month.
- **Response (200 OK):**
  ```json
  {
    "total_requests": 1500000,
    "error_rate": "0.02%",
    "p95_latency": "185ms",
    "top_endpoint": "/assets/list"
  }
  ```

### 4.6 `POST /data/import`
- **Description:** Uploads a file for auto-detection and import.
- **Request:** `multipart/form-data` (File, import_type).
- **Response (202 Accepted):**
  ```json
  {
    "job_id": "job_abc_123",
    "estimated_completion": "2023-10-24T14:00:00Z",
    "status_url": "/api/v1/data/import/status/job_abc_123"
  }
  ```

### 4.7 `GET /data/export`
- **Description:** Generates a data export in the requested format.
- **Parameters:** `format` (csv|json|xml|legacy), `filter_id` (uuid).
- **Response (200 OK):** Redirect to signed S3 download URL.

### 4.8 `POST /auth/2fa/verify`
- **Description:** Verifies a hardware key challenge.
- **Request:**
  ```json
  {
    "challenge_id": "chal_123",
    "signature": "base64_encoded_signature",
    "client_data": "json_payload"
  }
  ```
- **Response (200 OK):**
  ```json
  { "session_verified": true, "session_token": "final_access_token" }
  ```

---

## 5. DATABASE SCHEMA

The system utilizes a hybrid database approach: **PostgreSQL** for the Read Model and **EventStoreDB** for the Command Model. The following tables represent the Read Model.

### 5.1 Table: `Users`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | PK | Unique identifier |
| `username` | VARCHAR(50) | Unique, Not Null | Login handle |
| `email` | VARCHAR(255) | Not Null | HIPAA contacted email |
| `role_id` | INT | FK $\rightarrow$ Roles | User permissions level |
| `mfa_enabled` | BOOLEAN | Default False | Status of 2FA |
| `created_at` | TIMESTAMP | Not Null | Account creation date |

### 5.2 Table: `Roles`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `role_id` | INT | PK | Role identifier |
| `role_name` | VARCHAR(20) | Not Null | e.g., 'Admin', 'User' |
| `permissions` | JSONB | Not Null | List of granted permissions |

### 5.3 Table: `UserSecurity`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `sec_id` | UUID | PK | Security record ID |
| `user_id` | UUID | FK $\rightarrow$ Users | Associated user |
| `public_key` | TEXT | Not Null | WebAuthn public key |
| `key_type` | VARCHAR(20) | Not Null | 'YubiKey', 'Titan', etc. |
| `last_used` | TIMESTAMP | - | Last successful 2FA login |

### 5.4 Table: `Assets`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `asset_id` | UUID | PK | Unique asset ID |
| `file_name` | VARCHAR(255) | Not Null | Original filename |
| `s3_path` | TEXT | Not Null | Path in Production bucket |
| `mime_type` | VARCHAR(50) | Not Null | File type (PDF, JPG) |
| `size_bytes` | BIGINT | Not Null | Total file size |
| `is_scanned` | BOOLEAN | Default False | ClamAV status |

### 5.5 Table: `WorkflowRules`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `rule_id` | UUID | PK | Rule identifier |
| `name` | VARCHAR(100) | Not Null | User-defined name |
| `trigger_event` | VARCHAR(50) | Not Null | Event that fires rule |
| `logic_json` | JSONB | Not Null | The Compiled Rete graph |
| `version` | INT | Not Null | Incremental version |
| `is_active` | BOOLEAN | Default True | Enabled/Disabled status |

### 5.6 Table: `WorkflowLogs`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `log_id` | BIGINT | PK | Execution log ID |
| `rule_id` | UUID | FK $\rightarrow$ WorkflowRules | Rule that was triggered |
| `event_id` | UUID | - | The triggering event ID |
| `status` | VARCHAR(20) | Not Null | 'Success', 'Failed', 'Loop' |
| `execution_time` | INT | - | Time in milliseconds |

### 5.7 Table: `AuditEvents` (Event Store Projection)
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | UUID | PK | Unique event ID |
| `aggregate_id` | UUID | Index | ID of the entity changed |
| `event_type` | VARCHAR(50) | Not Null | e.g., 'UserCreated' |
| `payload` | JSONB | Not Null | The state change data |
| `timestamp` | TIMESTAMP | Not Null | Precise UTC time |
| `user_id` | UUID | FK $\rightarrow$ Users | Who performed the action |

### 5.8 Table: `RateLimitKeys`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `api_key` | VARCHAR(64) | PK | Hashed API key |
| `current_count` | INT | Not Null | Current window count |
| `window_start` | TIMESTAMP | Not Null | Start of sliding window |
| `limit_tier` | INT | Not Null | Max allowed requests |

### 5.9 Table: `ImportJobs`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `job_id` | UUID | PK | Job identifier |
| `user_id` | UUID | FK $\rightarrow$ Users | User who started import |
| `status` | VARCHAR(20) | Not Null | 'Pending', 'Processing', 'Done' |
| `error_log` | TEXT | - | Detailed failure reasons |
| `rows_processed` | INT | - | Count of successful rows |

### 5.10 Table: `ClientData` (Legacy Bridge)
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `client_id` | UUID | PK | Internal Juniper ID |
| `legacy_id` | VARCHAR(50) | Index | ID from Stack A/B/C |
| `sync_status` | VARCHAR(20) | Not Null | 'Synced', 'Dirty', 'Conflict' |
| `last_sync` | TIMESTAMP | - | Last time bridged to legacy |

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### 6.1.1 Development Environment (`dev`)
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Local Docker Compose setups for developers, with a shared staging-like "Dev-Svr" hosted on a low-spec AWS EC2 instance.
- **Deployment:** Automatic deployments via Git push to the `dev` branch.
- **Data:** Mock data generated by scripts; no real PHI data allowed.

#### 6.1.2 Staging Environment (`stg`)
- **Purpose:** Integration testing, QA, and UAT (User Acceptance Testing).
- **Infrastructure:** A mirrored replica of Production. Kubernetes (EKS) cluster with 3 nodes.
- **Deployment:** Manual trigger via JIRA ticket approval.
- **Data:** Anonymized production data snapshots.

#### 6.1.3 Production Environment (`prd`)
- **Purpose:** Live user traffic and business operations.
- **Infrastructure:** Multi-AZ (Availability Zone) deployment on AWS. EKS cluster with auto-scaling enabled.
- **Deployment:** **Manual deployments performed by a single DevOps person.** This represents a significant "Bus Factor of 1" risk.
- **Data:** Fully encrypted HIPAA-compliant data.

### 6.2 CI/CD Pipeline and Technical Debt
The current CI pipeline is a major bottleneck. It consists of a single Jenkins pipeline that runs all tests sequentially.
- **Current Execution Time:** 45 minutes.
- **Cause:** Lack of parallelization and unoptimized Docker image builds.
- **Mitigation Plan:** The project lead (Astrid Moreau) has flagged this as technical debt. The goal is to implement "Test Splitting" and "Layer Caching" to reduce the time to $< 10$ minutes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and logic gates (e.g., the Rete engine's rule evaluator).
- **Tooling:** PyTest (Backend), Jest (Frontend).
- **Requirement:** 80% code coverage for all "Critical" priority features.

### 7.2 Integration Testing
- **Scope:** Communication between the API Gateway, the Event Store, and the Read Database.
- **Scenario:** A "Command" is issued $\rightarrow$ Event is stored $\rightarrow$ Projection updates Read DB $\rightarrow$ "Query" returns the updated value.
- **Frequency:** Executed on every merge request to the `staging` branch.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "User logs in with Yubikey $\rightarrow$ Uploads Asset $\rightarrow$ Trigger Rule $\rightarrow$ Receives Email").
- **Tooling:** Cypress / Appium.
- **Execution:** Run weekly on the Staging environment.

### 7.4 Compliance Testing (HIPAA)
- **Scope:** Encryption verification, access control audits, and data leakage tests.
- **Frequency:** Quarterly internal audits, with one major external audit before the 2026-10-15 milestone.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotates out of role | High | High | Build a contingency plan with a fallback architecture that is less dependent on specific executive mandates. |
| **R-02** | Team lacks experience in CQRS/Event Sourcing | High | Medium | De-scope affected features if the learning curve prevents hitting milestones. Provide external consultancy training. |
| **R-03** | DevOps "Bus Factor" (Single person deployment) | Medium | Critical | Document the deployment process in a "Runbook" and train Quinn Kim on basic deployment scripts. |
| **R-04** | Legacy system downtime during migration | Low | Critical | Implement a "Parallel Run" phase where both systems operate simultaneously for 30 days. |
| **R-05** | CI Pipeline failure slows development | High | Low | Prioritize a "Pipeline Sprint" to parallelize tests and optimize Docker builds. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal breach.
- **High:** Major delay or significant budget overage.
- **Medium:** Manageable delay with some feature trade-offs.
- **Low:** Minor annoyance with no impact on launch date.

---

## 9. TIMELINE

### 9.1 Phase Breakdown
The project is divided into four primary phases, utilizing a modified Agile-Waterfall hybrid approach.

#### Phase 1: Foundation (2023-12 - 2024-06)
- Infrastructure setup (AWS EKS).
- Implementation of the Event Store and Read Database.
- Core Auth (2FA) completion.

#### Phase 2: Core Logic (2024-07 - 2025-03)
- Development of the Workflow Engine.
- API Rate Limiting implementation.
- Implementation of the Legacy ACL (Anti-Corruption Layer).

#### Phase 3: Data Migration (2025-04 - 2026-03)
- Development of the Import/Export auto-detection engine.
- Migration of legacy data from Stack A, B, and C.
- Beta testing with a small subset of users.

#### Phase 4: Validation and Launch (2026-04 - 2026-10)
- Final stress testing.
- Production launch.
- Final security audit.

### 9.2 Milestone Schedule
| Milestone | Event | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| **M1** | **Production Launch** | **2026-06-15** | Workflow Engine & Rate Limiter Complete |
| **M2** | **Internal Alpha Release** | **2026-08-15** | Data Import/Export in Review |
| **M3** | **Security Audit Passed** | **2026-10-15** | HIPAA compliance verification |

---

## 10. MEETING NOTES

*Note: Per company policy, these are summaries of recorded video calls. No one on the team has rewatched the full recordings.*

### Meeting 1: Architecture Review (Date: 2023-11-05)
- **Attendees:** Astrid, Quinn, Rosa, Nadia.
- **Discussion:** The team debated whether to use a standard CRUD architecture or CQRS. Quinn expressed concern about the complexity of managing two separate data models (Read/Write).
- **Decision:** Astrid mandated CQRS because the "audit-critical" nature of the project requires an immutable event log for HIPAA compliance.
- **Action Item:** Quinn to research "Materialized Views" in PostgreSQL to simplify the Read side.

### Meeting 2: The "Bus Factor" Crisis (Date: 2024-02-12)
- **Attendees:** Astrid, DevOps Lead.
- **Discussion:** The team realized that only one person knows how to deploy to production. If that person is sick, the launch is blocked.
- **Decision:** The DevOps lead will create a "Deployment Runbook" in the Wiki. However, the deployment remains manual for now to ensure stability.
- **Action Item:** Astrid to request budget for a second DevOps engineer in Q3.

### Meeting 3: Legal Blocker (Date: 2024-05-20)
- **Attendees:** Astrid, Legal Counsel.
- **Discussion:** The Data Processing Agreement (DPA) is currently stuck in legal review. Without this, the team cannot move real PHI data into the staging environment.
- **Decision:** The team will use "Synthetic Data" for the next two sprints to avoid stalling development.
- **Action Item:** Astrid to follow up with the Legal VP daily until the DPA is signed.

---

## 11. BUDGET BREAKDOWN

The total investment for Project Juniper is **$3,000,000**.

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 12-person cross-functional team over 3 years. |
| **Infrastructure** | 15% | $450,000 | AWS EKS, RDS, CloudFront, and S3 costs. |
| **Tools & Licenses** | 5% | $150,000 | JIRA, Jenkins, ClamAV Enterprise, Datadog. |
| **Security Audit** | 5% | $150,000 | Third-party HIPAA compliance certification. |
| **Contingency** | 10% | $300,000 | Reserved for de-scoping or emergency hiring. |

**Personnel Detail:**
- Engineering Manager (Astrid): $180k/yr
- Leads (Quinn, Rosa): $160k/yr each
- Support/Devs: $120k - $140k/yr

---

## 12. APPENDICES

### Appendix A: Legacy Stack Mapping Table
This table defines how legacy fields are mapped into the Juniper domain to prevent data corruption.

| Legacy Stack | Legacy Field | Juniper Field | Type | Logic |
| :--- | :--- | :--- | :--- | :--- |
| Stack A | `CUST_REF_ID` | `client_id` | UUID | Cast String $\rightarrow$ UUID |
| Stack B | `FILE_BLOB` | `asset_id` | UUID | Extract from BLOB metadata |
| Stack C | `USER_LOGIN` | `username` | VARCHAR | Trim whitespace, lowercase |

### Appendix B: HIPAA Compliance Checklist
The following controls must be verified by Rosa Santos prior to Milestone 3:
1. **Encryption at Rest:** All EBS volumes and RDS instances must use AWS KMS keys.
2. **Encryption in Transit:** Minimum TLS 1.2 (TLS 1.3 preferred) for all endpoints.
3. **Automatic Log-off:** Mobile app sessions must expire after 15 minutes of inactivity.
4. **Unique User Identification:** No shared accounts; all actions must be tied to a `user_id`.
5. **Automatic Audit Trails:** Every change to `ClientData` must generate an `AuditEvent` in the Event Store.
6. **Access Control:** Implementation of Role-Based Access Control (RBAC) via the `Roles` table.