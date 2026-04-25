# PROJECT SPECIFICATION: PROJECT VANGUARD
**Version:** 1.0.4  
**Document Status:** Active / Baseline  
**Company:** Verdant Labs  
**Date:** October 24, 2023  
**Project Lead:** Amira Oduya (Tech Lead)  
**Classification:** Internal / Proprietary (PCI DSS Level 1)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Vanguard represents a mission-critical infrastructure overhaul for Verdant Labs. The organization currently relies on a 15-year-old legacy IoT device network that governs the core retail operations across all physical locations. This legacy system, while stable in its prime, has become a systemic risk. It suffers from monolithic fragility, lack of scalability, and an inability to integrate with modern retail analytics tools. Because the entire company depends on this network for inventory tracking, point-of-sale synchronization, and device management, the cost of failure is catastrophic.

The primary objective of Vanguard is the complete replacement of this legacy stack with a modern, scalable, and secure IoT network. The most stringent constraint of this project is **zero downtime tolerance**. Any interruption in the transition from the legacy system to Vanguard would result in immediate revenue loss and operational paralysis across the retail chain.

### 1.2 Strategic Objectives
Vanguard is not merely a technical upgrade but a strategic pivot toward a micro-frontend architecture. By decoupling the user interface and the backend services, Verdant Labs will enable independent team ownership, allowing for faster iteration cycles and reduced deployment risk. Furthermore, the system must adhere to PCI DSS Level 1 compliance, as the network will process credit card data directly at the edge (IoT device level), necessitating a rigorous security posture.

### 1.3 ROI Projection
The projected Return on Investment (ROI) is calculated based on three primary drivers:
1. **Operational Efficiency:** Reduction in maintenance man-hours for the legacy system (currently consuming 40% of the engineering budget) by an estimated 70%.
2. **Reduced Latency:** Improving API response times to a p95 of <200ms will increase transaction throughput at retail kiosks, projected to increase conversion rates by 2.5%.
3. **Risk Mitigation:** Eliminating the "single point of failure" inherent in the legacy system prevents potential outages that are estimated to cost the company $150,000 per hour of downtime.

With a modest budget of $400,000, the project is designed for high efficiency. The ROI is expected to break even within 14 months post-launch, driven by the removal of legacy licensing fees and the increase in operational uptime.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Vanguard utilizes a modern TypeScript ecosystem to ensure type safety across the entire stack. The architecture is designed as a series of micro-frontends served via Vercel, communicating with a robust backend powered by Next.js API routes, Prisma ORM, and a PostgreSQL database.

### 2.2 Architecture Components
- **Frontend:** Next.js 14 (App Router) utilizing a micro-frontend pattern. Independent modules are deployed as separate applications but unified through a shared design system and shell.
- **Backend/API:** Next.js Serverless Functions acting as the orchestration layer.
- **Database:** PostgreSQL 15 managed instance.
- **ORM:** Prisma (with strategic raw SQL bypasses for performance-critical queries).
- **Deployment:** Vercel for frontend/API; LaunchDarkly for feature flagging and canary releases.

### 2.3 ASCII Architecture Diagram
```text
[ IoT Device Network ] <---(MTLS / HTTPS)---> [ Vercel Edge Network ]
                                                    |
                                                    v
                                        [ Next.js Micro-Frontends ]
                                       /            |             \
                         [ Auth Module ]    [ Dashboard Module ]  [ API Gateway ]
                                 |                  |                      |
                                 v                  v                      v
                          [ Redis Cache ] <--- [ Prisma ORM ] <--- [ PostgreSQL DB ]
                                                    ^
                                                    |
                                        [ Raw SQL Performance Layer ]
                                                    |
                                        [ PCI DSS Compliant Vault ]
```

### 2.4 Data Flow and Security
Because the system processes credit card data directly, the architecture implements a "strict isolation" zone. Data entering the system is encrypted at the edge using AES-256. The PostgreSQL database utilizes Row Level Security (RLS) to ensure that different retail locations cannot access each other's data. Prisma handles standard CRUD operations, but for high-frequency IoT telemetry, raw SQL is utilized to bypass the ORM overhead, ensuring the p95 response time targets are met.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
- **Priority:** Medium
- **Status:** Blocked (Dependency on Identity Provider API)
- **Description:**
The authentication system is the gatekeeper for the entire Vanguard network. It must support three primary roles: `SuperAdmin` (Global control), `RegionalManager` (Access to specific geographic clusters), and `StoreAssociate` (Local device management).

The system will implement OpenID Connect (OIDC) for identity management. Given the PCI DSS requirements, Multi-Factor Authentication (MFA) is mandatory for all users with `SuperAdmin` or `RegionalManager` privileges. The RBAC system will be implemented via a middleware layer in Next.js that checks the user's claims against the requested resource.

**Technical Requirements:**
- JWT-based session management with short-lived access tokens (15 mins) and long-lived refresh tokens stored in HttpOnly cookies.
- Audit logging for every authentication attempt, including IP address and device fingerprint.
- Integration with the corporate LDAP for seamless employee onboarding.
- The "Blocked" status is currently due to a mismatch in the OIDC discovery document provided by the third-party identity provider, preventing the successful handshake of the auth flow.

### 3.2 Customer-Facing API with Versioning and Sandbox
- **Priority:** Low (Nice to have)
- **Status:** Blocked (Pending API Rate Limit Resolution)
- **Description:**
To allow retail partners to integrate their own analytics tools, Vanguard will provide a public-facing REST API. To prevent breaking changes, the API will implement strict semantic versioning (e.g., `/v1/devices`, `/v2/devices`).

A critical component of this feature is the **Sandbox Environment**. This is a mirrored version of the production environment with synthetic data, allowing third-party developers to test their integrations without affecting live retail devices. 

**Technical Requirements:**
- Rate limiting implemented via Redis to prevent DDoS attacks on the API gateway.
- API Key management system allowing customers to rotate keys.
- Automated documentation generated via Swagger/OpenAPI 3.0.
- The "Blocked" status is a direct result of the third-party API rate limits encountered during testing, which prevent the sandbox from populating synthetic data at the required scale.

### 3.3 Offline-First Mode with Background Sync
- **Priority:** Low (Nice to have)
- **Status:** In Progress
- **Description:**
Retail environments often suffer from intermittent connectivity. The Vanguard dashboard must remain functional even when the local network is down. This is achieved through a "Local-First" strategy using IndexedDB for browser-side storage.

When a user performs an action (e.g., updating a device configuration) while offline, the action is queued in a local "Outbox." Once connectivity is restored, a background synchronization service will reconcile the local changes with the PostgreSQL database.

**Technical Requirements:**
- Implementation of a Conflict Resolution Strategy (Last-Write-Wins) to handle data collisions during sync.
- Use of Service Workers to cache critical application assets for instant loading.
- A "Sync Status" indicator in the UI to inform users whether their data is currently local or persisted to the cloud.
- Current progress involves the implementation of the IndexedDB schema and the basic sync loop.

### 3.4 Localization and Internationalization (i18n)
- **Priority:** Low (Nice to have)
- **Status:** In Review
- **Description:**
As Verdant Labs expands, the Vanguard system must support 12 different languages to accommodate global retail staff. This involves more than simple translation; it requires localization of date formats, currency symbols, and right-to-left (RTL) support for specific locales.

The implementation uses `next-intl` for routing and translation management. Translation files are stored as JSON objects, indexed by locale codes (e.g., `en-US`, `fr-FR`, `ja-JP`).

**Technical Requirements:**
- Dynamic loading of translation bundles to avoid increasing the initial JS payload.
- Support for RTL layouts (e.g., Arabic) through CSS logical properties.
- A translation management workflow where non-technical staff can submit translation updates via a Google Sheet that is then converted to JSON.
- Currently in review to ensure that the 12 selected languages cover all active retail markets without overlap.

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
- **Priority:** Critical (Launch Blocker)
- **Status:** Not Started
- **Description:**
The central hub of Vanguard is the operator dashboard. Given the diversity of retail needs, a one-size-fits-all view is insufficient. Users must be able to customize their workspace by adding, removing, and rearranging widgets (e.g., "Device Health Monitor," "Real-time Transaction Volume," "Security Alerts").

The dashboard will utilize a grid-based layout system (React-Grid-Layout) allowing users to resize and drag widgets. The configuration for each user's layout will be persisted in the PostgreSQL database as a JSONB blob.

**Technical Requirements:**
- High-performance rendering to ensure that dragging widgets does not cause layout shift or lag.
- A "Widget Library" where users can select from a pre-defined set of data visualization components.
- State management using Zustand to track widget positions and filter settings in real-time.
- This is a launch blocker because without it, the operational staff cannot monitor the legacy-to-vanguard transition effectively.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted under `https://api.vanguard.verdantlabs.io`.

### 4.1 GET `/v1/devices`
**Description:** Retrieve a list of all registered IoT devices.
- **Request:** `GET /v1/devices?region=north_america&status=active`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "dev_9921", "status": "active", "firmware": "2.1.0", "last_ping": "2023-10-24T10:00:00Z" },
    { "id": "dev_4432", "status": "inactive", "firmware": "2.0.9", "last_ping": "2023-10-23T14:20:00Z" }
  ],
  "pagination": { "total": 150, "page": 1, "limit": 20 }
}
```

### 4.2 POST `/v1/devices/{id}/config`
**Description:** Update the configuration of a specific IoT device.
- **Request:** `POST /v1/devices/dev_9921/config`
- **Body:** `{ "polling_interval": 30, "power_save": true }`
- **Response (202 Accepted):**
```json
{ "status": "queued", "job_id": "job_abc123", "estimated_completion": "200ms" }
```

### 4.3 GET `/v1/transactions/summary`
**Description:** Get aggregated transaction data for the current window. (PCI DSS Compliant)
- **Request:** `GET /v1/transactions/summary?window=1h`
- **Response (200 OK):**
```json
{
  "total_volume": 45000.50,
  "transaction_count": 1200,
  "error_rate": "0.02%"
}
```

### 4.4 PATCH `/v1/users/{userId}/role`
**Description:** Update the RBAC role of a user.
- **Request:** `PATCH /v1/users/user_554/role`
- **Body:** `{ "role": "RegionalManager" }`
- **Response (200 OK):**
```json
{ "userId": "user_554", "new_role": "RegionalManager", "updated_at": "2023-10-24T11:00:00Z" }
```

### 4.5 GET `/v1/health/system`
**Description:** System health check for the Vanguard network.
- **Request:** `GET /v1/health/system`
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "legacy_bridge": "operational"
}
```

### 4.6 POST `/v1/auth/mfa/verify`
**Description:** Verify the MFA token for administrative access.
- **Request:** `POST /v1/auth/mfa/verify`
- **Body:** `{ "userId": "user_123", "token": "554210" }`
- **Response (200 OK):**
```json
{ "authenticated": true, "session_token": "eyJhbG..." }
```

### 4.7 DELETE `/v1/devices/{id}`
**Description:** Decommission an IoT device.
- **Request:** `DELETE /v1/devices/dev_9921`
- **Response (204 No Content):** `(Empty Body)`

### 4.8 GET `/v1/sandbox/status`
**Description:** Check the current state of the sandbox environment.
- **Request:** `GET /v1/sandbox/status`
- **Response (200 OK):**
```json
{ "environment": "sandbox", "data_freshness": "2023-10-24T00:00:00Z", "api_limit_remaining": 500 }
```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15 instance. We use a mix of structured relations and JSONB for flexibility in device configurations.

### 5.1 Tables and Relationships

1.  **`users`**: Core user account data.
    - `id` (UUID, PK), `email` (String, Unique), `password_hash` (String), `mfa_secret` (String), `created_at` (Timestamp).
2.  **`roles`**: Defined roles for RBAC.
    - `id` (Int, PK), `role_name` (String, Unique) [e.g., 'SuperAdmin'].
3.  **`user_roles`**: Mapping table for users and roles.
    - `user_id` (UUID, FK -> users.id), `role_id` (Int, FK -> roles.id).
4.  **`devices`**: The inventory of IoT hardware.
    - `id` (String, PK), `serial_number` (String, Unique), `firmware_version` (String), `status` (Enum: active, inactive, error), `last_ping` (Timestamp).
5.  **`device_configs`**: Detailed configuration for each device.
    - `device_id` (String, PK, FK -> devices.id), `settings` (JSONB), `updated_at` (Timestamp).
6.  **`regions`**: Physical retail zones.
    - `id` (Int, PK), `region_name` (String), `timezone` (String).
7.  **`region_devices`**: Mapping devices to regions.
    - `region_id` (Int, FK -> regions.id), `device_id` (String, FK -> devices.id).
8.  **`transactions`**: PCI DSS encrypted transaction records.
    - `id` (UUID, PK), `device_id` (String, FK -> devices.id), `encrypted_payload` (Text), `amount` (Decimal), `timestamp` (Timestamp).
9.  **`audit_logs`**: Traceability for all system changes.
    - `id` (BigInt, PK), `user_id` (UUID, FK -> users.id), `action` (String), `entity_id` (String), `timestamp` (Timestamp).
10. **`dashboard_layouts`**: Persisted user interface preferences.
    - `user_id` (UUID, PK, FK -> users.id), `layout_json` (JSONB), `updated_at` (Timestamp).

### 5.2 Critical Performance Note
Due to the volume of `transactions` and `audit_logs` tables, 30% of queries bypass Prisma and use raw SQL via `prisma.$queryRaw` to implement specific indexing strategies (e.g., BRIN indexes for timestamps) that the ORM does not natively optimize.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Vanguard utilizes a three-tier environment strategy to ensure the "zero downtime" requirement.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature development.
- **Deployment:** Automated pushes to branch-specific Vercel previews.
- **Data:** Mocked data and a shared development PostgreSQL instance.
- **Access:** All 20+ team members.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation and QA.
- **Deployment:** Mirrored production configuration.
- **Data:** Anonymized production snapshot.
- **Access:** QA team, Amira Oduya, and Product Designers.
- **Special Note:** This is where the Sandbox API environment is hosted.

#### 6.1.3 Production (Prod)
- **Purpose:** Live retail operations.
- **Deployment:** Canary releases via LaunchDarkly.
- **Data:** Live, encrypted PCI DSS data.
- **Access:** Restricted to DevOps (Rosa Costa) and Tech Lead (Amira Oduya).

### 6.2 CI/CD Pipeline
The pipeline is triggered via GitHub Actions. 
1. **Build Phase:** TypeScript compilation and linting.
2. **Test Phase:** Unit and integration tests.
3. **Deploy Phase:** Push to Vercel.
4. **Activation Phase:** Feature flags in LaunchDarkly are gradually toggled from 1% $\rightarrow$ 10% $\rightarrow$ 50% $\rightarrow$ 100% of the retail fleet.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** Jest and Vitest.
- **Scope:** Pure functions, utility classes, and individual React components.
- **Requirement:** 80% code coverage for the `auth` and `transaction` modules.

### 7.2 Integration Testing
- **Tooling:** Supertest and Prisma Mock.
- **Scope:** API endpoint validation and database transaction flows.
- **Focus:** Ensuring that raw SQL queries return the same results as the Prisma ORM equivalents.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys (e.g., "Admin updates device config" $\rightarrow$ "Device receives update" $\rightarrow$ "Dashboard reflects change").
- **Frequency:** Run on every merge request to the `main` branch.

### 7.4 PCI DSS Compliance Testing
A quarterly penetration test is conducted by an external third party to verify the isolation of the credit card processing layer. This includes "white-box" testing of the encrypted payload handlers.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotation | High | High | Develop a fallback architecture and maintain a detailed "Project Charter" signed by the executive board to ensure continuity. |
| R-02 | Primary vendor EOL | Medium | Critical | Raise as a primary blocker in the next board meeting; begin evaluating alternative vendors for the hardware bridge. |
| R-03 | Third-party API Rate Limits | High | Medium | Implement aggressive caching in the staging environment and request a limit increase from the vendor. |
| R-04 | Migration instability (Raw SQL) | Medium | High | Implement strict database migration versioning and manual review for any raw SQL changes. |
| R-05 | Team Cohesion/Trust | Medium | Low | Bi-weekly "sprint retros" and collaborative architecture workshops to build trust. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required.
- **Medium/High:** Monitoring and mitigation plan in place.
- **Low:** Accepted risk.

---

## 9. TIMELINE

### 9.1 Phase Overview
The project is divided into three primary phases, mapping to the defined milestones.

#### Phase 1: The Foundation (Current $\rightarrow$ 2026-07-15)
- **Focus:** Core API development, PCI DSS compliance setup, and the legacy bridge.
- **Key Dependency:** Resolution of the third-party API rate limit blocker.
- **Target:** Production Launch (Milestone 1).

#### Phase 2: Optimization (2026-07-16 $\rightarrow$ 2026-09-15)
- **Focus:** Fine-tuning the micro-frontend performance, finalizing the customizable dashboard.
- **Key Dependency:** Successful canary rollout of the first 1,000 devices.
- **Target:** Architecture Review Complete (Milestone 2).

#### Phase 3: Stabilization (2026-09-16 $\rightarrow$ 2026-11-15)
- **Focus:** Bug fixing, localization polish, and offline-mode optimization.
- **Key Dependency:** User feedback from the first 10k active users.
- **Target:** Post-launch Stability Confirmed (Milestone 3).

### 9.2 Gantt-Style Dependency Map
`[Dev Auth] $\rightarrow$ [API Gateway] $\rightarrow$ [Canary Deploy] $\rightarrow$ [Production Launch]`
`[UI Design] $\rightarrow$ [Dashboard Widget Dev] $\rightarrow$ [UAT] $\rightarrow$ [Production Launch]`
`[Legacy Audit] $\rightarrow$ [Raw SQL Optimizations] $\rightarrow$ [Architecture Review]`

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment (2023-11-05)
- *Attendees:* Amira, Rosa, Camila, Veda.
- **Notes:**
  - Micro-frontends vs Monolith.
  - Agreed on Vercel.
  - Rosa worried about DB migrations.
  - Amira says raw SQL is necessary for the p95 target.
  - Action: Veda to map out legacy data fields.

### Meeting 2: Blocker Sync (2023-12-12)
- *Attendees:* Amira, Rosa, Veda.
- **Notes:**
  - API rate limits hitting.
  - Sandbox is broken.
  - Vendor says "wait 2 weeks."
  - Amira: "Cannot wait. We need a mock server."
  - Decision: Build internal mock API for testing.

### Meeting 3: UX Review (2024-01-20)
- *Attendees:* Amira, Camila, Veda.
- **Notes:**
  - Dashboard too cluttered.
  - Camila wants drag-and-drop.
  - Amira says it's a launch blocker.
  - Veda thinks it will slow down the p95.
  - Decision: Use Zustand for state, keep the API calls lean.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salaries for internal staff and contractor fees (Veda Park). |
| **Infrastructure** | $60,000 | Vercel Enterprise, PostgreSQL Managed Instance, Redis Cloud. |
| **Tools & Licenses** | $30,000 | LaunchDarkly, PCI Compliance Audit, GitHub Enterprise. |
| **Contingency** | $30,000 | Reserve for emergency vendor pivots or hardware replacement. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Performance Optimization Log
Due to the 30% raw SQL bypass, the following queries are handled outside of Prisma to ensure the <200ms p95 response:
- **Telemetry Aggregation:** `SELECT device_id, AVG(temp) FROM telemetry WHERE timestamp > ... GROUP BY device_id`. (Prisma's `groupBy` was found to be 4x slower).
- **Transaction Batching:** Bulk inserts of encrypted credit card payloads are performed via `COPY` commands to reduce I/O overhead.

### Appendix B: PCI DSS Level 1 Compliance Checklist
- [x] **Network Segmentation:** Production environment is logically separated from Dev/Staging.
- [x] **Encryption at Rest:** All `transactions.encrypted_payload` fields use AES-256.
- [x] **Encryption in Transit:** TLS 1.3 mandatory for all device-to-cloud communication.
- [x] **Access Control:** MFA enabled for all privileged accounts.
- [ ] **Quarterly Audit:** Scheduled for 2026-06-01.