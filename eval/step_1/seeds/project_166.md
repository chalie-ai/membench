# PROJECT SPECIFICATION: PROJECT BEACON
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Last Updated:** 2024-05-22  
**Project Owner:** Beatriz Jensen (Engineering Manager)  
**Company:** Bridgewater Dynamics  
**Confidentiality Level:** Internal / Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Beacon is a flagship strategic initiative for Bridgewater Dynamics, designed to catalyze a critical partnership integration within the logistics and shipping sector. In the current global supply chain climate, the ability to synchronize real-time telemetry and shipping manifests with external partners is not merely a competitive advantage but a operational necessity. Beacon serves as the bridge between Bridgewater Dynamics’ internal logistics engine and the API ecosystem of a strategic external partner. 

The core business driver is the reduction of "dark time"—the window between a shipment leaving a port and its arrival at a distribution center where visibility is currently limited. By integrating directly with the external partner’s API on their timeline, Beacon will automate the synchronization of vessel tracking, customs clearance status, and last-mile logistics. This eliminates manual data entry, reduces human error in manifest reporting, and optimizes route planning through real-time data ingestion.

### 1.2 ROI Projection
With a total project budget exceeding $5,000,000, the Return on Investment (ROI) is measured across three primary vectors: operational efficiency, customer retention, and market expansion.

1.  **Operational Cost Reduction:** By automating the data sync, we project a reduction of 15,000 man-hours per annum previously spent on manual reconciliation. At an average burdened labor rate of $85/hr, this represents a direct saving of $1.275M annually.
2.  **Churn Mitigation:** Real-time visibility is the #1 requested feature from our Tier-1 enterprise clients. By hitting the target launch date of October 2025, we aim to secure contracts worth an additional $12M in Annual Recurring Revenue (ARR) that are currently "at risk" due to the lack of transparency.
3.  **Market Positioning:** The ability to scale to 10x the current system capacity (as required by the project specs) allows Bridgewater Dynamics to move from a regional logistics provider to a global orchestrator.

The projected Break-Even Point (BEP) is 14 months post-launch, with a 3-year Net Present Value (NPV) estimated at $18.4M.

### 1.3 Strategic Alignment
Beacon is a board-level priority. It transitions the company from a "reactive" data model (where we update records upon receipt of emails/PDFs) to a "proactive" model (where we pull data via gRPC and REST streams). The success of Beacon is tied directly to the company's 2026 goal of achieving a 25% increase in throughput capacity without increasing headcount.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Beacon utilizes a "Modular Monolith transitioning to Microservices" approach. To avoid the "distributed monolith" trap, the team is building the core logic within a single deployable unit but strictly enforcing boundary interfaces. As specific domains (e.g., the Notification System or the Search Engine) reach a level of complexity or load that requires independent scaling, they will be carved out into standalone Go microservices.

### 2.2 The Stack
- **Language:** Go (Golang) 1.22+ for all backend services due to its superior concurrency primitives (goroutines) and performance in high-throughput logistics environments.
- **Communication:** gRPC for internal service-to-service communication to ensure type safety and low latency. REST/JSON is reserved for external API consumption and the frontend.
- **Database:** CockroachDB (Distributed SQL). Chosen for its survival capabilities across multiple GCP regions, ensuring that if a single zone fails, shipping data remains available.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
- **Security:** ISO 27001 certified environment. All data at rest is encrypted via AES-256, and data in transit uses TLS 1.3.

### 2.3 System Diagram (ASCII)

```text
[External Partner API] <---(HTTPS/REST)---> [Beacon Integration Gateway]
                                                       |
                                                       v
                                         [API Rate Limiter & Auth Layer]
                                                       |
                                                       v
      _________________________________________________|_________________________________________________
     |                                                                                                   |
     |                                     [ CORE BEACON LOGIC ]                                         |
     |  (Modular Monolith Phase)                                                                         |
     |                                                                                                   |
     |  [Shipment Manager] <---> [Search Engine (Elastic)] <---> [Notification Engine] <---> [Dashboard]  |
     |          ^                                                                                           |
     |          |                                                                                           |
     |__________|_______________________________________________________________________________________|
                |                                      |
                v                                      v
      [ CockroachDB Cluster ]                [ Redis Cache / PubSub ]
      (Multi-Region Deployment)             (Session & Rate Limit State)
                |
                v
      [ GitHub Actions CI/CD ] ---> [ GKE Cluster (Blue-Green Deployment) ]
```

### 2.4 Data Flow
1. **Ingestion:** The Integration Gateway polls the external partner's API.
2. **Validation:** Data is validated against the internal schema; if valid, it is written to CockroachDB.
3. **Indexing:** A Change Data Capture (CDC) pipeline pushes updates to the Full-Text Index for the Advanced Search feature.
4. **Notification:** If a shipment status changes (e.g., "Delayed"), the Notification Engine triggers a push/SMS alert.
5. **Visualization:** The Customizable Dashboard pulls aggregated data via gRPC from the core logic and renders it via the frontend.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** In Design

**Description:**
The Dashboard is the primary interface for logistics operators. Unlike a static report, the Beacon Dashboard allows users to curate their own "Command Center" by dragging and dropping widgets from a library of available data views.

**Technical Requirements:**
- **Widget Engine:** The frontend will implement a grid-based layout system (e.g., React-Grid-Layout). Each widget is a standalone component that communicates with a specific gRPC endpoint.
- **Persistence:** User layout configurations (widget position, size, and filtered view) must be stored in the `user_preferences` table in CockroachDB as a JSONB blob.
- **State Management:** Use of a global state manager (Redux or Zustand) to handle real-time updates across widgets without refreshing the page.

**Functional Specifications:**
- **Widget Library:** Must include "Active Shipments," "Alerts Feed," "Partner API Health," and "Volume Heatmap."
- **Drag-and-Drop:** Users can resize widgets and move them. Changes are saved automatically via a "debounce" mechanism to prevent excessive API calls.
- **Custom Filtering:** Each widget can have its own local filter (e.g., "Only show shipments for Region: APAC").

**Success Metric:** Users should be able to configure a personalized dashboard in under 2 minutes.

---

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Review

**Description:**
Because Beacon integrates with an external partner's API, we must strictly adhere to their rate limits to avoid being blacklisted. Simultaneously, we must provide our internal users with analytics regarding their API consumption.

**Technical Requirements:**
- **Algorithm:** Implementation of a "Token Bucket" algorithm. This allows for short bursts of traffic while maintaining a steady average rate.
- **Storage:** Redis will be used to store bucket tokens with a TTL (Time-to-Live) to ensure sub-millisecond latency for rate-check operations.
- **Middleware:** The rate limiter will exist as a Go middleware wrapper around all incoming and outgoing API requests.

**Functional Specifications:**
- **Dynamic Limits:** Ability for Beatriz (Project Lead) to adjust rate limits via a config file without requiring a full redeployment.
- **Analytics Dashboard:** A view for administrators showing 429 (Too Many Requests) error rates and total calls per hour.
- **Alerting:** If the system hits 90% of the partner's rate limit, a high-priority alert is sent to the engineering Slack channel.

**Success Metric:** Zero "429 Too Many Requests" errors received from the external partner in a production environment.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Medium | **Status:** In Review

**Description:**
Logistics operators deal with millions of records. A standard SQL `LIKE` query is insufficient. Beacon requires a full-text search capability that allows users to find shipments by partial manifest numbers, container IDs, or customer names across 12 different languages.

**Technical Requirements:**
- **Indexing Engine:** Integration of Elasticsearch or Meilisearch. A synchronization worker will listen to CockroachDB CDC (Change Data Capture) events and update the search index in near real-time.
- **Faceted Search:** Implementation of "buckets" for filtering. Users can filter by "Status" (In Transit, Delivered, Delayed), "Carrier," and "Destination Country."
- **Tokenization:** Use of language-specific analyzers to handle stemming and lemmatization for the 12 supported languages.

**Functional Specifications:**
- **Search Latency:** Results must return within 300ms for a dataset of 10 million records.
- **Highlighting:** The search result should highlight the specific keyword match within the shipment description.
- **Boolean Logic:** Support for AND/OR/NOT operators in the search bar.

**Success Metric:** Search accuracy (precision/recall) above 95% based on internal QA test sets.

---

### 3.4 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** Not Started

**Description:**
Beacon must keep stakeholders informed of critical events (e.g., Customs Hold, Vessel Diversion) without requiring them to constantly poll the dashboard.

**Technical Requirements:**
- **Provider Integration:** Use of SendGrid for Email, Twilio for SMS, and Firebase Cloud Messaging (FCM) for Push notifications.
- **Queueing:** A RabbitMQ or NATS JetStream cluster will handle the notification queue to ensure that a spike in events doesn't crash the core API.
- **Retry Logic:** Implementation of exponential backoff for failed delivery attempts.

**Functional Specifications:**
- **Preference Center:** Users must be able to toggle which notifications they receive via which channel (e.g., "SMS for Urgent only, Email for Daily Digests").
- **Templating:** Use of a templating engine (like Go templates) to allow dynamic insertion of shipment IDs and timestamps into messages.
- **Audit Trail:** Every notification sent must be logged in the `notification_logs` table for compliance.

**Success Metric:** Notification delivery latency (event trigger to device receipt) under 30 seconds.

---

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low | **Status:** In Progress

**Description:**
Bridgewater Dynamics operates globally. Beacon must be usable by staff in 12 different languages across the EMEA, APAC, and AMER regions.

**Technical Requirements:**
- **Resource Bundles:** Use of JSON-based translation files stored in the frontend repository and cached via CDN.
- **UTF-8 Encoding:** Absolute requirement for all database columns and API endpoints to support non-Latin characters (e.g., Kanji, Cyrillic).
- **Date/Currency Formatting:** Integration of the `intl` JavaScript API for the frontend and Go's `time` package for the backend to handle timezone shifts and currency symbols.

**Functional Specifications:**
- **Language Switching:** A dropdown in the user profile allowing instant switching between the 12 supported languages.
- **Right-to-Left (RTL) Support:** UI layout must support RTL flipping for languages like Arabic.
- **Dynamic Translation:** Support for "on-the-fly" translation of partner API error messages using a translation layer.

**Success Metric:** 100% of the primary UI paths translated into all 12 target languages.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `X-Beacon-Auth-Token` in the header.

### 4.1 Shipment Management

**1. GET `/shipments`**
- **Description:** Retrieve a paginated list of shipments.
- **Query Params:** `page` (int), `limit` (int), `status` (string), `query` (string).
- **Example Request:** `GET /api/v1/shipments?limit=20&status=delayed`
- **Response (200 OK):**
  ```json
  {
    "data": [
      {"id": "SHIP-123", "status": "delayed", "origin": "Shanghai", "destination": "Long Beach", "eta": "2025-09-10T14:00:00Z"}
    ],
    "pagination": {"total": 1250, "next_page": 2}
  }
  ```

**2. GET `/shipments/{id}`**
- **Description:** Get detailed telemetry for a specific shipment.
- **Example Request:** `GET /api/v1/shipments/SHIP-123`
- **Response (200 OK):**
  ```json
  {
    "id": "SHIP-123",
    "current_lat": 34.0522,
    "current_long": -118.2437,
    "events": [
      {"timestamp": "2025-08-01T10:00:00Z", "event": "Departed Port"}
    ]
  }
  ```

**3. PATCH `/shipments/{id}`**
- **Description:** Manually override shipment status or details.
- **Request Body:** `{"status": "delivered", "notes": "Received at warehouse 4"}`
- **Response (200 OK):** `{"status": "success", "updated_at": "2025-08-15T09:00:00Z"}`

### 4.2 Dashboard & User Prefs

**4. GET `/user/preferences`**
- **Description:** Retrieve the user's dashboard layout and notification settings.
- **Response (200 OK):**
  ```json
  {
    "layout": [{"widget": "active_shipments", "x": 0, "y": 0, "w": 6, "h": 4}],
    "language": "en-US",
    "notifications": {"sms": true, "email": true}
  }
  ```

**5. PUT `/user/preferences`**
- **Description:** Save dashboard layout.
- **Request Body:** `{"layout": [...], "language": "fr-FR"}`
- **Response (200 OK):** `{"status": "updated"}`

### 4.3 Partner API Integration

**6. GET `/partner/sync/status`**
- **Description:** Check the current health and sync lag of the external partner API.
- **Response (200 OK):**
  ```json
  {
    "partner_status": "online",
    "last_sync_timestamp": "2025-05-22T10:00:00Z",
    "lag_seconds": 45
  }
  ```

**7. POST `/partner/sync/trigger`**
- **Description:** Manually trigger a synchronization event (Admin only).
- **Response (202 Accepted):** `{"job_id": "sync-abc-123", "status": "queued"}`

### 4.4 Analytics & Rate Limiting

**8. GET `/analytics/usage`**
- **Description:** Get usage stats for API rate limiting.
- **Response (200 OK):**
  ```json
  {
    "total_requests_24h": 450000,
    "rate_limit_hits": 12,
    "p95_latency_ms": 185
  }
  ```

---

## 5. DATABASE SCHEMA

The system uses CockroachDB. All tables are distributed across three regions (us-east, us-west, europe-west).

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email` (unique), `password_hash`, `role` | User account data. |
| `shipments` | `shipment_id` | `partner_id` | `manifest_no`, `current_status`, `eta` | Core shipping data. |
| `shipment_events` | `event_id` | `shipment_id` | `event_type`, `timestamp`, `location` | Audit log of shipment moves. |
| `partners` | `partner_id` | - | `api_endpoint`, `api_key_encrypted`, `tier` | External partner details. |
| `user_preferences` | `pref_id` | `user_id` | `layout_json`, `language_code`, `timezone` | Dashboard and L10n settings. |
| `notifications` | `notif_id` | `user_id`, `shipment_id` | `channel`, `sent_at`, `status` | History of sent alerts. |
| `rate_limits` | `limit_id` | `partner_id` | `max_requests`, `window_seconds`, `burst` | Configuration for rate limits. |
| `usage_logs` | `log_id` | `user_id` | `endpoint_hit`, `response_time`, `status_code` | Telemetry for usage analytics. |
| `widgets` | `widget_id` | - | `widget_type`, `default_config`, `version` | Registry of available widgets. |
| `audit_trail` | `audit_id` | `user_id` | `action`, `table_affected`, `old_value`, `new_value` | ISO 27001 compliance log. |

### 5.2 Relationships
- `users` $\rightarrow$ `user_preferences` (1:1)
- `users` $\rightarrow$ `notifications` (1:N)
- `partners` $\rightarrow$ `shipments` (1:N)
- `shipments` $\rightarrow$ `shipment_events` (1:N)
- `shipments` $\rightarrow$ `notifications` (1:N)
- `partners` $\rightarrow$ `rate_limits` (1:1)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Beacon utilizes a strict three-tier environment strategy to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Iterative development and feature testing.
- **Infrastructure:** Small GKE cluster (3 nodes), shared CockroachDB instance.
- **Deployment:** Automatic deploy on every push to `develop` branch via GitHub Actions.
- **Data:** Anonymized sample data; no real partner API keys.

#### 6.1.2 Staging (Stage)
- **Purpose:** Final QA, Load Testing, and UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of Production (10 nodes), dedicated CockroachDB cluster.
- **Deployment:** Deployed on merge to `release/*` branches.
- **Data:** Sanitized production snapshots. Connects to the partner's Sandbox API.

#### 6.1.3 Production (Prod)
- **Purpose:** Live external partner integration and user access.
- **Infrastructure:** High-availability GKE cluster across 3 GCP regions. Multi-region CockroachDB cluster.
- **Deployment:** Blue-Green deployment. New version is deployed to "Green" environment, tested, and then traffic is shifted via the Load Balancer.
- **Security:** Strict IAM roles, VPC peering, and Secret Manager for API keys.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1. **Lint/Test:** `go fmt`, `go vet`, and `go test ./...` are run on every PR.
2. **Build:** Docker images are built and pushed to Google Artifact Registry.
3. **Deploy:** `kubectl` applies the manifests to the target environment.
4. **Smoke Test:** A suite of 20 critical path tests is run against the Green environment before the traffic shift.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every Go function must have a corresponding `_test.go` file.
- **Requirement:** 80% code coverage for the `core` and `integration` packages.
- **Tooling:** `testing` package, `testify/assert` for readable assertions.
- **Mocking:** Use of `mockgen` to create mocks for the database and external API clients.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the Go services and the CockroachDB/Redis layers.
- **Method:** Use of **Testcontainers** to spin up a real CockroachDB instance in a Docker container during the test run.
- **Focus:** Ensuring gRPC contracts are honored and database migrations do not break existing data.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulating real user journeys from the frontend to the external partner API.
- **Tooling:** Playwright for frontend flows; k6 for load testing.
- **Scenarios:**
    - User logs in $\rightarrow$ modifies dashboard $\rightarrow$ searches for shipment $\rightarrow$ triggers notification.
    - Partner API sends a status update $\rightarrow$ Beacon processes it $\rightarrow$ User receives push notification.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements are 10x current capacity with no infra budget. | High | Critical | **Escalate to steering committee** for additional funding. Implement aggressive caching in Redis to reduce DB load. |
| R-02 | Competitor is building the same product and is 2 months ahead. | Medium | High | **Document workarounds** and share with the team. Accelerate the "High Priority" features (Dashboard, Rate Limiting). |
| R-03 | Key team member on medical leave for 6 weeks (Current Blocker). | High | Medium | Redistribute tasks among the remaining 7 members. Beatriz to take over some technical oversight. |
| R-04 | External partner API changes schema without notice. | Medium | High | Implement a "Schema Validation Layer" that alerts the team immediately if an unexpected field is received. |
| R-05 | Technical debt: 3,000-line 'God class' for Auth/Logging/Email. | High | Medium | Schedule "Refactor Fridays." Incrementally move functionality into separate services. |

**Impact Matrix:**
- **Low:** Minimal delay, no budget impact.
- **Medium:** 1-2 week delay, manageable cost.
- **High:** Project milestone missed, significant cost increase.
- **Critical:** Project failure, board-level visibility.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Current - 2025-02-01)
- **Focus:** Infrastructure setup, CockroachDB schema finalization, and basic API connectivity.
- **Dependencies:** GCP Project approval, Partner API key delivery.
- **Key Goal:** Establish the "Modular Monolith" base.

### 9.2 Phase 2: Core Feature Build (2025-02-01 - 2025-06-01)
- **Focus:** Development of the Customizable Dashboard and Rate Limiting.
- **Dependencies:** Completion of the Auth layer (refactoring the 'God class').
- **Key Goal:** Functional internal alpha.

### 9.3 Phase 3: Integration & Scaling (2025-06-01 - 2025-08-15)
- **Focus:** Advanced Search, Notification System, and Performance Tuning for 10x load.
- **Dependencies:** Elasticsearch cluster deployment.
- **Milestone 1 (2025-08-15):** Stakeholder demo and sign-off.

### 9.4 Phase 4: Beta & Onboarding (2025-08-16 - 2025-10-15)
- **Focus:** L10n/I18n finalization, Beta testing with select clients.
- **Milestone 2 (2025-10-15):** First paying customer onboarded.

### 9.5 Phase 5: Stability & Optimization (2025-10-16 - 2025-12-15)
- **Focus:** Bug fixing, p95 latency optimization, and final security audits.
- **Milestone 3 (2025-12-15):** Post-launch stability confirmed.

---

## 10. MEETING NOTES

*Note: Per team culture, these are summaries of recorded video calls that are rarely re-watched.*

### Meeting 1: Architecture Alignment (2024-06-12)
**Attendees:** Beatriz, Devika, Gia, Dmitri.
- **Discussion:** Debate over whether to go full microservices immediately or start with a modular monolith.
- **Decision:** Beatriz decided on a modular monolith. Devika expressed concerns about the "God class" creating a bottleneck.
- **Outcome:** Agreed to prioritize the refactor of the 3,000-line class in Phase 1. Dmitri assigned to map the dependencies of the God class.
- **Slack Follow-up:** Decision finalized in `#beacon-dev` channel.

### Meeting 2: The "10x Load" Crisis (2024-07-05)
**Attendees:** Beatriz, Devika, Gia.
- **Discussion:** Review of performance requirements. The board expects 10x current capacity, but the infrastructure budget is frozen.
- **Decision:** Devika suggested that without more nodes, the p95 latency will spike.
- **Outcome:** Beatriz to escalate this to the steering committee. Gia noted that the ISO 27001 requirements might add overhead to the latency.
- **Slack Follow-up:** Beatriz posted the escalation email draft in Slack for team review.

### Meeting 3: Partner API Sync Timeline (2024-08-20)
**Attendees:** Beatriz, Devika, Dmitri.
- **Discussion:** The external partner shifted their API release date back by 3 weeks.
- **Decision:** We cannot move our Milestone 1 date, but we can mock the API responses.
- **Outcome:** Dmitri to build a "Mock Partner Server" using Go to allow the team to continue developing the Dashboard and Search features.
- **Slack Follow-up:** Mock server specs shared as a PDF in the channel.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$5,250,000** (Flagship Initiative)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,412,500 | 8 engineers, 1 PM, 1 QA (part-time). Includes bonuses. |
| **Infrastructure** | 20% | $1,050,000 | GCP GKE, CockroachDB Cloud, Redis, Elasticsearch. |
| **Tools & Licensing** | 5% | $262,500 | GitHub Enterprise, SendGrid, Twilio, Datadog. |
| **Contingency** | 10% | $525,000 | Set aside for "Emergency Infrastructure" or contractor help. |

*Note: Budget is subject to board-level reporting every quarter.*

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt Analysis
The current `CoreEngine` class in the legacy system is approximately 3,100 lines of Go code. It handles:
1.  **Authentication:** JWT validation and session management.
2.  **Logging:** Wrapper for structured logging to Cloud Logging.
3.  **Email:** SMTP client logic for shipping alerts.
4.  **State Management:** Global shipment cache.

**Refactor Plan:**
- **Step 1:** Move SMTP logic to `internal/notifications`.
- **Step 2:** Move JWT logic to `internal/auth`.
- **Step 3:** Move logging to a global middleware.
- **Step 4:** Convert `CoreEngine` into a thin interface that delegates to these new packages.

### Appendix B: ISO 27001 Compliance Checklist
To maintain certification, Beacon must implement:
- **Access Control:** All access to the production environment must be through a bastion host with MFA.
- **Data Encryption:** All PII (Personally Identifiable Information) in the `users` and `shipments` tables must be encrypted at the application layer.
- **Audit Logging:** Every `UPDATE` or `DELETE` operation in CockroachDB must be mirrored in the `audit_trail` table with the `user_id` and `timestamp`.
- **Vulnerability Scanning:** GitHub Actions must run Snyk or Trivy on every build to detect vulnerable dependencies.