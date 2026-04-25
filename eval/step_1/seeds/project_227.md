# PROJECT SPECIFICATION: PROJECT JUNIPER
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Company:** Pivot North Engineering  
**Date:** October 26, 2023  
**Classification:** Confidential - PCI DSS Restricted

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Juniper is a strategic, "moonshot" Research and Development initiative commissioned by Pivot North Engineering. The objective is to architect and deploy a next-generation fintech payment processing system tailored specifically for the retail sector. Unlike standard payment gateways, Juniper is designed to integrate deeply into retail workflow automation, providing not just transaction processing but a comprehensive operational layer for merchants.

### 1.2 Business Justification
The retail payment landscape is currently dominated by legacy systems characterized by high transaction fees, rigid API structures, and poor developer experiences. Pivot North Engineering identifies a market gap for a high-performance, modular system that allows retailers to customize their payment flows via a visual automation engine while maintaining strict PCI DSS Level 1 compliance.

The project is categorized as a moonshot due to the high technical complexity and the inherent uncertainty of the Return on Investment (ROI). However, the project enjoys strong executive sponsorship, as a successful deployment would pivot the company from a service provider to a platform owner, creating a recurring revenue stream and significantly increasing the company's valuation.

### 1.3 ROI Projections
While the project is currently unfunded and bootstrapping via existing team capacity, the projected ROI is based on three primary levers:
1. **Reduction in Transaction Costs:** By bypassing several intermediary processors and optimizing the routing logic, Juniper aims to reduce the cost per transaction by 35% compared to the legacy systems currently used by our pilot retail partners.
2. **Market Expansion:** The ability to offer a "white-label" payment processing suite to mid-market retailers is projected to generate an Estimated Annual Recurring Revenue (ERR) of $2.4M within the first 18 months post-launch.
3. **Operational Efficiency:** Through the integrated workflow automation engine, retail clients are expected to reduce their manual reconciliation time by 60%, increasing the perceived value of the platform.

### 1.4 Strategic Alignment
Juniper aligns with Pivot North’s long-term goal of vertical integration. By controlling the payment rails, the company eliminates dependency on third-party fintech vendors whose pricing models are volatile and whose API stability is often inconsistent.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design Philosophy
Juniper utilizes a **Modular Monolith** architecture. The system is developed as a single deployable unit to minimize operational complexity during the R&D phase, but is strictly partitioned into domain-driven modules (e.g., `PaymentCore`, `TenantManager`, `WorkflowEngine`). This allows the team to transition to microservices incrementally as load increases or as specific domains require independent scaling.

### 2.2 Technology Stack
- **Language:** TypeScript (Strict Mode)
- **Frontend:** Next.js 14 (App Router)
- **ORM:** Prisma
- **Database:** PostgreSQL 15.4 (Managed instance)
- **Deployment:** Vercel (Edge Functions for low-latency routing)
- **Feature Management:** LaunchDarkly
- **Security:** PCI DSS Level 1 Certification (Hardware Security Modules - HSMs for key management)

### 2.3 Architecture Diagram (ASCII Representation)

```text
[ Client Layer ] <---> [ Vercel Edge Network ] <---> [ Next.js App Router ]
                                                            |
                                                            v
                                               [ Modular Monolith Core ]
                                               /            |            \
                   ___________________________/             |             \___________________________
                  |                                         |                                         |
        [ Tenant Isolation Module ]              [ Payment Processing Module ]             [ Workflow Automation Module ]
                  |                                         |                                         |
                  |                                         v                                         |
                  |                            [ PCI DSS Compliant Vault ]                            |
                  |                                         |                                         |
                  \_________________________________________|_________________________________________/
                                                            |
                                                            v
                                                [ Prisma / Raw SQL Layer ]
                                                            |
                                                   [ PostgreSQL Database ]
                                                (Multi-tenant Shared Schema)
```

### 2.4 Security Architecture
Because Juniper processes credit card data directly, the architecture adheres to **PCI DSS Level 1**. 
- **Data Encryption:** All PAN (Primary Account Numbers) are encrypted at the application level using AES-256-GCM before entering the database.
- **Key Rotation:** Keys are stored in a cloud-based HSM and rotated every 90 days.
- **Network Isolation:** The payment processing module resides in a restricted VPC with no direct public internet access; all requests must pass through a hardened API Gateway.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Juniper must support thousands of retail merchants (tenants) on a shared infrastructure. To ensure security and data privacy, the system implements a "Shared Schema, Row-Level Security (RLS)" approach. Every table in the database contains a `tenant_id` column.

**Functional Requirements:**
- **Isolation Enforcement:** The system must prevent "Cross-Tenant Data Leakage." A request from Tenant A must never be able to access data belonging to Tenant B, even if a developer forgets a `where` clause in a query.
- **Context Propagation:** The `tenant_id` must be extracted from the JWT (JSON Web Token) at the middleware level and injected into the Prisma context.
- **Performance:** RLS must not degrade query performance. Indexes must be composite, starting with `tenant_id`.

**Technical Implementation:**
We are implementing PostgreSQL Row Level Security policies. The application connects to the database using a limited-privilege user. Before executing a query, the application executes `SET app.current_tenant = 'tenant_id'`. The DB policy then filters all SELECT/UPDATE/DELETE operations based on this session variable.

**Acceptance Criteria:**
- Successful penetration test confirming that a modified API request cannot access another tenant's data.
- Latency overhead for RLS queries is $<10\text{ms}$.

---

### 3.2 Real-time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Complete

**Description:**
The retail dashboard allows multiple administrators to edit payment rules and store configurations simultaneously. This requires a real-time synchronization engine to prevent data loss and "last-write-wins" conflicts.

**Functional Requirements:**
- **Crdt Integration:** Use Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency across all clients.
- **Presence Indicators:** Show which users are currently editing a specific field.
- **Latency Compensation:** Local optimistic updates must be reflected immediately on the UI.

**Technical Implementation:**
The team implemented **Yjs**, a CRDT framework, integrated with a WebSocket provider. State changes are propagated as binary updates. When a user makes a change, the update is broadcast to other active sessions and persisted to the PostgreSQL database as a BLOB representing the document state.

**Acceptance Criteria:**
- Simultaneous edits by 5 users on a single configuration page result in a consistent final state across all screens.
- Sync latency remains under 100ms on a standard 4G connection.

---

### 3.3 A/B Testing Framework (Baked into Feature Flags)
**Priority:** Medium | **Status:** Blocked

**Description:**
To optimize checkout conversion rates for retailers, Juniper requires a built-in A/B testing framework. Rather than building a separate tool, this is integrated directly into the LaunchDarkly feature flag implementation.

**Functional Requirements:**
- **Targeting Rules:** Ability to assign users to "Variant A" or "Variant B" based on a hash of their `user_id`.
- **Metric Tracking:** Automatic tracking of conversion events (e.g., "Payment Completed") associated with a specific variant.
- **Statistically Significant Analysis:** A dashboard showing the lift in conversion for the winning variant.

**Technical Implementation:**
The system will utilize LaunchDarkly’s "Segments" feature. A middleware layer will intercept the user request, determine the assigned variant via the LD SDK, and inject the variant ID into the analytics event stream.

**Blocker:** Budget approval for the "Enterprise" tier of LaunchDarkly is pending; the current "Starter" tier does not support the required targeting granularity for A/B testing.

---

### 3.4 Offline-first Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Description:**
Retail environments (e.g., pop-up shops, warehouses) often have unstable internet. Juniper must allow merchants to process payments and manage configurations offline, syncing data once connectivity is restored.

**Functional Requirements:**
- **Local Persistence:** Use IndexedDB to store pending transactions and configuration changes.
- **Conflict Resolution:** When syncing, the system must handle conflicts using a "Timestamp-based Versioning" strategy.
- **Queue Management:** A background worker must manage the upload queue, ensuring "Exactly-Once" delivery of payment requests.

**Technical Implementation:**
The frontend will implement a Service Worker to intercept network requests. If the network is offline, requests are serialized into a "Sync Queue" in IndexedDB. Upon the `online` event, the worker iterates through the queue, sending requests with an `idempotency_key` to prevent duplicate charges.

**Blocker:** The team is currently struggling with the complexity of the idempotency logic across the modular monolith; architectural review is required.

---

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
A core value proposition of Juniper is the ability for retailers to create complex payment logic without writing code (e.g., "If transaction > $500 AND customer is VIP, apply 10% discount and route to Manual Review").

**Functional Requirements:**
- **Visual Canvas:** A drag-and-drop interface for creating logic flows.
- **Rule Engine:** A backend processor that evaluates these rules against incoming transaction data in real-time.
- **Trigger/Action Model:** Support for various triggers (Payment Received, Refund Requested) and actions (Send Email, Update Ledger, Trigger Refund).

**Technical Implementation:**
The visual builder generates a JSON representation of a Directed Acyclic Graph (DAG). The backend uses a custom interpreter that traverses this graph. To ensure performance, the rules are compiled into a simplified logic tree and cached in Redis.

**Acceptance Criteria:**
- A user can create a 3-step rule (Trigger $\rightarrow$ Condition $\rightarrow$ Action) and have it execute within 50ms of a transaction event.
- The visual builder supports undo/redo functionality.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication is handled via Bearer JWTs.

### 4.1 Create Payment Intent
`POST /payments/intent`
- **Description:** Initializes a payment process.
- **Request Body:**
```json
{
  "amount": 5000, 
  "currency": "USD",
  "payment_method": "card",
  "metadata": { "order_id": "ORD-123" }
}
```
- **Response (201 Created):**
```json
{
  "intent_id": "pi_987654321",
  "client_secret": "sec_xyz123",
  "status": "requires_payment_method"
}
```

### 4.2 Process Payment
`POST /payments/capture`
- **Description:** Finalizes the payment.
- **Request Body:**
```json
{
  "intent_id": "pi_987654321",
  "payment_token": "tok_visa_444"
}
```
- **Response (200 OK):**
```json
{
  "transaction_id": "txn_001",
  "status": "succeeded",
  "timestamp": "2025-06-01T12:00:00Z"
}
```

### 4.3 List Tenant Transactions
`GET /tenant/transactions`
- **Description:** Retrieves a list of transactions for the authenticated tenant.
- **Query Params:** `limit=20`, `offset=0`, `status=succeeded`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "txn_001", "amount": 5000, "status": "succeeded" }
  ],
  "pagination": { "total": 150, "next_offset": 20 }
}
```

### 4.4 Update Workflow Rule
`PATCH /workflows/rules/{rule_id}`
- **Description:** Updates the logic of a specific automation rule.
- **Request Body:**
```json
{
  "condition": { "field": "amount", "operator": ">", "value": 1000 },
  "action": { "type": "notify", "channel": "email" }
}
```
- **Response (200 OK):**
```json
{ "status": "updated", "version": 4 }
```

### 4.5 Create Refund
`POST /payments/refund`
- **Description:** Issues a full or partial refund.
- **Request Body:**
```json
{
  "transaction_id": "txn_001",
  "amount": 2000,
  "reason": "customer_request"
}
```
- **Response (200 OK):**
```json
{ "refund_id": "ref_555", "status": "processed" }
```

### 4.6 Get Tenant Configuration
`GET /tenant/config`
- **Description:** Fetches the current settings for the retail tenant.
- **Response (200 OK):**
```json
{
  "tenant_name": "Global Retail Co",
  "currency_default": "USD",
  "features": { "offline_mode": false, "automation": true }
}
```

### 4.7 Register Webhook
`POST /webhooks/register`
- **Description:** Allows tenants to register a URL for event notifications.
- **Request Body:**
```json
{
  "url": "https://retailer.com/webhooks/juniper",
  "events": ["payment.succeeded", "payment.failed"]
}
```
- **Response (201 Created):**
```json
{ "webhook_id": "wh_123" }
```

### 4.8 Validate Idempotency Key
`GET /payments/validate/{key}`
- **Description:** Checks if a request with a specific key has already been processed.
- **Response (200 OK):**
```json
{ "exists": true, "original_response": { "status": "succeeded" } }
```

---

## 5. DATABASE SCHEMA

### 5.1 Schema Overview
The database uses a shared schema approach with `tenant_id` as the primary partition key for all tables.

### 5.2 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `id` (UUID) | None | `name`, `api_key`, `plan_level` | Stores core merchant account data. |
| `users` | `id` (UUID) | `tenant_id` | `email`, `role`, `password_hash` | User accounts linked to tenants. |
| `payment_intents` | `id` (UUID) | `tenant_id`, `user_id` | `amount`, `currency`, `status` | Initial request for payment. |
| `transactions` | `id` (UUID) | `intent_id`, `tenant_id` | `txn_hash`, `amount`, `status` | The final processed transaction record. |
| `cards` | `id` (UUID) | `tenant_id`, `user_id` | `tokenized_pan`, `expiry`, `last4` | PCI-compliant tokenized card data. |
| `workflow_rules` | `id` (UUID) | `tenant_id` | `dag_json`, `is_active`, `version` | The JSON logic for the automation engine. |
| `workflow_logs` | `id` (UUID) | `rule_id`, `tenant_id` | `input_data`, `result`, `timestamp` | Audit trail for rule executions. |
| `idempotency_keys` | `key` (String) | `tenant_id` | `request_hash`, `response_body` | Prevents duplicate transaction processing. |
| `feature_flags` | `id` (UUID) | `tenant_id` | `flag_name`, `variant`, `enabled` | Local cache of LaunchDarkly flags. |
| `audit_logs` | `id` (UUID) | `user_id`, `tenant_id` | `action`, `resource_id`, `timestamp` | Security logs for PCI compliance. |

### 5.3 Relationships
- `tenants` $\rightarrow$ `users` (One-to-Many)
- `tenants` $\rightarrow$ `payment_intents` (One-to-Many)
- `payment_intents` $\rightarrow$ `transactions` (One-to-One)
- `workflow_rules` $\rightarrow$ `workflow_logs` (One-to-Many)
- `tenants` $\rightarrow$ `cards` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Juniper utilizes three distinct environments to ensure stability and PCI compliance.

#### 6.1.1 Development (`dev`)
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** Vercel Preview deployments.
- **Database:** Shared PostgreSQL instance with a `dev` schema.
- **Data:** Mock data; no real PII or credit card data.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production testing, QA, and UAT (User Acceptance Testing).
- **Infrastructure:** Dedicated Vercel environment mirroring production.
- **Database:** A sanitized clone of production data.
- **Security:** Access restricted to the internal team (VPN required).

#### 6.1.3 Production (`prod`)
- **Purpose:** Live retail traffic.
- **Infrastructure:** Vercel production cluster with global edge distribution.
- **Database:** High-availability PostgreSQL cluster with synchronous replication.
- **Security:** Full PCI DSS Level 1 lockdown. Only the `PaymentCore` module has access to the HSM.

### 6.2 Release Process
1. **Feature Branching:** All development occurs in Git branches.
2. **Canary Releases:** New features are deployed to 5% of users via LaunchDarkly.
3. **Monitoring:** Sentry and Datadog are used to monitor error rates during canary phases.
4. **Full Rollout:** Once metrics are stable, the feature flag is toggled to 100%.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** Jest and Vitest.
- **Scope:** Pure functions, utility classes, and individual Prisma models.
- **Requirement:** 80% code coverage on the `PaymentCore` module.

### 7.2 Integration Testing
- **Tooling:** Supertest and Testcontainers.
- **Scope:** API endpoints and database interactions.
- **Approach:** Spin up a temporary PostgreSQL container, run migrations, execute API calls, and verify the database state. Special focus on testing Row Level Security (RLS) to ensure no tenant can see another's data.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys (e.g., "Create Rule $\rightarrow$ Process Payment $\rightarrow$ Verify Rule Execution").
- **Approach:** Automated browser tests running against the staging environment.

### 7.4 PCI Compliance Testing
- **External Audit:** Quarterly vulnerability scans (ASV scans).
- **Internal Audit:** Bi-annual penetration testing focused on the vaulting mechanism.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor (Payment Rail) announced EOL for current API. | High | Critical | Escalate to steering committee for additional funding to migrate to NewRail API. |
| R-02 | Team lacks experience with TypeScript/Next.js stack. | Medium | High | Provide dedicated learning weeks; de-scope non-essential features if milestones are missed. |
| R-03 | Budget for critical tool (LD Enterprise) pending. | High | Medium | Revert to basic internal flag system if approval is denied. |
| R-04 | Performance degradation due to Raw SQL usage. | Low | Medium | Refactor the most critical 10% of raw queries back into Prisma as performance optimizes. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project failure or security breach.
- **High:** Major delay in milestone delivery or significant feature loss.
- **Medium:** Noticeable impact but manageable through workarounds.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE

### 9.1 Project Phases

| Phase | Name | Start Date | End Date | Dependencies | Key Deliverables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| P1 | Foundation | 2025-01-01 | 2025-05-15 | None | Architecture Review |
| P2 | Core Build | 2025-05-16 | 2025-07-15 | P1 | MVP Feature Complete |
| P3 | Hardening | 2025-07-16 | 2025-09-15 | P2 | Internal Alpha Release |
| P4 | Beta/Pilot | 2025-09-16 | 2025-12-01 | P3 | Pilot Retail Launch |

### 9.2 Milestone Detail
- **Milestone 1: Architecture Review (2025-05-15):** Approval of the Modular Monolith design and RLS implementation.
- **Milestone 2: MVP Feature Complete (2025-07-15):** All "Critical" and "High" priority features (Multi-tenancy, Workflow Engine, Offline Mode) functionally working.
- **Milestone 3: Internal Alpha Release (2025-09-15):** Stable build deployed to staging for internal Pivot North testing.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2024-11-12)
- **Attendees:** Jasper, Kian, Nyla
- **Notes:**
    - RLS vs Separate DBs.
    - Jasper: "Go with RLS. Easier to manage."
    - Kian: "Prisma doesn't support RLS natively, need raw SQL wrappers."
    - Decision: Use `prisma.$executeRaw` for session settings.
    - Action: Kian to prototype the middleware.

### Meeting 2: Budget Review (2024-12-05)
- **Attendees:** Jasper, Executive Sponsor
- **Notes:**
    - LD Enterprise cost too high.
    - Sponsor: "Still waiting on Q1 budget."
    - Jasper: "A/B testing is blocked without it."
    - Decision: Keep A/B testing as 'Blocked'.
    - Action: Jasper to send a formal impact memo.

### Meeting 3: Sprint 4 Retrospective (2025-02-20)
- **Attendees:** Jasper, Kian, Nyla, Chioma, QA
- **Notes:**
    - Raw SQL in 30% of queries.
    - Chioma: "Migrations are failing in dev."
    - Jasper: "We need performance. We'll live with the debt for now."
    - QA: "Offline sync is flaky."
    - Decision: Prioritize idempotency keys.

---

## 11. BUDGET BREAKDOWN

*Note: Project is currently bootstrapping with existing personnel. Figures below represent the "implied cost" of capacity and projected tool spends.*

| Category | Estimated Allocation | Notes |
| :--- | :--- | :--- |
| **Personnel** | $850,000 (Annualized) | 6 FTEs (Including CTO and Intern) |
| **Infrastructure** | $24,000 / year | Vercel Pro + Managed PostgreSQL |
| **Tools** | $12,000 / year | LaunchDarkly, Sentry, Datadog |
| **PCI Compliance** | $15,000 / year | External ASV Scans & Audits |
| **Contingency** | $50,000 | Reserved for emergency vendor migration (R-01) |
| **TOTAL** | **$951,000** | **Currently Unfunded (Internal R&D)** |

---

## 12. APPENDICES

### Appendix A: Idempotency Logic Detail
To prevent double-charging in the "Offline-first" mode, Juniper implements a strict idempotency window of 24 hours. 
1. Client generates a UUIDv4 `idempotency_key`.
2. Server checks `idempotency_keys` table.
3. If key exists, return the cached `response_body` without re-processing the payment.
4. If key does not exist, lock the row, process the payment, and store the result.

### Appendix B: Technical Debt Log
- **Debt Item 1:** Raw SQL Bypass. $\sim 30\%$ of queries bypass Prisma for performance. Risk: Schema migrations may break these queries.
- **Debt Item 2:** Lack of Comprehensive API Documentation. Current Swagger docs are incomplete.
- **Debt Item 3:** Manual Deployment of Database Migrations. Not yet integrated into a CI/CD pipeline.