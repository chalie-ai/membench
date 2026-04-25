# PROJECT SPECIFICATION DOCUMENT: PROJECT IRONCLAD
**Version:** 1.0.4  
**Status:** Baseline / Active  
**Date:** October 24, 2023  
**Company:** Talus Innovations  
**Project Lead:** Darian Park (Tech Lead)  
**Classification:** Confidential – Board Level Reporting

---

## 1. EXECUTIVE SUMMARY

**Business Justification**
Project "Ironclad" represents a strategic pivot for Talus Innovations. The current iteration of our logistics and shipping marketplace has suffered from catastrophic user feedback, characterized by systemic instability, poor UI/UX, and a failure to meet the rigorous compliance standards required by our high-value government contracts. Market analysis indicates that while the core business logic of Talus Innovations is sound, the delivery mechanism—the customer-facing platform—is the primary bottleneck to revenue growth. 

The "Ironclad" rebuild is not merely a feature update but a comprehensive architectural overhaul. By moving from a legacy monolith to a Go-based microservices architecture leveraging gRPC and CockroachDB, Talus Innovations intends to eliminate the performance bottlenecks and data consistency issues that plagued the previous version. The primary objective is to regain market trust and secure a dominant position in the logistics and shipping sector by providing a platform that is not only performant but legally compliant with FedRAMP standards.

**ROI Projection**
With a budget exceeding $5M, Ironclad is the flagship initiative for the current fiscal cycle. The projected Return on Investment (ROI) is based on three primary levers:
1. **Customer Retention:** A projected 40% increase in retention rates by eliminating the "catastrophic" UX failures of the previous version.
2. **Government Market Expansion:** Achieving FedRAMP authorization unlocks a projected $12M in untapped government contract opportunities over the next 24 months.
3. **Operational Efficiency:** Reducing infrastructure overhead and incident response time through Kubernetes orchestration and automated scaling on GCP, aiming for a 25% reduction in OpEx related to system downtime.

The long-term goal is to transform the marketplace into the industry standard for secure, international logistics, where "Ironclad" refers not just to the project name, but to the perceived security and reliability of the shipping transactions processed through the platform.

---

## 2. TECHNICAL ARCHITECTURE

Ironclad utilizes a **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies (databases, APIs, UI). This ensures that the system remains testable and adaptable, allowing the team to swap out adapters (e.g., switching from a mock API to a live partner API) without altering the core domain.

**The Stack:**
- **Language:** Go (Golang) 1.21+ for all microservices.
- **Communication:** gRPC for internal service-to-service communication (Protocol Buffers for serialization) to ensure high throughput and low latency.
- **Database:** CockroachDB (Distributed SQL) to provide global scalability and strong consistency, critical for shipping manifests and financial transactions.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
- **Security:** Mutual TLS (mTLS) for inter-service communication and strict adherence to FedRAMP High impact level controls.

**Architectural ASCII Diagram Description:**
The system is structured as follows:
`[User Interface/Client] <--> [API Gateway (REST/gRPC-Web)] <--> [Domain Services (Hexagonal)] <--> [Adapters] <--> [External Systems]`

Detailed Flow:
```text
       +------------------+
       |   External User   | (Web/Mobile/Gov Portal)
       +--------+---------+
                | HTTPS/JSON
                v
       +--------+---------+
       |   API Gateway     | (Authentication, Rate Limiting, Routing)
       +--------+---------+
                | gRPC
                v
       +-----------------------------------------------------------+
       |                   MICROSERVICES LAYER                     |
       |  +------------------+      +---------------------------+  |
       |  |  Order Service   | <--> |  Payment/Billing Service  |  |
       |  +--------+---------+      +-------------+-------------+  |
       |           |                              |                |
       |  +--------+---------+      +-------------+-------------+  |
       |  |  Shipping Service| <--> |  Identity/Auth Service    |  |
       |  +--------+---------+      +---------------------------+  |
       +-----------+-----------------------------------------------+
                   | (Adapters)
                   v
       +-----------------------------------------------------------+
       |                   DATA & INFRA LAYER                      |
       |  +-------------------+      +---------------------------+ |
       |  |   CockroachDB     |      |   Google Cloud Storage    | |
       |  | (Global Cluster)  |      |   (Encrypted Buckets)     | |
       |  +-------------------+      +---------------------------+ |
       +-----------------------------------------------------------+
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/i18n)
- **Priority:** Critical (Launch Blocker)
- **Status:** In Progress
- **Description:** To compete in the global logistics market, Ironclad must support 12 primary languages (English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Arabic, Hindi, Russian, and Italian).
- **Technical Implementation:** 
    - Use of `golang.org/x/text` for message translation and collation.
    - Implementation of a Translation Management System (TMS) where translators can update `.json` or `.po` files without requiring a code deploy.
    - Database schema must support UTF-8 encoding globally via CockroachDB to handle non-Latin characters.
    - Dynamic detection of user locale via the `Accept-Language` HTTP header and user profile settings.
- **Success Criteria:** 100% of user-facing strings must be externalized. No hard-coded strings in the frontend or backend.
- **Integration:** Integration with a CDN to cache localized static assets closer to the user's geographic region.

### 3.2 API Rate Limiting and Usage Analytics
- **Priority:** High
- **Status:** In Review
- **Description:** To prevent system abuse and monetize API access for corporate partners, a robust rate-limiting mechanism is required.
- **Technical Implementation:**
    - Implementation of a Token Bucket algorithm via Redis to track requests per API key.
    - Tiered rate limits: `Basic` (100 req/min), `Professional` (1,000 req/min), `Enterprise` (10,000 req/min).
    - Middleware in the Go API Gateway that intercepts all requests, checks the `X-API-KEY` header, and returns a `429 Too Many Requests` response if limits are exceeded.
    - Analytics pipeline: Every request is logged to a Prometheus/Grafana stack to track usage patterns, latency, and error rates.
- **Analytics Requirements:** Dashboard showing top 10 users by volume, peak traffic hours, and most utilized endpoints.

### 3.3 File Upload with Virus Scanning and CDN Distribution
- **Priority:** High
- **Status:** In Review
- **Description:** Logistics requires the upload of customs forms, IDs, and manifests. These files must be scanned for malware and served via a high-performance CDN.
- **Technical Implementation:**
    - **Upload Flow:** Client $\rightarrow$ API Gateway $\rightarrow$ Upload Service $\rightarrow$ Temporary GCS Bucket.
    - **Scanning:** Integration with ClamAV or a similar FedRAMP-approved virus scanner. Files are held in a "quarantine" bucket until a `Clean` signal is received.
    - **Distribution:** Once scanned, files are moved to a public/private production bucket integrated with Google Cloud CDN.
    - **Security:** Implementation of Signed URLs (Short-lived) to ensure that only authorized users can download specific documents.
- **Performance Goal:** File upload to availability in CDN $< 5$ seconds for files up to 10MB.

### 3.4 Multi-tenant Data Isolation
- **Priority:** High
- **Status:** Not Started
- **Description:** Ironclad must support multiple corporate clients (tenants) on a shared infrastructure while ensuring that no tenant can ever access another tenant's data.
- **Technical Implementation:**
    - **Row-Level Security (RLS):** Every table in CockroachDB will include a `tenant_id` column.
    - **Application Layer:** Every gRPC request must carry a `tenant_id` in the metadata context. The data access layer (DAL) will automatically append `WHERE tenant_id = ?` to all queries.
    - **Isolation Level:** "Silo" approach for high-security government clients (dedicated database clusters) and "Pool" approach for standard clients (shared cluster, logically separated).
- **Compliance:** This is a prerequisite for FedRAMP authorization, as data leakage between tenants is a critical failure.

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
- **Priority:** Low (Nice to Have)
- **Status:** In Progress
- **Description:** A user-configurable home screen allowing logistics managers to prioritize the information they see (e.g., "Active Shipments," "Revenue Trend," "Alerts").
- **Technical Implementation:**
    - Frontend implementation using React-Grid-Layout for the drag-and-drop interface.
    - Backend persistence of the layout configuration as a JSON blob in the `user_preferences` table.
    - Widget-specific API endpoints that provide data in a standardized format for the dashboard components.
- **UI/UX:** Widgets must be responsive and support different sizes (1x1, 2x1, 2x2).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are served via the API Gateway. Internal communication uses gRPC, but external clients interact via REST/JSON.

### 4.1 Authentication
- **Endpoint:** `POST /v1/auth/login`
- **Request:** `{"email": "user@talus.com", "password": "hashed_password"}`
- **Response:** `{"token": "jwt_token_here", "expires_at": "2023-12-01T00:00:00Z"}`
- **Description:** Validates credentials and returns a JWT.

### 4.2 Shipment Creation
- **Endpoint:** `POST /v1/shipments`
- **Request:** `{"origin": "US-NYC", "destination": "UK-LON", "weight": 50.5, "tenant_id": "T123"}`
- **Response:** `{"shipment_id": "SHIP-998877", "status": "pending", "tracking_url": "/track/SHIP-998877"}`
- **Description:** Initiates a new shipping order.

### 4.3 Shipment Tracking
- **Endpoint:** `GET /v1/shipments/{id}`
- **Request:** Path parameter `{id}`
- **Response:** `{"id": "SHIP-998877", "current_location": "Atlantic Ocean", "eta": "2026-07-10"}`
- **Description:** Retrieves real-time tracking data.

### 4.4 Document Upload
- **Endpoint:** `POST /v1/documents/upload`
- **Request:** Multipart Form Data (`file`, `shipment_id`)
- **Response:** `{"doc_id": "DOC-1122", "status": "scanning"}`
- **Description:** Uploads a logistics document for virus scanning.

### 4.5 Tenant Management
- **Endpoint:** `GET /v1/tenant/config`
- **Request:** Header `X-API-KEY`
- **Response:** `{"tenant_name": "GlobalLogistics Corp", "tier": "Enterprise", "quota": "10000"}`
- **Description:** Fetches tenant-specific configuration and limits.

### 4.6 Language Preference
- **Endpoint:** `PATCH /v1/user/preferences/locale`
- **Request:** `{"locale": "fr-FR"}`
- **Response:** `{"status": "updated", "current_locale": "fr-FR"}`
- **Description:** Updates the user's preferred language.

### 4.7 Rate Limit Status
- **Endpoint:** `GET /v1/account/limits`
- **Request:** Header `X-API-KEY`
- **Response:** `{"remaining_requests": 450, "reset_time": "2023-10-24T14:00:00Z"}`
- **Description:** Allows clients to programmatically check their remaining quota.

### 4.8 Widget Layout Save
- **Endpoint:** `POST /v1/user/dashboard/layout`
- **Request:** `{"layout_json": "[{ 'i': 'A', 'x': 0, 'y': 0, 'w': 2, 'h': 2 }]"}`
- **Response:** `{"status": "success"}`
- **Description:** Persists the drag-and-drop dashboard configuration.

---

## 5. DATABASE SCHEMA

**Database:** CockroachDB (Distributed SQL)
**Naming Convention:** snake_case

### 5.1 Table: `tenants`
- `tenant_id` (UUID, PK)
- `tenant_name` (VARCHAR)
- `tier` (ENUM: 'basic', 'pro', 'enterprise')
- `created_at` (TIMESTAMP)
- `is_active` (BOOLEAN)

### 5.2 Table: `users`
- `user_id` (UUID, PK)
- `tenant_id` (UUID, FK $\rightarrow$ tenants.tenant_id)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `mfa_secret` (VARCHAR)
- `last_login` (TIMESTAMP)

### 5.3 Table: `user_preferences`
- `pref_id` (UUID, PK)
- `user_id` (UUID, FK $\rightarrow$ users.user_id)
- `locale` (VARCHAR, e.g., 'en-US')
- `dashboard_layout` (JSONB)
- `timezone` (VARCHAR)

### 5.4 Table: `shipments`
- `shipment_id` (UUID, PK)
- `tenant_id` (UUID, FK $\rightarrow$ tenants.tenant_id)
- `origin_address` (TEXT)
- `destination_address` (TEXT)
- `status` (VARCHAR)
- `weight` (DECIMAL)
- `created_at` (TIMESTAMP)

### 5.5 Table: `shipment_events`
- `event_id` (UUID, PK)
- `shipment_id` (UUID, FK $\rightarrow$ shipments.shipment_id)
- `event_type` (VARCHAR)
- `location` (VARCHAR)
- `timestamp` (TIMESTAMP)

### 5.6 Table: `documents`
- `doc_id` (UUID, PK)
- `shipment_id` (UUID, FK $\rightarrow$ shipments.shipment_id)
- `tenant_id` (UUID, FK $\rightarrow$ tenants.tenant_id)
- `gcs_path` (VARCHAR)
- `virus_scan_status` (ENUM: 'pending', 'clean', 'infected')
- `mime_type` (VARCHAR)

### 5.7 Table: `api_keys`
- `key_id` (UUID, PK)
- `tenant_id` (UUID, FK $\rightarrow$ tenants.tenant_id)
- `api_key_hash` (VARCHAR, UNIQUE)
- `rate_limit_tier` (VARCHAR)
- `expires_at` (TIMESTAMP)

### 5.8 Table: `api_usage_logs`
- `log_id` (BIGINT, PK)
- `key_id` (UUID, FK $\rightarrow$ api_keys.key_id)
- `endpoint` (VARCHAR)
- `response_code` (INT)
- `request_timestamp` (TIMESTAMP)

### 5.9 Table: `billing_accounts`
- `account_id` (UUID, PK)
- `tenant_id` (UUID, FK $\rightarrow$ tenants.tenant_id)
- `credit_card_token` (VARCHAR)
- `billing_email` (VARCHAR)
- `currency` (VARCHAR)

### 5.10 Table: `invoices`
- `invoice_id` (UUID, PK)
- `account_id` (UUID, FK $\rightarrow$ billing_accounts.account_id)
- `amount` (DECIMAL)
- `status` (ENUM: 'paid', 'unpaid', 'overdue')
- `due_date` (DATE)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
The project maintains three distinct environments to ensure stability and compliance.

**Development (Dev):**
- **Purpose:** Rapid iteration and feature testing.
- **Configuration:** Lower resource limits, mocked external APIs.
- **Deployment:** Automatic deployment on merge to `develop` branch.
- **Database:** Shared CockroachDB cluster with separate logical databases per developer.

**Staging (Staging):**
- **Purpose:** Pre-production validation, UAT, and FedRAMP audit simulations.
- **Configuration:** Mirrored production specs (1:1). Real external API integrations.
- **Deployment:** Triggered by release candidates.
- **Database:** Standalone CockroachDB cluster.

**Production (Prod):**
- **Purpose:** Live customer traffic.
- **Configuration:** High-availability, multi-region GCP deployment.
- **Deployment:** **Manual deployment performed by Yves Park (DevOps Engineer).**
- **Database:** Multi-region CockroachDB cluster with strict backup/recovery policies.

### 6.2 Infrastructure Details
- **Cluster:** GKE (Google Kubernetes Engine) with Autoscaling enabled.
- **CI/CD:** GitHub Actions for build and test; manual approval for production rollout.
- **Observability:** 
    - **Logging:** Google Cloud Logging (Stackdriver).
    - **Metrics:** Prometheus for time-series data, Grafana for visualization.
    - **Tracing:** Jaeger for gRPC request tracing across microservices.

### 6.3 The "Bus Factor" Risk
It is explicitly noted that the deployment process is currently manual and managed solely by Yves Park. This creates a **Bus Factor of 1**. To mitigate this, the team is working toward "Infrastructure as Code" (Terraform) and automated CD pipelines, although the current mandate requires a human-in-the-loop for Production for security reasons.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every Go microservice must maintain $>80\%$ test coverage.
- **Tools:** `testing` package, `testify` for assertions, `mockery` for generating mocks of ports.
- **Focus:** Testing business logic in the "Core" layer of the hexagonal architecture, isolated from the database and network.

### 7.2 Integration Testing
- **Approach:** Testing the "Adapters" and their interaction with real dependencies.
- **Tools:** `testcontainers-go` to spin up ephemeral CockroachDB and Redis instances.
- **Focus:** Verifying SQL queries, gRPC contract adherence, and external API response handling.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Black-box testing of the entire system from the API Gateway.
- **Tools:** Playwright for frontend flows, Postman/Newman for API suites.
- **Focus:** Critical user journeys: "Login $\rightarrow$ Create Shipment $\rightarrow$ Upload Document $\rightarrow$ Track Shipment."

### 7.4 Security Testing
- **Penetration Testing:** Quarterly external audits required for FedRAMP.
- **Static Analysis:** `gosec` integrated into the CI pipeline to detect common security vulnerabilities.
- **Dynamic Analysis:** OWASP ZAP runs against the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% next fiscal quarter | Medium | High | Develop a "Lean" fallback architecture; prioritize critical features over "nice-to-haves" (e.g., drop Dashboard). |
| R-02 | Partner API undocumented/buggy | High | Medium | Create a wrapper/adapter layer to sanitize partner data; de-scope affected features if unresolved by Milestone 1. |
| R-03 | Bus Factor of 1 (Yves Park) | Medium | Critical | Documentation of all manual deployment steps; cross-train Darian Park on GKE basics. |
| R-04 | FedRAMP Audit Failure | Low | Critical | Continuous compliance monitoring; engage a 3rd party FedRAMP consultant for pre-audits. |
| R-05 | Third-party API Rate Limits | High | Medium | Implement local caching and request queuing to avoid hitting limits during testing. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or failure to launch.
- **High:** Significant delay or major feature loss.
- **Medium:** Manageable delay; requires workaround.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE

### 9.1 Phase 1: Foundation & Core Services (Oct 2023 - May 2026)
- **Focus:** Setting up GKE, CockroachDB, and basic gRPC service definitions.
- **Dependencies:** Infrastructure must be live before any service deployment.
- **Key Deliverable:** Multi-tenant data isolation architecture.

### 9.2 Phase 2: Feature Implementation (June 2026 - July 2026)
- **Focus:** L10n/i18n, File Uploads, and Rate Limiting.
- **Dependencies:** L10n is a launch blocker and must be completed first.
- **Key Deliverable:** Internal Alpha.

### 9.3 Phase 3: Stability & Compliance (August 2026 - October 2026)
- **Focus:** Performance tuning and FedRAMP audit.
- **Dependencies:** All features must be frozen.
- **Key Deliverable:** Performance benchmarks and Audit certification.

### 9.4 Milestones
- **Milestone 1: Internal Alpha Release** $\rightarrow$ **Target: 2026-06-15**
- **Milestone 2: Post-launch Stability Confirmed** $\rightarrow$ **Target: 2026-08-15**
- **Milestone 3: Performance Benchmarks Met** $\rightarrow$ **Target: 2026-10-15**

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per the team's preference, formal meeting minutes are not kept. The following is a synthesis of key decisions made in the `#ironclad-dev` Slack channel.

### Thread: "The Partner API Nightmare" (Nov 12, 2023)
- **Darian Park:** "The shipping partner's API is returning 500s on basic GET requests and the docs are 3 years out of date. We can't rely on their 'Estimated Delivery' field."
- **Joelle Costa:** "If we can't trust the data, we can't put it in the UI. It'll just lead to more catastrophic feedback."
- **Decision:** Darian decided to implement a "Fallback Estimate" logic. If the partner API fails or returns null, the system will calculate an estimate based on historical averages. If the API remains unstable by Milestone 1, the feature will be de-scoped.

### Thread: "FedRAMP vs. Speed" (Jan 20, 2024)
- **Yves Park:** "Adding mTLS and encrypted buckets to every service is slowing down the local dev loop."
- **Yara Costa (Intern):** "Can we use a simpler auth for Dev?"
- **Joelle Costa:** "No. We need to ensure that the security posture is consistent across environments to avoid 'it works in dev' bugs during the audit."
- **Decision:** The team agreed to keep strict security in Dev but invested in optimizing the local Kubernetes (minikube/kind) startup scripts to reduce friction.

### Thread: "Budget Anxiety" (March 5, 2024)
- **Darian Park:** "Heard from the board that there's a possibility of a 30% budget cut next quarter. We need to be careful."
- **Yves Park:** "Does that mean we cut the GCP multi-region setup?"
- **Darian Park:** "Potentially. Let's design the system so we can run on a single region if needed, and only scale to multi-region once the budget is locked."
- **Decision:** Architecture will be "multi-region ready" but deployed as "single-region" in the short term to save costs.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | 8 FTEs over 3 years (including benefits/bonuses). |
| **Infrastructure (GCP)** | $800,000 | Includes GKE, CockroachDB Cloud, and Cloud Storage. |
| **Security & Compliance** | $400,000 | FedRAMP auditors, penetration testing, and certification fees. |
| **Tools & Licenses** | $100,000 | IDEs, GitHub Enterprise, Monitoring tools (Datadog/Grafana). |
| **Contingency Fund** | $500,000 | Reserved for the 30% budget risk and unforeseen API costs. |

**Financial Note:** Personnel costs are the largest driver. The team size is lean (8 people), but the seniority required for Go/gRPC and FedRAMP compliance necessitates higher-than-average salaries.

---

## 12. APPENDICES

### Appendix A: gRPC Service Definition (Protobuf Example)
To ensure consistency, all services must define their interfaces in `.proto` files.

```protobuf
syntax = "proto3";

package ironclad.shipping;

service ShippingService {
  rpc CreateShipment (CreateShipmentRequest) returns (ShipmentResponse);
  rpc GetShipmentStatus (ShipmentIdRequest) returns (ShipmentStatusResponse);
}

message CreateShipmentRequest {
  string origin = 1;
  string destination = 2;
  double weight = 3;
  string tenant_id = 4;
}

message ShipmentResponse {
  string shipment_id = 1;
  string status = 2;
  string tracking_url = 3;
}

message ShipmentIdRequest {
  string shipment_id = 1;
}

message ShipmentStatusResponse {
  string shipment_id = 1;
  string current_location = 2;
  string eta = 3;
}
```

### Appendix B: FedRAMP Compliance Checklist (High Level)
The following controls must be verified by Joelle Costa before the external audit:
1. **Access Control (AC):** Implement MFA for all administrative access to GCP and Kubernetes.
2. **Audit and Accountability (AU):** Centralized logging of all "privileged" actions; logs must be immutable.
3. **Configuration Management (CM):** Baseline configurations for all GKE nodes must be documented and enforced via policy.
4. **Identification and Authentication (IA):** All internal service-to-service traffic must use mTLS with rotating certificates.
5. **System and Communications Protection (SC):** Encryption of data at rest (AES-256) and data in transit (TLS 1.3).