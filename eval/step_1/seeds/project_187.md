# PROJECT SPECIFICATION: PROJECT RAMPART
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Classification:** Internal Confidential – Deepwell Data  
**Project Lead:** Xena Jensen (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

Project Rampart is a strategic "moonshot" R&D initiative commissioned by Deepwell Data, specifically designed to modernize the operational backbone of our food and beverage distribution vertical. In an industry characterized by legacy monolithic software and fragmented data silos, Rampart aims to provide a centralized, high-performance internal enterprise tool capable of orchestrating complex logistics, inventory management, and vendor communications.

**Business Justification**
Currently, Deepwell Data relies on a mixture of manual spreadsheets and aging third-party software that lacks the agility required for modern food-and-beverage supply chain volatility. The "moonshot" nature of this project stems from the ambition to move from a reactive data posture to a predictive one. By consolidating data streams into a single, high-performance interface, Rampart intends to eliminate the "information lag" that currently results in an estimated 12% wastage of perishable goods annually across our partner networks.

**ROI Projection**
While the project is currently unfunded (bootstrapping via existing capacity), the projected Return on Investment is based on two primary levers:
1. **Operational Efficiency:** By achieving the success metric of a 50% reduction in manual processing time for end users, we project a reclaim of 1,200 man-hours per month across the logistics team. Based on an average burdened labor cost of $65/hour, this equates to a monthly operational saving of $78,000.
2. **Waste Reduction:** A targeted 2% reduction in perishable waste via better data visibility is estimated to save the company $450,000 in the first fiscal year post-deployment.

Despite the uncertainty of the ROI—given the R&D nature of the tool—the project enjoys strong executive sponsorship from the C-Suite. This support is predicated on the belief that failing to build a proprietary tool like Rampart leaves Deepwell Data vulnerable to competitors who are already digitizing their supply chains.

**Strategic Alignment**
Rampart aligns with the "Digital First 2026" initiative. It serves as a proof-of-concept for a micro-frontend architecture, which, if successful, will be rolled out across all internal Deepwell Data tools. The project's success will be measured not just by the tool's utility, but by the technical feasibility of maintaining a high-performance, multi-tenant system managed by a lean, high-trust team.

---

## 2. TECHNICAL ARCHITECTURE

Rampart utilizes a modern, type-safe stack designed for rapid iteration and extreme scalability. The core philosophy is a **Micro-Frontend (MFE) Architecture**, allowing independent team ownership of specific modules, which prevents the codebase from becoming a monolithic bottleneck as the tool expands.

### 2.1 Tech Stack
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Radix UI.
- **Backend/API:** Next.js Server Actions and Route Handlers (TypeScript).
- **ORM:** Prisma (v5.x).
- **Database:** PostgreSQL 15 (Managed instance).
- **Deployment/Hosting:** Vercel (Production and Preview environments).
- **Infrastructure:** AWS S3 for file storage, CloudFront for CDN distribution.

### 2.2 Architecture Diagram (ASCII Description)
The system follows a decoupled layer approach where the frontend modules communicate via a unified API gateway provided by the Next.js backend.

```text
[ USER BROWSER ] 
       |
       v
[ VERCEL EDGE NETWORK / CDN ] <------> [ S3 BUCKETS (Static Assets/Files) ]
       |
       v
[ NEXT.JS APPLICATION LAYER ] 
       |
       +-- [ MFE: Data Import Module ] ----+
       |                                   |
       +-- [ MFE: Workflow Engine ] -------+---> [ AUTH: SAML/OIDC ]
       |                                   |
       +-- [ MFE: Tenant Management ] ----+
       |
       v
[ PRISMA ORM LAYER ]
       |
       v
[ POSTGRESQL DATABASE ]
       |
       +-- [ Schema: Tenant_Isolation ]
       +-- [ Schema: User_Permissions ]
       +-- [ Schema: Workflow_Rules ]
```

### 2.3 Architectural Decisions
- **Micro-Frontend Implementation:** To avoid the complexity of Module Federation, Rampart uses a "Component Library" approach where different feature teams (currently solo) build independent directories in the `/app` folder, sharing a common UI kit but maintaining separate state logic.
- **Deployment Pipeline:** Currently, the project relies on a single DevOps engineer for manual deployments. This creates a high "bus factor" risk, as the deployment logic is not fully automated and requires manual verification of environment variables.
- **CI/CD Bottleneck:** The current GitHub Actions pipeline takes 45 minutes. This is due to sequential execution of comprehensive E2E tests and a lack of dependency caching. Optimization (parallelization) is deferred to the next sprint.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-Tenant Data Isolation (Priority: High | Status: Blocked)
**Description:**
The core of Rampart is its ability to serve multiple different business units (Tenants) within the food and beverage ecosystem while ensuring that no data leaks between them. Because this is shared infrastructure, isolation must happen at the application and database layers.

**Technical Requirements:**
- **Row-Level Security (RLS):** Implement PostgreSQL RLS policies to ensure that every query automatically filters by `tenant_id`.
- **Tenant Resolver:** A middleware layer in Next.js that identifies the tenant based on the request header or subdomain (e.g., `tenant1.rampart.deepwell.com`).
- **Context Propagation:** The `tenant_id` must be passed through every Prisma query. Any query missing a `tenant_id` must be rejected by the API.
- **Isolation Validation:** A suite of automated tests that attempt to access Tenant B's data using Tenant A's credentials; these tests must fail 100% of the time.

**User Experience:**
Users should be unaware of the multi-tenancy. The system should feel like a private instance. Admins, however, will have a "Global View" to manage all tenants from a single dashboard.

**Current Blocker:**
The implementation is currently blocked by the "Identity Core" team, whose deliverable for the Tenant Mapping API is 3 weeks overdue.

---

### 3.2 SSO Integration with SAML and OIDC (Priority: Low | Status: Blocked)
**Description:**
To integrate with Deepwell Data’s corporate security policy, Rampart must support Single Sign-On (SSO) using both SAML 2.0 (for legacy corporate directories) and OIDC (for modern cloud identity providers).

**Technical Requirements:**
- **Protocol Support:** Support for `Auth0` or `Okta` as the primary identity broker.
- **Just-In-Time (JIT) Provisioning:** Users should be automatically created in the Rampart database upon their first successful SSO login, mapping their corporate roles to Rampart permissions.
- **Token Management:** Secure handling of JWTs (JSON Web Tokens) with short expiration times and secure refresh token rotation stored in HttpOnly cookies.
- **Multi-Provider Logic:** The system must allow different tenants to use different SSO providers (e.g., Tenant A uses Azure AD via SAML, Tenant B uses Google Workspace via OIDC).

**User Experience:**
A "Sign in with Corporate ID" button on the landing page. After authentication, the user is redirected back to their specific tenant dashboard.

**Current Blocker:**
Blocked pending the finalization of the security audit for the core authentication middleware.

---

### 3.3 File Upload with Virus Scanning and CDN (Priority: High | Status: In Design)
**Description:**
Food and beverage logistics require the upload of high-volumes of PDF invoices, CSV manifests, and images of delivery receipts. This feature manages the secure ingestion and global distribution of these files.

**Technical Requirements:**
- **Ingestion Pipeline:** Files are uploaded to a "Quarantine" S3 bucket.
- **Virus Scanning:** An asynchronous Lambda function triggers a scan via ClamAV or an equivalent API. Files marked "Clean" are moved to the "Production" bucket; "Infected" files are deleted and the user is notified.
- **CDN Distribution:** Files are served via Amazon CloudFront with signed URLs to ensure that only authorized users can access specific documents.
- **Chunked Uploads:** Support for files up to 500MB using multipart uploads to prevent timeout on slow connections.

**User Experience:**
A drag-and-drop upload zone with a real-time progress bar. A "Scanning..." status indicator appears until the virus scan is complete, at which point the file becomes "Available."

---

### 3.4 Data Import/Export with Format Auto-Detection (Priority: Medium | Status: Blocked)
**Description:**
The tool must allow users to import large datasets from various legacy systems (Excel, CSV, JSON, XML) and export them for reporting.

**Technical Requirements:**
- **Auto-Detection Engine:** Use a "magic byte" check and structural analysis to determine if an uploaded file is a CSV, XLS, or JSON file without relying solely on the file extension.
- **Schema Mapping:** A UI-based mapper that allows users to map their source columns (e.g., "Prod_ID") to Rampart's internal fields (e.g., "sku_identifier").
- **Asynchronous Processing:** Since imports can involve 100k+ rows, the process must happen in a background worker (via BullMQ or similar) to avoid blocking the main thread.
- **Export Engine:** Ability to generate filtered reports in PDF or XLSX formats using the `exceljs` library.

**User Experience:**
An "Import Wizard" that guides the user through: Upload $\rightarrow$ Detection $\rightarrow$ Mapping $\rightarrow$ Validation $\rightarrow$ Confirmation.

**Current Blocker:**
Blocked by the lack of a finalized data dictionary from the business stakeholders.

---

### 3.5 Workflow Automation Engine with Visual Rule Builder (Priority: Low | Status: In Progress)
**Description:**
A "Low-Code" engine that allows non-technical users to create automated business rules (e.g., "If shipment is delayed > 2 hours AND value > $5,000, notify Regional Manager").

**Technical Requirements:**
- **Visual Rule Builder:** A React-based flow chart interface (using React Flow) where users can drag and drop "Triggers," "Conditions," and "Actions."
- **Rule Evaluator:** A backend engine that parses these rules into a JSON logic format (using `json-logic-js`) and evaluates them against incoming events.
- **Event Bus:** Integration with a messaging system to trigger rules based on database changes or API calls.
- **Audit Log:** Every execution of a rule must be logged with the input data, the result, and the timestamp.

**User Experience:**
A canvas where users connect nodes. A "Test Rule" button that allows users to simulate an event to see if the rule triggers correctly before deploying it to production.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are RESTful and require a valid JWT in the `Authorization: Bearer <token>` header.

### 4.1 Tenant Management
**Endpoint:** `POST /api/v1/tenants`
- **Description:** Creates a new tenant organization.
- **Request Body:** `{ "name": "String", "region": "String", "plan": "String" }`
- **Response (201):** `{ "id": "uuid", "createdAt": "timestamp", "status": "provisioning" }`

**Endpoint:** `GET /api/v1/tenants/{tenantId}/settings`
- **Description:** Retrieves configuration for a specific tenant.
- **Response (200):** `{ "tenantId": "uuid", "ssoEnabled": true, "maxUploadSize": "500MB" }`

### 4.2 File Operations
**Endpoint:** `POST /api/v1/files/upload`
- **Description:** Initiates a multipart upload.
- **Request Body:** `FormData { "file": File, "category": "String" }`
- **Response (202):** `{ "uploadId": "uuid", "status": "scanning" }`

**Endpoint:** `GET /api/v1/files/{fileId}/status`
- **Description:** Checks the virus scan status of a file.
- **Response (200):** `{ "fileId": "uuid", "status": "clean|infected|scanning" }`

### 4.3 Data Import/Export
**Endpoint:** `POST /api/v1/import/detect`
- **Description:** Detects the format of a provided file.
- **Request Body:** `FormData { "file": File }`
- **Response (200):** `{ "detectedFormat": "CSV", "confidence": 0.98, "columns": ["Date", "SKU", "Qty"] }`

**Endpoint:** `POST /api/v1/export/generate`
- **Description:** Triggers a background export job.
- **Request Body:** `{ "filters": { "startDate": "ISO8601", "endDate": "ISO8601" }, "format": "xlsx" }`
- **Response (202):** `{ "jobId": "uuid", "estimatedTime": "30s" }`

### 4.4 Workflow Engine
**Endpoint:** `POST /api/v1/workflows`
- **Description:** Saves a new visual rule configuration.
- **Request Body:** `{ "name": "String", "nodes": [], "edges": [], "logic": "JSONLogicObject" }`
- **Response (201):** `{ "workflowId": "uuid", "status": "active" }`

**Endpoint:** `DELETE /api/v1/workflows/{workflowId}`
- **Description:** Deactivates and deletes a workflow.
- **Response (204):** No content.

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. All tables utilize UUIDs for primary keys to facilitate easier sharding and tenant isolation.

### 5.1 Table Definitions

1.  **`tenants`**
    - `id`: UUID (PK)
    - `name`: VARCHAR(255)
    - `slug`: VARCHAR(50) (Unique)
    - `created_at`: TIMESTAMP
    - `updated_at`: TIMESTAMP

2.  **`users`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `email`: VARCHAR(255) (Unique)
    - `full_name`: VARCHAR(255)
    - `role`: VARCHAR(50) (e.g., 'ADMIN', 'OPERATOR')
    - `sso_provider_id`: VARCHAR(255)

3.  **`tenant_settings`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `sso_enabled`: BOOLEAN
    - `default_currency`: VARCHAR(3)
    - `timezone`: VARCHAR(50)

4.  **`files`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `user_id`: UUID (FK $\rightarrow$ users.id)
    - `filename`: VARCHAR(255)
    - `s3_key`: TEXT
    - `status`: VARCHAR(20) (e.g., 'SCANNING', 'CLEAN', 'INFECTED')
    - `mime_type`: VARCHAR(100)

5.  **`import_jobs`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `status`: VARCHAR(20)
    - `rows_processed`: INTEGER
    - `error_log`: TEXT
    - `started_at`: TIMESTAMP

6.  **`workflows`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `name`: VARCHAR(255)
    - `definition`: JSONB (Stores the React Flow graph)
    - `logic_json`: JSONB (Stores the executable logic)
    - `is_active`: BOOLEAN

7.  **`workflow_logs`**
    - `id`: UUID (PK)
    - `workflow_id`: UUID (FK $\rightarrow$ workflows.id)
    - `trigger_event`: VARCHAR(100)
    - `outcome`: VARCHAR(50)
    - `execution_time_ms`: INTEGER
    - `timestamp`: TIMESTAMP

8.  **`permissions`**
    - `id`: UUID (PK)
    - `role`: VARCHAR(50)
    - `resource`: VARCHAR(100)
    - `action`: VARCHAR(20) (e.g., 'READ', 'WRITE', 'DELETE')

9.  **`audit_logs`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `user_id`: UUID (FK $\rightarrow$ users.id)
    - `action`: TEXT
    - `ip_address`: VARCHAR(45)
    - `timestamp`: TIMESTAMP

10. **`api_keys`**
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ tenants.id)
    - `key_hash`: TEXT
    - `expires_at`: TIMESTAMP
    - `last_used_at`: TIMESTAMP

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `tenants` $\rightarrow$ `files`, `tenants` $\rightarrow$ `workflows`.
- **One-to-One:** `tenants` $\rightarrow$ `tenant_settings`.
- **Many-to-One:** `workflow_logs` $\rightarrow$ `workflows`, `audit_logs` $\rightarrow$ `users`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

The project follows a tiered environment strategy. Deployment is currently manual, performed by a single DevOps specialist.

### 6.1 Environment Descriptions

#### Development (Dev)
- **Purpose:** Individual developer experimentation and feature branching.
- **Hosting:** Local Docker containers or Vercel Preview deployments.
- **Database:** Local PostgreSQL instance or a shared "Dev" cloud DB.
- **Deployment:** Triggered on every git push to a feature branch.

#### Staging (Staging)
- **Purpose:** QA, UAT (User Acceptance Testing), and stakeholder previews.
- **Hosting:** Dedicated Vercel project (`rampart-staging.vercel.app`).
- **Database:** Managed PostgreSQL instance (mirror of production schema).
- **Deployment:** Manual trigger by DevOps person upon merge to the `develop` branch.

#### Production (Prod)
- **Purpose:** Live enterprise tool for end users.
- **Hosting:** Production Vercel environment (`rampart.deepwell.com`).
- **Database:** High-availability managed PostgreSQL with automated backups.
- **Deployment:** Manual deployment via Vercel CLI/Dashboard by the DevOps lead after a successful Staging sign-off.

### 6.2 Infrastructure Constraints
- **Bus Factor:** The deployment process is a critical risk. All environment variables and deployment scripts are known only to one person.
- **CI Pipeline:** The GitHub Actions pipeline is currently non-parallelized, leading to a 45-minute build time. This includes:
    - `npm install` (5 mins)
    - `TypeScript Check` (10 mins)
    - `Unit Tests` (10 mins)
    - `Integration Tests` (10 mins)
    - `E2E Cypress Tests` (10 mins)

---

## 7. TESTING STRATEGY

Given the high-trust, low-ceremony nature of the team, testing is focused on automation rather than manual regression.

### 7.1 Unit Testing
- **Tooling:** Jest and Vitest.
- **Scope:** All utility functions, data transformation logic, and individual UI components.
- **Requirement:** Minimum 80% code coverage for the `logic/` and `utils/` directories.

### 7.2 Integration Testing
- **Tooling:** Prisma Mock and Supertest.
- **Scope:** API endpoints and database interactions. We focus on verifying that the `tenant_id` is correctly applied to all queries to prevent data leakage.
- **Requirement:** Every API endpoint must have a corresponding "Unauthorized Access" test case (attempting to access data from a different tenant).

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Cypress.
- **Scope:** Critical user journeys (e.g., "User uploads file $\rightarrow$ scans $\rightarrow$ views result").
- **Requirement:** These tests run in the CI pipeline but are the primary cause of the 45-minute delay. They are currently executed sequentially.

### 7.4 Security Testing
- **Penetration Testing:** Conducted quarterly by an external third party.
- **Focus:** SQL injection, XSS, and Broken Object Level Authorization (BOLA) specifically regarding the multi-tenant architecture.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is building same product (2 months ahead) | High | High | Hire a specialized contractor to accelerate development and reduce bus factor. |
| R-02 | Scope creep from stakeholders adding 'small' features | High | Medium | Implement a strict "Feature Freeze" 2 weeks before each milestone. De-scope non-essential features if unresolved. |
| R-03 | Deployment Bus Factor (Only 1 DevOps person) | Medium | High | Document the manual deployment process and create a "Emergency Deployment Guide" for Xena Jensen. |
| R-04 | CI Pipeline Slowness (45 mins) | High | Low | Implement parallel test execution and dependency caching in GitHub Actions. |
| R-05 | Dependency on external team (3 weeks behind) | High | High | Escalate to executive sponsorship to prioritize the Identity Core team's deliverables. |

**Probability/Impact Matrix:**
- **High/High:** R-01, R-05 (Immediate action required)
- **High/Medium:** R-02 (Active monitoring)
- **Medium/High:** R-03 (Contingency planning)
- **High/Low:** R-04 (Scheduled for optimization)

---

## 9. TIMELINE AND MILESTONES

The project is structured in three major phases. Dependencies are critical, particularly on the external Identity Core team.

### 9.1 Phase 1: Foundations & Performance
- **Focus:** Core architecture, database setup, and performance tuning.
- **Dependencies:** None.
- **Key Milestone:** **Milestone 1: Performance benchmarks met (Target: 2025-07-15)**.
    - *Success Metric:* p95 API response time under 200ms.

### 9.2 Phase 2: Security & Data Integrity
- **Focus:** Multi-tenancy, SSO, and virus scanning.
- **Dependencies:** Identity Core Team (3-week lag).
- **Key Milestone:** **Milestone 2: Security audit passed (Target: 2025-09-15)**.
    - *Success Metric:* Zero "High" or "Critical" vulnerabilities in the quarterly pen test.

### 9.3 Phase 3: Automation & Delivery
- **Focus:** Workflow engine and data import/export.
- **Dependencies:** Business stakeholder sign-off on data dictionary.
- **Key Milestone:** **Milestone 3: Stakeholder demo and sign-off (Target: 2025-11-15)**.
    - *Success Metric:* 50% reduction in manual processing time during UAT.

---

## 10. MEETING NOTES

*Note: All meetings were recorded via Zoom. Per team culture, these recordings are archived but not rewatched. The following summaries are distilled from Slack discussions following the calls.*

### Meeting 1: Architecture Alignment (2023-11-02)
- **Attendees:** Xena, Kai, Lior, Mosi.
- **Discussion:** Lior raised concerns that the micro-frontend approach might overcomplicate the UX for a solo developer. Kai argued that it's necessary for future scaling.
- **Decision:** Proceed with MFE using the "Component Library" approach in Next.js. Decisions will continue to be finalized in the `#rampart-dev` Slack channel to maintain low ceremony.
- **Action Item:** Kai to create the base UI kit in Tailwind.

### Meeting 2: The "Identity Blocker" (2023-12-15)
- **Attendees:** Xena, Mosi.
- **Discussion:** Mosi reported that the Identity Core team has missed their third deadline for the Tenant Mapping API. Xena noted that this blocks both Multi-tenancy and SSO.
- **Decision:** Xena to escalate the blocker to the VP of Engineering. In the meantime, Mosi will create a "Mock Identity Provider" to allow frontend development to continue.
- **Action Item:** Mosi to deploy the mock API by Friday.

### Meeting 3: Budget & Resource Review (2024-01-10)
- **Attendees:** Xena, Executive Sponsor.
- **Discussion:** Discussion on the "unfunded" nature of the project. The sponsor reiterated that there is no direct budget, but "capacity" is granted.
- **Decision:** To mitigate the competitor risk (Risk R-01), the sponsor agreed to a "discretionary spend" for one external contractor for 3 months to help with the DevOps pipeline and CI optimization.
- **Action Item:** Xena to source a contractor from the approved vendor list.

---

## 11. BUDGET BREAKDOWN

As a bootstrapping project, the budget is primarily comprised of internal labor (capacity) rather than cash expenditure.

| Category | Annual Estimated Cost | Funding Source | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel (Internal)** | $480,000 | Dept. OpEx | Xena, Kai, Lior, Mosi (allocated % of time) |
| **Personnel (Contractor)** | $65,000 | Discretionary | 3-month contract for DevOps/CI optimization |
| **Infrastructure (Vercel)** | $12,000 | Team Budget | Enterprise Plan (Pro) |
| **Infrastructure (AWS/S3)** | $8,000 | Team Budget | S3, CloudFront, Lambda |
| **Tools (SAML/Auth0)** | $5,000 | Team Budget | B2B SaaS license |
| **Contingency** | $10,000 | Discretionary | Emergency API credits/Third-party audit |
| **TOTAL** | **$580,000** | **Mixed** | **ROI projected at $1.2M+ annually** |

---

## 12. APPENDICES

### Appendix A: Performance Benchmark Methodology
To meet Milestone 1, the team will use `k6` for load testing.
- **Scenario:** 100 concurrent users performing a mix of `GET /tenants/settings` (60%) and `POST /files/upload` (40%).
- **Goal:** p95 response time $< 200\text{ms}$.
- **Environment:** Tests must be run against the Staging environment with a production-sized dataset (1 million rows in the `audit_logs` table).

### Appendix B: Virus Scanning Workflow (Technical Detail)
The file upload process follows a strict state machine:
1. `PENDING`: File uploaded to `s3://rampart-quarantine/`.
2. `SCANNING`: Lambda trigger initiates `clamav-scan`.
3. `CLEAN`: File moved to `s3://rampart-prod/` $\rightarrow$ database updated to `status: 'CLEAN'`.
4. `INFECTED`: File deleted from S3 $\rightarrow$ database updated to `status: 'INFECTED'` $\rightarrow$ Notification sent to `audit_logs`.
5. `ERROR`: Scan failed $\rightarrow$ File remains in quarantine $\rightarrow$ Retried 3 times before marking as `ERROR`.