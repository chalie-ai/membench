# PROJECT SPECIFICATION: PROJECT DRIFT
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Final Specification / Active Development  
**Project Lead:** Wes Fischer (VP of Product)  
**Classification:** Confidential – Ridgeline Platforms  

---

## 1. EXECUTIVE SUMMARY

**Project Drift** represents a strategic pivot for Ridgeline Platforms, marking the company's initial entry into a new, untapped segment of the automotive industry. While Ridgeline Platforms has historically dominated in adjacent sectors, Project Drift is a "greenfield" initiative designed to capture market share in a high-growth automotive niche. To achieve this, the project involves the migration from a legacy architectural mindset toward a modern, highly scalable API Gateway and microservices orchestration layer.

**Business Justification**  
The automotive market is currently shifting toward decentralized data processing and real-time telemetry. Our current infrastructure cannot support the latency requirements or the data residency laws required for this new market. By implementing a serverless architecture orchestrated by an API Gateway, Ridgeline Platforms can scale horizontally to meet unpredictable demand without the overhead of managing massive server clusters. This agility is critical for a product entering a market where the company has no prior operational footprint.

**Financial Investment and ROI Projection**  
The project has been allocated a total budget of **$3,000,000**. This substantial investment underscores the high executive visibility and the strategic importance of the venture. The ROI is projected based on two primary drivers:
1. **Operational Efficiency:** A target 50% reduction in manual processing time for end users, which is expected to reduce customer churn by 15% and increase the Average Revenue Per User (ARPU) by $1,200 annually.
2. **Market Penetration:** By achieving GDPR and CCPA compliance from Day 1, the product can be launched simultaneously in North American and European markets, accelerating the time-to-revenue by an estimated 6 months.

The projected break-even point is 18 months post-launch, with an estimated Year 3 revenue contribution of $12M. Success is binary: the project must pass an external audit on the first attempt and meet performance benchmarks by April 2026 to ensure the viability of the business model.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Drift utilizes a "Pragmatic Modernism" approach. The core business logic resides in a **Ruby on Rails monolith** (Version 7.1) for rapid development and developer ergonomics, hosted on **Heroku**. However, to handle the scale and specific needs of the automotive industry (such as high-frequency telemetry), this monolith is augmented by a **Serverless Architecture** utilizing AWS Lambda functions and an **Amazon API Gateway**.

The API Gateway acts as the "brains" of the system, handling request routing, rate limiting, and authentication before delegating specific heavy-lift tasks to serverless functions. This hybrid approach allows the team of four to maintain the speed of a monolith while gaining the elasticity of microservices.

### 2.2 System Diagram (ASCII)
```text
[ Client (Web/Mobile) ] 
       |
       v
[ AWS API Gateway ] <--- (Auth/Rate Limiting/Routing)
       |
       +---------------------------------------+
       |                                       |
       v                                       v
[ Serverless Functions ]                [ Ruby on Rails Monolith ]
(AWS Lambda / Node.js)                    (Heroku - Core Logic)
       |                                       |
       +-------------------+-------------------+
                           |
                           v
                [ MySQL Database Cluster ]
                (RDS - EU Region Residency)
                           |
                [ S3 Bucket / CloudFront CDN ]
                (File Storage & Distribution)
```

### 2.3 Data Residency & Compliance
To satisfy **GDPR and CCPA** requirements, all data at rest is stored in the `eu-central-1` (Frankfurt) region. The API Gateway implements geographic routing to ensure that EU citizen data never leaves the EU jurisdiction. Encryption is handled via AES-256 at the database level and TLS 1.3 in transit.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**  
Users must be able to upload large automotive technical documents (PDFs, CAD files, High-Res Images) and share them across the platform. Given the sensitivity of automotive intellectual property and the risk of malware in uploaded documents, a multi-stage pipeline is required.

**Technical Workflow:**
1. **Ingestion:** The client requests a pre-signed S3 URL via the `/upload/request` endpoint.
2. **Staging:** The file is uploaded to an "Inbound" S3 bucket.
3. **Scanning:** An S3 Trigger invokes a Lambda function that sends the file to an external virus scanning API (e.g., ClamAV or CrowdStrike).
4. **Verification:** If the scan returns "Clean," the file is moved to the "Production" bucket. If "Infected," the file is quarantined, and the user is notified.
5. **Distribution:** The Production bucket is linked to a CloudFront CDN with a custom domain (`cdn.drift.ridgeline.com`) to ensure low-latency access globally.

**Acceptance Criteria:**
- Files up to 500MB must be supported.
- Virus scanning must complete within 30 seconds of upload.
- Files must be served via HTTPS with a cache-hit ratio of >80% for popular documents.
- All upload logs must be stored for 90 days for audit purposes.

### 3.2 Webhook Integration Framework
**Priority:** High | **Status:** In Design

**Description:**  
The automotive ecosystem relies on third-party tools (ERPs, Telematics providers). Project Drift must provide a framework allowing these tools to receive real-time updates when specific events occur within the platform (e.g., `vehicle.registration_complete`, `document.approved`).

**Technical Workflow:**
1. **Subscription:** Users configure a webhook URL and a set of "Event Triggers" via the dashboard.
2. **Event Bus:** When a trigger occurs in the Rails monolith, a message is published to an Amazon SQS queue.
3. **Dispatcher:** A serverless "Webhook Dispatcher" function reads from SQS and sends a POST request to the target URL.
4. **Retry Logic:** The system must implement exponential backoff. If a target returns a 5xx error, the system retries at 1m, 5m, 30m, and 2h intervals.
5. **Security:** Every webhook payload must include an `X-Drift-Signature` header (HMAC-SHA256) to allow the receiver to verify the authenticity of the request.

**Acceptance Criteria:**
- Ability to support at least 10 distinct event types.
- Delivery latency from event trigger to webhook POST must be under 2 seconds.
- User dashboard must show a "Delivery Log" of the last 50 attempts per webhook.

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** Blocked (Pending Design Finalization)

**Description:**  
End users require a personalized view of their automotive fleet data. The dashboard must be customizable, allowing users to move, resize, and add widgets (e.g., "Fuel Efficiency Chart," "Maintenance Alerts," "Regional Map").

**Technical Workflow:**
1. **Frontend:** Implementation of `react-grid-layout` for the drag-and-drop interface.
2. **State Persistence:** The layout configuration (coordinates, dimensions, widget IDs) is stored as a JSON blob in the `user_dashboard_configs` table.
3. **Widget Rendering:** Each widget is a standalone React component that fetches data from specific API Gateway endpoints.
4. **Dynamic Loading:** Widgets are lazy-loaded to ensure the initial page load is under 1.5 seconds.

**Acceptance Criteria:**
- Users can save multiple dashboard layouts.
- Widgets must be responsive across desktop and tablet views.
- Drag-and-drop movement must persist immediately upon release.

### 3.4 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** Not Started

**Description:**  
Automotive technicians often work in "dead zones" (garages, underground lots) where connectivity is intermittent. The application must allow users to continue working offline and sync changes once a connection is restored.

**Technical Workflow:**
1. **Client Storage:** Implementation of IndexedDB via PouchDB to store local copies of required data.
2. **Change Tracking:** Every local mutation is timestamped and stored in a "Pending Sync" queue.
3. **Sync Engine:** A background service worker monitors network status. Upon reconnection, it initiates a "Delta Sync."
4. **Conflict Resolution:** The server uses a "Last Write Wins" (LWW) strategy unless a version conflict is detected, in which case the record is flagged for manual review.

**Acceptance Criteria:**
- App must be fully functional for data entry without an internet connection.
- Sync must occur automatically within 5 seconds of network restoration.
- Zero data loss during transitions between offline and online states.

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low | **Status:** Complete

**Description:**  
Allows multiple users to edit a vehicle's technical specification document simultaneously. This feature was developed as a proof-of-concept and is now considered complete.

**Technical Workflow:**
1. **WebSocket Layer:** Managed via ActionCable (Rails).
2. **Operational Transformation (OT):** Implementation of an OT algorithm to handle concurrent text insertions and deletions.
3. **Presence Indicators:** "User X is typing..." indicators based on cursor position tracking.
4. **State Snapshots:** Every 30 seconds, a snapshot of the document is saved to MySQL to prevent data loss during crashes.

**Acceptance Criteria:**
- Support for up to 10 concurrent editors per document.
- Latency between edits must be under 100ms.
- No "ghost" characters or overlapping text during simultaneous edits.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/v1/`. Base URL: `api.drift.ridgeline.com`.

### 4.1 Authentication & Session
**Endpoint:** `POST /auth/login`  
**Description:** Authenticates user and returns a JWT.  
**Request:**
```json
{
  "email": "user@ridgeline.com",
  "password": "hashed_password_123"
}
```
**Response:** `200 OK`
```json
{
  "token": "eyJhbGciOiJIUzI1...",
  "expires_at": "2023-10-24T12:00:00Z"
}
```

### 4.2 File Upload Request
**Endpoint:** `POST /files/upload-request`  
**Description:** Generates a pre-signed S3 URL.  
**Request:**
```json
{
  "filename": "engine_specs.pdf",
  "content_type": "application/pdf"
}
```
**Response:** `201 Created`
```json
{
  "upload_url": "https://s3.eu-central-1.amazonaws.com/drift-inbound/...",
  "file_id": "uuid-123-456"
}
```

### 4.3 File Status Check
**Endpoint:** `GET /files/status/{file_id}`  
**Description:** Checks if the virus scan is complete.  
**Response:** `200 OK`
```json
{
  "file_id": "uuid-123-456",
  "status": "scanning|clean|infected",
  "cdn_url": "https://cdn.drift.ridgeline.com/files/uuid-123-456"
}
```

### 4.4 Webhook Subscription
**Endpoint:** `POST /webhooks/subscribe`  
**Description:** Registers a third-party URL for event notifications.  
**Request:**
```json
{
  "target_url": "https://client-erp.com/api/drift",
  "events": ["vehicle.updated", "document.uploaded"]
}
```
**Response:** `201 Created`
```json
{
  "webhook_id": "wh_98765",
  "secret": "whsec_abc123"
}
```

### 4.5 Dashboard Config
**Endpoint:** `GET /user/dashboard/config`  
**Description:** Retrieves the current layout of widgets.  
**Response:** `200 OK`
```json
{
  "layout": [
    {"i": "widget_1", "x": 0, "y": 0, "w": 6, "h": 4},
    {"i": "widget_2", "x": 6, "y": 0, "w": 6, "h": 4}
  ]
}
```

### 4.6 Update Dashboard Config
**Endpoint:** `PUT /user/dashboard/config`  
**Description:** Saves a new layout.  
**Request:**
```json
{
  "layout": [...]
}
```
**Response:** `200 OK`

### 4.7 Vehicle Telemetry Fetch
**Endpoint:** `GET /vehicles/{vin}/telemetry`  
**Description:** Returns latest telemetry data for a specific VIN.  
**Response:** `200 OK`
```json
{
  "vin": "1A2B3C...",
  "fuel_level": 72,
  "engine_temp": 95,
  "timestamp": "2023-10-24T10:00:00Z"
}
```

### 4.8 User Profile Update
**Endpoint:** `PATCH /user/profile`  
**Description:** Updates user account details.  
**Request:**
```json
{
  "display_name": "Wes Fischer",
  "timezone": "UTC+1"
}
```
**Response:** `200 OK`

---

## 5. DATABASE SCHEMA

**Database Engine:** MySQL 8.0 (AWS RDS)  
**Isolation Level:** Repeatable Read  
**Region:** eu-central-1

### 5.1 Table Definitions

1.  **`users`**
    *   `id` (UUID, PK)
    *   `email` (VARCHAR 255, Unique)
    *   `password_digest` (VARCHAR 255)
    *   `role` (ENUM: 'admin', 'tech', 'manager')
    *   `created_at` (TIMESTAMP)

2.  **`vehicles`**
    *   `id` (UUID, PK)
    *   `vin` (VARCHAR 17, Unique, Indexed)
    *   `model` (VARCHAR 100)
    *   `year` (INT)
    *   `owner_id` (UUID, FK -> users.id)

3.  **`telemetry_logs`**
    *   `id` (BIGINT, PK)
    *   `vehicle_id` (UUID, FK -> vehicles.id)
    *   `metric_name` (VARCHAR 50)
    *   `metric_value` (DECIMAL 10,2)
    *   `recorded_at` (TIMESTAMP, Indexed)

4.  **`documents`**
    *   `id` (UUID, PK)
    *   `vehicle_id` (UUID, FK -> vehicles.id)
    *   `s3_key` (VARCHAR 512)
    *   `status` (ENUM: 'pending', 'clean', 'infected')
    *   `checksum` (VARCHAR 64)

5.  **`webhook_subscriptions`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> users.id)
    *   `target_url` (VARCHAR 2048)
    *   `secret` (VARCHAR 255)
    *   `active` (BOOLEAN)

6.  **`webhook_events`**
    *   `id` (UUID, PK)
    *   `subscription_id` (UUID, FK -> webhook_subscriptions.id)
    *   `event_type` (VARCHAR 50)
    *   `payload` (JSON)
    *   `attempt_count` (INT)
    *   `last_attempt_at` (TIMESTAMP)

7.  **`user_dashboard_configs`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> users.id)
    *   `layout_json` (JSON)
    *   `updated_at` (TIMESTAMP)

8.  **`audit_logs`**
    *   `id` (BIGINT, PK)
    *   `user_id` (UUID, FK -> users.id)
    *   `action` (VARCHAR 100)
    *   `ip_address` (VARCHAR 45)
    *   `created_at` (TIMESTAMP)

9.  **`collaborative_docs`**
    *   `id` (UUID, PK)
    *   `title` (VARCHAR 255)
    *   `content` (TEXT)
    *   `version` (INT)
    *   `last_modified_by` (UUID, FK -> users.id)

10. **`fleet_groups`**
    *   `id` (UUID, PK)
    *   `group_name` (VARCHAR 100)
    *   `manager_id` (UUID, FK -> users.id)

### 5.2 Relationships
- **Users $\rightarrow$ Vehicles:** One-to-Many (A user can own multiple vehicles).
- **Vehicles $\rightarrow$ TelemetryLogs:** One-to-Many (A vehicle has thousands of telemetry entries).
- **Vehicles $\rightarrow$ Documents:** One-to-Many (A vehicle can have multiple spec sheets/manuals).
- **Users $\rightarrow$ DashboardConfigs:** One-to-One (Each user has one active layout).
- **WebhookSubscriptions $\rightarrow$ WebhookEvents:** One-to-Many (One subscription receives many events).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Drift utilizes a **Continuous Deployment (CD)** pipeline. Every merged Pull Request (PR) to the `main` branch is automatically deployed to production.

| Environment | Purpose | Infrastructure | Data Source |
| :--- | :--- | :--- | :--- |
| **Development** | Feature building | Local Docker / Heroku Dev Dynos | Seeded MySQL |
| **Staging** | QA & Legal Review | Heroku Staging App | Anonymized Prod Clone |
| **Production** | Live Users | Heroku Performance Dynos + AWS Lambda | Production RDS (EU) |

### 6.2 Infrastructure Details
- **Heroku:** Handles the Ruby on Rails monolith. We utilize a "Performance-M" dyno tier to ensure sufficient RAM for the Rails application.
- **AWS API Gateway:** Acts as the entry point. It handles throttling (10,000 requests per second) and integrates with AWS Cognito for identity management.
- **AWS Lambda:** Written in Node.js 18.x. Used for virus scanning, webhook dispatching, and high-frequency telemetry ingestion.
- **CI/CD Pipeline:** GitHub Actions $\rightarrow$ Heroku API $\rightarrow$ AWS CloudFormation (for Lambdas).

### 6.3 Data Residency Enforcement
All RDS instances and S3 buckets are locked to the `eu-central-1` region. The `terraform` configuration includes a region-lock policy that prevents the creation of resources in non-EU regions, ensuring compliance with GDPR.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Ruby on Rails:** RSpec is used for all model and controller tests. Coverage target: 85%.
- **Lambda Functions:** Jest is used for Node.js functions. Every function must have a mock for the S3 and SQS triggers.
- **Frequency:** Run on every PR commit via GitHub Actions.

### 7.2 Integration Testing
- **API Gateway Flows:** Postman collections are automated using Newman to verify that requests flow correctly from the Gateway $\rightarrow$ Lambda $\rightarrow$ Database.
- **Database Integrity:** Integration tests verify that foreign key constraints are maintained during complex deletions (e.g., deleting a vehicle must clean up telemetry logs).
- **Sync Testing:** Specifically for the "Offline-First" mode, we simulate network latency and outages using Chrome DevTools' network throttling and verify that the PouchDB $\rightarrow$ Rails sync resolves without data loss.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Cypress is used for frontend E2E testing.
- **Critical Paths:**
    1. User Login $\rightarrow$ Upload File $\rightarrow$ Wait for Scan $\rightarrow$ View File via CDN.
    2. Create Webhook $\rightarrow$ Trigger Event $\rightarrow$ Verify external POST request.
    3. Drag widget on Dashboard $\rightarrow$ Refresh $\rightarrow$ Verify position remains.
- **Frequency:** Run daily on the `main` branch.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding "small" features. | High | Medium | Accept the risk; monitor weekly during stakeholder syncs. Log all changes in the "Change Request" doc. |
| **R2** | Key Architect leaving the company in 3 months. | Medium | High | De-scope affected features if a replacement is not hired by the milestone date. Document all architectural decisions now. |
| **R3** | Legal review of Data Processing Agreement (DPA) delay. | High | Critical | **Current Blocker.** Escalate to VP of Legal; prepare a "temporary data handling" plan that doesn't store PII. |
| **R4** | Technical debt from hardcoded config values in 40+ files. | High | Medium | Implement a centralized `config` gem or AWS Parameter Store. Schedule a "Debt Sprint" in Q1 2026. |

### 8.1 Probability/Impact Matrix
- **High Impact / High Probability:** R1 (Scope Creep) $\rightarrow$ Must be actively managed.
- **High Impact / Medium Probability:** R2 (Architect Loss) $\rightarrow$ Contingency planning required.
- **Critical Impact / High Probability:** R3 (Legal Block) $\rightarrow$ Absolute priority.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Description
- **Phase 1: Foundation (Now - April 2026):** Focus on API Gateway setup, GDPR compliance, and performance tuning.
- **Phase 2: Feature Build (April 2026 - June 2026):** Implementation of File Uploads, Webhooks, and Dashboard.
- **Phase 3: Hardening & Audit (June 2026 - August 2026):** Final bug fixing, external security audit, and performance stress tests.

### 9.2 Key Milestones
- **Milestone 1: Performance Benchmarks Met**
    - **Target Date:** 2026-04-15
    - **Criteria:** API response time < 200ms (p95); Database query time < 50ms.
- **Milestone 2: MVP Feature-Complete**
    - **Target Date:** 2026-06-15
    - **Criteria:** All 5 features (Critical/High/Medium) passing E2E tests.
- **Milestone 3: Architecture Review Complete**
    - **Target Date:** 2026-08-15
    - **Criteria:** Final sign-off from the external auditor and the internal security team.

---

## 10. MEETING NOTES (EXTRACTS)

*Note: These are excerpts from the shared running document (currently 200 pages). Due to the lack of searchability, these items were manually extracted.*

### Meeting 1: Technical Strategy Sync (2023-11-02)
**Attendees:** Wes, Xavi, Felix, Omar
- **Discussion:** Omar raised concerns about the 40+ files containing hardcoded values. Xavi suggested using AWS Parameter Store, but Wes decided to stick with a simple `dotenv` approach for now to avoid adding complexity too early.
- **Decision:** We will accept the technical debt for now but must track it in the risk register.
- **Action Item:** Xavi to set up the Heroku-AWS pipeline by Friday.

### Meeting 2: Design Review - Dashboard (2023-11-15)
**Attendees:** Wes, Felix, Omar
- **Discussion:** Felix presented the drag-and-drop mockups. Omar noted that saving the layout as a JSON blob in MySQL would be the fastest way to implement. Wes expressed concern that stakeholders might want "preset" templates.
- **Decision:** Feature is currently **Blocked** until Felix finalizes the "Template" vs "Custom" UX flow.
- **Action Item:** Felix to update Figma prototypes.

### Meeting 3: Legal & Compliance Sync (2023-12-01)
**Attendees:** Wes, Legal Counsel
- **Discussion:** Legal is still reviewing the Data Processing Agreement. Wes emphasized that this is a launch blocker. Legal mentioned that the EU data residency requirement is non-negotiable.
- **Decision:** No development on the "User Profile" system will occur until the DPA is signed to avoid storing data that might need to be deleted.
- **Action Item:** Wes to email the CEO to expedite the legal review.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | Salaries for the team of 4 over 2.5 years, including bonuses. |
| **Infrastructure** | $450,000 | Heroku Performance Dynos, AWS Lambda, RDS, S3, and CloudFront. |
| **Tools & Licenses** | $150,000 | GitHub Enterprise, Postman, Figma, Datadog, and Security Audit fees. |
| **Contingency** | $600,000 | Buffer for scope creep, emergency hiring, and unexpected infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: Versioning and Dependency Matrix
| Component | Version | Purpose |
| :--- | :--- | :--- |
| Ruby | 3.2.2 | Language Runtime |
| Ruby on Rails | 7.1.0 | Core Monolith Framework |
| MySQL | 8.0.33 | Relational Database |
| Node.js | 18.x | Lambda Runtime |
| React | 18.2.0 | Frontend Framework |
| AWS SDK | 3.x | Infrastructure Management |

### Appendix B: Virus Scanning Logic Flow
To ensure the "Critical" status of the file upload feature is met, the scanning logic follows a strict state machine:
1. `UPLOADED` $\rightarrow$ Trigger `ScanLambda`.
2. `ScanLambda` $\rightarrow$ Call `ExternalScannerAPI`.
3. If `API_RESPONSE == "CLEAN"` $\rightarrow$ Move to `S3_PROD_BUCKET` $\rightarrow$ Set status `CLEAN`.
4. If `API_RESPONSE == "INFECTED"` $\rightarrow$ Move to `S3_QUARANTINE_BUCKET` $\rightarrow$ Set status `INFECTED` $\rightarrow$ Notify User.
5. If `API_RESPONSE == "TIMEOUT/ERROR"` $\rightarrow$ Re-queue for 3 attempts $\rightarrow$ Finally set status `SCAN_FAILED` (Manual Review required).