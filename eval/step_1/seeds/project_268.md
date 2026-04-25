Due to the extreme length requirement of this request (6,000–8,000 words), the following is a comprehensive, formal Project Specification Document for **Project Obelisk**. This document is designed as the "Single Source of Truth" for the development team at Clearpoint Digital.

***

# PROJECT SPECIFICATION: OBELISK
**Version:** 1.0.4  
**Status:** Draft / Under Review  
**Last Updated:** 2024-10-27  
**Classification:** Confidential / HIPAA Compliant  
**Project Lead:** Esme Gupta (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Obelisk represents the most critical infrastructure upgrade in the history of Clearpoint Digital. For 15 years, the company’s logistics and shipping operations have relied on a monolithic legacy system—hereafter referred to as "The Monolith." While The Monolith served the company during its growth phase, it has become a liability. The system is built on deprecated frameworks, lacks horizontal scalability, and suffers from significant technical debt that prevents the integration of modern machine learning (ML) models for predictive routing and demand forecasting.

The primary objective of Project Obelisk is the deployment of a modern ML-driven orchestration layer to replace The Monolith. Because the entire company depends on this system for real-time shipping manifests and customs documentation, the project has a **zero downtime tolerance**. Any interruption in service during the transition would result in an estimated loss of $140,000 per hour in operational revenue and potential contractual penalties with international shipping partners.

### 1.2 Strategic Objectives
The transition to Obelisk is not merely a "lift and shift" but a fundamental architectural pivot. By moving to a CQRS (Command Query Responsibility Segregation) pattern with Event Sourcing, Clearpoint Digital will gain a granular audit trail of every shipment state change—a requirement for the high-stakes logistics industry. Furthermore, the integration of ML models will optimize route efficiency, reducing fuel costs by a projected 12% and increasing delivery speed by 18%.

### 1.3 ROI Projection
The Return on Investment (ROI) for Project Obelisk is calculated across three primary vectors:
1.  **Operational Efficiency:** Reduction in manual routing adjustments. Projected savings: $2.4M annually.
2.  **Infrastructure Cost Reduction:** Transitioning from legacy on-premise servers to a managed cloud environment with auto-scaling. Projected savings: $400k annually.
3.  **Risk Mitigation:** Elimination of the "single point of failure" inherent in The Monolith's fragile codebase.

The total projected ROI over 36 months is estimated at $8.2M, with the break-even point occurring 14 months post-launch. Funding is released in tranches based on the achievement of specific milestones, ensuring that the company only invests further as the project proves its stability.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Project Obelisk is characterized by a "mixed stack" inheritance. Because we are replacing a 15-year-old system, the new architecture must interoperate with three legacy stacks: a Java 6 monolith, a PHP 5.4 reporting engine, and a Delphi-based warehouse management system.

To manage this complexity, we have adopted **CQRS (Command Query Responsibility Segregation)**. This separates the "write" side (Commands) from the "read" side (Queries), allowing the ML models to update shipment predictions without locking the tables used by the logistics operators to track packages. **Event Sourcing** is implemented for all audit-critical domains (e.g., Chain of Custody, Customs Clearances), ensuring that we store every state change as a sequence of events rather than just the current state.

### 2.2 System Diagram (ASCII Representation)
The following represents the data flow from the Legacy Interface to the Obelisk ML Layer:

```text
[USER INTERFACE] <--> [API GATEWAY (Nginx/Kong)] <--> [AUTH SERVICE (OAuth2/HIPAA)]
                               |
                               v
             __________________________________________
            |        COMMAND SIDE (Write)             |
            |  [API Controller] -> [Command Bus]       |
            |         |               |                |
            |         v               v                |
            |  [Domain Logic] -> [Event Store (NoSQL)] | <--- (Event Sourcing)
            |__________________________________________|
                               |
                               v (Async Projection)
             __________________________________________
            |         QUERY SIDE (Read)                |
            |  [Read Model (PostgreSQL)] <--- [ML Model]| <--- (Predictive Routing)
            |         |                                 |
            |         v                                |
            |  [Read API] -> [Materialized Views]      |
            |__________________________________________|
                               |
                               v
[LEGACY STACK A (Java)] [LEGACY STACK B (PHP)] [LEGACY STACK C (Delphi)]
```

### 2.3 Security and Compliance
Since Clearpoint Digital handles medical shipping logistics, the system must be **HIPAA compliant**. 
- **Encryption at Rest:** All database volumes are encrypted using AES-256.
- **Encryption in Transit:** All internal communication occurs over TLS 1.3.
- **Audit Logs:** The Event Store serves as the immutable record for HIPAA auditing, ensuring no record is ever "deleted," only "countered" by a new event.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Design

**Description:**
To prevent the ML inference endpoints from being overwhelmed by legacy polling mechanisms, a robust rate-limiting layer is required. This system must differentiate between internal service-to-service calls and external partner API calls.

**Functional Requirements:**
- **Tiered Limiting:** Implementation of "Bronze," "Silver," and "Gold" tiers for API keys.
- **Sliding Window Algorithm:** Use of a sliding window log to prevent "bursting" at the turn of the minute.
- **Analytics Pipeline:** Every request must be logged to a time-series database (InfluxDB) to track usage patterns and identify "noisy neighbors."
- **Header Injection:** The API must return `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers.

**Technical Implementation:**
The rate limiter will be implemented as a middleware layer using Redis as the backplane. This ensures that rate limits are synchronized across multiple pods in the Kubernetes cluster. When a limit is exceeded, the system must return a `429 Too Many Requests` response with a `Retry-After` header. The analytics engine will aggregate these hits into a Grafana dashboard for the Tech Lead to monitor.

---

### 3.2 A/B Testing Framework (Feature Flag Integrated)
**Priority:** High | **Status:** In Review

**Description:**
The ML model deployment strategy requires the ability to route a percentage of traffic to a "Challenger" model while the "Champion" model continues to serve the majority of requests. This framework must be baked directly into the feature flag system.

**Functional Requirements:**
- **Dynamic Routing:** Ability to shift traffic from 90/10 to 50/50 via a dashboard without a redeploy.
- **User Stickiness:** A specific user or shipment ID must consistently see the same model version to prevent erratic routing behavior.
- **Metric Correlation:** The system must tag every API response with the `model_version_id` so that downstream analytics can correlate a specific model with delivery efficiency.

**Technical Implementation:**
We will utilize a modified implementation of Unleash or LaunchDarkly. The "Variation" of the feature flag will be determined by a hash of the `CustomerID` modulo 100. This ensures deterministic routing. The ML model wrapper will intercept the flag value and route the request to the corresponding TensorFlow Serving endpoint.

---

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** Blocked (Awaiting Legal)

**Description:**
Shipping manifests and customs documents often arrive as PDFs or images. These must be uploaded, scanned for malware, and then distributed via a CDN for global access by port authorities.

**Functional Requirements:**
- **Asynchronous Scanning:** Files are uploaded to a "Quarantine" S3 bucket. A Lambda trigger kicks off a ClamAV scan.
- **Promotion Logic:** Files that pass scanning are moved to the "Clean" bucket and indexed in the database.
- **CDN Integration:** Clean files are served via CloudFront with signed URLs that expire after 4 hours.
- **HIPAA Sanitization:** Metadata must be stripped from files before they are cached on the CDN.

**Technical Implementation:**
The upload flow will use S3 Pre-signed URLs to reduce load on the API servers. Once the `S3:ObjectCreated` event fires, an AWS Lambda function invokes the virus scanner. If a threat is detected, the file is deleted immediately, and a `SecurityAlert` event is published to the Event Store. This feature is currently blocked pending the Legal Review of the Data Processing Agreement (DPA) regarding third-party scanning services.

---

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** Complete

**Description:**
Stakeholders require daily, weekly, and monthly summaries of shipping volumes and ML accuracy metrics. These reports must be generated automatically and delivered via email or SFTP.

**Functional Requirements:**
- **Template Engine:** Support for dynamic PDF layouts using Headless Chrome (Puppeteer).
- **CSV Export:** High-performance streaming export for datasets exceeding 100,000 rows.
- **Scheduler:** A cron-based system to trigger reports at specific UTC times.
- **Delivery Gateways:** Integration with SendGrid for email and an internal SFTP server for legacy partners.

**Technical Implementation:**
The system utilizes a worker-queue pattern (Celery + RabbitMQ). The "Report Generator" worker queries the Read Model (PostgreSQL), generates the file in a temporary volume, uploads it to a secure vault, and notifies the delivery service. This is the only feature currently marked as "Complete" and has been verified by Wyatt Jensen (QA Lead).

---

### 3.5 Localization and Internationalization (i18n)
**Priority:** Low | **Status:** In Review

**Description:**
As Clearpoint Digital expands into the EMEA and APAC markets, the Obelisk dashboard must support 12 different languages to accommodate regional logistics operators.

**Functional Requirements:**
- **Dynamic Translation:** Support for JSON-based translation keys.
- **Locale Detection:** Support for `Accept-Language` headers and user-profile overrides.
- **RTL Support:** UI layout must support Right-to-Left (RTL) languages such as Arabic.
- **Date/Currency Formatting:** Automatic formatting of dates (ISO vs US) and currencies based on the locale.

**Technical Implementation:**
The frontend (React) will use `react-i18next`. Translation files will be hosted in a separate Git repository to allow non-technical translators to submit PRs without touching the application code. This feature is currently low priority as the initial launch targets the North American market.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer` token in the Authorization header.

### 4.1 `POST /shipments`
**Description:** Creates a new shipment entry and triggers the initial ML routing prediction.
- **Request Body:**
  ```json
  {
    "origin_id": "NYC-01",
    "destination_id": "LON-05",
    "weight_kg": 45.2,
    "priority": "express",
    "contents": "Medical Supplies"
  }
  ```
- **Response (202 Accepted):**
  ```json
  {
    "shipment_id": "OB-9928374",
    "status": "pending_prediction",
    "estimated_completion": "2025-05-15T10:00:00Z"
  }
  ```

### 4.2 `GET /shipments/{id}`
**Description:** Retrieves the current state and prediction of a specific shipment.
- **Response (200 OK):**
  ```json
  {
    "shipment_id": "OB-9928374",
    "current_location": "JFK_AIRPORT",
    "predicted_route": ["JFK", "LHR", "LON-05"],
    "eta": "2025-05-18T14:00:00Z",
    "model_version": "v2.1.4-beta"
  }
  ```

### 4.3 `PUT /shipments/{id}/route`
**Description:** Manually overrides the ML-predicted route. (Triggers an Event in the Event Store).
- **Request Body:**
  ```json
  {
    "new_route": ["JFK", "CDG", "LON-05"],
    "reason": "Weather delay at LHR",
    "operator_id": "USER-882"
  }
  ```
- **Response (200 OK):**
  ```json
  { "status": "updated", "event_id": "evt_55621" }
  ```

### 4.4 `GET /analytics/usage`
**Description:** Returns usage statistics for a specific API key.
- **Response (200 OK):**
  ```json
  {
    "api_key": "key_prod_882",
    "requests_24h": 45000,
    "limit_24h": 50000,
    "burst_count": 12
  }
  ```

### 4.5 `POST /reports/generate`
**Description:** Manually triggers a PDF/CSV report generation.
- **Request Body:**
  ```json
  {
    "report_type": "monthly_efficiency",
    "format": "pdf",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
  ```
- **Response (201 Created):**
  ```json
  { "job_id": "job_abc_123", "status": "queued" }
  ```

### 4.6 `GET /reports/download/{job_id}`
**Description:** Downloads a generated report from the secure vault.
- **Response:** Binary stream of PDF/CSV file.

### 4.7 `POST /upload/document`
**Description:** Uploads a manifest file (Currently Blocked).
- **Request Body:** `multipart/form-data` containing file and `shipment_id`.
- **Response (202 Accepted):**
  ```json
  { "upload_id": "up_772", "status": "scanning" }
  ```

### 4.8 `PATCH /flags/ab-test`
**Description:** Adjusts the traffic split for an ML model A/B test.
- **Request Body:**
  ```json
  {
    "test_id": "route_model_v2",
    "champion_weight": 80,
    "challenger_weight": 20
  }
  ```
- **Response (200 OK):**
  ```json
  { "status": "updated", "active_split": "80/20" }
  ```

---

## 5. DATABASE SCHEMA

The system utilizes a polyglot persistence strategy. The **Event Store** is NoSQL (MongoDB), while the **Read Model** is Relational (PostgreSQL).

### 5.1 Read Model (PostgreSQL) - Tables

| Table Name | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- |
| `shipments` | `id` (PK), `current_status`, `created_at` | 1:N with `route_logs` | Core shipment state |
| `customers` | `id` (PK), `company_name`, `hipaa_consent` | 1:N with `shipments` | Customer profile |
| `routes` | `id` (PK), `segment_start`, `segment_end` | N:M with `shipments` | Pre-defined shipping lanes |
| `predictions` | `id` (PK), `shipment_id` (FK), `model_id` | N:1 with `shipments` | ML output storage |
| `users` | `id` (PK), `username`, `role_id` (FK) | N:1 with `roles` | System access |
| `roles` | `id` (PK), `role_name` | 1:N with `users` | Permission levels |
| `api_keys` | `key_hash` (PK), `user_id` (FK), `tier` | N:1 with `users` | Rate limiting keys |
| `report_jobs` | `id` (PK), `user_id` (FK), `status` | N:1 with `users` | Report tracking |
| `audit_logs` | `id` (PK), `event_id` (FK), `timestamp` | 1:1 with `events` | Relational audit view |
| `localization_meta`| `locale_id` (PK), `language_name` | N:A | i18n mapping |

### 5.2 Event Store (MongoDB) - Schema
The Event Store does not use traditional tables but documents. Each document represents a state change.

**Collection: `shipment_events`**
- `eventId`: UUID (Primary Key)
- `aggregateId`: ShipmentID (Indexing Key)
- `eventType`: (e.g., `ShipmentCreated`, `RoutePredicted`, `CustomsCleared`)
- `payload`: JSON blob containing the change
- `timestamp`: ISO8601
- `version`: Integer (for optimistic locking)
- `metadata`: `{ "userId": "...", "ipAddress": "...", "modelVersion": "..." }`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Overview
Obelisk is deployed on AWS using EKS (Elastic Kubernetes Service). Due to the "Bus Factor of 1" risk, all deployment scripts are stored in a centralized Git repository, though they are executed manually by the single DevOps engineer.

### 6.2 Environments

#### Dev Environment (`dev-cluster`)
- **Purpose:** Sandbox for developers to test new features.
- **Database:** Shared instance of PostgreSQL and MongoDB.
- **Deployment:** Automatic on merge to `develop` branch.
- **Data:** Anonymized subsets of production data.

#### Staging Environment (`stg-cluster`)
- **Purpose:** Pre-production validation and QA.
- **Database:** Isolated instances; mirrors production configuration.
- **Deployment:** Manual trigger by Wyatt Jensen (QA Lead).
- **Data:** Full sanitized copy of production data.

#### Production Environment (`prod-cluster`)
- **Purpose:** Live shipping operations.
- **Database:** High-availability (Multi-AZ) RDS and MongoDB Atlas.
- **Deployment:** Manual deployment performed by the DevOps engineer. 
- **Strictness:** Zero-downtime requirement. Use of Blue/Green deployments to allow instant rollback.

### 6.3 CI/CD Pipeline Technical Debt
The current CI pipeline is a significant bottleneck.
- **Issue:** The pipeline takes **45 minutes** to complete.
- **Cause:** Lack of parallelization in the test suite and sequential Docker image building.
- **Current State:** The `Jenkinsfile` runs `npm test`, `pytest`, and `go test` sequentially.
- **Proposed Fix:** Implement Matrix builds in Jenkins to run test suites in parallel across three different nodes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every business logic component must have >80% code coverage.
- **Tools:** PyTest (Python), Jest (React), JUnit (Java Legacy Bridge).
- **Focus:** Pure functions and domain entities. Mocking is mandatory for all external API calls.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the Command side and the Event Store.
- **Scenario:** A `CreateShipment` command is issued $\rightarrow$ Event is written to MongoDB $\rightarrow$ Projection updates PostgreSQL Read Model.
- **Validation:** Verify that the Read Model is eventually consistent within 500ms.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulating a full shipment lifecycle from creation to delivery.
- **Tools:** Playwright.
- **Critical Path:** "Create Shipment" $\rightarrow$ "Wait for ML Prediction" $\rightarrow$ "Approve Route" $\rightarrow$ "Generate PDF Manifest."

### 7.4 Performance Testing
- **Benchmark:** The system must handle 500 requests per second (RPS) with a P99 latency of <200ms.
- **Tool:** JMeter.
- **Target Date:** 2025-05-15 (Milestone 1).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Budget cut by 30% in next fiscal quarter | Medium | High | Accept risk; monitor weekly; prioritize "Must-Have" features. |
| **R-02** | Team lack of experience with CQRS/Event Sourcing | High | Medium | Assign Ravi Santos as the dedicated owner to track and resolve technical gaps. |
| **R-03** | Legacy system instability during migration | Low | Critical | Implement a "Strangler Fig" pattern; migrate one module at a time. |
| **R-04** | DevOps "Bus Factor of 1" (Single person dependency) | High | High | Document all deployment steps in Wiki; cross-train Ravi Santos on basic K8s commands. |
| **R-05** | Legal delay on Data Processing Agreement (DPA) | High | Medium | Continue developing "File Upload" locally using mock scanners; cannot deploy to Staging. |

---

## 9. TIMELINE & GANTT DESCRIPTION

### Phase 1: Foundation & Core ML Integration (Now – 2025-05-15)
- **Focus:** Setting up the CQRS infrastructure and integrating the first set of ML models.
- **Dependency:** Successful setup of the Event Store.
- **Key Goal:** Meet Performance Benchmarks (Milestone 1).

### Phase 2: Feature Expansion & Integration (2025-05-16 – 2025-07-15)
- **Focus:** Implementing A/B testing frameworks, finalizing Report Generation, and attempting File Upload (pending legal).
- **Dependency:** Completion of the API Rate Limiting design.
- **Key Goal:** Stakeholder Demo and Sign-off (Milestone 2).

### Phase 3: Migration & Onboarding (2025-07-16 – 2025-09-15)
- **Focus:** Parallel running of Obelisk and The Monolith. Gradual traffic shift.
- **Dependency:** Passing the external HIPAA audit.
- **Key Goal:** First paying customer onboarded (Milestone 3).

---

## 10. MEETING NOTES
*Note: These are extracted from the shared 200-page running document. Search is not available; these were found by scrolling manually.*

### Meeting 1: Architecture Sync (2024-11-02)
**Attendees:** Esme, Ravi, Wyatt, Rafik
- **Discussion:** Ravi expressed concern that Event Sourcing might be "overkill" for the shipment tracking module. Esme countered that the audit requirements for HIPAA and international customs make the immutable log non-negotiable.
- **Decision:** Proceed with Event Sourcing for the `shipments` and `customs` domains. Use standard CRUD for the `users` and `roles` domains to simplify development.
- **Action Item:** Ravi to create a PoC of the Event Store by Friday.

### Meeting 2: The "Budget Panic" (2024-11-15)
**Attendees:** Esme, Company Executives
- **Discussion:** CFO mentioned a potential 30% budget cut for Q1 due to shipping volume drops in the APAC region.
- **Decision:** The team will not cut scope yet. Instead, we will monitor the burn rate weekly. If the cut happens, we will move "Localization" and "File Upload" to the "Post-Launch" backlog.
- **Action Item:** Esme to update the Risk Register.

### Meeting 3: CI/CD Bottleneck Session (2024-12-01)
**Attendees:** Esme, DevOps Person, Ravi
- **Discussion:** Team is frustrated that the CI pipeline takes 45 minutes. Rafik mentioned that he spends 2 hours a day just waiting for builds.
- **Decision:** The DevOps person agrees to look into parallelizing the test runners.
- **Action Item:** DevOps to provide a report on potential Jenkins plugins for parallelization by next sprint.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches. The following is the projected spend for the total project lifecycle.

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,200,000 | Includes Esme, Ravi, Wyatt, and Rafik (Contractor). |
| **Infrastructure** | 20% | $400,000 | AWS EKS, RDS, MongoDB Atlas, CloudFront. |
| **Tools/Licenses** | 10% | $200,000 | Datadog, New Relic, SendGrid, Unleash Enterprise. |
| **Contingency** | 10% | $200,000 | Reserved for unexpected legal costs or emergency scaling. |
| **TOTAL** | **100%** | **$2,000,000** | |

---

## 12. APPENDICES

### Appendix A: ML Model Versioning Strategy
To ensure reproducibility, all ML models are versioned using a Semantic Versioning (SemVer) approach combined with a git hash of the training dataset.
- **Version Format:** `v[Major].[Minor].[Patch]-[DatasetHash]`
- **Example:** `v2.1.4-a7b8c9d`
- **Storage:** Models are stored in an S3 bucket under `/models/{version}/model.pb`.
- **Deployment:** The A/B testing framework (Feature 3.2) calls these specific paths to load the model into the TensorFlow Serving container.

### Appendix B: HIPAA Data Mapping
The following fields are identified as Protected Health Information (PHI) and must be encrypted using the application-layer encryption (ALE) before being written to the Event Store.

| Field Name | Source | Encryption Level | Access Level |
| :--- | :--- | :--- | :--- |
| `patient_name` | Shipment Manifest | AES-256-GCM | Level 1 (Medical Lead) |
| `medical_id` | Shipping Label | AES-256-GCM | Level 1 (Medical Lead) |
| `destination_address`| Shipping Label | AES-256-GCM | Level 2 (Logistics Op) |
| `contents_description`| Manifest | AES-256-GCM | Level 2 (Logistics Op) |

*End of Document*