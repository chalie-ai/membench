# PROJECT SPECIFICATION: PROJECT EMBER
**Document Version:** 1.0.4  
**Status:** Active / Draft for Review  
**Classification:** Internal / Proprietary – Stormfront Consulting  
**Last Updated:** October 26, 2023  
**Owner:** Astrid Moreau (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ember is a strategic platform modernization initiative undertaken by Stormfront Consulting to transition its core internal enterprise operations within the renewable energy sector from a legacy monolithic architecture to a scalable microservices-oriented ecosystem. The primary driver for this transition is the obsolescence of the current "Stormfront Core" system, which has become a bottleneck for operational efficiency, unable to handle the surge in data volume associated with the company's expansion into offshore wind and high-capacity solar arrays.

The goal of Ember is not a "big bang" migration but a disciplined, 18-month phased transition. The project aims to dismantle the existing monolith by establishing a "clean monolith" transitional state—where module boundaries are strictly enforced via internal APIs—before incrementally carving out services into independent AWS ECS containers.

### 1.2 Business Justification
Stormfront Consulting operates in a highly regulated environment where data integrity and security are paramount. The legacy system currently suffers from excessive technical debt, specifically regarding its database layer, where performance hacks (raw SQL) have made updates precarious. The business risk of remaining on the legacy system includes potential downtime during regulatory audits and an inability to scale to new regional markets.

Furthermore, the current cost of transaction processing is unsustainable. Due to inefficient resource allocation and outdated licensing models, the operational cost per transaction is roughly 35% higher than industry benchmarks. By leveraging a modern Python/Django stack on AWS, Ember will optimize resource utilization through auto-scaling and efficient caching strategies.

### 1.3 ROI Projection and Success Metrics
The Return on Investment (ROI) for Project Ember is calculated based on three primary pillars: Operational Efficiency, Risk Mitigation, and Infrastructure Cost Reduction.

**Key Performance Indicators (KPIs):**
1.  **Cost Reduction:** The primary financial metric is a targeted **35% reduction in cost per transaction** compared to the legacy system. This will be achieved through the migration to AWS ECS and the implementation of Redis caching, reducing expensive database hits.
2.  **Security Posture:** Given that the system processes credit card data directly (PCI DSS Level 1), the success criterion is **zero critical security incidents** within the first 12 months of production.
3.  **System Stability:** A reduction in Mean Time to Recovery (MTTR) by 50% through the implementation of automated health checks and container orchestration.

**Financial Projection:**
Based on current transaction volumes of 1.2M events per month, a 35% cost reduction is projected to save Stormfront Consulting approximately $420,000 in operational overhead annually, offsetting the initial development costs within 14 months of full deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architectural Philosophy
Project Ember utilizes a "Modular Monolith" approach. To avoid the "distributed monolith" antipattern, the system is developed as a single Django project with strictly isolated apps (modules). Each module communicates with others via defined service layers rather than direct cross-app imports. This allows for a seamless transition to full microservices in the later stages of the 18-month roadmap.

### 2.2 The Tech Stack
*   **Language/Framework:** Python 3.11 / Django 4.2 LTS (Long Term Support)
*   **Primary Database:** PostgreSQL 15.3 (Managed via AWS RDS)
*   **Caching/Queue:** Redis 7.0 (Managed via AWS ElastiCache)
*   **Deployment:** AWS ECS (Fargate) for serverless container orchestration
*   **CI/CD:** GitHub Actions deploying to AWS ECR and ECS
*   **Security:** PCI DSS Level 1 Compliant environment with encrypted data-at-rest (AES-256) and TLS 1.3 in-transit.

### 2.3 ASCII Architecture Diagram
```text
[ User Browser / Mobile ] 
          |
          v
[ AWS Route 53 / ALB (Application Load Balancer) ]
          |
          +---------------------------------------+
          |                                       |
          v                                       v
[ AWS ECS Fargate Cluster ] <------> [ AWS ElastiCache (Redis) ]
|                                   |  - Session Management
|  +---------------------------+   |  - API Rate Limiting
|  |  Django Modular Monolith   |   |  - Notification Queue
|  |                           |   |
|  | [Auth Module] <----------+ |   |
|  | [Tenant Module] <-------+ |   |
|  | [File/CDN Module] <------+ |   |
|  | [Notify Module] <---------+ |   |
|  +---------------------------+   |
+-----------------------------------+
          |
          v
[ AWS RDS (PostgreSQL) ] <--- [ S3 Bucket (Encrypted) ]
- Master / Read Replicas       - File Storage (Virus Scanned)
- Schema per Tenant (Logic)    - Static Asset Distribution
```

### 2.4 Data Isolation Strategy
To meet the high-priority requirement for multi-tenant data isolation, Ember employs a **Shared Infrastructure, Discriminator Column** approach. Every table contains a `tenant_id` foreign key. A custom Django Middleware injects the current `tenant_id` into every query filter via a global manager, ensuring that data leakage between different energy firms (tenants) is architecturally impossible.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 SSO Integration (SAML and OIDC)
**Priority:** Low | **Status:** Complete
**Description:**
The system provides a unified authentication gateway allowing enterprise clients to use their own Identity Providers (IdP) via Security Assertion Markup Language (SAML 2.0) and OpenID Connect (OIDC).

**Technical Specifications:**
The implementation uses `django-allauth` and `python3-saml`. The system supports "Just-in-Time" (JIT) provisioning, where users are automatically created in the Ember database upon their first successful SSO login, provided they belong to a whitelisted domain.

**Workflow:**
1. User selects "Login with Enterprise SSO."
2. Ember redirects to the configured IdP (e.g., Okta, Azure AD).
3. IdP authenticates the user and sends a signed SAML assertion or OIDC token back to the `/auth/sso/callback` endpoint.
4. Ember validates the signature against the stored public key and maps the user's attributes (email, role, department) to the internal user profile.

**Compliance:**
To maintain PCI DSS Level 1, SSO tokens are never stored in plain text, and session cookies are flagged as `HttpOnly`, `Secure`, and `SameSite=Strict`.

### 3.2 Multi-Tenant Data Isolation
**Priority:** High | **Status:** Blocked
**Description:**
This feature ensures that data for different clients (Tenants) is logically isolated. While the infrastructure is shared (shared PostgreSQL instance), no tenant should ever be able to access, modify, or even see the existence of another tenant's data.

**Technical Specifications:**
The system implements a "Shared Schema" model. A `Tenant` model exists in the `core` app. All other models (e.g., `EnergyMetric`, `ClientInvoice`) inherit from a `TenantBaseModel` which includes a `tenant_id` field.

**The Blocking Issue:**
This feature is currently blocked by the discovery that the legacy data migration scripts are producing inconsistent `tenant_id` mappings. Until the data cleansing phase of the legacy monolith is complete, enabling this isolation layer would result in massive data loss for 20% of existing records.

**Required Logic:**
*   **Request Filtering:** A middleware layer intercepts every request, identifies the tenant via the subdomain (e.g., `client-a.ember.stormfront.com`), and sets a thread-local variable.
*   **Query Override:** The PostgreSQL manager is overridden to automatically append `WHERE tenant_id = current_tenant` to every SELECT, UPDATE, and DELETE query.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical | **Status:** Blocked (Launch Blocker)
**Description:**
Users must be able to upload large technical specifications and energy reports. Due to the sensitivity of the renewable energy infrastructure, every file must be scanned for malware before being committed to permanent storage.

**Technical Specifications:**
1.  **Ingest:** Files are uploaded to a "Quarantine" S3 bucket.
2.  **Scanning:** An AWS Lambda function is triggered on upload, which invokes a ClamAV (Clam antivirus) instance running in a separate container.
3.  **Disposition:** If the scan returns `CLEAN`, the file is moved to the "Production" S3 bucket and tagged with the `tenant_id`. If `INFECTED`, the file is deleted, and a security alert is logged.
4.  **Distribution:** Files are served via AWS CloudFront (CDN) using "Signed URLs" to ensure that only authenticated users with the correct permissions can access the files.

**The Blocking Issue:**
The feature is blocked due to the primary vendor for the virus scanning API announcing an End-of-Life (EOL) for their specific SDK, which is incompatible with Python 3.11. A replacement vendor must be vetted and approved by the security board.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical | **Status:** In Progress (Launch Blocker)
**Description:**
Given the PCI DSS Level 1 requirements and the criticality of the renewable energy grid data, password-based authentication is insufficient. Ember implements multi-factor authentication (MFA) with a preference for hardware-based keys.

**Technical Specifications:**
The system supports two tiers of 2FA:
*   **Tier 1 (TOTP):** Time-based One-Time Passwords (Google Authenticator, Authy).
*   **Tier 2 (WebAuthn/FIDO2):** Support for physical hardware keys (YubiKey, Google Titan).

**Implementation Detail:**
WebAuthn is implemented via the `pywebauthn` library. The server sends a challenge to the browser, the hardware key signs the challenge using a private key, and the server verifies the signature using the stored public key.

**Current State:**
TOTP is fully functional. Hardware key registration is currently in the "Beta" stage, with testing occurring on the staging environment. The final "Launch Blocker" status remains until the hardware key support is verified for all 6 core team members and the QA lead.

### 3.5 Notification System (Email, SMS, In-App, Push)
**Priority:** High | **Status:** Blocked
**Description:**
A centralized notification engine to alert users of system events, regulatory deadlines, and security warnings.

**Technical Specifications:**
The system uses a "Fan-out" architecture. When an event occurs (e.g., `InvoiceCreated`), a message is published to a Redis queue. A set of "Worker" services (Celery) consume these messages and determine the delivery channel based on user preferences.

**Delivery Channels:**
*   **Email:** Sent via AWS SES (Simple Email Service).
*   **SMS:** Sent via Twilio.
*   **In-App:** Real-time updates via Django Channels (WebSockets).
*   **Push:** Delivered via Firebase Cloud Messaging (FCM).

**The Blocking Issue:**
This feature is currently blocked by third-party API rate limits. During stress testing, the Twilio and SES sandboxes are triggering rate-limit exceptions, preventing the team from verifying the system's ability to handle bulk notifications for 10,000+ users.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer <JWT_TOKEN>` in the Authorization header.

### 4.1 Authentication & Users
**Endpoint:** `POST /auth/login`
*   **Description:** Authenticates user and returns JWT.
*   **Request:** `{"username": "astrid_m", "password": "..."}`
*   **Response:** `{"token": "eyJ...", "refresh": "...", "user_id": 101}`

**Endpoint:** `POST /auth/2fa/verify`
*   **Description:** Verifies 2FA token or WebAuthn signature.
*   **Request:** `{"code": "123456", "method": "totp"}`
*   **Response:** `{"status": "verified", "session_id": "..."}`

### 4.2 Tenant Management
**Endpoint:** `GET /tenants/profile`
*   **Description:** Retrieves current tenant settings.
*   **Request:** None (uses JWT context).
*   **Response:** `{"tenant_name": "SolarWind Ltd", "plan": "enterprise", "region": "EU-West-1"}`

**Endpoint:** `PATCH /tenants/settings`
*   **Description:** Updates tenant configuration.
*   **Request:** `{"update_logo": "base64_string", "contact_email": "admin@solarwind.com"}`
*   **Response:** `{"status": "updated", "timestamp": "2023-10-26T10:00:00Z"}`

### 4.3 File Management
**Endpoint:** `POST /files/upload`
*   **Description:** Uploads a file to the quarantine bucket.
*   **Request:** Multipart form-data (`file`, `category`).
*   **Response:** `{"file_id": "uuid-123", "status": "scanning", "eta": "30s"}`

**Endpoint:** `GET /files/download/{file_id}`
*   **Description:** Generates a signed CloudFront URL for a clean file.
*   **Request:** None.
*   **Response:** `{"url": "https://cdn.ember.com/signed-link-abc...", "expires": "3600s"}`

### 4.4 Notifications
**Endpoint:** `GET /notifications`
*   **Description:** Fetches unread notifications for the user.
*   **Request:** `{"limit": 20, "offset": 0}`
*   **Response:** `[{"id": 1, "message": "Invoice Overdue", "severity": "high", "read": false}]`

**Endpoint:** `POST /notifications/mark-read`
*   **Description:** Marks a specific notification as read.
*   **Request:** `{"notification_id": 1}`
*   **Response:** `{"status": "success"}`

---

## 5. DATABASE SCHEMA

The database uses PostgreSQL 15.3. Due to the "Clean Monolith" approach, tables are grouped by module, though they reside in the same database.

### 5.1 Core & Tenant Tables
1.  **`tenants`**:
    *   `id` (UUID, PK)
    *   `name` (VARCHAR 255)
    *   `domain` (VARCHAR 255, Unique)
    *   `created_at` (Timestamp)
    *   `is_active` (Boolean)
2.  **`users`**:
    *   `id` (UUID, PK)
    *   `tenant_id` (FK -> tenants.id)
    *   `email` (VARCHAR 255, Unique)
    *   `password_hash` (TEXT)
    *   `last_login` (Timestamp)
    *   `role_id` (FK -> roles.id)

### 5.2 Security & Auth Tables
3.  **`roles`**:
    *   `id` (INT, PK)
    *   `role_name` (VARCHAR 50) - e.g., 'Admin', 'Analyst'
    *   `permissions` (JSONB)
4.  **`two_factor_keys`**:
    *   `id` (UUID, PK)
    *   `user_id` (FK -> users.id)
    *   `secret_key` (TEXT, Encrypted)
    *   `method` (VARCHAR 20) - 'TOTP' or 'WEBAUTHN'
    *   `public_key` (TEXT) - For hardware keys

### 5.3 File & Content Tables
5.  **`files`**:
    *   `id` (UUID, PK)
    *   `tenant_id` (FK -> tenants.id)
    *   `owner_id` (FK -> users.id)
    *   `s3_key` (TEXT)
    *   `filename` (VARCHAR 255)
    *   `virus_scan_status` (ENUM: 'Pending', 'Clean', 'Infected')
    *   `upload_date` (Timestamp)
6.  **`file_versions`**:
    *   `id` (UUID, PK)
    *   `file_id` (FK -> files.id)
    *   `version_number` (INT)
    *   `s3_key` (TEXT)

### 5.4 Notification Tables
7.  **`notification_templates`**:
    *   `id` (INT, PK)
    *   `event_type` (VARCHAR 100)
    *   `subject_template` (TEXT)
    *   `body_template` (TEXT)
8.  **`notifications`**:
    *   `id` (UUID, PK)
    *   `user_id` (FK -> users.id)
    *   `tenant_id` (FK -> tenants.id)
    *   `channel` (VARCHAR 20) - 'Email', 'SMS', 'Push', 'InApp'
    *   `message` (TEXT)
    *   `is_read` (Boolean)
    *   `created_at` (Timestamp)

### 5.5 Business Logic Tables
9.  **`energy_metrics`**:
    *   `id` (BIGINT, PK)
    *   `tenant_id` (FK -> tenants.id)
    *   `metric_value` (DECIMAL)
    *   `unit` (VARCHAR 20)
    *   `timestamp` (Timestamp)
10. **`billing_transactions`**:
    *   `id` (UUID, PK)
    *   `tenant_id` (FK -> tenants.id)
    *   `amount` (DECIMAL)
    *   `card_token` (TEXT, PCI Compliant Token)
    *   `status` (VARCHAR 20)
    *   `processed_at` (Timestamp)

**Relationships:**
*   `tenants` is the root; almost every table has a `tenant_id` for isolation.
*   `users` belong to `tenants` (Many-to-One).
*   `two_factor_keys` belong to `users` (One-to-Many).
*   `files` are linked to `tenants` and `users` for ownership and access control.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ember utilizes three distinct environments to ensure stability and regulatory compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and initial integration.
*   **Infrastructure:** Shared ECS Cluster, small RDS instance (db.t3.micro).
*   **Deployment:** Automatic deployment on merge to `develop` branch.
*   **Data:** Anonymized seed data.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Pre-production testing, QA verification, and Regulatory Review.
*   **Infrastructure:** Mirror of Production (ECS Fargate, RDS db.m5.large).
*   **Deployment:** Triggered by tagged releases (e.g., `v1.2.0-rc1`).
*   **Data:** Scrubbed production snapshots.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live enterprise tool.
*   **Infrastructure:** High-availability multi-AZ deployment.
*   **Deployment:** Quarterly releases aligned with regulatory review cycles.
*   **Data:** Live, encrypted PCI DSS Level 1 data.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1.  **Linting/Testing:** Every PR triggers `flake8` and `pytest`.
2.  **Containerization:** On merge, a Docker image is built and pushed to AWS ECR (Elastic Container Registry).
3.  **Deployment:** ECS service is updated using a "Rolling Update" strategy to ensure zero downtime.

### 6.3 Scaling and Performance
*   **Horizontal Scaling:** ECS Fargate auto-scaling is configured based on CPU and Memory utilization (>70%).
*   **Caching:** Redis is used to store session data and frequently accessed tenant configuration, reducing RDS load.
*   **Database Optimization:** While 30% of queries currently use raw SQL for performance (Technical Debt), the target is to migrate these to optimized Django QuerySets using `select_related` and `prefetch_related`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tool:** `pytest` and `unittest.mock`.
*   **Scope:** Every single business logic function and utility method must have 100% coverage.
*   **Focus:** Testing the `TenantBaseModel` manager to ensure that `tenant_id` is always filtered correctly.

### 7.2 Integration Testing
*   **Tool:** `Django TestCase` with a dedicated PostgreSQL test database.
*   **Scope:** Testing the interaction between modules (e.g., does the `Auth` module correctly trigger a `Notification` on failed login?).
*   **Focus:** Verifying the flow of data through the Redis queue into the Celery workers.

### 7.3 End-to-End (E2E) Testing
*   **Tool:** Playwright / Selenium.
*   **Scope:** Critical user paths:
    *   SSO Login $\rightarrow$ Dashboard access.
    *   File Upload $\rightarrow$ Virus Scan $\rightarrow$ CDN Download.
    *   Hardware Key Registration $\rightarrow$ 2FA Challenge $\rightarrow$ Login.
*   **Focus:** Cross-browser compatibility and PCI DSS flow verification.

### 7.4 Security Testing (Penetration Testing)
*   **Frequency:** Quarterly.
*   **Scope:** Attempting "Tenant Leaks" (trying to access `Tenant B` data with `Tenant A` credentials).
*   **Focus:** Validating that raw SQL queries do not introduce SQL injection vulnerabilities.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key architect is leaving in 3 months | High | High | Create a detailed architectural fallback plan; accelerate knowledge transfer sessions with Astrid and Eben. |
| **R2** | Primary vendor EOL for virus scanning SDK | High | Critical | Escalate to the board as a blocker; evaluate alternative vendors (CrowdStrike, SentinelOne) immediately. |
| **R3** | Raw SQL technical debt causing migration failure | Medium | High | Implement a "SQL Audit" phase; gradually replace raw SQL with ORM using `QuerySet.extra()` or `RawSQL` objects for safer migrations. |
| **R4** | Third-party API rate limits (Twilio/SES) | High | Medium | Request production quotas from vendors; implement an internal "Rate Limit Buffer" using Redis to queue messages. |
| **R5** | PCI DSS Compliance failure during audit | Low | Critical | Conduct monthly internal audits; use automated compliance scanning tools. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate launch blocker, potential legal/financial penalty.
*   **High:** Significant delay in milestone achievement.
*   **Medium:** Affects developer velocity, manageable through workarounds.
*   **Low:** Minimal impact on delivery.

---

## 9. TIMELINE AND MILESTONES

Project Ember follows a phased release cycle. Because of the regulatory nature of the energy industry, releases are quarterly.

### 9.1 Phase 1: Foundation & Core Isolation (Current - March 2025)
*   **Objective:** Establish the modular monolith and solve the tenant isolation blocker.
*   **Dependency:** Data cleansing of legacy records.
*   **Key Deliverable:** Working Multi-tenant logic.

### 9.2 Phase 2: Security Hardening (March 2025 - June 2025)
*   **Objective:** Finalize 2FA and File Scanning.
*   **Dependency:** Vendor replacement for virus scanning SDK.
*   **Key Deliverable:** PCI DSS Level 1 certification readiness.

### 9.3 Phase 3: Feature Completion & Alpha (June 2025 - September 2025)
*   **Objective:** Implement Notification system and finalize internal alpha.
*   **Dependency:** Resolution of API rate limits.
*   **Key Deliverable:** Internal Alpha Release.

### 9.4 Milestone Tracking
| Milestone | Target Date | Status | Criteria for Success |
| :--- | :--- | :--- | :--- |
| **Internal Alpha Release** | 2025-09-15 | Pending | All 5 features integrated; basic UX flow validated by internal staff. |
| **MVP Feature-Complete** | 2025-07-15 | Pending | All "Critical" and "High" priority features passed QA. |
| **Post-Launch Stability** | 2025-05-15 | Pending | System running in Prod for 30 days with no critical regressions. |

*(Note: Milestone dates are sequenced by target completion, reflecting the iterative nature of the modular-to-microservice transition.)*

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*As per team policy, formal meeting minutes are not kept. All decisions are captured in Slack threads. Below are curated summaries of key decision threads.*

### Thread: #ember-dev-sync (2023-10-12)
**Topic:** The Raw SQL Dilemma
**Astrid:** "We have about 30% of the legacy queries using raw SQL for performance. If we run a standard Django migration on the `energy_metrics` table, we risk breaking the reports."
**Eben:** "Can we just keep them? The performance gain is 4x over the ORM for those specific joins."
**Astrid:** "We can't. It's a security risk and makes the schema rigid. Decision: We'll keep them for now but mark every raw query with a `# TODO: MIGRATE_TO_ORM` tag. We will not allow new raw SQL in the Ember codebase."
**Decision:** Raw SQL is permitted for legacy migration only; new code must use the ORM.

### Thread: #ember-product (2023-10-18)
**Topic:** 2FA Hardware Keys vs. SMS
**Nyla:** "Users are complaining that SMS 2FA is annoying. Can we just do email?"
**Astrid:** "No. PCI DSS Level 1 and the energy sector's security requirements essentially mandate strong MFA. SMS is too vulnerable to SIM swapping."
**Nyla:** "What about YubiKeys?"
**Astrid:** "Yes. We'll implement WebAuthn. It's more secure and actually faster for the user."
**Decision:** Hardware key support is a "Critical" launch blocker.

### Thread: #ember-ops (2023-10-22)
**Topic:** Third-Party Rate Limiting
**Eben:** "We're hitting the Twilio rate limits during the load tests for the notification system. The whole worker queue is backing up."
**Astrid:** "Are we using the sandbox account?"
**Eben:** "Yeah, that's the problem. The sandbox is throttled."
**Astrid:** "Contact the account manager. We need the production quota increased now, or the notification system is effectively blocked."
**Decision:** Project status for Notification System updated to "Blocked" until production quotas are secured.

---

## 11. BUDGET BREAKDOWN

Budget is released in tranches based on the achievement of milestones. The total budget is variable, but the current allocation for the 18-month window is broken down as follows:

### 11.1 Personnel (Monthly)
*   **Tech Lead (Astrid):** $14,000 / mo
*   **DevOps Engineer (Eben):** $12,000 / mo
*   **Product Designer (Nyla):** $11,000 / mo
*   **Intern (Fleur):** $4,000 / mo
*   **Dedicated QA (Contractor):** $9,000 / mo
*   **Total Personnel Monthly:** $50,000 $\rightarrow$ **Total 18-Month Est: $900,000**

### 11.2 Infrastructure (AWS Monthly)
*   **ECS Fargate & ALB:** $1,200 / mo
*   **RDS PostgreSQL (Multi-AZ):** $800 / mo
*   **ElastiCache Redis:** $400 / mo
*   **S3 & CloudFront:** $300 / mo
*   **Total Infrastructure Monthly:** $2,700 $\rightarrow$ **Total 18-Month Est: $48,600**

### 11.3 Tools & Licensing (Annual)
*   **GitHub Enterprise:** $5,000 / yr
*   **Twilio/SES Credits:** $12,000 / yr
*   **Virus Scanning Vendor:** $25,000 / yr
*   **PCI DSS Compliance Audit:** $40,000 / yr
*   **Total Tooling Est:** $82,000 / yr $\rightarrow$ **Total 18-Month Est: $123,000**

### 11.4 Contingency Fund
*   **Buffer:** $150,000 (Reserved for emergency architectural pivots or vendor replacements).

**Grand Total Projected Budget:** **$1,221,600**

---

## 12. APPENDICES

### Appendix A: Database Migration Strategy
Because 30% of the system relies on raw SQL, the migration strategy involves a "Shadow Write" phase. 
1.  **Phase 1:** New schema is deployed alongside the old schema.
2.  **Phase 2:** The application writes to both the old (legacy) and new (Ember) tables.
3.  **Phase 3:** A background process compares the data for consistency.
4.  **Phase 4:** Once consistency is verified for 99.9% of records, the raw SQL queries are deprecated and the legacy tables are dropped.

### Appendix B: PCI DSS Level 1 Compliance Checklist
To maintain compliance, the following technical controls are implemented in Ember:
*   **Data Encryption:** All credit card tokens are stored using AES-256 encryption with keys managed by AWS KMS (Key Management Service).
*   **Network Isolation:** The production database resides in a private subnet with no public internet access; all access is via the ECS service.
*   **Audit Logging:** Every access to sensitive data is logged to AWS CloudWatch with an immutable log stream.
*   **Access Control:** Implement "Principle of Least Privilege" (PoLP). Only the Tech Lead (Astrid) has access to the production environment's root keys.