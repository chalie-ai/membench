# PROJECT SPECIFICATION DOCUMENT: PROJECT UMBRA
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Company:** Iron Bay Technologies  
**Confidentiality Level:** High (PCI DSS Level 1)

---

## 1. EXECUTIVE SUMMARY

Project Umbra represents a critical strategic evolution for Iron Bay Technologies. Originally conceived during a corporate hackathon as a proof-of-concept for automated hardware orchestration within the media and entertainment sector, Umbra has organically grown into an internal productivity tool currently supporting 500 daily active users (DAU). The objective of the current initiative is to transition Umbra from a fragile internal utility into a robust, scalable IoT device network capable of supporting enterprise-grade workloads and external client pilots.

**Business Justification**
In the media and entertainment industry, the cost of downtime for hardware (cameras, lighting rigs, server racks, and signal processors) is measured in thousands of dollars per minute. Current manual orchestration is prone to human error and inefficiency. Umbra provides a centralized control plane for these IoT devices, allowing for remote configuration, health monitoring, and automated deployment of device settings. By digitizing the hardware layer, Iron Bay Technologies reduces manual labor costs for on-site technicians by an estimated 40% and accelerates production setup times by 60%.

**ROI Projection**
With a total budget allocation exceeding $5,000,000, the project is viewed as a flagship initiative with direct reporting lines to the board. The projected ROI is calculated based on three primary levers:
1. **Operational Efficiency:** Reduction in on-site engineering hours. Expected savings of $1.2M annually across 10 major production hubs.
2. **Error Reduction:** Minimizing hardware misconfigurations that lead to production delays. Projected risk mitigation value of $800K per annum.
3. **Market Expansion:** Transitioning from an internal tool to a licensed product. The external beta (Milestone 3) is designed to validate a SaaS pricing model targeting a Total Addressable Market (TAM) of $25M within the entertainment sector.

The projected break-even point is Q4 2027, with an expected Net Present Value (NPV) of $3.2M over five years. Given the direct processing of credit card data for premium hardware subscriptions, the project adheres to PCI DSS Level 1 compliance, ensuring the highest security standard to protect revenue streams and corporate reputation.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Umbra utilizes a "Pragmatic Monolith" approach. The stack is intentionally simple to allow a small team (3-4 people) to maintain high velocity. 

- **Framework:** Ruby on Rails 7.1 (Monolith)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons)
- **Hosting:** Heroku Private Spaces (to meet PCI compliance requirements)
- **Language:** Ruby 3.2

The system is currently a modular monolith. To prevent the "Big Ball of Mud" syndrome, business logic is separated into domains (Billing, Device Management, Analytics). We are transitioning to microservices incrementally, starting with the most resource-intensive components (Report Generation and Notification Dispatch).

### 2.2 System Diagram Description (ASCII)
The following describes the data flow from the IoT device to the user dashboard.

```text
[IoT Devices] ----(MQTT/HTTPS)----> [Heroku Load Balancer]
                                          |
                                          v
                            [Rails Application Server] <---> [Redis Cache]
                                          |
          ________________________________|________________________________
         |                |               |                |               |
  [Auth Service]   [Device Manager]  [Billing Engine]  [Report Engine]  [Notification]
         |                |               |                |               |
         |________________|_______________|________________|_______________|
                                          |
                                          v
                                   [MySQL Database] <---> [S3 File Storage]
                                          |
                                   [PCI Vault/Token]
```

**Diagram Logic:**
1. **Edge Layer:** IoT devices communicate via secure HTTPS endpoints or MQTT brokers.
2. **Application Layer:** The Rails monolith handles request routing, authentication, and business logic.
3. **State Layer:** MySQL manages relational data; Redis manages session state and rate-limiting counters.
4. **Compliance Layer:** Credit card data never touches the main MySQL database in plain text; it is routed to a PCI-compliant vault.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/I18n)
**Priority:** Critical | **Status:** Complete | **Version:** v1.0.0

**Description:**
To support global media production hubs, Umbra must be usable by technicians in multiple regions. This feature involves the implementation of a comprehensive translation framework across the entire UI and API.

**Technical Specification:**
- **Framework:** Implementation of the `i18n` Ruby gem.
- **Scope:** 12 supported languages: English (US/UK), Spanish, French, German, Japanese, Mandarin (Simplified), Korean, Portuguese, Italian, Arabic, Russian, and Hindi.
- **Storage:** Translation strings are stored in `.yml` files within the `config/locales` directory.
- **Detection:** The system detects the user's language preference based on:
    1. User profile setting (Highest priority).
    2. `Accept-Language` HTTP header.
    3. Browser default.
- **UI Adjustments:** Implementation of Right-to-Left (RTL) support for Arabic, requiring a separate CSS mirror file (`umbra-rtl.css`).

**Validation:** All 12 languages have been audited by native speakers and the "Language Switcher" component is integrated into the global navigation bar.

### 3.2 PDF/CSV Report Generation and Scheduled Delivery
**Priority:** High | **Status:** Complete | **Version:** v1.1.0

**Description:**
Executive stakeholders require periodic audits of device uptime and energy consumption. This feature allows users to generate snapshots of their network health in portable formats.

**Technical Specification:**
- **PDF Generation:** Utilizes the `WickedPDF` and `wkhtmltopdf` binaries. Reports are rendered from HTML templates to ensure visual consistency.
- **CSV Generation:** Uses the standard Ruby `CSV` library for high-performance data dumping of large device logs.
- **Scheduling Engine:** A customized Sidekiq-Scheduler implementation. Users can define cron-like intervals (e.g., "Every Monday at 8:00 AM").
- **Delivery Pipeline:**
    - Reports are generated in a background worker.
    - Files are uploaded to an encrypted AWS S3 bucket with a 7-day Time-To-Live (TTL).
    - A signed URL is emailed to the user.
- **Data Scope:** Reports include Device Heartbeat logs, Error Rate percentages, and User Activity summaries.

**Validation:** Successfully tested with reports containing up to 50,000 rows of CSV data without timing out the Heroku dyno.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** In Design | **Version:** v1.2.0 (Proposed)

**Description:**
To prevent API abuse and provide a basis for tiered pricing, Umbra requires a sophisticated rate-limiting mechanism and a way to track endpoint usage.

**Technical Specification:**
- **Algorithm:** Fixed-window counter using Redis.
- **Tiers:**
    - *Free/Internal:* 1,000 requests/hour.
    - *Pilot:* 10,000 requests/hour.
    - *Enterprise:* 100,000 requests/hour.
- **Implementation:** A custom Rails middleware that intercepts requests before they hit the controller. If the limit is exceeded, the server returns a `429 Too Many Requests` response.
- **Analytics Pipeline:**
    - Every request is logged to a `request_logs` table in MySQL.
    - A background job aggregates these logs hourly into a `daily_usage_stats` table to keep the primary log table from bloating.
- **Headers:** The API will return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Validation:** Success will be measured by the ability to throttle a simulated DDoS attack without impacting legitimate user traffic.

### 3.4 Notification System (Email, SMS, In-App, Push)
**Priority:** High | **Status:** In Design | **Version:** v1.3.0 (Proposed)

**Description:**
The system must alert technicians immediately when a device goes offline or a critical error occurs.

**Technical Specification:**
- **Dispatcher:** A centralized `NotificationDispatcher` service that determines the optimal channel based on the alert's severity.
- **Channels:**
    - **Email:** Powered by SendGrid. Used for weekly reports and account changes.
    - **SMS:** Powered by Twilio. Used for "Critical" priority alerts (e.g., Device Offline).
    - **In-App:** A WebSocket-based notification bell using ActionCable.
    - **Push:** Integration with Firebase Cloud Messaging (FCM) for mobile alerts.
- **User Preferences:** A matrix in the database allowing users to toggle specific notification types per channel (e.g., "Email: Yes, SMS: No" for "Low Battery" alerts).
- **Queueing:** All notifications are processed via Sidekiq to prevent blocking the main request-response cycle.

**Validation:** Low-latency delivery (under 5 seconds for SMS/Push) is required for critical alerts.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** In Review | **Version:** v1.4.0 (Proposed)

**Description:**
Given the PCI DSS Level 1 requirement and the sensitivity of the IoT network, standard passwords are insufficient. This feature implements multi-factor authentication.

**Technical Specification:**
- **TOTP Implementation:** Integration of the `rotp` gem for time-based one-time passwords (Google Authenticator/Authy).
- **Hardware Keys:** WebAuthn API integration to support FIDO2 keys (YubiKey).
- **Enrollment Flow:** 
    - User enables 2FA in settings.
    - System generates a QR code for TOTP or prompts for a hardware key touch.
    - System generates 10 one-time recovery codes.
- **Enforcement:** 2FA is mandatory for all users with `admin` or `billing_manager` roles.
- **Security:** Secret keys for TOTP are encrypted at rest using AES-256-GCM.

**Validation:** Penetration testing must confirm that 2FA cannot be bypassed via session hijacking or API manipulation.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require an `Authorization: Bearer <token>` header.

### 4.1 Device Management
**Endpoint:** `GET /devices`
- **Description:** List all registered IoT devices.
- **Request Parameters:** `filter[status]=online`, `page=1`, `per_page=20`
- **Response Example:**
```json
{
  "data": [
    { "id": "dev_9921", "name": "Camera-01", "status": "online", "last_seen": "2023-10-24T10:00:00Z" }
  ],
  "meta": { "total_count": 450, "current_page": 1 }
}
```

**Endpoint:** `POST /devices/{id}/reboot`
- **Description:** Trigger a remote reboot of a specific device.
- **Request Body:** `{ "force": true, "delay": 0 }`
- **Response Example:**
```json
{ "status": "success", "message": "Reboot signal sent to dev_9921" }
```

### 4.2 Reporting & Analytics
**Endpoint:** `POST /reports/generate`
- **Description:** Trigger an on-demand report.
- **Request Body:** `{ "type": "uptime", "format": "pdf", "start_date": "2023-01-01", "end_date": "2023-01-31" }`
- **Response Example:**
```json
{ "job_id": "job_abc123", "status": "processing", "eta": "30 seconds" }
```

**Endpoint:** `GET /reports/download/{job_id}`
- **Description:** Retrieve a generated report.
- **Response:** Redirects to a signed S3 URL.

### 4.3 Billing & Account (PCI Compliant)
**Endpoint:** `POST /billing/payment-method`
- **Description:** Update credit card details (tokens only).
- **Request Body:** `{ "payment_token": "tok_visa_12345" }`
- **Response Example:**
```json
{ "status": "updated", "last_four": "4242" }
```

**Endpoint:** `GET /billing/usage`
- **Description:** Get current month's API consumption.
- **Response Example:**
```json
{ "current_usage": 4500, "limit": 10000, "percentage": "45%" }
```

### 4.4 User & Security
**Endpoint:** `POST /auth/2fa/enable`
- **Description:** Initialize 2FA enrollment.
- **Request Body:** `{ "method": "totp" }`
- **Response Example:**
```json
{ "secret": "JBSWY3DPEHPK3PXP", "qr_code_url": "https://api.umbra.io/qr/..." }
```

**Endpoint:** `POST /auth/session`
- **Description:** Primary login endpoint.
- **Request Body:** `{ "email": "user@ironbay.com", "password": "password123" }`
- **Response Example:**
```json
{ "token": "jwt_access_token_here", "expires_at": "2023-10-24T12:00:00Z" }
```

---

## 5. DATABASE SCHEMA

**Engine:** MySQL 8.0  
**Naming Convention:** Snake_case

### 5.1 Table Definitions

1. **`users`**
   - `id` (UUID, PK)
   - `email` (String, Unique)
   - `password_digest` (String)
   - `role` (Enum: admin, operator, viewer)
   - `locale` (String, Default: 'en')
   - `two_factor_enabled` (Boolean)
   - `created_at` / `updated_at` (Timestamp)

2. **`devices`**
   - `id` (UUID, PK)
   - `serial_number` (String, Unique)
   - `firmware_version` (String)
   - `status` (Enum: online, offline, maintenance)
   - `last_heartbeat` (Timestamp)
   - `user_id` (UUID, FK -> users.id)
   - `created_at` (Timestamp)

3. **`device_logs`**
   - `id` (BigInt, PK)
   - `device_id` (UUID, FK -> devices.id)
   - `event_type` (String)
   - `payload` (JSON)
   - `created_at` (Timestamp, Indexed)

4. **`billing_accounts`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `stripe_customer_id` (String)
   - `plan_type` (Enum: free, pilot, enterprise)
   - `current_period_end` (Timestamp)

5. **`payment_methods`**
   - `id` (UUID, PK)
   - `billing_account_id` (UUID, FK -> billing_accounts.id)
   - `card_token` (String)
   - `last_four` (String)
   - `expiry_date` (Date)

6. **`scheduled_reports`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `report_type` (String)
   - `frequency` (String, Cron format)
   - `delivery_email` (String)
   - `active` (Boolean)

7. **`api_usage_stats`**
   - `id` (BigInt, PK)
   - `user_id` (UUID, FK -> users.id)
   - `endpoint` (String)
   - `request_count` (Integer)
   - `timestamp` (Date, Indexed)

8. **`notifications`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `channel` (Enum: email, sms, push, in_app)
   - `message` (Text)
   - `read_at` (Timestamp, Nullable)
   - `created_at` (Timestamp)

9. **`two_factor_keys`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `encrypted_secret` (Text)
   - `recovery_codes` (JSON)
   - `created_at` (Timestamp)

10. **`system_configs`**
    - `id` (Integer, PK)
    - `key` (String, Unique)
    - `value` (Text)
    - `environment` (Enum: dev, staging, prod)

### 5.2 Relationships
- `users` 1:N `devices`
- `users` 1:1 `billing_accounts`
- `billing_accounts` 1:N `payment_methods`
- `devices` 1:N `device_logs`
- `users` 1:N `scheduled_reports`
- `users` 1:N `api_usage_stats`
- `users` 1:N `notifications`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra employs a three-tier environment strategy to ensure stability and PCI compliance.

**1. Development (`dev`)**
- **Host:** Heroku (Shared Dynos)
- **Database:** Local MySQL / Heroku Postgres (Free Tier)
- **CI/CD:** Automatic deploy on push to `develop` branch.
- **Purpose:** Feature development and initial unit testing.

**2. Staging (`staging`)**
- **Host:** Heroku (Standard Dynos)
- **Database:** Heroku MySQL (Mirrored Production Schema)
- **CI/CD:** Automatic deploy on merge to `main` (before prod promotion).
- **Purpose:** Quality Assurance (QA) and User Acceptance Testing (UAT). This environment mimics production hardware configurations.

**3. Production (`prod`)**
- **Host:** Heroku Private Space (Dedicated Network)
- **Database:** Heroku MySQL (High Availability Cluster)
- **CI/CD:** Continuous Deployment. Every merged PR into the `production` branch is deployed immediately.
- **Purpose:** Live user traffic and PCI-compliant data processing.

### 6.2 Infrastructure Components
- **Load Balancer:** Heroku Router (handles SSL termination).
- **Background Processing:** Sidekiq with Redis (used for report generation and notifications).
- **File Storage:** AWS S3 with Server-Side Encryption (SSE).
- **Log Aggregation:** Papertrail for real-time log monitoring and error alerting.
- **Compliance:** VPC (Virtual Private Cloud) to isolate the production database from the public internet.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** RSpec, FactoryBot.
- **Coverage Goal:** 80% line coverage.
- **Focus:** Business logic, helper methods, and model validations. Every model must have a corresponding spec file.
- **Execution:** Run on every PR via GitHub Actions.

### 7.2 Integration Testing
- **Tooling:** Capybara, Selenium.
- **Focus:** High-level user flows (e.g., "User logs in -> Navigates to Device List -> Triggers Reboot").
- **PCI Specifics:** Integration tests for billing must use Stripe/Payment gateway "test mode" tokens to avoid real financial transactions.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Cypress.
- **Focus:** Cross-browser compatibility and critical path validation in the Staging environment.
- **Frequency:** Executed weekly and before any major milestone release.

### 7.4 Performance Testing
- **Tooling:** JMeter.
- **Focus:** API rate limiting thresholds and report generation timeouts.
- **Scenario:** Simulate 5,000 concurrent IoT device heartbeats to ensure the Rails monolith can handle the ingress.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor EOL (End-of-Life) for IoT gateway | High | Critical | Build a contingency fallback architecture using open-source MQTT brokers. |
| **R-02** | Scope creep from non-technical stakeholders | High | Medium | Engage external consultant for an independent assessment of the roadmap. |
| **R-03** | PCI DSS Audit Failure | Low | Critical | Monthly internal audits and strict adherence to the tokenization strategy. |
| **R-04** | Technical Debt (God Class) | High | Medium | Incremental refactoring: move methods to "Service Objects" over 3 sprints. |
| **R-05** | Team Dysfunction (Lead/PM conflict) | Medium | High | Establish a formal "Decision Log" to remove personality-based friction. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or total data loss.
- **High:** Significant delay to milestones.
- **Medium:** Manageable overhead or minor feature delay.
- **Low:** Negligible impact on delivery.

---

## 9. TIMELINE & GANTT DESCRIPTION

### 9.1 Phase 1: Foundation & Compliance (Now - 2026-03-15)
- **Focus:** Cleaning up technical debt, finalizing the modular monolith structure, and completing the architecture review.
- **Dependency:** Budget approval for the critical tool purchase.
- **Key Milestone:** **Milestone 1: Architecture Review Complete (2026-03-15)**.

### 9.2 Phase 2: Hardening & Feature Completion (2026-03-16 - 2026-05-15)
- **Focus:** Implementing 2FA and the Notification System. Hardening the API for external use.
- **Dependency:** Completion of the "God Class" refactoring.
- **Key Milestone:** **Milestone 2: Production Launch (2026-05-15)**.

### 9.3 Phase 3: External Beta & Iteration (2026-05-16 - 2026-07-15)
- **Focus:** Onboarding 10 pilot users, monitoring NPS, and adjusting API rate limits based on real-world usage.
- **Dependency:** Successful production launch.
- **Key Milestone:** **Milestone 3: External Beta with 10 Pilot Users (2026-07-15)**.

---

## 10. MEETING NOTES

### Meeting 1: Architecture & Debt Review
**Date:** 2023-11-02  
**Attendees:** Dante Oduya, Alejandro Oduya, Ilya Santos, Paloma Liu  
**Discussion:**
- Dante presented the current state of the `SystemManager` class (the 3,000-line God class). He argued that it is too risky to refactor now.
- Paloma (Contractor) disagreed, stating that the class is causing merge conflicts every single day.
- Ilya noted that the UI is becoming sluggish because the `SystemManager` is being called in the view layer.
- Tension arose between Dante (Tech Lead) and the Project Manager (represented here by the product requirements) regarding the priority of refactoring vs. new features.

**Action Items:**
- [Dante] Create a map of the `SystemManager` dependencies. (Owner: Dante | Due: 2023-11-10)
- [Paloma] Propose a "Service Object" pattern to break up the God class. (Owner: Paloma | Due: 2023-11-12)

### Meeting 2: Vendor EOL Crisis
**Date:** 2023-12-15  
**Attendees:** Dante Oduya, Alejandro Oduya  
**Discussion:**
- Alejandro reported that the primary vendor for the IoT gateway has announced end-of-life for their current API version by Q1 2026.
- This creates a massive risk for the Production Launch (Milestone 2).
- Dante suggested that the current Heroku setup might not be flexible enough to handle a custom MQTT broker.
- Decision made to allocate 20% of each sprint to "Contingency Architecture."

**Action Items:**
- [Alejandro] Research open-source alternatives to the vendor gateway. (Owner: Alejandro | Due: 2023-12-20)
- [Dante] Draft a fallback architecture diagram. (Owner: Dante | Due: 2023-12-25)

### Meeting 3: Budget & Blocker Sync
**Date:** 2024-01-10  
**Attendees:** Dante Oduya, Ilya Santos, Paloma Liu  
**Discussion:**
- The team discussed the pending budget approval for the "Critical Tool Purchase" (Enterprise Monitoring Suite).
- Ilya expressed concern that without this tool, they cannot guarantee the 80% feature adoption rate because they can't see where users are getting stuck.
- Paloma noted that the lack of tool budget is a symptom of the board's hesitation regarding the $5M+ spend.
- Dante remained silent for most of the meeting, reflecting the ongoing dysfunction between the lead and the PM.

**Action Items:**
- [Dante] Send a formal request for the tool purchase to the Board via the PM. (Owner: Dante | Due: 2024-01-12)
- [Ilya] Document the specific metrics that the tool will track to justify the ROI. (Owner: Ilya | Due: 2024-01-15)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+ (Flagship Initiative)

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $2,800,000 | Salaries for 2 full-time employees, 1 designer, and contractor fees for Paloma Liu over 3 years. |
| **Infrastructure** | $1,200,000 | Heroku Private Spaces, MySQL High Availability, AWS S3, and SendGrid/Twilio API costs. |
| **Tools & Licenses** | $400,000 | Enterprise Monitoring Suite (Pending), PCI Compliance Auditing tools, and IDE licenses. |
| **Contingency Fund** | $600,000 | Reserve for vendor pivot and emergency scaling during external beta. |
| **Total** | **$5,000,000** | |

---

## 12. APPENDICES

### Appendix A: The "God Class" Refactoring Map
The `SystemManager` class currently handles the following domains:
1. **Authentication:** `SystemManager.authenticate_user(email, password)`
2. **Logging:** `SystemManager.log_event(device_id, event)`
3. **Emailing:** `SystemManager.send_alert_email(user_id, message)`
4. **Hardware Control:** `SystemManager.send_reboot_command(device_id)`

**Proposed Refactor:**
- `AuthService` $\rightarrow$ handles all login/session logic.
- `AuditLogger` $\rightarrow$ handles MySQL log insertions.
- `NotificationService` $\rightarrow$ handles email/SMS dispatch.
- `DeviceController` $\rightarrow$ handles hardware-level API calls.

### Appendix B: PCI DSS Level 1 Compliance Checklist
To maintain compliance, the Umbra network implements the following:
- **Encryption:** All data in transit is encrypted via TLS 1.3.
- **Tokenization:** Credit card numbers are never stored in the MySQL database. Only "tokens" provided by the payment gateway are stored.
- **Access Control:** Database access is restricted to a specific bastion host.
- **Audit Trails:** Every access to the `payment_methods` table is logged with the user's ID and a timestamp.
- **Network Isolation:** The production environment is isolated in a Heroku Private Space with restricted ingress/egress.