# PROJECT SPECIFICATION DOCUMENT: PROJECT FATHOM
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Classification:** Confidential - Clearpoint Digital Internal  
**Project Lead:** Ren Kim (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Fathom" is a strategic, comprehensive rebuild of Clearpoint Digital’s flagship real-time collaboration tool tailored specifically for the automotive industry. The project is born out of a critical necessity; the current legacy iteration of the tool has received catastrophic user feedback, characterized by systemic stability issues, an intuitive failure in UX, and an inability to scale with the high-density data requirements of modern automotive supply chain management.

Fathom is not merely a feature update but a complete architectural pivot. The goal is to move from a monolithic, fragile system to a robust, event-driven microservices architecture capable of supporting real-time collaboration between automotive OEMs (Original Equipment Manufacturers), Tier 1 suppliers, and logistics partners.

### 1.2 Business Justification
The automotive sector is currently undergoing a digital transformation, moving toward "Industry 4.0" standards. Our clients require real-time visibility into parts procurement, design iterations, and compliance reporting. The failure of the previous version of our tool resulted in a 15% churn rate in Q3. To regain market trust and prevent further attrition, Clearpoint Digital is investing $3M into Fathom.

The business justification rests on three pillars:
1. **Churn Mitigation:** By providing a stable, high-performance tool, we stop the bleeding of existing enterprise contracts.
2. **Market Penetration:** The current gap in the market for a dedicated *automotive-specific* collaboration tool (rather than a general-purpose tool like Jira or Slack) allows Fathom to capture a niche but high-value segment.
3. **Operational Efficiency:** Moving to a self-hosted, microservices-based approach reduces the long-term cost of scaling and allows for strict adherence to data residency laws.

### 1.3 ROI Projection
The financial objective of Fathom is to generate $500,000 in new attributed revenue within the first 12 months of the general release (post-August 2026). 

**Projected ROI Calculation:**
- **Initial Investment:** $3,000,000.
- **Year 1 Revenue Target:** $500,000 (Direct new sales).
- **Indirect Value:** Retention of existing accounts valued at approximately $2.2M in annual recurring revenue (ARR) that were deemed "at risk" due to the legacy system's failures.
- **Break-even Analysis:** While the direct revenue target is $500K, the "hidden" ROI is the protection of the $2.2M ARR. If Fathom prevents a 20% churn of these accounts, the project pays for itself in terms of retained value within 18 months.

### 1.4 Success Metrics
The success of Project Fathom will be measured by:
- **Technical Performance:** API response time (p95) must remain under 200ms during peak loads (defined as 5,000 concurrent users per tenant).
- **Financial Growth:** Attainment of the $500K new revenue target.
- **User Satisfaction:** A Net Promoter Score (NPS) increase from the current -22 to at least +30.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Fathom utilizes a modern, asynchronous stack designed for high throughput and strict data isolation.

- **Backend:** Python 3.11 with FastAPI (Asynchronous Server Gateway Interface).
- **Database:** MongoDB 6.0 (Document-oriented for flexibility in automotive part schemas).
- **Task Queue/Async Processing:** Celery 5.3 with Redis as the broker.
- **Event Streaming:** Apache Kafka 3.5 (For inter-service communication and real-time event sourcing).
- **Containerization:** Docker Compose for orchestration of microservices.
- **Hosting:** Self-hosted on dedicated bare-metal clusters to meet strict EU data residency requirements.

### 2.2 Architectural Pattern: Event-Driven Microservices
Fathom is decoupled into specialized services:
1. **Auth Service:** Manages identity, RBAC, and session tokens.
2. **Document Service:** Handles PDF/CSV generation and metadata.
3. **Notification Service:** Manages the multi-channel alert system.
4. **File Service:** Manages uploads, virus scanning, and CDN integration.
5. **Collaboration Service:** Manages the real-time state of shared documents/dashboards.

### 2.3 System Diagram (ASCII Representation)

```text
[ Client Layer ]  -->  [ Load Balancer / Nginx ]
                               |
                               v
                    [ API Gateway (FastAPI) ]
                               |
      _________________________|_________________________
     |               |                 |                |
[Auth Service] [File Service] [Doc Service] [Notification Service]
     |               |                 |                |
     |               v                 v                v
     |        [ S3 / CDN ]      [ Celery Workers ]  [ SMTP/SMS Gateway ]
     |               ^                 ^                ^
     |               |                 |                |
     |        (Event Stream: Apache Kafka Bus) <---------|
     |               |                 |
     v               v                 v
[ MongoDB Cluster (EU Region - Sharded by TenantID) ]
```

### 2.4 Data Residency and Security
To comply with GDPR and CCPA, Fathom implements a "Regional Silo" strategy. All data for EU customers is stored on physical hardware located within the EU. Data is encrypted at rest using AES-256 and in transit via TLS 1.3.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Not Started

**Description:**
The automotive industry relies heavily on compliance and audit trails. Fathom must provide a robust engine capable of aggregating real-time collaboration data into formal PDF and CSV reports. These reports are used for quality assurance (QA) audits and supply chain snapshots.

**Functional Requirements:**
- **Dynamic Templating:** Users can define report templates using a drag-and-drop interface.
- **Aggregation Engine:** The system must query MongoDB and aggregate data across multiple tenants (if authorized) or single tenants.
- **Scheduling Logic:** A cron-like scheduler integrated with Celery to trigger reports daily, weekly, or monthly.
- **Delivery Channels:** Reports must be delivered via email attachment or uploaded to the internal File Service for retrieval.

**Technical Implementation:**
- Use `ReportLab` for PDF generation and `Pandas` for CSV serialization.
- Reports will be generated as background tasks via Celery to avoid blocking the API.
- **Trigger Flow:** `Schedule Service` $\rightarrow$ `Kafka Topic (report_requested)` $\rightarrow$ `Doc Service` $\rightarrow$ `Celery Worker` $\rightarrow$ `S3 Store` $\rightarrow$ `Notification Service`.

**Acceptance Criteria:**
- Generation of a 100-page PDF report in under 30 seconds.
- 100% delivery success rate for scheduled reports.

---

### 3.2 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** Not Started

**Description:**
Real-time collaboration requires immediate feedback. Fathom needs a centralized notification hub that routes alerts based on user preferences and urgency.

**Functional Requirements:**
- **Multi-Channel Routing:**
    - *In-App:* WebSocket-based alerts for active users.
    - *Email:* Summary digests and critical alerts via SendGrid.
    - *SMS:* High-priority alerts (e.g., production line stoppage) via Twilio.
    - *Push:* Mobile notifications for managers on the go.
- **Preference Center:** Users must be able to toggle specific notification types per channel.
- **Notification Grouping:** To prevent "notification fatigue," similar alerts must be batched.

**Technical Implementation:**
- **Event-Driven Architecture:** The Notification Service listens to a global Kafka topic `system_events`.
- **WebSocket Integration:** FastAPI's `WebSocket` endpoints will push real-time updates to the frontend.
- **Priority Queueing:** Celery queues will be split into `high_priority` (SMS/Push) and `low_priority` (Email digests).

**Acceptance Criteria:**
- In-app notifications delivered within 500ms of the event.
- Ability to mute all notifications for a specific project.

---

### 3.3 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** In Review

**Description:**
Given the sensitivity of automotive blueprints and pricing, a rigorous RBAC system is mandatory. This is the foundation of the security model.

**Functional Requirements:**
- **Identity Management:** JWT-based authentication with short-lived access tokens and long-lived refresh tokens.
- **Role Hierarchy:**
    - *Super Admin:* Full system access, billing, and tenant management.
    - *Org Admin:* Management of users and roles within a specific company.
    - *Editor:* Ability to modify documents and reports.
    - *Viewer:* Read-only access to specific project folders.
- **Session Management:** Ability for Admins to revoke sessions remotely.

**Technical Implementation:**
- **FastAPI Security:** Implementation of `OAuth2PasswordBearer` and custom dependency injections for role verification.
- **Schema:** A dedicated `roles` collection in MongoDB mapping users to permissions (Permission-based access control).
- **Middleware:** A custom FastAPI middleware to validate JWTs and check RBAC permissions before reaching the endpoint logic.

**Acceptance Criteria:**
- Unauthorized users are blocked with a `403 Forbidden` response.
- Token rotation occurs every 15 minutes.

---

### 3.4 Multi-Tenant Data Isolation with Shared Infrastructure
**Priority:** Low (Nice-to-Have) | **Status:** In Design

**Description:**
To optimize costs, Fathom uses a shared infrastructure model, but data must be logically isolated to prevent "leakage" between competing automotive OEMs.

**Functional Requirements:**
- **Logical Isolation:** Every database query must be scoped by a `tenant_id`.
- **Tenant Onboarding:** Automated provisioning of tenant-specific configurations.
- **Shared Resources:** Shared API gateways and Kafka brokers, but isolated database collections or sharded clusters.

**Technical Implementation:**
- **Query Interceptor:** A wrapper around the MongoDB driver that automatically appends `{ "tenant_id": current_user.tenant_id }` to all find/update/delete operations.
- **Sharding:** Using MongoDB's sharding capabilities, where the `tenant_id` serves as the shard key to physically distribute data across nodes.

**Acceptance Criteria:**
- Zero instances of cross-tenant data leakage during penetration testing.
- Ability to migrate a single tenant's data to a dedicated cluster if they upgrade to a "Premium" tier.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Users must upload large CAD files, spreadsheets, and images. Because these files are shared across organizations, a security breach via a malicious file could compromise the entire network.

**Functional Requirements:**
- **Secure Uploads:** Multipart uploads supporting files up to 2GB.
- **Automated Virus Scanning:** All files must be scanned by ClamAV before being marked as "Available."
- **CDN Distribution:** Files are cached globally via a CDN to ensure low-latency access for international teams.
- **Versioning:** Files should maintain a version history to prevent accidental overwrites.

**Technical Implementation:**
- **Workflow:** `FastAPI Upload` $\rightarrow$ `Temporary S3 Bucket` $\rightarrow$ `Celery Trigger` $\rightarrow$ `ClamAV Scanner` $\rightarrow$ `Production S3 Bucket` $\rightarrow$ `CloudFront CDN`.
- **Virus Scanning:** A dedicated Docker container running ClamAV that polls the temporary bucket.
- ** CDN Logic:** Use of signed URLs with a 15-minute expiration to ensure secure access.

**Acceptance Criteria:**
- Files with known malware are quarantined and the user is notified within 10 seconds.
- Upload speed maintains 80% of the user's available bandwidth.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. All requests require a `Authorization: Bearer <JWT>` header.

### 4.1 Auth Service
**1. POST `/auth/login`**
- **Purpose:** Authenticate user and return tokens.
- **Request:** `{"email": "user@clearpoint.com", "password": "securepassword123"}`
- **Response (200):** `{"access_token": "eyJ...", "refresh_token": "def...", "expires_in": 900}`
- **Response (401):** `{"error": "Invalid credentials"}`

**2. POST `/auth/refresh`**
- **Purpose:** Refresh access token using a refresh token.
- **Request:** `{"refresh_token": "def..."}`
- **Response (200):** `{"access_token": "eyJ...", "expires_in": 900}`

### 4.2 File Service
**3. POST `/files/upload`**
- **Purpose:** Initiate a file upload.
- **Request:** Multipart form-data (`file`, `tenant_id`, `project_id`).
- **Response (202):** `{"file_id": "uuid-123", "status": "scanning", "eta": "10s"}`

**4. GET `/files/download/{file_id}`**
- **Purpose:** Get a signed CDN URL for a file.
- **Response (200):** `{"download_url": "https://cdn.fathom.com/get/abc123xyz", "expires_at": "2023-10-24T12:00:00Z"}`

### 4.3 Document Service
**5. POST `/reports/generate`**
- **Purpose:** Manually trigger a report.
- **Request:** `{"template_id": "temp-456", "format": "pdf", "filters": {"date_range": "last_7_days"}}`
- **Response (201):** `{"report_id": "rep-789", "status": "queued"}`

**6. GET `/reports/status/{report_id}`**
- **Purpose:** Check if a scheduled/manual report is finished.
- **Response (200):** `{"status": "completed", "url": "https://cdn.fathom.com/reports/rep-789.pdf"}`

### 4.4 Notification Service
**7. PATCH `/notifications/settings`**
- **Purpose:** Update user alert preferences.
- **Request:** `{"email": true, "sms": false, "push": true, "digest_frequency": "weekly"}`
- **Response (200):** `{"message": "Preferences updated"}`

**8. GET `/notifications/unread`**
- **Purpose:** Fetch all unread in-app notifications.
- **Response (200):** `[{"id": "n1", "msg": "New report available", "timestamp": "..."}, {...}]`

---

## 5. DATABASE SCHEMA

Fathom uses MongoDB. Below are the logical collections (tables) and their relationships.

### 5.1 Collection: `tenants`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `company_name` | String | Legal name of the automotive company |
| `region` | String | EU / US / APAC (Used for data residency) |
| `plan_tier` | String | Basic, Professional, Enterprise |
| `created_at` | DateTime | Timestamp of onboarding |

### 5.2 Collection: `users`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `tenant_id` | ObjectId | FK to `tenants` |
| `email` | String | Unique identifier |
| `password_hash` | String | Argon2 hashed password |
| `full_name` | String | User's legal name |
| `last_login` | DateTime | Tracking for session timeouts |

### 5.3 Collection: `roles`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `role_name` | String | Admin, Editor, Viewer |
| `permissions` | Array | List of strings (e.g., `["file:upload", "report:generate"]`) |

### 5.4 Collection: `user_roles`
| Field | Type | Description |
| :--- | :--- | :--- |
| `user_id` | ObjectId | FK to `users` |
| `role_id` | ObjectId | FK to `roles` |
| `assigned_at` | DateTime | Date role was granted |

### 5.5 Collection: `projects`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `tenant_id` | ObjectId | FK to `tenants` |
| `project_name` | String | Name of the automotive project (e.g., "EV-Chassis-2026") |
| `status` | String | Active, Archived, Planning |

### 5.6 Collection: `files`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `project_id` | ObjectId | FK to `projects` |
| `uploaded_by` | ObjectId | FK to `users` |
| `s3_path` | String | Path to the file in S3 |
| `virus_scan_status` | String | Pending, Clean, Infected |
| `checksum` | String | SHA-256 hash for integrity check |

### 5.7 Collection: `reports`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `tenant_id` | ObjectId | FK to `tenants` |
| `template_id` | ObjectId | FK to `report_templates` |
| `generation_date` | DateTime | When the report was run |
| `delivery_status` | String | Sent, Failed, Pending |

### 5.8 Collection: `report_templates`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `tenant_id` | ObjectId | FK to `tenants` |
| `config_json` | Object | Layout and field mapping |
| `format` | String | PDF or CSV |

### 5.9 Collection: `notifications`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `user_id` | ObjectId | FK to `users` |
| `message` | String | The alert text |
| `is_read` | Boolean | Tracking for in-app notifications |
| `channel` | String | Email, SMS, In-App, Push |

### 5.10 Collection: `audit_logs`
| Field | Type | Description |
| :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key |
| `tenant_id` | ObjectId | FK to `tenants` |
| `user_id` | ObjectId | FK to `users` |
| `action` | String | e.g., "FILE_DOWNLOADED" |
| `timestamp` | DateTime | Exact time of action |
| `ip_address` | String | Source IP for security audits |

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Fathom utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and unit testing.
- **Infrastructure:** Docker Compose on developer machines and a shared "Dev" server.
- **Data:** Mock data; no real customer information.
- **Deployment:** Continuous Integration (CI) trigger on every push to `develop` branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** User Acceptance Testing (UAT) and QA validation.
- **Infrastructure:** Mirror of production (EU-based bare metal).
- **Data:** Anonymized production snapshots.
- **Deployment:** Manual trigger after `develop` $\rightarrow$ `release` merge.

#### 6.1.3 Production (Prod)
- **Purpose:** Customer-facing live environment.
- **Infrastructure:** High-availability cluster across three EU availability zones.
- **Data:** Encrypted, live customer data.
- **Deployment:** Manual QA gate. A release candidate must be signed off by the QA lead. Deployment happens in a 2-day window to allow for rollback if regressions are found.

### 6.2 CI/CD Pipeline
1. **Commit:** Developer pushes code to GitLab.
2. **CI Pipeline:**
    - Linting (Flake8/Black)
    - Unit Tests (Pytest)
    - Security Scan (Bandit)
3. **Build:** Docker image created and pushed to private registry.
4. **Staging Deploy:** Image deployed to Staging for QA.
5. **QA Gate:** QA team validates features.
6. **Prod Deploy:** Orchestrated rollout via Docker Compose / Ansible.

### 6.3 Self-Hosting Requirements
To satisfy the EU data residency requirement, Clearpoint Digital maintains its own hardware. 
- **CPU:** 64-core AMD EPYC processors.
- **RAM:** 512GB ECC RAM.
- **Storage:** NVMe RAID 10 for MongoDB high-IOPS requirements.
- **Network:** Dedicated 10Gbps fiber uplink.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and API endpoints.
- **Tooling:** `Pytest` with `pytest-asyncio`.
- **Requirement:** 80% minimum code coverage.
- **Focus:** Edge cases in RBAC logic, data transformation in the report engine, and input validation in FastAPI.

### 7.2 Integration Testing
- **Scope:** Communication between microservices and databases.
- **Tooling:** Docker Compose to spin up a local Kafka and MongoDB instance.
- **Focus:** 
    - Event propagation: Ensure a file upload trigger correctly initiates a virus scan.
    - Database constraints: Ensure `tenant_id` is present in all queries.
    - API Contract: Validating that the Auth service provides tokens that the Document service accepts.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from login to report download.
- **Tooling:** Playwright / Selenium.
- **Focus:** 
    - User logs in $\rightarrow$ Uploads CAD file $\rightarrow$ Waits for scan $\rightarrow$ Generates report $\rightarrow$ Downloads PDF.
    - Testing the 200ms p95 API response time under simulated load using `Locust.io`.

### 7.4 QA Gate Process
Every deployment to Production requires a signed "QA Pass" document. This includes:
- Smoke test of all critical paths.
- Regression test of the top 5 most used features.
- Verification of GDPR data deletion scripts (Right to be Forgotten).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead in product delivery. | High | High | Hire external contractor to accelerate File Service and Auth development; reduce bus factor. | Ren Kim |
| R-02 | Performance requirements 10x current capacity without budget for more hardware. | Medium | Critical | Assign dedicated performance owner to optimize MongoDB indexing and Kafka partitioning. | Arjun Nakamura |
| R-03 | Legal review of Data Processing Agreement (DPA) is stalled. | Medium | High | Escalation to Clearpoint Legal VP; prepare "lite" version of DPA for early beta customers. | Celine Nakamura |
| R-04 | Technical Debt: Hardcoded configs in 40+ files. | High | Medium | Implement a centralized `ConfigService` using environment variables and `.env` files; refactor in Sprint 2. | Arjun Nakamura |
| R-05 | Data residency breach (EU data leaked to US). | Low | Critical | Implement hard-coded region checks at the DB driver level and automated geography audits. | Ren Kim |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project failure or legal action.
- **High:** Significant delay or revenue loss.
- **Medium:** Manageable via sprint adjustments.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

The project follows an Agile-Waterfall hybrid approach. Development is agile, but milestones are fixed for executive visibility.

### 9.1 Phase 1: Foundation (Oct 2023 - Jan 2024)
- **Focus:** Infrastructure setup, Auth Service, and File Service.
- **Dependencies:** Hardware procurement and legal DPA review.
- **Key Goal:** Establish the secure "plumbing" of the system.

### 9.2 Phase 2: Core Feature Build (Jan 2024 - Apr 2024)
- **Focus:** Report Generation, Notification System, and RBAC refinement.
- **Dependencies:** Successful integration of Kafka event bus.
- **Milestone 1: MVP Feature-Complete (Target: 2026-04-15)**
    - *Note:* Date reflects the long-term stabilization period required for automotive industrial standards.

### 9.3 Phase 3: Hardening and Audit (Apr 2024 - Jun 2024)
- **Focus:** Performance tuning, load testing, and security patching.
- **Dependencies:** Final MVP sign-off.
- **Milestone 2: Security Audit Passed (Target: 2026-06-15)**
    - External third-party penetration test and GDPR compliance certification.

### 9.4 Phase 4: Commercial Launch (Jun 2024 - Aug 2024)
- **Focus:** Beta onboarding and billing integration.
- **Dependencies:** Security audit completion.
- **Milestone 3: First Paying Customer Onboarded (Target: 2026-08-15)**

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment (2023-11-02)
**Attendees:** Ren, Arjun, Hana
- PDFs slow. Need Celery.
- Kafka vs RabbitMQ? Ren says Kafka for event sourcing.
- MongoDB for parts data.
- Hana hates the old UI. New one needs "Dark Mode" for factory floors.
- Action: Arjun to setup Docker Compose base.

### Meeting 2: Security Review (2023-11-16)
**Attendees:** Ren, Arjun, Celine
- DPA still stuck in legal. Blocker.
- Virus scanning: ClamAV.
- Signed URLs for CDN. 15 min expiry.
- Need EU data residency. Bare metal.
- Action: Celine to ping legal again.

### Meeting 3: Performance Crisis (2023-12-05)
**Attendees:** Ren, Arjun
- 10x load req. No more budget for servers.
- Must optimize MongoDB indexes.
- p95 < 200ms.
- Hardcoded configs are a mess (40 files).
- Action: Arjun to start config refactor.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

### 11.1 Personnel ($2,100,000)
- **Engineering Manager (Ren):** $250k / year
- **DevOps Engineer (Arjun):** $180k / year
- **Product Designer (Hana):** $160k / year
- **Support Engineer (Celine):** $130k / year
- **Contractor (Mitigation for R-01):** $200k (Flat fee for accelerated delivery)
- **QA Team (Dedicated):** $300k (External agency)
- **Remaining Personnel Buffer:** $880k (Future hires for scale)

### 11.2 Infrastructure ($450,000)
- **Bare Metal Servers (EU):** $200k (Upfront hardware cost)
- **Data Center Colocation (3 years):** $150k
- **CDN (CloudFront/Akamai):** $50k (Estimated usage)
- **Backup/Disaster Recovery:** $50k

### 11.3 Software & Tools ($150,000)
- **MongoDB Enterprise Licenses:** $80k
- **SaaS Tools (SendGrid, Twilio, GitLab):** $40k
- **Security Auditing Tools:** $30k

### 11.4 Contingency Fund ($300,000)
- **Reserve:** Held for unforeseen hardware failures, emergency contractor surge, or legal fees.

---

## 12. APPENDICES

### Appendix A: Kafka Topic Definitions
To ensure the event-driven architecture remains organized, the following topic naming convention is mandated: `fathom.<service>.<event_type>`.

| Topic Name | Producer | Consumer | Payload Example |
| :--- | :--- | :--- | :--- |
| `fathom.file.upload_complete` | File Service | Notification, Doc | `{"file_id": "123", "tenant": "T1"}` |
| `fathom.file.scan_result` | File Service | File Service (State) | `{"file_id": "123", "result": "clean"}` |
| `fathom.doc.report_ready` | Doc Service | Notification | `{"report_id": "R456", "user_id": "U789"}` |
| `fathom.auth.user_created` | Auth Service | Notification | `{"user_id": "U789", "email": "..."}` |

### Appendix B: Disaster Recovery Plan (DRP)
In the event of a catastrophic failure of the EU data center:
1. **RPO (Recovery Point Objective):** 1 hour. MongoDB OpLogs are mirrored to a secondary "Warm Site" in a separate EU region (e.g., Frankfurt to Ireland).
2. **RTO (Recovery Time Objective):** 4 hours.
3. **Failover Process:** 
    - Update DNS entries to point to the secondary site.
    - Promote the secondary MongoDB member to Primary.
    - Re-initialize Kafka clusters from the latest snapshot.
    - Verify CDN cache consistency.