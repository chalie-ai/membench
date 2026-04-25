Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Technical Specification Document (TSD). 

***

# PROJECT SPECIFICATION: PROJECT EMBER
**Document Version:** 1.0.4  
**Last Updated:** 2025-10-12  
**Status:** Draft/In-Review  
**Classification:** Confidential – Coral Reef Solutions  
**Project Lead:** Rumi Gupta (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ember is a strategic healthcare records platform initiative developed by Coral Reef Solutions. While the company operates primarily within the agriculture technology sector, the internal management of workforce health, safety, and compliance records has become a fragmented liability. Currently, the organization utilizes four redundant internal tools to track employee health certifications, field medical records, occupational safety logs, and vaccination registries. These tools operate in silos, leading to massive data duplication, synchronization errors, and a significant administrative burden on the operations team.

The primary objective of Project Ember is the consolidation of these four legacy tools into a single, unified modular monolith. By streamlining these records into a centralized platform, Coral Reef Solutions aims to eliminate the technical overhead of maintaining four separate codebases and the operational overhead of manual data entry across multiple interfaces.

### 1.2 Business Justification
The current operational model is unsustainable. With a workforce expanding across multiple agricultural zones, the lack of a unified health record system has resulted in a 22% increase in administrative man-hours over the last fiscal year. The "redundancy tax"—the cost of paying for four different hosting environments and the developer hours required to patch four different systems—is currently estimated at $145,000 annually in wasted capacity.

Project Ember is framed as a cost-reduction initiative. By migrating to a single platform, Coral Reef Solutions will achieve:
1. **Operational Efficiency:** Removal of duplicate data entry.
2. **Compliance Security:** Centralized auditing for ISO 27001 certification, ensuring that sensitive health data is handled under a single, rigorous security protocol rather than four varying standards.
3. **Data Integrity:** Elimination of the "source of truth" conflict where different tools report different health statuses for the same employee.

### 1.3 ROI Projection and Financial Model
Project Ember is currently an **unfunded initiative**. It is being bootstrapped using existing team capacity (20+ people across three departments). Because there is no direct capital expenditure (CapEx) allocated, the ROI is calculated based on "Recovered Capacity" and "OpEx Reduction."

**Projected Annual Savings:**
- **Infrastructure Consolidation:** $12,000 (Reduction in Heroku Dyno counts and redundant database instances).
- **Labor Recovery:** $110,000 (Based on a 50% reduction in manual processing time for 10 administrative staff).
- **Risk Mitigation:** Estimated $25,000 (Avoidance of potential compliance fines related to fragmented health records).

**Total Projected Year 1 ROI:** ~$147,000.

### 1.4 Success Criteria
The success of Project Ember will be measured by two primary Key Performance Indicators (KPIs):
- **Metric 1 (Efficiency):** A 50% reduction in manual processing time for end-users (measured via time-to-completion for standard record updates).
- **Metric 2 (Adoption):** 10,000 Monthly Active Users (MAU) within six months of the official launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Philosophy
The architecture of Project Ember is governed by the principle of "Pragmatic Simplicity." To ensure rapid delivery with a bootstrapped team, the project utilizes a **Ruby on Rails monolith**. This approach minimizes the "distributed system tax" while allowing for future scalability.

The platform is designed as a **Modular Monolith**. Logic is separated into bounded contexts (e.g., `Records`, `Billing`, `Auth`, `Notifications`) within the same codebase. This allows the team to transition to microservices incrementally if the load exceeds the capacity of the monolith, without requiring a full rewrite.

### 2.2 The Stack
- **Language/Framework:** Ruby 3.2.2 / Rails 7.1 (API Mode)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL Add-ons)
- **Hosting:** Heroku (Private Spaces for ISO 27001 compliance)
- **Caching:** Redis
- **Background Processing:** Sidekiq
- **File Storage:** AWS S3 with CloudFront CDN

### 2.3 Architecture Diagram (ASCII Representation)

```text
[ End Users / Third Party Clients ]
             |
             v
     [ CloudFront CDN ] <---- (Static Assets / Verified Health Docs)
             |
             v
     [ Heroku Load Balancer ]
             |
             v
    _________________________________________________________________
   |                      EMBER MODULAR MONOLITH                     |
   |                                                                 |
   |  [ API Gateway Layer ] --> [ Versioning Logic (v1, v2) ]         |
   |                                                                 |
   |  [ Modules ]                                                    |
   |   ├── Health Records Module (Core Logic)                        |
   |   ├── Webhook Engine (Integration Framework)                   |
   |   ├── File Processor (Virus Scanning -> S3 Upload)              |
   |   ├── Sync Engine (Offline-First Background Worker)              |
   |   └── Feature Flag/AB System (Flipper/Custom)                   |
   |_________________________________________________________________|
             |                             |
             v                             v
     [ MySQL Database ]            [ Redis Cache ]
     (Relational Records)           (Session / Job Queue)
             |
             v
     [ External APIs / Webhooks ] --> [ Third Party Ag-Tech Tools ]
```

### 2.4 Security and Compliance
Because the platform handles healthcare records, it must reside within an **ISO 27001 certified environment**. This necessitates:
- **Encryption at Rest:** AES-256 for all database volumes.
- **Encryption in Transit:** TLS 1.3 for all API calls.
- **Audit Logging:** Every read/write access to a health record must be logged with a timestamp and User ID.
- **Manual QA Gate:** No code reaches production without a manual sign-off from the QA lead, ensuring no security regressions occur.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Review

**Functional Description:**
The Ember API serves as the primary gateway for external agriculture technology partners to push and pull health record data. To prevent breaking changes for third-party integrations, the API must implement a strict versioning strategy.

**Technical Requirements:**
- **Versioning:** The API will use URI-based versioning (e.g., `/api/v1/records`). When a breaking change is introduced, `v2` will be launched, and `v1` will be deprecated with a 6-month sunset period.
- **Sandbox Environment:** A mirrored environment (`sandbox.ember.coralreef.com`) will be provided. The sandbox will use a separate MySQL instance with anonymized data, allowing developers to test integrations without risking real health records.
- **Authentication:** JWT (JSON Web Tokens) with a rotation policy. API keys will be generated via the administrative dashboard.
- **Rate Limiting:** 1,000 requests per hour per API key to prevent DDoS and resource exhaustion.

**User Workflow:**
1. Developer requests an API key via the Ember Portal.
2. Developer tests their integration against the Sandbox environment.
3. Once validated, the developer switches the base URL to the Production environment.

### 3.2 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Functional Description:**
Ember must notify third-party tools when health records change (e.g., a certification expires or a new health clearance is uploaded). This framework allows for real-time synchronization across the Ag-Tech ecosystem.

**Technical Requirements:**
- **Event Registry:** A system to define "Trigger Events" (e.g., `record.created`, `record.updated`, `certification.expired`).
- **Payload Delivery:** Webhooks will be delivered via POST requests with a JSON payload.
- **Retry Logic:** If the receiving server returns a non-200 status, Ember will employ an exponential backoff retry strategy (5 attempts over 24 hours).
- **Security (HMAC):** Each webhook request will include an `X-Ember-Signature` header, allowing the recipient to verify the payload using a shared secret.
- **Delivery Logs:** A dashboard for administrators to see successful and failed webhook deliveries.

**Impact:** Without this, the "consolidation" goal fails because other tools will remain out of sync, forcing users back into manual data entry.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** High | **Status:** In Progress

**Functional Description:**
Users must be able to upload medical certificates, IDs, and health forms. Given the sensitivity of healthcare data and the risk of malware, a secure pipeline is required.

**Technical Requirements:**
- **Upload Pipeline:** `Client -> Rails API -> ClamAV Scanner -> AWS S3`.
- **Virus Scanning:** Integration with a ClamAV instance. Files are uploaded to a "Quarantine" bucket. Only after a `CLEAN` scan result are they moved to the "Permanent" bucket.
- **CDN Distribution:** CloudFront will be used to serve files. To ensure security, CloudFront will use **Signed URLs** with a maximum expiration of 15 minutes.
- **File Constraints:** Maximum file size of 25MB. Supported formats: `.pdf`, `.jpg`, `.png`.

**User Workflow:**
A user uploads a PDF of a vaccination record. The system scans it for viruses. Once cleared, the record is associated with the user's profile, and the user can view it via a time-limited secure link.

### 3.4 A/B Testing Framework (Feature Flag System)
**Priority:** High | **Status:** Blocked

**Functional Description:**
To optimize the user experience and ensure that consolidation actually reduces manual processing time, the team requires the ability to toggle features and run A/B tests.

**Technical Requirements:**
- **Feature Flagging:** Integration of the `Flipper` gem to enable/disable features for specific user segments (e.g., "Beta Users," "Region A").
- **A/B Logic:** The system must be able to assign a user to "Cohort A" or "Cohort B" and persist this assignment in the database.
- **Metric Tracking:** Integration with an analytics layer to track which cohort completes the health record update faster.
- **Blocking Factor:** This feature is currently blocked due to a conflict with the ISO 27001 audit requirements regarding "non-deterministic user experiences" in a regulated environment.

**Goal:** Test two different UI layouts for the "Quick Upload" page to see which results in fewer errors.

### 3.5 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Functional Description:**
Agriculture workers often operate in "dead zones" (remote fields) with no cellular connectivity. They must be able to update health records or log incidents offline.

**Technical Requirements:**
- **Client-Side Storage:** Use of IndexedDB (via a service worker) to cache data locally.
- **Conflict Resolution:** The "Last Write Wins" (LWW) strategy will be applied, but if a record has been updated by an admin in the interim, the system will trigger a "Conflict Resolution" prompt to the user.
- **Sync Queue:** A local queue of "pending changes" that automatically triggers a sync request when the browser detects a `navigator.onLine` event.
- **Background Sync API:** Utilization of the browser's Background Sync API to ensure data is pushed even if the tab is closed.

**User Workflow:**
A field medic records a health check-up in a remote area. The app saves the data locally. When the medic returns to the base station with Wi-Fi, the app automatically pushes the data to the Ember API in the background.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints return JSON. Base URL: `https://api.ember.coralreef.com/api/v1`

### 4.1 GET `/records`
**Description:** Retrieves a paginated list of health records.
- **Request Params:** `page` (int), `per_page` (int), `status` (string)
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "rec_123", "employee_id": "emp_456", "status": "compliant", "updated_at": "2026-01-10T10:00:00Z" }
  ],
  "meta": { "total_pages": 5, "current_page": 1 }
}
```

### 4.2 POST `/records`
**Description:** Creates a new healthcare record.
- **Request Body:** `{ "employee_id": "string", "record_type": "string", "data": { "field": "value" } }`
- **Response (201 Created):**
```json
{ "id": "rec_789", "status": "pending_review" }
```

### 4.3 GET `/records/{id}`
**Description:** Retrieves a specific record.
- **Response (200 OK):**
```json
{ "id": "rec_123", "details": { "vaccination_status": "complete", "last_exam": "2025-12-01" } }
```

### 4.4 PATCH `/records/{id}`
**Description:** Updates an existing record.
- **Request Body:** `{ "status": "non-compliant", "reason": "Expired certification" }`
- **Response (200 OK):**
```json
{ "id": "rec_123", "updated_at": "2026-02-15T09:00:00Z" }
```

### 4.5 DELETE `/records/{id}`
**Description:** Soft-deletes a record.
- **Response (204 No Content):** `Empty body`

### 4.6 POST `/webhooks/subscriptions`
**Description:** Subscribes a third-party tool to specific events.
- **Request Body:** `{ "target_url": "https://partner.com/webhook", "events": ["record.updated"] }`
- **Response (201 Created):**
```json
{ "subscription_id": "sub_abc", "secret": "whsec_xyz" }
```

### 4.7 GET `/files/upload-url`
**Description:** Requests a pre-signed S3 URL for secure file upload.
- **Request Body:** `{ "filename": "cert_01.pdf", "content_type": "application/pdf" }`
- **Response (200 OK):**
```json
{ "upload_url": "https://s3.aws.com/bucket/...", "file_id": "file_999" }
```

### 4.8 GET `/sync/delta`
**Description:** Retrieves all changes since a specific timestamp for offline sync.
- **Request Params:** `since` (ISO8601 timestamp)
- **Response (200 OK):**
```json
{ "changes": [ { "id": "rec_1", "action": "updated" }, { "id": "rec_2", "action": "created" } ] }
```

---

## 5. DATABASE SCHEMA

**Database Engine:** MySQL 8.0  
**Naming Convention:** snake_case  
**Primary Key Strategy:** UUIDs for all public-facing IDs to prevent enumeration attacks.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `email` (VARCHAR 255, Unique)
    - `password_digest` (VARCHAR 255)
    - `role` (ENUM: 'admin', 'medic', 'employee')
    - `created_at` (TIMESTAMP)
    - `updated_at` (TIMESTAMP)

2.  **`employees`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `employee_number` (VARCHAR 50, Unique)
    - `region_id` (INT, FK -> regions.id)
    - `full_name` (VARCHAR 255)
    - `date_of_birth` (DATE)

3.  **`health_records`**
    - `id` (UUID, PK)
    - `employee_id` (UUID, FK -> employees.id)
    - `record_type` (VARCHAR 50)
    - `status` (VARCHAR 20)
    - `data` (JSONB) - Stores specific medical metrics
    - `created_at` (TIMESTAMP)
    - `updated_at` (TIMESTAMP)

4.  **`certifications`**
    - `id` (UUID, PK)
    - `record_id` (UUID, FK -> health_records.id)
    - `cert_name` (VARCHAR 255)
    - `expiry_date` (DATE)
    - `is_verified` (BOOLEAN)

5.  **`files`**
    - `id` (UUID, PK)
    - `record_id` (UUID, FK -> health_records.id)
    - `s3_key` (VARCHAR 512)
    - `mime_type` (VARCHAR 50)
    - `scan_status` (ENUM: 'pending', 'clean', 'infected')
    - `uploaded_at` (TIMESTAMP)

6.  **`webhook_subscriptions`**
    - `id` (UUID, PK)
    - `target_url` (VARCHAR 512)
    - `secret_token` (VARCHAR 255)
    - `active` (BOOLEAN)

7.  **`webhook_events`**
    - `id` (BIGINT, PK)
    - `subscription_id` (UUID, FK -> webhook_subscriptions.id)
    - `event_type` (VARCHAR 50)
    - `payload` (JSONB)
    - `attempt_count` (INT)
    - `last_attempt_at` (TIMESTAMP)

8.  **`regions`**
    - `id` (INT, PK)
    - `region_name` (VARCHAR 100)
    - `timezone` (VARCHAR 50)

9.  **`feature_flags`**
    - `id` (INT, PK)
    - `flag_name` (VARCHAR 100, Unique)
    - `enabled` (BOOLEAN)
    - `cohort` (VARCHAR 50)

10. **`audit_logs`**
    - `id` (BIGINT, PK)
    - `user_id` (UUID, FK -> users.id)
    - `action` (VARCHAR 255)
    - `resource_id` (UUID)
    - `ip_address` (VARCHAR 45)
    - `timestamp` (TIMESTAMP)

### 5.2 Relationships
- `User` has one `Employee`.
- `Employee` has many `HealthRecords`.
- `HealthRecord` has many `Certifications` and many `Files`.
- `WebhookSubscription` has many `WebhookEvents`.
- `Employee` belongs to one `Region`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ember utilizes a three-tier environment strategy to ensure stability and compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Individual developer experimentation and feature branching.
- **Infrastructure:** Local Docker containers simulating the Heroku environment.
- **Database:** Local MySQL instance with seeded mock data.
- **Deployment:** Automatic on commit to `dev` branch.

#### 6.1.2 Staging (QA)
- **Purpose:** Final verification and stakeholder demos.
- **Infrastructure:** Heroku Staging Pipeline.
- **Database:** A sanitized clone of the production database (PII removed).
- **Deployment:** Triggered by merge to `staging` branch. Requires manual QA gate sign-off.
- **QA Gate:** Luna Fischer (DevOps) and Xena Stein (Junior Dev) must verify that all JIRA tickets for the release are marked "Resolved."

#### 6.1.3 Production (Prod)
- **Purpose:** Live end-user traffic.
- **Infrastructure:** Heroku Private Space (ISO 27001 compliant).
- **Database:** Production MySQL Cluster with High Availability (HA) enabled.
- **Deployment:** 2-day turnaround. Code is merged to `main`, deployed to staging, then manually promoted to production after the QA gate.

### 6.2 Infrastructure Management
Infrastructure is managed as code (IaC) using Terraform to ensure that the staging and production environments remain identical.

- **Log Management:** Papertrail for real-time log aggregation.
- **Monitoring:** New Relic for APM (Application Performance Monitoring) to track response times and error rates.
- **Backup Strategy:** Daily snapshots of the MySQL database with 30-day retention.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (RSpec)
- **Scope:** Individual methods, models, and controllers.
- **Requirement:** 80% code coverage.
- **Focus:** Validating the `HealthRecords` business logic and ensuring that date normalization handles the legacy format issues (see Technical Debt section).

### 7.2 Integration Testing
- **Scope:** API endpoint flows and database interactions.
- **Approach:** Testing the request-response cycle using `RSpec Request Specs`.
- **Focus:** Ensuring the Webhook Engine correctly triggers an event when a `HealthRecord` is updated and that the file upload pipeline correctly marks files as `infected` when the virus scanner returns a positive result.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from the frontend to the database.
- **Tooling:** Playwright or Cypress.
- **Focus:** 
    - **Offline Mode Sync:** Simulating network loss, updating a record, and restoring network to verify the background sync.
    - **Secure File Access:** Verifying that a user cannot access a file via URL once the Signed URL has expired.

### 7.4 Manual QA Gate
As per the technical architecture, every deployment to production requires a manual sign-off. This includes:
1. Verification of the "Critical" launch blockers (Webhooks and Offline Sync).
2. Smoke testing of the API Sandbox.
3. Verification that no new date format inconsistencies were introduced.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R1 | Project sponsor rotation | High | Medium | Accept risk; monitor weekly in status meetings to ensure new sponsor alignment. | Rumi Gupta |
| R2 | Scope creep (Stakeholder 'small' features) | High | High | Assign a dedicated owner to track all requests in JIRA; reject any feature not in the original spec. | Mosi Jensen |
| R3 | Infrastructure provisioning delays | Medium | High | Maintain a secondary cloud provider (Azure) as a fallback if Heroku Private Space setup fails. | Luna Fischer |
| R4 | Data Migration Failure (Legacy Tools) | Medium | High | Perform incremental data migrations in staging before the final production cut-over. | Xena Stein |
| R5 | ISO 27001 Audit Failure | Low | Critical | Weekly security audits of the environment and strict adherence to the manual QA gate. | Luna Fischer |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **High/Medium:** Closely monitored.
- **Low/Critical:** Preventive measures implemented.

---

## 9. TIMELINE AND PHASES

The project follows a phased approach with a total duration from conception to MVP of approximately 10 months.

### Phase 1: Foundation (Now – 2026-04-15)
- **Objective:** Establish the core monolith and data models.
- **Key Deliverables:**
    - Modular monolith setup.
    - MySQL schema implementation.
    - Basic API authentication.
- **Milestone 1:** Architecture review complete (**Target: 2026-04-15**).

### Phase 2: Critical Feature Development (2026-04-16 – 2026-06-15)
- **Objective:** Build the launch-blocking features.
- **Key Deliverables:**
    - Webhook integration framework.
    - Offline-first sync engine.
    - Virus scanning pipeline.
- **Milestone 2:** Stakeholder demo and sign-off (**Target: 2026-06-15**).

### Phase 3: Refinement and MVP (2026-06-16 – 2026-08-15)
- **Objective:** Finalize the API and A/B testing frameworks.
- **Key Deliverables:**
    - Public API v1 launch.
    - A/B testing system (pending ISO audit).
    - Final data migration from 4 legacy tools.
- **Milestone 3:** MVP feature-complete (**Target: 2026-08-15**).

**Dependencies:**
- Webhook Framework $\rightarrow$ Dependent on API Gateway completion.
- Offline Sync $\rightarrow$ Dependent on Database Schema finalization.
- MVP Launch $\rightarrow$ Dependent on ISO 27001 certification of the Prod environment.

---

## 10. MEETING NOTES

### Meeting 1: Initial Architecture Sync (2025-11-05)
- **Attendees:** Rumi, Luna, Mosi, Xena.
- **Notes:**
    - Monolith vs Microservices? $\rightarrow$ Monolith for speed.
    - Heroku chosen.
    - Date formats in legacy tools are a mess. 3 different formats.
    - Action: Xena to research normalization gems.

### Meeting 2: Webhook Framework Brainstorm (2025-12-12)
- **Attendees:** Rumi, Luna, Xena.
- **Notes:**
    - Need HMAC for security.
    - Use Sidekiq for retries.
    - Concern: What if the partner endpoint is slow? $\rightarrow$ Use async jobs.
    - Status: Critical blocker.

### Meeting 3: Stakeholder Review - Scope Check (2026-01-20)
- **Attendees:** Rumi, Mosi, Stakeholders.
- **Notes:**
    - Stakeholders want "Quick-Export to Excel" added.
    - Rumi: Not in spec.
    - Mosi: Will track in JIRA as "Potential Phase 2".
    - Sponsor rotating out soon? $\rightarrow$ Monitor weekly.

---

## 11. BUDGET BREAKDOWN

Since Project Ember is **unfunded** and bootstrapped, the "budget" represents the internal cost of labor and existing infrastructure allocations.

| Category | Description | Allocated Amount (Internal Value) |
| :--- | :--- | :--- |
| **Personnel** | 20+ staff across 3 depts (Approx 20% capacity) | $450,000 (Estimated labor cost) |
| **Infrastructure** | Heroku Private Space, AWS S3, CloudFront | $18,000 / year |
| **Tools** | New Relic, Papertrail, JIRA Premium | $4,500 / year |
| **Contingency** | Buffer for emergency cloud scaling | $5,000 |
| **TOTAL** | **Total Internal Investment** | **$477,500** |

*Note: All amounts are based on internalized costs of existing employee salaries and current software subscriptions.*

---

## 12. APPENDICES

### Appendix A: Legacy Date Format Normalization Table
The technical debt identified in the codebase involves three competing date formats. The `DateNormalizationService` will be implemented to map these to ISO8601.

| Legacy Tool | Format | Example | Normalized Format |
| :--- | :--- | :--- | :--- |
| Tool A (Health) | MM/DD/YYYY | 12/01/2023 | YYYY-MM-DD |
| Tool B (Safety) | DD-MM-YYYY | 01-12-2023 | YYYY-MM-DD |
| Tool C (Vaccine) | YYYY/MM/DD | 2023/12/01 | YYYY-MM-DD |
| Tool D (General) | Epoch Timestamp | 1701424800 | YYYY-MM-DD |

### Appendix B: ISO 27001 Compliance Checklist for Ember
The following must be verified by Luna Fischer before the Production promotion:
- [ ] **Encryption:** All MySQL volumes encrypted at rest?
- [ ] **Access Control:** IAM roles strictly limited to Rumi and Luna?
- [ ] **Logging:** All `GET /records/{id}` calls logged to `audit_logs`?
- [ ] **Network:** Production subnet isolated from Dev/Staging?
- [ ] **Backup:** Successfully tested a restore from a snapshot in the last 30 days?
- [ ] **Scanning:** ClamAV successfully detecting test EICAR strings?