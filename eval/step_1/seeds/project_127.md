# PROJECT SPECIFICATION: KEYSTONE (v1.0.4)
**Company:** Crosswind Labs  
**Industry:** Aerospace  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Document Owner:** Haruki Fischer (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Keystone" is a strategic imperative for Crosswind Labs. The current legacy system, characterized by monolithic instability and poor user experience, has reached a critical failure point. Catastrophic user feedback from our tier-1 aerospace clients indicates that the existing platform is no longer fit for purpose, specifically regarding data integrity, latency, and the inability to scale under the rigorous demands of modern aerospace logistics and telemetry.

In the aerospace sector, the cost of failure is not merely financial but operational. The legacy system’s inability to handle concurrent data streams and its lack of a transparent audit trail have led to customer churn and a damaged brand reputation. Keystone is not a mere "update" but a complete rebuild of the customer-facing product. By migrating to a modern microservices architecture, we are addressing the core pain points: system fragility, opaque data flows, and inefficient resource utilization.

### 1.2 Strategic Objectives
The primary goal of Keystone is to stabilize the customer experience while drastically reducing the operational cost of maintaining the platform. The project focuses on high-availability, strict auditability via Event Sourcing, and a scalable infrastructure capable of handling a 10x increase in load without linear increases in cost.

### 1.3 ROI Projection
Given the lean budget of $150,000, the Return on Investment (ROI) is calculated based on three primary vectors:
1.  **Churn Reduction:** By resolving the "catastrophic" user experience issues, we project a 20% increase in customer retention over the first 12 months post-launch.
2.  **Infrastructure Efficiency:** A mandatory success criterion is the reduction of cost-per-transaction by 35%. By moving from legacy VM-based hosting to a highly optimized Kubernetes environment on GCP with a CockroachDB backend, we expect to save approximately $45,000 per annum in cloud spend.
3.  **Operational Velocity:** The transition to a CQRS (Command Query Responsibility Segregation) pattern will allow the team to iterate on read-models without risking the integrity of the write-store, reducing the time-to-market for new features by an estimated 40%.

### 1.4 Financial Constraints
The budget is strictly capped at $150,000. This is a "shoestring" budget for a project of this magnitude. Every dollar is scrutinized by executive leadership. Consequently, the project prioritizes "Critical" launch blockers over "Nice to have" features. Any deviation from the budget requires a formal request to Haruki Fischer and a subsequent audit by the finance department.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Keystone utilizes a distributed microservices architecture implemented in Go (Golang). The choice of Go is driven by the need for high concurrency and low memory overhead, which is essential given the infrastructure budget constraints. Communication between services is handled via gRPC for internal high-performance calls and REST/JSON for external-facing API gateways.

### 2.2 Architecture Pattern: CQRS and Event Sourcing
To meet the audit-critical requirements of the aerospace industry, Keystone implements **Command Query Responsibility Segregation (CQRS)** combined with **Event Sourcing**.

-   **Command Side:** Handles the intent to change state. Every change is recorded as an immutable event in the Event Store (CockroachDB).
-   **Query Side:** Asynchronous projections consume these events to build optimized read-models. This ensures that the "Source of Truth" is an append-only log of events, providing a perfect audit trail for every transaction.

### 2.3 ASCII Infrastructure Diagram
```text
[ External User ]  ---> [ GCP Cloud Load Balancer ]
                                |
                                v
                      [ Kubernetes Cluster (GKE) ]
                                |
        ________________________|________________________
       |                        |                        |
 [ API Gateway ] <---gRPC---> [ Order Service ] <---gRPC---> [ File Service ]
       |                        |                        |
       |                  [ Event Store ]           [ Cloud Storage ]
       |                 (CockroachDB)              (GCP Bucket)
       |                        |                        |
       |                        v                        |
       |               [ Projection Engine ]              |
       |                        |                         |
       |                        v                        |
       |               [ Read-Model DB ] <-----------------
       |                 (CockroachDB)
       |________________________|_________________________|
                                |
                    [ External Services / Webhooks ]
```

### 2.4 Data Layer
**CockroachDB** was selected as the primary database for its distributed SQL capabilities, ensuring that the platform remains resilient across multiple GCP zones. The database handles both the Event Store (immutable logs) and the materialized read-views.

### 2.5 Deployment Strategy
Keystone employs a modern CI/CD pipeline using:
-   **LaunchDarkly:** Used for feature flagging. All new features are deployed "dark" and toggled on for specific user segments.
-   **Canary Releases:** Traffic is shifted incrementally (1% -> 5% -> 25% -> 100%) to ensure that new builds do not introduce regressions in the high-stakes aerospace environment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Priority: Critical | Status: In Review)
**Description:** 
Because Keystone is a rebuild following catastrophic feedback, we cannot rely on "gut feeling" for UI/UX decisions. A robust A/B testing framework is required to validate design changes against actual user behavior. This framework is baked directly into the LaunchDarkly feature flag system.

**Technical Requirements:**
-   **Integration:** The framework must interface with the LaunchDarkly SDK to assign users to "Treatment" or "Control" groups based on their `user_id` and `org_id`.
-   **Telemetry:** Every interaction within an A/B test must be logged to the usage analytics service with a `correlation_id` linking the user to their specific test variant.
-   **Statistical Significance:** The system must track conversion events (e.g., successful file upload, completed telemetry report) and calculate p-values to determine if a variant is statistically superior.
-   **Dynamic Configuration:** Product managers must be able to adjust the weight of the distribution (e.g., 10% A, 90% B) without redeploying code.

**User Workflow:**
1. Product Lead defines a hypothesis (e.g., "Changing the dashboard layout to a grid view increases navigation speed").
2. Engineering creates a feature flag `exp_dashboard_grid_v1`.
3. Users are randomly assigned via the SDK.
4. Analytics collect time-on-page and click-through rates.
5. The winning variant is promoted to 100% rollout.

### 3.2 File Upload with Virus Scanning & CDN (Priority: Critical | Status: In Design)
**Description:** 
Aerospace clients upload large telemetry datasets and technical blueprints. Security is paramount; no file can enter the system without being scanned for malware and viruses. To ensure global accessibility for remote hangars and labs, files must be distributed via a Content Delivery Network (CDN).

**Technical Requirements:**
-   **Ingest Pipeline:** Files are uploaded via a multipart stream to a temporary GCP bucket.
-   **Scanning Layer:** A dedicated "Scanner Service" triggers upon upload. It utilizes ClamAV or a similar enterprise-grade scanner to check for signatures. If a virus is detected, the file is immediately quarantined and the user is notified via a `422 Unprocessable Entity` response.
-   **CDN Integration:** Once cleared, files are moved to a "Production Bucket" and served via Google Cloud CDN with signed URLs for security.
-   **Chunked Uploads:** To support files up to 5GB, the API must support chunked uploads with checksum verification (`SHA-256`) for each part to prevent corruption.

**Validation Logic:**
-   `Max_File_Size`: 5GB.
-   `Allowed_Extensions`: .pdf, .csv, .json, .dwg, .step.
-   `Scanning_Timeout`: 120 seconds.

### 3.3 API Rate Limiting and Usage Analytics (Priority: High | Status: Not Started)
**Description:** 
To prevent system abuse and manage infrastructure costs on our shoestring budget, we must implement a strict rate-limiting mechanism and a granular analytics suite.

**Technical Requirements:**
-   **Token Bucket Algorithm:** Implement a token bucket algorithm at the API Gateway level.
-   **Tiered Limits:** Rate limits must be configurable per organization. (e.g., Basic: 100 req/min, Premium: 1000 req/min).
-   **Headers:** Every response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
-   **Analytics Pipeline:** All requests are asynchronously pushed to a Kafka-like stream (or GCP Pub/Sub) to be indexed into the usage analytics database.
-   **Metrics:** Track 4xx/5xx error rates, latency (p95, p99), and most-called endpoints per user.

**Implementation Detail:**
The rate limiter will use a Redis cache for fast atomic increments of token counts, ensuring that the latency overhead for checking the limit is $< 2ms$.

### 3.4 Webhook Integration Framework (Priority: High | Status: Complete)
**Description:** 
Allowing third-party aerospace tools to react to events within Keystone. This framework enables a "push" model where external systems are notified of state changes (e.g., "Telemetry Report Generated").

**Technical Requirements:**
-   **Event Registry:** Users can register a URL and a set of events they wish to subscribe to.
-   **Retry Logic:** Exponential backoff (1m, 5m, 15m, 1h) for failed deliveries.
-   **Security:** Every webhook payload must be signed with an `X-Keystone-Signature` (HMAC-SHA256) to allow the receiver to verify the sender.
-   **Payload Format:** JSON structured as: `{"event": "string", "timestamp": "ISO8601", "data": {}}`.

**Current State:**
This feature is complete and verified. It is currently being used by the internal QA team to trigger automated test suites.

### 3.5 SSO Integration with SAML and OIDC (Priority: Low | Status: In Review)
**Description:** 
Enterprises in the aerospace sector require Single Sign-On (SSO) to manage user access centrally. This feature integrates Keystone with providers like Okta, Azure AD, and Google Workspace.

**Technical Requirements:**
-   **SAML 2.0 Support:** Ability to ingest metadata XML from the Identity Provider (IdP).
-   **OIDC Flow:** Support for Authorization Code Flow with PKCE for secure authentication.
-   **Just-In-Time (JIT) Provisioning:** Automatically create a user profile in CockroachDB upon the first successful SSO login if the user exists in the IdP.
-   **Attribute Mapping:** Map IdP claims (e.g., `groups`, `department`) to Keystone internal roles (`Admin`, `Viewer`, `Operator`).

**Status Note:** 
Given the budget and the "Critical" status of other features, this remains a low priority. It is in review to determine if a third-party managed service (like Auth0) is more cost-effective than building a custom implementation.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path `/api/v1`.

### 4.1 Authentication & Identity
**`POST /auth/login`**
-   **Description:** Authenticate user and return JWT.
-   **Request:** `{"email": "user@crosswind.com", "password": "..."}`
-   **Response:** `200 OK {"token": "eyJ...", "expires_at": "2023-10-25T00:00:00Z"}`

**`GET /auth/session`**
-   **Description:** Validate current session token.
-   **Response:** `200 OK {"user_id": "uuid", "role": "admin"}`

### 4.2 File Management
**`POST /files/upload`**
-   **Description:** Initiates a chunked upload.
-   **Request:** `{"filename": "telemetry_01.csv", "total_chunks": 10, "checksum": "sha256..."}`
-   **Response:** `201 Created {"upload_id": "up_987", "endpoint": "/files/upload/up_987"}`

**`GET /files/download/{file_id}`**
-   **Description:** Retrieves a signed CDN URL.
-   **Response:** `200 OK {"url": "https://cdn.keystone.com/files/abc?sig=xyz", "expires_in": 3600}`

### 4.3 A/B Testing & Config
**`GET /config/features`**
-   **Description:** Returns active feature flags for the current user.
-   **Response:** `200 OK {"features": {"exp_dashboard_grid": true, "new_upload_flow": false}}`

**`POST /config/ab-test/event`**
-   **Description:** Logs a conversion event for an A/B test.
-   **Request:** `{"test_id": "grid_test", "event_name": "click_nav", "value": 1}`
-   **Response:** `204 No Content`

### 4.4 Webhooks
**`POST /webhooks/subscriptions`**
-   **Description:** Create a new webhook subscription.
-   **Request:** `{"target_url": "https://client.com/hook", "events": ["file.uploaded", "report.finalized"]}`
-   **Response:** `201 Created {"subscription_id": "sub_123"}`

**`DELETE /webhooks/subscriptions/{id}`**
-   **Description:** Remove a subscription.
-   **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The database is hosted on CockroachDB. Relationships are maintained via UUIDs.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role`, `org_id` | `orgs(1:N)` | User identity and auth |
| `orgs` | `org_id` | `name`, `billing_tier`, `created_at` | `users(1:N)` | Client organization data |
| `events` | `event_id` | `aggregate_id`, `event_type`, `payload`, `version` | `aggregates(1:N)` | Event Store (Immutable) |
| `aggregates` | `aggregate_id` | `type`, `current_version`, `last_updated` | `events(1:1)` | CQRS Aggregate roots |
| `files` | `file_id` | `owner_id`, `filename`, `status`, `cdn_url` | `users(1:N)` | File metadata and status |
| `file_chunks` | `chunk_id` | `file_id`, `sequence_num`, `checksum` | `files(1:N)` | Tracks multipart uploads |
| `webhooks` | `hook_id` | `org_id`, `target_url`, `secret` | `orgs(1:N)` | Webhook registration |
| `webhook_logs` | `log_id` | `hook_id`, `response_code`, `attempt_num` | `webhooks(1:N)` | Delivery audit trail |
| `ab_tests` | `test_id` | `name`, `variant_a_weight`, `variant_b_weight` | N/A | A/B test definitions |
| `user_variants` | `id` | `user_id`, `test_id`, `assigned_variant` | `users, ab_tests` | User mapping to test groups |

### 5.2 Schema Logic
The `events` table is the core of the system. Any change to a "File" or "User" does not update a row in the `files` or `users` table directly in the write-path. Instead, an event (e.g., `FileUploadedEvent`) is appended to the `events` table. A background worker then updates the `files` table (the read-model) to reflect the current state.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Keystone utilizes three distinct environments to ensure stability and rigorous testing.

#### 6.1.1 Development (Dev)
-   **Purpose:** Feature development and initial integration testing.
-   **Infrastructure:** Small GKE cluster with preemptible nodes to save costs.
-   **Database:** Single-node CockroachDB instance.
-   **Deployment:** Automatic deploy on every commit to `develop` branch.

#### 6.1.2 Staging (Stage)
-   **Purpose:** Pre-production validation, QA regression, and stakeholder demos.
-   **Infrastructure:** Mirror of production architecture but scaled down (3 nodes).
-   **Database:** 3-node CockroachDB cluster.
-   **Deployment:** Manual trigger from `develop` to `release` branch.

#### 6.1.3 Production (Prod)
-   **Purpose:** Live customer traffic.
-   **Infrastructure:** High-availability GKE cluster across 3 GCP zones.
-   **Database:** Full multi-region CockroachDB cluster.
-   **Deployment:** Canary releases via LaunchDarkly and Kubernetes ingress traffic splitting.

### 6.2 Infrastructure Cost Management
With a $150,000 budget, infrastructure is a major concern.
-   **Spot Instances:** Dev and Stage environments exclusively use GCP Spot VMs.
-   **Autoscaling:** HPA (Horizontal Pod Autoscaler) is configured based on CPU and Memory metrics to scale down during off-peak hours (midnight to 6 AM UTC).
-   **Storage:** Old telemetry files are automatically moved to "Coldline" storage after 90 days of inactivity.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
-   **Approach:** Every Go package must have corresponding `_test.go` files.
-   **Requirement:** Minimum 80% code coverage for all business logic in the `internal/domain` package.
-   **Tooling:** `go test` with race detector enabled.

### 7.2 Integration Testing
-   **Approach:** Focus on the interaction between microservices and the database.
-   **Requirement:** Use `Testcontainers` to spin up a temporary CockroachDB instance for every test suite to ensure a clean state.
-   **Focus:** Verify gRPC contract adherence and Event Sourcing projection accuracy.

### 7.3 End-to-End (E2E) Testing
-   **Approach:** Black-box testing of the user journey.
-   **Tooling:** Playwright for frontend automation; Postman/Newman for API flow validation.
-   **Scenario:** A full cycle: *User Login $\rightarrow$ File Upload $\rightarrow$ Virus Scan $\rightarrow$ Webhook Notification $\rightarrow$ File Download.*

### 7.4 Quality Assurance (Dedicated QA)
The dedicated QA engineer is responsible for the "Bug Bash" held every Friday. No ticket can be moved to "Closed" in JIRA without a QA sign-off and a linked test report.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Performance requirements are 10x legacy capacity with no extra budget. | High | Critical | Accept risk. Implement strict monitoring; optimize Go runtime; use aggressive caching. |
| **R-02** | Primary vendor dependency announced EOL (End-of-Life). | Medium | High | Monitor vendor updates weekly. If no resolution, de-scope dependent features before Milestone 2. |
| **R-03** | Design disagreement between Product and Engineering Leads. | High | Medium | Escalate to executive steering committee; force decision via "Design Spike" and prototype. |
| **R-04** | Technical debt: Hardcoded config values in 40+ files. | High | Medium | Systematic migration to `env` variables and Secret Manager during Sprint 1. |

### 8.1 Probability/Impact Matrix
-   **Critical:** Immediate project failure or launch blocker.
-   **High:** Significant delay or budget overrun.
-   **Medium:** Manageable with effort.
-   **Low:** Minimal impact on timeline.

---

## 9. TIMELINE

The project is divided into three major phases leading up to the final onboarding.

### 9.1 Phase 1: Foundation & Performance (Current $\rightarrow$ 2025-06-15)
-   **Focus:** Infrastructure setup, Go microservices boilerplate, and performance tuning.
-   **Key Dependency:** Resolution of the design disagreement between leads.
-   **Milestone 1:** Performance benchmarks met (10x capacity validation).

### 9.2 Phase 2: Feature Completion & Hardening (2025-06-16 $\rightarrow$ 2025-08-15)
-   **Focus:** Implementing A/B testing and File Upload/Scanning. Completion of the API rate limiter.
-   **Key Dependency:** Successful penetration testing of the file upload pipeline.
-   **Milestone 2:** Stakeholder demo and formal sign-off.

### 9.3 Phase 3: Pilot & Onboarding (2025-08-16 $\rightarrow$ 2025-10-15)
-   **Focus:** Beta testing with a limited user group, final bug fixes, and SSO integration (if budget allows).
-   **Key Dependency:** Passing the external audit on the first attempt.
-   **Milestone 3:** First paying customer onboarded.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per the team dynamic, there are no formal meeting minutes. Decisions are captured in Slack threads.

### Meeting 1: Infrastructure Review (Thread: #eng-keystone-arch)
**Date:** 2023-11-02
**Participants:** Haruki, Sienna, Hana
-   **Sienna:** "The current frontend is struggling with the gRPC-web bridge. Can we move to a BFF (Backend for Frontend) pattern?"
-   **Haruki:** "Yes, but only if it doesn't add more than 20ms of latency. We are already on a shoestring budget for GCP. I'll approve the BFF if Sienna can prove it doesn't require a larger instance size."
-   **Hana:** "I'm worried about the virus scanning latency. If we do it synchronously, the user will time out."
-   **Decision:** File uploads will be asynchronous. User gets a `202 Accepted`, and the status is updated via webhook or polling.

### Meeting 2: The Design Conflict (Thread: #prod-eng-sync)
**Date:** 2023-11-15
**Participants:** Haruki, Product Lead (External), Sienna
-   **Product Lead:** "The dashboard needs to be a real-time stream of all aerospace telemetry. I don't care about the cost."
-   **Haruki:** "I do care. We have a $150k budget total. Real-time streams for 10x the current users will bankrupt the project in two months."
-   **Sienna:** "Could we do 'near real-time' with 30-second polling or WebSockets with a strict throttle?"
-   **Decision:** Compromise reached—dashboard will use a "Refresh" button and a 5-minute auto-update. Real-time is deferred to v2.0.

### Meeting 3: Security Audit Planning (Thread: #security-audit)
**Date:** 2023-12-01
**Participants:** Hana, Haruki, Kenji
-   **Hana:** "We have no formal compliance framework (like SOC2), but we need to pass the external audit for the first customer."
-   **Kenji:** "I found 12 files where the DB password is hardcoded. I'm cleaning them up now."
-   **Hana:** "Wait, it's 40+ files. We need a script to find all strings that look like credentials. We can't fail the audit because of a leaked password in a git commit."
-   **Decision:** Kenji is assigned a 'Technical Debt' sprint to move all configs to GCP Secret Manager.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000  
**Currency:** USD

| Category | Allocated Amount | Percentage | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $90,000 | 60% | 6-person team (averaged over project duration) |
| **Infrastructure** | $30,000 | 20% | GCP (GKE, CockroachDB, Cloud Storage, CDN) |
| **Software/Tools** | $15,000 | 10% | LaunchDarkly, GitHub Enterprise, Sentry |
| **External Audit** | $10,000 | 6.7% | Third-party penetration test & audit |
| **Contingency** | $5,000 | 3.3% | Emergency buffer for critical blockers |

**Budget Note:** Due to the "shoestring" nature of this budget, any overage in the Infrastructure category must be offset by a reduction in the Contingency fund.

---

## 12. APPENDICES

### Appendix A: gRPC Service Definition (Protobuf)
The internal communication utilizes `.proto` files. Below is the definition for the `FileService`.

```protobuf
syntax = "proto3";
package keystone.files;

service FileService {
  rpc InitiateUpload(UploadRequest) returns (UploadResponse);
  rpc UploadChunk(ChunkRequest) returns (ChunkResponse);
  rpc GetFileStatus(StatusRequest) returns (StatusResponse);
}

message UploadRequest {
  string filename = 1;
  int32 total_chunks = 2;
  string checksum = 3;
}

message UploadResponse {
  string upload_id = 1;
}

message ChunkRequest {
  string upload_id = 1;
  int32 sequence_num = 2;
  bytes data = 3;
}

message ChunkResponse {
  bool success = 1;
}

message StatusRequest {
  string file_id = 1;
}

message StatusResponse {
  string status = 2; // e.g., "SCANNING", "CLEARED", "INFECTED"
  string cdn_url = 3;
}
```

### Appendix B: Event Sourcing State Transition Table
This table defines how events translate into the read-model for the `Files` domain.

| Event Type | Payload | Read-Model Effect |
| :--- | :--- | :--- |
| `FileUploadInitiated` | `file_id`, `user_id`, `size` | Create row in `files` table; status = `PENDING` |
| `ChunkUploaded` | `file_id`, `chunk_id` | Increment `chunks_received` count |
| `VirusScanStarted` | `file_id`, `timestamp` | Update status = `SCANNING` |
| `VirusScanCompleted` | `file_id`, `result` | If result == `CLEAN`, status = `AVAILABLE`. If `DIRTY`, status = `QUARANTINED` |
| `CdnDistributionSet` | `file_id`, `url` | Update `cdn_url` field in `files` table |