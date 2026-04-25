# PROJECT SPECIFICATION DOCUMENT: PROJECT KEYSTONE
**Document Version:** 1.0.4  
**Status:** Final Approval Pending  
**Date:** October 24, 2025  
**Company:** Flintrock Engineering  
**Project Lead:** Ira Nakamura (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Keystone is a strategic initiative by Flintrock Engineering to transition a high-potential machine learning (ML) prototype—originally developed during a company-wide hackathon—into a robust, scalable, and production-grade internal productivity tool. In the high-stakes environment of cybersecurity, efficiency in threat detection and pattern recognition is paramount. The original hackathon version of Keystone demonstrated an unprecedented ability to automate routine security analysis tasks, quickly gaining a grassroots user base of 500 daily active users (DAU) within the organization.

The current objective is to formalize this tool into a professional deployment, moving away from "shadow IT" and into a governed, secure, and maintainable architectural framework. Keystone will serve as the central hub for ML-driven cybersecurity analysis, allowing engineers to deploy models, monitor their performance, and integrate outputs into existing security workflows.

### 1.2 Business Justification
Currently, the 500 users are relying on an unstable, single-server instance with no formal backup or scaling strategy. The business risk of a failure is significant, as workflows have already become dependent on the tool. By formalizing Keystone, Flintrock Engineering ensures operational continuity and security.

The primary business drivers are:
1. **Operational Efficiency:** Reducing the manual effort required for security log analysis.
2. **Risk Mitigation:** Moving the tool from an unmonitored hackathon script to a secured environment with internal audits.
3. **Knowledge Centralization:** Creating a shared infrastructure where ML models can be versioned and audited across the cybersecurity team.

### 1.3 ROI Projection
With a total budget of $1.5M, the project is positioned to deliver significant returns. The primary ROI metric is the **Cost Per Transaction (CPT)**. The legacy system—consisting of fragmented manual scripts and expensive third-party licenses—currently operates at a high cost per analysis. 

**Projected Financial Gains:**
- **Direct Cost Reduction:** A targeted 35% reduction in cost per transaction compared to the legacy system. This is achieved by optimizing AWS ECS resource allocation and consolidating redundant third-party API calls into a shared Redis cache.
- **Labor Savings:** An estimated saving of 12,000 engineering hours per year across 500 users, assuming a productivity increase of 0.5 hours per user per day.
- **Infrastructure Efficiency:** By implementing multi-tenant data isolation and shared infrastructure, the company avoids the cost of spinning up separate instances for different security teams, reducing cloud spend by an estimated $120k annually.

The total projected ROI over the first 24 months post-launch is estimated at $2.8M, factoring in reclaimed engineering time and infrastructure optimization.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Keystone utilizes a modern micro-frontend architecture, allowing independent team ownership of specific UI modules. The backend is built on a Python/Django framework, leveraging its robust ORM and administrative capabilities, paired with PostgreSQL for relational data and Redis for caching and session management.

The system is deployed on AWS Elastic Container Service (ECS) using Fargate for serverless compute, ensuring that the infrastructure can scale based on the heavy computational demands of ML model inference.

### 2.2 System Diagram (ASCII Description)
The following represents the data flow from the user request to the ML model execution and data persistence.

```text
[ User Browser ] <---> [ CloudFront CDN ] <---> [ AWS ALB (Load Balancer) ]
                                                         |
                                                         v
                                            [ AWS ECS Cluster (Fargate) ]
                                            |---------------------------|
                                            | [ Django App Container ]  | <---> [ Redis Cache ]
                                            | (API Gateway / Logic)     |
                                            |---------------------------|
                                                         |
                                                         v
                                            [ PostgreSQL RDS Instance ]
                                            (Users, Tenants, Logs, Meta)
                                                         |
                                                         v
                                            [ ML Model Inference Engine ]
                                            (S3 Model Store -> Memory)
                                                         |
                                                         v
                                            [ External Third-Party APIs ]
                                            (Via Webhook Framework)
```

### 2.3 Architecture Details
- **Micro-Frontend Strategy:** The UI is split into "Module-Containers." For example, the "Analytics Dashboard" and the "Model Management Console" are developed and deployed independently, preventing a single UI bug from crashing the entire application.
- **Data Layer:** PostgreSQL 15.4 is utilized for structured data. Redis 7.2 serves as the primary message broker for asynchronous tasks (via Celery) and as a high-speed cache for ML inference results.
- **Compute:** AWS ECS ensures that the Python/Django environment is isolated. The ML models are loaded into memory via a custom wrapper that interacts with the ECS task definition.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework
**Priority:** Medium | **Status:** In Review
**Description:**
The Webhook Integration Framework allows Keystone to communicate with external cybersecurity tools (e.g., SIEMs, Jira, Slack) and receive triggers from them. This transforms Keystone from a passive tool into an active participant in the security ecosystem.

**Detailed Requirements:**
- **Event Subscription:** Users must be able to define "Triggers" (e.g., "When a high-severity alert is triggered in CrowdStrike") and "Actions" (e.g., "Run ML Model X on the affected IP").
- **Payload Transformation:** A flexible mapping engine that allows users to map incoming JSON fields from third-party tools to Keystone internal data schemas.
- **Security Handshake:** Implementation of HMAC signatures for all incoming webhooks to ensure that requests originate from trusted sources.
- **Retry Logic:** An exponential backoff mechanism to handle downstream failures, ensuring that critical security alerts are not lost.

**Technical Implementation:**
The framework will use a dedicated Django app `keystone.webhooks`. It will utilize a PostgreSQL table to store endpoint URLs and secret keys. Incoming requests will be queued in Redis and processed asynchronously by Celery workers to avoid blocking the API response.

### 3.2 Multi-Tenant Data Isolation
**Priority:** Medium | **Status:** Not Started
**Description:**
As Keystone expands, different security teams within Flintrock Engineering (e.g., Incident Response, Threat Hunting, Compliance) must have their data isolated to prevent leakage and ensure a clean audit trail, while still sharing the same underlying ECS hardware.

**Detailed Requirements:**
- **Logical Separation:** Implementation of a `tenant_id` column across all primary database tables. Every query must be scoped to the current user's `tenant_id`.
- **Shared Infrastructure:** To minimize costs, the project will use a "Shared Schema" approach rather than "Schema-per-Tenant," utilizing PostgreSQL Row-Level Security (RLS) where possible.
- **Tenant Administration:** A centralized admin panel for Ira Nakamura to assign users to specific tenants and manage resource quotas per tenant.
- **Cross-Tenant Sharing:** A controlled mechanism to allow a "Global Admin" to view data across all tenants for organization-wide security reports.

**Technical Implementation:**
A custom Django Middleware will be developed to extract the `tenant_id` from the session or JWT and apply a global filter to all QuerySets using a custom Manager class.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** In Review
**Description:**
To prevent any single user or automated script from crashing the ML inference engine, a sophisticated rate-limiting system is required. Additionally, management needs visibility into which features are being used to justify the $1.5M investment.

**Detailed Requirements:**
- **Tiered Rate Limits:** Different limits for "Standard Users" (e.g., 100 requests/min) and "Power Users/Service Accounts" (e.g., 1000 requests/min).
- **Sliding Window Algorithm:** Implementation of a sliding window counter using Redis to ensure precise rate limiting.
- **Usage Telemetry:** Every API call must be logged with metadata: user ID, tenant ID, endpoint, response time, and payload size.
- **Analytics Dashboard:** A visualization layer showing "Top 10 Most Used Models" and "Peak Usage Hours."

**Technical Implementation:**
The system will leverage `django-ratelimit` for basic constraints, with a custom Redis-based implementation for the sliding window. Analytics will be pushed to a PostgreSQL table `api_logs` and aggregated hourly via a cron job.

### 3.4 Advanced Search with Faceted Filtering
**Priority:** Medium | **Status:** In Review
**Description:**
With 500 users generating thousands of ML analysis reports, finding specific historical data is becoming impossible. A full-text search engine with the ability to filter by categories (facets) is required.

**Detailed Requirements:**
- **Full-Text Indexing:** Integration of PostgreSQL `tsvector` and `tsquery` for efficient searching across large text blocks (e.g., ML model output logs).
- **Faceted Navigation:** The UI must allow users to narrow results by: Date Range, Model Version, Threat Level, and Tenant.
- **Search Suggestions:** An autocomplete feature that suggests previous queries or common security tags.
- **Indexing Pipeline:** An asynchronous process that indexes new ML reports in real-time as they are generated.

**Technical Implementation:**
The search functionality will be implemented via a specialized `SearchIndex` table. We will avoid adding an external Elasticsearch cluster to keep the stack lean, instead relying on GIN indexes in PostgreSQL to achieve sub-second search latency.

### 3.5 Real-Time Collaborative Editing
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:**
Security analysts often need to collaborate on the "Final Report" derived from ML findings. This feature allows multiple users to edit the same analysis document simultaneously.

**Detailed Requirements:**
- **Conflict Resolution:** Use of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to ensure that simultaneous edits do not overwrite each other.
- **Presence Indicators:** Real-time "Cursors" showing where other team members are currently typing.
- **Version History:** The ability to roll back to any previous version of a collaboratively edited document.
- **WebSocket Integration:** Use of Django Channels to maintain a persistent connection between the client and server.

**Technical Implementation:**
This is the most complex feature and will be implemented using `Yjs` (a CRDT library) on the frontend and a WebSocket consumer in Django Channels. Given its "Low" priority, if technical hurdles arise, this will be the first feature candidate for de-scoping.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and require a Bearer Token in the Authorization header. Base URL: `https://keystone.flintrock.internal/api/v1/`

### 4.1 ML Model Inference
- **Endpoint:** `POST /models/infer/`
- **Description:** Sends data to a specific ML model for analysis.
- **Request:**
  ```json
  {
    "model_id": "cyber-threat-v2.1",
    "input_data": "base64_encoded_log_stream",
    "tenant_id": "sec_ops_01"
  }
  ```
- **Response:** `202 Accepted` (Returns a `job_id` for polling).

### 4.2 Inference Status Polling
- **Endpoint:** `GET /models/status/{job_id}/`
- **Description:** Checks if the ML model has finished processing the request.
- **Response:**
  ```json
  {
    "job_id": "abc-123",
    "status": "completed",
    "result_url": "/api/v1/models/result/abc-123/"
  }
  ```

### 4.3 Webhook Registration
- **Endpoint:** `POST /webhooks/register/`
- **Description:** Registers a third-party tool to receive notifications.
- **Request:**
  ```json
  {
    "target_url": "https://hooks.slack.com/services/T000/B000",
    "event_type": "model_completion",
    "secret_token": "k3yst0ne_secret_99"
  }
  ```
- **Response:** `201 Created`.

### 4.4 Tenant Management
- **Endpoint:** `GET /tenants/{tenant_id}/users/`
- **Description:** Lists all users associated with a specific security tenant.
- **Response:** `200 OK` with a list of user objects.

### 4.5 Advanced Search
- **Endpoint:** `GET /search/`
- **Description:** Performs faceted search across ML reports.
- **Query Params:** `?q=malware&threat_level=high&start_date=2026-01-01`
- **Response:** `200 OK` with a paginated list of report summaries.

### 4.6 Usage Analytics
- **Endpoint:** `GET /analytics/usage/`
- **Description:** Returns aggregate usage statistics for the authenticated tenant.
- **Response:**
  ```json
  {
    "total_requests": 5400,
    "avg_latency": "120ms",
    "cost_per_transaction": 0.04
  }
  ```

### 4.7 Model Version Control
- **Endpoint:** `POST /models/version/`
- **Description:** Deploys a new version of an ML model.
- **Request:**
  ```json
  {
    "model_name": "anomaly-detector",
    "version": "3.0.1",
    "s3_path": "s3://flintrock-ml/models/ad-3.0.1.pkl"
  }
  ```
- **Response:** `201 Created`.

### 4.8 Collaboration Session
- **Endpoint:** `POST /collaboration/session/`
- **Description:** Initializes a WebSocket session for collaborative editing.
- **Request:** `{"document_id": "rep-999"}`
- **Response:** `200 OK` with a WebSocket connection URL.

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15.4 instance. All tables use UUIDs as primary keys to facilitate distributed data scaling.

### 5.1 Table Definitions

1. **`tenants`**
   - `id` (UUID, PK): Unique identifier for the organization unit.
   - `name` (VARCHAR): Name of the security team.
   - `created_at` (TIMESTAMP): Record creation date.
   - `config` (JSONB): Tenant-specific settings.

2. **`users`**
   - `id` (UUID, PK): Unique identifier.
   - `tenant_id` (UUID, FK): Link to `tenants`.
   - `username` (VARCHAR, Unique): User login.
   - `role` (ENUM): 'Admin', 'Analyst', 'Viewer'.
   - `last_login` (TIMESTAMP).

3. **`ml_models`**
   - `id` (UUID, PK): Unique identifier.
   - `name` (VARCHAR): Model name.
   - `version` (VARCHAR): Semantic version (e.g., 1.2.0).
   - `s3_path` (TEXT): Path to the model weights in AWS S3.
   - `is_active` (BOOLEAN): Whether the model is currently serving requests.

4. **`inference_jobs`**
   - `id` (UUID, PK): Job identifier.
   - `model_id` (UUID, FK): Link to `ml_models`.
   - `tenant_id` (UUID, FK): Link to `tenants`.
   - `status` (ENUM): 'Pending', 'Processing', 'Completed', 'Failed'.
   - `input_hash` (TEXT): SHA-256 hash of input for caching.
   - `created_at` (TIMESTAMP).

5. **`inference_results`**
   - `id` (UUID, PK): Result identifier.
   - `job_id` (UUID, FK): Link to `inference_jobs`.
   - `output_data` (JSONB): The ML model's findings.
   - `execution_time` (FLOAT): Time taken in milliseconds.

6. **`webhooks`**
   - `id` (UUID, PK): Webhook identifier.
   - `tenant_id` (UUID, FK): Owner of the webhook.
   - `target_url` (TEXT): Destination URL.
   - `secret` (VARCHAR): Secret for HMAC signing.
   - `event_type` (VARCHAR): e.g., "job_completed".

7. **`api_logs`**
   - `id` (BIGINT, PK): Sequential ID.
   - `user_id` (UUID, FK): Who made the request.
   - `endpoint` (TEXT): API path accessed.
   - `response_code` (INT): HTTP status.
   - `latency` (INT): Response time in ms.
   - `timestamp` (TIMESTAMP).

8. **`search_index`**
   - `id` (UUID, PK): Index identifier.
   - `document_id` (UUID, FK): Link to `inference_results`.
   - `content_vector` (TSVECTOR): PostgreSQL full-text search vector.

9. **`collaboration_docs`**
   - `id` (UUID, PK): Document identifier.
   - `tenant_id` (UUID, FK): Owner tenant.
   - `content` (TEXT): The current state of the document.
   - `version` (INT): Current version number.

10. **`collaboration_history`**
    - `id` (UUID, PK): History identifier.
    - `doc_id` (UUID, FK): Link to `collaboration_docs`.
    - `user_id` (UUID, FK): Who made the change.
    - `change_delta` (JSONB): The specific change made.
    - `timestamp` (TIMESTAMP).

### 5.2 Key Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `tenants` $\rightarrow$ `inference_jobs`, `tenants` $\rightarrow$ `webhooks`.
- **One-to-One:** `inference_jobs` $\rightarrow$ `inference_results`.
- **Many-to-One:** `inference_jobs` $\rightarrow$ `ml_models`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Keystone follows a strict three-tier environment promotion strategy to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and initial unit testing.
- **Configuration:** Smallest possible ECS Fargate tasks (0.25 vCPU, 0.5 GB RAM).
- **Database:** Local PostgreSQL containers and a shared Dev RDS instance.
- **Deployment:** Continuous Deployment (CD) triggered on every merge to the `develop` branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and QA.
- **Configuration:** Mirror of production (1 vCPU, 2 GB RAM) but with lower replica counts.
- **Database:** Staging RDS instance with a sanitized snapshot of production data.
- **Deployment:** Triggered upon a release candidate (RC) tag.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user environment (500 DAU).
- **Configuration:** High-availability ECS Fargate cluster across two Availability Zones (AZs).
- **Database:** Multi-AZ PostgreSQL RDS with automated backups and read replicas.
- **Deployment:** Weekly Release Train (see Section 2.3).

### 6.2 The Weekly Release Train
The project adheres to a strict "Release Train" philosophy. 
- **Schedule:** Deployments occur every Wednesday at 03:00 UTC.
- **Cut-off:** Code must be merged and verified in Staging by Monday at 17:00 UTC to be included in the Wednesday train.
- **No Hotfixes:** To ensure stability and prevent "configuration drift," no hotfixes are permitted outside the train. If a critical bug is found, it must wait for the next Wednesday cycle unless a "Catastrophic Failure" is declared by Ira Nakamura.

### 6.3 Infrastructure Constraints
**Current Blocker:** As of October 2025, infrastructure provisioning for the Production ECS cluster has been delayed by the cloud provider (AWS) due to region-specific capacity constraints. Yuki Park is currently exploring alternative AZs to resolve this.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** All business logic in Django views, serializers, and utility functions.
- **Framework:** `pytest` with `pytest-django`.
- **Requirement:** Minimum 80% code coverage for all new features.
- **Execution:** Run on every Pull Request via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between Django, Redis, and PostgreSQL.
- **Focus:** Specifically targeting the Webhook framework and the Multi-Tenant isolation logic to ensure `tenant_id` leaks are impossible.
- **Execution:** Run in the Staging environment daily.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user paths (e.g., "Upload Log $\rightarrow$ Run Model $\rightarrow$ View Result").
- **Framework:** Playwright.
- **Focus:** Testing the micro-frontend boundaries to ensure the "Analytics" module doesn't break when the "Model Management" module is updated.
- **Execution:** Manual sign-off by Dina Moreau (QA Lead) prior to every Wednesday release train.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for cybersecurity data may change. | High | High | Hire a specialized contractor to provide regulatory guidance and reduce the "bus factor" of internal legal knowledge. |
| R-02 | Team lacks deep experience with Django/ECS stack. | Medium | High | De-scope low-priority features (e.g., Collaborative Editing) if the team cannot reach proficiency by Milestone 1. |
| R-03 | Cloud provider provisioning delays. | High | Medium | Explore multi-region deployment or temporary migration to alternative instance types. |
| R-04 | Performance degradation as user base grows. | Medium | Medium | Implement aggressive Redis caching and PostgreSQL indexing based on `api_logs` data. |

**Probability/Impact Matrix:**
- **High/High:** Immediate Action Required (R-01).
- **High/Medium:** Monitoring and contingency planning (R-03).
- **Medium/High:** Skill acquisition and scope management (R-02).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Description
The project is divided into three primary phases: Foundation, Validation, and Launch.

#### Phase 1: Foundation (Now $\rightarrow$ 2026-07-15)
- Focus: Establishing the ECS infrastructure, implementing the multi-tenant core, and completing the ML inference pipeline.
- **Dependency:** Resolution of AWS provisioning blocker.
- **Milestone 1:** MVP Feature-Complete (Target: 2026-07-15).

#### Phase 2: Validation (2026-07-16 $\rightarrow$ 2026-09-15)
- Focus: Implementing the Webhook framework, Advanced Search, and API Rate Limiting. Rigorous QA by Dina Moreau.
- **Dependency:** Successful completion of MVP features.
- **Milestone 2:** Stakeholder Demo and Sign-off (Target: 2026-09-15).

#### Phase 3: Launch (2026-09-16 $\rightarrow$ 2026-11-15)
- Focus: Final stress testing, documentation, and gradual rollout to the 500 users.
- **Dependency:** Stakeholder sign-off from Milestone 2.
- **Milestone 3:** Production Launch (Target: 2026-11-15).

### 9.2 Gantt-Style Dependency Map
`Infrastructure` $\rightarrow$ `Multi-Tenancy` $\rightarrow$ `ML Pipeline` $\rightarrow$ `Webhooks/Search` $\rightarrow$ `QA Sign-off` $\rightarrow$ `Launch`.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per the team dynamic, formal minutes are not taken. The following decisions are extracted from documented Slack threads.

### Meeting 1: Architecture Alignment (Thread: #keystone-dev)
**Participants:** Ira Nakamura, Yuki Park, Rafik Stein
- **Topic:** Database scaling.
- **Discussion:** Rafik suggested using MongoDB for the ML results because the output is semi-structured. Yuki argued that adding another database increases the maintenance burden and that PostgreSQL JSONB is sufficient.
- **Decision:** Use PostgreSQL JSONB for all ML results to keep the stack lean.
- **Action:** Yuki to set up RDS instance.

### Meeting 2: Release Cadence Debate (Thread: #keystone-ops)
**Participants:** Ira Nakamura, Dina Moreau, Yuki Park
- **Topic:** Hotfix policy.
- **Discussion:** Dina expressed concern that waiting a full week for a bug fix during the pilot phase would frustrate users. Ira insisted that "hotfix culture" leads to production instability.
- **Decision:** Strict adherence to the Wednesday Release Train. No exceptions. If a bug is "show-stopping," the team will use feature flags to disable the broken component rather than deploying an unplanned fix.

### Meeting 3: Feature Prioritization (Thread: #keystone-mgmt)
**Participants:** Ira Nakamura, Dina Moreau
- **Topic:** Collaborative Editing vs. Webhooks.
- **Discussion:** The team is behind on the Webhook framework. Dina suggested that Collaborative Editing (currently in progress) is a "nice-to-have" and could be delaying the "must-have" integration features.
- **Decision:** Move Collaborative Editing to "Low Priority." If the Webhook framework isn't ready by July, Collaborative Editing will be stripped from the MVP.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000 USD

### 11.1 Personnel ($1,100,000)
- **Project Lead (Ira Nakamura):** $220,000 (Salary + Bonus)
- **DevOps Engineer (Yuki Park):** $180,000
- **QA Lead (Dina Moreau):** $160,000
- **Junior Developer (Rafik Stein):** $90,000
- **Other 8 Cross-functional members:** $450,000 (Pro-rated allocation from other teams)

### 11.2 Infrastructure ($200,000)
- **AWS ECS Fargate:** $80,000 (Annual projected cost)
- **AWS RDS (PostgreSQL):** $50,000
- **AWS S3 & CloudFront:** $30,000
- **Redis Managed Service:** $40,000

### 11.3 Tools & Third-Party Services ($100,000)
- **JIRA/Confluence Licenses:** $20,000
- **Security Scanning Tools:** $50,000
- **ML Model Training Compute (Spot Instances):** $30,000

### 11.4 Contingency ($100,000)
- **Regulatory Contractor:** $60,000 (Allocated to mitigate Risk R-01)
- **Emergency Buffer:** $40,000

---

## 12. APPENDICES

### Appendix A: Technical Debt Registry
The current version of Keystone suffers from significant technical debt inherited from the hackathon project:
1. **Logging:** There is currently no structured logging framework. All debugging is performed by reading `stdout` from the ECS containers.
   - *Resolution:* Implementation of `structlog` is scheduled for Phase 1.
2. **Hardcoded Secrets:** Several API keys are currently hardcoded in the `.env` files.
   - *Resolution:* Migration to AWS Secrets Manager is mandatory before Milestone 1.
3. **Lack of Type Hinting:** The original Python code lacks type hints, making it difficult for Rafik Stein to maintain.
   - *Resolution:* Gradual introduction of `mypy` for all new modules.

### Appendix B: ML Model Loading Sequence
To optimize the ECS Fargate startup time, the following loading sequence is implemented:
1. **Container Start:** Django initializes and checks the `ml_models` table.
2. **Weight Retrieval:** The system checks the Redis cache for a "Warm-up" flag.
3. **S3 Pull:** If the flag is missing, the model weights are pulled from S3 to a local `/tmp` directory.
4. **Memory Map:** The model is loaded into memory using `joblib` with `mmap_mode='r'` to reduce RAM overhead.
5. **Health Check:** The container reports "Healthy" to the ALB only after the model is fully loaded into memory.