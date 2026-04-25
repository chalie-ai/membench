Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, industrial-grade Project Specification. It is structured to serve as the "Single Source of Truth" for the development team at Nightjar Systems.

***

# PROJECT SPECIFICATION: GLACIER
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Owner:** Ola Stein (CTO)  
**Company:** Nightjar Systems  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Glacier" is a mission-critical initiative by Nightjar Systems to overhaul the company’s foundational healthcare records infrastructure. Despite Nightjar Systems operating within the logistics and shipping industry, the movement of medical supplies, pharmaceuticals, and temperature-sensitive healthcare cargo requires a robust, compliant, and highly available records platform. 

The current system is a 15-year-old monolithic legacy application. Over a decade and a half, this system has become the single point of failure for the entire organization. Every shipment, customs clearance, and regulatory audit depends on the data held within this legacy core. The technical debt has reached a critical mass where maintenance is no longer sustainable, and the risk of a catastrophic system failure is increasing daily.

### 1.2 Business Justification
The "Zero Downtime Tolerance" requirement is the driving force behind Glacier. In the logistics of healthcare, a four-hour outage does not just mean lost revenue; it means spoiled vaccines, expired life-saving medications, and legal liability for Nightjar Systems. The legacy system lacks the scalability to handle the 40% increase in shipment volume seen over the last 24 months.

By migrating to a modern micro-frontend architecture, Nightjar Systems will achieve:
1. **Operational Resilience:** Elimination of the "single point of failure" via independent deployment cycles.
2. **Developer Velocity:** Reducing the deployment cycle from monthly (legacy) to daily (Glacier).
3. **Market Competitiveness:** The ability to expose a customer-facing API will allow Nightjar to integrate directly with hospital ERPs, removing manual data entry and reducing errors by an estimated 30%.

### 1.3 ROI Projection
The budget for Glacier is $3,000,000. The projected Return on Investment (ROI) is calculated based on three primary levers:
- **Reduction in Operational Overhead:** By automating the record-keeping process and eliminating manual legacy patches, the company expects to save $450,000 per annum in engineering maintenance costs.
- **Revenue Growth via API:** The introduction of the Customer-Facing API (a critical launch blocker) is expected to attract high-value enterprise clients, projecting a revenue increase of $1.2M in the first 18 months post-launch.
- **Risk Mitigation:** The cost of a total legacy system collapse is estimated at $10M+ in lost contracts and fines. Glacier effectively hedges this risk.

The total projected ROI is expected to reach break-even within 22 months of the Production Launch (Target: 2026-07-15).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Glacier utilizes a **Micro-Frontend (MFE) Architecture**. Given the complexity of healthcare records (where auditing, user management, and record viewing are distinct domains), the platform is split into independent ownership modules. This prevents a bug in the "Notification System" from crashing the "Authentication" or "API" layers.

### 2.2 The Stack
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS.
- **Backend/ORM:** Prisma ORM.
- **Database:** PostgreSQL 15 (Managed via AWS RDS or similar).
- **Hosting/Deployment:** Vercel (Frontend) and Kubernetes (Backend services).
- **CI/CD:** GitLab CI with rolling deployments to ensure zero downtime.

### 2.3 System Diagram (ASCII Description)
```text
[ User Browser ] <---> [ Vercel Edge Network ] <---> [ Next.js App Shell ]
                                                           |
                                                           | (Module Federation)
                                                           v
        +-----------------------------------------------------------------------+
        |                         MICRO-FRONTEND LAYER                          |
        |  [ Auth Module ]    [ Records Module ]    [ Search Module ]    [ API Mgr ]|
        +-----------------------------------------------------------------------+
                                                           |
                                                           | (REST / GraphQL)
                                                           v
        +-----------------------------------------------------------------------+
        |                         SERVICE LAYER (K8s)                           |
        |  [ Auth Service ]   [ Notification Svc ]   [ Indexing Svc ]   [ Audit Svc ]|
        +-----------------------------------------------------------------------+
                                                           |
                                                           | (Prisma Client)
                                                           v
        +-----------------------------------------------------------------------+
        |                         DATA PERSISTENCE                              |
        |  [ PostgreSQL Master ] <---> [ Read Replica 1 ] <---> [ Read Replica 2 ] |
        +-----------------------------------------------------------------------+
```

### 2.4 Deployment Strategy
To meet the "Zero Downtime" requirement, GitLab CI will orchestrate **Rolling Deployments**. 
1. New pods are spun up in the Kubernetes cluster.
2. Health checks verify the new version.
3. Traffic is shifted incrementally (Canary release) from the old pods to the new pods.
4. If error rates spike above 0.5%, an automatic rollback is triggered.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** High | **Status:** Blocked
**Description:** 
A comprehensive security layer to ensure that sensitive healthcare records are only accessible to authorized personnel. Given the nature of the logistics industry, roles must differentiate between "Warehouse Operator," "Compliance Officer," "Client Admin," and "System Superuser."

**Functional Requirements:**
- **Multi-Factor Authentication (MFA):** Mandatory for all "Compliance" and "Admin" roles using TOTP (Time-based One-Time Password).
- **JWT Implementation:** Stateless authentication using signed JSON Web Tokens with a 15-minute expiry and a secure refresh token stored in an `HttpOnly` cookie.
- **Granular Permissions:** Permissions are not just role-based but attribute-based (ABAC). For example, a Warehouse Operator can only view records for shipments currently located in their specific geographic zone.
- **Session Management:** Ability for administrators to revoke active sessions globally in the event of a security breach.

**Technical Constraints:**
- Must integrate with the existing Nightjar LDAP for internal employees while supporting OAuth2 for external customers.
- Password hashing must use Argon2id.

**Current Blocker:**
There is a fundamental design disagreement between the Product Lead and Engineering Lead regarding whether the RBAC should be managed within the application logic or handled at the Database Row Level Security (RLS) layer in PostgreSQL. Engineering prefers RLS for security, while Product argues it will slow down the development of the customer-facing API.

---

### 3.2 Notification System
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:** 
A multi-channel communication engine designed to alert users of critical record updates, shipment delays, or compliance failures.

**Functional Requirements:**
- **Email:** Integration with SendGrid for transactional emails (e.g., "Record Updated").
- **SMS:** Integration with Twilio for urgent alerts (e.g., "Temperature Threshold Exceeded").
- **In-App:** A real-time notification bell using WebSockets (Socket.io) to push updates without page refreshes.
- **Push:** Browser-based push notifications for mobile users utilizing Service Workers.

**Technical Specifications:**
- **Queueing:** To prevent the API from slowing down, notifications must be processed asynchronously. A Redis-backed queue (BullMQ) will be used to handle outgoing messages.
- **Preference Center:** Users must be able to toggle which channels they receive specific notification types on.
- **Retry Logic:** Exponential backoff for failed SMS/Email deliveries.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low (Nice to Have) | **Status:** In Design
**Description:** 
A high-performance search interface allowing users to find specific records across millions of entries using complex filters.

**Functional Requirements:**
- **Full-Text Search (FTS):** Implementation of PostgreSQL `tsvector` and `tsquery` for keyword searches across shipment IDs, patient IDs, and cargo descriptions.
- **Faceted Filtering:** A sidebar allowing users to filter by Date Range, Cargo Type (e.g., Cold Chain, Hazardous), Origin Country, and Status (e.g., In-Transit, Delivered).
- **Autocomplete:** As-you-type suggestions for common search terms to reduce user error.

**Technical Specifications:**
- **Indexing Strategy:** GIN (Generalized Inverted Index) will be used for the FTS columns to maintain sub-second response times.
- **Debouncing:** Frontend implementation of 300ms debouncing on the search input to prevent API hammering.
- **Caching:** Frequent search queries will be cached in Redis for 5 minutes.

---

### 3.4 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low (Nice to Have) | **Status:** In Design
**Description:** 
A non-repudiation log that records every single read, write, and update operation performed on a healthcare record.

**Functional Requirements:**
- **Immutability:** Once a log entry is written, it must be impossible to modify or delete, even by a system administrator.
- **Detailed Context:** Each log must capture the User ID, Timestamp, IP Address, Action Performed, Old Value, and New Value.
- **Exportability:** One-click generation of PDF/CSV audit reports for regulatory bodies.

**Technical Specifications:**
- **Storage:** Logs will be written to a dedicated `audit_logs` table. To ensure tamper-evidence, the system will implement "Cryptographic Chaining"—each log entry will contain a hash of the previous entry.
- **Write-Ahead Logging:** The audit service will operate on a "Write-First" basis; the primary record update will not be committed until the audit log is successfully persisted.
- **Cold Storage:** Logs older than 2 years will be archived to AWS S3 Glacier for long-term retention.

---

### 3.5 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** 
A robust REST API that allows Nightjar's B2B customers to programmatically access and update their records, bypassing the GUI.

**Functional Requirements:**
- **API Versioning:** URI-based versioning (e.g., `/api/v1/records`) to ensure backward compatibility.
- **Sandbox Environment:** A mirrored "Stage" environment where customers can test their integrations without affecting live production data.
- **Rate Limiting:** Implementation of a leaky-bucket algorithm to limit requests per API key (e.g., 100 requests/minute for Standard tier, 1000/minute for Enterprise).
- **Documentation:** Automated Swagger/OpenAPI 3.0 documentation.

**Technical Specifications:**
- **Authentication:** API Key and Secret pair (X-API-KEY header).
- **Payloads:** Strict JSON schema validation using Zod.
- **Sandbox Sync:** A nightly job that scrubs sensitive PII (Personally Identifiable Information) from Production and syncs a subset of data to the Sandbox database.

**Current Blocker:**
Blocked by Feature 3.1 (Auth/RBAC). The API cannot be launched without a finalized authorization strategy to determine which customer can access which records.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include `Authorization: Bearer <token>`.

### 4.1 `GET /records`
**Description:** Retrieves a paginated list of healthcare records.
- **Query Params:** `page` (int), `limit` (int), `filter` (string).
- **Request Example:** `GET /api/v1/records?page=1&limit=20&filter=cold-chain`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "REC-9921", "status": "In-Transit", "cargo_type": "Vaccine", "last_updated": "2023-10-24T10:00:00Z" }
  ],
  "pagination": { "total": 1450, "pages": 73 }
}
```

### 4.2 `POST /records`
**Description:** Creates a new healthcare record.
- **Request Body:**
```json
{
  "patient_ref": "PAT-112",
  "cargo_details": "Insulin - Batch A",
  "temp_requirement": "2-8C",
  "origin": "Berlin",
  "destination": "New York"
}
```
- **Response (201 Created):** `{ "id": "REC-9922", "status": "Created" }`

### 4.3 `PATCH /records/{id}`
**Description:** Updates an existing record.
- **Request Body:** `{ "status": "Delivered" }`
- **Response (200 OK):** `{ "id": "REC-9921", "status": "Delivered" }`

### 4.4 `GET /records/{id}`
**Description:** Fetches full details of a specific record.
- **Response (200 OK):**
```json
{
  "id": "REC-9921",
  "details": { ... },
  "audit_history_summary": "5 changes"
}
```

### 4.5 `DELETE /records/{id}`
**Description:** Performs a "soft delete" on a record.
- **Response (204 No Content):** (Empty body)

### 4.6 `GET /auth/session`
**Description:** Validates the current session token.
- **Response (200 OK):** `{ "user": "Sanjay Fischer", "role": "DevOps", "expires": "2023-10-24T11:00:00Z" }`

### 4.7 `POST /notifications/send`
**Description:** Manual trigger for a notification (Admin only).
- **Request Body:** `{ "userId": "USER-1", "channel": "SMS", "message": "Urgent: Cargo Temp Alert" }`
- **Response (202 Accepted):** `{ "jobId": "job_8821" }`

### 4.8 `GET /audit/logs`
**Description:** Retrieves audit logs for a specific record.
- **Query Params:** `recordId` (string).
- **Response (200 OK):**
```json
[
  { "timestamp": "2023-10-24T09:00:00Z", "user": "Admin", "action": "UPDATE", "change": "Status: Pending -> Shipped" }
]
```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL relational schema managed via Prisma.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role_id` | User account data. |
| `roles` | `role_id` | None | `role_name`, `permissions_json` | RBAC role definitions. |
| `records` | `record_id` | `created_by` | `cargo_type`, `temp_req`, `status` | Core healthcare records. |
| `shipments` | `shipment_id` | `record_id` | `tracking_number`, `carrier` | Shipping logistics data. |
| `locations` | `loc_id` | None | `city`, `country`, `warehouse_code` | Geospatial data. |
| `audit_logs` | `log_id` | `user_id`, `record_id` | `action`, `prev_value`, `new_value`, `hash` | Tamper-evident logs. |
| `notifications` | `notif_id` | `user_id` | `channel`, `message`, `is_read` | Notification history. |
| `api_keys` | `key_id` | `user_id` | `api_key_hash`, `rate_limit`, `expires` | Customer API access. |
| `clients` | `client_id` | None | `company_name`, `industry_segment` | B2B Customer entities. |
| `temp_logs` | `temp_id` | `record_id` | `recorded_temp`, `timestamp` | IoT temperature telemetry. |

### 5.2 Key Relationships
- **One-to-Many:** `users` $\rightarrow$ `audit_logs` (One user creates many logs).
- **One-to-One:** `records` $\rightarrow$ `shipments` (One record per shipment).
- **Many-to-Many:** `users` $\rightarrow$ `roles` (Handled via a join table `user_roles`).
- **One-to-Many:** `records` $\rightarrow$ `temp_logs` (One record has many temperature readings over time).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy

#### Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Individual developer branches deployed to Vercel Preview deployments.
- **Database:** Local Dockerized PostgreSQL containers.
- **Deployment Trigger:** Every push to a feature branch.

#### Staging (Stage/Sandbox)
- **Purpose:** Integration testing, QA, and Customer Sandbox.
- **Infrastructure:** A Kubernetes namespace that mirrors Production.
- **Database:** A sanitized clone of the Production database (PII removed).
- **Deployment Trigger:** Merges to the `develop` branch.

#### Production (Prod)
- **Purpose:** Live customer traffic.
- **Infrastructure:** Multi-region Kubernetes cluster with Vercel Edge caching.
- **Database:** High-availability PostgreSQL with synchronous replication to a standby instance.
- **Deployment Trigger:** Tagged releases to the `main` branch after QA approval.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is defined via Terraform. This ensures that if the Production environment needs to be evacuated to a different region, the entire stack can be redeployed in under 30 minutes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** Jest and Vitest.
- **Target:** 80% code coverage.
- **Focus:** Business logic, utility functions, and Prisma middleware.
- **Execution:** Run on every commit via GitLab CI.

### 7.2 Integration Testing
- **Tool:** Supertest and Pytest.
- **Focus:** API endpoint contracts. Testing the flow between the API layer and the Database.
- **Scenario:** "Create a record $\rightarrow$ Update status $\rightarrow$ Verify audit log entry exists."
- **Execution:** Run on every merge request to `develop`.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Critical user journeys (e.g., "Login $\rightarrow$ Search for Record $\rightarrow$ Export Audit Report").
- **Execution:** Run nightly against the Staging environment.

### 7.4 Performance Testing
- **Tool:** k6.
- **Goal:** Milestone 1 (Performance Benchmarks).
- **Target:** 500 concurrent requests per second with a P95 latency of $< 200ms$.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is 2 months ahead in product release. | High | High | Develop a "Fast-Follow" contingency plan. Focus on the API (Critical) to win on integration quality rather than just feature set. |
| **R-02** | Primary Vendor EOL (End-of-Life) announcement. | Medium | Critical | Assign Orin Liu as the dedicated owner to track the vendor's roadmap and develop a migration wrapper to abstract the vendor's API. |
| **R-03** | Zero-Downtime migration failure. | Low | Critical | Implement a "Shadow Write" phase where data is written to both legacy and Glacier systems simultaneously for 30 days. |
| **R-04** | Design deadlock between Product/Eng leads. | High | Medium | CTO (Ola Stein) to act as the final tie-breaker; move decision to a formal RFC (Request for Comments) document. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project halt or business failure.
- **High:** Significant delay or budget overrun.
- **Medium:** Manageable with effort.
- **Low:** Minimal impact on timeline.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Oct 2023 - May 2026)
- **Focus:** Core DB schema, Auth (once unblocked), and Basic Record CRUD.
- **Dependency:** Resolution of the RBAC design disagreement.
- **Goal:** Reach internal Alpha.

### 9.2 Phase 2: Optimization (May 2026 - July 2026)
- **Focus:** Performance tuning and API Sandbox.
- **Key Milestone:** **Milestone 1 (2026-05-15)** - Performance benchmarks must be met (P95 < 200ms).
- **Dependency:** Successful completion of E2E testing.

### 9.3 Phase 3: Transition (July 2026)
- **Focus:** Data migration from 15-year-old legacy system.
- **Key Milestone:** **Milestone 2 (2026-07-15)** - Production Launch.
- **Method:** Blue-Green deployment.

### 9.4 Phase 4: Stabilization (July 2026 - Sept 2026)
- **Focus:** Bug fixing and NPS monitoring.
- **Key Milestone:** **Milestone 3 (2026-09-15)** - Stability confirmation.
- **Success Metric:** NPS > 40.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team policy, formal minutes are not kept. The following are synthesized from key decision threads in the `#glacier-core` Slack channel.

### Thread 1: The "Date Format" Disaster
**Date:** Nov 12, 2023  
**Participants:** Sanjay, Gemma, Orin  
**Discussion:** Sanjay pointed out that the legacy system uses `MM/DD/YYYY`, the new API uses `ISO-8601`, and the database is storing some dates as `Unix Timestamps`.  
**Decision:** The team agreed that since no normalization layer exists, Orin will implement a `DateUtility` wrapper in the core library. All new code must use ISO-8601. Legacy data will be normalized *during* the migration script, not in the application layer.

### Thread 2: The RBAC Deadlock
**Date:** Dec 05, 2023  
**Participants:** Ola (CTO), Product Lead, Engineering Lead  
**Discussion:** Heated debate over Row Level Security (RLS) vs. Application-level checks. Product Lead argues RLS makes the API "black-box" and hard to debug for customers. Engineering Lead argues application-level checks are prone to "leaky" permissions.  
**Decision:** Ola stepped in. Decision postponed until the API specification is finalized. Currently listed as a **Blocker**.

### Thread 3: Vendor EOL Panic
**Date:** Jan 20, 2024  
**Participants:** Ola, Orin  
**Discussion:** Vendor "LogiTrack" announced EOL for their v3 API by 2026.  
**Decision:** Orin Liu is officially assigned as the "Vendor Liaison." He will build an abstraction layer (Adapter Pattern) so that if the vendor is replaced, only the adapter needs to be rewritten, not the core business logic.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 12-person team over 2.5 years, including contractor fees for Orin Liu. |
| **Infrastructure** | 15% | $450,000 | Vercel Enterprise, AWS RDS (Multi-AZ), Kubernetes Cluster, GitLab Premium. |
| **Tools & Licenses** | 10% | $300,000 | SendGrid, Twilio, New Relic (Monitoring), Sentry (Error Tracking). |
| **Contingency** | 10% | $300,000 | Reserved for emergency vendor replacements or accelerated hiring. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following items are acknowledged as "Accepted Debt" to meet the 2026-07-15 deadline:
1. **Date Normalization:** The codebase currently contains three different date formats. A full cleanup is deferred until post-launch stability (Milestone 3).
2. **External Compliance:** The platform is only undergoing an internal security audit. External certifications (HIPAA/GDPR) are not required for this phase but may be needed for future market expansion.
3. **Notification Priority:** The notification system is currently "Low Priority" and may be launched as a basic email-only version if the API timeline slips.

### Appendix B: Data Migration Strategy
To achieve zero downtime during the transition from the 15-year-old legacy system, the following "Parallel Run" strategy will be used:
1. **Phase 1 (Read-Only):** Glacier reads from the legacy DB but doesn't write.
2. **Phase 2 (Shadow Write):** Both systems receive writes. Glacier validates the data against legacy outputs.
3. **Phase 3 (Primary Switch):** Glacier becomes the system of record. Legacy system remains as a read-only backup for 90 days.
4. **Phase 4 (Decommission):** Legacy system is shut down.