# PROJECT SPECIFICATION: PROJECT HARBINGER
**Document Version:** 1.0.4  
**Status:** Active / Draft  
**Last Updated:** 2024-05-20  
**Company:** Stratos Systems  
**Classification:** Internal / Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project Harbinger represents a pivotal shift in Stratos Systems' approach to agricultural technology. Originally conceived as a rapid prototype during a company-wide hackathon, Harbinger has evolved from a proof-of-concept into a mission-critical internal productivity tool. Currently serving 500 daily active users (DAU) across our internal ag-tech research and development divisions, the tool streamlines the orchestration of embedded firmware deployments to remote agricultural sensors and autonomous machinery.

The core value proposition of Harbinger is the reduction of "sensor-to-insight" latency. By providing a unified interface for firmware management, telemetry monitoring, and device configuration, Harbinger replaces a fragmented set of legacy bash scripts and manual SSH workflows. 

### 1.2 Business Justification
The agricultural sector is currently undergoing a massive digital transformation. The ability to deploy updates to thousands of field-deployed devices without physical intervention is not merely a convenience—it is a competitive necessity. Stratos Systems has identified a gap in the market for a "Firmware-as-a-Service" (FaaS) layer tailored specifically for high-latency, low-bandwidth agricultural environments (e.g., remote cornfields with sporadic LTE/LoRaWAN connectivity).

Internal metrics indicate that before Harbinger, the average time to deploy a critical firmware patch across a test fleet was 4.5 business days. With the prototype version of Harbinger, this has been reduced to 6 hours. This 98% increase in operational efficiency directly translates to faster R&D cycles and reduced hardware downtime.

### 1.3 ROI Projection and Budget
Stratos Systems has allocated a substantial budget of $3,000,000 for the formalization and scaling of Harbinger. This investment is justified by three primary revenue and cost-saving streams:
1. **Reduction in Field Engineering Costs:** By automating firmware recovery and updates, we project a reduction of $400,000 per year in travel and labor costs for field technicians.
2. **Accelerated Time-to-Market:** Reducing the firmware iteration cycle allows the company to launch new sensor products 3 months ahead of schedule, providing an estimated first-mover advantage valued at $1.2M in potential early contracts.
3. **SaaS Transition:** While currently an internal tool, the long-term roadmap involves pivoting Harbinger into a commercial product for external ag-tech firms. Based on a projected subscription model of $50/device/month, a modest 10,000-device rollout would generate $6M in Annual Recurring Revenue (ARR).

The project is under high executive visibility, as it serves as the flagship demonstration of Stratos Systems' ability to modernize its internal tooling and transition toward a cloud-native architecture.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Harbinger utilizes a modern, highly concurrent stack designed for real-time updates and high availability. The core is built using **Elixir** and the **Phoenix Framework**, leveraging the Erlang VM (BEAM) for its legendary fault tolerance and ability to handle thousands of simultaneous connections—critical for managing a fleet of embedded devices.

The frontend is implemented using **Phoenix LiveView**, allowing the team to push real-time telemetry data from agricultural sensors directly to the user's browser via WebSockets, eliminating the need for a heavy React/Vue state management layer.

### 2.2 Architectural Diagram (ASCII)

```text
[ Field Sensors/Hardware ] <---(MQTT/HTTPS)---> [ Fly.io Load Balancer ]
                                                      |
                                                      v
                                           +-----------------------+
                                           |   Phoenix Application |
                                           |  (Modular Monolith)   |
                                           +-----------+-----------+
                                                       |
           +-----------------------+--------------------+-----------------------+
           |                       |                                           |
 [ LiveView Frontend ]    [ Core Business Logic ]                    [ Background Jobs ]
 (Real-time Dashboard)     (Firmware Orchestrator)                   (Oban / Queue)
           |                       |                                           |
           +-----------------------+--------------------+-----------------------+
                                                       |
                                           +-----------v-----------+
                                           |   PostgreSQL DB       |
                                           | (Relational Storage)   |
                                           +-----------------------+
                                                       |
                                           +-----------v-----------+
                                           |  Tamper-Evident Log   |
                                           | (Audit Trail Storage) |
                                           +-----------------------+
```

### 2.3 Component Details
- **Application Layer:** The system is currently a **modular monolith**. This allows the team of six to maintain a single codebase and deployment pipeline while maintaining clear boundary separation between modules (e.g., `Billing`, `DeviceManagement`, `Auth`). The long-term strategy is an incremental transition to microservices as the load increases.
- **Persistence:** **PostgreSQL** serves as the primary source of truth. High-frequency telemetry is handled via optimized time-series tables within Postgres.
- **Infrastructure:** The application is deployed on **Fly.io**, utilizing their global edge network to reduce latency for international users.
- **Deployment Pipeline:** CI/CD is handled via **GitHub Actions**. We employ a **blue-green deployment** strategy: a new version of the app is spun up alongside the old one; traffic is shifted only after health checks pass, ensuring zero-downtime updates.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** In Design

**Description:**
Agricultural data arrives in a chaotic variety of formats (CSV, JSON, XML, and proprietary binary formats from older sensor hardware). Users must be able to upload these files without manually specifying the format. The system must analyze the first 1KB of the file to determine the MIME type and structure.

**Functional Requirements:**
1. **Auto-Detection Engine:** The system shall implement a "magic byte" analysis to identify file types. For CSVs, the engine must detect delimiters (comma, tab, semicolon) and encoding (UTF-8, Latin-1).
2. **Mapping Interface:** Once the format is detected, the user is presented with a mapping screen where they can map detected columns (e.g., "temp_c") to internal system fields (e.g., `ambient_temperature`).
3. **Bulk Export:** Users can export filtered device data into any of the supported formats.
4. **Validation:** All imports must undergo a "Dry Run" phase where the system reports potential data type mismatches (e.g., string found where float expected) before committing to the database.

**Technical Implementation:**
The import process will be handled by an `Oban` background worker to prevent blocking the web request. Files will be uploaded to an S3-compatible bucket, and a `DataImport` record will be created in the database to track the status of the import.

---

### 3.2 Localization and Internationalization (L10n/i18n)
**Priority:** Medium | **Status:** In Review

**Description:**
Stratos Systems is expanding into markets across Brazil, India, and the EU. Harbinger must support 12 distinct languages to allow local field operators to interact with the system in their native tongue.

**Functional Requirements:**
1. **Language Support:** Initial launch must support English, Spanish, Portuguese, French, German, Mandarin, Japanese, Hindi, Arabic, Russian, Dutch, and Italian.
2. **Dynamic Switching:** Users must be able to switch languages via a dropdown in the user profile, with the preference saved in the `users` table.
3. **RTL Support:** For Arabic, the Phoenix LiveView templates must support Right-to-Left (RTL) CSS mirroring.
4. **Date/Currency Formatting:** The system must automatically format dates (DD/MM/YYYY vs MM/DD/YYYY) and currency based on the selected locale.

**Technical Implementation:**
We will use the `Gettext` library integrated with Phoenix. Translation files (`.po` files) will be stored in the `/priv/gettext` directory. A custom helper function `__(message)` will be used throughout the codebase to wrap all user-facing strings.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Description:**
Due to the high visibility of this project and the sensitivity of the firmware being deployed, every administrative action (e.g., "Update Firmware on Fleet A") must be logged in a way that cannot be altered, even by a database administrator.

**Functional Requirements:**
1. **Comprehensive Logging:** Every `POST`, `PATCH`, and `DELETE` request must be logged, including the user ID, timestamp, IP address, old value, and new value.
2. **Tamper-Evidence:** The system shall implement a cryptographic chain (similar to a blockchain). Each log entry will contain a SHA-256 hash of the previous entry, creating a linear chain.
3. **Verification Tool:** A daily automated task must verify the integrity of the hash chain. If a hash mismatch is detected, an immediate alert is sent to the Security Engineer (Luciano Kim).
4. **Immutable Storage:** Logs will be mirrored to a write-once-read-many (WORM) storage bucket.

**Technical Implementation:**
The `AuditLog` table will include a `previous_hash` and `current_hash` column. A PostgreSQL trigger will be used to ensure that no `UPDATE` or `DELETE` operations are permitted on the `audit_logs` table.

---

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Design

**Description:**
Multiple engineers often need to configure a single device's parameters simultaneously. Harbinger requires a collaborative editing environment where changes are reflected in real-time across all active sessions.

**Functional Requirements:**
1. **Presence Tracking:** Using Phoenix Presence, users should see who else is currently editing a specific device configuration (e.g., "Rafik is editing...").
2. **Real-time Sync:** Changes made by one user must appear instantly on others' screens without a page refresh.
3. **Conflict Resolution:** The system will use a "Last Write Wins" (LWW) strategy for simple fields, but for complex configuration blocks, it will implement Operational Transformation (OT) to merge changes.
4. **Locking Mechanism:** Users can optionally "lock" a section of the configuration to prevent others from editing it while they are making critical changes.

**Technical Implementation:**
This will be implemented using LiveView's `phx-socket` and a pub-sub mechanism. When a user modifies a field, a `broadcast` event is sent to the topic `device:config:<id>`, and other connected clients update their local state via the socket.

---

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
To prevent unauthorized firmware deployments—which could potentially brick thousands of devices—all administrative accounts must be secured with strong multi-factor authentication.

**Functional Requirements:**
1. **TOTP Support:** Support for Time-based One-Time Passwords (TOTP) via apps like Google Authenticator or Authy.
2. **WebAuthn/FIDO2:** Full support for hardware security keys (e.g., YubiKey) for high-privilege accounts.
3. **Recovery Codes:** Upon 2FA setup, the system must generate 10 one-time use recovery codes.
4. **Enforcement:** 2FA is mandatory for all users with `admin` or `manager` roles; it is optional for `viewer` roles.

**Technical Implementation:**
The implementation uses the `otplib` for TOTP generation and the `webauthn` library for hardware key challenges. The user's 2FA secret is encrypted at rest using AES-256.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include an `Authorization: Bearer <token>` header.

### 4.1 Device Management

**GET `/api/v1/devices`**
- **Description:** Retrieve a paginated list of all registered devices.
- **Query Params:** `page` (int), `limit` (int), `status` (string: online/offline).
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "dev_123", "name": "North_Field_Sensor_01", "status": "online", "firmware_version": "2.1.0" },
    { "id": "dev_456", "name": "North_Field_Sensor_02", "status": "offline", "firmware_version": "2.0.9" }
  ],
  "meta": { "total": 1200, "page": 1, "per_page": 50 }
}
```

**PATCH `/api/v1/devices/{id}`**
- **Description:** Update device metadata or configuration.
- **Request Body:** `{ "name": "New Name", "tags": ["Experimental", "Zone-B"] }`
- **Response (200 OK):**
```json
{ "id": "dev_123", "status": "updated", "updated_at": "2024-05-20T10:00:00Z" }
```

### 4.2 Firmware Orchestration

**POST `/api/v1/firmware/deploy`**
- **Description:** Trigger a firmware update to a specific fleet.
- **Request Body:** `{ "fleet_id": "fleet_north", "version_id": "fw_99", "rollout_strategy": "canary" }`
- **Response (202 Accepted):**
```json
{ "job_id": "job_abc123", "status": "queued", "estimated_completion": "2024-05-20T11:00:00Z" }
```

**GET `/api/v1/firmware/status/{job_id}`**
- **Description:** Get the progress of a specific deployment job.
- **Response (200 OK):**
```json
{ "job_id": "job_abc123", "progress": "65%", "success_count": 650, "fail_count": 20, "pending": 330 }
```

### 4.3 Audit and Security

**GET `/api/v1/audit/logs`**
- **Description:** Retrieve security logs (Admin only).
- **Response (200 OK):**
```json
{
  "logs": [
    { "timestamp": "2024-05-20T08:00:00Z", "user": "rafik_s", "action": "FIRMWARE_UPDATE", "target": "dev_123", "hash": "a1b2c3d4..." }
  ]
}
```

**POST `/api/v1/auth/2fa/verify`**
- **Description:** Verify a TOTP or WebAuthn challenge.
- **Request Body:** `{ "code": "123456" }`
- **Response (200 OK):** `{ "authenticated": true, "session_token": "sess_xyz" }`

### 4.4 Data Import/Export

**POST `/api/v1/import/upload`**
- **Description:** Upload a data file for processing.
- **Request Body:** Multipart form-data (file).
- **Response (201 Created):** `{ "import_id": "imp_789", "detected_format": "CSV", "status": "processing" }`

**GET `/api/v1/import/status/{import_id}`**
- **Description:** Check the status of a file import.
- **Response (200 OK):** `{ "import_id": "imp_789", "status": "completed", "rows_imported": 5000, "errors": 0 }`

---

## 5. DATABASE SCHEMA

The system uses a PostgreSQL 15 database. All tables use UUIDs as primary keys.

### 5.1 Table Definitions

1. **`users`**
   - `id` (UUID, PK)
   - `email` (String, Unique)
   - `password_hash` (String)
   - `role` (Enum: admin, manager, viewer)
   - `locale` (String, default: 'en-US')
   - `two_fa_enabled` (Boolean)
   - `two_fa_secret` (String, Encrypted)

2. **`devices`**
   - `id` (UUID, PK)
   - `serial_number` (String, Unique)
   - `name` (String)
   - `status` (Enum: online, offline, maintenance)
   - `current_firmware_id` (UUID, FK -> `firmware_versions`)
   - `last_seen_at` (Timestamp)

3. **`fleets`**
   - `id` (UUID, PK)
   - `name` (String)
   - `description` (Text)
   - `created_at` (Timestamp)

4. **`fleet_devices`** (Join table for M:M relationship)
   - `fleet_id` (UUID, FK -> `fleets`)
   - `device_id` (UUID, FK -> `devices`)

5. **`firmware_versions`**
   - `id` (UUID, PK)
   - `version_string` (String, e.g., "2.1.0")
   - `binary_url` (String)
   - `checksum` (String)
   - `created_by` (UUID, FK -> `users`)
   - `created_at` (Timestamp)

6. **`deployment_jobs`**
   - `id` (UUID, PK)
   - `firmware_id` (UUID, FK -> `firmware_versions`)
   - `fleet_id` (UUID, FK -> `fleets`)
   - `status` (Enum: queued, running, completed, failed)
   - `started_at` (Timestamp)
   - `completed_at` (Timestamp)

7. **`audit_logs`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> `users`)
   - `action` (String)
   - `payload` (JSONB)
   - `previous_hash` (String)
   - `current_hash` (String)
   - `timestamp` (Timestamp)

8. **`import_sessions`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> `users`)
   - `filename` (String)
   - `format` (String)
   - `status` (Enum: uploaded, processing, completed, failed)

9. **`billing_accounts`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> `users`)
   - `stripe_customer_id` (String)
   - `plan_level` (Enum: basic, pro, enterprise)
   - `auto_renew` (Boolean)

10. **`billing_invoices`**
    - `id` (UUID, PK)
    - `account_id` (UUID, FK -> `billing_accounts`)
    - `amount` (Decimal)
    - `paid` (Boolean)
    - `invoice_date` (Timestamp)

### 5.2 Relationships Summary
- `users` has a 1:1 relationship with `billing_accounts`.
- `users` has a 1:M relationship with `firmware_versions` and `audit_logs`.
- `fleets` and `devices` have a M:M relationship via `fleet_devices`.
- `firmware_versions` has a 1:M relationship with `devices` (as the current version).
- `deployment_jobs` links `firmware_versions` and `fleets`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Harbinger employs a three-tier environment strategy to ensure stability before production deployment.

#### 6.1.1 Development (Dev)
- **Purpose:** Daily iteration, feature experimentation.
- **Infrastructure:** Individual developer laptops and a shared `dev.harbinger.stratos.io` instance on Fly.io.
- **Database:** Local PostgreSQL instances; shared dev DB for integration testing.
- **CI/CD:** Triggered on every push to `feature/*` branches.

#### 6.1.2 Staging (Stage)
- **Purpose:** QA testing, stakeholder demos, and final verification.
- **Infrastructure:** `stage.harbinger.stratos.io` mirroring production specs.
- **Database:** A sanitized snapshot of production data (anonymized).
- **CI/CD:** Triggered on merge to `develop` branch. Deployment is automated.

#### 6.1.3 Production (Prod)
- **Purpose:** End-user access (500+ users).
- **Infrastructure:** `app.harbinger.stratos.io` deployed across three Fly.io regions (USA, EU, Asia) to minimize latency.
- **Database:** High-availability PostgreSQL cluster with automated daily backups and point-in-time recovery (PITR).
- **CI/CD:** Triggered on merge to `main`. Uses blue-green deployment.

### 6.2 Infrastructure Specifications
- **Containerization:** All services are Dockerized using the official Elixir image.
- **Load Balancing:** Fly.io manages the ingress and distributes traffic across available app instances.
- **Secret Management:** Secrets (DB passwords, API keys) are stored in Fly.io secrets and injected as environment variables at runtime.
- **Monitoring:** Prometheus and Grafana are used for system metrics; Sentry is used for real-time error tracking and alerting.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and modules (e.g., `FirmwareVersion.calculate_checksum/1`).
- **Tooling:** `ExUnit` is the standard testing framework.
- **Requirement:** All new business logic must have $>80\%$ line coverage.
- **Execution:** Run locally by developers and automatically by GitHub Actions on every commit.

### 7.2 Integration Testing
- **Scope:** Interaction between modules and the database (e.g., verifying that a `deployment_job` correctly updates the `devices` table).
- **Tooling:** `ExUnit` with `Ecto.Sandbox` to ensure database isolation.
- **Approach:** We use "fixtures" to populate the database with a consistent set of test devices and users.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "User logs in $\rightarrow$ Uploads Firmware $\rightarrow$ Deploys to Fleet $\rightarrow$ Verifies Status").
- **Tooling:** `Wallaby` (for LiveView testing) and `Playwright`.
- **Approach:** Tests are run against the Staging environment before any production release.

### 7.4 The Billing Module Debt
**CRITICAL NOTE:** The `Billing` module currently has **zero test coverage**. Due to deadline pressure during the transition from hackathon project to internal tool, the billing logic was deployed without a test suite. This is a known technical debt item. 
- **Immediate Action:** A "Testing Sprint" is scheduled for 2025-06-01 to implement full integration tests for the billing cycle.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor (Executive VP) is rotating out of their role. | High | High | **Accept & Monitor:** Maintain weekly reports to the sponsor's successor to ensure continuity of funding. |
| **R-02** | Competitor "AgriCorp" is building a similar tool and is 2 months ahead. | High | Medium | **External Assessment:** Engage a third-party consultant to perform a gap analysis and identify "killer features" we can implement to leapfrog them. |
| **R-03** | Dysfunctional team dynamics (PM and Lead Engineer are not speaking). | Medium | High | **Management Intervention:** Rafik Stein (EM) to facilitate weekly moderated syncs to ensure technical requirements are aligned. |
| **R-04** | Critical team member on medical leave for 6 weeks. | Certain | Medium | **Resource Reallocation:** Redistribute the workload among the remaining 5 members; delay non-critical features (e.g., Localization). |
| **R-05** | Data corruption during firmware update on remote devices. | Low | Critical | **Safe-Mode Recovery:** Implement a "Golden Image" bootloader on hardware that allows fallback to a stable version if an update fails. |

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with strict dependencies.

### 9.1 Phase 1: Foundation & Security (Jan 2025 - July 2025)
- **Focus:** Hardening the prototype, implementing 2FA, and establishing the audit trail.
- **Dependency:** Security audit completion.
- **Milestone 1:** **Architecture Review Complete** (Target: 2025-07-15).

### 9.2 Phase 2: Scaling & Localization (July 2025 - Sept 2025)
- **Focus:** Rolling out i18n for 12 languages and optimizing the data import engine.
- **Dependency:** Architecture sign-off from Milestone 1.
- **Milestone 2:** **Stakeholder Demo and Sign-off** (Target: 2025-09-15).

### 9.3 Phase 3: Commercial Readiness (Sept 2025 - Nov 2025)
- **Focus:** Finalizing collaborative editing, cleaning up billing technical debt, and onboarding the first external partner.
- **Dependency:** Stakeholder sign-off from Milestone 2.
- **Milestone 3:** **First Paying Customer Onboarded** (Target: 2025-11-15).

---

## 10. MEETING NOTES (EXTRACT)

*Note: These notes are extracted from the `harbinger_running_notes.docx` file (200 pages, unsearchable).*

### Meeting 1: Technical Sync (2024-04-12)
**Attendees:** Rafik, Eben, Luciano, Chandra
**Discussion:** 
- Luciano raised concerns about the `audit_logs` table. He stated that standard Postgres logs are not enough and insisted on a cryptographic chain.
- Chandra suggested using a separate blockchain for logs; Rafik shot this down as "over-engineering" and "unnecessary cost."
- **Decision:** Agreed to implement SHA-256 chaining within the PostgreSQL table.
- **Conflict:** The PM (not present) had previously requested a different logging format. Rafik noted that the PM hasn't responded to emails in two weeks.

### Meeting 2: Feature Prioritization (2024-05-05)
**Attendees:** Rafik, Eben, Chandra
**Discussion:**
- Discussion regarding the "Data Import" feature. Eben argued that auto-detection should be client-side to reduce server load.
- Chandra disagreed, arguing that agricultural files are too large for browser-side processing and must be handled by Elixir/Oban.
- **Decision:** The import logic will be server-side.
- **Status Update:** 2FA is now marked as "Complete."

### Meeting 3: Crisis Management (2024-05-18)
**Attendees:** Rafik, Luciano
**Discussion:**
- Discussion regarding the team member on medical leave. The team is currently missing their primary DevOps specialist for the next 6 weeks.
- Luciano expressed concern that the "Audit Trail" (Critical/Blocker) is now stalled because he is the only one who understands the crypto implementation.
- Rafik suggested that Chandra (the contractor) take over the basic implementation, but Luciano refused, citing security risks.
- **Decision:** Audit Trail is officially marked as **BLOCKED**.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $2,100,000 | Salaries for 5 FTEs + 1 Contractor (Chandra) over 2 years. |
| **Infrastructure** | $350,000 | Fly.io hosting, S3 storage, and DB clustering across 3 regions. |
| **Software & Tools** | $120,000 | Sentry, GitHub Enterprise, Jira, and specialized Ag-Tech simulation software. |
| **External Consulting** | $180,000 | Independent assessment of AgriCorp's competitive advantage. |
| **Contingency** | $250,000 | Emergency fund for hardware replacements or unexpected legal compliance. |

---

## 12. APPENDICES

### Appendix A: Firmware Handshake Protocol
To ensure the "Tamper-Evident" nature of the system extends to the hardware, Harbinger uses a custom handshake:
1. **Challenge:** Server sends a 32-byte random nonce.
2. **Response:** Device signs the nonce with its private key (stored in the hardware secure element) and returns the signature + current firmware hash.
3. **Verification:** Server verifies the signature against the stored public key and ensures the hash matches the expected version in the `firmware_versions` table.

### Appendix B: Data Import Magic-Byte Table
The auto-detection engine uses the following hexadecimal signatures for initial file identification:
- **CSV:** No magic bytes; detected by analyzing the first 10 lines for consistent delimiter counts (`,`, `;`, `\t`).
- **JSON:** Starts with `7B` (`{`) or `5B` (`[`).
- **XML:** Starts with `3C 3F` (`<?`).
- **Binary (Proprietary):** Starts with `53 54 52 41` (`STRA` in ASCII).