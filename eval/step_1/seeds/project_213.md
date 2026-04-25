# PROJECT SPECIFICATION: PROJECT LODESTAR
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Date:** October 26, 2023  
**Classification:** Confidential / Proprietary  
**Owner:** Priya Santos, Engineering Manager  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Lodestar represents a strategic pivot for Crosswind Labs, moving the company into a dedicated automotive embedded systems vertical. The catalyst for this project is a high-value enterprise partnership with a Tier-1 automotive manufacturer (hereafter referred to as "The Client"). The Client has committed to a recurring annual contract value (ACV) of $2,000,000, provided that the Lodestar firmware meets the rigorous safety, security, and performance standards required for modern vehicle telematics and onboard diagnostic systems.

The automotive sector is currently transitioning toward "Software Defined Vehicles" (SDVs), creating a massive market gap for firmware that can bridge the gap between low-level hardware abstraction and high-level cloud orchestration. Lodestar is designed to fill this gap, providing a robust, Rust-based firmware layer that ensures memory safety and high concurrency, paired with a modern React-based management interface for fleet operators.

### 1.2 ROI Projection and Financial Goals
With a total investment budget of $3,000,000, the financial trajectory for Lodestar is aggressive but sustainable. The immediate ROI is driven by the $2M annual payment from the anchor client. However, the long-term objective is to productize this firmware as a white-label solution for other automotive OEMs.

**Financial Metrics:**
- **Year 1 Revenue:** $2M (Anchor Client) + $500K (Targeted New Revenue from Pilot Programs) = $2.5M.
- **Break-even Point:** Approximately 14 months post-launch.
- **Projected 3-Year NPV:** $4.2M, assuming a 20% growth in the automotive client base.

### 1.3 Strategic Objectives
The primary objective is the delivery of a production-ready firmware suite by June 15, 2025. Success is not merely technical stability, but market penetration. The project aims to achieve a Net Promoter Score (NPS) of >40 within the first quarter of deployment, signaling that the product is not just functional, but a joy for automotive engineers to implement.

### 1.4 Scope Overview
Lodestar encompasses the development of the embedded Rust core, a lightweight SQLite edge database for telemetry caching, a serverless backend orchestration layer via Cloudflare Workers, and a React-based dashboard. The system must be FedRAMP authorized to ensure eligibility for government-contracted automotive fleets (e.g., Department of Defense logistics).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level System Design
Lodestar utilizes a hybrid edge-cloud architecture. The "Edge" consists of the automotive hardware running the Rust firmware, while the "Cloud" consists of a globally distributed serverless mesh.

**The Technical Stack:**
- **Firmware/Backend:** Rust (Edition 2021) for memory safety and zero-cost abstractions.
- **Frontend:** React 18+ with TypeScript and Tailwind CSS.
- **Edge Storage:** SQLite (via `rusqlite`) for high-performance local data persistence.
- **Cloud Infrastructure:** Cloudflare Workers (Serverless) and API Gateway.
- **Configuration/Rollout:** LaunchDarkly for feature flagging and canary deployments.

### 2.2 Architectural Diagram (ASCII Description)
```text
[ VEHICLE HARDWARE ] <--- SPI/I2C/CAN Bus ---> [ LODESTAR FIRMWARE (Rust) ]
                                                           |
                                                           v
                                              [ LOCAL STORAGE (SQLite Edge) ]
                                                           |
                                                           | (Encrypted HTTPS/gRPC)
                                                           v
[ CLOUDFLARE WORKERS ] <--- [ API GATEWAY ] <--- [ AUTH LAYER (FedRAMP Compliant) ]
         |                                           |
         v                                           v
[ GLOBAL STATE STORE ] <-------------------- [ REACT MANAGEMENT DASHBOARD ]
         |                                           |
         +------> [ LAUNCHDARKLY (Feature Flags) ] <---+
```

### 2.3 Infrastructure Logic
The system leverages serverless functions to avoid the overhead of maintaining persistent server clusters. All API requests are routed through an API Gateway that handles rate limiting and authentication. To maintain high availability during updates, Lodestar employs a "Canary Release" strategy where new firmware versions are pushed to 1% of the fleet, monitored for 24 hours, and then scaled linearly.

### 2.4 Security and Compliance
Because Lodestar targets government clients, FedRAMP authorization is non-negotiable. This requires:
1. **FIPS 140-2 Validated Encryption:** All data at rest in SQLite and in transit must use validated cryptographic modules.
2. **Strict IAM:** Role-based access control (RBAC) implemented at the API Gateway level.
3. **Audit Logging:** Every state change in the firmware must be logged to an immutable ledger in the cloud.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Design
**Description:**
Automotive environments are characterized by intermittent connectivity (tunnels, rural areas). The firmware must operate fully without a network connection, caching all telemetry, diagnostic logs, and user configurations locally.

**Functional Requirements:**
- **Local Persistence:** All incoming CAN bus data must be written to the SQLite edge database immediately.
- **Queue Management:** A "Pending Sync" table must track records that have not yet been acknowledged by the cloud backend.
- **Exponential Backoff:** The sync engine must attempt reconnection every 30 seconds, 1 minute, 5 minutes, and 15 minutes to prevent battery drain and network congestion.
- **Conflict Resolution:** In the event of a configuration change occurring both on the device and the dashboard, the "Last Write Wins" (LWW) strategy will be applied, using high-precision timestamps (nanoseconds).
- **Delta Compression:** To minimize data costs, the system will only sync the "diff" between the last successful sync and the current state.

**Technical Constraints:**
- Local storage must not exceed 2GB to prevent disk overflow on the embedded module.
- Sync processes must run in a low-priority Rust thread to ensure that primary vehicle functions (diagnostics) are never blocked.

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:**
The system must allow engineers to import historical vehicle data from various formats (JSON, CSV, XML, and proprietary binary formats from legacy OEMs) and export current state data for regulatory audits.

**Functional Requirements:**
- **Auto-Detection Engine:** The system will read the first 1KB of any uploaded file to identify magic bytes and structural patterns (e.g., `{` for JSON, `,` for CSV).
- **Schema Mapping:** A visual mapping tool in the React frontend allows users to map imported columns to Lodestar's internal SQLite schema.
- **Validation Pipeline:** Imported data must pass through a validation layer that checks for "out-of-bounds" automotive values (e.g., engine temperature cannot be -500°C).
- **Export Formats:** Support for `.csv`, `.parquet` (for big data analysis), and `.pdf` (for compliance reports).

**Blocker Details:**
This feature is currently blocked by the "Data Schema Definition" deliverable from the External Standards Team, which is 3 weeks overdue. Without the final specification of the OEM data format, the auto-detection logic cannot be finalized.

### 3.3 A/B Testing Framework (Integrated with Feature Flags)
**Priority:** Medium | **Status:** Complete
**Description:**
To optimize firmware performance and UX, the team has implemented a framework that allows different segments of the vehicle fleet to run different logic paths based on LaunchDarkly flags.

**Functional Requirements:**
- **Cohort Assignment:** Vehicles are assigned to Cohort A or B based on a hash of their VIN (Vehicle Identification Number).
- **Dynamic Switching:** The firmware can switch logic paths (e.g., different telemetry sampling rates) in real-time without a full reboot.
- **Metric Tracking:** The system automatically tags all telemetry data with the active feature flag version, allowing the backend to correlate performance with specific versions.
- **Safety Kill-Switch:** If a canary release shows an increase in "Critical Error" logs, LaunchDarkly will automatically flip the flag back to the stable version across the entire fleet.

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low (Nice to Have) | **Status:** In Design
**Description:**
A high-level tool allowing fleet managers to create "If-This-Then-That" (IFTTT) style rules for vehicle behavior.

**Functional Requirements:**
- **Visual Builder:** A React-based drag-and-drop interface where users can define triggers (e.g., "Engine Temp > 100°C") and actions (e.g., "Send SMS to Fleet Manager").
- **Rule Compilation:** Rules are compiled into a JSON logic tree and pushed to the device via the API Gateway.
- **Local Execution:** The Rust firmware interprets these rules locally to ensure that safety-critical automations do not depend on cloud connectivity.
- **Condition Nesting:** Support for complex logic including AND/OR gates and nested conditions.

### 3.5 Notification System (Email, SMS, In-App, Push)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started
**Description:**
A multi-channel alert system to notify operators of critical vehicle failures, security breaches, or maintenance requirements.

**Functional Requirements:**
- **Priority Routing:** 
    - *Critical:* Push Notification + SMS (Immediate).
    - *Warning:* In-App Notification + Email (Within 1 hour).
    - *Information:* In-App Notification (Next login).
- **Template Engine:** A system to manage localized templates for different languages and regions.
- **Notification Aggregation:** To avoid "alert fatigue," multiple similar warnings from a single vehicle will be bundled into a single summary notification.
- **Audit Trail:** A record of when a notification was sent and when it was acknowledged by the operator.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted via Cloudflare Workers. Base URL: `https://api.lodestar.crosswind.io/v1/`

### 4.1 `GET /telemetry/latest`
- **Description:** Fetches the most recent telemetry data for a specific vehicle.
- **Request:** `?vin={vehicle_vin}`
- **Response:**
  ```json
  {
    "vin": "1HGCM82...",
    "timestamp": "2023-10-26T14:00:00Z",
    "metrics": {
      "fuel_level": 64.2,
      "oil_pressure": 42.1,
      "engine_temp": 92.5
    },
    "status": "online"
  }
  ```

### 4.2 `POST /sync/upload`
- **Description:** Endpoint for firmware to push queued SQLite data.
- **Request Body:**
  ```json
  {
    "vin": "1HGCM82...",
    "batch_id": "batch_9921",
    "payload": [
      {"ts": 1698321600, "code": "P0301", "val": 12},
      {"ts": 1698321660, "code": "P0301", "val": 14}
    ]
  }
  ```
- **Response:** `202 Accepted` with `{"sync_id": "sync_abc123"}`.

### 4.3 `PATCH /config/update`
- **Description:** Updates the configuration flags for a specific vehicle.
- **Request Body:**
  ```json
  {
    "vin": "1HGCM82...",
    "settings": {
      "sampling_rate": "500ms",
      "logging_level": "DEBUG"
    }
  }
  ```
- **Response:** `200 OK` with updated config object.

### 4.4 `GET /fleet/status`
- **Description:** Returns an overview of all connected vehicles.
- **Response:**
  ```json
  {
    "total_vehicles": 1250,
    "online": 1100,
    "offline": 150,
    "alerts_active": 12
  }
  ```

### 4.5 `POST /notifications/send`
- **Description:** Manually trigger a notification to a user/manager.
- **Request Body:**
  ```json
  {
    "user_id": "user_882",
    "channel": "sms",
    "message": "Vehicle VIN... is overheating!",
    "priority": "critical"
  }
  ```
- **Response:** `201 Created`.

### 4.6 `GET /auth/session`
- **Description:** Validates the current session token for FedRAMP compliance.
- **Request Header:** `Authorization: Bearer <token>`
- **Response:** `{"status": "valid", "expires": "2023-10-26T18:00:00Z"}`.

### 4.7 `GET /diagnostics/logs`
- **Description:** Retrieves raw system logs from the edge device.
- **Request:** `?vin={vin}&level=ERROR`
- **Response:** Array of log objects including timestamp, severity, and message.

### 4.8 `DELETE /fleet/vehicle/{vin}`
- **Description:** Decommissions a vehicle from the fleet management system.
- **Response:** `204 No Content`.

---

## 5. DATABASE SCHEMA

The Lodestar system utilizes two database layers: an Edge SQLite instance for local storage and a Cloud Distributed DB for global state.

### 5.1 Edge Database (SQLite)
| Table | Purpose | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `telemetry_cache` | Buffer for unsynced data | `id (PK)`, `timestamp`, `metric_id`, `value` | Many-to-One `metric_defs` |
| `metric_defs` | Definition of CAN bus codes | `metric_id (PK)`, `label`, `unit` | One-to-Many `telemetry_cache` |
| `sync_log` | Tracks sync attempts | `sync_id (PK)`, `start_time`, `end_time`, `status` | N/A |
| `local_config` | Current device settings | `key (PK)`, `value`, `last_updated` | N/A |
| `event_log` | System errors and warnings | `event_id (PK)`, `severity`, `msg`, `ts` | N/A |

### 5.2 Cloud Database (Distributed)
| Table | Purpose | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `vehicles` | Global fleet registry | `vin (PK)`, `model`, `firmware_version`, `owner_id` | One-to-Many `telemetry_history` |
| `users` | Operator accounts | `user_id (PK)`, `email`, `role`, `auth_token` | One-to-Many `vehicles` |
| `telemetry_history`| Aggregated long-term data | `hist_id (PK)`, `vin (FK)`, `timestamp`, `value` | Many-to-One `vehicles` |
| `notifications` | Audit trail of alerts | `note_id (PK)`, `user_id (FK)`, `timestamp`, `channel` | Many-to-One `users` |
| `feature_flags` | Mirror of LaunchDarkly state | `flag_key (PK)`, `enabled`, `cohort_rules` | N/A |

### 5.3 Relationship Logic
The `vehicles` table acts as the central hub. All telemetry, notifications, and configuration changes are linked via the `vin` (Vehicle Identification Number), which serves as the unique immutable identifier across both edge and cloud layers.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lodestar maintains three distinct environments to ensure stability and compliance.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and unit testing.
- **Infrastructure:** Local Docker containers and Cloudflare Workers (Dev namespace).
- **Data:** Mocked vehicle data.
- **Deployment:** Automatic push on every commit to `develop` branch.

**2. Staging (Stage):**
- **Purpose:** Integration testing and Stakeholder demos.
- **Infrastructure:** Mirror of Production; connected to a limited set of "Test Bench" hardware.
- **Data:** Sanitized production data.
- **Deployment:** Manual trigger from `release` branch.

**3. Production (Prod):**
- **Purpose:** Live vehicle fleet.
- **Infrastructure:** FedRAMP authorized Cloudflare Workers environment.
- **Data:** Real-time encrypted vehicle data.
- **Deployment:** Canary release via LaunchDarkly.

### 6.2 Canary Release Process
1. **Deployment:** New firmware is pushed to the "Stable" bucket.
2. **Activation:** The `lodestar_version_v2` flag is enabled for 1% of VINs.
3. **Observation:** Monitoring for "Kernel Panic" or "SQLite Corruption" logs for 24 hours.
4. **Scaling:** Increment to 10% $\rightarrow$ 25% $\rightarrow$ 50% $\rightarrow$ 100%.
5. **Rollback:** Instant disable of the flag in LaunchDarkly reverts all vehicles to v1 logic.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (Rust & React)
- **Rust:** Use `cargo test` for every module. We emphasize "property-based testing" for the sync engine to ensure that no matter the network failure pattern, data integrity is maintained.
- **React:** Jest and React Testing Library for component-level validation, focusing on the visual rule builder's state management.

### 7.2 Integration Testing
- **Hardware-in-the-Loop (HIL):** Using simulated CAN bus generators to feed the Rust firmware real-world failure scenarios.
- **API Contract Testing:** Using Prism to ensure the React frontend and Cloudflare Workers adhere to the documented API specifications.

### 7.3 End-to-End (E2E) Testing
- **Scenario Testing:** "Vehicle enters tunnel $\rightarrow$ generates 50 errors $\rightarrow$ exits tunnel $\rightarrow$ verifies cloud dashboard reflects all 50 errors."
- **Tooling:** Playwright for frontend E2E and custom Python scripts for firmware-to-cloud verification.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | High | Negotiate timeline extension now; diversify stakeholder buy-in across other VP levels. |
| R-02 | Budget cut of 30% in next fiscal Q | Medium | High | Document "lean" workarounds; prioritize critical features (1, 2, 5) and deprioritize the automation engine. |
| R-03 | Dependency on External Team (3 wks behind) | High | Medium | Establish daily sync with the external lead; develop a "mock" data format to unblock development. |
| R-04 | Technical Debt (Raw SQL in 30% of queries) | Medium | High | Schedule "Refactor Sprints" every 4 weeks to move raw SQL into the ORM. |
| R-05 | FedRAMP Certification Delay | Low | High | Engage a 3rd party compliance consultant early to perform gap analysis. |

**Impact Matrix:**
- **Probability:** Low (1-33%), Medium (34-66%), High (67-100%).
- **Impact:** Low (Minor delay), Medium (Feature drop), High (Project failure/Budget collapse).

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation & Core Logic (Now - Feb 2024)
- **Focus:** Rust core architecture and SQLite schema finalization.
- **Dependencies:** Internal hardware specs.
- **Deliverable:** Working prototype of local data caching.

### 9.2 Phase 2: Connectivity & Cloud Integration (Mar 2024 - Dec 2024)
- **Focus:** Cloudflare Workers implementation, API Gateway, and Sync Engine.
- **Dependencies:** External team's data format (Current Blocker).
- **Deliverable:** Beta version of the "Sync" functionality.

### 9.3 Phase 3: Frontend & User Experience (Jan 2025 - May 2025)
- **Focus:** React Dashboard, Visual Rule Builder, and Notification System.
- **Dependencies:** Finalized API endpoints.
- **Deliverable:** Full-stack integration.

### 9.4 Phase 4: Validation & Launch (June 2025 - Oct 2025)
- **Milestone 1 (2025-06-15):** Production Launch.
- **Milestone 2 (2025-08-15):** Stakeholder demo and sign-off.
- **Milestone 3 (2025-10-15):** Performance benchmarks (Latency < 200ms, Sync success > 99.9%).

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per team policy, formal minutes are not kept. Decisions are captured in Slack threads.*

### Meeting 1: Architecture Alignment (Thread: #lodestar-tech-sync)
- **Participants:** Priya, Fleur, Ilya.
- **Discussion:** Debate between using a hosted Postgres instance vs. Cloudflare Workers with a distributed KV store. 
- **Decision:** Fleur argued that the latency for automotive telemetry needs global distribution. Decision: Use Cloudflare Workers for the API layer and a distributed state store to ensure minimal latency for vehicles globally.
- **Action:** Fleur to set up the initial Worker environment.

### Meeting 2: The "Raw SQL" Crisis (Thread: #lodestar-dev-debt)
- **Participants:** Priya, Fleur.
- **Discussion:** Fleur noted that the ORM is slowing down the telemetry ingestion pipeline. 30% of queries are now raw SQL to meet performance targets.
- **Decision:** Priya acknowledged the technical debt. Decision: We will allow raw SQL for the `telemetry_cache` table for now but forbid it for the `users` and `vehicles` tables to prevent migration disasters.
- **Action:** Document all raw SQL queries in a `DEBT.md` file.

### Meeting 3: External Blocker Escalation (Thread: #lodestar-mgmt)
- **Participants:** Priya, Dina.
- **Discussion:** Dina reported the External Standards team is 3 weeks late on the data format spec. Feature 2 (Import/Export) is completely stalled.
- **Decision:** Priya will escalate to the Client's project manager to pressure the external team. In the meantime, the team will implement a "Generic JSON" importer as a temporary workaround.
- **Action:** Priya to send a formal email to the Client today.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $2,100,000 | Salaries for 8 team members over 2 years (including benefits). |
| **Infrastructure** | 15% | $450,000 | Cloudflare Workers, LaunchDarkly Enterprise, FedRAMP audit costs. |
| **Tools & Hardware** | 10% | $300,000 | Embedded test boards, CAN bus analyzers, MacBook Pros. |
| **Contingency** | 5% | $150,000 | Reserve for emergency pivots or budget cuts. |

**Note on Budget Risks:** If the 30% budget cut (R-02) occurs, the "Contingency" and "Tools" budget will be exhausted first, and the project will transition to a "Critical Only" feature set, eliminating Feature 4 (Workflow Automation).

---

## 12. APPENDICES

### Appendix A: Rust Memory Management Strategy
To ensure the firmware does not crash in a vehicle, we employ a strict `no_std` or limited-std approach for the core driver loop. We use `Arc` (Atomic Reference Counting) and `Mutex` for shared state between the CAN bus listener and the SQLite writer. To prevent memory leaks, all long-running tasks are wrapped in a watchdog timer that re-initializes the module if a heartbeat is missed for more than 500ms.

### Appendix B: FedRAMP Compliance Matrix
The following controls are being implemented to meet the "Low-Impact" FedRAMP baseline:
- **AC-2 (Account Management):** Integration with Okta for centralized identity management.
- **SC-8 (Transmission Confidentiality):** All API calls use TLS 1.3 with mandatory certificate pinning.
- **AU-2 (Event Logging):** All administrative actions in the React dashboard are logged to an immutable Cloudflare Logpush bucket.
- **IA-2 (Identification and Authentication):** Multi-factor authentication (MFA) required for all users with "Admin" or "Fleet Manager" roles.