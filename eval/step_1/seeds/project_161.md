# PROJECT SPECIFICATION: PROJECT FORGE
**Document Version:** 1.0.4-RELEASE  
**Date:** October 24, 2025  
**Status:** Active/Baseline  
**Classification:** Confidential - Verdant Labs Internal  
**Project Lead:** Niko Gupta (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Forge is a mission-critical embedded systems firmware management and productivity tool developed by Verdant Labs for the government services sector. Originally conceived as a rapid prototype during a company hackathon, Forge has evolved organically into a vital piece of internal infrastructure. Despite its humble beginnings, it currently supports 500 daily active users (DAU) who rely on the system to orchestrate firmware deployments, track hardware revisions, and automate compliance auditing across distributed government nodes.

The core objective of Forge is to transition from a "hackathon project" into a hardened, enterprise-grade platform capable of scaling to 10,000 monthly active users (MAU). This transition requires a rigorous shift toward formalized architecture, stringent security compliance (GDPR/CCPA), and the implementation of a high-reliability workflow automation engine.

### 1.2 Business Justification
In the government services industry, the cost of firmware failure is not measured merely in downtime, but in systemic risk. Currently, the process of updating embedded systems across diverse jurisdictions is plagued by manual intervention, fragmented spreadsheets, and inconsistent auditing. Forge centralizes this orchestration. By providing a single pane of glass for firmware lifecycle management, Verdant Labs eliminates the "human-in-the-loop" bottleneck that currently delays deployment cycles.

The primary business driver is the reduction of operational overhead. Current manual processing of firmware updates and compliance reporting takes an average of 12 man-hours per deployment cycle per node. Forge aims to reduce this by 50%, effectively reclaiming thousands of engineering hours annually.

### 1.3 ROI Projection
With a lean budget of $150,000, the Return on Investment (ROI) is calculated based on labor cost savings and risk mitigation.

*   **Labor Savings:** Assuming an average engineering cost of $85/hr, a 50% reduction in manual processing for 500 users across 100 nodes results in an estimated annual saving of $1.2M in operational expenditure (OpEx).
*   **Risk Mitigation:** By implementing the CQRS event-sourcing model, Verdant Labs avoids the catastrophic costs associated with audit failure in government contracts, where non-compliance penalties can exceed $250,000 per incident.
*   **Scalability:** The move to Fly.io and a distributed Elixir/Phoenix architecture allows the system to scale to 10,000 MAU without a linear increase in infrastructure costs, projecting a cost-per-user decrease of 40% over 18 months.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Forge utilizes a high-concurrency stack designed for real-time updates and fault tolerance:
*   **Language/Framework:** Elixir with the Phoenix framework. Elixir's BEAM VM is critical for handling the thousands of concurrent WebSocket connections required for real-time firmware monitoring.
*   **Frontend:** Phoenix LiveView. This allows the team to maintain a rich, reactive UI without the overhead of a separate JavaScript framework, keeping the team lean.
*   **Database:** PostgreSQL 15. Used for persistent state and relational data.
*   **Infrastructure:** Fly.io. Chosen for its ability to deploy globally, ensuring data residency in the EU to satisfy GDPR requirements.
*   **Architectural Pattern:** Command Query Responsibility Segregation (CQRS) with Event Sourcing. 

### 2.2 Event Sourcing and CQRS
Because Forge operates in a government context, a standard CRUD (Create, Read, Update, Delete) model is insufficient. Every change to a firmware configuration must be immutable and auditable. 

In Forge, "Commands" (e.g., `UpdateFirmwareVersion`) are validated and then appended to an Event Store as a sequence of events (`FirmwareVersionUpdated`). "Queries" are served by projected read-models in PostgreSQL. This ensures that we can reconstruct the state of any embedded device at any point in time.

### 2.3 Architectural Diagram (ASCII Representation)

```text
[ USER BROWSER ] <---(WebSockets/HTTP)---> [ FLY.IO EDGE ]
                                               |
                                               v
                                     [ PHOENIX LIVEVIEW APP ]
                                     /          |           \
          (Commands)            (Events)     (Queries)    (External)
               |                    |           |             |
               v                    v           v             v
    [ COMMAND HANDLERS ] ----> [ EVENT STORE ] <--- [ READ MODELS (Postgres) ]
               |                    |           |             |
               +--------------------+-----------+             |
                                    |                           |
                                    v                           v
                         [ EVENT PROJECTORS ] <--- [ WEBHOOK ENGINE ] <--- [ 3rd PARTY APIs ]
                                    |
                                    +---> [ FIRMWARE NODES (Embedded) ]
```

### 2.4 Data Residency and Security
To comply with GDPR and CCPA, the architecture implements "Regional Sharding." While the control plane is global, the actual firmware binaries and user-identifiable data are pinned to the `ams3` (Amsterdam) and `fra` (Frankfurt) Fly.io regions. This ensures that EU data never leaves the EU jurisdiction.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine (Priority: Critical)
**Status:** In Design | **Launch Blocker:** Yes

The Workflow Automation Engine is the heart of Forge. It allows administrators to define complex logic for firmware deployment (e.g., "If Node A updates successfully AND Node B is reachable, then trigger update on Node C").

**Functional Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface allowing users to chain "Triggers," "Conditions," and "Actions."
- **Trigger Types:** Webhook arrivals, scheduled cron timers, or state changes in a device (e.g., `battery_level < 20%`).
- **Condition Logic:** Boolean algebra (AND/OR/NOT) applied to device metadata.
- **Action Execution:** API calls to embedded devices, notification alerts via Slack/Email, or triggering secondary workflows.

**Technical Implementation:**
The engine will be implemented as a state machine using Elixir GenServer processes. Each active workflow instance is a process that tracks its current state. The "Visual Rule Builder" will generate a JSON representation of the logic, which is then parsed into a series of function calls.

**Failure Handling:**
Workflows must support "Retry Policies" (Exponential Backoff) and "Dead Letter Queues" (DLQ) for failed actions. If a workflow fails three times, it must trigger a `WORKFLOW_CRITICAL_FAILURE` event for manual intervention.

### 3.2 Real-time Collaborative Editing (Priority: High)
**Status:** In Review

To allow multiple engineers to configure firmware manifests simultaneously, Forge implements a collaborative editor.

**Functional Requirements:**
- **Multi-user Presence:** Users can see who else is currently editing a manifest via colored cursors.
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to prevent "last-write-wins" data loss.
- **Atomic Saves:** Changes are streamed in real-time but committed to the Event Store in atomic batches.

**Technical Implementation:**
Using Phoenix Channels, the system will broadcast diffs of the document. To minimize latency, the "Source of Truth" resides in a temporary Redis cache before being projected into the PostgreSQL read-model. The conflict resolution logic is handled server-side to ensure that the final state is consistent across all clients.

**User Experience:**
The UI must indicate "Saving..." and "Synced" states. If a network partition occurs, the system should enter "Offline Mode" and attempt to merge changes upon reconnection.

### 3.3 Webhook Integration Framework (Priority: Medium)
**Status:** Complete

This framework allows Forge to communicate with third-party monitoring tools and CI/CD pipelines.

**Functional Requirements:**
- **Payload Normalization:** Ability to map incoming JSON payloads from various vendors into the Forge internal event format.
- **Secret Validation:** Support for HMAC signatures to verify that incoming webhooks are from trusted sources.
- **Outgoing Webhooks:** Ability to notify external systems when a firmware update is completed.

**Technical Implementation:**
The framework utilizes a dynamic routing table in PostgreSQL. When a request hits `/api/v1/webhooks/:provider_id`, the system lookups the transformation logic associated with that `provider_id`.

**Verification:**
The framework has been tested against 15 different third-party API formats and supports a maximum throughput of 1,000 requests per second per region.

### 3.4 Customizable Dashboard (Priority: Low)
**Status:** In Design

A personalized landing page for users to monitor their specific fleet of devices.

**Functional Requirements:**
- **Widget Library:** Pre-built widgets for "Device Health," "Deployment Progress," "Error Logs," and "Resource Utilization."
- **Drag-and-Drop Layout:** Users can resize and reposition widgets; the layout is saved to their user profile.
- **Dynamic Filtering:** Widgets should respond to global filters (e.g., "Filter by Region: EU-West").

**Technical Implementation:**
The layout is stored as a JSON blob in the `user_preferences` table. LiveView handles the real-time updates of the widget data via `pubsub` broadcasts.

### 3.5 Data Import/Export (Priority: Low)
**Status:** Blocked

A utility to migrate device lists and firmware histories from legacy CSV/XML systems.

**Functional Requirements:**
- **Format Auto-Detection:** The system should analyze the first 10 lines of an uploaded file to determine if it is CSV, JSON, or XML.
- **Mapping Interface:** A UI allowing users to map legacy column headers (e.g., "S/N") to Forge fields (e.g., `serial_number`).
- **Bulk Validation:** A pre-import check that identifies errors (e.g., duplicate IDs) before any data is committed to the database.

**Blocking Issue:**
Current blockage is due to a lack of a standardized schema for the legacy government files, which vary by department. Implementation is paused until the "Mapping Interface" design is approved.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include an `Authorization: Bearer <token>` header.

### 4.1 Device Management

**GET `/devices`**
- **Description:** Retrieve a list of all embedded devices.
- **Query Params:** `status` (online/offline), `region` (EU/US).
- **Response:** `200 OK`
- **Body:** `[{"id": "dev_123", "version": "1.0.2", "status": "online"}, ...]`

**PATCH `/devices/:id/firmware`**
- **Description:** Trigger a firmware update for a specific device.
- **Request Body:** `{"version": "1.0.3", "force": false}`
- **Response:** `202 Accepted`
- **Body:** `{"job_id": "job_abc", "estimated_completion": "2026-03-16T12:00:00Z"}`

### 4.2 Workflow Engine

**POST `/workflows`**
- **Description:** Create a new automation rule.
- **Request Body:** `{"name": "Auto-Rollback", "rules": [...], "trigger": "failure_detected"}`
- **Response:** `201 Created`
- **Body:** `{"id": "wf_99", "status": "inactive"}`

**DELETE `/workflows/:id`**
- **Description:** Remove a workflow.
- **Response:** `204 No Content`

### 4.3 Webhooks & Integration

**POST `/webhooks/receive`**
- **Description:** Entry point for third-party tool notifications.
- **Request Body:** Dynamic JSON payload.
- **Response:** `200 OK` (Acknowledged)

**GET `/webhooks/logs`**
- **Description:** Audit log of all incoming/outgoing webhook traffic.
- **Response:** `200 OK`
- **Body:** `[{"timestamp": "...", "provider": "GitHub", "status": "success"}]`

### 4.4 System & Audit

**GET `/audit/events`**
- **Description:** Fetch the event stream for a specific resource (CQRS Event Store).
- **Query Params:** `resource_id`, `since_date`.
- **Response:** `200 OK`
- **Body:** `[{"event_id": "ev_1", "type": "VERSION_CHANGE", "payload": {...}}]`

**GET `/system/health`**
- **Description:** Check system status and database connectivity.
- **Response:** `200 OK`
- **Body:** `{"status": "healthy", "db_latency": "12ms", "region": "ams3"}`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15. Due to the CQRS architecture, we distinguish between the **Event Store** (Append-only) and **Read Models** (Relational).

### 5.1 Event Store (The Source of Truth)
1.  **`events`**
    *   `id` (UUID, PK): Unique event identifier.
    *   `aggregate_id` (UUID, Indexed): The ID of the device or workflow this event belongs to.
    *   `event_type` (String): e.g., "FIRMWARE_UPDATED", "USER_LOGIN".
    *   `payload` (JSONB): The actual data change.
    *   `created_at` (Timestamp): Exact time of occurrence.
    *   `version` (Integer): Sequential version number for the aggregate.

### 5.2 Read Models (Projected State)
2.  **`users`**
    *   `id` (UUID, PK)
    *   `email` (String, Unique)
    *   `password_hash` (String)
    *   `role` (Enum: Admin, Operator, Auditor)
    *   `region` (String): User's home jurisdiction (EU/US).

3.  **`devices`**
    *   `id` (UUID, PK)
    *   `serial_number` (String, Unique)
    *   `current_version` (String)
    *   `status` (Enum: Online, Offline, Updating, Error)
    *   `last_seen_at` (Timestamp)
    *   `region_id` (FK -> `regions`)

4.  **`regions`**
    *   `id` (UUID, PK)
    *   `name` (String): e.g., "EU-Central-1"
    *   `data_residency_compliant` (Boolean)

5.  **`workflows`**
    *   `id` (UUID, PK)
    *   `name` (String)
    *   `definition` (JSONB): The rule-builder logic.
    *   `is_active` (Boolean)
    *   `created_by` (FK -> `users`)

6.  **`workflow_executions`**
    *   `id` (UUID, PK)
    *   `workflow_id` (FK -> `workflows`)
    *   `status` (Enum: Pending, Running, Completed, Failed)
    *   `started_at` (Timestamp)
    *   `finished_at` (Timestamp)

7.  **`firmware_blobs`**
    *   `id` (UUID, PK)
    *   `version` (String, Unique)
    *   `checksum` (String): SHA-256 hash for integrity.
    *   `storage_path` (String): Path in S3/Fly.io volume.
    *   `created_at` (Timestamp)

8.  **`webhook_configs`**
    *   `id` (UUID, PK)
    *   `provider` (String)
    *   `target_url` (String)
    *   `secret_token` (String)
    *   `event_filters` (JSONB)

9.  **`user_preferences`**
    *   `user_id` (FK -> `users`, PK)
    *   `dashboard_layout` (JSONB)
    *   `notification_settings` (JSONB)

10. **`audit_logs`**
    *   `id` (UUID, PK)
    *   `user_id` (FK -> `users`)
    *   `action` (String)
    *   `ip_address` (String)
    *   `timestamp` (Timestamp)

### 5.2 Relationships
- `users` (1) $\rightarrow$ `user_preferences` (1)
- `users` (1) $\rightarrow$ `workflows` (N)
- `regions` (1) $\rightarrow$ `devices` (N)
- `workflows` (1) $\rightarrow$ `workflow_executions` (N)
- `events` (N) $\rightarrow$ `devices` (1 via `aggregate_id`)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Forge utilizes three distinct environments to ensure stability before government-facing releases.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and local testing.
- **Infrastructure:** Local Dockerized PostgreSQL and Elixir nodes.
- **Deployment:** Continuous integration (CI) on every push to `feature/*` branches.
- **Data:** Mock data; no real government node IDs.

#### 6.1.2 Staging (QA Gate)
- **Purpose:** Final validation, security scanning, and UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of production on Fly.io (`staging.forge.verdant.io`).
- **Deployment:** Triggered after successful merge to `develop`.
- **The QA Gate:** A mandatory manual sign-off by Esme Park (Support Engineer) and Wren Costa (Security Engineer) is required. This involves a 2-day turnaround where the build is smoke-tested against a subset of real hardware.

#### 6.1.3 Production (Prod)
- **Purpose:** Live service for 500+ users.
- **Infrastructure:** Multi-region Fly.io cluster with auto-scaling.
- **Deployment:** Blue-Green deployment strategy to ensure zero downtime.
- **Data residency:** Strict routing rules ensure EU users only hit EU-based PostgreSQL replicas.

### 6.2 Deployment Pipeline
1.  **Push:** Engineer pushes to GitHub.
2.  **CI:** GitHub Actions runs `mix test` and `creusot` (static analysis).
3.  **Staging:** If tests pass, the build is deployed to Staging.
4.  **Manual Gate:** QA team validates features.
5.  **Production:** Upon approval, the image is promoted to Production.

---

## 7. TESTING STRATEGY

Given the critical nature of embedded firmware, a "Swiss Cheese" model of testing is employed—multiple layers of defense to catch bugs.

### 7.1 Unit Testing
- **Focus:** Individual functions, pure logic, and state transitions in GenServers.
- **Tooling:** `ExUnit`.
- **Requirement:** 80% code coverage. All "Command" handlers must have 100% coverage.
- **Example:** Testing that the `VersionValidator` correctly rejects a downgrade from v1.2 to v1.1 unless the `force` flag is true.

### 7.2 Integration Testing
- **Focus:** Interaction between the Phoenix app and the PostgreSQL database, as well as external API calls.
- **Tooling:** `Wallaby` for browser-based flow testing.
- **Critical Path:** Validating that an event written to the `events` table is correctly projected into the `devices` read-model within < 500ms.

### 7.3 End-to-End (E2E) Testing
- **Focus:** The entire lifecycle from "Admin triggers update" $\rightarrow$ "Webhook received" $\rightarrow$ "Device updated."
- **Hardware-in-the-Loop (HIL):** We maintain a "Device Farm" of 20 physical embedded boards in the office. E2E tests trigger real firmware flashes on these boards.
- **Frequency:** Run once per day (Nightly build).

### 7.4 Security Testing
- **Focus:** OWASP Top 10, GDPR data leakage, and RBAC (Role-Based Access Control) bypasses.
- **Tooling:** Automated scans via `Snyk` and manual penetration testing by Wren Costa.
- **Requirement:** Zero "High" or "Critical" vulnerabilities allowed in the Production build.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Integration partner's API is undocumented and buggy. | High | High | Negotiate timeline extension with stakeholders; implement a "shim" layer to sanitize buggy API responses. |
| **R2** | Scope creep from stakeholders adding 'small' features. | High | Medium | Strict adherence to the priority list. De-scope low-priority features (e.g., Dashboard) if critical blockers (Workflow Engine) slide. |
| **R3** | Budget exhaustion due to unexpected cloud costs. | Medium | High | Use Fly.io resource limits and alerts. Every $100 overage requires Niko Gupta's approval. |
| **R4** | Data residency violation (GDPR). | Low | Critical | Mandatory region-pinning in Fly.io config; quarterly audits by Wren Costa. |
| **R5** | Database corruption due to raw SQL usage. | Medium | High | Prioritize a "SQL Cleanup" sprint to move the 30% raw SQL queries back into Ecto (the ORM). |

### 8.1 Probability/Impact Matrix
- **Critical:** (High Prob / High Impact) $\rightarrow$ Immediate action required.
- **High:** (High Prob / Med Impact) or (Low Prob / High Impact) $\rightarrow$ Active monitoring.
- **Medium:** (Med Prob / Med Impact) $\rightarrow$ Planned mitigation.
- **Low:** (Low Prob / Low Impact) $\rightarrow$ Accept risk.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases and Dependencies

**Phase 1: Hardening (Now $\rightarrow$ March 2026)**
- Focus: Security and Stability.
- Key Dependency: Completion of the Security Audit.
- **Milestone 1: Security audit passed (2026-03-15).**

**Phase 2: Core Logic (March $\rightarrow$ May 2026)**
- Focus: Workflow Automation Engine and CQRS refinement.
- Key Dependency: Finalization of the Visual Rule Builder design.
- **Milestone 2: Architecture review complete (2026-05-15).**

**Phase 3: Validation (May $\rightarrow$ July 2026)**
- Focus: Beta testing and Performance tuning.
- Key Dependency: Successful deployment of the Workflow Engine.
- **Milestone 3: External beta with 10 pilot users (2026-07-15).**

### 9.2 Gantt Chart Description
- **Month 1-3:** Security remediation $\rightarrow$ Audit $\rightarrow$ Sign-off.
- **Month 4-6:** Workflow Engine Design $\rightarrow$ Implementation $\rightarrow$ Integration Tests $\rightarrow$ Arch Review.
- **Month 7-9:** Collaborative Editing Polish $\rightarrow$ Beta Recruitment $\rightarrow$ Beta Launch $\rightarrow$ Feedback Loop.

---

## 10. MEETING NOTES

### Meeting 1: Budget Crisis & Tooling
**Date:** 2025-11-12 | **Attendees:** Niko, Wren, Esme
- Budget tight.
- Need the "Firmware-Verify" tool ($\$4,500$).
- Approval pending from Finance.
- Niko to poke CFO again.
- Esme says without it, manual QA takes 2x longer.

### Meeting 2: The "Raw SQL" Problem
**Date:** 2025-12-05 | **Attendees:** Niko, Anders, Wren
- 30% of queries bypassing Ecto.
- Performance was the reason.
- Now migrations are breaking things.
- Plan: Dedicated "Technical Debt" sprint in Feb.
- Anders worried about the `devices` table lock during migration.

### Meeting 3: Scope Creep Discussion
**Date:** 2026-01-20 | **Attendees:** Niko, Stakeholders
- Stakeholders want "Custom Email Templates" for alerts.
- Niko said no.
- Priority is Workflow Engine.
- Agreed: Email templates move to "Post-Launch" bucket.
- Stakeholders unhappy but accept the 2026-07-15 date.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $\$150,000$ (Shoestring)

| Category | Allocated | Actual/Projected | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $\$90,000$ | $\$90,000$ | Distributed team (mostly internal labor costs/stipends). |
| **Infrastructure** | $\$30,000$ | $\$22,000$ | Fly.io hosting, PostgreSQL managed instances, S3 buckets. |
| **Tools/Licenses** | $\$15,000$ | $\$12,000$ | Security scanners, "Firmware-Verify" tool (pending). |
| **Contingency** | $\$15,000$ | $\$5,000$ | Emergency patches, unexpected API costs. |
| **Total** | **$\$150,000$** | **$\$129,000$** | Remaining $\approx \$21k$ for final beta phase. |

*Note: Every single expenditure over $\$500$ requires a written justification and Niko Gupta's signature.*

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (CRDTs)
To support real-time collaborative editing, Forge implements a LWW-Element-Set (Last-Write-Wins) CRDT for the firmware manifest. 
- **State:** Each field in the manifest is stored as a tuple: `(value, timestamp)`.
- **Merge Rule:** When two updates conflict, the update with the higher timestamp (UTC) is preserved.
- **Garbage Collection:** To prevent the event store from growing infinitely, "snapshots" are taken every 1,000 events. The snapshot becomes the new baseline, and old events are archived to cold storage.

### Appendix B: GDPR Compliance Mapping
| GDPR Requirement | Forge Implementation |
| :--- | :--- |
| **Right to Erasure** | `DELETE` command in CQRS triggers a "tombstone" event; all PII is scrubbed from read-models. |
| **Data Residency** | Fly.io region-pinning ensures EU data stays in `ams3`/`fra`. |
| **Access Control** | RBAC ensured via Phoenix.Component authentication guards on all `/api/v1` routes. |
| **Auditability** | Immutable event store provides a full history of every data access and modification. |