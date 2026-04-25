# PROJECT SPECIFICATION DOCUMENT: PROJECT DRIFT
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Project Code:** DRIFT-BT-2025  
**Company:** Bellweather Technologies  
**Date:** October 24, 2024  
**Classification:** Confidential / Regulatory Compliance  

---

## 1. EXECUTIVE SUMMARY

Project Drift is a mission-critical machine learning (ML) model deployment initiative undertaken by Bellweather Technologies to address an urgent regulatory compliance gap within the healthcare sector. The project is driven by an immutable legal deadline occurring six months from the project start date. Failure to deploy the Drift framework by this date would result in significant legal penalties, loss of licensure in key European markets, and a catastrophic breach of regulatory trust.

The core objective of Drift is to modernize the deployment pipeline for Bellweather’s predictive healthcare models, transitioning from a legacy, monolithic structure to a scalable, three-tier architecture that ensures data residency compliance (GDPR and CCPA) and enhances operational efficiency. The project is not merely a technical upgrade but a strategic business pivot. By implementing the Drift framework, Bellweather will be able to deploy models that adhere to strict EU data sovereignty laws, allowing the company to capture untapped market share in Germany and France.

**Business Justification and ROI Projection**
The business justification for Project Drift rests on two pillars: Risk Mitigation and Revenue Growth. From a risk perspective, the cost of non-compliance is estimated at up to 4% of annual global turnover under GDPR, far exceeding the project's $800,000 budget. From a growth perspective, the ability to offer a compliant, high-performance ML deployment environment allows Bellweather to enter the "High-Compliance Healthcare" tier, attracting premium clients who require rigorous audit trails and data residency.

The projected Return on Investment (ROI) is quantified through two primary metrics:
1. **Direct Revenue:** A projected $500,000 in new revenue attributed directly to the Drift product within the first 12 months post-launch. This will be driven by the ability to sign three major EU-based healthcare providers currently stalled in the sales pipeline due to compliance blockers.
2. **Operational Efficiency:** A targeted 35% reduction in cost per transaction compared to the legacy system. By optimizing the inference layer and moving away from expensive, over-provisioned legacy VMs toward a more streamlined three-tier architecture with efficient resource utilization, the company expects to save approximately $12,000 per month in cloud compute costs.

The project is supported by a high-trust, low-ceremony team of eight specialists, led by Ravi Liu. With a comfortable budget of $800,000 and a disciplined approach to technical debt, Project Drift is positioned to meet its legal obligations while providing a scalable foundation for future ML innovations.

---

## 2. TECHNICAL ARCHITECTURE

Project Drift employs a traditional three-tier architecture (Presentation, Business Logic, Data) designed to interoperate across three legacy stacks inherited from previous acquisitions (Stack A: Python/Django, Stack B: Node.js/Express, Stack C: Java/Spring Boot). The primary challenge is ensuring these disparate environments communicate via a unified API gateway.

### 2.1 Architectural Components
- **Presentation Tier:** A React-based dashboard for model monitoring and a customer-facing API. This tier handles request routing, authentication via OAuth2/OpenID Connect, and the rendering of compliance reports.
- **Business Logic Tier (Application Layer):** This consists of the ML Inference Engine, the Webhook Framework, and the Report Generator. It is hosted in a containerized environment (Kubernetes) to allow for canary releases. Logic is partitioned by service: the Inference Service handles model predictions, while the Integration Service handles third-party webhooks.
- **Data Tier:** A hybrid database approach utilizing PostgreSQL for relational metadata and an S3-compatible object store for ML model weights and large-scale audit logs. To meet GDPR/CCPA requirements, data residency is enforced via region-locked clusters in the EU (AWS eu-central-1).

### 2.2 ASCII Architecture Diagram

```text
[ CLIENT LAYER ] <---> [ API GATEWAY / LOAD BALANCER ]
                               |
                               v
                     [ PRESENTATION TIER ]
                     (React UI / Public API)
                               |
                               | (REST/gRPC)
                               v
                     [ BUSINESS LOGIC TIER ]
      _________________________|_________________________
     |                         |                         |
 [ ML Inference ]      [ Webhook Framework ]     [ Report Engine ]
 (Canary Deploy)       (Third-Party Sync)         (PDF/CSV Gen)
     |                         |                         |
     |_________________________|_________________________|
                               |
                               v
                        [ DATA TIER ]
      _________________________|_________________________
     |                         |                         |
 [ PostgreSQL DB ]     [ Object Store (S3) ]    [ Tamper-Proof Log ]
 (Metadata/Users)     (Model Weights/PDFs)     (Audit Trail/WORM)
     |                         |                         |
     └---[ EU RESIDENCY ZONE ]---[ EU RESIDENCY ZONE ]---┘
```

### 2.3 Stack Interoperability
To bridge the three legacy stacks, Drift utilizes a "Sidecar" pattern. Each legacy service is wrapped in a lightweight Go-based proxy that standardizes logging and header propagation, ensuring that a request originating in the Node.js stack can seamlessly trigger a process in the Java stack without losing the trace ID or security context.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** Not Started
**Description:** 
The Webhook Integration Framework is the most critical component of Project Drift. It provides a standardized mechanism for Bellweather's ML models to communicate with third-party healthcare tools (e.g., Electronic Health Record (EHR) systems, billing software, and patient portals). The framework must support bi-directional communication: receiving triggers from external systems and sending model inference results back to those systems.

**Functional Requirements:**
- **Event Subscription:** Users must be able to define "Event Triggers" (e.g., `prediction.completed`, `data.drift_detected`) and associate them with a destination URL.
- **Payload Standardization:** All outgoing webhooks must follow a strict JSON schema version 2.1 to ensure compatibility across different EHR vendors.
- **Retry Logic:** An exponential backoff strategy is required for failed deliveries. The system should attempt delivery 5 times over 24 hours before marking the webhook as "failed."
- **Security:** Every webhook payload must include a `X-Bellweather-Signature` header (HMAC-SHA256) allowing the receiver to verify the authenticity of the request.
- **Delivery Guarantee:** Implementation of a "At-Least-Once" delivery guarantee using a message queue (RabbitMQ) to prevent data loss during spikes.

**Technical Constraints:**
The framework must handle a burst capacity of 1,000 events per second without increasing the latency of the core inference engine. It must be decoupled from the main business logic via an asynchronous event bus.

---

### 3.2 PDF/CSV Report Generation
**Priority:** Medium | **Status:** Not Started
**Description:**
Regulatory compliance requires that Bellweather provide periodic "Model Validity Reports." These reports must summarize model performance, data drift metrics, and a list of all interventions made by human operators. The feature will allow administrators to generate these reports on-demand or via a recurring schedule.

**Functional Requirements:**
- **Templates:** The system must support three distinct templates: Regulatory Compliance, Executive Summary, and Technical Audit.
- **Scheduled Delivery:** Users can set a Cron-based schedule (e.g., `0 0 1 * *` for monthly) to automatically generate and email reports to a list of stakeholders.
- **Export Formats:** High-fidelity PDFs (for regulatory submission) and CSVs (for data analysis in Excel/Tableau).
- **Data Aggregation:** The engine must query the PostgreSQL database for the last 30 days of performance metrics and aggregate them into a summary table.
- **Storage:** Generated reports must be stored in the EU-based S3 bucket for 7 years to meet medical record retention laws.

**Technical Constraints:**
Report generation is a resource-intensive task. It must be implemented as a background worker process (Celery) to avoid blocking the main application thread. PDF generation will use the `WeasyPrint` library for CSS-based styling.

---

### 3.3 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** In Review
**Description:**
Healthcare providers often operate in environments with unstable internet connectivity (e.g., radiology basements or rural clinics). This feature allows the presentation tier to function without an active connection, queuing requests locally and syncing them once connectivity is restored.

**Functional Requirements:**
- **Client-Side Storage:** Use IndexedDB to cache the last 50 model requests and results locally on the user's browser.
- **Optimistic UI:** The UI must show "Pending" status for any action taken offline, updating to "Synced" once the server acknowledges the request.
- **Conflict Resolution:** Use a "Last-Write-Wins" strategy for simple metadata and a "Merge-Conflict" prompt for critical model configuration changes.
- **Background Sync API:** Implementation of the Service Worker Background Sync API to push queued requests to the server even if the browser tab is closed.
- **Data Integrity:** All offline data must be encrypted at rest on the client device using AES-256 to prevent unauthorized access to PHI (Protected Health Information).

**Technical Constraints:**
The system must distinguish between "Read-Only" offline mode (viewing cached reports) and "Read-Write" offline mode (queuing new inference requests).

---

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Medium | **Status:** In Design
**Description:**
To enable third-party developers to build on top of Bellweather’s ML models, Project Drift will expose a public REST API. To prevent breaking changes and allow for safe testing, the API will include strict versioning and a dedicated sandbox environment.

**Functional Requirements:**
- **Semantic Versioning:** Endpoints must be prefixed by version (e.g., `/v1/predict`, `/v2/predict`). The system must support two concurrent major versions.
- **Sandbox Environment:** A mirrored environment with synthetic data where customers can test their integrations without affecting production data or incurring costs.
- **API Key Management:** A self-service portal for users to generate, rotate, and revoke API keys.
- **Rate Limiting:** Implementation of a token-bucket algorithm to limit requests based on the customer's subscription tier (e.g., 100 requests/min for Basic, 1,000 for Enterprise).
- **Documentation:** Auto-generated Swagger/OpenAPI 3.0 documentation that is always in sync with the current deployment.

**Technical Constraints:**
The sandbox must be logically isolated from the production database to ensure no real patient data is ever exposed to the API sandbox.

---

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low (Nice to Have) | **Status:** Blocked
**Description:**
This feature provides an immutable log of every action taken within the Drift system. Every API call, configuration change, and data access event must be recorded in a way that proves the log has not been altered after the fact.

**Functional Requirements:**
- **Comprehensive Logging:** Capture User ID, Timestamp, IP Address, Action Performed, and the "Before/After" state of the modified object.
- **Hash Chaining:** Each log entry must contain a SHA-256 hash of the previous entry, creating a blockchain-like chain that makes unauthorized deletions detectable.
- **WORM Storage:** Logs must be written to "Write Once, Read Many" (WORM) storage (e.g., AWS S3 Object Lock) to prevent modification.
- **Audit Search:** An administrative interface to query logs by user, date range, or event type.
- **Alerting:** Immediate notification to the Security Engineer (Quinn Fischer) if a hash chain discontinuity is detected.

**Technical Constraints:**
Currently blocked due to the lack of a finalized legal definition of "tamper-evident" for the specific EU region. Once defined, this will be implemented using an Amazon QLDB (Quantum Ledger Database) for high-integrity logging.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the `Authorization` header. Base URL: `https://api.bellweather-drift.eu/v1`

### 4.1 `POST /inference/predict`
**Description:** Submits a patient data payload for ML model prediction.
- **Request:**
  ```json
  {
    "patient_id": "PAT-99283",
    "metrics": { "blood_pressure": "120/80", "glucose": 95 },
    "model_version": "2.4.1"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "prediction_id": "PRED-112233",
    "result": "low_risk",
    "confidence": 0.98,
    "timestamp": "2025-01-10T14:22:01Z"
  }
  ```

### 4.2 `GET /inference/history/{patient_id}`
**Description:** Retrieves the prediction history for a specific patient.
- **Request:** `/inference/history/PAT-99283`
- **Response (200 OK):**
  ```json
  {
    "patient_id": "PAT-99283",
    "history": [
      { "date": "2024-11-01", "result": "moderate_risk" },
      { "date": "2025-01-10", "result": "low_risk" }
    ]
  }
  ```

### 4.3 `POST /webhooks/subscribe`
**Description:** Registers a third-party URL to receive event notifications.
- **Request:**
  ```json
  {
    "event_type": "prediction.completed",
    "target_url": "https://client-ehr.com/webhook",
    "secret": "whsec_abc123"
  }
  ```
- **Response (201 Created):**
  ```json
  { "subscription_id": "SUB-5544", "status": "active" }
  ```

### 4.4 `GET /reports/generate`
**Description:** Triggers a manual generation of a compliance report.
- **Request:**
  ```json
  {
    "report_type": "regulatory",
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "format": "pdf"
  }
  ```
- **Response (202 Accepted):**
  ```json
  { "job_id": "JOB-887", "estimated_completion": "30s" }
  ```

### 4.5 `GET /reports/download/{job_id}`
**Description:** Downloads a previously generated report.
- **Request:** `/reports/download/JOB-887`
- **Response:** Binary stream (application/pdf)

### 4.6 `PATCH /config/model-params`
**Description:** Updates hyperparameters for a deployed model.
- **Request:**
  ```json
  {
    "model_id": "ML-DR-01",
    "params": { "threshold": 0.85, "weight_decay": 0.001 }
  }
  ```
- **Response (200 OK):**
  ```json
  { "status": "updated", "version": "2.4.2" }
  ```

### 4.7 `GET /sandbox/test-predict`
**Description:** Sandbox-only endpoint for testing payload validity without costing credits.
- **Request:** Same as `/inference/predict`
- **Response (200 OK):**
  ```json
  { "sandbox_mode": true, "validation": "success", "mock_result": "low_risk" }
  ```

### 4.8 `DELETE /api-keys/{key_id}`
**Description:** Revokes a specific API key.
- **Request:** `/api-keys/key_88221`
- **Response (204 No Content):** Empty.

---

## 5. DATABASE SCHEMA

Project Drift utilizes a PostgreSQL 15 database. All tables are hosted in the `eu-central-1` region.

### 5.1 Table Definitions

1. **`users`**
   - `user_id` (UUID, PK): Unique identifier.
   - `email` (VARCHAR, Unique): User's login email.
   - `role` (ENUM): 'admin', 'analyst', 'provider'.
   - `created_at` (TIMESTAMP): Account creation date.

2. **`patients`**
   - `patient_id` (UUID, PK): Unique identifier.
   - `encrypted_name` (TEXT): AES-256 encrypted name.
   - `region` (VARCHAR): EU member state (for residency tracking).
   - `consent_status` (BOOLEAN): GDPR consent flag.

3. **`ml_models`**
   - `model_id` (UUID, PK): Unique identifier.
   - `version` (VARCHAR): Semantic version (e.g., "2.4.1").
   - `weights_path` (TEXT): Path to S3 object.
   - `deployed_at` (TIMESTAMP): Deployment timestamp.

4. **`predictions`**
   - `prediction_id` (UUID, PK): Unique identifier.
   - `patient_id` (UUID, FK): Reference to `patients`.
   - `model_id` (UUID, FK): Reference to `ml_models`.
   - `result` (TEXT): The prediction outcome.
   - `confidence` (FLOAT): Confidence score (0.0-1.0).

5. **`webhook_subscriptions`**
   - `sub_id` (UUID, PK): Unique identifier.
   - `user_id` (UUID, FK): Reference to `users`.
   - `target_url` (TEXT): The destination URL.
   - `event_type` (VARCHAR): Trigger event.
   - `secret_hash` (TEXT): Hashed secret for signature verification.

6. **`webhook_logs`**
   - `log_id` (BIGINT, PK): Sequential ID.
   - `sub_id` (UUID, FK): Reference to `webhook_subscriptions`.
   - `payload` (JSONB): The sent data.
   - `response_code` (INT): HTTP response from client.
   - `attempt_count` (INT): Number of retry attempts.

7. **`reports`**
   - `report_id` (UUID, PK): Unique identifier.
   - `user_id` (UUID, FK): User who requested the report.
   - `s3_url` (TEXT): Location of the generated file.
   - `report_type` (VARCHAR): 'regulatory', 'executive', 'technical'.
   - `generated_at` (TIMESTAMP): Completion time.

8. **`report_schedules`**
   - `schedule_id` (UUID, PK): Unique identifier.
   - `cron_expression` (VARCHAR): Timing logic.
   - `recipient_emails` (TEXT[]): Array of email addresses.
   - `last_run` (TIMESTAMP): Last execution date.

9. **`api_keys`**
   - `key_id` (UUID, PK): Unique identifier.
   - `user_id` (UUID, FK): Owner of the key.
   - `key_hash` (TEXT): Hashed API key.
   - `rate_limit_tier` (VARCHAR): 'basic', 'enterprise'.
   - `expires_at` (TIMESTAMP): Key expiration date.

10. **`audit_logs`**
    - `event_id` (BIGINT, PK): Sequential ID.
    - `user_id` (UUID, FK): Actor.
    - `action` (VARCHAR): The operation performed.
    - `prev_hash` (TEXT): Hash of the previous log entry.
    - `current_hash` (TEXT): SHA-256 hash of current entry.

### 5.2 Relationships
- `users` $\rightarrow$ `webhook_subscriptions` (1:N)
- `patients` $\rightarrow$ `predictions` (1:N)
- `ml_models` $\rightarrow$ `predictions` (1:N)
- `users` $\rightarrow$ `reports` (1:N)
- `webhook_subscriptions` $\rightarrow$ `webhook_logs` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Drift utilizes three distinct environments to ensure stability and regulatory compliance.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and unit testing.
- **Infrastructure:** Local Docker Compose and a shared AWS `t3.medium` instance.
- **Data:** Fully synthetic data; no real PHI is permitted.
- **Deploy Cycle:** Continuous Integration (CI) on every git push.

**2. Staging (Stage):**
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Infrastructure:** A mirrored replica of the production environment in `eu-central-1`.
- **Data:** Anonymized production data.
- **Deploy Cycle:** Weekly merges from `develop` to `staging` branch.

**3. Production (Prod):**
- **Purpose:** Live regulatory compliance and customer serving.
- **Infrastructure:** High-availability Kubernetes cluster (EKS) across three availability zones in Frankfurt.
- **Data:** Real PHI, encrypted at rest and in transit.
- **Deploy Cycle:** Gated releases using LaunchDarkly feature flags and canary deployments.

### 6.2 Canary Release Process
To mitigate risk, all new ML models and features are deployed via a Canary process:
1. **Phase 1 (1% Traffic):** The new version is deployed to a single pod. Metrics are monitored for 2 hours.
2. **Phase 2 (10% Traffic):** If error rates remain $< 0.1\%$, traffic is increased to 10%.
3. **Phase 3 (50% Traffic):** Performance benchmarks (latency/throughput) are compared against the baseline.
4. **Phase 4 (100% Traffic):** Full rollout.

### 6.3 Feature Flagging
LaunchDarkly is used to decouple deployment from release. For example, the "Offline-First Mode" will be deployed to production code but kept "OFF" via a feature flag until the final QA sign-off is received from Yael Oduya.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Every individual function and class.
- **Tooling:** `pytest` (Python), `Jest` (Node.js), `JUnit` (Java).
- **Requirement:** Minimum 80% code coverage for the Business Logic Tier.
- **Execution:** Runs automatically on every Pull Request via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Communication between the three legacy stacks and the database.
- **Methodology:** "Contract Testing" using Pact. This ensures that if the Node.js stack changes its API response, the Java stack is notified immediately.
- **Database Tests:** Use of ephemeral PostgreSQL containers (Testcontainers) to verify schema migrations without affecting staging.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "User uploads data $\rightarrow$ Model predicts $\rightarrow$ Webhook triggers $\rightarrow$ Report is generated").
- **Tooling:** Cypress for UI flows; Postman/Newman for API flows.
- **Frequency:** Full E2E suite runs every Sunday at 02:00 UTC.

### 7.4 Performance & Stress Testing
Given the requirement that the system must handle 10x the current capacity, a dedicated stress test suite is implemented using `k6`.
- **Baseline:** Current capacity (X).
- **Target:** 10X load for 4 hours without degradation in response time (P99 $< 200\text{ms}$).
- **Failure Mode:** Testing the "Circuit Breaker" pattern to ensure the system fails gracefully rather than crashing.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | Medium | High | Hire a specialized contractor to reduce "bus factor" and allow for flexible scaling of labor costs. |
| R-02 | Performance requirements 10x current capacity with no extra infra budget | High | Critical | Engage external consultant for an independent assessment of the inference engine's efficiency. |
| R-03 | Delay in EU regulatory definition of "Tamper-Evident" | High | Low | Keep the Audit Trail feature as "Low Priority" and blocked until legal clarity is provided. |
| R-04 | Interoperability failure between the 3 legacy stacks | Medium | Medium | Implement a standardized Sidecar proxy and strict API contract testing. |
| R-05 | Data residency breach (Data leaking outside EU) | Low | Critical | Implement strict AWS IAM policies and region-lock buckets; conduct monthly residency audits. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project stoppage or legal failure.
- **High:** Significant delay or budget overage.
- **Medium:** Moderate impact on timeline; manageable.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project timeline is a strict 6-month sprint ending on the legal deadline.

### Phase 1: Foundation & Security (Month 1-2)
- **Focus:** Setting up the three-tier architecture and EU data residency.
- **Dependencies:** Infrastructure provisioning must be complete before the Security Audit.
- **Key Target:** **Milestone 1 (Security Audit Passed) - 2025-03-15**.

### Phase 2: Core Feature Implementation (Month 3-4)
- **Focus:** Building the Webhook Framework (Critical) and API Versioning.
- **Dependencies:** Webhook framework must be finished before the Sandbox API is finalized.
- **Key Target:** Alpha release to internal stakeholders.

### Phase 3: Optimization & Stability (Month 5)
- **Focus:** Report Generation and Offline-First mode.
- **Dependencies:** Stability of the core inference engine.
- **Key Target:** **Milestone 2 (Post-launch Stability Confirmed) - 2025-05-15**.

### Phase 4: Stress Testing & Handover (Month 6)
- **Focus:** Scaling to 10x capacity and final regulatory sign-off.
- **Dependencies:** All features must be in "Review" or "Complete" status.
- **Key Target:** **Milestone 3 (Performance Benchmarks Met) - 2025-07-15**.

---

## 10. MEETING NOTES

*Note: All meetings are recorded as video calls. Per team culture, these are not rewatched; decisions are documented in Slack summaries.*

### Meeting 1: Kickoff & Stack Alignment
**Date:** 2024-11-02 | **Attendees:** Ravi, Bram, Quinn, Yael
- **Discussion:** Ravi highlighted the 6-month hard deadline. Bram expressed concern over the "mixed stack" (Django/Node/Java).
- **Decision:** The team agreed to use a Go-based Sidecar proxy to standardize communication. This avoids rewriting legacy code.
- **Action Item:** Bram to map all current API endpoints in the legacy systems.

### Meeting 2: Security Residency Review
**Date:** 2024-12-15 | **Attendees:** Ravi, Quinn, Yael
- **Discussion:** Quinn warned that simply using an EU region is not enough for GDPR; we need "at-rest" encryption keys managed within the EU.
- **Decision:** Move from standard AWS KMS to a dedicated CloudHSM instance located in Frankfurt.
- **Action Item:** Quinn to update the infrastructure-as-code (Terraform) files to include CloudHSM.

### Meeting 3: Performance Crisis Brainstorming
**Date:** 2025-02-10 | **Attendees:** Ravi, Bram, Quinn
- **Discussion:** Initial load tests show the system crashing at 3x capacity, far short of the 10x requirement. There is no budget for more servers.
- **Decision:** Ravi approved the engagement of an external consultant (Expert-ML-Consulting LLC) for a 2-week audit of the inference code to optimize C++ kernels.
- **Action Item:** Ravi to finalize the contract for the external consultant.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $520,000 | Salaries for 8 members across 2 time zones (6 months). |
| **Infrastructure** | $140,000 | AWS EU-Central-1 (EKS, RDS, S3, CloudHSM). |
| **External Tools** | $60,000 | LaunchDarkly (Enterprise), Datadog, Sentry, GitHub Enterprise. |
| **Consultancy** | $40,000 | Performance optimization expert and independent security auditor. |
| **Contingency** | $40,000 | Reserve for emergency scaling or legal adjustments. |

**Budget Note:** There is a known risk of a 30% cut in the next quarter. If this occurs, the "Contingency" and "Consultancy" budgets will be the first to be absorbed, and personnel may be shifted to a contractor-heavy model to reduce overhead.

---

## 12. APPENDICES

### Appendix A: Data Residency Compliance Matrix
To satisfy GDPR/CCPA, the following data mapping is enforced:
- **Patient PII:** Encrypted via AES-256; Keys stored in EU-Frankfurt HSM.
- **Model Weights:** Stored in S3 Bucket `drift-models-eu-central-1`.
- **Audit Logs:** Written to WORM storage in EU-Frankfurt.
- **Backup/DR:** Cross-region replication only within EU boundaries (e.g., Frankfurt to Ireland).

### Appendix B: Legacy Stack Interoperability Mapping
| Legacy Stack | Primary Role | Communication Protocol | Bridge Mechanism |
| :--- | :--- | :--- | :--- |
| Stack A (Django) | User Management | REST / JSON | Sidecar Proxy (Go) |
| Stack B (Node.js) | Real-time Notifications | WebSockets | Redis Pub/Sub |
| Stack C (Java) | ML Inference Engine | gRPC | Protobuf Definitions |

---
**End of Document**