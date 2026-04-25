Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document. To ensure the highest level of detail, every section is expanded with the specific technical constraints, dates, and financial figures requested.

***

# PROJECT EMBER: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Active/Draft  
**Date:** October 24, 2023  
**Classification:** Confidential – Internal Use Only  
**Project Lead:** Bram Nakamura (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ember represents a strategic pivot for Deepwell Data. While the company has historically dominated data analytics in the industrial sector, Project Ember is the vehicle for entering the Real Estate market. This is a greenfield product, meaning there is no legacy code to migrate; however, the architectural philosophy is a "migration-ready" microservices design. The objective is to build a highly scalable API Gateway and a suite of microservices that allow real estate agencies to manage high-volume property data, client leads, and transactional histories with millisecond latency.

### 1.2 Business Justification
The real estate market is currently underserved by modern, real-time data tools. Most existing solutions are monolithic and suffer from significant lag in data synchronization. By leveraging Elixir and Phoenix, Deepwell Data can offer a "Live" experience where property updates and bid changes are reflected instantly across all client dashboards.

The move into this market is a diversification strategy. By decoupling the API gateway from the core business logic, Deepwell can eventually white-label the "Ember Engine" to other vertical markets. The decision to implement a micro-frontend architecture ensures that as the team grows, individual features (e.g., Search, Reporting, Auth) can be developed and deployed by independent teams without risking the stability of the entire platform.

### 1.3 ROI Projection
The project is backed by a $1.5M budget. The projected Return on Investment (ROI) is calculated based on a three-year horizon:
- **Year 1 (Development & Beta):** Estimated cost of $1.5M. Revenue: $0.
- **Year 2 (Market Penetration):** Targeting 50 mid-sized real estate firms at an average contract value (ACV) of $40,000/year. Projected Revenue: $2M.
- **Year 3 (Scaling):** Expanding to 200 firms. Projected Revenue: $8M.

The ROI is anticipated to hit break-even by Month 14 post-launch. The primary value drivers are the reduction in operational overhead (via Fly.io automation) and the high retention rate expected from the "sticky" nature of the real-time data integration.

### 1.4 Strategic Alignment
Ember aligns with Deepwell Data’s "Core-to-Edge" strategy: maintaining a robust core data layer while pushing the user experience to the edge. The use of Elixir/Phoenix ensures that the system can handle the "thundering herd" problem common in real estate during peak listing hours (e.g., Friday afternoons).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Project Ember utilizes a **Micro-Frontend (MFE)** architecture paired with a **Distributed Microservices** backend. The system is designed to be HIPAA compliant, meaning all PII (Personally Identifiable Information) is encrypted at the field level before hitting the persistence layer.

**The Stack:**
- **Language:** Elixir 1.15+ (OTP 25)
- **Web Framework:** Phoenix 1.13 (LiveView for real-time UI)
- **Database:** PostgreSQL 15 (Managed via Fly.io)
- **Infrastructure:** Fly.io (Global edge distribution)
- **Deployment:** LaunchDarkly (Feature Flags), Canary Releases via Fly.io proxies.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ CLIENT LAYER ] 
      |
      ▼
[ MICRO-FRONTENDS (React/LiveView) ] <--- (Independently Deployed)
      |
      ▼
[ API GATEWAY (Phoenix/Plug) ] <--- (Auth, Rate Limiting, Routing)
      |
      +-------------------------------------------------------+
      |                       |                              |
      ▼                       ▼                              ▼
[ AUTH SERVICE ]       [ SEARCH SERVICE ]          [ REPORT SERVICE ]
(PostgreSQL)           (PostgreSQL + Full Text)    (S3 + Postgres)
      |                       |                              |
      +-----------------------+------------------------------+
                              |
                              ▼
                    [ SHARED ENCRYPTION LAYER ]
                    (AES-256-GCM / HIPAA Compliant)
                              |
                              ▼
                    [ FLY.IO GLOBAL NETWORK ]
```

### 2.3 Component Breakdown
1. **API Gateway:** A lightweight Phoenix application utilizing `Plug` for request interceptors. It handles JWT validation, request transformation, and routing to the appropriate microservice.
2. **Micro-Frontends:** The UI is split into "Domains." For example, the Search UI is a separate bundle from the User Profile UI. This allows the frontend lead, Tariq Jensen, to deploy updates to the search facets without rebuilding the authentication flow.
3. **The LiveView Engine:** Used for the real-time dashboard. When a property status changes in the database, a Phoenix PubSub message is broadcast, and the UI updates instantly without a page refresh.
4. **Encryption Layer:** Every write operation passes through a security middleware managed by Zia Nakamura. This ensures that data is encrypted at rest using AES-256-GCM, satisfying HIPAA requirements for sensitive client data.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** In Progress
**Description:** 
The authentication system is the gateway to all Ember services. It must support multi-tenancy, allowing a single real estate agency to have multiple users with varying levels of permission.

**Technical Details:**
- **Mechanism:** JWT (JSON Web Tokens) with a 15-minute expiration and a sliding-window refresh token stored in a secure HTTP-only cookie.
- **RBAC Levels:**
    - `SuperAdmin`: Full system access, billing management, and global configuration.
    - `AgencyAdmin`: Management of all agency users, API key generation, and report scheduling.
    - `Agent`: Ability to list properties, edit their own leads, and generate reports.
    - `Client`: Read-only access to specific properties shared by an agent.
- **Security Requirements:** Password hashing via Argon2id. Account lockout after 5 failed attempts. Mandatory MFA (Multi-Factor Authentication) for `SuperAdmin` and `AgencyAdmin` roles.
- **Implementation Path:** Using `phx.gen.auth` as a baseline, but customized to support the multi-tenant schema where `user_id` is tied to an `organization_id`.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** Complete
**Description:** 
To meet HIPAA compliance and financial auditing standards, every mutation in the system must be recorded. The audit trail must be "tamper-evident," meaning any alteration of a historical log must be detectable.

**Technical Details:**
- **Storage:** A dedicated `audit_logs` table in PostgreSQL.
- **Mechanism:** Each log entry contains a SHA-256 hash of the current record concatenated with the hash of the previous record (a blockchain-style ledger).
- **Captured Events:** 
    - `USER_LOGIN`, `USER_LOGOUT`
    - `PROPERTY_CREATE`, `PROPERTY_UPDATE`, `PROPERTY_DELETE`
    - `PERMISSION_CHANGE`, `API_KEY_ROTATION`
- **Retention:** Logs are archived to S3 Glacier after 90 days for long-term compliance storage.
- **Verification:** A daily cron job verifies the hash chain. If a gap or mismatch is found, an alert is triggered to Zia Nakamura.

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** Not Started
**Description:** 
The core value proposition for users is the ability to find properties across massive datasets using complex filters (e.g., "3+ bedrooms, < $500k, within 5 miles of downtown, with a swimming pool").

**Technical Details:**
- **Indexing:** Using PostgreSQL GIN (Generalized Inverted Index) for full-text search.
- **Faceted Filtering:** Implementation of a dynamic filter builder that aggregates counts for each attribute (e.g., "Bedrooms: 2 (45), 3 (120), 4+ (12)").
- **Query Optimization:** Since 30% of queries currently bypass the ORM via raw SQL (Technical Debt), the search service will utilize `Ecto.Query` for standard filters and `fragment` for complex PostgreSQL TSVector searches.
- **Caching:** Results are cached in Redis for 60 seconds to prevent database hammering during peak traffic.

### 3.4 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** Low | **Status:** Blocked
**Description:** 
Deepwell Data intends to monetize the platform by allowing third-party developers to build apps on top of Ember. This requires a professional-grade public API.

**Technical Details:**
- **Versioning:** URI-based versioning (e.g., `/v1/properties`, `/v2/properties`).
- **Sandbox:** A separate environment (`sandbox.ember.deepwell.io`) that mirrors production but uses mocked data and has no effect on real-world listings.
- **Rate Limiting:** Tiered limits (Free: 1,000 req/day, Pro: 100,000 req/day) implemented via the API Gateway using a Token Bucket algorithm.
- **Current Blocker:** This feature is currently blocked because the third-party real estate data providers (MLS) have imposed strict rate limits on the testing accounts, making it impossible to validate the sandbox's sync logic.

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low | **Status:** In Design
**Description:** 
Agencies require weekly performance reports (leads generated, properties sold) delivered to their email in PDF and CSV formats.

**Technical Details:**
- **Generation Engine:** Using the `Pdfex` library for PDF generation and the `CSV` Elixir library for data exports.
- **Scheduling:** Implemented via `Oban` (PostgreSQL-backed job queue) for reliable background processing.
- **Delivery:** Integration with SendGrid for email delivery.
- **Storage:** Generated reports are stored in a temporary S3 bucket with a 7-day TTL (Time-to-Live) before automatic deletion.
- **Templates:** Liquid templates for PDF layouts to allow for agency branding (custom logos and colors).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests and responses use `application/json`.

### 4.1 Authentication Endpoints

**POST `/auth/login`**
- **Request:** `{ "email": "user@example.com", "password": "password123" }`
- **Response (200):** `{ "token": "eyJ...", "refresh_token": "def...", "user": { "id": 1, "role": "Agent" } }`
- **Response (401):** `{ "error": "Invalid credentials" }`

**POST `/auth/refresh`**
- **Request:** `{ "refresh_token": "def..." }`
- **Response (200):** `{ "token": "eyJ...", "refresh_token": "ghi..." }`

### 4.2 Property Management Endpoints

**GET `/properties`**
- **Query Params:** `?limit=20&offset=0&q=modern+villa&min_price=100000`
- **Response (200):** 
  ```json
  {
    "data": [
      { "id": "prop_123", "address": "123 Maple St", "price": 450000, "status": "active" }
    ],
    "pagination": { "total": 150, "next": "/api/v1/properties?offset=20" }
  }
  ```

**POST `/properties`**
- **Request:** `{ "address": "456 Oak Ave", "price": 600000, "beds": 3, "baths": 2 }`
- **Response (201):** `{ "id": "prop_456", "status": "created" }`

**PATCH `/properties/{id}`**
- **Request:** `{ "price": 580000, "status": "pending" }`
- **Response (200):** `{ "id": "prop_456", "updated_at": "2026-01-10T10:00:00Z" }`

**DELETE `/properties/{id}`**
- **Response (204):** No Content

### 4.3 Report and Audit Endpoints

**GET `/reports/generate`**
- **Request:** `{ "type": "monthly_leads", "format": "pdf", "email": "boss@agency.com" }`
- **Response (202):** `{ "job_id": "job_abc_123", "status": "queued" }`

**GET `/audit/logs`**
- **Request:** `?start_date=2026-01-01&end_date=2026-01-31`
- **Response (200):**
  ```json
  {
    "logs": [
      { "timestamp": "2026-01-05T12:00:00Z", "action": "PROPERTY_UPDATE", "user_id": 45, "hash": "a1b2c3..." }
    ]
  }
  ```

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. Due to HIPAA requirements, the `encrypted_data` column in the `profiles` and `leads` tables stores the actual PII, while the `searchable_hash` column allows for lookups without decrypting the entire table.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `organizations` | `org_id` | `name`, `tax_id`, `plan_level` | 1:N with `users` |
| `users` | `user_id` | `org_id`, `email`, `password_hash`, `role` | N:1 with `organizations` |
| `properties` | `prop_id` | `org_id`, `address`, `price`, `status`, `last_updated` | N:1 with `organizations` |
| `leads` | `lead_id` | `prop_id`, `user_id`, `encrypted_pii`, `source` | N:1 with `properties`, `users` |
| `audit_logs` | `log_id` | `user_id`, `action`, `payload`, `prev_hash`, `current_hash` | N:1 with `users` |
| `roles` | `role_id` | `role_name`, `permissions_bitmask` | 1:N with `users` |
| `appointments` | `appt_id` | `lead_id`, `user_id`, `start_time`, `end_time` | N:1 with `leads`, `users` |
| `api_keys` | `key_id` | `user_id`, `key_hash`, `scopes`, `expires_at` | N:1 with `users` |
| `attachments` | `file_id` | `prop_id`, `s3_url`, `mime_type`, `file_size` | N:1 with `properties` |
| `report_schedules`| `sched_id` | `org_id`, `report_type`, `cron_expression` | N:1 with `organizations` |

### 5.2 Relationship Logic
- **Organizations $\rightarrow$ Users:** Strict hierarchy. A user cannot exist without an organization. This ensures data isolation.
- **Properties $\rightarrow$ Leads:** A lead is always associated with a specific property listing.
- **Audit Log $\rightarrow$ All:** The `audit_logs` table is the "truth" layer. Every change to any other table triggers a write to this table via a PostgreSQL trigger and an Elixir `after_save` hook.

### 5.3 Schema Performance Note
To mitigate the danger of the raw SQL bypass (30% of queries), the team is implementing a **Strict Schema Migration Policy**. No raw SQL may be used for `INSERT` or `UPDATE` operations; raw SQL is permitted only for `SELECT` operations involving complex window functions or CTEs that Ecto cannot express efficiently.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ember utilizes three distinct environments, all hosted on Fly.io.

**1. Development (`dev.ember.deepwell.io`)**
- **Purpose:** Feature experimentation and internal testing.
- **Deployment:** Automatic deploy on merge to `develop` branch.
- **Data:** Seeded with anonymized dummy data.
- **Configuration:** Debug mode enabled; verbose logging.

**2. Staging (`staging.ember.deepwell.io`)**
- **Purpose:** Pre-production validation, QA, and User Acceptance Testing (UAT).
- **Deployment:** Triggered by a Release Candidate (RC) tag.
- **Data:** Scrubbed production snapshot.
- **Configuration:** Mirrors production exactly, including HIPAA encryption keys.

**3. Production (`app.ember.deepwell.io`)**
- **Purpose:** Live customer traffic.
- **Deployment:** Canary release strategy. New code is rolled out to 5% of users, monitored for 1 hour, then scaled to 25%, 50%, and 100%.
- **Data:** Real customer data, encrypted at rest.

### 6.2 Infrastructure Details
- **Fly.io Setup:** We utilize a global cluster with nodes in `iad` (Virginia), `ams` (Amsterdam), and `hkg` (Hong Kong) to minimize latency for the global real estate market.
- **Database:** Managed PostgreSQL with automatic failover and point-in-time recovery (PITR).
- **Feature Flags:** LaunchDarkly is integrated into the Phoenix pipeline. This allows the team to merge code to production in a "dark" state and toggle features on for specific pilot users.
- **Secrets Management:** Fly Secrets are used for database credentials and API keys; no secrets are stored in the repository.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (The Foundation)
- **Tooling:** ExUnit.
- **Approach:** Every Elixir module must have a corresponding `.exs` test file. We target 90% code coverage for business logic.
- **Focus:** Edge cases in the RBAC logic and the encryption/decryption utility functions.

### 7.2 Integration Testing (The Glue)
- **Tooling:** Wallaby / Phoenix Test Helpers.
- **Approach:** Testing the interaction between the API Gateway and the underlying microservices.
- **Focus:** Ensuring that a request to `/api/v1/properties` correctly authenticates and retrieves data from the Property Service.

### 7.3 End-to-End (E2E) Testing (The User Experience)
- **Tooling:** Playwright.
- **Approach:** Testing critical user journeys (e.g., "Agent logs in $\rightarrow$ creates property $\rightarrow$ generates report").
- **Focus:** Real-time updates. Tests must verify that a change in one browser window is reflected in another via LiveView.

### 7.4 Performance and Load Testing
- **Tooling:** K6.
- **Metric:** Target 200ms response time for 95% of requests at a load of 5,000 concurrent users.
- **Scenario:** Simulating a "Friday Listing Rush" where 1,000 properties are updated simultaneously.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Team lacks Elixir/Phoenix experience | High | High | **Contingency:** Fallback architecture using Node.js/TypeScript is documented. Pair programming and intensive 4-week bootcamp completed. |
| **R-02** | Stakeholder scope creep | High | Medium | **Ownership:** Bram Nakamura acts as the sole gatekeeper for the product backlog. All "small" features must be submitted as RFCs. |
| **R-03** | Third-party API Rate Limits | Medium | High | **Current Blocker:** Implement a local caching proxy to simulate API responses during testing. Negotiate higher limits for the sandbox environment. |
| **R-04** | Technical Debt (Raw SQL) | Medium | High | **Policy:** Mandatory migration review. Any raw SQL query must be signed off by the CTO to ensure it doesn't break during schema changes. |
| **R-05** | HIPAA Compliance Leak | Low | Critical | **Audit:** Monthly third-party security audit and automated penetration testing by Zia Nakamura. |

---

## 9. TIMELINE

The project is divided into three primary phases. All dates are targets and subject to the "Scope Creep" mitigation policy.

### Phase 1: Core Infrastructure & Alpha (Now $\rightarrow$ 2026-09-15)
- **Oct 2023 - Dec 2023:** Setup Fly.io clusters, establish CI/CD pipelines, and implement the Encryption Layer.
- **Jan 2024 - June 2024:** Build Auth/RBAC and the Audit Trail system.
- **July 2024 - Dec 2024:** Development of the Property Management microservice and API Gateway.
- **Jan 2025 - Sept 2025:** Internal stability testing and bug scrubbing.
- **Milestone 3:** Internal Alpha Release (Target: 2026-09-15). *Note: Alpha release occurs after the external beta to ensure a stable internal baseline.*

### Phase 2: Pilot & Validation (Sept 2025 $\rightarrow$ 2026-05-15)
- **Oct 2025 - Feb 2026:** Implementation of Search and Reporting (Low priority features).
- **March 2026 - May 2026:** Onboarding 10 pilot users for the external beta.
- **Milestone 1:** External Beta Launch (Target: 2026-05-15).

### Phase 3: Sign-off & Launch (May 2026 $\rightarrow$ 2026-07-15)
- **June 2026:** Feedback loop from pilot users; final UI polish by Tariq Jensen.
- **July 2026:** Final stakeholder presentation and budget audit.
- **Milestone 2:** Stakeholder Demo and Sign-off (Target: 2026-07-15).

---

## 10. MEETING NOTES

*Note: These are summaries of recorded video calls. Per company culture, the full videos are archived but rarely viewed.*

### Meeting 1: Architecture Deep Dive (2023-11-02)
- **Attendees:** Bram, Tariq, Zia, Zara.
- **Discussion:** Discussion on whether to use a monolithic DB or one DB per service.
- **Decision:** Decided on a "Logical Split." One physical PostgreSQL cluster on Fly.io, but separate schemas for each service to allow for future physical separation if needed.
- **Conflict:** Tariq expressed concern that micro-frontends might increase initial load time. Zia argued that the security benefits of isolated domains outweigh the 200ms latency increase.
- **Action Item:** Tariq to research Module Federation for the frontend.

### Meeting 2: The "Raw SQL" Crisis (2024-02-15)
- **Attendees:** Bram, Zia, Zara.
- **Discussion:** Zara discovered that several "performance optimizations" in the Property Service used raw SQL that bypassed Ecto's migration tracking.
- **Decision:** All raw SQL queries must now be wrapped in a specific `PerformanceQuery` module and documented.
- **Bram's Note:** "We are trading long-term maintainability for short-term speed. We need to be careful not to let the technical debt snowball."

### Meeting 3: API Rate Limit Blocker (2024-05-20)
- **Attendees:** Bram, Tariq, Zara.
- **Discussion:** The team is unable to test the Sandbox API because the MLS provider is capping requests at 100 per hour.
- **Decision:** The team will build a "Mock Provider" service that simulates the MLS API. This allows development to continue while Bram negotiates a higher limit with the provider.
- **Status:** Feature 2 (Customer API) moved to "Blocked" status.

---

## 11. BUDGET BREAKDOWN

The total project budget is **$1,500,000**.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $975,000 | 4 full-time roles over 2.5 years. |
| **Infrastructure** | 15% | $225,000 | Fly.io hosting, S3 storage, Redis clusters. |
| **Software/Tools** | 10% | $150,000 | LaunchDarkly, SendGrid, Datadog, GitHub Enterprise. |
| **Contingency** | 10% | $150,000 | Reserved for emergency scaling or specialized consultants. |

**Spending Forecast:**
- **Year 1:** $600k (Heavy on personnel and tool setup).
- **Year 2:** $600k (Scaling infra and pilot support).
- **Year 3:** $300k (Maintenance and final launch phase).

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Checklist
To maintain the "Security" pillar of Project Ember, Zia Nakamura has mandated the following:
1. **Encryption at Rest:** All sensitive columns in PostgreSQL use `pgcrypto` or application-level AES-256-GCM.
2. **Encryption in Transit:** TLS 1.3 is enforced for all connections between the API Gateway and Microservices.
3. **Access Control:** No developer has direct access to the Production database. All queries must go through a bastion host with logged access.
4. **Auditability:** The `audit_logs` table must record the "who, what, when, and where" of every PII access.

### Appendix B: Technical Debt Registry (The "Wall of Shame")
This list is updated weekly by Zara Park to ensure the team does not ignore the "dangerous" parts of the codebase.

1. **Issue:** Property Search query uses a `JOIN` across 6 tables in raw SQL.
   - **Risk:** Schema change to `organizations` will crash the search.
   - **Fix:** Rewrite using Ecto.Query by Q3 2024.
2. **Issue:** PDF generation is currently synchronous in the dev environment.
   - **Risk:** Will timeout in production.
   - **Fix:** Move to `Oban` background workers.
3. **Issue:** Frontend uses a mix of LiveView and React.
   - **Risk:** Inconsistent state management.
   - **Fix:** Standardize on LiveView for all real-time components.