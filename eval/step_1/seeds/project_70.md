# PROJECT EMBER: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Status:** Draft/Active  
**Project Lead:** Arjun Gupta (Engineering Manager)  
**Company:** Tundra Analytics  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Ember represents a critical strategic evolution for Tundra Analytics. As a leader in agriculture technology, Tundra Analytics provides high-precision data telemetry for large-scale farming operations. The current monolithic architecture has reached its scaling limit, creating significant friction in the delivery of new features and limiting the company's ability to integrate with strategic partners. 

The primary business driver for Project Ember is the integration with a key external strategic partner (hereafter referred to as "Partner X"). Partner X operates on a rigid, externally dictated timeline for API synchronization. To remain competitive and fulfill the contractual obligations of this partnership, Tundra Analytics must transition from its legacy system to a modern, serverless microservices architecture orchestrated by a robust API Gateway. This transition will allow Tundra to decouple its internal business logic from the external partner's API constraints, ensuring that partner-driven changes do not cause cascading failures across the Tundra ecosystem.

### 1.2 ROI Projection
The financial investment for Project Ember is capped at $1.5M. The projected Return on Investment (ROI) is calculated based on three primary levers:
1. **Reduced Operational Overhead:** Transitioning to serverless functions (Vercel/Next.js) is projected to reduce infrastructure maintenance costs by 22% annually by eliminating the need for manual server patching and scaling.
2. **Increased Market Penetration:** The implementation of SSO (SAML/OIDC) and localization for 12 languages opens the door to enterprise-level agricultural conglomerates in the EU and LATAM markets, with a projected revenue increase of $3.2M in the first 18 months post-launch.
3. **Partner Integration Efficiency:** By implementing an API Gateway, the time-to-market for new partner-driven features is expected to drop from 6 weeks to 10 business days.

The total projected Net Present Value (NPV) of this migration over three years is estimated at $4.8M, assuming a successful launch by the September 2025 performance benchmark milestone.

### 1.3 Scope Statement
Project Ember encompasses the migration of core agricultural telemetry and user management services to a TypeScript-based serverless stack. This includes the implementation of a centralized API Gateway to handle request routing, rate limiting, and security orchestration. The project focuses specifically on five key feature sets, ranging from critical SSO integration to "nice-to-have" automated billing.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Ember utilizes a "Backend-for-Frontend" (BFF) pattern combined with a serverless microservices architecture. By leveraging Next.js and Vercel, we maximize developer velocity and minimize cold-start latency. The architecture is designed to be "eventual consistency" focused, utilizing PostgreSQL via Prisma for strongly typed data access.

### 2.2 Stack Detail
- **Language:** TypeScript 5.2+ (Strict Mode)
- **Framework:** Next.js 14 (App Router)
- **ORM:** Prisma 5.0+
- **Database:** PostgreSQL 15 (Managed via Vercel Postgres/Neon)
- **Deployment:** Vercel (Edge Functions for Gateway, Serverless Functions for Logic)
- **Feature Management:** LaunchDarkly (for canary releases and feature toggling)
- **Security:** Quarterly Penetration Testing (External Vendor)

### 2.3 API Gateway Orchestration
The API Gateway acts as the single entry point for all client requests. It is responsible for:
- **Authentication:** Validating JWTs and SAML assertions.
- **Routing:** Mapping incoming requests to specific serverless function endpoints.
- **Transformation:** Converting Partner X’s legacy XML responses into standardized JSON for the frontend.
- **Rate Limiting:** Implementing leaky-bucket algorithms to prevent DDoS and API abuse.

### 2.4 ASCII Architecture Diagram
```text
[ CLIENT LAYER ]          [ GATEWAY LAYER ]            [ MICROSERVICES LAYER ]
+----------------+       +-------------------+       +-----------------------+
| Web Dashboard   | ----> | Vercel Edge Router | ----> | Auth Service (SAML)    |
| (Next.js/TS)    |       | (API Gateway)     |       +-----------------------+
+----------------+       +---------+---------+       +-----------------------+
                                   |                 | Sync Service (Offline) |
[ EXTERNAL PARTNER ]               |                 +-----------------------+
+----------------+       +---------v---------+       +-----------------------+
| Partner X API   | <--- | Adaptation Layer  | <---> | Billing Service (Prisma)|
| (REST/XML)      |       | (Transformation) |       +-----------------------+
+----------------+       +-------------------+       +-----------------------+
                                                             |
                                                     +-------v----------------+
                                                     | PostgreSQL Database     |
                                                     | (User, Crop, Bill, Sync)|
                                                     +-----------------------+
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Progress
**Description:** 
The authentication system must support a multi-tenant architecture where users are assigned to specific agricultural organizations. RBAC will be implemented to ensure that data isolation is maintained across different farm sizes and corporate entities.

**Detailed Requirements:**
- **Roles:** The system shall support four primary roles: `SuperAdmin` (Tundra internal), `OrgAdmin` (Customer company lead), `FarmManager` (Field operator), and `ReadOnly` (Auditor).
- **Permission Logic:** Permissions are defined at the action level (e.g., `crop:write`, `billing:read`). A middleware layer in the API Gateway will intercept every request and validate the user's token against the required permission for that specific endpoint.
- **Token Management:** Use of JWT (JSON Web Tokens) with a 15-minute expiration and a sliding session refresh token stored in an HttpOnly cookie.
- **Role Transition:** Users must be able to switch between multiple organizations if they are consultants managing multiple farms.

**Implementation Detail:** 
The RBAC system will utilize a "Permission-Role-User" junction table. When a user logs in, their active permissions are cached in a Redis layer (via Vercel KV) to avoid repeated database hits on every single API call.

### 3.2 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** Not Started
**Description:** 
Agriculture technology is frequently used in rural areas with intermittent 4G/5G connectivity. The application must allow users to input crop data and sensor readings while offline, syncing automatically when a connection is re-established.

**Detailed Requirements:**
- **Local Persistence:** Use of IndexedDB via a wrapper like `Dexie.js` to store pending mutations.
- **Conflict Resolution:** The system will employ a "Last Write Wins" strategy by default, but for critical telemetry data, it will implement a versioning timestamp (Optimistic Locking).
- **Background Sync:** Implementation of the Service Worker API to handle sync events. When the browser detects a `sync` event, it will push the local queue to the `/api/sync/bulk` endpoint.
- **UI Feedback:** A persistent "Sync Status" indicator in the footer: `Synced`, `Syncing...`, or `Offline (X pending changes)`.

**Implementation Detail:** 
The Sync Service will implement a checksum validation. The client sends a hash of the local state; the server compares it with the database state. If they mismatch, the server sends a delta-update package to the client.

### 3.3 Localization and Internationalization (i18n)
**Priority:** Medium | **Status:** Blocked
**Description:** 
Tundra Analytics is expanding globally. The platform must support 12 distinct languages, including English, Spanish, Portuguese, French, German, Mandarin, Japanese, Hindi, Vietnamese, Thai, Dutch, and Polish.

**Detailed Requirements:**
- **Dynamic Routing:** Use of Next.js dynamic segments (`/[lang]/dashboard`) to handle localized URLs.
- **Translation Management:** Integration with a Headless CMS or translation tool (e.g., Lokalise) to allow non-technical translators to update copy without code deployments.
- **Regional Formatting:** Localization of dates (ISO 8601), currency (USD, EUR, BRL), and metric/imperial units (Hectares vs. Acres).
- **Right-to-Left (RTL) Support:** While not currently required for the 12 languages, the CSS architecture (Tailwind) must be structured to support RTL flips.

**Blocker Note:** This feature is currently blocked awaiting the finalization of the "Language Asset Pack" from the marketing department and the legal review of terms and conditions in 12 languages.

### 3.4 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Not Started
**Description:** 
A "nice-to-have" feature to automate the invoicing process based on the amount of telemetry data ingested per month.

**Detailed Requirements:**
- **Tiered Pricing:** Support for `Basic` (up to 10k sensors), `Pro` (up to 100k sensors), and `Enterprise` (Unlimited).
- **Usage Tracking:** A background worker that aggregates daily sensor hits and updates the `BillingUsage` table.
- **Invoicing:** Integration with Stripe for automated monthly credit card charging and PDF invoice generation.
- **Grace Periods:** Implementation of a 14-day grace period for failed payments before restricting access to "Read-Only" mode.

**Technical Debt Warning:** The current legacy billing module has 0% test coverage. This new module must be built from scratch with 100% unit test coverage for the calculation logic to avoid the regressions seen in the previous version.

### 3.5 SSO Integration with SAML and OIDC Providers
**Priority:** Critical | **Status:** In Review
**Description:** 
This is a launch blocker. Enterprise clients require the ability to manage users via their own identity providers (Okta, Azure AD, Google Workspace).

**Detailed Requirements:**
- **SAML 2.0:** Support for Service Provider (SP) initiated and Identity Provider (IdP) initiated SSO.
- **OIDC:** Integration with OpenID Connect for modern OAuth2 flows.
- **Just-in-Time (JIT) Provisioning:** Automatically create a user account in Tundra Analytics upon the first successful SSO login, mapping SAML attributes to Tundra roles.
- **Certificate Management:** A secure vault for storing IdP public certificates for signature verification.

**Implementation Detail:** 
We will use `passport-saml` and `next-auth` for the orchestration layer. The flow involves a redirect to the IdP, a POST callback containing a SAMLResponse, and a verification step against the stored public key of the partner organization.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `Bearer <JWT>` token in the Authorization header.

### 4.1 `POST /auth/sso/login`
Initiates the SSO flow.
- **Request Body:** `{ "provider": "okta", "orgId": "org_123" }`
- **Response (200):** `{ "url": "https://okta.com/auth/..." }`
- **Response (400):** `{ "error": "Invalid Provider" }`

### 4.2 `POST /auth/sso/callback`
The endpoint where the IdP sends the SAML assertion.
- **Request Body:** `{ "SAMLResponse": "..." }`
- **Response (200):** `{ "token": "jwt_access_token", "refreshToken": "jwt_refresh_token", "user": { "id": "u_987", "role": "FarmManager" } }`

### 4.3 `GET /telemetry/sensors`
Retrieves a list of all active sensors for the authenticated user's organization.
- **Query Params:** `?farmId=f_456&status=active`
- **Response (200):** `[ { "id": "s_1", "type": "moisture", "value": 45.2, "timestamp": "2023-10-26T10:00Z" }, ... ]`

### 4.4 `POST /telemetry/sync/bulk`
Bulk upload for offline-first sync.
- **Request Body:** `{ "batchId": "b_001", "data": [ { "sensorId": "s_1", "val": 44.1, "ts": "..." }, ... ] }`
- **Response (202):** `{ "status": "Accepted", "processed": 45, "conflicts": 2 }`

### 4.5 `GET /billing/subscription`
Retrieves current subscription status.
- **Response (200):** `{ "plan": "Pro", "nextBillingDate": "2023-11-01", "usage": "85%" }`

### 4.6 `PATCH /user/profile`
Updates user preferences and localization settings.
- **Request Body:** `{ "language": "pt-BR", "timezone": "America/Sao_Paulo" }`
- **Response (200):** `{ "userId": "u_987", "updated": true }`

### 4.7 `GET /partner/status`
Checks the current health and sync status of the Partner X API integration.
- **Response (200):** `{ "status": "Healthy", "lastSync": "2023-10-26T09:45Z", "latency": "140ms" }`

### 4.8 `DELETE /admin/user/{userId}`
Administrative removal of a user (SuperAdmin only).
- **Response (204):** No content.
- **Response (403):** `{ "error": "Insufficient Permissions" }`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15, managed via Prisma.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `id` (UUID) | `orgId` | `email`, `passwordHash`, `roleId` | Core user identity and credentials. |
| `Organizations` | `id` (UUID) | - | `name`, `ssoProvider`, `createdAt` | The tenant entity (Agriculture Co). |
| `Roles` | `id` (Int) | - | `roleName`, `permissions` (JSONB) | Defines RBAC levels (e.g., Admin). |
| `Farms` | `id` (UUID) | `orgId` | `location`, `acreage`, `climateZone` | Physical farm entities. |
| `Sensors` | `id` (UUID) | `farmId` | `sensorType`, `lastSeen`, `status` | Hardware telemetry devices. |
| `TelemetryData` | `id` (BigInt) | `sensorId` | `value`, `timestamp`, `unit` | Time-series data for crops. |
| `SyncQueue` | `id` (UUID) | `userId` | `payload` (JSONB), `status`, `retryCount` | Tracks offline-first sync status. |
| `Subscriptions` | `id` (UUID) | `orgId` | `planType`, `stripeCustomerId`, `active` | Billing and plan details. |
| `BillingLogs` | `id` (UUID) | `subId` | `amount`, `transactionDate`, `status` | Audit trail for payments. |
| `AuditLogs` | `id` (BigInt) | `userId` | `action`, `ipAddress`, `timestamp` | Security logs for pen-testing. |

### 5.2 Relationships
- **One-to-Many:** `Organizations` $\rightarrow$ `Users` (One org has many users).
- **One-to-Many:** `Organizations` $\rightarrow$ `Farms` (One org manages many farms).
- **One-to-Many:** `Farms` $\rightarrow$ `Sensors` (One farm has many sensors).
- **One-to-Many:** `Sensors` $\rightarrow$ `TelemetryData` (One sensor generates millions of readings).
- **One-to-One:** `Organizations` $\rightarrow$ `Subscriptions` (One org has one active plan).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We employ a three-tier environment strategy to ensure stability and rigorous testing.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and internal testing.
- **Deployment:** Automatic deploy on every merge to `develop` branch.
- **Data:** Mock data and sanitized snapshots of production.
- **Access:** All 12 team members.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation, QA, and stakeholder demos.
- **Deployment:** Triggered by a release candidate (RC) tag.
- **Data:** Mirror of production schema with anonymized data.
- **Access:** Engineering team, Product Designer (Nadira), and Stakeholders.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live customer traffic.
- **Deployment:** Canary releases via Vercel. 5% of traffic is shifted to the new version, monitored for 1 hour, then scaled to 100%.
- **Data:** Live customer data.
- **Access:** Strictly limited to Arjun Gupta and lead DevOps.

### 6.2 Feature Flagging and Canary Releases
LaunchDarkly is integrated into the codebase. Every new feature in Project Ember must be wrapped in a feature flag.
- **Canary Flow:** 
    1. Deploy code to `prod` (hidden by flag).
    2. Enable flag for "Internal Beta" group (Tundra employees).
    3. Enable flag for 10% of "Partner X" users.
    4. Full rollout.

### 6.3 Infrastructure as Code (IaC)
While Vercel handles the compute, the PostgreSQL instance is managed via Terraform to ensure that backups and scaling rules are version-controlled.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** Jest + Vitest
- **Coverage Target:** 80% overall. 100% for billing and auth logic.
- **Frequency:** Runs on every commit (GitHub Actions).
- **Focus:** Pure functions, utility helpers, and Prisma schema validators.

### 7.2 Integration Testing
- **Tool:** Playwright
- **Focus:** Testing the interaction between the API Gateway and the microservices.
- **Scenarios:** 
    - Successful SAML handshake.
    - Bulk sync upload with 10% simulated packet loss.
    - RBAC permission denial for `ReadOnly` users attempting to delete sensors.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress
- **Focus:** Critical user journeys.
- **Key Paths:**
    - `Login` $\rightarrow$ `Dashboard` $\rightarrow$ `Sensor Detail` $\rightarrow$ `Update Value`.
    - `Admin` $\rightarrow$ `Billing` $\rightarrow$ `Upgrade Plan`.

### 7.4 Security Testing
- **Quarterly Pen-Testing:** An external security firm will perform "black box" testing every three months.
- **SAML Validation:** Specific focus on XML Signature wrapping attacks and Replay attacks.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for AgTech data change. | High | Medium | Hire a specialized legal contractor to reduce "bus factor" and ensure compliance. | Arjun |
| R-02 | Scope creep from stakeholders. | High | High | Strict "Change Request" process; de-scope low-priority features (e.g., Billing) if milestones are missed. | Arjun |
| R-03 | Key team member medical leave (6 weeks). | Actual | High | Redistribute tasks across the remaining 11 members; prioritize "Critical" features over "Medium". | Team |
| R-04 | Technical debt in legacy billing module. | Actual | Medium | Complete rewrite of the billing module with 100% test coverage. | Arjun |
| R-05 | Partner X API downtime/instability. | Medium | High | Implement aggressive caching and a circuit breaker pattern in the API Gateway. | Xavi |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **High/Medium:** Monitor weekly.
- **Medium/Low:** Accept risk.

---

## 9. TIMELINE

Project Ember is tracked across three primary phases.

### Phase 1: Foundation & Security (Oct 2023 - May 2025)
- **Focus:** Infrastructure setup, API Gateway orchestration, and SSO.
- **Dependencies:** SAML provider specifications from Partner X.
- **Key Milestone:** **Milestone 1: Security Audit Passed (2025-05-15)**.
- **Activities:** 
    - Setup Vercel/Postgres environments.
    - Implement SSO (SAML/OIDC).
    - Build RBAC system.

### Phase 2: Core Functionality & Integration (May 2025 - July 2025)
- **Focus:** Telemetry sync, offline-first mode, and partner API mapping.
- **Dependencies:** Completion of security audit.
- **Key Milestone:** **Milestone 2: Stakeholder Demo & Sign-off (2025-07-15)**.
- **Activities:** 
    - Implement IndexedDB sync logic.
    - Map Partner X API endpoints to internal services.
    - Development of localization (pending blocker).

### Phase 3: Optimization & Launch (July 2025 - Sept 2025)
- **Focus:** Performance tuning, billing automation, and final QA.
- **Dependencies:** Stakeholder sign-off.
- **Key Milestone:** **Milestone 3: Performance Benchmarks Met (2025-09-15)**.
- **Activities:** 
    - p95 latency optimization.
    - Final penetration test.
    - Automated billing rollout.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team policy, formal meeting minutes are not kept. Decisions are documented in Slack threads. Below are the transcriptions of three pivotal decision threads.

### Thread 1: #eng-ember-arch (Date: 2023-11-02)
**Arjun:** "I'm seeing some lag in the Partner X mock API. Should we implement a caching layer at the Gateway or the Service level?"
**Xavi:** "If we do it at the Gateway, we can serve stale data while the service refreshes. Better for the UX in rural areas."
**Anouk:** "Agree. Let's use Vercel KV for a 5-minute TTL on telemetry lookups."
**Decision:** API Gateway will implement a 5-minute cache using Vercel KV to mitigate Partner X API latency.

### Thread 2: #prod-ember-design (Date: 2023-12-15)
**Nadira:** "The current SSO flow takes 4 redirects. It's confusing for the users. Can we flatten it?"
**Arjun:** "SAML requires the redirect to the IdP. We can't change that, but we can add a 'Redirecting to your identity provider...' loading screen to manage expectations."
**Anouk:** "I'll build a custom transition component for that."
**Decision:** Add a branded transition screen during SSO redirects to improve perceived performance.

### Thread 3: #eng-ember-billing (Date: 2024-01-20)
**Arjun:** "I've reviewed the legacy billing code. It's a disaster. No tests, nested loops for tax calculation. We cannot migrate this."
**Xavi:** "Do we have time to rewrite it?"
**Arjun:** "We have the budget. We'll treat the billing module as a new service. New requirement: 100% unit test coverage on all financial logic. No exceptions."
**Decision:** Total rewrite of the billing module; mandated 100% test coverage.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$1,500,000 USD**

### 11.1 Personnel ($1,100,000)
- **Engineering Management (Arjun):** $180,000
- **Frontend Lead (Anouk):** $150,000
- **Product Designer (Nadira):** $130,000
- **Support Engineer (Xavi):** $120,000
- **8x Full-stack Developers:** $520,000 (Average $65k/person for project duration)

### 11.2 Infrastructure & Tools ($220,000)
- **Vercel Enterprise Plan:** $40,000
- **PostgreSQL Managed (Neon/Vercel):** $30,000
- **LaunchDarkly Enterprise:** $25,000
- **Security Pen-Testing (Quarterly):** $60,000 ($15k per audit)
- **Lokalise (i18n tool):** $15,000
- **Misc. Cloud Costs:** $50,000

### 11.3 Contingency & Legal ($180,000)
- **Regulatory Contractor:** $80,000 (To mitigate Risk R-01)
- **Emergency Buffer:** $100,000 (For unexpected hardware/licensing needs)

---

## 12. APPENDICES

### Appendix A: Partner X API Mapping Table
The following mapping is used by the Adaptation Layer in the API Gateway to translate Partner X's legacy XML to Tundra JSON.

| Partner X Endpoint | Tundra Ember Endpoint | Transformation Logic |
| :--- | :--- | :--- |
| `GET /xml/sensor_list` | `GET /telemetry/sensors` | Map `<SENS_ID>` to `id`, `<VAL>` to `value`. |
| `POST /xml/sync_data` | `POST /telemetry/sync/bulk` | Convert JSON array to XML SOAP envelope. |
| `GET /xml/user_auth` | `POST /auth/sso/callback` | Map SAML Attribute Statements to User Roles. |

### Appendix B: Performance Benchmark Definitions
To meet Milestone 3, the following metrics must be validated under a simulated load of 10,000 concurrent requests.

1. **p95 Latency:** 95% of all requests to the API Gateway must complete in $\le 200\text{ms}$.
2. **Error Rate:** The HTTP 5xx error rate must remain below 0.1% during peak load.
3. **Cold Start:** Serverless function cold starts must be mitigated using Vercel's "Warm-up" patterns, keeping initial response times under 500ms.
4. **Sync Throughput:** The `/api/sync/bulk` endpoint must be able to process 500 records per second without database locking.