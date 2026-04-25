Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity Project Specification. It is structured as a formal corporate artifact for Crosswind Labs.

***

# PROJECT SPECIFICATION: PROJECT INGOT
**Version:** 1.0.4  
**Status:** Active / In-Progress  
**Company:** Crosswind Labs  
**Industry:** Agriculture Technology  
**Classification:** CONFIDENTIAL – PCI DSS LEVEL 1 COMPLIANT  
**Date:** October 24, 2024  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ingot is a strategic infrastructure modernization and cost-reduction initiative undertaken by Crosswind Labs. The primary objective is the consolidation of four redundant internal toolsets—currently operating on disparate technology stacks and incurring significant operational overhead—into a single, unified API Gateway and Microservices ecosystem. These tools, which manage soil sensor telemetry, livestock tracking, crop yield forecasting, and irrigation scheduling, have evolved in silos, leading to data duplication, fragmented security postures, and unsustainable maintenance costs.

### 1.2 Business Justification
The current operational state of Crosswind Labs' internal tooling is characterized by "Technical Fragmentation." Four separate teams maintain four separate backend architectures, totaling 14 different database instances and four distinct authentication layers. This redundancy results in a "maintenance tax" where approximately 40% of engineering hours are spent on synchronization and interoperability rather than feature development. 

By migrating to a centralized API Gateway (Project Ingot), the organization will achieve:
1. **Reduction in Operational Expenditure (OpEx):** Consolidating infrastructure will reduce cloud hosting costs by an estimated $140,000 per annum.
2. **Security Hardening:** Centralizing the processing of credit card data into a single, PCI DSS Level 1 compliant vault removes the risk of "security leakage" across the four legacy tools.
3. **Developer Velocity:** A unified Kafka-driven event bus replaces brittle REST-to-REST polling, reducing latency in telemetry processing from 4 seconds to <200ms.

### 1.3 ROI Projection
The projected Return on Investment (ROI) for Project Ingot is calculated over a 24-month horizon. 
- **Initial Investment:** The variable, milestone-based funding model allocates an estimated $850,000 for the initial development phase.
- **Cost Savings:** Through the decommissioning of legacy servers and the reduction of third-party licensing for four separate observability tools, the company expects a recapture of $210,000 in Year 1 and $350,000 in Year 2.
- **Efficiency Gain:** By reducing the CI pipeline time (currently 45 minutes) and consolidating the stacks, we project a 15% increase in overall engineering throughput.
- **Net ROI:** Expected 142% by the end of FY2026.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Ingot utilizes a **Polyglot Microservices Architecture** connected by an **Event-Driven Backbone**. Because the project inherits three different existing stacks (Node.js/Express, Java/Spring Boot, and Python/FastAPI), the Gateway acts as the translation layer, ensuring that the frontend remains agnostic to the backend heterogeneity.

### 2.2 Stack Composition
- **API Gateway:** Kong Gateway (Enterprise Edition) for request routing, rate limiting, and PCI-compliant authentication.
- **Event Bus:** Apache Kafka v3.6.0 (Confluent Cloud) for asynchronous communication between services.
- **Persistence Layers:** 
    - PostgreSQL 15.4 (Relational data, User Profiles).
    - MongoDB 6.0 (Telemetry logs, flexible sensor data).
    - Redis 7.2 (Distributed caching and session management).
- **Interoperability Layer:** gRPC for high-performance synchronous internal communication.

### 2.3 ASCII System Architecture Diagram
```text
[ Client Layer ]  --> [ Cloudflare WAF ] --> [ Kong API Gateway ]
                                                   |
        ___________________________________________|____________________________________
       |                    |                      |                    |                |
[ Auth Service ]    [ Billing Service ]    [ Telemetry Service ]  [ Device Service ]  [ Analytics ]
(Node.js/Mongo)    (Java/Postgres)        (Python/TimescaleDB)  (Node.js/Postgres)  (Python/Spark)
       |                    |                      |                    |                |
       |____________________|______________________|____________________|________________|
                                     |
                          [ Apache Kafka Cluster ] <--- Event Stream (Protobuf)
                                     |
               ______________________|______________________
              |                      |                      |
      [ Webhook Worker ]    [ Audit Log Store ]    [ Notification Engine ]
```

### 2.4 Security Framework (PCI DSS Level 1)
As Project Ingot processes credit card data directly, the following controls are mandatory:
- **Encryption:** AES-256 at rest; TLS 1.3 in transit.
- **Tokenization:** Primary Account Numbers (PANs) must never be stored in the general database; they are replaced by tokens stored in a hardened Vault (HashiCorp Vault).
- **Network Isolation:** The Billing Service resides in a restricted VPC subnet with no direct internet access; all traffic must pass through the Gateway.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/I18n)
**Priority:** Medium | **Status:** In Design
**Scope:** The system must support 12 primary languages (English, Spanish, French, German, Mandarin, Japanese, Portuguese, Hindi, Arabic, Vietnamese, Thai, and Dutch) to accommodate global agricultural markets.

**Functional Requirements:**
- **Dynamic Translation Fetching:** The frontend shall send an `Accept-Language` header. The API Gateway will intercept this and append a `locale` attribute to the request context.
- **Translation Store:** A centralized Redis cache will store key-value pairs for translations (e.g., `dashboard.welcome` $\rightarrow$ "Bienvenido").
- **Right-to-Left (RTL) Support:** The UI framework must detect Arabic and Hebrew locales to flip the layout direction.
- **Currency Formatting:** Integration with the `Intl.NumberFormat` API to handle currency symbols and decimal separators based on the user's region.

**Implementation Detail:**
Translation files will be stored in JSON format in a Git-managed repository, converted to Protobuf for efficient delivery to the frontend via a dedicated `/i18n/bundle` endpoint.

### 3.2 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** Complete
**Scope:** A robust framework allowing third-party agricultural tools (e.g., John Deere Ops Center, Climate FieldView) to receive real-time alerts from Ingot.

**Functional Requirements:**
- **Payload Signing:** All outgoing webhooks must include an `X-Hub-Signature-256` header (HMAC-SHA256) to allow the receiver to verify the sender's identity.
- **Retry Logic:** Implementation of an Exponential Backoff strategy. If a target URL returns a 5xx error, Ingot will retry at 1m, 5m, 15m, 1h, and 6h intervals.
- **Dead Letter Queues (DLQ):** After 5 failed attempts, the webhook event is moved to a Kafka DLQ for manual inspection by the DevOps engineer (Finn Gupta).
- **User-Configurable Endpoints:** Users can define multiple destination URLs for specific event types (e.g., `SENSOR_THRESHOLD_EXCEEDED`, `BILLING_FAILURE`).

**Technical Specification:**
The framework utilizes a dedicated "Webhook Dispatcher" microservice written in Go for high concurrency, consuming events from the `ingot.webhooks` Kafka topic.

### 3.3 A/B Testing Framework (Feature Flag System)
**Priority:** High | **Status:** Blocked
**Scope:** A system to toggle features for specific user segments and conduct A/B tests on new UI components without redeploying code.

**Functional Requirements:**
- **Percentage Rollouts:** Ability to enable a feature for exactly X% of the user base.
- **User Segment Targeting:** Flags can be targeted based on `region`, `crop_type`, or `subscription_tier`.
- **Metric Tracking:** Integration with the Analytics service to correlate feature flag state with User NPS or Conversion rates.
- **Override Capability:** Ability for the Tech Lead (Freya Kim) to force-enable a flag for specific internal tester accounts.

**Blocker Detail:**
This feature is currently blocked by the A/B Testing SDK's incompatibility with the current version of the legacy Java stack. A bridge wrapper is being developed.

### 3.4 Customer-Facing API (Versioning & Sandbox)
**Priority:** Low (Nice to Have) | **Status:** Complete
**Scope:** A public-facing REST API allowing enterprise customers to programmatically access their farm data.

**Functional Requirements:**
- **URI Versioning:** Strict versioning via URL paths (e.g., `/v1/sensors`, `/v2/sensors`). Version 1 remains supported for 12 months after Version 2 launch.
- **Sandbox Environment:** A mirrored "Staging" environment where customers can test API calls using mock data without affecting production records.
- **API Key Management:** A self-service portal where users generate and revoke `X-API-KEY` tokens.
- **Rate Limiting:** Tiered limits (Free: 100 req/hr; Pro: 10,000 req/hr) enforced at the Kong Gateway level.

**Technical Specification:**
The sandbox environment utilizes a separate PostgreSQL schema (`sandbox_db`) populated with synthetic agricultural data generated by a Python script.

### 3.5 Customizable Dashboard (Drag-and-Drop Widgets)
**Priority:** High | **Status:** Not Started
**Scope:** A modular dashboard allowing users to organize their telemetry views using a grid-based drag-and-drop interface.

**Functional Requirements:**
- **Widget Library:** A set of pre-defined components (e.g., "Soil Moisture Graph," "Active Alerts List," "Weather Forecast").
- **Layout Persistence:** Dashboard configurations (X/Y coordinates and widget IDs) must be saved as a JSON blob in the User Profile database.
- **Real-time Updates:** Widgets must use WebSockets (via the Gateway) to update in real-time as Kafka events arrive.
- **Custom Sizing:** Ability to resize widgets (1x1, 2x1, 2x2) while maintaining a responsive grid.

**Implementation Detail:**
The frontend will use `react-grid-layout` for the UI, and the backend will provide a `/dashboard/config` endpoint for saving and retrieving layout states.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `https://api.crosswindlabs.io/ingot/`.

### 4.1 Authentication & User Management
**Endpoint:** `POST /auth/login`
- **Description:** Authenticates user and returns a JWT.
- **Request:** `{"email": "user@farm.com", "password": "..."}`
- **Response:** `{"token": "eyJhbG...", "expires_in": 3600}`

**Endpoint:** `GET /user/profile`
- **Description:** Retrieves the current authenticated user's profile.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `{"user_id": "u123", "name": "John Doe", "locale": "en-US", "tier": "pro"}`

### 4.2 Billing & Payments (PCI DSS Compliant)
**Endpoint:** `POST /billing/payment-method`
- **Description:** Securely adds a payment method.
- **Request:** `{"token": "tok_visa_123", "billing_zip": "90210"}`
- **Response:** `{"status": "success", "method_id": "pm_987"}`

**Endpoint:** `GET /billing/invoices`
- **Description:** Returns a list of historical invoices.
- **Request:** `{"year": 2024, "limit": 10}`
- **Response:** `[{"invoice_id": "inv_001", "amount": 49.99, "date": "2024-01-01", "status": "paid"}]`

### 4.3 Telemetry & Sensors
**Endpoint:** `GET /telemetry/sensors`
- **Description:** Lists all active sensors for the user's account.
- **Request:** `{"farm_id": "f_55"}`
- **Response:** `{"sensors": [{"id": "s1", "type": "moisture", "value": 34.2, "unit": "percentage"}]}`

**Endpoint:** `POST /telemetry/data`
- **Description:** Ingests raw sensor data.
- **Request:** `{"sensor_id": "s1", "value": 35.1, "timestamp": "2025-06-01T12:00:00Z"}`
- **Response:** `{"status": "accepted", "event_id": "ev_999"}`

### 4.4 Webhooks & Integration
**Endpoint:** `POST /webhooks/subscribe`
- **Description:** Subscribes a third-party URL to specific events.
- **Request:** `{"target_url": "https://partner.com/callback", "events": ["THRESHOLD_ALERT"]}`
- **Response:** `{"subscription_id": "sub_444", "secret": "whsec_abc123"}`

**Endpoint:** `DELETE /webhooks/unsubscribe/{id}`
- **Description:** Removes a webhook subscription.
- **Request:** Path parameter `{id}`
- **Response:** `{"status": "deleted"}`

---

## 5. DATABASE SCHEMA

The Ingot project utilizes a hybrid database strategy. Relational data is stored in PostgreSQL, while time-series telemetry is stored in a specialized PostgreSQL extension (TimescaleDB) and metadata in MongoDB.

### 5.1 Table Definitions (PostgreSQL)

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `locale`, `created_at` | 1:M $\rightarrow$ `farms` | Core user identity |
| `farms` | `farm_id` | `owner_id`, `farm_name`, `region_code`, `timezone` | M:1 $\rightarrow$ `users` | Physical farm entities |
| `sensors` | `sensor_id` | `farm_id`, `sensor_type`, `model_number`, `status` | M:1 $\rightarrow$ `farms` | Registered hardware |
| `subscriptions` | `sub_id` | `user_id`, `plan_type`, `start_date`, `end_date` | M:1 $\rightarrow$ `users` | Billing plan state |
| `payment_tokens` | `token_id` | `user_id`, `vault_ref`, `last_four`, `exp_date` | M:1 $\rightarrow$ `users` | PCI Vault references |
| `webhook_configs` | `config_id` | `user_id`, `target_url`, `secret_key`, `is_active` | M:1 $\rightarrow$ `users` | External integration targets |
| `event_logs` | `event_id` | `config_id`, `payload`, `response_code`, `attempt_count` | M:1 $\rightarrow$ `webhook_configs` | Audit trail for webhooks |
| `dashboard_layouts`| `layout_id` | `user_id`, `config_json`, `updated_at` | M:1 $\rightarrow$ `users` | Saved UI grid states |
| `api_keys` | `key_id` | `user_id`, `hashed_key`, `permissions`, `created_at` | M:1 $\rightarrow$ `users` | Access tokens for external API |
| `audit_trail` | `audit_id` | `user_id`, `action`, `timestamp`, `ip_address` | M:1 $\rightarrow$ `users` | Compliance/PCI log |

### 5.2 NoSQL Schema (MongoDB - Telemetry Store)
**Collection:** `sensor_readings`
- `_id`: ObjectId
- `sensor_id`: UUID (Indexed)
- `timestamp`: Date (Sharding key)
- `value`: Double
- `metadata`: Object (e.g., `{ "battery_level": 80, "firmware": "2.1.0" }`)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ingot follows a strict promotion path to ensure stability and regulatory compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Individual feature development and unit testing.
- **Infrastructure:** Local Docker Compose setups and a shared Kubernetes (k8s) namespace in AWS EKS.
- **Data:** Synthetic data only. No real user data is permitted here.
- **Deploy Cycle:** Continuous (on every merge to `develop` branch).

#### 6.1.2 Staging (Staging/QA)
- **Purpose:** Integration testing, UAT (User Acceptance Testing), and Sandbox API hosting.
- **Infrastructure:** Mirror of Production (scaled down to 25% capacity).
- **Data:** Anonymized production snapshots.
- **Deploy Cycle:** Weekly (every Thursday).

#### 6.1.3 Production (Prod)
- **Purpose:** End-user traffic and billing processing.
- **Infrastructure:** Multi-region AWS EKS cluster with Auto-scaling Groups (ASG).
- **Data:** Live encrypted production data.
- **Deploy Cycle:** Quarterly releases (aligned with regulatory review cycles).

### 6.2 CI/CD Pipeline
The current pipeline is a major pain point.
- **Current State:** A Jenkins-based pipeline that executes sequentially. Total runtime: **45 minutes**.
- **Proposed Optimization:** Transition to GitHub Actions with parallel job execution for unit tests and container scanning, aiming to reduce runtime to <10 minutes.

### 6.3 Infrastructure as Code (IaC)
All environments are provisioned via **Terraform v1.5.0**. No manual changes to the AWS Console are permitted. State files are stored in a remote S3 bucket with DynamoDB locking.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Requirement:** 80% minimum code coverage across all microservices.
- **Tools:** Jest (Node.js), JUnit (Java), PyTest (Python).
- **Focus:** Business logic, utility functions, and data transformation layers.

### 7.2 Integration Testing
- **Requirement:** Every service-to-service communication must be verified via contract testing.
- **Tools:** Pact.io for contract testing; Testcontainers for database integration.
- **Focus:** Kafka topic producers/consumers, gRPC calls, and API Gateway routing.

### 7.3 End-to-End (E2E) Testing
- **Requirement:** Critical paths (Login $\rightarrow$ Add Sensor $\rightarrow$ Generate Billing $\rightarrow$ Webhook Trigger) must be automated.
- **Tools:** Cypress for frontend E2E; Postman/Newman for API flows.
- **Focus:** User journeys and cross-service orchestration.

### 7.4 Security Testing
- **Vulnerability Scanning:** Snyk scans on every commit to identify outdated dependencies.
- **Penetration Testing:** Quarterly external audits by a PCI-certified QSA (Qualified Security Assessor).
- **Rate Limit Testing:** Using JMeter to ensure the Kong Gateway successfully drops requests exceeding the defined quotas.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Integration partner's API is undocumented and buggy. | High | High | Escalate to steering committee for additional funding for a dedicated integration engineer. |
| **R2** | Budget may be cut by 30% in the next fiscal quarter. | Medium | High | Document workarounds, prioritize "Critical" features, and share efficiency gains with management. |
| **R3** | PCI DSS audit failure due to legacy data leakage. | Low | Critical | Implement a strict "Data Purge" script for all legacy databases; manual audit of S3 buckets. |
| **R4** | Kafka lag during peak telemetry spikes (harvest season). | Medium | Medium | Implement horizontal scaling of consumer groups and optimize Protobuf serialization. |
| **R5** | Solo developer burnout/bottleneck. | Medium | High | Rigorous documentation of all architectural decisions in JIRA and Slack to enable rapid onboarding. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or legal penalty.
- **High:** Significant delay in milestone delivery.
- **Medium:** Manageable with resource reallocation.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE & PHASES

The project follows a milestone-based funding release.

### Phase 1: Foundation & Consolidation (Jan 2025 – June 2025)
- **Jan - Feb:** Setup of Kong Gateway and Kafka Cluster. Migration of User Auth from 4 tools to 1.
- **Mar - Apr:** Implementation of the Webhook Integration Framework (Complete). Development of the Billing Service (PCI Level 1).
- **May - June:** Integration of legacy telemetry data into the new MongoDB store.
- **Milestone 1: Internal Alpha Release** $\rightarrow$ **Target: 2025-06-15**

### Phase 2: Feature Hardening & Scale (June 2025 – August 2025)
- **June - July:** Implementation of L10n/I18n for 12 languages. Development of the Customizable Dashboard.
- **July - Aug:** Solving the A/B Testing framework blocker. Final security hardening and PCI audit.
- **Milestone 2: Production Launch** $\rightarrow$ **Target: 2025-08-15**

### Phase 3: Optimization & Benchmarking (August 2025 – October 2025)
- **Aug - Sept:** Performance tuning of the Kafka consumers. Parallelization of the CI pipeline.
- **Sept - Oct:** Stress testing the API Gateway under 5x peak load.
- **Milestone 3: Performance Benchmarks Met** $\rightarrow$ **Target: 2025-10-15**

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project guidelines, formal meeting notes are not kept. The following are synthesized from decision-making Slack threads.*

### Thread 1: Topic - Webhook Signing Strategy
**Date:** 2024-11-12
**Participants:** Freya Kim, Cleo Fischer, Finn Gupta
**Discussion:**
- **Finn:** "Should we use simple API keys for webhooks or HMAC signatures?"
- **Cleo:** "PCI DSS and our security posture require non-repudiation. API keys in headers are too risky if the partner logs them. We need HMAC-SHA256."
- **Freya:** "Agreed. Let's go with HMAC. Finn, ensure the secret is stored in Vault, not the app config."
- **Decision:** Implement `X-Hub-Signature-256` for all outgoing webhooks.

### Thread 2: Topic - The CI Pipeline Bottleneck
**Date:** 2024-12-05
**Participants:** Freya Kim, Lina Oduya
**Discussion:**
- **Lina:** "I've been waiting 45 minutes for the build to finish three times today. It's killing my productivity."
- **Freya:** "I know. The legacy Java tests are running sequentially. We need to parallelize the Maven build."
- **Lina:** "Can I try to rewrite the test runner using a matrix in GitHub Actions?"
- **Freya:** "Yes, but don't touch it until after the alpha release. Focus on the L10n design first. We'll prioritize the pipeline in Phase 3."
- **Decision:** CI optimization deferred to Phase 3.

### Thread 3: Topic - Partner API Instability
**Date:** 2025-01-20
**Participants:** Freya Kim, Finn Gupta
**Discussion:**
- **Finn:** "The third-party Ag-Tech API is returning 429 Too Many Requests even when we are under the limit. Their documentation is lying to us."
- **Freya:** "This is the same issue we had last month. We can't build a reliable integration on a buggy API."
- **Finn:** "I can try a caching layer, but it won't solve the real-time requirement."
- **Freya:** "I'm escalating this to the steering committee. We need more funding to either build a custom proxy or pay for a higher-tier support plan from the partner."
- **Decision:** Escalate to steering committee; current blocker logged in JIRA.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the completion of Milestones 1, 2, and 3.

| Category | Allocation (USD) | Description |
| :--- | :--- | :--- |
| **Personnel** | $520,000 | Solo Developer (Primary), DevOps/Security oversight (Part-time). |
| **Infrastructure (AWS)** | $180,000 | EKS Clusters, RDS, S3, Cloudflare Enterprise. |
| **Software & Tools** | $65,000 | Kong Enterprise, Confluent Cloud (Kafka), Snyk, Datadog. |
| **PCI Compliance Audit** | $45,000 | External QSA certification and annual audit fees. |
| **Contingency Fund** | $40,000 | Buffer for partner API issues or emergency scaling. |
| **TOTAL PROJECTED** | **$850,000** | |

**Funding Release Schedule:**
- **Tranche 1 (Start):** $300,000 (Initial setup and framework development).
- **Tranche 2 (Post-Milestone 1):** $300,000 (Feature completion and Beta).
- **Tranche 3 (Post-Milestone 2):** $250,000 (Launch and Performance tuning).

---

## 12. APPENDICES

### Appendix A: Kafka Topic Registry
To ensure consistency across the mixed-stack architecture, all Kafka messages must use the following naming convention: `ingot.<domain>.<event_type>`.

| Topic Name | Producer | Consumer | Payload Format |
| :--- | :--- | :--- | :--- |
| `ingot.billing.payment_success` | Billing Service | Notification Engine | Protobuf (v1.2) |
| `ingot.telemetry.reading_captured` | Telemetry Service | Analytics, Webhook Worker | Protobuf (v1.0) |
| `ingot.user.profile_updated` | Auth Service | All Services (Cache Refresh) | JSON |
| `ingot.device.status_change` | Device Service | Telemetry Service | Protobuf (v1.1) |

### Appendix B: PCI DSS Compliance Checklist for Ingot
The following controls must be verified by Cleo Fischer before Milestone 2:
1. **Firewall Configuration:** Ensure no direct route from the public internet to the `Billing Service` VPC.
2. **Data Encryption:** Verify that `payment_tokens` table in PostgreSQL does not contain raw PANs.
3. **Access Control:** Multi-factor authentication (MFA) required for all SSH access to production nodes.
4. **Logging:** All access to the `audit_trail` table must be logged to a write-once-read-many (WORM) drive.
5. **Key Rotation:** Encryption keys for the Vault must be rotated every 90 days.