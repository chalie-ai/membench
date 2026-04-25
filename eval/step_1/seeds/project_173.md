# PROJECT SPECIFICATION: PROJECT ARCHWAY
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Project Code:** ARCH-2025-BW  
**Company:** Bellweather Technologies  
**Classification:** Confidential / ISO 27001 Compliant  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Archway is a strategic infrastructure modernization initiative undertaken by Bellweather Technologies. The primary objective is the consolidation of four redundant internal telecommunications management tools—currently operating as disparate silos with overlapping functionality—into a single, unified API gateway and a modular microservices architecture. This migration aims to eliminate technical redundancy, reduce operational overhead, and streamline the internal developer experience across the organization.

### 1.2 Business Justification
Currently, Bellweather Technologies maintains four legacy systems: *TelcoCore*, *NetSight*, *SignalFlow*, and *ProvisionX*. Each of these tools handles aspects of network provisioning, customer data management, and signal analytics. However, the duplication of these services has led to "data drift," where a customer's record in *TelcoCore* may differ from their record in *ProvisionX*. This fragmentation creates significant operational friction, increases the risk of regulatory non-compliance, and inflates licensing and maintenance costs.

By migrating these functions into Project Archway, the company will achieve a "Single Source of Truth" (SSoT) for all internal telecommunications tooling. This consolidation will reduce the surface area for security vulnerabilities and allow the engineering team to focus on feature parity and enhancement rather than maintaining four separate legacy codebases.

### 1.3 ROI Projection
The total budget for Project Archway is $1.5M. The projected Return on Investment (ROI) is calculated based on the following cost-reduction vectors over a 24-month period:

1.  **Infrastructure Cost Reduction:** Consolidating four Heroku instances into a single, optimized modular monolith/microservice hybrid is expected to save approximately $120,000 per annum in hosting and add-on costs.
2.  **Labor Efficiency:** Estimated reduction of 1,500 engineering hours per year previously spent on cross-tool data synchronization and bug fixing across redundant systems. At an average loaded cost of $120/hour, this equals $180,000 in reclaimed productivity.
3.  **Regulatory Risk Mitigation:** By ensuring ISO 27001 compliance across a single gateway rather than four disparate tools, the company avoids potential non-compliance fines which, in the telecommunications sector, can reach six figures per incident.

**Projected Total Savings (24 Months):** ~$600,000 in direct costs, with an additional $300,000 in indirect productivity gains. The project is expected to reach a break-even point within 18 months of the Production Launch (2025-08-15).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Archway adopts a "Modular Monolith to Microservices" migration pattern (the Strangler Fig Pattern). To minimize risk and leverage the team's current comfort level, the system will be built using **Ruby on Rails (v7.1)**, **MySQL (v8.0)**, and hosted on **Heroku**. 

The architecture begins as a modular monolith—where boundaries are strictly enforced within a single codebase—and will incrementally offload high-load functions into standalone microservices as the system scales.

### 2.2 System Components
- **API Gateway:** The entry point for all internal requests. It handles rate limiting, authentication (SAML/OIDC), and request routing.
- **Modular Core:** The main Rails application containing the business logic for the four consolidated tools.
- **Data Persistence Layer:** A centralized MySQL database utilizing partitioned tables to separate legacy data from new consolidated data.
- **Worker Tier:** Sidekiq for asynchronous processing of PDF/CSV reports and data imports.

### 2.3 ASCII Architecture Diagram
```text
[ Client Requests ] 
       |
       v
+---------------------------------------+
|          API GATEWAY (Nginx/Rails)    | <--- (SAML/OIDC Auth)
+---------------------------------------+
       |                 |
       v                 v
+-------------------+   +----------------------------+
|  MODULAR MONOLITH |   |   EXTERNAL MICROSERVICES   |
| (Ruby on Rails)   |   |  (Future Migration Path)    |
|                   |   |                            |
| +---------------+ |   | +------------------------+  |
| | User Service   | |   | | Billing Service (Node) |  |
| +---------------+ |   | +------------------------+  |
| +---------------+ |   | +------------------------+  |
| | Report Engine  | |   | | Network Sync (Go)      |  |
| +---------------+ |   | +------------------------+  |
| +---------------+ |   +----------------------------+
| | Import/Export  | |
| +---------------+ |
+-------------------+
       |
       v
+---------------------------------------+
|        MySQL 8.0 DATABASE              |
| (Users, Logs, Reports, Telemetry Data) |
+---------------------------------------+
       |
       v
+---------------------------------------+
|       S3 / HEROKU STORAGE              |
| (Stored PDFs, CSVs, Backups)          |
+---------------------------------------+
```

### 2.4 Infrastructure Specifications
- **Runtime:** Ruby 3.3.0
- **Framework:** Rails 7.1.x
- **Database:** MySQL 8.0.35 (Amazon RDS/Heroku Postgres compatible)
- **Caching:** Redis 7.0
- **Environment:** ISO 27001 Certified Cloud VPC

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 SSO Integration with SAML and OIDC (Critical)
**Status:** Complete | **Priority:** Critical (Launch Blocker)

The SSO integration is the cornerstone of Project Archway's security. Since Bellweather Technologies operates in a highly regulated environment, password-based authentication is prohibited for internal tools. 

**Technical Implementation:**
The system implements `omniauth-saml` and `omniauth-openid-connect`. The Gateway acts as the Service Provider (SP), trusting the corporate Identity Provider (IdP) (Okta/Azure AD). Upon a request to `/auth/saml`, the user is redirected to the IdP. Upon successful authentication, the IdP returns a signed XML response containing user attributes (Email, Role, EmployeeID). 

**Functional Requirements:**
- **Attribute Mapping:** The system must map SAML attributes to internal Rails roles (`admin`, `operator`, `viewer`).
- **Session Management:** Sessions are stored in Redis with a hard timeout of 8 hours, aligned with corporate security policy.
- **Just-in-Time (JIT) Provisioning:** If a user exists in the IdP but not in the Archway database, a user record is created automatically upon the first successful login.
- **OIDC Fallback:** For legacy mobile clients, OIDC provides a JWT-based authentication flow.

### 3.2 PDF/CSV Report Generation with Scheduled Delivery (Medium)
**Status:** Complete | **Priority:** Medium

The report engine replaces the fragmented reporting tools in *NetSight* and *SignalFlow*. It allows administrators to generate complex snapshots of network health and user activity.

**Technical Implementation:**
Reports are generated using the `WickedPDF` and `CSV` gems. To prevent request timeouts, report generation is handled asynchronously via **Sidekiq**. When a user requests a report, a `ReportJob` is queued. Once complete, the file is uploaded to an S3 bucket with a time-limited pre-signed URL.

**Functional Requirements:**
- **Format Support:** Support for `.pdf` (formatted for A4) and `.csv` (RFC 4180 compliant).
- **Scheduling Engine:** A cron-like scheduler (via `sidekiq-scheduler`) allows users to set reports for daily, weekly, or monthly delivery.
- **Delivery Vectors:** Reports are delivered via corporate email (SMTP) and an internal notification center.
- **Templating:** Reports use Liquid templates to allow the UX team (Fleur Fischer) to update layouts without requiring a full deployment.

### 3.3 Data Import/Export with Format Auto-Detection (Medium)
**Status:** Blocked | **Priority:** Medium

This feature is designed to facilitate the migration of data from the four legacy tools into Archway. It must handle disparate data formats without requiring the user to specify the source tool.

**Technical Implementation:**
The system will utilize a "Strategy Pattern" for parsing. A `FormatDetector` class will sample the first 10 lines of an uploaded file to detect delimiters (comma, tab, pipe) and encoding (UTF-8, ISO-8859-1). Once detected, the appropriate `ParserStrategy` (e.g., `CsvParser`, `JsonParser`, `XlsxParser`) is instantiated.

**Functional Requirements:**
- **Auto-Detection:** Ability to distinguish between a *TelcoCore* CSV and a *ProvisionX* JSON export based on header signatures.
- **Validation Pipeline:** Data must pass through a three-stage validation process: Schema Validation $\rightarrow$ Type Casting $\rightarrow$ Business Logic Check.
- **Error Reporting:** Instead of failing the entire import, the system must generate an "Error Log CSV" listing every row that failed and the specific reason (e.g., "Invalid IP Address format in Column 4").
- **Blocker Detail:** Current development is blocked due to missing data dictionaries from the *ProvisionX* legacy team.

### 3.4 API Rate Limiting and Usage Analytics (Low)
**Status:** In Review | **Priority:** Low (Nice to have)

To prevent internal services from overwhelming the Gateway, a rate-limiting mechanism is required.

**Technical Implementation:**
Implemented using the `rack-attack` gem. Rate limits are defined in `config/initializers/rack_attack.rb`. Limits are tracked in Redis using a sliding-window algorithm to prevent "burst" traffic from triggering false positives.

**Functional Requirements:**
- **Tiered Limiting:** Different limits based on the API key role (e.g., `System_Service` = 10,000 rpm; `User_Interface` = 100 rpm).
- **Analytics Dashboard:** A view for Bodhi Nakamura (CTO) to monitor the most heavily used endpoints and identify "chatty" services.
- **HTTP 429 Handling:** The API must return a standard `429 Too Many Requests` response with a `Retry-After` header.
- **Logging:** Every rate-limit trigger must be logged to the `api_logs` table for audit purposes.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support (Low)
**Status:** In Review | **Priority:** Low (Nice to have)

While SSO provides the primary security layer, 2FA is requested for users with `super_admin` privileges.

**Technical Implementation:**
Integration of the `rotp` gem for Time-based One-Time Passwords (TOTP) and `webauthn-ruby` for FIDO2/WebAuthn hardware keys (e.g., YubiKey).

**Functional Requirements:**
- **Hardware Key Support:** Users must be able to register multiple YubiKeys for redundancy.
- **Recovery Codes:** Generation of ten 12-character single-use recovery codes upon 2FA activation.
- **Step-up Authentication:** The system should prompt for 2FA only when a user attempts a "Critical Action" (e.g., deleting a network node), rather than at every login.
- **Grace Period:** A 24-hour window for users to set up 2FA after an admin mandate is issued.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All responses are in JSON format.

### 4.1 Authentication Endpoints
**POST `/api/v1/auth/saml/callback`**
- **Description:** Receives the SAML assertion from the IdP.
- **Request:** `samlResponse` (XML String)
- **Response:** `200 OK` `{ "token": "jwt_token_string", "user": { "id": 123, "role": "admin" } }`

**POST `/api/v1/auth/logout`**
- **Description:** Invalidates the current session/token.
- **Request:** `Authorization: Bearer <token>`
- **Response:** `204 No Content`

### 4.2 Report Management Endpoints
**GET `/api/v1/reports`**
- **Description:** Lists all reports generated by the current user.
- **Request:** `Authorization: Bearer <token>`
- **Response:** `200 OK` `[ { "id": "rep_01", "name": "Monthly Signal Audit", "status": "complete", "url": "https://s3.../file.pdf" } ]`

**POST `/api/v1/reports/generate`**
- **Description:** Triggers an asynchronous report generation.
- **Request:** `{ "type": "network_health", "format": "pdf", "filters": { "region": "North_East" } }`
- **Response:** `202 Accepted` `{ "job_id": "sidekiq_abc123", "status": "queued" }`

### 4.3 Data Migration Endpoints
**POST `/api/v1/import/upload`**
- **Description:** Uploads a file for auto-detection and import.
- **Request:** `Multipart/form-data` (File upload)
- **Response:** `201 Created` `{ "import_id": "imp_99", "detected_format": "CSV_TELCOCORE", "estimated_rows": 5000 }`

**GET `/api/v1/import/status/:id`**
- **Description:** Checks the progress of a specific import job.
- **Request:** `import_id` (Path parameter)
- **Response:** `200 OK` `{ "progress": "65%", "errors": 12, "processed": 3250 }`

### 4.4 User & System Management Endpoints
**GET `/api/v1/users/me`**
- **Description:** Returns the current authenticated user's profile.
- **Request:** `Authorization: Bearer <token>`
- **Response:** `200 OK` `{ "email": "u.moreau@bellweather.com", "role": "contractor", "last_login": "2025-01-10T10:00:00Z" }`

**PATCH `/api/v1/system/config`**
- **Description:** Updates system-wide configuration values.
- **Request:** `{ "setting_key": "max_retry_attempts", "value": "5" }`
- **Response:** `200 OK` `{ "status": "updated" }`

---

## 5. DATABASE SCHEMA

The database uses MySQL 8.0. All tables use `bigint` for primary keys and `utf8mb4` encoding.

### 5.1 Table Definitions

| Table Name | Description | Primary Key | Key Fields / Relationships |
| :--- | :--- | :--- | :--- |
| `users` | Central user registry | `user_id` | `email` (unique), `role_id` (FK), `saml_uid` (unique) |
| `roles` | RBAC definitions | `role_id` | `role_name` (admin, operator, viewer), `permissions` (JSON) |
| `api_keys` | Service-to-service tokens | `key_id` | `user_id` (FK), `key_hash`, `expires_at` |
| `reports` | Report metadata and status | `report_id` | `user_id` (FK), `status` (queued, complete, failed), `s3_path` |
| `report_schedules` | Cron definitions for reports | `sched_id` | `report_id` (FK), `cron_expression`, `delivery_email` |
| `imports` | Batch import tracking | `import_id` | `user_id` (FK), `source_tool` (TelcoCore, etc), `status` |
| `import_errors` | Specific row failures | `error_id` | `import_id` (FK), `row_number`, `error_message` |
| `audit_logs` | Security and action logs | `log_id` | `user_id` (FK), `action`, `ip_address`, `timestamp` |
| `system_configs` | Global settings | `config_id` | `config_key` (unique), `config_value` |
| `network_nodes` | Consolidated telecom data | `node_id` | `node_name`, `ip_address`, `status`, `legacy_tool_id` |

### 5.2 Key Relationships
- **One-to-Many:** `users` $\rightarrow$ `audit_logs` (A user generates many logs).
- **One-to-Many:** `imports` $\rightarrow$ `import_errors` (An import can have many row errors).
- **Many-to-One:** `users` $\rightarrow$ `roles` (Many users share one role).
- **One-to-One:** `report_schedules` $\rightarrow$ `reports` (A schedule defines one specific report type).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Archway utilizes three distinct environments to ensure stability and ISO 27001 compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and local testing.
- **Access:** All team members (Bodhi, Wyatt, Fleur, Umi).
- **Database:** Local MySQL instance or shared Dev Heroku app.
- **Deployment:** Continuous Integration (CI) via GitHub Actions on every push to `develop` branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation, QA testing, and Regulatory Review.
- **Access:** Team members and internal stakeholders.
- **Database:** A sanitized clone of production data.
- **Deployment:** Triggered upon merge to `release` branch. This environment mirrors Production specs exactly.

#### 6.1.3 Production (Prod)
- **Purpose:** Live internal tool for Bellweather employees.
- **Access:** Strictly controlled; production logs are forwarded to a secure SIEM.
- **Deployment:** Quarterly releases. Deployments are performed via Heroku Pipeline with a "Blue-Green" strategy to ensure zero downtime.

### 6.2 CI/CD Pipeline
1. **Commit:** Developer pushes to GitHub.
2. **Lint/Test:** GitHub Actions runs `RuboCop` and `RSpec`.
3. **Build:** Heroku Buildpacks compile assets and install gems.
4. **Deploy to Dev:** Automatic deployment to the Dev environment.
5. **QA Gate:** Manual sign-off by dedicated QA member.
6. **Promote to Stage:** Merge to `release` $\rightarrow$ Deploy to Staging.
7. **Regulatory Review:** Quarterly audit of the Staging environment.
8. **Promote to Prod:** Final push to Production on the quarterly release date.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** RSpec.
- **Scope:** Every model and service object must have 90%+ test coverage.
- **Focus:** Testing business logic in isolation (e.g., ensuring the `FormatDetector` correctly identifies a CSV from a JSON file).
- **Mocking:** Use `WebMock` and `VCR` to simulate external API calls to the IdP.

### 7.2 Integration Testing
- **Tooling:** Request Specs / Capybara.
- **Scope:** Testing the interaction between the API Gateway and the Modular Monolith.
- **Focus:** End-to-end request flows, such as:
    1. Requesting a report $\rightarrow$ Sidekiq Job $\rightarrow$ S3 Upload $\rightarrow$ Email Notification.
    2. SAML Login $\rightarrow$ Session Creation $\rightarrow$ Protected Endpoint Access.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Selenium / Cypress.
- **Scope:** User journeys from the perspective of the end-user (Fleur's UX research).
- **Focus:** Critical paths such as "Importing a legacy file" and "Generating a monthly report."
- **Environment:** Performed exclusively in the Staging environment.

### 7.4 Regulatory & Security Testing
- **Penetration Testing:** Quarterly internal pen-tests to maintain ISO 27001 certification.
- **SAML Validation:** Rigorous testing of XML signature verification to prevent "SAML Wrapping" attacks.
- **Rate Limit Stress Tests:** Using `JMeter` to ensure the gateway does not crash under a 10x load spike.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Regulatory requirements change mid-project. | High | High | Negotiate flexible timeline extensions with stakeholders; maintain modular code. |
| **R2** | Team lacks experience with Ruby on Rails/Heroku. | High | Medium | Document workarounds in a shared Wiki; implement pair programming; utilize contractor (Umi). |
| **R3** | Performance bottlenecks in MySQL during import. | Medium | Medium | Implement database indexing and batch processing; move to a larger RDS instance if needed. |
| **R4** | SSO Provider downtime prevents all user access. | Low | Critical | Implement emergency "Break-glass" admin accounts with hardware keys (bypassing SAML). |
| **R5** | Data loss during migration from legacy tools. | Medium | High | Run parallel systems for one quarter; perform checksum validation on all imports. |

### 8.1 Probability/Impact Matrix
- **High Probability/High Impact:** R1 (Regulatory Changes). *Priority 1*
- **High Probability/Medium Impact:** R2 (Skill Gap). *Priority 2*
- **Medium Probability/High Impact:** R5 (Data Loss). *Priority 3*

---

## 9. TIMELINE

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Now - 2025-03-01):** Setup of Heroku environments, ISO 27001 compliance audit, and implementation of SSO.
- **Phase 2: Core Consolidation (2025-03-01 - 2025-06-01):** Building the modular monolith, report engine, and initial data migration scripts.
- **Phase 3: Optimization & QA (2025-06-01 - 2025-08-15):** Stress testing, performance tuning, and final regulatory sign-off.
- **Phase 4: Launch & Stabilization (2025-08-15 - 2025-10-15):** Production rollout and alpha feedback loop.

### 9.2 Key Milestones
- **Milestone 1 (2025-06-15):** Performance benchmarks met (API latency < 200ms).
- **Milestone 2 (2025-08-15):** Production launch (Full cut-over from legacy tools).
- **Milestone 3 (2025-10-15):** Internal alpha release of "Phase 2" features (Advanced Analytics).

### 9.3 Dependencies
- **Critical Path:** SSO $\rightarrow$ Modular Monolith $\rightarrow$ Data Import $\rightarrow$ Production Launch.
- **Blocker:** The "Data Import" feature is currently blocked by the absence of *ProvisionX* data dictionaries.

---

## 10. MEETING NOTES

*Note: These entries are extracted from the 200-page unsearchable running document maintained by the team.*

### Meeting 1: Initial Architecture Sync (2024-11-12)
**Attendees:** Bodhi, Wyatt, Fleur, Umi
**Discussion:**
- Bodhi emphasized the need for a "simple" stack. He rejected the suggestion to use Kubernetes, citing that the team is too small to manage the overhead. 
- Wyatt expressed concern regarding the hardcoded configuration values (40+ files). He suggested a `secrets.yml` or Heroku Config Vars approach.
- Fleur noted that the legacy tools had "conflicting UI patterns." She proposed a complete UX overhaul rather than migrating the old look.
**Decision:** Agreed to use Rails on Heroku. Wyatt will start a "Config Cleanup" sprint to remove hardcoded values.

### Meeting 2: Security & Compliance Review (2024-12-05)
**Attendees:** Bodhi, Wyatt, Umi
**Discussion:**
- The team discussed the ISO 27001 requirements. Umi pointed out that SAML is non-negotiable for the launch blocker.
- Wyatt mentioned that the hardware key support (2FA) might be too complex for the first release.
- Bodhi reminded the team that the budget is $1.5M and we can afford better QA if we find bugs early.
**Decision:** SAML/OIDC is the priority. 2FA is moved to "Low Priority/In Review" status.

### Meeting 3: Resource Crisis & Blocker Update (2025-01-15)
**Attendees:** Bodhi, Wyatt, Fleur
**Discussion:**
- **Emergency:** A key team member (not specified in the prompt, but impacting the pipeline) is on medical leave for 6 weeks.
- Bodhi noted this will delay the "Data Import" feature.
- Umi is attempting to find the *ProvisionX* dictionaries, but the legacy team is unresponsive.
- The team discussed the "unsearchable" meeting document; Wyatt joked that they need a "Search for the Meeting Notes" feature.
**Decision:** Focus on the "Report Generation" feature (which is now complete) to maintain momentum while the import feature remains blocked.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $900,000 | Salaries for Bodhi, Wyatt, Fleur, and Umi's contract fees. |
| **Infrastructure** | $200,000 | Heroku Enterprise credits, MySQL RDS, S3 Storage, Redis Cloud. |
| **Security & Compliance** | $150,000 | ISO 27001 Certification audits and penetration testing vendors. |
| **Software Licenses** | $50,000 | New Relic for monitoring, GitHub Enterprise, Okta integration. |
| **Contingency Fund** | $200,000 | Reserved for regulatory changes, emergency staffing, or hardware. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Ledger
The project inherited significant technical debt from the four legacy systems.
1.  **Hardcoded Configurations:** 42 files contain hardcoded IP addresses and API keys. This is being migrated to Heroku Config Vars.
2.  **Schema Inconsistency:** *TelcoCore* uses `VARCHAR(255)` for IDs, while *ProvisionX* uses `UUID`. The Archway `network_nodes` table will normalize all to `UUID`.
3.  **Ruby Version Drift:** Legacy tools are running on Ruby 2.5. The migration to 3.3 involves significant syntax updates, specifically around keyword arguments.

### Appendix B: Data Mapping Matrix (Legacy $\rightarrow$ Archway)

| Legacy Field (TelcoCore) | Legacy Field (NetSight) | Archway Field | Data Type |
| :--- | :--- | :--- | :--- |
| `cust_id` | `account_num` | `user_id` | UUID |
| `sig_strength` | `dbm_level` | `signal_metrics` | Decimal |
| `prov_date` | `activation_ts` | `activated_at` | DateTime |
| `node_name` | `device_id` | `node_identifier` | String |

---
**End of Specification Document**