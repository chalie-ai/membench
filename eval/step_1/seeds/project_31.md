# PROJECT SPECIFICATION: PROJECT WAYFINDER
**Document Version:** 1.0.4  
**Status:** Draft/Review  
**Date:** October 26, 2023  
**Owner:** Celine Liu, VP of Product  
**Classification:** CONFIDENTIAL – Oakmount Group  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Wayfinder is a strategic architectural migration and feature expansion initiative for Oakmount Group’s internal productivity tool. Originally conceived as a rapid-prototype hackathon project, the application has seen unexpected organic growth, now serving 500 daily active users (DAU) across the organization. As the tool has evolved into a critical piece of the cybersecurity operational workflow, the original "modular monolith" architecture has become a bottleneck for scalability, deployment velocity, and security compliance.

The primary objective of Project Wayfinder is to migrate the existing codebase into a distributed microservices architecture utilizing Go, gRPC, and Kubernetes on Google Cloud Platform (GCP), fronted by a robust API Gateway. This transition will decouple core business domains, allowing independent scaling and faster iteration cycles.

### 1.2 Business Justification
The current monolith is unable to support the performance requirements of our growing user base. Latency is increasing, and the lack of structured logging makes production debugging a manual, time-intensive process. Furthermore, as a cybersecurity firm, Oakmount Group is subject to stringent regulatory requirements. To transition this tool from an internal utility to a potentially commercializable product, it must achieve full HIPAA compliance, including encrypted data at rest and in transit, and a tamper-evident audit trail.

Failure to migrate will result in increased system downtime and the inability to pass the mandatory annual security audits. By modularizing the system, we reduce the "blast radius" of failures and enable a rolling deployment strategy via GitLab CI, ensuring zero-downtime updates.

### 1.3 ROI Projection and Success Criteria
The financial justification for Project Wayfinder is based on two primary drivers: operational efficiency and revenue generation. By automating infrastructure and improving stability, we project a 20% reduction in engineering hours spent on maintenance. 

**Primary Success Metrics:**
1. **Compliance:** Pass the external HIPAA and SOC2 audit on the first attempt.
2. **Revenue:** Generate $500,000 in new attributed revenue within 12 months post-launch. This revenue will be derived from offering the tool as a value-add service to Oakmount’s premium cybersecurity clients.
3. **Performance:** Meet specific latency benchmarks (sub-100ms response times for 95% of API calls) by the 2025-03-15 deadline.

### 1.4 Funding Model
Budgeting for Project Wayfinder is variable and milestone-based. Funding is released in tranches upon the successful completion of specified deliverables. This ensures fiscal accountability and allows the steering committee to adjust funding based on the project's trajectory and the company's quarterly financial health.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Wayfinder is transitioning from a **Modular Monolith** to a **Microservices Architecture**. We are employing the "Strangler Fig" pattern, where new functionality is built as microservices and existing monolithic functions are incrementally migrated.

### 2.2 The Tech Stack
*   **Language:** Go (Golang) 1.21+ for all backend services due to its concurrency primitives and performance.
*   **Communication:** gRPC for internal service-to-service communication (Protocol Buffers) to ensure type safety and low latency. REST/JSON is used exclusively at the API Gateway level for client consumption.
*   **Database:** CockroachDB (v23.1) for its distributed SQL capabilities, ensuring high availability and strong consistency across GCP regions.
*   **Orchestration:** Kubernetes (GKE) for container orchestration.
*   **CI/CD:** GitLab CI with automated rolling deployments.
*   **Security:** TLS 1.3 for all data in transit; AES-256 for data at rest.

### 2.3 API Gateway Design
The API Gateway acts as the single entry point for all clients. It handles:
*   **Authentication:** Validating JWTs and interfacing with the Identity Service.
*   **Rate Limiting:** Preventing API abuse using a token-bucket algorithm.
*   **Request Routing:** Mapping external REST paths to internal gRPC services.
*   **Protocol Translation:** Converting HTTP/1.1 JSON requests into gRPC calls.

### 2.4 ASCII Architecture Diagram
```text
[ Client App / Browser ] 
          |
          v (HTTPS/JSON)
+-----------------------+
|      API GATEWAY       | <--- [ Auth Service ]
| (Routing, Rate Limit)  |
+-----------+-----------+
            |
            | (gRPC / Protobuf)
            v
    +-------+-----------------------+-------+
    |       |                       |       |
    v       v                       v       v
[ Auth ] [ Audit ] [ Collaborative ] [ Import ] [ Webhook ]
Service   Service      Service       Service    Service
    |       |               |           |          |
    +-------+---------------+-----------+----------+
                            |
                            v
                  +-------------------+
                  |   CockroachDB    |
                  | (Distributed SQL)|
                  +-------------------+
                            |
                            v
                  [ GCP Cloud Storage ]
                    (Encrypted Backups)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
The authentication system must provide a secure, scalable method for identifying users and authorizing their actions across the Wayfinder ecosystem. Given the cybersecurity context, we require a Zero Trust approach.

**Technical Requirements:**
1.  **Identity Provider:** Integration with Oakmount’s corporate OIDC (OpenID Connect) provider.
2.  **JWT Management:** The Auth Service will issue short-lived JSON Web Tokens (JWT) containing claims for user ID and assigned roles.
3.  **RBAC Model:** Roles are defined as `Admin`, `Editor`, `Viewer`, and `Auditor`. Permissions are mapped to specific actions (e.g., `audit.read`, `data.export`).
4.  **Session Management:** Implementation of a refresh token rotation strategy to prevent session hijacking.
5.  **Encryption:** All passwords (where stored locally) must be hashed using Argon2id.

**Workflow:**
When a user logs in, the API Gateway forwards the request to the Auth Service. After successful OIDC validation, the Auth Service generates a JWT signed with a rotating private key. This token is passed in the `Authorization: Bearer` header for all subsequent requests. The Gateway validates the signature and checks the role claims against the requested endpoint's required permission level.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
To meet HIPAA and cybersecurity compliance, every write-action and sensitive read-action within the system must be logged in a way that cannot be altered or deleted by any user, including administrators.

**Technical Requirements:**
1.  **Immutable Logs:** Logs are written to a write-once-read-many (WORM) storage layer.
2.  **Cryptographic Chaining:** Each log entry contains a hash of the previous entry (blockchain-style chaining). This ensures that if a record is deleted or modified, the hash chain is broken.
3.  **Detailed Metadata:** Every entry must capture: `timestamp`, `user_id`, `action_type`, `resource_id`, `request_ip`, and `payload_diff`.
4.  **Asynchronous Logging:** To prevent performance degradation, the Audit Service will consume events from a Kafka or NATS message queue rather than blocking the main request thread.

**Compliance Note:**
The audit trail must be stored in a separate CockroachDB cluster or a dedicated secure bucket on GCP with "Object Lock" enabled to prevent deletion for a period of 7 years.

### 3.3 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Users need the ability to migrate data into Wayfinder from various cybersecurity tools and export data for reporting. The system must automatically detect the file format and map it to the internal schema.

**Technical Requirements:**
1.  **Format Support:** Support for JSON, CSV, XML, and YAML.
2.  **Auto-Detection Logic:** The Import Service will analyze the first 1KB of the uploaded file (magic bytes and structural analysis) to determine the format.
3.  **Schema Mapping:** A configurable mapping engine that allows admins to define how external fields map to Wayfinder fields.
4.  **Validation Pipeline:** All imports must pass through a validation stage where data is checked for type correctness and HIPAA compliance (e.g., scanning for unencrypted PII).
5.  **Chunked Uploads:** For files larger than 50MB, the system must support multipart uploads to prevent memory exhaustion in the Kubernetes pods.

**Export Process:**
Exports will be processed as background jobs. The user requests an export; the system generates a signed GCP Cloud Storage URL and notifies the user via email/notification when the file is ready for download.

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Review

**Description:**
Wayfinder allows multiple users to work on a single productivity document simultaneously. To avoid "last-write-wins" data loss, a robust conflict resolution mechanism is required.

**Technical Requirements:**
1.  **Operational Transformation (OT) or CRDTs:** The team will implement Conflict-free Replicated Data Types (CRDTs) specifically for text and state synchronization to ensure eventual consistency across all clients.
2.  **WebSocket Integration:** Use of WebSockets (via the API Gateway) for low-latency, bi-directional communication.
3.  **Presence Tracking:** A "Presence Service" to show which users are currently active in a document and their cursor positions.
4.  **Versioning:** Automatic snapshots of documents every 5 minutes to allow users to revert to a previous state.

**Consistency Model:**
The system uses a "strong eventual consistency" model. Changes are broadcasted via the Collaborative Service and persisted to CockroachDB. If two users edit the same character, the CRDT logic resolves the order based on a deterministic timestamp.

### 3.5 Webhook Integration Framework for Third-Party Tools
**Priority:** Medium | **Status:** In Progress

**Description:**
Wayfinder must be able to trigger actions in external tools (e.g., Slack, Jira, PagerDuty) and receive signals from them to update internal states.

**Technical Requirements:**
1.  **Webhook Registry:** A UI and API for users to register external URLs and the specific events that should trigger a POST request.
2.  **Retry Mechanism:** Implementation of an exponential backoff strategy for failed webhook deliveries.
3.  **Security (HMAC):** All outgoing webhooks must be signed with an HMAC-SHA256 signature so the receiver can verify the request originated from Wayfinder.
4.  **Payload Templates:** Ability for users to define the JSON structure of the outgoing payload using a simple templating language (e.g., Handlebars).

**Event Pipeline:**
When a relevant event occurs (e.g., `task.completed`), the event is published to the internal message bus. The Webhook Service subscribes to these events and dispatches the payloads to the registered endpoints.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `Authorization: Bearer <JWT>` header.

### 4.1 Authentication
**`POST /auth/login`**
*   **Description:** Exchanges OIDC credentials for a Wayfinder JWT.
*   **Request Body:** `{"client_id": "string", "client_secret": "string"}`
*   **Response (200):** `{"token": "eyJ...", "expires_at": "2023-10-26T12:00:00Z"}`

### 4.2 Audit Logs
**`GET /audit/logs`**
*   **Description:** Retrieves a paginated list of audit events.
*   **Query Params:** `page=1`, `limit=50`, `user_id=123`
*   **Response (200):** `{"data": [{"id": "log_1", "action": "update_policy", "timestamp": "..."}], "next_page": 2}`

**`GET /audit/verify`**
*   **Description:** Validates the integrity of the audit chain for a specific time range.
*   **Query Params:** `start=timestamp`, `end=timestamp`
*   **Response (200):** `{"status": "verified", "chain_id": "abc-123"}`

### 4.3 Data Management
**`POST /data/import`**
*   **Description:** Uploads a file for auto-detection and import.
*   **Request Body:** `multipart/form-data` (file)
*   **Response (202):** `{"job_id": "job_999", "status": "processing"}`

**`GET /data/export/{resource_id}`**
*   **Description:** Requests an export of a specific resource.
*   **Response (200):** `{"download_url": "https://storage.googleapis.com/...", "expires_in": 3600}`

### 4.4 Collaboration
**`POST /collab/join/{doc_id}`**
*   **Description:** Joins a collaborative session for a document.
*   **Response (200):** `{"websocket_url": "wss://wayfinder.oakmount.com/socket", "session_id": "sess_456"}`

### 4.5 Webhooks
**`POST /webhooks/register`**
*   **Description:** Configures a new webhook.
*   **Request Body:** `{"target_url": "https://hooks.slack.com/...", "event": "audit.alert"}`
*   **Response (201):** `{"webhook_id": "wh_789"}`

**`DELETE /webhooks/{webhook_id}`**
*   **Description:** Removes a registered webhook.
*   **Response (204):** No content.

---

## 5. DATABASE SCHEMA

The system utilizes CockroachDB. All tables use `UUID` as the primary key to avoid hotspots in the distributed cluster.

### 5.1 Table Definitions

1.  **`users`**
    *   `id` (UUID, PK): Unique identifier.
    *   `email` (String, Unique): User's corporate email.
    *   `role_id` (UUID, FK): Links to roles table.
    *   `created_at` (Timestamp): Account creation date.
    *   `last_login` (Timestamp): For auditing purposes.

2.  **`roles`**
    *   `id` (UUID, PK): Unique identifier.
    *   `role_name` (String): (e.g., "Admin", "Viewer").
    *   `permissions` (JSONB): List of granted permissions.

3.  **`audit_logs`**
    *   `id` (UUID, PK): Unique identifier.
    *   `user_id` (UUID, FK): Who performed the action.
    *   `action` (String): The operation (e.g., "USER_LOGIN").
    *   `payload` (JSONB): The change delta.
    *   `prev_hash` (String): Hash of the previous log entry.
    *   `current_hash` (String): Hash of the current entry.
    *   `timestamp` (Timestamp): Event time.