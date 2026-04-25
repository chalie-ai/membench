# PROJECT SPECIFICATION DOCUMENT: PROJECT WAYFINDER
**Version:** 1.0.4-BETA  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Document Owner:** Xavi Costa (CTO, Clearpoint Digital)  
**Classification:** Internal Confidential

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Wayfinder** is a specialized embedded systems firmware and accompanying management suite developed by Clearpoint Digital. Originally conceived during a company-wide hackathon, Wayfinder has evolved from a proof-of-concept into a critical internal productivity tool used by 500 daily users within the real estate sector. The project aims to bridge the gap between physical real estate asset management and digital oversight through a high-performance firmware layer that interfaces with proprietary hardware sensors and a cloud-based management dashboard.

The core objective of Wayfinder is to automate the tracking and operational efficiency of physical assets (smart locks, environmental sensors, and occupancy monitors) across diverse real estate portfolios. By integrating embedded firmware with a modern web stack, Clearpoint Digital intends to reduce manual site visits by 40% and increase asset uptime to 99.9%.

### 1.2 Business Justification
Within the real estate industry, the lack of standardized communication between embedded hardware and management software leads to "data silos." Wayfinder solves this by providing a unified TypeScript-based orchestration layer. The transition from a hackathon project to a formal internal tool is driven by the immediate demand from the operations team to scale the current 500-user base to a broader corporate rollout.

The business justification rests on three pillars:
1. **Operational Efficiency:** Reducing the time spent on manual hardware resets and configuration.
2. **Data Centralization:** Moving from fragmented CSV logs to a real-time PostgreSQL database.
3. **Scalability:** Transitioning the "modular monolith" to a microservices architecture to handle the projected increase in device density.

### 1.3 ROI Projection
With a total project budget of $150,000, the Return on Investment (ROI) is calculated based on the reduction of labor hours for field technicians. 

*   **Current Manual Cost:** 500 users spending an average of 2 hours/week on manual asset auditing = 1,000 hours/week.
*   **Projected Automated Cost:** Wayfinder reduces this to 30 minutes/week per user = 250 hours/week.
*   **Labor Savings:** 750 hours/week $\times$ $65/hour avg. technician rate = $48,750 per week.
*   **Break-even Point:** Given the $150,000 budget, the project will reach a break-even point within approximately 3.1 weeks of full operational deployment, assuming 100% adoption.

The long-term financial goal is to scale to 10,000 Monthly Active Users (MAUs) within six months of launch, which would project a yearly operational saving of approximately $12 million in labor and efficiency gains.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Wayfinder utilizes a hybrid architecture combining low-level embedded firmware (C/C++ for device logic) with a modern full-stack management layer:
*   **Frontend/Backend:** TypeScript, Next.js (App Router)
*   **ORM:** Prisma
*   **Database:** PostgreSQL (Hosted on AWS RDS)
*   **Deployment/Hosting:** Vercel (Frontend/API), AWS (Firmware binaries/IoT Core)
*   **Communication:** MQTT for device-to-cloud; REST/Webhooks for cloud-to-third-party.

### 2.2 System Architecture Diagram (ASCII)
The following diagram illustrates the flow from the physical embedded device to the end-user dashboard.

```text
[ Embedded Device ] <---(MQTT/TLS)---> [ AWS IoT Core ]
       |                                      |
       | (Firmware Logic)                      | (Data Stream)
       v                                      v
[ Hardware Sensors ]                   [ Next.js API Routes ]
(Zigbee/LoRaWAN)                              |
                                              | (Prisma ORM)
                                              v
[ Third Party Tools ] <---(Webhooks)--- [ PostgreSQL DB ]
(CRM / Billing / ERP)                         ^
                                              |
                                      [ Vercel Deployment ]
                                              |
                                      [ User Dashboard ]
                                      (Next.js/TypeScript)
```

### 2.3 Architectural Transition: Monolith to Microservices
Currently, Wayfinder is a **modular monolith**. All logic for billing, localization, and device management resides within a single Next.js codebase. To prevent the "bus factor of 1" (currently the single DevOps person) from becoming a catastrophic failure point, the team is incrementally extracting services.
*   **Phase 1:** Extract the *Webhook Framework* into a standalone Lambda function.
*   **Phase 2:** Migrate *Billing and Subscription* to a separate service to isolate financial data.
*   **Phase 3:** Separate the *Localization Engine* to allow for independent updates to language packs without redeploying the entire core.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/i18n)
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:** 
Wayfinder must support 12 distinct languages to accommodate Clearpoint Digital's global real estate expansion. This is not merely a UI translation task but a comprehensive firmware and cloud synchronization effort. The firmware must be capable of pushing localized alert messages to hardware displays, while the Next.js dashboard must dynamically switch languages based on user profile settings or browser headers.

**Technical Requirements:**
*   **Implementation:** Use `next-intl` for the frontend and a custom JSON-based translation map stored in PostgreSQL for the firmware's dynamic strings.
*   **Supported Languages:** English (US), English (UK), Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, and Dutch.
*   **Firmware Constraint:** String tables must be compressed to fit within the 256KB flash memory limit of the embedded controllers.
*   **Fallback Logic:** All requests must fall back to English (US) if a specific key is missing in the target language locale.

**Workflow:**
1. The user selects a language in the "Account Settings" dashboard.
2. An API call updates the `UserPreferences` table.
3. A "Locale Update" command is sent via MQTT to the associated embedded device.
4. The device updates its internal string pointer to the corresponding language offset in the flash memory.

### 3.2 Webhook Integration Framework
**Priority:** High | **Status:** Blocked

**Description:**
To make Wayfinder a central hub for real estate productivity, it must communicate with third-party tools (e.g., Salesforce, Yardi, AppFolio). The Webhook Framework allows Wayfinder to push real-time events (e.g., "Device Offline," "Battery Low," "Unauthorized Access") to external endpoints.

**Technical Requirements:**
*   **Event Trigger System:** A middleware layer in the Next.js API that monitors Prisma events.
*   **Payload Structure:** Standardized JSON payloads containing `event_type`, `timestamp`, `device_id`, and `payload_data`.
*   **Retry Logic:** Exponential backoff retry mechanism for failed deliveries (Max 5 retries over 24 hours).
*   **Security:** HMAC signatures included in the header (`X-Wayfinder-Signature`) to allow third-party tools to verify the authenticity of the request.

**Current Blocker:** The integration partner's API is undocumented and buggy, preventing the finalization of the payload handshake.

### 3.3 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** Blocked

**Description:**
As Wayfinder moves from an internal tool to a potentially billable service for partners, an automated billing system is required. This includes subscription tiers (Basic, Pro, Enterprise) and usage-based billing tied to the number of embedded devices active in the field.

**Technical Requirements:**
*   **Payment Gateway:** Integration with Stripe for recurring billing.
*   **Tier Enforcement:** A middleware check on every API request to verify the user's current subscription level.
*   **Usage Tracking:** A daily cron job that counts active `Device` entries in the database and updates the `SubscriptionUsage` table.
*   **Invoicing:** Automatic PDF generation of monthly invoices via a serverless function.

**Current Blocker:** Lack of definitive pricing approval from the executive board.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:**
Users require different data views depending on their role (e.g., a technician needs battery levels; a manager needs occupancy rates). A customizable dashboard allows users to add, remove, and rearrange widgets.

**Technical Requirements:**
*   **Library:** Integration of `react-grid-layout` for the drag-and-drop interface.
*   **Persistence:** Widget coordinates (`x`, `y`, `w`, `h`) and widget IDs must be stored in the `UserDashboardConfig` table in PostgreSQL.
*   **Widget Types:** 
    *   *Device Health Gauge:* Real-time signal strength.
    *   *Activity Feed:* Recent events from the webhook framework.
    *   *Asset Map:* Geospatial view of all embedded devices.
*   **Performance:** Client-side caching of widget data to prevent excessive API calls during drag-and-drop operations.

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Description:**
For large-scale real estate deployments, multiple engineers often configure the same set of devices. Collaborative editing allows multiple users to modify device configurations in real-time without overwriting each other's changes.

**Technical Requirements:**
*   **Protocol:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) via Yjs.
*   **Transport:** WebSocket connection (via Socket.io) to broadcast changes across clients.
*   **State Management:** A "Presence" indicator showing which user is currently editing a specific device configuration field.
*   **Conflict Strategy:** "Last Write Wins" (LWW) for non-critical fields; "Manual Merge" for critical firmware parameter changes.

**Current Blocker:** Backend resource constraints; the current modular monolith cannot handle the WebSocket overhead without a dedicated Redis instance for pub/sub.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is handled via JWT in the `Authorization: Bearer <token>` header.

### 4.1 `GET /devices`
**Description:** Retrieves a list of all embedded devices associated with the user's organization.
*   **Request:** `GET /api/v1/devices?status=online&limit=50`
*   **Response (200 OK):**
```json
[
  {
    "id": "dev_9921",
    "name": "North Wing Sensor 01",
    "status": "online",
    "firmware_version": "2.1.0",
    "last_ping": "2023-10-24T14:22:01Z"
  }
]
```

### 4.2 `POST /devices/{id}/config`
**Description:** Pushes a new configuration payload to a specific embedded device.
*   **Request:** `POST /api/v1/devices/dev_9921/config`
*   **Body:**
```json
{
  "polling_interval": 300,
  "power_mode": "low_power",
  "alert_threshold": 85
}
```
*   **Response (202 Accepted):** `{"message": "Config queued for deployment", "job_id": "job_abc123"}`

### 4.3 `GET /billing/subscription`
**Description:** Returns current subscription status and usage metrics.
*   **Request:** `GET /api/v1/billing/subscription`
*   **Response (200 OK):**
```json
{
  "plan": "Enterprise",
  "status": "active",
  "devices_used": 412,
  "device_limit": 500,
  "renewal_date": "2024-01-15"
}
```

### 4.4 `POST /webhooks/register`
**Description:** Registers a new third-party endpoint for event notifications.
*   **Request:** `POST /api/v1/webhooks/register`
*   **Body:**
```json
{
  "target_url": "https://api.external-crm.com/wayfinder",
  "events": ["device.offline", "battery.critical"],
  "secret": "whsec_kL92mN1..."
}
```
*   **Response (201 Created):** `{"webhook_id": "wh_5542", "status": "active"}`

### 4.5 `PATCH /users/preferences`
**Description:** Updates user preferences, including localization settings.
*   **Request:** `PATCH /api/v1/users/preferences`
*   **Body:**
```json
{
  "language": "fr",
  "timezone": "Europe/Paris",
  "notifications_enabled": true
}
```
*   **Response (200 OK):** `{"status": "updated", "updated_at": "2023-10-24T10:00:00Z"}`

### 4.6 `GET /analytics/health`
**Description:** Aggregated health data for all deployed firmware.
*   **Request:** `GET /api/v1/analytics/health`
*   **Response (200 OK):**
```json
{
  "total_devices": 500,
  "online": 482,
  "offline": 18,
  "firmware_distribution": {
    "v2.1.0": 400,
    "v2.0.9": 100
  }
}
```

### 4.7 `DELETE /devices/{id}`
**Description:** Decommissions a device and wipes its cloud configuration.
*   **Request:** `DELETE /api/v1/devices/dev_9921`
*   **Response (204 No Content):** (Empty body)

### 4.8 `GET /system/status`
**Description:** Heartbeat endpoint for monitoring system uptime and CI/CD health.
*   **Request:** `GET /api/v1/system/status`
*   **Response (200 OK):**
```json
{
  "uptime": "14d 6h 22m",
  "db_connection": "healthy",
  "api_latency": "42ms",
  "version": "1.0.4-BETA"
}
```

---

## 5. DATABASE SCHEMA

The database is managed via Prisma ORM on a PostgreSQL instance.

### 5.1 Tables and Relationships

1.  **`User`**
    *   `id` (UUID, PK): Unique identifier.
    *   `email` (String, Unique): User login.
    *   `password_hash` (String): Bcrypt hash.
    *   `role` (Enum): `ADMIN`, `TECH`, `MANAGER`.
    *   `org_id` (FK $\to$ `Organization.id`).

2.  **`Organization`**
    *   `id` (UUID, PK): Unique identifier.
    *   `name` (String): Company name.
    *   `subscription_tier` (Enum): `BASIC`, `PRO`, `ENTERPRISE`.
    *   `created_at` (DateTime).

3.  **`Device`**
    *   `id` (String, PK): Hardware MAC address/Unique ID.
    *   `org_id` (FK $\to$ `Organization.id`).
    *   `firmware_version` (String).
    *   `status` (Enum): `ONLINE`, `OFFLINE`, `MAINTENANCE`.
    *   `last_ping` (DateTime).

4.  **`DeviceConfig`**
    *   `id` (UUID, PK).
    *   `device_id` (FK $\to$ `Device.id`).
    *   `settings` (JSONB): Stores polling rates, thresholds, etc.
    *   `version` (Integer): For conflict resolution.

5.  **`UserPreferences`**
    *   `user_id` (FK $\to$ `User.id`, PK).
    *   `language` (String): e.g., "en-US", "fr-FR".
    *   `timezone` (String).
    *   `theme` (Enum): `LIGHT`, `DARK`.

6.  **`Webhook`**
    *   `id` (UUID, PK).
    *   `org_id` (FK $\to$ `Organization.id`).
    *   `target_url` (String).
    *   `secret` (String): For HMAC signatures.
    *   `is_active` (Boolean).

7.  **`WebhookEvent`**
    *   `id` (UUID, PK).
    *   `webhook_id` (FK $\to$ `Webhook.id`).
    *   `event_type` (String).
    *   `payload` (JSONB).
    *   `attempt_count` (Integer).
    *   `last_attempt` (DateTime).

8.  **`SubscriptionUsage`**
    *   `id` (UUID, PK).
    *   `org_id` (FK $\to$ `Organization.id`).
    *   `month_year` (String): e.g., "2023-10".
    *   `device_count` (Integer).
    *   `billed_amount` (Decimal).

9.  **`UserDashboardConfig`**
    *   `id` (UUID, PK).
    *   `user_id` (FK $\to$ `User.id`).
    *   `layout_json` (JSONB): Stores widget coordinates and IDs.

10. **`AuditLog`**
    *   `id` (UUID, PK).
    *   `user_id` (FK $\to$ `User.id`).
    *   `action` (String).
    *   `timestamp` (DateTime).
    *   `ip_address` (String).

### 5.2 Entity Relationship Summary
*   **Organization $\to$ User:** One-to-Many.
*   **Organization $\to$ Device:** One-to-Many.
*   **Device $\to$ DeviceConfig:** One-to-One.
*   **User $\to$ UserPreferences:** One-to-One.
*   **Organization $\to$ Webhook:** One-to-Many.
*   **Webhook $\to$ WebhookEvent:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### 6.1.1 Development (`dev`)
*   **Host:** Local machines / Docker Desktop.
*   **Database:** Local PostgreSQL container.
*   **CI/CD:** Local git hooks.
*   **Purpose:** Individual feature development and unit testing.

#### 6.1.2 Staging (`staging`)
*   **Host:** Vercel Preview Deployments.
*   **Database:** Dedicated Staging RDS instance (subset of production data).
*   **CI/CD:** Automatic deploy on merge to `develop` branch.
*   **Purpose:** Integration testing and Stakeholder UAT (User Acceptance Testing).

#### 6.1.3 Production (`prod`)
*   **Host:** Vercel Production.
*   **Database:** Production RDS instance (High Availability, Multi-AZ).
*   **CI/CD:** Manual deployment triggered by the DevOps lead.
*   **Purpose:** Live environment for the 500 daily users.

### 6.2 The "Bus Factor" and DevOps Risk
Deployment is currently handled by a single DevOps person. This represents a critical risk. To mitigate this, the team is documenting the manual deployment scripts and moving toward a more automated GitHub Action workflow.

### 6.3 CI Pipeline Inefficiency
The current CI pipeline takes **45 minutes** per run. This is caused by:
1.  Sequential execution of TypeScript type-checking.
2.  Unoptimized Prisma schema generation.
3.  Lack of parallelization in the test suite.
*   **Immediate Goal:** Implement `turbo` (Turborepo) to cache builds and parallelize test execution to reduce time to $<10$ minutes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions and business logic (e.g., billing calculation, HMAC signature generation).
*   **Tooling:** Jest and Vitest.
*   **Requirement:** 80% code coverage for all new features.

### 7.2 Integration Testing
*   **Focus:** API endpoints, Database queries via Prisma, and MQTT message flow.
*   **Tooling:** Supertest and Postman Collections.
*   **Strategy:** Mocking the embedded hardware using a Python-based MQTT simulator to verify that the backend correctly processes device heartbeats.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** Critical user journeys (e.g., "User updates device config $\to$ Device receives update $\to$ User sees status change").
*   **Tooling:** Playwright.
*   **Execution:** Run weekly against the Staging environment.

### 7.4 Firmware Testing
*   **Hardware-in-the-Loop (HIL):** A dedicated test rig containing five physical devices of varying hardware revisions.
*   **Stress Testing:** Flooding the MQTT broker with 1,000 simulated devices to test the backend's ability to handle the projected 10k MAU scale.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Integration partner API is undocumented/buggy | High | High | Negotiate timeline extension with stakeholders; implement a "compatibility layer" to normalize buggy responses. |
| R-02 | Key architect leaving in 3 months | Medium | Critical | Mandatory documentation of all custom workarounds; knowledge transfer sessions twice weekly. |
| R-03 | Bus factor of 1 for DevOps | High | High | Document manual deployment steps; train Anouk Nakamura on Vercel/AWS infrastructure. |
| R-04 | CI Pipeline delay (45 mins) | High | Medium | Implement Turborepo and parallelize Jest tests. |
| R-05 | Firmware flash memory overflow | Medium | Medium | Implement string compression and remove unused debug symbols. |

### 8.1 Probability/Impact Matrix
*   **Critical:** High Probability + High Impact (R-01, R-03)
*   **High:** Medium Probability + High Impact (R-02)
*   **Moderate:** High Probability + Medium Impact (R-04)
*   **Low:** Medium Probability + Medium Impact (R-05)

---

## 9. TIMELINE AND MILESTONES

The project follows an iterative agile approach with hard deadlines for stakeholder demos.

### 9.1 Phases

**Phase 1: Foundation & Localization (Current $\to$ April 2026)**
*   **Focus:** Resolving the "Launch Blocker" (L10n/i18n).
*   **Dependencies:** Finalization of translation strings for 12 languages.
*   **Milestone 1:** Internal Alpha Release (Target: 2026-04-15).

**Phase 2: Integration & Stability (April 2026 $\to$ June 2026)**
*   **Focus:** Implementing the Webhook Framework and resolving API bugs with partners.
*   **Dependencies:** Documentation from integration partner.
*   **Milestone 2:** Stakeholder Demo and Sign-off (Target: 2026-06-15).

**Phase 3: Scale & Optimization (June 2026 $\to$ August 2026)**
*   **Focus:** Performance tuning, CI pipeline optimization, and benchmark testing.
*   **Dependencies:** Successful sign-off from Phase 2.
*   **Milestone 3:** Performance Benchmarks Met (Target: 2026-08-15).

### 9.2 Gantt-Style Dependency View
`[L10n Development] ----> [Alpha Release] ----> [Webhook Framework] ----> [Partner Integration] ----> [Demo/Sign-off] ----> [Perf Benchmarks]`

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Since the team does not keep formal notes, the following is a synthesis of critical decisions captured in Slack threads.*

### Meeting 1: Thread #dev-sync (Oct 12, 2023)
**Topic:** CI Pipeline Sluggishness
*   **Selin:** "The 45-minute CI wait is killing my velocity. I can't iterate on security patches if I have to wait an hour for a build."
*   **Xavi:** "Agreed. It's a bottleneck. Anouk, can we move the Prisma generation to a pre-build step?"
*   **Anouk:** "I'll look into it. I think we're running the same tests multiple times. I'll propose using Turborepo to cache the results."
*   **Decision:** Anouk to research Turborepo; prioritize CI optimization in the next sprint.

### Meeting 2: Thread #arch-discuss (Oct 19, 2023)
**Topic:** Architect Departure & Knowledge Transfer
*   **Xavi:** "As you all know, our lead architect is moving on in 3 months. We need to ensure we aren't left with a 'black box' in the firmware logic."
*   **Ines:** "Most of the weird workarounds for the Zigbee stack are only in his head. We need a living document."
*   **Selin:** "I can help document the security handshakes if he can walk me through the current implementation."
*   **Decision:** Weekly "Brain Dump" sessions scheduled every Thursday for the next 12 weeks.

### Meeting 3: Thread #product-roadmap (Oct 26, 2023)
**Topic:** Localization as a Blocker
*   **Xavi:** "We can't move to the 10k MAU goal if the dashboard is only in English. The European teams are refusing the beta."
*   **Ines:** "The firmware can handle it, but we need the JSON translation maps from the marketing team."
*   **Anouk:** "I'll set up `next-intl` on the frontend. We just need to agree on the 12 languages."
*   **Decision:** Localization is officially marked as a "Critical Launch Blocker." Development to start immediately.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Shoestring)

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $97,500 | Salary for team of 8 (blended rate), including Ines's contract fees. |
| **Infrastructure** | 15% | $22,500 | Vercel Pro, AWS RDS (PostgreSQL), AWS IoT Core, and Domain/SSL. |
| **Tools & Licenses** | 10% | $15,000 | GitHub Enterprise, Slack, Jira, and specialized firmware debugging tools. |
| **Contingency** | 10% | $15,000 | Reserved for emergency hardware replacements or external security consultants. |

**Budget Note:** Every dollar is under scrutiny. Xavi Costa (CTO) must approve any spend exceeding $500.

---

## 12. APPENDICES

### Appendix A: Firmware Communication Protocol
The Wayfinder firmware communicates using a binary-packed format over MQTT to minimize data usage over cellular backhauls.

**Packet Structure:**
`[Header: 2 bytes][DeviceID: 8 bytes][PayloadLength: 2 bytes][Payload: Variable][Checksum: 2 bytes]`

**Common Command Codes:**
*   `0x01`: Heartbeat (Device $\to$ Cloud)
*   `0x02`: Config Update (Cloud $\to$ Device)
*   `0x03`: Firmware Update Trigger (Cloud $\to$ Device)
*   `0x04`: Alert/Event (Device $\to$ Cloud)

### Appendix B: Success Metrics Detail
To achieve the success criteria, the following KPIs will be tracked:

**Metric 1: External Audit Pass (First Attempt)**
*   **Target:** 0 Critical vulnerabilities.
*   **Verification:** Third-party penetration test and compliance check against internal security standards.
*   **Key Focus:** JWT expiration, SQL injection prevention in Prisma queries, and MQTT TLS 1.3 encryption.

**Metric 2: 10,000 MAU within 6 Months**
*   **Target:** Linear growth of ~1,666 users per month post-launch.
*   **Verification:** Monthly active user count from the `AuditLog` and `User` tables.
*   **Technical Requirement:** Database must sustain 100 concurrent requests per second (RPS) with $<200\text{ms}$ latency.