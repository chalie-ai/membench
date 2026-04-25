Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional technical specification. To maintain the requested depth, each section is expanded with granular technical data, specific naming conventions, and detailed business logic.

***

# PROJECT SPECIFICATION: PROJECT DRIFT
**Document Version:** 1.0.4  
**Status:** Baseline  
**Date:** October 24, 2023  
**Company:** Coral Reef Solutions  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Drift" is a critical cost-reduction initiative commissioned by Coral Reef Solutions to address systemic inefficiency within the company’s fintech operations. Currently, the organization maintains four redundant internal tools—legacy systems tasked with disparate but overlapping functions of ledger reconciliation, client onboarding, internal audit logging, and risk reporting. These systems operate on four different legacy stacks, requiring four separate maintenance budgets and four distinct sets of security patches.

The operational overhead of maintaining these "silos" has led to "data drift," where the same client entity exists with conflicting attributes across different tools. Drift aims to consolidate these four redundant tools into a single, unified SaaS platform. By migrating to a modern, simplified Ruby on Rails monolith, Coral Reef Solutions will eliminate the licensing fees of three legacy vendors and reduce the engineering hours spent on "bridge" scripts that currently synchronize data between the redundant tools.

### 1.2 ROI Projection
The $3M investment in Project Drift is projected to yield a positive ROI within 18 months of production launch. 

**Cost Savings Analysis:**
- **Licensing Reduction:** Elimination of legacy tool licenses is estimated to save $450,000 annually.
- **Operational Efficiency:** Reducing the "integration tax" (the time spent by engineers managing the four separate tools) is estimated to reclaim 2,500 engineering hours per year, valued at approximately $320,000.
- **Infrastructure Consolidation:** Moving from four fragmented environments to a single Heroku-managed environment is expected to reduce cloud spend by 22% ($80,000/year).

**Projected Total Annual Savings:** ~$850,000.
**Break-even Point:** Q3 2027.

### 1.3 Strategic Alignment
Drift is not merely a technical migration but a strategic alignment project. By unifying the data model, Coral Reef Solutions will achieve a "Single Source of Truth" (SSOT), enabling more accurate financial reporting and reducing the risk of regulatory non-compliance associated with inconsistent data across internal tools.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
To maximize velocity and minimize complexity for a small team of four, Project Drift utilizes a "Boring Technology" stack. The goal is stability and rapid iteration over experimental architecture.

- **Primary Framework:** Ruby on Rails v7.1 (Monolith)
- **Primary Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons)
- **Infrastructure:** Heroku Platform-as-a-Service (PaaS)
- **Orchestration:** Serverless functions (AWS Lambda) triggered via AWS API Gateway for high-compute asynchronous tasks.
- **Compliance:** ISO 27001 certified environment.

### 2.2 Architectural Flow (ASCII Diagram Description)
The system follows a hybrid monolith-serverless pattern. While the core business logic resides in Rails, heavy-lifting tasks are offloaded to serverless functions to keep the web dynos responsive.

```
[ User Browser / API Client ]
          |
          v
[ Heroku Load Balancer ]
          |
          v
[ Ruby on Rails Monolith (Web Dynos) ] <---> [ MySQL Database ]
          |                                      ^
          | (Event Trigger)                      | (Data Sync)
          v                                      |
[ AWS API Gateway ]                              |
          |                                      |
          v                                      |
[ AWS Lambda (Serverless Functions) ] ------------+
   - Virus Scanning
   - CDN Cache Purging
   - PDF Generation
```

### 2.3 Integration Logic
The Rails monolith handles session management, RBAC, and primary CRUD operations. When a "heavy" action is triggered (e.g., a file upload for virus scanning), Rails sends a payload to the API Gateway. The Lambda function processes the request and updates the MySQL database directly or via a callback webhook to the Rails app.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** In Design | **Lead:** Ren Kim

**Description:**
The core of the Drift platform requires a rigorous authentication system to ensure that sensitive fintech data is only accessible to authorized personnel. Given the ISO 27001 requirement, the system must implement an audited trail of every login and privilege escalation.

**Functional Requirements:**
- **Multi-Factor Authentication (MFA):** Mandatory TOTP (Time-based One-Time Password) for all users.
- **Role Hierarchy:** 
    - *Super Admin:* Full system access, user management, and audit log viewing.
    - *Compliance Officer:* Read-only access to all financial data, full access to audit logs.
    - *Operator:* Read/Write access to specific client records based on assigned territory.
    - *Viewer:* Read-only access to their own assigned portfolio.
- **Session Management:** JWT (JSON Web Tokens) stored in secure, HTTP-only cookies with a 30-minute sliding expiration.
- **Password Policy:** Minimum 12 characters, requiring uppercase, lowercase, numeric, and special characters.

**Technical Logic:**
The system will utilize a `Roles` and `Permissions` join table. Permissions are granular (e.g., `can_edit_ledger`, `can_approve_onboarding`). A user's role is a collection of these permissions. This prevents "role creep" and allows for quick adjustments without changing the code.

### 3.2 Localization and Internationalization (L10n/i18n)
**Priority:** High | **Status:** In Progress | **Lead:** Noor Moreau

**Description:**
To support global operations, Drift must support 12 languages (English, Spanish, French, German, Mandarin, Japanese, Portuguese, Italian, Korean, Arabic, Dutch, and Russian).

**Functional Requirements:**
- **Dynamic Switching:** Users can switch languages via a profile setting or a dropdown in the footer.
- **RTL Support:** Full Right-to-Left (RTL) layout support for Arabic.
- **Currency Formatting:** Automatic formatting of currency based on the selected locale (e.g., $1,000.00 vs 1.000,00 €).
- **Date/Time Normalization:** All dates stored in UTC in MySQL and rendered in the user's local timezone via `moment.js` or Rails' `I18n` helpers.

**Technical Logic:**
The platform uses the Rails `I18n` gem. Translation files (`en.yml`, `es.yml`, etc.) are managed in a dedicated `/config/locales` directory. To prevent the application from bloating, translations are lazy-loaded based on the user's session preference.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Review | **Lead:** Sol Jensen

**Description:**
Users must be able to upload KYC (Know Your Customer) documents. These files must be scanned for malware before being stored and then distributed via CDN for fast retrieval by internal auditors.

**Functional Requirements:**
- **Upload Pipeline:** Files are uploaded to a temporary S3 "Quarantine" bucket.
- **Virus Scanning:** An AWS Lambda function is triggered upon upload, running a ClamAV scan.
- **Promotion Logic:** If "Clean," the file is moved to the "Production" S3 bucket. If "Infected," the file is deleted, and an alert is sent to the Security Engineer (Ren Kim).
- **CDN Delivery:** Files are served via CloudFront with signed URLs to prevent unauthorized public access.

**Technical Logic:**
The Rails app generates a pre-signed S3 URL for the frontend. The frontend uploads directly to S3 to avoid choking the Rails web dynos. The S3 `ObjectCreated` event triggers the Lambda virus scan.

### 3.4 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** Complete | **Lead:** Noor Moreau

**Description:**
Designed for field agents who may lose connectivity, the platform allows basic data entry and viewing while offline.

**Functional Requirements:**
- **Local Persistence:** Use of IndexedDB for storing cached records and pending changes.
- **Queue Management:** A "Sync Queue" that tracks all mutations made while offline.
- **Conflict Resolution:** A "Last-Write-Wins" strategy for simple fields, and a manual "Review Conflict" flag for complex financial records.
- **Automatic Re-sync:** Once a heartbeat to the server is restored, the queue is flushed sequentially.

**Technical Logic:**
Implemented using a Service Worker that intercepts network requests. When the `navigator.onLine` status is false, requests are routed to IndexedDB. Upon reconnection, a background sync process sends the queued payloads to the `/api/v1/sync` endpoint.

### 3.5 Customer-Facing API with Versioning and Sandbox
**Priority:** Low | **Status:** Not Started | **Lead:** Kamau Park

**Description:**
A public-facing REST API allowing B2B clients to programmatically push data into Drift.

**Functional Requirements:**
- **API Key Management:** Users can generate and revoke API keys (secret/public pair).
- **Versioning:** Versioning via URL (e.g., `/api/v1/`, `/api/v2/`).
- **Sandbox Environment:** A mirrored "test" environment where clients can run requests without impacting production data.
- **Rate Limiting:** 1,000 requests per hour per API key, enforced via Redis.

**Technical Logic:**
The API will be built using Rails' `api_only` mode for the controllers. Versioning will be handled via namespaced controllers. The sandbox will be a separate Heroku app (`drift-sandbox.heroku.com`) pointing to a separate "Sandbox" MySQL instance.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include an `Authorization: Bearer <token>` header.

### 4.1 `POST /auth/login`
- **Purpose:** Authenticate user and return JWT.
- **Request Body:** `{"email": "user@example.com", "password": "password123"}`
- **Response (200):** `{"token": "eyJhbG...", "expires_at": "2023-10-25T10:00:00Z"}`
- **Response (401):** `{"error": "Invalid credentials"}`

### 4.2 `GET /users/profile`
- **Purpose:** Retrieve the authenticated user's profile and role.
- **Request Body:** None.
- **Response (200):** `{"id": 45, "name": "Jane Doe", "role": "Operator", "locale": "en-US"}`

### 4.3 `POST /documents/upload_url`
- **Purpose:** Get a pre-signed S3 URL for file upload.
- **Request Body:** `{"filename": "kyc_doc.pdf", "content_type": "application/pdf"}`
- **Response (200):** `{"upload_url": "https://s3.amazonaws.com/drift-quarantine/...", "file_id": "uuid-123"}`

### 4.4 `GET /documents/:id`
- **Purpose:** Retrieve a signed CDN link for a file.
- **Request Body:** None.
- **Response (200):** `{"cdn_url": "https://cdn.drift.com/files/uuid-123?token=abc", "expires_in": 3600}`

### 4.5 `GET /ledger/summary`
- **Purpose:** Get a summary of financial accounts.
- **Request Body:** `{"start_date": "2023-01-01", "end_date": "2023-12-31"}`
- **Response (200):** `{"total_balance": 1500000.00, "currency": "USD", "accounts_count": 12}`

### 4.6 `PATCH /ledger/accounts/:id`
- **Purpose:** Update a specific ledger account.
- **Request Body:** `{"status": "verified", "balance": 1200.50}`
- **Response (200):** `{"id": 101, "status": "verified", "updated_at": "2023-10-24T15:00:00Z"}`

### 4.7 `GET /audit/logs`
- **Purpose:** Retrieve system audit logs (Admin/Compliance only).
- **Request Body:** `{"filter": "auth_failures", "limit": 50}`
- **Response (200):** `[{"timestamp": "...", "user_id": 12, "action": "LOGIN_FAILED", "ip": "1.1.1.1"}]`

### 4.8 `POST /sync/batch`
- **Purpose:** Process offline-first background sync queue.
- **Request Body:** `{"batch_id": "sync-99", "changes": [{"action": "update", "table": "clients", "data": {...}}]}`
- **Response (200):** `{"status": "success", "synced_records": 5, "conflicts": 0}`

---

## 5. DATABASE SCHEMA

The database utilizes a normalized MySQL 8.0 schema. All tables use `bigint` for primary keys to avoid overflow.

### 5.1 Tables and Relationships

1. **`users`**
   - `id` (PK), `email` (Unique), `password_digest`, `mfa_secret`, `role_id` (FK), `locale` (varchar), `created_at`, `updated_at`.
2. **`roles`**
   - `id` (PK), `role_name` (Unique), `description`.
3. **`permissions`**
   - `id` (PK), `permission_key` (Unique), `description`.
4. **`role_permissions`** (Join Table)
   - `role_id` (FK), `permission_id` (FK).
5. **`clients`**
   - `id` (PK), `full_name`, `tax_id` (Unique), `country_code`, `status` (enum: pending, active, archived), `created_at`.
6. **`accounts`**
   - `id` (PK), `client_id` (FK), `account_number` (Unique), `balance` (decimal 19,4), `currency_code`.
7. **`transactions`**
   - `id` (PK), `account_id` (FK), `amount` (decimal), `transaction_type` (enum), `timestamp`.
8. **`documents`**
   - `id` (PK), `client_id` (FK), `s3_key`, `status` (enum: quarantined, clean, infected), `virus_scan_date`.
9. **`audit_logs`**
   - `id` (PK), `user_id` (FK), `action`, `target_table`, `target_id`, `ip_address`, `created_at`.
10. **`sync_sessions`**
    - `id` (PK), `user_id` (FK), `device_id`, `last_synced_at`, `pending_changes_count`.

### 5.2 Key Relationships
- **User $\to$ Role:** Many-to-One.
- **Role $\to$ Permission:** Many-to-Many.
- **Client $\to$ Account:** One-to-Many.
- **Account $\to$ Transaction:** One-to-Many.
- **Client $\to$ Document:** One-to-Many.
- **User $\to$ Audit Log:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To maintain stability, Drift employs a strict three-tier environment promotion strategy.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Access:** Full access for the team of 4.
- **Data:** Mock data generated by seeds.
- **Deployment:** Continuous Deployment (CD) from the `develop` branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation, QA, and UAT (User Acceptance Testing).
- **Access:** Team and selected Project Sponsors.
- **Data:** Sanitized snapshot of production data (GDPR compliant).
- **Deployment:** Deployed from the `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live fintech operations.
- **Access:** Restricted to Kamau Park and Ren Kim.
- **Data:** Real customer data.
- **Deployment:** Weekly release train.

### 6.2 The Release Train
**Policy:** All changes (features, bug fixes, config updates) are bundled into a weekly release.
- **Cut-off:** Wednesday, 23:59 UTC.
- **Deployment Window:** Thursday, 02:00 UTC.
- **Strict Rule:** No hotfixes are permitted outside the train. If a critical bug is found, it must be fixed in `develop`, promoted to `stage`, and then deployed in the next scheduled train, unless a "Severity 0" emergency is declared by the Engineering Manager.

### 6.3 Infrastructure as Code (IaC)
While Heroku is used for the monolith, the AWS components (Lambda, S3, API Gateway) are managed via Terraform to ensure the ISO 27001 environment can be replicated exactly if a disaster recovery event occurs.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** RSpec.
- **Coverage Target:** 85% minimum.
- **Focus:** Business logic, model validations, and helper methods. Every single Rails model must have a corresponding `_spec.rb` file.

### 7.2 Integration Testing
- **Tool:** RSpec Request Specs.
- **Focus:** API endpoint contracts. We test the request/response cycle including authentication headers.
- **Mocking:** Use `VCR` to record and replay responses from the external integration partner's API to avoid flaky tests.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Critical "Happy Paths" (e.g., User Login $\to$ Upload Document $\to$ Verify Document).
- **Frequency:** Run on the `stage` environment before every weekly release train.

### 7.4 Security Testing
- **Static Analysis:** `Brakeman` for Rails security vulnerability scanning.
- **Dependency Scanning:** `Bundler-audit` to check for CVEs in gems.
- **Penetration Testing:** Quarterly external audit as required by ISO 27001.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | Medium | High | Escalate to Steering Committee immediately to secure long-term funding commitments. |
| R-02 | Integration partner's API is undocumented/buggy | High | Medium | Raise as a formal blocker in the next Board Meeting; request a dedicated technical liaison. |
| R-03 | Legal review of Data Processing Agreement (DPA) delay | High | High | Establish a weekly cadence with Legal; provide a "Risk Acceptance" sign-off for dev environments. |
| R-04 | Production debugging difficulty (Lack of structured logging) | Medium | Medium | Implement `Lograge` in the next sprint to replace stdout with JSON structured logs. |
| R-05 | ISO 27001 Certification failure | Low | Critical | Weekly compliance checks by Ren Kim; strictly follow the Terraform-defined infrastructure. |

---

## 9. TIMELINE & MILESTONES

### 9.1 Project Phases
**Phase 1: Foundation & Core Auth (Oct 2023 – May 2025)**
- Focus on RBAC, Database Schema, and Basic Rails setup.
- Dependency: Legal review of DPA.

**Phase 2: Feature Parity & Consolidation (May 2025 – July 2025)**
- Migration of data from 4 redundant tools.
- Implementation of L10n/i18n.
- Dependency: Completion of MVP feature set.

**Phase 3: Hardening & Launch (July 2025 – Sept 2025)**
- Load testing to meet p95 < 200ms.
- Final ISO 27001 audit.
- Final Production cut-over.

### 9.2 Key Milestone Dates
- **Milestone 1: MVP Feature-Complete** $\to$ **2025-05-15**
- **Milestone 2: Architecture Review Complete** $\to$ **2025-07-15**
- **Milestone 3: Production Launch** $\to$ **2025-09-15**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Kamau Park, Noor Moreau, Ren Kim, Sol Jensen  
**Discussion:**
- The team discussed whether to go with a Microservices architecture. Kamau vetoed this, citing the small team size (4 people).
- Decision: Stick to a Rails monolith for speed, using Lambda only for the virus scanner.
- Noor raised concerns about the offline-first sync logic. Decision: Use IndexedDB on the frontend and a batch sync endpoint on the backend.

**Action Items:**
- [Kamau] Finalize the Heroku plan selection (Professional vs Enterprise).
- [Ren] Draft the ISO 27001 compliance checklist.

### Meeting 2: Localization Strategy
**Date:** 2023-12-15  
**Attendees:** Kamau Park, Noor Moreau  
**Discussion:**
- Noor presented the 12-language list. Discussion on how to handle Arabic RTL.
- Decision: Implement a CSS class `.rtl` on the body tag based on the user's locale setting.
- Discussion on currency: Agreed that MySQL will store values in `decimal(19,4)` to avoid floating point errors.

**Action Items:**
- [Noor] Set up the `I18n` gem and create the initial `.yml` files for English and Spanish.

### Meeting 3: Risk Assessment & Blockers
**Date:** 2024-01-20  
**Attendees:** Kamau Park, Ren Kim, Sol Jensen  
**Discussion:**
- Ren reported that the integration partner's API is returning inconsistent 500 errors without documentation.
- Kamau identified that the project sponsor is rotating out of their role.
- Discussion on logging: The team is struggling to debug production issues because they are reading raw stdout.

**Action Items:**
- [Kamau] Email the Steering Committee regarding the sponsor rotation.
- [Kamau] Add "Partner API instability" to the Board Meeting agenda.
- [Ren] Research `Lograge` for structured logging.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $2,100,000 | Salaries for 3 FTEs + 1 Contractor (Sol Jensen) over 24 months. |
| **Infrastructure** | 15% | $450,000 | Heroku Enterprise, AWS Lambda, S3, CloudFront, MySQL managed instances. |
| **Tools & Licensing** | 5% | $150,000 | ISO 27001 Certification audits, Terraform Cloud, Sentry for error tracking. |
| **Contingency** | 10% | $300,000 | Reserve for unforeseen legal costs or additional contract help. |

---

## 12. APPENDICES

### Appendix A: Data Migration Mapping
This section details how the 4 redundant tools map into the new Drift schema.
- **Tool A (Ledger):** Maps to `accounts` and `transactions`.
- **Tool B (Onboarding):** Maps to `clients` and `documents`.
- **Tool C (Audit):** Maps to `audit_logs`.
- **Tool D (Risk):** Maps to `clients` (risk status attributes).
- **Migration Strategy:** A custom Ruby script will extract data from the 4 legacy SQL databases, normalize it into CSVs, and import it into Drift using the `ActiveRecord` import gem.

### Appendix B: ISO 27001 Control Mapping
To ensure certification, the following controls are implemented:
- **Access Control:** RBAC is strictly enforced. All administrative actions are logged in the `audit_logs` table.
- **Encryption:** Data at rest is encrypted using AWS KMS. Data in transit is forced via TLS 1.3.
- **Network Security:** Heroku Private Spaces are used to isolate the database from the public internet.
- **Availability:** 99.9% uptime target achieved through Heroku's multi-zone redundancy.