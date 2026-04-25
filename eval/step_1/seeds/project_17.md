# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Status:** Baseline Approved  
**Company:** Flintrock Engineering  
**Project Code:** GLACIER-2025  
**Last Updated:** 2024-11-14  
**Classification:** Confidential / Internal Only

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Glacier represents a strategic pivot for Flintrock Engineering. While the firm has a storied history in industrial automation and general hardware engineering, Glacier marks the company’s inaugural foray into the healthcare IoT sector. The objective is to build a greenfield IoT device network designed for high-reliability medical data ingestion, edge processing, and centralized cloud visualization. 

The system is designed to bridge the gap between bedside medical instrumentation and administrative healthcare dashboards, providing a secure, low-latency pipeline for real-time patient telemetry and device health monitoring. Because this is a new market for Flintrock, Project Glacier is not merely a technical challenge but a market-entry vehicle.

### 1.2 Business Justification
The healthcare IoT market is currently experiencing a CAGR of 14.2%, driven by the shift toward remote patient monitoring (RPM) and the digitization of hospital assets. Flintrock’s core competency in robust hardware integration provides a competitive advantage in reliability—a critical requirement in healthcare where downtime can lead to patient harm. 

By developing a proprietary, high-performance network using Rust and Cloudflare Workers, Flintrock can offer a product that outperforms legacy healthcare systems in terms of latency and data integrity. The "greenfield" nature of the project allows the team to avoid the "technical baggage" of legacy healthcare protocols, implementing a modern, API-first architecture from the ground up.

### 1.3 ROI Projection
The budget for Project Glacier is set at $800,000 for a 6-month build cycle. The projected Return on Investment (ROI) is calculated based on a three-year horizon:

*   **Year 1 (Market Entry):** Focus on Beta partnerships with three regional clinics. Projected revenue is minimal, focusing on validation and NPS growth.
*   **Year 2 (Scaling):** Expected conversion of Beta sites to paid subscriptions and the acquisition of 15 mid-sized hospitals. Projected Revenue: $2.1M.
*   **Year 3 (Market Leadership):** Expansion into national healthcare networks. Projected Revenue: $5.5M.

The estimated Net Present Value (NPV) of the project over 36 months, assuming a discount rate of 10%, is approximately $3.8M. The Break-Even Point (BEP) is anticipated at Month 14 post-production launch.

### 1.4 Strategic Alignment
Glacier aligns with Flintrock Engineering’s goal of diversifying revenue streams away from traditional industrial contracts. By establishing a foothold in healthcare, the company mitigates the risk of industrial market downturns and positions itself as a leader in "Critical Infrastructure IoT."

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Glacier employs a traditional three-tier architecture (Presentation, Business Logic, Data) but optimizes the "Data" tier using a hybrid Edge-to-Cloud model. To ensure the extreme reliability required for healthcare, the system minimizes the number of moving parts between the medical device and the data storage layer.

### 2.2 The Stack
*   **Backend:** Rust (utilizing the Axum framework for the API and Tokio for asynchronous runtime). Rust was chosen for its memory safety and performance, eliminating the possibility of null-pointer exceptions during critical medical data processing.
*   **Frontend:** React 18.2 (TypeScript) with Tailwind CSS for the administrative dashboard and device management portal.
*   **Edge Storage:** SQLite. Each IoT gateway device runs a local SQLite instance to buffer data during network outages, ensuring zero data loss.
*   **Cloud Infrastructure:** Cloudflare Workers. The business logic is deployed as serverless functions to ensure global distribution and minimal latency.
*   **CI/CD:** GitHub Actions for automated testing and deployment pipelines.
*   **Deployment Strategy:** Blue-Green deployment. Two identical production environments are maintained; the "Green" environment is updated and tested before traffic is cut over from "Blue."

### 2.3 System Topology (ASCII Representation)

```text
[ Medical IoT Devices ]  <-- (MQTT/CoAP) --> [ Edge Gateway ]
                                              | (Local SQLite Buffer)
                                              v
[ Cloudflare Network ] <---------------- [ Rust Backend (Workers) ]
       |                                       |
       |--> [ Auth Layer (OIDC/SAML) ] <-------|
       |                                       |
       |--> [ Data Logic/Processing ] <--------|
       |                                       |
       v                                       v
[ Global Database ] <------------------- [ Persistent Storage ]
       ^                                       ^
       |                                       |
[ React Admin Dashboard ] <--- (REST/JSON) ----|
```

### 2.4 Data Flow Description
1.  **Ingestion:** IoT devices push telemetry data to the Edge Gateway.
2.  **Buffering:** The Gateway writes data to a local SQLite database. This protects against the "Internet Outage" scenario common in large hospital complexes.
3.  **Synchronization:** The Gateway syncs data to the Rust backend via encrypted HTTPS requests.
4.  **Processing:** Cloudflare Workers execute the business logic (filtering, alerting, and formatting).
5.  **Consumption:** The React frontend queries the backend via REST API to visualize patient data.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Functional Description:**
The system must allow healthcare administrators to import legacy patient and device data from various formats (.csv, .json, .xml, .hl7) and export current system data for regulatory audits. The core innovation is the "Auto-Detection Engine," which analyzes the first 100 lines of any uploaded file to determine the schema and format without requiring user input.

**Technical Requirements:**
*   **Analysis Pipeline:** The Rust backend will implement a "Magic Byte" check followed by a regex-based pattern matching system to identify HL7 (Health Level 7) versus standard CSVs.
*   **Validation:** Upon detection, the system will map the detected columns to the internal Glacier schema. If a confidence score is below 85%, the system will prompt the user with a "Suggested Mapping" interface.
*   **Export Logic:** Exports must be generated as streamed responses to prevent memory overflow when handling datasets exceeding 1GB.
*   **Audit Trail:** Every import/export action must be logged in the `audit_logs` table, including the user ID, timestamp, and checksum of the file.

**User Workflow:**
1. User navigates to "Data Management" $\rightarrow$ "Import."
2. User uploads a file (e.g., `patient_records_2023.csv`).
3. System identifies the file as CSV, detects columns `PatientID`, `HeartRate`, and `Timestamp`.
4. System presents a preview: "Detected as Medical Telemetry CSV. Import 14,000 records?"
5. User confirms; data is ingested into the database.

### 3.2 SSO Integration (SAML and OIDC Providers)
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Functional Description:**
Given the healthcare context, individual passwords are a security liability. Project Glacier must integrate Single Sign-On (SSO) to allow hospital staff to use their institutional credentials (e.g., Azure AD, Okta, PingIdentity). The system must support both Security Assertion Markup Language (SAML 2.0) and OpenID Connect (OIDC).

**Technical Requirements:**
*   **OIDC Flow:** Implementation of the Authorization Code Flow with PKCE (Proof Key for Code Exchange) to secure the React frontend.
*   **SAML Integration:** The backend must handle XML-based SAML assertions, including signature verification using the provider's public key.
*   **Attribute Mapping:** The system must map "Claims" from the provider (e.g., `role: chief_surgeon`) to internal Glacier permissions (`role: admin`).
*   **Session Management:** JWTs (JSON Web Tokens) will be issued upon successful SSO authentication, stored in `HttpOnly` cookies to prevent XSS attacks.

**Current Blocker:** The project is waiting for the security team to provide the metadata XML files from the primary test provider.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Functional Description:**
Users may need to upload device manuals, patient reports, or calibration certificates. These files must be scanned for malware to prevent the "Patient Zero" scenario where a malicious file infects the hospital network. Once scanned, files should be cached on a Content Delivery Network (CDN) for fast global access.

**Technical Requirements:**
*   **Scan Pipeline:** Upon upload, the file is sent to an isolated sandbox (ClamAV or a similar API) for scanning.
*   **Quarantine:** Files marked as "Infected" are immediately deleted and the event is logged in the security dashboard.
*   **CDN Integration:** Clean files are pushed to Cloudflare R2 (Object Storage) and served via the Cloudflare CDN.
*   **Access Control:** Files are not public; they are served via "Signed URLs" that expire after 15 minutes.

### 3.4 A/B Testing Framework (Feature Flag Integrated)
**Priority:** High | **Status:** In Design

**Functional Description:**
To optimize the UI for different medical specialties (e.g., Cardiology vs. Neurology), the team needs a way to roll out features to a subset of users. This will be built directly into the feature flag system rather than as a separate library.

**Technical Requirements:**
*   **Flag Logic:** The Rust backend will maintain a `feature_flags` table. Each flag can be associated with a "Percentage Rollout" (e.g., 10% of users see the new dashboard).
*   **Bucket Assignment:** Users are assigned a persistent "Bucket ID" (hash of UserID + Salt) to ensure a consistent experience (no flipping between A and B versions).
*   **Analytics Integration:** Every action taken within an A/B test variant must be tagged with the variant ID in the `usage_analytics` table.
*   **Control Group:** The system must always maintain a "Control" group to measure the baseline performance against the "Treatment" group.

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Design

**Functional Description:**
To prevent Denial-of-Service (DoS) attacks and ensure fair resource distribution among different hospital clients, the API must implement strict rate limiting. Simultaneously, the system must track usage patterns to inform future billing and scaling decisions.

**Technical Requirements:**
*   **Algorithm:** A "Token Bucket" algorithm implemented at the Cloudflare Worker level.
*   **Limits:** Default limits set to 1,000 requests per minute per API key, with "Burst" capacity of 1,500.
*   **Headers:** All responses must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
*   **Analytics Pipeline:** Every request is logged to a time-series database (or specialized SQLite table) capturing: Endpoint, Response Time, User Agent, and Status Code.
*   **Alerting:** If an API key hits the rate limit 5 times in one hour, an automated alert is sent to Zev Park (Support Engineer).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication requires a Bearer Token in the header.

### 4.1 `POST /devices/register`
**Description:** Registers a new IoT device to the network.
*   **Request Body:**
    ```json
    {
      "device_id": "GLA-9902-X",
      "model": "HeartRate-Pro",
      "firmware_version": "1.0.2",
      "location_id": "WARD-4B"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "status": "success",
      "device_token": "auth_token_88231",
      "created_at": "2025-01-10T10:00:00Z"
    }
    ```

### 4.2 `GET /telemetry/{device_id}`
**Description:** Retrieves the most recent telemetry data for a specific device.
*   **Response (200 OK):**
    ```json
    {
      "device_id": "GLA-9902-X",
      "last_reading": {
        "value": 72,
        "unit": "bpm",
        "timestamp": "2025-01-10T10:05:00Z"
      },
      "status": "online"
    }
    ```

### 4.3 `POST /data/import`
**Description:** Uploads a file for auto-detection and import.
*   **Request:** Multipart form-data (File upload).
*   **Response (202 Accepted):**
    ```json
    {
      "job_id": "import_5543",
      "status": "processing",
      "estimated_time": "30s"
    }
    ```

### 4.4 `GET /analytics/usage`
**Description:** Retrieves API usage statistics for the current organization.
*   **Response (200 OK):**
    ```json
    {
      "total_requests": 145000,
      "error_rate": "0.02%",
      "p95_latency": "120ms"
    }
    ```

### 4.5 `POST /auth/sso/login`
**Description:** Initiates the SSO handshake.
*   **Request Body:**
    ```json
    {
      "provider": "okta",
      "callback_url": "https://glacier.med/auth/callback"
    }
    ```
*   **Response (302 Redirect):** Redirects to the provider's login page.

### 4.6 `PATCH /devices/{device_id}/config`
**Description:** Updates device configuration (e.g., sampling rate).
*   **Request Body:**
    ```json
    {
      "sampling_rate_seconds": 30,
      "alert_threshold": 120
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "updated", "effective_date": "2025-01-10T10:10:00Z" }
    ```

### 4.7 `GET /users/profile`
**Description:** Returns the current authenticated user's profile and roles.
*   **Response (200 OK):**
    ```json
    {
      "username": "r.jensen",
      "role": "CTO",
      "permissions": ["admin", "billing", "system_config"]
    }
    ```

### 4.8 `DELETE /devices/{device_id}`
**Description:** Decommissions a device and archives its data.
*   **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The system uses a relational model. The Edge uses SQLite, while the Cloud layer uses a distributed PostgreSQL-compatible store (via Cloudflare D1/Hyperdrive).

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `organizations` | `org_id` (PK), `name`, `sso_config` | 1:N with `users` | Top-level entity (The Hospital). |
| `users` | `user_id` (PK), `org_id` (FK), `email`, `role` | N:1 with `organizations` | Personnel accessing the dashboard. |
| `devices` | `device_id` (PK), `org_id` (FK), `model`, `status` | N:1 with `organizations` | The physical IoT sensors. |
| `telemetry` | `reading_id` (PK), `device_id` (FK), `val`, `ts` | N:1 with `devices` | The raw medical readings. |
| `audit_logs` | `log_id` (PK), `user_id` (FK), `action`, `timestamp` | N:1 with `users` | Record of all sensitive actions. |
| `feature_flags` | `flag_id` (PK), `key`, `is_enabled`, `rollout_pct` | None | Controls A/B test variants. |
| `user_flags` | `mapping_id` (PK), `user_id` (FK), `flag_id` (FK) | N:1 with `users`, `flags` | Specific flag assignments for users. |
| `usage_analytics` | `event_id` (PK), `org_id` (FK), `endpoint`, `latency` | N:1 with `organizations` | API performance tracking. |
| `import_jobs` | `job_id` (PK), `user_id` (FK), `status`, `file_hash` | N:1 with `users` | Tracks status of data imports. |
| `device_configs` | `config_id` (PK), `device_id` (FK), `param`, `value` | N:1 with `devices` | Key-value store for device settings. |

### 5.2 Relationship Logic
*   **Cascading Deletes:** If an `organization` is deleted, all associated `users` and `devices` are purged.
*   **Indexing:** B-Tree indexes are placed on `telemetry(device_id, ts)` to ensure that time-series queries for a specific device remain under 50ms.
*   **Constraint:** A unique constraint exists on `devices(device_id)` to prevent duplicate registration of the same hardware.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Glacier utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
*   **Purpose:** Daily feature iteration and unit testing.
*   **Infrastructure:** Individual developer branches deployed to ephemeral Cloudflare Worker namespaces.
*   **Database:** Local SQLite instances and a shared "Dev" D1 database.
*   **Access:** All 8 team members.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Pre-production validation and QA.
*   **Infrastructure:** A mirrored version of the production environment.
*   **Database:** A sanitized clone of production data (PII removed).
*   **Access:** Project Lead, Frontend Lead, and Product Designer.
*   **Deployment:** Triggered automatically upon merging a PR into the `develop` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live healthcare environment.
*   **Infrastructure:** Full Cloudflare Global Network with Blue-Green deployment capabilities.
*   **Database:** High-availability distributed cluster with daily snapshots.
*   **Access:** Strictly controlled via SSO; only Renzo Jensen can trigger the final "Green" cut-over.

### 6.2 CI/CD Pipeline
Using GitHub Actions, the pipeline follows these steps:
1.  **Lint & Format:** `cargo fmt` and `eslint` check for style violations.
2.  **Test:** Run unit tests and integration tests. If any fail, the build is rejected.
3.  **Build:** Compile Rust to WebAssembly (Wasm) for Cloudflare Workers.
4.  **Deploy to Stage:** Push to the Staging environment.
5.  **Smoke Test:** Automated scripts verify the `/health` endpoint.
6.  **Production Push:** Upon manual approval, the build is deployed to the "Green" slot.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Backend (Rust):** Every business logic function must have associated `#[test]` blocks. Focus is on edge cases (e.g., null values in telemetry, invalid SAML assertions).
*   **Frontend (React):** Vitest and React Testing Library are used to test component rendering and state transitions.
*   **Coverage Goal:** 80% minimum code coverage.

### 7.2 Integration Testing
*   **API Testing:** Postman collections are integrated into GitHub Actions to verify that the Rust backend and the database communicate correctly.
*   **End-to-End (E2E) Flow:** A "Golden Path" test is run daily:
    `Device Registration` $\rightarrow$ `Telemetry Push` $\rightarrow$ `Dashboard Visualization` $\rightarrow$ `Data Export`.
*   **Tooling:** Playwright for E2E browser automation.

### 7.3 End-to-End and Stress Testing
*   **Latency Testing:** Measuring the time from a device signal to a dashboard update. Target: $< 500\text{ms}$.
*   **Load Testing:** Using k6 to simulate 5,000 concurrent devices pushing data every 10 seconds.
*   **Penetration Testing:** Quarterly external security audits focusing on the SSO bypass and API injection.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor announced EOL for critical component | High | Critical | **Parallel-Path:** Prototype an alternative approach using a different hardware vendor simultaneously. |
| R-02 | Project sponsor is rotating out of their role | Medium | High | **External Audit:** Engage a third-party consultant for an independent assessment to ensure project continuity. |
| R-03 | Healthcare data compliance breach | Low | Critical | Quarterly penetration testing and strict AES-256 encryption at rest. |
| R-04 | "God Class" technical debt causes crash | High | Medium | **Incremental Refactor:** Break down the 3,000-line class into `AuthService`, `LoggingService`, and `EmailService` across 3 sprints. |
| R-05 | Timezone lag between team members | Medium | Low | Formalize communication via JIRA; all decisions must be documented in writing. |

**Impact Matrix:**
*   *Critical:* Project failure or legal liability.
*   *High:* Major milestone delay.
*   *Medium:* Feature degradation.
*   *Low:* Minor inconvenience.

---

## 9. TIMELINE

Project Glacier follows a 6-month aggressive build cycle.

### Phase 1: Foundation (Months 1-2)
*   **Focus:** Infrastructure setup, Basic API, and Edge Gateway prototype.
*   **Key Dependency:** Finalization of the Rust-to-Wasm pipeline.
*   **Milestones:** Establish CI/CD; implement Basic Device Registration.

### Phase 2: Core Features (Months 3-4)
*   **Focus:** Data Import/Export, SSO Integration, and A/B Framework.
*   **Key Dependency:** Receipt of SAML metadata from providers.
*   **Milestones:** Feature 1 and 2 marked as "Completed."

### Phase 3: Hardening & Launch (Months 5-6)
*   **Focus:** Stress testing, refactoring the "God Class," and final UX polish.
*   **Key Dependency:** Successful penetration test.
*   **Milestones:**
    *   **2025-12-15:** Production Launch.

### Post-Launch Stability
*   **2025-08-15:** Post-launch stability confirmed (Note: This is a backward-looking audit of the first 8 months of the roadmap).
*   **2025-10-15:** Performance benchmarks met (Latency $< 500\text{ms}$).

---

## 10. MEETING NOTES

### Meeting 1: Architecture Baseline
**Date:** 2024-11-01 | **Attendees:** Renzo, Beatriz, Wyatt, Zev
*   **Discussion:** Debate over using a heavy backend (Kubernetes) vs. Lightweight (Cloudflare Workers). Renzo insisted on Workers to minimize operational overhead for a new market entry.
*   **Decision:** Adopt the Three-Tier architecture with Rust/Wasm on Cloudflare.
*   **Action Items:**
    *   Beatriz: Set up the React boilerplate. (Owner: Beatriz)
    *   Renzo: Configure the GitHub Actions workflow. (Owner: Renzo)

### Meeting 2: The "God Class" Crisis
**Date:** 2024-11-15 | **Attendees:** Renzo, Zev
*   **Discussion:** Zev pointed out that the `CoreManager` class has reached 3,000 lines and is causing merge conflicts every 48 hours. It currently handles Auth, Logging, and Email.
*   **Decision:** The class will not be deleted immediately to avoid breaking the build, but a "Strangler Fig" pattern will be used to migrate logic to smaller services.
*   **Action Items:**
    *   Zev: Map all dependencies of `CoreManager`. (Owner: Zev)

### Meeting 3: Vendor EOL Strategy
**Date:** 2024-12-05 | **Attendees:** Renzo, Wyatt
*   **Discussion:** The primary sensor vendor announced EOL for the v2 chip. If we rely solely on them, the product will be dead on arrival.
*   **Decision:** Start a "Parallel Path" prototype using the alternative chipset immediately. Budget allocated for 2 prototype boards.
*   **Action Items:**
    *   Wyatt: Update the hardware specs for the alternative chip. (Owner: Wyatt)
    *   Renzo: Reach out to the external consultant for the sponsor rotation risk. (Owner: Renzo)

---

## 11. BUDGET BREAKDOWN

The total budget of **$800,000** is allocated as follows:

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | 8 engineers/designers over 6 months. |
| **Infrastructure** | 10% | $80,000 | Cloudflare Workers, R2, D1, and GitHub Enterprise. |
| **Tools & Hardware** | 10% | $80,000 | IoT Prototyping boards, IDE licenses, and Testing devices. |
| **Consulting** | 5% | $40,000 | External independent assessment for sponsor rotation. |
| **Contingency** | 5% | $40,000 | Emergency buffer for vendor pivots. |

---

## 12. APPENDICES

### Appendix A: The "God Class" Refactor Map
The current `CoreManager.rs` contains:
1.  `fn authenticate_user()` $\rightarrow$ Move to `services/auth.rs`
2.  `fn log_system_event()` $\rightarrow$ Move to `services/logger.rs`
3.  `fn send_notification_email()` $\rightarrow$ Move to `services/email.rs`
4.  `fn validate_token()` $\rightarrow$ Move to `services/auth.rs`

### Appendix B: Security Hardening Checklist
*   [ ] All API endpoints implement Rate Limiting.
*   [ ] SAML assertions are signed and verified.
*   [ ] No PII is stored in plain text in SQLite buffers.
*   [ ] All production secrets are stored in Cloudflare Secrets, not in the repository.
*   [ ] Blue-Green switch requires a 2-person approval (CTO + Lead Dev).