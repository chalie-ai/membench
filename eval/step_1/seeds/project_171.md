# PROJECT SPECIFICATION: PROJECT JETSTREAM
**Document Version:** 1.0.4  
**Status:** Active/Baseline  
**Last Updated:** 2024-10-24  
**Classification:** Confidential - Internal Only  
**Project Owner:** Xiomara Kim, VP of Product  
**Organization:** Bridgewater Dynamics

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Jetstream is a flagship greenfield initiative commissioned by Bridgewater Dynamics. The objective is the development of a sophisticated internal enterprise tool designed to penetrate a new, untapped market segment within the cybersecurity industry. While Bridgewater Dynamics possesses a strong legacy in infrastructure and networking, Jetstream represents a strategic pivot into high-velocity cybersecurity automation and intelligence orchestration.

Given that the company has never operated in this specific market, Jetstream is not merely a tool but a market-entry vehicle. It is designed to provide an integrated ecosystem for real-time threat detection, notification, and third-party orchestration, leveraging a modern, high-performance technology stack to outperform existing legacy systems in the industry.

### 1.2 Business Justification
The current cybersecurity landscape is characterized by fragmented toolsets and high latency in response times. By building Jetstream, Bridgewater Dynamics intends to bridge the gap between raw data ingestion and actionable intelligence. The business justification rests on three pillars:
1.  **Market Diversification:** Reducing reliance on legacy revenue streams by entering a high-growth cybersecurity niche.
2.  **Operational Efficiency:** Moving away from monolithic legacy systems to a microservices-based, event-driven architecture.
3.  **Competitive Advantage:** Utilizing Rust for the backend to achieve memory safety and execution speeds that exceed current industry standards.

### 1.3 ROI Projection and Financial Impact
With a total budget allocation exceeding $5,000,000, Jetstream is a high-stakes investment with board-level reporting requirements. The projected Return on Investment (ROI) is calculated based on a three-year horizon:

*   **Direct Cost Reduction:** The transition from legacy polling systems to the Jetstream event-driven architecture is projected to reduce the cost per transaction by 35%. Based on current volume, this represents an annual operational saving of approximately $1.2M.
*   **Market Capture:** By targeting an NPS (Net Promoter Score) of 40+ within the first quarter of release, the company anticipates a conversion rate of 15% from pilot users to full enterprise contracts, projecting an additional $8M in annual recurring revenue (ARR) by Year 2.
*   **Resource Optimization:** The use of Cloudflare Workers and SQLite at the edge minimizes centralized server costs, projecting a 20% reduction in cloud infrastructure spend compared to traditional AWS/Azure deployments.

The total projected 3-year ROI is estimated at 210%, contingent upon hitting the milestone dates set for 2026.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Jetstream is built upon a highly decentralized, event-driven architecture designed for extreme low latency and high availability. The core philosophy is to push computation as close to the user as possible (the "edge") while maintaining a robust, type-safe backend for complex business logic.

### 2.2 The Technology Stack
*   **Backend:** Rust (utilizing the Actix-web framework for high-performance HTTP handling).
*   **Frontend:** React 18+ with TypeScript and Tailwind CSS.
*   **Edge Storage:** SQLite (deployed via Cloudflare D1) for low-latency local state and caching.
*   **Compute:** Cloudflare Workers for global distribution and request routing.
*   **Message Broker:** Apache Kafka for asynchronous communication between microservices.
*   **Database (Central):** PostgreSQL (for persistent, relational enterprise data).

### 2.3 Architectural Diagram (ASCII)

```text
[ User Browser ] <--- HTTPS/WSS ---> [ Cloudflare Workers ]
                                            |
                                            | (Edge Cache/State)
                                            v
                                     [ SQLite (Edge) ]
                                            |
                                            | (API Gateway / Rust Backend)
                                            v
    +-----------------------------------------------------------------------+
    |                          EVENT BUS (Apache Kafka)                     |
    +-----------------------------------------------------------------------+
           ^                        ^                       ^
           |                        |                       |
   [ Notification Svc ]    [ Webhook Framework ]    [ Data Import/Export ]
           |                        |                       |
           v                        v                       v
    [ SMTP/Twilio/APNS ]    [ 3rd Party APIs ]      [ S3/Enterprise Storage ]
           |                        |                       |
           +------------------------+-----------------------+
                                    |
                          [ Central PostgreSQL DB ]
```

### 2.4 Communication Patterns
The system utilizes a hybrid communication model:
1.  **Synchronous (REST/gRPC):** Used for critical paths such as SSO authentication and real-time user queries.
2.  **Asynchronous (Event-Driven):** All state-changing operations (e.g., triggering a notification, processing a data import) are published to Kafka topics. This ensures that a failure in the notification service does not block the primary user action.

### 2.5 Deployment Strategy
Jetstream employs a strict **Continuous Deployment (CD)** pipeline. Every pull request (PR) that passes the automated test suite and is merged into the `main` branch is automatically deployed to the production environment. This allows the team of 8 to maintain high velocity and ensures that the "latest" version is always the "deployed" version.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System
**Priority:** Critical (Launch Blocker) | **Status:** Complete

The Notification System is the heartbeat of Jetstream, responsible for ensuring that cybersecurity alerts reach the end-user through the most efficient channel. It is designed as a multi-channel dispatcher capable of handling millions of events per hour.

**Functional Requirements:**
*   **Omni-channel Support:** The system must support Email (via SendGrid), SMS (via Twilio), In-App (via WebSockets), and Push Notifications (via Firebase Cloud Messaging).
*   **Preference Engine:** Users must be able to define granular preferences (e.g., "Critical alerts via SMS, Low-priority via Email").
*   **Templating:** Use of a Liquid-based templating engine to allow dynamic content injection into alerts.
*   **Retry Logic:** Exponential backoff for failed deliveries to third-party providers.

**Technical Implementation:**
The service consumes `notification_requested` events from Kafka. It looks up the user's notification preferences in the PostgreSQL database and routes the message to the appropriate provider. To prevent "alert fatigue," the system implements a throttling mechanism that aggregates multiple similar alerts into a single summary notification if the frequency exceeds 5 per minute.

### 3.2 Webhook Integration Framework
**Priority:** High | **Status:** Complete

The Webhook Framework allows Jetstream to act as both a producer and consumer of events, integrating with a vast array of third-party cybersecurity tools (e.g., Splunk, CrowdStrike, PagerDuty).

**Functional Requirements:**
*   **Dynamic Endpoint Generation:** Each user can generate a unique webhook URL for incoming data.
*   **Payload Transformation:** A middleware layer that allows users to map incoming JSON fields to Jetstream's internal data model.
*   **Signature Verification:** Support for HMAC-SHA256 signatures to ensure that incoming webhooks are from trusted sources.
*   **Outbound Triggering:** Ability to trigger an external webhook based on internal Jetstream events.

**Technical Implementation:**
Built using Rust's `serde` library for high-speed JSON parsing. The framework maintains a registry of "Webhook Subscriptions" in the database. When an internal event occurs, the `WebhookDispatcher` service identifies all matching subscriptions and sends asynchronous POST requests using the `reqwest` library.

### 3.3 SSO Integration (SAML & OIDC)
**Priority:** Medium | **Status:** Complete

To fit into the enterprise environment of Bridgewater Dynamics' clients, Jetstream provides robust Single Sign-On (SSO) capabilities, ensuring that identity management is centralized.

**Functional Requirements:**
*   **SAML 2.0 Support:** Integration with providers like Okta and Azure AD.
*   **OIDC Support:** Integration with Google Workspace and GitHub Enterprise.
*   **Just-In-Time (JIT) Provisioning:** Automatic account creation upon first successful SSO login.
*   **Attribute Mapping:** Ability to map SAML assertions to internal user roles (e.g., `Admin`, `Analyst`, `Viewer`).

**Technical Implementation:**
The system uses a dedicated `AuthService` implemented in Rust. For SAML, it handles the XML parsing and signature verification using the `saml2` crate. For OIDC, it implements the Authorization Code Flow with PKCE. All session tokens are issued as JWTs (JSON Web Tokens) with a 12-hour expiration, stored in secure, HttpOnly cookies.

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

This feature allows users to migrate large volumes of cybersecurity logs and configurations into Jetstream and export them for external auditing.

**Functional Requirements:**
*   **Auto-Detection:** The system must automatically detect whether an uploaded file is CSV, JSON, XML, or Parquet without user input.
*   **Schema Mapping:** An interactive UI for users to map detected columns to the database schema.
*   **Bulk Processing:** Ability to handle files up to 10GB using stream-processing to avoid memory overflow.
*   **Export Scheduling:** Automated weekly exports to S3-compatible storage.

**Technical Implementation (Planned):**
The backend will utilize the `polars` library in Rust for high-performance data frame manipulation and format detection. The process will be split into a two-stage pipeline: (1) an "Ingestion Stage" that uploads the file to an S3 bucket and (2) a "Processing Stage" where a worker reads the file in chunks, validates the format, and performs bulk inserts into PostgreSQL. **Current Blockage:** Integration with the partner's legacy API for schema validation is currently failing.

### 3.5 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Blocked

Given that cybersecurity analysts may operate in "air-gapped" or low-connectivity environments, Jetstream must remain functional without a constant internet connection.

**Functional Requirements:**
*   **Local State Persistence:** Use of SQLite via WebAssembly (WASM) in the browser to store active sessions and draft configurations.
*   **Optimistic UI:** Actions taken offline (e.g., updating a rule) should appear successful immediately.
*   **Conflict Resolution:** A "last-write-wins" strategy with an option for users to manually resolve conflicts during synchronization.
*   **Background Sync:** Use of Service Workers to push queued changes to the server once connectivity is restored.

**Technical Implementation (Planned):**
The frontend will implement a `SyncManager` that tracks a "Change Log" in the local SQLite database. Upon detecting a `network-online` event, the manager will iterate through the log and send a batch of `sync_requests` to the backend. The backend will validate the version timestamp of each record to prevent overwriting newer data. **Current Blockage:** Incompatibility between the current SQLite WASM build and the specific version of Cloudflare Workers' runtime.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /notifications/send`
Triggers a manual notification alert.
*   **Request Body:**
    ```json
    {
      "userId": "usr_9921",
      "channel": "sms",
      "priority": "critical",
      "message": "Intrusion detected in Sector 7G"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    { "jobId": "job_abc123", "status": "queued" }
    ```

### 4.2 `GET /webhooks/subscriptions`
Lists all active webhook integrations for the authenticated organization.
*   **Request:** `GET /api/v1/webhooks/subscriptions?orgId=org_55`
*   **Response (200 OK):**
    ```json
    [
      { "id": "wh_1", "targetUrl": "https://splunk.com/hook", "event": "threat_detected" }
    ]
    ```

### 4.3 `POST /auth/sso/saml/init`
Initiates the SAML authentication flow.
*   **Request Body:** `{ "idpEntityId": "https://okta.com/app/jetstream" }`
*   **Response (302 Redirect):** Redirects user to the Identity Provider's SSO URL.

### 4.4 `POST /data/import/upload`
Uploads a file for import with auto-detection.
*   **Request:** Multipart form-data containing `file` and `orgId`.
*   **Response (201 Created):**
    ```json
    { "uploadId": "up_789", "detectedFormat": "parquet", "status": "processing" }
    ```

### 4.5 `GET /data/export/status`
Checks the progress of a background export job.
*   **Request:** `GET /api/v1/data/export/status?jobId=exp_44`
*   **Response (200 OK):**
    ```json
    { "progress": 65, "estimatedCompletion": "2026-05-10T14:00:00Z" }
    ```

### 4.6 `POST /sync/push`
Pushes offline changes from the local SQLite store to the server.
*   **Request Body:**
    ```json
    {
      "clientId": "client_xyz",
      "changes": [
        { "table": "rules", "action": "update", "data": { "id": 1, "name": "New Rule" }, "timestamp": 1712345678 }
      ]
    }
    ```
*   **Response (200 OK):** `{ "synced": true, "conflicts": 0 }`

### 4.7 `GET /system/health`
Returns the health status of the microservices cluster.
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "services": { "notifications": "up", "webhooks": "up", "import": "degraded" }
    }
    ```

### 4.8 `DELETE /auth/session/terminate`
Invalidates the current JWT session.
*   **Request:** `DELETE /api/v1/auth/session/terminate`
*   **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The system utilizes a central PostgreSQL database for authoritative state and distributed SQLite instances for edge caching.

### 5.1 Tables and Relationships

| Table Name | Key Fields | Primary Key | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | `id`, `name`, `plan_level`, `created_at` | `id` (UUID) | 1:N with `users` | Top-level tenant |
| `users` | `id`, `org_id`, `email`, `full_name`, `role_id` | `id` (UUID) | N:1 with `organizations` | User identity |
| `roles` | `id`, `role_name`, `permissions_mask` | `id` (INT) | 1:N with `users` | RBAC definitions |
| `notifications` | `id`, `user_id`, `channel`, `content`, `sent_at` | `id` (UUID) | N:1 with `users` | History of alerts |
| `user_prefs` | `user_id`, `channel`, `enabled`, `quiet_hours` | `(user_id, channel)` | 1:1 with `users` | Notification settings |
| `webhooks` | `id`, `org_id`, `target_url`, `secret_token` | `id` (UUID) | N:1 with `organizations` | Outbound targets |
| `webhook_logs` | `id`, `webhook_id`, `payload`, `response_code` | `id` (BIGINT) | N:1 with `webhooks` | Audit trail of hooks |
| `imports` | `id`, `org_id`, `filename`, `status`, `row_count` | `id` (UUID) | N:1 with `organizations` | File import tracking |
| `sync_logs` | `id`, `user_id`, `client_id`, `last_sync_at` | `id` (UUID) | N:1 with `users` | Offline sync audit |
| `sso_configs` | `id`, `org_id`, `provider_type`, `metadata_url` | `id` (UUID) | N:1 with `organizations` | SAML/OIDC settings |

### 5.2 Key Indices and Performance
To support the high-performance requirements of the cybersecurity market, the following indices are implemented:
*   `idx_notifications_user_sent`: B-Tree index on `(user_id, sent_at)` for fast retrieval of recent alerts.
*   `idx_webhook_org`: Hash index on `org_id` for rapid lookup of organization-wide hooks.
*   `idx_sync_client`: Unique index on `client_id` to ensure atomic sync session management.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Jetstream maintains three distinct environments to ensure stability while permitting rapid iteration.

#### 6.1.1 Development (Dev)
*   **Purpose:** Sandbox for engineers to test new features.
*   **Configuration:** Local Docker Compose stacks mirroring the production Kafka/Postgres setup.
*   **Deployment:** Manual push to `dev` branch.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Pre-production validation and QA.
*   **Configuration:** A mirrored instance of the production environment on Cloudflare Workers, using a subset of anonymized production data.
*   **Deployment:** Automatic deployment upon merge into the `staging` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live enterprise environment.
*   **Configuration:** Full global distribution across Cloudflare’s edge network with Kafka clusters deployed in three geographic regions (US-East, EU-West, APAC-South) for redundancy.
*   **Deployment:** **Continuous Deployment (CD).** Every merged PR into the `main` branch is automatically deployed.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1.  **Lint/Test:** `cargo fmt`, `cargo clippy`, and `npm test` are run on every commit.
2.  **Build:** Rust binaries are compiled to WASM for Cloudflare Workers.
3.  **Smoke Test:** A suite of 50 critical end-to-end tests is run against a temporary ephemeral environment.
4.  **Deploy:** `wrangler publish` pushes the code to the edge.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Backend:** 100% coverage required for the `AuthService` and `NotificationDispatcher`. Rust's built-in `#[test]` framework is used.
*   **Frontend:** Jest and React Testing Library are used to verify component behavior in isolation.

### 7.2 Integration Testing
*   **Kafka Flows:** Integration tests verify that a message published to the `threat_detected` topic correctly triggers a notification record in PostgreSQL.
*   **API Contracts:** Postman collections are used to validate that the API responses match the documented schema.

### 7.3 End-to-End (E2E) Testing
*   **Playwright:** A suite of E2E tests simulates a user journey from SSO Login $\rightarrow$ Data Import $\rightarrow$ Webhook Configuration.
*   **Frequency:** E2E tests run on every PR merge. A failure in E2E automatically triggers a rollback of the production deployment.

### 7.4 Security Testing
*   **Quarterly Penetration Testing:** A third-party firm is contracted every three months to attempt to breach the system, specifically focusing on the SSO and Webhook endpoints.
*   **Static Analysis:** `cargo-audit` is run daily to detect vulnerabilities in Rust dependencies.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Integration partner's API is undocumented and buggy | High | High | **Parallel-Path:** Prototype an alternative integration approach simultaneously to avoid total project stall. | Arun Santos |
| R-02 | Key Architect leaving the company in 3 months | Medium | Critical | **Knowledge Transfer:** Assign a dedicated owner to shadow the architect and document all structural decisions. | Xiomara Kim |
| R-03 | Performance degradation due to raw SQL usage | High | Medium | **Refactor Sprint:** Schedule a "Debt Month" after Milestone 2 to migrate raw SQL back to the ORM. | Wanda Kim |
| R-04 | Cloudflare Worker memory limits exceeded by Rust WASM | Medium | High | **Optimization:** Implement a strict memory-budgeting policy and use `wee_alloc` for smaller binaries. | Wanda Kim |
| R-05 | User adoption failure (NPS < 40) | Low | High | **User Research:** Lior Stein to conduct weekly feedback sessions with the 10 pilot users. | Lior Stein |

**Impact Matrix:**
*   *Critical:* Project failure or severe data breach.
*   *High:* Significant delay in milestone or major feature loss.
*   *Medium:* Minor delay or performance degradation.
*   *Low:* Negligible impact on timeline.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown

#### Phase 1: Foundation & Core Services (Current - May 2026)
*   **Focus:** Complete the notification, webhook, and SSO systems.
*   **Key Dependency:** Stable Kafka cluster deployment.
*   **Target:** Finalize the "Critical" launch blockers.

#### Phase 2: Beta & Validation (May 2026 - July 2026)
*   **Milestone 1: External beta with 10 pilot users (Target: 2026-05-15).**
*   **Focus:** Gathering NPS data and refining the UX based on Lior Stein's research.
*   **Key Dependency:** Resolution of the Data Import blocker.

#### Phase 3: Executive Sign-off (July 2026 - September 2026)
*   **Milestone 2: Stakeholder demo and sign-off (Target: 2026-07-15).**
*   **Focus:** Polishing the UI and ensuring the cost-per-transaction reduction is measurable.
*   **Key Dependency:** Completion of the Offline-First mode.

#### Phase 4: Final Architecture Hardening (September 2026 - December 2026)
*   **Milestone 3: Architecture review complete (Target: 2026-09-15).**
*   **Focus:** Addressing technical debt (raw SQL migration) and final penetration testing.

### 9.2 Gantt-Style Dependency Map
`[Core Svc] -> [Data Import Fix] -> [External Beta] -> [Offline Sync] -> [Stakeholder Demo] -> [Arch Review]`

---

## 10. MEETING NOTES (SLACK-STYLE)

As per team agreement, no formal minutes are kept. The following are synthesized from key decision threads in the `#jetstream-dev` Slack channel.

### Meeting 1: The "Raw SQL" Debate
**Date:** 2024-11-12
**Participants:** Wanda Kim, Xiomara Kim, Key Architect
**Discussion:**
*   **Wanda:** "The ORM is killing the performance on the `notifications` table. We're seeing 200ms latency for simple fetches."
*   **Architect:** "I've bypassed the ORM with raw SQL for the top 30% of queries. It brings it down to 15ms."
*   **Xiomara:** "Is this dangerous for migrations?"
*   **Architect:** "Yes, if we change the schema, the raw SQL will break. But we can't afford the latency."
*   **Decision:** Allow raw SQL for performance-critical paths. Wanda to track these queries in a `debt_log.md` for future refactoring.

### Meeting 2: The Partner API Crisis
**Date:** 2025-01-15
**Participants:** Arun Santos, Xiomara Kim
**Discussion:**
*   **Arun:** "The partner API is a disaster. The documentation says it's a POST, but it only responds to GET. Half the fields are returning nulls."
*   **Xiomara:** "We can't let this block the Data Import feature. It's a launch blocker."
*   **Arun:** "I suggest we don't wait for them to fix it. I can build a shim that scrapes their frontend or try a different provider."
*   **Decision:** Parallel-path strategy adopted. Arun will continue trying to fix the API while simultaneously prototyping an alternative approach.

### Meeting 3: SSO Scope Creep
**Date:** 2025-03-02
**Participants:** Lior Stein, Xiomara Kim, Key Architect
**Discussion:**
*   **Lior:** "Pilot users are asking for Social Login (Google/Facebook). They find SAML too corporate."
*   **Xiomara:** "We are an enterprise tool. Social login isn't in the spec."
*   **Architect:** "Adding OIDC for Google is easy, but Facebook is a security nightmare for this industry."
*   **Decision:** Implement OIDC for Google Workspace only. Reject Facebook/Twitter logins to maintain security posture.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+

### 11.1 Personnel ($3,200,000)
| Role | Count | Annual Rate (Avg) | Duration | Total |
| :--- | :--- | :--- | :--- | :--- |
| VP Product (Project Lead) | 1 | $250,000 | 2 Years | $500,000 |
| Data Engineer | 1 | $180,000 | 2 Years | $360,000 |
| UX Researcher | 1 | $150,000 | 2 Years | $300,000 |
| Support Engineer | 1 | $120,000 | 2 Years | $240,000 |
| Backend Engineers (Contract) | 3 | $200,000 | 2 Years | $1,200,000 |
| Frontend Engineers (Contract) | 1 | $180,000 | 2 Years | $360,000 |
| **Total Personnel** | **8** | - | - | **$2,960,000** |

### 11.2 Infrastructure ($800,000)
*   **Cloudflare Enterprise Plan:** $200,000 (includes Workers, D1, and R2 storage).
*   **Managed Kafka (Confluent):** $400,000 (high-throughput clusters across 3 regions).
*   **PostgreSQL Managed Service:** $200,000 (high-availability clusters).

### 11.3 Tooling and Security ($400,000)
*   **Penetration Testing (Quarterly):** $150,000 ($37.5k per engagement).
*   **SaaS Licenses (JIRA, GitHub Enterprise, Slack):** $100,000.
*   **API Provider Costs (Twilio, SendGrid):** $150,000.

### 11.4 Contingency Fund ($600,000)
*   Reserved for emergency hiring or unforeseen infrastructure scaling needs during the beta phase.

---

## 12. APPENDICES

### Appendix A: Kafka Topic Schema
To ensure consistency across microservices, the following Kafka topic naming conventions and schemas are enforced:

1.  **Topic:** `notification.requested`
    *   *Key:* `user_id`
    *   *Value:* `{ "userId": UUID, "priority": Enum, "message": String, "timestamp": Long }`
2.  **Topic:** `webhook.triggered`
    *   *Key:* `org_id`
    *   *Value:* `{ "webhookId": UUID, "payload": JSON, "attemptCount": Int }`
3.  **Topic:** `data.import.started`
    *   *Key:* `import_id`
    *   *Value:* `{ "importId": UUID, "filePath": String, "format": String }`

### Appendix B: Rust Memory Management Policy
Due to the deployment on Cloudflare Workers (WASM), the team must adhere to the following constraints to prevent `Out of Memory` (OOM) crashes:
*   **Zero-Copy Parsing:** Use `serde` and `std::borrow::Cow` where possible to avoid unnecessary allocations during JSON processing.
*   **Stream Processing:** Never load a full file into memory during data import. Use `AsyncRead` and process in 64KB chunks.
*   **Heap Optimization:** The `wee_alloc` allocator is enabled for all production builds to reduce the binary size and memory footprint.
*   **Crate Restrictions:** Avoid using heavy crates that rely on `std::os` or large static buffers.