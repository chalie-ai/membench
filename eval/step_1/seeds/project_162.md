# PROJECT SPECIFICATION: CANOPY
**Version:** 1.0.4  
**Status:** Active / Development  
**Last Updated:** 2024-10-24  
**Project Lead:** Fleur Nakamura  
**Confidentiality:** Level 4 (Internal Silverthread AI)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Canopy" is the strategic overhaul of Silverthread AI’s core supply chain management (SCM) infrastructure. For fifteen years, the company has relied on a legacy monolithic system that, while stable, has become a bottleneck for growth in the rapidly expanding renewable energy sector. As Silverthread AI scales its operations to meet global demands for sustainable energy components, the inability to handle real-time logistics, modern API integrations, and collaborative procurement has become a critical business risk.

Canopy is designed to be a high-performance, real-time SCM system built on Elixir and Phoenix. The primary objective is to replace the legacy system with zero downtime, ensuring that the global supply chain—which operates 24/7—remains uninterrupted. Given the criticality of this system, Canopy is classified as a "Flagship Initiative," with direct reporting lines to the Board of Directors.

### 1.2 Business Justification
The current legacy system suffers from severe "technical calcification." Simple updates to procurement logic take weeks due to the fragility of the codebase. Furthermore, the lack of real-time visibility into the supply chain leads to inventory surpluses in some regions and critical shortages in others, costing the company an estimated $1.2M annually in inefficient logistics.

The renewable energy industry is currently experiencing a volatile growth phase. The ability to pivot procurement strategies in real-time, integrate with new vendors via webhooks, and collaborate across time zones is no longer a luxury but a competitive necessity. 

### 1.3 ROI Projection and Success Metrics
The budget for Canopy is set at $5,000,000+, reflecting the scale of the replacement and the risk associated with the transition. The Return on Investment (ROI) is projected based on two primary drivers:
1.  **Operational Efficiency:** Reduction in procurement lead times by 15% and a decrease in inventory waste by 10%.
2.  **Revenue Growth:** Opening new API-driven partnership channels.

**Success Criteria:**
- **Metric 1 (Stability):** Achieve 99.9% uptime during the first 90 days post-launch. This is non-negotiable given the zero-downtime requirement.
- **Metric 2 (Revenue):** Generate $500,000 in new revenue directly attributed to the capabilities of the Canopy system (e.g., through new vendor integrations or increased throughput) within 12 months of deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Canopy utilizes a **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies (databases, third-party APIs, and the UI). This is critical for the renewable energy sector, where integration partners often change their API specifications.

- **The Core:** Contains the business rules, entities, and domain logic (e.g., SupplyChain.Procurement, Order.Validation).
- **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `Repository` port for data access).
- **Adapters:** Implementation details. For example, a `PostgresAdapter` implements the `Repository` port, or a `PhoenixLiveViewAdapter` handles the user interface.

### 2.2 The Stack
- **Language:** Elixir (for high concurrency and fault tolerance).
- **Web Framework:** Phoenix (for scalable web routing).
- **Real-time Layer:** Phoenix LiveView (to enable collaborative editing without complex JS frameworks).
- **Database:** PostgreSQL 16 (Relational data with JSONB for flexible vendor schemas).
- **Infrastructure:** Fly.io (Global distribution to reduce latency for international supply chain hubs).
- **Security Standard:** ISO 27001 Certified Environment.

### 2.3 System Topology (ASCII Representation)
```text
[ User Interface ] <--> [ Phoenix LiveView ] <--> [ Application Boundary ]
                                                          |
                                                          v
[ External APIs ] <--> [ Adapters / Ports ] <--> [ Core Domain Logic ]
(Vendor APIs)             (API Clients)            (Supply Chain Rules)
                                                          |
                                                          v
[ PostgreSQL ] <---------------------------------- [ Database Adapter ]
(Persistence)
```

### 2.4 High-Availability Strategy
To achieve zero downtime during the transition from the 15-year-old legacy system, Canopy will employ a **"Strangler Fig" pattern**. We will incrementally route specific modules (e.g., "Inventory Tracking") from the legacy system to Canopy via a proxy layer. Only after a module is proven stable in production will the legacy counterpart be decommissioned.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Progress
**Requirement:** Users across different geographical regions must be able to edit procurement manifests and shipping schedules simultaneously without overwriting each other's changes.

**Detailed Specification:**
Since Canopy manages critical energy infrastructure, data integrity is paramount. We are implementing a **CRDT (Conflict-free Replicated Data Type)** approach using Elixir's distributed nature. When two users edit the same field in a "Shipping Manifest," the system will not use a "last-write-wins" strategy. Instead, it will track causal ordering of operations.

Phoenix LiveView will be used to push real-time updates to all connected clients. When a user enters a field, a "presence" indicator will show other active users on that specific record. If a conflict occurs that the CRDT cannot resolve automatically (e.g., two users assigning the same unique SKU to different warehouses), the system will flag the record for "Manual Reconciliation" and notify the Project Lead.

**Technical Implementation:**
- Use `Phoenix.Presence` for user tracking.
- Implement a `Delta` table to track granular changes to manifests.
- Backend resolution logic will handle merge conflicts using a hybrid Logical Clock (HLC).

### 3.2 Webhook Integration Framework
**Priority:** Low | **Status:** Not Started
**Requirement:** Provide a mechanism for third-party logistics (3PL) partners to push updates to Canopy automatically.

**Detailed Specification:**
The framework must allow users to define "Event Triggers" (e.g., `Shipment_Departed`, `Payment_Received`) and map them to an external URL. 

The system will implement a "Retry with Exponential Backoff" strategy. If a partner's endpoint is down, Canopy will attempt redelivery at 1, 5, 15, and 60-minute intervals. To ensure security, every webhook payload will be signed with an `X-Canopy-Signature` HMAC-SHA256 header, allowing the receiver to verify the request originated from Silverthread AI.

**Deliverables:**
- A management UI for creating and deleting webhooks.
- A delivery log to audit failed attempts.
- A "Test Webhook" button to send a sample payload to the partner.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** In Progress
**Requirement:** Protect the system from being overwhelmed by automated scripts from partners and provide visibility into who is using the API.

**Detailed Specification:**
We are implementing a **Token Bucket Algorithm** for rate limiting. Limits will be tiered based on the partner's contract level (e.g., "Tier 1: 1000 req/min", "Tier 2: 5000 req/min"). 

The analytics component will track the number of requests per endpoint and the latency of those requests. This data will be stored in a separate `api_logs` table and aggregated hourly into a `usage_stats` table to avoid performance degradation. If a partner hits their limit, the API will return a `429 Too Many Requests` response with a `Retry-After` header.

**Technical Detail:**
- Implementation via a Phoenix Plug that checks the API key against the bucket in Redis.
- Analytics dashboard for the Engineering Manager to monitor "Heavy Hitters."

### 3.4 Notification System (Omni-channel)
**Priority:** Medium | **Status:** In Progress
**Requirement:** A unified system to alert users of critical supply chain events via Email, SMS, In-app notifications, and Push notifications.

**Detailed Specification:**
The system must support "Preference Mapping," where users can choose which channel they prefer for specific alert types. For example, "Urgent Shipment Delay" $\rightarrow$ SMS and Push; "Weekly Report" $\rightarrow$ Email.

The architecture will use a **Dispatcher Pattern**. A `NotificationRequest` is created in the core; the `NotificationDispatcher` then looks up user preferences and routes the request to the appropriate adapter (e.g., SendGrid for email, Twilio for SMS, Firebase for push). To prevent spamming, the system will implement "Notification Bundling," where multiple small updates (e.g., "Item A shipped," "Item B shipped") are grouped into a single daily digest.

**Technical Implementation:**
- Oban (background job processor) for asynchronous delivery.
- Template engine using Heex for customizable email/SMS layouts.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low | **Status:** In Review
**Requirement:** Secure access for high-privilege accounts using TOTP and FIDO2/WebAuthn hardware keys.

**Detailed Specification:**
Given the ISO 27001 requirements, standard password authentication is insufficient for admin roles. We are implementing 2FA that supports both software tokens (Google Authenticator/Authy) and hardware keys (YubiKey).

The workflow involves a "Step-up Authentication" process. For standard viewing, a session cookie suffices. For "Critical Actions" (e.g., changing a $1M procurement order), the system will challenge the user for their hardware key.

**Security Controls:**
- Storage of recovery codes using bcrypt.
- Mandatory 2FA for all users with the `admin` or `manager` role.
- Detailed audit logs of every 2FA attempt, including the device fingerprint.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer <token>` in the Authorization header.

### 4.1 GET `/shipments`
**Description:** Retrieve a list of all active shipments with filtering.
- **Query Params:** `status` (string), `origin` (string), `limit` (int).
- **Response:** `200 OK`
```json
[
  {
    "id": "shp_9921",
    "status": "in_transit",
    "origin": "Shanghai",
    "destination": "Berlin",
    "eta": "2025-06-01T12:00:00Z"
  }
]
```

### 4.2 POST `/shipments`
**Description:** Create a new shipment record.
- **Request Body:**
```json
{
  "origin": "Shanghai",
  "destination": "Berlin",
  "items": [{"sku": "SOL-442", "qty": 500}]
}
```
- **Response:** `201 Created`

### 4.3 PATCH `/shipments/{id}`
**Description:** Update shipment status or details.
- **Request Body:** `{"status": "delivered"}`
- **Response:** `200 OK`

### 4.4 GET `/inventory/{sku}`
**Description:** Check stock levels for a specific part.
- **Response:** `200 OK`
```json
{
  "sku": "SOL-442",
  "total_quantity": 15000,
  "locations": [
    {"warehouse": "WH-East", "qty": 5000},
    {"warehouse": "WH-West", "qty": 10000}
  ]
}
```

### 4.5 POST `/auth/2fa/register`
**Description:** Register a new hardware key (WebAuthn).
- **Request Body:** `{"challenge": "...", "credentialId": "..."}`
- **Response:** `200 OK`

### 4.6 POST `/webhooks/subscribe`
**Description:** Register a new webhook endpoint.
- **Request Body:** `{"event": "shipment.updated", "url": "https://partner.com/webhook"}`
- **Response:** `201 Created`

### 4.7 GET `/analytics/usage`
**Description:** Retrieve API usage statistics (Admin only).
- **Response:** `200 OK`
```json
{
  "period": "2024-10",
  "total_requests": 1250000,
  "error_rate": "0.02%"
}
```

### 4.8 GET `/notifications/unread`
**Description:** Fetch unread notifications for the current user.
- **Response:** `200 OK`
```json
[
  {"id": "notif_1", "message": "Order #502 Delayed", "severity": "critical"}
]
```

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 16. All tables use `uuid` for primary keys to ensure consistency across distributed environments.

### 5.1 Tables and Relationships

| Table Name | Description | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | User account details | `id (PK)`, `email`, `password_hash`, `role` | 1:M with `user_preferences` |
| `user_preferences` | Notification settings | `id (PK)`, `user_id (FK)`, `channel`, `enabled` | M:1 with `users` |
| `shipments` | Core shipping data | `id (PK)`, `origin`, `dest`, `status`, `updated_at` | 1:M with `shipment_items` |
| `shipment_items` | Items within a shipment | `id (PK)`, `shipment_id (FK)`, `sku`, `qty` | M:1 with `shipments` |
| `inventory` | Current stock levels | `sku (PK)`, `total_qty`, `last_audit_date` | 1:M with `warehouse_stock` |
| `warehouse_stock` | Stock per location | `id (PK)`, `sku (FK)`, `warehouse_id (FK)`, `qty` | M:1 with `inventory` |
| `warehouses` | Physical locations | `id (PK)`, `name`, `address`, `capacity` | 1:M with `warehouse_stock` |
| `webhooks` | External callback URLs | `id (PK)`, `event_type`, `url`, `secret_key` | N/A |
| `webhook_logs` | Delivery audit trail | `id (PK)`, `webhook_id (FK)`, `status`, `response_code` | M:1 with `webhooks` |
| `audit_logs` | Security/Change tracking | `id (PK)`, `user_id (FK)`, `action`, `timestamp` | M:1 with `users` |

### 5.2 Key Constraints
- **Indexing:** B-Tree indexes on `shipments.status` and `inventory.sku` for fast retrieval.
- **Foreign Keys:** `ON DELETE RESTRICT` is applied to all core inventory tables to prevent accidental deletion of critical supply chain data.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Canopy utilizes three distinct environments on Fly.io to ensure stability.

1.  **Development (`dev`):**
    - Used by the core team (Fleur, Maren, Uma, Sanjay).
    - Automatic deployments from the `develop` branch.
    - Mocked third-party APIs to avoid rate-limit blocks.

2.  **Staging (`stg`):**
    - Mirrored production environment with anonymized production data.
    - **Manual QA Gate:** Every release candidate must be signed off by the dedicated QA engineer.
    - Two-day turnaround period for bug fixes identified in staging.

3.  **Production (`prod`):**
    - ISO 27001 compliant.
    - Multi-region deployment (US-East, EU-West, Asia-Pacific).
    - Zero-downtime blue-green deployments.

### 6.2 Deployment Pipeline
`Code Commit` $\rightarrow$ `CI Tests` $\rightarrow$ `Dev Deploy` $\rightarrow$ `Staging Deploy` $\rightarrow$ `Manual QA Sign-off` $\rightarrow$ `Production Deploy`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Using `ExUnit`. Every core domain function in the Hexagonal architecture must have $\ge 90\%$ coverage. Tests focus on pure functions (e.g., calculating shipment weights, validating SKU formats).

### 7.2 Integration Testing
Focuses on the "Adapters." We test the `PostgresAdapter` against a real database and the `APIClient` against a Prism mock server. This ensures that the communication between the core and external systems is robust.

### 7.3 End-to-End (E2E) Testing
Using `Wallaby.js` or `Playwright` to simulate user journeys in the Phoenix LiveView frontend. Key flows tested:
- Creating a shipment and seeing it update in real-time on another user's screen.
- Triggering a 2FA challenge during a high-value transaction.
- Setting up a webhook and verifying the delivery log.

### 7.4 Regression Testing
A full regression suite is run on the staging environment every 48 hours to ensure that new changes do not break the legacy system integration.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is building a similar product and is 2 months ahead. | High | High | **Parallel-Path Strategy:** Prototype an alternative architectural approach simultaneously to accelerate delivery of "Killer Features." |
| **R-02** | Integration partner API is undocumented and buggy. | High | Medium | **Documentation Buffer:** Dedicate Sanjay (Contractor) to document all workarounds and maintain a "Partner Quirks" internal wiki. |
| **R-03** | Legacy system data migration failure. | Medium | Critical | **Incremental Migration:** Use the Strangler Fig pattern to move data in small batches. |
| **R-04** | Third-party API rate limits blocking testing. | High | Medium | **Mocking Layer:** Implement a local mock server that simulates partner responses to decouple development from API limits. |

**Probability/Impact Matrix:**
- **Critical:** Immediate Board-level escalation.
- **High:** Weekly review with Fleur Nakamura.
- **Medium:** Handled within the team in Slack.

---

## 9. TIMELINE

### 9.1 Phase Overview
The project is divided into four primary phases, with a focus on the three major milestones.

**Phase 1: Foundation & Core Migration (Now $\rightarrow$ May 2025)**
- Setup Fly.io infrastructure.
- Implement Hexagonal core.
- Migrate basic Inventory modules.
- **Milestone 1: Stakeholder Demo and Sign-off (Target: 2025-05-15)**

**Phase 2: Real-time Features & Integration (May 2025 $\rightarrow$ July 2025)**
- Deploy Collaborative Editing (CRDTs).
- Implement Notification System.
- Finalize API Rate Limiting.
- **Milestone 2: Post-launch Stability Confirmed (Target: 2025-07-15)**

**Phase 3: Security Hardening (July 2025 $\rightarrow$ September 2025)**
- Roll out 2FA and Hardware Key support.
- ISO 27001 audit preparation.
- Final legacy system decommissioning.
- **Milestone 3: Security Audit Passed (Target: 2025-09-15)**

**Phase 4: Optimization & Expansion (September 2025 $\rightarrow$ December 2025)**
- Webhook framework rollout.
- Revenue tracking and metric analysis.

---

## 10. MEETING NOTES

### Meeting 1: 2024-11-12
- **Attendees:** Fleur, Maren, Uma, Sanjay
- **Notes:**
    - Legacy system is too slow.
    - Discussed Elixir. Maren likes it.
    - 2FA needs to be YubiKey. Uma says ISO 27001 requires it.
    - Decision: Use Fly.io for global regions.

### Meeting 2: 2024-12-05
- **Attendees:** Fleur, Maren, Sanjay
- **Notes:**
    - Third-party API is a mess.
    - Sanjay found a bug in their `/orders` endpoint.
    - Blocking testing.
    - Decision: Sanjay to write a wrapper to clean the data.

### Meeting 3: 2025-01-20
- **Attendees:** Fleur, Maren, Uma
- **Notes:**
    - Competitor "Solaris" launched their SCM.
    - They have a better UI.
    - Need to pivot.
    - Decision: Parallel-path the prototype for the dashboard.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,250,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,412,500 | 4 Full-time, 1 Contractor, 1 QA (over 18 months). |
| **Infrastructure** | 15% | $787,500 | Fly.io credits, Redis clusters, PostgreSQL managed instances. |
| **Security & Tools** | 10% | $525,000 | ISO 27001 certification audits, YubiKey bulk purchase, Twilio/SendGrid. |
| **Contingency** | 10% | $525,000 | Reserve for unexpected integration delays or pivots. |

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt
Currently, the system contains a `LegacyAuthManager` class (approx. 3,000 lines). This class handles:
1. User authentication.
2. System-wide logging.
3. Email dispatch.
4. Session management.

**Refactor Plan:**
- `LegacyAuthManager.authenticate` $\rightarrow$ `Canopy.Auth.UserSession`
- `LegacyAuthManager.log` $\rightarrow$ `Canopy.Telemetry.Logger`
- `LegacyAuthManager.send_mail` $\rightarrow$ `Canopy.Notifications.EmailAdapter`

### Appendix B: Conflict Resolution Logic (CRDT)
For the collaborative editing feature, the following logic is applied to `ShipmentManifest` updates:
1. **LWW-Element-Set:** Used for simple fields (e.g., "Warehouse Name").
2. **Sequence CRDT:** Used for the list of items in a shipment to ensure that items added by two different users appear in the same order for everyone.
3. **Vector Clocks:** Used to track the causality of updates across the three Fly.io regions to ensure eventual consistency.