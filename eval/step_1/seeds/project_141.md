# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft/Internal Review  
**Author:** Orin Oduya (VP of Product)  
**Classification:** Confidential – Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Glacier represents a critical strategic pivot for Coral Reef Solutions within the agriculture technology (AgTech) sector. For the past three years, the organization has operated using four disparate internal payment and billing tools. These tools—LegacyBill, AgriPay, SeedFlow, and HarvestCash—were acquired or developed in silos, resulting in extreme operational redundancy, fragmented data silos, and a bloated overhead cost. 

The primary objective of Glacier is a cost-reduction initiative. By consolidating these four redundant systems into a single, unified fintech payment processing system, Coral Reef Solutions will eliminate triple-licensing fees, reduce maintenance overhead for four separate codebases, and provide a "single source of truth" for all financial transactions across the AgTech portfolio.

### 1.2 ROI Projection and Success Metrics
The project is backed by a $1.5M budget, reflecting the high priority placed on operational efficiency. The return on investment (ROI) is calculated through two primary lenses: cost avoidance and revenue generation.

**Cost Avoidance:** By decommissioning the four legacy tools, the company expects to save approximately $200,000 annually in cloud licensing and third-party API maintenance fees.

**Revenue Generation:** The unification of these tools allows for the introduction of sophisticated pricing models and tiered subscriptions that were previously impossible due to technical fragmentation. The target success metric is **$500,000 in new revenue** attributed directly to Glacier's enhanced capabilities within the first 12 months post-launch.

**User Adoption:** To ensure the transition does not disrupt existing agricultural client workflows, the project sets a success threshold of an **80% feature adoption rate** among pilot users. This ensures that the consolidation is not merely a technical success, but a functional one that meets the needs of the end-user.

### 1.3 Strategic Alignment
Glacier aligns with the broader corporate goal of "Digital Simplification." By moving to a serverless architecture with consolidated data isolation, Coral Reef Solutions transitions from a fragmented "collection of tools" to a scalable "platform." The project focuses on high-stability features (audit trails, multi-tenancy) to ensure that as the AgTech market evolves, the financial backbone of the company is tamper-proof and scalable.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Glacier utilizes a **Mixed-Stack Serverless Architecture**. Due to the nature of the consolidation, Glacier must interoperate with three different legacy stacks (Node.js/TypeScript, Python/Django, and Java/Spring Boot). Rather than a complete rewrite—which would be prohibitively expensive and risky—Glacier acts as an orchestration layer.

The system is built upon **Serverless Functions** (AWS Lambda / Azure Functions) orchestrated by a centralized **API Gateway**. This allows the team to wrap legacy logic in modern interfaces while gradually migrating the core business logic to a unified TypeScript environment.

### 2.2 Infrastructure Components
- **Orchestration Layer:** API Gateway (RESTful) handling routing, rate limiting, and authentication.
- **Compute Layer:** Serverless functions triggered by API events or asynchronous queues.
- **Data Layer:** A multi-tenant PostgreSQL instance utilizing Row-Level Security (RLS) for isolation.
- **State Management:** Redis clusters for caching and session management.
- **Security Layer:** Quarterly penetration testing and an internal IAM (Identity and Access Management) system.

### 2.3 Architecture Diagram (ASCII)

```text
[ Client Layer ] <---> [ API Gateway ] <---> [ Auth / IAM Service ]
                               |
                               v
                 [ Serverless Orchestration Layer ]
                /              |               \
      (Lambda A)             (Lambda B)           (Lambda C)
     [New Logic]          [Legacy Bridge]       [Integration]
          |                    |                      |
          v                    v                      v
    [ PostgreSQL ] <--- [ Shared Data Bus ] ---> [ Third Party APIs ]
    (Multi-Tenant)        (Event Bridge)        (Stripe/Plaid/etc)
          ^                                            ^
          |                                            |
    [ Audit Log ] <--- [ Tamper-Evident Storage ] <--- [ Security ]
    (S3 Glacier)       (SHA-256 Hashing)             (Pen-Testing)
```

### 2.4 Data Isolation Strategy
The system implements **Multi-tenant Data Isolation** via a shared infrastructure model. Each single-tenant client is assigned a unique `tenant_id`. Every database query is filtered by this ID. To prevent "leaky" queries, a database middleware layer enforces the presence of the `tenant_id` in the WHERE clause of every SQL statement.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Complete

**Functional Description:**
The Workflow Automation Engine allows AgTech administrators to create complex "If-This-Then-That" (IFTTT) logic for payment processing. Given the complexity of agricultural billing (e.g., payments triggered by harvest dates or weather events), a visual rule builder was implemented to allow non-technical users to define payment triggers.

**Technical Specifications:**
- **Visual Builder:** A drag-and-drop interface developed by Dmitri Jensen using React Flow. It allows users to connect "Triggers" (e.g., Invoice Created) to "Actions" (e.g., Send Email, Trigger Payment).
- **Rule Engine:** The backend parses the visual graph into a JSON-based logic tree stored in the `workflow_definitions` table.
- **Execution:** A serverless worker polls the event bus. When a trigger event occurs, the worker evaluates the logic tree and executes the associated actions.
- **Example Workflow:** "IF [Crop_Weight] > 500kg AND [Payment_Status] == 'Pending' THEN [Execute_Payment] AND [Notify_Vendor]."

**Completion Note:** This feature is fully deployed in the staging environment and has passed QA sign-off by Beatriz Moreau.

### 3.2 Multi-Tenant Data Isolation with Shared Infrastructure
**Priority:** High | **Status:** Complete

**Functional Description:**
To maintain cost efficiency while ensuring strict security, Glacier uses a shared infrastructure model. Unlike a "database-per-tenant" approach, which would be an administrative nightmare with thousands of agricultural clients, Glacier uses a "schema-shared" approach with logical isolation.

**Technical Specifications:**
- **Tenant Identification:** Every request must include a `X-Tenant-ID` header, validated against the JWT (JSON Web Token).
- **Row-Level Security (RLS):** The PostgreSQL database implements RLS. A session variable is set at the start of every transaction: `SET app.current_tenant = 'tenant_123';`. The database then automatically hides all rows that do not match this ID.
- **Shared Resource Management:** To prevent a single large client from consuming all serverless concurrency, the API Gateway implements tenant-based rate limiting.

**Completion Note:** This architecture is the foundation of the project and was the first component verified during the initial architecture sprint.

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** Complete

**Functional Description:**
In fintech, traceability is non-negotiable. The Audit Trail logs every change to financial records, ensuring that no payment can be modified without a permanent record. The "Tamper-Evident" requirement ensures that even a database administrator cannot alter logs without detection.

**Technical Specifications:**
- **Logging Mechanism:** Every `UPDATE` or `DELETE` operation triggers a Lambda function that captures the "Before" and "After" state of the record.
- **Hashing Chain:** Each log entry contains a SHA-256 hash of its own data plus the hash of the previous entry (similar to a blockchain). This creates a cryptographic chain.
- **Cold Storage:** Logs are archived every 24 hours to an Amazon S3 bucket with "Object Lock" enabled, preventing deletion for a period of 7 years.
- **Verification Tool:** A utility exists to scan the hash chain; any mismatch in the hashes triggers an immediate security alert to the VP of Product.

**Completion Note:** This feature satisfies the basic internal compliance requirements for financial auditing.

### 3.4 A/B Testing Framework (Feature Flag System)
**Priority:** High | **Status:** Not Started

**Functional Description:**
To optimize the payment conversion rate for agricultural users, the system requires a built-in A/B testing framework. This is not a separate tool but is "baked into" the feature flag system. This allows the team to roll out new payment UI components to 10% of users and measure the impact on completion rates.

**Technical Specifications (Planned):**
- **Flag Management:** A dashboard to define flags (e.g., `new_checkout_flow`).
- **Assignment Engine:** A deterministic hashing algorithm based on `user_id` to ensure a user consistently sees the same variant.
- **Telemetry:** Integration with the analytics engine to track "Conversion Rate" per variant.
- **Rollout Strategy:** Ability to transition a flag from `experimental` (50/50 split) to `stable` (100% rollout).

**Implementation Plan:** This will be developed following the production launch to allow for iterative refinement of the UI.

### 3.5 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Not Started

**Functional Description:**
While the core payment engine handles transactions, the automated billing system will manage recurring invoices, subscription tiers (e.g., Basic, Pro, Enterprise Ag), and automated dunning (retrying failed payments).

**Technical Specifications (Planned):**
- **Subscription Engine:** A state machine to handle transitions (Active $\rightarrow$ Past Due $\rightarrow$ Cancelled).
- **Billing Cycles:** Support for monthly, quarterly, and annual billing, with a specific "Seasonal" cycle for farmers (billing based on harvest cycles).
- **Dunning Logic:** Automated email sequences triggered by payment failures, with an escalating retry schedule (Day 1, Day 3, Day 7).
- **Invoice Generator:** A PDF generation service that attaches a breakdown of costs to the billing event.

**Implementation Plan:** This is a "nice to have" and will only be addressed if the budget allows after the primary milestones are met.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/` and require a Bearer Token in the Authorization header.

### 4.1 Payment Processing

**Endpoint:** `POST /payments/execute`
- **Description:** Initiates a payment transaction.
- **Request Body:**
  ```json
  {
    "amount": 1250.00,
    "currency": "USD",
    "source_id": "src_98765",
    "destination_id": "dest_12345",
    "metadata": { "invoice_id": "INV-2024-001" }
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "transaction_id": "txn_abc123",
    "status": "processing",
    "estimated_completion": "2023-10-25T10:00:00Z"
  }
  ```

**Endpoint:** `GET /payments/{transaction_id}`
- **Description:** Retrieves the current status of a specific payment.
- **Response (200 OK):**
  ```json
  {
    "transaction_id": "txn_abc123",
    "status": "completed",
    "amount": 1250.00,
    "timestamp": "2023-10-24T14:00:00Z"
  }
  ```

### 4.2 Workflow Automation

**Endpoint:** `POST /workflows/create`
- **Description:** Saves a new visual rule definition.
- **Request Body:**
  ```json
  {
    "workflow_name": "Harvest Trigger",
    "rules": [
      { "trigger": "event.harvest_complete", "action": "payment.execute" }
    ]
  }
  ```
- **Response (201 Created):**
  ```json
  { "workflow_id": "wf_5566", "status": "active" }
  ```

**Endpoint:** `DELETE /workflows/{workflow_id}`
- **Description:** Deactivates and removes a workflow.
- **Response (204 No Content):** `Empty Body`

### 4.3 Multi-Tenancy & Administration

**Endpoint:** `GET /tenants/{tenant_id}/config`
- **Description:** Retrieves configuration settings for a specific agricultural client.
- **Response (200 OK):**
  ```json
  {
    "tenant_id": "tenant_123",
    "currency_default": "USD",
    "billing_cycle": "seasonal"
  }
  ```

**Endpoint:** `POST /tenants/provision`
- **Description:** Provisions a new tenant environment.
- **Request Body:** `{ "client_name": "GreenValley Farms", "admin_email": "admin@gv.com" }`
- **Response (201 Created):** `{ "tenant_id": "tenant_999", "setup_status": "complete" }`

### 4.4 Audit & Compliance

**Endpoint:** `GET /audit/logs?tenant_id={id}&start_date={date}`
- **Description:** Retrieves a tamper-evident log of all activities for a tenant.
- **Response (200 OK):**
  ```json
  [
    { "log_id": "log_001", "action": "UPDATE", "hash": "a1b2c3d4...", "prev_hash": "0000..." }
  ]
  ```

**Endpoint:** `POST /audit/verify`
- **Description:** Triggers a full cryptographic verification of the audit chain.
- **Response (200 OK):** `{ "status": "verified", "mismatches": 0 }`

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL instance. All tables use UUIDs as primary keys.

### 5.1 Table Definitions

1.  **`tenants`**
    - `tenant_id` (UUID, PK)
    - `company_name` (VARCHAR)
    - `created_at` (TIMESTAMP)
    - `status` (ENUM: active, suspended, archived)
2.  **`users`**
    - `user_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `email` (VARCHAR, UNIQUE)
    - `password_hash` (TEXT)
    - `role` (ENUM: admin, operator, viewer)
3.  **`accounts`**
    - `account_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `balance` (DECIMAL 19,4)
    - `currency` (VARCHAR 3)
4.  **`transactions`**
    - `transaction_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `source_account_id` (UUID, FK $\rightarrow$ accounts)
    - `dest_account_id` (UUID, FK $\rightarrow$ accounts)
    - `amount` (DECIMAL 19,4)
    - `status` (ENUM: pending, completed, failed)
    - `created_at` (TIMESTAMP)
5.  **`workflow_definitions`**
    - `workflow_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `logic_json` (JSONB)
    - `is_active` (BOOLEAN)
6.  **`workflow_executions`**
    - `execution_id` (UUID, PK)
    - `workflow_id` (UUID, FK $\rightarrow$ workflow_definitions)
    - `status` (ENUM: success, error)
    - `executed_at` (TIMESTAMP)
7.  **`audit_logs`**
    - `log_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `entity_name` (VARCHAR) — (e.g., 'transactions')
    - `entity_id` (UUID)
    - `old_value` (JSONB)
    - `new_value` (JSONB)
    - `hash` (VARCHAR 64)
    - `prev_hash` (VARCHAR 64)
8.  **`feature_flags`**
    - `flag_id` (UUID, PK)
    - `flag_key` (VARCHAR, UNIQUE)
    - `variant_config` (JSONB)
    - `is_enabled` (BOOLEAN)
9.  **`flag_assignments`**
    - `assignment_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ users)
    - `flag_id` (UUID, FK $\rightarrow$ feature_flags)
    - `assigned_variant` (VARCHAR)
10. **`subscriptions`**
    - `subscription_id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants)
    - `plan_type` (VARCHAR)
    - `start_date` (DATE)
    - `end_date` (DATE)
    - `auto_renew` (BOOLEAN)

### 5.2 Relationships
- **Tenants $\rightarrow$ Users/Accounts/Transactions:** One-to-Many. The `tenant_id` is the primary partition key for all data.
- **Users $\rightarrow$ Flag Assignments:** One-to-Many. Allows specific users to be targeted for A/B tests.
- **Workflow Definitions $\rightarrow$ Executions:** One-to-Many. Tracks every time a rule is triggered.
- **Audit Logs $\rightarrow$ Tenants:** Many-to-One. All logs are grouped by tenant for regulatory export.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Glacier utilizes three distinct environments to ensure stability.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and feature development.
- **Access:** Full access for the 6-person team.
- **Deployment:** Continuous deployment via GitHub Actions.
- **Data:** Mocked data; no real client information.

**2. Staging (QA):**
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Access:** Development team and Beatriz Moreau (QA Lead).
- **Deployment:** Triggered manually after a successful Dev build.
- **Data:** Sanitized clones of production data.

**3. Production (Prod):**
- **Purpose:** Live agricultural client processing.
- **Access:** Highly restricted. Only Orin Oduya and designated DevOps leads have deployment rights.
- **Deployment:** Manual QA Gate. A deployment is only pushed if Beatriz Moreau provides a signed-off QA report.

### 6.2 The "QA Gate" Deployment Process
To mitigate risks in a fintech environment, Glacier does not use fully automated CD for Production. The process is as follows:
1. Code is merged to `main`.
2. Build is deployed to **Staging**.
3. **QA Window:** Beatriz Moreau conducts a full regression suite.
4. **Sign-off:** QA Lead marks the build as "Passed" in Jira.
5. **Deployment:** Manual trigger to Prod.
6. **Turnaround:** The standard turnaround from Staging sign-off to Production is **2 days**.

### 6.3 Infrastructure Bottlenecks
Currently, the **CI pipeline takes 45 minutes**. This is due to a lack of parallelization in the testing suite and the inclusion of heavy legacy Java artifacts in the serverless build process. This is identified as a primary piece of technical debt to be addressed post-launch.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Every serverless function must have $\ge 80\%$ line coverage.
- **Tools:** Jest (for TypeScript), PyTest (for Python).
- **Focus:** Business logic, hash calculations for audit logs, and tenant-id filtering logic.

### 7.2 Integration Testing
- **Scope:** Verifying the interaction between the API Gateway and the Serverless functions, as well as the database connectivity.
- **Method:** Automated "Smoke Tests" that run against the Staging environment.
- **Focus:** Ensuring the Mixed-Stack interoperability works (e.g., the Node.js function can correctly read data written by the Java legacy bridge).

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Create Tenant $\rightarrow$ Set Workflow $\rightarrow$ Execute Payment").
- **Tools:** Cypress / Playwright.
- **Frequency:** Performed by Beatriz Moreau's team during the 2-day QA gate before production deployment.

### 7.4 Security Testing
- **Penetration Testing:** Performed **quarterly** by an external security firm.
- **Focus:** Testing for "Tenant Leakage" (attempting to access `tenant_B` data using a `tenant_A` token) and SQL injection in the legacy bridges.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with serverless mixed-stack architecture | High | High | Negotiate timeline extension with stakeholders; provide internal training. |
| R-02 | Regulatory requirements for Ag-Fintech are changing | Medium | High | Engage external consultant for an independent assessment of compliance. |
| R-03 | CI Pipeline inefficiency causing dev velocity drop | High | Medium | Allocate a "Tech Debt Sprint" to parallelize the 45-min pipeline. |
| R-04 | Legacy stack interoperability failures | Medium | High | Implement rigorous integration testing and a "Circuit Breaker" pattern. |
| R-05 | Cloud provider provisioning delays | High | Medium | Maintain a multi-cloud strategy or use alternative regions. |

**Impact Matrix:**
- **Low:** Minimal impact on launch date.
- **Medium:** Delay of 1–2 weeks; budget increase $< 5\%$.
- **High:** Critical failure; launch delay $> 1$ month; budget increase $> 10\%$.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases
The project is divided into four primary phases:

**Phase 1: Foundation (Current - Jan 2025)**
- Establishment of Multi-tenant isolation.
- Development of Audit Trail logging.
- Setup of API Gateway.
- *Dependency:* Cloud provider provisioning (Current Blocker).

**Phase 2: Core Logic (Jan 2025 - April 2025)**
- Finalization of Workflow Automation engine.
- Legacy bridge integration for the 3 stacks.
- Initial QA regression cycles.

**Phase 3: Launch and Stabilization (April 2025 - June 2025)**
- Production launch of the unified system.
- Monitoring of feature adoption.
- Post-launch bug fixing.

**Phase 4: Optimization (June 2025 - August 2025)**
- Implementation of A/B Testing framework.
- Architecture review and cleanup.
- Stakeholder final demo.

### 9.2 Key Milestone Dates
- **Milestone 1: Production Launch** $\rightarrow$ **2025-04-15**
- **Milestone 2: Architecture Review Complete** $\rightarrow$ **2025-06-15**
- **Milestone 3: Stakeholder Demo and Sign-off** $\rightarrow$ **2025-08-15**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-02)
- **Attendees:** Orin, Dmitri, Beatriz, Esme
- **Notes:**
    - Dmitri worried about the mixed stack.
    - Beatriz wants 2 days for QA before prod. Agreed.
    - Esme mentions the legacy Java code is messy.
    - Decision: use API Gateway to hide the mess.
    - Blocker: Cloud provider still hasn't provisioned the VPC.

### Meeting 2: Sprint 4 Review (2023-12-15)
- **Attendees:** Orin, Dmitri, Beatriz, Esme
- **Notes:**
    - Workflow engine is "done".
    - Beatriz found a bug in tenant isolation.
    - Fixed it via RLS.
    - Discussion on CI pipeline. 45 mins is too long.
    - Orin: "Fix it later, focus on launch."

### Meeting 3: Risk Assessment (2024-01-20)
- **Attendees:** Orin, Beatriz, External Consultant (Briefly)
- **Notes:**
    - Regs might change in Q3.
    - Consultant suggests independent audit.
    - Orin to check budget for consultant.
    - Team trust is "building" but still some tension between Esme and Dmitri over code style.

---

## 11. BUDGET BREAKDOWN

The total budget for Project Glacier is **$1,500,000**. This is a well-funded initiative, allowing for high-quality QA and robust DevOps.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $950,000 | Salaried staff (4) + Contractor (Esme) for 18 months. |
| **Infrastructure** | $200,000 | AWS/Azure serverless costs, PostgreSQL managed instances, Redis. |
| **Tooling & Security** | $150,000 | Quarterly pen-testing, CI/CD licenses, monitoring tools (Datadog). |
| **External Consulting** | $100,000 | Regulatory assessment and independent security audits. |
| **Contingency** | $100,000 | Reserved for emergency scaling or timeline extensions. |
| **Total** | **$1,500,000** | |

---

## 12. APPENDICES

### Appendix A: Legacy Stack Interop Mapping
To ensure the three legacy stacks can communicate, the following translation layer is used:
- **LegacyBill (Node.js):** Communicates via JSON over HTTPS.
- **AgriPay (Python):** Uses a gRPC bridge for high-performance transaction updates.
- **SeedFlow (Java):** Uses a SOAP-to-REST wrapper implemented in the API Gateway to allow modern serverless functions to call legacy endpoints.

### Appendix B: Hash Chain Specification
The tamper-evident storage uses the following logic for log chaining:
$\text{Hash}_n = \text{SHA-256}(\text{Timestamp} + \text{TenantID} + \text{Payload} + \text{Hash}_{n-1})$

This ensures that any alteration to a record in the past would require the recalculation of all subsequent hashes, which is computationally infeasible given the "Object Lock" on the S3 archive.