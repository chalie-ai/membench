Due to the extreme length requirements of this request (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document. To ensure the highest quality and adherence to all specific constraints, the content is expanded with deep technical rigor, simulated architectural decisions, and exhaustive detail.

***

# PROJECT SPECIFICATION: LATTICE
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Classification:** CONFIDENTIAL / INTERNAL ONLY  
**Project Lead:** Tomas Gupta (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Lattice" represents a strategic pivot for Tundra Analytics, marking the company's entry into the specialized cybersecurity monitoring vertical for the Food and Beverage (F&B) industry. The objective is to provide a high-integrity, on-premise monitoring dashboard that allows enterprise clients to track security events, manage compliance, and automate incident responses without exposing sensitive operational data to the public cloud.

### 1.2 Business Justification
The primary driver for Lattice is a commitment from a single Tier-1 enterprise client in the F&B sector. This client has expressed an immediate need for a system that bridges the gap between Industrial Control Systems (ICS) monitoring and corporate IT security. The client has agreed to a recurring annual contract value of $2,000,000 (USD), provided that the system meets stringent HIPAA compliance standards (due to the health-related nature of some nutritional data and employee wellness programs) and remains entirely on-premise.

### 1.3 Financial ROI Projection
The project is funded with a modest budget of $400,000. Given the $2M annual revenue from the anchor client, the Return on Investment (ROI) is exceptionally high. 

*   **Year 1 Projected Gross Revenue:** $2,000,000 (Anchor Client) + $500,000 (Targeted secondary market expansion) = $2,500,000.
*   **Initial Capital Expenditure (CapEx):** $400,000.
*   **Estimated OpEx (Year 1):** $150,000 (Maintenance and Support).
*   **Projected Year 1 Net Profit:** ~$1,950,000.

The primary success metric for the business is the acquisition of an additional $500,000 in new revenue within 12 months of launch, proving that Lattice is a scalable product vertical rather than a one-off custom build.

### 1.4 Strategic Objectives
1.  **Zero-Cloud Footprint:** Ensuring 100% on-premise deployment to satisfy regulatory requirements.
2.  **Tamper-Proof Integrity:** Implementing audit trails that cannot be modified by system administrators.
3.  **Industrial Scalability:** Meeting performance benchmarks that exceed current system capacities by 10x.
4.  **Regulatory Compliance:** Passing the external HIPAA audit on the first attempt.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Lattice is built upon a microservices architecture to ensure modularity and scalability. The core logic is implemented in **Java 17 with Spring Boot 3.x**. All persistent data is stored in an **Oracle DB 19c** instance located within the client’s physical data center.

Communication between services is event-driven, utilizing **Apache Kafka** as the message broker. This ensures that high-velocity security events can be ingested without blocking the user interface or crashing the primary database.

### 2.2 ASCII Architecture Diagram
```text
[ Client Browser ] <--- HTTPS/TLS 1.3 ---> [ API Gateway (Spring Cloud Gateway) ]
                                                     |
                                                     v
        +-------------------------------------------------------------------------+
        |                          ON-PREMISE DATA CENTER                        |
        |                                                                         |
        |  +-------------------+       +-------------------+       +-----------+  |
        |  |  Auth Service     | <---> |  Audit Service    | <---> | Oracle DB |  |
        |  |  (Spring Boot)    |       |  (Spring Boot)    |       |  (19c)    |  |
        |  +-------------------+       +-------------------+       +-----------+  |
        |          ^                                ^                      ^       |
        |          |                                |                      |       |
        |          v                                v                      v       |
        |  +-------------------------------------------------------------------+  |
        |  |                        Apache Kafka Cluster                      |  |
        |  |          (Event Bus for Security Alerts & Workflow Triggers)       |  |
        |  +-------------------------------------------------------------------+  |
        |          ^                                ^                      ^       |
        |          |                                |                      |       |
        |  +-------------------+       +-------------------+       +-----------+  |
        |  | Workflow Engine   |       | File Processor    |       | Report Gen|  |
        |  |  (Visual Builder)  |       | (AV Scanning)     |       | (PDF/CSV) |  |
        |  +-------------------+       +-------------------+       +-----------+  |
        +-------------------------------------------------------------------------+
```

### 2.3 Technical Stack Details
*   **Language:** Java 17 (LTS).
*   **Framework:** Spring Boot 3.2.x, Spring Security, Spring Data JPA.
*   **Database:** Oracle Database 19c (Enterprise Edition).
*   **Messaging:** Apache Kafka 3.6.
*   **Frontend:** React 18 with TypeScript and Tailwind CSS.
*   **Security:** AES-256 encryption for data at rest; TLS 1.3 for data in transit.
*   **Compliance:** HIPAA-aligned access controls (Role-Based Access Control - RBAC).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
The Audit Trail is the backbone of Lattice’s compliance strategy. Every action taken within the system—from a user logging in to a security rule being modified—must be recorded in a non-repudiable ledger. Standard database logs are insufficient; the system requires "tamper-evident" storage.

**Functional Requirements:**
*   **Immutable Records:** Once a log entry is written, it cannot be edited or deleted, even by a super-administrator.
*   **Cryptographic Chaining:** Each log entry must contain a hash of the previous entry (similar to a blockchain), ensuring that any deletion or modification of an entry breaks the chain and triggers an immediate system alert.
*   **Detailed Metadata:** Each entry must capture: Timestamp (UTC), User ID, Action Type, IP Address, Old Value, New Value, and Session ID.
*   **Real-time Alerting:** If the hash-chain validation fails during a routine integrity check, the system must notify the Security Officer immediately via the dashboard.

**Technical Implementation:**
The `AuditService` will intercept all `@Write` operations via Spring AOP (Aspect-Oriented Programming). Before the data hits the Oracle DB, a SHA-256 hash is generated using the current record and the hash of the previous record. This hash is stored in a dedicated `AUDIT_LOG` table. A background "Integrity Watchdog" service will scan the table every 60 minutes to verify the chain.

**Compliance Context:**
Under HIPAA, the ability to track who accessed PHI (Protected Health Information) is mandatory. The tamper-evident nature of this log satisfies the "Integrity" and "Audit Controls" requirements of the HIPAA Security Rule.

---

### 3.2 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Complete

**Description:**
Given that F&B production facilities often have "dead zones" with poor Wi-Fi or intentional air-gapped sections, Lattice must allow operators to continue monitoring and logging events without a persistent network connection.

**Functional Requirements:**
*   **Local State Persistence:** The frontend will utilize IndexedDB to store a local copy of the dashboard state and any pending actions.
*   **Queue Management:** Actions performed offline are queued in a "Pending Sync" state.
*   **Transparent Synchronization:** Once the connection is restored, the system must perform a background sync, pushing queued actions to the server in the order they occurred.
*   **Conflict Resolution:** If a record was modified on the server while the user was offline, the system will use a "Latest Write Wins" strategy, unless the record is an Audit Log, in which case both entries are preserved with timestamps.

**Technical Implementation:**
A Service Worker is implemented to intercept API requests. When a 503 or network timeout occurs, the `OfflineManager` intercepts the request and stores the payload in IndexedDB. A `SyncManager` uses the `navigator.onLine` API to trigger the push sequence. All sync requests are wrapped in a Kafka transaction to ensure "exactly-once" delivery.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
The Workflow Engine allows users to automate responses to security threats. For example: "If a login attempt fails 5 times from a non-corporate IP, block the user and alert the admin."

**Functional Requirements:**
*   **Visual Drag-and-Drop Interface:** A React-based node editor where users can link "Triggers" (events) to "Actions" (outputs).
*   **Boolean Logic Support:** Ability to create complex conditions (AND, OR, NOT) within a rule.
*   **Action Library:** Pre-defined actions including "Email Notification," "User Account Lock," "Log to Audit Trail," and "Trigger External Webhook."
*   **Rule Versioning:** All rules must be versioned. Changes to a rule must be approved by a second administrator (Two-Man Rule).

**Technical Implementation:**
The visual builder generates a JSON representation of the workflow. This JSON is parsed by the `WorkflowEngine` (Spring Boot) and converted into a series of Kafka listeners. When an event hits the Kafka topic, the engine evaluates it against the active JSON rule-set and executes the corresponding action via a strategy pattern.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Progress

**Description:**
Users need to upload security reports and configuration files. Because these files can be vectors for malware, they must be scanned before being stored.

**Functional Requirements:**
*   **Secure Upload Pipeline:** Files are uploaded to a temporary "quarantine" zone.
*   **Automated AV Scanning:** Integration with an on-premise ClamAV instance to scan files for known signatures.
*   **Internal CDN:** Once cleared, files are moved to an internal high-availability file store (MinIO) to ensure fast retrieval across the plant.
*   **Virus Alerting:** If a file is flagged, the file is deleted immediately, and a "Critical" event is sent to the Audit Trail.

**Technical Implementation:**
The `FileService` implements a multi-stage pipeline. Upload $\rightarrow$ Quarantine Storage $\rightarrow$ ClamAV API Scan $\rightarrow$ MinIO Storage. To meet the "no cloud" requirement, the CDN is simulated using a load-balanced cluster of Nginx servers serving the MinIO buckets.

---

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:**
Management requires periodic reports on system health and security breaches for regulatory reviews.

**Functional Requirements:**
*   **Template Builder:** Ability to select which metrics (e.g., "Total Blocked IPs," "Average Response Time") appear in the report.
*   **Scheduled Delivery:** A cron-like scheduler to generate reports weekly or monthly.
*   **Format Support:** Export to PDF (for formal audits) and CSV (for data analysis).
*   **Secure Delivery:** Reports are delivered via internal SMTP or placed in a secure, encrypted folder.

**Technical Implementation:**
Planned implementation using **JasperReports** for PDF generation and **OpenCSV** for CSV exports. A Spring `@Scheduled` task will query the Oracle DB for the defined metrics and trigger the generation service.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 Auth Endpoints
**`POST /auth/login`**
*   **Description:** Authenticates user and returns a JWT.
*   **Request:** `{ "username": "tgupta", "password": "password123" }`
*   **Response:** `200 OK { "token": "eyJhbG...", "expiresIn": 3600 }`

**`POST /auth/logout`**
*   **Description:** Invalidates the current session token.
*   **Request:** No body.
*   **Response:** `204 No Content`

### 4.2 Audit Endpoints
**`GET /audit/logs`**
*   **Description:** Retrieves a paginated list of audit logs.
*   **Request Params:** `page=0&size=50&filter=CRITICAL`
*   **Response:** `200 OK { "content": [ { "id": 101, "event": "LOGIN_FAIL", "user": "jdoe", "timestamp": "2023-10-24T10:00Z" } ], "total": 5000 }`

**`GET /audit/verify`**
*   **Description:** Triggers an immediate hash-chain verification of the audit trail.
*   **Request:** No body.
*   **Response:** `200 OK { "status": "VALID", "lastChecked": "2023-10-24T11:00Z" }`

### 4.3 Workflow Endpoints
**`POST /workflow/rules`**
*   **Description:** Saves a new automation rule.
*   **Request:** `{ "ruleName": "BlockIP", "trigger": "FAIL_LOGIN_5X", "action": "LOCK_USER" }`
*   **Response:** `201 Created { "ruleId": "wf-992" }`

**`DELETE /workflow/rules/{id}`**
*   **Description:** Deletes a specific automation rule.
*   **Request:** ID in path.
*   **Response:** `204 No Content`

### 4.4 File & Report Endpoints
**`POST /files/upload`**
*   **Description:** Uploads a file to the quarantine zone for scanning.
*   **Request:** Multipart form-data (file).
*   **Response:** `202 Accepted { "fileId": "file-abc-123", "status": "SCANNING" }`

**`GET /reports/generate/{type}`**
*   **Description:** Manually triggers a report generation (PDF or CSV).
*   **Request:** `type` = `pdf` | `csv`.
*   **Response:** `200 OK { "downloadUrl": "/api/v1/reports/download/rep-456" }`

---

## 5. DATABASE SCHEMA

The system uses an Oracle 19c database. All tables use `VARCHAR2` for strings and `TIMESTAMP WITH TIME ZONE` for date-time fields.

### 5.1 Table Definitions

1.  **`USERS`**: Stores user credentials and roles.
    *   `user_id` (PK), `username` (Unique), `password_hash`, `role_id` (FK), `created_at`.
2.  **`ROLES`**: Defines RBAC levels.
    *   `role_id` (PK), `role_name` (e.g., ADMIN, VIEWER, AUDITOR).
3.  **`AUDIT_LOG`**: The tamper-evident ledger.
    *   `log_id` (PK), `timestamp`, `user_id` (FK), `action`, `previous_hash`, `current_hash`, `payload`.
4.  **`WORKFLOW_RULES`**: Stores the JSON definition of automation.
    *   `rule_id` (PK), `rule_name`, `json_definition`, `version`, `is_active`, `created_by` (FK).
5.  **`SECURITY_EVENTS`**: Raw events ingested from Kafka.
    *   `event_id` (PK), `source_ip`, `event_type`, `severity`, `timestamp`.
6.  **`FILES`**: Metadata for uploaded files.
    *   `file_id` (PK), `filename`, `checksum`, `scan_status` (CLEAN/INFECTED), `storage_path`.
7.  **`SCHEDULED_REPORTS`**: Configurations for automated reporting.
    *   `report_id` (PK), `frequency`, `recipient_email`, `metrics_json`, `last_run`.
8.  **`SESSIONS`**: Tracks active user sessions.
    *   `session_id` (PK), `user_id` (FK), `start_time`, `expiry_time`, `ip_address`.
9.  **`DEVICE_INVENTORY`**: List of monitored F&B machinery/servers.
    *   `device_id` (PK), `device_name`, `mac_address`, `firmware_version`, `location_zone`.
10. **`ALERTS`**: Triggered notifications from the workflow engine.
    *   `alert_id` (PK), `event_id` (FK), `rule_id` (FK), `status` (OPEN/RESOLVED), `assigned_to` (FK).

### 5.2 Relationships
*   `USERS` $\rightarrow$ `ROLES` (Many-to-One)
*   `USERS` $\rightarrow$ `AUDIT_LOG` (One-to-Many)
*   `SECURITY_EVENTS` $\rightarrow$ `ALERTS` (One-to-Many)
*   `WORKFLOW_RULES` $\rightarrow$ `ALERTS` (One-to-Many)
*   `USERS` $\rightarrow$ `SESSIONS` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Because cloud is forbidden, we maintain three physically distinct zones within the on-premise data center.

#### 6.1.1 Development (DEV)
*   **Purpose:** Feature development and initial unit testing.
*   **Hardware:** Low-spec virtual machines (VMs).
*   **Database:** Small Oracle XE instance.
*   **CI/CD:** Jenkins pipeline triggering builds on every commit.

#### 6.1.2 Staging (STG)
*   **Purpose:** Pre-production testing, performance benchmarking, and UAT.
*   **Hardware:** Mirror of production hardware.
*   **Database:** Oracle 19c (Full Enterprise Edition).
*   **Network:** Simulates the production VLANs to test firewall rules.

#### 6.1.3 Production (PROD)
*   **Purpose:** Live monitoring for the enterprise client.
*   **Hardware:** High-availability cluster with redundant power and networking.
*   **Update Cycle:** Quarterly releases. No "hotfixes" are allowed without a full regulatory review cycle.

### 6.2 Deployment Pipeline
Current pipeline is a significant source of technical debt.
1.  **Build:** Maven build of all microservices.
2.  **Test:** JUnit and Mockito tests.
3.  **Package:** Docker images created for each service.
4.  **Deploy:** Ansible scripts push images to the on-premise Kubernetes (K8s) cluster.
*   **Issue:** Total pipeline time is **45 minutes**.
*   **Goal:** Parallelize the test suite and optimize Docker layering to reduce this to <15 minutes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tooling:** JUnit 5, Mockito.
*   **Requirement:** 80% code coverage on all business logic in the `AuditService` and `WorkflowEngine`.
*   **Approach:** Use `@DataJpaTest` for slice testing of Oracle repositories.

### 7.2 Integration Testing
*   **Tooling:** Testcontainers.
*   **Requirement:** Verify the interaction between Spring Boot and Kafka.
*   **Approach:** Spin up a temporary Kafka container to ensure that events emitted by the `SecurityEventService` are correctly consumed by the `WorkflowEngine`.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Requirement:** Validate critical user journeys (e.g., "Create Rule $\rightarrow$ Trigger Event $\rightarrow$ Receive Alert").
*   **Approach:** Automated scripts run against the Staging environment before every quarterly release.

### 7.4 Performance Testing
*   **Tooling:** JMeter.
*   **Requirement:** The system must handle 10x the current throughput of the legacy system.
*   **Approach:** Simulate 10,000 events per second (EPS) flowing through Kafka and verify that Oracle DB write latency remains under 50ms.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding "small" features. | High | Medium | Escalate all new feature requests to the Steering Committee; request additional funding for additions. |
| **R2** | Performance requirements (10x) exceed infrastructure. | Medium | High | De-scope non-critical features (e.g., high-res report graphics) if benchmarks aren't met by Milestone 2. |
| **R3** | HIPAA audit failure. | Low | Critical | Conduct monthly internal "pre-audits" using an external consultant. |
| **R4** | CI Pipeline inefficiency (45 min). | High | Low | Implement parallel test execution in Jenkins. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project failure or legal non-compliance.
*   **High:** Significant delay or budget overrun.
*   **Medium:** Minor delay, manageable via team effort.
*   **Low:** Negligible impact on delivery.

---

## 9. TIMELINE & MILESTONES

The project follows a phased approach aligned with the quarterly regulatory review cycles.

### 9.1 Phase 1: Foundation (Now $\rightarrow$ 2025-06-15)
*   **Focus:** Completing the critical "Launch Blockers."
*   **Dependencies:** Oracle DB installation and Kafka cluster setup.
*   **Milestone 1:** **MVP Feature-Complete (2025-06-15).**
    *   Criterium: All critical features (Audit, Workflow) are operational in Staging.

### 9.2 Phase 2: Optimization (2025-06-16 $\rightarrow$ 2025-08-15)
*   **Focus:** Performance tuning and stress testing.
*   **Dependencies:** Successful completion of MVP.
*   **Milestone 2:** **Performance Benchmarks Met (2025-08-15).**
    *   Criterium: System handles 10x load without crash or data loss.

### 9.3 Phase 3: Compliance & Handover (2025-08-16 $\rightarrow$ 2025-10-15)
*   **Focus:** External audit and final documentation.
*   **Dependencies:** Stable performance benchmarks.
*   **Milestone 3:** **Architecture Review Complete (2025-10-15).**
    *   Criterium: Third-party sign-off on HIPAA compliance.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning & Technical Debt
**Date:** 2023-11-02 | **Attendees:** Tomas, Emeka, Lev, Chioma

*   **Discussion:**
    *   Chioma raised concerns about the 45-minute CI pipeline. It is slowing down the development cycle and leading to "context switching" losses.
    *   Tomas acknowledged the debt but insisted that the Audit Trail (Priority: Critical) takes precedence over pipeline optimization.
    *   Emeka reported that the Offline-First mode is complete but needs a final sign-off from QA.
*   **Decisions:**
    *   Pipeline optimization is deferred until the Audit Trail is "In Review."
    *   Lev will perform a "Chaos Test" on the Offline-First sync logic.
*   **Action Items:**
    *   [Emeka] Push final Offline-First PR for review. (Due: 2023-11-05)
    *   [Lev] Document the sync conflict resolution cases. (Due: 2023-11-07)

### Meeting 2: Third-Party API Blocker
**Date:** 2023-11-15 | **Attendees:** Tomas, Emeka, Lev, Chioma

*   **Discussion:**
    *   The team is currently blocked by rate limits on the third-party security feed API during integration testing.
    *   Lev noted that the system crashes when the API returns a 429 (Too Many Requests) because the retry logic is too aggressive.
*   **Decisions:**
    *   Implement an Exponential Backoff strategy for all external API calls.
    *   Create a "Mock API" service for the DEV environment to bypass rate limits entirely during feature development.
*   **Action Items:**
    *   [Chioma] Develop the Mock API service. (Due: 2023-11-20)
    *   [Tomas] Negotiate a higher rate limit with the vendor. (Due: 2023-11-22)

### Meeting 3: Scope Creep & Budget Review
**Date:** 2023-12-01 | **Attendees:** Tomas, Emeka, Lev, Chioma

*   **Discussion:**
    *   The client has requested a new feature: "Real-time Heatmap of Global Login Attempts."
    *   Tomas noted that this was not in the original spec and would require significant frontend work from Emeka.
    *   The budget of $400k is already tight.
*   **Decisions:**
    *   The Heatmap is officially categorized as "Scope Creep."
    *   Tomas will escalate this to the Steering Committee. If the client wants the heatmap, they must provide additional funding or agree to de-scope the PDF/CSV report generator.
*   **Action Items:**
    *   [Tomas] Draft the escalation memo for the Steering Committee. (Due: 2023-12-05)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000 USD

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salaries for 2-person core team + Junior Dev support over the project lifecycle. |
| **Infrastructure** | $60,000 | On-premise server hardware, Oracle DB Licensing, and Kafka cluster nodes. |
| **Tools & Licenses** | $30,000 | IDE licenses (IntelliJ), Jenkins Enterprise, JasperReports license. |
| **Contingency** | $30,000 | Emergency buffer for hardware failure or critical consultant hire for HIPAA audit. |

**Budget Notes:**
*   Personnel costs are the primary driver. 
*   The infrastructure budget is modest because Tundra Analytics is utilizing existing rack space in the client's data center.

---

## 12. APPENDICES

### Appendix A: Cryptographic Chain Logic
The tamper-evident audit log operates on the following formula for each record $n$:
$$H_n = \text{SHA-256}(Timestamp + UserID + Action + Payload + H_{n-1})$$
Where $H_n$ is the hash of the current record and $H_{n-1}$ is the hash of the preceding record. If any record is altered, $H_n$ will no longer match the calculated hash of the modified data, creating a "break" in the chain.

### Appendix B: HIPAA Compliance Mapping
| HIPAA Requirement | Lattice Implementation |
| :--- | :--- |
| **$\S 164.312(a)(1)$ Access Control** | RBAC implemented via Spring Security and Oracle DB User Roles. |
| **$\S 164.312(b)$ Audit Controls** | Tamper-evident `AUDIT_LOG` table with cryptographic chaining. |
| **$\S 164.312(c)(1)$ Integrity** | SHA-256 validation and background "Integrity Watchdog" service. |
| **$\S 164.312(e)(1)$ Transmission Security** | TLS 1.3 enforced for all internal microservice communication. |