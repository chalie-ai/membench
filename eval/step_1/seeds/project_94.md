# PROJECT SPECIFICATION DOCUMENT: KEYSTONE (v1.0.4)
**Project Name:** Keystone  
**Client/Company:** Flintrock Engineering  
**Industry:** Real Estate  
**Document Status:** Finalized for Implementation  
**Last Updated:** October 24, 2023  
**Project Lead:** Gia Santos (CTO)

---

## 1. EXECUTIVE SUMMARY

**Business Justification**
Project Keystone represents a critical strategic pivot for Flintrock Engineering. Following the release of the legacy collaboration tool, the company experienced catastrophic user feedback, characterized by systemic instability, an archaic user interface, and a failure to meet the basic needs of real estate professionals. The current churn rate is unsustainable, and the brand reputation within the real estate sector has been severely compromised. 

The goal of Keystone is a total rebuild. In the real estate industry, the speed of data transmission—property listings, contract revisions, and stakeholder approvals—is a primary competitive advantage. The legacy system failed because it was a static document repository masquerading as a collaboration tool. Keystone will transition the product from a "storage" mindset to a "workflow" mindset, introducing real-time synchronization and advanced discovery tools that allow brokers, engineers, and investors to collaborate on property assets in a shared, live environment.

**ROI Projection**
Given that Keystone is currently unfunded and bootstrapping using existing team capacity, the ROI is calculated primarily through churn reduction and the acquisition of high-value enterprise accounts. 

1. **Churn Reduction:** By replacing the failed legacy system with a high-performance tool, Flintrock expects to reduce the current 15% monthly churn to under 3%.
2. **Market Expansion:** The introduction of a customer-facing API allows for third-party integrations (e.g., integration with MLS or Zillow), opening a new B2B revenue stream.
3. **Operational Efficiency:** The automation engine will reduce manual data entry for users, increasing the "stickiness" of the platform.

The projected financial impact is an increase in Monthly Recurring Revenue (MRR) from the current $12k/month (stagnant) to $85k/month within 12 months of the Milestone 2 stability confirmation. The cost of failure is essentially the total loss of the real estate product vertical.

---

## 2. TECHNICAL ARCHITECTURE

Keystone utilizes a traditional three-tier architecture designed for scalability and maintainability, deployed on AWS Elastic Container Service (ECS).

### 2.1 The Stack
- **Presentation Layer:** React.js (Frontend) communicating via REST and WebSockets.
- **Business Logic Layer:** Python 3.11 / Django 4.2.
- **Data Layer:** PostgreSQL 15 (Relational data) and Redis 7.0 (Caching and Pub/Sub).
- **Infrastructure:** AWS ECS (Fargate), AWS RDS (PostgreSQL), AWS ElastiCache (Redis), and S3 for asset storage.

### 2.2 Architecture Diagram (ASCII)
```text
[ User Browser / Client ] <--- HTTPS/WSS ---> [ AWS Application Load Balancer ]
                                                          |
                                                          v
                                           [ AWS ECS Cluster (Fargate) ]
                                           |  (Django App Instances)  |
                                           |_________________________|
                                            /           |           \
                                           /            |            \
                  [ Redis Cluster ] <---/               |             \---> [ AWS S3 ]
                  (WebSockets/Caching)                   |                (Document Storage)
                                                        v
                                               [ AWS RDS (PostgreSQL) ]
                                               (Primary Application DB)
```

### 2.3 Technical Logic Flow
The application follows a strict separation of concerns. The presentation layer handles the UI state and optimistic updates for real-time collaboration. The business logic layer (Django) manages authentication, validation, and the orchestration of the automation engine. The data layer ensures ACID compliance for billing and property records while utilizing Redis for the high-throughput requirements of the real-time collaborative editor.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** 
The real estate industry deals with massive datasets containing varying attributes (acreage, zoning codes, price ranges, square footage). A standard keyword search is insufficient. Keystone requires a faceted search system that allows users to drill down into properties using a combination of full-text search (for descriptions and notes) and structured filters (for quantitative data).

**Technical Requirements:**
- **Indexing:** Implementation of PostgreSQL GIN (Generalized Inverted Index) for full-text search across the `Property` and `Document` tables.
- **Faceted Logic:** The system must dynamically calculate the count of available records for each filter category (e.g., "Residential (45)", "Commercial (12)").
- **Query Optimization:** Use of materialized views to pre-calculate common filter combinations to prevent expensive JOIN operations during peak usage.
- **User Interface:** A left-hand sidebar containing collapsible filter categories with multi-select checkboxes and range sliders for pricing.

**Blocking Issue:** Current design disagreement between Product and Engineering leads regarding whether to use an external engine (Elasticsearch) or stick to PostgreSQL. Engineering prefers PostgreSQL to minimize infrastructure overhead; Product wants the speed of Elasticsearch.

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** Medium | **Status:** In Design
**Description:**
To integrate with the broader real estate ecosystem, Keystone must provide a robust API for third-party developers and enterprise clients. This API will allow external software to push property updates or pull collaboration logs.

**Technical Requirements:**
- **Versioning:** The API will follow a URI-based versioning strategy (e.g., `/api/v1/`).
- **Sandbox Environment:** A mirrored environment (`sandbox.keystone.flintrock.com`) where users can test API calls against non-production data without affecting live property records.
- **Authentication:** Implementation of OAuth2 and API Key rotations.
- **Rate Limiting:** Redis-backed throttling to prevent API abuse, with tiers based on the user's subscription level (e.g., 1,000 requests/hr for Basic, 10,000 for Enterprise).

### 3.3 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** In Review
**Description:**
Users must be able to edit property descriptions and deal sheets simultaneously. The "last-write-wins" approach of the legacy system caused massive data loss, which is a primary driver for this rebuild.

**Technical Requirements:**
- **Operational Transformation (OT):** Implementation of an OT or CRDT (Conflict-free Replicated Data Type) mechanism to handle concurrent edits.
- **WebSocket Integration:** Use of Django Channels to maintain a persistent connection between the client and the server.
- **Presence Tracking:** A "Who is here" indicator showing active users' cursors and avatars in the document.
- **Concurrency Logic:** When two users edit the same character index, the system must resolve the conflict based on timestamp and user priority levels defined in the workspace settings.

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** Blocked
**Description:**
Real estate workflows are repetitive (e.g., "If property status changes to 'Under Contract', then notify the legal team and create a task for the title search"). Keystone will provide a visual "If-This-Then-That" (IFTTT) style builder.

**Technical Requirements:**
- **Trigger System:** A hook-based system that listens for specific events in the PostgreSQL database (e.g., `PropertyStatusChanged`).
- **Action Registry:** A library of predefined actions (Email, Slack Notification, Task Creation, API Call).
- **Visual Builder:** A React-based drag-and-drop interface that compiles a visual graph into a JSON representation of the rule.
- **Execution Engine:** An asynchronous worker (Celery) that processes the automation queue to ensure the UI remains responsive.

**Blocking Issue:** Blocked pending the completion of the API versioning (Feature 3.2), as the automation engine relies on internal API calls to trigger actions.

### 3.5 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker) | **Status:** In Review
**Description:**
The previous version handled billing manually via invoices, leading to significant revenue leakage. Keystone must automate the entire lifecycle: signup, trial, payment, renewal, and cancellation.

**Technical Requirements:**
- **Stripe Integration:** Complete integration with Stripe Billing for subscription management and recurring payments.
- **Plan Logic:** Support for three tiers: Basic, Professional, and Enterprise.
- **Webhooks:** Implementation of a secure webhook listener to update user permissions in real-time when a payment fails or a plan is upgraded.
- **Dunning Process:** Automated email sequences for failed payments before account suspension.
- **Tax Calculation:** Integration of automated sales tax based on the property's jurisdiction and company headquarters.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer <token>` in the Authorization header.

### 4.1 Property Management
**GET `/api/v1/properties/`**
- **Description:** Retrieve a list of properties with optional faceted filters.
- **Request Params:** `?status=active&price_max=500000&q=downtown`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "count": 1,
    "results": [{"id": "prop_123", "address": "123 Main St", "price": 450000}]
  }
  ```

**POST `/api/v1/properties/`**
- **Description:** Create a new property listing.
- **Request Body:** `{"address": "456 Oak Ave", "price": 600000, "description": "Modern loft"}`
- **Response:** `201 Created`
- **Example Response:** `{"id": "prop_456", "status": "created"}`

### 4.2 Collaboration & Documents
**GET `/api/v1/documents/{doc_id}/`**
- **Description:** Fetch the current state of a collaborative document.
- **Response:** `200 OK`
- **Example Response:** `{"id": "doc_789", "content": "Project Notes...", "version": 42}`

**PATCH `/api/v1/documents/{doc_id}/`**
- **Description:** Update a document fragment (used by OT engine).
- **Request Body:** `{"delta": "Insert 'X' at index 10", "version": 42}`
- **Response:** `200 OK`

### 4.3 Billing & Account
**GET `/api/v1/billing/subscription/`**
- **Description:** Retrieve current subscription status.
- **Response:** `200 OK`
- **Example Response:** `{"plan": "Professional", "renews_at": "2026-01-01"}`

**POST `/api/v1/billing/upgrade/`**
- **Description:** Change the current subscription tier.
- **Request Body:** `{"new_plan": "Enterprise"}`
- **Response:** `200 OK`

### 4.4 Automation Engine
**GET `/api/v1/automations/`**
- **Description:** List all active workflow rules.
- **Response:** `200 OK`
- **Example Response:** `[{"id": "rule_1", "trigger": "status_change", "action": "email_notify"}]`

**POST `/api/v1/automations/`**
- **Description:** Create a new automation rule.
- **Request Body:** `{"trigger": "status_change", "condition": "status == 'Sold'", "action": "archive_doc"}`
- **Response:** `201 Created`

---

## 5. DATABASE SCHEMA

The database is hosted on AWS RDS PostgreSQL. Below are the core tables and their relationships.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `Users` | `user_id (PK)`, `email`, `password_hash`, `role_id` | 1:N with `WorkspaceMembers` | User authentication and profiles. |
| `Workspaces` | `workspace_id (PK)`, `name`, `owner_id` | 1:N with `Properties` | The primary organizational unit. |
| `WorkspaceMembers` | `member_id (PK)`, `user_id (FK)`, `workspace_id (FK)`, `role` | N:1 with `Users` | Mapping users to specific workspaces. |
| `Properties` | `prop_id (PK)`, `workspace_id (FK)`, `address`, `price`, `status` | N:1 with `Workspaces` | Core real estate asset data. |
| `Documents` | `doc_id (PK)`, `prop_id (FK)`, `content`, `version` | N:1 with `Properties` | Collaborative text data for assets. |
| `DocVersions` | `version_id (PK)`, `doc_id (FK)`, `user_id (FK)`, `snapshot` | N:1 with `Documents` | History for conflict resolution. |
| `Automations` | `rule_id (PK)`, `workspace_id (FK)`, `trigger_event`, `action_json` | N:1 with `Workspaces` | Definitions for the rule builder. |
| `Subscriptions` | `sub_id (PK)`, `workspace_id (FK)`, `stripe_id`, `plan_level` | 1:1 with `Workspaces` | Billing status and plan data. |
| `Invoices` | `inv_id (PK)`, `sub_id (FK)`, `amount`, `date_paid` | N:1 with `Subscriptions` | Transactional history. |
| `AuditLogs` | `log_id (PK)`, `user_id (FK)`, `action`, `timestamp` | N:1 with `Users` | Security and change tracking. |

### 5.2 Schema Logic
- **Integrity:** Foreign key constraints are enforced on all relationships to prevent orphaned property records.
- **Indexing:** B-Tree indexes are applied to `email` and `workspace_id`. A GIN index is applied to the `content` field in the `Documents` table for full-text search.
- **Partitioning:** The `AuditLogs` table is partitioned by month to maintain query performance as the log grows.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Deployment Pipeline
Keystone utilizes a Continuous Deployment (CD) model. Every merged Pull Request (PR) to the `main` branch is automatically deployed to production.

**Pipeline Flow:**
`Developer Push` $\rightarrow$ `GitHub Actions (Unit Tests)` $\rightarrow$ `Snyk Security Scan` $\rightarrow$ `Docker Image Build` $\rightarrow$ `Push to AWS ECR` $\rightarrow$ `AWS ECS Service Update`.

### 6.2 Environment Descriptions

#### 6.2.1 Development (Dev)
- **Purpose:** Feature development and local testing.
- **Host:** Local Docker Compose / Individual Dev pods.
- **DB:** Local PostgreSQL container.
- **Access:** Developers only.

#### 6.2.2 Staging (Staging)
- **Purpose:** QA and Product sign-off. This is where the "Sandbox" API resides.
- **Host:** AWS ECS (t3.medium).
- **DB:** RDS Instance (Small).
- **Data:** Sanitized production snapshots.
- **Access:** All team members and selected Beta testers.

#### 6.2.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Host:** AWS ECS Fargate (Auto-scaling).
- **DB:** RDS Multi-AZ High Availability.
- **Caching:** ElastiCache Redis (Clustered).
- **Access:** Restricted via IAM roles and VPN.

---

## 7. TESTING STRATEGY

Given the high-stakes nature of real estate data and the failure of the previous system, a multi-layered testing strategy is mandatory.

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Every business logic function in the Django `services.py` and `models.py` files must have $\ge 90\%$ coverage.
- **Execution:** Triggered on every PR via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between Django, Redis, and PostgreSQL.
- **Focus:** Specifically testing the Operational Transformation (OT) logic for collaborative editing to ensure that two concurrent updates result in a consistent state across all clients.
- **Tooling:** Custom test suites that simulate multiple WebSocket clients sending simultaneous patches.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright
- **Scope:** Critical user journeys (e.g., "User signs up $\rightarrow$ Creates Workspace $\rightarrow$ Adds Property $\rightarrow$ Invites Collaborator $\rightarrow$ Edits Document").
- **Execution:** Weekly full-regression suite run against the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory changes in real estate laws. | Medium | High | Hire a specialized contractor (Rumi Gupta) to maintain a compliance matrix. |
| R-02 | Key Architect leaving in 3 months. | High | High | Immediate documentation of all "magic" logic; knowledge transfer sessions every Tuesday. |
| R-03 | CD pipeline causes production regression. | Medium | Medium | Implementation of automated "Canary" deployments; 5-minute rollback trigger. |
| R-04 | Database performance degradation. | Low | High | Periodic indexing audits and use of RDS Performance Insights. |
| R-05 | Design deadlock between Product/Eng. | High | Medium | CTO (Gia Santos) to make final binding decision by 2023-11-01. |

**Probability/Impact Matrix:**
- **Critical:** (High Prob / High Impact) $\rightarrow$ Immediate action (R-02).
- **Major:** (Medium Prob / High Impact) $\rightarrow$ Continuous monitoring (R-01).
- **Manageable:** (Low Prob / Medium Impact) $\rightarrow$ Standard procedure (R-03, R-04).

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Overview
The project is divided into three primary phases focusing on Feature Completion, Stability, and Final Review.

#### Phase 1: Core Feature Sprint (Now $\rightarrow$ 2026-05-15)
- **Focus:** Clearing launch blockers (Search and Billing).
- **Dependencies:** Billing must be finalized before the API sandbox can be fully tested.
- **Goal:** Reach MVP Feature-Complete status.

#### Phase 2: Stabilization & Scaling (2026-05-16 $\rightarrow$ 2026-07-15)
- **Focus:** Bug scrubbing, performance tuning, and user onboarding.
- **Dependencies:** Successful migration of legacy users to the new schema.
- **Goal:** Confirm post-launch stability.

#### Phase 3: Final Optimization (2026-07-16 $\rightarrow$ 2026-09-15)
- **Focus:** Final architecture review and technical debt cleanup.
- **Dependencies:** Analysis of 60 days of production logs.
- **Goal:** Complete architecture review.

### 9.2 Gantt-Style Sequence
`[2023-10] [Search Design] ----> [Billing Dev] ----> [Collaboration Review] ----> [MVP 2026-05-15] ----> [Stability 2026-07-15] ----> [Arch Review 2026-09-15]`

---

## 10. MEETING NOTES

### Meeting 1: 2023-10-12 (Sync Call)
- **Attendees:** Gia, Yael, Gideon, Rumi.
- **Notes:**
    - Search is a mess.
    - Gia wants Postgres; Product wants Elastic.
    - Blocked.
    - Gideon worried about the "hardcoded values" in the legacy files (40+ files).
    - Action: Yael to audit config files.

### Meeting 2: 2023-10-19 (Async Standup)
- **Updates:**
    - Rumi: API sandbox docs 50% done.
    - Gideon: Security audit internal only. No SOC2 yet.
    - Gia: Budget still zero. We are bootstrapping.
    - Yael: Redis pub/sub working for real-time edits.

### Meeting 3: 2023-10-26 (Emergency Sync)
- **Attendees:** Gia, Gideon.
- **Notes:**
    - Architect leaving in 90 days.
    - Panic.
    - Need to document the "magic" logic for the OT conflict resolution.
    - Gideon to set up a shared Wiki for workarounds.

---

## 11. BUDGET BREAKDOWN

As the project is currently unfunded and bootstrapping with existing team capacity, the "budget" refers to the internal allocation of resources and existing operational costs.

| Category | Allocated Value (Internal/Annual) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,140,000 (Equity/Salary) | 12-person team (Avg $95k/year). |
| **Infrastructure** | $24,000 (AWS Credit/OpEx) | ECS, RDS, ElastiCache, S3. |
| **Tools** | $4,200 (SaaS) | GitHub Enterprise, Snyk, Slack. |
| **Contingency** | $15,000 (Reserve) | Specifically for Rumi's contract extensions. |
| **TOTAL** | **$1,183,200** | **Internal Cost Basis.** |

---

## 12. APPENDICES

### Appendix A: Technical Debt Manifest
The legacy system contains significant technical debt that must be purged during the transition to Keystone. 
- **Hardcoded Configurations:** There are approximately 42 files where database credentials, API keys for legacy services, and environment-specific URLs are hardcoded. 
- **Remediation Plan:** All values are to be moved to AWS Secrets Manager and accessed via a centralized `config.py` wrapper in the new Django app.

### Appendix B: Conflict Resolution Logic (OT)
To ensure real-time stability, Keystone implements a simplified Operational Transformation (OT) approach:
1. **Client-side:** Every change is sent as an operation `Op(type, position, character, version)`.
2. **Server-side:** The server maintains the master version. If a client sends an operation based on `version 10` but the server is already at `version 12`, the server transforms the incoming operation's position based on the missed operations (11 and 12) before applying it to the master document.
3. **Broadcast:** The transformed operation is broadcasted to all other connected clients to ensure eventual consistency.