Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Document (PSD). It expands every provided detail into a rigorous technical framework designed for a development team at Talus Innovations.

***

# PROJECT SPECIFICATION: TRELLIS
**Version:** 1.0.4  
**Status:** Active / High Urgency  
**Company:** Talus Innovations  
**Date of Issue:** January 15, 2026  
**Classification:** Internal / ISO 27001 Restricted  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Trellis** is a specialized IoT device network deployment engineered specifically for the real estate sector. Developed by Talus Innovations, the system serves as a centralized orchestration layer for smart building sensors, HVAC controls, and security peripherals. The primary driver for Trellis is not purely commercial growth, but **urgent regulatory compliance**. New legislation regarding building energy efficiency and safety reporting mandates that all commercial properties under the Talus portfolio implement standardized, auditable IoT monitoring by the end of the current six-month window. Failure to comply will result in significant legal penalties and the potential loss of operating licenses in key metropolitan markets.

### 1.2 Business Justification
The real estate industry is undergoing a digital transformation where "dumb" buildings are becoming liabilities. Trellis provides the necessary infrastructure to move from fragmented, vendor-specific silos to a unified, compliant network. By integrating disparate IoT protocols into a single Elixir-based monolith, Talus Innovations can ensure that reporting data is immutable, timestamped, and ready for regulatory audit.

The urgency of this project is underscored by a hard legal deadline. With only six months until the compliance window closes, the project has been fast-tracked. The decision to use a "clean monolith" architecture is a strategic choice to minimize the latency and complexity associated with microservices, ensuring that the team can pivot quickly as regulatory requirements evolve.

### 1.3 ROI Projection
The Return on Investment (ROI) for Trellis is calculated across three primary vectors:
1. **Avoidance of Penalties:** Estimated avoidance of $1.2M in non-compliance fines across 40 properties.
2. **Operational Efficiency:** A projected 50% reduction in manual processing time for facility managers who currently collect data manually from various building controllers.
3. **Asset Value Appreciation:** Integration of a certified ISO 27001 compliant IoT network increases the valuation of the real estate assets by approximately 3-5% due to "Smart Building" certification.

**Projected 3-Year ROI:** 215%, accounting for the initial $800,000 investment and ongoing maintenance costs.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Selection
Trellis is built on the **BEAM ecosystem** to leverage its legendary concurrency and fault tolerance, which are critical for handling thousands of simultaneous IoT heartbeat signals.

- **Language/Framework:** Elixir / Phoenix (v1.7.11)
- **Real-time Interface:** Phoenix LiveView (for low-latency dashboard updates without full-page refreshes)
- **Database:** PostgreSQL 15.4 (Relational storage for device metadata and compliance logs)
- **Hosting:** Fly.io (Global distribution to minimize latency between IoT gateways and the cloud)
- **Security Standard:** ISO 27001 Certified Environment (Encryption at rest and in transit, strict IAM roles)

### 2.2 Architectural Pattern: The Clean Monolith
Trellis avoids the "distributed monolith" trap. It utilizes a single deployment unit but maintains strict **Module Boundaries**. 

**Core Modules:**
- `Trellis.Accounts`: User authentication and RBAC.
- `Trellis.Devices`: Device registration, state management, and heartbeat monitoring.
- `Trellis.Compliance`: Logic for regulatory reporting and audit trails.
- `Trellis.Automation`: The visual rule engine and webhook dispatcher.
- `Trellis.Billing`: Subscription logic and invoicing.

### 2.3 ASCII Architecture Diagram
```text
[ IoT Device Layer ]       [ Gateway Layer ]       [ Cloud Layer (Fly.io) ]
+-----------------+       +----------------+      +-----------------------+
| Sensor A (Temp) | ---->  |  MQTT Broker   | ---> |  Phoenix / Elixir     |
| Sensor B (CO2)  |       |  (Local Edge)   |      |  [ LiveView UI ]      |
| Actuator (HVAC) | <----  |  TLS Tunnel    | <--- |  [ Business Logic ]    |
+-----------------+       +----------------+      +-----------|-----------+
                                                               |
                                                               v
                                                  +-----------------------+
                                                  | PostgreSQL Database    |
                                                  | (ISO 27001 Encrypted)  |
                                                  +-----------------------+
                                                               ^
                                                               |
                                                  +-----------------------+
                                                  | External API / Webhooks|
                                                  | (Third-party Tools)   |
                                                  +-----------------------+
```

### 2.4 Deployment Strategy
Deployments are aligned with **Regulatory Review Cycles**. To maintain stability during audits, the team will utilize **Quarterly Releases**. 
- **Q1 Release:** Initial Alpha / Internal Testing.
- **Q2 Release:** Beta / External Pilot (Milestone 1).
- **Q3 Release:** Compliance Final / Production Sign-off (Milestone 3).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
- **Priority:** Critical (Launch Blocker)
- **Status:** In Design
- **Description:** The dashboard is the primary interface for real estate managers to monitor compliance status and device health. Because different properties have different sensor arrays, a one-size-fits-all dashboard is impossible.
- **Technical Requirements:** 
    - Use LiveView's `phx-drop-target` and `phx-drag` attributes to allow users to rearrange widgets.
    - Widgets must be persisted in the `user_dashboards` table as a JSONB array of coordinates and widget types.
    - Supported Widget Types: Gauge (for temperature/humidity), Status List (for device connectivity), Compliance Alert (for regulatory breaches), and Trend Graph (for energy usage).
- **User Experience:** A "Gallery" sidebar where users can drag new widgets onto the canvas. Widgets must snap to a 12-column grid.
- **Acceptance Criteria:** A user must be able to create a layout, save it, and have that layout persist across sessions. The dashboard must update in real-time as IoT data streams in via Phoenix PubSub.

### 3.2 Workflow Automation Engine with Visual Rule Builder
- **Priority:** Critical (Launch Blocker)
- **Status:** Complete
- **Description:** A system that allows non-technical users to create "If-This-Then-That" logic for building management. For example: "If Temperature in Room 302 > 75°F AND Time is between 9AM-5PM, THEN set HVAC to Cool."
- **Technical Requirements:** 
    - A visual builder that generates a JSON-based rule schema.
    - A background worker (Obby or Quantum) that evaluates these rules every 60 seconds against the current state of the `devices` table.
    - Integration with the Webhook Framework to trigger external notifications.
- **Rule Structure:** `Condition` (Trigger) $\rightarrow$ `Filter` (Constraint) $\rightarrow$ `Action` (Command).
- **Acceptance Criteria:** The engine must process 1,000 rules per second without increasing API latency beyond 200ms.

### 3.3 Real-time Collaborative Editing with Conflict Resolution
- **Priority:** High
- **Status:** In Design
- **Description:** Multiple property managers often need to configure a building's device settings simultaneously. To prevent "last-write-wins" data loss, Trellis implements collaborative editing.
- **Technical Requirements:** 
    - Implementation of **Operational Transformation (OT)** or **CRDTs (Conflict-free Replicated Data Types)** using Elixir's `GenServer` to manage state.
    - Presence tracking via Phoenix Presence to show who is currently editing a specific device configuration.
    - A "Locking" mechanism at the field level to prevent simultaneous edits of the same variable.
- **Conflict Resolution:** If two users edit the same value, the system will prioritize the user with the higher RBAC permission level; if equal, the most recent timestamp wins.
- **Acceptance Criteria:** Latency between collaborators must be $<100ms$ for cursor position updates.

### 3.4 Webhook Integration Framework for Third-Party Tools
- **Priority:** Medium
- **Status:** Complete
- **Description:** A framework allowing Trellis to push events to external real estate management software (e.g., Yardi, AppFolio).
- **Technical Requirements:** 
    - Endpoint management via `/api/webhooks` where users can register target URLs and secret keys.
    - Event types: `device.offline`, `compliance.alert`, `billing.failed`.
    - Retry logic: Exponential backoff for failed deliveries (5 attempts over 24 hours).
    - Signature verification: All payloads must be signed with an `X-Trellis-Signature` HMAC-SHA256 header.
- **Acceptance Criteria:** Successfully deliver 99.9% of webhooks to verified endpoints within 5 seconds of the event trigger.

### 3.5 Automated Billing and Subscription Management
- **Priority:** Low (Nice to Have)
- **Status:** In Progress
- **Description:** A system to charge property owners based on the number of active IoT devices connected to the Trellis network.
- **Technical Requirements:** 
    - Integration with Stripe Billing API.
    - A "Metered Billing" model where usage is calculated based on the `device_heartbeats` table count per month.
    - Automatic generation of PDF invoices stored in an S3 bucket.
- **Subscription Tiers:** Basic (up to 50 devices), Professional (up to 500 devices), Enterprise (Unlimited).
- **Acceptance Criteria:** Automatic transition of account status to "Delinquent" if payment fails after three attempts, restricting API access to the dashboard only.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/` and require a `Bearer` token in the Authorization header.

### 4.1 Device Management
**`GET /api/v1/devices`**
- **Description:** Retrieve a list of all registered IoT devices.
- **Query Params:** `property_id` (optional), `status` (online/offline).
- **Response:** `200 OK`
```json
[
  {"id": "dev_123", "name": "Temp-Sensor-01", "status": "online", "last_seen": "2026-01-15T10:00:00Z"},
  {"id": "dev_456", "name": "HVAC-Ctrl-02", "status": "offline", "last_seen": "2026-01-14T22:15:00Z"}
]
```

**`POST /api/v1/devices`**
- **Description:** Register a new device in the network.
- **Request Body:** `{"serial_number": "SN-998", "model": "T-1000", "property_id": "prop_789"}`
- **Response:** `201 Created`
```json
{"id": "dev_789", "created_at": "2026-01-15T12:00:00Z", "status": "pending_activation"}
```

### 4.2 Compliance & Reporting
**`GET /api/v1/compliance/status`**
- **Description:** Get the overall compliance percentage for a specific property.
- **Request Body:** `{"property_id": "prop_123"}`
- **Response:** `200 OK`
```json
{"property_id": "prop_123", "compliance_score": 84.5, "missing_metrics": ["CO2_Level", "Humidity"]}
```

**`POST /api/v1/compliance/audit-log`**
- **Description:** Manually push an audit event for regulatory review.
- **Request Body:** `{"event": "Inspection", "inspector_id": "user_44", "notes": "Quarterly check complete"}`
- **Response:** `202 Accepted`

### 4.3 Automation & Rules
**`GET /api/v1/rules`**
- **Description:** List all active automation rules.
- **Response:** `200 OK`
```json
[{"id": "rule_1", "trigger": "temp > 75", "action": "hvac_cool", "enabled": true}]
```

**`PATCH /api/v1/rules/:id`**
- **Description:** Update a specific automation rule.
- **Request Body:** `{"enabled": false}`
- **Response:** `200 OK`

### 4.4 Webhooks & Integration
**`POST /api/v1/webhooks/subscribe`**
- **Description:** Subscribe a URL to specific event types.
- **Request Body:** `{"url": "https://client.com/webhook", "events": ["device.offline"]}`
- **Response:** `201 Created`

**`DELETE /api/v1/webhooks/:id`**
- **Description:** Remove a webhook subscription.
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system utilizes a PostgreSQL database. All tables use UUIDs for primary keys to prevent enumeration attacks and facilitate distributed data synchronization.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `password_hash` (String)
    - `role` (Enum: 'Admin', 'Manager', 'Viewer')
    - `created_at` (Timestamp)

2.  **`properties`**
    - `id` (UUID, PK)
    - `name` (String)
    - `address` (Text)
    - `regulatory_region` (String)
    - `owner_id` (UUID, FK $\rightarrow$ `users.id`)

3.  **`devices`**
    - `id` (UUID, PK)
    - `property_id` (UUID, FK $\rightarrow$ `properties.id`)
    - `serial_number` (String, Unique)
    - `device_type` (String)
    - `status` (Enum: 'online', 'offline', 'error')
    - `last_heartbeat` (Timestamp)

4.  **`device_readings`**
    - `id` (BigInt, PK)
    - `device_id` (UUID, FK $\rightarrow$ `devices.id`)
    - `metric_type` (String) — *e.g., "Temperature"*
    - `value` (Float)
    - `captured_at` (Timestamp)

5.  **`automation_rules`**
    - `id` (UUID, PK)
    - `property_id` (UUID, FK $\rightarrow$ `properties.id`)
    - `logic_json` (JSONB) — *Stores the visual rule structure*
    - `is_active` (Boolean)
    - `updated_at` (Timestamp)

6.  **`webhook_subscriptions`**
    - `id` (UUID, PK)
    - `target_url` (String)
    - `secret_token` (String)
    - `event_types` (Array[String])
    - `created_at` (Timestamp)

7.  **`compliance_logs`**
    - `id` (UUID, PK)
    - `property_id` (UUID, FK $\rightarrow$ `properties.id`)
    - `event_type` (String)
    - `payload` (JSONB)
    - `timestamp` (Timestamp)

8.  **`user_dashboards`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ `users.id`)
    - `layout_config` (JSONB) — *Stores widget positions and sizes*
    - `updated_at` (Timestamp)

9.  **`subscriptions`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ `users.id`)
    - `stripe_customer_id` (String)
    - `plan_level` (Enum: 'Basic', 'Pro', 'Enterprise')
    - `status` (String)

10. **`audit_trails`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ `users.id`)
    - `action` (String)
    - `resource_id` (UUID)
    - `timestamp` (Timestamp)

### 5.2 Relationships
- **One-to-Many:** `users` $\rightarrow$ `properties` (One user can manage multiple properties).
- **One-to-Many:** `properties` $\rightarrow$ `devices` (A property contains many devices).
- **One-to-Many:** `devices` $\rightarrow$ `device_readings` (A device generates millions of readings).
- **Many-to-One:** `automation_rules` $\rightarrow$ `properties` (Rules are property-scoped).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### 6.1.1 Development (`dev`)
- **Purpose:** Individual feature development and sandboxing.
- **Hosting:** Local Docker containers and a small Fly.io shared app.
- **Database:** Local Postgres 15 instance.
- **CI/CD:** GitHub Actions trigger on push to `feature/*` branches.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Integration testing, QA, and Stakeholder Demos.
- **Hosting:** Fly.io (Scaled to 2 nodes).
- **Database:** Managed Postgres on Fly.io (Mirror of Production schema).
- **Security:** Mocked ISO 27001 environment; limited to internal Talus IPs.
- **CI/CD:** Auto-deploy on merge to `develop` branch.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live regulatory compliance monitoring.
- **Hosting:** Fly.io (High Availability, Multi-region).
- **Database:** Fully redundant PostgreSQL cluster with point-in-time recovery (PITR).
- **Security:** Full ISO 27001 certification. Hardware Security Modules (HSM) for key management.
- **CI/CD:** Manual trigger on `main` branch, following a signed-off QA report from Felix Fischer.

### 6.2 Infrastructure Blockers
**Current Status:** CRITICAL BLOCKER.
The cloud provider (Fly.io) has delayed the provisioning of the dedicated ISO 27001 VPC (Virtual Private Cloud) for the production environment. This has halted the deployment of the `prod` environment, meaning all current testing is limited to `staging`. This must be resolved by the DevOps lead immediately to avoid missing the external beta date.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `ExUnit` (Built-in Elixir).
- **Approach:** Every module boundary must have a corresponding test file. Business logic in `Trellis.Compliance` must have 100% coverage due to the legal nature of the project.
- **Requirement:** All tests must pass in the CI pipeline before a PR can be merged.

### 7.2 Integration Testing
- **Approach:** Focus on the interaction between the Phoenix frontend and the Postgres backend.
- **Tooling:** `Wallaby` for browser-based integration tests.
- **Scope:** Specifically testing the "Critical" features (Dashboard and Rule Builder) to ensure that UI actions correctly trigger database updates and IoT commands.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulated IoT device hardware.
- **Implementation:** A "Mock Device" Elixir script that simulates 1,000 concurrent devices sending telemetry data to the API to test system load and real-time LiveView updates.
- **Verification:** Felix Fischer's QA team will perform "Chaos Engineering" tests, randomly killing nodes in the Fly.io cluster to ensure zero data loss.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements change mid-build | High | High | Escalate to steering committee for additional funding/time. | Kira Moreau |
| R-02 | Budget cut by 30% in next quarter | Medium | High | Assign dedicated owner to track spend; prioritize "Critical" features. | Finance Lead |
| R-03 | Infrastructure provisioning delay | High | Medium | Explore fallback to AWS GovCloud if Fly.io fails to deliver. | DevOps |
| R-04 | Team dysfunction (Kira $\leftrightarrow$ Lead Eng) | High | Medium | Weekly moderated syncs; strict use of Jira/Linear for comms. | HR/VP Product |
| R-05 | Technical Debt (God Class) | High | Medium | Schedule a "Refactor Sprint" after Milestone 1. | Lead Eng |

**Probability/Impact Matrix:**
- **High/High:** Critical (R-01, R-02) $\rightarrow$ Immediate Management Attention.
- **High/Medium:** Warning (R-03, R-04, R-05) $\rightarrow$ Continuous Monitoring.

---

## 9. TIMELINE AND MILESTONES

The project follows a strict 6-month timeline. Any deviation will be flagged as a "Compliance Risk."

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Months 1-2):**
    - Core API development.
    - Implementation of the Rule Builder (Complete).
    - Webhook Framework (Complete).
    - *Dependency: Infrastructure provisioning.*
- **Phase 2: User Interface (Months 3-4):**
    - Development of the Customizable Dashboard.
    - Collaborative Editing logic.
    - Beta user onboarding.
- **Phase 3: Compliance & Hardening (Months 5-6):**
    - ISO 27001 audit and certification.
    - Load testing and performance tuning.
    - Final stakeholder sign-off.

### 9.2 Key Milestones
- **Milestone 1: External beta with 10 pilot users**
    - **Target Date:** 2026-05-15
    - **Success Metric:** 80% feature adoption among pilot users.
- **Milestone 2: Architecture review complete**
    - **Target Date:** 2026-07-15
    - **Goal:** Validate that the "Clean Monolith" is scaling and the "God Class" has been decomposed.
- **Milestone 3: Stakeholder demo and sign-off**
    - **Target Date:** 2026-09-15
    - **Goal:** Final verification of regulatory compliance and production hand-off.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. In accordance with company culture, these recordings are archived and almost never rewatched. The following are summarized takeaways from the recordings.*

### Meeting 1: Sprint Planning - "The Architecture Clash"
- **Date:** 2026-01-20
- **Participants:** Kira Moreau, Lead Engineer, Dayo Santos, Felix Fischer.
- **Discussion:** Kira pushed for a faster rollout of the billing system. The Lead Engineer argued that the billing system is a low priority and that the Dashboard is the only thing that matters for the legal deadline.
- **Outcome:** Kira and the Lead Engineer stopped speaking for the remainder of the call. Dayo Santos agreed to prioritize the Dashboard widgets.
- **Decision:** Billing is officially moved to "Low Priority / In Progress."

### Meeting 2: Technical Debt Review - "The God Class"
- **Date:** 2026-02-05
- **Participants:** Lead Engineer, Selin Santos, Felix Fischer.
- **Discussion:** Selin Santos expressed confusion while trying to add a new email notification. She discovered the `Trellis.Core.Manager` class is 3,000 lines long and handles everything from password hashing to SMTP logs.
- **Outcome:** The Lead Engineer acknowledged it's a "mess" but stated there is no time to fix it until after the Beta.
- **Decision:** The God Class will be documented as technical debt and scheduled for a refactor in July.

### Meeting 3: Infrastructure Emergency
- **Date:** 2026-02-18
- **Participants:** Kira Moreau, DevOps, Felix Fischer.
- **Discussion:** The team realized that the ISO 27001 environment on Fly.io has not been provisioned. Felix noted that he cannot run E2E tests in a production-like environment.
- **Outcome:** High tension. Kira requested an immediate escalation to the provider.
- **Decision:** Infrastructure provisioning is marked as a "Current Blocker."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

### 11.1 Personnel ($580,000)
- **Project Lead (Kira Moreau):** $120,000 (Allocated for 6 months)
- **Frontend Lead (Dayo Santos):** $90,000
- **QA Lead (Felix Fischer):** $80,000
- **Junior Dev (Selin Santos):** $40,000
- **Other Engineers/DevOps (7 members):** $250,000

### 11.2 Infrastructure ($120,000)
- **Fly.io Dedicated Nodes:** $45,000
- **PostgreSQL Managed Cluster:** $30,000
- **ISO 27001 Certification Audit Fees:** $35,000
- **S3 Storage & CDN:** $10,000

### 11.3 Tools & Licenses ($40,000)
- **Stripe Enterprise API:** $10,000
- **Monitoring (Sentry/New Relic):** $15,000
- **Project Management (Linear/Jira):** $5,000
- **Collaborative Tools (Zoom/Slack):** $10,000

### 11.4 Contingency ($60,000)
- **Reserve Fund:** $60,000 (To be used for "Risk 1" escalation or emergency hiring if the project timeline slips).

---

## 12. APPENDICES

### Appendix A: The "God Class" Decomposition Plan
The `Trellis.Core.Manager` class currently handles:
1. User Authentication $\rightarrow$ Move to `Trellis.Accounts.Auth`
2. System Logging $\rightarrow$ Move to `Trellis.Telemetry.Logger`
3. Email Dispatch $\rightarrow$ Move to `Trellis.Notifications.Email`
4. Session Management $\rightarrow$ Move to `Trellis.Accounts.Session`

**Refactor Schedule:**
- Week 1: Extract Email Logic.
- Week 2: Extract Logging.
- Week 3: Extract Auth.
- Week 4: Final cleanup and regression testing.

### Appendix B: ISO 27001 Compliance Checklist
To meet the certification required for the production environment, the following must be implemented:
- [ ] **Access Control:** MFA required for all developers accessing the production console.
- [ ] **Data Encryption:** AES-256 encryption for all data at rest in PostgreSQL.
- [ ] **Audit Logging:** All administrative actions must be recorded in the `audit_trails` table with no possibility of deletion (Append-only).
- [ ] **Network Isolation:** The production database must not be accessible via the public internet (Private Networking only).
- [ ] **Vulnerability Scanning:** Weekly automated scans of all Elixir dependencies using `mix audit`.