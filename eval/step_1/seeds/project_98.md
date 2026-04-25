Due to the extreme length requirement of 6,000 to 8,000 words, this document is structured as a comprehensive, professional technical specification. It follows a rigorous industrial format, expanding every provided detail into a granular execution plan for Bellweather Technologies.

***

# PROJECT SPECIFICATION: PROJECT QUORUM
**Document Version:** 1.0.4  
**Status:** Draft / Internal Review  
**Last Updated:** October 24, 2024  
**Project Lead:** Tariq Nakamura (CTO)  
**Classification:** Confidential - Bellweather Technologies  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Quorum represents a strategic cost-reduction and operational efficiency initiative for Bellweather Technologies. Currently, the organization maintains four redundant internal machine learning deployment tools, each with its own maintenance overhead, disparate codebase, and overlapping functionality. This redundancy has resulted in an estimated annual waste of $120,000 in cloud compute costs and approximately 1,500 man-hours of redundant engineering effort per year.

The objective of Quorum is to consolidate these legacy tools into a single, unified ML model deployment platform. By streamlining the pipeline from model training to production inference, Bellweather Technologies will reduce operational friction and centralize its healthcare-grade data governance. 

### 1.2 Project Goals
The primary goal is the deployment of a robust, multi-tenant platform capable of hosting various healthcare ML models (predictive diagnostics, patient flow optimization, and billing automation) while maintaining strict regulatory compliance (GDPR/CCPA). The project aims to transition the organization from a fragmented toolset to a "modular monolith" that can be incrementally decomposed into microservices as the user base scales.

### 1.3 ROI Projection and Financial Impact
With a total budget of $400,000, Quorum is positioned as a high-ROI venture. The financial justification is broken down as follows:
- **Direct Cost Savings:** Elimination of four legacy licenses and reduced infrastructure sprawl is projected to save $45,000 in Year 1 and $80,000 in Year 2.
- **Engineering Efficiency:** Reducing the maintenance burden from four systems to one is expected to recapture 20% of the backend team's capacity.
- **Revenue Acceleration:** By consolidating the deployment pipeline, the time-to-market for new healthcare ML models is expected to drop from 12 weeks to 4 weeks.
- **Break-even Analysis:** Based on the $400,000 investment, Bellweather Technologies expects to reach the break-even point by Month 14 post-launch, driven primarily by the onboarding of paying customers (Milestone 2).

### 1.4 Strategic Alignment
Quorum aligns with the corporate mandate to standardize data residency within the EU to satisfy healthcare regulators. By centralizing deployment, Bellweather can implement a single, audited security gate rather than managing four disparate security protocols.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Quorum is built on a **Modular Monolith** architecture. This design choice allows the team of six to maintain velocity without the overhead of distributed system complexity, while providing clear boundaries (via Python modules) that allow for future extraction into microservices (e.g., moving the Billing module to its own service).

**The Stack:**
- **Language:** Python 3.11+
- **Framework:** FastAPI (Asynchronous API layer)
- **Database:** MongoDB 6.0 (Document store for flexible ML metadata and tenant configs)
- **Task Queue:** Celery 5.3 (Distributed task processing for model inference and billing)
- **Message Broker:** Redis 7.0
- **Containerization:** Docker Compose (Orchestrating API, Worker, Redis, and MongoDB)
- **Hosting:** Self-hosted on private EU-based servers (to meet data residency requirements).

### 2.2 Architectural Diagram (ASCII Description)
The system flow is designed as follows:

```text
[ User Interface (React/Next.js) ]
             |
             v
[ Nginx Load Balancer / Reverse Proxy ]
             |
             v
[ FastAPI Application Server (The Monolith) ]
    |                |                 |
    | (Read/Write)   | (Task Offload)  | (Auth/Session)
    v                v                 v
[ MongoDB Cluster ] [ Celery Workers ] [ Redis Cache ]
    |                |                 |
    |                |                 |
    +--> [ EU Data Volumes ] <--- [ ML Model Binaries ]
```

**Component Descriptions:**
1. **FastAPI Layer:** Handles request validation, JWT authentication, and routing. It serves as the orchestration layer.
2. **Celery Workers:** Since ML model inference can be computationally expensive and time-consuming, these workers handle the "heavy lifting" asynchronously to prevent API timeouts.
3. **MongoDB:** Stores tenant-specific configurations, user profiles, and model versioning history.
4. **Redis:** Acts as the broker for Celery and a cache for frequently accessed model metadata.
5. **EU Data Volumes:** All persistent storage is mapped to physical disks located in the EU to ensure GDPR compliance.

### 2.3 Transition Strategy to Microservices
As the project scales toward the target of 10,000 MAU, the following decomposition path is planned:
- **Phase 1:** Extract the Notification System into a standalone service (due to high volatility in SMS/Email provider APIs).
- **Phase 2:** Extract the Billing and Subscription module (to isolate financial data for easier PCI auditing).
- **Phase 3:** Extract the Model Inference Engine into a GPU-optimized cluster separate from the administrative API.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Critical)
**Status:** Not Started | **Launch Blocker:** Yes

**Description:**
Quorum must support multiple healthcare organizations (tenants) on shared infrastructure while ensuring that no tenant can access another tenant's data. Given the sensitivity of healthcare data, "soft isolation" is insufficient; a rigorous logical isolation strategy is required.

**Technical Requirements:**
- **Tenant Identifier:** Every document in MongoDB must contain a `tenant_id` field. 
- **Query Interceptors:** The FastAPI layer must implement a dependency injection mechanism that automatically injects the `tenant_id` from the authenticated JWT into every MongoDB query. This prevents "leaky" queries where a developer forgets to add a filter.
- **Storage Isolation:** While the database is shared, the model binaries (stored on disk) must be stored in tenant-specific directories with Linux-level permissioning (`/data/tenants/{tenant_id}/models/`).
- **Shared Infrastructure:** To optimize costs, tenants share the same Celery worker pool. However, tasks must be tagged with `tenant_id` for auditing and resource tracking.

**Acceptance Criteria:**
- An authenticated user from Tenant A cannot access a resource belonging to Tenant B, even if the direct UUID of the resource is known.
- All API responses must be filtered by the active tenant context.
- Successful verification via an external security audit of the isolation logic.

### 3.2 Automated Billing and Subscription Management (Priority: Medium)
**Status:** In Review | **Technical Debt:** High (No test coverage)

**Description:**
A system to manage the transition from a free beta to a paid model. This includes tiered pricing (Basic, Professional, Enterprise) based on the number of ML model inferences and the number of users per tenant.

**Technical Requirements:**
- **Subscription Tiers:**
    - *Basic:* $200/mo, 1,000 inferences, 5 users.
    - *Professional:* $800/mo, 10,000 inferences, 20 users.
    - *Enterprise:* Custom pricing, unlimited inferences.
- **Integration:** Integration with Stripe API for payment processing and webhook handling.
- **Usage Tracking:** A Celery task that increments an `inference_count` in the `subscriptions` collection every time a model is successfully called.
- **Grace Periods:** A 7-day grace period for failed payments before account suspension.

**Known Issues:**
The billing module was deployed under extreme deadline pressure and currently has **0% unit test coverage**. This is a critical risk. Any changes to this module must first be preceded by the creation of a comprehensive test suite.

**Acceptance Criteria:**
- Ability to upgrade/downgrade tiers via the UI.
- Automatic generation of monthly PDF invoices stored in MongoDB (GridFS).
- System triggers a "Payment Failed" notification via the Notification System.

### 3.3 Real-time Collaborative Editing with Conflict Resolution (Priority: Medium)
**Status:** Blocked | **Blocker:** Key team member on medical leave

**Description:**
Users within a tenant must be able to collaborate on model configuration files (JSON/YAML) in real-time. This is critical for data scientists and engineers who need to tune hyperparameters simultaneously.

**Technical Requirements:**
- **WebSocket Integration:** Use FastAPI's WebSocket support to maintain a persistent connection between the client and server.
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to ensure that if two users edit the same line, the system resolves the conflict without data loss.
- **Presence Indicator:** Show "User X is typing..." and highlight the specific line being edited.
- **Auto-save:** Changes are persisted to MongoDB every 5 seconds or upon loss of focus.

**Current Blocker:**
The lead engineer responsible for the WebSocket implementation is currently on medical leave for 6 weeks. Work on this feature is frozen until their return or until a replacement contractor is sourced.

**Acceptance Criteria:**
- Latency for updates between two users must be under 200ms.
- No data loss during concurrent edits of the same field.

### 3.4 Localization and Internationalization (L10n/I18n) (Priority: Low)
**Status:** Complete

**Description:**
The platform must support 12 languages to facilitate global expansion, particularly in the EU and APAC regions.

**Technical Requirements:**
- **Framework:** Use of `gettext` and JSON translation files stored in the `/locales` directory.
- **Supported Languages:** English, French, German, Spanish, Italian, Portuguese, Dutch, Polish, Swedish, Japanese, Korean, and Chinese (Simplified).
- **Dynamic Switching:** Users can change their language preference in their profile, which is then stored in the `users` collection and sent as an `Accept-Language` header in API requests.
- **Date/Currency Formatting:** Use of the `Babel` library to ensure dates and currency symbols are formatted according to the user's locale.

**Acceptance Criteria:**
- All UI strings are wrapped in translation functions.
- Switching languages updates the entire UI without requiring a full page reload.
- Correct rendering of non-Latin characters (UTF-8).

### 3.5 Notification System (Priority: High)
**Status:** In Progress

**Description:**
A centralized system to alert users of critical events: model failures, billing alerts, and collaborative invitations.

**Technical Requirements:**
- **Multi-Channel Delivery:**
    - **Email:** Integrated via SendGrid.
    - **SMS:** Integrated via Twilio.
    - **In-App:** Managed via a MongoDB `notifications` collection and pushed via WebSockets.
    - **Push:** Integration with Firebase Cloud Messaging (FCM).
- **Preference Center:** Users must be able to toggle which notifications they receive for each channel (e.g., "Email: Yes, SMS: No").
- **Priority Queueing:** High-priority alerts (e.g., "Model Downtime") must jump to the front of the Celery queue.

**Acceptance Criteria:**
- Notifications are delivered within 30 seconds of the triggering event.
- Users can mark notifications as "read" across all devices.
- The system handles "rate limiting" to avoid spamming users.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer <JWT>` token in the Authorization header.

### 4.1 Tenant Management
**Endpoint:** `POST /api/v1/tenants/provision`
- **Description:** Provisions a new healthcare tenant and initializes their isolated data structures.
- **Request Body:**
  ```json
  {
    "org_name": "St. Jude Medical",
    "admin_email": "admin@stjude.com",
    "region": "EU-West-1",
    "plan": "professional"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "tenant_id": "tnt_98765",
    "api_key": "sk_live_...",
    "status": "provisioning"
  }
  ```

### 4.2 Model Deployment
**Endpoint:** `POST /api/v1/models/deploy`
- **Description:** Deploys a new ML model version to the production environment.
- **Request Body:**
  ```json
  {
    "model_name": "cardio-predict-v2",
    "s3_path": "s3://bellweather-eu/models/cardio-v2.pkl",
    "version": "2.1.0",
    "resource_limits": { "cpu": 2, "ram": "4Gi" }
  }
  ```
- **Response (202 Accepted):**
  ```json
  {
    "deployment_id": "dep_12345",
    "estimated_completion": "2025-06-15T14:00:00Z"
  }
  ```

### 4.3 Model Inference
**Endpoint:** `POST /api/v1/models/{model_id}/predict`
- **Description:** Sends data to a deployed model and returns a prediction.
- **Request Body:**
  ```json
  {
    "input_data": { "age": 45, "cholesterol": 210, "blood_pressure": "140/90" },
    "priority": "high"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "prediction": "high_risk",
    "confidence": 0.89,
    "inference_time_ms": 142
  }
  ```

### 4.4 Subscription Update
**Endpoint:** `PATCH /api/v1/billing/subscription`
- **Description:** Updates the subscription tier for the current tenant.
- **Request Body:**
  ```json
  {
    "new_plan": "enterprise",
    "payment_method_id": "pm_123456789"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "updated",
    "next_billing_date": "2025-11-15"
  }
  ```

### 4.5 Notification Settings
**Endpoint:** `PUT /api/v1/users/me/notifications`
- **Description:** Updates the user's communication preferences.
- **Request Body:**
  ```json
  {
    "email": true,
    "sms": false,
    "push": true,
    "in_app": true
  }
  ```
- **Response (200 OK):**
  ```json
  { "message": "Preferences updated successfully" }
  ```

### 4.6 Model Version History
**Endpoint:** `GET /api/v1/models/{model_id}/versions`
- **Description:** Retrieves all historical versions of a specific model for rollback purposes.
- **Response (200 OK):**
  ```json
  [
    { "version": "2.1.0", "deployed_at": "2025-01-10", "status": "active" },
    { "version": "2.0.0", "deployed_at": "2024-11-01", "status": "archived" }
  ]
  ```

### 4.7 Collaborative Session
**Endpoint:** `GET /api/v1/collaboration/session/{config_id}`
- **Description:** Initiates a WebSocket handshake for collaborative editing.
- **Response:** `101 Switching Protocols` (WebSocket Connection established).

### 4.8 Health Check
**Endpoint:** `GET /api/v1/system/health`
- **Description:** Returns the health status of the monolith, MongoDB, Redis, and Celery workers.
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "components": {
      "mongodb": "connected",
      "redis": "connected",
      "celery": "active"
    }
  }
  ```

---

## 5. DATABASE SCHEMA (MONGODB)

Since Quorum uses MongoDB, the schema is defined as a set of collections with implied relationships. All collections are indexed by `tenant_id`.

### 5.1 Collection: `tenants`
- `_id`: ObjectId (Primary Key)
- `org_name`: String
- `creation_date`: Date
- `region`: String (e.g., "EU-Central-1")
- `subscription_status`: String (Active, Past_Due, Cancelled)
- `settings`: Object (Custom branding, timezone, etc.)

### 5.2 Collection: `users`
- `_id`: ObjectId
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `email`: String (Indexed)
- `password_hash`: String
- `role`: String (Admin, DataScientist, Viewer)
- `locale`: String (e.g., "fr_FR")
- `notification_prefs`: Object (email: bool, sms: bool, etc.)

### 5.3 Collection: `models`
- `_id`: ObjectId
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `name`: String
- `description`: String
- `framework`: String (PyTorch, Scikit-Learn, TensorFlow)
- `created_by`: ObjectId (Foreign Key $\rightarrow$ `users`)
- `current_version`: String

### 5.4 Collection: `model_versions`
- `_id`: ObjectId
- `model_id`: ObjectId (Foreign Key $\rightarrow$ `models`)
- `version_string`: String (e.g., "1.0.4")
- `binary_path`: String (Path to EU-disk)
- `hyperparameters`: Object
- `metrics`: Object (Accuracy, F1-Score, etc.)
- `deployment_date`: Date

### 5.5 Collection: `deployments`
- `_id`: ObjectId
- `model_version_id`: ObjectId (Foreign Key $\rightarrow$ `model_versions`)
- `status`: String (Pending, Deploying, Active, Failed)
- `endpoint_url`: String
- `start_time`: Date
- `end_time`: Date

### 5.6 Collection: `subscriptions`
- `_id`: ObjectId
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `plan_type`: String (Basic, Prof, Ent)
- `stripe_customer_id`: String
- `monthly_cost`: Decimal
- `inference_count`: Integer (Reset monthly)
- `last_payment_date`: Date

### 5.7 Collection: `inferences`
- `_id`: ObjectId
- `model_id`: ObjectId (Foreign Key $\rightarrow$ `models`)
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `input_hash`: String
- `timestamp`: Date
- `processing_time`: Float

### 5.8 Collection: `notifications`
- `_id`: ObjectId
- `user_id`: ObjectId (Foreign Key $\rightarrow$ `users`)
- `type`: String (Billing, System, Collab)
- `message`: String
- `is_read`: Boolean
- `created_at`: Date

### 5.9 Collection: `collaboration_configs`
- `_id`: ObjectId
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `config_json`: String (Current state of the config)
- `last_edited_by`: ObjectId (Foreign Key $\rightarrow$ `users`)
- `version_lock`: Integer (For optimistic concurrency)

### 5.10 Collection: `audit_logs`
- `_id`: ObjectId
- `tenant_id`: ObjectId (Foreign Key $\rightarrow$ `tenants`)
- `user_id`: ObjectId (Foreign Key $\rightarrow$ `users`)
- `action`: String (e.g., "MODEL_DEPLOYED")
- `timestamp`: Date
- `ip_address`: String

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum utilizes a three-tier environment strategy to ensure stability and regulatory compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** Local Docker Compose on developer machines and a shared "Dev" server.
- **Data:** Mock data; no real patient records.
- **Deployment:** Automatic on push to `develop` branch.

#### 6.1.2 Staging (QA Gate)
- **Purpose:** Final validation before production. This environment mirrors production exactly.
- **Infrastructure:** Single-node instance in an EU-based data center.
- **Deployment:** Manual trigger by the QA Lead. 
- **QA Gate:** A strict 2-day turnaround for QA testing. No code reaches production without a "QA Approved" sign-off in Jira.

#### 6.1.3 Production (Prod)
- **Purpose:** Live client traffic.
- **Infrastructure:** Highly available cluster of self-hosted servers in the EU.
- **Data Residency:** Strictly enforced via physical disk mounting. No data leaves the EU region.
- **Deployment:** Blue-Green deployment strategy to ensure zero downtime during updates.

### 6.2 CI/CD Pipeline
1. **Commit:** Code pushed to GitHub.
2. **Linting/Testing:** GitHub Actions runs `flake8` and `pytest`.
3. **Build:** Docker image created and pushed to a private registry.
4. **Staging Deploy:** Image deployed to Staging.
5. **Manual QA:** QA team spends 48 hours testing the feature.
6. **Production Deploy:** After approval, the image is rolled out to Production servers.

### 6.3 Scaling Strategy
Because the system is a modular monolith, scaling is primarily vertical (increasing CPU/RAM) until the 10,000 MAU mark is approached. Once the "Inference" module becomes the bottleneck, it will be moved to a separate GPU cluster using the microservices transition plan outlined in Section 2.3.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, API utility classes, and database schemas.
- **Tooling:** `pytest`.
- **Requirement:** All new features must have $\ge 80\%$ line coverage.
- **Critical Focus:** The Billing module requires a retroactive unit testing sprint to resolve existing technical debt.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between FastAPI, MongoDB, and Celery.
- **Tooling:** `TestContainers` (to spin up temporary MongoDB/Redis instances).
- **Key Scenarios:**
    - Verifying that `tenant_id` is correctly passed from the JWT to the MongoDB query.
    - Ensuring that Celery tasks are correctly queued and processed.
    - Testing the Stripe webhook flow for subscription updates.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Complete user journeys from login to model prediction.
- **Tooling:** `Playwright` or `Selenium`.
- **Key Scenarios:**
    - Tenant A signs up $\rightarrow$ Deploys Model $\rightarrow$ Runs Prediction $\rightarrow$ Receives Bill.
    - User A and User B edit the same configuration file simultaneously (Collision Test).
    - Switching language to Japanese and verifying all UI labels are correct.

### 7.4 Regulatory Testing (Compliance)
- **Data Residency Audit:** Weekly scripts to verify that no data is stored in non-EU regions.
- **Penetration Testing:** Quarterly third-party security audits to ensure GDPR/CCPA compliance.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor dependency announced EOL for product | High | Critical | Escalate to steering committee for additional funding to build in-house replacement. |
| R-02 | Regulatory requirements (GDPR/CCPA) change mid-project | Medium | High | Engage external legal consultant for monthly independent assessments. |
| R-03 | Key team member on medical leave (6 weeks) | Certain | Medium | Redistribute tasks; consider hiring a short-term contractor for WebSocket work. |
| R-04 | Billing module failures due to lack of tests | High | High | Immediate "Testing Sprint" dedicated solely to the billing module. |
| R-05 | Dysfunctional team dynamic (PM vs Lead Engineer) | High | Medium | CTO (Tariq) to mediate weekly syncs; enforce written communication. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal penalty.
- **High:** Major delay or significant budget overrun.
- **Medium:** Moderate delay; manageable through reallocation.
- **Low:** Negligible impact.

---

## 9. TIMELINE & GANTT DESCRIPTION

### Phase 1: Foundation & Isolation (Now – June 15, 2025)
- **Focus:** Multi-tenant isolation and core API.
- **Dependencies:** MongoDB schema finalization.
- **Milestone 1:** External beta with 10 pilot users (Target: 2025-06-15).
- **Key Activity:** Implementation of the `tenant_id` query interceptor.

### Phase 2: Commercialization (June 16 – August 15, 2025)
- **Focus:** Billing, Subscriptions, and Notification system.
- **Dependencies:** Successful beta feedback from Phase 1.
- **Milestone 2:** First paying customer onboarded (Target: 2025-08-15).
- **Key Activity:** Fixing technical debt in the billing module.

### Phase 3: Optimization & Scale (August 16 – October 15, 2025)
- **Focus:** Collaborative editing and architecture review.
- **Dependencies:** Return of lead engineer from medical leave.
- **Milestone 3:** Architecture review complete (Target: 2025-10-15).
- **Key Activity:** Transitioning from modular monolith to initial microservices.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Kickoff - Q1
**Date:** 2024-11-05  
**Attendees:** Tariq Nakamura, Eshan Park, Gia Nakamura, Cleo Stein  
**Discussion:**
- Tariq emphasized the criticality of the multi-tenant isolation. He stated that "any data leak between tenants is an immediate project termination event."
- Eshan expressed concern about the choice of MongoDB for billing, arguing for PostgreSQL. Tariq overrode this, citing the need for schema flexibility for ML metadata.
- Gia presented the UX research for the 12 supported languages, noting that the Japanese UI requires more vertical space for labels.

**Action Items:**
- [Eshan] Finalize `tenants` collection schema. (Due: Nov 12)
- [Gia] Provide final localization strings for the dashboard. (Due: Nov 15)

### Meeting 2: Emergency Risk Review
**Date:** 2024-12-10  
**Attendees:** Tariq Nakamura, Eshan Park, Cleo Stein  
**Discussion:**
- Notification received that the primary vendor for the ML orchestration layer has announced End-of-Life (EOL) for their v3 API by early 2025.
- Eshan and Tariq had a heated exchange regarding the timeline. Eshan argued that the project is underfunded for a full rewrite; Tariq insisted on a "patch-and-pivot" strategy.
- Discussion on the medical leave of the WebSocket lead; Cleo Stein suggested taking over some of the backend logic, but cannot do the real-time synchronization.

**Action Items:**
- [Tariq] Escalate EOL vendor risk to the Steering Committee for extra budget. (Due: Dec 15)
- [Tariq] Source a contractor for WebSocket implementation. (Due: Dec 20)

### Meeting 3: Billing Module Audit
**Date:** 2025-01-20  
**Attendees:** Tariq Nakamura, Eshan Park, QA Lead  
**Discussion:**
- The QA lead reported that the Billing module has zero test coverage and failed 3 out of 5 edge-case tests (specifically regarding currency conversion).
- Eshan admitted the module was rushed to meet the internal demo deadline.
- Decision: All feature work on the Notification system is paused for one week to implement unit tests for the Billing module.

**Action Items:**
- [Eshan] Write unit tests for `billing_service.py`. (Due: Jan 27)
- [QA Lead] Create a regression test suite for subscription upgrades. (Due: Jan 27)

---

## 11. BUDGET BREAKDOWN

Total Budget: **$400,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Includes Eshan, Gia, Cleo, and dedicated QA. |
| **Infrastructure** | 15% | $60,000 | EU-based server rentals and storage volumes. |
| **Tools & Licenses** | 10% | $40,000 | MongoDB Atlas (Enterprise), SendGrid, Twilio, Stripe. |
| **Contingency** | 10% | $40,000 | Reserved for vendor EOL emergency and consultants. |

**Financial Notes:**
- The personnel budget is lean for a team of 6; this assumes Cleo Stein remains as a contractor.
- The contingency fund is currently earmarked for the "Vendor EOL" risk. If not used, it will be applied to accelerate Milestone 3.

---

## 12. APPENDICES

### Appendix A: Data Residency Protocol
To comply with GDPR and CCPA, Bellweather Technologies implements the following "Hard Residency" rules:
1. **Physical Location:** All data resides in the `eu-central-1` region.
2. **Encryption:** Data is encrypted at rest using AES-256. Keys are managed via a Hardware Security Module (HSM) located within the EU.
3. **Cross-Border Transfer:** No data is cached on CDN nodes outside the EU. All requests are routed through a single EU-based load balancer.
4. **Right to Erasure:** The system implements a "Hard Delete" function that wipes all tenant documents and associated model binaries from disk upon request.

### Appendix B: Celery Task Workflow
Because ML inference is asynchronous, the following state machine is used:
1. **Request:** API receives `POST /predict` $\rightarrow$ writes a "Pending" record to the `inferences` collection.
2. **Queue:** Task is pushed to the `inference_queue` in Redis.
3. **Processing:** A Celery worker picks up the task, loads the model binary from the EU-disk, and runs the prediction.
4. **Completion:** Worker updates the `inferences` record to "Complete" and pushes a notification via WebSocket to the user.
5. **Timeout:** If the task exceeds 60 seconds, it is marked as "Failed" and a notification is sent to the tenant admin.