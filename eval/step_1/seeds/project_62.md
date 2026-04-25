# Project Specification: Bastion Healthcare Records Platform
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2025  
**Company:** Pivot North Engineering  
**Project Lead:** Cassius Oduya  

---

## 1. Executive Summary

### 1.1 Project Overview
Project "Bastion" is a specialized healthcare records platform designed to operate within the education industry. Originally conceived as a rapid-prototype hackathon project, Bastion has evolved into a critical internal productivity tool that currently supports 500 daily active users (DAU). The primary objective is to transition this "accidental" success into a production-grade, scalable, and secure platform capable of supporting institutional healthcare data management within educational environments (e.g., university health centers, K-12 school nurse registries).

### 1.2 Business Justification
The education sector currently lacks a streamlined, integrated healthcare record system that balances the strict privacy requirements of HIPAA/GDPR with the operational needs of academic administration. Bastion fills this gap by providing a centralized repository for student health records, immunization tracking, and emergency contact management. 

The transition from a hackathon project to a formal product is driven by the organic growth of the user base. With 500 users already relying on the tool for daily productivity, the demand for a formalized, commercially viable version is evident. By professionalizing the codebase and adding critical security layers, Pivot North Engineering can pivot from an internal tool to a B2B SaaS model.

### 1.3 ROI Projection and Financial Constraints
The project is operating on a "shoestring" budget of **$150,000**. Every dollar is under intense scrutiny, necessitating a lean approach to development. The Return on Investment (ROI) is projected based on the transition to a subscription model for educational institutions.

**Financial Projections (Year 1 post-launch):**
- **Target Customer Base:** 20 Mid-to-Large Scale Educational Institutions.
- **Average Contract Value (ACV):** $15,000/year.
- **Projected Annual Recurring Revenue (ARR):** $300,000.
- **Break-even Point:** Approximately 6 months post-launch.
- **Projected ROI:** 100% return on the initial $150,000 investment within the first 12 months, excluding ongoing operational costs.

The lean budget requires the team to leverage a simple, monolith architecture to minimize infrastructure overhead and avoid the "complexity tax" associated with microservices.

---

## 2. Technical Architecture

### 2.1 Architectural Philosophy
Bastion utilizes a **Clean Monolith** architecture. The goal is to maintain a single deployable unit to reduce operational complexity while enforcing strict module boundaries within the Ruby on Rails application. This prevents the "big ball of mud" syndrome and allows for easier extraction of services in the future if the scale warrants it.

**Stack Details:**
- **Language/Framework:** Ruby on Rails 7.1 (API and Web mode)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons)
- **Hosting:** Heroku (PaaS)
- **Caching:** Redis (via Heroku Data for Redis)
- **Security Standard:** ISO 27001 Certified Environment

### 2.2 System Diagram (ASCII Description)
The following represents the request-response flow and data isolation layers.

```text
[ User / Client ]  ---> [ Heroku Load Balancer / Router ]
                                 |
                                 v
                    +---------------------------+
                    |   Rails Monolith (App)     |
                    |  +---------------------+   |
                    |  |  Auth Module (2FA)  |   | <--- [Hardware Keys/WebAuthn]
                    |  +---------------------+   |
                    |  |  Records Module      |   | <--- [Healthcare Logic]
                    |  +---------------------+   |
                    |  |  API / Sandbox Layer |   | <--- [External Integrations]
                    |  +---------------------+   |
                    |  |  Sync / Offline Mod  |   | <--- [Background Workers]
                    |  +---------------------+   |
                    +---------------------------+
                                 |
                +----------------+----------------+
                |                                  |
                v                                  v
      [ MySQL Database ]                   [ Redis Cache/Queue ]
      - Patient Records                    - Session Store
      - Audit Logs                        - Sidekiq Jobs
      - User Permissions                   - Rate Limit Counters
```

### 2.3 Infrastructure Logic
To maintain simplicity and adhere to the budget, the team avoids Kubernetes or complex AWS orchestrations. Heroku provides the necessary abstraction. The "Bus Factor of 1" regarding deployment is managed by Thiago Santos, who handles all manual pipeline triggers. While this is a risk, it ensures a single point of accountability for the ISO 27001 compliance checks during deployment.

---

## 3. Detailed Feature Specifications

### 3.1 Customer-Facing API with Versioning and Sandbox (Priority: High | Status: Blocked)
The Bastion API is designed to allow educational institutions to integrate their own student information systems (SIS) with the healthcare records platform. 

**Functional Requirements:**
- **Versioning:** The API must use URI versioning (e.g., `/api/v1/`). All breaking changes must trigger a version increment.
- **Sandbox Environment:** A mirrored environment where developers can test requests against mock data without affecting production records.
- **Authentication:** API Key-based authentication via `X-API-KEY` headers, tied to the organization's account.
- **Data Format:** All requests and responses must be in JSON format.

**Technical Implementation:**
The API will be implemented using a dedicated `Api::V1` namespace in Rails. A separate `sandbox` database will be maintained on Heroku, utilizing a different set of environment variables to ensure complete isolation. 

**Blocking Issue:** This feature is currently blocked awaiting the legal review of the Data Processing Agreement (DPA), as the API exposes sensitive healthcare data to third-party systems.

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support (Priority: Critical | Status: Blocked)
Due to the sensitivity of healthcare records and the ISO 27001 requirement, 2FA is a non-negotiable launch blocker.

**Functional Requirements:**
- **Multi-Modal Auth:** Support for Time-based One-Time Passwords (TOTP) via apps like Google Authenticator and hardware keys (FIDO2/WebAuthn).
- **Enrollment Flow:** Users must be forced to enroll in 2FA upon their first login after the feature launch.
- **Recovery Codes:** Generation of ten one-time-use recovery codes upon successful setup.
- **Hardware Support:** Integration with Yubikeys and Apple/Google biometric keys via the WebAuthn API.

**Technical Implementation:**
The platform will utilize the `devise-two-factor` gem for TOTP and a custom implementation of the `webauthn` ruby gem for hardware keys. The database will store the public key and sign-count for each hardware device registered.

**Blocking Issue:** Blocked by the same legal DPA review, as the identity verification process must comply with institutional privacy laws.

### 3.3 API Rate Limiting and Usage Analytics (Priority: Low | Status: Complete)
This feature ensures the stability of the platform by preventing any single API consumer from overwhelming the MySQL database.

**Functional Requirements:**
- **Tiers:** Three tiers of rate limits: Basic (100 req/min), Pro (1,000 req/min), and Enterprise (Custom).
- **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics:** A dashboard for administrators to see the top 10 most active API keys and the most frequent error endpoints.

**Technical Implementation:**
Implemented using the `rack-attack` gem. Rate limits are tracked in Redis for sub-millisecond latency. Analytics are aggregated via a daily Sidekiq cron job that summarizes request logs into the `api_usage_stats` table.

### 3.4 Offline-First Mode with Background Sync (Priority: High | Status: In Design)
Healthcare workers in schools often move between areas with poor Wi-Fi (e.g., gymnasiums, sports fields).

**Functional Requirements:**
- **Local Storage:** Use of IndexedDB to store a local copy of the current patient's record.
- **Queueing:** All writes performed offline must be queued in a "Pending Sync" local table.
- **Conflict Resolution:** "Last Write Wins" strategy for general fields, but a "Manual Review" flag for critical medical data (e.g., allergy updates).
- **Background Sync:** Automatic triggering of sync when the `navigator.onLine` event fires.

**Technical Implementation:**
The front-end will move toward a Progressive Web App (PWA) model. A Service Worker will intercept network requests. For the backend, a `sync_log` table will track the version of the record sent by the client to ensure no data is overwritten by an older offline session.

### 3.5 Data Import/Export with Format Auto-Detection (Priority: Low | Status: In Review)
Institutions often migrate from legacy CSVs or proprietary XML formats.

**Functional Requirements:**
- **Auto-Detection:** The system must analyze the first 10 rows of an uploaded file to guess the format (CSV, JSON, XML).
- **Mapping Tool:** A UI allowing users to map their CSV columns to Bastion's internal fields (e.g., "Student_Name" $\rightarrow$ "full_name").
- **Export:** Support for exporting full patient histories in PDF (for legal) and JSON (for portability).

**Technical Implementation:**
Utilizing the `SmarterCSV` gem for parsing. The auto-detection logic uses a series of regular expression checks on the file header. Exporting to PDF is handled via `WickedPDF` to ensure consistent formatting.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1/`.

### 4.1 `GET /patients`
**Description:** Retrieves a paginated list of patients.
- **Request Parameters:** `page` (int), `per_page` (int), `query` (string).
- **Response (200 OK):**
```json
{
  "patients": [
    { "id": "uuid-123", "full_name": "John Doe", "dob": "2010-05-12" }
  ],
  "meta": { "total_pages": 5, "current_page": 1 }
}
```

### 4.2 `POST /patients`
**Description:** Creates a new patient record.
- **Request Body:** `{ "full_name": "Jane Smith", "dob": "2011-08-20", "institution_id": "inst-99" }`
- **Response (201 Created):**
```json
{ "id": "uuid-456", "status": "created" }
```

### 4.3 `GET /patients/:id`
**Description:** Retrieves full details for a specific patient.
- **Response (200 OK):**
```json
{
  "id": "uuid-123",
  "medical_history": [...],
  "immunizations": [...]
}
```

### 4.4 `PATCH /patients/:id`
**Description:** Updates patient information.
- **Request Body:** `{ "address": "123 Maple St" }`
- **Response (200 OK):**
```json
{ "id": "uuid-123", "updated_at": "2025-10-24T10:00:00Z" }
```

### 4.5 `GET /immunizations`
**Description:** Returns all immunization records for the authenticated institution.
- **Response (200 OK):**
```json
{ "records": [ { "patient_id": "uuid-123", "vaccine": "MMR", "date": "2020-01-01" } ] }
```

### 4.6 `POST /immunizations`
**Description:** Adds a new immunization entry.
- **Request Body:** `{ "patient_id": "uuid-123", "vaccine": "Varicella", "date": "2021-06-15" }`
- **Response (201 Created):**
```json
{ "id": "imm-789", "status": "recorded" }
```

### 4.7 `GET /sandbox/status`
**Description:** Checks if the current environment is the sandbox or production.
- **Response (200 OK):**
```json
{ "environment": "sandbox", "version": "1.0.4-beta" }
```

### 4.8 `DELETE /patients/:id`
**Description:** Soft-deletes a patient record.
- **Response (204 No Content):** (Empty body)

---

## 5. Database Schema

The system utilizes a MySQL relational database. All tables use UUIDs as primary keys to ensure data portability.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `institutions` | `id` | None | `name`, `subscription_tier`, `dpa_signed` | The school or district. |
| `users` | `id` | `institution_id` | `email`, `password_digest`, `role` | Staff members. |
| `two_factor_keys` | `id` | `user_id` | `otp_secret`, `webauthn_pubkey` | 2FA secrets. |
| `patients` | `id` | `institution_id` | `full_name`, `dob`, `student_id` | The student/patient. |
| `medical_records`| `id` | `patient_id`, `user_id` | `diagnosis`, `treatment`, `notes` | Clinical entries. |
| `immunizations` | `id` | `patient_id` | `vaccine_type`, `dose_date`, `lot_number` | Vaccination history. |
| `api_keys` | `id` | `institution_id` | `key_hash`, `last_used_at`, `scopes` | API access tokens. |
| `api_usage_stats` | `id` | `api_key_id` | `request_count`, `timestamp`, `endpoint` | Rate limit tracking. |
| `sync_logs` | `id` | `patient_id`, `user_id` | `client_version`, `sync_status` | Offline sync tracking. |
| `audit_logs` | `id` | `user_id`, `patient_id` | `action`, `ip_address`, `timestamp` | ISO 27001 requirement. |

### 5.2 Relationships
- `Institution` $\rightarrow$ `Users` (One-to-Many)
- `Institution` $\rightarrow$ `Patients` (One-to-Many)
- `User` $\rightarrow$ `TwoFactorKeys` (One-to-One)
- `Patient` $\rightarrow$ `MedicalRecords` (One-to-Many)
- `Patient` $\rightarrow$ `Immunizations` (One-to-Many)
- `Institution` $\rightarrow$ `ApiKeys` (One-to-Many)

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Bastion utilizes three distinct Heroku environments to isolate development and production data.

#### 6.1.1 Development (`bastion-dev`)
- **Purpose:** Daily coding and experimentation.
- **Data:** Seeded with mock data; wiped weekly.
- **Access:** All developers.
- **Deployment:** Automated via GitHub integration on the `dev` branch.

#### 6.1.2 Staging (`bastion-staging`)
- **Purpose:** QA, UAT, and Legal/Compliance review.
- **Data:** Anonymized production snapshots.
- **Access:** Developers and Project Lead.
- **Deployment:** Manual trigger from `main` branch.

#### 6.1.3 Production (`bastion-prod`)
- **Purpose:** End-user operations.
- **Data:** Real healthcare records.
- **Access:** Strictly limited to Cassius Oduya and Thiago Santos.
- **Deployment:** Manual deployment performed by Thiago Santos. This manual step is mandatory to ensure that a final checksum of the ISO 27001 compliance checklist is verified.

### 6.2 Infrastructure Components
- **Load Balancer:** Heroku Router.
- **Web Dynos:** 2x Standard-2X (for production).
- **Worker Dynos:** 1x Standard-1X (for Sidekiq background jobs).
- **Database:** Heroku MySQL (Standard Tier) with automated daily backups.
- **SSL/TLS:** Managed by Heroku (TLS 1.3 required for all healthcare data in transit).

---

## 7. Testing Strategy

To ensure stability with a distributed team of 15, a multi-layered testing approach is implemented.

### 7.1 Unit Testing (RSpec)
Every new feature must have corresponding unit tests.
- **Coverage Target:** 80% line coverage.
- **Focus:** Model validations, helper methods, and isolated business logic in services.
- **Execution:** Run on every push via GitHub Actions.

### 7.2 Integration Testing (Request Specs)
Integration tests ensure that the API and Web controllers interact correctly with the database.
- **Focus:** End-to-end request flow (e.g., `POST /patients` $\rightarrow$ `GET /patients/:id`).
- **Database:** Use of `DatabaseCleaner` to ensure a pristine state between tests.

### 7.3 End-to-End (E2E) Testing (Playwright)
E2E tests simulate the user's journey in the browser.
- **Critical Paths:**
    - User login $\rightarrow$ 2FA prompt $\rightarrow$ Dashboard access.
    - Patient search $\rightarrow$ Record update $\rightarrow$ Sync verification.
    - CSV Import $\rightarrow$ Mapping $\rightarrow$ Data verification.
- **Frequency:** Run on the `main` branch before deployment to Staging.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Key architect leaving in 3 months | High | High | Accept risk. Monitor weekly during 1:1s; prioritize documentation of core logic. |
| R2 | Team lacks experience with Rails/MySQL | High | Medium | Engage external consultant for a monthly independent architectural assessment. |
| R3 | Legal DPA review delay | Medium | High | Maintain "Blocked" status on API/2FA; focus on "In Design" features (Offline Mode). |
| R4 | Bus factor of 1 (Deployment) | High | Medium | Thiago Santos to create a "Deployment Runbook" to be stored in the internal Wiki. |
| R5 | Budget overrun ($150k limit) | Low | High | Monthly budget audits by Cassius Oduya; no new third-party paid tools without approval. |

**Probability/Impact Matrix:**
- **Critical:** R1, R3
- **Moderate:** R2, R4
- **Low:** R5

---

## 9. Timeline

The project follows a phased approach with dependencies on legal approval.

### 9.1 Phase 1: Foundation & Hardening (Now $\rightarrow$ 2026-06-15)
- **Focus:** Code cleanup, ISO 27001 environment prep, and documentation.
- **Dependency:** External consultant assessment.
- **Milestone 1:** Architecture Review Complete (Target: 2026-06-15).

### 9.2 Phase 2: Core Feature Implementation (2026-06-16 $\rightarrow$ 2026-08-15)
- **Focus:** Unblocking 2FA and API once DPA is signed. Implementing Offline-First mode.
- **Dependency:** Legal sign-off on Data Processing Agreement.
- **Milestone 2:** Internal Alpha Release (Target: 2026-08-15).

### 9.3 Phase 3: Beta & Market Entry (2026-08-16 $\rightarrow$ 2026-10-15)
- **Focus:** Pilot user onboarding, bug fixing, and refining the Import/Export tool.
- **Dependency:** Stable Alpha build.
- **Milestone 3:** First Paying Customer Onboarded (Target: 2026-10-15).

---

## 10. Meeting Notes

### Meeting 1: Sprint Planning - Oct 20, 2025
- **Attendees:** Cassius, Thiago, Alejandro, Sol.
- **Notes:**
    - 2FA still blocked by legal.
    - Alejandro wants to review the ISO 27001 checklist for the prod env.
    - Sol suggesting a different gem for the offline sync.
    - Budget check: $12k spent on Heroku addons this month.

### Meeting 2: Tech Debt Sync - Oct 27, 2025
- **Attendees:** Cassius, Thiago, Sol.
- **Notes:**
    - `Patient` model is getting too large.
    - Decided to move immunization logic to a service object.
    - Technical debt is manageable; 10% of sprint capacity allocated to refactoring.
    - Thiago warns about the manual deploy process taking too long.

### Meeting 3: Risk Assessment - Nov 3, 2025
- **Attendees:** Cassius, Alejandro.
- **Notes:**
    - Architect's exit date confirmed.
    - No immediate panic; will monitor weekly.
    - Consultant's report is due next Friday.
    - Legal still hasn't responded to the DPA email. Cassius to escalate.

---

## 11. Budget Breakdown

Total Budget: **$150,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Salaries for distributed team (partial) and Sol (Contractor). |
| **Infrastructure** | 20% | $30,000 | Heroku dynos, MySQL, Redis, and Backup storage. |
| **Tools & Compliance** | 10% | $15,000 | ISO 27001 auditing tools, WebAuthn certification, External Consultant. |
| **Contingency** | 10% | $15,000 | Reserve for emergency scaling or legal fees. |

---

## 12. Appendices

### Appendix A: ISO 27001 Compliance Checklist
To maintain certification in the production environment, the following must be verified by Alejandro Santos during every deployment:
1. **Encryption at Rest:** All MySQL volumes must be encrypted using AES-256.
2. **Encryption in Transit:** No HTTP traffic permitted; HSTS enabled.
3. **Access Control:** RBAC (Role-Based Access Control) verified for all administrative users.
4. **Audit Trail:** All `DELETE` and `PATCH` operations on patient records must be logged in the `audit_logs` table with a timestamp and User ID.
5. **Vulnerability Scanning:** Monthly Dependabot and Snyk scans must show zero "Critical" vulnerabilities.

### Appendix B: Offline Sync Conflict Logic
When a client attempts to sync data that has been modified on the server since the client's last sync, the following logic is applied:

1. **Field-Level Comparison:**
   - If `Server_Value == Client_Value`, ignore.
   - If `Server_Value != Client_Value` and field is "Non-Critical" (e.g., Address), **Last Write Wins**.
2. **Critical Field Handling:**
   - If field is "Critical" (e.g., Allergy, Medication), the server rejects the update.
   - The server returns a `409 Conflict` response with the current server state.
   - The UI prompts the healthcare worker to "Keep Local," "Keep Server," or "Merge Manually."
3. **Version Tracking:**
   - Each record has a `lock_version` integer.
   - Clients must send the `lock_version` they are updating. If the server version is higher, a conflict is triggered.