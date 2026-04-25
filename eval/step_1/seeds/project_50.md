Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive **Technical Project Specification (TPS)**. It is designed to serve as the "Single Source of Truth" (SSOT) for the development team at Flintrock Engineering.

***

# PROJECT SPECIFICATION: PROJECT DRIFT
**Document Version:** 1.0.4  
**Last Updated:** 2024-05-20  
**Classification:** Internal / Confidential  
**Project Lead:** Kian Jensen (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project "Drift" represents a strategic pivot for Flintrock Engineering. While the company has a proven track record in industrial engineering and systems integration, Drift is a greenfield venture into the Media and Entertainment (M&E) e-commerce marketplace sector. The objective is to create a high-performance, scalable platform where digital assets, licensing rights, and entertainment media can be traded and managed in a secure environment.

### 1.2 Business Justification
The M&E sector is currently undergoing a transition toward decentralized ownership and niche marketplaces. By entering this space, Flintrock Engineering aims to diversify its revenue streams away from traditional contract engineering and toward a scalable SaaS/Marketplace model. Despite the company having no prior experience in this specific industry, the underlying technical requirements—high concurrency, secure transactions, and robust audit trails—align with Flintrock's core competencies.

### 1.3 ROI Projection
As the project is currently unfunded and bootstrapping via existing team capacity (12 cross-functional members), the initial "investment" is calculated as the opportunity cost of internal labor. 

*   **Year 1 (Development & Alpha):** Expected Spend: $1.2M (Internal Labor Cost). Expected Revenue: $0.
*   **Year 2 (Beta & Market Entry):** Projected Revenue: $2.5M via transaction fees (2.5% per trade) and premium vendor subscriptions ($499/mo).
*   **Year 3 (Scaling):** Projected Revenue: $8M based on a target acquisition of 50,000 active monthly users.

The projected ROI by the end of Year 3 is 3.4x, assuming a successful Internal Alpha release by November 15, 2025. The primary driver of value is the proprietary "Tamper-Evident Audit Trail," which allows Drift to attract high-value corporate clients in the entertainment industry who require strict compliance for intellectual property transfers.

### 1.4 Strategic Alignment
Drift serves as a "learning vehicle" for the company to modernize its deployment patterns. By utilizing Kubernetes and GitLab CI in an ISO 27001 certified environment, Flintrock is upgrading its institutional knowledge, which will eventually benefit its primary engineering contracts.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Drift utilizes a traditional Three-Tier Architecture to ensure a clean separation of concerns, which is critical given the team's lack of experience with the inherited mixed stacks.

1.  **Presentation Tier (Frontend):** A hybrid of React 18.2 and legacy Vue 2.x components (inherited).
2.  **Business Logic Tier (Backend):** A polyglot microservices layer consisting of Node.js (TypeScript), Python (FastAPI), and a legacy Java Spring Boot module.
3.  **Data Tier (Persistence):** A combination of PostgreSQL 15 for relational data and MongoDB 6.0 for flexible catalog schemas.

### 2.2 System Diagram (ASCII Representation)
```text
[ USER BROWSER / MOBILE APP ]
            |
            | HTTPS / TLS 1.3
            v
[ CLOUD LOAD BALANCER (NGINX) ] <---> [ ISO 27001 COMPLIANCE GATEWAY ]
            |
            +---------------------------------------+
            |             K8S CLUSTER               |
            |  +---------------------------------+  |
            |  |  API GATEWAY (Node.js/TypeScript) |  |
            |  +---------------------------------+  |
            |        |              |              |
            |        v              v              |
            |  [Auth Service]  [Market Service]  [Audit Service]
            |  (SAML/OIDC)      (Python/FastAPI)  (Java/Spring)
            |        |              |              |
            +--------+--------------+--------------+
                     |              |
                     v              v
            [ PostgreSQL DB ] <---> [ MongoDB Atlas ]
            (User/Order/Tx)         (Media Catalog)
                     |
                     v
            [ WORM Storage ] <--- (Tamper-Evident Logs)
```

### 2.3 The "Mixed Stack" Integration Strategy
The project inherits three different stacks. To ensure interoperability:
- **Communication:** All services communicate via RESTful JSON APIs and an asynchronous RabbitMQ message bus.
- **Authentication:** A centralized JWT (JSON Web Token) issued by the Auth Service is passed in the `Authorization: Bearer` header across all tiers.
- **Data Sync:** The Java legacy module synchronizes with the PostgreSQL DB via a shared persistence layer to avoid double-writing.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: Medium | Status: Complete)
**Description:** A comprehensive multi-channel alerting system to keep users informed of marketplace activity (bids, sales, account alerts).

**Detailed Requirements:**
The notification system must support four distinct channels: Email, SMS, In-App, and Push. It is designed as a decoupled service that listens to events on the RabbitMQ bus. When a "SaleEvent" is triggered by the Market Service, the Notification Service determines the user's preferences and dispatches the message.

*   **Email:** Integrated via SendGrid API. Supports HTML templates for transaction receipts.
*   **SMS:** Integrated via Twilio. Used exclusively for 2FA and critical security alerts.
*   **In-App:** A WebSocket-based system (Socket.io) that pushes real-time notifications to the React frontend.
*   **Push:** Implementation via Firebase Cloud Messaging (FCM) for Android and iOS devices.

**Logic Flow:**
1.  Event arrives at `notification-queue`.
2.  Service checks `user_preferences` table in PostgreSQL.
3.  If `email_enabled = true`, the payload is sent to the SendGrid adapter.
4.  The system logs the delivery attempt in the `notification_logs` table.

**Verification:** This feature is marked as complete. Unit tests cover 92% of the logic, and integration tests confirm delivery latency under 2 seconds for In-App notifications.

### 3.2 Audit Trail Logging (Priority: Medium | Status: In Progress)
**Description:** A tamper-evident logging system designed to track every modification of ownership for media assets, ensuring a verifiable chain of custody.

**Detailed Requirements:**
Given the industry (Media & Entertainment), the integrity of the audit trail is paramount. Standard database logs are insufficient. The system must implement "Write Once Read Many" (WORM) principles.

*   **Tamper-Evidence:** Each log entry contains a SHA-256 hash of the current record plus the hash of the previous record (a hash-chain). If any record is altered, the chain breaks.
*   **Storage:** Logs are mirrored to an immutable S3 bucket with "Object Lock" enabled.
*   **Scope:** All `UPDATE` and `DELETE` operations on the `assets` and `transactions` tables must trigger an audit event.

**Current Implementation Status:**
The Java Spring Boot module is currently handling the hash-chain generation. However, the integration with the S3 Object Lock is still in development. The team is currently debugging a race condition where high-frequency trades create duplicate hash entries.

**Operational Logic:**
`Event` $\rightarrow$ `AuditService` $\rightarrow$ `CalculateHash(Current + PrevHash)` $\rightarrow$ `Write to DB` $\rightarrow$ `Push to Immutable S3`.

### 3.3 SSO Integration (Priority: Medium | Status: Not Started)
**Description:** Implementation of Single Sign-On (SSO) to allow corporate entertainment entities to manage their staff access via SAML 2.0 and OIDC (OpenID Connect).

**Detailed Requirements:**
To attract B2B clients, Drift must allow users to log in using their corporate credentials (e.g., Okta, Azure AD). 

*   **SAML 2.0:** Must support Service Provider (SP) initiated flows. The system will act as the SP, redirecting users to their Identity Provider (IdP).
*   **OIDC:** Integration with Google Workspace and Microsoft Entra ID for smaller boutique studios.
*   **User Provisioning:** Just-in-Time (JIT) provisioning must be implemented. When a user first logs in via SSO, their profile is automatically created in the `users` table based on the claims provided by the IdP.

**Technical Constraints:**
The system must map external claims (e.g., `groups: "admin"`) to internal Drift roles (`role: "marketplace_manager"`). This mapping configuration will be stored in a secure JSON configuration file within the Auth Service.

### 3.4 Customizable Dashboard (Priority: Low | Status: In Review)
**Description:** A drag-and-drop interface allowing users to personalize their marketplace overview using various data widgets.

**Detailed Requirements:**
The dashboard is intended for "Power Users" (high-volume traders). It should allow users to arrange widgets such as "Current Bids," "Watchlist," "Revenue Analytics," and "Recent Purchases."

*   **Drag-and-Drop:** Implementation using `react-grid-layout`.
*   **Widget API:** Each widget is a standalone component that polls a specific API endpoint (e.g., `/api/v1/dashboard/revenue`).
*   **Persistence:** The layout configuration (coordinates and widget IDs) must be saved to the `user_dashboard_config` table in JSONB format.

**Review Notes:**
The Product Designer (Rumi Kim) has flagged the current UX as "too cluttered." The engineering team is reviewing whether to limit the number of active widgets to 6 per page to prevent frontend performance degradation (DOM bloat).

### 3.5 Localization and Internationalization (Priority: Low | Status: Blocked)
**Description:** Full support for 12 languages to enable global expansion into Asian and European entertainment markets.

**Detailed Requirements:**
The system must support a dynamic translation layer that does not require a redeploy for content changes.

*   **Framework:** Use of `i18next` for the React frontend.
*   **Backend Strategy:** Translation keys stored in a dedicated `translations` table.
*   **Language Support:** English, Spanish, French, German, Japanese, Korean, Chinese (Simplified), Chinese (Traditional), Italian, Portuguese, Arabic, and Hindi.
*   **Currency Handling:** Integration with a real-time exchange rate API to display prices in local currencies.

**Blocker Analysis:**
This feature is currently blocked by the lack of a finalized Content Strategy. The stakeholders have not provided the approved glossary of industry terms for the target languages, and the budget does not yet cover professional translation services.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and require a Bearer Token in the header.

### 4.1 Asset Management
**Endpoint:** `GET /api/v1/assets/{asset_id}`  
**Description:** Retrieves detailed information about a specific media asset.
- **Request:** `GET /api/v1/assets/AST-9902`
- **Response (200 OK):**
```json
{
  "asset_id": "AST-9902",
  "title": "Neo-Tokyo Concept Art",
  "owner_id": "USR-441",
  "price": 1200.00,
  "currency": "USD",
  "status": "for_sale",
  "metadata": { "resolution": "8K", "format": "TIFF" }
}
```

**Endpoint:** `POST /api/v1/assets`  
**Description:** Lists a new asset for sale.
- **Request:** `POST /api/v1/assets`
- **Body:** `{"title": "Vintage Synth Loop", "price": 50.00, "category": "Audio"}`
- **Response (201 Created):** `{"asset_id": "AST-1042", "status": "pending_review"}`

### 4.2 Transactional Operations
**Endpoint:** `POST /api/v1/trades/bid`  
**Description:** Places a bid on an asset.
- **Request:** `POST /api/v1/trades/bid`
- **Body:** `{"asset_id": "AST-9902", "amount": 1300.00}`
- **Response (202 Accepted):** `{"bid_id": "BID-771", "timestamp": "2025-06-01T10:00:00Z"}`

**Endpoint:** `GET /api/v1/trades/history/{user_id}`  
**Description:** Returns a paginated list of a user's trade history.
- **Request:** `GET /api/v1/trades/history/USR-441?page=1&limit=20`
- **Response (200 OK):** `{"trades": [...], "total_pages": 5}`

### 4.3 User & Auth
**Endpoint:** `POST /api/v1/auth/sso/init`  
**Description:** Initiates the SAML handshake.
- **Request:** `POST /api/v1/auth/sso/init`
- **Body:** `{"provider": "okta_corp_a"}`
- **Response (302 Redirect):** `Location: https://okta.com/auth/...?relay_state=...`

**Endpoint:** `GET /api/v1/users/profile`  
**Description:** Fetches the authenticated user's profile.
- **Request:** `GET /api/v1/users/profile`
- **Response (200 OK):** `{"username": "jdoe", "email": "jdoe@flintrock.com", "tier": "premium"}`

### 4.4 System & Audit
**Endpoint:** `GET /api/v1/audit/verify/{asset_id}`  
**Description:** Verifies the integrity of the hash-chain for a specific asset.
- **Request:** `GET /api/v1/audit/verify/AST-9902`
- **Response (200 OK):** `{"integrity": "valid", "chain_length": 14, "last_verified": "2025-05-20T12:00:00Z"}`

**Endpoint:** `PUT /api/v1/settings/notifications`  
**Description:** Updates user notification preferences.
- **Request:** `PUT /api/v1/settings/notifications`
- **Body:** `{"email": true, "sms": false, "push": true}`
- **Response (200 OK):** `{"status": "updated"}`

---

## 5. DATABASE SCHEMA

The system utilizes a hybrid persistence model. PostgreSQL handles transactional and relational data, while MongoDB handles the polymorphic nature of media assets.

### 5.1 PostgreSQL Schema (Relational)

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID) | - | `email`, `password_hash`, `mfa_secret` | Core user account data. |
| `profiles` | `profile_id` (UUID) | `user_id` | `display_name`, `bio`, `avatar_url` | Publicly visible user info. |
| `assets` | `asset_id` (UUID) | `owner_id` | `title`, `current_price`, `status` | The "registry" of all assets. |
| `transactions` | `tx_id` (UUID) | `buyer_id`, `seller_id`, `asset_id` | `amount`, `tx_date`, `payment_status` | Records of all completed sales. |
| `bids` | `bid_id` (UUID) | `user_id`, `asset_id` | `bid_amount`, `expiry_date` | Active offers on assets. |
| `audit_logs` | `log_id` (BigInt) | `asset_id` | `prev_hash`, `curr_hash`, `timestamp` | The tamper-evident chain. |
| `notification_prefs`| `pref_id` (UUID) | `user_id` | `email_enabled`, `sms_enabled`, `push_enabled`| User channel settings. |
| `roles` | `role_id` (Int) | - | `role_name`, `permissions_json` | RBAC definitions. |
| `user_roles` | `mapping_id` (UUID) | `user_id`, `role_id` | `assigned_at` | User-to-role mapping. |
| `dashboard_configs` | `config_id` (UUID) | `user_id` | `layout_json` | Saved widget positions. |

### 5.2 MongoDB Schema (Document)
**Collection:** `asset_metadata`
- **Document ID:** Linked to `assets.asset_id`
- **Fields:**
    - `technical_specs`: { `bitrate`, `resolution`, `codec`, `duration` }
    - `licensing_terms`: { `commercial_use`: bool, `exclusive`: bool, `region_lock`: [] }
    - `version_history`: [ { `version`: 1, `timestamp`: "...", `changes`: "..." } ]
    - `tags`: [ "synthwave", "80s", "ambient" ]

### 5.3 Relationships
- `users` $\rightarrow$ `profiles` (1:1)
- `users` $\rightarrow$ `assets` (1:N, as owner)
- `assets` $\rightarrow$ `transactions` (1:N)
- `assets` $\rightarrow$ `audit_logs` (1:N)
- `users` $\rightarrow$ `bids` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Drift employs a strict environment isolation policy to meet ISO 27001 requirements.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and unit testing.
- **Deployment:** Automatic deploy on push to `feature/*` branches.
- **Infrastructure:** Shared K8s namespace with limited resources.
- **Data:** Mock data; wiped weekly.

#### 6.1.2 Staging (Stage)
- **Purpose:** Integration testing and stakeholder demos.
- **Deployment:** Deploy on merge to `develop` branch.
- **Infrastructure:** Mirrored production architecture (scaled down).
- **Data:** Anonymized production snapshots.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user traffic.
- **Deployment:** Rolling deployment via GitLab CI triggered by `main` branch tags.
- **Infrastructure:** High-availability K8s cluster across 3 availability zones.
- **Data:** Encrypted at rest; strictly controlled access.

### 6.2 CI/CD Pipeline
**Tooling:** GitLab CI.
1.  **Build Phase:** Docker images created for each microservice.
2.  **Test Phase:** Run Jest (Frontend), PyTest (Market Service), and JUnit (Audit Service).
3.  **Security Scan:** SonarQube scan for vulnerabilities and hardcoded secrets.
4.  **Deploy Phase:** `kubectl apply` to the target environment using Helm charts.

### 6.3 Infrastructure Provisioning
**Current Status:** **BLOCKED.** 
The cloud provider has delayed the provisioning of the ISO 27001 certified VPC and the WORM-compliant S3 buckets. Development is currently proceeding using local Docker Compose environments, but this poses a risk to the "Internal Alpha" timeline.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Requirement:** 80% minimum coverage for all new business logic.
- **Tools:** Jest (Frontend), PyTest (Python), JUnit (Java).
- **Focus:** Individual function logic, validation rules, and utility helpers.

### 7.2 Integration Testing
- **Requirement:** All API contracts must be validated.
- **Tools:** Postman / Newman.
- **Focus:** Testing the interaction between the API Gateway and microservices, and the communication between the backend and the mixed database layers (PostgreSQL $\leftrightarrow$ MongoDB).

### 7.3 End-to-End (E2E) Testing
- **Requirement:** Critical path testing (User Registration $\rightarrow$ Asset Listing $\rightarrow$ Bidding $\rightarrow$ Purchase).
- **Tools:** Cypress.
- **Focus:** User journeys and frontend-to-backend flow.

### 7.4 Performance Testing
- **Requirement:** API response time p95 < 200ms at peak load.
- **Tools:** k6.io.
- **Scenario:** Simulate 5,000 concurrent users performing "Search" and "Bid" operations.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | Critical | Hire an experienced contractor immediately to transfer knowledge and reduce "bus factor." |
| R-02 | Team unfamiliarity with mixed stack | Medium | High | Mandatory weekly "Knowledge Share" sessions; exhaustive documentation of workarounds in the Wiki. |
| R-03 | Infrastructure delay (Cloud Provider) | High | Medium | Develop a local Kubernetes (Minikube) environment to simulate prod and avoid total stagnation. |
| R-04 | Technical debt (Hardcoded configs) | High | Medium | Implement a centralized Configuration Service (Spring Cloud Config or similar) to replace hardcoded values in 40+ files. |
| R-05 | ISO 27001 Compliance failure | Low | Critical | Bi-weekly audits by the compliance officer; strict adherence to the security gateway. |

**Probability/Impact Matrix:**
- **Critical:** Project failure or total loss of data.
- **High:** Significant delay in milestones or major feature regression.
- **Medium:** Manageable delay or minor performance hit.

---

## 9. TIMELINE & MILESTONES

The project is managed in two-week sprints. Due to the bootstrapping nature, resources are stretched.

### 9.1 Phase Descriptions
1.  **Phase 1: Foundation (Jan 2025 - July 2025)**
    - Focus: Setting up the K8s cluster, integrating the three stacks, and finalizing the Notification system.
    - Dependency: Cloud provider provisioning.
2.  **Phase 2: Core Marketplace (July 2025 - Sept 2025)**
    - Focus: Implementing Asset Management and the Audit Trail.
    - Dependency: Successful completion of Performance Benchmarks.
3.  **Phase 3: Enterprise Readiness (Sept 2025 - Nov 2025)**
    - Focus: SSO integration and Dashboard polish.
    - Dependency: Stakeholder sign-off.

### 9.2 Key Milestones
- **Milestone 1: Performance benchmarks met**
  - **Target Date:** 2025-07-15
  - **Criteria:** p95 response < 200ms; MongoDB query optimization complete.
- **Milestone 2: Stakeholder demo and sign-off**
  - **Target Date:** 2025-09-15
  - **Criteria:** Working E2E flow of asset trade and audit verification.
- **Milestone 3: Internal alpha release**
  - **Target Date:** 2025-11-15
  - **Criteria:** Deployment to Prod environment; 99.9% uptime for first 72 hours of internal testing.

---

## 10. MEETING NOTES (The "Running Log")

*Note: Per company standard, these are excerpts from the 200-page unsearchable shared document. References are by page number.*

### Meeting 1: Initial Stack Audit (Page 12)
**Date:** 2024-06-10  
**Attendees:** Kian, Camila, Rumi, Zola  
**Discussion:** 
- Camila expressed concern over the Vue 2.x legacy components. She noted that the "interoperability" is currently just a series of iframes, which is unacceptable for a professional marketplace.
- Kian reminded the team that we are bootstrapping. We cannot rewrite the legacy stack from scratch.
- **Decision:** Use a "Strangler Fig" pattern. Gradually replace Vue components with React as we build new features.
- **Action:** Camila to map out which legacy pages are the most critical.

### Meeting 2: The "Hardcoding" Crisis (Page 45)
**Date:** 2024-07-02  
**Attendees:** Kian, Zola, (Contractor TBD)  
**Discussion:**
- Zola discovered that database credentials and API keys are hardcoded in over 40 different files across the Java and Node.js services.
- Zola stated, "I can't find where the production DB URL is defined; it's different in three files."
- Kian admitted that the previous developer rushed the prototype.
- **Decision:** This is now a priority "Technical Debt" item. Zola will lead the effort to migrate these to environment variables.
- **Action:** Zola to create a `.env.example` file and a central Vault for secrets.

### Meeting 3: Audit Trail Logic (Page 88)
**Date:** 2024-08-14  
**Attendees:** Kian, Rumi, (Architect leaving in 3 months)  
**Discussion:**
- The Architect explained the SHA-256 chaining mechanism. He warned that if the sequence is interrupted by a failed write, the entire chain for that asset is corrupted.
- Rumi asked how this would be displayed to the user. "Does the user see the hash?"
- Architect replied that users see a "Verified" badge; the hash is for auditors.
- **Decision:** Implement a "Reconciliation Job" that runs every midnight to verify all chains and alert the team of discrepancies.
- **Action:** Architect to document the hashing algorithm before his departure.

---

## 11. BUDGET BREAKDOWN

Since the project is bootstrapping with existing capacity, the "Budget" represents internal cost allocations and the projected spend for external tools.

| Category | Annual Allocation | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,200,000 | 12 FTEs (Internal cost center allocation). |
| **Infrastructure** | $45,000 | K8s Cluster, MongoDB Atlas, PostgreSQL Managed. |
| **Tooling/SaaS** | $12,000 | GitLab Premium, SendGrid, Twilio, SonarQube. |
| **Contractors** | $80,000 | Specialist hired to mitigate Risk R-01 (Architect exit). |
| **Contingency** | $25,000 | Buffer for emergency cloud scaling or security audits. |
| **TOTAL** | **$1,362,000** | |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Security Requirements
To maintain certification, the Drift environment must adhere to the following:
1.  **Encryption:** All data at rest must be encrypted using AES-256. All data in transit must use TLS 1.3.
2.  **Access Control:** Principle of Least Privilege (PoLP). Developers have no direct access to production databases; all changes must go through a CI/CD pipeline.
3.  **Logging:** All administrative actions (SSH, kubectl exec) must be logged to a remote, read-only server.
4.  **Vulnerability Management:** Weekly dependency scans via `npm audit` and `pip-audit`.

### Appendix B: Database Migration Plan
Because we are inheriting three different stacks, the migration to the unified PostgreSQL/MongoDB schema will follow this sequence:
1.  **Shadow Write Phase:** The new services will write to the new DB while still reading from the legacy DB.
2.  **Comparison Phase:** A script will compare the data between the legacy and new DBs to ensure 100% parity.
3.  **Cut-over Phase:** The legacy DB will be set to read-only for 24 hours before being decommissioned.
4.  **Verification:** A full backup will be taken and stored in an off-site location before the final deletion of legacy tables.