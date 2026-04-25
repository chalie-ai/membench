# PROJECT SPECIFICATION DOCUMENT: PROJECT OBELISK
**Document Version:** 1.0.4  
**Status:** Formal Specification / Active  
**Company:** Bridgewater Dynamics  
**Project Lead:** Devika Park (CTO)  
**Date of Issue:** October 24, 2023  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

Project Obelisk represents a strategic pivot for Bridgewater Dynamics, marking the company's formal entry into a greenfield fintech market. While Bridgewater Dynamics has historically excelled in enterprise resource planning and logistics software, Obelisk is a venture into high-frequency financial data management and reporting, a sector where the company has no prior operational footprint. The objective is to deliver a mobile-first application that allows institutional clients to manage complex financial portfolios with offline capabilities and automated regulatory reporting.

**Business Justification**  
The fintech sector is currently experiencing a shift toward "mobile-institutional" tools. There is a significant gap in the market for high-fidelity, offline-capable tools that bridge the gap between desktop terminals (like Bloomberg) and consumer banking apps. By leveraging our existing expertise in high-availability systems and applying it to this new domain, Bridgewater Dynamics aims to capture a 5% market share of mid-tier hedge fund administrators within the first 24 months of launch.

**ROI Projection**  
With a capital expenditure exceeding $5,000,000, Project Obelisk is a flagship initiative reporting directly to the board. The projected Return on Investment (ROI) is calculated based on a subscription-based SaaS model. 
- **Year 1 (Post-Launch):** Projected revenue of $2.2M through a limited beta of 15 institutional clients.
- **Year 2:** Scaling to 60 clients with an ARR (Annual Recurring Revenue) projection of $8.5M.
- **Break-even point:** Estimated at Month 30 post-launch.
- **Efficiency Gain:** A primary driver of the ROI is the 50% reduction in manual processing time for end users, which increases the "stickiness" of the product and justifies a premium pricing tier.

**Strategic Alignment**  
Obelisk is not merely a product but a proof-of-concept for Bridgewater Dynamics' ability to enter new markets. The success of this project will dictate the company's M&A strategy for the next five years. Because this is a greenfield project, the risk profile is higher than usual, necessitating the rigorous architectural standards and board-level oversight outlined in this document.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Project Obelisk utilizes a complex mixed-stack architecture. Due to the organizational structure of Bridgewater Dynamics, the project inherits three legacy stacks that must interoperate seamlessly:
1. **Stack A (Legacy Core):** Java/Spring Boot (handling transactional data).
2. **Stack B (Analytics Engine):** Python/FastAPI (handling quantitative calculations).
3. **Stack C (User Gateway):** Node.js/TypeScript (handling API orchestration).

The system is designed as a set of microservices. To prevent tight coupling between these disparate stacks, communication is handled via an **event-driven architecture using Apache Kafka**. This ensures that if the Python analytics engine lags during a heavy computation, the User Gateway can still provide cached data to the mobile client without blocking.

### 2.2 ASCII Architecture Diagram
```text
[ Mobile App (React Native) ] 
          |
          v
[ Load Balancer (Nginx) ]
          |
          v
[ API Gateway (Node.js/TypeScript) ] <--- (Stack C)
          |
    ______|_____________________________________________
   |              |                    |                |
   v              v                    v                v
[ Auth Svc ]  [ Report Svc ]   [ Portfolio Svc ]  [ Sync Svc ]
(Java/Spring) (Python/FastAPI) (Java/Spring)    (Node.js)
   |              |                    |                |
   |______________|____________________|________________|
                          |
                          v
               [ Apache Kafka Event Bus ]
                          |
        __________________|___________________
       |                  |                   |
[ Postgres DB ]    [ Redis Cache ]     [ S3 Blob Store ]
(System State)     (Session/Real-time)  (PDFs/CSVs)
```

### 2.3 Integration Logic
The "Mixed Stack" interoperability is achieved through a standardized JSON schema registry. When the Portfolio Service (Java) updates a balance, it publishes a `BALANCE_UPDATED` event to Kafka. The Report Service (Python) consumes this event to trigger a scheduled PDF generation, and the Sync Service (Node.js) flags the record as "dirty" for the mobile app's next background sync.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** Low (Nice to have)
*   **Status:** Complete
*   **Description:** A comprehensive system to manage user identity, session persistence, and permissioning across different organizational levels (e.g., Analyst, Portfolio Manager, Administrator).
*   **Detailed Logic:**
    The system implements an OAuth2 + OpenID Connect (OIDC) flow. Users are authenticated via the API Gateway, which issues a JWT (JSON Web Token) containing a payload of claims. These claims define the user's role.
    - **Analyst:** Read-only access to portfolios; can trigger report generation.
    - **Portfolio Manager:** Can modify asset allocations; can approve reports.
    - **Administrator:** Full system access, including user management and audit log viewing.
    The RBAC is enforced at the middleware level in the Node.js gateway. If a user attempts to access `/api/v1/admin/settings` with an `Analyst` role, the gateway returns a `403 Forbidden` before the request even reaches the microservices.
*   **Technical Implementation:**
    The authentication logic is currently contained within the "God Class" (see Technical Debt section), requiring a future refactor. It uses Argon2 for password hashing and a rotating secret key for JWT signing.

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
*   **Priority:** Medium
*   **Status:** Not Started
*   **Description:** An automated engine that aggregates financial data into professional-grade PDF and CSV reports, delivered via email or in-app notification on a user-defined schedule.
*   **Detailed Logic:**
    Users can create "Report Templates" specifying which data points (e.g., Total AUM, Quarterly Yield, Risk Variance) should be included. The scheduling is handled by a distributed cron job within the Python Analytics Engine.
    1. **Trigger:** The scheduler identifies a report due at 08:00 UTC.
    2. **Data Aggregation:** The Report Service queries the Portfolio Service and the Analytics Engine via gRPC to gather the latest figures.
    3. **Rendering:** Using `ReportLab` (for PDF) and `Pandas` (for CSV), the service generates the files.
    4. **Storage:** Files are uploaded to an AWS S3 bucket with a Time-to-Live (TTL) of 30 days.
    5. **Delivery:** An event is sent to the Notification Service to email the user a pre-signed URL to download the document.
*   **Constraints:** Reports must be generated in the background to avoid blocking the main event loop. Max file size is capped at 50MB.

### 3.3 Localization and Internationalization (L10n/i18n)
*   **Priority:** High
*   **Status:** In Progress
*   **Description:** Ensuring the application is fully functional and culturally adapted for 12 different languages, including right-to-left (RTL) support for Arabic.
*   **Detailed Logic:**
    The application uses a key-value translation system. All strings are stored in JSON localization files (e.g., `en-US.json`, `ja-JP.json`). The mobile app detects the system locale on boot and loads the corresponding file.
    - **Dynamic Translation:** For financial data, the system must handle currency symbol placement and decimal separators (e.g., `1,234.56` in US vs `1.234,56` in Germany).
    - **RTL Support:** The UI layout must flip horizontally when Arabic is selected. This requires using Flexbox `flex-direction: row-reverse` for specific components.
    - **Language List:** English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, Russian, and Hindi.
*   **Current Progress:** English, Spanish, and French are complete. Japanese and Mandarin are in the review phase. Arabic RTL layout is currently causing regressions in the navigation bar.

### 3.4 Audit Trail Logging with Tamper-Evident Storage
*   **Priority:** Low (Nice to have)
*   **Status:** In Design
*   **Description:** A secure, immutable log of every write-action performed within the system to meet future regulatory requirements.
*   **Detailed Logic:**
    Unlike standard application logs, the Audit Trail must be tamper-evident. Every entry will be hashed using SHA-256, and each single entry will contain the hash of the previous entry (a blockchain-lite structure).
    - **Captured Events:** User ID, Timestamp, IP Address, Action (e.g., `UPDATE_PORTFOLIO`), Old Value, New Value.
    - **Storage:** Logs are written to a Write-Once-Read-Many (WORM) storage volume.
    - **Verification:** A daily "Integrity Job" will re-calculate the hash chain. If a mismatch is found (indicating an unauthorized modification of the log), a critical alert is sent to the CTO (Devika Park).
*   **Design Constraint:** To avoid performance degradation, audit logging is performed asynchronously via Kafka. The main transaction is committed first, and the audit event is processed by the `AuditService` milliseconds later.

### 3.5 Offline-First Mode with Background Sync
*   **Priority:** High
*   **Status:** In Progress
*   **Description:** Allowing users to view and edit financial data without an active internet connection, with automatic synchronization once connectivity is restored.
*   **Detailed Logic:**
    Obelisk employs a "Local-First" strategy using a SQLite database on the mobile device.
    - **Read Path:** The app always reads from the local SQLite cache first.
    - **Write Path:** When a user makes a change offline, the change is stored in an "Outbox" table with a timestamp and a sequence number.
    - **Sync Mechanism:** Upon detecting a network connection (via a NetInfo listener), the app initiates a "Reconciliation Loop." It pushes the Outbox events to the `/api/v1/sync` endpoint.
    - **Conflict Resolution:** The system uses a "Last-Write-Wins" (LWW) strategy based on the client's timestamp, unless the change involves a critical financial transaction, in which case it is flagged for manual review by the user ("Conflict Detected: Please choose which version to keep").
*   **Technical Challenge:** Managing the delta-updates for large datasets to prevent the mobile app from consuming excessive data during the sync process.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer <JWT>` token in the header.

### 4.1 `POST /auth/login`
*   **Purpose:** Authenticate user and return token.
*   **Request Body:** `{"email": "user@bridge.com", "password": "hashed_password"}`
*   **Response (200 OK):** `{"token": "eyJhbG...", "expires_in": 3600, "role": "Analyst"}`

### 4.2 `GET /portfolio/summary`
*   **Purpose:** Retrieve a high-level overview of the user's assigned portfolios.
*   **Query Params:** `?currency=USD&period=quarterly`
*   **Response (200 OK):** `{"portfolios": [{"id": "PF-101", "value": 5000000, "change": "+2.4%"}, {...}]}`

### 4.3 `POST /reports/generate`
*   **Purpose:** Manually trigger a report generation.
*   **Request Body:** `{"template_id": "standard_q_report", "portfolio_id": "PF-101", "format": "pdf"}`
*   **Response (202 Accepted):** `{"job_id": "job_8821", "status": "processing", "eta": "30s"}`

### 4.4 `GET /reports/download/{job_id}`
*   **Purpose:** Retrieve the final report file.
*   **Response (302 Found):** Redirects to a pre-signed S3 URL.

### 4.5 `POST /sync/push`
*   **Purpose:** Push local offline changes to the server.
*   **Request Body:** `{"changes": [{"action": "update", "entity": "asset", "id": "A-55", "data": {"qty": 100}, "timestamp": "2025-01-10T10:00Z"}]}`
*   **Response (200 OK):** `{"synced_count": 1, "conflicts": []}`

### 4.6 `GET /sync/pull`
*   **Purpose:** Fetch updates since the last known sync timestamp.
*   **Query Params:** `?since=2025-01-10T00:00Z`
*   **Response (200 OK):** `{"updates": [...], "server_time": "2025-01-11T12:00Z"}`

### 4.7 `PATCH /user/profile`
*   **Purpose:** Update user localization preferences.
*   **Request Body:** `{"language": "ja-JP", "timezone": "Asia/Tokyo"}`
*   **Response (200 OK):** `{"status": "updated"}`

### 4.8 `GET /audit/logs`
*   **Purpose:** Retrieve a list of system events (Admin only).
*   **Query Params:** `?start_date=2025-01-01&end_date=2025-01-15`
*   **Response (200 OK):** `{"logs": [{"id": "LOG-1", "user": "Devika", "action": "SENSITIVE_ACCESS", "timestamp": "..."}]}`

---

## 5. DATABASE SCHEMA

The system uses a distributed database approach. The primary state is stored in PostgreSQL, with a Redis layer for caching and S3 for blobs.

### 5.1 Table Definitions

1.  **`users`**: Stores core identity.
    - `user_id` (UUID, PK), `email` (VARCHAR, Unique), `password_hash` (TEXT), `role_id` (FK), `created_at` (Timestamp).
2.  **`roles`**: Defines RBAC levels.
    - `role_id` (INT, PK), `role_name` (VARCHAR: Admin, Manager, Analyst), `permissions` (JSONB).
3.  **`portfolios`**: High-level portfolio containers.
    - `portfolio_id` (UUID, PK), `owner_id` (FK), `portfolio_name` (VARCHAR), `base_currency` (VARCHAR(3)).
4.  **`assets`**: Individual financial instruments.
    - `asset_id` (UUID, PK), `portfolio_id` (FK), `ticker` (VARCHAR), `quantity` (DECIMAL), `last_price` (DECIMAL).
5.  **`transactions`**: History of asset changes.
    - `tx_id` (UUID, PK), `asset_id` (FK), `user_id` (FK), `amount` (DECIMAL), `tx_type` (BUY/SELL), `timestamp` (Timestamp).
6.  **`report_templates`**: Configurations for PDF/CSV output.
    - `template_id` (UUID, PK), `name` (VARCHAR), `config_json` (JSONB), `created_by` (FK).
7.  **`scheduled_reports`**: Users' delivery preferences.
    - `schedule_id` (UUID, PK), `user_id` (FK), `template_id` (FK), `frequency` (DAILY/WEEKLY/MONTHLY), `delivery_time` (TIME).
8.  **`report_jobs`**: Tracking the status of generation tasks.
    - `job_id` (UUID, PK), `schedule_id` (FK/Null), `status` (PENDING/DONE/FAILED), `s3_path` (TEXT).
9.  **`audit_logs`**: The tamper-evident log.
    - `log_id` (BIGINT, PK), `user_id` (FK), `action` (VARCHAR), `payload` (JSONB), `previous_hash` (TEXT), `current_hash` (TEXT).
10. **`sync_sessions`**: Tracking mobile device synchronization.
    - `session_id` (UUID, PK), `user_id` (FK), `device_id` (VARCHAR), `last_sync_timestamp` (Timestamp).

### 5.2 Relationships
- **Users $\rightarrow$ Roles:** Many-to-One.
- **Users $\rightarrow$ Portfolios:** One-to-Many.
- **Portfolios $\rightarrow$ Assets:** One-to-Many.
- **Assets $\rightarrow$ Transactions:** One-to-Many.
- **Users $\rightarrow$ Scheduled Reports:** One-to-Many.
- **Report Templates $\rightarrow$ Scheduled Reports:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Obelisk uses a three-tier environment strategy. Because of the regulatory nature of the fintech industry, releases are not continuous; they are **quarterly**, aligned with external review cycles.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and initial integration.
- **Infrastructure:** Kubernetes (K8s) cluster on a small-scale managed node.
- **Data:** Synthetic data only; no real client information.
- **Deploy Cycle:** Continuous Deployment (CD) on merge to `develop` branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and regulatory dry-runs.
- **Infrastructure:** Mirrored production environment (identical CPU/RAM/Disk specs).
- **Data:** Anonymized production snapshots.
- **Deploy Cycle:** Bi-weekly releases from `develop` to `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live client traffic.
- **Infrastructure:** Multi-region AWS deployment across `us-east-1` and `eu-west-1` for high availability.
- **Data:** Encrypted at rest (AES-256) and in transit (TLS 1.3).
- **Deploy Cycle:** Quarterly releases (March, June, September, December) following a 2-week "freeze" period for final QA.

### 6.2 CI/CD Pipeline
The pipeline uses GitLab CI.
1. **Build Phase:** Docker images are created for each microservice.
2. **Test Phase:** Unit tests $\rightarrow$ Integration tests $\rightarrow$ Security scan.
3. **Artifact Store:** Images are pushed to a private Amazon Elastic Container Registry (ECR).
4. **Deployment:** Helm charts are used to deploy the images into the K8s cluster.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Each microservice must maintain a minimum of 80% code coverage.
- **Java/Spring:** JUnit 5 and Mockito.
- **Python/FastAPI:** PyTest.
- **Node.js:** Jest.
- **Focus:** Testing business logic in isolation (e.g., verifying that a currency conversion function handles rounding correctly).

### 7.2 Integration Testing
Focuses on the communication between the three inherited stacks via Kafka.
- **Method:** Contract Testing using **Pact**. This ensures that if the Java service changes its output schema, the Python service is notified immediately during the build phase.
- **Kafka Testing:** Using Testcontainers to spin up a temporary Kafka broker to verify that events are produced and consumed in the correct order.

### 7.3 End-to-End (E2E) Testing
Validates the entire user journey from the mobile app to the database.
- **Tools:** Appium (for mobile automation) and Cypress (for the admin web portal).
- **Scenario Examples:** 
    1. User logs in $\rightarrow$ Modifies a portfolio $\rightarrow$ Goes offline $\rightarrow$ Modifies again $\rightarrow$ Goes online $\rightarrow$ Verifies data is correct on the server.
    2. User schedules a report $\rightarrow$ System triggers job $\rightarrow$ User receives email $\rightarrow$ User downloads PDF.

### 7.4 Penetration Testing
As the company does not follow a specific compliance framework (like SOC2 or PCI-DSS) yet, the primary security mechanism is **Quarterly External Penetration Testing**. An outside firm is hired every three months to attempt to breach the API Gateway and the S3 storage.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | High | Accept risk; monitor weekly progress; prioritize documentation of the Kafka event schemas. | Devika Park |
| R-02 | Team lack of experience with mixed stack | Medium | High | De-scope affected features (e.g., move Audit Trail to "Optional") if milestones are missed. | Nadia N. |
| R-03 | Regulatory rejection of quarterly release | Low | Critical | Increase frequency of pre-release audits with the legal team. | Devika Park |
| R-04 | Data sync conflicts in offline mode | High | Medium | Implement LWW (Last-Write-Wins) and manual resolution UI. | Xiomara G. |
| R-05 | "God Class" failure during refactor | Medium | High | Implement a "Strangler Fig" pattern; migrate functions one-by-one to new services. | Nadia N. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt / Board-level failure.
- **High:** Significant delay in Milestone 1.
- **Medium:** Feature degradation / Budget overrun.
- **Low:** Minor inconvenience / Non-blocking.

---

## 9. TIMELINE & GANTT DESCRIPTION

The project follows a phased approach leading up to the August 2025 launch.

### Phase 1: Foundation (Oct 2023 - April 2024)
- **Focus:** Core infrastructure, Kafka setup, and "God Class" decomposition.
- **Dependencies:** Completion of the API Gateway is required before any frontend work can begin.
- **Key Milestone:** Internal Alpha (Jan 2024).

### Phase 2: Feature Build-Out (May 2024 - Jan 2025)
- **Focus:** Implementing L10n/i18n and Offline-First mode.
- **Dependencies:** L10n must be integrated into the UI components before the PDF reporting engine is finalized (to ensure reports are also localized).
- **Key Milestone:** Feature Complete (Jan 2025).

### Phase 3: Hardening & Regulatory Prep (Feb 2025 - July 2025)
- **Focus:** Penetration testing, performance tuning, and stability audits.
- **Dependencies:** Stability confirmed in Staging before moving to Production.
- **Key Milestone:** Final Regulatory Sign-off (July 2025).

### Milestone Targets
- **Milestone 1: Production Launch** $\rightarrow$ **2025-08-15**
- **Milestone 2: Post-launch stability confirmed** $\rightarrow$ **2025-10-15**
- **Milestone 3: Security audit passed** $\rightarrow$ **2025-12-15**

---

## 10. MEETING NOTES (EXTRACT)

*Note: These extracts are taken from the "Obelisk_Global_Notes.docx", a 200-page unsearchable shared document.*

**Meeting Date: 2023-11-12**  
**Attendees:** Devika, Nadia, Xiomara, Dante  
**Topic:** The "God Class" Problem  
**Discussion:** Nadia raised concerns that the current authentication/logging/email class is now 3,000 lines long and causing merge conflicts every hour. Dante mentioned that it’s becoming a single point of failure. Devika decided that while it’s a technical debt nightmare, we cannot stop all feature development to rewrite it.  
**Decision:** We will leave the God Class as is for now but create a new "Service Wrapper" to intercept calls. This is the "Strangler Fig" approach. Nadia will start the wrapper next sprint.

**Meeting Date: 2023-12-05**  
**Attendees:** Devika, Nadia, Xiomara  
**Topic:** L10n and Arabic RTL  
**Discussion:** Xiomara demonstrated that the current layout breaks when switching to Arabic. The "Back" button disappears off-screen. Nadia noted that the mixed-stack backend isn't sending the correct locale headers for some requests.  
**Decision:** High priority. We will move L10n to "High Priority" (up from Medium) because the board wants to see the Middle East market potential. Nadia to investigate the header mismatch.

**Meeting Date: 2024-01-20**  
**Attendees:** Devika, Dante  
**Topic:** Resource Constraints  
**Discussion:** A key team member (Backend Dev) has gone on medical leave for 6 weeks. This creates a gap in the Kafka implementation. Devika expressed concern about the timeline but refused to add new headcount due to the "veteran team" dynamic (the current team has worked together on 3 projects and doesn't integrate new people well).  
**Decision:** Dante will pick up the Kafka consumer logic. We will accept a slower velocity for the next 6 weeks. No new hires.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,500,000+ (Flagship Initiative)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,575,000 | 12-person team for 2 years (including benefits/bonuses). |
| **Infrastructure** | 15% | $825,000 | AWS Multi-region, K8s clusters, S3, Redis Enterprise. |
| **Tools & Licensing** | 10% | $550,000 | GitLab Premium, Appium Enterprise, Pen-Testing firms. |
| **Contingency** | 10% | $550,000 | Reserve for emergency scaling or regulatory fines. |

**Financial Reporting:** This budget is reviewed monthly by the Board of Directors. Any variance over 5% requires a formal justification memo signed by Devika Park.

---

## 12. APPENDICES

### Appendix A: God Class Refactor Map
The current `SystemCoreManager.java` (the 3,000-line God Class) will be decomposed into the following microservices:
1. `AuthService.java` $\rightarrow$ Logic for JWT issuance and role validation.
2. `AuditLogService.java` $\rightarrow$ Logic for SHA-256 hashing and WORM storage.
3. `EmailNotificationService.java` $\rightarrow$ SMTP integration and template rendering.
4. `UserSessionManager.java` $\rightarrow$ Redis-based session tracking.

### Appendix B: Offline Sync Conflict Logic
The "Last-Write-Wins" (LWW) algorithm is defined as follows:
Given two versions of a record $R$: $R_{client}$ and $R_{server}$.
1. If $Timestamp(R_{client}) > Timestamp(R_{server})$, then $R_{server} = R_{client}$.
2. If $Timestamp(R_{client}) < Timestamp(R_{server})$, the client is notified of a conflict.
3. If the record is marked as `CRITICAL` (e.g., a transaction above $10,000), LWW is disabled, and the record is moved to a `ManualResolutionQueue` for the user to approve via a side-by-side comparison UI.