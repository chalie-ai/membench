# PROJECT SPECIFICATION DOCUMENT: PROJECT KEYSTONE
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Project Lead:** Xiomara Stein  
**Date:** October 24, 2023  
**Company:** Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Keystone" is a strategic initiative by Coral Reef Solutions to develop a specialized Learning Management System (LMS) tailored for the logistics and shipping industry. Unlike generic educational platforms, Keystone is designed to bridge the gap between theoretical maritime logistics training and real-world operational execution. The platform serves as a central hub for employee certification, safety training, and regulatory compliance management within the shipping sector.

The core of Keystone's value proposition lies in its integration. This is not a standalone product but a strategic partnership integration. Keystone must synchronize seamlessly with an external partner's API (the "LogiSync" API), allowing for the real-time mapping of employee certifications to active shipping manifests and vessel assignments. This synchronization ensures that no crew member is assigned to a vessel without the requisite, up-to-date certifications, thereby reducing legal liability and operational downtime.

### 1.2 Business Justification
The logistics and shipping industry is currently facing a critical skills gap and increasing regulatory scrutiny. Manual tracking of certifications via spreadsheets has led to an average of 12% operational delays per quarter due to "certification lapses" discovered during port inspections. By automating the validation of training through the Keystone LMS, Coral Reef Solutions expects to reduce these delays by 80%.

Furthermore, the integration with the partner API allows for "Just-in-Time" (JIT) training. When a shipping route changes or a new vessel type is introduced, the system can automatically push required training modules to the relevant personnel based on the API data from the partner, ensuring 100% compliance before the vessel leaves port.

### 1.3 ROI Projection
The budget for Keystone is set at $400,000. The projected Return on Investment (ROI) is calculated based on three primary drivers:
1.  **Reduction in Regulatory Fines:** Estimated savings of $120,000/year by eliminating certification gaps.
2.  **Operational Efficiency:** Reduction in vessel downtime (estimated at $15,000 per hour of delay) is projected to save the company $250,000 annually.
3.  **Training Scalability:** Moving from manual instructor-led training to a digital LMS reduces per-employee training costs from $450 to $110.

The total projected first-year gain is estimated at $580,000, representing a 145% ROI within the first 12 months of full production launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Overview
Keystone utilizes a "Clean Monolith" architecture. While the system is deployed as a single unit to simplify deployment and management, the internal structure is strictly modular. This approach prevents the codebase from becoming a "big ball of mud" while avoiding the operational complexity of microservices given the modest team size.

The project is unique in that it inherits three different legacy stacks from previous prototypes and partner modules:
1.  **Stack A (Legacy Node.js/Express):** Handling basic user routing and legacy API wrappers.
2.  **Stack B (Python/Django):** Managing the heavy-lift data processing and import/export logic.
3.  **Stack C (Ruby on Rails):** Handling the original administrative dashboard and role management.

These three stacks interoperate via a shared PostgreSQL database and a unified Redis caching layer. Communication between modules is handled through internal service interfaces to minimize direct dependency on the underlying language-specific frameworks.

### 2.2 System Diagram (ASCII)

```text
[ User Browser / Client ] 
          |
          v
[ Nginx Reverse Proxy / Load Balancer ]
          |
          +--------------------------------------------------------+
          |                                                        |
[ Module 1: Auth/SSO (Node.js) ] <---> [ Module 2: LMS Core (Django) ] <---> [ Module 3: Admin (Rails) ]
          |                                                        |
          +--------------------------+-----------------------------+
                                     |
                                     v
                        [ Shared Redis Cache Layer ]
                                     |
                                     v
                        [ PostgreSQL Primary Database ]
                                     |
                                     v
                    [ External Partner API (LogiSync) ]
                    (Via Webhook/REST integration)
```

### 2.3 Technical Specifications
*   **Language Versions:** Node.js v18.x, Python 3.11, Ruby 3.2.
*   **Database:** PostgreSQL 15.2.
*   **Cache:** Redis 7.0.
*   **Infrastructure:** AWS EC2 (m5.large) with RDS (db.m5.large).
*   **Security:** Quarterly penetration testing conducted by third-party auditors. No specific compliance framework (like HIPAA or SOC2) is required, but OWASP Top 10 mitigations are mandatory.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 SSO Integration (SAML and OIDC)
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

The Single Sign-On (SSO) module is the gateway for all users. Because Coral Reef Solutions operates globally, users must be able to authenticate using their corporate credentials via SAML 2.0 (for enterprise partners) and OIDC (for modern cloud-integrated clients).

**Functional Requirements:**
*   **SAML 2.0 Flow:** The system must act as a Service Provider (SP). It must handle `<AuthnRequest>` and process `<SAMLResponse>` assertions, including attribute mapping for user roles.
*   **OIDC Flow:** Implementation of the Authorization Code Flow with PKCE (Proof Key for Code Exchange) to ensure secure authentication for the web frontend.
*   **Identity Provider (IdP) Management:** An admin interface to configure metadata URLs, Client IDs, and Client Secrets for multiple IdPs.
*   **Session Management:** Centralized JWT (JSON Web Token) issuance upon successful SSO handshake, with a 12-hour expiration and sliding window refresh.

**Technical Implementation:**
The SSO module will be housed in the Node.js stack to leverage the `passport.js` and `saml2-js` libraries. Upon successful authentication, the system must perform a "Just-in-Time" (JIT) account creation if the user does not exist in the PostgreSQL `users` table.

**Blocking Issue:** The integration is currently blocked by a missing metadata XML file from the primary shipping partner and the ongoing medical leave of the lead integration engineer.

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** Complete

This feature allows administrators to migrate employee training records from legacy CSV, XML, and JSON files. The system must automatically detect the file format and map the columns to the internal schema.

**Functional Requirements:**
*   **Automatic MIME Detection:** Using magic-number byte checking to identify file types regardless of the file extension.
*   **Schema Mapping:** A "heuristic mapper" that suggests column mappings based on keyword similarity (e.g., "Emp_ID" maps to `user_id`).
*   **Validation Gate:** A preview screen showing a sample of 10 records and highlighting any data type mismatches (e.g., text in a date field) before committing to the database.
*   **Bulk Export:** Capability to export all training records in the same format as the import for auditing purposes.

**Technical Implementation:**
Implemented in the Python/Django stack using the `Pandas` library for data manipulation. The process is handled asynchronously via Celery workers to prevent request timeouts during large (10k+ row) imports.

### 3.3 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** In Design

Keystone must notify external systems when specific events occur (e.g., "Certification Completed," "Certification Expired"). Conversely, it must be able to receive triggers from the partner API to update user status.

**Functional Requirements:**
*   **Event Registry:** A defined list of triggerable events: `cert.issued`, `cert.expired`, `user.promoted`, `course.completed`.
*   **Payload Delivery:** Delivery of JSON payloads via POST requests to user-defined endpoints with a retry mechanism (exponential backoff) if the target server is down.
*   **Security (Signing):** All outgoing webhooks must include an `X-Keystone-Signature` header (HMAC-SHA256) to allow the receiver to verify the payload source.
*   **Incoming Webhook Endpoints:** A dedicated endpoint (`/api/webhooks/partner`) to receive real-time updates from the LogiSync API regarding vessel assignments.

**Technical Implementation:**
The framework will utilize a Redis-backed queue to manage delivery attempts. A "Dead Letter Queue" (DLQ) will be implemented to alert Rumi Oduya (Support Engineer) if a webhook fails more than 5 times.

### 3.4 User Authentication and RBAC
**Priority:** Low | **Status:** Complete

Role-Based Access Control (RBAC) ensures that users can only access data relevant to their position (e.g., a Captain can see their crew's certs, but a Crew Member can only see their own).

**Functional Requirements:**
*   **Role Hierarchy:** Four primary roles: `SuperAdmin`, `OrgAdmin`, `Instructor`, and `Student`.
*   **Permission Matrix:** Granular control over "Create," "Read," "Update," and "Delete" (CRUD) actions for every module.
*   **Session Persistence:** Secure HTTP-only cookies to prevent XSS-based session hijacking.
*   **Password Policy:** Minimum 12 characters, requiring mixed case, numbers, and symbols for non-SSO users.

**Technical Implementation:**
Implemented within the Ruby on Rails stack using the `Pundit` gem. Roles are stored in a `roles` table and linked to users via a join table `user_roles`.

### 3.5 Advanced Search with Faceted Filtering
**Priority:** High | **Status:** Blocked

Administrators need to quickly find specific employees based on certifications, vessel assignments, and expiration dates across thousands of records.

**Functional Requirements:**
*   **Full-Text Search:** Ability to search across user names, certification titles, and course descriptions using fuzzy matching.
*   **Faceted Filtering:** A sidebar allowing users to drill down by "Certification Status" (Active/Expired/Pending), "Region," and "Vessel Class."
*   **Indexing:** Use of an inverted index to ensure search results return in under 200ms.
*   **Exportable Results:** Ability to export the current filtered view into a CSV report.

**Technical Implementation:**
The plan is to implement an Elasticsearch instance. However, this is currently blocked as the infrastructure team has not yet approved the additional memory requirements for the Elasticsearch cluster on the existing AWS instance.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions. Base URL: `https://api.keystone.coralreef.com/v1`

### 4.1 `GET /users`
*   **Description:** Retrieves a list of all users with optional filtering.
*   **Query Params:** `role` (string), `status` (string), `search` (string).
*   **Request Example:** `GET /users?role=Student&search=Smith`
*   **Response (200 OK):**
    ```json
    [
      { "id": "u102", "name": "John Smith", "role": "Student", "status": "active" }
    ]
    ```

### 4.2 `POST /auth/sso/saml/consume`
*   **Description:** Consumes the SAML response from the IdP.
*   **Request Example:** `POST /auth/sso/saml/consume` (Body: XML SAMLResponse)
*   **Response (200 OK):**
    ```json
    { "token": "eyJhbGci...[JWT]", "expires_at": "2026-07-15T12:00:00Z" }
    ```

### 4.3 `POST /import/upload`
*   **Description:** Uploads a file for data import.
*   **Request Example:** `POST /import/upload` (Multipart/form-data: file)
*   **Response (202 Accepted):**
    ```json
    { "job_id": "job_8821", "status": "processing", "estimated_time": "30s" }
    ```

### 4.4 `GET /import/status/{job_id}`
*   **Description:** Checks the status of a background import job.
*   **Request Example:** `GET /import/status/job_8821`
*   **Response (200 OK):**
    ```json
    { "job_id": "job_8821", "status": "completed", "records_processed": 450, "errors": 0 }
    ```

### 4.5 `POST /webhooks/subscribe`
*   **Description:** Registers a third-party URL to receive event notifications.
*   **Request Example:** `POST /webhooks/subscribe` (Body: `{"url": "https://partner.com/hook", "events": ["cert.expired"]}`)
*   **Response (201 Created):**
    ```json
    { "webhook_id": "wh_992", "status": "active" }
    ```

### 4.6 `POST /webhooks/partner/receive`
*   **Description:** Endpoint for the external LogiSync API to push vessel updates.
*   **Request Example:** `POST /webhooks/partner/receive` (Body: `{"vessel_id": "V-44", "crew_id": "u102", "action": "assign"}`)
*   **Response (200 OK):**
    ```json
    { "message": "Update received" }
    ```

### 4.7 `GET /search/certifications`
*   **Description:** Perfroms a faceted search for certifications.
*   **Query Params:** `q` (query), `facet_status` (string), `facet_date` (range).
*   **Request Example:** `GET /search/certifications?q=Safety&facet_status=expired`
*   **Response (200 OK):**
    ```json
    { "total": 12, "results": [{ "id": "c1", "name": "Basic Safety Training", "expiry": "2025-01-01" }] }
    ```

### 4.8 `PATCH /users/{id}/role`
*   **Description:** Updates the RBAC role of a specific user.
*   **Request Example:** `PATCH /users/u102/role` (Body: `{"role": "Instructor"}`)
*   **Response (200 OK):**
    ```json
    { "user_id": "u102", "new_role": "Instructor", "updated_at": "2026-07-15T10:00:00Z" }
    ```

---

## 5. DATABASE SCHEMA

The system utilizes a shared PostgreSQL database. All tables use UUIDs for primary keys to facilitate future distribution.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `sso_provider`, `last_login` | Core user account data. |
| `roles` | `role_id` | None | `role_name`, `permissions_json` | Definition of RBAC roles. |
| `user_roles` | `id` | `user_id`, `role_id` | `assigned_at` | Mapping users to roles. |
| `courses` | `course_id` | None | `title`, `description`, `version`, `is_mandatory` | Educational modules. |
| `certifications`| `cert_id` | `user_id` | `course_id`, `issue_date`, `expiry_date`, `status` | User achievement records. |
| `vessels` | `vessel_id` | None | `vessel_name`, `vessel_class`, `imo_number` | Shipping vessel metadata. |
| `assignments` | `assignment_id`| `user_id`, `vessel_id`| `start_date`, `end_date`, `position` | Mapping crew to ships. |
| `import_jobs` | `job_id` | None | `filename`, `status`, `error_log`, `created_at` | Tracking of data imports. |
| `webhook_configs`| `hook_id` | None | `target_url`, `secret_token`, `is_active` | Third-party webhook targets. |
| `event_logs` | `log_id` | `hook_id` | `event_type`, `payload`, `response_code`, `timestamp`| Audit trail for webhooks. |

### 5.2 Relationships
*   `users` $\rightarrow$ `user_roles` (1:N)
*   `roles` $\rightarrow$ `user_roles` (1:N)
*   `users` $\rightarrow$ `certifications` (1:N)
*   `courses` $\rightarrow$ `certifications` (1:N)
*   `users` $\rightarrow$ `assignments` (1:N)
*   `vessels` $\rightarrow$ `assignments` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Keystone utilizes three distinct environments to ensure stability.

**1. Development (Dev):**
*   **Purpose:** Feature iteration and unit testing.
*   **Access:** Open to all engineers.
*   **Deployment:** Automatic deployment via GitHub Actions on merge to `develop` branch.
*   **Data:** Mock data generated via seed scripts.

**2. Staging (Staging):**
*   **Purpose:** Integration testing and QA validation.
*   **Access:** Engineering team and QA Lead (Kira Costa).
*   **Deployment:** Manual trigger from `develop` $\rightarrow$ `staging`.
*   **Data:** Anonymized production snapshot.

**3. Production (Prod):**
*   **Purpose:** Live user access.
*   **Access:** Restricted to Xiomara Stein and Rumi Oduya.
*   **Deployment:** Manual QA gate. Kira Costa must sign off on the release ticket in JIRA. Total turnaround from Staging $\rightarrow$ Prod is 2 business days.

### 6.2 CI/CD Pipeline
The pipeline is hosted on GitHub Actions. 
1.  **Build Phase:** Compiles Ruby, Python, and Node.js binaries.
2.  **Test Phase:** Runs the full suite of unit and integration tests.
3.  **Lint Phase:** Checks for adherence to style guides.
4.  **QA Gate:** For Production, the pipeline pauses until the `qa_approval` label is added to the corresponding JIRA ticket.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Each of the three stacks has its own unit testing framework:
*   **Node.js:** Jest for SSO and API routing logic.
*   **Python:** PyTest for data import and mapping logic.
*   **Ruby:** RSpec for RBAC and Admin dashboard logic.
*   **Requirement:** Minimum 80% code coverage on all new features.

### 7.2 Integration Testing
Integration tests focus on the inter-stack communication and the shared PostgreSQL database. 
*   **Database Integrity:** Tests ensure that a user created in the Node.js SSO module is immediately visible to the Ruby RBAC module.
*   **API Contract Testing:** Using Pact to ensure that the frontend and backend agree on the JSON structure of API responses.

### 7.3 End-to-End (E2E) Testing
Kira Costa (QA Lead) manages E2E tests using Playwright. 
*   **Critical Path Testing:** A "Happy Path" test suite is run before every deployment: `Login $\rightarrow$ Course Selection $\rightarrow$ Course Completion $\rightarrow$ Certification Issuance $\rightarrow$ Admin Verification`.
*   **Regression Testing:** A suite of 50 core tests that verify that new changes haven't broken the legacy import/export functionality.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Primary Vendor EOL (End-of-Life) | High | Critical | **Parallel-Path:** Develop a prototype using an open-source alternative (Moodle/Canvas API) while the vendor product is still active. |
| R2 | Partner API Undocumented/Buggy | High | Medium | **De-scoping:** If the API cannot reliably support a feature by Milestone 2, the feature will be removed from the MVP scope. |
| R3 | Technical Debt (Hardcoded Configs) | Medium | Medium | **Refactor Sprint:** Dedicate one full sprint post-Milestone 1 to migrate all 40+ files' hardcoded values to a centralized `.env` and AWS Secrets Manager. |
| R4 | Key Team Member Leave | Medium | High | **Cross-Training:** Rumi Oduya to shadow Tala Fischer on backend tasks to ensure coverage during the 6-week absence. |

**Probability/Impact Matrix:**
*   **High/Critical:** Immediate action required; daily monitoring.
*   **High/Medium:** Weekly review in status meetings.
*   **Medium/Medium:** Monitored via JIRA backlog.

---

## 9. TIMELINE

### 9.1 Phases and Milestones

| Phase | Start Date | End Date | Milestone | Dependency |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | 2026-01-01 | 2026-07-15 | **Internal Alpha Release** | SSO Integration (Blocked) |
| **Phase 2: Refinement** | 2026-07-16 | 2026-09-15 | **Architecture Review** | Webhook Framework |
| **Phase 3: Hardening** | 2026-09-16 | 2026-11-15 | **Production Launch** | QA Gate Sign-off |

### 9.2 Gantt-Style Logic
*   **T0 $\rightarrow$ T1 (Alpha):** Focus on completing the Webhook framework and resolving the SSO blocker. The Data Import feature is already complete and will be used to populate the Alpha environment.
*   **T1 $\rightarrow$ T2 (Review):** Focus on the Advanced Search implementation (pending AWS memory approval) and cleaning up the hardcoded configuration values.
*   **T2 $\rightarrow$ T3 (Launch):** Final penetration testing, stress testing the API to ensure p95 < 200ms, and final documentation.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning (2023-10-10)
*   SSO still blocked.
*   Partner hasn't sent XML.
*   Xiomara says: "We can't launch without this."
*   Tala suggests mocking the SAML response for now to unblock frontend.
*   Decided: Mocking approved for Dev env only.

### Meeting 2: Technical Debt Review (2023-10-17)
*   Hardcoded values found in 42 files.
*   Rumi says: "Makes deployments a nightmare."
*   Tala suggests AWS Secrets Manager.
*   Xiomara: "Wait until after Alpha."
*   Decision: Schedule "Cleanup Sprint" for August 2026.

### Meeting 3: Risk Assessment (2023-10-24)
*   Vendor announced EOL.
*   Team panicked.
*   Xiomara: "Start a parallel prototype."
*   Tala to spend 10% of time on alternative API.
*   Kira notes: "Need to update test cases if API changes."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $310,000 | Salary/Contract for 6 members (incl. Engineering Manager and QA). |
| **Infrastructure** | $45,000 | AWS EC2, RDS, Redis, and Elasticsearch (estimated yearly). |
| **Software Tools** | $15,000 | JIRA Licenses, GitHub Enterprise, Pen-testing software. |
| **Contingency** | $30,000 | Buffer for vendor pivots or extended medical leave coverage. |

---

## 12. APPENDICES

### Appendix A: Hardcoded Value Registry
The following files have been identified as containing hardcoded credentials or environment URLs and are flagged for the August 2026 cleanup:
1.  `/config/database.rb` (Production DB URL)
2.  `/src/auth/saml_config.js` (Partner Metadata URL)
3.  `/app/utils/api_helper.py` (Partner API Key)
4.  (39 other files omitted for brevity, listed in JIRA ticket KEY-402)

### Appendix B: API Performance Baseline
To meet the success criterion of **p95 < 200ms**, the following baselines were established during the alpha phase using JMeter:
*   **GET /users:** 45ms (Avg), 110ms (p95)
*   **GET /search/certifications:** 320ms (Avg), 850ms (p95) $\rightarrow$ *FAIL: Requires Elasticsearch implementation.*
*   **POST /webhooks/partner/receive:** 22ms (Avg), 60ms (p95)