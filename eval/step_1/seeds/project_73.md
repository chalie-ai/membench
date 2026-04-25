# PROJECT VANGUARD: PLATFORM MODERNIZATION SPECIFICATION
**Document Version:** 1.0.4  
**Status:** Baseline / Approved  
**Owner:** Niko Liu (Engineering Manager)  
**Company:** Clearpoint Digital  
**Classification:** Confidential – PCI DSS Restricted  
**Date:** October 24, 2025  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Vanguard represents a critical strategic pivot for Clearpoint Digital. As a primary provider of government services, our current operational efficiency is hindered by a legacy monolithic architecture that, while structurally "clean," has reached the ceiling of its scalability and maintainability. Project Vanguard is the formalized initiative to migrate this monolith into a distributed microservices architecture governed by a centralized API Gateway.

The objective is to decouple high-load government service modules—specifically billing, document handling, and user dashboards—into independent services. This migration will occur over an 18-month window, ensuring zero downtime for citizens accessing essential services. The project is currently entering its primary build phase, backed by a budget of $800,000, which provides a comfortable runway for the intensive 6-month core development cycle.

### 1.2 Business Justification
The current monolithic system, while stable, creates a "deployment bottleneck." A change in the billing module requires a full redeployment of the entire government services suite, introducing unacceptable risks to system stability. Furthermore, the requirement for PCI DSS Level 1 compliance necessitates a strict isolation of credit card processing data. By migrating to a microservices architecture, we can isolate the "Payment Vault" service, reducing the scope of PCI audits and lowering the risk of wide-scale data breaches.

From an operational standpoint, the government agencies utilizing Clearpoint Digital are demanding higher agility. The transition to an API Gateway allows for the rapid onboarding of third-party integration partners without modifying the core business logic.

### 1.3 ROI Projection and Success Metrics
The Return on Investment (ROI) for Project Vanguard is calculated based on two primary vectors: operational cost reduction and risk mitigation.

**Metric 1: Reduction in Manual Processing.**  
Current manual processing for government applications takes an average of 12 business days. Through the implementation of the Workflow Automation Engine and the new API Gateway, we project a **50% reduction in manual processing time**, bringing the average down to 6 business days. This saves an estimated $1.2M annually in administrative labor costs.

**Metric 2: Compliance and Audit.**  
The cost of a failed PCI DSS audit or a security breach in a government context is catastrophic, potentially totaling millions in fines and lost contracts. Success is defined as **passing the external security audit on the first attempt** by November 15, 2026.

**Financial Projection:**
- **Total Investment:** $800,000
- **Projected Annual Savings:** $1.2M (Labor) + $200k (Infra optimization)
- **Break-even Point:** Month 7 post-deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Vanguard employs a "Strangler Fig" pattern to migrate the monolith. We are inheriting three distinct legacy stacks:
1. **Stack A (Legacy Java/Spring):** Core government logic.
2. **Stack B (Node.js/Express):** User-facing portals.
3. **Stack C (Python/Django):** Data processing and reporting.

These three stacks must interoperate via a new **Kong API Gateway** (v3.4), which handles authentication, rate limiting, and request routing.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ Client Layer ] 
      |
      v
[ Kong API Gateway (v3.4) ] <---> [ Auth Service (OAuth2/OIDC) ]
      |
      +-------------------------------------------------------+
      |                       |                              |
[ Dashboard Svc ]      [ Billing Svc ]              [ Document Svc ]
(Node.js/React)       (Java/Spring Boot)           (Python/FastAPI)
      |                       |                              |
[ Redis Cache ]       [ PostgreSQL (PCI) ]           [ S3 Bucket / ClamAV ]
      |                       |                              |
      +-----------------------+------------------------------+
                              |
                    [ Legacy Monolith (The Core) ]
                    (Interoperability via gRPC/REST)
```

### 2.3 Technical Stack Details
- **Runtime Environments:** Docker 24.0, Kubernetes 1.27 (EKS).
- **CI/CD:** GitLab CI (Version 16.x) utilizing rolling deployments to ensure zero-downtime.
- **Communication:** REST for external consumers; gRPC for internal service-to-service communication to minimize latency.
- **Security:** TLS 1.3 for all transit; AES-256 encryption for data at rest; PCI DSS Level 1 compliance for the Billing Service.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** In Progress | **Owner:** Finn Costa (Frontend Lead)

**Functional Description:**
The Dashboard serves as the primary interface for government administrators. It must allow users to personalize their workspace by adding, removing, and rearranging "widgets" (small data visualizations or action panels).

**Detailed Requirements:**
- **Widget Library:** Users can choose from a library of 12 pre-defined widgets (e.g., "Pending Applications," "Revenue Monthly Chart," "System Health").
- **Drag-and-Drop Engine:** Implementation via `react-grid-layout` v1.4.0. The layout must persist in the database so the user's configuration is saved across sessions.
- **Dynamic Data Fetching:** Each widget must call a specific endpoint on the API Gateway. To prevent "request storms," the dashboard must implement a debounced loading strategy.
- **State Management:** Use Redux Toolkit to manage the global state of the dashboard layout.

**Technical Constraints:**
- Must support window resizing (responsive breakpoints at 1024px, 768px, and 480px).
- Maximum of 20 widgets per dashboard to prevent browser DOM performance degradation.

---

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** Complete | **Owner:** Niko Liu

**Functional Description:**
Given the government nature of the project, every state-changing action must be logged. These logs must be "tamper-evident," meaning any alteration to a historical log entry must be detectable.

**Detailed Requirements:**
- **Event Capture:** Every `POST`, `PUT`, `PATCH`, and `DELETE` request passing through the API Gateway must be logged.
- **Cryptographic Chaining:** Each log entry contains a hash of the previous entry (Blockchain-lite approach), creating a chain of integrity.
- **Storage:** Logs are written to an immutable S3 bucket with "Object Lock" enabled.
- **Searchability:** An indexing service (Elasticsearch 8.x) provides a read-only view of these logs for auditors.

**Technical Constraints:**
- Latency overhead for logging must be < 50ms.
- Storage must be PCI DSS compliant, ensuring no Plaintext Primary Account Numbers (PAN) are ever written to logs.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low (Nice to Have) | **Status:** Complete | **Owner:** Ines Oduya

**Functional Description:**
A system that allows non-technical staff to create "If-This-Then-That" (IFTTT) rules for government application processing.

**Detailed Requirements:**
- **Visual Builder:** A node-based UI using `React Flow` where users can drag "Triggers" (e.g., "Application Submitted") and "Actions" (e.g., "Send Email," "Change Status to Pending").
- **Rule Engine:** A backend processor that evaluates these rules against incoming events.
- **Variable Injection:** Ability to inject data from the application (e.g., "Dear {applicant_name}") into automated messages.

**Technical Constraints:**
- Rules must be validated for circular dependencies before deployment.
- Maximum execution depth of 10 nested rules to prevent infinite loops.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** Complete | **Owner:** Yara Stein

**Functional Description:**
A secure pipeline for users to upload supporting documents (PDFs, JPGs) which are then scanned for malware before being stored and served.

**Detailed Requirements:**
- **Upload Pipeline:** Files are uploaded to a "Quarantine" S3 bucket.
- **Virus Scanning:** A trigger invokes a ClamAV-based microservice to scan the file. If a virus is detected, the file is deleted immediately, and the user is notified.
- **Distribution:** Once cleared, files are moved to a "Production" bucket and served via CloudFront CDN.
- **Integrity:** Files are hashed (SHA-256) upon upload and verified upon delivery.

**Technical Constraints:**
- Maximum file size: 25MB.
- Scanning must be completed within 30 seconds of upload.

---

### 3.5 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** Complete | **Owner:** Niko Liu

**Functional Description:**
A PCI DSS Level 1 compliant system for handling government service fees and recurring subscriptions.

**Detailed Requirements:**
- **Payment Vaulting:** Integration with Stripe/Braintree to ensure Clearpoint Digital never stores raw credit card numbers.
- **Subscription Logic:** Support for monthly, quarterly, and annual billing cycles.
- **Invoicing:** Automatic generation of PDF invoices stored in the Document Service.
- **Dunning Process:** Automated retry logic for failed payments (3 attempts over 14 days).

**Technical Constraints:**
- Must adhere to strict PCI DSS Level 1 isolation.
- All financial transactions must be recorded in the Audit Trail (Feature 3.2).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are routed through the API Gateway at `https://api.clearpoint.gov/v1/`.

### 4.1 Dashboard Endpoints
**Endpoint:** `GET /dashboard/layout`
- **Description:** Retrieves the saved widget configuration for the current user.
- **Request:** `Header: Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "userId": "user_9921",
    "widgets": [
      {"id": "w1", "type": "chart", "x": 0, "y": 0, "w": 6, "h": 4},
      {"id": "w2", "type": "list", "x": 6, "y": 0, "w": 6, "h": 4}
    ]
  }
  ```

**Endpoint:** `POST /dashboard/layout`
- **Description:** Saves the new drag-and-drop layout.
- **Request Body:**
  ```json
  {
    "widgets": [{"id": "w1", "x": 2, "y": 0, "w": 6, "h": 4}]
  }
  ```
- **Response (201 Created):** `{"status": "success"}`

### 4.2 Billing Endpoints
**Endpoint:** `POST /billing/checkout`
- **Description:** Initiates a payment session.
- **Request Body:** `{"amount": 5000, "currency": "USD", "paymentMethod": "cc"}`
- **Response (200 OK):** `{"checkoutUrl": "https://stripe.com/pay/...", "sessionId": "sess_123"}`

**Endpoint:** `GET /billing/invoice/{invoiceId}`
- **Description:** Retrieves a billing invoice.
- **Response (200 OK):** `{"invoiceId": "inv_001", "amount": 50.00, "status": "paid", "url": "..."}`

### 4.3 Document Endpoints
**Endpoint:** `POST /docs/upload`
- **Description:** Uploads a file to the quarantine zone.
- **Request:** Multipart form data.
- **Response (202 Accepted):** `{"fileId": "file_abc123", "status": "scanning"}`

**Endpoint:** `GET /docs/status/{fileId}`
- **Description:** Checks if the virus scan is complete.
- **Response (200 OK):** `{"fileId": "file_abc123", "status": "clean", "cdnUrl": "..."}`

### 4.4 Workflow Endpoints
**Endpoint:** `POST /workflow/rules`
- **Description:** Creates a new automation rule.
- **Request Body:** `{"trigger": "APP_SUBMIT", "action": "NOTIFY_ADMIN", "condition": "amount > 1000"}`
- **Response (201 Created):** `{"ruleId": "rule_88"}`

**Endpoint:** `DELETE /workflow/rules/{ruleId}`
- **Description:** Deactivates a rule.
- **Response (204 No Content):** `null`

---

## 5. DATABASE SCHEMA

The system utilizes a distributed database approach. The Billing Service uses a hardened PostgreSQL instance, while the Dashboard and Workflow services use a shared PostgreSQL cluster.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | N/A | `email`, `role`, `created_at` | User identity and permissions. |
| `dashboard_layouts` | `layout_id` | `user_id` | `config_json`, `updated_at` | Stores widget positions. |
| `widgets` | `widget_id` | N/A | `widget_type`, `default_query` | Registry of available widgets. |
| `audit_logs` | `log_id` | `user_id` | `action`, `payload`, `prev_hash`, `current_hash` | Tamper-evident event log. |
| `workflow_rules` | `rule_id` | `creator_id` | `trigger_event`, `logic_json`, `is_active` | Automation rule definitions. |
| `workflow_history` | `exec_id` | `rule_id` | `triggered_at`, `outcome`, `duration` | Log of rule executions. |
| `documents` | `doc_id` | `user_id` | `filename`, `s3_path`, `virus_status` | File metadata and status. |
| `scan_results` | `scan_id` | `doc_id` | `scanner_version`, `threat_found`, `timestamp` | Detailed ClamAV results. |
| `subscriptions` | `sub_id` | `user_id` | `plan_id`, `status`, `next_billing_date` | Recurring billing state. |
| `transactions` | `txn_id` | `sub_id` | `amount`, `gateway_txn_id`, `timestamp` | Financial record of payments. |

### 5.2 Relationships
- `users` $\rightarrow$ `dashboard_layouts` (1:1)
- `users` $\rightarrow$ `audit_logs` (1:N)
- `users` $\rightarrow$ `documents` (1:N)
- `documents` $\rightarrow$ `scan_results` (1:1)
- `subscriptions` $\rightarrow$ `transactions` (1:N)
- `workflow_rules` $\rightarrow$ `workflow_history` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Vanguard utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature testing.
- **Infrastructure:** Shared Kubernetes namespace.
- **Database:** Mock data / Local PostgreSQL.
- **Deployment:** Automatic push from `develop` branch in GitLab CI.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of production hardware (1:1 scale).
- **Database:** Sanitized copy of production data.
- **Deployment:** Manual trigger from `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live government services.
- **Infrastructure:** Multi-AZ (Availability Zone) EKS Cluster with Auto-scaling groups.
- **Database:** High-availability PostgreSQL with synchronous replication.
- **Deployment:** Rolling updates (Canary deployment) via GitLab CI.

### 6.2 CI/CD Pipeline Analysis
The current CI pipeline is a known bottleneck.
- **Current State:** 45-minute total runtime. This is caused by sequential execution of the test suite and a lack of Docker layer caching.
- **Optimization Plan:**
    - Implement **Parallel Test Execution**: Splitting the 4,000 unit tests into 4 parallel jobs.
    - **Layer Caching**: Utilizing GitLab's `S3 cache` for Docker images.
    - **Selective Builds**: Only rebuilding services whose code has changed (using `changes` keyword in `.gitlab-ci.yml`).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every microservice must maintain $\ge 80\%$ code coverage.
- **Tools:** JUnit 5 (Java), PyTest (Python), Jest (Node.js).
- **Requirement:** All unit tests must pass in the GitLab CI pipeline before merging to `develop`.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the API Gateway and the downstream services.
- **Focus:** Contract testing. We use **Pact** to ensure that the Billing Service doesn't break the Dashboard's expectation of the API response.
- **Environment:** Executed in the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulating a full user journey (e.g., "User logs in $\rightarrow$ Uploads Document $\rightarrow$ Pays Fee $\rightarrow$ Views Dashboard").
- **Tools:** Cypress 12.x.
- **Frequency:** Executed once per release candidate.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotating out of role | Medium | High | Negotiate timeline extension with remaining stakeholders; secure written sign-off on current milestones. |
| **R-02** | Integration partner API undocumented/buggy | High | Medium | Dedicate one engineer to create an internal "Wrapper SDK" that documents workarounds and stabilizes the API. |
| **R-03** | PCI Audit failure | Low | Critical | Bi-weekly internal audits; engage a 3rd party pre-audit consultant in September 2026. |
| **R-04** | CI Pipeline bottleneck (45m) | High | Low | Implement parallelization and Docker caching (see Section 6.2). |

### 8.1 Probability/Impact Matrix
- **High Impact / High Probability:** Integration Partner API $\rightarrow$ **Immediate Action Required**.
- **High Impact / Medium Probability:** Sponsor Rotation $\rightarrow$ **Active Monitoring**.
- **Low Impact / High Probability:** CI Pipeline $\rightarrow$ **Scheduled Maintenance**.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase breakdown
The project follows a phased approach over 18 months, with a core "Build Phase" of 6 months.

**Phase 1: Discovery & Foundation (Months 1-3)**
- Architecture design and API Gateway setup.
- Setup of Kubernetes clusters.

**Phase 2: Core Build (Months 4-9) — CURRENT PHASE**
- Migration of Billing and Document services.
- Development of the Customizable Dashboard.
- Implementation of the Audit Trail.

**Phase 3: Hardening & Compliance (Months 10-15)**
- Security auditing and PCI DSS Level 1 certification.
- Integration of Workflow Engine.
- Load testing and CI pipeline optimization.

**Phase 4: Transition & Sunset (Months 16-18)**
- Final traffic shift from Monolith $\rightarrow$ Microservices.
- Decommissioning of legacy servers.

### 9.2 Key Milestone Dates
- **Milestone 1: Stakeholder demo and sign-off** $\rightarrow$ **Target: 2026-07-15**
  - *Dependency:* Dashboard and Billing services must be functional in Staging.
- **Milestone 2: Internal alpha release** $\rightarrow$ **Target: 2026-09-15**
  - *Dependency:* Document upload and Virus scanning must be integrated.
- **Milestone 3: Security audit passed** $\rightarrow$ **Target: 2026-11-15**
  - *Dependency:* Audit trail logs must be verified as tamper-evident.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2025-11-02)
- *Attendees:* Niko, Finn, Ines, Yara.
- *Notes:*
    - Monolith is too slow.
    - Need Kong for gateway.
    - Finn wants React Flow for rules.
    - Niko says yes, but keep it low priority.
    - 45 min CI is a joke. Need to fix.

### Meeting 2: Integration Crisis (2025-12-12)
- *Attendees:* Niko, Yara.
- *Notes:*
    - Partner API is broken.
    - No docs.
    - Yara found a way to bypass the bug by sending a null header.
    - Niko: "Document it in the Wiki immediately."
    - Rate limits are killing the test suite. Blocked.

### Meeting 3: Budget and Sponsor Review (2026-01-20)
- *Attendees:* Niko, Project Sponsor.
- *Notes:*
    - Sponsor leaving in Q3.
    - Budget is $800k—enough for now.
    - Need a demo by July.
    - Concerns about PCI audit. Niko confirmed the "Payment Vault" approach.

---

## 11. BUDGET BREAKDOWN

The total project budget is **$800,000**, allocated for the core 6-month build and subsequent hardening.

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Salaries for 20+ person team across 3 departments. |
| **Infrastructure** | 20% | $160,000 | AWS EKS, RDS, S3, and CloudFront costs. |
| **Tooling/Licenses** | 8% | $64,000 | Kong Enterprise, GitLab Premium, Snyk Security, Pact.io. |
| **Contingency** | 7% | $56,000 | Reserve for emergency third-party consulting or hardware. |
| **TOTAL** | **100%** | **$800,000** | |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To achieve the target milestone on 2026-11-15, the following must be verified:
1. **Network Segmentation:** The Billing Service must reside in a private subnet with no direct public internet access (routed only through the Gateway).
2. **Encryption:** All PAN (Primary Account Numbers) must be replaced by tokens from the payment provider.
3. **Access Control:** Multi-factor authentication (MFA) required for all engineers accessing the production environment.
4. **Logging:** Audit logs must be reviewed weekly for unauthorized access attempts.

### Appendix B: Third-Party API Workarounds (The "Partner" Document)
Due to the undocumented nature of the integration partner's API, the following workarounds are mandated:
- **Issue:** `/get-status` endpoint returns 500 if the request body is empty.
- **Workaround:** Always send `{"ping": true}` in the request body.
- **Issue:** Rate limits are set to 10 requests per second (RPS) in the Sandbox environment.
- **Workaround:** Implement a `Sleeper` utility in the integration test suite to throttle requests to 8 RPS.
- **Issue:** Date format is inconsistently `YYYY-MM-DD` and `DD/MM/YYYY`.
- **Workaround:** Use a custom regex parser in the `DataTransformation` utility class.