# Project Specification: Project Ember
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 24, 2023  
**Company:** Coral Reef Solutions  
**Document Owner:** Greta Jensen (Engineering Manager)

---

## 1. Executive Summary

### Business Justification
Project Ember is a strategic imperative for Coral Reef Solutions. For fifteen years, the company has relied on a legacy cybersecurity monitoring system—now an aging monolith—to maintain the integrity of its retail operations. This legacy system is the single point of failure for the organization's security posture. As the retail landscape shifts toward omni-channel commerce and integrated supply chains, the current system's inability to scale, lack of real-time telemetry, and fragile codebase have become critical business risks. Any significant downtime in the monitoring layer results in an immediate loss of visibility into potential threats, creating a vulnerability gap that is unacceptable in the current threat landscape.

The objective of Project Ember is to replace this legacy system with a modern, high-performance cybersecurity dashboard. Unlike a standard migration, Ember requires a "zero downtime" transition. This means the new system must run in parallel with the legacy system, mirroring data and validating outputs until a seamless cutover can be achieved. 

### ROI Projection and Strategic Value
The ROI for Project Ember is measured through both cost avoidance and direct revenue generation. 
1. **Direct Revenue:** By introducing a customer-facing API and advanced monitoring capabilities, Coral Reef Solutions aims to monetize security-as-a-service for its high-tier retail partners. The target is to generate **$500,000 in new revenue** within the first 12 months post-launch.
2. **Cost Avoidance:** The legacy system currently requires approximately 40 man-hours per week of manual patching and "babysitting" by senior engineers. Transitioning to a managed Next.js/Vercel stack will reduce operational overhead by an estimated 60%.
3. **Compliance Value:** To secure government-sector retail contracts, FedRAMP authorization is mandatory. Project Ember is designed from the ground up to meet these stringent security requirements, unlocking a market segment previously inaccessible to the company.

### Operational Constraint
Crucially, Project Ember is currently **unfunded**. There is no dedicated capital expenditure budget. The project is being "bootstrapped," utilizing existing team capacity. This means the four-person team is balancing Ember's development with their daily operational responsibilities for Coral Reef Solutions, making efficient time management and strict adherence to the architecture critical.

---

## 2. Technical Architecture

### Architectural Pattern: Hexagonal Architecture (Ports and Adapters)
To ensure the system is maintainable and decoupled from external dependencies (such as the buggy integration partner API), Project Ember employs a Hexagonal Architecture.

**The Core (Domain Layer):** contains the business logic (e.g., threat detection algorithms, alert routing rules). This layer has zero knowledge of the database or the web framework.
**Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IAlertRepository`, `IUserAuthProvider`).
**Adapters:** Concrete implementations of the ports.
- *Persistence Adapter:* Prisma + PostgreSQL.
- *Web Adapter:* Next.js API Routes.
- *External Adapter:* Integration with the legacy system's data stream and the third-party partner API.

### ASCII Architecture Diagram
```text
       [ USER BROWSER ] <--> [ NEXT.JS / VERCEL FRONTEND ]
                                      |
                                      v
             ____________________[ WEB ADAPTER ]____________________
            |                                                       |
            |   [ INPUT PORT ] <-----------------> [ OUTPUT PORT ]  |
            |          |                                    |       |
            |          v                                     v       |
            |   ( SERVICE LAYER ) <-----------> ( DOMAIN MODELS )   |
            |          ^                                    ^       |
            |__________|____________________________________|_______|
                       |                                    |
       ________________v______________________       ________v_________________
      | [ PERSISTENCE ADAPTER (Prisma) ]     |     | [ EXTERNAL API ADAPTER ] |
      |--------------------------------------|     |---------------------------|
      |  [ PostgreSQL Database ]             |     | [ Legacy System / Partner]|
      |______________________________________|     |___________________________|
```

### Tech Stack Specifications
- **Frontend/Backend:** Next.js 14 (App Router), TypeScript 5.x.
- **ORM:** Prisma 5.x.
- **Database:** PostgreSQL 15.4 (Managed via Vercel Postgres/Neon).
- **Deployment:** Vercel (Edge Functions for global low-latency monitoring).
- **Auth:** NextAuth.js with OpenID Connect (OIDC) for FedRAMP compliance.
- **State Management:** Zustand for real-time dashboard state; React Query for server-state synchronization.

---

## 3. Detailed Feature Specifications

### Feature 1: Localization and Internationalization (i18n)
- **Priority:** Medium | **Status:** Blocked
- **Description:** As Coral Reef Solutions expands its retail footprint globally, the dashboard must support 12 languages (English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Italian, Arabic, Dutch, and Hindi).
- **Functional Requirements:**
    - Implementation of a dynamic locale-switching mechanism that detects user preference via browser headers but allows manual override.
    - Integration of `next-intl` or `i18next` for translation key management.
    - Right-to-Left (RTL) support for Arabic, requiring a CSS mirroring strategy using Tailwind CSS `rtl:` modifiers.
    - Support for locale-specific date/time formatting (ISO 8601) and currency symbols for billing modules.
- **Constraints:** This feature is currently **blocked** due to the lack of approved translation strings from the legal and compliance team.
- **Acceptance Criteria:** A user can switch between any of the 12 languages without a page reload, and all UI elements (including tooltips and error messages) update accordingly.

### Feature 2: Customer-Facing API with Versioning and Sandbox
- **Priority:** Medium | **Status:** Not Started
- **Description:** To achieve the $500K revenue target, Ember must expose its monitoring capabilities via a RESTful API, allowing retail partners to integrate their own security tools.
- **Functional Requirements:**
    - **Versioning:** The API must use URI versioning (e.g., `/api/v1/alerts`).
    - **Sandbox Environment:** A mirrored "Sandbox" environment where customers can test API calls against synthetic data without affecting production monitors.
    - **Rate Limiting:** Implementation of a leaky-bucket algorithm to prevent API abuse, with tiers based on the customer's subscription level.
    - **Authentication:** API Key-based authentication using rotating secrets stored in an encrypted vault.
- **Technical Detail:** The API will be built using Next.js Route Handlers, with a dedicated middleware layer for validation using Zod.
- **Acceptance Criteria:** Third-party developers can successfully authenticate and retrieve security telemetry from the sandbox environment.

### Feature 3: Advanced Search with Faceted Filtering and Full-Text Indexing
- **Priority:** High | **Status:** In Review
- **Description:** Cybersecurity analysts need to query millions of events quickly. Standard SQL `LIKE` queries are insufficient.
- **Functional Requirements:**
    - **Full-Text Search (FTS):** Implementation of PostgreSQL GIN indexes for rapid searching across event logs and threat descriptions.
    - **Faceted Filtering:** A sidebar allowing users to drill down by "Severity" (Low, Med, High, Critical), "Source IP," "Event Type," and "Time Range."
    - **Query Persistence:** Ability for users to save complex filter combinations as "Named Views."
    - **Highlighting:** Search results must highlight the matching keyword in the snippet.
- **Technical Detail:** Use of the `tsvector` and `tsquery` types in PostgreSQL to handle stemming and stop-words.
- **Acceptance Criteria:** A search query across 1 million records must return results in under 200ms.

### Feature 4: Real-Time Collaborative Editing with Conflict Resolution
- **Priority:** Critical | **Status:** Not Started (Launch Blocker)
- **Description:** During a security breach ("War Room" scenario), multiple analysts must be able to annotate a threat report or modify firewall rules simultaneously without overwriting each other's changes.
- **Functional Requirements:**
    - **Operational Transformation (OT) or CRDTs:** Implementation of Conflict-free Replicated Data Types (CRDTs) using Yjs or Automerge to ensure eventual consistency.
    - **Presence Indicators:** "Who is here" avatars and remote cursors showing exactly where other analysts are editing.
    - **Locking Mechanism:** Optional element-level locking for critical configuration changes to prevent accidental overrides.
    - **Audit Trail:** A detailed history of who changed what value and when, allowing for "time-travel" restoration of previous states.
- **Technical Detail:** WebSocket connection via a dedicated Node.js server (separate from Next.js serverless functions) to handle the persistent state of the collaborative session.
- **Acceptance Criteria:** Two users editing the same text field simultaneously must see their changes merge in real-time without data loss.

### Feature 5: Multi-tenant Data Isolation with Shared Infrastructure
- **Priority:** Medium | **Status:** In Progress
- **Description:** To keep costs low (bootstrapping), Ember uses shared infrastructure but must strictly isolate data between different retail clients.
- **Functional Requirements:**
    - **Row-Level Security (RLS):** Implementation of PostgreSQL RLS policies where every table includes a `tenant_id`.
    - **Tenant Context:** A middleware layer that extracts the `tenant_id` from the JWT and applies it to every Prisma query.
    - **Shared Schema:** Use of a single database schema for all tenants to simplify migrations, but with strict logical isolation.
    - **Tenant Management:** An admin interface for the Coral Reef team to create, suspend, or delete tenant accounts.
- **Technical Detail:** Prisma middleware will be used to inject `where: { tenantId: currentUser.tenantId }` into every find/update/delete operation.
- **Acceptance Criteria:** A user from Tenant A must be unable to access any data belonging to Tenant B, even if they possess the direct UUID of a Tenant B record.

---

## 4. API Endpoint Documentation

All endpoints require a Bearer Token in the Authorization header. All responses follow the format: `{ "data": { ... }, "error": null }` or `{ "data": null, "error": { "code": 400, "message": "..." } }`.

| Endpoint | Method | Path | Description | Request Body / Params | Response Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Get Alerts** | GET | `/api/v1/alerts` | Retrieve list of active alerts | `?severity=critical&limit=20` | `{"data": [{"id": "alrt_1", "msg": "SQL Injection detected"}]}` |
| **Create Alert** | POST | `/api/v1/alerts` | Manually trigger a security alert | `{"type": "IDS", "severity": "high", "source": "10.0.0.1"}` | `{"data": {"id": "alrt_2", "status": "created"}}` |
| **Update Alert** | PATCH | `/api/v1/alerts/:id` | Update alert status/assignment | `{"status": "resolved", "assignedTo": "user_8"}` | `{"data": {"id": "alrt_1", "status": "resolved"}}` |
| **Search Logs** | POST | `/api/v1/search` | Perform faceted full-text search | `{"query": "firewall", "filters": {"ip": "192.168.1.1"}}` | `{"data": {"results": [...], "total": 145}}` |
| **Tenant Info** | GET | `/api/v1/tenant/profile` | Get current tenant metadata | N/A | `{"data": {"name": "RetailCorp", "tier": "Gold"}}` |
| **Collab Session**| POST | `/api/v1/sessions` | Initialize a collaborative war-room | `{"alertId": "alrt_1"}` | `{"data": {"sessionId": "sess_99", "wsUrl": "wss://..."}}` |
| **API Key Rotate**| POST | `/api/v1/auth/rotate` | Rotate the customer API secret | `{"oldKey": "sk_..."}` | `{"data": {"newKey": "sk_new..."}}` |
| **System Health** | GET | `/api/v1/health` | Check system and legacy bridge status | N/A | `{"data": {"status": "healthy", "legacyBridge": "connected"}}` |

---

## 5. Database Schema

The database uses PostgreSQL with a strictly typed Prisma schema. All tables utilize UUIDs for primary keys.

### Tables and Relationships

1.  **`Tenant`**: The top-level entity.
    - `id`: UUID (PK)
    - `name`: String
    - `plan_tier`: Enum (Basic, Gold, Platinum)
    - `created_at`: Timestamp
2.  **`User`**: Users belonging to a tenant.
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ Tenant.id)
    - `email`: String (Unique)
    - `role`: Enum (Admin, Analyst, Viewer)
3.  **`Alert`**: Security events monitored.
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ Tenant.id)
    - `severity`: Enum (Low, Medium, High, Critical)
    - `description`: Text
    - `status`: Enum (Open, In-Progress, Resolved)
    - `created_at`: Timestamp
4.  **`AuditLog`**: Every change made in the system.
    - `id`: UUID (PK)
    - `user_id`: UUID (FK $\rightarrow$ User.id)
    - `action`: String
    - `entity_id`: UUID
    - `timestamp`: Timestamp
5.  **`CollaborativeSession`**: Tracking active "War Rooms."
    - `id`: UUID (PK)
    - `alert_id`: UUID (FK $\rightarrow$ Alert.id)
    - `started_at`: Timestamp
    - `ended_at`: Timestamp (Nullable)
6.  **`SessionParticipant`**: Users inside a session.
    - `session_id`: UUID (FK $\rightarrow$ CollaborativeSession.id)
    - `user_id`: UUID (FK $\rightarrow$ User.id)
    - `joined_at`: Timestamp
7.  **`APIKey`**: Customer-facing keys.
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ Tenant.id)
    - `hashed_key`: String
    - `last_used`: Timestamp
8.  **`LocalizationString`**: Translation mappings.
    - `id`: UUID (PK)
    - `key`: String (e.g., "dashboard.welcome")
    - `language_code`: String (e.g., "en-US", "ar-SA")
    - `translation`: Text
9.  **`IntegrationConfig`**: Settings for the partner API.
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ Tenant.id)
    - `api_endpoint`: String
    - `timeout_ms`: Integer
10. **`BillingAccount`**: Internal tracking of the $500K revenue target.
    - `id`: UUID (PK)
    - `tenant_id`: UUID (FK $\rightarrow$ Tenant.id)
    - `monthly_recurring_revenue`: Decimal
    - `last_invoice_date`: Date

---

## 6. Deployment and Infrastructure

### Environment Strategy
Ember utilizes three distinct environments to ensure stability and FedRAMP compliance.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and feature experimentation.
- **Infrastructure:** Vercel Preview Deployments.
- **Database:** Isolated Dev PostgreSQL instance with seeded mock data.
- **Access:** Entire internal team.

**2. Staging (Staging):**
- **Purpose:** Pre-production validation and QA. This environment mirrors Production exactly.
- **Infrastructure:** Vercel Staging branch.
- **Database:** Staging PostgreSQL instance containing a sanitized subset of production data.
- **Access:** Engineering team and selected Stakeholders.

**3. Production (Prod):**
- **Purpose:** Live monitoring for retail clients.
- **Infrastructure:** Vercel Production (with Global Edge Network).
- **Database:** High-Availability PostgreSQL cluster with automated hourly backups.
- **Access:** Only the Project Lead and Senior Backend Engineer.

### Deployment Cycle
Due to the retail industry's regulatory requirements, Ember does not use continuous deployment to production. Instead, it follows **Quarterly Releases**. 
- **Cycle:** Dev $\rightarrow$ Staging $\rightarrow$ Regulatory Review $\rightarrow$ Prod.
- **Window:** Releases occur on the first Tuesday of every quarter.
- **Zero Downtime:** Blue/Green deployment strategy is used. The legacy system remains active until the new version is verified in the production environment.

---

## 7. Testing Strategy

### Unit Testing
- **Scope:** Pure functions, domain logic, and utility helpers.
- **Tooling:** Vitest.
- **Requirement:** All new domain logic must have >90% coverage.
- **Focus:** Testing the Hexagonal Core without mocking the database.

### Integration Testing
- **Scope:** Testing the "Adapters."
- **Tooling:** Prisma Client and a dedicated Dockerized PostgreSQL container.
- **Focus:** Verifying that Row-Level Security (RLS) correctly isolates tenant data and that API endpoints return the correct schema.

### End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Search Alert $\rightarrow$ Resolve Alert").
- **Tooling:** Playwright.
- **Focus:** Ensuring the frontend and backend communicate correctly across the Vercel Edge network.

### Special Case: The Billing Module
**Current Status:** The core billing module was deployed under extreme deadline pressure and currently has **zero test coverage**. 
- **Remediation Plan:** This is identified as critical technical debt. The team is tasked with writing a comprehensive regression suite for the billing module before the 2026-07-15 security audit.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Budget cut by 30% in next fiscal quarter | High | High | Build a contingency plan with a fallback architecture (reducing third-party tool dependencies). |
| R2 | Integration partner's API is undocumented/buggy | Medium | High | De-scope affected features if unresolved by Milestone 2. Implement a robust wrapper with circuit breakers. |
| R3 | FedRAMP authorization failure | Low | Critical | Conduct monthly internal "mini-audits" to ensure compliance before the final review. |
| R4 | Team dysfunction leads to attrition | Medium | High | Weekly moderated syncs; move communication to Jira/GitHub Issues to reduce direct friction between PM and Lead. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure.
- **High:** Significant delay or loss of core functionality.
- **Medium:** Manageable with effort.
- **Low:** Minor annoyance.

---

## 9. Timeline and Milestones

The project timeline is calculated from the start date of October 2023, targeting a full release in late 2026.

### Phase 1: Foundation & Legacy Bridge (Oct 2023 - May 2026)
- **Focus:** Building the Hexagonal core and mirroring legacy data.
- **Dependency:** Stable connection to the legacy database.
- **Milestone 1: Performance benchmarks met (2026-05-15).** Target: Query response <200ms for 1M records.

### Phase 2: Security & Hardening (May 2026 - July 2026)
- **Focus:** FedRAMP compliance, RLS implementation, and fixing billing module debt.
- **Dependency:** Successful completion of Phase 1 benchmarks.
- **Milestone 2: Security audit passed (2026-07-15).** External audit of data isolation and access controls.

### Phase 3: Feature Completion & Pilot (July 2026 - Sept 2026)
- **Focus:** Collaborative editing, API sandbox, and i18n (once unblocked).
- **Dependency:** Passed security audit.
- **Milestone 3: Stakeholder demo and sign-off (2026-09-15).** Final presentation to Coral Reef executives.

---

## 10. Meeting Notes

### Meeting 1: Technical Alignment
**Date:** 2023-11-02  
**Attendees:** Greta Jensen, Xena Kim, Ilya Kim, Tariq Jensen  
**Discussion:** 
- Greta pushed for a strict Hexagonal Architecture to isolate the "messy" legacy system.
- Xena expressed concerns about Vercel's cold starts affecting real-time monitoring alerts.
- Ilya argued that the current dashboard layout is too cluttered for a 15-year-old system replacement; suggested a "clean slate" UX.
- Tariq raised a point about the integration partner's API failing intermittently during the last 48 hours.
**Action Items:**
- [Xena] Research Edge Functions to mitigate cold starts. (Owner: Xena)
- [Ilya] Create wireframes for the "Clean Slate" dashboard. (Owner: Ilya)
- [Greta] Contact the integration partner regarding API stability. (Owner: Greta)

### Meeting 2: The "Billing Debt" Crisis
**Date:** 2024-02-15  
**Attendees:** Greta Jensen, Xena Kim  
**Discussion:**
- (Note: Tension was high; the two participants spoke primarily through the Jira ticket and avoided eye contact).
- Greta noted that the billing module was deployed without tests.
- Xena argued that the deadline was impossible and that "shipping was the priority."
- It was decided that the billing module cannot be modified further until a full test suite is written.
**Action Items:**
- [Xena] Block all changes to the billing module. (Owner: Xena)
- [Greta] Schedule a "Debt Sprint" for Q3. (Owner: Greta)

### Meeting 3: FedRAMP Strategy
**Date:** 2024-06-20  
**Attendees:** Greta Jensen, Xena Kim, Tariq Jensen  
**Discussion:**
- Discussion on the requirement for "Government Cloud" isolation.
- Tariq suggested that Row-Level Security (RLS) in Postgres is the most efficient way to handle this without spinning up 100 separate databases.
- Xena agreed but warned that RLS can lead to performance degradation if not indexed correctly.
- Agreed to implement RLS and monitor performance during the 2026-05-15 benchmark phase.
**Action Items:**
- [Tariq] Draft the RLS policy schema. (Owner: Tariq)
- [Xena] Run a performance test on 10M rows with RLS enabled. (Owner: Xena)

---

## 11. Budget Breakdown

Since the project is **unfunded (bootstrapped)**, the budget represents "Internal Resource Allocation" (the cost of employee time) rather than cash spend.

| Category | Annualized Cost (Estimated) | Detail |
| :--- | :--- | :--- |
| **Personnel (Full-time)** | $420,000 | Salary allocation for Greta, Xena, Ilya. |
| **Personnel (Contract)** | $110,000 | Contract fees for Tariq. |
| **Infrastructure** | $12,000 | Vercel Pro + Neon Postgres managed costs. |
| **Tools** | $3,000 | GitHub Enterprise, Jira, Figma, Sentry. |
| **Contingency** | $50,000 | Buffer for potential emergency contractor hire if budget is cut by 30%. |
| **Total Virtual Budget** | **$595,000** | |

*Note: If the 30% budget cut occurs, the project will transition from a 4-person team to a 3-person team, and Tariq's contract will be terminated first.*

---

## 12. Appendices

### Appendix A: FedRAMP Compliance Checklist
To achieve authorization, Ember must implement the following:
1. **FIPS 140-2 Validated Encryption:** All data at rest must be encrypted using AES-256.
2. **Multi-Factor Authentication (MFA):** Mandatory for all administrative accounts.
3. **Audit Logging:** Every API request must be logged with a timestamp, user ID, and action taken (implemented in `AuditLog` table).
4. **Vulnerability Scanning:** Weekly automated scans of the Next.js dependency tree using `npm audit` and Snyk.

### Appendix B: Legacy Data Mapping
The following mapping is used to migrate data from the 15-year-old system to the new PostgreSQL schema:

| Legacy Table | Ember Table | Field Mapping | Transformation |
| :--- | :--- | :--- | :--- |
| `TBL_SEC_EVNT` | `Alert` | `EVNT_DESC` $\rightarrow$ `description` | Trim whitespace, sanitize HTML |
| `TBL_USR_ACC` | `User` | `ACC_ID` $\rightarrow$ `id` | Convert Integer to UUID |
| `LOG_HISTORY` | `AuditLog` | `OP_CODE` $\rightarrow$ `action` | Map numeric codes to string labels |
| `CLIENT_INFO` | `Tenant` | `CUST_NAME` $\rightarrow$ `name` | Standardize casing |