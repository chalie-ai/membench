# PROJECT SPECIFICATION: PROJECT INGOT
**Document Version:** 1.0.4  
**Status:** Draft / Under Review  
**Last Updated:** 2025-10-24  
**Classification:** Internal Confidential – Oakmount Group  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Ingot" represents a strategic pivot for Oakmount Group, moving from a generalist agriculture technology service provider to a specialized product-vertical leader. The objective is the development of a high-performance internal enterprise tool designed to manage large-scale agricultural data, resource allocation, and real-time collaborative planning. Unlike previous iterative updates to existing software, Ingot is a ground-up build designed to satisfy the rigorous requirements of a single, high-value enterprise client who has committed to an annual contract value (ACV) of $2,000,000.

### 1.2 Business Justification and ROI Projection
The agricultural sector is currently undergoing a digital transformation where real-time data synchronization is the primary differentiator. Oakmount Group has identified a gap in the market for a "Command Center" style application that allows global agricultural managers to collaborate on land-use data in real-time without the latency inherent in current cloud-based tools. 

The financial justification is grounded in a high-certainty revenue stream. With a committed $2M annual payment from the anchor client, the project achieves a positive ROI within the first 30 months post-launch, despite the initial $5M+ capital expenditure.

**ROI Projections:**
- **Year 1 (Development):** -$5.2M (CAPEX)
- **Year 2 (Launch):** +$2M (Anchor Client) + $500k (Projected early adopters)
- **Year 3 (Scaling):** +$4.5M (Expansion to 5 additional enterprise clients at $800k/ea)
- **Cumulative 3-Year ROI:** Expected 12% growth in net profit margins for the AgTech division.

Beyond the direct revenue, Ingot establishes a proprietary technology stack that Oakmount Group can license to other firms, creating a scalable "Product Vertical" rather than a "Service Engagement." This shift increases the company's valuation by moving from a labor-based revenue model to a recurring software license model.

### 1.3 Strategic Alignment
Ingot is a flagship initiative with board-level reporting. The project is not merely a software delivery task but a proof-of-concept for the organization's ability to execute high-stakes, on-premise enterprise deployments. Success here will dictate the board's appetite for further R&D investments in the AgTech space.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy: Hexagonal Architecture
To ensure the system remains maintainable and testable despite the team's limited experience with the specific stack, Ingot utilizes **Hexagonal Architecture (Ports and Adapters)**. This decouples the core business logic (the "Domain") from the external infrastructure (the "Adapters").

**Key Layers:**
1.  **Domain Layer:** Contains the business entities, value objects, and domain services. It has zero dependencies on external frameworks.
2.  **Application Layer (Ports):** Defines the interfaces (Ports) that the domain requires to interact with the outside world (e.g., `UserRepositoryPort`).
3.  **Infrastructure Layer (Adapters):** Implements the ports. This is where the Oracle DB logic, the Spring Boot REST controllers, and the on-premise networking logic reside.

### 2.2 Technical Stack
- **Language:** Java 21 (LTS)
- **Framework:** Spring Boot 3.2.x
- **Database:** Oracle Database 21c (On-Premise)
- **Deployment:** On-premise data center (Strictly no cloud/AWS/Azure/GCP)
- **Build Tool:** Maven 3.9.x
- **Communication:** REST for APIs, WebSockets for real-time collaboration.

### 2.3 ASCII Architecture Diagram
Below is the conceptual flow of a request through the Ingot system.

```text
[ External Client/UI ]  <---> [ REST Adapter (Spring MVC) ]
                                        |
                                        v
[ Infrastructure ] <--- [ Application Port (Interface) ] ---> [ Domain Core ]
(Oracle DB / File System)              ^                      (Business Logic)
                                       |
[ On-Premise Hardware ] <--- [ Persistence Adapter (JPA/SQL) ]
```

### 2.4 Deployment Strategy
The project follows a **Continuous Deployment (CD)** model. To maintain velocity in a high-trust environment, any Pull Request (PR) that passes the automated test suite and receives a peer sign-off is merged directly into the `main` branch and deployed to the production environment. This "trunk-based" approach reduces integration hell but places a heavy premium on the robustness of the automated testing suite.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
The core of Ingot is the ability for multiple users across different geographies to edit agricultural planning sheets simultaneously. This requires a system that prevents data loss when two users edit the same cell or field at the same time.

**Detailed Requirements:**
- **Operational Transformation (OT):** The system must implement OT or CRDTs (Conflict-free Replicated Data Types) to ensure convergence. Given the Oracle DB backend, the team is leaning toward a centralized OT approach where the server acts as the single source of truth.
- **Concurrency Control:** When a user begins typing in a field, a "lock" signal must be broadcast to all other connected clients via WebSockets to indicate that the field is "busy," although the system must gracefully handle "optimistic" edits if the network lags.
- **Latency Compensation:** The UI must reflect changes locally immediately (optimistic UI updates) and reconcile them once the server acknowledges the operation.
- **Conflict Resolution Logic:** If two edits occur simultaneously, the "Last Write Wins" (LWW) strategy will be applied based on the server-side timestamp, unless the field is marked as "High Precision," in which case the system must prompt the user to manually resolve the conflict.

**Acceptance Criteria:**
- Zero data loss during simultaneous edits by 50 concurrent users on a single document.
- Synchronization latency under 200ms within the internal Oakmount network.

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** Medium | **Status:** In Progress

**Description:**
To allow the enterprise client to integrate Ingot with their own internal ERP systems, a robust, versioned API is required. This API must be stable, documented, and provide a safe environment for testing.

**Detailed Requirements:**
- **Semantic Versioning:** The API must use URI versioning (e.g., `/api/v1/...`). When breaking changes are introduced, a new version (`/v2/`) must be deployed, and the previous version must be supported for 6 months.
- **Sandbox Environment:** A logically separated "Sandbox" instance of the database and application must be available. This allows the client to run integration tests without polluting production data.
- **Rate Limiting:** To protect the on-premise hardware, the API must implement rate limiting (e.g., 1,000 requests per minute per API key) using a bucket-algorithm implemented in the Spring Boot interceptor layer.
- **Authentication:** OAuth2 with JWT (JSON Web Tokens) issued by the Oakmount internal identity provider.

**Acceptance Criteria:**
- Client can successfully authenticate and retrieve data from the `/v1/` endpoint.
- Sandbox environment is fully isolated from the production Oracle DB.

### 3.3 Localization (L10n) and Internationalization (I18n)
**Priority:** Low (Nice to Have) | **Status:** In Review

**Description:**
As the project serves a distributed team across 5 countries and the client's global operations, the UI must support 12 different languages.

**Detailed Requirements:**
- **Resource Bundle Strategy:** All UI text must be externalized into `.properties` files using the `MessageSource` interface in Spring.
- **Language Set:** Support for English, Spanish, French, Portuguese, Mandarin, German, Japanese, Hindi, Arabic, Dutch, Russian, and Vietnamese.
- **Dynamic Switching:** Users must be able to change their language preference in the user profile settings without restarting the application.
- **Locale-Aware Formatting:** Dates, currencies, and numerical separators must automatically adjust based on the user's locale (e.g., `DD/MM/YYYY` for UK vs `MM/DD/YYYY` for US).

**Acceptance Criteria:**
- UI displays correctly in all 12 languages without text clipping or layout breaks.
- Date/Time formats match the selected locale.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** In Review

**Description:**
Users require a personalized "Command Center" where they can arrange widgets (e.g., "Crop Yield Forecast," "Personnel Allocation," "Weather Alerts") based on their specific role.

**Detailed Requirements:**
- **Widget Library:** A set of predefined components (charts, tables, KPIs) that can be instantiated.
- **Persistence:** The layout configuration (X, Y coordinates and dimensions of widgets) must be saved to the Oracle DB under a `user_dashboard_config` table.
- **Drag-and-Drop Interface:** Implementation of a grid-based layout system where widgets snap to a 12-column grid.
- **Custom Queries:** High-level users should be able to create "Custom Widgets" based on saved API queries.

**Acceptance Criteria:**
- User can move a widget from position (0,0) to (2,1) and have that state persist across sessions.
- Dashboard loads in under 2 seconds with 10 active widgets.

### 3.5 A/B Testing Framework for Feature Flags
**Priority:** High | **Status:** In Review

**Description:**
To mitigate the risk of deploying untested features to the entire user base, a feature flag system with built-in A/B testing capabilities is required.

**Detailed Requirements:**
- **Feature Toggles:** Ability to enable/disable features for specific user groups via a management console.
- **A/B Segmentation:** The system must be able to split users into "Control" and "Treatment" groups based on a hash of their User ID.
- **Metric Tracking:** The framework must hook into the logging system to track which group a user belonged to when a specific action was taken.
- **Dynamic Updates:** Feature flags must be updated in real-time without requiring a restart of the Java application (polling or WebSocket update).

**Acceptance Criteria:**
- Ability to roll out a feature to 10% of users and measure the impact on NPS/Usage.
- Zero performance degradation when checking feature flag status in a request loop.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under the base URL: `https://ingot.oakmount.internal/api/v1`

### 4.1 `GET /assets`
- **Description:** Retrieves a list of all agricultural assets.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  [
    { "id": "AST-101", "name": "North Field A", "type": "Land", "status": "Active" },
    { "id": "AST-202", "name": "Tractor-X4", "type": "Equipment", "status": "Maintenance" }
  ]
  ```

### 4.2 `POST /assets`
- **Description:** Creates a new asset.
- **Request Body:**
  ```json
  { "name": "South Field B", "type": "Land", "region": "BR-South" }
  ```
- **Response (201 Created):**
  ```json
  { "id": "AST-103", "status": "Created" }
  ```

### 4.3 `GET /collaboration/session/{sessionId}`
- **Description:** Joins a real-time editing session.
- **Request:** `/collaboration/session/SES-998`
- **Response (200 OK):**
  ```json
  { "sessionId": "SES-998", "activeUsers": 4, "websocketUrl": "wss://ingot.oakmount.internal/ws/SES-998" }
  ```

### 4.4 `PATCH /collaboration/update`
- **Description:** Sends an operational transformation delta.
- **Request Body:**
  ```json
  { "sessionId": "SES-998", "fieldId": "cell-44", "delta": "Change 'Corn' to 'Soy'", "version": 102 }
  ```
- **Response (200 OK):**
  ```json
  { "status": "Accepted", "newVersion": 103 }
  ```

### 4.5 `GET /dashboard/config`
- **Description:** Retrieves the user's customized dashboard layout.
- **Response (200 OK):**
  ```json
  { "userId": "USR-12", "widgets": [ { "id": "W-1", "x": 0, "y": 0, "w": 4, "h": 2 } ] }
  ```

### 4.6 `PUT /dashboard/config`
- **Description:** Updates the user's dashboard layout.
- **Request Body:**
  ```json
  { "widgets": [ { "id": "W-1", "x": 2, "y": 0, "w": 4, "h": 2 } ] }
  ```
- **Response (204 No Content)**

### 4.7 `GET /i18n/messages?lang=fr`
- **Description:** Fetches localization strings for the frontend.
- **Response (200 OK):**
  ```json
  { "welcome_msg": "Bienvenue dans Ingot", "save_btn": "Enregistrer" }
  ```

### 4.8 `POST /flags/toggle`
- **Description:** Admin endpoint to toggle feature flags.
- **Request Body:**
  ```json
  { "flagName": "NEW_DASHBOARD_V2", "enabled": true, "percentage": 20 }
  ```
- **Response (200 OK):**
  ```json
  { "status": "Updated" }
  ```

---

## 5. DATABASE SCHEMA

The system utilizes an Oracle 21c database. Due to performance constraints, 30% of the queries bypass the JPA ORM and use native SQL.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email`, `role_id`, `locale` | Core user accounts |
| `roles` | `role_id` | - | `role_name`, `permissions` | RBAC roles |
| `assets` | `asset_id` | - | `name`, `type`, `region_id` | Ag-assets (Land, Eq) |
| `regions` | `region_id` | - | `region_name`, `country_code` | Geographic regions |
| `collab_sessions` | `session_id` | - | `start_time`, `doc_id` | Active editing sessions |
| `doc_versions` | `version_id` | `session_id` | `delta_json`, `timestamp` | OT History |
| `user_configs` | `config_id` | `user_id` | `pref_json`, `theme` | UI preferences |
| `dashboard_widgets`| `widget_id` | `config_id` | `widget_type`, `pos_x`, `pos_y`| Saved dashboard layout |
| `feature_flags` | `flag_id` | - | `flag_key`, `is_enabled`, `rollout_%`| A/B test toggles |
| `audit_logs` | `log_id` | `user_id` | `action`, `timestamp`, `ip_address`| SOC 2 Compliance logs |

### 5.2 Relationships
- **Users $\rightarrow$ Roles:** Many-to-One (Each user has one primary role).
- **Users $\rightarrow$ User\_Configs:** One-to-One.
- **User\_Configs $\rightarrow$ Dashboard\_Widgets:** One-to-Many (One config contains many widgets).
- **Collab\_Sessions $\rightarrow$ Doc\_Versions:** One-to-Many (One session generates many version increments).
- **Assets $\rightarrow$ Regions:** Many-to-One.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 On-Premise Environment
Due to strict security requirements, no cloud providers are utilized. The application is hosted in Oakmount Group's internal data center in the US-East facility.

### 6.2 Environment Tiers

#### 6.2.1 Development (Dev)
- **Purpose:** Individual feature development and unit testing.
- **Infrastructure:** 3 virtual machines (VMs) running Ubuntu 22.04.
- **Database:** H2 In-memory database for local dev, shared Oracle Dev instance for integration.
- **Deployment:** Manual trigger via Jenkins.

#### 6.2.2 Staging (Staging)
- **Purpose:** Pre-production validation and SOC 2 compliance auditing.
- **Infrastructure:** Mirror of production (2 VMs, Load Balancer).
- **Database:** Oracle DB (Staging Instance) with sanitized production data.
- **Deployment:** Automatic deploy upon merge to `develop` branch.

#### 6.2.3 Production (Prod)
- **Purpose:** Live client environment.
- **Infrastructure:** 4 high-compute VMs in a clustered configuration.
- **Database:** Oracle 21c RAC (Real Application Clusters) for high availability.
- **Deployment:** Continuous Deployment (CD). Every merged PR to `main` is deployed.

### 6.3 SOC 2 Type II Compliance
To achieve compliance before launch, the following must be implemented:
- **Encryption:** AES-256 for data at rest in Oracle DB.
- **Transport:** TLS 1.3 for all internal and external communications.
- **Access:** Multi-factor authentication (MFA) for all developers accessing the on-premise servers.
- **Logging:** Immutable audit logs stored in the `audit_logs` table, mirrored to a read-only syslog server.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Coverage Goal:** 80% minimum coverage for Domain layer.
- **Frequency:** Run on every commit via pre-commit hooks.
- **Focus:** Business logic, OT conflict resolution algorithms, and validation logic.

### 7.2 Integration Testing
- **Framework:** SpringBootTest with Testcontainers (for Oracle DB).
- **Scope:** Testing the "Adapters"—ensuring the Java code correctly communicates with the Oracle DB and that the REST endpoints return expected JSON structures.
- **Critical Path:** Validation of the raw SQL queries that bypass the ORM to ensure they don't break during schema migrations.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright / Selenium.
- **Scope:** User journeys (e.g., "User logs in $\rightarrow$ opens dashboard $\rightarrow$ edits asset $\rightarrow$ sees one other user edit the same asset").
- **Frequency:** Run on the Staging environment before any PR is merged to `main`.

### 7.4 Performance Testing
- **Tool:** JMeter.
- **Goal:** Ensure the system handles 10,000 monthly active users (MAU) with a peak concurrency of 500 users during the morning "sync" window.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Plan |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | High | Establish a "Steering Committee" instead of a single sponsor. Create a fallback architecture document that doesn't rely on the sponsor's specific vision. |
| R-02 | Team lacks experience with Java/Oracle/Spring | High | Medium | Engage external consultant (Expert-level) for monthly architectural reviews and a one-time independent assessment of the codebase. |
| R-03 | Dependency on external team (3 weeks behind) | Medium | High | Pivot development to features that don't rely on the external deliverable. Use "mock" interfaces to simulate the missing dependency. |
| R-04 | Raw SQL technical debt causing migration failure | Medium | High | Create a strict "SQL Registry" where all raw queries are documented. Implement a database migration tool (Flyway) with a mandatory staging-test phase. |
| R-05 | SOC 2 Compliance failure | Low | Critical | Bi-weekly audits with the internal compliance officer. Automated security scanning in the CI/CD pipeline. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundation (Current - 2026-07-14)
- **Focus:** Core Domain model, Oracle DB setup, and Basic API.
- **Dependencies:** External team delivery (Currently blocked).
- **Key Deliverable:** Working prototype of the collaborative editor.

### 9.2 Milestone 1: Stakeholder Demo and Sign-off
- **Target Date:** 2026-07-15
- **Goal:** Demonstrate the real-time editing and basic dashboard to the board and the anchor client.
- **Requirement:** All "Critical" priority features must be in a "Review" state.

### 9.3 Phase 2: Hardening (2026-07-16 - 2026-09-14)
- **Focus:** SOC 2 compliance, API Versioning, Sandbox environment.
- **Dependencies:** Completion of the external team's deliverable.

### 9.4 Milestone 2: Internal Alpha Release
- **Target Date:** 2026-09-15
- **Goal:** Deployment to a limited internal user group (20 users) for stress testing.
- **Requirement:** Bug-free "Happy Path" for all high and medium priority features.

### 9.5 Phase 3: Client Onboarding (2026-09-16 - 2026-11-14)
- **Focus:** Localization (12 languages), Dashboard polish, Client API integration.
- **Dependencies:** Successful alpha results.

### 9.6 Milestone 3: First Paying Customer Onboarded
- **Target Date:** 2026-11-15
- **Goal:** Full production deployment for the anchor client.
- **Requirement:** SOC 2 Type II certification completed.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per the "low-ceremony" team dynamic, formal meeting minutes are not kept. Decisions are documented in Slack threads.

### Thread 1: #ingot-dev-channel (2025-11-12)
**Topic: The ORM Performance Issue**
- **Ingrid:** "The JPA overhead on the asset-query is killing us. We're seeing 2s latency on the main list."
- **Noor:** "I've tried indexing the region_id, but the join is still slow."
- **Thiago:** "Can we just write a raw SQL query for this one? It's just a read."
- **Ingrid:** "Agreed. Let's bypass the ORM for the `GET /assets` endpoint. But we must document the raw SQL in the registry so we don't break it during the next migration."
- **Decision:** Use raw SQL for high-latency read queries; document in `sql-registry.md`.

### Thread 2: #ingot-product (2025-12-05)
**Topic: Collaborative Editing Conflict Resolution**
- **Udo:** "If two users edit the same cell, the UI is flickering between values. We need a better resolution."
- **Ingrid:** "LWW (Last Write Wins) is the easiest, but the client wants precision. Let's implement a version-check. If the version sent by the client is behind the server version, reject the update and trigger a 'Conflict' modal."
- **Udo:** "Will that be too disruptive for the user?"
- **Ingrid:** "For 90% of fields, yes. Let's do LWW for 'Notes' and Version-Check for 'Financials'."
- **Decision:** Hybrid conflict resolution (LWW for notes, Version-Check for high-precision data).

### Thread 3: #ingot-ops (2026-01-20)
**Topic: Deployment Frequency**
- **Noor:** "We're merging 5-10 PRs a day. I'm worried about the production stability with the current CD pipeline."
- **Thiago:** "The tests are passing, but we had one outage yesterday because of a DB lock."
- **Ingrid:** "We trust the team. Let's keep CD, but add a 'Canary' stage where the PR goes to one VM first for 10 minutes before hitting the whole cluster."
- **Noor:** "I can set that up in Jenkins."
- **Decision:** Implement Canary deployments to mitigate CD risks.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,250,000 (Approved by Board)

### 11.1 Personnel (Total: $3,800,000)
- **Internal Team (15 members):** $3,200,000 (Covers salaries, benefits, and overhead for the duration of the project).
- **External Consultant (Architecture Review):** $400,000 (Fixed-fee engagement for the duration of the project).
- **Specialized SOC 2 Auditors:** $200,000 (Certification and audit fees).

### 11.2 Infrastructure (Total: $850,000)
- **Hardware Procurement:** $500,000 (High-spec on-premise servers, storage arrays, and networking gear).
- **Oracle Licenses:** $300,000 (Enterprise licenses for 21c RAC).
- **Backup/DR Systems:** $50,000 (Off-site tape backups and redundant power).

### 11.3 Tools & Software (Total: $200,000)
- **IDE & Dev Tooling:** $50,000 (JetBrains licenses, Maven plugins).
- **Monitoring & Logging:** $100,000 (On-premise ELK stack and Prometheus/Grafana).
- **Testing Suite Licenses:** $50,000 (Playwright/Enterprise testing tools).

### 11.4 Contingency Fund (Total: $400,000)
- **Risk Mitigation:** $400,000 (Reserved for unexpected hardware failures, emergency staffing, or scope creep requested by the anchor client).

---

## 12. APPENDICES

### Appendix A: Raw SQL Registry (Sample)
To manage the technical debt associated with bypassing the ORM, all raw queries must be registered here.

| Query ID | Endpoint | Table | Purpose | Risk Level |
| :--- | :--- | :--- | :--- | :--- |
| `SQL-001` | `GET /assets` | `assets`, `regions` | Complex join for region-based filtering | High |
| `SQL-002` | `GET /collab/history` | `doc_versions` | High-speed retrieval of version history | Medium |

### Appendix B: SOC 2 Compliance Checklist
The following items must be verified by Noor Liu and the external auditor prior to the November 15th launch.

1. [ ] **Encryption at Rest:** Verified for `users` and `audit_logs` tables.
2. [ ] **Encryption in Transit:** TLS 1.3 enforced on all ports.
3. [ ] **Access Control:** All `root` access to production VMs requires a ticket ID and manager approval.
4. [ ] **Backup Validation:** Monthly restoration tests performed and logged.
5. [ ] **Dependency Scanning:** OWASP Dependency-Check integrated into the Jenkins pipeline.
6. [ ] **Audit Trail:** Every `DELETE` or `UPDATE` operation in the `assets` table generates a record in `audit_logs`.