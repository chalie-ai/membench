Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. To maintain the highest level of professional rigor, it is structured as a living technical manual for the development team at Ridgeline Platforms.

***

# PROJECT SPECIFICATION: NEXUS
**Project Code:** RP-NEXUS-2026  
**Version:** 1.0.4-beta  
**Classification:** Confidential / ISO 27001 Restricted  
**Last Updated:** 2024-05-22  
**Owner:** Arun Oduya (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Nexus represents a strategic pivot for Ridgeline Platforms. While the company has historically excelled in standalone legal service tooling, the current market shift toward integrated ecosystem legal services necessitates a robust Supply Chain Management (SCM) system specifically tailored for legal procurement, vendor management, and external counsel coordination. 

The primary driver for Nexus is a strategic partnership integration. Ridgeline Platforms is integrating with a critical external entity whose API governs a significant portion of the legal supply chain. Because the synchronization depends on the partner’s timeline, Nexus is designed not just as a tool, but as a flexible middleware layer that can adapt to external API fluctuations while providing a high-performance interface for internal stakeholders.

In the legal industry, "supply chain" refers to the procurement of expert witnesses, outsourced discovery services, court reporting, and specialized legal research. The inefficiency in managing these vendors currently costs the firm approximately $1.2M annually in leaked billable hours and redundant administrative overhead. Nexus will centralize these operations, automate the procurement workflow, and ensure compliance with strict regulatory mandates.

### 1.2 ROI Projection and Success Metrics
With a total investment of $3,000,000, the project is under high executive visibility. The ROI is calculated based on two primary levers: revenue generation through new service offerings and operational cost reduction.

**Metric 1: Revenue Generation**
The target is **$500,000 in new revenue** attributed directly to Nexus within 12 months of launch. This will be achieved by offering "Integrated Legal Procurement" as a premium tier to existing clients, allowing them to manage their own external vendor networks through our platform.

**Metric 2: Customer Satisfaction**
A target **Net Promoter Score (NPS) of >40** within the first quarter post-launch. Given the friction associated with legal procurement, a high NPS will validate the effectiveness of the "drag-and-drop" dashboard and the automation engine.

**Financial Breakdown of Value:**
- Estimated Operational Savings: $400,000/year (Reduced manual entry).
- Projected Upsell Revenue: $500,000/year.
- Total Year 1 Value: $900,000.
- Break-even point: Approximately 3.3 years, excluding the strategic value of the partnership integration.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Nexus is built on a modern, high-concurrency stack designed for real-time updates and extreme reliability.

- **Language/Framework:** Elixir/Phoenix (v1.7+). Chosen for its fault tolerance (OTP) and ability to handle thousands of simultaneous connections via the BEAM VM.
- **Frontend:** Phoenix LiveView. This enables real-time updates for the dashboard and rule-builder without the overhead of a heavy SPA framework like React, reducing the state-synchronization complexity.
- **Database:** PostgreSQL 15. Used for relational data integrity and complex querying.
- **Infrastructure:** Fly.io. Utilized for global distribution and seamless scaling of Elixir nodes.
- **Compliance:** The environment is strictly ISO 27001 certified, requiring encrypted volumes at rest, TLS 1.3 for all transit, and rigorous audit logging for every administrative action.

### 2.2 Architecture Logic (Three-Tier Model)
Nexus follows a traditional three-tier architecture to ensure a clean separation of concerns, which is critical given the risk of the key architect departing.

1.  **Presentation Layer:** Phoenix LiveView and HTML/CSS. Handles the drag-and-drop interface and real-time state updates.
2.  **Business Logic Layer (Contexts):** Elixir modules that encapsulate business rules. This layer manages the transformation of external API data into internal legal procurement entities.
3.  **Data Layer:** PostgreSQL. All data persistence is handled here. Note: Due to performance constraints on large legal datasets, 30% of queries currently bypass the Ecto ORM in favor of Raw SQL (see Technical Debt section).

### 2.3 ASCII Architecture Diagram
```text
[ EXTERNAL API ] <--- HTTPS/TLS 1.3 ---> [ NEXUS SYSTEM ]
                                               |
                                               v
                                     +---------------------+
                                     |    FLY.IO CLUSTER    |
                                     | (Elixir/Phoenix App) |
                                     +----------+----------+
                                                |
          +-------------------------------------+-------------------------------------+
          |                                     |                                     |
 [ PRESENTATION LAYER ]               [ BUSINESS LOGIC ]                    [ DATA LAYER ]
 | - LiveView Dashboards | <---Sync---> | - Workflow Engine  | <---SQL---> | - PostgreSQL 15 |
 | - Drag-and-Drop UI    |              | - Webhook Handler  |             | - ISO 27001 Enc  |
 | - SAML/OIDC Auth     |              | - Rate Limit Mgr   |             | - Raw SQL Optims |
 +----------------------+              +--------------------+             +------------------+
          ^                                                                           ^
          |                                                                            |
          +--------------------------[ MANUAL QA GATE ]--------------------------------+
                                 (2-Day Turnaround Window)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework
**Priority:** High | **Status:** Complete | **Version:** v1.0.0

The Webhook Integration Framework is the backbone of the strategic partnership. It allows external legal service providers to push real-time updates (e.g., "Document Uploaded," "Case Status Changed") into the Nexus ecosystem without the need for constant polling.

**Functional Requirements:**
- **Payload Validation:** Every incoming webhook must be validated against a registered HMAC signature using a shared secret key to prevent spoofing.
- **Retry Logic:** If the Nexus internal processing fails, the system implements an exponential backoff retry mechanism (1m, 5m, 15m, 1h).
- **Event Routing:** The framework maps external API event types to internal Nexus "Triggers" that can be picked up by the Workflow Automation Engine.
- **Idempotency:** To prevent duplicate processing of the same event, every webhook payload is logged in an `incoming_webhooks` table, and processed based on a unique `external_event_id`.

**Technical Detail:**
The framework utilizes Elixir's `GenStage` to buffer incoming requests, ensuring that a spike in external API activity does not crash the application.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** In Progress | **Version:** v0.8.0

The dashboard is the primary interface for legal managers to track the "supply chain" of their legal cases. Given the complexity of legal data, a static dashboard is insufficient.

**Functional Requirements:**
- **Widget Library:** Users can choose from a set of pre-defined widgets: "Pending Procurement," "Vendor Performance Heatmap," "Budget Burn Rate," and "Case Timeline."
- **Drag-and-Drop Interface:** Using LiveView and a JS hook (SortableJS), users can rearrange widgets. The coordinates and dimensions of these widgets are saved to the user's profile in the database.
- **Real-time Data Binding:** Each widget is a LiveView component that subscribes to a Phoenix PubSub topic. When a webhook updates a case status, the widget updates instantly without a page refresh.
- **Custom Filtering:** Widgets support "Global Filters" (e.g., filter all widgets by "Case #12345" or "Partner: Smith").

**Technical Detail:**
Widget positions are stored as a JSONB column in the `user_dashboards` table, allowing for flexible layouts without requiring schema migrations for every new widget type.

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Not Started | **Version:** v0.1.0 (Planned)

The goal of this feature is to allow non-technical legal staff to automate procurement steps. For example: *"If a vendor's bid is > $10,000 AND the vendor is not ISO 27001 certified, then route the request to the Compliance Officer for manual review."*

**Functional Requirements:**
- **Visual Rule Builder:** A node-based UI where users can drag "Triggers" (e.g., Webhook Received), "Conditions" (e.g., Amount > X), and "Actions" (e.g., Send Email, Update Status).
- **Condition Logic:** Support for AND/OR logic gates and complex string matching (regex) for legal document filenames.
- **Execution Engine:** A background worker (Oban) that processes these rules asynchronously to ensure the UI remains responsive.
- **Audit Trail:** Every automated action must be logged with a timestamp and the ID of the rule that triggered it to satisfy legal auditing requirements.

**Technical Detail:**
Rules will be stored as a Directed Acyclic Graph (DAG) in PostgreSQL. The engine will traverse the graph starting from the trigger node.

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** Blocked | **Version:** v0.0.0

**BLOCKER:** Currently blocked by the third-party API rate limits. The authentication flow requires a "handshake" with the external partner's identity provider to verify user credentials, but the sandbox environment is currently hitting rate limits during the OAuth2 exchange.

**Functional Requirements:**
- **Granular Permissions:** Roles include `SuperAdmin`, `CaseManager`, `ProcurementOfficer`, and `ExternalVendor`.
- **Permission Matrix:** Access is defined at the resource level (e.g., `Vendor:Read`, `Vendor:Write`, `Case:Archive`).
- **Session Management:** Secure, encrypted cookies with a 12-hour expiration and sliding window renewal.
- **Audit Logs:** Every login attempt and permission change must be logged in the `security_audit_log` table.

**Technical Detail:**
RBAC will be implemented using a "Claims" based approach where the user's role is embedded in the session token, reducing the need to query the database on every request.

### 3.5 SSO Integration with SAML and OIDC Providers
**Priority:** Medium | **Status:** Complete | **Version:** v1.0.0

To support enterprise legal firms, Nexus integrates with standard identity providers (Azure AD, Okta, Ping Identity).

**Functional Requirements:**
- **SAML 2.0 Support:** Full support for Service Provider (SP) initiated flows.
- **OIDC Integration:** OpenID Connect for modern cloud-based authentication.
- **Just-In-Time (JIT) Provisioning:** Users are automatically created in the Nexus database upon their first successful SSO login, provided they belong to an authorized corporate domain.
- **Attribute Mapping:** Mapping of external SAML attributes (e.g., `department`) to internal Nexus roles.

**Technical Detail:**
Implemented using the `ueberauth` library in Elixir, ensuring a standardized way to handle multiple authentication providers.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST principles and return JSON. Authentication requires a Bearer Token in the header.

### 4.1 GET `/api/v1/vendors`
**Description:** Retrieves a paginated list of all registered legal vendors.
- **Query Params:** `page` (int), `per_page` (int), `status` (string).
- **Request Example:** `GET /api/v1/vendors?page=1&status=active`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "vend_9921", "name": "Global Discovery LLC", "rating": 4.8, "status": "active" },
    { "id": "vend_4432", "name": "Expert Witness Pro", "rating": 4.2, "status": "active" }
  ],
  "meta": { "total_count": 150, "total_pages": 8 }
}
```

### 4.2 POST `/api/v1/webhooks/register`
**Description:** Registers a new webhook endpoint for an external partner.
- **Request Body:**
```json
{
  "callback_url": "https://partner.com/nexus-receiver",
  "events": ["case.updated", "invoice.paid"],
  "secret_token": "sk_live_5521abc"
}
```
- **Response (201 Created):** `{ "id": "wh_001", "status": "active" }`

### 4.3 PATCH `/api/v1/cases/{case_id}/status`
**Description:** Updates the status of a legal procurement case.
- **Request Body:** `{ "status": "under_review", "comments": "Awaiting compliance check." }`
- **Response (200 OK):** `{ "case_id": "case_771", "new_status": "under_review", "updated_at": "2026-06-10T14:00:00Z" }`

### 4.4 GET `/api/v1/dashboard/widgets`
**Description:** Retrieves the user's personalized widget configuration.
- **Response (200 OK):**
```json
{
  "user_id": "user_123",
  "layout": [
    { "widget_id": "burn_rate", "x": 0, "y": 0, "w": 6, "h": 4 },
    { "widget_id": "pending_tasks", "x": 6, "y": 0, "w": 6, "h": 4 }
  ]
}
```

### 4.5 POST `/api/v1/automation/rules`
**Description:** Creates a new workflow automation rule.
- **Request Body:**
```json
{
  "name": "High Value Review",
  "trigger": "invoice.created",
  "condition": { "field": "amount", "operator": ">", "value": 10000 },
  "action": "notify_compliance"
}
```
- **Response (201 Created):** `{ "rule_id": "rule_99", "status": "enabled" }`

### 4.6 GET `/api/v1/audit/logs`
**Description:** Fetches security and activity logs for ISO 27001 compliance.
- **Query Params:** `start_date`, `end_date`, `user_id`.
- **Response (200 OK):**
```json
{
  "logs": [
    { "timestamp": "2026-05-01T10:00Z", "user": "u_1", "action": "AUTH_LOGIN", "ip": "192.168.1.1" }
  ]
}
```

### 4.7 PUT `/api/v1/vendors/{vendor_id}/certification`
**Description:** Updates the ISO certification status of a vendor.
- **Request Body:** `{ "is_certified": true, "expiry_date": "2027-12-31" }`
- **Response (200 OK):** `{ "vendor_id": "vend_9921", "certified": true }`

### 4.8 DELETE `/api/v1/webhooks/{webhook_id}`
**Description:** Deletes a webhook registration.
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. Due to the high volume of audit logs and the complexity of the automation engine, the schema is normalized to 3NF, except for the `user_dashboards` table which uses JSONB for flexibility.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `password_hash` (String, Nullable for SSO)
    - `role_id` (FK -> roles.id)
    - `last_login_at` (Timestamp)
    - `created_at` (Timestamp)

2.  **`roles`**
    - `id` (Integer, PK)
    - `name` (String, Unique) - e.g., 'SuperAdmin', 'Vendor'
    - `permissions` (JSONB) - List of granular permission strings.

3.  **`vendors`**
    - `id` (UUID, PK)
    - `company_name` (String)
    - `contact_email` (String)
    - `iso_certified` (Boolean)
    - `certification_expiry` (Date)
    - `overall_rating` (Decimal)

4.  **`cases`**
    - `id` (UUID, PK)
    - `case_number` (String, Unique)
    - `client_id` (UUID)
    - `status` (Enum: 'draft', 'pending', 'approved', 'closed')
    - `total_budget` (Decimal)
    - `assigned_manager_id` (FK -> users.id)

5.  **`procurement_requests`**
    - `id` (UUID, PK)
    - `case_id` (FK -> cases.id)
    - `vendor_id` (FK -> vendors.id)
    - `amount` (Decimal)
    - `status` (String)
    - `created_at` (Timestamp)

6.  **`automation_rules`**
    - `id` (UUID, PK)
    - `name` (String)
    - `trigger_event` (String)
    - `condition_logic` (JSONB)
    - `action_type` (String)
    - `is_active` (Boolean)

7.  **`incoming_webhooks`**
    - `id` (UUID, PK)
    - `external_event_id` (String, Unique)
    - `payload` (JSONB)
    - `processed_at` (Timestamp, Nullable)
    - `status` (Enum: 'pending', 'processed', 'failed')

8.  **`user_dashboards`**
    - `user_id` (FK -> users.id, PK)
    - `layout_config` (JSONB) - Stores widget coordinates and sizes.
    - `updated_at` (Timestamp)

9.  **`security_audit_log`**
    - `id` (BigInt, PK)
    - `user_id` (FK -> users.id)
    - `action` (String)
    - `ip_address` (Inet)
    - `timestamp` (Timestamp)
    - `resource_accessed` (String)

10. **`sso_providers`**
    - `id` (UUID, PK)
    - `provider_name` (String) - e.g., 'Okta'
    - `entity_id` (String)
    - `sso_url` (String)
    - `certificate` (Text)

### 5.2 Key Relationships
- **Users $\rightarrow$ Roles:** Many-to-One.
- **Cases $\rightarrow$ Procurement Requests:** One-to-Many.
- **Vendors $\rightarrow$ Procurement Requests:** One-to-Many.
- **Users $\rightarrow$ Security Audit Log:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Nexus utilizes a strict three-tier environment strategy to ensure that no unvetted code reaches production, satisfying the ISO 27001 requirement for change management.

**1. Development (Dev):**
- **Purpose:** Feature development and internal team testing.
- **Deployment:** Automated on every push to the `develop` branch.
- **Database:** Ephemeral PostgreSQL instances; data is reset weekly.
- **Access:** Full access for all 20+ team members.

**2. Staging (Staging):**
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and partner API integration testing.
- **Deployment:** Triggered upon merge from `develop` to `release` branch.
- **Database:** Mirror of production (anonymized).
- **Access:** Project Lead (Arun), DevOps (Udo), and select Stakeholders.

**3. Production (Prod):**
- **Purpose:** Live environment for legal clients.
- **Deployment:** **Manual QA Gate.** A deployment cannot occur until a QA lead signs off on the Staging build. There is a strict **2-day turnaround** for the QA window.
- **Database:** High-availability PostgreSQL cluster on Fly.io with point-in-time recovery (PITR).
- **Access:** Restricted to Udo Costa (DevOps) and Arjun Stein (Security).

### 6.2 Infrastructure Details
- **Runtime:** Elixir/Phoenix on Fly.io.
- **Clustering:** Distributed Erlang nodes across three regions (US-East, US-West, EU-West) to ensure 99.9% availability.
- **CI/CD Pipeline:** GitHub Actions $\rightarrow$ Fly.io.
- **Secrets Management:** Encrypted via Fly Secrets, injected as environment variables at runtime.

---

## 7. TESTING STRATEGY

Given the high executive visibility and the $3M investment, a "fail-fast" testing strategy is implemented across three layers.

### 7.1 Unit Testing
- **Focus:** Individual functions and business logic in Elixir modules.
- **Tooling:** `ExUnit`.
- **Requirement:** 80% code coverage is required for all new modules.
- **Specifics:** Testing the "Rule Builder" logic in isolation by mocking API responses.

### 7.2 Integration Testing
- **Focus:** The interaction between the Application and the Database/External APIs.
- **Tooling:** `Wallaby` for browser-based flows and custom Elixir scripts for API testing.
- **Key Scenario:** Testing the "Webhook $\rightarrow$ Automation Engine $\rightarrow$ Database Update" flow to ensure data consistency.
- **Handling External APIs:** Use of "VCR" (recording and replaying API responses) to bypass rate limits during integration tests.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Complete user journeys (e.g., "Admin logs in via SSO $\rightarrow$ Creates Case $\rightarrow$ Assigns Vendor $\rightarrow$ Receives Webhook Update").
- **Tooling:** `Playwright`.
- **Frequency:** Run nightly on the Staging environment.
- **Manual Gate:** The 2-day turnaround deployment window includes a manual "smoke test" performed by Xena Stein (Support Engineer) to ensure user-facing stability.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect leaving in 3 months | High | High | Negotiate timeline extension with stakeholders; prioritize knowledge transfer documentation and pair programming immediately. |
| **R-02** | Regulatory requirements change | Medium | High | Engage external legal-tech consultant for an independent assessment of the evolving compliance landscape. |
| **R-03** | Third-party API rate limits | High | Medium | Implement a robust caching layer and a request-queueing system; negotiate higher limits with the partner company. |
| **R-04** | Technical Debt (Raw SQL) | Medium | High | Schedule "Migration Sprints" to convert the 30% raw SQL queries back into Ecto ORM calls to make schema updates safer. |
| **R-05** | ISO 27001 Certification Failure | Low | Critical | Regular internal audits by Arjun Stein and a pre-audit gap analysis. |

**Probability/Impact Matrix:**
- **Critical:** High Probability / High Impact (Requires immediate executive intervention).
- **High:** Medium Probability / High Impact (Managed via active mitigation).
- **Medium:** High Probability / Low Impact (Handled by the dev team).

---

## 9. PROJECT TIMELINE

The project is executed in four primary phases. Dependencies are tightly coupled with the external partner's API release schedule.

### Phase 1: Foundation & Integration (Now – 2026-06-01)
- **Focus:** Webhook framework, SSO, and Basic Data Models.
- **Dependency:** External API Sandbox Access.
- **Key Deliverable:** Stable data ingestion pipeline.

### Phase 2: User Interface & Experience (2026-06-02 – 2026-06-15)
- **Focus:** Customizable Dashboard and Role-Based Access Control (once unblocked).
- **Milestone 1:** **Stakeholder Demo and Sign-off (Target: 2026-06-15).**
- **Dependency:** Resolution of RBAC blocker.

### Phase 3: Intelligence & Automation (2026-06-16 – 2026-08-15)
- **Focus:** Visual Rule Builder and Workflow Engine.
- **Milestone 2:** **Performance Benchmarks Met (Target: 2026-08-15).**
- **Dependency:** Stable dashboard deployment.

### Phase 4: Hardening & Compliance (2026-08-16 – 2026-10-15)
- **Focus:** Final security audits, ISO 27001 certification, and bug fixing.
- **Milestone 3:** **Security Audit Passed (Target: 2026-10-15).**
- **Dependency:** Full feature freeze by 2026-09-01.

---

## 10. MEETING NOTES

*Note: The official team notes are kept in a shared running document (approx. 200 pages) which is currently unsearchable. The following are transcribed summaries of the three most critical decision-making sessions.*

### Meeting 1: Architecture Alignment (2024-02-10)
**Attendees:** Arun, Udo, Arjun, Xena.
- **Discussion:** The team debated using a React frontend vs. Phoenix LiveView. Xena expressed concern about the complexity of maintaining a separate JS build pipeline for a 20-person team.
- **Decision:** Arun decided on LiveView to maximize development speed and reduce "state-sync" bugs.
- **Action Item:** Udo to set up the Fly.io cluster with three-region distribution.

### Meeting 2: The RBAC Blocker Crisis (2024-04-15)
**Attendees:** Arun, Arjun, Udo.
- **Discussion:** The team discovered that the external partner's API rate limits are far lower than documented. This is preventing the RBAC system from completing the OAuth2 handshake during testing.
- **Decision:** The project will "mock" the auth response in Dev/Staging to allow feature development to continue, but the "Blocked" status remains for the production-ready RBAC.
- **Action Item:** Arjun to contact the partner's technical lead to request a rate-limit increase for the `dev_client_id`.

### Meeting 3: Technical Debt Review (2024-05-01)
**Attendees:** Arun, Udo.
- **Discussion:** Udo pointed out that 30% of the queries are now Raw SQL to handle massive legal dataset joins that were timing out in Ecto. He warned that future migrations to the `cases` table could be catastrophic.
- **Decision:** The team will not refactor now (to avoid delaying Milestone 1) but will dedicate the first two weeks of Phase 4 specifically to "ORM Recovery."
- **Action Item:** Udo to document all Raw SQL queries in a centralized `sql_danger_zone.md` file.

---

## 11. BUDGET BREAKDOWN

The total budget of **$3,000,000** is allocated across four categories.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $2,100,000 | 20+ staff across 3 departments (Product, Eng, Ops) for 18 months. |
| **Infrastructure** | 15% | $450,000 | Fly.io premium hosting, ISO 27001 certified backups, and database clusters. |
| **Tools & Licensing** | 5% | $150,000 | SAML/OIDC provider licenses (Okta), Security auditing software. |
| **Contingency** | 10% | $300,000 | Reserved for external consultants and potential timeline extensions. |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Matrix
To maintain certification, Nexus must adhere to the following controls:
1.  **Access Control:** All administrative access to the production database requires Multi-Factor Authentication (MFA) and is logged.
2.  **Encryption:** Data at rest is encrypted using AES-256. All API communications must utilize TLS 1.3 with a minimum key length of 2048 bits.
3.  **Vulnerability Management:** Monthly dependency scans using `mix hex.compile` and automated Snyk scans on the GitHub repository.
4.  **Incident Response:** A defined 4-hour window for critical security patch deployment in the event of a Zero-Day vulnerability.

### Appendix B: Raw SQL Performance Optimization List
The following queries are identified as "Bypassing the ORM" for performance reasons and must be manually updated during any schema change:
- `GET /api/v1/vendors` (Complex join between `vendors`, `procurement_requests`, and `cases` to calculate `overall_rating`).
- `GET /api/v1/audit/logs` (Deep pagination across 10M+ rows of audit data).
- `POST /api/v1/automation/rules` (Recursive CTE used to validate that the rule graph does not contain cycles).