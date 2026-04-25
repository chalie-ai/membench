Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, industrial-grade Project Specification. It is structured to serve as the "Single Source of Truth" (SSoT) for the 12-person team at Bridgewater Dynamics.

***

# PROJECT SPECIFICATION: PROJECT INGOT
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/Draft  
**Owner:** Finn Kim (Tech Lead)  
**Company:** Bridgewater Dynamics  
**Industry:** Government Services  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Ingot is a comprehensive rebuild of the Bridgewater Dynamics educational Learning Management System (LMS). The project is born out of necessity following catastrophic user feedback regarding the legacy system, which suffered from systemic instability, an unintuitive UI, and prohibitive latency. Ingot is designed to transition the organization from a legacy monolithic failure to a modern, scalable, and modular platform capable of serving government-sector educational needs.

### 1.2 Business Justification
The current system has reached a state of technical insolvency. User churn rates have spiked by 40% in the last two quarters, and government contract renewals are at risk due to the platform's inability to handle concurrent user loads and its archaic navigation. The business justification for Ingot is three-fold:
1.  **Retention:** By rebuilding the UX from the ground up, we eliminate the "friction points" identified in the user feedback surveys.
2.  **Scalability:** The transition to AWS ECS and a modular architecture allows the system to scale horizontally, ensuring government agencies can onboard thousands of users without performance degradation.
3.  **Agility:** The implementation of a built-in A/B testing framework allows Bridgewater Dynamics to iterate based on real-time data rather than guesswork.

### 1.3 ROI Projection
The financial projection for Project Ingot is based on a recovery of lost contracts and the acquisition of new government service tenders. 
- **Direct Revenue Recovery:** Estimated $2.4M in retained annual recurring revenue (ARR) by preventing contract churn.
- **Operational Efficiency:** Reduction in support tickets by an estimated 60% through the implementation of intuitive workflows and self-service dashboard widgets.
- **Cost Reduction:** Transitioning from legacy on-premise servers to an optimized AWS ECS footprint is projected to reduce infrastructure overhead by 15% annually.
- **Projected ROI:** 310% over a 24-month period following the Production Launch (Milestone 2).

### 1.4 Strategic Alignment
Ingot aligns with Bridgewater Dynamics' goal of becoming the primary digital infrastructure provider for government educational services. By focusing on "high-trust, low-ceremony" development, the team is prioritizing speed-to-market and functional robustness over bureaucratic documentation, ensuring that the product reflects current user needs.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Ingot utilizes a **Modular Monolith** architecture. While the code resides in a single repository for deployment simplicity (via Django), the internal logic is strictly decoupled into domain-driven modules (e.g., `auth`, `course_engine`, `automation`, `billing`). This allows the team to incrementally migrate high-load modules into independent microservices as the user base grows toward the 10,000 MAU target.

### 2.2 Stack Specifications
- **Language/Framework:** Python 3.11 / Django 4.2 (LTS)
- **Primary Database:** PostgreSQL 15 (Managed RDS)
- **Caching/Message Broker:** Redis 7.0 (ElastiCache)
- **Containerization:** Docker 24.0
- **Orchestration:** AWS ECS (Fargate)
- **CDN:** Amazon CloudFront
- **Storage:** AWS S3 (Standard and Intelligent-Tiering)
- **CI/CD:** GitHub Actions

### 2.3 System Topology (ASCII Representation)
```text
[ User Browser ] <---> [ CloudFront CDN ] <---> [ Application Load Balancer ]
                                                         |
                                                         v
                                            ___________________________
                                           |      AWS ECS Cluster      |
                                           |  (Django Modular Monolith)|
                                           |___________________________|
                                               /         |          \
                                              v          v           v
                                     [ PostgreSQL ]  [ Redis ]  [ AWS S3 ]
                                     (User Data)    (Cache/Queues) (Files)
                                              ^
                                              |
                                     [ GitHub Actions CI/CD ]
                                     (Build -> Test -> Deploy)
```

### 2.4 Data Flow
1.  **Request:** User sends request via HTTPS.
2.  **Routing:** ALB routes request to an available ECS Task.
3.  **Processing:** Django processes the request. If the request requires a heavy operation (e.g., virus scanning a file), a task is pushed to Redis and handled by a Celery worker.
4.  **Persistence:** Data is committed to PostgreSQL via the Django ORM.
5.  **Response:** The final payload is returned as JSON or rendered HTML.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** Complete
**Description:** 
The Workflow Automation Engine allows administrators to create "If-This-Then-That" (IFTTT) style rules to automate student progression and administrative tasks. For example: *"If a student completes Course A and scores > 80%, then unlock Course B and send a notification to the supervisor."*

**Detailed Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface using React-Flow where admins can map triggers to actions.
- **Trigger Types:** Event-based triggers (e.g., `course_completed`, `login_count_reached`, `document_uploaded`).
- **Action Types:** System actions (e.g., `assign_role`, `send_email`, `update_status`).
- **Conditionals:** Logic gates supporting AND/OR operations and threshold comparisons (e.g., `score >= 80`).
- **Execution Engine:** A background worker system (Celery) that evaluates triggers against the database and executes actions asynchronously to prevent UI blocking.
- **Logging:** Every automated action must be logged in the `automation_audit` table for government auditing purposes.

**Technical Implementation:**
The engine uses a JSON-based logic schema stored in the `WorkflowRule` table. The `RuleEvaluator` class parses this JSON and uses Python’s `getattr` to dynamically check user attributes against defined thresholds.

### 3.2 A/B Testing Framework (Feature Flag System)
**Priority:** Critical | **Status:** In Progress (Launch Blocker)
**Description:** 
To avoid the catastrophic failure of the previous version, Ingot incorporates a native A/B testing framework. This allows the team to roll out new features to a subset of users (e.g., 5% of government employees) before a full release.

**Detailed Requirements:**
- **Feature Flagging:** Ability to toggle features on/off globally or per-user group via a management dashboard.
- **Bucket Allocation:** A deterministic hashing algorithm (using User ID) to ensure a user remains in the same "bucket" (A or B) throughout their session.
- **Metric Tracking:** Integration with the analytics pipeline to track conversion rates, click-through rates (CTR), and error rates for each variant.
- **Automatic Kill-Switch:** If the error rate for Variant B exceeds a threshold (e.g., 2% increase in 500 errors), the system must automatically revert all users to Variant A.
- **Configuration:** Flags should be stored in Redis for sub-millisecond retrieval during the request lifecycle.

**Technical Implementation:**
The framework uses a Django Middleware that checks for active flags in Redis before the view is rendered. The `ABTestEngine` class handles the distribution of users based on a seed value and a percentage weight.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Progress
**Description:** 
Government users must upload certifications and assignments. These files must be scanned for malware before being stored and then distributed via CDN for low-latency access.

**Detailed Requirements:**
- **Upload Pipeline:** Multi-part upload to a "Quarantine" S3 bucket.
- **Virus Scanning:** Integration with ClamAV via a dedicated Lambda function. Files are scanned upon upload; if a virus is detected, the file is deleted immediately, and the user is notified.
- **CDN Integration:** Once cleared, files are moved to the "Production" S3 bucket, which is served through Amazon CloudFront.
- **Access Control:** Signed URLs are required to ensure that only authorized users can access specific files.
- **File Constraints:** Support for PDF, DOCX, and JPG, with a maximum file size of 50MB per upload.

**Technical Implementation:**
`S3UploadService` manages the lifecycle. A S3 Event Notification triggers the `VirusScanLambda`. Upon a "Clean" result, the Lambda moves the object to the production bucket and updates the database record to `is_safe=True`.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** In Review
**Description:** 
A personalized landing page where users can arrange widgets (e.g., "My Courses," "Upcoming Deadlines," "Recent Grade Reports") according to their preference.

**Detailed Requirements:**
- **Widget Library:** A set of pre-defined components (CourseProgress, NotificationCenter, ResourceQuickLinks).
- **State Persistence:** The layout (position, size, and visibility of widgets) must be saved to the user's profile in the database.
- **Drag-and-Drop Interface:** Use of `react-grid-layout` to allow users to resize and rearrange widgets on a 12-column grid.
- **Widget API:** Each widget must have its own independent API endpoint to allow for lazy loading and independent refresh rates.
- **Default Templates:** Role-based default layouts (e.g., "Student View" vs. "Admin View").

**Technical Implementation:**
Layouts are stored as a JSON blob in the `UserProfile` table. The frontend fetches this JSON and maps it to the corresponding React components.

### 3.5 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** In Progress
**Description:** 
A secure system to manage user identities and permissions, ensuring that users only access data authorized for their specific government role.

**Detailed Requirements:**
- **Authentication:** Support for JWT (JSON Web Tokens) for stateless session management.
- **RBAC Levels:** 
    - `SuperAdmin`: Full system access.
    - `OrgAdmin`: Access to their specific government agency's data.
    - `Instructor`: Course management and grading.
    - `Student`: Course consumption and profile management.
- **Permission Mapping:** Fine-grained permissions (e.g., `can_edit_course`, `can_view_grades`).
- **Password Policy:** Complexity requirements (min 12 chars, mixed case, special chars) as per government standards.
- **Session Management:** Automatic session expiration after 30 minutes of inactivity.

**Technical Implementation:**
Extending Django's `AbstractUser` and using `django-guardian` for object-level permissions. Access is validated via a custom `@role_required` decorator on API views.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 Authentication
- **Endpoint:** `POST /auth/login/`
- **Request:** `{ "username": "jdoe", "password": "secretpassword" }`
- **Response:** `{ "token": "eyJhbG...", "expires_in": 3600, "user_role": "Student" }`
- **Description:** Validates credentials and returns a JWT.

### 4.2 Dashboard Layout
- **Endpoint:** `GET /user/dashboard/layout/`
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `{ "layout": [ {"i": "course_widget", "x": 0, "y": 0, "w": 4, "h": 2}, ... ] }`
- **Description:** Retrieves the current user's custom dashboard configuration.

### 4.3 Dashboard Update
- **Endpoint:** `PATCH /user/dashboard/layout/`
- **Request:** `{ "layout": [ {"i": "course_widget", "x": 2, "y": 0, "w": 4, "h": 2}, ... ] }`
- **Response:** `{ "status": "success", "updated_at": "2025-01-10T12:00:00Z" }`
- **Description:** Saves the new drag-and-drop layout.

### 4.4 File Upload
- **Endpoint:** `POST /files/upload/`
- **Request:** `Multipart/form-data { "file": Binary, "category": "assignment" }`
- **Response:** `{ "file_id": "file_9982", "status": "scanning", "upload_url": "..." }`
- **Description:** Uploads a file to the quarantine bucket for scanning.

### 4.5 File Status Check
- **Endpoint:** `GET /files/status/{file_id}/`
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `{ "file_id": "file_9982", "is_safe": true, "cdn_url": "https://cdn.ingot.gov/..." }`
- **Description:** Checks if ClamAV has cleared the file for production.

### 4.6 Workflow Trigger
- **Endpoint:** `POST /automation/trigger/`
- **Request:** `{ "event_type": "course_completed", "user_id": 456, "course_id": 101 }`
- **Response:** `{ "job_id": "celery_task_123", "status": "queued" }`
- **Description:** Manually triggers an automation rule (Admin only).

### 4.7 Feature Flag Status
- **Endpoint:** `GET /config/flags/`
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `{ "new_dashboard_v2": true, "beta_grading_system": false }`
- **Description:** Returns the flags enabled for the specific user's bucket.

### 4.8 User Role Update
- **Endpoint:** `PUT /admin/users/{user_id}/role/`
- **Request:** `{ "new_role": "Instructor" }`
- **Response:** `{ "user_id": 456, "role": "Instructor", "updated_by": "FinnKim" }`
- **Description:** Updates a user's RBAC role.

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | - | `email`, `password_hash`, `role_id` | Core user identity. |
| `Roles` | `role_id` | - | `role_name`, `permission_level` | RBAC role definitions. |
| `UserProfiles` | `profile_id` | `user_id` | `dashboard_json`, `timezone`, `bio` | User preferences and layout. |
| `Courses` | `course_id` | `instructor_id` | `title`, `description`, `version` | Educational course metadata. |
| `Enrollments` | `enroll_id` | `user_id`, `course_id` | `enrollment_date`, `completion_status` | Mapping of students to courses. |
| `Files` | `file_id` | `user_id` | `s3_path`, `is_safe`, `mime_type` | File metadata and scan status. |
| `WorkflowRules` | `rule_id` | `created_by` | `trigger_event`, `logic_json`, `is_active` | Automation logic definitions. |
| `AutomationLogs` | `log_id` | `rule_id`, `user_id` | `executed_at`, `outcome` | Audit trail for automation. |
| `FeatureFlags` | `flag_id` | - | `flag_name`, `percentage_rollout`, `is_enabled` | A/B test configurations. |
| `UserFlagBuckets` | `bucket_id` | `user_id`, `flag_id` | `assigned_variant` (A/B) | Mapping users to specific variants. |

### 5.2 Relationships
- **Users $\to$ UserProfiles:** 1:1 (Every user has one profile).
- **Roles $\to$ Users:** 1:N (One role can be assigned to many users).
- **Users $\to$ Enrollments $\to$ Courses:** M:N (Many users can enroll in many courses).
- **Users $\to$ Files:** 1:N (Users can upload multiple files).
- **WorkflowRules $\to$ AutomationLogs:** 1:N (One rule can trigger many logs).
- **FeatureFlags $\to$ UserFlagBuckets:** 1:N (One flag is mapped to many user buckets).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ingot utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and initial integration.
- **Infrastructure:** Small ECS cluster, shared PostgreSQL instance.
- **Deployment:** Triggered on merge to `develop` branch.
- **Data:** Anonymized subsets of production data.

#### 6.1.2 Staging (`stg`)
- **Purpose:** Pre-production testing, QA, and Legal/Compliance review.
- **Infrastructure:** Mirror of Production (Production-parity).
- **Deployment:** Triggered on merge to `release` branch.
- **Data:** Full copy of production data (sanitized).

#### 6.1.3 Production (`prd`)
- **Purpose:** Live customer-facing environment.
- **Infrastructure:** High-availability ECS cluster across 3 Availability Zones (AZs).
- **Deployment:** Blue-Green deployment strategy via GitHub Actions.
- **Traffic Shift:** Traffic is shifted 10% $\to$ 50% $\to$ 100% after health checks pass.

### 6.2 CI/CD Pipeline (GitHub Actions)
1.  **Lint/Test:** Every push triggers `flake8` and `pytest`.
2.  **Build:** Docker image is built and pushed to Amazon ECR.
3.  **Deploy (Staging):** Image is deployed to Staging.
4.  **Smoke Test:** Automated Selenium scripts verify core paths.
5.  **Approval:** Manual sign-off from Finn Kim.
6.  **Deploy (Prod):** Blue-Green shift to Production ECS.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Individual functions, model methods, and utility classes.
- **Tool:** `pytest` and `unittest.mock`.
- **Coverage Target:** 85% minimum.
- **Frequency:** Every commit.

### 7.2 Integration Testing
- **Focus:** API endpoint contracts, database migrations, and Redis cache consistency.
- **Tool:** `Django REST Framework` test suite.
- **Scope:** Verifying that the `WorkflowEngine` correctly updates the `UserProfiles` table upon a trigger.
- **Frequency:** Daily on the `develop` branch.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (The "Happy Path").
- **Tool:** `Playwright` or `Selenium`.
- **Scenarios:**
    - User logs in $\to$ drags a widget $\to$ refreshes $\to$ layout persists.
    - User uploads a file $\to$ file is scanned $\to$ user receives "Safe" notification.
    - Admin creates an automation rule $\to$ student completes course $\to$ rule executes.
- **Frequency:** Every release candidate in Staging.

### 7.4 Penetration Testing
- **Frequency:** Quarterly.
- **Scope:** OWASP Top 10, specifically targeting JWT hijacking and S3 bucket leakage.
- **Execution:** External contractor (Astrid Nakamura) performs "black-box" testing on the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key Architect leaving in 3 months | High | High | Accept risk; monitor weekly. Focus on documenting the modular monolith logic before departure. |
| **R2** | Regulatory requirements changing | Medium | High | Document workarounds in a shared Wiki; maintain a flexible schema for `UserProfiles`. |
| **R3** | "God Class" technical debt | High | Medium | Incremental refactoring: Extract authentication and logging into separate services over the next 2 sprints. |
| **R4** | Legal delay on Data Agreement | Medium | High | Blockers: Currently waiting on legal review. Team will focus on UI/UX features that don't require PII. |
| **R5** | Performance degradation at 10k MAU | Low | High | Implement Redis caching for all GET requests; use p95 monitoring to trigger auto-scaling. |

**Probability/Impact Matrix:**
- **Critical:** R1, R2 (Requires active monitoring).
- **Manageable:** R3, R4, R5 (Handled via standard sprints/legal follow-ups).

---

## 9. TIMELINE

### 9.1 Phase breakdown (Gantt-style)

**Phase 1: Core Foundation (Now $\to$ 2025-03-01)**
- [ ] Refactor "God Class" (Auth/Log/Email)
- [ ] Setup AWS ECS/RDS Infrastructure
- [ ] Implement RBAC and JWT Auth
- *Dependency: Legal review of Data Processing Agreement.*

**Phase 2: Feature Implementation (2025-03-02 $\to$ 2025-06-15)**
- [ ] Build Visual Rule Builder for Automation
- [ ] Implement S3/ClamAV Pipeline
- [ ] Develop A/B Testing Framework
- [ ] Build Drag-and-Drop Dashboard
- **Milestone 1: MVP Feature-Complete (2025-06-15)**

**Phase 3: Stabilization & Beta (2025-06-16 $\to$ 2025-08-15)**
- [ ] Load testing for 10,000 MAU
- [ ] Quarterly Pen-test by Astrid Nakamura
- [ ] Bug scrubbing and UI polishing
- **Milestone 2: Production Launch (2025-08-15)**

**Phase 4: Post-Launch Iteration (2025-08-16 $\to$ 2025-10-15)**
- [ ] Monitor A/B test results for Dashboard
- [ ] Transition first module to a microservice
- [ ] Finalize regulatory compliance docs
- **Milestone 3: Internal Alpha Release (2025-10-15)**

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom/Google Meet. These recordings are archived but historically ignored by the team. Decisions are finalized in Slack.*

### Meeting 1: Architecture Kickoff (2023-11-01)
- **Attendees:** Finn Kim, Ira Fischer, Quinn Fischer.
- **Discussion:** Debate over going full microservices immediately vs. modular monolith.
- **Decision:** Finn decided on a modular monolith to reduce initial complexity. Ira raised concerns about the `God class` (3,000 lines).
- **Outcome:** Decision made in Slack: "We'll carve the God class out as we build the Auth module."

### Meeting 2: Security & Compliance Review (2023-12-15)
- **Attendees:** Finn Kim, Quinn Fischer, Astrid Nakamura.
- **Discussion:** Discussion on whether to use a specific government compliance framework.
- **Decision:** Quinn noted that the requirements are still "fluid."
- **Outcome:** Decided to avoid locking into a framework and instead perform quarterly pen-tests to satisfy the current vague requirements.

### Meeting 3: A/B Framework Pivot (2024-02-10)
- **Attendees:** Finn Kim, Ira Fischer.
- **Discussion:** The original plan was to use a third-party tool (LaunchDarkly), but cost was too high for the variable budget.
- **Decision:** Build a native A/B framework into the feature flag system.
- **Outcome:** This became a "Critical/Launch Blocker" priority to ensure no repeat of the legacy system's failure.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the successful completion of Milestones 1, 2, and 3.

| Category | Allocation | Amount (Est.) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $1,260,000 | 12-person team (incl. Astrid's contract). |
| **Infrastructure** | 15% | $270,000 | AWS ECS, RDS, CloudFront, S3. |
| **Tools/Licenses** | 5% | $90,000 | GitHub Enterprise, IDEs, Monitoring tools. |
| **Contingency** | 10% | $180,000 | Reserved for regulatory shifts/emergency scaling. |
| **TOTAL** | **100%** | **$1,800,000** | *Variable based on tranche release.* |

---

## 12. APPENDICES

### Appendix A: "God Class" Refactoring Plan
The current `SystemManager` class handles authentication, logging, and email. It is 3,000 lines of spaghetti code.
- **Step 1:** Create `AuthService` and move all `login/logout/verify` methods.
- **Step 2:** Create `AuditLogger` and move all `log_event` methods.
- **Step 3:** Create `NotificationEngine` and move all `send_email/send_sms` methods.
- **Target Completion:** End of Phase 1.

### Appendix B: ClamAV Scan Logic
The virus scanning process follows a strict state machine:
1.  `UPLOADED` $\to$ File sits in `quarantine-bucket`.
2.  `SCANNING` $\to$ Lambda triggers `clamscan`.
3.  `CLEAN` $\to$ Move to `production-bucket` $\to$ Update DB `is_safe=True`.
4.  `INFECTED` $\to$ Delete file $\to$ Log security event $\to$ Notify user.
5.  `ERROR` $\to$ Retry 3 times $\to$ Manual review by Quinn Fischer.