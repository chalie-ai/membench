# PROJECT SPECIFICATION: PROJECT ECLIPSE
**Document Version:** 1.0.4  
**Status:** Draft / Active  
**Project Lead:** Dina Nakamura (CTO)  
**Company:** Deepwell Data  
**Classification:** Internal Only  
**Date:** October 24, 2023

---

## 1. EXECUTIVE SUMMARY

**Project Eclipse** is a strategic technical overhaul designed to consolidate Deepwell Data’s fragmented operational infrastructure. Currently, the company relies on four redundant internal tools—*AgriTrack, SoilSync, YieldView,* and *CropGuard*—each maintaining its own database, authentication layer, and deployment pipeline. This redundancy has led to catastrophic "data silos," operational inefficiency, and an escalating cloud spend that threatens the company's margins. 

The primary objective of Project Eclipse is to migrate these four legacy monoliths into a unified microservices architecture governed by a centralized API Gateway. By transitioning to a high-performance Elixir/Phoenix stack deployed on Fly.io, Deepwell Data intends to transition from a "brute force" scaling model to a streamlined, event-driven architecture.

**Business Justification:**
The current infrastructure cost is unsustainable. We are paying for four sets of managed database instances, four redundant logging suites, and overlapping API subscriptions. Furthermore, the lack of a unified API layer means that updating a single business rule regarding crop yield calculations requires coordinated changes across four different codebases, often resulting in data discrepancies.

**ROI Projection:**
The primary financial driver is the reduction of the "cost per transaction." Currently, the overhead of maintaining four separate environments results in a high operational cost per API call. By consolidating these into a single gateway with shared caching and optimized PostgreSQL clusters, we project a **35% reduction in cost per transaction**. 

Beyond direct infrastructure savings, the ROI is realized through:
1. **Developer Velocity:** Reducing the time-to-market for new features by eliminating the need to synchronize updates across four tools.
2. **Operational Stability:** Replacing unstable legacy endpoints with a unified, rate-limited gateway.
3. **Risk Mitigation:** Addressing the "God Class" technical debt that currently represents a single point of failure for authentication and logging.

**Funding Model:**
Budget is not allocated as a lump sum but is released in **milestone-based tranches**. Funding for the subsequent phase is unlocked only upon the successful verification of the previous milestone’s success criteria (e.g., Performance benchmarks on 2025-06-15).

---

## 2. TECHNICAL ARCHITECTURE

Project Eclipse utilizes a modern functional stack centered on **Elixir 1.15** and **Phoenix 1.7**. The choice of Elixir allows Deepwell Data to leverage the BEAM virtual machine for massive concurrency, essential for the real-time collaborative features and high-throughput API gateway requirements.

### 2.1 Architecture Pattern: CQRS and Event Sourcing
For audit-critical domains (such as crop yield certification and financial transactions), Project Eclipse implements **Command Query Responsibility Segregation (CQRS)**. 

- **Command Side:** Handles the intent to change state. Every action is recorded as an immutable event in an `events` table (Event Sourcing).
- **Query Side:** Specialized read-models (projections) are maintained in PostgreSQL to provide high-performance data retrieval without complex joins across event logs.

### 2.2 System Diagram (ASCII Representation)

```text
[ Client Applications ]  --> [ Fly.io Global Edge ]
                                     |
                                     v
                          +-----------------------+
                          |    API GATEWAY        | <--- Rate Limiting & 
                          | (Phoenix / Plug)       |      Usage Analytics
                          +-----------------------+
                                     |
        _____________________________|_____________________________
       |                             |                             |
       v                             v                             v
[ Notification Svc ]        [ Collaboration Svc ]        [ File/CDN Svc ]
(Email, SMS, Push)          (LiveView / WebSockets)       (Virus Scan/S3)
       |                             |                             |
       +------------+----------------+-----------------------------+
                    |
                    v
        +-----------------------+      +-----------------------+
        |   PostgreSQL Cluster  | <--> |   Event Store (Log)   |
        | (Read/Write Splitting) |      | (Immutable Sequence)  |
        +-----------------------+      +-----------------------+
```

### 2.3 Deployment Pipeline
Deployment follows a rigorous manual QA gate. No code enters production without a sign-off from the Support Engineer (Astrid Costa) and the CTO.
1. **Development:** Local Docker containers.
2. **Staging:** Mirror of production on Fly.io.
3. **QA Gate:** 48-hour (2-day) turnaround for manual regression testing.
4. **Production:** Atomic deployment via Fly.io.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-Time Collaborative Editing with Conflict Resolution
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Description:** Deepwell Data users must be able to edit agricultural field maps and crop schedules simultaneously. Because multiple agronomists often work on the same plot, the system must handle concurrent edits without data loss.
*   **Technical Specification:** 
    The system will utilize **Phoenix LiveView** and **WebSockets** to maintain a stateful connection between the client and the server. To handle conflicts, we will implement an **Operational Transformation (OT)** or **Conflict-free Replicated Data Type (CRDT)** approach. 
    - The `CollaborationSvc` will maintain a "Presence" state using Phoenix Presence to track who is currently viewing a document.
    - Every keystroke or map adjustment is sent as a delta update.
    - The server validates the delta against the current version ID. If a version mismatch occurs (e.g., User A and User B edit the same cell), the server applies a deterministic resolution rule (Last-Write-Wins or Semantic Merge) and broadcasts the corrected state back to all clients.
*   **Acceptance Criteria:**
    - Latency for updates must be <100ms for users in the same region.
    - No data loss during simultaneous edits by up to 5 users per document.
    - Visual indicators (cursors) must show the real-time position of other users.

### 3.2 Localization and Internationalization (L10n/I18n)
*   **Priority:** High
*   **Status:** Blocked (Pending Legal/Data Processing Agreement)
*   **Description:** The platform must support 12 different languages to accommodate global agricultural markets. This includes not just UI translation, but date, time, and unit conversions (e.g., hectares to acres).
*   **Technical Specification:** 
    We will use the `Gettext` library integrated with Phoenix. Translation files (`.po` files) will be stored in the repository and managed via a localization dashboard. 
    - **Language Support:** English, Spanish, Portuguese, French, Mandarin, Hindi, Arabic, German, Japanese, Vietnamese, Thai, and Swahili.
    - **Dynamic Content:** The system must support "Dynamic Translation" for user-generated labels via a translation API.
    - **Regional Settings:** A `user_settings` table will store the preferred locale, which will trigger the correct translation set on the API Gateway layer.
*   **Acceptance Criteria:**
    - All UI strings must be externalized into Gettext files.
    - Right-to-Left (RTL) support for Arabic.
    - Unit conversion logic must be centralized in a `MeasurementSvc` to ensure consistency across the 12 locales.

### 3.3 File Upload with Virus Scanning and CDN Distribution
*   **Priority:** High
*   **Status:** Blocked (Pending Legal/Data Processing Agreement)
*   **Description:** Users must be able to upload high-resolution satellite imagery and soil reports. These files must be scanned for malware before being stored and then distributed via a CDN for low-latency access.
*   **Technical Specification:** 
    1. **Upload Flow:** The client requests a pre-signed URL from the API Gateway. The file is uploaded directly to an S3-compatible bucket (Fly.io compatible).
    2. **Scanning:** Upon upload completion, an S3 Trigger invokes a Lambda function (or Elixir worker) that pipes the file through a **ClamAV** instance.
    3. **Quarantine:** If the virus scan fails, the file is moved to a `quarantine/` prefix and a notification is sent to the user.
    4. **Distribution:** Once cleared, the file is indexed in the database and served via a CloudFront or Fly.io CDN edge cache.
*   **Acceptance Criteria:**
    - Maximum upload size: 500MB.
    - Virus scan completion time: < 30 seconds.
    - CDN cache hit rate: > 80% for frequently accessed reports.

### 3.4 API Rate Limiting and Usage Analytics
*   **Priority:** Medium
*   **Status:** In Design
*   **Description:** To protect the microservices from being overwhelmed and to track usage for billing, the API Gateway must implement strict rate limiting and detailed telemetry.
*   **Technical Specification:** 
    We will implement a **Token Bucket algorithm** using **Redis**.
    - **Tiers:** 
        - *Free:* 1,000 requests/hour.
        - *Standard:* 10,000 requests/hour.
        - *Enterprise:* 100,000 requests/hour.
    - **Tracking:** Each request will be logged to an `api_logs` table containing the `api_key`, `endpoint_path`, `response_code`, and `latency_ms`.
    - **Analytics:** A background GenServer will aggregate these logs into a `daily_usage_stats` table every hour to provide a dashboard for the admin.
*   **Acceptance Criteria:**
    - Correct `429 Too Many Requests` response when limits are exceeded.
    - Analytics dashboard reflects usage with a maximum lag of 60 minutes.

### 3.5 Notification System
*   **Priority:** Medium
*   **Status:** In Review
*   **Description:** A unified system to handle all outbound communications (Email, SMS, In-App, and Push).
*   **Technical Specification:** 
    A centralized `NotificationSvc` will act as a dispatcher.
    - **Channels:**
        - *Email:* Integrated via SendGrid.
        - *SMS:* Integrated via Twilio.
        - *Push:* Integrated via Firebase Cloud Messaging (FCM).
        - *In-App:* Handled via Phoenix Channels (WebSockets).
    - **Logic:** The system will use a "Preference Matrix" stored in the DB. If a user has disabled SMS but enabled Email for "Critical Alerts," the dispatcher will only route to SendGrid.
    - **Queueing:** Using **Oban** (PostgreSQL-based job queue) to handle retries and exponential backoff for failed deliveries.
*   **Acceptance Criteria:**
    - Delivery of a "Critical Alert" across all enabled channels within 5 seconds of the trigger.
    - Full audit log of sent notifications.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base URL: `https://api.deepwelldata.com/v1/`

### 4.1 Authentication & Gateway
**POST `/auth/login`**
- **Purpose:** Authenticate user and return JWT.
- **Request:** `{ "email": "user@deepwell.com", "password": "hashed_password" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_at": "2023-10-25T00:00:00Z" }`

**GET `/gateway/usage`**
- **Purpose:** Return current rate-limit status.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "remaining": 450, "reset_at": 1698240000 }`

### 4.2 Collaboration Service
**GET `/collab/document/{id}`**
- **Purpose:** Fetch the current state of a collaborative map.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "id": "doc_123", "content": "{...}", "version": 42 }`

**PATCH `/collab/document/{id}/delta`**
- **Purpose:** Submit a partial update (delta) to a document.
- **Request:** `{ "version": 42, "delta": { "field_1": "New Value" } }`
- **Response:** `200 OK { "new_version": 43, "status": "merged" }`

### 4.3 Notification Service
**POST `/notify/send`**
- **Purpose:** Trigger a notification to a user.
- **Request:** `{ "user_id": "u_99", "channel": "sms", "message": "Crop alert: Frost detected!" }`
- **Response:** `202 Accepted { "job_id": "oban_556" }`

**GET `/notify/preferences/{user_id}`**
- **Purpose:** Retrieve user notification settings.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "email": true, "sms": false, "push": true }`

### 4.4 File Service
**POST `/files/upload-url`**
- **Purpose:** Request a pre-signed S3 URL.
- **Request:** `{ "filename": "satellite_map.tif", "size": 10485760 }`
- **Response:** `200 OK { "upload_url": "https://s3.amazon...", "file_id": "f_789" }`

**GET `/files/download/{file_id}`**
- **Purpose:** Retrieve a sanitized file via CDN.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `302 Found (Redirect to CDN URL)`

---

## 5. DATABASE SCHEMA

The system uses a single PostgreSQL 15 cluster with logical partitioning.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `id (PK)`, `email`, `password_hash`, `locale` | 1:N with `user_settings` | Core identity table. |
| `user_settings` | `id (PK)`, `user_id (FK)`, `theme`, `timezone` | N:1 with `users` | User preferences. |
| `api_keys` | `id (PK)`, `user_id (FK)`, `key_hash`, `tier` | N:1 with `users` | Rate limiting tier assignment. |
| `documents` | `id (PK)`, `owner_id (FK)`, `version`, `content` | N:1 with `users` | Collaborative map data. |
| `document_events` | `id (PK)`, `doc_id (FK)`, `delta`, `created_at` | N:1 with `documents` | Event store for CQRS. |
| `files` | `id (PK)`, `user_id (FK)`, `s3_path`, `scan_status` | N:1 with `users` | File metadata and virus status. |
| `notifications` | `id (PK)`, `user_id (FK)`, `channel`, `status` | N:1 with `users` | Log of sent notifications. |
| `notification_prefs`| `id (PK)`, `user_id (FK)`, `channel`, `enabled` | N:1 with `users` | Opt-in/out matrix. |
| `api_logs` | `id (PK)`, `api_key_id (FK)`, `path`, `latency` | N:1 with `api_keys` | Telemetry for analytics. |
| `daily_usage_stats`| `id (PK)`, `api_key_id (FK)`, `date`, `total_reqs` | N:1 with `api_keys` | Aggregated usage data. |

### 5.2 Schema Logic
The `document_events` table is the heart of the event-sourcing mechanism. No record in `documents` is updated without first appending an entry to `document_events`. This ensures that the "Audit-Critical" requirement is met, allowing the team to reconstruct the state of a map at any specific point in time for regulatory compliance.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Topology
Project Eclipse is hosted on **Fly.io**, utilizing their global anycast network to minimize latency for the collaborative editing features.

- **Development (Dev):**
    - Each developer runs a local stack via `docker-compose`.
    - Shared Dev environment on Fly.io for integration testing.
    - Database: PostgreSQL (Single Instance).
- **Staging (Staging):**
    - Exact replica of Production.
    - Used for the **Manual QA Gate**.
    - Database: PostgreSQL (Primary/Replica).
    - All third-party integrations (Twilio, SendGrid) use "Sandbox" credentials.
- **Production (Prod):**
    - Distributed across three regions (US-East, EU-West, Asia-Pacific).
    - Database: Managed PostgreSQL Cluster with High Availability.
    - Redis: Distributed for rate limiting and Phoenix Presence.

### 6.2 The QA Gate Process
The deployment process is strictly linear:
1. **Push to `main`** $\rightarrow$ Auto-deploy to Staging.
2. **QA Window:** Astrid Costa performs manual regression tests.
3. **Sign-off:** Dina Nakamura approves the release.
4. **Promotion:** Staging $\rightarrow$ Production.
5. **Turnaround:** Total time from code-complete to production is **2 days**.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (ExUnit)
Every Elixir module must have a corresponding `test` file.
- **Coverage Goal:** 80% line coverage.
- **Focus:** Pure functions, business logic in the `CollaborationSvc`, and measurement conversions in the L10n module.

### 7.2 Integration Testing
Focuses on the interaction between the API Gateway and the underlying microservices.
- **Tooling:** `Wallaby` for browser-based LiveView testing.
- **Scope:** End-to-end flow of a user logging in, uploading a file, and receiving a notification.
- **S3 Mocking:** Use of `S3Mock` to avoid incurring costs during CI/CD.

### 7.3 End-to-End (E2E) and Manual QA
Because the project involves complex real-time collaboration, automated tests are insufficient.
- **Manual Gate:** Astrid Costa validates "Edge Case" scenarios (e.g., two users editing the same field while one loses internet connection).
- **Performance Benchmarking:** Using `k6` to simulate 1,000 concurrent users to ensure the 2025-06-15 performance targets are met.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Integration partner's API is undocumented/buggy | High | High | **Parallel Path:** Develop a prototype for an alternative provider simultaneously. |
| R2 | Key Architect leaving in 3 months | Medium | Critical | **External Consultant:** Hire an independent auditor to assess the architecture now. |
| R3 | Legal review of Data Processing Agreement (DPA) | High | Medium | **Current Blocker:** Escalated to Legal; features 4 & 5 are frozen until signed. |
| R4 | "God Class" failures during migration | Medium | High | **Refactor Sprint:** Dedicated 2-week window to break the 3k-line class into smaller modules. |

**Impact Matrix:**
- **Critical:** Blockers for launch (e.g., Collaboration Svc, Architect departure).
- **High:** Significant delays or performance degradation.
- **Medium:** Manageable through standard development cycles.

---

## 9. TIMELINE AND PHASES

### Phase 1: The Foundation (Oct 2023 - May 2025)
- **Focus:** API Gateway, Auth migration, and "God Class" decomposition.
- **Dependencies:** Legal DPA signature (required for File/L10n work).
- **Key Goal:** Stabilize the core routing and security.

### Phase 2: Real-time & Performance (June 2025)
- **Focus:** Finalizing the Collaboration Svc and conflict resolution.
- **Milestone 1 (2025-06-15):** Performance benchmarks must be met (Latency <100ms).

### Phase 3: Security & Compliance (July 2025 - August 2025)
- **Focus:** Internal security audit of the new gateway and CQRS event logs.
- **Milestone 2 (2025-08-15):** Security audit passed.

### Phase 4: Beta & Global Launch (Sept 2025 - Oct 2025)
- **Focus:** Rolling out L10n (12 languages) and File Uploads.
- **Milestone 3 (2025-10-15):** External beta with 10 pilot users.

---

## 10. MEETING NOTES

*Note: All meetings recorded via Zoom. No participants have reported watching the recordings.*

### Meeting 1: Architecture Sync (2023-11-02)
- **Attendees:** Dina, Orin, Cleo, Astrid.
- **Discussion:** Orin argued for a Kafka-based event stream. Dina rejected this as "over-engineering" for a team of 4, insisting on PostgreSQL-based event sourcing for simplicity.
- **Decision:** Stick to PostgreSQL for the event store. Orin remained silent for the last 15 minutes of the call.
- **Action Item:** Cleo to finish the Figma mocks for the collaborative map.

### Meeting 2: The "God Class" Crisis (2023-12-15)
- **Attendees:** Dina, Orin, Astrid.
- **Discussion:** Astrid reported that the 3,000-line authentication/logging class is causing intermittent timeouts in the legacy system. Orin pointed out that the class is too fragile to touch without a full rewrite.
- **Decision:** The team will not rewrite it yet but will wrap it in a "Facade" pattern to isolate it from the new gateway.
- **Note:** Dina and Orin spent 10 minutes arguing about naming conventions; they stopped speaking to each other for the remainder of the meeting.

### Meeting 3: Legal Blocker Update (2024-02-10)
- **Attendees:** Dina, Cleo, Astrid.
- **Discussion:** The DPA (Data Processing Agreement) is still with the legal team. This is now officially blocking the "Localization" and "File Upload" features.
- **Decision:** Shift focus to the Notification System and API Rate Limiting to avoid idle time.
- **Action Item:** Dina to email the Head of Legal.

---

## 11. BUDGET BREAKDOWN

The budget is released in tranches based on the milestones in Section 9. Total estimated budget is variable, with the following category weights.

| Category | Allocation (%) | Estimated Amount (Tranche 1) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $180,000 | Salaries for 4 team members. |
| **Infrastructure** | 20% | $60,000 | Fly.io, Redis, PostgreSQL Managed. |
| **External Tools** | 10% | $30,000 | SendGrid, Twilio, FCM, ClamAV. |
| **Contingency** | 10% | $30,000 | External consultant for architect risk. |
| **Total** | **100%** | **$300,000** | *Per Tranche Period* |

---

## 12. APPENDICES

### Appendix A: The "God Class" Map
The legacy `SystemManager.ex` (the 3,000-line God Class) currently handles:
- **Lines 1-500:** OAuth2 token validation and session management.
- **Lines 501-1200:** Global logging to a legacy flat file.
- **Lines 1201-2000:** Email template rendering and SMTP dispatch.
- **Lines 2001-3000:** Miscellaneous utility functions (date formatting, string stripping).
**Migration Plan:** This will be broken into `AuthSvc`, `LogSvc`, and `EmailSvc`.

### Appendix B: Localization Matrix
The following 12 languages are prioritized based on regional crop yield data:
1. **English (US/UK)**
2. **Spanish (Mexico/Spain)**
3. **Portuguese (Brazil)**
4. **French (France/West Africa)**
5. **Mandarin (China)**
6. **Hindi (India)**
7. **Arabic (Egypt/UAE)**
8. **German (Germany)**
9. **Japanese (Japan)**
10. **Vietnamese (Vietnam)**
11. **Thai (Thailand)**
12. **Swahili (Kenya/Tanzania)**

*All translations will be verified by local agricultural consultants to ensure that technical terminology (e.g., "Nitrogen Leaching") is translated accurately.*