# PROJECT SPECIFICATION: PROJECT HALCYON
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Classification:** Confidential – Tundra Analytics Internal  
**Date:** October 24, 2025  
**Project Lead:** Wanda Jensen (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

Project Halcyon represents a strategic pivot for Tundra Analytics, marking the company’s formal entry into the Food and Beverage (F&B) industrial embedded systems market. The project is conceived not as a general market product, but as a bespoke, high-reliability firmware and software ecosystem driven by a single, high-value enterprise client. This client has committed to a recurring annual contract value (ACV) of $2,000,000, providing a massive ROI relative to the initial development investment.

### Business Justification
The F&B industry currently relies on legacy telemetry systems that are plagued by high latency and exorbitant transactional costs. The enterprise client requires a modernized, edge-computing solution capable of processing sensory data in real-time while maintaining strict compliance with health and safety regulations. By leveraging a Rust-based firmware stack, Halcyon aims to eliminate the memory-safety vulnerabilities common in C/C++ legacy systems, thereby reducing downtime and maintenance costs.

### ROI Projection
The financial model for Halcyon is aggressive. With a lean development budget of $150,000 and a projected annual revenue of $2,000,000, the project achieves a break-even point within the first quarter of full deployment. 

**Key Financial Metrics:**
*   **Initial Investment:** $150,000 (Shoestring Budget).
*   **Annual Revenue:** $2,000,000.
*   **Projected ROI (Year 1):** 1,233%.
*   **Cost Efficiency:** The primary success metric is a 35% reduction in cost per transaction compared to the client's current legacy infrastructure.

### Strategic Objective
The goal is to deliver a "Modular Monolith" that provides immediate stability for the client while allowing Tundra Analytics to incrementally transition toward a microservices architecture as the product vertical expands to other clients. The system must be HIPAA compliant—despite being an F&B project—because the client’s facility integrates health-monitoring wearables for staff, requiring the highest tier of data encryption at rest and in transit.

---

## 2. TECHNICAL ARCHITECTURE

Halcyon utilizes a hybrid edge-cloud architecture. The firmware resides on embedded hardware, managing local data ingestion and storage, while a cloud-based orchestration layer handles reporting and administration.

### Technology Stack
*   **Firmware/Backend:** Rust (utilizing `tokio` for async runtime and `serde` for serialization). Rust was chosen specifically for its memory safety and performance, critical for the "zero critical security incidents" mandate.
*   **Frontend:** React 18.2 (TypeScript) with Tailwind CSS for the administrative dashboard.
*   **Edge Storage:** SQLite 3.45.0, acting as the local buffer for offline-first capabilities.
*   **Cloud Infrastructure:** Cloudflare Workers (Serverless) providing the API gateway and compute layer.
*   **Communication:** Protobuf over TLS 1.3 for device-to-cloud communication to minimize payload size.

### Architecture Diagram (ASCII Representation)

```text
[ Embedded Hardware (Edge) ]               [ Cloud Layer (Cloudflare) ]
+---------------------------+             +----------------------------+
|  Sensors -> Rust Firmware  |             |   Cloudflare Worker (API)   |
|             |              |             |            |               |
|  +----------v----------+   |             |  +---------v----------+    |
|  | Local SQLite Storage |   | <---TLS---> |  | Authentication     |    |
|  +----------^----------+   |             |  +---------^----------+    |
|             |              |             |            |               |
|  +----------v----------+   |             |  +---------v----------+    |
|  | Background Sync Mgr  |   |             |  | Global State Store  |    |
|  +----------------------+   |             |  +--------------------+    |
+---------------------------+             +----------------------------+
            ^                                            ^
            |                                            |
    [ Local Admin UI ] <------------------------> [ Web Dashboard (React) ]
```

### Architectural Transition Path
The project begins as a **Modular Monolith**. All business logic resides in a single Rust binary to simplify deployment and debugging for the small 4-person team. As the system scales, the "Report Generation" and "Automation Engine" modules will be extracted into standalone Cloudflare Workers (Microservices) to prevent a single point of failure and allow independent scaling.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation & Scheduled Delivery
**Priority:** High | **Status:** In Progress

This feature is the primary value-driver for the enterprise client's executive team. The system must aggregate raw sensor data from the edge, process it into KPIs (Key Performance Indicators), and generate immutable reports.

*   **Functional Requirements:**
    *   The system must support the generation of PDF (via `headless-chrome` or `weasyprint` wrappers) and CSV files.
    *   Reports must include: Device ID, Timestamp, Variance from Baseline, and Compliance Status.
    *   **Scheduling Engine:** A cron-based trigger within the Cloudflare Workers environment that executes on a daily, weekly, or monthly cadence.
    *   **Delivery:** Integration with SendGrid API for email delivery and an S3-compatible bucket for archival.
*   **Technical Implementation:**
    *   Reports are generated asynchronously. A request is placed in a queue; a worker processes the SQLite data from the edge (via the sync layer), generates the file, and uploads it to a secure bucket.
    *   Encryption: Files must be encrypted using AES-256 before being stored in the archival bucket to maintain HIPAA compliance.
*   **User Interface:** A "Report Builder" screen in React where users can toggle specific metrics and define the recipient email list.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** In Design

To ensure system stability and prevent Denial-of-Service (DoS) scenarios—whether accidental or malicious—a robust rate-limiting layer is required.

*   **Functional Requirements:**
    *   **Tiered Limiting:** Define limits based on user roles (e.g., Admin: 10,000 req/hr, Viewer: 1,000 req/hr).
    *   **Sliding Window Algorithm:** Implementation of a sliding window counter to prevent "bursting" at the turn of the hour.
    *   **Analytics Dashboard:** A view for Tundra Analytics to monitor total API calls, 429 (Too Many Requests) error rates, and peak usage times.
*   **Technical Implementation:**
    *   Use Cloudflare Workers KV (Key-Value store) to track request counts per API key with a TTL (Time to Live) of 3600 seconds.
    *   Middleware in the Rust backend will intercept incoming requests and validate the current count against the KV store before proceeding to the business logic.
*   **Metric Collection:** Every request will log a metadata packet (timestamp, endpoint, response time, user_id) to an analytics table in the database for long-term trend analysis.

### 3.3 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** In Review

Given the industrial nature of F&B plants, Wi-Fi dead zones are common. The system must remain functional without a cloud connection.

*   **Functional Requirements:**
    *   **Local Persistence:** All data generated by the firmware must be written to the local SQLite database first.
    *   **Sync Queue:** A "Pending Upload" queue that tracks records not yet acknowledged by the cloud.
    *   **Conflict Resolution:** A "Last-Write-Wins" (LWW) strategy for configuration changes, but an "Append-Only" strategy for telemetry data to ensure no data loss.
*   **Technical Implementation:**
    *   The Rust firmware will implement a `SyncManager` thread. This thread polls for network connectivity every 30 seconds.
    *   Upon reconnection, the manager will batch-upload pending records using a compressed Protobuf stream to minimize bandwidth.
    *   **Exponential Backoff:** If the cloud returns a 5xx error, the sync manager will wait $2^n$ seconds before retrying.

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** Not Started

While the client currently has a small user base, the system must be architected for multi-tenant security.

*   **Functional Requirements:**
    *   **Authentication:** JWT (JSON Web Tokens) issued via an OAuth2 flow.
    *   **Roles:** Three primary roles: `SuperAdmin` (Full access), `Operator` (Read/Write data, no config), `Auditor` (Read-only reports).
    *   **Session Management:** Secure, HTTP-only cookies to prevent XSS-based token theft.
*   **Technical Implementation:**
    *   Password hashing using `Argon2id` within the Rust backend.
    *   A middleware layer that checks the `role` claim within the JWT against the required permission for the requested endpoint.
    *   Integration with the HIPAA compliance requirement by logging every "Access" event to an immutable audit log.

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low | **Status:** Blocked

This feature allows users to create "If-This-Then-That" (IFTTT) style triggers (e.g., "If Temperature > 40°F for 10 mins, Send Alert to Manager").

*   **Functional Requirements:**
    *   **Visual Builder:** A drag-and-drop interface in React to define trigger conditions and actions.
    *   **Rule Evaluation:** A lightweight engine in the Rust firmware that evaluates rules locally to ensure immediate action without cloud round-trips.
    *   **Action Library:** Pre-defined actions including `EmailAlert`, `LogEvent`, and `TriggerRelay`.
*   **Blocker:** This feature is currently blocked pending budget approval for a specialized logic-graphing library license.
*   **Technical Implementation:**
    *   Rules will be stored as JSON logic trees in the SQLite database.
    *   The firmware will use a "Visitor Pattern" to traverse the logic tree and evaluate the current sensor state against the defined thresholds.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted on `api.halcyon.tundra.io`. All requests must include a `Authorization: Bearer <JWT>` header.

### 4.1 GET `/v1/telemetry/latest`
**Description:** Retrieves the most recent sensor reading from the device.
*   **Request:** `GET /v1/telemetry/latest?device_id=DEV-102`
*   **Response (200 OK):**
    ```json
    {
      "timestamp": "2026-05-15T10:00:00Z",
      "device_id": "DEV-102",
      "readings": { "temp": 34.2, "humidity": 45.1 },
      "status": "nominal"
    }
    ```

### 4.2 POST `/v1/reports/generate`
**Description:** Manually triggers a report generation.
*   **Request Body:**
    ```json
    {
      "report_type": "compliance_summary",
      "start_date": "2026-05-01",
      "end_date": "2026-05-15",
      "format": "pdf"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    { "job_id": "job_88234", "status": "queued", "estimated_time": "45s" }
    ```

### 4.3 GET `/v1/reports/download/{job_id}`
**Description:** Downloads a completed report.
*   **Request:** `GET /v1/reports/download/job_88234`
*   **Response:** Binary stream (PDF/CSV) with `Content-Type: application/pdf`.

### 4.4 POST `/v1/device/config`
**Description:** Updates the firmware configuration on a specific device.
*   **Request Body:**
    ```json
    {
      "device_id": "DEV-102",
      "sampling_rate": 60,
      "alert_threshold": 42.0
    }
    ```
*   **Response (200 OK):** `{ "status": "success", "applied_at": "2026-05-15T10:05:00Z" }`

### 4.5 GET `/v1/analytics/usage`
**Description:** Returns API usage statistics for the billing period.
*   **Request:** `GET /v1/analytics/usage?month=May&year=2026`
*   **Response (200 OK):**
    ```json
    {
      "total_requests": 154000,
      "rate_limit_hits": 12,
      "avg_latency_ms": 42
    }
    ```

### 4.6 PUT `/v1/user/profile`
**Description:** Updates the authenticated user's profile settings.
*   **Request Body:** `{ "email": "m.liu@client.com", "timezone": "EST" }`
*   **Response (200 OK):** `{ "status": "updated" }`

### 4.7 GET `/v1/system/health`
**Description:** Check health of the cloud gateway and connected edge devices.
*   **Request:** `GET /v1/system/health`
*   **Response (200 OK):**
    ```json
    {
      "cloud_status": "healthy",
      "connected_devices": 142,
      "sync_lag_avg": "1.2s"
    }
    ```

### 4.8 DELETE `/v1/device/{device_id}`
**Description:** Decommissions a device and wipes its cloud-side data.
*   **Request:** `DELETE /v1/device/DEV-102`
*   **Response (204 No Content):** `Empty`

---

## 5. DATABASE SCHEMA

The system uses a distributed database approach: SQLite at the edge for speed/offline capability, and a relational store (PostgreSQL via Cloudflare Hyperdrive) in the cloud.

### Table Definitions

1.  **`devices`**: Stores hardware metadata.
    *   `device_id` (UUID, PK), `model_version` (String), `firmware_version` (String), `installation_date` (Date), `status` (Enum: Active, Inactive, Fault).
2.  **`telemetry_logs`**: High-volume sensor data.
    *   `log_id` (BigInt, PK), `device_id` (FK), `timestamp` (DateTime), `reading_value` (Float), `sensor_type` (String).
3.  **`users`**: User account information.
    *   `user_id` (UUID, PK), `username` (String), `password_hash` (String), `email` (String), `role_id` (FK).
4.  **`roles`**: RBAC role definitions.
    *   `role_id` (Int, PK), `role_name` (String), `permissions` (JSONB).
5.  **`report_jobs`**: Tracking for the report generation engine.
    *   `job_id` (UUID, PK), `user_id` (FK), `report_type` (String), `status` (Enum: Pending, Processing, Completed, Failed), `created_at` (DateTime).
6.  **`report_schedules`**: Cron-like settings for automated reports.
    *   `schedule_id` (UUID, PK), `user_id` (FK), `frequency` (String), `delivery_email` (String), `last_run` (DateTime).
7.  **`api_usage_logs`**: Audit trail for rate limiting.
    *   `request_id` (UUID, PK), `user_id` (FK), `endpoint` (String), `timestamp` (DateTime), `response_code` (Int).
8.  **`sync_queue`**: Edge-side tracking of unsynced data.
    *   `queue_id` (Int, PK), `payload` (Blob), `attempts` (Int), `created_at` (DateTime).
9.  **`automation_rules`**: Definitions for the rule builder.
    *   `rule_id` (UUID, PK), `device_id` (FK), `logic_json` (Text), `is_active` (Boolean).
10. **`audit_trail`**: HIPAA-mandated access logs.
    *   `audit_id` (BigInt, PK), `user_id` (FK), `action` (String), `resource_id` (String), `timestamp` (DateTime), `ip_address` (String).

### Relationships
*   `users` $\rightarrow$ `roles` (Many-to-One)
*   `telemetry_logs` $\rightarrow$ `devices` (Many-to-One)
*   `report_jobs` $\rightarrow$ `users` (Many-to-One)
*   `automation_rules` $\rightarrow$ `devices` (Many-to-One)
*   `api_usage_logs` $\rightarrow$ `users` (Many-to-One)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### Environment Strategy
Halcyon utilizes three distinct environments to ensure the "zero critical security incidents" goal.

1.  **Development (Dev):**
    *   **Purpose:** Rapid iteration and feature development.
    *   **Infrastructure:** Local Docker containers for Rust backend and React frontend.
    *   **Data:** Mock data generated by scripts.
    *   **Deployment:** Automatic on commit to `develop` branch.

2.  **Staging (Stage):**
    *   **Purpose:** Pre-production validation and QA.
    *   **Infrastructure:** Cloudflare Workers (Staging namespace), mirrored SQLite environment on test hardware.
    *   **Data:** Anonymized subset of real client data.
    *   **Deployment:** Manual trigger by Wanda Jensen after PR approval.

3.  **Production (Prod):**
    *   **Purpose:** Live client environment.
    *   **Infrastructure:** Cloudflare Workers (Production), hardened embedded hardware.
    *   **Data:** Fully encrypted HIPAA-compliant production data.
    *   **Deployment:** Subject to a **manual QA gate** by Lev Oduya. Turnaround is strictly 2 days from Stage approval to Prod deployment.

### Deployment Pipeline
`Git Push` $\rightarrow$ `CI Pipeline (Tests)` $\rightarrow$ `Dev Deploy` $\rightarrow$ `QA Review` $\rightarrow$ `Staging Deploy` $\rightarrow$ `Lev Oduya Approval` $\rightarrow$ `Prod Deploy`.

---

## 7. TESTING STRATEGY

Testing is divided into three tiers to ensure the stability of the firmware and the reliability of the cloud.

### 7.1 Unit Testing
*   **Rust:** Extensive use of `#[cfg(test)]` modules. Every business logic function (e.g., rate limiting math, Protobuf serialization) must have $\ge 90\%$ coverage.
*   **React:** Vitest for component-level testing, ensuring that the "Report Builder" handles various date ranges without crashing.
*   **Tooling:** `cargo test` and `npm test`.

### 7.2 Integration Testing
*   **Edge-to-Cloud:** Simulated network failure tests to verify that the `SyncManager` correctly queues data in SQLite and flushes it upon reconnection.
*   **Database:** Testing the interaction between the Cloudflare Worker and the PostgreSQL store to ensure that complex joins for reports execute within the 500ms timeout limit.
*   **Tooling:** Postman for API collection testing.

### 7.3 End-to-End (E2E) Testing
*   **Scenario-Based:** A full "Day in the Life" test: Sensor triggers $\rightarrow$ Data logged to SQLite $\rightarrow$ Synced to Cloud $\rightarrow$ Report generated $\rightarrow$ Email delivered.
*   **Security Audits:** Quarterly penetration tests focusing on the JWT implementation and HIPAA encryption standards.
*   **Tooling:** Playwright for frontend E2E flows.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding "small" features. | High | Medium | Accept the risk; monitor weekly in sprint reviews. |
| **R2** | Team lacks experience with Rust/Cloudflare Workers. | High | High | Document workarounds; internal knowledge-sharing sessions. |
| **R3** | Budget overrun due to shoestring $150k limit. | Medium | High | Every single expenditure is scrutinized by Wanda Jensen. |
| **R4** | Hardware failure in harsh F&B environment. | Medium | Medium | Use industrial-grade SQLite journaling for data integrity. |
| **R5** | HIPAA compliance breach. | Low | Critical | Mandatory encryption at rest/transit; strict audit logs. |

**Probability/Impact Matrix:**
*   *Critical:* Immediate project failure or legal action.
*   *High:* Significant delay or budget breach.
*   *Medium:* Manageable delay or minor feature cut.
*   *Low:* Negligible impact.

---

## 9. TIMELINE

Project Halcyon follows a phased approach with strict milestones. All dates are fixed to ensure the client's $2M annual commitment is secured.

### Phase 1: Foundation (Now – 2026-05-15)
*   **Focus:** Core Rust firmware and basic API connectivity.
*   **Key Activity:** Establishing the SQLite edge-buffer and basic Cloudflare Worker routing.
*   **Dependency:** Setup of the basic network layer.
*   **Milestone 1:** **Performance benchmarks met (2026-05-15).**

### Phase 2: Feature Implementation (2026-05-16 – 2026-07-15)
*   **Focus:** Reports, Rate Limiting, and RBAC.
*   **Key Activity:** Developing the PDF/CSV generation engine and the React dashboard.
*   **Dependency:** Completion of the database schema.
*   **Milestone 2:** **MVP feature-complete (2026-07-15).**

### Phase 3: Hardening & Review (2026-07-16 – 2026-09-15)
*   **Focus:** QA, Security Audits, and Optimization.
*   **Key Activity:** Stress testing the sync manager and finalizing HIPAA documentation.
*   **Dependency:** Stable MVP build.
*   **Milestone 3:** **Architecture review complete (2026-09-15).**

---

## 10. MEETING NOTES

### Meeting 1: Tech Stack Alignment
**Date:** 2025-11-02  
**Attendees:** Wanda, Maren, Lev, Juno  
*   Rust vs C++ debate.
*   Maren prefers Rust for memory safety.
*   Wanda agrees.
*   Lev concerned about testing tools for Rust.
*   Decision: Use `cargo-tarpaulin` for coverage.

### Meeting 2: Budget Crisis
**Date:** 2025-12-15  
**Attendees:** Wanda, Juno  
*   Budget too tight.
*   Tool purchase for visual builder blocked.
*   Juno suggests open-source alternatives.
*   Wanda says "not robust enough" for this client.
*   Pending: Budget approval for the library.

### Meeting 3: Sprint 4 Retrospective
**Date:** 2026-01-20  
**Attendees:** All  
*   Sync issues on edge.
*   Maren found a bug in SQLite WAL mode.
*   Fix implemented.
*   Lev says QA gate is taking too long.
*   Wanda: "2 days is non-negotiable for stability."

---

## 11. BUDGET BREAKDOWN

The budget is a strict $150,000. Every dollar is allocated to ensure maximum efficiency.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Small team of 4; partial allocation of internal salaries. |
| **Infrastructure** | 20% | $30,000 | Cloudflare Workers, PostgreSQL, S3 buckets. |
| **Tools/Licenses** | 15% | $22,500 | Specialized IDEs, PDF libraries (pending approval). |
| **Contingency** | 5% | $7,500 | Emergency hardware replacements. |
| **Total** | **100%** | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Checklist
To meet the legal requirements for health-integrated F&B environments, Halcyon adheres to the following:
1.  **Encryption at Rest:** All SQLite databases on the edge are encrypted using SQLCipher with AES-256.
2.  **Encryption in Transit:** TLS 1.3 is mandatory for all communication between edge and cloud.
3.  **Access Control:** RBAC is strictly enforced; no "God Mode" exists without a multi-sig approval for SuperAdmin access.
4.  **Auditability:** Every API call that accesses PII (Personally Identifiable Information) is logged in the `audit_trail` table with a non-nullable timestamp and user ID.

### Appendix B: Protobuf Schema (Simplified)
For efficiency, the device communicates using the following structure rather than JSON:

```protobuf
message TelemetryPacket {
  string device_id = 1;
  uint64 timestamp = 2;
  float temperature = 3;
  float humidity = 4;
  bool alarm_active = 5;
}

message SyncResponse {
  uint64 last_processed_id = 1;
  bool success = 2;
  string error_message = 3;
}
```
This reduces the payload size by approximately 60%, contributing directly to the metric of reducing cost per transaction by 35%.