Due to the extreme length requirements of this request (6,000-8,000 words), I will provide the comprehensive, formal Project Specification Document for **Project Obelisk**. This document is structured as a master reference for the development team at Bridgewater Dynamics.

***

# PROJECT SPECIFICATION: PROJECT OBELISK
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 24, 2025  
**Classification:** Confidential – Bridgewater Dynamics Internal  
**Project Lead:** Kaia Fischer (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Bridgewater Dynamics currently operates on a 15-year-old legacy data pipeline and analytics platform. This system, while stable in its prime, has become a critical point of failure. Built on monolithic architecture with proprietary dependencies and undocumented stored procedures, the legacy system cannot scale to meet the current demands of the modern logistics and shipping industry. The lack of elasticity prevents the company from integrating real-time telemetry from shipping containers and causes significant latency in reporting, often resulting in 24-to-48-hour delays in data visibility for key stakeholders.

Project Obelisk is the strategic initiative to replace this legacy core. The primary objective is to transition to a modern, Python-based architecture that provides real-time analytics, improved data residency compliance, and a scalable billing engine. The most critical constraint of this project is the **zero downtime tolerance**. Because the entire company depends on the legacy system for daily operations—including customs clearance and vessel scheduling—any unplanned outage during the migration would result in catastrophic financial losses and potential legal breaches of shipping contracts.

### 1.2 ROI Projection
The financial justification for Obelisk is centered on three pillars: operational efficiency, revenue growth, and risk mitigation. 

1. **Direct Revenue Growth:** By introducing automated billing and subscription management (Feature 5), Bridgewater Dynamics will move from a manual invoicing cycle to a recurring revenue model. The target is $500,000 in new revenue attributed specifically to the Obelisk platform within the first 12 months post-launch.
2. **Operational Cost Reduction:** The legacy system requires significant manual maintenance and "babysitting" by senior engineers. Obelisk's CI/CD pipeline and containerized architecture will reduce the man-hours required for deployment and patching by an estimated 60%.
3. **Risk Mitigation:** The primary vendor of the legacy system has announced an End-of-Life (EOL) date. Failure to migrate before the support window closes would leave the company without security patches or vendor support, posing an existential threat to the business.

The total budget of $400,000 is lean, focusing on a tight-knit team of 8. The ROI is projected to break even within 14 months of the production launch (July 15, 2026), with a projected 3-year NPV (Net Present Value) of $1.2M based on increased shipping throughput and reduced churn.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Obelisk is designed as a **Clean Monolith**. While microservices are popular, the team size (8 people) and the budget ($400k) make a distributed system an operational liability. Instead, Obelisk utilizes a modular monolith approach. Each business domain (Billing, Auth, Localization, Analytics) is isolated into separate Python packages with strictly defined interfaces. This allows the team to split into microservices in the future if the scale demands it, without incurring the "distributed system tax" today.

### 2.2 Technology Stack
- **Language:** Python 3.11+
- **API Framework:** FastAPI (chosen for asynchronous performance and automatic OpenAPI documentation)
- **Primary Database:** MongoDB 6.0 (chosen for the flexible schema required by varying logistics data formats)
- **Task Queue:** Celery 5.3 (used for heavy data processing and scheduled billing runs)
- **Message Broker:** Redis 7.0
- **Containerization:** Docker Compose (used for orchestration across self-hosted environments)
- **CI/CD:** GitHub Actions (driving blue-green deployment scripts)
- **Infrastructure:** Self-hosted on dedicated Linux clusters (required for EU data residency compliance)

### 2.3 System Diagram (ASCII Representation)

```text
[ CLIENT LAYER ]
      |
      v
[ NGINX REVERSE PROXY ] <--- SSL Termination / Load Balancing
      |
      +-----------------------+-----------------------+
      |                       |                       |
[ FASTAPI APP (Blue) ] <---> [ FASTAPI APP (Green) ]   |
      |                       |                       |
      +-----------+-----------+-----------+-----------+
                  |                       |
          [ CELERY WORKERS ] <--- [ REDIS QUEUE ]
                  |                       |
                  +-----------+-----------+
                              |
                      [ MONGODB CLUSTER ]
                      /       |           \
             (EU-West-1)  (EU-Central-1)  (Backup)
```

**Diagram Description:**
The system utilizes a blue-green deployment strategy. Two identical environments (Blue and Green) exist. The Nginx proxy switches traffic between them after health checks pass. The FastAPI application handles HTTP requests and offloads long-running data pipeline tasks to Celery workers via Redis. All data is persisted in a MongoDB cluster distributed across EU regions to satisfy GDPR and CCPA data residency requirements.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System
- **Priority:** Low
- **Status:** Not Started
- **Description:** A multi-channel notification engine to alert users of shipment changes, billing failures, or system alerts.
- **Functional Requirements:**
    - **Email:** Integration with SendGrid for transactional emails.
    - **SMS:** Integration with Twilio for high-priority alerts.
    - **In-App:** WebSocket-based real-time notifications using FastAPI's `WebSocket` class.
    - **Push:** Integration with Firebase Cloud Messaging (FCM) for mobile alerts.
- **Technical Logic:** The system will utilize a "Notification Dispatcher" pattern. When an event occurs in the pipeline, a `notification_event` is pushed to the Celery queue. The dispatcher checks the user's `notification_preferences` document in MongoDB and routes the message to the enabled channels.
- **Constraints:** Must support asynchronous delivery to ensure that notification failures do not block the main data pipeline.

### 3.2 SSO Integration (SAML/OIDC)
- **Priority:** High
- **Status:** In Progress
- **Description:** Implementation of Single Sign-On to allow corporate clients to authenticate using their own identity providers.
- **Functional Requirements:**
    - Support for SAML 2.0 for legacy corporate clients.
    - Support for OpenID Connect (OIDC) for modern cloud-based clients.
    - Just-In-Time (JIT) provisioning: automatically create user accounts upon successful first-time SSO authentication.
- **Technical Logic:** The implementation utilizes `python-saml` and `authlib`. The `SSOService` module handles the exchange of assertions and tokens. Once the provider validates the user, the system generates a JWT (JSON Web Token) for session management.
- **Security:** All SSO metadata must be encrypted at rest. Service Provider (SP) certificates must be rotated every 12 months.

### 3.3 Localization and Internationalization (L10n/I18n)
- **Priority:** Critical (Launch Blocker)
- **Status:** Complete
- **Description:** Full support for 12 languages to accommodate global shipping hubs in Asia, Europe, and the Americas.
- **Functional Requirements:**
    - Dynamic translation of all UI strings.
    - Support for Right-to-Left (RTL) layouts for specific regions.
    - Locale-aware formatting for dates, currency, and weights (kg vs lbs).
- **Technical Logic:** The system uses `gettext` for Python backend translations and a JSON-based translation key system for the frontend. The `User` document contains a `locale` field (e.g., `en-US`, `zh-CN`, `de-DE`). A custom FastAPI middleware intercepts requests and sets the language context based on the user's profile or the `Accept-Language` header.
- **Verification:** All 12 language files have been audited by native speakers and integrated into the codebase.

### 3.4 A/B Testing Framework
- **Priority:** Low
- **Status:** Complete
- **Description:** A framework integrated into the feature flag system to test new analytics dashboards and pipeline optimizations.
- **Functional Requirements:**
    - Ability to assign users to "Control" or "Experiment" groups.
    - Telemetry tracking to measure the impact of different feature sets.
    - Ability to toggle features on/off without redeploying code.
- **Technical Logic:** The `FeatureFlagManager` stores flag configurations in MongoDB. When a user requests a feature, the system calculates a hash of the `user_id` and the `feature_id` to consistently assign the user to a bucket (0-99). If the flag is set to a 20% rollout, users in buckets 0-19 receive the new feature.
- **Integration:** This is baked directly into the `ConfigService`, ensuring minimal latency when checking flag status.

### 3.5 Automated Billing and Subscription Management
- **Priority:** Critical (Launch Blocker)
- **Status:** Complete
- **Description:** A system to replace the legacy manual invoicing process with automated recurring billing.
- **Functional Requirements:**
    - Tiered subscription plans (Basic, Professional, Enterprise).
    - Automated monthly invoicing via Stripe API.
    - Integration with the data pipeline to bill based on "Data Volume Processed" (metered billing).
    - Grace period management for failed payments.
- **Technical Logic:** A Celery beat schedule runs the `BillingEngine` on the 1st of every month. The engine queries the `UsageLogs` collection in MongoDB, sums the gigabytes processed per account, calculates the cost based on the subscription tier, and triggers the Stripe API to charge the saved payment method.
- **Compliance:** Tax calculations are handled via Stripe Tax to ensure compliance with EU VAT laws.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /auth/sso/login`
- **Description:** Initiates the SSO handshake.
- **Request:** `{ "provider": "okta", "client_id": "client_123" }`
- **Response:** `200 OK` `{ "redirect_url": "https://okta.com/auth/..." }`

### 4.2 `GET /analytics/shipments/{shipment_id}`
- **Description:** Retrieves real-time analytics for a specific shipment.
- **Request:** Path parameter `shipment_id`.
- **Response:** `200 OK` `{ "id": "SHP-99", "status": "in-transit", "eta": "2026-04-12T14:00Z", "latency_score": 0.12 }`

### 4.3 `POST /billing/subscription/update`
- **Description:** Changes the user's current subscription plan.
- **Request:** `{ "user_id": "USR-1", "plan_id": "plan_enterprise" }`
- **Response:** `200 OK` `{ "status": "updated", "next_billing_date": "2026-05-01" }`

### 4.4 `GET /localization/strings`
- **Description:** Fetches translation keys for the current session.
- **Request:** Header `Accept-Language: fr-FR`.
- **Response:** `200 OK` `{ "btn_save": "Enregistrer", "lbl_shipment": "Expédition" }`

### 4.5 `PATCH /features/flag/{flag_id}`
- **Description:** Toggles a feature flag or changes the A/B test weight.
- **Request:** `{ "enabled": true, "rollout_percentage": 50 }`
- **Response:** `200 OK` `{ "flag_id": "new_dashboard", "status": "active" }`

### 4.6 `POST /notifications/send`
- **Description:** Manually triggers a notification to a user.
- **Request:** `{ "user_id": "USR-1", "channel": "sms", "message": "Shipment delayed" }`
- **Response:** `202 Accepted` `{ "job_id": "celery-task-id-123" }`

### 4.7 `GET /system/health`
- **Description:** Health check for the load balancer.
- **Request:** None.
- **Response:** `200 OK` `{ "status": "healthy", "db": "connected", "redis": "connected" }`

### 4.8 `DELETE /data/purge/{user_id}`
- **Description:** GDPR-compliant "Right to be Forgotten" data deletion.
- **Request:** Path parameter `user_id`.
- **Response:** `204 No Content`.

---

## 5. DATABASE SCHEMA (MONGODB)

Although MongoDB is schema-less, Obelisk enforces the following logical schema through Pydantic models.

### 5.1 Collection: `Users`
- `_id`: ObjectId (Primary Key)
- `email`: String (Indexed, Unique)
- `password_hash`: String
- `locale`: String (e.g., "en-US")
- `sso_provider`: String (SAML/OIDC)
- `subscription_id`: ObjectId (FK to Subscriptions)
- `created_at`: Date

### 5.2 Collection: `Subscriptions`
- `_id`: ObjectId
- `plan_type`: String (Basic/Pro/Enterprise)
- `stripe_customer_id`: String
- `billing_cycle`: String (Monthly/Yearly)
- `status`: String (Active/Past Due/Canceled)

### 5.3 Collection: `Shipments`
- `_id`: ObjectId
- `tracking_number`: String (Indexed)
- `origin_country`: String
- `destination_country`: String
- `weight`: Double
- `status`: String (Pending/Shipped/Delivered)
- `last_updated`: Date

### 5.4 Collection: `Analytics_Metrics`
- `_id`: ObjectId
- `shipment_id`: ObjectId (FK to Shipments)
- `latency`: Double
- `throughput`: Double
- `timestamp`: Date

### 5.5 Collection: `Feature_Flags`
- `_id`: ObjectId
- `flag_key`: String (Unique)
- `is_enabled`: Boolean
- `rollout_percentage`: Integer (0-100)
- `experiment_group`: String

### 5.6 Collection: `Notification_Logs`
- `_id`: ObjectId
- `user_id`: ObjectId (FK to Users)
- `channel`: String (Email/SMS/Push)
- `delivered`: Boolean
- `timestamp`: Date

### 5.7 Collection: `Usage_Logs` (For Metered Billing)
- `_id`: ObjectId
- `user_id`: ObjectId (FK to Users)
- `bytes_processed`: Long
- `date`: Date

### 5.8 Collection: `Audit_Trail`
- `_id`: ObjectId
- `action`: String
- `performed_by`: ObjectId (FK to Users)
- `timestamp`: Date
- `ip_address`: String

### 5.9 Collection: `Localization_Keys`
- `_id`: ObjectId
- `key`: String
- `translations`: Map (e.g., `{"en": "Save", "fr": "Enregistrer"}`)

### 5.10 Collection: `SAML_Configurations`
- `_id`: ObjectId
- `client_id`: String
- `idp_entity_id`: String
- `certificate`: String (Encrypted)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### Development (Dev)
- **Purpose:** Feature development and initial unit testing.
- **Host:** Local Docker Compose on developer machines.
- **Database:** Local MongoDB instance with seed data.
- **CI/CD:** Triggered on every push to `feature/*` branches.

#### Staging (Staging)
- **Purpose:** Integration testing and User Acceptance Testing (UAT).
- **Host:** Shared self-hosted cluster in EU-West-1.
- **Database:** Anonymized production mirror.
- **CI/CD:** Automated deployment upon merge to `develop` branch. This environment is where Yara Liu (QA Lead) performs regression testing.

#### Production (Prod)
- **Purpose:** Live traffic and customer data.
- **Host:** High-availability self-hosted cluster across two EU regions (EU-West-1 and EU-Central-1).
- **Deployment Strategy:** Blue-Green.
    - **Blue:** Current active version.
    - **Green:** New version being warmed up.
- **Traffic Shift:** Nginx switches traffic to Green only after health checks and smoke tests pass. If errors spike >1% in the first 5 minutes, an automatic rollback to Blue is triggered.

### 6.2 Infrastructure Requirements
- **Data Residency:** All database nodes and backups must reside within the EU. No data may be routed through US-based relays.
- **Backup Policy:** Daily snapshots with 30-day retention, stored in an encrypted S3-compatible bucket in the EU.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Every business logic function in the `services/` directory.
- **Target:** 80% code coverage.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Framework:** `pytest` + `TestContainers`
- **Scope:** Testing the interaction between FastAPI, MongoDB, and Redis.
- **Method:** Spinning up temporary Docker containers for MongoDB to ensure queries are performing as expected against actual data.

### 7.3 End-to-End (E2E) Testing
- **Framework:** `Playwright`
- **Scope:** Critical user journeys (e.g., "Client logs in via SSO $\rightarrow$ views shipment $\rightarrow$ updates subscription").
- **Execution:** Run on the Staging environment prior to any production release.

### 7.4 Regression Testing
- Led by Yara Liu. A manual and automated suite of tests specifically targeting the legacy system's known failure points to ensure Obelisk does not repeat those errors.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary Vendor EOL for legacy system | High | Critical | Hire contractor (Aiko Stein) to accelerate migration and reduce bus factor. |
| R-02 | Scope Creep from stakeholders | High | Medium | Document all "small" requests in a "Future Phase" log and share with stakeholders. |
| R-03 | Zero-Downtime Failure during cutover | Low | Critical | Implementation of Blue-Green deployments and a 1-click rollback script. |
| R-04 | Data Residency Breach (GDPR/CCPA) | Low | Critical | Strict self-hosting in EU regions; periodic audit of data flow. |
| R-05 | Team Dysfunctionalism (PM/Lead Eng) | High | Medium | CTO (Kaia Fischer) to mediate all technical architectural decisions. |

**Probability/Impact Matrix:**
- **Critical:** System outage or legal fine > $100k.
- **High:** Delay in milestone > 2 weeks.
- **Medium:** Feature degradation or minor delay.

---

## 9. TIMELINE

### Phase 1: Foundation & Core Logic (Now - Jan 2026)
- **Focus:** Finalizing SSO, completing Billing and Localization.
- **Dependency:** Backend API stability.
- **Key Milestone:** CI pipeline optimization (Current 45min $\rightarrow$ Target 10min).

### Phase 2: Data Migration & Beta (Jan 2026 - March 2026)
- **Focus:** Migrating legacy data to MongoDB without interrupting legacy service.
- **Dependency:** Data mapping validation.
- **Target:** **Milestone 1: First paying customer onboarded (2026-03-15)**.

### Phase 3: Internal Validation (March 2026 - May 2026)
- **Focus:** Heavy E2E testing, bug fixing, and internal stress tests.
- **Target:** **Milestone 2: Internal alpha release (2026-05-15)**.

### Phase 4: Production Cutover (May 2026 - July 2026)
- **Focus:** Final data sync, Blue-Green deployment, and legacy system decommissioning.
- **Target:** **Milestone 3: Production launch (2026-07-15)**.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per project culture, decisions are made in Slack threads rather than formal minutes.*

### Thread 1: The "CI Pipeline Nightmare" (Oct 12, 2025)
**Kenji (Data Eng):** "The CI pipeline is taking 45 minutes. It's killing our velocity. I'm spending half my day waiting for GitHub Actions to finish."
**Yara (QA Lead):** "I agree. I can't run regression tests effectively if the build takes an hour."
**Kaia (CTO):** "We don't have time to rewrite the whole pipeline. Kenji, look into parallelizing the test suites. Split the `pytest` runs into four parallel jobs. Let's get this under 15 minutes by next sprint."
**Decision:** Parallelize CI tests using GitHub Actions matrix strategy.

### Thread 2: The "SAML vs OIDC" Debate (Nov 02, 2025)
**Aiko (Contractor):** "Some of our oldest clients are still on SAML 1.1. Do we really need to support it?"
**Kaia (CTO):** "SAML 2.0 is the minimum. We aren't going back to 1.1. If the client can't upgrade, we'll provide them with a secure manual login as a fallback."
**Kenji (Data Eng):** "Wait, I thought we were doing OIDC only for the new portal?"
**Kaia (CTO):** "No, we need both. Logistics clients are slow to migrate. Implement SAML 2.0 and OIDC. Period."
**Decision:** Support both SAML 2.0 and OIDC; no support for SAML 1.1.

### Thread 3: The "Feature Creep" Conflict (Dec 15, 2025)
**Stakeholder (Sales):** "Can we just add a small 'Export to PDF' button for the reports? It's just one button."
**Kenji (Data Eng):** "That's not just a button. We need a PDF generation library, templates, and a way to handle large datasets. That's at least 3 days of work."
**Kaia (CTO):** "We are not adding it now. We are in a launch-blocker phase with billing and localization. Put it in the 'Post-Launch' doc."
**Kenji (Data Eng):** *(Does not respond to the Sales stakeholder)*
**Decision:** "Export to PDF" moved to Phase 5 (Post-Launch).

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $280,000 | Salaries for team of 8 (including partial contractor fees for Aiko). |
| **Infrastructure** | 15% | $60,000 | Self-hosted server hardware, EU data center leasing, Redis/Mongo licenses. |
| **Tools & APIs** | 5% | $20,000 | Stripe fees, SendGrid, Twilio, GitHub Enterprise. |
| **Contingency** | 10% | $40,000 | Reserved for emergency contractor scaling or hardware failure. |

---

## 12. APPENDICES

### Appendix A: CI Pipeline Optimization Plan
Currently, the CI pipeline runs sequentially: `Linting` $\rightarrow$ `Unit Tests` $\rightarrow$ `Integration Tests` $\rightarrow$ `Build`.
The proposed optimization involves:
1. **Matrix Execution:** Splitting the 1,200 unit tests into 4 groups of 300, running in parallel.
2. **Layer Caching:** Using `actions/cache` for Docker layers and Python `pip` dependencies.
3. **Selective Testing:** Implementing `git diff` analysis to only run tests for modules that have changed.
**Target:** Reduction of pipeline time from 45m to 12m.

### Appendix B: Legacy Data Migration Strategy
The migration from the 15-year-old SQL-based system to MongoDB will follow a **Double-Write** strategy:
1. **Shadow Write:** For 30 days, all new data will be written to both the legacy system and Obelisk.
2. **Backfill:** A background process will migrate historical data in chunks of 10,000 records per hour to avoid overloading the legacy DB.
3. **Verification:** A checksum script will compare records between the two systems.
4. **Cutover:** Once checksums match for 7 consecutive days, the legacy system will be set to read-only, and Obelisk will become the System of Record.