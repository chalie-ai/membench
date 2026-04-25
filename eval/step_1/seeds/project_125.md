# PROJECT SPECIFICATION: PROJECT GLACIER
**Version:** 1.0.4-BETA  
**Status:** Draft for Implementation  
**Date:** October 24, 2023  
**Company:** Stratos Systems  
**Classification:** Confidential / Internal Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Glacier is the strategic response to a critical failure in the current payment processing ecosystem utilized by Stratos Systems for its educational sector clients. The legacy system—characterized by high latency, frequent downtime, and a fragmented user interface—has resulted in catastrophic user feedback, leading to a churn rate of 18% in the last fiscal quarter. Educational institutions, particularly those dealing with government funding and large-scale student tuition, require absolute precision, auditability, and reliability. The existing system fails to meet these basic requirements, creating a reputational risk that threatens the company's survival in the EdTech space.

Glacier is not merely an iteration; it is a complete ground-up rebuild. By shifting to a Rust-based backend and leveraging Cloudflare Workers for edge computing, Stratos Systems aims to eliminate the latency bottlenecks that plagued the previous version. The primary objective is to transition from a "leaky" legacy system to a hardened, FedRAMP-compliant infrastructure that can support government-funded education contracts, thereby opening a new revenue stream previously inaccessible due to security deficiencies.

### 1.2 ROI Projection
Given that Project Glacier is currently unfunded and bootstrapping via existing team capacity, the ROI is calculated based on "cost avoidance" and "market expansion."

*   **Churn Reduction:** By improving the NPS score from the current negative range to >40, we project a reduction in churn from 18% to <5%. For a client base generating $12M ARR, this represents a retention of $1.56M in annual revenue.
*   **Government Market Entry:** FedRAMP authorization allows Stratos Systems to bid on Department of Education (DoE) contracts. The projected Total Addressable Market (TAM) for these contracts is estimated at $4.2M in the first 18 months post-launch.
*   **Infrastructure Optimization:** Moving to Cloudflare Workers and SQLite at the edge is projected to reduce monthly AWS overhead from $8,500/mo to approximately $2,100/mo, resulting in an annual saving of $76,800.

The total projected financial impact over the first 24 months post-launch is estimated at $5.7M, assuming the successful onboarding of the first paying customer by December 15, 2026.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Project Glacier utilizes a traditional three-tier architecture but implements it using a "Modern Edge" approach to ensure the p95 response time remains under 200ms.

1.  **Presentation Tier (Frontend):** A React-based Single Page Application (SPA) deployed via Cloudflare Pages. It utilizes Tailwind CSS for styling and TanStack Query for state management and caching.
2.  **Business Logic Tier (Backend):** A series of Rust-based micro-services compiled to WebAssembly (Wasm) and deployed as Cloudflare Workers. Rust was chosen for its memory safety and performance, critical for financial calculations and FedRAMP compliance.
3.  **Data Tier (Storage):** A hybrid approach utilizing SQLite for edge-local caching and state (using Cloudflare D1) and a centralized PostgreSQL instance (managed via Supabase/AWS) for the source of truth and long-term audit logs.

### 2.2 ASCII Architecture Diagram
```text
[ USER BROWSER ] 
       |
       v
[ CLOUDFLARE EDGE / GLOBAL NETWORK ]
       |
       +--> [ React Frontend (Cloudflare Pages) ]
       |
       +--> [ Rust Backend (Cloudflare Workers / Wasm) ]
               |
               +--[ Cache/Session ]--> [ SQLite / D1 Edge DB ]
               |
               +--[ Core Logic ]------> [ Auth / Logic / Validation ]
               |
               +--[ Persistent Storage ]--> [ PostgreSQL (Main DB) ]
                                              |
                                              +--> [ Tamper-Evident Log ]
                                              +--> [ PDF/CSV Storage (S3) ]
```

### 2.3 Technical Constraints
*   **Strict Weekly Release Train:** To maintain stability, all code must be merged by Thursday 12:00 PM UTC for a Friday 09:00 AM UTC deployment. No hotfixes are permitted outside this window unless a "Severity 1" outage is declared by Wyatt Park.
*   **The "Raw SQL" Debt:** Currently, 30% of the data access layer bypasses the ORM to utilize raw SQL for performance. This creates a significant risk during migrations. All new development must utilize the ORM unless a performance benchmark proves a >50ms improvement.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
To meet FedRAMP requirements and secure financial transactions, Glacier must implement a robust 2FA system. While standard TOTP (Time-based One-Time Password) is required, the system must prioritize hardware-based authentication (FIDO2/WebAuthn) to prevent phishing attacks.

**Detailed Requirements:**
*   **WebAuthn Integration:** The system must support YubiKey and Google Titan keys. The backend must handle the challenge-response cycle via the Rust `webauthn-rs` crate.
*   **Fallback Mechanisms:** Users must be able to generate one-time recovery codes (10 codes per user) stored as salted hashes in the database.
*   **Enforcement Levels:** 2FA must be mandatory for any user with "Administrator" or "Finance" roles. For "Standard" users, it is encouraged but optional.
*   **Session Binding:** Once 2FA is verified, the session token must be bound to the hardware device fingerprint to prevent session hijacking.

**Acceptance Criteria:**
1. User can register a YubiKey via the `/settings/security` page.
2. User is prompted for a hardware touch upon login from a new IP address.
3. Recovery codes successfully grant access when the hardware key is lost.
4. System logs every successful and failed 2FA attempt in the audit trail.

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Educational institutions require monthly financial reconciliations for government audits. Glacier must provide an automated system to generate these reports and deliver them via secure channels.

**Detailed Requirements:**
*   **Generation Engine:** Use a Rust-based PDF generator (e.g., `printpdf`) to create non-editable financial statements.
*   **CSV Export:** Provide a raw data export for use in Excel/Google Sheets, ensuring UTF-8 encoding and RFC 4180 compliance.
*   **Scheduling Logic:** A cron-based trigger within Cloudflare Workers (Cron Triggers) will execute report generation on the 1st of every month at 00:00 UTC.
*   **Delivery Pipeline:** Reports must be uploaded to an encrypted S3 bucket. The user is sent a signed, time-limited URL (expiring in 24 hours) via email.

**Acceptance Criteria:**
1. Administrator can schedule a "Weekly Tuition Summary" report.
2. PDF reports are formatted with the Stratos Systems corporate header and footer.
3. CSV exports contain all transaction fields including timestamps, UIDs, and currency codes.
4. Reports are delivered within 15 minutes of the scheduled trigger.

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review

**Description:**
Given the fintech nature of the product, every state change must be logged. To satisfy FedRAMP, these logs must be "tamper-evident," meaning any modification to a historical log entry must be detectable.

**Detailed Requirements:**
*   **Hashing Chain:** Each log entry must contain a SHA-256 hash of the previous entry, creating a cryptographic chain.
*   **Immutable Storage:** Logs are written to a "Write Once, Read Many" (WORM) storage bucket.
*   **Scope of Logging:** All `POST`, `PUT`, `PATCH`, and `DELETE` requests must be logged, including the User ID, Timestamp, IP Address, Request Payload, and Response Status.
*   **Verification Tool:** A built-in admin utility must be able to re-calculate the hash chain to verify that no logs have been deleted or altered.

**Acceptance Criteria:**
1. Any attempt to manually edit a row in the `audit_logs` table breaks the hash chain verification.
2. Log entries are generated in < 20ms to avoid impacting API performance.
3. Logs are searchable by User ID and Date Range.

### 3.4 A/B Testing Framework (Integrated into Feature Flags)
**Priority:** High | **Status:** Blocked

**Description:**
To avoid the "catastrophic feedback" of the previous version, Glacier will use an integrated A/B testing framework. This allows the team to roll out new UI patterns to 5% of users before a full release.

**Detailed Requirements:**
*   **Flag Definition:** Feature flags are defined in a JSON configuration file stored in the edge KV store.
*   **Bucketing Logic:** Users are assigned a persistent "bucket ID" (0-99) based on a hash of their User ID.
*   **Metric Tracking:** The framework must track conversion rates (e.g., "Payment Completion Rate") for Version A vs. Version B.
*   **Automatic Rollback:** If a feature flag's associated error rate exceeds 1%, the system must automatically toggle the flag to "Off" for all users.

**Acceptance Criteria:**
1. Product lead can change a flag from "Control" to "Experiment" without a code deploy.
2. Users in the same bucket consistently see the same version of a feature.
3. Analytics dashboard shows a side-by-side comparison of the two variants.

### 3.5 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** Blocked

**Description:**
The system requires a granular permission system to separate duties between student administrators, financial officers, and system auditors.

**Detailed Requirements:**
*   **Roles:** Defined roles include `SuperAdmin`, `FinanceManager`, `Auditor`, and `Student`.
*   **Permission Mapping:** A many-to-many relationship between roles and specific permissions (e.g., `can_refund_payment`, `can_view_audit_logs`).
*   **JWT Implementation:** Use JSON Web Tokens (JWT) with a short expiry (15 minutes) and a refresh token stored in an `HttpOnly` cookie.
*   **Middleware Enforcement:** A Rust middleware layer must intercept every request and validate that the user's role possesses the required permission for that specific endpoint.

**Acceptance Criteria:**
1. A user with the `Auditor` role cannot execute a `POST` request to the `/payments` endpoint.
2. Changing a user's role in the DB reflects in their session upon the next token refresh.
3. JWTs are signed using the RS256 algorithm.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer` token in the Authorization header.

### 4.1 `POST /payments/process`
**Description:** Initiates a new payment transaction.
*   **Request Body:**
    ```json
    {
      "amount": 1250.00,
      "currency": "USD",
      "student_id": "STU-99283",
      "payment_method_id": "pm_12345",
      "idempotency_key": "unique-req-id-001"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "transaction_id": "TXN-882731",
      "status": "pending",
      "created_at": "2026-08-15T10:00:00Z"
    }
    ```

### 4.2 `GET /payments/transaction/{id}`
**Description:** Retrieves the status of a specific transaction.
*   **Request:** `GET /api/v1/payments/transaction/TXN-882731`
*   **Response (200 OK):**
    ```json
    {
      "transaction_id": "TXN-882731",
      "amount": 1250.00,
      "status": "completed",
      "timestamp": "2026-08-15T10:05:00Z"
    }
    ```

### 4.3 `POST /reports/generate`
**Description:** Manually triggers the generation of a financial report.
*   **Request Body:**
    ```json
    {
      "report_type": "tuition_reconciliation",
      "format": "pdf",
      "start_date": "2026-01-01",
      "end_date": "2026-01-31"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    {
      "job_id": "JOB-4412",
      "status": "processing",
      "estimated_completion": "2 minutes"
    }
    ```

### 4.4 `GET /reports/download/{job_id}`
**Description:** Retrieves a signed URL for a generated report.
*   **Request:** `GET /api/v1/reports/download/JOB-4412`
*   **Response (200 OK):**
    ```json
    {
      "url": "https://s3.stratossystems.com/reports/temp-link-xyz.pdf",
      "expires_at": "2026-08-16T10:00:00Z"
    }
    ```

### 4.5 `POST /auth/2fa/register`
**Description:** Registers a new WebAuthn hardware key.
*   **Request Body:**
    ```json
    {
      "credential_id": "base64_encoded_id",
      "public_key": "base64_encoded_key",
      "sign_count": 0
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "registered", "key_id": "KEY-551" }
    ```

### 4.6 `POST /auth/2fa/verify`
**Description:** Verifies a hardware key challenge.
*   **Request Body:**
    ```json
    {
      "challenge": "server_provided_challenge",
      "signature": "client_generated_signature"
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "verified", "session_token": "jwt_token_here" }
    ```

### 4.7 `GET /audit/logs`
**Description:** Retrieves a paginated list of system audit logs.
*   **Query Params:** `?page=1&limit=50&user_id=USR-123`
*   **Response (200 OK):**
    ```json
    {
      "logs": [
        { "id": "LOG-1", "action": "PAYMENT_CREATE", "user": "USR-123", "hash": "a1b2c3d4..." }
      ],
      "next_page": 2
    }
    ```

### 4.8 `POST /flags/update`
**Description:** Updates the state of a feature flag (Admin only).
*   **Request Body:**
    ```json
    {
      "flag_id": "new_payment_flow",
      "enabled": true,
      "percentage": 10
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "updated", "updated_at": "2026-08-15T12:00:00Z" }
    ```

---

## 5. DATABASE SCHEMA

The system uses a relational model. Due to the performance requirements, certain tables are mirrored in SQLite for edge access, while the primary source of truth resides in PostgreSQL.

### 5.1 Table Definitions

1.  **`users`**
    *   `user_id` (UUID, PK)
    *   `email` (VARCHAR, Unique)
    *   `password_hash` (VARCHAR)
    *   `role_id` (FK -> roles.role_id)
    *   `created_at` (Timestamp)

2.  **`roles`**
    *   `role_id` (INT, PK)
    *   `role_name` (VARCHAR: SuperAdmin, FinanceManager, Auditor, Student)
    *   `description` (TEXT)

3.  **`permissions`**
    *   `perm_id` (INT, PK)
    *   `perm_key` (VARCHAR: e.g., 'payment.create')
    *   `description` (TEXT)

4.  **`role_permissions`**
    *   `role_id` (FK -> roles.role_id)
    *   `perm_id` (FK -> permissions.perm_id)
    *   *Composite PK (role_id, perm_id)*

5.  **`payments`**
    *   `payment_id` (UUID, PK)
    *   `student_id` (UUID)
    *   `amount` (DECIMAL 19,4)
    *   `currency` (VARCHAR 3)
    *   `status` (VARCHAR: pending, completed, failed, refunded)
    *   `created_at` (Timestamp)
    *   `updated_at` (Timestamp)

6.  **`payment_methods`**
    *   `method_id` (UUID, PK)
    *   `user_id` (FK -> users.user_id)
    *   `provider` (VARCHAR: stripe, paypal, bank_transfer)
    *   `token` (VARCHAR)
    *   `last_four` (VARCHAR 4)

7.  **`audit_logs`**
    *   `log_id` (BIGINT, PK)
    *   `user_id` (FK -> users.user_id)
    *   `action` (VARCHAR)
    *   `payload` (JSONB)
    *   `timestamp` (Timestamp)
    *   `previous_hash` (VARCHAR 64)
    *   `current_hash` (VARCHAR 64)

8.  **`two_factor_keys`**
    *   `key_id` (UUID, PK)
    *   `user_id` (FK -> users.user_id)
    *   `public_key` (TEXT)
    *   `credential_id` (TEXT)
    *   `created_at` (Timestamp)

9.  **`report_jobs`**
    *   `job_id` (UUID, PK)
    *   `user_id` (FK -> users.user_id)
    *   `report_type` (VARCHAR)
    *   `status` (VARCHAR: queued, processing, completed, failed)
    *   `s3_url` (VARCHAR)
    *   `created_at` (Timestamp)

10. **`feature_flags`**
    *   `flag_id` (VARCHAR, PK)
    *   `is_enabled` (BOOLEAN)
    *   `rollout_percentage` (INT)
    *   `updated_by` (FK -> users.user_id)

### 5.2 Relationships
*   **One-to-Many:** `users` $\to$ `payments` (One user can have many payments).
*   **Many-to-Many:** `roles` $\leftrightarrow$ `permissions` (via `role_permissions`).
*   **One-to-One:** `users` $\to$ `two_factor_keys` (Simplified for hardware keys).
*   **One-to-Many:** `users` $\to$ `audit_logs` (One user generates many log entries).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Glacier maintains three distinct environments. Promotion to the next environment occurs only after the QA Lead (Elara Stein) provides a sign-off in the Slack `#glacier-deploy` channel.

#### 6.1.1 Development (Dev)
*   **Purpose:** Daily feature development and iteration.
*   **Deployment:** Continuous Deployment (CD) on every merge to the `develop` branch.
*   **Infrastructure:** Cloudflare Workers (Dev namespace), SQLite local files.
*   **Data:** Mock data only. No PII (Personally Identifiable Information) allowed.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
*   **Deployment:** Weekly Release Train (Tuesdays).
*   **Infrastructure:** Mirror of Production, but with lower-tier compute resources.
*   **Data:** Sanitized production clone.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer traffic.
*   **Deployment:** Weekly Release Train (Fridays 09:00 AM UTC).
*   **Infrastructure:** Full Cloudflare Edge network, PostgreSQL High Availability (HA) cluster.
*   **Data:** Live encrypted client data.

### 6.2 Deployment Pipeline
1.  **CI Phase:** GitHub Actions runs `cargo test` and `npm test`.
2.  **Security Scan:** Snyk scan for dependencies; `cargo audit` for Rust crates.
3.  **Artifact Creation:** Rust code is compiled to Wasm targets.
4.  **Deploy:** `wrangler deploy` pushes the Wasm binary to the designated Cloudflare environment.
5.  **Smoke Test:** Automated health check on `/api/v1/health` endpoint.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Backend (Rust):** Every business logic function must have a corresponding unit test. We target 80% code coverage. Use `mockall` for mocking external API calls (e.g., payment gateways).
*   **Frontend (React):** Use Vitest and React Testing Library to test individual components (e.g., ensuring the payment form validates currency inputs).

### 7.2 Integration Testing
*   **API Integration:** A suite of tests using `K6` and `Postman` to verify the flow between the Rust backend and the PostgreSQL database.
*   **Database Migrations:** Since 30% of the code uses raw SQL, every migration must be tested against a production-sized dataset clone in Staging to ensure no performance regressions or locking issues.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Critical Paths:**
    1. User Login $\to$ 2FA Verification $\to$ Payment Processing $\to$ Receipt Generation.
    2. Admin Login $\to$ Report Scheduling $\to$ Download PDF.
    3. User Role Change $\to$ Permission Verification (Access Denied).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | Critical | **Parallel-Path:** Prototype alternative architecture patterns and document all "tribal knowledge" now. | Wyatt Park |
| R-02 | Competitor 2 months ahead in market | Medium | High | **Competitive Intelligence:** Dedicated owner to track competitor feature releases and prioritize "gap-fill" features. | Gael Santos |
| R-03 | Raw SQL debt causes migration failure | High | Medium | **Strict Migration Policy:** No raw SQL changes allowed without a peer review from the DevOps engineer. | Xiomara Moreau |
| R-04 | FedRAMP authorization delay | Low | High | **Early Audit:** Perform a "pre-audit" internally to identify gaps before the official certification process. | Elara Stein |
| R-05 | Design disagreement (Product vs Eng) | High | Medium | **Decision Pivot:** Escalation to VP level; use A/B testing to let data decide the winner. | Wyatt Park |

---

## 9. TIMELINE AND MILESTONES

Project Glacier follows a phased approach. Dependencies are strict: 2FA and Report Generation *must* be completed before Production Launch.

### Phase 1: Core Foundation (Now $\to$ March 2026)
*   **Objective:** Establish the Rust/Cloudflare infrastructure.
*   **Key Activities:** Implement RBAC, build the payment processing engine, set up the SQLite edge layer.
*   **Dependency:** Hardware key API integration must be finalized.

### Phase 2: Hardening & Compliance (April 2026 $\to$ July 2026)
*   **Objective:** Achieve FedRAMP readiness.
*   **Key Activities:** Implement tamper-evident logging, finalize PDF generation, conduct security audits.
*   **Dependency:** Final sign-off on the audit trail logic.

### Phase 3: Launch & Onboarding (August 2026 $\to$ December 2026)
*   **Milestone 1: Production Launch (Target: 2026-08-15)**
    *   The system goes live for a select group of beta users.
*   **Milestone 2: Internal Alpha Release (Target: 2026-10-15)**
    *   Internal Stratos Systems staff stress-test the system with simulated high load.
*   **Milestone 3: First Paying Customer Onboarded (Target: 2026-12-15)**
    *   Full commercial rollout.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per team dynamic, formal minutes are not kept. The following are synthesized from Slack threads in the `#glacier-dev` channel.*

### Thread 1: The "Raw SQL" Debate (2023-11-12)
**Xiomara Moreau:** "I'm seeing a lot of `query_raw` calls in the payment logic. If we change the schema for the FedRAMP audit requirements, these are going to blow up. We need to move back to the ORM."
**Gael Santos:** "The ORM adds 40ms of overhead on the payment fetch. With the 200ms p95 goal, we can't afford that. I'll stick to raw SQL for the hot paths."
**Wyatt Park:** "Decision: Keep raw SQL for the `payments` and `audit_logs` tables only. Everything else must use the ORM. Xiomara, please create a 'Dangerous Query' registry so we know exactly what to check during migrations."

### Thread 2: 2FA Priority Shift (2023-12-05)
**Elara Stein:** "The current 2FA implementation doesn't support WebAuthn. If we want the government contracts, basic SMS/Email 2FA won't cut it. We need hardware keys."
**Wyatt Park:** "Agreed. Moving 2FA from 'Low' to 'Critical'. It's now a launch blocker. Gael, prioritize the `webauthn-rs` integration over the A/B testing framework."
**Gael Santos:** "Understood. Moving A/B testing to 'Blocked' until 2FA is stable."

### Thread 3: Release Train Enforcement (2024-01-20)
**Xiomara Moreau:** "We had three 'emergency' hotfixes last week. It's making the staging environment unstable. We can't keep doing this."
**Wyatt Park:** "New rule: Weekly Release Train. No exceptions. If you miss the Thursday 12:00 PM cutoff, your feature waits until next Friday. No hotfixes unless the site is literally down. Let's keep the ceremony low but the discipline high."
**Elara Stein:** "Supported. I'll update the QA checklist to reflect the Friday deployment window."

---

## 11. BUDGET BREAKDOWN

Project Glacier is bootstrapping with existing capacity. The "Budget" represents the internal allocation of resources and anticipated infrastructure costs.

| Category | Allocation/Cost | Description |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $420,000 (est.) | Combined salary load for Wyatt, Xiomara, and Elara for the project duration. |
| **Contractor (Gael)** | $85,000 | Fixed-fee contract for Rust backend development. |
| **Infrastructure (Cloudflare)** | $12,000 / yr | Workers, Pages, D1, and KV store (Projected). |
| **Infrastructure (PostgreSQL)** | $18,000 / yr | Managed HA instance via Supabase/AWS. |
| **Security/FedRAMP Audit** | $50,000 | Third-party certification and penetration testing. |
| **Tooling (Snyk/K6/etc.)** | $5,000 / yr | DevSecOps tool licenses. |
| **Contingency** | $20,000 | Buffer for unexpected infrastructure spikes or API costs. |
| **TOTAL (ESTIMATED)** | **$610,000** | Total internal "cost" of development. |

---

## 12. APPENDICES

### Appendix A: Performance Benchmarking Strategy
To ensure the **p95 < 200ms** metric, the team will implement the following:
1.  **Synthetic Monitoring:** Cloudflare Observatory will be used to track global latency.
2.  **Cold Start Mitigation:** Rust Wasm modules must be kept under 1MB to ensure cold starts do not exceed 50ms.
3.  **SQLite Optimization:** Indices must be created on `student_id` and `payment_id` within the edge D1 database to ensure $O(1)$ lookup times for active sessions.

### Appendix B: FedRAMP Compliance Checklist
The following technical controls must be verified by Elara Stein before the August 2026 launch:
*   **AC-2 (Account Management):** Automatic lockout after 5 failed 2FA attempts.
*   **AU-2 (Event Logging):** Tamper-evident logs must capture all administrative changes.
*   **IA-2 (Identification and Authentication):** Multi-factor authentication (MFA) utilizing hardware keys for all privileged accounts.
*   **SC-28 (Protection of Information at Rest):** All PostgreSQL data must be encrypted using AES-256.
*   **SC-8 (Transmission Confidentiality):** TLS 1.3 required for all data in transit.