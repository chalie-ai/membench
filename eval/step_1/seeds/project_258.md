# PROJECT SPECIFICATION DOCUMENT: PROJECT CITADEL (v1.0.4)

**Company:** Iron Bay Technologies  
**Industry:** Real Estate  
**Project Status:** Active / In-Development  
**Confidentiality Level:** Level 4 (Strictly Confidential / HIPAA Compliant)  
**Document Owner:** Rumi Jensen (CTO)  
**Date of Last Revision:** October 24, 2023

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Citadel is a mission-critical strategic initiative developed by Iron Bay Technologies to provide high-fidelity cybersecurity monitoring specifically tailored for the real estate sector. The real estate industry is currently undergoing a rapid digital transformation, migrating legacy property management systems to cloud-based architectures. This shift has exposed a critical vulnerability: the lack of centralized, real-time security visibility across fragmented portfolios.

Iron Bay Technologies has entered into a strategic partnership with a leading external security intelligence provider. Citadel serves as the integration hub, syncing with this provider's proprietary API to aggregate threat intelligence, network anomalies, and access logs into a single, actionable dashboard. For the real estate industry—where a single breach of a property management system can compromise the PII (Personally Identifiable Information) of thousands of tenants—the ability to detect and mitigate threats in real-time is not just a competitive advantage, but a legal necessity.

### 1.2 Strategic Objectives
The primary objective is to create a "single pane of glass" for security officers at real estate firms to monitor their digital assets. By integrating third-party security feeds via a robust webhook framework and implementing a tamper-evident audit trail, Citadel will ensure that Iron Bay Technologies remains the gold standard for secure real estate technology.

### 1.3 ROI Projection and Financial Impact
The financial viability of Citadel is based on a B2B SaaS model. Based on current market analysis of the real estate prop-tech sector, the projected Return on Investment (ROI) is calculated as follows:

*   **Revenue Stream:** A tiered subscription model (Basic, Professional, Enterprise) targeting mid-to-large scale real estate investment trusts (REITs).
*   **Projected Revenue:** Based on the target of 10,000 Monthly Active Users (MAU) within six months of launch, assuming an average revenue per user (ARPU) of $12.00, the projected monthly recurring revenue (MRR) is $120,000.
*   **Cost Reduction:** By automating security monitoring, client firms are projected to reduce their external security consultant spend by 20-30%.
*   **Break-even Analysis:** With the current variable budget and milestone-based funding, the project is expected to reach its break-even point 14 months post-launch.
*   **ROI Forecast:** A projected 240% ROI over the first 36 months, driven by the high barrier to entry created by the strategic API partnership and HIPAA compliance certification.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Citadel utilizes a microservices architecture to ensure scalability and fault tolerance. Communication between services is handled via an event-driven model using Apache Kafka, ensuring that high-volume security logs do not bottleneck the user interface.

**The Stack:**
*   **Backend:** Python 3.11 / Django 4.2 (REST Framework)
*   **Primary Database:** PostgreSQL 15 (Relational data, User profiles, Billing)
*   **Caching/Message Broker:** Redis 7.0 (Session management, Temporary caching)
*   **Event Stream:** Apache Kafka (Asynchronous log processing)
*   **Infrastructure:** AWS ECS (Elastic Container Service)
*   **Orchestration:** Kubernetes (EKS)
*   **CI/CD:** GitLab CI with rolling deployment strategies.

### 2.2 ASCII Architecture Diagram
```text
[ User Browser / Client ] 
       | (HTTPS/TLS 1.3)
       v
[ AWS Application Load Balancer ]
       |
       +-----> [ API Gateway / Nginx ]
                    |
                    +-----> [ Auth Service (Django) ] <---> [ PostgreSQL ]
                    |
                    +-----> [ Monitoring Service (Django) ] <---> [ Redis ]
                    |                                          ^
                    |                                          |
                    +-----> [ Data Ingestion Service ] ---------+
                                     |
                                     v
                             [ Kafka Topic: security_events ]
                                     |
                                     +-----> [ Audit Logger Service ] ---> [ Tamper-Evident Storage ]
                                     |
                                     +-----> [ Notification Engine ] ---> [ SMS/Email/Push ]
                                     |
                                     +-----> [ External API Sync ] <---> [ External Partner API ]
```

### 2.3 Security and Compliance
As a HIPAA-compliant system, Citadel implements the following:
*   **Encryption at Rest:** All PostgreSQL volumes are encrypted using AWS KMS (AES-256).
*   **Encryption in Transit:** TLS 1.3 enforced for all internal and external traffic.
*   **Data Isolation:** Logical separation of tenant data within the database.
*   **Access Control:** Role-Based Access Control (RBAC) integrated with the authentication service.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework
**Priority:** Medium | **Status:** In Review

The Webhook Integration Framework allows third-party security tools (e.g., CrowdStrike, SentinelOne) to push real-time alerts into the Citadel dashboard. Rather than polling the external API constantly, Citadel provides a set of endpoints where external tools can post JSON payloads.

**Functional Requirements:**
*   **Dynamic Endpoint Generation:** Each user/organization is assigned a unique webhook URL (e.g., `/api/v1/webhooks/receiver/{unique_token}/`).
*   **Payload Validation:** A validation layer that checks the incoming JSON against a predefined schema. If the payload is malformed, the system returns a `400 Bad Request` and logs the failure.
*   **Secret Handshake:** To prevent spoofing, Citadel implements a shared secret mechanism. The external tool must sign the payload using an HMAC-SHA256 signature, which Citadel verifies using the stored secret.
*   **Retry Logic:** If the internal Kafka producer fails, the framework must return a `503 Service Unavailable`, signaling the third-party tool to retry based on its exponential backoff policy.

**Technical Implementation:**
The framework will consist of a `WebhookManager` class that maps incoming tokens to specific tenant IDs and event types. Once verified, the payload is serialized and pushed to the `incoming_events` Kafka topic for downstream processing by the Monitoring Service.

### 3.2 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker) | **Status:** In Design

This feature manages the commercial lifecycle of the Citadel user base. Given the variable budget of the project, the billing system must be modular to accommodate changes in pricing tiers.

**Functional Requirements:**
*   **Tiered Subscription Logic:** Three tiers: *Estate Basic* (up to 500 assets), *Estate Pro* (up to 5,000 assets), and *Estate Enterprise* (unlimited).
*   **Automated Invoicing:** Integration with Stripe API to handle monthly recurring billing. Invoices must be generated on the 1st of every month.
*   **Grace Period Management:** If a payment fails, the system enters a 7-day "Grace Period" where services remain active but the user sees a "Payment Overdue" banner. After 7 days, the account is transitioned to "Read-Only" mode.
*   **Usage Tracking:** A background worker that counts the number of monitored assets per tenant every 24 hours and updates the billing record.

**Technical Implementation:**
A dedicated `BillingService` will handle the interaction between the Django app and Stripe. A PostgreSQL table `subscription_plans` will store the pricing and limits, while `user_subscriptions` will track the current state of each account. A Celery beat task will run daily to verify subscription validity.

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** Not Started

For HIPAA compliance, every action within Citadel must be logged in a way that cannot be altered or deleted by any user, including administrators.

**Functional Requirements:**
*   **Immutable Logs:** Once a log entry is written, it cannot be edited. Any "change" to a record must be stored as a new version of that record.
*   **Cryptographic Chaining:** Each log entry will contain a hash of the previous entry (`CurrentHash = Hash(Timestamp + Action + Data + PreviousHash)`). This creates a blockchain-like chain.
*   **Daily Anchoring:** Every 24 hours, the final hash of the day's logs will be signed with a private key and stored in a separate, write-once-read-many (WORM) S3 bucket.
*   **Searchable Interface:** An admin panel allowing auditors to filter logs by user, date range, and action type.

**Technical Implementation:**
The system will use a middleware layer in Django that intercepts every `POST`, `PUT`, and `DELETE` request. The `AuditLog` model will store the hashed entries. A background process will verify the integrity of the chain hourly; if a hash mismatch is detected, a critical alert is triggered.

### 3.4 Notification System (Email, SMS, In-App, Push)
**Priority:** Low (Nice to Have) | **Status:** Not Started

The notification system provides the mechanism for alerting security officers when critical thresholds are met.

**Functional Requirements:**
*   **Multi-Channel Routing:** Users can configure their preferences (e.g., "Critical alerts via SMS and Email, Low alerts via In-App only").
*   **Template Engine:** A dynamic templating system allowing the product team to modify notification wording without changing code.
*   **Notification Aggregation:** To prevent "alert fatigue," the system will group similar alerts occurring within a 5-minute window into a single "Digest" notification.
*   **Push Integration:** Integration with Firebase Cloud Messaging (FCM) for mobile push notifications.

**Technical Implementation:**
A `NotificationDispatcher` service will consume messages from the `alerts` Kafka topic. It will check the `user_notification_preferences` table and route the message to the appropriate provider (SendGrid for email, Twilio for SMS, FCM for push).

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** Complete

This feature allows users to migrate their existing security logs from other platforms into Citadel or export them for external audits.

**Functional Requirements:**
*   **Automatic Format Detection:** The system analyzes the first 10 lines of an uploaded file to determine if it is CSV, JSON, XML, or Parquet.
*   **Schema Mapping:** A UI component that allows users to map their external columns (e.g., "src_ip") to Citadel's internal fields (e.g., "source_address").
*   **Asynchronous Processing:** Large files ( > 100MB) are processed in the background using Celery to prevent request timeouts.
*   **Export Scheduling:** Users can schedule weekly exports of their audit logs to be delivered via SFTP.

**Technical Implementation:**
The `ImportService` uses the `pandas` library for data manipulation and format detection. Uploads are stored in an S3 "Landing Zone" before being parsed and inserted into PostgreSQL in batches of 1,000 records to optimize database performance.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 `GET /assets/`
**Description:** Retrieves a list of all monitored real estate assets for the authenticated tenant.
*   **Request Parameters:** `limit` (int), `offset` (int), `status` (string).
*   **Response (200 OK):**
    ```json
    {
      "count": 150,
      "results": [
        { "id": "ast-9921", "name": "Plaza Tower A", "status": "secure", "last_scan": "2023-10-20T10:00Z" }
      ]
    }
    ```

### 4.2 `POST /assets/`
**Description:** Registers a new asset for monitoring.
*   **Request Body:**
    ```json
    { "name": "Sunset Villas", "ip_range": "192.168.1.0/24", "criticality": "high" }
    ```
*   **Response (201 Created):**
    ```json
    { "id": "ast-9922", "status": "provisioning" }
    ```

### 4.3 `GET /alerts/`
**Description:** Fetches security alerts filtered by severity.
*   **Request Parameters:** `severity` (critical|warning|info), `start_date` (ISO8601).
*   **Response (200 OK):**
    ```json
    {
      "alerts": [
        { "id": "al-441", "type": "Brute Force", "severity": "critical", "timestamp": "2023-10-21T04:12Z" }
      ]
    }
    ```

### 4.4 `POST /webhooks/register/`
**Description:** Generates a unique webhook URL and secret for a third-party tool.
*   **Request Body:** `{ "tool_name": "CrowdStrike", "event_types": ["malware_detected", "unauthorized_access"] }`
*   **Response (201 Created):**
    ```json
    { "webhook_url": "https://citadel.io/api/v1/webhooks/receiver/abc-123-xyz/", "secret": "sk_live_99887766" }
    ```

### 4.5 `GET /audit/logs/`
**Description:** Retrieves the tamper-evident audit trail.
*   **Request Parameters:** `user_id` (uuid), `date_from` (ISO8601), `date_to` (ISO8601).
*   **Response (200 OK):**
    ```json
    {
      "logs": [
        { "seq": 1001, "timestamp": "2023-10-21T08:00Z", "action": "USER_LOGIN", "hash": "e3b0c442...", "prev_hash": "a1b2c3d4..." }
      ]
    }
    ```

### 4.6 `POST /billing/subscription/update/`
**Description:** Updates the current subscription plan.
*   **Request Body:** `{ "plan_id": "estate_pro" }`
*   **Response (200 OK):**
    ```json
    { "status": "updated", "new_plan": "Estate Pro", "next_billing_date": "2023-11-01" }
    ```

### 4.7 `GET /system/health/`
**Description:** Returns the operational status of all microservices.
*   **Response (200 OK):**
    ```json
    { "status": "healthy", "services": { "db": "up", "redis": "up", "kafka": "up", "api": "up" } }
    ```

### 4.8 `POST /import/upload/`
**Description:** Uploads a log file for processing.
*   **Request Body:** `multipart/form-data` (file upload).
*   **Response (202 Accepted):**
    ```json
    { "job_id": "job-556677", "status": "processing", "estimated_time": "120s" }
    ```

---

## 5. DATABASE SCHEMA

The database is implemented in PostgreSQL 15. The schema is designed for high normalization to maintain data integrity, with specific indexing on timestamp and tenant columns for performance.

### 5.1 Tables and Relationships

1.  **`tenants`**
    *   `id` (UUID, PK): Unique identifier for the real estate company.
    *   `company_name` (VARCHAR): Official legal name.
    *   `created_at` (TIMESTAMP): Account creation date.
    *   `is_active` (BOOLEAN): Subscription status.
    *   *Relationship: One-to-Many with `users`, `assets`, and `subscriptions`.*

2.  **`users`**
    *   `id` (UUID, PK): User identifier.
    *   `tenant_id` (UUID, FK): Link to `tenants`.
    *   `email` (VARCHAR, Unique): User email.
    *   `password_hash` (VARCHAR): Argon2 hashed password.
    *   `role` (ENUM): ('Admin', 'Analyst', 'Auditor').
    *   *Relationship: Many-to-One with `tenants`.*

3.  **`assets`**
    *   `id` (UUID, PK): Unique asset identifier.
    *   `tenant_id` (UUID, FK): Link to `tenants`.
    *   `name` (VARCHAR): Name of the property/server.
    *   `ip_address` (INET): The IP address of the asset.
    *   `criticality` (ENUM): ('Low', 'Medium', 'High', 'Critical').
    *   *Relationship: Many-to-One with `tenants`.*

4.  **`subscriptions`**
    *   `id` (UUID, PK): Subscription ID.
    *   `tenant_id` (UUID, FK): Link to `tenants`.
    *   `plan_type` (ENUM): ('Basic', 'Pro', 'Enterprise').
    *   `stripe_customer_id` (VARCHAR): ID for external billing.
    *   `status` (VARCHAR): ('Active', 'Past Due', 'Canceled').
    *   *Relationship: One-to-One with `tenants`.*

5.  **`security_events`**
    *   `id` (BIGINT, PK): Event ID.
    *   `asset_id` (UUID, FK): Link to `assets`.
    *   `event_type` (VARCHAR): Type of threat (e.g., "SQL Injection").
    *   `severity` (INT): Scale of 1-10.
    *   `payload` (JSONB): The raw event data from the API.
    *   `timestamp` (TIMESTAMP): When the event occurred.
    *   *Relationship: Many-to-One with `assets`.*

6.  **`audit_logs`**
    *   `id` (BIGINT, PK): Log sequence number.
    *   `user_id` (UUID, FK): Link to `users`.
    *   `action` (VARCHAR): Action performed (e.g., "UPDATE_ASSET").
    *   `current_hash` (VARCHAR): SHA-256 hash of current record.
    *   `previous_hash` (VARCHAR): SHA-256 hash of previous record.
    *   `timestamp` (TIMESTAMP): Log time.
    *   *Relationship: Many-to-One with `users`.*

7.  **`webhook_configs`**
    *   `id` (UUID, PK): Config ID.
    *   `tenant_id` (UUID, FK): Link to `tenants`.
    *   `secret_token` (VARCHAR): Token used for URL generation.
    *   `hmac_key` (VARCHAR): Secret used for payload verification.
    *   `is_active` (BOOLEAN): Enabled/Disabled status.
    *   *Relationship: Many-to-One with `tenants`.*

8.  **`notification_preferences`**
    *   `user_id` (UUID, PK/FK): Link to `users`.
    *   `email_enabled` (BOOLEAN): Global toggle for email.
    *   `sms_enabled` (BOOLEAN): Global toggle for SMS.
    *   `push_enabled` (BOOLEAN): Global toggle for push.
    *   `alert_threshold` (ENUM): ('Critical Only', 'All').
    *   *Relationship: One-to-One with `users`.*

9.  **`import_jobs`**
    *   `id` (UUID, PK): Job ID.
    *   `tenant_id` (UUID, FK): Link to `tenants`.
    *   `file_path` (VARCHAR): S3 path to the uploaded file.
    *   `status` (ENUM): ('Pending', 'Processing', 'Completed', 'Failed').
    *   `rows_processed` (INT): Number of successfully imported lines.
    *   *Relationship: Many-to-One with `tenants`.*

10. **`api_sync_logs`**
    *   `id` (BIGINT, PK): Sync log ID.
    *   `external_provider` (VARCHAR): Name of the partner company.
    *   `sync_status` (VARCHAR): ('Success', 'Partial', 'Fail').
    *   `records_synced` (INT): Count of records retrieved.
    *   `timestamp` (TIMESTAMP): Time of sync.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Citadel utilizes three distinct environments to ensure that no unvetted code ever reaches production.

#### 6.1.1 Development (DEV)
*   **Purpose:** Feature development and unit testing.
*   **Infrastructure:** Local Docker Compose and a small shared AWS ECS cluster.
*   **Database:** PostgreSQL 15 (Ephemeral/Reset weekly).
*   **Deployment:** Automatic trigger on every push to the `develop` branch.

#### 6.1.2 Staging (STG)
*   **Purpose:** Pre-production validation, User Acceptance Testing (UAT), and integration testing with the partner's Sandbox API.
*   **Infrastructure:** Mirror of production (AWS ECS / Kubernetes).
*   **Database:** Sanitized copy of production data.
*   **Deployment:** Triggered on merge to the `release` branch.

#### 6.1.3 Production (PROD)
*   **Purpose:** Live customer environment.
*   **Infrastructure:** High-availability AWS ECS with Auto-scaling Groups (ASG) across three Availability Zones (AZs).
*   **Database:** RDS PostgreSQL Multi-AZ with automated snapshots every 6 hours.
*   **Deployment:** Rolling deployments via GitLab CI. A "Blue-Green" strategy is used: the "Green" environment is spun up and tested; traffic is then shifted from "Blue" to "Green" using the Load Balancer. If errors spike, an automatic rollback is triggered.

### 6.2 CI/CD Pipeline
The GitLab CI pipeline consists of the following stages:
1.  **Lint:** Flake8 and Black for Python code quality.
2.  **Test:** Running Pytest suite (Unit and Integration).
3.  **Build:** Creating Docker images and pushing to AWS ECR.
4.  **Security Scan:** Using Snyk to scan for dependencies with known vulnerabilities.
5.  **Deploy:** Updating the Kubernetes deployment manifests via `kubectl`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Approach:** Every single function and method must have a corresponding test case in the `/tests/unit` directory.
*   **Tooling:** `pytest` and `unittest.mock`.
*   **Coverage Goal:** 85% minimum code coverage.
*   **Focus:** Business logic, utility functions, and API serializers.

### 7.2 Integration Testing
*   **Approach:** Testing the interaction between services (e.g., API $\rightarrow$ Kafka $\rightarrow$ Audit Logger).
*   **Tooling:** `TestContainers` to spin up ephemeral PostgreSQL and Kafka instances.
*   **Focus:** Database migrations, API endpoint response codes, and event-driven workflows.

### 7.3 End-to-End (E2E) Testing
*   **Approach:** Simulating complete user journeys from the browser.
*   **Tooling:** `Playwright` or `Selenium`.
*   **Critical Paths:**
    1.  User registration $\rightarrow$ Subscription payment $\rightarrow$ Asset registration.
    2.  External API trigger $\rightarrow$ Dashboard alert $\rightarrow$ Notification received.
    3.  Data import upload $\rightarrow$ Schema mapping $\rightarrow$ Data visibility in dashboard.

### 7.4 Security Testing
*   **Penetration Testing:** Quarterly external audits.
*   **Fuzzing:** Sending malformed JSON to the webhook endpoints to ensure system stability.
*   **HIPAA Audit:** Monthly verification of encryption keys and access logs.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | **Scope Creep:** Stakeholders adding 'small' features continuously. | High | Medium | **Parallel-Path:** Prototype alternative approach simultaneously to show trade-offs in time/cost. |
| R-02 | **Budget Cut:** Fiscal quarter budget may be cut by 30%. | Medium | High | **Board Escalation:** Raise as a critical blocker in the next board meeting to secure funding. |
| R-03 | **API Latency:** Partner API response times exceed 2 seconds. | Medium | Medium | **Asynchronous Buffering:** Use Kafka to decouple API sync from the user-facing dashboard. |
| R-04 | **Technical Debt:** The 3,000-line 'God Class' causes regressions. | High | Medium | **Incremental Refactoring:** Allocate 10% of every sprint to break the class into modular services. |
| R-05 | **Data Breach:** Leak of PII resulting in HIPAA violation. | Low | Critical | **Encryption & WORM:** Enforce AES-256 and use WORM storage for audit logs. |

**Probability/Impact Matrix:**
*   *Low Probability / Low Impact:* Monitor.
*   *High Probability / Medium Impact:* Active mitigation.
*   *Low Probability / Critical Impact:* Intensive preventive controls.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
*   **Phase 1: Core Foundation (Now - May 2026):** Focus on the "God Class" refactoring, Subscription Management, and Data Import/Export.
*   **Phase 2: Beta Expansion (May 2026 - July 2026):** Implementation of the Webhook framework and onboarding of pilot users.
*   **Phase 3: Hardening & Compliance (July 2026 - September 2026):** Completion of the Audit Trail and final security audit.

### 9.2 Milestone Schedule

| Milestone | Target Date | Description | Dependencies |
| :--- | :--- | :--- | :--- |
| **M1: Production Launch** | 2026-05-15 | Full system deployment to PROD. | Billing System, Data Import. |
| **M2: External Beta** | 2026-07-15 | 10 pilot users active in the system. | Webhook Framework, Basic UI. |
| **M3: Security Audit** | 2026-09-15 | Third-party HIPAA/Security pass. | Audit Trail, Encryption. |

### 9.3 Gantt-Style Dependency View
`Refactor God Class` $\rightarrow$ `Billing System` $\rightarrow$ `Production Launch` $\rightarrow$ `Webhook Frame` $\rightarrow$ `External Beta` $\rightarrow$ `Audit Trail` $\rightarrow$ `Security Audit`.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Review (Oct 12, 2023)
*   **Attendees:** Rumi, Felix, Matteo, Dmitri.
*   **Notes:**
    *   Kafka too complex? Felix says no, need it for scale.
    *   Postgres for everything? Yes, except notifications.
    *   S3 for logs? Yes, must be WORM.
    *   Dmitri to research HMAC for webhooks.

### Meeting 2: Billing & Scope (Oct 19, 2023)
*   **Attendees:** Rumi, Matteo.
*   **Notes:**
    *   Stakeholders want "dark mode" now. Rumi says no, not a priority.
    *   Billing is a blocker. Need Stripe integration by Q1.
    *   Plan levels: Basic, Pro, Enterprise.
    *   Matteo to design the subscription upgrade flow.

### Meeting 3: Technical Debt Sync (Oct 26, 2023)
*   **Attendees:** Rumi, Felix, Dmitri.
*   **Notes:**
    *   God class is a mess. 3,000 lines.
    *   Doing Auth, Logging, Email all in one.
    *   Felix suggests breaking it into `AuthManager`, `LogManager`, and `MailService`.
    *   Dmitri to start writing unit tests for the God class before the split.

---

## 11. BUDGET BREAKDOWN

The budget for Project Citadel is variable and released in tranches based on milestone completion.

| Category | Allocation | Estimated Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $450,000 | Solo developer (Lead) + Internal team overhead. |
| **Infrastructure** | 20% | $150,000 | AWS EKS, RDS, S3, Kafka Managed Service. |
| **Tools & Licenses** | 10% | $75,000 | GitLab Premium, Snyk, SendGrid, Twilio, Stripe. |
| **Contingency** | 10% | $75,000 | Reserved for budget cuts or emergency scaling. |
| **Total** | **100%** | **$750,000** | *Estimated for first 18 months.* |

---

## 12. APPENDICES

### Appendix A: The "God Class" Refactoring Plan
The current `CoreManager` class handles too many responsibilities. The refactoring will proceed in three stages:
1.  **Extraction of Email Logic:** Move all `send_mail` methods to a new `NotificationService`.
2.  **Isolation of Authentication:** Move JWT validation and password hashing to an `IdentityService`.
3.  **Logging Decoupling:** Move all `write_log` calls to a `LoggingService` that pushes to Kafka.
*   **Target Date for completion:** February 2026.

### Appendix B: HIPAA Compliance Checklist
To ensure Milestone 3 is met, the following technical controls must be verified:
*   [ ] **Access Control:** Unique User IDs and automatic session timeouts (15 mins).
*   [ ] **Audit Controls:** Implementation of the `audit_logs` table with cryptographic chaining.
*   [ ] **Integrity:** Use of SHA-256 hashes to detect unauthorized modification of PHI.
*   [ ] **Transmission Security:** Enforced TLS 1.3 for all data moving between AWS regions.
*   [ ] **Data Disposal:** Automated script to permanently delete tenant data upon contract termination (GDPR/HIPAA right to be forgotten).