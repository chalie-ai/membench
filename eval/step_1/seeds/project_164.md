Due to the extreme length requirements (6,000-8,000 words), this document is presented as a comprehensive, formal engineering specification. It is designed as the "Single Source of Truth" (SSOT) for the Lodestar development team.

***

# PROJECT SPECIFICATION: PROJECT LODESTAR
**Document Version:** 1.0.4  
**Last Updated:** 2024-05-22  
**Status:** Active/In-Development  
**Classification:** Confidential / ISO 27001 Compliant  
**Project Lead:** Wanda Jensen (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Lodestar is a mission-critical embedded systems firmware and orchestration layer redesign commissioned by Deepwell Data. The project seeks to replace a 15-year-old legacy system—the "Core-Legacy Engine"—which currently serves as the backbone for the company’s educational hardware deployments. The legacy system, while stable, is built on monolithic architecture with deprecated dependencies, creating a significant operational risk. Because the entire company depends on this system for real-time data processing in educational environments, Lodestar is being developed with a **zero-downtime tolerance** mandate.

### 1.2 Business Justification
The legacy system has reached its "end-of-life" (EOL) phase. Maintenance costs have increased by 40% year-over-year due to the scarcity of developers familiar with the archaic codebase. Furthermore, the inability to integrate with modern cloud-native APIs has hindered Deepwell Data’s ability to scale its educational offerings. Lodestar transitions the firmware orchestration from a brittle, single-point-of-failure model to a modular monolith that can incrementally shift toward microservices. This ensures that the company can continue to ship hardware while updating the software logic without interrupting the end-user experience.

### 1.3 ROI Projection
The financial justification for the $1.5M investment is based on three primary drivers:
1. **Reduction in OpEx:** By moving to AWS ECS and implementing automated CI/CD, the manual deployment hours are projected to drop from 120 man-hours per release to under 4 hours.
2. **Risk Mitigation:** The cost of a total system failure of the legacy engine is estimated at $500k per hour of downtime. Zero-downtime migration eliminates this catastrophic risk.
3. **Market Expansion:** The new feature set (specifically the Workflow Automation Engine and Collaborative Editing) is projected to increase the annual contract value (ACV) of educational licenses by 15% by 2027.

The projected break-even point for the $1.5M expenditure is 18 months post-deployment, with a projected 3-year ROI of 210%.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Lodestar utilizes a **Modular Monolith** approach. This allows the team to maintain a single deployment pipeline (minimizing complexity during the migration phase) while enforcing strict boundary separation between modules. As the system stabilizes and the legacy system is fully decommissioned, high-load modules (e.g., the Notification System) will be extracted into standalone microservices.

### 2.2 The Stack
- **Backend Framework:** Python 3.11 / Django 4.2 LTS (Chosen for rapid development and robust ORM).
- **Database:** PostgreSQL 15 (Primary relational store for structured educational data).
- **Caching/Message Broker:** Redis 7.0 (Used for real-time collaboration state and task queuing).
- **Deployment:** AWS Elastic Container Service (ECS) using Fargate for serverless scaling.
- **Infrastructure as Code:** Terraform and GitHub Actions for CI/CD.
- **Compliance:** All environments are hosted within an ISO 27001 certified AWS Landing Zone.

### 2.3 System Topology (ASCII Description)
The following represents the traffic flow from the embedded hardware to the cloud backend.

```text
[ Embedded Hardware ]  <--->  [ AWS ALB / Load Balancer ]
                                      |
                                      v
                        [ AWS ECS Cluster (Fargate) ]
                        |                              |
         +--------------+--------------+               |
         |  (Django App - Module A)     |               |
         |  - Workflow Engine           |               |
         |  - Collaboration Logic       |               |
         +--------------+--------------+               |
                        |                              |
         +--------------v--------------+               |
         |  (Django App - Module B)     |               |
         |  - Notification Dispatcher   |               |
         |  - Search/Indexing           |               |
         +--------------+--------------+               |
                        |                              |
        +---------------+--------------+---------------+
        |               |              |               |
 [ PostgreSQL ]    [ Redis Cache ]  [ S3 Bucket ]  [ Third-Party APIs ]
 (System State)    (Pub/Sub & Locks) (PDF/CSV Gen)  (SMS/Email Gateways)
```

### 2.4 Data Flow and Connectivity
Hardware devices connect via secure WebSockets for real-time updates and REST for configuration changes. All traffic is encrypted via TLS 1.3. The transition from legacy to Lodestar is managed via a "Strangler Fig" pattern, where specific API calls are intercepted by a proxy and routed to the new Lodestar service if the feature has been migrated, otherwise falling back to the legacy engine.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System
**Priority:** High | **Status:** In Progress

**Overview:**
The Notification System is the primary communication bridge between the embedded hardware, the administrative backend, and the end-users (students/teachers). It must handle multi-channel delivery (Email, SMS, In-App, Push) with guaranteed delivery for critical alerts.

**Detailed Functional Requirements:**
1. **Multi-Channel Dispatch:** The system must support a "Preference Matrix" where users can toggle which notifications they receive via which channel.
2. **Priority Queueing:** Notifications are categorized as `CRITICAL`, `WARNING`, or `INFO`. Critical alerts (e.g., hardware failure) must bypass standard queues and be dispatched via the "Fast Track" Redis stream to ensure sub-second delivery.
3. **Template Engine:** A dynamic template system using Jinja2, allowing administrators to create branded emails and SMS messages with placeholders (e.g., `{{user_name}}, your device {{device_id}} requires attention`).
4. **Retry Logic:** Exponential backoff for failed API calls to third-party providers (Twilio for SMS, SendGrid for Email).

**Technical Implementation:**
The system utilizes a Celery task queue backed by Redis. When a trigger occurs in the firmware, an event is published to the `notifications` topic. The `NotificationDispatcher` service consumes this event, checks the `UserNotificationPreference` table in PostgreSQL, and routes the message to the appropriate adapter.

**Constraints:**
- Must comply with GDPR and CCPA regarding user opt-outs.
- Must handle a burst of 10,000 notifications per minute during school "start-of-day" windows.

---

### 3.2 Advanced Search with Faceted Filtering
**Priority:** Low (Nice-to-have) | **Status:** In Progress

**Overview:**
This feature allows administrators to query vast amounts of hardware telemetry and student performance data using complex filters and full-text search.

**Detailed Functional Requirements:**
1. **Full-Text Indexing:** Integration of PostgreSQL `tsvector` and `tsquery` to allow searching across device logs, user notes, and configuration files.
2. **Faceted Filtering:** A sidebar UI allowing users to drill down by `Region`, `Device Model`, `Firmware Version`, and `Date Range`.
3. **Autocomplete/Suggestions:** A "Search-as-you-type" experience utilizing a Redis-backed prefix search to reduce database load.
4. **Saveable Queries:** Users can save complex filter combinations as "Views" for daily monitoring.

**Technical Implementation:**
To prevent search queries from locking the primary production tables, Lodestar implements a "Read Replica" strategy. All search queries are routed to a PostgreSQL read-only instance. For high-performance facets, the system pre-calculates counts using a materialized view that refreshes every 30 minutes.

**Constraints:**
- Search latency must not exceed 500ms for queries returning <1000 results.
- Indexing of new data must happen asynchronously to avoid blocking the main write thread.

---

### 3.3 Workflow Automation Engine (Visual Rule Builder)
**Priority:** High | **Status:** Complete

**Overview:**
The Workflow Engine allows non-technical educators to create "If-This-Then-That" (IFTTT) logic for their hardware. For example: "If temperature > 40°C AND user is in Room 101, THEN send SMS to Technician."

**Detailed Functional Requirements:**
1. **Visual Rule Builder:** A drag-and-drop interface (developed by Saoirse Oduya) that generates a JSON representation of a logical tree.
2. **Trigger System:** Supports hardware-based triggers (sensor thresholds), time-based triggers (cron), and event-based triggers (user login).
3. **Action Library:** A set of predefined actions: `SendNotification`, `UpdateDeviceConfig`, `LogEvent`, and `TriggerExternalWebhook`.
4. **Conflict Resolution:** A logic validator that detects circular dependencies (e.g., Rule A triggers Rule B, which triggers Rule A).

**Technical Implementation:**
The engine utilizes a Recursive Descent Parser to evaluate the JSON logic trees. Each rule is stored in the `workflow_rules` table. When a trigger event arrives, the `WorkflowEvaluator` service fetches all active rules associated with that event ID and executes the action chain in a transactional block.

**Constraints:**
- Maximum rule depth of 10 levels to prevent stack overflow during evaluation.
- Evaluation must complete within 50ms to avoid delaying firmware responses.

---

### 3.4 PDF/CSV Report Generation
**Priority:** Low (Nice-to-have) | **Status:** Blocked

**Overview:**
The reporting module generates compliance and performance reports for educational boards. This is currently blocked due to dependencies on the undocumented third-party API used for historical data aggregation.

**Detailed Functional Requirements:**
1. **Scheduled Delivery:** Ability to schedule reports (Weekly, Monthly, Quarterly) via a cron-style scheduler.
2. **Customizable Layouts:** PDF generation using WeasyPrint, allowing for CSS-based styling of reports.
3. **Data Aggregation:** Ability to join data from the `device_metrics` table and `user_activity` table to create a comprehensive "Device Health Report."
4. **Secure Delivery:** Reports are uploaded to an S3 bucket with a signed URL sent via the Notification System, ensuring reports are not sent as insecure attachments.

**Technical Implementation:**
The system uses a background worker pattern. A `ReportRequest` is created in the DB, a Celery worker generates the CSV/PDF in a temporary directory, uploads it to S3, and then marks the request as `COMPLETE`.

**Constraints:**
- Reports exceeding 10,000 rows must be generated as CSV only to prevent memory exhaustion.
- Must be fully blocked until the Integration Partner API provides the necessary historical endpoint.

---

### 3.5 Real-time Collaborative Editing
**Priority:** High | **Status:** Complete

**Overview:**
Allows multiple administrators to configure a single piece of hardware concurrently without overwriting each other's changes. This is critical for large-scale educational deployments where multiple technicians may be tuning a system.

**Detailed Functional Requirements:**
1. **Operational Transformation (OT):** Implementation of a conflict resolution algorithm to ensure that concurrent edits converge to the same state.
2. **Presence Indicators:** Visual indicators showing who is currently editing which field (e.g., "Wanda is typing...").
3. **Atomic Locks:** Field-level locking to prevent two users from editing the exact same parameter simultaneously.
4. **Version History:** A full audit log of every change made during a session, allowing for "Point-in-Time" recovery.

**Technical Implementation:**
Lodestar uses Django Channels for WebSocket communication. The "Current State" of the edited object is cached in Redis. When a user makes a change, the change is sent as a "Delta" via WebSocket. The server applies the delta to the Redis state, broadcasts the change to other connected clients, and asynchronously persists the final state to PostgreSQL.

**Constraints:**
- Maximum of 50 concurrent collaborators per device configuration page.
- Conflict resolution must be deterministic; the server's timestamp is the ultimate authority.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. All requests require a Bearer Token in the `Authorization` header.

### 4.1 Notification Dispatch
- **Endpoint:** `POST /api/v1/notifications/send`
- **Description:** Triggers a notification based on a template.
- **Request Body:**
  ```json
  {
    "user_id": 10293,
    "template_id": "hw_failure_alert",
    "context": { "device_id": "LD-99", "error_code": "E04" },
    "priority": "critical"
  }
  ```
- **Response:** `202 Accepted` | `{"job_id": "abc-123", "status": "queued"}`

### 4.2 Workflow Rule Creation
- **Endpoint:** `POST /api/v1/workflows/rules`
- **Description:** Creates a new automation rule.
- **Request Body:**
  ```json
  {
    "name": "Temp Alert",
    "trigger": { "type": "sensor", "metric": "temp", "threshold": 40 },
    "action": { "type": "notify", "channel": "sms" }
  }
  ```
- **Response:** `201 Created` | `{"rule_id": 505, "status": "active"}`

### 4.3 Device Configuration Update
- **Endpoint:** `PATCH /api/v1/devices/{device_id}/config`
- **Description:** Updates specific firmware parameters.
- **Request Body:**
  ```json
  {
    "sampling_rate": "500ms",
    "power_mode": "low_power"
  }
  ```
- **Response:** `200 OK` | `{"status": "updated", "version": "1.2.1"}`

### 4.4 Collaborative Session Join
- **Endpoint:** `POST /api/v1/collaboration/sessions`
- **Description:** Initializes a WebSocket connection for real-time editing.
- **Request Body:** `{"device_id": "LD-99"}`
- **Response:** `200 OK` | `{"websocket_url": "wss://api.deepwell.com/ws/collab/LD-99"}`

### 4.5 Search Facets Retrieval
- **Endpoint:** `GET /api/v1/search/facets`
- **Description:** Returns available filter options for the current dataset.
- **Query Params:** `?category=hardware`
- **Response:** `200 OK` | `{"facets": {"model": ["X1", "X2"], "region": ["North", "South"]}}`

### 4.6 Advanced Search
- **Endpoint:** `GET /api/v1/search/query`
- **Description:** Performs full-text and faceted search.
- **Query Params:** `?q=failure&model=X1&region=North`
- **Response:** `200 OK` | `{"results": [...], "total": 42, "page": 1}`

### 4.7 Report Generation Request
- **Endpoint:** `POST /api/v1/reports/generate`
- **Description:** Queues a PDF/CSV report for generation.
- **Request Body:** `{"type": "health_check", "start_date": "2026-01-01", "end_date": "2026-01-31"}`
- **Response:** `202 Accepted` | `{"report_id": "rep-88", "estimated_time": "30s"}`

### 4.8 Collaboration History
- **Endpoint:** `GET /api/v1/collaboration/{device_id}/history`
- **Description:** Retrieves the audit log of changes.
- **Response:** `200 OK` | `{"history": [{"timestamp": "...", "user": "Wanda", "change": "sampling_rate: 1s -> 500ms"}]}`

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL 15. All tables utilize UUIDs as primary keys to prevent ID enumeration and facilitate easier microservice migration.

### 5.1 Table Definitions

1. **`users`**
   - `user_id` (UUID, PK)
   - `email` (VARCHAR, Unique)
   - `password_hash` (TEXT)
   - `role` (ENUM: Admin, Technician, Student)
   - `created_at` (TIMESTAMP)

2. **`devices`**
   - `device_id` (UUID, PK)
   - `serial_number` (VARCHAR, Unique)
   - `model_id` (FK -> `device_models`)
   - `firmware_version` (VARCHAR)
   - `last_seen` (TIMESTAMP)
   - `status` (ENUM: Online, Offline, Error)

3. **`device_models`**
   - `model_id` (UUID, PK)
   - `model_name` (VARCHAR)
   - `manufacturer` (VARCHAR)
   - `spec_sheet_url` (TEXT)

4. **`user_notification_preferences`**
   - `pref_id` (UUID, PK)
   - `user_id` (FK -> `users`)
   - `channel` (ENUM: Email, SMS, Push, InApp)
   - `enabled` (BOOLEAN)
   - `category` (VARCHAR: e.g., "Alerts", "Marketing")

5. **`notification_logs`**
   - `log_id` (UUID, PK)
   - `user_id` (FK -> `users`)
   - `channel` (VARCHAR)
   - `message_body` (TEXT)
   - `delivered_at` (TIMESTAMP)
   - `status` (ENUM: Sent, Failed, Pending)

6. **`workflow_rules`**
   - `rule_id` (UUID, PK)
   - `name` (VARCHAR)
   - `logic_json` (JSONB) - Stores the visual rule tree.
   - `is_active` (BOOLEAN)
   - `created_by` (FK -> `users`)

7. **`workflow_logs`**
   - `log_id` (UUID, PK)
   - `rule_id` (FK -> `workflow_rules`)
   - `triggered_at` (TIMESTAMP)
   - `outcome` (TEXT)

8. **`device_configs`**
   - `config_id` (UUID, PK)
   - `device_id` (FK -> `devices`)
   - `config_payload` (JSONB)
   - `version` (INTEGER)
   - `updated_at` (TIMESTAMP)

9. **`collaboration_sessions`**
   - `session_id` (UUID, PK)
   - `device_id` (FK -> `devices`)
   - `started_at` (TIMESTAMP)
   - `ended_at` (TIMESTAMP)

10. **`collaboration_audit_trail`**
    - `audit_id` (UUID, PK)
    - `session_id` (FK -> `collaboration_sessions`)
    - `user_id` (FK -> `users`)
    - `field_changed` (VARCHAR)
    - `old_value` (TEXT)
    - `new_value` (TEXT)
    - `timestamp` (TIMESTAMP)

### 5.2 Relationships
- `users` 1:N `user_notification_preferences`
- `devices` 1:1 `device_configs`
- `device_models` 1:N `devices`
- `workflow_rules` 1:N `workflow_logs`
- `collaboration_sessions` 1:N `collaboration_audit_trail`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lodestar utilizes three distinct environments to ensure stability and ISO 27001 compliance.

**1. Development (Dev):**
- **Purpose:** Feature experimentation and unit testing.
- **Infrastructure:** Small ECS cluster, shared PostgreSQL instance.
- **Deployment:** Automatic deploy on every merge to the `develop` branch.

**2. Staging (Staging):**
- **Purpose:** Integration testing, QA, and Stakeholder UAT.
- **Infrastructure:** Mirror of Production (ECS Fargate, Read Replicas).
- **Data:** Anonymized production data snapshot.
- **Deployment:** Triggered by release tags in GitHub Actions.

**3. Production (Prod):**
- **Purpose:** Live operational environment.
- **Infrastructure:** High-availability ECS cluster across 3 Availability Zones.
- **Compliance:** Full encryption at rest and in transit; audit logs streamed to AWS CloudWatch and S3.
- **Deployment:** Blue-Green Deployment strategy.

### 6.2 Blue-Green Deployment Process
To achieve the **zero-downtime** requirement:
1. **Green Environment:** A new version of the application is deployed to a separate set of ECS tasks.
2. **Health Checks:** The ALB performs deep health checks on the Green environment.
3. **Traffic Shift:** Once healthy, the ALB gradually shifts traffic (10% $\rightarrow$ 50% $\rightarrow$ 100%) from Blue (old) to Green (new).
4. **Rollback:** If any p95 latency spikes or error rates increase above 1%, the ALB instantly reverts 100% of traffic to the Blue environment.

### 6.3 CI/CD Pipeline (GitHub Actions)
- **Linting/Formatting:** Black and Flake8 run on every push.
- **Testing:** PyTest suite runs (Unit $\rightarrow$ Integration $\rightarrow$ E2E).
- **Containerization:** Docker images are built and pushed to AWS ECR.
- **Deployment:** Terraform scripts update the ECS service definition.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and logic components (e.g., the Workflow Logic Parser).
- **Tooling:** `pytest` with `unittest.mock`.
- **Requirement:** Minimum 85% code coverage for all new modules.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between the Django app, PostgreSQL, and Redis.
- **Approach:** Using `TestContainers` to spin up real instances of Postgres and Redis during the test phase.
- **Focus:** Ensuring that the Collaboration Logic correctly synchronizes state between the cache and the database.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Create Rule $\rightarrow$ Trigger Event $\rightarrow$ Receive SMS").
- **Tooling:** Playwright for UI automation and `requests` for API flow testing.
- **Execution:** Weekly runs in the Staging environment.

### 7.4 Performance Testing
- **Load Testing:** Using Locust to simulate 5,000 concurrent device connections.
- **Metric:** Ensure p95 API response time remains under 200ms.
- **Chaos Engineering:** Randomly terminating ECS tasks in Staging to ensure the system recovers without data loss.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | Medium | High | Build a contingency plan: prioritize core firmware stability over "nice-to-have" search/reporting features. |
| R-02 | Integration partner API is undocumented/buggy | High | Medium | Create an "Adapter Layer" to isolate partner bugs; de-scope PDF reporting if API remains unstable by Milestone 2. |
| R-03 | Legacy system downtime during migration | Low | Critical | Use the Strangler Fig pattern with a fail-safe proxy that reverts to legacy on any Lodestar error. |
| R-04 | Personnel loss (key member departure) | Low | Medium | Maintain rigorous documentation (this doc) and cross-train the intern (Wes Santos) on core modules. |

**Probability/Impact Matrix:**
- **Low/Low:** Monitor only.
- **High/Medium:** Active mitigation required.
- **Low/Critical:** High-alert monitoring and immediate rollback plans.

---

## 9. TIMELINE & MILESTONES

### 9.1 Phases and Dependencies
**Phase 1: Core Infrastructure (Completed)**
- Setup AWS ECS, PostgreSQL, and CI/CD.
- Implementation of Collaborative Editing and Workflow Engine.

**Phase 2: Communication & Search (Current)**
- Implementation of Notification System (In Progress).
- Implementation of Advanced Search (In Progress).
- *Dependency:* Notification system must be stable before the External Beta.

**Phase 3: Validation & Beta (Upcoming)**
- External Beta testing with pilot users.
- Refinement of API based on pilot feedback.

**Phase 4: Final Transition**
- Full cut-over from Legacy to Lodestar.
- Decommissioning of legacy servers.

### 9.2 Key Milestone Dates
- **Milestone 1: External Beta (10 Pilot Users)**
  - **Target Date:** 2026-04-15
  - **Criteria:** Notification system and Workflow engine fully operational.
- **Milestone 2: Stakeholder Demo and Sign-off**
  - **Target Date:** 2026-06-15
  - **Criteria:** All "High" priority features passed QA; p95 latency < 200ms.
- **Milestone 3: Internal Alpha Release**
  - **Target Date:** 2026-08-15
  - **Criteria:** Full internal rollout to all Deepwell Data staff.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per team agreement, formal meeting minutes are not kept. The following are synthesized from key Slack decision threads.*

### Thread 1: `#lodestar-dev` — 2024-02-10
**Participants:** Wanda, Ravi, Saoirse
**Topic:** Blue-Green vs. Canary Deployment
- **Wanda:** "We can't afford a 1% error rate for 10 minutes during a Canary roll-out. The legacy system is too critical."
- **Ravi:** "Agreed. Let's stick to Blue-Green. We'll spin up a full parallel environment and flip the ALB switch only after the health checks pass 100%."
- **Decision:** Blue-Green deployment is the mandatory standard for all Production updates.

### Thread 2: `#lodestar-design` — 2024-03-05
**Participants:** Saoirse, Wanda, Wes
**Topic:** Visual Rule Builder Complexity
- **Saoirse:** "The current drag-and-drop is getting too cluttered. I suggest moving to a 'block-based' logic like Scratch."
- **Wes:** "I can implement the frontend changes, but will the JSON schema change?"
- **Wanda:** "Keep the JSON schema backward compatible. The backend doesn't care how the user draws the rule, as long as the logic tree is valid."
- **Decision:** Transition to block-based UI; maintain existing JSONB schema in PostgreSQL.

### Thread 3: `#lodestar-infra` — 2024-04-12
**Participants:** Ravi, Wanda
**Topic:** Third-Party API Rate Limits (Current Blocker)
- **Ravi:** "The partner API is throttling us at 100 requests/min. We can't even finish the integration tests for the PDF reports."
- **Wanda:** "We've emailed them three times. If they don't increase the limit by the end of the month, we are officially blocking the Report Generation feature."
- **Decision:** Report Generation is marked as `BLOCKED`. Priority shifted to refining the Notification system.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $975,000 | Salaries for Tech Lead, DevOps, Designer, and Intern across 24 months. |
| **Infrastructure** | 15% | $225,000 | AWS ECS, RDS, Redis, and S3 costs (including scaling for peak load). |
| **Tools & Licensing** | 5% | $75,000 | GitHub Enterprise, Datadog for monitoring, Twilio/SendGrid APIs. |
| **Contingency** | 15% | $225,000 | Reserved for budget cuts or emergency third-party consultancy. |

**Budget Note:** In the event of the projected 30% budget cut ($450k), the Contingency fund will be exhausted first, followed by the complete removal of the "Low Priority" features (Advanced Search and PDF Reporting).

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Algorithm (OT)
To handle real-time collaborative editing, Lodestar implements a simplified Operational Transformation (OT) logic. When two users edit the same field:
1. **Client Side:** Local change is applied immediately (optimistic UI).
2. **Server Side:** The server receives the change and checks the `version_id`.
3. **Transformation:** If the `version_id` is outdated, the server transforms the incoming operation based on the history of operations since that version.
4. **Broadcast:** The transformed operation is broadcast to all clients.
5. **Convergence:** All clients apply the transformed operation, ensuring that everyone sees the same final state.

### Appendix B: ISO 27001 Compliance Checklist
To maintain certification, the Lodestar environment adheres to:
- **Encryption:** All S3 buckets use AES-256; all DB connections use SSL/TLS.
- **Access Control:** IAM roles are strictly scoped (Least Privilege Principle).
- **Auditability:** Every API call is logged with the user ID and timestamp in a non-mutable CloudWatch log group.
- **Vulnerability Scanning:** Snyk scans Docker images for vulnerabilities during the GitHub Actions build phase.
- **Backups:** RDS snapshots are taken every 6 hours and replicated across two AWS regions.