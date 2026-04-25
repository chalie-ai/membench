Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, high-fidelity Project Specification. It serves as the "Single Source of Truth" (SSOT) for Project Umbra.

***

# PROJECT SPECIFICATION: PROJECT UMBRA
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Company:** Flintrock Engineering  
**Confidentiality Level:** Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Umbra is a strategic initiative by Flintrock Engineering to modernize the core operational backbone of our legal services division. For fifteen years, the company has relied on a legacy monolithic system (codenamed "The Vault") for model processing and case management. While stable, The Vault has become a bottleneck, lacking the scalability to handle modern machine learning (ML) workloads and the flexibility required for current legal data standards.

Umbra is not merely an upgrade; it is a complete replacement. The project involves deploying a state-of-the-art ML model deployment framework that manages the lifecycle of legal predictive models—from inference to auditing. Given that the entire company depends on this system for daily operations, the primary constraint is a **zero-downtime tolerance**. Any outage during the transition from The Vault to Umbra would result in an immediate loss of billable hours and potential breach of client SLAs.

### 1.2 Business Justification
The business case for Umbra is driven by three primary factors:
1. **Operational Risk:** The legacy system runs on hardware and software versions that are no longer supported, creating a critical failure risk.
2. **Performance Bottlenecks:** Current inference times for legal document analysis are averaging 12 seconds per page; Umbra aims to reduce this to <2 seconds.
3. **Revenue Expansion:** The current system cannot support a multi-tenant subscription model, preventing Flintrock from offering "Law-as-a-Service" (LaaS) to external firms.

### 1.3 ROI Projection
The budget for Project Umbra is capped at $400,000. While modest, this is sufficient for a lean, highly skilled team focused on a phased rollout.

**Projected Financial Impact:**
- **Direct Revenue:** The primary success metric is the generation of **$500,000 in new revenue** within the first 12 months post-launch. This will be achieved via the new automated billing and subscription modules, allowing for tiered pricing based on API call volume.
- **Cost Reduction:** By migrating to AWS ECS, we expect a 30% reduction in server maintenance overhead compared to the on-premise legacy hardware.
- **Efficiency Gain:** We project a 20% increase in lawyer productivity due to the advanced search and faster ML inference times.

**ROI Calculation (12 Month):**
$\text{ROI} = \frac{(\text{New Revenue} + \text{Cost Savings}) - \text{Initial Investment}}{\text{Initial Investment}}$
$\text{ROI} = \frac{(\$500,000 + \$40,000) - \$400,000}{\$400,000} = 35\%$

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern
Umbra utilizes a traditional three-tier architecture to ensure a clean separation of concerns, facilitate independent scaling, and simplify the manual QA gate process.

1. **Presentation Tier:** A Django-based frontend providing a web interface for internal administrators and a RESTful API for external consumers.
2. **Business Logic Tier (Application Layer):** Python/Django services that handle the orchestration of ML model calls, authentication, and billing logic.
3. **Data Tier:** A persistent layer comprising PostgreSQL for relational data and Redis for high-speed caching and session management.

### 2.2 System Diagram (ASCII)

```text
[ CLIENTS ] ----> [ AWS Application Load Balancer ]
                          |
                          v
[ AWS ECS Cluster (Django Application Containers) ]
    |                     |                     |
    | (REST/JSON)         | (Cache/Queue)        | (SQL)
    v                     v                     v
[ ML Model Endpoints ]  [ Redis Cluster ]    [ PostgreSQL DB ]
    |                     |                     |
    +--- S3 Model Store ---+                     +--- Backup S3 ---+
```

### 2.3 Component Details
- **Language:** Python 3.11 (Strict typing via MyPy).
- **Framework:** Django 4.2 LTS.
- **Database:** PostgreSQL 15.2 (RDS).
- **Cache/Broker:** Redis 7.0 (ElastiCache).
- **Compute:** AWS ECS (Fargate) to eliminate server management overhead.
- **Model Storage:** AWS S3 for versioned `.pkl` and `.h5` model artifacts.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** Critical | **Status:** Complete | **ID:** FEAT-001

**Description:**
This feature is the primary launch blocker. It replaces the manual invoicing process of the legacy system with an automated, subscription-based engine. The system must track API consumption per client, calculate monthly costs based on tiered pricing, and automatically trigger invoices via the Stripe API.

**Functional Requirements:**
- **Tiered Pricing:** Support for three tiers: *Basic* (1k calls/mo), *Professional* (10k calls/mo), and *Enterprise* (Unlimited).
- **Consumption Tracking:** Every single call to the ML inference engine must be logged in the `api_usage` table with a timestamp and client ID.
- **Automatic Invoicing:** On the 1st of every month, the system must aggregate the previous month's usage and generate a PDF invoice.
- **Grace Periods:** If a payment fails, the system must grant a 7-day grace period before restricting API access.

**Technical Implementation:**
The system utilizes a background Celery worker that polls the `subscription` table. A Django signal is triggered upon every successful ML inference, incrementing the usage counter in Redis to avoid hitting PostgreSQL for every single request. Every 10 minutes, the Redis counter is flushed to the primary DB.

---

### 3.2 SSO Integration (SAML and OIDC)
**Priority:** Medium | **Status:** Complete | **ID:** FEAT-002

**Description:**
To ensure security and streamline onboarding for large legal firms, Umbra implements Single Sign-On (SSO). This allows clients to use their existing corporate credentials (Azure AD, Okta, Google Workspace) to access the platform.

**Functional Requirements:**
- **SAML 2.0 Support:** Ability to upload metadata XML files from client Identity Providers (IdPs).
- **OIDC Support:** Implementation of the OpenID Connect flow for modern OAuth2-based providers.
- **Just-in-Time (JIT) Provisioning:** Automatically create a user account in the Umbra database upon their first successful SSO login, mapping their corporate email to a unique internal ID.
- **Role Mapping:** Ability to map SAML attributes (e.g., `memberOf`) to Django Group permissions (e.g., `Admin`, `Analyst`).

**Technical Implementation:**
Implemented using the `python3-saml` library and `django-allauth`. The system maintains a `sso_configuration` table that stores the EntityID, SSO URL, and Public Certificate for each tenant.

---

### 3.3 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** In Progress | **ID:** FEAT-003

**Description:**
The notification system is designed to keep users informed of model completion status, billing alerts, and system maintenance. It must be polymorphic, allowing a single event (e.g., "Model Processing Complete") to be routed through multiple channels based on user preference.

**Functional Requirements:**
- **Preference Center:** Users must be able to toggle notifications for each channel (Email, SMS, In-App, Push) on a per-category basis.
- **Templating Engine:** Use of Jinja2 templates to allow the marketing team to update email layouts without developer intervention.
- **SMS Integration:** Integration with Twilio for critical alerts.
- **Push Notifications:** Use of Firebase Cloud Messaging (FCM) for web-push alerts.
- **Queueing:** All notifications must be processed asynchronously via Redis/Celery to prevent blocking the main application thread.

**Technical Implementation:**
A `Notification` model acts as the source of truth, while `NotificationChannel` defines the delivery method. A `NotificationDispatcher` class evaluates the user's preferences and iterates through the active channels to deliver the payload.

---

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Low | **Status:** In Design | **ID:** FEAT-004

**Description:**
To allow external partners to integrate their own software with Umbra, a public-facing API is required. This must include a "Sandbox" environment where developers can test their integrations using mock data without incurring costs or affecting production models.

**Functional Requirements:**
- **URI Versioning:** API endpoints must be versioned (e.g., `/api/v1/predict/` and `/api/v2/predict/`).
- **API Key Management:** Users can generate, rotate, and revoke API keys through their dashboard.
- **Sandbox Isolation:** Sandbox requests are routed to a separate set of "mock" models that return deterministic responses for testing.
- **Rate Limiting:** Implement a "leaky bucket" algorithm to limit requests based on the user's subscription tier.

**Technical Implementation:**
Planned implementation using Django Rest Framework (DRF). Versioning will be handled via URL paths. The sandbox will be a separate ECS service deployment mirroring the production environment but connected to a "sandbox" PostgreSQL schema.

---

### 3.5 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** Blocked | **ID:** FEAT-005

**Description:**
Legal practitioners need to search through millions of processed documents. Standard SQL `LIKE` queries are insufficient. This feature requires a full-text search (FTS) engine capable of handling complex legal terminology and providing faceted filters (e.g., filter by Date, Case Type, Jurisdiction).

**Functional Requirements:**
- **Full-Text Indexing:** Indexing of all uploaded legal documents and ML-generated summaries.
- **Faceted Filtering:** A sidebar allowing users to narrow results by multiple dimensions.
- **Highlighting:** Search results must highlight the exact phrase where the match was found.
- **Synonym Support:** The search engine must recognize that "Attorney" and "Lawyer" are functionally equivalent in this context.

**Technical Implementation:**
Currently blocked pending a decision on whether to use PostgreSQL's built-in GIN indexing or to deploy a dedicated Elasticsearch cluster. If the volume of documents exceeds 10 million, Elasticsearch will be the required path.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under the base URL: `https://api.umbra.flintrock.io`

### 4.1 `POST /api/v1/auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Request Body:**
  ```json
  { "email": "user@firm.com", "password": "hashed_password" }
  ```
- **Response (200 OK):**
  ```json
  { "token": "eyJhbGci...", "expires_in": 3600 }
  ```

### 4.2 `POST /api/v1/models/predict`
- **Description:** Sends a document for ML inference.
- **Request Body:**
  ```json
  { "document_id": "DOC-9982", "model_version": "2.1.0", "priority": "high" }
  ```
- **Response (202 Accepted):**
  ```json
  { "job_id": "job_abc_123", "status": "queued", "eta": "45s" }
  ```

### 4.3 `GET /api/v1/models/status/{job_id}`
- **Description:** Checks the status of a specific prediction job.
- **Response (200 OK):**
  ```json
  { "job_id": "job_abc_123", "status": "completed", "result_url": "/api/v1/results/abc_123" }
  ```

### 4.4 `GET /api/v1/billing/usage`
- **Description:** Returns the current month's API usage for the authenticated client.
- **Response (200 OK):**
  ```json
  { "client_id": "C-55", "calls_used": 4502, "tier_limit": 10000, "percentage": 45.02 }
  ```

### 4.5 `PUT /api/v1/user/preferences`
- **Description:** Updates notification settings.
- **Request Body:**
  ```json
  { "email_notifications": true, "sms_notifications": false, "push_notifications": true }
  ```
- **Response (200 OK):**
  ```json
  { "status": "updated" }
  ```

### 4.6 `POST /api/v1/sso/config`
- **Description:** Configures SAML/OIDC settings for a new tenant.
- **Request Body:**
  ```json
  { "tenant_id": "T-101", "provider": "okta", "metadata_url": "https://okta.com/app/metadata" }
  ```
- **Response (201 Created):**
  ```json
  { "config_id": "cfg_992", "status": "pending_verification" }
  ```

### 4.7 `GET /api/v1/documents/search`
- **Description:** Executes a faceted search across legal documents. (Currently Mocked)
- **Request Parameters:** `?q=merger+agreement&jurisdiction=NY&date_start=2020-01-01`
- **Response (200 OK):**
  ```json
  { "results": [...], "facets": { "jurisdiction": { "NY": 50, "CA": 20 } }, "total": 70 }
  ```

### 4.8 `DELETE /api/v1/api-keys/{key_id}`
- **Description:** Revokes an active API key.
- **Response (204 No Content):**
  *(Empty body)*

---

## 5. DATABASE SCHEMA

### 5.1 Entity Relationship Overview
The database is a relational PostgreSQL schema. The core of the system revolves around the `Client` entity, which links to `Subscriptions`, `Users`, and `InferenceJobs`.

### 5.2 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `clients` | `client_id` | None | `company_name`, `tax_id`, `created_at` | Top-level tenant info |
| `users` | `user_id` | `client_id` | `email`, `password_hash`, `last_login` | User authentication |
| `subscriptions`| `sub_id` | `client_id` | `tier_level`, `start_date`, `status` | Billing tier management |
| `api_keys` | `key_id` | `user_id` | `key_value`, `created_at`, `is_active` | API authentication |
| `api_usage` | `usage_id` | `client_id` | `endpoint`, `timestamp`, `cost_cents` | Audit log for billing |
| `models` | `model_id` | None | `version`, `s3_path`, `is_active` | Versioning of ML models |
| `inference_jobs`| `job_id` | `user_id`, `model_id`| `status`, `input_doc_id`, `result_json`| Lifecycle of a prediction |
| `documents` | `doc_id` | `client_id` | `file_path`, `checksum`, `upload_date`| Metadata for processed files |
| `notifications` | `notif_id` | `user_id` | `channel`, `content`, `sent_at` | History of sent alerts |
| `sso_configs` | `config_id` | `client_id` | `idp_url`, `cert_public`, `protocol` | SAML/OIDC settings |

### 5.3 Relationships
- `clients` $\rightarrow$ `users` (1:N)
- `clients` $\rightarrow$ `subscriptions` (1:1)
- `clients` $\rightarrow$ `api_usage` (1:N)
- `users` $\rightarrow$ `inference_jobs` (1:N)
- `models` $\rightarrow$ `inference_jobs` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra utilizes three distinct environments to ensure stability and the enforcement of the manual QA gate.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and unit testing.
- **Infrastructure:** Small ECS Fargate task, local PostgreSQL.
- **Access:** Open to the development team.
- **CI/CD:** Automatic deploy on every merge to `develop` branch.

#### 6.1.2 Staging (QA)
- **Purpose:** Final validation and User Acceptance Testing (UAT).
- **Infrastructure:** Mirrors Production exactly (AWS ECS, RDS, Redis).
- **Access:** Limited to the Project Team and select Pilot Users.
- **CI/CD:** Deploys only after a successful merge to `release` branch. This is where the **Manual QA Gate** occurs.

#### 6.1.3 Production (Prod)
- **Purpose:** Live company operations.
- **Infrastructure:** Multi-AZ deployment for high availability.
- **Access:** Restricted to the Tech Lead (Tariq Kim) and Support Engineer (Wes Park).
- **CI/CD:** 2-day turnaround. Deployments happen only after Mosi Liu (QA Lead) signs off on the Staging build.

### 6.2 The Manual QA Gate
Given the zero-downtime requirement, no code reaches production without a manual sign-off.
1. Developer pushes to `release`.
2. Automated tests run in Staging.
3. Mosi Liu performs a 24-hour regression test.
4. If passed, Tariq Kim triggers the production deployment via the AWS CLI.
5. If failed, the build is rolled back to the previous stable version in Staging.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** `pytest`
- **Coverage Target:** 85%
- **Focus:** Business logic in `services.py`, utility functions, and model validation logic.
- **Frequency:** Run on every commit.

### 7.2 Integration Testing
- **Tool:** Django Test Suite + TestContainers
- **Focus:** Database transactions, Redis cache hits/misses, and third-party API integrations (Stripe, Twilio).
- **Strategy:** We use a temporary PostgreSQL container to ensure the schema is migrated correctly before testing the API endpoints.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright / Selenium
- **Focus:** Critical user paths (e.g., "Login $\rightarrow$ Upload Document $\rightarrow$ View Prediction $\rightarrow$ Check Billing").
- **Frequency:** Run once per release cycle in the Staging environment.

### 7.4 Load Testing
- **Tool:** Locust
- **Target:** 500 concurrent requests per second on the `/predict` endpoint.
- **Goal:** Ensure the ECS Auto-scaling group triggers correctly when CPU utilization hits 70%.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-001 | Key architect leaving in 3 months | High | Critical | Escalate to steering committee for budget to hire a permanent replacement or a high-end contractor. |
| R-002 | Regulatory requirements change | Medium | High | Engage external legal-tech consultant for independent monthly assessments. |
| R-003 | Legacy system data corruption | Low | Critical | Implement a "read-only" shadow mode during migration to verify data integrity. |
| R-004 | AWS Outage | Low | High | Deploy across two AWS Availability Zones (AZs) to ensure failover. |
| R-005 | Budget Overrun | Medium | Low | Strict adherence to "must-have" features; defer low-priority features to Post-MVP. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project halt or company-wide operational failure.
- **High:** Significant delay in milestones or major feature rework.
- **Medium:** Minor delay or inconvenience.
- **Low:** Negligible impact on timeline.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Now – 2025-07-15)
- **Focus:** Core infrastructure, SSO, and Billing.
- **Dependency:** Completion of the database schema migration.
- **Milestone 1:** **External beta with 10 pilot users (2025-07-15).**

### 9.2 Phase 2: Feature Expansion (2025-07-16 – 2025-09-15)
- **Focus:** Notification system, ML model optimization, and API sandbox.
- **Dependency:** Successful stability of the Beta group.
- **Milestone 2:** **MVP feature-complete (2025-09-15).**

### 9.3 Phase 3: Final Validation (2025-09-16 – 2025-11-15)
- **Focus:** Load testing, external audit prep, and stakeholder walkthroughs.
- **Dependency:** Feature freeze on 2025-10-01.
- **Milestone 3:** **Stakeholder demo and sign-off (2025-11-15).**

### 9.4 Gantt Description
- **Month 1-3:** Infrastructure Setup $\rightarrow$ SSO Integration $\rightarrow$ Billing Logic.
- **Month 4-6:** ML Model Porting $\rightarrow$ Beta Testing $\rightarrow$ Notification System.
- **Month 7-9:** API Versioning $\rightarrow$ QA Regression $\rightarrow$ Stakeholder Sign-off.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per project guidelines, formal notes are not taken. The following are synthesized from critical decision threads in the `#proj-umbra-dev` Slack channel.*

### 10.1 Discussion: Billing Logic vs. Performance
**Date:** 2023-11-05
**Participants:** Tariq Kim, Pax Fischer
**Thread Summary:**
- Pax expressed concern that writing to PostgreSQL for every API call would kill performance.
- Tariq suggested using Redis as an intermediate counter.
- **Decision:** Use Redis `INCR` for real-time tracking, then a Celery beat task to sync totals to PostgreSQL every 10 minutes.

### 10.2 Discussion: The "Manual Gate" Turnaround
**Date:** 2023-12-12
**Participants:** Tariq Kim, Mosi Liu
**Thread Summary:**
- Mosi argued that a 1-day turnaround for QA was too aggressive for a "zero-downtime" system.
- Tariq agreed that regression testing for legal models requires deeper verification.
- **Decision:** Official deployment turnaround set to 2 business days.

### 10.3 Discussion: SSO Provider Selection
**Date:** 2024-01-20
**Participants:** Tariq Kim, Mosi Liu, Wes Park
**Thread Summary:**
- Wes noted that several clients use legacy SAML providers that don't support OIDC.
- The team discussed whether to support only OIDC for simplicity.
- **Decision:** Must support both SAML 2.0 and OIDC to avoid losing high-value Enterprise clients.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

### 11.1 Personnel ($310,000)
- **Tariq Kim (Tech Lead):** $120,000 (Architecture, Review, Lead)
- **Pax Fischer (Data Engineer):** $90,000 (Pipeline, DB, Infrastructure)
- **Mosi Liu (QA Lead):** $60,000 (Testing, Audit, Validation)
- **Wes Park (Support Engineer):** $40,000 (Deployment, Client Support)

### 11.2 Infrastructure ($50,000)
- **AWS ECS/Fargate:** $20,000 (Compute)
- **AWS RDS (Postgres) & ElastiCache:** $15,000 (Data)
- **S3 Storage & Data Transfer:** $10,000 (Model storage)
- **Twilio/SendGrid/Firebase:** $5,000 (Communications)

### 11.3 Tools & Licensing ($15,000)
- **IDE Licenses & GitHub Enterprise:** $5,000
- **External Security Audit (Internal prep):** $10,000

### 11.4 Contingency ($25,000)
- **Emergency Buffer:** Reserved for unforeseen regulatory changes or critical bug fixes.

---

## 12. APPENDICES

### Appendix A: ML Model Versioning Policy
To prevent "model drift" and ensure legal reproducibility, Umbra follows a strict semantic versioning system for ML models:
- **Major (X.0.0):** Architecture change (e.g., switching from Random Forest to Transformer). Requires full re-validation of all 10 pilot users.
- **Minor (0.X.0):** Retrained model with new data. Requires a benchmark test against the "Gold Dataset."
- **Patch (0.0.X):** Hyperparameter tuning or weight adjustment. Requires a smoke test.

### Appendix B: Data Migration Strategy (The Vault $\rightarrow$ Umbra)
The migration will follow a **"Parallel Run"** strategy:
1. **Step 1:** The legacy system remains the "System of Record."
2. **Step 2:** All incoming data is mirrored to the Umbra database in real-time.
3. **Step 3:** For 30 days, both systems process the same data. Results are compared.
4. **Step 4:** If results diverge by $>0.1\%$, the migration is paused.
5. **Step 5:** Once parity is confirmed, the DNS is switched to Umbra, and the legacy system is set to read-only for 90 days.