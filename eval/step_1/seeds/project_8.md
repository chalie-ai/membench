Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. It is structured to serve as the "Single Source of Truth" (SSoT) for the Cornice development team at Duskfall Inc.

***

# PROJECT SPECIFICATION: PROJECT CORNICE
**Document Version:** 1.0.4  
**Status:** Active/Baseline  
**Last Updated:** 2024-10-24  
**Classification:** CONFIDENTIAL – DUSKFALL INC. INTERNAL  
**Project Lead:** Kamau Blackwood-Diallo  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Cornice is a high-risk, high-reward R&D initiative commissioned by Duskfall Inc. within the cybersecurity domain. The project focuses on developing a specialized embedded systems firmware layer designed to interface with legacy industrial controllers while providing modern, cloud-integrated security telemetry. Unlike standard product cycles, Cornice is classified as a "moonshot" project. It aims to bridge the gap between air-gapped hardware and AWS-based analytics, creating a secure "cornice" or edge-boundary that monitors for anomalies in firmware execution.

### 1.2 Business Justification
In the current cybersecurity landscape, Industrial Control Systems (ICS) are increasingly targeted by state-sponsored actors. Most existing solutions are either purely software-based (lacking hardware-level visibility) or purely hardware-based (lacking cloud scalability). Cornice seeks to occupy the middle ground. By deploying a Python/Django-managed control plane that interfaces with embedded C-firmware (via the specified stack), Duskfall Inc. can offer a "Security-as-a-Service" model for critical infrastructure.

The strategic value lies not in immediate market saturation, but in the intellectual property (IP) generated. The ability to perform full-text indexing and faceted search across firmware memory dumps and event logs in real-time represents a significant competitive advantage.

### 1.3 ROI Projection
Given the "moonshot" nature of the project, the ROI is inherently uncertain. However, executive sponsorship remains strong due to the potential for a "winner-take-all" scenario in the ICS security market. 

**Projected Financials:**
- **Initial Investment:** $150,000 (Fixed Budget).
- **Projected Year 1 Revenue (Post-Launch):** $450,000 based on three pilot contracts at $150k each.
- **Break-even Point:** Estimated Q3 2026.
- **Strategic ROI:** Acquisition of 5+ patents related to embedded-to-cloud telemetry and a footprint in the ISO 27001 certified industrial sector.

The project operates on a "shoestring" budget. Every single expenditure is scrutinized by the executive board, requiring the team to prioritize lean development and the use of open-source components where possible.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
The architecture follows a clean monolith approach to minimize overhead for the small 4-person team. While the target is embedded firmware, the management and orchestration layer is a robust web-based system.

- **Language/Framework:** Python 3.11 / Django 4.2 (LTS)
- **Database:** PostgreSQL 15 (Relational data, configuration, and user roles)
- **Caching/Queueing:** Redis 7.0 (Session management, rate limiting, and task queuing)
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless compute
- **Deployment:** GitHub Actions (CI/CD) with Blue-Green deployment strategies to ensure zero-downtime updates.
- **Security Compliance:** The entire environment must be hosted within an ISO 27001 certified VPC, utilizing AWS KMS for encryption at rest and TLS 1.3 for data in transit.

### 2.2 Architecture Diagram (ASCII)
```text
[ Embedded Hardware Layer ] <---(Secure Tunnel/MQTT)---> [ AWS Cloud Infrastructure ]
           |                                                   |
           |                                       ______________________________
           |                                      |      AWS ECS Cluster         |
           |                                      |  [ Django Monolith App ]      |
           |                                      |      |            |           |
           |                                      |      v            v           |
           |                                      | [PostgreSQL]  [ Redis Cache ] |
           |                                      |______|______________|__________|
           |                                                   |
           |                                       [ GitHub Actions CI/CD ]
           |                                                   |
           |                                       [ Blue/Green Deployment ]
           |                                                   |
           |                                       [ ISO 27001 Compliant VPC ]
```

### 2.3 Module Boundaries
To prevent the monolith from becoming "spaghetti code," the following boundaries are strictly enforced:
1. **Core-Firmware-Bridge:** Handles the low-level byte-stream communication with embedded devices.
2. **Analytics-Engine:** Manages the full-text indexing and faceted search logic.
3. **Report-Generator:** A decoupled module for PDF/CSV generation.
4. **Auth-Guard:** Manages RBAC and authentication.
5. **Edge-Gateway:** Handles API rate limiting and usage tracking.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering & Full-Text Indexing
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
The core value proposition of Cornice is the ability to search through millions of firmware event logs and hardware state snapshots. This is not a simple `LIKE %query%` database search; it requires a full-text indexing engine (implemented via PostgreSQL GIN indexes and specialized Django search vectors).

**Functional Requirements:**
- **Full-Text Search:** Users must be able to query natural language strings against logs. The system must support stemming and stop-word removal.
- **Faceted Filtering:** A sidebar must provide dynamic counts of attributes (e.g., "Error Level: Critical (45)", "Device ID: 0x04 (112)"). Filtering must be additive (AND logic).
- **Indexing Pipeline:** As logs arrive from the embedded devices, they must be asynchronously processed by a Celery worker and indexed in the PostgreSQL search vector column.
- **Query Optimization:** Search queries must return results in under 300ms for datasets up to 10 million records.

**Technical Implementation:**
The system will utilize `django.contrib.postgres.search`. A `SearchVectorField` will be added to the `DeviceLog` table. A Redis-backed cache will store the most common facet counts to prevent heavy aggregate queries on every page load.

---

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Blocked (Waiting on Infrastructure)

**Description:**
Enterprise clients require audit-ready reports. Cornice must generate snapshots of system health and security breaches in PDF and CSV formats.

**Functional Requirements:**
- **Customizable Templates:** Users can select which data fields (e.g., timestamps, event IDs, severity) appear in the report.
- **Scheduled Delivery:** Reports can be scheduled (Daily, Weekly, Monthly) via a cron-style scheduler.
- **Asynchronous Processing:** Generation is handled by a background worker to prevent blocking the main request-response cycle.
- **Delivery Mechanism:** Reports are uploaded to an S3 bucket with a time-limited signed URL sent via email.

**Technical Implementation:**
`ReportLab` will be used for PDF generation and Python's `csv` module for spreadsheets. The scheduling logic will be implemented using `django-celery-beat`. The "Blocked" status is due to the delayed AWS S3 bucket provisioning.

---

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
To protect the system from DDoS and ensure fair usage among the small pilot group, a strict rate-limiting layer is required.

**Functional Requirements:**
- **Tiered Limiting:** Different limits based on the API key (e.g., Pilot User: 100 req/min; Admin: Unlimited).
- **Sliding Window Algorithm:** Use a Redis-based sliding window to track requests per second/minute.
- **Analytics Dashboard:** A view for administrators to see which endpoints are most used and which users are hitting limits.
- **Header Feedback:** API responses must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Implementation:**
Implementation using `django-ratelimit` and a custom middleware that intercepts requests. Usage data is stored in a Redis time-series and periodically flushed to PostgreSQL for long-term analytics.

---

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low (Nice to Have) | **Status:** Complete

**Description:**
A standard security layer to ensure only authorized personnel can access the firmware telemetry.

**Functional Requirements:**
- **Authentication:** Session-based login for the dashboard and Token-based authentication (JWT) for the API.
- **Roles:** Three defined roles: `SuperAdmin` (Full access), `Operator` (View and report generation), and `Auditor` (Read-only access to logs).
- **Permission Mapping:** Specific Django permissions mapped to each role (e.g., `can_change_firmware_config`).

**Technical Implementation:**
Utilizes `django.contrib.auth` and `django-rest-framework-simplejwt`. Role mapping is handled via a `UserRole` profile model linked to the standard User model.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** High | **Status:** In Design

**Description:**
Users must be able to upload firmware binary patches for deployment to the embedded devices. Because these files could be malicious, they must be scanned before being distributed.

**Functional Requirements:**
- **Secure Upload:** Files are uploaded to a temporary "quarantine" S3 bucket.
- **Virus Scanning:** Integration with a scanning engine (e.g., ClamAV) to check for known malware signatures.
- **CDN Distribution:** Once cleared, files are moved to a production bucket backed by Amazon CloudFront for global distribution to edge devices.
- **Checksum Validation:** The system must calculate and store a SHA-256 hash to ensure file integrity upon arrival at the device.

**Technical Implementation:**
AWS Lambda triggers a virus scan on S3 `PutObject` events. A Django signal updates the file status to `CLEAN` or `INFECTED` based on the scan result.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and return JSON. Base URL: `https://api.cornice.duskfall.io/v1/`

### 4.1 GET `/search/`
- **Description:** Performs a faceted search across firmware logs.
- **Request Params:** `q` (query string), `facet_level` (filter), `page` (integer).
- **Response Example:**
  ```json
  {
    "results": [{"id": 101, "msg": "Buffer overflow detected", "severity": "critical"}],
    "facets": {"severity": {"critical": 45, "warning": 120}},
    "pagination": {"total": 165, "next": "/search/?page=2"}
  }
  ```

### 4.2 POST `/reports/generate/`
- **Description:** Triggers a report generation task.
- **Request Body:** `{"format": "pdf", "filters": {"start_date": "2025-01-01"}, "email": "user@example.com"}`
- **Response Example:**
  ```json
  {"task_id": "celery-uuid-123", "status": "pending", "eta": "2025-05-20T10:05:00Z"}
  ```

### 4.3 GET `/analytics/usage/`
- **Description:** Retrieves API usage statistics for the authenticated user.
- **Response Example:**
  ```json
  {"user_id": 42, "requests_24h": 15400, "limit_hit_count": 3}
  ```

### 4.4 POST `/auth/login/`
- **Description:** Authenticates user and returns JWT.
- **Request Body:** `{"username": "kblackwood", "password": "secure_password"}`
- **Response Example:**
  ```json
  {"access": "eyJhbG...", "refresh": "eyJhbG..."}
  ```

### 4.5 POST `/firmware/upload/`
- **Description:** Uploads a binary patch for scanning.
- **Request Body:** Multipart form-data (`file`: binary).
- **Response Example:**
  ```json
  {"upload_id": "file-99", "status": "quarantined", "scan_start": "2025-05-20T10:00:01Z"}
  ```

### 4.6 GET `/devices/status/`
- **Description:** Lists all connected embedded devices and their current health.
- **Response Example:**
  ```json
  {"devices": [{"id": "DEV_01", "status": "online", "firmware_ver": "1.0.2"}]}
  ```

### 4.7 PATCH `/devices/{id}/config/`
- **Description:** Updates configuration for a specific embedded device.
- **Request Body:** `{"sampling_rate": "10ms", "logging_level": "DEBUG"}`
- **Response Example:**
  ```json
  {"status": "success", "applied": true}
  ```

### 4.8 GET `/system/health/`
- **Description:** Checks the health of the Django monolith and Redis/Postgres connections.
- **Response Example:**
  ```json
  {"status": "healthy", "database": "connected", "redis": "connected"}
  ```

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL 15. All tables utilize UUIDs as primary keys for security and distributed scalability.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `username` (Varchar, Unique)
    - `password_hash` (Text)
    - `email` (Varchar)
    - `last_login` (Timestamp)

2.  **`roles`**
    - `id` (UUID, PK)
    - `role_name` (Varchar: 'SuperAdmin', 'Operator', 'Auditor')
    - `permissions_json` (JSONB)

3.  **`user_role_map`**
    - `user_id` (FK -> users.id)
    - `role_id` (FK -> roles.id)

4.  **`devices`**
    - `id` (UUID, PK)
    - `hw_serial` (Varchar, Unique)
    - `firmware_version` (Varchar)
    - `ip_address` (Inet)
    - `status` (Varchar: 'online', 'offline', 'error')

5.  **`device_logs`**
    - `id` (UUID, PK)
    - `device_id` (FK -> devices.id)
    - `timestamp` (Timestamp)
    - `message` (Text)
    - `severity` (Int)
    - `search_vector` (TSVector) — *Crucial for faceted search*

6.  **`api_keys`**
    - `id` (UUID, PK)
    - `user_id` (FK -> users.id)
    - `key_hash` (Varchar)
    - `rate_limit_tier` (Varchar)
    - `created_at` (Timestamp)

7.  **`rate_limit_logs`**
    - `id` (UUID, PK)
    - `api_key_id` (FK -> api_keys.id)
    - `endpoint` (Varchar)
    - `timestamp` (Timestamp)
    - `is_blocked` (Boolean)

8.  **`firmware_binaries`**
    - `id` (UUID, PK)
    - `filename` (Varchar)
    - `s3_path` (Varchar)
    - `sha256_hash` (Varchar)
    - `scan_status` (Varchar: 'pending', 'clean', 'infected')

9.  **`reports`**
    - `id` (UUID, PK)
    - `user_id` (FK -> users.id)
    - `report_type` (Varchar)
    - `s3_url` (Varchar)
    - `scheduled_time` (Timestamp)

10. **`system_config`**
    - `id` (UUID, PK)
    - `config_key` (Varchar, Unique)
    - `config_value` (Text)
    - `updated_at` (Timestamp)

### 5.2 Relationships
- **One-to-Many:** `users` $\rightarrow$ `api_keys`
- **One-to-Many:** `devices` $\rightarrow$ `device_logs`
- **Many-to-Many:** `users` $\leftrightarrow$ `roles` (via `user_role_map`)
- **One-to-Many:** `users` $\rightarrow$ `reports`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To ensure stability, the project utilizes three isolated environments.

#### 6.1.1 Development (DEV)
- **Purpose:** Local testing and feature development.
- **Infrastructure:** Docker Compose mirroring the production stack (Postgres/Redis/Django).
- **Database:** Seeded with mock firmware data.
- **CI/CD:** Automatic deployment to DEV on every push to a `feature/*` branch.

#### 6.1.2 Staging (STG)
- **Purpose:** Pre-production validation and QA testing.
- **Infrastructure:** AWS ECS Fargate (Single small instance).
- **Database:** A sanitized clone of production data.
- **CI/CD:** Deployed upon merge to the `develop` branch. This environment is used for the "Internal Alpha" milestone.

#### 6.1.3 Production (PROD)
- **Purpose:** Live customer operations.
- **Infrastructure:** AWS ECS Fargate (Auto-scaling cluster).
- **Deployment:** Blue-Green deployment. The "Green" environment is spun up and tested via a health-check endpoint before the Load Balancer switches traffic from "Blue."
- **Security:** ISO 27001 compliance. All traffic routed through an AWS Application Load Balancer (ALB) with WAF (Web Application Firewall) enabled.

### 6.2 Infrastructure Provisioning (The Current Blocker)
As noted in the risk register, infrastructure provisioning is currently delayed. The team is unable to spin up the STG and PROD VPCs due to a pending quota increase and account verification from the cloud provider. This blocks the "Report Generation" feature, which depends on S3.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, Django models, and utility logic.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** Minimum 80% code coverage. All new PRs must maintain or increase this coverage.
- **Frequency:** Run on every local commit and every GitHub Action trigger.

### 7.2 Integration Testing
- **Scope:** Interaction between Django, PostgreSQL, and Redis.
- **Approach:** Using `TestContainers` to spin up actual database instances during the test phase to avoid "mocking the database."
- **Key Focus:** Verifying that the faceted search indexing pipeline correctly transforms raw logs into `TSVector` entries.

### 7.3 End-to-End (E2E) Testing
- **Scope:** User journeys (e.g., Login $\rightarrow$ Search $\rightarrow$ Generate Report).
- **Tooling:** Playwright or Selenium.
- **Approach:** Automated scripts that run against the Staging environment.
- **Frequency:** Run once per day (Nightly builds).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect leaving in 3 months | High | Critical | **Parallel-Pathing:** Prototype an alternative architecture simultaneously. Cross-train Hessa Kowalski-Nair on all architectural decisions. |
| **R-02** | Integration partner's API is buggy/undocumented | High | Medium | **Dedicated Owner:** Assign one developer to act as the "Integration Liaison" to document the API via trial-and-error and maintain a separate Wiki of quirks. |
| **R-03** | Budget exhaustion ($150k limit) | Medium | High | **Strict Scrutiny:** Monthly budget audits. Avoid premium AWS services; stick to Fargate and managed Postgres. |
| **R-04** | Infrastructure provisioning delay | Medium | High | **Local Simulation:** Use Docker-Compose to simulate S3 and ECS locally so development does not halt. |
| **R-05** | Failure to meet p95 latency (<200ms) | Low | Medium | **Redis Optimization:** Implement aggressive caching for faceted search results. |

**Impact Matrix:**
- **Low:** Minor delay, no budget impact.
- **Medium:** Feature delay, manageable budget shift.
- **High:** Milestone missed, significant budget risk.
- **Critical:** Project failure/Cancellation.

---

## 9. TIMELINE AND MILESTONES

The project is divided into four phases. Dependencies are strictly managed via JIRA.

### Phase 1: Core Foundation (Jan 2025 – May 2025)
- **Focus:** RBAC, API Rate Limiting, and Basic Search.
- **Dependency:** Successful AWS account provisioning.
- **Milestone 1:** **First paying customer onboarded (Target: 2025-05-15).**

### Phase 2: Analytics & Reporting (May 2025 – July 2025)
- **Focus:** Full-text indexing, Faceted filters, PDF/CSV generation.
- **Dependency:** Resolution of R-02 (Integration API).
- **Milestone 2:** **Stakeholder demo and sign-off (Target: 2025-07-15).**

### Phase 3: Security & Distribution (July 2025 – Sept 2025)
- **Focus:** Virus scanning, CDN distribution, Firmware upload.
- **Dependency:** Completion of Phase 2.
- **Milestone 3:** **Internal alpha release (Target: 2025-09-15).**

### Phase 4: Optimization & Hardening (Sept 2025 – Dec 2025)
- **Focus:** p95 latency tuning, ISO 27001 audit, Final bug scrubbing.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom/Teams. Due to the team's culture, these recordings are rarely re-watched; however, the following summaries are extracted from the transcripts.*

### Meeting 1: Project Kickoff (2024-11-01)
- **Attendees:** Kamau Blackwood-Diallo, Hessa Kowalski-Nair, Nadira Vasquez-Okafor, Nyla Blackwood-Diallo (Remote from Gothenburg).
- **Discussion:** Kamau emphasized the "shoestring" nature of the $150k budget. Nyla (Consultant) suggested that the clean monolith is the only way to survive with 4 people; microservices would be "architectural suicide" given the team size.
- **Decision:** Confirmed Django/Postgres stack. Agreed that all communication must be tracked in JIRA to maintain formality.

### Meeting 2: Architecture Review & Risk Assessment (2024-12-15)
- **Attendees:** Kamau, Hessa, Nadira.
- **Discussion:** Hessa raised concerns about the integration partner's API, noting that the documentation is effectively non-existent and the endpoints return inconsistent JSON. Nadira pointed out that the virus scanning requirement for firmware uploads will be a bottleneck.
- **Decision:** Assigned Hessa as the dedicated owner for the buggy API. Decided to use a "Parallel-Path" strategy for the architecture to mitigate the risk of the lead architect's departure.

### Meeting 3: Infrastructure Crisis Sync (2025-02-10)
- **Attendees:** Kamau, Hessa, Nadira, Nyla.
- **Discussion:** The cloud provider has delayed the provisioning of the ISO 27001 VPC. Report generation is now officially "Blocked." Kamau mentioned that his lighthouse duties are becoming more automated, allowing him more time to push the cloud provider.
- **Decision:** Team will pivot to local Docker simulations of S3 and ECS to keep the "Report Generation" logic moving forward until the cloud provider resolves the issue.

---

## 11. BUDGET BREAKDOWN

The total budget is capped at **$150,000.00**.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $97,500 | Small team (4); includes Nyla's consultancy fees. |
| **Infrastructure** | 20% | $30,000 | AWS ECS, RDS, S3, CloudFront (Estimated for 1 year). |
| **Tools/Licenses** | 5% | $7,500 | GitHub Enterprise, JIRA, Virus scanning API. |
| **Contingency** | 10% | $15,000 | Reserved for emergency API overrides or hardware failure. |
| **Total** | **100%** | **$150,000** | **Fixed Cap** |

*Every expense over $500 requires written approval from Kamau Blackwood-Diallo and the executive sponsor.*

---

## 12. APPENDICES

### Appendix A: Faceted Search Logic Detail
The faceted search is implemented using a combination of PostgreSQL `tsvector` and `tsquery`. 
1. **Preprocessing:** Every log entry is processed: `search_vector = to_tsvector('english', message)`.
2. **Querying:** A user query `q="buffer overflow"` is converted to a `tsquery` using the `plainto_tsquery` function.
3. **Faceting:** The system runs a `GROUP BY` on the `severity` and `device_id` columns for all records that match the search vector, returning a count of each.
4. **Complexity:** $O(log N)$ for search retrieval and $O(K)$ for facet aggregation where $K$ is the number of unique categories.

### Appendix B: Blue-Green Deployment Workflow
To maintain an ISO 27001 compliant environment, the following deployment flow is used:
1. **Build:** GitHub Action builds the Docker image and pushes it to AWS ECR.
2. **Provision:** ECS spins up a "Green" task set with the new image.
3. **Health Check:** A specialized endpoint `/health/deep` is polled. It checks DB connectivity and Redis latency.
4. **Cutover:** If the health check passes, the AWS ALB shifts 10% $\rightarrow$ 50% $\rightarrow$ 100% of traffic to the Green environment.
5. **Rollback:** If any 5xx errors spike above 1% during the shift, the ALB immediately reverts to the "Blue" environment.