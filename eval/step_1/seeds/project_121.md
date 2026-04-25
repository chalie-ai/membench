Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. To maintain the requested depth, every section is expanded with granular technical details, simulated corporate bureaucracy, and precise architectural mapping.

***

# PROJECT VANGUARD: COMPREHENSIVE PROJECT SPECIFICATION
**Document Version:** 1.0.4  
**Status:** Active / In-Progress  
**Classification:** Internal – Bridgewater Dynamics  
**Date:** October 24, 2023  
**Project Lead:** Nadia Gupta

---

## 1. EXECUTIVE SUMMARY

**Project Identification**
Project Vanguard represents a critical platform modernization effort for Bridgewater Dynamics. As a primary provider in the telecommunications sector, Bridgewater Dynamics has historically relied on a monolithic architecture that has reached its vertical scaling limit. The core legacy system, a sprawling Ruby-on-Rails monolith dating back to 2012, currently suffers from "deployment dread," where a single change in the billing module can inadvertently crash the customer portal.

**Business Justification**
The primary driver for Vanguard is the transition from a monolithic architecture to a decoupled microservices ecosystem. The current monolith possesses a high degree of coupling, leading to an average deployment time of 4 hours and a Mean Time to Recovery (MTTR) of 120 minutes. In the high-stakes telecommunications industry, where service availability is tied to strict SLAs, this fragility is an existential risk. 

The modernization effort aims to implement an API Gateway pattern to abstract the underlying microservices, allowing the team to migrate functionality incrementally (the "Strangler Fig" pattern) over an 18-month window. By shifting to Elixir/Phoenix, the company leverages the BEAM virtual machine's ability to handle massive concurrency—essential for managing the millions of simultaneous socket connections required for real-time telecom telemetry.

**ROI Projection**
The financial justification for Vanguard is centered on operational efficiency and infrastructure cost reduction. 
1. **Transaction Cost Reduction:** By optimizing the data path and utilizing event-driven communication via Kafka, the projected cost per transaction is expected to drop by 35%. This is achieved by removing redundant database queries and replacing synchronous REST calls with asynchronous event processing.
2. **Developer Velocity:** By decoupling the services, the time to move a feature from "Development" to "Production" is projected to decrease from 14 days to 3 days.
3. **Infrastructure Right-Sizing:** Moving to Fly.io allows for global distribution of services closer to the edge, reducing latency by an estimated 40ms for international clients.

**Budgetary Constraints**
Vanguard is operating on a "shoestring" budget of $150,000. Given the constraints, the project is being executed by a lean team. Every dollar is scrutinized under a strict cost-benefit analysis. The budget is heavily skewed toward infrastructure and specialized tools, with minimal overhead for external consultants.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Vanguard utilizes a distributed microservices architecture. The core principle is "Isolation of Concerns." Each service owns its own database (Database-per-Service pattern) to ensure that a failure in one domain does not cascade. Communication is split between synchronous requests (via the API Gateway) and asynchronous events (via Apache Kafka).

### 2.2 The Stack
- **Language/Framework:** Elixir 1.14 / Phoenix 1.6.
- **Real-time Layer:** Phoenix LiveView for the administrative dashboards, allowing for stateful, real-time updates without the overhead of a heavy JS framework.
- **Data Store:** PostgreSQL 15 (Managed Fly.io Postgres).
- **Message Broker:** Apache Kafka (Managed Confluent Cloud) for event streaming.
- **Hosting:** Fly.io (Global Edge Deployment).
- **CI/CD:** GitHub Actions utilizing a blue-green deployment strategy to ensure zero downtime.

### 2.3 ASCII Architecture Diagram
```text
[ Client / Web Browser ] 
          |
          v
[    API GATEWAY (Phoenix)    ]  <-- Auth, Rate Limiting, Routing
          |
          +---------------------------------------+
          |                   |                   |
          v                   v                   v
[ Billing Service ]    [ User Service ]     [ Automation Service ]
 (Postgres DB)          (Postgres DB)       (Postgres DB)
          |                   |                   |
          +-------------------+-------------------+
                              |
                              v
                    [ KAFKA EVENT BUS ]
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
 [ Notification Svc ]  [ Analytics Svc ]    [ Audit Svc ]
```

### 2.4 Communication Patterns
- **External $\to$ Internal:** Clients communicate with the API Gateway via HTTPS/REST. The Gateway performs JWT validation and forwards requests to the appropriate microservice via internal gRPC or HTTP.
- **Internal $\to$ Internal (Sync):** Used sparingly for critical read-operations where immediate consistency is required.
- **Internal $\to$ Internal (Async):** The primary mode of communication. For example, when the `Billing Service` completes a transaction, it publishes a `transaction.completed` event to Kafka. The `Notification Service` and `Analytics Service` subscribe to this event to trigger emails and update reports respectively.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
- **Priority:** Medium
- **Status:** Blocked
- **Description:** An administrative interface allowing operators to visualize real-time network health and billing metrics.
- **Functional Requirements:**
    - Users must be able to add/remove widgets from a predefined library.
    - Widgets must support different data visualizations (Time-series graphs, Gauges, Tables).
    - Layouts must be persisted in the database and reload based on the user's profile.
- **Technical Implementation:** 
    - The frontend will use Phoenix LiveView with a JavaScript hook for `SortableJS` to handle the drag-and-drop interaction. 
    - State updates will be sent via WebSocket to the server, which will update the `user_dashboard_configs` table.
- **Blocking Issue:** The feature is currently blocked by a lack of finalized UI/UX prototypes from Alejandro Santos and a critical dependency on the "Data Aggregator" service which is currently failing its performance benchmarks.
- **Acceptance Criteria:** User can drag a "Revenue" widget to the top-left corner, refresh the page, and find the widget in the same position.

### 3.2 Webhook Integration Framework
- **Priority:** High
- **Status:** Complete
- **Description:** A system allowing third-party tools (e.g., Slack, Zapier, Custom CRM) to receive real-time notifications from the Vanguard platform.
- **Functional Requirements:**
    - Support for custom endpoint URLs.
    - Secret key rotation for webhook security (HMAC signatures).
    - Retry logic with exponential backoff (max 5 attempts).
    - Event filtering (users choose which events trigger the webhook).
- **Technical Implementation:**
    - A dedicated `Webhook Service` that consumes events from Kafka.
    - Use of `Tesla` (Elixir HTTP client) for outgoing requests.
    - A PostgreSQL table `webhook_subscriptions` to store target URLs and event triggers.
- **Validation:** Successfully tested against a mock server; 10,000 events pushed with a 0.01% failure rate (all failed requests were correctly retried).

### 3.3 A/B Testing Framework (Feature Flag Integration)
- **Priority:** High
- **Status:** Not Started
- **Description:** A system to toggle features for specific percentages of the user base and measure the impact on KPIs.
- **Functional Requirements:**
    - Ability to define "Experiments" with a control group and one or more variant groups.
    - Percentage-based rollout (e.g., 10% of users see the new billing page).
    - Integration with the existing feature flag system to ensure no latency overhead.
    - Tracking of conversion metrics per variant.
- **Technical Implementation:**
    - Use of a "Hashing" strategy for user assignment (UserID + ExperimentID hashed to a number 0-99) to ensure sticky assignments without storing every user's variant in the DB.
    - Metadata passed via the API Gateway to downstream services to indicate which variant the user belongs to.
- **Acceptance Criteria:** A developer can toggle a flag in the admin panel, and 20% of users instantly see the "New Pricing" layout.

### 3.4 Workflow Automation Engine with Visual Rule Builder
- **Priority:** Medium
- **Status:** In Progress
- **Description:** A low-code engine allowing non-technical staff to create "If-This-Then-That" rules for telecom account management.
- **Functional Requirements:**
    - Visual canvas for building logic flows (Nodes and Edges).
    - Support for triggers (e.g., "Account Balance < $5") and actions (e.g., "Send SMS Warning").
    - Validation logic to prevent infinite loops in rules.
- **Technical Implementation:**
    - The engine uses a Directed Acyclic Graph (DAG) structure stored in JSONB format in PostgreSQL.
    - A custom DSL (Domain Specific Language) parser in Elixir to evaluate these rules against incoming Kafka events.
- **Current Progress:** The backend parser is 80% complete. The visual builder frontend is currently being developed by Arun Oduya.

### 3.5 Notification System (Email, SMS, In-app, Push)
- **Priority:** Low
- **Status:** In Review
- **Description:** A centralized hub for all outbound communications to the customer.
- **Functional Requirements:**
    - Multi-channel support via a single API call.
    - Template management system (Handlebars-style syntax).
    - Opt-out/Preference management for users.
    - Priority queuing (e.g., "Password Reset" emails take precedence over "Marketing" emails).
- **Technical Implementation:**
    - Integration with SendGrid (Email), Twilio (SMS), and Firebase Cloud Messaging (Push).
    - Use of Elixir `Oban` for reliable background job processing and retries.
- **Review Notes:** Currently under review by Nadia Gupta to ensure that the SMS logic doesn't bypass the rate-limiting logic implemented in the API Gateway.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and require a `Bearer <JWT>` token in the Authorization header.

### 4.1 User Management
**`GET /v1/users/:id`**
- **Description:** Retrieve detailed user profile.
- **Request:** `GET /v1/users/usr_98765`
- **Response (200 OK):**
  ```json
  {
    "id": "usr_98765",
    "email": "user@example.com",
    "status": "active",
    "tier": "premium",
    "created_at": "2023-01-15T10:00:00Z"
  }
  ```

**`PATCH /v1/users/:id`**
- **Description:** Update user preferences.
- **Request:** `PATCH /v1/users/usr_98765` | Body: `{"notification_pref": "email_only"}`
- **Response (200 OK):** `{"status": "updated", "timestamp": "2023-10-24T14:20:00Z"}`

### 4.2 Billing & Transactions
**`POST /v1/billing/invoice`**
- **Description:** Generate a manual invoice for a client.
- **Request:** `POST /v1/billing/invoice` | Body: `{"user_id": "usr_98765", "amount": 49.99, "currency": "USD"}`
- **Response (201 Created):**
  ```json
  {
    "invoice_id": "inv_112233",
    "amount": 49.99,
    "status": "pending",
    "due_date": "2023-11-24"
  }
  ```

**`GET /v1/billing/usage`**
- **Description:** Get real-time data usage for the current billing cycle.
- **Request:** `GET /v1/billing/usage?user_id=usr_98765`
- **Response (200 OK):** `{"data_used_gb": 14.2, "limit_gb": 20.0, "percentage": 71}`

### 4.3 Automation & Webhooks
**`POST /v1/webhooks/subscribe`**
- **Description:** Register a new webhook endpoint.
- **Request:** `POST /v1/webhooks/subscribe` | Body: `{"url": "https://client.com/callback", "events": ["payment.success", "user.created"]}`
- **Response (201 Created):** `{"webhook_id": "wh_5566", "secret": "shhh_secret_key"}`

**`DELETE /v1/webhooks/:id`**
- **Description:** Remove a webhook subscription.
- **Request:** `DELETE /v1/webhooks/wh_5566`
- **Response (204 No Content):** (Empty body)

### 4.4 System & Health
**`GET /v1/system/health`**
- **Description:** Global health check for the API Gateway and downstream services.
- **Request:** `GET /v1/system/health`
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "services": {
      "billing": "up",
      "user": "up",
      "automation": "degraded",
      "kafka": "up"
    }
  }
  ```

**`GET /v1/system/metrics`**
- **Description:** Retrieve current system throughput and latency.
- **Request:** `GET /v1/system/metrics`
- **Response (200 OK):** `{"req_per_sec": 1200, "avg_latency_ms": 45, "error_rate": "0.02%"}`

---

## 5. DATABASE SCHEMA

Vanguard uses a distributed PostgreSQL architecture. While each service has its own logical database, the following is the unified schema for the primary services.

### 5.1 User Service Tables
1. **`users`**
   - `id` (UUID, PK): Primary Identifier.
   - `email` (VARCHAR, Unique): User login.
   - `password_hash` (VARCHAR): Argon2id hash.
   - `mfa_enabled` (BOOLEAN): Default false.
   - `created_at` (TIMESTAMP): Auto-generated.
2. **`user_profiles`**
   - `user_id` (UUID, FK $\to$ users.id): One-to-one relationship.
   - `full_name` (VARCHAR): Legal name.
   - `timezone` (VARCHAR): User's local timezone.
   - `address_json` (JSONB): Structured address data.
3. **`user_dashboard_configs`**
   - `id` (UUID, PK): Configuration ID.
   - `user_id` (UUID, FK $\to$ users.id): Owner of the config.
   - `layout_json` (JSONB): Coordinates and sizes of widgets.
   - `updated_at` (TIMESTAMP).

### 5.2 Billing Service Tables
4. **`accounts`**
   - `id` (UUID, PK): Billing account ID.
   - `user_id` (UUID, FK $\to$ users.id): Link to User service.
   - `balance` (DECIMAL 12,2): Current credit/debit.
   - `currency` (VARCHAR(3)): ISO code (e.g., USD).
5. **`transactions`**
   - `id` (UUID, PK): Transaction ID.
   - `account_id` (UUID, FK $\to$ accounts.id): Account involved.
   - `amount` (DECIMAL 12,2): Value of transaction.
   - `type` (ENUM): 'credit', 'debit', 'refund'.
   - `status` (ENUM): 'pending', 'completed', 'failed'.
6. **`invoices`**
   - `id` (UUID, PK): Invoice ID.
   - `account_id` (UUID, FK $\to$ accounts.id).
   - `total_amount` (DECIMAL 12,2).
   - `due_date` (DATE).
   - `is_paid` (BOOLEAN).

### 5.3 Automation Service Tables
7. **`workflows`**
   - `id` (UUID, PK): Workflow ID.
   - `name` (VARCHAR): Human-readable name.
   - `definition` (JSONB): The DAG logic of the workflow.
   - `is_active` (BOOLEAN).
8. **`workflow_logs`**
   - `id` (BIGINT, PK): Log entry ID.
   - `workflow_id` (UUID, FK $\to$ workflows.id).
   - `trigger_event` (VARCHAR): The event that started the flow.
   - `execution_time_ms` (INTEGER).
   - `result` (ENUM): 'success', 'failure'.

### 5.4 Webhook Service Tables
9. **`webhook_subscriptions`**
   - `id` (UUID, PK): Subscription ID.
   - `user_id` (UUID, FK $\to$ users.id).
   - `target_url` (TEXT): The destination endpoint.
   - `secret_token` (VARCHAR): HMAC key.
   - `events_list` (ARRAY): List of events to trigger.
10. **`webhook_deliveries`**
    - `id` (UUID, PK): Delivery attempt ID.
    - `subscription_id` (UUID, FK $\to$ webhook_subscriptions.id).
    - `payload` (JSONB): The data sent.
    - `response_code` (INTEGER): HTTP status from target.
    - `attempt_count` (INTEGER): Number of retries.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Vanguard maintains three distinct environments to ensure stability and testing rigor.

**Development (Dev)**
- **Purpose:** Local development and individual feature testing.
- **Host:** Local Docker containers / Fly.io dev clusters.
- **Data:** Mock data generated by `ExMachina` (Elixir factory).
- **Deployment:** Triggered on every push to a feature branch.

**Staging (Stage)**
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and integration testing.
- **Host:** Fly.io `staging` region.
- **Data:** Sanitized clone of production data (PII removed).
- **Deployment:** Triggered on merge to the `develop` branch. This environment mirrors Production's hardware specs exactly.

**Production (Prod)**
- **Purpose:** Live customer traffic.
- **Host:** Fly.io multi-region cluster (US-East, EU-West, AP-Southeast).
- **Data:** Live production PostgreSQL.
- **Deployment:** Blue-Green deployment. The "Green" version is deployed alongside the "Blue" version. Traffic is shifted via the API Gateway once health checks pass.

### 6.2 CI/CD Pipeline (GitHub Actions)
1. **Lint & Format:** Run `mix format` and `credo` for style consistency.
2. **Test Suite:** Execute all unit and integration tests.
3. **Build:** Compile Elixir releases into a Docker image.
4. **Push:** Upload image to the Fly.io registry.
5. **Deploy:** Roll out to Staging $\to$ Manual Approval $\to$ Roll out to Production.

### 6.3 Monitoring and Observability
- **Logging:** Structured JSON logs streamed to a centralized logging service.
- **Metrics:** Prometheus for collecting system-level metrics (CPU, Mem) and Phoenix.Telemetry for application-level metrics (request duration, Kafka lag).
- **Alerting:** PagerDuty integration for critical failures (e.g., API Gateway 5xx error rate > 1%).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Individual functions and modules.
- **Approach:** Using `ExUnit`. Every new business logic function must have a corresponding test file.
- **Coverage Target:** 80% coverage across all new microservices.
- **Special Case:** The "Core Billing Module" currently has **0% test coverage**. This is a critical piece of technical debt. A "Testing Sprint" is scheduled for Q1 2024 to retrospectively add tests to this module.

### 7.2 Integration Testing
- **Focus:** The interaction between two or more services.
- **Approach:** Using `Wallaby` for end-to-end browser flow and `Hound` for API testing.
- **Scenario:** A test will trigger a payment in the `Billing Service` and verify that the `Webhook Service` sends the correct payload to a mock endpoint.
- **Kafka Testing:** Using a dedicated "Test Topic" to ensure events are produced and consumed with correct schemas.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (The "Happy Path").
- **Approach:** Automated scripts that simulate a user signing up, creating a workflow, and receiving a notification.
- **Frequency:** Run every 24 hours against the Staging environment.

### 7.4 Performance Testing
- **Focus:** Latency and Throughput.
- **Tools:** `K6` (JavaScript-based load testing).
- **Benchmarks:**
    - API Gateway latency must be $< 50ms$ at 1,000 Requests Per Second (RPS).
    - Kafka consumer lag must not exceed 2 seconds during peak load.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget may be cut by 30% in the next fiscal quarter. | High | Severe | **Parallel-Pathing:** Simultaneously prototype a "Lite" version of the architecture using shared databases instead of full microservices to reduce infrastructure costs. |
| R-02 | Primary vendor dependency (Payment Processor) announced EOL. | Medium | High | **De-scoping:** If a replacement is not found by Milestone 2, de-scope the "Advanced Billing" features and move to a basic flat-fee model. |
| R-03 | API Rate Limits on 3rd party APIs during testing. | High | Medium | **Mocking:** Implement a robust mocking layer (`Mox` in Elixir) to simulate external API responses during development and CI/CD. |
| R-04 | Technical Debt in Core Billing Module (No Tests). | Certain | High | **Incremental Refactoring:** Allocate 20% of every sprint to "Debt Repayment" focusing exclusively on the billing module. |
| R-05 | Solo Developer Burnout. | Medium | Severe | **Documentation:** Heavy emphasis on detailed specs (this document) so that onboarding a second developer in the future is seamless. |

---

## 9. TIMELINE & PHASES

The project is scheduled over 18 months, divided into three primary phases.

### Phase 1: Foundation & Gateway (Months 1–6)
- **Goal:** Establish the API Gateway and migrate the first service (User Service).
- **Dependencies:** Infrastructure setup on Fly.io.
- **Activities:**
    - Month 1: CI/CD pipeline and basic Gateway routing.
    - Month 2: Migration of User DB to PostgreSQL 15.
    - Month 3: Implementation of JWT authentication.
    - Month 4-6: Kafka cluster setup and initial event-bus patterns.
- **Milestone 1 (2025-07-15):** Performance benchmarks met (Latency $< 50ms$).

### Phase 2: Core Migration & Feature Build (Months 7–12)
- **Goal:** Migrate Billing and Automation services; implement high-priority features.
- **Dependencies:** Completion of User Service migration.
- **Activities:**
    - Month 7: Billing Service migration (and debt cleanup).
    - Month 8: Webhook Framework implementation (Complete).
    - Month 9: Workflow Automation Engine development.
    - Month 10-12: A/B Testing Framework development.
- **Milestone 2 (2025-09-15):** Internal alpha release.

### Phase 3: Optimization & Expansion (Months 13–18)
- **Goal:** Final feature polish, external beta, and legacy system decommissioning.
- **Dependencies:** Stable Internal Alpha.
- **Activities:**
    - Month 13: Notification system review and deployment.
    - Month 14: Dashboard widget implementation (once unblocked).
    - Month 15: Pilot user onboarding.
    - Month 16-18: Final stress testing and legacy monolith shutdown.
- **Milestone 3 (2025-11-15):** External beta with 10 pilot users.

---

## 10. MEETING NOTES

*Note: Per company culture, these are summaries of recorded video calls. None of the recordings have been rewatched.*

### Meeting 1: Architecture Alignment (2023-11-05)
- **Attendees:** Nadia Gupta, Arun Oduya, Alejandro Santos, Farid Fischer.
- **Discussion:** Discussion revolved around whether to use RabbitMQ or Kafka. Farid suggested RabbitMQ for simplicity, but Nadia insisted on Kafka due to the need for event replayability for the billing audit logs.
- **Decision:** Kafka is the standard.
- **Action Item:** Nadia to set up Confluent Cloud account.

### Meeting 2: The Budget Crisis (2023-12-12)
- **Attendees:** Nadia Gupta, Finance Rep.
- **Discussion:** Finance warned that the $150k budget is "absolute" and likely to be squeezed. Nadia argued that moving to Elixir will save money in the long run via reduced server count.
- **Decision:** Budget remains $150k, but Nadia must provide monthly "cost-per-transaction" reports to prove ROI.
- **Action Item:** Implement Prometheus metrics for cost tracking.

### Meeting 3: Feature Prioritization Clash (2024-01-20)
- **Attendees:** Nadia Gupta, Alejandro Santos, Arun Oduya.
- **Discussion:** Alejandro wanted the Dashboard to be the primary focus. Nadia blocked this, stating the Dashboard is useless without the underlying data services (Billing/Automation) being migrated first.
- **Decision:** Dashboard moved to "Medium" priority and marked as "Blocked" until the data aggregator is ready.
- **Action Item:** Arun to focus on the Workflow Engine's visual builder.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Shoestring)

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | $80,000 | $80,000 | Primary developer salary and small stipends for leads. |
| **Infrastructure** | $30,000 | $30,000 | Fly.io hosting, Managed Postgres, and Confluent Cloud. |
| **Software Tools** | $15,000 | $15,000 | GitHub Enterprise, PagerDuty, SendGrid/Twilio APIs. |
| **Contingency** | $25,000 | $25,000 | Reserved for emergency hardware scaling or vendor price hikes. |

*Note: Personnel costs are minimized by utilizing existing staff roles; the budget focuses on the "delta" cost of the migration.*

---

## 12. APPENDICES

### Appendix A: Kafka Topic Schema Definitions
To ensure data consistency, all Kafka events must adhere to the following Avro-style schemas:

1. **`payment.processed`**
   - `transaction_id`: UUID (Required)
   - `account_id`: UUID (Required)
   - `amount`: Decimal (Required)
   - `status`: String (Required - 'success'|'fail')
   - `timestamp`: Long (Unix Epoch)

2. **`user.updated`**
   - `user_id`: UUID (Required)
   - `changed_fields`: Array[String] (Required)
   - `timestamp`: Long (Unix Epoch)

### Appendix B: Blue-Green Deployment Logic
The deployment process follows a strict 4-step sequence:
1. **Provision:** A new set of containers (Green) is launched with the new code version.
2. **Warm-up:** The API Gateway sends 1% of traffic to Green. The system monitors for a 5xx spike.
3. **Switch:** If the error rate remains below 0.1%, the Gateway flips 100% of traffic to Green.
4. **Retain:** The Blue version is kept dormant for 30 minutes. If a critical bug is found, the Gateway flips back to Blue instantly.