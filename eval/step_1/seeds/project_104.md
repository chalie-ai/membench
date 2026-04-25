Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity Project Specification Document. It is structured to serve as the "Single Source of Truth" for Tundra Analytics' development team.

***

# PROJECT MERIDIAN: COMPREHENSIVE PROJECT SPECIFICATION
**Document Version:** 1.0.4  
**Last Updated:** May 22, 2024  
**Status:** Approved / Active  
**Classification:** Confidential – Internal Use Only  
**Owner:** Juno Park (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Meridian represents a critical strategic pivot for Tundra Analytics. The current iteration of our customer-facing ML model deployment platform has suffered a catastrophic failure in user satisfaction, characterized by high churn rates, critical stability issues, and a perceived lack of security. User feedback indicates that the legacy system is unintuitive, prone to downtime, and fails to meet the rigorous compliance standards required by our enterprise telecommunications clients.

The telecommunications industry is currently undergoing a massive shift toward AI-driven network optimization and predictive churn modeling. To maintain market share, Tundra Analytics must provide a robust, scalable, and secure environment where clients can deploy their proprietary ML models into production environments without friction. The current "Legacy-Stack" is no longer viable; it is a monolithic structure that prevents rapid iteration and fails to support modern security protocols.

Project Meridian is not merely an update; it is a complete architectural rebuild. By transitioning to a Hexagonal Architecture (Ports and Adapters), we decouple the core business logic (the ML model orchestration) from the external infrastructure (database, API gateways, and UI). This allows the company to pivot its technology stack in the future without rewriting the core intellectual property.

### 1.2 ROI Projection and Financial Goals
The project is allocated a budget of $1.5M. This investment is justified by three primary financial levers:
1. **Reduction in Operational Overhead:** The legacy system requires constant manual intervention from the DevOps team to prevent crashes. We project a 35% reduction in cost per transaction by optimizing resource allocation and automating the deployment pipeline.
2. **Churn Mitigation:** Current customer attrition is estimated at 22% annually due to product dissatisfaction. Project Meridian aims to reduce this to <5% by delivering a modern, stable UX.
3. **Expanded Market Reach:** By achieving PCI DSS Level 1 compliance, Tundra Analytics can move into the financial-telecom crossover sector (mobile payments, billing infrastructure), opening a new revenue stream estimated at $2.2M in Year 1 post-launch.

### 1.3 Strategic Objectives
*   **Stability:** Eliminate the "God Class" dependencies that cause systemic failures.
*   **Security:** Implement hardware-backed 2FA and tamper-evident logging to satisfy regulatory audits.
*   **Scalability:** Enable the platform to handle a 10x increase in model deployments without linear increases in latency.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Project Meridian utilizes the Hexagonal Architecture (Ports and Adapters) pattern. The goal is to isolate the core domain logic from the external world. This is essential because we are inheriting three different legacy stacks (a Java-based backend, a Python-based ML execution engine, and a legacy Node.js frontend) that must interoperate seamlessly.

*   **The Core (Domain):** Contains the business logic for ML model versioning, deployment scheduling, and resource allocation. It has no knowledge of the database or the API.
*   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `IUserRepository`, `IModelDeployer`).
*   **Adapters:** The concrete implementations of the ports. For example, a `PostgresUserAdapter` implements the `IUserRepository` port to store data in a SQL database.

### 2.2 ASCII Architecture Diagram
```text
       [ External Clients ] <--- HTTPS/REST ---> [ API Adapter ]
                                                       |
                                                       v
   +-----------------------------------------------------------------------+
   |                           APPLICATION CORE                            |
   |                                                                       |
   |  +-----------------------+          +------------------------------+  |
   |  |   Model Orchestrator  | <------> |   Compliance & Audit Engine  |  |
   |  +-----------------------+          +------------------------------+  |
   |             ^                                      ^                 |
   |             |                                      |                 |
   |      [ Port: ModelRepo ]                    [ Port: AuditLog ]        |
   +-------------|--------------------------------------|-------------------+
                 |                                      |
                 v                                      v
   +----------------------------+        +---------------------------------+
   | [ Adapter: ML Execution ]   |        | [ Adapter: Tamper-Proof Store ]  |
   | (Python/Triton Inference)  |        | (Immutable Ledger/WORM Storage)  |
   +----------------------------+        +---------------------------------+
                 |                                      |
                 v                                      v
       [ GPU Cluster / K8s ]                    [ PCI Compliant Storage ]
```

### 2.3 Interoperability Strategy
The three inherited stacks will be integrated via a centralized Message Bus (RabbitMQ) and a shared API Gateway.
1.  **Legacy Stack A (Java/Spring):** Will be refactored into the "User Management" adapter.
2.  **Legacy Stack B (Python/FastAPI):** Will serve as the "Inference Engine" adapter.
3.  **Legacy Stack C (Node.js/React):** Will be completely rewritten as the frontend, interacting with the core via the API Gateway.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Requirement:** To meet PCI DSS Level 1 standards, the system must enforce multi-factor authentication (MFA) for all administrative and high-privilege user accounts.

**Functional Specifications:**
The system must support both software-based TOTP (Time-based One-Time Password) via apps like Google Authenticator and hardware-based authentication via FIDO2/WebAuthn (e.g., YubiKey). 
1.  **Enrollment Flow:** Users must be able to register multiple hardware keys. The system will generate a unique public key pair, storing the public key in the `UserSecurity` table and the private key on the device.
2.  **Challenge-Response:** During login, the server will send a random challenge. The hardware key signs this challenge and returns it. The server verifies the signature using the stored public key.
3.  **Recovery Codes:** Upon activation of 2FA, the system must generate ten 12-digit recovery codes, stored as bcrypt hashes.

**Technical Constraints:**
*   Must adhere to the WebAuthn API standard.
*   Session tokens must be invalidated immediately upon a 2FA failure.
*   Hardware key registration must occur over a TLS 1.3 encrypted connection.

**Acceptance Criteria:**
*   User cannot access the dashboard without successful 2FA verification.
*   Hardware key registration takes less than 30 seconds.
*   System correctly rejects expired TOTP codes.

---

### 3.2 Audit Trail Logging with Tamper-Evident Storage
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Review
*   **Requirement:** Every state-changing action within the system (model deployment, user permission change, data export) must be logged in a manner that prevents retrospective alteration.

**Functional Specifications:**
The audit log must capture the "Who, What, When, and Where" of every transaction.
1.  **Event Capture:** The `AuditInterceptor` adapter will capture the Request ID, User ID, Timestamp, Action Type, Old Value, and New Value.
2.  **Tamper-Evidence:** To prevent DB administrators from altering logs, each log entry will contain a cryptographic hash of the previous entry (a hash-chain).
3.  **Storage:** Logs will be written to a Write-Once-Read-Many (WORM) storage bucket in AWS S3, ensuring that once a log is written, it cannot be deleted or modified for 7 years (per regulatory requirements).
4.  **Alerting:** Any attempt to modify a log entry (detected via hash mismatch during daily integrity checks) must trigger an immediate P1 alert to the security team.

**Technical Constraints:**
*   Hashing algorithm: SHA-256.
*   Latency: Audit logging must be asynchronous to avoid blocking the main execution thread, but must guarantee "at-least-once" delivery via a persistent queue.

**Acceptance Criteria:**
*   A full audit trail can be reconstructed for any user action.
*   Manual database edits to the audit table are detectable within 24 hours.
*   Logs are stored in a non-rewriteable format.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
*   **Priority:** Medium
*   **Status:** Not Started
*   **Requirement:** Users need to manage thousands of ML models. A basic SQL `LIKE` query is insufficient. We require a professional search experience.

**Functional Specifications:**
1.  **Full-Text Search:** Implement an inverted index (via Elasticsearch) to allow users to search model descriptions, tags, and metadata.
2.  **Faceted Filtering:** Users must be able to drill down by:
    *   Model Version (v1, v2, v3...)
    *   Deployment Environment (Dev, Staging, Prod)
    *   Status (Active, Deprecated, Training)
    *   Owner (Lead Data Scientist, Analyst)
3.  **Query Suggestions:** Implement a "type-ahead" suggest feature that predicts model names based on the first three characters entered.

**Technical Constraints:**
*   Elasticsearch cluster must be synced with the primary PostgreSQL database via a Change Data Capture (CDC) pipeline.
*   Search latency must be under 200ms for 95% of queries.

**Acceptance Criteria:**
*   Search returns results based on keyword relevance.
*   Faceted filters update the result count in real-time.
*   Indexing of new models occurs within 5 seconds of creation.

---

### 3.4 Data Import/Export with Format Auto-Detection
*   **Priority:** Low (Nice to Have)
*   **Status:** In Design
*   **Requirement:** Simplify the onboarding of legacy ML datasets into the Meridian platform.

**Functional Specifications:**
1.  **Auto-Detection:** The system must analyze the first 1MB of an uploaded file to detect the format (CSV, JSON, Parquet, Avro).
2.  **Schema Mapping:** Upon detection, the system will propose a schema mapping. The user can then map "Source Column A" to "Target Field B".
3.  **Export Profiles:** Users can define "Export Profiles" (e.g., "Quarterly Regulatory Export") which automate the collection and formatting of specific model performance metrics.

**Technical Constraints:**
*   Maximum file size for browser upload: 500MB. Larger files must be uploaded via an S3 Signed URL.
*   Processing must occur in a background worker (Celery/Redis) to prevent request timeouts.

**Acceptance Criteria:**
*   System correctly identifies CSV vs. Parquet files 100% of the time.
*   Exported files match the requested format without data corruption.

---

### 3.5 Real-Time Collaborative Editing with Conflict Resolution
*   **Priority:** Low (Nice to Have)
*   **Status:** In Design
*   **Requirement:** Allow multiple data scientists to configure model hyperparameters and deployment schedules simultaneously.

**Functional Specifications:**
1.  **Operational Transformation (OT):** Implement an OT or CRDT (Conflict-free Replicated Data Type) mechanism to handle concurrent edits to the model configuration JSON.
2.  **Presence Indicators:** Show who is currently editing a specific configuration field (e.g., "Layla is editing Learning Rate...").
3.  **Conflict Resolution:** In the event of a hard collision, the system will prompt the user to "Keep Mine," "Keep Theirs," or "Merge Manually."

**Technical Constraints:**
*   Communication must happen over WebSockets for low latency.
*   State must be persisted every 5 seconds to avoid data loss during connection drops.

**Acceptance Criteria:**
*   Two users can edit the same field and see each other's changes in <100ms.
*   No data is lost during a simultaneous "Save" action.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/` and require a Bearer JWT token.

### 4.1 Authentication & Identity
**1. POST `/api/v1/auth/login`**
*   **Description:** Primary entry point for users.
*   **Request:** `{ "username": "jdoe", "password": "..." }`
*   **Response:** `200 OK { "token": "JWT_STR", "mfa_required": true, "mfa_type": "TOTP" }`

**2. POST `/api/v1/auth/mfa/verify`**
*   **Description:** Verifies the 2FA token or WebAuthn challenge.
*   **Request:** `{ "token": "123456", "session_id": "..." }`
*   **Response:** `200 OK { "access_token": "FINAL_JWT", "expires_in": 3600 }`

### 4.2 Model Management
**3. GET `/api/v1/models`**
*   **Description:** Retrieves a list of ML models with optional faceted filters.
*   **Request:** `?status=active&owner=juno&q=churn_prediction`
*   **Response:** `200 OK { "data": [ { "id": "mod_01", "name": "Churn v2", "status": "active" } ], "total": 1 }`

**4. POST `/api/v1/models/deploy`**
*   **Description:** Triggers the deployment of a model to a specific environment.
*   **Request:** `{ "model_id": "mod_01", "env": "production", "version": "2.4.1" }`
*   **Response:** `202 Accepted { "job_id": "job_abc123", "status": "queued" }`

### 4.3 Audit & Compliance
**5. GET `/api/v1/audit/logs`**
*   **Description:** Fetches the tamper-evident audit trail.
*   **Request:** `?start_date=2025-01-01&end_date=2025-01-31`
*   **Response:** `200 OK { "logs": [ { "timestamp": "...", "action": "USER_LOGIN", "hash": "0xABC..." } ] }`

**6. GET `/api/v1/audit/verify`**
*   **Description:** Checks the integrity of the hash chain for a specific date range.
*   **Request:** `?range=last_24h`
*   **Response:** `200 OK { "integrity": "verified", "checksum": "0xXYZ..." }`

### 4.4 User & System
**7. PATCH `/api/v1/user/profile`**
*   **Description:** Updates user settings and 2FA preferences.
*   **Request:** `{ "mfa_enabled": true, "hardware_key_id": "key_99" }`
*   **Response:** `200 OK { "status": "updated" }`

**8. GET `/api/v1/system/health`**
*   **Description:** Returns the status of the inherited stacks (Java, Python, Node).
*   **Request:** `N/A`
*   **Response:** `200 OK { "status": "healthy", "components": { "inference_engine": "up", "db": "up", "gateway": "up" } }`

---

## 5. DATABASE SCHEMA

The system utilizes PostgreSQL 15 for relational data and AWS S3 for immutable log storage.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role` | Core user identity. |
| `user_security` | `sec_id` | `user_id` | `mfa_secret`, `hardware_key_pub`, `is_mfa_enabled` | 2FA and WebAuthn keys. |
| `models` | `model_id` | `creator_id` | `name`, `description`, `current_version` | ML model metadata. |
| `model_versions` | `ver_id` | `model_id` | `version_string`, `s3_path`, `checksum` | Specific iterations of models. |
| `deployments` | `deploy_id` | `ver_id` | `env_id`, `deployed_at`, `status` | Deployment history. |
| `environments` | `env_id` | None | `env_name` (Dev/Staging/Prod), `region` | Infrastructure targets. |
| `audit_logs` | `log_id` | `user_id` | `action`, `prev_hash`, `curr_hash`, `timestamp` | Tamper-evident event log. |
| `facets` | `facet_id` | None | `category`, `label` | Search categories for filtering. |
| `model_facets` | `map_id` | `model_id`, `facet_id` | `assigned_at` | Mapping models to search facets. |
| `recovery_codes` | `code_id` | `user_id` | `hashed_code`, `is_used` | 2FA backup codes. |

### 5.2 Key Relationships
*   **One-to-One:** `users` $\rightarrow$ `user_security`. Each user has exactly one security profile.
*   **One-to-Many:** `models` $\rightarrow$ `model_versions`. A model can have infinite versions.
*   **Many-to-Many:** `models` $\leftrightarrow$ `facets` via `model_facets`. Models can have multiple tags, and tags can belong to many models.
*   **One-to-Many:** `users` $\rightarrow$ `audit_logs`. One user generates many log entries.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Meridian employs a three-tier environment strategy to ensure stability and PCI compliance.

**1. Development (DEV)**
*   **Purpose:** Rapid iteration and unit testing.
*   **Infrastructure:** Ephemeral Kubernetes namespaces in AWS.
*   **Data:** Mocked data or anonymized subsets of production data.
*   **Deployment:** Continuous Integration (CI) triggers on every git push.

**2. Staging (STAGING)**
*   **Purpose:** QA, User Acceptance Testing (UAT), and Beta testing.
*   **Infrastructure:** Mirrors Production exactly (Blue/Green deployment).
*   **Data:** Sanitized production clones.
*   **Deployment:** Weekly releases. This is where the 10 pilot users (Milestone 2) will operate.

**3. Production (PROD)**
*   **Purpose:** Customer-facing live environment.
*   **Infrastructure:** Multi-region AWS clusters with high availability (HA) and PCI DSS Level 1 isolation.
*   **Data:** Live customer data.
*   **Deployment:** Quarterly releases. Every release must be signed off by the Regulatory Review Board.

### 6.2 CI/CD Pipeline
*   **Tooling:** Jenkins for orchestration, Docker for containerization, Helm for K8s management.
*   **Gatekeeping:** Code cannot move from Staging to Prod without a successful "Security Scan" (Snyk) and "QA Sign-off" (Yuki Park).
*   **Rollback:** Automated rollback to the previous stable version if the error rate exceeds 1% in the first hour post-launch.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Scope:** Individual functions and domain logic.
*   **Target:** 80% code coverage.
*   **Approach:** Using JUnit (Java), PyTest (Python), and Jest (React). All unit tests must run in the CI pipeline.

### 7.2 Integration Testing
*   **Scope:** Interaction between adapters and the core, and between different stacks.
*   **Target:** All API endpoints and database transactions.
*   **Approach:** Postman collections integrated into Jenkins. Focus on "Happy Path" and "Edge Case" (e.g., what happens if the Python inference engine is down but the Java backend is up?).

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Complete user journeys (e.g., Login $\rightarrow$ Upload Model $\rightarrow$ Deploy $\rightarrow$ Verify Audit Log).
*   **Target:** Critical paths (2FA, Model Deployment).
*   **Approach:** Cypress.io scripts running against the Staging environment.

### 7.4 Compliance Testing (PCI DSS)
*   **Approach:** Third-party penetration testing and internal audit of the `audit_logs` hash-chain.
*   **Frequency:** Monthly during the build phase; quarterly once in production.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Hexagonal Architecture | High | Medium | Hire a specialized contractor for the first 3 months to mentor the team and review architecture. |
| R-02 | Key Architect leaving in 3 months | Medium | High | Mandatory "Knowledge Transfer" (KT) sessions every Friday; all architectural decisions must be documented in Confluence. |
| R-03 | PCI DSS Level 1 Audit failure | Low | Critical | Weekly compliance reviews with Yuki Park and an external auditor. |
| R-04 | Integration failure between the 3 legacy stacks | High | High | Implement a strict API Contract (OpenAPI/Swagger) that all teams must adhere to. |
| R-05 | Dependency on the 'God Class' causing delays | High | Medium | Incremental refactoring: wrap the God Class in an adapter and slowly move methods to the core. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project halt.
*   **High:** Potential milestone delay.
*   **Medium:** Requires management attention but not a blocker.
*   **Low:** Manageable via standard processes.

---

## 9. TIMELINE AND MILESTONES

The project follows a gated release cycle. Dependencies are marked to show critical paths.

### 9.1 Phase 1: Foundation & Refactoring (May 2024 – August 2024)
*   **Objective:** Break down the "God Class" and establish the Hexagonal Core.
*   **Key Activities:**
    *   Set up K8s environments (Dev/Staging).
    *   Implement the `IUserRepository` and `IModelRepo` ports.
    *   Contractor onboarding for architecture guidance.
*   **Dependency:** Completion of the API Contract.

### 9.2 Phase 2: Security & Compliance (August 2024 – October 2024)
*   **Objective:** Deliver the launch blockers (2FA and Audit Logging).
*   **Key Activities:**
    *   Develop WebAuthn hardware key support.
    *   Implement the hash-chained audit log and WORM storage.
    *   Internal security audit.
*   **Dependency:** Stable User Management module from Phase 1.
*   **MILESTONE 1:** Stakeholder demo and sign-off (Target: 2025-08-15).

### 9.3 Phase 3: Beta & Optimization (October 2024 – December 2024)
*   **Objective:** External validation and performance tuning.
*   **Key Activities:**
    *   Deploy to the 10 pilot users.
    *   Implement Advanced Search and Faceted Filtering.
    *   Performance tuning of the Python inference engine.
*   **Dependency:** Milestone 1 Approval.
*   **MILESTONE 2:** External beta with 10 pilot users (Target: 2025-10-15).

### 9.4 Phase 4: Production Hardening (December 2024 – January 2025)
*   **Objective:** Final regulatory review and global rollout.
*   **Key Activities:**
    *   Full PCI DSS Level 1 certification.
    *   Final load testing.
    *   Production cut-over.
*   **MILESTONE 3:** Production launch (Target: 2025-12-15).

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment
**Date:** June 5, 2024  
**Attendees:** Juno Park, Layla Costa, Yuki Park, Darian Oduya  
**Discussion:**
*   **Juno** expressed concern that the 3,000-line 'God Class' is the single biggest point of failure.
*   **Layla** argued that trying to delete the God Class entirely would be too risky. She proposed "The Strangler Pattern": wrapping the class in a Port/Adapter and slowly migrating functionality.
*   **Yuki** reminded the team that if the God Class handles authentication, any change to it must be regression-tested for 48 hours.
*   **Decision:** The team agreed to use the Strangler Pattern. No new features will be added to the God Class.

**Action Items:**
*   `Layla Costa`: Draft the initial `IAuthPort` interface. (Due: June 12)
*   `Darian Oduya`: Document all current "God Class" dependencies for the knowledge base. (Due: June 15)

---

### Meeting 2: 2FA and Hardware Key Strategy
**Date:** July 12, 2024  
**Attendees:** Juno Park, Layla Costa, Yuki Park  
**Discussion:**
*   **Yuki** noted that simply using SMS for 2FA is not sufficient for PCI DSS Level 1.
*   **Layla** proposed using WebAuthn for YubiKey support.
*   **Juno** questioned the cost of providing hardware keys to users.
*   **Decision:** Tundra Analytics will not provide the keys; instead, the software will support *BYOK* (Bring Your Own Key), but must provide a fallback TOTP option.

**Action Items:**
*   `Layla Costa`: Research WebAuthn library compatibility with the legacy Java stack. (Due: July 19)
*   `Yuki Park`: Create the compliance checklist for 2FA verification. (Due: July 20)

---

### Meeting 3: Emergency Resource Planning
**Date:** August 2, 2024  
**Attendees:** Juno Park, Layla Costa, Yuki Park, Darian Oduya  
**Discussion:**
*   **Current Blocker:** A key developer (not listed in the core 4) is on medical leave for 6 weeks.
*   **Impact:** This has stalled the "Advanced Search" feature and the "Data Import" design.
*   **Juno** decided that "Advanced Search" will be pushed back to Phase 3 to prioritize the 2FA launch blocker.
*   **Layla** suggested that the contractor hired for architecture could help fill the gap in the search implementation.

**Action Items:**
*   `Juno Park`: Reallocate $20k from the contingency budget to increase contractor hours. (Due: Aug 4)
*   `Yuki Park`: Update the QA plan to reflect the delayed Search feature. (Due: Aug 7)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $850,000 | Salaries for 12-person cross-functional team (approx. 1 year). |
| **Contractor Fees** | $120,000 | Specialist architecture consultant for Hexagonal implementation. |
| **Infrastructure (AWS)** | $210,000 | K8s clusters, WORM storage, RDS, and Elasticsearch instances. |
| **Security Tooling** | $80,000 | Snyk, PCI Compliance auditing software, and Pentesting. |
| **Software Licenses** | $40,000 | JIRA, Confluence, Datadog, and IDE licenses. |
| **Contingency Fund** | $200,000 | For medical leave coverage, emergency hardware, and scope creep. |

**Financial Note:** All expenditures must be approved by Juno Park via JIRA ticket and linked to a specific Milestone.

---

## 12. APPENDICES

### Appendix A: The "God Class" Decomposition Map
The `GlobalManager` class currently handles:
1.  `processLogin()` $\rightarrow$ Move to `AuthService` (Core)
2.  `writeLog()` $\rightarrow$ Move to `AuditAdapter` (Adapter)
3.  `sendEmail()` $\rightarrow$ Move to `NotificationPort` (Port)
4.  `validateCC()` $\rightarrow$ Move to `PaymentGateway` (Adapter)
5.  `fetchUser()` $\rightarrow$ Move to `UserRepository` (Adapter)

The transition plan involves creating "Proxy Methods" in the `GlobalManager` that simply call the new services. Once all calls are routed, the `GlobalManager` will be deleted.

### Appendix B: PCI DSS Level 1 Requirements Matrix
For Project Meridian to be compliant, the following must be verified:
*   **Requirement 3:** Protect stored cardholder data. (Handled by encryption-at-rest in RDS).
*   **Requirement 7:** Restrict access to cardholder data by business need-to-know. (Handled by Role-Based Access Control - RBAC).
*   **Requirement 10:** Track and monitor all access to network resources and cardholder data. (Handled by the Tamper-Evident Audit Log).
*   **Requirement 12:** Maintain a policy that addresses information security. (Handled by the Project Specification and quarterly reviews).