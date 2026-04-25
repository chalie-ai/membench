Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. To ensure the highest level of detail, each section has been expanded with the requested technical specifics, including database schemas, API definitions, and organizational logic.

***

# PROJECT SPECIFICATION: PROJECT CITADEL
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Approved / Baseline  
**Classification:** Confidential – Talus Innovations Internal  
**Project Lead:** Gia Gupta (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Citadel represents a strategic pivot for Talus Innovations. For the first time in the company's history, Talus is entering the legal services industry—a high-barrier, high-compliance market characterized by extreme requirements for data integrity and confidentiality. Citadel is a greenfield machine learning model deployment platform designed to automate legal document analysis, discovery, and compliance auditing. Unlike generic ML wrappers, Citadel is engineered for "Extreme Sovereignty," ensuring that legal firms can deploy models with a level of security and auditability that meets the strictest jurisdictional requirements.

### 1.2 Business Justification
The legal tech market is currently fragmented between legacy on-premise software and overly permissive cloud-native tools. There is a significant "trust gap" where law firms possess massive amounts of unstructured data but are hesitant to use LLMs due to leakage risks and the lack of a verifiable audit trail. Citadel fills this gap by implementing a "Clean Monolith" architecture using Rust for memory safety and Cloudflare Workers for edge-based low-latency delivery.

By leveraging a high-performance Rust backend, we minimize the compute overhead associated with typical Python-based ML wrappers, allowing us to maintain an API response time p95 under 200ms. This technical advantage translates to a superior user experience for legal professionals who require instantaneous search and retrieval across millions of case documents.

### 1.3 ROI Projection
The project is funded with a budget of $800,000 over a 6-month build cycle. Based on current market analysis of the "Legal ML" vertical, Talus Innovations projects the following financial outcomes:
*   **Year 1 Revenue Goal:** $2.4M ARR based on a B2B SaaS model targeting 15 mid-to-large size law firms.
*   **Cost of Acquisition (CAC):** Estimated at $12,000 per firm.
*   **Lifetime Value (LTV):** Projected at $180,000 per firm over 3 years.
*   **Break-even Point:** Month 14 post-launch.

The ROI is further amplified by the "first-mover" advantage in deploying an ISO 27001 certified ML environment at the edge. By reducing the latency of legal discovery from hours to milliseconds, Citadel provides a tangible productivity gain that justifies a premium pricing tier.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Citadel utilizes a **Clean Monolith** architecture. While the industry trend leans toward microservices, the Citadel team (a veteran group of 8) has opted for a monolith with strictly enforced module boundaries. This approach eliminates network overhead between services and simplifies the deployment pipeline, as every merged PR goes directly to production via a continuous deployment (CD) mechanism.

### 2.2 The Stack
*   **Backend:** Rust (v1.78+). Chosen for its memory safety and performance, critical for handling large legal datasets and ensuring the 200ms p95 latency goal.
*   **Frontend:** React (v18.2) with TypeScript. Focused on a high-density "Workstation" UI for legal analysts.
*   **Edge Layer:** Cloudflare Workers. This allows for global distribution of the model's inference endpoints, bringing the computation closer to the legal firm's regional data centers.
*   **Edge Storage:** SQLite. Used for local caching and offline-first capabilities, ensuring that legal professionals can continue working during intermittent connectivity.
*   **Security:** ISO 27001 Certified Environment. All infrastructure is provisioned via Terraform into a locked-down VPC.

### 2.3 ASCII Architecture Diagram
```text
[ User Browser ] <--- HTTPS/WSS ---> [ Cloudflare Edge Network ]
                                             |
                                             v
                                   [ Cloudflare Workers ]
                                   /         |          \
                    (Auth Module) <--- (Routing) ---> (Localization Module)
                                             |
                                             v
                                   [ Rust Core Monolith ]
                                   /         |          \
                (ML Inference Engine) <--- (Logic) ---> (Audit Trail Engine)
                                             |
                                             v
                    [ SQLite Edge Cache ] <---> [ Primary Persistent DB ]
                                                        |
                                                [ Tamper-Evident Log ]
                                                (Write-Once-Read-Many)
```

### 2.4 Data Flow
1.  **Request:** A user sends a query for a legal document.
2.  **Edge Interception:** Cloudflare Workers handle the initial request, validating the JWT and checking the localization header for the correct language pack.
3.  **Processing:** The Rust backend receives the request, queries the faceted index for the most relevant documents, and passes them through the ML model for summarization.
4.  **Audit:** Simultaneously, the Audit Trail Engine logs the access event into a tamper-evident storage system.
5.  **Response:** The result is streamed back to the React frontend.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Design
**Requirement:** The legal industry requires a non-repudiable record of who accessed what document and when. Standard database logs are insufficient as they can be modified by database administrators.

**Technical Specification:**
Citadel will implement a "hash-chain" logging system. Every log entry will contain the cryptographic hash of the previous entry. This creates a linear chain of evidence. If a single bit of a previous log is altered, the chain is broken, and the system triggers a security alert. 
*   **Storage Mechanism:** Logs will be written to a WORM (Write-Once-Read-Many) storage bucket.
*   **Verification:** A daily "Heartbeat" service will re-calculate the chain hashes and sign them with a private key held in a Hardware Security Module (HSM).
*   **Granularity:** Every API call, including read-only GET requests, must be logged. This includes the User ID, Timestamp (UTC), Request Payload, and the resulting Model Output.
*   **Retention:** Logs must be retained for 7 years per legal compliance standards.

### 3.2 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Design
**Requirement:** Legal firms operate on a "Need to Know" basis. A junior associate should not have access to the partner-level strategy documents for a high-profile case.

**Technical Specification:**
We will implement a multi-tenant RBAC system. 
*   **Identity Provider:** Integration with Okta/Azure AD via SAML 2.0.
*   **Roles:** 
    *   `SuperAdmin`: Full system access, billing, and user management.
    *   `Partner`: Full access to all cases within their firm.
    *   `Associate`: Access to assigned cases only.
    *   `Auditor`: Read-only access to audit logs and system health.
*   **Permission Logic:** Permissions are evaluated at the Rust module boundary. A `PermissionGuard` middleware will intercept every request and verify if the user's role is mapped to the requested resource ID in the `role_permissions` table.
*   **Session Management:** Stateless JWTs with a 15-minute expiration and a sliding-window refresh token stored in a secure, HTTP-only cookie.

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Critical (Launch Blocker) | **Status:** In Design
**Requirement:** Legal discovery involves searching through millions of pages. Users must be able to filter by "Date Range," "Jurisdiction," "Case Type," and "Attorney" while performing a full-text search.

**Technical Specification:**
Since this is a launch blocker, the architecture uses a hybrid approach.
*   **Indexing:** We will use a custom Rust-based inverted index for full-text search, leveraging the `tantec` crate for high-performance indexing.
*   **Faceted Filtering:** Facets are pre-computed at the time of document ingestion. A "Facet Map" will be stored in the primary database, allowing the UI to show counts (e.g., "New York (452 documents)") instantly.
*   **Query Execution:**
    1.  The user enters a keyword and selects "Civil Law" and "2020-2022."
    2.  The system first filters the document IDs using the faceted index (O(1) lookup).
    3.  It then performs the full-text search only on the filtered subset.
    4.  The ML model ranks the results by "Legal Relevance" rather than just keyword frequency.
*   **Performance Goal:** Search results must return in < 150ms for datasets up to 10 million documents.

### 3.4 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Not Started
**Requirement:** Lawyers often work in courtrooms or secure facilities with no internet access. The system must allow them to read and annotate documents offline.

**Technical Specification:**
*   **Local Storage:** Use SQLite (via WASM) inside the browser to mirror a subset of the user's active cases.
*   **Sync Strategy:** A "Version Vector" approach will be used to track changes. 
    *   When the user is offline, all changes (annotations, tags) are written to a local `pending_sync` table in SQLite.
    *   Upon reconnection, a Background Sync worker initiates a "Reconciliation Phase."
*   **Conflict Resolution:** "Last Write Wins" (LWW) will be the default, but for legal annotations, the system will prompt the user to resolve conflicts manually if two different users edited the same paragraph.
*   **Data Encryption:** The local SQLite database must be encrypted using AES-256, with the key stored in the browser's IndexedDB, protected by the user's session.

### 3.5 Localization and Internationalization (i18n) for 12 Languages
**Priority:** Critical (Launch Blocker) | **Status:** In Review
**Requirement:** To compete globally, Citadel must support 12 languages including English, French, German, Mandarin, Japanese, Spanish, Portuguese, Arabic, Russian, Korean, Italian, and Dutch.

**Technical Specification:**
*   **Framework:** Implementation of the `fluent` localization system (by Mozilla) in the Rust backend and React frontend.
*   **Dynamic Loading:** Translation bundles will be stored as JSON files on Cloudflare Workers KV storage. This allows the team to update translations without redeploying the entire monolith.
*   **Right-to-Left (RTL) Support:** The React frontend will implement a dynamic CSS layout that flips based on the language locale (specifically for Arabic).
*   **ML Model Localization:** The underlying ML model must be prompted using "System Personas" for each language to ensure legal terminology is culturally and jurisdictionally accurate.
*   **Date/Currency Formatting:** Use the `Intl` API in JavaScript to ensure date formats (DD/MM/YYYY vs MM/DD/YYYY) and currency symbols are correct for each of the 12 target regions.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer <JWT>` token in the Authorization header.

### 4.1 `POST /auth/login`
*   **Description:** Authenticates user and returns session tokens.
*   **Request Body:** `{"email": "user@firm.com", "password": "hashed_password"}`
*   **Response (200 OK):** `{"accessToken": "ey...", "refreshToken": "zx...", "expiresIn": 900}`
*   **Response (401 Unauthorized):** `{"error": "Invalid credentials"}`

### 4.2 `GET /search`
*   **Description:** Performs faceted full-text search.
*   **Query Params:** `q=string`, `facet_jurisdiction=NY`, `facet_date_start=2020-01-01`, `page=1`
*   **Response (200 OK):**
    ```json
    {
      "results": [{"docId": "123", "snippet": "...the court found...", "score": 0.98}],
      "facets": {"jurisdiction": {"NY": 452, "CA": 120}},
      "total": 572
    }
    ```

### 4.3 `POST /documents/upload`
*   **Description:** Uploads a legal document for processing.
*   **Request Body:** Multipart form data (File, CaseId).
*   **Response (202 Accepted):** `{"jobId": "upload_8892", "status": "processing"}`

### 4.4 `GET /audit/logs`
*   **Description:** Retrieves the tamper-evident audit trail.
*   **Query Params:** `userId=string`, `startDate=date`, `endDate=date`
*   **Response (200 OK):** `{"logs": [{"timestamp": "...", "action": "READ", "docId": "123", "hash": "0xabc..."}]}`

### 4.5 `GET /documents/{docId}/summarize`
*   **Description:** Triggers the ML model to summarize a specific document.
*   **Response (200 OK):** `{"summary": "The defendant is accused of...", "confidence": 0.94}`

### 4.6 `PATCH /documents/{docId}/metadata`
*   **Description:** Updates tags or facets of a document.
*   **Request Body:** `{"tags": ["Urgent", "Appeal"], "caseId": "CASE-99"}`
*   **Response (200 OK):** `{"status": "updated"}`

### 4.7 `GET /user/profile`
*   **Description:** Returns the current user's profile and RBAC roles.
*   **Response (200 OK):** `{"userId": "u1", "name": "Gia Gupta", "role": "SuperAdmin", "firm": "Talus Innovations"}`

### 4.8 `POST /sync/push`
*   **Description:** Pushes offline changes from the SQLite edge cache to the primary DB.
*   **Request Body:** `{"changes": [{"action": "EDIT", "docId": "123", "content": "..."}], "vector": 14}`
*   **Response (200 OK):** `{"status": "synced", "newVector": 15}`

---

## 5. DATABASE SCHEMA

The primary database is a relational store (PostgreSQL) with SQLite used for edge caching.

### 5.1 Tables and Relationships

1.  **`firms`**
    *   `firm_id` (UUID, PK)
    *   `firm_name` (VARCHAR)
    *   `subscription_tier` (VARCHAR)
    *   `created_at` (TIMESTAMP)

2.  **`users`**
    *   `user_id` (UUID, PK)
    *   `firm_id` (FK -> firms.firm_id)
    *   `email` (VARCHAR, UNIQUE)
    *   `password_hash` (TEXT)
    *   `role_id` (FK -> roles.role_id)

3.  **`roles`**
    *   `role_id` (INT, PK)
    *   `role_name` (VARCHAR) - e.g., 'Partner', 'Associate'
    *   `permissions_mask` (INT)

4.  **`cases`**
    *   `case_id` (UUID, PK)
    *   `firm_id` (FK -> firms.firm_id)
    *   `case_title` (VARCHAR)
    *   `open_date` (DATE)
    *   `closed_date` (DATE)

5.  **`documents`**
    *   `doc_id` (UUID, PK)
    *   `case_id` (FK -> cases.case_id)
    *   `file_path` (TEXT)
    *   `content_hash` (TEXT) - For deduplication
    *   `version` (INT)

6.  **`document_facets`**
    *   `facet_id` (UUID, PK)
    *   `doc_id` (FK -> documents.doc_id)
    *   `facet_key` (VARCHAR) - e.g., 'Jurisdiction'
    *   `facet_value` (VARCHAR) - e.g., 'New York'

7.  **`audit_logs`**
    *   `log_id` (BIGINT, PK)
    *   `user_id` (FK -> users.user_id)
    *   `action` (VARCHAR)
    *   `resource_id` (UUID)
    *   `timestamp` (TIMESTAMP)
    *   `prev_hash` (TEXT) - Chain link
    *   `current_hash` (TEXT)

8.  **`ml_summaries`**
    *   `summary_id` (UUID, PK)
    *   `doc_id` (FK -> documents.doc_id)
    *   `summary_text` (TEXT)
    *   `model_version` (VARCHAR)
    *   `confidence_score` (FLOAT)

9.  **`sync_vectors`**
    *   `user_id` (FK -> users.user_id)
    *   `last_sync_version` (INT)
    *   `device_id` (VARCHAR)

10. **`localization_cache`**
    *   `locale_id` (VARCHAR, PK) - e.g., 'en-US', 'fr-FR'
    *   `translation_bundle` (JSONB)
    *   `last_updated` (TIMESTAMP)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Citadel employs a strict three-tier environment strategy. Because we utilize a Continuous Deployment (CD) model, the transition from staging to production is automated via GitHub Actions.

#### 6.1.1 Development Environment (`dev`)
*   **Purpose:** Rapid iteration for the team.
*   **Infrastructure:** Local Docker containers for Rust/Postgres, mirroring the production environment as closely as possible.
*   **Deployment:** Triggered on every commit to the `develop` branch.
*   **Data:** Mocked legal datasets.

#### 6.1.2 Staging Environment (`staging`)
*   **Purpose:** Final QA, Security Audit verification, and Stakeholder demos.
*   **Infrastructure:** A mirrored "Shadow" production environment on Cloudflare Workers.
*   **Deployment:** Triggered on merge to the `main` branch.
*   **Data:** Anonymized real-world data.

#### 6.1.3 Production Environment (`prod`)
*   **Purpose:** Live client operations.
*   **Infrastructure:** ISO 27001 certified cloud environment with multi-region failover.
*   **Deployment:** Every merged PR to `main` that passes the staging smoke tests is automatically deployed to production.
*   **Security:** All traffic is encrypted via TLS 1.3. Data at rest is encrypted using AWS KMS managed keys.

### 6.2 CI/CD Pipeline
1.  **Pull Request:** Developer submits a PR.
2.  **CI Check:** Rust compiler runs `cargo check`, `cargo test`, and `cargo clippy`.
3.  **QA Gate:** Taj Park (QA Lead) approves the PR after manual verification in `dev`.
4.  **Merge:** PR merges to `main`.
5.  **Stage Deploy:** Automatic deployment to `staging`.
6.  **Production Push:** After 2 hours of zero-error telemetry in staging, the code is promoted to `prod`.

---

## 7. TESTING STRATEGY

Given the criticality of legal data, a "Zero-Regression" testing policy is enforced.

### 7.1 Unit Testing
*   **Scope:** All Rust modules (Logic, Auth, Localization).
*   **Approach:** Every function must have a corresponding test case. We target 90% code coverage.
*   **Tooling:** Built-in `cargo test` framework.

### 7.2 Integration Testing
*   **Scope:** Database interactions and API endpoint flows.
*   **Approach:** We use "Containerized Testing." A fresh PostgreSQL and SQLite instance is spun up for each test suite to ensure isolation.
*   **Key Scenario:** Verifying that a change in the `User` role immediately restricts access to a `Document` via the `PermissionGuard`.

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Critical user paths (e.g., Login $\rightarrow$ Search $\rightarrow$ Summarize $\rightarrow$ Log Out).
*   **Approach:** Use Playwright for headless browser testing.
*   **Frequency:** Run once per deployment cycle.
*   **Metric:** If any E2E test fails, the production deployment is automatically rolled back to the previous stable hash.

### 7.4 Security Testing
*   **Penetration Testing:** Monthly internal audits conducted by the CTO.
*   **Compliance:** Quarterly review of ISO 27001 controls to ensure no "configuration drift" has occurred in the Cloudflare environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Primary vendor (ML Model Provider) announced EOL for their current API. | High | Critical | **Contingency Plan:** Building a fallback adapter for an open-source Llama-3 based model hosted on private GPUs. |
| **R2** | Project Sponsor (Executive) is rotating out of their role. | Medium | High | **Action:** Raise as a blocker in the next board meeting to secure a successor sponsor immediately. |
| **R3** | Latency exceeds 200ms p95 due to large document sizes. | Low | Medium | **Mitigation:** Implement aggressive pagination and streaming responses using Rust's `tokio` async runtime. |
| **R4** | Localization errors in critical legal terminology. | Medium | High | **Mitigation:** Hire certified legal translators for a final review of the 12-language bundles. |

### 8.1 Probability/Impact Matrix
*   **Critical:** Immediate project failure or legal liability.
*   **High:** Significant delay or loss of key functionality.
*   **Medium:** Manageable delay with minimal impact on launch.
*   **Low:** Minor inconvenience.

---

## 9. TIMELINE AND PHASES

The project is scheduled for a 6-month build (October 2025 – April 2026), with a launch target of May 2026.

### Phase 1: Foundation & Core Engine (Month 1-2)
*   **Focus:** Rust backend setup, Monolith module boundaries, Database schema implementation.
*   **Dependency:** Budget approval for the critical tool purchase (Current Blocker).
*   **Goal:** Establish basic connectivity between React and Rust.

### Phase 2: Critical Feature Implementation (Month 3-4)
*   **Focus:** Advanced Search, Localization, and Audit Trail.
*   **Milestone:** **Architecture Review Complete (2026-07-15)**.
*   **Dependency:** Finalization of the 12-language translation bundles.

### Phase 3: Hardening & Compliance (Month 5)
*   **Focus:** RBAC, Offline-first sync, and Security Hardening.
*   **Milestone:** **Security Audit Passed (2026-05-15)**.
*   **Dependency:** Completion of the ISO 27001 environmental checklist.

### Phase 4: Validation & Launch (Month 6)
*   **Focus:** E2E Testing, Stakeholder Demos, and Performance Tuning.
*   **Milestone:** **Stakeholder Demo and Sign-off (2026-09-15)**.
*   **Goal:** Hit p95 < 200ms and 99.9% uptime.

---

## 10. MEETING NOTES

*Note: These notes are extracted from the project's shared running document (200 pages, unsearchable). The team refers to this as "The Great Scroll."*

### Meeting 1: Kickoff & Stack Alignment (2025-11-02)
**Attendees:** Gia, Rafik, Taj, Ira
**Discussion:**
- Gia emphasized the "Clean Monolith" approach. Ira questioned if microservices would scale better. Gia countered that the team is small (8 people) and the priority is speed of delivery and low latency.
- Rafik expressed concern regarding the 200ms p95 requirement. He suggested that we move as much logic as possible to the Cloudflare Edge to avoid round-trips to the origin server.
- **Decision:** Use Rust for the backend to ensure zero-cost abstractions and maximum performance.
- **Action Item:** Rafik to draft the initial module boundaries.

### Meeting 2: The Vendor Crisis (2025-12-15)
**Attendees:** Gia, Rafik, Taj, Ira
**Discussion:**
- Rafik reported that the primary ML vendor announced the EOL (End of Life) for their v2 API.
- Taj noted that this could break the "Advanced Search" feature since it relies on the vendor's embedding model.
- Gia instructed the team to immediately begin a contingency plan. "We cannot let a third-party API be a single point of failure for a legal product."
- **Decision:** Allocate 20% of sprint capacity to building a "Model Adapter" layer that can switch between providers.
- **Action Item:** Gia to discuss the budget for private GPU hosting with the board.

### Meeting 3: The "Budget Blocker" Sync (2026-01-20)
**Attendees:** Gia, Rafik, Taj, Ira
**Discussion:**
- The team is currently blocked on the purchase of the "Indexing-Pro" tool, which is required for the faceted search implementation.
- Ira mentioned that they are currently using stdout for debugging production issues because structured logging isn't implemented yet. Gia admitted this is a significant piece of technical debt.
- Taj warned that if the tool purchase isn't approved by Feb 1st, the "Critical" launch blocker (Advanced Search) will be delayed.
- **Decision:** Gia will mark the budget approval as a "Critical Blocker" in the board report.
- **Action Item:** Rafik to implement a basic `tracing` crate setup in Rust to replace stdout logging.

---

## 11. BUDGET BREAKDOWN

The total budget of $800,000 is allocated to ensure a high-quality, secure build without cutting corners on compliance.

### 11.1 Personnel ($580,000)
*   **Project Lead (Gia Gupta):** $150,000 (Strategic oversight and architecture).
*   **Senior Backend Engineer (Rafik Santos):** $130,000 (Core Rust development).
*   **QA Lead (Taj Park):** $110,000 (Testing and security verification).
*   **Junior Developer (Ira Nakamura):** $70,000 (Frontend and localized bundles).
*   **Other 4 Team Members:** $120,000 (Combined specialized roles).

### 11.2 Infrastructure ($120,000)
*   **Cloudflare Enterprise Plan:** $40,000 (Edge Workers, KV storage, and WAF).
*   **AWS ISO 27001 Environment:** $60,000 (Managed PostgreSQL, KMS, and HSM).
*   **Edge Cache Nodes:** $20,000.

### 11.3 Tools & Licensing ($50,000)
*   **Indexing-Pro License:** $25,000 (Current budget approval pending).
*   **Security Audit Fees:** $15,000 (Third-party certification).
*   **Localization Services:** $10,000 (Professional legal translation).

### 11.4 Contingency Fund ($50,000)
*   Reserved for the "Vendor EOL" risk (R1), specifically for potential GPU rental costs if the fallback model is required.

---

## 12. APPENDICES

### Appendix A: ML Inference Latency Budget
To achieve the p95 < 200ms goal, the request budget is broken down as follows:
*   **Network Round Trip (Edge):** 30ms
*   **Auth & RBAC Check:** 10ms
*   **Faceted Search Lookup:** 40ms
*   **ML Model Inference:** 80ms
*   **Serialization/JSON overhead:** 20ms
*   **Total:** 180ms (20ms buffer).

### Appendix B: Tamper-Evident Log Hash Algorithm
The audit trail uses the following logic:
$H_n = \text{SHA-256}(H_{n-1} + \text{Timestamp} + \text{UserID} + \text{Action} + \text{Payload})$
Where $H_n$ is the hash of the current log entry and $H_{n-1}$ is the hash of the previous entry. This creates a cryptographic chain. To verify the integrity of the log, the system re-computes all hashes from $H_0$ to $H_{latest}$. Any mismatch indicates a data breach or unauthorized modification.