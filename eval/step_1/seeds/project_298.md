# PROJECT SPECIFICATION DOCUMENT: PROJECT CANOPY
**Document Version:** 1.0.4  
**Status:** Active/Draft  
**Last Updated:** October 24, 2023  
**Project Owner:** Lev Park (Tech Lead)  
**Company:** Stratos Systems  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Canopy" is a strategic healthcare records platform designed by Stratos Systems to consolidate four disparate, redundant internal tools into a single, unified ecosystem. Currently, the organization suffers from fragmented data silos, overlapping license costs, and inefficient operational workflows caused by the maintenance of four legacy systems: *MedTrack (Patient Records), CliniFlow (Scheduling), HealthVault (Document Storage), and SignalPath (Patient Notifications).* 

The objective of Canopy is to eliminate these redundancies by migrating all functionality into a high-performance, HIPAA-compliant monolith. By centralizing these operations, Stratos Systems aims to reduce operational overhead, minimize the risk of data synchronization errors, and provide a seamless interface for healthcare providers.

### 1.2 Business Justification
The current architectural fragmentation results in a "tax" on productivity. Developers must maintain four separate codebase environments, and clinicians must toggle between four different UIs to complete a single patient intake process. This fragmentation has led to an estimated 15% increase in administrative errors and a significant increase in cloud infrastructure spending due to redundant database instances and overlapping API gateways.

Canopy is not merely a technical migration but a cost-reduction initiative. By consolidating these tools, Stratos Systems will realize immediate savings in software licensing (estimated $450k/year) and infrastructure costs. Furthermore, the shift to a modern Elixir/Phoenix stack will allow for higher concurrency with fewer server resources, reducing the total cost of ownership (TCO).

### 1.3 ROI Projection
With a total budget allocation of over $5M, the Board of Directors views Canopy as a flagship initiative. The projected Return on Investment (ROI) is calculated based on the following pillars:

1.  **Direct Cost Savings:** $1.2M over 36 months through the decommissioning of legacy servers and the cancellation of third-party licenses.
2.  **Operational Efficiency:** A projected 20% increase in clinician throughput by reducing the "app-switching" time during patient encounters.
3.  **Risk Mitigation:** Reduction in HIPAA compliance liability. Managing one secure, audited system is significantly cheaper and safer than managing four.
4.  **Scale Potential:** The platform is designed to support 10,000 monthly active users (MAUs) within six months of launch, creating a scalable foundation for future healthcare product expansions.

The break-even point for the $5M investment is projected at 28 months post-launch, primarily driven by the reduction in headcount required for legacy maintenance and the optimization of cloud spend on Fly.io.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The "Clean Monolith" Approach
Canopy utilizes a "Clean Monolith" architecture. Unlike a microservices approach, which would introduce unnecessary network latency and deployment complexity for a small team, Canopy centralizes logic within a single Elixir/Phoenix application. However, to prevent the codebase from becoming a "big ball of mud," the system is strictly divided into **Contexts**. 

Each context (e.g., `Canopy.Accounts`, `Canopy.Records`, `Canopy.Notifications`) owns its own data logic and API. Interaction between contexts is handled through a public API surface, ensuring that a change in the notification logic does not accidentally break the authentication flow.

### 2.2 Technology Stack
- **Language:** Elixir (v1.15+)
- **Web Framework:** Phoenix (v1.7+)
- **Frontend:** Phoenix LiveView (for real-time state management without heavy JS frameworks)
- **Database:** PostgreSQL 15 (Relational data store)
- **Infrastructure:** Fly.io (Global distribution and easy scaling)
- **Security:** AES-256 encryption at rest; TLS 1.3 in transit.

### 2.3 Architecture Diagram (ASCII Representation)

```text
[ USER BROWSER ] <---(WebSocket/HTTPS)---> [ FLY.IO LOAD BALANCER ]
                                                  |
                                                  v
                                      [ PHOENIX LIVEVIEW LAYER ]
                                      (Real-time State & UI)
                                                  |
         __________________________________________|__________________________________________
        |                          |                               |                             |
 [ AUTH CONTEXT ]          [ RECORDS CONTEXT ]            [ AUTOMATION CONTEXT ]        [ NOTIFICATION CONTEXT ]
 (RBAC / Sessions)         (HIPAA Data Store)              (Rule Engine/Webhooks)        (SMS/Email/Push)
        |                          |                               |                             |
        |__________________________|_______________________________|_____________________________|
                                   |
                                   v
                        [ POSTGRESQL DATABASE ]
                        (Encrypted Tables / Raw SQL)
                                   |
                                   v
                        [ S3 COMPATIBLE STORAGE ]
                        (Encrypted File Blobs)
```

### 2.4 Data Flow and Security
Because Canopy handles Protected Health Information (PHI), the architecture enforces a "Zero Trust" internal policy. Every request is intercepted by a Plug (Middleware) that verifies the user's role and session validity. Database access is limited to the application user; no external tools have direct access to the production DB.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical | **Status:** In Review | **Launch Blocker:** Yes

The RBAC system is the foundation of Canopy. Given the sensitivity of healthcare records, the system must implement a "Least Privilege" model. Authentication is handled via secure session cookies and bcrypt password hashing.

**Functional Requirements:**
- **Multi-Factor Authentication (MFA):** Mandatory for all clinical staff. Integration with TOTP (Time-based One-Time Password) apps.
- **Role Hierarchy:** The system supports four primary roles: `SuperAdmin`, `Clinician`, `Nurse`, and `Patient`. 
- **Permission Matrix:** Permissions are not assigned to users, but to roles. Roles are then assigned to users. This allows for rapid updates to access levels across the entire organization.
- **Session Management:** Sessions expire after 15 minutes of inactivity to prevent unauthorized access to unattended terminals.

**Technical Implementation:**
The `Canopy.Accounts` context manages the `users`, `roles`, and `permissions` tables. A custom Phoenix Plug, `Canopy.Plugs.Authorize`, checks the current session's role against the required permission for the requested route. If a user lacks the required role, a 403 Forbidden response is returned.

---

### 3.2 Webhook Integration Framework
**Priority:** Medium | **Status:** In Progress

The Webhook framework allows Canopy to communicate with third-party healthcare tools (e.g., external labs or billing software) without requiring a full API integration for every single vendor.

**Functional Requirements:**
- **Event Subscription:** Users can define "Events" (e.g., `patient.record_updated`, `appointment.cancelled`) that trigger a webhook.
- **Payload Delivery:** Canopy sends a JSON payload to a user-defined URL via a POST request.
- **Retry Logic:** If a third-party endpoint returns a non-2xx response, Canopy implements an exponential backoff retry strategy (attempting delivery at 1m, 5m, 15m, and 1h).
- **Security:** Every webhook request includes an `X-Canopy-Signature` header (HMAC-SHA256) to allow the receiver to verify the authenticity of the payload.

**Technical Implementation:**
Webhooks are processed asynchronously using Oban (a PostgreSQL-based job queue for Elixir). This ensures that a slow third-party API does not hang the main application thread.

---

### 3.3 Workflow Automation Engine (Visual Rule Builder)
**Priority:** Low | **Status:** In Review

This feature allows administrators to create "If-This-Then-That" (IFTTT) logic for patient care workflows without writing code.

**Functional Requirements:**
- **Visual Builder:** A drag-and-drop interface (built with LiveView) where users can connect "Triggers" to "Actions."
- **Triggers:** Examples include "Patient blood pressure > 140/90" or "Appointment date is tomorrow."
- **Actions:** Examples include "Send SMS to Doctor," "Flag record for review," or "Trigger Webhook."
- **Conditional Logic:** Ability to add "Filters" (e.g., Only trigger if Patient Age > 65).

**Technical Implementation:**
Rules are stored in a JSONB column in the `automation_rules` table. The `Canopy.Automation` engine scans events in real-time and matches them against the stored JSON logic.

---

### 3.4 Notification System
**Priority:** Low | **Status:** In Progress

A multi-channel notification system to ensure critical health alerts reach the correct provider instantly.

**Functional Requirements:**
- **Channel Selection:** Ability to route messages via Email (SendGrid), SMS (Twilio), In-App (LiveView sockets), and Push (Firebase).
- **Preference Center:** Users can toggle which types of notifications they receive on which channels.
- **Priority Queueing:** "Urgent" notifications (e.g., critical lab results) bypass the standard queue to be delivered within seconds.
- **Audit Log:** Every notification sent must be logged with a timestamp and delivery status for HIPAA compliance.

**Technical Implementation:**
Implemented as a separate `Canopy.Notifications` context. It uses a strategy pattern to swap delivery providers without affecting the business logic.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Low | **Status:** Blocked

The system must handle medical imaging (DICOM) and PDF records while ensuring the platform is not compromised by malicious uploads.

**Functional Requirements:**
- **Secure Upload:** Files are uploaded to a temporary "quarantine" bucket.
- **Virus Scanning:** Integration with ClamAV or a similar scanning service to inspect files before they are moved to permanent storage.
- **CDN Distribution:** Once cleared, files are served via a signed URL through a CDN to ensure low-latency access for clinicians globally.
- **Encryption:** Files are encrypted using server-side encryption (SSE) before being written to disk.

**Technical Implementation:**
Currently blocked due to the absence of a dedicated security engineer to sign off on the ClamAV integration. Once unblocked, this will utilize an asynchronous pipeline: `Upload` $\rightarrow$ `Scan` $\rightarrow$ `Encrypt` $\rightarrow$ `Distribute`.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer <JWT>` token in the Authorization header.

### 4.1 Authentication Endpoints
**POST `/api/v1/auth/login`**
- **Description:** Authenticates user and returns a session token.
- **Request:** `{"email": "user@stratos.com", "password": "hashed_password"}`
- **Response:** `200 OK` $\rightarrow$ `{"token": "jwt_abc123", "user_id": 456}`

**POST `/api/v1/auth/logout`**
- **Description:** Invalidates the current session token.
- **Request:** `{}`
- **Response:** `204 No Content`

### 4.2 Patient Records Endpoints
**GET `/api/v1/records/{patient_id}`**
- **Description:** Retrieves the full healthcare record for a specific patient.
- **Response:** `200 OK` $\rightarrow$ `{"id": "p1", "name": "John Doe", "vitals": {...}, "history": [...]}`

**PATCH `/api/v1/records/{patient_id}`**
- **Description:** Updates specific fields in a patient record.
- **Request:** `{"vitals": {"bp": "120/80"}}`
- **Response:** `200 OK` $\rightarrow$ `{"status": "updated", "version": 4}`

### 4.3 Webhook Management Endpoints
**POST `/api/v1/webhooks`**
- **Description:** Registers a new webhook destination.
- **Request:** `{"url": "https://client.com/callback", "event": "patient.updated"}`
- **Response:** `201 Created` $\rightarrow$ `{"webhook_id": "wh_999"}`

**DELETE `/api/v1/webhooks/{webhook_id}`**
- **Description:** Removes a webhook registration.
- **Response:** `204 No Content`

### 4.4 Automation Endpoints
**GET `/api/v1/automations`**
- **Description:** Lists all active workflow rules.
- **Response:** `200 OK` $\rightarrow$ `[{"id": 1, "name": "BP Alert", "active": true}]`

**POST `/api/v1/automations/execute`**
- **Description:** Manually triggers a workflow for testing.
- **Request:** `{"rule_id": 1, "patient_id": "p123"}`
- **Response:** `202 Accepted`

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. Due to performance requirements, approximately 30% of queries bypass the Ecto ORM and use raw SQL.

### 5.1 Tables and Relationships

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `id (PK)`, `email`, `password_hash`, `role_id (FK)` | $\text{1:1}$ with `roles` | Core user accounts. |
| `roles` | `id (PK)`, `role_name`, `permissions_bitmask` | $\text{1:N}$ with `users` | RBAC role definitions. |
| `patients` | `id (PK)`, `external_id`, `dob`, `gender` | $\text{1:N}$ with `records` | Basic patient demographics. |
| `records` | `id (PK)`, `patient_id (FK)`, `data (JSONB)`, `version` | $\text{N:1}$ with `patients` | Encrypted health data. |
| `audit_logs` | `id (PK)`, `user_id (FK)`, `action`, `timestamp` | $\text{N:1}$ with `users` | HIPAA mandatory audit trail. |
| `webhooks` | `id (PK)`, `user_id (FK)`, `url`, `event_type` | $\text{N:1}$ with `users` | Third-party integration targets. |
| `webhook_logs` | `id (PK)`, `webhook_id (FK)`, `status`, `payload` | $\text{N:1}$ with `webhooks` | Delivery history. |
| `automation_rules` | `id (PK)`, `name`, `logic (JSONB)`, `is_active` | $\text{1:N}$ with `audit_logs` | Workflow definitions. |
| `notifications` | `id (PK)`, `user_id (FK)`, `channel`, `content` | $\text{N:1}$ with `users` | Messages sent to users. |
| `files` | `id (PK)`, `patient_id (FK)`, `s3_key`, `checksum` | $\text{N:1}$ with `patients` | Pointers to encrypted blobs. |

### 5.2 Critical Migration Note
**WARNING:** Because 30% of the application uses raw SQL queries for performance, any schema change to the `records` or `audit_logs` tables must be manually verified against the raw SQL strings in the codebase. Standard Ecto migrations may not catch breaks in raw SQL queries.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Canopy utilizes a Continuous Deployment (CD) pipeline. Every Pull Request (PR) that is merged into the `main` branch is automatically deployed to production.

- **Development (Local):** Developers run the full stack locally using Docker Compose (PostgreSQL, Redis).
- **Staging:** A mirror of production hosted on Fly.io. This is used for final QA and external auditor previews. Data is anonymized.
- **Production:** The live environment on Fly.io, distributed across three regions (US-East, US-West, EU-West) to ensure high availability.

### 6.2 Infrastructure Details
- **Orchestration:** Fly.io (Machines API)
- **Database:** Managed PostgreSQL with automatic backups every 6 hours.
- **Cache:** Redis for session storage and PubSub.
- **CDN:** Cloudflare for static asset delivery and DDoS protection.

### 6.3 Deployment Pipeline
1.  **GitHub Action:** Triggered on PR merge.
2.  **Build:** Compiles Elixir binaries into a Docker image.
3.  **Test:** Runs `mix test` (Unit/Integration).
4.  **Deploy:** `fly deploy` pushes the image to the production cluster.
5.  **Migration:** `mix ecto.migrate` is run as a release command.

---

## 7. TESTING STRATEGY

To maintain high reliability in a healthcare context, a three-tier testing approach is mandated.

### 7.1 Unit Testing
- **Focus:** Individual functions and module logic.
- **Tool:** ExUnit.
- **Requirement:** 80% code coverage for all `Context` modules.
- **Example:** Testing the logic that calculates if a patient's blood pressure is "Critical."

### 7.2 Integration Testing
- **Focus:** Interaction between the application and the database/external APIs.
- **Tool:** ExUnit + Mox (for mocking external services like Twilio/SendGrid).
- **Requirement:** All critical paths (Login $\rightarrow$ View Record $\rightarrow$ Update Record) must have integration tests.

### 7.3 End-to-End (E2E) Testing
- **Focus:** The user's actual experience in the browser.
- **Tool:** Wallaby or Playwright.
- **Requirement:** High-priority "Golden Paths" are tested weekly.
- **Scenario:** A clinician logging in via MFA, searching for a patient, and uploading a PDF record.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Elixir/Phoenix stack | High | High | Build a contingency plan with a fallback architecture (Rails/Postgres). Implement weekly "Pair Programming" sessions. |
| R-02 | Project sponsor rotation (Loss of executive support) | Medium | High | Assign a dedicated owner to track board-level reporting and maintain a direct line to the new sponsor. |
| R-03 | Technical debt: Raw SQL usage in ORM | High | Medium | Create a "SQL Registry" document listing all raw queries. Require manual audit for any schema change. |
| R-04 | HIPAA Compliance failure in first audit | Low | Critical | Conduct internal "mock audits" monthly. Use a checklist based on the HITRUST framework. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project termination or legal action.
- **High:** Significant delay in milestones or budget overruns.
- **Medium:** Manageable delay with minimal impact on ROI.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE

The project follows a phased approach. Dependencies are strictly managed to prevent bottlenecks.

### 9.1 Phase 1: Foundation (Current $\rightarrow$ 2026-04-15)
- **Focus:** Core infrastructure, RBAC, and basic record management.
- **Dependency:** Finalization of the RBAC model.
- **Milestone 1 (MVP Feature-Complete):** 2026-04-15. All "Critical" and "Medium" features must be operational.

### 9.2 Phase 2: Hardening & Launch (2026-04-16 $\rightarrow$ 2026-06-15)
- **Focus:** Security audits, load testing, and data migration from the 4 legacy tools.
- **Dependency:** Successful completion of MVP features.
- **Milestone 2 (Production Launch):** 2026-06-15. Platform goes live to the first 1,000 users.

### 9.3 Phase 3: Optimization & Review (2026-06-16 $\rightarrow$ 2026-08-15)
- **Focus:** Implementing "Low" priority features (Notification system, Automation engine).
- **Dependency:** Stability of the production environment.
- **Milestone 3 (Architecture Review):** 2026-08-15. Final technical sign-off by the board.

---

## 10. MEETING NOTES

*Note: These notes are extracted from the shared 200-page running document. The document remains unsearchable and is organized chronologically.*

### Meeting 1: Stack Selection & Risk Analysis
**Date:** 2023-11-02  
**Attendees:** Lev Park, Luciano Jensen, Wanda Santos, Wes Fischer  
**Discussion:**
- Lev proposed Elixir/Phoenix for the high concurrency requirements. 
- Luciano raised a concern: "None of us have actually shipped an Elixir app to production."
- Wanda questioned if LiveView would support the complex visual rule builder.
- **Decision:** The team agreed to move forward with Elixir but decided to maintain a "Fallback Plan" (Ruby on Rails) in case the learning curve prevents MVP completion.
- **Action Item:** Luciano to set up the initial Fly.io environment.

### Meeting 2: The "Raw SQL" Performance Trade-off
**Date:** 2023-12-15  
**Attendees:** Lev Park, Luciano Jensen  
**Discussion:**
- Lev noted that Ecto's generated queries for the `audit_logs` table were too slow during bulk inserts.
- Luciano suggested using `COPY` commands via raw SQL.
- **Decision:** It was decided that performance is the priority for board-level reporting. Raw SQL will be permitted for the top 30% of most-hit queries.
- **Risk:** Both acknowledged that this makes migrations dangerous. They agreed to manually check SQL strings during PR reviews.

### Meeting 3: Resource Crisis & Blocker Management
**Date:** 2024-01-10  
**Attendees:** Lev Park, Wanda Santos, Wes Fischer  
**Discussion:**
- A key team member (unnamed in notes) is on medical leave for 6 weeks.
- Wanda noted that the "File Upload" feature is now effectively blocked as the medical leave affects the only person capable of the security integration.
- Wes suggested shifting focus to the Webhook framework to maintain velocity.
- **Decision:** Shift priority to Webhooks and RBAC; put "File Upload" on hold until the member returns.

---

## 11. BUDGET BREAKDOWN

The total budget for Project Canopy is **$5,000,000+**.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $3,250,000 | Salaries for 4-person team over 3 years + benefits. |
| **Infrastructure** | 15% | $750,000 | Fly.io clusters, PostgreSQL managed hosting, Cloudflare. |
| **Security/Audit** | 10% | $500,000 | External HIPAA auditors, Penetration testing firms. |
| **Tooling/Licensing** | 5% | $250,000 | GitHub Enterprise, Slack, SendGrid, Twilio. |
| **Contingency** | 5% | $250,000 | Emergency fund for "Fallback Architecture" if Elixir fails. |

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Checklist
To pass the external audit on the first attempt, the following must be verified:
1. **Access Control:** Unique user IDs and automatic log-off.
2. **Audit Controls:** Every single read/write to the `records` table must be logged in `audit_logs`.
3. **Integrity:** Use of SHA-256 checksums for all uploaded files to ensure no tampering.
4. **Transmission Security:** All traffic must be TLS 1.3 encrypted; no plaintext HTTP.

### Appendix B: Raw SQL Registry (Sample)
Due to the technical debt mentioned in Section 5.2, the following queries are identified as "High Risk" during migrations:
- `SELECT * FROM records WHERE patient_id = $1` (Bypasses Ecto for speed).
- `INSERT INTO audit_logs (user_id, action) VALUES ...` (Bulk insert via raw SQL).
- `UPDATE patients SET last_accessed = NOW() WHERE id = $1` (Direct SQL update).
- **Migration Rule:** Any change to `records.patient_id` or `audit_logs.user_id` requires a grep of the entire `/lib` folder for these strings.