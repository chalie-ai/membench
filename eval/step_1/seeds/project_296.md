# PROJECT SPECIFICATION: PROJECT GANTRY
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Last Updated:** October 24, 2025  
**Project Lead:** Viktor Fischer (CTO)  
**Company:** Hearthstone Software  

---

## 1. EXECUTIVE SUMMARY

### Business Justification
Project Gantry represents a strategic pivot for Hearthstone Software, marking the establishment of a new product vertical specifically tailored for the education sector. The project is catalyzed by a high-value partnership with a single enterprise client—a multi-state educational consortium—that has committed to an annual recurring revenue (ARR) of $2,000,000. 

The education market is currently fragmented, with institutions struggling to unify disparate data streams from Learning Management Systems (LMS), student information systems, and administrative portals. Gantry is designed to solve this by providing a robust data pipeline and analytics platform that allows these institutions to automate complex administrative workflows and gain real-time insights into student performance and operational efficiency.

The decision to build Gantry is not merely a pursuit of revenue, but a tactical move to enter a vertical with high switching costs and long-term stability. By delivering a specialized tool for this enterprise client, Hearthstone Software creates a "beachhead" that can be leveraged to capture the broader K-12 and Higher Ed market.

### ROI Projection and Financial Constraints
Despite the $2M annual payout from the client, the internal development budget for Gantry is strictly capped at $150,000. This "shoestring" budget is a conscious decision by executive leadership to maximize the profit margin of the new vertical. Every dollar is scrutinized, and the project is operated under a lean methodology.

**Projected ROI (Year 1):**
*   **Gross Revenue:** $2,000,000
*   **Development Cost:** ($150,000)
*   **Infrastructure/Heroku Overhead (Est):** ($45,000)
*   **Estimated Net Profit:** $1,805,000
*   **ROI Percentage:** ~1,203%

The risk associated with this low budget is significant, as it limits the ability to outsource tasks or purchase expensive third-party licenses. However, the project leverages a high-trust, low-ceremony team of 20+ people across three departments (Engineering, Product/UX, and Support), utilizing internal talent to keep costs low. The success of Gantry hinges on the ability to deliver a SOC 2 Type II compliant system using a simplified technical stack, avoiding "over-engineering" in favor of rapid delivery and stability.

---

## 2. TECHNICAL ARCHITECTURE

### Architectural Philosophy
Gantry is built on a "Simplicity First" mandate. To minimize operational overhead and maximize developer velocity, the project utilizes a Ruby on Rails monolith. While the industry trend leans toward microservices, Gantry deliberately avoids this complexity to stay within budget and maintain a small team footprint.

### The Stack
*   **Language/Framework:** Ruby 3.3.0 / Rails 7.1 (Monolith)
*   **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL addons)
*   **Hosting:** Heroku (Private Spaces for SOC 2 compliance)
*   **Cache/Queue:** Redis (via Heroku Data for Redis)
*   **Background Processing:** Sidekiq

### CQRS and Event Sourcing
For audit-critical domains (specifically financial records and student grade changes), Gantry implements Command Query Responsibility Segregation (CQRS) with event sourcing. Instead of storing only the current state, every change is stored as an immutable event in an `event_store` table.

**The Flow:**
1.  **Command:** A user requests a change (e.g., "Update Grade").
2.  **Event:** A `GradeChanged` event is appended to the event store.
3.  **Projection:** A background worker updates the "Read Model" (the standard MySQL table) to reflect the current state.
4.  **Audit:** The event store provides a tamper-evident history for SOC 2 compliance.

### System Diagram (ASCII Description)
```text
[ User Browser/Client ] 
       |
       v
[ Heroku Load Balancer ]
       |
       v
[ Rails Monolith (Web Dynos) ] <---> [ Redis (Sidekiq/Caching) ]
       |                                   |
       +------------------+               |
       |                  |               |
[ MySQL (Read Model) ] [ MySQL (Event Store) ] <--- [ Event Projection Worker ]
       ^                  ^
       |                  |
[ SOC 2 Encrypted Storage (AWS S3) ] <--- [ Tamper-Evident Logs ]
```

The architecture ensures that the "Read Model" provides high-performance queries for the analytics dashboard, while the "Event Store" guarantees a perfect audit trail of every data mutation.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### Feature 1: Workflow Automation Engine with Visual Rule Builder
*   **Priority:** High
*   **Status:** Not Started
*   **Description:** A system allowing non-technical administrators to create "If-This-Then-That" (IFTTT) logic for student data. For example: "If a student's average drops below 70% AND attendance is < 80%, then send an alert to the academic advisor."
*   **Detailed Logic:**
    *   **Trigger Layer:** Events are emitted from the system (e.g., `student.grade_updated`).
    *   **Condition Layer:** A series of boolean checks using a DSL (Domain Specific Language).
    *   **Action Layer:** A predefined set of outputs (Email, SMS, API Webhook, Database Update).
*   **Visual Rule Builder:** A drag-and-drop interface using React Flow. Users can map triggers to actions visually. The frontend will serialize these maps into a JSON schema that the Rails backend interprets.
*   **Execution:** The engine will run asynchronously via Sidekiq to ensure that complex rules do not block the main request-response cycle. Each rule execution is logged for audit purposes.

### Feature 2: Multi-tenant Data Isolation with Shared Infrastructure
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Blocked (Dependent on External Deliverable)
*   **Description:** Gantry must support multiple educational institutions on a single set of Heroku dynos and a single MySQL instance while ensuring no data leakage between tenants.
*   **Implementation Strategy:**
    *   **Row-Level Security:** Every table (except global config) contains a `tenant_id`.
    *   **Scope Enforcement:** A mandatory `default_scope` is applied to all ActiveRecord models to ensure `where(tenant_id: current_tenant_id)` is appended to every query.
    *   **Tenant Context:** The `Current` object in Rails will hold the `tenant_id` for the duration of the request, extracted from the subdomain (e.g., `university-a.gantry.com`).
*   **Isolation Requirements:** Since this is a launch blocker, the team must implement "Hard Isolation" for the event store. Any failure in the `tenant_id` check must trigger a 500 error rather than returning null or cross-tenant data.

### Feature 3: Offline-First Mode with Background Sync
*   **Priority:** Low (Nice to Have)
*   **Status:** In Review
*   **Description:** Ability for administrators in low-connectivity areas (e.g., rural schools) to input data without an active internet connection.
*   **Technical Approach:**
    *   **Client-Side Storage:** Use IndexedDB via Dexie.js to store pending mutations.
    *   **Sync Queue:** A local queue of operations (Create/Update/Delete) timestamped with a UUID.
    *   **Reconciliation:** Upon reconnection, Gantry uses a "Last-Write-Wins" (LWW) strategy based on the client-side timestamp.
*   **Constraints:** Only specific "lightweight" forms are eligible for offline mode. Large analytics reports require a live connection.

### Feature 4: Audit Trail Logging with Tamper-Evident Storage
*   **Priority:** Medium
*   **Status:** Blocked
*   **Description:** A secure log of all administrative actions to satisfy SOC 2 Type II requirements.
*   **Implementation:**
    *   **Event Sourcing:** Every write operation creates a record in the `audit_logs` table.
    *   **Hashing:** Each single log entry contains a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody.
    *   **External Archiving:** Every 24 hours, the chain is signed with a private key and uploaded to a write-once-read-many (WORM) S3 bucket.
*   **Verification:** An internal tool will periodically re-calculate the hashes to ensure no records have been deleted or modified by a database administrator.

### Feature 5: Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** Medium
*   **Status:** In Design
*   **Description:** Enhanced security for administrative accounts, moving beyond passwords to MFA.
*   **Supported Methods:**
    *   **TOTP:** Time-based One-Time Passwords via Google Authenticator or Authy.
    *   **WebAuthn:** Support for hardware keys (YubiKey, Titan Security Key) using the FIDO2 standard.
*   **UX Flow:** During the login process, if 2FA is enabled, the user is redirected to a `/auth/challenge` page. For hardware keys, the browser's `navigator.credentials.get()` API is invoked.
*   **Recovery:** Provision of 10 one-time-use recovery codes stored as salted hashes in the database.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and return JSON. Authentication is handled via Bearer Tokens in the header.

### 1. `POST /api/v1/workflows`
*   **Description:** Create a new automation rule.
*   **Request Body:**
    ```json
    {
      "name": "Low Grade Alert",
      "trigger": "grade_change",
      "conditions": [{"field": "score", "operator": "lt", "value": 70}],
      "action": "email_advisor"
    }
    ```
*   **Response (201 Created):**
    ```json
    { "id": "wf_9982", "status": "active", "created_at": "2026-01-10T10:00:00Z" }
    ```

### 2. `GET /api/v1/tenants/settings`
*   **Description:** Retrieve configuration for the current tenant.
*   **Response (200 OK):**
    ```json
    { "tenant_id": "t_441", "institution_name": "West Valley High", "plan": "Enterprise" }
    ```

### 3. `GET /api/v1/audit_logs`
*   **Description:** Retrieve a paginated list of audit events.
*   **Query Params:** `page=1&per_page=50`
*   **Response (200 OK):**
    ```json
    { "logs": [{"id": 101, "event": "user_login", "user_id": 5, "timestamp": "..."}], "meta": {"total": 1000} }
    ```

### 4. `POST /api/v1/sync/batch`
*   **Description:** Upload offline changes in a single batch.
*   **Request Body:**
    ```json
    { "changes": [{"action": "update", "table": "students", "id": 45, "data": {"name": "John Doe"}}] }
    ```
*   **Response (200 OK):**
    ```json
    { "synced_count": 1, "conflicts": [] }
    ```

### 5. `POST /api/v1/auth/2fa/enable`
*   **Description:** Initialize 2FA setup.
*   **Response (200 OK):**
    ```json
    { "secret": "KJSDFL34SDF", "qr_code_url": "https://gantry.com/qr/..." }
    ```

### 6. `POST /api/v1/auth/2fa/verify`
*   **Description:** Verify the 2FA token to complete setup.
*   **Request Body:** `{ "code": "123456" }`
*   **Response (200 OK):** `{ "status": "verified" }`

### 7. `GET /api/v1/analytics/student_performance`
*   **Description:** Get aggregated performance data.
*   **Query Params:** `course_id=123`
*   **Response (200 OK):**
    ```json
    { "average_score": 82.4, "fail_rate": "12%", "trend": "improving" }
    ```

### 8. `DELETE /api/v1/workflows/:id`
*   **Description:** Remove an automation rule.
*   **Response (204 No Content):** `Empty Body`

---

## 5. DATABASE SCHEMA

Gantry utilizes a MySQL 8.0 database. All tables include `created_at` and `updated_at` timestamps.

### Tables and Relationships

1.  **`tenants`**
    *   `id` (UUID, PK)
    *   `name` (VARCHAR)
    *   `subdomain` (VARCHAR, Unique Index)
    *   `soc2_compliant` (BOOLEAN)
    *   *Relationship: One-to-Many with Users, Workflows.*

2.  **`users`**
    *   `id` (INT, PK)
    *   `tenant_id` (UUID, FK)
    *   `email` (VARCHAR, Unique)
    *   `password_digest` (VARCHAR)
    *   `mfa_enabled` (BOOLEAN)
    *   `mfa_secret` (VARCHAR, Encrypted)
    *   *Relationship: Belongs to Tenant.*

3.  **`students`**
    *   `id` (INT, PK)
    *   `tenant_id` (UUID, FK)
    *   `external_id` (VARCHAR) - ID from the external LMS.
    *   `first_name` (VARCHAR)
    *   `last_name` (VARCHAR)
    *   `email` (VARCHAR)

4.  **`grades`**
    *   `id` (INT, PK)
    *   `student_id` (INT, FK)
    *   `tenant_id` (UUID, FK)
    *   `score` (DECIMAL)
    *   `course_id` (INT)
    *   *Relationship: Belongs to Student and Tenant.*

5.  **`event_store` (The Heart of CQRS)**
    *   `id` (BIGINT, PK)
    *   `tenant_id` (UUID, FK)
    *   `aggregate_id` (VARCHAR) - The ID of the object being changed.
    *   `event_type` (VARCHAR) - e.g., "GradeUpdated".
    *   `payload` (JSON) - The delta of the change.
    *   `version` (INT) - Sequence number for the aggregate.
    *   `created_at` (TIMESTAMP)

6.  **`audit_logs`**
    *   `id` (BIGINT, PK)
    *   `user_id` (INT, FK)
    *   `action` (VARCHAR)
    *   `entity_type` (VARCHAR)
    *   `entity_id` (INT)
    *   `previous_hash` (VARCHAR(64)) - For tamper evidence.
    *   `current_hash` (VARCHAR(64))

7.  **`workflows`**
    *   `id` (UUID, PK)
    *   `tenant_id` (UUID, FK)
    *   `name` (VARCHAR)
    *   `definition` (JSON) - Stores the triggers and actions.
    *   `is_active` (BOOLEAN)

8.  **`workflow_executions`**
    *   `id` (BIGINT, PK)
    *   `workflow_id` (UUID, FK)
    *   `status` (ENUM: pending, success, failed)
    *   `error_message` (TEXT)

9.  **`mfa_recovery_codes`**
    *   `id` (INT, PK)
    *   `user_id` (INT, FK)
    *   `code_hash` (VARCHAR)
    *   `used_at` (TIMESTAMP)

10. **`sync_sessions`**
    *   `id` (UUID, PK)
    *   `user_id` (INT, FK)
    *   `device_id` (VARCHAR)
    *   `last_synced_at` (TIMESTAMP)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### Environment Strategy
Gantry utilizes a three-tier environment strategy hosted on Heroku to ensure stability and a rigorous promotion path.

**1. Development (Dev)**
*   **Purpose:** Sandbox for developers to iterate on features.
*   **Config:** Shared dynos, small MySQL instance.
*   **Deployment:** Automatic deploy on every push to the `develop` branch.
*   **Data:** Mock data only; no real client data is ever permitted in Dev.

**2. Staging (Staging)**
*   **Purpose:** Pre-production validation and QA.
*   **Config:** Mirrored to Production specs (Private Space).
*   **Deployment:** Deployed once per week as part of the release train.
*   **Data:** Anonymized production snapshots for realistic performance testing.

**3. Production (Prod)**
*   **Purpose:** Live client environment.
*   **Config:** High-availability dynos, redundant MySQL clusters, encrypted S3 buckets.
*   **Deployment:** Strict "Weekly Release Train." No hotfixes are permitted outside the train unless there is a total system outage.
*   **Security:** SOC 2 Type II compliant environment.

### Release Train Process
*   **Cut-off:** Every Thursday at 12:00 PM UTC.
*   **Testing:** All features must be merged into the `release` branch and pass the full CI suite.
*   **Deployment:** Friday at 10:00 AM UTC.
*   **Rollback:** If critical bugs are found during the first 4 hours, the entire release is reverted to the previous stable version.

### Infrastructure Constraints
Due to the $150k budget, Gantry avoids expensive managed services like Snowflake or Datadog. We rely on Heroku's native logging and MySQL's built-in indexing for performance. The primary infrastructure cost is the Heroku Private Space required for SOC 2 compliance.

---

## 7. TESTING STRATEGY

### Unit Testing (RSpec)
*   **Coverage Target:** 80% across all models and services.
*   **Approach:** Isolated tests using FactoryBot and Mocking.
*   **Focus:** Validation logic, CQRS event projections, and the Workflow Engine's DSL interpreter.

### Integration Testing (Request Specs)
*   **Approach:** Test API endpoints from the request layer down to the database.
*   **Focus:** Multi-tenant isolation. Every integration test must verify that a user from Tenant A cannot access data from Tenant B.
*   **Tooling:** RSpec Request Specs.

### End-to-End (E2E) Testing (Playwright)
*   **Approach:** Headless browser tests simulating critical user journeys.
*   **Key Journeys:**
    1.  User logs in $\rightarrow$ sets up 2FA $\rightarrow$ creates a workflow $\rightarrow$ verifies a trigger works.
    2.  User enters offline mode $\rightarrow$ makes a change $\rightarrow$ reconnects $\rightarrow$ verifies sync.
*   **Execution:** Run on the Staging environment before every Friday release.

### Performance Testing
*   **Benchmark:** The system must handle 1,000 concurrent users per tenant without response times exceeding 200ms for read operations.
*   **Tooling:** Apache JMeter.
*   **Target Date:** Milestone 3 (2026-08-15).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key Architect leaving in 3 months | High | Critical | Document all design patterns immediately. Build a "Fallback Architecture" that simplifies CQRS if the replacement hire is less experienced. |
| **R2** | Budget cut by 30% in next quarter | Medium | High | Identify "nice-to-have" features (e.g., Offline Mode) for immediate removal. Document workarounds to reduce Heroku costs. |
| **R3** | CI Pipeline bottleneck (45 min) | Certain | Medium | Prioritize parallelization of RSpec tests using the `parallel_tests` gem. Split the pipeline into "Fast" and "Slow" suites. |
| **R4** | Dependency delay (3 weeks behind) | High | Medium | Use "Contract Testing." Create a mock API of the missing deliverable so development can continue without the live dependency. |
| **R5** | SOC 2 Audit Failure | Low | Critical | Weekly internal audits of the `audit_logs` chain. Hire a third-party pre-assessment consultant using the contingency budget. |

### Probability/Impact Matrix
*   **Critical:** Immediate project failure or loss of $2M contract.
*   **High:** Major feature delay or budget exhaustion.
*   **Medium:** Developer productivity loss or performance degradation.
*   **Low:** Minor UX inconvenience.

---

## 9. TIMELINE AND PHASES

### Phase 1: Foundation (Oct 2025 - Jan 2026)
*   **Focus:** Multi-tenancy, Database Schema, SOC 2 Setup.
*   **Key Dependency:** Completion of the external deliverable (currently 3 weeks behind).
*   **Deliverables:** Basic Rails monolith, Tenant isolation logic, Heroku Private Space.

### Phase 2: Core Engine (Feb 2026 - Apr 2026)
*   **Focus:** Workflow Automation Engine, Event Sourcing.
*   **Milestone 1:** **Stakeholder Demo and Sign-off (2026-04-15)**.
*   **Deliverables:** Visual Rule Builder, Audit Trail, basic Analytics Dashboard.

### Phase 3: Hardening (Apr 2026 - Jun 2026)
*   **Focus:** 2FA, Security Audit, Performance Tuning.
*   **Milestone 2:** **Production Launch (2026-06-15)**.
*   **Deliverables:** Hardware key support, SOC 2 certification, Production deployment.

### Phase 4: Optimization (Jun 2026 - Aug 2026)
*   **Focus:** Offline Mode, Scalability, Benchmarking.
*   **Milestone 3:** **Performance Benchmarks Met (2026-08-15)**.
*   **Deliverables:** Background sync implementation, Load test reports.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project culture, no formal minutes are kept. The following are synthesized from Slack threads in the `#gantry-dev` channel.*

### Thread 1: On Multi-Tenancy (2025-11-12)
**Viktor Fischer:** "Everyone, we can't afford a separate DB per tenant. The budget is too tight. We go with shared infra, but I want a hard lock on `tenant_id`. If someone forgets to scope a query, the app should crash, not leak data."
**Tomas Stein:** "Agreed. I'll implement a `TenantGuard` module in the ApplicationController. If `current_tenant` is nil, it's an automatic 403."
**Farid Stein:** "Will this affect the URL structure? I'm designing the dashboard now."
**Viktor Fischer:** "Yes, subdomains are the way. `institution.gantry.com`. Make sure the UX handles the transition between the global login and the tenant-specific dashboard."
**Decision:** Use subdomain-based tenant identification with a mandatory `default_scope` on all models.

### Thread 2: The CI Pipeline Crisis (2025-12-05)
**Kian Moreau:** "The CI pipeline is taking 45 minutes. I can't even push a typo fix without losing my whole morning. We need to fix this."
**Tomas Stein:** "It's the integration tests. They're hitting the DB sequentially. We don't have the budget for more CI runners."
**Viktor Fischer:** "Fine. Tomas, spend this Friday optimizing. I don't care if we miss a feature goal this week. We can't move at this speed. Parallelize the RSpec suite."
**Decision:** Immediate pivot to parallelize CI tests. Tomas Stein assigned to lead optimization.

### Thread 3: Architect Departure Contingency (2026-01-20)
**Viktor Fischer:** "The lead architect is leaving in 3 months. We're in a precarious spot. We need to move the 'brain' of the system into the docs now."
**Tomas Stein:** "I'm worried about the CQRS implementation. It's the most complex part. If we lose the architect, we might not be able to maintain the event store."
**Viktor Fischer:** "Here's the plan: we document the event projections in detail. If the replacement hire can't handle CQRS, we have a fallback plan to move back to a standard CRUD model for non-critical tables. We trade audit depth for maintainability if we have to."
**Decision:** Document all event-sourcing logic immediately; create a "Simplified CRUD" fallback plan for non-audit-critical domains.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Internal Labor (Allocated) | $90,000 | Distributed across 3 departments. |
| **Infrastructure** | Heroku Private Space & Add-ons | $35,000 | Includes MySQL, Redis, and SOC 2 compliant environment. |
| **Tools** | Software Licenses (GitHub, Slack, etc.) | $10,000 | Minimal set; utilizing existing company licenses where possible. |
| **Contingency** | Emergency Fund | $15,000 | Reserved for SOC 2 audit fees or urgent hardware needs. |
| **TOTAL** | | **$150,000** | |

**Financial Constraint Note:** Since the budget is "shoestring," no external contractors are allowed. All work must be performed by the 20+ internal staff. Any spending over $500 requires direct approval from Viktor Fischer via Slack.

---

## 12. APPENDICES

### Appendix A: SOC 2 Type II Compliance Checklist
To achieve certification before the June 15th launch, the following technical controls must be verified:
1.  **Access Control:** All production access is logged. No developer has direct DB access in Prod (use Heroku CLI with limited roles).
2.  **Encryption:** Data at rest must be encrypted using AES-256. Data in transit must use TLS 1.3.
3.  **Auditability:** The `audit_logs` table must be immutable. Any attempt to modify a log must be detectable via the hash-chain verification tool.
4.  **Change Management:** The "Weekly Release Train" serves as the formal change management process. All changes must be linked to a Jira ticket and a peer-reviewed PR.

### Appendix B: Event Sourcing Logic (Technical Detail)
For the `grades` domain, the state is never updated directly. 
*   **Command:** `UpdateGrade(student_id: 10, new_score: 85)`
*   **Event Produced:** `GradeChangedEvent(student_id: 10, old_score: 70, new_score: 85, timestamp: T1)`
*   **Projection Logic:**
    ```ruby
    def apply(event)
      student_grade = Grade.find_by(student_id: event.student_id)
      student_grade.update!(score: event.new_score)
    end
    ```
*   **Reconstruction:** To find the state of a grade at any point in time, Gantry replays the event stream for that `aggregate_id` from $T=0$ up to the desired timestamp. This ensures a mathematically provable audit trail for educational compliance.