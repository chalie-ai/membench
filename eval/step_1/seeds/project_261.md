# PROJECT SPECIFICATION DOCUMENT: SENTINEL
**Document Version:** 1.0.4  
**Status:** Active/Working Document  
**Project Lead:** Emeka Oduya (CTO)  
**Company:** Oakmount Group  
**Classification:** Internal - Highly Confidential (Healthcare Data)  
**Date Created:** October 24, 2025  
**Last Updated:** November 12, 2025  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Sentinel is a real-time collaboration tool designed specifically for the high-stakes, high-compliance environment of the healthcare industry. Originally conceived as a hackathon project within the Oakmount Group, Sentinel demonstrated an unexpected and rapid organic adoption rate, currently supporting 500 daily active users (DAUs) across multiple clinical and administrative departments. 

The core business problem Sentinel solves is the "fragmentation of clinical communication." In healthcare, critical data often resides in silos—email, legacy EHR (Electronic Health Record) notes, and physical hand-off sheets. This fragmentation leads to cognitive overload for practitioners and increases the risk of medical error. Sentinel provides a unified, real-time workspace where multidisciplinary teams can collaborate on patient care plans, administrative workflows, and research documents without leaving a secure, ISO 27001-compliant environment.

By migrating from a fragmented ecosystem to a centralized real-time tool, Oakmount Group aims to eliminate the "communication lag" that currently plagues inter-departmental coordination. The tool's ability to provide a single source of truth in real-time reduces the time spent on reconciliation meetings and manual data entry.

### 1.2 ROI Projection
The financial justification for Sentinel is based on a "Cost of Inefficiency" model. Currently, 500 users spend an estimated 4.5 hours per week on manual processing—specifically updating spreadsheets, sending follow-up emails to confirm document versions, and manually merging clinical notes.

**Projected Savings:**
- **Direct Labor Savings:** A 50% reduction in manual processing time (Success Criterion 2) equates to 2.25 hours saved per user, per week. Across 500 users, this represents 1,125 hours of reclaimed productivity weekly. At an average burdened labor rate of $65/hour, the projected annual savings exceed $3.6 million.
- **Risk Mitigation:** By reducing version-control errors in care plans, the organization anticipates a decrease in "preventable administrative errors," which currently cost the group approximately $200,000 annually in correction labor and compliance penalties.
- **Scalability:** While the current budget is a "shoestring" $150,000, the ROI is calculated against the operational efficiency gains rather than the development cost.

The primary goal is to achieve a Net Promoter Score (NPS) of >40 within the first quarter post-launch, ensuring that the tool is not just functional, but embraced by the clinical staff, thereby guaranteeing the sustainability of the productivity gains.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Overview
Sentinel utilizes a modern, asynchronous architecture designed for high availability and strict data isolation. The system is built on a **Python/FastAPI** backend, leveraging **MongoDB** for flexible document storage and **Celery** for background task processing. 

The architecture is designed as a series of serverless functions orchestrated by an **API Gateway**. This allows the Oakmount Group to scale individual components of the collaboration tool independently—for example, scaling the real-time socket handlers during peak morning shift-change hours without needing to scale the billing or search modules.

### 2.2 ASCII Architecture Diagram Description
The system follows a layered approach. Below is the structural flow:

```text
[ Client Layer ]  --> (Web Browser / Mobile App)
       |
       v
[ Gateway Layer ] --> (API Gateway / Load Balancer)
       |
       +-----> [ Auth Service ] ----> (Hardware Key / 2FA Validation)
       |
       +-----> [ Orchestration Layer (FastAPI) ]
                   |
                   +-- [ Real-time Engine ] <--> (WebSocket / Operational Transform)
                   |
                   +-- [ Search Engine ] <--> (MongoDB Text Index / Faceted Search)
                   |
                   +-- [ Billing Module ] <--> (Stripe/Internal Ledger)
                   |
                   v
[ Data & Task Layer ]
       |
       +-----> [ MongoDB Cluster ] (Document Store)
       |
       +-----> [ Redis ] (Celery Broker / WebSocket Session Store)
       |
       +-----> [ Celery Workers ] (Asynchronous PDF generation, Email, Audit Logs)
```

### 2.3 Infrastructure Strategy
The entire stack is containerized using **Docker Compose** and is **self-hosted** within the Oakmount Group’s private cloud. This is a non-negotiable requirement to maintain ISO 27001 certification, as third-party cloud hosting of patient-adjacent data would require extensive BAA (Business Associate Agreements) and potential regulatory hurdles.

The deployment pipeline includes a mandatory **manual QA gate**. No code reaches production without a sign-off from Hugo Jensen (QA Lead). This ensures that "move fast and break things" does not apply to healthcare productivity, where a bug could lead to critical data loss.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
The cornerstone of Sentinel is the ability for multiple healthcare providers to edit a document simultaneously without overwriting each other's changes. Given the criticality of medical data, "Last Write Wins" is unacceptable. The system must implement a robust conflict resolution mechanism.

**Technical Specification:**
Sentinel utilizes a hybrid of **Operational Transformation (OT)** and **CRDTs (Conflict-free Replicated Data Types)**. When a user makes a change, the delta is sent via WebSockets to the FastAPI server. The server transforms the operation against concurrent operations from other users and broadcasts the transformed operation to all connected clients.

**Detailed Requirements:**
- **Concurrency Control:** Support for up to 50 simultaneous editors per document.
- **Cursor Tracking:** Real-time visualization of other users' cursors with name tags.
- **Version History:** Every "committed" state is snapshotted in MongoDB, allowing users to revert to any version from the last 30 days.
- **Latency Target:** End-to-end propagation of an edit must occur in <100ms to prevent "typing lag."
- **Conflict Handling:** In the event of a network partition, the system will prioritize the most recent timestamped change but flag the section as "Conflict Pending" for manual review by the document owner.

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** In Progress

**Description:**
Due to ISO 27001 requirements and the sensitivity of healthcare data, standard password authentication is insufficient. Sentinel requires a mandatory 2FA layer.

**Technical Specification:**
The system supports **WebAuthn** for hardware keys (YubiKey, Titan) and TOTP (Time-based One-Time Passwords) via apps like Google Authenticator.

**Detailed Requirements:**
- **Hardware Key Integration:** Use of the `python-fido2` library to handle attestation and assertion.
- **Enrollment Flow:** Users must register at least two 2FA methods (one primary hardware key, one backup TOTP) to prevent lockout.
- **Session Management:** JWT (JSON Web Tokens) are used for session persistence, with a maximum lifespan of 12 hours, requiring re-authentication for high-privilege actions (e.g., exporting patient lists).
- **Recovery Codes:** Generation of 10 single-use recovery codes upon 2FA setup, stored as bcrypt hashes in MongoDB.
- **Audit Trail:** Every 2FA attempt (success or failure) is logged with IP and device fingerprint.

### 3.3 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** Complete

**Description:**
Although Sentinel is an internal tool, it is funded by a "charge-back" model where different hospital departments are billed based on their usage tiers.

**Technical Specification:**
A dedicated module handles the calculation of monthly costs based on the number of active seats and storage used.

**Detailed Requirements:**
- **Tiered Pricing:** Three tiers: Basic (up to 50 users), Professional (up to 200), and Enterprise (unlimited).
- **Automated Invoicing:** On the 1st of every month, a Celery task triggers the `billing_engine` to aggregate usage data from the `subscriptions` collection.
- **Payment Integration:** Integration with the internal Oakmount Group General Ledger API to automate departmental fund transfers.
- **Grace Periods:** 14-day grace period for unpaid departmental accounts before "Read-Only" mode is triggered.
- **Notification:** Automated email alerts sent 5 days before the billing cycle ends.

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** Not Started

**Description:**
As the volume of collaborative documents grows, users need a way to find specific information across thousands of files using natural language and specific attributes.

**Technical Specification:**
Leveraging MongoDB's `$search` pipeline and text indices to provide high-performance querying.

**Detailed Requirements:**
- **Full-Text Indexing:** All document bodies and titles must be indexed.
- **Faceted Filtering:** Users should be able to filter results by:
    - Date range (Created/Modified).
    - Author/Department.
    - Document Tag (e.g., #CarePlan, #Audit, #Research).
    - Access Level.
- **Search Suggestions:** A "type-ahead" feature providing suggested documents based on the first three characters entered.
- **Ranking Algorithm:** Results are ranked by a combination of keyword frequency and "recency bias" (newer documents appear higher).

### 3.5 Webhook Integration Framework for Third-Party Tools
**Priority:** Low | **Status:** Blocked

**Description:**
The ability for Sentinel to push notifications or data to external healthcare tools (e.g., paging systems, external lab portals).

**Technical Specification:**
A generic webhook dispatcher that allows administrators to define a URL and a trigger event.

**Detailed Requirements:**
- **Event Triggers:** Trigger webhooks on `document_created`, `document_updated`, or `user_joined_workspace`.
- **Payload Format:** JSON payloads containing the event type, timestamp, and a unique resource ID.
- **Security:** All outgoing webhooks must be signed using an HMAC-SHA256 signature to allow the receiving end to verify the source.
- **Retry Logic:** Exponential backoff retry strategy for failed deliveries (3 retries over 1 hour).
- **Monitoring:** A dashboard showing the delivery success rate of all active webhooks.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer` token in the Authorization header.

### 4.1 Document Management
**Endpoint:** `POST /documents`
- **Description:** Create a new collaborative document.
- **Request Body:** `{"title": "Patient X Care Plan", "content": "", "department_id": "dept_123"}`
- **Response (201):** `{"doc_id": "doc_987", "created_at": "2025-11-12T10:00:00Z"}`

**Endpoint:** `GET /documents/{doc_id}`
- **Description:** Retrieve document content and metadata.
- **Response (200):** `{"doc_id": "doc_987", "title": "Patient X Care Plan", "content": "...", "version": 45}`

**Endpoint:** `PATCH /documents/{doc_id}`
- **Description:** Update a specific section of a document.
- **Request Body:** `{"delta": "...", "version": 45}`
- **Response (200):** `{"status": "success", "new_version": 46}`

### 4.2 User & Authentication
**Endpoint:** `POST /auth/2fa/register`
- **Description:** Link a hardware key to a user account.
- **Request Body:** `{"credential_id": "...", "public_key": "..."}`
- **Response (200):** `{"status": "verified", "method": "webauthn"}`

**Endpoint:** `POST /auth/login`
- **Description:** Primary authentication step.
- **Request Body:** `{"username": "emeka_oduya", "password": "..."}`
- **Response (200):** `{"temp_token": "...", "requires_2fa": true}`

### 4.3 Billing & Admin
**Endpoint:** `GET /billing/invoice/{dept_id}`
- **Description:** Retrieve the latest invoice for a department.
- **Response (200):** `{"invoice_id": "inv_001", "amount": 450.00, "status": "paid"}`

**Endpoint:** `POST /admin/webhooks/create`
- **Description:** Configure a new outgoing webhook.
- **Request Body:** `{"target_url": "https://hooks.external.com", "event": "doc_updated"}`
- **Response (201):** `{"webhook_id": "wh_555"}`

### 4.4 Search
**Endpoint:** `GET /search?q={query}&dept={dept_id}`
- **Description:** Perform a faceted search across documents.
- **Response (200):** `{"results": [{"doc_id": "...", "score": 0.98}], "total": 12}`

---

## 5. DATABASE SCHEMA (MongoDB)

Sentinel uses a document-oriented schema. While MongoDB is schemaless, the application enforces the following structures via Pydantic models.

### 5.1 Collections List
1. **Users:** Core identity data.
2. **Documents:** The content and metadata of collaborative files.
3. **Operations:** Log of all OT changes (used for versioning/recovery).
4. **Workspaces:** Groupings of documents by department.
5. **Subscriptions:** Billing tiers and payment history.
6. **AuditLogs:** Every single action taken in the system for ISO 27001.
7. **AuthMethods:** Storage for WebAuthn public keys and TOTP seeds.
8. **Webhooks:** Configuration for third-party integrations.
9. **Permissions:** ACLs (Access Control Lists) mapping users to documents.
10. **Sessions:** Active login sessions and device fingerprints.

### 5.2 Key Collection Details

**Users Collection**
- `_id`: ObjectId (PK)
- `username`: String (Unique)
- `email`: String (Unique)
- `password_hash`: String
- `dept_id`: ObjectId (FK -> Workspaces)
- `role`: Enum (Admin, Practitioner, Auditor)
- `created_at`: DateTime

**Documents Collection**
- `_id`: ObjectId (PK)
- `title`: String
- `body`: String
- `current_version`: Integer
- `owner_id`: ObjectId (FK -> Users)
- `workspace_id`: ObjectId (FK -> Workspaces)
- `tags`: Array[String]
- `last_modified`: DateTime

**Operations Collection**
- `_id`: ObjectId (PK)
- `doc_id`: ObjectId (FK -> Documents)
- `user_id`: ObjectId (FK -> Users)
- `version`: Integer
- `op_type`: Enum (Insert, Delete, Retain)
- `op_data`: String/JSON
- `timestamp`: DateTime

**Subscriptions Collection**
- `_id`: ObjectId (PK)
- `workspace_id`: ObjectId (FK -> Workspaces)
- `tier`: Enum (Basic, Professional, Enterprise)
- `monthly_cost`: Decimal
- `status`: Enum (Active, PastDue, Cancelled)
- `next_billing_date`: Date

**AuditLogs Collection**
- `_id`: ObjectId (PK)
- `timestamp`: DateTime
- `user_id`: ObjectId (FK -> Users)
- `action`: String (e.g., "DOC_EXPORT", "USER_LOGIN")
- `resource_id`: String
- `ip_address`: String
- `outcome`: Enum (Success, Failure)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes three distinct environments to ensure stability and security.

**Development (Dev):**
- **Purpose:** Active coding and feature experimentation.
- **Access:** All 15 team members.
- **Database:** Mock data only; no real patient information.
- **Deployment:** Automated on every merge to `develop` branch.

**Staging (Staging):**
- **Purpose:** Pre-production validation and QA.
- **Access:** Developers and Hugo Jensen (QA Lead).
- **Database:** Anonymized production snapshot.
- **Deployment:** Triggered manually after Dev tests pass. This environment mirrors Production's hardware specs exactly.

**Production (Prod):**
- **Purpose:** Live user environment (500 DAUs).
- **Access:** Restricted to Emeka Oduya and Suki Moreau (for support).
- **Database:** Encrypted at rest, ISO 27001 compliant.
- **Deployment:** Manual QA gate. 2-day turnaround from Staging sign-off to Production deploy.

### 6.2 Infrastructure Stack
- **Containerization:** Docker Compose is used to orchestrate the FastAPI app, MongoDB, and Celery workers.
- **OS:** Ubuntu 22.04 LTS.
- **Networking:** Private VPC with no direct public internet access to the database layer. The API Gateway acts as the sole entry point.
- **Backup:** Daily incremental backups of MongoDB to an off-site encrypted S3-compatible bucket.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, Pydantic models, and API route logic.
- **Tooling:** `pytest` and `httpx` for async requests.
- **Requirement:** Minimum 80% code coverage for any new feature.
- **Frequency:** Run on every commit via CI pipeline.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between FastAPI, MongoDB, and Celery.
- **Focus:** Ensuring that a document update correctly triggers a Celery task to update the search index.
- **Method:** Spinning up a temporary Docker Compose environment with a "Test" MongoDB instance.
- **Frequency:** Run once per pull request.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "Login with 2FA -> Open Document -> Edit Content -> Save").
- **Tooling:** Playwright for browser automation.
- **Method:** Automated scripts simulating real user interactions in the Staging environment.
- **Frequency:** Run before every production deployment.

### 7.4 QA Gate Process
Hugo Jensen maintains the final authority on deployment. The "QA Gate" involves:
1. **Regression Suite:** Running all E2E tests.
2. **Manual Sanity Check:** Testing the specific "Critical" feature of the sprint.
3. **Security Review:** Verifying that no new endpoints bypass the 2FA layer.
4. **Sign-off:** A formal "GO/NO-GO" decision logged in the project management tool.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with FastAPI/MongoDB stack | High | High | Build a contingency plan with a fallback architecture (e.g., Flask/Postgres) and schedule weekly peer-programming sessions. |
| R-02 | Budget cut by 30% in next fiscal quarter | Medium | High | Engage an external consultant for an independent assessment to prove ROI to stakeholders and justify budget retention. |
| R-03 | Hardware key adoption is lower than expected | Low | Medium | Provide a fallback TOTP (App-based) 2FA method to ensure users aren't blocked. |
| R-04 | Real-time conflict resolution causes data loss | Low | Critical | Implement rigorous snapshotting and a "Journal" of all operations to allow manual reconstruction of documents. |
| R-05 | ISO 27001 audit failure | Low | High | Conduct monthly internal "mock audits" and maintain a strict documentation trail for all security changes. |

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown
**Phase 1: Foundation & Hardening (Current - April 2026)**
- Focus on 2FA implementation and stabilizing the collaborative editing engine.
- Dependency: Completion of the 2FA module is required before the security audit.
- **Milestone 1: Security audit passed (Target: 2026-04-15)**

**Phase 2: Stability & Performance (April 2026 - June 2026)**
- Focus on optimizing the MongoDB queries and refining the WebSocket handler to handle higher concurrency.
- Dependency: Stable real-time editing must be confirmed in Staging.
- **Milestone 2: Post-launch stability confirmed (Target: 2026-06-15)**

**Phase 3: Feature Expansion (June 2026 - August 2026)**
- Implementation of advanced search and the webhook framework (if budget permits).
- Dependency: Stability metrics must meet the "zero critical bugs" threshold.
- **Milestone 3: MVP feature-complete (Target: 2026-08-15)**

### 9.2 Gantt-Style Dependencies
- `2FA Development` $\rightarrow$ `Security Audit` $\rightarrow$ `Production Launch`
- `Collaborative Engine` $\rightarrow$ `Performance Tuning` $\rightarrow$ `Stability Confirmation`
- `Billing Module (Complete)` $\rightarrow$ `Budget Review` $\rightarrow$ `Feature Expansion`

---

## 10. MEETING NOTES (Slack Archive)

*Note: Per project standards, no formal minutes are kept. The following are synthesized from key decision-making threads in the #sentinel-dev Slack channel.*

### Meeting 1: Architecture Pivot (Thread: #sentinel-arch-decisions)
**Participants:** Emeka Oduya, Astrid Park
**Context:** Discussion on whether to use a relational database or MongoDB.
- **Astrid:** "If we go with Postgres, we'll struggle with the varying structure of clinical notes. MongoDB's flexible schema is better for the 'document' nature of the tool."
- **Emeka:** "I agree, but we need to be disciplined about the schema. We can't let it become a data swamp. Let's use Pydantic for strict validation at the API layer."
- **Decision:** Proceed with MongoDB; implement Pydantic models to enforce a "virtual schema."

### Meeting 2: The "Shoestring" Budget Crisis (Thread: #sentinel-ops)
**Participants:** Emeka Oduya, Hugo Jensen, Suki Moreau
**Context:** Reaction to the news of a potential 30% budget cut.
- **Suki:** "If we lose budget, we can't afford the external security auditors for the April milestone."
- **Hugo:** "We should prioritize the conflict resolution engine over the search feature. If we don't get real-time right, the tool is useless."
- **Emeka:** "Correct. Search and Webhooks are now 'low priority.' We focus everything on the 'Critical' and 'High' items. I'll bring in a consultant to validate our ROI so we can fight for the budget."
- **Decision:** Re-prioritize features; Search and Webhooks moved to "Nice to have."

### Meeting 3: 2FA Hardware Key Implementation (Thread: #sentinel-security)
**Participants:** Emeka Oduya, Astrid Park, Hugo Jensen
**Context:** Determining how to handle hardware key registration.
- **Hugo:** "We can't just allow any key. We need to ensure the keys are FIPS-compliant for ISO 27001."
- **Astrid:** "The `python-fido2` library allows us to check the attestation certificate. We can whitelist specific AAGUIDs (Authenticator Attestation GUIDs)."
- **Emeka:** "Let's do that. Only YubiKey and Google Titan keys will be accepted for the 'High' security role."
- **Decision:** Implement AAGUID whitelisting for hardware keys.

---

## 11. BUDGET BREAKDOWN

The total budget is $150,000. Due to the "shoestring" nature of the project, expenses are tracked weekly.

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $95,000 | Distributed team of 15 (Combination of internal salaries and contractor stipends). |
| **Infrastructure** | $20,000 | Self-hosted server hardware, electricity, and private cloud storage. |
| **Security & Tools** | $15,000 | ISO 27001 certification fees, MongoDB Enterprise subscription, and Docker licenses. |
| **Contingency** | $20,000 | Reserved for emergency hardware replacement or external security consultants. |
| **Total** | **$150,000** | |

**Financial Constraints:**
- Every expense over $500 requires direct sign-off from Emeka Oduya.
- A 30% budget cut would remove $45,000, primarily impacting the "Contingency" and "Personnel" (contractor) lines.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (Operational Transformation)
To handle real-time editing, Sentinel uses a transformation function $\text{T}(\text{op}_1, \text{op}_2)$. 
If User A inserts "X" at position 5 and User B inserts "Y" at position 5 simultaneously:
1. The server receives $\text{op}_A$ and $\text{op}_B$.
2. The server transforms $\text{op}_B$ relative to $\text{op}_A$.
3. The resulting operation $\text{op}_{B}'$ is "Insert 'Y' at position 6."
4. This ensures that both users see the same final string ("XY") regardless of network latency.

### Appendix B: ISO 27001 Compliance Checklist
For Milestone 1, the following technical controls must be verified:
- **Access Control:** All users are mapped to a specific department via `dept_id`. No global read access.
- **Encryption:** All data in MongoDB is encrypted using AES-256. All API traffic is forced over TLS 1.3.
- **Logging:** Every `POST`, `PATCH`, and `DELETE` request is mirrored to the `AuditLogs` collection with a non-nullable `user_id`.
- **Availability:** Use of Docker Compose restart policies and daily off-site backups ensures a Recovery Time Objective (RTO) of 4 hours.