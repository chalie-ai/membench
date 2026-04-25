Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, formal technical specification. It expands every detail provided into a professional engineering standard, including synthetic technical data, architectural patterns, and project management artifacts.

***

# PROJECT SPECIFICATION: DRIFT LMS
**Document Version:** 1.0.4  
**Project Code:** VL-DRFT-2025  
**Company:** Verdant Labs  
**Date:** October 24, 2023  
**Classification:** Confidential / ISO 27001 Restricted  
**Status:** Active / In-Development  

---

## 1. EXECUTIVE SUMMARY

**1.1 Project Overview**  
Project "Drift" is a strategic Research and Development (R&D) moonshot initiative commissioned by Verdant Labs. The goal is to develop a high-performance Educational Learning Management System (LMS) specifically tailored for the legal services industry. Unlike generic LMS platforms, Drift is designed to handle the complex regulatory requirements, high-security standards, and rigorous documentation needs inherent to legal professional development and continuing legal education (CLE).

**1.2 Business Justification**  
The legal services industry is currently underserved by modern LMS technology. Existing solutions are either bloated enterprise suites (e.g., Moodle, Canvas) that lack the necessary security rigor or niche tools that lack scalability. Verdant Labs aims to capture a first-mover advantage in "Legal-Tech Ed" by creating a platform that prioritizes data sovereignty, extreme low latency for global users, and audit-ready reporting. 

Because this is a moonshot project, the ROI is not guaranteed in the short term. However, the strategic value lies in the intellectual property (IP) generated—specifically the Rust-based backend architecture and the edge-computing deployment model. By solving the hardest problems in legal data management first, Verdant Labs can pivot this technology into other highly regulated industries (Healthcare, Finance) if the legal market penetration proves slower than expected.

**1.3 ROI Projection**  
While the project is treated as an R&D expense, the projected financial trajectory is as follows:
- **Year 1 (Development & Beta):** Net loss of $800,000 (Investment phase).
- **Year 2 (Market Entry):** Projected revenue of $1.2M through a "Pilot-to-Enterprise" licensing model, targeting five Tier-1 law firms.
- **Year 3 (Scale):** Projected ARR of $4.5M as the platform expands to include automated certification and compliance tracking.
- **Intangible ROI:** Improvement in Verdant Labs' engineering capability regarding Rust and Cloudflare Workers, reducing future time-to-market for other edge-based products.

**1.4 Executive Sponsorship**  
The project is heavily sponsored by the C-suite, granting the team a "protected" status. This means that while ROI is uncertain, the budget is secured, and the team is encouraged to prioritize technical excellence and ISO 27001 compliance over immediate monetization.

---

## 2. TECHNICAL ARCHITECTURE

**2.1 Architectural Philosophy**  
Drift utilizes a **Modular Monolith** approach. To avoid the premature complexity of microservices, all logic resides within a single deployment unit but is strictly partitioned into domain-driven modules (Auth, Billing, Courseware, Reporting). This allows for an incremental transition to microservices as specific modules (e.g., the PDF generation engine) outgrow the resources of a single worker.

**2.2 The Stack**  
- **Backend:** Rust (Axum framework). Rust was chosen for memory safety and performance, critical for the p95 response time targets.
- **Frontend:** React 18+ with TypeScript and Tailwind CSS.
- **Edge Logic:** Cloudflare Workers. This allows the application to execute logic as close to the legal professional as possible, reducing latency.
- **Database:** SQLite for the edge (via Cloudflare D1) for rapid read-access, with a centralized PostgreSQL instance for long-term persistence and auditing.
- **Security:** The entire environment is hosted within an ISO 27001 certified perimeter, ensuring all data at rest and in transit is encrypted with AES-256.

**2.3 System Diagram (ASCII Representation)**

```text
[ Client Browser ] <---> [ Cloudflare Global Edge ]
                               |
                               v
                    [ Cloudflare Workers (Rust) ]
                               |
            ---------------------------------------
            |                  |                  |
    [ Feature Flag ]    [ SQLite / D1 ]    [ Auth Module ]
    (A/B Testing)       (Edge Cache/Sess)   (RBAC Logic)
            |                  |                  |
            ---------------------------------------
                               |
                               v
                    [ Centralized PostgreSQL ]
                    (Audit Logs / Master Data)
                               |
                               v
                    [ S3 Bucket / PDF Storage ]
```

**2.4 Performance Targets**  
- **p95 Latency:** < 200ms for all API responses.
- **Availability:** 99.9% uptime.
- **Deployment Cycle:** 2-day turnaround including manual QA gate.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: A/B Testing Framework (Feature Flag System)
- **Priority:** High | **Status:** In Progress
- **Description:** A system integrated directly into the feature flag infrastructure that allows the product team to serve different versions of a feature to specific user segments without deploying new code.
- **Detailed Specification:**
  The framework must allow for "Weighted Distribution." For example, 20% of users see "Course View A" and 80% see "Course View B." The system must track user interaction metrics for both cohorts to determine which version yields higher engagement.
- **Technical Implementation:** 
  - Use a `flags` table in SQLite to store the current state of experiments.
  - The Rust backend will intercept requests and check the `user_id` against the experiment bucket.
  - Data is persisted in the `experiment_metrics` table, tracking clicks, time-on-page, and completion rates.
- **Acceptance Criteria:**
  - Ability to toggle a flag in real-time without a restart.
  - Accurate bucketing of users (no user should switch versions mid-session).
  - Dashboard visualization of A/B results.

### 3.2 Feature 2: Data Import/Export with Auto-Detection
- **Priority:** Medium | **Status:** In Design
- **Description:** A robust utility for importing student records, course materials, and legal certifications from various formats.
- **Detailed Specification:**
  The system must support `.csv`, `.xlsx`, and `.json`. The "Auto-Detection" engine uses a heuristic approach: it scans the first 10 lines of a file, identifies delimiters, and attempts to map column headers to the Drift schema (e.g., "Student Name" $\rightarrow$ `user_full_name`).
- **Technical Implementation:**
  - Implement a "Staging Import" table where data is held before being committed to the production tables.
  - A mapping UI allows the user to manually correct any auto-detection errors.
  - Export functionality must be a mirrored process, allowing for "Full Dump" or "Filtered Export" (e.g., only users who completed a specific course).
- **Acceptance Criteria:**
  - Support for files up to 50MB.
  - 90% accuracy in auto-detecting standard legal CSV formats.
  - Detailed error logs for failed rows during import.

### 3.3 Feature 3: User Authentication and RBAC
- **Priority:** Critical (Launch Blocker) | **Status:** Blocked
- **Description:** A secure identity management system providing Role-Based Access Control (RBAC) to ensure legal data confidentiality.
- **Detailed Specification:**
  Authentication must support Multi-Factor Authentication (MFA) via TOTP. The RBAC system defines four primary roles: `SuperAdmin`, `Instructor`, `Student`, and `Auditor`. Permissions are granular (e.g., `can_edit_course`, `can_view_grades`, `can_export_reports`).
- **Technical Implementation:**
  - JWT (JSON Web Tokens) for session management, stored in HttpOnly cookies.
  - Middleware in the Rust backend checks the `role` claim in the JWT against the requested endpoint's required permission.
  - Password hashing using Argon2id.
- **Acceptance Criteria:**
  - Users cannot access endpoints above their privilege level (HTTP 403).
  - MFA is mandatory for `SuperAdmin` and `Instructor` roles.
  - Session timeout expires after 30 minutes of inactivity.

### 3.4 Feature 4: Real-time Collaborative Editing
- **Priority:** Medium | **Status:** Complete
- **Description:** A shared workspace for instructors to build course curriculums simultaneously.
- **Detailed Specification:**
  This feature implements a Conflict-free Replicated Data Type (CRDT) approach. When two instructors edit the same paragraph, the system merges the changes based on a causal ordering of events rather than a "last-write-wins" strategy.
- **Technical Implementation:**
  - WebSocket connections via Cloudflare Workers' Durable Objects to maintain state.
  - Frontend uses a custom hook to sync local state with the remote server.
  - Conflict resolution is handled by the `Yjs` library integrated into the React frontend.
- **Acceptance Criteria:**
  - Latency between users < 100ms.
  - Zero data loss during concurrent edits.
  - Presence indicators (cursors) showing where other users are active.

### 3.5 Feature 5: PDF/CSV Report Generation & Scheduling
- **Priority:** Critical (Launch Blocker) | **Status:** Not Started
- **Description:** An automated engine to generate legal compliance reports and deliver them via email.
- **Detailed Specification:**
  The system must generate "Certification of Completion" PDFs that include a cryptographically signed QR code for verification. Scheduling allows administrators to set reports (Daily, Weekly, Monthly) to be sent to specific stakeholders.
- **Technical Implementation:**
  - Use a headless Chrome instance (via a separate microservice/lambda) to render HTML to PDF.
  - A cron-job scheduler in the backend triggers the generation engine.
  - Integration with SendGrid or AWS SES for email delivery.
- **Acceptance Criteria:**
  - PDFs must be formatted according to legal standards (fixed margins, specific fonts).
  - Scheduled reports must deliver within 1 hour of the trigger time.
  - Support for batching 1,000+ reports without crashing the worker.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and return JSON. Base URL: `https://api.drift.verdantlabs.io/v1`.

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns session token.
- **Request Body:** `{ "email": "user@law.com", "password": "hashed_password" }`
- **Response (200 OK):** `{ "token": "eyJ...", "user_id": "uuid-123", "role": "Student" }`
- **Response (401 Unauthorized):** `{ "error": "Invalid credentials" }`

### 4.2 `GET /courses`
- **Description:** Retrieves a list of all available courses.
- **Query Params:** `?category=corporate_law&sort=newest`
- **Response (200 OK):** `[ { "id": "c1", "title": "Tax Law 101", "credits": 5 }, ... ]`

### 4.3 `POST /courses/{id}/enroll`
- **Description:** Enrolls the authenticated user in a course.
- **Request Body:** `{ "payment_ref": "tx_999" }`
- **Response (201 Created):** `{ "status": "enrolled", "enrollment_date": "2025-11-01" }`

### 4.4 `PATCH /courses/{id}/content`
- **Description:** Updates course content (requires `Instructor` role).
- **Request Body:** `{ "section_id": "s1", "text": "Updated legal precedent..." }`
- **Response (200 OK):** `{ "version": "2.1.0", "updated_at": "2025-11-02T10:00Z" }`

### 4.5 `GET /reports/compliance/{user_id}`
- **Description:** Generates a compliance summary for a specific user.
- **Response (200 OK):** `{ "user_id": "uuid-123", "completed_hours": 40, "status": "Compliant" }`

### 4.6 `POST /reports/schedule`
- **Description:** Sets up a recurring PDF report.
- **Request Body:** `{ "report_type": "monthly_audit", "email": "admin@firm.com", "cron": "0 0 1 * *" }`
- **Response (201 Created):** `{ "schedule_id": "sch_456", "next_run": "2026-01-01" }`

### 4.7 `POST /import/detect`
- **Description:** Analyzes an uploaded file to detect format and mapping.
- **Request Body:** `multipart/form-data (file)`
- **Response (200 OK):** `{ "format": "CSV", "detected_columns": ["FirstName", "LastName", "Email"], "confidence": 0.98 }`

### 4.8 `GET /flags/experiment/{experiment_id}`
- **Description:** Returns the assigned variant for the current user.
- **Response (200 OK):** `{ "variant": "B", "feature_enabled": true }`

---

## 5. DATABASE SCHEMA

The system utilizes a hybrid model. SQLite (D1) is used for the Edge cache, and PostgreSQL is the source of truth.

### 5.1 Table Definitions

1. **`users`**
   - `id` (UUID, PK): Unique identifier.
   - `email` (VARCHAR, Unique): Primary login identifier.
   - `password_hash` (TEXT): Argon2id hash.
   - `role_id` (INT, FK): Link to `roles` table.
   - `mfa_secret` (TEXT): Encrypted TOTP secret.
   - `created_at` (TIMESTAMP): Audit timestamp.

2. **`roles`**
   - `id` (INT, PK): Primary key.
   - `role_name` (VARCHAR): (e.g., 'SuperAdmin').
   - `permissions_bitmask` (INT): Bitwise representation of access rights.

3. **`courses`**
   - `id` (UUID, PK): Course identifier.
   - `title` (VARCHAR): Course name.
   - `description` (TEXT): Long-form description.
   - `credits` (DECIMAL): CLE credits awarded.
   - `is_published` (BOOLEAN): Visibility toggle.

4. **`modules`**
   - `id` (UUID, PK): Module identifier.
   - `course_id` (UUID, FK): Links to `courses`.
   - `order_index` (INT): Sequencing for the curriculum.
   - `content_json` (JSONB): The CRDT-based content state.

5. **`enrollments`**
   - `id` (UUID, PK): Enrollment record.
   - `user_id` (UUID, FK): Link to `users`.
   - `course_id` (UUID, FK): Link to `courses`.
   - `status` (ENUM): ('active', 'completed', 'dropped').
   - `completion_date` (TIMESTAMP): When the course was finished.

6. **`assessments`**
   - `id` (UUID, PK): Test identifier.
   - `module_id` (UUID, FK): Link to `modules`.
   - `passing_score` (INT): Minimum required to pass.

7. **`user_scores`**
   - `id` (UUID, PK): Score record.
   - `user_id` (UUID, FK): Link to `users`.
   - `assessment_id` (UUID, FK): Link to `assessments`.
   - `score` (INT): The achieved score.

8. **`feature_flags`**
   - `id` (VARCHAR, PK): Flag key (e.g., 'new_dashboard_v2').
   - `is_enabled` (BOOLEAN): Global toggle.
   - `rollout_percentage` (INT): 0-100.
   - `experiment_id` (UUID, Nullable): Link to `experiments`.

9. **`experiments`**
   - `id` (UUID, PK): Experiment identifier.
   - `name` (VARCHAR): Human-readable name.
   - `start_date` (TIMESTAMP): When it began.
   - `end_date` (TIMESTAMP): When it concludes.

10. **`audit_logs`**
    - `id` (BIGINT, PK): Sequential ID.
    - `user_id` (UUID, FK): Who performed the action.
    - `action` (VARCHAR): Action type (e.g., 'UPDATE_COURSE').
    - `ip_address` (INET): Origin of the request.
    - `timestamp` (TIMESTAMP): Exact time of event.

### 5.2 Relationships
- `users` $\rightarrow$ `roles` (Many-to-One)
- `courses` $\rightarrow$ `modules` (One-to-Many)
- `users` $\rightarrow$ `enrollments` $\leftarrow$ `courses` (Many-to-Many)
- `modules` $\rightarrow$ `assessments` (One-to-Many)
- `users` $\rightarrow$ `user_scores` $\leftarrow$ `assessments` (Many-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

**6.1 Environment Strategy**
We maintain three distinct environments to ensure stability and ISO 27001 compliance.

1. **Development (Dev):**
   - Used by engineers for daily coding.
   - SQLite locally; mock services for PDF generation.
   - Auto-deploy on merge to `develop` branch.

2. **Staging (QA):**
   - A mirrored copy of Production.
   - Full ISO 27001 compliance controls.
   - Used by Paloma Oduya (QA Lead) for regression testing.
   - **Deployment Gate:** Manual sign-off by QA Lead required before promotion to Prod.

3. **Production (Prod):**
   - The live environment for pilot users.
   - Deployed via Cloudflare Workers globally.
   - High-availability PostgreSQL cluster with read-replicas in three regions.

**6.2 CI/CD Pipeline**
- **Build:** GitHub Actions triggers on PR. Rust code is compiled to WebAssembly (Wasm) for Cloudflare Workers.
- **Test:** Unit tests and integration tests must pass (100% success rate).
- **Manual Gate:** Once tests pass, a JIRA ticket is created for Paloma. Paloma performs a 2-day manual smoke test.
- **Deploy:** Upon approval, the Wasm binary is pushed to the Production environment.

**6.3 Infrastructure Constraints**
- **Worker Limits:** Each Worker has a 128MB RAM limit. Large PDF generation must be offloaded to an external HTTP service to avoid `Worker.exceeded.memory` errors.
- **Data Sovereignty:** All data for EU users must reside in the Frankfurt region to comply with GDPR and legal industry standards.

---

## 7. TESTING STRATEGY

**7.1 Unit Testing**
- **Focus:** Individual Rust functions, React components.
- **Tooling:** `cargo test` for backend; `Jest` and `React Testing Library` for frontend.
- **Requirement:** 80% code coverage on all business logic modules.

**7.2 Integration Testing**
- **Focus:** API endpoints and database interactions.
- **Method:** Testing the interaction between the Axum backend and the SQLite/Postgres layer.
- **Scenario:** Ensure that a user with the `Student` role cannot call the `PATCH /courses` endpoint.

**7.3 End-to-End (E2E) Testing**
- **Focus:** Critical user journeys (e.g., Sign up $\rightarrow$ Enroll in Course $\rightarrow$ Complete Quiz $\rightarrow$ Download PDF).
- **Tooling:** `Playwright`.
- **Frequency:** Run every 24 hours on the Staging environment.

**7.4 Manual QA Gate**
As per the project constraints, every deployment has a mandatory manual gate. Paloma Oduya (QA Lead) verifies:
- Feature correctness against JIRA requirements.
- Visual regression on Chrome, Safari, and Firefox.
- Performance verification (p95 checks).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Regulatory requirements change mid-build | High | High | Maintain a flexible schema; negotiate timeline extensions with stakeholders. |
| R2 | Scope creep from "small" feature requests | High | Medium | Document all workarounds; strictly adhere to JIRA ticketing; reject non-critical items until v1.1. |
| R3 | Rust talent gap/onboarding delay | Low | Medium | Use Mila Jensen (Intern) as a primary learner; provide intensive Rust mentorship via Bodhi Stein. |
| R4 | ISO 27001 Audit Failure | Low | Critical | Weekly security audits; automated vulnerability scanning in CI/CD. |
| R5 | Memory leaks in Wasm workers | Medium | Medium | Implement strict memory monitoring and a periodic "soft restart" of worker instances. |

**Impact Matrix:**
- **Critical:** Project termination or legal liability.
- **High:** Milestone delay of > 2 weeks.
- **Medium:** Minor feature delay or performance dip.
- **Low:** Negligible impact on launch.

---

## 9. TIMELINE AND PHASES

The project is on a 6-month accelerated build cycle.

**Phase 1: Foundation (Month 1-2)**
- Setup ISO 27001 environment.
- Implement Core Auth and RBAC (currently blocked).
- Establish Rust $\rightarrow$ Cloudflare pipeline.
- *Dependency:* Auth must be unblocked before Courseware development begins.

**Phase 2: Core Feature Build (Month 3-4)**
- Implement Collaborative Editing (Completed).
- Build A/B Testing Framework (In Progress).
- Develop Data Import/Export engine.
- *Dependency:* CRDT implementation must be stable before A/B testing on the editor begins.

**Phase 3: Hardening & Reporting (Month 5)**
- Implement PDF/CSV Generation.
- Setup Scheduling Cron jobs.
- Full regression testing by QA.
- *Dependency:* Reporting depends on the finalized data schema from Phase 1.

**Phase 4: Launch & Pilot (Month 6)**
- **2026-03-15:** Production Launch.
- **2026-05-15:** External Beta (10 pilot users).
- **2026-07-15:** Final Stakeholder Demo and Sign-off.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning - Architecture Review
**Date:** 2023-11-02 | **Attendees:** Bodhi, Chandra, Paloma, Mila
- **Discussion:** Bodhi proposed the modular monolith approach. Chandra expressed concern regarding SQLite's concurrency limits for the edge.
- **Decision:** We will use Cloudflare D1 for session and flag caching, but use a centralized Postgres for "Truth" data to avoid concurrency bottlenecks.
- **Action Items:**
  - Chandra: Finalize D1 schema mapping. [Owner: Chandra]
  - Bodhi: Review ISO 27001 checklist for the worker environment. [Owner: Bodhi]

### Meeting 2: Feature Flag Synchronization
**Date:** 2023-12-15 | **Attendees:** Bodhi, Chandra, Mila
- **Discussion:** Mila noted that the A/B testing framework was conflicting with the collaborative editing state. Users were seeing different versions of the editor, causing CRDT sync errors.
- **Decision:** A/B tests will be applied at the *component* level, not the *page* level, to ensure the underlying data model remains consistent.
- **Action Items:**
  - Mila: Refactor `ExperimentProvider` to wrap individual components. [Owner: Mila]
  - Bodhi: Update the JIRA ticket for the A/B framework. [Owner: Bodhi]

### Meeting 3: Blockers and Technical Debt
**Date:** 2024-01-10 | **Attendees:** Bodhi, Paloma, Chandra
- **Discussion:** Paloma identified a critical issue: three different date formats (ISO 8601, Unix Epoch, and RFC 2822) are being used across the codebase. This is causing bugs in the report generation logic.
- **Decision:** We will not perform a full refactor now to avoid delaying the launch. Instead, we will implement a `DateNormalization` utility layer that all modules must use.
- **Action Items:**
  - Chandra: Write the `normalize_date()` helper function in Rust. [Owner: Chandra]
  - Paloma: Create a test suite specifically for date-edge cases. [Owner: Paloma]

---

## 11. BUDGET BREAKDOWN

Total Budget: **$800,000** (Fixed for 6-month build)

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | 6 engineers/QA (Average $93k per head for 6 mo). |
| **Infrastructure** | 15% | $120,000 | Cloudflare Enterprise, Postgres Managed Instance, S3. |
| **Security/Compliance** | 5% | $40,000 | ISO 27001 Certification audits and consultants. |
| **Tools & Licensing** | 5% | $40,000 | JIRA, GitHub Enterprise, SendGrid, Playwright Cloud. |
| **Contingency** | 5% | $40,000 | Reserved for emergency scaling or regulatory shifts. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following technical debts are acknowledged and scheduled for resolution post-Milestone 3:
1. **Date Normalization:** Current codebase uses mixed date formats. (Mitigated by `DateNormalization` utility).
2. **Monolith Scaling:** The `Courseware` module is becoming too large; needs split into a separate worker.
3. **Mocked Payments:** Currently using a mock payment gateway; needs full Stripe/LawPay integration.

### Appendix B: ISO 27001 Compliance Matrix
To maintain certification, the project adheres to:
- **A.9 Access Control:** RBAC is strictly enforced via JWT and middleware.
- **A.10 Cryptography:** All PII is encrypted with AES-256; passwords use Argon2id.
- **A.12 Operations Security:** Manual QA gate and 2-day turnaround prevent unstable code from hitting production.
- **A.13 Communications Security:** All traffic is forced over TLS 1.3.