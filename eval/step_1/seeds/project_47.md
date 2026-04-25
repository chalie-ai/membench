# Project Specification: Project Trellis
**Version:** 1.0.4  
**Status:** Draft / Pending Legal Approval  
**Date:** October 24, 2023  
**Company:** Stratos Systems  
**Classification:** Internal / Proprietary  

---

## 1. Executive Summary

**Project Overview**
Project Trellis is a strategic internal enterprise integration tool developed by Stratos Systems to bridge the gap between our internal food and beverage supply chain management and a critical external partner's data ecosystem. The primary objective is to synchronize real-time inventory, logistics, and partnership data via an external API, automating what is currently a fragmented, manual process. In the high-stakes food and beverage industry, where perishability and just-in-time delivery are paramount, the inability to sync partner data in real-time results in significant waste and revenue loss.

**Business Justification**
Currently, Stratos Systems relies on manual data entry and periodic CSV uploads to coordinate with our primary strategic partner. This process is prone to human error, resulting in a 12% discrepancy rate in inventory reporting and an average delay of 48 hours in order visibility. Trellis will replace these manual workflows with a Go-based microservices architecture, utilizing serverless functions and gRPC for high-performance communication. By integrating directly with the partner’s API on their deployment timeline, Stratos Systems will move from a reactive to a proactive supply chain model.

**ROI Projection**
The project is allocated a budget of $1.5M. The projected Return on Investment (ROI) is calculated based on three primary levers:
1. **Reduction in Labor Costs:** By automating the data ingestion and reconciliation process, we project a 50% reduction in manual processing time for end-users (Operational Staff), saving approximately 4,000 man-hours per year.
2. **Waste Reduction:** Improved synchronization of perishables is expected to reduce spoilage by 15%, estimated at a savings of $220,000 annually.
3. **Operational Efficiency:** Eliminating the 48-hour data lag allows for tighter inventory windows, increasing warehouse throughput by 10%.

The total projected annual savings are estimated at $640,000. Given the $1.5M initial investment, the project will reach its break-even point within 27 months of full deployment, excluding the strategic value of the partnership stability.

**Strategic Alignment**
Trellis is not merely a tool but a strategic hedge. By building a robust integration layer, Stratos Systems ensures that it remains the dominant partner in the relationship, possessing a superior technical interface that makes the partnership indispensable to the external vendor.

---

## 2. Technical Architecture

### 2.1 Architectural Philosophy
Trellis is designed as a distributed system utilizing a serverless-first approach on Google Cloud Platform (GCP). The architecture leverages Go for its concurrency primitives and performance, which is critical for handling the high-throughput data streams typical of F&B logistics.

### 2.2 The Stack
- **Language:** Go 1.21+ (Golang)
- **Communication:** gRPC for internal service-to-service communication; REST/JSON for external API consumption.
- **Database:** CockroachDB (Distributed SQL for high availability and global consistency).
- **Orchestration:** Kubernetes (GKE) managing the API Gateway and supporting services.
- **Compute:** GCP Cloud Functions (Serverless) for event-driven processing and periodic syncs.
- **Gateway:** GCP API Gateway for request routing, authentication, and rate limiting.

### 2.3 System Diagram (ASCII Description)
The following is a logical representation of the data flow:

```text
[ External Partner API ] <---(HTTPS/TLS 1.3)---> [ GCP API Gateway ]
                                                       |
                                                       v
                                            [ Orchestration Layer ]
                                            (Cloud Functions / GKE)
                                            /          |          \
                    _______________________/           |           \_______________________
                   |                                   |                                   |
        [ Sync Service (Go) ]                [ Notification Svc (Go) ]           [ Analytics Svc (Go) ]
                   |                                   |                                   |
                   |                                   |                                   |
           (gRPC Call)                          (gRPC Call)                        (gRPC Call)
                   |                                   |                                   |
                   v                                   v                                   v
           [ CockroachDB Cluster ] <--------------------------------------------------------'
           (Multi-region Deployment)
                   ^
                   |
           [ Frontend (React/TS) ] <---(REST API)--- [ Backend Gateway ]
```

### 2.4 Deployment Strategy
The project follows a strict **Weekly Release Train**.
- **Schedule:** Every Tuesday at 03:00 UTC.
- **Policy:** No hotfixes are permitted outside the train. If a bug is discovered on Wednesday, it must wait until the following Tuesday's train unless a "Critical P0" is declared by Dante Oduya (CTO).
- **Pipeline:** GitLab CI/CD $\rightarrow$ Dev $\rightarrow$ Staging $\rightarrow$ Production.

---

## 3. Detailed Feature Specifications

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** Blocked (Pending API Schema Finalization)

The dashboard serves as the central nervous system for Trellis users. Unlike standard static reports, this interface allows operational managers to curate their own view of the supply chain.

**Functional Requirements:**
- **Widget Library:** Users can choose from a set of predefined widgets (e.g., "Current Inventory Levels," "Pending Partner Shipments," "System Health," "API Sync Latency").
- **Drag-and-Drop Interface:** Utilizing `react-grid-layout`, users can resize and reposition widgets.
- **Persistence:** Dashboard configurations must be saved to the `user_preferences` table in CockroachDB so that the layout persists across sessions.
- **Real-time Updates:** Widgets must utilize WebSockets or long-polling to update data without page refreshes.

**Technical Implementation:**
The frontend will request a JSON configuration object representing the layout. The backend will provide a gRPC endpoint `/GetDashboardLayout` which returns the coordinates and widget IDs. When a user moves a widget, a `/UpdateDashboardLayout` call is triggered.

**Blocking Factor:** The dashboard is currently blocked because the external partner has not provided the final JSON schema for the "Live Inventory" endpoint, meaning the widgets cannot be mapped to real data.

### 3.2 Notification System (Email, SMS, In-app, Push)
**Priority:** Critical | **Status:** Blocked (Legal/DPA)

This is a launch-blocker. The system must notify stakeholders immediately when a sync fails, a shipment is delayed, or a critical inventory threshold is hit.

**Functional Requirements:**
- **Multi-Channel Delivery:** Integration with SendGrid (Email), Twilio (SMS), and Firebase Cloud Messaging (Push).
- **Notification Routing:** An internal rules engine determines the channel based on urgency. (e.g., P0 = SMS + Push; P2 = Email).
- **User Preferences:** Users must be able to toggle notifications on/off per channel.
- **Audit Log:** Every notification sent must be logged in the `notification_logs` table for compliance.

**Technical Implementation:**
The `NotificationService` will act as a consumer of a Pub/Sub queue. When the `SyncService` detects an anomaly, it publishes a message to the `notifications-topic`. The `NotificationService` then processes this message, checks user preferences, and invokes the appropriate third-party API.

**Blocking Factor:** This is blocked pending legal review of the Data Processing Agreement (DPA). Since SMS and Email involve transmitting PII (Personally Identifiable Information) to third parties, legal must approve the data handling terms.

### 3.3 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** In Design

Given that warehouse environments often have "dead zones" with poor Wi-Fi, the tool must remain functional without a constant connection.

**Functional Requirements:**
- **Local Caching:** Use IndexedDB to store the last known state of the dashboard and pending actions.
- **Optimistic UI:** When a user makes a change (e.g., marking a shipment as "received"), the UI updates immediately, and the action is queued locally.
- **Conflict Resolution:** A "Last-Write-Wins" strategy will be implemented, with a manual override prompt if a server-side change conflicts with a local change.
- **Background Sync:** Use Service Workers to detect when connectivity is restored and flush the queue to the backend.

**Technical Implementation:**
The frontend will implement a `SyncManager` class that wraps all API calls. If a `503` or network error is caught, the request is serialized and stored in IndexedDB. Upon the `online` event, the manager iterates through the queue and executes the requests sequentially.

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** In Progress

To prevent the external partner from banning the Stratos Systems API key, a robust throttling layer is required.

**Functional Requirements:**
- **Token Bucket Algorithm:** Implement rate limiting at the API Gateway level to ensure we stay within the partner's limit (100 requests/minute).
- **Usage Tracking:** Log every single request made to the external API, including response time and status code.
- **Analytics Dashboard:** A view for the CTO to see total API consumption and identify "noisy" services.

**Technical Implementation:**
A Redis-backed rate limiter will be implemented within the API Gateway. The `UsageAnalyticsService` will asynchronously write logs to a CockroachDB table `api_usage_logs` to avoid adding latency to the main request path.

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** Blocked

Management requires weekly snapshots of partnership performance to be delivered via email.

**Functional Requirements:**
- **Templated Reports:** Ability to generate PDFs based on HTML templates (using `wkhtmltopdf` or a similar Go library).
- **CSV Export:** Direct dump of filtered query results into CSV format.
- **Scheduler:** A cron-like service (using GCP Cloud Scheduler) to trigger report generation every Monday at 08:00 AM.
- **Delivery:** Integration with the Notification System to email the generated files.

**Technical Implementation:**
A dedicated `ReportingService` will handle the heavy lifting. Since PDF generation is CPU-intensive, it will run as a separate serverless function to avoid impacting the performance of the main API.

---

## 4. API Endpoint Documentation

All endpoints are hosted under `https://api.trellis.stratos.internal/v1/`.

### 4.1 GET `/sync/status`
**Description:** Returns the current health and last-sync timestamp of the external API integration.
- **Request:** No parameters.
- **Response:**
  ```json
  {
    "status": "healthy",
    "last_sync": "2023-10-24T14:30:00Z",
    "pending_records": 450,
    "latency_ms": 120
  }
  ```

### 4.2 POST `/inventory/update`
**Description:** Manually triggers a refresh of a specific SKU's inventory from the partner.
- **Request:** `{ "sku": "FB-102-RED", "warehouse_id": "WH-01" }`
- **Response:**
  ```json
  {
    "transaction_id": "tx-99821",
    "status": "queued",
    "estimated_completion": "2023-10-24T14:32:00Z"
  }
  ```

### 4.3 GET `/dashboard/layout`
**Description:** Retrieves the user's customized widget configuration.
- **Request:** `?user_id=user_789`
- **Response:**
  ```json
  {
    "user_id": "user_789",
    "widgets": [
      {"id": "w1", "type": "inventory_chart", "x": 0, "y": 0, "w": 6, "h": 4},
      {"id": "w2", "type": "alert_list", "x": 6, "y": 0, "w": 6, "h": 4}
    ]
  }
}
  ```

### 4.4 PUT `/dashboard/layout`
**Description:** Saves the user's customized widget configuration.
- **Request:** `{ "user_id": "user_789", "layout": [...] }`
- **Response:** `{ "status": "success", "version": 4 }`

### 4.5 GET `/reports/generate`
**Description:** Triggers an immediate generation of a PDF report.
- **Request:** `?type=weekly_summary&format=pdf`
- **Response:**
  ```json
  {
    "report_id": "rep-554",
    "download_url": "https://storage.googleapis.com/trellis-reports/rep-554.pdf",
    "expires_at": "2023-10-25T00:00:00Z"
  }
  ```

### 4.6 POST `/notifications/settings`
**Description:** Updates user notification preferences.
- **Request:** `{ "user_id": "user_789", "preferences": { "sms": false, "email": true, "push": true } }`
- **Response:** `{ "status": "updated" }`

### 4.7 GET `/analytics/usage`
**Description:** Returns API usage stats for the last 24 hours.
- **Request:** `?range=24h`
- **Response:**
  ```json
  {
    "total_requests": 144000,
    "error_rate": "0.02%",
    "peak_requests_per_sec": 25
  }
  ```

### 4.8 POST `/sync/force`
**Description:** Forces a full reconciliation of all partner data (Administrative use only).
- **Request:** `{ "reason": "Data discrepancy found in WH-02" }`
- **Response:** `{ "job_id": "job-112", "status": "started" }`

---

## 5. Database Schema

Trellis utilizes CockroachDB for its distributed nature. All tables use UUIDs as primary keys to prevent collisions across regions.

### 5.1 Tables and Relationships

1.  **`users`**
    - `user_id` (UUID, PK)
    - `email` (String, Unique)
    - `full_name` (String)
    - `role` (Enum: ADMIN, OPERATOR, VIEWER)
    - `created_at` (Timestamp)

2.  **`user_preferences`**
    - `pref_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ `users`)
    - `dashboard_json` (JSONB) - *Stores widget positions*
    - `notification_settings` (JSONB) - *Stores channel toggles*
    - `updated_at` (Timestamp)

3.  **`partner_inventory`**
    - `item_id` (UUID, PK)
    - `external_sku` (String, Indexed)
    - `quantity` (Decimal)
    - `unit_of_measure` (String)
    - `last_updated_external` (Timestamp)
    - `last_updated_internal` (Timestamp)

4.  **`sync_logs`**
    - `log_id` (UUID, PK)
    - `timestamp` (Timestamp)
    - `records_processed` (Int)
    - `errors_encountered` (Int)
    - `duration_ms` (Int)
    - `status` (Enum: SUCCESS, PARTIAL, FAIL)

5.  **`notifications`**
    - `notification_id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ `users`)
    - `message` (Text)
    - `channel` (Enum: SMS, EMAIL, PUSH, IN_APP)
    - `sent_at` (Timestamp)
    - `read_at` (Timestamp, Nullable)

6.  **`api_usage_logs`**
    - `request_id` (UUID, PK)
    - `endpoint` (String)
    - `response_code` (Int)
    - `latency_ms` (Int)
    - `request_timestamp` (Timestamp)

7.  **`reports`**
    - `report_id` (UUID, PK)
    - `type` (String)
    - `generated_at` (Timestamp)
    - `storage_path` (String)
    - `triggered_by` (UUID, FK $\rightarrow$ `users`)

8.  **`shipments`**
    - `shipment_id` (UUID, PK)
    - `external_tracking_id` (String, Unique)
    - `status` (Enum: PENDING, IN_TRANSIT, DELIVERED, CANCELLED)
    - `origin_id` (String)
    - `destination_id` (String)
    - `eta` (Timestamp)

9.  **`billing_module_records`** (Note: Core module with known technical debt)
    - `invoice_id` (UUID, PK)
    - `amount` (Decimal)
    - `currency` (String)
    - `status` (Enum: PAID, UNPAID, OVERDUE)
    - `due_date` (Date)

10. **`system_config`**
    - `config_key` (String, PK)
    - `config_value` (String)
    - `updated_by` (UUID, FK $\rightarrow$ `users`)
    - `updated_at` (Timestamp)

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
We maintain three distinct environments to ensure stability and isolation.

#### Dev Environment (`trellis-dev`)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Shared GKE cluster, small CockroachDB instance (single node).
- **Deployment:** Automatic on every commit to the `develop` branch.
- **Data:** Mock data generated via seeds; no real partner API access.

#### Staging Environment (`trellis-staging`)
- **Purpose:** Integration testing, QA, and UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of production (multi-node CockroachDB).
- **Deployment:** Triggered by merge to `release-candidate` branch.
- **Data:** Anonymized production data; connection to the partner's "Sandbox" API.

#### Production Environment (`trellis-prod`)
- **Purpose:** Live business operations.
- **Infrastructure:** High-availability GKE cluster across 3 GCP regions; CockroachDB multi-region cluster.
- **Deployment:** Weekly Release Train (Tuesdays 03:00 UTC).
- **Data:** Live partner data.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is managed via Terraform. Any change to the environment (e.g., adding a new Cloud Function or adjusting K8s resource limits) must be submitted as a Pull Request to the `infrastructure` repo and approved by Dante Oduya.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Approach:** Every Go function must have a corresponding `_test.go` file.
- **Coverage Goal:** 80% overall, though currently lower due to the billing module.
- **Tooling:** `go test` with `testify/assert` for validations.
- **CI Integration:** Tests run on every push. Failure to pass unit tests blocks the merge to `develop`.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between microservices (e.g., `SyncService` $\rightarrow$ `NotificationService`).
- **Tooling:** Docker Compose for local orchestration of CockroachDB and Go services.
- **Focus:** gRPC contract validation and database migration stability.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulating full user journeys (e.g., "User logs in $\rightarrow$ views dashboard $\rightarrow$ triggers sync $\rightarrow$ receives notification").
- **Tooling:** Cypress for frontend E2E; Postman/Newman for API suite validation.
- **Schedule:** E2E suites run in the Staging environment every Monday to verify the "Release Candidate" before the Tuesday train.

### 7.4 Special Case: The Billing Module
**Known Issue:** The core billing module was deployed under extreme deadline pressure without test coverage.
**Mitigation:** A "Stabilization Sprint" is scheduled for Q1 2026 to implement retrospective tests (Characterization Tests) to ensure no regressions occur during future updates.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor announces EOL for product | Medium | Critical | Build a "Fallback Architecture" layer. Decouple the core logic from the vendor API using an internal abstraction layer so the backend can be swapped to a new provider with minimal rewrites. |
| R-02 | Team lacks experience with Go/gRPC/CockroachDB | High | Medium | Document all workarounds in the internal Wiki. Conduct "Knowledge Share" sessions every Friday. Use a formal mentor-led code review process. |
| R-03 | Legal review of DPA takes longer than expected | High | High | Identify non-PII features that can be launched first. Escalate to the Legal VP if approval exceeds 30 days. |
| R-04 | Weekly release train prevents critical hotfixes | Low | Medium | Establish a "P0 Exception" protocol. If a bug causes >10% revenue loss/hour, the CTO can authorize an emergency out-of-band deploy. |

---

## 9. Timeline

### 9.1 Phase Breakdown

**Phase 1: Foundation (Now $\rightarrow$ 2026-01)**
- Setup GCP Infrastructure (Terraform).
- Implement basic gRPC communication between services.
- Establish the Weekly Release Train.
- *Dependency:* Infrastructure setup must be complete before service development.

**Phase 2: Core Integration (2026-01 $\rightarrow$ 2026-06)**
- Develop `SyncService` and `AnalyticsService`.
- Implement API rate limiting.
- Connect to partner Sandbox API.
- *Dependency:* Partner API documentation must be finalized.

**Phase 3: User Interface & Notifications (2026-06 $\rightarrow$ 2026-10)**
- Build Customizable Dashboard.
- Implement Notification System (post-legal approval).
- Implement Offline-First sync.
- *Dependency:* Legal DPA approval required for Notification launch.

**Phase 4: Hardening & Launch (2026-10 $\rightarrow$ 2026-12)**
- Full E2E testing.
- Final security penetration tests.
- Onboard first paying customer.

### 9.2 Key Milestones
- **Milestone 1:** First paying customer onboarded $\rightarrow$ **Target: 2026-07-15**
- **Milestone 2:** Security audit passed $\rightarrow$ **Target: 2026-09-15**
- **Milestone 3:** MVP feature-complete $\rightarrow$ **Target: 2026-11-15**

---

## 10. Meeting Notes (Slack Thread Archives)

*Note: Per team dynamic, no formal minutes are kept. The following are condensed summaries of decision-making threads from Slack.*

### Thread 1: #trellis-dev (Date: 2023-10-12)
**Topic:** Discussion on Hotfixes
- **Sanjay:** "We have a bug in the dashboard layout that's shifting widgets by 10px. Can we push a quick fix today?"
- **Dante:** "No. We are sticking to the release train. If it's not breaking the system, it waits until Tuesday."
- **Quinn:** "Agreed. Better to have a predictable cadence than a broken prod environment from rushed fixes."
- **Decision:** All UI bugs, regardless of size, must wait for the Tuesday release train.

### Thread 2: #trellis-arch (Date: 2023-10-18)
**Topic:** Tech Stack Learning Curve
- **Ren:** "I'm struggling with the CockroachDB consistency levels. I keep getting serialization errors on the billing update."
- **Dante:** "This is expected. We're all learning this on the fly. Ren, document the exact error and the workaround you found in the Wiki."
- **Sanjay:** "I'll do the same for the gRPC interceptors."
- **Decision:** Team will maintain a shared "Workarounds" document to mitigate the lack of prior experience with the stack.

### Thread 3: #trellis-legal (Date: 2023-10-21)
**Topic:** Notification Blocker
- **Quinn:** "I've finished the E2E tests for the SMS system, but I can't trigger them in staging because the API keys are pending legal."
- **Dante:** "Still waiting on the DPA review. Until then, the Notification system is officially 'Blocked'. Do not attempt to bypass this using personal accounts."
- **Decision:** Notification system remains blocked until the legal team provides a signed DPA.

---

## 11. Budget Breakdown

**Total Budget:** $1,500,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $950,000 | Salary for 4 FTEs (CTO, Frontend Lead, QA Lead, Support Eng) over project duration. |
| **Infrastructure** | $220,000 | GCP Costs (GKE, Cloud Functions, CockroachDB Cloud, API Gateway). |
| **Tools & Licenses** | $80,000 | JIRA, GitLab Premium, SendGrid, Twilio, Firebase, CockroachDB Enterprise. |
| **Security/Audit** | $100,000 | Quarterly penetration testing and final security audit for Milestone 2. |
| **Contingency** | $150,000 | Buffer for vendor price increases or emergency architectural pivots (Risk R-01). |

---

## 12. Appendices

### Appendix A: gRPC Service Definitions (.proto)
The communication between the `SyncService` and the `NotificationService` is defined as follows:

```protobuf
syntax = "proto3";

package trellis.notifications;

service NotificationService {
  rpc SendAlert (AlertRequest) returns (AlertResponse);
  rpc UpdatePreferences (PrefRequest) returns (PrefResponse);
}

message AlertRequest {
  string user_id = 1;
  string message = 2;
  enum Severity {
    INFO = 0;
    WARNING = 1;
    CRITICAL = 2;
  }
  Severity severity = 3;
}

message AlertResponse {
  bool delivered = 1;
  string tracking_id = 2;
}
```

### Appendix B: Data Reconciliation Logic
To ensure data integrity between Stratos Systems and the External Partner, Trellis implements a "Two-Phase Reconciliation" process:

1.  **Delta Fetch:** Every 15 minutes, the `SyncService` requests only records modified since the last `last_updated_external` timestamp.
2.  **Checksum Validation:** Every 24 hours (at 00:00 UTC), the system performs a full hash comparison of the total inventory count for each warehouse. If the hash does not match the partner's provided hash, a `POST /sync/force` is automatically triggered to overwrite the local state with the partner's source of truth.