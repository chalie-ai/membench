Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. It expands every provided detail into a professional engineering standard, incorporating the specific constraints of Stormfront Consulting.

***

# PROJECT SPECIFICATION: CITADEL
**Project Code:** CIT-2024-SCM  
**Version:** 1.0.4-ALPHA  
**Status:** Active / In-Development  
**Classification:** Confidential - Stormfront Consulting  
**Date of Issue:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Citadel" is a strategic platform modernization effort designed to overhaul the supply chain management (SCM) capabilities of Stormfront Consulting within the Media and Entertainment industry. The primary objective is to transition the existing legacy monolithic infrastructure into a high-performance, scalable microservices architecture over a period of 18 months. 

The media and entertainment sector requires a highly specialized supply chain—managing digital assets, licensing rights, physical distribution media, and complex vendor contracts. The current monolith has become a bottleneck, exhibiting significant latency and deployment fragility. Citadel intends to solve this by utilizing a "Clean Monolith" approach initially, ensuring strict module boundaries that allow for seamless extraction into microservices without disrupting business operations.

### 1.2 Business Justification
The current legacy system is unable to handle the surge in high-resolution asset tracking and real-time distribution updates required by modern streaming and cinematic workflows. The operational cost of maintaining the monolith is increasing, and the risk of systemic failure is growing. By transitioning to a Rust-based backend and leveraging Cloudflare Workers for edge computing, Stormfront Consulting will achieve:
- **Reduced Latency:** Moving logic to the edge reduces the time to retrieve supply chain data globally.
- **Increased Reliability:** Rust’s memory safety guarantees eliminate common runtime crashes associated with the previous system.
- **Scalability:** The microservices transition allows individual components (e.g., the import/export engine) to scale independently during peak production cycles.

### 1.3 ROI Projection and Success Metrics
As the project is currently unfunded and bootstrapping with existing team capacity, the ROI is measured primarily through operational efficiency and new revenue streams.
- **Direct Revenue Target:** The system is projected to generate **$500,000 in new revenue** within the first 12 months post-launch. This will be achieved through the introduction of a "Premium Supply Chain Tier" for high-budget studio clients who require the advanced security and auditability provided by the new system.
- **Audit Compliance:** A critical success metric is passing the external ISO 27001 audit on the first attempt. Failure to do so would result in the loss of existing government-contracted media projects.
- **Cost Avoidance:** By migrating to a distributed Rust/Cloudflare architecture, the company expects a 30% reduction in cloud compute costs compared to the previous oversized monolithic VM clusters.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Citadel employs a "Clean Monolith" architectural pattern. This means that while the code resides in a single repository and is deployed as a unified unit initially, the internal structure is strictly partitioned into domains (e.g., `auth`, `inventory`, `integration`). This prevents "spaghetti" dependencies and allows Xavi Liu’s team to peel off services into independent microservices over the 18-month roadmap.

**The Stack:**
- **Backend:** Rust (Tokio runtime, Axum framework).
- **Frontend:** React 18.2 with TypeScript and Tailwind CSS.
- **Edge Layer:** Cloudflare Workers (for global routing, caching, and lightweight edge logic).
- **Database:** SQLite for edge caching and localized state; PostgreSQL (Managed) for the primary source of truth.
- **Infrastructure:** ISO 27001 certified environment.

### 2.2 ASCII Architecture Diagram
```text
[ USER BROWSER ] <---> [ CLOUDFLARE WORKERS (Edge) ] <---> [ GLOBAL CDN ]
                                  |
                                  | (gRPC / HTTPS)
                                  v
                    +---------------------------+
                    |    CITADEL CLEAN MONOLITH  |
                    |  (Rust / Axum / Tokio)    |
                    |                           |
                    |  [Module: Auth/RBAC]      | <--- Boundary 1
                    |  [Module: Data I/O]       | <--- Boundary 2
                    |  [Module: Webhooks]       | <--- Boundary 3
                    |  [Module: SSO/SAML]       | <--- Boundary 4
                    +---------------------------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
    [ SQLite Edge DB ]    [ Primary PostgreSQL ]   [ S3 Asset Store ]
    (Local State/Cache)    (System of Record)       (Media Files)
```

### 2.3 Design Principles
- **Strict Boundary Enforcement:** Modules may only communicate via defined internal APIs. Direct database access across module boundaries is strictly forbidden.
- **Type Safety:** End-to-end type safety from the Rust backend to the React frontend using shared TypeScript definitions generated via `ts-rs`.
- **Edge-First:** Wherever possible, read-heavy requests are intercepted by Cloudflare Workers and served via SQLite edge caches to reduce origin load.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
- **Priority:** Low (Nice to Have)
- **Status:** Not Started
- **Description:** A comprehensive system to manage user identity and permissions within the Citadel platform.
- **Detailed Specification:** 
The RBAC system must support a hierarchical permission model. Roles include `SuperAdmin`, `SupplyChainManager`, `Vendor`, and `Auditor`. Each role is associated with a set of permissions (e.g., `inventory.read`, `inventory.write`, `user.manage`). 
The system will utilize JSON Web Tokens (JWT) for session management. The backend must implement a middleware layer in Rust that intercepts every request to the `/api/v1/admin/*` and `/api/v1/supply/*` paths, validating the token and checking the user's role against the required permission for that specific endpoint.
- **Functional Requirements:**
    - Users must be able to log in via email and password.
    - Admins must be able to assign/revoke roles via a management dashboard.
    - The system must log all "Permission Denied" attempts for security auditing.
- **Acceptance Criteria:** A user with the `Vendor` role should be unable to access the `SuperAdmin` dashboard and should receive a `403 Forbidden` response.

### 3.2 Data Import/Export with Format Auto-Detection
- **Priority:** Critical (Launch Blocker)
- **Status:** In Review
- **Description:** A robust engine to import and export supply chain data across various industry formats (CSV, JSON, XML, and proprietary media industry formats like EBU Core).
- **Detailed Specification:**
This feature is the core of Citadel's utility. The system must accept file uploads and automatically detect the format based on magic bytes and structural analysis. 
The Rust backend will implement a "Strategy Pattern" where different parsers are registered for different formats. Upon upload, the `FormatDetector` service will analyze the file. If it is a `.csv` file, it will attempt to match columns against known supply chain schemas (e.g., "Part Number", "Quantity", "Vendor ID"). If the format is unrecognized, the system must prompt the user to manually map the columns.
Exporting data must allow the user to select a target format. The system will stream the data from PostgreSQL, transform it via the requested strategy, and serve it as a downloadable blob via Cloudflare Workers to ensure high performance for large datasets.
- **Functional Requirements:**
    - Support for files up to 500MB.
    - Auto-detection of CSV, JSON, and XML.
    - Mapping interface for custom column headers.
- **Acceptance Criteria:** A user uploads a CSV file with non-standard headers; the system detects it is a CSV and provides a mapping screen; the data is successfully imported into the database.

### 3.3 Webhook Integration Framework
- **Priority:** Low (Nice to Have)
- **Status:** Blocked
- **Description:** A framework allowing third-party tools (e.g., Jira, Slack, ERP systems) to receive real-time updates from Citadel.
- **Detailed Specification:**
The webhook framework will follow a "Publisher-Subscriber" model. Users can define "Subscriptions" within Citadel, specifying an event (e.g., `shipment.delivered`, `inventory.low`) and a destination URL.
When an event triggers in the Rust backend, the `WebhookDispatcher` will queue a job. A background worker will then send a POST request to the third-party URL with a signed payload to ensure authenticity. 
The system must implement a retry logic with exponential backoff (1min, 5min, 15min, 1hr) if the third-party endpoint returns a non-200 status code. To prevent "webhook storms," the system will implement rate limiting per subscription.
- **Functional Requirements:**
    - Ability to create, edit, and delete webhook endpoints.
    - HMAC-SHA256 signing of payloads.
    - Delivery logs showing request/response headers and bodies.
- **Acceptance Criteria:** Upon a status change of a shipment to "Delivered", the system sends a signed JSON payload to a configured external URL within 5 seconds.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
- **Priority:** Critical (Launch Blocker)
- **Status:** In Review
- **Description:** High-security authentication requiring a second factor, specifically supporting FIDO2/WebAuthn hardware keys (e.g., YubiKey).
- **Detailed Specification:**
Given the ISO 27001 requirement, 2FA is non-negotiable for all users with administrative privileges. The system will implement the WebAuthn standard. 
The process involves two phases: Registration and Authentication. During registration, the backend generates a challenge that the frontend passes to the hardware key. The key signs the challenge and returns it; the backend verifies the signature using the stored public key.
The system must also support TOTP (Time-based One-Time Passwords) via apps like Google Authenticator as a fallback. If a hardware key is lost, a set of one-time recovery codes must be provided to the user during setup.
- **Functional Requirements:**
    - Integration with `webauthn-rs` crate for backend verification.
    - Support for YubiKey, Titan, and Windows Hello/Apple TouchID.
    - Mandatory 2FA for all `SuperAdmin` and `SupplyChainManager` roles.
- **Acceptance Criteria:** A user cannot log in to a privileged account without providing a valid hardware key signature or TOTP code.

### 3.5 SSO Integration with SAML and OIDC Providers
- **Priority:** Medium
- **Status:** Blocked
- **Description:** Integration with enterprise identity providers (Okta, Azure AD, Ping Identity) using SAML 2.0 and OpenID Connect (OIDC).
- **Detailed Specification:**
To cater to large entertainment studios, Citadel must support Single Sign-On (SSO). This removes the need for local password management for corporate users.
The system will implement a Service Provider (SP) role. For OIDC, it will use the Authorization Code Flow with PKCE. For SAML, it will handle XML-based assertions and metadata exchanges.
The integration must include "Just-In-Time" (JIT) provisioning, where a user account is automatically created in Citadel the first time they authenticate via the corporate SSO, provided their corporate group membership matches a predefined mapping (e.g., Azure Group "SCM_Users" maps to Citadel Role "SupplyChainManager").
- **Functional Requirements:**
    - Configuration screen for Client ID, Client Secret, and Discovery URLs.
    - Support for SAML 2.0 metadata XML upload.
    - Mapping of SSO group attributes to Citadel RBAC roles.
- **Acceptance Criteria:** A user from a client organization can log into Citadel using their corporate Okta credentials without creating a separate Citadel password.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1`. All requests require `Content-Type: application/json`.

### 4.1 Authentication Endpoints
**1. POST `/api/v1/auth/login`**
- **Description:** Authenticates user and returns a JWT.
- **Request:** `{ "email": "user@stormfront.com", "password": "securepassword123" }`
- **Response (200):** `{ "token": "eyJhbG...", "expires_at": "2023-10-25T12:00:00Z" }`

**2. POST `/api/v1/auth/2fa/verify`**
- **Description:** Verifies the hardware key signature or TOTP code.
- **Request:** `{ "userId": "uuid-123", "challengeResponse": "base64-signature" }`
- **Response (200):** `{ "status": "verified", "sessionToken": "..." }`

### 4.2 Data Import/Export Endpoints
**3. POST `/api/v1/data/import`**
- **Description:** Uploads a file for supply chain import.
- **Request:** `Multipart/form-data` containing `file` and `importType`.
- **Response (202):** `{ "jobId": "job-999", "status": "processing", "estimatedTime": "30s" }`

**4. GET `/api/v1/data/import/{jobId}`**
- **Description:** Checks the status of an import job.
- **Request:** Path parameter `jobId`.
- **Response (200):** `{ "status": "completed", "recordsImported": 4500, "errors": [] }`

**5. GET `/api/v1/data/export`**
- **Description:** Triggers a data export.
- **Request:** Query params `?format=csv&range=last_quarter`
- **Response (200):** `{ "downloadUrl": "https://cdn.citadel.io/export/xyz123.csv", "expiresIn": 3600 }`

### 4.3 Supply Chain Management Endpoints
**6. GET `/api/v1/inventory/items`**
- **Description:** Lists all tracked assets in the supply chain.
- **Request:** Query params `?category=digital_asset&limit=100`
- **Response (200):** `[ { "id": "item-1", "sku": "MOV-001", "qty": 50, "location": "Vault-A" }, ... ]`

**7. PATCH `/api/v1/inventory/items/{id}`**
- **Description:** Updates the status or quantity of a specific item.
- **Request:** `{ "qty": 45, "status": "in_transit" }`
- **Response (200):** `{ "id": "item-1", "updatedAt": "2023-10-24T10:00:00Z" }`

### 4.4 Integration Endpoints
**8. POST `/api/v1/webhooks/subscribe`**
- **Description:** Registers a new webhook listener.
- **Request:** `{ "event": "shipment.delivered", "targetUrl": "https://client.com/webhook" }`
- **Response (201):** `{ "subscriptionId": "sub-456", "status": "active" }`

---

## 5. DATABASE SCHEMA

Citadel uses a relational model to ensure data integrity. The primary database is PostgreSQL, with SQLite used at the edge for cached views.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `mfa_enabled` | 1:M `user_roles` | Core user identity. |
| `roles` | `role_id` | `role_name`, `permissions_bitmask` | M:M `users` | Defined roles (Admin, Vendor, etc). |
| `user_roles` | `id` | `user_id`, `role_id` | FK to `users`, `roles` | Mapping of users to roles. |
| `assets` | `asset_id` | `sku`, `asset_name`, `category_id` | M:1 `categories` | The physical/digital items being tracked. |
| `categories` | `cat_id` | `category_name`, `description` | 1:M `assets` | Groups of assets (e.g., "Hard Drives"). |
| `inventory_logs`| `log_id` | `asset_id`, `change_qty`, `timestamp`| M:1 `assets` | Audit trail for every inventory change. |
| `vendors` | `vendor_id` | `company_name`, `contact_email` | 1:M `shipments` | Third-party providers. |
| `shipments` | `ship_id` | `vendor_id`, `status`, `tracking_no` | M:1 `vendors` | Logistics tracking for assets. |
| `webhook_subs` | `sub_id` | `target_url`, `event_type`, `secret` | M:1 `users` | Webhook registration data. |
| `auth_keys` | `key_id` | `user_id`, `public_key`, `credential_id`| M:1 `users` | FIDO2/WebAuthn public keys. |

### 5.2 Relationship Logic
- **User $\rightarrow$ Role:** A many-to-many relationship managed via `user_roles`. This allows a user to be both a `Vendor` and an `Auditor` simultaneously.
- **Asset $\rightarrow$ Log:** Every change to an `asset` must trigger an insert into `inventory_logs` to maintain an immutable audit trail for ISO 27001 compliance.
- **Shipment $\rightarrow$ Vendor:** A one-to-many relationship. A vendor can have multiple shipments, but each shipment belongs to one primary vendor.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Citadel utilizes a three-tier environment strategy. All environments are hosted within an ISO 27001 certified cloud region.

#### 6.1.1 Development (`dev`)
- **Purpose:** Rapid iteration and feature development.
- **Configuration:** Automated deployments from `develop` branch. SQLite used for primary storage to speed up migrations.
- **Access:** Restricted to the internal team of 15.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation and QA.
- **Configuration:** Mirror of Production. Uses a sanitized clone of production data. 
- **Gate:** This environment is where the "Manual QA Gate" occurs. No code enters production without a signed-off QA report in JIRA.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live client environment.
- **Configuration:** High-availability PostgreSQL cluster, Cloudflare Workers for global distribution.
- **Deployment:** 2-day turnaround time from Staging sign-off to Production deployment to allow for final sanity checks.

### 6.2 Infrastructure as Code (IaC)
Maeve Fischer (DevOps Engineer) manages the infrastructure using Terraform. All networking, including VPCs, security groups, and Cloudflare route configurations, is version-controlled.

### 6.3 Deployment Workflow
1. **Code Push:** Developer pushes to `feature/*` $\rightarrow$ Merge to `develop`.
2. **CI Pipeline:** Rust tests run $\rightarrow$ Binary compiled $\rightarrow$ Deployed to `dev`.
3. **Promotion:** `develop` merged to `release/v1.x` $\rightarrow$ Deployed to `staging`.
4. **QA Gate:** Xena Jensen (Support/QA) performs manual verification. If passed, JIRA ticket is moved to "Ready for Prod".
5. **Production Release:** Manual trigger of the deployment pipeline $\rightarrow$ 2-day window for monitoring.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Written in Rust using the `#[test]` attribute. Every module boundary must have 80% code coverage. 
- **Focus:** Pure functions, data transformation logic, and the `FormatDetector` logic for import/export.
- **Tooling:** `cargo test`.

### 7.2 Integration Testing
Tests that verify the interaction between the Rust backend and the PostgreSQL/SQLite databases.
- **Focus:** API endpoint correctness, RBAC permission enforcement, and database migration stability.
- **Approach:** Use of Dockerized PostgreSQL containers to run a suite of "real-world" scenarios (e.g., "Import CSV $\rightarrow$ Verify DB state $\rightarrow$ Export CSV").

### 7.3 End-to-End (E2E) Testing
Testing the entire flow from the React frontend through Cloudflare Workers to the backend.
- **Focus:** Critical paths (e.g., the 2FA login flow, the data import wizard).
- **Tooling:** Playwright/Cypress running against the `staging` environment.
- **Frequency:** Executed once per release candidate.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is building same product and is 2 months ahead. | High | High | Hire a specialized contractor to increase development velocity and reduce "bus factor". | Xavi Liu |
| R-02 | Project sponsor is about to rotate out of their role. | Medium | High | Assign a dedicated "Political Owner" to maintain visibility and secure continued bootstrapping. | Xavi Liu |
| R-03 | ISO 27001 audit failure. | Low | Critical | Implement strict logging and RBAC; conduct internal pre-audits every sprint. | Rumi Nakamura |
| R-04 | Performance degradation during monolith $\rightarrow$ microservice shift. | Medium | Medium | Use the "Clean Monolith" boundary approach to isolate performance bottlenecks. | Maeve Fischer |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **Medium/High:** Closely monitored in weekly status meetings.
- **Low/Critical:** Contingency plan established.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach over 18 months.

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Months 1-6):** Establishment of the Clean Monolith, ISO 27001 environment setup, and critical 2FA/Import features.
- **Phase 2: Hardening (Months 7-12):** Refinement of RBAC, completion of SSO, and external audit preparation.
- **Phase 3: Decoupling (Months 13-18):** Gradual extraction of modules into microservices.

### 9.2 Key Milestones
| Milestone | Target Date | Dependency | Description |
| :--- | :--- | :--- | :--- |
| M1: Production Launch | 2026-05-15 | 2FA & Import Complete | Full system live for first set of clients. |
| M2: Architecture Review | 2026-07-15 | M1 Success | Formal review of the "Clean Monolith" boundaries. |
| M3: MVP Feature-Complete| 2026-09-15 | SSO Integration | All planned priority-1 and priority-2 features live. |

---

## 10. MEETING NOTES

*Note: Per company policy, all meetings are recorded via video call. No one re-watches these videos; therefore, these summarized notes are the only permanent record of decisions.*

### Meeting 1: Architecture Kickoff (2023-11-01)
- **Attendees:** Xavi, Maeve, Rumi, Xena.
- **Discussion:** Discussion on whether to go straight to microservices. Xavi argued that the team is too small (15 people) to manage 20+ repositories.
- **Decision:** Adopt the "Clean Monolith" approach. Rust will be used for the backend to ensure the performance needed for the edge.
- **Action Item:** Maeve to set up the Cloudflare Workers environment.

### Meeting 2: Security & Audit Review (2023-12-15)
- **Attendees:** Xavi, Rumi, Xena.
- **Discussion:** Rumi raised concerns that the current password-only login would not pass the ISO 27001 audit. 
- **Decision:** 2FA with hardware key support is upgraded to "Critical - Launch Blocker".
- **Action Item:** Rumi to research `webauthn-rs` for the Rust implementation.

### Meeting 3: Import/Export Bottlenecks (2024-02-10)
- **Attendees:** Xavi, Maeve, Xena.
- **Discussion:** Xena reported that users are attempting to upload files larger than 100MB, which is timing out the current API.
- **Decision:** Move import processing to an asynchronous job queue. The API will return a `202 Accepted` and a `jobId`.
- **Action Item:** Xavi to implement the job queue in the Rust backend.

---

## 11. BUDGET BREAKDOWN

The project is currently **unfunded** and is bootstrapping via existing team capacity. The "budget" refers to the internal allocation of man-hours and existing corporate infrastructure credits.

| Category | Allocation (Internal Cost) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 (Estimated) | 15 engineers across 5 countries over 18 months. |
| **Infrastructure**| $45,000 / year | Cloudflare Workers, Managed PostgreSQL, S3. |
| **Tools** | $12,000 / year | JIRA, GitHub Enterprise, Terraform Cloud. |
| **Contingency** | $150,000 (Budgeted) | Reserve for the contractor needed to mitigate Risk R-01. |
| **Total Est. Cost**| **$1,907,000** | Internalized cost of development. |

---

## 12. APPENDICES

### Appendix A: Data Import Format Matrix
This table defines the logic used by the `FormatDetector` service.

| Magic Bytes / Pattern | Detected Format | Parser Strategy | Priority |
| :--- | :--- | :--- | :--- |
| `0xEF 0xBB 0xBF` | UTF-8 CSV | `CsvParser` | High |
| `{"` or `[` | JSON | `JsonParser` | High |
| `<?xml` | XML | `XmlParser` | Medium |
| `EBUCORE` | EBU Core | `MediaIndustryParser`| Medium |

### Appendix B: ISO 27001 Compliance Mapping
This maps technical features to the required audit controls.

| ISO 27001 Control | Citadel Feature | Implementation Detail |
| :--- | :--- | :--- |
| A.9.2.2 User Access Provisioning | RBAC / SSO | JIT provisioning via OIDC/SAML. |
| A.9.4.2 Secure Log-on Procedures | 2FA / Hardware Keys | WebAuthn requirement for Admins. |
| A.12.4.1 Event Logging | `inventory_logs` | Immutable audit trail in PostgreSQL. |
| A.13.1.1 Network Controls | Cloudflare Workers | Edge-level firewall and DDoS protection. |