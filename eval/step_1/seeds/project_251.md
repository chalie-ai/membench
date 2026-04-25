# PROJECT SPECIFICATION: PROJECT BASTION
**Document Version:** 1.0.4  
**Status:** Final / Approved  
**Date:** October 24, 2024  
**Owner:** Suki Moreau (CTO)  
**Classification:** Confidential – Oakmount Group Internal

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Bastion is a strategic Research and Development initiative commissioned by the Oakmount Group. It is designed as a comprehensive data pipeline and analytics platform specifically tailored for the renewable energy sector. The primary objective of Bastion is to aggregate heterogeneous data streams from solar arrays, wind turbine telemetry, and grid-edge storage devices, converting raw sensory data into actionable business intelligence for grid operators and asset managers.

### 1.2 Business Justification
The renewable energy sector is currently plagued by "data silos," where hardware manufacturers provide proprietary formats that cannot be easily cross-referenced. Oakmount Group aims to position itself as the central nervous system for these assets. By creating a platform that can ingest, normalize, and analyze data regardless of the hardware vendor, Bastion transforms Oakmount from a service provider into a platform provider. 

The "moonshot" nature of this project stems from the inherent uncertainty of the current regulatory landscape. However, the strategic value lies in the "First Mover Advantage." If Bastion becomes the industry standard for renewable energy telemetry, the company will possess an insurmountable moat in terms of data gravity and ecosystem lock-in.

### 1.3 ROI Projection
Given that Project Bastion is currently unfunded and bootstrapping using existing team capacity, the traditional ROI calculation (Net Present Value) is atypical. Instead, the ROI is projected via "Strategic Optionality."

**Conservative Projection (3-Year Horizon):**
- **Direct Revenue:** $2.4M ARR via tiered API access and platform licensing.
- **Cost Savings:** 30% reduction in manual data auditing costs for current Oakmount clients.
- **Strategic Value:** Ability to bid on government infrastructure contracts requiring ISO 27001 compliance and advanced telemetry auditing.

While the immediate ROI is uncertain, the risk of *not* building Bastion is the loss of market share to agile startups specializing in "Energy-as-a-Service" (EaaS). Executive sponsorship remains strong, viewing this as a high-risk, high-reward investment in the company's future intellectual property.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Philosophy
Bastion utilizes a "Clean Monolith" approach. While the industry trend leans toward microservices, the current team size (15 people) and the need for rapid iteration make a distributed system a liability. The architecture enforces strict module boundaries (Modular Monolith), ensuring that the domain logic for the "Workflow Automation Engine" is physically and logically separated from the "Audit Trail" logic, allowing for a future migration to microservices if the project scales.

### 2.2 The Mixed-Stack Challenge
The project inherits three legacy stacks that must interoperate:
1. **Legacy Telemetry (Python 3.7/Django):** Handles raw socket connections from wind turbines.
2. **Analytics Engine (Java 11/Spring Boot):** Performs heavy-duty time-series calculations.
3. **Customer Portal (Node.js/React):** The primary interface for end-users.

These three stacks communicate via a shared PostgreSQL 15 instance and a RabbitMQ message bus.

### 2.3 ASCII Architecture Diagram
```text
[ EXTERNAL DATA SOURCES ] --> [ INGESTION LAYER ] --> [ MESSAGE BUS ]
(Wind/Solar/Grid APIs)       (Python/Django App)     (RabbitMQ)
                                     |                    |
                                     v                    v
[ USER INTERFACE ] <--- [ CORE MONOLITH ] <--- [ ANALYTICS ENGINE ]
(React/TypeScript)     (Node.js/Express)       (Java/Spring Boot)
       ^                      |                           |
       |                      v                           v
       +----------- [ POSTGRESQL CLUSTER ] <-------------+
                    (Audit Logs | Asset Data | Users)
                                     |
                                     v
                         [ ISO 27001 SECURE VAULT ]
                         (KMS / HSM / Encrypted EBS)
```

### 2.4 Deployment Strategy
Currently, Bastion relies on a "Single Point of Failure" deployment model. All deployments are performed manually by one DevOps engineer. This represents a "Bus Factor of 1." The pipeline is a Jenkins-based system where the CI stage takes approximately 45 minutes due to a lack of parallelization and bloated integration tests.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Complete
**Description:**
The Workflow Automation Engine allows operators to define "If-This-Then-That" (IFTTT) logic for energy assets. For example, "If Wind Turbine A output drops below 20% and wind speed is > 10m/s, then trigger a Maintenance Ticket."

**Technical Specifications:**
- **Visual Rule Builder:** A drag-and-drop canvas using React-Flow, allowing users to map triggers to actions.
- **Rule Execution:** Rules are compiled into JSON logic and stored in the `workflow_rules` table. The Java Analytics Engine polls these rules every 60 seconds against the incoming telemetry stream.
- **State Machine:** The engine utilizes a finite state machine (FSM) to ensure that a "Maintenance Ticket" isn't triggered every second, but rather once per incident.
- **Integration:** Connects directly to the Audit Trail for logging every rule execution.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review
**Description:**
To meet ISO 27001 requirements, every change to the system—whether by a user or an automated workflow—must be logged in a way that cannot be altered after the fact.

**Technical Specifications:**
- **Hashing Chain:** Each log entry contains a SHA-256 hash of (Current Entry + Previous Entry Hash), creating a blockchain-like ledger within the PostgreSQL database.
- **WORM Storage:** Once a log is finalized, it is mirrored to an AWS S3 bucket with "Object Lock" enabled (Write Once, Read Many), preventing any deletion or modification for 7 years.
- **Verification Tool:** A background worker periodically re-calculates the hashes. If a mismatch is found, an immediate "Security Breach" alert is dispatched to Suki Moreau.
- **Granularity:** Logs capture `timestamp`, `actor_id`, `action_type`, `previous_state`, `new_state`, and `ip_address`.

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** Blocked
**Description:**
A user-configurable landing page where renewable energy managers can arrange "widgets" (gauges, time-series graphs, alert lists) to monitor their fleet.

**Technical Specifications:**
- **Widget Library:** A set of pre-defined components built with Chart.js and D3.js.
- **Layout Persistence:** The layout is stored as a JSON blob in the `user_dashboards` table, utilizing a grid-coordinate system (x, y, w, h).
- **Real-time Updates:** Widgets subscribe to WebSocket channels via the Node.js backend to receive live telemetry without refreshing the page.
- **Blocker:** This feature is currently blocked by the lack of a standardized data schema for the "Mixed Stack" telemetry; the frontend cannot reliably predict the data types returning from the Java vs. Python backends.

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Low (Nice to Have) | **Status:** In Design
**Description:**
An external REST API that allows third-party partners to programmatically pull analytics and push asset configurations.

**Technical Specifications:**
- **Versioning:** Use of URI versioning (e.g., `/api/v1/assets`).
- **Sandbox Environment:** A mirrored, anonymized database where customers can test their API calls without affecting production data.
- **Authentication:** OAuth2 with JWT (JSON Web Tokens). API keys are rotated every 90 days.
- **Rate Limiting:** Implemented via Redis, capping users at 1,000 requests per hour for the "Standard" tier.

### 3.5 Webhook Integration Framework for Third-Party Tools
**Priority:** Low (Nice to Have) | **Status:** Not Started
**Description:**
A framework to push Bastion events (e.g., "Critical Failure Detected") to external URLs (Slack, Microsoft Teams, PagerDuty).

**Technical Specifications:**
- **Payload Format:** Standard JSON payload containing the event type, severity, and a deep link back to the Bastion dashboard.
- **Retry Logic:** Exponential backoff strategy. If a webhook fails, the system retries at 1 min, 5 mins, 15 mins, and 1 hour.
- **Secret Signing:** Each webhook request is signed with an `X-Bastion-Signature` header (HMAC-SHA256) to allow the receiver to verify the request originated from Oakmount Group.
- **Management UI:** A page where users can add/remove URLs and test the connection with a "Send Test Ping" button.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted on `https://api.bastion.oakmount.com`.

### 4.1 Asset Management
**GET /api/v1/assets**
- **Description:** Retrieves a list of all monitored renewable energy assets.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  [
    {"id": "WIND-001", "type": "turbine", "status": "active", "location": "North Sea"},
    {"id": "SOL-442", "type": "array", "status": "maintenance", "location": "Nevada"}
  ]
  ```

**POST /api/v1/assets**
- **Description:** Registers a new asset into the system.
- **Request Body:**
  ```json
  {"asset_name": "Sahara-East-01", "type": "solar", "capacity_mw": 50}
  ```
- **Response (201 Created):** `{"id": "SOL-999", "status": "registered"}`

### 4.2 Workflow Automation
**GET /api/v1/workflows**
- **Description:** Lists all active automation rules.
- **Response (200 OK):**
  ```json
  [{"rule_id": "RULE-101", "trigger": "low_output", "action": "email_admin"}]
  ```

**POST /api/v1/workflows/execute**
- **Description:** Manually triggers a workflow for testing.
- **Request Body:** `{"rule_id": "RULE-101", "override_params": {"force": true}}`
- **Response (202 Accepted):** `{"job_id": "JOB-8821", "status": "queued"}`

### 4.3 Audit & Security
**GET /api/v1/audit/logs**
- **Description:** Retrieves the tamper-evident log chain.
- **Query Params:** `?start_date=2024-01-01&end_date=2024-01-02`
- **Response (200 OK):**
  ```json
  [{"timestamp": "2024-10-24T10:00Z", "action": "LOGIN", "hash": "a1b2c3...", "prev_hash": "z9y8x7..."}]
  ```

**POST /api/v1/audit/verify**
- **Description:** Triggers a full chain verification of the audit logs.
- **Response (200 OK):** `{"status": "verified", "checksums": "valid", "last_verified": "2024-10-24T12:00Z"}`

### 4.4 Telemetry Data
**GET /api/v1/telemetry/{asset_id}**
- **Description:** Fetches real-time metrics for a specific asset.
- **Response (200 OK):**
  ```json
  {"asset_id": "WIND-001", "metrics": {"wind_speed": "12m/s", "output_kw": "450"}}
  ```

**PUT /api/v1/telemetry/{asset_id}/config**
- **Description:** Updates the polling frequency of the hardware.
- **Request Body:** `{"polling_interval_seconds": 30}`
- **Response (200 OK):** `{"status": "updated"}`

---

## 5. DATABASE SCHEMA

The system utilizes a PostgreSQL 15 cluster. All tables use UUIDs as primary keys to support future sharding.

### 5.1 Table Definitions

1. **`users`**
   - `user_id` (UUID, PK)
   - `email` (VARCHAR, Unique)
   - `password_hash` (TEXT)
   - `role` (ENUM: 'admin', 'operator', 'viewer')
   - `created_at` (TIMESTAMP)

2. **`assets`**
   - `asset_id` (UUID, PK)
   - `name` (VARCHAR)
   - `type` (ENUM: 'wind', 'solar', 'hydro', 'storage')
   - `capacity_mw` (DECIMAL)
   - `installation_date` (DATE)
   - `status` (VARCHAR)

3. **`telemetry_data`** (Partitioned by month)
   - `data_id` (BIGINT, PK)
   - `asset_id` (UUID, FK -> assets)
   - `metric_name` (VARCHAR)
   - `metric_value` (DOUBLE PRECISION)
   - `captured_at` (TIMESTAMP)

4. **`workflow_rules`**
   - `rule_id` (UUID, PK)
   - `name` (VARCHAR)
   - `trigger_condition` (JSONB)
   - `action_payload` (JSONB)
   - `is_active` (BOOLEAN)

5. **`workflow_executions`**
   - `exec_id` (UUID, PK)
   - `rule_id` (UUID, FK -> workflow_rules)
   - `triggered_at` (TIMESTAMP)
   - `status` (ENUM: 'success', 'failed', 'pending')

6. **`audit_logs`**
   - `log_id` (UUID, PK)
   - `timestamp` (TIMESTAMP)
   - `actor_id` (UUID, FK -> users)
   - `action` (VARCHAR)
   - `payload_before` (JSONB)
   - `payload_after` (JSONB)
   - `entry_hash` (VARCHAR)
   - `prev_hash` (VARCHAR)

7. **`user_dashboards`**
   - `dashboard_id` (UUID, PK)
   - `user_id` (UUID, FK -> users)
   - `layout_config` (JSONB)
   - `updated_at` (TIMESTAMP)

8. **`api_keys`**
   - `key_id` (UUID, PK)
   - `user_id` (UUID, FK -> users)
   - `key_value` (VARCHAR, Encrypted)
   - `expires_at` (TIMESTAMP)

9. **`webhook_subscriptions`**
   - `sub_id` (UUID, PK)
   - `user_id` (UUID, FK -> users)
   - `target_url` (TEXT)
   - `event_types` (ARRAY)
   - `secret_token` (VARCHAR)

10. **`system_config`**
    - `config_key` (VARCHAR, PK)
    - `config_value` (TEXT)
    - `updated_by` (UUID, FK -> users)

### 5.2 Relationships
- `users` $\rightarrow$ `audit_logs` (One-to-Many)
- `assets` $\rightarrow$ `telemetry_data` (One-to-Many)
- `workflow_rules` $\rightarrow$ `workflow_executions` (One-to-Many)
- `users` $\rightarrow$ `user_dashboards` (One-to-One)
- `users` $\rightarrow$ `api_keys` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and local testing.
- **Host:** Individual developer machines + shared Docker Compose environment.
- **Database:** Local PostgreSQL containers with seeded mock data.
- **Deployment:** Manual `git push` to a dev branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation, QA testing, and UAT.
- **Host:** AWS EC2 instances in a dedicated VPC.
- **Database:** RDS PostgreSQL (Small instance).
- **Deployment:** Manual trigger by the DevOps person. This environment mimics Production exactly, including the ISO 27001 security constraints.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Host:** AWS EKS (Elastic Kubernetes Service) with multi-AZ distribution.
- **Database:** RDS PostgreSQL (Multi-AZ, High Availability) with automated snapshots every 6 hours.
- **Deployment:** Manual deployment. The "Bus Factor of 1" risk is highest here; only the DevOps lead has the SSH keys and IAM permissions to execute the final `kubectl apply`.

### 6.2 Infrastructure Constraints
- **Security:** Must maintain ISO 27001 certification. This requires all data at rest to be encrypted using AES-256 and all data in transit to use TLS 1.3.
- **CI/CD Pipeline:** The current Jenkins pipeline consists of a single linear sequence. To fix the 45-minute build time, the team plans to implement parallel test execution (splitting the Java and Node.js suites) and caching for the `node_modules` and Maven dependencies.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Objective:** Validate individual functions and logic blocks in isolation.
- **Tooling:** Jest (Node.js), JUnit 5 (Java), PyTest (Python).
- **Requirement:** All new PRs must have $>80\%$ code coverage.
- **Focus:** Business logic in the Workflow Engine and Hash calculations in the Audit Trail.

### 7.2 Integration Testing
- **Objective:** Ensure the three inherited stacks communicate correctly.
- **Approach:** "Contract Testing." We define the API expectations between the Python ingestion layer and the Java analytics engine.
- **Tooling:** Postman/Newman for API contract validation.
- **Scenario:** Verify that a raw data packet from Python is correctly parsed and stored in PostgreSQL for the Java engine to read.

### 7.3 End-to-End (E2E) Testing
- **Objective:** Simulate a complete user journey from data ingestion to dashboard visualization.
- **Tooling:** Playwright / Cypress.
- **Critical Path:**
  1. Simulate hardware telemetry $\rightarrow$ Ingestion Layer.
  2. Verify Workflow Engine triggers an alert.
  3. Verify Audit Log records the alert.
  4. Verify the alert appears on the Dashboard.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for renewables change mid-project. | High | High | **Accept Risk:** Monitor weekly via legal updates; maintain modular architecture to pivot quickly. |
| R-02 | Integration partner API is undocumented and buggy. | High | Medium | **Active Mitigation:** Document every quirk/workaround in the internal Wiki; create a wrapper layer to sanitize partner data. |
| R-03 | DevOps "Bus Factor of 1" (Single point of failure). | Medium | Critical | **Planned Mitigation:** Cross-train Kai Santos on deployment scripts by Q1 2025. |
| R-04 | CI Pipeline latency (45 min) slows development velocity. | High | Low | **Planned Mitigation:** Implement parallelization of test suites in the Jenkinsfile. |
| R-05 | Inherited stacks lead to "Dependency Hell." | Medium | Medium | **Active Mitigation:** Use Docker containers to isolate runtime environments for each stack. |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required.
- **High:** Regular monitoring and contingency planning.
- **Medium:** Manageable through standard procedures.
- **Low:** Accept and ignore until it manifests.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Current $\rightarrow$ Jan 2025)
- **Focus:** Stability of the mixed-stack communication and completion of the Workflow Engine.
- **Dependency:** Completion of the PostgreSQL schema migration.
- **Key Goal:** Resolve the "Blocked" status of the Dashboard by standardizing the telemetry schema.

### 9.2 Phase 2: Hardening (Jan 2025 $\rightarrow$ April 2025)
- **Focus:** Security audit, ISO 27001 compliance check, and Audit Trail finalization.
- **Dependency:** Successful E2E testing of the tamper-evident logs.
- **Milestone 1: Production Launch (Target: 2025-04-15)**

### 9.3 Phase 3: Stabilization (April 2025 $\rightarrow$ June 2025)
- **Focus:** Monitoring uptime, fixing production bugs, and scaling the database.
- **Metric:** Achieve 99.9% uptime.
- **Milestone 2: Post-launch stability confirmed (Target: 2025-06-15)**

### 9.4 Phase 4: Expansion (June 2025 $\rightarrow$ August 2025)
- **Focus:** Developing the Customer API and Sandbox environment.
- **Dependency:** Stability of the core platform.
- **Milestone 3: Internal alpha release of API (Target: 2025-08-15)**

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Due to the length of calls, these summaries are the only written records available.*

### Meeting 1: Architecture Review (Oct 12, 2024)
- **Attendees:** Suki, Layla, Kai, Zev.
- **Discussion:** Layla raised concerns about the "Clean Monolith" approach, suggesting microservices for the dashboard. Suki overruled, citing the 15-person team size and the risk of operational overhead.
- **Decision:** Stick to the monolith but enforce strict module boundaries using Java packages and Node.js folders.
- **Action Item:** Zev to document the current data flow from the Python stack to the Java stack.

### Meeting 2: Security & ISO 27001 Alignment (Oct 19, 2024)
- **Attendees:** Suki, Kai.
- **Discussion:** Kai pointed out that the current manual deployment process is a security risk. Suki agreed but noted that they lack the budget for a full CI/CD overhaul right now.
- **Decision:** Implement "Two-Person Approval" for production deployments. Kai will review the deployment manifest before the DevOps person executes it.
- **Action Item:** Kai to draft the tamper-evidence verification script for the Audit Trail.

### Meeting 3: Sprint Planning - "The Dashboard Blocker" (Oct 26, 2024)
- **Attendees:** Suki, Layla, Kai, Zev.
- **Discussion:** Layla demonstrated that the dashboard widgets are crashing because the Java API returns `float` while the Python API returns `string` for the same metric.
- **Decision:** Implement a "Data Normalization Layer" in the Node.js backend to cast all telemetry to a consistent format before sending it to the frontend.
- **Action Item:** Layla to define the required frontend data types; Zev to implement the casting logic.

---

## 11. BUDGET BREAKDOWN

As Project Bastion is currently unfunded and bootstrapping, the budget represents "Opportunity Cost" (internal allocation of existing salaries) rather than cash expenditures.

| Category | Annual Allocated Value | Description |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $1,850,000 | Distributed team of 15 (Suki, Layla, Kai, Zev, +11 others) across 5 countries. |
| **Infrastructure (AWS)** | $42,000 | RDS, EKS, and S3 Object Lock storage (covered by Oakmount Group's general IT budget). |
| **Tools & Licenses** | $12,000 | Jenkins Enterprise, JetBrains IDs, and Zoom Pro. |
| **Contingency** | $50,000 | Set aside for emergency external security auditing (ISO 27001). |
| **TOTAL** | **$1,954,000** | **Total internal cost of ownership.** |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist
To maintain certification, Bastion must adhere to the following:
- **A.12.1.2 Change Management:** All changes to production must be logged and approved.
- **A.12.4.1 Event Logging:** The Audit Trail must record all user activities.
- **A.18.1.1 Identification of Applicable Legislation:** Weekly monitoring of renewable energy laws (Mitigation R-01).
- **Encryption:** All S3 buckets must use SSE-KMS.

### Appendix B: Telemetry Data normalization Logic
To resolve the Dashboard blocker, the following logic is applied at the Node.js Gateway:

```typescript
function normalizeMetric(value: any, targetType: 'float' | 'int' | 'string'): any {
    if (targetType === 'float') {
        const parsed = parseFloat(value);
        return isNaN(parsed) ? 0.0 : parsed;
    }
    if (targetType === 'int') {
        const parsed = parseInt(value, 10);
        return isNaN(parsed) ? 0 : parsed;
    }
    return String(value);
}
```
This ensures that regardless of whether the data comes from the Legacy Python stack or the Java Analytics engine, the React frontend receives a consistent type, preventing UI crashes.