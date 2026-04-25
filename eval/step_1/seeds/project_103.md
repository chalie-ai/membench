# PROJECT SPECIFICATION: TRELLIS
**Document Version:** 1.0.4  
**Date:** October 24, 2024  
**Project Status:** Active / High Urgency  
**Classification:** Confidential / HIPAA Restricted  
**Owner:** Nightjar Systems  

---

## 1. EXECUTIVE SUMMARY

**Project Trellis** is a mission-critical embedded systems firmware and accompanying management ecosystem developed by Nightjar Systems. The project is situated within the education sector, specifically targeting the management and monitoring of specialized hardware deployed in learning environments. 

### Business Justification
The primary driver for Project Trellis is a strict regulatory compliance mandate. New educational data privacy and safety laws (ED-REG 2025) require that all embedded hardware interacting with student data must implement specific audit trails, encryption standards, and access controls. Failure to achieve compliance by the legal deadline in six months will result in the immediate cessation of the company's ability to sell hardware in three major domestic markets, potentially leading to a loss of $2.4M in annual recurring revenue (ARR). 

The urgency of this project is underscored by the "hard legal deadline" of April 15, 2025. While the project is categorized as firmware, the scope extends to the orchestration layer—the software that manages the firmware updates, configuration, and telemetry of thousands of distributed edge devices.

### ROI Projection
The Return on Investment (ROI) for Project Trellis is calculated not through direct new revenue, but through risk mitigation and market retention. 
1. **Revenue Protection:** By meeting the compliance deadline, Nightjar Systems protects existing contracts worth $4.2M.
2. **Operational Efficiency:** The transition to a Rust-based backend and CQRS architecture is projected to reduce system crashes by 40% and decrease the time required for regulatory audits from three weeks to two days.
3. **Market Advantage:** Being the first in the education sector to provide a HIPAA-compliant, tamper-evident audit trail for embedded hardware provides a competitive moat, allowing the company to bid on higher-security government education contracts.

The total project budget of $400,000 is lean, necessitating a highly focused development cycle. The budget is primarily allocated to the distributed team of 15 experts across five countries, ensuring 24-hour coverage across time zones (UTC-5 to UTC+9).

---

## 2. TECHNICAL ARCHITECTURE

### Architectural Philosophy
Trellis utilizes a hybrid edge-cloud architecture. The firmware resides on the embedded devices, communicating via a secure gateway to a centralized management plane.

**The Stack:**
- **Backend:** Rust (Tokio, Axum) for high-performance, memory-safe concurrency.
- **Frontend:** React (TypeScript, Tailwind CSS) for the administrative dashboard.
- **Edge Storage:** SQLite (WAL mode) for local data persistence and buffering.
- **Cloud Orchestration:** Cloudflare Workers for global low-latency API routing and edge logic.
- **Data Pattern:** Command Query Responsibility Segregation (CQRS) with Event Sourcing. This is mandatory for the audit-critical domains to ensure that every state change is captured as an immutable event.

### System Component Diagram (ASCII Representation)

```text
[ EMBEDDED DEVICE (Edge) ] <--- TLS 1.3 ---> [ CLOUDFLARE WORKERS ]
       |                                            |
       |-- SQLite (Local Store)                     |-- API Gateway / Rate Limiter
       |-- Rust Firmware (Core)                     |-- Auth Service (OIDC/SAML)
       |-- Hardware Sensors                        |
                                                    V
                                            [ BACKEND SERVICES (Rust) ]
                                                    |
                ____________________________________|____________________________________
               |                                    |                                    |
      [ COMMAND SIDE (Write) ]             [ EVENT STORE (Immutable) ]           [ QUERY SIDE (Read) ]
               |                                    |                                    |
       (Validate Command)  ----->  (Append Event to Log)  ----->  (Update Read Model/View)
               |                                    |                                    |
               |____________________________________|____________________________________|
                                                    |
                                            [ HIPAA COMPLIANT STORAGE ]
                                            (AES-256 Encrypted At Rest)
```

### Data Flow and Security
All data moving between the embedded hardware and the Cloudflare Workers is encrypted using TLS 1.3 with mutual authentication (mTLS) utilizing device-specific certificates. The CQRS implementation ensures that "Commands" (e.g., `ChangeDeviceConfig`) are separated from "Queries" (e.g., `GetDeviceStatus`). The Event Store acts as the single source of truth, ensuring a complete, tamper-evident history of all device interactions.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** Complete | **Version:** v1.1.0

**Description:**
The RBAC system governs how users (administrators, teachers, technicians) interact with the Trellis management plane. Due to HIPAA compliance, access is granted based on the "Principle of Least Privilege."

**Functional Requirements:**
- **Identity Management:** Users are stored with hashed passwords using Argon2id.
- **Role Definition:**
    - *SuperAdmin:* Full system access, user management, and global configuration.
    - *Auditor:* Read-only access to audit trails and system logs.
    - *Operator:* Ability to push firmware updates and change device settings.
    - *Viewer:* Read-only access to device telemetry.
- **Session Management:** JWTs (JSON Web Tokens) with a 15-minute expiration and sliding window refresh tokens stored in a secure HTTP-only cookie.
- **Access Control Lists (ACL):** Granular permissions mapped to specific API endpoints.

**Implementation Details:**
The RBAC system is integrated into the Rust backend via a middleware layer that intercepts every request, extracts the user role from the JWT, and verifies it against a permission matrix before allowing the request to reach the handler.

---

### 3.2 SSO Integration with SAML and OIDC Providers
**Priority:** Low | **Status:** In Design | **Version:** v0.9.0-beta

**Description:**
To reduce password fatigue and improve security for large educational institutions, Trellis must support Single Sign-On (SSO) via SAML 2.0 and OpenID Connect (OIDC).

**Functional Requirements:**
- **Provider Support:** Integration with Azure AD, Okta, and Google Workspace.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user account in the Trellis database upon their first successful SSO login, assigning a default "Viewer" role.
- **Attribute Mapping:** Map SAML assertions (e.g., `memberOf` groups) to Trellis RBAC roles.
- **Metadata Exchange:** Support for XML metadata exchange for SAML provider configuration.

**Implementation Strategy:**
The team will implement an abstraction layer in the backend that treats the internal auth system and external SSO providers as "Identity Sources." The flow will redirect the user to the provider's challenge page and handle the callback via a secure endpoint `/auth/callback`.

---

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Complete | **Version:** v1.0.2

**Description:**
To prevent Denial of Service (DoS) attacks and ensure fair resource allocation across thousands of embedded devices, a robust rate-limiting mechanism is implemented at the Cloudflare Worker level.

**Functional Requirements:**
- **Token Bucket Algorithm:** Implementation of a token bucket to allow for short bursts of traffic while maintaining a steady long-term rate.
- **Tiered Limits:**
    - *Device API:* 60 requests per minute (RPM) per device ID.
    - *Admin API:* 200 RPM per user account.
- **Analytics Pipeline:** Every request is logged with metadata (latency, endpoint, status code, user agent) and piped to a Prometheus/Grafana stack for real-time monitoring.
- **Headers:** Responses must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Detail:**
Rate limiting is handled using Cloudflare KV (Key-Value) store to track request counts globally across the edge, ensuring that a device cannot bypass limits by hitting different regional endpoints.

---

### 3.4 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Progress | **Version:** v0.8.5-alpha

**Description:**
The core of the regulatory compliance requirement. This feature ensures that every administrative action—and every critical device state change—is recorded in a way that cannot be altered or deleted without detection.

**Functional Requirements:**
- **Event Sourcing:** Instead of updating a "Current State" table, the system appends events to an immutable log.
- **Cryptographic Chaining:** Each log entry contains a SHA-256 hash of the previous entry, creating a blockchain-like chain.
- **Write-Once-Read-Many (WORM):** Integration with S3 Object Lock or similar immutable storage to prevent deletion.
- **Audit Search:** An optimized query interface for auditors to filter by timestamp, user ID, or device ID.

**Implementation Detail:**
The Rust backend utilizes an event-store pattern. When a `UpdateFirmware` command is issued, a `FirmwareUpdateInitiated` event is written to the SQLite edge store and then synced to the cloud Event Store. Any attempt to modify a historical record would break the hash chain, triggering a critical security alert.

---

### 3.5 Webhook Integration Framework for Third-Party Tools
**Priority:** Medium | **Status:** In Design | **Version:** v0.7.0-dev

**Description:**
Trellis must allow external educational management software to react to events occurring on the embedded devices (e.g., "Device Offline," "Compliance Violation Detected").

**Functional Requirements:**
- **Webhook Registration:** An API for users to register target URLs and select specific events to subscribe to.
- **Retry Logic:** Exponential backoff retry mechanism (up to 5 attempts) if the target server returns a non-200 status code.
- **Payload Security:** Inclusion of an `X-Trellis-Signature` header (HMAC-SHA256) to allow the receiver to verify the payload's authenticity.
- **Delivery Guarantees:** At-least-once delivery semantics.

**Design Specification:**
The framework will use a message queue (RabbitMQ or similar) to decouple the event trigger from the webhook delivery, ensuring that slow third-party endpoints do not block the main system execution.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer <JWT>` token in the Authorization header.

### 4.1 `POST /auth/login`
**Description:** Authenticates a user and returns a session token.
- **Request Body:**
  ```json
  { "email": "v.kim@nightjar.com", "password": "secure_password_123" }
  ```
- **Response (200 OK):**
  ```json
  { "token": "eyJhbGci...", "expires_at": "2024-10-24T12:00:00Z" }
  ```

### 4.2 `GET /devices`
**Description:** Retrieves a list of all registered embedded devices.
- **Query Params:** `status` (online/offline), `limit`, `offset`.
- **Response (200 OK):**
  ```json
  [
    { "id": "dev_001", "status": "online", "firmware_version": "2.1.0", "last_seen": "2024-10-24T10:00:00Z" }
  ]
  ```

### 4.3 `POST /devices/{id}/update`
**Description:** Triggers a firmware update for a specific device.
- **Request Body:**
  ```json
  { "version": "2.2.0", "force": false, "schedule_time": "2024-10-25T02:00:00Z" }
  ```
- **Response (202 Accepted):**
  ```json
  { "job_id": "job_9988", "status": "queued" }
  ```

### 4.4 `GET /audit/logs`
**Description:** Fetches tamper-evident logs for compliance review.
- **Query Params:** `start_date`, `end_date`, `userId`.
- **Response (200 OK):**
  ```json
  [
    { "eventId": "evt_123", "timestamp": "...", "action": "CONFIG_CHANGE", "user": "admin_1", "hash": "a1b2c3d4..." }
  ]
  ```

### 4.5 `PUT /devices/{id}/config`
**Description:** Updates the configuration parameters of a device.
- **Request Body:**
  ```json
  { "polling_interval": 30, "log_level": "debug" }
  ```
- **Response (200 OK):**
  ```json
  { "status": "success", "applied_at": "2024-10-24T11:00:00Z" }
  ```

### 4.6 `GET /analytics/usage`
**Description:** Returns API usage statistics for the current organization.
- **Response (200 OK):**
  ```json
  { "total_requests": 150000, "error_rate": "0.02%", "p95_latency": "120ms" }
  ```

### 4.7 `POST /webhooks/subscribe`
**Description:** Registers a new webhook endpoint.
- **Request Body:**
  ```json
  { "url": "https://partner.com/webhook", "events": ["device.offline", "device.error"] }
  ```
- **Response (201 Created):**
  ```json
  { "webhook_id": "wh_445", "secret": "whsec_..." }
  ```

### 4.8 `DELETE /users/{id}`
**Description:** Soft-deletes a user from the system (required for HIPAA "Right to be Forgotten").
- **Response (204 No Content):**
  *(Empty body)*

---

## 5. DATABASE SCHEMA

The system uses a hybrid approach: SQLite at the edge for local caching and a PostgreSQL-compatible cloud database for the central management plane.

### Table Definitions

1. **`users`**
   - `user_id` (UUID, PK)
   - `email` (VARCHAR, Unique)
   - `password_hash` (TEXT)
   - `role_id` (FK $\rightarrow$ roles)
   - `created_at` (TIMESTAMP)
   - `last_login` (TIMESTAMP)

2. **`roles`**
   - `role_id` (INT, PK)
   - `role_name` (VARCHAR) — (e.g., 'SuperAdmin', 'Auditor')
   - `permissions` (JSONB) — List of granular capabilities.

3. **`devices`**
   - `device_id` (UUID, PK)
   - `serial_number` (VARCHAR, Unique)
   - `firmware_version` (VARCHAR)
   - `status` (ENUM: online, offline, maintenance)
   - `org_id` (FK $\rightarrow$ organizations)
   - `last_heartbeat` (TIMESTAMP)

4. **`organizations`**
   - `org_id` (UUID, PK)
   - `name` (VARCHAR)
   - `billing_address` (TEXT)
   - `compliance_level` (INT)

5. **`event_store` (The Immutable Log)**
   - `event_id` (BIGINT, PK)
   - `device_id` (FK $\rightarrow$ devices, Nullable)
   - `user_id` (FK $\rightarrow$ users, Nullable)
   - `event_type` (VARCHAR)
   - `payload` (JSONB)
   - `created_at` (TIMESTAMP)
   - `previous_hash` (VARCHAR)
   - `current_hash` (VARCHAR)

6. **`device_configs`**
   - `config_id` (UUID, PK)
   - `device_id` (FK $\rightarrow$ devices)
   - `settings` (JSONB)
   - `version` (INT)
   - `updated_at` (TIMESTAMP)

7. **`firmware_releases`**
   - `release_id` (UUID, PK)
   - `version` (VARCHAR)
   - `binary_url` (TEXT)
   - `checksum` (VARCHAR)
   - `is_stable` (BOOLEAN)

8. **`sso_providers`**
   - `provider_id` (UUID, PK)
   - `provider_type` (ENUM: SAML, OIDC)
   - `entity_id` (VARCHAR)
   - `sso_url` (TEXT)
   - `certificate` (TEXT)

9. **`webhook_subscriptions`**
   - `webhook_id` (UUID, PK)
   - `target_url` (TEXT)
   - `secret_token` (VARCHAR)
   - `event_mask` (VARCHAR)
   - `is_active` (BOOLEAN)

10. **`api_usage_logs`**
    - `log_id` (BIGINT, PK)
    - `user_id` (FK $\rightarrow$ users)
    - `endpoint` (VARCHAR)
    - `response_time_ms` (INT)
    - `status_code` (INT)
    - `timestamp` (TIMESTAMP)

### Relationships
- `users` $\rightarrow$ `roles` (Many-to-One)
- `devices` $\rightarrow$ `organizations` (Many-to-One)
- `event_store` $\rightarrow$ `devices` and `users` (Many-to-One)
- `device_configs` $\rightarrow$ `devices` (One-to-One per version)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### Environment Strategy
The project utilizes three distinct environments to ensure stability and compliance.

1. **Development (DEV):**
   - **Purpose:** Feature iteration and unit testing.
   - **Infrastructure:** Local Docker containers and a shared Cloudflare Worker "Preview" namespace.
   - **Data:** Anonymized mock data only. No real student or user data permitted.

2. **Staging (STG):**
   - **Purpose:** Integration testing and UAT (User Acceptance Testing).
   - **Infrastructure:** Mirror of production, hosted on a separate Cloudflare account.
   - **Data:** Sanitized snapshots of production data.
   - **Deployment:** Automatic deployment from the `main` branch upon successful CI pass.

3. **Production (PROD):**
   - **Purpose:** Live regulatory-compliant environment.
   - **Infrastructure:** High-availability Cloudflare Workers, multi-region PostgreSQL clusters.
   - **Deployment:** **Manual deployments only.** Conducted by the sole DevOps engineer. 
   - **Approval:** Requires sign-off from Vera Kim (Engineering Manager).

### The "Bus Factor" Risk
Currently, deployment is managed by a single individual. This creates a "Bus Factor of 1." If this person is unavailable, the production pipeline stalls. To mitigate this, the project is documenting all deployment scripts in the `docs/devops` folder, and a contractor is being sought to provide redundancy.

---

## 7. TESTING STRATEGY

To meet the 99.9% uptime requirement and the strict compliance needs, a multi-layered testing approach is implemented.

### 7.1 Unit Testing
- **Focus:** Pure logic in Rust (e.g., hash chaining, RBAC permission checks).
- **Framework:** `cargo test`.
- **Requirement:** 80% code coverage on all "Command" handlers.

### 7.2 Integration Testing
- **Focus:** Interaction between Rust backend, SQLite edge, and the Event Store.
- **Framework:** Testcontainers for PostgreSQL and Redis.
- **Scenario:** "Command $\rightarrow$ Event $\rightarrow$ Read Model" flow must be verified to ensure CQRS consistency.

### 7.3 End-to-End (E2E) Testing
- **Focus:** User journeys in the React frontend and actual hardware communication.
- **Framework:** Playwright for frontend; custom hardware simulation scripts for firmware.
- **Key Path:** User logs in $\rightarrow$ selects device $\rightarrow$ pushes update $\rightarrow$ verifies update in audit log.

### 7.4 Compliance Testing
- **Penetration Testing:** Quarterly external audits to verify HIPAA compliance.
- **Tamper Test:** Attempting to manually edit the `event_store` table to verify that the hash chain validation fails and alerts the administrator.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding "small" features. | High | High | Hire a contractor to increase capacity; strictly enforce JIRA ticketing and change requests. |
| R-02 | Project sponsor rotates out of role, losing political cover. | Medium | High | De-scope non-critical "nice-to-have" features (e.g., SSO) if leadership support wavers. |
| R-03 | Single point of failure in DevOps (Bus Factor 1). | Medium | Critical | Transition to "Infrastructure as Code" (Terraform); hire secondary DevOps contractor. |
| R-04 | Firmware regressions causing device bricking. | Low | Critical | Implementation of "Dual-Bank" bootloading allowing fallback to the previous stable version. |
| R-05 | HIPAA breach due to improper log access. | Low | Critical | Mandatory mTLS and strict RBAC; automatic log rotation and encrypted archiving. |

### Probability/Impact Matrix
- **Critical:** Immediate project failure or legal penalty.
- **High:** Significant delay or budget overage.
- **Medium:** Manageable impact with schedule adjustment.
- **Low:** Negligible impact.

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project is on a compressed 6-month timeline leading up to the legal deadline of April 15, 2025.

### Phase 1: Core Compliance & Stabilization (Months 1-2)
- **Focus:** Completing the Audit Trail (Feature 4) and stabilizing RBAC.
- **Dependencies:** Completion of the Event Store schema.
- **Key Milestone:** Internal Alpha release.

### Phase 2: Integration & Edge Optimization (Months 3-4)
- **Focus:** Refining the Rust-to-SQLite pipeline and implementing API rate limiting.
- **Dependencies:** Hardware simulator stability.
- **Key Milestone:** Beta release to select partners.

### Phase 3: Final Validation & Launch (Months 5-6)
- **Focus:** E2E testing, HIPAA certification, and final manual deployment to PROD.
- **Dependencies:** Final sign-off from the Project Sponsor.
- **Key Milestone:** **Production Launch (2025-04-15).**

### Post-Launch Phase (Months 7-9)
- **Stability Window:** (Until 2025-06-15) Focus on uptime and bug fixes.
- **Performance Benchmarking:** (Until 2025-08-15) Optimizing query speeds for the audit trail.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning - Oct 12, 2024
- **Attendees:** Vera, Dayo, Camila, Yuki, DevOps.
- **Notes:**
    - Audit trail logic still buggy.
    - Yuki struggling with Rust ownership rules in the event store.
    - Camila says UX for the audit log is "too dense."
    - Decision: Simplify the log view to a "summary table" with a "detail drill-down."
    - Action: Dayo to update React components by Friday.

### Meeting 2: Stakeholder Alignment - Oct 19, 2024
- **Attendees:** Vera, Project Sponsor, Product Lead.
- **Notes:**
    - Sponsor wants "Quick Reports" added to the dashboard.
    - Vera disagreed; says it's scope creep.
    - Product Lead wants it for the demo.
    - Outcome: Standoff. No decision made.
    - Blocker: Design disagreement between product and engineering leads.

### Meeting 3: Technical Review - Oct 26, 2024
- **Attendees:** Vera, Dayo, Yuki, DevOps.
- **Notes:**
    - SSO integration (SAML) is lagging.
    - Decided to move SSO to "Low Priority."
    - DevOps warns about the manual deployment risk again.
    - Vera: "We'll find a contractor in November."
    - Technical debt: Team spent 10% of this sprint cleaning up the SQLite wrapper. Satisfactory.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000 (Fixed)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $300,000 | Distributed team of 15 (Competitive rates for Rust/React) |
| **Infrastructure** | 10% | $40,000 | Cloudflare Workers, PostgreSQL managed instances, S3 WORM |
| **Tools & Licenses**| 5% | $20,000 | JIRA, GitHub Enterprise, IDE licenses, Monitoring tools |
| **Contingency** | 10% | $40,000 | Reserved for the DevOps contractor and emergency fixes |

**Budget Status:** On track. No overages reported in Q4.

---

## 12. APPENDICES

### Appendix A: Cryptographic Specification for Audit Trails
To ensure the "tamper-evident" nature of the logs, Trellis uses a SHA-256 hash chain.
1. Each event $E_n$ contains a payload $P_n$ and a timestamp $T_n$.
2. The hash for the current event is calculated as: 
   $H_n = \text{SHA-256}(H_{n-1} + P_n + T_n)$
3. The value $H_{n-1}$ is the hash of the preceding event.
4. During a compliance audit, the system re-calculates the chain from $H_0$ to $H_{latest}$. Any mismatch indicates data manipulation.

### Appendix B: HIPAA Data Encryption Standards
All data in the Trellis ecosystem must adhere to the following:
- **In Transit:** TLS 1.3 with AES-256-GCM. All internal service-to-service communication is encrypted.
- **At Rest:** AES-256-XTS encryption for the PostgreSQL cloud database. SQLite edge databases are encrypted using SQLCipher.
- **Key Management:** Keys are rotated every 90 days via a secure Key Management Service (KMS), with master keys stored in a hardware security module (HSM).
- **Auditability:** All access to the decryption keys is logged in the immutable `event_store`.