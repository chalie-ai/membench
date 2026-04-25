Due to the extreme length requirements of your request (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification. To maintain the highest level of detail, it utilizes a formal engineering format, expanding every prompt requirement into a granular technical requirement.

***

# PROJECT SPECIFICATION: PINNACLE LMS
**Version:** 1.0.4  
**Status:** Active/Draft  
**Date:** October 24, 2023  
**Project Lead:** Wyatt Santos (CTO, Tundra Analytics)  
**Classification:** Internal / Confidential

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
**Pinnacle** is a specialized educational Learning Management System (LMS) developed by Tundra Analytics. Unlike general-purpose LMS platforms, Pinnacle is engineered specifically for the logistics and shipping industry, focusing on compliance training, hazardous materials certification, and operational efficiency for port and warehouse personnel. 

The project is positioned as a strategic new product vertical for Tundra Analytics. The impetus for this development is a high-value partnership with a primary enterprise client in the shipping sector who has committed to a recurring annual contract value (ACV) of $2,000,000. This provides a clear, immediate market fit and a guaranteed revenue stream upon successful delivery.

### 1.2 Business Justification & ROI Projection
The financial justification for Pinnacle is rooted in a high Return on Investment (ROI) ratio. With a total development budget of $400,000 and a guaranteed annual return of $2,000,000 from a single client, the project achieves a 5x return on investment within the first year of operation.

**ROI Analysis:**
- **Initial Investment:** $400,000 (Capex/Opex)
- **Year 1 Revenue:** $2,000,000 (Enterprise Contract)
- **Net Profit (Y1):** $1,600,000
- **Projected Margin:** 80% (post-initial development)

Beyond the immediate financial gain, Pinnacle allows Tundra Analytics to pivot from a pure analytics firm into a SaaS provider for the logistics vertical. The scalability of the platform allows for the onboarding of subsequent shipping firms, potentially scaling the annual recurring revenue (ARR) to $10M+ within 36 months.

### 1.3 Strategic Objectives
The primary goal is to deliver a robust, ISO 27001-compliant platform that handles the high-stakes training requirements of the shipping industry. Success is defined by the ability to pass an external security audit on the first attempt and achieving an 80% feature adoption rate among the initial pilot group.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Technology Stack
The platform is built on a modern, asynchronous, and highly scalable stack designed for rapid iteration.

- **Backend:** Python 3.11+ utilizing the **FastAPI** framework for high-performance asynchronous API endpoints.
- **Database:** **MongoDB 6.0** (NoSQL) to handle the flexible nature of educational content and varying user metadata.
- **Task Queue:** **Celery 5.2** with **Redis** as the broker for background processing of certifications and reporting.
- **Containerization:** **Docker Compose** for local development and orchestration.
- **Infrastructure:** Self-hosted on hardened virtual private servers (VPS) to ensure data sovereignty for the enterprise client.
- **Orchestration:** Serverless functions triggered via an **API Gateway**, allowing for granular scaling of specific LMS modules (e.g., the quiz engine).

### 2.2 Architectural Diagram (ASCII)

```text
[ USER BROWSER / MOBILE APP ]
           |
           v
    [ API GATEWAY (NGINX) ] <---- [ LaunchDarkly Feature Flags ]
           |
    -------------------------------------------------
    |                |               |               |
[ FastAPI App ]  [ FastAPI App ]  [ FastAPI App ] [ FastAPI App ]
 (Auth/User)      (Course Mgmt)    (Grading)       (Reporting)
    |                |               |               |
    -------------------------------------------------
           |                       |
           v                       v
    [ MongoDB Cluster ]      [ Redis / Celery Queue ]
    (User/Course Data)       (Async Job Processing)
           |                       |
           -------------------------
                        |
              [ ISO 27001 Hardened OS ]
              [ Self-Hosted Environment ]
```

### 2.3 Deployment Strategy
Pinnacle utilizes a sophisticated deployment pipeline to minimize downtime and risk:
1. **Canary Releases:** New versions are deployed to 5% of users initially. Monitoring tools track error rates before a full rollout.
2. **Feature Flags:** All major features are wrapped in **LaunchDarkly** flags. This allows the team to toggle features on/off instantly without redeploying code.
3. **Environment Parity:** Docker Compose is used across Dev, Staging, and Production to ensure "it works on my machine" translates to "it works in prod."

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine (Visual Rule Builder)
**Priority:** Low (Nice to Have) | **Status:** Complete

The Workflow Automation Engine allows administrators to create "If-This-Then-That" (IFTTT) logic for student progression. Instead of hard-coding course paths, admins use a visual drag-and-drop interface to set triggers and actions.

**Technical Specification:**
The engine operates on a JSON-based logic tree stored in MongoDB. A "Trigger" (e.g., `COURSE_COMPLETED`) initiates a check against a set of "Conditions" (e.g., `SCORE > 80%`). If conditions are met, an "Action" is executed (e.g., `UNLOCK_MODULE_B` or `SEND_EMAIL_CERTIFICATION`).

**User Experience:**
The visual builder uses a node-based canvas. Users can drag "Trigger Nodes" and connect them via "Logic Edges" to "Action Nodes." This is critical for logistics training where a user must pass a "Safety Level 1" quiz before the system allows them to access "Heavy Machinery Operation" materials.

**Implementation Details:**
- Backend: A recursive evaluator function in FastAPI that parses the JSON logic tree.
- Frontend: React-flow library for the node-based visualization.

### 3.2 A/B Testing Framework
**Priority:** Medium | **Status:** Blocked

The A/B testing framework is designed to be baked directly into the LaunchDarkly feature flag system. It allows Tundra Analytics to test different instructional designs (e.g., Video vs. Text-based learning) to see which yields higher completion rates.

**Technical Specification:**
The framework leverages "User Segments" within LaunchDarkly. A user is randomly assigned to `Bucket A` or `Bucket B` upon their first login. The system then logs interaction events (clicks, time-on-page, quiz scores) tagged with the bucket ID.

**Blocking Issue:**
Development is currently blocked due to the medical leave of the Lead Frontend Engineer, who was responsible for the event-tracking instrumentation required to feed the A/B data back into the analytics engine.

**Success Metric:**
The framework must be able to provide a statistical significance (p-value < 0.05) for the difference in course completion rates between two variants.

### 3.3 Offline-First Mode with Background Sync
**Priority:** Low (Nice to Have) | **Status:** In Progress

Given that logistics workers often operate in "dead zones" (warehouses, ships, remote docks), the platform must support offline learning.

**Technical Specification:**
Pinnacle utilizes a Progressive Web App (PWA) architecture with **IndexedDB** for client-side storage. When a user enters a "Course," the system pre-fetches all necessary assets (PDFs, Quiz JSONs, Videos) and stores them locally.

**Sync Logic:**
A background synchronization service monitors the `navigator.onLine` status. When connectivity is restored, the service pushes a queue of "Completed Actions" (e.g., quiz answers, time spent) to the `/sync` endpoint using a conflict-resolution strategy: *Last-Write-Wins* based on the client's timestamp.

**Challenges:**
Handling large video files in IndexedDB is currently causing storage quota alerts on some mobile devices; the team is exploring an aggressive compression strategy.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low (Nice to Have) | **Status:** Complete

Due to the ISO 27001 requirements, standard password authentication is insufficient. Pinnacle implements multi-factor authentication (MFA).

**Technical Specification:**
The system supports both Time-based One-Time Passwords (TOTP) via apps like Google Authenticator and hardware-based keys using the **WebAuthn** standard (e.g., Yubikeys).

**Authentication Flow:**
1. User enters username/password.
2. Server validates credentials and checks if 2FA is enabled.
3. Server issues a temporary `MFA_PENDING` token.
4. User provides TOTP code or touches their hardware key.
5. Server validates the second factor and issues the final JWT (JSON Web Token).

**Security Note:**
All 2FA secrets are encrypted at rest in MongoDB using AES-256 encryption with keys managed by a secure vault.

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** Complete

To accommodate different user roles (Student, Instructor, Compliance Officer), the dashboard is fully modular.

**Technical Specification:**
The dashboard is composed of "Widget Components." Each widget is a standalone React component that fetches data from a specific API endpoint. Users can drag these widgets to reorder them or resize them.

**Persistence:**
The layout configuration (coordinates, widget IDs, and sizes) is saved as a JSON object in the `user_preferences` collection in MongoDB.

**Available Widgets:**
- **Progress Ring:** Circular visualization of course completion %.
- **Upcoming Deadlines:** A list of expiring certifications.
- **Quick-Start:** A button to resume the last viewed lesson.
- **Leaderboard:** A competitive ranking of users by certification speed.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful principles and return JSON. Base URL: `https://api.pinnacle.tundra.io/v1`

### 4.1 User Authentication
**Endpoint:** `POST /auth/login`
- **Description:** Authenticates user and returns a pending MFA token.
- **Request:** `{ "username": "jdoe_shipping", "password": "hashed_password" }`
- **Response:** `{ "status": "MFA_REQUIRED", "mfa_token": "xyz123...", "expires": "300s" }`

### 4.2 MFA Verification
**Endpoint:** `POST /auth/mfa/verify`
- **Description:** Validates TOTP or WebAuthn response.
- **Request:** `{ "mfa_token": "xyz123...", "code": "123456" }`
- **Response:** `{ "access_token": "jwt_token_here", "refresh_token": "ref_token_here" }`

### 4.3 Course Retrieval
**Endpoint:** `GET /courses/{course_id}`
- **Description:** Fetches metadata and structure for a specific course.
- **Response:**
  ```json
  {
    "course_id": "LOG-101",
    "title": "Hazardous Materials Handling",
    "modules": [
      {"id": 1, "title": "Introduction", "status": "completed"},
      {"id": 2, "title": "Safety Protocols", "status": "locked"}
    ]
  }
  ```

### 4.4 Progress Update (Sync)
**Endpoint:** `POST /sync/progress`
- **Description:** Updates course progress from offline mode.
- **Request:**
  ```json
  {
    "user_id": "u123",
    "updates": [
      {"module_id": 1, "completion_date": "2025-01-10T10:00:00Z", "score": 95}
    ]
  }
  ```
- **Response:** `{ "status": "synced", "conflicts_resolved": 0 }`

### 4.5 Rule Builder Save
**Endpoint:** `POST /admin/workflows/save`
- **Description:** Saves a visual rule configuration.
- **Request:** `{ "workflow_id": "wf_01", "logic_tree": { "trigger": "...", "actions": [...] } }`
- **Response:** `{ "status": "success", "version": 4 }`

### 4.6 Dashboard Layout
**Endpoint:** `PUT /user/preferences/dashboard`
- **Description:** Updates the drag-and-drop layout coordinates.
- **Request:** `{ "layout": [{"widget": "progress_ring", "x": 0, "y": 0, "w": 2, "h": 2}] }`
- **Response:** `{ "updated": true }`

### 4.7 Certification Generation
**Endpoint:** `GET /certifications/generate/{user_id}/{course_id}`
- **Description:** Triggers a Celery task to generate a PDF certificate.
- **Response:** `{ "task_id": "celery_task_id_99", "status": "pending" }`

### 4.8 User Management
**Endpoint:** `PATCH /admin/users/{user_id}`
- **Description:** Updates user roles or permissions.
- **Request:** `{ "role": "instructor", "permissions": ["can_grade", "can_edit_course"] }`
- **Response:** `{ "user_id": "u123", "new_role": "instructor" }`

---

## 5. DATABASE SCHEMA (MONGODB)

Since MongoDB is schema-less, the following describes the **expected document structures** and relationships.

### 5.1 Collection: `users`
- `_id`: ObjectId (Primary Key)
- `username`: String (Unique Index)
- `password_hash`: String
- `mfa_secret`: Encrypted String
- `role`: String (Enum: 'student', 'instructor', 'admin')
- `preferences`: Object (Nested layout data)
- `created_at`: Timestamp

### 5.2 Collection: `courses`
- `_id`: ObjectId
- `title`: String
- `description`: String
- `version`: Integer
- `modules`: Array of ObjectRefs (Points to `modules` collection)
- `category`: String (e.g., 'Maritime', 'Warehouse')

### 5.3 Collection: `modules`
- `_id`: ObjectId
- `course_id`: ObjectId (Foreign Key)
- `title`: String
- `content_url`: String
- `order`: Integer
- `is_locked`: Boolean

### 5.4 Collection: `user_progress`
- `_id`: ObjectId
- `user_id`: ObjectId (FK)
- `module_id`: ObjectId (FK)
- `status`: String (Enum: 'not_started', 'in_progress', 'completed')
- `score`: Decimal
- `last_accessed`: Timestamp

### 5.5 Collection: `workflows`
- `_id`: ObjectId
- `name`: String
- `logic_tree`: Object (Nested JSON representing the rule builder)
- `is_active`: Boolean
- `created_by`: ObjectId (FK)

### 5.6 Collection: `certifications`
- `_id`: ObjectId
- `user_id`: ObjectId (FK)
- `course_id`: ObjectId (FK)
- `issue_date`: Timestamp
- `expiry_date`: Timestamp
- `cert_hash`: String (Unique identifier for verification)

### 5.7 Collection: `audit_logs`
- `_id`: ObjectId
- `actor_id`: ObjectId (FK)
- `action`: String
- `ip_address`: String
- `timestamp`: Timestamp
- `payload`: Object (Changes made)

### 5.8 Collection: `feature_flags`
- `_id`: ObjectId
- `flag_name`: String (Matches LaunchDarkly keys)
- `enabled_for_roles`: Array of Strings
- `override_users`: Array of ObjectIds

### 5.9 Collection: `ab_tests`
- `_id`: ObjectId
- `test_name`: String
- `variants`: Array (['A', 'B'])
- `metric_tracked`: String
- `start_date`: Timestamp

### 5.10 Collection: `billing_records`
- `_id`: ObjectId
- `client_id`: String
- `amount`: Decimal
- `billing_cycle`: String
- `status`: String (Enum: 'paid', 'pending', 'overdue')

**Relationships Summary:**
- `Users` $\rightarrow$ `UserProgress` (1:N)
- `Courses` $\rightarrow$ `Modules` (1:N)
- `Users` $\rightarrow$ `Certifications` (1:N)
- `Workflows` $\rightarrow$ `UserProgress` (Logic trigger relationship)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Pinnacle utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and initial unit testing.
- **Host:** Local Docker containers / Tundra Dev Server.
- **Database:** MongoDB Atlas (Free Tier) or local Docker Mongo.
- **Configuration:** Debug mode enabled; no SSL requirements.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing and Client UAT (User Acceptance Testing).
- **Host:** Dedicated VPS mimicking production hardware.
- **Database:** Mirror of production (sanitized data).
- **Configuration:** Full SSL; LaunchDarkly staging project; ISO 27001 baseline security.

#### 6.1.3 Production (Prod)
- **Purpose:** Live enterprise client usage.
- **Host:** Self-hosted, hardened servers in the client's preferred region.
- **Database:** High-availability MongoDB Replica Set with automated backups.
- **Configuration:** Strict ISO 27001 compliance; Canary deployment enabled; Monitoring via Prometheus/Grafana.

### 6.2 Infrastructure as Code (IaC)
The environment is defined using Docker Compose files and Ansible playbooks. This ensures that the "self-hosted" requirement is met consistently across different hardware providers.

### 6.3 Security Hardening
To meet ISO 27001:
- **Network:** Firewall restricted to specific IP ranges.
- **Encryption:** All data encrypted at rest (AES-256) and in transit (TLS 1.3).
- **Access:** SSH access disabled in favor of a bastion host with key-based authentication.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Testing individual FastAPI endpoints, utility functions, and the Workflow Engine logic.
- **Requirement:** 80% code coverage for all new modules.
- **Execution:** Run on every Git push via GitHub Actions.

### 7.2 Integration Testing
- **Framework:** `HTTPX` and `Pytest-asyncio`
- **Scope:** Testing the interaction between FastAPI and MongoDB. Validating that a "Course Completion" trigger correctly updates the `user_progress` and triggers a `certification` record.
- **Execution:** Run daily on the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright
- **Scope:** Simulating a student's journey: Login $\rightarrow$ Complete Course $\rightarrow$ Take Quiz $\rightarrow$ Receive Certificate.
- **Focus:** Critical path testing, including the "Offline-First" sync flow (simulating network loss).

### 7.4 The "Billing Module" Debt Issue
**Current State:** The core billing module was deployed without tests to meet a deadline.
**Remediation Plan:** 
1. Immediate freeze on billing logic changes.
2. Development of a comprehensive "Billing Regression Suite" (50+ test cases).
3. Retroactive testing of all existing billing calculations before the next release cycle.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lack of experience with FastAPI/MongoDB | High | Medium | Hire a specialized contractor for a 3-month mentorship/consultancy period to reduce bus factor. | Wyatt S. |
| R-02 | Primary vendor EOL (End-of-Life) announcement | Medium | High | Assign dedicated owner to track the roadmap and migrate to an alternative library/service. | Vera P. |
| R-03 | Key team member on medical leave (6 weeks) | High | High | Reallocate tasks; delay "A/B Testing" feature; prioritize "Workflow Engine" stability. | Wyatt S. |
| R-04 | Failure to pass ISO 27001 audit | Low | Critical | Conduct bi-weekly internal security audits using Anouk Park’s checklist. | Anouk P. |
| R-05 | Technical debt in Billing Module | Medium | High | Dedicated "Sprint 0" for billing test coverage before next deployment. | Kian F. |

**Impact Matrix:**
- **Critical:** Project failure or legal liability.
- **High:** Major feature delay or significant budget overage.
- **Medium:** Minor feature delay or manageable technical debt.
- **Low:** Negligible impact on timeline.

---

## 9. TIMELINE & MILESTONES

The project follows an aggressive but focused timeline.

### 9.1 Phase 1: Foundation & Alpha (Now $\rightarrow$ Oct 15, 2025)
- **Focus:** Core API development, User Auth, Basic Course Structure.
- **Dependency:** Environment hardening must be complete before Alpha release.
- **Target Milestone:** **Internal Alpha Release (2025-10-15).**

### 9.2 Phase 2: Beta & Refinement (Oct 16, 2025 $\rightarrow$ Aug 15, 2025*)
*(Note: The project targets these specific dates in the future/inverted sequence as requested)*
- **Focus:** Workflow Engine, Offline Sync, Dashboard.
- **Dependency:** Recovery of team member from medical leave to enable A/B Testing.
- **Target Milestone:** **External Beta with 10 Pilot Users (2025-08-15).**

### 9.3 Phase 3: Enterprise Onboarding (Aug 16, 2025 $\rightarrow$ June 15, 2025*)
- **Focus:** External Audit, Final Bug Squashing, Client Data Migration.
- **Dependency:** Passing the ISO 27001 audit.
- **Target Milestone:** **First Paying Customer Onboarded (2025-06-15).**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Wyatt, Vera, Anouk, Kian  
**Discussion:** 
The team debated whether to use PostgreSQL or MongoDB. Wyatt argued that the flexible nature of course content (varying quiz types, multimedia assets) makes NoSQL a better fit. Anouk raised concerns about ACID compliance for the billing module.
**Decision:** Proceed with MongoDB, but implement a strict schema validation layer at the application level for billing records.
**Action Items:**
- [Vera] Set up Docker Compose environment with Mongo Replica Set. (Owner: Vera)
- [Wyatt] Draft the initial API spec for User Auth. (Owner: Wyatt)

### Meeting 2: The "Vendor Crisis" Sync
**Date:** 2023-12-15  
**Attendees:** Wyatt, Vera, Anouk  
**Discussion:** 
A primary dependency for the PDF generation engine announced it will reach EOL in 12 months. The team expressed concern that the current implementation is too tightly coupled.
**Decision:** Assign Vera to research `ReportLab` and `WeasyPrint` as replacements. All new PDF logic must be abstracted behind an interface to allow for a "plug-and-play" swap.
**Action Items:**
- [Vera] Complete vendor replacement analysis by end of month. (Owner: Vera)
- [Anouk] Ensure new library meets security standards. (Owner: Anouk)

### Meeting 3: Resource Reallocation (Medical Leave)
**Date:** 2024-01-10  
**Attendees:** Wyatt, Kian, Anouk  
**Discussion:** 
One key developer is on medical leave for 6 weeks. This has stalled the A/B Testing framework. Wyatt suggests shifting Kian's focus from support to helping with basic UI components, but admits the complex A/B logic is blocked.
**Decision:** Mark "A/B Testing Framework" as **Blocked**. Pivot resources to ensure the "Offline-First" mode is stable, as the shipping client emphasized this as a "must-have" during the last call.
**Action Items:**
- [Kian] Take over basic frontend ticket queue for the Dashboard. (Owner: Kian)
- [Wyatt] Update the client on the A/B testing delay. (Owner: Wyatt)

---

## 11. BUDGET BREAKDOWN

Total Budget: **$400,000**

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $280,000 | Salaries for the 12-person team (distributed across the dev cycle). |
| **Infrastructure** | 10% | $40,000 | Self-hosted VPS, MongoDB Atlas backup, and Redis hosting. |
| **Tools/SaaS** | 5% | $20,000 | LaunchDarkly (Enterprise Tier), GitHub Actions, Sentry.io. |
| **Contractor** | 10% | $40,000 | Specialized FastAPI/Mongo consultant to mitigate "Bus Factor" risk. |
| **Contingency** | 5% | $20,000 | Emergency buffer for unexpected infrastructure costs or legal fees. |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist
To ensure the "Pass external audit on first attempt" success criterion, the following controls are implemented:
1. **Access Control:** Role-Based Access Control (RBAC) integrated into the FastAPI dependency injection system.
2. **Cryptography:** Use of `bcrypt` for password hashing and `cryptography.fernet` for secret storage.
3. **Logging:** Comprehensive audit logs stored in a read-only MongoDB collection, capturing all `ADMIN` level actions.
4. **Network Security:** Implement a Zero Trust model; no internal services are exposed to the public internet except through the API Gateway.

### Appendix B: Celery Task Pipeline for Certifications
Due to the resource-heavy nature of PDF generation, the following pipeline is used:
1. `generate_cert_request` $\rightarrow$ API receives request, creates a record in `certifications` collection with status `PENDING`.
2. `celery_worker_pdf` $\rightarrow$ Picks up task, fetches user/course data, generates PDF using the template engine.
3. `celery_worker_upload` $\rightarrow$ Uploads the final PDF to the secure storage bucket.
4. `celery_worker_notify` $\rightarrow$ Updates status to `COMPLETED` and sends an email notification to the user.
5. **Error Handling:** If any step fails, the task is retried 3 times with exponential backoff before being marked as `FAILED` and alerting the team via Slack.