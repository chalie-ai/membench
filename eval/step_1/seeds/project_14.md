Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, industrial-grade Project Specification Document. It is structured to serve as the "Single Source of Truth" (SSOT) for the development team at Coral Reef Solutions.

***

# PROJECT HARBINGER: OFFICIAL PROJECT SPECIFICATION
**Document Version:** 1.0.4  
**Status:** Draft/Review  
**Last Updated:** October 24, 2023  
**Classification:** Confidential / HIPAA Compliant  
**Project Lead:** Cleo Moreau (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Harbinger is a critical infrastructure transformation initiative for Coral Reef Solutions. The objective is the complete replacement of a 15-year-old legacy monolith that currently handles all educational administrative and student data. This legacy system, while stable, has become a bottleneck for innovation, suffering from extreme technical debt and an inability to scale with the company’s growing client base in the education sector.

The project involves migrating the existing monolithic architecture into a modernized API Gateway and Microservices ecosystem. Given that the entire company depends on this system, the mandate is **zero downtime tolerance**. Any outage during migration would result in significant financial loss and reputational damage within the education market.

### 1.2 Business Justification
The legacy system is currently built on an antiquated version of Ruby on Rails (v3.2) and a fragmented MySQL 5.5 instance. The primary drivers for this migration are:
1. **Scalability:** The current system cannot handle concurrent users during peak "enrollment seasons" (August/September), leading to p95 response times exceeding 4 seconds.
2. **Compliance:** As the company expands into healthcare-adjacent education (e.g., nursing certifications), HIPAA compliance is no longer optional; it is a prerequisite for new contracts.
3. **Agility:** Feature deployment currently takes 3 weeks due to a manual deployment process and a massive, fragile test suite.

### 1.3 ROI Projection
The transition to Project Harbinger is projected to deliver the following returns over a 24-month period:
- **Infrastructure Cost Reduction:** By moving from over-provisioned legacy hardware to a streamlined Heroku environment with optimized dynos, we expect a 15% reduction in monthly compute costs.
- **Developer Velocity:** Automation via GitHub Actions and the adoption of Hexagonal Architecture is projected to reduce "time-to-market" for new features from 21 days to 5 days.
- **Revenue Growth:** The ability to offer multi-tenant isolation (Feature 5) allows Coral Reef Solutions to enter the "Enterprise" market, targeting large school districts with contracts valued at $500k+ annually.
- **Risk Mitigation:** Eliminating the "single point of failure" monolith reduces the projected cost of unplanned outages (estimated at $12,000/hour) by approximately 90%.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Project Harbinger utilizes a Hexagonal Architecture to decouple the core business logic from external dependencies (databases, third-party APIs, and UI). This is critical given the unstable nature of our integration partners.

**The Core Domain:** Contains the business rules, entities, and use cases. It has no knowledge of MySQL or Heroku.
**The Ports:** Interfaces that define how the core interacts with the outside world (e.g., `UserRepository` interface).
**The Adapters:** Implementations of these ports (e.g., `MySQLUserRepository` or `ExternalPartnerAPIAdapter`).

### 2.2 ASCII Architecture Diagram
```text
[ CLIENT LAYER ]          [ API GATEWAY (Kong/Nginx) ]
      |                            |
      | (HTTPS/JSON)               | (Routing, Rate Limiting, Auth)
      v                            v
+-----------------------------------------------------------+
|                   MICROSERVICE BOUNDARY                   |
|                                                           |
|   +-------------------+        +---------------------+    |
|   |  Primary Adapter   | <----> |   Core Domain       |    |
|   | (REST Controllers) |        | (Business Logic)    |    |
|   +-------------------+        +---------------------+    |
|            ^                               ^              |
|            |                               |              |
|            v                               v              |
|   +-------------------+        +---------------------+    |
|   |  Secondary Adapter | <----> |    Port Interface    |    |
|   | (DB/External API)   |        | (Repository/Client)  |    |
|   +-------------------+        +---------------------+    |
+-----------------------------------------------------------+
      |                                       |
      v                                       v
[ MySQL 8.0 / RDS ]                  [ External Education API ]
 (Encrypted at Rest)                   (Buggy/Undocumented)
```

### 2.3 The Stack
- **Language/Framework:** Ruby on Rails 7.1 (API Mode).
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL Add-ons).
- **Deployment:** Heroku with Blue-Green deployment strategy.
- **CI/CD:** GitHub Actions for automated linting, testing, and deployment.
- **Security:** TLS 1.3 for transit; AES-256 for data at rest. All HIPAA-sensitive fields are encrypted at the application level using `lockbox`.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Functional Specification:**
The system must provide a centralized identity management service. Due to the multi-tenant nature of the education industry, the RBAC system must support hierarchical roles (e.g., Super Admin $\rightarrow$ District Admin $\rightarrow$ School Admin $\rightarrow$ Teacher $\rightarrow$ Student).

**Technical Requirements:**
- **JWT Implementation:** Use JSON Web Tokens (JWT) for stateless authentication. Tokens must include a `tenant_id` and `role_id` claim.
- **Password Hashing:** Argon2id for password hashing to ensure maximum resistance against GPU-based cracking.
- **Session Management:** Implementation of a "Revocation List" in Redis to allow immediate logout of compromised accounts.
- **RBAC Matrix:**
    - *Student:* Read-only access to their own grades/courses.
    - *Teacher:* Read/Write access to students in their assigned classrooms.
    - *District Admin:* Full management of all schools within their district.

**Acceptance Criteria:**
1. User can register and verify email via a signed token.
2. User can login and receive a JWT.
3. Requesting a resource without the required role returns a `403 Forbidden`.
4. Password reset flow includes multi-factor authentication (MFA) via SMS/Email.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** Not Started

**Functional Specification:**
Each user role requires a different set of KPIs. The dashboard must allow users to customize their view by adding, removing, and rearranging "widgets" (e.g., "Student Attendance Graph," "Upcoming Deadlines," "Grade Distribution").

**Technical Requirements:**
- **Frontend:** React.js with `react-grid-layout` for the drag-and-drop functionality.
- **Persistence:** A `dashboard_layouts` table in the database storing JSON blobs of the widget coordinates and IDs.
- **Widget API:** A polymorphic endpoint `/api/v1/widgets/{widget_type}/data` that fetches specific data based on the widget ID.
- **Caching:** Use Redis to cache widget data for 5 minutes to prevent overloading the MySQL DB during high-traffic morning login periods.

**Acceptance Criteria:**
1. User can drag a widget from the "Library" to the "Workspace."
2. Dashboard layout is persisted and loads identically across different browsers.
3. Widgets update their data in real-time via WebSockets (ActionCable).

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Not Started

**Functional Specification:**
To meet HIPAA and educational regulatory standards, every mutation (Create, Update, Delete) must be logged. These logs must be immutable; once written, they cannot be changed, even by a Super Admin.

**Technical Requirements:**
- **Interceptors:** Use Rails `around_action` or a custom Middleware to capture the `user_id`, `timestamp`, `request_payload`, and `ip_address`.
- **Tamper-Evidence:** Each log entry must contain a SHA-256 hash of (Current Entry + Hash of Previous Entry), creating a blockchain-like chain of custody.
- **Storage:** Logs are written to a separate "Audit DB" to ensure that a primary DB failure doesn't wipe the audit trail.
- **Archiving:** Logs older than 7 years are automatically moved to AWS S3 Glacier for long-term cold storage.

**Acceptance Criteria:**
1. Every change to a student's record creates an entry in the `audit_logs` table.
2. Attempting to manually edit an audit log entry triggers a checksum failure alert.
3. Audit reports can be exported as signed PDFs.

### 3.4 Notification System (Email, SMS, In-App, Push)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Functional Specification:**
A unified notification engine to alert users of critical events (e.g., grade changes, appointment reminders, system alerts). The system must support "channel preference" where a user can opt-out of SMS but stay opted-in for Email.

**Technical Requirements:**
- **Architecture:** Asynchronous processing using Sidekiq and Redis.
- **Adapters:** 
    - Email $\rightarrow$ SendGrid
    - SMS $\rightarrow$ Twilio
    - Push $\rightarrow$ Firebase Cloud Messaging (FCM)
- **Queue Strategy:** Use priority queues (`high`, `default`, `low`). Password resets go to `high`; weekly newsletters go to `low`.
- **Throttling:** Implement a "Cooldown" period to prevent spamming users (max 3 push notifications per hour).

**Acceptance Criteria:**
1. Triggering an event in the core domain sends a notification to the correct channel based on user settings.
2. Failures in the Twilio API do not crash the main application (graceful degradation).
3. Notification status (Sent, Delivered, Read) is tracked in the database.

### 3.5 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** High | **Status:** In Design

**Functional Specification:**
The system must support thousands of separate educational institutions (Tenants) on a single set of servers. Data from "School A" must never be visible to "School B," even in the event of a developer error in a SQL query.

**Technical Requirements:**
- **Isolation Strategy:** Row-Level Security (RLS) via a `tenant_id` column on every table.
- **Global Scope:** Implement a `default_scope` in the Rails models to automatically append `WHERE tenant_id = X` to all queries.
- **Connection Switching:** Use a custom middleware that identifies the tenant based on the subdomain (e.g., `springfield.coralreef.edu`) and sets the `Current.tenant` variable.
- **Schema Design:** A shared-schema approach to minimize the overhead of managing 1,000+ separate MySQL databases.

**Acceptance Criteria:**
1. A user from Tenant A cannot access a record from Tenant B via a direct ID guess (IDOR attack).
2. Adding a new tenant requires zero database migrations.
3. Tenant-specific configuration (e.g., custom logos, timezones) is correctly applied.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions. Headers required for all requests:
- `Authorization: Bearer <JWT>`
- `X-Tenant-ID: <UUID>`
- `Content-Type: application/json`

### 4.1 Authentication
**Endpoint:** `POST /api/v1/auth/login`
- **Request:** `{"email": "user@example.edu", "password": "securepassword123"}`
- **Response (200):** `{"token": "eyJhbG...", "expires_at": "2023-10-24T12:00:00Z", "user": {"id": 1, "role": "teacher"}}`
- **Response (401):** `{"error": "Invalid credentials"}`

### 4.2 User Profile
**Endpoint:** `GET /api/v1/users/me`
- **Response (200):** `{"id": 1, "name": "Jane Doe", "email": "jane@example.edu", "role": "teacher", "tenant_id": "uuid-123"}`

### 4.3 Student Records (List)
**Endpoint:** `GET /api/v1/students?classroom_id=505`
- **Response (200):** `{"data": [{"id": 101, "name": "Alice", "grade": "A"}, {"id": 102, "name": "Bob", "grade": "B"}]}`
- **Response (403):** `{"error": "Insufficient permissions to view this classroom"}`

### 4.4 Student Records (Update)
**Endpoint:** `PATCH /api/v1/students/{id}`
- **Request:** `{"grade": "A+"}`
- **Response (200):** `{"id": 101, "status": "updated", "updated_at": "2023-10-24T10:00:00Z"}`

### 4.5 Dashboard Layout
**Endpoint:** `POST /api/v1/dashboard/layout`
- **Request:** `{"widgets": [{"id": "grade_chart", "x": 0, "y": 0, "w": 4, "h": 2}]}`
- **Response (201):** `{"status": "layout saved"}`

### 4.6 Notification Preferences
**Endpoint:** `PUT /api/v1/settings/notifications`
- **Request:** `{"email": true, "sms": false, "push": true}`
- **Response (200):** `{"status": "preferences updated"}`

### 4.7 Audit Log Retrieval
**Endpoint:** `GET /api/v1/audit/logs?start_date=2023-01-01&end_date=2023-01-31`
- **Response (200):** `{"logs": [{"id": 5001, "action": "UPDATE", "target": "student_101", "timestamp": "..."}]}`

### 4.8 Tenant Onboarding
**Endpoint:** `POST /api/v1/admin/tenants`
- **Request:** `{"institution_name": "North High", "admin_email": "admin@northhigh.edu"}`
- **Response (201):** `{"tenant_id": "uuid-999", "status": "created"}`

---

## 5. DATABASE SCHEMA

The database uses MySQL 8.0. All tables include `created_at` and `updated_at` timestamps.

### 5.1 Table Definitions

1. **`tenants`**
   - `id` (UUID, PK)
   - `name` (Varchar 255)
   - `subdomain` (Varchar 63, Unique)
   - `plan_level` (Enum: Basic, Pro, Enterprise)
   - `created_at` (Timestamp)

2. **`users`**
   - `id` (BigInt, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
   - `email` (Varchar 255, Unique)
   - `password_digest` (Varchar 255)
   - `role_id` (Int, FK $\rightarrow$ roles.id)
   - `mfa_secret` (Varchar 255, Encrypted)

3. **`roles`**
   - `id` (Int, PK)
   - `name` (Varchar 50) - e.g., 'Student', 'Teacher'
   - `hierarchy_level` (Int)

4. **`permissions`**
   - `id` (Int, PK)
   - `action` (Varchar 100) - e.g., 'students.write'

5. **`role_permissions`**
   - `role_id` (Int, FK)
   - `permission_id` (Int, FK)

6. **`students`**
   - `id` (BigInt, PK)
   - `tenant_id` (UUID, FK)
   - `user_id` (BigInt, FK $\rightarrow$ users.id)
   - `current_grade_level` (Int)
   - `encrypted_ssn` (Varchar 255, Encrypted)

7. **`classrooms`**
   - `id` (BigInt, PK)
   - `tenant_id` (UUID, FK)
   - `teacher_id` (BigInt, FK $\rightarrow$ users.id)
   - `subject` (Varchar 100)

8. **`dashboard_layouts`**
   - `id` (BigInt, PK)
   - `user_id` (BigInt, FK $\rightarrow$ users.id)
   - `layout_json` (JSON)
   - `updated_at` (Timestamp)

9. **`notifications`**
   - `id` (BigInt, PK)
   - `user_id` (BigInt, FK)
   - `message` (Text)
   - `channel` (Enum: email, sms, push, inapp)
   - `is_read` (Boolean)

10. **`audit_logs`**
    - `id` (BigInt, PK)
    - `tenant_id` (UUID, FK)
    - `user_id` (BigInt, FK)
    - `action` (Varchar 50)
    - `payload` (JSON)
    - `prev_hash` (Varchar 64)
    - `current_hash` (Varchar 64)

### 5.2 Relationships
- **One-to-Many:** `Tenants` $\rightarrow$ `Users`, `Tenants` $\rightarrow$ `Students`, `Users` $\rightarrow$ `Notifications`.
- **Many-to-Many:** `Roles` $\leftrightarrow$ `Permissions` (via `role_permissions`).
- **One-to-One:** `Users` $\rightarrow$ `DashboardLayouts`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Harbinger utilizes a three-tier environment strategy to ensure stability and zero downtime.

**1. Development (Dev):**
- **Purpose:** Feature iteration and local testing.
- **Infrastructure:** Local Docker containers mimicking Heroku.
- **Deployment:** Manual push to `dev` branch.
- **Database:** Seeded with anonymized data.

**2. Staging (Stage):**
- **Purpose:** Pre-production validation, QA, and User Acceptance Testing (UAT).
- **Infrastructure:** Heroku Staging Dynos.
- **Deployment:** Automated via GitHub Actions upon merge to `develop` branch.
- **Data:** A sanitized clone of production data (HIPAA-stripped).

**3. Production (Prod):**
- **Purpose:** Live customer traffic.
- **Infrastructure:** Heroku Performance Dynos with Auto-scaling.
- **Deployment:** Blue-Green Deployment.
    - **Blue:** Current live version.
    - **Green:** New version.
    - Traffic is shifted via the Load Balancer only after health checks pass.

### 6.2 CI/CD Pipeline
1. **Push:** Developer pushes code to GitHub.
2. **Lint/Test:** GitHub Actions runs RuboCop and RSpec.
3. **Build:** Docker image is built and scanned for vulnerabilities.
4. **Deploy to Stage:** Code is deployed to the Staging environment.
5. **Smoke Test:** Automated Selenium tests verify critical paths.
6. **Production Promotion:** Manual approval triggers the Blue-Green switch in Production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Core business logic in the Domain layer.
- **Tool:** RSpec.
- **Requirement:** 90% code coverage for all Domain Services. Mocks/Stubs are used for all Ports (Adapters).

### 7.2 Integration Testing
- **Focus:** Port implementations (Adapters).
- **Approach:** Testing the actual interaction between the application and the MySQL database or Third-Party APIs.
- **Tool:** FactoryBot for data setup; VCR for recording and replaying API responses from the integration partner to avoid rate-limit blocks.

### 7.3 End-to-End (E2E) Testing
- **Focus:** User journeys (e.g., "Student logs in $\rightarrow$ checks grade $\rightarrow$ receives notification").
- **Tool:** Cypress.
- **Scenario:** Critical paths (Auth, Dashboard, Tenant switching) are tested in the Staging environment before every production release.

### 7.4 Performance Testing
- **Tool:** k6.
- **Goal:** Validate that p95 response times remain under 200ms at a simulated load of 5,000 concurrent users.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Project sponsor rotating out of role | High | Critical | Establish a "Steering Committee" of three executives instead of one. Create a detailed fallback architecture document. |
| R2 | Integration partner API is buggy/undocumented | High | High | Assign Ola Stein (Contractor) as the dedicated "Integration Owner" to reverse-engineer the API and build a wrapper. |
| R3 | Third-party API rate limits blocking tests | Critical | Medium | Implement a Mock Server for testing; request a higher rate limit for the staging IP address. |
| R4 | Raw SQL technical debt causing migration failure | Medium | High | Audit all raw SQL queries. Convert to Arel or ActiveRecord. Implement "Shadow Writes" during the migration phase. |
| R5 | HIPAA compliance breach | Low | Catastrophic | Regular third-party security audits; mandatory encryption for all PII; strict IAM roles on Heroku. |

---

## 9. TIMELINE AND PHASES

### Phase 1: Foundation (Oct 2023 - Jan 2024)
- **Focus:** Infrastructure setup and Auth.
- **Dependencies:** Heroku account setup $\rightarrow$ RBAC implementation.
- **Key Deliverable:** Working JWT auth and multi-tenant scaffolding.

### Phase 2: Core Feature Development (Feb 2024 - April 2024)
- **Focus:** Notifications and Dashboard.
- **Dependencies:** Auth $\rightarrow$ Notifications $\rightarrow$ Dashboard.
- **Key Deliverable:** Beta version of the user dashboard.

### Phase 3: Hardening and Migration (May 2024 - May 2025)
- **Focus:** Audit logs and Data Migration.
- **Dependencies:** Data cleaning $\rightarrow$ Shadow writes $\rightarrow$ Final cut-over.
- **Milestone 1 (2025-05-15):** Production Launch.

### Phase 4: Post-Launch & Audit (June 2025 - Sept 2025)
- **Milestone 2 (2025-07-15):** Security audit passed.
- **Milestone 3 (2025-09-15):** First paying customer onboarded.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-10-12  
**Attendees:** Cleo Moreau, Luciano Jensen, Xavi Jensen, Ola Stein  
**Discussion:**
- Cleo emphasized the "Zero Downtime" requirement.
- Luciano proposed Blue-Green deployments via Heroku to mitigate risk.
- Xavi raised concerns about the drag-and-drop dashboard performance on mobile devices.
- Ola pointed out that the current integration partner API returns inconsistent JSON formats.

**Action Items:**
- [Luciano] Set up the GitHub Actions pipeline for the `dev` branch. (Due: 2023-10-20)
- [Ola] Document the known bugs in the integration partner's API. (Due: 2023-10-25)
- [Xavi] Create Figma prototypes for the widget system. (Due: 2023-10-30)

### Meeting 2: The "Raw SQL" Crisis
**Date:** 2023-11-05  
**Attendees:** Cleo Moreau, Luciano Jensen, Ola Stein  
**Discussion:**
- The team discovered that 30% of the legacy queries bypass the ORM.
- Luciano warned that running standard migrations could break these queries.
- Cleo decided that any raw SQL must be documented in a "Technical Debt Registry" and rewritten as Rails queries before the May 2025 launch.

**Action Items:**
- [Luciano] Script a grep search to find all instances of `execute("SELECT...` in the legacy codebase. (Due: 2023-11-10)
- [Cleo] Review the budget for additional contractor help if the SQL cleanup takes too long. (Due: 2023-11-15)

### Meeting 3: Rate Limit Blocker
**Date:** 2023-12-01  
**Attendees:** Cleo Moreau, Luciano Jensen, Ola Stein  
**Discussion:**
- The team is currently blocked by the integration partner's 100 req/min limit during integration tests.
- Ola suggested using VCR for recording responses.
- Cleo will contact the partner's CTO to request a dedicated sandbox environment.

**Action Items:**
- [Ola] Implement VCR for all integration tests. (Due: 2023-12-05)
- [Cleo] Email partner CTO regarding sandbox access. (Due: 2023-12-02)

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the successful completion of milestones.

| Category | Allocated Amount | Funding Tranche | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $1,200,000 | Q1-Q4 2024 | Salaries for 20+ staff across 3 departments. |
| **Infrastructure** | $150,000 | Annual | Heroku Performance Dynos, Redis, MySQL. |
| **Tools/Licensing** | $45,000 | Upfront | SendGrid, Twilio, GitHub Enterprise, Datadog. |
| **Security Audit** | $80,000 | Pre-Milestone 2 | External penetration testing and HIPAA certification. |
| **Contingency** | $200,000 | Variable | Reserved for "Risk 1" fallback architecture. |
| **Total** | **$1,675,000** | | |

---

## 12. APPENDICES

### Appendix A: Data Migration Strategy (Shadow Writes)
To achieve zero downtime, we will use the "Shadow Write" pattern:
1. **Phase 1:** Update the legacy system to write all new data to both the legacy MySQL DB and the new Harbinger DB.
2. **Phase 2:** Run a background migration script to copy historical data from legacy $\rightarrow$ Harbinger.
3. **Phase 3:** Implement "Read-Verification," where the system reads from both DBs and logs a warning if the data differs.
4. **Phase 4:** Once data parity is 100%, flip the read switch to Harbinger and deprecate the legacy DB.

### Appendix B: HIPAA Encryption Standard
All PII (Personally Identifiable Information) must be encrypted.
- **Algorithm:** AES-256-GCM.
- **Key Management:** Keys are stored in Heroku Config Vars (encrypted at rest) and rotated every 90 days.
- **Field Level:** Only the `students.encrypted_ssn` and `users.mfa_secret` are encrypted at the field level; the rest of the database is encrypted at the volume level.