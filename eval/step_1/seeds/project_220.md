# PROJECT SPECIFICATION DOCUMENT: PROJECT CORNICE
**Document Version:** 1.0.4  
**Status:** Finalized / Baseline  
**Date:** October 24, 2025  
**Owner:** Celine Kim (CTO)  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Cornice" is a strategic initiative by Talus Innovations to modernize the core operational infrastructure of the company. For over 15 years, Talus Innovations has relied on a legacy monolithic system—internally referred to as "The Anchor"—which governs the primary business logic of our fintech operations. While stable, The Anchor is built on deprecated libraries, lacks scalable API connectivity, and represents a significant operational risk. Cornice is designed as a direct, high-fidelity replacement for this system.

The primary objective is the migration of all enterprise workflows to a modern Python/Django ecosystem without a single second of downtime. Because Talus Innovations operates in the high-stakes fintech sector, any interruption in service would result in immediate financial loss and regulatory penalties.

### 1.2 Business Justification
The legacy system has reached its "end-of-life" in terms of maintainability. Maintenance costs have spiked by 40% year-over-year due to the scarcity of developers who can maintain the legacy codebase and the increasing difficulty of patching security vulnerabilities. Furthermore, the lack of native GDPR and CCPA compliance in the legacy system poses a legal liability as Talus expands its EU footprint.

Cornice will resolve these issues by introducing a three-tier architecture that separates presentation from business logic, ensuring that updates to the UI do not compromise the integrity of the data layer. By moving to AWS ECS and PostgreSQL, Talus will transition from expensive on-premise server maintenance to a scalable cloud model.

### 1.3 ROI Projection
The projected Return on Investment (ROI) for Cornice is calculated based on three primary pillars:
1.  **Operational Cost Reduction:** Estimated savings of $120,000 per annum through the decommissioning of legacy hardware and reduction in manual patching hours.
2.  **Risk Mitigation:** Elimination of potential regulatory fines associated with GDPR/CCPA non-compliance, which can reach up to 4% of global annual turnover.
3.  **Efficiency Gains:** A projected 25% increase in employee productivity via the implementation of the "Advanced Search" and "Notification" modules, reducing the time spent on manual data retrieval from 15 minutes to under 30 seconds per query.

The total project budget is $800,000. Given the projected efficiency gains and cost savings, the break-even point is estimated at 14 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Cornice follows a traditional Three-Tier Architecture to ensure strict separation of concerns, facilitating easier auditing and security patching.

1.  **Presentation Tier:** A Django-templated frontend (transitioning toward a decoupled JS framework) serving as the user interface.
2.  **Business Logic Tier (Application Layer):** Python/Django backend executing the core fintech calculations, validation logic, and integration with third-party APIs.
3.  **Data Tier:** A PostgreSQL relational database for persistent storage, with Redis acting as a high-speed caching and message brokering layer for asynchronous tasks.

### 2.2 Infrastructure Diagram (ASCII)
```text
[ CLIENT BROWSER ] 
       |
       v
[ AWS Application Load Balancer (ALB) ]
       |
       v
[ AWS ECS (Fargate) ] <---- [ Redis Cache/Celery ]
|  (Django App Container)  |       ^
|  - Version: 2.4.1        |       |
|  - Python: 3.11          |       |
|__________________________|       |
       |                           |
       v                           v
[ PostgreSQL RDS (EU-West-1) ] <--- [ S3 Bucket (CDN) ]
(Data Residency: Ireland/EU)         (Virus-Scanned Files)
```

### 2.3 Technology Stack
*   **Language:** Python 3.11
*   **Framework:** Django 4.2 (LTS)
*   **Database:** PostgreSQL 15.4
*   **Caching/Queue:** Redis 7.0 (via Celery for background workers)
*   **Containerization:** Docker / AWS ECS (Fargate)
*   **Storage:** AWS S3 with CloudFront CDN distribution
*   **Compliance:** Data Residency enforced in `eu-west-1` (Dublin) to meet GDPR requirements.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: Critical)
**Status:** In Design | **Launch Blocker: Yes**

The Notification System is the central nervous system of Cornice. Given the fintech nature of the tool, missed notifications regarding trade settlements or compliance alerts are unacceptable. 

**Functional Requirements:**
The system must support four distinct channels:
1.  **In-App:** Real-time alerts using WebSockets (Django Channels) that appear in the user's notification bell.
2.  **Email:** Transactional emails sent via AWS SES, utilizing Django templates for branding consistency.
3.  **SMS:** Urgent alerts sent via Twilio API for critical system failures or security breaches.
4.  **Push:** Browser-based push notifications for high-priority updates.

**Logic Workflow:**
Notifications are triggered by "Events" within the business logic layer. A `NotificationDispatcher` class will evaluate the user's preferences (stored in the `UserPreference` table) to determine which channels to utilize. For instance, a "Password Change" event must trigger both Email and In-App notifications, while a "Monthly Report" may only trigger an In-App alert.

**Technical Constraints:**
To avoid blocking the main request-response cycle, all notifications must be dispatched asynchronously via Celery. The system must handle "Retry Logic" for failed SMS/Email deliveries, implementing an exponential backoff strategy.

### 3.2 Offline-First Mode with Background Sync (Priority: Medium)
**Status:** Not Started

Due to the nature of field audits and occasional connectivity issues in regional offices, Cornice must support offline data entry.

**Functional Requirements:**
The application will utilize a Service Worker and IndexedDB to cache essential application shells and a subset of the user's active data. When the user is offline, the UI will allow them to continue performing "Create" and "Update" operations on specific entities (e.g., Audit Logs).

**Synchronization Logic:**
Once a connection is re-established, the system will perform a "Delta Sync." The client will send a payload of all locally stored changes since the last successful `sync_timestamp`. The backend will use a "Last-Write-Wins" conflict resolution strategy, unless a version conflict is detected, in which case the record is flagged for manual review by the user.

**Technical Specifications:**
The sync mechanism will utilize a RESTful endpoint `/api/v1/sync/` that accepts a JSON array of mutations. The background sync process must be throttled to prevent overwhelming the server during a mass-reconnection event.

### 3.3 File Upload with Virus Scanning and CDN Distribution (Priority: Medium)
**Status:** Not Started

Users must be able to upload supporting financial documentation (PDF, XLSX) which are then distributed globally for review.

**Functional Requirements:**
1.  **Upload:** Files are uploaded via a multipart form to a temporary staging area in S3.
2.  **Scanning:** An AWS Lambda function is triggered upon upload, invoking the ClamAV engine to scan for malware and viruses.
3.  **Distribution:** Once cleared, the file is moved to a production S3 bucket and served via AWS CloudFront CDN to minimize latency.

**Security Constraints:**
Files must be renamed to UUIDs upon upload to prevent directory traversal attacks. All files must be encrypted at rest using AES-256. Access to files is managed via "Signed URLs" with a maximum TTL (Time-to-Live) of 15 minutes, ensuring that documents are not leaked via public URLs.

### 3.4 Advanced Search with Faceted Filtering (Priority: Medium)
**Status:** Complete

The search module allows users to navigate millions of legacy records with sub-second latency.

**Functional Requirements:**
The system implements full-text indexing using PostgreSQL's `tsvector` and `tsquery`. Users can perform complex queries across multiple fields (e.g., Client Name, Transaction ID, Date Range).

**Faceted Filtering:**
The UI provides a sidebar of filters (facets) that update dynamically. For example, if a user searches for "Quarterly Report," the facets will show the number of results per "Year," "Region," and "Asset Class."

**Technical Implementation:**
Search queries are routed through a dedicated `SearchService` that optimizes queries by utilizing GIN (Generalized Inverted Index) on the database. To prevent performance degradation, the search function utilizes a "Debounce" mechanism on the frontend, ensuring requests are only sent after the user has stopped typing for 300ms.

### 3.5 Data Import/Export with Format Auto-Detection (Priority: Medium)
**Status:** Complete

To facilitate the migration from The Anchor, Cornice supports bulk ingestion of data.

**Functional Requirements:**
The import tool supports CSV, JSON, and XML. It features a "Format Auto-Detector" that analyzes the first 10 lines of a file to determine the delimiter and structure before prompting the user for field mapping.

**Export Capabilities:**
Users can export filtered datasets into the same formats. Large exports ( > 5,000 rows) are handled as background jobs; the system generates a CSV file in S3 and emails the user a download link once the process is complete.

**Validation Logic:**
During import, the system performs "Dry Run" validation. It checks for data type mismatches and constraint violations (e.g., unique IDs) without committing the transaction to the database.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require an `Authorization: Bearer <token>` header. Base URL: `https://api.cornice.talus.io/v1/`

### 4.1 `GET /auth/session`
*   **Description:** Validates the current session and returns user permissions.
*   **Request:** None.
*   **Response (200 OK):**
    ```json
    {
      "user_id": "u-99283",
      "role": "Admin",
      "permissions": ["read:all", "write:all"],
      "expires_at": "2026-10-15T12:00:00Z"
    }
    ```

### 4.2 `POST /notifications/send`
*   **Description:** Triggers a custom notification to a specific user.
*   **Request:**
    ```json
    {
      "user_id": "u-123",
      "message": "Trade settlement complete",
      "priority": "high",
      "channels": ["email", "in-app"]
    }
    ```
*   **Response (202 Accepted):** `{"job_id": "job-8821", "status": "queued"}`

### 4.3 `GET /search/query`
*   **Description:** Executes a faceted search across the database.
*   **Request Params:** `q=string`, `facet_region=EU`, `page=1`.
*   **Response (200 OK):**
    ```json
    {
      "results": [...],
      "facets": { "region": {"EU": 450, "US": 120}, "year": {"2024": 100} },
      "total": 570
    }
    ```

### 4.4 `POST /files/upload`
*   **Description:** Uploads a file for virus scanning.
*   **Request:** `multipart/form-data` (file, category).
*   **Response (201 Created):**
    ```json
    {
      "file_id": "f-5541",
      "status": "scanning",
      "cdn_url": null
    }
    ```

### 4.5 `POST /sync/delta`
*   **Description:** Syncs offline changes to the server.
*   **Request:**
    ```json
    {
      "last_sync": "2026-01-01T10:00:00Z",
      "changes": [{"action": "update", "id": 101, "data": {...}}]
    }
    ```
*   **Response (200 OK):** `{"status": "synced", "conflicts": []}`

### 4.6 `GET /export/download/{job_id}`
*   **Description:** Retrieves a generated export file from S3.
*   **Request:** `job_id` in path.
*   **Response (302 Redirect):** Redirects to a temporary S3 Signed URL.

### 4.7 `GET /users/profile`
*   **Description:** Returns the authenticated user's profile.
*   **Response (200 OK):** `{"name": "John Doe", "email": "j.doe@talus.io"}`

### 4.8 `PATCH /users/preferences`
*   **Description:** Updates notification preferences.
*   **Request:** `{"email_enabled": false, "sms_enabled": true}`
*   **Response (200 OK):** `{"status": "updated"}`

---

## 5. DATABASE SCHEMA

The database uses PostgreSQL 15.4. All tables use UUIDs as primary keys for distributed system compatibility.

### 5.1 Table Definitions

1.  **`users`**: Core user identity.
    *   `id` (UUID, PK), `email` (VARCHAR, Unique), `password_hash` (TEXT), `role_id` (FK), `created_at` (Timestamp).
2.  **`roles`**: Role-based access control.
    *   `id` (UUID, PK), `role_name` (VARCHAR), `permissions` (JSONB).
3.  **`user_preferences`**: User settings for notifications and UI.
    *   `user_id` (FK), `email_enabled` (Bool), `sms_enabled` (Bool), `push_enabled` (Bool), `timezone` (VARCHAR).
4.  **`notifications`**: Audit log of all sent notifications.
    *   `id` (UUID, PK), `user_id` (FK), `message` (TEXT), `channel` (VARCHAR), `sent_at` (Timestamp), `read_at` (Timestamp, Nullable).
5.  **`documents`**: Metadata for uploaded files.
    *   `id` (UUID, PK), `owner_id` (FK), `s3_key` (VARCHAR), `status` (Enum: scanning, clean, infected), `mime_type` (VARCHAR).
6.  **`audit_logs`**: Tracking all system changes for compliance.
    *   `id` (UUID, PK), `user_id` (FK), `action` (VARCHAR), `entity_id` (UUID), `timestamp` (Timestamp).
7.  **`sync_sessions`**: Tracks offline sync events.
    *   `id` (UUID, PK), `user_id` (FK), `device_id` (VARCHAR), `last_sync_at` (Timestamp).
8.  **`financial_records`**: The primary business data.
    *   `id` (UUID, PK), `client_id` (FK), `amount` (Decimal), `currency` (VARCHAR), `transaction_date` (Date).
9.  **`clients`**: Information about the fintech clients.
    *   `id` (UUID, PK), `name` (VARCHAR), `country_code` (VARCHAR), `compliance_level` (Integer).
10. **`search_index`**: Materialized view for fast searching.
    *   `record_id` (UUID), `search_vector` (TSVector).

### 5.2 Relationships
*   **One-to-One:** `users` $\rightarrow$ `user_preferences`.
*   **One-to-Many:** `users` $\rightarrow$ `notifications`, `users` $\rightarrow$ `documents`, `users` $\rightarrow$ `audit_logs`.
*   **One-to-Many:** `clients` $\rightarrow$ `financial_records`.
*   **Many-to-One:** `users` $\rightarrow$ `roles`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To ensure zero downtime and a stable release train, Cornice utilizes three distinct environments:

#### 6.1.1 Development (Dev)
*   **Purpose:** Iterative feature development and unit testing.
*   **Configuration:** Local Docker Compose or a shared "sandbox" ECS cluster.
*   **Database:** Mock data / Sanitized snapshots.
*   **Deployment:** Continuous Integration (CI) triggers on every commit to `develop` branch.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and Legal review.
*   **Configuration:** Mirrored production environment in `eu-west-1`.
*   **Database:** Anonymized production clone.
*   **Deployment:** Merges from `develop` to `release` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live enterprise operations.
*   **Configuration:** High-availability ECS cluster across three Availability Zones (AZs).
*   **Database:** Multi-AZ RDS PostgreSQL with automated backups every 6 hours.
*   **Deployment:** Weekly Release Train (Every Tuesday at 03:00 UTC).

### 6.2 The Release Train
The project strictly adheres to a "Weekly Release Train." 
*   **No Hotfixes:** If a bug is discovered on Wednesday, it must be fixed in Dev, Stage, and deployed the following Tuesday.
*   **Cut-off:** All JIRA tickets must be in "Resolved" status by Monday 18:00 UTC to be included in the train.
*   **Rollback:** Every deployment includes a blue-green swap. If the health check fails, the ALB automatically reverts to the previous version.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Scope:** Individual Python functions and Django models.
*   **Tooling:** `pytest` and `unittest.mock`.
*   **Requirement:** 80% minimum code coverage. All business logic in the "God Class" (during refactor) must have 100% coverage before modification.

### 7.2 Integration Testing
*   **Scope:** Interaction between Django, PostgreSQL, and Redis.
*   **Methodology:** Using `pytest-django`, we spin up a temporary test database for every suite. We test the API contract (request/response) for all 8 primary endpoints.
*   **Key Focus:** Ensuring the `NotificationDispatcher` correctly routes messages to the mock AWS SES/Twilio endpoints.

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Full user journeys (e.g., "User uploads file $\rightarrow$ waits for scan $\rightarrow$ views file via CDN").
*   **Tooling:** Playwright.
*   **Frequency:** Run against the Staging environment before every Tuesday release train.

### 7.4 Security Testing
*   **Static Analysis:** `Bandit` and `Snyk` are integrated into the CI pipeline to catch common Python vulnerabilities.
*   **Dynamic Analysis:** Monthly penetration tests performed by Malik Moreau to ensure GDPR/CCPA data residency constraints are not bypassed.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | High | Hire contractor (Leandro Moreau) to diversify knowledge and reduce bus factor. |
| R-02 | Team lack of experience with Python/Django | Medium | Medium | Maintain a shared "Wiki of Workarounds" and conduct weekly peer reviews. |
| R-03 | Data Processing Agreement (DPA) legal block | High | Critical | Escalate to Legal VP; utilize a provisional DPA for staging only. |
| R-04 | Legacy "God Class" failure during refactor | Medium | High | Implement a "Strangler Fig" pattern; migrate logic piece-by-piece into service layers. |
| R-05 | Zero-downtime migration failure | Low | Critical | Implement blue-green deployments and a 24-hour "shadow run" period. |

**Impact Matrix:**
*   **Critical:** System outage or legal non-compliance.
*   **High:** Milestone delay $> 2$ weeks.
*   **Medium:** Feature quality degradation.
*   **Low:** Minor UI/UX bugs.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
1.  **Foundation Phase (Nov 2025 - Feb 2026):** Setup of AWS infrastructure, database schema implementation, and refactoring of the "God Class."
2.  **Feature Build Phase (Mar 2026 - May 2026):** Implementation of Notification System and Offline-First mode.
3.  **Beta Phase (June 2026 - Aug 2026):** External testing and onboarding.
4.  **Hardening Phase (Sept 2026 - Oct 2026):** Performance tuning, security audits, and final migration.

### 9.2 Key Milestones
*   **Milestone 1: External Beta (10 Pilot Users)**
    *   *Target Date:* 2026-06-15
    *   *Dependencies:* Notification system (Critical) must be operational.
*   **Milestone 2: First Paying Customer Onboarded**
    *   *Target Date:* 2026-08-15
    *   *Dependencies:* GDPR/CCPA legal review completed.
*   **Milestone 3: Full Production Launch**
    *   *Target Date:* 2026-10-15
    *   *Dependencies:* Zero-downtime migration validated in Staging.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment (2025-11-02)
**Attendees:** Celine Kim, Fleur Gupta, Malik Moreau
*   Three-tier design confirmed.
*   Postgres for data, Redis for tasks.
*   EU-West-1 for GDPR.
*   Celine insists on weekly release train. No hotfixes.

### Meeting 2: Risk Mitigation Sync (2025-12-12)
**Attendees:** Celine Kim, Leandro Moreau
*   Sponsor rotation is a worry.
*   Leandro onboarded as contractor.
*   Knowledge transfer starts now.
*   God class is "terrifying"—3k lines. Must break it down.

### Meeting 3: Legal & Blocker Review (2026-01-15)
**Attendees:** Celine Kim, Malik Moreau, Legal Rep
*   DPA still not signed.
*   Blocker for production data.
*   Using dummy data in Stage for now.
*   Malik warns about CCPA gaps in legacy export.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Salaries for Fleur, Malik; Contract fees for Leandro. |
| **Infrastructure** | 15% | $120,000 | AWS ECS, RDS, S3, CloudFront (Est. 6 months + buffer). |
| **Tools & Licenses** | 10% | $80,000 | JIRA, Snyk, Twilio API, AWS SES, Playwright Cloud. |
| **Contingency** | 10% | $80,000 | Reserved for unexpected legal costs or infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: The "God Class" Refactoring Plan
The current `LegacyCore` class is a 3,000-line file handling `Auth`, `Logging`, and `Email`. 
**Refactor Path:**
1.  **Extract Auth:** Move to `django.contrib.auth` and custom `AuthenticationService`.
2.  **Extract Logging:** Implement `structlog` and route to CloudWatch.
3.  **Extract Email:** Move to the new `NotificationDispatcher`.
4.  **Verification:** Run the legacy test suite against the new service-based architecture to ensure parity.

### Appendix B: GDPR Data Residency Mapping
To comply with EU data residency:
*   **Primary Database:** `rds.eu-west-1.amazonaws.com`
*   **S3 Buckets:** `s3.eu-west-1.amazonaws.com`
*   **Backup Vault:** Locked to the Ireland region.
*   **Access Control:** Any admin access from outside the EU is routed through a secure VPN with MFA, and all access is logged in the `audit_logs` table.