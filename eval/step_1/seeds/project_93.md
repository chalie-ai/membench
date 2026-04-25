# PROJECT SPECIFICATION: PROJECT CANOPY
**Document Version:** 1.0.4  
**Status:** Draft / Pending Technical Lead Approval  
**Date:** October 24, 2025  
**Company:** Iron Bay Technologies  
**Confidentiality:** Proprietary & Confidential (ISO 27001 Compliant)

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Canopy is a strategic initiative by Iron Bay Technologies to develop a high-performance data pipeline and analytics platform specifically tailored for the logistics and shipping industry. The platform aims to bridge the gap between raw telematics/shipping data and actionable business intelligence, allowing logistics providers to monitor fleet efficiency, cargo transit times, and operational bottlenecks in real-time.

**Business Justification**  
The impetus for Project Canopy is a direct commitment from a single Tier-1 enterprise client in the global shipping sector. This client has agreed to a contract value of $2,000,000 USD annually upon successful delivery of the MVP. This creates a massive ROI opportunity for Iron Bay Technologies, shifting the company from a service-provider model to a high-margin product vertical. Given the niche nature of logistics analytics, Canopy is positioned to capture a significant market share by solving the "last-mile data gap"—the inability of current systems to integrate disparate shipping manifests with real-time GPS and port congestion data.

**ROI Projection**  
With a lean development budget of $150,000 and an annual recurring revenue (ARR) of $2M from the anchor client, the project demonstrates a theoretical ROI of over 1,200% in Year 1. However, this is contingent on the platform meeting the strict performance and security requirements mandated by the client.

**Strategic Constraints**  
The project is operating under a "shoestring" budget of $150,000. Every expenditure is under extreme scrutiny by the finance department. To maintain agility and reduce initial overhead, the team has opted for a "deliberately simple" stack (Ruby on Rails, MySQL, Heroku). The primary challenge lies in the team's lack of familiarity with this stack and the internal dysfunction between the Project Manager (PM) and the Tech Lead, Niko Gupta. Success depends on hitting three critical milestones by December 15, 2026, while navigating a volatile internal team dynamic and significant technical debt.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Canopy is designed as a **Modular Monolith**. The decision to use Ruby on Rails (v7.1) was driven by the need for rapid prototyping and a shared codebase that allows the small team of 12 to move quickly. While the current implementation is a monolith, the codebase is structured into "bounded contexts" (e.g., `Billing`, `Analytics`, `Ingestion`, `UserManagement`) to facilitate an incremental transition to microservices as the platform scales to meet the 10,000 MAU target.

### 2.2 Component Overview
- **Application Layer:** Ruby on Rails 7.1 (API mode).
- **Data Layer:** MySQL 8.0 (Amazon RDS managed via Heroku).
- **Infrastructure:** Heroku Private Spaces (to satisfy ISO 27001 requirements).
- **Cache Layer:** Redis (for real-time collaborative state and session management).
- **Background Processing:** Sidekiq for asynchronous report generation and data ingestion.

### 2.3 ASCII Architecture Diagram
```text
[ External Data Sources ]  --> [ Heroku API Gateway ] --> [ Rails Monolith ]
(Shipping APIs/IoT)             (SSL Termination)        (Business Logic)
                                                               |
                                        -----------------------|-----------------------
                                        |                      |                      |
                                [ MySQL Database ]      [ Redis Cache ]        [ S3 Bucket ]
                                (Relational Store)      (Real-time State)      (PDF/CSVs)
                                        |                      |
                                [ Raw SQL Layer ] <--- [ Performance Bypass ]
                                (30% of Queries)
                                        |
                                [ ISO 27001 Env ] <--- [ Audit Trail Logs ]
```

### 2.4 Technical Debt Warning
A critical architectural risk is the "Performance Bypass." Due to the complexity of logistics joins, 30% of the application's queries bypass the ActiveRecord ORM in favor of Raw SQL. This has created a significant risk during migrations; any schema change must be manually audited against all raw SQL strings to prevent production outages.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing (Priority: Critical)
**Status:** In Progress | **Launch Blocker:** Yes
**Description:** 
The core value proposition for the enterprise client is the ability for multiple logistics coordinators to edit shipping manifests and route plans simultaneously. This feature requires a "Google Docs-style" experience where changes are reflected in real-time without page refreshes.

**Technical Requirements:**
- **Conflict Resolution:** The system must implement Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs). Given the Rails stack, the team will utilize ActionCable for WebSockets to broadcast changes.
- **State Management:** The current state of a shared document must be cached in Redis to ensure latency remains under 100ms for updates.
- **Locking Mechanism:** Implement optimistic locking at the database level using a `lock_version` column to prevent "lost updates" when two users save simultaneously.
- **UI/UX:** Haruki Stein (UX Researcher) has specified a "Presence Indicator" (colored avatars) showing who is currently editing which field.

**Acceptance Criteria:**
- Two users editing the same field must resolve to the last-write-wins or merged state without data loss.
- Latency from User A's keystroke to User B's screen must be < 200ms.
- System must handle up to 50 concurrent editors per manifest.

### 3.2 PDF/CSV Report Generation (Priority: High)
**Status:** Not Started
**Description:** 
Logistics managers require scheduled, high-fidelity reports for customs and regulatory compliance. These reports must aggregate data from multiple shipment cycles and be delivered via email or API.

**Technical Requirements:**
- **Generation Engine:** Use the `WickedPDF` or `Grover` gem for PDF rendering and the native Ruby `CSV` library for data exports.
- **Scheduling:** Integration with `Sidekiq-Cron` to allow users to schedule reports (e.g., "Every Monday at 08:00 UTC").
- **Storage:** Reports must be generated in a background worker, uploaded to an ISO 27001 compliant S3 bucket, and a signed URL sent to the user.
- **Data Aggregation:** Since reports involve massive datasets, these must use the Raw SQL performance bypass to avoid ActiveRecord overhead.

**Acceptance Criteria:**
- Reports must generate within 30 seconds for datasets up to 100k rows.
- Scheduled emails must trigger within 5 minutes of the scheduled time.
- PDFs must be tamper-proof and read-only.

### 3.3 Audit Trail Logging (Priority: Medium)
**Status:** Not Started
**Description:** 
For ISO 27001 certification and shipping liability, every change to a manifest or user permission must be logged in a tamper-evident storage system.

**Technical Requirements:**
- **Immutability:** Logs must be written to a "Write-Once-Read-Many" (WORM) storage or a database table where the `UPDATE` and `DELETE` permissions are revoked for the application user.
- **Hashing:** Each log entry must contain a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody to ensure no logs were deleted.
- **Fields:** Must capture `timestamp`, `user_id`, `action`, `previous_value`, `new_value`, and `ip_address`.
- **Storage:** Logs will be stored in a separate `audit_logs` table in MySQL, but archived daily to encrypted S3 cold storage.

**Acceptance Criteria:**
- Any attempt to modify a log entry must be detectable by the system.
- Search capability must allow admins to filter by `user_id` or `entity_id` with results returning in < 2 seconds.

### 3.4 Customizable Dashboard (Priority: Medium)
**Status:** In Review
**Description:** 
A drag-and-drop interface allowing users to create custom views of their shipping data using various "widgets" (e.g., Pie charts for carrier distribution, Line graphs for transit times).

**Technical Requirements:**
- **Frontend:** Implementation of `React-Grid-Layout` to handle the drag-and-drop functionality.
- **Widget Registry:** A backend registry of available widgets, each mapping to a specific API endpoint.
- **Persistence:** User dashboard configurations must be stored as JSONB in the MySQL database (`dashboard_configs` table).
- **Data Fetching:** Widgets should use asynchronous polling or WebSockets to refresh data without reloading the page.

**Acceptance Criteria:**
- Users can add/remove/resize at least 5 different widget types.
- Dashboard layouts must persist across sessions and devices.
- Loading a dashboard with 10 widgets must complete in under 1.5 seconds.

### 3.5 Customer-Facing API (Priority: Low)
**Status:** In Review
**Description:** 
A RESTful API allowing the enterprise client to integrate Canopy data into their own internal ERP systems.

**Technical Requirements:**
- **Versioning:** Use URI versioning (e.g., `/api/v1/...`).
- **Sandbox:** A separate "Sandbox" Heroku app with anonymized data for client testing.
- **Authentication:** API Key-based authentication with rotating secrets.
- **Rate Limiting:** Implement `Rack::Attack` to limit requests to 1,000 calls per hour per API key.

**Acceptance Criteria:**
- All endpoints must return standard JSON responses.
- Sandbox environment must be completely isolated from production data.
- Documentation must be provided via Swagger/OpenAPI 3.0.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require the header `Authorization: Bearer <TOKEN>` and `Content-Type: application/json`.

### 4.1 `GET /api/v1/shipments`
**Description:** Retrieve a paginated list of all shipments.
- **Query Params:** `page` (int), `per_page` (int), `status` (string).
- **Request Example:** `GET /api/v1/shipments?page=1&status=in_transit`
- **Response Example:**
```json
{
  "data": [
    { "id": "SHP-101", "origin": "Shanghai", "destination": "Long Beach", "eta": "2026-11-12" }
  ],
  "meta": { "current_page": 1, "total_pages": 10 }
}
```

### 4.2 `POST /api/v1/shipments`
**Description:** Create a new shipment record.
- **Request Body:** `{ "origin": "Rotterdam", "destination": "New York", "carrier_id": 502 }`
- **Response Example:** `201 Created`
```json
{ "id": "SHP-102", "status": "pending", "created_at": "2026-10-24T10:00:00Z" }
```

### 4.3 `PATCH /api/v1/shipments/:id`
**Description:** Update shipment details (triggers real-time collaborative sync).
- **Request Body:** `{ "status": "delivered" }`
- **Response Example:** `200 OK`
```json
{ "id": "SHP-101", "status": "delivered", "updated_at": "2026-10-24T11:00:00Z" }
```

### 4.4 `GET /api/v1/analytics/transit-times`
**Description:** Returns aggregated transit time data for dashboard widgets.
- **Response Example:**
```json
{
  "labels": ["Jan", "Feb", "Mar"],
  "datasets": [{ "label": "Avg Days", "data": [14, 12, 15] }]
}
```

### 4.5 `POST /api/v1/reports/generate`
**Description:** Trigger an immediate PDF/CSV report generation.
- **Request Body:** `{ "type": "pdf", "format": "monthly_summary", "email": "admin@client.com" }`
- **Response Example:** `202 Accepted`
```json
{ "job_id": "sidekiq_99821", "status": "queued" }
```

### 4.6 `GET /api/v1/audit/logs`
**Description:** Retrieve the tamper-evident audit trail.
- **Query Params:** `entity_id` (string), `user_id` (int).
- **Response Example:**
```json
[
  { "timestamp": "2026-10-24T09:00:00Z", "user_id": 12, "action": "UPDATE", "hash": "a1b2c3..." }
]
```

### 4.7 `GET /api/v1/users/me`
**Description:** Retrieve current authenticated user profile.
- **Response Example:**
```json
{ "id": 12, "name": "John Doe", "role": "logistics_manager", "permissions": ["read", "write"] }
```

### 4.8 `DELETE /api/v1/shipments/:id`
**Description:** Soft-delete a shipment record.
- **Response Example:** `204 No Content`

---

## 5. DATABASE SCHEMA

The database uses MySQL 8.0. Due to the performance bypass, all table changes must be vetted by Niko Gupta.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `id` | N/A | `email`, `password_digest`, `role` | User account management |
| `organizations` | `id` | N/A | `company_name`, `iso_cert_id` | Enterprise client data |
| `shipments` | `id` | `org_id`, `carrier_id` | `origin`, `destination`, `status`, `lock_version` | Core shipping data |
| `carriers` | `id` | N/A | `carrier_name`, `scac_code`, `contact_info` | Shipping carrier details |
| `manifests` | `id` | `shipment_id` | `cargo_type`, `weight`, `volume` | Detailed cargo manifests |
| `audit_logs` | `id` | `user_id` | `action`, `prev_val`, `new_val`, `prev_hash` | Tamper-evident logging |
| `dashboard_configs`| `id` | `user_id` | `layout_json` (JSONB), `theme` | Saved UI layouts |
| `reports` | `id` | `org_id` | `report_type`, `s3_url`, `scheduled_at` | PDF/CSV metadata |
| `api_keys` | `id` | `user_id` | `key_hash`, `last_used_at`, `expires_at` | API access control |
| `collaboration_sessions`| `id` | `manifest_id` | `session_token`, `active_users_count` | Real-time session tracking |

### 5.2 Relationships
- `organizations` (1) $\rightarrow$ `shipments` (N)
- `shipments` (1) $\rightarrow$ `manifests` (N)
- `users` (1) $\rightarrow$ `audit_logs` (N)
- `users` (1) $\rightarrow$ `dashboard_configs` (1)
- `carriers` (1) $\rightarrow$ `shipments` (N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Canopy utilizes a three-tier environment strategy hosted on Heroku.

1.  **Development (dev):**
    - **Purpose:** Individual feature development.
    - **Access:** All developers.
    - **Data:** Mock data generated via `faker` gem.
    - **Deployments:** Triggered on every push to `develop` branch.

2.  **Staging (staging):**
    - **Purpose:** Final QA and User Acceptance Testing (UAT).
    - **Access:** Dev team, Haruki Stein, and select client stakeholders.
    - **Data:** Anonymized production snapshot.
    - **Deployments:** Manual trigger from `develop` to `staging`.

3.  **Production (prod):**
    - **Purpose:** Live enterprise environment.
    - **Access:** Restricted to Kenji Jensen (DevOps) and Niko Gupta.
    - **Data:** Live client data (Encrypted at rest).
    - **Deployments:** Manual QA gate required. Turnaround time is 2 days.

### 6.2 ISO 27001 Compliance
To maintain the required certification, the production environment is isolated within a Heroku Private Space. All data in transit is encrypted via TLS 1.3, and database disks are encrypted using AES-256.

### 6.3 Deployment Pipeline
The deployment process is intentionally slowed to ensure stability:
1. **Merge Request:** Developer submits code to `develop`.
2. **CI Pipeline:** Automated tests (RSpec) must pass 100%.
3. **Staging Deploy:** Code is pushed to Staging.
4. **QA Gate:** Manual verification by Anouk Park (Support Engineer) and Niko Gupta.
5. **Production Deploy:** Manual deployment to Production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** RSpec.
- **Approach:** Focus on business logic in models and service objects.
- **Coverage Target:** 80% of all new code.
- **Specific Focus:** Every Raw SQL query must have a corresponding unit test to verify that it handles `NULL` values and edge cases correctly.

### 7.2 Integration Testing
- **Tool:** Capybara and FactoryBot.
- **Approach:** Test the "Happy Path" of the 5 core features. Specifically, testing the interaction between the Rails API and the MySQL database.
- **Critical Path:** The "Collaborative Editing" flow must be tested for race conditions using concurrent threads.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress.
- **Approach:** Mimic the user journey of a Logistics Manager from login $\rightarrow$ dashboard $\rightarrow$ shipment edit $\rightarrow$ report generation.
- **Environment:** Performed exclusively in the Staging environment before any Production release.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Ruby/Rails/Heroku | High | High | Hire a specialized Rails contractor for a 3-month mentorship/code review period. | Niko Gupta |
| R-02 | Key Architect leaving in 3 months | Medium | High | Assign a dedicated owner to document all architectural decisions and transition knowledge. | Niko Gupta |
| R-03 | PM/Tech Lead communication breakdown | High | Medium | Establish a strictly documented "Decision Log" to bypass verbal disagreements. | Project Lead |
| R-04 | Raw SQL queries break during migrations | Medium | High | Implement a mandatory "Migration Audit" step where all raw SQL is grep-searched for changed columns. | Kenji Jensen |
| R-05 | Budget overrun ($150k limit) | Low | High | Monthly budget reviews; use of Heroku "Standard" dynos instead of "Performance" where possible. | Finance Dept |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases
- **Phase 1: Foundation (Now – Aug 2026):** Focus on the monolith setup, basic shipment CRUD, and the critical Collaborative Editing feature.
- **Phase 2: Hardening (Aug 2026 – Oct 2026):** Security audits, ISO 27001 compliance checks, and the Audit Trail implementation.
- **Phase 3: Feature Completion (Oct 2026 – Dec 2026):** Dashboard widgets, Report generation, and API Sandbox.

### 9.2 Key Milestones
- **Milestone 1: Internal Alpha Release (2026-08-15)**
  - *Deliverables:* Collaborative editing functional, Basic shipment tracking, User authentication.
  - *Dependency:* Resolve design disagreement between product and engineering.
- **Milestone 2: Security Audit Passed (2026-10-15)**
  - *Deliverables:* Audit trail logs active, ISO 27001 environment verified, Penetration test complete.
  - *Dependency:* Completion of the Audit Trail feature.
- **Milestone 3: MVP Feature-Complete (2026-12-15)**
  - *Deliverables:* PDF/CSV reports, Customizable Dashboard, API v1.
  - *Dependency:* Passing of the Security Audit.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per team culture, no formal minutes are kept. The following are transcribed summaries of critical decision threads from the `#canopy-dev` Slack channel.*

### Meeting 1: The "Architecture Clash" (2025-11-02)
**Participants:** Niko (Tech Lead), PM (Product Manager)
**Discussion:** PM insisted on a microservices architecture from Day 1 to "be future-proof." Niko argued that with 12 people and a $150k budget, the overhead of managing 10+ services would kill the project.
**Decision:** (Thread ended in stalemate) Eventually agreed to a "Modular Monolith" using Ruby on Rails. PM reluctantly agreed as long as the code is organized into "bounded contexts."
**Outcome:** Architecture locked as Rails Monolith.

### Meeting 2: Performance vs. Clean Code (2025-12-15)
**Participants:** Niko, Kenji, Anouk
**Discussion:** Kenji pointed out that ActiveRecord was causing N+1 query issues on the shipment manifest view, resulting in 4-second load times.
**Decision:** Niko authorized the "Performance Bypass." The team will write raw SQL for complex analytics queries.
**Outcome:** 30% of the codebase now uses Raw SQL; documented as a primary technical debt risk.

### Meeting 3: The Budget Crisis (2026-01-20)
**Participants:** Niko, PM, Finance Rep
**Discussion:** Finance noted that the current burn rate on Heroku Private Spaces and high-tier RDS instances was exceeding the $150k total budget projection.
**Decision:** The team will downgrade the Dev and Staging environments to "Standard" dynos. Only Production will remain on the ISO-compliant Private Space.
**Outcome:** Budget tightened; manual QA gate reinforced to prevent costly production rollbacks.

---

## 11. BUDGET BREAKDOWN

**Total Project Budget:** $150,000.00 USD

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel (Contractor)** | $65,000 | Special Rails expert to mitigate "Bus Factor" and lack of stack experience. |
| **Infrastructure (Heroku/AWS)** | $40,000 | Includes Private Space for ISO 27001 and RDS MySQL instances. |
| **Software Tools/Licenses** | $15,000 | IDEs, CI/CD tools, Security scanning software (Snyk/SonarQube). |
| **Security Audit (Third Party)** | $20,000 | External ISO 27001 certification and penetration testing. |
| **Contingency Fund** | $10,000 | Reserved for emergency scaling or critical bug fixes. |
| **Total** | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: Collaborative Editing Conflict Resolution Logic
The system uses a hybrid approach for the critical "Real-time Editing" feature:
1. **Client Side:** Each client maintains a local copy of the document and a "pending changes" queue.
2. **Server Side:** The Rails server acts as the single source of truth. When a change is received via ActionCable, the server validates the `lock_version`.
3. **Resolution:** If `current_version == lock_version`, the change is accepted and broadcasted. If `current_version > lock_version`, the server sends a `CONFLICT` signal, and the client is prompted to merge or overwrite.

### Appendix B: Raw SQL Migration Protocol
To prevent the "Performance Bypass" from breaking the system, the following protocol is mandatory:
1. **Search:** Before running `rake db:migrate`, the developer must run `grep -r "SELECT" app/services/` to find all raw SQL queries.
2. **Impact Analysis:** Identify any queries referencing columns being renamed or dropped.
3. **Manual Update:** Manually update the raw SQL string to match the new schema.
4. **Verification:** Run the specific unit tests for those queries in the Staging environment before proceeding to Production.