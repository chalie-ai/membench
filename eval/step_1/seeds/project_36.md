Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, industrial-grade Project Specification Document (PSD). It expands upon the provided constraints with granular technical details, specific API paths, and exhaustive schema definitions to ensure it serves as the primary reference for the development team.

***

# PROJECT SPECIFICATION: CORNICE
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Classification:** Internal / Proprietary / FedRAMP Compliant  
**Last Updated:** 2025-10-12  
**Project Lead:** Kian Nakamura (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
**Cornice** is a high-security, real-time collaboration tool engineered by Talus Innovations specifically for the government services sector. Unlike generic collaboration software, Cornice is designed to operate within the rigorous compliance frameworks required by federal agencies, focusing on high-availability, immutable audit trails, and secure data sovereignty. 

The primary objective of Cornice is to provide a unified workspace where government contractors and agency officials can collaborate on sensitive documentation, report generation, and data analysis in real-time without compromising the security posture of the hosting environment.

### 1.2 Business Justification
The impetus for Cornice is a strategic partnership with a single enterprise government client. This client has committed to a service agreement totaling **$2,000,000 (USD) annually**, providing a guaranteed immediate revenue stream upon successful deployment. The demand is driven by the client's inability to use commercial-off-the-shelf (COTS) software due to strict FedRAMP requirements and the need for specialized report generation capabilities.

### 1.3 ROI Projection
With a total development budget of **$1,500,000**, the project is designed to achieve a break-even point within the first nine months post-launch. 

*   **Year 1 Revenue:** $2,000,000 (Enterprise Client)
*   **Year 1 Capex/Opex:** $1,500,000 (Budget) + $\approx$ $200,000 (GCP Infrastructure/Maintenance)
*   **Projected Net Profit (Year 1):** $300,000
*   **Year 2 Projection:** With the framework established, Talus Innovations intends to scale this product vertical to three additional government agencies, projecting a Year 2 ARR (Annual Recurring Revenue) of $6M to $8M.

### 1.4 Strategic Alignment
Cornice transforms Talus Innovations from a service-based consultancy into a product-led organization. By solving the "security vs. usability" paradox for government workers, Cornice establishes a competitive moat through FedRAMP authorization, which serves as a significant barrier to entry for smaller competitors.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Cornice utilizes a traditional three-tier architecture, modernized through a microservices approach to ensure scalability and fault tolerance. The system is designed to handle high-concurrency real-time updates using gRPC for inter-service communication and Go for the backend logic.

### 2.2 The Stack
*   **Language:** Go (Golang) 1.21+ for all microservices.
*   **Communication:** gRPC for internal service-to-service calls; REST/JSON for the frontend API gateway.
*   **Database:** CockroachDB (Distributed SQL) to ensure consistency across geographic regions and high availability.
*   **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
*   **Security:** TLS 1.3 encryption in transit, AES-256 at rest, and FedRAMP-compliant IAM.

### 2.3 Architecture Diagram (ASCII Description)
The following represents the data flow from the end-user to the persistence layer:

```text
[ USER BROWSER / CLIENT ] 
          |
          | (HTTPS / WSS)
          v
[ GCP LOAD BALANCER ] <---- [ Cloud Armor / WAF ]
          |
          v
[ API GATEWAY (Go) ] <---- [ Auth Service (2FA/Hardware Key) ]
          |
          +-----------------------+-----------------------+
          |                       |                       |
          v                       v                       v
[ COLLAB SERVICE ]       [ REPORT SERVICE ]       [ SEARCH SERVICE ]
  (Real-time Sync)         (PDF/CSV Gen)            (Elastic-Indexing)
          |                       |                       |
          +-----------------------+-----------------------+
                                  |
                                  v
                      [ COCKROACHDB CLUSTER ]
                      (Multi-Region Distributed)
                                  |
                      [ GCP CLOUD STORAGE (GCS) ]
                      (Stored PDF/CSV Reports)
```

### 2.4 Design Rationale
*   **Go Microservices:** Chosen for its superior concurrency primitives (goroutines) and efficiency in handling gRPC streams, which is critical for real-time collaboration.
*   **CockroachDB:** Selected over standard PostgreSQL to avoid a single point of failure and to provide "survival" capabilities if a GCP zone goes offline, which is a requirement for government-grade SLAs.
*   **gRPC:** Used to reduce latency and payload size compared to REST for internal communication, ensuring the "real-time" feel of the collaboration tool.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
The system must allow users to aggregate collaboration data, project milestones, and audit logs into professional PDF and CSV reports. These reports can be generated on-demand or scheduled for delivery to specific stakeholders via secure email or internal notification systems.

**Functional Requirements:**
1.  **Template Engine:** Users can select from predefined government-standard templates (e.g., Monthly Progress Report, Audit Summary).
2.  **Data Aggregation:** The service must query the `collaboration_logs` and `milestone_tracker` tables to populate the report.
3.  **Scheduling Logic:** A cron-based scheduler within the Report Service allows users to set delivery frequencies (Daily, Weekly, Monthly) at specific UTC timestamps.
4.  **Delivery Pipeline:** Reports are generated as temporary blobs in GCS, then delivered via a secure signed URL to the recipient.
5.  **Format Support:** 
    *   **PDF:** Fixed-layout, branded with agency logos, containing tables and charts.
    *   **CSV:** Raw data export for use in external auditing tools.

**Technical Implementation:**
The Report Service utilizes the `gofpdf` library for PDF generation and the standard `encoding/csv` package for CSVs. The scheduling is managed by a distributed ticker system in Go, ensuring that if one pod restarts, the schedule is maintained across the cluster.

---

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
To meet FedRAMP requirements, Cornice must implement a robust authentication layer. This includes standard password-based login supplemented by a mandatory second factor. The system must specifically support FIDO2/WebAuthn hardware keys (e.g., YubiKey).

**Functional Requirements:**
1.  **Enrollment Flow:** Users must register at least one hardware key during their first login. 
2.  **Challenge-Response:** The system must implement the WebAuthn flow: the server sends a random challenge, the hardware key signs it, and the server verifies the signature.
3.  **Fallback Mechanism:** In the event of a lost key, a highly secure "Recovery Code" system (16-character alphanumeric) is provided during setup.
4.  **Session Management:** JWT (JSON Web Tokens) are used for session persistence, with short expiration times (15 minutes) and secure refresh tokens stored in an encrypted cookie.
5.  **Audit Logging:** Every successful and failed 2FA attempt must be logged with IP address and timestamp.

**Technical Implementation:**
The Auth Service integrates the `webauthn` Go library. It maintains a `user_credentials` table in CockroachDB to store the public keys associated with each user's hardware device. All authentication requests are routed through the API Gateway, which validates the JWT before allowing access to business logic services.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Users must be able to search across thousands of collaboration documents and messages. This requires more than simple SQL `LIKE` queries; it requires a full-text search (FTS) engine capable of handling complex queries and faceted filtering (filtering by date, user, project, or security level).

**Functional Requirements:**
1.  **Full-Text Indexing:** All document content and messages are indexed. The system must support stemming (e.g., searching "collaborate" finds "collaboration").
2.  **Faceted Navigation:** A sidebar allowing users to drill down results (e.g., "Show me all PDF reports from July 2026 created by Tariq Stein").
3.  **Real-time Indexing:** As users edit documents in the collaboration tool, the index must be updated within 5 seconds to ensure search accuracy.
4.  **Permission-Aware Search:** Search results must be filtered based on the user's access level. A user should never see a search result for a document they do not have permission to view.

**Technical Implementation:**
The Search Service utilizes an inverted index approach. While CockroachDB provides basic GIN indexing, for the required scale and speed, the team is implementing a sidecar indexing service that syncs data from CockroachDB into a dedicated search index. Query parsing is handled via a custom Go parser that converts user input into optimized SQL and index queries.

---

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
The landing page for Cornice users is a customizable dashboard. Users should be able to organize their workspace by adding, removing, and rearranging widgets that provide real-time snapshots of their projects.

**Functional Requirements:**
1.  **Widget Library:** Pre-defined widgets including "Recent Documents," "Pending Approvals," "Upcoming Milestones," and "System Health."
2.  **Drag-and-Drop Interface:** A frontend implementation allowing users to move widgets across a grid system (similar to a 12-column Bootstrap grid).
3.  **State Persistence:** The layout configuration (widget ID, X/Y position, size) must be saved to the database so the dashboard remains consistent across sessions.
4.  **Real-time Updates:** Widgets must use WebSockets or gRPC-web to update their data in real-time without requiring a full page refresh.

**Technical Implementation:**
The frontend will use a React-based grid library (e.g., `react-grid-layout`). The backend will provide a `GET /api/v1/dashboard/config` endpoint to retrieve the user's specific layout and a `POST /api/v1/dashboard/config` endpoint to save changes. Each widget will correspond to a specific gRPC call to the respective business logic service (e.g., the "Upcoming Milestones" widget calls the Project Service).

---

### 3.5 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** Not Started

**Description:**
Government workers often operate in "low-connectivity" environments (SCIFs, field work). Cornice must allow users to continue editing documents and interacting with the tool while offline, syncing changes automatically once a connection is re-established.

**Functional Requirements:**
1.  **Local Persistence:** The browser must use IndexedDB to store a local copy of the documents the user is currently working on.
2.  **Conflict Resolution:** The system must implement a Conflict-free Replicated Data Type (CRDT) approach to ensure that when two users edit the same line offline and then sync, the changes are merged logically without data loss.
3.  **Sync Queue:** An outbound queue of "pending changes" that is processed sequentially upon reconnection.
4.  **Connectivity Status Indicator:** A UI element informing the user of their current sync status (Synced, Syncing, or Offline).

**Technical Implementation:**
The team will implement a Yjs-based CRDT framework. Local changes are captured as "update" blobs in IndexedDB. Upon reconnection, the client sends these blobs to the Collaboration Service via a gRPC stream. The server applies the updates to the CockroachDB state and broadcasts the changes to other active collaborators.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. Authentication requires a Bearer Token in the header.

### 4.1 Authentication Service
**`POST /api/v1/auth/login`**
*   **Description:** Initiates the first phase of authentication (Username/Password).
*   **Request:** `{ "username": "kian.nakamura", "password": "encrypted_password" }`
*   **Response:** `{ "status": "challenge_required", "challenge": "base64_encoded_challenge", "session_id": "sess_12345" }`

**`POST /api/v1/auth/verify-2fa`**
*   **Description:** Verifies the hardware key signature.
*   **Request:** `{ "session_id": "sess_12345", "credential_id": "key_id", "signature": "sig_data" }`
*   **Response:** `{ "token": "jwt_access_token", "refresh_token": "jwt_refresh_token" }`

### 4.2 Report Service
**`POST /api/v1/reports/generate`**
*   **Description:** Trigger an immediate report generation.
*   **Request:** `{ "template_id": "gov_monthly_01", "format": "PDF", "project_id": "proj_99" }`
*   **Response:** `{ "report_id": "rep_555", "status": "processing", "estimated_time": "10s" }`

**`POST /api/v1/reports/schedule`**
*   **Description:** Schedule a recurring report delivery.
*   **Request:** `{ "template_id": "gov_weekly_02", "frequency": "weekly", "delivery_email": "audit@gov.us", "start_date": "2026-01-01" }`
*   **Response:** `{ "schedule_id": "sched_888", "next_run": "2026-01-07T00:00:00Z" }`

### 4.3 Search Service
**`GET /api/v1/search?q={query}&facet={filter}`**
*   **Description:** Performs a full-text search with optional filtering.
*   **Request Params:** `q` (search string), `facet` (e.g., `author:Tariq`)
*   **Response:** `[{ "doc_id": "doc_1", "title": "Budget Forecast", "snippet": "...$1.5M budget allocated...", "score": 0.98 }]`

### 4.4 Collaboration Service
**`GET /api/v1/docs/{doc_id}`**
*   **Description:** Retrieves the current state of a collaboration document.
*   **Response:** `{ "doc_id": "doc_1", "content": "...", "version": 45, "last_modified": "2026-05-10T12:00:00Z" }`

**`PATCH /api/v1/docs/{doc_id}`**
*   **Description:** Updates a specific section of a document.
*   **Request:** `{ "delta": "...", "base_version": 45 }`
*   **Response:** `{ "status": "success", "new_version": 46 }`

### 4.5 Dashboard Service
**`GET /api/v1/dashboard/config`**
*   **Description:** Retrieves the user's widget layout.
*   **Response:** `[{ "widget_id": "milestone_clock", "x": 0, "y": 0, "w": 4, "h": 2 }]`

---

## 5. DATABASE SCHEMA

Cornice uses CockroachDB for a distributed, strongly consistent SQL layer.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID, PK), `email`, `password_hash`, `role_id` | 1:N with `user_credentials` | Core user identity. |
| `roles` | `role_id` (INT, PK), `role_name`, `permissions_json` | 1:N with `users` | RBAC permissions mapping. |
| `user_credentials` | `cred_id` (UUID, PK), `user_id` (FK), `pub_key`, `device_name` | N:1 with `users` | Hardware key public keys. |
| `projects` | `project_id` (UUID, PK), `name`, `client_id`, `created_at` | 1:N with `documents` | Top-level project containers. |
| `documents` | `doc_id` (UUID, PK), `project_id` (FK), `title`, `content_blob` | N:1 with `projects` | The actual collaborative content. |
| `document_versions` | `version_id` (UUID, PK), `doc_id` (FK), `delta`, `author_id` (FK) | N:1 with `documents` | Audit trail of every change. |
| `milestones` | `ms_id` (UUID, PK), `project_id` (FK), `due_date`, `status` | N:1 with `projects` | Project tracking goals. |
| `reports` | `report_id` (UUID, PK), `template_id`, `gcs_path`, `created_by` (FK) | N:1 with `users` | Metadata for generated reports. |
| `report_schedules` | `sched_id` (UUID, PK), `template_id`, `cron_expression`, `recipient` | N:1 with `users` | Scheduling logic for reports. |
| `audit_logs` | `log_id` (BIGINT, PK), `user_id` (FK), `action`, `timestamp`, `ip_addr` | N:1 with `users` | FedRAMP required activity log. |

### 5.2 Relationship Logic
*   **Users $\rightarrow$ Credentials:** One user can register multiple hardware keys (Primary, Backup).
*   **Projects $\rightarrow$ Documents:** A project acts as a folder containing multiple collaborative docs.
*   **Documents $\rightarrow$ Versions:** Every "Save" or "Sync" action creates a new entry in `document_versions` to allow for point-in-time recovery.
*   **Users $\rightarrow$ Audit Logs:** Every single API request is linked to a `user_id` for compliance auditing.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Cornice employs a Continuous Deployment (CD) pipeline where every merged Pull Request (PR) to the `main` branch is automatically deployed to production.

#### 6.1.1 Development Environment (`dev`)
*   **Purpose:** Feature experimentation and unit testing.
*   **Config:** Small GKE cluster (3 nodes), single-node CockroachDB.
*   **Deployment:** Triggered on every commit to feature branches.

#### 6.1.2 Staging Environment (`staging`)
*   **Purpose:** Pre-production validation, QA, and User Acceptance Testing (UAT).
*   **Config:** Mirror of production architecture but with reduced resource limits.
*   **Deployment:** Triggered upon merge to `develop` branch. This is where the "Security Audit" (Milestone 1) is conducted.

#### 6.1.3 Production Environment (`prod`)
*   **Purpose:** Live government client operations.
*   **Config:** Multi-region GKE cluster across 3 GCP zones. CockroachDB cluster with 6 nodes (3 per region) for high availability.
*   **Deployment:** Automatic deployment via `main` branch merge.
*   **Security:** FedRAMP High boundary. No direct SSH access; all changes via Kubernetes ConfigMaps and Secrets.

### 6.2 CI/CD Pipeline
1.  **Build:** Go binaries are compiled into Docker images.
2.  **Test:** Unit tests and integration tests must pass 100%.
3.  **Scan:** Snyk and SonarQube scan for vulnerabilities and technical debt.
4.  **Deploy:** `kubectl apply` updates the deployment in GKE using a rolling update strategy (zero downtime).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Scope:** Individual Go functions and gRPC handlers.
*   **Target:** 80% code coverage.
*   **Tooling:** `go test` with `testify` for assertions.
*   **Focus:** Business logic, data validation, and CRDT merge logic.

### 7.2 Integration Testing
*   **Scope:** Service-to-service communication and database persistence.
*   **Approach:** Use `testcontainers-go` to spin up a real CockroachDB instance during the test phase.
*   **Focus:** Ensuring the API Gateway correctly routes requests to the Search and Report services.

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Full user journeys (e.g., Login $\rightarrow$ Create Doc $\rightarrow$ Generate Report $\rightarrow$ Logout).
*   **Tooling:** Playwright for browser automation.
*   **Focus:** Validating that the frontend React components correctly interact with the Go backend and that 2FA hardware key simulation works.

### 7.4 Security Testing
*   **Penetration Testing:** Quarterly third-party audits to ensure FedRAMP compliance.
*   **Fuzzing:** Using `go-fuzz` on gRPC endpoints to prevent buffer overflow or crash-inducing payloads.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is building similar tool; 2 months ahead. | High | High | Develop a contingency fallback architecture that allows faster pivoting of features. Focus on "FedRAMP First" to out-compete on security. |
| **R-02** | Primary vendor dependency announces EOL. | Medium | Critical | Raise as a formal blocker in the next board meeting. Identify alternative open-source replacements for the deprecated tool. |
| **R-03** | Budget approval for critical tool pending. | Medium | Medium | Kian Nakamura to escalate to Finance. Use open-source alternatives temporarily to avoid blocking development. |
| **R-04** | Lack of structured logging (Technical Debt). | High | Medium | Implement `zap` or `logrus` for structured JSON logging. Stop relying on `stdout` for production debugging. |
| **R-05** | FedRAMP authorization delay. | Low | Critical | Engage a specialized FedRAMP consultant early to ensure all documentation matches the implementation. |

**Probability/Impact Matrix:**
*   **High/Critical:** Immediate action required.
*   **Medium/Medium:** Monitor and plan mitigation.
*   **Low/Medium:** Accept risk or monitor.

---

## 9. TIMELINE & PHASES

### 9.1 Phase 1: Foundation & Security (Now – 2026-07-15)
*   **Focus:** Core Auth, Database Schema, and FedRAMP alignment.
*   **Key Activity:** Finalizing 2FA and Hardware Key integration.
*   **Milestone 1:** **Security Audit Passed (2026-07-15).**

### 9.2 Phase 2: Feature Completion (2026-07-16 – 2026-09-15)
*   **Focus:** Advanced Search and Dashboard implementation.
*   **Key Activity:** Integrating the Search Service index and building the React drag-and-drop UI.
*   **Milestone 2:** **Production Launch (2026-09-15).**

### 9.3 Phase 3: Stability & Optimization (2026-09-16 – 2026-11-15)
*   **Focus:** Bug fixing, performance tuning, and Offline-First mode.
*   **Key Activity:** Implementing CRDTs for background sync.
*   **Milestone 3:** **Post-launch Stability Confirmed (2026-11-15).**

---

## 10. MEETING NOTES

*Note: These summaries are derived from recorded video calls. Per team policy, raw video is not archived for review; only these summaries are maintained.*

### Meeting 1: Architecture Alignment (2025-11-05)
*   **Attendees:** Kian Nakamura, Tariq Stein, Xander Kim, Dmitri Jensen.
*   **Discussion:** The team debated between PostgreSQL and CockroachDB. Tariq argued that the government client requires multi-region resilience. 
*   **Decision:** CockroachDB was selected to ensure no single point of failure across GCP zones.
*   **Action Item:** Tariq to design the initial schema for `audit_logs` to satisfy FedRAMP.

### Meeting 2: The Competitor Crisis (2026-02-12)
*   **Attendees:** Kian Nakamura, Xander Kim.
*   **Discussion:** Intelligence suggests a competitor is 2 months ahead in feature parity. Xander suggested streamlining the dashboard to a "minimalist" approach to speed up delivery.
*   **Decision:** Kian approved a "Contingency Plan" to simplify the initial widget set to launch faster, while maintaining the high-security 2FA as the primary differentiator.
*   **Action Item:** Kian to document fallback architecture for board review.

### Meeting 3: The Logging Bottleneck (2026-05-20)
*   **Attendees:** Kian Nakamura, Dmitri Jensen.
*   **Discussion:** Dmitri reported that debugging the Report Service is nearly impossible because the team is reading raw `stdout` in the logs. 
*   **Decision:** Acknowledged as critical technical debt. The team will prioritize implementing structured logging (`zap`) in the next sprint.
*   **Action Item:** Dmitri to create a shared logging middleware for all microservices.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000 (USD)

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $950,000 | Salaries for 12-person cross-functional team (including EM, Data Eng, Designer, Support). |
| **Infrastructure** | $250,000 | GCP (GKE, CockroachDB Cloud, GCS, Cloud Armor). |
| **Tooling & Licenses** | $150,000 | Security scanners, IDE licenses, WebAuthn certification, and the "critical tool" pending approval. |
| **Contingency** | $150,000 | Buffer for unexpected FedRAMP audit costs or hardware key procurement. |

**Budget Note:** The $1.5M budget is heavily front-loaded to ensure the "Critical" launch blockers are resolved by the September 2026 launch date.

---

## 12. APPENDICES

### Appendix A: FedRAMP Compliance Mapping
The Cornice architecture maps to the following NIST 800-53 controls:
*   **AC-2 (Account Management):** Managed via the `users` and `roles` tables with strict RBAC.
*   **IA-2 (Identification and Authentication):** Satisfied by mandatory 2FA and Hardware Key support.
*   **AU-2 (Event Logging):** Satisfied by the `audit_logs` table, recording every authenticated action.
*   **SC-28 (Protection of Information at Rest):** All CockroachDB nodes use AES-256 disk encryption.

### Appendix B: CRDT Merge Logic (Pseudo-code)
To support the "Offline-First" mode, the system uses a LWW-Element-Set (Last-Write-Wins).

```go
type Update struct {
    Timestamp int64
    UserID    string
    Operation string // "INSERT" or "DELETE"
    Value     string
}

func Merge(localState []Update, remoteState []Update) []Update {
    // 1. Combine both sets of updates
    merged := append(localState, remoteState...)
    
    // 2. Sort by timestamp descending
    sort.Slice(merged, func(i, j int) bool {
        return merged[i].Timestamp > merged[j].Timestamp
    })
    
    // 3. Apply only the most recent change per unique element ID
    finalState := make(map[string]Update)
    for _, up := range merged {
        if _, exists := finalState[up.Value]; !exists {
            finalState[up.Value] = up
        }
    }
    return flatten(finalState)
}
```
This ensures that when a government worker returns from a low-connectivity area, their changes are merged based on the most recent timestamp, preventing the "overwriting" of data by older offline edits.