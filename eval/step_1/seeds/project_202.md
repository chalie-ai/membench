# PROJECT SPECIFICATION DOCUMENT: PROJECT GANTRY
**Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 24, 2023  
**Company:** Stratos Systems  
**Classification:** Confidential – Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Gantry represents a strategic pivot for Stratos Systems, marking the company's entry into the Agriculture Technology (AgTech) sector. Gantry is designed as a sophisticated IoT device network capable of managing high-density sensor arrays and actuator controllers across vast agricultural landscapes. The system aims to bridge the gap between raw field telemetry and actionable enterprise business intelligence.

### 1.2 Business Justification
The impetus for Project Gantry is a direct partnership with a Tier-1 enterprise agricultural conglomerate. This client has committed to a service agreement yielding $2M in annual recurring revenue (ARR) upon successful deployment. For Stratos Systems, Gantry is not merely a product but a "vertical beachhead." By solving the complex problems of offline-first connectivity and real-time collaborative management in a rural environment, Stratos establishes a proprietary framework that can be licensed to other agricultural enterprises.

### 1.3 ROI Projection and Financial Outlook
With a total capital expenditure (CAPEX) budget of $3M, the project is heavily front-loaded in personnel and infrastructure costs. 

**Projected Financials:**
- **Year 1 Investment:** $3,000,000 (Development, Hardware, Infrastructure).
- **Year 1 Revenue (Post-Launch):** $2,000,000 (Single Enterprise Contract).
- **Year 2 Projected Revenue:** $5,500,000 (Expansion to 2 additional enterprise clients + tiered subscription scaling).
- **Break-Even Point:** Estimated at Month 14 post-launch.
- **ROI (3-Year Window):** Anticipated at 210%, driven by the transition from a bespoke project to a scalable SaaS-lite model.

### 1.4 Strategic Objectives
The primary objective is to deliver a robust, ISO 27001-compliant IoT orchestration platform. The project must balance the immediate needs of the anchor client with the long-term scalability of the Gantry architecture. Success is measured not just by the delivery of features, but by the stability of the network (99.9% uptime) and the ability to pass a rigorous external security audit on the first attempt.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Gantry utilizes a Hexagonal Architecture to decouple the core business logic (the "Domain") from external dependencies (the "Infrastructure"). This is critical given the risk associated with the undocumented partner APIs and the potential need to swap out database drivers or messaging queues without rewriting the business rules.

**Core Components:**
- **The Domain:** Pure Python logic containing the business rules for IoT device state, billing logic, and collaborative editing algorithms.
- **Ports:** Interfaces that define *how* the domain communicates with the outside world (e.g., `IDeviceRepository`, `INotificationService`).
- **Adapters:** Concrete implementations of ports. For example, the `MongoDeviceAdapter` implements `IDeviceRepository` using MongoDB.

### 2.2 Tech Stack
- **Language/Framework:** Python 3.11 / FastAPI (Asynchronous I/O for high-concurrency IoT telemetry).
- **Database:** MongoDB 6.0 (NoSQL for flexible device metadata and telemetry storage).
- **Task Queue:** Celery 5.3 with Redis as a broker (For asynchronous processing of webhooks and billing cycles).
- **Containerization:** Docker Compose (Standardized environments across dev, staging, and prod).
- **Hosting:** Self-hosted on private infrastructure to meet strict ISO 27001 requirements and client data sovereignty mandates.

### 2.3 ASCII Architecture Diagram
```text
[ External Clients ] <---> [ FastAPI Gateway ] <---> [ Application Core ]
                                   ^                        |
                                   |                        |
                          [ Adapters Layer ] <--------------+
                                   |
        +--------------------------+--------------------------+
        |                          |                          |
 [ MongoDB Atlas ]          [ Celery Worker ]          [ Partner API ]
 (State/Telemetry)          (Background Jobs)          (External Integration)
        |                          |                          |
  [ Raw SQL Layer ] <--- [ Performance Optimized Queries ] ---> [ Cache ]
```

### 2.4 Deployment Strategy: The Release Train
Gantry follows a strict **Weekly Release Train** model.
- **Train Departure:** Every Thursday at 02:00 UTC.
- **Cut-off:** All merged PRs must be verified by QA by Wednesday 18:00 UTC.
- **Policy:** No hotfixes are permitted outside the train. If a bug is discovered on Friday, it is queued for the following Thursday. This ensures stability and prevents "regression cascades" in a complex IoT environment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing (Priority: Critical)
**Status:** In Progress | **Launch Blocker: YES**

**Description:**
Agricultural managers often need to calibrate device thresholds (e.g., moisture levels, temperature triggers) simultaneously from different locations. This feature allows multiple users to edit device configuration files in real-time without overwriting each other's changes.

**Technical Implementation:**
We are implementing a Conflict-free Replicated Data Type (CRDT) approach using a LWW-Element-Set (Last-Write-Wins) to handle concurrent updates. Since the environment is offline-first, the system must resolve conflicts after a device reconnects to the network.

**Operational Requirements:**
- **Latency:** UI updates must reflect changes within 200ms for connected users.
- **Conflict Resolution:** In the event of a collision, the system will prioritize the most recent timestamp provided by the server, unless a manual override is triggered by an administrator.
- **Locking:** "Soft-locking" will be implemented where a user seeing another user's cursor in a field is warned that the field is being edited.

**Success Criteria:**
- Zero data loss during concurrent edits by three or more users.
- Seamless transition from "Offline" to "Collaborative" mode upon reconnection.

### 3.2 Offline-First Mode with Background Sync (Priority: Medium)
**Status:** Complete**

**Description:**
Given that agricultural fields often have sporadic LTE/Satellite connectivity, Gantry cannot rely on a constant heartbeat. The device-side software must allow full operational capability (data logging, local trigger execution) while offline, syncing data once a connection is re-established.

**Technical Implementation:**
The system employs a local SQLite buffer on the IoT gateway. Data is stored with a monotonically increasing sequence ID. Upon reconnection, the `SyncManager` initiates a "handshake" with the FastAPI backend, comparing the last successfully received sequence ID.

**Sync Logic:**
- **Delta Uploads:** Only changed records are uploaded to reduce bandwidth.
- **Compression:** Payloads are compressed using Gzip before transmission.
- **Conflict Handling:** The backend utilizes the sequence IDs to ensure data is inserted into MongoDB in the correct chronological order, regardless of the upload time.

**Success Criteria:**
- 100% data recovery after a simulated 48-hour network outage.
- Sync process does not exceed 5% of the total available bandwidth during peak telemetry windows.

### 3.3 Customer-Facing API with Versioning and Sandbox (Priority: Medium)
**Status:** In Review**

**Description:**
To allow the enterprise client to build their own dashboards, Gantry provides a RESTful API. To ensure longevity, the API must be versioned, and a sandbox environment must be provided for the client's developers to test scripts without affecting live agricultural hardware.

**Technical Implementation:**
- **Versioning:** URI-based versioning (e.g., `/api/v1/...`).
- **Sandbox:** A mirrored environment utilizing a "mock" device layer. Requests to the sandbox API trigger simulated device responses based on predefined profiles.
- **Authentication:** OAuth2 with JWTs (JSON Web Tokens), with scopes defining access levels (e.g., `read:telemetry`, `write:config`).

**Sandbox Constraints:**
- The sandbox is isolated from the production database.
- It mimics the latency of the real-world network to provide a realistic testing environment for the client.

**Success Criteria:**
- Ability to deprecate v1 while v2 is active without breaking client integrations.
- Sandbox environment mirroring 95% of production API behavior.

### 3.4 Webhook Integration Framework (Priority: High)
**Status:** In Design**

**Description:**
The client requires Gantry to trigger external actions (e.g., notifying a third-party irrigation vendor or triggering an alert in a legacy ERP system) when specific telemetry thresholds are met.

**Technical Implementation:**
A "Dispatcher" service built on Celery. When a "Trigger Event" is fired in the domain layer, the Dispatcher looks up the registered webhooks for that event.
- **Retry Policy:** Exponential backoff (1min, 5min, 15min, 1hr) for failed deliveries.
- **Security:** Each webhook payload is signed with an HMAC-SHA256 signature to allow the receiver to verify the origin.
- **Filtering:** Users can define JSON-based filters so webhooks only fire if specific conditions are met (e.g., `temperature > 35C`).

**Success Criteria:**
- Delivery of webhooks within 5 seconds of the event trigger.
- Full traceability of webhook delivery attempts in the admin dashboard.

### 3.5 Automated Billing and Subscription Management (Priority: Low)
**Status:** Blocked**

**Description:**
A system to track device usage, data throughput, and monthly subscription tiers. This is a "nice to have" as the current anchor client is on a flat-fee annual contract, but it is necessary for future scaling.

**Technical Implementation (Proposed):**
Integration with a billing engine (e.g., Stripe or a custom internal ledger). The system will track "Active Device Months" (ADM) as the primary billing metric.
- **Metering:** A Celery beat task will aggregate daily usage from the `Telemetry` collection.
- **Invoicing:** Automated PDF generation and emailing on the 1st of every month.

**Reason for Block:**
Budget approval for the necessary billing middleware license is currently pending executive sign-off.

**Success Criteria:**
- Accurate calculation of monthly usage across 10,000+ devices.
- Automated suspension of API access for accounts with overdue payments.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1` and require a Bearer Token.

### 4.1 `GET /devices`
**Description:** Retrieve a list of all registered IoT devices.
- **Request:** `GET /api/v1/devices?status=active&limit=50`
- **Response:** `200 OK`
- **Body:**
```json
[
  {
    "id": "dev_8821",
    "name": "North-Field-Sensor-01",
    "status": "active",
    "last_seen": "2023-10-20T14:22:01Z"
  }
]
```

### 4.2 `POST /devices/{id}/config`
**Description:** Update configuration for a specific device.
- **Request:** `POST /api/v1/devices/dev_8821/config`
- **Body:**
```json
{
  "sampling_rate": 300,
  "thresholds": { "moisture": 20.5 },
  "sync_interval": "1h"
}
```
- **Response:** `202 Accepted` (Processing via background sync)

### 4.3 `GET /telemetry/{device_id}`
**Description:** Fetch time-series data for a device.
- **Request:** `GET /api/v1/telemetry/dev_8821?start=2023-10-01&end=2023-10-24`
- **Response:** `200 OK`
- **Body:**
```json
{
  "device_id": "dev_8821",
  "data": [
    {"timestamp": "2023-10-01T00:00Z", "value": 22.1, "metric": "temp"},
    {"timestamp": "2023-10-01T01:00Z", "value": 21.8, "metric": "temp"}
  ]
}
```

### 4.4 `POST /webhooks/register`
**Description:** Create a new webhook integration.
- **Request:** `POST /api/v1/webhooks/register`
- **Body:**
```json
{
  "event": "threshold_exceeded",
  "target_url": "https://client-erp.com/api/alerts",
  "secret": "shhh_secret_key"
}
```
- **Response:** `201 Created`

### 4.5 `GET /collaboration/session/{session_id}`
**Description:** Get the current state of a shared editing session.
- **Request:** `GET /api/v1/collaboration/session/sess_992`
- **Response:** `200 OK`
- **Body:**
```json
{
  "session_id": "sess_992",
  "active_users": ["user_1", "user_4"],
  "document_state": { "field_a": "value_x" }
}
```

### 4.6 `PATCH /collaboration/session/{session_id}/update`
**Description:** Submit a CRDT delta update.
- **Request:** `PATCH /api/v1/collaboration/session/sess_992/update`
- **Body:**
```json
{
  "user_id": "user_1",
  "delta": { "field_a": "value_y", "timestamp": 1698154000 }
}
```
- **Response:** `200 OK`

### 4.7 `GET /billing/usage`
**Description:** Retrieve current month's usage metrics.
- **Request:** `GET /api/v1/billing/usage`
- **Response:** `200 OK`
- **Body:**
```json
{
  "month": "October",
  "total_devices": 1200,
  "data_consumed_gb": 45.2,
  "estimated_cost": 1200.00
}
```

### 4.8 `POST /sandbox/simulate-device`
**Description:** Trigger a simulated device event in the sandbox.
- **Request:** `POST /api/v1/sandbox/simulate-device`
- **Body:**
```json
{
  "device_id": "sim_01",
  "event_type": "critical_failure",
  "value": 999
}
```
- **Response:** `200 OK`

---

## 5. DATABASE SCHEMA

Gantry uses MongoDB, but for architectural clarity and the purpose of managing the 30% "raw SQL" performance debt, we treat the collections as structured entities.

### 5.1 Entities and Relationships

| Table/Collection | Description | Key Fields | Relationship |
| :--- | :--- | :--- | :--- |
| **Organizations** | Top-level client entities | `org_id` (PK), `name`, `billing_tier`, `iso_cert_status` | 1:N with Users |
| **Users** | System access accounts | `user_id` (PK), `org_id` (FK), `email`, `role` | N:1 with Organizations |
| **Devices** | Physical IoT hardware | `device_id` (PK), `org_id` (FK), `model_id` (FK), `status` | N:1 with Organizations |
| **DeviceModels** | Hardware specifications | `model_id` (PK), `firmware_version`, `manufacturer` | 1:N with Devices |
| **Telemetry** | Time-series sensor data | `entry_id` (PK), `device_id` (FK), `timestamp`, `value`, `metric_type` | N:1 with Devices |
| **Configs** | Device settings snapshots | `config_id` (PK), `device_id` (FK), `payload` (JSON), `version` | 1:N with Devices |
| **Webhooks** | Third-party integration rules | `hook_id` (PK), `org_id` (FK), `target_url`, `event_type` | N:1 with Organizations |
| **WebhookLogs** | History of webhook attempts | `log_id` (PK), `hook_id` (FK), `status_code`, `request_body` | N:1 with Webhooks |
| **CollabSessions** | Real-time edit sessions | `session_id` (PK), `device_id` (FK), `created_at` | 1:1 with Devices |
| **SyncLogs** | Offline-sync audit trail | `sync_id` (PK), `device_id` (FK), `last_seq_id`, `sync_status` | N:1 with Devices |

### 5.2 Performance Note (The "Raw SQL" Debt)
Approximately 30% of the `Telemetry` and `SyncLogs` queries bypass the Mongo-ODM to use raw aggregation pipelines or targeted SQL-like queries via a middleware layer for performance reasons. This creates a high risk during schema migrations, as these queries are not tracked by the ORM's migration scripts.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry employs three distinct environments to ensure the stability of the production network.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature experimentation and unit testing.
- **Host:** Local Docker Compose on engineer machines.
- **Database:** Ephemeral MongoDB instance.
- **CI/CD:** Triggered on every commit to a feature branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Integration testing and "Release Train" validation.
- **Host:** Private Cloud (K8s Cluster).
- **Database:** Persistent MongoDB cluster mirroring production data (anonymized).
- **CI/CD:** Automated deployment every Tuesday.

#### 6.1.3 Production (Prod)
- **Purpose:** Live enterprise client operations.
- **Host:** Self-hosted, ISO 27001 certified data center.
- **Database:** High-availability MongoDB Replica Set across three availability zones.
- **CI/CD:** Thursday 02:00 UTC Release Train.

### 6.2 Infrastructure Requirements
- **Isolation:** Virtual Private Cloud (VPC) with strict ingress/egress rules.
- **Encryption:** All data at rest encrypted via AES-256. TLS 1.3 for all data in transit.
- **Backups:** Daily snapshots of MongoDB with a 30-day retention policy; tested weekly.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Pure business logic in the Domain layer.
- **Tooling:** `pytest`.
- **Requirement:** 80% code coverage minimum for any new feature to be merged into the release train.
- **Mocking:** Use of `unittest.mock` to isolate ports from adapters.

### 7.2 Integration Testing
- **Scope:** Interaction between the FastAPI gateway and MongoDB/Celery.
- **Tooling:** `TestClient` (FastAPI) and Dockerized services.
- **Focus:** Validating that the "Ports and Adapters" are correctly wired. Testing the "Offline-First" sync sequence from local SQLite $\rightarrow$ FastAPI $\rightarrow$ MongoDB.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Complete user flows (e.g., "Create Device $\rightarrow$ Set Threshold $\rightarrow$ Trigger Webhook").
- **Tooling:** `Playwright` for the frontend; `Postman/Newman` for API suites.
- **Frequency:** Performed on the Staging environment every Wednesday before the release train departure.

### 7.4 Quality Assurance (QA) Process
Javier Kim (QA Lead) oversees the final "Go/No-Go" decision for the release train. No feature is promoted to production unless it has a signed-off test report covering the "Happy Path" and "Edge Case" scenarios.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect leaving in 3 months | High | Critical | Develop a "Fallback Architecture" document; prioritize knowledge transfer sessions between architect and Ibrahim Costa. |
| **R-02** | Partner API is undocumented/buggy | High | Medium | Dedicated "Integration Wrapper" layer to normalize data; maintain an internal Wiki of known bugs and workarounds. |
| **R-03** | Budget for critical tool pending | Medium | High | Identify open-source alternatives (though potentially less stable) as a temporary stop-gap. |
| **R-04** | Raw SQL debt causes migration failure | Medium | High | Implement a "Query Audit" where all raw SQL is documented in a central registry; perform manual verification during migrations. |
| **R-05** | ISO 27001 Audit failure | Low | Critical | Monthly internal "pre-audits" and strict adherence to the documented security framework. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project halt or loss of $2M contract.
- **High:** Significant delay in milestones or stability issues.
- **Medium:** Feature degradation or delayed "nice-to-have" items.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Now – Jan 2026):** Focus on the core IoT network, offline-first stability, and the "critical" collaborative editing feature.
- **Phase 2: Integration (Jan 2026 – June 2026):** Implementation of the Webhook framework and API sandbox.
- **Phase 3: Validation (June 2026 – Aug 2026):** Alpha testing, stakeholder demos, and ISO 27001 audit.
- **Phase 4: Stability (Aug 2026 – April 2026):** Post-launch monitoring and stabilization.

### 9.2 Critical Milestones
- **Internal Alpha Release:** Target **2026-06-15**. 
  - *Dependencies:* Collaborative editing must be 100% stable.
- **Stakeholder Demo and Sign-off:** Target **2026-08-15**.
  - *Dependencies:* Alpha release stability and successful demo of the API sandbox.
- **Post-launch Stability Confirmed:** Target **2026-04-15** (Following the 2026 launch window).
  - *Dependencies:* 90 days of 99.9% uptime achieved.

---

## 10. MEETING NOTES

### 10.1 Meeting: Sprint 4 Sync (2023-11-02)
- **Attendees:** Aaliya, Ibrahim, Javier, Yara.
- **Notes:**
  - Collab editing still buggy.
  - Yara struggling with MongoDB aggregation.
  - Ibrahim says raw SQL is the only way for the telemetry report.
  - Aaliya reminded everyone: No hotfixes. Wait for Thursday.

### 10.2 Meeting: Architecture Review (2023-11-15)
- **Attendees:** Aaliya, Ibrahim.
- **Notes:**
  - Architect leaving in 3 months.
  - Need "Plan B" for the data layer.
  - Ibrahim thinks the hexagonal approach helps here.
  - Agreed: Start documenting the "Fallback Architecture" now.

### 10.3 Meeting: Budget & Tools (2023-12-01)
- **Attendees:** Aaliya, Finance Rep.
- **Notes:**
  - Billing tool purchase still pending.
  - Finance wants a more detailed ROI for the tool.
  - Aaliya flagged it as a blocker for Feature 2.
  - No decision yet.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | Salaries for 12-person cross-functional team over project duration. |
| **Infrastructure** | 20% | $600,000 | Self-hosted servers, ISO 27001 certified DC leases, Redis/Mongo licenses. |
| **Tools & Software** | 10% | $300,000 | Development tools, Security scanners, Billing middleware (Pending). |
| **Contingency** | 5% | $150,000 | Emergency hardware replacement and unplanned consultant costs. |

---

## 12. APPENDICES

### Appendix A: CRDT Logic for Collaborative Editing
To resolve conflicts in a distributed agricultural network, Gantry uses a **State-based CRDT**. 
Each configuration field is stored as a tuple: `(value, timestamp, node_id)`.
When merging two states:
1. Compare timestamps.
2. The largest timestamp wins.
3. If timestamps are identical, the node with the lowest alphanumeric `node_id` wins.
This ensures that all nodes eventually converge to the same state without requiring a central coordinator, supporting the offline-first requirement.

### Appendix B: ISO 27001 Compliance Checklist
To pass the external audit on the first attempt, the following controls must be verified:
- **Access Control:** All team members must use MFA for server access.
- **Log Management:** All `POST/PATCH/DELETE` requests must be logged to a read-only audit trail.
- **Encryption:** Database disks must be encrypted; no plaintext keys in the `docker-compose.yml`.
- **Vulnerability Scanning:** Weekly automated scans of the Docker images for CVEs.
- **Network Segregation:** Production environment must be logically separated from Dev/Stage.