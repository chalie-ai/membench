# Project Specification Document: Project Glacier
**Document Version:** 1.0.4  
**Status:** Active/Draft  
**Last Updated:** 2024-05-12  
**Classification:** Confidential / HIPAA Protected  
**Project Lead:** Tomas Nakamura  

---

## 1. Executive Summary

### 1.1 Business Justification
Project Glacier is the strategic initiative by Hearthstone Software to rebuild its core healthcare records platform. While Hearthstone Software operates primarily within the real estate industry, the expansion into healthcare records management for real estate-integrated health facilities (such as assisted living, senior care homes, and corporate wellness campuses) has become a primary growth lever. 

The current legacy system has suffered catastrophic user feedback. Users have cited systemic latency, an intuitive failure in the UI/UX, and critical failures in data integrity. This "catastrophic" feedback has led to a 22% churn rate in the last fiscal quarter. Project Glacier is not merely an update but a comprehensive rebuild designed to recover market trust, ensure strict HIPAA compliance, and modernize the underlying infrastructure to support multi-tenant scaling.

The strategic pivot involves moving from a monolithic, slow-response architecture to a high-performance Rust-based backend leveraging Cloudflare Workers for edge computing. By doing so, Hearthstone Software aims to capture a larger share of the "Health-Real Estate" intersection market, where the demand for secure, fast, and portable patient records is paramount.

### 1.2 ROI Projection
The financial justification for Project Glacier is predicated on three primary levers: cost reduction, churn mitigation, and market expansion.

**Cost Reduction:** The legacy system relies on expensive, oversized virtual machines. By migrating to a serverless-edge architecture (Cloudflare Workers) and an optimized Rust backend, the projected cost per transaction is expected to drop by 35%. Based on current volumes of 1.2 million transactions per month, this represents an estimated annual saving of $145,000 in infrastructure overhead.

**Churn Mitigation:** Reducing the churn rate from 22% to a projected 5% through the elimination of the "catastrophic" bugs and UI failures is estimated to retain approximately $850,000 in Annual Recurring Revenue (ARR) that is currently at risk.

**Operational Efficiency:** A 50% reduction in manual processing time for end users will allow our clients to operate with fewer administrative staff, increasing the perceived value of the platform and allowing Hearthstone to move to a higher pricing tier.

**Total Projected 3-Year ROI:** 240%, with the break-even point expected within 14 months post-MVP launch.

---

## 2. Technical Architecture

### 2.1 System Overview
Project Glacier utilizes a traditional three-tier architecture—Presentation, Business Logic, and Data—but implements it using modern, high-performance technologies to solve the latency issues of the previous version.

- **Presentation Layer:** A React 18.x single-page application (SPA) utilizing TypeScript for type safety. The frontend is deployed via Cloudflare Pages for global distribution.
- **Business Logic Layer:** A backend written in Rust (using the Axum framework) deployed as a series of microservices on Kubernetes. This layer handles the heavy lifting, complex calculations, and HIPAA-compliant data processing.
- **Data Layer:** A hybrid approach using SQLite for edge caching/local state and a centralized PostgreSQL cluster for the primary source of truth.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ Client Browser/App ]  <-- HTTPS/TLS 1.3 --> [ Cloudflare Edge (Workers) ]
                                                            |
                                                            | (Request Routing)
                                                            v
                                             [ Kubernetes Cluster (GKE) ]
                                             +-------------------------+
                                             | [ Rust API Gateway ]     |
                                             +------------|------------+
                                                          |
             +--------------------------------------------+-------------------------------------------+
             |                                            |                                           |
 [ Business Logic: Auth ]                  [ Business Logic: Records ]                  [ Business Logic: Billing ]
 (Rust / Axum / JWT)                      (Rust / Axum / HIPAA-Enc)                    (Rust / Axum / No Tests!)
             |                                            |                                           |
             +--------------------------------------------+-------------------------------------------+
                                                          |
                                                          v
                                             [ Data Persistence Layer ]
                                             +-------------------------+
                                             |   [ Primary PostgreSQL ] | <--- Master Data (Encrypted)
                                             |   [ Edge SQLite Cache ]  | <--- Localized Fast Access
                                             +-------------------------+
```

### 2.3 Data Flow and Security
To maintain HIPAA compliance, the architecture implements "Encryption in Transit" (TLS 1.3) and "Encryption at Rest" (AES-256). The Rust backend acts as the primary security sentinel, ensuring that no unencrypted PII (Personally Identifiable Information) ever touches the persistent storage layer without being passed through the encryption module managed by Felix Jensen.

---

## 3. Detailed Feature Specifications

### 3.1 Multi-tenant Data Isolation (Priority: Critical)
**Status:** Not Started | **Launch Blocker: Yes**

The core requirement for Project Glacier is the ability to host multiple real estate health entities on a shared infrastructure while ensuring that Data Entity A can never, under any circumstances, access Data Entity B’s records. 

**Technical Implementation:**
We will implement "Row-Level Security" (RLS) at the database level. Every table in the database will contain a `tenant_id` column. The Rust backend will intercept every request, validate the tenant identity via a JWT (JSON Web Token), and inject the `tenant_id` into every SQL query. 

**Functional Requirements:**
1. **Tenant Provisioning:** A mechanism to create new tenant silos upon customer onboarding.
2. **Isolation Verification:** A set of automated tests that attempt to access data across tenant boundaries to ensure the system rejects the request.
3. **Shared Schema:** To maintain maintainability, we will use a shared schema rather than separate databases per tenant, relying on the RLS logic for isolation.
4. **Administrative Override:** A highly restricted "Super Admin" role for Hearthstone support (Hugo Park) to troubleshoot issues, requiring a double-signed token for access.

**Failure Mode:** If a request arrives without a valid `tenant_id`, the system must return a 403 Forbidden and log a security alert to the monitoring dashboard.

### 3.2 Customer-Facing API with Versioning and Sandbox (Priority: High)
**Status:** In Design

To allow real estate firms to integrate their own property management software with Glacier, we are building a robust RESTful API.

**Technical Implementation:**
The API will be versioned via the URL path (e.g., `/v1/records/`). We will implement a "Sandbox" environment which is a mirrored version of the production environment but populated with synthetic, non-PII data.

**Functional Requirements:**
1. **API Key Management:** Users can generate, rotate, and revoke API keys within their dashboard.
2. **Rate Limiting:** Implemented via Cloudflare Workers to prevent DDoS and ensure fair usage (100 requests/second per tenant).
3. **Versioning Strategy:** We will support two concurrent versions (Current and Legacy). When `v2` is released, `v1` will be deprecated and supported for exactly 6 months.
4. **Sandbox Mirroring:** A dedicated staging database that allows developers to test "Create, Read, Update, Delete" (CRUD) operations without impacting real patient records.

**Documentation:** The API will be documented using OpenAPI 3.0 (Swagger), providing interactive examples for all endpoints.

### 3.3 Data Import/Export with Format Auto-Detection (Priority: Medium)
**Status:** In Review

Migrating from the legacy system and other competitors requires a flexible ingestion engine.

**Technical Implementation:**
A Rust-based parsing engine that utilizes a "Strategy Pattern" to detect file formats. The system will sample the first 1KB of an uploaded file to determine if it is CSV, JSON, HL7, or XML.

**Functional Requirements:**
1. **Auto-Detection:** The system must identify the file type without user input.
2. **Mapping Tool:** A UI-based mapper allowing users to link their source columns (e.g., "Patient_Name") to Glacier fields (e.g., "full_name").
3. **Validation Pipeline:** Before importing, data is placed in a "Pending" state where a validation script checks for missing required fields or data type mismatches.
4. **Export Flexibility:** Users can export their entire tenant dataset into a zipped archive of encrypted JSON files for compliance backups.

**Error Handling:** If a row fails validation, the system will provide a detailed error report (Row X: Column Y is invalid) rather than failing the entire upload.

### 3.4 Workflow Automation Engine with Visual Rule Builder (Priority: Low)
**Status:** Not Started | **Nice to Have**

This feature aims to reduce manual processing time by automating repetitive tasks (e.g., "If patient age > 80, trigger weekly wellness check notification").

**Technical Implementation:**
A JSON-based rule engine where the "Visual Rule Builder" in React generates a logic tree. This tree is stored in the database and evaluated by a background worker in the Rust backend.

**Functional Requirements:**
1. **Trigger Events:** Ability to trigger rules based on data changes (e.g., a record update).
2. **Action Library:** Pre-defined actions such as "Send Email," "Create Task," or "Update Status."
3. **Visual Interface:** A drag-and-drop canvas where users can connect "Triggers" to "Actions" via logical connectors (AND/OR).
4. **Execution Logs:** A detailed log showing when a rule was triggered and whether the action succeeded.

**Constraint:** To prevent infinite loops, the engine will limit recursive triggers to a depth of 3.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support (Priority: Low)
**Status:** In Design | **Nice to Have**

Given the sensitive nature of healthcare records, standard passwords are insufficient.

**Technical Implementation:**
Integration of WebAuthn for hardware keys (YubiKey, Google Titan) and TOTP (Time-based One-Time Password) for apps like Google Authenticator.

**Functional Requirements:**
1. **Hardware Key Enrollment:** A secure flow for users to register their FIDO2/WebAuthn devices.
2. **Fallback Methods:** Ability to generate 10 one-time recovery codes if the hardware key is lost.
3. **Step-up Authentication:** The system can require 2FA again when a user attempts to perform a "High Risk" action, such as exporting the entire database.
4. **Admin Enforcement:** Tenant admins can mandate that all users within their organization must enable 2FA to log in.

**Security Note:** All 2FA secrets must be stored using an industry-standard encryption library, never in plaintext.

---

## 4. API Endpoint Documentation

All endpoints require a `X-API-KEY` in the header and use JSON for request/response bodies. Base URL: `https://api.glacier.hearthstone.com/v1`

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns a JWT.
- **Request:** `{"email": "user@example.com", "password": "securepassword"}`
- **Response:** `200 OK` -> `{"token": "eyJhbG...", "expires_at": "2025-06-15T12:00:00Z"}`

### 4.2 `GET /records/patient/{id}`
- **Description:** Retrieves a specific patient record.
- **Request:** Path parameter `{id}`.
- **Response:** `200 OK` -> `{"id": "pat_123", "name": "John Doe", "dob": "1950-01-01", "records": [...]}`

### 4.3 `POST /records/patient`
- **Description:** Creates a new patient record.
- **Request:** `{"name": "Jane Smith", "dob": "1962-05-12", "tenant_id": "tenant_88"}`
- **Response:** `201 Created` -> `{"id": "pat_124", "status": "created"}`

### 4.4 `PUT /records/patient/{id}`
- **Description:** Updates existing patient data.
- **Request:** `{"address": "123 Maple St", "phone": "555-0199"}`
- **Response:** `200 OK` -> `{"id": "pat_123", "updated_at": "2025-06-15T10:00:00Z"}`

### 4.5 `DELETE /records/patient/{id}`
- **Description:** Soft-deletes a patient record (HIPAA compliance requires archival).
- **Request:** Path parameter `{id}`.
- **Response:** `204 No Content`.

### 4.6 `GET /tenants/config`
- **Description:** Fetches the specific configuration for the authenticated tenant.
- **Request:** None.
- **Response:** `200 OK` -> `{"tenant_id": "tenant_88", "plan": "Enterprise", "max_users": 50}`

### 4.7 `POST /import/detect`
- **Description:** Uploads a file snippet to detect its format.
- **Request:** Multipart form-data (file stream).
- **Response:** `200 OK` -> `{"detected_format": "HL7", "confidence": 0.98}`

### 4.8 `GET /billing/usage`
- **Description:** Returns current month's transaction usage.
- **Request:** None.
- **Response:** `200 OK` -> `{"current_month": "June", "transactions": 14500, "cost": 217.50}`

---

## 5. Database Schema

The system uses a PostgreSQL primary database. All tables utilize UUIDs as primary keys.

| Table Name | Description | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `tenants` | Top-level organization data | `tenant_id (PK)`, `company_name`, `created_at`, `plan_level` | 1:N with `users` |
| `users` | User account details | `user_id (PK)`, `tenant_id (FK)`, `email`, `password_hash`, `mfa_enabled` | N:1 with `tenants` |
| `patients` | Core patient demographic info | `patient_id (PK)`, `tenant_id (FK)`, `full_name`, `dob`, `ssn_encrypted` | N:1 with `tenants` |
| `medical_records` | Clinical notes and data | `record_id (PK)`, `patient_id (FK)`, `clinical_text_encrypted`, `created_by (FK)` | N:1 with `patients` |
| `audit_logs` | Tracking all PII access | `log_id (PK)`, `user_id (FK)`, `patient_id (FK)`, `action`, `timestamp` | N:1 with `users` |
| `api_keys` | Management of external access | `key_id (PK)`, `tenant_id (FK)`, `key_hash`, `last_used_at` | N:1 with `tenants` |
| `billing_accounts` | Financial tracking | `account_id (PK)`, `tenant_id (FK)`, `stripe_customer_id`, `balance` | 1:1 with `tenants` |
| `billing_transactions`| Individual charge events | `txn_id (PK)`, `account_id (FK)`, `amount`, `txn_date`, `status` | N:1 with `billing_accounts` |
| `workflow_rules` | Automation logic | `rule_id (PK)`, `tenant_id (FK)`, `trigger_event`, `action_json` | N:1 with `tenants` |
| `workflow_logs` | Execution history of rules | `exec_id (PK)`, `rule_id (FK)`, `status`, `error_message` | N:1 with `workflow_rules` |

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Project Glacier utilizes three distinct environments to ensure stability and security.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** Small Kubernetes namespace, mock data.
- **Deployment:** Automatic deployment on every merge to the `develop` branch.
- **Access:** Restricted to the team of 6.

**2. Staging (Staging):**
- **Purpose:** QA testing and stakeholder demos.
- **Infrastructure:** Mirrored production environment (same CPU/RAM specs) but with a sanitized dataset.
- **Deployment:** Triggered by a merge to the `release` branch.
- **Access:** Team of 6, QA Lead, and key stakeholders.

**3. Production (Prod):**
- **Purpose:** Live customer traffic.
- **Infrastructure:** High-availability Kubernetes cluster across three availability zones.
- **Deployment:** Rolling deployments via GitLab CI. Each deployment is gated by a manual sign-off from Tomas Nakamura.
- **Access:** Highly restricted; only automated CI/CD service accounts and the Project Lead have write access.

### 6.2 CI/CD Pipeline
The GitLab CI pipeline consists of four stages:
1. **Build:** Compile Rust binaries and build React assets.
2. **Test:** Run unit and integration tests. If coverage drops below 80% (except for the billing module), the build fails.
3. **Deploy to Staging:** Update Kubernetes manifests and restart pods.
4. **Promote to Prod:** A manual trigger that executes a rolling update to ensure zero downtime.

---

## 7. Testing Strategy

Due to the "catastrophic" nature of the legacy failure, the testing strategy for Glacier is aggressive and multi-layered.

### 7.1 Unit Testing
- **Backend:** Every Rust function must have corresponding unit tests. We use the `cargo test` framework.
- **Frontend:** Jest and React Testing Library for component-level validation.
- **Target:** 90% coverage on all new business logic.

### 7.2 Integration Testing
- **API Testing:** Automated Postman collections that run against the Staging environment to verify endpoint contracts.
- **Database Isolation Tests:** A specialized suite of tests that specifically attempt to perform "cross-tenant" queries to verify that RLS is working.
- **End-to-End (E2E):** Playwright scripts that simulate a user logging in, creating a patient record, and exporting it.

### 7.3 Special Case: The Billing Module
**Current Debt:** The core billing module was deployed without tests under deadline pressure.
**Remediation Plan:** 
- A "Freeze Period" is scheduled for July 2025 where no new billing features will be added.
- Viktor Moreau is tasked with writing a full regression suite for the billing module.
- No billing updates will be pushed to Production until the test coverage reaches 100% for the `billing_transactions` logic.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding 'small' features. | High | Medium | Accept the risk; monitor weekly in sync calls and log "out-of-scope" items in a separate backlog. |
| R-02 | Primary vendor dependency announced End-of-Life (EOL). | Medium | Critical | **Blocker:** Raise in next board meeting. Evaluate alternative vendors (e.g., migrating from the legacy vendor to a native AWS/GCP solution). |
| R-03 | Data Processing Agreement (DPA) legal delay. | High | High | **Current Blocker:** Follow up with legal daily. Project cannot move to "Prod" without this signature. |
| R-04 | Performance degradation as tenant count grows. | Low | Medium | Implement horizontal pod autoscaling in Kubernetes and aggressive caching in SQLite. |
| R-05 | Security breach of PII data. | Low | Catastrophic | Regular third-party HIPAA audits and strict adherence to Felix Jensen's security protocols. |

---

## 9. Timeline and Milestones

The project follows a phased approach with hard deadlines for stakeholder sign-off.

### 9.1 Gantt-Style Phase Description

**Phase 1: Foundation (Current - 2025-06-15)**
- Setup Kubernetes infrastructure.
- Implement Multi-tenant Isolation (Critical).
- Core API Design.
- **Dependency:** Legal sign-off on DPA.
- **Milestone 1:** Stakeholder demo and sign-off (Target: 2025-06-15).

**Phase 2: Onboarding & Stability (2025-06-16 - 2025-08-15)**
- Finalize Data Import/Export tools.
- Onboard first beta customer.
- Fix Billing Module technical debt.
- **Dependency:** Milestone 1 sign-off.
- **Milestone 2:** First paying customer onboarded (Target: 2025-08-15).

**Phase 3: Feature Completion & Scaling (2025-08-16 - 2025-10-15)**
- Implement 2FA and Hardware Key support.
- Finalize the Workflow Automation Engine.
- Load testing for 10,000+ concurrent users.
- **Dependency:** Milestone 2 success.
- **Milestone 3:** MVP feature-complete (Target: 2025-10-15).

---

## 10. Meeting Notes

### Meeting 1: Architecture Review
**Date:** 2024-05-01  
**Attendees:** Tomas Nakamura, Viktor Moreau, Felix Jensen  
**Discussion:**
- Viktor proposed moving from PostgreSQL-only to a hybrid PostgreSQL/SQLite model to reduce latency. 
- Felix expressed concerns about data synchronization between the edge and the core.
- Decision: Use SQLite for read-heavy "session" data and PostgreSQL for the source of truth.

**Action Items:**
- [Viktor] Create a prototype for the edge-sync mechanism. (Due: 2024-05-08)
- [Felix] Draft the encryption spec for the data-at-rest layer. (Due: 2024-05-08)

---

### Meeting 2: Scope and Stakeholder Pressure
**Date:** 2024-05-15  
**Attendees:** Tomas Nakamura, Hugo Park  
**Discussion:**
- Hugo reported that stakeholders are requesting a "Dark Mode" and "Custom Themes" for the dashboard, claiming they are "small" features.
- Tomas noted that this is classic scope creep.
- Decision: We will acknowledge these requests but will not allocate any engineering hours until Milestone 3 is achieved.

**Action Items:**
- [Tomas] Create a "Future Enhancements" list to appease stakeholders without committing resources. (Due: 2024-05-17)

---

### Meeting 3: Emergency Blocker Sync
**Date:** 2024-05-22  
**Attendees:** All Team Members  
**Discussion:**
- The team discussed the EOL announcement from the primary vendor. This is now a critical risk.
- The current blocker is the Legal Review of the DPA; without it, we cannot move to a production-ready cloud environment.
- Decision: Tomas will escalate the vendor EOL and the DPA delay to the board.

**Action Items:**
- [Tomas] Prepare the slide deck for the board meeting regarding the vendor blocker. (Due: 2024-05-25)
- [Hugo] Draft a temporary manual workaround for data ingestion to keep beta users happy. (Due: 2024-05-30)

---

## 11. Budget Breakdown

The budget for Project Glacier is variable, released in tranches upon the successful completion of each milestone.

| Category | Allocation (USD) | Note |
| :--- | :--- | :--- |
| **Personnel** | $720,000 | 6 members (Avg $120k/yr) for the project duration. |
| **Infrastructure** | $45,000 | GKE Cluster, Cloudflare Workers, Managed PostgreSQL. |
| **Tools & Licenses** | $12,000 | GitLab Premium, Snyk Security, Datadog monitoring. |
| **Contingency** | $60,000 | Reserved for emergency vendor migration due to EOL risk. |
| **Total Projected** | **$837,000** | |

**Tranche Release Schedule:**
- Tranche 1 (30%): Released upon project kickoff.
- Tranche 2 (30%): Released upon Milestone 1 (2025-06-15).
- Tranche 3 (40%): Released upon Milestone 2 (2025-08-15).

---

## 12. Appendices

### Appendix A: HIPAA Compliance Checklist
To ensure the "Healthcare Records" aspect of the platform is legal, the following must be verified before Milestone 3:
1. **Access Control:** Unique user IDs and automatic session timeouts.
2. **Audit Controls:** Every read/write to the `medical_records` table must be logged in `audit_logs`.
3. **Integrity:** Implementation of checksums to ensure data has not been altered by unauthorized parties.
4. **Transmission Security:** Forcing TLS 1.3 for all external traffic.

### Appendix B: Rust-to-SQLite Edge Mapping
For the performance boost, the following data is cached at the edge via Cloudflare Workers:
- **Patient Basic Info:** Name, DOB, and Tenant ID.
- **User Session:** JWT and role permissions.
- **Configuration:** Tenant-specific UI settings.

Any update to these fields in the PostgreSQL master must trigger a "Purge" request to the Cloudflare Worker to ensure the edge cache is refreshed, preventing "stale data" bugs.