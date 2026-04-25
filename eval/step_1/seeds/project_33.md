# PROJECT SPECIFICATION DOCUMENT: SENTINEL
**Document Version:** 1.0.4  
**Date:** October 26, 2023  
**Status:** Draft / Under Review  
**Company:** Duskfall Inc.  
**Classification:** Confidential / Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project "Sentinel" is a strategic pivot for Duskfall Inc., transforming a high-impact internal productivity tool—born from a corporate hackathon—into a full-scale, enterprise-grade e-commerce marketplace specifically tailored for the logistics and shipping industry. Currently serving 500 daily internal users, the tool has proven its utility in optimizing shipping workflows. The objective is to transition this tool from a "utility" to a "platform," enabling external vendors and logistics partners to transact and manage shipping services in a secure, multi-tenant environment.

### 1.2 Business Justification
The logistics industry is currently plagued by fragmented communication and archaic manual ordering systems. Duskfall Inc. has identified a market gap for a centralized marketplace where shipping capacity can be traded and managed with real-time visibility. By leveraging the existing internal success of the prototype, Sentinel aims to capture this market share. The project is designated as a flagship initiative, reporting directly to the Board of Directors, reflecting its criticality to the company’s 2025 growth strategy.

### 1.3 ROI Projection and Financial Impact
With a budget allocation exceeding $5M, Duskfall Inc. anticipates a high Return on Investment based on the following projections:
- **Revenue Generation:** Transitioning to a transactional model with a 2.5% marketplace commission fee per shipment booked.
- **Operational Efficiency:** An estimated 30% reduction in manual procurement time for logistics partners.
- **Market Position:** By deploying a SOC 2 Type II compliant platform, Duskfall Inc. will be the first in its niche to offer a "Security-First" logistics marketplace, providing a competitive moat against legacy providers.
- **Projected Break-even:** Estimated at 14 months post-launch, assuming a conversion rate of 15% of current internal users to external paying tenants.

### 1.4 Strategic Objective
The primary goal is to move from a modular monolith to a scalable microservices architecture that can support an increase from 500 users to 50,000+ users without degradation in performance. The transition will be incremental to ensure business continuity.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Stack
- **Language/Framework:** Python 3.11 with FastAPI (chosen for asynchronous capabilities and high performance).
- **Database:** MongoDB 6.0 (chosen for flexible schema requirements in logistics manifests).
- **Task Queue:** Celery with Redis as the broker (for asynchronous processing of shipping labels and notifications).
- **Containerization:** Docker Compose for local development and orchestration.
- **Deployment:** Self-hosted on private cloud infrastructure to maintain strict control over data residency.

### 2.2 Architecture Philosophy: The Incremental Shift
Sentinel is currently a **Modular Monolith**. To avoid "Big Bang" rewrite failures, the team is implementing a "Strangler Fig" pattern. Critical features (e.g., the Notification System and API Gateway) are being developed as independent services that communicate via REST and RabbitMQ, while the core order processing remains in the monolith until Milestone 3.

### 2.3 ASCII Architecture Diagram
```text
[ External Clients ] ----> [ API Gateway / Nginx ] ----> [ Auth Layer (JWT) ]
                                     |
                                     v
                    +---------------------------------------+
                    |        MODULAR MONOLITH (Core)         |
                    |  +---------------------------------+  |
                    |  |  Order Management Module         |  |
                    |  +---------------------------------+  |
                    |  |  Shipping Logic Module           |  |
                    |  +---------------------------------+  |
                    |  |  User & Role Management          |  |
                    |  +---------------------------------+  |
                    +---------------------------------------+
                                     |            ^
                                     v            |
                    +---------------------------------------+
                    |        ASYNCHRONOUS LAYER             |
                    |  [ Celery Workers ] <--> [ Redis ]    |
                    +---------------------------------------+
                                     |            ^
                                     v            |
                    +---------------------------------------+
                    |        DATA PERSISTENCE                |
                    |  [ MongoDB Cluster ] [ Audit Log Store ]|
                    +---------------------------------------+
```

### 2.4 Infrastructure Constraints
Because the platform is self-hosted, the team is responsible for the entire OSI model from the application layer down to the virtualized hardware. All deployments must pass through a manual QA gate, creating a mandatory 2-day turnaround for any production push to ensure stability.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging (Priority: Critical - Launch Blocker)
**Status: Not Started**

The Audit Trail is the most critical component for SOC 2 Type II compliance. Every state-changing action within Sentinel must be recorded in a manner that is immutable and tamper-evident.

**Functional Requirements:**
- **Comprehensive Capture:** The system must log the Actor (User ID), Action (e.g., "Update Shipping Rate"), Timestamp (UTC), IP Address, and the "Before" and "After" state of the modified object.
- **Tamper-Evidence:** To prevent administrative manipulation of logs, the system will implement a cryptographic chaining mechanism. Each log entry will contain a SHA-256 hash of the previous entry.
- **Storage Strategy:** Logs will be stored in a dedicated MongoDB collection with "Append-Only" permissions at the database level.
- **Retrieval:** An internal admin dashboard will allow auditors to query logs by timeframe, user, or resource ID.

**Technical Specification:**
The logging middleware will intercept every `POST`, `PUT`, `PATCH`, and `DELETE` request in FastAPI. The middleware will serialize the request body and the resulting response. To avoid performance degradation, logs will be pushed to a Celery queue and written asynchronously to the Audit Store.

**Compliance Goal:** This feature directly satisfies the "Common Criteria" for security and confidentiality under SOC 2, ensuring that unauthorized changes to shipping data can be detected and traced.

### 3.2 Customer-Facing API (Priority: Critical - Launch Blocker)
**Status: In Design**

Sentinel will not just be a web portal; it will be a platform. The API allows logistics partners to integrate their own Warehouse Management Systems (WMS) directly into the Sentinel marketplace.

**Functional Requirements:**
- **Versioning:** The API will use URI versioning (e.g., `/api/v1/`) to ensure backward compatibility.
- **Sandbox Environment:** A mirrored "Sandbox" environment will be provided to clients. This environment will use a separate MongoDB instance with mocked payment gateways, allowing developers to test integrations without affecting production data.
- **Rate Limiting:** To prevent DDoS and resource exhaustion, the API will implement tiered rate limiting (e.g., 1,000 requests/hour for Standard, 10,000 for Enterprise).
- **Authentication:** API Key-based authentication combined with OAuth2 for high-privilege operations.

**Technical Specification:**
The API will be built using FastAPI's dependency injection system to handle authentication and rate-limiting. Request/Response validation will be strictly enforced using Pydantic models to ensure data integrity.

**Client Experience:** A developer portal will be provided, containing Swagger/OpenAPI documentation and a "Try it Out" interactive console.

### 3.3 Notification System (Priority: High)
**Status: In Design**

Real-time communication is vital in logistics. The notification system must bridge the gap between automated system events and human action.

**Functional Requirements:**
- **Multi-Channel Delivery:** The system must support four distinct channels:
    - **Email:** For formal confirmations and invoices (via SendGrid).
    - **SMS:** For urgent delivery alerts (via Twilio).
    - **In-App:** A notification bell and toast alerts for logged-in users.
    - **Push:** Mobile alerts for drivers and warehouse managers (via Firebase).
- **User Preferences:** A "Notification Center" where users can toggle which events trigger which channels (e.g., "Email me for invoices, but SMS me for delivery delays").
- **Templating Engine:** A dynamic template system allowing the business team to edit notification wording without developer intervention.

**Technical Specification:**
A `NotificationDispatcher` service will be created. When a system event occurs (e.g., `Order_Shipped`), the dispatcher will query the user's preferences and route the message to the appropriate provider. This will be handled entirely via Celery to ensure the main application thread is never blocked by third-party API latency.

### 3.4 Workflow Automation Engine (Priority: Medium)
**Status: In Progress**

To provide value to large shipping firms, Sentinel must allow them to automate repetitive tasks based on custom business rules.

**Functional Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface where users can define "If-This-Then-That" (IFTTT) logic. Example: *If [Shipment Weight] > 500kg AND [Destination] == "International", Then [Set Priority] to "High" AND [Notify] "Logistics Manager".*
- **Trigger Events:** Support for system triggers (status changes, time-based delays, value thresholds).
- **Action Library:** A predefined set of actions including updating record fields, sending notifications, or triggering external API webhooks.

**Technical Specification:**
The engine will utilize a JSON-based logic tree stored in MongoDB. A specialized "Rule Evaluator" service will monitor the system's event stream. When an event matches a rule's trigger, the evaluator will execute the associated action chain. To prevent infinite loops (e.g., Rule A triggers Rule B, which triggers Rule A), a maximum recursion depth of 5 will be enforced.

### 3.5 Multi-Tenant Data Isolation (Priority: Medium)
**Status: In Design**

As Sentinel moves from an internal tool to a marketplace, it must support multiple independent companies (tenants) on the same infrastructure.

**Functional Requirements:**
- **Logical Isolation:** Every single record in the database must be associated with a `tenant_id`.
- **Strict Access Control:** The system must ensure that a user from Tenant A can never view, edit, or even know the existence of data from Tenant B.
- **Shared Infrastructure:** To optimize costs, tenants will share the same MongoDB cluster and FastAPI application instances, but their data will be logically partitioned.
- **Tenant Onboarding:** A streamlined process to create a new tenant, assign an admin user, and initialize default settings.

**Technical Specification:**
The team will implement a "Tenant Middleware" in FastAPI. Every request will be intercepted to extract the `tenant_id` from the authenticated JWT. This ID will be automatically injected into every MongoDB query filter (e.g., `db.orders.find({ "tenant_id": current_tenant_id, "order_id": id })`). This prevents "leaky" queries where a developer might forget to add the tenant filter manually.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under the base URL `https://api.sentinel.duskfall.com/v1/`.

### 4.1 Logistics Endpoints

#### `GET /shipments`
- **Description:** Retrieves a list of shipments for the authenticated tenant.
- **Query Parameters:** `status` (string), `page` (int), `limit` (int).
- **Request Example:** `GET /shipments?status=pending&page=1&limit=20`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "SHIP-101", "origin": "NYC", "destination": "LON", "status": "pending" }
  ],
  "pagination": { "total": 150, "page": 1, "pages": 8 }
}
```

#### `POST /shipments`
- **Description:** Creates a new shipment request.
- **Request Body:**
```json
{
  "origin_address": "123 Industrial Way, NY",
  "destination_address": "456 Port Rd, London",
  "weight": 450.5,
  "dimensions": {"l": 100, "w": 80, "h": 60},
  "priority": "standard"
}
```
- **Response (201 Created):**
```json
{ "id": "SHIP-102", "status": "created", "estimated_delivery": "2025-05-20" }
```

#### `PATCH /shipments/{id}`
- **Description:** Updates shipment details or status.
- **Request Body:** `{ "status": "in_transit" }`
- **Response (200 OK):** `{ "id": "SHIP-101", "status": "in_transit", "updated_at": "2025-04-10T10:00Z" }`

#### `GET /rates/quote`
- **Description:** Calculates an estimated shipping cost based on weight and distance.
- **Request Body:** `{ "origin_zip": "10001", "dest_zip": "SW1A 1AA", "weight": 10.5 }`
- **Response (200 OK):** `{ "quote_id": "Q-99", "amount": 125.50, "currency": "USD" }`

### 4.2 Management Endpoints

#### `POST /auth/login`
- **Description:** Authenticates user and returns a JWT.
- **Request Body:** `{ "email": "user@company.com", "password": "secretpassword" }`
- **Response (200 OK):** `{ "token": "eyJhbG...", "expires_in": 3600 }`

#### `GET /tenants/settings`
- **Description:** Retrieves the current tenant's configuration.
- **Response (200 OK):** `{ "tenant_name": "GlobalLogistics Co", "plan": "Enterprise", "feature_flags": ["automation_engine", "sms_alerts"] }`

#### `POST /notifications/preferences`
- **Description:** Updates user alert settings.
- **Request Body:** `{ "email": true, "sms": false, "push": true }`
- **Response (200 OK):** `{ "status": "updated" }`

#### `GET /audit/logs`
- **Description:** Retrieves the tamper-evident audit trail (Admin only).
- **Query Parameters:** `resource_id` (string), `start_date` (ISO8601).
- **Response (200 OK):**
```json
[
  { "timestamp": "2025-04-01T12:00Z", "user": "admin_1", "action": "UPDATE_PRICE", "prev": 100, "new": 110, "hash": "a1b2c3d4..." }
]
```

---

## 5. DATABASE SCHEMA (MONGODB)

Given the use of MongoDB, the schema is defined by document collections. Relationships are maintained via `ObjectId` references.

### 5.1 Collections Overview

| Collection Name | Primary Key | Key Fields | Relationship |
| :--- | :--- | :--- | :--- |
| `Tenants` | `_id` | `company_name`, `subscription_tier`, `created_at` | One-to-Many with Users |
| `Users` | `_id` | `email`, `password_hash`, `role`, `tenant_id` | Many-to-One with Tenants |
| `Shipments` | `_id` | `tracking_number`, `tenant_id`, `status`, `weight` | Many-to-One with Tenants |
| `Quotes` | `_id` | `amount`, `currency`, `shipment_id`, `expires_at` | One-to-One with Shipments |
| `AuditLogs` | `_id` | `timestamp`, `user_id`, `action`, `prev_state`, `next_state`, `hash` | Many-to-One with Users |
| `NotificationPrefs` | `_id` | `user_id`, `channel_email`, `channel_sms`, `channel_push` | One-to-One with Users |
| `WorkflowRules` | `_id` | `tenant_id`, `trigger_event`, `conditions_json`, `actions_json` | Many-to-One with Tenants |
| `Addresses` | `_id` | `street`, `city`, `country`, `tenant_id` | Many-to-One with Tenants |
| `Invoices` | `_id` | `shipment_id`, `amount`, `payment_status`, `due_date` | One-to-One with Shipments |
| `APIKeys` | `_id` | `key_hash`, `user_id`, `tenant_id`, `last_used` | Many-to-One with Users |

### 5.2 Key Relationship Logic
- **Data Isolation:** The `tenant_id` field is present in 9 out of 10 collections. It is the primary index for all queries.
- **Audit Chain:** The `AuditLogs` collection uses the `hash` field to link to the previous record, creating a linked list of all system changes.
- **Workflow Mapping:** `WorkflowRules` link to the event stream. When a `Shipment` status changes, the system queries the `WorkflowRules` collection for all rules where `trigger_event == "SHIPMENT_STATUS_CHANGE"`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes three distinct environments to ensure that the manual QA gate is effective.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and local testing.
- **Infrastructure:** Local Docker Compose setups for each developer.
- **Data:** Mocked data and sanitized snapshots of production.
- **Deployment:** Continuous integration via Git branches.

#### 6.1.2 Staging (QA Gate)
- **Purpose:** Pre-production validation and User Acceptance Testing (UAT).
- **Infrastructure:** A mirror of the production environment (dedicated servers).
- **Data:** Full-scale anonymized production data.
- **Deployment:** Triggered upon merge to `main`. This environment is where the **2-day turnaround** occurs. No code reaches production without 48 hours of stability in Staging.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Infrastructure:** High-availability cluster with load balancers.
- **Data:** Live encrypted customer data.
- **Deployment:** Manual trigger by Gemma Fischer after QA sign-off.

### 6.2 Security and Compliance
- **SOC 2 Type II:** The infrastructure is hardened using SSH key-only access, encrypted disks (AES-256), and mandatory MFA for all developers.
- **Network:** All traffic is routed through an Nginx reverse proxy with SSL termination.
- **Secrets Management:** Environment variables are managed via an encrypted vault; no secrets are stored in the repository.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Individual business logic functions and Pydantic model validations.
- **Tooling:** `pytest` with `pytest-mock`.
- **Requirement:** 80% minimum code coverage for all new modules.
- **Execution:** Runs on every push to GitHub via CI pipeline.

### 7.2 Integration Testing
- **Focus:** API endpoint flow, MongoDB query correctness, and Celery task execution.
- **Approach:** Testing the interaction between FastAPI and the database using a temporary "Test MongoDB" Docker container.
- **Scope:** Validating that the `tenant_id` isolation middleware correctly prevents cross-tenant data access.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "Create Shipment" $\rightarrow$ "Get Quote" $\rightarrow$ "Payment" $\rightarrow$ "Notification").
- **Tooling:** Playwright for frontend-to-backend flow validation.
- **Execution:** Run in the Staging environment prior to the production deployment gate.

### 7.4 Performance Testing
- **Focus:** Testing the impact of raw SQL bypasses in the ORM.
- **Metric:** Latency for the top 10 most frequent queries must remain under 200ms under a load of 500 concurrent users.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead in market release | High | Critical | Develop a "Fallback Architecture" that prioritizes the MVP launch over the full microservices transition to hit the market faster. |
| R-02 | Primary vendor EOL for key dependency | Medium | High | Engage an external consultant to perform an independent assessment of alternative libraries and provide a migration path. |
| R-03 | Technical Debt: Raw SQL usage (30% of queries) | High | Medium | Implement a "Migration Sprint" every 4 weeks to replace raw SQL with optimized ORM queries or safe stored procedures. |
| R-04 | SOC 2 Audit failure on first attempt | Low | Critical | Conduct a "Pre-Audit" internal review and implement the Audit Trail logging feature as the top priority. |
| R-05 | Dependency on external team (3 weeks behind) | High | Medium | Establish a daily sync with the external team lead and identify if a "mock" version of their deliverable can be used in the interim. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required (R-01, R-05).
- **High/Medium:** Regular monitoring and planned remediation (R-03).
- **Medium/High:** Contingency planning (R-02).

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase 1: Foundational Stability (Now – April 15, 2025)
- **Focus:** Stabilizing the modular monolith and completing the core API design.
- **Key Activity:** Transitioning the internal tool to the new multi-tenant structure.
- **Dependency:** Completion of the API Gateway.
- **Milestone 1:** Architecture review complete (2025-04-15).

### 9.2 Phase 2: Security & Compliance (April 16 – June 15, 2025)
- **Focus:** Implementation of the Audit Trail and SOC 2 hardening.
- **Key Activity:** Implementing the cryptographic hashing for logs and external security penetration testing.
- **Dependency:** Audit Trail must be "Critical" status complete.
- **Milestone 2:** Security audit passed (2025-06-15).

### 9.3 Phase 3: Feature Expansion (June 16 – August 15, 2025)
- **Focus:** Notification system, Workflow engine, and Sandbox environment.
- **Key Activity:** Beta testing with 10 selected external partners.
- **Dependency:** Multi-tenant isolation must be verified.
- **Milestone 3:** Stakeholder demo and sign-off (2025-08-15).

### 9.4 Phase 4: Launch & Scale (August 16, 2025 – Forward)
- **Focus:** Public release and transition to full microservices.
- **Key Activity:** Monitoring the 99.9% uptime metric.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per project culture, Duskfall Inc. does not keep formal meeting minutes. The following is a synthesis of decisions made in the `#proj-sentinel-dev` Slack channel.*

### Thread 1: "The ORM Problem" (Date: 2023-11-12)
- **Javier Stein:** "The raw SQL in the shipping manifest queries is making the schema migration a nightmare. I'm terrified to touch the `Shipments` collection."
- **Gemma Fischer:** "I agree. We did it for performance during the hackathon, but it's a liability now. Ravi, can you start mapping out all the raw SQL calls?"
- **Ravi Park:** "On it. I'll create a spreadsheet of every raw query and its purpose."
- **Decision:** The team decided to allocate 20% of every sprint to "ORM Recovery" to phase out raw SQL.

### Thread 2: "The Competitor Threat" (Date: 2023-12-05)
- **Wyatt Fischer:** "Marketing just told me 'LogiFast' is launching their marketplace in February. They're about 8 weeks ahead of us."
- **Gemma Fischer:** "We can't rush the security audit, but we can change the architecture. Let's build a contingency plan. If we can't finish the microservices transition by June, we'll launch as a scaled-up monolith and migrate in the background."
- **Decision:** Agreed on a "Fallback Architecture" to ensure a Q3 2025 launch regardless of microservice progress.

### Thread 3: "SOC 2 Blocking" (Date: 2024-01-20)
- **Gemma Fischer:** "The Board is breathing down my neck about the audit. The Audit Trail is currently 'Not Started' but it's the biggest blocker for SOC 2."
- **Javier Stein:** "If we use a standard log, the auditors will say it's too easy to edit. We need the hash-chaining."
- **Wyatt Fischer:** "Can we make the audit logs viewable to the customer too? For transparency?"
- **Gemma Fischer:** "No, that's a security risk. Audit logs are for admins and auditors only."
- **Decision:** Audit Trail is officially promoted to "Critical - Launch Blocker" and prioritized over the Workflow Engine.

---

## 11. BUDGET BREAKDOWN

**Total Budgeted:** $5,250,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,412,500 | 8 FTEs (incl. Tech Lead, Frontend Lead, Designer) over 18 months. |
| **Infrastructure** | 15% | $787,500 | Private cloud hosting, MongoDB Atlas clusters, Redis, and Backup storage. |
| **Tools & Licenses** | 5% | $262,500 | Docker Enterprise, SendGrid, Twilio, Firebase, SOC 2 Audit fees. |
| **Consultancy** | 5% | $262,500 | External security auditors and the EOL vendor assessment consultant. |
| **Contingency** | 10% | $525,000 | Reserve for emergency scaling or accelerated development. |

---

## 12. APPENDICES

### Appendix A: Performance Benchmarks
To maintain the success criterion of 99.9% uptime, the following performance targets are established for the API:
- **P95 Latency:** < 300ms for all `GET` requests.
- **P99 Latency:** < 800ms for complex `POST` requests (including Celery dispatch).
- **Concurrent Users:** The system must support 5,000 concurrent WebSocket connections for real-time shipping updates without increasing CPU utilization beyond 70% on the application nodes.

### Appendix B: SOC 2 Compliance Mapping
| SOC 2 Principle | Sentinel Feature | Validation Method |
| :--- | :--- | :--- |
| **Security** | Multi-tenant Data Isolation | Automated penetration tests verifying no cross-tenant data leak. |
| **Confidentiality** | AES-256 Disk Encryption | Verification of volume encryption settings in the private cloud. |
| **Availability** | 99.9% Uptime Target | Load balancer health checks and automated failover testing. |
| **Processing Integrity** | Tamper-Evident Audit Trail | Cryptographic hash verification of the `AuditLogs` collection. |