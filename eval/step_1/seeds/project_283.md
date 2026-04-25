# PROJECT SPECIFICATION: PROJECT DELPHI
**Document Version:** 1.0.4  
**Status:** Active / High Priority  
**Last Updated:** 2025-10-20  
**Project Lead:** Kenji Costa (CTO)  
**Company:** Crosswind Labs  

---

## 1. EXECUTIVE SUMMARY

Project Delphi is a mission-critical data pipeline and analytics platform engineered specifically for the education sector. The platform is designed to aggregate, process, and analyze student performance and administrative data to ensure compliance with upcoming regional educational regulatory standards. Crosswind Labs is facing a hard legal deadline in six months; failure to deploy a compliant system by June 15, 2026, will result in significant statutory penalties and the potential loss of operating licenses in three primary jurisdictions.

The business justification for Delphi centers on the transition from manual, fragmented data reporting to a centralized, automated compliance engine. Currently, educational institutions utilizing Crosswind Labs' services spend thousands of man-hours manually compiling reports. Delphi aims to automate these workflows, reducing manual processing time by 50%. 

From a financial perspective, this is a high-visibility $3M investment. The ROI projection is based on three primary drivers:
1. **Risk Mitigation:** Avoiding fines that are estimated to exceed $1.2M per quarter in non-compliance penalties.
2. **Market Capture:** By being the first to offer a SOC 2 Type II compliant analytics suite in this niche, Crosswind Labs expects to capture an additional 15% of the regional market share within the first 12 months post-launch.
3. **Operational Efficiency:** The reduction in support tickets related to custom report requests is projected to save $200k annually in operational overhead.

The project is currently under extreme pressure. While the budget is substantial, the team size is lean (6 members), and the internal dynamics are strained. The critical path depends on the successful delivery of the Two-Factor Authentication (2FA) and PDF/CSV reporting modules, both of which are launch blockers. Failure to meet the June 15th deadline is not an option, necessitating a "war room" approach to development and a rigorous adherence to the milestones outlined in this specification.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Delphi utilizes a modern, decoupled architecture designed for scalability and independent deployment. The core backend is built on **Python 3.11** using the **FastAPI** framework for high-performance asynchronous API delivery. Data persistence is handled by **MongoDB 6.0**, chosen for its flexibility with evolving educational data schemas. Background processing and heavy-duty data pipeline tasks are managed by **Celery 5.3** with Redis as the message broker.

The frontend adopts a **Micro-Frontend (MFE)** architecture. This allows independent team ownership of specific modules (e.g., the Analytics Dashboard vs. the User Management console), reducing merge conflicts and allowing for independent deployment cycles.

### 2.2 Infrastructure
The system is **self-hosted** on dedicated bare-metal servers to ensure data sovereignty and compliance with education privacy laws. The environment is orchestrated via **Docker Compose**, ensuring parity between development and production.

### 2.3 Architecture Diagram (ASCII)

```text
[ Client Layer ]
       |
       v
[ Nginx Load Balancer ] <--- SSL Termination
       |
       +---------------------------------------+
       |               |                       |
 [ MFE: Dashboard ] [ MFE: Reporting ] [ MFE: Admin ]
       |               |                       |
       +-------------------+-------------------+
                               |
                               v
                     [ FastAPI Gateway ] (REST API)
                               |
       +-----------------------+-----------------------+
       |                       |                       |
 [ MongoDB Cluster ]    [ Redis Queue ]        [ External APIs ]
 (Multi-tenant Data)           |               (Edu-Data Sync)
                               v
                      [ Celery Workers ]
                      (PDF Gen / Data ETL)
                               |
                               v
                      [ S3 Local Storage ]
                      (Generated Reports)
```

### 2.4 Architectural Constraints
*   **Bus Factor:** The deployment process is currently manual and handled by a single DevOps engineer. This represents a critical single point of failure.
*   **Performance Gap:** The current system capacity is significantly below the required 10x load. Workarounds include aggressive Redis caching and the implementation of "read-only" replicas for MongoDB.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Blocked  
**Description:** To accommodate schools with unstable internet connectivity, Delphi must allow users to input data and navigate the platform without an active connection. All changes must be persisted locally and synchronized once connectivity is restored.

**Functional Requirements:**
- **Local Persistence:** Implementation of IndexedDB within the browser to store pending mutations.
- **Conflict Resolution:** A "Last-Write-Wins" strategy will be employed initially, though the system must track version timestamps for every record to allow for manual override if a conflict is detected.
- **Background Sync:** Integration of Service Workers to handle the synchronization process in the background, ensuring the user is notified upon successful upload.
- **State Management:** The frontend must transition between `ONLINE`, `SYNCING`, and `OFFLINE` states, visually indicating the status in the UI header.

**Technical Constraints:**
This feature is currently **Blocked** due to third-party API rate limits. The synchronization process triggers massive bursts of API calls that exceed the current quotas of the primary education data provider. Until the rate limits are increased or a batch-upload endpoint is developed, this feature cannot move to "In Progress."

### 3.2 Multi-Tenant Data Isolation with Shared Infrastructure
**Priority:** Medium | **Status:** Complete  
**Description:** Delphi must ensure that data from one educational institution is completely inaccessible to another, despite sharing the same MongoDB clusters and application servers.

**Functional Requirements:**
- **Tenant Identification:** Every request must include a `tenant_id` in the JWT payload.
- **Query Filtering:** All MongoDB queries must be appended with a tenant filter (e.g., `{ "tenant_id": request.tenant_id, ... }`).
- **Infrastructure Sharing:** To optimize costs, tenants share the same database instance, but are isolated at the document level.
- **Administrative Access:** A "Super-Admin" role exists for Crosswind Labs employees to provide support, requiring an explicit audit log entry every time a tenant's data is accessed.

**Implementation Detail:**
Isolation is enforced at the FastAPI middleware level. A `TenantContext` object is instantiated per request, ensuring that the developer cannot accidentally query data across tenants.

### 3.3 SSO Integration (SAML and OIDC)
**Priority:** High | **Status:** In Design  
**Description:** Enterprise educational clients require Single Sign-On (SSO) to manage users via their own identity providers (IdPs) like Azure AD, Okta, or Google Workspace.

**Functional Requirements:**
- **SAML 2.0 Support:** Support for Service Provider-Initiated (SP-Init) and Identity Provider-Initiated (IdP-Init) SSO flows.
- **OIDC Integration:** Implementation of OpenID Connect for modern cloud-based authentication.
- **User Provisioning:** Just-In-Time (JIT) provisioning to create user accounts upon their first successful SSO login.
- **Attribute Mapping:** A configurable mapping interface where admins can map IdP claims (e.g., `department`) to Delphi roles (e.g., `ReportViewer`).

**Design Specification:**
The system will use a dedicated `AuthService` micro-service to handle the handshake between the IdP and the Delphi platform, issuing a unified internal JWT upon successful authentication.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** In Progress  
**Description:** Due to the sensitive nature of student data and SOC 2 requirements, 2FA is mandatory for all administrative accounts.

**Functional Requirements:**
- **TOTP Support:** Integration with apps like Google Authenticator or Authy using time-based one-time passwords.
- **WebAuthn/FIDO2:** Full support for hardware security keys (e.g., YubiKey) to prevent phishing attacks.
- **Recovery Codes:** Generation of 10 one-time-use recovery codes upon 2FA setup.
- **Enforcement Policy:** Admins can mandate 2FA for specific user roles across the tenant.

**Critical Path:**
This is a launch blocker. The current implementation is in the "In Progress" stage, focusing on the WebAuthn handshake. Failure to complete this by the production launch will result in a SOC 2 compliance failure.

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** In Review  
**Description:** The core value proposition of Delphi is the ability to generate regulatory compliance reports in PDF and CSV formats and deliver them to stakeholders on a schedule.

**Functional Requirements:**
- **Dynamic Templating:** Use of Jinja2 and WeasyPrint to generate PDFs from HTML templates.
- **Asynchronous Generation:** Reports are processed by Celery workers to prevent API timeouts for large datasets.
- **Scheduling Engine:** A cron-like scheduler allowing users to send reports weekly, monthly, or quarterly.
- **Delivery Channels:** Integration with SMTP for email delivery and S3-compatible storage for downloadable archives.

**Review Notes:**
Currently "In Review." The QA team has identified a bug where CSV exports containing special characters (UTF-8) are improperly rendered in legacy versions of Excel. Fixes are required before the module can be marked "Complete."

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication requires a Bearer Token in the Header.

### 4.1 `POST /auth/login`
*   **Description:** Authenticates user and returns JWT.
*   **Request:** `{"email": "user@school.edu", "password": "password123"}`
*   **Response:** `{"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}`

### 4.2 `GET /tenant/settings`
*   **Description:** Retrieves the current tenant's configuration.
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response:** `{"tenant_id": "T-992", "name": "Springfield High", "compliance_level": "Gold"}`

### 4.3 `POST /reports/generate`
*   **Description:** Triggers an asynchronous report generation task.
*   **Request:** `{"report_type": "annual_compliance", "format": "pdf", "filters": {"year": 2025}}`
*   **Response:** `{"task_id": "celery-uuid-12345", "status": "queued"}`

### 4.4 `GET /reports/status/{task_id}`
*   **Description:** Polls the status of a report generation task.
*   **Request:** Path parameter `task_id`
*   **Response:** `{"status": "completed", "download_url": "https://s3.crosswind.io/reports/file.pdf"}`

### 4.5 `PUT /user/security/2fa/setup`
*   **Description:** Initiates the 2FA registration process.
*   **Request:** `{"method": "webauthn"}`
*   **Response:** `{"challenge": "base64_challenge_string", "userId": "user-123"}`

### 4.6 `GET /analytics/student-performance`
*   **Description:** Fetches aggregated performance metrics for the dashboard.
*   **Request:** Query params `?grade=10&subject=math`
*   **Response:** `{"p95_score": 82, "average_score": 74, "trend": "upward"}`

### 4.7 `POST /sync/push`
*   **Description:** Receives batches of offline data for synchronization.
*   **Request:** `{"batch_id": "b-101", "records": [{"id": "1", "data": "..."}, {"id": "2", "data": "..."}]}`
*   **Response:** `{"synced_count": 2, "conflicts": 0}`

### 4.8 `DELETE /admin/users/{user_id}`
*   **Description:** Removes a user from the tenant.
*   **Request:** Path parameter `user_id`
*   **Response:** `{"message": "User successfully deleted"}`

---

## 5. DATABASE SCHEMA

Delphi uses MongoDB. While schemaless, the following collections and implicit schemas are enforced via Pydantic models in the FastAPI layer.

### 5.1 Collections Overview

| Collection | Description | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | Org-level data | `_id` | `name, domain, plan_id, created_at` | One-to-Many with Users |
| `Users` | User accounts | `_id` | `email, password_hash, tenant_id, role` | Belongs to Tenant |
| `Students` | Student records | `_id` | `external_id, tenant_id, grade_level` | Belongs to Tenant |
| `PerformanceMetrics` | Time-series data | `_id` | `student_id, score, subject, timestamp` | Belongs to Student |
| `Reports` | Generated report metadata | `_id` | `tenant_id, type, s3_path, scheduled_date` | Belongs to Tenant |
| `Schedules` | Report delivery timing | `_id` | `tenant_id, report_type, cron_expression` | Belongs to Tenant |
| `AuthProviders` | SSO Configurations | `_id` | `tenant_id, provider_type, entity_id, cert` | Belongs to Tenant |
| `AuditLogs` | Compliance tracking | `_id` | `user_id, action, timestamp, ip_address` | Belongs to User |
| `TwoFactorSecrets` | 2FA keys | `_id` | `user_id, secret_key, method, is_verified` | Belongs to User |
| `Billing` | Subscription data | `_id` | `tenant_id, amount, billing_cycle, status` | Belongs to Tenant |

### 5.2 Key Relationships & Constraints
*   **Tenant Isolation:** Every single collection (except global system configs) contains a `tenant_id`. This is the primary shard key.
*   **Cascading Deletes:** When a `Tenant` is deleted, a Celery task is triggered to purge all associated `Users`, `Students`, and `Reports`.
*   **Indexing:** Compound indexes are placed on `{tenant_id, student_id}` for performance in the analytics engine.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi utilizes three distinct environments to ensure stability and compliance.

**1. Development (Dev)**
- **Purpose:** Feature iteration and unit testing.
- **Host:** Local developer machines and a shared "dev" server.
- **Data:** Mocked data; no real student PII.
- **Deployment:** Manual `docker-compose up --build`.

**2. Staging (Staging)**
- **Purpose:** QA, UAT, and SOC 2 pre-audit.
- **Host:** Dedicated staging server mirroring production hardware.
- **Data:** Anonymized production snapshots.
- **Deployment:** Manual deployment by the DevOps lead.

**3. Production (Prod)**
- **Purpose:** Live customer traffic.
- **Host:** High-availability bare-metal cluster.
- **Data:** Encrypted PII; strict access controls.
- **Deployment:** Manual deployment. **Critical Risk:** The "Bus Factor of 1" means only one person knows the deployment sequence and holds the SSH keys for the production environment.

### 6.2 Infrastructure Specifications
- **OS:** Ubuntu 22.04 LTS
- **Containerization:** Docker 24.0.0, Docker Compose 2.20.0
- **Network:** Private VLAN with a single entry point via Nginx Reverse Proxy.
- **Backup:** Nightly snapshots of MongoDB volumes backed up to an off-site encrypted glacier storage.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** Pytest.
- **Coverage Target:** 80% (Current: 40%).
- **Scope:** Business logic in FastAPI services and Celery tasks.
- **Note:** The **Core Billing Module** currently has **0% test coverage**. This is a significant piece of technical debt that was deployed under deadline pressure.

### 7.2 Integration Testing
- **Framework:** Pytest with `httpx` for API calls.
- **Scope:** Testing the interaction between FastAPI, MongoDB, and Redis.
- **Focus:** Ensuring that the `tenant_id` filter is applied to every single database call to prevent data leakage.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scope:** Critical user journeys (e.g., Login $\rightarrow$ Generate Report $\rightarrow$ Download PDF).
- **Frequency:** Run against Staging before every production release.

### 7.4 QA Process
Sanjay Kim (QA Lead) manages a dedicated QA flow. No feature is moved to "Complete" without a signed-off test report. However, due to the dysfunction between the PM and the Lead Engineer, bug reports are often ignored or disputed, leading to a bottleneck in the "In Review" stage.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead with a similar product. | High | Critical | **Parallel-Path:** Prototype an alternative, more aggressive feature set simultaneously with the core build. |
| R-02 | Performance requirements are 10x current capacity. | High | High | Document workarounds (caching, read-replicas) and share with the team; prioritize API optimization. |
| R-03 | Bus Factor of 1 (Deployment). | Medium | Critical | Document the deployment process in the internal Wiki; introduce a second person to the deployment rotation. |
| R-04 | SOC 2 Compliance Failure. | Low | Critical | Rigorous internal audits and prioritizing 2FA and Audit Logging. |
| R-05 | Technical Debt in Billing Module. | High | Medium | Schedule a "Debt Sprint" post-launch to implement retrospective tests. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal penalty.
- **High:** Significant delay or loss of revenue.
- **Medium:** Manageable impact with resource reallocation.

---

## 9. TIMELINE

### 9.1 Phase Breakdown

**Phase 1: Foundation (Completed)**
- Multi-tenant isolation.
- Basic API scaffolding.
- MongoDB Schema design.

**Phase 2: Core Compliance (Current - 2025-12 to 2026-03)**
- 2FA implementation (Critical Path).
- SSO Integration.
- Report Generation Engine.
- *Dependency:* SOC 2 audit preparation.

**Phase 3: Polishing & Beta (2026-03 to 2026-05)**
- Offline-first mode (pending API rate limit resolution).
- E2E testing.
- Beta onboarding for the first customer.

**Phase 4: Launch & Review (2026-06 to 2026-08)**
- Production cut-over.
- Post-launch stabilization.
- Final Architecture Review.

### 9.2 Key Milestones
- **Milestone 1:** First paying customer onboarded $\rightarrow$ **2026-04-15**
- **Milestone 2:** Production launch $\rightarrow$ **2026-06-15**
- **Milestone 3:** Architecture review complete $\rightarrow$ **2026-08-15**

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning (2025-11-05)
- 2FA is the priority.
- Kenji says "move faster."
- Sanjay reports PDFs are broken on Excel.
- Mosi mentions the frontend is lagging due to MFE complexity.
- *Decision:* Focus on 2FA first, then PDFs.

### Meeting 2: Emergency Sync (2025-12-12)
- API rate limits are killing the offline-sync tests.
- Mosi and Kenji arguing about state management.
- Paz says support tickets are increasing for the old system.
- *Decision:* Prototype a batch-upload endpoint to bypass rate limits.

### Meeting 3: Budget Review (2026-01-20)
- $3M budget is holding, but infrastructure costs are rising.
- No extra budget for more servers despite 10x load requirement.
- Kenji tells the team to "optimize the code instead of adding RAM."
- *Decision:* Implementation of Redis caching for all analytics endpoints.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$3,000,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 6 FTEs over 12 months (incl. QA and Support). |
| **Infrastructure** | 20% | $600,000 | Bare-metal servers, Redis managed service, S3 storage. |
| **Tools & Licenses** | 5% | $150,000 | MongoDB Enterprise, SOC 2 Audit fees, IDEs. |
| **Contingency** | 10% | $300,000 | Reserved for emergency scaling or legal consultants. |

---

## 12. APPENDICES

### Appendix A: SOC 2 Compliance Checklist
- [ ] **Access Control:** 2FA implemented for all admin accounts.
- [ ] **Audit Logging:** All data access logged with timestamp and user ID.
- [ ] **Data Encryption:** AES-256 encryption at rest; TLS 1.3 in transit.
- [ ] **Change Management:** Documented approval process for all production deployments.
- [ ] **Vendor Management:** Due diligence performed on all third-party API providers.

### Appendix B: Performance Workarounds for 10x Load
Due to the lack of additional infrastructure budget, the following software-level optimizations are mandated:
1. **Materialized Views:** Complex analytics queries will be pre-computed every hour and stored in a `MaterializedMetrics` collection.
2. **Aggressive Caching:** Use of Redis for any request with a TTL of 300 seconds for non-critical data.
3. **Pagination:** Strict enforcement of `limit` and `offset` on all API endpoints to prevent memory exhaustion.
4. **Lazy Loading:** Micro-frontends must only load assets when the user navigates to that specific module.