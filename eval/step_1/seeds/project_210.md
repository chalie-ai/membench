Due to the extreme length requirements (6,000–8,000 words), this document is structured as a Comprehensive Technical Specification. It is designed to serve as the "Single Source of Truth" (SSoT) for the engineering team at Pivot North Engineering.

***

# PROJECT SPECIFICATION: JUNIPER
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Owner:** Camila Liu (Engineering Manager)  
**Company:** Pivot North Engineering  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Juniper" is a strategic cost-reduction and operational efficiency initiative commissioned by Pivot North Engineering. Currently, the organization maintains four redundant internal tools—originally developed by disparate teams across the education sector vertical—to handle student data management, course scheduling, grading analytics, and administrative billing. This fragmentation has led to "data silos," inconsistent user experiences, and an unsustainable overhead in maintenance and licensing costs.

The primary business driver for Juniper is the consolidation of these four legacy tools into a single, unified SaaS platform. By migrating to a modernized stack (Rust/React/Cloudflare Workers), Pivot North Engineering aims to eliminate the redundant compute costs of four separate legacy environments and reduce the operational burden on the DevOps team. 

### 1.2 ROI Projection and Financial Goals
The project is backed by a total budget of $1.5M. While the primary driver is cost reduction (OpEx), Juniper is designed to be a revenue generator through the introduction of a tiered subscription model for external educational partners.

**Financial Success Metrics:**
- **New Revenue:** Target of $500,000 in new attributed revenue within 12 months of the 2026-09-15 sign-off.
- **Operational Savings:** Estimated reduction of $120,000/year in legacy server maintenance and license fees.
- **Infrastructure Efficiency:** By utilizing SQLite at the edge via Cloudflare Workers, the project intends to reduce latency by 60% compared to the current centralized legacy databases, directly impacting user retention and productivity.

### 1.3 Project Scope
Juniper will provide a centralized hub for educational administration. The scope includes the migration of all existing data from legacy tools, the implementation of a robust Role-Based Access Control (RBAC) system, and the integration of automated billing. The platform will prioritize high availability and security, with a specific focus on a "zero critical security incident" mandate for the first year of operation.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Juniper utilizes a cutting-edge, high-performance stack designed for global distribution and minimal latency.

- **Backend:** Rust (utilizing the Axum framework). Rust was selected for its memory safety and performance, ensuring that the platform can handle the 10x capacity requirement without increasing the infrastructure budget.
- **Frontend:** React 18+ with TypeScript.
- **Edge Layer:** Cloudflare Workers. This allows the application logic to run closer to the user.
- **Database:** SQLite (deployed via Cloudflare D1/Edge). This enables "edge-side" data persistence, reducing the need for expensive centralized database clusters.
- **Architecture Pattern:** Micro-frontend (MFE). Each core module (Billing, Admin, Analytics, User Mgmt) is owned by a specific sub-team, allowing independent deployment cycles.

### 2.2 Architectural Diagram (ASCII Representation)

```text
[ USER BROWSER ] 
       |
       v
[ CLOUDFLARE GLOBAL NETWORK ]
       |
       +---> [ Edge Router / Load Balancer ]
       |             |
       |             +---> [ MFE: User Auth (React) ] <---> [ Rust Worker A ] <---> [ SQLite Edge DB ]
       |             |
       |             +---> [ MFE: Billing (React) ]  <---> [ Rust Worker B ] <---> [ SQLite Edge DB ]
       |             |
       |             +---> [ MFE: Admin Tool (React) ] <---> [ Rust Worker C ] <---> [ SQLite Edge DB ]
       |             |
       |             +---> [ MFE: Analytics (React) ] <---> [ Rust Worker D ] <---> [ SQLite Edge DB ]
       |
       v
[ SHARED SERVICES LAYER ]
       |
       +---> [ Audit Trail Logging (Tamper-Evident Store) ]
       |
       +---> [ Background Sync Service (Offline-First) ]
       |
       +---> [ Stripe API / Billing Gateway ]
```

### 2.3 Deployment Pipeline
Juniper employs a Continuous Deployment (CD) philosophy.
- **Trunk-Based Development:** All developers merge into the `main` branch.
- **Automatic Promotion:** Every merged Pull Request (PR) that passes the automated test suite (unit, integration, and e2e) is automatically deployed to production via Cloudflare Wrangler.
- **Version Control:** Git (GitHub).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Review

The authentication system serves as the gateway to Juniper. Given the education industry's sensitivity, the RBAC system must be granular.

**Functional Requirements:**
- **Identity Management:** Users must be able to sign up, sign in, and recover passwords.
- **Role Definition:** Three primary roles: `SuperAdmin` (Pivot North staff), `OrgAdmin` (School administrators), and `User` (Teachers/Staff).
- **Permission Mapping:** Permissions are mapped to roles. For example, only `OrgAdmin` can access the billing tab for their specific organization.
- **Session Management:** JWT-based sessions stored in secure, HTTP-only cookies.

**Technical Implementation:**
The Rust backend will implement a middleware layer that intercepts every request to check the user's JWT. The `claims` section of the JWT will contain the `role_id`. If a user attempts to access an endpoint reserved for `SuperAdmin` while holding a `User` role, the system will return a `403 Forbidden` response.

**Integration:** This feature must integrate with the 2FA system (Feature 3.2) to ensure that administrative actions are properly verified.

---

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** In Design

To prevent unauthorized access to sensitive student data, Juniper will implement a multi-layered 2FA system.

**Functional Requirements:**
- **TOTP Support:** Users can use apps like Google Authenticator or Authy.
- **WebAuthn/FIDO2:** Full support for hardware keys (e.g., YubiKey).
- **Recovery Codes:** Upon activation, users are provided 10 one-time use recovery codes.
- **Enforcement:** 2FA can be mandated at the `OrgAdmin` level for all users within their organization.

**Technical Implementation:**
The Rust backend will utilize the `webauthn-rs` crate to handle the challenge-response mechanism for hardware keys. For TOTP, the `google-authenticator` crate will be used to verify time-based codes. The state of 2FA (Enabled/Disabled) will be stored in the `user_security_settings` table.

**User Flow:**
1. User logs in with password.
2. System checks `two_factor_enabled` flag.
3. If true, the system prompts for a hardware key touch or a 6-digit TOTP code.
4. Upon successful verification, the full session JWT is issued.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low | **Status:** Complete

Audit trails are critical for compliance in the education sector, ensuring that every change to a student's record is traceable.

**Functional Requirements:**
- **Comprehensive Logging:** Every `POST`, `PUT`, and `DELETE` request must be logged.
- **Immutability:** Logs cannot be edited or deleted, even by a `SuperAdmin`.
- **Tamper-Evidence:** Use of cryptographic hashing (SHA-256) to chain log entries.

**Technical Implementation:**
Each log entry contains a `hash` of the current record plus the `hash` of the previous record (similar to a blockchain). This creates a chain of custody. The logs are stored in a dedicated `audit_logs` table. A daily background worker calculates the root hash of the day's logs and stores it in a separate, read-only storage bucket to ensure that if the database is compromised, the logs cannot be silently altered.

**Logged Fields:** `timestamp`, `user_id`, `action`, `resource_id`, `old_value`, `new_value`, and `ip_address`.

---

### 3.4 Automated Billing and Subscription Management
**Priority:** Low | **Status:** In Review

Juniper transitions the internal tool from a cost-center to a revenue-center by implementing automated billing.

**Functional Requirements:**
- **Tiered Pricing:** Basic, Professional, and Enterprise tiers.
- **Automatic Invoicing:** Monthly recurring billing via Stripe integration.
- **Subscription Lifecycle:** Handle upgrades, downgrades, and cancellations automatically.
- **Dunning Process:** Automated emails for failed payments.

**Technical Implementation:**
The system will use Stripe Webhooks to synchronize subscription status. When a payment is successful, Stripe sends a `customer.subscription.updated` event to the Juniper `/api/billing/webhook` endpoint. The Rust backend then updates the `org_subscription` table in the SQLite DB, granting or revoking access to specific features based on the tier.

**Logic Flow:**
1. User selects "Professional Tier" $\to$ Redirect to Stripe Checkout.
2. Stripe processes payment $\to$ Webhook sent to Juniper.
3. Juniper updates `organization.plan_id` $\to$ UI updates to unlock Professional features.

---

### 3.5 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** In Progress

Given that educators often work in areas with spotty internet (e.g., gymnasiums or rural schools), an offline-first experience is a critical "nice-to-have."

**Functional Requirements:**
- **Local Persistence:** Use of IndexedDB in the browser to store data locally.
- **Optimistic UI:** Changes appear immediate to the user, regardless of connectivity.
- **Background Synchronization:** Once a connection is re-established, the system syncs local changes to the server.
- **Conflict Resolution:** "Last-write-wins" strategy, with a manual override for critical data conflicts.

**Technical Implementation:**
The React frontend will implement a Service Worker to intercept network requests. If the network is offline, requests are queued in an `outbox` store within IndexedDB. A `sync-manager` loop checks for connectivity every 30 seconds. Upon reconnection, it flushes the `outbox` to the `/api/sync` endpoint.

**Data Flow:**
`User Edit` $\to$ `IndexedDB Update` $\to$ `UI Update` $\to$ `Sync Queue` $\to$ `Rust API` $\to$ `SQLite Edge DB`.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions. All requests require a `Bearer <JWT>` token in the Authorization header unless otherwise specified.

### 4.1 Authentication Endpoints

**POST `/api/auth/login`**
- **Description:** Authenticates user and returns session token.
- **Request Body:** `{"email": "user@pivotnorth.com", "password": "password123"}`
- **Success Response (200 OK):** `{"token": "eyJhbG...", "expires_in": 3600}`
- **Error Response (401):** `{"error": "Invalid credentials"}`

**POST `/api/auth/2fa/verify`**
- **Description:** Verifies the 2FA code during the second stage of login.
- **Request Body:** `{"code": "123456", "userId": "uuid-123"}`
- **Success Response (200 OK):** `{"status": "verified", "session_token": "..."}`

### 4.2 User & RBAC Endpoints

**GET `/api/users/me`**
- **Description:** Retrieves the current authenticated user's profile and roles.
- **Response (200 OK):** `{"id": "uuid-123", "role": "OrgAdmin", "email": "user@pivotnorth.com"}`

**PATCH `/api/users/role`**
- **Description:** Updates a user's role (Requires `SuperAdmin` permissions).
- **Request Body:** `{"userId": "uuid-456", "newRole": "User"}`
- **Response (200 OK):** `{"status": "updated"}`

### 4.3 Billing Endpoints

**GET `/api/billing/subscription`**
- **Description:** Retrieves current subscription plan for the user's organization.
- **Response (200 OK):** `{"plan": "Professional", "status": "active", "next_billing_date": "2024-01-01"}`

**POST `/api/billing/checkout`**
- **Description:** Creates a Stripe checkout session.
- **Request Body:** `{"planId": "plan_pro_123"}`
- **Response (200 OK):** `{"checkout_url": "https://stripe.com/checkout/..."}`

### 4.4 Sync & Audit Endpoints

**POST `/api/sync/push`**
- **Description:** Receives batched updates from the offline-first client.
- **Request Body:** `{"updates": [{"table": "students", "action": "update", "data": {...}}]}`
- **Response (200 OK):** `{"synced_count": 15, "conflicts": []}`

**GET `/api/audit/logs`**
- **Description:** Retrieves audit logs for a specific resource (Requires `SuperAdmin`).
- **Query Params:** `?resourceId=uuid-789`
- **Response (200 OK):** `[{"timestamp": "...", "action": "UPDATE", "user": "uuid-123"}]`

---

## 5. DATABASE SCHEMA

Juniper uses a relational model implemented via SQLite at the edge.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | `org_id` | `name`, `domain`, `created_at` | One $\to$ Many `users` | The top-level entity (Schools/Districts). |
| `users` | `user_id` | `email`, `password_hash`, `org_id` | Many $\to$ One `organizations` | User account details. |
| `roles` | `role_id` | `role_name` (Admin, User, etc.) | One $\to$ Many `user_roles` | Definitions of roles. |
| `user_roles` | `id` | `user_id`, `role_id` | Links `users` and `roles` | Mapping users to specific roles. |
| `subscriptions` | `sub_id` | `org_id`, `plan_id`, `status` | Many $\to$ One `organizations` | Billing status and plan level. |
| `plans` | `plan_id` | `name`, `monthly_price`, `limit_users` | One $\to$ Many `subscriptions` | Pricing tiers. |
| `audit_logs` | `log_id` | `user_id`, `action`, `prev_hash` | Many $\to$ One `users` | Tamper-evident change logs. |
| `security_settings`| `id` | `user_id`, `two_factor_enabled` | One $\to$ One `users` | User 2FA and security flags. |
| `offline_sync_queue`| `sync_id` | `user_id`, `payload`, `status` | Many $\to$ One `users` | Queue for offline updates. |
| `user_profiles` | `profile_id` | `user_id`, `full_name`, `avatar_url` | One $\to$ One `users` | Extended user metadata. |

### 5.2 Relationship Logic
- **Orphan Prevention:** `DELETE` cascades are disabled for `organizations` to prevent accidental loss of `audit_logs`.
- **Indexing:** B-Tree indexes are applied to `email` in the `users` table and `org_id` across all related tables to ensure $O(\log n)$ lookup times.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Juniper operates across three distinct environments. To maintain the "every merged PR goes to production" rule, we utilize feature flags (via LaunchDarkly) to hide incomplete features.

#### 6.1.1 Development (`dev`)
- **Purpose:** Individual developer sandbox.
- **Infrastructure:** Local Rust binaries, local SQLite files.
- **Deployment:** Manual.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Integration testing and QA validation.
- **Infrastructure:** Cloudflare Workers (Staging Namespace), D1 Database (Staging Instance).
- **Deployment:** Automatic merge from `develop` branch.
- **Data:** Anonymized production snapshot updated weekly.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live user traffic.
- **Infrastructure:** Cloudflare Workers Global Network, D1 Edge Database.
- **Deployment:** Automatic merge from `main` branch.
- **Scaling:** Automatic horizontal scaling managed by Cloudflare.

### 6.2 Infrastructure Costs
The budget for infrastructure is strictly capped. By using the "Worker-to-D1" architecture, we avoid expensive VPCs and managed Kubernetes clusters.
- **Compute:** Cloudflare Workers (Plan: Enterprise).
- **Storage:** D1 SQLite instances.
- **CDN/Caching:** Cloudflare Edge Cache.

---

## 7. TESTING STRATEGY

Given the distributed nature of the team and the CD pipeline, a rigorous automated testing suite is mandatory.

### 7.1 Unit Testing
- **Backend:** Rust `cargo test` suite. Focuses on business logic, RBAC permission checks, and hash calculations for audit logs.
- **Frontend:** Jest and React Testing Library. Focuses on component rendering and state transitions.
- **Coverage Goal:** 80% line coverage.

### 7.2 Integration Testing
- **API Tests:** Postman/Newman collections integrated into the CI pipeline. Every PR is tested against the `/api` endpoints to ensure no breaking changes in the request/response contracts.
- **Database Tests:** Specialized tests to ensure SQLite migrations do not cause data loss or locking issues during concurrent writes.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Critical Paths:** 
    - User Sign-up $\to$ 2FA Activation $\to$ Login.
    - OrgAdmin $\to$ Plan Upgrade $\to$ Stripe Payment.
    - User $\to$ Offline Edit $\to$ Reconnect $\to$ Sync.
- **Execution:** E2E tests run on every merge to `main` before the production deploy is finalized.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements 10x current capacity with no added budget. | High | Critical | **Contingency Plan:** Implement a fallback architecture using a Read-Replica strategy for the SQLite edge DBs and aggressive caching at the CDN level. |
| R-02 | Key Architect leaving the company in 3 months. | High | High | **Knowledge Transfer:** Engage an external consultant immediately for an independent assessment and to document all architectural decisions. |
| R-03 | Distributed team (5 countries) causing communication lag. | Medium | Medium | **Sync Cadence:** Implement "Core Hours" (13:00–16:00 UTC) where all 15 members must be available for synchronous meetings. |
| R-04 | Design disagreement between Product and Engineering leads. | High | Medium | **Arbitration:** Escalate blocker to Camila Liu for final decision based on the ROI projection and budget constraints. |
| R-05 | Technical debt: Hardcoded values in 40+ files. | High | Medium | **Refactoring Sprint:** Allocate Sprint 4 specifically to move all constants to a centralized `.env` and `config.toml` system. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases of Development

**Phase 1: Foundation (Now – 2026-02-01)**
- Focus: Core Rust API, SQLite Schema setup, RBAC implementation.
- Dependency: Resolution of the Product/Engineering design disagreement.

**Phase 2: Feature Build-out (2026-02-01 – 2026-05-15)**
- Focus: 2FA integration, Billing system, Audit trail completion.
- Dependency: Successful integration of Stripe API.

**Phase 3: Edge Optimization & Sync (2026-05-15 – 2026-07-15)**
- Focus: Offline-first mode and Background Sync.
- Dependency: Stability of the core API.

**Phase 4: Validation & Handover (2026-07-15 – 2026-09-15)**
- Focus: External consultant review, E2E stress testing, Stakeholder demos.

### 9.2 Critical Milestones
- **Milestone 1: MVP Feature-Complete** $\to$ **Target: 2026-05-15**. All 5 features implemented (regardless of status) and integrated into the build.
- **Milestone 2: Architecture Review Complete** $\to$ **Target: 2026-07-15**. External consultant signs off on the scalability of the Rust/SQLite stack.
- **Milestone 3: Stakeholder Demo & Sign-off** $\to$ **Target: 2026-09-15**. Final approval from Pivot North leadership.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-05)
- **Attendees:** Camila, Bodhi, Devika
- **Notes:**
    - Bodhi concerned about SQLite write-locks.
    - Devika wants more E2E tests for 2FA.
    - Camila: "Just use D1, it handles the distribution."
    - Decision: Use D1 for edge persistence.

### Meeting 2: Product/Eng Friction (2023-11-12)
- **Attendees:** Camila, Product Lead (Unnamed)
- **Notes:**
    - Product wants a "Fancy Dashboard."
    - Engineering says "No budget for extra compute."
    - Disagreement on "Offline Mode" priority.
    - Outcome: Still blocked.

### Meeting 3: Sprint Planning (2023-11-19)
- **Attendees:** Full Team (15 members)
- **Notes:**
    - Ravi (Intern) asking about Rust ownership.
    - Audit trail is actually done.
    - Need to fix hardcoded IPs in `config.rs`.
    - 2FA design is "mostly" there.

---

## 11. BUDGET BREAKDOWN

The total budget is **$1,500,000**.

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $1,050,000 | 15 distributed engineers, 1 EM, and the Intern. |
| **Infrastructure** | 10% | $150,000 | Cloudflare Enterprise, Stripe fees, GitHub Enterprise. |
| **External Consulting**| 5% | $75,000 | Independent architectural assessment (Risk R-02). |
| **Tools & Licenses** | 5% | $75,000 | LaunchDarkly, Playwright Cloud, IDE licenses. |
| **Contingency** | 10% | $150,000 | Reserve for performance fallbacks (Risk R-01). |

---

## 12. APPENDICES

### Appendix A: Rust Configuration & Hardcoded Values
The current technical debt involves 42 files containing hardcoded strings. The following must be migrated to the `config.toml` by Sprint 4:
- `API_BASE_URL`
- `STRIPE_SECRET_KEY`
- `DB_CONNECTION_STRING`
- `AUTH_TOKEN_EXPIRY`
- `S3_BUCKET_NAME`

### Appendix B: Conflict Resolution Logic (Offline Sync)
When a conflict occurs during background sync, the system will use the following logic:
1. **Timestamp Comparison:** Compare the `updated_at` field of the local record and the server record.
2. **Precedence:** If the difference is $> 5$ seconds, the server record wins.
3. **Manual Intervention:** If the difference is $< 5$ seconds, the record is flagged as `CONFLICT` in the UI, and the `OrgAdmin` is prompted to choose the correct version.