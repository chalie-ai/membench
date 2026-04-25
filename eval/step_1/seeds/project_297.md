Due to the extreme length requirements of this request (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity Project Specification Document. To ensure the depth and detail required for a development team to reference daily, I have expanded every provided constraint into a professional corporate framework.

***

# PROJECT SPECIFICATION: RAMPART
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Company:** Bellweather Technologies  
**Project Lead:** Felix Oduya (CTO)  
**Date:** October 26, 2023 (Last Updated)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Rampart" is a strategic SaaS platform developed by Bellweather Technologies to serve as the primary integration layer for our automotive partnership ecosystem. The automotive industry is currently undergoing a massive shift toward software-defined vehicles and integrated supply chain logistics. Bellweather Technologies has identified a critical gap in how partnership data is synced between OEMs (Original Equipment Manufacturers) and third-party logistics providers.

Rampart is designed to solve this by providing a robust, secure, and scalable interface that syncs with an external partner’s API. The business necessity stems from a strategic partnership agreement where Bellweather must provide a portal for the partner's clients to manage workflows, billing, and automotive data synchronization. Without Rampart, the company remains dependent on manual data entry and fragmented email communication, which introduces unacceptable operational risks and latency in the supply chain.

### 1.2 Strategic Objectives
The primary objective is to transition from a manual partnership model to an automated, API-driven SaaS model. By leveraging a modular monolith architecture, Rampart will provide a stable environment for critical automotive workflows while allowing for the future extraction of microservices as the user base grows.

### 1.3 ROI Projection
The Return on Investment (ROI) for Rampart is calculated based on three primary levers:
1. **Operational Efficiency:** Reduction of manual data entry hours by an estimated 85% across the partnership team.
2. **Revenue Growth:** The ability to scale the partnership to 10,000 monthly active users (MAUs) without a linear increase in support staff.
3. **Risk Mitigation:** Elimination of data silos and the reduction of synchronization errors that currently result in an average loss of $12,000 per incident in logistics penalties.

We project a break-even point within 14 months post-launch, with a projected 3-year net present value (NPV) of $4.2M, assuming the successful attainment of 10,000 MAUs.

### 1.4 High-Level Scope
Rampart encompasses the development of a customizable dashboard, a visual workflow automation engine, a comprehensive RBAC system, and a localized interface for global automotive markets. All infrastructure is strictly on-premise, adhering to the rigid security requirements of the Bellweather data center.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Rampart is built as a **Modular Monolith**. This approach was selected to minimize network latency and simplify deployment in an on-premise environment while maintaining clear boundaries between domains (Billing, Auth, Workflow, Dashboard). As the system scales, these modules are designed to be extracted into independent microservices via the "Strangler Fig" pattern.

### 2.2 Technology Stack
- **Backend:** Java 17 / Spring Boot 3.x
- **Database:** Oracle Database 19c (Enterprise Edition)
- **Frontend:** React 18 with TypeScript (integrated via GitLab CI)
- **Deployment:** Kubernetes (on-premise cluster)
- **CI/CD:** GitLab CI (Internal)
- **Infrastructure:** Physical Rack Servers (Bellweather Data Center)
- **Caching:** Redis (Internal cluster)

### 2.3 System Diagram (ASCII Representation)

```text
[ Client Browser ] <---> [ Load Balancer (F5) ] 
                                 |
                                 v
                    [ Kubernetes Cluster (On-Prem) ]
                    |-----------------------------|
                    |  [ Rampart Modular Monolith]|
                    |  |--- Module: Auth/RBAC     || <--> [ Oracle DB 19c ]
                    |  |--- Module: Billing       || <--> [ Redis Cache ]
                    |  |--- Module: Dashboard    ||
                    |  |--- Module: Workflow      ||
                    |  |--- Module: I18n/Loc      ||
                    |-----------------------------|
                                 |
                                 v
                    [ External Partner API (HTTPS) ]
                    (Syncs on Partner's Timeline)
```

### 2.4 Data Flow and Sync Logic
Because the project depends on an external API on the partner's timeline, Rampart utilizes an **Asynchronous Polling & Webhook Pattern**.
1. The `ExternalSyncService` schedules tasks via Spring Quartz.
2. Data is fetched from the partner API and staged in a `sync_staging` table.
3. A validation engine checks the data against internal Bellweather rules.
4. Validated data is committed to the primary Oracle schema.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:** 
The dashboard serves as the primary landing page for automotive partners. It must allow users to configure their workspace by adding, removing, and rearranging "Widgets" that visualize key performance indicators (KPIs) related to their automotive fleet and partnership status.

**Functional Requirements:**
- **Widget Catalog:** Users can select from a library of widgets (e.g., "Active Shipments," "Billing Status," "Workflow Alerts," "Partner Sync Health").
- **Drag-and-Drop Interface:** Implementation of `react-grid-layout` to allow users to resize and reposition widgets on a 12-column grid.
- **Persistence:** The layout configuration (X, Y coordinates, width, height) must be stored as a JSON blob in the `user_dashboard_config` table.
- **Real-time Updates:** Widgets must utilize WebSocket (via Spring Message Broker) to update data without page refreshes.

**Technical Constraints:**
- The dashboard must load in under 2 seconds.
- State must be persisted every time a widget is moved (debounced by 500ms).
- Support for "Read-Only" templates defined by administrators.

**User Story:** *As a Fleet Manager, I want to place my "Urgent Alerts" widget at the top left of my screen so that I can immediately see critical issues upon login.*

---

### 3.2 Localization and Internationalization (L10n/I18n)
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:** 
To support the global nature of the automotive industry, Rampart must support 12 specific languages. This involves not just translation, but regional formatting for dates, currencies, and measurements.

**Functional Requirements:**
- **Supported Languages:** English (US), English (UK), German, French, Spanish, Italian, Japanese, Korean, Mandarin, Portuguese (BR), Arabic, and Russian.
- **Dynamic Switching:** Users can change their language preference in the Profile settings, triggering a global state change in the React frontend.
- **Resource Bundles:** Use of Java `.properties` files for backend error messages and JSON translation files for the frontend.
- **Regional Formatting:** Dates must follow the ISO 8601 standard but be displayed based on locale (e.g., MM/DD/YYYY for US, DD/MM/YYYY for UK).

**Technical Constraints:**
- Right-to-Left (RTL) support is mandatory for the Arabic localization.
- The system must default to English (US) if the user's browser locale is not among the 12 supported languages.

**User Story:** *As a Japanese Logistics Officer, I want to view the interface in Japanese so that I can operate the system without language barriers.*

---

### 3.3 Automated Billing and Subscription Management
**Priority:** High | **Status:** Complete

**Description:** 
This module handles the financial relationship between Bellweather Technologies and the SaaS users. It manages subscription tiers, automated invoicing, and payment processing.

**Functional Requirements:**
- **Tier Management:** Support for "Basic," "Professional," and "Enterprise" tiers with varying feature flags.
- **Automated Invoicing:** Generation of monthly PDF invoices via a scheduled JasperReports job.
- **Subscription Lifecycle:** Logic to handle upgrades, downgrades, and cancellations.
- **Payment Gateway Integration:** Integration with the internal corporate payment rail (on-premise financial gateway).

**Technical Constraints:**
- All financial calculations must use `BigDecimal` to avoid floating-point precision errors.
- Audit logs for every billing change must be stored in an immutable `billing_audit_trail` table.
- Invoices must be archived for 7 years per corporate policy.

**User Story:** *As a Billing Administrator, I want the system to automatically charge the client's account on the 1st of every month so that we maintain a steady cash flow.*

---

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** Not Started

**Description:** 
A secure identity management system ensuring that users only access data and features they are authorized to use. This is the foundation of the platform's security.

**Functional Requirements:**
- **Multi-Factor Authentication (MFA):** Integration with internal TOTP (Time-based One-Time Password) services.
- **Role Hierarchy:** Definition of roles: `SuperAdmin` > `OrgAdmin` > `Manager` > `Viewer`.
- **Permission Mapping:** Permissions are mapped to specific API endpoints and UI components (e.g., `EDIT_BILLING`, `VIEW_DASHBOARD`).
- **Session Management:** JWT-based authentication with short-lived access tokens (15 mins) and longer-lived refresh tokens (7 days) stored in the Oracle DB.

**Technical Constraints:**
- Passwords must be hashed using BCrypt with a work factor of 12.
- Unauthorized attempts to access endpoints must return a `403 Forbidden` with a logged security event.
- Session timeouts must occur after 30 minutes of inactivity.

**User Story:** *As a Viewer, I should be able to see the dashboard but I should not be able to modify the workflow rules.*

---

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:** 
The "core" of Rampart. This engine allows users to create complex "If-This-Then-That" (IFTTT) logic to automate automotive logistics tasks.

**Functional Requirements:**
- **Visual Rule Builder:** A node-based drag-and-drop editor (using `React Flow`) where users can connect "Triggers," "Conditions," and "Actions."
- **Trigger Library:** Events such as `ShipmentCreated`, `SyncFailed`, `InventoryLow`, or `DateReached`.
- **Condition Logic:** Support for AND/OR gates and comparison operators (e.g., `Inventory < 10`).
- **Action Execution:** Ability to send notifications, trigger external API calls, or update internal record statuses.

**Technical Constraints:**
- The engine must use a directed acyclic graph (DAG) to prevent infinite loops in workflow execution.
- Workflow execution must be asynchronous, utilizing a RabbitMQ message queue to ensure no triggers are missed.
- Maximum execution time for a single workflow chain is 30 seconds.

**User Story:** *As an Operations Manager, I want to create a rule that says "If a shipment is delayed by > 24 hours AND the priority is High, then send an alert to the Account Manager."*

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests/responses use `application/json`.

### 4.1 Dashboard Endpoints
**Endpoint:** `GET /api/v1/dashboard/config`
- **Description:** Retrieves the user's current dashboard layout.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK`
  ```json
  {
    "userId": "12345",
    "layout": [
      {"id": "widget_1", "x": 0, "y": 0, "w": 4, "h": 2},
      {"id": "widget_2", "x": 4, "y": 0, "w": 8, "h": 2}
    ]
  }
  ```

**Endpoint:** `POST /api/v1/dashboard/config`
- **Description:** Updates the user's dashboard layout.
- **Request Body:**
  ```json
  {
    "layout": [{"id": "widget_1", "x": 0, "y": 0, "w": 6, "h": 4}]
  }
  ```
- **Response:** `204 No Content`

### 4.2 Workflow Endpoints
**Endpoint:** `GET /api/v1/workflows`
- **Description:** Lists all active workflows for the organization.
- **Response:** `200 OK`
  ```json
  [
    {"id": "wf_001", "name": "Delayed Shipments Alert", "status": "ACTIVE"}
  ]
  ```

**Endpoint:** `POST /api/v1/workflows/execute`
- **Description:** Manually triggers a workflow for testing.
- **Request Body:** `{"workflowId": "wf_001", "testData": {...}}`
- **Response:** `202 Accepted`

### 4.3 Billing Endpoints
**Endpoint:** `GET /api/v1/billing/subscription`
- **Description:** Returns current plan and renewal date.
- **Response:** `200 OK`
  ```json
  {
    "plan": "Enterprise",
    "nextBillingDate": "2025-01-01",
    "status": "ACTIVE"
  }
  ```

**Endpoint:** `PATCH /api/v1/billing/upgrade`
- **Description:** Upgrades the user to a higher tier.
- **Request Body:** `{"newPlanId": "plan_enterprise_01"}`
- **Response:** `200 OK`

### 4.4 User/Auth Endpoints
**Endpoint:** `POST /api/v1/auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request Body:** `{"username": "foduya", "password": "..."}`
- **Response:** `200 OK`
  ```json
  { "accessToken": "eyJ...", "refreshToken": "fXy..." }
  ```

**Endpoint:** `GET /api/v1/auth/me`
- **Description:** Returns the profile and roles of the currently authenticated user.
- **Response:** `200 OK`
  ```json
  { "username": "foduya", "roles": ["SuperAdmin"], "email": "felix@bellweather.com" }
  ```

---

## 5. DATABASE SCHEMA

**Database:** Oracle 19c
**Schema Name:** `RAMPART_PROD`

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Key(s) | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `username`, `password_hash`, `email`, `mfa_secret` | Core user identity |
| `roles` | `role_id` | None | `role_name`, `description` | RBAC role definitions |
| `user_roles` | `id` | `user_id`, `role_id` | `assigned_at` | Maps users to roles |
| `organizations` | `org_id` | None | `org_name`, `tax_id`, `country_code` | Partnership entities |
| `subscriptions` | `sub_id` | `org_id` | `plan_type`, `start_date`, `end_date`, `status` | Billing state |
| `billing_invoices` | `invoice_id` | `sub_id` | `amount`, `due_date`, `paid_status`, `pdf_link` | Financial records |
| `dashboards` | `dash_id` | `user_id` | `config_json`, `updated_at` | Widget layout storage |
| `workflow_defs` | `wf_id` | `org_id` | `dag_structure_json`, `name`, `is_active` | Workflow logic |
| `workflow_logs` | `log_id` | `wf_id` | `execution_time`, `status`, `error_msg` | Execution history |
| `sync_staging` | `sync_id` | None | `external_ref_id`, `payload`, `sync_timestamp` | Partner API buffer |

### 5.2 Relationships
- **One-to-Many:** `organizations` $\rightarrow$ `subscriptions` (An org may have multiple subscriptions over time).
- **Many-to-Many:** `users` $\leftrightarrow$ `roles` (via `user_roles` join table).
- **One-to-One:** `users` $\rightarrow$ `dashboards` (Each user has one primary dashboard config).
- **One-to-Many:** `workflow_defs` $\rightarrow$ `workflow_logs` (One workflow definition generates many logs).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 On-Premise Constraints
Per company policy, **no cloud providers (AWS, Azure, GCP) are permitted**. All data must reside within the Bellweather Technologies physical data center. This includes all backups and failover sites.

### 6.2 Environment Descriptions

#### 6.2.1 Development (DEV)
- **Purpose:** Active feature development and unit testing.
- **Hardware:** Shared virtualized cluster.
- **Database:** Oracle XE (Express Edition) instance.
- **Deployment:** Triggered on merge to `develop` branch.

#### 6.2.2 Staging (STG)
- **Purpose:** Pre-production validation, UAT, and Security Audit.
- **Hardware:** Mirror of production hardware (1:1 scale).
- **Database:** Oracle 19c (Standard Edition).
- **Deployment:** Triggered on merge to `release` branch.

#### 6.2.3 Production (PROD)
- **Purpose:** Live automotive partner traffic.
- **Hardware:** High-availability rack servers with redundant power and networking.
- **Database:** Oracle 19c (Enterprise Edition) with RAC (Real Application Clusters).
- **Deployment:** Rolling updates via Kubernetes to ensure zero downtime.

### 6.3 CI/CD Pipeline (GitLab CI)
The current pipeline is a primary source of technical debt.
- **Pipeline Stages:** `Build` $\rightarrow$ `Unit Test` $\rightarrow$ `Integration Test` $\rightarrow$ `Security Scan` $\rightarrow$ `Deploy`.
- **Current Bottleneck:** The pipeline takes **45 minutes** due to sequential execution of integration tests and lack of container image caching.
- **Planned Optimization:** Parallelization of the `Integration Test` stage across 4 runners and implementing a local Docker registry cache.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** JUnit 5, Mockito.
- **Requirement:** Minimum 80% line coverage for all service-layer classes.
- **Frequency:** Executed on every commit to `develop`.

### 7.2 Integration Testing
- **Tooling:** Testcontainers (using an Oracle-XE container).
- **Focus:** Testing the interaction between the Spring Boot application and the Oracle DB, specifically focusing on complex SQL queries in the Workflow engine.
- **Frequency:** Executed once per merge request.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Cypress.
- **Focus:** Critical user paths:
    - Login $\rightarrow$ Configure Dashboard $\rightarrow$ Save.
    - Create Workflow $\rightarrow$ Trigger Event $\rightarrow$ Verify Action.
    - Subscription Upgrade $\rightarrow$ Verify Invoice Generation.
- **Frequency:** Executed weekly on the Staging environment.

### 7.4 Security Testing
- **Audit:** Internal security audit conducted by the Bellweather Infosec team.
- **Scope:** Penetration testing of API endpoints and verification of RBAC constraints.
- **Target Date:** 2025-06-15.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor announced EOL (End of Life) for their API product. | High | Critical | Accept the risk; monitor vendor announcements weekly via Felix Oduya. |
| **R-02** | Team has no prior experience with Java/Spring Boot/Oracle stack. | High | Medium | Engage an external consultant for a 4-week independent architecture assessment. |
| **R-03** | Dependency on Team B's deliverable (currently 3 weeks behind). | High | High | Escalate to CTO; identify "mock" interfaces to allow development to continue. |
| **R-04** | CI Pipeline latency (45 mins) slows development velocity. | Certain | Medium | Implement parallel test execution in GitLab CI. |
| **R-05** | On-prem hardware procurement delays. | Medium | High | Pre-order hardware 3 months in advance of Milestone 2. |

### 8.1 Probability/Impact Matrix
- **Critical:** Probability > 70%, Impact = System Failure.
- **High:** Probability 40-70%, Impact = Project Delay.
- **Medium:** Probability 20-40%, Impact = Minor Feature Omission.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Current - June 2025)
- **Focus:** RBAC implementation, Billing module refinement, and Workflow engine review.
- **Dependency:** Team B must deliver the API specification.
- **Key Target:** Milestone 1 (Security Audit) - **2025-06-15**.

### 9.2 Phase 2: Integration & Launch (June 2025 - August 2025)
- **Focus:** Finalizing the Drag-and-Drop Dashboard, integrating external partner API, and UAT.
- **Key Target:** Milestone 2 (Production Launch) - **2025-08-15**.

### 9.3 Phase 3: Stabilization (August 2025 - October 2025)
- **Focus:** Bug fixing, performance tuning of Oracle queries, and monitoring MAU growth.
- **Key Target:** Milestone 3 (Stability Confirmed) - **2025-10-15**.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per the "high-trust, low-ceremony" team dynamic, no formal minutes are kept. The following are synthesized from key Slack threads.*

### Thread 1: Architecture Pivot (Date: 2023-11-12)
- **Felix Oduya:** "I've seen the latest on the external API. We can't go full microservices yet. Let's stick to a modular monolith. Easier to deploy on-prem."
- **Olga Nakamura:** "Agreed. I can set up the Kubernetes pods to handle the monolith, but we need to be careful with the Oracle connection pool."
- **Decision:** Project will proceed as a modular monolith transitioning incrementally to microservices.

### Thread 2: The CI Pipeline Crisis (Date: 2023-12-05)
- **Anouk Liu:** "I'm waiting 45 minutes for the build just to see a CSS change. This is killing my flow."
- **Olga Nakamura:** "The integration tests are running sequentially. I'll look into GitLab parallel runners next week."
- **Felix Oduya:** "Prioritize this. If we can't deploy quickly, we can't iterate."
- **Decision:** CI optimization is now a secondary priority for DevOps.

### Thread 3: Vendor EOL Discussion (Date: 2024-01-20)
- **Devika Oduya:** "The partner just emailed. Their legacy API is EOL by end of next year."
- **Felix Oduya:** "We know. We can't switch partners mid-stream. We accept the risk for now. We'll monitor it weekly and plan a migration in 2026 if needed."
- **Decision:** Risk R-01 is accepted. No immediate architectural change.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the completion of milestones.

| Category | Allocation (USD) | Details |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | 15 distributed engineers (Avg $120k/yr) |
| **Infrastructure** | $450,000 | Physical servers, Oracle Enterprise licenses, Networking gear |
| **Tools/Software** | $120,000 | GitLab Premium, JasperReports, IDE Licenses |
| **External Consultant**| $85,000 | Tech stack assessment (Mitigation for R-02) |
| **Contingency** | $200,000 | 10% buffer for unexpected hardware/license costs |
| **TOTAL** | **$2,655,000** | |

**Tranche Release Schedule:**
- **Tranche 1 (Initial):** $1,000,000 (Project kick-off)
- **Tranche 2 (Post-Milestone 1):** $800,000 (Audit passed)
- **Tranche 3 (Post-Milestone 2):** $600,000 (Production launch)
- **Tranche 4 (Post-Milestone 3):** $255,000 (Stability confirmed)

---

## 12. APPENDICES

### Appendix A: Oracle DB Optimization Guide
To prevent the "slow query" problem common in automotive data sets, the following indexing strategy is mandated for Rampart:
1. **B-Tree Indexes:** All `user_id` and `org_id` columns must be indexed.
2. **Bitmap Indexes:** Use for low-cardinality columns such as `subscription_status` and `country_code`.
3. **Partitioning:** The `workflow_logs` table must be partitioned by month (`LOG_DATE`) to ensure that queries for recent logs do not scan the entire table.

### Appendix B: External API Sync Logic
The sync service implements a "Watermark" system to handle the external company's timeline:
1. The system stores the `last_sync_timestamp` in the `sync_metadata` table.
2. Every 15 minutes, the `ExternalSyncService` requests data where `updated_at > last_sync_timestamp`.
3. If the external API is down, the system implements an exponential backoff (1min, 5min, 15min, 1hr) to avoid overloading the partner's server.
4. All failed sync attempts are logged to the `sync_staging` table with a `STATUS = 'FAILED'` for manual review by Devika Oduya.