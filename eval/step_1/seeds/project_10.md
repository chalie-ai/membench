# PROJECT SPECIFICATION: PROJECT DELPHI
**Version:** 1.0.4  
**Status:** Draft/Internal Reference  
**Date:** October 24, 2023  
**Classification:** Confidential / FedRAMP Compliant  
**Author:** Kamau Stein, CTO  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Delphi represents a strategic pivot for Duskfall Inc. For the first time in the company's history, Duskfall is entering the Education Technology (EdTech) vertical. While the company has a strong foothold in corporate enterprise software, the education market presents a unique growth trajectory, particularly within the K-12 and Higher Education government sectors. The primary business driver is the capture of state-funded educational contracts which require rigid compliance standards and a modern, scalable delivery mechanism for collaborative learning tools.

The core objective of Project Delphi is to migrate from a legacy monolithic architecture to a streamlined, API-gateway-led microservices approach (implemented as a clean monolith for initial stability) that can support real-time collaborative environments. By building this "greenfield" product, Duskfall Inc. avoids the technical debt of its existing corporate suites and can implement a modern security posture from the ground up, specifically targeting FedRAMP authorization to unlock government procurement channels.

### 1.2 ROI Projection
The financial investment for Project Delphi is budgeted at $5.2 million. The return on investment is calculated based on a targeted capture of three major state-level education contracts within the first 24 months. 

**Financial Targets:**
*   **Year 1 Revenue Goal:** $500,000 in new attributed revenue.
*   **Break-even Analysis:** Expected by Q3 2027.
*   **Market Expansion:** Expansion into the government education sector is projected to increase the company's Total Addressable Market (TAM) by 22%.

The ROI is not merely financial; the project serves as a lighthouse for the organization's transition toward more modular architecture and rigorous security compliance (FedRAMP), which can be leveraged for other product lines.

### 1.3 Strategic Alignment
Project Delphi aligns with the Board’s "Horizon 3" growth initiative: diversification of revenue streams. By operating in a market where the company has zero legacy footprint, Delphi allows for rapid experimentation with A/B testing and feature-flagged deployments, ensuring the product-market fit is validated before scaling the user base.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Delphi utilizes a **"Clean Monolith"** strategy. While the goal is a microservices migration, the team has opted for a modular monolith to reduce network latency and deployment complexity within the on-premise data center constraints. Each module (Collaborative Editing, Notification, Audit, etc.) is strictly decoupled via internal Java interfaces, allowing for a future "lift-and-shift" into independent microservices without rewriting the business logic.

### 2.2 Technology Stack
*   **Backend:** Java 17 / Spring Boot 3.1.x
*   **API Gateway:** Spring Cloud Gateway (on-premise deployment)
*   **Database:** Oracle Database 19c (Enterprise Edition)
*   **Deployment:** On-premise physical servers (No Cloud/AWS/Azure permitted per government data residency requirements)
*   **Security:** Spring Security with OAuth2/OpenID Connect, tailored for FedRAMP High baseline.
*   **Caching:** Redis 7.0 (On-premise) for session management and real-time state.

### 2.3 Architecture Diagram (ASCII)

```text
[ Client Browser / Mobile App ]
           |
           v (HTTPS/TLS 1.3)
+---------------------------------------+
|        API GATEWAY (Spring Cloud)     | <--- Rate Limiting, AuthN/AuthZ,
| [ /api/v1/collab ] [ /api/v1/audit ]  |      Routing to Modules
+---------------------------------------+
           |
           v
+---------------------------------------+
|       CLEAN MONOLITH (JVM)            |
|                                       |
|  +------------+    +---------------+  |
|  | Collab Mod  | <->| Audit Mod     |  |
|  +------------+    +---------------+  |
|        ^                    ^         |
|        |                    |        |
|  +------------+    +---------------+  |
|  | Notif Mod   |    | A/B Test Mod  |  |
|  +------------+    +---------------+  |
|        |                    |         |
+---------------------------------------+
           |
           v
+---------------------------------------+
|      ORACLE DB 19c (On-Prem)          |
|  [ Tables ] [ Raw SQL Views ] [ PL/SQL] |
+---------------------------------------+
           |
           v
+---------------------------------------+
|    FedRAMP COMPLIANT LOG STORAGE      |
|      (Write-Once-Read-Many/WORM)       |
+---------------------------------------+
```

### 2.4 Data Access Layer
Due to performance requirements for real-time editing, the team has implemented a hybrid data access layer. While Hibernate/JPA is used for 70% of CRUD operations, **30% of queries bypass the ORM using raw SQL (JdbcTemplate)** to optimize complex joins and bulk inserts. This creates a significant technical debt risk, as schema migrations must be manually verified against these raw queries to prevent runtime failures.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical | **Status:** Blocked | **Launch Blocker:** Yes

**Description:**
This feature allows multiple educators and students to edit the same document simultaneously. The system must handle concurrent updates without data loss or "last-write-wins" overrides. 

**Technical Specification:**
The system will implement **Operational Transformation (OT)** or **Conflict-free Replicated Data Types (CRDTs)**. Given the Java stack, the team is evaluating the use of a customized LWW-Element-Set (Last-Write-Wins) for simple attributes and a sequence-based OT for text blocks.
*   **WebSockets:** Connection will be managed via Spring WebSocket with STOMP.
*   **State Management:** The current "cursor position" and "active user" state will be cached in Redis to minimize Oracle DB hits.
*   **Conflict Resolution Logic:** When two users edit the same character index, the server-side sequencer will assign a timestamp. The transformation engine will adjust the index of the second operation relative to the first.

**Blocker Detail:** 
The feature is currently blocked due to a failure in the WebSocket handshake protocol when passing through the on-premise hardware load balancer, resulting in 502 Bad Gateway errors.

---

### 3.2 A/B Testing Framework (Integrated Feature Flags)
**Priority:** Critical | **Status:** In Progress | **Launch Blocker:** Yes

**Description:**
A sophisticated A/B testing framework baked directly into the feature flag system. This allows the product team to roll out features to a percentage of the user base (e.g., 10% of teachers in one district) and measure engagement metrics before a full rollout.

**Technical Specification:**
*   **Flag Engine:** A custom implementation within the `com.duskfall.delphi.config` package.
*   **Assignment Logic:** Users are hashed based on their `user_id` and `tenant_id`. The hash is mapped to a bucket (0-99). If the flag is set to 20%, users in buckets 0-19 see the feature.
*   **Persistence:** Flag configurations are stored in the `sys_feature_flags` table in Oracle.
*   **Telemetry:** Every action taken by a user within an A/B test must be tagged with the `experiment_id` and `variant_id` in the audit logs.

**Current Status:** 
The core hashing logic is complete. The integration with the UI to handle "variant-specific CSS" is still in development.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical | **Status:** Blocked | **Launch Blocker:** Yes

**Description:**
For FedRAMP compliance, every state-changing operation must be logged. These logs must be "tamper-evident," meaning any attempt to alter a log entry must be detectable by a third-party auditor.

**Technical Specification:**
*   **Chain of Trust:** Each log entry will contain a SHA-256 hash of the previous entry (blockchain-lite approach).
*   **Storage:** Logs are written to an Oracle table and simultaneously streamed to a WORM (Write Once Read Many) storage appliance on-premise.
*   **Schema:** The `audit_trail` table includes `timestamp`, `user_id`, `action_type`, `old_value`, `new_value`, and `entry_hash`.
*   **Verification:** A nightly batch job will re-calculate the hash chain to ensure no records were deleted or altered.

**Blocker Detail:** 
Blocked due to the lack of available WORM storage hardware in the current data center rack. Procurement is pending.

---

### 3.4 Notification System (Multi-Channel)
**Priority:** High | **Status:** In Progress

**Description:**
A centralized notification hub that routes alerts to users via four distinct channels: Email, SMS, In-app (WebSocket), and Push notifications.

**Technical Specification:**
*   **Dispatcher:** A `NotificationDispatcher` service that evaluates user preferences stored in the `user_notification_prefs` table.
*   **Email:** Integration with the internal SMTP relay via JavaMailSender.
*   **SMS:** Integration with a third-party gateway (currently evaluating vendors).
*   **Push:** Firebase Cloud Messaging (FCM) via an on-premise proxy.
*   **Queueing:** Notifications are placed in a RabbitMQ queue to ensure asynchronous delivery and retry logic (exponential backoff).

**Current Status:** 
Email and In-app notifications are functional. SMS and Push are awaiting API credentials from the vendor.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** In Design

**Description:**
Allows users to upload educational materials (PDFs, Images, Videos). All files must be scanned for malware before being available for download.

**Technical Specification:**
*   **Upload Path:** Files are uploaded to a temporary "quarantine" directory on a SAN (Storage Area Network).
*   **Scanning:** An asynchronous process triggers a ClamAV scan on the uploaded file.
*   **Distribution:** Once cleared, files are moved to a "Production" directory. An on-premise Nginx cache serves as the "CDN" for internal network distribution.
*   **Metadata:** File metadata (size, mime-type, scan-result) is stored in the `document_metadata` table.

**Current Status:** 
The architectural diagram is approved; development has not yet started.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the `/api/v1/` prefix. Authentication is required via Bearer Token (JWT).

### 4.1 Collaborative Document Access
`GET /api/v1/collab/document/{docId}`
*   **Description:** Retrieves the current state of a collaborative document.
*   **Request:** `docId` (UUID)
*   **Response:** `200 OK` { "docId": "...", "content": "...", "version": 104 }

### 4.2 Document Update (OT Patch)
`POST /api/v1/collab/document/{docId}/patch`
*   **Description:** Sends an operational transformation patch to the server.
*   **Request:** `{ "version": 104, "operation": "insert", "index": 12, "text": "Hello" }`
*   **Response:** `200 OK` { "newVersion": 105, "status": "applied" }

### 4.3 Feature Flag Check
`GET /api/v1/config/features/{featureKey}`
*   **Description:** Checks if a specific feature is enabled for the authenticated user.
*   **Request:** `featureKey` (String)
*   **Response:** `200 OK` { "featureKey": "new-dashboard", "isEnabled": true, "variant": "B" }

### 4.4 Notification Preference Update
`PUT /api/v1/user/notifications/prefs`
*   **Description:** Updates user's preferred notification channels.
*   **Request:** `{ "email": true, "sms": false, "push": true }`
*   **Response:** `204 No Content`

### 4.5 Audit Log Retrieval (Admin Only)
`GET /api/v1/admin/audit?userId={userId}`
*   **Description:** Retrieves the tamper-evident audit trail for a specific user.
*   **Request:** `userId` (UUID)
*   **Response:** `200 OK` [ { "timestamp": "...", "action": "LOGIN", "hash": "..." } ]

### 4.6 File Upload (Quarantine)
`POST /api/v1/files/upload`
*   **Description:** Uploads a file to the quarantine area for scanning.
*   **Request:** Multipart form-data (File)
*   **Response:** `202 Accepted` { "fileId": "...", "status": "scanning" }

### 4.7 File Status Check
`GET /api/v1/files/status/{fileId}`
*   **Description:** Checks if the virus scan has completed.
*   **Request:** `fileId` (UUID)
*   **Response:** `200 OK` { "fileId": "...", "scanResult": "CLEAN", "url": "..." }

### 4.8 A/B Test Metric Submission
`POST /api/v1/analytics/event`
*   **Description:** Submits a user interaction event linked to an A/B test.
*   **Request:** `{ "eventId": "btn_click", "experimentId": "EXP_01", "value": 1 }`
*   **Response:** `201 Created`

---

## 5. DATABASE SCHEMA

The system utilizes Oracle 19c. Relationships are enforced via Foreign Keys, except where raw SQL performance requirements necessitated "soft-links."

### 5.1 Table Definitions

1.  **`users`**: Primary user account table.
    *   `user_id` (UUID, PK), `username` (VARCHAR2), `password_hash` (VARCHAR2), `email` (VARCHAR2), `created_at` (TIMESTAMP).
2.  **`tenants`**: Education districts or schools.
    *   `tenant_id` (UUID, PK), `district_name` (VARCHAR2), `region` (VARCHAR2), `subscription_level` (VARCHAR2).
3.  **`user_tenant_mapping`**: Links users to their respective schools.
    *   `mapping_id` (PK), `user_id` (FK), `tenant_id` (FK), `role` (VARCHAR2).
4.  **`documents`**: Collaborative document metadata.
    *   `doc_id` (UUID, PK), `tenant_id` (FK), `owner_id` (FK), `title` (VARCHAR2), `current_version` (NUMBER).
5.  **`document_content`**: Stores the actual text (CLOB).
    *   `doc_id` (FK), `content_blob` (CLOB), `last_modified` (TIMESTAMP).
6.  **`sys_feature_flags`**: Feature flag configurations.
    *   `flag_id` (PK), `feature_key` (VARCHAR2), `is_enabled` (NUMBER 1), `rollout_percentage` (NUMBER), `variant_data` (JSON).
7.  **`user_notification_prefs`**: User-specific channel preferences.
    *   `user_id` (FK), `channel_email` (NUMBER 1), `channel_sms` (NUMBER 1), `channel_push` (NUMBER 1).
8.  **`audit_trail`**: Tamper-evident log.
    *   `log_id` (PK), `timestamp` (TIMESTAMP), `user_id` (FK), `action` (VARCHAR2), `prev_hash` (VARCHAR2), `current_hash` (VARCHAR2).
9.  **`document_metadata`**: File upload info.
    *   `file_id` (UUID, PK), `doc_id` (FK), `file_name` (VARCHAR2), `scan_status` (VARCHAR2), `storage_path` (VARCHAR2).
10. **`ab_test_metrics`**: Telemetry for A/B testing.
    *   `metric_id` (PK), `experiment_id` (VARCHAR2), `user_id` (FK), `variant` (VARCHAR2), `event_value` (NUMBER).

### 5.2 Key Relationships
*   **One-to-Many:** `tenants` $\rightarrow$ `users` (via `user_tenant_mapping`).
*   **One-to-One:** `documents` $\rightarrow$ `document_content`.
*   **Many-to-One:** `audit_trail` $\rightarrow$ `users`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi utilizes three distinct physical environments within the on-premise data center. No cloud mirroring is permitted.

**Development (DEV):**
*   **Purpose:** Feature integration and unit testing.
*   **Hardware:** 2x Virtual Machines (16GB RAM, 8 vCPUs).
*   **DB:** Oracle XE (Express Edition).
*   **Deploy Cycle:** Continuous Integration (on commit).

**Staging (STG):**
*   **Purpose:** QA, UAT, and FedRAMP compliance pre-audits.
*   **Hardware:** 4x Physical Blades (64GB RAM, 16 vCPUs) mimicking production.
*   **DB:** Oracle 19c (Standard Edition) - mirrored schema from Prod.
*   **Deploy Cycle:** Bi-weekly.

**Production (PROD):**
*   **Purpose:** Live customer traffic.
*   **Hardware:** High-availability cluster (128GB RAM, 32 vCPUs per node), Load-balanced.
*   **DB:** Oracle 19c (Enterprise Edition) with RAC (Real Application Clusters).
*   **Deploy Cycle:** **Weekly Release Train (Tuesdays at 02:00 AM).**

### 6.2 The Release Train
The "Weekly Release Train" is a non-negotiable deployment policy. 
*   **Cut-off:** All code must be merged by Friday 5:00 PM.
*   **QA Window:** Saturday to Monday.
*   **Deployment:** Tuesday 02:00 AM.
*   **Hotfixes:** No hotfixes are permitted outside the train. If a critical bug is found on Wednesday, it must wait for the following Tuesday's train, unless a "Board-Level Emergency" is declared.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** JUnit 5, Mockito.
*   **Coverage Goal:** 80% line coverage.
*   **Requirement:** Every raw SQL query in the `JdbcTemplate` layer must have a corresponding unit test that validates the result set against a H2 in-memory database.

### 7.2 Integration Testing
*   **Framework:** SpringBootTest, Testcontainers (for Oracle).
*   **Focus:** Testing the boundary between the API Gateway and the modular monolith. 
*   **Scenario:** Validating that a request to `/api/v1/collab` is correctly routed and the OAuth2 token is validated before hitting the business logic.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Selenium / Playwright.
*   **Focus:** Critical user journeys.
*   **Key Test Case:** "Teacher creates document $\rightarrow$ Student joins $\rightarrow$ Both edit simultaneously $\rightarrow$ Changes persist in Oracle DB."

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor announces EOL for core library | Medium | High | Escalate to Steering Committee for additional funding to replace the library. |
| **R-02** | Key Architect leaving company in 3 months | High | High | Engage external consultant for an independent assessment and knowledge transfer. |
| **R-03** | Raw SQL technical debt causes migration failure | High | Medium | Mandatory manual review of all raw SQL queries during the "Release Train" QA window. |
| **R-04** | FedRAMP audit failure | Low | Critical | Weekly compliance checks against the FedRAMP High baseline. |

**Impact Matrix:**
*   **Critical:** Project termination or total budget loss.
*   **High:** Milestone delay > 1 month or > $100k cost increase.
*   **Medium:** Feature scope reduction.
*   **Low:** Minor timeline shift.

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Description
*   **Phase 1: Foundation (Now - April 2026):** Setting up the on-premise infrastructure, API Gateway, and Basic Auth.
*   **Phase 2: Core Features (April 2026 - June 2026):** Implementation of A/B testing and Notification systems.
*   **Phase 3: Compliance & Scaling (June 2026 - August 2026):** FedRAMP hardening and performance tuning.

### 9.2 Key Milestones
| Milestone | Target Date | Dependency | Success Criteria |
| :--- | :--- | :--- | :--- |
| **M1: Stakeholder Demo** | 2026-04-15 | All "In Progress" features must be in STG. | Sign-off from CTO and Board. |
| **M2: First Paying Customer**| 2026-06-15 | M1 Sign-off + FedRAMP provisional auth. | Invoice issued for > $10k. |
| **M3: Performance Benchmarks**| 2026-08-15 | M2 Customer Onboarding. | < 200ms latency for 95% of API calls. |

---

## 10. MEETING NOTES (Shared Running Document)
*Note: This is an excerpt from the 200-page unsearchable running document. Formatting is inconsistent.*

**Meeting Date: 2023-11-12**
**Attendees:** Kamau, Priya, Bram, Omar
**Discussion:**
Kamau wants to push the release train to twice a week. Bram says "absolutely not" because the QA cycle for Oracle migrations is too long. Priya is annoyed that the load balancer is still dropping WebSocket packets. Omar mentions that the support tickets for the internal beta are spiking.
**Decision:** Keep the weekly release train. Priya to investigate the load balancer settings.

**Meeting Date: 2023-12-05**
**Attendees:** Kamau, Priya, Bram, Omar
**Discussion:**
The team is discussing the raw SQL usage. Kamau argues it's necessary for the 200ms latency target. Bram points out that the last three migrations failed because the ORM didn't know about the raw SQL views. There is a tense silence. Kamau and Priya stop speaking to each other for the rest of the meeting. 
**Decision:** No change to raw SQL usage, but Bram will add a "SQL Checklist" to the release train.

**Meeting Date: 2024-01-20**
**Attendees:** Kamau, Priya, Bram, Omar
**Discussion:**
The vendor EOL announcement came in. We need more money for the replacement. Kamau says he will handle the Steering Committee. Omar asks about the WORM storage for the audit logs. Priya says the hardware is still stuck in procurement. 
**Decision:** Escalate R-01 to the board. Mark Audit Trail as "Blocked."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,200,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $2,800,000 | 4 full-time engineers (3 years), benefits, and bonuses. |
| **Infrastructure** | $1,200,000 | On-premise servers, Oracle Enterprise licenses, WORM storage. |
| **Tools & Licensing** | $400,000 | IDEs, Security scanning tools (Snyk, SonarQube), RabbitMQ Enterprise. |
| **Consulting** | $300,000 | External Architect for R-02 and FedRAMP auditor. |
| **Contingency** | $500,000 | Reserved for vendor EOL replacement and hardware overruns. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Protocol
Because 30% of the codebase bypasses the ORM, the following protocol must be followed for every schema change:
1.  Extract all `JdbcTemplate` calls from the codebase.
2.  Run the proposed `ALTER TABLE` script against a clone of the production database.
3.  Execute all extracted raw SQL queries.
4.  Verify that the result sets match the expected output.
5.  Sign off in the "Release Train" checklist.

### Appendix B: FedRAMP Control Mapping
Project Delphi must adhere to the following specific controls:
*   **AC-2 (Account Management):** Managed via the `users` and `user_tenant_mapping` tables.
*   **AU-2 (Event Logging):** Implemented via the `audit_trail` table and WORM storage.
*   **SC-7 (Boundary Protection):** Enforced by the on-premise data center firewall and API Gateway.
*   **IA-2 (Identification and Authentication):** Multi-factor authentication required for all administrative access to the Oracle DB.