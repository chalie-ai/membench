# PROJECT SPECIFICATION DOCUMENT: PROJECT ECLIPSE
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Document Owner:** Uma Moreau (Engineering Manager)  
**Company:** Verdant Labs  
**Confidentiality Level:** Restricted (HIPAA Compliant)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Eclipse" is a specialized healthcare records platform developed by Verdant Labs. While Verdant Labs operates primarily within the telecommunications industry, Eclipse was conceived as an internal productivity tool to manage the complex intersection of health data and telecommunications infrastructure (e.g., managing health-related connectivity for remote clinics and emergency services). What began as a rapid-prototype hackathon project has evolved into a mission-critical utility currently serving 500 daily active users (DAU).

The platform is designed to bridge the gap between legacy telecommunications record-keeping and modern healthcare data standards. It serves as a centralized hub for record management, auditing, and collaboration, ensuring that internal staff can manage patient-related infrastructure data without compromising security or regulatory compliance.

### 1.2 Business Justification
The primary driver for Eclipse is the reduction of operational inefficiency. Currently, the process of managing healthcare-related records within the telecommunications framework is manual, fragmented across disparate spreadsheets, and prone to human error. This inefficiency results in delayed service deployments and increased risk of compliance breaches.

By transitioning from a "hackathon" codebase to a formal, engineered platform, Verdant Labs aims to institutionalize the knowledge currently trapped in the tool’s early adopters. The business justification rests on three pillars:
1.  **Regulatory Necessity:** Transitioning to a fully HIPAA-compliant architecture to avoid catastrophic legal liabilities.
2.  **Operational Scalability:** Moving from 500 users to a potential organization-wide rollout.
3.  **Risk Mitigation:** Resolving the "bus factor" and technical debt associated with the project's rapid, informal origin.

### 1.3 ROI Projection
The budget for Eclipse is strictly capped at $150,000. Given the "shoestring" nature of this funding, the ROI is calculated based on labor hours reclaimed and risk avoidance.

**Projected Annual Gains:**
*   **Labor Reduction:** An estimated 50% reduction in manual processing time for end users. Based on 500 users spending an average of 4 hours per week on manual record reconciliation, this equates to 100,000 man-hours saved per year. At an average internal cost of $45/hour, the gross productivity gain is $4.5M.
*   **Compliance Savings:** Avoiding a single HIPAA violation (which can range from $100 to $50,000 per record) justifies the $150k investment immediately.
*   **NPS Improvement:** Target NPS of >40. Higher internal satisfaction correlates with a 15% reduction in staff turnover within the operational departments.

**Total Projected 12-Month ROI:** $\approx 3,000\%$ based on productivity gains vs. initial capital expenditure.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Stack
Eclipse utilizes a modern, asynchronous stack designed for high throughput and strict auditability.

*   **Backend:** Python 3.11 / FastAPI. Chosen for its native support for asynchronous I/O and automatic OpenAPI generation.
*   **Primary Database:** MongoDB 6.0 (Community Edition). Used for the flexible schema required by diverse healthcare record types.
*   **Task Queue:** Celery 5.3 with Redis as the broker. Handles heavy report generation and data synchronization.
*   **Containerization:** Docker Compose for orchestration.
*   **Hosting:** Self-hosted on Verdant Labs’ private cloud infrastructure to maintain total control over data residency.

### 2.2 Architectural Pattern: CQRS & Event Sourcing
To meet HIPAA audit requirements, Eclipse employs Command Query Responsibility Segregation (CQRS) with Event Sourcing for audit-critical domains (e.g., Patient Record Modification).

*   **Command Side:** Handles writes. Every change to a record is stored as an immutable event in the `EventStore` collection.
*   **Query Side:** Materialized views are maintained in MongoDB for fast read access.
*   **Event Store:** A sequential log of every change, ensuring that any record state can be reconstructed at any point in time for auditors.

### 2.3 Architecture Diagram (ASCII)

```text
[ Client Layer ] <---- HTTPS/TLS 1.3 ----> [ FastAPI Gateway ]
                                                 |
                                                 v
        __________________________________________/ \__________________________________________
       |                                                                                        |
 [ Command Side (Write) ]                                                     [ Query Side (Read) ]
       |                                                                                        |
       v                                                                                        v
 [ Validation Logic ]  ---> [ Event Store (MongoDB) ] ---> [ Projector/Worker ] ---> [ Read Models ]
       |                                                            ^                           |
       |                                                            |                           |
       +------> [ Celery Worker ] ----------------------------------+                           |
                      |                                                                         |
                      v                                                                         v
              [ External APIs / SAML ]                                                 [ User Dashboard ]
```

### 2.4 Security Posture
HIPAA compliance is the baseline.
*   **Encryption at Rest:** AES-256 encryption for all MongoDB volumes.
*   **Encryption in Transit:** TLS 1.3 enforced for all endpoints.
*   **Access Control:** Attribute-Based Access Control (ABAC) integrated with the OIDC provider.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Description:** Users must be able to edit healthcare records simultaneously without overwriting changes. Given the sensitivity of healthcare data, "last-write-wins" is unacceptable.
*   **Technical Approach:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs). The team is leaning toward a Yjs-based CRDT implementation integrated via WebSockets.
*   **Requirements:**
    *   **Cursor Tracking:** Users must see the presence and cursor location of other active editors.
    *   **Versioning:** Every "session" of collaboration must be snapshotted.
    *   **Conflict Resolution:** Logical clocks (Lamport timestamps) will be used to order operations. If two users edit the same field, the system will merge the changes based on the CRDT ruleset.
    *   **Locking Mechanism:** Fine-grained field-level locking to prevent conflicting edits on critical medical IDs.
*   **Acceptance Criteria:** Two users editing the same document simultaneously must see identical final states within 200ms of the last edit.

### 3.2 Localization and Internationalization (L10n/I18n)
*   **Priority:** Medium
*   **Status:** Complete
*   **Description:** The platform supports 12 languages to accommodate Verdant Labs' global workforce.
*   **Technical Approach:** Implementation of `gettext` for Python and a JSON-based translation mapping for the frontend.
*   **Scope:**
    *   **Languages:** English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Italian, Arabic, Russian, and Hindi.
    *   **Dynamic Formatting:** Date, time, and currency formatting are handled via the `Babel` library to ensure regional accuracy.
    *   **Right-to-Left (RTL) Support:** CSS mirrors for Arabic and Hebrew layouts.
*   **Verification:** All UI strings were extracted to `.po` files and verified by native speakers in the respective regions.

### 3.3 SSO Integration with SAML and OIDC
*   **Priority:** Medium
*   **Status:** In Design
*   **Description:** Transition from local user management to enterprise-grade Single Sign-On (SSO) to ensure centralized identity management and immediate offboarding.
*   **Technical Approach:** Using `python-saml` for SAML 2.0 and `authlib` for OIDC.
*   **Requirements:**
    *   **Provider Support:** Must support Azure AD, Okta, and Ping Identity.
    *   **Just-in-Time (JIT) Provisioning:** Users not in the Eclipse database should be created upon their first successful SSO login, provided they have the required group membership.
    *   **Token Lifecycle:** JWTs (JSON Web Tokens) will have a short lifespan (15 minutes) with a secure refresh token rotation policy.
*   **Security:** All callback URLs must be whitelisted and use HTTPS.

### 3.4 Automated Billing and Subscription Management
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Review
*   **Description:** While internal, the tool requires a cost-recovery model where different departments are billed based on their seat count and data storage usage.
*   **Technical Approach:** Integration with an internal ERP system via a custom Celery task that aggregates usage metrics monthly.
*   **Requirements:**
    *   **Tiered Pricing:** Basic, Professional, and Enterprise tiers based on record volume.
    *   **Automatic Invoicing:** Generation of PDF invoices on the 1st of every month.
    *   **Usage Tracking:** MongoDB aggregation pipelines will calculate total documents per `tenant_id` every 24 hours.
    *   **Grace Periods:** 15-day grace period for departments with expired funding before "Read-Only" mode is triggered.
*   **Acceptance Criteria:** Successful generation of a billing report for 10 simulated departments with varying usage levels.

### 3.5 Multi-tenant Data Isolation with Shared Infrastructure
*   **Priority:** Medium
*   **Status:** Blocked
*   **Description:** The system must ensure that data from one department/tenant is logically invisible to another, despite sharing the same MongoDB cluster.
*   **Technical Approach:** "Logical Isolation" using a `tenant_id` shard key on every document.
*   **Requirements:**
    *   **Middleware Enforcement:** A FastAPI dependency must be implemented to inject the `tenant_id` from the JWT into every database query.
    *   **Query Guardrails:** No query is allowed to execute without a `tenant_id` filter.
    *   **Encryption:** Tenant-specific encryption keys managed via a Key Management Service (KMS).
*   **Blocker Reason:** Currently waiting on the Security Audit team to approve the key rotation policy for the KMS.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 GET `/records/{record_id}`
*   **Description:** Retrieve a specific healthcare record.
*   **Request Headers:** `Authorization: Bearer <token>`
*   **Response (200 OK):**
    ```json
    {
      "record_id": "REC-99283",
      "patient_name": "John Doe",
      "data": { "blood_type": "O+", "last_visit": "2023-10-01" },
      "version": 12,
      "tenant_id": "DEPT-TELCO-01"
    }
    ```

### 4.2 POST `/records/update`
*   **Description:** Submit a change to a record (Command side of CQRS).
*   **Request Body:**
    ```json
    {
      "record_id": "REC-99283",
      "updates": { "last_visit": "2023-11-15" },
      "change_reason": "Annual checkup"
    }
    ```
*   **Response (202 Accepted):** `{"status": "event_queued", "event_id": "evt_abc123"}`

### 4.3 GET `/auth/sso/login`
*   **Description:** Initiate SAML/OIDC handshake.
*   **Response (302 Redirect):** Redirects user to the configured Identity Provider (IdP).

### 4.4 POST `/billing/calculate`
*   **Description:** Trigger a manual billing calculation for a specific tenant.
*   **Request Body:** `{"tenant_id": "DEPT-TELCO-01", "period": "2023-Q3"}`
*   **Response (200 OK):** `{"total_amount": 1250.00, "currency": "USD"}`

### 4.5 GET `/audit/logs/{record_id}`
*   **Description:** Retrieve the full event history for a record.
*   **Response (200 OK):**
    ```json
    [
      {"timestamp": "2023-01-01T10:00Z", "user": "Umi K.", "action": "create"},
      {"timestamp": "2023-05-12T14:20Z", "user": "Ines K.", "action": "update_field_blood_type"}
    ]
    ```

### 4.6 PUT `/settings/localization`
*   **Description:** Update user language preferences.
*   **Request Body:** `{"language_code": "fr-FR", "timezone": "Europe/Paris"}`
*   **Response (200 OK):** `{"status": "updated"}`

### 4.7 GET `/health/status`
*   **Description:** System heartbeat and dependency check.
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "dependencies": { "mongodb": "up", "redis": "up", "celery": "up" }
    }
    ```

### 4.8 POST `/admin/tenant/create`
*   **Description:** Provision a new tenant environment.
*   **Request Body:** `{"tenant_name": "Nordic Ops", "admin_email": "admin@nordic.com"}`
*   **Response (201 Created):** `{"tenant_id": "DEPT-NORDIC-05"}`

---

## 5. DATABASE SCHEMA

The system uses MongoDB. While schemaless, the following logical collections and fields are enforced by Pydantic models in the FastAPI layer.

### 5.1 Collection: `Patients`
*   **_id:** ObjectId (PK)
*   **patient_uuid:** UUID (Unique Index)
*   **tenant_id:** String (Indexed) - For multi-tenancy isolation.
*   **demographics:** Object `{ name, dob, gender, contact }`
*   **created_at:** Timestamp
*   **updated_at:** Timestamp

### 5.2 Collection: `Records`
*   **_id:** ObjectId (PK)
*   **patient_uuid:** UUID (FK $\rightarrow$ Patients)
*   **tenant_id:** String (Indexed)
*   **clinical_data:** Object (Dynamic schema for health metrics)
*   **version:** Integer (For optimistic locking)
*   **last_modified_by:** UserID

### 5.3 Collection: `EventStore` (The Event Sourcing Log)
*   **_id:** ObjectId (PK)
*   **aggregate_id:** UUID (Reference to the Record/Patient)
*   **event_type:** String (e.g., "RECORD_UPDATED", "SENSITIVE_FIELD_ACCESSED")
*   **payload:** Object (The diff of the change)
*   **timestamp:** Timestamp (High precision)
*   **user_id:** UserID
*   **correlation_id:** UUID (To track the request across services)

### 5.4 Collection: `Users`
*   **_id:** ObjectId (PK)
*   **email:** String (Unique Index)
*   **hashed_password:** String (Only for non-SSO users)
*   **sso_provider_id:** String (External ID from Okta/Azure)
*   **role:** Enum (Admin, Doctor, Support, Auditor)
*   **tenant_id:** String (Indexed)

### 5.5 Collection: `Tenants`
*   **_id:** ObjectId (PK)
*   **tenant_name:** String
*   **subscription_plan:** String (Basic, Pro, Enterprise)
*   **billing_email:** String
*   **status:** Enum (Active, Suspended, Pending)

### 5.6 Collection: `Subscriptions`
*   **_id:** ObjectId (PK)
*   **tenant_id:** ObjectId (FK $\rightarrow$ Tenants)
*   **start_date:** Date
*   **end_date:** Date
*   **auto_renew:** Boolean

### 5.7 Collection: `BillingInvoices`
*   **_id:** ObjectId (PK)
*   **tenant_id:** ObjectId (FK $\rightarrow$ Tenants)
*   **amount:** Decimal
*   **invoice_date:** Date
*   **payment_status:** Enum (Unpaid, Paid, Overdue)

### 5.8 Collection: `AuditLogs` (General System Logs)
*   **_id:** ObjectId (PK)
*   **action:** String
*   **timestamp:** Timestamp
*   **ip_address:** String
*   **user_agent:** String

### 5.9 Collection: `Localizations`
*   **_id:** ObjectId (PK)
*   **language_code:** String (e.g., "en-US")
*   **translation_bundle:** Object (Key-value pairs for UI strings)

### 5.10 Collection: `SessionCache` (Backed by Redis, mirrored in Mongo for auditing)
*   **session_id:** String (PK)
*   **user_id:** UserID
*   **expires_at:** Timestamp
*   **mfa_verified:** Boolean

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Overview
Eclipse is self-hosted on Verdant Labs' private cloud. There is currently a critical "bus factor" of 1, as a single DevOps engineer manages all deployments.

### 6.2 Environment Specifications

| Environment | Purpose | Infrastructure | Database | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | Feature build & local testing | Local Docker Desktop | Mongo (Local) | `docker-compose up` |
| **Staging** | QA and Integration testing | K8s Namespace (Small) | Mongo (Staging Cluster) | Manual Git trigger |
| **Production** | End-user access (500 users) | K8s Cluster (High Avail) | Mongo (Atlas-like Private) | Manual SSH/Script |

### 6.3 Deployment Pipeline
The current CI pipeline is a significant source of technical debt.
*   **Pipeline Duration:** 45 minutes.
*   **Bottlenecks:** Sequential execution of the full E2E test suite and lack of Docker layer caching.
*   **Deployment Flow:** 
    1. Code push to `main` $\rightarrow$ 2. Jenkins build $\rightarrow$ 3. Unit Tests $\rightarrow$ 4. Integration Tests $\rightarrow$ 5. Manual approval $\rightarrow$ 6. Manual deployment by DevOps.

### 6.4 Resource Allocation
*   **CPU:** 4 vCPUs (Production)
*   **RAM:** 16GB (Production)
*   **Storage:** SSDs with RAID 10 for MongoDB data volumes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** `pytest`
*   **Coverage Goal:** 80% of business logic.
*   **Focus:** Validation logic, CRDT merge functions, and billing calculation formulas.
*   **Execution:** Every commit in the CI pipeline.

### 7.2 Integration Testing
*   **Focus:** API endpoint connectivity, MongoDB query performance, and Celery task completion.
*   **Approach:** Using `TestClient` from FastAPI to simulate HTTP requests against a temporary Dockerized MongoDB instance.
*   **Execution:** Triggered on merge requests to `develop` branch.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Focus:** Critical user paths (e.g., "Login $\rightarrow$ Open Record $\rightarrow$ Edit Record $\rightarrow$ Save").
*   **Execution:** Weekly on the Staging environment. This is currently the primary cause of the 45-minute pipeline delay.

### 7.4 Security Testing
*   **Penetration Testing:** Annual external audit.
*   **Static Analysis:** `Bandit` for Python security linting.
*   **Compliance Check:** Monthly automated scan for HIPAA-sensitive data in non-encrypted fields.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor dependency announced EOL (End-of-Life) | High | Critical | Hire a specialized contractor to migrate functionality and reduce the bus factor. |
| R-02 | Team lacks experience with FastAPI/MongoDB/CRDTs | Medium | High | De-scope non-essential features if milestones are missed; provide training budget. |
| R-03 | Single point of failure in DevOps (Bus Factor 1) | High | Critical | Document all deployment scripts; cross-train Uma Moreau on basic K8s management. |
| R-04 | CI Pipeline inefficiency (45 min) | High | Low | Implement parallel test execution and Docker layer caching. |
| R-05 | Multi-tenant leakage (Security Breach) | Low | Catastrophic | Implement strict middleware query filters and conduct a 3rd party security audit. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project halt or legal action.
*   **High:** Significant delay or budget overrun.
*   **Medium:** Manageable impact on timeline.
*   **Low:** Minor annoyance/technical debt.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases

**Phase 1: Stabilization (Current $\rightarrow$ July 2026)**
*   Focus on converting the "hackathon" code into a production-ready state.
*   Implement the billing system and finalize the collaborative editing design.
*   **Dependency:** Design approval for CRDTs.

**Phase 2: Security & Compliance (July 2026 $\rightarrow$ Sept 2026)**
*   Focus on HIPAA hardening, SSO integration, and the security audit.
*   **Dependency:** Completion of the SSO design phase.

**Phase 3: Feature Completion (Sept 2026 $\rightarrow$ Nov 2026)**
*   Finalizing multi-tenant isolation and polishing the UI.
*   Final performance tuning of the 45-minute CI pipeline.

### 9.2 Milestone Dates

| Milestone | Target Date | Success Criteria |
| :--- | :--- | :--- |
| **Milestone 1: Internal Alpha** | 2026-07-15 | 500 users can use the tool without critical crashes. |
| **Milestone 2: Security Audit** | 2026-09-15 | 100% of "High" severity findings resolved; HIPAA sign-off. |
| **Milestone 3: MVP Complete** | 2026-11-15 | All 5 features implemented; NPS $> 40$ in alpha. |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-05)
*   **Attendees:** Uma, Umi, Ines
*   **Notes:**
    *   CRDTs too complex?
    *   Yjs suggested.
    *   Event sourcing for records—yes.
    *   Mongo for everything.
    *   Action: Umi to prototype Yjs.

### Meeting 2: Budget Review (2023-11-12)
*   **Attendees:** Uma, Finance Dept
*   **Notes:**
    *   $150k total.
    *   No more headcount.
    *   Contractor for EOL vendor issue?
    *   Approved if within the $150k.
    *   Everything scrutinized.

### Meeting 3: Pipeline Frustration (2023-11-19)
*   **Attendees:** Uma, Ines, Hana
*   **Notes:**
    *   45 min wait for CI.
    *   Ines says E2E is the problem.
    *   Hana says manual deploys are slow.
    *   DevOps person is overwhelmed.
    *   Decided: Put "Parallelize Tests" in the backlog for Q1 2026.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Core team salaries/stipends and project management. |
| **Infrastructure** | 15% | $22,500 | Private cloud hosting, MongoDB licenses, Redis instance. |
| **External Contractor** | 15% | $22,500 | Mitigation of Risk R-01 (EOL Vendor) and R-03 (Bus Factor). |
| **Tools & Licensing** | 5% | $7,500 | SAML/OIDC provider fees, security scanning tools. |
| **Contingency** | 5% | $7,500 | Emergency fixes and critical hardware failures. |

*Note: Every single expenditure must be approved by Uma Moreau and the Finance department via the "Shoestring Procurement" process.*

---

## 12. APPENDICES

### Appendix A: CRDT Operational Logic
For the collaborative editing feature, the system implements a **Last-Write-Wins (LWW) Element Set** for simple fields and a **Sequence CRDT** for text blocks. 
1.  **Update Event:** When a user types, a `delta` is created containing the operation, a timestamp, and a unique client ID.
2.  **Propagation:** The delta is broadcast via WebSockets to all active clients.
3.  **Integration:** The receiving client integrates the delta into its local state. If timestamps conflict, the client ID with the higher alphanumeric value wins.
4.  **Persistence:** The final state is periodically flushed to MongoDB as a "Snapshot" to prevent the event log from growing infinitely.

### Appendix B: HIPAA Compliance Checklist
To pass the 2026-09-15 security audit, the following must be verified:
*   [ ] **Access Control:** Unique User IDs and automatic logouts after 15 minutes of inactivity.
*   [ ] **Audit Controls:** Record of all access to PHI (Protected Health Information) stored in `EventStore`.
*   [ ] **Integrity:** Digital signatures on record versions to prevent undetected tampering.
*   [ ] **Transmission Security:** Forced TLS 1.3 with no fallback to SSLv3 or TLS 1.0.
*   [ ] **Data Disposal:** Defined process for purging records after the 7-year legal retention period.