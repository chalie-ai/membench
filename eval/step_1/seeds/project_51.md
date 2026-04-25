Due to the extreme length requirements (6,000–8,000 words), this document is structured as a comprehensive, professional Technical Specification Document (TSD). It serves as the "Single Source of Truth" for the development team at Ridgeline Platforms.

***

# PROJECT CAIRN: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Active/Baseline  
**Date:** October 24, 2024  
**Project Lead:** Rosa Kim (CTO)  
**Company:** Ridgeline Platforms  
**Confidentiality Level:** Internal - Restricted  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Cairn" is a mission-critical supply chain management system specifically tailored for the legal services industry. Unlike traditional retail supply chains, the "supply chain" in legal services refers to the flow of discovery documents, expert witness testimony, regulatory filings, and contractual obligations across multiple jurisdictions. 

The urgency of Cairn is driven by a hard legal deadline occurring six months from the project start date. Failure to deploy a compliant system will result in severe regulatory penalties and potential loss of licensure for Ridgeline Platforms' clients. The system must ensure that every "link" in the legal supply chain is traceable, immutable, and compliant with international data laws.

### 1.2 Business Justification
The current legacy system is a fragmented collection of spreadsheets and legacy SQL databases that lack audit trails and fail to meet modern GDPR/CCPA standards. As legal services transition to more digitized, cross-border workflows, the risk of "compliance leakage"—where sensitive data resides in unauthorized jurisdictions—has become a board-level liability.

Cairn solves this by implementing a distributed architecture that enforces data residency and strict Role-Based Access Control (RBAC). By automating the tracking of legal deliverables and automating the compliance checks, the company reduces the manual overhead associated with regulatory reporting.

### 1.3 ROI Projection
The project operates on a highly constrained budget of $150,000. However, the projected ROI is calculated based on two primary drivers:
1. **Cost Reduction:** By migrating from legacy on-premise servers to a highly optimized GCP Kubernetes environment and reducing manual reconciliation, the cost per transaction is projected to decrease by 35%.
2. **Risk Mitigation:** The avoidance of regulatory fines (estimated at $2M+ for non-compliance in the EU) provides an immediate insurance-style ROI.
3. **Operational Efficiency:** We project an 80% feature adoption rate among pilot users, which will allow the company to scale its client base by 20% without increasing administrative headcount.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Cairn utilizes a **microservices architecture** designed for high availability and strict data partitioning. To handle the legal industry's requirement for "perfect" audit trails, the system employs an **event-driven communication** model via Apache Kafka. This ensures that every state change in the supply chain is recorded as an event, providing an immutable log of all actions.

### 2.2 The Stack
*   **Language:** Go (Golang) for all microservices due to its concurrency primitives and performance.
*   **Communication:** gRPC for internal service-to-service calls to minimize latency and ensure strong typing via Protocol Buffers.
*   **Database:** CockroachDB (Distributed SQL) to handle multi-region data residency requirements and ensure strong consistency (ACID).
*   **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
*   **Message Broker:** Apache Kafka for asynchronous event propagation.
*   **Frontend:** React with TypeScript (implied by UX researcher's focus).

### 2.3 System Topology (ASCII Diagram)

```text
[ Client Browser / Legal Portal ] 
            | (HTTPS/TLS 1.3)
            v
    [ Google Cloud Load Balancer ]
            |
    [ GKE Ingress Controller ]
            |
    ----------------------------------------------------------------------
    |                 KUBERNETES CLUSTER (GCP)                           |
    |                                                                    |
    |  [ API Gateway ] <------> [ Auth Service ] <------> [ CockroachDB ]|
    |        |                         |                                |
    |        v                         v                                |
    |  [ Event Bus (Kafka) ] <--- [ Audit Log Service ]                  |
    |        |                                                          |
    |        +------> [ Supply Chain Service ] <---> [ CockroachDB (EU) ]|
    |        |                                                          |
    |        +------> [ Document Service ] <---> [ GCP Cloud Storage ]   |
    |        |                                                          |
    |        +------> [ Localization Service ] <--> [ Redis Cache ]     |
    |                                                                    |
    ----------------------------------------------------------------------
            |
    [ External Integration Partner API ] <--- (Buggy/Undocumented)
```

### 2.4 Data Residency and Security
To comply with GDPR and CCPA, Cairn implements **Regional Data Sharding**. CockroachDB is configured to pin specific rows to EU-based nodes for European clients. All data at rest is encrypted using AES-256, and all data in transit uses TLS 1.3.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Review
*   **Description:** A robust identity management system that ensures only authorized legal personnel can access sensitive supply chain data.

**Functional Requirements:**
The system must support three primary roles: `SuperAdmin`, `LegalAuditor`, and `CaseManager`.
- `SuperAdmin`: Full system access, user provisioning, and system configuration.
- `LegalAuditor`: Read-only access to all audit logs and supply chain movements; cannot modify data.
- `CaseManager`: Full CRUD access to cases and documents they are specifically assigned to.

**Technical Implementation:**
Authentication will be handled via JWT (JSON Web Tokens) with a short expiration (15 minutes) and a sliding-window refresh token stored in an encrypted HttpOnly cookie. The `Auth Service` will expose a gRPC endpoint to other microservices to validate tokens. 

**Conflict Resolution:** If a user's role is changed while they have an active session, the `Auth Service` will emit a "SessionInvalidate" event via Kafka, forcing the API Gateway to reject subsequent requests until a re-authentication occurs.

---

### 3.2 Localization and Internationalization (L10n/I18n)
*   **Priority:** Medium
*   **Status:** In Review
*   **Description:** Support for 12 primary languages to facilitate cross-border legal supply chain management.

**Functional Requirements:**
The system must support dynamic switching of languages without page reloads. The 12 supported languages include English, French, German, Spanish, Italian, Portuguese, Chinese (Mandarin), Japanese, Korean, Arabic, Dutch, and Polish. 

**Technical Implementation:**
We will use a "Translation Key" approach. The frontend will store keys (e.g., `SUPPLY_CHAIN_STATUS`), which are mapped to actual strings in a `Localization Service`. This service will cache translations in Redis to prevent database hits on every page load. 

The system must handle Right-to-Left (RTL) layouts for Arabic. The CSS framework will utilize logical properties (e.g., `margin-inline-start` instead of `margin-left`) to ensure the layout flips correctly based on the locale.

---

### 3.3 Real-time Collaborative Editing with Conflict Resolution
*   **Priority:** Medium
*   **Status:** In Review
*   **Description:** Allowing multiple legal analysts to edit supply chain manifests and compliance reports simultaneously.

**Functional Requirements:**
Users must see "presence indicators" (who else is editing the document) and real-time cursor movements. Edits must be propagated with sub-100ms latency.

**Technical Implementation:**
Cairn will implement **Operational Transformation (OT)** or **CRDTs (Conflict-free Replicated Data Types)**. Given the requirement for a strict legal audit trail, CRDTs (specifically LWW-Element-Set) will be used to ensure that no data is ever "lost" during a conflict, only superseded by a more recent timestamp. 

WebSockets will be used for the real-time transport layer. When a user makes a change, the change is sent as a "Delta" to the `Collaborative Service`, which broadcasts the delta to all other connected clients and asynchronously commits the final state to CockroachDB.

---

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Medium
*   **Status:** Blocked (Dependent on UI Component Library)
*   **Description:** A personalized home screen where users can arrange widgets to monitor their specific legal supply chain KPIs.

**Functional Requirements:**
Users can drag widgets (e.g., "Pending Compliance Approvals," "Critical Deadline Timer," "Recent Document Uploads") and resize them. The layout must be persisted per user.

**Technical Implementation:**
The dashboard will be implemented using a grid-based layout system (e.g., React-Grid-Layout). The state of the dashboard (widget ID, X-coordinate, Y-coordinate, Width, Height) will be stored as a JSON blob in the `UserPreferences` table in CockroachDB. 

Since this is currently **blocked**, the team is utilizing a mock-up in Figma to define the API contracts for the widget data providers so that backend development can continue in parallel.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
*   **Priority:** Low (Nice to have)
*   **Status:** In Design
*   **Description:** Secure upload of legal evidence and documents with automatic malware detection and global delivery.

**Functional Requirements:**
Files must be scanned for viruses before being marked as "Available" in the supply chain. Large files must be distributed via a CDN to ensure legal teams in different continents can access documents without latency.

**Technical Implementation:**
1. **Upload:** Files are uploaded to a "Quarantine" bucket in GCP Cloud Storage.
2. **Scanning:** A Go-based worker service triggers a ClamAV scan on the file.
3. **Promotion:** If clean, the file is moved to the "Production" bucket.
4. **Distribution:** The Production bucket is fronted by Google Cloud CDN.
5. **Security:** Each file is served via a "Signed URL" with a 10-minute expiration to prevent unauthorized link sharing.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/v1/`. Authentication requires a Bearer Token in the header.

### 4.1 Auth Service
**Endpoint:** `POST /v1/auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request:** `{"username": "string", "password": "string"}`
- **Response:** `200 OK {"token": "eyJ...", "expires_at": "2025-10-24T12:00:00Z"}`

**Endpoint:** `POST /v1/auth/refresh`
- **Description:** Refreshes the access token using a refresh token.
- **Request:** `{"refresh_token": "string"}`
- **Response:** `200 OK {"token": "eyJ...", "expires_at": "..."}`

### 4.2 Supply Chain Service
**Endpoint:** `GET /v1/supply-chain/track/{case_id}`
- **Description:** Retrieves the current state and history of a legal supply chain.
- **Request:** Path parameter `case_id`.
- **Response:** `200 OK {"case_id": "C-123", "status": "In-Review", "history": [...]}`

**Endpoint:** `PATCH /v1/supply-chain/update-status`
- **Description:** Updates the status of a specific item in the chain.
- **Request:** `{"item_id": "item-99", "new_status": "Completed", "user_id": "user-1"}`
- **Response:** `200 OK {"updated_at": "..."}`

### 4.3 Document Service
**Endpoint:** `POST /v1/docs/upload`
- **Description:** Initiates a secure file upload.
- **Request:** Multipart form-data containing file and `case_id`.
- **Response:** `202 Accepted {"upload_id": "up-555", "status": "Scanning"}`

**Endpoint:** `GET /v1/docs/download/{doc_id}`
- **Description:** Generates a signed URL for a document.
- **Request:** Path parameter `doc_id`.
- **Response:** `200 OK {"download_url": "https://storage.googleapis.com/...signed-url"}`

### 4.4 Localization Service
**Endpoint:** `GET /v1/locale/strings?lang=fr`
- **Description:** Fetches all translation keys for a specific language.
- **Request:** Query param `lang`.
- **Response:** `200 OK {"SUPPLY_CHAIN_STATUS": "État de la chaîne d'approvisionnement", ...}`

**Endpoint:** `PUT /v1/locale/strings`
- **Description:** Allows an admin to update a translation string.
- **Request:** `{"lang": "fr", "key": "STATUS", "value": "Nouvelle Valeur"}`
- **Response:** `200 OK`

---

## 5. DATABASE SCHEMA (CockroachDB)

### 5.1 Table Definitions

| Table Name | Key Field | Type | Description | Relationships |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID) | Primary | User account details | 1:N with `user_roles` |
| `roles` | `role_id` (INT) | Primary | Definition of roles (Admin, Auditor, etc) | 1:N with `user_roles` |
| `user_roles` | `id` (UUID) | Primary | Mapping users to roles | FK `user_id`, `role_id` |
| `cases` | `case_id` (UUID) | Primary | Legal case container | 1:N with `supply_chain_items` |
| `supply_chain_items` | `item_id` (UUID) | Primary | Specific deliverable in the chain | FK `case_id` |
| `item_history` | `history_id` (UUID) | Primary | Immutable log of status changes | FK `item_id` |
| `documents` | `doc_id` (UUID) | Primary | File metadata and storage path | FK `case_id` |
| `user_preferences` | `user_id` (UUID) | Primary/FK | User dashboard layout JSON | FK `user_id` |
| `locales` | `lang_code` (STR) | Primary | List of supported language codes | 1:N with `translations` |
| `translations` | `trans_id` (UUID) | Primary | Key-value pairs for translations | FK `lang_code` |

### 5.2 Key Relationships
- **The Audit Trail:** `supply_chain_items` $\rightarrow$ `item_history`. Any update to an item creates a new row in `item_history` via a database trigger or service-level event.
- **Permissioning:** `users` $\rightarrow$ `user_roles` $\rightarrow$ `roles`. A user can have multiple roles, and the most permissive role is applied.
- **Localization:** `locales` $\rightarrow$ `translations`. Each translation is tied to a locale code (e.g., 'en-US').

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Cairn employs a strict **Continuous Deployment (CD)** pipeline. Every PR merged into the `main` branch is automatically deployed to production.

#### 6.1.1 Development (Dev)
- **Purpose:** Local feature development and unit testing.
- **Infrastructure:** Local Kubernetes (minikube) or shared Dev namespace in GKE.
- **Database:** Single-node CockroachDB.
- **Deployment:** Manual trigger via `git push`.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing and QA. Mirrors Production exactly.
- **Infrastructure:** GKE Cluster (Small).
- **Database:** 3-node CockroachDB cluster.
- **Deployment:** Automatic on merge to `develop` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live legal operations.
- **Infrastructure:** GKE Cluster (Autoscaling, Multi-zonal).
- **Database:** Multi-region CockroachDB with data pinning for EU residency.
- **Deployment:** Automatic on merge to `main`.

### 6.2 CI/CD Pipeline
1. **Commit:** Developer pushes code to GitHub.
2. **Lint/Test:** GitHub Actions runs `go test` and `golangci-lint`.
3. **Build:** Docker image is built and pushed to Google Artifact Registry.
4. **Deploy:** Helm chart updates the GKE deployment.
5. **Health Check:** Kubernetes Liveness/Readiness probes verify the service. If they fail, the deployment is automatically rolled back.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Each microservice must maintain $\ge 80\%$ code coverage. Go's `testing` package is used for logic verification. Mocking of the database is handled via `sqlmock`.

### 7.2 Integration Testing
Since the system relies on Kafka and gRPC, integration tests are conducted using **Testcontainers**. A real instance of Kafka and CockroachDB is spun up in a Docker container during the test phase to verify that the `Supply Chain Service` correctly consumes events and writes to the DB.

### 7.3 End-to-End (E2E) Testing
Critical user journeys (e.g., "User logs in $\rightarrow$ Uploads Document $\rightarrow$ Updates Status $\rightarrow$ Auditor Verifies") are tested using Playwright. These tests run against the Staging environment before any PR is merged to `main`.

### 7.4 Compliance Testing
A dedicated "Compliance Audit" test suite runs weekly, verifying that no data tagged as `EU_RESIDENT` is stored on nodes located in the US region.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Integration partner's API is undocumented/buggy | High | High | **Parallel-Path:** Prototype an alternative integration approach/wrapper simultaneously. |
| **R2** | Project sponsor is rotating out of role | Medium | High | **Executive Escalation:** Raise as a critical blocker in the next board meeting to secure a successor. |
| **R3** | Budget overrun due to GCP costs | Medium | Medium | **Strict Monitoring:** Implement GCP budgets and alerts; use preemptible nodes for non-critical workers. |
| **R4** | Hard legal deadline missed | Low | Critical | **Priority Shaving:** Move "Nice to have" features (File Upload) to Phase 2. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure.
- **High:** Significant delay or budget hit.
- **Medium:** Manageable with effort.

---

## 9. TIMELINE & MILESTONES

The project follows an aggressive 6-month trajectory.

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Months 1-2):** Focus on Auth, RBAC, and basic Database schema.
- **Phase 2: Core Logic (Months 3-4):** Implementation of Supply Chain tracking and Localization.
- **Phase 3: Refinement (Months 5-6):** Collaborative editing, Dashboard, and Final Compliance Audit.

### 9.2 Gantt-Style Roadmap
- **Oct 2024 - Nov 2024:** Architecture Design $\rightarrow$ Auth Service Dev $\rightarrow$ CI/CD Pipeline Setup.
- **Dec 2024 - Jan 2025:** Supply Chain Logic $\rightarrow$ Integration with Partner API (R1 Mitigation) $\rightarrow$ Localization.
- **Feb 2025:** **Milestone 1: First paying customer onboarded (Target: 2025-03-15).**
- **Mar 2025 - Apr 2025:** Collaborative Editing $\rightarrow$ Dashboard (once unblocked) $\rightarrow$ E2E Testing.
- **May 2025:** **Milestone 2: Architecture review complete (Target: 2025-05-15).**
- **Jun 2025:** Final Hardening $\rightarrow$ GDPR Compliance Audit $\rightarrow$ Performance Tuning.
- **Jul 2025:** **Milestone 3: MVP feature-complete (Target: 2025-07-15).**

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff & Budget Alignment
**Date:** 2024-10-01  
**Attendees:** Rosa Kim, Ira Costa, Zia Costa, Luciano Stein  
**Notes:**
- Rosa emphasized the "shoestring" budget of $150k. Every GCP resource must be optimized.
- The hard legal deadline in 6 months is non-negotiable.
- Team agreed to a formal communication style: JIRA for all tasks, no "verbal" agreements.
- Luciano (Intern) assigned to support Ira with CockroachDB schema migrations.

**Action Items:**
- [Rosa] Finalize GCP Project billing account. (Owner: Rosa)
- [Ira] Draft initial DB schema. (Owner: Ira)
- [Zia] Create UX wireframes for RBAC flow. (Owner: Zia)

---

### Meeting 2: Integration Risk Assessment
**Date:** 2024-11-15  
**Attendees:** Rosa Kim, Ira Costa  
**Notes:**
- Ira reported that the partner's API is returning inconsistent 500 errors and the documentation is outdated.
- This is identified as **Risk 1**.
- Decision: We will not wait for the partner to fix their API. Ira will build a "Compatibility Layer" that handles retries and fallback mocks.
- Parallel-path approach: Ira will investigate if a third-party aggregator can replace the partner entirely.

**Action Items:**
- [Ira] Create a prototype of the Compatibility Layer. (Owner: Ira)
- [Rosa] Reach out to partner's CTO to express urgency. (Owner: Rosa)

---

### Meeting 3: Blocker & Sponsor Discussion
**Date:** 2024-12-10  
**Attendees:** Rosa Kim, Zia Costa, Ira Costa  
**Notes:**
- **Current Blocker:** The "Identity Provider" team is 3 weeks behind on the shared library we need. This is delaying the Auth Service.
- **Sponsor Risk:** Rosa noted that the project sponsor is likely rotating out of their role. This puts our budget at risk if the new sponsor doesn't value the project.
- Decision: Rosa will move this to the "Board Meeting" agenda for the next session to secure a commitment from the incoming sponsor.

**Action Items:**
- [Rosa] Add "Project Cairn Funding" to Board Meeting Agenda. (Owner: Rosa)
- [Ira] Implement a local mock for the Identity Provider to avoid further blocking. (Owner: Ira)

---

## 11. BUDGET BREAKDOWN

Total Budget: **$150,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Covers core team and intern stipend. |
| **Infrastructure** | 20% | $30,000 | GCP GKE, CockroachDB Cloud, Kafka managed service. |
| **Tools & Licenses** | 10% | $15,000 | JIRA, GitHub Enterprise, Snyk for security scanning. |
| **Contingency** | 10% | $15,000 | Emergency buffer for R1/R2 mitigation. |

**Budgetary Constraint Note:** No additional hires are permitted. If the workload exceeds capacity, features must be descoped (Priority: Low/Medium).

---

## 12. APPENDICES

### Appendix A: gRPC Protocol Buffer Definition
Example of the `.proto` definition for the Supply Chain service:

```protobuf
syntax = "proto3";

package cairn.supplychain;

service SupplyChainService {
  rpc GetItemStatus (ItemRequest) returns (ItemResponse);
  rpc UpdateItemStatus (UpdateStatusRequest) returns (UpdateStatusResponse);
}

message ItemRequest {
  string item_id = 1;
  string case_id = 2;
}

message ItemResponse {
  string item_id = 1;
  string current_status = 2;
  repeated StatusChange history = 3;
}

message StatusChange {
  string status = 1;
  string timestamp = 2;
  string user_id = 3;
}

message UpdateStatusRequest {
  string item_id = 1;
  string new_status = 2;
  string user_id = 3;
}

message UpdateStatusResponse {
  bool success = 1;
  string updated_at = 2;
}
```

### Appendix B: GDPR Data Mapping
To ensure compliance, the following mapping is used for CockroachDB `REGIONAL BY ROW` configuration:

- **EU-West-1 (Ireland):** All rows where `client_region == 'EU'`.
- **US-East-1 (N. Virginia):** All rows where `client_region == 'US'`.
- **Global:** `roles`, `locales`, and `translations` tables are replicated globally for performance.

**Compliance Check Procedure:**
The `Audit Log Service` will run a weekly script:
`SELECT count(*) FROM users WHERE region = 'EU' AND node_location != 'eu-west-1';`
If the result is $> 0$, an immediate alert is sent to Rosa Kim and the compliance officer.