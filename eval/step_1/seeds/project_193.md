# PROJECT SPECIFICATION DOCUMENT: PROJECT DRIFT
**Document Version:** 1.0.4  
**Last Updated:** 2023-10-24  
**Classification:** Confidential - Talus Innovations Internal  
**Project Code:** DRIFT-2026-ML  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Drift" is a mission-critical machine learning model deployment initiative undertaken by Talus Innovations. The primary objective is the total replacement of the "Legacy Core" (LC-15), a 15-year-old monolithic system that serves as the operational backbone for the company’s fintech services. The LC-15 system has become a liability due to its fragility, lack of scalability, and the unavailability of talent proficient in its proprietary scripting language.

Drift is not merely an upgrade but a wholesale migration to a modern Java/Spring Boot architecture, integrating a machine learning inference engine designed to automate risk assessment and transactional anomalies. Because the company depends entirely on this system for real-time processing, the deployment mandate is absolute: **zero downtime tolerance**. Any outage during the migration would result in immediate revenue loss and regulatory penalties.

### 1.2 Business Justification
The business justification for Drift is rooted in risk mitigation and operational efficiency. The current legacy system requires manual intervention for 22% of all transactions, leading to a bottleneck that prevents Talus Innovations from scaling its customer base. By deploying the Drift ML model, Talus aims to automate 85% of these manual reviews, reducing operational overhead by an estimated $2.1M annually.

Furthermore, the legacy system is no longer compliant with evolving HIPAA standards regarding data encryption and audit trails. Drift implements a "security-first" approach, ensuring that all Personally Identifiable Information (PII) and Protected Health Information (PHI) are encrypted at rest and in transit, thereby avoiding potential multi-million dollar non-compliance fines.

### 1.3 ROI Projection
The project operates on a shoestring budget of $150,000. Given the lean nature of the team (a solo developer under the guidance of the Tech Lead), the ROI is projected as follows:

*   **Year 1 (Implementation & Stability):** Initial investment of $150k. Projected cost savings from reduced manual review: $800k.
*   **Year 2 (Scaling):** Projected operational savings of $1.2M through the removal of legacy hardware maintenance contracts (currently costing $140k/year).
*   **Net Present Value (NPV):** Estimated at $1.85M over three years.
*   **Break-even Point:** Quarter 2 following the "First Paying Customer" milestone (approx. November 2026).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Drift follows a traditional three-tier architecture to ensure stability and ease of maintenance within the constraints of the Talus Innovations on-premise data center. Cloud services are strictly prohibited due to regulatory requirements and internal security policies.

**The Three Tiers:**
1.  **Presentation Layer:** A secure web interface and a versioned REST API providing the interface for internal operators and external B2B clients.
2.  **Business Logic Layer (The Core):** A Spring Boot application hosting the ML inference engine, the workflow automation logic, and the HIPAA-compliant encryption services.
3.  **Data Layer:** A high-availability Oracle DB cluster managing transactional data, model weights, and system configuration.

### 2.2 ASCII Architecture Diagram
```text
[ USER / CLIENT ] <--- HTTPS (TLS 1.3) ---> [ LOAD BALANCER (F5 BIG-IP) ]
                                                      |
                                                      v
                                       [ WEB/API SERVER (Spring Boot) ]
                                       |               |              |
                                       | (Logic)       | (Auth/Sec)    | (Inference)
                                       v               v              v
                            [ WORKFLOW ENGINE ] <--> [ ENCRYPTION ] <--> [ ML MODEL ]
                                       |               |              |
                                       +---------------+--------------+
                                                      |
                                                      v
                                       [ DATA ACCESS LAYER (Hibernate) ]
                                                      |
                                                      v
                                       [ ORACLE DB CLUSTER (On-Prem) ]
                                       | - Tablespaces (Encrypted)    |
                                       | - Audit Logs (Read-Only)      |
                                       | - Model Metadata             |
```

### 2.3 Technical Stack Specifications
*   **Language:** Java 17 (LTS)
*   **Framework:** Spring Boot 3.1.x
*   **Database:** Oracle Database 19c (Enterprise Edition)
*   **Deployment Target:** RHEL 8 (Red Hat Enterprise Linux) on-premise blades.
*   **Security:** AES-256 encryption for data at rest; TLS 1.3 for all transit.
*   **Integration:** RESTful APIs, Webhooks (JSON over HTTPS).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework (Priority: Critical - Launch Blocker)
**Status:** In Design | **Priority:** Critical

The Webhook Integration Framework is the most critical component of Drift, as it allows the ML model to push real-time alerts to third-party risk-management tools and internal monitoring dashboards. Without this, the system remains a "black box," requiring manual polling, which is unacceptable for a fintech environment.

**Functional Requirements:**
The framework must support the registration of "Listener" URLs where the Drift system will send POST requests upon specific trigger events (e.g., `MODEL_ALERT_HIGH_RISK`, `TRANSACTION_FLAGGED`). To ensure reliability, the framework must implement a **Retry Logic with Exponential Backoff**. If a third-party endpoint is down, Drift will retry the delivery at 1, 5, 15, and 60-minute intervals before marking the event as "Dead Letter."

**Security Considerations:**
Since webhooks send sensitive data to external endpoints, every payload must be signed with an HMAC (Hash-based Message Authentication Code) using a secret shared between Talus and the client. This ensures the receiver can verify the payload originated from Drift and was not tampered with during transit.

**Technical Implementation:**
The system will utilize a `WebhookOutboundQueue` table in Oracle DB to track pending notifications. A scheduled Spring Boot task will poll this queue, attempt delivery via `RestTemplate`, and update the status to `DELIVERED` or `FAILED`.

---

### 3.2 Workflow Automation Engine with Visual Rule Builder (Priority: High)
**Status:** In Progress | **Priority:** High

The Workflow Automation Engine is designed to replace the manual decision-making process of the legacy system. It allows non-technical operators to define "If-Then-Else" logic based on the output of the ML model.

**Functional Requirements:**
The "Visual Rule Builder" is a frontend interface where users can drag and drop logic blocks. For example: *“IF ML_Risk_Score > 0.8 AND Transaction_Amount > $5,000 THEN Route to Senior Auditor.”* These visual rules are translated into a JSON-based Domain Specific Language (DSL) stored in the database.

The engine must support **Conditional Branching** and **Parallel Execution**. A single trigger can kick off multiple workflows (e.g., notifying a customer via email while simultaneously flagging the transaction for internal review).

**Technical Implementation:**
The backend implements a `WorkflowExecutor` service that parses the JSON DSL. It uses the Strategy Pattern to execute different "Action" classes (e.g., `EmailAction`, `FlagTransactionAction`, `ApiCallAction`). To prevent infinite loops in user-defined rules, the engine imposes a maximum recursion depth of 10.

---

### 3.3 Localization and Internationalization (L10n/I18n) (Priority: High)
**Status:** Not Started | **Priority:** High

As Talus Innovations expands into global markets, the Drift system must support 12 different languages (English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, Dutch, and Russian).

**Functional Requirements:**
The system must support dynamic language switching based on the user's profile settings or the `Accept-Language` HTTP header. This includes not only the UI labels but also the generated reports and error messages.

**Technical Implementation:**
The project will utilize Spring’s `MessageSource` and `ResourceBundle` mechanisms. Translation strings will be stored in `.properties` files (e.g., `messages_en.properties`, `messages_fr.properties`). To facilitate updates without redeploying the entire application, the project will implement a `DatabaseMessageSource` that allows the QA lead (Anouk Gupta) to update translations directly in a specialized Oracle table, which is then cached in memory.

**Currency and Date Formatting:**
The system must automatically adjust date formats (e.g., MM/DD/YYYY vs DD/MM/YYYY) and currency symbols based on the locale, ensuring that financial reports are compliant with local regional standards.

---

### 3.4 Customer-Facing API with Versioning and Sandbox (Priority: Medium)
**Status:** Blocked (Waiting on Legal) | **Priority:** Medium

The API is the primary gateway for B2B partners to interact with the Drift ML model. It is currently blocked pending the legal review of the Data Processing Agreement (DPA), as the API exposes PII to external entities.

**Functional Requirements:**
The API must be versioned using URI versioning (e.g., `/api/v1/predict` and `/api/v2/predict`). This allows Talus to update the ML model logic without breaking existing client integrations. 

A **Sandbox Environment** is required. This is a mirrored instance of the production environment but populated with "synthetic" (anonymized) data. Clients can test their integrations in the sandbox without risking actual financial transactions.

**Technical Implementation:**
The API will be secured using OAuth2 with JWT (JSON Web Tokens). Rate limiting will be enforced via a `Bucket4j` implementation to prevent API abuse, limiting clients to 1,000 requests per minute. The sandbox will be isolated on a separate subnet within the data center to ensure no cross-contamination between test and production data.

---

### 3.5 PDF/CSV Report Generation (Priority: Low)
**Status:** Complete | **Priority:** Low

The reporting module provides scheduled summaries of ML model performance and transactional flags for executive review.

**Functional Requirements:**
Users can schedule reports (Daily, Weekly, Monthly) to be delivered via internal email or uploaded to a secure SFTP folder. The reports must be available in both PDF (for presentation) and CSV (for data analysis in Excel).

**Technical Implementation:**
The PDF generation is handled by the `JasperReports` library, which allows for highly formatted templates. CSVs are generated using `OpenCSV`. The scheduling is managed by a Spring `@Scheduled` task that queries the Oracle DB for all active report subscriptions and triggers the generation process during low-traffic windows (02:00 AM EST).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a valid JWT in the `Authorization: Bearer <token>` header.

### 4.1 ML Prediction Endpoint
**Path:** `POST /api/v1/predict`  
**Description:** Submits transaction data for ML risk scoring.  
**Request:**
```json
{
  "transaction_id": "TXN-992834",
  "amount": 1250.00,
  "currency": "USD",
  "merchant_id": "M-5542",
  "timestamp": "2023-10-24T14:20:00Z"
}
```
**Response (200 OK):**
```json
{
  "prediction_id": "PRED-112",
  "risk_score": 0.82,
  "recommendation": "FLAG_FOR_REVIEW",
  "model_version": "drift-v2.1.0"
}
```

### 4.2 Webhook Registration
**Path:** `POST /api/v1/webhooks/register`  
**Description:** Registers a new external URL for event notifications.  
**Request:**
```json
{
  "callback_url": "https://partner-site.com/webhooks/talus",
  "events": ["MODEL_ALERT_HIGH_RISK", "SYSTEM_ERROR"],
  "secret_key": "shared-secret-12345"
}
```
**Response (201 Created):**
```json
{
  "webhook_id": "WH-883",
  "status": "PENDING_VERIFICATION"
}
```

### 4.3 Workflow Rule Update
**Path:** `PUT /api/v1/workflow/rules/{ruleId}`  
**Description:** Updates a specific automation rule.  
**Request:**
```json
{
  "rule_name": "High Value Flag",
  "condition": "risk_score > 0.9 && amount > 10000",
  "action": "ROUTE_TO_SENIOR_AUDITOR"
}
```
**Response (200 OK):**
```json
{
  "status": "UPDATED",
  "effective_date": "2023-10-24T15:00:00Z"
}
```

### 4.4 Sandbox Data Request
**Path:** `GET /api/v1/sandbox/data`  
**Description:** Retrieves a set of synthetic test cases for integration testing.  
**Response (200 OK):**
```json
[
  {"test_case": "Edge Case 1", "expected_score": 0.1},
  {"test_case": "Fraud Case A", "expected_score": 0.95}
]
```

### 4.5 Report Schedule Setup
**Path:** `POST /api/v1/reports/schedule`  
**Description:** Configures a recurring PDF/CSV report.  
**Request:**
```json
{
  "report_type": "WEEKLY_SUMMARY",
  "format": "PDF",
  "delivery_method": "EMAIL",
  "recipient": "exec-team@talus.com"
}
```
**Response (201 Created):**
```json
{
  "schedule_id": "SCH-441",
  "next_run": "2023-10-31T02:00:00Z"
}
```

### 4.6 Model Version Inquiry
**Path:** `GET /api/v1/model/version`  
**Description:** Returns current production model metadata.  
**Response (200 OK):**
```json
{
  "version": "2.1.0",
  "deployed_at": "2023-09-12",
  "accuracy_metric": 0.942,
  "last_retrained": "2023-08-01"
}
```

### 4.7 System Health Check
**Path:** `GET /api/v1/health`  
**Description:** Heartbeat endpoint for monitoring tools.  
**Response (200 OK):**
```json
{
  "status": "UP",
  "db_connection": "CONNECTED",
  "ml_engine": "ACTIVE",
  "uptime": "14d 02h 11m"
}
```

### 4.8 Audit Log Retrieval
**Path:** `GET /api/v1/audit/logs?userId=123`  
**Description:** Retrieves HIPAA-compliant access logs for a specific user.  
**Response (200 OK):**
```json
[
  {"timestamp": "2023-10-24T10:00:01Z", "action": "VIEW_PII", "result": "SUCCESS"},
  {"timestamp": "2023-10-24T10:05:22Z", "action": "UPDATE_RULE", "result": "SUCCESS"}
]
```

---

## 5. DATABASE SCHEMA

The database resides on a clustered Oracle 19c instance. All tables containing PII are encrypted using Transparent Data Encryption (TDE).

### 5.1 Tables and Relationships

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `USERS` | `user_id` | `username`, `password_hash`, `role_id`, `locale_id` | `roles.role_id`, `locales.locale_id` | System users and auth. |
| `ROLES` | `role_id` | `role_name`, `permissions_bitmask` | `users.role_id` | Role-based access control. |
| `LOCALES` | `locale_id` | `language_code`, `country_code`, `currency_symbol` | `users.locale_id` | I18n configuration. |
| `TRANSACTIONS` | `txn_id` | `amount`, `currency`, `timestamp`, `user_id` | `users.user_id` | Core transaction data. |
| `ML_PREDICTIONS` | `pred_id` | `txn_id`, `risk_score`, `model_version`, `created_at` | `transactions.txn_id` | Results of ML inference. |
| `WORKFLOW_RULES` | `rule_id` | `rule_name`, `dsl_logic`, `is_active`, `created_by` | `users.user_id` | Visual rule builder output. |
| `WEBHOOK_CONFIG` | `webhook_id` | `callback_url`, `secret_key`, `status`, `created_at` | N/A | Third-party integration settings. |
| `WEBHOOK_LOGS` | `log_id` | `webhook_id`, `payload`, `http_status`, `retry_count` | `webhook_config.webhook_id` | Delivery history. |
| `REPORT_SCHEDULES` | `sched_id` | `report_type`, `format`, `cron_expression`, `recipient` | N/A | Scheduled reporting metadata. |
| `AUDIT_TRAILS` | `audit_id` | `user_id`, `action`, `timestamp`, `ip_address`, `resource_id` | `users.user_id` | HIPAA compliance logging. |

### 5.2 Relationship Map
*   **Users $\to$ Transactions:** One-to-Many.
*   **Transactions $\to$ ML Predictions:** One-to-One.
*   **Users $\to$ Workflow Rules:** One-to-Many (Creator).
*   **Webhook Config $\to$ Webhook Logs:** One-to-Many.
*   **Users $\to$ Audit Trails:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Because this is an on-premise deployment with zero downtime tolerance, the project utilizes a strict three-environment promotion path.

#### 6.1.1 Development (DEV)
*   **Purpose:** Initial coding and unit testing.
*   **Hardware:** Single virtual machine (VM) with a lightweight Oracle XE instance.
*   **Deployment:** Continuous integration (CI) via Jenkins. Every commit triggers a build.

#### 6.1.2 Staging (STG)
*   **Purpose:** QA and User Acceptance Testing (UAT). This environment is a hardware mirror of Production.
*   **Hardware:** Dual-node cluster with a full Oracle 19c instance.
*   **Deployment:** Weekly release train. Only artifacts that have passed Anouk Gupta’s QA sign-off are promoted to Staging.

#### 6.1.3 Production (PROD)
*   **Purpose:** Live financial processing.
*   **Hardware:** High-availability cluster across two physical data center racks to prevent single-point-of-failure.
*   **Deployment:** **Weekly Release Train (Wednesdays at 03:00 AM EST).** 
*   **Zero Downtime Strategy:** Using a Blue-Green deployment strategy. The "Green" environment is updated; traffic is shifted via the F5 Load Balancer only after a successful smoke test. If any critical error is detected, traffic is instantly routed back to the "Blue" (previous) environment.

### 6.2 Infrastructure Constraints
*   **No Cloud:** All data must reside within the Talus Innovations firewall.
*   **Network:** Strict VLAN isolation. The Database tier cannot be accessed directly from the Presentation tier; all requests must pass through the Business Logic tier.
*   **Backups:** Nightly incremental backups of the Oracle DB, stored on an immutable WORM (Write Once Read Many) drive for compliance.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Approach:** JUnit 5 and Mockito.
*   **Coverage Goal:** 80% for new modules.
*   **Focus:** Business logic in the `Service` layer and ML utility functions. Since the core billing module currently has **zero test coverage** (Technical Debt), all new changes to billing must be accompanied by regression tests.

### 7.2 Integration Testing
*   **Approach:** Spring Boot Test with Testcontainers (running Oracle DB in a container).
*   **Focus:** Ensuring the `WorkflowExecutor` correctly interacts with the `ML_PREDICTIONS` table and that the `WebhookFramework` handles network timeouts gracefully.

### 7.3 End-to-End (E2E) Testing
*   **Approach:** Automated Selenium scripts for the UI and Postman collections for the API.
*   **Focus:** The "Happy Path" from transaction ingestion $\to$ ML scoring $\to$ Workflow triggering $\to$ Webhook notification.
*   **QA Lead:** Anouk Gupta is the final authority for E2E sign-off. No release enters the "Train" without a signed-off UAT report.

### 7.4 Performance and Stress Testing
*   **Tool:** Apache JMeter.
*   **Target:** The system must handle 500 transactions per second (TPS) with a 95th percentile latency of $< 200\text{ms}$ for the `/predict` endpoint.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Project sponsor rotating out of role | High | High | **Parallel-pathing:** Prototype alternative architectural approaches simultaneously so the project can pivot quickly to a new sponsor's preference. |
| **R2** | Scope creep from stakeholders | High | Medium | **De-scoping:** Any "small" feature request added after the freeze date will be moved to "Phase 2" or result in the de-scoping of a lower-priority feature. |
| **R3** | Technical debt in billing module | Medium | Critical | **Regression focused:** Mandatory test coverage for any modified line of code in the billing module. |
| **R4** | Legal delay in DPA review | Medium | Medium | **Blocked status:** API development is paused, but internal logic is developed using "mock" external interfaces to avoid wasting developer time. |

**Probability/Impact Matrix:**
*   *High/High $\to$ Immediate Attention (R1)*
*   *High/Medium $\to$ Active Monitoring (R2)*
*   *Medium/Critical $\to$ Risk Mitigation Plan (R3)*

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown
The project is divided into four distinct phases. Due to the "Weekly Release Train" constraint, all deliverables must be aligned with Wednesday deployment windows.

**Phase 1: Core Engine & Infrastructure (2023-11 to 2024-06)**
*   Setup on-premise environment.
*   ML model integration.
*   Development of the core billing logic (with new tests).

**Phase 2: Automation & Integration (2024-07 to 2025-03)**
*   Visual Rule Builder development.
*   Webhook Framework implementation (Critical Path).
*   Initial I18n framework.

**Phase 3: API & Compliance (2025-04 to 2026-01)**
*   API versioning implementation.
*   Sandbox environment setup.
*   Legal DPA sign-off and HIPAA audit.

**Phase 4: Stability & Onboarding (2026-02 to 2026-10)**
*   Pilot user testing.
*   Fine-tuning ML hyperparameters.
*   Client onboarding.

### 9.2 Key Milestones
| Milestone | Description | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| **M1** | **Production Launch** | 2026-06-15 | Webhook Framework completion |
| **M2** | **Post-launch Stability Confirmed** | 2026-08-15 | Zero critical bugs for 30 days |
| **M3** | **First Paying Customer Onboarded** | 2026-10-15 | API Sandbox verification |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Zev Park, Esme Fischer, Anouk Gupta, Bram Fischer  
**Discussion:**
*   Zev emphasized that the $150k budget is absolute. No additional licensing for cloud services will be approved.
*   Esme raised concerns about the Oracle DB version. It was decided to stick with 19c to maintain compatibility with the legacy data migration scripts.
*   Anouk pointed out that the "Zero Downtime" requirement makes the weekly release train dangerous if the rollback plan isn't robust.
*   **Decision:** Use Blue-Green deployment on the F5 Load Balancer for all PROD releases.

**Action Items:**
*   Zev: Finalize the VM allocation with the Data Center team. (Owner: Zev)
*   Esme: Create the initial ER diagram for the Oracle schema. (Owner: Esme)

---

### Meeting 2: The "Billing Debt" Crisis
**Date:** 2024-02-15  
**Attendees:** Zev Park, Esme Fischer, Anouk Gupta  
**Discussion:**
*   During the development of the Workflow Engine, it was discovered that the core billing module has zero unit test coverage.
*   Esme noted that the original legacy code was deployed under extreme deadline pressure 10 years ago.
*   Anouk refused to sign off on the next release train until a basic regression suite is built for the billing calculations.
*   **Decision:** The developer will spend the next two sprints exclusively on "Catch-up Testing" for the billing module before proceeding with the Visual Rule Builder.

**Action Items:**
*   Developer: Implement JUnit tests for `BillingCalculator.java`. (Owner: Solo Dev)
*   Anouk: Define a "Minimum Viable Test Suite" for the billing module. (Owner: Anouk)

---

### Meeting 3: Webhook Design Review
**Date:** 2024-05-10  
**Attendees:** Zev Park, Esme Fischer, Bram Fischer  
**Discussion:**
*   The team discussed the "Launch Blocker" status of the Webhook Framework.
*   Bram expressed concern that if a partner's endpoint is slow, it might hang the Spring Boot worker threads, causing a system-wide slowdown.
*   Esme proposed using an asynchronous queue (Oracle table as a queue) to decouple the event trigger from the actual HTTP delivery.
*   **Decision:** Implement a `WebhookOutboundQueue` with a separate background worker to ensure the main transaction flow is never blocked by external API latency.

**Action Items:**
*   Esme: Design the `WEBHOOK_LOGS` table schema. (Owner: Esme)
*   Zev: Verify if the F5 Load Balancer can handle the outbound traffic volume. (Owner: Zev)

---

## 11. BUDGET BREAKDOWN

The total budget of **$150,000** is strictly allocated. Because Talus Innovations uses internal personnel, the "Personnel" cost represents the internal cost-center allocation for the solo developer's time and a portion of the lead's oversight.

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $90,000 | Allocation for solo developer (18 months) and Zev Park's oversight. |
| **Infrastructure** | $30,000 | On-premise hardware upgrades, Oracle license maintenance, and F5 config. |
| **Tools & Software** | $15,000 | IDE licenses (IntelliJ), JasperReports commercial license, and Jenkins plugins. |
| **Contingency** | $15,000 | Reserved for emergency hardware replacement or external legal consultant fees. |
| **Total** | **$150,000** | |

**Financial Oversight:**
Every expenditure over $500 must be approved by Zev Park and logged in JIRA under the `BUDGET-TRACK` ticket. Any deviation from this budget will require a formal request to the project sponsor.

---

## 12. APPENDICES

### Appendix A: HIPAA Encryption Standard
To maintain HIPAA compliance, the following encryption standards are mandated for Project Drift:
1.  **Data at Rest:** All tables containing PHI/PII must use Oracle Transparent Data Encryption (TDE). Keys are stored in a physical Hardware Security Module (HSM) located in the data center.
2.  **Data in Transit:** All internal communication between the Presentation and Business layers must use TLS 1.3.
3.  **Password Storage:** Passwords must be hashed using BCrypt with a minimum cost factor of 12. No plaintext passwords shall exist in the database or logs.

### Appendix B: Legacy Migration Mapping
The migration from the LC-15 system to Drift requires a mapping of legacy data types to modern Java/Oracle types.

| Legacy Field | Drift Field | Logic Change |
| :--- | :--- | :--- |
| `CUST_ID_OLD` | `user_id` | UUID conversion (string to numeric) |
| `AMT_VAL` | `amount` | Conversion from fixed-point to `BigDecimal` |
| `SQR_CODE` | `risk_score` | ML model replaces the legacy square-root calculation |
| `TS_UTC` | `timestamp` | Standardized to ISO 8601 format |