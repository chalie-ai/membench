Due to the extreme length requirements of this request (6,000–8,000 words), this document is presented as a comprehensive, professional Technical Specification Document (TSD). It is structured as the "Source of Truth" for the Ironclad project at Duskfall Inc.

***

# PROJECT SPECIFICATION: PROJECT IRONCLAD
**Document Version:** 1.0.4  
**Status:** Draft/Review  
**Date:** October 24, 2025  
**Classification:** Duskfall Inc. Internal / Proprietary  
**Project Lead:** Ola Costa (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ironclad is a strategic enterprise integration tool developed by Duskfall Inc. to facilitate a high-stakes partnership within the aerospace industry. The primary objective of Ironclad is to create a robust, high-performance synchronization layer between Duskfall’s internal aerospace telemetry and logistics systems and an external partner’s proprietary API. Because the project is contingent upon the external partner's development timeline, Ironclad is designed as a flexible middleware system capable of adapting to shifting API specifications while maintaining strict data integrity and high availability.

### 1.2 Business Justification
In the aerospace sector, synchronization of supply chain and component telemetry is critical for safety and regulatory compliance. Currently, Duskfall Inc. relies on manual data imports and fragmented legacy scripts to communicate with this strategic partner. This leads to a "data lag" of up to 48 hours, increasing the risk of procurement errors and delaying assembly timelines. 

Ironclad will automate this integration, providing real-time visibility into the partner's capacity and shipment status. By implementing a Rust-based backend and a Cloudflare-distributed edge layer, Duskfall will reduce data latency from 48 hours to under 300 milliseconds.

### 1.3 ROI Projection
The project is allocated a budget of $1.5M. The projected Return on Investment (ROI) is calculated based on three primary drivers:
1. **Reduction in Manual Labor:** Automation of the sync process is expected to save 4,200 man-hours per year across the logistics and engineering departments, valued at approximately $420,000/year.
2. **Error Mitigation:** Reducing "wrong-part" procurement errors caused by stale data is projected to save $600,000 annually in wasted materials and shipping costs.
3. **Accelerated Time-to-Market:** By streamlining the partnership integration, the lead time for new aerospace component iterations is expected to drop by 12%, resulting in an estimated $1.2M in additional quarterly revenue.

The total projected first-year benefit is $2.22M, providing a positive ROI within the first nine months of full deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Ironclad utilizes a traditional three-tier architecture (Presentation, Business Logic, Data) optimized for edge computing to ensure low latency across Duskfall’s distributed global offices.

**The Stack:**
- **Frontend:** React 18.x (TypeScript) with Tailwind CSS for the administrative dashboard.
- **Backend:** Rust (Axum framework) for high-performance, memory-safe business logic.
- **Edge/Compute:** Cloudflare Workers for request routing and lightweight logic.
- **Database:** SQLite (via LiteFS/Turso) for edge data persistence and local caching.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ User Browser / Client ] 
          |
          v
[ Cloudflare Edge Network ] <--- (Global Traffic Management)
          |
          +---- [ Cloudflare Workers ] (Auth / Rate Limiting / Routing)
          |           |
          |           v
          |    [ Rust Backend (Axum) ] <--- (Business Logic Tier)
          |           |
          |           +---- [ External Partner API ] (External Sync)
          |           |
          |           v
          |    [ SQLite / LiteFS ] <--- (Data Persistence Tier)
          |           |
          +-----------+
```

### 2.3 Component Breakdown
1. **Presentation Tier:** A React SPA hosted on Cloudflare Pages. It provides the interface for monitoring sync status, adjusting rate limits, and managing API keys.
2. **Business Logic Tier:** A compiled Rust binary deployed as a set of microservices. Rust was chosen to prevent memory-related crashes and provide the speed necessary for processing massive aerospace telemetry datasets.
3. **Data Tier:** SQLite is used at the edge to provide near-instantaneous reads. Data is replicated across regions using LiteFS to ensure that a failure in one geographic zone does not result in data loss.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Functional Specification:**
The system must implement a sophisticated rate-limiting mechanism to protect both Duskfall’s internal infrastructure and the external partner’s API from exhaustion. This feature is a launch blocker because the external partner has mandated strict request quotas; exceeding these quotas will result in a 30-day IP ban.

The rate limiter will implement a "Token Bucket" algorithm. Every API key associated with the partner integration will be assigned a bucket with a maximum capacity (e.g., 1,000 requests) and a refill rate (e.g., 10 requests per second). When a request arrives, the system checks if a token is available. If the bucket is empty, the system returns a `429 Too Many Requests` response.

**Usage Analytics requirements:**
The system must track and visualize the following metrics in the React dashboard:
- Total requests per hour/day/month.
- Percentage of requests resulting in 4xx or 5xx errors.
- Latency spikes relative to the external partner's API response times.
- Top 5 most utilized endpoints.

**Technical implementation:**
Rate limit state will be stored in a distributed Redis cache (integrated via Cloudflare Workers KV) to ensure that limits are enforced globally and not just per-instance. Analytics will be aggregated asynchronously via a background worker to avoid adding latency to the primary request path.

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** Blocked (Waiting on External Partner)

**Functional Specification:**
Ironclad will expose a RESTful API that allows other internal Duskfall departments to query the synced data from the external partner. To ensure stability, the API must support semantic versioning (e.g., `/v1/`, `/v2/`).

**Versioning Strategy:**
The system will use URI-based versioning. When a new version is released, the previous version will remain supported for a period of six months. The Rust backend will utilize a routing trait to map versioned paths to specific handler functions, ensuring that breaking changes in the external partner's API do not break internal Duskfall tools.

**Sandbox Environment:**
A complete mirror of the production environment—the "Sandbox"—will be provided. The Sandbox will use a mocked version of the external partner's API. This allows internal developers to test their integrations without risking the production rate limits or altering real-world aerospace data. The Sandbox will be isolated in a separate SQLite database instance.

**Blocking Dependency:**
Development is currently blocked because the external partner has not yet released their "Partner SDK v2.0," which defines the data structures required for the v1 Ironclad API.

### 3.3 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** Not Started

**Functional Specification:**
Given that some aerospace engineers operate in "dead zones" (hangars with poor connectivity), the Ironclad dashboard must support offline-first functionality. 

**Mechanism:**
The React frontend will utilize a Service Worker to cache the application shell and a local IndexedDB instance to store a subset of the most recent sync data. When a user performs an action while offline (e.g., flagging a shipment as "reviewed"), the action will be stored in an "Outbox" queue within IndexedDB.

**Background Sync:**
Using the Background Sync API, the browser will automatically push the Outbox queue to the Rust backend once the connection is restored. The backend must implement "Idempotency Keys" for every request to ensure that if a sync operation is retried due to a flaky connection, the data is not duplicated in the SQLite database.

### 3.4 User Authentication and RBAC
**Priority:** Low | **Status:** Not Started

**Functional Specification:**
While Ironclad is an internal tool, access must be restricted based on the user's role within Duskfall Inc. The system will integrate with Duskfall's corporate Azure AD (Active Directory) via OAuth2/OpenID Connect.

**Role-Based Access Control (RBAC) Matrix:**
- **Viewer:** Can view analytics and sync status. Cannot change rate limits or API keys.
- **Operator:** Can trigger manual syncs and modify notification settings.
- **Administrator:** Full access, including the ability to rotate API keys and modify the rate-limiting bucket sizes.

**Implementation:**
JWTs (JSON Web Tokens) will be issued upon successful Azure AD authentication. These tokens will contain the user's role in the payload. The Rust backend will use a middleware layer to intercept requests and verify that the user's role has the necessary permissions for the requested endpoint.

### 3.5 Notification System (Email, SMS, In-App, Push)
**Priority:** High | **Status:** In Review

**Functional Specification:**
The notification system is designed to alert the operations team when the sync process fails or when the external partner's API returns critical errors.

**Notification Channels:**
1. **Email:** Sent via SendGrid for detailed error reports and weekly summaries.
2. **SMS:** Sent via Twilio for "Critical" alerts (e.g., API Ban, System Down).
3. **In-App:** A notification bell in the React dashboard using WebSockets for real-time alerts.
4. **Push:** Browser push notifications for operators who have the dashboard open in the background.

**Logic Flow:**
The system will utilize a "Notification Dispatcher" service. When an event occurs (e.g., `SYNC_FAILURE`), the dispatcher checks the user's preference matrix. If the alert is "Critical," it triggers all four channels. If it is "Warning," it only triggers Email and In-App.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `X-Ironclad-API-Key` header.

### 4.1 GET `/sync/status`
**Description:** Returns the current status of the external API synchronization.
- **Request:** `GET /api/v1/sync/status`
- **Response (200 OK):**
```json
{
  "status": "synchronized",
  "last_sync_time": "2026-08-12T14:30:00Z",
  "pending_records": 0,
  "health": "healthy"
}
```

### 4.2 POST `/sync/trigger`
**Description:** Manually forces a synchronization cycle.
- **Request:** `POST /api/v1/sync/trigger` | Body: `{ "force_full_refresh": true }`
- **Response (202 Accepted):**
```json
{
  "job_id": "sync_992834",
  "estimated_completion": "2026-08-12T14:35:00Z"
}
```

### 4.3 GET `/analytics/usage`
**Description:** Retrieves rate limit usage for the current window.
- **Request:** `GET /api/v1/analytics/usage?period=hour`
- **Response (200 OK):**
```json
{
  "limit": 1000,
  "used": 452,
  "remaining": 548,
  "reset_time": "2026-08-12T15:00:00Z"
}
```

### 4.4 PATCH `/config/rate-limits`
**Description:** Updates the token bucket size (Admin only).
- **Request:** `PATCH /api/v1/config/rate-limits` | Body: `{ "bucket_size": 2000, "refill_rate": 20 }`
- **Response (200 OK):**
```json
{
  "updated": true,
  "new_limit": 2000
}
```

### 4.5 GET `/data/telemetry/{id}`
**Description:** Fetches a specific aerospace component telemetry record.
- **Request:** `GET /api/v1/data/telemetry/PART-9901`
- **Response (200 OK):**
```json
{
  "part_id": "PART-9901",
  "status": "In Transit",
  "location": "Warehouse-B",
  "timestamp": "2026-08-12T10:00:00Z"
}
```

### 4.6 POST `/notifications/settings`
**Description:** Updates user notification preferences.
- **Request:** `POST /api/v1/notifications/settings` | Body: `{ "email": true, "sms": false, "push": true }`
- **Response (200 OK):**
```json
{ "message": "Preferences updated successfully" }
```

### 4.7 GET `/health`
**Description:** Simple heartbeat endpoint for monitoring.
- **Request:** `GET /api/v1/health`
- **Response (200 OK):**
```json
{ "status": "up", "version": "1.0.4", "uptime": 86400 }
```

### 4.8 DELETE `/cache/flush`
**Description:** Clears the edge SQLite cache (Admin only).
- **Request:** `DELETE /api/v1/cache/flush`
- **Response (204 No Content):** `(Empty)`

---

## 5. DATABASE SCHEMA

Ironclad uses SQLite for its lean footprint and edge compatibility.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email`, `role_id`, `last_login` | Internal Duskfall users. |
| `roles` | `role_id` | - | `role_name`, `permissions_bitmask` | RBAC role definitions. |
| `api_keys` | `key_id` | `user_id` | `hashed_key`, `created_at`, `expires_at` | Keys for API access. |
| `sync_logs` | `log_id` | - | `timestamp`, `records_processed`, `status` | Audit trail of sync jobs. |
| `telemetry_data` | `part_id` | - | `external_ref_id`, `payload`, `updated_at` | The core mirrored data. |
| `rate_limits` | `limit_id` | - | `endpoint_path`, `bucket_size`, `refill_rate` | Config for rate limiting. |
| `usage_stats` | `stat_id` | `key_id` | `request_count`, `timestamp`, `response_code` | Granular usage tracking. |
| `notifications` | `notify_id` | `user_id` | `channel`, `message`, `is_read`, `created_at` | Notification history. |
| `user_preferences`| `pref_id` | `user_id` | `email_enabled`, `sms_enabled`, `push_enabled` | Notification settings. |
| `external_partner_config` | `config_id` | - | `api_endpoint`, `auth_token_secret`, `timeout_ms` | Connection settings. |

### 5.2 Relationships
- `users` $\rightarrow$ `roles` (Many-to-One): Each user has one primary role.
- `users` $\rightarrow$ `api_keys` (One-to-Many): A user can generate multiple keys.
- `users` $\rightarrow$ `user_preferences` (One-to-One): Each user has one set of preferences.
- `api_keys` $\rightarrow$ `usage_stats` (One-to-Many): Each key generates many usage entries.
- `users` $\rightarrow$ `notifications` (One-to-Many): Users receive multiple notifications.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Architecture
Ironclad maintains three distinct environments to ensure stability.

**1. Development (Dev):**
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Local Docker containers and a shared "Dev" Cloudflare Worker.
- **Database:** Local SQLite files.
- **Deployment:** Automatic on git push to `develop` branch.

**2. Staging (Stage):**
- **Purpose:** Pre-production validation and stakeholder demos.
- **Infrastructure:** Cloudflare Workers (Staging Namespace) and a Turso SQLite cluster.
- **Database:** Mirror of production schema with anonymized data.
- **Deployment:** Manual trigger from the `release` branch.

**3. Production (Prod):**
- **Purpose:** Live strategic partnership integration.
- **Infrastructure:** Global Cloudflare Edge Network with Rust binaries deployed via WASM.
- **Database:** Distributed SQLite via LiteFS.
- **Deployment:** **Manual deployment performed by a single DevOps person.**

### 6.2 The "Bus Factor" Warning
It is formally noted that the deployment process is entirely manual and managed by a single individual. This creates a "Bus Factor of 1." If the DevOps lead is unavailable, the project cannot be deployed to production. This is a recognized risk and a target for future remediation.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend (Rust):** Using `cargo test`. We require 80% coverage on all business logic handlers and data transformation functions.
- **Frontend (React):** Using Vitest for utility functions and Jest for component logic.

### 7.2 Integration Testing
- **API Contracts:** We use Prism to mock the external partner's API. Integration tests verify that the Rust backend correctly handles `429` (Rate Limit) and `503` (Service Unavailable) responses from the partner.
- **Database:** Integration tests are run against a temporary SQLite in-memory database to verify schema migrations and query performance.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical paths are tested in Staging, including:
    - User login $\rightarrow$ Dashboard $\rightarrow$ Trigger Manual Sync $\rightarrow$ Verify Status Change.
    - Changing a rate limit $\rightarrow$ Verifying a request is blocked at the 1,001st attempt.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut of 30% in next fiscal quarter. | Medium | High | Accept risk; monitor weekly. Prioritize critical features (Rate Limiting) over low-priority ones (RBAC). |
| R-02 | Scope creep from stakeholders (small features). | High | Medium | Document all "small" requests as workarounds and share with the team to maintain visibility. |
| R-03 | Dependency on external partner API deliverables. | High | High | (Current Blocker) Maintain daily contact; build mocks based on available documentation. |
| R-04 | DevOps Single Point of Failure (Bus Factor 1). | Low | Critical | Document deployment steps in a README; cross-train Ola Costa on basic deployment scripts. |

**Impact Matrix:**
- **Critical:** Project stoppage or catastrophic data loss.
- **High:** Significant delay in milestones or loss of key functionality.
- **Medium:** Manageable delay; requires reallocation of resources.
- **Low:** Negligible impact on launch date.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases
1. **Phase 1: Foundation (Jan 2026 - Aug 2026)**
   - Setup Rust boilerplate, Cloudflare environment, and SQLite schema.
   - Implement basic connectivity to external partner's API.
2. **Phase 2: Core Logic (Aug 2026 - Oct 2026)**
   - Development of Rate Limiting and Analytics.
   - Implementation of the sync engine.
3. **Phase 3: Refinement & UI (Oct 2026 - Dec 2026)**
   - React dashboard completion.
   - Notification system integration.
   - Final E2E testing.

### 9.2 Critical Milestones
- **Milestone 1: Architecture Review Complete**
  - **Target Date:** 2026-08-15
  - **Dependency:** Final approval of the SQLite schema by the Tech Lead.
- **Milestone 2: Performance Benchmarks Met**
  - **Target Date:** 2026-10-15
  - **Requirement:** Sync 100,000 records in under 60 seconds with < 1% error rate.
- **Milestone 3: Stakeholder Demo and Sign-off**
  - **Target Date:** 2026-12-15
  - **Requirement:** Successful demonstration of the Sandbox environment and Rate Limiting.

---

## 10. MEETING NOTES

### Meeting 1: Initial Sprint Planning
**Date:** 2025-11-02  
**Attendees:** Ola, Yara, Farid, Beatriz  
- Rust stack confirmed.
- SQLite for edge—discuss LiteFS.
- Need Azure AD for auth.
- Farid worried about API keys in plain text.

### Meeting 2: Partner API Sync Update
**Date:** 2025-12-15  
**Attendees:** Ola, Yara  
- Partner is 3 weeks behind.
- Blocked on v2.0 SDK.
- Yara to build mocks.
- Ola says "don't wait," build the shell.

### Meeting 3: Budget and Risk Review
**Date:** 2026-01-20  
**Attendees:** Ola, Finance Rep  
- 30% cut possible next Q.
- Ola: "We'll just watch it."
- Stakeholders asking for "small" export-to-CSV feature.
- Decision: Document as workaround.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $1,100,000 | 15 engineers (distributed) across 5 countries for 18 months. |
| **Infrastructure** | $150,000 | Cloudflare Workers, Turso/SQLite clusters, Azure AD licenses. |
| **Tools & Software** | $50,000 | JIRA, Slack Enterprise, SendGrid, Twilio, Playwright Cloud. |
| **Contingency** | $200,000 | Reserved for emergency scaling or unexpected partner API changes. |

---

## 12. APPENDICES

### Appendix A: Rust Configuration Details
To ensure consistent builds across the distributed team, the following `Cargo.toml` profiles are mandated:
- **Optimization:** `opt-level = "z"` (Optimize for size to fit Cloudflare Worker limits).
- **LTO:** `lto = true` (Link Time Optimization enabled).
- **Panic:** `panic = "abort"` (To reduce binary size).

### Appendix B: External API Error Mapping
The following table defines how external partner errors are mapped to Ironclad's internal responses:

| Partner Error Code | Ironclad Internal Code | Action |
| :--- | :--- | :--- |
| `ERR_LIMIT_EXCEEDED` | `429 Too Many Requests` | Trigger Rate Limit alert; back off 30s. |
| `ERR_AUTH_FAIL` | `500 Internal Server Error` | Trigger "Critical" SMS notification to Admin. |
| `ERR_DATA_MALFORMED`| `422 Unprocessable Entity`| Log to `sync_logs` and skip record. |
| `ERR_TIMEOUT` | `504 Gateway Timeout` | Retry 3 times with exponential backoff. |