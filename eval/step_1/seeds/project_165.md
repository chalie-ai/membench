# Project Specification Document: Project Gantry
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Formal Specification / Active Development  
**Company:** Bellweather Technologies  
**Classification:** Internal / Proprietary  

---

## 1. Executive Summary

**Project Overview**  
Project Gantry is a specialized fintech payment processing system engineered by Bellweather Technologies specifically for the Food and Beverage (F&B) industry. Unlike generic payment gateways, Gantry is designed to handle the high-velocity, high-volume transaction patterns typical of hospitality environments, including split-billing, tipping logic, and offline resilience. The project is initiated as a new product vertical, driven by a strategic partnership with a single enterprise client who has committed to an annual contract value of $2,000,000.

**Business Justification**  
The F&B sector is currently underserved by modern payment processors that can bridge the gap between legacy on-premise Point of Sale (POS) hardware and modern cloud-like API experiences. By developing Gantry, Bellweather Technologies is not merely building a tool, but establishing a foothold in the fintech space. The enterprise client serves as the "anchor tenant," providing the necessary validation and initial revenue stream to fund the development of a scalable product that can eventually be white-labeled for other F&B conglomerates.

**ROI Projection and Financials**  
The project is operating on a "shoestring" budget of $150,000. Given the high constraints of the budget, the Return on Investment (ROI) is projected to be exceptionally high. With a guaranteed $2M annual recurring revenue (ARR) from the anchor client, the initial investment of $150,000 is recouped within the first month of full production launch. 

The primary success metrics are tied to growth and adoption:
- **Revenue Growth:** Achieving $500,000 in *additional* new revenue (beyond the anchor client) within 12 months of launch.
- **User Adoption:** Reaching 10,000 Monthly Active Users (MAU) within 6 months of the August 2026 launch.

**Strategic Constraints**  
The system must operate under strict regulatory and infrastructure constraints. Due to the client's security posture, no cloud services (AWS, Azure, GCP) are permitted. All deployment must occur within the Bellweather on-premise data center. Furthermore, the system must maintain rigorous GDPR and CCPA compliance, with a mandatory requirement for data residency within the European Union (EU) for all European transactions.

---

## 2. Technical Architecture

### 2.1 System Design Philosophy
Gantry utilizes a **Micro-Frontend (MFE) Architecture**. This approach allows the small team of four to maintain independent ownership of specific functional domains, reducing merge conflicts and allowing for independent deployment cycles. Each MFE is served as a separate bundle and integrated via a shell application (The Gantry Orchestrator).

### 2.2 Technology Stack
- **Backend:** Java 17 / Spring Boot 3.2.x
- **Database:** Oracle Database 19c (Enterprise Edition)
- **Frontend:** React 18 (Micro-frontend architecture using Module Federation)
- **Infrastructure:** On-premise Bare Metal / VMware
- **Deployment:** GitHub Actions (Self-hosted runners) $\rightarrow$ Blue-Green Deployment logic
- **Security:** SAML 2.0, OIDC, AES-256 encryption at rest

### 2.3 Architecture Diagram (ASCII Description)

```text
[ CLIENT BROWSER ] 
       |
       v
[ Gantry Orchestrator (MFE Shell) ] <--- (Authentication / Routing)
       |
       +---- [ MFE: Auth & Security ] ----> [ SSO / 2FA Service ]
       |                                          |
       +---- [ MFE: Payment Flow ]    ----> [ Payment Engine ]
       |                                          |
       +---- [ MFE: Rule Builder ]    ----> [ Workflow Automation ]
       |                                          |
       +---- [ MFE: File Management ] ----> [ File Scan Service ]
                                                  |
                                                  v
                                     [ Oracle DB 19c (EU Cluster) ]
                                                  ^
                                                  |
                                     [ On-Premise Data Center ]
                                     (Firewall / Hardware HSM)
```

### 2.4 Data Residency and Compliance
To satisfy GDPR and CCPA, Gantry implements a "Regional Sharding" strategy. While the application logic is centralized, the Oracle DB instances are partitioned. All PII (Personally Identifiable Information) for EU citizens is stored on physical disks located in the Frankfurt data center. Access is audited via a centralized logging system that records every query touching PII.

---

## 3. Detailed Feature Specifications

### 3.1 SSO Integration (SAML and OIDC)
**Priority:** High | **Status:** Not Started  
**Description:** 
Gantry must allow enterprise users to authenticate using their corporate credentials. The system must act as a Service Provider (SP) and integrate with Identity Providers (IdPs) such as Okta, Azure AD, and PingIdentity.

**Functional Requirements:**
- Support for SAML 2.0 for legacy enterprise systems.
- Support for OpenID Connect (OIDC) for modern identity management.
- Just-In-Time (JIT) provisioning to create user profiles upon first successful login.
- Mapping of SAML attributes (e.g., `memberOf`) to Gantry internal roles (`Admin`, `Manager`, `Cashier`).

**Technical Implementation:**
The integration will utilize `spring-security-saml2-service-provider`. The flow will involve an exchange of XML-based assertions. For OIDC, the system will implement the Authorization Code Flow with PKCE (Proof Key for Code Exchange) to ensure secure token exchange.

**Acceptance Criteria:**
- Users can login via a "Company SSO" button.
- Tokens are validated and session-managed via a secure HTTP-only cookie.
- Logout triggers a global session termination across the IdP.

---

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** In Design  
**Description:** 
Given the financial nature of the system, password-based authentication is insufficient. Gantry requires a mandatory 2FA layer for all users accessing administrative or financial configuration panels.

**Functional Requirements:**
- Implementation of TOTP (Time-based One-Time Password) via apps like Google Authenticator.
- Mandatory support for FIDO2/WebAuthn hardware keys (e.g., YubiKey).
- Ability for users to register multiple backup keys.
- Recovery code generation (10 one-time use codes).

**Technical Implementation:**
The system will use the WebAuthn API to interact with hardware keys. The backend will store public keys in the `user_mfa_keys` table. During the challenge-response phase, the server generates a random challenge, the hardware key signs it, and the server verifies the signature using the stored public key.

**Acceptance Criteria:**
- Users cannot access the "Admin" dashboard without a successful 2FA challenge.
- Hardware keys are recognized and authenticated within < 2 seconds.
- System fails securely if the MFA service is unreachable.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** In Progress  
**Description:** 
F&B clients require flexible rules for payment processing (e.g., "If transaction > $500 AND client is 'VIP', apply 5% discount and notify Manager"). This feature allows non-technical users to build these rules.

**Functional Requirements:**
- A drag-and-drop visual interface to define "If-This-Then-That" (IFTTT) logic.
- Pre-defined triggers: `TransactionCreated`, `PaymentFailed`, `RefundRequested`.
- Pre-defined actions: `ApplyDiscount`, `SendNotification`, `FlagForReview`.
- Versioning of rules to allow rollback of faulty automation logic.

**Technical Implementation:**
The engine uses a Domain Specific Language (DSL) translated into JSON. The backend evaluates these rules using a lightweight expression language (SpEL - Spring Expression Language). The visual builder is a React-based flow chart using `react-flow`.

**Acceptance Criteria:**
- A user can create a rule and see it execute in real-time during a test transaction.
- Rules are validated for circular dependencies before being saved.

---

### 3.4 Offline-First Mode with Background Sync
**Priority:** High | **Status:** In Review  
**Description:** 
In high-traffic restaurant environments, network instability is common. The system must allow payments to be processed locally and synced when connectivity is restored.

**Functional Requirements:**
- Local caching of transaction data using IndexedDB in the browser.
- Queueing system for "Pending Sync" transactions.
- Conflict resolution logic (Last-Write-Wins or Manual Review) when syncing.
- Visual indicator of "Offline Mode" and "Syncing..." status.

**Technical Implementation:**
A Service Worker will intercept API requests. If the network is down, the request is diverted to the `OfflineQueue` in IndexedDB. Upon reconnection, a background sync process iterates through the queue, sending requests to the `/api/v1/sync` endpoint using exponential backoff to avoid overwhelming the server.

**Acceptance Criteria:**
- System remains functional (payment entry) during a simulated 5-minute network outage.
- All offline transactions are uploaded exactly once upon reconnection.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** High | **Status:** Not Started  
**Description:** 
The system allows clients to upload store logos, digital menus, and tax documents. These must be scanned for malware and delivered efficiently.

**Functional Requirements:**
- Maximum file size limit of 25MB.
- Integration with a virus scanning engine (ClamAV).
- Distribution of assets via an on-premise CDN (Nginx Cache).
- MIME-type validation to prevent executable uploads.

**Technical Implementation:**
The upload process follows this pipeline: `Client` $\rightarrow$ `Upload API` $\rightarrow$ `Temporary Storage` $\rightarrow$ `ClamAV Scan` $\rightarrow$ `Permanent Storage (S3-compatible on-prem)`. Once scanned and cleared, the file is pushed to the Nginx edge nodes for distribution.

**Acceptance Criteria:**
- Files containing known malware signatures are rejected immediately.
- Assets are served from the closest edge node with a latency < 100ms.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1` and require a Bearer Token in the Authorization header.

### 4.1 Authentication
**Endpoint:** `POST /auth/login`
- **Request:** `{"username": "string", "password": "string", "mfa_token": "string"}`
- **Response:** `{"token": "jwt_string", "expires_at": "iso_timestamp"}`
- **Description:** Validates credentials and MFA token.

**Endpoint:** `POST /auth/sso/saml`
- **Request:** SAML Assertion XML via POST.
- **Response:** `{"token": "jwt_string", "user_id": "uuid"}`
- **Description:** Handles SAML response from IdP.

### 4.2 Payments
**Endpoint:** `POST /payments/process`
- **Request:** `{"amount": 120.50, "currency": "EUR", "payment_method": "card", "merchant_id": "uuid"}`
- **Response:** `{"transaction_id": "tx_123", "status": "pending", "sync_id": "sync_abc"}`
- **Description:** Initiates a payment transaction.

**Endpoint:** `GET /payments/status/{transaction_id}`
- **Request:** Path variable `transaction_id`.
- **Response:** `{"status": "completed", "timestamp": "iso_timestamp", "auth_code": "8821"}`
- **Description:** Checks current status of a transaction.

### 4.3 Workflow & Automation
**Endpoint:** `POST /workflow/rules`
- **Request:** `{"name": "VIP Discount", "logic": "json_dsl_blob", "active": true}`
- **Response:** `{"rule_id": "rule_99", "status": "created"}`
- **Description:** Creates a new automation rule.

**Endpoint:** `DELETE /workflow/rules/{rule_id}`
- **Request:** Path variable `rule_id`.
- **Response:** `{"status": "deleted"}`
- **Description:** Deactivates and removes a rule.

### 4.4 File Management
**Endpoint:** `POST /files/upload`
- **Request:** Multipart/form-data (File binary).
- **Response:** `{"file_id": "file_456", "cdn_url": "https://cdn.gantry.internal/file_456"}`
- **Description:** Uploads a file and triggers the virus scan.

**Endpoint:** `GET /files/scan-status/{file_id}`
- **Request:** Path variable `file_id`.
- **Response:** `{"status": "clean" | "infected" | "scanning"}`
- **Description:** Polls the virus scanner for the result of an upload.

---

## 5. Database Schema

The system uses Oracle DB 19c. All tables use UUIDs as primary keys.

### 5.1 Table Definitions

1. **`users`**: Stores core identity data.
   - `user_id` (UUID, PK), `username` (VARCHAR2), `email` (VARCHAR2), `password_hash` (VARCHAR2), `created_at` (TIMESTAMP).
2. **`user_roles`**: Mapping of users to permissions.
   - `role_id` (UUID, PK), `user_id` (FK $\rightarrow$ users), `role_name` (VARCHAR2 - e.g., 'ADMIN'), `assigned_at` (TIMESTAMP).
3. **`user_mfa_keys`**: Stores public keys for 2FA.
   - `key_id` (UUID, PK), `user_id` (FK $\rightarrow$ users), `key_type` (VARCHAR2 - 'TOTP'/'FIDO2'), `public_key` (BLOB), `is_active` (BOOLEAN).
4. **`merchants`**: Stores F&B client entity data.
   - `merchant_id` (UUID, PK), `merchant_name` (VARCHAR2), `tax_id` (VARCHAR2), `region` (VARCHAR2 - 'EU'/'US'), `created_at` (TIMESTAMP).
5. **`transactions`**: Core payment records.
   - `transaction_id` (UUID, PK), `merchant_id` (FK $\rightarrow$ merchants), `amount` (NUMBER 19,4), `currency` (VARCHAR2(3)), `status` (VARCHAR2), `timestamp` (TIMESTAMP).
6. **`transaction_logs`**: Audit trail for payments.
   - `log_id` (UUID, PK), `transaction_id` (FK $\rightarrow$ transactions), `event` (VARCHAR2), `old_value` (TEXT), `new_value` (TEXT), `changed_by` (FK $\rightarrow$ users).
7. **`workflow_rules`**: Store the DSL for automation.
   - `rule_id` (UUID, PK), `merchant_id` (FK $\rightarrow$ merchants), `rule_logic` (CLOB), `is_active` (BOOLEAN), `version` (INTEGER).
8. **`offline_sync_queue`**: Tracks pending syncs.
   - `sync_id` (UUID, PK), `merchant_id` (FK $\rightarrow$ merchants), `payload` (CLOB), `retry_count` (INTEGER), `last_attempt` (TIMESTAMP).
9. **`uploaded_files`**: Metadata for assets.
   - `file_id` (UUID, PK), `uploaded_by` (FK $\rightarrow$ users), `filename` (VARCHAR2), `storage_path` (VARCHAR2), `scan_status` (VARCHAR2).
10. **`audit_events`**: System-wide security logs.
    - `event_id` (UUID, PK), `user_id` (FK $\rightarrow$ users), `action` (VARCHAR2), `ip_address` (VARCHAR2), `timestamp` (TIMESTAMP).

### 5.2 Relationships
- One-to-Many: `users` $\rightarrow$ `user_roles`
- One-to-Many: `users` $\rightarrow$ `user_mfa_keys`
- One-to-Many: `merchants` $\rightarrow$ `transactions`
- One-to-One: `transactions` $\rightarrow$ `transaction_logs`
- One-to-Many: `merchants` $\rightarrow$ `workflow_rules`

---

## 6. Deployment and Infrastructure

### 6.1 Environment Descriptions

#### Development (DEV)
- **Purpose:** Individual feature development and unit testing.
- **Hardware:** Local Dockerized environments (using Testcontainers for Oracle DB).
- **CI/CD:** Triggered on every push to `feature/*` branches.

#### Staging (STG)
- **Purpose:** Integration testing and User Acceptance Testing (UAT).
- **Hardware:** Virtualized cluster in the on-prem data center.
- **Data:** Anonymized production-like dataset.
- **Deployment:** Triggered on merge to `develop` branch.

#### Production (PROD)
- **Purpose:** Live transaction processing for the anchor client.
- **Hardware:** Bare-metal Oracle RAC cluster for high availability.
- **Data:** Real customer PII, encrypted at rest.
- **Deployment:** Blue-Green strategy. The "Green" environment is updated, health-checked, and then the load balancer flips traffic from "Blue" to "Green."

### 6.2 Deployment Pipeline
We use GitHub Actions with self-hosted runners located inside the Bellweather firewall.
1. **Build:** Maven compile and unit test execution.
2. **Artifact:** Docker image pushed to internal registry.
3. **Deploy (Staging):** Automated deploy to STG cluster $\rightarrow$ Integration tests.
4. **Deploy (Production):** Manual approval $\rightarrow$ Deploy to Green $\rightarrow$ Smoke test $\rightarrow$ Traffic switch.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Requirement:** 80% minimum code coverage for all business logic services.
- **Focus:** Edge cases in payment rounding, currency conversion, and rule evaluation.

### 7.2 Integration Testing
- **Framework:** Spring Boot Test.
- **Approach:** Using **Testcontainers** to spin up a temporary Oracle DB instance to ensure SQL queries are compatible with the 19c dialect.
- **Focus:** API endpoint connectivity, database constraint validation, and SSO handshake flows.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Approach:** Simulating a full user journey from login $\rightarrow$ payment $\rightarrow$ rule trigger $\rightarrow$ file upload.
- **Focus:** Micro-frontend communication and "Offline Mode" simulation (using Chrome DevTools network throttling).

### 7.4 Security Testing
- **SAST:** SonarQube integrated into GitHub Actions to detect vulnerabilities.
- **DAST:** Monthly OWASP ZAP scans against the Staging environment.
- **Compliance:** Quarterly internal audits for GDPR data residency.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Java/Spring/Oracle stack | High | High | Hire a specialized contractor (Hana Moreau) to mentor and reduce "bus factor." |
| R-02 | Integration partner API is undocumented and buggy | High | Medium | Establish a "Workaround Wiki" to document undocumented behaviors and share with the team. |
| R-03 | Budget exhaustion before Production launch | Medium | Critical | Strict scrutiny of all expenses; avoid any paid 3rd party SaaS tools. |
| R-04 | Data residency failure (GDPR violation) | Low | Critical | Physical partitioning of DB servers; strict network routing rules. |
| R-05 | Performance bottlenecks on-premise | Medium | High | Early load testing using JMeter; optimize Oracle indexing. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or legal catastrophe.
- **High:** Significant delay in milestones.
- **Medium:** manageable through extra effort.
- **Low:** Negligible impact.

---

## 9. Timeline

### 9.1 Phase Description

**Phase 1: Foundation & Core Architecture (Now $\rightarrow$ 2026-10-15)**
- Setup of on-premise infrastructure and CI/CD pipelines.
- Core database schema implementation.
- Development of the MFE Shell.
- **Milestone 2: Architecture Review Complete (Target: 2026-10-15)**

**Phase 2: Critical Feature Sprint (2026-10-16 $\rightarrow$ 2026-12-15)**
- Implementation of 2FA and SSO (Launch Blockers).
- Completion of the Offline-First sync engine.
- Integration of the Payment Processor API.
- **Milestone 3: MVP Feature-Complete (Target: 2026-12-15)**

**Phase 3: Hardening & Compliance (2026-12-16 $\rightarrow$ 2026-08-15)**
- Implementation of Virus Scanning and CDN.
- Full GDPR/CCPA audit and remediation.
- Load testing and performance tuning.
- Final UAT with the anchor client.
- **Milestone 1: Production Launch (Target: 2026-08-15)**

*Note: The timeline is sequenced to ensure the "Launch Blocker" (2FA) is resolved long before the final production date.*

---

## 10. Meeting Notes

### Meeting 1: Architecture Alignment
**Date:** 2023-11-05 | **Attendees:** Zia, Felix, Veda, Hana  
**Discussion:** 
The team discussed the constraint of no cloud usage. Veda expressed concern that a Micro-Frontend architecture might be overkill for a team of 4. Zia argued that since they are a veteran team, the independence of MFEs will actually speed up development by reducing merge conflicts. Felix raised a point about Oracle DB licensing costs.  
**Decisions:**
- Proceed with MFE using Module Federation.
- Use Oracle 19c Enterprise Edition provided by the corporate license.  
**Action Items:**
- [Felix] Map out the initial DB schema $\rightarrow$ Due 2023-11-12.
- [Veda] Create a high-level wireframe for the Rule Builder $\rightarrow$ Due 2023-11-15.

### Meeting 2: The API Crisis
**Date:** 2023-12-12 | **Attendees:** Zia, Felix, Hana  
**Discussion:** 
Felix and Hana reported that the third-party payment API is severely undocumented. They are seeing 403 errors without explanation and intermittent 500s. More importantly, they are currently **blocked by third-party API rate limits** during the integration testing phase.  
**Decisions:**
- Implement a "Mock Server" to allow frontend development to continue while the API issues are resolved.
- Hana will dedicate the next sprint to "Reverse Engineering" the API via packet capture.  
**Action Items:**
- [Hana] Document all discovered API endpoints and their actual (not documented) behavior $\rightarrow$ Ongoing.
- [Zia] Contact the partner's technical lead to request a rate-limit increase for the STG environment $\rightarrow$ Due 2023-12-14.

### Meeting 3: Technical Debt Review
**Date:** 2024-01-20 | **Attendees:** Zia, Felix, Veda, Hana  
**Discussion:** 
Zia identified a critical issue during a code review: **hardcoded configuration values (URLs, API keys, DB credentials) are scattered across 40+ files**. This is a security risk and makes blue-green deployments impossible.  
**Decisions:**
- Immediate halt on new feature development for 3 days.
- Migration of all hardcoded values to a centralized `application.yml` and use of Spring `@Value` or `@ConfigurationProperties`.
- Integration of a secret management tool (Vault) on-premise.  
**Action Items:**
- [Felix] Create a script to grep all files for hardcoded IPs/keys $\rightarrow$ Due 2024-01-21.
- [Hana] Refactor the PaymentService to use the new config properties $\rightarrow$ Due 2024-01-24.

---

## 11. Budget Breakdown

**Total Budget:** $150,000  
**Strategy:** Shoestring / Lean. Every dollar is scrutinized.

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel (Contractor)** | $85,000 | Payment for Hana Moreau (Specialist Contractor) to mitigate the "bus factor" and provide stack expertise. |
| **Infrastructure** | $25,000 | On-premise hardware upgrades (RAM/SSD for Oracle DB) and Nginx Edge server licenses. |
| **Tools & Software** | $15,000 | SonarQube licenses, ClamAV enterprise support, and professional IDE licenses. |
| **Contingency** | $25,000 | Reserved for emergency hardware failure or critical security remediation. |

*Note: Full-time salaries for Zia, Felix, and Veda are handled via Bellweather's corporate payroll and are not deducted from the $150k project budget.*

---

## 12. Appendices

### Appendix A: Rule Builder DSL Specification
The Workflow Automation Engine uses a JSON-based logic tree. 

**Example Rule:**
```json
{
  "ruleId": "rule_vip_01",
  "trigger": "TRANSACTION_CREATED",
  "conditions": [
    {
      "field": "transaction.amount",
      "operator": "GREATER_THAN",
      "value": 500
    },
    {
      "field": "customer.tier",
      "operator": "EQUALS",
      "value": "VIP"
    }
  ],
  "actions": [
    {
      "type": "APPLY_DISCOUNT",
      "params": { "percentage": 5 }
    },
    {
      "type": "NOTIFY_USER",
      "params": { "role": "MANAGER", "channel": "EMAIL" }
    }
  ]
}
```

### Appendix B: Offline Sync Conflict Resolution Matrix
When the system returns online, the following logic is applied to synchronize the `offline_sync_queue` with the Oracle DB:

| Conflict Scenario | Resolution Strategy | Logic |
| :--- | :--- | :--- |
| Transaction Modified Offline vs Online | **Last-Write-Wins** | The timestamp of the last update determines the final state. |
| Duplicate Transaction ID | **Reject Sync** | The second attempt is logged as a "Duplicate Error" for manual review. |
| Invalid Merchant State | **Queue for Review** | If the merchant was deactivated while the transaction was offline, the record is sent to a manual review queue. |
| Partial Sync Failure | **Atomic Rollback** | If a batch of 10 transactions is synced and the 5th fails, the entire batch is rolled back to maintain consistency. |