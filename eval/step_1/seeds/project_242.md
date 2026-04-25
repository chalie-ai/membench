Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Technical Specification Document (TSD). It is structured to serve as the "Single Source of Truth" for the development team at Nightjar Systems.

***

# PROJECT SPECIFICATION: PROJECT UMBRA
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft/Active  
**Company:** Nightjar Systems  
**Classification:** Confidential – Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Umbra is a strategic platform modernization effort for Nightjar Systems, specifically targeting the aerospace sector. The project aims to transition the existing legacy cybersecurity monitoring infrastructure from a monolithic architecture to a modern, scalable microservices-based ecosystem. The primary objective is to provide real-time visibility into threat landscapes across aerospace telemetry and ground-control systems, ensuring high availability and rigorous data integrity.

### 1.2 Business Justification
The aerospace industry operates under extreme precision and high-stakes security requirements. The current monolithic system has become a bottleneck, suffering from deployment fragility, slow iteration cycles, and an inability to scale horizontally during high-traffic security events. By moving to a microservices architecture over an 18-month transition period, Nightjar Systems will reduce the "Mean Time to Repair" (MTTR) for critical bugs and increase the "Deployment Frequency" (DF) from monthly to weekly (within the bounds of regulatory review).

The business driver is the need for a "single pane of glass" dashboard that can ingest massive streams of security logs and provide actionable intelligence without the latency inherent in the current legacy system.

### 1.3 ROI Projection and Success Criteria
The financial viability of Umbra is tied to both operational efficiency and market expansion. The project is funded via milestone-based tranches, meaning funding is released only upon the achievement of specific technical and business goals.

**Metric 1: Revenue Generation**  
The primary financial goal is to attribute $500,000 in new revenue to the Umbra platform within the first 12 months of the first paying customer’s onboarding. This will be achieved through a tiered SaaS pricing model targeting mid-sized aerospace contractors who require compliant security monitoring but lack the infrastructure to build it in-house.

**Metric 2: Customer Satisfaction**  
The product must achieve a Net Promoter Score (NPS) above 40 within the first quarter of general availability. This is a critical KPI, as the aerospace sector relies heavily on trust and referral. A score of 40+ indicates that the product is not only functional but intuitive, solving a genuine pain point in the current workflow of Security Operations Center (SOC) analysts.

**ROI Summary Table:**
| Category | Projected Impact | Value |
| :--- | :--- | :--- |
| New Revenue | Direct B2B Sales | $500,000 |
| OpEx Reduction | Reduced Server Overhead | $45,000 / year |
| Risk Mitigation | Lower Probability of Breach | $\text{Value of avoided downtime}$ |

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Umbra follows a traditional three-tier architecture, optimized for the transition from monolith to microservices. While the long-term goal is a fully decoupled mesh, the immediate implementation focuses on a clean separation of concerns.

**1. Presentation Tier:** Built with **Next.js** and **TypeScript**. This layer handles client-side rendering (CSR) for the dashboard and server-side rendering (SSR) for initial load and SEO/Performance optimization. It communicates via RESTful APIs to the business logic layer.
**2. Business Logic Tier:** A series of Node.js services (initially hosted as Next.js API routes, migrating to standalone containers) that handle authentication, data processing, and alert triggering.
**3. Data Tier:** A **PostgreSQL** database managed via **Prisma ORM**. This ensures type-safety across the stack and allows for rapid schema migrations.

### 2.2 ASCII System Architecture Diagram
```text
[ USER BROWSER ] <---> [ VERCEL EDGE NETWORK ]
                               |
                               v
                    [ NEXT.JS FRONTEND (TS) ]
                               |
         ______________________|______________________
        |                      |                      |
 [ AUTH SERVICE ]      [ MONITORING ENGINE ]    [ REPORTING SVC ]
        |                      |                      |
        |______________________|______________________|
                               |
                               v
                      [ PRISMA ORM LAYER ]
                               |
                               v
                    [ POSTGRESQL DATABASE ]
            (Multi-tenant Schema / Row Level Security)
                               |
        _______________________|_______________________
       |                       |                       |
 [ AUDIT LOGS ]        [ TELEMETRY DATA ]       [ USER PROFILES ]
 (Tamper-Evident)       (Time-Series Data)       (Relational Data)
```

### 2.3 Tech Stack Justification
- **TypeScript:** Essential for the aerospace industry to minimize runtime errors in critical monitoring systems.
- **Next.js:** Provides the necessary routing and optimization for a complex dashboard with many nested views.
- **Prisma:** Selected for its ability to handle complex relational mappings between aerospace assets and security events.
- **PostgreSQL:** The industry standard for reliability and support for JSONB types, which are necessary for varying security log formats.
- **Vercel:** Chosen for rapid deployment cycles and seamless integration with Next.js, enabling the quarterly release schedule.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: High | Status: Not Started)
**Description:**
Since Nightjar Systems serves multiple aerospace clients, Umbra must ensure that data from one client (Tenant A) is never visible to another client (Tenant B), even though they share the same physical database infrastructure.

**Functional Requirements:**
- **Logical Isolation:** Every table in the database must contain a `tenant_id` column. All queries must be filtered by this ID.
- **RLS Implementation:** Use PostgreSQL Row Level Security (RLS) to ensure that even a compromised API endpoint cannot leak data across tenants.
- **Tenant Provisioning:** A mechanism to create new tenants, assign them to a specific "Tier" (e.g., Basic, Pro, Enterprise), and allocate resource quotas.
- **Administrative Override:** A "Super-Admin" role must exist for Nightjar employees to troubleshoot client issues, but this must be logged in the audit trail.

**Technical Implementation:**
The `tenant_id` will be extracted from the JWT (JSON Web Token) during the request lifecycle. A middleware in Next.js will inject the `tenant_id` into the Prisma client context, ensuring that no `findMany` or `update` call is executed without a tenant filter.

### 3.2 Audit Trail Logging with Tamper-Evident Storage (Priority: High | Status: In Design)
**Description:**
In the aerospace sector, "who did what and when" is a regulatory requirement. The audit trail must record every configuration change, user login, and data export. Crucially, the logs must be "tamper-evident," meaning any attempt to alter a log entry must be detectable.

**Functional Requirements:**
- **Immutable Logs:** Once written, log entries cannot be edited or deleted by any user, including admins.
- **Cryptographic Chaining:** Each log entry will contain a hash of the previous entry (similar to a blockchain), creating a chain of integrity.
- **Event Capture:** Capture the `actor_id`, `action`, `timestamp`, `ip_address`, and `delta` (the difference between the old value and the new value).
- **Verification Utility:** A built-in tool that can scan the log chain and alert if a hash mismatch is found.

**Technical Implementation:**
Logs will be stored in a dedicated `audit_logs` table. A trigger in PostgreSQL will prevent `UPDATE` or `DELETE` operations on this table. The hashing will be performed using SHA-256, where $\text{Hash}_n = \text{SHA256}(\text{Data}_n + \text{Hash}_{n-1})$.

### 3.3 Advanced Search with Faceted Filtering (Priority: Low | Status: In Review)
**Description:**
SOC analysts need to sift through millions of security events. A standard keyword search is insufficient. This feature provides "faceted search," allowing users to drill down by severity, asset type, time range, and alert category.

**Functional Requirements:**
- **Full-Text Indexing:** Integration of GIN indexes in PostgreSQL to allow fast searching of unstructured log messages.
- **Dynamic Facets:** The sidebar must update in real-time to show the count of results for each filter (e.g., "High Severity: 42").
- **Boolean Logic:** Support for `AND`, `OR`, and `NOT` operators in the search bar.
- **Saved Searches:** Ability for users to save a complex filter set as a "View" for daily monitoring.

**Technical Implementation:**
The system will utilize PostgreSQL `tsvector` for full-text search. Facets will be calculated using `GROUP BY` queries on the filtered result set. To optimize performance, the search will be decoupled from the main operational database and indexed via a materialized view.

### 3.4 Offline-First Mode with Background Sync (Priority: Low | Status: Blocked)
**Description:**
Certain aerospace environments (e.g., hangars or remote flight lines) have intermittent connectivity. This feature allows users to continue interacting with the dashboard while offline and sync changes once connectivity is restored.

**Functional Requirements:**
- **Local Persistence:** Use IndexedDB via a library like `Dexie.js` to cache the current state of the dashboard.
- **Optimistic UI Updates:** Changes made offline should appear immediately in the UI, marked as "Pending Sync."
- **Conflict Resolution:** A "Last-Write-Wins" or "Manual Merge" strategy to handle cases where data was changed on the server and locally simultaneously.
- **Background Sync API:** Use the browser's Service Worker API to push queued changes in the background.

**Technical Implementation:**
This feature is currently **Blocked** due to the lack of a defined conflict resolution policy for aerospace telemetry data. Once unblocked, it will implement a "Queue" system where all mutations are stored as a series of events (Event Sourcing) and played back to the server upon reconnection.

### 3.5 Data Import/Export with Format Auto-Detection (Priority: Low | Status: Not Started)
**Description:**
Users must be able to migrate data from legacy CSVs, JSON logs, or XML formats into Umbra. The system should automatically detect the format and map the fields to the internal schema.

**Functional Requirements:**
- **Auto-Detection:** The system must analyze the first 10 lines of an uploaded file to determine the MIME type and delimiter.
- **Schema Mapping:** A UI for users to map "Legacy Field A" to "Umbra Field B" if the auto-detection fails.
- **Bulk Export:** Ability to export filtered data into CSV or PDF for regulatory reporting.
- **Validation:** A pre-import check that flags malformed data before it enters the database.

**Technical Implementation:**
The backend will utilize a stream-processing library to handle large files without crashing the Node.js process. A set of "Parser Strategies" will be implemented; the system will iterate through these strategies until one returns a valid parse result.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and require a Bearer Token in the Authorization header.

### 4.1 Authentication & Tenant Management
**`POST /api/v1/auth/login`**
- **Description:** Authenticates user and returns a JWT and tenant context.
- **Request:** `{ "email": "user@nightjar.com", "password": "..." }`
- **Response:** `{ "token": "eyJ...", "tenantId": "T-101", "role": "analyst" }`

**`GET /api/v1/tenant/config`**
- **Description:** Retrieves tenant-specific settings (e.g., alert thresholds).
- **Response:** `{ "tenantId": "T-101", "settings": { "alert_threshold": 5, "timezone": "UTC" } }`

### 4.2 Security Event Monitoring
**`GET /api/v1/events`**
- **Description:** Fetches a list of security events with optional filtering.
- **Query Params:** `?severity=high&limit=50&offset=0`
- **Response:** `[ { "id": "evt_1", "timestamp": "2023-10-24T10:00Z", "message": "Unauthorized Access Attempt", "severity": "high" }, ... ]`

**`POST /api/v1/events/acknowledge`**
- **Description:** Marks a security event as acknowledged by an analyst.
- **Request:** `{ "eventId": "evt_1", "notes": "Investigating potential false positive." }`
- **Response:** `{ "status": "success", "updatedAt": "2023-10-24T10:05Z" }`

### 4.3 Audit and Compliance
**`GET /api/v1/audit/logs`**
- **Description:** Returns the tamper-evident log chain.
- **Response:** `[ { "seq": 1, "hash": "a1b2...", "action": "USER_LOGIN", "userId": "u_1" }, ... ]`

**`POST /api/v1/audit/verify`**
- **Description:** Triggers a full chain verification check.
- **Response:** `{ "verified": true, "lastValidSeq": 5402, "errors": [] }`

### 4.4 Search and Data
**`GET /api/v1/search`**
- **Description:** Performs a full-text search across event logs.
- **Query Params:** `?q=firewall+breach&tenantId=T-101`
- **Response:** `{ "results": [...], "facets": { "severity": { "high": 10, "low": 2 } } }`

**`POST /api/v1/import/upload`**
- **Description:** Uploads a data file for import.
- **Request:** Multipart form-data containing the file.
- **Response:** `{ "jobId": "job_99", "status": "processing", "estimatedTime": "30s" }`

---

## 5. DATABASE SCHEMA

The database uses a relational structure with a heavy emphasis on `tenant_id` for isolation.

### 5.1 Table Definitions

1.  **`Tenants`**
    - `id` (UUID, PK): Unique identifier for the client.
    - `name` (String): Company name.
    - `plan_level` (Enum): [BASIC, PRO, ENTERPRISE].
    - `created_at` (Timestamp).
2.  **`Users`**
    - `id` (UUID, PK): Unique user identifier.
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants): The client the user belongs to.
    - `email` (String, Unique): User login email.
    - `password_hash` (String): Argon2 hashed password.
    - `role` (Enum): [ADMIN, ANALYST, VIEW_ONLY].
3.  **`SecurityEvents`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `severity` (Enum): [INFO, LOW, MEDIUM, HIGH, CRITICAL].
    - `source_ip` (Inet): IP address of the event source.
    - `message` (Text): Full log message.
    - `timestamp` (Timestamp).
    - `status` (Enum): [OPEN, ACKNOWLEDGED, RESOLVED].
4.  **`AuditLogs`**
    - `id` (BigInt, PK): Sequential ID.
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `user_id` (UUID, FK $\rightarrow$ Users).
    - `action` (String): Description of the change.
    - `prev_hash` (String): SHA-256 hash of the previous row.
    - `curr_hash` (String): SHA-256 hash of current row.
    - `timestamp` (Timestamp).
5.  **`Assets`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `asset_name` (String): e.g., "Flight-Control-Srv-01".
    - `asset_type` (String): e.g., "Server", "Satellite-Link".
    - `ip_address` (Inet).
6.  **`EventAssignments`**
    - `event_id` (UUID, FK $\rightarrow$ SecurityEvents).
    - `user_id` (UUID, FK $\rightarrow$ Users).
    - `assigned_at` (Timestamp).
7.  **`SearchQueries`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `user_id` (UUID, FK $\rightarrow$ Users).
    - `query_string` (Text).
    - `is_saved` (Boolean).
8.  **`ImportJobs`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `filename` (String).
    - `status` (Enum): [PENDING, PROCESSING, COMPLETED, FAILED].
    - `error_log` (Text).
9.  **`AlertThresholds`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ Tenants).
    - `event_type` (String).
    - `threshold_value` (Int).
    - `notification_channel` (String).
10. **`UserSessions`**
    - `session_id` (String, PK).
    - `user_id` (UUID, FK $\rightarrow$ Users).
    - `expires_at` (Timestamp).
    - `ip_address` (Inet).

### 5.2 Key Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many. Each user belongs to exactly one tenant.
- **Tenants $\rightarrow$ SecurityEvents:** One-to-Many. Data isolation is enforced here.
- **Users $\rightarrow$ AuditLogs:** One-to-Many. Tracks user activity.
- **SecurityEvents $\rightarrow$ Assets:** Many-to-One. Events are linked to specific aerospace assets.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra utilizes a three-tier environment strategy to ensure that no untested code reaches the production aerospace telemetry streams.

**1. Development (Dev):**
- **Purpose:** Feature development and unit testing.
- **Deployment:** Automatic deployment on every push to the `dev` branch.
- **Database:** Shared development database with mocked tenant data.
- **Access:** Restricted to the internal development team.

**2. Staging (Stage):**
- **Purpose:** Pre-production validation and Quality Assurance (QA) testing.
- **Deployment:** Triggered upon merging `dev` into `staging`.
- **Database:** A sanitized clone of the production database (PII removed).
- **Access:** Developers, QA, and selected Stakeholders.

**3. Production (Prod):**
- **Purpose:** Live customer environment.
- **Deployment:** Quarterly releases aligned with regulatory review cycles.
- **Database:** High-availability PostgreSQL cluster with multi-region replication.
- **Access:** End-customers and Nightjar Systems SREs.

### 6.2 CI/CD Pipeline
The pipeline is managed via Vercel and GitHub Actions.
- **Step 1: Linting & Type Check:** `npm run lint` and `tsc` must pass.
- **Step 2: Unit Tests:** Execution of Jest suites.
- **Step 3: Integration Tests:** Testing API endpoints against a temporary Dockerized PostgreSQL instance.
- **Step 4: Deployment to Stage:** Vercel Preview Deployment.
- **Step 5: Regulatory Sign-off:** Manual approval by the Compliance Officer.
- **Step 6: Production Deploy:** Atomic swap to the production domain.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Individual functions, utility classes, and Prisma hooks.
- **Tooling:** Jest and Vitest.
- **Target:** 80% code coverage.
- **Approach:** Mocking external dependencies (e.g., mocking the database response) to ensure tests are fast and deterministic.

### 7.2 Integration Testing
- **Focus:** The interaction between the API layer and the database.
- **Tooling:** Supertest and Testcontainers.
- **Approach:** Spinning up a real PostgreSQL instance in a Docker container, seeding it with test data, and executing API calls to verify that Row Level Security (RLS) and tenant isolation are functioning correctly.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "Login $\rightarrow$ View Alert $\rightarrow$ Acknowledge Alert").
- **Tooling:** Playwright.
- **Approach:** Simulating a real user browser session on the Staging environment. E2E tests are run against the full stack, including the Vercel deployment.

### 7.4 Penetration Testing
As per the security requirement, the production environment will undergo quarterly penetration testing.
- **Scope:** API vulnerability scanning (OWASP Top 10), SQL injection attempts, and JWT hijacking tests.
- **Frequency:** Every 90 days.
- **Remediation:** All "Critical" and "High" findings must be patched within 14 business days.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Next.js/Prisma stack | High | High | Negotiate timeline extension; implement weekly peer-learning sessions. | Quinn Nakamura |
| R-02 | Budget cut of 30% in next fiscal quarter | Medium | High | Dedicated budget owner to optimize tool spend and prioritize "Must-Have" features. | Quinn Nakamura |
| R-03 | Regulatory review delays quarterly release | Medium | Medium | Early submission of documentation to compliance officers. | Compliance Lead |
| R-04 | Performance degradation with multi-tenant RLS | Low | Medium | Implement advanced indexing and materialized views for heavy queries. | Ibrahim Santos |

**Risk Matrix:**
- **Probability:** Low (1), Medium (2), High (3)
- **Impact:** Low (1), Medium (2), High (3)
- **Score:** Prob $\times$ Impact. Any score $\ge 6$ requires an active mitigation plan.

---

## 9. TIMELINE AND PHASES

The project is spread over 18 months, moving from Monolith to Microservices.

### Phase 1: Foundation & Core API (Months 1-6)
- **M1: Architecture Setup:** Initialize Next.js, Prisma, and Vercel pipeline.
- **M2: Tenant Isolation:** Implement RLS and Tenant management.
- **M3: Security Audit:** **(Target: 2025-03-15)** Pass the external security audit.
- **Dependency:** Budget approval for the critical security tool purchase.

### Phase 2: Feature Expansion & Beta (Months 7-12)
- **M4: Audit Trail:** Deploy tamper-evident logging system.
- **M5: Beta Onboarding:** **(Target: 2025-05-15)** Onboard first paying customer.
- **M6: Advanced Search:** Implement full-text indexing and facets.
- **Dependency:** Successful completion of Phase 1 security audit.

### Phase 3: Optimization & Scale (Months 13-18)
- **M7: Final Demo:** **(Target: 2025-07-15)** Stakeholder demo and final sign-off.
- **M8: Data Import/Export:** Implement auto-detection tools.
- **M9: Offline Mode:** (If unblocked) Implement background sync.
- **Dependency:** Revenue targets from first customer.

---

## 10. MEETING NOTES (Sourced from Slack)

*Note: Per project dynamics, no formal minutes are kept. The following are synthesized from decision-making threads in the #umbra-dev channel.*

### Meeting 1: Tech Stack Debate (Thread: #tech-stack-final)
- **Participants:** Quinn, Ibrahim, Aaliya.
- **Discussion:** Aaliya suggested using MongoDB for logs to handle the variable nature of aerospace data. Ibrahim disagreed, arguing that the requirement for "Tamper-Evident Storage" and "Audit Trails" requires the ACID compliance and relational integrity of PostgreSQL.
- **Decision:** Stick with PostgreSQL. Use JSONB columns for variable log data to get the "best of both worlds."
- **Outcome:** Prisma schema updated to include `JSONB` for the `SecurityEvents.message` field.

### Meeting 2: Budget Crisis (Thread: #budget-alert)
- **Participants:** Quinn, Finance Dept.
- **Discussion:** Finance alerted Quinn that there is a high probability of a 30% budget cut next quarter. Quinn argued that this would jeopardize the "Offline-First" and "Search" features.
- **Decision:** Priority shifted. Multi-tenancy and Audit Trails are now "Non-Negotiable." Search and Offline mode are downgraded to "Nice to Have."
- **Outcome:** Roadmap adjusted; features 1, 3, and 5 moved to "Low Priority."

### Meeting 3: The "Communication Gap" (Thread: #team-sync)
- **Participants:** Umi, Ibrahim.
- **Discussion:** Umi expressed frustration that the UX designs for the faceted search are being ignored because the Lead Engineer (Ibrahim) and the PM (Quinn) are not speaking. Ibrahim claimed the designs are "unimplementable" given the current API constraints.
- **Decision:** Umi will create a "Technical UX" document that specifies the API calls needed for each UI component to bridge the gap.
- **Outcome:** A new Figma-to-API mapping document was created.

---

## 11. BUDGET BREAKDOWN

The budget is released in tranches based on the milestones in Section 9.

| Category | Annual Budget | Quarterly Allocation | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | $720,000 | $180,000 | 6 FTEs (Eng Manager, Leads, Juniors, QA) |
| **Infrastructure** | $48,000 | $12,000 | Vercel Enterprise, AWS RDS PostgreSQL, Redis |
| **Tools** | $15,000 | $3,750 | Snyk, Datadog, Figma, Jira |
| **Contingency** | $60,000 | $15,000 | Emergency scaling or specialized security consultants |
| **Total** | **$843,000** | **$210,750** | |

**Critical Blocker:** Budget approval for a "Critical Security Tool" (valued at $12,000) is still pending. This tool is required for the Milestone 1 security audit. Without it, the audit may fail.

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The project has inherited significant technical debt from the monolith. The following must be addressed during the 18-month transition:
- **Hardcoded Values:** Configuration values (API keys, database strings) are scattered across 40+ files. These must be moved to a centralized `.env` management system (e.g., Vercel Environment Variables).
- **Legacy API Wrappers:** The transition requires "shim" layers to allow the new microservices to communicate with the old monolith during the migration.
- **Unstructured Logs:** Legacy data is stored in an inconsistent format; the "Import" feature must include a cleanup script.

### Appendix B: Penetration Testing Checklist
The quarterly penetration tests will specifically target the following areas:
1. **Tenant Escape:** Attempting to access `Tenant B` data using a `Tenant A` token.
2. **Hash Collision:** Attempting to modify an audit log and recalculate the hash chain to hide an action.
3. **Bypass Auth:** Testing if `/api/v1/audit/logs` can be accessed without a valid JWT.
4. **Resource Exhaustion:** Testing the "Search" endpoint with extremely large queries to see if it crashes the database (DoS attack).