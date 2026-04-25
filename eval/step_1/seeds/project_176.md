Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional technical specification. 

***

# PROJECT SPECIFICATION: PROJECT LODESTAR
**Document Version:** 1.0.4  
**Status:** Active / Urgent  
**Last Updated:** 2024-11-01  
**Classification:** Confidential / Internal (Talus Innovations)  
**Project Owner:** Darian Costa (CTO)  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Lodestar is a mission-critical fintech payment processing system developed by Talus Innovations, specifically engineered for the renewable energy sector. The primary objective of Lodestar is to modernize the financial transaction layer for energy production credits and subscription-based utility billing. 

Unlike standard payment gateways, Lodestar must handle complex regulatory requirements unique to the renewable energy industry, including carbon credit offsets, state-level energy subsidies, and multi-tenant billing structures. This project is not merely a feature upgrade; it is a regulatory compliance mandate. Failure to deploy a fully audited, tamper-evident payment system within the six-month window will result in severe legal penalties and the potential loss of operational licenses in key markets.

### 1.2 Business Justification
The renewable energy market is shifting toward "Energy-as-a-Service" (EaaS) models. Current legacy systems at Talus Innovations rely on manual invoicing and disparate spreadsheets, leading to a 12% leakage in revenue due to billing errors and uncaptured subsidies. Lodestar will automate these processes, ensuring 100% capture of billable events.

Furthermore, the regulatory landscape (specifically under the new Green Finance Compliance Act) requires that all payment processing systems provide an immutable audit trail. The current system is non-compliant. Lodestar implements a CQRS (Command Query Responsibility Segregation) architecture with Event Sourcing, ensuring that every financial state change is recorded as a discrete, immutable event.

### 1.3 ROI Projection
The projected Return on Investment for Project Lodestar is calculated across three primary vectors over a 36-month horizon:

1.  **Regulatory Risk Mitigation:** Avoidance of projected fines ranging from $1.2M to $4.5M per annum for non-compliance.
2.  **Operational Efficiency:** Reduction of the billing cycle from 15 days to near-real-time, reducing Days Sales Outstanding (DSO) by an estimated 22%.
3.  **Revenue Capture:** Recovery of the 12% leakage via automated subscription management, projected to add $850,000 in annual recurring revenue (ARR).

Total projected 3-year ROI is estimated at 410%, with the break-even point occurring 8 months post-launch.

### 1.4 Strategic Alignment
Lodestar serves as the flagship initiative for Talus Innovations' 2025 fiscal strategy. Reporting for this project occurs at the Board level, meaning any slippage in the timeline is escalated immediately to the executive steering committee. Given the $5M+ budget and the high stakes, the project follows a strict formal communication protocol managed by CTO Darian Costa.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Lodestar is built on the principle of "Correctness First." Given the financial nature of the system, we have opted for a Rust backend to ensure memory safety and concurrency without data races. To handle the scale of renewable energy telemetry data while maintaining low latency at the edge, we utilize Cloudflare Workers and SQLite for edge-caching of read-models.

The system utilizes **CQRS (Command Query Responsibility Segregation)**. This separates the "write" operations (Commands) from the "read" operations (Queries). For the audit-critical domains (Payment Processing and Ledgering), we employ **Event Sourcing**. Instead of storing only the current state of a balance, we store the sequence of events that led to that state.

### 2.2 High-Level Architecture Diagram (ASCII)

```text
[ USER INTERFACE ] <---> [ API GATEWAY / CF WORKERS ] <---> [ AUTH LAYER ]
       (React)               (Routing/Caching)             (ISO 27001)
                                     |
                                     v
                      _______________________________
                     |      COMMAND SIDE (Rust)      |
                     |-------------------------------|
                     |  API Endpoints -> Command Bus  |
                     |  Validation -> Event Store     |
                     |_______________________________|
                                     |
                                     v (Event Stream)
                      _______________________________
                     |       QUERY SIDE (Rust)        |
                     |-------------------------------|
                     |  Event Projections -> Read DB  |
                     |  SQLite (Edge) / Postgres    |
                     |_______________________________|
                                     |
                                     v
                      _______________________________
                     |      EXTERNAL INTEGRATIONS    |
                     |-------------------------------|
                     |  Payment Gateways | Regulators |
                     |_______________________________|
```

### 2.3 Component Deep Dive
- **Backend (Rust):** Leveraging the `Actix-web` framework for high-throughput asynchronous processing. Rust was chosen to eliminate "null pointer" exceptions and provide the performance required for p95 < 200ms.
- **Frontend (React):** A TypeScript-based React application utilizing Tailwind CSS for a high-density financial dashboard.
- **Edge Layer (Cloudflare Workers):** Used for distributing read-only data (e.g., subscription status) to the edge, reducing the load on the central database.
- **Storage (SQLite/Event Store):** SQLite is utilized at the edge for temporary state and configuration, while the primary Event Store utilizes a write-ahead log (WAL) to ensure data integrity.
- **Security:** The environment is ISO 27001 certified. This includes encrypted data-at-rest (AES-256) and data-in-transit (TLS 1.3), with hardware security modules (HSM) for signing financial transactions.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** High | **Status:** Blocked
**Description:** 
This module manages the lifecycle of a customer’s financial relationship with Talus Innovations. It handles the creation of subscription plans, automated recurring billing, and the calculation of variable energy usage costs.

**Functional Requirements:**
- **Plan Management:** Ability to define "Tiered," "Flat-rate," and "Usage-based" pricing models.
- **Billing Cycles:** Support for monthly, quarterly, and annual billing intervals with automated invoice generation.
- **Dunning Process:** An automated system to handle failed payments, including retry logic (3 attempts over 14 days) and notification triggers.
- **Proration Engine:** Automatic calculation of credits and debits when a user upgrades or downgrades a plan mid-cycle.

**Detailed Logic:**
The system must interface with the energy meter telemetry data to calculate usage-based billing. The `BillingEngine` will trigger on the 1st of every month, querying the `UsageEventStore` to aggregate total kWh consumed. This sum is multiplied by the current rate defined in the `SubscriptionPlan` table.

**Blocking Issue:** 
This feature is currently blocked by the third-party payment gateway's API rate limits, preventing the testing of high-volume recurring billing batches.

---

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Blocked
**Description:** 
A regulatory requirement that ensures every modification to a financial record is logged and cannot be altered or deleted without detection. This is the core "Proof of Compliance" for the project.

**Functional Requirements:**
- **Immutable Logs:** Every write operation must create a log entry in the `AuditLog` table.
- **Cryptographic Chaining:** Each log entry must contain a SHA-256 hash of the previous entry, creating a blockchain-like structure.
- **Tamper Detection:** A background worker must periodically validate the chain of hashes. If a mismatch is found, an immediate alert is sent to the Security Engineer (Yonas Park).
- **Regulatory Export:** Ability to generate a signed PDF report of all transactions for a specific entity over a specific timeframe.

**Detailed Logic:**
When a command (e.g., `UpdateBalance`) is executed, the system generates an `AuditEvent`. This event contains: `Timestamp`, `UserID`, `OperationID`, `PayloadBefore`, `PayloadAfter`, and `PreviousHash`. The `CurrentHash` is then calculated as `Hash(Payload + PreviousHash)`.

**Blocking Issue:**
Blocked by the lack of a finalized specification for the regulatory reporting format from the governing body.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical | **Status:** Complete
**Description:** 
The "Brain" of Lodestar. This allows non-technical operators to define business logic for payment routing and compliance checks via a drag-and-drop interface.

**Functional Requirements:**
- **Visual Canvas:** A React-based flow chart where nodes represent actions (e.g., "Send Email," "Charge Card," "Wait 24h") and edges represent conditional logic.
- **Trigger System:** Workflows can be triggered by events (e.g., `PaymentFailed`, `NewUserRegistered`).
- **Variable Injection:** Ability to use placeholders like `{{customer_email}}` or `{{invoice_amount}}` within the workflow.
- **Version Control:** Every change to a workflow must be versioned, allowing a roll-back to a previous logic state.

**Technical Implementation:**
The visual builder generates a JSON representation of the graph. The Rust backend parses this JSON into a Directed Acyclic Graph (DAG) and executes it using a state machine. Since this is a launch-blocker and is marked "Complete," it has passed all QA cycles.

---

### 3.4 Webhook Integration Framework
**Priority:** Low | **Status:** Blocked
**Description:** 
A system to notify third-party tools (e.g., CRM, Accounting software) when specific events occur within Lodestar.

**Functional Requirements:**
- **Endpoint Registration:** Users can register a URL to receive POST requests.
- **Event Selection:** Users can choose which events they want to subscribe to (e.g., `subscription.created`, `payment.refunded`).
- **Retry Logic:** Exponential backoff for failed deliveries (1m, 5m, 15m, 1h, 24h).
- **Security Signing:** Every webhook payload must be signed with an HMAC-SHA256 signature in the header for verification by the receiver.

**Detailed Logic:**
When an event is persisted to the Event Store, the `WebhookDispatcher` identifies all active subscriptions for that event type. It queues the payload into a Redis-backed message queue to ensure that the main payment flow is not delayed by slow third-party endpoints.

**Blocking Issue:**
Blocked by the instability of the integration partner's API, which frequently returns 500 errors during webhook handshake tests.

---

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** Complete
**Description:** 
A high-level operational overview for Talus Innovations executives to monitor the health of the payment system and financial metrics.

**Functional Requirements:**
- **Widget Library:** A set of pre-built components (e.g., "Revenue Heatmap," "Pending Approvals," "System Latency").
- **Layout Persistence:** Users can drag and resize widgets; the layout is saved to the user's profile in the database.
- **Real-time Updates:** Integration with WebSockets to update financial totals without page refreshes.
- **Role-Based Access:** Different widgets are visible based on user permissions (e.g., the CTO sees system health; the CFO sees revenue).

**Technical Implementation:**
Implemented using `react-grid-layout`. The backend provides a dedicated `/api/v1/dashboard/metrics` endpoint that aggregates data from the Query side of the CQRS architecture to ensure sub-second load times.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a Bearer Token in the Authorization header. Base URL: `https://api.lodestar.talus.io/v1`.

### 4.1 `POST /payments/process`
**Description:** Initiates a new payment transaction.
- **Request Body:**
  ```json
  {
    "amount": 1250.00,
    "currency": "USD",
    "source_id": "src_998877",
    "customer_id": "cust_12345",
    "idempotency_key": "unique-req-id-001"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "transaction_id": "tx_556677",
    "status": "processing",
    "created_at": "2025-05-01T10:00:00Z"
  }
  ```

### 4.2 `GET /subscriptions/{sub_id}`
**Description:** Retrieves the current state of a subscription.
- **Response (200 OK):**
  ```json
  {
    "id": "sub_123",
    "plan": "enterprise_renewable",
    "status": "active",
    "next_billing_date": "2025-06-01"
  }
  ```

### 4.3 `POST /billing/invoice`
**Description:** Manually triggers the generation of an invoice.
- **Request Body:** `{ "customer_id": "cust_123" }`
- **Response (200 OK):** `{ "invoice_url": "https://lodestar.io/inv/8899" }`

### 4.4 `GET /audit/logs`
**Description:** Returns a paginated list of audit events.
- **Query Params:** `?start_date=2025-01-01&end_date=2025-01-31&page=1`
- **Response (200 OK):**
  ```json
  {
    "logs": [{ "event_id": "evt_1", "action": "UPDATE_BALANCE", "hash": "a1b2c3..." }],
    "next_page": 2
  }
  ```

### 4.5 `PUT /workflows/{wf_id}/publish`
**Description:** Deploys a visual rule builder configuration to production.
- **Request Body:** `{ "version": "2.1.0", "description": "Updated tax logic" }`
- **Response (200 OK):** `{ "status": "published", "deployed_at": "..." }`

### 4.6 `GET /dashboard/widgets/layout`
**Description:** Retrieves the user's saved dashboard configuration.
- **Response (200 OK):** `{ "layout": [{ "i": "rev_map", "x": 0, "y": 0, "w": 4, "h": 2 }] }`

### 4.7 `POST /webhooks/register`
**Description:** Subscribes a URL to specific event types.
- **Request Body:**
  ```json
  {
    "target_url": "https://partner.com/webhook",
    "events": ["payment.success", "payment.failed"]
  }
  ```
- **Response (201 Created):** `{ "webhook_id": "wh_990" }`

### 4.8 `DELETE /subscriptions/{sub_id}`
**Description:** Cancels a subscription.
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

Lodestar uses a hybrid approach: a relational database for state and an event store for history.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role` | One-to-Many with `subscriptions` |
| `subscriptions` | `sub_id` | `user_id`, `plan_id`, `status`, `start_date` | Many-to-One with `plans` |
| `plans` | `plan_id` | `name`, `monthly_cost`, `billing_type` | One-to-Many with `subscriptions` |
| `transactions` | `tx_id` | `sub_id`, `amount`, `currency`, `status` | Many-to-One with `subscriptions` |
| `event_store` | `event_id` | `aggregate_id`, `event_type`, `payload`, `version` | The source of truth for all states |
| `audit_logs` | `log_id` | `tx_id`, `timestamp`, `prev_hash`, `curr_hash` | One-to-One with `event_store` |
| `workflows` | `wf_id` | `name`, `json_definition`, `version`, `is_active` | N/A |
| `webhook_configs`| `wh_id` | `target_url`, `secret_key`, `is_enabled` | Many-to-Many with `event_types` |
| `event_types` | `type_id` | `event_name` (e.g., "payment.failed") | N/A |
| `user_layouts` | `layout_id` | `user_id`, `json_config` | One-to-One with `users` |

### 5.2 Relationship Logic
- **The Event Store** is the primary write target. Whenever a `transaction` is updated, a row is added to `event_store`, which then triggers an update to the `transactions` read-table.
- **The Audit Log** acts as a secondary wrapper around the `event_store`, adding the cryptographic hashing layer.
- **User Layouts** are stored as JSON blobs to allow for flexible widget configurations without altering the schema.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lodestar employs a strictly segregated three-tier environment strategy to meet ISO 27001 requirements.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Dockerized containers running on local workstations and a shared staging cluster.
- **Data:** Anonymized synthetic data.
- **Deployment:** Continuous Integration (CI) on every push to `dev` branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing and Stakeholder UAT (User Acceptance Testing).
- **Infrastructure:** A mirror of the production environment hosted on Cloudflare Workers and a dedicated Rust-cluster.
- **Data:** Sanitized production snapshots.
- **Deployment:** Weekly merges from `dev` to `staging` after passing the automated test suite.

#### 6.1.3 Production (Prod)
- **Purpose:** Live financial processing.
- **Infrastructure:** Multi-region deployment with failover capabilities. All traffic routed through Cloudflare for DDoS protection.
- **Data:** Encrypted live financial data.
- **Deployment:** Quarterly releases. No code enters Production without a sign-off from Darian Costa (CTO) and a successful regulatory review.

### 6.2 CI/CD Pipeline
1. **Build:** Rust binaries are compiled and optimized using `cargo build --release`.
2. **Test:** Execution of the full test suite (Unit $\rightarrow$ Integration $\rightarrow$ E2E).
3. **Security Scan:** Mandatory `cargo audit` and `snyk` scans for dependency vulnerabilities.
4. **Deploy:** Blue-Green deployment to ensure zero-downtime updates.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and logic blocks (e.g., the proration calculator).
- **Requirement:** 80% code coverage minimum for the Rust backend.
- **Tooling:** `cargo test`.

### 7.2 Integration Testing
- **Scope:** Interaction between components (e.g., API $\rightarrow$ Event Store $\rightarrow$ Read Model).
- **Focus:** Testing the CQRS lag. We must ensure that once a command is processed, the query side is updated within 100ms.
- **Tooling:** Postman/Newman collections.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Complete user journeys (e.g., User signs up $\rightarrow$ selects plan $\rightarrow$ payment processed $\rightarrow$ dashboard updates).
- **Tooling:** Playwright for frontend flow validation.
- **Environment:** Conducted exclusively in the Staging environment.

### 7.4 Performance Testing
- **Target:** p95 response time < 200ms.
- **Method:** Load testing using `k6` to simulate 10,000 concurrent requests per second, simulating a "billing day" spike.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Budget cut by 30% in next fiscal quarter | Medium | High | Escalate to steering committee; prioritize critical items (Workflow Engine) and de-scope "nice-to-haves" (Webhooks). |
| **R2** | Integration partner API is undocumented/buggy | High | High | Create an abstraction layer (Adapter Pattern) to isolate partner code. De-scope if unresolved by 2025-05-15. |
| **R3** | Failure to meet legal deadline (6 months) | Low | Critical | Implement "Crisis Mode" sprints; shift Lior Park (Contractor) to full-time support. |
| **R4** | Technical Debt (Hardcoded configs in 40+ files) | High | Medium | Dedicated "Cleanup Sprint" scheduled for February 2025 to move all configs to a centralized `.env` and Secret Manager. |

---

## 9. TIMELINE

### 9.1 Project Phases

| Phase | Duration | Key Activities | Dependencies |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Month 1-2 | Infrastructure setup, ISO 27001 audit, Workflow Engine completion. | None |
| **Phase 2: Core Dev** | Month 3-4 | Billing Engine, Audit Trail, Dashboard refinement. | Phase 1 |
| **Phase 3: Integration** | Month 5 | API integrations, Webhook framework, E2E testing. | Phase 2, Partner API |
| **Phase 4: Compliance** | Month 6 | Final regulatory review, Load testing, Production rollout. | Phase 3 |

### 9.2 Critical Milestones
- **Milestone 1 (2025-05-15): Stakeholder Demo and Sign-off.** 
  - *Requirement:* All "Critical" and "High" priority features must be functional in Staging.
- **Milestone 2 (2025-07-15): Post-launch Stability Confirmed.** 
  - *Requirement:* Zero critical bugs in Production for 30 consecutive days.
- **Milestone 3 (2025-09-15): MVP Feature-Complete.** 
  - *Requirement:* All features, including "Low" priority webhooks, fully deployed.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per project guidelines, no formal meeting notes are kept. The following are synthesized from the project's decision-making Slack threads.*

### 10.1 Thread: #lodestar-dev (2024-11-10)
**Darian Costa:** "Umi, the dashboard widgets are looking great, but the latency on the revenue heatmap is hitting 400ms. We need that p95 under 200ms."
**Umi Liu:** "It's because we're querying the event store directly for the aggregate. I'll move it to the SQLite edge cache."
**Darian Costa:** "Agreed. Do it. Also, Yonas, where are we on the ISO 27001 checklist?"
**Yonas Park:** "Encryption is done. Waiting on the external auditor for the physical security sign-off on the data center."
**Decision:** Shift dashboard metrics to SQLite edge caching to meet performance targets.

### 10.2 Thread: #lodestar-blockers (2024-11-15)
**Lior Park:** "I can't test the recurring billing batch. The partner API is returning 429 (Too Many Requests) even though we're within the tier."
**Darian Costa:** "This is the third time this week. Yonas, can we implement a local mock server for the partner API so Lior can keep moving?"
**Yonas Park:** "Yes, I can spin up a Prism mock server by tomorrow."
**Decision:** Use a mock server for development to bypass partner API rate limits.

### 10.3 Thread: #lodestar-budget (2024-11-20)
**Darian Costa:** "Just got off the board call. There is a rumor that the Q2 budget might be slashed by 30%. We need to be lean."
**Umi Liu:** "Does that mean the Webhook framework is out?"
**Darian Costa:** "Likely. If the cut happens, we prioritize the Audit Trail and Billing. Webhooks are 'nice to have.' I'll escalate this to the steering committee to fight for the full $5M."
**Decision:** Mark Webhook framework as Low priority and a candidate for de-scoping.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | Salaries for Darian, Umi, Yonas, and Lior's contract fee. |
| **Infrastructure** | $600,000 | Cloudflare Enterprise, Rust-optimized clusters, HSM modules. |
| **Compliance & Tools** | $400,000 | ISO 27001 Certification, Snyk, Datadog, JIRA Enterprise. |
| **Contingency** | $800,000 | Reserved for emergency scaling or legal consulting. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following issues have been identified and must be resolved before Milestone 2:
1. **Config Leakage:** Hardcoded API keys and environment variables are scattered across 42 files (e.g., `src/config/constants.rs`, `src/utils/net.rs`).
2. **Error Handling:** Several modules use `unwrap()` instead of proper `Result` handling, posing a crash risk.
3. **Documentation:** The internal Rust crate documentation is missing for the `BillingEngine` module.

### Appendix B: ISO 27001 Compliance Matrix
| Requirement | Lodestar Implementation | Evidence |
| :--- | :--- | :--- |
| A.12.6.1 Management of Technical Vulnerabilities | Automated Snyk/Cargo-Audit scans on every PR. | CI Pipeline Logs |
| A.10.1.1 Policy on the use of Cryptographic Controls | AES-256 for data at rest; TLS 1.3 for transit. | Architecture Doc |
| A.9.2.3 Management of Privileged Access Rights | Role-Based Access Control (RBAC) via OAuth2. | User Table/Auth Log |