# PROJECT SPECIFICATION: BEACON DATA PIPELINE & ANALYTICS PLATFORM
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Company:** Clearpoint Digital  
**Date:** October 24, 2024  
**Classification:** Confidential / Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Beacon" represents a strategic pivot for Clearpoint Digital, marking the transition from a pure service provider to a product-driven organization. The primary driver for this initiative is a high-value enterprise partnership with a Tier-1 aerospace manufacturer. This client has identified a critical gap in their operational telemetry and supply chain analytics, requiring a platform that can process massive volumes of sensor data while adhering to strict on-premise security constraints. 

The aerospace industry operates under rigorous regulatory frameworks (FAA, EASA) and national security protocols, which precludes the use of public cloud infrastructure (AWS, Azure, GCP). Beacon is designed to fill this void by providing a localized, high-performance data pipeline capable of real-time analytics without data leaving the client’s physical data center.

### 1.2 ROI Projection and Financial Viability
The project is anchored by a committed annual recurring revenue (ARR) of $2,000,000 from the anchor client. Given the current funding model—bootstrapping with existing team capacity—the project has a remarkably low initial capital expenditure (CapEx). 

**Projected ROI Analysis (Year 1):**
- **Revenue:** $2,000,000 (Fixed Annual Contract)
- **Estimated Operational Cost (OpEx):** $650,000 (Allocated personnel costs for 15 engineers/product staff across 5 countries).
- **Infrastructure Costs:** $120,000 (On-premise hardware maintenance and Oracle licensing).
- **Net Profit (Year 1):** ~$1,230,000.

The ROI is further amplified by the "product vertical" strategy. By building Beacon as a modular platform rather than a custom one-off tool, Clearpoint Digital can license this software to other aerospace entities facing similar air-gapped requirements. The projected 5-year ROI exceeds 400% as the product moves from a single-client pilot to a broader industry offering.

### 1.3 Strategic Objective
The goal is to deliver a SOC 2 Type II compliant platform that reduces manual data processing time for aerospace engineers by 50%. Success will be measured by the platform's ability to ingest heterogeneous data streams, resolve collaborative conflicts in real-time, and provide a customizable analytical surface for decision-makers.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Beacon utilizes a microservices architecture built on the **Java 17 / Spring Boot 3.2** ecosystem. To satisfy the aerospace client's "No Cloud" mandate, the entire stack is deployed on a private on-premise data center utilizing a VMware vSphere virtualization layer.

Communication between services is primarily event-driven via **Apache Kafka**, ensuring that the high-velocity data pipelines do not block the user-facing analytical dashboards. State management is handled by an **Oracle Database 19c** cluster, chosen for its robust ACID compliance and existing footprints within the client's infrastructure.

### 2.2 System Diagram (ASCII Description)
The following represents the logical flow of data and request handling:

```text
[EXTERNAL DATA SOURCES] --> [INGESTION SERVICE] --> [KAFKA BUS]
                                     |                  |
                                     v                  v
[USER INTERFACE (React)] <--> [API GATEWAY] <--> [ANALYTICS SERVICE]
                                     |                  |
                                     v                  v
                          [COLLABORATION SERVICE] <--> [ORACLE DB 19c]
                                     ^                  ^
                                     |                  |
                          [BILING/SUBSCRIPTION] <--- [AUTH MODULE]
```

**Diagram Component Details:**
1.  **Ingestion Service:** Handles the raw data stream, performs format auto-detection, and pushes events to Kafka.
2.  **Kafka Bus:** The central nervous system. Topics are partitioned by sensor ID and site location to ensure scalability.
3.  **Analytics Service:** Consumes Kafka events, performs aggregations, and populates the Oracle DB.
4.  **Collaboration Service:** Implements Operational Transformation (OT) or CRDTs for real-time editing.
5.  **API Gateway:** The single entry point for the frontend; handles JWT validation and request routing.
6.  **Oracle DB:** The persistent store for configuration, user data, and aggregated metrics.

### 2.3 Security and Compliance
To achieve SOC 2 Type II compliance, the architecture implements:
- **Encryption at Rest:** Oracle Transparent Data Encryption (TDE).
- **Encryption in Transit:** TLS 1.3 for all inter-service and client-to-server communication.
- **Audit Logging:** Every write operation is logged to a read-only audit table with immutable timestamps.
- **IAM:** Integration with the client's Active Directory via LDAP.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** Complete | **Version:** 1.0.0

**Description:**
In the aerospace context, multiple engineers often need to annotate a single data stream or configure a shared pipeline simultaneously. This feature allows multiple users to edit the same configuration file or analytic report in real-time without overwriting each other's changes.

**Technical Implementation:**
The system utilizes a Conflict-free Replicated Data Type (CRDT) approach combined with a WebSocket layer. When a user makes a change, the `CollaborationService` broadcasts a "delta" packet to all other connected clients. The system uses a Last-Writer-Wins (LWW) element set for simple attributes and a sequence-based approach for text fields.

**Detailed Requirements:**
- **Latency:** End-to-end synchronization must occur in < 200ms.
- **Presence:** Users must see a "cursor" and highlight representing other active users.
- **Version History:** Every single change is snapshotted. Users can revert to any version within a 30-day window.
- **Locking Mechanism:** While the system is collaborative, a "Hard Lock" can be placed by an administrator to prevent any changes during a critical review phase.

**Acceptance Criteria:**
- Two users editing the same field simultaneously result in a consistent state across both browsers.
- No data loss occurs during network intermittent disconnection (offline mode with subsequent re-sync).

---

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** In Progress | **Version:** 0.8.0

**Description:**
The dashboard is the primary interface for the analytics platform. Users must be able to build their own views by dragging and dropping widgets (graphs, gauges, tables, and heatmaps) onto a grid.

**Technical Implementation:**
The frontend uses a grid-stack library. Each widget is a micro-frontend component that subscribes to a specific Kafka topic or Oracle query. The layout configuration is stored as a JSON blob in the `user_dashboard_configs` table in Oracle DB.

**Detailed Requirements:**
- **Widget Library:** Must include Line Charts (TimeSeries), Pie Charts (Distribution), Single Value Gauges (Real-time), and Data Tables (Raw logs).
- **Data Binding:** Users can bind a widget to a specific "Data Stream" via a dropdown menu.
- **Persistence:** Dashboards must be saveable as templates and shareable with other team members.
- **Responsiveness:** The grid must automatically snap to a 12-column layout across different screen resolutions.

**Acceptance Criteria:**
- A user can create a dashboard, add three different widget types, arrange them, and save the view.
- Refreshing the page restores the exact layout and data state.

---

### 3.3 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker) | **Status:** In Design | **Version:** 0.1.0

**Description:**
Since Beacon is a product vertical, it requires a built-in mechanism to manage the enterprise client's subscription, track usage metrics (e.g., data volume ingested), and generate monthly invoices.

**Technical Implementation:**
The `BillingService` will track the volume of messages passing through the Kafka bus. It will integrate with the client's procurement system via a secure SOAP endpoint (required by the client's legacy finance system).

**Detailed Requirements:**
- **Tiered Pricing:** Support for "Base Fee" + "Per GB" overage charges.
- **Invoice Generation:** Automatic PDF generation on the 1st of every month.
- **Subscription Tiers:** Ability to toggle features (e.g., the Workflow Engine) on or off based on the subscription level.
- **Alerting:** Notify the account owner when 80% of the monthly data quota has been consumed.

**Acceptance Criteria:**
- System correctly calculates a bill based on 1.5TB of data ingestion at $0.50/GB + $100k base fee.
- Invoice is generated and stored in the system for download.

---

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low (Nice to Have) | **Status:** In Progress | **Version:** 0.3.0

**Description:**
This feature allows users to create "If-This-Then-That" (IFTTT) style rules. For example, "If sensor temperature > 500°C for 5 minutes, then send an alert to the maintenance lead."

**Technical Implementation:**
The engine uses a Directed Acyclic Graph (DAG) to represent the workflow. A visual builder (React-Flow) allows users to link nodes. The backend translates these graphs into Drools (Java Rule Engine) scripts.

**Detailed Requirements:**
- **Triggers:** Support for threshold breaches, time-based events, and manual triggers.
- **Actions:** Support for Email, Slack, System Alert, and triggering a secondary data pipeline.
- **Logic Gates:** Implementation of AND, OR, and NOT operators.
- **Validation:** The system must prevent circular dependencies in the workflow graph.

**Acceptance Criteria:**
- A user can visually build a 3-step workflow and trigger it via a simulated data spike.

---

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to Have) | **Status:** Complete | **Version:** 1.0.0

**Description:**
Aerospace data comes in various formats (CSV, JSON, XML, and proprietary binary formats like ARINC 429). This feature allows users to upload files, and the system automatically detects the format and maps it to the internal schema.

**Technical Implementation:**
The `ImportService` uses a "Magic Byte" detection system to identify file types. For CSV/JSON, it employs a sampling algorithm to guess the column types (Integer, Float, String, Date).

**Detailed Requirements:**
- **Auto-Detection:** Support for .csv, .json, .xml, and .parquet.
- **Mapping Interface:** A UI where users can manually correct the auto-detected mapping if it is incorrect.
- **Bulk Export:** Export of filtered datasets back to CSV or Parquet for external analysis in R or Python.
- **Validation:** Check for data integrity (e.g., nulls in required fields) before committing to Oracle DB.

**Acceptance Criteria:**
- Uploading a 1GB CSV file results in successful detection and ingestion into the database within 10 minutes.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer <JWT>` token in the header.

### 4.1 Authentication & User Management
**Endpoint:** `POST /auth/login`
- **Description:** Authenticates user via LDAP.
- **Request:** `{"username": "z_nakamura", "password": "password123"}`
- **Response:** `200 OK` $\rightarrow$ `{"token": "eyJhbG... ", "expiresIn": 3600}`

**Endpoint:** `GET /users/profile`
- **Description:** Retrieves the current user's settings and role.
- **Request:** No body.
- **Response:** `200 OK` $\rightarrow$ `{"userId": "U102", "role": "ADMIN", "name": "Zola Nakamura"}`

### 4.2 Collaboration Service
**Endpoint:** `POST /collab/session/join`
- **Description:** Joins a real-time editing session for a specific report.
- **Request:** `{"reportId": "REP-99", "userId": "U102"}`
- **Response:** `200 OK` $\rightarrow$ `{"sessionId": "SESS-445", "socketUrl": "wss://beacon.local/ws"}`

**Endpoint:** `PATCH /collab/update`
- **Description:** Sends a delta update for a document.
- **Request:** `{"sessionId": "SESS-445", "delta": {"field": "temp_threshold", "value": 450}}`
- **Response:** `204 No Content`

### 4.3 Analytics & Dashboards
**Endpoint:** `GET /analytics/metrics/{metricId}`
- **Description:** Fetches time-series data for a specific sensor.
- **Request:** `?start=2024-01-01&end=2024-01-02`
- **Response:** `200 OK` $\rightarrow$ `{"metricId": "M1", "data": [{"t": 171000, "v": 45.2}, ... ]}`

**Endpoint:** `POST /dashboards/save`
- **Description:** Saves the current dashboard layout.
- **Request:** `{"userId": "U102", "layout": "JSON_BLOB"}`
- **Response:** `201 Created` $\rightarrow$ `{"dashboardId": "DB-12"}`

### 4.4 Billing & System
**Endpoint:** `GET /billing/usage`
- **Description:** Returns total data ingested for the current billing cycle.
- **Request:** No body.
- **Response:** `200 OK` $\rightarrow$ `{"currentMonthUsageGB": 1240.5, "quotaGB": 2000}`

**Endpoint:** `GET /system/health`
- **Description:** Checks the status of all microservices and Kafka brokers.
- **Request:** No body.
- **Response:** `200 OK` $\rightarrow$ `{"status": "UP", "services": {"ingestion": "UP", "billing": "DOWN"}}`

---

## 5. DATABASE SCHEMA

The database is hosted on **Oracle 19c**. All tables utilize `VARCHAR2` for strings and `NUMBER` for numeric values to ensure compatibility.

### 5.1 Table Definitions

1.  **`users`**: Primary user registry.
    - `user_id` (PK, UUID)
    - `username` (Unique, VARCHAR2(50))
    - `email` (VARCHAR2(100))
    - `role_id` (FK $\rightarrow$ `roles.role_id`)
    - `created_at` (Timestamp)

2.  **`roles`**: RBAC definitions.
    - `role_id` (PK, Int)
    - `role_name` (VARCHAR2(20)) (e.g., ADMIN, ANALYST, VIEWER)
    - `permissions` (CLOB)

3.  **`data_streams`**: Metadata for ingested sensor streams.
    - `stream_id` (PK, UUID)
    - `sensor_name` (VARCHAR2(100))
    - `unit_of_measure` (VARCHAR2(10))
    - `sampling_rate` (Number)
    - `created_at` (Timestamp)

4.  **`telemetry_data`**: High-volume time-series data (Partitioned by Month).
    - `data_id` (PK, Number)
    - `stream_id` (FK $\rightarrow$ `data_streams.stream_id`)
    - `val` (Number)
    - `ts` (Timestamp)

5.  **`dashboard_configs`**: Stores the layout JSON.
    - `config_id` (PK, UUID)
    - `user_id` (FK $\rightarrow$ `users.user_id`)
    - `layout_json` (CLOB)
    - `last_modified` (Timestamp)

6.  **`collab_sessions`**: Active real-time sessions.
    - `session_id` (PK, UUID)
    - `report_id` (VARCHAR2(50))
    - `start_time` (Timestamp)
    - `end_time` (Timestamp)

7.  **`collab_deltas`**: Log of every change for versioning.
    - `delta_id` (PK, Number)
    - `session_id` (FK $\rightarrow$ `collab_sessions.session_id`)
    - `user_id` (FK $\rightarrow$ `users.user_id`)
    - `change_data` (CLOB)
    - `timestamp` (Timestamp)

8.  **`subscriptions`**: Client plan details.
    - `sub_id` (PK, UUID)
    - `client_id` (VARCHAR2(50))
    - `plan_type` (VARCHAR2(20))
    - `monthly_quota_gb` (Number)
    - `status` (VARCHAR2(10)) (ACTIVE, SUSPENDED)

9.  **`billing_invoices`**: Generated monthly bills.
    - `invoice_id` (PK, UUID)
    - `sub_id` (FK $\rightarrow$ `subscriptions.sub_id`)
    - `amount` (Number(12,2))
    - `issue_date` (Date)
    - `payment_status` (VARCHAR2(10))

10. **`workflow_rules`**: Automation logic.
    - `rule_id` (PK, UUID)
    - `rule_name` (VARCHAR2(100))
    - `logic_graph` (CLOB)
    - `is_active` (Number(1))
    - `created_by` (FK $\rightarrow$ `users.user_id`)

### 5.2 Relationships
- `users` $\rightarrow$ `roles` (Many-to-One)
- `users` $\rightarrow$ `dashboard_configs` (One-to-Many)
- `data_streams` $\rightarrow$ `telemetry_data` (One-to-Many)
- `subscriptions` $\rightarrow$ `billing_invoices` (One-to-Many)
- `collab_sessions` $\rightarrow$ `collab_deltas` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Beacon uses three distinct environments, all hosted on-premise in the client's data center.

| Environment | Purpose | Specs | Database | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | Feature dev / Unit testing | 2x VM (16GB RAM, 8 vCPU) | Oracle XE | GitHub Actions $\rightarrow$ SSH |
| **Staging** | QA / Integration / UAT | 4x VM (32GB RAM, 16 vCPU) | Oracle 19c (Lite) | Blue-Green via GH Actions |
| **Production** | Live Enterprise Use | 12x VM (128GB RAM, 32 vCPU) | Oracle 19c (RAC) | Blue-Green via GH Actions |

### 6.2 CI/CD Pipeline
We use **GitHub Actions** (Self-hosted runners located within the on-premise network to avoid firewall breaches).
1.  **Commit:** Developer pushes code to `feature/` branch.
2.  **Build:** Maven compiles Java code and runs JUnit tests.
3.  **Scan:** SonarQube scans for security vulnerabilities and code smells.
4.  **Artifact:** A Docker image is built and pushed to the local Harbor Registry.
5.  **Deploy:** 
    - **Staging:** Automatic deploy on merge to `develop`.
    - **Production:** Manual trigger on merge to `main`. We use **Blue-Green deployment**: the new version (Green) is spun up alongside the old (Blue). Traffic is switched via the Nginx Load Balancer only after health checks pass.

### 6.3 On-Premise Infrastructure
- **Network:** All traffic is routed through a Cisco ASA firewall. No outbound internet access is permitted for the production environment.
- **Storage:** SAN storage using PureStorage for high-IOPS requirements of the Oracle DB and Kafka logs.
- **Backup:** Daily snapshots taken via Veeam and stored on a separate immutable backup server.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Coverage Goal:** 80% line coverage.
- **Scope:** Every single business logic method in the `Service` layer must have a corresponding unit test.

### 7.2 Integration Testing
- **Framework:** Spring Boot Test with **Testcontainers**.
- **Approach:** We spin up a temporary Oracle container and a Kafka container to test the interaction between the `IngestionService` and the `AnalyticsService`.
- **Focus:** Ensuring that Kafka offsets are correctly managed and that database transactions are committed/rolled back correctly.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Approach:** Automated browser scripts that simulate a user journey: Login $\rightarrow$ Create Dashboard $\rightarrow$ Add Widget $\rightarrow$ Verify Data Display.
- **Execution:** Run nightly on the Staging environment.

### 7.4 Performance Benchmarking
- **Tool:** JMeter.
- **Target:** The system must handle 50,000 events per second per Kafka partition with a p99 latency of $< 500ms$ for the dashboard update.
- **Stress Test:** Simulate 100 concurrent users performing heavy data exports.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Scope creep from stakeholders adding 'small' features. | High | Medium | Maintain a strict Product Backlog; any new feature requires a signed "Change Request" and an adjustment to the timeline. Build a fallback architecture to allow for modular additions. | Zola Nakamura |
| **R-02** | Integration partner's API is undocumented and buggy. | High | High | Assign a dedicated engineer to "reverse engineer" the API. Maintain a separate "Integration Wrapper" service to sanitize partner data. | Petra Liu |
| **R-03** | SOC 2 Type II audit failure. | Low | Critical | Conduct monthly internal pre-audits. Use automated compliance tracking tools. | Greta Kim |
| **R-04** | Hardware failure in on-premise DC. | Medium | High | Implement Oracle RAC for DB high availability and Kafka replication factor of 3 across different physical hosts. | Petra Liu |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or total loss of revenue.
- **High:** Significant delay to milestones or budget overrun.
- **Medium:** Noticeable impact on quality or timeline, but manageable.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation & Core Infrastructure (Completed)
- **Dates:** 2024-06-01 $\rightarrow$ 2024-10-30
- **Activities:** Setup of on-premise servers, Kafka cluster installation, Basic Auth module, Data Import/Export feature.
- **Dependencies:** Hardware procurement from client.

### 9.2 Phase 2: Feature Completion & MVP (Current)
- **Dates:** 2024-11-01 $\rightarrow$ 2025-03-15
- **Activities:** Finalizing Collaborative Editing, completing the Dashboard Widgets, and designing the Billing system.
- **Milestone 1 (2025-03-15):** MVP Feature Complete.
- **Dependencies:** Resolution of third-party API rate limits.

### 9.3 Phase 3: Hardening & Optimization
- **Dates:** 2025-03-16 $\rightarrow$ 2025-05-15
- **Activities:** Performance tuning of Oracle queries, Kafka partition optimization, SOC 2 security hardening.
- **Milestone 2 (2025-05-15):** Performance benchmarks met.

### 9.4 Phase 4: Pilot & Beta Launch
- **Dates:** 2025-05-16 $\rightarrow$ 2025-07-15
- **Activities:** Onboarding 10 pilot users, collecting feedback, fixing critical bugs.
- **Milestone 3 (2025-07-15):** External beta launch.

---

## 10. MEETING NOTES (Excerpts from "The Master Log")

*Note: The following is a condensed version of the 200-page unsearchable shared document.*

### Meeting 1: Architecture Review (2024-07-12)
**Attendees:** Zola, Petra, Greta, Joelle.
**Discussion:**
- Petra raised concerns about the Oracle DB licensing costs if we scale the number of cores too high.
- Zola insisted on the on-premise requirement, noting that the client will not even consider a hybrid cloud approach due to ITAR regulations.
- Joelle asked if we could use MongoDB for the dashboard configs. Petra vetoed this, stating that adding another database technology would increase the operational burden on the client's DBAs.
**Decision:** Stick to Oracle 19c for all persistence. Use CLOBs for JSON storage.

### Meeting 2: The "API Nightmare" Sync (2024-09-05)
**Attendees:** Zola, Petra, Greta.
**Discussion:**
- Petra reported that the third-party API for sensor data is returning 429 (Too Many Requests) even when we are within the agreed quota.
- Greta noted that the undocumented fields in the API are causing `NullPointerExceptions` in the ingestion service.
- Zola expressed frustration that the partner has not provided updated documentation.
**Decision:** Petra to implement a "Retry with Exponential Backoff" strategy and a "Circuit Breaker" pattern to prevent the ingestion service from crashing. Petra is now the designated owner for all partner API issues.

### Meeting 3: SOC 2 Readiness Check (2024-11-20)
**Attendees:** Zola, Greta, Joelle.
**Discussion:**
- Greta pointed out that the current logging doesn't track "Who accessed which record," which is a SOC 2 requirement.
- Joelle suggested using a Spring AOP (Aspect-Oriented Programming) interceptor to log all requests to the `TelemetryData` repository.
- Zola reminded the team that the audit must be completed before the March MVP launch.
**Decision:** Implement the `AuditInterceptor` by the end of the next sprint.

---

## 11. BUDGET BREAKDOWN

The project is bootstrapping with existing team capacity, meaning "Personnel" refers to the allocation of salaries already budgeted under Clearpoint Digital's general OpEx, now tagged to Project Beacon.

| Category | Year 1 Allocated Cost | Notes |
| :--- | :--- | :--- |
| **Personnel (Engineering)** | $520,000 | 15 distributed staff across 5 countries. |
| **Personnel (Product/QA)** | $130,000 | VP Product and QA Lead overhead. |
| **Infrastructure (Hardware)** | $45,000 | Server rack maintenance and power (Client subsidized). |
| **Software Licenses** | $60,000 | Oracle 19c Enterprise licenses & Harbor Pro. |
| **Tooling & Security** | $15,000 | SonarQube and SOC 2 auditing software. |
| **Contingency Fund** | $50,000 | Reserved for emergency hardware replacement. |
| **TOTAL** | **$820,000** | |

**Financial Note:** Against the $2,000,000 annual contract, the project maintains a healthy gross margin of approximately 59%.

---

## 12. APPENDICES

### Appendix A: Data Ingestion Logic (Pseudo-code)
The `AutoDetectionService` uses the following logic to identify incoming streams:

```java
public StreamType detectFormat(File uploadedFile) {
    byte[] header = readFirst1024Bytes(uploadedFile);
    if (isMagicBytes(header, 0xEF, 0xBB, 0xBF)) return StreamType.UTF8_CSV;
    if (isMagicBytes(header, 0x7B)) return StreamType.JSON; // Starts with {
    if (isMagicBytes(header, 0x3C)) return StreamType.XML;   // Starts with <
    if (isMagicBytes(header, 0x41, 0x52, 0x49, 0x4E)) return StreamType.ARINC_429;
    return StreamType.UNKNOWN;
}
```

### Appendix B: Conflict Resolution Matrix
For the Collaborative Editing feature, the following resolution rules apply:

| Conflict Type | Resolution Strategy | Logic |
| :--- | :--- | :--- |
| **Text Field** | Sequence-based OT | Each character is assigned a unique ID and position. |
| **Numeric Value** | Last-Writer-Wins (LWW) | The update with the latest server-side timestamp is kept. |
| **Checkbox/Toggle** | Boolean OR | If any user toggles a "Warning" to ON, it remains ON until explicitly turned OFF. |
| **Widget Position** | Coordinate Average | If two users move a widget to different spots, it snaps to the midpoint (temporary) until one user confirms. |