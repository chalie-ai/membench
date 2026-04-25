# PROJECT SPECIFICATION DOCUMENT: GANTRY LMS
**Version:** 1.2.0  
**Status:** Active / In-Development  
**Last Updated:** 2024-05-22  
**Document Owner:** Elara Costa (VP of Product)  
**Organization:** Coral Reef Solutions  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Gantry" is an internal Learning Management System (LMS) designed specifically for the government services sector. What began as a rapid-prototype hackathon project has evolved into a mission-critical productivity tool, currently supporting 500 daily active users (DAU). The platform is designed to bridge the gap between complex government regulatory requirements and the need for agile, internal staff upskilling.

The primary objective of Gantry is to provide a centralized hub for training modules, compliance tracking, and certification management. Unlike commercial off-the-shelf LMS solutions, Gantry is tailored for the strict data residency and security requirements of government contracts, ensuring that all PII (Personally Identifiable Information) is handled according to stringent legal frameworks.

### 1.2 Business Justification
The government services industry is characterized by high turnover and constant regulatory shifts. The cost of manual training and the risk of non-compliance fines represent a significant financial liability for Coral Reef Solutions. Gantry mitigates this by automating the delivery of mandatory training and providing an immutable audit trail of completion.

Currently, the organization relies on fragmented spreadsheets and emails to track employee certifications. By consolidating this into Gantry, Coral Reef Solutions expects to reduce the "time-to-competency" for new hires by 40% and reduce the administrative overhead of compliance reporting by 60%.

### 1.3 ROI Projection (3-Year Horizon)
Despite being currently unfunded and bootstrapping with existing team capacity, the projected ROI is calculated based on "cost avoidance" and "productivity gains."

*   **Administrative Efficiency:** Reducing manual tracking for 500 users is estimated to save 1,200 man-hours per year. At an average internal rate of $85/hour, this is a direct saving of $102,000/year.
*   **Risk Mitigation:** Avoiding a single compliance failure in a government audit can save the company between $250,000 and $1,000,000 in potential penalties.
*   **Infrastructure Optimization:** By leveraging AWS ECS and an existing team, the marginal cost of scaling Gantry is low.

**Projected 3-Year Net Benefit:** $750,000 - $1.2M (calculated as Total Cost of Ownership vs. Operational Savings).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Gantry utilizes a traditional three-tier architecture to ensure a clear separation of concerns, allowing for independent scaling of the presentation and business logic layers.

1.  **Presentation Layer:** A responsive frontend (integrated via Django Templates and limited React components) serving the user interface.
2.  **Business Logic Layer:** A Python/Django backend implementing the "Fat Model, Thin View" pattern, managing authentication, course logic, and report generation.
3.  **Data Layer:** A persistent PostgreSQL database for relational data and a Redis cache for session management and task queuing.

### 2.2 System Diagram (ASCII Representation)
```text
[ USER BROWSER ] <---> [ AWS ALB (Application Load Balancer) ]
                               |
                               v
                +------------------------------+
                |      AWS ECS CLUSTER          |
                |  (Django App Containers)     |
                |  [Pod A] [Pod B] [Pod C]      |
                +------------------------------+
                               |
         +---------------------+---------------------+
         |                     |                     |
         v                     v                     v
 [ POSTGRESQL RDS ]      [ REDIS ELASTICACHE ]  [ S3 BUCKET ]
 (Relational Data)       (Caching & Celery)      (PDFs/CSVs)
         ^                     ^                     ^
         |                     |                     |
         +----------- [ DATA RESIDENCY: EU ] ---------+
```

### 2.3 Technical Stack Details
- **Language:** Python 3.11
- **Framework:** Django 4.2 LTS
- **Database:** PostgreSQL 15.3 (AWS RDS)
- **Caching/Queue:** Redis 7.0 (AWS ElastiCache)
- **Deployment:** AWS ECS (Fargate)
- **CI/CD:** GitHub Actions $\rightarrow$ AWS ECR $\rightarrow$ ECS
- **Compliance:** Data residency enforced via `eu-central-1` (Frankfurt) and `eu-west-1` (Ireland) regions to meet GDPR requirements.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation & Scheduled Delivery
**Priority:** High | **Status:** Not Started

**Functional Description:**
The system must generate comprehensive compliance and progress reports for administrative users. These reports must be exportable in both PDF (for formal auditing) and CSV (for data analysis) formats. A critical requirement is the "Scheduled Delivery" engine, which allows administrators to set a recurring trigger (Daily, Weekly, Monthly) to email these reports to specific stakeholders.

**Technical Requirements:**
- **Library:** `ReportLab` for PDF generation and `Pandas` for CSV manipulation.
- **Async Processing:** All report generation must be offloaded to Celery workers to prevent blocking the request-response cycle.
- **Storage:** Generated files must be stored in an S3 bucket with a 30-day TTL (Time-to-Live) policy.
- **Scheduling:** Use `django-celery-beat` for managing the cron-like schedules.

**User Workflow:**
1. Admin navigates to `/reports/create/`.
2. Admin selects the data range, the target users, and the desired format (PDF/CSV).
3. Admin toggles "Schedule this report," selects "Every Monday at 08:00 UTC," and enters recipient emails.
4. System validates the query, creates a `ScheduledReport` record, and queues the first generation task.

### 3.2 Webhook Integration Framework
**Priority:** Low | **Status:** In Progress

**Functional Description:**
Gantry must be able to notify external third-party tools when specific events occur within the LMS (e.g., `course.completed`, `user.certified`, `report.generated`). This framework allows government partners to integrate Gantry data into their own internal dashboards.

**Technical Requirements:**
- **Payload:** Standard JSON format containing the event type, timestamp, and relevant entity IDs.
- **Security:** Every webhook request must include an `X-Gantry-Signature` header (HMAC-SHA256) to allow the receiver to verify the authenticity of the payload.
- **Retry Logic:** An exponential backoff strategy (5 attempts) must be implemented for failed deliveries (non-2xx responses).
- **Endpoint:** A dedicated management interface at `/settings/webhooks/` to add/remove target URLs.

**User Workflow:**
1. User enters the "Integration" panel.
2. User provides a destination URL and selects the "Event Trigger" from a dropdown.
3. Gantry sends a "Test Payload" to the URL to verify connectivity.
4. Once saved, the system monitors the Django signals; upon the trigger event, a Celery task is dispatched to POST the data to the external URL.

### 3.3 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** Complete

**Functional Description:**
A multi-channel notification engine that ensures users are alerted to course deadlines, certification expirations, and system announcements. This system is now fully operational.

**Technical Requirements:**
- **Email:** Integration via AWS SES.
- **SMS:** Integration via Twilio API.
- **In-App:** A WebSocket-based notification bell using Django Channels.
- **Push:** Firebase Cloud Messaging (FCM) for mobile browser notifications.
- **Preference Center:** A user-facing setting page where users can toggle specific channels for specific notification types.

**Implementation Detail:**
The system uses a `Notification` model that acts as a registry. When a trigger occurs, a `NotificationDispatcher` class determines which channels the user has enabled and routes the message through the respective provider's API.

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** In Progress

**Functional Description:**
To facilitate the migration of users and course content from legacy spreadsheets, Gantry requires a robust import/export utility. The system must automatically detect whether an uploaded file is CSV, XLSX, or JSON and map the fields to the internal database schema.

**Technical Requirements:**
- **Detection:** Use the `python-magic` library to determine MIME types.
- **Mapping:** A dynamic mapping interface where users can drag-and-drop source columns to target fields (e.g., "Employee Name" $\rightarrow$ `user.full_name`).
- **Validation:** Pre-import validation to check for duplicate emails or invalid date formats, providing a detailed error report before final commit.

**User Workflow:**
1. Admin uploads a file via `/admin/import/`.
2. System analyzes the file header and suggests a mapping.
3. Admin confirms or adjusts the mapping.
4. System processes the file in chunks of 100 rows to avoid memory overflows.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** Blocked

**Functional Description:**
Due to the sensitivity of government data, standard password authentication is insufficient. Gantry requires 2FA, specifically supporting Time-based One-Time Passwords (TOTP) and hardware-based security keys (FIDO2/WebAuthn).

**Technical Requirements:**
- **TOTP:** Implementation via `django-two-factor-auth`.
- **Hardware Keys:** Integration with `PyWebAuthn` to support YubiKeys and Google Titan keys.
- **Recovery:** Generation of ten 8-digit backup codes upon initial setup.

**Blocker Detail:**
Current implementation is blocked due to a conflict between the legacy "God class" (see Technical Debt) and the required middleware for WebAuthn. The authentication flow in the God class is too tightly coupled to allow the injection of the 2FA challenge-response loop without breaking existing session management.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a Bearer Token in the Authorization header.

### 4.1 `GET /api/v1/courses/`
- **Description:** Retrieves a list of all available courses.
- **Request Parameters:** `?category=compliance&search=safety`
- **Response (200 OK):**
```json
[
  {
    "id": "crs_101",
    "title": "Government Ethics 101",
    "duration_mins": 120,
    "status": "published"
  }
]
```

### 4.2 `POST /api/v1/courses/{id}/enroll`
- **Description:** Enrolls the authenticated user in a specific course.
- **Request Body:** `{ "userId": "usr_552" }`
- **Response (201 Created):**
```json
{
  "enrollment_id": "enr_9901",
  "status": "active",
  "expiry_date": "2025-12-31"
}
```

### 4.3 `GET /api/v1/users/{id}/progress`
- **Description:** Returns the completion percentage of all courses for a specific user.
- **Response (200 OK):**
```json
{
  "user_id": "usr_552",
  "overall_completion": 65.4,
  "courses": [
    { "course_id": "crs_101", "progress": 100 },
    { "course_id": "crs_102", "progress": 30 }
  ]
}
```

### 4.4 `POST /api/v1/reports/generate`
- **Description:** Triggers an immediate generation of a report.
- **Request Body:** `{ "type": "compliance", "format": "pdf", "user_ids": ["usr_1", "usr_2"] }`
- **Response (202 Accepted):**
```json
{
  "task_id": "celery_abc_123",
  "status": "queued",
  "poll_url": "/api/v1/reports/status/celery_abc_123"
}
```

### 4.5 `GET /api/v1/reports/status/{task_id}`
- **Description:** Checks the status of a background report generation task.
- **Response (200 OK):**
```json
{
  "task_id": "celery_abc_123",
  "status": "completed",
  "download_url": "https://s3.eu-central-1.amazonaws.com/gantry/reports/rep_77.pdf"
}
```

### 4.6 `PUT /api/v1/user/profile/2fa`
- **Description:** Updates 2FA preferences.
- **Request Body:** `{ "enabled": true, "method": "hardware_key" }`
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "2FA configuration updated."
}
```

### 4.7 `POST /api/v1/webhooks/register`
- **Description:** Registers a new webhook endpoint.
- **Request Body:** `{ "url": "https://partner.gov/api/callback", "events": ["course.completed"] }`
- **Response (201 Created):**
```json
{
  "webhook_id": "wh_445",
  "secret": "shhh_secret_key_123"
}
```

### 4.8 `GET /api/v1/system/health`
- **Description:** Returns the health status of the application and its dependencies.
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.2.0"
}
```

---

## 5. DATABASE SCHEMA

### 5.1 Entity Relationship Overview
The schema follows a highly normalized relational structure to ensure data integrity and auditability.

### 5.2 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `password_hash` (String)
    - `full_name` (String)
    - `role` (Enum: STUDENT, INSTRUCTOR, ADMIN)
    - `two_factor_enabled` (Boolean)
    - `created_at` (Timestamp)

2.  **`courses`**
    - `id` (UUID, PK)
    - `title` (String)
    - `description` (Text)
    - `category` (String)
    - `version` (String)
    - `is_mandatory` (Boolean)
    - `created_by` (FK $\rightarrow$ `users.id`)

3.  **`modules`**
    - `id` (UUID, PK)
    - `course_id` (FK $\rightarrow$ `courses.id`)
    - `title` (String)
    - `content_url` (String)
    - `order_index` (Integer)

4.  **`enrollments`**
    - `id` (UUID, PK)
    - `user_id` (FK $\rightarrow$ `users.id`)
    - `course_id` (FK $\rightarrow$ `courses.id`)
    - `enrolled_at` (Timestamp)
    - `completion_status` (Enum: IN_PROGRESS, COMPLETED, EXPIRED)

5.  **`user_progress`**
    - `id` (UUID, PK)
    - `user_id` (FK $\rightarrow$ `users.id`)
    - `module_id` (FK $\rightarrow$ `modules.id`)
    - `last_accessed` (Timestamp)
    - `is_complete` (Boolean)

6.  **`certifications`**
    - `id` (UUID, PK)
    - `user_id` (FK $\rightarrow$ `users.id`)
    - `course_id` (FK $\rightarrow$ `courses.id`)
    - `issue_date` (Date)
    - `expiry_date` (Date)
    - `certificate_hash` (String)

7.  **`scheduled_reports`**
    - `id` (UUID, PK)
    - `report_type` (String)
    - `frequency` (Enum: DAILY, WEEKLY, MONTHLY)
    - `recipient_emails` (JSON Array)
    - `last_run` (Timestamp)
    - `next_run` (Timestamp)

8.  **`webhooks`**
    - `id` (UUID, PK)
    - `target_url` (String)
    - `secret` (String)
    - `active` (Boolean)
    - `created_at` (Timestamp)

9.  **`webhook_logs`**
    - `id` (UUID, PK)
    - `webhook_id` (FK $\rightarrow$ `webhooks.id`)
    - `payload` (JSONB)
    - `response_code` (Integer)
    - `attempt_number` (Integer)
    - `timestamp` (Timestamp)

10. **`audit_logs`**
    - `id` (UUID, PK)
    - `user_id` (FK $\rightarrow$ `users.id`)
    - `action` (String)
    - `ip_address` (String)
    - `timestamp` (Timestamp)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry utilizes three distinct environments to isolate development and ensure production stability.

| Environment | Purpose | AWS Region | Resource Specs |
| :--- | :--- | :--- | :--- |
| **Development** | Feature iteration | `eu-central-1` | t3.medium, Single-AZ RDS |
| **Staging** | QA, UAT, Integration | `eu-central-1` | t3.large, Multi-AZ RDS (Mirror Prod) |
| **Production** | Live User Traffic | `eu-central-1` | m5.large (Auto-scaling), Multi-AZ RDS |

### 6.2 Deployment Pipeline
Deployment is fully automated via GitHub Actions.

1.  **Build Phase:** Triggered on merge to `main`. Runs `pytest` and `flake8` linting.
2.  **Artifact Phase:** Builds Docker image $\rightarrow$ pushes to AWS ECR.
3.  **Deploy Phase:** 
    - **Blue-Green Deployment:** A new set of containers (Green) is spun up.
    - **Health Check:** The ALB performs a health check on the `/api/v1/system/health` endpoint.
    - **Traffic Shift:** If healthy, 100% of traffic is routed to Green.
    - **Rollback:** If health checks fail, traffic remains on Blue, and the Green deployment is terminated.

### 6.3 Infrastructure as Code (IaC)
All infrastructure is managed via Terraform to ensure reproducibility. Key modules include:
- `vpc.tf`: Defines private subnets for RDS/ECS and public subnets for ALB.
- `ecs.tf`: Defines Fargate task definitions and service autoscaling policies.
- `rds.tf`: Configures PostgreSQL with encrypted storage and automated snapshots.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Individual functions, model methods, and utility classes.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** Minimum 80% code coverage for all business logic in `services.py`.

### 7.2 Integration Testing
- **Focus:** API endpoint flow and database transactions.
- **Tooling:** Django `APITestCase` and `Postman` automated collections.
- **Scenario:** Testing the full flow from `Course Enrollment` $\rightarrow$ `Module Completion` $\rightarrow$ `Certificate Generation`.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (The "Happy Path").
- **Tooling:** Playwright.
- **Key Tests:**
    - Admin can upload a CSV and successfully import 50 users.
    - User can complete a course and receive a notification.
    - 2FA challenge is presented upon login (once unblocked).

### 7.4 Performance Testing
- **Tooling:** Locust.
- **Target:** Simulate 5,000 concurrent users (10x current load) to validate the `p95 < 200ms` response time requirement.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor EOL (End-of-Life) for core dependency | Medium | High | Negotiate timeline extension; research replacement libraries. | Elara Costa |
| R-02 | Performance requirements (10x load) without budget | High | High | Assign dedicated owner to optimize DB queries and implement Redis caching. | Uma Gupta |
| R-03 | 2FA implementation blocked by technical debt | High | Medium | Refactor the 'God class' into modular services before attempting 2FA. | Solo Dev |
| R-04 | Data residency non-compliance | Low | Critical | Use AWS Config and IAM policies to restrict data to EU regions. | Uma Gupta |

### 8.1 Probability/Impact Matrix
- **Critical:** High Probability + High Impact (R-02)
- **High:** Medium Probability + High Impact (R-01)
- **Medium:** High Probability + Medium Impact (R-03)
- **Low:** Low Probability + High Impact (R-04)

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown

**Phase 1: Stability & Foundation (Now $\rightarrow$ 2025-06-15)**
- Refactor 'God class' (Auth/Log/Email) into three separate services.
- Implement Redis caching for heavy course queries.
- **Milestone 1:** Post-launch stability confirmed.

**Phase 2: Feature Expansion (2025-06-16 $\rightarrow$ 2025-08-15)**
- Complete Report Generation (PDF/CSV) and Scheduler.
- Unblock and implement 2FA (Hardware Key support).
- Finalize Webhook Framework.
- **Milestone 2:** MVP feature-complete.

**Phase 3: Optimization & Launch (2025-08-16 $\rightarrow$ 2025-10-15)**
- Final Load Testing (10x capacity).
- Final UAT with government pilot group.
- Production cutover.
- **Milestone 3:** Production launch.

### 9.2 Dependency Map
- `Refactor God Class` $\rightarrow$ `2FA Implementation` (HARD DEPENDENCY)
- `S3 Configuration` $\rightarrow$ `Report Generation` (HARD DEPENDENCY)
- `Database Indexing` $\rightarrow$ `Performance Metric (p95)` (SOFT DEPENDENCY)

---

## 10. MEETING NOTES

### Meeting 1: Q1 Architecture Review (2024-02-10)
- *Attendees:* Elara, Uma, Selin
- *Notes:*
    - Gantry growing fast.
    - 500 users hitting the DB hard.
    - Need Redis for session storage.
    - Uma suggests RDS Multi-AZ for stability.
    - Decisions: Move to ECS Fargate.

### Meeting 2: Feature Prioritization (2024-03-15)
- *Attendees:* Elara, Selin, Orla
- *Notes:*
    - Reports are priority 1.
    - 2FA is a "must-have" for gov.
    - Webhooks are "nice to have."
    - Orla says 2FA is blocked.
    - Elara: check the God class.
    - Decisions: Shift 2FA to Medium priority until refactor happens.

### Meeting 3: Budget & Resource Sync (2024-04-05)
- *Attendees:* Elara, Uma
- *Notes:*
    - Still no budget.
    - Bootstrapping with existing dev.
    - Performance requirements 10x.
    - Uma: "Can't scale if we don't optimize the God class."
    - Decisions: Assign solo dev to refactor first.

---

## 11. BUDGET BREAKDOWN

As an unfunded project, the budget represents the "Opportunity Cost" of team capacity and existing infrastructure overhead.

| Category | Annual Allocation (Est.) | Notes |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $210,000 | Pro-rated time for VP Product, Data Eng, Designer, and Solo Dev. |
| **Infrastructure (AWS)** | $12,000 | ECS, RDS, ElastiCache, and S3 (Standard Tiers). |
| **Tools/Licenses** | $2,500 | GitHub Enterprise, Jira, Twilio/SES API costs. |
| **Contingency (10%)** | $22,450 | Reserved for emergency scaling or contractor hours. |
| **Total Estimated Cost** | **$246,950** | |

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt Analysis
The current `core/auth_manager.py` contains a class `GantryManager` totaling 3,000 lines.
- **Current Responsibilities:**
    - User session validation and password hashing.
    - System-wide logging to PostgreSQL.
    - Email template rendering and sending via SES.
    - Course access permission checks.
- **Refactoring Plan:** 
    1. Split into `AuthenticationService`, `LoggingService`, and `NotificationService`.
    2. Implement a `PermissionProxy` for access control.
    3. Move logic into Django signals where appropriate.

### Appendix B: Data Residency Compliance Matrix
To satisfy GDPR and CCPA for government services:
- **Storage:** All EBS volumes and RDS instances are encrypted with AES-256.
- **Location:** All data is stored exclusively in the `eu-central-1` (Frankfurt) region.
- **Access:** Access to the production database is restricted via a Bastion host and requires MFA.
- **Deletion:** Implemented a `hard_delete` mechanism to ensure "Right to be Forgotten" requests are processed across all backups within 30 days.