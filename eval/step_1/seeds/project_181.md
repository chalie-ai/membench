# PROJECT SPECIFICATION DOCUMENT: PROJECT SENTINEL (v1.0.4)
**Company:** Bellweather Technologies  
**Project Code:** SENTINEL-2024-RD  
**Status:** Active / R&D  
**Date:** October 26, 2023  
**Classification:** Confidential / Proprietary  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Sentinel is a moonshot R&D initiative spearheaded by Bellweather Technologies, designed to disrupt the intersection of healthcare records management and legal services. While traditionally, healthcare records platforms focus on clinical outcomes, Sentinel is engineered specifically for legal professionals—attorneys, paralegals, and insurance adjusters—who require an immutable, high-fidelity audit trail of medical history for litigation, compliance, and disability claims.

**Business Justification**  
The legal services industry currently suffers from "document fragmentation," where medical records are stored as unstructured PDFs or siloed in various EHR (Electronic Health Record) systems. This leads to massive inefficiencies in discovery phases of litigation. Sentinel aims to centralize this data into a structured, queryable platform that ensures data integrity and legal admissibility. By providing a single source of truth, Bellweather Technologies positions itself as the primary infrastructure layer for medical-legal evidence.

**ROI Projection and Strategic Value**  
As a moonshot project, the immediate Return on Investment (ROI) is characterized by high uncertainty. The budget is lean ($150,000), reflecting the experimental nature of the product. However, the executive sponsorship is strong, as a successful launch would open a blue-ocean market. 

The financial target is aggressive: **$500,000 in attributed new revenue within the first 12 months of launch**. This revenue is projected to stem from three primary streams:
1. **SaaS Subscription Fees:** Tiered pricing based on the volume of patient records managed.
2. **Integration Fees:** One-time setup costs for linking Sentinel to existing legal case management software.
3. **API Monetization:** Charging third-party legal researchers for anonymized, aggregated healthcare trend data.

While the initial capital expenditure is low, the long-term value lies in the proprietary data ingestion engine and the SOC 2 Type II compliant infrastructure, which create a high barrier to entry for competitors. Failure to meet the $500K target will result in a pivot toward a "white-label" API service for larger legal firms.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Sentinel utilizes a modern, highly concurrent stack centered around the Elixir language and the Phoenix framework. The choice of Elixir/Phoenix is critical to handle the real-time nature of medical record synchronization and the high-concurrency requirements of legal discovery workflows.

**The Stack:**
- **Backend:** Elixir / Phoenix 1.7 (OTP 25)
- **Frontend:** Phoenix LiveView (for real-time state management without heavy JS frameworks)
- **Primary Database:** PostgreSQL 15 (Relational storage for records and users)
- **Event Stream:** Apache Kafka (Event-driven communication between microservices)
- **Deployment:** Fly.io (Global distribution and rapid scaling)
- **Feature Management:** LaunchDarkly (Granular control over canary releases)

### 2.2 Architectural Pattern: Event-Driven Microservices
Sentinel is not a monolith. It is decomposed into several specialized microservices to ensure that a failure in the "Analytics" module does not crash the "Authentication" or "Data Ingestion" modules. Communication occurs asynchronously via Kafka topics.

**ASCII Architecture Diagram Description:**
```text
[ Client Browser ] <--- WebSocket (LiveView) ---> [ Phoenix Gateway ]
                                                          |
                                                          v
                                               [ Kafka Event Bus (Topic: record_updates) ]
                                               /                  |                  \
                                              v                   v                   v
                                    [ Auth Service ]    [ Record Service ]    [ Analytics Service ]
                                           |                      |                      |
                                           v                      v                      v
                                    [ PostgreSQL ] <---------- [ PostgreSQL ] <---------- [ PostgreSQL ]
                                    (User DB)                  (Records DB)             (Stats DB)
                                           ^                      ^                      ^
                                           |                      |                      |
                                           +----------------------+----------------------+
                                                          |
                                                   [ Fly.io Edge ]
                                                          |
                                                   [ LaunchDarkly Flags ]
```

### 2.3 Data Flow Logic
When a legal professional uploads a medical record, the following sequence occurs:
1. The **Phoenix Gateway** receives the binary via a multipart request.
2. The file is streamed to an S3-compatible bucket, and a `FILE_UPLOADED` event is pushed to Kafka.
3. The **Record Service** consumes this event, parses the metadata, and writes it to the Records DB.
4. The **Analytics Service** consumes the event to update usage quotas and rate-limit counters.
5. The **LiveView** frontend updates the user's dashboard in real-time via a PubSub message, notifying them that the record is "Processed."

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** High | **Status:** Complete | **Version:** v1.0.0
*   **Description:** The dashboard is the central hub for legal professionals to monitor their active cases and patient record statuses. It allows users to personalize their workspace by adding, removing, and rearranging widgets.
*   **Functional Specifications:**
    *   **Widget Library:** Users can select from a library of widgets including "Active Cases," "Pending Record Requests," "Recent Activity Feed," and "Storage Quota Meter."
    *   **Drag-and-Drop Engine:** Implementation via a combination of Phoenix LiveView and a lightweight JS library (SortableJS). The layout state is persisted as a JSON blob in the PostgreSQL `user_preferences` table.
    *   **Real-time Updates:** Widgets utilize Phoenix PubSub. For example, when a record is approved, the "Pending Requests" widget decrements its count without a page refresh.
    *   **Responsiveness:** The grid system is based on a 12-column layout, ensuring the dashboard is usable on both desktop and tablets.
*   **User Story:** *As a Lead Attorney, I want to see my most urgent pending records on the left and my overall case volume on the right so I can prioritize my morning review.*

### 3.2 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** Medium | **Status:** In Review | **Version:** v1.1.0
*   **Description:** A robust security layer to ensure that sensitive healthcare data is only accessible to authorized personnel.
*   **Functional Specifications:**
    *   **Identity Provider:** Custom implementation using `bcrypt` for password hashing and JWTs for session management.
    *   **Role Hierarchy:** 
        *   *SuperAdmin:* Full system access, budget management, and global settings.
        *   *FirmAdmin:* Management of users within their specific legal firm.
        *   *Associate:* Access to assigned cases only.
        *   *Auditor:* Read-only access to all records for compliance checks.
    *   **Session Management:** Sliding window expiration (2 hours of inactivity) and mandatory MFA (Multi-Factor Authentication) via TOTP for any user with Admin privileges.
    *   **Audit Logging:** Every RBAC change or access attempt to a sensitive record is logged into the `audit_logs` table with a timestamp and IP address.
*   **User Story:** *As a FirmAdmin, I need to restrict new paralegals to only see the cases they are assigned to, preventing them from viewing high-profile litigation records.*

### 3.3 Workflow Automation Engine with Visual Rule Builder
*   **Priority:** Medium | **Status:** In Design | **Version:** v1.2.0
*   **Description:** An automation tool that allows users to create "If-This-Then-That" (IFTTT) style rules for record processing.
*   **Functional Specifications:**
    *   **Visual Builder:** A node-based UI where users can drag "Triggers" and "Actions." (e.g., Trigger: `Record Uploaded` $\rightarrow$ Action: `Notify Lead Attorney`).
    *   **Rule Engine:** The backend will implement a domain-specific language (DSL) that evaluates conditions against incoming Kafka events.
    *   **Supported Triggers:** `Upload Complete`, `Audit Failure`, `Date Threshold Reached`, `Case Status Changed`.
    *   **Supported Actions:** `Email Notification`, `Move to Folder`, `Trigger API Call`, `Flag for Manual Review`.
    *   **Validation:** The system must prevent circular dependencies (infinite loops) in rule definitions.
*   **User Story:** *As a Case Manager, I want to automatically flag any medical record that is more than 5 years old for a secondary review to ensure it meets the statute of limitations.*

### 3.4 API Rate Limiting and Usage Analytics
*   **Priority:** Medium | **Status:** Not Started | **Version:** v1.3.0
*   **Description:** A system to protect the platform from abuse and provide data on how the API is being used by third-party legal software.
*   **Functional Specifications:**
    *   **Algorithm:** Implementation of the "Token Bucket" algorithm to allow for short bursts of traffic while maintaining a steady average rate.
    *   **Tiers:** 
        *   *Free:* 100 requests/hour.
        *   *Professional:* 5,000 requests/hour.
        *   *Enterprise:* Custom limits.
    *   **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
    *   **Analytics Dashboard:** A view for admins to see the most active API keys and the most frequently hit endpoints to identify potential bottlenecks.
*   **User Story:** *As a CTO, I want to prevent a single malfunctioning client script from overwhelming our Fly.io instances and crashing the system for all other users.*

### 3.5 Multi-tenant Data Isolation (Shared Infrastructure)
*   **Priority:** Low | **Status:** Blocked | **Version:** v1.4.0
*   **Description:** A mechanism to ensure that data from Law Firm A is logically separated from Law Firm B, despite sharing the same PostgreSQL cluster.
*   **Functional Specifications:**
    *   **Row-Level Security (RLS):** Utilization of PostgreSQL RLS policies. Every table must have a `firm_id` column.
    *   **Tenant Context:** The Phoenix application must set a `current_firm_id` session variable at the start of every request.
    *   **Shared Schema:** To minimize infrastructure costs (given the $150k budget), a single schema will be used rather than separate databases per tenant.
    *   **Blocking Factor:** This feature is currently blocked by the third-party API rate limits during integration testing, which prevents the team from verifying if tenant-specific API keys are being routed correctly.
*   **User Story:** *As a Legal Auditor, I need a guarantee that no matter the query, Firm A can never accidentally retrieve a record belonging to Firm B.*

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and return JSON. Base URL: `https://api.sentinel.bellweather.tech/v1`

### 4.1 Authentication
**POST `/auth/login`**
- **Request:** `{ "email": "string", "password": "string" }`
- **Response:** `200 OK { "token": "jwt_token_string", "expires_at": "timestamp" }`
- **Example:** `{ "email": "beatriz@bellweather.tech", "password": "secure_password" }` $\rightarrow$ `{ "token": "eyJhbG...", "expires_at": "2023-10-26T14:00:00Z" }`

**POST `/auth/refresh`**
- **Request:** `{ "refresh_token": "string" }`
- **Response:** `200 OK { "token": "new_jwt_token" }`

### 4.2 Record Management
**GET `/records`**
- **Query Params:** `?firm_id=123&status=processed&limit=20`
- **Response:** `200 OK { "data": [ { "id": "uuid", "patient_name": "...", "upload_date": "..." } ], "total": 150 }`

**POST `/records/upload`**
- **Request:** `Multipart/form-data { "file": Binary, "case_id": "uuid" }`
- **Response:** `202 Accepted { "job_id": "kafka_event_id", "status": "queued" }`

**GET `/records/{id}`**
- **Response:** `200 OK { "id": "uuid", "content": "...", "metadata": { "provider": "Mayo Clinic", "date": "2021-05-12" } }`

**PATCH `/records/{id}/status`**
- **Request:** `{ "status": "verified" | "rejected" | "pending" }`
- **Response:** `200 OK { "id": "uuid", "new_status": "verified" }`

### 4.3 Dashboard & Analytics
**GET `/dashboard/widgets`**
- **Response:** `200 OK { "widgets": [ { "type": "case_count", "position": { "x": 0, "y": 0 } }, ... ] }`

**PUT `/dashboard/widgets`**
- **Request:** `{ "layout": [ { "id": "w1", "x": 2, "y": 0 }, ... ] }`
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system uses a relational PostgreSQL schema. All tables use `UUID` as primary keys.

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `firm_id` | `email`, `password_hash`, `role` | User accounts and credentials. |
| `firms` | `firm_id` | None | `firm_name`, `subscription_tier`, `created_at` | Legal firm organization details. |
| `patients` | `patient_id` | None | `patient_external_id`, `dob`, `gender` | Anonymized patient metadata. |
| `records` | `record_id` | `patient_id`, `firm_id`, `case_id` | `file_path`, `status`, `uploaded_at` | Main table for medical record entries. |
| `cases` | `case_id` | `firm_id` | `case_number`, `case_name`, `status` | Legal case groupings. |
| `audit_logs` | `log_id` | `user_id`, `record_id` | `action`, `ip_address`, `timestamp` | Immutable record of all data access. |
| `user_preferences`| `pref_id` | `user_id` | `dashboard_layout_json`, `theme` | User-specific UI settings. |
| `automation_rules`| `rule_id` | `firm_id` | `trigger_event`, `action_payload`, `is_active` | Definitions for the rule builder. |
| `api_keys` | `key_id` | `firm_id` | `api_key_hash`, `rate_limit_tier` | Keys for third-party integrations. |
| `usage_metrics` | `metric_id` | `api_key_id` | `request_count`, `window_start`, `window_end` | Tracking for rate limiting. |

**Relationships:**
- `Firms` $\rightarrow$ `Users` (One-to-Many)
- `Firms` $\rightarrow$ `Cases` (One-to-Many)
- `Cases` $\rightarrow$ `Records` (One-to-Many)
- `Patients` $\rightarrow$ `Records` (One-to-Many)
- `Users` $\rightarrow$ `Audit_Logs` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes a three-tier environment strategy hosted on Fly.io.

**1. Development (Dev):**
- **Purpose:** Daily iteration and feature development.
- **Spec:** 2 vCPUs, 1GB RAM.
- **Database:** Shared Dev PostgreSQL instance.
- **Deployment:** Triggered by push to `develop` branch.
- **Feature Flags:** All flags enabled for testing.

**2. Staging (Staging):**
- **Purpose:** QA, UAT (User Acceptance Testing), and Security Audits.
- **Spec:** Mirror of Production (4 vCPUs, 4GB RAM).
- **Database:** Isolated Staging PostgreSQL.
- **Deployment:** Triggered by merge to `release` branch.
- **Feature Flags:** Managed via LaunchDarkly to simulate production rollouts.

**3. Production (Prod):**
- **Purpose:** Live customer traffic.
- **Spec:** Auto-scaling cluster (min 2, max 10 nodes), 4GB RAM per node.
- **Database:** High-availability PostgreSQL with automated backups.
- **Deployment:** Canary releases. New code is routed to 5% of users initially.
- **Feature Flags:** Strict control; only "Stable" features enabled.

### 6.2 Infrastructure Components
- **Fly.io:** Used for global distribution to reduce latency for legal firms in different time zones.
- **Kafka:** Deployed as a managed cluster to handle the event-driven communication between the Record and Analytics services.
- **LaunchDarkly:** Used to decouple deployment (pushing code) from release (turning on features). This allows Beatriz (CTO) to toggle the "Automation Engine" off instantly if it causes system instability.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** `ExUnit` (Elixir's native testing framework).
- **Scope:** Every core business logic function (e.g., the RBAC permission checker, the rate-limit bucket calculator) must have 90%+ code coverage.
- **Cadence:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Tooling:** `Wallaby` for browser automation, `Ecto.Schedules` for DB state.
- **Scope:** Focus on the "Happy Path" of the Kafka event chain. Example: Upload File $\rightarrow$ Kafka Event $\rightarrow$ DB Write $\rightarrow$ LiveView Update.
- **Requirement:** Tests must be run against a clean PostgreSQL instance to ensure no data leakage between tests.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys:
    1. User logs in $\rightarrow$ uploads record $\rightarrow$ verifies record appears in dashboard.
    2. Admin changes user role $\rightarrow$ user attempts to access restricted record $\rightarrow$ receives 403 Forbidden.
    3. User drags a widget $\rightarrow$ refreshes page $\rightarrow$ widget remains in new position.

### 7.4 Security Testing
- **Compliance:** SOC 2 Type II.
- **Approach:** Quarterly penetration testing and automated vulnerability scanning of all dependencies using `mix audit`.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding "small" features. | High | High | **Parallel-Pathing:** Prototype alternative approaches simultaneously to show the cost/time trade-off of requested changes. |
| **R2** | Performance requirements are 10x current capacity with no budget increase. | Medium | High | **Workaround Documentation:** Optimize PostgreSQL queries and implement aggressive caching (Redis); share these workarounds with the team to manage expectations. |
| **R3** | SOC 2 Type II audit failure. | Low | Critical | Engage a compliance consultant early; automate audit logging from day one. |
| **R4** | Dependency on third-party API rate limits (Current Blocker). | High | Medium | Implement a mock API server for testing; negotiate higher limits for the staging environment. |

**Probability/Impact Matrix:**
- High Prob/High Impact $\rightarrow$ Immediate Action Required (R1)
- Medium Prob/High Impact $\rightarrow$ Active Monitoring (R2)
- Low Prob/Critical Impact $\rightarrow$ Contingency Planning (R3)

---

## 9. TIMELINE

### Phase 1: Foundation & Core UI (Completed)
- **Duration:** Jan 2024 - June 2024
- **Key Deliverable:** Customizable Dashboard.
- **Dependencies:** None.

### Phase 2: Security & Access (In Progress)
- **Duration:** July 2024 - August 2024
- **Key Deliverable:** RBAC and Auth System.
- **Dependency:** Completion of Database Schema.
- **Milestone 1:** Security audit passed (Target: 2025-08-15).

### Phase 3: Automation & Intelligence (Upcoming)
- **Duration:** September 2024 - October 2024
- **Key Deliverable:** Workflow Automation Engine.
- **Dependency:** Stable RBAC implementation.
- **Milestone 2:** First paying customer onboarded (Target: 2025-10-15).

### Phase 4: Scaling & Analytics (Final)
- **Duration:** November 2024 - December 2024
- **Key Deliverable:** API Rate Limiting and Analytics.
- **Dependency:** Multi-tenant isolation logic.
- **Milestone 3:** Stakeholder demo and sign-off (Target: 2025-12-15).

---

## 10. MEETING NOTES

*Note: These summaries are derived from recorded video calls (which are archived but rarely reviewed by the team).*

### Meeting 1: Q3 Planning & Scope Review
**Date:** 2024-07-10 | **Attendees:** Beatriz, Dante, Wyatt, Hana
- **Discussion:** Beatriz emphasized the "shoestring" nature of the budget. Dante raised concerns about Kafka overhead for such a small team. 
- **Decision:** The team agreed to stick with Kafka to ensure future scalability, despite the current complexity.
- **Action Item:** Hana to investigate if Fly.io's managed Postgres handles RLS efficiently enough to support multi-tenancy.

### Meeting 2: The "Rate Limit" Blocker Sync
**Date:** 2024-08-02 | **Attendees:** Beatriz, Dante, Wyatt, Hana
- **Discussion:** Wyatt reported that E2E tests are failing because the third-party medical API is throttling the staging environment.
- **Decision:** Instead of paying for a higher tier (budget constraint), the team will build a "Mock API" that mimics the third-party responses for all QA cycles.
- **Action Item:** Dante to implement the Mock API by Friday.

### Meeting 3: Technical Debt & Config Review
**Date:** 2024-08-20 | **Attendees:** Beatriz, Dante, Wyatt, Hana
- **Discussion:** Hana pointed out that there are hardcoded API keys and database URLs scattered across 40+ files, making environment switching a nightmare.
- **Decision:** The team will dedicate one full sprint to "Debt Liquidation," moving all constants into `.env` files and a centralized `Config` module.
- **Action Item:** All members to identify hardcoded values in their respective modules.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $105,000 | Salary for 3 internal staff and contractor fees for Hana Costa. |
| **Infrastructure** | 15% | $22,500 | Fly.io hosting, Kafka managed cluster, PostgreSQL storage. |
| **Tools & SaaS** | 10% | $15,000 | LaunchDarkly license, SOC 2 compliance software, GitHub Enterprise. |
| **Contingency** | 5% | $7,500 | Emergency API overages or critical hardware replacements. |

**Budgetary Constraint Note:** Every dollar is scrutinized. Any expenditure over $500 requires direct sign-off from Beatriz Park.

---

## 12. APPENDICES

### Appendix A: Hardcoded Configuration Debt Map
The following files have been identified as containing hardcoded values that must be migrated to the centralized config:
- `lib/sentinel/api_client.ex` (API Keys)
- `config/runtime.exs` (DB Connection Strings)
- `web/controllers/record_controller.ex` (Static Timeout Values)
- `lib/sentinel/auth/token.ex` (Secret Salts)
- [36 other files identified in JIRA ticket SENT-902]

### Appendix B: SOC 2 Type II Compliance Checklist
To meet Milestone 1 (2025-08-15), the following controls must be implemented:
1. **Access Control:** MFA for all administrative accounts.
2. **Change Management:** All code changes must have a peer-reviewed Pull Request (PR) and a linked JIRA ticket.
3. **Encryption:** All data must be encrypted at rest (AES-256) and in transit (TLS 1.3).
4. **Incident Response:** A documented process for reporting and mitigating security breaches.
5. **Auditability:** Every write operation in the `records` table must trigger an entry in `audit_logs`.