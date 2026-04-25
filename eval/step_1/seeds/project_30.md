# PROJECT SPECIFICATION DOCUMENT: IRONCLAD
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Final Draft for Executive Review  
**Project Code:** IC-AERO-2026  
**Company:** Flintrock Engineering  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Ironclad" is a mission-critical initiative undertaken by Flintrock Engineering to replace a 15-year-old legacy collaboration system. This legacy system currently serves as the central nervous system for the company’s aerospace operations, managing everything from fuselage design iterations to orbital trajectory calculations and cross-departmental communication. Due to the criticality of these operations, the replacement must occur with **zero downtime tolerance**. Any outage in collaboration tools translates directly to a loss of productivity for thousands of engineers and a potential risk to aerospace safety compliance.

### 1.2 Business Justification
The existing system, developed in the late 2000s, is built on monolithic architecture that cannot scale with current cloud-native requirements and suffers from significant latency issues when accessed from Flintrock’s international offices. Furthermore, the legacy system lacks modern security protocols, making it a liability under current aerospace industry regulations. 

Ironclad will implement a high-performance, real-time collaboration environment utilizing a Rust-based backend for maximum memory safety and execution speed, and a React-based frontend for a modern, responsive user experience. By utilizing Cloudflare Workers and SQLite at the edge, Flintrock will eliminate the "latency tax" currently paid by remote teams in five different countries.

### 1.3 ROI Projection and Financial Impact
With a substantial budget investment of **$3,000,000**, the project is high-visibility and carries high executive expectations. The projected Return on Investment (ROI) is calculated based on three primary drivers:
1. **Operational Efficiency:** Reduction in system latency from 400ms to <50ms for global users, projected to save 12,000 engineering man-hours annually.
2. **Risk Mitigation:** Elimination of legacy system crashes, which currently result in an estimated $150,000 loss per hour of downtime.
3. **Compliance Cost Reduction:** Achieving SOC 2 Type II compliance will reduce insurance premiums and legal auditing costs by approximately $200,000 per year.

The total projected 3-year net benefit is estimated at $7.4M, providing a significant ROI despite the high initial capital expenditure.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Ironclad follows a traditional three-tier architecture (Presentation, Business Logic, Data) but optimizes the data layer for global distribution.

**The Presentation Layer:** A React 18+ single-page application (SPA) utilizing Tailwind CSS for styling and Redux Toolkit for state management. It communicates with the backend via REST APIs and WebSockets for real-time updates.

**The Business Logic Layer:** A high-concurrency backend written in Rust using the Actix-web framework. Rust was chosen specifically for its "fearless concurrency" and memory safety, which are paramount in aerospace applications where data corruption is unacceptable.

**The Data Layer:** A hybrid approach utilizing SQLite for edge-caching and local state management via Cloudflare Workers, with a centralized PostgreSQL instance for the primary source of truth.

### 2.2 System Diagram (ASCII Representation)
```text
[ USER BROWSER ] <---(WebSocket/HTTPS)---> [ CLOUDFLARE WORKERS ]
       |                                           |
       | (React Frontend)                  (Edge Logic / SQLite)
       v                                           v
[ GLOBAL CDN ] <--------------------------> [ RUST BACKEND (Actix) ]
                                                   |
                                                   | (SQL / TCP)
                                                   v
                                       [ CENTRAL POSTGRESQL DB ]
                                                   |
                                       [ SOC 2 COMPLIANCE LAYER ]
```

### 2.3 Tech Stack Specifications
- **Frontend:** React v18.2, TypeScript v5.0, Tailwind CSS v3.3.
- **Backend:** Rust v1.72 (Stable), Actix-web v4.4, Serde for serialization.
- **Database:** SQLite v3.42 (Edge), PostgreSQL v15.4 (Primary).
- **Infrastructure:** Cloudflare Workers, Cloudflare D1, AWS (for primary DB).
- **Deployment:** Manual QA Gate $\rightarrow$ Staging $\rightarrow$ Production.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** In Review
**Description:** 
The dashboard is the primary landing page for all Ironclad users. Given the diverse roles within Flintrock (from procurement officers to propulsion engineers), a one-size-fits-all view is insufficient. This feature allows users to create a personalized workspace using a grid-based layout.

**Technical Requirements:**
- **Grid System:** Implementation of `react-grid-layout` to allow users to resize and reposition widgets.
- **Widget Library:** Initial launch will include six core widgets: *Active Projects*, *Team Notifications*, *Upcoming Milestones*, *Recent Documents*, *System Health Status*, and *Personal Tasks*.
- **Persistence:** Dashboard layouts must be persisted in the database as a JSON blob linked to the UserID, ensuring the layout remains consistent across different devices.
- **State Management:** Real-time updates for widget data must be handled via WebSockets to prevent the need for page refreshes.

**User Workflow:**
1. User enters "Edit Mode" via a dashboard toggle.
2. User drags a widget from the "Widget Gallery" onto the grid.
3. User resizes the widget to fit their preferred viewing area.
4. User clicks "Save Layout," triggering a `PUT /api/v1/user/dashboard` request.

---

### 3.2 Localization and Internationalization (L10n/I18n)
**Priority:** High | **Status:** In Review
**Description:** 
Ironclad must support 12 languages to accommodate Flintrock’s global distributed team. This is not merely a translation of UI strings but a comprehensive adaptation of date formats, numerical delimiters, and cultural contexts.

**Technical Requirements:**
- **Framework:** Use of `react-i18next` for frontend translation management.
- **Backend Support:** The Rust backend must utilize the `fluent` library to handle complex pluralization and gender-specific grammar in translations.
- **Language Set:** English (US/UK), French, German, Japanese, Mandarin, Korean, Spanish, Portuguese, Italian, Russian, Arabic, and Hindi.
- **Dynamic Loading:** Translation files must be split into namespaces and loaded asynchronously to minimize the initial bundle size.

**Localization Logic:**
The system will detect the user's browser locale upon first login and store the preference in the `UserPreferences` table. If a user manually changes the language, a global state update is triggered, and the application re-renders without a full page reload.

---

### 3.3 Automated Billing and Subscription Management
**Priority:** High | **Status:** Complete
**Description:** 
While Ironclad is an internal tool, it operates on a "charge-back" model where different aerospace departments (e.g., "Mars Initiative," "Satellite Division") are billed based on their seat count and data storage usage.

**Technical Requirements:**
- **Integration:** Integration with an internal corporate financial API to automate ledger entries.
- **Calculation Engine:** A Rust-based cron job that runs on the 1st of every month to calculate total resource consumption per department.
- **Tiered Logic:** Implementation of "Basic," "Advanced," and "Enterprise" tiers for different project sizes.
- **Audit Trail:** Every billing event must be logged with an immutable timestamp and a unique transaction ID for SOC 2 compliance.

**Completed Implementation:**
The system currently supports automated invoice generation in PDF format and triggers alerts to department heads when their budget threshold (defined in `DeptBudget` table) is reached 80%.

---

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** In Progress
**Description:** 
Given the sensitivity of aerospace data, password-based authentication is insufficient. Ironclad requires a robust 2FA system, specifically prioritizing hardware-based security keys.

**Technical Requirements:**
- **WebAuthn API:** Implementation of the WebAuthn standard to allow FIDO2 keys (e.g., YubiKey) for authentication.
- **Fallback Mechanisms:** TOTP (Time-based One-Time Password) via apps like Google Authenticator for users without hardware keys.
- **Recovery Flow:** Secure generation of one-time recovery codes (10 codes per user) stored using bcrypt hashing.
- **Session Management:** Forced re-authentication every 30 days or upon detection of a new IP address.

**Current Status:**
The TOTP flow is fully implemented. The team is currently integrating the `webauthn-rs` crate to handle the challenge-response cycle for hardware keys.

---

### 3.5 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Medium | **Status:** Not Started
**Description:** 
Users must be able to find specific technical documents or communication threads across millions of records using complex filters.

**Technical Requirements:**
- **Indexing Engine:** Implementation of a full-text search (FTS) index. While the core is PostgreSQL, we will evaluate Meilisearch or Elasticsearch for higher-performance indexing.
- **Faceted Filtering:** Ability to filter results by *Project ID*, *Author*, *Date Range*, *File Type*, and *Security Clearance Level*.
- **Search Syntax:** Support for boolean operators (AND, OR, NOT) and exact-match quotes.
- **Performance:** Target search response time of $<200$ms for queries across 1M+ records.

**Plan of Action:**
Once the launch-blocker (Dashboard) is resolved, the team will implement a search middleware in Rust that sanitizes queries and optimizes the SQL `tsvector` calls to the database.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `Bearer <JWT>` token in the header.

### 4.1 `GET /auth/session`
- **Description:** Validates the current session and returns user profile metadata.
- **Request:** `GET /api/v1/auth/session`
- **Response (200 OK):**
  ```json
  {
    "user_id": "usr_9921",
    "username": "nstein_tech",
    "role": "admin",
    "session_expiry": "2023-12-01T12:00:00Z"
  }
  ```

### 4.2 `POST /collaboration/document/create`
- **Description:** Creates a new real-time collaborative document.
- **Request Body:**
  ```json
  {
    "title": "Fuselage Stress Test Results",
    "project_id": "proj_alpha_01",
    "visibility": "internal"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "doc_id": "doc_44512",
    "url": "/edit/doc_44512",
    "created_at": "2023-10-25T10:00:00Z"
  }
  ```

### 4.3 `PUT /user/dashboard/layout`
- **Description:** Updates the user's customized dashboard widget configuration.
- **Request Body:**
  ```json
  {
    "layout_config": [
      {"id": "widget_tasks", "x": 0, "y": 0, "w": 4, "h": 2},
      {"id": "widget_health", "x": 4, "y": 0, "w": 2, "h": 2}
    ]
  }
  ```
- **Response (200 OK):** `{"status": "success", "updated_at": "..."}`

### 4.4 `GET /search/faceted`
- **Description:** Performs a full-text search with applied filters.
- **Params:** `q=propulsion`, `project=mars_01`, `limit=20`
- **Response (200 OK):**
  ```json
  {
    "results": [...],
    "facets": {
      "projects": {"mars_01": 12, "venus_02": 3},
      "years": {"2023": 10, "2022": 5}
    }
  }
  ```

### 4.5 `POST /auth/2fa/register-key`
- **Description:** Registers a new hardware security key.
- **Request Body:** `{ "challenge": "...", "credentialId": "..." }`
- **Response (200 OK):** `{"status": "key_registered"}`

### 4.6 `GET /billing/usage`
- **Description:** Returns current month's resource consumption for the user's department.
- **Response (200 OK):**
  ```json
  {
    "dept_id": "dept_propulsion",
    "current_spend": 12450.00,
    "budget_limit": 50000.00,
    "percentage_used": 24.9
  }
  ```

### 4.7 `PATCH /collaboration/document/permissions`
- **Description:** Updates access control for a specific document.
- **Request Body:** `{ "doc_id": "doc_123", "user_id": "usr_456", "access": "read-write" }`
- **Response (200 OK):** `{"status": "permissions_updated"}`

### 4.8 `GET /system/health`
- **Description:** Public health check endpoint for monitoring.
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "db_connection": "connected",
    "version": "1.0.4-stable"
  }
  ```

---

## 5. DATABASE SCHEMA

The system uses a relational model in PostgreSQL with SQLite mirrors at the edge.

### 5.1 Table Definitions

1.  **`Users`**
    - `user_id` (UUID, PK)
    - `email` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `mfa_enabled` (BOOLEAN)
    - `created_at` (TIMESTAMP)
2.  **`Profiles`**
    - `profile_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ Users)
    - `full_name` (VARCHAR)
    - `timezone` (VARCHAR)
    - `language_pref` (VARCHAR(5))
3.  **`Departments`**
    - `dept_id` (UUID, PK)
    - `dept_name` (VARCHAR)
    - `budget_limit` (NUMERIC)
    - `cost_center_code` (VARCHAR)
4.  **`Projects`**
    - `project_id` (UUID, PK)
    - `dept_id` (UUID, FK $\rightarrow$ Departments)
    - `project_name` (VARCHAR)
    - `security_level` (INT)
5.  **`Documents`**
    - `doc_id` (UUID, PK)
    - `project_id` (UUID, FK $\rightarrow$ Projects)
    - `content` (TEXT/JSONB)
    - `last_modified_by` (UUID, FK $\rightarrow$ Users)
    - `version_number` (INT)
6.  **`Document_Permissions`**
    - `perm_id` (UUID, PK)
    - `doc_id` (UUID, FK $\rightarrow$ Documents)
    - `user_id` (UUID, FK $\rightarrow$ Users)
    - `access_level` (ENUM: 'read', 'write', 'admin')
7.  **`Dashboard_Configs`**
    - `config_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ Users)
    - `layout_json` (JSONB)
    - `updated_at` (TIMESTAMP)
8.  **`Billing_Events`**
    - `event_id` (UUID, PK)
    - `dept_id` (UUID, FK $\rightarrow$ Departments)
    - `amount` (NUMERIC)
    - `timestamp` (TIMESTAMP)
    - `description` (TEXT)
9.  **`Auth_Keys`**
    - `key_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ Users)
    - `public_key` (TEXT)
    - `credential_id` (TEXT)
10. **`Audit_Logs`**
    - `log_id` (BIGINT, PK)
    - `user_id` (UUID, FK $\rightarrow$ Users)
    - `action` (VARCHAR)
    - `resource_id` (UUID)
    - `timestamp` (TIMESTAMP)

### 5.2 Relationships
- **One-to-One:** `Users` $\rightarrow$ `Profiles`.
- **One-to-Many:** `Departments` $\rightarrow$ `Projects`; `Users` $\rightarrow$ `Dashboard_Configs`.
- **Many-to-Many:** `Users` $\leftrightarrow$ `Documents` via `Document_Permissions`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To ensure the "zero downtime" requirement, Ironclad utilizes a three-stage pipeline.

**1. Development (Dev):**
- **Purpose:** Active feature development and unit testing.
- **Hosting:** Local Docker containers and a shared dev-cluster in AWS.
- **Database:** Ephemeral PostgreSQL instances.

**2. Staging (QA):**
- **Purpose:** Pre-production validation, SOC 2 auditing, and UAT (User Acceptance Testing).
- **Hosting:** Mirror of Production environment.
- **Data:** Anonymized production data snapshots.
- **Gate:** Manual QA sign-off by Nia Stein is required before any build moves to Production.

**3. Production (Prod):**
- **Purpose:** Live aerospace operations.
- **Hosting:** Globally distributed Cloudflare Workers + AWS RDS (Multi-AZ).
- **Deployment:** Blue-Green deployment strategy. The "Green" environment is spun up; traffic is shifted incrementally (5%, 25%, 100%) after health checks pass.

### 6.2 Infrastructure Pipeline
The deployment turnaround is strictly **2 days**. 
- **Day 1:** Merge to `main` $\rightarrow$ Automated CI (Rust tests/React linting) $\rightarrow$ Deploy to Staging.
- **Day 2:** Manual QA Gate $\rightarrow$ Final approval $\rightarrow$ Production rollout.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `#[test]` modules for every business logic function. Focus on edge cases in the billing engine and permission logic.
- **Frontend:** Vitest and React Testing Library for component-level verification.
- **Coverage Target:** 85% minimum line coverage.

### 7.2 Integration Testing
- **API Testing:** Postman/Newman collections run against the Staging environment to verify endpoint contracts.
- **Database Testing:** Integration tests to ensure raw SQL queries (the 30% bypass) do not break during schema migrations.
- **Concurrency Testing:** Using `k6` to simulate 1,000 concurrent users editing a single document to test WebSocket stability.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Critical Paths:** 
    - Login $\rightarrow$ 2FA $\rightarrow$ Dashboard Access.
    - Document Creation $\rightarrow$ Real-time Edit $\rightarrow$ Save.
    - Billing Report Generation.
- **Frequency:** E2E suite runs every night at 02:00 UTC.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | High | Accept risk; weekly knowledge transfer sessions; document all core logic in Wiki. |
| R-02 | Regulatory requirements change | Medium | High | Document workarounds in a dedicated "Compliance Log"; share with legal weekly. |
| R-03 | ORM bypass causing migration failure | Medium | Critical | Implement a strict manual review for all raw SQL changes; run migration dry-runs on Staging. |
| R-04 | Design disagreement (Product vs Eng) | High | Medium | Scheduled mediation meetings with Nia Stein as final arbiter. |
| R-05 | SOC 2 Compliance failure | Low | Critical | Pre-audit by external consultant 2 months before launch. |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required (R-03, R-05).
- **High:** Weekly monitoring (R-01, R-02).
- **Medium:** Monthly review (R-04).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Description
- **Phase 1: Foundation (Now - Jan 2026):** Core Rust backend, Database schema finalization, and Billing system completion.
- **Phase 2: Feature Build (Feb 2026 - May 2026):** Dashboard implementation, L10n integration, and 2FA completion.
- **Phase 3: Hardening & Compliance (May 2026 - July 2026):** SOC 2 Audit, Performance tuning of raw SQL, and Beta testing.
- **Phase 4: Deployment & Stability (July 2026 - Sept 2026):** Phased rollout and post-launch monitoring.

### 9.2 Key Milestones
- **Milestone 1: Production Launch**
  - **Target Date:** 2026-05-15
  - **Dependency:** SOC 2 Compliance, Dashboard "Critical" status resolved.
- **Milestone 2: Internal Alpha Release**
  - **Target Date:** 2026-07-15
  - **Dependency:** 2FA stable, L10n for top 3 languages.
- **Milestone 3: Post-launch Stability Confirmed**
  - **Target Date:** 2026-09-15
  - **Dependency:** NPS score > 40, 10k MAU target.

---

## 10. MEETING NOTES

### Meeting 1: Technical Debt and the ORM Dilemma
**Date:** 2023-11-12  
**Attendees:** Nia Stein, Meera Stein, Juno Stein  
**Discussion:**
The team discussed the current state of the data layer. Meera noted that 30% of the queries bypass the ORM for performance reasons. Juno raised concerns that this makes database migrations dangerous as the ORM cannot track these dependencies.
**Decisions:**
- We will not rewrite the raw SQL now (too time-consuming).
- A "SQL Registry" document will be created to track all raw queries.
**Action Items:**
- [Meera] Create the SQL Registry document. (Due: Nov 19)
- [Nia] Review migration scripts for the next sprint. (Due: Nov 20)

### Meeting 2: Dashboard Design Conflict
**Date:** 2023-12-05  
**Attendees:** Nia Stein, Product Lead (External), Engineering Team  
**Discussion:**
Product wants a highly fluid, "canvas-style" dashboard. Engineering argues that the requested complexity will jeopardize the May 15th launch date and introduce stability risks.
**Decisions:**
- Compromise reached: The dashboard will use a structured grid (react-grid-layout) rather than a free-form canvas.
- This allows for the "drag-and-drop" feel while keeping the underlying data structure simple.
**Action Items:**
- [Nia] Update the feature spec for the Dashboard. (Due: Dec 07)
- [Product Lead] Approve the grid-based mockups. (Due: Dec 10)

### Meeting 3: SOC 2 Compliance Strategy
**Date:** 2024-01-15  
**Attendees:** Juno Stein, Nia Stein, Yara Gupta  
**Discussion:**
Juno presented the requirements for SOC 2 Type II. The main gaps are in the audit logging of the legacy data migration and the lack of hardware-key enforcement.
**Decisions:**
- Implementation of the `Audit_Logs` table is now a P0 priority.
- Yara (Intern) will assist in documenting the "Access Control Matrix" for the auditor.
**Action Items:**
- [Juno] Finalize the Audit Log schema. (Due: Jan 20)
- [Yara] Map all user roles to specific API permissions. (Due: Jan 25)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000  

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 15 members over 2.5 years, including benefits. |
| **Infrastructure** | 15% | $450,000 | Cloudflare Workers, AWS RDS, Global CDN costs. |
| **Software & Tools** | 5% | $150,000 | IDE licenses, CI/CD tools, SOC 2 Audit fees. |
| **Contingency** | 15% | $450,000 | Reserved for regulatory changes and emergency staffing. |

**Financial Tracking:**
- Total Spent to Date: $840,000
- Remaining Balance: $2,160,000
- Burn Rate: ~$45,000 / month

---

## 12. APPENDICES

### Appendix A: Raw SQL Performance Justification
In several critical paths (e.g., the `Document_Permissions` lookup), the ORM generates nested joins that result in $O(n^2)$ complexity. By using raw SQL with specific indexed hints (`INDEX(idx_doc_user)`), the team reduced query execution time from 1.2s to 45ms. This optimization is required to meet the zero-downtime and high-performance requirements of Flintrock Engineering's aerospace workflows.

### Appendix B: L10n Translation Mapping Table
The following mapping is used for the 12 supported languages to ensure consistency across the frontend and backend:

| Language | ISO Code | Backend Bundle | Locale Priority |
| :--- | :--- | :--- | :--- |
| English (US) | en-US | `en_US.ftl` | 1 |
| French | fr-FR | `fr_FR.ftl` | 2 |
| German | de-DE | `de_DE.ftl` | 3 |
| Japanese | ja-JP | `ja_JP.ftl` | 4 |
| Mandarin | zh-CN | `zh_CN.ftl` | 5 |
| Korean | ko-KR | `ko_KR.ftl` | 6 |
| Spanish | es-ES | `es_ES.ftl` | 7 |
| Portuguese | pt-BR | `pt_BR.ftl` | 8 |
| Italian | it-IT | `it_IT.ftl` | 9 |
| Russian | ru-RU | `ru_RU.ftl` | 10 |
| Arabic | ar-SA | `ar_SA.ftl` | 11 |
| Hindi | hi-IN | `hi_IN.ftl` | 12 |