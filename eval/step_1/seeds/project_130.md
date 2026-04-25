# PROJECT SPECIFICATION: PROJECT UMBRA
**Company:** Coral Reef Solutions  
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/Baseline  
**Classification:** Internal Proprietary  

---

## 1. EXECUTIVE SUMMARY

Project Umbra represents a strategic pivot for Coral Reef Solutions. Historically focused on marine environmental monitoring, the company is now venturing into the aerospace industry—a market characterized by extreme telemetry requirements, high-latency communication environments, and rigorous data integrity standards. Umbra is a greenfield IoT device network designed to manage high-frequency data streams from aerospace components (sensors, actuators, and propulsion monitors) and synchronize this data across distributed ground stations and orbital relays.

The business justification for Umbra is rooted in the inefficiency of current legacy aerospace telemetry systems. Existing solutions are often monolithic, proprietary, and prohibitively expensive to scale. By implementing a modernized, serverless-orchestrated architecture, Coral Reef Solutions aims to capture a market share of the "New Space" economy, providing a flexible, API-driven infrastructure for satellite constellations and unmanned aerial vehicles (UAVs).

The projected Return on Investment (ROI) is based on two primary efficiency drivers. First, the system is engineered to reduce the cost per transaction—defined as the cost to ingest, process, and store one telemetry packet—by 35% compared to industry-standard legacy systems. This is achieved through the use of Heroku’s managed services and a streamlined Ruby on Rails monolith that minimizes overhead. Second, the project aims for a 50% reduction in manual processing time for end-users. By replacing manual data scrubbing and spreadsheet-based analysis with real-time collaborative editing and automated reporting, the operational overhead for aerospace engineers is halved.

Financially, the project operates on a variable, milestone-based funding model. Tranches of capital are released upon the successful completion of predefined milestones (Stakeholder Demo, Performance Benchmarks, and Production Launch). This ensures that the company minimizes financial risk while entering an unfamiliar market. The project is executed by a veteran team of 15 distributed professionals across five countries, leveraging their history of collaboration to mitigate the risks associated with a new industry entry.

---

## 2. TECHNICAL ARCHITECTURE

The architecture of Umbra is designed for "deliberate simplicity." While the aerospace domain is complex, the software layer is kept lean to ensure agility and maintainability.

### 2.1 The Stack
- **Core Framework:** Ruby on Rails 7.1 (Monolith)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons)
- **Platform:** Heroku (PaaS)
- **Compute:** Serverless Functions (AWS Lambda via Heroku Buildpacks)
- **Orchestration:** API Gateway (AWS API Gateway) for routing requests to serverless functions and the Rails monolith.

### 2.2 Architectural Design
The system utilizes a hybrid approach. The Rails monolith handles session management, user authentication, and complex business logic (the "Command Center"). High-throughput IoT data ingestion, however, is offloaded to serverless functions to prevent the monolith from becoming a bottleneck during telemetry spikes.

**ASCII Architecture Diagram:**
```text
[IoT Device Network] 
       |
       v
[AWS API Gateway] <------------------ [Authentication Layer]
       |
       +---> [Serverless Functions] --> [Data Validation/Filtering]
       |                                        |
       |                                        v
       +---> [Rails Monolith] <---------- [MySQL Database]
       |          |                            ^
       |          v                            |
       |    [Collaborative Engine] -------------+
       |          |
       v          v
[Web/Mobile Client] <--- [WebSocket/ActionCable]
```

### 2.3 Data Flow
1. **Ingestion:** IoT devices push telemetry via MQTT or HTTPS to the API Gateway.
2. **Processing:** API Gateway routes the request to a serverless function that performs initial schema validation.
3. **Persistence:** Validated data is written to the MySQL database.
4. **Real-time Update:** The Rails monolith detects the update via a database trigger or event bus and pushes a notification to the collaborative editing interface using ActionCable (WebSockets).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
In the aerospace context, multiple engineers must analyze telemetry data and annotate device configurations simultaneously. This feature provides a shared workspace where changes made by one user are reflected across all connected clients in real-time. Given the distributed nature of the team and the criticality of the data, "last-write-wins" is insufficient.

**Technical Implementation:**
Umbra utilizes Operational Transformation (OT) and a Conflict-free Replicated Data Type (CRDT) approach to ensure consistency. The system implements a centralized authority model via the Rails monolith. When a user edits a telemetry annotation, the change is sent as a "delta" through a WebSocket connection (ActionCable). The server sequences these deltas, applies them to the MySQL state, and broadcasts the transformed delta to all other active participants.

**Conflict Resolution Logic:**
If two users attempt to edit the same field (e.g., a sensor threshold value) at the exact same millisecond, the system employs a timestamp-based tie-breaker combined with a versioning vector. Each document has a `version_id`. If a client submits an edit based on `version 10` but the server is already at `version 11`, the server calculates the diff and merges the changes. If the changes overlap on the exact same character or value, the system flags a "soft conflict" and allows the user to choose the preferred value, though the CRDT layer prevents the database from ever reaching an inconsistent state.

### 3.2 Offline-First Mode with Background Sync
**Priority:** High | **Status:** In Review

**Description:**
Aerospace operators often work in "dead zones" (e.g., hangar basements or remote launch sites) where connectivity is intermittent. This feature allows users to continue interacting with the Umbra interface, making configuration changes and adding notes without an active internet connection.

**Technical Implementation:**
The client-side utilizes IndexedDB for local persistence. All API requests are intercepted by a Service Worker. If the network is offline, the request is queued in an "Outbox" within IndexedDB. Once the Service Worker detects a `navigator.onLine` event, it initiates a background synchronization process.

**Sync Logic & Reconciliation:**
The synchronization follows a "Queue-and-Replay" pattern. When connectivity is restored, the client sends the queued operations in chronological order. The server uses an idempotent API design—every request includes a `client_request_id` (UUID). This ensures that if a sync request is sent twice due to a flickering connection, the server only processes it once. The server responds with a `sync_token`, which the client uses to prune its local outbox.

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** Not Started

**Description:**
Stakeholders require periodic snapshots of device health and performance metrics. This feature involves the generation of professional-grade PDF reports (for executives) and raw CSV exports (for data scientists).

**Technical Implementation:**
Generation will be handled by a background worker (Sidekiq) to avoid blocking the main Rails request thread. For PDFs, the system will use `WickedPDF` or `Grover` (Puppeteer-based) to render HTML templates into high-fidelity documents. CSVs will be generated using the native Ruby `CSV` library.

**Scheduling and Delivery:**
The system will implement a `ReportSchedule` table in MySQL, allowing users to define frequency (Daily, Weekly, Monthly). A cron-like scheduler (via `sidekiq-scheduler`) will trigger the generation process. Reports will be uploaded to an S3 bucket, and a signed URL will be emailed to the user via SendGrid. The system must support "Report Templates," allowing users to select which telemetry KPIs are included in their specific PDF.

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low (Nice to Have) | **Status:** In Progress

**Description:**
As the volume of IoT devices grows, finding a specific device or event based on metadata (e.g., "all sensors in the propulsion module with a temperature > 500C and status 'warning'") becomes difficult. This feature provides a Google-like search experience.

**Technical Implementation:**
While MySQL provides basic full-text search, Umbra will implement an inverted index for faster retrieval. The search engine will index device metadata, logs, and user annotations. Faceted filtering will be implemented by aggregating counts of attributes (e.g., Brand: SpaceX (10), Blue Origin (5)) in the sidebar.

**Indexing Strategy:**
The team is currently implementing a "Search Indexer" worker that asynchronously updates the search index whenever a device record is updated in MySQL. This prevents the search functionality from slowing down the primary write operations. The frontend will use a debounced input field to prevent overloading the server with requests on every keystroke.

### 3.5 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** Low (Nice to Have) | **Status:** In Progress

**Description:**
To allow third-party aerospace partners to integrate their own software with Umbra, a public REST API is required. This must be stable, versioned, and provide a safe environment for testing (Sandbox).

**Technical Implementation:**
The API will be developed as a separate namespace within the Rails monolith (`/api/v1/`). Versioning is handled via URL pathing to ensure backward compatibility. The sandbox environment will be a logically isolated partition of the database where users can create "mock" devices and trigger simulated telemetry data without affecting production records.

**Authentication and Rate Limiting:**
The API will use API Keys (hashed in the database) for authentication. Rate limiting will be enforced using the `rack-attack` gem, limiting users to 1,000 requests per hour in the sandbox and 10,000 in production to prevent DDoS attacks and ensure fair resource distribution across the distributed team's infrastructure.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints return JSON. Base URL: `https://api.umbra.coralreef.io`

### 4.1 GET `/api/v1/devices`
**Description:** Retrieve a list of all registered IoT devices.
**Request:** `GET /api/v1/devices?status=active&limit=20`
**Response:** `200 OK`
```json
{
  "devices": [
    { "id": "dev_9921", "name": "Propulsion_S1", "status": "active", "last_ping": "2026-04-01T12:00:00Z" }
  ],
  "pagination": { "total": 150, "offset": 0 }
}
```

### 4.2 POST `/api/v1/telemetry`
**Description:** Ingest data from a device.
**Request:** `POST /api/v1/telemetry`
**Body:**
```json
{
  "device_id": "dev_9921",
  "timestamp": "2026-04-01T12:05:00Z",
  "metrics": { "temp": 450.2, "pressure": 12.1 },
  "checksum": "a1b2c3d4"
}
```
**Response:** `202 Accepted` (Processed asynchronously via serverless function).

### 4.3 PATCH `/api/v1/devices/:id`
**Description:** Update device configuration.
**Request:** `PATCH /api/v1/devices/dev_9921`
**Body:** `{ "sampling_rate": "500ms" }`
**Response:** `200 OK`
```json
{ "id": "dev_9921", "sampling_rate": "500ms", "updated_at": "2026-04-01T12:10:00Z" }
```

### 4.4 GET `/api/v1/reports/:id`
**Description:** Retrieve a generated report PDF link.
**Request:** `GET /api/v1/reports/rep_443`
**Response:** `200 OK`
```json
{ "report_id": "rep_443", "download_url": "https://s3.amazonaws.com/umbra/rep_443.pdf", "expires_at": "2026-04-02T00:00:00Z" }
```

### 4.5 POST `/api/v1/collaboration/session`
**Description:** Initialize a real-time editing session.
**Request:** `POST /api/v1/collaboration/session`
**Body:** `{ "document_id": "doc_123" }`
**Response:** `201 Created`
```json
{ "session_id": "sess_abc", "websocket_url": "wss://umbra.coralreef.io/cable" }
```

### 4.6 GET `/api/v1/search`
**Description:** Faceted search for devices and logs.
**Request:** `GET /api/v1/search?q=propulsion&facet=status:warning`
**Response:** `200 OK`
```json
{
  "results": [{ "id": "dev_9921", "match_score": 0.98 }],
  "facets": { "status": { "active": 100, "warning": 12, "critical": 2 } }
}
```

### 4.7 DELETE `/api/v1/sandbox/reset`
**Description:** Clear all data in the user's sandbox environment.
**Request:** `DELETE /api/v1/sandbox/reset`
**Response:** `204 No Content`

### 4.8 GET `/api/v1/health`
**Description:** System health check for monitoring.
**Request:** `GET /api/v1/health`
**Response:** `200 OK`
```json
{ "status": "healthy", "database": "connected", "redis": "connected", "version": "1.0.4" }
```

---

## 5. DATABASE SCHEMA

The system uses a MySQL 8.0 relational schema. All tables use `BIGINT UNSIGNED` for primary keys and `DATETIME(6)` for high-precision aerospace timestamps.

### 5.1 Table Definitions

1. **`users`**
   - `id` (PK), `email` (unique), `password_digest`, `full_name`, `role` (admin/engineer/viewer), `created_at`, `updated_at`.
2. **`organizations`**
   - `id` (PK), `name`, `billing_tier`, `api_key_hash`, `created_at`.
3. **`devices`**
   - `id` (PK), `org_id` (FK), `serial_number` (unique), `model_name`, `firmware_version`, `status` (enum), `last_ping_at`, `created_at`.
4. **`telemetry_packets`**
   - `id` (PK), `device_id` (FK), `timestamp` (indexed), `payload` (JSONB), `checksum`, `created_at`.
5. **`annotations`**
   - `id` (PK), `packet_id` (FK), `user_id` (FK), `content` (text), `version`, `created_at`.
6. **`collaboration_sessions`**
   - `id` (PK), `document_id`, `started_at`, `ended_at`.
7. **`session_participants`**
   - `id` (PK), `session_id` (FK), `user_id` (FK), `joined_at`.
8. **`report_schedules`**
   - `id` (PK), `org_id` (FK), `frequency` (enum), `recipient_email`, `template_config` (JSON), `next_run_at`.
9. **`generated_reports`**
   - `id` (PK), `schedule_id` (FK), `s3_url`, `generated_at`, `status` (success/fail).
10. **`audit_logs`**
    - `id` (PK), `user_id` (FK), `action` (string), `target_id` (string), `timestamp`, `ip_address`.

### 5.2 Relationships
- `Organizations` has many `Users` and `Devices`.
- `Devices` has many `TelemetryPackets`.
- `TelemetryPackets` has many `Annotations`.
- `Users` has many `Annotations` and `AuditLogs`.
- `ReportSchedules` belongs to `Organizations` and has many `GeneratedReports`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra follows a strict three-tier environment promotion strategy to ensure aerospace-grade stability.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and unit testing.
- **Access:** Full access for the 15-person distributed team.
- **Persistence:** Ephemeral database snapshots; data is wiped weekly.
- **Deployment:** Automatic push from `develop` branch.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation and QA.
- **Access:** Tech Lead (Kira Santos) and designated QA testers.
- **Persistence:** Mirror of production schema with anonymized production data.
- **Deployment:** Manual trigger. This environment hosts the **Manual QA Gate**.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live aerospace telemetry monitoring.
- **Access:** Restricted to Tech Lead and Security Engineer (Jasper Fischer).
- **Persistence:** High-availability MySQL cluster with daily backups.
- **Deployment:** Final sign-off required. 2-day turnaround for any hotfixes.

### 6.2 The Deployment Pipeline
1. **Code Push:** Developer pushes to GitHub.
2. **CI Pipeline:** GitHub Actions runs RuboCop (linting) and RSpec (unit tests).
3. **Dev Deployment:** Automated deployment to Heroku Dev.
4. **Merge to Staging:** After peer review, code is merged to `staging`.
5. **QA Gate:** A mandatory 48-hour window where the team performs manual regression testing.
6. **Production Push:** Following QA sign-off, the build is promoted to Production.

---

## 7. TESTING STRATEGY

Given the "launch blocker" nature of some features, testing is segmented into three rigorous layers.

### 7.1 Unit Testing
- **Tool:** RSpec.
- **Coverage Goal:** 90% for core business logic (e.g., conflict resolution, telemetry validation).
- **Focus:** Testing individual methods in isolation using mocks and stubs. Every serverless function has a corresponding unit test suite to validate input/output mapping.

### 7.2 Integration Testing
- **Tool:** Capybara and FactoryBot.
- **Focus:** Verifying the interaction between the Rails monolith and the MySQL database, and the interaction between API Gateway and serverless functions.
- **Key Scenario:** Testing the "Offline-First" sync by simulating network failure in a controlled integration environment and verifying that the `Outbox` correctly replays requests to the server.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Simulating a complete user journey.
- **Critical Path:** 
  1. User logs in $\rightarrow$ 2. Joins collaborative session $\rightarrow$ 3. Edits a telemetry point $\rightarrow$ 4. Another user sees the change $\rightarrow$ 5. User generates a PDF report.
- **Frequency:** Run on every build in the Staging environment before the manual QA gate.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key architect is leaving in 3 months | High | Critical | **Parallel-Pathing:** Prototype an alternative architectural approach simultaneously to ensure no single-point-of-failure in knowledge. |
| R-02 | Scope creep from stakeholders | High | Medium | **Dedicated Owner:** Assign a specific team member to track all "small" requests and force them through a formal change-request board. |
| R-03 | Medical leave of key member (Current) | Occurred | High | **Resource Redistribution:** Distribute the blocked member's tasks across the remaining 14 members; extend internal deadlines for non-critical features. |
| R-04 | Data latency in aerospace relays | Medium | High | **Optimistic UI:** Implement client-side state updates that assume success, reverting only if the server returns an error. |
| R-05 | Heroku scaling limits | Low | Medium | **Strategic Migration:** Monitor memory usage; if limits are hit, migrate the monolith to AWS EKS while keeping the serverless layer. |

**Impact Matrix:**
- **Critical:** Project halt / Data loss.
- **High:** Milestone delay / Major feature failure.
- **Medium:** Minor feature delay / User inconvenience.
- **Low:** Cosmetic issues.

---

## 9. TIMELINE & PHASES

Project Umbra is tracked via a milestone-based Gantt structure.

### Phase 1: Foundation & Real-time Sync (Current - April 2026)
- **Focus:** Infrastructure setup and Collaborative Editing.
- **Dependencies:** Serverless function orchestration must be stable before telemetry ingestion starts.
- **Target:** **Milestone 1 (2026-04-15) - Stakeholder demo and sign-off.**

### Phase 2: Data Reliability & Performance (April 2026 - June 2026)
- **Focus:** Offline-first mode and telemetry optimization.
- **Dependencies:** Collaborative engine must be bug-free before implementing offline sync to avoid complex merge conflicts.
- **Target:** **Milestone 2 (2026-06-15) - Performance benchmarks met.**

### Phase 3: Reporting & Public Interface (June 2026 - August 2026)
- **Focus:** PDF/CSV generation, Advanced Search, and Customer API.
- **Dependencies:** Production-grade data must be available in MySQL to test reports and search.
- **Target:** **Milestone 3 (2026-08-15) - Production launch.**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Baseline
**Date:** 2023-11-05  
**Attendees:** Kira Santos, Emeka Costa, Jasper Fischer, Noor Nakamura  
**Discussion:**  
The team debated whether to use a microservices architecture given the "aerospace" label. Kira argued that a Rails monolith on Heroku is the fastest path to market and reduces the cognitive load for a distributed team. Jasper raised concerns about security, but it was decided that internal audits are sufficient for the current scope.  
**Decisions:**  
- Stick to Rails monolith + Serverless Functions.  
- No external compliance (SOC2/HIPAA) required for V1.  
**Action Items:**  
- Kira: Set up Heroku organization and initial pipelines. (Owner: Kira)  
- Jasper: Define the internal security audit checklist. (Owner: Jasper)

### Meeting 2: Conflict Resolution Deep Dive
**Date:** 2023-12-12  
**Attendees:** Kira Santos, Emeka Costa, Noor Nakamura  
**Discussion:**  
Noor presented the initial implementation of "last-write-wins" for collaborative editing. Kira rejected this, noting that in aerospace, a telemetry change by a senior engineer must not be blindly overwritten by a junior dev. The team shifted toward CRDTs and Operational Transformation.  
**Decisions:**  
- Implement a version-vector system for all document edits.  
- Use ActionCable for real-time broadcasting.  
**Action Items:**  
- Noor: Research `Yjs` or `Automerge` for CRDT implementation. (Owner: Noor)  
- Emeka: Optimize MySQL table for version history. (Owner: Emeka)

### Meeting 3: Risk Mitigation & Resource Planning
**Date:** 2024-01-20  
**Attendees:** All Team Members  
**Discussion:**  
Discussion regarding the architect's departure in 3 months. The team expressed anxiety about the loss of institutional knowledge. Kira proposed a "parallel-path" strategy: whoever is not the architect will spend 20% of their sprint prototyping an alternative approach to the current design to ensure the project can survive the departure. Discussion also touched upon the current blocker (team member on medical leave).  
**Decisions:**  
- Implement "Parallel-Path" prototyping immediately.  
- Shift non-critical tasks from the member on medical leave to the rest of the team.  
**Action Items:**  
- All: Allocate 1 day per week to alternative prototyping. (Owner: Team)  
- Kira: Adjust sprint velocity for the next 6 weeks. (Owner: Kira)

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on milestones. Total estimated budget for the current cycle: **$1,250,000**.

### 11.1 Personnel (65%)
- **Total:** $812,500  
- **Breakdown:** Salaries for 15 distributed members across 5 countries. This includes the Tech Lead, Data Engineer, Security Engineer, and Junior Developer. Rates vary by region but are averaged across the distributed team.

### 11.2 Infrastructure (15%)
- **Total:** $187,500  
- **Breakdown:**  
  - Heroku Enterprise Plan: $45,000/year  
  - AWS API Gateway & Lambda: $60,000/year (Projected based on telemetry volume)  
  - MySQL Managed Instances: $30,000/year  
  - S3 Storage for Reports: $12,500/year  
  - Other (DNS, CDN): $40,000/year

### 11.3 Tools & Software (10%)
- **Total:** $125,000  
- **Breakdown:**  
  - GitHub Enterprise: $15,000  
  - SendGrid (Email Delivery): $10,000  
  - Monitoring (New Relic/Datadog): $40,000  
  - Collaborative Tools (Slack/Zoom/Jira): $60,000

### 11.4 Contingency Fund (10%)
- **Total:** $125,000  
- **Purpose:** Reserved for emergency hiring to replace the departing architect or to cover unforeseen scaling costs during the production launch.

---

## 12. APPENDICES

### Appendix A: Serverless Function Logic
The serverless functions act as a "Pre-Processor" for the Rails monolith. A typical function follows this logic:
1. **Trigger:** HTTPS Request via API Gateway.
2. **Schema Validation:** Check if `device_id` is a valid UUID and `timestamp` is in ISO8601 format.
3. **Threshold Check:** If a metric (e.g., `temp`) exceeds a critical threshold, the function injects a `priority: high` flag into the payload.
4. **Dispatch:** The validated payload is pushed to a Redis queue, which is then consumed by the Rails monolith for database persistence.
5. **Response:** Returns `202 Accepted` to the device to minimize connection time.

### Appendix B: Data Integrity and Checksums
To ensure that telemetry data is not corrupted during transmission from aerospace devices:
- **Algorithm:** All packets must include a CRC32 checksum.
- **Verification:** The serverless function recalculates the checksum upon receipt. If the calculated checksum does not match the provided `checksum` field, the packet is discarded and a `400 Bad Request` is returned with the error code `ERR_CHECKSUM_MISMATCH`.
- **Recovery:** Devices are programmed to retry failed transmissions every 30 seconds for a maximum of 5 attempts before caching the data locally for "Offline-First" sync.