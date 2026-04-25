# PROJECT SPECIFICATION: PROJECT UMBRA
**Version:** 1.0.4  
**Status:** Draft/Active  
**Classification:** CONFIDENTIAL – STRATOS SYSTEMS  
**Date:** October 26, 2023  
**Owner:** Bodhi Moreau (CTO)

---

## 1. EXECUTIVE SUMMARY

**Project Umbra** is a strategic technical consolidation initiative undertaken by Stratos Systems. The primary business objective is to migrate four redundant internal healthcare management tools—currently operating as monolithic silos with overlapping functionality—into a single, unified API Gateway and Microservices architecture. These legacy systems currently incur significant operational overhead, including quadruple licensing costs for third-party integrations and fragmented data silos that hinder patient care coordination and billing accuracy.

**Business Justification**  
The current fragmented state of Stratos Systems' internal tooling has led to a "data drift" phenomenon where patient records across the four tools are often contradictory. This not only poses a regulatory risk under HIPAA and PCI DSS standards but also creates an operational bottleneck. By consolidating these tools into Project Umbra, Stratos Systems will eliminate redundant server costs, reduce the surface area for security vulnerabilities, and streamline the developer experience by providing a single source of truth for internal API consumption.

**ROI Projection**  
As Project Umbra is currently unfunded and bootstrapping with existing team capacity, the ROI is calculated primarily through "cost avoidance" and "operational efficiency." 
- **Direct Cost Reduction:** Estimated saving of $142,000/year in decommissioned legacy server hosting and redundant SaaS licenses.
- **Developer Velocity:** Reduction in onboarding time for new engineers from 4 weeks to 1 week due to a unified codebase and documentation.
- **Risk Mitigation:** Elimination of potential PCI non-compliance fines which can reach $100,000 per month for systemic failures.
- **Scale Projection:** The system is designed to support 10,000 Monthly Active Users (MAU) within six months of launch, allowing the company to pivot from internal tooling to a potential B2B SaaS offering in the healthcare sector.

The migration focuses on a high-performance stack (Elixir/Phoenix) to handle the concurrency requirements of real-time healthcare data streaming via LiveView. Despite the dysfunctional team dynamics and the lack of prior experience with the stack, the strategic move to a micro-frontend architecture ensures that independent teams can eventually own specific domains, preventing the new system from becoming the same monolith it is replacing.

---

## 2. TECHNICAL ARCHITECTURE

Project Umbra utilizes a **Micro-Frontend (MFE) Architecture** backed by an **Elixir/Phoenix** ecosystem. The core of the system is a centralized API Gateway that handles request routing, authentication, and rate limiting before forwarding requests to specialized microservices.

### 2.1 Technology Stack
- **Language/Framework:** Elixir 1.15+, Phoenix 1.7 (utilizing LiveView for real-time dashboard updates).
- **Database:** PostgreSQL 15.4 (with PostGIS for healthcare facility location tracking).
- **Infrastructure:** Fly.io (Global distribution with Anycast IP).
- **Deployment:** GitHub Actions for CI/CD, utilizing Blue-Green deployment strategies to ensure zero downtime during healthcare critical hours.
- **Security:** PCI DSS Level 1 Compliance. All credit card data is encrypted at the application level using AES-256 before hitting the database.

### 2.2 Architectural Diagram Description (ASCII)
The following diagram illustrates the request flow from the client to the data layer:

```text
[ Client Browser / MFE ] 
          |
          v
[ Fly.io Global Edge ]  <-- DNS / SSL Termination
          |
          v
[ API Gateway (Phoenix) ] <-- Auth, Rate Limiting, Routing
          |
    ______|_____________________________________________
   |              |                 |                   |
   v              v                 v                   v
[Import Svc]  [Workflow Svc]   [Billing Svc]      [Audit Svc]
   |              |                 |                   |
   +--------------+-----------------+-------------------+
                                  |
                                  v
                      [ PostgreSQL Cluster ]
                      (Read Replicas / Master)
```

### 2.3 Micro-Frontend Strategy
The UI is split into independent modules. Each module (e.g., Billing Dashboard, Workflow Builder) is developed, tested, and deployed independently. This prevents the "dysfunctional" team dynamics from stalling the project; if the Lead Engineer and PM are not communicating, the independent ownership of MFEs allows the Junior Developer and DevOps Engineer to continue pushing features in their respective domains without blocking the rest of the pipeline.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**  
The system must allow healthcare providers to upload patient data, billing records, and insurance claims in various formats (CSV, XML, JSON, HL7). The system must automatically detect the file format and map the data to the internal PostgreSQL schema without manual user intervention.

**Technical Requirements:**  
- **Auto-Detection Engine:** A MIME-type check followed by a "magic byte" analysis. If the file is CSV, the system will perform a "header-scan" to match columns against known healthcare templates.
- **Processing Pipeline:** Large files must be processed asynchronously using `Oban` (Elixir background jobs) to avoid blocking the API Gateway.
- **Validation:** Data must be validated against the healthcare domain schema (e.g., ensuring date formats are ISO-8601).

**User Workflow:**  
1. User uploads a file via the `POST /api/v1/import` endpoint.
2. The system returns a `202 Accepted` with a `job_id`.
3. The background worker detects the format (e.g., "HL7 v2.x").
4. The worker transforms the data into the internal format and updates the `import_logs` table.
5. User receives a LiveView notification upon completion.

### 3.2 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** In Design

**Description:**  
A low-code environment where administrators can define "If-This-Then-That" (IFTTT) logic for patient management. For example: *"If a patient's blood pressure is > 140/90 AND age > 65, then flag for urgent review and notify the primary physician."*

**Technical Requirements:**  
- **Visual Builder:** A Phoenix LiveView-based drag-and-drop interface allowing the creation of logic nodes.
- **Rule Engine:** A Domain Specific Language (DSL) written in Elixir that compiles the visual nodes into executable functions.
- **Trigger System:** Hooks into the API Gateway's event stream. Every state change in the database triggers a check against the active rules.

**Complexity Note:**  
Since the team is unfamiliar with Elixir, the rule builder will initially use a simplified JSON-logic representation before moving to a full DSL.

### 3.3 A/B Testing Framework (Integrated into Feature Flags)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**  
To ensure the migration doesn't disrupt patient care, new features must be rolled out to a subset of users. This framework is not a separate tool but is "baked into" the existing feature flag system.

**Technical Requirements:**  
- **Assignment Logic:** Users are hashed by their `user_id` to ensure a consistent experience (sticky sessions).
- **Telemetry:** Every action performed under a specific flag version must be tagged in the audit log to measure conversion or error rates.
- **Control Group:** Ability to define a 5% control group that never sees new features, providing a baseline for stability.

**Evaluation Metrics:**  
The framework must track "Time to Task Completion." If a new UI variant increases the time it takes to enter a patient record by >10%, the flag should be automatically toggled off.

### 3.4 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low (Nice to Have) | **Status:** In Review

**Description:**  
For PCI DSS Level 1 compliance and healthcare regulations, every change to a record must be logged. These logs must be "tamper-evident," meaning any attempt to alter the audit log after the fact is detectable.

**Technical Requirements:**  
- **Hashing:** Each log entry contains a SHA-256 hash of the previous entry (creating a linear hash chain).
- **Storage:** Logs are written to a write-once-read-many (WORM) storage volume on Fly.io.
- **Verification:** A daily cron job re-calculates the hash chain to ensure no records were deleted or modified.

### 3.5 Automated Billing and Subscription Management
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:**  
Transitioning the internal tool into a potentially monetizable product requires a robust billing layer. This involves subscription tiers (Basic, Professional, Enterprise) and automated invoicing.

**Technical Requirements:**  
- **PCI Compliance:** Credit card data must never be stored in plain text. Integration with a PCI-compliant vault.
- **Billing Cycles:** Support for monthly and annual billing, with automated "dunning" (retry) logic for failed payments.
- **Usage Tracking:** A metering service that tracks API calls per account to apply overage charges.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication is handled via JWT in the `Authorization: Bearer <token>` header.

### 4.1 Import Data
`POST /import`
- **Description:** Uploads a data file for processing.
- **Request Body:** `multipart/form-data` (file: `binary`)
- **Success Response:** `202 Accepted`
  ```json
  { "job_id": "job_88234", "status": "processing", "estimated_completion": "2023-10-27T10:00:00Z" }
  ```
- **Error Response:** `413 Payload Too Large`

### 4.2 Get Import Status
`GET /import/:job_id`
- **Description:** Checks the progress of a specific import job.
- **Response:** `200 OK`
  ```json
  { "job_id": "job_88234", "progress": "65%", "errors": ["Row 45: Invalid Date"] }
  ```

### 4.3 Create Workflow Rule
`POST /workflows`
- **Description:** Saves a new automation rule from the visual builder.
- **Request Body:** 
  ```json
  { "name": "High BP Alert", "trigger": "patient_update", "condition": "bp > 140", "action": "notify_doctor" }
  ```
- **Response:** `201 Created`

### 4.4 Get Feature Flags
`GET /config/flags`
- **Description:** Returns a list of active feature flags for the requesting user.
- **Response:** `200 OK`
  ```json
  { "flags": { "new_billing_ui": true, "beta_export": false } }
  ```

### 4.5 Create Billing Profile
`POST /billing/profile`
- **Description:** Sets up a new payment profile.
- **Request Body:**
  ```json
  { "customer_name": "Clinic A", "card_token": "tok_visa_123", "plan_id": "plan_pro" }
  ```
- **Response:** `201 Created`

### 4.6 Get Audit Log
`GET /audit/logs?start_date=2023-01-01&end_date=2023-01-31`
- **Description:** Retrieves a filtered list of system changes.
- **Response:** `200 OK`
  ```json
  [ { "timestamp": "...", "user": "jsmith", "action": "update_patient", "hash": "a1b2c3..." } ]
  ```

### 4.7 List Patients
`GET /patients`
- **Description:** Returns a paginated list of patients.
- **Response:** `200 OK`
  ```json
  { "data": [...], "meta": { "page": 1, "total": 500 } }
  ```

### 4.8 Update Patient Record
`PATCH /patients/:id`
- **Description:** Updates specific fields of a patient record.
- **Request Body:** `{ "last_name": "Smith-Jones" }`
- **Response:** `200 OK`

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15.4 cluster. All tables use UUIDs as primary keys for security and distributed scalability.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role` | User accounts and authentication. |
| `patients` | `patient_id` | `user_id` | `first_name`, `last_name`, `dob` | Core patient healthcare records. |
| `medical_records` | `record_id` | `patient_id` | `diagnosis`, `treatment`, `timestamp` | Historical medical data. |
| `import_jobs` | `job_id` | `user_id` | `file_name`, `status`, `detected_format` | Tracking for data imports. |
| `workflow_rules` | `rule_id` | `user_id` | `trigger_event`, `logic_json`, `is_active` | Automation engine definitions. |
| `feature_flags` | `flag_id` | None | `flag_name`, `is_enabled`, `rollout_pct` | A/B testing and feature toggles. |
| `user_flag_map` | `map_id` | `user_id`, `flag_id` | `assigned_variant` | Specific flag assignment per user. |
| `audit_logs` | `log_id` | `user_id` | `action`, `payload_diff`, `prev_hash` | Tamper-evident system logs. |
| `billing_accounts`| `acc_id` | `user_id` | `stripe_customer_id`, `plan_type` | Subscription and account status. |
| `transactions` | `tx_id` | `acc_id` | `amount`, `currency`, `status` | Payment history. |

### 5.2 Relationships
- `users` $\rightarrow$ `patients` (1:N)
- `patients` $\rightarrow$ `medical_records` (1:N)
- `users` $\rightarrow$ `import_jobs` (1:N)
- `users` $\rightarrow$ `workflow_rules` (1:N)
- `feature_flags` $\rightarrow$ `user_flag_map` (1:N)
- `users` $\rightarrow$ `billing_accounts` (1:1)
- `billing_accounts` $\rightarrow$ `transactions` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra utilizes three distinct environments to ensure stability and security.

1. **Development (Dev):**
   - **Host:** Local Docker containers + Fly.io `dev` app.
   - **Database:** Shared PostgreSQL instance with anonymized data.
   - **CI/CD:** Every push to a feature branch triggers a build and test suite.

2. **Staging (Staging):**
   - **Host:** Fly.io `staging` app.
   - **Database:** Mirror of production schema (empty data).
   - **Purpose:** Final QA and UAT (User Acceptance Testing). This environment is used to verify PCI compliance before the production push.

3. **Production (Prod):**
   - **Host:** Fly.io Multi-region cluster.
   - **Database:** High-Availability (HA) PostgreSQL cluster with automatic failover.
   - **Strategy:** **Blue-Green Deployment**. The "Green" environment is updated and health-checked. Once verified, the API Gateway shifts traffic from "Blue" to "Green" instantly.

### 6.2 CI/CD Pipeline (GitHub Actions)
The pipeline follows a strict sequence:
`Lint` $\rightarrow$ `Unit Tests` $\rightarrow$ `Integration Tests` $\rightarrow$ `Build Image` $\rightarrow$ `Deploy to Staging` $\rightarrow$ `Manual Approval` $\rightarrow$ `Deploy to Production`.

---

## 7. TESTING STRATEGY

Due to the critical nature of healthcare data and the team's lack of experience with Elixir, a rigorous testing pyramid is implemented.

### 7.1 Unit Testing
- **Tool:** `ExUnit`.
- **Focus:** Pure functions, data transformation logic (especially for the Import engine), and validation rules.
- **Requirement:** 80% code coverage on all new business logic.

### 7.2 Integration Testing
- **Tool:** `Wallaby` (for Phoenix LiveView).
- **Focus:** Ensuring the API Gateway correctly routes requests to microservices and that database transactions are atomic.
- **Scenario:** Testing a full "Import $\rightarrow$ Process $\rightarrow$ Audit Log" flow.

### 7.3 End-to-End (E2E) Testing
- **Tool:** `Playwright`.
- **Focus:** Critical user journeys.
- **Key Paths:** 
  1. User logs in $\rightarrow$ uploads CSV $\rightarrow$ confirms data import.
  2. Admin creates a workflow rule $\rightarrow$ triggers a patient update $\rightarrow$ verifies notification.
  3. User updates credit card $\rightarrow$ verifies billing status change.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Team lack of experience with Elixir/Phoenix | High | High | Negotiate timeline extension; provide 2 weeks of dedicated training. |
| R2 | Regulatory (HIPAA/PCI) changes mid-project | Medium | High | Raise as a blocker in the next board meeting; involve legal early. |
| R3 | Team dysfunction (CTO/PM conflict) | High | Medium | Implement strict ticket-based communication to avoid verbal friction. |
| R4 | Performance degradation under 10k MAU | Low | High | Implement Fly.io auto-scaling and PostgreSQL read replicas. |
| R5 | Data loss during migration from legacy tools | Medium | High | Implement dual-write period where data is written to both old and new systems. |

**Probability/Impact Matrix:**
- **High/High:** R1, R2 (Critical focus)
- **High/Medium:** R3 (Manageable through process)
- **Low/High:** R4 (Technical solution available)

---

## 9. TIMELINE AND PHASES

Project Umbra is structured into four phases. Note that the current "Blocker" (Team member on medical leave) has shifted the start of Phase 2.

### Phase 1: Foundation (Oct 2023 - Feb 2024)
- **Focus:** API Gateway setup, Database Schema implementation, PCI Vault integration.
- **Dependency:** Infrastructure setup on Fly.io.

### Phase 2: Core Features (Mar 2024 - Dec 2024)
- **Focus:** Data Import engine (Critical), Workflow Builder (High), A/B Testing Framework (Critical).
- **Dependency:** Successful completion of the Import engine before Workflow Builder can be tested with real data.

### Phase 3: Polish and Compliance (Jan 2025 - June 2025)
- **Focus:** Audit logs, Billing system, external PCI DSS Level 1 audit.
- **Dependency:** Finalized regulatory requirements.

### Phase 4: Launch and Stability (July 2025 - Nov 2025)
- **Milestone 1:** Post-launch stability confirmed (Target: 2025-07-15)
- **Milestone 2:** First paying customer onboarded (Target: 2025-09-15)
- **Milestone 3:** Architecture review complete (Target: 2025-11-15)

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff
**Date:** October 26, 2023  
**Attendees:** Bodhi (CTO), Renzo (DevOps), Jasper (Security), Dante (Junior Dev)  
**Discussion:**
- Bodhi introduced the Elixir/Phoenix stack. Dante expressed concern regarding the learning curve.
- Jasper emphasized that since the system processes credit card data directly, PCI DSS Level 1 is non-negotiable.
- Renzo questioned the choice of Fly.io over AWS. Bodhi insisted on Fly.io for the edge computing capabilities.
- **Conflict Note:** A brief argument occurred between the PM (not present, but mentioned via email) and Bodhi regarding the "unfunded" nature of the project.

**Action Items:**
- **Renzo:** Set up the Fly.io organization and basic VPC. (Due: Nov 1)
- **Jasper:** Draft the PCI compliance checklist. (Due: Nov 5)
- **Bodhi:** Provide learning resources for Elixir to the team. (Due: Oct 30)

### Meeting 2: Technical Deep Dive - Import Engine
**Date:** November 15, 2023  
**Attendees:** Bodhi, Renzo, Dante  
**Discussion:**
- Dante presented a prototype for the auto-detection logic. He suggested using a "heuristic-based" approach for CSVs.
- Renzo noted that large imports might crash the API Gateway. The team decided to move all processing to `Oban` background workers.
- Bodhi requested that the import engine be treated as the "top launch blocker."

**Action Items:**
- **Dante:** Implement the `magic-byte` detection for HL7 files. (Due: Nov 20)
- **Renzo:** Configure the PostgreSQL read-replica for the import worker to avoid locking the master DB. (Due: Nov 22)

### Meeting 3: Risk Assessment & Blocker Review
**Date:** December 10, 2023  
**Attendees:** Bodhi, Jasper, Renzo  
**Discussion:**
- **Current Blocker:** The team discussed the impact of the key developer being on medical leave for 6 weeks.
- Bodhi admitted that the project is behind schedule due to the learning curve.
- Jasper warned that regulatory requirements for the audit trail are still being finalized by the board.
- **Team Tension:** It was noted that the PM has not responded to the last three architecture requests from the lead engineer.

**Action Items:**
- **Bodhi:** Request a timeline extension from stakeholders due to medical leave and stack learning curve. (Due: Dec 12)
- **Jasper:** Escalate the regulatory uncertainty as a blocker for the next board meeting. (Due: Dec 15)

---

## 11. BUDGET BREAKDOWN

Despite being "unfunded" in terms of a dedicated new budget, the project consumes existing capacity and infrastructure. The following is the projected internal cost allocation (bootstrapped).

| Category | Annual Estimated Cost | Details |
| :--- | :--- | :--- |
| **Personnel** | $680,000 | Salary allocation for 6 team members (distributed across other projects). |
| **Infrastructure** | $12,000 | Fly.io dedicated CPUs, PostgreSQL managed clusters, and Anycast IP. |
| **Tools** | $4,500 | GitHub Actions (Enterprise), Sentry for error tracking, Datadog for monitoring. |
| **Compliance/Audit** | $25,000 | External PCI DSS Level 1 certification and annual audit fees. |
| **Contingency** | $15,000 | Emergency cloud scaling or external consulting for Elixir optimization. |
| **TOTAL** | **$736,500** | **Internal Cost Basis** |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Implementation Detail
Because Stratos Systems processes credit card data directly, the following technical controls are mandatory:
1. **Encryption at Rest:** All `card_number` fields in the `transactions` table are encrypted using `AES-256-GCM`. The encryption key is stored in a separate hardware security module (HSM).
2. **Network Segmentation:** The billing microservice is isolated in its own VPC. Only the API Gateway can communicate with it via a strictly defined set of ports.
3. **Tokenization:** Once a card is captured, it is immediately tokenized. The system stores the token, not the raw PAN (Primary Account Number).

### Appendix B: Data Migration Mapping (Legacy $\rightarrow$ Umbra)
To ensure consistency during the migration from the four redundant tools, the following mapping is used:

| Legacy Tool | Field Name | Umbra Table | Umbra Field | Transformation |
| :--- | :--- | :--- | :--- | :--- |
| Tool A (Admin) | `patient_id_val` | `patients` | `patient_id` | UUID Cast |
| Tool B (Clinic) | `clinic_ref_no` | `patients` | `external_id` | String Trim |
| Tool C (Billing) | `cc_exp_date` | `transactions` | `expiry` | Format to ISO |
| Tool D (Audit) | `log_msg` | `audit_logs` | `payload_diff` | JSON Wrap |