# PROJECT SPECIFICATION DOCUMENT: PROJECT HALCYON (v2.1.0)

**Company:** Flintrock Engineering  
**Industry:** Food and Beverage  
**Date:** May 22, 2024  
**Document Status:** Active/Reference  
**Confidentiality Level:** Internal/HIPAA Compliant  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Halcyon is a specialized cybersecurity monitoring dashboard designed for Flintrock Engineering. Originally conceived during a company-wide hackathon as a proof-of-concept to visualize network anomalies across food production facilities, Halcyon has rapidly evolved into a critical internal productivity tool. Currently supporting 500 daily active users (DAU), the tool provides real-time visibility into the security posture of Industrial Control Systems (ICS), IoT sensors in beverage bottling lines, and corporate administrative networks.

The primary goal of the current development phase is to transition Halcyon from a "successful prototype" to a "hardened enterprise product." This involves implementing critical reporting capabilities, stabilizing the offline-first synchronization engine, and ensuring strict adherence to HIPAA compliance standards—necessitated by Flintrock Engineering’s expansion into nutritional health services and biometric employee monitoring.

### 1.2 Business Justification
In the food and beverage industry, downtime is measured in thousands of dollars per minute. A cybersecurity breach targeting the PLC (Programmable Logic Controllers) of a bottling plant can lead to physical spoilage of product or, worse, safety hazards. Halcyon mitigates this risk by centralizing disparate security logs into a single pane of glass. 

Before Halcyon, security analysts spent approximately 15 hours per week manually aggregating logs from three different vendors. With Halcyon’s automated aggregation and visualization, this overhead has been reduced to under 2 hours per week. This represents a significant gain in operational efficiency and a reduction in the Mean Time to Detect (MTTD) security incidents.

### 1.3 ROI Projection
The Return on Investment (ROI) for Halcyon is calculated based on three primary vectors:
1. **Labor Cost Reduction:** By automating report generation and log aggregation, we estimate a saving of 1.2 FTEs (Full Time Equivalents) across the security operations center (SOC), totaling approximately $180,000/year.
2. **Risk Mitigation:** The average cost of a breach in the manufacturing sector is $4.5M. By reducing MTTD by an estimated 40%, Halcyon lowers the probability of a catastrophic outage.
3. **Compliance Savings:** Automated HIPAA audit trails eliminate the need for external consultants to manually verify data encryption, saving an estimated $45,000 per annual audit cycle.

**Projected 3-Year ROI:** 340%, with a break-even point reached 7 months post-production launch (December 2025).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Halcyon utilizes a modern, high-performance stack designed for low latency and high reliability. The core philosophy is a **Micro-Frontend Architecture**, allowing the 2-person core team (augmented by junior support) to deploy updates to specific dashboard widgets without risking the stability of the entire application.

**The Stack:**
- **Backend:** Rust (Actix-web framework) for memory safety and high concurrency.
- **Frontend:** React 18.x with TypeScript and Tailwind CSS.
- **Edge Layer:** Cloudflare Workers for global request routing and low-latency authentication checks.
- **Edge Storage:** SQLite (via WASM/Origin) for local caching and offline-first capabilities.
- **CI/CD:** GitHub Actions.

### 2.2 Architecture Diagram (ASCII)

```text
[ User Browser ] <---> [ Cloudflare Workers (Edge Auth/Routing) ]
                               |
                               v
        _______________________|_______________________
       |                                               |
 [ React Frontend ] <--- (WebSocket) ---> [ Rust Backend (Actix) ]
       |                                               |
       | (Local Storage/IndexedDB)                     | (gRPC/REST)
       v                                               v
 [ SQLite Edge DB ] <--------------------------> [ Central Postgres/S3 ]
 (Offline-First Sync)                             (Persistent Store)
                                                      |
                                                      v
                                             [ External Security Logs ]
                                             (Firewalls, IDS, PLC Logs)
```

### 2.3 Technical Design Decisions
- **Rust for Backend:** Chosen specifically to handle the high volume of security telemetry data without the garbage collection pauses associated with Java or Node.js, ensuring that real-time alerts are processed in milliseconds.
- **SQLite at Edge:** To support "offline-first" mode, the application synchronizes a subset of the global state to a local SQLite database. This ensures that if a plant manager loses internet connectivity in a remote area of the warehouse, they can still view the last known security state of their equipment.
- **Blue-Green Deployment:** To ensure 99.9% uptime, GitHub Actions deploys to a "Green" environment. Once smoke tests pass, the Cloudflare Worker shifts traffic from "Blue" to "Green."

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation (Priority: Critical)
**Status:** In Review | **Launch Blocker:** Yes

**Description:** 
The system must generate comprehensive security posture reports. These reports are used by the steering committee for quarterly reviews and by external auditors for HIPAA compliance verification.

**Detailed Functional Requirements:**
- **Template Engine:** The system will use a LaTeX-based engine on the backend to generate high-fidelity PDFs.
- **Data Aggregation:** Reports must aggregate data from the `security_events` and `audit_logs` tables, summarizing total threats detected, blocked vs. ignored alerts, and system uptime.
- **Scheduling:** Users can define a CRON expression (e.g., `0 0 1 * *` for the 1st of every month) to trigger reports.
- **Delivery:** Reports are delivered via email (SMTP) and uploaded to an encrypted S3 bucket with a time-limited signed URL.
- **CSV Export:** A raw data dump feature allowing analysts to export specific filtered views of the dashboard into CSV format for further analysis in Excel or Tableau.

**Acceptance Criteria:**
- Reports generated in under 30 seconds for a standard 30-day window.
- PDF layouts maintain branding consistency for Flintrock Engineering.
- Scheduled reports arrive within 15 minutes of the scheduled time.

### 3.2 Offline-First Mode with Background Sync (Priority: High)
**Status:** In Progress

**Description:**
Given the industrial environment of food production plants, intermittent Wi-Fi is common. Halcyon must remain functional without a live connection.

**Detailed Functional Requirements:**
- **Local Persistence:** The React frontend will interface with a SQLite WASM instance. All critical dashboard state is mirrored locally.
- **Queueing System:** Any actions taken while offline (e.g., acknowledging an alert) are stored in an `outbox` table in the local SQLite DB.
- **Conflict Resolution:** The system uses a "Last Write Wins" (LWW) strategy based on synchronized NTP timestamps to resolve conflicts when the device reconnects.
- **Background Sync:** Utilizing Service Workers, the app will detect the `online` event and trigger a synchronization process that pushes the `outbox` to the Rust backend and pulls the latest delta updates.

**Acceptance Criteria:**
- App loads in < 2 seconds when offline using cached data.
- Background sync completes without user intervention upon reconnection.
- No data loss during transitions between 4G and Wi-Fi.

### 3.3 Webhook Integration Framework (Priority: High)
**Status:** In Review

**Description:**
Halcyon must act as a hub, pushing security alerts to third-party tools (e.g., PagerDuty, Slack, Jira) via customizable webhooks.

**Detailed Functional Requirements:**
- **Payload Customization:** A visual editor where users can map Halcyon event fields (e.g., `severity`, `source_ip`, `timestamp`) to JSON keys required by the third-party API.
- **Retry Logic:** Implementation of an exponential backoff strategy (1min, 5min, 15min, 1hr) for failed deliveries (HTTP 5xx or 429).
- **Secret Management:** Each webhook must have a unique `signing_secret` used to generate an HMAC-SHA256 signature in the header, allowing the receiver to verify the authenticity of the request.
- **Event Filtering:** Users can specify which alerts trigger a webhook (e.g., only "Critical" severity events from the "Bottling Line 4" zone).

**Acceptance Criteria:**
- Webhooks trigger within 5 seconds of an event being logged in the backend.
- Correct HMAC signatures are generated and validated.
- Failed webhooks are logged in the "Integration Health" dashboard.

### 3.4 Notification System (Priority: High)
**Status:** Not Started

**Description:**
A multi-channel alerting system to ensure security analysts are notified of critical threats regardless of their current device or connectivity.

**Detailed Functional Requirements:**
- **In-App Notifications:** A real-time notification bell using WebSockets (Rust `tokio-tungstenite`) to push alerts to the active UI.
- **Email Alerts:** Integration with AWS SES for detailed alert summaries.
- **SMS Notifications:** Integration with Twilio for high-priority "Wake Up" alerts.
- **Push Notifications:** Web-push API implementation for browser-level notifications.
- **Preference Center:** A user settings page allowing users to toggle channels based on alert severity (e.g., "Critical" $\rightarrow$ SMS/Push/Email; "Low" $\rightarrow$ In-app only).

**Acceptance Criteria:**
- Push notifications delivered to mobile browsers within 10 seconds.
- SMS messages correctly formatted and delivered via Twilio.
- User preferences are respected across all channels.

### 3.5 Customer-Facing API (Priority: Low)
**Status:** Complete

**Description:**
A versioned REST API allowing internal stakeholders or approved third-party vendors to programmatically query the security status.

**Detailed Functional Requirements:**
- **Versioning:** API is versioned via the URL path (e.g., `/api/v1/`).
- **Sandbox Environment:** A mirrored "Sandbox" environment with mocked data for developers to test their integrations without affecting production telemetry.
- **Authentication:** API Key-based authentication with rotation capabilities.
- **Rate Limiting:** Tiered rate limiting implemented via Cloudflare Workers (e.g., 100 requests/minute for standard users).

**Acceptance Criteria:**
- API returns standard JSON responses with consistent error codes.
- Sandbox environment behaves identically to production regarding schema.
- Rate limiting correctly triggers HTTP 429 responses.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer` token in the Authorization header.

### 4.1 `GET /alerts`
**Description:** Retrieves a list of active security alerts.
- **Query Params:** `severity` (optional), `status` (optional), `limit` (default 50).
- **Request Example:** `GET /api/v1/alerts?severity=critical`
- **Response Example:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "alt-9901",
      "timestamp": "2024-05-22T14:30:00Z",
      "severity": "critical",
      "message": "Unauthorized PLC access detected in Zone B",
      "source": "192.168.1.45"
    }
  ],
  "pagination": { "total": 1, "next": null }
}
```

### 4.2 `POST /alerts/{id}/acknowledge`
**Description:** Marks an alert as acknowledged by an analyst.
- **Request Example:** `POST /api/v1/alerts/alt-9901/acknowledge`
- **Response Example:**
```json
{
  "status": "success",
  "updated_at": "2024-05-22T14:35:00Z",
  "acknowledged_by": "amira.santos@flintrock.com"
}
```

### 4.3 `GET /reports/scheduled`
**Description:** Returns a list of all configured scheduled reports.
- **Response Example:**
```json
{
  "reports": [
    {
      "id": "rep-123",
      "name": "Monthly Compliance",
      "cron": "0 0 1 * *",
      "format": "PDF",
      "recipients": ["exec-team@flintrock.com"]
    }
  ]
}
```

### 4.4 `POST /reports/generate`
**Description:** Manually triggers a report generation.
- **Request Body:** `{"report_type": "security_summary", "start_date": "2024-01-01", "end_date": "2024-01-31", "format": "CSV"}`
- **Response Example:**
```json
{
  "job_id": "job-abc-123",
  "status": "processing",
  "estimated_completion": "15s"
}
```

### 4.5 `GET /system/health`
**Description:** Returns the health status of the backend and database connections.
- **Response Example:**
```json
{
  "status": "healthy",
  "uptime": "142h 12m",
  "database": "connected",
  "redis_cache": "connected"
}
```

### 4.6 `POST /webhooks/create`
**Description:** Registers a new webhook endpoint.
- **Request Body:** `{"target_url": "https://hooks.slack.com/services/...", "events": ["critical_alert"], "secret": "user-defined-secret"}`
- **Response Example:**
```json
{
  "webhook_id": "wh-778",
  "status": "active",
  "verification_url": "https://halcyon.flintrock.io/verify/wh-778"
}
```

### 4.7 `GET /user/preferences`
**Description:** Retrieves notification preferences for the authenticated user.
- **Response Example:**
```json
{
  "user_id": "user-44",
  "notifications": {
    "email": true,
    "sms": false,
    "push": true,
    "in_app": true
  }
}
```

### 4.8 `PUT /user/preferences`
**Description:** Updates notification preferences.
- **Request Body:** `{"notifications": {"sms": true}}`
- **Response Example:**
```json
{ "status": "updated", "timestamp": "2024-05-22T15:00:00Z" }
```

---

## 5. DATABASE SCHEMA

Halcyon uses a relational model to ensure data integrity and HIPAA-compliant audit trails.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role`, `mfa_secret` | 1:N $\rightarrow$ `audit_logs` | System users and auth data. |
| `assets` | `asset_id` | `ip_address`, `mac_address`, `zone_id`, `asset_type` | N:1 $\rightarrow$ `zones` | Physical/Virtual devices monitored. |
| `zones` | `zone_id` | `zone_name`, `location`, `security_level` | 1:N $\rightarrow$ `assets` | Physical plant areas (e.g., "Bottling Line A"). |
| `security_events`| `event_id` | `asset_id`, `severity`, `event_type`, `payload` | N:1 $\rightarrow$ `assets` | Raw security telemetry logs. |
| `alerts` | `alert_id` | `event_id`, `status` (open/closed), `assigned_to` | 1:1 $\rightarrow$ `security_events` | Escalated events requiring action. |
| `audit_logs` | `log_id` | `user_id`, `action`, `timestamp`, `ip_address` | N:1 $\rightarrow$ `users` | HIPAA compliant record of all changes. |
| `webhooks` | `webhook_id` | `target_url`, `secret`, `active_status` | 1:N $\rightarrow$ `webhook_logs` | Third-party integration configs. |
| `webhook_logs` | `delivery_id` | `webhook_id`, `response_code`, `retry_count` | N:1 $\rightarrow$ `webhooks` | History of webhook deliveries. |
| `scheduled_reports`| `report_id` | `cron_schedule`, `format`, `recipient_email` | N:1 $\rightarrow$ `users` | Cron-based report configs. |
| `notification_prefs`| `pref_id` | `user_id`, `channel`, `enabled` | N:1 $\rightarrow$ `users` | User-level alert settings. |

### 5.2 HIPAA Compliance Implementation
- **Encryption at Rest:** All tables in the production Postgres instance are encrypted using AES-256.
- **Encryption in Transit:** All data moving between the React frontend, Cloudflare Workers, and the Rust backend is forced over TLS 1.3.
- **Immutable Audit Logs:** The `audit_logs` table is configured as an "append-only" table; no `UPDATE` or `DELETE` operations are permitted on this table.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy

| Environment | Purpose | Infrastructure | Data Source |
| :--- | :--- | :--- | :--- |
| **Development** | Local iteration | Docker Compose (Rust, Postgres) | Mock Data / Seed Scripts |
| **Staging** | QA and Stakeholder Demo | Cloudflare Workers (Staging), AWS EC2 (t3.medium) | Sanitized Prod Snapshot |
| **Production** | End User Access | Cloudflare Workers (Prod), AWS EKS (Auto-scaling) | Live Production Data |

### 6.2 CI/CD Pipeline (GitHub Actions)
The pipeline currently consists of three stages:
1. **Build & Lint:** Runs `cargo fmt` and `npm run lint`. (Current duration: 5 mins)
2. **Test Suite:** Executes unit tests and integration tests. (Current duration: 10 mins)
3. **Deploy:** Performs a blue-green deployment via Cloudflare Wrangler. (Current duration: 30 mins)

**Known Issue:** The total pipeline duration is 45 minutes. This is identified as a primary source of technical debt. The team intends to parallelize the Rust compilation process using a distributed build cache to reduce this to < 15 minutes.

### 6.3 Blue-Green Deployment Logic
1. New version is deployed to the **Green** environment.
2. A health check endpoint `/system/health` is polled.
3. If 200 OK is received, the Cloudflare Worker updates the routing table to point 10% of traffic to Green (Canary).
4. If error rates remain $< 0.1\%$, traffic is shifted to 100% Green.
5. The **Blue** environment is kept on standby for 30 minutes for immediate rollback.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `#[cfg(test)]` modules for every logic component. Focus on the synchronization engine and HMAC generation.
- **Frontend:** Vitest for utility functions and state management logic (Zustand stores).
- **Target:** 80% code coverage.

### 7.2 Integration Testing
- **API Testing:** Postman collections integrated into GitHub Actions to validate endpoint responses and status codes.
- **Database Testing:** Test containers (via Docker) to run migrations and verify schema constraints.
- **Sync Testing:** Simulated network latency and disconnects to verify the SQLite background sync logic.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Critical Paths:** 
    1. User login $\rightarrow$ View Critical Alert $\rightarrow$ Acknowledge Alert.
    2. Configure Webhook $\rightarrow$ Trigger Event $\rightarrow$ Verify External Delivery.
    3. Schedule Report $\rightarrow$ Wait for Trigger $\rightarrow$ Download PDF.
- **Frequency:** Run on every merge to the `main` branch.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Budget may be cut by 30% in next fiscal quarter. | Medium | High | Escalate to steering committee; prioritize "Critical" features and defer "Low" priority API enhancements. |
| **R-02** | Primary vendor dependency announced End-of-Life (EOL). | High | Medium | Document workarounds; evaluate open-source alternatives; allocate 2 sprints for migration. |
| **R-03** | Design disagreement between Product and Engineering leads. | High | Medium | Establish a "Design Tie-breaker" process; use A/B testing with a small user group (10 users) to decide. |
| **R-04** | CI Pipeline inefficiency (45 min build time). | High | Low | Implement parallelization and caching in GitHub Actions. |
| **R-05** | Failure to pass HIPAA external audit. | Low | Critical | Monthly internal pre-audits; strict adherence to encryption standards. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required.
- **Medium/High:** Active monitoring and mitigation.
- **Low/Medium:** Logged and reviewed monthly.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Hardening (Now $\rightarrow$ Aug 2025):** Focus on the "launch blockers." Implementation of PDF reporting and stabilizing the offline-first synchronization.
- **Phase 2: Validation (Aug 2025 $\rightarrow$ Oct 2025):** User Acceptance Testing (UAT) and stakeholder demos. Refining the UI based on Tomas's research.
- **Phase 3: Deployment (Oct 2025 $\rightarrow$ Dec 2025):** Gradual rollout, final HIPAA audit, and production scaling.

### 9.2 Milestone Schedule

| Milestone | Target Date | Dependency | Goal |
| :--- | :--- | :--- | :--- |
| **M1: MVP Feature-Complete** | 2025-08-15 | Webhook Framework | All high/critical features (PDF, Sync, Webhooks) operational. |
| **M2: Stakeholder Sign-off** | 2025-10-15 | M1 Completion | Demo of the full workflow to Flintrock VP of Engineering. |
| **M3: Production Launch** | 2025-12-15 | External Audit | 100% migration of 500 users to the new hardened version. |

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team dynamic, formal meeting minutes are not kept. The following are curated summaries of decision-making threads from the `#halcyon-dev` Slack channel.

### Thread 1: The "Offline Mode" Dispute
**Date:** 2024-03-12
**Participants:** Amira Santos, Tomas Moreau, Kamau Gupta
**Context:** Discussion on whether to use IndexedDB or SQLite WASM for offline storage.
- **Tomas:** "IndexedDB is easier for the frontend, but the data structure is too loose for security logs."
- **Amira:** "We need the relational power of SQL for the sync logic. If we use SQLite WASM, we can run the same queries on the edge as we do on the backend."
- **Kamau:** "Isn't the binary size for SQLite WASM too large for the initial load?"
- **Amira:** "We can lazy-load it. Let's go with SQLite."
- **Decision:** **SQLite WASM adopted for offline-first mode.**

### Thread 2: The PDF Blocker
**Date:** 2024-04-05
**Participants:** Xavi Moreau, Amira Santos
**Context:** Tension regarding the priority of PDF reports vs. the Notification system.
- **Xavi:** "The board won't sign off on the budget for Q3 if they don't see the monthly PDF reports. It's a launch blocker."
- **Amira:** "The notification system is more technically urgent for the users. Why are we prioritizing a PDF over real-time SMS?"
- **Xavi:** "Because the PDF is how we prove compliance. No compliance = no project. It moves to 'Critical'."
- **Decision:** **PDF generation is now a "Critical" launch blocker; Notification system moved to "High".**

### Thread 3: CI Pipeline Venting
**Date:** 2024-05-10
**Participants:** Amira Santos, Kamau Gupta
**Context:** Frustration over the 45-minute CI wait time.
- **Kamau:** "I've spent more time waiting for GitHub Actions today than actually coding."
- **Amira:** "It's a mess. We're compiling the entire Rust toolchain from scratch on every push. We need to implement `sccache` or use a dedicated runner."
- **Decision:** **Added "CI Optimization" to the technical debt backlog; to be addressed after Milestone 1.**

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches upon the completion of milestones.

### 11.1 Budget Allocation (Annualized)

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $380,000 | 2 Full-time engineers, 1 Part-time UX Researcher. |
| **Infrastructure** | $24,000 | AWS EKS, Cloudflare Enterprise, S3 Storage. |
| **Tooling** | $12,000 | GitHub Enterprise, Twilio API, AWS SES, PagerDuty. |
| **Contingency** | $45,000 | Reserved for emergency vendor migration or audit failures. |
| **Total** | **$461,000** | |

### 11.2 Funding Tranche Schedule
- **Tranche 1 (Initial):** $150,000 (Released at project start).
- **Tranche 2 (M1 Sign-off):** $160,000 (Released 2025-08-15).
- **Tranche 3 (M2 Sign-off):** $151,000 (Released 2025-10-15).

---

## 12. APPENDICES

### Appendix A: HIPAA Encryption Matrix
To satisfy the external audit, the following encryption standards are mandated for all Halcyon components:

| Data State | Encryption Standard | Implementation |
| :--- | :--- | :--- |
| **At Rest (DB)** | AES-256 | AWS RDS Encryption / EBS Volume Encryption |
| **In Transit** | TLS 1.3 | Cloudflare Edge Certificates $\rightarrow$ Backend |
| **At Rest (Logs)** | PGP / AES-GCM | S3 Server-Side Encryption with KMS |
| **Auth Tokens** | JWT (RS256) | Signed with private key, rotated every 24 hours |

### Appendix B: Vendor Dependency Map
The team must monitor the following dependencies, particularly those nearing EOL.

- **Dependency A (Network Telemetry Provider):** Currently providing the raw log stream. **Status:** EOL announced for v3.4. **Action:** Amira is evaluating "OpenTelemetry" as a replacement.
- **Dependency B (Cloudflare Workers):** Core routing and auth. **Status:** Stable.
- **Dependency C (Twilio):** SMS Gateway. **Status:** Stable.
- **Dependency D (AWS SES):** Email delivery. **Status:** Stable.