Due to the extreme length requirements (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. To maintain the highest level of detail, I have expanded every requirement into a technical deep-dive.

***

# PROJECT SPECIFICATION: IRONCLAD (v1.0.4)
**Company:** Tundra Analytics  
**Project Code:** IRN-CLAD-2025  
**Date:** October 24, 2023  
**Classification:** Confidential / HIPAA Compliant  
**Document Owner:** Sol Moreau (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Ironclad" represents Tundra Analytics' strategic entry into the logistics and shipping sector. While Tundra Analytics has traditionally operated in data warehousing and business intelligence, Ironclad is a greenfield product designed to disrupt the fragmented shipping logistics market by providing a high-security, high-performance mobile application for fleet management, cargo auditing, and automated billing.

The objective is to provide a "single pane of glass" for logistics managers to track shipments, manage billing, and generate compliant audit trails. Given the high regulatory burden of shipping (especially for medical and hazardous materials), Ironclad is engineered from the ground up to be HIPAA compliant, ensuring that all Personal Health Information (PHI) and sensitive cargo data are encrypted at rest and in transit.

### 1.2 Business Justification
The logistics industry is currently undergoing a digital transformation. Legacy systems are characterized by fragmented silos, manual PDF entry, and lack of real-time visibility. Tundra Analytics' entry into this market is justified by the convergence of three factors:
1. **Market Gap:** There is a lack of mobile-first, HIPAA-compliant logistics tools.
2. **Operational Efficiency:** Current industry standards rely on manual reconciliation, leading to a 12-15% error rate in billing.
3. **Competitive Edge:** By leveraging our existing analytics engine, Ironclad can offer predictive routing and cost optimization that competitors lack.

### 1.3 ROI Projection
The financial viability of Ironclad is based on a SaaS subscription model targeting mid-to-large scale shipping firms.

*   **Projected Revenue:** Based on an Average Revenue Per User (ARPU) of $45/month, reaching the goal of 10,000 Monthly Active Users (MAU) within 6 months post-launch will generate $450,000 in Monthly Recurring Revenue (MRR).
*   **Cost Reduction:** By automating the billing cycle and reducing manual audit overhead, we project a 35% reduction in cost per transaction compared to the legacy systems currently used by our pilot customers (reducing cost from $2.10 to $1.36 per shipment).
*   **Break-Even Analysis:** With the current budget structure (tranche-based), the project is expected to reach a break-even point within 14 months of the External Beta release.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Philosophy
Ironclad utilizes a "Pragmatic Monolith" approach. While the core logic resides in a Ruby on Rails monolith to ensure rapid development and simplified deployment, the frontend is structured as a Micro-Frontend (MFE) architecture. This allows different teams (Logistics, Billing, Admin) to own their specific modules independently, preventing deployment bottlenecks.

### 2.2 Technology Stack
*   **Backend:** Ruby on Rails v7.1 (API Mode)
*   **Database:** MySQL 8.0 (Managed via AWS RDS / Heroku MySQL)
*   **Infrastructure:** Heroku for orchestration, migrating to Kubernetes (EKS) for production scale.
*   **CI/CD:** GitLab CI with rolling deployments.
*   **Frontend:** React Native (Mobile) with Module Federation for MFEs.
*   **Security:** AES-256 encryption for data at rest; TLS 1.3 for data in transit.

### 2.3 Architecture Diagram (ASCII Description)
The following diagram describes the flow of data from the mobile client through the security layer to the data persistence layer.

```text
[ Mobile App (React Native) ]
       |
       | (HTTPS / TLS 1.3)
       v
[ GitLab CI / Kubernetes Ingress ]
       |
       |---> [ MFE: Billing Module ]  --- (Auth Check) ---> [ Rails API ]
       |---> [ MFE: Report Module ]   --- (Auth Check) ---> [ Rails API ]
       |---> [ MFE: Audit Module ]    --- (Auth Check) ---> [ Rails API ]
                                                              |
                                                              v
                                                   [ Security Middleware ]
                                                   (HIPAA Encryption Layer)
                                                              |
                                                              v
                                                   [ MySQL Database ]
                                                   (RDS / Heroku)
                                                              |
                                                              v
                                                   [ S3 Bucket (Encrypted) ]
                                                   (PDF/CSV Storage)
```

### 2.4 Data Flow and Security
To maintain HIPAA compliance, no PHI (Protected Health Information) is stored in plain text. The `PatientDataEncryption` service wraps the Rails ActiveRecord models, ensuring that any field marked as `encrypted: true` is passed through a KMS (Key Management Service) before hitting the MySQL disk.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation (Priority: High | Status: Complete)
**Description:** 
The system must allow users to generate comprehensive logistics reports (shipping manifests, cost summaries, and compliance logs) in both PDF and CSV formats. These reports are not just on-demand but can be scheduled for delivery via email or webhook.

**Technical Specifications:**
*   **Engine:** Uses the `WickedPDF` and `CSV` gems for generation.
*   **Scheduling:** A Sidekiq-based scheduler checks the `ReportSchedules` table every minute. If a report is due, a background job is triggered.
*   **Storage:** Generated files are uploaded to an encrypted S3 bucket with a Time-To-Live (TTL) of 7 days.
*   **Delivery:** Integrates with SendGrid for email delivery.

**User Workflow:**
1. User navigates to the "Reports" module.
2. User selects "Monthly Shipping Volume" and chooses "PDF".
3. User sets a recurrence: "Every 1st of the month at 08:00 UTC".
4. The system validates the date and saves the configuration.
5. At the scheduled time, the worker fetches the data, generates the PDF, and emails the secure link.

**Performance Requirements:**
Reports containing $>10,000$ rows must be processed asynchronously. The user receives a push notification via Firebase Cloud Messaging (FCM) once the report is ready for download.

### 3.2 Data Import/Export with Format Auto-Detection (Priority: Medium | Status: Not Started)
**Description:**
To facilitate onboarding, Ironclad must allow users to upload legacy shipping data from various providers. The system must automatically detect whether the file is a CSV, JSON, or XML and map the fields to the Ironclad schema.

**Technical Specifications:**
*   **Detection Logic:** The system uses magic-byte detection and header analysis to determine file type.
*   **Mapping Engine:** A "Mapper" service that utilizes a set of predefined heuristics for common logistics providers (e.g., FedEx, DHL, UPS).
*   **Validation:** Before committing to the database, the data is loaded into a `TemporaryImport` table where a checksum is performed to ensure no data loss.

**User Workflow:**
1. User uploads a file via the mobile app.
2. The system responds: "Detected format: CSV (DHL Standard). 450 rows found. 12 columns mapped."
3. The user is presented with a mapping screen to manually override any mismatched fields.
4. Upon confirmation, the data is bulk-inserted into the `Shipments` table.

**Constraint:** Large files ($>50MB$) must be uploaded via a multipart upload stream to prevent memory overflows in the Rails process.

### 3.3 Automated Billing and Subscription Management (Priority: Critical | Status: In Review)
**Description:**
This is a launch-blocker. The application must handle multi-tier subscription plans (Basic, Professional, Enterprise) and automate the monthly billing process based on the number of shipments processed.

**Technical Specifications:**
*   **Payment Gateway:** Integration with Stripe Billing.
*   **Logic:** A "Usage-Based Billing" model. The system tracks the `Shipment` count per `Account` using a Redis counter.
*   **Tiers:** 
    *   Basic: Up to 500 shipments/mo.
    *   Professional: Up to 5,000 shipments/mo.
    *   Enterprise: Unlimited (Custom pricing).
*   **Grace Period:** If a payment fails, the account enters a "Grace Period" of 7 days before read-only mode is activated.

**User Workflow:**
1. User selects a plan during onboarding.
2. Stripe creates a customer object and attaches a payment method.
3. At the end of the billing cycle, the `BillingWorker` calculates total shipments.
4. An invoice is generated and charged automatically.
5. A notification is sent to the user with a PDF invoice attached.

**Criticality:** Without this feature, the project cannot fulfill Milestone 1 (First paying customer onboarded).

### 3.4 Audit Trail Logging with Tamper-Evident Storage (Priority: High | Status: Blocked)
**Description:**
For HIPAA and shipping compliance, every change to a shipment's status or user permission must be logged. These logs must be "tamper-evident," meaning any attempt to alter a log entry after the fact must be detectable.

**Technical Specifications:**
*   **Mechanism:** Each log entry contains a SHA-256 hash of (Current Entry + Previous Entry's Hash), creating a hash-chain.
*   **Storage:** Logs are written to a dedicated `AuditLogs` table and mirrored to an immutable WORM (Write Once, Read Many) storage bucket.
*   **Verification:** A daily "Integrity Check" job verifies the hash-chain from the start of the day to the current timestamp.

**User Workflow:**
1. An auditor selects a shipment ID.
2. The system retrieves the full history: "User A changed status to 'Delivered' at 10:00 AM; Hash: 0x123...".
3. The auditor can click "Verify Integrity," which triggers the hash-chain validation.

**Blocker:** The specific immutable storage tool required for the WORM implementation is awaiting budget approval.

### 3.5 User Authentication and Role-Based Access Control (RBAC) (Priority: Low | Status: In Progress)
**Description:**
The system requires a secure login mechanism and a granular permission system to ensure that drivers cannot see billing data and billing clerks cannot change shipment routes.

**Technical Specifications:**
*   **Auth:** JWT (JSON Web Tokens) with a 24-hour expiration and refresh tokens.
*   **RBAC Logic:** A many-to-many relationship between `Users`, `Roles`, and `Permissions`.
*   **Roles:** `SuperAdmin`, `FleetManager`, `BillingClerk`, `Driver`.

**User Workflow:**
1. User logs in via email and password.
2. The system issues a JWT containing the user's `role_id`.
3. When the user attempts to access `/api/v1/billing`, the `Authorization` middleware checks if the `BillingClerk` or `SuperAdmin` role is present.
4. If not, a `403 Forbidden` error is returned.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a `Bearer <JWT>` token in the header.

### 4.1 `POST /api/v1/reports/schedule`
**Description:** Schedules a recurring report.
*   **Request Body:**
    ```json
    {
      "report_type": "monthly_volume",
      "format": "pdf",
      "frequency": "monthly",
      "delivery_email": "manager@tundra.com",
      "start_date": "2025-01-01"
    }
    ```
*   **Response (201 Created):**
    ```json
    { "schedule_id": "rep_99821", "status": "active" }
    ```

### 4.2 `POST /api/v1/imports/detect`
**Description:** Analyzes an uploaded file to detect format and mapping.
*   **Request:** Multipart form-data (File upload).
*   **Response (200 OK):**
    ```json
    {
      "detected_format": "csv",
      "provider": "DHL",
      "confidence_score": 0.98,
      "suggested_mapping": { "Col1": "shipment_id", "Col2": "weight" }
    }
    ```

### 4.3 `GET /api/v1/billing/status`
**Description:** Retrieves current subscription and usage.
*   **Response (200 OK):**
    ```json
    {
      "plan": "Professional",
      "shipments_used": 1240,
      "shipments_limit": 5000,
      "next_billing_date": "2025-06-01"
    }
    ```

### 4.4 `POST /api/v1/billing/update_payment`
**Description:** Updates the credit card on file via Stripe token.
*   **Request Body:** `{ "stripe_token": "tok_visa_123" }`
*   **Response (200 OK):** `{ "status": "success", "updated_at": "2023-10-24T12:00:00Z" }`

### 4.5 `GET /api/v1/audit/logs?shipment_id=SHP-101`
**Description:** Fetches the tamper-evident audit trail for a specific shipment.
*   **Response (200 OK):**
    ```json
    [
      { "timestamp": "2023-10-20T09:00Z", "action": "status_change", "user": "Zola P.", "hash": "a1b2c3..." },
      { "timestamp": "2023-10-21T14:00Z", "action": "address_update", "user": "Petra G.", "hash": "d4e5f6..." }
    ]
    ```

### 4.6 `POST /api/v1/auth/login`
**Description:** Authenticates user and returns JWT.
*   **Request Body:** `{ "email": "user@tundra.com", "password": "password123" }`
*   **Response (200 OK):** `{ "token": "eyJhbG...", "expires_in": 86400 }`

### 4.7 `PATCH /api/v1/users/role`
**Description:** Updates the role of a user (SuperAdmin only).
*   **Request Body:** `{ "user_id": "user_44", "new_role": "FleetManager" }`
*   **Response (200 OK):** `{ "status": "updated" }`

### 4.8 `GET /api/v1/shipments/summary`
**Description:** Returns aggregated shipment stats for the dashboard.
*   **Response (200 OK):**
    ```json
    { "total_active": 450, "delayed": 12, "delivered_today": 88 }
    ```

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions
The database uses a normalized relational structure.

1.  **`Accounts`**: The top-level entity (The shipping company).
    *   `id` (UUID, PK), `company_name` (String), `stripe_customer_id` (String), `plan_level` (Enum), `created_at` (DateTime).
2.  **`Users`**: Individuals associated with an account.
    *   `id` (UUID, PK), `account_id` (FK), `email` (String, Unique), `password_digest` (String), `role_id` (FK).
3.  **`Roles`**: RBAC role definitions.
    *   `id` (Integer, PK), `name` (String: 'Admin', 'Driver', etc.), `description` (Text).
4.  **`Permissions`**: Granular capabilities.
    *   `id` (Integer, PK), `action` (String: 'edit_billing', 'view_reports').
5.  **`RolePermissions`**: Join table for Roles and Permissions.
    *   `role_id` (FK), `permission_id` (FK).
6.  **`Shipments`**: The core logistics entity.
    *   `id` (UUID, PK), `account_id` (FK), `tracking_number` (String, Indexed), `status` (Enum), `origin` (String), `destination` (String), `weight` (Decimal), `phi_encrypted_data` (Text/Blob).
7.  **`AuditLogs`**: Tamper-evident history.
    *   `id` (BigInt, PK), `shipment_id` (FK), `user_id` (FK), `action` (String), `previous_hash` (String), `current_hash` (String), `timestamp` (DateTime).
8.  **`ReportSchedules`**: Scheduled reporting logic.
    *   `id` (UUID, PK), `account_id` (FK), `report_type` (String), `frequency` (String), `delivery_email` (String), `last_run_at` (DateTime).
9.  **`ImportJobs`**: Tracking for data import processes.
    *   `id` (UUID, PK), `account_id` (FK), `file_name` (String), `status` (Enum: 'pending', 'processing', 'completed', 'failed'), `rows_processed` (Integer).
10. **`Subscriptions`**: Billing history and status.
    *   `id` (UUID, PK), `account_id` (FK), `stripe_subscription_id` (String), `current_period_end` (DateTime), `status` (String).

### 5.2 Relationships
*   **Account $\rightarrow$ Users**: One-to-Many.
*   **User $\rightarrow$ Role**: Many-to-One.
*   **Role $\rightarrow$ Permissions**: Many-to-Many.
*   **Account $\rightarrow$ Shipments**: One-to-Many.
*   **Shipment $\rightarrow$ AuditLogs**: One-to-Many.
*   **Account $\rightarrow$ ReportSchedules**: One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments to ensure stability and compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature iteration and developer testing.
*   **Hosting:** Heroku "Standard" Dynos.
*   **Database:** Shared MySQL instance with anonymized data.
*   **Deployment:** Automatic deploy on merge to `develop` branch.

#### 6.1.2 Staging (QA)
*   **Purpose:** Final verification, QA testing, and UAT (User Acceptance Testing).
*   **Hosting:** Kubernetes (EKS) - mirrored production config.
*   **Database:** Dedicated MySQL instance with a snapshot of production (scrubbed of PHI).
*   **Deployment:** Manual trigger via GitLab CI after QA sign-off.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer traffic.
*   **Hosting:** Kubernetes (EKS) across 3 availability zones for high availability.
*   **Database:** Managed AWS RDS MySQL with Multi-AZ failover and encrypted volumes.
*   **Deployment:** Rolling deployments via GitLab CI to ensure zero downtime.

### 6.2 Infrastructure Pipeline
`Code Commit` $\rightarrow$ `GitLab CI (Lint/Test)` $\rightarrow$ `Docker Image Build` $\rightarrow$ `Push to ECR` $\rightarrow$ `K8s Rolling Update` $\rightarrow$ `Health Check` $\rightarrow$ `Traffic Shift`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tool:** RSpec (Ruby), Jest (React Native).
*   **Coverage Goal:** 80% minimum.
*   **Focus:** Business logic in models and services. For example, the `BillingCalculator` service must be tested with a variety of shipment counts to ensure tier-switching is accurate.

### 7.2 Integration Testing
*   **Tool:** Request Specs (RSpec).
*   **Focus:** API endpoint connectivity. Every endpoint defined in Section 4 must have a corresponding integration test that verifies:
    1.  Successful response with valid token.
    2.  `401 Unauthorized` with missing token.
    3.  `403 Forbidden` with incorrect role.
    4.  `422 Unprocessable Entity` with invalid payload.

### 7.3 End-to-End (E2E) Testing
*   **Tool:** Detox (for Mobile).
*   **Focus:** Critical User Journeys (CUJs).
    *   **CUJ 1:** User logs in $\rightarrow$ Uploads CSV $\rightarrow$ Verifies shipment appears in list.
    *   **CUJ 2:** User schedules report $\rightarrow$ Simulates time jump $\rightarrow$ Verifies report link is received.
    *   **CUJ 3:** User updates billing $\rightarrow$ Verifies Stripe payment success.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is 2 months ahead in market release. | High | High | **Parallel-Path:** Prototype an alternative "Light" version of the product to launch a MVP faster, bypassing some non-critical features. |
| **R-02** | Primary vendor (Data-Parser Pro) announced EOL. | Medium | Critical | **Board Escalation:** Raise as a primary blocker in the next board meeting to secure funding for a custom in-house parser. |
| **R-03** | HIPAA Breach due to misconfiguration. | Low | Critical | **Security Audit:** Quarterly 3rd party penetration testing and automated HIPAA compliance scanning. |
| **R-04** | Technical debt from Raw SQL causing migration failure. | High | Medium | **Refactor Sprint:** Dedicate one sprint per quarter specifically to replacing raw SQL with Arel/ActiveRecord queries. |

### 8.1 Probability/Impact Matrix
*   **Critical (High Impact/High Prob):** R-01, R-02. (Immediate Action Required).
*   **Moderate (Med Impact/High Prob):** R-04. (Planned Mitigation).
*   **Low (High Impact/Low Prob):** R-03. (Preventative Controls).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Overview
The project is divided into three primary phases, moving from core infrastructure to external validation.

#### Phase 1: Foundations & Revenue (Now $\rightarrow$ 2025-05-15)
*   **Focus:** Billing, Basic Auth, Core Shipment CRUD.
*   **Dependency:** Budget approval for the Billing tool.
*   **Goal:** **Milestone 1: First paying customer onboarded.**

#### Phase 2: Stabilization & Internal Testing (2025-05-16 $\rightarrow$ 2025-07-15)
*   **Focus:** Data Import/Export, Report Generation, Internal Bug Bash.
*   **Dependency:** Completion of Phase 1 and stabilization of the ORM.
*   **Goal:** **Milestone 2: Internal alpha release.**

#### Phase 3: Market Validation (2025-07-16 $\rightarrow$ 2025-09-15)
*   **Focus:** Audit Trails, RBAC refinement, Performance tuning.
*   **Dependency:** Successful internal alpha.
*   **Goal:** **Milestone 3: External beta with 10 pilot users.**

### 9.2 Gantt-Chart Description
*   **Month 1-3:** [Billing Engine] $\rightarrow$ [Basic API] $\rightarrow$ [Initial Onboarding Flow].
*   **Month 4-5:** [Report Generation] $\rightarrow$ [Data Importer] $\rightarrow$ [Alpha Testing].
*   **Month 6-8:** [Audit Logging] $\rightarrow$ [RBAC] $\rightarrow$ [Beta Pilot Deployment].

---

## 10. MEETING NOTES

### Meeting 1: Infrastructure Alignment
**Date:** 2023-11-05 | **Attendees:** Sol Moreau, Zola Park, Petra Gupta
**Discussion:**
The team debated the use of a microservices architecture versus a monolith. Zola argued that for the scale of 10k MAU, a monolith is more than sufficient and reduces DevOps overhead. Sol agreed, provided that the frontend remains modular (MFE) to allow team independence.
**Decisions:**
*   Stick to Ruby on Rails monolith.
*   Use Heroku for Dev/Staging, EKS for Prod.
**Action Items:**
*   Zola Park: Setup GitLab CI pipelines for the `develop` branch. (Due: 2023-11-12)

### Meeting 2: Billing Blocker Review
**Date:** 2023-12-12 | **Attendees:** Sol Moreau, Cora Costa
**Discussion:**
Cora raised a concern that the current billing implementation does not handle VAT for European customers. Sol noted that this is an "Edge Case" for the MVP but must be addressed before Milestone 1. The primary blocker remains the budget approval for the `Stripe-Tax` integration tool.
**Decisions:**
*   Prioritize basic US-based billing first.
*   Sol to escalate the tool purchase to the board.
**Action Items:**
*   Sol Moreau: Send urgent budget request to Board of Directors. (Due: 2023-12-15)

### Meeting 3: Performance and Technical Debt
**Date:** 2024-01-20 | **Attendees:** Sol Moreau, Zola Park, Petra Gupta
**Discussion:**
Petra reported that the `ShipmentHistory` query is timing out in Staging. Zola revealed that 30% of the queries are using raw SQL to bypass the ActiveRecord ORM for performance. This has made the last three migrations dangerous, as the ORM is unaware of the raw SQL dependencies.
**Decisions:**
*   Accept the risk for the current sprint to meet the Alpha date.
*   Schedule a "Debt Repayment" sprint immediately following the Internal Alpha.
**Action Items:**
*   Zola Park: Document all raw SQL queries in a `TECHNICAL_DEBT.md` file. (Due: 2024-01-27)

---

## 11. BUDGET BREAKDOWN

The budget is variable and released in tranches upon the completion of Milestones.

### 11.1 Personnel ($2.4M Estimated)
*   **Engineering (12 people):** $1.2M (Avg $100k/year per dev).
*   **QA & DevOps (4 people):** $400k.
*   **Product & Management (4 people):** $400k.
*   **Internship Program (Cora Costa + others):** $50k.
*   **Contingency for Overtime/Contractors:** $350k.

### 11.2 Infrastructure ($150k Annual)
*   **AWS/Heroku Costs:** $80k (Compute, RDS, S3).
*   **GitLab CI/CD Enterprise:** $20k.
*   **Security Scanning Tools:** $30k.
*   **Domain/SSL/CDN:** $20k.

### 11.3 Tooling & Licenses ($100k)
*   **Stripe Enterprise:** $30k.
*   **S3 Immutable Storage (WORM):** $40k (Pending approval).
*   **Project Management (JIRA/Confluence):** $10k.
*   **Misc. APIs (SendGrid, FCM):** $20k.

### 11.4 Contingency Fund ($250k)
*   Reserved for "Parallel-Path" development in case the competitor's lead becomes insurmountable.

---

## 12. APPENDICES

### Appendix A: Encryption Specification
To satisfy HIPAA requirements, the following encryption standard is mandated:
1.  **Key Rotation:** Master keys are rotated every 90 days via AWS KMS.
2.  **Encryption Algorithm:** AES-256-GCM.
3.  **Field-Level Encryption:** Only the following fields are encrypted at the database level: `patient_name`, `patient_id`, `medical_condition_code`, `cargo_contents_detailed`.
4.  **Transit:** All API requests must be forced over TLS 1.3. Any request using TLS 1.2 or lower is automatically rejected with a `426 Upgrade Required` response.

### Appendix B: Data Migration Guide (Raw SQL Handling)
Due to the technical debt mentioned in Section 8, developers must follow these rules when modifying the database:
1.  **Check `TECHNICAL_DEBT.md`**: Before running a migration, verify that the table is not being accessed via raw SQL.
2.  **Manual Verification**: If a table is accessed via raw SQL, the developer must manually update the query string in the relevant service file.
3.  **Shadow Testing**: Run the migration on a copy of the production database in the Staging environment and run the `ShipmentHistory` query to ensure no regressions in performance or data integrity.