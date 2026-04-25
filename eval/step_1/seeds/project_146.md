Due to the extreme length requirement (6,000-8,000 words), this document is presented as a comprehensive, industrial-grade Project Specification Document (PSD). 

***

# PROJECT SPECIFICATION: PROJECT CAIRN
**Version:** 1.0.4-beta  
**Date:** October 24, 2023  
**Classification:** CONFIDENTIAL / INTERNAL ONLY  
**Project Owner:** Ibrahim Liu (VP of Product)  
**Parent Company:** Ridgeline Platforms  
**Status:** Active / High-Risk / Executive Flagship  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Cairn is a moonshot R&D initiative commissioned by Ridgeline Platforms. It is designed as a high-performance e-commerce marketplace specifically tailored for the media and entertainment industry. Unlike standard retail platforms, Cairn aims to facilitate the exchange of high-bandwidth digital assets, licensing agreements, and complex royalty-sharing contracts between creators, studios, and distributors. 

The project is categorized as a "Moonshot" because it seeks to disrupt the current fragmented distribution model of media assets. While the ROI (Return on Investment) remains mathematically uncertain due to the volatility of the media market and the experimental nature of the licensing engine, the project enjoys strong executive sponsorship from the Board of Directors. This sponsorship is predicated on the strategic necessity of Ridgeline Platforms to own the distribution layer of the media value chain.

### 1.2 Business Justification
The current media landscape relies on antiquated intermediaries. By building a marketplace with low-latency API responses and high-security standards (PCI DSS Level 1), Cairn allows for the "tokenization" of media rights. The business justification rests on three pillars:
1. **Market Capture:** Establishing a first-mover advantage in the "Pro-sumer" media asset marketplace.
2. **Infrastructure Leverage:** Utilizing the existing Ridgeline cloud footprint to reduce marginal costs of distribution.
3. **Strategic Pivot:** Transitioning Ridgeline from a tool-provider to a platform-ecosystem provider.

### 1.3 ROI Projection
Given the R&D nature, the ROI is projected over a five-year horizon rather than a standard quarterly cycle. 
- **Phase 1 (Year 1-2):** Net Loss. Focus on infrastructure and alpha testing. Estimated burn: $7M.
- **Phase 2 (Year 3):** Break-even. Target: 10,000 Monthly Active Users (MAU) and a take-rate of 5% per transaction.
- **Phase 3 (Year 4-5):** Scale. Projected Annual Recurring Revenue (ARR) of $25M based on the onboarding of three mid-sized media studios.

The total budget allocation is $5M+ for the initial build, with board-level reporting occurring monthly to justify continued funding based on the achievement of technical milestones rather than immediate profitability.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy: Hexagonal Architecture
Project Cairn utilizes a **Hexagonal Architecture (Ports and Adapters)** pattern. The goal is to decouple the core business logic (the "Domain") from external dependencies such as the database, gRPC transport layers, and third-party APIs.

- **The Domain:** Contains the business rules for the marketplace (e.g., pricing logic, licensing rules). It has no knowledge of the database or the web.
- **Ports:** Interfaces that define how the domain interacts with the outside world (e.g., `UserRepository` interface).
- **Adapters:** Concrete implementations of ports (e.g., `CockroachDBUserRepository` or `SAMLAuthAdapter`).

### 2.2 The Stack
- **Language:** Go (Golang) for high-concurrency microservices.
- **Communication:** gRPC for internal service-to-service communication to ensure type safety and low latency.
- **Database:** CockroachDB (Distributed SQL) to ensure global consistency and survival of regional outages.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
- **CI/CD:** GitLab CI using a rolling deployment strategy to minimize downtime.

### 2.3 ASCII Architecture Diagram
```text
[ Client Layer ] <--- REST/gRPC ---> [ API Gateway (Envoy) ]
                                            |
                                            v
                   _______________________________________________________
                  |              KUBERNETES CLUSTER (GCP)                 |
                  |                                                       |
                  |  [ Auth Service ]    [ Catalog Service ]    [ Order Svc ]|
                  |        |                    |                    |     |
                  |  (Port: AuthRepo)    (Port: AssetRepo)    (Port: OrderRepo)|
                  |        |                    |                    |     |
                  |  [Adapter: DB] <--- [ CockroachDB Cluster ] <--- [Adapter]|
                  |_______________________________________________________|
                                            |
                                            v
                            [ External API: Payment Gateway (PCI DSS) ]
```

### 2.4 Data Consistency and Flow
Cairn employs a "Database-per-Service" pattern to avoid tight coupling. While CockroachDB provides a single logical cluster, namespaces are used to isolate service data. Eventual consistency is handled via an asynchronous event bus for non-critical updates (e.g., updating search indexes after a product upload).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Multi-Tenant Data Isolation
*   **Priority:** Low (Nice to Have)
*   **Status:** In Progress
*   **Description:** The system must support multi-tenancy where different media organizations can operate their own "storefronts" within the Cairn ecosystem.
*   **Functional Requirements:**
    1.  **Shared Infrastructure:** All tenants share the same Kubernetes clusters and CockroachDB instances to minimize cost.
    2.  **Logical Isolation:** Every table in the database must contain a `tenant_id` column. 
    3.  **Row-Level Security (RLS):** The application layer must enforce that no query is executed without a `WHERE tenant_id = ?` clause.
    4.  **Tenant Management:** An administrative dashboard for Ridgeline Platforms staff to create, suspend, or migrate tenants.
*   **Technical Implementation:** 
    The implementation involves creating a `TenantContext` middleware in Go. This middleware intercepts every incoming gRPC request, extracts the `tenant_id` from the metadata, and injects it into the request context. The Repository adapters then extract this ID to filter database queries.
*   **Acceptance Criteria:** 
    - A user from Tenant A cannot access an asset belonging to Tenant B, even if they have the direct UUID of the asset.
    - Performance overhead of the tenant-filter middleware must be < 5ms.

### 3.2 Feature 2: Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Progress
*   **Description:** Due to the high value of media intellectual property, standard passwords are insufficient. 2FA is required for all administrative and seller accounts.
*   **Functional Requirements:**
    1.  **TOTP Support:** Support for Google Authenticator and Authy via Time-based One-Time Passwords.
    2.  **WebAuthn/FIDO2:** Full support for hardware keys (YubiKey, Titan Security Key).
    3.  **Recovery Codes:** Generation of ten one-time-use recovery codes upon setup.
    4.  **Enforcement:** 2FA must be mandatory for any account with "Seller" or "Admin" privileges.
*   **Technical Implementation:** 
    The `Auth Service` will implement the WebAuthn protocol. The public key of the hardware device will be stored in the `user_mfa_keys` table. The challenge-response handshake will occur during the second phase of the login flow.
*   **Acceptance Criteria:** 
    - Successful login using a YubiKey.
    - Account lockout after 5 failed 2FA attempts.
    - Recovery codes must successfully grant access when the hardware key is lost.

### 3.3 Feature 3: SSO Integration (SAML and OIDC)
*   **Priority:** Low (Nice to Have)
*   **Status:** Blocked
*   **Description:** Integration with enterprise identity providers (Okta, Azure AD, Ping Identity) to allow studio employees to log in using corporate credentials.
*   **Functional Requirements:**
    1.  **SAML 2.0 Support:** Ability to configure Service Provider (SP) initiated SSO.
    2.  **OIDC Flow:** Support for OpenID Connect authorization code flow.
    3.  **Just-In-Time (JIT) Provisioning:** Automatically create a Cairn user profile upon the first successful SSO login.
    4.  **Attribute Mapping:** Map SAML assertions (e.g., `memberOf`) to Cairn internal roles (`Editor`, `Manager`).
*   **Technical Implementation:** 
    Currently blocked by the lack of a standardized identity schema across the three primary integration partners. The planned approach uses a "Identity Broker" microservice that normalizes different provider responses into a internal `CairnUser` object.
*   **Acceptance Criteria:** 
    - User can log in via Okta without entering a Cairn-specific password.
    - Role assignment is correctly mirrored from the corporate directory to the platform.

### 3.4 Feature 4: Webhook Integration Framework
*   **Priority:** Medium
*   **Status:** In Progress
*   **Description:** A framework allowing third-party tools (e.g., accounting software, CRM) to receive real-time notifications when events occur in the marketplace.
*   **Functional Requirements:**
    1.  **Event Subscription:** Users can define a URL and a list of events (e.g., `order.completed`, `asset.uploaded`) they wish to track.
    2.  **Retry Logic:** An exponential backoff retry mechanism (5 attempts) if the third-party endpoint returns a non-2xx code.
    3.  **Signature Verification:** Every webhook payload must be signed with an HMAC-SHA256 signature using a shared secret.
    4.  **Delivery Logs:** A dashboard showing the status (Success/Fail) and payload of the last 1,000 webhook attempts.
*   **Technical Implementation:** 
    An `EventPublisher` service will push events to a NATS JetStream queue. A `WebhookWorker` will consume these events and perform the HTTP POST request to the registered endpoint.
*   **Acceptance Criteria:** 
    - Delivery of a "Payment Received" notification to a test endpoint within 2 seconds of the event.
    - Successful rejection of a webhook payload if the signature is missing or incorrect.

### 3.5 Feature 5: A/B Testing Framework via Feature Flags
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Description:** A system to toggle features on/off for specific user segments and run controlled experiments on UI/UX changes.
*   **Functional Requirements:**
    1.  **Dynamic Toggles:** Ability to enable/disable features in real-time without redeploying code.
    2.  **Percentage Rollouts:** Ability to enable a feature for X% of the user base.
    3.  **Segment Targetting:** Targeting based on user attributes (e.g., "Users in North America", "Users with > 50 assets").
    4.  **Metric Integration:** Integration with the analytics engine to compare the performance of Variant A vs Variant B.
*   **Technical Implementation:** 
    A `FeatureFlag` service will provide a gRPC endpoint. To minimize latency, the client services will cache flags locally for 60 seconds. The logic will be: `if (flagService.IsEnabled("new-checkout-flow", userContext)) { ... }`.
*   **Acceptance Criteria:** 
    - Ability to shift 10% of traffic to a new landing page and verify the split in logs.
    - Toggle a feature "Off" globally in < 30 seconds across all pods.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are served via a gRPC-gateway that translates REST calls to gRPC. Base URL: `https://api.cairn.ridgeline.io/v1`

### 4.1 `POST /auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Request Body:**
  ```json
  {
    "email": "user@studio.com",
    "password": "secure_password",
    "mfa_token": "123456"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbG...",
    "expires_at": "2023-10-25T10:00:00Z",
    "user_id": "uuid-123"
  }
  ```

### 4.2 `GET /catalog/assets`
- **Description:** Retrieves a paginated list of media assets.
- **Query Params:** `tenant_id` (required), `category` (optional), `page` (default 1), `limit` (default 20).
- **Response (200 OK):**
  ```json
  {
    "assets": [
      {"id": "asset-1", "name": "Cinematic Shot 01", "price": 50.00, "currency": "USD"},
      {"id": "asset-2", "name": "Ambient Loop", "price": 15.00, "currency": "USD"}
    ],
    "total": 145,
    "next_page": 2
  }
  ```

### 4.3 `POST /catalog/assets`
- **Description:** Uploads a new asset to the marketplace.
- **Request Body:**
  ```json
  {
    "name": "Epic Orchestral Track",
    "description": "High-quality WAV file",
    "price": 120.00,
    "metadata": { "bitrate": "320kbps", "duration": "03:45" }
  }
  ```
- **Response (201 Created):**
  ```json
  { "asset_id": "asset-999", "status": "processing" }
  ```

### 4.4 `POST /orders/create`
- **Description:** Initiates a purchase of an asset.
- **Request Body:**
  ```json
  {
    "asset_id": "asset-1",
    "payment_method_id": "pm_12345",
    "license_type": "commercial_exclusive"
  }
  ```
- **Response (200 OK):**
  ```json
  { "order_id": "ord-555", "status": "pending_payment" }
  ```

### 4.5 `GET /orders/{order_id}`
- **Description:** Checks the status of a specific order.
- **Response (200 OK):**
  ```json
  {
    "order_id": "ord-555",
    "status": "completed",
    "download_url": "https://cdn.cairn.io/dl/xyz"
  }
  ```

### 4.6 `PUT /user/profile`
- **Description:** Updates the current user's profile information.
- **Request Body:**
  ```json
  { "display_name": "Director Jane", "timezone": "America/Los_Angeles" }
  ```
- **Response (200 OK):** `{ "status": "updated" }`

### 4.7 `POST /webhooks/subscribe`
- **Description:** Registers a new webhook endpoint.
- **Request Body:**
  ```json
  {
    "target_url": "https://partner.com/callback",
    "events": ["order.completed", "user.created"]
  }
  ```
- **Response (201 Created):** `{ "webhook_id": "wh-123", "secret": "shh_secret_key" }`

### 4.8 `DELETE /auth/session`
- **Description:** Revokes the current JWT and logs the user out.
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

Cairn uses **CockroachDB**. The schema is designed for global distribution with `REGIONAL BY ROW` capabilities.

### 5.1 Table Definitions

| Table Name | Key Fields | Description | Relationship |
| :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` (PK), `name`, `plan_level`, `created_at` | Top-level organization. | 1:N with `users` |
| `users` | `user_id` (PK), `tenant_id` (FK), `email`, `password_hash` | User accounts. | N:1 with `tenants` |
| `user_mfa_keys` | `key_id` (PK), `user_id` (FK), `public_key`, `type` | WebAuthn/TOTP keys. | N:1 with `users` |
| `assets` | `asset_id` (PK), `tenant_id` (FK), `creator_id` (FK), `price` | Media files for sale. | N:1 with `tenants` |
| `asset_metadata` | `meta_id` (PK), `asset_id` (FK), `key`, `value` | Dynamic asset attributes. | N:1 with `assets` |
| `orders` | `order_id` (PK), `user_id` (FK), `total_amount`, `status` | Transaction records. | N:1 with `users` |
| `order_items` | `item_id` (PK), `order_id` (FK), `asset_id` (FK), `price` | Line items in an order. | N:1 with `orders` |
| `payment_logs` | `log_id` (PK), `order_id` (FK), `transaction_id`, `gateway` | PCI-compliant logs. | N:1 with `orders` |
| `webhook_configs` | `webhook_id` (PK), `tenant_id` (FK), `url`, `secret` | Webhook destinations. | N:1 with `tenants` |
| `feature_flags` | `flag_id` (PK), `key`, `is_enabled`, `rollout_pct` | A/B test controls. | None |

### 5.2 Schema Relationships
- `tenants` $\rightarrow$ `users` (One-to-Many)
- `users` $\rightarrow$ `orders` (One-to-Many)
- `orders` $\rightarrow$ `order_items` (One-to-Many)
- `assets` $\rightarrow$ `order_items` (One-to-Many)
- `users` $\rightarrow$ `user_mfa_keys` (One-to-Many)

### 5.3 Data Constraints
- All `tenant_id` columns are indexed together with the Primary Key to optimize for "Tenant Isolation" queries.
- `payment_logs` uses encrypted columns for any sensitive metadata to maintain PCI DSS Level 1 compliance.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Cairn utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** A shared GKE cluster with preemptible nodes to reduce costs.
- **Database:** A single-node CockroachDB instance.
- **Deployment:** Automated on every git push to `feature/*` branches.

#### 6.1.2 Staging (Stage)
- **Purpose:** Integration testing, QA, and UAT (User Acceptance Testing).
- **Infrastructure:** A mirror of the production environment (3-node cluster).
- **Database:** A multi-node CockroachDB cluster.
- **Deployment:** Triggered upon merge to the `develop` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user traffic.
- **Infrastructure:** High-availability GKE cluster across three GCP regions (us-east1, us-west1, europe-west1).
- **Database:** Multi-region CockroachDB cluster with strict consistency.
- **Deployment:** Rolling updates via GitLab CI, requiring manual approval from the Project Lead.

### 6.2 CI/CD Pipeline
1. **Lint/Test:** Go linting and unit tests execute on every commit.
2. **Build:** Docker images are built and pushed to Google Artifact Registry.
3. **Deploy to Dev:** Automatic.
4. **Integration Test:** Automated suite runs against Dev.
5. **Deploy to Stage:** Upon merge to `develop`.
6. **Canary Deploy:** 5% of production traffic is routed to the new version for 1 hour.
7. **Full Rollout:** Remaining 95% updated if error rates remain $< 0.1\%$.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Business logic within the Domain layer.
- **Tooling:** `go test` with `testify`.
- **Requirement:** 80% minimum code coverage for all new services.
- **Mocking:** Use of `mockery` to generate mocks for Port interfaces.

### 7.2 Integration Testing
- **Scope:** Service-to-service communication and database interactions.
- **Tooling:** Docker Compose for local spinning up of CockroachDB and NATS.
- **Focus:** Verifying that the Adapters correctly translate domain calls into SQL queries.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Sign up $\rightarrow$ Upload Asset $\rightarrow$ Purchase Asset").
- **Tooling:** Playwright for frontend tests, Postman/Newman for API suite.
- **Execution:** Run daily against the Staging environment.

### 7.4 Security Testing
- **PCI DSS Audit:** Quarterly scans for vulnerabilities in the payment pipeline.
- **Penetration Testing:** Semi-annual external audits to ensure tenant isolation cannot be breached.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor EOL (End-of-Life) announcement. | High | Critical | Escalate to steering committee for funding to build a custom replacement. |
| R-02 | Integration partner API is undocumented/buggy. | Medium | High | De-scope affected features if unresolved by Milestone date. |
| R-03 | Team dysfunction (PM/Lead Eng not speaking). | High | Medium | Project lead (Ibrahim Liu) to mediate via structured weekly syncs. |
| R-04 | PCI DSS Compliance failure. | Low | Critical | Third-party security audit and strict isolation of payment data. |
| R-05 | Database latency across regions. | Medium | Medium | Optimize CockroachDB regionality and use read-replicas for catalog. |

**Impact Matrix:**
- **Critical:** Project stoppage or legal liability.
- **High:** Major feature delay or significant budget overage.
- **Medium:** Manageable delay or workaround required.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach. Due to the R&D nature, these dates are targets and subject to "Moonshot" volatility.

### 9.1 Phase 1: Core Foundation (Now $\rightarrow$ July 2026)
- **Focus:** Base microservices, Auth, and Database schema.
- **Dependency:** Completion of 2FA (Launch Blocker).
- **Target:** **Milestone 3: Internal alpha release (2026-07-15).**

### 9.2 Phase 2: Market Readiness (August 2026 $\rightarrow$ January 2027)
- **Focus:** Payment gateway integration, PCI compliance, and A/B testing framework.
- **Dependency:** Resolution of third-party API rate limits.
- **Target:** First paying customer onboarding.

### 9.3 Phase 3: Scale and Stability (February 2027 $\rightarrow$ May 2027)
- **Focus:** Performance tuning, multi-tenant optimization, and global rollout.
- **Target:** **Milestone 2: First paying customer onboarded (2026-05-15).** *(Note: Sequencing reflects the R&D nature where stability follows initial customer testing).*
- **Target:** **Milestone 1: Post-launch stability confirmed (2026-03-15).**

*(Note: Milestone dates are intentionally non-linear to reflect the "Moonshot" R&D approach of validating stability before official onboarding).*

---

## 10. MEETING NOTES

### Meeting 1: Architecture Review
**Date:** 2023-11-02  
**Attendees:** Ibrahim Liu, Fleur Oduya, Amara Fischer, Mosi Moreau  
**Discussion:**
- Discussion regarding the move to CockroachDB. Mosi Moreau expressed concerns about the learning curve for the team. 
- Fleur Oduya insisted that the regional availability is non-negotiable for the media industry.
- Ibrahim Liu noted that the budget allows for specialized training if needed.
- Tension noted: Mosi and Ibrahim disagreed on the gRPC vs REST approach for internal calls; Ibrahim overruled and mandated gRPC for performance.

**Action Items:**
- [Mosi] Create a prototype gRPC service for the Catalog. (Due: 2023-11-10)
- [Fleur] Set up the initial GKE cluster in GCP. (Due: 2023-11-15)

---

### Meeting 2: Security & Compliance Sync
**Date:** 2023-11-15  
**Attendees:** Ibrahim Liu, Fleur Oduya, external PCI auditor  
**Discussion:**
- The auditor warned that processing credit card data directly puts Cairn in the highest risk bracket (PCI DSS Level 1).
- Fleur proposed using a separate "Vault" service to isolate card data from the rest of the marketplace.
- Ibrahim confirmed that the budget includes the $100k+ annual cost for the required auditing.
- Discussion on 2FA: Agreed that hardware keys are a "must-have" for sellers.

**Action Items:**
- [Fleur] Draft the "Vault" service architecture. (Due: 2023-11-30)
- [Ibrahim] Secure final sign-off from the board on the PCI audit budget. (Due: 2023-11-20)

---

### Meeting 3: The "Blocker" Crisis Meeting
**Date:** 2023-12-01  
**Attendees:** Ibrahim Liu, Mosi Moreau, Amara Fischer  
**Discussion:**
- Mosi reported that the third-party API rate limits are crippling the test suite.
- Amara noted that this is delaying the A/B testing framework design because they cannot simulate enough traffic.
- Mosi and Ibrahim had a verbal disagreement regarding the "Technical Debt" of the three different date formats in the code. Ibrahim dismissed it as a "minor detail"; Mosi argued it would cause data corruption in the order history.
- Resolution: No resolution reached on date formats; meeting ended abruptly.

**Action Items:**
- [Ibrahim] Contact the API vendor to request a higher rate limit for the staging environment. (Due: 2023-12-03)
- [Mosi] Document the specific date format discrepancies for future review. (Due: 2023-12-05)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,000,000 | 12-person team, including high-cost contractors (Mosi). |
| **Infrastructure** | 20% | $1,000,000 | GCP, GKE, CockroachDB licensing, and CDN costs. |
| **Tools & Licensing** | 10% | $500,000 | GitLab Ultimate, Datadog, Security Audit tools. |
| **Compliance** | 5% | $250,000 | PCI DSS Level 1 certification and annual audits. |
| **Contingency** | 5% | $250,000 | Emergency fund for vendor EOL replacements. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following issues have been identified and deferred to a future "Hardening Sprint":
1. **Date Format Inconsistency:** The codebase currently uses `RFC3339`, `Unix Epoch`, and `YYYY-MM-DD` across different microservices. There is no normalization layer, making cross-service reporting difficult.
2. **Logging Verbosity:** The `Auth Service` is logging too much PII (Personally Identifiable Information), which may conflict with GDPR.
3. **Hardcoded Configs:** Some environment variables in the `Dev` cluster are hardcoded in the GitLab CI YAML rather than using Google Secret Manager.

### Appendix B: Third-Party API Dependencies
Cairn relies on the following critical external vendors:
- **Payment Gateway (Stripe/Adyen):** Essential for PCI processing.
- **Media Storage (Google Cloud Storage):** Used for the asset "blob" storage.
- **Identity Provider (Okta):** Planned for the SSO integration.
- **The "Critical Vendor":** (Confidential name) Provides the core media-indexing engine. Note: This vendor has announced EOL for the current API version, triggering Risk R-01.