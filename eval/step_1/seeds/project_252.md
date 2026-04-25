# PROJECT SPECIFICATION DOCUMENT: PROJECT VANGUARD
**Version:** 1.0.4  
**Date:** May 15, 2025  
**Status:** Approved/Baseline  
**Author:** Jasper Jensen, Engineering Manager  
**Company:** Stratos Systems  
**Confidentiality:** Level 4 (HIPAA Restricted)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Vanguard represents a mission-critical strategic pivot for Stratos Systems. After the launch of our legacy healthcare records system, the organization experienced catastrophic user feedback, citing unintuitive navigation, systemic instability, and a lack of transparency in billing. Consequently, Vanguard is not merely an update, but a complete customer-facing product rebuild designed to salvage the company's reputation in the healthcare-fintech sector.

Vanguard aims to bridge the gap between healthcare record management and financial operations (fintech), creating a seamless pipeline where patient records trigger automated billing and insurance claims processing. The project is tasked with modernizing the user experience while maintaining rigorous HIPAA compliance.

### 1.2 Business Justification
The current legacy system has led to a churn rate of 35% in the first quarter post-launch. In the healthcare industry, trust is the primary currency; the failure of the previous version has created a perception of instability that threatens Stratos Systems' market position. The justification for Vanguard is twofold:
1. **Retention:** By rebuilding the frontend and optimizing the backend via hexagonal architecture, we expect to reduce churn to under 5%.
2. **Revenue Stream Stabilization:** The current manual billing process is prone to a 12% error rate. Automating this via the "Automated Billing" feature will recoup an estimated $120,000 in leaked revenue per quarter.

### 1.3 ROI Projection
With a total budget of $800,000, the investment is projected to break even within 14 months post-launch. 
- **Direct Revenue:** Onboarding the first paying customer by December 15, 2025, is expected to initiate a recurring revenue stream of $15,000/month per mid-sized clinic.
- **Operational Efficiency:** Reducing the CI pipeline from 45 minutes to 10 minutes (target) will save approximately 120 developer hours per month.
- **Market Valuation:** A successful pivot from "failed launch" to "industry leader in healthcare fintech" is estimated to increase the company's valuation by 20% during the next funding round.

### 1.4 Strategic Alignment
Vanguard aligns with the Stratos Systems "Patient-First" initiative, ensuring that the financial side of healthcare (billing/subscriptions) does not interfere with the clinical side (records/uploads).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Mixed Stack Challenge
Vanguard inherits three legacy stacks that must interoperate seamlessly. This is the primary technical challenge:
1. **Stack A (Legacy Core):** Java Spring Boot 2.x with a monolithic PostgreSQL database.
2. **Stack B (Billing Engine):** Node.js/TypeScript with a MongoDB instance.
3. **Stack C (Frontend):** An aging Angular 8 application.

Vanguard will migrate the frontend to React 18 and encapsulate the legacy logic using a Hexagonal Architecture.

### 2.2 Hexagonal Architecture (Ports and Adapters)
To prevent the "big ball of mud" seen in the previous version, Vanguard utilizes a Hexagonal Architecture. This decouples the core business logic (The Domain) from external concerns (The Infrastructure).

- **The Core:** Contains the business entities and use cases (e.g., `ProcessBillingUseCase`, `UploadMedicalRecordUseCase`).
- **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `IBillingRepository`, `IFileStorageService`).
- **Adapters:** Concrete implementations of the ports (e.g., `PostgresBillingAdapter`, `S3FileAdapter`, `StripePaymentAdapter`).

### 2.3 ASCII Architecture Diagram
```text
[ EXTERNAL CLIENTS ] <---> [ ADAPTERS (Primary) ] <---> [ PORTS (Input) ]
                                                               |
                                                               v
                                                     [ DOMAIN BUSINESS LOGIC ]
                                                     (Entities / Use Cases)
                                                               ^
                                                               |
[ EXTERNAL SERVICES ] <---> [ ADAPTERS (Secondary) ] <---> [ PORTS (Output) ]
      |                           |                            |
      +--> Stripe API            +--> MongoDB Adapter          +--> Postgres DB
      +--> AWS S3/ClamAV          +--> Legacy Java API          +--> Redis Cache
      +--> SendGrid               +--> Auth0 Adapter           +--> CDN Edge
```

### 2.4 Security and Compliance
As a healthcare platform, HIPAA compliance is non-negotiable.
- **Encryption at Rest:** All databases use AES-256 encryption.
- **Encryption in Transit:** TLS 1.3 is mandated for all connections.
- **Audit Logging:** Every access to a patient record is logged in an immutable ledger with a timestamp, user ID, and action performed.
- **BBA:** All infrastructure providers (AWS) must have a signed Business Associate Agreement.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Detailed Description:**
The billing system must automate the transition from a medical encounter (record creation) to a financial transaction. This involves integrating with a payment gateway (Stripe) and managing multi-tiered subscription plans (Basic, Professional, Enterprise). The system must handle automated invoicing, failed payment retries (dunning), and tax calculations based on the provider's jurisdiction.

**Functional Requirements:**
- **Subscription Engine:** Ability to create and modify subscription plans via an admin panel.
- **Automatic Trigger:** When a "Consultation" record is marked as "Complete," the system must automatically generate a pending invoice.
- **Dunning Logic:** If a payment fails, the system will attempt retries at 1, 3, and 7 days before restricting account access.
- **Invoice Generation:** PDF generation of HIPAA-compliant invoices containing only necessary billing codes (ICD-10) without exposing full clinical notes.

**Technical Constraints:**
- Must use the `BillingAdapter` to interface with the legacy MongoDB instance for historical data.
- Must implement an idempotency key for all payment requests to prevent double-charging.

---

### 3.2 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Detailed Description:**
Healthcare providers must upload high-resolution diagnostic images (DICOM, JPEG, PDF). Because these files are uploaded by external users, they represent a significant security vector. Every file must be scanned for malware before being persisted and then distributed via a secure, authenticated CDN for fast retrieval by clinicians.

**Functional Requirements:**
- **Upload Pipeline:** User $\rightarrow$ S3 Landing Bucket $\rightarrow$ ClamAV Scanner $\rightarrow$ S3 Permanent Bucket.
- **Virus Scanning:** Any file flagged as "infected" must be immediately quarantined and the user notified.
- **CDN Integration:** Use AWS CloudFront with "Signed URLs." Files are not public; the system generates a time-limited URL (e.g., 15 minutes) upon user request.
- **File Validation:** Restrict uploads to specific MIME types (.pdf, .jpg, .png, .dcm) and a maximum size of 50MB per file.

**Technical Constraints:**
- The virus scan must happen asynchronously via an S3 Trigger $\rightarrow$ Lambda function to avoid blocking the UI.
- Files must be encrypted with KMS keys before being written to the permanent bucket.

---

### 3.3 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** High | **Status:** Blocked

**Detailed Description:**
To maintain cost-efficiency, Vanguard uses a shared infrastructure model (Shared Database, Shared App Server) but must guarantee absolute data isolation. A user from "Clinic A" must never, under any circumstance, be able to access data from "Clinic B," even if they guess a record ID.

**Functional Requirements:**
- **Tenant Identification:** Every request must carry a `TenantID` in the JWT (JSON Web Token) payload.
- **Row-Level Security (RLS):** Implementation of PostgreSQL RLS where every query automatically appends a `WHERE tenant_id = X` clause.
- **Schema Isolation:** While the DB is shared, logical separation is enforced via a `tenants` table that maps users to specific organization IDs.
- **Cross-Tenant Prevention:** The API layer must validate that the requested Resource ID belongs to the `TenantID` present in the authenticated session.

**Technical Constraints:**
- This feature is currently blocked by the medical leave of the Lead Database Architect.
- Implementation must not introduce more than 10ms of latency to the query execution time.

---

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Low (Nice to Have) | **Status:** In Review

**Detailed Description:**
To allow third-party integrations (e.g., pharmacies, insurance providers), Vanguard will provide a RESTful API. To ensure stability, the API will be versioned, and a "Sandbox" environment will be provided so developers can test integrations without affecting real patient data.

**Functional Requirements:**
- **Versioning:** Use URI versioning (e.g., `/api/v1/records`).
- **Sandbox Environment:** A mirrored version of the production environment with synthetic (fake) data.
- **API Key Management:** Users can generate, rotate, and revoke API keys from their dashboard.
- **Rate Limiting:** Implement a leaky-bucket algorithm to limit requests (e.g., 100 requests/minute for Basic tier).

**Technical Constraints:**
- The Sandbox must be logically isolated from Production to prevent accidental data leaks.
- API documentation must be auto-generated using Swagger/OpenAPI 3.0.

---

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** In Design

**Detailed Description:**
Clinicians have different needs. A surgeon needs different data on their home screen than a billing clerk. This feature allows users to customize their dashboard by adding, removing, and rearranging widgets (e.g., "Upcoming Appointments," "Pending Invoices," "Recent Lab Results").

**Functional Requirements:**
- **Widget Library:** A set of pre-defined components (charts, lists, alerts).
- **Layout Persistence:** The user's layout (X/Y coordinates and widget IDs) must be saved to the database.
- **Drag-and-Drop UI:** Using `react-grid-layout` to allow intuitive resizing and repositioning.
- **Real-time Updates:** Widgets should use WebSockets or Polling to update data without a full page refresh.

**Technical Constraints:**
- The dashboard must remain performant with up to 12 active widgets.
- Layout configurations must be stored as a JSON blob in the user preferences table.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the header: `Authorization: Bearer <JWT>`.

### 4.1 Billing Endpoints

**1. GET `/api/v1/billing/subscriptions`**
- **Description:** Retrieve the current subscription status for the authenticated tenant.
- **Request:** `GET /api/v1/billing/subscriptions`
- **Response (200 OK):**
  ```json
  {
    "subscription_id": "sub_8821",
    "plan": "Enterprise",
    "status": "active",
    "next_billing_date": "2025-07-01"
  }
  ```

**2. POST `/api/v1/billing/invoices`**
- **Description:** Manually trigger an invoice for a specific patient encounter.
- **Request:** `POST /api/v1/billing/invoices`
  ```json
  { "encounter_id": "enc_445", "amount": 150.00, "currency": "USD" }
  ```
- **Response (201 Created):**
  ```json
  { "invoice_id": "inv_990", "status": "pending", "url": "https://vanguard.io/pay/inv_990" }
  ```

### 4.2 Records Endpoints

**3. GET `/api/v1/records/{patient_id}`**
- **Description:** Fetch the clinical record for a patient.
- **Request:** `GET /api/v1/records/pat_123`
- **Response (200 OK):**
  ```json
  {
    "patient_id": "pat_123",
    "name": "John Doe",
    "records": [ { "date": "2025-01-10", "note": "Routine checkup", "code": "Z00.00" } ]
  }
  ```

**4. POST `/api/v1/records/{patient_id}/upload`**
- **Description:** Upload a medical file (triggers virus scan).
- **Request:** `POST /api/v1/records/pat_123/upload` (Multipart/form-data)
- **Response (202 Accepted):**
  ```json
  { "file_id": "file_abc", "status": "scanning", "message": "File is being scanned for viruses." }
  ```

### 4.3 Tenant & Auth Endpoints

**5. GET `/api/v1/tenant/profile`**
- **Description:** Get organization details.
- **Response (200 OK):**
  ```json
  { "tenant_id": "org_55", "name": "Northside Clinic", "region": "US-East" }
  ```

**6. PUT `/api/v1/tenant/settings`**
- **Description:** Update clinic configurations.
- **Request:** `PUT /api/v1/tenant/settings` `{ "timezone": "EST", "currency": "USD" }`
- **Response (200 OK):** `{ "status": "updated" }`

### 4.4 Dashboard Endpoints

**7. GET `/api/v1/dashboard/layout`**
- **Description:** Fetch saved widget layout.
- **Response (200 OK):**
  ```json
  { "layout": [ { "id": "widget_1", "x": 0, "y": 0, "w": 2, "h": 2 } ] }
  ```

**8. POST `/api/v1/dashboard/layout`**
- **Description:** Save new widget layout.
- **Request:** `POST /api/v1/dashboard/layout` `{ "layout": [...] }`
- **Response (200 OK):** `{ "status": "saved" }`

---

## 5. DATABASE SCHEMA

The system uses a hybrid approach: PostgreSQL for relational records and MongoDB for unstructured billing logs.

### 5.1 PostgreSQL Schema (Core)

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | - | `name`, `plan_type`, `created_at` | The root organization |
| `users` | `user_id` | `tenant_id` | `email`, `password_hash`, `role` | System users |
| `patients` | `patient_id` | `tenant_id` | `first_name`, `last_name`, `dob` | Patient demographics |
| `clinical_records` | `record_id` | `patient_id`, `tenant_id` | `clinical_note`, `icd_code`, `timestamp` | Medical entries |
| `files` | `file_id` | `patient_id`, `tenant_id` | `s3_path`, `mime_type`, `scan_status` | Metadata for uploads |
| `audit_logs` | `log_id` | `user_id`, `tenant_id` | `action`, `resource_id`, `timestamp` | HIPAA Access logs |
| `dashboard_configs`| `config_id` | `user_id` | `layout_json`, `updated_at` | User UI preferences |
| `appointments` | `appt_id` | `patient_id`, `tenant_id` | `start_time`, `end_time`, `status` | Scheduling |
| `insurance_providers`| `provider_id` | - | `company_name`, `payer_id` | Insurance entities |
| `claims` | `claim_id` | `record_id`, `provider_id` | `amount_claimed`, `status` | Financial claims |

### 5.2 Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many.
- **Tenants $\rightarrow$ Patients:** One-to-Many (Strict isolation).
- **Patients $\rightarrow$ Clinical Records:** One-to-Many.
- **Users $\rightarrow$ Audit Logs:** One-to-Many.
- **Clinical Records $\rightarrow$ Claims:** One-to-One.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Deployment Strategy: The Weekly Release Train
Vanguard operates on a strict **Weekly Release Train**. 
- **Schedule:** Every Tuesday at 03:00 UTC.
- **Rule:** If a feature is not "Production Ready" (passed QA and Security) by Monday 12:00 UTC, it is bumped to the next train.
- **No Hotfixes:** To ensure stability and HIPAA compliance, hotfixes are prohibited. Critical bugs are bundled into the next train unless there is a total system outage, in which case an Emergency Change Request (ECR) must be signed by Jasper Jensen.

### 6.2 Environment Descriptions

#### 6.2.1 Development (Dev)
- **Purpose:** Local iteration and feature development.
- **Infrastructure:** Dockerized local environments.
- **Data:** Synthetic seed data; no real patient data allowed.

#### 6.2.2 Staging (QA/UAT)
- **Purpose:** Integration testing and User Acceptance Testing (UAT).
- **Infrastructure:** AWS EKS Cluster (small), RDS Postgres.
- **Deployment:** Automated via CI pipeline upon merge to `develop` branch.
- **Data:** Anonymized production snapshots.

#### 6.2.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Infrastructure:** Multi-AZ AWS EKS Cluster, Aurora PostgreSQL (Global), CloudFront CDN.
- **Deployment:** Manual trigger of the Release Train pipeline.
- **Data:** Fully encrypted, real patient records.

### 6.3 CI Pipeline Optimization
Current technical debt has resulted in a **45-minute CI pipeline**. The optimization plan is:
1. **Parallelization:** Split unit tests into 4 parallel shards (Target: -20 mins).
2. **Caching:** Implement Docker layer caching for Node modules (Target: -10 mins).
3. **Selective Testing:** Only run tests for changed modules using `git diff` (Target: -10 mins).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** Jest (Frontend), JUnit 5 (Java), Mocha (Node).
- **Requirement:** Minimum 80% code coverage for all Domain logic.
- **Focus:** Pure functions, business rules, and input validation.

### 7.2 Integration Testing
- **Tool:** Postman/Newman, TestContainers.
- **Focus:** Port-Adapter communication. Specifically, testing the `PostgresBillingAdapter` against a real database instance to ensure RLS (Row Level Security) is functioning.
- **Frequency:** Run on every merge request to the `develop` branch.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Critical Paths:** 
  - Patient record creation $\rightarrow$ Billing trigger $\rightarrow$ Payment success.
  - File upload $\rightarrow$ Virus scan $\rightarrow$ View via CDN.
  - Tenant A attempting to access Tenant B's record $\rightarrow$ 403 Forbidden.

### 7.4 Security Testing (Penetration Testing)
- **Quarterly Audits:** Third-party security firms will perform black-box testing.
- **Static Analysis:** Snyk and SonarQube integrated into the CI pipeline to catch OWASP Top 10 vulnerabilities.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Team lacks experience in the mixed tech stack | High | High | Hire a specialized contractor for 3 months to provide mentorship and reduce bus factor. |
| **R2** | Project sponsor rotating out of role | Medium | Medium | Document all architectural decisions and workarounds; establish a transition period with the new sponsor. |
| **R3** | CI pipeline slowness delaying releases | High | Low | Implementation of the Pipeline Optimization Plan (Section 6.3). |
| **R4** | Data leak between tenants | Low | Critical | Mandatory RLS in Postgres and automated E2E "cross-tenant" tests. |
| **R5** | Regulatory change in HIPAA laws | Low | Medium | Monthly compliance review with the legal team. |

### 8.1 Probability/Impact Matrix
- **High/High:** Immediate action required (R1).
- **High/Low:** Monitor and optimize (R3).
- **Low/Critical:** Robust prevention and testing (R4).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundation (May 2025 - August 2025)
- **Focus:** Hexagonal setup, Security hardening, and Billing Engine.
- **Dependencies:** Contractor onboarding.
- **Target Milestone 1:** **Security Audit Passed (2025-08-15)**.

### 9.2 Phase 2: Feature Build-out (August 2025 - October 2025)
- **Focus:** File upload pipeline, Multi-tenant isolation, and Dashboard design.
- **Dependencies:** Return of the lead architect from medical leave.
- **Target Milestone 2:** **External Beta with 10 Pilot Users (2025-10-15)**.

### 9.3 Phase 3: Stabilization & Launch (October 2025 - December 2025)
- **Focus:** Performance tuning (p95 response time), API versioning, and Onboarding.
- **Dependencies:** Beta feedback loop.
- **Target Milestone 3:** **First Paying Customer Onboarded (2025-12-15)**.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. These notes summarize the key decisions made during the calls.*

### Meeting 1: Architecture Alignment (2025-05-20)
- **Participants:** Jasper Jensen, Yara Liu, Amira Fischer.
- **Discussion:** Debate over whether to use a monolithic database or a database-per-tenant approach. 
- **Decision:** Decided on shared infrastructure with Row Level Security (RLS). Amira expressed concern that users might feel "less secure" with shared DBs, but Jasper overruled based on the $800k budget constraint.
- **Action Item:** Jasper to research the specific RLS implementation for PostgreSQL 15.

### Meeting 2: The "Blocker" Sync (2025-06-05)
- **Participants:** Jasper Jensen, Dina Moreau.
- **Discussion:** Discussion on the impact of the Lead Architect's 6-week medical leave. 
- **Decision:** Feature 3 (Multi-tenant isolation) is officially moved to "Blocked." The team will focus on the Billing Engine and File Uploads (which are less dependent on the core DB schema) in the interim.
- **Action Item:** Dina to contact the contractor to see if they can cover the architectural gap.

### Meeting 3: Release Train Protocol (2025-06-12)
- **Participants:** Full Team.
- **Discussion:** Yara Liu argued that "critical hotfixes" should be allowed outside the weekly train to keep the UI polished.
- **Decision:** Jasper denied the request. The "No Hotfix" rule stands to ensure that the catastrophic failure of the previous version is not repeated through rushed patches.
- **Action Item:** Yara to build a "Feature Flag" system to toggle off buggy features without needing a new deployment.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000  
**Duration:** 6 Months (Build) + 2 Months (Beta/Stabilization)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Salaries for Jasper, Yara, Amira, Dina + External Contractor. |
| **Infrastructure** | 15% | $120,000 | AWS (EKS, Aurora, S3, CloudFront) and MongoDB Atlas. |
| **Tools & Licenses** | 10% | $80,000 | Snyk, SonarQube, Stripe Fees, Zoom, Jira, ClamAV Enterprise. |
| **Contingency** | 10% | $80,000 | Reserve for emergency contractor hours or infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: Performance Metrics & Success Criteria
To validate the success of Project Vanguard, the following metrics will be tracked using Datadog:
- **API Response Time:** p95 latency must be $\le 200\text{ms}$ during peak load (defined as 50 concurrent requests per second).
- **NPS (Net Promoter Score):** Measured via an in-app survey 30 days after onboarding. Target: $\text{NPS} > 40$.
- **Error Rate:** The billing error rate must drop from 12% to $< 0.5\%$.

### Appendix B: Technical Debt Log & Resolution Path
| Debt Item | Description | Estimated Effort | Resolution |
| :--- | :--- | :--- | :--- |
| **CI Pipeline** | 45-minute build time | Medium | Parallelize tests in Phase 1. |
| **Legacy Stack A** | Java 8 dependencies | High | Wrap in a REST adapter; migrate to Java 17 in Phase 2. |
| **Frontend Debt** | Angular 8 $\rightarrow$ React migration | Medium | Incremental migration using a "Strangler Fig" pattern. |
| **Manual Billing** | Manual invoice entry | Low | Automate via the `BillingEngine` service. |