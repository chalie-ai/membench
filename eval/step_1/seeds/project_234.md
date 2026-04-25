# PROJECT SPECIFICATION DOCUMENT: PROJECT DELPHI
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Baseline Approved  
**Company:** Hearthstone Software  
**Project Lead:** Devika Oduya (VP of Product)

---

## 1. EXECUTIVE SUMMARY

Project Delphi is a mission-critical strategic SaaS platform developed by Hearthstone Software, specifically engineered for the real estate industry. The primary objective of Delphi is to establish a sophisticated strategic partnership integration, serving as a bridge between Hearthstone’s internal ecosystem and a third-party external partner’s API. Given the nature of the partnership, the project is bound by the external partner's development timeline, necessitating a flexible yet rigorous architectural approach.

### Business Justification
The real estate sector is currently plagued by fragmented data silos and manual entry processes that slow down the closing of transactions. By integrating with the external partner’s API, Delphi will automate the synchronization of property listings, escrow data, and client documentation. The strategic value lies in "locking in" the partnership, creating a competitive moat that prevents clients from migrating to competitors by embedding Hearthstone’s services directly into the partner's workflow.

The decision to use a Ruby on Rails monolith, despite the industry trend toward microservices, is a calculated strategic choice. By prioritizing "speed to market" and "simplicity of maintenance," Hearthstone can deploy a stable product within the modest budget of $400,000. This allows the veteran team of six to focus on the complex logic of the API synchronization rather than the overhead of distributed system orchestration.

### ROI Projection
The Return on Investment (ROI) for Project Delphi is calculated based on two primary KPIs: a 50% reduction in manual processing time for end-users and a 35% reduction in cost per transaction compared to the legacy system. 

1. **Labor Savings:** By automating data entry and syncing, we project a saving of approximately 12 hours per user per week. Across a target user base of 500 agents, this equates to 6,000 hours of recovered productivity per week.
2. **Operational Efficiency:** Reducing the cost per transaction by 35% is achieved by eliminating redundant API calls and manual audit checks through the implementation of CQRS and event sourcing, which provide a built-in audit trail.
3. **Market Position:** While a competitor is currently estimated to be two months ahead in development, the robust localization and advanced workflow automation within Delphi are expected to provide a superior user experience that will reclaim market share within six months of launch.

The projected break-even point for the $400,000 investment is estimated at 14 months post-production launch, based on a conservative subscription growth model and the reduction of operational overhead.

---

## 2. TECHNICAL ARCHITECTURE

### Architectural Philosophy
Delphi is built as a **Ruby on Rails monolith**. This choice minimizes the "network tax" and simplifies deployment on **Heroku**. To balance the simplicity of a monolith with the need for high-integrity data tracking (essential for real estate audits), the system employs **CQRS (Command Query Responsibility Segregation)** with **Event Sourcing** for audit-critical domains (specifically the Financials and Contract modules).

### System Diagram (ASCII Representation)
```text
[ External Partner API ] <---- HTTPS/REST ----> [ Delphi API Gateway/Adapter ]
                                                            |
                                                            v
[ Client Browser/App ] <--- JSON/HTML ---> [ Rails Application Layer ]
                                                            |
       _____________________________________________________|_____________________________________________________
      |                                                     |                                                     |
[ Command Side (Write) ]                       [ Query Side (Read) ]                       [ Background Workers ]
      |                                                     |                                                     |
      v                                                     v                                                     v
[ Event Store (MySQL) ] ----(Projector)----> [ Read Models (MySQL) ] <--- [ Sidekiq / Redis ] <--- [ Event Triggers ]
      |                                                     |                                                     |
      +-----------------------------------------------------+------------------------------------------------------+
                                                            |
                                                   [ Heroku Platform ]
                                                            |
                                                   [ MySQL Managed DB ]
```

### Component Details
- **The Adapter:** A dedicated layer designed to handle the external API's idiosyncrasies, including rate limiting and pagination.
- **Event Store:** Instead of updating a record in place, every change to a property or contract is stored as an immutable event. This ensures a 100% accurate audit trail for regulatory reviews.
- **Projectors:** Background processes that take events and update the "Read Models" (standard SQL tables) for fast retrieval.
- **Deployment Strategy:** Quarterly releases. This slow cadence is intentional to align with the regulatory review cycles of the real estate industry, ensuring that every update is vetted for compliance.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### Feature 1: Localization and Internationalization (L10n/I18n)
**Priority:** High | **Status:** In Progress
**Requirement:** The platform must support 12 distinct languages to facilitate global real estate expansion.

**Detailed Specification:**
The system utilizes the Rails `I18n` library but extends it with a database-backed dynamic translation layer to allow administrators to update terminology without a full code deployment. The 12 supported languages include English, Spanish, French, German, Mandarin, Japanese, Portuguese, Italian, Arabic, Korean, Russian, and Dutch.

The implementation requires a `Locale` model and a `Translation` model. Every user profile is linked to a `preferred_locale`. When a request hits the application, a middleware identifies the locale from the URL (e.g., `/es/dashboard`) or the user session. 

**Critical Technical Requirements:**
- **RTL Support:** For Arabic, the CSS must switch to a Right-to-Left (RTL) layout. This is handled by adding a `dir="rtl"` attribute to the `<html>` tag based on the locale.
- **Currency Formatting:** Real estate values must be formatted according to the locale (e.g., using commas vs. periods for decimals).
- **Timezone Handling:** All timestamps are stored in UTC and converted to the user's local timezone via the `timezone` gem.
- **Interpolation:** The system must support complex interpolation for dynamic strings (e.g., "Welcome, [User Name], your property in [City] is ready").

**Success Criteria:** A user can switch between all 12 languages without seeing any "missing translation" keys, and the UI remains visually coherent in RTL modes.

---

### Feature 2: Advanced Search with Faceted Filtering
**Priority:** Medium | **Status:** Complete
**Requirement:** Users must be able to filter thousands of properties using multiple criteria simultaneously with sub-second response times.

**Detailed Specification:**
The search engine is powered by a combination of MySQL full-text indexing for basic queries and a custom-built faceted filtering system. Unlike simple search, faceted search allows users to see the count of results for each filter option (e.g., "3 Bedrooms (42)").

**Technical Implementation:**
The system uses a "Query Object" pattern to build complex SQL queries dynamically. To avoid the performance hit of `COUNT(*)` on large tables, Delphi utilizes a cached "Facets Table" that is updated every 15 minutes via a Sidekiq cron job.

**Filtering Capabilities:**
- **Text Search:** Full-text search across property descriptions and addresses.
- **Range Filters:** Price ranges, square footage, and year built.
- **Boolean Filters:** "Has Pool," "Garage," "Waterfront."
- **Categorical Filters:** Property type (Condo, Single Family, Commercial).

**Performance Benchmarks:**
The search must return results in under 200ms for a dataset of 100,000 properties. This is achieved by indexing all filtered columns and using a materialized view for the most common search combinations.

---

### Feature 3: Workflow Automation Engine
**Priority:** Medium | **Status:** Complete
**Requirement:** A visual rule builder that allows non-technical users to automate repetitive tasks (e.g., "If property status changes to 'Sold', send email to Accountant").

**Detailed Specification:**
The engine consists of a "Trigger-Condition-Action" architecture. 
1. **Trigger:** An event emitted by the system (e.g., `PropertyUpdated`, `DocumentUploaded`).
2. **Condition:** A logical check (e.g., `Price > 1,000,000`).
3. **Action:** A resulting operation (e.g., `SendEmail`, `UpdateStatus`, `CreateTask`).

**The Visual Rule Builder:**
The frontend utilizes a drag-and-drop interface where users can connect blocks. This visual graph is serialized into a JSON blob stored in the `automation_rules` table. The backend parses this JSON into a series of Ruby procs that are executed asynchronously via Sidekiq.

**Execution Logic:**
To prevent infinite loops (e.g., Rule A triggers Rule B, which triggers Rule A), the engine implements a "recursion depth" limit of 5. If a chain of automations exceeds this limit, the system halts the execution and logs a critical error to the admin dashboard.

---

### Feature 4: Real-time Collaborative Editing
**Priority:** Low | **Status:** In Design
**Requirement:** Multiple users should be able to edit a property listing or contract simultaneously without overwriting each other's changes.

**Detailed Specification:**
This feature is designed as a "Nice to Have" and is currently in the architectural design phase. The proposed solution is to implement **Operational Transformation (OT)** or **Conflict-free Replicated Data Types (CRDTs)** to handle concurrency.

**Proposed Workflow:**
1. **WebSockets:** Use ActionCable (Rails' built-in WebSocket framework) to push updates to all connected clients in real-time.
2. **Presence Tracking:** A "Who is here" sidebar showing active users and their current cursor position.
3. **Conflict Resolution:** Since the project uses event sourcing, conflict resolution is handled by treating each edit as a discrete event. If two users edit the same field, the "Last Write Wins" (LWW) strategy will be applied by default, but a "Conflict History" will be maintained allowing a manager to revert to a previous state.

**UI/UX Considerations:**
- Fields being edited by another user will be highlighted in a specific color (assigned to that user).
- A "Locking" mechanism will be implemented for critical fields (e.g., Final Sale Price) to prevent any simultaneous edits.

---

### Feature 5: A/B Testing Framework (Feature Flag System)
**Priority:** Medium | **Status:** In Progress
**Requirement:** The ability to toggle features for specific user segments and measure the impact of different UI versions.

**Detailed Specification:**
Instead of a third-party tool, Delphi uses a custom-baked framework integrated into the `FeatureFlags` module. This ensures no external dependencies for critical feature delivery.

**The Mechanism:**
Feature flags are stored in a MySQL table `feature_flags` with columns for `flag_name`, `enabled`, and `percentage_rollout`. The system uses a deterministic hash of the `user_id` to decide if a user falls into the "A" or "B" group, ensuring a consistent experience across sessions.

**A/B Testing Integration:**
When a feature flag is marked as an "Experiment," the system begins logging all interactions with that feature into the `experiment_metrics` table.
- **Variant A:** Control group (current behavior).
- **Variant B:** Test group (new behavior).

**Metrics Captured:**
- Click-through rate (CTR) on the feature.
- Time-to-completion for the task associated with the feature.
- Conversion rate (e.g., "Did the user complete the listing creation?").

The framework is designed to allow the Product Lead (Devika) to toggle a feature "OFF" instantly across the entire platform if a critical bug is discovered in production.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer` token in the Authorization header.

### 1. Sync External Data
- **Path:** `POST /sync/external_properties`
- **Description:** Triggers a pull of property data from the partner API.
- **Request Body:** `{ "partner_id": "string", "sync_type": "full|delta" }`
- **Response (202 Accepted):** `{ "job_id": "job_abc123", "status": "queued" }`

### 2. Get Property Details
- **Path:** `GET /properties/:id`
- **Description:** Retrieves detailed information for a specific property.
- **Response (200 OK):**
```json
{
  "id": "prop_99",
  "address": "123 Maple St",
  "price": 450000,
  "status": "active",
  "locale": "en-US"
}
```

### 3. Update Property Status
- **Path:** `PATCH /properties/:id/status`
- **Description:** Updates the status of a property (triggers workflow automation).
- **Request Body:** `{ "status": "sold" }`
- **Response (200 OK):** `{ "id": "prop_99", "new_status": "sold", "updated_at": "2023-10-24T10:00:00Z" }`

### 4. Create Automation Rule
- **Path:** `POST /automations/rules`
- **Description:** Saves a new visual rule configuration.
- **Request Body:** `{ "name": "Sold Notification", "logic": { "trigger": "status_change", "condition": "price > 500k", "action": "email_admin" } }`
- **Response (201 Created):** `{ "rule_id": "rule_001", "status": "active" }`

### 5. Fetch Search Facets
- **Path:** `GET /search/facets`
- **Description:** Returns the counts for all available filters.
- **Response (200 OK):**
```json
{
  "property_types": { "Condo": 150, "SingleFamily": 300 },
  "price_ranges": { "0-200k": 50, "200k-500k": 200 }
}
```

### 6. Execute Search
- **Path:** `GET /search/properties`
- **Description:** Performs a faceted search.
- **Query Params:** `?q=modern+villa&price_max=600000&type=Condo`
- **Response (200 OK):** `{ "results": [...], "total_count": 42, "page": 1 }`

### 7. Toggle Feature Flag
- **Path:** `POST /admin/feature_flags/:flag_id/toggle`
- **Description:** Enables or disables a feature (Admin only).
- **Request Body:** `{ "enabled": false }`
- **Response (200 OK):** `{ "flag": "beta_search", "status": "disabled" }`

### 8. Get Audit Log
- **Path:** `GET /audit/events/:property_id`
- **Description:** Retrieves the event stream for a specific property (CQRS Event Store).
- **Response (200 OK):**
```json
[
  { "event_id": "evt_1", "type": "PriceChanged", "payload": { "old": 400k, "new": 450k }, "timestamp": "..." },
  { "event_id": "evt_2", "type": "StatusChanged", "payload": { "new": "sold" }, "timestamp": "..." }
]
```

---

## 5. DATABASE SCHEMA

The database is hosted on **MySQL**. Below are the core tables and their relationships.

### Table 1: `users`
- `id` (UUID, PK)
- `email` (String, Unique)
- `password_digest` (String)
- `preferred_locale` (String, default 'en')
- `role` (Enum: admin, agent, partner)
- `created_at` (Timestamp)

### Table 2: `properties` (Read Model)
- `id` (UUID, PK)
- `external_id` (String, Index) - Link to partner API
- `address` (String)
- `price` (Decimal)
- `status` (String)
- `property_type` (String)
- `updated_at` (Timestamp)
- *Relationship: Belongs to User (Agent)*

### Table 3: `events` (The Event Store)
- `id` (BigInt, PK)
- `aggregate_id` (UUID, Index) - Usually the Property ID
- `event_type` (String) - e.g., "PropertyPriceUpdated"
- `payload` (JSONB) - The actual data change
- `created_at` (Timestamp)
- *Relationship: Many-to-One with Properties*

### Table 4: `locales`
- `id` (Int, PK)
- `code` (String, Unique) - e.g., "en", "fr", "ar"
- `name` (String)
- `is_rtl` (Boolean)

### Table 5: `translations`
- `id` (Int, PK)
- `locale_id` (FK -> locales.id)
- `key` (String) - The translation key
- `value` (Text) - The translated text
- *Relationship: Belongs to Locale*

### Table 6: `automation_rules`
- `id` (UUID, PK)
- `name` (String)
- `logic_json` (JSONB)
- `is_active` (Boolean)
- `created_by` (FK -> users.id)

### Table 7: `feature_flags`
- `id` (Int, PK)
- `flag_name` (String, Unique)
- `enabled` (Boolean)
- `rollout_percentage` (Int)
- `experiment_id` (String, Nullable)

### Table 8: `experiment_metrics`
- `id` (BigInt, PK)
- `feature_flag_id` (FK -> feature_flags.id)
- `user_id` (FK -> users.id)
- `action` (String) - e.g., "click"
- `timestamp` (Timestamp)

### Table 9: `search_facets_cache`
- `facet_key` (String, PK)
- `facet_value` (String)
- `count` (Int)
- `last_updated` (Timestamp)

### Table 10: `partner_sync_logs`
- `id` (BigInt, PK)
- `sync_job_id` (String)
- `status` (Enum: success, failure)
- `records_processed` (Int)
- `error_message` (Text)
- `completed_at` (Timestamp)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### Environment Strategy
Delphi utilizes three distinct Heroku environments to ensure stability and a clean promotion path.

1. **Development (`delphi-dev`):**
   - Used by Xavi and the team for active feature development.
   - Auto-deploys from the `develop` branch.
   - Uses a shared MySQL instance with sanitized seed data.
   - Logging: Debug level.

2. **Staging (`delphi-staging`):**
   - A mirror of production. Used for QA and stakeholder demos.
   - Deploys from the `release` branch.
   - Connected to a sandbox version of the external partner's API.
   - Used for the "Security Audit" phase before production push.

3. **Production (`delphi-prod`):**
   - The live environment.
   - Strict access control (Devika and Arjun only).
   - Quarterly release cycle.
   - High-availability MySQL cluster with daily automated backups.

### Infrastructure Pipeline
- **CI/CD:** GitHub Actions handles the pipeline. A merge to `main` triggers a series of tests; upon success, it triggers a Heroku pipeline promotion.
- **Caching:** Redis is used for Sidekiq (job queueing) and for caching expensive search facets.
- **Monitoring:** New Relic is installed for APM (Application Performance Monitoring) to track request latency and database bottlenecks.

---

## 7. TESTING STRATEGY

Given the "audit-critical" nature of real estate transactions, the testing strategy is exhaustive.

### Unit Testing
- **Framework:** RSpec.
- **Coverage Goal:** 80% of business logic.
- **Focus:** Every "Command" in the CQRS architecture must have a unit test to ensure the event is generated correctly. Example: Testing that updating a price produces a `PriceChanged` event.

### Integration Testing
- **Framework:** RSpec Request Specs.
- **Focus:** Validating the API endpoints. Every endpoint defined in Section 4 has a corresponding set of tests verifying:
  - Correct HTTP status codes.
  - Schema validation of JSON responses.
  - Permission checks (e.g., an Agent cannot toggle a Feature Flag).

### End-to-End (E2E) Testing
- **Framework:** Cypress.
- **Focus:** Critical user journeys.
  - **Scenario 1:** A user logs in, searches for a property using facets, and updates the status.
  - **Scenario 2:** An admin creates an automation rule and verifies it triggers an email.
  - **Scenario 3:** A user switches the language to Arabic and verifies the UI flips to RTL.

### Regulatory Audit Testing
Before each quarterly release, a "Data Integrity Test" is run. This script replays the event store from day zero to ensure that the current state of the Read Models matches the results of the event stream.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Scope creep from stakeholders adding 'small' features | High | Medium | Hire a dedicated contractor to increase capacity and reduce bus factor. |
| R2 | Competitor is 2 months ahead in the market | High | High | Document workarounds for competitor gaps; share these "winning points" with the team to prioritize high-value features. |
| R3 | Key team member on medical leave (6 weeks) | Actual | High | Redistribute tasks; Xavi (Junior Dev) to shadow Arjun (DevOps) to handle basic deployments. |
| R4 | Technical debt: Hardcoded config in 40+ files | High | Medium | Implement a `Config` service; migrate hardcoded values to Heroku Env Vars during the next two sprints. |
| R5 | External API downtime/instability | Medium | High | Implement a robust "Retry with Exponential Backoff" strategy and a circuit breaker pattern. |

**Probability/Impact Matrix:**
- **High/High:** Immediate priority (R2).
- **High/Medium:** Planned mitigation (R1, R4).
- **Actual/High:** Active management (R3).

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project follows a linear-agile hybrid approach, culminating in a Production Launch on August 15, 2025.

### Phase 1: Foundation & API Integration (Jan 2025 - Mar 2025)
- **Focus:** Core monolith setup, MySQL schema, and the External API Adapter.
- **Dependencies:** Access to Partner API documentation and sandbox keys.
- **Key Milestone:** Successful "First Sync" of data.

### Phase 2: Feature Development (Apr 2025 - Jun 2025)
- **Focus:** Localization, Advanced Search, and Workflow Automation.
- **Dependencies:** UX research completion from Dina Nakamura.
- **Key Milestone:** Feature Complete for Priority 1-3.

### Phase 3: Polishing & A/B Framework (Jul 2025 - Aug 2025)
- **Focus:** Feature Flags, A/B Testing, and final UI polish.
- **Dependencies:** Stable build of search and automation.
- **Milestone 1: Production Launch (Target: 2025-08-15)**

### Phase 4: Post-Launch Validation (Sep 2025 - Dec 2025)
- **Focus:** Security audits and performance tuning.
- **Milestone 2: Security Audit Passed (Target: 2025-10-15)**
- **Milestone 3: Performance Benchmarks Met (Target: 2025-12-15)**

---

## 10. MEETING NOTES

### Meeting 1: Sprint Kickoff - "The Monolith Decision"
**Date:** 2023-11-02 | **Attendees:** Devika, Arjun, Dina, Xavi
**Discussion:**
The team debated whether to move to a microservices architecture given the "real-time" requirements of the collaborative editing feature. Devika asserted that with a $400k budget, the overhead of Kubernetes or separate service repos would be fatal to the timeline.
**Decisions:**
- Stick to Ruby on Rails monolith.
- Use CQRS for the "Financials" domain to ensure auditability without the complexity of a full microservice.
- Use Heroku for managed infrastructure to keep the DevOps load light for Arjun.
**Action Items:**
- [Arjun] Setup Heroku pipelines and MySQL instance. (Due: Nov 10)
- [Xavi] Draft initial `Property` and `Event` models. (Due: Nov 12)

### Meeting 2: UX Review - "Localization & RTL"
**Date:** 2023-12-15 | **Attendees:** Devika, Dina, Xavi
**Discussion:**
Dina presented research showing that Arabic users struggle with standard "flipped" layouts if the icons are not also mirrored. Xavi expressed concern about the effort to maintain 12 different language files.
**Decisions:**
- Implement a database-backed translation system to allow on-the-fly edits.
- Use a CSS utility class `.rtl-flip` for icons that need mirroring.
- Prioritize English, Spanish, and Arabic first as a "pilot" group.
**Action Items:**
- [Dina] Provide a list of all UI strings requiring translation. (Due: Jan 5)
- [Xavi] Implement the `Locale` and `Translation` tables. (Due: Jan 15)

### Meeting 3: Risk Mitigation - "The Competitor Gap"
**Date:** 2024-02-10 | **Attendees:** Devika, Arjun, Dina, Xavi
**Discussion:**
Devika reported that a competitor has launched their beta and is roughly 2 months ahead of Delphi. The team felt discouraged. Devika emphasized that the competitor lacks a visual rule builder and robust localization.
**Decisions:**
- Shift focus to "Feature 3 (Workflow Automation)" to create a unique selling point.
- Document exactly where the competitor's UX fails (via Dina's research) and ensure Delphi solves those specific pain points.
- Hire a contract developer for 3 months to help Xavi with the "grunt work" of migrating hardcoded configs.
**Action Items:**
- [Devika] Finalize contract with the external developer. (Due: Feb 20)
- [Dina] Create a "Competitor Gap Analysis" document. (Due: Feb 25)

---

## 11. BUDGET BREAKDOWN

The total budget is **$400,000**. This is a focused budget requiring strict adherence to avoid overruns.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $300,000 | 6-person core team + 1 temporary contractor. |
| **Infrastructure** | 10% | $40,000 | Heroku (Production, Staging, Dev), Managed MySQL, Redis, New Relic. |
| **Tools & Licenses** | 5% | $20,000 | GitHub Enterprise, Figma, Jira, Slack, Localized Testing Tools. |
| **Contingency** | 10% | $40,000 | Reserved for emergency contractor scaling or API overage costs. |
| **Total** | **100%** | **$400,000** | |

---

## 12. APPENDICES

### Appendix A: Hardcoded Configuration Migration Plan
As noted in the Risk Register, there are currently hardcoded values in 40+ files (e.g., API keys, timeout settings, partner endpoints).
**Migration Steps:**
1. **Audit:** Xavi will run a global grep search for `ENV['` and hardcoded strings like `http://api.partner.com`.
2. **Centralization:** All values will be moved to a `config/settings.yml` file.
3. **Heroku Integration:** The `settings.yml` will be wired to Heroku Environment Variables using the `config` gem.
4. **Verification:** A script will be run to ensure no file contains a raw IP address or API secret before the Oct 15 security audit.

### Appendix B: Event Sourcing Payload Schema
To ensure the audit trail is consistent, all events in the `events` table must follow a strict JSON schema:
```json
{
  "version": "1.0",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "actor": {
    "user_id": "UUID",
    "role": "String"
  },
  "change": {
    "field": "String",
    "previous_value": "Mixed",
    "new_value": "Mixed"
  },
  "metadata": {
    "request_id": "String",
    "ip_address": "String"
  }
}
```
This schema allows the "Projector" to accurately reconstruct the state of any property at any specific point in time by replaying events up to a certain timestamp.