# PROJECT SPECIFICATION: PROJECT FATHOM
**Version:** 1.0.4  
**Status:** Draft/Active  
**Project Lead:** Gia Gupta (CTO)  
**Company:** Ridgeline Platforms  
**Date:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

Project Fathom represents a critical strategic pivot for Ridgeline Platforms. For fifteen years, the company’s core operations—powering thousands of agricultural technology endpoints across North America—have relied on a legacy monolithic system. While this system facilitated initial growth, it has become a liability. The codebase is characterized by extreme fragility, lack of modularity, and a mounting "technical debt" crisis, most notably evidenced by a 3,000-line "God class" that manages the critical intersection of authentication, logging, and email dispatch. This monolithic architecture creates a "single point of failure" risk that threatens the operational stability of our entire client base.

The business justification for Fathom is twofold: risk mitigation and scalable growth. The legacy system cannot support modern multi-tenancy requirements, nor can it scale to meet the demands of the next decade of AgTech innovation. Any outage in the legacy system results in an immediate cessation of data flow for our farmers, leading to potential crop management failures and significant contractual penalties. Therefore, Project Fathom is tasked with the migration of these legacy services into a modern API gateway and microservices architecture with a **zero-downtime tolerance policy**.

The ROI projection for this $3M investment is aggressive but attainable. By moving to a cloud-native, TypeScript/Next.js stack on Vercel, we expect a 40% reduction in infrastructure overhead and a 60% increase in developer velocity. More importantly, the introduction of a customer-facing API and a robust sandbox environment will allow Ridgeline Platforms to transition from a closed-loop service to a platform ecosystem. We project $500,000 in new revenue within the first 12 months post-launch, driven by new API-tier subscription models. Furthermore, the shift to a HIPAA-compliant, encrypted infrastructure will open new markets in agricultural bio-security and health-integrated farming.

The project is a high-visibility executive priority. Failure to migrate without downtime would not only result in financial loss but would cause irreparable damage to the brand's reputation in the agricultural community, where trust and reliability are the primary currencies.

---

## 2. TECHNICAL ARCHITECTURE

Project Fathom utilizes a modern, distributed architecture designed for extreme reliability and strict data isolation. The core of the system is built using **TypeScript**, leveraging **Next.js** for the frontend and API routes, **Prisma** as the ORM, and **PostgreSQL** for relational data storage.

### 2.1 Architectural Pattern: CQRS and Event Sourcing
To meet the audit-critical requirements of AgTech (where tracking the provenance of data is legally required), Fathom implements **Command Query Responsibility Segregation (CQRS)**. 

- **Command Side:** Handles all state-changing operations. Every change is recorded as an immutable event in an Event Store.
- **Query Side:** Optimized read-models are maintained in PostgreSQL, updated asynchronously via event handlers. This ensures that the "Audit Log" is not just a table, but the actual source of truth.

### 2.2 Infrastructure Stack
- **Framework:** Next.js 14 (App Router)
- **Database:** PostgreSQL 15 (Managed via Vercel Postgres/Neon)
- **ORM:** Prisma 5.0+
- **Deployment:** Vercel (Continuous Deployment Pipeline)
- **Security:** AES-256 encryption for data at rest; TLS 1.3 for data in transit.

### 2.3 ASCII Architecture Diagram
```text
[ Client Applications ]  <--> [ Vercel Edge Network / CDN ]
                                      |
                                      v
                          [ Fathom API Gateway ]
                (Auth, Rate Limiting, Routing, Versioning)
                                      |
        _______________________________|_______________________________
       |                              |                               |
 [ Tenant Service ]          [ Billing Service ]           [ File/Media Service ]
 (Multi-tenant Isolation)    (Stripe/Subscription)         (Virus Scan -> S3/CDN)
       |                              |                               |
       v                              v                               v
 [ Command Bus ] ------------> [ Event Store ] <------------ [ Query Projections ]
 (Write Logic)                 (Immutable Log)                (Read-optimized DB)
       |                              |                               |
       └------------------------------>-------------------------------┘
                                      |
                          [ PostgreSQL Cluster ]
                          (HIPAA Compliant Storage)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Critical)
**Status:** In Design | **Launch Blocker:** Yes

The core requirement for Fathom is the ability to serve multiple agricultural firms on shared infrastructure while ensuring that no tenant can ever access another tenant's data. Given the sensitivity of crop yield data, this is a non-negotiable security requirement.

**Technical Implementation:**
Fathom will implement a "Row-Level Security" (RLS) approach combined with a "Tenant ID" discriminator on every table. Every request hitting the API Gateway must be accompanied by a verified `tenant_id` extracted from the JWT (JSON Web Token). 

The Prisma middleware will be configured to automatically inject a `WHERE tenant_id = X` clause into every query. To prevent "leaky" queries, a custom PostgreSQL schema will be implemented where the application user has limited permissions, and a security policy enforces the isolation at the database engine level.

**Key Requirements:**
- Hard isolation: A query for `User` must never return a user from another `tenant_id`.
- Shared Infrastructure: All tenants reside in the same PostgreSQL cluster to minimize cost and management overhead.
- Dynamic Routing: The API gateway must resolve the tenant based on the subdomain (e.g., `firm-a.fathom.ag`) or a custom header.

### 3.2 Automated Billing and Subscription Management (Priority: Critical)
**Status:** Complete | **Launch Blocker:** Yes

This system manages the financial lifecycle of a client, from onboarding to renewal. It replaces the manual invoicing process of the legacy system.

**Technical Implementation:**
Integration with Stripe Billing. The system utilizes a webhook-driven architecture where Stripe notifies the Fathom `BillingService` of payment success or failure. 

**Workflow:**
1. **Subscription Creation:** User selects a tier (Basic, Pro, Enterprise).
2. **Payment Processing:** Secure redirect to Stripe Checkout.
3. **Entitlement Update:** Upon `checkout.session.completed`, the `Subscription` table in PostgreSQL is updated, and a `Tenant` flag is set to `active`.
4. **Dunning:** Automated email triggers via the legacy-replacement email service if a payment fails.

**Completed Deliverables:**
- Subscription logic for 3 tiers.
- Integration with Stripe Webhooks.
- Automated PDF invoice generation.

### 3.3 File Upload with Virus Scanning and CDN Distribution (Priority: Critical)
**Status:** In Progress | **Launch Blocker:** Yes

Farmers frequently upload high-resolution satellite imagery and soil reports. These files must be scanned for malware before being stored and then distributed globally for low-latency access.

**Technical Implementation:**
1. **Upload:** Files are uploaded via a signed URL to an S3 "Quarantine" bucket.
2. **Scanning:** An AWS Lambda trigger initiates a ClamAV scan on every uploaded object.
3. **Promotion:** If the scan is clean, the file is moved from the `quarantine` bucket to the `production` bucket. If infected, it is deleted and a security alert is logged.
4. **Distribution:** CloudFront CDN is layered over the production bucket with signed cookies for access control.

**Key Requirements:**
- Maximum file size: 500MB per upload.
- Real-time scanning: Files must be scanned in < 30 seconds.
- CDN Caching: 24-hour TTL for public-facing agricultural reports.

### 3.4 Customer-Facing API with Versioning and Sandbox (Priority: High)
**Status:** Blocked | **Launch Blocker:** No

To enable the "Platform" strategy, Fathom must provide an API that external partners can integrate with. This requires a stable versioning system and a safe "Sandbox" environment where developers can test without affecting production data.

**Technical Implementation:**
- **Versioning:** URI-based versioning (e.g., `/v1/assets`, `/v2/assets`). The Gateway will route requests based on the version prefix.
- **Sandbox:** A separate PostgreSQL instance mirroring the production schema but containing synthetic data. API keys issued for the sandbox will be restricted to the `sandbox.fathom.ag` endpoint.
- **Rate Limiting:** Implementation of a token bucket algorithm to prevent API abuse.

**Current Blocker:** The "God class" in the legacy system handles the current API key logic, and until that is decoupled, the new API Gateway cannot safely migrate the keys.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support (Priority: Critical)
**Status:** In Design | **Launch Blocker:** Yes

Due to the HIPAA compliance requirements and the criticality of agricultural data, standard password-based auth is insufficient.

**Technical Implementation:**
- **TOTP:** Support for Google Authenticator/Authy using the `speakeasy` library.
- **WebAuthn/FIDO2:** Implementation of hardware key support (YubiKey) for high-privilege administrative accounts.
- **Recovery:** Generation of 10 one-time use backup codes stored using bcrypt hashing.

**User Flow:**
1. User enters username/password.
2. System checks if 2FA is enabled.
3. User is prompted for a 6-digit code or a hardware key touch.
4. Upon verification, the session JWT is issued.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer <JWT>` token in the Authorization header. All responses are in JSON.

### 4.1 Authentication & Users
**`POST /api/v1/auth/login`**
- **Request:** `{ "email": "user@farm.com", "password": "password123" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_at": "2023-10-25T00:00:00Z" }`

**`POST /api/v1/auth/2fa/verify`**
- **Request:** `{ "code": "123456", "deviceId": "hw-key-99" }`
- **Response:** `200 OK { "session_id": "sess_abc123" }`

### 4.2 Tenant Management
**`GET /api/v1/tenant/profile`**
- **Request:** No body.
- **Response:** `200 OK { "tenant_id": "t_01", "name": "Green Valley Farms", "plan": "Enterprise" }`

**`PATCH /api/v1/tenant/settings`**
- **Request:** `{ "notifications_enabled": true, "timezone": "America/Central" }`
- **Response:** `200 OK { "status": "updated" }`

### 4.3 Billing & Subscriptions
**`GET /api/v1/billing/subscription`**
- **Request:** No body.
- **Response:** `200 OK { "plan": "Pro", "next_billing_date": "2024-01-15", "status": "active" }`

**`POST /api/v1/billing/upgrade`**
- **Request:** `{ "new_plan_id": "plan_enterprise_01" }`
- **Response:** `201 Created { "checkout_url": "https://stripe.com/..." }`

### 4.4 File Management
**`POST /api/v1/files/upload-url`**
- **Request:** `{ "filename": "soil_report.pdf", "contentType": "application/pdf" }`
- **Response:** `200 OK { "upload_url": "https://s3.amazon.com/...", "file_id": "f_987" }`

**`GET /api/v1/files/download/{file_id}`**
- **Request:** Path parameter `file_id`.
- **Response:** `302 Redirect { "location": "https://cdn.fathom.ag/files/f_987" }`

---

## 5. DATABASE SCHEMA

The database uses a normalized relational structure. All tables include `created_at`, `updated_at`, and `deleted_at` (for soft deletes).

### 5.1 Table Definitions

1. **`Tenants`**
   - `id` (UUID, PK)
   - `name` (VARCHAR)
   - `slug` (VARCHAR, Unique) - Used for subdomains.
   - `plan_id` (FK -> Plans)
   - `status` (ENUM: active, suspended, trialing)

2. **`Users`**
   - `id` (UUID, PK)
   - `tenant_id` (FK -> Tenants)
   - `email` (VARCHAR, Unique)
   - `password_hash` (VARCHAR)
   - `mfa_secret` (VARCHAR, Encrypted)
   - `role` (ENUM: admin, editor, viewer)

3. **`Plans`**
   - `id` (UUID, PK)
   - `name` (VARCHAR)
   - `monthly_price` (DECIMAL)
   - `storage_limit_gb` (INT)
   - `api_rate_limit` (INT)

4. **`Subscriptions`**
   - `id` (UUID, PK)
   - `tenant_id` (FK -> Tenants)
   - `stripe_subscription_id` (VARCHAR)
   - `current_period_end` (TIMESTAMP)
   - `cancel_at_period_end` (BOOLEAN)

5. **`Files`**
   - `id` (UUID, PK)
   - `tenant_id` (FK -> Tenants)
   - `user_id` (FK -> Users)
   - `s3_key` (VARCHAR)
   - `filename` (VARCHAR)
   - `virus_scan_status` (ENUM: pending, clean, infected)
   - `size_bytes` (BIGINT)

6. **`AuditEvents`** (The Event Store)
   - `id` (BIGINT, PK)
   - `tenant_id` (FK -> Tenants)
   - `entity_type` (VARCHAR) - e.g., "User", "File"
   - `entity_id` (UUID)
   - `action` (VARCHAR) - e.g., "UPDATE_PLAN"
   - `payload` (JSONB) - The state change
   - `timestamp` (TIMESTAMP)

7. **`ApiKeys`**
   - `id` (UUID, PK)
   - `tenant_id` (FK -> Tenants)
   - `key_hash` (VARCHAR)
   - `label` (VARCHAR)
   - `last_used_at` (TIMESTAMP)
   - `expires_at` (TIMESTAMP)

8. **`HardwareKeys`**
   - `id` (UUID, PK)
   - `user_id` (FK -> Users)
   - `public_key` (TEXT)
   - `credential_id` (VARCHAR)

9. **`BillingInvoices`**
   - `id` (UUID, PK)
   - `tenant_id` (FK -> Tenants)
   - `amount` (DECIMAL)
   - `stripe_invoice_id` (VARCHAR)
   - `paid_status` (BOOLEAN)

10. **`SessionLogs`**
    - `id` (UUID, PK)
    - `user_id` (FK -> Users)
    - `ip_address` (INET)
    - `user_agent` (TEXT)
    - `login_time` (TIMESTAMP)

### 5.2 Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many.
- **Tenants $\rightarrow$ Subscriptions:** One-to-One.
- **Users $\rightarrow$ HardwareKeys:** One-to-Many.
- **Tenants $\rightarrow$ AuditEvents:** One-to-Many.
- **Files $\rightarrow$ Users:** Many-to-One.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

Project Fathom utilizes a **Continuous Deployment (CD)** model. Every Pull Request (PR) merged into the `main` branch is automatically deployed to production.

### 6.1 Environment Strategy

#### Development (`dev`)
- **Purpose:** Individual feature development and local testing.
- **Database:** Local Dockerized PostgreSQL.
- **Deployment:** Vercel Preview Deployments.
- **Trigger:** Every push to a feature branch.

#### Staging (`staging`)
- **Purpose:** Integration testing and QA. A mirror of production.
- **Database:** Staging PostgreSQL cluster (anonymized production snapshot).
- **Deployment:** Merges to `develop` branch.
- **Trigger:** Automatic merge of approved PRs from `dev`.

#### Production (`prod`)
- **Purpose:** Live client traffic.
- **Database:** High-availability PostgreSQL cluster with automated backups.
- **Deployment:** Merges to `main` branch.
- **Trigger:** Merges from `staging` after a manual "green light" from the QA lead.

### 6.2 The Zero-Downtime Migration Path
To migrate from the 15-year-old legacy system without downtime, we employ the **Strangler Fig Pattern**:
1. **Proxy Layer:** The new API Gateway is placed in front of the legacy system.
2. **Incremental Routing:** Specific endpoints (e.g., `/billing`) are routed to Fathom services, while others remain routed to the legacy monolith.
3. **Data Sync:** A background worker synchronizes data from the legacy database to PostgreSQL in real-time.
4. **Final Cutover:** Once all endpoints are migrated and verified, the legacy system is decommissioned.

---

## 7. TESTING STRATEGY

Given the $3M investment and high visibility, a "fail-fast" testing approach is implemented.

### 7.1 Unit Testing
- **Tool:** Jest
- **Scope:** Every business logic function must have $>90\%$ coverage.
- **Focus:** Validation logic, price calculations, and permission checks.
- **CI Integration:** All unit tests must pass before a PR can be merged.

### 7.2 Integration Testing
- **Tool:** Supertest + Testcontainers
- **Scope:** Testing the interaction between services and the database.
- **Focus:** Ensuring the RLS (Row Level Security) policies actually prevent cross-tenant data access.
- **Method:** Spin up a temporary PostgreSQL container, seed it with two tenants, and attempt to query Tenant B's data using Tenant A's token.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright
- **Scope:** Critical user paths (The "Golden Paths").
- **Key Scenarios:**
    - User registration $\rightarrow$ Subscription $\rightarrow$ File Upload.
    - Login $\rightarrow$ 2FA Challenge $\rightarrow$ Dashboard Access.
    - Admin $\rightarrow$ Tenant Suspension $\rightarrow$ User Access Denied.

### 7.4 Security Testing
- **Tool:** Snyk / OWASP ZAP
- **Scope:** Dependency scanning and penetration testing.
- **Focus:** Checking for SQL injection in the Prisma layer and ensuring HIPAA-compliant encryption of PII (Personally Identifiable Information).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | High | Hire a specialized contractor immediately to perform knowledge transfer and reduce the "bus factor." |
| R-02 | Stakeholder scope creep ('small' features) | High | Medium | Strict Change Request process. Any feature not in the original spec must be traded for an existing feature or deferred to v2.0. |
| R-03 | Legacy "God Class" instability during migration | Medium | Critical | Prioritize the decoupling of the God class into three distinct services: `AuthService`, `LoggingService`, and `EmailService`. |
| R-04 | Data loss during migration from legacy DB | Low | Critical | Use double-writing (writing to both legacy and new DB) for 30 days before cutting over read-access. |
| R-05 | HIPAA compliance audit failure | Low | High | Bi-weekly internal audits by Priya Fischer and quarterly third-party reviews. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project stoppage / Legal liability.
- **High:** Significant delay / Budget overrun.
- **Medium:** Minor delay / Workaround available.
- **Low:** Negligible impact.

---

## 9. TIMELINE

The project is divided into four distinct phases. All dates are targets.

### Phase 1: Foundation & Decoupling (Now - Jan 2026)
- **Dependencies:** Hiring contractor for Architect risk.
- **Focus:** Setting up Vercel/Postgres, building the API Gateway, and breaking the 3,000-line God class.
- **Milestone:** God class fully decomposed into microservices.

### Phase 2: Core Feature Implementation (Feb 2026 - June 2026)
- **Dependencies:** Foundation completion.
- **Focus:** Implementing Multi-tenant isolation, 2FA, and File Scanning.
- **Milestone:** "Feature Complete" for all launch-blockers.

### Phase 3: Beta & Migration (July 2026 - Sept 2026)
- **Dependencies:** Staging environment stability.
- **Focus:** Strangler Fig routing, data synchronization, and internal beta testing.
- **Milestone 1: Post-launch stability confirmed (2026-07-15)**
- **Milestone 2: Production Launch (2026-09-15)**

### Phase 4: Hardening & Compliance (Oct 2026 - Nov 2026)
- **Dependencies:** Production launch.
- **Focus:** Full security audit, performance tuning, and API Sandbox release.
- **Milestone 3: Security audit passed (2026-11-15)**

---

## 10. MEETING NOTES

*Note: All meetings were recorded via Zoom. Transcripts are stored in the project archive, although historical data shows that these recordings are rarely rewatched by the team.*

### Meeting 1: Architecture Alignment (Oct 12, 2023)
**Attendees:** Gia Gupta, Noor Liu, Priya Fischer, Celine Stein
- **Discussion:** Noor raised concerns about the performance of CQRS for simple CRUD operations. Gia argued that for the audit-critical domain (e.g., changing soil nitrate data), the event log is non-negotiable.
- **Decision:** Use CQRS only for "Audit-Critical" domains. Standard user profile updates will use traditional Prisma CRUD.
- **Action Item:** Noor to draft the event schema for `AuditEvents` table.

### Meeting 2: The "God Class" Crisis (Oct 19, 2023)
**Attendees:** Gia Gupta, Noor Liu, Celine Stein
- **Discussion:** Celine attempted to refactor the `AuthManager` class and found that a change to the email formatting logic broke the login flow. The team discussed the "intertwined" nature of the 3,000-line class.
- **Decision:** We will not refactor the God class in place. We will build a "Sidecar" service that mirrors its functionality, then flip the switch at the Gateway level.
- **Action Item:** Gia to allocate budget for the contractor to assist in this decoupling.

### Meeting 3: Security Review & HIPAA (Oct 26, 2023)
**Attendees:** Gia Gupta, Priya Fischer
- **Discussion:** Priya reviewed the current Vercel deployment. She noted that while Vercel is secure, we need a more explicit "Data Residency" guarantee for certain EU-based AgTech clients.
- **Decision:** Implement region-specific PostgreSQL clusters for EU tenants.
- **Action Item:** Priya to update the technical specification for multi-tenant isolation to include regional routing.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$3,000,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 20+ engineers, QA, and Project Managers over 3 years. |
| **Infrastructure** | 15% | $450,000 | Vercel Enterprise, AWS S3, PostgreSQL Managed Services. |
| **Specialized Tools** | 5% | $150,000 | Snyk, ClamAV Enterprise, Stripe Fees, Security Audit tools. |
| **Contractor** | 10% | $300,000 | Specialized Architect to mitigate "Bus Factor" risk. |
| **Contingency** | 5% | $150,000 | Emergency buffer for scope creep or infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: God Class Decomposition Map
The legacy `LegacySystemManager.ts` (3,000 lines) will be split into the following services:
1. **`IdentityService`**: Handles password hashing, JWT issuance, and session management.
2. **`NotificationService`**: Handles SMTP integration, email templating, and SMS alerts.
3. **`TelemetryService`**: Handles application logging, error reporting, and audit trails.

### Appendix B: Data Encryption Standard
All PII (Personally Identifiable Information) and sensitive Ag-data must follow these standards:
- **Encryption Algorithm:** AES-256-GCM.
- **Key Management:** AWS KMS (Key Management Service) with rotation every 90 days.
- **Salt:** All password hashes must use a minimum 16-byte random salt with bcrypt (cost factor 12).
- **Transit:** Enforce HSTS (HTTP Strict Transport Security) on all endpoints.