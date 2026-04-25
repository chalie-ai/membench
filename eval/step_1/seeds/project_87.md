# PROJECT SPECIFICATION DOCUMENT: PROJECT OBELISK
**Version:** 1.0.4  
**Status:** Baseline  
**Date:** October 26, 2023  
**Company:** Pivot North Engineering  
**Project Lead:** Ira Kim (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Obelisk is the strategic initiative by Pivot North Engineering to modernize the company’s core e-commerce marketplace. For 15 years, the organization has relied on a legacy monolithic system that has become a bottleneck for growth, a liability for security, and a burden for maintenance. As the primary vehicle for delivering government services, the marketplace is the lifeblood of the company's revenue stream and operational integrity. 

The objective of Obelisk is to replace this legacy infrastructure with a high-performance, scalable, and secure cloud-native platform. Because this system supports critical government service procurement, the project carries a "zero downtime" mandate. Any interruption in service would not only result in immediate financial loss but would jeopardize Pivot North Engineering's standing with government contracts and regulatory bodies.

### 1.2 Business Justification
The legacy system currently suffers from "architectural rigidity," where a single change to the checkout logic can trigger regressions in the user profile modules. Technical debt has accumulated to a point where the cost of maintenance exceeds the cost of a complete rebuild. Furthermore, the legacy system lacks the granular audit capabilities required by modern government transparency laws. 

Obelisk introduces a Command Query Responsibility Segregation (CQRS) architecture with Event Sourcing. This is not merely a technical preference but a business requirement: in government services, the *history* of how a state was reached is as important as the state itself. By recording every change as a discrete event, Obelisk provides an immutable ledger of all transactions and modifications.

### 1.3 ROI Projection
With a total investment of $3M, Pivot North Engineering expects the following returns over a 36-month horizon:
*   **Operational Efficiency:** A projected 40% reduction in manual support tickets related to "ghost orders" and data inconsistencies, which currently cost the company $120k/year in labor.
*   **Revenue Growth:** The ability to onboard new government vendors 60% faster due to the new webhook integration framework and modernized API, projected to increase Gross Merchandise Volume (GMV) by 15% annually.
*   **Risk Mitigation:** Elimination of the "Single Point of Failure" risk associated with the legacy server hardware, avoiding potential outages that are estimated to cost $50k per hour of downtime.
*   **Compliance Cost Reduction:** Reduction in audit preparation time from 3 weeks to 2 days via the automated tamper-evident audit trail.

The projected Break-Even Point (BEP) is calculated at 22 months post-deployment, with a forecasted 3-year Net Present Value (NPV) of $1.2M.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Obelisk utilizes a distributed architecture designed for high availability and strict data residency. The core logic is implemented in **Python/Django**, leveraging the framework's robust ORM and administrative capabilities, but decoupled via a CQRS pattern to separate write operations (Commands) from read operations (Queries).

**The Stack:**
*   **Language:** Python 3.11+ / Django 4.2 LTS
*   **Primary Database:** PostgreSQL 15 (Relational store for current state)
*   **Event Store:** PostgreSQL (Append-only event table for event sourcing)
*   **Caching/Messaging:** Redis 7.0 (Used for session management, CQRS projection updates, and as a message broker for Celery)
*   **Infrastructure:** AWS ECS (Elastic Container Service) managing Fargate tasks.
*   **Orchestration:** Kubernetes (EKS) for rolling deployments and auto-scaling.
*   **CI/CD:** GitLab CI with automated pipelines for linting, testing, and deployment.

### 2.2 ASCII Architecture Diagram
```text
[ Client Layer ]  -->  [ AWS Application Load Balancer ]
                               |
                               v
                    [ AWS ECS / EKS Cluster ]
                    -------------------------------------------------------
                    |  [ API Gateway / Django App ]                       |
                    |         |                                          |
                    |         |----(Command)----> [ Command Bus ]         |
                    |         |                      |                    |
                    |         |                      v                    |
                    |         |             [ Event Store (Postgres) ] <---|-- (Audit Log)
                    |         |                      |                  |
                    |         |                      v                    |
                    |         |             [ Event Processor/Worker ]     |
                    |         |                      |                    |
                    |         |                      v                    |
                    |         |             [ Read Model (Postgres/Redis)] |
                    |         |                      |                    |
                    |         |<---(Query)-----------|                    |
                    -------------------------------------------------------
                               |
                               v
                    [ AWS S3 / RDS / ElastiCache ]
                    (Data Residency: EU-Central-1)
```

### 2.3 Data Residency and Compliance
To meet GDPR and CCPA requirements, all production data is strictly hosted in the `eu-central-1` (Frankfurt) region. No PII (Personally Identifiable Information) is permitted to leave the EU boundary. Database backups are encrypted using AWS KMS with customer-managed keys. The CQRS event store ensures that any "Right to be Forgotten" request is handled by issuing a "Tombstone" event that masks the PII in the read model while maintaining the integrity of the event chain.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** In Design

**Description:**
The marketplace requires a collaborative environment where government procurement officers can co-edit service requisitions and contract drafts in real-time. Because multiple users may edit the same field simultaneously, a sophisticated conflict resolution mechanism is required to prevent data loss.

**Technical Specification:**
The system will implement Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs). Given the need for a linear audit trail, a centralized OT approach integrated with the Django Channels (WebSockets) framework is selected. 

*   **Synchronization:** Every keystroke or change is sent as a "delta" to the server. The server assigns a sequence number to each operation.
*   **Conflict Resolution:** If two users edit the same line, the server utilizes a "Last-Write-Wins" strategy for simple fields, but for large text blocks, it merges changes based on the index of the character change.
*   **State Management:** The current state of the document is cached in Redis for low-latency retrieval, while the full history is persisted in the Event Store.
*   **UI/UX:** Users will see "Presence Indicators" (avatars) showing who is currently editing which section of the document.

**Acceptance Criteria:**
- Support for up to 20 concurrent editors per document.
- Latency between edits across different regions must be $< 200\text{ms}$.
- Zero data loss during simultaneous edits of the same field.

### 3.2 Webhook Integration Framework for Third-Party Tools
**Priority:** Low | **Status:** Complete

**Description:**
To allow external government software (ERP, Budgeting tools) to react to events in the Obelisk marketplace, a flexible webhook system was developed. This allows Pivot North to decouple the core marketplace from external ecosystem dependencies.

**Technical Specification:**
The framework follows a "Publisher-Subscriber" pattern. Users can register a URL and a set of "Event Triggers" (e.g., `order.created`, `payment.failed`, `vendor.verified`).

*   **Delivery Mechanism:** When a triggering event occurs in the CQRS event store, a Celery task is dispatched to push a JSON payload to the registered URL.
*   **Security:** Each payload includes an `X-Obelisk-Signature` header (HMAC SHA-256) allowing the receiver to verify the authenticity of the request.
*   **Retry Policy:** An exponential backoff strategy is implemented (1min, 5min, 30min, 2hrs) for failed deliveries. After 5 failed attempts, the webhook is marked as "Degraded."
*   **Payload Versioning:** Payloads are versioned (e.g., `v1.0`) to ensure backward compatibility as the API evolves.

**Acceptance Criteria:**
- Successful delivery of payloads to verified endpoints within 5 seconds of the event.
- Verification of HMAC signatures on the receiving end.
- Automated disabling of endpoints that return 4xx errors consistently.

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low | **Status:** In Review

**Description:**
Given the sensitivity of government service procurement, standard password-based authentication is insufficient. Obelisk implements a multi-layered 2FA system, prioritizing hardware-based security.

**Technical Specification:**
The system implements the WebAuthn (Web Authentication) standard. This allows users to authenticate using FIDO2-compliant hardware keys (e.g., YubiKey) or biometric providers (TouchID, Windows Hello).

*   **Registration Flow:** Users navigate to Security Settings $\rightarrow$ Enable 2FA $\rightarrow$ Register Key. The server sends a challenge; the key signs it; the server stores the Public Key.
*   **Authentication Flow:** After the primary password check, the system prompts for the hardware key. The browser invokes the WebAuthn API, and the server validates the signature against the stored public key.
*   **Fallback Mechanisms:** TOTP (Time-based One-Time Passwords) via apps like Google Authenticator is provided as a secondary option. Backup codes (10 unique 8-character strings) are generated upon setup.
*   **Session Binding:** Once 2FA is completed, a secure, encrypted session cookie is issued with a 12-hour expiration.

**Acceptance Criteria:**
- Successful login using YubiKey 5 series.
- Successful recovery using backup codes.
- Prevention of login if 2FA is enabled but the second factor is not provided.

### 3.4 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low | **Status:** In Design

**Description:**
To meet strict government regulatory requirements, Obelisk must maintain an immutable record of every action taken within the system. This is not a simple log file, but a cryptographically verifiable trail.

**Technical Specification:**
The system utilizes a "Merkle Tree" inspired hashing approach for the Event Store. 

*   **Chaining:** Each audit entry contains the hash of the previous entry. This creates a cryptographic chain where altering a single record invalidates all subsequent hashes.
*   **Storage:** Audit logs are written to a WORM (Write Once, Read Many) S3 bucket with "Object Lock" enabled.
*   **Verification:** A daily "Heartbeat" process calculates the root hash of the day's events and signs it with a corporate private key.
*   **Granularity:** Every field change is logged: `User ID`, `Timestamp`, `Action`, `Old Value`, `New Value`, `IP Address`, and `Request ID`.

**Acceptance Criteria:**
- Proof of tampering if any record in the database is manually altered.
- Ability to reconstruct the state of any entity at any specific point in time.
- Audit logs are immutable and cannot be deleted even by the system administrator.

### 3.5 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** Complete

**Description:**
A robust identity management system is required to handle the diverse range of users, from government auditors to third-party vendors.

**Technical Specification:**
Obelisk uses a custom RBAC implementation built on Django’s `AbstractUser` and `Group` models, extended for granular permissioning.

*   **Roles:** Defined roles include `SuperAdmin`, `ProcurementOfficer`, `VendorManager`, `Auditor`, and `Guest`.
*   **Permission Mapping:** Permissions are mapped to specific "Actions" (e.g., `can_approve_contract`, `can_edit_vendor_profile`).
*   **Middleware:** A custom Django middleware intercepts every request, checking the user's role against the required permission for the target view/endpoint.
*   **Token Management:** JWT (JSON Web Tokens) are used for API authentication, with a short-lived access token (15 mins) and a long-lived refresh token (7 days).

**Acceptance Criteria:**
- Users with the `Auditor` role can view all documents but cannot edit any.
- Users with `Guest` role cannot access the `/admin` or `/procurement` dashboards.
- Successful token refresh without requiring re-authentication for 7 days.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful principles. Base URL: `https://api.obelisk.pivotnorth.com/v1/`

### 4.1 `POST /auth/login`
**Description:** Authenticates user and returns JWT tokens.
*   **Request:**
    ```json
    {
      "username": "jdoe_gov",
      "password": "secure_password123"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "access_token": "eyJhbG...",
      "refresh_token": "def456...",
      "expires_in": 900
    }
    ```

### 4.2 `GET /contracts/{contract_id}`
**Description:** Retrieves the current state of a government contract.
*   **Request:** `GET /contracts/CONT-9982`
*   **Response (200 OK):**
    ```json
    {
      "id": "CONT-9982",
      "status": "Draft",
      "value": 450000.00,
      "vendor": "GlobalTech Inc",
      "last_modified": "2023-10-25T14:00:00Z"
    }
    ```

### 4.3 `PATCH /contracts/{contract_id}`
**Description:** Updates contract details (triggers a Command in CQRS).
*   **Request:**
    ```json
    {
      "value": 460000.00,
      "reason": "Added shipping costs"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    { "message": "Update request queued", "job_id": "job_abc123" }
    ```

### 4.4 `GET /audit/logs?entity=contract&id=CONT-9982`
**Description:** Retrieves the full event history for a specific entity.
*   **Response (200 OK):**
    ```json
    [
      { "event_id": 101, "timestamp": "...", "change": "Created", "user": "admin" },
      { "event_id": 105, "timestamp": "...", "change": "Value updated to 460k", "user": "jdoe" }
    ]
    ```

### 4.5 `POST /webhooks/register`
**Description:** Registers a third-party URL for event notifications.
*   **Request:**
    ```json
    {
      "url": "https://client-erp.gov/webhook",
      "events": ["order.created", "order.completed"]
    }
    ```
*   **Response (201 Created):**
    ```json
    { "webhook_id": "wh_789", "status": "active" }
    ```

### 4.6 `POST /auth/2fa/register`
**Description:** Registers a FIDO2 hardware key.
*   **Request:**
    ```json
    {
      "credentialId": "base64_id",
      "publicKey": "base64_pubkey",
      "transports": ["usb"]
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "Key registered successfully" }
    ```

### 4.7 `GET /vendors`
**Description:** Lists all approved vendors.
*   **Response (200 OK):**
    ```json
    [
      { "id": "V-1", "name": "GovSupply Co", "rating": 4.8 },
      { "id": "V-2", "name": "SecureNet", "rating": 4.2 }
    ]
    ```

### 4.8 `DELETE /auth/logout`
**Description:** Invalidates the current session and refresh token.
*   **Response (204 No Content):** `Empty Body`

---

## 5. DATABASE SCHEMA

The Obelisk database utilizes a dual-store approach: the **State Store** (current snapshot) and the **Event Store** (immutable history).

### 5.1 Table Definitions

| Table Name | Description | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | User identity and credentials | `id (PK)`, `email`, `password_hash`, `role_id (FK)` | $\rightarrow$ roles |
| `roles` | RBAC role definitions | `id (PK)`, `role_name`, `permissions_json` | $\leftarrow$ users |
| `profiles` | User metadata/contact info | `id (PK)`, `user_id (FK)`, `full_name`, `dept` | $\rightarrow$ users |
| `vendors` | Marketplace vendor data | `id (PK)`, `company_name`, `tax_id`, `status` | $\leftarrow$ contracts |
| `contracts` | Current state of agreements | `id (PK)`, `vendor_id (FK)`, `total_value`, `version` | $\rightarrow$ vendors |
| `event_store` | Immutable event log (CQRS) | `event_id (PK)`, `entity_type`, `entity_id`, `payload`, `created_at` | $\rightarrow$ contracts/users |
| `webhooks` | Third-party integration URLs | `id (PK)`, `target_url`, `secret_key`, `is_active` | N/A |
| `webhook_logs` | History of webhook deliveries | `id (PK)`, `webhook_id (FK)`, `response_code`, `timestamp` | $\rightarrow$ webhooks |
| `auth_keys` | FIDO2 Public Keys | `id (PK)`, `user_id (FK)`, `public_key`, `device_name` | $\rightarrow$ users |
| `audit_hashes` | Cryptographic chain anchors | `block_id (PK)`, `previous_hash`, `current_hash`, `timestamp` | N/A |

### 5.2 Relationship Logic
1.  **One-to-Many:** One `Role` can be assigned to many `Users`.
2.  **One-to-One:** Each `User` has exactly one `Profile`.
3.  **Many-to-One:** Many `Contracts` belong to one `Vendor`.
4.  **Event Sourcing:** The `event_store` acts as the source of truth. The `contracts` table is a "Projection"—a materialized view created by replaying events from the `event_store`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Obelisk maintains three distinct environments to ensure stability and zero downtime.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and unit testing.
*   **Configuration:** Shared PostgreSQL instance, local Redis.
*   **Deployments:** Triggered on every commit to a feature branch.
*   **Data:** Anonymized subsets of production data.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Integration testing and UAT (User Acceptance Testing).
*   **Configuration:** Exact mirror of Production (EKS cluster, RDS Multi-AZ).
*   **Deployments:** Triggered on merge to `main`.
*   **Data:** Full snapshot of production data (scrubbed of PII).

#### 6.1.3 Production (Prod)
*   **Purpose:** Live government services.
*   **Configuration:** High-availability EKS cluster across 3 availability zones.
*   **Deployment:** Rolling updates via GitLab CI. New pods are spun up and health-checked before old pods are drained (Zero-Downtime).
*   **Data:** Live encrypted data in `eu-central-1`.

### 6.2 CI/CD Pipeline
The pipeline is managed via `.gitlab-ci.yml` and consists of four stages:
1.  **Lint/Test:** Run `flake8` and `pytest` (Unit tests).
2.  **Build:** Create Docker image $\rightarrow$ Push to AWS ECR.
3.  **Deploy-Stage:** Update K8s manifests in staging.
4.  **Deploy-Prod:** Manual trigger $\rightarrow$ Canary deployment (5% traffic $\rightarrow$ 25% $\rightarrow$ 100%).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Scope:** Individual functions, Django models, and utility helpers.
*   **Tooling:** `pytest` and `unittest.mock`.
*   **Coverage Goal:** 85% line coverage.
*   **Execution:** Run on every push to GitLab.

### 7.2 Integration Testing
*   **Scope:** Interaction between Django, PostgreSQL, and Redis.
*   **Approach:** Spin up temporary containers using `Docker Compose` to test the CQRS event flow (Command $\rightarrow$ Event Store $\rightarrow$ Projection $\rightarrow$ Read Model).
*   **Critical Path:** Testing the "Eventual Consistency" window to ensure the read model updates within 500ms.

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Complete user journeys (e.g., Login $\rightarrow$ Create Contract $\rightarrow$ Approve Contract).
*   **Tooling:** `Playwright` or `Selenium`.
*   **Focus:** Critical path workflows and cross-browser compatibility (Chrome, Firefox, Edge).

### 7.4 Security Testing
*   **DAST/SAST:** Integration of `Snyk` and `Bandit` into the CI pipeline to detect vulnerabilities.
*   **Penetration Testing:** Semi-annual external audit to ensure GDPR/CCPA compliance.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements change during dev | High | High | Weekly monitoring meetings; design for modularity. |
| R-02 | Project Sponsor rotation | Medium | Medium | Engage external consultant for independent assessment. |
| R-03 | Zero-downtime migration failure | Low | Critical | Blue/Green deployment; detailed rollback scripts. |
| R-04 | Team trust/collaboration gaps | Medium | Medium | Agile ceremonies; shared ownership of modules. |
| R-05 | Data residency breach | Low | Critical | AWS Region locking; strict IAM policies. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal action.
- **High:** Significant delay or budget overage.
- **Medium:** Manageable impact on timeline.
- **Low:** Minor annoyance.

---

## 9. TIMELINE

### 9.1 Phases and Dependencies

| Phase | Duration | Focus | Dependency |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Oct '23 - Jan '24 | RBAC, Infrastructure, Core API | None |
| **Phase 2: Core Logic** | Feb '24 - Jun '24 | CQRS Implementation, Vendor Modules | Phase 1 |
| **Phase 3: Collaboration** | Jul '24 - Oct '24 | Real-time editing, WebSockets | Phase 2 |
| **Phase 4: Hardening** | Nov '24 - Mar '25 | 2FA, Audit Trail, Security Patching | Phase 3 |
| **Phase 5: Migration** | Apr '25 - Aug '25 | Legacy Data Migration, Zero-Downtime Cutover | Phase 4 |

### 9.2 Key Milestones
- **M1: Production Launch (2025-08-15):** The system goes live for all government users.
- **M2: Security Audit Passed (2025-10-15):** External verification of GDPR and FIPS compliance.
- **M3: MVP Feature-Complete (2025-12-15):** All "low" priority features (Webhooks, 2FA) fully optimized.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Ira, Nadia, Sol, Wyatt  
- CQRS vs Monolith.  
- Ira wants event sourcing.  
- Nadia concerned about K8s complexity.  
- Sol needs read-only audit logs.  
- Decision: Use Postgres for both event and state stores to reduce infra overhead.

### Meeting 2: Security Review
**Date:** 2023-12-15  
**Attendees:** Ira, Sol, Nadia  
- 2FA discussion.  
- Sol insists on YubiKeys for admins.  
- Wyatt says users will complain about hardware requirements.  
- Decision: Hardware keys for Admin; TOTP for standard users.  
- Blocker: Legal review of Data Processing Agreement (DPA) still pending.

### Meeting 3: Technical Debt Sync
**Date:** 2024-01-20  
**Attendees:** Ira, Nadia, Wyatt  
- Date format issue.  
- Wyatt found ISO-8601, Epoch, and US-Slash formats in the codebase.  
- Nadia suggests a normalization layer.  
- Decision: Postpone normalization until Phase 2; use a wrapper for now.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | 15 distributed engineers over 2.5 years. |
| **Infrastructure** | $450,000 | AWS EKS, RDS, S3, and CloudFront costs. |
| **Tools & Licenses** | $150,000 | GitLab Ultimate, Snyk, Datadog, Jira. |
| **External Consultants**| $200,000 | Security audit and sponsor-rotation assessment. |
| **Contingency (13.3%)** | $400,000 | For regulatory shifts and scope creep. |

---

## 12. APPENDICES

### Appendix A: Date Normalization Plan
Current Technical Debt: The system currently uses three date formats:
1. `YYYY-MM-DD` (ISO)
2. `Unix Timestamp` (Integer)
3. `MM/DD/YYYY` (Legacy US)

**Resolution Path:**
A `DateNormalizationMiddleware` will be implemented in Phase 2. All incoming API requests will be coerced into ISO-8601. The database layer will store all timestamps as `UTC TIMESTAMP WITH TIME ZONE`. A utility class `ObeliskDate` will handle the conversion for legacy exports.

### Appendix B: Distributed Team Logistics
The team is distributed across 5 countries (USA, Germany, India, Canada, Estonia). 
- **Core Hours:** 14:00 - 17:00 UTC (The "Golden Window" where all members are online).
- **Communication:** Slack for async; Zoom for daily stand-ups; GitLab for code review.
- **Trust Building:** Bi-weekly virtual "Social Hours" and peer-programming pairs to accelerate the forming stage of the team dynamic.