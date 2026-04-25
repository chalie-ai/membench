# PROJECT SPECIFICATION: PROJECT CANOPY
**Document Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2023  
**Project Lead:** Kai Liu (Engineering Manager)  
**Confidentiality:** Internal Use Only – Verdant Labs

---

## 1. EXECUTIVE SUMMARY

**Business Justification**
Project Canopy is a mission-critical initiative for Verdant Labs, designed to replace the "Legacy Core," a 15-year-old monolithic system that currently serves as the backbone for all media production and distribution workflows within the company. For over a decade, the Legacy Core has maintained the company's operational stability, but it has now reached a state of technical insolvency. The system is written in deprecated languages, lacks documentation, and possesses a fragile codebase where a single commit in the billing module can inadvertently crash the content delivery pipeline.

The primary driver for Canopy is the "Zero Downtime Tolerance" mandate. Because the entire enterprise depends on this system for real-time media asset management and client billing, any outage exceeding 15 minutes results in an estimated loss of $45,000 in operational productivity and potential contractual penalties with external media partners. The current legacy system is incapable of scaling to meet the demands of Verdant Labs' current growth trajectory, particularly in the realms of multi-tenancy and internationalization.

**Objectives**
Canopy seeks to transition the organization to a modern, clean monolith architecture that preserves the performance of a single-process system while enforcing strict module boundaries. This will allow for phased migration (Strangler Fig pattern), where legacy modules are decommissioned one by one.

**ROI Projection**
The Return on Investment for Project Canopy is calculated across three primary vectors:
1. **Operational Efficiency:** By automating the workflow engine (replacing manual script interventions), we project a 30% reduction in manual operator hours, saving approximately $1.2M annually in labor costs.
2. **Infrastructure Cost Reduction:** Moving from the legacy mainframe-style hosting to a shared-infrastructure multi-tenant model is expected to reduce cloud overhead by $250,000 per year.
3. **Risk Mitigation:** The elimination of the "Legacy Core" removes the catastrophic risk of a total system failure due to outdated dependencies that are no longer patched for security vulnerabilities.

**Financial Framework**
Funding for Canopy is not provided as a lump sum. Instead, Verdant Labs has implemented a milestone-based funding model. Budget tranches are released upon the successful verification of specific technical milestones (e.g., successful data migration of the first tenant). This ensures that the project remains accountable to the business goals and prevents "sunk cost" fallacies in the event of architectural pivots.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Canopy is designed as a **Clean Monolith**. While the industry has trended toward microservices, Verdant Labs has opted for a modular monolith to avoid the network latency and complexity overhead that would hinder the p95 response time goals. 

The architecture enforces strict boundaries:
- **API Layer:** Handles request validation, authentication, and versioning.
- **Domain Layer:** Contains pure business logic, isolated from database and external API concerns.
- **Infrastructure Layer:** Handles database persistence, cache management, and third-party integrations.

### 2.2 Stack Interoperability
Canopy is inheriting three disparate stacks from previous internal attempts at modernization:
1. **The Legacy Java Stack:** Used for heavy-duty media processing.
2. **The Node.js Middleware:** Used for rapid API prototyping.
3. **The Python Data Layer:** Used for asset metadata indexing.

These three stacks interoperate via a shared Redis backplane and a unified PostgreSQL database. Communication between these inherited modules is handled through a strict internal event bus to prevent tight coupling.

### 2.3 ASCII Architecture Diagram
```text
[ Client Layer ]  --> [ Load Balancer (Nginx) ]
                               |
                               v
[ API Gateway (Node.js) ] <--> [ Auth Module (SAML/OIDC) ]
          |
          +-------------------+-------------------+
          |                   |                   |
[ Workflow Engine ]   [ Tenant Manager ]   [ Asset API ]
(Python/Celery)       (Java/Spring)        (Node.js/TS)
          |                   |                   |
          +-------------------+-------------------+
                               |
                    [ Shared Redis Cache ]
                               |
                    [ PostgreSQL Cluster ]
                               |
                    [ S3 Media Storage ]
```

### 2.4 Deployment Strategy
The deployment process is currently highly centralized. A single DevOps engineer manages the entire pipeline via manual triggers. 
- **Bus Factor:** 1. (Critical Risk)
- **Pipeline:** Jenkins-based CI/CD.
- **The "45-Minute Bottleneck":** The current CI pipeline is unoptimized. It runs all 12,000+ unit tests sequentially and performs a full image rebuild on every commit. This creates a significant drag on developer velocity.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-Tenant Data Isolation (Priority: High | Status: In Review)
**Description:**
Canopy must support multiple business units (tenants) within Verdant Labs, each requiring strict data isolation to prevent cross-tenant data leakage. Because we are using shared infrastructure (a single PostgreSQL cluster), isolation must be handled at the application and database levels.

**Detailed Requirements:**
- **Row-Level Security (RLS):** Every table containing tenant-specific data must include a `tenant_id` column. PostgreSQL RLS policies will be implemented to ensure that a session authenticated for Tenant A cannot query rows belonging to Tenant B.
- **Tenant Provisioning:** An administrative interface must allow the creation of new tenants, assigning them specific quotas for storage and API rate limits.
- **Shared Schema:** To minimize maintenance overhead, all tenants share the same schema. The logic for isolation resides in the `TenantContext` provider within the application code.
- **Data Migration:** A utility must be developed to migrate legacy data from the monolithic "all-in-one" legacy tables into the new tenant-aware schema without taking the system offline.

**Acceptance Criteria:**
1. A query performed by a user from Tenant A must return a 403 or empty set when attempting to access a Resource ID belonging to Tenant B.
2. Tenant onboarding must be completed in under 5 minutes.

### 3.2 Workflow Automation Engine (Priority: Medium | Status: Complete)
**Description:**
A visual rule builder allowing non-technical users to define "If-This-Then-That" (IFTTT) logic for media asset processing. For example: "If a video file is uploaded in 4K and tagged 'Raw', then trigger the 'Proxy Generation' worker and notify the lead editor."

**Detailed Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface (implemented using React Flow) where users can connect triggers (events) to actions (tasks).
- **Rule Engine:** A backend processor that evaluates incoming events against active rules using a JSON-logic based evaluation system.
- **State Machine:** The engine must track the state of a workflow (Pending $\rightarrow$ Processing $\rightarrow$ Completed/Failed) and allow for manual restarts of failed steps.
- **Concurrency Control:** The engine must handle up to 500 concurrent workflow executions per tenant without degrading performance.

**Acceptance Criteria:**
1. Users can create a 3-step workflow (Trigger $\rightarrow$ Filter $\rightarrow$ Action) via the UI.
2. The engine processes an event in under 500ms from trigger to action initiation.

### 3.3 Localization and Internationalization (Priority: Medium | Status: Not Started)
**Description:**
Verdant Labs is expanding its operations to EMEA and APAC regions. Canopy must support 12 languages (including English, Mandarin, Japanese, French, German, Spanish, Korean, Arabic, Portuguese, Hindi, Italian, and Russian).

**Detailed Requirements:**
- **i18n Framework:** Use of `i18next` for the frontend and a centralized translation management system (TMS) for the backend.
- **Dynamic Translation Loading:** The application must detect the user's locale via the `Accept-Language` header or user profile settings and load the corresponding JSON translation bundle.
- **Right-to-Left (RTL) Support:** The UI must support mirroring for Arabic, ensuring that the layout flips correctly without breaking the visual rule builder.
- **Unicode Compliance:** All database fields must use `UTF8` encoding to support non-Latin character sets.

**Acceptance Criteria:**
1. Toggle between English and Japanese updates all UI labels without a page refresh.
2. Arabic layout mirrors correctly (RTL) in the dashboard.

### 3.4 SSO Integration (Priority: Low | Status: In Progress)
**Description:**
Integration with the corporate identity provider to ensure seamless access and centralized user management.

**Detailed Requirements:**
- **SAML 2.0:** Support for Okta as the primary identity provider for corporate employees.
- **OIDC:** Support for OpenID Connect for external contractors and partners.
- **Just-In-Time (JIT) Provisioning:** When a user logs in via SSO for the first time, a local user account must be created automatically with roles mapped from the SSO assertions.
- **Session Management:** Implementation of secure, rotating JWTs (JSON Web Tokens) with a 12-hour expiration and refresh token rotation.

**Acceptance Criteria:**
1. User can log in via the "Corporate SSO" button and be redirected to the dashboard.
2. User roles in Okta (e.g., "Admin") map correctly to Canopy roles.

### 3.5 Customer-Facing API (Priority: Low | Status: In Review)
**Description:**
A public-facing REST API that allows external partners to programmatically upload assets and trigger workflows.

**Detailed Requirements:**
- **API Versioning:** Use of URI versioning (e.g., `/v1/assets`, `/v2/assets`) to ensure backward compatibility.
- **Sandbox Environment:** A mirrored environment (`sandbox.api.verdantlabs.com`) where customers can test their integrations without affecting production data.
- **API Key Management:** A portal where users can generate, rotate, and revoke API keys.
- **Rate Limiting:** Implementation of a token-bucket algorithm to limit users to 1,000 requests per hour in the free tier and 10,000 in the premium tier.

**Acceptance Criteria:**
1. API v1 remains functional while API v2 introduces breaking changes.
2. A request to the sandbox environment does not create records in the production database.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Base URL: `https://canopy.verdantlabs.com/api/v1`

### 4.1 `GET /assets`
**Description:** Retrieves a paginated list of media assets for the authenticated tenant.
- **Query Params:** `page` (int), `limit` (int), `filter` (string)
- **Request Example:** `GET /api/v1/assets?page=1&limit=20`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "asset_9921", "name": "scene_01_take_4.mov", "status": "processing", "size": 104857600 }
  ],
  "pagination": { "total": 150, "page": 1, "pages": 8 }
}
```

### 4.2 `POST /assets`
**Description:** Uploads a new media asset and associates it with a tenant.
- **Request Body:** Multipart form-data (file, metadata)
- **Response (201 Created):**
```json
{ "id": "asset_9922", "status": "uploaded", "url": "/assets/download/asset_9922" }
```

### 4.3 `GET /assets/{id}`
**Description:** Retrieves detailed metadata for a specific asset.
- **Response (200 OK):**
```json
{ "id": "asset_9921", "tenant_id": "tenant_44", "codec": "ProRes 422", "resolution": "3840x2160" }
```

### 4.4 `PUT /assets/{id}`
**Description:** Updates asset metadata or tags.
- **Request Body:** `{ "tags": ["final", "color-graded"], "description": "Updated version" }`
- **Response (200 OK):** `{ "id": "asset_9921", "updated_at": "2023-10-24T10:00:00Z" }`

### 4.5 `POST /workflows/execute`
**Description:** Manually triggers a specific workflow by ID.
- **Request Body:** `{ "workflow_id": "wf_001", "asset_id": "asset_9921" }`
- **Response (202 Accepted):** `{ "execution_id": "exe_554", "status": "queued" }`

### 4.6 `GET /workflows/status/{execution_id}`
**Description:** Checks the progress of a triggered workflow.
- **Response (200 OK):** `{ "execution_id": "exe_554", "progress": "45%", "current_step": "Proxy Generation" }`

### 4.7 `POST /tenants/onboard`
**Description:** (Admin only) Creates a new tenant and allocates resources.
- **Request Body:** `{ "company_name": "Global Media Ltd", "region": "EU-West-1", "quota_gb": 5000 }`
- **Response (201 Created):** `{ "tenant_id": "tenant_45", "api_key": "sk_live_xxxx" }`

### 4.8 `GET /auth/session`
**Description:** Validates the current session and returns user roles.
- **Response (200 OK):** `{ "user": "j.doe", "roles": ["editor", "admin"], "expires": "2023-10-24T22:00:00Z" }`

---

## 5. DATABASE SCHEMA

**Database:** PostgreSQL 15.4  
**Isolation Strategy:** `tenant_id` foreign key on all operational tables.

### 5.1 Table Definitions

1.  **`tenants`**
    - `id` (UUID, PK): Unique tenant identifier.
    - `name` (VARCHAR): Name of the business unit.
    - `created_at` (TIMESTAMP): Account creation date.
    - `status` (ENUM): 'active', 'suspended', 'pending'.
    - `plan_level` (VARCHAR): 'basic', 'premium', 'enterprise'.

2.  **`users`**
    - `id` (UUID, PK): Unique user identifier.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id): The tenant the user belongs to.
    - `email` (VARCHAR, UNIQUE): User email.
    - `password_hash` (TEXT): Argon2id hash.
    - `last_login` (TIMESTAMP): Last authentication timestamp.

3.  **`user_roles`**
    - `user_id` (UUID, FK $\rightarrow$ users.id)
    - `role_name` (VARCHAR): 'admin', 'editor', 'viewer'.
    - `assigned_at` (TIMESTAMP).

4.  **`assets`**
    - `id` (UUID, PK): Unique asset ID.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id): Ownership.
    - `file_path` (TEXT): S3 pointer.
    - `file_size` (BIGINT): Size in bytes.
    - `mime_type` (VARCHAR): e.g., 'video/quicktime'.
    - `created_at` (TIMESTAMP).

5.  **`asset_metadata`**
    - `asset_id` (UUID, FK $\rightarrow$ assets.id)
    - `key` (VARCHAR): e.g., 'resolution'.
    - `value` (TEXT): e.g., '4K'.

6.  **`workflows`**
    - `id` (UUID, PK): Workflow definition ID.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `name` (VARCHAR): Human readable name.
    - `definition_json` (JSONB): The visual rule builder output.
    - `is_active` (BOOLEAN).

7.  **`workflow_executions`**
    - `id` (UUID, PK): Execution instance ID.
    - `workflow_id` (UUID, FK $\rightarrow$ workflows.id)
    - `asset_id` (UUID, FK $\rightarrow$ assets.id)
    - `status` (ENUM): 'queued', 'running', 'completed', 'failed'.
    - `started_at` (TIMESTAMP).
    - `finished_at` (TIMESTAMP).

8.  **`workflow_steps`**
    - `id` (UUID, PK)
    - `execution_id` (UUID, FK $\rightarrow$ workflow_executions.id)
    - `step_name` (VARCHAR)
    - `status` (VARCHAR)
    - `logs` (TEXT).

9.  **`api_keys`**
    - `key_hash` (VARCHAR, PK): Hashed version of the API key.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `created_at` (TIMESTAMP).
    - `expires_at` (TIMESTAMP).

10. **`audit_logs`**
    - `id` (BIGSERIAL, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `user_id` (UUID, FK $\rightarrow$ users.id)
    - `action` (VARCHAR): e.g., 'ASSET_DELETE'.
    - `timestamp` (TIMESTAMP).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Overview
Canopy utilizes a three-tier environment strategy to ensure the "Zero Downtime" requirement is met during the transition from legacy.

| Environment | Purpose | Infrastructure | Data Source |
| :--- | :--- | :--- | :--- |
| **Development** | Feature iteration | Dockerized Local / Dev-K8s | Mock Data / Seeded DB |
| **Staging** | QA & UAT | Shared K8s Cluster (Staging namespace) | Anonymized Production Snapshot |
| **Production** | Live Enterprise Traffic | High-Availability K8s (Multi-AZ) | Live Production DB |

### 6.2 Infrastructure Components
- **Compute:** Amazon EKS (Elastic Kubernetes Service) managing pods for the three disparate stacks.
- **Database:** Amazon RDS for PostgreSQL with Multi-AZ deployment for failover.
- **Cache:** Amazon ElastiCache (Redis) used for session storage and inter-module communication.
- **Storage:** Amazon S3 with Intelligent-Tiering for media asset storage.
- **Networking:** AWS Application Load Balancer (ALB) routing traffic based on path (`/api` $\rightarrow$ Node.js, `/workflow` $\rightarrow$ Python).

### 6.3 Deployment Workflow (Manual)
Currently, deployments are executed manually by the single DevOps engineer:
1. **Build:** Jenkins triggers a build of the Docker images.
2. **Push:** Images are pushed to Amazon ECR.
3. **Apply:** `kubectl apply -f k8s/production/` is executed manually.
4. **Verification:** Smoke tests are run against the `/health` endpoint.

**Critical Note:** This process is a known single point of failure. Automation via ArgoCD is proposed for Q4 2024.

---

## 7. TESTING STRATEGY

To replace a system the entire company depends on, the testing rigor must be absolute.

### 7.1 Unit Testing
- **Coverage Goal:** 80% minimum line coverage for the Domain Layer.
- **Tools:** Jest (Node.js), PyTest (Python), JUnit (Java).
- **Execution:** Run during the CI pipeline. (Currently contributing to the 45-minute delay).

### 7.2 Integration Testing
- **Focus:** Testing the boundaries between the three inherited stacks.
- **Approach:** Using "Contract Testing" (Pact) to ensure that the Node.js API layer and the Python Workflow engine agree on the JSON schema for asset requests.
- **Database Testing:** Each integration test runs in a dedicated PostgreSQL schema that is wiped and recreated to ensure idempotency.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user paths (e.g., Asset Upload $\rightarrow$ Workflow Trigger $\rightarrow$ Process Completion).
- **Tools:** Playwright for frontend flow validation.
- **Zero-Downtime Validation:** Use of "Shadow Traffic" where a percentage of live requests from the Legacy Core are mirrored to Canopy to compare outputs without affecting the user.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Team lacks experience in mixed-stack (Java/Node/Python) interoperability. | High | High | Hire a specialist contractor to architect the event bus and reduce the "bus factor." |
| **R-02** | Project sponsor (VP of Ops) rotates out of role, leading to budget cuts. | Medium | High | Engage an external consultant for an independent assessment to validate ROI to the new sponsor. |
| **R-03** | Legacy system data is too corrupt for clean migration. | Medium | Medium | Implement a "Data Cleaning" layer in the migration script with manual override flags. |
| **R-04** | CI Pipeline bottleneck (45 mins) slows time-to-market. | High | Medium | Parallelize test suites and implement incremental builds. |
| **R-05** | Single DevOps person leaves (Bus Factor 1). | Medium | Critical | Document all manual steps in Wiki and prioritize the move to ArgoCD. |

**Impact Matrix:**
- **High:** Project failure or $>1$ hour downtime.
- **Medium:** Feature delay or minor performance degradation.
- **Low:** Cosmetic bugs or non-critical tool issues.

---

## 9. TIMELINE AND PHASES

The project follows a phased rollout to satisfy the zero-downtime requirement.

### Phase 1: Foundation (Now $\rightarrow$ 2024-12-01)
- **Focus:** Core architecture, Tenant Isolation, and Workflow Engine completion.
- **Dependency:** Agreement on design between Product and Engineering.
- **Key Milestone:** Internal Alpha release.

### Phase 2: Integration & Migration (2024-12-01 $\rightarrow$ 2025-06-15)
- **Focus:** SSO integration, Localization, and gradual migration of legacy data.
- **Dependency:** Contractor onboarding for stack expertise.
- **Milestone 1:** **Production Launch (2025-06-15)**.

### Phase 3: Expansion & Monetization (2025-06-15 $\rightarrow$ 2025-08-15)
- **Focus:** Customer-facing API and Sandbox environment.
- **Dependency:** Stability of the core tenant manager.
- **Milestone 2:** **First Paying Customer Onboarded (2025-08-15)**.

### Phase 4: Optimization & Stabilization (2025-08-15 $\rightarrow$ 2025-10-15)
- **Focus:** Performance tuning (p95 targets) and CI pipeline optimization.
- **Dependency:** Post-launch telemetry data.
- **Milestone 3:** **Post-launch stability confirmed (2025-10-15)**.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-02)
- *Attendees:* Kai Liu, Gideon Nakamura, DevOps Lead.
- *Notes:*
    - Gideon hates the mixed stack.
    - Discussion on monolithic vs microservices.
    - Kai decided on "Clean Monolith."
    - DevOps says CI is too slow (45 mins).
    - Action: Gideon to map out module boundaries.

### Meeting 2: Product Review (2023-11-15)
- *Attendees:* Kai Liu, Product Manager, Rosa Park.
- *Notes:*
    - PM wants more "flashy" features for the API.
    - Kai says "no" to API priority. Focus on tenants first.
    - **BLOCKER:** Disagreement on whether the visual rule builder should support loops.
    - Rosa asked about the intern's role in the API design.
    - Decision: Loops are out of scope for v1.

### Meeting 3: Risk Assessment (2023-12-01)
- *Attendees:* Kai Liu, Callum Jensen, VP of Ops.
- *Notes:*
    - VP might move to the London office in Jan.
    - Callum concerned about E2E test coverage for the legacy migration.
    - Agreed to hire contractor for Python/Java bridge.
    - Budget tranche 2 approved pending "Tenant Isolation" demo.

---

## 11. BUDGET BREAKDOWN

Total budget is variable and released in tranches. The projected spend for the current fiscal year is distributed as follows:

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $2,100,000 | 20+ full-time staff across 3 departments. |
| **Infrastructure** | 15% | $480,000 | AWS EKS, RDS, S3, and Redis costs. |
| **External Services**| 10% | $320,000 | Stack contractor and independent consultant. |
| **Software Tools** | 5% | $80,000 | Jenkins, Playwright, i18n TMS licenses. |
| **Contingency** | 5% | $160,000 | Reserved for emergency scaling or pivots. |
| **Total** | **100%** | **$3,140,000** | |

---

## 12. APPENDICES

### Appendix A: Performance Target Benchmarks
To achieve the **p95 < 200ms** response time, the following constraints are applied to all API endpoints:
- **DB Query Limit:** No request may execute more than 5 separate SQL queries. Use of `JOIN` or `JSONB` aggregation is mandated.
- **Cache Strategy:** The `/assets/{id}` endpoint must have a Redis TTL of 300 seconds.
- **Payload Size:** Maximum response payload for list endpoints is 1MB. Pagination is mandatory for any result set $> 100$ items.

### Appendix B: Legacy Data Migration Mapping
| Legacy Table | Canopy Table | Transformation Logic |
| :--- | :--- | :--- |
| `old_media_blob` | `assets` | Move binary to S3; store pointer in `file_path`. |
| `user_master` | `users` | Map `legacy_id` to `UUID`. |
| `client_config` | `tenants` | Group by `client_id` to create unique `tenant_id`. |
| `meta_dump` | `asset_metadata` | Parse unstructured text into Key-Value pairs. |