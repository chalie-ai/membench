# Project Specification Document: Project Cairn
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft for Executive Review  
**Classification:** Internal/Confidential  
**Project Lead:** Elio Gupta (VP of Product)

---

## 1. Executive Summary

**Project Overview**  
Project Cairn is a high-stakes, real-time collaboration tool developed by Stormfront Consulting, specifically tailored for the rigorous demands of the legal services industry. Unlike generic productivity suites, Cairn is designed to handle the high-security, high-compliance requirements of legal discovery, contract negotiation, and multi-party litigation coordination. 

**Business Justification**  
The legal industry is currently underserved by general-purpose collaboration tools that lack the granular permissioning and auditability required for attorney-client privilege. Cairn aims to capture this niche by providing a "single pane of glass" for legal teams to collaborate on documents in real-time without compromising data sovereignty. Given the high billable rates of legal professionals, a tool that increases efficiency by even 5% per case can result in millions of dollars in reclaimed billable hours for a mid-to-large scale law firm.

**ROI Projection**  
Cairn is categorized as a "moonshot" R&D project. While the immediate Return on Investment (ROI) is uncertain due to the experimental nature of the real-time synchronization engine, the strategic value is immense. If successful, Cairn will transition from an internal tool to a SaaS offering. We project a Break-Even Point (BEP) at month 18 post-launch, assuming a subscription model of $150/user/month with an initial target of 2,000 seats across five pilot firms. The projected Year 3 ARR (Annual Recurring Revenue) is estimated at $3.6M, providing a positive ROI on the initial $5M+ investment.

**Strategic Sponsorship**  
This project enjoys strong executive sponsorship and is a flagship initiative for Stormfront Consulting, with progress reports delivered directly to the Board of Directors. Despite the technical uncertainty and the dysfunctional team dynamic, the project is mandated to proceed to Milestone 1 to prove the viability of the real-time legal collaboration thesis.

---

## 2. Technical Architecture

### 2.1 Architectural Overview
Cairn utilizes a **Micro-Frontend (MFE) Architecture**, allowing for independent team ownership of specific functional domains. This prevents the frontend from becoming a monolithic bottleneck and allows for the deployment of specific modules (e.g., the Search module vs. the Auth module) without impacting the entire user session.

**The Stack:**
- **Backend:** Python 3.11 with FastAPI (Asynchronous ASGI framework)
- **Database:** MongoDB 6.0 (NoSQL for flexible document schemas in legal case files)
- **Task Queue:** Celery 5.3 with Redis as a broker (for virus scanning and index updates)
- **Containerization:** Docker Compose (for local development and orchestration)
- **Hosting:** Self-hosted on private Stormfront Consulting infrastructure.

### 2.2 ASCII System Architecture Diagram
```text
[ Client Layer (Browser) ]
       |
       | (HTTPS / WebSocket)
       v
[ Nginx Load Balancer ]
       |
       +---------------------------------------+
       |                                       |
[ MFE: Auth Module ] <---> [ API Gateway (FastAPI) ] <---> [ MongoDB Cluster ]
[ MFE: Search Module ] <---> [   Business Logic    ] <---> [ Redis Cache ]
[ MFE: Collab Module ] <---> [   Middleware       ] <---> [ Celery Workers ]
                                      |                           |
                                      |                           v
                                      +------------------> [ Virus Scanner/CDN ]
```

### 2.3 Architecture Constraints
The system is deployed via manual processes handled by a single DevOps engineer. This creates a "Bus Factor of 1," representing a significant operational risk. There is no automated CI/CD pipeline; deployments consist of `docker-compose pull` and `docker-compose up -d` commands executed via SSH on the production server.

---

## 3. Detailed Feature Specifications

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical | **Status:** In Review | **ID:** FEAT-005

**Functional Description:**  
This feature provides the foundational security layer for Cairn. Given the sensitivity of legal data, the RBAC system must support "Need-to-Know" access patterns. Users are assigned roles (e.g., Managing Partner, Associate, Paralegal, External Counsel), and permissions are mapped to specific "Matters" (case folders).

**Detailed Requirements:**
- **Authentication:** JWT (JSON Web Token) based authentication with a 24-hour expiration and refresh token rotation.
- **RBAC Logic:** A hierarchical permission model where "Managing Partners" inherit all permissions of "Associates."
- **Audit Logging:** Every authentication attempt and permission change must be logged to a non-mutable MongoDB collection.
- **Integration:** Integration with Stormfront's internal LDAP for employee onboarding.

**Technical Implementation:**  
The logic currently resides within a 3,000-line "God Class" (`AuthManager.py`). This class handles the password hashing (Bcrypt), the session management, the email notification triggers for password resets, and the logging of IP addresses. This is a primary source of technical debt and is scheduled for refactoring into three separate services: `IdentityService`, `PermissionService`, and `NotificationService`.

### 3.2 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Medium | **Status:** Complete | **ID:** FEAT-004

**Functional Description:**  
Legal professionals deal with thousands of documents per case. This feature allows users to find specific clauses, names, or dates across all documents in a matter using natural language and faceted filters.

**Detailed Requirements:**
- **Full-Text Indexing:** Integration of MongoDB's `$text` index to allow for keyword searches across large bodies of text.
- **Faceted Filtering:** Users can filter results by Date Range, Document Type (PDF, DOCX, Email), Author, and Priority.
- **Highlighter:** The search results must return "snippets" of the document where the keyword was found, with the keyword highlighted.
- **Performance:** Search queries must return results in under 200ms for datasets up to 100,000 documents per matter.

**Technical Implementation:**  
Implemented using a custom FastAPI endpoint that translates frontend filter objects into MongoDB aggregation pipelines. The indexing is performed asynchronously via Celery workers to ensure that uploading a new document does not freeze the UI.

### 3.3 A/B Testing Framework (Feature Flag System)
**Priority:** Medium | **Status:** Complete | **ID:** FEAT-001

**Functional Description:**  
To validate ROI and user adoption, Cairn includes a built-in A/B testing framework. This allows the product team to roll out new UI components to a subset of users (e.g., 10% of pilot users) to measure engagement before a full release.

**Detailed Requirements:**
- **Flag Management:** A centralized administrative panel where Elio Gupta can toggle features "ON" or "OFF" without a code deployment.
- **User Bucketing:** A deterministic hashing algorithm that assigns users to "Group A" (Control) or "Group B" (Treatment) based on their UserID.
- **Telemetry:** Automatic logging of which feature flag was active when a user completed a specific action (e.g., "Document Saved").

**Technical Implementation:**  
The system uses a `FeatureFlag` collection in MongoDB. The frontend MFE queries the `/api/v1/flags` endpoint on initialization and stores the flags in a Redux state, which determines which components are rendered.

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** In Design | **ID:** FEAT-002

**Functional Description:**  
Users must be able to upload evidence and legal briefs. Because these files often come from untrusted external sources, they must be scanned for malware before being available to the rest of the team.

**Detailed Requirements:**
- **Scanning Pipeline:** Files are uploaded to a "Quarantine" S3 bucket. A Celery worker triggers a ClamAV scan. If clean, the file is moved to the "Production" bucket.
- **CDN Integration:** Files are served via a cached CDN layer to ensure low latency for remote legal teams.
- **Version Control:** Each upload creates a new version of the document; the "Current" version is pointed to by a database reference.

**Technical Implementation:**  
Proposed use of `FastAPI`'s `UploadFile` for streaming data to the quarantine bucket, with a webhook notifying the Celery worker to initiate the scan.

### 3.5 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** In Review | **ID:** FEAT-003

**Functional Description:**  
Lawyers often work in courtrooms or airplanes with unstable internet. Cairn must allow users to edit documents offline and sync changes automatically once a connection is restored.

**Detailed Requirements:**
- **Local Storage:** Use of IndexedDB in the browser to store a local cache of the active "Matter."
- **Conflict Resolution:** A "Last-Write-Wins" strategy for simple fields and a "Merge-Conflict-UI" for document text.
- **Background Sync:** Use of Service Workers to detect connectivity changes and push pending changes to the `/api/v1/sync` endpoint.

**Technical Implementation:**  
Currently in the review phase. The proposed approach uses an Operational Transformation (OT) or CRDT (Conflict-free Replicated Data Type) library, though the team's lack of experience with these technologies is a noted risk.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1`. Base URL: `https://cairn.stormfront.internal/api/v1`.

### 4.1 Authentication Endpoints
**POST `/auth/login`**
- **Request:** `{ "username": "string", "password": "string" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_in": 86400 }`
- **Description:** Authenticates user and returns a JWT.

**POST `/auth/refresh`**
- **Request:** `{ "refresh_token": "string" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_in": 86400 }`
- **Description:** Refreshes the session token.

### 4.2 User & RBAC Endpoints
**GET `/users/me`**
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "id": "uuid", "role": "Associate", "permissions": ["read_matter", "write_matter"] }`
- **Description:** Returns the current user's profile and permissions.

**PATCH `/users/{id}/role`**
- **Request:** `{ "new_role": "string" }`
- **Response:** `200 OK { "status": "updated" }`
- **Description:** Admin-only endpoint to change user roles.

### 4.3 Search Endpoints
**GET `/search/query`**
- **Request:** `?q=merger&matter_id=123&filter_date_start=2023-01-01`
- **Response:** `200 OK { "results": [ { "doc_id": "uuid", "snippet": "...merger agreement...", "score": 0.98 } ] }`
- **Description:** Executes faceted full-text search.

**GET `/search/facets`**
- **Request:** `?matter_id=123`
- **Response:** `200 OK { "doc_types": { "PDF": 45, "DOCX": 12 }, "authors": ["John Doe", "Jane Smith"] }`
- **Description:** Returns available filters for the search UI.

### 4.4 Document & File Endpoints
**POST `/docs/upload`**
- **Request:** Multipart Form Data `{ "file": Binary, "matter_id": "string" }`
- **Response:** `202 Accepted { "job_id": "celery_uuid", "status": "scanning" }`
- **Description:** Uploads a file and triggers the virus scanning pipeline.

**GET `/docs/{doc_id}/download`**
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK (Binary Stream)`
- **Description:** Streams a file from the CDN after verifying RBAC permissions.

---

## 5. Database Schema

Cairn uses MongoDB. While schema-less, the following logical collections and structures are enforced via Pydantic models in the FastAPI layer.

| Collection Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `Users` | `user_id` | `username`, `password_hash`, `email`, `role_id` | `role_id` $\rightarrow$ `Roles` |
| `Roles` | `role_id` | `role_name`, `permission_level`, `description` | One-to-Many with `Users` |
| `Matters` | `matter_id` | `case_number`, `client_name`, `created_at`, `status` | One-to-Many with `Documents` |
| `Documents` | `doc_id` | `matter_id`, `filename`, `s3_path`, `version`, `checksum` | `matter_id` $\rightarrow$ `Matters` |
| `Permissions` | `perm_id` | `user_id`, `matter_id`, `access_level` (Read/Write/Admin) | Many-to-Many `Users` $\leftrightarrow$ `Matters` |
| `AuditLogs` | `log_id` | `user_id`, `action`, `timestamp`, `ip_address`, `resource_id` | `user_id` $\rightarrow$ `Users` |
| `FeatureFlags` | `flag_id` | `flag_name`, `is_enabled`, `percentage_rollout` | N/A |
| `UserSegments` | `segment_id` | `user_id`, `flag_id`, `assigned_group` (A/B) | `user_id` $\rightarrow$ `Users` |
| `SearchIndices` | `index_id` | `doc_id`, `tokenized_text`, `metadata_tags` | `doc_id` $\rightarrow$ `Documents` |
| `SyncQueue` | `sync_id` | `user_id`, `pending_changes`, `last_sync_timestamp` | `user_id` $\rightarrow$ `Users` |

---

## 6. Deployment and Infrastructure

### 6.1 Environment Descriptions

**Development (Dev)**
- **Host:** Local Docker Desktop / Minikube.
- **Purpose:** Feature development and unit testing.
- **Data:** Mocked data generated by a Python script.
- **Deployment:** Manual `docker-compose up`.

**Staging (Staging)**
- **Host:** `staging.cairn.stormfront.internal`
- **Purpose:** Integration testing and UAT (User Acceptance Testing) for pilot users.
- **Data:** Sanitized snapshot of production data.
- **Deployment:** Manual pull from the `main` branch by the DevOps lead.

**Production (Prod)**
- **Host:** `cairn.stormfront.internal`
- **Purpose:** Live environment for executive demo and pilot users.
- **Data:** Actual legal matter data.
- **Deployment:** Manual deployment (Bus Factor 1). High-risk manual synchronization of MongoDB indices.

### 6.2 Infrastructure Components
- **Server:** 2x Ubuntu 22.04 Nodes (16vCPU, 64GB RAM).
- **Storage:** Network Attached Storage (NAS) for MongoDB data persistence.
- **CDN:** Internal Stormfront Cache Layer (Nginx-based).

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Approach:** Pytest for all backend logic.
- **Coverage Target:** 70% of the business logic.
- **Focus:** Testing individual FastAPI route handlers and MongoDB query builders.
- **Constraint:** Due to the "God Class" (`AuthManager.py`), unit tests for authentication are currently brittle and frequently fail.

### 7.2 Integration Testing
- **Approach:** Postman collections executed via a Jenkins runner.
- **Focus:** End-to-end flows: `Login` $\rightarrow$ `Search for Matter` $\rightarrow$ `Upload Document` $\rightarrow$ `Verify Virus Scan`.
- **Frequency:** Run once per deployment to Staging.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Cypress tests for the Micro-Frontend shells.
- **Focus:** Verifying that the MFE communication (via a global event bus) is functioning correctly.
- **Scenario:** Testing the A/B framework to ensure a user in Group B sees the new search UI and a user in Group A sees the old one.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | High | High | Accept risk and monitor weekly in budget reviews. |
| R-02 | Team lack of experience with FastAPI/MongoDB | High | Medium | Raise as a formal blocker in the next Board meeting. |
| R-03 | DevOps "Bus Factor of 1" (Single point of failure) | Medium | Critical | Cross-train Nadia Park on basic Docker Compose commands. |
| R-04 | Technical Debt in `AuthManager.py` | High | Medium | Schedule a dedicated "Refactor Sprint" before Milestone 2. |
| R-05 | Dependency on External API (3 weeks behind) | High | High | Identify alternative mocks to allow development to continue. |

**Probability/Impact Matrix:**
- **Critical:** R-03 (High impact if the person leaves).
- **High:** R-01, R-02, R-05.
- **Medium:** R-04.

---

## 9. Timeline and Milestones

### 9.1 Phase Description
- **Phase 1: Foundation (Now - 2025-07-15):** Focus on RBAC, basic document storage, and search indexing.
- **Phase 2: Feature Expansion (2025-07-16 - 2025-09-15):** Implementation of A/B testing and virus scanning.
- **Phase 3: Optimization (2025-09-16 - 2025-11-15):** Performance tuning and offline-first sync.

### 9.2 Gantt-Style Milestones
| Milestone | Target Date | Dependencies | Key Deliverable |
| :--- | :--- | :--- | :--- |
| **M1: Internal Alpha** | 2025-07-15 | RBAC (FEAT-005) | Working prototype for internal stakeholders. |
| **M2: MVP Complete** | 2025-09-15 | Virus Scan (FEAT-002) | Feature-complete build for pilot law firms. |
| **M3: Perf Benchmarks**| 2025-11-15 | Search (FEAT-004) | 200ms search latency on 100k documents. |

---

## 10. Meeting Notes

### Meeting 1: Project Alignment
**Date:** 2023-11-02 | **Attendees:** Elio, Beau, Petra, Nadia
**Discussion:**
- Elio presented the board's desire for a "flashy" demo. 
- Beau expressed frustration that the API specifications for the search module were changed three times in two weeks.
- Petra raised concerns about the internal-only security audit, arguing that legal clients will demand SOC2 compliance.
- Elio dismissed the SOC2 concern, stating that the executive sponsorship protects them from this requirement for now.
**Action Items:**
- Beau to finish the search UI mockup. (Owner: Beau)
- Petra to document the current security gaps. (Owner: Petra)

### Meeting 2: Technical Blockers
**Date:** 2023-11-15 | **Attendees:** Elio, Beau, Petra, Nadia
**Discussion:**
- The team discussed the "God Class" (`AuthManager.py`). Beau refuses to touch it, claiming it is "Petra's architectural mess."
- Petra responded by stating that the lack of a clear product spec from Elio led to the class's growth.
- Nadia pointed out that the dependency on the External API team is now 3 weeks behind, preventing the offline-sync feature from being tested.
- Silence followed for 5 minutes as Elio and Beau stopped speaking to each other.
**Action Items:**
- Elio to contact the other team's manager to resolve the 3-week delay. (Owner: Elio)
- Nadia to create a mock API for the sync service. (Owner: Nadia)

### Meeting 3: Budgetary Review
**Date:** 2023-12-01 | **Attendees:** Elio, Board Representative
**Discussion:**
- The board questioned the $5M spend relative to the "uncertain ROI."
- Elio highlighted the A/B testing framework as a way to prove value quickly.
- Discussion regarding the 30% potential budget cut for the next quarter.
- The board requested a performance benchmark report by November 2025.
**Action Items:**
- Elio to prepare a weekly budget monitoring sheet. (Owner: Elio)
- Team to prioritize the "Critical" RBAC feature to avoid a launch blocker. (Owner: All)

---

## 11. Budget Breakdown

**Total Allocated Budget:** $5,250,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,412,500 | 4 Full-time senior salaries + Benefits (3 years) |
| **Infrastructure**| 15% | $787,500 | Self-hosted servers, NAS storage, Electricity/Cooling |
| **Software Tools** | 5% | $262,500 | MongoDB Enterprise, Docker Business, JetBrains Licenses |
| **Contingency** | 15% | $787,500 | Reserve for emergency scaling or external consultants |

**Fiscal Note:** A projected 30% cut would reduce the budget by ~$1.57M, which would likely necessitate the removal of the "Offline-First" and "Virus Scanning" features.

---

## 12. Appendices

### Appendix A: "God Class" Analysis (`AuthManager.py`)
The `AuthManager.py` file is currently 3,142 lines of code. It violates the Single Responsibility Principle (SRP) by performing the following tasks:
1. **Database Connectivity:** Directly opens MongoDB connections rather than using a dependency-injected session.
2. **Encryption:** Implements a custom wrapper around Bcrypt.
3. **Emailing:** Contains hard-coded SMTP settings for the Stormfront mail server.
4. **Logging:** Writes directly to a local `.log` file instead of using the centralized logging service.
5. **Permission Mapping:** Contains a hard-coded dictionary of 50+ roles and their corresponding permissions.

### Appendix B: Performance Benchmarking Methodology
To meet Milestone 3, the following test suite will be executed:
1. **Dataset:** A synthetic dataset of 100,000 PDF documents, each containing 10-50 pages of legal text.
2. **Query Set:** 1,000 randomized queries including single-word keywords and multi-word phrases.
3. **Metric:** The "P99 Latency" must be $\le 200\text{ms}$.
4. **Hardware:** Tests must be run on the production-spec Ubuntu nodes to account for real-world I/O overhead.