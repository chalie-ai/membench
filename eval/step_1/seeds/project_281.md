# PROJECT SPECIFICATION: PROJECT IRONCLAD
**Document Version:** 1.4.2  
**Status:** Active / In-Development  
**Classification:** Internal / Confidential  
**Last Updated:** 2025-10-12  
**Owner:** Haruki Nakamura, Engineering Manager  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Ironclad is the strategic initiative by Stratos Systems to replace the "Legacy Core," a 15-year-old monolithic collaboration system that serves as the operational backbone for our fintech services. The legacy system, while stable, is built on aging technology that cannot scale to meet current market demands, lacks modern API capabilities, and creates significant operational risk due to its "single point of failure" architecture. 

In the fintech sector, real-time collaboration is not merely a convenience but a regulatory and operational necessity. The legacy system currently suffers from latency spikes during peak trading hours and lacks the granular multi-tenancy required for our expanding global client base. The objective of Ironclad is to provide a high-performance, real-time collaboration tool that ensures zero downtime during the transition, as any service interruption would result in catastrophic financial loss and regulatory penalties.

### 1.2 Strategic Objectives
The primary goal is to migrate all existing users to the Ironclad platform without a single second of service unavailability. This requires a "strangler pattern" approach, where functionality is peeled away from the legacy system and routed to the new Go-based microservices architecture.

### 1.3 ROI Projection and Financial Impact
The $3M investment in Project Ironclad is projected to yield a positive ROI within 24 months of full deployment. 

**Cost Reduction:**
- **Operational Efficiency:** By moving to a Kubernetes-orchestrated environment on GCP and utilizing CockroachDB’s distributed nature, we project a 35% reduction in cost per transaction. The legacy system requires expensive, oversized vertical scaling; Ironclad will utilize horizontal scaling to optimize resource consumption.
- **Maintenance Costs:** Reducing the manual overhead required to maintain the 15-year-old codebase is estimated to save $400k annually in developer hours.

**Revenue Growth:**
- **Market Expansion:** The introduction of a customer-facing API (Feature 3) allows Stratos Systems to enter the "Platform-as-a-Service" (PaaS) market, potentially opening a new revenue stream estimated at $1.2M in the first year post-launch.
- **Customer Retention:** Improving real-time synchronization and offline capabilities will reduce churn among high-frequency trading clients who currently experience timeouts.

**Projected 3-Year Net Benefit:** $2.1M (after deducting initial $3M investment and ongoing GCP costs).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Ironclad is designed as a **modular monolith transitioning to microservices**. To avoid the "distributed monolith" trap, the team is building a single deployable unit with strict internal boundary enforcement (via Go packages) before splitting them into independent gRPC services.

### 2.2 The Tech Stack
- **Language:** Go 1.21+ (chosen for concurrency primitives and performance).
- **Communication:** gRPC for internal service-to-service communication; REST/JSON for the customer-facing API.
- **Database:** CockroachDB (Distributed SQL) to ensure high availability and regional data residency.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
- **CI/CD:** GitLab CI with Canary and Rolling deployments.
- **Security:** TLS 1.3 for all transit; AES-256 for data at rest.

### 2.3 System Diagram (ASCII Representation)
```text
                                 [ EXTERNAL USERS ]
                                         |
                                         v
                          +------------------------------+
                          |      GCP Cloud Load Balancer  |
                          +------------------------------+
                                         |
                                         v
                          +------------------------------+
                          |  API Gateway (Envoy/Istio)    | <--- Auth/SAML/OIDC
                          +------------------------------+
                                         |
         +-------------------------------+-------------------------------+
         |                               |                               |
         v                               v                               v
 [ Tenant Service ]              [ Collaboration Svc ]          [ Data Import Svc ]
 (Multi-tenancy Logic)            (Real-time Sync/Websockets)     (Format Auto-detect)
         |                               |                               |
         +-------------------------------+-------------------------------+
                                         |
                                         v
                          +------------------------------+
                          |      CockroachDB Cluster     |
                          | (EU-West-1 / US-East-1 / AS)  |
                          +------------------------------+
                                         ^
                                         |
                          +------------------------------+
                          |      Legacy Core Bridge      | <--- Dual-Write Sync
                          +------------------------------+
```

### 2.4 Data Residency and Compliance
To satisfy GDPR and CCPA, Ironclad utilizes CockroachDB’s "regional tables." Data belonging to EU citizens is pinned to the `eu-west-1` region. The system implements a strict "Hard Partition" logic where the Tenant ID determines the physical location of the data shards.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Critical | Status: Complete)
**Description:** 
Ironclad must support thousands of independent corporate clients (tenants) on a shared infrastructure while ensuring that no tenant can ever access another tenant's data. This is a "hard" isolation requirement.

**Functional Specifications:**
- **Logical Isolation:** Every database query must include a `tenant_id` filter. This is enforced at the repository layer using a middleware wrapper that injects the tenant context from the gRPC metadata.
- **Physical Sharding:** Using CockroachDB, rows are partitioned by `tenant_id`. This ensures that data for a specific tenant is co-located on the same nodes to minimize cross-region latency.
- **Tenant Provisioning:** When a new client is onboarded, the system must automatically create a tenant profile, assign a unique UUID, and initialize default permission sets.
- **Shared Infrastructure:** While data is isolated, the compute layer (Kubernetes pods) is shared. Resource quotas (CPU/RAM) are applied per tenant to prevent "noisy neighbor" syndrome.

**Validation:**
Validation is performed via a "Cross-Tenant Leak Test" suite, where a request with Tenant A's token attempts to access Resource B. Any successful access is marked as a P0 blocker.

### 3.2 Offline-First Mode with Background Sync (Priority: Critical | Status: Blocked)
**Description:** 
Users must be able to continue working on collaboration documents even when their internet connection is severed. Changes are stored locally and synchronized once connectivity is restored.

**Functional Specifications:**
- **Local Storage:** The frontend utilizes IndexedDB to cache the working set of documents. 
- **Conflict Resolution:** The system uses Conflict-free Replicated Data Types (CRDTs) to merge concurrent edits. LWW (Last Write Wins) is used for simple metadata, but sequence-based CRDTs are used for document text.
- **Background Synchronization:** A service worker monitors the network state. Upon reconnection, the client initiates a "Sync Handshake" using a version vector to determine which delta updates need to be pushed to the server.
- **Push Notifications:** The server sends a "Dirty State" flag via WebSocket to notify the client that the local cache is outdated.

**Current Blocker:** The team has encountered a race condition where the `sync_version` in CockroachDB is incrementing faster than the client can acknowledge, leading to infinite loop retries. This is currently assigned to Zia Santos.

### 3.3 Customer-Facing API with Versioning and Sandbox (Priority: Critical | Status: In Design)
**Description:** 
To enable integration with other fintech tools, Ironclad provides a public REST API. To ensure stability, a versioning strategy and a separate sandbox environment are required.

**Functional Specifications:**
- **API Versioning:** Versions are handled via the URL path (e.g., `/v1/documents`, `/v2/documents`). The system must support at least two concurrent versions.
- **Sandbox Environment:** A mirrored version of the production environment (on a smaller scale) where clients can test their integrations without affecting real data. The sandbox uses a separate `sandbox_tenant_id` prefix.
- **Rate Limiting:** Implemented via a Token Bucket algorithm. Tiers are defined as:
    - *Standard:* 100 requests/minute.
    - *Premium:* 1,000 requests/minute.
- **Authentication:** API keys are issued via the management console, hashed using SHA-256, and stored in the `api_keys` table.

**Deliverables:** 
- OpenAPI 3.0 Specification.
- Developer Portal with "Try it Now" functionality.

### 3.4 Data Import/Export with Format Auto-Detection (Priority: Critical | Status: Blocked)
**Description:** 
Users must be able to migrate data from the legacy system and other third-party tools into Ironclad. The system must automatically detect the file format (CSV, JSON, XML, proprietary legacy binary).

**Functional Specifications:**
- **Format Detection:** The system reads the first 4KB of an uploaded file (magic bytes) to determine the file type. If the type is unknown, it attempts to parse the first line as JSON or CSV.
- **Async Processing:** Large imports are handled via a worker queue (RabbitMQ). The user is notified via a WebSocket event once the import is complete.
- **Mapping Engine:** A UI-based tool allows users to map columns from their imported file to Ironclad’s internal schema.
- **Export:** Data can be exported in JSON or CSV formats, with a full audit log of who performed the export and where the data went.

**Current Blocker:** The legacy system exports data in a proprietary binary format that is not documented. The team is waiting for the legacy maintainer to provide the spec.

### 3.5 SSO Integration with SAML and OIDC (Priority: Low | Status: In Design)
**Description:** 
Enterprise clients require the ability to manage users via their own Identity Providers (IdPs) such as Okta, Azure AD, or Google Workspace.

**Functional Specifications:**
- **SAML 2.0:** Support for Service Provider (SP) initiated SSO. Ironclad provides the metadata XML for the client to upload to their IdP.
- **OIDC:** Integration with OpenID Connect for modern authentication flows, utilizing JWTs for session management.
- **Just-In-Time (JIT) Provisioning:** Users are automatically created in the Ironclad database upon their first successful SSO login, based on the claims passed in the SAML assertion.
- **Group Mapping:** Mapping SAML groups to internal Ironclad roles (e.g., `SAML_ADMIN` -> `SYSTEM_ADMIN`).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path: `https://api.ironclad.stratos.com/`

### 4.1 `POST /v1/auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Request Body:**
  ```json
  {
    "username": "user@client.com",
    "password": "hashed_password"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGci...",
    "expires_at": "2025-10-12T12:00:00Z"
  }
  ```

### 4.2 `GET /v1/tenants/{tenant_id}/documents`
- **Description:** Lists all documents for a specific tenant.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  [
    { "id": "doc_123", "name": "Q3 Projections", "last_modified": "2025-10-01" },
    { "id": "doc_456", "name": "Compliance Audit", "last_modified": "2025-10-05" }
  ]
  ```

### 4.3 `PATCH /v1/documents/{doc_id}`
- **Description:** Updates a specific document's content using a delta patch.
- **Request Body:**
  ```json
  {
    "delta": { "insert": "Updated text", "at": 150 },
    "version": 12
  }
  ```
- **Response (200 OK):**
  ```json
  { "status": "merged", "new_version": 13 }
  ```

### 4.4 `GET /v1/tenants/{tenant_id}/usage`
- **Description:** Returns resource usage metrics for the tenant (for billing).
- **Response (200 OK):**
  ```json
  {
    "storage_used_gb": 45.2,
    "api_calls_month": 120000,
    "active_users": 150
  }
  ```

### 4.5 `POST /v1/import/upload`
- **Description:** Uploads a file for format detection and import.
- **Request:** Multipart/form-data (file upload).
- **Response (202 Accepted):**
  ```json
  { "job_id": "job_998877", "status": "queued" }
  ```

### 4.6 `GET /v1/import/status/{job_id}`
- **Description:** Checks the progress of an import job.
- **Response (200 OK):**
  ```json
  { "job_id": "job_998877", "progress": "65%", "status": "processing" }
  ```

### 4.7 `POST /v1/export/request`
- **Description:** Triggers a full data export for a tenant.
- **Request Body:** `{ "format": "json", "scope": "all" }`
- **Response (202 Accepted):**
  ```json
  { "download_url": "https://exports.ironclad.com/dl/xyz123", "expires": "24h" }
  ```

### 4.8 `DELETE /v1/tenants/{tenant_id}/users/{user_id}`
- **Description:** Removes a user from a tenant (GDPR Right to Erasure).
- **Response (204 No Content):**
  - *Success.*

---

## 5. DATABASE SCHEMA (CockroachDB)

The database follows a distributed schema. All tables are partitioned by `tenant_id`.

### 5.1 Tables Definition

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | None | `name`, `region`, `plan_id`, `created_at` | Core tenant metadata. |
| `users` | `user_id` | `tenant_id` | `email`, `password_hash`, `last_login` | User account details. |
| `documents` | `doc_id` | `tenant_id`, `owner_id` | `title`, `content_ref`, `version` | Document metadata. |
| `document_deltas`| `delta_id` | `doc_id` | `user_id`, `change_data`, `timestamp` | CRDT operation log. |
| `permissions` | `perm_id` | `tenant_id`, `user_id`, `doc_id` | `role` (READ, WRITE, ADMIN) | ACL for documents. |
| `api_keys` | `key_id` | `tenant_id`, `user_id` | `hashed_key`, `expires_at` | API access tokens. |
| `import_jobs` | `job_id` | `tenant_id` | `status`, `file_path`, `error_log` | Tracking data imports. |
| `audit_logs` | `log_id` | `tenant_id`, `user_id` | `action`, `resource_id`, `ip_address` | Compliance tracking. |
| `tenant_configs` | `config_id` | `tenant_id` | `key`, `value` (JSONB) | Custom tenant settings. |
| `sso_providers` | `provider_id` | `tenant_id` | `provider_type`, `entity_id`, `cert` | SSO configuration. |

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `tenants` $\rightarrow$ `documents`, `tenants` $\rightarrow$ `api_keys`.
- **One-to-Many:** `documents` $\rightarrow$ `document_deltas`.
- **Many-to-Many:** `users` $\leftrightarrow$ `documents` (via `permissions` table).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature experimentation and individual developer testing.
- **Infrastructure:** Single-node Kubernetes cluster on GKE.
- **Database:** Local CockroachDB instance in a single-node configuration.
- **Deployment:** Triggered on every push to a feature branch.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Integration testing, QA, and Stakeholder Demos.
- **Infrastructure:** Multi-zone GKE cluster mimicking Production.
- **Database:** 3-node CockroachDB cluster.
- **Deployment:** Triggered on merge to `main`. Includes a full suite of automated integration tests.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live customer traffic.
- **Infrastructure:** Multi-regional GKE cluster (EU, US, ASIA).
- **Database:** 9-node CockroachDB cluster distributed globally.
- **Deployment:** Rolling updates via GitLab CI. Canary deployments route 5% of traffic to the new version for 1 hour before full rollout.

### 6.2 CI/CD Pipeline
The pipeline is managed via `.gitlab-ci.yml`:
1. **Lint/Test:** Go linting and unit tests.
2. **Build:** Docker image creation and push to Google Container Registry (GCR).
3. **Deploy to Staging:** Automated deployment to staging.
4. **Integration Test:** Run E2E test suite against staging.
5. **Manual Approval:** Required for Production deployment.
6. **Canary Release:** Deploy to 5% of pods $\rightarrow$ monitor error rates $\rightarrow$ full rollout.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic in Go packages.
- **Requirement:** All new functions must have $>80\%$ code coverage.
- **Tooling:** `go test`, `mockery` for mocking gRPC clients.

### 7.2 Integration Testing
- **Focus:** Interaction between microservices and CockroachDB.
- **Approach:** Use `Testcontainers` to spin up a real CockroachDB instance during the CI process.
- **Key Scenarios:** 
    - Tenant A cannot access Tenant B's data.
    - API rate limits are enforced correctly.
    - gRPC timeouts are handled gracefully.

### 7.3 End-to-End (E2E) Testing
- **Focus:** The full user journey from UI to Database.
- **Tooling:** Playwright for browser automation.
- **Critical Path:**
    1. User logs in $\rightarrow$ Creates document $\rightarrow$ Edits document $\rightarrow$ Refreshes page $\rightarrow$ Data persists.
    2. User goes offline $\rightarrow$ Edits document $\rightarrow$ Goes online $\rightarrow$ Syncs successfully.

### 7.4 Performance Testing
- **Focus:** Ensuring the 10x capacity requirement.
- **Tooling:** k6.io for load testing.
- **Benchmark:** Simulate 100,000 concurrent WebSocket connections with a 50ms p99 latency requirement for document updates.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding 'small' features. | High | Medium | Implement a strict Change Request (CR) process. Negotiate timeline extensions for any non-critical additions. |
| R-02 | Performance requirements 10x legacy with no budget increase. | Medium | High | Engage external consultant for independent assessment of GKE/CockroachDB tuning. |
| R-03 | Legacy system "undocumented" binary format blocks import. | High | Medium | Dedicate Zia Santos to reverse-engineer binary blobs; request legacy vendor support. |
| R-04 | Team dysfunction (PM/Lead disconnect). | High | High | Implement structured weekly syncs moderated by an external department head. |
| R-05 | Regional data residency failure (GDPR). | Low | Critical | Implement automated "Data Location Audits" that run weekly to verify row locality. |

**Impact Matrix:**
- **Critical:** Project failure or legal action.
- **High:** Significant delay or major budget overrun.
- **Medium:** Minor delay or manageable cost increase.
- **Low:** Negligible impact.

---

## 9. TIMELINE AND MILESTONES

The project is executed in phases. Dependencies are marked as (D).

### 9.1 Phase 1: Foundation (Current - June 2026)
- **Development of Multi-tenant Core:** Complete.
- **SAML/OIDC Design:** In Progress.
- **Security Audit Preparation:** In Progress.
- **Milestone 1: Security Audit Passed** $\rightarrow$ **Target: 2026-06-15**.

### 9.2 Phase 2: Feature Parity (June 2026 - August 2026)
- **Unblocking Offline Sync:** (D: Fix CockroachDB race condition).
- **Implementing Import/Export:** (D: Obtain legacy binary spec).
- **Public API Beta:** (D: Finalize sandbox environment).
- **Milestone 2: Performance Benchmarks Met** $\rightarrow$ **Target: 2026-08-15**.

### 9.3 Phase 3: Transition & Launch (August 2026 - October 2026)
- **Legacy Data Migration:** Moving users in batches.
- **Zero-Downtime Cutover:** Routing traffic via API Gateway.
- **Stakeholder UAT:** User Acceptance Testing.
- **Milestone 3: Stakeholder Demo and Sign-off** $\rightarrow$ **Target: 2026-10-15**.

---

## 10. MEETING NOTES (Sourced from Shared Running Doc)

*Note: These notes are extracted from the 200-page unsearchable shared document.*

### Meeting 1: Architecture Review (2025-11-12)
**Attendees:** Haruki, Zia, Thiago, Astrid.
- **Discussion:** Zia argued that the "modular monolith" is just a monolith with extra steps. He wants to jump straight to 15 microservices. Haruki denied this, citing the need for stability.
- **Conflict:** Haruki and the PM (not present) had a disagreement via email regarding the deadline. Haruki stated the timeline is unrealistic given the current lack of structured logging.
- **Decision:** Proceed with the modular monolith approach. Zia to implement the Tenant isolation layer.
- **Action Item:** Astrid to draft the initial CockroachDB schema.

### Meeting 2: UX & Offline Mode (2026-01-20)
**Attendees:** Thiago, Zia, Haruki.
- **Discussion:** Thiago presented the UX for "Offline Mode." He wants a visible "Syncing..." indicator that changes color based on the percentage of data pushed. 
- **Technical Constraint:** Zia noted that calculating the exact percentage of sync for CRDTs is computationally expensive.
- **Decision:** Use a simplified "Syncing / Synced" binary status instead of a percentage.
- **Observation:** The meeting was interrupted twice because Haruki and the PM were arguing over the budget for an external consultant.

### Meeting 3: API Design & Sandbox (2026-03-05)
**Attendees:** Astrid, Zia, Haruki.
- **Discussion:** Astrid proposed using a separate GCP project for the Sandbox environment to ensure total isolation.
- **Concern:** Haruki worried about the cost of running a second GKE cluster.
- **Decision:** Use a separate namespace in the Staging cluster for the Sandbox to save costs, but use a separate CockroachDB cluster.
- **Technical Debt Note:** Zia mentioned that debugging the Sandbox is nearly impossible because the team is still reading `stdout` instead of using structured logging. Haruki told him to "focus on the launch blockers" first.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

### 11.1 Personnel ($2,100,000)
- **Engineering Team (15 FTEs):** $1,600,000 (Avg. $106k/year).
- **UX Research & Design (3 FTEs):** $300,000.
- **Contractors (Astrid Gupta & Others):** $200,000.

### 11.2 Infrastructure ($450,000)
- **GCP Consumption:** $300,000 (GKE, Cloud Storage, Load Balancers).
- **CockroachDB Enterprise Licensing:** $100,000.
- **GitLab CI/CD Premium:** $50,000.

### 11.3 Tools & Services ($200,000)
- **Security Auditing Firm:** $100,000 (For Milestone 1).
- **External Performance Consultant:** $70,000 (For Risk R-02).
- **Testing Tooling (Playwright/k6 Licenses):** $30,000.

### 11.4 Contingency ($250,000)
- **Reserve Fund:** $250,000 (Allocated for unexpected infrastructure spikes or timeline extensions due to scope creep).

---

## 12. APPENDICES

### Appendix A: Logging Technical Debt Resolution Plan
The current state of logging (reading `stdout`) is unacceptable for a fintech product. 
- **Proposed Solution:** Transition to `uber-go/zap` for structured JSON logging.
- **Pipeline:** Logs $\rightarrow$ Fluentbit $\rightarrow$ Google Cloud Logging (Stackdriver).
- **Fields to be captured:** `tenant_id`, `request_id`, `user_id`, `latency_ms`, `severity`.
- **Timeline:** This will be addressed as a "Technical Debt Sprint" immediately following Milestone 2.

### Appendix B: CRDT Implementation Details
To achieve the offline-first requirement, Ironclad implements an **LWW-Element-Set** and a **Sequence CRDT**.
- **State Vector:** Each client maintains a vector clock.
- **Causality:** If an update arrives with a version vector that is not contiguous, the system requests a "gap fill" from the server.
- **Garbage Collection:** To prevent the delta log from growing infinitely, the server performs "Snapshotting" every 1,000 operations, collapsing the history into a single base state.