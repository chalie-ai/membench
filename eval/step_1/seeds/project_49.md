Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Document (PSD). It serves as the "Single Source of Truth" (SSOT) for the Forge project at Oakmount Group.

***

# PROJECT SPECIFICATION: FORGE
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Company:** Oakmount Group  
**Industry:** Media and Entertainment  
**Classification:** Confidential / HIPAA Compliant  
**Last Updated:** 2024-05-22  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Forge" represents a strategic pivot for Oakmount Group. Historically, the company has operated in industrial logistics; Forge is a greenfield venture into the Media and Entertainment (M&E) sector. The objective is the development of an embedded systems firmware suite that bridges high-fidelity media capture hardware with cloud-based orchestration. Unlike previous Oakmount projects, Forge is designed to handle massive data throughputs required for real-time media processing while maintaining a strict security posture.

### 1.2 Business Justification
The M&E industry is currently experiencing a shift toward "Virtual Production" and "Edge-Rendered" content. There is a significant market gap for a firmware-to-cloud pipeline that allows creators to manage hardware assets remotely with low latency. By entering this market, Oakmount Group diversifies its revenue stream and leverages its existing expertise in hardware-software integration. 

The "greenfield" nature of this project allows the team to avoid the legacy constraints of the company’s logistics software. However, because Oakmount has never operated in M&E, the project carries a high risk regarding regulatory alignment and user expectation.

### 1.3 ROI Projection
The financial success of Forge is measured by the transition from milestone-based funding to recurring subscription revenue. 
- **Year 1 Investment:** Estimated at $2.4M (covering personnel, R&D, and prototype hardware).
- **Projected Year 2 Revenue:** $4.2M based on a target acquisition of 15 mid-sized production houses.
- **Projected Year 3 Revenue:** $12M as the product scales to enterprise-level studios.
- **Estimated ROI:** 250% over 36 months.
- **Cost Savings:** By utilizing a "simple monolith" architecture (Ruby on Rails), the company reduces operational overhead and DevOps headcount, saving approximately $180k/year in specialized infrastructure roles.

### 1.4 Strategic Alignment
Forge aligns with Oakmount’s "Innovation 2030" initiative, pushing the company toward high-margin software-as-a-service (SaaS) models. The integration of HIPAA-compliant data handling ensures that the system can be pivoted into medical imaging or high-security government media projects if the entertainment market fluctuates.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The "Simple Monolith" Philosophy
The Forge architecture deliberately eschews the complexity of microservices. To maintain a high-trust, low-ceremony development speed, the team has opted for a Ruby on Rails monolith. This allows for rapid iteration, shared business logic, and simplified deployment.

**Stack Components:**
- **Language:** Ruby 3.2.2
- **Framework:** Ruby on Rails 7.1 (Monolith)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres-compatible layer/RDS)
- **Hosting:** Heroku (for rapid scaling and deployment simplicity)
- **Encryption:** AES-256-GCM for data at rest; TLS 1.3 for data in transit.

### 2.2 System Architecture Diagram (ASCII)

```text
[ Embedded Hardware (Forge Devices) ] 
              |
              | (TLS 1.3 / MQTT / HTTPS)
              v
[ Heroku Load Balancer (ALB) ]
              |
              v
[ Rails Monolith Application ] <---- [ Feature Flag System ]
      |                |
      |                +-----> [ Redis Cache (Session/Rate Limiting) ]
      v                |
[ MySQL Database ] <---+-----> [ S3 Bucket (Reports/PDF/CSV) ]
      |
      +---- [ HIPAA Encryption Layer (KMS) ]
```

### 2.3 Module Boundaries
Despite being a monolith, Forge utilizes a "Modular Monolith" approach. Logic is separated into the following domain boundaries:
- `Forge::Billing`: Manages subscriptions and invoicing.
- `Forge::Collaboration`: Handles real-time socket connections and conflict resolution.
- `Forge::Reporting`: Manages PDF/CSV generation and scheduling.
- `Forge::Analytics`: Tracks API usage and performance metrics.
- `Forge::Identity`: Handles HIPAA-compliant user authentication and RBAC.

### 2.4 Security Architecture
Given the HIPAA compliance requirement:
- **Data Isolation:** All PII (Personally Identifiable Information) is stored in encrypted columns using the `lockbox` gem.
- **Audit Logs:** Every write action to the database is logged with a timestamp, user ID, and original value.
- **Network:** No public access to the database; all traffic flows through the Rails application layer.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Blocked | **Owner:** Bram Oduya
**Description:** A comprehensive system to handle tiered subscription plans (Basic, Pro, Studio) and automated monthly invoicing.

The billing module must integrate with a third-party provider (Stripe) to handle PCI-compliant credit card storage. The system will manage "seats" per organization, where an admin can add or remove users. When a user's subscription expires, the system must trigger a "Grace Period" state (14 days) before restricting API access.

**Functional Requirements:**
- Automatic generation of monthly PDF invoices.
- Pro-rated billing for mid-month plan upgrades.
- Webhook listeners to handle failed payments.
- Integration with the `Forge::Identity` module to lock accounts based on payment status.

**Technical Detail:** 
The system will use a `Subscriptions` table linked to `Organizations`. A background worker (Sidekiq) will run daily to check for expiring accounts and trigger renewal emails. Since this is currently **Blocked**, the team is awaiting a finalized pricing strategy from the executive board.

### 3.2 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low | **Status:** In Progress | **Owner:** Renzo Stein
**Description:** Allowing multiple engineers to configure the firmware parameters of a single hardware device simultaneously without overwriting each other's changes.

This feature utilizes WebSockets (ActionCable) to push real-time updates. The core challenge is "Operational Transformation" (OT) or "Conflict-free Replicated Data Types" (CRDTs). Given the nature of firmware configs (mostly key-value pairs), a "Last-Writer-Wins" strategy is being implemented for non-critical fields, while critical hardware offsets require a "Lock-and-Edit" mechanism.

**Functional Requirements:**
- Presence indicators (showing who is currently editing a device config).
- Real-time "diff" view of changes before they are committed to the device.
- Conflict resolution modal when two users save the same parameter within 500ms.

**Technical Detail:** 
The state is maintained in Redis to ensure sub-100ms latency for updates. When a user modifies a value, a `Patch` object is broadcast to all connected clients. The firmware on the device only accepts the "Finalized" commit to prevent unstable hardware states during editing.

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** Blocked | **Owner:** Bram Oduya
**Description:** A system for generating hardware health and usage reports, deliverable via email or downloadable via the dashboard.

Reports will aggregate data from the `UsageLogs` table, calculating uptime, error rates, and thermal performance of the embedded systems. Users can schedule these reports (Daily, Weekly, Monthly).

**Functional Requirements:**
- Custom template builder for PDF reports.
- CSV export for raw data analysis in Excel/Google Sheets.
- Scheduling engine using `sidekiq-scheduler`.
- S3 storage for generated reports with a 30-day TTL (Time-to-Live).

**Technical Detail:** 
Due to the heavy resource load of PDF generation (WickedPDF), these tasks are offloaded to a dedicated worker queue. The current **Blocked** status is due to the "Technical Debt" regarding date formats; generating a report with three different date formats (ISO8601, Epoch, and MM-DD-YYYY) is resulting in corrupted data visualization.

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** In Progress | **Owner:** Hana Nakamura
**Description:** Protection of the system from API abuse and a dashboard for users to track their own resource consumption.

The system implements a "Leaky Bucket" algorithm to limit requests per API key. Analytics will track the most used endpoints to inform future infrastructure scaling.

**Functional Requirements:**
- Dynamic rate limits based on the user's subscription tier (e.g., Basic: 100 req/min, Studio: 5000 req/min).
- `X-RateLimit-Remaining` headers in all API responses.
- Usage dashboard showing p95 latency and total request volume.

**Technical Detail:** 
Rate limiting is handled at the middleware level using `rack-attack`. Usage data is streamed into a `UsageAnalytics` table. To avoid slowing down the main request thread, analytics are written to Redis and flushed to MySQL in batches every 60 seconds.

### 3.5 A/B Testing Framework (Feature Flag System)
**Priority:** Low | **Status:** In Design | **Owner:** Nia Oduya
**Description:** A system to toggle features on/off for specific user groups to test new firmware configurations.

Rather than hard-coding "if/else" statements, the system will use a feature flag management layer. This allows the team to roll out a new firmware update to 5% of the user base before a full release.

**Functional Requirements:**
- Ability to target flags by `organization_id` or `user_role`.
- Integration with the A/B testing framework to track which group has better performance (lower latency).
- Admin UI to toggle flags in real-time without redeploying code.

**Technical Detail:** 
The design utilizes the `flipper` gem. Flags will be stored in MySQL to ensure consistency across the Heroku dynos. The design phase is focusing on how to synchronize these flags down to the embedded firmware, as the hardware needs to know which "feature set" it is currently running.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer` token for authentication and use `application/json`.

### 4.1 Device Management
**Endpoint:** `POST /api/v1/devices`  
**Description:** Registers a new embedded hardware unit to an organization.  
**Request:**
```json
{
  "serial_number": "FORGE-9920-X",
  "firmware_version": "0.8.1",
  "location_id": "STUDIO_A"
}
```
**Response:** `201 Created`
```json
{
  "id": "dev_8821",
  "status": "provisioning",
  "created_at": "2024-05-22T10:00:00Z"
}
```

**Endpoint:** `GET /api/v1/devices/:id/config`  
**Description:** Retrieves the current configuration parameters for a device.  
**Response:** `200 OK`
```json
{
  "id": "dev_8821",
  "parameters": {
    "sample_rate": 48000,
    "buffer_size": 512,
    "encryption_level": "high"
  }
}
```

### 4.2 Collaborative Editing
**Endpoint:** `PATCH /api/v1/devices/:id/config`  
**Description:** Updates specific parameters (used by the collaborative editor).  
**Request:**
```json
{
  "parameters": { "buffer_size": 1024 },
  "version_tag": "v12"
}
```
**Response:** `200 OK` or `409 Conflict` (if `version_tag` is outdated).

**Endpoint:** `GET /api/v1/collaboration/active_sessions`  
**Description:** Lists all devices currently being edited.  
**Response:** `200 OK`
```json
{
  "sessions": [
    { "device_id": "dev_8821", "users": ["user_1", "user_4"] }
  ]
}
```

### 4.3 Reporting & Analytics
**Endpoint:** `POST /api/v1/reports/generate`  
**Description:** Triggers an immediate PDF/CSV report generation.  
**Request:**
```json
{
  "type": "health_check",
  "format": "pdf",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```
**Response:** `202 Accepted` (Returns a job ID for polling).

**Endpoint:** `GET /api/v1/analytics/usage`  
**Description:** Fetches usage statistics for the current API key.  
**Response:** `200 OK`
```json
{
  "total_requests": 150400,
  "rate_limit_hit_count": 12,
  "p95_latency_ms": 188
}
```

### 4.4 Subscription & Billing
**Endpoint:** `GET /api/v1/billing/subscription`  
**Description:** Returns the current subscription tier and status.  
**Response:** `200 OK`
```json
{
  "plan": "Studio",
  "status": "active",
  "next_billing_date": "2024-06-01"
}
```

**Endpoint:** `POST /api/v1/billing/upgrade`  
**Description:** Upgrades the organization to a higher tier.  
**Request:**
```json
{ "new_plan_id": "plan_studio_enterprise" }
```
**Response:** `200 OK`.

---

## 5. DATABASE SCHEMA

The database uses a relational MySQL structure. All timestamps use `datetime(6)` for microsecond precision.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | `id` | - | `name`, `billing_email`, `industry_code` | Top-level tenant for billing. |
| `users` | `id` | `org_id` | `email`, `password_digest`, `role` | HIPAA-compliant user accounts. |
| `devices` | `id` | `org_id` | `serial_number`, `firmware_ver`, `status` | Tracks embedded hardware units. |
| `device_configs` | `id` | `device_id` | `config_json`, `version_tag`, `updated_at` | Versioned hardware settings. |
| `subscriptions` | `id` | `org_id` | `plan_type`, `start_date`, `end_date` | Manages payment tiers. |
| `usage_logs` | `id` | `device_id` | `endpoint_hit`, `response_time`, `timestamp` | Raw data for analytics/reports. |
| `audit_logs` | `id` | `user_id` | `action`, `resource_id`, `old_value`, `new_value` | HIPAA compliance requirement. |
| `feature_flags` | `id` | - | `flag_name`, `is_enabled`, `target_group` | Controls feature rollouts. |
| `reports` | `id` | `org_id` | `report_type`, `s3_url`, `generated_at` | Metadata for generated PDFs/CSVs. |
| `scheduled_tasks` | `id` | `org_id` | `cron_expression`, `task_type`, `last_run` | Scheduling for report delivery. |

### 5.2 Relationships
- **Organization $\rightarrow$ Users:** One-to-Many.
- **Organization $\rightarrow$ Devices:** One-to-Many.
- **Device $\rightarrow$ DeviceConfigs:** One-to-Many (History of changes).
- **User $\rightarrow$ AuditLogs:** One-to-Many.
- **Device $\rightarrow$ UsageLogs:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Forge utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (`dev`)
- **Purpose:** Active coding and feature branching.
- **Infrastructure:** Local Docker Compose environments and a shared Heroku `dev` app.
- **Data:** Mock data; no real PII.
- **Deployments:** Automatic on push to `develop` branch.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation and QA testing.
- **Infrastructure:** Heroku `staging` dynos. Mirror of production config.
- **Data:** Anonymized production snapshots.
- **Deployments:** Manual trigger after `dev` is cleared.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live client environment.
- **Infrastructure:** Heroku Performance-M dynos, High-Availability MySQL.
- **Data:** Encrypted HIPAA-compliant data.
- **Deployments:** Manual QA Gate $\rightarrow$ 2-day turnaround window.

### 6.2 The QA Gate Process
No code enters production without a manual sign-off from the dedicated QA engineer.
1. **Build:** Code is merged to `main` and deployed to Staging.
2. **Verification:** QA tests the specific feature tickets.
3. **Approval:** QA marks the build as "Green" in Slack.
4. **Deployment:** The Project Lead triggers the Heroku pipeline to Production.
5. **Observation:** 48-hour window to monitor p95 latency before the release is considered "stable."

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** RSpec
- **Coverage Target:** 80% of business logic.
- **Focus:** Validating individual methods, specifically in the `Forge::Identity` and `Forge::Billing` modules. Mocking is used for all external API calls (Stripe, S3).

### 7.2 Integration Testing
- **Tool:** Capybara / Selenium
- **Focus:** End-to-end flows, such as "User registers $\rightarrow$ Creates Organization $\rightarrow$ Adds Device."
- **API Testing:** Using `Postman` and `curl` scripts to verify that the API endpoints return the correct JSON schema and HTTP status codes.

### 7.3 End-to-End (E2E) Firmware Testing
- **Approach:** Hardware-in-the-Loop (HIL).
- **Process:** A physical "Forge" device is connected to a test harness. The Rails app sends a configuration change via API $\rightarrow$ The device applies the change $\rightarrow$ The test harness verifies the electrical output change.
- **Latency Testing:** Measuring the round-trip time from API call to hardware execution to ensure the p95 < 200ms requirement.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Regulatory requirements change (HIPAA/M&E) | High | High | Accept risk; monitor weekly via legal counsel. | Nia Oduya |
| **R-02** | Performance requirements 10x current capacity | Medium | Critical | Assign dedicated owner to optimize DB queries and Redis caching. | Bram Oduya |
| **R-03** | Data Processing Agreement (DPA) delay | High | Medium | Current Blocker: Escalated to Legal for priority review. | Nia Oduya |
| **R-04** | Technical Debt: Date format inconsistency | High | Medium | Implement a normalization layer (`Forge::DateTimeHelper`) before report launch. | Renzo Stein |
| **R-05** | Contractor availability (Renzo Stein) | Low | Medium | Maintain detailed documentation to allow for quick handoff. | Nia Oduya |

---

## 9. TIMELINE & MILESTONES

The project follows a milestone-based funding model. Each milestone must be signed off by the Oakmount Group board before the next funding tranche is released.

### 9.1 Phase 1: Foundation (Current - March 2026)
- **Focus:** Core monolith setup, HIPAA security implementation, and basic device connectivity.
- **Dependency:** Legal review of DPA.
- **Milestone 1:** Post-launch stability confirmed.
- **Target Date:** 2026-03-15.

### 9.2 Phase 2: Market Entry (March 2026 - May 2026)
- **Focus:** Billing integration, API rate limiting, and onboarding the first pilot customer.
- **Dependency:** Pricing strategy approval.
- **Milestone 2:** First paying customer onboarded.
- **Target Date:** 2026-05-15.

### 9.3 Phase 3: Feature Completion (May 2026 - July 2026)
- **Focus:** Collaborative editing, scheduled reporting, and A/B testing framework.
- **Dependency:** Resolution of date-format technical debt.
- **Milestone 3:** MVP feature-complete.
- **Target Date:** 2026-07-15.

---

## 10. MEETING NOTES

*Note: Per company culture, these meetings are recorded via Zoom. These notes are the distilled summaries of the recordings.*

### Meeting 1: Architecture Alignment (2024-01-10)
- **Attendees:** Nia, Bram, Hana, Renzo.
- **Discussion:** Debate between microservices vs. monolith. Bram argued that with a team of 6, microservices would create "operational hell." Hana raised concerns about security boundaries.
- **Decision:** Agreed on a Ruby on Rails monolith with strict module boundaries. This maintains the "high-trust, low-ceremony" dynamic.
- **Outcome:** Heroku selected for deployment to avoid managing Kubernetes clusters.

### Meeting 2: The "Date Format" Crisis (2024-03-05)
- **Attendees:** Nia, Bram, Renzo.
- **Discussion:** Renzo discovered that the firmware sends dates in Epoch, the Rails app uses ISO8601, and the legacy reporting tool expects MM-DD-YYYY. This is causing the PDF reports to fail.
- **Decision:** Do not attempt to migrate the entire database (too risky). Instead, build a normalization layer in the `Forge::Reporting` module.
- **Outcome:** Feature 3 (Reports) is officially moved to "Blocked" until the normalization layer is tested.

### Meeting 3: Performance Scaling Review (2024-04-12)
- **Attendees:** Nia, Bram, Hana.
- **Discussion:** The board increased the expected capacity requirements by 10x. Bram noted that the current MySQL instance will bottleneck. Nia confirmed there is no additional budget for a larger database cluster.
- **Decision:** Implement aggressive Redis caching for device configurations and offload analytics to a background queue. Bram is the dedicated owner for this.
- **Outcome:** p95 latency goal of 200ms remains the primary success metric.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the completion of the milestones defined in Section 9.

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,850,000 | Salaries for 5 FTEs and Contractor (Renzo). |
| **Infrastructure** | $220,000 | Heroku Performance Dynos, Managed MySQL, Redis. |
| **Tools & Licensing** | $45,000 | Stripe API, S3 Storage, GitHub Enterprise, Zoom. |
| **Security Audit** | $80,000 | Third-party HIPAA compliance certification. |
| **Contingency** | $205,000 | Reserve for unexpected hardware failures or legal fees. |
| **TOTAL** | **$2,400,000** | **Variable / Milestone-based funding.** |

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Checklist
To ensure the project meets the required security standards, the following must be verified before Milestone 1:
1. **Encryption at Rest:** All `user` and `device_config` tables must use the `lockbox` gem for column-level encryption.
2. **Encryption in Transit:** All endpoints must reject non-HTTPS requests.
3. **Access Control:** Implement a strict Role-Based Access Control (RBAC) system (Admin, Manager, Technician).
4. **Audit Trail:** All changes to the `device_configs` table must be mirrored in the `audit_logs` table.
5. **Automatic Logout:** Session timeouts must be set to 30 minutes of inactivity.

### Appendix B: Firmware-to-Cloud Handshake Protocol
The embedded systems use a specific handshake to authenticate with the Rails monolith:
1. **Handshake Init:** Device sends `POST /api/v1/handshake` with `serial_number` and a `challenge_nonce`.
2. **Server Response:** Server validates the serial number against the `devices` table and returns a signed JWT (JSON Web Token) with a 1-hour expiration.
3. **Authenticated Requests:** The device includes the JWT in the `Authorization: Bearer` header for all subsequent requests.
4. **Re-authentication:** If the server returns a `401 Unauthorized`, the device must repeat the handshake process.