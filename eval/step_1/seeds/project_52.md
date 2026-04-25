# PROJECT SPECIFICATION: PROJECT CITADEL
**Document Version:** 1.0.4  
**Date:** October 24, 2024  
**Status:** Approved / Baseline  
**Project Lead:** Hessa Park (VP of Product)  
**Classification:** Confidential – Oakmount Group Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Citadel represents a strategic pivot for Oakmount Group, transitioning from traditional educational services into a high-value, AI-driven product vertical. The project involves the deployment of a sophisticated machine learning model designed to provide predictive educational analytics and real-time content optimization for enterprise-level educational institutions. 

The primary driver for Citadel is a single, high-value enterprise client—a global education conglomerate—that has committed to an annual recurring revenue (ARR) of $2,000,000 upon successful deployment of the MVP. This provides a powerful incentive for Oakmount Group to establish a foothold in this market, as the client’s adoption serves as a definitive case study for further market expansion.

### 1.2 Business Justification
The education sector is currently undergoing a digital transformation where static learning materials are being replaced by adaptive learning systems. The "Citadel" model leverages proprietary ML algorithms to personalize learning paths in real-time, filling a gap in the current market for secure, on-premise, enterprise-grade deployments.

Given the extreme sensitivity of student data, the client has mandated a strict on-premise deployment. This architectural constraint creates a competitive moat; while many SaaS competitors offer cloud-based ML, few can offer the security and residency guarantees of a local Oracle-backed, Spring Boot environment.

### 1.3 ROI Projection and Financials
The project is allocated a modest but focused budget of $400,000. This budget covers the development cycle from inception to the production launch on July 15, 2025. 

**Projected Return on Investment (ROI):**
- **Direct Revenue:** $2,000,000 ARR starting Q3 2025.
- **Development Cost:** $400,000 (One-time).
- **Year 1 Net Gain:** $1,600,000.
- **ROI Ratio:** 400% in the first year post-launch.

The ROI is exceptionally high due to the "single-client anchor" model. Once the infrastructure is built and the ML model is tuned to the client's specific data residency needs, the marginal cost of supporting the client is low, allowing the majority of the ARR to flow directly to the bottom line.

### 1.4 Strategic Goals
1. **Market Entry:** Successfully transition Oakmount Group into the ML-driven education vertical.
2. **Compliance Leadership:** Establish a gold standard for GDPR and CCPA compliance in on-premise ML deployments.
3. **Operational Excellence:** Implement a rigorous weekly release train to ensure stability and predictability in a distributed team environment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Overview
Project Citadel utilizes a traditional three-tier architecture to ensure maximum stability, maintainability, and compliance with the client's strict on-premise requirements. No cloud services (AWS, Azure, GCP) are permitted.

**Tier 1: Presentation Layer**
A React-based frontend communicating via RESTful APIs. The frontend is served as static assets from an on-premise Nginx server.

**Tier 2: Business Logic Layer (The Application Server)**
Built on **Java 17** and **Spring Boot 3.2**. This layer handles the ML model orchestration, user authentication, and business rules. The ML model is integrated via a JNI (Java Native Interface) wrapper or a sidecar C++ process to handle the heavy tensor computations, ensuring that the Spring Boot layer remains responsive.

**Tier 3: Data Layer**
A robust **Oracle Database 19c** instance. All data persists on physical hardware located within the client's EU-based data centers to satisfy GDPR residency requirements.

### 2.2 ASCII Architecture Diagram
```text
[ USER BROWSER ] <--- HTTPS/TLS 1.3 ---> [ NGINX REVERSE PROXY ]
                                                 |
                                                 v
                                     [ SPRING BOOT APP SERVER ]
                                     /             |            \
                (Auth/Logic) <--- /               | \ ---> (ML Model Engine)
                      |                           |                |
                      |                           |                |
                      v                           v                v
             [ ORACLE DB 19c ] <------------------/         [ LOCAL FILE SYSTEM ]
             (Data Residency: EU)                           (Model Weights/Logs)
```

### 2.3 Technical Constraints
- **No Cloud:** All components must reside on physical hardware provided by the client.
- **Strict Versioning:** All libraries must be pinned to specific versions to prevent "dependency drift" across the distributed team.
- **Data Residency:** No data may leave the EU boundaries. All backups and logs must be stored on local encrypted disks.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Not Started
*   **Description:** Users must be able to collaborate on educational content in real-time. This requires a synchronization mechanism that handles simultaneous edits without data loss.
*   **Detailed Specifications:**
    *   **Concurrency Model:** The system will implement Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs). Given the requirement for a "single source of truth" in the Oracle DB, a centralized OT server within the Spring Boot application is preferred.
    *   **Websocket Integration:** A dedicated `/ws/collab` endpoint will be established using STOMP over WebSockets. 
    *   **Conflict Resolution:** In the event of a race condition (two users editing the same character index), the server will timestamp the operations and apply the "last write wins" rule for metadata, but use OT for text insertion/deletion to ensure no content is erased.
    *   **State Management:** The frontend will maintain a local "shadow" copy of the document. Changes are pushed as small "deltas" rather than full document uploads to minimize bandwidth.
    *   **Locking Mechanism:** To prevent extreme conflicts, the system will implement "soft locking" where a user's cursor position is visible to others, signaling an intent to edit a specific block.
*   **Acceptance Criteria:** Two users in different countries can edit the same text block simultaneously with <200ms latency and zero data loss upon synchronization.

### 3.2 Offline-First Mode with Background Sync
*   **Priority:** Low (Nice to Have)
*   **Status:** In Design
*   **Description:** Allows educators to continue working on content in areas of poor connectivity, with data syncing automatically once a connection is restored.
*   **Detailed Specifications:**
    *   **Client-Side Storage:** Use IndexedDB to store a local cache of the user's current work-in-progress.
    *   **Sync Queue:** A local queue of "pending mutations" will be maintained. Each mutation is assigned a UUID and a sequence number.
    *   **Background Worker:** Use a Service Worker to detect "online" events. Upon reconnection, the worker will trigger a `POST /api/v1/sync` request containing the mutation queue.
    *   **Reconciliation Logic:** The server will validate the sequence numbers. If the server version is significantly ahead, it will trigger a "Merge Conflict" UI, forcing the user to choose between the local and server version.
    *   **Storage Limits:** The offline cache will be limited to 50MB per user to prevent browser performance degradation.
*   **Acceptance Criteria:** User can make 10 edits while offline; upon reconnection, all 10 edits are applied to the Oracle DB in the correct chronological order.

### 3.3 Customer-Facing API with Versioning and Sandbox
*   **Priority:** Medium
*   **Status:** Blocked (Waiting on Legal)
*   **Description:** A set of REST APIs allowing the client to integrate Citadel's ML insights into their own internal dashboards.
*   **Detailed Specifications:**
    *   **Versioning Strategy:** URI-based versioning (e.g., `/api/v1/...`, `/api/v2/...`). Versions must be supported for at least 12 months before deprecation.
    *   **Sandbox Environment:** A mirrored version of the production environment using anonymized "dummy" data. This allows the client's developers to test integrations without risking production data.
    *   **Authentication:** API Keys (X-API-KEY header) combined with OAuth2.0 client credentials flow.
    *   **Documentation:** Swagger/OpenAPI 3.0 specification hosted at `/api/docs`.
    *   **Request/Response Format:** All data must be exchanged in JSON format using UTF-8 encoding.
*   **Acceptance Criteria:** The client can successfully retrieve a predictive score via the API in the sandbox environment without affecting production records.

### 3.4 API Rate Limiting and Usage Analytics
*   **Priority:** High
*   **Status:** In Design
*   **Description:** To protect the on-premise hardware from being overwhelmed, the API must restrict the number of requests per client/user.
*   **Detailed Specifications:**
    *   **Algorithm:** Token Bucket algorithm will be implemented. 
    *   **Tiers:** 
        - Standard: 100 requests/minute.
        - Premium: 1,000 requests/minute.
    *   **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
    *   **Analytics Engine:** A separate table in Oracle DB will log every API call, including the endpoint, response time, status code, and the originating IP address.
    *   **Monitoring:** A dashboard for Hessa Park to monitor usage spikes and identify potential bottlenecks in the ML model's inference time.
*   **Acceptance Criteria:** A request exceeding the 101st call in a single minute must return a `429 Too Many Requests` HTTP status code.

### 3.5 SSO Integration with SAML and OIDC Providers
*   **Priority:** High
*   **Status:** In Progress
*   **Description:** Integration with the client's corporate identity provider to allow seamless login.
*   **Detailed Specifications:**
    *   **SAML 2.0:** Support for Service Provider Initiated (SP-Initiated) SSO. The application will act as the SP, redirecting users to the client's Identity Provider (IdP).
    *   **OIDC:** Support for OpenID Connect using the Authorization Code Flow with PKCE.
    *   **User Mapping:** The system must automatically map SAML assertions (e.g., `eduPersonAffiliation`) to internal Citadel roles (Admin, Teacher, Student).
    *   **Session Management:** Sessions will be managed via secure, HTTP-only cookies with a 4-hour expiration time.
    *   **Fallback:** A local "Emergency Admin" account must exist for system recovery if the SSO provider is down, requiring a 256-bit encrypted password stored in a secure vault.
*   **Acceptance Criteria:** A user can successfully log in using their corporate credentials and be assigned the correct role based on their IdP attributes.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `GET /students/{studentId}/predictions`
*   **Description:** Retrieves the ML-generated success probability for a specific student.
*   **Request:** `studentId` (UUID)
*   **Response:**
    ```json
    {
      "studentId": "550e8400-e29b-41d4-a716-446655440000",
      "prediction_score": 0.87,
      "confidence_interval": [0.82, 0.91],
      "timestamp": "2025-01-10T14:30:00Z"
    }
    ```

### 4.2 `POST /content/update`
*   **Description:** Updates educational content with conflict resolution tokens.
*   **Request:**
    ```json
    {
      "contentId": "cont-998",
      "delta": "Insert 'Quantum Physics' at index 45",
      "versionToken": "v1.0.42"
    }
    ```
*   **Response:** `200 OK` or `409 Conflict`

### 4.3 `GET /analytics/usage`
*   **Description:** Provides usage statistics for a specific API key.
*   **Request:** `apiKey` (Query Param)
*   **Response:**
    ```json
    {
      "totalRequests": 15000,
      "rateLimitRemaining": 450,
      "averageLatencyMs": 120
    }
    ```

### 4.4 `POST /auth/sso/callback`
*   **Description:** The endpoint where the SAML/OIDC provider redirects the user after authentication.
*   **Request:** `SAMLResponse` or `code` (POST body)
*   **Response:** `302 Redirect` to Dashboard.

### 4.5 `PUT /settings/system`
*   **Description:** Updates global system configurations (ML threshold, etc.).
*   **Request:**
    ```json
    {
      "ml_threshold": 0.75,
      "maintenance_mode": false
    }
    ```
*   **Response:** `204 No Content`

### 4.6 `GET /sandbox/test-data`
*   **Description:** Returns a set of mock data for the customer sandbox environment.
*   **Request:** None.
*   **Response:** `JSON Array` of 100 mock student records.

### 4.7 `DELETE /cache/clear`
*   **Description:** Forces a clear of the server-side ML inference cache.
*   **Request:** `adminToken` (Header)
*   **Response:** `200 OK`

### 4.8 `GET /health`
*   **Description:** Liveness and readiness probe for the release train monitoring.
*   **Request:** None.
*   **Response:** `{"status": "UP", "db": "CONNECTED", "ml_engine": "READY"}`

---

## 5. DATABASE SCHEMA

The database is hosted on Oracle 19c. All tables use `VARCHAR2` for strings and `NUMBER` for numeric values.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `USERS` | `USER_ID` | `EMAIL`, `SAML_UID`, `ROLE_ID` | FK to `ROLES` | Core user account data. |
| `ROLES` | `ROLE_ID` | `ROLE_NAME`, `PERMISSIONS` | - | Defines system access levels. |
| `STUDENTS` | `STUDENT_ID` | `EXTERNAL_ID`, `GRADE_LEVEL` | - | Educational profiles. |
| `PREDICTIONS` | `PRED_ID` | `STUDENT_ID`, `SCORE`, `TIMESTAMP` | FK to `STUDENTS` | ML output history. |
| `CONTENT` | `CONTENT_ID` | `BODY_TEXT`, `VERSION_TAG` | - | The educational materials. |
| `EDIT_LOGS` | `LOG_ID` | `CONTENT_ID`, `USER_ID`, `DELTA` | FK to `CONTENT`, `USERS` | Audit trail for collaboration. |
| `API_KEYS` | `KEY_ID` | `KEY_VALUE`, `CLIENT_ID`, `STATUS` | - | Authentication for the API. |
| `USAGE_METRICS` | `METRIC_ID` | `KEY_ID`, `ENDPOINT`, `LATENCY` | FK to `API_KEYS` | Rate limiting data. |
| `SESSIONS` | `SESS_ID` | `USER_ID`, `EXPIRY_DATE`, `IP` | FK to `USERS` | Active session tracking. |
| `SYSTEM_CONFIG`| `CONFIG_ID` | `KEY`, `VALUE`, `MODIFIED_BY` | FK to `USERS` | Global application settings. |

### 5.2 Schema Relationships
- **One-to-Many:** `ROLES` $\rightarrow$ `USERS` (One role can be assigned to many users).
- **One-to-Many:** `STUDENTS` $\rightarrow$ `PREDICTIONS` (One student has many ML predictions over time).
- **One-to-Many:** `CONTENT` $\rightarrow$ `EDIT_LOGS` (One piece of content has many versions/edits).
- **One-to-Many:** `API_KEYS` $\rightarrow$ `USAGE_METRICS` (One key generates many metric entries).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions
Due to the "no cloud" constraint, all environments are physically separated on different server racks within the on-premise data center.

#### 6.1.1 Development (DEV)
- **Purpose:** Feature development and initial unit testing.
- **Infrastructure:** 2x Virtual Machines (VMs), 16GB RAM, 4-core CPU.
- **Database:** Local Oracle XE instance.
- **Access:** Open to the distributed team via VPN.

#### 6.1.2 Staging (STG)
- **Purpose:** Integration testing and UAT (User Acceptance Testing). This is a mirrored copy of the Production hardware.
- **Infrastructure:** 2x Physical Servers, 64GB RAM, 16-core CPU.
- **Database:** Oracle 19c Enterprise Edition (Standard).
- **Access:** Restricted to Project Lead and QA.

#### 6.1.3 Production (PROD)
- **Purpose:** Live environment serving the $2M client.
- **Infrastructure:** High-availability cluster of 3 physical servers, 128GB RAM, 32-core CPU, NVMe storage for ML model weights.
- **Database:** Oracle 19c RAC (Real Application Clusters) for zero-downtime.
- **Access:** Strictly controlled; deployments occur only via the release train.

### 6.2 The Weekly Release Train
Project Citadel adheres to a strict **Weekly Release Train**.
- **Cycle:** Wednesday 02:00 AM UTC.
- **Cut-off:** All code must be merged into the `release` branch by Monday 17:00 UTC.
- **No Hotfixes:** Under no circumstances are hotfixes applied directly to production. If a critical bug is found on Thursday, it must be fixed and deployed on the following Wednesday's train.
- **Process:** `DEV` $\rightarrow$ `STG` (QA Sign-off) $\rightarrow$ `PROD`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Coverage Target:** 80% minimum coverage for business logic.
- **Execution:** Runs automatically on every commit to the `dev` branch via a local Jenkins instance.

### 7.2 Integration Testing
- **Focus:** Verifying the communication between Spring Boot and the Oracle DB, and Spring Boot and the ML Engine.
- **Method:** Use of **Testcontainers** to spin up a temporary Oracle container for integration tests.
- **Critical Path:** All `/api/v1` endpoints must be tested against the actual database schema.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium and Cypress.
- **Scenario-Based:** Tests will follow "User Journeys" (e.g., "User logs in via SSO $\rightarrow$ Opens Content $\rightarrow$ Edits with Colleague $\rightarrow$ Views ML Prediction").
- **Environment:** Conducted exclusively in the Staging (STG) environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Competitor is building same product and is 2 months ahead. | High | Critical | Develop a contingency plan with a fallback architecture that allows faster feature pivoting. |
| **R2** | Integration partner's API is undocumented and buggy. | High | Medium | Manually document all observed behaviors; create a "workaround" wiki for the dev team. |
| **R3** | On-premise hardware delivery delays. | Medium | High | Use virtualized environments for as long as possible to keep development moving. |
| **R4** | Data breach in EU data center. | Low | Critical | Implement AES-256 encryption at rest and TLS 1.3 in transit; quarterly audits. |
| **R5** | "God Class" technical debt causes system crash. | High | Medium | Schedule a "Debt Sprint" in February to decompose the 3,000-line class into services. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure/loss of client.
- **High:** Significant delay in milestones.
- **Medium:** Manageable with extra effort.
- **Low:** Minimal impact on timeline.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Oct 2024 - Jan 2025):** Setup of on-premise infrastructure, SSO integration, and DB schema implementation.
- **Phase 2: Core ML & Collaboration (Jan 2025 - Mar 2025):** Deployment of the ML model engine and the real-time editing system.
- **Phase 3: API & Scaling (Mar 2025 - May 2025):** Finalization of the customer-facing API and rate-limiting logic.
- **Phase 4: Hardening & Launch (May 2025 - July 2025):** Extensive E2E testing, external audits, and production rollout.

### 9.2 Key Milestones
| Milestone | Target Date | Dependency | Description |
| :--- | :--- | :--- | :--- |
| **M1** | 2025-03-15 | Legal DPA Review | First paying customer onboarded to the system. |
| **M2** | 2025-05-15 | Collab Editing Feature | MVP feature-complete (All 5 features implemented). |
| **M3** | 2025-07-15 | External Audit Pass | Full Production launch and handover to client. |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2024-11-02
**Attendees:** Hessa, Hana, Pax
- Oracle DB version confirmed as 19c.
- No cloud. Absolutely no cloud.
- Pax worried about Java/C++ bridge for ML model.
- Decision: Use JNI.
- Hana to start schema.

### Meeting 2: Sprint Planning - Collaboration
**Date:** 2024-12-15
**Attendees:** Hessa, Brigid, Hana
- Collab editing is a blocker.
- Brigid says UX for conflicts must be simple.
- OT vs CRDT?
- Hessa: "Just pick one that works by March."
- Action: Hana to prototype OT.

### Meeting 3: Emergency Budget Review
**Date:** 2025-01-20
**Attendees:** Hessa, Pax
- $400k is tight.
- Contractor fees for Pax increasing.
- Decision: Cut back on "Offline Mode" polish to save costs.
- Legal review of DPA still pending. Blocker.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Salaries for 15 distributed members & Pax (Contractor). |
| **Infrastructure** | 20% | $80,000 | On-premise server hardware and Oracle licensing. |
| **Tools/Software** | 5% | $20,000 | JIRA licenses, IDEs, and security scanning tools. |
| **Contingency** | 10% | $40,000 | Reserved for risk mitigation (R1, R2). |

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt Report
The current codebase contains a class titled `SystemCoreManager.java` spanning 3,042 lines. This class currently handles:
1. User Authentication logic.
2. Global Logging wrappers.
3. SMTP Email dispatch.
4. Oracle DB connection pooling.

**Risk:** Any change to the email logic can potentially break the authentication flow.
**Resolution Plan:** The class will be decomposed into `AuthService`, `LogService`, and `NotificationService` during the February 2025 Debt Sprint.

### Appendix B: Data Processing Agreement (DPA) Status
The current blocker for the Customer API (Feature 3) is the legal review of the DPA.
- **Current Status:** Pending review by Oakmount Group Legal and Client Legal.
- **Core Conflict:** Client demands full ownership of ML weights trained on their data; Oakmount Group seeks to retain the "base model" IP.
- **Impact:** API development is paused until the legal boundary of "Derived Data" is defined.