# PROJECT SPECIFICATION DOCUMENT: PROJECT LODESTAR
**Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Active / Baseline  
**Classification:** Confidential - Hearthstone Software Internal  
**Project Lead:** Wes Kim (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Lodestar is a comprehensive, ground-up rebuild of the Hearthstone Software e-commerce marketplace, specifically tailored for the cybersecurity industry. The current version of the platform has suffered from catastrophic user feedback, characterized by extreme friction in the procurement process, an unintuitive interface, and a failure to meet the high-security expectations of cybersecurity professionals. Lodestar is not merely an update; it is a strategic pivot to regain market share and restore brand trust.

The objective is to transform the marketplace from a static storefront into a dynamic, collaborative security asset hub. The project focuses on high-value features such as real-time collaboration and customizable dashboards, ensuring that CISO-level users can manage their security spend and toolsets with surgical precision.

### 1.2 Business Justification
The cybersecurity market demands a level of trust and reliability that the current legacy system cannot provide. User feedback indicates that the current "clunky" interface is viewed as a proxy for the quality of the security tools being sold. By implementing a modern, responsive, and highly performant architecture (Ruby on Rails monolith with Hexagonal patterns), Hearthstone Software will reduce customer churn, which has increased by 22% over the last three quarters.

The "Lodestar" rebuild addresses the critical gap between complex cybersecurity procurement needs and the current simplified, yet broken, e-commerce flow. By providing a collaborative environment where security teams can vet products before purchase, we move from a transactional model to a partner-centric model.

### 1.3 ROI Projection
The total budget for Lodestar is $800,000. The projected Return on Investment (ROI) is calculated based on three primary levers:
1. **Churn Reduction:** An expected 15% decrease in churn, representing an estimated $1.2M in retained annual recurring revenue (ARR).
2. **Conversion Rate Optimization:** A projected 10% increase in checkout completion rates due to the removal of current UX bottlenecks.
3. **Operational Efficiency:** Reduction in support tickets related to "UI confusion" by an estimated 40%, saving approximately $50k/year in support overhead.

The break-even point is projected for Month 14 post-launch, with a projected 3-year Net Present Value (NPV) of $2.4M.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Strategy
Lodestar utilizes a **Ruby on Rails (v7.1)** monolith. The decision to use a monolith is deliberate; given the small 2-person core team (Chioma and Ilya), the overhead of microservices would either jeopardize the 6-month timeline or introduce unnecessary deployment complexity. To prevent the "big ball of mud" common in monoliths, we are implementing **Hexagonal Architecture (Ports and Adapters)**.

In this pattern, the core business logic (Entities and Use Cases) is isolated from external concerns (Database, API, UI). 
- **The Core:** Contains the business rules for the cybersecurity marketplace.
- **Ports:** Interfaces that define how the core interacts with the outside world.
- **Adapters:** Concrete implementations (e.g., a MySQL adapter for persistence, a Heroku adapter for deployment, or a SAML adapter for authentication).

### 2.2 Infrastructure Stack
- **Language:** Ruby 3.3.0
- **Framework:** Rails 7.1 (API + Hotwire/Turbo for frontend interactivity)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres is avoided to maintain strict MySQL requirements)
- **Hosting:** Heroku (Private Spaces for SOC 2 compliance)
- **Caching:** Redis 7.0
- **Worker Queue:** Sidekiq Enterprise

### 2.3 Architecture Diagram (ASCII)
```text
[ CLIENT LAYER ] 
       |
       v
[ ADAPTERS (Inbound) ] <--- (Controllers, API Endpoints, Webhooks)
       |
       v
[ PORTS (Interfaces) ] <--- (Service Layer Definitions)
       |
       v
[ CORE DOMAIN ] <---------- (Business Logic, Entities, Validation)
       |
       v
[ PORTS (Interfaces) ] <--- (Repository Interfaces, Mailer Interfaces)
       |
       v
[ ADAPTERS (Outbound) ] <--- (MySQL DB, SendGrid, SAML Providers, CSV Generator)
       |
       v
[ EXTERNAL SYSTEMS ] <--- (MySQL Database, Identity Providers, Third Party APIs)
```

### 2.4 Security and Compliance
As a cybersecurity product, **SOC 2 Type II compliance** is a hard requirement before the production launch. This necessitates:
- Encryption of all data at rest (AES-256).
- TLS 1.3 for all data in transit.
- Strict IAM roles within Heroku.
- Audit logs for every administrative action (implemented via a dedicated `AuditLog` table).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical | **Status:** Not Started | **Launch Blocker:** Yes

**Functional Description:**
The dashboard serves as the primary landing page for the user. Unlike the legacy system’s static page, Lodestar will provide a "Grid System" where users can add, remove, and reposition widgets. Widgets include "Current Subscriptions," "Security Spend Trends," "Pending Approvals," and "Threat Intelligence Feeds."

**Detailed Requirements:**
- **Widget Library:** A set of pre-defined components that users can pull from a side-drawer.
- **Persistence:** The layout (X, Y coordinates and dimensions) must be saved to the `user_dashboard_configs` table so the layout persists across sessions.
- **Drag-and-Drop Logic:** Implementation using `SortableJS` or `React-Grid-Layout` integrated via Hotwire.
- **Customization:** Users must be able to rename widgets and set refresh intervals (e.g., "Refresh every 5 minutes").

**Technical Constraints:**
- The dashboard must load in under 1.2 seconds.
- State must be synchronized via JSON blobs in MySQL to allow for flexible widget configurations.

---

### 3.2 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** Critical | **Status:** In Design | **Launch Blocker:** Yes

**Functional Description:**
Cybersecurity procurement often requires a team effort. This feature allows multiple users (e.g., a Security Architect and a Procurement Officer) to edit a "Procurement Request" or "Security Configuration" document simultaneously.

**Detailed Requirements:**
- **Presence Indicators:** Show who is currently viewing the document (avatars in the top right).
- **Real-Time Sync:** Changes must be reflected across all clients in < 100ms.
- **Conflict Resolution:** Use an **Operational Transformation (OT)** or **CRDT (Conflict-free Replicated Data Type)** approach. If two users edit the same field, the system must merge changes based on timestamp and user priority.
- **Locking Mechanism:** For critical fields (like "Budget Limit"), a pessimistic lock should be applied when one user begins editing to prevent race conditions.

**Technical Constraints:**
- Implementation via ActionCable (WebSockets) for the transport layer.
- Redis will be used to track the ephemeral state of active collaborators.

---

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Blocked | **Dependency:** Data Warehouse Migration

**Functional Description:**
Users need to export their spending and security audit logs for regulatory compliance. This system must generate high-fidelity PDFs and raw CSVs and deliver them via email or an in-app notification.

**Detailed Requirements:**
- **Scheduled Delivery:** A cron-like interface where users can set "Monthly," "Weekly," or "Custom" delivery dates.
- **Custom Templates:** Ability to choose between "Executive Summary" (PDF) and "Detailed Audit" (CSV).
- **Async Processing:** Reports must be generated in the background via Sidekiq to prevent blocking the web thread.
- **Storage:** Generated files must be stored in an encrypted S3 bucket with a 30-day expiration TTL.

**Technical Constraints:**
- Use `WickedPDF` or `Grover` (Puppeteer-based) for PDF generation to ensure CSS fidelity.
- CSV generation must utilize stream-processing for datasets exceeding 10,000 rows to avoid memory overflow.

---

### 3.4 SSO Integration (SAML and OIDC)
**Priority:** Low | **Status:** Complete

**Functional Description:**
Enterprise customers require Single Sign-On (SSO) to manage user access through their own identity providers (IdPs) such as Okta, Azure AD, or Ping Identity.

**Detailed Requirements:**
- **SAML 2.0 Support:** Ability to upload metadata XML files from the IdP.
- **OIDC Flow:** Standard OAuth2.0 flow for modern identity providers.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user account in the Lodestar database upon successful first-time SSO login.
- **Attribute Mapping:** Ability to map SAML attributes (e.g., `memberOf`) to internal Lodestar roles (`Admin`, `Viewer`, `Buyer`).

**Technical Constraints:**
- Implementation via the `devise` and `omniauth` gems.
- Encryption of IdP certificates within the database using `lockbox`.

---

### 3.5 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Blocked | **Dependency:** Finance API Approval

**Functional Description:**
A self-service portal for managing subscriptions, updating credit cards, and viewing historical invoices.

**Detailed Requirements:**
- **Tiered Pricing:** Support for "Professional," "Enterprise," and "Government" tiers.
- **Proration:** Automatic calculation of costs when upgrading/downgrading mid-cycle.
- **Dunning Management:** Automated emails for failed credit card payments with a 3-day grace period.
- **Invoice Generation:** Automated PDF invoicing sent via email upon successful payment.

**Technical Constraints:**
- Integration with Stripe Billing or Chargebee.
- Webhook listeners to update `subscription_status` in the MySQL database.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and return JSON. Base URL: `https://api.lodestar.hearthstone.com/v1`

### 4.1 Authentication
`POST /auth/login`
- **Request:** `{ "email": "user@company.com", "password": "..." }`
- **Response:** `200 OK { "token": "jwt_token_here", "user_id": 123 }`

### 4.2 Dashboard Config
`GET /dashboard/config`
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "layout": [{ "widget": "spend_chart", "x": 0, "y": 0, "w": 6, "h": 4 }] }`

`PUT /dashboard/config`
- **Request:** `{ "layout": [...] }`
- **Response:** `200 OK { "status": "updated" }`

### 4.3 Collaborative Documents
`GET /docs/{doc_id}`
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "id": "doc_1", "content": "...", "version": 45 }`

`POST /docs/{doc_id}/patch`
- **Request:** `{ "operation": "insert", "position": 12, "value": "security", "version": 45 }`
- **Response:** `200 OK { "new_version": 46, "merged_content": "..." }`

### 4.4 Reporting
`POST /reports/schedule`
- **Request:** `{ "report_type": "csv", "frequency": "monthly", "email": "ciso@company.com" }`
- **Response:** `201 Created { "schedule_id": "sch_99" }`

`GET /reports/download/{report_id}`
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `302 Redirect (to S3 Signed URL)`

### 4.5 Subscription
`GET /billing/subscription`
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "plan": "Enterprise", "renews_at": "2026-01-01" }`

`PATCH /billing/subscription`
- **Request:** `{ "plan_id": "plan_premium_01" }`
- **Response:** `200 OK { "status": "pending_payment" }`

---

## 5. DATABASE SCHEMA

The database uses MySQL 8.0. All tables use `bigint` for primary keys and `datetime(6)` for timestamps.

### 5.1 Table Definitions

1. **`users`**
   - `id` (PK), `email` (unique), `password_digest`, `full_name`, `role_id` (FK), `created_at`, `updated_at`.
2. **`roles`**
   - `id` (PK), `role_name` (e.g., "Admin", "Buyer"), `permissions_bitmask`.
3. **`organizations`**
   - `id` (PK), `company_name`, `tax_id`, `billing_address`, `sso_enabled` (boolean).
4. **`organization_users`**
   - `id` (PK), `organization_id` (FK), `user_id` (FK), `joined_at`.
5. **`products`**
   - `id` (PK), `sku` (unique), `name`, `description`, `price_cents`, `category`.
6. **`subscriptions`**
   - `id` (PK), `organization_id` (FK), `plan_id`, `status` (active/past_due/canceled), `current_period_end`.
7. **`dashboard_configs`**
   - `id` (PK), `user_id` (FK), `layout_json` (JSON type), `updated_at`.
8. **`collaboration_docs`**
   - `id` (PK), `title`, `content` (longtext), `version_number` (int), `last_modified_by` (FK).
9. **`report_schedules`**
   - `id` (PK), `user_id` (FK), `report_type`, `frequency`, `delivery_email`, `next_run_at`.
10. **`audit_logs`**
    - `id` (PK), `user_id` (FK), `action` (string), `ip_address`, `timestamp`, `payload_before`, `payload_after`.

### 5.2 Relationships
- **User $\to$ Organization:** Many-to-Many via `organization_users`.
- **Organization $\to$ Subscription:** One-to-One.
- **User $\to$ DashboardConfig:** One-to-One.
- **User $\to$ AuditLog:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We utilize three distinct environments to ensure stability and compliance.

#### Development (`dev`)
- **Purpose:** Feature development and local testing.
- **Access:** All developers.
- **Deployment:** Automatic on push to `develop` branch.
- **Database:** Shared MySQL instance with anonymized data.

#### Staging (`staging`)
- **Purpose:** Pre-production QA and User Acceptance Testing (UAT).
- **Access:** Dev team and select stakeholders (Ilya Kim, Wes Kim).
- **Deployment:** Triggered by merge requests to the `release` branch.
- **Configuration:** Mirror of Production (identical instance sizes and DB versions).

#### Production (`prod`)
- **Purpose:** Customer-facing environment.
- **Access:** Restricted to Engineering Manager (Wes Kim).
- **Deployment:** Quarterly releases. This slow cadence is mandated by the regulatory review cycle (SOC 2 audit checkpoints).
- **Infrastructure:** Heroku Private Spaces with dedicated dynos.

### 6.2 Deployment Pipeline
1. **CI:** GitHub Actions runs RSpec and Rubocop.
2. **Artifact:** Docker image built and pushed to Heroku Registry.
3. **Staging Deploy:** Manual trigger $\to$ QA Sign-off $\to$ Security Scan.
4. **Prod Deploy:** Quarterly window $\to$ Blue/Green deployment to prevent downtime.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** RSpec.
- **Coverage Goal:** 90% for the "Core Domain" (Use Cases/Entities).
- **Approach:** Mocking all adapters (MySQL, Heroku API) to ensure business logic is tested in isolation.

### 7.2 Integration Testing
- **Tool:** RSpec / FactoryBot.
- **Focus:** Testing the interaction between the Core and the Adapters.
- **Scenario:** Ensuring that a "Create Subscription" request correctly updates the MySQL database and triggers a Sidekiq job.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Critical user journeys.
- **Key Paths:** 
    - User logs in via SSO $\to$ Navigates to Dashboard $\to$ Drags a widget $\to$ Saves.
    - User opens Collaborative Doc $\to$ Edits field $\to$ Verifies change on second browser instance.

### 7.4 Performance Testing
- **Tool:** JMeter.
- **Target:** API p95 response time < 200ms at 500 concurrent requests/sec.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% next fiscal quarter | Medium | High | Negotiate timeline extension with stakeholders; identify "non-essential" features for descoping. |
| R-02 | Competitor is 2 months ahead in market | High | Critical | Raise as a primary blocker in the next board meeting; prioritize "Critical" features over "Low" ones. |
| R-03 | Key team member on medical leave (6 weeks) | Actual | High | Redistribution of tasks to contractor (Hana Costa); extend Milestone 1 target if necessary. |
| R-04 | SOC 2 audit failure before launch | Low | Critical | Bi-weekly internal audits and use of compliance software (Vanta/Drata). |
| R-05 | Technical debt: Lack of structured logging | High | Medium | Implement `Lograge` and `ELK Stack` in Q1 to replace stdout reading. |

**Impact Matrix:**
- **Critical:** Project failure or launch delay > 1 month.
- **High:** Feature removal or launch delay 2-4 weeks.
- **Medium:** Minor feature degradation.
- **Low:** Negligible impact on timeline.

---

## 9. TIMELINE

The project follows a linear progression with strict gates.

### Phase 1: Core Foundation (Oct 2025 - Jan 2026)
- **Focus:** Hexagonal architecture setup, MySQL schema migration, SSO implementation.
- **Dependency:** Finalization of security requirements.
- **Milestone:** Infrastructure Baseline.

### Phase 2: Critical Feature Build (Jan 2026 - June 2026)
- **Focus:** Collaborative Editing (CRDT) and Customizable Dashboard.
- **Dependency:** Frontend Lead (Chioma) and UX Researcher (Ilya) alignment on widget specs.
- **Milestone 1: MVP Feature-Complete (Target: 2026-06-15)**.

### Phase 3: Alpha & Stabilization (June 2026 - Aug 2026)
- **Focus:** Internal testing, bug fixing, and report generation implementation.
- **Dependency:** Data Warehouse migration completion.
- **Milestone 2: Internal Alpha Release (Target: 2026-08-15)**.

### Phase 4: Compliance & Benchmarking (Aug 2026 - Oct 2026)
- **Focus:** SOC 2 Type II audit, p95 latency tuning, final UAT.
- **Dependency:** Third-party auditor availability.
- **Milestone 3: Performance Benchmarks Met (Target: 2026-10-15)**.

---

## 10. MEETING NOTES

*Note: The following are excerpts from the master meeting document (currently 200 pages, unsearchable).*

### Meeting 1: Project Kickoff (October 27, 2025)
**Attendees:** Wes Kim, Chioma Gupta, Ilya Kim, Hana Costa.
- **Wes:** "The current product is a disaster. Feedback is catastrophic. We are rebuilding from the ground up. No legacy code is to be ported unless it's a data migration."
- **Chioma:** "I'm concerned about the 6-month window for the dashboard. Drag-and-drop is tricky with Rails' standard views. I suggest using Hotwire with a JS library."
- **Ilya:** "The users hate the current flow because it's linear. They want a workspace, not a store. I will provide the wireframes for the widgets by November 15."
- **Decision:** Agreed on Hexagonal Architecture to ensure we can swap adapters if we move off Heroku.

### Meeting 2: Technical Review - Collaborative Editing (November 20, 2025)
**Attendees:** Wes Kim, Chioma Gupta, Hana Costa.
- **Hana:** "If we use standard Rails controllers, the latency will be too high for real-time editing. We need ActionCable."
- **Wes:** "What about conflict resolution? If two users hit 'Save' at the same time, we lose data."
- **Chioma:** "I've been researching CRDTs (Conflict-free Replicated Data Types). It's a bit complex for a 2-person core team, but it's the only way to avoid the 'lost update' problem."
- **Decision:** Proceed with a simplified OT (Operational Transformation) approach for now; shift to CRDT if alpha testing shows too many conflicts.

### Meeting 3: Budget and Risk Sync (December 12, 2025)
**Attendees:** Wes Kim, Chioma Gupta.
- **Wes:** "Heads up: There is a rumor that the board might cut the budget by 30% in the next quarter. We need to be lean."
- **Chioma:** "If the budget drops, we can't afford the Enterprise Sidekiq license. We'll have to move to the open-source version, which means slower background processing for reports."
- **Wes:** "Agreed. Let's prioritize the 'Critical' features. If the cut happens, the 'Nice to Have' features (Billing and SSO refinements) are the first to go."
- **Decision:** Document the 'descoping' path in the risk register.

---

## 11. BUDGET BREAKDOWN

The total budget is **$800,000**, allocated for a 6-month development cycle plus stabilization.

### 11.1 Personnel ($620,000)
- **Wes Kim (EM/Lead):** $160,000 (Management and Architecture oversight)
- **Chioma Gupta (Frontend Lead):** $140,000 (Frontend development and UI implementation)
- **Ilya Kim (UX Researcher):** $120,000 (User research, wireframing, and usability testing)
- **Hana Costa (Contractor):** $200,000 (Full-stack development and API implementation)

### 11.2 Infrastructure ($70,000)
- **Heroku Private Space:** $30,000 (Includes dedicated dynos and network isolation)
- **MySQL (Managed):** $15,000 (High-availability cluster)
- **Redis Enterprise:** $10,000 (State management for collaborative editing)
- **S3 Storage & CDN:** $15,000 (Report storage and asset delivery)

### 11.3 Tools & Compliance ($60,000)
- **SOC 2 Audit Fees:** $35,000 (External auditor and certification)
- **Compliance Software (Vanta):** $10,000
- **JIRA/Confluence/GitHub Licenses:** $15,000

### 11.4 Contingency Fund ($50,000)
- Reserved for emergency hardware, unexpected licensing costs, or short-term contractor extension if the medical leave extends beyond 6 weeks.

---

## 12. APPENDICES

### Appendix A: Data Migration Strategy
Because Lodestar is a rebuild, we must migrate users from the legacy MySQL database.
1. **Extraction:** ETL process using a custom Ruby script to extract `user_emails` and `hashed_passwords`.
2. **Transformation:** Mapping legacy `user_role` strings to the new `permissions_bitmask` in the `roles` table.
3. **Loading:** Batch insertion into the Lodestar `users` and `organizations` tables.
4. **Verification:** A checksum script will compare the total record count and email uniqueness between the old and new systems.

### Appendix B: Collaborative Editing State Machine
The "Collaborative Editing" feature follows this state transition:
- `Idle` $\to$ `Connecting` (User opens document).
- `Connecting` $\to$ `Synced` (ActionCable subscription established, version $N$ received).
- `Synced` $\to$ `Editing` (User keystroke triggers `patch` request).
- `Editing` $\to$ `Conflict` (Incoming version $N+1$ contradicts local change).
- `Conflict` $\to$ `Resolved` (CRDT logic merges change, state returns to `Synced`).
- `Synced` $\to$ `Disconnected` (Heartbeat failure $\to$ Local read-only mode).