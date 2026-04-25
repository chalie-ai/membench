# PROJECT SPECIFICATION DOCUMENT: IRONCLAD
**Version:** 1.0.4-RELEASE  
**Date:** October 24, 2023  
**Project Code:** CL-IC-2024  
**Status:** Active / In-Development  
**Confidentiality:** Internal / Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
"Ironclad" began as a high-intensity hackathon project within Clearpoint Digital, designed to solve an immediate internal friction point: the fragmented procurement and management of telecommunications infrastructure and services. What started as a prototype has organically evolved into a critical productivity tool, currently serving 500 daily active users (DAU) within the organization. However, the tool's current state—characterized by rapid, undocumented growth—is unsustainable.

The telecommunications industry is currently undergoing a shift toward "Infrastructure as Code" and rapid service provisioning. Clearpoint Digital requires a robust e-commerce marketplace that allows internal teams and external partners to procure, manage, and scale telecom assets without the current overhead of manual ticketing and multi-day approval cycles. Ironclad is designed to transition from a "hackathon tool" to a production-grade internal marketplace.

The primary business driver is the elimination of operational silos. Currently, provisioning a new virtual circuit or managing a subscription for a carrier-grade firewall requires manual intervention across three different departments. Ironclad centralizes this into a single, multi-tenant interface, providing a unified "storefront" for telecom resources.

### 1.2 ROI Projection
The project is backed by a budget of $800,000, with a projected 6-month development cycle. The Return on Investment (ROI) is calculated based on the following pillars:

1.  **Labor Cost Reduction:** The primary success metric is a 50% reduction in manual processing time for end users. Based on an average of 120 man-hours per week spent on manual provisioning across the org, a 50% reduction saves approximately 60 hours/week. At an average burdened labor rate of $110/hr, this equates to ~$343,200 in annual recaptured productivity.
2.  **Error Mitigation:** Manual entries in telecom provisioning lead to an average of 4% configuration error rate, causing downtime. By automating the workflow via the "Visual Rule Builder," we project a 90% reduction in human-entry errors, saving an estimated $120,000 annually in emergency rollback costs and SLA penalties.
3.  **Scalability:** Moving from a monolithic hackathon script to a professional Elixir/Phoenix architecture allows the system to scale from 500 users to 5,000+ without a linear increase in administrative overhead.

**Projected Total Annual Savings/Gain:** ~$463,200.  
**Payback Period:** Approximately 20.7 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Ironclad utilizes a traditional three-tier architecture, optimized for the high-concurrency requirements of telecommunications data streams.

*   **Presentation Layer:** Built using **Phoenix LiveView**. This allows for real-time updates of marketplace pricing, order status, and workflow execution without the overhead of a heavy JavaScript framework. It provides the "snappy" feel required for a productivity tool.
*   **Business Logic Layer:** Developed in **Elixir**. The BEAM VM is chosen specifically for its fault tolerance and ability to handle thousands of concurrent processes (GenServers) to manage individual subscription timers and webhook listeners.
*   **Data Layer:** **PostgreSQL** serves as the primary relational store. Given the regulatory requirements, data is partitioned to ensure strict multi-tenant isolation.

### 2.2 Infrastructure & Deployment
The application is hosted on **Fly.io**, utilizing their global edge network to keep data closer to the end-users while maintaining a centralized primary database. To comply with GDPR and CCPA, the primary database and all backups are pinned to EU-based regions (e.g., `ams` or `fra`).

### 2.3 ASCII Architecture Diagram
```text
[ User Browser ] <--- WebSocket (Phoenix Channels) ---> [ LiveView Presentation ]
                                                               |
                                                               v
[ External API ] <--- HTTP/JSON ---> [ Business Logic (Elixir/Phoenix) ]
                                              |                |
       _______________________________________|                |
      |                                                         |
[ Workflow Engine ] <--- [ Rule Builder ]             [ Auth/Security Layer ]
      |                                                          |
      |                                                          |
      v                                                          v
[ PostgreSQL DB ] <--- [ Tenant Schema Isolation ] <--- [ Hardware Key Auth ]
      |
      +--> [ EU-West-1 Residency ]
      +--> [ Encrypted Volume ]
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-Tenant Data Isolation (Priority: High | Status: In Progress)
**Objective:** Ensure that data belonging to different organizational units or external partners is logically and physically separated to prevent cross-tenant data leakage, satisfying GDPR/CCPA requirements.

**Functional Specifications:**
Ironclad employs a "Shared Database, Separate Schema" approach. Each tenant is assigned a unique `tenant_id` (UUID). Upon request, the Phoenix controller identifies the tenant via the subdomain or a secure session cookie and switches the PostgreSQL search path to the corresponding schema.

*   **Tenant Onboarding:** When a new department is onboarded, a migration script creates a new schema and populates the mandatory base tables (Users, Roles, Settings).
*   **Data Residency:** The system must verify that the `tenant_location` attribute is set to `EU` before allowing the creation of a tenant on the EU cluster.
*   **Cross-Tenant Queries:** Only users with the `Global_Admin` role may execute queries across schemas, utilizing a specialized `cross_tenant_query` module that logs every access attempt for audit purposes.

**Technical Constraints:**
*   Maximum of 1,000 schemas per database instance to avoid PostgreSQL catalog bloat.
*   Use of `foreign_key` constraints across schemas is prohibited; relationships must be managed at the application level via the `tenant_id`.

### 3.2 Workflow Automation Engine with Visual Rule Builder (Priority: High | Status: In Review)
**Objective:** Allow non-technical administrators to create "If-This-Then-That" (IFTTT) logic for provisioning telecom services.

**Functional Specifications:**
The Visual Rule Builder is a drag-and-drop interface where users can define triggers (e.g., "Order Placed") and actions (e.g., "Send Email to Network Ops" and "Trigger API call to Carrier").

*   **The Logic Graph:** Rules are stored as Directed Acyclic Graphs (DAGs) in the database.
*   **Trigger Types:**
    *   *Event-based:* Order status change, payment failure, user registration.
    *   *Schedule-based:* Weekly audit checks, monthly subscription renewals.
*   **Action Types:**
    *   *Internal:* Update record, change user permission.
    *   *External:* Trigger webhook, send Slack notification.

**Technical Constraints:**
To prevent infinite loops (e.g., Action A triggers Trigger B which triggers Action A), the engine implements a "Max Recursion Depth" of 5. If a workflow exceeds 5 levels of nesting, the process is killed, and an alert is sent to the system admin.

### 3.3 Two-Factor Authentication with Hardware Key Support (Priority: Critical | Status: In Progress)
**Objective:** Secure internal telecom infrastructure access by mandating MFA, specifically supporting FIDO2/WebAuthn hardware keys (e.g., YubiKey).

**Functional Specifications:**
This is a **Launch Blocker**. Given the sensitivity of the telecommunications data, standard SMS-based 2FA is deemed insufficient.

*   **Registration Flow:** Users navigate to `/settings/security`. They are prompted to register a hardware key. The server sends a challenge; the key signs it; the server verifies the signature and stores the public key.
*   **Authentication Flow:** After password verification, the system checks if the user has a registered hardware key. If so, a challenge is issued. The user must physically touch the key to complete the login.
*   **Recovery Codes:** Upon setup, 10 single-use backup codes are generated. These are hashed using Argon2 and stored in the database.

**Technical Constraints:**
*   Compliance with WebAuthn L2 standards.
*   Hardware keys must be compatible with USB-C and NFC for mobile admins.

### 3.4 Automated Billing and Subscription Management (Priority: Medium | Status: Complete)
**Objective:** Automate the lifecycle of service subscriptions and generate invoices based on usage metrics.

**Functional Specifications:**
This module handles the transition from "Trial" to "Paid" status and manages recurring monthly charges.

*   **Billing Cycles:** Supports monthly and annual billing.
*   **Tiered Pricing:** Integration of a pricing table where costs fluctuate based on the number of active circuits (e.g., 1-10 circuits = $50/ea, 11-50 = $40/ea).
*   **Dunning Process:** If a payment fails, the system triggers a 3-step dunning sequence:
    1.  Day 1: Email notification.
    2.  Day 7: Warning that service will be suspended.
    3.  Day 14: Move tenant to `read-only` mode.

**Technical Constraints:**
*   Integration with a payment gateway (Stripe/Braintree) via a secure vault.
*   All currency calculations must use the `Decimal` type to avoid floating-point errors.

### 3.5 Webhook Integration Framework (Priority: Low | Status: In Progress)
**Objective:** Provide a way for third-party external tools (like ServiceNow or Jira) to receive real-time notifications from Ironclad.

**Functional Specifications:**
A "nice to have" feature that allows tenants to register a URL that Ironclad will "ping" whenever a specific event occurs.

*   **Event Selection:** Users can check boxes for events they want to track (e.g., `order.created`, `subscription.cancelled`).
*   **Payload Format:** Standard JSON payload including `event_type`, `timestamp`, and the `resource_id`.
*   **Retry Logic:** If the third-party endpoint returns a non-200 status code, Ironclad will retry with exponential backoff (1m, 10m, 1h, 24h).

**Technical Constraints:**
*   To prevent the "noisy neighbor" problem, webhooks are processed in a separate background queue using `Oban`.
*   Payloads must be signed with an `X-Ironclad-Signature` HMAC header to ensure authenticity.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1`. All requests require a `Bearer <token>` in the Authorization header.

### 4.1 GET `/api/v1/tenants/:tenant_id/services`
**Description:** Retrieves a list of all telecom services provisioned for a specific tenant.
*   **Request Parameters:** `limit` (int), `offset` (int).
*   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "data": [
        { "id": "svc_9921", "name": "Fiber Link A", "status": "active", "price": 120.00 },
        { "id": "svc_9922", "name": "Cloud Firewall", "status": "pending", "price": 45.00 }
      ],
      "pagination": { "total": 2, "next": "/api/v1/tenants/123/services?offset=2" }
    }
    ```

### 4.2 POST `/api/v1/orders`
**Description:** Creates a new order for a telecom service.
*   **Request Body:**
    ```json
    {
      "service_id": "svc_445",
      "quantity": 1,
      "billing_cycle": "monthly",
      "tenant_id": "tnt_882"
    }
    ```
*   **Response (201 Created):**
    ```json
    { "order_id": "ord_7712", "estimated_delivery": "2025-11-01", "status": "queued" }
    ```

### 4.3 PUT `/api/v1/workflow/rules/:rule_id`
**Description:** Updates the logic of a specific automation rule.
*   **Request Body:**
    ```json
    {
      "trigger": "payment.failed",
      "action": "notify.slack",
      "channel_id": "C12345",
      "message": "Payment failed for tenant {{tenant_name}}"
    }
    ```
*   **Response (200 OK):** `{ "status": "updated", "rule_id": "rule_001" }`

### 4.4 GET `/api/v1/auth/mfa/verify`
**Description:** Verifies the hardware key challenge response.
*   **Request Body:**
    ```json
    {
      "credentialId": "base64_encoded_id",
      "signature": "base64_encoded_sig",
      "clientDataJSON": "base64_encoded_json"
    }
    ```
*   **Response (200 OK):** `{ "authenticated": true, "session_token": "jwt_token_here" }`

### 4.5 DELETE `/api/v1/tenants/:tenant_id/subscriptions/:sub_id`
**Description:** Cancels a specific subscription.
*   **Response (204 No Content):** Empty body.

### 4.6 POST `/api/v1/webhooks/register`
**Description:** Registers a new webhook endpoint.
*   **Request Body:**
    ```json
    {
      "target_url": "https://partner.com/webhook",
      "events": ["order.completed", "user.deleted"]
    }
    ```
*   **Response (201 Created):** `{ "webhook_id": "wh_552", "secret": "whsec_abc123" }`

### 4.7 GET `/api/v1/billing/invoice/:invoice_id`
**Description:** Retrieves a PDF link and metadata for a specific invoice.
*   **Response (200 OK):**
    ```json
    { "invoice_id": "inv_101", "amount": 450.00, "pdf_url": "https://s3.eu-west-1.amazonaws.com/inv_101.pdf" }
    ```

### 4.8 PATCH `/api/v1/tenants/:tenant_id/settings`
**Description:** Updates tenant-wide configuration.
*   **Request Body:** `{ "data_residency": "EU", "timezone": "CET" }`
*   **Response (200 OK):** `{ "status": "success" }`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15. All timestamps are stored in UTC.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `id` (UUID) | None | `name`, `slug`, `residency` | The core entity for multi-tenancy. |
| `users` | `id` (UUID) | `tenant_id` | `email`, `password_hash`, `role` | User credentials and tenant mapping. |
| `services` | `id` (UUID) | None | `sku`, `name`, `base_price` | Catalog of available telecom assets. |
| `subscriptions`| `id` (UUID) | `tenant_id`, `service_id` | `start_date`, `status`, `tier` | Active service agreements. |
| `orders` | `id` (UUID) | `tenant_id`, `user_id` | `total_amount`, `status` | Order transaction history. |
| `mfa_keys` | `id` (UUID) | `user_id` | `public_key`, `credential_id` | FIDO2 hardware key public data. |
| `workflow_rules`| `id` (UUID) | `tenant_id` | `trigger_event`, `action_json` | DAG definitions for automation. |
| `invoices` | `id` (UUID) | `subscription_id` | `amount`, `due_date`, `paid_at` | Billing records. |
| `webhooks` | `id` (UUID) | `tenant_id` | `target_url`, `secret_token` | Third-party integration targets. |
| `audit_logs` | `id` (BIGINT) | `tenant_id`, `user_id` | `action`, `ip_address` | Immutable log of all system changes. |

### 5.2 Relationships
*   **One-to-Many:** `tenants` $\to$ `users` (A tenant has many users).
*   **One-to-Many:** `tenants` $\to$ `subscriptions` (A tenant manages multiple services).
*   **Many-to-One:** `orders` $\to$ `users` (Many orders can be placed by one user).
*   **One-to-One:** `users` $\to$ `mfa_keys` (Usually one primary hardware key per user).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments to ensure stability and regulatory compliance.

#### 6.1.1 Development (`dev`)
*   **Purpose:** Feature iteration and developer sandbox.
*   **Infrastructure:** Local Docker containers and a shared "Dev" cluster on Fly.io.
*   **Data:** Anonymized seed data; no real production PII.
*   **Deployment:** Continuous deployment on every merge to the `develop` branch.

#### 6.1.2 Staging (`stage`)
*   **Purpose:** QA, UAT (User Acceptance Testing), and Regulatory Pre-review.
*   **Infrastructure:** Mirrors production hardware specs.
*   **Data:** A sanitized clone of production data (obfuscated).
*   **Deployment:** Bi-weekly releases from the `release` branch.

#### 6.1.3 Production (`prod`)
*   **Purpose:** Live end-user environment.
*   **Infrastructure:** Multi-region Fly.io clusters with EU-pinned data residency.
*   **Data:** Real customer data; encrypted at rest (AES-256).
*   **Deployment:** **Quarterly releases** aligned with regulatory review cycles. This rigid schedule is required to ensure the "Ironclad" compliance audit is completed before new features hit production.

### 6.2 CI/CD Pipeline
The pipeline uses GitHub Actions. The flow is:
`Feature Branch` $\to$ `Pull Request` $\to$ `CI Suite (ExUnit)` $\to$ `Merge to Develop` $\to$ `Deploy to Dev` $\to$ `Merge to Release` $\to$ `Deploy to Stage` $\to$ `Quarterly Manual Approval` $\to$ `Deploy to Prod`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tool:** `ExUnit`.
*   **Scope:** Every single function in the business logic layer must have a corresponding test file.
*   **Coverage Target:** 90% line coverage. Focus is on the `Billing` and `Workflow` modules where logic errors are most costly.

### 7.2 Integration Testing
*   **Tool:** `Wallaby.js` (for LiveView components) and custom Elixir integration tests.
*   **Scope:** Testing the interaction between the Phoenix controllers and the PostgreSQL database. Specifically, verifying that the `tenant_id` isolation is working and that users cannot access data from other schemas.
*   **Key Test Case:** "User A from Tenant 1 attempts to GET `/api/v1/tenants/Tenant2/services` $\to$ Expected: 403 Forbidden."

### 7.3 End-to-End (E2E) Testing
*   **Tool:** `Playwright`.
*   **Scope:** Critical user journeys (The "Happy Path").
    *   Login $\to$ Register Hardware Key $\to$ Purchase Service $\to$ Create Workflow Rule $\to$ Verify Billing.
*   **Execution:** Run daily against the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | High | High | Hire a specialized contractor to reduce the "bus factor" and handle overflow, allowing for a reduction in full-time headcount if necessary. |
| R-02 | Partner API is undocumented and buggy | Medium | High | Ravi Kim to dedicate 10% of sprint time to reverse-engineering the API and documenting workarounds in the internal Wiki. |
| R-03 | Regulatory review delays quarterly release | Medium | Medium | Maintain a "Hotfix" branch for critical security patches that can bypass the quarterly cycle with emergency approval. |
| R-04 | Technical debt (Hardcoded values in 40+ files) | High | Medium | Implement a `Config` module and a phased migration to move all hardcoded strings/IPs into environment variables. |

### 8.1 Probability/Impact Matrix
*   **Critical:** (R-01) $\to$ High Prob / High Impact.
*   **High:** (R-02, R-04) $\to$ Med Prob / High Impact.
*   **Medium:** (R-03) $\to$ Med Prob / Med Impact.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
**Phase 1: Foundation & Security (Months 1-2)**
*   Focus: MFA implementation, Tenant isolation, and Database migration.
*   Dependency: Hardware key procurement for the dev team.

**Phase 2: Commerce & Billing (Months 3-4)**
*   Focus: Subscription engine, Payment gateway integration, and Order API.
*   Dependency: Completion of the Billing module.

**Phase 3: Automation & Optimization (Months 5-6)**
*   Focus: Visual Rule Builder and Webhook framework.
*   Dependency: Stable order flow.

### 9.2 Key Milestones
1.  **Milestone 1: First paying customer onboarded**
    *   *Target Date:* 2025-08-15
    *   *Requirement:* Billing and Tenant isolation must be in Production.
2.  **Milestone 2: Performance benchmarks met**
    *   *Target Date:* 2025-10-15
    *   *Requirement:* Support 5,000 concurrent users with $<200\text{ms}$ response time.
3.  **Milestone 3: Architecture review complete**
    *   *Target Date:* 2025-12-15
    *   *Requirement:* Final sign-off from CTO Chioma Stein and external auditors.

---

## 10. MEETING NOTES (Running Log)

*Note: These notes are extracted from the 200-page unsearchable shared document.*

### Meeting 1: Sprint Kickoff - "The Friction Point"
**Date:** 2023-11-02
**Attendees:** Chioma Stein, Ravi Kim, Anders Park, Valentina Jensen.
**Discussion:**
*   Chioma emphasizes that the "hackathon" days are over. The tool must now be "Ironclad."
*   Valentina raises a concern about the hardcoded API keys in the `config/` files. Chioma acknowledges but tells her to focus on the MFA module first.
*   **Decision:** MFA is now a "Launch Blocker." No one gets access to the production build without a YubiKey.

### Meeting 2: The "Silence" Sync
**Date:** 2023-11-15
**Attendees:** Chioma Stein, Ravi Kim, Anders Park.
**Discussion:**
*   Tension is high. The Project Manager (PM) and Lead Engineer (LE) are not speaking.
*   Ravi reports that the integration partner's API returns 500 errors for 20% of requests and has no documentation.
*   Anders is frustrated that he's receiving builds for QA that fail on the first login screen.
*   **Decision:** Ravi will create a "Workaround Document" for the buggy API. Chioma will attempt to mediate between the PM and LE, though no progress is made.

### Meeting 3: Blocker Resolution
**Date:** 2023-11-29
**Attendees:** All hands.
**Discussion:**
*   Current Blocker: The "Network Infrastructure Team" is 3 weeks behind on delivering the VLAN assignment API. Ironclad cannot provision services without this.
*   Valentina suggests mocking the API to continue development.
*   **Decision:** The team will implement a "Mock Provider" in the business logic layer. Once the other team delivers, a simple switch in the `.env` file will toggle from `MOCK` to `LIVE`.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$800,000**

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | Salaries for 20+ people across 3 departments. |
| **Infrastructure** | 15% | $120,000 | Fly.io hosting, PostgreSQL managed instances, S3 buckets. |
| **Tools & Licenses** | 5% | $40,000 | YubiKey hardware for staff, Playwright/Wallaby licenses, Monitoring tools. |
| **Contingency** | 10% | $80,000 | Reserve for emergency contractor hires if budget cuts occur. |

---

## 12. APPENDICES

### Appendix A: Hardcoded Configuration Audit
The following files have been identified as containing hardcoded values that must be migrated to the environment configuration:
1.  `lib/ironclad/api_client.ex` (API Keys)
2.  `config/runtime.exs` (DB Passwords)
3.  `lib/ironclad/billing/stripe_worker.ex` (Webhook Secrets)
4.  `lib/ironclad/auth/mfa_service.ex` (Salt values)
*... [Total 40+ files identified]*

### Appendix B: Regulatory Data Residency Mapping
To satisfy GDPR, the following mapping is enforced at the infrastructure level:
*   **Tenant Region: EU** $\to$ Fly.io Region: `ams` (Amsterdam) / `fra` (Frankfurt).
*   **Tenant Region: US** $\to$ Fly.io Region: `iad` (Northern Virginia).
*   **Backup Policy:** Daily snapshots stored in the same region as the primary database. Cross-region replication is disabled for EU tenants.