# PROJECT SPECIFICATION DOCUMENT: DRIFT (v1.0.4)

**Company:** Stratos Systems  
**Project Name:** Drift  
**Project Lead:** Meera Costa (Engineering Manager)  
**Date of Issue:** October 26, 2023  
**Status:** Active / High Priority  
**Confidentiality:** Level 4 (Proprietary)

---

## 1. EXECUTIVE SUMMARY

### Business Justification
"Drift" represents a strategic pivot for Stratos Systems, marking the entry into a high-value real estate vertical. The project is driven by a singular, high-net-worth enterprise client who has committed to an annual recurring revenue (ARR) of $2,000,000, provided the application meets specific operational requirements. The core value proposition of Drift is to automate the fragmented data flow within luxury real estate portfolio management, replacing manual spreadsheet tracking with a high-performance, collaborative mobile environment.

The primary business driver is the reduction of operational friction. Currently, the anchor client spends an estimated 40 man-hours per week on manual data entry and report consolidation. Drift aims to automate this pipeline, targeting a 50% reduction in manual processing time. By capturing this efficiency, Stratos Systems secures not only the $2M annual contract but also a scalable blueprint to penetrate the broader luxury real estate market.

### ROI Projection
The financial architecture of Drift is designed for extreme lean efficiency. With a total development budget of $150,000 (a "shoestring" allocation), the project is positioned for an aggressive Return on Investment. 

*   **Year 1 Revenue:** $2,000,000 (Enterprise Client) + $500,000 (Projected New Market Revenue) = $2,500,000.
*   **Total Initial Investment:** $150,000.
*   **Operating Costs (Infrastructure/Maintenance):** Estimated at $45,000/year.
*   **Projected Net Profit (Year 1):** ~$2,305,000.

The ROI is exceptionally high due to the pre-existing commitment of the anchor client. However, the risk profile is skewed by the team's lack of experience with the chosen technical stack (Rust/Cloudflare Workers). The business justification rests on the ability to deliver a PCI DSS Level 1 compliant system that handles sensitive credit card data directly, providing a competitive moat that other real estate apps lack.

---

## 2. TECHNICAL ARCHITECTURE

### Architecture Overview
Drift employs a traditional three-tier architecture designed for edge-computing efficiency and extreme low-latency.

1.  **Presentation Layer (Frontend):** A React-based mobile application (delivered via Capacitor/Ionic for native wrapping). The frontend handles state management using Redux Toolkit and communicates with the backend via RESTful JSON APIs.
2.  **Business Logic Layer (Backend):** A series of Rust-based services deployed as Cloudflare Workers. This "serverless" approach ensures that the logic is executed as close to the user as possible. Rust was selected for its memory safety and performance, which is critical for the real-time collaborative editing features.
3.  **Data Layer (Persistence):** A hybrid approach utilizing SQLite for edge caching and local state, with a primary persistent store hosted on Cloudflare D1 (SQL).

### ASCII Architecture Diagram
```text
[ USER DEVICE ] <---HTTPS/TLS 1.3---> [ CLOUDFLARE EDGE ]
       |                                      |
       | (React Frontend)                     | (Cloudflare Workers - Rust)
       | [ Local SQLite Cache ]              | [ Business Logic / Validation ]
       |                                      |
       +-------------------------------------+
                                             |
                                             v
                            [ DATA PERSISTENCE LAYER ]
                            |   - Cloudflare D1 (SQL)  |
                            |   - Blob Storage (PDFs)   |
                            |   - PCI Vault (Encrypted) |
                            +--------------------------+
                                             |
                                             v
                            [ EXTERNAL SERVICES ]
                            |   - Stripe API (PCI)     |
                            |   - SendGrid (Email)     |
                            +--------------------------+
```

### Technical Specifications
*   **Backend Language:** Rust (Edition 2021)
*   **Frontend Framework:** React 18.2 with TypeScript
*   **Database:** SQLite (Edge) / Cloudflare D1 (Cloud)
*   **Deployment:** Weekly Release Train (Every Friday 04:00 UTC)
*   **Security Standard:** PCI DSS Level 1 Compliance (Direct CC processing)

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Blocked
*   **Description:** This feature is the foundation of the application's security. It must manage identity verification and ensure that users can only access data relevant to their assigned roles (e.g., Admin, Broker, Client, Auditor).
*   **Detailed Requirements:**
    *   **Authentication:** The system must support JWT (JSON Web Tokens) for session management. Tokens must have a short TTL (Time-to-Live) of 15 minutes, with refresh tokens stored in a secure, HTTP-only cookie.
    *   **RBAC Matrix:** 
        *   *Admin:* Full system access, user management, and audit log viewing.
        *   *Broker:* Ability to edit property data and generate reports for assigned portfolios.
        *   *Client:* Read-only access to their specific portfolio dashboards.
        *   *Auditor:* Read-only access to all financial records and PCI logs.
    *   **The "God Class" Issue:** Currently, authentication is handled by a 3,000-line Rust module that also manages logging and email. This creates a massive bottleneck and security risk. The specification requires the decomposition of this class into three distinct services: `AuthService`, `LogManager`, and `NotificationEngine`.
    *   **PCI Integration:** Authentication must integrate with the PCI vault to ensure that users accessing credit card data undergo additional identity verification.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** High
*   **Status:** Blocked
*   **Description:** A highly flexible landing page for users to monitor real estate KPIs. Users must be able to customize their view by adding, removing, and rearranging widgets.
*   **Detailed Requirements:**
    *   **Widget Library:** The system must provide at least 10 pre-defined widgets, including "Portfolio Value," "Monthly Cash Flow," "Pending Closings," and "Rental Yields."
    *   **Drag-and-Drop Interface:** Implementation using `react-grid-layout` or similar, allowing users to resize widgets and move them across a 12-column grid.
    *   **Persistence:** Dashboard configurations (widget ID, position, size) must be saved to the `user_preferences` table in the database so the layout persists across devices.
    *   **Data Fetching:** Widgets must fetch data asynchronously via dedicated API endpoints. If a widget's data source is unavailable, it must display a "Data Unavailable" state without crashing the rest of the dashboard.
    *   **Customization Logic:** Users can "pin" specific reports to the dashboard, turning a PDF report into a visual summary widget.

### 3.3 Real-time Collaborative Editing with Conflict Resolution
*   **Priority:** Medium
*   **Status:** Complete
*   **Description:** Multiple users must be able to edit property details and financial sheets simultaneously without overwriting each other's changes.
*   **Detailed Requirements:**
    *   **Concurrency Model:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency.
    *   **Presence Indicators:** Users must see a real-time cursor or "User X is typing..." indicator when another person is editing the same field.
    *   **Conflict Resolution:** In the event of a simultaneous edit to a single value, the system shall utilize a "Last Write Wins" (LWW) strategy based on server-side timestamps, unless the field is flagged as "Strict," in which case the system prompts the user to choose the correct version.
    *   **WebSocket Integration:** The Rust backend utilizes WebSockets via Cloudflare Durable Objects to maintain state and broadcast changes to all connected clients in milliseconds.
    *   **Latency Target:** End-to-end latency for edits must remain under 100ms.

### 3.4 PDF/CSV Report Generation and Scheduled Delivery
*   **Priority:** Medium
*   **Status:** Not Started
*   **Description:** The ability to transform raw portfolio data into professional, client-ready reports delivered via email on a recurring schedule.
*   **Detailed Requirements:**
    *   **Templates:** The system must support HTML-to-PDF templates using a headless browser (Puppeteer) running in a worker environment.
    *   **Data Export:** Support for CSV exports for all tabular data, including custom filtering (e.g., "Export all properties with < 4% cap rate").
    *   **Scheduling Engine:** A cron-like service that checks the `report_schedules` table daily. It must support frequencies: Daily, Weekly, Monthly, and Quarterly.
    *   **Delivery Pipeline:** Generated reports are uploaded to a secure Cloudflare R2 bucket, and a signed URL is emailed to the client via the `NotificationEngine`.
    *   **Audit Trail:** Every generated report must be logged in the `report_logs` table, recording who requested it and who received it.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** Medium
*   **Status:** Blocked
*   **Description:** An advanced security layer to protect high-value real estate accounts, supporting both software and hardware-based tokens.
*   **Detailed Requirements:**
    *   **TOTP Support:** Support for Time-based One-Time Passwords (TOTP) via apps like Google Authenticator or Authy.
    *   **WebAuthn/FIDO2:** Implementation of hardware key support (e.g., YubiKey) using the WebAuthn API to prevent phishing attacks.
    *   **Recovery Codes:** Upon 2FA setup, the system must generate ten one-time-use recovery codes. These must be stored using a salted hash (bcrypt).
    *   **Enforcement Logic:** Admins can force 2FA for users with the "Broker" or "Admin" role. "Client" roles may opt-in.
    *   **Grace Period:** A 24-hour window where users can access the account with a password only after a 2FA reset request, pending admin approval.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a `Bearer <JWT>` in the Authorization header.

### 4.1 `POST /auth/login`
*   **Description:** Authenticates user and returns session tokens.
*   **Request Body:**
    ```json
    { "email": "user@stratos.com", "password": "secure_password_123" }
    ```
*   **Response (200 OK):**
    ```json
    { "access_token": "eyJ...", "refresh_token": "def...", "expires_in": 900 }
    ```

### 4.2 `GET /portfolio/summary`
*   **Description:** Returns a high-level summary of the user's real estate portfolio.
*   **Response (200 OK):**
    ```json
    { 
      "total_value": 45000000, 
      "net_cash_flow": 120000, 
      "property_count": 14,
      "currency": "USD" 
    }
    ```

### 4.3 `PATCH /properties/{id}`
*   **Description:** Updates specific fields of a property (Collaborative).
*   **Request Body:**
    ```json
    { "valuation": 1200000, "status": "under_contract", "timestamp": "2023-10-26T10:00:00Z" }
    ```
*   **Response (200 OK):**
    ```json
    { "id": "prop_882", "updated_at": "2023-10-26T10:00:05Z", "version": 42 }
    ```

### 4.4 `POST /reports/generate`
*   **Description:** Triggers an immediate generation of a PDF report.
*   **Request Body:**
    ```json
    { "template_id": "quarterly_tax_v1", "property_ids": ["p1", "p2"], "format": "pdf" }
    ```
*   **Response (202 Accepted):**
    ```json
    { "job_id": "job_99123", "status": "processing", "estimated_completion": "30s" }
    ```

### 4.5 `GET /dashboard/config`
*   **Description:** Retrieves the user's customized widget layout.
*   **Response (200 OK):**
    ```json
    { 
      "layout": [
        { "widget": "cash_flow", "x": 0, "y": 0, "w": 6, "h": 4 },
        { "widget": "yield_chart", "x": 6, "y": 0, "w": 6, "h": 4 }
      ] 
    }
    ```

### 4.6 `POST /payments/process`
*   **Description:** Directly processes a credit card payment (PCI DSS Level 1).
*   **Request Body:**
    ```json
    { "amount": 5000, "currency": "USD", "card_token": "tok_visa_442", "billing_zip": "90210" }
    ```
*   **Response (200 OK):**
    ```json
    { "transaction_id": "tx_556677", "status": "success", "receipt_url": "https://..." }
    ```

### 4.7 `GET /auth/mfa/verify`
*   **Description:** Verifies a 2FA token.
*   **Request Body:**
    ```json
    { "otp_code": "123456", "userId": "user_771" }
    ```
*   **Response (200 OK):**
    ```json
    { "verified": true, "session_token": "abc..." }
    ```

### 4.8 `DELETE /users/{id}/session`
*   **Description:** Force-logs out a user from all devices.
*   **Response (204 No Content):** `Empty`

---

## 5. DATABASE SCHEMA

The database is hosted on Cloudflare D1. All primary keys are UUIDs.

### 5.1 Table Definitions

1.  **`users`**: Core identity data.
    *   `user_id` (UUID, PK), `email` (TEXT, UNIQUE), `password_hash` (TEXT), `role_id` (FK), `mfa_enabled` (BOOLEAN), `created_at` (TIMESTAMP).
2.  **`roles`**: Defines RBAC levels.
    *   `role_id` (INT, PK), `role_name` (TEXT: 'Admin', 'Broker', etc.), `permissions` (JSONB).
3.  **`properties`**: Real estate asset data.
    *   `property_id` (UUID, PK), `address` (TEXT), `valuation` (DECIMAL), `owner_id` (FK), `status` (TEXT), `last_modified` (TIMESTAMP).
4.  **`portfolio_mapping`**: Links users to portfolios.
    *   `mapping_id` (UUID, PK), `user_id` (FK), `property_id` (FK), `access_level` (INT).
5.  **`user_preferences`**: Dashboard and UI settings.
    *   `pref_id` (UUID, PK), `user_id` (FK), `dashboard_json` (JSONB), `theme` (TEXT).
6.  **`report_schedules`**: Automation for PDF delivery.
    *   `schedule_id` (UUID, PK), `user_id` (FK), `template_id` (TEXT), `frequency` (TEXT), `delivery_email` (TEXT).
7.  **`report_logs`**: Audit trail for report generation.
    *   `log_id` (UUID, PK), `schedule_id` (FK), `generated_at` (TIMESTAMP), `status` (TEXT), `file_path` (TEXT).
8.  **`transactions`**: Financial records for PCI processing.
    *   `tx_id` (UUID, PK), `user_id` (FK), `amount` (DECIMAL), `currency` (TEXT), `status` (TEXT), `timestamp` (TIMESTAMP).
9.  **`mfa_secrets`**: Encrypted TOTP keys.
    *   `secret_id` (UUID, PK), `user_id` (FK), `encrypted_secret` (TEXT), `recovery_codes` (TEXT).
10. **`audit_logs`**: System-wide event tracking.
    *   `event_id` (UUID, PK), `user_id` (FK), `action` (TEXT), `ip_address` (TEXT), `timestamp` (TIMESTAMP).

### 5.2 Key Relationships
*   `users` $\xrightarrow{N:1}$ `roles`
*   `users` $\xrightarrow{1:N}$ `portfolio_mapping` $\xrightarrow{N:1}$ `properties`
*   `users` $\xrightarrow{1:N}$ `report_schedules`
*   `users` $\xrightarrow{1:1}$ `user_preferences`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Drift utilizes a strict three-environment pipeline to ensure stability and PCI compliance.

1.  **Development (DEV):**
    *   **Purpose:** Feature iteration and initial testing.
    *   **Access:** Full team (Meera, Rafik, Yara, Orin).
    *   **Data:** Mock data only.
    *   **Deployment:** Continuous Integration (CI) on every push to `dev` branch.
2.  **Staging (STG):**
    *   **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
    *   **Access:** Project Lead and Anchor Client representative.
    *   **Data:** Anonymized production snapshots.
    *   **Deployment:** Triggered upon successful merge to `release` branch.
3.  **Production (PROD):**
    *   **Purpose:** Live environment for the enterprise client.
    *   **Access:** Restricted to Meera Costa and Rafik Santos.
    *   **Data:** Live, PCI-encrypted data.
    *   **Deployment:** Weekly Release Train (Fridays 04:00 UTC).

### 6.2 The Release Train
The project operates on a **Non-Negotiable Weekly Release Train**. 
*   **Cut-off:** All code must be merged to the `release` branch by Thursday 20:00 UTC.
*   **Deployment:** Friday 04:00 UTC.
*   **Hotfixes:** No hotfixes are permitted outside the release train. If a critical bug is found, it is patched in DEV/STG and deployed on the following Friday. This prevents "configuration drift" and ensures the PCI audit trail remains clean.

---

## 7. TESTING STRATEGY

Given the "shoestring" budget and high-risk stack, testing is automated to reduce manual QA overhead.

### 7.1 Unit Testing
*   **Backend (Rust):** Using `cargo test`. Every business logic function must have $\ge 80\%$ coverage. Focus on the conflict resolution logic in the collaborative editing module.
*   **Frontend (React):** Using Jest and React Testing Library. Focus on widget rendering and form validation.

### 7.2 Integration Testing
*   **API Testing:** Postman collections are used to validate all 8 core endpoints. Tests are integrated into the CI pipeline via Newman.
*   **Database Tests:** SQLite-specific tests to ensure that local-to-cloud synchronization does not result in data loss.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Critical Paths:** 
    *   User Login $\rightarrow$ Dashboard Customization $\rightarrow$ Property Edit $\rightarrow$ Report Generation.
    *   Payment Processing flow (using Stripe Sandbox).
*   **Frequency:** E2E suite runs once every Wednesday to identify blockers before the Friday release train.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Team has no experience with Rust/Cloudflare Workers | High | High | Accept risk; monitor weekly velocity. Implement aggressive peer reviews. |
| R2 | Regulatory requirements for real estate may change | Medium | Medium | De-scope affected features if unresolved by Milestone date. |
| R3 | PCI DSS Level 1 audit failure | Low | Critical | Use tokenization; strictly isolate payment logic; conduct monthly internal audits. |
| R4 | "God Class" technical debt causes system crash | Medium | High | Refactor in 2-week sprints; isolate Auth, Logging, and Email into micro-services. |
| R5 | Budget exhaustion ($150k limit) | Low | High | Strict scrutiny of infrastructure costs; no new tool acquisitions without Meera's approval. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases
1.  **Phase 1: Infrastructure & Auth (Now $\rightarrow$ Aug 2025):** Focus on breaking the God Class and establishing the PCI vault.
2.  **Phase 2: Core Feature Set (Aug $\rightarrow$ Oct 2025):** Implementation of dashboards and report generation.
3.  **Phase 3: Polish & Benchmarking (Oct $\rightarrow$ Dec 2025):** Performance tuning and final client sign-off.

### 9.2 Key Milestones
*   **Milestone 1: Production Launch (Target: 2025-08-15)**
    *   *Dependencies:* RBAC complete, PCI DSS certification, Basic Portfolio view.
*   **Milestone 2: Internal Alpha Release (Target: 2025-10-15)**
    *   *Dependencies:* Dashboard widgets functional, Collaborative editing verified.
*   **Milestone 3: Performance Benchmarks Met (Target: 2025-12-15)**
    *   *Dependencies:* API response time $< 100ms$, PDF generation $< 10s$.

---

## 10. MEETING NOTES

### Meeting 1: Technical Stack Alignment
**Date:** 2023-11-02 | **Attendees:** Meera, Rafik, Yara, Orin
**Discussion:**
*   Rafik expressed concern regarding the learning curve for Rust. Meera acknowledged the risk but emphasized the need for the performance profile for the anchor client.
*   Yara raised a point about the dashboard; she wants "true" drag-and-drop, not just a list of widgets.
*   Orin asked about the God Class. Rafik warned him not to touch it until the refactoring plan is approved.
**Action Items:**
*   Rafik to set up the Cloudflare Worker environment. (Owner: Rafik)
*   Yara to provide Figma mocks for the 12-column dashboard grid. (Owner: Yara)

### Meeting 2: PCI Compliance Review
**Date:** 2023-11-15 | **Attendees:** Meera, Rafik
**Discussion:**
*   Meera emphasized that we cannot use a 3rd party "easy" checkout; the client wants direct control over the payment flow, requiring PCI Level 1.
*   Rafik noted that this means the Rust backend must handle encryption at the field level before hitting D1.
*   Decision: We will implement a dedicated "Vault Service" to separate card data from user profiles.
**Action Items:**
*   Rafik to draft the encryption schema for the `transactions` table. (Owner: Rafik)
*   Meera to verify the audit requirements with the client's legal team. (Owner: Meera)

### Meeting 3: Release Train Implementation
**Date:** 2023-12-01 | **Attendees:** Meera, Rafik, Yara, Orin
**Discussion:**
*   Meera introduced the "No Hotfix" rule. The team reacted with hesitation, especially Orin, who feared "breaking prod" for a week.
*   Meera explained that for a $2M client, stability is more important than agility.
*   Decision: All "Critical" bugs will be handled via a feature-flag toggle (off-switch) rather than a hotfix.
**Action Items:**
*   Meera to implement a feature-flagging system (e.g., Unleash or custom). (Owner: Meera)
*   Rafik to create the GitHub Action for the Friday 04:00 UTC deploy. (Owner: Rafik)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $105,000 | Adjusted for 8-person team across 2 time zones. |
| **Infrastructure** | 15% | $22,500 | Cloudflare Workers, D1, R2, and Stripe fees. |
| **Tools & Licenses** | 5% | $7,500 | Figma, GitHub Enterprise, Postman, Playwright. |
| **Contingency** | 10% | $15,000 | Reserved for regulatory changes (Risk R2). |

*Note: Personnel costs are highly subsidized by the company as this is a strategic vertical.*

---

## 12. APPENDICES

### Appendix A: God Class Refactoring Plan
The current `CoreManager.rs` is 3,000 lines and handles `Auth`, `Log`, and `Email`. 
1.  **Step 1 (Isolation):** Wrap all `Email` calls in a trait. Move them to `NotificationEngine.rs`.
2.  **Step 2 (Extraction):** Move `Log` logic into a dedicated `AuditLogger` module that writes directly to the `audit_logs` table.
3.  **Step 3 (Purge):** The remaining `CoreManager.rs` will be renamed `AuthService.rs` and focused solely on session and role management.

### Appendix B: Collaborative Editing Conflict Matrix
| Scenario | Action A (User 1) | Action B (User 2) | Result | Logic |
| :--- | :--- | :--- | :--- | :--- |
| Field Update | Set Val = 1M | Set Val = 1.1M | 1.1M | Last Write Wins (Timestamp) |
| Status Change | Set 'Sold' | Set 'Under Contract' | 'Sold' | Status Hierarchy (Sold > Contract) |
| Deletion | Delete Property | Edit Property | Delete | Deletion takes precedence |
| Simultaneous | Edit Field X | Edit Field Y | Both Saved | Independent Field Updates |