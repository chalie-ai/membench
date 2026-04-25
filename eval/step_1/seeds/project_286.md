# PROJECT SPECIFICATION: PROJECT LATTICE
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Status:** Draft/Active  
**Classification:** Confidential – Nightjar Systems Internal  
**Owner:** Olga Gupta (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Lattice is a strategic moonshot R&D initiative commissioned by Nightjar Systems. The primary objective is to migrate the company’s legacy monolithic real estate management system into a modern, scalable microservices architecture governed by a centralized API Gateway. In the highly competitive real estate sector, the ability to pivot rapidly—integrating new listing APIs, managing cross-border properties, and automating tenant workflows—is a critical differentiator. Lattice is designed to transform our rigid infrastructure into a fluid, "lattice-like" network of decoupled services that can be scaled independently based on demand.

### 1.2 Business Justification
The current monolithic architecture at Nightjar Systems has reached a point of critical fragility. Deployment cycles are slow, and a single bug in the billing module can bring down the entire listing engine. As Nightjar Systems expands into international markets, the lack of localization and the inability to handle region-specific data residency laws (GDPR, CCPA) have become significant business risks. 

Project Lattice addresses these pain points by implementing a Hexagonal Architecture (Ports and Adapters). By decoupling the core business logic from external dependencies (databases, third-party APIs, and UI frameworks), Nightjar can swap out a PostgreSQL instance for a specialized graph database or integrate a new SMS provider without rewriting the core domain logic.

### 1.3 ROI Projection and "Moonshot" Nature
Lattice is explicitly categorized as a "moonshot" project. This means the immediate Return on Investment (ROI) is uncertain and potentially negative in the first 18 months due to the high cost of migration and the lack of immediate new feature delivery. However, the long-term ROI is projected based on three vectors:
1. **Operational Efficiency:** Reducing the "Time to Market" for new features from 6 weeks to 1 week.
2. **Infrastructure Cost Optimization:** Using canary releases and Vercel’s serverless functions to reduce idle server costs by an estimated 30%.
3. **Risk Mitigation:** Achieving ISO 27001 certification, which is a prerequisite for securing high-value institutional real estate contracts worth an estimated $5M in annual recurring revenue (ARR).

While the immediate financial gain is speculative, the strategic value of technical agility and security compliance makes this a priority for executive sponsorship.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Hexagonal Pattern (Ports and Adapters)
Project Lattice utilizes a Hexagonal Architecture to ensure that the business logic (the "Core") remains agnostic of the delivery mechanism and the data storage layer.

- **The Core:** Contains the domain entities and business rules (e.g., Lease Calculation Logic, Property Valuation).
- **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IPropertyRepository`, `INotificationService`).
- **Adapters:** Concrete implementations of ports (e.g., `PrismaPropertyRepository` for PostgreSQL, `TwilioSmsAdapter` for SMS).

### 2.2 Technology Stack
- **Language:** TypeScript 5.2 (Strict Mode)
- **Frontend/BFF:** Next.js 14 (App Router)
- **ORM:** Prisma 5.x
- **Database:** PostgreSQL 15 (Managed via Vercel Postgres/AWS RDS)
- **Hosting:** Vercel (Frontend and Serverless Functions)
- **Feature Management:** LaunchDarkly
- **Security:** ISO 27001 Compliant VPC and IAM roles

### 2.3 System Diagram (ASCII Representation)
```text
[ Client: Web/Mobile ] 
       |
       v
[ API Gateway / Next.js Middleware ] <---> [ LaunchDarkly (Feature Flags) ]
       |
       +---------------------------------------+
       |                                       |
[ Service: Notifications ]             [ Service: Property Mgmt ]
       |                                       |
  ( Ports )                              ( Ports )
       |                                       |
 [ Adapters: SendGrid, Twilio ]          [ Adapters: Prisma, PostgreSQL ]
       |                                       |
       +------------------+--------------------+
                          |
                  [ ISO 27001 Secure Cloud ]
```

### 2.4 Infrastructure Strategy
The system will utilize a **Canary Release** strategy. When a new version of a microservice is deployed, Vercel will route 5% of traffic to the new version. Performance metrics (p95 response time) will be monitored via Prometheus. If the error rate remains <0.1%, traffic will be incremented by 25% every hour until 100% saturation is reached.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
Real estate platforms require the handling of massive amounts of imagery, legal PDFs, and tenant documentation. To prevent the upload of malicious payloads, Lattice implements a "Secure Ingest Pipeline."

**Functional Requirements:**
- **Upload Path:** Users upload files via a signed URL generated by the API Gateway to avoid overloading the application server.
- **Scanning Layer:** Every uploaded file is intercepted by a ClamAV-based scanning microservice. Files are held in a "Quarantine" S3 bucket until a `CLEAN` signal is received.
- **CDN Distribution:** Once cleared, files are moved to a "Public/Private" production bucket and cached via the Vercel Edge Network (CDN) for low-latency retrieval globally.
- **Virus Scanning Logic:** If a virus is detected, the file is deleted immediately, and a security event is logged in the `audit_logs` table. The user is notified via the Notification System.

**Technical Implementation:**
The feature uses a `FileAdapter` port. The current implementation uses an AWS S3 adapter. The virus scanning is handled by an asynchronous Lambda function triggered by S3 `PutObject` events.

---

### 3.2 Notification System (Email, SMS, In-App, Push)
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
A centralized notification engine that decouples the trigger (e.g., "Lease Signed") from the delivery method (e.g., "Push Notification").

**Functional Requirements:**
- **Multi-Channel Delivery:** Support for SendGrid (Email), Twilio (SMS), Firebase Cloud Messaging (Push), and a WebSocket-based in-app notification center.
- **Preference Management:** Users must be able to opt-in/out of specific channels per notification category (e.g., "Billing Alerts" via Email only).
- **Template Engine:** A Handlebars-based templating system that allows the marketing team to update email copy without developer intervention.
- **Priority Queuing:** "Critical" notifications (e.g., Password Reset) bypass the standard queue and are processed by a dedicated "High Priority" worker.

**Technical Specification:**
The system implements a `NotificationDispatcher` that queries the `user_notification_preferences` table. It then iterates through the enabled channels and calls the respective adapters.
- **Endpoint:** `POST /api/v1/notifications/dispatch`
- **Retry Logic:** Exponential backoff for failed SMS delivery (3 attempts).

---

### 3.3 Localization and Internationalization (12 Languages)
**Priority:** High | **Status:** In Review

**Description:**
To support the global expansion of Nightjar Systems, the platform must support 12 primary languages, including Right-to-Left (RTL) support for Arabic and Hebrew.

**Functional Requirements:**
- **Dynamic Translation:** Use of `next-intl` for client-side translations and a PostgreSQL-backed translation table for dynamic content (e.g., property descriptions).
- **Regional Formatting:** Automatic formatting of currency, dates, and addresses based on the user's `locale` setting.
- **Language Detection:** Auto-detection based on the `Accept-Language` header with a fallback to English (US).
- **Supported Languages:** English, Spanish, French, German, Chinese (Simplified), Japanese, Korean, Arabic, Hebrew, Portuguese, Italian, and Russian.

**Technical Implementation:**
Translations are stored in JSON files for static UI elements and a `translations` table for dynamic content.
- **Schema:** `translations` table linked by `key`, `locale`, and `namespace`.
- **Caching:** Translation bundles are cached at the Edge to prevent database round-trips for every page load.

---

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** Not Started

**Description:**
A "No-Code" engine allowing real estate agents to create automation rules (e.g., "If property status changes to 'Rented', then send email to Owner and Archive Listing").

**Functional Requirements:**
- **Visual Builder:** A drag-and-drop interface using React Flow to map triggers to actions.
- **Trigger System:** Event-based triggers sourced from the API Gateway (e.g., `PROPERTY_UPDATED`, `PAYMENT_RECEIVED`).
- **Action Library:** A set of predefined actions (Send Email, Update Database, Trigger Webhook).
- **Condition Logic:** Support for complex Boolean logic (AND/OR) within the rule builder.

**Technical Specification:**
The engine will use a JSON-based Domain Specific Language (DSL) to represent workflows. A `WorkflowExecutor` service will parse these JSON definitions and execute the sequence of ports/adapters.
- **Example Rule:** `{ trigger: "payment_late", condition: "days_overdue > 5", action: "send_sms_reminder" }`

---

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** Not Started

**Description:**
A utility for migrating property data from legacy CSV, XML, and JSON files into the Lattice ecosystem.

**Functional Requirements:**
- **Auto-Detection:** The system must analyze the first 10 lines of a file to determine the format (CSV, JSON, XML) and the encoding (UTF-8, Latin-1).
- **Schema Mapping:** A tool allowing users to map source columns (e.g., "Street_Addr") to Lattice fields (e.g., `property_address`).
- **Bulk Processing:** Background processing using a queue (BullMQ) to handle files with up to 100,000 records without timing out the HTTP request.
- **Validation Report:** A post-import report highlighting rows that failed validation due to type mismatches.

**Technical Specification:**
The implementation will use a `DataIngestionAdapter`. The pipeline will involve: `Upload` $\to$ `Detect Format` $\to$ `Validate Schema` $\to$ `Bulk Insert (Prisma)`.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`.

### 4.1 `POST /api/v1/properties`
**Description:** Creates a new real estate listing.
- **Request Body:**
  ```json
  {
    "title": "Luxury Penthouse",
    "price": 1200000,
    "address": "123 Sky Lane, NY",
    "locale": "en-US"
  }
  ```
- **Response (201 Created):**
  ```json
  { "id": "prop_8821", "status": "active", "createdAt": "2023-10-26T10:00:00Z" }
  ```

### 4.2 `GET /api/v1/properties/{id}`
**Description:** Retrieves detailed property information.
- **Response (200 OK):**
  ```json
  { "id": "prop_8821", "title": "Luxury Penthouse", "p95_load_time": "140ms" }
  ```

### 4.3 `POST /api/v1/notifications/send`
**Description:** Dispatches a notification via the specified channel.
- **Request Body:**
  ```json
  {
    "userId": "user_44",
    "channel": "sms",
    "templateId": "payment_reminder",
    "data": { "amount": "$1,200", "dueDate": "2023-11-01" }
  }
  ```
- **Response (202 Accepted):** `{ "jobId": "job_abc123", "status": "queued" }`

### 4.4 `PATCH /api/v1/users/{id}/preferences`
**Description:** Updates localization and notification settings.
- **Request Body:**
  ```json
  { "language": "fr-FR", "notifications": { "email": true, "sms": false } }
  ```
- **Response (200 OK):** `{ "status": "updated" }`

### 4.5 `POST /api/v1/files/upload-url`
**Description:** Generates a signed S3 URL for secure file upload.
- **Request Body:** `{ "fileName": "contract.pdf", "fileSize": 2048000 }`
- **Response (200 OK):** `{ "uploadUrl": "https://s3.amazon.com/...", "fileId": "file_xyz" }`

### 4.6 `GET /api/v1/files/{id}/status`
**Description:** Checks if a file has passed virus scanning.
- **Response (200 OK):** `{ "fileId": "file_xyz", "scanStatus": "CLEAN", "cdnUrl": "https://cdn.nightjar.com/..." }`

### 4.7 `POST /api/v1/workflows/create`
**Description:** Saves a new automation rule.
- **Request Body:** `{ "name": "Late Pay Alert", "definition": { "trigger": "payment_late", "action": "sms" } }`
- **Response (201 Created):** `{ "workflowId": "wf_99" }`

### 4.8 `GET /api/v1/billing/summary`
**Description:** Retrieves billing data (Note: High technical debt in this module).
- **Response (200 OK):** `{ "totalOwed": 5000, "currency": "USD", "warning": "No test coverage for this endpoint" }`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15. All tables utilize UUIDs as primary keys.

### 5.1 Table Definitions

1.  **`users`**: Stores core identity data.
    - `id` (UUID, PK), `email` (String, Unique), `password_hash` (String), `created_at` (Timestamp).
2.  **`profiles`**: User metadata and localization.
    - `id` (UUID, PK), `user_id` (FK $\to$ users), `full_name` (String), `locale` (String, default 'en-US'), `timezone` (String).
3.  **`properties`**: Real estate listing data.
    - `id` (UUID, PK), `owner_id` (FK $\to$ users), `title` (String), `price` (Decimal), `status` (Enum: active, pending, rented).
4.  **`property_details`**: Extended attributes (Hexagonal adapter target).
    - `property_id` (FK $\to$ properties), `sq_ft` (Integer), `bedrooms` (Integer), `bathrooms` (Integer).
5.  **`notifications`**: Audit trail of sent messages.
    - `id` (UUID, PK), `user_id` (FK $\to$ users), `channel` (Enum: email, sms, push, in_app), `message_body` (Text), `sent_at` (Timestamp).
6.  **`user_notification_preferences`**: User opt-in settings.
    - `user_id` (FK $\to$ users, PK), `channel` (String, PK), `enabled` (Boolean).
7.  **`files`**: Metadata for uploaded documents.
    - `id` (UUID, PK), `uploader_id` (FK $\to$ users), `s3_key` (String), `scan_status` (Enum: pending, clean, infected), `mime_type` (String).
8.  **`translations`**: Localization mapping.
    - `id` (UUID, PK), `namespace` (String), `key` (String), `locale` (String), `translation` (Text).
9.  **`workflows`**: Automation definitions.
    - `id` (UUID, PK), `creator_id` (FK $\to$ users), `dsl_definition` (JSONB), `is_active` (Boolean).
10. **`billing_accounts`**: Financial tracking (The high-debt module).
    - `id` (UUID, PK), `user_id` (FK $\to$ users), `balance` (Decimal), `last_payment_date` (Timestamp).

### 5.2 Relationships
- `users` $\to$ `profiles` (1:1)
- `users` $\to$ `properties` (1:N)
- `users` $\to$ `notifications` (1:N)
- `users` $\to$ `user_notification_preferences` (1:N)
- `properties` $\to$ `property_details` (1:1)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Topology
Lattice utilizes three distinct environments to ensure stability and ISO 27001 compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature branching.
- **Deployment:** Automatic deploy on every push to `feature/*` branches.
- **Database:** Shared Dev PostgreSQL instance with mocked data.
- **Security:** Low restriction; developers have full DB access.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and QA.
- **Deployment:** Deployed from the `develop` branch.
- **Database:** Clone of production (anonymized via a masking script).
- **Security:** Mirror of production IAM roles. This is where the "External Beta" (Milestone 2) will reside.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Deployment:** Deployed from `main` branch via Canary releases.
- **Database:** High-availability PostgreSQL cluster with multi-region failover.
- **Security:** ISO 27001 certified environment. No direct human access to the DB; all changes via Prisma Migrations.

### 6.2 The Vercel/LaunchDarkly Pipeline
We use **LaunchDarkly** for feature flags to decouple deployment from release. 
1. Code is deployed to Production (hidden behind a flag).
2. QA tests the feature in Prod using a "QA-only" flag.
3. The Project Lead (Olga) toggles the flag for 10% of users.
4. If p95 response time remains <200ms, the flag is rolled out to 100%.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** Vitest
- **Scope:** Domain logic in the Hexagonal Core.
- **Requirement:** 80% coverage for all new services.
- **Note:** The billing module currently has 0% coverage; this is documented as technical debt.

### 7.2 Integration Testing
- **Tool:** Jest + Prisma Mock
- **Scope:** Validating the interaction between Adapters and the Core.
- **Focus:** Testing the `NotificationDispatcher` with mocked Twilio/SendGrid responses to ensure the logic handles API failures correctly.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright
- **Scope:** Critical user paths (e.g., "Upload Property Image $\to$ Wait for Scan $\to$ View in Gallery").
- **Frequency:** Run on every merge request to the `develop` branch.

### 7.4 Performance Testing
- **Tool:** k6
- **Metric:** p95 Response Time.
- **Target:** < 200ms at a simulated load of 5,000 concurrent requests.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | Medium | Critical | Escalate to steering committee for multi-executive sponsorship and guaranteed funding. |
| R-02 | Scope creep from stakeholders | High | Medium | Maintain a strict "Change Request" log. Document workarounds for non-essential features. |
| R-03 | Budget approval delay for tool purchase | High | High | Identify open-source alternatives (e.g., replacing a paid tool with a self-hosted version) as a temporary bridge. |
| R-04 | Billing module failure (due to lack of tests) | Medium | Critical | Prioritize a "stabilization sprint" to add regression tests to the billing module before Milestone 2. |
| R-05 | ISO 27001 Audit Failure | Low | Critical | Weekly security reviews with Tomas Oduya; use automated compliance checklists. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
**Phase 1: Core Foundation (Now $\to$ Aug 2025)**
- Setup Hexagonal Architecture.
- Complete File Upload & Virus Scanning.
- Develop Notification System (Current Focus).
- **Milestone 1: Internal Alpha Release (2025-08-15)**

**Phase 2: Global Expansion (Aug 2025 $\to$ Oct 2025)**
- Implementation of 12-language Localization.
- Migration of legacy property data.
- Onboarding of 10 pilot users.
- **Milestone 2: External Beta (2025-10-15)**

**Phase 3: Optimization & Governance (Oct 2025 $\to$ Dec 2025)**
- Build Visual Workflow Engine.
- Finalize Data Import/Export tools.
- Comprehensive Architecture Review.
- **Milestone 3: Architecture Review Complete (2025-12-15)**

### 9.2 Dependency Map
- `Notification System` $\to$ Required for `External Beta`.
- `ISO 27001 Environment` $\to$ Required for `Internal Alpha`.
- `Localization` $\to$ Required for `External Beta`.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Per team culture, these recordings are rarely rewatched; decisions are codified in Slack and then summarized here.*

### Meeting 1: Architecture Alignment (2023-11-02)
- **Attendees:** Olga, Lior, Tomas, Callum.
- **Discussion:** Debate over whether to use a monolithic DB or per-service DBs.
- **Decision:** To maintain agility and budget, we will use a single PostgreSQL instance but implement "Logical Separation" (different schemas).
- **Action Item:** Lior to define the schema boundaries.

### Meeting 2: The "Billing Debt" Crisis (2023-11-15)
- **Attendees:** Olga, Lior, Tomas, Callum.
- **Discussion:** Realization that the billing module was pushed to production without a single test case during the last "crunch" period.
- **Decision:** We cannot rewrite it now, but we will not add any new features to billing until a baseline of 40% integration test coverage is met.
- **Action Item:** Callum to document known bugs in the billing module for the support team.

### Meeting 3: Tooling Budget Blockage (2023-12-01)
- **Attendees:** Olga, Tomas.
- **Discussion:** The request for the advanced security scanning tool is still sitting in "Pending" with Finance.
- **Decision:** Tomas will use a community edition of ClamAV for the alpha, but Olga will escalate the budget request to the steering committee as a "Critical Blocker."
- **Action Item:** Olga to send the escalation email by Friday.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000 USD

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $900,000 | Salaries for 4 FTEs (EM, Data Eng, Security Eng, Support Eng) over 18 months. |
| **Infrastructure** | $250,000 | Vercel Enterprise, AWS RDS, S3, and CDN costs. |
| **Tools & Licensing** | $150,000 | LaunchDarkly, SendGrid, Twilio, ISO 27001 Audit Fees. |
| **Contingency** | $200,000 | Reserved for emergency scaling or specialized consultants. |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist
To satisfy the external audit (Success Criterion 2), Project Lattice must adhere to:
- **A.9 Access Control:** All database access must be via IAM roles with MFA.
- **A.12 Operations Security:** All logs must be streamed to a read-only WORM (Write Once Read Many) storage.
- **A.14 System Acquisition:** All 3rd party libraries must be scanned for vulnerabilities using `npm audit` and Snyk.

### Appendix B: Performance Baseline (P95 Targets)
The success of the API Gateway is measured by the following p95 targets:
- **Property Retrieval:** < 120ms
- **Notification Dispatch (Queueing):** < 50ms
- **File Status Check:** < 100ms
- **Billing Summary (Legacy):** < 400ms (Expected to be higher due to technical debt).