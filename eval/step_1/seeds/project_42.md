# PROJECT SPECIFICATION: PROJECT MONOLITH
**Version:** 1.0.4  
**Status:** Final Baseline  
**Classification:** Internal Confidential  
**Date:** May 1, 2026  
**Project Lead:** Veda Oduya (Tech Lead)  
**Company:** Deepwell Data  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Monolith is a mission-critical internal enterprise tool developed by Deepwell Data to ensure regulatory compliance within the renewable energy sector. As the energy market shifts toward decentralized grids and green credits, governmental bodies have introduced strict reporting and auditing requirements regarding energy provenance and financial transparency. Failure to meet these requirements by the legal deadline of November 15, 2026, would result in severe fines and the potential loss of operating licenses.

Monolith serves as the central nervous system for Deepwell Data’s compliance operations. It is designed to ingest massive streams of energy data, validate financial transactions, and maintain an immutable record of all regulatory activities. The system must handle sensitive financial data, necessitating a PCI DSS Level 1 certification, as the tool will process credit card transactions directly for regulatory filing fees and vendor payments.

### 1.2 Business Justification
The current legacy system—a fragmented collection of spreadsheets and outdated SQL databases—is incapable of producing the "tamper-evident" reports required by the new legislation. Manual data aggregation currently takes 400 man-hours per month, with a high error rate that poses a significant legal risk. Monolith automates this pipeline, transforming raw energy metrics into compliant reports in real-time.

The urgency is driven by the "Hard Legal Deadline." There is no grace period for compliance. The project is tasked with replacing the existing fragmented infrastructure with a high-performance, scalable Go-based microservices architecture.

### 1.3 ROI Projection
The financial justification for Monolith is based on two primary drivers: cost reduction and risk mitigation.

1.  **Operational Cost Reduction:** The legacy system is inefficient, costing $0.42 per transaction in cloud compute and manual labor. Monolith aims to reduce this to $0.27 per transaction (a 35% reduction). Based on an estimated volume of 10 million transactions per quarter, this results in an annual saving of approximately $1.8 million.
2.  **Risk Mitigation:** The potential fines for non-compliance are estimated at $50,000 per day of delinquency. By hitting the November 15 deadline, the company avoids a catastrophic liability.
3.  **Customer Satisfaction:** By improving the accuracy and speed of compliance reporting for partners, Deepwell Data projects an NPS (Net Promoter Score) increase from 12 to 40+ within the first quarter post-launch.

**Total Budget:** $400,000. Given the urgency and the team size (20+ people), the budget is modest, requiring a lean approach to procurement and a focus on existing GCP credits.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Monolith is built using a **Hexagonal Architecture** to decouple the core business logic (Domain) from external dependencies (Infrastructure). This ensures that the system remains testable and adaptable, particularly as we migrate away from the end-of-life vendor dependency.

-   **The Core (Domain):** Contains the business entities and use cases. It has no knowledge of databases, APIs, or external services.
-   **Ports:** Interfaces that define how the core wants to interact with the outside world (e.g., `UserRepository` interface).
-   **Adapters:** Concrete implementations of ports. For example, a `CockroachDBUserRepository` implements the `UserRepository` port.

### 2.2 Technical Stack
-   **Language:** Go 1.21+ (Chosen for concurrency and performance).
-   **Communication:** gRPC (Internal microservice communication) and REST/JSON (External API gateways).
-   **Database:** CockroachDB (Distributed SQL for high availability and strong consistency).
-   **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
-   **Security:** PCI DSS Level 1 compliance standards, utilizing envelope encryption for credit card data.

### 2.3 System Diagram (ASCII Representation)

```text
                                 [ EXTERNAL CLIENTS ]
                                          |
                                  (REST / HTTPS / TLS)
                                          |
                                  [ API GATEWAY / K8S INGRESS ]
                                          |
         _________________________________|_________________________________
        |                                 |                                 |
 [ AUTH SERVICE ]                 [ COMPLIANCE SERVICE ]             [ NOTIFICATION SERVICE ]
 (RBAC / JWT)                     (Audit Trails / Reports)          (Email/SMS/Push)
        |                                 |                                 |
  [ Port: UserRepo ]              [ Port: AuditRepo ]                [ Port: NotifRepo ]
        |                                 |                                 |
 [ Adapter: CRDB ]                [ Adapter: CRDB / S3 ]             [ Adapter: SendGrid/Twilio ]
        |_________________________________|_________________________________|
                                          |
                                 [ COCKROACHDB CLUSTER ]
                                 (Multi-Region Deployment)
```

### 2.4 Deployment Strategy
The current deployment process is highly centralized. All deployments to `dev`, `staging`, and `prod` are performed manually by a single DevOps Engineer. 

**Critical Vulnerability:** This creates a "Bus Factor of 1." If the DevOps lead is unavailable, the pipeline freezes. While the team is moving toward GitOps, the current mandate is manual deployment to ensure strict PCI DSS change-control auditing.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
This feature provides the foundational security layer for Monolith. Because the system handles PCI DSS data and regulatory filings, a robust RBAC system is mandatory. It must support multi-tenancy across different energy departments.

**Functional Requirements:**
-   **Authentication:** Implementation of OAuth2/OpenID Connect with mandatory Multi-Factor Authentication (MFA) for all administrative accounts.
-   **Role Hierarchy:**
    -   *Super Admin:* Full system access, user management, and audit log overrides.
    -   *Compliance Officer:* Ability to create and sign off on regulatory reports.
    -   *Data Analyst:* Read-only access to energy metrics; no access to PII or credit card data.
    -   *Auditor:* Read-only access to the tamper-evident audit trails.
-   **Session Management:** JWT-based sessions with a 15-minute sliding expiration and secure HTTP-only cookies.

**Technical Detail:**
The current implementation is plagued by a **3,000-line "God Class"** (`AuthManager.go`) that handles authentication, logging, and email dispatch. This class must be refactored into separate domain services before the security audit on 2026-09-15.

**PCI DSS Constraint:** 
All authentication logs must be stored in the tamper-evident audit trail. No passwords or secrets may be logged in plain text.

---

### 3.2 Notification System
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
The notification system ensures that compliance officers are alerted to data anomalies, filing deadlines, and security breaches in real-time. Given the legal nature of the project, "missed notifications" are considered a project failure.

**Functional Requirements:**
-   **Multi-Channel Delivery:**
    -   **Email:** For official reports and weekly summaries (Integration: SendGrid).
    -   **SMS:** For urgent, high-priority alerts (Integration: Twilio).
    -   **In-App:** A notification bell and toast system for users currently logged into the dashboard.
    -   **Push:** For mobile alerts via Firebase Cloud Messaging (FCM).
-   **Preference Center:** Users must be able to toggle which channels they receive for specific alert types (e.g., "Email only for reports, SMS for critical errors").
-   **Retry Logic:** Implementation of an exponential backoff strategy for failed delivery attempts to ensure 99.9% delivery success.

**Technical Detail:**
The system uses a producer-consumer pattern. The core business logic publishes an "Event" to a NATS message queue, and the Notification Service consumes these events to route them to the appropriate adapter.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review

**Description:**
To meet renewable energy regulatory standards, Monolith must provide a "source of truth" that proves data was not altered after the fact. This is the core of the compliance requirement.

**Functional Requirements:**
-   **Immutable Records:** Every write operation to the database must be mirrored in an audit log.
-   **Tamper-Evidence:** Each log entry must contain a cryptographic hash of the previous entry (blockchain-style chaining).
-   **Storage:** Logs are stored in a "WORM" (Write Once, Read Many) bucket on GCP Cloud Storage with Object Lock enabled.
-   **Verification Tool:** An internal utility that can scan the entire audit chain to verify that no records have been deleted or modified.

**Technical Detail:**
The system implements a SHA-256 hashing algorithm. Each audit record consists of: `timestamp`, `user_id`, `action`, `resource_id`, `previous_hash`, and `current_hash`.

---

### 3.4 Webhook Integration Framework
**Priority:** Medium | **Status:** In Progress

**Description:**
Monolith needs to interact with third-party energy monitoring tools and financial platforms. The webhook framework allows external systems to push data into Monolith and allows Monolith to trigger events in external tools.

**Functional Requirements:**
-   **Incoming Webhooks:** A flexible endpoint that can accept JSON payloads and route them to specific internal handlers based on a `webhook_id`.
-   **Outgoing Webhooks:** A subscription model where third-party tools can register for events (e.g., `report.completed`).
-   **Security:** Every webhook must be validated using an HMAC signature to prevent spoofing.
-   **Replay Mechanism:** If a third-party endpoint is down, Monolith must store the event and retry delivery every 5, 15, and 60 minutes.

**Technical Detail:**
The framework uses a dynamic routing map stored in CockroachDB, mapping external event types to Go internal function signatures.

---

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:**
To ease the transition from the legacy system, Monolith needs the ability to ingest data in various formats without requiring the user to manually specify the file type.

**Functional Requirements:**
-   **Auto-Detection:** The system must analyze the first 1KB of an uploaded file to determine if it is CSV, JSON, XML, or Parquet.
-   **Bulk Import:** Support for files up to 2GB, processed asynchronously via a background worker.
-   **Export:** Ability to export compliance reports into PDF (for regulators) and CSV (for internal analysis).
-   **Validation:** A "dry run" mode that identifies formatting errors before the final import.

**Technical Detail:**
This will be implemented as a separate "Data-Ingest" microservice using a worker pool to prevent blocking the main API threads.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are served over HTTPS/TLS 1.3. Authentication is required via Bearer Token (`Authorization: Bearer <JWT>`).

### 4.1 Authentication Endpoints
**1. POST `/api/v1/auth/login`**
-   **Description:** Authenticates user and returns JWT.
-   **Request:** `{"email": "user@deepwell.com", "password": "password123", "mfa_code": "123456"}`
-   **Response:** `{"token": "eyJ...", "expires_at": "2026-05-01T12:00:00Z"}`

**2. POST `/api/v1/auth/refresh`**
-   **Description:** Refreshes an expired session token.
-   **Request:** `{"refresh_token": "ref_..."}`
-   **Response:** `{"token": "eyJ...", "expires_at": "..."}`

### 4.2 Compliance & Audit Endpoints
**3. GET `/api/v1/compliance/reports`**
-   **Description:** Fetches a list of all generated regulatory reports.
-   **Request:** Query params `?start_date=2026-01-01&end_date=2026-01-31`
-   **Response:** `[{"report_id": "R1", "status": "verified", "date": "2026-01-15"}]`

**4. POST `/api/v1/compliance/verify-chain`**
-   **Description:** Triggers a full cryptographic scan of the audit trail.
-   **Request:** `{"chain_id": "global_audit_01"}`
-   **Response:** `{"status": "valid", "entries_scanned": 450000, "integrity": "verified"}`

### 4.3 Notification Endpoints
**5. GET `/api/v1/notifications/preferences`**
-   **Description:** Retrieves user notification settings.
-   **Request:** None
-   **Response:** `{"email": true, "sms": false, "push": true}`

**6. PATCH `/api/v1/notifications/preferences`**
-   **Description:** Updates user notification settings.
-   **Request:** `{"sms": true}`
-   **Response:** `{"status": "updated"}`

### 4.4 Webhook Endpoints
**7. POST `/api/v1/webhooks/ingress`**
-   **Description:** Public endpoint for third-party tools to push data.
-   **Request:** `{"event": "energy_spike", "value": 450, "timestamp": "..."}` (Must include `X-Hub-Signature`)
-   **Response:** `{"status": "accepted", "event_id": "evt_998"}`

**8. POST `/api/v1/webhooks/subscribe`**
-   **Description:** Registers a new outgoing webhook URL.
-   **Request:** `{"url": "https://partner.com/callback", "event_type": "report.finalized"}`
-   **Response:** `{"webhook_id": "wh_123", "secret": "shhh_secret"}`

---

## 5. DATABASE SCHEMA

The system utilizes **CockroachDB** for its distributed nature and strong consistency (Serializability).

### 5.1 Table Definitions

1.  **`users`**
    -   `user_id` (UUID, PK)
    -   `email` (String, Unique)
    -   `password_hash` (String)
    -   `mfa_secret` (String)
    -   `created_at` (Timestamp)
2.  **`roles`**
    -   `role_id` (Int, PK)
    -   `role_name` (String) — e.g., 'SuperAdmin', 'Auditor'
3.  **`user_roles`**
    -   `user_id` (UUID, FK)
    -   `role_id` (Int, FK)
    -   *Relationship: Many-to-Many*
4.  **`audit_logs`**
    -   `log_id` (UUID, PK)
    -   `user_id` (UUID, FK)
    -   `action` (String)
    -   `payload` (JSONB)
    -   `previous_hash` (String)
    -   `current_hash` (String)
    -   `created_at` (Timestamp)
5.  **`compliance_reports`**
    -   `report_id` (UUID, PK)
    -   `creator_id` (UUID, FK)
    -   `status` (Enum: Draft, Pending, Verified)
    -   `storage_path` (String) — Path to GCP bucket
    -   `checksum` (String)
6.  **`notification_settings`**
    -   `user_id` (UUID, PK/FK)
    -   `email_enabled` (Boolean)
    -   `sms_enabled` (Boolean)
    -   `push_enabled` (Boolean)
7.  **`webhooks_subscriptions`**
    -   `webhook_id` (UUID, PK)
    -   `target_url` (String)
    -   `event_type` (String)
    -   `secret_token` (String)
8.  **`webhook_logs`**
    -   `log_id` (UUID, PK)
    -   `webhook_id` (UUID, FK)
    -   `response_code` (Int)
    -   `attempt_count` (Int)
    -   `last_attempt` (Timestamp)
9.  **`credit_card_tokens`** (PCI DSS Encrypted)
    -   `token_id` (UUID, PK)
    -   `user_id` (UUID, FK)
    -   `encrypted_card_data` (Blob)
    -   `last_four` (String)
    -   `expiry_date` (Date)
10. **`energy_metrics`**
    -   `metric_id` (UUID, PK)
    -   `source_id` (String)
    -   `value` (Decimal)
    -   `timestamp` (Timestamp)

### 5.2 Relationships
-   `users` $\rightarrow$ `user_roles` $\rightarrow$ `roles` (RBAC Mapping)
-   `users` $\rightarrow$ `audit_logs` (Attribution)
-   `users` $\rightarrow$ `compliance_reports` (Ownership)
-   `users` $\rightarrow$ `notification_settings` (One-to-One)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### Development (`dev`)
-   **Purpose:** Feature experimentation and unit testing.
-   **Infrastructure:** A single GKE cluster with auto-scaling disabled. CockroachDB is run in a single-node container for speed.
-   **Deployment:** Triggered by merges to the `develop` branch.

#### Staging (`stg`)
-   **Purpose:** Pre-production validation and User Acceptance Testing (UAT).
-   **Infrastructure:** Mirrored to Production architecture but with reduced node counts.
-   **Data:** Anonymized production data snapshots.
-   **Deployment:** Manual promotion by the DevOps engineer after QA sign-off.

#### Production (`prod`)
-   **Purpose:** Live regulatory reporting and financial processing.
-   **Infrastructure:** Multi-region GKE deployment across `us-east1`, `us-west1`, and `europe-west1` to ensure zero downtime.
-   **Database:** CockroachDB cluster with 3 nodes per region for survival of regional failure.
-   **Security:** Hardened VPC with no public IPs; access only via IAP (Identity-Aware Proxy) and the API Gateway.

### 6.2 The "Bus Factor 1" Deployment Process
Currently, all deployments follow this strict manual sequence:
1.  DevOps Lead pulls the latest tagged image from Artifact Registry.
2.  Manual update of the Kubernetes manifest YAML files.
3.  `kubectl apply -f` executed against the cluster.
4.  Manual health check of the `/health` endpoint.
5.  Manual update of the "Version" table in the database.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
-   **Approach:** Every domain function must have $>80\%$ code coverage.
-   **Tooling:** `go test` with `testify/assert`.
-   **Focus:** Business logic in the "Core" of the hexagonal architecture. Since the Core has no dependencies, unit tests are fast and deterministic.

### 7.2 Integration Testing
-   **Approach:** Testing the "Adapters" against real (containerized) dependencies.
-   **Tooling:** `Testcontainers-go` to spin up a temporary CockroachDB instance.
-   **Focus:** Verifying that SQL queries are correct and gRPC communication between services is functional.

### 7.3 End-to-End (E2E) Testing
-   **Approach:** Black-box testing of the API Gateway to the Database.
-   **Tooling:** Postman collections and a custom Go-based E2E suite.
-   **Scenario:** "User logs in $\rightarrow$ uploads energy data $\rightarrow$ generates report $\rightarrow$ verifies audit log $\rightarrow$ receives email notification."

### 7.4 Security Testing
-   **Penetration Testing:** A third-party audit is scheduled for 2026-09-15 to verify PCI DSS Level 1 compliance.
-   **Fuzzing:** Using `go-fuzz` on the webhook ingress endpoints to prevent buffer overflow or injection attacks.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | High | Accept risk; monitor weekly; encourage documentation of "God Class." | Veda Oduya |
| R-02 | Primary Vendor EOL (End-of-Life) | Medium | High | Assign dedicated owner to track migration to new vendor. | Yves Nakamura |
| R-03 | Deployment Bus Factor (1 Person) | High | Medium | Cross-train one other engineer on `kubectl` basics. | DevOps Lead |
| R-04 | PCI DSS Audit Failure | Low | Critical | Weekly internal security reviews; strictly follow Level 1 checklist. | Wyatt Moreau |
| R-05 | Budget Overrun for Tools | Medium | Medium | Monitor spend via GCP Billing alerts; prioritize "Must-Have" tools. | Veda Oduya |

### 8.1 Probability/Impact Matrix
-   **High/High:** Immediate action required (Architect departure).
-   **Medium/High:** Dedicated tracking (Vendor EOL).
-   **High/Medium:** Process improvement (Deployment bottleneck).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
-   **Phase 1: Foundation (May - July 2026):** Focus on RBAC, the Core architecture, and the "God Class" refactor.
-   **Phase 2: Compliance Core (July - September 2026):** Focus on Audit Trails, Notification Systems, and Performance Benchmarking.
-   **Phase 3: Hardening & Launch (September - November 2026):** Focus on the Security Audit, Bug Squashing, and Production rollout.

### 9.2 Gantt-Chart Style Timeline

| Activity | May | Jun | Jul | Aug | Sep | Oct | Nov |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Core RBAC Implementation | XXX | XXX | | | | | |
| Notification System Dev | | XXX | XXX | | | | |
| Audit Trail Dev | | | XXX | XXX | | | |
| **M1: Perf Benchmarks (07-15)** | | | **!** | | | | |
| Refactor 'God Class' | | | | XXX | XXX | | |
| **M2: Security Audit (09-15)** | | | | | **!** | | |
| Webhook Integration | | | | | XXX | XXX | |
| Final QA & UAT | | | | | | XXX | |
| **M3: Production Launch (11-15)** | | | | | | | **!** |

---

## 10. MEETING NOTES

*Note: Per company policy, all meetings are recorded via video call. These notes are summaries extracted from the recordings, as the recordings are rarely re-watched.*

### Meeting 1: Architecture Alignment (2026-05-10)
-   **Attendees:** Veda, Yves, Wyatt, Sergei.
-   **Discussion:** Yves raised concerns about CockroachDB latency in the `europe-west1` region. Wyatt insisted that the PCI DSS requirements mean we cannot use a shared database for card data and audit logs.
-   **Decision:** Agreed to use separate keyspaces within CockroachDB to isolate card data. Veda approved the use of gRPC for all internal service calls to reduce overhead.
-   **Action Item:** Sergei to map out the current "God Class" dependencies.

### Meeting 2: The "Vendor Crisis" (2026-06-22)
-   **Attendees:** Veda, Yves.
-   **Discussion:** The primary vendor for energy data ingestion announced EOL for their API v3. If we don't migrate to v4, the data feed will cut off in October.
-   **Decision:** Yves is assigned as the dedicated owner to track the vendor's new SDK. Veda decided we will not delay the project but will build a "Vendor Adapter" to make future switches easier.
-   **Action Item:** Yves to contact vendor support for the Beta SDK.

### Meeting 3: Budget Blockers (2026-08-05)
-   **Attendees:** Veda, Wyatt.
-   **Discussion:** Wyatt reported that the budget approval for the "Hardware Security Module" (HSM) for PCI compliance is still pending from finance. Without it, the security audit in September is at risk.
-   **Decision:** Veda will escalate to the CFO. In the meantime, they will use a software-simulated HSM for the staging environment.
-   **Action Item:** Veda to send "Urgent" email to Finance.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salaries for focused core team members and allocated hours for the 20+ person cross-dept group. |
| **Infrastructure (GCP)** | $60,000 | GKE clusters, CockroachDB Dedicated, Cloud Storage WORM buckets. |
| **Security Tools & Licenses** | $30,000 | PCI DSS auditing software, HSM license, SendGrid/Twilio API costs. |
| **Contingency Fund** | $30,000 | Reserve for emergency vendor migration or overtime pay for the final push. |

**Current Status:** $12,000 spent on initial GCP setup. Pending approval for HSM purchase ($5,000).

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt Analysis
The file `internal/auth/manager.go` is currently 3,142 lines long. It violates the Single Responsibility Principle by performing the following:
1.  Validating JWTs.
2.  Writing audit logs to the database.
3.  Formatting and sending "Welcome" emails via SMTP.
4.  Handling credit card tokenization.
5.  Caching user permissions in an in-memory map.

**Refactoring Plan:**
-   `AuthManager` $\rightarrow$ `AuthService` (Authentication only).
-   `AuditLogger` $\rightarrow$ Moved to `internal/audit` package.
-   `EmailDispatcher` $\rightarrow$ Moved to `internal/notifications` package.
-   `PaymentProcessor` $\rightarrow$ Moved to `internal/payments` package.

### Appendix B: PCI DSS Level 1 Compliance Checklist
To pass the audit on 2026-09-15, the following must be verified:
-   [ ] **Requirement 1:** Firewall configurations block all traffic except for the API Gateway.
-   [ ] **Requirement 3:** All stored credit card data is encrypted using AES-256 with keys rotated annually.
-   [ ] **Requirement 7:** RBAC is strictly enforced; the "Principle of Least Privilege" is applied to all 20+ team members.
-   [ ] **Requirement 10:** Audit trails are immutable and stored on a separate physical/logical volume.
-   [ ] **Requirement 11:** Regular vulnerability scans are performed on the GKE cluster.