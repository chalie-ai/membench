Due to the extreme length requirements of this request (6,000–8,000 words), the following document is presented as a comprehensive, professional Project Specification Document. To maintain the integrity of the technical details, it is structured as a master reference guide for the development team of Project Delphi.

***

# PROJECT SPECIFICATION: DELPHI LMS
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft for Review  
**Classification:** Confidential - Flintrock Engineering Internal  
**Project Lead:** Xander Moreau (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Delphi is a strategic educational Learning Management System (LMS) platform developed by Flintrock Engineering. The project is designed specifically for the government services industry, where compliance, auditability, and scalability are paramount. The core objective of Delphi is to serve as a cost-reduction initiative by consolidating four redundant internal tools currently used for training, certification, and compliance tracking into a single, unified ecosystem.

Currently, Flintrock Engineering maintains four disparate systems: the "Legacy Training Portal," the "Certification Tracker," the "Compliance Repository," and the "Onboarding Module." These systems suffer from fragmented data, overlapping subscription costs, and divergent user experiences. By merging these into Delphi, the organization aims to eliminate the operational overhead associated with maintaining four separate codebases and four different database schemas.

### 1.2 Business Justification
The justification for Project Delphi is rooted in operational efficiency and risk mitigation. The existing toolset requires significant manual intervention to sync user progress across platforms, leading to data silos and reporting inaccuracies. In a government services context, these inaccuracies can lead to compliance failures and potential legal liabilities.

By centralizing these functions, Flintrock Engineering will realize a significant reduction in "Total Cost of Ownership" (TCO). Although the project is currently unfunded and bootstrapping with existing team capacity, the long-term ROI is calculated based on the decommissioning of legacy server costs and the reclamation of approximately 1,200 man-hours per year previously spent on manual data reconciliation.

### 1.3 ROI Projection
The projected ROI is calculated over a 36-month horizon:
- **Operational Savings:** Reduction of $120,000/year in licensing fees for legacy SaaS components.
- **Productivity Gains:** 50% reduction in manual processing time for end users, equating to an estimated $200,000 in recovered labor productivity.
- **Risk Avoidance:** Mitigation of potential audit fines (estimated at $50k–$250k per incident) by implementing a tamper-evident audit trail.
- **Net Projection:** A projected break-even point at Month 14, with a cumulative 3-year saving of approximately $640,000.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Technology Stack
The Delphi platform is built on a modern, scalable stack designed to handle high-concurrency government workloads while maintaining strict security standards.

- **Backend:** Python 3.11 / Django 4.2 (LTS)
- **Database:** PostgreSQL 15 (Primary relational store)
- **Caching/Queueing:** Redis 7.0 (Session management and Celery task broker)
- **Infrastructure:** AWS ECS (Elastic Container Service)
- **Orchestration:** AWS API Gateway interfacing with serverless functions (AWS Lambda) for specific high-burst event processing.
- **Compliance:** ISO 27001 certified environment.

### 2.2 Architecture Diagram (ASCII Representation)
The following diagram describes the request flow from the client to the data layer:

```text
[ End User / Browser ] 
          |
          v
[ AWS CloudFront (CDN) ]
          |
          v
[ AWS API Gateway ] <--- (Authentication/Rate Limiting)
          |
          +-----------------------+
          |                       |
          v                       v
[ AWS Lambda (Serverless) ]   [ AWS ECS (Django Containers) ]
(Short-lived logic)           (Core Business Logic / ORM)
          |                       |
          +-----------+-----------+
                      |
                      v
             [ Redis Cache Layer ] <--- (Session/Task Queue)
                      |
                      v
            [ PostgreSQL DB Cluster ]
            (Schema: Delphi_Prod_v1)
                      |
                      v
            [ S3 Bucket (Encrypted) ] <--- (Audit Logs/Assets)
```

### 2.3 Architectural Decisions
The decision to combine ECS with serverless functions via API Gateway is intended to balance the stability of a Django monolithic core with the scalability of Lambda for specific endpoints (e.g., heavy PDF certificate generation). 

**Critical Technical Debt Note:** It is acknowledged that 30% of the current query layer bypasses the Django ORM in favor of raw SQL to optimize performance for large government datasets. This introduces a high risk during database migrations and requires strict manual verification by Nia Oduya before any schema changes are applied.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:**
The Audit Trail is the most vital component of the Delphi system. Given the government services industry, every action taken by a user—especially administrative changes to certifications—must be logged in a manner that cannot be altered by any user, including the database administrator.

**Functional Requirements:**
- **Immutable Logs:** Once a log entry is written, it must be cryptographically signed. 
- **Hashing Mechanism:** Use SHA-256 hashing where each log entry includes the hash of the previous entry (Blockchain-style chaining).
- **Storage:** Logs are written to a write-once-read-many (WORM) S3 bucket with Object Lock enabled.
- **Granularity:** Every `POST`, `PUT`, `PATCH`, and `DELETE` request must trigger a log entry containing: Timestamp, UserID, IP Address, Request Payload, and Response Status.

**Implementation Detail:**
A Django Middleware will be implemented to intercept requests. For "Critical" rated endpoints, the middleware will serialize the request and push it to a Redis queue, which a Celery worker will then process and write to the tamper-evident storage.

### 3.2 A/B Testing Framework (Feature Flag System)
**Priority:** High | **Status:** Blocked

**Description:**
To ensure data-driven UX improvements, Delphi requires a built-in A/B testing framework. This framework must be integrated directly into the feature flag system to allow for gradual rollouts and cohort-based testing.

**Functional Requirements:**
- **Dynamic Toggling:** Ability to enable/disable features for specific user segments without deploying new code.
- **Cohort Management:** Users must be randomly assigned to "Control" or "Test" groups based on their `user_id` modulo 100.
- **Metric Integration:** The framework must hook into the telemetry system to track if "Variant B" leads to a higher completion rate of educational modules.
- **Persistence:** A user’s assignment to a group must persist across sessions.

**Blocking Factor:** Currently blocked pending the finalization of the user segmentation logic in the core identity provider.

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** Blocked

**Description:**
The end-user experience is centered around a personalized dashboard. Users should be able to customize their workspace by adding, removing, and rearranging widgets (e.g., "Course Progress," "Upcoming Deadlines," "Certification Status").

**Functional Requirements:**
- **Widget Library:** A set of predefined widgets developed by Felix Santos.
- **State Persistence:** Widget positions (X, Y coordinates) and visibility must be stored in the user's profile in PostgreSQL.
- **Drag-and-Drop Interface:** Implementation via React-Grid-Layout or similar, ensuring smooth interaction.
- **Responsive Layout:** The dashboard must collapse gracefully from a 4-column desktop view to a 1-column mobile view.

**Blocking Factor:** Blocked due to the lack of a finalized UI component library for the widget containers.

### 3.4 Automated Billing and Subscription Management
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:**
While primarily an internal tool, Delphi may eventually be offered to external government partners. This requires a robust billing engine to handle subscriptions and automated invoicing.

**Functional Requirements:**
- **Tiered Pricing:** Support for "Basic," "Professional," and "Enterprise" tiers.
- **Payment Gateway:** Integration with Stripe or a government-approved payment processor.
- **Automated Invoicing:** Monthly generation of PDF invoices stored in S3.
- **Dunning Process:** Automated email alerts when a payment fails, followed by a 14-day grace period before account suspension.

**Implementation Detail:**
A dedicated `BillingService` class will handle the logic, decoupling the subscription state from the user’s authentication state to prevent lockout during payment failures.

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Description:**
Support for 12 primary languages to accommodate international government contractors. This involves both the translation of the UI (I18n) and the localization of date/currency formats (L10n).

**Functional Requirements:**
- **Translation Files:** Use of `.po` and `.mo` files via Django’s translation framework.
- **Language Selection:** A user-profile setting to toggle language, defaulting to the browser's `Accept-Language` header.
- **UTF-8 Compliance:** Ensuring all database fields supporting user-generated content use `utf8mb4` encoding.
- **Right-to-Left (RTL) Support:** CSS adjustments for languages like Arabic.

**Blocking Factor:** Blocked until the list of 12 specific languages is finalized by the stakeholder group.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is handled via JWT (JSON Web Tokens) in the Authorization header.

### 4.1 `GET /api/v1/courses/`
- **Description:** Retrieves a list of available educational courses.
- **Request:** `GET /api/v1/courses/?category=compliance`
- **Response (200 OK):**
```json
[
  {
    "id": "crs_9921",
    "title": "ISO 27001 Basics",
    "duration": "2h 30m",
    "status": "active"
  }
]
```

### 4.2 `POST /api/v1/courses/{course_id}/enroll`
- **Description:** Enrolls the authenticated user in a specific course.
- **Request:** `POST /api/v1/courses/crs_9921/enroll`
- **Response (201 Created):**
```json
{
  "enrollment_id": "enr_5542",
  "status": "enrolled",
  "completion_deadline": "2026-12-01"
}
```

### 4.3 `GET /api/v1/users/me/progress`
- **Description:** Returns the current progress of the authenticated user across all modules.
- **Request:** `GET /api/v1/users/me/progress`
- **Response (200 OK):**
```json
{
  "overall_completion": "65%",
  "completed_courses": ["crs_101", "crs_102"],
  "in_progress": ["crs_9921"]
}
```

### 4.4 `PATCH /api/v1/users/me/profile`
- **Description:** Updates user profile settings (e.g., language, timezone).
- **Request:** `PATCH /api/v1/users/me/profile` | Body: `{"language": "fr-FR"}`
- **Response (200 OK):**
```json
{
  "user_id": "usr_123",
  "updated_fields": ["language"],
  "timestamp": "2023-10-24T10:00:00Z"
}
```

### 4.5 `GET /api/v1/audit/logs`
- **Description:** (Admin Only) Retrieves the tamper-evident audit logs.
- **Request:** `GET /api/v1/audit/logs?start_date=2023-01-01`
- **Response (200 OK):**
```json
{
  "logs": [
    {
      "event_id": "evt_001",
      "action": "CERT_MODIFICATION",
      "user": "adm_01",
      "hash": "a1b2c3d4...",
      "prev_hash": "f9e8d7c6..."
    }
  ]
}
```

### 4.6 `POST /api/v1/admin/feature-flags`
- **Description:** (Admin Only) Toggles a feature flag for A/B testing.
- **Request:** `POST /api/v1/admin/feature-flags` | Body: `{"flag_id": "new_dashboard_v2", "enabled": true}`
- **Response (200 OK):**
```json
{
  "flag_id": "new_dashboard_v2",
  "status": "active",
  "affected_cohort": "Group B"
}
```

### 4.7 `GET /api/v1/billing/invoice/{invoice_id}`
- **Description:** Retrieves a specific invoice PDF link.
- **Request:** `GET /api/v1/billing/invoice/inv_2023_001`
- **Response (200 OK):**
```json
{
  "invoice_id": "inv_2023_001",
  "amount": 150.00,
  "currency": "USD",
  "download_url": "https://s3.aws.amazon.com/delphi-invoices/inv_001.pdf"
}
```

### 4.8 `PUT /api/v1/dashboard/layout`
- **Description:** Saves the custom drag-and-drop widget configuration.
- **Request:** `PUT /api/v1/dashboard/layout` | Body: `{"widgets": [{"id": "prog_1", "x": 0, "y": 0}]}`
- **Response (200 OK):**
```json
{
  "status": "success",
  "layout_version": "1.2"
}
```

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. Due to performance requirements, several views are implemented to handle the 30% raw SQL query load.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role_id` | 1:N with `enrollments` | Core user identity. |
| `roles` | `role_id` | `role_name`, `permissions_json` | 1:N with `users` | RBAC permissions. |
| `courses` | `course_id` | `title`, `description`, `version` | 1:N with `modules` | Course metadata. |
| `modules` | `module_id` | `course_id`, `content_body`, `order` | N:1 with `courses` | Individual lessons. |
| `enrollments` | `enr_id` | `user_id`, `course_id`, `status` | N:1 with `users`, `courses` | Tracks user progress. |
| `certifications`| `cert_id` | `user_id`, `course_id`, `issue_date` | N:1 with `users` | Issued credentials. |
| `audit_logs` | `log_id` | `user_id`, `action`, `payload_hash` | N:1 with `users` | Tamper-evident trail. |
| `feature_flags` | `flag_id` | `flag_name`, `is_enabled`, `cohort` | None | A/B test control. |
| `user_dashboards`| `dash_id` | `user_id`, `layout_json` | 1:1 with `users` | Saved widget positions. |
| `subscriptions` | `sub_id` | `user_id`, `plan_type`, `expiry_date` | N:1 with `users` | Billing state. |

### 5.2 Schema Relationships
- **Users $\rightarrow$ Enrollments $\rightarrow$ Courses:** A user can have multiple enrollments, and each enrollment points to a single course.
- **Users $\rightarrow$ Audit Logs:** A one-to-many relationship where every single mutation in the system creates a record in the `audit_logs` table.
- **Users $\rightarrow$ User Dashboards:** A strict 1:1 relationship to ensure each user has exactly one saved layout.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi utilizes a three-tier environment strategy to ensure stability and ISO 27001 compliance.

**1. Development (Dev):**
- **Purpose:** Feature development and unit testing.
- **Configuration:** Local Docker Compose and a shared AWS Dev cluster.
- **Deployment:** Continuous deployment via GitHub Actions.

**2. Staging (Staging):**
- **Purpose:** Integration testing and QA.
- **Configuration:** Mirror of Production (ECS cluster with smaller instance sizes).
- **Deployment:** Manual trigger from Dev. This environment contains the "Manual QA Gate."

**3. Production (Prod):**
- **Purpose:** Live government service delivery.
- **Configuration:** Multi-AZ (Availability Zone) ECS cluster, RDS Multi-AZ for PostgreSQL, and encrypted S3 buckets.
- **Deployment:** Strict 2-day turnaround after Staging sign-off.

### 6.2 Deployment Pipeline
The deployment process is designed to be cautious:
1. **Merge to Main:** Triggered by PR approval from Xander Moreau.
2. **Automated Test Suite:** Runs unit tests and linting.
3. **Staging Deploy:** Automated deploy to Staging environment.
4. **Manual QA Gate:** Felix Santos and Nia Oduya must manually verify the feature in Staging.
5. **Production Window:** Deployment occurs during the Tuesday 02:00 UTC window to minimize impact.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** All business logic in `services.py` and `models.py`.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** Minimum 80% code coverage for all new features.

### 7.2 Integration Testing
- **Scope:** API endpoints and database interactions.
- **Tooling:** Django Rest Framework (DRF) `APITestCase`.
- **Focus:** Specifically testing the raw SQL queries to ensure they do not break during schema migrations.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user paths (Enrollment $\rightarrow$ Module Completion $\rightarrow$ Certification).
- **Tooling:** Playwright.
- **Frequency:** Run once per release cycle in the Staging environment.

### 7.4 Compliance Testing
- **Audit Verification:** A monthly "Tamper Test" where a script attempts to modify an audit log entry to verify that the hash-chain failure is detected and alerted.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Team lacks experience with Python/Django/AWS ECS stack. | High | High | Negotiate timeline extension; implement weekly peer-review sessions. |
| **R-02** | Scope creep from stakeholders adding 'small' features. | High | Medium | Xander Moreau assigned as dedicated owner to veto/track all new requests. |
| **R-03** | Raw SQL queries cause migration failure. | Medium | Critical | Mandatory manual review of all `.sql` files by Nia Oduya. |
| **R-04** | ISO 27001 audit failure. | Low | Critical | Pre-audit internal review and use of AWS Artifact for compliance reports. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required (R-01, R-02).
- **Medium/Critical:** High monitoring required (R-03).
- **Low/Critical:** Preventative measures in place (R-04).

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with strict dependency gates.

### 9.1 Phase 1: Foundation (Current $\rightarrow$ 2026-08-15)
- **Focus:** Core API, Database Schema, and Audit Trail implementation.
- **Dependencies:** AWS Environment Provisioning.
- **Target:** **Milestone 1: Internal Alpha Release (2026-08-15).**

### 9.2 Phase 2: Feature Expansion (2026-08-16 $\rightarrow$ 2026-10-15)
- **Focus:** Dashboard widgets, A/B framework, and Course management.
- **Dependencies:** Completion of Milestone 1.
- **Target:** **Milestone 2: MVP Feature-Complete (2026-10-15).**

### 9.3 Phase 3: Hardening & Compliance (2026-10-16 $\rightarrow$ 2026-12-15)
- **Focus:** ISO 27001 hardening, performance tuning of raw SQL, and final QA.
- **Dependencies:** Feature freeze.
- **Target:** **Milestone 3: Architecture Review Complete (2026-12-15).**

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff
**Date:** 2023-11-01 | **Attendees:** Xander, Nia, Felix, Sergei
- **Discussion:** Initial review of the 4 legacy tools. Xander emphasized that the priority is cost reduction, not feature parity. Sergei expressed concern regarding the serverless/ECS hybrid approach.
- **Decision:** Agreed to use API Gateway as the primary orchestrator to allow future flexibility.
- **Action Items:**
    - Nia: Draft initial PostgreSQL schema. (Due: 2023-11-08)
    - Felix: Audit existing UX of legacy tools. (Due: 2023-11-15)

### Meeting 2: Architecture Deep-Dive
**Date:** 2023-11-15 | **Attendees:** Xander, Nia, Sergei
- **Discussion:** Debate over the ORM vs. Raw SQL. Nia demonstrated that the Django ORM was too slow for the "Certification History" report (1M+ rows).
- **Decision:** Allow raw SQL for specific read-heavy endpoints, but require a `migration_impact.md` document for every change.
- **Action Items:**
    - Sergei: Set up the AWS ECS cluster in Dev. (Due: 2023-11-22)
    - Nia: Implement the initial Audit Trail logic. (Due: 2023-11-30)

### Meeting 3: UX and Feature Prioritization
**Date:** 2023-12-01 | **Attendees:** Xander, Felix, Nia
- **Discussion:** Felix presented the dashboard mockups. Xander noted that the A/B testing framework is becoming a priority for stakeholders.
- **Decision:** Move A/B testing to "High Priority," but mark as "Blocked" until the identity provider is updated.
- **Action Items:**
    - Felix: Finalize widget specifications. (Due: 2023-12-10)
    - Xander: Communicate timeline extension to stakeholders regarding the tech stack learning curve. (Due: 2023-12-05)

---

## 11. BUDGET BREAKDOWN

As this project is bootstrapping with existing capacity, the "Budget" represents the internal allocation of labor and AWS credits.

| Category | Allocation (Annualized) | Details |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $450,000 | 2 FTEs (Nia, Felix) + VP oversight (Xander). |
| **Personnel (Contract)** | $120,000 | Sergei Stein (Contractor hours). |
| **Infrastructure (AWS)** | $45,000 | ECS, RDS, S3, and API Gateway costs. |
| **Software Tools** | $12,000 | JIRA, GitHub Enterprise, Sentry.io. |
| **Contingency Fund** | $25,000 | Set aside for emergency scaling/burst capacity. |
| **TOTAL** | **$652,000** | **Current Funding Status: Bootstrapped.** |

---

## 12. APPENDICES

### Appendix A: Tamper-Evident Log Specification
The audit log employs a linked-list hashing strategy. 
`Current_Hash = SHA256(Timestamp + UserID + Action + Payload + Previous_Hash)`
If a single bit is changed in an old log entry, the hash chain for all subsequent entries will break. A daily "Consistency Check" job runs at 00:00 UTC to verify the chain integrity.

### Appendix B: Raw SQL Performance Constraints
The following queries are exempt from ORM usage to prevent database timeouts:
1. `GET /api/v1/admin/reports/certification-summary`: Uses a Complex CTE (Common Table Expression) to aggregate 5 million records.
2. `GET /api/v1/audit/logs`: Uses index-only scans on the `log_id` and `timestamp` fields to ensure sub-200ms response times.
3. `POST /api/v1/internal/bulk-enrollment`: Uses the PostgreSQL `COPY` command for high-speed data ingestion.