# PROJECT SPECIFICATION DOCUMENT: PROJECT LATTICE
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2023  
**Project Lead:** Juno Costa (VP of Product)  
**Company:** Tundra Analytics  
**Classification:** Confidential – ISO 27001 Compliant

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Lattice is a strategic cost-reduction and operational efficiency initiative commissioned by Tundra Analytics. Currently, the organization operates four redundant internal tools for cybersecurity marketplace management. These tools—legacy billing systems, disparate audit trackers, fragmented notification engines, and siloed file repositories—have created a "technical archipelago," resulting in duplicated licensing costs, fragmented data, and significant operational overhead.

The objective of Lattice is to consolidate these four redundant systems into a single, unified e-commerce marketplace specifically tailored for the cybersecurity industry. By centralizing these functions, Tundra Analytics aims to eliminate the overhead associated with maintaining four separate codebases and reduce the cognitive load on operators.

### 1.2 ROI Projection and Success Metrics
The project represents a substantial investment of $3M, reflecting high executive visibility. The return on investment (ROI) is calculated through both direct cost savings (license elimination) and operational efficiency.

**Key Performance Indicators (KPIs):**
*   **Metric 1: Operational Efficiency:** Achieve a 50% reduction in manual processing time for end-users. This will be measured by comparing the time taken to onboard a new cybersecurity vendor across the four legacy tools versus the unified Lattice platform.
*   **Metric 2: Revenue Growth:** Generate $500,000 in new revenue attributed directly to the product within 12 months of launch. This will be achieved by reducing the "time-to-market" for new security products listed on the marketplace.
*   **Metric 3: Cost Reduction:** Reduction of redundant infrastructure costs by an estimated $120,000 per annum following the decommissioning of legacy tools.

### 1.4 Project Scope
Lattice will provide a secure, scalable environment for the distribution and billing of cybersecurity services. The scope includes the development of a micro-frontend architecture, a robust backend powered by FastAPI, and a tamper-evident audit system. Due to the nature of the industry, all developments must strictly adhere to ISO 27001 certification standards.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Overview
Lattice employs a **Micro-Frontend (MFE) Architecture** paired with a distributed backend. This allows independent team ownership of specific marketplace modules (e.g., Billing, Notifications, File Management) without creating deployment bottlenecks.

**Core Stack:**
*   **Backend:** Python 3.11 with FastAPI (Asynchronous framework for high concurrency).
*   **Database:** MongoDB (NoSQL for flexibility in cybersecurity product metadata).
*   **Task Queue:** Celery with Redis as the broker (For asynchronous processing of virus scans and emails).
*   **Containerization:** Docker Compose for orchestration.
*   **Hosting:** Self-hosted on Tundra Analytics private cloud (Required for ISO 27001 compliance).

### 2.2 Architectural Diagram (ASCII)

```text
[ CLIENT LAYER ]
      |
      +--> [ MFE: User Dashboard ] ----+
      +--> [ MFE: Vendor Portal ] -----+--> [ API GATEWAY / NGINX ]
      +--> [ MFE: Admin Panel ] -------+           |
                                                  | (REST/JSON)
                                                  v
[ SERVICE LAYER ]                          [ FastAPI APP ]
      |                                            |
      +--> [ Auth Service ] <---------------------+---+--> [ MongoDB Cluster ]
      +--> [ Billing Service ] <------------------+   |
      +--> [ File/Scan Service ] <----------------+   +--> [ Redis Cache ]
      +--> [ Notification Service ] <-------------+   |
                                                      |
[ ASYNC LAYER ]                                        |
      |                                                v
      +--> [ Celery Worker 1: Virus Scanning ] <------+
      +--> [ Celery Worker 2: Email/SMS Dispatch ] <---+
      +--> [ Celery Worker 3: Audit Logging ] <---------+
                                                      |
[ EXTERNAL ]                                          v
      +--> [ CDN: Static Assets ] <-------------------+
      +--> [ Payment Gateway (Stripe/Wire) ] <---------+
      +--> [ SMS Gateway (Twilio) ] <-----------------+
```

### 2.3 Data Flow and Security
All requests must pass through an authentication middleware that validates JWT tokens. Because this is a cybersecurity marketplace, the "Zero Trust" model is applied. Data at rest is encrypted using AES-256, and all inter-service communication occurs over TLS 1.3.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical | **Status:** Blocked (Pending Legal Review of Data Processing Agreement) | **Impact:** Launch Blocker

**Description:**
As a cybersecurity marketplace, Lattice must ensure that no malicious payloads are uploaded by vendors or users. This feature handles the ingestion of security tools, whitepapers, and license files.

**Detailed Workflow:**
1.  **Ingestion:** Files are uploaded via a multipart/form-data endpoint. The file is initially stored in a "Quarantine" bucket in MongoDB GridFS.
2.  **Scanning:** A Celery task is triggered to pass the file through a multi-engine virus scanner (ClamAV and a proprietary Tundra internal scanner). 
3.  **Validation:** If a threat is detected, the file is immediately deleted, and an "Incident Report" is logged in the audit trail.
4.  **Distribution:** Once cleared, the file is pushed to the internal CDN. A signed URL is generated with a 15-minute expiration to prevent unauthorized hotlinking.

**Technical Requirements:**
*   Maximum file size: 2GB.
*   Scanning latency must be under 30 seconds for files < 100MB.
*   CDN must be geographically distributed across Tundra's primary data centers.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review

**Description:**
For ISO 27001 compliance, every state-changing action in the system must be logged. This is not a standard application log but a legal record of who did what and when.

**Detailed Workflow:**
1.  **Capture:** Every API request to a `POST`, `PUT`, or `DELETE` endpoint triggers a logging event.
2.  **Hashing:** The system creates a SHA-256 hash of the current log entry combined with the hash of the previous entry (creating a hash-chain).
3.  **Storage:** Logs are written to a MongoDB collection with "Write Once Read Many" (WORM) characteristics enabled at the storage level.
4.  **Verification:** A nightly cron job recalculates the chain to ensure no records have been deleted or modified.

**Technical Requirements:**
*   Fields captured: Timestamp (UTC), UserID, IP Address, Request Path, Payload (Masked), Response Code, and Sequence Hash.
*   Storage: Logs must be retained for 7 years per regulatory requirements.

### 3.3 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** In Design

**Description:**
A centralized hub to manage all communications with users. This replaces the disparate emailers and alert systems in the four legacy tools.

**Detailed Workflow:**
1.  **Trigger:** Services emit a `NotificationEvent` to the Celery queue.
2.  **Preference Engine:** The system checks the User Profile to see which channels are enabled (e.g., User A wants Email for billing, but Push for security alerts).
3.  **Dispatch:**
    *   *Email:* Sent via SMTP/SendGrid.
    *   *SMS:* Dispatched via Twilio.
    *   *In-App:* Pushed via WebSocket (FastAPI) to the MFE.
    *   *Push:* Sent via Firebase Cloud Messaging (FCM).
4.  **Tracking:** The system tracks "Sent," "Delivered," and "Read" statuses.

**Technical Requirements:**
*   Support for templated messages using Jinja2.
*   Rate limiting to prevent spamming users (max 5 notifications per hour per user).

### 3.4 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** Blocked (Waiting on Legal)

**Description:**
Consolidation of the four legacy billing methods into a unified subscription engine. This manages recurring revenue for cybersecurity software licenses.

**Detailed Workflow:**
1.  **Plan Selection:** Users select from tiered pricing (Basic, Pro, Enterprise).
2.  **Cycle Management:** The system manages monthly and annual billing cycles.
3.  **Invoice Generation:** Automatic PDF generation using a headless Chrome instance.
4.  **Dunning Process:** Automated email sequences for failed payments before account suspension.

**Technical Requirements:**
*   Support for multiple currencies (USD, EUR, GBP).
*   Integration with Tundra’s internal financial ledger.
*   Tax calculation logic based on user jurisdiction.

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** Not Started

**Description:**
A "nice-to-have" feature to protect the system from abuse and provide business intelligence on how vendors are using the marketplace APIs.

**Detailed Workflow:**
1.  **Interception:** A FastAPI middleware checks the API key of the incoming request.
2.  **Bucket Algorithm:** Uses a Token Bucket algorithm stored in Redis to track requests per second (RPS).
3.  **Throttling:** If the limit is exceeded, returns a `429 Too Many Requests` response.
4.  **Analytics:** Usage data is aggregated every hour and stored in a MongoDB collection for reporting.

**Technical Requirements:**
*   Configurable limits per user tier (e.g., Free: 100 req/min; Gold: 5000 req/min).
*   Real-time dashboard for admins to adjust limits on the fly.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication requires a Bearer Token in the Header.

### 4.1 File Upload & Management
**Endpoint:** `POST /files/upload`
*   **Description:** Uploads a file to quarantine for virus scanning.
*   **Request:** `multipart/form-data` (file: Binary, category: String)
*   **Response:** `202 Accepted`
    ```json
    { "file_id": "uuid-123", "status": "scanning", "eta": "30s" }
    ```

**Endpoint:** `GET /files/status/{file_id}`
*   **Description:** Checks the scanning status and retrieves CDN link if cleared.
*   **Response:** `200 OK`
    ```json
    { "file_id": "uuid-123", "status": "cleared", "url": "https://cdn.lattice.io/dl/abc" }
    ```

### 4.2 Audit Trail
**Endpoint:** `GET /audit/logs`
*   **Description:** Retrieve a paginated list of audit events.
*   **Query Params:** `page`, `limit`, `userId`, `startDate`, `endDate`
*   **Response:** `200 OK`
    ```json
    { "logs": [{ "timestamp": "2023-10-24T10:00Z", "action": "FILE_UPLOAD", "user": "u45" }], "next_page": 2 }
    ```

**Endpoint:** `POST /audit/verify-chain`
*   **Description:** Triggers an immediate integrity check of the hash chain.
*   **Response:** `200 OK`
    ```json
    { "integrity": "verified", "last_checked": "2023-10-24T10:05Z" }
    ```

### 4.3 Notifications
**Endpoint:** `POST /notifications/send`
*   **Description:** Manually trigger a notification (Admin only).
*   **Request:** `{ "userId": "u123", "message": "Hello", "channels": ["email", "push"] }`
*   **Response:** `201 Created`
    ```json
    { "notification_id": "n-987", "status": "queued" }
    ```

**Endpoint:** `PATCH /notifications/preferences`
*   **Description:** Update user communication preferences.
*   **Request:** `{ "email": false, "sms": true, "push": true }`
*   **Response:** `200 OK`
    ```json
    { "status": "updated" }
    ```

### 4.4 Billing
**Endpoint:** `GET /billing/subscription`
*   **Description:** Retrieve current user subscription details.
*   **Response:** `200 OK`
    ```json
    { "plan": "Enterprise", "renewal_date": "2024-01-01", "status": "active" }
    ```

**Endpoint:** `POST /billing/checkout`
*   **Description:** Initialize a payment session.
*   **Request:** `{ "planId": "plan_pro_monthly", "paymentMethod": "credit_card" }`
*   **Response:** `200 OK`
    ```json
    { "checkout_url": "https://billing.lattice.io/pay/sess_xyz" }
    ```

---

## 5. DATABASE SCHEMA (MONGODB)

Lattice uses a document-oriented schema. While MongoDB is schemaless, the following logical collections and fields are enforced via Pydantic models in the FastAPI layer.

### 5.1 Collections

1.  **`users`**
    *   `_id`: ObjectId
    *   `email`: String (Indexed, Unique)
    *   `password_hash`: String
    *   `role`: String (Admin, Vendor, Customer)
    *   `preferences`: Map (Notification settings)
    *   `created_at`: Date

2.  **`products`** (Cybersecurity tools/services)
    *   `_id`: ObjectId
    *   `vendor_id`: ObjectId (Ref: `users`)
    *   `name`: String
    *   `version`: String
    *   `price`: Decimal
    *   `category`: String (Firewall, Endpoint, IAM)
    *   `metadata`: Map (Technical specs)

3.  **`subscriptions`**
    *   `_id`: ObjectId
    *   `user_id`: ObjectId (Ref: `users`)
    *   `product_id`: ObjectId (Ref: `products`)
    *   `start_date`: Date
    *   `end_date`: Date
    *   `status`: String (Active, PastDue, Canceled)

4.  **`files`**
    *   `_id`: ObjectId
    *   `uploader_id`: ObjectId (Ref: `users`)
    *   `filename`: String
    *   `checksum`: String (SHA-256)
    *   `scan_status`: String (Quarantine, Cleared, Infected)
    *   `cdn_url`: String
    *   `size_bytes`: Long

5.  **`audit_logs`**
    *   `_id`: ObjectId
    *   `timestamp`: Date (Indexed)
    *   `user_id`: ObjectId (Ref: `users`)
    *   `action`: String
    *   `payload`: String (JSON)
    *   `previous_hash`: String
    *   `current_hash`: String

6.  **`notifications`**
    *   `_id`: ObjectId
    *   `user_id`: ObjectId (Ref: `users`)
    *   `channel`: String (Email, SMS, etc.)
    *   `content`: String
    *   `delivered_at`: Date
    *   `read_at`: Date

7.  **`invoices`**
    *   `_id`: ObjectId
    *   `subscription_id`: ObjectId (Ref: `subscriptions`)
    *   `amount`: Decimal
    *   `tax`: Decimal
    *   `pdf_link`: String
    *   `payment_status`: String (Paid, Unpaid)

8.  **`api_keys`**
    *   `_id`: ObjectId
    *   `user_id`: ObjectId (Ref: `users`)
    *   `key_hash`: String
    *   `rate_limit_tier`: String
    *   `expires_at`: Date

9.  **`usage_metrics`**
    *   `_id`: ObjectId
    *   `api_key_id`: ObjectId (Ref: `api_keys`)
    *   `endpoint`: String
    *   `request_count`: Long
    *   `window_start`: Date

10. **`vendor_profiles`**
    *   `_id`: ObjectId
    *   `user_id`: ObjectId (Ref: `users`)
    *   `company_name`: String
    *   `iso_certification_id`: String
    *   `verified_status`: Boolean

### 5.2 Relationships Summary
*   **One-to-Many:** `users` $\rightarrow$ `products` (One vendor, many products).
*   **One-to-Many:** `users` $\rightarrow$ `subscriptions` (One user, many subs).
*   **One-to-Many:** `users` $\rightarrow$ `audit_logs` (One user, many log entries).
*   **One-to-One:** `users` $\rightarrow$ `vendor_profiles` (One user account, one vendor profile).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To ensure ISO 27001 compliance and stability, Lattice utilizes a three-tier environment strategy. All environments are isolated via VLANs.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and initial unit testing.
*   **Configuration:** Local Docker Compose setups for developers; a shared "Integration Dev" server.
*   **Data:** Synthetic data only; no real customer PII.
*   **Deployment:** Automated on every merge to `develop` branch.

#### 6.1.2 Staging (QA)
*   **Purpose:** Pre-production validation and User Acceptance Testing (UAT).
*   **Configuration:** Mirrors Production hardware and network topology.
*   **Data:** Anonymized production snapshots.
*   **Deployment:** Requires a **manual QA gate**. Once a feature is merged to `release`, a QA engineer must sign off on the feature set. There is a strict **2-day turnaround** for the QA gate process.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer traffic.
*   **Configuration:** High-availability cluster, self-hosted on Tundra Analytics private cloud.
*   **Data:** Encrypted production data.
*   **Deployment:** Manual trigger by Juno Costa (Project Lead) following Staging sign-off.

### 6.2 Infrastructure Components
*   **Reverse Proxy:** Nginx (Handles SSL termination and load balancing).
*   **Orchestration:** Docker Compose (deployed via custom Ansible playbooks).
*   **Storage:** MongoDB Atlas (On-Premise version) with triple-node replication.
*   **Caching:** Redis 7.0 for Celery and API rate limiting.
*   **Security:** Hardware Security Modules (HSM) for managing encryption keys.

---

## 7. TESTING STRATEGY

The goal is 90% code coverage across the backend and 70% across the micro-frontends.

### 7.1 Unit Testing
*   **Backend:** Python `pytest` is used for all FastAPI endpoints. Each service must have mock objects for MongoDB and Redis to ensure tests are isolated.
*   **Frontend:** Jest and React Testing Library for individual component validation.
*   **Frequency:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
*   **Focus:** Interaction between services (e.g., ensuring the `File Service` correctly triggers the `Notification Service` upon a virus detection).
*   **Tooling:** `Postman/Newman` collections running against the Staging environment.
*   **Database:** Dedicated "Integration DB" that is wiped and seeded before every test run.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** Critical user journeys (e.g., "Vendor uploads tool $\rightarrow$ System scans $\rightarrow$ Customer buys $\rightarrow$ License delivered").
*   **Tooling:** Playwright for browser automation.
*   **Cadence:** Weekly regression suites run every Friday in the Staging environment.

### 7.4 Security Testing
*   **Penetration Testing:** Bi-annual external audit.
*   **Static Analysis:** SonarQube integrated into the CI/CD pipeline to detect security hotspots and "God classes."
*   **Dependency Scanning:** Snyk to monitor for vulnerable Python packages.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Performance requirements are 10x current capacity with no extra budget. | High | High | Build a contingency plan with a fallback architecture (e.g., introducing Redis caching layers and optimizing MongoDB indices). |
| R2 | Integration partner's API is undocumented and buggy. | High | Medium | Assign a dedicated owner (Jules Liu) to track issues, maintain a "shadow" documentation file, and implement aggressive error handling. |
| R3 | Legal review of DPA takes longer than expected. | Medium | Critical | Identify "Non-PII" features that can be developed and tested in isolation to prevent total team idling. |
| R4 | Technical debt: 3,000-line 'God class' causing instability. | High | Medium | Schedule a phased refactor (Sprints 4-6) to break the class into `AuthService`, `LogService`, and `EmailService`. |
| R5 | ISO 27001 compliance failure during audit. | Low | Critical | Weekly internal compliance checkpoints and strict adherence to the "Manual QA Gate" process. |

### Probability/Impact Matrix
*   **High Probability / High Impact:** R1, R4
*   **High Probability / Medium Impact:** R2
*   **Medium Probability / Critical Impact:** R3
*   **Low Probability / Critical Impact:** R5

---

## 9. TIMELINE AND MILESTONES

The project is divided into four phases over a 10-month window.

### 9.1 Phase 1: Foundation (Oct 2023 - Jan 2024)
*   **Focus:** Core infrastructure setup, MongoDB schema finalization, and the "God Class" refactor.
*   **Dependencies:** None.
*   **Key Deliverable:** Working API Gateway and Auth system.

### 9.2 Phase 2: Core Features (Jan 2024 - April 2024)
*   **Focus:** File Upload (Critical), Audit Trail (High), and Notification System (Medium).
*   **Dependencies:** Legal sign-off on DPA (for File Upload).
*   **Milestone 1:** **Performance benchmarks met (Target: 2025-04-15)**.
    *   *Requirement:* System must handle 1,000 concurrent requests with $<200\text{ms}$ latency.

### 9.3 Phase 3: Business Logic (April 2024 - June 2024)
*   **Focus:** Billing and Subscription Management, API Rate Limiting.
*   **Dependencies:** Phase 2 completion.
*   **Milestone 2:** **Stakeholder demo and sign-off (Target: 2025-06-15)**.
    *   *Requirement:* Full walkthrough of the end-to-end vendor onboarding and payment flow.

### 9.4 Phase 4: Hardening & Launch (June 2024 - August 2024)
*   **Focus:** E2E testing, ISO audit, and production environment tuning.
*   **Dependencies:** Stakeholder sign-off.
*   **Milestone 3:** **Production launch (Target: 2025-08-15)**.

---

## 10. MEETING NOTES

*Note: These are excerpts from the 200-page shared running document. The document is currently unsearchable, requiring manual scrolling.*

### Meeting 1: Architecture Alignment (2023-11-02)
**Attendees:** Juno Costa, Nadira Nakamura, Gideon Moreau, Jules Liu.
*   **Discussion:** Nadira expressed concerns about the micro-frontend overhead for a team of 12. Gideon argued that it is necessary for independent ownership of the Billing vs. Notification modules.
*   **Decision:** Proceed with MFE. Nadira to define the shell application (Host) and a standard set of shared UI components to ensure consistency.
*   **Action Item:** Nadira to provide the MFE communication protocol (Event Bus) by next week.

### Meeting 2: The "God Class" Crisis (2023-12-15)
**Attendees:** Juno Costa, Jules Liu, Nadira Nakamura.
*   **Discussion:** Jules Liu reported that the 3,000-line class handling Auth, Logging, and Email is causing regression bugs in every single PR. It is currently impossible to test the Email logic without triggering a full Auth sequence.
*   **Decision:** This is now officially designated as "Technical Debt." We will not add new features to this class. A "Refactor Sprint" is scheduled for February.
*   **Action Item:** Jules to map out the internal dependencies of the God class.

### Meeting 3: Blockage Update (2024-02-10)
**Attendees:** Juno Costa, Jules Liu.
*   **Discussion:** File Upload is still blocked. Legal has not returned the Data Processing Agreement (DPA). This is a launch blocker.
*   **Decision:** The team will pivot to the Notification System and Audit Trail logging to maintain velocity. Jules will use "dummy" file uploads for testing purposes until the legal green light is given.
*   **Action Item:** Juno to escalate the DPA review to the Chief Legal Officer.

---

## 11. BUDGET BREAKDOWN

The total investment is **$3,000,000 USD**.

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,800,000 | 12-person cross-functional team (Salaries, Benefits, Contractor fees for Jules Liu). |
| **Infrastructure** | 20% | $600,000 | Self-hosted server hardware, MongoDB on-prem licenses, HSM modules, and CDN costs. |
| **Tools & Software** | 10% | $300,000 | Snyk, SonarQube, Twilio/SendGrid credits, and ISO 27001 certification audit fees. |
| **Contingency** | 10% | $300,000 | Reserved for Risk R1 (Performance fallback) and potential infrastructure scaling. |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist
To maintain certification, the Lattice project must satisfy the following:
1.  **A.9 Access Control:** Implementation of RBAC (Role-Based Access Control) and MFA for all admin accounts.
2.  **A.12.4 Logging:** The Audit Trail feature must be immutable and monitored for unauthorized access.
3.  **A.13.1 Network Security:** Separation of Dev, Staging, and Prod environments via physical or virtual firewalls.
4.  **A.14.2 Security in Development:** Mandatory manual QA gate and peer review for all production deployments.

### Appendix B: Performance Benchmarking Specs
To meet Milestone 1, the system must pass the following "Stress Tests" in the Staging environment:
*   **Concurrent Users:** 1,000 active sessions.
*   **Request Rate:** 500 Requests Per Second (RPS) on the `/api/v1/audit/logs` endpoint.
*   **File Ingestion:** Concurrent upload of 50 files (up to 500MB each) without crashing the Celery worker.
*   **Database Latency:** MongoDB query execution time for the `subscriptions` collection must be $<50\text{ms}$ with an index on `user_id`.