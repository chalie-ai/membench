# PROJECT SPECIFICATION DOCUMENT: PROJECT CAIRN
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Company:** Bridgewater Dynamics  
**Date:** October 24, 2023  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Cairn is a strategic platform modernization effort commissioned by Bridgewater Dynamics to transition the company’s core data pipeline and analytics engine from a legacy monolithic architecture to a scalable, microservices-oriented ecosystem. Operating within the food and beverage industry, Bridgewater Dynamics manages high-velocity supply chain data, ingredient sourcing metrics, and distribution analytics. The current system, while functional, has reached a point of technical saturation where the cost of maintenance exceeds the value of new feature development.

The objective of Cairn is to decouple the monolithic "God class" structures into discrete, manageable services that allow for independent scaling, deployment, and maintenance. This transition is scheduled over an 18-month horizon, aiming to replace the rigid legacy systems with a flexible three-tier architecture (Presentation, Business Logic, and Data) that can support the evolving demands of the food and beverage market.

### 1.2 Business Justification
The food and beverage sector is currently experiencing a shift toward "hyper-local" sourcing and real-time inventory transparency. The existing monolith cannot handle the increased telemetry from IoT-enabled warehouses or the complex multi-tenancy requirements of new partner integrations. By migrating to a microservices architecture, Bridgewater Dynamics can reduce system downtime by an estimated 40% and increase the velocity of feature releases from quarterly to bi-weekly.

Furthermore, the legacy system lacks the granular data isolation required for the company's expansion into third-party analytics services. Project Cairn introduces a robust multi-tenant framework, ensuring that client data is strictly isolated while leveraging shared infrastructure to maintain cost efficiency.

### 1.3 ROI Projection and Success Metrics
With a total budget allocation of $400,000, the project is designed to be a lean, focused effort. The primary financial goal is the generation of **$500,000 in new revenue** attributed directly to the Cairn platform within the first 12 months post-launch. This revenue will be driven by the introduction of tiered subscription models and the ability to onboard larger enterprise clients who require SOC 2 Type II compliance.

Beyond financial gains, the project's success will be measured by customer satisfaction. The target is a **Net Promoter Score (NPS) above 40** within the first quarter of the external beta launch. Achieving this will signal that the modernization has successfully addressed the latency and stability issues prevalent in the legacy system.

### 1.4 Strategic Alignment
Project Cairn aligns with the broader corporate goal of "Digital Transformation 2025," moving the company away from manual data reconciliation toward automated, real-time insights. By implementing automated billing and sophisticated report generation, Bridgewater Dynamics will transition from a service-provider model to a Product-as-a-Service (PaaS) model.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Cairn utilizes a traditional three-tier architecture but implements it through a microservices lens to facilitate the transition from the monolith. The system must interoperate across three inherited legacy stacks: a Python/Django framework (Data Processing), a Java/Spring Boot framework (Billing/Admin), and a Node.js/Express layer (Frontend API).

### 2.2 High-Level Component Diagram (ASCII)

```text
[ CLIENT LAYER ]  -->  [ API GATEWAY (Kong/Nginx) ]  --> [ AUTH SERVICE ]
                                |                              |
                                v                              v
                      [ BUSINESS LOGIC LAYER ] <------> [ SHARED CACHE (Redis) ]
                      /         |             \
      [ Data Import Svc ] [ Report Gen Svc ] [ Billing Svc ]
              |                 |                  |
              v                 v                  v
      [ DATA STORAGE LAYER (PostgreSQL / S3 / MongoDB) ]
              |                 |                  |
              +-----------------+------------------+
                                |
                      [ GitLab CI / CD Pipeline ]
                                |
                      [ Kubernetes (K8s) Cluster ]
                      (Dev -> Staging -> Production)
```

### 2.3 Detailed Tier Breakdown
- **Presentation Layer:** A React-based frontend communicating via RESTful APIs. It handles user interactions and triggers report generation requests.
- **Business Logic Layer:** A series of decoupled microservices. The core logic is being migrated out of the 3,000-line "God class" (the `SystemKernel` class) into specialized services.
- **Data Layer:** A polyglot persistence strategy. Relational data (users, subscriptions, tenant configs) resides in PostgreSQL; large-scale telemetry and food-industry logs are stored in MongoDB; generated reports are stored in AWS S3.

### 2.4 Deployment Strategy
The project utilizes **GitLab CI** for continuous integration and delivery. The deployment strategy is a **Rolling Deployment** to a Kubernetes cluster. This ensures that updates to the analytics engine do not cause downtime for the reporting services. 

**Environment Flow:**
1. `feature/*` branch $\rightarrow$ Dev Environment (Automated Unit Tests)
2. `develop` branch $\rightarrow$ Staging Environment (QA Lead Nadira Stein's sign-off)
3. `main` branch $\rightarrow$ Production Environment (SOC 2 Compliance Check)

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Critical | **Status:** In Progress | **Launch Blocker:** Yes

**Description:** 
The platform must support multiple food and beverage clients (tenants) on a single shared set of compute resources while ensuring that no tenant can ever access another tenant's data. This is the most critical technical hurdle for Project Cairn.

**Functional Requirements:**
- **Tenant Identification:** Every request must carry a `Tenant-ID` header. The API Gateway will validate this ID against the tenant registry.
- **Row-Level Security (RLS):** At the database level, PostgreSQL Row-Level Security will be implemented. Every table containing client data must have a `tenant_id` column. Queries will be automatically filtered based on the authenticated session's `tenant_id`.
- **Shared Compute:** To optimize the $400k budget, tenants will share the same Kubernetes pods. Isolation is achieved logically at the application and database layers rather than physically through separate clusters.
- **Schema Strategy:** A "Shared Schema, Shared Table" approach is adopted to minimize maintenance overhead.

**Technical Constraints:**
The system must handle up to 500 concurrent tenants without performance degradation. The data isolation layer must be transparent to the developers; the `TenantContext` object in the business logic layer must automatically inject the `tenant_id` into all repository calls.

**Acceptance Criteria:**
- A query from Tenant A must return a 403 Forbidden or an empty set if attempting to access a resource belonging to Tenant B.
- Performance overhead for RLS must be less than 50ms per query.

---

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical | **Status:** Complete | **Launch Blocker:** Yes

**Description:** 
Clients require high-fidelity reports on food supply chain efficiency, waste metrics, and vendor performance. These reports must be available for on-demand download and automated delivery via email.

**Functional Requirements:**
- **Format Support:** The system generates `.pdf` for executive summaries and `.csv` for raw data analysis.
- **Scheduling Engine:** A Quartz-based scheduler allows users to set report frequency (Daily, Weekly, Monthly).
- **Delivery Pipeline:** Reports are generated in a background worker, uploaded to an S3 bucket with a signed URL, and an email notification is sent via SendGrid.
- **Templates:** Dynamic templates are used to inject tenant-specific branding and logos into the PDF reports.

**Technical Implementation:**
The `ReportService` uses a headless Chrome instance (Puppeteer) to render HTML templates into PDFs. For CSVs, a streaming writer is used to prevent memory overflow when processing millions of rows of food inventory data.

**Acceptance Criteria:**
- Reports must be generated within 30 seconds for datasets up to 100k rows.
- Scheduled reports must be delivered within 15 minutes of the scheduled timestamp.
- PDF outputs must maintain consistent formatting across all standard page sizes (A4, Letter).

---

### 3.3 Automated Billing and Subscription Management
**Priority:** Critical | **Status:** Blocked | **Launch Blocker:** Yes

**Description:** 
To achieve the $500k revenue target, Cairn requires an integrated billing system that handles monthly subscriptions, usage-based overages (e.g., data volume processed), and automated invoicing.

**Functional Requirements:**
- **Tiered Pricing:** Support for "Basic," "Professional," and "Enterprise" tiers.
- **Metered Billing:** Tracking the number of API calls or GBs of data imported to bill for overages.
- **Subscription Lifecycle:** Automated handling of upgrades, downgrades, and cancellations.
- **Payment Gateway:** Integration with Stripe for credit card processing and automated recurring billing.

**Current Blocker:** 
Integration with the legacy Java-based accounting system is currently failing due to an incompatible version of the SOAP wrapper. Development is paused until the legacy API is patched.

**Technical Constraints:**
The billing service must maintain an immutable audit log of all transactions to meet SOC 2 compliance requirements. All currency calculations must use `BigDecimal` to avoid floating-point errors.

**Acceptance Criteria:**
- Automated invoice generation on the 1st of every month.
- Grace period of 7 days for failed payments before account suspension.

---

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** In Progress | **Nice to Have:** Yes

**Description:** 
The food and beverage industry uses a variety of legacy formats (XML, JSON, CSV, XLS). Cairn needs a flexible way to ingest this data without requiring manual configuration for every file.

**Functional Requirements:**
- **Auto-Detection:** The system analyzes the first 1KB of an uploaded file to determine the MIME type and delimiter.
- **Mapping Engine:** A UI-based mapper that allows users to link their source columns (e.g., "Prod_ID") to Cairn's internal schema ("product_identifier").
- **Bulk Export:** Ability to export any filtered view of the analytics dashboard back into CSV or JSON.
- **Validation:** Real-time validation of data types (e.g., ensuring a "Quantity" field is numeric).

**Technical Implementation:**
A pipeline of `FileAnalyzers` is used. The `MagicBytesAnalyzer` identifies the file type, and the `SchemaInferenceEngine` suggests the most likely mapping.

**Acceptance Criteria:**
- Correctly identify 95% of common CSV and JSON variants without user intervention.
- Export processes must be asynchronous to avoid timing out the HTTP connection.

---

### 3.5 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** Blocked | **Nice to Have:** Yes

**Description:** 
A granular permission system to control who can view reports, who can modify billing settings, and who can manage tenant configurations.

**Functional Requirements:**
- **Roles:** Admin, Manager, Viewer, and Auditor.
- **Permissions:** Fine-grained actions (e.g., `reports:export`, `billing:update`).
- **JWT Integration:** Secure token-based authentication using OAuth2/OpenID Connect.
- **Session Management:** Ability to revoke sessions globally or per-user.

**Current Blocker:** 
The "God class" currently handles authentication in a non-thread-safe manner. Attempting to implement RBAC on top of this class is causing regression bugs in the logging system. The Tech Lead (Aiko Oduya) has decided to block this until the God class is successfully decomposed.

**Acceptance Criteria:**
- A "Viewer" role must be unable to access the `/api/v1/billing` endpoint.
- Authentication tokens must expire every 24 hours and be refreshable.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require the `Tenant-ID` header.

### 4.1 Authentication & Session
**Endpoint:** `POST /auth/login`  
**Description:** Authenticates user and returns a JWT.  
**Request:**
```json
{
  "username": "anouk_m",
  "password": "secure_password_123"
}
```
**Response (200 OK):**
```json
{
  "token": "eyJhbGci...",
  "expires_in": 86400,
  "user_id": "u-99821"
}
```

### 4.2 Report Generation
**Endpoint:** `POST /reports/generate`  
**Description:** Triggers a report generation process.  
**Request:**
```json
{
  "report_type": "inventory_waste",
  "format": "pdf",
  "date_range": { "start": "2023-01-01", "end": "2023-01-31" }
}
```
**Response (202 Accepted):**
```json
{
  "job_id": "job-550e8400",
  "status": "processing",
  "estimated_completion": "2023-10-24T14:05:00Z"
}
```

### 4.3 Report Download
**Endpoint:** `GET /reports/download/{job_id}`  
**Description:** Retrieves the final report file.  
**Response:** 302 Redirect to S3 Signed URL.

### 4.4 Tenant Management
**Endpoint:** `GET /tenant/config`  
**Description:** Retrieves current tenant configuration and limits.  
**Response (200 OK):**
```json
{
  "tenant_name": "GlobalFoods Co",
  "plan": "Professional",
  "storage_limit_gb": 500,
  "user_seats": 15
}
```

### 4.5 Data Import
**Endpoint:** `POST /data/import`  
**Description:** Uploads a data file for processing.  
**Request:** Multipart/form-data (File upload).  
**Response (201 Created):**
```json
{
  "import_id": "imp-772",
  "detected_format": "csv",
  "rows_detected": 4500
}
```

### 4.6 Subscription Update
**Endpoint:** `PATCH /billing/subscription`  
**Description:** Changes the current subscription tier.  
**Request:**
```json
{
  "new_plan": "Enterprise"
}
```
**Response (200 OK):**
```json
{
  "status": "upgraded",
  "next_billing_date": "2023-11-01"
}
```

### 4.7 Metric Analytics
**Endpoint:** `GET /analytics/waste-metrics`  
**Description:** Returns aggregated waste data for the dashboard.  
**Response (200 OK):**
```json
{
  "total_waste_kg": 1240.5,
  "top_waste_category": "Dairy",
  "trend": "decreasing"
}
```

### 4.8 System Health
**Endpoint:** `GET /health`  
**Description:** Kubernetes liveness/readiness probe.  
**Response (200 OK):**
```json
{
  "status": "UP",
  "database": "connected",
  "cache": "connected"
}
```

---

## 5. DATABASE SCHEMA

The system utilizes a hybrid approach with PostgreSQL for relational integrity and MongoDB for high-volume event logs.

### 5.1 PostgreSQL Schema (Relational)

| Table Name | Description | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `tenants` | Core tenant registry | `tenant_id` (PK), `name`, `created_at`, `status` | 1:M with `users` |
| `users` | System user accounts | `user_id` (PK), `tenant_id` (FK), `email`, `password_hash` | M:1 with `tenants` |
| `roles` | RBAC Role definitions | `role_id` (PK), `role_name`, `permissions_json` | 1:M with `user_roles` |
| `user_roles` | Junction for User/Role | `user_id` (FK), `role_id` (FK) | M:M Junction |
| `subscriptions` | Billing plans | `sub_id` (PK), `tenant_id` (FK), `plan_type`, `start_date` | 1:1 with `tenants` |
| `invoices` | Billing history | `invoice_id` (PK), `tenant_id` (FK), `amount`, `status` | M:1 with `tenants` |
| `report_jobs` | Report tracking | `job_id` (PK), `tenant_id` (FK), `status`, `s3_path` | M:1 with `tenants` |
| `import_logs` | Import history | `import_id` (PK), `tenant_id` (FK), `file_name`, `rows_processed` | M:1 with `tenants` |
| `audit_logs` | SOC 2 Compliance logs | `log_id` (PK), `user_id` (FK), `action`, `timestamp`, `ip_address` | M:1 with `users` |
| `tenant_configs` | Tenant-specific settings | `config_id` (PK), `tenant_id` (FK), `setting_key`, `setting_value` | M:1 with `tenants` |

### 5.2 MongoDB Collections (Document)
- **`telemetry_events`**: Stores raw IoT data from food warehouses. Indexed by `tenant_id` and `timestamp`.
- **`report_snapshots`**: Stores the JSON representation of a report's data at the time of generation to ensure historical consistency.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Strategy
Cairn is deployed on a managed Kubernetes cluster (EKS). To maintain the budget of $400,000, we utilize **Spot Instances** for the `dev` and `staging` environments, while `prod` uses **On-Demand** instances for stability.

### 6.2 Environment Descriptions

#### 6.2.1 Development (`dev`)
- **Purpose:** Feature testing and initial integration.
- **Deployment:** Automated via GitLab CI on every push to `feature/*` branches.
- **Database:** Shared PostgreSQL instance with separate schemas per developer.
- **Resources:** 2 nodes, 4 vCPU, 16GB RAM.

#### 6.2.2 Staging (`staging`)
- **Purpose:** QA validation and UAT (User Acceptance Testing).
- **Deployment:** Triggered on merge to `develop`. This is the primary environment for Nadira Stein (QA Lead).
- **Database:** A sanitized clone of production data (anonymized).
- **Resources:** 3 nodes, 8 vCPU, 32GB RAM.

#### 6.2.3 Production (`prod`)
- **Purpose:** Live client traffic.
- **Deployment:** Manual trigger via GitLab CI after QA sign-off and Security Audit.
- **Database:** Highly available (HA) PostgreSQL cluster with multi-AZ replication.
- **Security:** SOC 2 Type II compliance controls active (Encryption at rest, TLS 1.3 in transit).
- **Resources:** 5+ nodes (Autoscaling), 16 vCPU+, 64GB RAM+.

### 6.3 CI/CD Pipeline Flow
1. **Commit:** Developer pushes code.
2. **Build:** GitLab Runner builds Docker image.
3. **Test:** Unit tests execute $\rightarrow$ if fail, pipeline stops.
4. **Deploy Dev:** Image pushed to Dev K8s namespace.
5. **QA Sign-off:** Nadira Stein marks the feature as "Verified" in Slack/GitLab.
6. **Deploy Prod:** Rolling update ensures zero-downtime.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every microservice must maintain $\ge 80\%$ code coverage.
- **Tools:** JUnit (Java), PyTest (Python), Jest (Node.js).
- **Focus:** Business logic in the "Service" layer. Mocking of database calls is mandatory.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between services (e.g., `ReportService` calling `TenantService`).
- **Tools:** Postman/Newman for API contract testing.
- **Focus:** Validating that the `Tenant-ID` is correctly propagated across service boundaries.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulation of complete user journeys (e.g., Login $\rightarrow$ Upload Data $\rightarrow$ Generate Report $\rightarrow$ Download PDF).
- **Tools:** Cypress.
- **Focus:** Critical path validation and UI responsiveness.

### 7.4 QA Workflow
Nadira Stein oversees the QA cycle. A "Bug" is only considered resolved when it is verified in the `staging` environment and a regression test is added to the E2E suite. Due to the "low-ceremony" team dynamic, bug reports are often initiated in Slack and then formalized in GitLab Issues.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for food data are finalized late. | High | High | Build a contingency fallback architecture with flexible schema mappings. |
| R-02 | Primary vendor for PDF engine announces EOL. | Medium | Medium | De-scope advanced PDF features or switch to an open-source alternative (e.g., WeasyPrint). |
| R-03 | SOC 2 Audit failure. | Low | Critical | Weekly compliance checks and internal audits by Aiko Oduya. |
| R-04 | "God Class" decomposition causes regressions. | High | Medium | Implement "Strangler Fig" pattern; migrate one function at a time. |
| R-05 | Budget overrun on cloud costs. | Medium | Low | Use K8s Horizontal Pod Autoscalers (HPA) and Spot Instances. |

**Probability/Impact Matrix:**
- **Critical:** Must be resolved before Milestone 1.
- **High:** Requires weekly monitoring.
- **Medium:** Managed via standard sprint planning.

---

## 9. TIMELINE AND MILESTONES

The project spans 18 months, but the critical path is focused on the next three milestones.

### 9.1 Phase 1: Foundation (Months 1-6)
- Focus on decomposing the God class and implementing the Tenant Isolation layer.
- **Dependency:** SOC 2 compliance framework must be established.

### 9.2 Phase 2: Feature Completion (Months 7-12)
- Completion of Reporting and Billing services.
- **Dependency:** Resolution of the SOAP wrapper issue for billing.

### 9.3 Phase 3: Beta and Stabilization (Months 13-18)
- External pilot users and performance tuning.

### 9.4 Critical Milestones

| Milestone | Description | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| **M1** | **Security Audit Passed** | 2025-08-15 | SOC 2 compliance logic implementation |
| **M2** | **External Beta (10 Users)** | 2025-10-15 | M1 completion + Report Gen stability |
| **M3** | **MVP Feature-Complete** | 2025-12-15 | M2 feedback + Billing integration |

---

## 10. MEETING NOTES (Running Document Excerpt)

*Note: The original project documentation consists of a 200-page shared running document that is currently unsearchable. Below are transcribed excerpts from three key decision meetings.*

### Meeting 1: Architecture Pivot (2023-11-12)
**Attendees:** Aiko, Anouk, Kenji
**Discussion:**
- Anouk raised concerns about using a separate database per tenant. She argued it would make the $400k budget impossible to maintain due to infrastructure costs.
- Kenji suggested Row-Level Security (RLS) in Postgres as a middle ground.
- **Decision:** Team agreed to "Shared Schema, Shared Table" using RLS.
- **Slack Follow-up:** Aiko confirmed this in `#cairn-dev` at 4:15 PM.

### Meeting 2: The "God Class" Crisis (2024-01-05)
**Attendees:** Aiko, Nadira, Anouk
**Discussion:**
- Nadira reported that three new bugs appeared in the email notification system after attempting to add RBAC roles.
- Aiko identified that the `SystemKernel` (God class) is handling authentication, logging, and email in a single 3,000-line block with shared mutable state.
- **Decision:** All work on Feature #1 (RBAC) is blocked. The team will prioritize extracting the `EmailService` and `LoggingService` into separate microservices.
- **Action:** Anouk to draft the new `EmailService` interface.

### Meeting 3: Vendor EOL Alert (2024-03-20)
**Attendees:** Aiko, Kenji
**Discussion:**
- Kenji noted that the vendor for the current data-import auto-detection library has announced End-of-Life (EOL) for version 4.x.
- Aiko evaluated the cost of upgrading to version 5.x versus building a custom parser.
- **Decision:** Since this is a "Low Priority" feature, we will stick to the current version until Milestone 2. If the library breaks, we will de-scope the "Auto-Detection" and force manual format selection.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Covers Aiko, Anouk, Nadira, and Kenji (Contractor) |
| **Infrastructure** | 20% | $80,000 | AWS EKS, RDS, S3, MongoDB Atlas |
| **Tools & Licensing** | 10% | $40,000 | GitLab Premium, SendGrid, Stripe Fees, SOC 2 Audit |
| **Contingency** | 5% | $20,000 | Reserve for regulatory changes (Risk R-01) |

**Financial Notes:**
- Kenji's contract is billed hourly at a fixed rate.
- Infrastructure costs are optimized using Spot instances in `dev` and `staging`.
- The $20k contingency fund is earmarked specifically for any architecture changes required by late-breaking regulatory requirements in the food and beverage sector.

---

## 12. APPENDICES

### Appendix A: The "God Class" (`SystemKernel.java`) Technical Debt Analysis
The `SystemKernel` class is the primary source of technical debt. It currently implements the following interfaces: `IAuthManager`, `ILogger`, `IEmailDispatcher`, `ITenantValidator`, and `IReportTrigger`.

**Key Issues:**
1. **Tight Coupling:** A change in the email template logic requires a full redeploy of the authentication system.
2. **Thread Safety:** The class uses a shared static `Map` for session tracking, leading to race conditions under high load.
3. **Maintainability:** With 3,000 lines of code, the cognitive load for new developers (like Kenji) is too high, leading to "fear-based development" where engineers avoid touching the core logic.

**Decomposition Plan:**
- Extract `AuthManager` $\rightarrow$ `AuthService` (Spring Boot)
- Extract `EmailDispatcher` $\rightarrow$ `NotificationService` (Node.js)
- Extract `Logger` $\rightarrow$ Centralized ELK Stack

### Appendix B: SOC 2 Type II Compliance Checklist
To meet the Milestone 1 target (2025-08-15), the following controls must be implemented and audited:

1. **Logical Access Control:** RBAC must be enforced (once unblocked) to ensure only authorized personnel access production data.
2. **Change Management:** All code must be reviewed by at least one other developer via GitLab Merge Requests.
3. **Data Encryption:** All PII (Personally Identifiable Information) must be encrypted using AES-256 at rest.
4. **Monitoring:** All administrative actions in the production environment must be logged to the `audit_logs` table with an immutable timestamp.
5. **Availability:** The Kubernetes cluster must be configured for multi-AZ (Availability Zone) deployment to ensure 99.9% uptime.