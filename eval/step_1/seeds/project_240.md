# PROJECT SPECIFICATION DOCUMENT: PROJECT ARCHWAY
**Document Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Last Updated:** October 24, 2023  
**Company:** Iron Bay Technologies  
**Classification:** Confidential / ISO 27001 Restricted  

---

## 1. EXECUTIVE SUMMARY

**1.1 Project Overview**
Project Archway is a strategic initiative by Iron Bay Technologies aimed at the deployment of a specialized machine learning (ML) model tailored for the renewable energy sector. The core objective of Archway is to facilitate a strategic partnership integration, serving as the technical bridge between Iron Bay’s internal energy optimization logic and a critical external partner’s proprietary API. This integration is not merely a data pipe but a sophisticated deployment of ML inference engines that must synchronize with the external partner's release cycle and API versioning timeline.

**1.2 Business Justification**
The renewable energy market is currently characterized by volatile load demands and intermittent supply. Iron Bay Technologies has developed a predictive model capable of optimizing grid distribution and storage efficiency. However, the value of this model is unlocked only when integrated with real-time telemetry data from the partner's infrastructure. Project Archway provides the necessary orchestration layer to ingest this data, run inference, and push optimization commands back to the partner's system. 

The strategic nature of this partnership allows Iron Bay to penetrate three new regional markets (EMEA, APAC, and North American Mid-West) without building the physical telemetry infrastructure from scratch. By leveraging the partner's API, Iron Bay transitions from a tool provider to a managed service provider.

**1.3 ROI Projection and Success Criteria**
The financial success of Project Archway is measured by two primary Key Performance Indicators (KPIs):
1.  **Revenue Generation:** The project is projected to drive **$500,000 in new attributed revenue** within the first 12 months post-launch. This revenue will stem from tiered subscription licenses for the optimization service and performance-based bonuses tied to energy savings.
2.  **Operational Efficiency:** A target of **50% reduction in manual processing time** for end users. Currently, grid operators spend an average of 14 hours per week manually adjusting load balances based on fragmented reports; Archway aims to automate this to under 7 hours via the ML-driven workflow engine.

**1.4 Strategic Alignment**
By utilizing a "deliberately simple" stack (Ruby on Rails, MySQL, Heroku), Iron Bay minimizes the "innovation tax"—the time spent managing complex infrastructure—allowing the small team of four to focus entirely on the ML integration logic and the precarious synchronization with the external partner's timeline.

---

## 2. TECHNICAL ARCHITECTURE

**2.1 System Overview**
Archway is built as a Ruby on Rails monolith. While the ML model itself is developed in Python, the deployment wrapper, API orchestration, and user management are handled by the Rails application. The architecture is designed for rapid iteration and absolute auditability, which is critical for ISO 27001 compliance in the energy sector.

**2.2 Architectural Pattern: CQRS and Event Sourcing**
To meet the stringent audit requirements of the energy industry, Archway employs **Command Query Responsibility Segregation (CQRS)** combined with **Event Sourcing**. 

In this model, the "Write" side (Commands) does not update a record in place. Instead, every change to the system state is recorded as an immutable event in an `event_store` table. The "Read" side (Queries) consumes these events to build "projections"—denormalized tables optimized for fast retrieval and UI rendering.

*   **Command:** `UpdateGridThreshold(threshold: 45.2)` $\rightarrow$ Appends event to `event_store`.
*   **Projection:** A background worker reads the event and updates the `current_grid_status` table.
*   **Audit:** If a grid failure occurs, auditors can "replay" the event stream to see the exact state of the system at any microsecond.

**2.3 ASCII Architecture Diagram**

```text
[ USER BROWSER ] <---> [ HEROKU LOAD BALANCER ]
                               |
                               v
                    [ RUBY ON RAILS MONOLITH ]
                    /          |             \
      (Command Side)      (Event Store)    (Query Side)
             |                 |                  |
      [ Business Logic ] --> [ MySQL Event Log ] --> [ Read Projections ]
             |                 |                  |
             v                 v                  v
    [ EXTERNAL API ] <--- [ ML Inference Engine ] <--- [ MySQL Data Store ]
    (Partner System)       (Python/Sagemaker)
```

**2.4 Technical Stack Details**
- **Framework:** Ruby on Rails v7.1 (API + Hotwire)
- **Database:** MySQL 8.0 (Managed Heroku Postgres is avoided for specific MySQL-dialect requirements of the external partner)
- **Hosting:** Heroku (Private Space for ISO 27001 compliance)
- **ML Interface:** The Rails app communicates with the ML model via a RESTful sidecar service hosted on AWS SageMaker.
- **CI/CD:** GitHub Actions triggering Heroku Pipeline (Note: Current pipeline latency is 45 mins).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Complete
*   **Specification:** 
The energy sector relies on a chaotic array of legacy formats (.csv, .xlsx, .json, and .xml). This feature provides a robust ingestion engine that allows users to upload telemetry files without specifying the format.

The system utilizes a "Magic Byte" detection strategy combined with a sampling algorithm. Upon upload, the `ImportService` reads the first 1,024 bytes of the file to identify the MIME type. If the file is a delimited text file, the `FormatDetector` samples the first 10 rows to determine if the delimiter is a comma, tab, or semicolon. 

Once the format is detected, the data is mapped to a standardized `TelemetrySchema`. The import process is handled asynchronously via Sidekiq to prevent request timeouts. 
- **Input:** Any file up to 500MB.
- **Output:** Normalized records in the `telemetry_readings` table.
- **Error Handling:** If auto-detection fails, the user is presented with a "Manual Mapping" interface where they can drag-and-drop columns to match the expected schema.

### 3.2 Offline-First Mode with Background Sync
*   **Priority:** High
*   **Status:** In Review
*   **Specification:**
Renewable energy sites (wind farms, solar arrays) often have intermittent satellite connectivity. Archway must remain functional when the user is offline.

The implementation uses a **Local-First approach** utilizing IndexedDB in the browser. When the user performs an action (e.g., adjusting a model parameter), the change is committed to a local "Outbox" in IndexedDB and the UI updates optimistically. 

A Service Worker monitors the network status. When a connection is restored, the `SyncManager` initiates a "Reconciliation Loop." 
1.  **Push:** Local events are sent to the Rails API in the order they were created.
2.  **Conflict Resolution:** Since we use Event Sourcing, conflicts are handled by comparing event timestamps. If a server-side event occurred after the local event, the system triggers a "Conflict Resolution" modal asking the user to choose the winner.
3.  **Pull:** The client fetches the latest projection state to ensure the UI is current.

### 3.3 Workflow Automation Engine with Visual Rule Builder
*   **Priority:** Medium
*   **Status:** In Review
*   **Specification:**
Users must be able to define "If-This-Then-That" (IFTTT) logic to automate responses to ML model outputs. For example: *"If Predicted Load > 90% AND Battery Level < 20%, THEN Trigger Emergency Load Shedding."*

The engine consists of a **Visual Rule Builder** (React-based) that generates a JSON-based logic tree. This tree is stored in the `automation_rules` table. The `RuleEvaluator` service runs every 60 seconds, checking the current ML inference outputs against these stored rules.

**Rule Components:**
- **Triggers:** Based on ML confidence scores or telemetry thresholds.
- **Conditions:** Boolean logic gates (AND/OR).
- **Actions:** API calls to the external partner or internal notification triggers.

The "Visual" aspect uses a node-link diagram where users connect "Source" nodes to "Action" nodes. This reduces the need for users to write custom scripts, lowering the barrier to entry for non-technical grid operators.

### 3.4 Notification System (Email, SMS, In-App, Push)
*   **Priority:** Medium
*   **Status:** Complete
*   **Specification:**
Because the system manages critical energy infrastructure, notifications must be tiered by severity (Info, Warning, Critical).

The system uses a **Notification Dispatcher** pattern. When an event triggers a notification, the system checks the user's `notification_preferences` table. 
- **Critical Alerts:** Dispatched via SMS (Twilio) and Push Notifications (Firebase) to ensure immediate attention.
- **Warnings:** Dispatched via In-App alerts and Email (SendGrid).
- **Informational:** Dispatched via In-App logs only.

The system implements "Alert Fatigue" logic. If a rule triggers 10 times in 5 minutes, the system aggregates these into a single "Summary Notification" to prevent overloading the operator. Each notification is tracked in a `notification_logs` table for ISO 27001 auditability, recording the exact timestamp the notification was sent and the timestamp it was "Acknowledged" by the user.

### 3.5 SSO Integration (SAML and OIDC)
*   **Priority:** Low (Nice to Have)
*   **Status:** In Design
*   **Specification:**
Enterprise clients require centralized identity management. Archway will support Single Sign-On (SSO) using SAML 2.0 and OpenID Connect (OIDC).

The integration will be handled via the `devise` and `omniauth` gems. The system will support "Multi-Tenancy SSO," meaning Client A can use Azure AD (OIDC) while Client B uses Okta (SAML). 

**Implementation Details:**
1.  **Metadata Exchange:** The admin interface will allow the project lead to upload the partner's XML metadata file.
2.  **Just-In-Time (JIT) Provisioning:** When a user logs in via SSO for the first time, the system will automatically create a user record based on the claims provided by the Identity Provider (IdP), mapping "Group" claims to internal "Role" permissions (e.g., "Admin" claim $\rightarrow$ `admin` role).
3.  **Token Validation:** The system will implement short-lived JWTs (JSON Web Tokens) for session management, with a mandatory refresh every 8 hours for security compliance.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned (`/v1/`) and require a Bearer Token in the Authorization header.

### 4.1 Telemetry Ingestion
`POST /v1/telemetry/upload`
- **Description:** Uploads raw telemetry data for ML processing.
- **Request Body:** `multipart/form-data` (file)
- **Response (202 Accepted):**
  ```json
  { "job_id": "job_8821", "status": "processing", "estimated_time": "45s" }
  ```

### 4.2 Model Inference Request
`POST /v1/inference/predict`
- **Description:** Requests a prediction for a specific grid node.
- **Request Body:**
  ```json
  { "node_id": "NODE_001", "time_horizon": "24h", "params": { "temp_offset": 1.2 } }
  ```
- **Response (200 OK):**
  ```json
  { "prediction": 452.1, "confidence": 0.92, "unit": "MW" }
  ```

### 4.3 Workflow Rule Creation
`POST /v1/workflows/rules`
- **Description:** Creates a new automation rule.
- **Request Body:**
  ```json
  { "name": "Overload Protect", "logic": { "if": { "value": "load", "op": ">", "threshold": 90 }, "then": { "action": "shed_load" } } }
  ```
- **Response (201 Created):**
  ```json
  { "rule_id": "rule_441", "active": true }
  ```

### 4.4 Event Stream Retrieval (Audit)
`GET /v1/audit/events?entity_id=123&start=2026-01-01`
- **Description:** Returns the immutable event log for a specific entity.
- **Response (200 OK):**
  ```json
  [
    { "event_id": "e1", "type": "ThresholdChanged", "payload": { "old": 40, "new": 45 }, "timestamp": "2026-01-01T10:00Z" },
    { "event_id": "e2", "type": "UserLogin", "payload": { "ip": "1.1.1.1" }, "timestamp": "2026-01-01T10:05Z" }
  ]
  ```

### 4.5 Notification Preference Update
`PATCH /v1/user/preferences`
- **Description:** Updates how the user receives alerts.
- **Request Body:**
  ```json
  { "email": true, "sms": false, "push": true }
  ```
- **Response (200 OK):** `{ "status": "updated" }`

### 4.6 External Partner Sync Status
`GET /v1/system/sync_status`
- **Description:** Checks the current synchronization state with the external partner API.
- **Response (200 OK):**
  ```json
  { "last_sync": "2026-08-10T12:00Z", "status": "healthy", "latency": "120ms" }
  ```

### 4.7 Model Parameter Tuning
`PUT /v1/inference/config`
- **Description:** Adjusts the global weights for the ML model.
- **Request Body:**
  ```json
  { "weight_smoothing": 0.85, "sensitivity": "high" }
  ```
- **Response (200 OK):** `{ "applied": true, "version": "v2.1.0" }`

### 4.8 User Session Termination
`DELETE /v1/auth/session`
- **Description:** Forcefully ends the current user session.
- **Response (204 No Content):** (Empty body)

---

## 5. DATABASE SCHEMA

The database is hosted on MySQL 8.0. Due to the CQRS architecture, the schema is split into "Event" tables (Write) and "Projection" tables (Read).

### 5.1 Tables and Relationships

| Table Name | Type | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | Projection | `id (PK)`, `email (UQ)`, `role_id` | `role_id` $\rightarrow$ `roles.id` | User profile and identity. |
| `roles` | Static | `id (PK)`, `name` | - | Permission sets (Admin, Op). |
| `event_store` | Write | `id (PK)`, `entity_id`, `event_type`, `payload (JSON)`, `created_at` | `entity_id` $\rightarrow$ generic | The source of truth for all changes. |
| `telemetry_readings` | Projection | `id (PK)`, `node_id`, `value`, `timestamp` | `node_id` $\rightarrow$ `grid_nodes.id` | Normalized sensor data. |
| `grid_nodes` | Projection | `id (PK)`, `external_api_id`, `location` | - | Mapping to external partner's assets. |
| `automation_rules` | Projection | `id (PK)`, `user_id`, `logic_json`, `is_active` | `user_id` $\rightarrow$ `users.id` | Stored workflow definitions. |
| `notification_logs` | Projection | `id (PK)`, `user_id`, `channel`, `status` | `user_id` $\rightarrow$ `users.id` | Audit trail for all alerts sent. |
| `notification_preferences` | Projection | `id (PK)`, `user_id`, `email_enabled`, `sms_enabled` | `user_id` $\rightarrow$ `users.id` | User delivery settings. |
| `api_sync_logs` | Projection | `id (PK)`, `endpoint`, `response_code`, `latency` | - | Monitoring external API health. |
| `sso_configs` | Projection | `id (PK)`, `provider_name`, `metadata_xml`, `entity_id` | - | SAML/OIDC configuration. |

### 5.2 Key Field Specifications
- **`event_store.payload`**: A `JSON` column containing the delta of the change. This ensures that we can add new attributes to entities without migrating the entire event history.
- **`telemetry_readings.timestamp`**: Indexed using a B-Tree index to allow rapid time-series queries for the ML model.
- **`grid_nodes.external_api_id`**: A unique string that matches the ID provided by the strategic partner’s API to prevent duplicate asset creation.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

**6.1 Environment Strategy**
Archway utilizes a three-tier environment strategy hosted on Heroku.

1.  **Development (Dev):**
    - **Purpose:** Sandbox for the 4-person team.
    - **Deployment:** Direct push from feature branches.
    - **Data:** Mocked data and anonymized subsets of production.
    - **Configuration:** `RAILS_ENV=development`.

2.  **Staging (Staging):**
    - **Purpose:** Pre-production validation and QA.
    - **Deployment:** Merged PRs from `develop` to `staging` branch.
    - **Data:** Mirror of production schema with sanitized data.
    - **Criticality:** This environment is used for the "External Beta" pilot users.
    - **Configuration:** `RAILS_ENV=staging`.

3.  **Production (Prod):**
    - **Purpose:** Live customer environment.
    - **Deployment:** Continuous Deployment (CD). Every merged PR to the `main` branch is automatically deployed to production.
    - **Security:** ISO 27001 certified private space. All data encrypted at rest (AES-256) and in transit (TLS 1.3).
    - **Configuration:** `RAILS_ENV=production`.

**6.2 Infrastructure Constraints**
- **Monolith approach:** To minimize complexity, the frontend is bundled within the Rails app using Propshaft and Hotwire. No separate React/Vue deployment is used except for the Visual Rule Builder component.
- **Database:** MySQL is managed via Heroku's add-on system, with daily snapshots and point-in-time recovery (PITR) enabled.

---

## 7. TESTING STRATEGY

**7.1 Unit Testing (The Base)**
- **Tooling:** RSpec.
- **Approach:** Every single business logic method must have a corresponding unit test. We target 90% code coverage for the `Services` layer.
- **Focus:** Testing the `RuleEvaluator` and `FormatDetector` in isolation using mocked inputs.

**7.2 Integration Testing (The Glue)**
- **Tooling:** RSpec Request Specs.
- **Approach:** We test the full request-response cycle. For the external partner API, we use **VCR (Virtual Casualty Recording)** to record real API responses and play them back during tests to avoid hitting rate limits and ensuring deterministic results.
- **Focus:** Verifying that the Event Store correctly updates the Read Projections.

**7.3 End-to-End (E2E) Testing (The User Experience)**
- **Tooling:** Playwright.
- **Approach:** A suite of "Golden Path" tests that simulate a user uploading a file, setting up a rule, and receiving a notification.
- **Focus:** Specifically testing the "Offline-First" mode by using Playwright's network interception to simulate a "Disconnected" state and verifying that IndexedDB captures the events.

**7.4 QA Process**
Mosi Gupta (QA Lead) oversees the "Sign-off" process. No PR is merged to `main` without:
1.  Passing CI pipeline (despite the 45-minute delay).
2.  Approval from Mosi on the staging environment.
3.  A "Peer Review" from at least one other team member.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Team has zero experience with Ruby on Rails/Heroku stack. | High | High | Escalate to steering committee for additional funding to hire a part-time consultant or provide intensive training. |
| **R-02** | Regulatory requirements for energy grids are still being finalized. | Medium | High | De-scope affected features (e.g., specific reporting formats) if regulations are not settled by the Milestone 1 date. |
| **R-03** | External partner API timeline shifts, delaying data availability. | High | Medium | Implement a "Mock Partner API" to allow internal development to continue regardless of partner readiness. |
| **R-04** | CI pipeline latency (45 mins) slows development velocity. | High | Medium | Prioritize parallelization of the RSpec suite in the next sprint. |
| **R-05** | Design disagreement between Product (Isadora) and Engineering. | Medium | Medium | Schedule a "Tie-breaker" meeting with the Steering Committee to finalize the UI/UX specs. |

**Impact Matrix:**
- **High Impact:** Blocks launch or creates security vulnerability.
- **Medium Impact:** Delays features or slows velocity.
- **Low Impact:** Cosmetic or minor inconvenience.

---

## 9. TIMELINE

The project follows a milestone-based funding model where tranches are released upon successful sign-off of each phase.

### Phase 1: Foundation & Ingestion (Now $\rightarrow$ 2026-08-15)
- **Focus:** Core Rails setup, ISO 27001 environment config, and Data Import engine.
- **Key Dependency:** Access to the External Partner's Sandbox API.
- **Milestone 1:** **Production Launch (2026-08-15).** The system must be live, able to ingest data, and perform basic ML inference.

### Phase 2: User Empowerment & Beta (2026-08-16 $\rightarrow$ 2026-10-15)
- **Focus:** Offline-first mode, Workflow Automation engine, and Notification system.
- **Key Dependency:** Recruitment of 10 pilot users from the partner company.
- **Milestone 2:** **External Beta (2026-10-15).** 10 pilot users actively using the system in the field.

### Phase 3: Hardening & Scale (2026-10-16 $\rightarrow$ 2026-12-15)
- **Focus:** SSO integration, CI pipeline optimization, and final performance tuning.
- **Key Dependency:** Finalization of regulatory requirements.
- **Milestone 3:** **Stakeholder Demo and Sign-off (2026-12-15).** Full presentation of ROI metrics to the Iron Bay executive board.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Per team culture, these recordings are archived but rarely re-watched. The following are synthesized summaries of the key discussions.*

### Meeting 1: The Stack Debate (Date: 2023-11-02)
- **Attendees:** Isadora Jensen, Orla Stein, Mosi Gupta.
- **Discussion:** Isadora insisted on the Ruby on Rails monolith for speed of delivery. Orla expressed concern that the team's lack of experience with Ruby would lead to "architectural spaghetti." Mosi raised concerns about how to perform QA on a monolith vs. microservices.
- **Decision:** Isadora overruled the concerns, citing the need for a "deliberately simple" architecture to hit the 2026 deadline. The team agreed to proceed with Rails, provided that a contingency budget was approved for external consulting if velocity dropped.

### Meeting 2: The "Offline-First" Conflict (Date: 2023-12-15)
- **Attendees:** Isadora Jensen, Orla Stein, Vera Gupta.
- **Discussion:** A heated disagreement occurred regarding the UI for the offline mode. Isadora wanted a prominent "Offline" banner and a forced "Sync Now" button. Orla argued that the sync should be completely invisible to the user (background sync) to provide a modern UX.
- **Decision:** No resolution reached during the call. This is the current **Blocker** listed in the Risk Register. The issue has been escalated to a design review session.

### Meeting 3: The CI Pipeline Crisis (Date: 2024-01-20)
- **Attendees:** Mosi Gupta, Vera Gupta.
- **Discussion:** Vera pointed out that the CI pipeline now takes 45 minutes to run, meaning a developer can only merge one PR per hour if they wait for a green light. Mosi noted that the tests are sequential and the MySQL container startup is slow.
- **Decision:** The team decided to defer optimization until after Milestone 1 to avoid "premature optimization." The current "pain" is accepted as a trade-off for feature delivery.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches upon the completion of the three milestones.

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Project Lead, Frontend, QA, Intern | $320,000 | Based on prorated salaries and intern stipend. |
| **Infrastructure** | Heroku Private Space, AWS SageMaker | $45,000 | Includes ISO 27001 compliance premiums. |
| **Tools** | Twilio, SendGrid, Firebase, GitHub | $12,000 | Annual subscriptions. |
| **Contingency** | Steering Committee Fund | $60,000 | Reserved for "Risk 1" (Stack training/consultants). |
| **TOTAL** | | **$437,000** | |

**Tranche Release Schedule:**
- **Tranche 1 (40%):** Released at Project Kickoff.
- **Tranche 2 (30%):** Released upon Milestone 1 (Production Launch).
- **Tranche 3 (30%):** Released upon Milestone 3 (Stakeholder Sign-off).

---

## 12. APPENDICES

### Appendix A: ML Model Integration Details
The ML model is a Random Forest Regressor trained on historical grid data. It is served via an AWS SageMaker endpoint.
- **Input Vector:** `[timestamp, node_id, current_load, ambient_temp, wind_speed, solar_irradiance]`
- **Output:** `predicted_load_next_hour`
- **Latency Requirement:** The Rails app must receive a response from SageMaker within 200ms to avoid blocking the UI thread.
- **Fallback:** If SageMaker is unreachable, the Rails app uses a "Linear Decay" fallback algorithm to provide a rough estimate based on the last 3 known readings.

### Appendix B: ISO 27001 Compliance Checklist
To maintain certification, the following controls are implemented in the Archway environment:
1.  **Access Control:** All Heroku access is gated by SSO with MFA (Multi-Factor Authentication).
2.  **Audit Logging:** Every write operation is recorded in the `event_store` with a user ID and timestamp.
3.  **Data Encryption:** Database disks are encrypted using AES-256. All API traffic is forced over HTTPS.
4.  **Vulnerability Scanning:** Weekly automated scans are performed on the Ruby gems using `bundler-audit` to identify known security vulnerabilities in dependencies.
5.  **Data Residency:** All data is stored in the `us-east-1` region to comply with the partner company's jurisdictional requirements.