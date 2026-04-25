# PROJECT SPECIFICATION: PROJECT RAMPART
**Document Version:** 1.2.0  
**Status:** Baseline  
**Last Updated:** October 24, 2023  
**Owner:** Noor Fischer (Tech Lead)  
**Classification:** Internal - Bellweather Technologies  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Rampart is a mission-critical supply chain management system developed for Bellweather Technologies, specifically tailored for the high-stakes environment of legal services. What began as a rapid-prototype hackathon project has evolved into a vital internal productivity tool, currently supporting 500 daily active users (DAU). In the legal services industry, supply chain management involves the orchestration of expert witnesses, specialized legal researchers, document forensic services, and third-party consultants. The lack of a centralized, audited system has historically led to fragmented communication, manual tracking in spreadsheets, and significant leakage in procurement efficiency.

Rampart transforms these manual workflows into a digitized, event-driven pipeline. By automating the lifecycle of a legal service request—from requisition and vendor selection to billing and delivery—Bellweather Technologies can scale its operations without a linear increase in administrative overhead. The system is designed to handle sensitive legal data, necessitating a robust architecture that ensures auditability and integrity.

### 1.2 ROI Projection and Financial Impact
With a budget allocation exceeding $5,000,000, Rampart is designated as a flagship initiative with direct reporting lines to the Board of Directors. The investment is predicated on two primary financial drivers: efficiency gains and revenue growth.

**Operational Efficiency:** 
The primary objective is a 50% reduction in manual processing time. Currently, procurement for a single complex litigation case involves approximately 40 hours of manual coordination across three departments. By automating vendor matching and billing, Rampart aims to reduce this to 20 hours. Across 500 users and thousands of cases annually, this represents a massive recapture of billable hours.

**Revenue Generation:** 
The project is projected to generate $500,000 in new revenue within the first 12 months post-launch. This will be achieved through the introduction of the customer-facing API, allowing external law firms and partners to integrate their procurement systems directly with Bellweather’s infrastructure, thereby creating a new "Platform-as-a-Service" (PaaS) revenue stream for the company.

### 1.3 Strategic Alignment
Rampart aligns with Bellweather’s strategic goal of "Digital Dominance in Legal Ops." By transitioning from a reactive, manual supply chain to a proactive, API-driven ecosystem, the company positions itself as the primary infrastructure provider for legal supply chains. The project's success is tied to the delivery of five core features that transition the tool from a "utility" to a "platform."

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
The system is built on a modern, scalable stack designed for high availability and strict data consistency:
- **Language/Framework:** Python 3.11 / Django 4.2 (utilizing Django REST Framework for API layers).
- **Primary Database:** PostgreSQL 15 (Relational data, ACID compliance).
- **Caching/Message Broker:** Redis 7.0 (Distributed caching, Celery task queue, and session management).
- **Deployment:** AWS ECS (Elastic Container Service) using Fargate for serverless compute scaling.
- **Storage:** AWS S3 for document storage, integrated with CloudFront for CDN distribution.

### 2.2 Architectural Pattern: CQRS and Event Sourcing
Due to the "audit-critical" nature of legal supply chains, Rampart employs Command Query Responsibility Segregation (CQRS) combined with Event Sourcing for specific domains (e.g., Billing and Document Custody).

- **Command Side:** Handles updates to the state. Every change is recorded as an immutable event in an `EventStore` table.
- **Query Side:** Optimized read-models (materialized views in PostgreSQL) that project the current state from the event stream.
- **Benefit:** This ensures a perfect audit trail. If a billing dispute arises, the system can "replay" every event that led to the final invoice amount, providing a forensic level of transparency required by legal regulators.

### 2.3 System Topology (ASCII Diagram Description)
The architecture follows a layered approach:

```text
[ Client Layer ]  --> [ CDN / CloudFront ] --> [ AWS ALB (Load Balancer) ]
                                                        |
                                                        v
[ API Layer ]     --> [ Django Application (ECS Fargate) ] <--> [ Redis Cache ]
                                       |                        |
                                       v                        v
[ Data Layer ]     --> [ PostgreSQL (Primary/Read Replicas) ] [ S3 Buckets ]
                                       |
                                       v
[ Event Store ]    --> [ Immutable Event Log (PostgreSQL) ] --> [ Materialized Views ]
```

**Diagram Narrative:**
1. Users interact via a Web UI or API.
2. Requests are routed through CloudFront (for static assets/files) and an Application Load Balancer (ALB).
3. The Django app processes the request. For high-frequency reads, it hits Redis.
4. Write operations (Commands) are written to the Event Store.
5. Background workers (Celery) process these events to update the Read-Models in PostgreSQL.
6. Files are streamed directly from S3 via signed URLs to ensure security.

### 2.4 Deployment Cycle
Rampart follows a **Quarterly Release Cycle**. Because the system operates within the legal industry, any major change requires a regulatory review period to ensure compliance with internal data handling policies.
- **Dev Environment:** Continuous deployment for feature branches.
- **Staging Environment:** Monthly freezes; mirrored production data (anonymized).
- **Production Environment:** Quarterly pushes, following a 2-week "burn-in" period in staging.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical | **Status:** Blocked | **Requirement ID:** FEAT-001

**Detailed Description:**
The system must support the upload of large-scale legal dossiers, evidence files, and contracts. Given the risk of malware in legal discovery, every upload must undergo a multi-stage scanning process before being accessible to other users.

**Functional Requirements:**
- **Upload Pipeline:** Files are uploaded to an "Ingestion" S3 bucket. A S3 Event Trigger invokes a Lambda function that sends the file to an antivirus engine (ClamAV).
- **Scanning Logic:** If a virus is detected, the file is quarantined, the upload is marked as "Failed," and the security team (Xiomara Park) is notified via an automated alert.
- **CDN Distribution:** Once cleared, the file is moved to the "Production" S3 bucket. Access is granted via CloudFront using Signed URLs with a maximum TTL of 15 minutes.
- **Integrity Checks:** The system must calculate and store a SHA-256 checksum of every file upon upload to ensure no tampering occurs during storage.

**Technical Constraints:**
- Maximum file size: 2GB.
- Throughput: Support for 10 concurrent uploads per user.
- Blockers: Current failure in the ClamAV Lambda integration causing timeouts on files > 50MB.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** Complete | **Requirement ID:** FEAT-002

**Detailed Description:**
To protect the system from abusive patterns and to provide data for the billing module, a sophisticated rate-limiting and telemetry system has been implemented.

**Functional Requirements:**
- **Tiered Limiting:** Rate limits are applied based on the user's role (Admin, Power User, Standard User).
- **Sliding Window Algorithm:** Implemented via Redis to track requests per minute (RPM).
- **Analytics Pipeline:** Every API call is logged to a Redis stream, which is then aggregated hourly into the `ApiUsageAnalytics` table.
- **Headers:** The API returns `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

**Implementation Details:**
The system uses a Django middleware that intercepts requests before they hit the view. If the Redis counter exceeds the threshold, a `429 Too Many Requests` response is returned. The analytics dashboard allows admins to see "Top 10 most active API keys" and "Peak usage hours."

### 3.3 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Design | **Requirement ID:** FEAT-003

**Detailed Description:**
To achieve the $500K revenue goal, Rampart must transition from an internal tool to a platform. This requires a public-facing API that external partners can use to submit service requests.

**Functional Requirements:**
- **API Versioning:** Use URI versioning (e.g., `/api/v1/...`). Version transitions must be supported for 12 months.
- **Sandbox Environment:** A completely isolated environment where partners can test their integrations against mock data without affecting production.
- **Authentication:** Implementation of OAuth2 with Client Credentials flow.
- **Developer Portal:** A basic documentation page (Swagger/OpenAPI 3.0) providing interactive endpoints for testing.

**Design Specifications:**
The sandbox will utilize a separate PostgreSQL schema (`sandbox_schema`) and a separate Redis instance to prevent cross-contamination. The API will expose a subset of the internal functionality, specifically the `RequestSubmission` and `StatusTracking` modules.

### 3.4 Automated Billing and Subscription Management
**Priority:** Critical | **Status:** In Design | **Requirement ID:** FEAT-004

**Detailed Description:**
A launch-blocking feature that converts usage data into invoices. This module must integrate with the internal finance system of Bellweather Technologies.

**Functional Requirements:**
- **Metered Billing:** Charges are based on the number of files processed and the number of API calls made (linking back to FEAT-002).
- **Subscription Tiers:** Support for "Flat Fee," "Per User," and "Usage-Based" pricing models.
- **Invoice Generation:** Monthly automated generation of PDF invoices stored in S3.
- **Payment Gateway:** Integration with a corporate payment rail (ACH/Wire) for automated settlement.

**Technical Design:**
The billing engine will run as a nightly Celery task. It will aggregate records from the `ApiUsageAnalytics` table and calculate totals based on the `PricingPlan` model. Because billing is audit-critical, it will use the CQRS Event Store to ensure that every change in a subscription's status is logged.

### 3.5 Offline-First Mode with Background Sync
**Priority:** High | **Status:** In Progress | **Requirement ID:** FEAT-005

**Detailed Description:**
Legal professionals often work in "dead zones" (courtrooms, secure archives). Rampart must allow users to continue drafting requests and managing their queue without an active internet connection.

**Functional Requirements:**
- **Local Persistence:** Use IndexedDB in the browser to store pending changes.
- **Conflict Resolution:** Use a "Last Write Wins" (LWW) strategy by default, with an option for "Manual Merge" for critical document edits.
- **Background Sync:** Utilize Service Workers to detect when connectivity is restored and push queued changes to the server.
- **State Indicator:** A UI element showing "Syncing...", "Synced", or "Offline - Changes Pending."

**Current Implementation Status:**
The frontend team has implemented the IndexedDB layer. The "Sync Engine" is currently being developed to handle the reconciliation of timestamps between the local client and the PostgreSQL server.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and return JSON. Base URL: `https://api.rampart.bellweather.tech/`

### 4.1 POST `/api/v1/files/upload`
- **Description:** Uploads a file for virus scanning and storage.
- **Request:** `multipart/form-data` { `file`: Binary, `category`: String }
- **Response (202 Accepted):**
  ```json
  {
    "upload_id": "up_98765",
    "status": "scanning",
    "checksum": "e3b0c442...",
    "estimated_completion": "2023-10-24T14:05:00Z"
  }
  ```

### 4.2 GET `/api/v1/files/download/{file_id}`
- **Description:** Generates a signed CDN URL for file retrieval.
- **Request:** Header `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "url": "https://cdn.rampart.tech/download/a7b8c9...",
    "expires_at": "2023-10-24T14:20:00Z"
  }
  ```

### 4.3 GET `/api/v1/analytics/usage`
- **Description:** Returns API usage statistics for the current billing cycle.
- **Request:** Query params `?start_date=...&end_date=...`
- **Response (200 OK):**
  ```json
  {
    "total_requests": 45000,
    "rate_limit_hits": 120,
    "avg_response_time_ms": 145
  }
  ```

### 4.4 POST `/api/v1/billing/subscriptions`
- **Description:** Create a new subscription for a customer account.
- **Request:** `{ "customer_id": "cust_123", "plan_id": "plan_gold" }`
- **Response (201 Created):**
  ```json
  {
    "subscription_id": "sub_5544",
    "status": "active",
    "next_billing_date": "2023-11-01"
  }
  ```

### 4.5 GET `/api/v1/requests/{request_id}`
- **Description:** Retrieve the status of a legal supply chain request.
- **Response (200 OK):**
  ```json
  {
    "id": "req_001",
    "status": "in_progress",
    "vendor": "Forensics Inc",
    "updated_at": "2023-10-24T10:00:00Z"
  }
  ```

### 4.6 PUT `/api/v1/requests/{request_id}`
- **Description:** Update a request (used by the offline sync engine).
- **Request:** `{ "status": "completed", "last_updated_client": "2023-10-24T11:00:00Z" }`
- **Response (200 OK):** `{ "status": "updated", "version": 4 }`

### 4.7 GET `/api/v1/sandbox/status`
- **Description:** Check if the current environment is the Sandbox or Production.
- **Response (200 OK):** `{ "environment": "sandbox", "version": "1.2.0-beta" }`

### 4.8 DELETE `/api/v1/files/{file_id}`
- **Description:** Trigger a soft-delete of a file and its associated CDN cache.
- **Response (204 No Content):** (Empty body)

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions
The system uses a PostgreSQL database. Below are the core tables.

1. **`Users`**
   - `user_id` (UUID, PK)
   - `email` (Varchar, Unique)
   - `role` (Enum: Admin, User, Contractor)
   - `created_at` (Timestamp)

2. **`Accounts`**
   - `account_id` (UUID, PK)
   - `company_name` (Varchar)
   - `billing_address` (Text)
   - `owner_id` (FK -> Users.user_id)

3. **`Subscriptions`**
   - `subscription_id` (UUID, PK)
   - `account_id` (FK -> Accounts.account_id)
   - `plan_id` (Varchar)
   - `status` (Enum: Active, Past Due, Canceled)
   - `start_date` (Timestamp)

4. **`PricingPlans`**
   - `plan_id` (Varchar, PK)
   - `monthly_cost` (Decimal)
   - `api_limit_rpm` (Integer)
   - `storage_limit_gb` (Integer)

5. **`SupplyRequests`**
   - `request_id` (UUID, PK)
   - `account_id` (FK -> Accounts.account_id)
   - `status` (Varchar)
   - `priority` (Integer)
   - `created_at` (Timestamp)

6. **`Vendors`**
   - `vendor_id` (UUID, PK)
   - `vendor_name` (Varchar)
   - `specialty` (Varchar)
   - `rating` (Decimal)

7. **`Documents`**
   - `doc_id` (UUID, PK)
   - `request_id` (FK -> SupplyRequests.request_id)
   - `s3_key` (Varchar)
   - `sha256_checksum` (Varchar)
   - `is_scanned` (Boolean)

8. **`ApiUsageAnalytics`**
   - `log_id` (BigInt, PK)
   - `user_id` (FK -> Users.user_id)
   - `endpoint` (Varchar)
   - `timestamp` (Timestamp)
   - `response_code` (Integer)

9. **`EventStore`** (The heart of the CQRS system)
   - `event_id` (BigInt, PK)
   - `aggregate_id` (UUID) - e.g., Request ID or Account ID
   - `event_type` (Varchar) - e.g., "BillingCycleStarted"
   - `payload` (JSONB) - The state change data
   - `created_at` (Timestamp)

10. **`AuditLogs`**
    - `audit_id` (BigInt, PK)
    - `user_id` (FK -> Users.user_id)
    - `action` (Varchar)
    - `ip_address` (Varchar)
    - `timestamp` (Timestamp)

### 5.2 Relationships
- **One-to-Many:** `Users` $\rightarrow$ `Accounts` (One user can manage multiple accounts).
- **One-to-Many:** `Accounts` $\rightarrow$ `Subscriptions` (An account has a history of subscriptions).
- **One-to-Many:** `Accounts` $\rightarrow$ `SupplyRequests` (Accounts initiate requests).
- **One-to-Many:** `SupplyRequests` $\rightarrow$ `Documents` (A request can have multiple evidence files).
- **Many-to-One:** `ApiUsageAnalytics` $\rightarrow$ `Users` (Tracking usage per user).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Rampart utilizes three distinct AWS-backed environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature experimentation and unit testing.
- **Infrastructure:** Small ECS Fargate clusters, shared PostgreSQL instance with separate databases per feature branch.
- **Deployment:** Triggered on every push to `develop` or feature branches via GitHub Actions.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation, QA, and Regulatory Review.
- **Infrastructure:** Mirrored production specs (Medium Fargate clusters, RDS Multi-AZ).
- **Data:** Scrubbed production snapshots are imported monthly.
- **Deployment:** Manual trigger upon completion of a sprint; requires sign-off from Noor Fischer.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user traffic.
- **Infrastructure:** Large Fargate clusters with Auto-scaling, RDS Aurora PostgreSQL with Read Replicas, Redis ElastiCache.
- **Deployment:** Quarterly releases. Uses a Blue/Green deployment strategy to ensure zero downtime.

### 6.2 Infrastructure Components
- **CI/CD Pipeline:** GitHub Actions $\rightarrow$ AWS ECR (Container Registry) $\rightarrow$ AWS ECS.
- **Monitoring:** AWS CloudWatch for logs and metrics, Sentry for real-time error tracking.
- **Networking:** VPC with private subnets for the database and Redis; public subnets for the ALB.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, Django models, and utility classes.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** 80% code coverage for all new features.
- **Frequency:** Run on every commit via CI pipeline.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between Django and PostgreSQL, Redis, and S3.
- **Strategy:** Use "Test Containers" to spin up a real PostgreSQL and Redis instance during the test run to avoid mocking database behavior.
- **Focus:** Validating the Event Sourcing flow (ensuring events in `EventStore` correctly update the Read-Models).

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Upload File $\rightarrow$ Scan $\rightarrow$ Assign to Request $\rightarrow$ Bill").
- **Tooling:** Playwright.
- **Frequency:** Executed weekly in the Staging environment.
- **Success Metric:** Zero regressions in "Critical" priority features.

### 7.4 Security Testing
- **Scope:** Internal security audit focused on IDOR (Insecure Direct Object Reference) and SQL Injection.
- **Lead:** Xiomara Park.
- **Cycle:** Performed once per quarter before the production release.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-001 | Integration partner API is undocumented/buggy | High | High | Hire a contractor (Wyatt Park) to specialize in reverse-engineering the API and build a wrapper. | Noor Fischer |
| R-002 | Regulatory requirements change mid-cycle | Medium | High | Assign a dedicated "Regulatory Owner" to track law changes and update specs weekly. | Project Lead |
| R-003 | Technical debt: Hardcoded configs in 40+ files | High | Medium | Implement a `config.py` using `python-decouple` and migrate values to AWS Secrets Manager. | Hessa Stein |
| R-004 | Virus scanner (ClamAV) latency causing timeouts | Medium | Medium | Implement an asynchronous "polling" pattern instead of a synchronous wait. | Xiomara Park |

**Probability/Impact Matrix:**
- **Critical:** High Prob / High Impact (R-001) $\rightarrow$ Immediate Action.
- **High:** Medium Prob / High Impact (R-002) $\rightarrow$ Close Monitoring.
- **Medium:** High Prob / Medium Impact (R-003) $\rightarrow$ Scheduled Refactor.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Infrastructure & Security (Now - Aug 2026):** Focus on the virus scanning blocker and the internal security audit.
- **Phase 2: Feature Completion (Aug 2026 - Oct 2026):** Finalizing the Billing module and the Offline-first sync engine.
- **Phase 3: Validation & Launch (Oct 2026 - Dec 2026):** Stakeholder demos, final regulatory sign-off, and board reporting.

### 9.2 Gantt-Chart Logic
- **Milestone 1: Security Audit Passed**
  - Target: 2026-08-15
  - Dependency: FEAT-001 (Virus Scanning) must be "Complete."
- **Milestone 2: MVP Feature-Complete**
  - Target: 2026-10-15
  - Dependency: FEAT-004 (Billing) and FEAT-005 (Offline Sync) must be "Complete."
- **Milestone 3: Stakeholder Demo and Sign-off**
  - Target: 2026-12-15
  - Dependency: Milestone 2 and successful E2E testing of all 5 priority features.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-05)
- **Attendees:** Noor, Hessa, Xiomara.
- **Notes:**
  - Event sourcing too slow for some queries.
  - Use materialized views.
  - Redis for rate limiting is working.
  - Need to fix hardcoded API keys in `settings.py`.

### Meeting 2: Partner API Crisis (2023-11-19)
- **Attendees:** Noor, Wyatt.
- **Notes:**
  - Partner API returning 500s randomly.
  - No documentation for the `/v2/submit` endpoint.
  - Wyatt to try packet sniffing.
  - Contractor budget approved to extend Wyatt's term.

### Meeting 3: Billing Design Review (2023-12-02)
- **Attendees:** Noor, Hessa, Board Rep.
- **Notes:**
  - Board wants "Tiered" pricing.
  - Must support ACH payments.
  - Billing is a launch blocker.
  - Hessa to draft schema for `Subscriptions` table.

---

## 11. BUDGET BREAKDOWN

**Total Project Budget:** $5,000,000+

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | Salaries for 20+ staff (Tech Lead, Backend, Security, QA, Project Mgr). |
| **Contractors** | $450,000 | Specialized API integration (Wyatt Park) and external consultants. |
| **AWS Infrastructure** | $800,000 | ECS, RDS, S3, CloudFront, and ElastiCache (3-year projection). |
| **Tools & Licensing** | $150,000 | Sentry, GitHub Enterprise, IDE licenses, and Antivirus engines. |
| **Contingency** | $400,000 | Buffer for regulatory shifts and emergency scaling. |

---

## 12. APPENDICES

### Appendix A: Event Sourcing Transition Logic
To move from the `EventStore` to the `SupplyRequest` Read-Model, the system uses the following projection logic:
1. Fetch all events for `aggregate_id` sorted by `created_at`.
2. Initialize a blank `SupplyRequest` object.
3. For each event:
   - If `RequestCreated` $\rightarrow$ Set initial status and account.
   - If `StatusChanged` $\rightarrow$ Update `status` field.
   - If `DocumentAttached` $\rightarrow$ Append `doc_id` to list.
4. Save the resulting object to the `SupplyRequests` table.

### Appendix B: Hardcoded Config Migration Plan
The project currently contains hardcoded values in 40+ files. The migration will occur as follows:
1. **Inventory:** Use `grep` to identify all strings matching pattern `CONST_` or `API_KEY_`.
2. **Centralization:** Move all values to a `.env` file (local) and AWS Secrets Manager (prod).
3. **Refactor:** Replace `settings.API_KEY = "xyz"` with `settings.API_KEY = os.getenv("API_KEY")`.
4. **Validation:** Run a full regression suite to ensure no environment-specific configs were missed.