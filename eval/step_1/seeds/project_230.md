Due to the extreme length requirements (6,000–8,000 words) and the structural complexity of a formal project specification, this document is presented as a comprehensive, industrial-grade Technical Specification Document (TSD). 

***

# PROJECT GLACIER: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Date:** October 24, 2024  
**Status:** Active / In-Development  
**Company:** Bellweather Technologies  
**Project Lead:** Alejandro Nakamura  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Glacier represents a strategic "pivot-and-rebuild" initiative for Bellweather Technologies. Following the deployment of our previous agricultural ML model interface, user feedback was catastrophic, citing extreme latency, unintuitive UX, and a failure to handle field-level connectivity issues. The agricultural sector requires high-reliability tools that function in remote environments; the previous version failed this fundamental requirement.

Project Glacier is not merely a patch but a complete architectural overhaul. The goal is to deploy a robust, scalable, and highly performant machine learning model deployment platform that enables farmers and agronomists to receive real-time crop yield predictions, soil health analytics, and pest risk assessments via a modernized interface. By migrating to an Elixir/Phoenix stack and implementing a Kafka-driven event architecture, Glacier will solve the concurrency and latency issues that plagued its predecessor.

### 1.2 Business Justification
The agricultural technology (AgTech) market is currently experiencing a surge in demand for precision farming tools. Bellweather Technologies currently holds a significant amount of proprietary ML model IP, but the "last mile" delivery—the software interface—is the primary bottleneck. The failure of the previous version resulted in a 40% churn rate among early adopters and a damaged brand reputation within the Midwest US and EU markets.

The business justification for Project Glacier is rooted in customer retention and market expansion. By rebuilding the product with a focus on "offline-first" capabilities and a high-performance API, Bellweather can reclaim its position as a leader in ML-driven agriculture. The move to Fly.io and a microservices architecture ensures that the platform can scale horizontally as we move from a pilot group to a global rollout.

### 1.3 ROI Projection
The total budget for Project Glacier is $400,000. The projected Return on Investment (ROI) is calculated based on the following metrics over a 24-month horizon:

1.  **Churn Reduction:** Reducing the current churn rate from 40% to <10%, preserving an estimated $1.2M in Annual Recurring Revenue (ARR).
2.  **User Acquisition:** Target of 10,000 Monthly Active Users (MAU) within six months of launch. At an average LTV (Lifetime Value) of $1,200 per corporate farm account, this represents a potential $12M pipeline.
3.  **Operational Efficiency:** By automating billing and subscription management (Feature 4), we expect to reduce administrative overhead by 15 man-hours per week.

The break-even point is projected for Q3 2025, approximately two months after the final performance benchmark milestone.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Glacier utilizes a "Pragmatic Microservices" approach. Rather than over-engineering with dozens of tiny services, we have partitioned the system into five core functional domains: API Gateway, ML Model Orchestrator, Billing/Subscription Engine, Notification Service, and User Data Store. 

The choice of **Elixir/Phoenix** is driven by the need for massive concurrency and real-time updates. **LiveView** allows the UI to reflect ML model state changes (e.g., "Processing Imagery...") without requiring the client to poll the server, which is critical for the high-latency environments typical of rural agriculture.

### 2.2 System Diagram (ASCII)
The following describes the flow of data from the client device through the event-driven backend.

```text
[ Client Devices ] <---> [ Fly.io Edge ] <---> [ Phoenix LiveView / API Gateway ]
                                                         |
                                                         v
[ PostgreSQL DB ] <--- [ Event Bus (Apache Kafka) ] <--- [ Model Orchestrator ]
      |                          |                               ^
      |                          v                               |
      +--------------> [ Notification Service ] <------- [ ML Model Weights ]
                                 |                               |
                         [ External Providers ] <----------------+
                         (Twilio, SendGrid, FCM)
```

### 2.3 Technology Stack Detail
- **Language:** Elixir 1.15+ / Erlang OTP 25
- **Web Framework:** Phoenix 1.7 (LiveView for real-time dashboards)
- **Database:** PostgreSQL 15.4 (Managed via Fly.io Postgres)
- **Message Broker:** Apache Kafka (for asynchronous event processing between microservices)
- **Hosting:** Fly.io (Global distribution with regions in EU and US)
- **ML Runtime:** Python/PyTorch (wrapped in a Go-based inference sidecar for performance)
- **Frontend:** Tailwind CSS, Phoenix LiveView, LocalStorage (for offline caching)

### 2.4 Data Residency and Compliance
To meet **GDPR** and **CCPA** requirements, Project Glacier implements a strict data residency policy. EU customer data is routed to the `ams` (Amsterdam) and `fra` (Frankfurt) regions of Fly.io. The database schema includes a `region_id` on every user-related table to ensure that queries are scoped to the correct geographic shard.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Low)
**Status: Complete**
**Description:** 
The system must ensure that data from one farming organization is never accessible to another, even though they share the same physical PostgreSQL infrastructure. 

**Technical Implementation:**
We have implemented a "Row-Level Security" (RLS) approach combined with a shared-schema architecture. Every table containing customer data (e.g., `crop_data`, `soil_metrics`) includes an `organization_id` column. A custom Phoenix Plug intercepts every request, extracts the `org_id` from the authenticated JWT, and injects it into the query context.

**Detailed Logic:**
1. **Context Injection:** When a request hits the server, the `TenantPlug` verifies the user's session.
2. **Query Scoping:** All Ecto queries are wrapped in a scope: `where(query, [q], q.organization_id == ^current_org_id)`.
3. **Validation:** If a user attempts to access a resource via a direct ID (e.g., `/api/v1/crop/12345`), the system checks the `organization_id` of crop `12345` against the user's session. If they do not match, a `403 Forbidden` is returned.

### 3.2 Offline-First Mode with Background Sync (Priority: High)
**Status: In Design**
**Description:**
Farmers often operate in "dead zones" with no cellular connectivity. The application must allow users to input data, trigger model requests, and view cached analytics while offline, then synchronize these changes automatically when a connection is restored.

**Technical Implementation:**
This feature relies on a "Write-Ahead Log" (WAL) on the client side using IndexedDB.

**Workflow:**
1. **Local Persistence:** When the user performs an action (e.g., logging a soil sample), the app writes the record to IndexedDB with a status of `pending_sync`.
2. **Optimistic UI:** The UI immediately reflects the change as if it were successful, marking the record with a "syncing" icon.
3. **Sync Engine:** A Service Worker monitors the `navigator.onLine` event. Upon reconnection, it initiates a "Reconciliation Loop."
4. **Conflict Resolution:** The server uses a "Last Write Wins" strategy based on a high-precision timestamp (`updated_at`). If the server version is newer, the client is prompted to resolve the conflict or overwrite.
5. **Background Uploads:** Large files (imagery for ML analysis) are uploaded via a chunked upload mechanism to prevent timeouts on unstable connections.

### 3.3 Notification System (Priority: Low)
**Status: Not Started**
**Description:**
A multi-channel alerting system to notify users of critical ML insights (e.g., "High risk of blight detected in Sector 4") or billing issues.

**Technical Implementation:**
This will be implemented as a standalone microservice consuming events from Kafka.

**Proposed Channels:**
- **Email:** Via SendGrid. Used for weekly reports and billing receipts.
- **SMS:** Via Twilio. Used for urgent field alerts.
- **In-App:** Via Phoenix PubSub and LiveView. Real-time toast notifications.
- **Push:** Via Firebase Cloud Messaging (FCM). Mobile alerts for Android/iOS.

**Logic Flow:**
An event `model.alert_generated` is published to Kafka. The Notification Service reads this event, checks the user's `notification_preferences` table, and triggers the appropriate provider.

### 3.4 Automated Billing and Subscription Management (Priority: Medium)
**Status: Complete**
**Description:**
A system to manage monthly and annual subscriptions, handle credit card processing, and automatically revoke API access for delinquent accounts.

**Technical Implementation:**
Integrated via Stripe Billing. We utilize Stripe Webhooks to synchronize subscription status with our local PostgreSQL `subscriptions` table.

**Details:**
- **Tiers:** "Seed" (Free), "Sprout" ($49/mo), "Harvest" ($199/mo).
- **Billing Cycle:** Monthly recurring billing with a 14-day grace period for failed payments.
- **Access Control:** A middleware check on the API Gateway verifies the `subscription_status` field. If `status == 'past_due'`, the user is redirected to the billing portal.
- **Invoicing:** Automated PDF generation is handled by Stripe, with a mirrored copy stored in our S3-compatible bucket for EU compliance.

### 3.5 Customer-Facing API (Priority: Critical)
**Status: Complete**
**Description:**
The core interface for third-party integrations and the frontend. It must be versioned to prevent breaking changes for legacy users.

**Technical Implementation:**
A RESTful API implemented in Phoenix, utilizing `JSON:API` standards. 

**Key Components:**
- **Versioning:** Managed via URL paths (e.g., `/api/v1/`). Version 2 will be introduced in Q4 2025.
- **Sandbox Environment:** A separate Fly.io app (`sandbox.glacier.bellweather.io`) using a cloned, anonymized database for developers to test their integrations.
- **Rate Limiting:** Implemented via Redis. Tiers are 1,000 requests/hr for "Seed" and 50,000 requests/hr for "Harvest."
- **Authentication:** OAuth2 with JWT (JSON Web Tokens) signed with an RS256 algorithm.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer <JWT>` token in the Authorization header.

### 4.1 Model Prediction Request
- **Path:** `POST /api/v1/predictions`
- **Description:** Submits field data for ML analysis.
- **Request Example:**
  ```json
  {
    "field_id": "field_9921",
    "metric_type": "soil_moisture",
    "value": 22.5,
    "timestamp": "2024-10-24T10:00:00Z"
  }
  ```
- **Response Example (202 Accepted):**
  ```json
  {
    "prediction_id": "pred_abc123",
    "status": "processing",
    "eta_seconds": 15
  }
  ```

### 4.2 Get Prediction Result
- **Path:** `GET /api/v1/predictions/{id}`
- **Description:** Retrieves the result of a previously submitted prediction.
- **Response Example (200 OK):**
  ```json
  {
    "prediction_id": "pred_abc123",
    "result": "Low Risk",
    "confidence": 0.94,
    "suggested_action": "Maintain current irrigation"
  }
  ```

### 4.3 List All Fields
- **Path:** `GET /api/v1/fields`
- **Description:** Returns a list of all registered fields for the authenticated organization.
- **Response Example (200 OK):**
  ```json
  [
    {"id": "field_1", "name": "North Corn Plot", "acreage": 120},
    {"id": "field_2", "name": "East Soy Plot", "acreage": 85}
  ]
  ```

### 4.4 Update Field Metadata
- **Path:** `PATCH /api/v1/fields/{id}`
- **Description:** Updates details of a specific field.
- **Request Example:**
  ```json
  { "name": "North Corn Plot - Revised" }
  ```
- **Response Example (200 OK):**
  ```json
  { "id": "field_1", "name": "North Corn Plot - Revised", "updated_at": "2024-10-24T11:00:00Z" }
  ```

### 4.5 Subscription Status
- **Path:** `GET /api/v1/billing/status`
- **Description:** Checks current plan and billing health.
- **Response Example (200 OK):**
  ```json
  {
    "plan": "Harvest",
    "status": "active",
    "next_billing_date": "2024-11-01"
  }
  ```

### 4.6 Create User API Key
- **Path:** `POST /api/v1/auth/keys`
- **Description:** Generates a new API key for third-party integration.
- **Response Example (201 Created):**
  ```json
  { "key_id": "key_556", "api_key": "glacier_live_xxxxxxxxxxxx" }
  ```

### 4.7 Get Model Version Info
- **Path:** `GET /api/v1/models/version`
- **Description:** Returns the current version of the ML model deployed in production.
- **Response Example (200 OK):**
  ```json
  { "version": "v4.2.1-stable", "deployed_at": "2024-09-10T00:00:00Z" }
  ```

### 4.8 Delete Field Data
- **Path:** `DELETE /api/v1/fields/{id}`
- **Description:** Deletes a field and all associated ML historical data (GDPR Right to Erasure).
- **Response Example (204 No Content):**
  `Empty Body`

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions
The system uses a PostgreSQL database. Below are the 10 primary tables.

1.  **`organizations`**
    - `id` (UUID, PK)
    - `name` (VARCHAR)
    - `region_id` (VARCHAR) - *For GDPR compliance*
    - `created_at` (TIMESTAMP)
2.  **`users`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK -> organizations.id)
    - `email` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `role` (ENUM: 'admin', 'analyst', 'viewer')
3.  **`fields`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK -> organizations.id)
    - `name` (VARCHAR)
    - `boundary_geojson` (JSONB)
    - `acreage` (DECIMAL)
4.  **`sensor_readings`**
    - `id` (BIGINT, PK)
    - `field_id` (UUID, FK -> fields.id)
    - `metric_type` (VARCHAR)
    - `value` (FLOAT)
    - `captured_at` (TIMESTAMP)
5.  **`predictions`**
    - `id` (UUID, PK)
    - `field_id` (UUID, FK -> fields.id)
    - `model_version` (VARCHAR)
    - `result` (TEXT)
    - `confidence` (FLOAT)
    - `created_at` (TIMESTAMP)
6.  **`subscriptions`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK -> organizations.id)
    - `stripe_subscription_id` (VARCHAR)
    - `plan_tier` (ENUM: 'seed', 'sprout', 'harvest')
    - `status` (VARCHAR)
7.  **`api_keys`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `key_hash` (TEXT)
    - `last_used_at` (TIMESTAMP)
8.  **`notification_preferences`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `email_enabled` (BOOLEAN)
    - `sms_enabled` (BOOLEAN)
    - `push_enabled` (BOOLEAN)
9.  **`audit_logs`**
    - `id` (BIGINT, PK)
    - `user_id` (UUID, FK -> users.id)
    - `action` (VARCHAR)
    - `timestamp` (TIMESTAMP)
10. **`sync_queue`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `payload` (JSONB)
    - `status` (ENUM: 'pending', 'synced', 'failed')

### 5.2 Relationships and Constraints
- **One-to-Many:** `organizations` $\rightarrow$ `users`, `organizations` $\rightarrow$ `fields`, `organizations` $\rightarrow$ `subscriptions`.
- **One-to-Many:** `fields` $\rightarrow$ `sensor_readings`, `fields` $\rightarrow$ `predictions`.
- **Foreign Key Constraint:** All deletions in `organizations` must cascade to `users` and `fields` to maintain referential integrity.
- **Indexing:** B-tree indexes on `org_id` and `field_id` across all tables to ensure query performance remains under 200ms.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Architecture
Glacier utilizes three distinct environments to isolate development from production.

| Environment | Purpose | Fly.io App Name | Database | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | Local feature work | `glacier-dev` | Local Docker PG | Individual Devs |
| **Staging** | QA and Stakeholder UAT | `glacier-staging` | Staging PG | Tomas Park (Manual) |
| **Production** | Live Customer Traffic | `glacier-prod` | Production PG | Tomas Park (Manual) |

### 6.2 Deployment Process (The "Bus Factor" Risk)
Current deployments are handled exclusively by **Tomas Park**. The process is as follows:
1. Code is merged into the `main` branch.
2. Tomas runs the `fly deploy` command from a secure administrative workstation.
3. Database migrations are run manually: `fly ssh console -C "mix ecto.migrate"`.
4. A health check is performed on the `/health` endpoint.

**Critical Vulnerability:** Because Tomas is the sole person with deployment credentials, the "bus factor" is 1. If Tomas is unavailable, the team cannot deploy updates. (Proposed mitigation: Implement GitHub Actions for automated CI/CD in Q3 2025).

### 6.3 Infrastructure Scaling
Fly.io allows for horizontal scaling of the Phoenix nodes. We currently run 3 nodes in `iad` (Virginia) and 3 nodes in `ams` (Amsterdam). Each node is allocated 2GB RAM and 2 vCPUs. If CPU utilization exceeds 70% for more than 10 minutes, an additional node is manually provisioned.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** ExUnit.
- **Focus:** Business logic in "Context" modules (e.g., `Billing.SubscriptionManager`).
- **Requirement:** All new PRs must maintain >80% code coverage.
- **Mocking:** Using `Mox` to simulate external API calls to Stripe and Twilio.

### 7.2 Integration Testing
- **Tooling:** Wallaby / Phoenix.LiveViewTest.
- **Focus:** Testing the interaction between the API Gateway and the PostgreSQL database.
- **Scenario:** Verifying that a request to `POST /predictions` correctly creates a record in the `predictions` table and sends a message to Kafka.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Focus:** Critical user journeys (e.g., "User signs up $\rightarrow$ Adds field $\rightarrow$ Uploads data $\rightarrow$ Sees prediction").
- **Environment:** Conducted exclusively in the **Staging** environment to ensure no production data is corrupted.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Performance requirements are 10x current capacity with no extra budget. | High | High | Negotiate timeline extension with stakeholders to allow for deeper optimization. |
| R2 | Project sponsor is rotating out of their role. | Medium | High | Engage external consultant for an independent assessment to validate progress to the new sponsor. |
| R3 | Raw SQL usage (30% of queries) makes migrations dangerous. | High | Medium | Schedule a "Technical Debt Sprint" to migrate raw SQL to Ecto queries where possible. |
| R4 | Bus Factor of 1 for deployments (Tomas Park). | Medium | High | Document deployment steps in Wiki and share credentials in a secure vault (HashiCorp Vault). |

### 8.1 Probability/Impact Matrix
- **Critical:** R1, R2 (High Prob/High Impact)
- **Major:** R3, R4 (Medium Prob/High Impact)

---

## 9. TIMELINE AND PHASES

### 9.1 Phase Overview
The project is divided into three primary phases leading up to the final benchmarks.

**Phase 1: Core Stabilization (Now $\rightarrow$ 2025-03-15)**
- Finalize Offline-First design.
- Stabilize API Gateway.
- Complete multi-tenant isolation.
- **Goal:** Production Launch.

**Phase 2: Validation & Feedback (2025-03-16 $\rightarrow$ 2025-05-15)**
- Onboard first 1,000 beta users.
- Refine UX based on real-world field data.
- Finalize Notification System.
- **Goal:** Stakeholder Demo and Sign-off.

**Phase 3: Scale & Optimize (2025-05-16 $\rightarrow$ 2025-07-15)**
- Optimize raw SQL queries to reduce DB load.
- Stress test for 10,000 MAU.
- Performance tuning of the ML inference sidecar.
- **Goal:** Performance Benchmarks Met.

### 9.2 Critical Path Dependencies
- **Offline Sync $\rightarrow$ Production Launch:** The product cannot launch without offline-first capabilities due to the nature of the user base.
- **Stakeholder Sign-off $\rightarrow$ Performance Scaling:** We cannot invest in infrastructure scaling until the feature set is locked and signed off by the sponsor.

---

## 10. MEETING NOTES

### Meeting 1: Architectural Review
**Date:** 2024-08-12  
**Attendees:** Alejandro, Tomas, Bodhi, Wanda  
**Discussion:**
The team discussed the danger of using raw SQL for the `sensor_readings` table. Wanda noted that the Ecto ORM was adding 40ms of overhead per query, which is unacceptable given the p95 target. Alejandro agreed to allow raw SQL for now but mandated that all such queries be wrapped in a specific `PerformanceQueries` module to make them easier to find and refactor later.

**Action Items:**
- [Tomas] Set up Kafka clusters on Fly.io. (Done)
- [Wanda] Audit all raw SQL queries and document them in the Wiki. (Pending)

### Meeting 2: UX/Offline Sync Brainstorming
**Date:** 2024-09-05  
**Attendees:** Alejandro, Bodhi, Wanda  
**Discussion:**
Bodhi presented the mockups for the "Offline Mode." There was a debate regarding how to handle conflicts. Wanda suggested a complex merging strategy, but Alejandro overruled, citing the $400k budget constraint. The team decided to implement "Last Write Wins" (LWW) for simplicity and speed of development.

**Action Items:**
- [Bodhi] Finalize IndexedDB schema for local storage. (Done)
- [Alejandro] Update project roadmap to reflect LWW strategy. (Done)

### Meeting 3: Risk Assessment & Sponsor Update
**Date:** 2024-10-10  
**Attendees:** Alejandro, Project Sponsor (External)  
**Discussion:**
The sponsor indicated they might rotate out of their role by January. Alejandro expressed concern regarding the continuity of funding and vision. The sponsor suggested bringing in an external consultant to review the technical architecture to ensure the new sponsor has an unbiased view of the project's health.

**Action Items:**
- [Alejandro] Reach out to "AgriTech Consultants Inc." for a quote on a 2-week audit. (Pending)
- [Tomas] Prepare a "System Health" report for the audit. (Pending)

---

## 11. BUDGET BREAKDOWN

The total budget is **$400,000**. This is a modest budget for a team of 12, requiring lean operations.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $300,000 | Salaries for 12 members (blended rate). |
| **Infrastructure** | 12% | $48,000 | Fly.io, Managed Postgres, Kafka hosting. |
| **Tools & Licensing** | 5% | $20,000 | Stripe fees, SendGrid, Twilio, Jira, GitHub. |
| **Consultancy** | 3% | $12,000 | External independent assessment for sponsor transition. |
| **Contingency** | 5% | $20,000 | Emergency buffer for infrastructure spikes. |
| **Total** | **100%** | **$400,000** | |

---

## 12. APPENDICES

### Appendix A: ML Model Inference Pipeline
The ML models are trained in PyTorch and exported as TorchScript files. To avoid the overhead of calling Python from Elixir, we use a sidecar written in Go (utilizing `cgo` and `libtorch`). 

**Request Flow:**
1. Phoenix $\rightarrow$ Kafka (`prediction_requested` topic).
2. Go Sidecar $\rightarrow$ Consumes from Kafka.
3. Go Sidecar $\rightarrow$ Loads model into VRAM $\rightarrow$ Runs Inference.
4. Go Sidecar $\rightarrow$ Kafka (`prediction_completed` topic).
5. Phoenix $\rightarrow$ Consumes result $\rightarrow$ Updates DB $\rightarrow$ Pushes to LiveView.

### Appendix B: GDPR Data Purge Procedure
To comply with "The Right to be Forgotten," the following sequence is executed when a user requests account deletion:
1. **Soft Delete:** User status set to `deleted_pending`.
2. **Dependency Search:** Identify all `field_ids` associated with the user's `org_id`.
3. **Hard Delete:** 
   - `DELETE FROM sensor_readings WHERE field_id IN (...)`
   - `DELETE FROM predictions WHERE field_id IN (...)`
   - `DELETE FROM users WHERE id = ...`
4. **Audit Log:** A record is kept in the `audit_logs` table indicating *that* a deletion occurred, without storing the deleted user's personal data.