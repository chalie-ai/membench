# PROJECT SPECIFICATION: BEACON
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Classification:** Internal - Flintrock Engineering  
**Date:** October 24, 2025  
**Owner:** Astrid Liu (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Beacon" is a mission-critical embedded systems firmware and cloud integration initiative developed by Flintrock Engineering. The project serves as the technical foundation for a strategic partnership within the healthcare industry, designed to synchronize high-fidelity medical device telemetry with an external partner’s proprietary API. Unlike standard standalone products, Beacon is an integration-centric project; its success is inextricably linked to the external partner’s deployment timeline and API availability. 

The system consists of firmware residing on edge devices, a localized SQLite database for data persistence during network outages, and a serverless cloud backend designed to orchestrate data flow between the healthcare providers and the strategic partner.

### 1.2 Business Justification
In the current healthcare landscape, data fragmentation between device manufacturers and clinical providers leads to significant delays in patient care. Flintrock Engineering has identified a gap in the market for a seamless "bridge" firmware that can normalize heterogeneous device data and push it to partner ecosystems in real-time. By developing Beacon, Flintrock positions itself as the essential middleware provider for this partnership, creating a high barrier to entry for competitors and securing a long-term recurring revenue stream through integration maintenance.

The primary business driver is the reduction of manual data entry by clinical staff. Currently, data is transferred via manual export/import processes that are prone to human error and latency. Beacon automates this pipeline, ensuring that clinical decisions are based on the most recent telemetry.

### 1.3 ROI Projection
The Return on Investment (ROI) for Project Beacon is calculated based on three primary levers:
1. **Operational Efficiency:** A projected 50% reduction in manual processing time for end users. Assuming a clinical staff cost of $85/hour and an average of 10 hours per week spent on manual data reconciliation per clinic, across 100 pilot clinics, this represents a cost saving of approximately $4.4 million annually.
2. **Strategic Partnership Value:** The integration is expected to unlock a tiered licensing model. We project a Year 1 revenue of $1.2M, scaling to $3.5M by Year 3 as more device types are supported.
3. **Market Expansion:** Success in this partnership provides a blueprint for integrating with other healthcare APIs, potentially expanding the addressable market by 300%.

The total projected ROI over 36 months is estimated at 240%, accounting for the variable milestone-based funding and development costs.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level System Design
Beacon utilizes a hybrid edge-cloud architecture. The firmware is written in **Rust** to ensure memory safety and high performance, which is critical for healthcare-grade embedded systems. The edge layer handles data ingestion, local storage, and initial normalization. The cloud layer, built on **Cloudflare Workers**, provides a globally distributed, serverless environment to handle API orchestration and multi-tenant data routing.

### 2.2 Stack Detail
- **Backend:** Rust (compiled to WebAssembly for Cloudflare Workers).
- **Frontend:** React 18 with Tailwind CSS for the provider dashboard.
- **Edge Storage:** SQLite (via an embedded C-wrapper in Rust) for local caching and store-and-forward capabilities.
- **Cloud Infrastructure:** Cloudflare Workers (Serverless), Cloudflare KV for session management, and Cloudflare D1 for distributed SQL.
- **Orchestration:** API Gateway (Cloudflare) managing routing, authentication, and rate limiting.
- **Deployment:** GitHub Actions CI/CD utilizing Blue-Green deployment strategies to ensure zero downtime for critical healthcare services.

### 2.3 ASCII Architecture Diagram
```text
[ Healthcare Device ] 
       |
       v
[ Beacon Firmware (Rust) ] <---> [ Local SQLite Edge DB ]
       |
       | (HTTPS/TLS 1.3)
       v
[ Cloudflare API Gateway ] <--- [ Auth / Rate Limiter ]
       |
       +-----------------------+-----------------------+
       |                       |                       |
[ Serverless Worker A ]  [ Serverless Worker B ]  [ Serverless Worker C ]
(Data Normalization)     (Tenant Isolation)       (Notification Engine)
       |                       |                       |
       v                       v                       v
[ External Partner API ] <--- [ Analytics ] <--- [ D1 Database ]
```

### 2.4 Component Descriptions
- **Rust Firmware:** Implements the core logic for device communication, data polling, and the SQLite bridge. It manages the "Heartbeat" of the device and handles the retry logic when the Cloudflare endpoint is unreachable.
- **Cloudflare Workers:** These functions act as the glue. Because they are serverless, they scale automatically based on the number of active beacons in the field.
- **SQLite Edge:** Used as a write-ahead log (WAL). If the internet fails, data is queued in SQLite and flushed to the cloud upon reconnection.
- **React Frontend:** A thin client for administrators to monitor device health, manage tenant settings, and view usage analytics.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** In Design

**Description:**
The system must support the ingestion of legacy healthcare data formats (HL7, FHIR, and custom CSVs) and export these into the partner's proprietary JSON format. The "Auto-Detection" engine must analyze the first 1KB of any uploaded file to determine the MIME type and schema version without requiring user input.

**Functional Requirements:**
- The system shall support `.csv`, `.json`, `.xml`, and `.hl7` extensions.
- The `FormatAnalyzer` module in Rust will use a regex-based heuristic to identify the schema.
- If a format is ambiguous, the system must trigger a "Verification Prompt" in the React frontend.
- Exported data must be validated against the Partner API's JSON schema before transmission.

**Technical Constraints:**
- Large files (>50MB) must be processed using a streaming parser to avoid memory overflow in the serverless worker (128MB limit).
- Local SQLite must store a hash of every imported file to prevent duplicate data entry.

**User Flow:**
User uploads a file $\rightarrow$ Cloudflare Worker triggers `detect_format()` $\rightarrow$ Format identified as "HL7v2" $\rightarrow$ Data mapped to Internal Schema $\rightarrow$ Pushed to SQLite/Cloud $\rightarrow$ Success notification.

---

### 3.2 Multi-Tenant Data Isolation with Shared Infrastructure
**Priority:** Medium | **Status:** In Progress

**Description:**
Beacon serves multiple healthcare providers (tenants) using a shared set of serverless functions. To ensure HIPAA-adjacent security and data integrity, the system must implement strict logical isolation. No tenant should ever be able to query or view data belonging to another tenant.

**Functional Requirements:**
- Every API request must include a `Tenant-ID` header, validated via JWT (JSON Web Token).
- The database queries must utilize a "Row-Level Security" (RLS) pattern, where every SQL statement includes a `WHERE tenant_id = ?` clause.
- Cache keys in Cloudflare KV must be prefixed with the Tenant ID (e.g., `tenant_123:session_abc`).
- Tenant-specific configurations (e.g., API keys for the partner) must be encrypted at rest using AES-256.

**Technical Constraints:**
- The shared infrastructure must handle "noisy neighbor" problems. If Tenant A floods the API, Tenant B's performance must not degrade.
- Isolation must be enforced at the middleware layer of the Cloudflare Worker, not just the frontend.

**Validation:**
A security test will be performed where a JWT for Tenant A is used to attempt to access a resource ID belonging to Tenant B; the system must return a `403 Forbidden` response.

---

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Because the external partner API imposes strict limits on request volume, Beacon must implement a sophisticated rate-limiting engine to prevent the partner from banning the Flintrock API key. Additionally, the system must track usage per tenant for billing purposes.

**Functional Requirements:**
- Implement a "Token Bucket" algorithm for rate limiting.
- Global limit: 1,000 requests per minute (RPM) across all tenants.
- Per-tenant limit: 100 RPM.
- When a limit is reached, the system must return a `429 Too Many Requests` response with a `Retry-After` header.
- Analytics must track: Total requests, Error rates (4xx, 5xx), Latency (p95, p99), and Data throughput (MB/s).

**Technical Constraints:**
- Rate limiting must be performed at the Edge (Cloudflare Workers) to prevent unnecessary load on the backend.
- Analytics data must be asynchronously written to the D1 database to avoid adding latency to the primary request path.

**Success Metric:**
Zero `429` responses received from the External Partner API during the Beta phase.

---

### 3.4 A/B Testing Framework (Feature Flag System)
**Priority:** Medium | **Status:** Blocked

**Description:**
To iteratively improve the firmware's data-polling efficiency, the team requires a framework to deploy different logic versions to subsets of devices. This is integrated into the feature flag system, allowing "Canary" releases.

**Functional Requirements:**
- Ability to define a "Flag" (e.g., `poll_interval_v2`) and assign it to a percentage of the device population (e.g., 10%).
- The React frontend must allow managers to shift the percentage in real-time.
- The firmware must check for active flags upon boot and periodically every 60 minutes.
- The system must track which version of the logic is active for every single data point recorded to ensure accurate A/B analysis.

**Technical Constraints:**
- Since the firmware is embedded, flag updates must be lightweight. Use a compact binary format or a small JSON object.
- To prevent "flag drift," flags must have an expiration date after which they default to "Off."

**Blocker:**
Currently blocked by the lack of a robust device-shadowing mechanism in the current cloud architecture.

---

### 3.5 Notification System (Email, SMS, In-App, Push)
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Description:**
The system must alert clinical staff when a device goes offline, when data synchronization fails, or when the partner API returns a critical error. This requires a multi-channel notification engine.

**Functional Requirements:**
- **Email:** Triggered via SendGrid for weekly reports and critical alerts.
- **SMS:** Triggered via Twilio for urgent "Device Offline" notifications.
- **In-App:** A notification bell in the React dashboard using WebSockets for real-time updates.
- **Push:** Mobile notifications via Firebase Cloud Messaging (FCM).
- User preference center: Users must be able to opt-in/out of specific channels for specific alert types.

**Technical Constraints:**
- Notification delivery must be decoupled from the main data pipeline using a message queue (e.g., Cloudflare Queues) to prevent blocking.
- To avoid "notification fatigue," the system must implement an alert-suppression window (e.g., no more than one SMS every 30 minutes for the same device).

**Blocker:**
Blocked by the external partner's failure to provide the necessary webhook endpoints for status updates.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted at `https://api.beacon.flintrock.io/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 `POST /data/import`
- **Description:** Uploads raw telemetry data for processing.
- **Request:** 
  - Body: `multipart/form-data` (File)
  - Header: `Tenant-ID: <uuid>`
- **Response:** 
  - `202 Accepted`: `{"job_id": "abc-123", "status": "processing"}`
  - `415 Unsupported Media Type`: `{"error": "Format not recognized"}`

### 4.2 `GET /data/export/{tenantId}`
- **Description:** Retrieves processed data in the partner's format.
- **Request:** `GET` with `tenantId` path parameter.
- **Response:** 
  - `200 OK`: `{"data": [...], "export_date": "2026-01-01T00:00:00Z"}`

### 4.3 `GET /devices/status`
- **Description:** Returns the connectivity status of all beacons for a tenant.
- **Request:** `GET`
- **Response:** 
  - `200 OK`: `[{"device_id": "B-01", "status": "online", "last_sync": "2026-07-10T12:00Z"}]`

### 4.4 `POST /tenant/config`
- **Description:** Updates tenant-specific settings (e.g., rate limit overrides).
- **Request:** 
  - Body: `{"poll_rate": 300, "alert_email": "admin@clinic.com"}`
- **Response:** 
  - `200 OK`: `{"message": "Configuration updated"}`

### 4.5 `GET /analytics/usage`
- **Description:** Provides a summary of API calls and data throughput.
- **Request:** `GET` with query params `?start=...&end=...`
- **Response:** 
  - `200 OK`: `{"total_calls": 5000, "errors": 12, "bandwidth_mb": 450}`

### 4.6 `POST /notifications/preferences`
- **Description:** Sets user notification channel preferences.
- **Request:** 
  - Body: `{"email": true, "sms": false, "push": true}`
- **Response:** 
  - `200 OK`: `{"status": "Preferences saved"}`

### 4.7 `GET /system/health`
- **Description:** Public health check endpoint for load balancers.
- **Request:** `GET`
- **Response:** 
  - `200 OK`: `{"status": "healthy", "version": "1.0.4"}`

### 4.8 `DELETE /data/purge`
- **Description:** Wipes all data for a specific tenant (GDPR/Compliance request).
- **Request:** `DELETE` with `Tenant-ID` header.
- **Response:** 
  - `204 No Content`

---

## 5. DATABASE SCHEMA

The system uses a distributed D1 SQL database. All tables include `created_at` and `updated_at` timestamps.

### 5.1 Tables and Relationships

1. **`Tenants`**
   - `tenant_id` (UUID, PK): Unique identifier for the healthcare provider.
   - `name` (VARCHAR): Name of the clinic/organization.
   - `api_key_encrypted` (TEXT): Encrypted key for the partner API.
   - `tier` (VARCHAR): 'Basic', 'Premium', 'Enterprise'.

2. **`Devices`**
   - `device_id` (UUID, PK): Unique hardware ID.
   - `tenant_id` (UUID, FK $\rightarrow$ Tenants): Owner of the device.
   - `firmware_version` (VARCHAR): Current version installed.
   - `last_heartbeat` (TIMESTAMP): Last time device checked in.

3. **`TelemetryData`**
   - `data_id` (BIGINT, PK): Primary key.
   - `device_id` (UUID, FK $\rightarrow$ Devices): Origin device.
   - `payload` (JSONB): The normalized telemetry data.
   - `raw_hash` (VARCHAR): Hash of the original raw file to prevent duplicates.

4. **`ImportJobs`**
   - `job_id` (UUID, PK): Unique job identifier.
   - `tenant_id` (UUID, FK $\rightarrow$ Tenants): Who initiated the import.
   - `status` (ENUM): 'Pending', 'Processing', 'Completed', 'Failed'.
   - `error_log` (TEXT): Details if the job failed.

5. **`FeatureFlags`**
   - `flag_id` (UUID, PK): Unique flag name.
   - `flag_key` (VARCHAR): e.g., "poll_interval_v2".
   - `enabled` (BOOLEAN): Global status.
   - `rollout_percentage` (INTEGER): 0-100.

6. **`FlagAssignments`**
   - `assignment_id` (UUID, PK): Primary key.
   - `device_id` (UUID, FK $\rightarrow$ Devices): Which device gets the flag.
   - `flag_id` (UUID, FK $\rightarrow$ FeatureFlags): Which flag is assigned.

7. **`UsageLogs`**
   - `log_id` (BIGINT, PK): Primary key.
   - `tenant_id` (UUID, FK $\rightarrow$ Tenants): The tenant responsible.
   - `endpoint` (VARCHAR): The API path called.
   - `response_code` (INTEGER): 200, 429, etc.
   - `latency_ms` (INTEGER): Time taken to process.

8. **`Notifications`**
   - `notification_id` (UUID, PK): Primary key.
   - `tenant_id` (UUID, FK $\rightarrow$ Tenants): Recipient tenant.
   - `channel` (ENUM): 'Email', 'SMS', 'Push', 'In-App'.
   - `message` (TEXT): Content of the alert.
   - `is_read` (BOOLEAN): Status.

9. **`NotificationPreferences`**
   - `pref_id` (UUID, PK): Primary key.
   - `tenant_id` (UUID, FK $\rightarrow$ Tenants): Recipient.
   - `channel` (VARCHAR): Channel name.
   - `enabled` (BOOLEAN): User choice.

10. **`AuditLogs`**
    - `audit_id` (BIGINT, PK): Primary key.
    - `actor_id` (UUID): User who performed the action.
    - `action` (VARCHAR): e.g., "DATA_PURGE".
    - `timestamp` (TIMESTAMP): Exact time of action.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Beacon utilizes three distinct environments to ensure stability in a healthcare context.

#### 6.1.1 Development (`dev`)
- **Purpose:** Rapid prototyping and feature development.
- **Infrastructure:** Cloudflare Worker (Dev namespace), SQLite local files.
- **Deployment:** Automated on every push to the `develop` branch via GitHub Actions.
- **Data:** Mock data and anonymized samples.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation and Partner API integration testing.
- **Infrastructure:** Mirror of Production.
- **Deployment:** Triggered by a merge to the `release` branch.
- **Data:** A subset of real, sanitized data. This environment is used for the "External Beta" pilot.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live healthcare data processing.
- **Infrastructure:** Fully redundant Cloudflare Worker deployment across 3 regions.
- **Deployment:** Blue-Green strategy. The new version is deployed to "Green"; after health checks pass, traffic is shifted from "Blue" to "Green" via API Gateway weights.
- **Data:** Live production data with strict encryption and backup policies.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions. 
1. **Lint/Test:** Rust `cargo test` and React `npm test`.
2. **Build:** Compile Rust to WASM.
3. **Deploy:** `wrangler publish` to the target environment.

**Technical Debt Note:** The pipeline currently takes 45 minutes. This is primarily due to sequential execution of the Rust test suite and slow WASM compilation. Future optimization involves parallelizing the test matrix and implementing a build cache for dependencies.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend (Rust):** Each module (Normalization, Rate Limiter, Parser) has its own unit tests. We target 80% code coverage.
- **Frontend (React):** Component testing using Jest and React Testing Library to ensure UI stability.
- **Mocking:** All external API calls are mocked using a local mock-server during unit tests to avoid hitting rate limits.

### 7.2 Integration Testing
- **Edge-to-Cloud:** Testing the communication between the Rust firmware and the Cloudflare Worker using a staging environment.
- **Database Integrity:** Ensuring that `Tenant-ID` isolation is strictly enforced across all D1 queries.
- **Format Detection:** A suite of 50+ "golden files" (known formats) is run through the auto-detector to ensure $100\%$ accuracy for supported types.

### 7.3 End-to-End (E2E) Testing
- **User Journeys:** Using Playwright to simulate a user uploading a file $\rightarrow$ checking the status $\rightarrow$ receiving a notification.
- **Partner API Simulation:** A specialized "Partner Mock" is used to simulate `429` errors and `500` timeouts to verify the system's resilience and retry logic.

### 7.4 Acceptance Criteria
- **Metric 1:** 50% reduction in manual processing time (verified via user time-tracking in the pilot).
- **Metric 2:** Pass the external security audit on the first attempt (verified by a 3rd party auditor).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | High | Accept risk; monitor weekly. Ensure all architecture decisions are documented in this spec. |
| R-02 | Team lacks experience with Rust/WASM | High | Medium | Assign a dedicated "Tech Lead" to conduct weekly code reviews and knowledge-sharing sessions. |
| R-03 | Partner API instability | Medium | High | Implement aggressive caching and a robust store-and-forward queue in the SQLite edge DB. |
| R-04 | Compliance/Audit failure | Low | High | Internal security audits conducted monthly prior to the final external audit. |
| R-05 | CI Pipeline bottleneck | High | Low | Future sprint dedicated to parallelizing GitHub Actions. |

**Probability/Impact Matrix:**
- **High/High:** Immediate attention required (R-01).
- **High/Medium:** Active management required (R-02, R-05).
- **Medium/High:** Contingency planning required (R-03).

---

## 9. TIMELINE

### 9.1 Phase 1: Foundation (Jan 2026 - July 2026)
- **Focus:** Architecture and Core Firmware.
- **Dependencies:** Finalization of Partner API specs.
- **Key Event:** **Milestone 1: Architecture review complete (2026-07-15).**

### 9.2 Phase 2: Implementation (July 2026 - Sept 2026)
- **Focus:** Feature development (Import/Export, Multi-tenancy).
- **Dependencies:** Stable build of the Rust firmware.
- **Key Event:** **Milestone 2: MVP feature-complete (2026-09-15).**

### 9.3 Phase 3: Validation (Sept 2026 - Nov 2026)
- **Focus:** Beta testing and performance tuning.
- **Dependencies:** Successful deployment to Staging.
- **Key Event:** **Milestone 3: External beta with 10 pilot users (2026-11-15).**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Kickoff
**Date:** 2025-11-05  
**Attendees:** Astrid Liu, Bram Jensen, Viktor Kim, Beau Fischer  
**Discussion:**
- Astrid presented the need for a serverless approach to minimize overhead.
- Bram expressed concern over the 128MB memory limit of Cloudflare Workers when parsing large HL7 files.
- Decision: Implement a streaming parser in Rust to handle data in chunks rather than loading files into memory.
- Viktor suggested that the UI should prioritize "Quick Sync" status over detailed logs for the clinician view.

**Action Items:**
- [Bram] Research `wasm-bindgen` performance for streaming parsers. (Due: 2025-11-12)
- [Beau] Draft the initial SQLite schema for local caching. (Due: 2025-11-12)

---

### Meeting 2: Rate Limit Crisis
**Date:** 2026-02-14  
**Attendees:** Astrid Liu, Bram Jensen, Beau Fischer  
**Discussion:**
- The team is currently blocked; the partner API is returning `429` errors even during low-volume testing.
- Beau noted that the current retry logic is "aggressive," which is worsening the rate-limiting.
- Decision: Implement "Exponential Backoff" with jitter. Move the rate-limiting logic to the edge (Cloudflare) to prevent requests from ever leaving the network if the bucket is empty.
- Astrid decided to prioritize the Rate Limiter as a "Launch Blocker."

**Action Items:**
- [Bram] Implement Token Bucket algorithm in the Cloudflare Worker. (Due: 2026-02-21)
- [Astrid] Contact the partner's technical lead to request a temporary limit increase for the staging environment. (Due: 2026-02-15)

---

### Meeting 3: Feature Flag & A/B Testing Review
**Date:** 2026-05-20  
**Attendees:** Astrid Liu, Viktor Kim, Beau Fischer  
**Discussion:**
- Discussion on how to roll out `poll_interval_v2`. 
- Viktor argued that we cannot trust a global rollout without seeing the impact on battery life for the embedded devices.
- Decision: The A/B testing framework is now "Blocked" until we implement a "Device Shadow" (a cloud-side mirror of the device state) to track battery and CPU metrics.
- Decision: Decisions will continue to be made via Slack for speed, but critical architectural changes must be documented here.

**Action Items:**
- [Beau] Research Cloudflare KV for implementing a basic Device Shadow. (Due: 2026-05-27)
- [Viktor] Define the success metrics for the `poll_interval_v2` test. (Due: 2026-05-27)

---

## 11. BUDGET BREAKDOWN

Budget is released in tranches based on the successful completion of Milestones 1, 2, and 3.

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 12-person team | $1,800,000 | Salaried engineers + Project Manager. |
| **Infrastructure** | Cloudflare, D1, KV | $45,000 | Scaling based on tenant growth. |
| **Tools** | GitHub, JetBrains, Slack | $12,000 | Annual licensing. |
| **Hardware** | Prototyping Beacons | $25,000 | 50 test units + components. |
| **Contingency** | 15% Buffer | $282,000 | Reserved for timeline slippage or audit fixes. |
| **TOTAL** | | **$2,164,000** | |

---

## 12. APPENDICES

### Appendix A: Rust Memory Management Strategy
To ensure the firmware operates within the tight constraints of the embedded hardware, the following rules are enforced:
1. **No `std::collections::HashMap`** in the hot path; use fixed-size arrays or `heapless` crates.
2. **Zero-Copy Parsing:** Use the `nom` crate for parsing telemetry data to avoid unnecessary allocations.
3. **SQLite WAL Mode:** Enable Write-Ahead Logging to prevent database locks during simultaneous read/write operations.

### Appendix B: Data Normalization Mapping Table
| Raw Field (HL7) | Beacon Internal Field | Partner API Field | Transformation |
| :--- | :--- | :--- | :--- |
| `PID-3` | `patient_id` | `ext_patient_uuid` | Hash with salt |
| `OBX-5` | `reading_value` | `metric_value` | Convert to Float64 |
| `OBX-11` | `reading_unit` | `unit_code` | Map to ISO-Standard |
| `TS` | `timestamp` | `event_time_utc` | Convert to ISO8601 |