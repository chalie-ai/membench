Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Technical Specification Document (TSD). It expands on every provided detail with industrial-grade specifics, including exact API paths, database types, and corporate logic.

***

# PROJECT SPECIFICATION: PROJECT SENTINEL
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Date:** October 24, 2023  
**Company:** Pivot North Engineering  
**Classification:** Confidential – Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Sentinel" represents the complete strategic rebuild of the Pivot North Engineering educational Learning Management System (LMS). The project is necessitated by catastrophic user feedback regarding the legacy system, which suffers from systemic instability, poor UI/UX, and an inability to scale to the demands of the legal services industry. The legal sector requires a level of precision, auditability, and security that the current iteration fails to provide.

Sentinel is designed to transition the platform from a fragile legacy tool into a robust, enterprise-grade LMS capable of supporting high-stakes legal certification and ongoing professional development. The primary objective is to replace the existing codebase with a modernized Python/Django architecture that ensures stability, role-based security, and scalable workflow automation.

### 1.2 Business Justification
The current system's failure has led to a measurable churn in client retention and a stagnation in new lead conversions. In the legal services industry, "educational" tools are not merely for learning; they are often tied to compliance and regulatory mandates. The inability of the current platform to provide reliable audit trails and consistent user experiences has created a liability for Pivot North Engineering.

The rebuild is not merely a feature update but a survival necessity. By implementing a three-tier architecture and a rigorous quarterly release cycle, Sentinel will align the product's deployment with the legal industry's regulatory review cycles, ensuring that all new features are compliant before they hit production.

### 1.3 ROI Projection and Success Metrics
Despite the project being unfunded (bootstrapping using existing team capacity), the projected Return on Investment (ROI) is substantial. The company aims to leverage existing payroll to create a high-value asset without additional capital expenditure.

**Metric 1: User Adoption**
The target is 10,000 Monthly Active Users (MAU) within six months of the official launch. This growth will be driven by the removal of current friction points in the user experience and the introduction of the visual rule builder.

**Metric 2: Revenue Generation**
The project is projected to attribute $500,000 in new revenue within 12 months post-launch. This revenue will be derived from three streams:
1. New enterprise legal contracts attracted by the improved stability.
2. Upselling existing clients to a "Premium Compliance" tier powered by the new audit trail logging.
3. Reduction in churn-related losses (estimated at $120k/year).

The ROI is calculated as: $\text{ROI} = \frac{(\text{New Revenue} - \text{Internal Labor Cost})}{\text{Internal Labor Cost}}$. Given that the team is already on payroll, the "cost" is measured in opportunity cost, which is outweighed by the existential risk of remaining on the legacy platform.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Sentinel utilizes a traditional three-tier architecture. This separation ensures that the presentation layer remains decoupled from the business logic, allowing for faster frontend iterations by Callum Stein without risking the integrity of the data layer managed by Orla Stein.

**Tiers:**
1. **Presentation Layer:** A modern React-based frontend (communicating via JSON API) handled by the Frontend Lead.
2. **Business Logic Layer:** A Python/Django REST Framework (DRF) backend deployed on AWS ECS.
3. **Data Layer:** A managed PostgreSQL instance for relational data and a Redis cache for session management and task queuing.

### 2.2 System Diagram (ASCII Representation)
```text
[ USER BROWSER ] <--- HTTPS/TLS ---> [ AWS APPLICATION LOAD BALANCER ]
                                            |
                                            v
                                [ AWS ECS SERVICE (Django) ]
                                /            |            \
          (Cache/Queue) <--- [ Redis ]    [ Business Logic ]    [ Logic/Auth ]
                                            |            |
                                            v            v
                                [ PostgreSQL DB ] <-> [ AWS S3 Bucket ]
                                (Primary Storage)     (File Storage/CDN)
```

### 2.3 Component Details
*   **Language:** Python 3.11+
*   **Framework:** Django 4.2 (LTS)
*   **Database:** PostgreSQL 15.2
*   **Caching/Queue:** Redis 7.0 (used for Celery task distribution)
*   **Containerization:** Docker 24.0, orchestrated via AWS ECS (Fargate)
*   **Deployment Strategy:** Quarterly releases. Every 90 days, a "Release Candidate" is promoted to staging, audited for regulatory compliance, and then deployed to production.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** In Progress
**Description:** A comprehensive security layer that manages identity and dictates access levels based on the user's role within a legal organization.

**Detailed Specification:**
The RBAC system must support four primary roles: `SuperAdmin`, `OrgAdmin`, `Instructor`, and `Learner`. Unlike standard LMS platforms, Sentinel requires "Granular Permission Sets." For example, an `Instructor` can grade a course but cannot modify the "Audit Trail" settings.

The system will implement JWT (JSON Web Tokens) for session management, stored in HTTP-only cookies to mitigate XSS attacks. The authentication flow must integrate with the legal firm's internal SSO (Single Sign-On) via SAML 2.0, though the initial build will rely on Django's internal `AbstractUser` model.

**Technical Requirements:**
*   Password hashing using Argon2.
*   Session timeouts strictly enforced at 30 minutes of inactivity for compliance.
*   Role-hierarchy logic: `SuperAdmin` $\rightarrow$ `OrgAdmin` $\rightarrow$ `Instructor` $\rightarrow$ `Learner`.
*   Middleware-level permission checks for every API request to ensure a user cannot access an endpoint simply by guessing the URL.

### 3.2 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Blocked
**Description:** A "No-Code" engine allowing administrators to create logic-based triggers (e.g., "If Learner completes Module A and scores > 80%, then enroll in Module B and notify Manager").

**Detailed Specification:**
The visual rule builder will be a drag-and-drop interface. On the backend, these rules are stored as JSON logic trees in PostgreSQL. The engine uses a "Trigger-Condition-Action" (TCA) framework.
*   **Trigger:** An event (e.g., `course_completed`, `document_uploaded`).
*   **Condition:** A boolean check (e.g., `score > 80`, `user_role == 'Partner'`).
*   **Action:** The outcome (e.g., `send_email`, `unlock_content`, `update_status`).

**Blocking Issue:** The engine currently relies on a third-party notification API for "Action" triggers. During integration testing, the team hit rate limits (100 requests/min), preventing the automation from executing in the staging environment. Development is halted until a higher tier is purchased or a custom mailer is built.

### 3.3 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** Not Started
**Description:** A tool to allow legal firms to migrate their existing student records and course materials into Sentinel without manual data entry.

**Detailed Specification:**
The system must support `.csv`, `.xlsx`, and `.json`. The "Auto-Detection" feature will use a sampling algorithm to analyze the first 10 rows of an uploaded file to guess the mapping of columns to database fields (e.g., mapping "Student Name" to `user.full_name`).

**Technical Workflow:**
1. User uploads file to S3.
2. A Celery worker triggers the `FormatDetector` class.
3. The system presents a "Mapping Preview" screen to the user for confirmation.
4. Data is validated against the schema. Any rows with errors are exported back to the user as a "Error Report" file, rather than failing the entire upload.

### 3.4 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Progress
**Description:** A non-destructive log of every administrative action taken within the platform to satisfy legal auditing requirements.

**Detailed Specification:**
Standard application logs are insufficient. Sentinel requires a "Tamper-Evident" log. Every entry in the `AuditLog` table will contain a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody. If any row is deleted or modified, the chain is broken, and an alert is triggered.

**Logged Events include:**
*   Permission changes.
*   Course content modifications.
*   User role elevations.
*   Manual grade overrides.

The log must capture: `timestamp`, `user_id`, `action_type`, `old_value`, `new_value`, and `ip_address`.

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** Not Started
**Description:** A secure mechanism for uploading legal documents and course materials, ensuring they are malware-free and delivered efficiently.

**Detailed Specification:**
Files will be uploaded to an S3 "Ingest" bucket. Before being moved to the "Public" bucket, files must be scanned by an asynchronous ClamAV worker. If a virus is detected, the file is quarantined, and the user is notified.

Once cleared, files are served via Amazon CloudFront (CDN) to reduce latency for international legal users. Access to files is controlled via "Signed URLs," ensuring that only authenticated users with the correct role can view specific documents.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 Auth Endpoints
**`POST /auth/login/`**
*   **Request:** `{"username": "string", "password": "string"}`
*   **Response (200):** `{"token": "eyJ...", "user_id": 123, "role": "Instructor"}`
*   **Response (401):** `{"error": "Invalid credentials"}`

**`POST /auth/logout/`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (204):** No content.

### 4.2 User & RBAC Endpoints
**`GET /users/me/`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (200):** `{"id": 123, "email": "user@pivotnorth.com", "permissions": ["view_courses", "edit_profile"]}`

**`PATCH /users/{id}/role/`**
*   **Request:** `{"role": "OrgAdmin"}`
*   **Response (200):** `{"status": "Role updated successfully"}`
*   **Note:** Restricted to `SuperAdmin`.

### 4.3 Automation Engine Endpoints
**`POST /automation/rules/`**
*   **Request:** `{"name": "Cert Rule", "trigger": "course_complete", "conditions": [{"field": "score", "op": "gt", "val": 80}], "actions": ["send_email"]}`
*   **Response (201):** `{"rule_id": 55, "status": "active"}`

**`GET /automation/rules/`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (200):** `[{"id": 55, "name": "Cert Rule", ...}]`

### 4.4 Audit & Data Endpoints
**`GET /audit/logs/`**
*   **Request:** Query params `?start_date=2026-01-01&end_date=2026-01-31`
*   **Response (200):** `{"logs": [{"timestamp": "...", "action": "role_change", "user": "Orla Stein"}]}`

**`POST /data/import/`**
*   **Request:** Multipart Form Data (File)
*   **Response (202):** `{"job_id": "job_abc123", "status": "processing"}`

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions

1.  **`Users`**
    *   `id` (UUID, PK)
    *   `email` (VARCHAR, Unique)
    *   `password_hash` (VARCHAR)
    *   `role_id` (FK $\rightarrow$ Roles)
    *   `created_at` (TIMESTAMP)
    *   `is_active` (BOOLEAN)

2.  **`Roles`**
    *   `id` (INT, PK)
    *   `role_name` (VARCHAR - e.g., 'SuperAdmin')
    *   `permissions_json` (JSONB)

3.  **`Organizations`**
    *   `id` (UUID, PK)
    *   `org_name` (VARCHAR)
    *   `billing_tier` (VARCHAR)
    *   `created_at` (TIMESTAMP)

4.  **`Courses`**
    *   `id` (UUID, PK)
    *   `org_id` (FK $\rightarrow$ Organizations)
    *   `title` (VARCHAR)
    *   `description` (TEXT)
    *   `version` (INT)

5.  **`Modules`**
    *   `id` (UUID, PK)
    *   `course_id` (FK $\rightarrow$ Courses)
    *   `order_index` (INT)
    *   `content_body` (TEXT)

6.  **`Enrollments`**
    *   `id` (UUID, PK)
    *   `user_id` (FK $\rightarrow$ Users)
    *   `course_id` (FK $\rightarrow$ Courses)
    *   `status` (ENUM: 'active', 'completed', 'dropped')
    *   `completion_date` (TIMESTAMP)

7.  **`AutomationRules`**
    *   `id` (UUID, PK)
    *   `name` (VARCHAR)
    *   `trigger_event` (VARCHAR)
    *   `logic_tree` (JSONB)
    *   `is_enabled` (BOOLEAN)

8.  **`AuditLogs`**
    *   `id` (BIGINT, PK)
    *   `user_id` (FK $\rightarrow$ Users)
    *   `action` (VARCHAR)
    *   `payload_before` (JSONB)
    *   `payload_after` (JSONB)
    *   `previous_hash` (VARCHAR)
    *   `current_hash` (VARCHAR)
    *   `timestamp` (TIMESTAMP)

9.  **`Files`**
    *   `id` (UUID, PK)
    *   `s3_key` (VARCHAR)
    *   `mime_type` (VARCHAR)
    *   `scan_status` (ENUM: 'pending', 'clean', 'infected')
    *   `uploaded_by` (FK $\rightarrow$ Users)

10. **`UserSessions`**
    *   `session_id` (VARCHAR, PK)
    *   `user_id` (FK $\rightarrow$ Users)
    *   `last_accessed` (TIMESTAMP)
    *   `ip_address` (INET)

### 5.2 Relationships
*   **One-to-Many:** `Organizations` $\rightarrow$ `Users` (One org has many users).
*   **One-to-Many:** `Courses` $\rightarrow$ `Modules` (One course has many modules).
*   **Many-to-Many:** `Users` $\langle\rightarrow$ `Courses` (via `Enrollments` table).
*   **One-to-Many:** `Users` $\rightarrow$ `AuditLogs` (One user generates many logs).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

#### Development (Dev)
*   **Purpose:** Local experimentation and feature branch testing.
*   **Infrastructure:** Local Docker Compose setups on developer machines.
*   **Database:** Local PostgreSQL container.
*   **CI/CD:** Pushed to GitHub $\rightarrow$ Triggered linting and unit tests.

#### Staging (Stage)
*   **Purpose:** Pre-production validation and Regulatory Review.
*   **Infrastructure:** AWS ECS Fargate (Small instance).
*   **Database:** RDS PostgreSQL (t3.medium).
*   **Data:** Anonymized production dump.
*   **Cycle:** Updated every two weeks; frozen 14 days prior to the quarterly release.

#### Production (Prod)
*   **Purpose:** Customer-facing live environment.
*   **Infrastructure:** AWS ECS Fargate (Auto-scaling cluster).
*   **Database:** RDS PostgreSQL (m5.large, Multi-AZ).
*   **Release Cycle:** Quarterly. Deployments occur at 02:00 UTC on the first Sunday of the quarter.

### 6.2 CI/CD Pipeline
We utilize a Jenkins pipeline for automation:
1. **Commit** $\rightarrow$ **Build** (Docker Image) $\rightarrow$ **Unit Tests** $\rightarrow$ **Staging Deploy**.
2. **Staging QA** (Hiro Moreau) $\rightarrow$ **UAT Approval** $\rightarrow$ **Production Deploy**.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** PyTest.
*   **Coverage Target:** 85% of business logic.
*   **Focus:** Individual functions, model methods, and utility classes.
*   **Frequency:** Every commit.

### 7.2 Integration Testing
*   **Focus:** API endpoint connectivity and database transactions.
*   **Approach:** Testing the full request-response cycle using Django's `APIClient`.
*   **Critical Path:** Validating that the `AuditLog` is correctly written whenever a `User` role is updated.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Focus:** Critical user journeys (e.g., "Learner logs in $\rightarrow$ completes module $\rightarrow$ receives certificate").
*   **Responsibility:** Hiro Moreau (QA Lead).
*   **Frequency:** Weekly on the Staging environment.

### 7.4 Penetration Testing
As the project lacks a formal compliance framework (e.g., SOC2), Pivot North Engineering will conduct **Quarterly Penetration Tests**. This involves a manual security review of the RBAC and API endpoints to identify vulnerabilities like IDOR (Insecure Direct Object References).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance requirements are 10x current capacity with no infra budget. | High | High | Build a contingency "Fallback Architecture" using lightweight caching and optimized DB indexing to maximize current hardware. |
| **R2** | Key architect is leaving the company in 3 months. | High | Critical | Raise as a blocker in the next board meeting; prioritize documentation and knowledge transfer to Orla Stein immediately. |
| **R3** | 3rd party API rate limits block automation engine. | Critical | Medium | Implement a local queuing system (Celery/Redis) to drip-feed requests or develop an in-house notification service. |
| **R4** | Regulatory review fails, delaying quarterly release. | Medium | High | Maintain a strict "Compliance Checklist" in JIRA; involve legal counsel in the Staging review phase. |

---

## 9. TIMELINE & GANTT DESCRIPTION

### Phase 1: Foundation (Current – 2026-04-15)
*   **Focus:** Authentication, RBAC, and Audit Trail.
*   **Dependencies:** Completion of the Database Schema.
*   **Critical Milestone:** **Milestone 1: Security Audit Passed (2026-04-15).**

### Phase 2: Core Logic (2026-04-16 – 2026-06-15)
*   **Focus:** Workflow Automation Engine and Data Import/Export.
*   **Dependencies:** Resolution of API rate-limit blocker.
*   **Critical Milestone:** **Milestone 2: Internal Alpha Release (2026-06-15).**

### Phase 3: Optimization & Launch (2026-06-16 – 2026-08-15)
*   **Focus:** File Uploads, CDN distribution, and performance tuning for 10k users.
*   **Dependencies:** Internal Alpha feedback.
*   **Critical Milestone:** **Milestone 3: Post-launch Stability Confirmed (2026-08-15).**

---

## 10. MEETING NOTES

### Meeting 1: 2023-11-05
*   **Attendees:** Orla, Callum, Hiro, Manu.
*   **Notes:**
    *   Current UI "unusable" per feedback.
    *   Callum says React is the only way.
    *   Orla wants Django for the backend.
    *   Manu asked about the budget. Orla said "we use what we have."
    *   **Decision:** Use Python/Django + React.

### Meeting 2: 2023-12-12
*   **Attendees:** Orla, Callum, Hiro.
*   **Notes:**
    *   API rate limits are killing the rule builder tests.
    *   Hiro says the "tamper-evident" log is failing if we delete rows.
    *   Need a fix for the hash chain.
    *   **Decision:** Move to an append-only table for logs.

### Meeting 3: 2024-01-20
*   **Attendees:** Orla, Callum, Hiro, Manu.
*   **Notes:**
    *   Architect leaving soon.
    *   Orla: "This is a blocker."
    *   Callum needs more specs on the import tool.
    *   Manu is struggling with the S3 permissions.
    *   **Decision:** Orla to bring architect departure to the board.

---

## 11. BUDGET BREAKDOWN

As the project is bootstrapping with existing team capacity, the "Budget" refers to the allocation of internal resources and existing AWS credits.

| Category | Allocation | Estimated Monthly Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 4 Full-time equivalents | $32,000 (Internal Payroll) | Orla, Callum, Hiro, Manu. |
| **Infrastructure** | AWS ECS, RDS, S3, CloudFront | $1,200 | Scaled for 10k MAU. |
| **Tools** | JIRA, GitHub Enterprise, Sentry | $450 | Software licenses. |
| **Contingency** | Reserved Credits | $500 | For burst capacity during imports. |
| **Total** | | **$34,150** | |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following items are acknowledged as technical debt to be addressed post-Milestone 3:
1.  **Structured Logging:** Currently, debugging requires reading `stdout`. A transition to ELK (Elasticsearch, Logstash, Kibana) is planned for Q4 2026.
2.  **Database Migrations:** Initial schema is being iterated rapidly; a full data migration strategy for the legacy system is still pending.
3.  **Unit Test Gaps:** Current coverage is at 40% for the automation engine; target is 85%.

### Appendix B: Format Auto-Detection Logic
The `FormatDetector` class uses the following logic to determine file types:
1.  **Magic Number Check:** Checks the first few bytes of the file (e.g., `PK` for .xlsx).
2.  **Delimiter Analysis:** If the file is text, it counts occurrences of `,`, `;`, and `\t` in the first 10 lines. The character with the most consistent frequency per line is chosen as the delimiter.
3.  **Header Matching:** Compares the first row against a dictionary of known legal keywords (e.g., "Student ID", "Certification Date", "Credit Hours").