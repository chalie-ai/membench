# PROJECT SPECIFICATION DOCUMENT: BASTION
**Version:** 1.0.4  
**Date:** October 24, 2024  
**Project Status:** Active / Critical  
**Classification:** Confidential - Pivot North Engineering  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Bastion" is a mission-critical e-commerce marketplace developed by Pivot North Engineering specifically for the aerospace industry. Unlike standard consumer marketplaces, Bastion is designed to facilitate the procurement of aerospace-grade components, where traceability, regulatory compliance, and rigorous auditing are not merely features but legal mandates. The project is currently operating under a strict legal deadline: the platform must be fully operational and compliant within six months to avoid severe regulatory penalties and the potential loss of operating licenses.

### 1.2 Business Justification
The aerospace sector is undergoing a rapid transition toward digitized procurement. Current methods—relying on fragmented emails, PDFs, and manual spreadsheets—fail to meet the emerging transparency requirements set by international aviation authorities. Bastion provides a centralized, immutable ledger of transactions and component provenance. By implementing a CQRS (Command Query Responsibility Segregation) architecture with event sourcing, Pivot North Engineering ensures that every change to a part's status or a transaction's state is recorded, providing a perfect audit trail that satisfies government regulators.

### 1.3 ROI Projection
Given the "shoestring" budget of $150,000, the Return on Investment (ROI) is not measured by immediate profit, but by risk mitigation and market positioning.
- **Risk Mitigation Value:** The avoidance of non-compliance fines, estimated at $250,000 per quarter if the deadline is missed.
- **Market Capture:** By being the first compliant digital marketplace in this niche, Pivot North expects to capture 15% of the regional aerospace MRO (Maintenance, Repair, and Overhaul) procurement market within 12 months.
- **Operational Efficiency:** Reducing procurement lead times from 14 days to 48 hours through automated vendor matching, projecting a 20% increase in procurement throughput.

### 1.4 Strategic Constraints
The project is constrained by a minimal team of four (Kaia Stein, Matteo Nakamura, Uma Nakamura, and Emeka Liu) and a highly dysfunctional communication environment. The lack of direct communication between the Project Lead and the Lead Engineer necessitates that this document serve as the "Single Source of Truth" (SSOT) to prevent catastrophic misalignment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design Philosophy
Bastion employs a decoupled architecture to ensure that the high-write demands of event sourcing do not interfere with the high-read demands of the marketplace storefront.

**CQRS (Command Query Responsibility Segregation):**
- **Command Side:** Handles all state-changing operations (e.g., "Create Order," "Update Inventory"). These are processed via Django signals and written to the Event Store.
- **Query Side:** Uses optimized PostgreSQL materialized views and Redis caching to serve the frontend, ensuring sub-second response times for aerospace part searches.

**Event Sourcing:**
Every state change is stored as an immutable event in the `event_store` table. This allows the system to reconstruct the state of any order at any point in time—a non-negotiable requirement for SOC 2 Type II compliance.

### 2.2 ASCII Architecture Diagram
```text
[ CLIENT LAYER ] 
      | (HTTPS/REST)
      v
[ AWS ALB / API GATEWAY ]
      |
      v
[ AWS ECS (Fargate) ] <---- [ Redis Cache ]
      |  (Django Application)
      |---------------------------------------|
      | [ Command Bus ]                       | [ Query Bus ]
      |   - Validate Request                  |   - Read Materialized Views
      |   - Append to Event Store             |   - Fetch Cached Data
      |_______________________________________|_________________
                               |
                               v
                    [ PostgreSQL Database ]
            /-----------------------------------\
            | [ Event Store ] | [ Read Models ] |
            | (Immutable Log) | (Normalized DB) |
            \-----------------------------------/
                               |
                               v
                    [ AWS S3 (Audit Logs) ]
```

### 2.3 Technology Stack
- **Language:** Python 3.11+
- **Framework:** Django 4.2 LTS (chosen for stability and administrative tooling).
- **Database:** PostgreSQL 15 (Primary store for events and read models).
- **Cache/Queue:** Redis 7.0 (Used for session management, caching, and Celery task brokering).
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless scaling.
- **Compliance:** SOC 2 Type II (Targeting audit readiness by Milestone 3).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Critical - Launch Blocker)
**Priority:** Critical | **Status:** In Progress

The A/B testing framework is not a separate tool but is integrated directly into the feature flag system. Because aerospace procurement involves high-stakes transactions, we cannot risk "blind" rollouts. This framework allows the team to toggle features for specific percentages of the user base based on their organizational ID.

**Technical Requirements:**
- **Flag Logic:** The system must support "Multi-variant" flags (A, B, C) rather than simple Booleans.
- **Assignment:** Users are hashed by their `user_id` to ensure a consistent experience (stickiness).
- **Metrics Integration:** Every event triggered by a user must be tagged with the active variant ID in the event store.
- **Rollout Strategy:** Gradual ramp-up (1% $\rightarrow$ 5% $\rightarrow$ 25% $\rightarrow$ 100%).

**Acceptance Criteria:**
- Ability to define a variant in the Django Admin panel.
- Zero latency impact on page load (cached via Redis).
- Statistical significance report generated per variant.

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Not Started

Given the sensitivity of aerospace blueprints and procurement data, standard password authentication is insufficient. Bastion requires mandatory 2FA for all administrative and vendor accounts.

**Technical Requirements:**
- **WebAuthn API:** Implementation of the WebAuthn standard to support hardware keys (Yubico, Google Titan).
- **Fallback Mechanisms:** TOTP (Time-based One-Time Password) via apps like Google Authenticator for users without hardware keys.
- **Recovery Codes:** Generation of ten 8-digit one-time use recovery codes upon setup.
- **Session Hardening:** 2FA must be re-validated every 24 hours for high-privilege actions (e.g., changing banking details).

**Acceptance Criteria:**
- User can register a FIDO2 compliant security key.
- System prevents login if 2FA is enabled but the second factor is not provided.
- Audit log records every successful and failed 2FA attempt.

### 3.3 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** In Progress

Aerospace technicians often work in hangars or "dead zones" with no connectivity. They must be able to log part inspections and order requests offline.

**Technical Requirements:**
- **Client-Side Storage:** Use of IndexedDB to store pending transactions.
- **Synchronization Engine:** A background worker (Service Worker) that detects "online" status and pushes queued events to the `/api/v1/sync` endpoint.
- **Conflict Resolution:** A "Last Write Wins" (LWW) strategy is used for general fields, but for inventory counts, a delta-based approach is required to prevent over-selling.
- **State Indicators:** UI must clearly show "Syncing..." and "Synced" status.

**Acceptance Criteria:**
- User can add an item to a procurement list while in Airplane Mode.
- Data persists after a browser refresh.
- Upon reconnection, data is uploaded without duplicate entries.

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low | **Status:** In Review

This feature allows multiple procurement officers to edit a single "Request for Quote" (RFQ) simultaneously, similar to Google Docs.

**Technical Requirements:**
- **WebSockets:** Implementation via Django Channels for real-time bidirectional communication.
- **Operational Transformation (OT):** To handle conflicts, the system will implement a simplified OT algorithm to merge text changes in the RFQ description.
- **Presence Indicators:** Display of active users and their cursor positions.
- **Versioning:** Every "Save" event creates a snapshot in the Event Store for easy rollback.

**Acceptance Criteria:**
- Two users editing the same field see changes in $\le 200ms$.
- No data loss occurs when two users edit the same line simultaneously.
- Cursor positions are accurately mapped to the DOM.

### 3.5 Webhook Integration Framework
**Priority:** Low | **Status:** Complete

To allow Bastion to integrate with third-party ERP (Enterprise Resource Planning) systems, a robust webhook framework has been built.

**Technical Requirements:**
- **Event Triggers:** Webhooks trigger on `order.created`, `order.shipped`, `payment.received`, and `compliance.failed`.
- **Payload Security:** All payloads must be signed using an HMAC (Hash-based Message Authentication Code) with a shared secret.
- **Retry Logic:** Exponential backoff retry strategy (1m, 5m, 15m, 1h) for failed deliveries.
- **Dead Letter Queue:** Webhooks that fail after 4 attempts are moved to a "Dead Letter" state for manual review by Emeka Liu.

**Acceptance Criteria:**
- Third-party server receives a valid JSON payload within 2 seconds of the event.
- Retries occur automatically upon 5xx server errors.
- Secret rotation is supported without downtime.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Header: `Authorization: Bearer <JWT_TOKEN>`.

### 4.1 `POST /api/v1/auth/2fa/register`
Registers a new hardware key.
- **Request:**
  ```json
  {
    "challenge": "a1b2c3d4...",
    "user_id": "uuid-1234-5678"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "status": "success",
    "key_id": "key_abc_123"
  }
  ```

### 4.2 `GET /api/v1/catalog/parts`
Retrieves a list of aerospace parts with filtering.
- **Query Params:** `?category=avionics&certified=true`
- **Response (200 OK):**
  ```json
  [
    {"id": "part-001", "name": "Fuel Pump X-1", "price": 4500.00, "stock": 12},
    {"id": "part-002", "name": "Actuator Y-2", "price": 1200.00, "stock": 5}
  ]
  ```

### 4.3 `POST /api/v1/orders/create`
Initiates a new procurement order.
- **Request:**
  ```json
  {
    "items": [{"part_id": "part-001", "qty": 1}],
    "shipping_address": "Hangar 4, JFK Airport"
  }
  ```
- **Response (201 Created):**
  ```json
  {"order_id": "ord-999", "status": "pending_compliance"}
  ```

### 4.4 `POST /api/v1/sync/batch`
The endpoint for the offline-first background sync.
- **Request:**
  ```json
  {
    "events": [
      {"type": "ORDER_UPDATE", "payload": {...}, "timestamp": "2025-08-01T10:00Z"},
      {"type": "PART_QUERY", "payload": {...}, "timestamp": "2025-08-01T10:05Z"}
    ]
  }
  ```
- **Response (200 OK):**
  ```json
  {"synced_count": 2, "conflicts": []}
  ```

### 4.5 `GET /api/v1/audit/trace/{order_id}`
Returns the full event history of an order for regulatory audit.
- **Response (200 OK):**
  ```json
  {
    "order_id": "ord-999",
    "history": [
      {"event": "CREATED", "user": "Kaia", "time": "T1"},
      {"event": "COMPLIANCE_CHECKED", "user": "System", "time": "T2"},
      {"event": "SHIPPED", "user": "Vendor_A", "time": "T3"}
    ]
  }
  ```

### 4.6 `PATCH /api/v1/feature-flags/toggle`
Internal endpoint for managing A/B test variants.
- **Request:**
  ```json
  {
    "flag_id": "new_checkout_flow",
    "variant": "B",
    "rollout_percentage": 10
  }
  ```
- **Response (200 OK):**
  ```json
  {"status": "updated"}
  ```

### 4.7 `GET /api/v1/webhooks/logs`
Retrieves delivery status of outgoing webhooks.
- **Response (200 OK):**
  ```json
  [
    {"webhook_id": "wh-1", "endpoint": "https://erp.com/api", "status": "failed", "error": "500 Internal Server Error"}
  ]
  ```

### 4.8 `POST /api/v1/auth/2fa/verify`
Verifies the second factor during login.
- **Request:**
  ```json
  {
    "user_id": "uuid-1234",
    "code": "554321"
  }
  ```
- **Response (200 OK):**
  ```json
  {"token": "jwt_session_token_xyz"}
  ```

---

## 5. DATABASE SCHEMA

The database is hosted on AWS RDS PostgreSQL 15. It utilizes a hybrid approach where the `event_store` is append-only, and other tables serve as "read models" for performance.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role` | Basic user identity and RBAC roles. |
| `user_auth_factors` | `factor_id` | `user_id` | `factor_type`, `public_key`, `secret` | Stores 2FA keys and TOTP secrets. |
| `parts` | `part_id` | None | `sku`, `certification_level`, `price` | Catalog of aerospace components. |
| `inventory` | `inv_id` | `part_id` | `warehouse_id`, `quantity_on_hand` | Current stock levels across sites. |
| `orders` | `order_id` | `user_id` | `total_amount`, `current_status` | The "Read Model" for current order state. |
| `order_items` | `item_id` | `order_id`, `part_id` | `quantity`, `unit_price` | Line items for each order. |
| `event_store` | `event_id` | `aggregate_id` | `event_type`, `payload` (JSONB), `created_at` | Immutable log of every state change. |
| `feature_flags` | `flag_id` | None | `flag_name`, `is_active`, `variant_config` | Configuration for A/B testing. |
| `webhook_configs` | `hook_id` | `user_id` | `target_url`, `secret_hash`, `events_subscribed` | Third-party integration settings. |
| `webhook_logs` | `log_id` | `hook_id` | `response_code`, `request_body`, `attempt_count` | History of webhook delivery attempts. |

### 5.2 Relationships
- **Users $\rightarrow$ Orders:** One-to-Many. One user can place multiple orders.
- **Orders $\rightarrow$ OrderItems:** One-to-Many. One order contains multiple parts.
- **Parts $\rightarrow$ OrderItems:** One-to-Many. One part can appear in many orders.
- **EventStore $\rightarrow$ Orders:** Many-to-One. Many events (Created $\rightarrow$ Paid $\rightarrow$ Shipped) result in one current Order state.
- **Users $\rightarrow$ UserAuthFactors:** One-to-Many. A user can have multiple 2FA methods (e.g., YubiKey and App).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To maintain SOC 2 compliance, environments are strictly isolated. No developer has write access to Production.

**1. Development (Dev):**
- **Purpose:** Local iterative development and feature branching.
- **Infrastructure:** Docker Compose on local machines.
- **Data:** Anonymized seed data.

**2. Staging (Staging):**
- **Purpose:** Pre-production validation and QA.
- **Infrastructure:** AWS ECS Fargate (T3.medium), RDS (db.t3.small).
- **Data:** A scrubbed snapshot of production data.
- **Gate:** Every PR must be merged here and verified by Matteo Nakamura.

**3. Production (Prod):**
- **Purpose:** Live regulatory-compliant marketplace.
- **Infrastructure:** AWS ECS Fargate (C5.large), RDS (db.m5.large) with Multi-AZ failover.
- **Security:** AWS KMS for encryption at rest; AWS Secrets Manager for API keys.

### 6.2 Deployment Pipeline
The deployment process is manual and cautious due to the criticality of the aerospace industry.
1. **Commit:** Code is pushed to `main`.
2. **CI:** GitHub Actions runs unit tests and linting.
3. **Staging Deploy:** Automated deploy to Staging.
4. **Manual QA Gate:** A 48-hour window where the feature is manually tested. If a bug is found, the build is rejected.
5. **Production Deploy:** Manual trigger by Kaia Stein.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Business logic in `services.py` and model validations.
- **Requirement:** 80% code coverage minimum for all new features.
- **Focus:** Edge cases in the A/B testing logic and 2FA validation.

### 7.2 Integration Testing
- **Framework:** `Django TestCase` with a dedicated PostgreSQL test database.
- **Scope:** API endpoint-to-database flow.
- **Focus:** Ensuring that a "Command" correctly appends an event to the `event_store` and updates the "Read Model" in the `orders` table.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Search Part $\rightarrow$ Purchase $\rightarrow$ Sync Offline").
- **Frequency:** Run against the Staging environment before every production release.

### 7.4 Compliance Testing
- **SOC 2 Audit:** A third-party auditor will perform a "Point-in-Time" audit.
- **Penetration Testing:** Uma Nakamura will conduct monthly internal "Red Team" attacks on the 2FA and API endpoints.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Integration partner API is undocumented/buggy | High | High | Hire a specialized contractor to build a wrapper layer and reduce the "bus factor." |
| **R2** | Regulatory requirements change mid-project | Medium | High | De-scope non-essential "nice-to-have" features (like Collaborative Editing) to free up time. |
| **R3** | Team dysfunction prevents critical decisions | High | Medium | All decisions must be documented in this Spec or Slack; avoid verbal agreements. |
| **R4** | Budget exhaustion before launch | Medium | High | Use AWS Free Tier for Dev/Staging; prioritize "Critical" features over "Low" priority ones. |
| **R5** | Data loss during offline-first sync | Low | High | Implement strict idempotent keys for every event to prevent duplicate processing. |

**Probability/Impact Matrix:**
- **Critical:** High Prob / High Impact (R1, R3) $\rightarrow$ Immediate Action.
- **Major:** Med Prob / High Impact (R2, R4) $\rightarrow$ Weekly Monitoring.
- **Minor:** Low Prob / High Impact (R5) $\rightarrow$ Technical Safeguards.

---

## 9. TIMELINE & MILESTONES

The project follows a compressed 6-month schedule. Because the deadline is legal, there is no flexibility for "scope creep."

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Months 1-2)**
  - Setup AWS ECS, RDS, and Event Store.
  - Implementation of basic catalog and user management.
  - **Dependency:** Legal approval of the Data Processing Agreement (Current Blocker).
- **Phase 2: Security & Compliance (Months 3-4)**
  - Implementation of 2FA and Hardware Key support.
  - Finalizing A/B testing framework.
  - Initial SOC 2 gap analysis.
- **Phase 3: Advanced Features & Stabilization (Months 5-6)**
  - Offline-first sync and background workers.
  - External Beta testing.
  - Final audit and production hardening.

### 9.2 Key Milestone Dates
| Milestone | Target Date | Deliverable | Dependency |
| :--- | :--- | :--- | :--- |
| **M1: External Beta** | 2025-08-15 | 10 Pilot Users live on Staging. | 2FA must be functional. |
| **M2: MVP Complete** | 2025-10-15 | All "Critical" and "High" features merged. | API Integration Wrapper complete. |
| **M3: Internal Alpha** | 2025-12-15 | Full system release; SOC 2 Audit passed. | Final legal review signed off. |

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project culture, no formal minutes are kept. The following are reconstructed from Slack threads in the #bastion-dev channel.*

### Meeting 1: The "API Nightmare" Discussion
**Date:** 2024-11-02  
**Participants:** Kaia Stein, Matteo Nakamura  
**Context:** Discussion regarding the integration partner's undocumented API.
- **Matteo:** "The partner API returns 500s for perfectly valid JSON. I'm spending 4 hours a day just guessing the field names. We can't hit the M2 milestone like this."
- **Kaia:** "We can't afford more full-time staff. Just wrap it in a try-except block and log the raw response to stdout."
- **Decision:** Decision made to hire a short-term contractor specifically to map the API and write a wrapper. This will be funded by the contingency budget.

### Meeting 2: The 2FA Conflict
**Date:** 2024-11-15  
**Participants:** Kaia Stein, Uma Nakamura  
**Context:** Discussion on hardware key requirements.
- **Uma:** "If we only do TOTP, we won't pass the higher-tier SOC 2 audit. We need FIDO2/WebAuthn support for hardware keys."
- **Kaia:** "That's too much work for the frontend. Can we just use email codes?"
- **Uma:** "Email is not secure enough for aerospace. It's a non-starter for the security audit."
- **Decision:** 2FA with hardware key support is upgraded to "High Priority." Matteo will be tasked with the WebAuthn integration.

### Meeting 3: The "Stdout" Debugging Crisis
**Date:** 2024-12-01  
**Participants:** Kaia Stein, Emeka Liu  
**Context:** Production issue where orders were disappearing.
- **Emeka:** "I've been staring at the stdout logs for three hours. I can't tell which user triggered the error because there's no structured logging. We need a proper logger."
- **Kaia:** "We don't have time to implement ELK or Datadog. Just use `print()` with a timestamp."
- **Emeka:** "That's not a solution, that's a disaster."
- **Decision:** No decision reached. Technical debt (Lack of structured logging) remains as a known issue. Emeka continues to manually parse logs.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Shoestring)

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $105,000 | Salary for the 4-person team (subsidized by Pivot North). |
| **Infrastructure** | 15% | $22,500 | AWS ECS, RDS, Redis, and S3 costs for 12 months. |
| **Tools/Licenses** | 5% | $7,500 | GitHub Enterprise, SOC 2 Audit prep tools, YubiKeys for testing. |
| **Contingency** | 10% | $15,000 | Budget for the API integration contractor and emergency fixes. |

**Financial Constraint Note:** Every single expenditure over $500 must be approved personally by Kaia Stein.

---

## 12. APPENDICES

### Appendix A: Event Sourcing Schema Detail
To ensure the `event_store` is performant, the `payload` field uses the PostgreSQL `JSONB` type. This allows for indexing of specific fields within the event without requiring a schema change for every new event type.

**Example Event Entry:**
- `event_id`: `evt_88221`
- `aggregate_id`: `ord_999`
- `event_type`: `ORDER_PRICE_ADJUSTED`
- `payload`: `{"old_price": 4500, "new_price": 4200, "reason": "bulk_discount", "adjusted_by": "user_44"}`
- `created_at`: `2025-08-10 14:00:00Z`

### Appendix B: SOC 2 Compliance Checklist
The following controls must be evidenced for the audit:
1. **Access Control:** No shared accounts; MFA enabled on all AWS Root/IAM accounts.
2. **Change Management:** All code changes must have a corresponding Jira ticket and a PR approval from the Tech Lead.
3. **Audit Logging:** Every API call that modifies data must be recorded in the `event_store`.
4. **Encryption:** All data in transit must use TLS 1.3; all data at rest must use AES-256.
5. **Business Continuity:** Daily RDS snapshots with a 30-day retention period.