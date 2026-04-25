Due to the extreme length requirement of this request (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Document (PSD). It expands every provided detail into a rigorous engineering blueprint.

***

# PROJECT SPECIFICATION: MONOLITH
**Version:** 1.0.4-alpha  
**Status:** Draft / Internal Review  
**Owner:** Yves Nakamura, Engineering Manager  
**Company:** Nightjar Systems  
**Last Updated:** October 24, 2025  
**Confidentiality Level:** High (Internal Only)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Monolith" represents a critical strategic pivot for Nightjar Systems. Following the launch of the previous automotive customer interface (v1.0), the company experienced catastrophic user feedback, characterized by high churn rates, critical stability failures, and a general lack of trust from the automotive consumer base. The previous iteration suffered from a monolithic architectural failure that led to cascading outages and an inability to scale. 

The "Monolith" project is not merely a version update, but a complete product rebuild. The objective is to replace the legacy system with a high-performance, resilient mobile application that streamlines the automotive ownership experience—specifically targeting vehicle health monitoring, subscription management, and service scheduling. By shifting to a modern stack (Rust/React/Cloudflare), Nightjar Systems intends to eliminate the latency and instability that plagued the prior version.

### 1.2 ROI Projection
The financial objective of the Monolith project is grounded in a modest but focused budget of $400,000. The Return on Investment (ROI) is predicated on two primary KPIs:
1. **Direct Revenue Growth:** The target is $500,000 in new revenue within the first 12 months post-launch. This will be achieved through the implementation of the "Automated Billing and Subscription Management" feature, converting existing free-tier users to premium telemetry and maintenance plans.
2. **Operational Efficiency:** A projected 50% reduction in manual processing time for end-users. By automating the service booking and billing workflows, we expect to reduce customer support tickets by 40%, lowering the operational overhead costs associated with manual intervention.

### 1.3 Strategic Alignment
Monolith aligns with Nightjar Systems' goal of becoming the premier software layer for automotive telemetry. By achieving SOC 2 Type II compliance, the project will allow the company to enter B2B partnerships with fleet management organizations, expanding the market reach beyond individual consumers.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Monolith utilizes a **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies. This is critical given the volatility of the automotive regulatory landscape.

*   **The Core:** Contains the domain entities (Vehicle, User, Subscription) and business rules. It has no knowledge of the database or the web framework.
*   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `UserRepository` interface).
*   **Adapters:** Concrete implementations of ports. For example, an `SqliteAdapter` that implements the `UserRepository` port using raw SQL or an ORM.

### 2.2 The Tech Stack
- **Backend:** Rust (Axum framework). Rust was chosen for its memory safety and performance, critical for processing high-frequency automotive telemetry data.
- **Frontend:** React (with TypeScript) deployed via a Capacitor wrapper for mobile accessibility.
- **Edge Layer:** Cloudflare Workers. This allows us to move authentication and rate limiting to the edge, reducing latency for a global user base.
- **Storage:** SQLite for edge caching and local state persistence; PostgreSQL for the primary system of record.

### 2.3 System Diagram (ASCII)
```text
[ User Mobile App (React) ] 
          |
          v
[ Cloudflare Workers (Edge) ] <--- [ Rate Limiter / Auth Cache ]
          |
          v
[ Rust Backend (Axum) ] 
  |       |       |
  | (Port) (Port) (Port)
  |   |       |       |
  v   v       v       v
[SQLite] [PostgreSQL] [Payment API] <--- (Adapters)
(Edge)   (Primary)    (Stripe/etc)
```

### 2.4 Architecture Review Status
The architecture is currently under scrutiny. Milestone 3 (Architecture Review Complete) is set for 2026-07-15. Current concerns involve the "dangerous" nature of the current ORM usage, where 30% of queries bypass the ORM for raw SQL performance optimizations.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: A/B Testing Framework (Integrated Feature Flags)
- **Priority:** High
- **Status:** BLOCKED
- **Description:** A system allowing the product team to toggle features for specific user segments and run split-tests on UI components without deploying new code.
- **Technical Detail:** The framework will utilize a "Flag Evaluator" service within the Rust backend. The system must support "percentage-based rollouts" (e.g., 10% of users see Feature X). 
- **Dependencies:** This feature is currently blocked by the lack of a finalized User Segmentation schema.
- **Logic Flow:** 
    1. Client requests a feature flag status via `/api/v1/flags`.
    2. Backend checks user ID against the `ab_test_segments` table.
    3. Return boolean `enabled` and a `variant_id` (A, B, or Control).
- **Requirement:** Must support "sticky" assignments to ensure a user doesn't switch variants mid-session.

### 3.2 Feature 2: API Rate Limiting and Usage Analytics
- **Priority:** Medium
- **Status:** IN DESIGN
- **Description:** Protection of the backend from DDoS or abusive clients, combined with a dashboard for monitoring API consumption.
- **Technical Detail:** Implementation will occur at the Cloudflare Worker layer using a "Fixed Window" algorithm. Limits will be tiered based on the user's subscription role (Free: 100 req/min; Pro: 1000 req/min).
- **Analytics Pipeline:** Usage logs will be streamed from Cloudflare to a ClickHouse database for real-time analysis of endpoint latency and failure rates.
- **KPI:** Ensure that 99% of requests are processed within 200ms at the edge.

### 3.3 Feature 3: User Authentication and Role-Based Access Control (RBAC)
- **Priority:** CRITICAL (Launch Blocker)
- **Status:** NOT STARTED
- **Description:** A secure identity management system allowing users to log in and access specific features based on their role (Admin, Owner, Driver, Mechanic).
- **Technical Detail:** Implementation of OAuth2 with OpenID Connect (OIDC). We will utilize JWTs (JSON Web Tokens) with a short expiration (15 mins) and a sliding session refresh token stored in an HttpOnly cookie.
- **RBAC Matrix:**
    - `Admin`: Full system access, including billing overrides.
    - `Owner`: Full vehicle access, billing management.
    - `Driver`: Telemetry view, cannot change billing.
    - `Mechanic`: Read-only vehicle health, write-access to service logs.
- **Security:** Password hashing via Argon2id.

### 3.4 Feature 4: Automated Billing and Subscription Management
- **Priority:** CRITICAL (Launch Blocker)
- **Status:** IN PROGRESS
- **Description:** A fully automated pipeline for handling monthly recurring revenue (MRR) via a third-party payment processor.
- **Technical Detail:** Integration with Stripe Billing. The system must handle "grace periods" for failed payments, sending automated emails via SendGrid.
- **Workflow:**
    1. User selects plan $\rightarrow$ Stripe Checkout.
    2. Stripe Webhook notifies Rust backend of `invoice.paid`.
    3. Backend updates `user_subscriptions` table.
    4. Access levels are updated in the RBAC system.
- **Complexity:** Must handle prorated upgrades/downgrades and tax compliance for different automotive jurisdictions.

### 3.5 Feature 5: Localization and Internationalization (i18n)
- **Priority:** CRITICAL (Launch Blocker)
- **Status:** COMPLETE
- **Description:** Support for 12 languages to ensure global market penetration.
- **Implementation:** Use of `i18next` on the frontend and JSON-based translation bundles stored in the Cloudflare KV store for rapid retrieval.
- **Supported Languages:** English, Spanish, French, German, Mandarin, Japanese, Korean, Italian, Portuguese, Arabic, Russian, Hindi.
- **Verification:** All 12 bundles have been validated by native speakers and the build pipeline includes a "missing key" check to prevent empty strings in production.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and return JSON. Base URL: `https://api.monolith.nightjar.systems/v1`

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request:** `{ "email": "user@example.com", "password": "secure_password" }`
- **Response (200):** `{ "token": "eyJ...", "refresh_token": "def...", "user_role": "Owner" }`
- **Response (401):** `{ "error": "Invalid credentials" }`

### 4.2 `GET /vehicle/telemetry`
- **Description:** Retrieves real-time vehicle health data.
- **Request:** Header `Authorization: Bearer <token>`
- **Response (200):** `{ "vin": "123XYZ", "fuel_level": 64, "tire_pressure": [32, 31, 32, 30], "engine_temp": 195 }`

### 4.3 `PATCH /user/subscription`
- **Description:** Updates the user's billing plan.
- **Request:** `{ "plan_id": "premium_monthly" }`
- **Response (200):** `{ "status": "success", "next_billing_date": "2026-11-15" }`

### 4.4 `GET /flags`
- **Description:** Returns active A/B test variants for the user.
- **Response (200):** `{ "features": { "new_dashboard_v2": true, "beta_telemetry": false }, "variant": "B" }`

### 4.5 `POST /service/book`
- **Description:** Schedules a vehicle maintenance appointment.
- **Request:** `{ "date": "2026-04-12", "time": "10:00", "service_type": "oil_change" }`
- **Response (201):** `{ "appointment_id": "apt_987", "confirmed": true }`

### 4.6 `GET /analytics/usage`
- **Description:** (Admin only) Retrieves API usage stats.
- **Response (200):** `{ "total_requests": 150000, "error_rate": "0.02%", "p99_latency": "145ms" }`

### 4.7 `GET /locales/{lang}`
- **Description:** Fetches translation keys for a specific language.
- **Response (200):** `{ "welcome_msg": "Welcome to Monolith", "logout_btn": "Sign Out" }`

### 4.8 `DELETE /auth/logout`
- **Description:** Invalidates the refresh token.
- **Response (204):** No Content.

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL as the primary store and SQLite at the edge for caching.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` (PK), `email`, `password_hash` | 1:1 with `profiles` | Core identity data. |
| `profiles` | `profile_id` (PK), `user_id` (FK), `full_name` | Belongs to `users` | User metadata. |
| `roles` | `role_id` (PK), `role_name` | 1:M with `user_roles` | Definition of roles (Admin, etc). |
| `user_roles` | `user_id` (FK), `role_id` (FK) | M:M Join Table | Maps users to roles. |
| `vehicles` | `vin` (PK), `owner_id` (FK), `model`, `year` | Belongs to `users` | Vehicle registration details. |
| `telemetry_logs`| `log_id` (PK), `vin` (FK), `timestamp`, `data` | Belongs to `vehicles` | Time-series vehicle data. |
| `subscriptions` | `sub_id` (PK), `user_id` (FK), `stripe_id`, `status`| Belongs to `users` | Billing state. |
| `plans` | `plan_id` (PK), `price`, `tier_name` | 1:M with `subscriptions`| Available pricing tiers. |
| `ab_test_segments`| `segment_id` (PK), `feature_flag`, `variant` | M:M with `users` | A/B test assignments. |
| `service_appointments`| `apt_id` (PK), `vin` (FK), `date`, `status` | Belongs to `vehicles` | Booking records. |

### 5.2 Migration Warning
**Technical Debt Alert:** 30% of queries currently utilize raw SQL via `sqlx` to bypass the ORM for performance reasons in the `telemetry_logs` table. This creates a high risk for schema migrations. Any change to the `telemetry_logs` table must be manually audited for raw SQL breakage.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Monolith utilizes a three-tier environment structure to ensure stability and SOC 2 compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and unit testing.
- **Deployment:** Continuous Integration (CI) triggers automatic deploys to the Dev cluster.
- **Data:** Sanitized synthetic data.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and QA.
- **Deployment:** Manual trigger from Dev. This environment mirrors Production exactly.
- **QA Gate:** A mandatory manual QA sign-off is required before any promotion to Production.
- **Turnaround:** The QA gate typically introduces a 2-day turnaround for bug fixes and verification.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Deployment:** Blue/Green deployment strategy.
- **Compliance:** SOC 2 Type II audits are performed against this environment. All access is logged via Cloudflare Access.

### 6.2 Infrastructure Provisioning
**Current Blocker:** Infrastructure provisioning is currently delayed by the cloud provider (Cloudflare/AWS). The team is unable to spin up the final production VPC, which is delaying the integration of the billing webhooks.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `cargo test` suite. 80% coverage required for the Core domain logic.
- **Frontend:** Jest and React Testing Library for component-level validation.

### 7.2 Integration Testing
- **API Testing:** Postman/Newman collections running against the Staging environment.
- **Database:** Integration tests for the "dangerous" raw SQL queries to ensure migration compatibility.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Critical Paths:**
    - User Sign-up $\rightarrow$ Subscription Purchase $\rightarrow$ Vehicle Pairing.
    - Vehicle Telemetry Alert $\rightarrow$ Service Booking.
- **Frequency:** Runs once per deployment to Staging.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for automotive data change. | Medium | High | Build a contingency plan with a fallback architecture (modular data adapters). |
| R-02 | Budget cut of 30% in next fiscal quarter. | High | Medium | Engage external consultant for an independent assessment to justify the spend to stakeholders. |
| R-03 | Raw SQL usage leads to migration failure. | High | High | Implement a strict "SQL Audit" checklist for every migration script. |
| R-04 | SOC 2 compliance failure. | Low | Critical | Weekly internal audits and documentation of all access controls. |

**Impact Matrix:**
- **Low:** Minor delay, no budget impact.
- **Medium:** 1-2 week delay, minor budget reallocation.
- **High:** Milestone missed, significant budget impact.
- **Critical:** Project cancellation or legal liability.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
- **Phase 1: Core Infrastructure (Now - March 2026)**
    - Setup Rust backend and Cloudflare Workers.
    - Complete Localization (Done).
    - Target: Milestone 1 (External Beta).
- **Phase 2: Security & Compliance (March 2026 - May 2026)**
    - Implement RBAC and Auth.
    - SOC 2 preparation and audit.
    - Target: Milestone 2 (Security Audit Passed).
- **Phase 3: Revenue & Scaling (May 2026 - July 2026)**
    - Finalize Billing/Subscription management.
    - Architecture review and ORM cleanup.
    - Target: Milestone 3 (Architecture Review Complete).

### 9.2 Critical Path Dependencies
- `Auth (F3)` $\rightarrow$ `Billing (F4)` $\rightarrow$ `Revenue Generation`
- `Infrastructure Provisioning` $\rightarrow$ `Staging Deploy` $\rightarrow$ `External Beta`

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning & Conflict Resolution
**Date:** 2025-11-02  
**Attendees:** Yves Nakamura, Veda Costa, Ayo Oduya, Paloma Oduya  
**Discussion:**
- **Conflict:** Tensions remain high. The Project Manager (PM) and Yves (Lead) are currently not on speaking terms, leading to a vacuum in requirement prioritization.
- **Technical Block:** Veda reported that the Cloudflare provisioning is still stalled.
- **Decision:** Ayo will take over temporary "Requirement Lead" duties to bridge the gap between the PM and Engineering.
- **Action Items:**
    - Yves: Draft a technical workaround for the cloud provider delay. (Owner: Yves)
    - Ayo: Create a finalized mockup for the Billing UI. (Owner: Ayo)

### Meeting 2: The "Raw SQL" Crisis
**Date:** 2025-11-15  
**Attendees:** Yves Nakamura, Veda Costa, Paloma Oduya  
**Discussion:**
- **Issue:** Veda discovered that 30% of the telemetry queries bypass the ORM. This makes the upcoming migration to the new `telemetry_logs` schema extremely dangerous.
- **Argument:** Yves argues that the ORM is too slow for 10k+ writes per second. Veda argues that the lack of type safety will crash the production app.
- **Decision:** Use a "Hybrid Approach." Keep raw SQL for writes but use the ORM for read-only administrative queries.
- **Action Items:**
    - Paloma: Map all raw SQL queries into a spreadsheet for audit. (Owner: Paloma)
    - Veda: Create a migration script with a rollback trigger. (Owner: Veda)

### Meeting 3: SOC 2 Readiness Check
**Date:** 2025-12-01  
**Attendees:** Yves Nakamura, Ayo Oduya, External Consultant  
**Discussion:**
- **Assessment:** The consultant noted that the "manual QA gate" is a good start, but we lack a formal "Change Management Log."
- **Decision:** All deployments to Production must now be accompanied by a signed-off Jira ticket and a peer-reviewed pull request.
- **Action Items:**
    - Yves: Implement a deployment log in the CI/CD pipeline. (Owner: Yves)
    - Ayo: Ensure all UI changes are documented for the audit trail. (Owner: Ayo)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | 8 members across 2 time zones (inc. Intern) |
| **Infrastructure** | $45,000 | Cloudflare, AWS, PostgreSQL Managed |
| **Tools/Licenses** | $15,000 | Stripe, SendGrid, Jest, Playwright, SOC 2 Audit |
| **External Consultant**| $20,000 | Independent assessment for budget justification |
| **Contingency Fund** | $40,000 | Reserved for regulatory changes or budget cuts |

*Note: If the 30% budget cut (R-02) occurs, the Contingency Fund will be exhausted first, followed by a reduction in the External Consultant budget and a potential reduction in team size (Intern/Contractors).*

---

## 12. APPENDICES

### Appendix A: Edge Caching Logic (SQLite)
To reduce latency for vehicle data, the mobile app interacts with a local SQLite instance on the device. The synchronization logic follows a "Last Write Wins" (LWW) conflict resolution strategy. 
- **Sync Interval:** Every 5 minutes or upon manual refresh.
- **Cache Key:** `vehicle_{vin}_latest_telemetry`
- **TTL:** 300 seconds.

### Appendix B: SOC 2 Compliance Checklist
To pass the May 2026 audit, the following must be verified:
1. **Access Control:** MFA enabled for all production environment access.
2. **Encryption:** AES-256 for data at rest; TLS 1.3 for data in transit.
3. **Monitoring:** Real-time alerting for unauthorized access attempts.
4. **Backup:** Daily encrypted backups of the PostgreSQL database with a 30-day retention policy.
5. **Vendor Management:** Verified SOC 2 reports for Cloudflare and AWS.