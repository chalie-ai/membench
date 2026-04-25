# PROJECT SPECIFICATION DOCUMENT: PROJECT OBELISK
**Document Version:** 1.0.4  
**Status:** Draft/Internal Review  
**Date:** October 24, 2025  
**Company:** Bellweather Technologies  
**Classification:** Confidential – Internal Use Only

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Obelisk is a strategic initiative by Bellweather Technologies to modernize the core operational infrastructure of the company. For 15 years, Bellweather has relied on a legacy monolithic system (hereafter referred to as "The Monolith") to manage aerospace telemetry, logistics, and client billing. This legacy system is currently a single point of failure, characterized by fragile dependencies, undocumented business logic, and a lack of scalability. Project Obelisk aims to replace this system with a modern, self-hosted SaaS platform designed for high availability, modularity, and extreme reliability.

### 1.2 Business Justification
The current legacy system has reached its "end-of-life" state. Maintenance costs have increased by 40% year-over-year due to the scarcity of developers familiar with the antiquated codebase. Furthermore, the system's inability to handle concurrent API requests from new aerospace partners has led to a 12% churn rate in the last fiscal year. The primary business driver for Obelisk is the elimination of operational risk. Because the entire company depends on this system, any downtime results in an immediate cessation of revenue-generating activities. The mandate for Obelisk is "Zero Downtime Tolerance."

### 1.3 ROI Projection
The total investment for Project Obelisk is $1.5M. The projected Return on Investment (ROI) is calculated over a 36-month horizon based on the following levers:
1.  **Reduction in Maintenance Costs:** By moving to a Python/FastAPI stack, Bellweather expects to reduce developer hours spent on "emergency patching" by 70%, saving approximately $210,000 annually.
2.  **Increased Throughput:** The new architecture is projected to handle 10x the current request volume, allowing the company to onboard an estimated $500,000 in new annual recurring revenue (ARR) from high-volume aerospace partners.
3.  **Risk Mitigation:** Avoiding a single catastrophic failure of The Monolith (estimated cost of $1.2M in lost contracts and penalties) justifies the project's expenditure.

The projected break-even point is 14 months post-launch. Success will be measured by a 99.9% uptime rate in the first 90 days and passing the external regulatory audit on the first attempt.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Obelisk utilizes a modern, asynchronous stack designed for high I/O throughput, essential for aerospace data processing.

*   **Language/Framework:** Python 3.11+ with FastAPI. FastAPI was chosen for its native asynchronous support and automatic OpenAPI documentation.
*   **Database:** MongoDB 6.0 (Cluster). A document-oriented database is required to handle the polymorphic nature of aerospace telemetry data which varies by vehicle model.
*   **Task Queue:** Celery 5.3 with Redis as the broker. This handles heavy-duty computations and background synchronization.
*   **Containerization:** Docker Compose for orchestration of self-hosted services.
*   **CI/CD:** GitHub Actions for automated testing and deployment.

### 2.2 Architectural Strategy: The Modular Monolith
To minimize risk during the transition from the 15-year-old legacy system, Obelisk will launch as a **Modular Monolith**. This approach keeps the codebase in a single repository but enforces strict boundary separation between domains (e.g., Billing, Auth, Telemetry). 

As the system stabilizes, these modules will be extracted into independent microservices. This allows the team to avoid the "distributed monolith" trap while providing a clear path toward horizontal scaling.

### 2.3 Infrastructure Diagram (ASCII)
```text
[ External Traffic ] 
       |
       v
[ Nginx Load Balancer ] <--- (Blue-Green Deployment Switch)
       |
       +-----------------------+-----------------------+
       |                       |                       |
 [ App Instance A ]     [ App Instance B ]      [ Admin Panel ]
 (Green - Active)       (Blue - Standby)        (Internal Only)
       |                       |                       |
       +-----------+-----------+-----------------------+
                   |
                   v
    +-------------------------------------------------+
    |             Internal Service Layer              |
    |  [ FastAPI ] <--> [ Celery Workers ] <--> [ Redis ]|
    +-------------------------------------------------+
                   |
                   v
    +-------------------------------------------------+
    |             Persistence Layer                   |
    |  [ MongoDB Primary ] <--> [ MongoDB Secondary ] |
    +-------------------------------------------------+
                   |
                   v
    [ S3 Compatible Object Store ] (Telemetry Archives)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Functional Specification:**
To protect the system from being overwhelmed by high-frequency aerospace telemetry streams, Obelisk must implement a sophisticated rate-limiting layer. Unlike standard global limits, Obelisk requires *Tiered Rate Limiting* based on the customer's subscription level.

*   **Token Bucket Algorithm:** Each API key will be associated with a "bucket" of tokens. Tokens are consumed upon each request and replenished at a fixed rate.
*   **Tiers:** 
    *   *Standard:* 1,000 requests/minute.
    *   *Premium:* 10,000 requests/minute.
    *   *Enterprise:* Custom negotiated limits.
*   **Analytics Engine:** Every request must be logged to a time-series collection in MongoDB. This data will be used to generate usage reports for customers and to trigger automatic billing adjustments.
*   **Header Response:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Constraints:**
The rate limiter must reside in the middleware layer of FastAPI to ensure that invalid requests are rejected before they hit the business logic, reducing CPU overhead. Redis will be used to track token counts in real-time to ensure sub-millisecond latency.

---

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Functional Specification:**
Bellweather intends to allow clients to programmatically interact with their data. This requires a public-facing API gateway distinct from the internal administrative API.

*   **Versioning:** The API will use URI versioning (e.g., `/v1/telemetry`, `/v2/telemetry`). This allows the team to introduce breaking changes without disrupting existing aerospace client integrations.
*   **Sandbox Environment:** A mirrored "Sandbox" environment will be provided. This environment will use a separate MongoDB database seeded with anonymized, synthetic aerospace data. Clients can test their integrations here without affecting production data.
*   **API Key Management:** Customers can generate, rotate, and revoke API keys via the user dashboard. Keys will be hashed using SHA-256 before storage.

**Technical Constraints:**
The sandbox must be logically isolated from production. Deployment will be handled via a separate Docker Compose file to ensure that a failure in the sandbox environment cannot cascade into the production environment.

---

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** Not Started

**Functional Specification:**
Given the sensitivity of aerospace data, standard password authentication is insufficient. Obelisk will implement a mandatory 2FA flow for all administrative accounts.

*   **TOTP Support:** Integration with apps like Google Authenticator or Authy using the Time-based One-Time Password (TOTP) algorithm.
*   **Hardware Key Support:** Full support for FIDO2/WebAuthn standards, allowing users to use YubiKeys or Titan Security Keys. This is a critical requirement for users operating in high-security environments where mobile phones are prohibited.
*   **Recovery Codes:** Upon 2FA setup, the system will generate ten one-time-use recovery codes. These must be stored as salted hashes.
*   **Grace Period:** A 24-hour grace period will be offered for new users to set up 2FA before the system locks the account.

**Technical Constraints:**
The 2FA state must be tracked in the session JWT (JSON Web Token). A "partial" token will be issued after the first factor (password), which only grants access to the `/auth/verify-2fa` endpoint. A "full" token is only issued after the second factor is verified.

---

### 3.4 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Functional Specification:**
Aerospace engineers often operate in "dead zones" (hangars, launchpads) with intermittent connectivity. The Obelisk frontend must allow users to continue data entry and viewing without an active internet connection.

*   **Local Persistence:** The frontend (React/TypeScript) will utilize IndexedDB to cache the current working set of data.
*   **Conflict Resolution:** A "Last-Write-Wins" strategy will be implemented for simple fields, while complex telemetry logs will use a "Merge-and-Notify" approach where conflicts are flagged for manual review.
*   **Background Sync:** Using Service Workers, the application will detect when the connection is restored and automatically push queued changes to the server.
*   **Sync Status Indicator:** A visible UI element will show the current sync state: `Synced`, `Syncing...`, or `Offline - Changes Pending`.

**Technical Constraints:**
To prevent data loss, the system must implement a "Write-Ahead Log" (WAL) in the browser. Every mutation is recorded locally before an attempt is made to sync with the FastAPI backend.

---

### 3.5 Automated Billing and Subscription Management
**Priority:** High | **Status:** In Design

**Functional Specification:**
Obelisk will transition from manual invoicing to an automated subscription model.

*   **Subscription Tiers:** Monthly and annual billing cycles for Standard, Premium, and Enterprise tiers.
*   **Automated Invoicing:** Integration with a payment gateway (e.g., Stripe) to generate PDF invoices and process credit card payments.
*   **Usage-Based Overages:** The system will link with the "Usage Analytics" feature (Feature 3.1). If a customer exceeds their API quota, an overage fee will be automatically calculated and added to the next billing cycle.
*   **Dunning Management:** Automated emails will be sent to customers whose credit cards are expiring or whose payments have failed.

**Technical Constraints:**
Billing data must be idempotent. The system must implement a "Billing Event" queue in Celery to ensure that no customer is charged twice for the same period, even if the payment gateway experiences a timeout.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /auth/login`
*   **Description:** Authenticates user and returns a partial JWT.
*   **Request:** `{"email": "user@bellweather.com", "password": "securepassword"}`
*   **Response (200):** `{"token": "eyJ...", "requires_2fa": true}`

### 4.2 `POST /auth/verify-2fa`
*   **Description:** Verifies 2FA code and returns full access JWT.
*   **Request:** `{"token": "eyJ...", "code": "123456"}`
*   **Response (200):** `{"access_token": "full_access_token", "expires_in": 3600}`

### 4.3 `GET /telemetry/stream/{vehicle_id}`
*   **Description:** Retrieves real-time telemetry for a specific vehicle.
*   **Request:** `Header: Authorization: Bearer <token>`
*   **Response (200):** `{"vehicle_id": "B-102", "data": [{"timestamp": "2026-01-01T12:00Z", "altitude": 35000, "velocity": 450}]}`

### 4.4 `POST /telemetry/upload`
*   **Description:** Uploads batch telemetry data.
*   **Request:** `{"vehicle_id": "B-102", "readings": [...]}`
*   **Response (202):** `{"status": "accepted", "job_id": "celery-task-id-123"}`

### 4.5 `GET /billing/usage`
*   **Description:** Returns current month's API usage analytics.
*   **Request:** `Header: Authorization: Bearer <token>`
*   **Response (200):** `{"total_requests": 45000, "limit": 50000, "percentage": 90}`

### 4.6 `PATCH /billing/subscription`
*   **Description:** Updates the customer subscription tier.
*   **Request:** `{"new_tier": "premium"}`
*   **Response (200):** `{"status": "updated", "next_billing_date": "2026-04-15"}`

### 4.7 `GET /system/health`
*   **Description:** Returns the health status of the modular monolith and its dependencies.
*   **Request:** N/A
*   **Response (200):** `{"status": "healthy", "mongodb": "connected", "redis": "connected", "uptime": "14d 2h"}`

### 4.8 `DELETE /auth/keys/{key_id}`
*   **Description:** Revokes a specific API key.
*   **Request:** `{"key_id": "key_abc_123"}`
*   **Response (204):** No Content.

---

## 5. DATABASE SCHEMA (MONGODB)

Since MongoDB is schema-less, the following describes the **enforced document structures** (Schema Validation) used in the application.

### 5.1 Collection: `users`
*   `_id`: ObjectId (PK)
*   `email`: String (Unique, Indexed)
*   `password_hash`: String
*   `mfa_secret`: String (Encrypted)
*   `mfa_enabled`: Boolean
*   `role`: String (`admin`, `engineer`, `client`)
*   `created_at`: ISODate

### 5.2 Collection: `api_keys`
*   `_id`: ObjectId (PK)
*   `user_id`: ObjectId (FK -> `users`)
*   `key_hash`: String (Unique)
*   `permissions`: Array (e.g., `['read:telemetry', 'write:telemetry']`)
*   `created_at`: ISODate
*   `last_used_at`: ISODate

### 5.3 Collection: `vehicles`
*   `_id`: ObjectId (PK)
*   `callsign`: String (Indexed)
*   `model`: String
*   `owner_id`: ObjectId (FK -> `users`)
*   `specs`: Object (Flexible schema for varying vehicle types)

### 5.4 Collection: `telemetry_logs`
*   `_id`: ObjectId (PK)
*   `vehicle_id`: ObjectId (FK -> `vehicles`, Indexed)
*   `timestamp`: ISODate (Indexed)
*   `metrics`: Object (Key-value pairs of sensor readings)
*   `quality_score`: Float (0.0 - 1.0)

### 5.5 Collection: `usage_stats`
*   `_id`: ObjectId (PK)
*   `api_key_id`: ObjectId (FK -> `api_keys`)
*   `request_count`: Integer
*   `window_start`: ISODate
*   `window_end`: ISODate

### 5.6 Collection: `subscriptions`
*   `_id`: ObjectId (PK)
*   `user_id`: ObjectId (FK -> `users`)
*   `tier`: String (`standard`, `premium`, `enterprise`)
*   `status`: String (`active`, `past_due`, `canceled`)
*   `renewal_date`: ISODate

### 5.7 Collection: `invoices`
*   `_id`: ObjectId (PK)
*   `subscription_id`: ObjectId (FK -> `subscriptions`)
*   `amount`: Decimal
*   `currency`: String (`USD`)
*   `paid`: Boolean
*   `invoice_pdf_url`: String

### 5.8 Collection: `sync_queues`
*   `_id`: ObjectId (PK)
*   `user_id`: ObjectId (FK -> `users`)
*   `payload`: Object
*   `status`: String (`pending`, `synced`, `conflict`)
*   `retry_count`: Integer

### 5.9 Collection: `audit_logs`
*   `_id`: ObjectId (PK)
*   `actor_id`: ObjectId (FK -> `users`)
*   `action`: String
*   `resource`: String
*   `timestamp`: ISODate
*   `ip_address`: String

### 5.10 Collection: `system_configs`
*   `_id`: String (PK, e.g., "global_settings")
*   `config_value`: Object
*   `updated_by`: ObjectId (FK -> `users`)
*   `version`: Integer

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Obelisk will utilize three distinct environments to ensure that no untested code ever reaches the aerospace production data.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and initial unit testing.
*   **Infrastructure:** Local Docker Compose environments on developer machines.
*   **Data:** Mock data generated by Xander Fischer’s scripts.
*   **Deployment:** Manual `docker-compose up`.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Pre-production validation and QA.
*   **Infrastructure:** A dedicated staging server mimicking the production hardware specs.
*   **Data:** A scrubbed (anonymized) clone of production data.
*   **Deployment:** Automatic via GitHub Actions upon merge to the `develop` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live aerospace operations.
*   **Infrastructure:** Self-hosted high-availability cluster.
*   **Deployment:** Blue-Green Deployment strategy. 
    *   **Green:** The current live version.
    *   **Blue:** The new version being deployed.
    *   Traffic is shifted via Nginx only after the "Green" health checks pass.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1.  **Linting/Static Analysis:** Run `flake8` and `mypy` on every push.
2.  **Unit Tests:** Run `pytest` suite.
3.  **Integration Tests:** Spin up a temporary MongoDB container to test API endpoints.
4.  **Build:** Create Docker images and push to the internal Bellweather registry.
5.  **Deploy:** Update the staging or production server via SSH orchestration.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions and business logic (e.g., calculating overage fees).
*   **Tooling:** `pytest`.
*   **Requirement:** Minimum 80% code coverage for all new modules.
*   **Execution:** Run on every commit in GitHub Actions.

### 7.2 Integration Testing
*   **Focus:** The interaction between FastAPI, MongoDB, and Celery.
*   **Approach:** "Black-box" testing of API endpoints. We will use `httpx` to make real requests to a running instance of the app in the CI environment.
*   **Scenario:** A full "User Journey" (Login $\rightarrow$ Upload Telemetry $\rightarrow$ Check Usage $\rightarrow$ Logout).

### 7.3 End-to-End (E2E) Testing
*   **Focus:** The critical path from the UI to the database and back.
*   **Tooling:** Playwright.
*   **Critical Path:** Specifically testing the "Offline-First" mode by simulating network disconnection in the browser and verifying data persistence in IndexedDB.

### 7.4 Penetration Testing
Because there is no formal compliance framework (like SOC2) yet, Bellweather will conduct **quarterly internal penetration tests**. This involves a dedicated security review of the API endpoints to prevent SQLi (though MongoDB is used, NoSQL injection is still a risk) and Broken Object Level Authorization (BOLA).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | Medium | Accept the risk; monitor weekly status of the transition. |
| R-02 | Integration partner's API is undocumented/buggy | High | High | Raise in the next board meeting as a critical blocker for telemetry ingestion. |
| R-03 | Zero-downtime migration fails | Low | Critical | Use Blue-Green deployments and a 1-hour rollback window. |
| R-04 | Performance degradation under load | Medium | High | Implement strict performance benchmarks (Milestone 3). |

**Current Blocker:** The project is currently stalled on the deployment of the production environment while waiting on the **legal review of the data processing agreement (DPA)**.

---

## 9. TIMELINE

### 9.1 Phase 1: Foundation (Now – March 2026)
*   **Focus:** Core architecture, DB schema, and the transition from legacy "Hardcoded Configs" to a centralized config service.
*   **Dependency:** Completion of the DPA legal review.
*   **Milestone 1:** Architecture review complete (Target: 2026-03-15).

### 9.2 Phase 2: Core Implementation (March 2026 – May 2026)
*   **Focus:** API Rate Limiting, Offline-First mode, and the 2FA system.
*   **Dependency:** Successful validation of the modular monolith boundaries.
*   **Milestone 2:** First paying customer onboarded (Target: 2026-05-15).

### 9.3 Phase 3: Optimization & Launch (May 2026 – July 2026)
*   **Focus:** Billing automation, performance tuning, and final audit preparation.
*   **Dependency:** Stable telemetry ingestion from the buggy partner API.
*   **Milestone 3:** Performance benchmarks met (Target: 2026-07-15).

---

## 10. MEETING NOTES

### Meeting 1: 2025-11-12 (Architecture Sync)
*   Quinn wants modular monolith.
*   Xander says MongoDB is too slow for raw logs. Quinn says "make it work."
*   Hessa mentions the UI feels "clunky" for offline mode.
*   Discussion on config files—too many hardcoded values (40+ files).
*   No decision on a config manager.

### Meeting 2: 2025-12-05 (Integration Blocker)
*   Partner API is a disaster. No docs.
*   Xander spent 3 days trying to find the telemetry endpoint.
*   Wanda reports users are complaining about the legacy system crashing daily.
*   Quinn and PM (unnamed) refused to look at each other during the meeting.
*   Decision: Escalate partner API to the board.

### Meeting 3: 2026-01-20 (Billing Design)
*   Stripe integration proposed.
*   Wanda asks if we support manual overrides for Enterprise clients.
*   Hessa wants a "Billing Dashboard" for the customer.
*   Legal review of DPA is still "pending."
*   Quinn: "Just keep coding the features, we'll figure out the legal stuff later."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $975,000 | 6 FTEs (Engineering, UX, Support, QA) |
| **Infrastructure** | 15% | $225,000 | Self-hosted servers, Redis/Mongo licenses, S3 storage |
| **Tools & Software** | 10% | $150,000 | GitHub Enterprise, IDE licenses, Monitoring tools |
| **Contingency** | 10% | $150,000 | For emergency scaling or legal consultants |

---

## 12. APPENDICES

### Appendix A: Technical Debt Audit (The "Hardcoded" Problem)
As identified in the current risk assessment, the legacy system's configuration values are scattered across approximately 42 files (including `.py`, `.env`, and `.json` files). 
*   **Impact:** Changing a single API timeout value currently requires a full redeploy of the monolith.
*   **Resolution Plan:** A new `SystemConfig` collection in MongoDB will be created. A `ConfigProvider` class in Python will be implemented to fetch these values at runtime with a 5-minute local cache.

### Appendix B: Performance Benchmarks (Milestone 3 Criteria)
To satisfy Milestone 3, the system must meet the following KPIs under a simulated load of 5,000 concurrent users:
1.  **P95 Latency:** All `GET` requests must return in $< 200\text{ms}$.
2.  **Throughput:** The system must handle $\geq 5,000$ telemetry packets per second without increasing Celery queue depth beyond 10,000.
3.  **Memory Footprint:** Each FastAPI worker must not exceed 512MB of RAM.
4.  **DB Indexing:** No query shall perform a "Collection Scan" (COLLSCAN) in the MongoDB logs.