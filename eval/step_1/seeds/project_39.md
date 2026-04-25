# PROJECT SPECIFICATION: WAYFINDER
**Document Version:** 1.0.4  
**Status:** Approved/Baseline  
**Date:** October 24, 2023  
**Company:** Deepwell Data  
**Project Lead:** Luciano Kim (CTO)  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
The "Wayfinder" project is a critical infrastructure overhaul for Deepwell Data. For fifteen years, the company has relied on a legacy firmware/software orchestration system to manage retail embedded assets. This legacy system has reached its architectural ceiling; it is unable to scale to meet the demands of modern retail environments, suffers from monolithic fragility, and lacks the API extensibility required for current market competitiveness. Because the entire organization depends on this system for core operations, any failure results in immediate revenue loss. Consequently, the primary business driver for Wayfinder is the replacement of this legacy system with a modern, scalable, and high-performance architecture with **zero downtime tolerance** during the transition.

The legacy system’s inability to handle current data throughput has created a bottleneck in customer onboarding. As retail clients move toward "Smart Store" configurations, the volume of telemetry and device state changes has increased exponentially. Wayfinder is designed to bridge this gap, providing a robust firmware management layer and a high-performance backend to handle a 10x increase in system capacity.

### 1.2 ROI Projection and Success Metrics
With a total project budget of $1.5M, the financial viability of Wayfinder is anchored in both cost reduction (legacy maintenance) and revenue growth. The project is projected to deliver a positive return on investment within 18 months of the final stability milestone.

**Primary Success Metrics:**
- **Direct Revenue:** $500,000 in new revenue attributed specifically to Wayfinder’s expanded capabilities (specifically the customer-facing API and improved data import/export) within 12 months post-launch.
- **Customer Satisfaction:** Achieve a Net Promoter Score (NPS) above 40 within the first quarter of general availability. This will be measured via automated surveys triggered after the first 30 days of a customer's onboarding.
- **Operational Stability:** Zero unplanned downtime during the migration from the legacy system to Wayfinder.
- **Performance Scaling:** Successful handling of 10x the current request volume per second (RPS) without increasing the baseline infrastructure budget.

### 1.3 Scope Summary
Wayfinder will implement a clean monolith architecture using TypeScript, Next.js, and PostgreSQL. It will provide a sophisticated customer-facing API, a comprehensive notification engine, and advanced data migration tools. The project will follow a strict weekly release train to ensure stability and predictability, avoiding the chaos of unplanned hotfixes.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Overview
Wayfinder utilizes a "Clean Monolith" approach. While the codebase is hosted in a single repository for deployment simplicity (Vercel), the internal logic is strictly partitioned into modules (Domain-Driven Design). This ensures that the system can be decomposed into microservices in the future if the 10x scaling requirements exceed the capacity of a single PostgreSQL instance.

**The Technology Stack:**
- **Frontend/Backend Framework:** Next.js (TypeScript) utilizing App Router for optimized server-side rendering and API route handling.
- **Database Layer:** PostgreSQL 15.x hosted on a managed instance.
- **ORM:** Prisma (used for 70% of queries to ensure type safety).
- **Performance Layer:** Raw SQL (used for 30% of queries where Prisma's overhead causes latency spikes, particularly in telemetry aggregation).
- **Deployment:** Vercel (Edge functions for low-latency API responses).

### 2.2 System Component Diagram (ASCII)
The following diagram represents the flow of data from the embedded retail hardware through the Wayfinder backend to the end user.

```text
[ Retail Embedded Hardware ]  <-- Firmware Updates/Heartbeats
          |
          | (HTTPS/TLS 1.3)
          v
[ Vercel Edge Network ]  <-- Request Routing & Rate Limiting
          |
          +-----------------------+-----------------------+
          |                       |                       |
[ API Gateway / Routes ]   [ Auth Layer ]         [ Feature Flag Service ]
          |                       |                       |
          v                       v                       v
[ Service Layer (TS) ] <--> [ Prisma ORM ] <--> [ PostgreSQL Database ]
          |                       |                       |
          |                       +--> [ Raw SQL Queries ] (Perf Critical)
          v
[ Notification Engine ] --> [ AWS SES (Email) / Twilio (SMS) / FCM (Push) ]
          |
          v
[ Customer Dashboard (Next.js) ]
```

### 2.3 Module Boundaries
To prevent the monolith from becoming "spaghetti code," the following boundaries are enforced:
- **Core Domain:** Handles the business logic of device state and retail configuration.
- **Integration Layer:** Manages the Customer API and external SAML/OIDC providers.
- **Infrastructure Layer:** Handles database migrations, logging, and Vercel deployment configurations.
- **Notification Module:** An isolated event-bus system that triggers alerts based on domain events.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API (Critical - Launch Blocker)
**Status:** In Progress | **Priority:** Critical

The Customer-Facing API is the primary vehicle for Wayfinder’s value proposition. It allows retail clients to programmatically manage their embedded devices, retrieve telemetry, and push configuration updates without manual dashboard intervention.

**Functional Requirements:**
- **Versioning:** The API must use URI-based versioning (e.g., `/api/v1/...`). All versions must be supported for 12 months after a new version is released.
- **Sandbox Environment:** A completely isolated "Sandbox" environment must be provided for every paying customer. Data in the sandbox must be logically separated from production data to prevent accidental production outages during testing.
- **Authentication:** API keys must be generated via the dashboard, with support for rotation and scoped permissions (Read-Only, Read-Write, Admin).
- **Rate Limiting:** Implemented via a sliding window algorithm (1,000 requests per minute per API key) to prevent system saturation.

**Technical Implementation:**
The API is built using Next.js API routes. Request validation is handled via Zod to ensure that only well-formed JSON reaches the service layer. To meet the 10x performance requirement, GET endpoints for telemetry data bypass Prisma and use raw SQL with optimized indexes on the `device_id` and `timestamp` columns.

**Acceptance Criteria:**
- A user can generate an API key in the dashboard and successfully call the `/v1/devices` endpoint.
- A request to the sandbox environment does not affect production data.
- The system returns a `429 Too Many Requests` error when rate limits are exceeded.

### 3.2 Data Import/Export with Format Auto-Detection (Critical - Launch Blocker)
**Status:** In Review | **Priority:** Critical

Because Wayfinder is replacing a 15-year-old system, the ability to migrate legacy data without manual script-writing is paramount. The import/export system must handle massive datasets (millions of rows) without locking the database.

**Functional Requirements:**
- **Auto-Detection:** The system must detect if the uploaded file is CSV, JSON, or XML based on magic bytes and header analysis.
- **Mapping Interface:** A UI-based mapper allowing users to link legacy column names (e.g., `dev_id_old`) to Wayfinder schema fields (e.g., `device_uuid`).
- **Asynchronous Processing:** Large imports must be processed in the background using a job queue. The user receives a notification once the import is complete.
- **Export Scheduling:** Users can schedule weekly exports of their device logs in their preferred format.

**Technical Implementation:**
The import engine uses a streaming parser (PapaParse for CSV) to avoid loading entire files into memory. Data is written to a temporary "staging" table before being validated and merged into the primary tables via a single transaction to ensure atomicity.

**Acceptance Criteria:**
- Successfully importing a 500MB CSV file without timing out the HTTP request.
- Correct identification of a JSON file vs a CSV file without the user specifying the format.
- Exporting a filtered list of devices to XML format.

### 3.3 Notification System (High)
**Status:** In Review | **Priority:** High

The notification system serves as the alerting engine for the retail embedded fleet. It must ensure that critical firmware failures are communicated to the right personnel immediately.

**Functional Requirements:**
- **Multi-Channel Delivery:** Support for Email (transactional), SMS (urgent), In-App (notifications center), and Push (mobile apps).
- **Preference Center:** Customers can toggle which channels they wish to use for specific alert types (e.g., "Critical Error" $\rightarrow$ SMS + Email; "Firmware Update Success" $\rightarrow$ In-App only).
- **Templating:** A dynamic template system using Handlebars, allowing for personalized messages (e.g., "Device [DeviceID] in Store [StoreName] is offline").
- **Retry Logic:** Exponential backoff for failed deliveries (3 retries over 1 hour).

**Technical Implementation:**
The system uses an event-driven architecture. When a domain event (e.g., `DEVICE_OFFLINE`) is triggered, the `NotificationService` checks the user's preferences in the database and dispatches the message to the respective provider (AWS SES for email, Twilio for SMS).

**Acceptance Criteria:**
- A triggered "Critical" event results in both an SMS and an Email being sent within 60 seconds.
- A user can disable SMS notifications in the dashboard, and subsequent events only trigger Emails.

### 3.4 SSO Integration (Low)
**Status:** In Review | **Priority:** Low

To facilitate enterprise adoption, Wayfinder must integrate with existing corporate identity providers.

**Functional Requirements:**
- **SAML 2.0 Support:** Integration with providers like Okta and Azure AD.
- **OIDC Support:** Integration with Google Workspace and other OpenID Connect providers.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user account upon their first successful SSO login if they belong to a verified corporate domain.
- **Attribute Mapping:** Ability to map SAML assertions to internal user roles (e.g., `MemberOf: Retail_Admins` $\rightarrow$ `Role: ADMIN`).

**Technical Implementation:**
Implemented using `next-auth` (Auth.js) with custom providers for SAML and OIDC. The session is managed via JWTs stored in encrypted cookies.

**Acceptance Criteria:**
- A user can log in using their corporate Okta account without a Wayfinder-specific password.
- The user is automatically assigned the correct role based on their SAML group membership.

### 3.5 A/B Testing Framework (Low)
**Status:** In Design | **Priority:** Low

The A/B testing framework is baked into the feature flag system to allow for data-driven decisions regarding the user interface and API behavior.

**Functional Requirements:**
- **Cohort Assignment:** Users are randomly assigned to "Control" or "Test" groups based on a hash of their `user_id`.
- **Flag Evaluation:** The frontend and backend can query the flag state to determine which feature version to display.
- **Metric Tracking:** Integration with the telemetry system to track which cohort has a higher conversion or success rate.
- **Gradual Rollout:** Ability to shift the percentage of users in the "Test" group from 0% to 100% over time.

**Technical Implementation:**
The framework utilizes a `feature_flags` table and a `user_cohorts` table. The logic for bucket assignment is handled at the Edge (Vercel Middleware) to prevent "flicker" during page loads.

**Acceptance Criteria:**
- Two different versions of a dashboard widget are shown to two different sets of users.
- The project lead can change the rollout percentage from 10% to 20% via the admin panel.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `X-API-Key` header for authentication.

### 4.1 Device Management

**`GET /devices`**
- **Description:** Returns a paginated list of all embedded devices.
- **Query Params:** `page` (int), `limit` (int), `status` (string).
- **Request Example:** `GET /api/v1/devices?page=1&limit=20`
- **Response Example:**
  ```json
  {
    "data": [
      { "id": "dev_01", "name": "Store-1-Reg1", "status": "online", "version": "2.4.1" }
    ],
    "pagination": { "total": 150, "pages": 8 }
  }
  ```

**`POST /devices`**
- **Description:** Registers a new device in the system.
- **Request Body:** `{ "name": "string", "serial_number": "string", "store_id": "uuid" }`
- **Response Example:**
  ```json
  { "id": "dev_99", "status": "provisioning", "created_at": "2023-10-24T10:00:00Z" }
  ```

**`PATCH /devices/{id}`**
- **Description:** Updates device configuration or metadata.
- **Request Body:** `{ "name": "New Name", "tags": ["priority-high"] }`
- **Response Example:** `{ "id": "dev_01", "updated": true }`

**`DELETE /devices/{id}`**
- **Description:** Decommissions a device and archives its data.
- **Response Example:** `{ "status": "archived", "timestamp": "..." }`

### 4.2 Telemetry and Logs

**`GET /telemetry/{id}`**
- **Description:** Retrieves the latest telemetry snapshot for a device.
- **Response Example:**
  ```json
  {
    "device_id": "dev_01",
    "metrics": { "cpu_usage": "12%", "mem_usage": "45%", "temp": "42C" },
    "timestamp": "2023-10-24T12:00:00Z"
  }
  ```

**`GET /logs/{id}`**
- **Description:** Retrieves device logs filtered by severity.
- **Query Params:** `severity` (ERROR, WARN, INFO).
- **Response Example:**
  ```json
  [
    { "timestamp": "...", "level": "ERROR", "message": "Connection timeout on port 8080" }
  ]
  ```

### 4.3 System and Account

**`GET /account/usage`**
- **Description:** Returns current API usage and quota.
- **Response Example:** `{ "requests_this_month": 45000, "quota": 100000, "percent": 45 }`

**`POST /sandbox/reset`**
- **Description:** Wipes all data in the sandbox environment for a fresh start.
- **Response Example:** `{ "status": "success", "message": "Sandbox environment purged." }`

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15 instance. Due to performance requirements, several views and materialized views are used for reporting.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | `org_id` | - | `name`, `plan_type`, `created_at` | Top-level retail client entity. |
| `users` | `user_id` | `org_id` | `email`, `password_hash`, `role` | System users and authentication. |
| `devices` | `device_id` | `org_id` | `serial_number`, `firmware_version`, `status` | The embedded hardware assets. |
| `stores` | `store_id` | `org_id` | `store_code`, `location_zip`, `timezone` | Physical retail locations. |
| `device_config` | `config_id` | `device_id` | `config_json`, `applied_at`, `version` | History of configuration changes. |
| `telemetry` | `entry_id` | `device_id` | `cpu_load`, `mem_load`, `timestamp` | Time-series performance data. |
| `logs` | `log_id` | `device_id` | `severity`, `message`, `timestamp` | System event logs. |
| `api_keys` | `key_id` | `user_id` | `hashed_key`, `scope`, `expires_at` | Authentication keys for API. |
| `notifications` | `notify_id` | `user_id` | `channel`, `message`, `is_read` | Outbound alert history. |
| `feature_flags` | `flag_id` | - | `key`, `is_enabled`, `rollout_percentage` | System toggle settings. |

### 5.2 Relationships
- `organizations` $\rightarrow$ `users` (One-to-Many)
- `organizations` $\rightarrow$ `stores` (One-to-Many)
- `stores` $\rightarrow$ `devices` (One-to-Many)
- `devices` $\rightarrow$ `telemetry` (One-to-Many)
- `devices` $\rightarrow$ `logs` (One-to-Many)
- `users` $\rightarrow$ `api_keys` (One-to-Many)

### 5.3 Migration Strategy
Because 30% of the queries bypass the ORM (Prisma), all migrations must be manually reviewed by the Senior Backend Engineer. The `prisma migrate` command is used for schema changes, but custom SQL scripts are run via a migration runner to handle complex index optimizations on the `telemetry` table.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Wayfinder utilizes a three-tier environment strategy to ensure zero-downtime deployments.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and internal testing.
- **Database:** Shared development DB with mocked data.
- **Deployment:** Automatic on push to `develop` branch.
- **Access:** Restricted to the 12-person team.

#### 6.1.2 Staging (`staging`)
- **Purpose:** QA, User Acceptance Testing (UAT), and Beta testing.
- **Database:** Anonymized clone of production data.
- **Deployment:** Triggered via JIRA ticket approval; occurs every Tuesday.
- **Access:** Team + 10 pilot users (Milestone 1).

#### 6.1.3 Production (`prod`)
- **Purpose:** Live retail operations.
- **Database:** High-availability PostgreSQL cluster with read-replicas.
- **Deployment:** The "Weekly Release Train."
- **Access:** All paying customers.

### 6.2 The Weekly Release Train
To maintain the "zero downtime" requirement, Wayfinder prohibits ad-hoc hotfixes.
- **Cycle:** Every Thursday at 03:00 UTC.
- **Process:** `Develop` $\rightarrow$ `Staging` $\rightarrow$ `Production`.
- **Cut-off:** All code must be merged into the release branch by Tuesday 23:59 UTC.
- **Rollback:** If a critical bug is found post-release, the entire system is rolled back to the previous stable version. Fixes are then queued for the next train.

### 6.3 Infrastructure Budgeting
The infrastructure budget is fixed. To achieve the 10x capacity increase without more funding, the team is implementing:
- **Database Indexing:** Strategic use of BRIN indexes for the `telemetry` table.
- **Edge Caching:** Using Vercel's Edge Network to cache common API responses for 60 seconds.
- **Query Optimization:** Replacing expensive Prisma `include` calls with targeted raw SQL joins.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** Jest + Vitest.
- **Coverage Goal:** 80% across all service layer logic.
- **Focus:** Business logic, Zod validation schemas, and utility functions.
- **Execution:** Run on every push via GitHub Actions.

### 7.2 Integration Testing
- **Framework:** Supertest + Prisma Mock.
- **Focus:** Testing the interaction between the API routes, the service layer, and the database.
- **Key Scenarios:** 
  - Verifying that a `DELETE /devices` request correctly archives the device and removes its active status.
  - Ensuring that the `NotificationService` correctly dispatches to the right provider based on user settings.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Focus:** Critical user journeys (e.g., "Onboard New Store", "Generate API Key", "Run Data Import").
- **Execution:** Run on the `staging` environment before every weekly release train.

### 7.4 Penetration Testing
As there is no specific compliance framework (like SOC2), Deepwell Data will contract an external security firm for **quarterly penetration tests**. These tests will specifically target the API endpoints and the SSO integration to ensure no privilege escalation is possible.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor dependency announces End-of-Life (EOL). | High | Critical | Escalate to steering committee immediately for additional funding to build a custom alternative or migrate vendors. |
| **R-02** | Performance requirements (10x) exceed current infra budget. | Medium | High | De-scope non-critical features (e.g., A/B testing) to save compute resources if unresolved by Milestone 2. |
| **R-03** | Dangerous migrations due to Raw SQL usage (Technical Debt). | High | Medium | Implement a mandatory "SQL Review" step in the PR process; use a dedicated migration tool that validates schema changes. |
| **R-04** | Legal review of Data Processing Agreement (DPA) delays launch. | Medium | High | (Current Blocker) Daily follow-ups with the legal department. Prepare technical data-mapping docs to expedite review. |

**Probability/Impact Matrix:**
- **Critical:** Immediate threat to project viability or business continuity.
- **High:** Significant delay or performance degradation.
- **Medium:** Manageable issue with clear workaround.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with strict dependencies.

### 9.1 Phase 1: Foundation (Now $\rightarrow$ May 2026)
- **Focus:** Core API, Data Import/Export, and Basic Dashboard.
- **Dependencies:** Legal review of DPA must be completed.
- **Target:** **Milestone 1 (2026-05-15): External beta with 10 pilot users.**

### 9.2 Phase 2: Monetization (May 2026 $\rightarrow$ July 2026)
- **Focus:** SSO Integration, Billing integration, and Performance Tuning.
- **Dependencies:** Successful completion of Beta testing.
- **Target:** **Milestone 2 (2026-07-15): First paying customer onboarded.**

### 9.3 Phase 3: Optimization (July 2026 $\rightarrow$ Sept 2026)
- **Focus:** Notification system polish, A/B testing framework, and final scaling tests.
- **Dependencies:** Stable performance under real load from paying customers.
- **Target:** **Milestone 3 (2026-09-15): Post-launch stability confirmed.**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-01 | **Participants:** Luciano Kim, Isadora Costa, Elio Jensen
- **Discussion:** The team debated using a microservices architecture from the start. Isadora argued that the overhead of managing 5-10 services would slow down the 12-person team. Luciano decided on a "Clean Monolith" to maintain velocity while ensuring strict module boundaries.
- **Decision:** Use a monolith with TypeScript/Next.js.
- **Action Item:** Isadora to define the folder structure for module boundaries. (Owner: Isadora)

### Meeting 2: Performance Crisis Review
**Date:** 2023-12-15 | **Participants:** Luciano Kim, Isadora Costa, Elio Jensen
- **Discussion:** Elio reported that Prisma was adding 200ms of latency to the telemetry endpoints. The 10x scaling requirement makes this unacceptable. Isadora suggested bypassing the ORM for high-volume read queries.
- **Decision:** Allow raw SQL for the 30% of queries that are performance-critical.
- **Action Item:** Create a "Raw SQL Registry" to track all non-ORM queries for migration safety. (Owner: Elio)

### Meeting 3: Vendor EOL Escalation
**Date:** 2024-02-10 | **Participants:** Luciano Kim, Steering Committee
- **Discussion:** The primary hardware vendor announced the EOL of the legacy communication protocol. This threatens the "zero downtime" migration.
- **Decision:** Luciano to request an emergency $100k budget increase from the steering committee to accelerate the development of a custom protocol bridge.
- **Action Item:** Luciano to present the detailed cost-benefit analysis to the Board. (Owner: Luciano)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $1,050,000 | 12-person team (Avg $87.5k/person/year across project duration). |
| **Infrastructure** | 15% | $225,000 | Vercel Enterprise, Managed PostgreSQL, AWS SES/Twilio. |
| **Tools & Licensing** | 5% | $75,000 | JIRA, GitHub Enterprise, Pen-testing contracts. |
| **Contingency** | 10% | $150,000 | Reserved for Vendor EOL mitigation and emergency scaling. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Performance Guidelines
To prevent the "Technical Debt" risk associated with bypassing Prisma, all raw SQL must adhere to these rules:
1. **Parameterization:** No string concatenation for queries; always use `$1, $2` placeholders to prevent SQL injection.
2. **Indexing:** Every raw query must be accompanied by an `EXPLAIN ANALYZE` output in the PR.
3. **Explicit Typing:** Results must be cast back into TypeScript interfaces immediately upon retrieval.

### Appendix B: Feature Flag Logic Flow
The A/B testing logic follows this sequence:
1. **Request Received:** Vercel Middleware intercepts the request.
2. **Identity Check:** Retrieve `user_id` from the session cookie.
3. **Hash Bucket:** `hash(user_id + flag_key) % 100`.
4. **Comparison:** If result is less than `rollout_percentage` in `feature_flags` table, set flag to `TRUE`.
5. **Injection:** The flag state is passed as a header to the Next.js page, which renders the corresponding UI component.