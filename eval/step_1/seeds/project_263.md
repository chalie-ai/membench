# PROJECT SPECIFICATION: PROJECT BEACON
**Document Version:** 1.0.4  
**Status:** Draft / Under Review  
**Date:** October 24, 2023  
**Classification:** Confidential - Internal Use Only  
**Company:** Deepwell Data  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Beacon represents a strategic pivot for Deepwell Data. While the company has established a footprint in data analytics and storage, the cybersecurity market remains an untapped frontier. Beacon is designed as a greenfield internal enterprise tool that serves as the foundational layer for a new suite of security-centric products. The primary objective is to establish a highly resilient, scalable, and secure infrastructure that can handle high-frequency API traffic while maintaining strict compliance standards.

The cybersecurity industry is currently experiencing a shift toward "Zero Trust" architectures. By building Beacon using a Go-based microservices architecture and implementing hardware-backed authentication, Deepwell Data is not merely building a tool, but is developing the intellectual property (IP) necessary to compete in the security sector. The tool will act as a gateway for internal security audits, threat detection orchestration, and identity management.

### 1.2 ROI Projection
Given the "shoestring" budget of $150,000, the ROI is calculated based on operational efficiency and risk mitigation rather than immediate direct revenue. 

**Projected Gains:**
- **Infrastructure Efficiency:** The migration from legacy systems to a CockroachDB/GCP stack is projected to reduce the cost per transaction by 35%. Based on current legacy overhead, this represents an estimated annual saving of $42,000 in cloud spend.
- **Market Entry Value:** Developing the Beacon core allows Deepwell Data to enter the cybersecurity market with a pre-validated, SOC 2 Type II compliant framework. The valuation of this IP is estimated at $250,000 in avoided development costs for future commercial versions.
- **Reduced Downtime:** By utilizing gRPC for inter-service communication and Kubernetes for orchestration, the projected system uptime is 99.99%, reducing the cost of unplanned outages by an estimated $15,000 per annum.

### 1.3 Strategic Goal
The ultimate goal of Beacon is to transition from an internal tool to a scalable product capable of supporting external tenants. Success is defined by meeting the p95 latency requirements and achieving a successful external beta by October 2026.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Beacon is designed as a **Modular Monolith transitioning to Microservices**. To optimize for the limited budget and small team size, the project begins as a single deployable binary (the monolith) with strict internal boundary separation. As features mature and scaling needs increase, these modules will be decoupled into independent gRPC services.

### 2.2 Technology Stack
- **Language:** Go 1.21+ (Chosen for concurrency primitives and execution speed).
- **Communication:** gRPC with Protocol Buffers (Protobuf) for low-latency internal communication.
- **Database:** CockroachDB v23.1 (Distributed SQL for high availability and strong consistency).
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
- **CI/CD:** GitHub Actions integrated with GKE for Continuous Deployment.
- **Compliance:** SOC 2 Type II framework integrated into the infrastructure layer.

### 2.3 System Diagram (ASCII Representation)

```text
[ User Request ] 
       |
       v
[ GCP Cloud Load Balancer ]
       |
       v
[ Kubernetes Ingress / Gateway ] <---> [ Authz/Authn Module (The God Class) ]
       |                                     |
       +-------------------------------------+
       |                                     |
       v                                     v
[ API Rate Limiter Service ] <---> [ CockroachDB Cluster ]
       |                                     ^
       v                                     |
[ Feature Modules ] ------------------------+
(Billing, Localization, RBAC)
       |
       v
[ External Vendor API ] <--- (RISK: EOL Dependency)
```

### 2.4 Design Constraints
- **Latency:** All internal gRPC calls must resolve in < 10ms.
- **Consistency:** Strong consistency is required for all authentication and billing transactions (handled by CockroachDB's Raft implementation).
- **Deployment:** Every merged Pull Request (PR) triggers an automated build and deployment to production. There is no "staging" delay for merged code; therefore, automated testing must be exhaustive.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** Complete

This feature serves as the bedrock of Beacon. It implements a comprehensive identity management system that ensures only authorized personnel can access specific cybersecurity toolsets.

**Functional Requirements:**
- **Identity Provider (IdP) Integration:** Support for internal LDAP and OIDC providers.
- **Role Mapping:** A hierarchical role system (SuperAdmin $\rightarrow$ Admin $\rightarrow$ Editor $\rightarrow$ Viewer).
- **Session Management:** JWT-based stateless sessions with short expiration times (15 minutes) and refresh tokens stored in CockroachDB.
- **Permission Granularity:** Permissions are mapped to specific API endpoints (e.g., `beacon.admin.settings.write`).

**Technical Implementation:**
The current implementation resides within the "God Class" (approx. 3,000 lines of code). This class handles the intersection of identity verification, audit logging, and email notifications. While functional and "Complete," it represents a significant point of technical debt that must be refactored into a dedicated `AuthService` before Milestone 2.

**Validation:**
Success is measured by the ability to deny unauthorized requests at the Gateway level before they reach the business logic, ensuring zero unauthorized access to sensitive security data.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** Blocked

To prevent system abuse and ensure fair resource distribution among internal teams, Beacon requires a robust rate-limiting mechanism.

**Functional Requirements:**
- **Tiered Throttling:** Different limits based on user roles (e.g., Viewer: 100 req/min, Admin: 1000 req/min).
- **Sliding Window Algorithm:** Implementation of a sliding window log to prevent "bursting" at the edge of a minute boundary.
- **Real-time Analytics:** A dashboard showing request counts, 429 (Too Many Requests) errors, and latency spikes.
- **Quota Management:** Ability for the CTO to manually override limits for specific high-priority service accounts.

**Technical Implementation:**
The proposed architecture uses a Redis-backed counter (to be deployed on GKE) to track requests across multiple pods. The analytics engine will asynchronously push metrics to a time-series table in CockroachDB.

**Blocker Detail:**
Currently blocked due to a design disagreement between the Product Lead and Engineering regarding whether rate-limiting should happen at the Load Balancer level (Cloud Armor) or the Application level (Go middleware). The engineering team argues for application-level control to allow for dynamic, user-based quotas.

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Blocked

Given the cybersecurity nature of the tool, standard password-based authentication is insufficient. Beacon must implement phishing-resistant MFA.

**Functional Requirements:**
- **FIDO2/WebAuthn Support:** Native support for hardware keys (YubiKey, Titan Security Key).
- **Fallback Methods:** TOTP (Time-based One-Time Password) via apps like Google Authenticator.
- **Enrollment Workflow:** A secure "Onboarding" flow where users must verify their identity via email before registering a hardware key.
- **Recovery Codes:** Generation of ten 8-digit one-time recovery codes stored as salted hashes.

**Technical Implementation:**
The system will use the `webauthn` Go library to handle the challenge-response mechanism. The public key and credential ID will be stored in the `user_mfa_devices` table.

**Blocker Detail:**
Blocked due to the "God Class" technical debt. The authentication logic is so tightly coupled with the email and logging systems that adding WebAuthn logic risks breaking the existing login flow for all users.

### 3.4 Localization and Internationalization (L10n/i18n)
**Priority:** High | **Status:** In Design

Deepwell Data operates across two time zones and intends to scale Beacon to a global workforce. The tool must support 12 languages.

**Functional Requirements:**
- **Supported Languages:** English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Italian, Russian, Arabic, and Hindi.
- **Dynamic Translation:** The UI must switch languages without requiring a page reload (Client-side state management).
- **Right-to-Left (RTL) Support:** The CSS framework must support RTL layouts for Arabic.
- **Locale-Aware Formatting:** Dates, currencies, and number formats must adjust based on the user's locale.

**Technical Implementation:**
The team will use `go-i18n` for backend translation strings and a JSON-based translation map for the frontend. Translation files will be stored in a dedicated GCS (Google Cloud Storage) bucket and cached in-memory upon service startup.

**Design Status:**
The design phase is currently mapping all "string keys" (e.g., `ERR_AUTH_001`) to a translation matrix. The team is debating whether to use a third-party translation service or a manual spreadsheet reviewed by the support engineer (Nadira Jensen).

### 3.5 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Blocked

While currently an internal tool, this feature prepares Beacon for a future "internal chargeback" model where different departments are billed based on their usage.

**Functional Requirements:**
- **Usage Tracking:** Integration with the Usage Analytics module to calculate monthly costs.
- **Invoice Generation:** Automated PDF generation of monthly usage reports.
- **Subscription Tiers:** Ability to assign "Small," "Medium," and "Large" quotas to different cost centers.
- **Payment Gateway Mock:** A simulated billing engine to test credits and debits.

**Technical Implementation:**
This will be a separate microservice using a ledger-style database schema to ensure every "charge" is immutable and auditable.

**Blocker Detail:**
Blocked due to low priority and the current focus on SOC 2 compliance. The steering committee has decided that billing logic is unnecessary until the external beta (Milestone 3) is successfully launched.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are served over HTTPS. Internal service-to-service communication uses gRPC, but the external-facing API uses REST/JSON for compatibility.

### 4.1 Authentication Endpoints

**1. POST `/api/v1/auth/login`**
- **Description:** Authenticates user and returns JWT.
- **Request:** `{ "username": "string", "password": "string", "mfa_token": "string" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_at": "2023-10-24T12:00:00Z" }`

**2. POST `/api/v1/auth/mfa/register`**
- **Description:** Registers a new hardware security key.
- **Request:** `{ "credential_id": "string", "public_key": "string", "sign_count": "int" }`
- **Response:** `201 Created { "status": "registered", "device_id": "dev_991" }`

### 4.2 User & RBAC Endpoints

**3. GET `/api/v1/users/me`**
- **Description:** Retrieves the current user's profile and permissions.
- **Response:** `200 OK { "id": "u123", "role": "Admin", "permissions": ["read:logs", "write:settings"] }`

**4. PATCH `/api/v1/users/{id}/role`**
- **Description:** Updates a user's role (Admin only).
- **Request:** `{ "role": "Editor" }`
- **Response:** `200 OK { "id": "u123", "new_role": "Editor" }`

### 4.3 Usage & Analytics Endpoints

**5. GET `/api/v1/analytics/usage`**
- **Description:** Retrieves usage stats for the current billing cycle.
- **Response:** `200 OK { "requests_total": 15000, "requests_blocked": 450, "p95_latency": "185ms" }`

**6. GET `/api/v1/analytics/top-consumers`**
- **Description:** Lists the top 10 users by request volume.
- **Response:** `200 OK [ { "user_id": "u1", "count": 5000 }, ... ]`

### 4.4 System Administration Endpoints

**7. PUT `/api/v1/system/rate-limits`**
- **Description:** Updates the global rate limit settings.
- **Request:** `{ "role": "Viewer", "limit_per_min": 200 }`
- **Response:** `200 OK { "status": "updated" }`

**8. GET `/api/v1/system/health`**
- **Description:** Returns the health status of the modular monolith and DB.
- **Response:** `200 OK { "status": "healthy", "db_connected": true, "version": "1.0.4" }`

---

## 5. DATABASE SCHEMA

The database is hosted on CockroachDB. All tables use UUIDs as primary keys to ensure global uniqueness across distributed nodes.

### 5.1 Tables and Fields

1.  **`users`**
    - `user_id` (UUID, PK)
    - `email` (String, Unique, Indexed)
    - `password_hash` (String)
    - `mfa_enabled` (Boolean)
    - `created_at` (Timestamp)
2.  **`roles`**
    - `role_id` (UUID, PK)
    - `role_name` (String, Unique) - *e.g., 'SuperAdmin'*
    - `description` (String)
3.  **`user_roles`**
    - `user_id` (UUID, FK $\rightarrow$ users)
    - `role_id` (UUID, FK $\rightarrow$ roles)
    - `assigned_at` (Timestamp)
4.  **`permissions`**
    - `perm_id` (UUID, PK)
    - `perm_key` (String, Unique) - *e.g., 'api:write'*
    - `description` (String)
5.  **`role_permissions`**
    - `role_id` (UUID, FK $\rightarrow$ roles)
    - `perm_id` (UUID, FK $\rightarrow$ permissions)
6.  **`mfa_devices`**
    - `device_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ users)
    - `device_type` (Enum: 'Yubikey', 'TOTP')
    - `public_key` (Text)
    - `last_used` (Timestamp)
7.  **`api_logs`**
    - `log_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ users)
    - `endpoint` (String)
    - `response_time_ms` (Int)
    - `status_code` (Int)
    - `timestamp` (Timestamp)
8.  **`rate_limit_configs`**
    - `config_id` (UUID, PK)
    - `role_id` (UUID, FK $\rightarrow$ roles)
    - `limit_per_minute` (Int)
    - `updated_at` (Timestamp)
9.  **`translations`**
    - `trans_id` (UUID, PK)
    - `locale` (String, Index) - *e.g., 'en-US', 'ja-JP'*
    - `key` (String)
    - `value` (Text)
10. **`billing_accounts`**
    - `account_id` (UUID, PK)
    - `cost_center_id` (String)
    - `current_balance` (Decimal)
    - `currency` (String)

### 5.2 Relationships
- **One-to-Many:** `users` $\rightarrow$ `mfa_devices`
- **Many-to-Many:** `users` $\rightarrow$ `roles` (via `user_roles`)
- **Many-to-Many:** `roles` $\rightarrow$ `permissions` (via `role_permissions`)
- **One-to-Many:** `users` $\rightarrow$ `api_logs`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Due to the continuous deployment model, the distinction between environments is based on traffic routing rather than separate build pipelines.

**1. Development (`dev`)**
- **Purpose:** Sandbox for developers to test new features.
- **Infrastructure:** Single-node GKE cluster, low-spec CockroachDB instance.
- **Trigger:** Pushed to `feature/*` branches.

**2. Staging (`stage`)**
- **Purpose:** Final validation against production-like data.
- **Infrastructure:** Multi-node GKE cluster, mirrored DB schema from production.
- **Trigger:** Pushed to `develop` branch.

**3. Production (`prod`)**
- **Purpose:** Live internal tool for Deepwell Data.
- **Infrastructure:** High-availability GKE cluster across 3 GCP zones. Full CockroachDB cluster with 3-node minimum.
- **Trigger:** Every merged PR to the `main` branch.

### 6.2 Deployment Pipeline
The pipeline is strictly automated via GitHub Actions:
1. **Lint/Test:** Go lint and unit tests must pass.
2. **Containerize:** Build Docker image $\rightarrow$ Push to Google Container Registry (GCR).
3. **Deploy:** `kubectl apply` to the GKE cluster.
4. **Smoke Test:** Automated health check on `/api/v1/system/health`.
5. **Rollback:** If health check fails, the pipeline automatically reverts to the previous image tag.

### 6.3 SOC 2 Compliance Layer
To meet the required SOC 2 Type II compliance, the following infrastructure controls are enforced:
- **Encryption:** All data encrypted at rest (AES-256) and in transit (TLS 1.3).
- **Audit Trails:** All `kubectl` commands and API requests are logged to Google Cloud Logging.
- **Access Control:** GKE cluster access is restricted via IAM and limited to Paz Gupta and Amara Santos.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic and helper functions.
- **Approach:** Using Go's `testing` package. Every new function must have a corresponding `_test.go` file.
- **Requirement:** 80% code coverage minimum.
- **Mocking:** Use of `gomock` to simulate database and external API responses.

### 7.2 Integration Testing
- **Focus:** Interaction between modules (e.g., Auth $\rightarrow$ DB).
- **Approach:** Running tests against a temporary CockroachDB Docker container.
- **Key Scenario:** Validating that a user with a 'Viewer' role cannot access an 'Admin' endpoint.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Full user journeys.
- **Approach:** Playwright scripts simulating a user logging in, enabling 2FA, and accessing analytics.
- **Frequency:** Executed on every merge to `main` before the final deployment step.

### 7.4 QA Workflow (Yael Park)
Yael Park manages the "Quality Gate." No PR can be merged without a "QA Approved" label. This involves:
1. Manual exploratory testing of the feature.
2. Edge case validation (e.g., invalid hardware key tokens).
3. Regression testing of the "God Class" to ensure no breakages in authentication.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary Vendor EOL (End-of-Life) | High | Critical | Escalate to steering committee for funding to build an in-house replacement or migrate to a new vendor. |
| R-02 | Stakeholder Scope Creep | High | Medium | Strict "Feature Freeze" 30 days before each milestone. De-scope low-priority features if dates are missed. |
| R-03 | "God Class" Technical Debt | Critical | High | Incremental refactoring: carve out one function at a time into the new `AuthService` during every sprint. |
| R-04 | SOC 2 Compliance Failure | Medium | Critical | Weekly compliance audits and automated security scanning (Snyk/Trivy). |
| R-05 | Budget Exhaustion | Medium | Medium | Strict scrutiny of GCP spend; utilize preemptible VMs for dev/stage environments. |

**Probability/Impact Matrix:**
- **Critical Impact:** Could stop the project or prevent launch.
- **High Impact:** Significant delay or loss of core functionality.
- **Medium Impact:** Manageable delay or minor feature loss.

---

## 9. TIMELINE

### 9.1 Phases and Dependencies

**Phase 1: Foundation (Now $\rightarrow$ 2026-06-15)**
- **Goal:** Internal Alpha Release.
- **Dependencies:** RBAC (Complete), Infrastructure Setup (In Progress).
- **Key Tasks:**
    - Refactor "God Class" (Partial).
    - Deploy GKE cluster.
    - Finalize internal alpha user list.

**Phase 2: Hardening (2026-06-16 $\rightarrow$ 2026-08-15)**
- **Goal:** Stakeholder Demo and Sign-off.
- **Dependencies:** Phase 1 Completion, SOC 2 Audit.
- **Key Tasks:**
    - Unblock Rate Limiting and 2FA.
    - Finalize Localization for top 3 languages.
    - Conduct internal security penetration test.

**Phase 3: Pilot (2026-08-16 $\rightarrow$ 2026-10-15)**
- **Goal:** External Beta with 10 pilot users.
- **Dependencies:** Stakeholder Sign-off, 2FA stability.
- **Key Tasks:**
    - Deploy to production for external access.
    - Monitor p95 latency at peak load.
    - Gather feedback from 10 pilot users.

### 9.2 Gantt-Style View
- **Jan '26 - Jun '26:** `[ FOUNDATION ]` $\rightarrow$ (Milestone 1: Alpha)
- **Jun '26 - Aug '26:** `[ HARDENING ]` $\rightarrow$ (Milestone 2: Sign-off)
- **Aug '26 - Oct '26:** `[ PILOTING ]` $\rightarrow$ (Milestone 3: Beta)

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom; however, these transcripts are largely ignored by the team. The following summaries represent the "effective" decisions derived from these calls.*

### Meeting 1: Architecture Alignment (2023-11-05)
**Attendees:** Paz Gupta, Amara Santos, Yael Park
- **Discussion:** Debate over the "Modular Monolith" vs. "Pure Microservices." Amara argued that pure microservices would blow the $150k budget due to infrastructure overhead.
- **Decision:** Start with a modular monolith. Use gRPC internally so that the "split" can happen without changing the API signatures.
- **Action Item:** Amara to set up the GCP project and basic GKE cluster.

### Meeting 2: The "God Class" Crisis (2023-12-12)
**Attendees:** Paz Gupta, Yael Park, Nadira Jensen
- **Discussion:** Yael reported that the 3,000-line authentication class is making it impossible to add 2FA without introducing bugs in the login flow. Nadira noted that support tickets for "login failures" are increasing in the dev environment.
- **Decision:** The class is officially labeled as "Technical Debt." A "Refactor-as-you-go" policy is implemented. No new features are to be added to this class; they must be built in the new `AuthService` and called by the class.
- **Action Item:** Paz to allocate 20% of every sprint to refactoring.

### Meeting 3: Localization Strategy (2024-01-20)
**Attendees:** Paz Gupta, Nadira Jensen
- **Discussion:** Nadira highlighted that the 12-language requirement is too ambitious for the current timeline. Discussed whether to use automated translation (Google Translate API) or manual review.
- **Decision:** Use a hybrid approach. Critical UI elements (Buttons, Errors) will be manually reviewed by Nadira. Descriptive text will use automated translation for the Alpha release.
- **Action Item:** Nadira to create the translation spreadsheet.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (USD)
**Status:** Highly Scrutinized

| Category | Allocated Amount | Description | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $90,000 | 8 members (blended rate/stipends) | Majority of budget; focused on core dev. |
| **Infrastructure** | $30,000 | GCP (GKE, CockroachDB, Cloud Armor) | Optimized via preemptible nodes. |
| **Tools/Licensing** | $15,000 | GitHub Enterprise, Snyk, WebAuthn Libs | Necessary for SOC 2 compliance. |
| **Contingency** | $15,000 | Emergency Vendor Replacement | Reserved for Risk R-01 (Vendor EOL). |

**Financial Constraint:** Any spend exceeding $500/month must be approved by Paz Gupta via email.

---

## 12. APPENDICES

### Appendix A: SOC 2 Type II Evidence Checklist
To achieve compliance, the team must produce the following evidence:
1. **Change Management:** Proof that every production change is linked to a merged PR and a QA approval.
2. **Access Reviews:** Quarterly logs showing who has access to the production GKE cluster.
3. **Encryption Proof:** Configuration files showing that CockroachDB is using encrypted volumes.
4. **Incident Response:** A documented playbook for handling a data breach, signed by the CTO.

### Appendix B: gRPC Proto Definition (Simplified)
The following is a representation of the `AuthService` protobuf definition used for internal communication:

```protobuf
syntax = "proto3";

package beacon.auth;

service AuthService {
  rpc ValidateToken(TokenRequest) returns (TokenResponse);
  rpc CheckPermission(PermissionRequest) returns (PermissionResponse);
  rpc RegisterMFA(MFARequest) returns (MFAResponse);
}

message TokenRequest {
  string token = 1;
}

message TokenResponse {
  bool valid = 1;
  string user_id = 2;
  string role = 3;
}

message PermissionRequest {
  string user_id = 1;
  string permission_key = 2;
}

message PermissionResponse {
  bool allowed = 1;
}

message MFARequest {
  string user_id = 1;
  string credential_id = 2;
  bytes public_key = 3;
}

message MFAResponse {
  bool success = 1;
  string device_id = 2;
}
```