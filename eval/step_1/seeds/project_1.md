Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Technical Specification Document (TSD). It is designed to be the "Single Source of Truth" for the development team at Hearthstone Software.

***

# PROJECT SPECIFICATION: CANOPY
**Document Version:** 1.0.4  
**Last Updated:** October 24, 2025  
**Status:** Active / In-Development  
**Project Lead:** Jasper Vasquez-Okafor  
**Classification:** Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Canopy" is a strategic cost-reduction and operational efficiency initiative spearheaded by Hearthstone Software. Currently, the company’s renewable energy division relies on four disparate internal tools to manage project lifecycles, site telemetry, workforce scheduling, and regulatory reporting. These tools—legacy systems developed over the last decade—create significant data silos, require four separate authentication flows, and incur overlapping licensing fees. 

The primary driver for Canopy is the consolidation of these redundant systems into a single, unified mobile application. By eliminating the overhead of maintaining four separate codebases and reducing the friction of data entry for field engineers, Canopy will drastically lower the Total Cost of Ownership (TCO) of our internal software suite.

### 1.2 Project Objectives
The objective is to deliver a high-performance mobile application that streamlines the workflow of renewable energy technicians and managers. The app will serve as the primary interface for field operations, integrating secure authentication, automated workflows, and multi-language support to accommodate global operations.

### 1.3 ROI Projection and Success Metrics
The financial justification for Canopy is rooted in both cost avoidance and revenue acceleration.
- **Direct Cost Savings:** Elimination of three redundant SaaS licenses and legacy server maintenance is projected to save $120,000 annually.
- **Operational Efficiency:** Reducing the "administrative burden" on field engineers (estimated at 4 hours per week per person) is projected to increase site deployment speed by 15%.
- **Revenue Goal:** The product is expected to facilitate an additional **$500,000 in new revenue** within 12 months of launch, attributed to the ability to scale operations faster and onboard new clients with a professional, unified toolset.
- **Adoption Metric:** Success will be measured by an **80% feature adoption rate** among the initial pilot user group (50 regional leads).

### 1.4 Budget Overview
The project is operating on a modest but focused budget of **$400,000**. This budget covers the personnel costs for a lean team and the necessary AWS infrastructure. While the budget is tight, it is workable provided the scope remains disciplined and the "modular monolith" approach prevents over-engineering in the early phases.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Canopy utilizes a **Modular Monolith** architecture. This approach allows the team to maintain a single deployable unit (reducing CI/CD complexity) while enforcing strict logical boundaries between modules (Authentication, Workflow, Localization, Search). This ensures that as the application grows, specific modules can be extracted into independent microservices without requiring a full system rewrite.

### 2.2 Technology Stack
- **Backend:** Python 3.11 / Django 4.2 (Long Term Support)
- **Database:** PostgreSQL 15 (Primary relational store)
- **Caching/Queue:** Redis 7.0 (Used for session management and Celery task queuing)
- **Frontend:** React Native (Cross-platform iOS/Android)
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless compute.
- **CI/CD:** GitHub Actions for automated testing and deployment.

### 2.3 High-Level Architecture Diagram (ASCII)

```text
[ Mobile Client (React Native) ]
           |
           | HTTPS / REST API / WebSocket
           v
[ AWS Application Load Balancer ]
           |
           v
[ AWS ECS Fargate (Django App Containers) ]
    |               |               |
    | (SQL)         | (Cache/Queue) | (Auth)
    v               v               v
[ PostgreSQL ]  [ Redis ]  [ SAML/OIDC Providers ]
 (User Data,     (Task Queue,    (Azure AD, Okta,
  Workflows,      Session,        Google Workspace)
  Localization)    Search Cache)
```

### 2.4 Deployment Strategy
The team employs a **Blue-Green Deployment** strategy. 
1. **Blue Environment:** The current stable production version.
2. **Green Environment:** The new version being deployed.
Traffic is shifted from Blue to Green via the ALB (Application Load Balancer) only after health checks pass. If a regression is detected, traffic is instantly rerouted back to Blue.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** High | **Status:** In Progress
*   **Description:** To secure sensitive renewable energy grid data, Canopy requires robust 2FA. Beyond standard TOTP (Time-based One-Time Password) apps, the system must support FIDO2/WebAuthn hardware keys (e.g., YubiKey).
*   **Functional Requirements:**
    *   Users must be able to register multiple 2FA methods.
    *   Hardware key authentication must be handled via the browser-based WebAuthn API for registration and verified via the mobile app.
    *   Recovery codes (10 unique 8-character strings) must be generated upon 2FA activation.
    *   The system must support "Remember this device" for 30 days using a secure, encrypted device token stored in the mobile secure enclave.
*   **Technical Implementation:**
    *   Use `django-two-factor-auth` as the base library.
    *   Implement a custom `WebAuthn` provider to handle the challenge/response handshake with hardware keys.
    *   The backend will store public keys in a `UserDevice` table linked to the User ID.
*   **User Flow:**
    1. User enters username/password.
    2. Server validates credentials and requests 2FA.
    3. User selects "Hardware Key" $\rightarrow$ App triggers biometric/USB-C prompt $\rightarrow$ Key signs the challenge $\rightarrow$ Server validates signature $\rightarrow$ Access granted.

### 3.2 Workflow Automation Engine with Visual Rule Builder
*   **Priority:** Medium | **Status:** Blocked (Pending Budget Approval for Logic-Engine Tool)
*   **Description:** A low-code engine allowing managers to create "If-This-Then-That" (IFTTT) rules for field operations (e.g., "If site voltage drops below 200V, notify the regional lead and create a priority ticket").
*   **Functional Requirements:**
    *   **Visual Builder:** A drag-and-drop interface where users can link "Triggers" to "Actions."
    *   **Triggers:** System events (Telemetry alerts, User status changes, Schedule deadlines).
    *   **Actions:** Email notifications, API calls to external tools, updating database fields.
    *   **Validation:** The engine must validate that a rule does not create an infinite loop before saving.
*   **Technical Implementation:**
    *   The engine will use a Directed Acyclic Graph (DAG) structure stored in JSONB format in PostgreSQL.
    *   A Celery worker will monitor a "Rule Execution Queue," evaluating incoming events against active rules.
    *   The visual builder will be implemented using `React Flow` on the frontend, translating visual nodes into a JSON schema.
*   **Constraint:** This feature is currently blocked due to the pending approval of a specialized logic-modeling license ($12,000 USD).

### 3.3 Localization and Internationalization (L10n/I18n)
*   **Priority:** High | **Status:** In Progress
*   **Description:** Canopy is deployed globally. The application must support 12 languages (English, Spanish, French, German, Mandarin, Japanese, Portuguese, Hindi, Arabic, Dutch, Italian, and Korean).
*   **Functional Requirements:**
    *   Dynamic language switching without requiring an app restart.
    *   Support for Right-to-Left (RTL) layouts for Arabic.
    *   Regional formatting for dates, currency (for cost-reduction tracking), and measurement units (Metric vs. Imperial).
    *   Translation management system (TMS) integration for external translators to update strings.
*   **Technical Implementation:**
    *   **Backend:** Use Django's `i18n` framework and `gettext`. All translatable strings must be wrapped in `_()`.
    *   **Frontend:** Use `i18next` for React Native. Translation files will be fetched from a Redis cache for high performance.
    *   **Database:** Create a `Translation` table to handle dynamic content (e.g., site descriptions) using a key-value pair mapping for each language code.

### 3.4 SSO Integration (SAML and OIDC)
*   **Priority:** Medium | **Status:** In Progress
*   **Description:** To consolidate 4 tools, Canopy must act as the central identity hub. It must integrate with existing enterprise identity providers (IdPs).
*   **Functional Requirements:**
    *   Support for SAML 2.0 (Security Assertion Markup Language) for legacy corporate AD.
    *   Support for OIDC (OpenID Connect) for modern cloud-based identity providers (Okta, Azure AD).
    *   Just-in-Time (JIT) provisioning: Automatically create a Canopy user account upon the first successful SSO login based on IdP attributes.
    *   Attribute mapping: Map IdP groups (e.g., "Renewables-Admin") to Canopy internal roles.
*   **Technical Implementation:**
    *   Integration via `python-social-auth` and `django-allauth`.
    *   Metadata XML exchange for SAML configuration.
    *   JWT (JSON Web Tokens) will be used for session maintenance after the initial SSO handshake.

### 3.5 Advanced Search with Faceted Filtering
*   **Priority:** Low | **Status:** Blocked
*   **Description:** A "Nice to Have" feature allowing users to find specific equipment or reports across thousands of sites using full-text search and complex filters.
*   **Functional Requirements:**
    *   **Full-Text Indexing:** Ability to search across multiple fields (Site Name, Technician, Asset ID).
    *   **Faceted Filtering:** Sidebar filters (e.g., "Status: Pending," "Region: North America," "Voltage: 500V-1000V").
    *   **Auto-suggest:** Real-time suggestions as the user types.
*   **Technical Implementation:**
    *   Implementation of `pg_trgm` and `tsvector` within PostgreSQL for full-text capabilities.
    *   If performance degrades, a transition to an Elasticsearch or Algolia instance will be required.
    *   Frontend will use a debounced search input to minimize API calls.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer <JWT_TOKEN>` in the header.

### 4.1 Auth: User Login
- **Endpoint:** `POST /auth/login/`
- **Request:**
  ```json
  {
    "username": "arun_bw",
    "password": "secure_password_123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGci...",
    "refresh_token": "def456...",
    "requires_2fa": true,
    "two_factor_method": "hardware_key"
  }
  ```

### 4.2 Auth: 2FA Verify
- **Endpoint:** `POST /auth/verify-2fa/`
- **Request:**
  ```json
  {
    "token": "eyJhbGci...",
    "assertion": "base64_encoded_webauthn_signature"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "authenticated",
    "session_expiry": "2026-10-25T12:00:00Z"
  }
  ```

### 4.3 Workflow: Get Rules
- **Endpoint:** `GET /workflows/rules/`
- **Query Params:** `?region=EU&status=active`
- **Response (200 OK):**
  ```json
  [
    {
      "id": "rule_99",
      "name": "Voltage Drop Alert",
      "trigger": "telemetry_event",
      "action": "email_notification",
      "is_active": true
    }
  ]
  ```

### 4.4 Workflow: Create Rule
- **Endpoint:** `POST /workflows/rules/`
- **Request:**
  ```json
  {
    "name": "Critical Failure Alert",
    "logic_graph": { "nodes": [...], "edges": [...] },
    "priority": "high"
  }
  ```
- **Response (201 Created):**
  ```json
  { "id": "rule_101", "status": "pending_validation" }
  ```

### 4.5 Localization: User Preferences
- **Endpoint:** `PATCH /user/preferences/`
- **Request:**
  ```json
  {
    "language_code": "fr-FR",
    "timezone": "Europe/Paris",
    "unit_system": "metric"
  }
  ```
- **Response (200 OK):**
  ```json
  { "updated": true, "current_lang": "French" }
  ```

### 4.6 Localization: Fetch Strings
- **Endpoint:** `GET /i18n/strings/`
- **Query Params:** `?lang=es-ES&module=dashboard`
- **Response (200 OK):**
  ```json
  {
    "welcome_msg": "Bienvenido a Canopy",
    "logout_btn": "Cerrar sesión"
  }
  ```

### 4.7 Site: Get Site Details
- **Endpoint:** `GET /sites/{site_id}/`
- **Response (200 OK):**
  ```json
  {
    "site_id": "SITE-442",
    "location": "Scotland",
    "capacity_mw": 150,
    "status": "Operational"
  }
  ```

### 4.8 Site: Update Status
- **Endpoint:** `PUT /sites/{site_id}/status/`
- **Request:**
  ```json
  {
    "status": "Maintenance",
    "notes": "Scheduled turbine blade replacement"
  }
  ```
- **Response (200 OK):**
  ```json
  { "updated_at": "2026-10-24T10:15:00Z", "new_status": "Maintenance" }
  ```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15 instance. All tables utilize UUIDs as primary keys to prevent ID enumeration and facilitate future microservice migration.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | - | `email`, `password_hash`, `role_id` | Core user identity |
| `Roles` | `role_id` | - | `role_name`, `permissions_json` | RBAC permission sets |
| `UserDevices` | `device_id` | `user_id` | `device_type`, `public_key`, `last_used` | 2FA Hardware key mapping |
| `Sites` | `site_id` | - | `site_name`, `geo_location`, `capacity` | Renewable energy site data |
| `Assets` | `asset_id` | `site_id` | `asset_type`, `serial_number`, `install_date` | Hardware at sites |
| `Workflows` | `workflow_id` | `creator_id` | `name`, `dag_structure`, `is_active` | Automation rules |
| `WorkflowLogs` | `log_id` | `workflow_id` | `triggered_at`, `outcome`, `error_msg` | Execution history |
| `Translations` | `trans_id` | - | `lang_code`, `key`, `translated_text` | Dynamic localization |
| `UserPrefs` | `pref_id` | `user_id` | `lang_code`, `timezone`, `unit_pref` | User-specific settings |
| `SsoProviders` | `prov_id` | - | `provider_name`, `entity_id`, `sso_url` | SAML/OIDC config |

### 5.2 Relationships
- **Users $\rightarrow$ UserDevices:** One-to-Many (A user can have multiple backup hardware keys).
- **Users $\rightarrow$ UserPrefs:** One-to-One.
- **Sites $\rightarrow$ Assets:** One-to-Many (One site contains many turbines/panels).
- **Workflows $\rightarrow$ WorkflowLogs:** One-to-Many.
- **Roles $\rightarrow$ Users:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Canopy maintains three distinct environments to ensure stability and prevent production regressions.

#### 6.1.1 Development (Dev)
- **Purpose:** Individual developer testing and feature integration.
- **Infrastructure:** Small ECS Fargate instances, shared PostgreSQL instance.
- **Deployment:** Automatic deploy on push to `develop` branch.
- **Data:** Mocked data; refreshed weekly.

#### 6.1.2 Staging (Staging)
- **Purpose:** Final QA, UAT (User Acceptance Testing), and stakeholder demos.
- **Infrastructure:** Mirrored production specs (scaled down).
- **Deployment:** Deploy on merge to `release` branch.
- **Data:** Anonymized snapshot of production data.

#### 6.1.3 Production (Prod)
- **Purpose:** Live end-user environment.
- **Infrastructure:** High-availability ECS cluster across 3 Availability Zones (AZs).
- **Deployment:** Blue-Green via GitHub Actions and AWS CodeDeploy.
- **Monitoring:** AWS CloudWatch for logs and Prometheus/Grafana for performance metrics.

### 6.2 CI/CD Pipeline
The pipeline is managed via **GitHub Actions**.
1. **Lint/Test:** On every PR, run `flake8` for linting and `pytest` for unit tests.
2. **Build:** Create a Docker image $\rightarrow$ Push to AWS ECR (Elastic Container Registry).
3. **Deploy to Staging:** Update ECS service $\rightarrow$ Run integration tests.
4. **Promote to Prod:** Manual trigger by Project Lead $\rightarrow$ Blue-Green shift $\rightarrow$ Post-deploy smoke tests.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every backend function must have a corresponding test in the `/tests/unit` directory.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** Minimum 85% code coverage. Focus on business logic in the `services.py` layer.

### 7.2 Integration Testing
- **Approach:** Test the interaction between the Django API and the PostgreSQL/Redis layers.
- **Focus:** API endpoint contracts. Ensure that a `POST` to `/auth/login/` correctly triggers a session in Redis.
- **Tooling:** `Pytest-django` and `Postman/Newman` for automated collection runs.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulate real user journeys on the mobile app.
- **Scenarios:** 
    - Login $\rightarrow$ 2FA Challenge $\rightarrow$ Dashboard access.
    - Create Workflow $\rightarrow$ Trigger event $\rightarrow$ Verify notification.
- **Tooling:** `Detox` for React Native E2E testing.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Budget cut by 30% in next fiscal quarter | Medium | High | Hire a specialized contractor to reduce "bus factor" and ensure development continues if a full-time role is frozen. |
| **R-02** | Integration partner's API is buggy/undocumented | High | Medium | Establish a "hard date" for API stability. If unresolved by Milestone 2, de-scope the affected features. |
| **R-03** | Hardware key adoption is lower than expected | Low | Low | Provide fallback TOTP (Google Authenticator) options. |
| **R-04** | Modular monolith becomes too bloated | Medium | Medium | Strict enforcement of module boundaries; quarterly "refactor sprints." |

**Probability/Impact Matrix:**
- **Critical:** High Prob / High Impact (Immediate action required)
- **Major:** Medium Prob / High Impact (Active monitoring)
- **Moderate:** High Prob / Low Impact (Manageable via process)

---

## 9. TIMELINE

### 9.1 Phase Description

**Phase 1: Foundation (Oct 2025 – March 2026)**
- Setup AWS Infrastructure and CI/CD.
- Implement Core Auth (SAML/OIDC) and 2FA.
- Database schema finalization.
- *Dependency:* SSO Provider access must be granted.

**Phase 2: Core Feature Build (March 2026 – June 2026)**
- Localization engine implementation.
- Integration of site and asset management.
- **Milestone 1: Performance benchmarks met (2026-06-15).** (Target: <200ms API response time).

**Phase 3: Automation & Refinement (June 2026 – August 2026)**
- Development of Visual Rule Builder.
- Integration with partner APIs.
- **Milestone 2: Stakeholder demo and sign-off (2026-08-15).**

**Phase 4: QA & Launch (August 2026 – October 2026)**
- Full E2E testing cycle.
- Beta pilot with 50 users.
- Bug scrubbing and technical debt resolution.
- **Milestone 3: MVP feature-complete (2026-10-15).**

---

## 10. MEETING NOTES

*Note: All meetings recorded via Zoom/Teams. Transcripts available in the project archive. No one has watched the recordings.*

### Meeting 1: Kick-off & Stack Alignment
**Date:** 2025-10-10  
**Attendees:** Jasper Vasquez-Okafor, Arun Blackwood-Diallo, Gia Kowalski-Nair, Bram Lindqvist-Tanaka.
- **Discussion:** Jasper introduced the project goals. Arun questioned the use of microservices from day one.
- **Decision:** Agreed on a "Modular Monolith." We start as one app but separate the code into logical domains to allow for future splitting.
- **Action Item:** Arun to set up the initial GitHub organization and AWS environment.

### Meeting 2: Internationalization Strategy
**Date:** 2025-11-05  
**Attendees:** Jasper, Arun, Gia.
- **Discussion:** Gia (Consultant from Edinburgh) pointed out that the current localization plan missed Arabic RTL support. She emphasized that the field technicians in the Middle East region would find the app unusable without it.
- **Decision:** Added RTL layout support to the High Priority list. Use `i18next` for dynamic flipping.
- **Action Item:** Gia to provide a list of the 12 critical languages based on current site footprints.

### Meeting 3: The "Budget Blocker" Crisis
**Date:** 2026-01-12  
**Attendees:** Jasper, Arun, Bram.
- **Discussion:** The team realized the Visual Rule Builder requires a specific logic-modeling tool license. Jasper confirmed the budget request is "stuck in procurement."
- **Decision:** Move the Workflow Engine to "Blocked" status. Arun will focus on 2FA and SSO in the meantime to prevent idle time.
- **Action Item:** Jasper to escalate the tool purchase to the CFO.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salary/Contract fees for Senior Dev, QA, and Lead. |
| **Infrastructure** | $45,000 | AWS ECS, RDS, Redis, and S3 storage (Year 1). |
| **Software Tools** | $35,000 | Logic-engine license, IDEs, CI/CD tool premium tiers. |
| **External Consulting** | $20,000 | Retainer for Gia Kowalski-Nair. |
| **Contingency** | $20,000 | Buffer for unexpected API integration costs. |

---

## 12. APPENDICES

### Appendix A: Database Indexing Strategy
To ensure the "Advanced Search" (even though low priority) doesn't crash the system, the following indexes are implemented:
- `idx_user_email`: B-Tree index on `Users(email)` for fast login.
- `idx_site_loc`: GIST index on `Sites(geo_location)` for spatial queries.
- `idx_workflow_active`: Partial index on `Workflows(is_active)` where `is_active = true`.
- `idx_asset_serial`: Unique index on `Assets(serial_number)`.

### Appendix B: Security Audit Protocol
Since no external compliance (SOC2/HIPAA) is required, the team follows an **Internal Security Audit** cycle:
1. **Static Analysis:** `Bandit` is run on every commit to find common Python security vulnerabilities.
2. **Dependency Scanning:** `Safety` is used to check for known vulnerabilities in installed packages.
3. **Secret Management:** No secrets in code. Use **AWS Secrets Manager** for database passwords and API keys.
4. **Audit Logs:** All `POST/PUT/DELETE` requests are logged in a `SystemAudit` table with timestamp, user ID, and IP address.