Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. To maintain professional standards and technical depth, it follows a strict engineering template.

***

# PROJECT SPECIFICATION: WAYFINDER
**Document Version:** 1.0.4  
**Status:** Draft for Internal Review  
**Date:** October 24, 2024  
**Company:** Iron Bay Technologies  
**Project Lead:** Wren Fischer (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Wayfinder represents a strategic pivot for Iron Bay Technologies. The initiative centers on the development of a robust API Gateway and the migration of core legacy services into a modern micro-modular architecture within the education sector. While the codebase remains a "clean monolith" for operational simplicity, the project is designed to decouple the customer-facing interface from the internal business logic, enabling high-scale integration for enterprise partners.

### 1.2 Business Justification
The primary driver for Wayfinder is a high-value enterprise client in the global education space. This client has committed to a recurring annual contract value (ACV) of $2,000,000, provided Iron Bay can deliver the specified API capabilities, localization, and security standards. 

Currently, the legacy system is incapable of supporting multi-tenant localization or external API consumption. The cost of maintaining the legacy infrastructure is rising, and the inability to provide a sandbox environment for the enterprise client's developers is a significant friction point that threatens the $2M revenue stream.

### 1.3 ROI Projection
With a dedicated budget of $1.5M for the development phase, the ROI is projected as follows:
- **Direct Revenue:** $2M annual recurring revenue (ARR) starting from the launch date.
- **Operational Efficiency:** A target reduction of 35% in cost per transaction. Currently, the legacy system incurs high overhead due to inefficient query patterns and lack of a caching layer at the gateway level.
- **Market Expansion:** By implementing localization for 12 languages, Iron Bay opens the door to the EMEA and APAC education markets, potentially increasing the TAM (Total Addressable Market) by 400% over the next 24 months.
- **Break-Even Point:** The project is expected to break even within 9 months post-launch, accounting for the $1.5M CAPEX investment and the ongoing OPEX of the Heroku environment.

### 1.4 Strategic Alignment
Wayfinder aligns with the company's goal of moving from a "tool-based" offering to a "platform-based" offering. By providing a versioned API and a developer sandbox, Iron Bay transitions from a software vendor to an infrastructure provider for educational institutions.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
The "Wayfinder" architecture is defined as a **Clean Monolith**. We are deliberately avoiding a distributed microservices mesh to prevent "distributed monolith" syndrome. Instead, we utilize clear module boundaries within a Ruby on Rails framework, ensuring that the API Gateway logic is logically separated from the core business domains.

**Core Stack:**
- **Framework:** Ruby on Rails 7.1 (API-only mode for the gateway layer).
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons).
- **Hosting:** Heroku (Dyno-based scaling).
- **Cache:** Redis (for session management and API rate limiting).
- **Search:** Elasticsearch (for faceted filtering).

### 2.2 System Diagram (ASCII Description)
The following describes the request flow from the external client to the database:

```text
[ External Client ]  ---> [ HTTPS / TLS 1.3 ]
                                  |
                                  v
                      +-------------------------+
                      |    API GATEWAY LAYER     |
                      | (Auth, Versioning, Rate  | <--- [ Redis Cache ]
                      |  Limiting, Localization) |
                      +-------------------------+
                                  |
                                  v
                      +-------------------------+
                      |   BUSINESS LOGIC LAYER   |
                      | (Modular Rails Services)|
                      | [Edu-Core] [User-Mgmt]  |
                      +-------------------------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
            v                     v                     v
    [ MySQL Database ]     [ Elasticsearch ]     [ External Auth ]
    (Relational Data)      (Full-Text Search)     (Hardware Keys)
```

### 2.3 Data Access Layer
A critical architectural detail is the "Performance Exception" rule. While the ActiveRecord ORM is the standard, 30% of the current codebase utilizes raw SQL for complex reporting queries. Wayfinder will maintain this for performance but will wrap these queries in "Repository" classes to prevent raw SQL from leaking into the controllers, facilitating safer migrations.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/I18n)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Wayfinder must support 12 specific languages: English (US/UK), Spanish, French, German, Mandarin (Simplified), Japanese, Portuguese (Brazilian), Arabic, Korean, Hindi, Italian, and Dutch.

**Technical Requirements:**
1. **Translation Storage:** Use the `i18n` gem combined with a database-backed translation table for dynamic content (e.g., course descriptions) and YAML files for static UI elements.
2. **Locale Detection:** The API Gateway must detect locale via the `Accept-Language` header or a `?locale=` query parameter.
3. **UTF-8 Compliance:** All MySQL tables must be migrated to `utf8mb4` to support complex characters in Mandarin and Arabic.
4. **Right-to-Left (RTL) Support:** The API must return a `direction: "rtl"` flag in the response metadata for Arabic.

**Acceptance Criteria:**
- API responses for the same resource differ correctly based on the locale header.
- All 12 languages are loaded without crashing the application.
- Dynamic content updates in the admin panel reflect in the API in real-time.

### 3.2 Customer-Facing API with Versioning & Sandbox
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
A public-facing API allowing the enterprise client to integrate their own dashboards with Wayfinder data. This includes a "Sandbox" environment where the client can test calls without affecting production data.

**Technical Requirements:**
1. **Versioning Strategy:** URI-based versioning (e.g., `/v1/courses`, `/v2/courses`).
2. **Sandbox Environment:** A mirrored Heroku app (`wayfinder-sandbox.herokuapp.com`) using a sanitized snapshot of production data.
3. **API Key Management:** Implement an `ApiKey` table with scopes (read, write, admin) and expiration dates.
4. **Rate Limiting:** 1,000 requests per minute per API key, enforced via Redis.

**Acceptance Criteria:**
- Client can generate a Sandbox key and receive a `200 OK` response.
- Requests to `/v1/` remain stable while `/v2/` introduces breaking changes.
- Sandbox data is isolated from production.

### 3.3 A/B Testing Framework (Integrated Feature Flags)
**Priority:** High | **Status:** Not Started

**Description:**
A system to toggle features on/off for specific user segments and perform A/B tests to determine the efficacy of new educational modules.

**Technical Requirements:**
1. **Feature Flag Engine:** Implementation of a `FeatureToggle` model linked to `User` and `Organization`.
2. **Weighting Logic:** The system must support "Percentage Rollouts" (e.g., 10% of users see Feature A, 90% see Feature B).
3. **Telemetry:** Integration with the logging system to track which version of a feature a user interacted with.
4. **Consistency:** A user must stay in the same bucket (A or B) across sessions using a deterministic hash of their `user_id`.

**Acceptance Criteria:**
- Ability to toggle a feature for a specific user via the admin console without a deployment.
- Statistical data showing the split of users between A and B variants.

### 3.4 Advanced Search with Faceted Filtering
**Priority:** High | **Status:** In Design

**Description:**
A high-performance search engine for educational content, supporting full-text indexing and facets (e.g., Filter by Grade Level, Subject, Language).

**Technical Requirements:**
1. **Elasticsearch Integration:** Syncing MySQL records to an Elasticsearch index using the `searchkick` gem.
2. **Faceted Indexing:** Creating "aggregations" for common fields: `category`, `difficulty_level`, and `author`.
3. **Full-Text Scoring:** Implementation of "boosting" where matches in the "Title" field are weighted higher than matches in the "Description" field.
4. **Asynchronous Indexing:** Use Sidekiq to update the search index to avoid blocking the main request thread.

**Acceptance Criteria:**
- Search results return in < 200ms for queries against 1M+ records.
- Facets update dynamically based on the search query.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Blocked

**Description:**
Enhanced security for administrative and high-privilege accounts, moving beyond SMS to TOTP (Time-based One-Time Password) and WebAuthn (Hardware keys like YubiKey).

**Technical Requirements:**
1. **WebAuthn API:** Integration of a WebAuthn library to handle public key registration and challenge-response.
2. **TOTP Fallback:** Support for Google Authenticator/Authy using a shared secret stored encrypted in MySQL.
3. **Recovery Codes:** Generation of 10 one-time use recovery codes upon 2FA activation.
4. **Session Hardening:** 2FA-verified sessions must have a shorter TTL (Time-to-Live).

**Acceptance Criteria:**
- User cannot access `/admin` without a successful 2FA challenge.
- Successful registration and authentication using a physical YubiKey.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints return JSON. Base URL for Production: `api.ironbay.edu/v1`. Base URL for Sandbox: `sandbox-api.ironbay.edu/v1`.

### 4.1 Authentication & Keys
**Endpoint:** `POST /auth/token`  
**Description:** Exchanges API keys for a short-lived JWT.  
**Request:**
```json
{
  "api_key": "way_live_abc123",
  "secret": "sk_secret_456"
}
```
**Response:** `200 OK`
```json
{
  "token": "eyJhbGci... ",
  "expires_at": "2025-10-25T12:00:00Z"
}
```

### 4.2 Course Retrieval (Localized)
**Endpoint:** `GET /courses/{id}`  
**Description:** Retrieves detailed course information based on the `Accept-Language` header.  
**Request Header:** `Accept-Language: es-ES`  
**Response:** `200 OK`
```json
{
  "id": "crs_99",
  "title": "Introducción a la Programación",
  "description": "Aprenda los conceptos básicos...",
  "locale": "es-ES"
}
```

### 4.3 Course Creation
**Endpoint:** `POST /courses`  
**Description:** Creates a new educational module.  
**Request:**
```json
{
  "title": "Advanced Calculus",
  "category": "Mathematics",
  "content": "...",
  "tags": ["STEM", "College"]
}
```
**Response:** `201 Created`

### 4.4 Faceted Search
**Endpoint:** `GET /search`  
**Description:** Performs a full-text search with filters.  
**Params:** `q=calculus&grade=12&subject=math`  
**Response:** `200 OK`
```json
{
  "results": [...],
  "facets": {
    "grade": { "11": 10, "12": 45, "13": 5 },
    "subject": { "math": 60, "physics": 12 }
  }
}
```

### 4.5 User Profile Update
**Endpoint:** `PATCH /users/me`  
**Description:** Updates the authenticated user's profile.  
**Request:**
```json
{
  "preferred_language": "fr-FR",
  "timezone": "Europe/Paris"
}
```
**Response:** `200 OK`

### 4.6 2FA Registration
**Endpoint:** `POST /auth/2fa/register`  
**Description:** Initiates the registration of a hardware key.  
**Request:**
```json
{
  "credential_id": "...",
  "public_key": "..."
}
```
**Response:** `201 Created`

### 4.7 Feature Flag Query
**Endpoint:** `GET /features`  
**Description:** Checks which feature flags are active for the current user (for frontend rendering).  
**Response:** `200 OK`
```json
{
  "flags": {
    "new_dashboard_v2": true,
    "advanced_reporting": false
  }
}
```

### 4.8 Sandbox Data Reset
**Endpoint:** `POST /sandbox/reset`  
**Description:** Wipes and restores the sandbox environment to the last snapshot. (Admin only).  
**Response:** `202 Accepted`

---

## 5. DATABASE SCHEMA

The system utilizes MySQL 8.0. To handle the raw SQL performance requirement, we use an indexing strategy optimized for read-heavy educational queries.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email`, `password_digest` | Core user identity. |
| `organizations` | `org_id` | - | `org_name`, `tier` | Enterprise clients (e.g., the $2M client). |
| `user_org_map` | `map_id` | `user_id`, `org_id` | `role` | Links users to organizations. |
| `courses` | `course_id` | `creator_id` | `slug`, `status` | Main educational content. |
| `translations` | `trans_id` | `course_id` | `locale`, `translated_text` | L10n storage for courses. |
| `api_keys` | `key_id` | `org_id` | `key_hash`, `scope`, `last_used` | Gateway access control. |
| `feature_flags` | `flag_id` | - | `flag_name`, `is_enabled` | Global toggle for features. |
| `flag_overrides` | `override_id` | `flag_id`, `user_id` | `value` | User-specific A/B testing overrides. |
| `search_indices` | `index_id` | `course_id` | `vector_data`, `token_set` | Cache for ES synchronization. |
| `auth_methods` | `method_id` | `user_id` | `type` (TOTP/WebAuthn), `secret` | 2FA credential storage. |

### 5.2 Relationships
- **One-to-Many:** `organizations` $\rightarrow$ `api_keys` (An org can have multiple keys for different services).
- **One-to-Many:** `courses` $\rightarrow$ `translations` (A course has one translation per supported language).
- **Many-to-Many:** `users` $\leftrightarrow$ `organizations` (via `user_org_map`).
- **One-to-Many:** `users` $\rightarrow$ `auth_methods` (A user can have both a YubiKey and an App-based TOTP).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We utilize a three-tier environment strategy hosted on Heroku to ensure stability and regulatory alignment.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and unit testing.
- **Configuration:** 2 Standard Dynos, shared MySQL instance.
- **Deployment:** Continuous integration (CI) via GitHub Actions on every push to `develop` branch.
- **Data:** Seeded with synthetic "dummy" data.

#### 6.1.2 Staging (`staging`)
- **Purpose:** QA validation and User Acceptance Testing (UAT).
- **Configuration:** 4 Standard Dynos, mirrored production MySQL schema.
- **Deployment:** Deployment occurs on a weekly basis from `develop` $\rightarrow$ `staging`.
- **Data:** Sanitized production snapshot updated monthly.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live enterprise client traffic.
- **Configuration:** 16 Performance-M Dynos, High-Availability MySQL Cluster, Redis Enterprise.
- **Deployment:** Quarterly releases. This slow cadence is mandatory to align with the education industry's regulatory review cycles.
- **Data:** Encrypted at rest; strict access control via VPN.

### 6.2 Infrastructure Constraints
- **Deployment Window:** Updates to Production occur on the first Sunday of the quarter at 02:00 UTC.
- **Backups:** Automated daily snapshots with 30-day retention.
- **Monitoring:** New Relic for APM (Application Performance Monitoring) and LogDNA for centralized logging.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** RSpec.
- **Requirement:** 80% code coverage for all new modules.
- **Focus:** Testing business logic in isolation. Mocks and stubs are used for external API calls to ensure the test suite remains fast (< 5 minutes).

### 7.2 Integration Testing
- **Framework:** RSpec Request Specs.
- **Focus:** Testing the interaction between the API Gateway and the Business Logic layer.
- **Key Scenarios:** 
    - Verify that an expired API key returns a `401 Unauthorized`.
    - Verify that a request for `locale=ja` returns Japanese text from the `translations` table.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Cypress.
- **Focus:** Critical user journeys from the perspective of the enterprise client.
- **Scenario:** "Client generates API key $\rightarrow$ makes a search request $\rightarrow$ receives faceted results $\rightarrow$ updates course title."

### 7.4 QA Process (Kira Jensen's Workflow)
1. **Ticket Assignment:** Feature is marked "Ready for QA" in Jira.
2. **Smoke Test:** Basic functionality check in Staging.
3. **Edge Case Testing:** Testing null values, oversized payloads, and unauthorized access attempts.
4. **Regression:** Running the full Cypress suite to ensure no legacy features broke.
5. **Sign-off:** Formal approval in Slack/Jira before the quarterly release merge.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotating out of role | High | High | Hire a specialized contractor to expand the knowledge base and reduce "bus factor." |
| **R-02** | Key Architect leaving in 3 months | Medium | High | Mandatory documentation of all architectural decisions; pair programming sessions for knowledge transfer. |
| **R-03** | Raw SQL Technical Debt | High | Medium | Encapsulate all raw SQL in Repository patterns; implement a "Migration Safety Checklist" for DB changes. |
| **R-04** | External Dependency Lag | High | Medium | (Current Blocker) Negotiate a "Minimum Viable Deliverable" from the other team to unblock development. |
| **R-05** | Localization Scope Creep | Medium | Low | Strict adherence to the 12-language list; no new languages added until V2. |

### 8.1 Probability/Impact Matrix
- **Critical (High Prob / High Impact):** R-01, R-04. These require daily monitoring by Wren Fischer.
- **Major (Med Prob / High Impact):** R-02. Requires a structured transition plan.
- **Manageable (High Prob / Med Impact):** R-03. Handled via code review and linting.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Oct 2024 - Jan 2025)
- **Focus:** API Gateway setup, Database migration to `utf8mb4`, and the initial API versioning logic.
- **Dependency:** Must resolve the 3-week lag from the external team before completing the Auth module.

### 9.2 Phase 2: Localization & Search (Jan 2025 - Apr 2025)
- **Focus:** Implementation of the 12-language translation system and the Elasticsearch cluster.
- **Milestone 1:** **External Beta (2025-04-15)**. Delivery of a working API and Search to 10 pilot users from the enterprise client.

### 9.3 Phase 3: Security & Experimentation (Apr 2025 - Aug 2025)
- **Focus:** 2FA/Hardware key integration and the A/B testing framework.
- **Milestone 2:** **Internal Alpha (2025-06-15)**. Full feature set available for internal Iron Bay staff.
- **Milestone 3:** **Performance Benchmarks (2025-08-15)**. Verification that cost per transaction is reduced by 35%.

### 9.4 Phase 4: Hardening & Launch (Aug 2025 - Oct 2025)
- **Focus:** Final QA audits, security hardening, and documentation.
- **Final Launch:** Targeted for the Q4 regulatory cycle.

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff & Technical Debt Audit
**Date:** 2024-10-10  
**Attendees:** Wren Fischer, Nia Moreau, Kira Jensen, Eshan Kim  
**Discussion:**
- Wren emphasized the $2M client's expectations. The priority is the API Gateway.
- Nia raised a red flag regarding the raw SQL in the legacy system. She noted that 30% of the queries bypass ActiveRecord, which makes schema migrations dangerous.
- Decision: All raw SQL must be moved into "Query Objects" to isolate the risk.
- **Action Items:**
    - [Nia] Create a catalog of all raw SQL queries. (Due: 2024-10-20)
    - [Wren] Finalize the contractor contract to mitigate the sponsor-rotation risk. (Due: 2024-10-15)

### Meeting 2: Localization Strategy Sync
**Date:** 2024-11-02  
**Attendees:** Wren Fischer, Nia Moreau, Kira Jensen  
**Discussion:**
- Discussion on whether to use a 3rd party translation service or in-house DB storage.
- Nia argues for DB storage for course content to allow the client to edit translations via the admin panel.
- Kira expressed concern about the QA load for 12 languages. 
- Decision: Use a hybrid approach—YAML for static UI, MySQL for dynamic content. Use a specialized contractor for linguistic validation.
- **Action Items:**
    - [Nia] Draft the `translations` table schema. (Due: 2024-11-10)
    - [Kira] Define the "Localization Test Matrix" for the 12 languages. (Due: 2024-11-15)

### Meeting 3: Blocker Resolution & Sandbox Planning
**Date:** 2024-12-05  
**Attendees:** Wren Fischer, Nia Moreau, Eshan Kim  
**Discussion:**
- The external team is now 3 weeks behind on the Identity Provider (IdP) deliverable.
- Eshan suggests creating a "Mock IdP" to allow the Wayfinder team to continue building the API Gateway.
- Decision: Proceed with the Mock IdP. This allows the team to build the Sandbox environment without waiting for the external team.
- **Action Items:**
    - [Eshan] Deploy the Mock IdP to the `dev` environment. (Due: 2024-12-10)
    - [Wren] Send a formal escalation email to the other team's lead. (Due: 2024-12-06)

---

## 11. BUDGET BREAKDOWN

The total project budget is **$1,500,000**. This is a well-funded initiative allowing for high-quality QA and DevOps overhead.

### 11.1 Personnel ($1,100,000)
- **Full-time Salaries (6 members):** $850,000 (Including Wren, Nia, Kira, Eshan, and two additional mid-level engineers).
- **External Contractor (Risk Mitigation):** $150,000 (Specialist for architectural documentation and bus-factor reduction).
- **Linguistic QA Contractors:** $100,000 (Expert translators for the 12 required languages).

### 11.2 Infrastructure ($180,000)
- **Heroku Performance Dynos:** $60,000 (Scaling for Prod, Staging, and Sandbox).
- **Managed MySQL & Redis Cluster:** $50,000.
- **Elasticsearch Managed Service:** $40,000.
- **Security Tooling (Snyk/Datadog):** $30,000.

### 11.3 Tools & Software ($70,000)
- **IDE Licenses & Collaboration Tools:** $20,000.
- **API Testing Tools (Postman Enterprise/Insomnia):** $10,000.
- **Hardware Keys (YubiKeys for team/beta):** $10,000.
- **Cloud-based QA Automation Licenses:** $30,000.

### 11.4 Contingency Fund ($150,000)
- **Emergency Buffer:** $150,000 (Reserved for unexpected infrastructure spikes or extended contractor needs if the key architect's exit is accelerated).

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Safety Protocol
Given that 30% of the ORM is bypassed, the following protocol is mandatory for any database change:
1. **Shadow Migration:** Run the migration on a copy of production data in the `staging` environment.
2. **Query Audit:** Use the "Raw SQL Catalog" (created by Nia) to identify every query that touches the modified table.
3. **Verification:** Manually execute the raw SQL queries against the migrated schema to ensure no `column not found` errors occur.
4. **Rollback Plan:** Every migration must include a tested `down` method that restores the previous schema state.

### Appendix B: Hardware Key (WebAuthn) Implementation Flow
The 2FA flow for hardware keys follows the FIDO2 standard:
1. **Challenge:** The server generates a random challenge and sends it to the client.
2. **Sign:** The user touches the YubiKey; the key signs the challenge using the private key stored on the hardware.
3. **Verify:** The server receives the signature and verifies it using the stored public key.
4. **Session:** Upon successful verification, the session is upgraded to `auth_level: 2` and a secure cookie is set.