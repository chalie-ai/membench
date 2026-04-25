# PROJECT SPECIFICATION: PROJECT OBELISK
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Last Updated:** 2024-10-25  
**Company:** Bridgewater Dynamics  
**Project Lead:** Bram Jensen (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Obelisk is a mission-critical modernization effort at Bridgewater Dynamics aimed at replacing a 15-year-old legacy machine learning system. The legacy system currently serves as the backbone for the company's renewable energy forecasting and grid optimization services. Because this system is the primary driver of revenue and operational stability, it is categorized as "Zero Downtime Tolerance." Any outage during the transition would result in immediate financial loss and potential regulatory penalties.

### 1.2 Business Justification
The current legacy system—built on monolithic architecture and deprecated libraries—has reached a state of critical fragility. Maintenance costs have ballooned as the pool of engineers capable of supporting the outdated codebase shrinks. More importantly, the legacy model cannot scale to handle the current volume of renewable energy data flowing from new solar and wind installations.

Obelisk will implement a modern, containerized ML deployment pipeline that allows for rapid iteration of models, improved inference latency, and robust multi-tenancy. By migrating to a three-tier architecture hosted on Kubernetes, Bridgewater Dynamics will shift from a rigid, fragile environment to a scalable, resilient infrastructure.

### 1.3 ROI Projection
The financial justification for Obelisk is rooted in three primary areas:
1. **Operational Cost Reduction:** Reduction in infrastructure "keep-the-lights-on" costs by 30% through the use of auto-scaling Kubernetes clusters, replacing expensive, over-provisioned bare-metal servers.
2. **Revenue Growth:** The ability to onboard larger enterprise clients via the new multi-tenant data isolation features. We project a 25% increase in Monthly Recurring Revenue (MRR) within the first year post-launch.
3. **Risk Mitigation:** Eliminating the "single point of failure" risk associated with the 15-year-old system. A single catastrophic failure of the legacy system is estimated to cost the company $50,000 per hour in lost productivity and SLA penalties.

### 1.4 Strategic Context
While the budget is constrained at $150,000 (a "shoestring" budget for a project of this magnitude), the ROI is projected to exceed the initial investment within 8 months of launch. The project is currently racing against a primary competitor who is approximately two months ahead in developing a similar ML deployment tool. Success is not merely about technical parity, but about operational stability and the ability to maintain 100% uptime during the migration.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Obelisk utilizes a traditional three-tier architecture designed to isolate the user interface, the business logic (ML inference and processing), and the data persistence layer. 

Due to the legacy requirements of Bridgewater Dynamics, the stack is "mixed," inheriting three different legacy stacks (Python 2.7, Java 8, and a proprietary C++ engine) that must interoperate through a series of RESTful APIs and message queues.

**ASCII ARCHITECTURE DIAGRAM DESCRIPTION:**
```text
[ USER LAYER ]  <--- HTTPS/TLS 1.3 ---> [ LOAD BALANCER (Nginx) ]
                                              |
                                              v
[ PRESENTATION LAYER ] <--- React 18.2 / TypeScript (Frontend)
                                              |
                                              v
[ BUSINESS LOGIC LAYER ] <--- API Gateway (Node.js/Express)
       |                                       |
       |------> [ ML Inference Service (FastAPI/Python 3.11) ] <--> [ Model Registry ]
       |                                       |
       |------> [ Legacy Wrapper (Java 8 / Spring) ] <--> [ Legacy C++ Engine ]
       |                                       |
       |------> [ Billing/Auth Service (Go) ] <--> [ Stripe API ]
                                              |
                                              v
[ DATA LAYER ] <--- PostgreSQL 15 (Primary) / Redis 7 (Caching) / S3 (Blob Storage)
```

### 2.2 Technology Stack Detail
*   **Frontend:** React 18.2 with Tailwind CSS for the presentation layer.
*   **Backend:** A polyglot microservices approach. Node.js for the API Gateway, FastAPI for the ML inference layer, and Go for the high-performance billing and authentication modules.
*   **Database:** PostgreSQL 15 for relational data; Redis 7 for caching inference results to meet the <200ms p95 latency goal.
*   **Infrastructure:** Kubernetes (EKS) managed clusters.
*   **CI/CD:** GitLab CI. Currently, the pipeline takes 45 minutes due to a lack of parallelization and unoptimized Docker layers. This is a known technical debt item.
*   **Compliance:** The entire architecture is designed to meet SOC 2 Type II compliance, requiring strict audit logs, encrypted data at rest (AES-256), and encrypted data in transit.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker)  
**Status:** Blocked (Waiting on Legal)

**Description:**
Obelisk requires a robust, automated billing system to transition from the legacy "manual invoice" model to a modern subscription-based SaaS model. This system must handle tiered pricing based on the volume of ML inferences performed by the client.

**Detailed Requirements:**
- **Subscription Tiers:** Support for 'Basic', 'Professional', and 'Enterprise' tiers.
- **Usage Tracking:** Integration with the ML inference service to track "tokens" or "requests" per tenant in real-time.
- **Automated Invoicing:** Generation of PDF invoices via a background worker (Celery/RabbitMQ) on the 1st of every month.
- **Payment Gateway:** Integration with Stripe API for credit card processing and automated dunning (retry logic) for failed payments.
- **Grace Periods:** A configurable 7-day grace period for failed payments before the system automatically restricts API access.

**Constraints:**
The feature is currently blocked by a legal review of the Data Processing Agreement (DPA). Legal must confirm that the flow of billing data to Stripe complies with the renewable energy regulations in the EU and North American markets.

**Acceptance Criteria:**
- User can upgrade/downgrade tier via the dashboard.
- System triggers an automatic "Payment Failed" email and restricts access after 7 days.
- Database records every single transaction with a unique `invoice_id` linked to the `tenant_id`.

---

### 3.2 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Critical (Launch Blocker)  
**Status:** In Review

**Description:**
Users must be able to search through millions of renewable energy data points and ML model logs. A standard SQL `LIKE` query is insufficient for the scale of data.

**Detailed Requirements:**
- **Full-Text Search (FTS):** Implementation of Elasticsearch or PostgreSQL GIN indexes to allow for fuzzy searching and partial matches across model metadata.
- **Faceted Filtering:** A sidebar allowing users to filter results by `Date Range`, `Region`, `Energy Source` (Wind, Solar, Hydro), and `Model Version`.
- **Indexing Strategy:** Asynchronous indexing of new model results using a "Write-Ahead Log" (WAL) approach to ensure the primary database is not slowed down by search index updates.
- **Highlighting:** The search results must highlight the specific keywords matched within the document snippet.

**Technical Implementation:**
The search service will implement a "Query Parser" that converts the frontend's JSON filter object into a complex Boolean query for the search engine.

**Acceptance Criteria:**
- Search results return in < 300ms for a dataset of 1 million records.
- Facets update dynamically as filters are selected.
- Full-text index is updated within 5 seconds of a new data entry.

---

### 3.3 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Low (Nice to Have)  
**Status:** In Progress

**Description:**
To optimize costs, Obelisk will use a "Shared Schema" approach rather than "Database-per-Tenant." However, strict logical isolation is required to prevent data leakage between competing energy firms.

**Detailed Requirements:**
- **Tenant ID Injection:** Every table in the database must include a `tenant_id` column.
- **Row-Level Security (RLS):** Implementation of PostgreSQL Row-Level Security policies to ensure that a database session can only see rows matching the current `tenant_id`.
- **Context Propagation:** The API Gateway must extract the `tenant_id` from the JWT (JSON Web Token) and propagate it through all internal service calls.
- **Shared Resource Management:** Implementation of rate-limiting per tenant to prevent a single "noisy neighbor" from consuming all ML inference resources.

**Implementation Note:**
Since this is a "Nice to Have," the team is focusing on the "Critical" blockers first, but the baseline schema is being built with `tenant_id` to avoid a massive migration later.

**Acceptance Criteria:**
- A query from Tenant A cannot return data from Tenant B, even if the `WHERE` clause is omitted in the application code (enforced at the DB level).
- Rate limiting kicks in at 1,000 requests per minute per tenant.

---

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium  
**Status:** In Design

**Description:**
Given the criticality of the energy grid data, standard password authentication is insufficient. Obelisk requires a high-assurance identity layer.

**Detailed Requirements:**
- **TOTP Support:** Implementation of Time-based One-Time Passwords (compatible with Google Authenticator/Authy).
- **WebAuthn/FIDO2:** Support for hardware keys (e.g., YubiKey) to prevent phishing attacks.
- **Recovery Codes:** Generation of ten 8-character one-time-use recovery codes upon 2FA enablement.
- **Enforcement Toggles:** Ability for administrators to "Force 2FA" for all users within a specific tenant.

**Design Considerations:**
Eshan Santos (Product Designer) is currently designing the "Enrollment Flow" to ensure users are not locked out during the transition from the legacy system.

**Acceptance Criteria:**
- User cannot access the dashboard without a valid 2FA token if enabled.
- YubiKey registration completes in under three steps.
- Recovery codes successfully grant access when the 2FA device is lost.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker)  
**Status:** In Progress

**Description:**
Users need to upload large datasets (CSV, JSON, Parquet) to train and validate ML models. These files must be scanned for malware before being stored.

**Detailed Requirements:**
- **Multipart Uploads:** Support for files up to 2GB using S3 multipart upload APIs.
- **Virus Scanning:** Integration with an asynchronous scanner (e.g., ClamAV) via a Lambda function. Files are marked `status: pending` until the scan returns `clean`.
- **CDN Integration:** Clean files are served via CloudFront to reduce latency for global users.
- **Content-Type Validation:** Strict validation of file headers (magic bytes) to ensure users aren't uploading executable files disguised as CSVs.

**Workflow:**
`Frontend` $\rightarrow$ `S3 (Quarantine Bucket)` $\rightarrow$ `Lambda (Virus Scan)` $\rightarrow$ `S3 (Clean Bucket)` $\rightarrow$ `CloudFront` $\rightarrow$ `End User`.

**Acceptance Criteria:**
- Files containing known signatures of viruses are automatically deleted and the user is notified.
- Large files (1GB+) upload without timing out.
- CDN cache is invalidated automatically when a file is overwritten.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path: `https://api.obelisk.bridgewater.io/v1`

### 4.1 `POST /auth/login`
- **Purpose:** Authenticates user and returns JWT.
- **Request:** `{ "email": "user@example.com", "password": "password123" }`
- **Response:** `{ "token": "eyJ...", "expires_in": 3600, "requires_2fa": true }`

### 4.2 `GET /models/inference`
- **Purpose:** Retrieves ML prediction for a specific energy grid segment.
- **Request:** `?segment_id=SEG-99&timestamp=2025-05-01T12:00Z`
- **Response:** `{ "prediction": 450.5, "confidence": 0.92, "unit": "MW", "latency_ms": 142 }`

### 4.3 `POST /billing/subscription`
- **Purpose:** Updates the current subscription plan.
- **Request:** `{ "plan_id": "plan_pro_monthly", "payment_method_id": "pm_123..." }`
- **Response:** `{ "status": "success", "next_billing_date": "2025-06-01" }`

### 4.4 `GET /search/assets`
- **Purpose:** Faceted search for renewable energy assets.
- **Request:** `?q=wind+farm&region=north_sea&type=turbine`
- **Response:** `{ "results": [...], "facets": { "regions": { "north_sea": 120, "baltic": 45 } }, "total": 165 }`

### 4.5 `POST /uploads/dataset`
- **Purpose:** Initiates a secure file upload.
- **Request:** `{ "filename": "grid_data_q1.csv", "size": 52428800 }`
- **Response:** `{ "upload_url": "https://s3.amazon.com/...", "upload_id": "up-8821" }`

### 4.6 `GET /tenant/config`
- **Purpose:** Fetches tenant-specific configuration and isolation settings.
- **Request:** Headers: `Authorization: Bearer <token>`
- **Response:** `{ "tenant_name": "EcoPower Ltd", "max_concurrency": 50, "region": "EU-West-1" }`

### 4.7 `POST /auth/2fa/verify`
- **Purpose:** Verifies the 2FA token.
- **Request:** `{ "token": "123456", "session_id": "sess_abc" }`
- **Response:** `{ "authenticated": true, "final_token": "eyJ..." }`

### 4.8 `DELETE /models/version/{version_id}`
- **Purpose:** Removes an outdated ML model version.
- **Request:** Path parameter `version_id`.
- **Response:** `{ "message": "Model version v2.1 deleted successfully" }`

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL 15. All tables use UUIDs for primary keys to facilitate future database sharding.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `tenants` | `id` (PK), `name`, `created_at` | 1:N with `users` | Primary entity for multi-tenancy. |
| `users` | `id` (PK), `tenant_id` (FK), `email`, `password_hash` | N:1 with `tenants` | User account credentials. |
| `user_2fa` | `user_id` (PK/FK), `secret`, `is_enabled` | 1:1 with `users` | 2FA settings and secrets. |
| `subscriptions`| `id` (PK), `tenant_id` (FK), `plan_id`, `status` | N:1 with `tenants` | Current billing status. |
| `invoices` | `id` (PK), `tenant_id` (FK), `amount`, `date` | N:1 with `tenants` | Historical billing records. |
| `ml_models` | `id` (PK), `tenant_id` (FK), `version`, `accuracy` | N:1 with `tenants` | Model metadata and versioning. |
| `inference_logs`| `id` (PK), `model_id` (FK), `input_data`, `output` | N:1 with `ml_models` | Log of every ML prediction. |
| `search_indices`| `id` (PK), `document_id`, `content_vector` | N:1 with `inference_logs`| Vectorized data for fast search. |
| `uploads` | `id` (PK), `tenant_id` (FK), `s3_path`, `status` | N:1 with `tenants` | Tracking file upload and scan status. |
| `audit_logs` | `id` (PK), `user_id` (FK), `action`, `timestamp` | N:1 with `users` | SOC 2 compliance audit trail. |

### 5.2 Key Constraints and Indices
- **Index on `inference_logs(tenant_id, timestamp)`**: Optimized for time-series retrieval per tenant.
- **Unique Constraint on `users(email)`**: Prevents duplicate account creation.
- **FK Constraint `on delete cascade`** for `user_2fa` to ensure clean deletion of user profiles.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Obelisk utilizes three distinct environments to ensure stability and zero downtime.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and individual engineer testing.
- **Configuration:** Minimal resource allocation (t3.medium nodes).
- **Deployment:** Triggered on every push to a feature branch.
- **Database:** Shared development DB with anonymized seed data.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and SOC 2 compliance audits.
- **Configuration:** Mirror of production (m5.large nodes).
- **Deployment:** Triggered on merge to `main`.
- **Database:** Separate instance with a restored snapshot of production data (scrubbed).

#### 6.1.3 Production (`prod`)
- **Purpose:** Live client traffic.
- **Configuration:** High-availability cluster across three Availability Zones (AZs).
- **Deployment:** **Rolling Deployments**. Kubernetes updates pods one-by-one to ensure zero downtime. If the health check fails for a new pod, the deployment is automatically rolled back.
- **Database:** Multi-AZ RDS with automated backups and failover.

### 6.2 CI/CD Pipeline (GitLab CI)
The pipeline currently consists of four stages:
1. **Lint/Test:** Runs ESLint and PyTest (approx. 10 mins).
2. **Build:** Dockerizes the 3 separate stacks (approx. 15 mins).
3. **Security Scan:** Runs Snyk for vulnerability detection (approx. 10 mins).
4. **Deploy:** Rolling update to K8s (approx. 10 mins).

**Technical Debt Note:** Total time is 45 minutes. The plan is to parallelize the Build stage using GitLab Runners with larger executors to reduce this to <15 minutes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Frontend:** Jest and React Testing Library. Coverage target: 70%.
- **Backend:** PyTest (FastAPI) and Go Testing. Coverage target: 80%.
- **Focus:** Testing individual functions, API request validation, and mathematical correctness of ML post-processing logic.

### 7.2 Integration Testing
- **Service Interaction:** Testing the communication between the API Gateway and the Legacy Java Wrapper.
- **Database Integration:** Using Testcontainers to run a real PostgreSQL instance during tests to verify RLS policies and schema constraints.
- **Third-Party APIs:** Mocking Stripe and S3 using Prism and LocalStack to avoid incurring costs and side effects during tests.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Critical Paths:** 
    1. User Login $\rightarrow$ 2FA $\rightarrow$ Dashboard.
    2. File Upload $\rightarrow$ Virus Scan $\rightarrow$ Model Inference.
    3. Subscription Upgrade $\rightarrow$ Payment $\rightarrow$ Access Grant.
- **Frequency:** Run on every merge request to `staging`.

### 7.4 Performance Testing
- **Tooling:** k6 (Grafana).
- **Target:** Verify that the p95 response time remains under 200ms while simulating 10,000 concurrent users.
- **Scenario:** "Peak Load" simulation where 50% of users are performing heavy search queries and 50% are requesting ML inferences.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Competitor is 2 months ahead in product launch. | High | High | Develop a "fallback architecture" that allows us to launch a Minimum Viable Product (MVP) with reduced features to capture market share faster. |
| R2 | Team lacks experience with the mixed tech stack. | High | Medium | Create a shared internal Wiki (Knowledge Base) to document workarounds and "gotchas." Hold weekly "Technical Deep Dive" sessions. |
| R3 | Legacy system failure during migration. | Medium | Critical | Implement a "Parallel Run" phase where both systems process data, and results are compared for parity before the legacy system is switched off. |
| R4 | SOC 2 Compliance failure. | Low | High | Engage a 3rd party auditor early for a "Gap Analysis" to identify and fix compliance holes before the final audit. |
| R5 | Budget overrun due to infrastructure costs. | Medium | Medium | Implement strict Kubernetes resource quotas and use Spot Instances for the `dev` and `staging` environments. |

**Probability/Impact Matrix:**
- **Critical:** (High Prob / High Impact) $\rightarrow$ R1
- **High:** (High Prob / Med Impact) $\rightarrow$ R2
- **Moderate:** (Med Prob / High Impact) $\rightarrow$ R3, R4

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases

**Phase 1: Foundation (Now $\rightarrow$ 2025-04-15)**
- Setup K8s clusters and GitLab CI pipelines.
- Implement core Database schema and Tenant isolation.
- **Milestone 1: Architecture Review Complete (2025-04-15).**

**Phase 2: Core Feature Development (2025-04-16 $\rightarrow$ 2025-06-15)**
- Build Advanced Search and File Upload services.
- Finalize 2FA and Auth flows.
- Integration of Legacy Wrapper.
- **Milestone 2: Stakeholder Demo and Sign-off (2025-06-15).**

**Phase 3: Stabilization and Compliance (2025-06-16 $\rightarrow$ 2025-08-15)**
- SOC 2 Type II Audit.
- Performance tuning to hit <200ms p95.
- Final migration from legacy system (The "Big Switch").
- **Milestone 3: Post-launch Stability Confirmed (2025-08-15).**

### 9.2 Dependencies
- **Legal Review** $\rightarrow$ **Billing System**: Billing cannot be finalized until the DPA is signed.
- **Architecture Review** $\rightarrow$ **Feature Development**: Core services cannot be built until the inter-stack communication protocol is approved.
- **S3 Integration** $\rightarrow$ **Virus Scanning**: Scanning logic depends on the S3 event trigger architecture.

---

## 10. MEETING NOTES

*Note: The following are summaries of recorded video calls. Per team culture, these calls are rarely rewatched; these summaries serve as the official record of decision.*

### Meeting 1: The "Legacy Panic" Call
**Date:** 2024-11-02  
**Participants:** Bram Jensen, Cora Jensen, Eshan Santos, Sage Santos  
**Discussion:**
- Bram expressed concern over the "fragility" of the 15-year-old system.
- Sage (Contractor) noted that the C++ engine uses a non-standard memory management system that will crash if called via a standard REST API.
- **Decision:** The team agreed to build a "Java Wrapper" (Spring Boot) to act as a buffer between the modern API Gateway and the legacy C++ engine. This adds latency but prevents system crashes.

### Meeting 2: The "Shoestring Budget" Sync
**Date:** 2024-12-10  
**Participants:** Bram Jensen, Sage Santos  
**Discussion:**
- Review of the $150,000 budget.
- Bram pointed out that we cannot afford a dedicated DevOps engineer for the full project duration.
- **Decision:** Sage will handle the K8s configuration as part of the contract, but the team must prioritize the "Mixed Stack" interoperability over "Nice to Have" features like Multi-tenancy to avoid budget bleed.

### Meeting 3: The "CI Pipeline Frustration" Session
**Date:** 2025-01-20  
**Participants:** Bram Jensen, Cora Jensen, Sage Santos  
**Discussion:**
- Cora noted that the 45-minute CI pipeline is killing frontend productivity. Every CSS change takes nearly an hour to verify in staging.
- Sage explained that the Docker build for the legacy Java stack is the primary bottleneck.
- **Decision:** The team will implement "Layer Caching" and move the Java build to a separate parallel job. This is marked as "Technical Debt" to be solved in the next sprint.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (USD)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $97,500 | Includes Bram (Mgmt), Cora, Eshan, and Sage (Contractor fees). |
| **Infrastructure** | 15% | $22,500 | AWS EKS, RDS, S3, and CloudFront costs for 12 months. |
| **Tools & Licensing** | 10% | $15,000 | GitLab Premium, Snyk, Stripe Fees, and SOC 2 Auditor. |
| **Contingency** | 10% | $15,000 | Reserved for emergency scaling or legal fees. |

**Budgetary Note:** Because the budget is a "shoestring" amount, any expenditure over $500 requires direct approval from Bram Jensen. Every single AWS instance type was scrutinized to ensure we are not over-provisioning.

---

## 12. APPENDICES

### Appendix A: SOC 2 Compliance Checklist
To achieve SOC 2 Type II, the Obelisk team must provide evidence for the following:
1. **Access Control:** Evidence that only authorized personnel have access to the `prod` environment (implemented via IAM roles and Okta).
2. **Change Management:** Evidence that all code changes are reviewed by at least one other engineer (implemented via GitLab Merge Request requirements).
3. **Encryption:** Proof that all data is encrypted at rest (AWS KMS) and in transit (TLS 1.3).
4. **Incident Response:** A documented plan for what happens if the ML model produces biased or incorrect energy predictions.

### Appendix B: Legacy Stack Compatibility Matrix
Since Obelisk inherits three different stacks, the following compatibility layer is enforced:

| Legacy Component | Protocol | Bridge Technology | Target Modern Service |
| :--- | :--- | :--- | :--- |
| C++ Engine v1.2 | Shared Memory | Java JNI / Spring Boot | FastAPI ML Service |
| Python 2.7 Scripts | TCP Socket | Celery / RabbitMQ | Node.js API Gateway |
| Old SQL Server | JDBC | PostgreSQL Foreign Data Wrapper | PostgreSQL 15 |

**Migration Strategy:**
The "Parallel Run" will involve piping 10% of production traffic to both the legacy system and the Obelisk system. A "Comparison Engine" will flag any discrepancies in the ML output. Once the discrepancy rate drops below 0.1% for 14 consecutive days, the legacy system will be decommissioned.