Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification Document (PSD). It is structured as the "Single Source of Truth" for the development team at Ridgeline Platforms.

***

# PROJECT SPECIFICATION: BEACON LMS
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 26, 2023  
**Project Lead:** Chandra Santos (CTO)  
**Company:** Ridgeline Platforms  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Beacon" is the strategic initiative to modernize the core educational infrastructure of Ridgeline Platforms. For fifteen years, the company has relied on a monolithic legacy system that has reached its end-of-life. This legacy system is the backbone of the company's service delivery; however, its fragility, lack of scalability, and outdated tech stack have become operational liabilities. Beacon is not merely a software upgrade but a complete architectural pivot designed to provide a seamless, scalable, and globally distributed Learning Management System (LMS).

### 1.2 Business Justification
The current legacy system suffers from significant "technical rot," characterized by undocumented dependencies and a lack of API parity with modern educational tools. The business risk of maintaining the status quo includes increased downtime, inability to scale to new markets, and a growing gap in regulatory compliance. Because the entire company depends on this system, the transition must be executed with **zero downtime tolerance**. Any outage during the migration would result in immediate revenue loss and catastrophic damage to customer trust.

### 1.3 ROI Projection
The investment of $800,000 is projected to yield a positive ROI within 18 months post-launch based on the following drivers:
1. **Reduction in Operational Overhead:** By moving to a Cloudflare Workers-based edge architecture, infrastructure costs are projected to drop by 30% compared to the current legacy server maintenance.
2. **Market Expansion:** With the "Critical" priority on localization (12 languages), Beacon opens the door to non-English speaking markets, projecting a 25% increase in total addressable market (TAM).
3. **Developer Velocity:** Transitioning from a legacy monolith to a micro-frontend architecture allows independent team ownership, reducing the lead time for new feature deployments from monthly cycles to a strict weekly release train.
4. **Customer Retention:** Improving the UX and stability is expected to drive the Net Promoter Score (NPS) above 40, reducing churn by an estimated 15%.

### 1.4 Strategic Goals
The primary objective is to migrate 100% of the legacy user base to Beacon by October 15, 2025, while achieving a target of 10,000 Monthly Active Users (MAU) within the first six months.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Beacon utilizes a cutting-edge, distributed architecture designed for high availability and low latency. The system departs from traditional centralized servers in favor of an "Edge-First" approach.

**The Tech Stack:**
- **Backend:** Rust (compiled to WebAssembly for Cloudflare Workers). Rust was chosen for its memory safety, performance, and ability to handle high concurrency without the overhead of a garbage collector.
- **Frontend:** React (Version 18.x) utilizing a Micro-Frontend (MFE) architecture. Each core module (Auth, Course Management, Reporting) is developed and deployed as an independent fragment.
- **Edge Data:** SQLite (via Cloudflare D1). This allows for low-latency read/write operations at the edge, ensuring the LMS remains responsive regardless of the user's geographic location.
- **Deployment:** Cloudflare Workers / Pages.

### 2.2 Architectural Diagram (ASCII Representation)
The following represents the request flow from the end-user to the data layer:

```text
[ End User / Browser ]
       |
       v
[ Cloudflare Global Edge Network ] <--- (DNS / SSL Termination)
       |
       +---------------------------------------+
       |       Micro-Frontend (MFE) Layer       |
       |  (React Fragments / Module Federation) |
       +---------------------------------------+
       |
       v
[ Cloudflare Workers (Rust/Wasm) ] <--- (Business Logic / API Gateway)
       |
       +------------------+------------------+
       |                  |                  |
[ SQLite (D1 Edge) ] [ External Auth ] [ Object Storage ]
(User Profiles/State) (SAML/OIDC/SSO) (Course Content/PDFs)
```

### 2.3 Micro-Frontend Strategy
To avoid the "distributed monolith" trap, Beacon implements independent team ownership. Each feature set is encapsulated in its own repository and deployed via a shared shell.
- **Shell App:** Handles global state, navigation, and the release train coordination.
- **Feature Fragments:** Independent React applications that are lazy-loaded based on the user's route.

### 2.4 Deployment Model: The Release Train
Beacon adheres to a strict **Weekly Release Train**. 
- **Schedule:** Every Tuesday at 04:00 UTC.
- **Constraint:** No exceptions. If a feature is not ready by the cutoff (Monday 12:00 UTC), it misses the train.
- **Hotfixes:** Forbidden outside the train. Any "critical" bug is patched in the next Tuesday release unless it constitutes a Total System Outage (TSO), in which case the CTO (Chandra Santos) must provide written override.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and RBAC
**Priority:** High | **Status:** Complete  
**Description:** A robust identity management system providing secure access and granular permissioning.

Because Beacon is a multi-tenant educational platform, the Role-Based Access Control (RBAC) must be flexible. The system implements a "Permission-Set" model rather than a simple "Role" model. A "Teacher" role is simply a collection of permissions (e.g., `course.create`, `grade.edit`, `student.view`).

**Technical Implementation:**
- **JWT Tokens:** Authentication is handled via signed JSON Web Tokens (JWT) stored in HttpOnly cookies.
- **Claims:** The JWT includes a `perms` claim containing a bitmask of the user's active permissions to minimize database lookups on every request.
- **Role Hierarchies:**
    - *Super Admin:* Full system access, billing, and global configuration.
    - *Organization Admin:* Access to all users and courses within a specific corporate or school entity.
    - *Instructor:* Access to assigned courses and student rosters.
    - *Student:* Access to enrolled courses and personal progress reports.
    - *Auditor:* Read-only access to compliance logs (Required for HIPAA).

**Edge Integration:**
The Rust backend validates the JWT at the edge. If a user's role is revoked in the central SQLite store, a "blacklist" entry is propagated to all edge nodes via Cloudflare KV within seconds, ensuring immediate access revocation.

---

### 3.2 Localization and Internationalization (i18n)
**Priority:** Critical | **Status:** In Review (Launch Blocker)  
**Description:** Full support for 12 languages to enable global market penetration.

This is a launch blocker. The system must not only translate UI text but also handle locale-specific formatting for dates, currencies, and numbers.

**Technical Implementation:**
- **Framework:** `react-i18next` for the frontend and a custom Rust `i18n` crate for backend error messages.
- **Translation Files:** JSON-based translation keys stored in the edge KV store for instant updates without redeploying code.
- **Language Set:** English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Arabic, Hindi, Russian, and Italian.
- **Dynamic Routing:** URLs will follow the pattern `/locale/dashboard` (e.g., `/es/dashboard`).
- **Right-to-Left (RTL) Support:** The CSS framework must utilize logical properties (e.g., `margin-inline-start` instead of `margin-left`) to support Arabic and Hebrew.

**Quality Assurance:**
Localization is not considered "Complete" until it has passed "Linguistic QA" by a native speaker. The "In Review" status indicates that the technical infrastructure is ready, but the actual translation strings for 4 of the 12 languages are still pending verification.

---

### 3.3 SSO Integration (SAML and OIDC)
**Priority:** Medium | **Status:** Blocked  
**Description:** Integration with Enterprise Identity Providers (IdPs) to allow single sign-on.

**The Block:** This feature is currently blocked due to a design disagreement between the Product Lead and Engineering Lead regarding whether to build a custom integration layer or use a third-party proxy like Auth0 or Okta.

**Technical Specification (Proposed):**
- **OIDC (OpenID Connect):** Support for Google Workspace, Microsoft Azure AD, and GitHub.
- **SAML 2.0:** Support for legacy corporate IdPs.
- **Flow:**
    1. User enters email.
    2. System identifies the domain and redirects to the corresponding IdP.
    3. IdP authenticates and sends a signed assertion back to the Beacon callback endpoint.
    4. Beacon validates the assertion and maps the IdP attributes (email, name, department) to the internal RBAC system.
- **Just-In-Time (JIT) Provisioning:** Users who exist in the IdP but not in Beacon's database will be automatically created upon their first successful login, assigning them a "Default Student" role.

---

### 3.4 Workflow Automation Engine
**Priority:** Low | **Status:** Not Started  
**Description:** A visual rule builder allowing administrators to automate educational workflows.

**Functionality:**
The engine will allow "If-This-Then-That" (IFTTT) logic for course management.
- *Example Rule:* "IF student completes Module 1 AND score > 80%, THEN unlock Module 2 AND send email notification to Instructor."

**Technical Design:**
- **Visual Builder:** A React-based drag-and-drop interface using `React Flow`.
- **Execution Engine:** A background worker in Rust that listens for "Event Triggers" (e.g., `COURSE_COMPLETED`).
- **Rule Storage:** Rules are stored as JSON logic trees in SQLite.
- **Rate Limiting:** To prevent infinite loops (e.g., Rule A triggers Rule B, which triggers Rule A), the engine will implement a maximum execution depth of 5 steps.

---

### 3.5 Two-Factor Authentication (2FA) with Hardware Keys
**Priority:** Low | **Status:** Not Started  
**Description:** Enhanced security for administrative accounts, supporting WebAuthn and hardware keys.

**Technical Specification:**
- **WebAuthn API:** Implementation of the FIDO2 standard to allow users to register Yubikeys or biometric authenticators (TouchID/FaceID).
- **Fallback Mechanism:** While hardware keys are the priority, the system will provide TOTP (Time-based One-Time Password) via apps like Google Authenticator as a fallback.
- **Recovery Codes:** Upon 2FA activation, the system generates ten one-time-use recovery codes. These are hashed using Argon2 and stored in the database.
- **Enforcement:** Super Admins will be *required* to enable 2FA; for students, it will be optional.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are RESTful and communicate via JSON. Base URL: `https://api.beacon.ridgeline.io/v1`

### 4.1 Authentication
- **`POST /auth/login`**
    - **Request:** `{ "email": "string", "password": "string" }`
    - **Response:** `200 OK` `{ "token": "jwt_string", "user": { "id": "uuid", "role": "student" } }`
- **`POST /auth/logout`**
    - **Request:** Headers only (Cookie)
    - **Response:** `204 No Content`

### 4.2 User Management
- **`GET /users/me`**
    - **Request:** Header `Authorization: Bearer <token>`
    - **Response:** `200 OK` `{ "id": "uuid", "email": "user@email.com", "locale": "en-US", "permissions": ["course.read"] }`
- **`PATCH /users/me/profile`**
    - **Request:** `{ "display_name": "string", "timezone": "string" }`
    - **Response:** `200 OK` `{ "status": "updated" }`

### 4.3 Course Management
- **`GET /courses`**
    - **Request:** Query params `?page=1&limit=20&search=rust`
    - **Response:** `200 OK` `{ "data": [ { "id": "uuid", "title": "Advanced Rust", "instructor": "id" } ], "total": 150 }`
- **`POST /courses`**
    - **Request:** `{ "title": "string", "description": "string", "category_id": "uuid" }`
    - **Response:** `201 Created` `{ "course_id": "uuid" }`

### 4.4 Localization
- **`GET /i18n/translations/{locale}`**
    - **Request:** `GET /i18n/translations/fr`
    - **Response:** `200 OK` `{ "welcome_msg": "Bienvenue", "login_btn": "Connexion" }`

### 4.5 Compliance/Audit
- **`GET /audit/logs`**
    - **Request:** Query params `?start_date=2025-01-01&end_date=2025-01-31`
    - **Response:** `200 OK` `{ "logs": [ { "timestamp": "iso8601", "action": "USER_LOGIN", "user_id": "uuid", "ip": "1.2.3.4" } ] }`

---

## 5. DATABASE SCHEMA

The system uses SQLite (via Cloudflare D1). Relationships are enforced at the application level in Rust.

### 5.1 Table Definitions

1. **`users`**
   - `id`: UUID (PK)
   - `email`: String (Unique, Indexed)
   - `password_hash`: String (Argon2id)
   - `role_id`: UUID (FK -> roles)
   - `locale`: String (Default: 'en-US')
   - `created_at`: Timestamp
   - `updated_at`: Timestamp

2. **`roles`**
   - `id`: UUID (PK)
   - `role_name`: String (e.g., 'Instructor')
   - `description`: String

3. **`permissions`**
   - `id`: UUID (PK)
   - `perm_key`: String (e.g., 'course.edit')
   - `description`: String

4. **`role_permissions`**
   - `role_id`: UUID (FK -> roles)
   - `perm_id`: UUID (FK -> permissions)
   - (Composite PK: role_id, perm_id)

5. **`courses`**
   - `id`: UUID (PK)
   - `title`: String
   - `description`: Text
   - `instructor_id`: UUID (FK -> users)
   - `is_published`: Boolean
   - `created_at`: Timestamp

6. **`modules`**
   - `id`: UUID (PK)
   - `course_id`: UUID (FK -> courses)
   - `title`: String
   - `order_index`: Integer
   - `is_locked`: Boolean

7. **`lessons`**
   - `id`: UUID (PK)
   - `module_id`: UUID (FK -> modules)
   - `content_url`: String (Link to Object Storage)
   - `content_type`: String (PDF, Video, Quiz)
   - `order_index`: Integer

8. **`enrollments`**
   - `id`: UUID (PK)
   - `user_id`: UUID (FK -> users)
   - `course_id`: UUID (FK -> courses)
   - `status`: String (Active, Completed, Dropped)
   - `enrolled_at`: Timestamp

9. **`progress`**
   - `id`: UUID (PK)
   - `user_id`: UUID (FK -> users)
   - `lesson_id`: UUID (FK -> lessons)
   - `completed_at`: Timestamp
   - `score`: Float

10. **`audit_logs`** (HIPAA Requirement)
    - `id`: UUID (PK)
    - `user_id`: UUID (FK -> users)
    - `action`: String
    - `resource_id`: String
    - `timestamp`: Timestamp
    - `ip_address`: String
    - `user_agent`: String

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Pipeline
Beacon utilizes three distinct environments to ensure stability and zero-downtime transitions.

1. **Development (`dev.beacon.ridgeline.io`)**
   - **Purpose:** Feature experimentation and unit testing.
   - **Deployment:** Triggered on every push to `develop` branch.
   - **Data:** Mock data generated by seed scripts.

2. **Staging (`staging.beacon.ridgeline.io`)**
   - **Purpose:** Pre-production validation, QA testing, and stakeholder review.
   - **Deployment:** Triggered on merge to `release` branch.
   - **Data:** Anonymized production clone (HIPAA compliant) updated weekly.

3. **Production (`app.beacon.ridgeline.io`)**
   - **Purpose:** Live user traffic.
   - **Deployment:** Weekly Release Train (Tuesdays).
   - **Strategy:** Blue-Green Deployment via Cloudflare Workers. The "Green" version is warmed up, then traffic is shifted 10% $\rightarrow$ 50% $\rightarrow$ 100% based on health checks.

### 6.2 HIPAA Compliance and Security
- **Data at Rest:** All SQLite data is encrypted using AES-256 at the storage layer provided by Cloudflare.
- **Data in Transit:** TLS 1.3 is mandatory for all connections.
- **Access Logs:** Every request to a HIPAA-protected resource is logged in the `audit_logs` table, including the user ID and the specific record accessed.
- **Secrets Management:** No keys are stored in code. All secrets (API keys, DB credentials) are managed via Cloudflare Workers Secrets.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (Rust & React)
- **Backend:** Every Rust module must have accompanying `#[cfg(test)]` blocks. Target coverage: 85%. Focus on business logic, permission checks, and data transformation.
- **Frontend:** Jest and React Testing Library for component-level tests. Focus on state transitions and prop-drilling.

### 7.2 Integration Testing
- **API Testing:** Using Pytest and Request to simulate end-to-end API calls against the `dev` environment.
- **Database Migrations:** A dedicated suite of tests that runs migration scripts and verifies schema integrity before any deployment to Staging.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys:
    1. Student login $\rightarrow$ Course Enrollment $\rightarrow$ Lesson Completion.
    2. Admin login $\rightarrow$ Course Creation $\rightarrow$ Student Assignment.
    3. SSO Login $\rightarrow$ Dashboard Access.
- **Frequency:** Run against Staging every Monday during the "Release Candidate" window.

### 7.4 QA Process (Finn Kim's Mandate)
The QA Lead (Finn Kim) has "Veto Power" over the release train. If a "Blocker" or "Critical" bug is found in Staging, the release is scrapped for that week, and the team reverts to the last stable version.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R1 | Scope creep from stakeholders adding 'small' features | High | Medium | Hire a dedicated contractor to increase bandwidth and reduce bus factor. | Chandra Santos |
| R2 | Regulatory (HIPAA) requirements change mid-build | Medium | High | Assign a dedicated Compliance Owner to track legal changes weekly. | Greta Moreau |
| R3 | Zero-downtime migration failure | Low | Critical | Implementation of Blue-Green deployment and a 1-click rollback script. | Ravi Liu |
| R4 | Designer/Eng lead disagreement stalls UI | High | Medium | Establish a "Tie-breaker" vote by the CTO within 48 hours of dispute. | Chandra Santos |
| R5 | Memory leaks in Rust Wasm modules | Low | Medium | Implement strict memory profiling in Staging using `wasm-bindgen` tools. | Ravi Liu |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal catastrophe.
- **High:** Significant delay or budget overrun.
- **Medium:** Manageable delay; requires resource reallocation.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project is divided into three main phases over 6 months.

### Phase 1: Foundation & Core Infrastructure (Now – June 15, 2025)
- **Focus:** Rust backend setup, SQLite schema implementation, and MFE shell.
- **Dependencies:** Completion of the Architecture Review.
- **Key Date:** **June 15, 2025 (Milestone 1: Architecture Review Complete)**.

### Phase 2: Feature Build-out (June 16 – August 15, 2025)
- **Focus:** Localization (Critical), SSO (Medium), and RBAC refinement.
- **Dependency:** Architecture Review must be signed off.
- **Key Date:** **August 15, 2025 (Milestone 2: MVP Feature-Complete)**.

### Phase 3: Hardening & Migration (August 16 – October 15, 2025)
- **Focus:** E2E testing, HIPAA audit, and phased migration of legacy users.
- **Dependency:** MVP feature completion and QA sign-off.
- **Key Date:** **October 15, 2025 (Milestone 3: Production Launch)**.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Per company culture, these recordings are rarely rewatched, so these summarized notes serve as the official record.*

### Meeting 1: Architecture Sync (2024-11-02)
- **Attendees:** Chandra, Ravi, Finn.
- **Discussion:** Debate over using PostgreSQL vs. SQLite. Ravi argued that the edge-latency benefits of SQLite/D1 outweigh the relational complexity of Postgres for our specific use case.
- **Decision:** Move forward with SQLite for edge state. Postgres is rejected to avoid the "Cold Start" latency of traditional database connections in Workers.

### Meeting 2: The "Localization" Crisis (2025-01-12)
- **Attendees:** Chandra, Ravi, Greta.
- **Discussion:** Greta reported that the translation agency is lagging on the Japanese and Korean strings. This puts the "Launch Blocker" status of the i18n feature at risk.
- **Decision:** Chandra will allocate an additional $15,000 from the contingency budget to onboard a secondary translation firm to accelerate the process.

### Meeting 3: Design Deadlock (2025-03-20)
- **Attendees:** Chandra, Ravi, Product Lead.
- **Discussion:** A heated disagreement occurred regarding the "Visual Rule Builder" UI. Product wants a "Canva-like" experience; Engineering argues this will delay the MVP by 3 weeks.
- **Decision:** Chandra intervened. The team will implement a "Simplified Logic Tree" for MVP, with the "Canva-like" experience moved to the Post-Launch Roadmap. This resolves the current blocker.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000  
**Duration:** 6 Months

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | 12-person cross-functional team (Salaries/Contractors) |
| **Infrastructure** | 15% | $120,000 | Cloudflare Enterprise, Object Storage, D1 Usage |
| **Tools & Licenses** | 5% | $40,000 | IDEs, Playwright Cloud, Translation Agency fees |
| **Contingency** | 10% | $80,000 | Reserved for risk mitigation (e.g., Contractor hire) |

**Personnel Detail:**
- 4 Full-stack Engineers (Rust/React)
- 2 Frontend Specialists (MFE Architecture)
- 2 QA Engineers (Finn Kim + 1)
- 1 Support Engineer (Greta Moreau)
- 1 Project Manager
- 1 Product Designer
- 1 CTO (Part-time oversight - Chandra Santos)

---

## 12. APPENDICES

### Appendix A: Structured Logging Proposal
**Current State:** Technical debt—production debugging requires reading `stdout`, which is unorganized and difficult to grep.
**Proposed Solution:** Implement a structured logging wrapper in Rust using the `tracing` crate.
- **Format:** JSON logs.
- **Fields:** `timestamp`, `level` (INFO, WARN, ERROR), `trace_id` (to track request flow across MFEs), `user_id`, and `message`.
- **Sink:** Export logs to Cloudflare Logpush $\rightarrow$ Axiom/Datadog for real-time monitoring.

### Appendix B: Legacy Data Migration Strategy
Because zero downtime is required, the migration will follow a "Dual-Write" strategy:
1. **Phase 1 (Shadow Write):** The legacy system continues to be the source of truth, but every write operation is mirrored to the Beacon database.
2. **Phase 2 (Read Validation):** Beacon reads data and compares it with the legacy system. Any discrepancies are logged as bugs.
3. **Phase 3 (Cutover):** Once the discrepancy rate is < 0.01%, the read-source is switched to Beacon. The legacy system remains as a read-only backup for 30 days.