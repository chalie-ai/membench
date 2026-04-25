# PROJECT SPECIFICATION DOCUMENT: DRIFT (V1.0.4)
**Company:** Stormfront Consulting  
**Industry:** Food and Beverage (F&B)  
**Classification:** Confidential / HIPAA Compliant  
**Date:** October 24, 2025  
**Document Owner:** Lior Fischer (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Drift" represents a critical strategic pivot for Stormfront Consulting. Following the launch of the legacy collaboration suite for the Food and Beverage sector, the organization faced catastrophic user feedback. Market research and churn analysis indicated that the previous iteration failed to meet the high-velocity demands of F&B supply chain management and menu coordination. The legacy system suffered from severe latency, a non-intuitive UI, and a lack of critical search capabilities, leading to a net promoter score (NPS) of -42.

The F&B industry requires a tool that can handle real-time updates to inventory, recipe changes, and compliance documentation across distributed sites. Drift is not merely a feature update but a complete product rebuild. The objective is to transition from a static document repository to a dynamic, real-time collaboration environment where stakeholders—from executive chefs to procurement officers—can synchronize data instantly.

### 1.2 ROI Projection and Success Metrics
The financial stakes for Drift are high, given the shoestring budget of $150,000. However, the projected Return on Investment (ROI) is anchored in two primary KPIs:
1. **Revenue Generation:** The project must attribute $500,000 in new revenue within 12 months post-launch. This will be achieved through a tiered subscription model targeting mid-to-large scale F&B enterprises.
2. **User Acquisition:** A target of 10,000 Monthly Active Users (MAU) within 6 months of the general release.

The ROI is calculated based on the reduction of churn (estimated 30% recovery of lost legacy users) and the acquisition of new enterprise contracts. By shifting to a modern hexagonal architecture and ensuring HIPAA compliance (essential for managing employee health data and food safety certifications), Stormfront Consulting will regain market trust and establish a scalable foundation for future growth.

### 1.3 Project Scope
Drift will provide a secure, on-premise hosted environment facilitating real-time document editing, advanced search, and secure identity management. The scope is strictly limited to the five priority features outlined in this document to prevent scope creep and ensure adherence to the rigid deployment train.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
To ensure the system remains maintainable and decoupled from its infrastructure, Drift utilizes a Hexagonal Architecture. This is critical given the strict requirement for on-premise deployment and the use of an Oracle DB, which can often lead to tight coupling if not managed.

**Core Logic (The Domain):** The center of the hexagon contains the business rules (e.g., conflict resolution logic for real-time editing, search indexing rules). It has no knowledge of the database or the web framework.
**Ports:** Interfaces that define how the core logic interacts with the outside world (e.g., `UserRepositoryPort`, `DocumentRepositoryPort`).
**Adapters:** Implementations of the ports. 
- *Driving Adapters:* Spring Boot REST Controllers that translate HTTP requests into domain calls.
- *Driven Adapters:* Oracle DB persistence layers that translate domain entities into SQL queries.

### 2.2 ASCII Architecture Diagram
```text
[ External Clients ] <--- HTTPS/TLS 1.3 ---> [ API Gateway/Load Balancer ]
                                                       |
                                                       v
            _______________________________________________________________________
           |                          SPRING BOOT APPLICATION                     |
           |                                                                        |
           |  [ Driving Adapters ] ----> [ Application Ports ] ----> [ Domain Core ] |
           |  (REST Controllers)       (Service Interfaces)       (Business Logic) |
           |          ^                                                     |       |
           |          |                                                     v       |
           |  [ Driven Adapters ] <---- [ Infrastructure Ports ] <---- [ Entities ]    |
           |  (Oracle JPA/Hibernate)    (Repository Interfaces)                     |
           |_______________________________________________________________________|
                                                       |
                                                       v
                                            [ On-Premise Oracle DB ]
                                            (AES-256 Encrypted at Rest)
                                            (Strict HIPAA Partitioning)
```

### 2.3 Technical Stack
- **Language:** Java 17 (LTS)
- **Framework:** Spring Boot 3.2.x
- **Database:** Oracle Database 19c (Enterprise Edition)
- **Hosting:** Stormfront On-Premise Data Center (Air-gapped from public cloud)
- **Security:** TLS 1.3 for transit; AES-256 for rest.
- **Communication:** WebSockets (STOMP) for real-time synchronization.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: Critical)
**Status:** Complete | **Impact:** Launch Blocker

The search functionality is the cornerstone of Drift, designed to replace the failed search mechanisms of the previous version. It allows users to query massive datasets of F&B recipes, compliance logs, and procurement contracts using full-text indexing.

**Detailed Requirements:**
- **Full-Text Indexing:** Implementation of an inverted index within the Oracle database using Oracle Text. Every document upload triggers an asynchronous indexing job.
- **Faceted Filtering:** Users must be able to narrow results by "Department" (e.g., Kitchen, Logistics), "Date Range," "Author," and "Document Status" (Draft, Approved, Archived).
- **Query Logic:** Support for Boolean operators (AND, OR, NOT) and wildcard searching.
- **Performance:** Search results must return in under 200ms for a dataset of 1 million records.
- **Integration:** The search adapter must decouple the query from the domain to allow for future migration to an external search engine (like Elasticsearch) if the on-premise Oracle Text performance degrades.

### 3.2 Real-Time Collaborative Editing with Conflict Resolution (Priority: Medium)
**Status:** Complete | **Impact:** Core Value Prop

This feature allows multiple users to edit a single document simultaneously, essential for menu planning and safety audits.

**Detailed Requirements:**
- **Concurrency Model:** Implementation of Operational Transformation (OT). Every change is treated as an "operation" (Insert, Delete, Retain) sent via WebSockets.
- **Conflict Resolution:** When two users edit the same character index, the OT engine resolves the state based on the server-assigned timestamp.
- **Presence Indicators:** Real-time cursor tracking and user avatars showing who is currently active in the document.
- **State Synchronization:** The system must maintain a "Shadow Document" on the server to validate operations before broadcasting them to other clients.
- **Latency Mitigation:** Local optimistic updates are applied immediately to the UI, with a rollback mechanism if the server rejects the operation.

### 3.3 API Rate Limiting and Usage Analytics (Priority: High)
**Status:** Blocked | **Impact:** System Stability

To prevent system abuse and provide data for the $500K revenue target, Drift requires a robust rate-limiting layer.

**Detailed Requirements:**
- **Token Bucket Algorithm:** Implementation of a token bucket to limit requests per API key. Limits are tiered based on the user's subscription level (e.g., Basic: 100 req/min, Enterprise: 5000 req/min).
- **Analytics Engine:** A background process that captures request metadata (endpoint, response time, status code, user ID) and stores it in a dedicated analytics table.
- **Dashboard Integration:** Data must be exportable to CSV for the business team to analyze usage patterns.
- **Blocking Status:** Currently blocked due to the absence of the primary Data Engineer (Noor Jensen) on medical leave; the implementation of the bucket logic depends on the specific Oracle partitioning strategy Noor was designing.

### 3.4 SSO Integration with SAML and OIDC (Priority: Medium)
**Status:** Blocked | **Impact:** Enterprise Adoption

Enterprise F&B clients require a single sign-on (SSO) mechanism to manage employees across large franchises.

**Detailed Requirements:**
- **SAML 2.0:** Support for Service Provider (SP) initiated SSO, allowing integration with Azure AD and Okta.
- **OIDC:** Implementation of OpenID Connect for modern authentication flows.
- **User Provisioning:** Just-In-Time (JIT) provisioning to create user profiles in the Oracle DB upon the first successful SSO login.
- **Security Mapping:** Mapping of SAML assertions to internal Drift roles (Admin, Editor, Viewer).
- **Blocking Status:** Blocked pending the security audit of the on-premise network's ability to handle external callbacks from OIDC providers.

### 3.5 File Upload with Virus Scanning and CDN Distribution (Priority: Low)
**Status:** Not Started | **Impact:** Nice-to-Have

This feature allows the upload of large PDFs (Health codes, Manuals) with a layer of security and optimized delivery.

**Detailed Requirements:**
- **Virus Scanning:** Integration with an on-premise ClamAV instance. No file is committed to permanent storage until the scan returns a "Clean" status.
- **CDN Strategy:** Since cloud CDNs are forbidden, this involves the deployment of regional internal proxy caches within the company's data centers to reduce latency.
- **Chunked Uploads:** Support for multipart uploads to handle files up to 500MB without timing out the Spring Boot connection.
- **Metadata Extraction:** Automatic extraction of file size, type, and checksum for auditing.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is required via Bearer Token in the header.

### 4.1 Search Documents
- **Endpoint:** `GET /search`
- **Description:** Performs a full-text search with faceted filters.
- **Request Parameters:**
    - `q` (string): Search query.
    - `dept` (string): Filter by department.
    - `start_date` (ISO-8601): Start range.
- **Example Request:** `GET /api/v1/search?q=salmon+recipe&dept=Kitchen`
- **Example Response:**
  ```json
  {
    "results": [
      {"doc_id": "101", "title": "Atlantic Salmon Grill", "relevance": 0.98}
    ],
    "facets": { "departments": {"Kitchen": 12, "Procurement": 2} }
  }
  ```

### 4.2 Create Document Session
- **Endpoint:** `POST /docs/session`
- **Description:** Initializes a real-time collaboration session.
- **Request Body:** `{"doc_id": "101", "user_id": "user_77"}`
- **Example Response:**
  ```json
  {
    "session_id": "sess_abc123",
    "websocket_url": "wss://drift.stormfront.local/ws/101"
  }
  ```

### 4.3 Apply Document Operation
- **Endpoint:** `POST /docs/op`
- **Description:** Submits an OT operation for conflict resolution.
- **Request Body:** `{"session_id": "sess_abc123", "op": "insert", "pos": 12, "char": "a", "version": 45}`
- **Example Response:**
  ```json
  { "status": "applied", "new_version": 46 }
  ```

### 4.4 Get User Usage Analytics
- **Endpoint:** `GET /analytics/usage/{userId}`
- **Description:** Returns total API calls and data transferred for a user.
- **Example Response:**
  ```json
  {
    "user_id": "user_77",
    "requests_24h": 450,
    "bandwidth_mb": 12.5
  }
  ```

### 4.5 SSO Initiation
- **Endpoint:** `GET /auth/sso/init`
- **Description:** Triggers the SAML/OIDC authentication flow.
- **Request Parameters:** `provider=azure`
- **Example Response:** `302 Redirect to Azure AD Login Page`

### 4.6 File Upload (Pre-scan)
- **Endpoint:** `POST /files/upload`
- **Description:** Uploads a file to the temporary virus-scanning buffer.
- **Request Body:** Multipart form data.
- **Example Response:**
  ```json
  { "file_id": "tmp_999", "status": "scanning" }
  ```

### 4.7 Get File Status
- **Endpoint:** `GET /files/status/{fileId}`
- **Description:** Checks if the virus scan is complete.
- **Example Response:**
  ```json
  { "file_id": "tmp_999", "status": "clean", "url": "/cdn/files/doc_101.pdf" }
  ```

### 4.8 Update Rate Limit Tier
- **Endpoint:** `PATCH /admin/limits/{userId}`
- **Description:** Manually overrides the rate limit for a specific user (Admin only).
- **Request Body:** `{"limit": 10000}`
- **Example Response:** `{"status": "updated"}`

---

## 5. DATABASE SCHEMA (ORACLE DB)

The database is designed for high availability and HIPAA compliance. All tables use `VARCHAR2` and `NUMBER` types standard to Oracle 19c.

### 5.1 Tables and Relationships

| Table Name | Key Fields | Description | Relationship |
| :--- | :--- | :--- | :--- |
| `USERS` | `USER_ID (PK)`, `EMAIL`, `SAML_UID`, `ROLE` | User identity and access level. | 1:N with `SESSIONS` |
| `DOCUMENTS` | `DOC_ID (PK)`, `TITLE`, `CONTENT_CLOB`, `VERSION` | Main document storage. | 1:N with `OPERATIONS` |
| `OPERATIONS` | `OP_ID (PK)`, `DOC_ID (FK)`, `USER_ID (FK)`, `OP_DATA` | Log of every edit for OT resolution. | N:1 with `DOCUMENTS` |
| `SESSIONS` | `SESS_ID (PK)`, `USER_ID (FK)`, `DOC_ID (FK)`, `START_TIME` | Active real-time sessions. | N:1 with `USERS` |
| `PERMISSIONS` | `PERM_ID (PK)`, `USER_ID (FK)`, `DOC_ID (FK)`, `LEVEL` | Access control list (ACL). | N:M (Users $\leftrightarrow$ Docs) |
| `SEARCH_INDEX` | `INDEX_ID (PK)`, `DOC_ID (FK)`, `TERM`, `POSITION` | Manual index for faceted search. | N:1 with `DOCUMENTS` |
| `API_LOGS` | `LOG_ID (PK)`, `USER_ID (FK)`, `ENDPOINT`, `TIMESTAMP` | Usage analytics tracking. | N:1 with `USERS` |
| `RATE_LIMITS` | `USER_ID (PK/FK)`, `TOKEN_BUCKET`, `REFILL_RATE` | Current state of rate limiting. | 1:1 with `USERS` |
| `FILE_METADATA` | `FILE_ID (PK)`, `DOC_ID (FK)`, `SCAN_STATUS`, `PATH` | Tracking uploaded assets. | N:1 with `DOCUMENTS` |
| `AUDIT_TRAIL` | `AUDIT_ID (PK)`, `USER_ID (FK)`, `ACTION`, `IP_ADDR` | HIPAA required access logs. | N:1 with `USERS` |

### 5.2 HIPAA Encryption Constraints
All tables containing Personally Identifiable Information (PII) are stored in a Tablespace encrypted with Oracle Transparent Data Encryption (TDE). The `CONTENT_CLOB` in the `DOCUMENTS` table is encrypted using an application-level AES-256 key managed by a hardware security module (HSM) in the on-premise data center.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Layout
Drift is hosted entirely on-premise. There is no cloud connectivity to ensure maximum security for F&B corporate secrets and HIPAA compliance.

- **Development Environment (DEV):** 
    - Localized Spring Boot instances.
    - H2 In-memory database for unit testing.
    - Mock-SAML provider for SSO testing.
- **Staging Environment (STG):** 
    - Mirror of production hardware.
    - Single-instance Oracle DB.
    - Used for Milestone 2 (External Beta).
- **Production Environment (PROD):** 
    - RAC (Real Application Clusters) for Oracle DB.
    - High-availability Spring Boot cluster behind a F5 Load Balancer.
    - Strictly air-gapped from public internet; access via corporate VPN only.

### 6.2 The Release Train
The project follows a **Weekly Release Train** model.
- **Cycle:** Monday (Freeze) $\rightarrow$ Tuesday-Thursday (QA/Regressions) $\rightarrow$ Friday 02:00 AM (Deployment).
- **No Hotfixes:** If a bug is found on Friday afternoon, it cannot be patched until the following Friday's train. This ensures that the strict HIPAA audit trail is never bypassed by "emergency" changes.
- **Pipeline:** Git $\rightarrow$ Jenkins (On-Prem) $\rightarrow$ Maven Build $\rightarrow$ Artifact Repository $\rightarrow$ Deployment Script.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Domain logic and OT conflict resolution.
- **Tooling:** JUnit 5 and Mockito.
- **Requirement:** 80% code coverage on all classes within the "Domain Core" hexagon.

### 7.2 Integration Testing
- **Focus:** Port/Adapter communication.
- **Method:** Using `@SpringBootTest` with Testcontainers for Oracle DB to ensure SQL queries are compatible with Oracle 19c syntax.
- **Scope:** Testing the flow from REST Controller $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ DB.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Real-time collaboration and Search.
- **Tooling:** Selenium and Playwright.
- **Scenario:** "User A and User B open the same document $\rightarrow$ both type simultaneously $\rightarrow$ verify consistent state $\rightarrow$ search for the typed keyword $\rightarrow$ verify result appears."

### 7.4 HIPAA Compliance Testing
- **Vulnerability Scanning:** Weekly scans using Nessus.
- **Encryption Audit:** Verification that data is encrypted both during transit (TLS check) and at rest (DB table decryption attempt without key).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Scope creep from F&B stakeholders adding "small" features. | High | High | **Parallel-path:** Prototype alternative approaches simultaneously to show the cost of change. |
| R2 | Key architect leaving company in 3 months. | Medium | High | **Knowledge Transfer:** Document all architectural workarounds and share in a central wiki. |
| R3 | Budget exhaustion due to Oracle licensing costs. | Medium | Medium | Strict monitoring of resource usage; use of minimal CPU cores for DB. |
| R4 | Medical leave of Noor Jensen (Current Blocker). | Actual | High | Shift focus to the "Complete" features (Search, OT) and delay Rate Limiting implementation. |
| R5 | On-premise hardware failure. | Low | High | Implementation of Oracle Data Guard for failover. |

**Probability/Impact Matrix:**
- High/High $\rightarrow$ Critical (R1)
- Medium/High $\rightarrow$ Major (R2)
- Low/High $\rightarrow$ Moderate (R5)

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase-Based Gantt Description

**Phase 1: Core Stabilization (Current - July 2026)**
- *Dependencies:* Fix hardcoded config values (Tech Debt).
- *Activities:* Finalize OT conflict resolution, optimize Oracle Text search.
- **Milestone 1: Security audit passed (Target: 2026-07-15)**

**Phase 2: Integration & Beta (July 2026 - September 2026)**
- *Dependencies:* Completion of SSO (once unblocked).
- *Activities:* Deploy to Staging, onboard pilot users, refine UI based on beta feedback.
- **Milestone 2: External beta with 10 pilot users (Target: 2026-09-15)**

**Phase 3: Validation & Launch (September 2026 - November 2026)**
- *Dependencies:* Final HIPAA sign-off.
- *Activities:* Load testing for 10k MAU, final bug scrubbing, stakeholder walkthrough.
- **Milestone 3: Stakeholder demo and sign-off (Target: 2026-11-15)**

---

## 10. MEETING NOTES

*Note: These excerpts are taken from the shared running document (currently 200 pages long and unsearchable).*

### Meeting 1: 2025-11-02 (Project Kickoff)
**Attendees:** Lior, Noor, Vivaan, Elio.
- **Lior:** Emphasized the $150k budget. "We cannot afford a single cloud instance. Everything must stay on our servers."
- **Vivaan:** Concerned about the "catastrophic feedback" on the old UI. Suggested a complete overhaul of the navigation.
- **Noor:** Warned that the Oracle DB version in the data center is aging. Suggested moving to 19c immediately.
- **Decision:** Adopt Hexagonal Architecture to ensure we can swap the DB if the on-premise hardware fails.

### Meeting 2: 2026-01-15 (The Technical Debt Crisis)
**Attendees:** Lior, Vivaan, Elio (Noor absent).
- **Elio:** Reported that he found hardcoded IP addresses and database credentials in over 40 different Java files. "It's a nightmare to move to staging."
- **Lior:** Confirmed the tech debt is a priority. "Elio, spend the next two weeks moving these to `application.properties` and encrypted environment variables."
- **Vivaan:** Asked if the search feature is actually done. Lior confirmed it's complete and a launch blocker.
- **Decision:** Prioritize the "Configuration Cleanup" sprint before the next release train.

### Meeting 3: 2026-04-10 (The Blocker Update)
**Attendees:** Lior, Vivaan, Elio.
- **Lior:** Announced that Noor is on medical leave for 6 weeks. 
- **Vivaan:** "The rate limiting and usage analytics are now completely blocked. We can't implement the token bucket without Noor's data schema."
- **Lior:** "We can't push the date. We will shift focus to the SSO integration and the file upload system. Elio, try to pick up the basic Java implementation of the rate limiter, but don't touch the DB until Noor returns."
- **Decision:** Pivot development focus to non-blocked features to maintain the release train velocity.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$150,000** (Fixed)

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $90,000 | 4-person team (including Intern Elio) for 12 months. |
| **Infrastructure** | $30,000 | Oracle Licensing, On-premise Server Maintenance, HSM hardware. |
| **Tools** | $10,000 | IntelliJ IDEA licenses, Jenkins plugins, Nessus vulnerability scanner. |
| **Contingency** | $20,000 | Buffer for emergency hardware replacement or external audit fees. |

**Budget Scrutiny Note:** Every dollar is tracked. Any spend over $500 requires direct sign-off from Lior Fischer.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (OT)
The Operational Transformation (OT) system uses a centralized server approach.
1. **Client A** sends operation $Op_A$ at version $V_1$.
2. **Client B** sends operation $Op_B$ at version $V_1$.
3. **Server** receives $Op_A$ first, applies it, and increments version to $V_2$.
4. **Server** receives $Op_B$. Since $Op_B$ was based on $V_1$, the server transforms $Op_B$ relative to $Op_A$ to create $Op_{B'}$.
5. **Server** applies $Op_{B'}$ and broadcasts both $Op_A$ and $Op_{B'}$ to all clients.
6. **Client B** receives $Op_A$, transforms it against their own $Op_B$, and updates the local state.

### Appendix B: HIPAA Encryption Standard Implementation
To meet HIPAA requirements for the F&B sector (specifically for handling employee health certifications and food-borne illness reports):
- **Data at Rest:** Oracle TDE (Transparent Data Encryption) is enabled for the `USERS` and `DOCUMENTS` tablespaces. The Master Encryption Key (MEK) is rotated every 90 days.
- **Data in Transit:** All internal traffic is routed through TLS 1.3. Certificates are issued by the Stormfront Internal CA.
- **Access Control:** Implement Role-Based Access Control (RBAC). The `AUDIT_TRAIL` table is append-only; no user, including the DBA, has `DELETE` or `UPDATE` permissions on this table.