# Project Specification: Project Keystone
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft for Engineering Review  
**Company:** Coral Reef Solutions  
**Project Lead:** Yara Liu (Engineering Manager)

---

## 1. Executive Summary

### 1.1 Overview
Project Keystone is a strategic SaaS platform developed by Coral Reef Solutions designed specifically for the education industry. The primary objective of Keystone is to serve as a high-reliability integration bridge and management layer that syncs critical educational data with a strategic external partner’s API. Unlike standard standalone SaaS products, Keystone is a "partnership integration" platform; its success is predicated on the seamless synchronization of student and institutional data between the Coral Reef ecosystem and the partner's external environment.

### 1.2 Business Justification
The education sector is currently fragmented, with institutional data residing in disparate silos. By building Keystone, Coral Reef Solutions positions itself as the central "keystone" (hence the name) that unlocks interoperability. The strategic partnership allows Coral Reef to enter a new market segment without building the core pedagogy tools from scratch, instead leveraging the partner's established toolset while providing the superior management, notification, and security wrapper that educational institutions demand.

The business value is driven by "stickiness." Once an institution integrates its data flow through Keystone, the cost of switching to a competitor increases significantly. Furthermore, the ability to provide SOC 2 Type II compliant data handling gives Coral Reef a competitive advantage over smaller, less secure educational startups.

### 1.3 ROI Projection
The project is backed by a budget of $1.5M. The projected Return on Investment (ROI) is calculated based on a three-year horizon:
- **Year 1 (Development & Launch):** Expected net loss due to CAPEX.
- **Year 2 (Growth):** Projected revenue of $2.2M through tiered subscription models (Institutional, Enterprise, and District levels).
- **Year 3 (Scale):** Projected revenue of $4.8M as the partnership expands to more regions.

**Key ROI Drivers:**
1. **Reduction in Churn:** Expected 15% increase in customer retention due to the integrated ecosystem.
2. **Market Expansion:** Access to the partner's existing client base of 500+ schools.
3. **Operational Efficiency:** Automation of data syncing reduces manual onboarding time from 4 weeks to 48 hours.

### 1.4 Strategic Alignment
Keystone aligns with Coral Reef Solutions' goal of becoming the industry leader in educational infrastructure. By prioritizing security (SOC 2) and a robust notification system, the platform ensures that administrators and students receive critical updates in real-time, solving a primary pain point in the current market.

---

## 2. Technical Architecture

### 2.1 System Overview
Keystone is designed as a **Clean Monolith**. While the industry trend leans toward microservices, the small team size (4 members) necessitates a monolith to minimize operational overhead and network latency. However, the monolith is structured with strict module boundaries to allow for future extraction into services if the scale warrants it.

**The Stack:**
- **Language:** Python 3.11
- **Framework:** Django 4.2 (utilizing Django Rest Framework for APIs)
- **Primary Database:** PostgreSQL 15 (Relational data, ACID compliance)
- **Caching/Queueing:** Redis 7.0 (used for Celery task queuing and session caching)
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless container execution.
- **CI/CD:** GitHub Actions triggering deployments to AWS.

### 2.2 Architecture Diagram Description (ASCII)
The following represents the request flow from the end-user to the external partner API.

```text
[ User Browser/App ] 
       |
       v (HTTPS/TLS 1.3)
[ AWS Application Load Balancer ]
       |
       v
[ AWS ECS Cluster (Django Monolith) ] <---> [ Redis Cache/Queue ]
       |                                          |
       |--- [ Module: Auth/Security ]             |--- [ Celery Worker ]
       |--- [ Module: Notification Engine ] <------|           |
       |--- [ Module: Data Sync Manager ] <-------------------|
       |--- [ Module: Dashboard/Analytics ]                   |
       |                                                       v
       |                                            [ External Partner API ]
       v                                            (Integration Point)
[ PostgreSQL Database ]
(User Profiles, Audit Logs,
 Sync State, Configurations)
```

### 2.3 Module Boundaries
To prevent the "big ball of mud" pattern, the project enforces the following boundaries:
- **`keystone.core`**: Shared utilities, base models, and configuration.
- **`keystone.auth`**: MFA, session management, and SOC 2 audit logging.
- **`keystone.notifications`**: Logic for dispatching across four channels.
- **`keystone.integration`**: The "Anti-Corruption Layer" (ACL) that handles the buggy external API.
- **`keystone.dashboard`**: Widget definitions and user preference storage.

### 2.4 Deployment Strategy: The Weekly Release Train
Keystone adheres to a strict **Weekly Release Train**. 
- **Cut-off:** Wednesday 12:00 PM UTC.
- **Deployment:** Thursday 02:00 AM UTC.
- **Rule:** No hotfixes are permitted outside this window unless a "Severity 1" (Total System Outage) is declared by Yara Liu. All features, regardless of "readiness," are merged into the release branch; if a feature is incomplete, it is hidden behind a **Feature Flag**.

---

## 3. Detailed Feature Specifications

### 3.1 Notification System
**Priority:** High | **Status:** In Review
**Description:** A multi-channel communication engine that alerts users of critical educational events, sync failures, and system updates.

**Detailed Requirements:**
- **Omnichannel Delivery:** The system must support four distinct channels:
    1. **Email:** Integration via SendGrid for transactional and marketing emails.
    2. **SMS:** Integration via Twilio for high-urgency alerts.
    3. **In-App:** A real-time notification bell using WebSockets (Django Channels).
    4. **Push:** Firebase Cloud Messaging (FCM) for mobile device alerts.
- **Preference Center:** Users must be able to toggle specific notification types (e.g., "Sync Alerts") on or off per channel.
- **Template Engine:** Use of Jinja2 templates to allow the marketing team to update notification copy without developer intervention.
- **Retry Logic:** Implement an exponential backoff strategy using Celery for failed delivery attempts (Max 3 retries).
- **Audit Trail:** Every notification sent must be logged in the `NotificationLog` table for SOC 2 compliance.

**Acceptance Criteria:**
- A user can opt-out of SMS but remain opted-in for Email.
- Notifications are delivered within 30 seconds of the triggering event.
- The system handles a burst of 10,000 notifications without crashing the API.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low | **Status:** In Progress
**Description:** A user-centric landing page where educational administrators can configure their view of institutional data.

**Detailed Requirements:**
- **Widget Library:** A set of pre-defined widgets (e.g., "Student Enrollment Graph," "Sync Status Indicator," "Recent Alerts").
- **Grid Layout:** Implementation of a CSS Grid or React-Grid-Layout system allowing users to resize and move widgets.
- **State Persistence:** Widget positions, sizes, and visibility must be saved to the database via a JSONB field in the `UserProfile` table.
- **Dynamic Data Fetching:** Each widget should call a specific API endpoint independently, preventing a single slow widget from blocking the entire page load.
- **Customization Options:** Users can rename widgets and set refresh intervals (e.g., every 5 minutes or on page load).

**Acceptance Criteria:**
- Users can move a widget from the left column to the right column, and the position is saved upon refresh.
- Adding a new widget does not require a page reload.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** Blocked
**Description:** A system to protect the platform from abuse and provide transparency on how the external partner API is being utilized.

**Detailed Requirements:**
- **Throttling:** Implementation of a "Leaky Bucket" algorithm. Limits will be set based on the user's subscription tier (e.g., 1,000 requests/hour for Basic, 10,000 for Enterprise).
- **Header Reporting:** Every API response must include headers indicating remaining quota (`X-RateLimit-Remaining`) and reset time (`X-RateLimit-Reset`).
- **Usage Dashboard:** An admin view showing the top 10 most active API keys and a time-series graph of total requests.
- **Alerting:** Trigger a notification to the system administrator when a user hits 90% of their monthly quota.
- **Backend Store:** Use Redis for atomic incrementing of request counts to ensure low-latency rate checking.

**Acceptance Criteria:**
- A request exceeding the limit returns a `429 Too Many Requests` status code.
- Analytics are updated in near real-time (within 60 seconds).

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** In Design
**Description:** A tool to allow institutions to migrate data from legacy CSV/XML/JSON files into the Keystone ecosystem.

**Detailed Requirements:**
- **Format Detection:** The system must analyze the first 1KB of an uploaded file to determine if it is CSV, JSON, or XML.
- **Schema Mapping:** A UI tool that allows users to map "Source Columns" (e.g., `st_name`) to "Keystone Fields" (e.g., `student_full_name`).
- **Asynchronous Processing:** Large files (>10MB) must be processed in the background via Celery to avoid HTTP timeouts.
- **Validation Phase:** A pre-import check that identifies formatting errors (e.g., invalid email formats) and provides a downloadable "Error Report" before the final commit.
- **Export Functionality:** Ability to export filtered datasets into the same three formats.

**Acceptance Criteria:**
- Successfully imports a 50,000-row CSV file without timing out the browser.
- Correctly identifies a JSON file even if the extension is missing.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Not Started
**Description:** A high-security authentication layer required for SOC 2 compliance, moving beyond simple passwords.

**Detailed Requirements:**
- **Time-based One-Time Password (TOTP):** Support for Google Authenticator and Authy via QR code generation.
- **WebAuthn/FIDO2 Support:** Integration for hardware keys (Yubico, Google Titan) to allow passwordless or second-factor biometric/physical login.
- **Recovery Codes:** Generation of ten one-time-use recovery codes upon 2FA activation.
- **Grace Periods:** A 24-hour window where a user can set up 2FA after a mandatory policy change before being locked out.
- **Session Hardening:** 2FA verification must be required for "privileged actions" (e.g., changing the API sync endpoint or deleting institutional data).

**Acceptance Criteria:**
- User cannot access the dashboard without a valid 2FA token if enabled.
- Hardware keys are successfully recognized via the browser's WebAuthn API.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 Authentication & User Management

#### `POST /auth/login`
- **Description:** Authenticates user and returns a JWT.
- **Request Body:** `{"username": "string", "password": "string"}`
- **Response (200 OK):** `{"token": "eyJ...", "expires_at": "2023-10-24T12:00:00Z"}`
- **Response (401 Unauthorized):** `{"error": "Invalid credentials"}`

#### `POST /auth/2fa/verify`
- **Description:** Verifies the second factor code.
- **Request Body:** `{"token": "temp_token", "code": "123456"}`
- **Response (200 OK):** `{"token": "final_jwt_token"}`

### 4.2 Notification System

#### `GET /notifications/`
- **Description:** Retrieves a list of in-app notifications for the current user.
- **Query Params:** `?unread_only=true`
- **Response (200 OK):** `[{"id": 101, "message": "Sync completed", "read": false, "timestamp": "..."}]`

#### `PATCH /notifications/{id}/`
- **Description:** Marks a notification as read.
- **Request Body:** `{"read": true}`
- **Response (200 OK):** `{"id": 101, "status": "read"}`

### 4.3 Integration & Sync

#### `POST /sync/trigger/`
- **Description:** Manually triggers a data sync with the external partner API.
- **Request Body:** `{"scope": "all" | "incremental", "force": boolean}`
- **Response (202 Accepted):** `{"job_id": "celery-task-id", "status": "queued"}`

#### `GET /sync/status/{job_id}/`
- **Description:** Polls the status of a specific sync job.
- **Response (200 OK):** `{"job_id": "...", "progress": 75, "status": "processing"}`

### 4.4 Dashboard & Config

#### `GET /dashboard/widgets/`
- **Description:** Retrieves the current layout and configuration of user widgets.
- **Response (200 OK):** `[{"widget_id": "enrollment_graph", "x": 0, "y": 0, "w": 6, "h": 4}]`

#### `PUT /dashboard/widgets/`
- **Description:** Updates the layout of the dashboard.
- **Request Body:** `[{"widget_id": "enrollment_graph", "x": 2, "y": 0, "w": 6, "h": 4}]`
- **Response (200 OK):** `{"message": "Layout saved successfully"}`

---

## 5. Database Schema

The system uses **PostgreSQL 15**. All tables use `UUID` for primary keys to prevent ID enumeration attacks.

### 5.1 Table Definitions

1.  **`Users`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `password_hash` (String)
    - `is_mfa_enabled` (Boolean)
    - `created_at` (Timestamp)

2.  **`UserProfiles`**
    - `user_id` (UUID, FK -> Users.id)
    - `full_name` (String)
    - `institution_id` (UUID, FK -> Institutions.id)
    - `dashboard_config` (JSONB) - *Stores widget positions and sizes*

3.  **`Institutions`**
    - `id` (UUID, PK)
    - `org_name` (String)
    - `partner_api_key` (Encrypted String)
    - `sync_interval` (Integer) - *Minutes*

4.  **`NotificationSettings`**
    - `user_id` (UUID, FK -> Users.id)
    - `channel_email` (Boolean)
    - `channel_sms` (Boolean)
    - `channel_push` (Boolean)
    - `channel_inapp` (Boolean)

5.  **`NotificationLogs`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK)
    - `channel` (Enum: email, sms, push, inapp)
    - `message_body` (Text)
    - `sent_at` (Timestamp)
    - `status` (Enum: delivered, failed, pending)

6.  **`SyncJobs`**
    - `id` (UUID, PK)
    - `institution_id` (UUID, FK)
    - `started_at` (Timestamp)
    - `completed_at` (Timestamp)
    - `records_processed` (Integer)
    - `status` (Enum: queued, running, completed, failed)

7.  **`SyncErrors`**
    - `id` (UUID, PK)
    - `job_id` (UUID, FK -> SyncJobs.id)
    - `error_payload` (JSONB)
    - `resolved` (Boolean)

8.  **`MFA_Devices`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK)
    - `device_type` (Enum: totp, webauthn)
    - `secret_key` (Encrypted String)
    - `public_key` (Text) - *For WebAuthn*

9.  **`API_Quotas`**
    - `user_id` (UUID, FK)
    - `request_count` (Integer)
    - `reset_date` (Timestamp)
    - `tier` (String)

10. **`AuditLogs`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK)
    - `action` (String)
    - `ip_address` (Inet)
    - `timestamp` (Timestamp)
    - `resource_affected` (String)

### 5.2 Relationships
- **Users $\to$ UserProfiles:** 1:1
- **Institutions $\to$ UserProfiles:** 1:Many (One institution has many users)
- **Users $\to$ NotificationLogs:** 1:Many
- **SyncJobs $\to$ SyncErrors:** 1:Many
- **Users $\to$ MFA_Devices:** 1:Many (Allows multiple hardware keys)

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Keystone utilizes three distinct AWS environments to ensure stability and security.

#### Development (Dev)
- **Purpose:** Sandbox for engineers to test new features.
- **Deployment:** Triggered by merges to the `develop` branch.
- **Infrastructure:** Smallest ECS instance size, local PostgreSQL instance for some devs, shared RDS for integration.
- **Data:** Anonymized seed data.

#### Staging (Staging)
- **Purpose:** Pre-production validation and QA. Mirror of Production.
- **Deployment:** Triggered by merges to the `release` branch.
- **Infrastructure:** Identical to Production but scaled down (e.g., 2 tasks instead of 10).
- **Data:** A sanitized snapshot of Production data (PII scrubbed).

#### Production (Prod)
- **Purpose:** Live user environment.
- **Deployment:** The "Weekly Release Train" (Thursdays 02:00 UTC).
- **Infrastructure:**
    - **Compute:** AWS ECS Fargate (Auto-scaling enabled).
    - **Database:** AWS RDS PostgreSQL (Multi-AZ for high availability).
    - **Cache:** AWS ElastiCache for Redis.
    - **Storage:** S3 for import/export file uploads.

### 6.2 SOC 2 Compliance Requirements
To meet SOC 2 Type II, the following infrastructure controls are implemented:
1. **Encryption at Rest:** All RDS and S3 volumes encrypted using AWS KMS.
2. **Encryption in Transit:** TLS 1.3 enforced for all API endpoints.
3. **VPC Isolation:** The database and Redis cache are in private subnets, accessible only via the ECS task security group.
4. **IAM Roles:** Least-privilege access; no engineer has direct "root" access to Production.
5. **Audit Logging:** CloudTrail enabled for all AWS API calls.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Coverage Goal:** 80% minimum.
- **Scope:** Business logic in `services.py` and utility functions. Mocking is used for all external API calls to the partner's system to avoid dependency on their uptime.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between the Django app, PostgreSQL, and Redis.
- **Approach:** Using a dedicated Docker Compose environment that spins up a temporary database and Redis instance for every test suite run.
- **Focus:** Ensuring the `SyncManager` correctly handles the state transitions in the `SyncJobs` table.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scope:** Critical user paths (e.g., Login $\to$ 2FA $\to$ Trigger Sync $\to$ Check Notification).
- **Frequency:** Run on every merge request to the `release` branch.

### 7.4 External API Mocking (The "Partner Simulator")
Because the partner's API is documented as "buggy and undocumented," the team has built a **Partner Simulator** (a small Flask app). This simulator mimics the partner's known buggy behaviors (e.g., random 500 errors, slow responses, incorrect JSON formats) to ensure Keystone's error handling is resilient.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Partner API is undocumented/buggy | High | High | Build a "Partner Simulator" for testing; negotiate timeline extension if breaking changes occur. |
| R-02 | Budget cut of 30% next quarter | Medium | Medium | Maintain a "Priority List." De-scope Low-priority features (Dashboard, Analytics, Import/Export) if budget is cut. |
| R-03 | SOC 2 Audit failure | Low | Critical | Engage a 3rd party compliance consultant early; implement automated audit logging. |
| R-04 | Technical Debt (Hardcoded values) | High | Medium | Allocate 10% of every release train to "Cleanup" tickets to remove hardcoded config. |
| R-05 | Deployment Train Delay | Medium | Low | Use Feature Flags to merge incomplete code without impacting the user experience. |

**Probability/Impact Matrix:**
- **High/High:** Immediate priority, requires weekly monitoring.
- **Medium/Medium:** Monitored during sprint planning.
- **Low/Critical:** Preventative measures in place.

---

## 9. Timeline

The project follows a phased approach leading up to the 2025 production launch.

### Phase 1: Foundation & Core Sync (Oct 2023 - June 2024)
- **Focus:** Setting up AWS ECS, PostgreSQL, and the basic API integration.
- **Dependencies:** Partner API access keys.
- **Goal:** A working sync between Coral Reef and the Partner.

### Phase 2: Security & Notifications (July 2024 - August 2025)
- **Focus:** Developing 2FA (WebAuthn) and the multi-channel notification engine.
- **Milestone:** **Production Launch (2025-08-15)**.
- **Dependency:** Finalization of notification provider contracts (Twilio/SendGrid).

### Phase 3: Compliance & Audit (August 2025 - October 2025)
- **Focus:** Hardening the system, finalizing audit logs, and external audit review.
- **Milestone:** **Security Audit Passed (2025-10-15)**.

### Phase 4: Optimization & Stability (October 2025 - December 2025)
- **Focus:** Fixing "edge case" bugs, optimizing SQL queries, and implementing the low-priority dashboard/analytics.
- **Milestone:** **Post-launch Stability Confirmed (2025-12-15)**.

---

## 10. Meeting Notes

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Yara Liu, Veda Fischer, Tomas Liu, Ingrid Kim  
**Minutes:**
- Discussion on whether to use Microservices. Veda argued that for a team of 4, the overhead of K8s and service discovery is too high.
- **Decision:** Proceed with a "Clean Monolith" on ECS Fargate.
- Tomas raised concerns about the "buggy API" impacting the UX.
- **Decision:** Implement an Anti-Corruption Layer (ACL) to sanitize partner data before it hits the core logic.
- **Action Items:**
    - Veda: Define the PostgreSQL schema draft. (Owner: Veda)
    - Yara: Draft the SOC 2 checklist. (Owner: Yara)

### Meeting 2: Notification Priority Review
**Date:** 2023-12-15  
**Attendees:** Yara Liu, Veda Fischer, Ingrid Kim  
**Minutes:**
- Review of the notification channels. Ingrid suggested adding Slack integration, but Yara rejected it as "scope creep" for the MVP.
- Discussion on SMS costs. Budget is sufficient, but we need a cap on messages per user.
- **Decision:** Notification system is Priority: High. SMS/Email must be functional before the 2FA system is finalized.
- **Action Items:**
    - Ingrid: Research SendGrid vs. Mailgun. (Owner: Ingrid)
    - Veda: Create the `NotificationLog` table. (Owner: Veda)

### Meeting 3: Budget & Blockers Sync
**Date:** 2024-01-10  
**Attendees:** Yara Liu, Veda Fischer, Tomas Liu  
**Minutes:**
- **Current Blocker:** The request for the "Enterprise Monitoring Tool" ($12k/yr) is still pending approval from finance.
- Yara noted that the hardcoded config values (40+ files) are becoming a bottleneck for the Dev environment setup.
- **Decision:** Dedicate the next release train (Jan 18) specifically to "Config Migration" (moving values to AWS Secrets Manager).
- Discussion on Risk R-02 (30% budget cut). Yara warned the team that the "Customizable Dashboard" may be cut if the budget is reduced.
- **Action Items:**
    - Yara: Follow up with Finance on the tool purchase. (Owner: Yara)
    - Veda: Map all hardcoded values to a `.env` template. (Owner: Veda)

---

## 11. Budget Breakdown

The total budget is **$1,500,000**.

### 11.1 Personnel ($950,000)
- **Engineering Manager (Yara):** $180k/yr $\times$ 2 years = $360k
- **Senior Backend (Veda):** $160k/yr $\times$ 2 years = $320k
- **UX Researcher (Tomas):** $120k/yr $\times$ 2 years = $240k
- **Contractor (Ingrid):** $30k/mo (part-time) for 1 year = $30k (adj. for specific project phase)
- *Note: Total personnel costs are staggered across the project duration.*

### 11.2 Infrastructure ($220,000)
- **AWS ECS/Fargate:** $5,000/mo $\times$ 24 months = $120k
- **AWS RDS/ElastiCache:** $3,000/mo $\times$ 24 months = $72k
- **S3/CloudFront/Networking:** $1,166/mo $\times$ 24 months = $28k

### 11.3 Tools & Compliance ($180,000)
- **SOC 2 Audit & Certification:** $60k (One-time fee + annual maintenance)
- **Monitoring Tools (New Purchase Pending):** $12k/yr $\times$ 2 years = $24k
- **Twilio/SendGrid/FCM:** $30k (Estimated usage)
- **Security Scanning Tools (Snyk/Checkmarx):** $66k

### 11.4 Contingency ($150,000)
- Reserved for emergency scaling, unexpected API changes, or additional contractor support.

---

## 12. Appendices

### Appendix A: Hardcoded Configuration Map
The following is a partial list of the 40+ files containing hardcoded values that must be migrated to AWS Secrets Manager:
- `settings.py`: API keys for SendGrid, Twilio.
- `sync_manager.py`: Partner API base URL.
- `auth_utils.py`: JWT secret key.
- `notifications/sms_provider.py`: Twilio Account SID.
- `integration/partner_client.py`: Timeout values and retry limits.
- (35+ other files across `core`, `auth`, and `integration` modules).

### Appendix B: Partner API "Bug" Catalog
To facilitate the development of the Partner Simulator, the following known issues have been documented:
1. **The "Ghost" 404:** The API occasionally returns a 404 for a record that exists, but resolves on the second attempt.
2. **The JSON Leak:** The API sometimes returns HTML (a 500 error page) with a `Content-Type: application/json` header.
3. **The Date Format Shift:** The API inconsistently switches between ISO 8601 and Unix timestamps depending on the endpoint.
4. **The Rate Limit Silence:** Instead of returning 429, the API sometimes simply drops the connection (TCP Reset).