Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. To maintain the requested depth, it includes granular technical schemas, exhaustive feature breakdowns, and simulated organizational documentation.

***

# PROJECT SPECIFICATION: HALCYON
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 24, 2023  
**Company:** Stormfront Consulting  
**Classification:** Confidential – Internal Use Only

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Halcyon** is a mission-critical data pipeline and analytics platform engineered for the legal services industry. The primary objective of Halcyon is to facilitate a strategic partnership integration, allowing Stormfront Consulting to synchronize complex legal data sets with an external partner's API. Because the partner operates on a proprietary timeline, Halcyon is designed as a resilient, asynchronous bridge that can ingest, transform, and visualize legal analytics without risking data loss or system instability.

### 1.2 Business Justification
The legal services market is currently shifting toward data-driven decision-making. Stormfront Consulting identifies a gap in the market for high-integrity, GDPR/CCPA-compliant pipelines that can handle the sensitivity of attorney-client privileged data while providing executive-level insights via an analytics dashboard. By integrating with our partner’s API, we gain access to a proprietary data stream that allows our consultants to offer predictive legal spend analytics and case-outcome forecasting.

The strategic value lies in the "moat" created by this integration. By being the first to operationalize this specific external API, Stormfront Consulting positions itself as the premier consultancy for high-net-worth legal firms requiring digitized intelligence.

### 1.3 ROI Projection and Success Metrics
The financial viability of Halcyon is predicated on a modest initial investment of $400,000. The ROI is projected based on the following success criteria:

*   **Metric 1: Revenue Generation.** The platform must attribute **$500,000 in new revenue** within the first 12 months of production launch. This will be achieved through a "Premium Analytics" subscription tier for existing clients and the acquisition of three new enterprise legal accounts.
*   **Metric 2: Customer Satisfaction.** A target **Net Promoter Score (NPS) of >40** within the first quarter post-launch. This ensures that the user experience is intuitive and the data accuracy is trusted.

Given the budget of $400k and a projected $500k revenue increase in Year 1, the project reaches a break-even point within approximately 9 months of deployment, assuming a steady state of operational costs.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Halcyon utilizes a **Hexagonal Architecture** to decouple the core business logic (the "Domain") from the external infrastructure (the "Adapters"). This is critical because the external partner's API is subject to change on their timeline; by using ports, we can swap out the API adapter without rewriting the core data pipeline.

*   **The Core:** Contains the legal analytics domain models and business rules (e.g., case valuation logic, data normalization rules).
*   **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IDataSource`, `IUserRepository`).
*   **Adapters:** Concrete implementations of ports. Examples include the `ExternalPartnerAPIAdapter`, the `MongoDBAdapter`, and the `FastAPIController`.

### 2.2 System Component Diagram (ASCII Description)
```text
[ External Partner API ] <--> [ API Adapter (Port) ] 
                                      |
                                      v
[ User Interface ] <--> [ FastAPI Controllers ] <--> [ Domain Core ]
                                      |                    ^
                                      v                    |
[ MongoDB Store ] <--> [ Repository Adapter (Port) ] <-----+
                                      |
                                      v
[ Celery Worker ] <--> [ Task Queue / Redis ] <--> [ Background Sync Engine ]
                                      |
                                      v
[ S3/CDN Bucket ] <--> [ File Upload Adapter ] <--> [ Virus Scanner (ClamAV) ]
```

### 2.3 Technical Stack
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (Asynchronous request handling)
*   **Database:** MongoDB v6.0 (NoSQL for flexible legal document schemas)
*   **Task Queue:** Celery 5.3 with Redis 7.0 as the broker
*   **Containerization:** Docker Compose for local development; Kubernetes (K8s) for production.
*   **CI/CD:** GitLab CI with rolling deployment strategies to ensure zero-downtime updates.
*   **Compliance:** Data residency is strictly enforced within EU-West-1 (Dublin) and EU-Central-1 (Frankfurt) to satisfy GDPR requirements.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Blocked
*   **Description:** 
    Given that legal professionals often work in high-security environments (courtrooms, archives) with intermittent connectivity, Halcyon must support full offline functionality. This feature allows users to perform data entry, modify case notes, and queue analytics requests while offline.

*   **Technical Implementation:**
    The frontend will utilize IndexedDB for local storage of state. A "Sync Manager" service will track a versioning timestamp for every local record. Upon reconnection, the system will perform a "Three-Way Merge": comparing the local state, the server state, and the last known synchronized state. 
    
    The background sync engine will utilize a Celery-based queue to process pending updates. To prevent race conditions, the system will implement **Optimistic Concurrency Control (OCC)** using a `version_id` field on every MongoDB document. If a collision occurs (the server version is higher than the local base version), the record is flagged for "Manual Resolution" in the UI.

*   **Constraint:** Currently blocked due to the lack of a finalized conflict resolution protocol agreed upon by the partner company.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Medium
*   **Status:** In Progress
*   **Description:** 
    The dashboard serves as the primary analytics interface. Users must be able to customize their view by adding, removing, and rearranging widgets (e.g., "Case Throughput," "Billable Hours Forecast," "Partner API Health").

*   **Technical Implementation:**
    The layout will be persisted in MongoDB as a JSON configuration object associated with the User Profile. We will use `react-grid-layout` for the frontend implementation. Each widget is a standalone component that consumes a specific FastAPI endpoint. 
    
    The "Widget Registry" defines the available data sources and visualization types (Bar Chart, Heatmap, KPI Card). When a user drags a widget, the `PUT /api/v1/user/dashboard-layout` endpoint is triggered to save the coordinates and dimensions of the widget.

*   **UX Goal:** Minimum latency of <200ms for widget movement; asynchronous loading of widget data to prevent the entire dashboard from hanging if one API call is slow.

### 3.3 API Rate Limiting and Usage Analytics
*   **Priority:** Medium
*   **Status:** In Design
*   **Description:** 
    To protect the system from overload and to monitor the usage of the external partner's API (which has strict quotas), Halcyon requires a robust rate-limiting layer.

*   **Technical Implementation:**
    We will implement a **Token Bucket Algorithm** using Redis. Each API key is assigned a bucket with a maximum capacity and a refill rate.
    - `RateLimitMiddleware`: A FastAPI middleware that intercepts every request.
    - `Redis Store`: Stores the current token count for each `client_id`.
    
    Usage analytics will be captured asynchronously. For every request, a Celery task will be dispatched to log the metadata (endpoint, timestamp, response size, latency) into a MongoDB collection named `api_usage_logs`. This allows the Project Lead to generate monthly reports on which features are most utilized.

### 3.4 File Upload with Virus Scanning and CDN Distribution
*   **Priority:** High
*   **Status:** Blocked
*   **Description:** 
    Legal cases involve the upload of thousands of PDFs, DOCXs, and images. These must be scanned for malware before being stored and then distributed via a CDN to ensure fast access for global teams.

*   **Technical Implementation:**
    The pipeline will follow this flow:
    1.  **Upload:** Client sends file to `/api/v1/files/upload`.
    2.  **Quarantine:** The file is temporarily stored in a "Quarantine" S3 bucket.
    3.  **Scanning:** A Celery worker triggers a `ClamAV` scan via a dedicated security container.
    4.  **Promotion:** If the scan is clean, the file is moved to the "Production" bucket.
    5.  **Distribution:** The file is served via an Amazon CloudFront distribution with signed URLs for security.

*   **Constraint:** Currently blocked pending budget approval for the enterprise-grade virus scanning license and the CDN infrastructure setup.

### 3.5 SSO Integration with SAML and OIDC Providers
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Progress
*   **Description:** 
    Enterprise legal firms require Single Sign-On (SSO) for security and compliance. Halcyon must support both SAML 2.0 (for legacy Active Directory environments) and OIDC (for modern cloud identities).

*   **Technical Implementation:**
    We will integrate `python3-saml` and `authlib` for OIDC. The system will act as a Service Provider (SP). 
    - **SAML Flow:** Redirect to IdP $\rightarrow$ SAML Assertion $\rightarrow$ Validation $\rightarrow$ JWT Issuance.
    - **OIDC Flow:** Authorization Code Grant $\rightarrow$ Token Exchange $\rightarrow$ JWT Issuance.
    
    The user's `organization_id` will be mapped from the SAML attribute `urn:oid:1.2.3.4` to ensure that users are automatically assigned to their respective company silo upon first login.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the `/api/v1/` prefix. Authentication is handled via Bearer JWT.

### 4.1 `POST /api/v1/sync/trigger`
Manually triggers a synchronization event with the external partner API.
- **Request:** `{ "sync_type": "full" | "incremental", "entity": "cases" }`
- **Response:** `202 Accepted` $\rightarrow$ `{ "job_id": "celery-uuid-123", "status": "queued" }`

### 4.2 `GET /api/v1/analytics/cases/summary`
Returns aggregated metrics for legal cases.
- **Request:** Query params `?start_date=2023-01-01&end_date=2023-12-31`
- **Response:** `200 OK` $\rightarrow$ `{ "total_cases": 1200, "avg_resolution_days": 45, "win_rate": 0.68 }`

### 4.3 `GET /api/v1/files/download/{file_id}`
Generates a signed CDN URL for file retrieval.
- **Request:** Path parameter `file_id`
- **Response:** `200 OK` $\rightarrow$ `{ "download_url": "https://cdn.halcyon.com/signed-link...", "expires_in": 3600 }`

### 4.4 `PUT /api/v1/user/dashboard-layout`
Updates the user's customized dashboard widget positions.
- **Request:** `{ "widgets": [ { "id": "widget_1", "x": 0, "y": 0, "w": 4, "h": 2 }, ... ] }`
- **Response:** `200 OK` $\rightarrow$ `{ "status": "updated" }`

### 4.5 `GET /api/v1/system/health`
Health check endpoint for K8s liveness/readiness probes.
- **Response:** `200 OK` $\rightarrow$ `{ "status": "healthy", "db": "connected", "redis": "connected" }`

### 4.6 `POST /api/v1/auth/saml/acs`
Assertion Consumer Service endpoint for SAML responses.
- **Request:** SAML Response XML (POST body)
- **Response:** `302 Redirect` $\rightarrow$ Redirects to `/dashboard` with session cookie.

### 4.7 `GET /api/v1/analytics/usage/limits`
Retrieves the current rate limit status for the API key.
- **Response:** `200 OK` $\rightarrow$ `{ "limit": 1000, "remaining": 450, "reset_at": "2023-10-25T00:00:00Z" }`

### 4.8 `DELETE /api/v1/cases/{case_id}`
Hard-deletes a case record (subject to GDPR "Right to be Forgotten").
- **Request:** Path parameter `case_id`
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA (MONGODB)

Since Halcyon uses MongoDB, the "tables" are collections. We employ a flexible schema with strict validation rules for core fields.

### 5.1 Collection: `users`
- `_id`: ObjectId (PK)
- `email`: String (Unique, Indexed)
- `password_hash`: String
- `role`: String (Admin, User, Auditor)
- `org_id`: ObjectId (FK $\rightarrow$ `organizations`)
- `sso_provider`: String (SAML, OIDC, Local)
- `last_login`: Date
- `dashboard_config`: Object (JSON layout)

### 5.2 Collection: `organizations`
- `_id`: ObjectId (PK)
- `name`: String
- `legal_entity_id`: String (External ID)
- `region`: String (e.g., "EU-West-1")
- `subscription_tier`: String (Basic, Premium)
- `api_quota`: Integer

### 5.3 Collection: `legal_cases`
- `_id`: ObjectId (PK)
- `case_number`: String (Unique, Indexed)
- `client_name`: String
- `status`: String (Open, Closed, Pending)
- `assigned_attorney`: ObjectId (FK $\rightarrow$ `users`)
- `external_ref_id`: String (ID from partner API)
- `valuation`: Decimal
- `created_at`: Date
- `updated_at`: Date

### 5.4 Collection: `case_documents`
- `_id`: ObjectId (PK)
- `case_id`: ObjectId (FK $\rightarrow$ `legal_cases`)
- `file_path`: String (S3 Key)
- `file_hash`: String (SHA-256)
- `virus_scan_status`: String (Pending, Clean, Infected)
- `mime_type`: String
- `uploaded_by`: ObjectId (FK $\rightarrow$ `users`)

### 5.5 Collection: `sync_logs`
- `_id`: ObjectId (PK)
- `job_id`: String (Celery UUID)
- `start_time`: Date
- `end_time`: Date
- `records_processed`: Integer
- `errors`: Array (Objects containing error message and record ID)
- `status`: String (Success, Partial, Failed)

### 5.6 Collection: `api_usage_logs`
- `_id`: ObjectId (PK)
- `user_id`: ObjectId (FK $\rightarrow$ `users`)
- `endpoint`: String
- `http_method`: String
- `response_time_ms`: Integer
- `timestamp`: Date

### 5.7 Collection: `audit_trail`
- `_id`: ObjectId (PK)
- `actor_id`: ObjectId (FK $\rightarrow$ `users`)
- `action`: String (e.g., "UPDATE_CASE_VALUATION")
- `entity_id`: ObjectId
- `old_value`: Object
- `new_value`: Object
- `timestamp`: Date

### 5.8 Collection: `rate_limits`
- `_id`: ObjectId (PK)
- `client_id`: String (Unique)
- `tokens`: Integer
- `last_refill`: Date

### 5.9 Collection: `sso_configurations`
- `_id`: ObjectId (PK)
- `org_id`: ObjectId (FK $\rightarrow$ `organizations`)
- `idp_metadata_url`: String
- `entity_id`: String
- `public_cert`: String

### 5.10 Collection: `analytics_snapshots`
- `_id`: ObjectId (PK)
- `snapshot_date`: Date
- `org_id`: ObjectId (FK $\rightarrow$ `organizations`)
- `metric_key`: String
- `metric_value`: Decimal

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Halcyon utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Host:** Local Docker Compose / Shared Dev K8s cluster.
- **Database:** Local MongoDB instance.
- **Purpose:** Rapid feature iteration.
- **Deploy Trigger:** Push to `develop` branch.

#### 6.1.2 Staging (Staging)
- **Host:** K8s Cluster (Mirror of Production).
- **Database:** Staging MongoDB (Sanitized copy of production data).
- **Purpose:** UAT (User Acceptance Testing) and Security Audits.
- **Deploy Trigger:** Merge to `release` branch.

#### 6.1.3 Production (Prod)
- **Host:** Managed K8s (EKS/GKE) with EU-region pinning.
- **Database:** MongoDB Atlas (Cluster with High Availability).
- **Purpose:** End-user access.
- **Deploy Trigger:** Tagged release via GitLab CI.

### 6.2 CI/CD Pipeline (GitLab CI)
1.  **Lint/Test:** Run `flake8` and `pytest`.
2.  **Build:** Create Docker image $\rightarrow$ Push to GitLab Container Registry.
3.  **Staging Deploy:** Update K8s manifests in Staging.
4.  **Security Scan:** Run `Snyk` for dependency vulnerabilities.
5.  **Prod Deploy:** Rolling update (maxSurge: 25%, maxUnavailable: 25%) to prevent downtime.

### 6.3 Data Residency
To comply with GDPR, all data is stored in the `eu-central-1` region. Cross-region replication is disabled. Backups are encrypted with AES-256 and stored in an immutable S3 bucket within the EU.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Individual business logic functions in the Domain Core.
- **Mocking:** Use `unittest.mock` for all Port interfaces.
- **Coverage Target:** 80% minimum.

### 7.2 Integration Testing
- **Framework:** `pytest` + `testcontainers`
- **Scope:** Testing the interaction between the FastAPI controllers and the MongoDB adapter.
- **Execution:** Spin up a temporary MongoDB container, run a set of seed data, execute the API call, and verify the database state.

### 7.3 End-to-End (E2E) Testing
- **Framework:** `Playwright`
- **Scope:** Critical user journeys (e.g., Login $\rightarrow$ Upload File $\rightarrow$ View Dashboard).
- **Execution:** Run against the Staging environment.

### 7.4 Security Testing
- **Static Analysis:** `Bandit` for Python security linting.
- **Dynamic Analysis:** OWASP ZAP scans on Staging endpoints.
- **Manual Audit:** Scheduled for Milestone 2 (July 2026).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Budget cut by 30% in next fiscal quarter | High | High | Escalate to steering committee; prioritize "Critical" features over "Medium". |
| **R2** | Scope creep from stakeholders | High | Medium | Engage external consultant for independent assessment of feature value. |
| **R3** | Partner API downtime/instability | Medium | High | Implement robust retry logic in Celery; cache data in MongoDB. |
| **R4** | GDPR Compliance failure | Low | Critical | Quarterly internal audits; data residency pinning. |
| **R5** | Technical Debt: Logging | High | Medium | Implement structured logging (JSON) using `structlog` in Q1 2026. |

**Probability/Impact Matrix:**
- High/High $\rightarrow$ Immediate Action Required
- High/Medium $\rightarrow$ Active Monitoring
- Low/Critical $\rightarrow$ Preventative Controls

---

## 9. TIMELINE

### Phase 1: Foundation (Now – 2026-02-01)
- Setup K8s infrastructure and GitLab CI.
- Implementation of Domain Core and Basic API Ports.
- Initial SSO integration (OIDC).
- **Dependencies:** Budget approval for core tools.

### Phase 2: Core Feature Build (2026-02-01 – 2026-05-15)
- Complete Offline-First logic.
- Finalize Dashboard widget system.
- Implement Rate Limiting.
- **Milestone 1: MVP Feature-Complete (2026-05-15).**

### Phase 3: Security & Hardening (2026-05-16 – 2026-07-15)
- Finalize Virus Scanning and CDN pipeline.
- Full SAML integration.
- External Security Audit.
- **Milestone 2: Security Audit Passed (2026-07-15).**

### Phase 4: Deployment & Optimization (2026-07-16 – 2026-09-15)
- Beta testing with selected legal firms.
- Performance tuning of MongoDB queries.
- Final production rollout.
- **Milestone 3: Production Launch (2026-09-15).**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-05)
- Quinn: Hexagonal is the way to go. No debating.
- Brigid: Worried about MongoDB overhead for simple relations.
- Kaia: EU residency is non-negotiable. Use Frankfurt.
- Maeve: Need the external API docs before I can start the adapter.
- Decision: Use Python/FastAPI.

### Meeting 2: Feature Prioritization (2023-12-12)
- Quinn: Offline-first is blocking launch.
- Brigid: Still waiting on the partner for the conflict resolution spec.
- Kaia: SAML is taking longer than expected. Need to pivot to OIDC first.
- Maeve: Dashboard widgets are mostly done.
- Decision: Mark Offline-First as "Blocked".

### Meeting 3: Budget Crisis (2024-01-20)
- Quinn: Rumors of 30% cut.
- Brigid: We can't cut the virus scanner; it's a security risk.
- Kaia: Agreed. If we cut, we cut the "Medium" priority widgets.
- Quinn: I'll talk to the steering committee.
- Decision: Maintain budget for "Critical" features; freeze "Medium" features if cuts occur.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | 4 FTEs (including contractor Maeve) |
| **Infrastructure** | 15% | $60,000 | K8s, MongoDB Atlas, S3, CloudFront |
| **Tools/Licenses** | 10% | $40,000 | Virus Scanner Enterprise, Security Audit |
| **Contingency** | 10% | $40,000 | Reserved for scope creep or emergency fixes |

---

## 12. APPENDICES

### Appendix A: Structured Logging Specification
Current technical debt involves reading `stdout`. The transition to structured logging will follow this JSON format:
```json
{
  "timestamp": "2026-05-15T10:00:00Z",
  "level": "ERROR",
  "logger": "sync_engine",
  "message": "External API Timeout",
  "context": {
    "job_id": "celery-123",
    "endpoint": "/v1/partner/cases",
    "retry_count": 3
  },
  "trace_id": "abc-123-xyz"
}
```

### Appendix B: Conflict Resolution Logic (Offline Sync)
When the Sync Manager detects a conflict:
1.  **Comparison:** Compare `updated_at` timestamps of Local vs Server.
2.  **Automatic Resolution:** If the change is to different fields (e.g., Local changed `notes`, Server changed `valuation`), merge both.
3.  **Manual Resolution:** If the same field was changed, the record is moved to `conflict_queue` and the user is prompted via the UI to select the "Winning" version.