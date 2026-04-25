# PROJECT SPECIFICATION DOCUMENT: PROJECT EMBER (v1.0.4)

**Document Status:** Active / Working Draft  
**Date:** October 24, 2025  
**Project Lead:** Dante Fischer, Engineering Manager  
**Company:** Clearpoint Digital  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Ember is a greenfield initiative by Clearpoint Digital to develop a high-performance healthcare records platform. While Clearpoint Digital has a storied history of success in the logistics and shipping industry—specializing in supply chain optimization and freight tracking—Ember represents a strategic pivot into the healthcare sector. This is a high-risk, high-reward venture, as the company is entering a market where it has no prior operational experience, no established client base, and no domain-specific legacy code.

**Business Justification**  
The decision to enter the healthcare records space is driven by the increasing convergence of logistics and health services (e.g., pharmaceutical supply chain integration and medical equipment tracking). By leveraging Clearpoint’s expertise in "moving things from point A to point B," Ember seeks to apply those logistical efficiencies to the movement and management of patient health records. The goal is to create a lightweight, agile platform that can bridge the gap between clinical data and administrative logistics.

**Financial Constraints & ROI Projection**  
Ember is operating on a "shoestring" budget of $150,000. This budget is strictly capped; every dollar is under intense scrutiny by the executive board. Consequently, the project relies on a lean, remote-first team and self-hosted infrastructure to minimize recurring SaaS costs.

The projected ROI is based on a "land and expand" strategy. By targeting 10,000 monthly active users (MAU) within six months of launch, Clearpoint Digital anticipates a transition from a free pilot phase to a tiered subscription model. Based on a conservative Average Revenue Per User (ARPU) of $1.50/month, the company projects a monthly recurring revenue (MRR) of $15,000, achieving a total break-even on the initial $150,000 investment within 10 months of launch, excluding ongoing maintenance costs.

**Strategic Objectives**  
1. Establish a foothold in the healthcare market.
2. Validate the applicability of logistics-based data orchestration in a clinical setting.
3. Develop a scalable, serverless-inspired architecture that can be pivoted based on pilot user feedback.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Ember utilizes a modern, asynchronous stack designed for high throughput and low latency. Despite being "self-hosted," the architecture mimics a serverless environment using API Gateway orchestration to trigger discrete Python/FastAPI functions.

**The Stack:**
- **Language:** Python 3.11 (FastAPI)
- **Database:** MongoDB (NoSQL for flexibility in health record schemas)
- **Task Queue:** Celery with Redis as the broker
- **Containerization:** Docker Compose (Orchestrating the app, DB, and workers)
- **Infrastructure:** Self-hosted on private VPS clusters.

### 2.2 Architectural Diagram (ASCII)

```text
[ Client Layer ]          [ Gateway Layer ]          [ Logic Layer ]          [ Data Layer ]
+----------------+       +-------------------+       +------------------+      +----------------+
| Web Dashboard  | ----> | API Gateway       | ----> | FastAPI Service A | ---> | MongoDB Cluster |
| (React/Tailwind)|       | (Nginx/Custom)    |       | (Patient Records) |      | (Patient Data)  |
+----------------+       +---------+---------+       +---------+--------+      +----------------+
                                  |                               ^
                                  | (Async Trigger)               | (State)
                                  v                               |
                         +-------------------+       +------------------+      +----------------+
                         | Celery Worker     | <--- | Background Task  | <--- | Redis Cache     |
                         | (Report Gen/Sync) |       | (Scheduled Job)  |      | (Task Queue)    |
                         +-------------------+       +------------------+      +----------------+
```

**Description:**
The Client Layer communicates via HTTPS to the API Gateway. The Gateway acts as the orchestrator, routing requests to specific FastAPI micro-functions. For long-running tasks (like PDF generation), the Gateway pushes a message to the Redis queue, which is picked up by a Celery worker. The worker interacts with MongoDB to pull the required records and then pushes the final artifact to the storage layer.

### 2.3 Deployment Strategy
The deployment process is currently a critical point of failure. We employ a "manual push" strategy managed by a single DevOps engineer. 
- **Bus Factor:** 1. If the DevOps engineer is unavailable, deployment ceases.
- **CI/CD Pipeline:** The pipeline is currently unoptimized, taking approximately 45 minutes to complete a single build/test cycle due to sequential execution and lack of caching.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation (Priority: High | Status: Complete)
**Description:** This feature allows healthcare providers to generate comprehensive patient summaries or administrative audits in PDF and CSV formats. These reports can be delivered immediately or scheduled for future delivery via email.

**Functional Requirements:**
- **Export Engine:** Uses `ReportLab` for PDF generation and `Pandas` for CSV formatting.
- **Scheduling:** Uses Celery Beat to trigger reports at specific intervals (Daily, Weekly, Monthly).
- **Delivery:** Integration with an SMTP relay to send reports to authorized personnel.
- **Templating:** Support for dynamic templates based on the report type (e.g., "Patient History" vs "Billing Summary").

**Technical Constraints:**
Reports are generated in the background to prevent API timeouts. Once the Celery worker completes the report, a notification is sent to the frontend via a WebSocket trigger.

**Success Criteria:**
- PDFs must render in under 5 seconds for records under 100 pages.
- CSVs must support UTF-8 encoding to prevent character corruption in international names.

### 3.2 Localization and Internationalization (Priority: Medium | Status: Complete)
**Description:** Ember supports 12 distinct languages to accommodate the global nature of healthcare logistics. This includes translation of the UI, date/time formatting, and currency conversion.

**Supported Languages:**
English, Spanish, French, German, Mandarin, Japanese, Arabic, Portuguese, Russian, Hindi, Korean, and Italian.

**Implementation Details:**
- **i18n Framework:** Utilizes `gettext` and a custom JSON-based translation map stored in MongoDB.
- **Dynamic Loading:** The frontend detects the browser's `Accept-Language` header and loads the corresponding locale file.
- **RTL Support:** The UI supports Right-to-Left (RTL) mirroring for Arabic.

**Constraint:**
All translations are currently managed via a static JSON file. Updates to translations require a deployment cycle, which is slowed by the 45-minute CI pipeline.

### 3.3 Offline-First Mode with Background Sync (Priority: Low | Status: In Design)
**Description:** This "nice to have" feature ensures that clinicians in low-connectivity environments can continue entering data without interruption.

**Proposed Workflow:**
- **Local Storage:** Use IndexedDB in the browser to cache record entries.
- **Conflict Resolution:** A "last-write-wins" strategy will be implemented initially, with a manual resolution screen for critical data conflicts.
- **Sync Engine:** A background service worker will poll for connectivity and push queued changes to the `/sync` endpoint.

**Design Challenges:**
The primary challenge is maintaining data integrity across 12 different languages while syncing. We must ensure that localized strings are not overwritten by the system default during a sync event.

### 3.4 Customizable Dashboard (Priority: Medium | Status: In Design)
**Description:** A drag-and-drop interface allowing users to organize "widgets" (e.g., Patient Volume, Pending Reports, Critical Alerts) based on their specific role.

**Proposed Implementation:**
- **Frontend:** `react-grid-layout` for the drag-and-drop functionality.
- **Persistence:** Dashboard layouts are stored as JSON blobs in the `user_preferences` MongoDB collection.
- **Widget API:** Each widget is a standalone component that calls a specific API endpoint to fetch its data.

**Product vs. Engineering Disagreement:**
Currently, there is a blocker regarding the dashboard. The Product Lead wants a fully "free-form" canvas, while the Engineering Lead (Dante Fischer) argues for a "grid-based" system to maintain responsiveness and accessibility standards.

### 3.5 API Rate Limiting & Usage Analytics (Priority: Critical | Status: In Progress)
**Description:** To prevent system collapse and enable future monetization, this feature implements strict limits on how many requests a user or organization can make per minute.

**Functional Requirements:**
- **Limiters:** Implemented using a "leaky bucket" algorithm via Redis.
- **Tiers:** 
    - *Trial:* 100 requests/min.
    - *Pilot:* 1,000 requests/min.
    - *Enterprise:* Unlimited.
- **Analytics:** Logging every request to a `usage_logs` collection to track feature adoption.

**Launch Blocker Status:**
This is a critical launch blocker. Without rate limiting, the self-hosted infrastructure is vulnerable to DDoS attacks or accidental recursive loops from client-side code.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 Get Patient Record
- **Path:** `GET /records/{patient_id}`
- **Description:** Retrieves the full health record for a specific patient.
- **Request:** `patient_id` (UUID)
- **Response:** `200 OK`
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Doe",
  "records": [{"date": "2025-01-10", "diagnosis": "Hypertension", "notes": "Stable"}],
  "locale": "en-US"
}
```

### 4.2 Create Report Request
- **Path:** `POST /reports/generate`
- **Description:** Triggers the generation of a PDF or CSV report.
- **Request Body:**
```json
{
  "type": "PDF",
  "patient_ids": ["id1", "id2"],
  "schedule": "immediate",
  "email": "admin@clinic.org"
}
```
- **Response:** `202 Accepted` (Returns a `job_id` for tracking).

### 4.3 Update Patient Info
- **Path:** `PATCH /records/{patient_id}`
- **Description:** Updates specific fields of a patient record.
- **Request Body:** `{"phone": "+1-555-0199"}`
- **Response:** `200 OK`

### 4.4 Get User Dashboard Layout
- **Path:** `GET /user/preferences/dashboard`
- **Description:** Fetches the saved widget layout for the authenticated user.
- **Response:** `200 OK`
```json
{
  "layout": [{"i": "widget1", "x": 0, "y": 0, "w": 2, "h": 2}, {"i": "widget2", "x": 2, "y": 0, "w": 2, "h": 2}]
}
```

### 4.5 Update Dashboard Layout
- **Path:** `PUT /user/preferences/dashboard`
- **Description:** Saves the current widget arrangement.
- **Request Body:** JSON layout object.
- **Response:** `204 No Content`

### 4.6 Get API Usage Stats
- **Path:** `GET /analytics/usage`
- **Description:** Returns the current month's request count for the user.
- **Response:** `200 OK`
```json
{
  "total_requests": 4500,
  "limit": 10000,
  "percentage_used": "45%"
}
```

### 4.7 Set User Locale
- **Path:** `POST /user/settings/locale`
- **Description:** Updates the preferred language for the user interface.
- **Request Body:** `{"language_code": "fr-FR"}`
- **Response:** `200 OK`

### 4.8 Sync Offline Data
- **Path:** `POST /sync`
- **Description:** Batch updates records from the offline cache.
- **Request Body:** Array of record updates with timestamps.
- **Response:** `200 OK` (Returns list of conflicts encountered).

---

## 5. DATABASE SCHEMA (MongoDB)

Because Ember uses MongoDB, the "tables" are described as collections with flexible schemas.

### 5.1 Collection: `patients`
- **_id:** ObjectId (Primary Key)
- **patient_uuid:** UUID (Unique Index)
- **first_name:** String
- **last_name:** String
- **dob:** Date
- **gender:** String
- **contact_info:** Object {phone: String, email: String}
- **created_at:** Timestamp
- **updated_at:** Timestamp

### 5.2 Collection: `medical_records`
- **_id:** ObjectId
- **patient_id:** ObjectId (Foreign Key $\rightarrow$ patients)
- **provider_id:** ObjectId (Foreign Key $\rightarrow$ users)
- **visit_date:** Date
- **diagnosis:** String
- **treatment_plan:** String
- **medications:** Array [String]
- **clinical_notes:** String
- **version:** Integer (For optimistic locking)

### 5.3 Collection: `users`
- **_id:** ObjectId
- **username:** String (Unique)
- **password_hash:** String
- **role:** Enum (Admin, Provider, Viewer)
- **department:** String
- **email:** String
- **mfa_enabled:** Boolean

### 5.4 Collection: `user_preferences`
- **_id:** ObjectId
- **user_id:** ObjectId (Foreign Key $\rightarrow$ users)
- **locale:** String (e.g., "en-GB")
- **timezone:** String
- **dashboard_config:** JSON Blob
- **theme:** Enum (Light, Dark, System)

### 5.5 Collection: `reports`
- **_id:** ObjectId
- **requested_by:** ObjectId (Foreign Key $\rightarrow$ users)
- **report_type:** Enum (PDF, CSV)
- **status:** Enum (Pending, Processing, Completed, Failed)
- **file_url:** String (Path to storage)
- **scheduled_for:** Date (Nullable)
- **created_at:** Timestamp

### 5.6 Collection: `usage_logs`
- **_id:** ObjectId
- **user_id:** ObjectId
- **endpoint_accessed:** String
- **timestamp:** Date
- **response_time_ms:** Integer
- **status_code:** Integer

### 5.7 Collection: `audit_trails`
- **_id:** ObjectId
- **actor_id:** ObjectId
- **action:** String (e.g., "UPDATE_RECORD")
- **target_id:** ObjectId
- **previous_value:** JSON
- **new_value:** JSON
- **timestamp:** Date

### 5.8 Collection: `organizations`
- **_id:** ObjectId
- **org_name:** String
- **subscription_tier:** Enum (Trial, Pilot, Enterprise)
- **billing_email:** String
- **api_key:** String (Hashed)

### 5.9 Collection: `notification_queue`
- **_id:** ObjectId
- **recipient_id:** ObjectId
- **message:** String
- **type:** Enum (Alert, ReportReady, System)
- **is_read:** Boolean
- **created_at:** Timestamp

### 5.10 Collection: `sync_sessions`
- **_id:** ObjectId
- **device_id:** String
- **user_id:** ObjectId
- **last_sync_timestamp:** Date
- **pending_changes_count:** Integer

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

**Development (Dev):**
- **Host:** Local machines (Docker Compose) and a shared "Dev-Box" VPS.
- **Purpose:** Feature development and initial integration testing.
- **Database:** Local MongoDB instance with seed data.
- **Deployment:** Pushed directly to the Dev-Box by developers.

**Staging (Staging):**
- **Host:** Dedicated VPS cluster mimicking production.
- **Purpose:** QA testing (Hessa Oduya's domain) and User Acceptance Testing (UAT).
- **Database:** A sanitized copy of production data.
- **Deployment:** Triggered via the 45-minute CI pipeline.

**Production (Prod):**
- **Host:** High-availability self-hosted cluster with load balancing.
- **Purpose:** Live user traffic.
- **Database:** MongoDB Replica Set for failover.
- **Deployment:** Manual deployment by the single DevOps person.

### 6.2 Infrastructure Constraints
The "self-hosted" nature of the project is a cost-saving measure to stay within the $150,000 budget. This means we do not have the auto-scaling capabilities of AWS or Azure. If traffic spikes beyond the capacity of the current VPS, the system will experience latency until the DevOps engineer manually provisions more resources.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Coverage Target:** 70%
- **Approach:** Every FastAPI endpoint must have a corresponding unit test that mocks the MongoDB connection. Tests are run sequentially in the CI pipeline, contributing to the 45-minute delay.

### 7.2 Integration Testing
- **Focus:** Testing the interaction between the FastAPI services and the Celery workers.
- **Approach:** Spin up a Docker Compose environment, trigger a report generation, and poll the database to verify the report status changes from `Pending` $\rightarrow$ `Completed`.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright
- **Scope:** Critical paths only (e.g., User Login $\rightarrow$ Create Record $\rightarrow$ Generate Report $\rightarrow$ Logout).
- **Frequency:** Performed by Hessa Oduya on the Staging environment before every Internal Alpha or External Beta release.

### 7.4 Penetration Testing
Since there is no formal compliance framework (like HIPAA or GDPR) currently implemented, the company relies on **Quarterly Penetration Testing**. An external security firm is hired every three months to attempt to breach the API and identify vulnerabilities.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding "small" features | High | High | **Parallel-Path:** Prototype an alternative approach simultaneously to show the cost/time tradeoff of the new request. |
| R-02 | Key architect leaving the company in 3 months | Medium | Critical | **External Audit:** Engage an external consultant for an independent assessment and documentation handover. |
| R-03 | CI Pipeline bottleneck (45 min build) | High | Medium | **Parallelization:** Future sprint item to move from sequential to parallel test execution. |
| R-04 | Single point of failure (DevOps person) | Medium | High | **Cross-Training:** Document deployment steps in a "Runbook" for Dante Fischer to follow. |
| R-05 | Budget exhaustion | Medium | High | **Strict Scrutiny:** Weekly budget review with the project lead to ensure no "hidden" costs. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundation (Current - April 2026)
- **Focus:** Core API development, DB schema finalization, and localization.
- **Dependencies:** Architecture review must be signed off.
- **Milestone 1:** Architecture review complete $\rightarrow$ **Target: 2026-04-15**

### 9.2 Phase 2: Alpha Integration (April 2026 - June 2026)
- **Focus:** Report generation, Dashboard prototypes, and Rate Limiting.
- **Dependencies:** Completion of Feature 5 (Rate Limiting) as it is a launch blocker.
- **Milestone 2:** Internal alpha release $\rightarrow$ **Target: 2026-06-15**

### 9.3 Phase 3: Beta Expansion (June 2026 - August 2026)
- **Focus:** Offline-first mode and pilot user onboarding.
- **Dependencies:** Successful internal alpha and stability of the self-hosted cluster.
- **Milestone 3:** External beta with 10 pilot users $\rightarrow$ **Target: 2026-08-15**

---

## 10. MEETING NOTES

*Note: These notes are extracted from the 200-page shared running document. The original document is unsearchable and non-indexed.*

### Meeting 1: Sprint Planning & Scope Conflict
**Date:** 2025-11-02  
**Attendees:** Dante Fischer, Idris Park, Hessa Oduya  
**Discussion:**
- Idris (Frontend) expressed concern that the current "Customizable Dashboard" requirements are too vague.
- Dante (Engineering) emphasized that we cannot afford a fully fluid layout due to the shoestring budget and the need for rapid development.
- **Decision:** The team will move toward a grid-based system. However, Product still disagrees, leading to the current "Blocker" status.

### Meeting 2: The "Bus Factor" Crisis
**Date:** 2025-11-15  
**Attendees:** Dante Fischer, DevOps Lead  
**Discussion:**
- Dante raised the issue of the 45-minute CI pipeline. The DevOps lead stated that the build server is underpowered.
- Discussion on the key architect's impending departure.
- **Decision:** We will not buy a new server (budget restriction). Instead, we will hire an external consultant for a one-time assessment of the architecture to ensure continuity.

### Meeting 3: Localization Review
**Date:** 2025-12-01  
**Attendees:** Idris Park, Kian Moreau  
**Discussion:**
- Kian (Junior Dev) reported bugs in the Arabic RTL mirroring.
- Idris noted that the JSON translation files are becoming too large and are slowing down the frontend load time.
- **Decision:** For now, we will keep the JSON files but will implement a "lazy-load" mechanism for locales that aren't currently active.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000  
**Currency:** USD

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Covers part-time allocations for the 20+ person team across 3 departments. |
| **Infrastructure** | 20% | $30,000 | Self-hosted VPS leases, Redis/MongoDB storage costs. |
| **External Tools** | 10% | $15,000 | Penetration testing fees, external consultant assessment. |
| **Contingency** | 10% | $15,000 | Reserved for emergency hardware failure or critical bugs. |

*Budget Note: All expenditures over $500 must be approved by Dante Fischer and the finance department.*

---

## 12. APPENDICES

### Appendix A: Celery Task Workflow
The report generation process follows a strict state machine to ensure reliability:
1. **State: PENDING** $\rightarrow$ Request received via `/reports/generate`.
2. **State: PROCESSING** $\rightarrow$ Celery worker picks up the task and queries MongoDB.
3. **State: RENDERING** $\rightarrow$ ReportLab converts data to PDF.
4. **State: DELIVERING** $\rightarrow$ SMTP relay sends the email.
5. **State: COMPLETED/FAILED** $\rightarrow$ Final state updated in the `reports` collection.

### Appendix B: Performance Benchmarks
To ensure the system can handle the goal of 10,000 MAU, the following benchmarks have been established for the self-hosted environment:
- **API Response Time:** $\le$ 200ms for 95% of requests.
- **DB Query Time:** $\le$ 50ms for indexed lookups on `patient_uuid`.
- **Max Concurrent Users:** 150 concurrent requests per second (RPS) before latency exceeds 1 second.
- **CI Pipeline Duration:** Currently 45 minutes (Target: 10 minutes).