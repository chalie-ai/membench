Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). It is designed as the "Single Source of Truth" (SSOT) for the development team.

***

# PROJECT VANGUARD: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 26, 2023  
**Company:** Verdant Labs  
**Classification:** Confidential – HIPAA Protected

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Vanguard is a strategic platform modernization effort undertaken by Verdant Labs. The primary objective is the transformation of a legacy monolithic healthcare records system—specifically tailored for the automotive industry (managing driver health certifications, occupational health records for plant workers, and fleet medical compliance)—into a scalable, resilient microservices architecture. This transition is slated for completion over an 18-month window.

The automotive industry requires specialized health tracking (e.g., DOT medical exams, heavy machinery certifications, and long-term occupational exposure tracking). The legacy system has become a bottleneck, hindering the ability of Verdant Labs to scale its client base and integrate with modern automotive ERPs. Vanguard replaces this technical debt with a high-concurrency system built on Elixir and Phoenix, utilizing LiveView for real-time data synchronization.

### 1.2 Business Justification
The legacy monolith is currently operating at 85% capacity during peak reporting periods, leading to latency issues that risk non-compliance with automotive safety regulations. By shifting to a microservices-oriented approach, Verdant Labs can decouple the "Compliance Engine" from the "User Portal," allowing for independent scaling. 

Furthermore, the shift enables the introduction of a customer-facing API, allowing automotive OEMs to pull health compliance data directly into their workforce management systems. This transforms Vanguard from a simple record-keeping tool into a critical piece of the automotive supply chain infrastructure.

### 1.3 ROI Projection and Financial Goals
With a total budget allocation of $5.2M, the project is a flagship initiative reporting directly to the Board of Directors. The financial success of Vanguard is measured by two primary KPIs:
1. **Direct Revenue Generation:** A target of $500,000 in new attributed revenue within the first 12 months post-launch. This is expected to come from "API Tier" subscriptions offered to fleet managers.
2. **Operational Efficiency:** A projected 30% reduction in infrastructure costs by moving from oversized legacy servers to right-sized Fly.io micro-instances.
3. **Risk Mitigation:** Avoiding the potential million-dollar fines associated with HIPAA non-compliance or data breaches through the implementation of modern encryption-at-rest and transit protocols.

### 1.4 Strategic Alignment
Vanguard aligns with the "Verdant 2025" digital transformation goal. By migrating the monolith, the company reduces its "Bus Factor" (currently high due to only two developers understanding the legacy COBOL/Java hybrid core) and empowers a distributed team of 15 specialists across 5 countries to contribute to a modern, documented codebase.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Philosophy
Vanguard utilizes a traditional three-tier architecture, adapted for a microservices transition. While the ultimate goal is full decomposition, the initial phase implements a "Strangler Fig" pattern where new features are built as services around the legacy core.

- **Presentation Tier:** Phoenix LiveView for real-time updates and a React-based administrative dashboard.
- **Business Logic Tier:** Elixir/Phoenix applications utilizing GenServers for state management and Observers for monitoring.
- **Data Tier:** PostgreSQL with read-replicas for reporting and an encrypted vault for PII (Personally Identifiable Information).

### 2.2 Infrastructure Stack
- **Language:** Elixir 1.15+
- **Framework:** Phoenix 1.7 (LiveView for real-time collaboration)
- **Database:** PostgreSQL 15 (Managed via Fly.io)
- **Deployment:** Fly.io (Global distribution to reduce latency for the distributed team)
- **Caching:** Redis for session management and API rate limiting.

### 2.3 ASCII Architecture Diagram
```text
[ CLIENT LAYER ] 
       |
       v
[ EDGE GATEWAY / LOAD BALANCER ] (Fly.io Anycast)
       |
       +-----------------------+-----------------------+
       |                       |                       |
 [ API GATEWAY ]        [ LIVEVIEW SOCKET ]     [ ADMIN PORTAL ]
 (REST/JSON)             (Websocket/State)      (HTML/JS)
       |                       |                       |
       v                       v                       v
 [ MICROSERVICES ] <---> [ MESSAGE BUS ] <---> [ LEGACY MONOLITH ]
 (Auth Service)           (Phoenix PubSub)       (Data Migration)
 (Notification Svc)
 (Records Service)
       |
       v
 [ DATA PERSISTENCE LAYER ]
       |
       +---> [ PostgreSQL Primary ] (Write)
       |
       +---> [ PostgreSQL Replica ] (Read)
       |
       +---> [ Encrypted Vault ] (HIPAA PII)
```

### 2.4 Security Protocols
Vanguard is strictly HIPAA compliant. All data must be encrypted:
- **At Rest:** AES-256 encryption for all database volumes.
- **In Transit:** TLS 1.3 for all API calls and internal service-to-service communication.
- **Field Level:** PII fields (SSN, Medical History) are encrypted using a separate key management service (KMS) before being stored in PostgreSQL.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API (Priority: Critical)
**Status:** In Review | **Version:** v1.0.0-beta

**Description:**
The API is the primary vehicle for the $500K revenue goal. It allows external automotive partners to programmatically manage driver health records. Because this is a "launch blocker," it requires rigorous versioning and a sandbox environment to ensure third-party developers do not corrupt production data.

**Functional Requirements:**
- **Versioning:** The API must use URI versioning (e.g., `/api/v1/...`). Version 1 will be supported for 24 months after v2 is released.
- **Sandbox Environment:** A mirrored environment (`sandbox-api.vanguard.verdantlabs.com`) with synthetic data. Sandbox keys are distinct from production keys.
- **Rate Limiting:** Implemented via Redis. Standard tier: 1,000 requests/hour; Premium tier: 10,000 requests/hour.
- **Authentication:** API Key-based authentication with rotation capabilities.

**Technical Logic:**
The API acts as a facade over the microservices. When a request hits `/api/v1/records`, the API Gateway authenticates the key, checks the rate limit in Redis, and proxies the request to the `Records Service`.

**Acceptance Criteria:**
- Ability to create, read, update, and delete (CRUD) a health record.
- Sandbox environment returns a 200 OK for synthetic IDs.
- API documentation (Swagger/OpenAPI) is auto-generated and accessible.

---

### 3.2 Notification System (Priority: High)
**Status:** In Review

**Description:**
A multi-channel notification engine to alert automotive fleet managers and drivers of expiring health certifications. This system must handle high volumes of asynchronous messages without blocking the main application thread.

**Functional Requirements:**
- **Email:** Integration with SendGrid for formal health notices.
- **SMS:** Integration with Twilio for urgent alerts (e.g., "Certification Expired").
- **In-App:** Real-time toast notifications powered by Phoenix LiveView.
- **Push:** Firebase Cloud Messaging (FCM) for mobile alerts.

**Technical Logic:**
The system uses a "Notification Dispatcher" pattern. A business event (e.g., `RecordExpired`) is published to the Phoenix PubSub. The `Notification Service` subscribes to this event and checks the user's `NotificationPreferences` table to determine which channels to trigger. This prevents "notification fatigue."

**Acceptance Criteria:**
- Latency from event trigger to email dispatch < 30 seconds.
- User can opt-out of SMS but remain opted-in for Email.
- Retries are implemented for failed SMS deliveries using an exponential backoff strategy.

---

### 3.3 Customizable Dashboard (Priority: Medium)
**Status:** In Design

**Description:**
A drag-and-drop interface for health administrators to organize their workspace. Since different automotive roles (e.g., Safety Officer vs. Plant Manager) need different data, the dashboard must be modular.

**Functional Requirements:**
- **Widget Library:** Pre-built widgets including "Expiring Certs," "Patient Volume," "Audit Logs," and "Regional Compliance Heatmap."
- **Drag-and-Drop:** Users can resize and reposition widgets.
- **Persistence:** Layout configurations must be saved to the database per user.
- **Real-time Data:** Widgets must update via LiveView without page refreshes.

**Technical Logic:**
The layout is stored as a JSON blob in the `user_dashboard_configs` table. The frontend uses a grid-system (similar to Gridstack.js) where each widget is a Phoenix LiveComponent. When a widget is moved, a `handle_event` call updates the JSON blob in the background.

**Acceptance Criteria:**
- Widgets maintain position after page reload.
- Page load time for dashboard < 2 seconds with 10 active widgets.
- Support for at least 5 distinct widget types.

---

### 3.4 User Authentication and RBAC (Priority: Medium)
**Status:** Complete

**Description:**
A robust identity management system ensuring that only authorized personnel can access sensitive medical records. This is the foundation of the platform's security.

**Functional Requirements:**
- **Multi-Factor Authentication (MFA):** Mandatory for all admin accounts.
- **Role-Based Access Control (RBAC):** Defined roles including `SuperAdmin`, `MedicalOfficer`, `FleetManager`, and `Driver`.
- **Session Management:** Secure cookies with 15-minute inactivity timeouts.
- **Audit Logging:** Every login attempt and role change is logged with a timestamp and IP address.

**Technical Logic:**
Implemented using `Pow` for authentication and a custom `Permission` schema. The `RBAC` logic is handled in the Phoenix pipeline: `plug :check_role, roles: [:medical_officer]`.

**Acceptance Criteria:**
- A `Driver` cannot access the `MedicalOfficer` record edit page.
- MFA challenge is triggered on login from a new IP.
- Session expires precisely after 15 minutes of inactivity.

---

### 3.5 Real-time Collaborative Editing (Priority: High)
**Status:** Blocked

**Description:**
Allows multiple medical professionals to update a single patient record simultaneously without overwriting each other's changes. This is critical for complex medical reviews.

**Functional Requirements:**
- **Presence Indicators:** Show who is currently viewing/editing a record (e.g., "Dr. Smith is typing...").
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs).
- **Auto-save:** Changes are saved in real-time as the user types.
- **Version History:** Ability to revert to a previous version of the record.

**Technical Logic:**
Utilizes Phoenix Presence to track active users. The conflict resolution will use a "Last Write Wins" (LWW) approach for simple fields and a CRDT approach for large text blocks (Medical Notes).

**Blocker Detail:** Currently blocked due to a mismatch between the legacy monolith's locking mechanism and the microservices' distributed state. The legacy system uses pessimistic locking (DB locks), while the new system requires optimistic locking.

**Acceptance Criteria:**
- Two users editing the same field see updates in < 100ms.
- No data loss during concurrent edits.
- History log shows exactly who changed which field.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require an `X-API-KEY` in the header.

### 4.1 Get Health Record
- **Path:** `/records/{record_id}`
- **Method:** `GET`
- **Request:** `GET /api/v1/records/REC-9921`
- **Response (200 OK):**
```json
{
  "id": "REC-9921",
  "patient_name": "John Doe",
  "status": "Certified",
  "expiry_date": "2025-12-01",
  "last_updated": "2023-10-20T10:00:00Z"
}
```

### 4.2 Create Health Record
- **Path:** `/records`
- **Method:** `POST`
- **Request:** 
```json
{
  "patient_name": "Jane Smith",
  "dob": "1985-05-12",
  "certification_type": "DOT-Medical"
}
```
- **Response (201 Created):** `{"id": "REC-9922", "status": "Pending"}`

### 4.3 Update Record Status
- **Path:** `/records/{record_id}/status`
- **Method:** `PATCH`
- **Request:** `{"status": "Expired"}`
- **Response (200 OK):** `{"id": "REC-9921", "new_status": "Expired"}`

### 4.4 List All Records (Paginated)
- **Path:** `/records`
- **Method:** `GET`
- **Params:** `?page=1&per_page=20`
- **Response (200 OK):** `{"data": [...], "meta": {"total": 1500, "page": 1}}`

### 4.5 Trigger Notification
- **Path:** `/notifications/send`
- **Method:** `POST`
- **Request:** `{"user_id": "USR-123", "message": "Your cert expires in 30 days", "channel": "sms"}`
- **Response (202 Accepted):** `{"job_id": "job_abc_123"}`

### 4.6 Get User Permissions
- **Path:** `/users/{user_id}/permissions`
- **Method:** `GET`
- **Response (200 OK):** `{"user_id": "USR-123", "roles": ["FleetManager"], "can_edit": false}`

### 4.7 Update Dashboard Layout
- **Path:** `/user/dashboard/layout`
- **Method:** `PUT`
- **Request:** `{"layout": [{"widget": "certs", "x": 0, "y": 0, "w": 2, "h": 2}]}`
- **Response (200 OK):** `{"status": "saved"}`

### 4.8 Get Audit Log
- **Path:** `/audit/logs`
- **Method:** `GET`
- **Params:** `?start_date=2023-01-01&end_date=2023-10-26`
- **Response (200 OK):** `[{"timestamp": "...", "action": "LOGIN", "user": "Admin1"}]`

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 15. Relationships are strictly enforced via foreign keys, except in the `audit_logs` table to ensure high write throughput.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationship | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `id` (UUID) | `email`, `password_hash`, `mfa_secret` | 1:1 with `profiles` | Core identity |
| `profiles` | `id` (UUID) | `first_name`, `last_name`, `phone` | FK to `users` | Personal details |
| `roles` | `id` (INT) | `role_name` (e.g., 'SuperAdmin') | 1:N with `user_roles` | RBAC definitions |
| `user_roles` | `id` (UUID) | `user_id`, `role_id` | FK to `users` & `roles` | Mapping users to roles |
| `records` | `id` (UUID) | `patient_id`, `cert_type`, `status`, `expiry_date` | FK to `profiles` | Medical records |
| `medical_notes` | `id` (UUID) | `record_id`, `note_content`, `author_id` | FK to `records` | Detailed health notes |
| `notifications` | `id` (UUID) | `user_id`, `channel`, `message`, `sent_at` | FK to `users` | Outbound alerts |
| `notification_prefs`| `id` (UUID) | `user_id`, `sms_enabled`, `email_enabled` | FK to `users` | User preferences |
| `dashboard_configs` | `id` (UUID) | `user_id`, `layout_json` | FK to `users` | Widget positions |
| `audit_logs` | `id` (BIGINT) | `actor_id`, `action`, `ip_address`, `timestamp` | FK to `users` (Loose) | Compliance tracking |

### 5.2 Key Constraints
- **Unique Index:** `users.email` must be unique.
- **Check Constraint:** `records.status` must be one of `['Pending', 'Certified', 'Expired', 'Revoked']`.
- **Encryption:** The `medical_notes.note_content` field is stored as an encrypted binary blob.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Vanguard utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and internal testing.
- **Configuration:** Lower-spec Fly.io instances, mock external APIs (Twilio/SendGrid).
- **Deployment:** Automated on every push to the `develop` branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Configuration:** Mirrored production specs. Uses a sanitized copy of production data (PII stripped).
- **Deployment:** Triggered by merge to `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer environment.
- **Configuration:** High-availability cluster across 3 regions (US-East, US-West, EU-West).
- **Deployment:** Weekly Release Train.

### 6.2 The "Release Train" Policy
Vanguard follows a strict **Weekly Release Train** schedule.
- **Deployment Window:** Every Tuesday at 03:00 UTC.
- **Cut-off:** All code must be merged to the `main` branch by Monday 12:00 UTC.
- **No Hotfixes:** There are no hotfixes outside the train. If a critical bug is found, it is patched and deployed in the next Tuesday window. *Exception: Total system outage (Board-level approval required).*

### 6.3 Fly.io Configuration
- **Regions:** `iad` (Virginia), `sjc` (San Jose), `ams` (Amsterdam).
- **Scaling:** Horizontal autoscaling based on CPU usage > 60%.
- **Backups:** Daily snapshots of PostgreSQL stored in an encrypted S3 bucket.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Pure functions, business logic, and utility modules.
- **Tooling:** `ExUnit`.
- **Requirement:** 80% code coverage minimum for all new services.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** Service-to-service communication and database integrity.
- **Tooling:** `Wallaby.js` (for frontend), `ExUnit` with `Ecto.Adapters.SQL.Sandbox`.
- **Scenario:** Verify that the `Notification Service` correctly triggers when a `Record` is updated to "Expired" in the `Records Service`.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "Driver uploads certificate -> Admin approves -> Notification sent").
- **Tooling:** Playwright.
- **Execution:** Run once per Release Train (Monday night).

### 7.4 Security Testing
- **Penetration Testing:** Quarterly external audit.
- **Static Analysis:** `Sobelow` for Elixir security scanning.
- **HIPAA Validation:** Automated checks to ensure no PII is logged in plain text in the `audit_logs`.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding "small" features. | High | Medium | **Parallel-Path:** Prototype alternative approaches simultaneously to show cost/time trade-offs. |
| **R2** | Team lacks experience with Elixir/Phoenix/LiveView. | High | High | **External Expert:** Engage an external consultant for a weekly independent code assessment and architectural review. |
| **R3** | Legacy Monolith data corruption during migration. | Medium | High | **Dual-Write:** Implement dual-writing to both legacy and new DBs for 30 days before cutting over. |
| **R4** | Distributed team communication lag (5 countries). | Medium | Medium | **Asynchronous First:** Move all decision-making to Slack threads and documented RFCs. |

**Probability/Impact Matrix:**
- **High/High:** Immediate priority (R2).
- **High/Medium:** Managed via process (R1).
- **Medium/High:** Technical safeguard (R3).

---

## 9. TIMELINE & MILESTONES

The project spans 18 months, divided into four primary phases.

### 9.1 Phase 1: Foundation (Months 1-6)
- **Focus:** Auth system, Infrastructure setup, Legacy API bridge.
- **Key Dependency:** Finalization of HIPAA encryption keys.
- **Milestone:** User Authentication & RBAC Complete (Achieved).

### 9.2 Phase 2: Core Feature Set (Months 7-12)
- **Focus:** Customer API, Notification System, Dashboard.
- **Key Dependency:** API Sandbox stability.
- **Milestone:** **MVP Feature-Complete (Target: 2025-06-15)**.

### 9.3 Phase 3: Advanced Collaboration (Months 13-15)
- **Focus:** Real-time collaborative editing, conflict resolution.
- **Key Dependency:** Resolution of "God Class" technical debt.
- **Milestone:** **Post-launch stability confirmed (Target: 2025-04-15)**. *Note: This occurs during the transition from Beta to GA.*

### 9.4 Phase 4: Validation & Handover (Months 16-18)
- **Focus:** External audits, Performance tuning, Legacy decommissioning.
- **Key Dependency:** Passing the 3rd party security audit.
- **Milestone:** **Security Audit Passed (Target: 2025-08-15)**.

---

## 10. MEETING NOTES (SLACK THREAD ARCHIVE)

*Note: Per company policy, formal meeting minutes are not kept. Decisions are captured in Slack threads.*

### Thread 1: The "God Class" Dilemma
**Date:** 2023-11-02
**Participants:** Hana Kim, Yves Nakamura, Maren Park
**Discussion:** 
Maren raised a concern that the `AuthManager` class has grown to 3,000 lines. It currently handles authentication, logging, AND email dispatch. 
**Decision:** 
Hana Kim ruled that we cannot refactor the entire class now without risking the release train. We will "strangle" it by moving the email logic into the new `Notification Service` first. The logging will remain in the God Class until Phase 3.
**Outcome:** Email logic migrated to Microservice; `AuthManager` reduced by 400 lines.

### Thread 2: Sandbox vs. Production Data
**Date:** 2023-11-15
**Participants:** Hana Kim, Kai Jensen, Yves Nakamura
**Discussion:** 
Kai suggested that customers want "real-world" data in the sandbox to test their integrations. Yves argued that this violates HIPAA if not perfectly anonymized.
**Decision:** 
The team will not use production data. Instead, Yves will write a script to generate "Synthetic Automotive Personas" (fake drivers with plausible medical histories).
**Outcome:** Implementation of a synthetic data generator.

### Thread 3: Real-time Conflict Strategy
**Date:** 2023-12-01
**Participants:** Hana Kim, Yves Nakamura
**Discussion:** 
Yves pointed out that the legacy monolith uses `SELECT FOR UPDATE` (pessimistic locking), which will kill performance in a distributed LiveView environment.
**Decision:** 
We will shift to optimistic locking for the new records. If two users edit the same field, the second user will receive a "Version Mismatch" notification and be asked to merge changes.
**Outcome:** Feature 5 (Collaborative Editing) marked as "Blocked" until the locking strategy is fully reconciled with the legacy core.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,200,000

### 11.1 Personnel ($3.8M)
- **Engineering Salaries:** $2.5M (15 members, distributed across 5 countries).
- **External Consultant:** $400K (Architecture review and Elixir mentorship).
- **Project Management/Lead:** $900K (Hana Kim and board reporting overhead).

### 11.2 Infrastructure ($600K)
- **Fly.io Hosting:** $300K (Including global distribution and managed Postgres).
- **Security Tooling:** $150K (KMS, SSL certificates, Pen-testing licenses).
- **SaaS Integrations:** $150K (SendGrid, Twilio, Firebase).

### 11.3 Tools & Licenses ($300K)
- **DevOps Tools:** $100K (GitHub Enterprise, Datadog, Sentry).
- **UX Research Tools:** $100K (UserTesting.com, Figma).
- **Hardware/Laptops:** $100K (Standardized dev kits for the distributed team).

### 11.4 Contingency ($500K)
- **Reserve:** $500K allocated for unforeseen technical hurdles (e.g., extending the "God Class" refactor) or emergency security patches.

---

## 12. APPENDICES

### Appendix A: The "God Class" Technical Debt Map
The `AuthManager` class (currently 3,000 lines) is the primary source of technical debt. It is mapped as follows:
- **Lines 1-800:** Session management and Cookie handling.
- **Lines 801-1600:** Password hashing and MFA validation logic.
- **Lines 1601-2200:** SMTP configuration and Email template rendering (To be moved to Notification Service).
- **Lines 2201-3000:** Legacy logging to flat files and database audit trails.

### Appendix B: HIPAA Encryption Specification
To meet compliance, Vanguard uses a "Double-Envelope" encryption strategy:
1. **Data Encryption Key (DEK):** A unique AES-256 key is generated for every single health record.
2. **Key Encryption Key (KEK):** The DEK is then encrypted using a Master Key stored in a hardware security module (HSM).
3. **Storage:** The encrypted DEK is stored in the `records` table, while the actual record content is stored in the `medical_notes` table. This ensures that even a full database dump is useless without the HSM master key.