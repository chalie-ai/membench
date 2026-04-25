# Project Specification Document: Project Aqueduct
**Document Version:** 1.0.4  
**Status:** Baseline / Active  
**Date:** October 24, 2023  
**Owner:** Vera Costa, VP of Product  
**Confidentiality Level:** Restricted (Stormfront Consulting Internal)

---

## 1. Executive Summary

### 1.1 Project Overview
Project Aqueduct is a comprehensive rebuild of Stormfront Consulting’s core payment processing system. The project is born out of a critical business necessity: the current legacy version of the platform has suffered catastrophic user feedback, characterized by instability, archaic UI/UX, and a failure to meet the evolving regulatory needs of high-value enterprise clients. This is not a mere iteration but a full-scale architectural overhaul designed to replace the "legacy monolith" with a modern, scalable, and secure fintech engine.

### 1.2 Business Justification
In the current fintech landscape, payment processing is the primary touchpoint for customer satisfaction. The legacy system’s failure has led to a churn rate of 14% in the last two quarters. Market analysis indicates that our competitors are leveraging micro-frontend architectures to deploy updates daily, whereas Stormfront is currently locked into monthly release cycles plagued by regressions. 

The justification for Aqueduct is three-fold:
1. **Customer Retention:** By addressing the systemic failures identified in the user feedback loops, we aim to stabilize the existing client base and stop the churn.
2. **Market Expansion:** The requirement for FedRAMP authorization is a strategic pivot to capture government contracts, a sector currently untapped due to the security shortcomings of the legacy system.
3. **Operational Efficiency:** Moving to AWS ECS and a micro-frontend approach will decouple development streams, allowing the team to iterate on specific modules without risking the entire payment pipeline.

### 1.3 ROI Projection
With a total investment of $3,000,000, Stormfront Consulting projects a Return on Investment (ROI) within 18 months of Milestone 2 (First paying customer onboarded). 

**Financial Projections:**
- **Projected Revenue Increase:** An estimated $4.5M increase in Annual Recurring Revenue (ARR) through the acquisition of three government agencies (leveraging FedRAMP compliance) and the conversion of 20% of churned enterprise clients.
- **Cost Reduction:** A 30% reduction in operational overhead by migrating from legacy on-premise servers to AWS ECS, reducing the need for manual server patching and hardware maintenance.
- **LTV Increase:** We project a 25% increase in Customer Lifetime Value (LTV) as the new feature set (Advanced Search, SSO, and Hardware 2FA) allows us to move up-market into the "Tier 1 Enterprise" bracket.

The ROI is calculated as: `(Net Gain from Investment / Cost of Investment) * 100`. Given the projected $4.5M revenue gain against a $3M spend, the initial ROI is projected at 50% in Year 1 post-launch, scaling as the government contracts mature.

---

## 2. Technical Architecture

### 2.1 Architectural Philosophy
Aqueduct utilizes a **Micro-Frontend (MFE) Architecture**. Unlike a traditional monolith, the user interface is split into independent fragments (e.g., Dashboard, Payment Portal, Security Settings), each owned by specific team members. This prevents a single point of failure in the UI and allows for independent deployment cycles.

The backend is a distributed system leveraging **Python/Django** for business logic, **PostgreSQL** for relational data consistency, and **Redis** for high-speed caching and session management.

### 2.2 Infrastructure Stack
- **Language/Framework:** Python 3.11 / Django 4.2 LTS
- **Database:** PostgreSQL 15 (RDS)
- **Caching/Queue:** Redis 7.0 (ElastiCache)
- **Orchestration:** AWS ECS (Elastic Container Service) using Fargate for serverless compute.
- **CI/CD:** Jenkins pipeline with a manual QA gate.
- **Compliance:** FedRAMP High Baseline.

### 2.3 System Data Flow (ASCII Diagram)

```text
[ Client Browser ] <---(HTTPS/TLS 1.3)---> [ AWS Application Load Balancer ]
                                                      |
                                                      v
        _______________________________________________|_______________________________________________
       |                                      [ AWS ECS Cluster ]                                      |
       |                                                                                                |
       |  [ MFE Shell ] <---> [ Django API Gateway ] <---> [ Auth Service ] <---> [ PostgreSQL DB ]      |
       |         ^                    |                         |                         ^             |
       |         |                    v                         v                         |             |
       |  [ MFE Modules ] <---> [ Redis Cache ] <---> [ Webhook Engine ] <---> [ Third-Party APIs ]      |
       |________________________________________________________________________________________________|
                                                      |
                                                      v
                                           [ FedRAMP Security Perimeter ]
                                           (Logging, Audit Trails, KMS)
```

### 2.4 Technical Constraints
The architecture must accommodate a strict **2-day turnaround for deployments**. Because of the manual QA gate, no code reaches production without a signed-off UAT (User Acceptance Testing) report. The system must also resolve the "God Class" technical debt—a 3,000-line file (`core/auth_utils.py`) that currently manages authentication, logging, and email. This will be decomposed into three separate services: `AuthManager`, `AuditLogger`, and `NotificationService`.

---

## 3. Detailed Feature Specifications

### 3.1 Webhook Integration Framework (Status: Complete | Priority: Medium)
The Webhook Framework allows third-party tools (e.g., Zapier, custom ERPs) to receive real-time notifications when payment events occur. 

**Functional Requirements:**
- **Event Subscriptions:** Users can define a target URL and select specific events (e.g., `payment.succeeded`, `payment.failed`, `refund.initiated`).
- **Payload Delivery:** The system sends a JSON payload containing the event metadata.
- **Retry Logic:** A linear backoff strategy (5 attempts over 24 hours) for failed deliveries (HTTP 4xx/5xx).
- **Security:** Every payload must include a `X-Aqueduct-Signature` header, generated using an HMAC-SHA256 hash of the payload and a secret key shared with the client.

**Technical Implementation:**
The framework utilizes a Redis-backed queue (Celery) to handle asynchronous delivery. When a payment event is triggered in the PostgreSQL database, a signal is sent to the `WebhookDispatcher` which retrieves all active subscriptions for that client and pushes them to the queue.

### 3.2 SSO Integration with SAML and OIDC (Status: In Review | Priority: High)
To meet enterprise security standards, Aqueduct must support Single Sign-On (SSO), allowing clients to use their own Identity Providers (IdPs) like Okta, Azure AD, or Google Workspace.

**Functional Requirements:**
- **SAML 2.0 Support:** Capability to import Metadata XML from the IdP and provide an Assertion Consumer Service (ACS) URL.
- **OIDC (OpenID Connect) Support:** Support for Authorization Code Flow with PKCE.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user profile in Aqueduct upon first successful SSO login, based on claims provided by the IdP.
- **Attribute Mapping:** Administrative interface to map SAML attributes (e.g., `memberOf`) to Aqueduct roles (e.g., `Admin`, `Viewer`).

**Technical Implementation:**
Integration is handled via the `django-allauth` and `python3-saml` libraries. The system validates the XML signatures of the SAML responses and manages the mapping of external Unique Identifiers (UUIDs) to internal user IDs.

### 3.3 Advanced Search with Faceted Filtering (Status: Complete | Priority: High)
The legacy system’s search was a simple `LIKE %query%` SQL statement, which was unusable for clients with millions of transactions.

**Functional Requirements:**
- **Full-Text Indexing:** Search across transaction IDs, customer names, notes, and memo fields.
- **Faceted Filtering:** A sidebar allowing users to narrow results by date range, payment status (Pending, Completed, Failed), amount range, and currency.
- **Latency:** Search results must be returned in under 200ms for datasets up to 10 million records.
- **Autocomplete:** Suggestions based on the most frequent search terms.

**Technical Implementation:**
We implemented a PostgreSQL GIN index for full-text search. For the faceted filtering, we use a "count-aggregation" query that runs in parallel with the main result set, utilizing Redis to cache common filter counts for 15 minutes.

### 3.4 A/B Testing Framework (Status: In Design | Priority: Low)
This "nice to have" feature is integrated into the existing feature flag system to allow the product team to test UI variations without deploying new code.

**Functional Requirements:**
- **Traffic Splitting:** Ability to assign a percentage of users (e.g., 10% Group A, 10% Group B, 80% Control) to a specific feature flag.
- **Sticky Assignment:** Ensure a user stays in their assigned group across sessions using a hash of their `user_id` and the `experiment_id`.
- **Metric Tracking:** Integration with the analytics engine to track conversion rates (e.g., "Did Group B complete the payment faster than Group A?").
- **Kill Switch:** Immediate ability to disable an experiment and revert all users to the control group.

**Technical Implementation:**
The framework will be built as a middleware layer in Django. It will check the `ExperimentConfig` table in PostgreSQL and cache the assignment in Redis to avoid database hits on every page load.

### 3.5 Two-Factor Authentication (2FA) with Hardware Keys (Status: Complete | Priority: Medium)
Due to the FedRAMP requirements and the high-value nature of payment processing, SMS-based 2FA is insufficient.

**Functional Requirements:**
- **WebAuthn Support:** Native support for FIDO2 hardware keys (e.g., YubiKey).
- **TOTP Support:** Support for authenticator apps (Google Authenticator, Authy).
- **Recovery Codes:** Generation of ten 16-character one-time use recovery codes.
- **Enforcement:** Ability for administrators to mandate 2FA for all users within a specific organization.

**Technical Implementation:**
The implementation uses the `webauthn` Python library. The public key from the hardware device is stored in the `user_security_keys` table, and challenges are generated and stored in Redis with a 5-minute TTL to prevent replay attacks.

---

## 4. API Endpoint Documentation

All endpoints follow RESTful conventions and require a Bearer Token in the `Authorization` header.

### 4.1 `POST /api/v1/payments/initiate`
Initiates a new payment transaction.
- **Request Body:**
  ```json
  {
    "amount": 1500.00,
    "currency": "USD",
    "destination_account": "ACC-998877",
    "idempotency_key": "uuid-1234-5678"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "transaction_id": "TXN-100200300",
    "status": "pending",
    "created_at": "2023-10-24T10:00:00Z"
  }
  ```

### 4.2 `GET /api/v1/payments/search`
Retrieves transactions based on facets and search terms.
- **Query Params:** `q=John Doe`, `status=completed`, `page=1`, `limit=50`
- **Response (200 OK):**
  ```json
  {
    "results": [{ "txn_id": "TXN-1", "amount": 50.00, "status": "completed" }],
    "facets": { "status": { "completed": 150, "pending": 20 } },
    "total_count": 170
  }
  ```

### 4.3 `POST /api/v1/webhooks/subscribe`
Registers a new webhook endpoint.
- **Request Body:**
  ```json
  {
    "url": "https://client-erp.com/webhooks",
    "events": ["payment.succeeded", "payment.failed"]
  }
  ```
- **Response (201 Created):**
  ```json
  { "subscription_id": "SUB-5544", "secret": "whsec_abc123" }
  ```

### 4.4 `POST /api/v1/auth/sso/saml/init`
Starts the SAML authentication handshake.
- **Request Body:** `{ "domain": "company.com" }`
- **Response (302 Redirect):** Redirects user to the IdP login page.

### 4.5 `POST /api/v1/auth/2fa/register-key`
Registers a FIDO2 hardware key.
- **Request Body:** `{ "publicKey": "...", "credentialId": "..." }`
- **Response (200 OK):** `{ "status": "registered" }`

### 4.6 `GET /api/v1/accounts/balance`
Returns the current balance of the authenticated account.
- **Response (200 OK):**
  ```json
  { "balance": 12450.50, "currency": "USD", "available_funds": 11000.00 }
  ```

### 4.7 `PATCH /api/v1/payments/{id}/cancel`
Cancels a pending transaction.
- **Request Body:** `{ "reason": "Customer request" }`
- **Response (200 OK):** `{ "transaction_id": "TXN-1", "status": "cancelled" }`

### 4.8 `GET /api/v1/system/health`
Checks the health of the API and its dependencies.
- **Response (200 OK):**
  ```json
  { "status": "healthy", "database": "connected", "redis": "connected" }
  ```

---

## 5. Database Schema

The database uses PostgreSQL 15. Below are the 10 core tables and their relationships.

### 5.1 Tables Definition

| Table Name | Key Fields | Primary Relationships | Purpose |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` (PK), `email`, `password_hash` | 1:N with `accounts` | Central user identity |
| `organizations` | `org_id` (PK), `name`, `fedramp_status` | 1:N with `users` | Corporate client entities |
| `accounts` | `account_id` (PK), `user_id` (FK), `balance` | N:1 with `users` | Financial account balances |
| `transactions` | `txn_id` (PK), `account_id` (FK), `amount` | N:1 with `accounts` | All payment movements |
| `transaction_logs` | `log_id` (PK), `txn_id` (FK), `event_type` | N:1 with `transactions` | Audit trail for payments |
| `webhook_subs` | `sub_id` (PK), `org_id` (FK), `target_url` | N:1 with `organizations` | Webhook registration |
| `webhook_logs` | `delivery_id` (PK), `sub_id` (FK), `status` | N:1 with `webhook_subs` | Tracking delivery attempts |
| `sso_configs` | `config_id` (PK), `org_id` (FK), `idp_entity_id` | N:1 with `organizations` | SAML/OIDC settings |
| `security_keys` | `key_id` (PK), `user_id` (FK), `public_key` | N:1 with `users` | Hardware key public keys |
| `feature_flags` | `flag_id` (PK), `flag_name`, `is_enabled` | None | Global feature toggles |

### 5.2 Key Relationship Logic
- **Transaction Integrity:** The `transactions` table uses a double-entry bookkeeping logic. Every movement is recorded with a corresponding offset in the `transaction_logs` table to ensure that the sum of all transactions equals the current `accounts.balance`.
- **Multi-tenancy:** Every `user` must belong to an `organization`. All API queries are scoped by `org_id` to prevent data leakage between clients, which is a core requirement for FedRAMP.

---

## 6. Deployment and Infrastructure

### 6.1 Environment Architecture
We maintain three strictly isolated environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Deployment:** Triggered automatically on merge to the `develop` branch.
- **Data:** Anonymized subsets of production data.
- **AWS Instance:** t3.medium ECS tasks.

#### 6.1.2 Staging (Stage)
- **Purpose:** User Acceptance Testing (UAT) and Integration Testing.
- **Deployment:** Manual trigger from the `develop` branch.
- **Data:** Mirror of production schema with synthetic high-volume data.
- **AWS Instance:** m5.large ECS tasks.
- **Gate:** This environment is where the **manual QA gate** resides. No code moves to Prod without a signed UAT document.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Deployment:** 2-day turnaround window after Stage approval.
- **Data:** Encrypted at rest (AES-256) and in transit (TLS 1.3).
- **AWS Instance:** c5.xlarge ECS tasks with auto-scaling based on CPU/Memory utilization.

### 6.2 Deployment Workflow
1. **Feature Branch $\rightarrow$ Develop Branch:** (Automated tests)
2. **Develop Branch $\rightarrow$ Staging:** (Integration tests)
3. **Staging $\rightarrow$ Manual QA Gate:** (Human sign-off by Vera Costa)
4. **Staging $\rightarrow$ Production:** (Blue/Green deployment via ECS)

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Tool:** PyTest.
- **Coverage Goal:** 85% minimum.
- **Focus:** Pure business logic, validation functions, and utility methods. All `AuthManager` methods must have 100% coverage.

### 7.2 Integration Testing
- **Tool:** Postman/Newman.
- **Focus:** API endpoint contracts. We test the interaction between the Django API and the PostgreSQL/Redis layers. 
- **Scenario:** A "Payment Cycle" test—initiating a payment, checking the balance update, and verifying the webhook trigger.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress.
- **Focus:** Critical user journeys in the micro-frontends.
- **Key Path:** "Login via SSO $\rightarrow$ Search for Transaction $\rightarrow$ Change 2FA Key $\rightarrow$ Logout."

### 7.4 Security Testing
- **FedRAMP Audit:** Monthly vulnerability scans using Nessus.
- **Penetration Testing:** Semi-annual external audit by a third-party security firm.
- **Static Analysis:** Bandit and SonarQube integrated into the Jenkins pipeline to catch SQL injection or insecure Python patterns.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary Vendor EOL (End-of-Life) | High | High | Negotiate a 12-month timeline extension; identify alternative vendors. |
| R-02 | Project Sponsor Rotation | Medium | High | Raise as a critical blocker in the next board meeting to secure a successor. |
| R-03 | FedRAMP Certification Delay | Medium | High | Engage a dedicated compliance consultant early; use AWS GovCloud. |
| R-04 | "God Class" Regression | High | Medium | Refactor into 3 services incrementally using the Strangler Pattern. |
| R-05 | Infrastructure Provisioning Delay | High | Medium | Use Terraform for Infrastructure-as-Code to speed up setup once provider clears. |

**Probability/Impact Matrix:**
- **Critical:** R-01, R-02 (Requires immediate executive attention)
- **High:** R-03, R-05 (Requires weekly monitoring)
- **Medium:** R-04 (Managed through technical debt sprints)

---

## 9. Timeline and Milestones

The project follows a phased approach with a strict adherence to the target dates.

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Now – 2026-03-15):** Focuses on the core API, Database migration, and decommissioning the God Class. Ends with stability confirmation.
- **Phase 2: Market Entry (2026-03-16 – 2026-05-15):** Focuses on the SSO and 2FA onboarding for the first high-value pilot client.
- **Phase 3: Feature Parity & Scale (2026-05-16 – 2026-07-15):** Finalizing the A/B testing framework and polishing the search facets.

### 9.2 Milestone Schedule
- **Milestone 1: Post-launch stability confirmed**
  - **Target Date:** 2026-03-15
  - **Dependencies:** Infrastructure provisioning, God Class refactor.
- **Milestone 2: First paying customer onboarded**
  - **Target Date:** 2026-05-15
  - **Dependencies:** SSO Integration, 2FA Hardware support.
- **Milestone 3: MVP feature-complete**
  - **Target Date:** 2026-07-15
  - **Dependencies:** A/B Testing Framework, Advanced Search optimization.

---

## 10. Meeting Notes

*Note: These notes are extracted from the shared running document (currently 200 pages, non-searchable).*

### Meeting 1: Technical Debt Review (2023-11-12)
**Attendees:** Vera Costa, Cora Jensen, Orin Moreau, Xiomara Kim.
- **Discussion:** The team discussed the `core/auth_utils.py` file. Xiomara pointed out that any change to the email logic currently risks breaking the authentication flow because they share the same global state.
- **Decision:** Agreed to implement the "Strangler Pattern." We will create a new `NotificationService` and move email logic there first, then tackle the logging, and finally the auth.
- **Action Item:** Cora to set up the new service container in ECS.

### Meeting 2: Infrastructure Blocker Sync (2023-12-05)
**Attendees:** Vera Costa, Cora Jensen.
- **Discussion:** Cora reported that AWS is delaying the provisioning of the dedicated FedRAMP-compliant VPC. This is currently a hard blocker for the staging environment setup.
- **Decision:** Vera will escalate this to the AWS Account Manager. In the meantime, the team will use a "mock" cloud environment using LocalStack to continue development.
- **Action Item:** Vera to call AWS Lead.

### Meeting 3: SSO Scope Expansion (2024-01-20)
**Attendees:** Vera Costa, Orin Moreau, Xiomara Kim.
- **Discussion:** Orin raised concerns that some government clients use an older version of SAML 1.1. 
- **Decision:** The team decided to stick strictly to SAML 2.0 and OIDC. Any client using SAML 1.1 will be required to use a bridge (like Okta) or upgrade, as supporting 1.1 would compromise the security posture required for FedRAMP.
- **Action Item:** Orin to document the supported SAML profiles.

---

## 11. Budget Breakdown

Total Budget: **$3,000,000**

### 11.1 Personnel ($2,100,000)
- **Project Lead (Vera):** $350,000 (Salary + Bonus)
- **DevOps Engineer (Cora):** $250,000
- **Security Engineer (Orin):** $250,000
- **Contractor (Xiomara):** $400,000 (High-rate specialist)
- **Additional 4 Developers:** $850,000 (Average $212.5k per head)

### 11.2 Infrastructure ($400,000)
- **AWS GovCloud/ECS Costs:** $200,000 (Reserved instances for 2 years)
- **PostgreSQL RDS (Multi-AZ):** $100,000
- **Redis ElastiCache:** $50,000
- **Monitoring Tools (Datadog/Splunk):** $50,000

### 11.3 Tools & Licensing ($200,000)
- **Security Audit Licenses:** $80,000
- **SAML/OIDC Commercial Library Licenses:** $40,000
- **QA Automation Tooling:** $30,000
- **IDE/Dev Productivity Tools:** $50,000

### 11.4 Contingency ($300,000)
- **Reserved for:** Vendor EOL mitigation (Risk R-01) and potential AWS cost overruns during the stability phase.

---

## 12. Appendices

### Appendix A: God Class Decomposition Map
The `core/auth_utils.py` (3,000 lines) is being split as follows:
1. **`auth_service.py`**: Handles JWT issuance, password hashing, and SAML assertions. (Estimated 1,100 lines)
2. **`audit_logger.py`**: Handles writing to the `transaction_logs` and system event logs. (Estimated 700 lines)
3. **`notification_manager.py`**: Handles SMTP integration, SendGrid API, and SMS alerts. (Estimated 1,200 lines)

### Appendix B: FedRAMP Security Controls Matrix (Partial)
To achieve authorization, Aqueduct must implement the following controls:
- **AC-2 (Account Management):** Automatic lock-out after 5 failed attempts.
- **AU-2 (Audit Events):** All administrative actions must be logged with a timestamp and UserID.
- **IA-2 (Identification and Authentication):** MFA (Hardware keys) required for all privileged accounts.
- **SC-8 (Transmission Confidentiality):** All data in transit must use TLS 1.3 with approved cipher suites.