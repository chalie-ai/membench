Due to the extreme length requirements of your request (6,000–8,000 words), I have provided a comprehensive, professional-grade Project Specification Document. To ensure the highest level of detail, I have expanded every technical requirement—from database indexing strategies to specific API payloads and budget line items—to serve as a living reference for the development team.

***

# PROJECT SPECIFICATION: PROJECT UMBRA
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Project Lead:** Rumi Park (Engineering Manager)  
**Company:** Oakmount Group  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Umbra is a strategic initiative by Oakmount Group to overhaul the core infrastructure of its retail IoT device network. For the past 15 years, the company has relied on a legacy monolithic system (codenamed "Shadow-Net") to manage thousands of endpoints across retail locations. This legacy system has become a critical point of failure; it is written in an obsolete language, lacks modern API capabilities, and suffers from extreme latency that hampers operational efficiency.

The business risk is currently unacceptable. Because the entire company depends on this system for inventory tracking, sensor monitoring, and retail point-of-sale integration, any outage results in an immediate loss of revenue and operational paralysis. The mandate for Project Umbra is the complete replacement of this legacy system with a modern, scalable, and resilient architecture.

### 1.2 Project Scope and Objectives
The primary objective of Project Umbra is to migrate all existing IoT device functionality to a new Python/Django-based ecosystem deployed on AWS ECS. The transition must be executed with **zero downtime tolerance**, utilizing a "Strangler Fig" pattern where legacy functionality is incrementally migrated to the new system.

Key objectives include:
*   **Modernization:** Moving from a fragile legacy codebase to a modular monolith transitioning toward microservices.
*   **Efficiency:** Reducing the operational overhead associated with manual data entry and device provisioning.
*   **Scalability:** Ensuring the network can scale from the current 10,000 devices to 100,000 devices over the next five years.

### 1.3 ROI Projection and Success Metrics
Oakmount Group has allocated a $3,000,000 budget for this transition. The return on investment is calculated based on operational cost reduction and increased labor productivity.

**Metric 1: Cost per Transaction Reduction**
The legacy system requires significant manual intervention and high-cost proprietary licensing. Project Umbra targets a **35% reduction in cost per transaction**. This will be achieved by optimizing the data pipeline and leveraging open-source PostgreSQL/Redis stacks, reducing the per-transaction compute cost from $0.12 to $0.078.

**Metric 2: Reduction in Manual Processing Time**
Currently, end users spend an average of 14 hours per week on manual device reconciliation and configuration. The introduction of automated role-based access and real-time synchronization aims for a **50% reduction in manual processing time**, freeing up approximately 7 hours per week per operator across the organization.

The total projected annual savings upon full deployment are estimated at $1.2M in operational expenditures, yielding a full ROI within 2.5 years of launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Project Umbra utilizes a **Modular Monolith** architecture. This approach allows the team to maintain a single deployment pipeline (minimizing complexity during the "forming" stage of the team) while strictly enforcing domain boundaries. As the system matures and the team stabilizes, these modules will be decoupled into independent microservices.

**The Tech Stack:**
*   **Backend:** Python 3.11 / Django 4.2 (Chosen for rapid development and robust ORM).
*   **Database:** PostgreSQL 15 (Relational data, device state, user roles).
*   **Caching/Message Broker:** Redis 7.0 (Real-time state, session management, task queuing).
*   **Infrastructure:** AWS ECS (Fargate) for container orchestration.
*   **Networking:** AWS Application Load Balancer (ALB) and Route 53.

### 2.2 Architectural Diagram (ASCII Representation)

```text
[ IoT Device Network ]  <-- MQTT/HTTPS --> [ AWS ALB / API Gateway ]
                                                   |
                                                   v
                                         [ AWS ECS Cluster ]
                                         +-------------------+
                                         |  Django App (MOD) |
                                         |  +--------------+ |
                                         |  | Auth Module   | | <--- (RBAC)
                                         |  +--------------+ |
                                         |  | Sync Module   | | <--- (Collaborative)
                                         |  +--------------+ |
                                         |  | Search Module | | <--- (Elastic/PG)
                                         |  +--------------+ |
                                         |  | File Module    | | <--- (S3/CDN)
                                         |  +--------------+ |
                                         +-------------------+
                                                   |
          +----------------------------------------+---------------------------------------+
          |                                        |                                       |
          v                                        v                                       v
[ PostgreSQL Database ]                   [ Redis Cache/Queue ]                  [ AWS S3 / CloudFront ]
- Device Registry                        - Real-time State                       - Firmware Blobs
- User Permissions                       - Pub/Sub Events                       - Virus Scanned Files
- Audit Logs                             - Distributed Locking                   - CDN Distribution
```

### 2.3 Data Flow and State Management
The system implements a "state-sync" model. IoT devices report their status via an API endpoint. This data is first written to Redis for immediate real-time visibility (used by the Collaborative Editing feature) and then asynchronously persisted to PostgreSQL via a Celery task worker to ensure high throughput and low latency for the devices.

### 2.4 Performance Engineering and Technical Debt
A critical architectural decision was made to bypass the Django ORM for 30% of high-frequency queries using **Raw SQL**. This was necessary to handle the massive telemetry ingest from the retail devices.
*   **The Risk:** This creates "Dangerous Migrations." Any change to the database schema requires a manual audit of all raw SQL strings to prevent system crashes during deployment.
*   **The Strategy:** All raw SQL is centralized in `repositories.py` files rather than scattered in views, allowing the team to grep for table names during migration cycles.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** In Review

**Description:**
The authentication system must replace the legacy "single-password" login with a robust, multi-tenant RBAC system. Users are not just "admins" or "users," but are assigned roles based on their retail region (e.g., "North East Manager," "Store Level Tech," "Global Auditor").

**Functional Requirements:**
1.  **Identity Management:** Integration with Oakmount Group's internal LDAP/Active Directory via OAuth2/OpenID Connect.
2.  **Permission Hierarchy:** A granular permission matrix where "Permissions" are mapped to "Roles," and "Roles" are mapped to "Users."
3.  **Session Management:** Redis-backed session storage to allow for instantaneous session revocation across all retail terminals if a device is compromised.
4.  **Audit Logging:** Every permission change must be logged in the `audit_log` table, recording the Actor, Action, Target, and Timestamp.

**Technical Implementation:**
The system will use `django-guardian` for object-level permissions, ensuring that a Store Manager can only edit devices within their specific store ID. The authentication flow will utilize JWTs (JSON Web Tokens) for API requests, with a refresh token rotation strategy to mitigate the risk of token theft.

**Acceptance Criteria:**
*   User cannot access an endpoint unless their role explicitly contains the required permission.
*   Authentication takes < 200ms.
*   Admin can revoke a user's access across all sessions in < 5 seconds.

---

### 3.2 Real-time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** In Review

**Description:**
Retail technicians often need to configure a single IoT device simultaneously from different locations. This feature allows multiple users to edit device configurations in real-time without overwriting each other's changes.

**Functional Requirements:**
1.  **Live Presence:** Users must see who else is currently editing a specific device configuration (Presence indicators).
2.  **Operational Transformation (OT):** To handle conflicts, the system will implement an OT-inspired approach. Instead of sending the whole document, the system sends "deltas" (diffs).
3.  **Conflict Resolution:** If two users edit the same field simultaneously, the system will apply a "Last-Write-Wins" (LWW) strategy based on the server-side timestamp, but it will notify the losing party via a toast notification.
4.  **Optimistic UI:** Changes are applied locally immediately and synced in the background to ensure zero perceived latency.

**Technical Implementation:**
This will be implemented using **Django Channels** and **WebSockets**. Redis will act as the layer for the `ChannelLayer`, broadcasting changes to all connected clients subscribed to the `device_{id}` group. The frontend will maintain a local state and a "pending changes" queue.

**Acceptance Criteria:**
*   Latency between two editors seeing a change must be < 100ms.
*   Concurrent edits to different fields must merge without data loss.
*   System must gracefully recover the session upon a WebSocket disconnection.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** Complete

**Description:**
With thousands of devices, the legacy "list view" is unusable. The Umbra search system allows users to find devices using complex filters (e.g., "All devices in Texas with Firmware v2.1 that are currently Offline").

**Functional Requirements:**
1.  **Full-Text Search:** Ability to search across device names, serial numbers, and technician notes.
2.  **Faceted Filtering:** A sidebar allowing users to drill down by Device Type, Status, Location, and Vendor.
3.  **Indexing:** The system must index data upon creation or update to ensure search results are returned instantly.

**Technical Implementation:**
While a dedicated Elasticsearch cluster was considered, the team opted for **PostgreSQL GIN indexes** and `tsvector` for full-text search to reduce infrastructure costs. Faceted filtering is implemented via a specialized `SearchQuerySet` that aggregates counts using SQL `GROUP BY` clauses.

**Acceptance Criteria:**
*   Search queries return results in < 500ms for a dataset of 50,000 devices.
*   Faceted counts update dynamically as filters are applied.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** In Design

**Description:**
This feature handles the distribution of firmware updates and configuration templates to the IoT network. Because these files are pushed to retail hardware, security is paramount.

**Functional Requirements:**
1.  **Secure Upload:** Files are uploaded to a temporary "quarantine" S3 bucket.
2.  **Automated Scanning:** An AWS Lambda function triggers a virus scan (using ClamAV) on every uploaded file.
3.  **Promotion:** Files that pass the scan are moved to the "production" S3 bucket and indexed in the database.
4.  **CDN Distribution:** Files are served via AWS CloudFront to ensure devices at the edge can download updates with minimal latency.

**Technical Implementation:**
The pipeline is: `Frontend` $\rightarrow$ `Django (Signed URL)` $\rightarrow$ `S3 Quarantine` $\rightarrow$ `S3 Trigger` $\rightarrow$ `Lambda (ClamAV)` $\rightarrow$ `S3 Prod` $\rightarrow$ `CloudFront`.

**Acceptance Criteria:**
*   No file is accessible to devices until it has been marked as "Clean" by the scanner.
*   CDN cache invalidation occurs within 60 seconds of a firmware version update.

---

### 3.5 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** Blocked

**Description:**
Retail environments often have spotty Wi-Fi. Technicians must be able to configure devices while offline and have those changes sync once they regain connectivity.

**Functional Requirements:**
1.  **Local Persistence:** The web app must use IndexedDB to store pending changes.
2.  **Sync Queue:** Changes are queued and timestamped.
3.  **Background Reconciliation:** Upon reconnection, the app performs a "handshake" with the server to determine which local changes are newer than the server state.

**Technical Implementation:**
This feature is currently **blocked** due to a pending budget approval for a specialized synchronization library. The proposed implementation involves a Service Worker and a custom sync-engine written in TypeScript.

**Acceptance Criteria:**
*   Users can perform 100% of configuration tasks while offline.
*   Sync occurs automatically upon network restoration without user intervention.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer <JWT>` token in the header.

### 4.1 Device Management

**Endpoint:** `GET /devices/`  
**Description:** Retrieve a paginated list of all IoT devices.  
**Query Params:** `?search=`, `?status=`, `?page=1`  
**Response:**
```json
{
  "count": 1250,
  "next": "/api/v1/devices/?page=2",
  "results": [
    { "id": "dev_991", "name": "Sensor_TX_01", "status": "online", "last_seen": "2023-10-24T10:00Z" }
  ]
}
```

**Endpoint:** `PATCH /devices/{id}/`  
**Description:** Update device configuration.  
**Request Body:**
```json
{
  "config_payload": { "sampling_rate": "5s", "power_mode": "low" },
  "updated_by": "user_44"
}
```
**Response:** `200 OK` with updated object.

### 4.2 RBAC and User Management

**Endpoint:** `POST /auth/token/`  
**Description:** Exchange credentials for a JWT.  
**Request Body:** `{ "username": "rpark", "password": "..." }`  
**Response:**
```json
{
  "access": "eyJhb...",
  "refresh": "def456...",
  "expires_in": 3600
}
```

**Endpoint:** `GET /auth/permissions/`  
**Description:** Retrieve the current user's role and assigned permissions.  
**Response:**
```json
{
  "role": "Regional Manager",
  "permissions": ["device.edit", "device.view", "report.export"]
}
```

### 4.3 Collaboration and Sync

**Endpoint:** `GET /sync/presence/{device_id}/`  
**Description:** Get a list of users currently editing a device.  
**Response:**
```json
{
  "active_users": [
    { "user_id": "ugupta", "name": "Valentina Gupta", "joined_at": "10:05:01" }
  ]
}
```

**Endpoint:** `POST /sync/delta/`  
**Description:** Push a configuration delta for collaborative editing.  
**Request Body:**
```json
{
  "device_id": "dev_991",
  "delta": { "field": "sampling_rate", "old": "10s", "new": "5s" },
  "timestamp": "2023-10-24T10:06:00.123Z"
}
```
**Response:** `201 Created`

### 4.4 File and Firmware

**Endpoint:** `POST /firmware/upload/`  
**Description:** Request a signed S3 URL for firmware upload.  
**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/quarantine/...",
  "file_id": "fw_8821",
  "expires_in": 300
}
```

**Endpoint:** `GET /firmware/status/{file_id}/`  
**Description:** Check if the virus scan has completed.  
**Response:**
```json
{
  "file_id": "fw_8821",
  "status": "scanning", // or "clean", "infected"
  "scan_completed_at": null
}
```

---

## 5. DATABASE SCHEMA

The database uses PostgreSQL 15. Due to the 30% raw SQL usage, all table names and column names are strictly immutable once deployed to production.

### 5.1 Table Definitions

1.  **`users`**: (Internal User Accounts)
    *   `id` (UUID, PK)
    *   `username` (Varchar, Unique)
    *   `email` (Varchar)
    *   `password_hash` (Text)
    *   `is_active` (Boolean)

2.  **`roles`**: (RBAC Roles)
    *   `id` (Integer, PK)
    *   `role_name` (Varchar) - e.g., "Admin", "Tech"
    *   `description` (Text)

3.  **`user_roles`**: (Many-to-Many Link)
    *   `user_id` (UUID, FK)
    *   `role_id` (Integer, FK)

4.  **`permissions`**: (Specific Access Rights)
    *   `id` (Integer, PK)
    *   `codename` (Varchar) - e.g., "can_reboot_device"
    *   `description` (Text)

5.  **`role_permissions`**: (Many-to-Many Link)
    *   `role_id` (Integer, FK)
    *   `permission_id` (Integer, FK)

6.  **`devices`**: (The Core IoT Registry)
    *   `id` (UUID, PK)
    *   `serial_number` (Varchar, Unique, Indexed)
    *   `model_id` (Varchar)
    *   `status` (Enum: online, offline, maintenance)
    *   `last_ping` (Timestamp)
    *   `current_firmware_version` (Varchar)

7.  **`device_configs`**: (Configuration State)
    *   `id` (Integer, PK)
    *   `device_id` (UUID, FK)
    *   `config_json` (JSONB) - Store for flexible config
    *   `updated_at` (Timestamp)

8.  **`firmware_blobs`**: (File Metadata)
    *   `id` (UUID, PK)
    *   `version` (Varchar)
    *   `s3_path` (Text)
    *   `scan_status` (Enum: pending, clean, infected)
    *   `checksum` (Varchar)

9.  **`audit_logs`**: (Compliance Tracking)
    *   `id` (BigInt, PK)
    *   `actor_id` (UUID, FK)
    *   `action` (Varchar)
    *   `target_id` (UUID)
    *   `timestamp` (Timestamp, Indexed)

10. **`sync_sessions`**: (Collaborative Session Tracking)
    *   `id` (UUID, PK)
    *   `device_id` (UUID, FK)
    *   `user_id` (UUID, FK)
    *   `connected_at` (Timestamp)

### 5.2 Relationships
*   **Users $\leftrightarrow$ Roles:** Many-to-Many via `user_roles`.
*   **Roles $\leftrightarrow$ Permissions:** Many-to-Many via `role_permissions`.
*   **Devices $\rightarrow$ Configs:** One-to-One relationship.
*   **Devices $\rightarrow$ Audit Logs:** One-to-Many (Each device can have many audit entries).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Umbra utilizes three distinct environments to ensure stability and zero-downtime deployment.

| Environment | Purpose | Infrastructure | Deployment Trigger |
| :--- | :--- | :--- | :--- |
| **Development** | Feature iteration | Local Docker / AWS Dev Cluster | Push to `develop` branch |
| **Staging** | QA & User Acceptance | Mirror of Prod (Smaller Scale) | Merge to `release` branch |
| **Production** | Live Retail Operations | AWS ECS (Multi-AZ) | Manual Approval $\rightarrow$ Green/Blue Deploy |

### 6.2 Deployment Pipeline
The deployment process is intentionally conservative due to the "zero downtime" requirement.
1.  **CI Build:** GitHub Actions runs unit tests and linting.
2.  **Staging Deployment:** Code is deployed to Staging.
3.  **Manual QA Gate:** Greta Nakamura (QA Lead) must sign off on the release. This includes a full regression suite and a check of any Raw SQL migrations.
4.  **Turnaround:** The window from "Merge to Release" to "Production Live" is exactly **2 days**.
5.  **Production Push:** Utilizing AWS ECS **Blue/Green deployment**. The "Green" environment is spun up; once health checks pass, traffic is shifted 10% $\rightarrow$ 50% $\rightarrow$ 100%.

### 6.3 Infrastructure Details
*   **ECS Fargate:** We use serverless containers to avoid managing EC2 instances.
*   **Auto-scaling:** Scaling triggers are set to 70% CPU utilization.
*   **Networking:** VPC with private subnets for the database and Redis; public subnets for the ALB.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** `pytest`.
*   **Coverage Goal:** 80% overall.
*   **Focus:** Business logic in `services.py` and validation logic in `serializers.py`.
*   **Mocking:** All external AWS calls are mocked using `moto`.

### 7.2 Integration Testing
*   **Focus:** Testing the interaction between Django, PostgreSQL, and Redis.
*   **Method:** A dedicated integration suite runs against a containerized version of the database to ensure that the "Raw SQL" queries do not break when the ORM schema changes.
*   **Frequency:** Every Pull Request.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Scope:** Critical user journeys (e.g., "User logs in $\rightarrow$ searches for device $\rightarrow$ edits config $\rightarrow$ saves change").
*   **Hardware Simulation:** A set of "Virtual IoT Devices" (Python scripts) simulate the MQTT/HTTPS traffic to test the real-time sync features.

### 7.4 QA Gate Process
Greta Nakamura leads the QA gate. No code enters production without a "QA Passed" label on the GitHub PR. The 2-day turnaround is spent on:
*   **Day 1:** Automated regression and sanity checks.
*   **Day 2:** Manual edge-case testing and final stakeholder sign-off.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Vendor EOL (End-of-Life) for primary IoT module | High | Critical | Build a "Hardware Abstraction Layer" (HAL) to allow switching vendors without rewriting core logic. |
| **R-02** | Project Sponsor Rotation | Medium | High | De-scope non-essential features (e.g., Offline-First) to ensure Milestone 2 is met regardless of leadership change. |
| **R-03** | Raw SQL Migration Failure | Medium | Critical | Implement a mandatory `sql-audit` step in the QA gate; use `pg_dump` backups before every deployment. |
| **R-04** | Team Friction (Forming Stage) | Medium | Medium | Implement bi-weekly retrospectives and shared ownership of modules to build trust. |

**Probability/Impact Matrix:**
*   **Critical:** Stop-ship event.
*   **High:** Significant delay or budget overrun.
*   **Medium:** Manageable with adjusted timeline.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown

**Phase 1: Core Infrastructure (Jan 2025 – July 2025)**
*   Focus: RBAC, Base API, and Database Migration from Legacy.
*   *Dependency:* Infrastructure setup must be complete before device migration.

**Phase 2: Real-time Capabilities (July 2025 – Sept 2025)**
*   Focus: Collaborative Editing, WebSocket integration, and Alpha testing.
*   *Dependency:* Auth system must be stable to manage collaborative sessions.

**Phase 3: Edge Distribution & Stability (Sept 2025 – Nov 2025)**
*   Focus: File uploads, CDN, and performance tuning.
*   *Dependency:* Alpha release feedback must be integrated.

### 9.2 Key Milestones
*   **Milestone 1: Internal Alpha Release (2025-07-15)**
    *   Goal: System functional for internal Oakmount staff.
    *   Success: 100% of basic CRUD operations working.
*   **Milestone 2: First Paying Customer Onboarded (2025-09-15)**
    *   Goal: Prove commercial viability and system stability under real load.
    *   Success: First external retail client successfully migrated.
*   **Milestone 3: Post-launch Stability Confirmed (2025-11-15)**
    *   Goal: Confirm "Zero Downtime" was achieved and metrics are met.
    *   Success: 30 days of 99.9% uptime.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Rumi Park, Valentina Gupta, Greta Nakamura, Aaliya Stein  
**Discussion:**
*   The team debated between a full microservices approach vs. a modular monolith.
*   Valentina raised concerns about the complexity of distributed transactions in a microservices setup given the team's current "forming" stage.
*   Rumi decided on the **Modular Monolith** to prioritize speed of delivery and ease of deployment.
*   Greta emphasized that any deployment must have a 2-day QA window to prevent legacy system crashes.

**Action Items:**
*   [Rumi] Finalize the modular folder structure in Django. (Due: 2023-11-05)
*   [Valentina] Map out the legacy database fields to the new PostgreSQL schema. (Due: 2023-11-10)

---

### Meeting 2: The "Raw SQL" Dilemma
**Date:** 2023-11-15  
**Attendees:** Rumi Park, Valentina Gupta, Greta Nakamura  
**Discussion:**
*   Valentina reported that 30% of the telemetry queries are too slow using the Django ORM.
*   The team agreed to use Raw SQL for performance but acknowledged this creates a "migration hazard."
*   Greta requested a specific "SQL Audit" checklist to be added to the QA process.
*   Decision: Raw SQL is permitted only in `repositories.py` files.

**Action Items:**
*   [Valentina] Create the `repositories.py` pattern for the telemetry module. (Due: 2023-11-20)
*   [Greta] Draft the SQL Audit checklist for the QA gate. (Due: 2023-11-22)

---

### Meeting 3: Vendor EOL and Risk Mitigation
**Date:** 2023-12-01  
**Attendees:** Rumi Park, Aaliya Stein, Executive Sponsor  
**Discussion:**
*   The primary IoT vendor announced end-of-life for the Gen-2 modules.
*   Aaliya pointed out that 40% of the current retail fleet uses these modules.
*   The sponsor expressed concern about budget for a hardware pivot.
*   Rumi proposed a Hardware Abstraction Layer (HAL) to decouple the software from the specific vendor's API.
*   The "Offline-First" feature is now officially **blocked** until the tool budget is approved.

**Action Items:**
*   [Rumi] Design the HAL interface for the device communication layer. (Due: 2023-12-15)
*   [Aaliya] Coordinate with the vendor to see if an extended support contract is possible. (Due: 2023-12-20)

---

## 11. BUDGET BREAKDOWN

The total investment for Project Umbra is **$3,000,000**.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,800,000 | Salaries for 20+ engineers, QA, and Support over 2 years. |
| **Infrastructure** | 20% | $600,000 | AWS ECS, RDS, Redis, S3, and CloudFront costs. |
| **Tools & Licensing** | 10% | $300,000 | Security scanning tools, IDE licenses, and (Pending) Sync Library. |
| **Contingency** | 10% | $300,000 | Reserved for vendor EOL pivot and emergency scaling. |

**Budget Note:** The "Tools" category currently has a pending request for $45,000 to unblock the "Offline-First" mode.

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Protocol
To mitigate the risk of raw SQL breaking the system, the following protocol is mandatory:
1.  **Detection:** Use `grep -r "cursor.execute" .` to identify all raw queries.
2.  **Verification:** Run the query against a restored production backup in the staging environment.
3.  **Sign-off:** The Data Engineer (Valentina Gupta) must manually verify that the SQL query is compatible with the new schema.
4.  **Execution:** Migrations are run with `django-admin migrate` followed by a manual check of the affected tables.

### Appendix B: Collaborative Conflict Resolution Logic
The "Last-Write-Wins" (LWW) logic is implemented as follows:
*   Every change request contains a `timestamp_utc` (ISO 8601 with millisecond precision).
*   The server compares the incoming `timestamp_utc` with the `last_updated` timestamp in the `device_configs` table.
*   If `incoming_timestamp > last_updated`, the change is applied.
*   If `incoming_timestamp < last_updated`, the change is rejected, and a `409 Conflict` response is returned to the client, triggering a local state refresh.