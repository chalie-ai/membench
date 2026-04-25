Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). It is designed as the "Single Source of Truth" for the Quorum development team.

***

# PROJECT SPECIFICATION: QUORUM
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / Baseline  
**Company:** Duskfall Inc.  
**Project Lead:** Devika Santos (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Quorum represents a strategic pivot for Duskfall Inc., moving from a legacy monolithic healthcare platform to a modern, scalable, micro-frontend architecture. The healthcare industry is currently undergoing a digital transformation where speed of iteration and reliability are paramount. Quorum is not merely a "rewrite" but a modernization effort designed to decouple business logic, improve developer velocity, and ensure that the platform can scale to meet 10x current capacity.

### 1.2 Business Justification
The legacy system has become a bottleneck for growth. With a monolithic codebase, deployment cycles are slow, and a single bug in the billing module can bring down the patient portal. Furthermore, the existing infrastructure cannot support the projected growth in user acquisition. By transitioning to a micro-frontend architecture utilizing TypeScript, Next.js, and Vercel, Duskfall Inc. will reduce the "Time to Market" for new features from months to weeks.

The strategic goal is to transition the entire ecosystem over an 18-month window, ensuring zero downtime for existing healthcare providers and patients. The move to a shared-infrastructure multi-tenant model will reduce operational overhead while maintaining strict data isolation.

### 1.3 ROI Projection and Success Metrics
Duskfall Inc. has allocated a total budget of $3,000,000 for this initiative. This is a high-visibility project with direct executive oversight. The return on investment (ROI) is calculated based on two primary success metrics:
1. **Revenue Growth:** The project is expected to generate $500,000 in new revenue attributed specifically to Quorum’s improved UX and new feature sets within the first 12 months post-launch.
2. **Security and Stability:** A target of zero critical security incidents in the first year. Reducing downtime and preventing data breaches in the healthcare sector avoids catastrophic regulatory fines and reputational damage.

The ROI is further bolstered by the reduction in "developer friction." By moving to a micro-frontend model, the 12-person cross-functional team can operate independently, reducing the cost of coordination and accelerating the delivery of high-value features.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Quorum employs a **Micro-Frontend (MFE) Architecture**. Unlike traditional SPAs, Quorum breaks the UI into independent fragments owned by different sub-teams. This prevents the "monolithic frontend" problem where a change in the "Patient Profile" page could accidentally break the "Scheduling" page.

The stack is standardized on:
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS.
- **Backend/API:** Next.js API Routes (Edge Runtime) and independent microservices.
- **ORM:** Prisma.
- **Database:** PostgreSQL (managed via Vercel Postgres / Neon).
- **Deployment:** Vercel.

### 2.2 System Diagram (ASCII Representation)

```text
[ Client Layer: Mobile App / Web ]
       |
       v
[ Vercel Edge Network / CDN ]
       |
       +-----------------------+-----------------------+
       |                       |                       |
 [ MFE: Patient Portal ] [ MFE: Provider Dashboard ] [ MFE: Admin Tools ]
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                    [ API Gateway / Route Handler ]
                               |
       +-----------------------+-----------------------+
       |                       |                       |
 [ Auth Service ]       [ Data Sync Service ]    [ Analytics Service ]
       |                       |                       |
       v                       v                       v
 [ PostgreSQL ] <------> [ Redis Cache ] <------> [ S3 Storage ]
 (Multi-tenant)          (Rate Limiting)          (Exports/Imports)
```

### 2.3 Data Flow and State Management
State is managed locally within MFEs using React Context and Zustand for lightweight global state. For the "Offline-First" requirement, Quorum utilizes IndexedDB for client-side persistence, which syncs with the PostgreSQL backend via a background synchronization worker.

### 2.4 Infrastructure Strategy
Duskfall Inc. leverages a "Shared Infrastructure" model. While data is logically isolated per tenant (using `tenant_id` partitioning), the compute resources (Vercel functions) are shared to maximize cost-efficiency and simplify deployment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:**
Healthcare providers often operate in "dead zones" (e.g., basement wards or rural clinics) where connectivity is intermittent. Quorum must allow users to continue inputting patient data, updating records, and viewing cached schedules without an active internet connection.

**Detailed Functional Requirements:**
- **Local Persistence:** Every write operation must be first committed to an IndexedDB store on the device.
- **Conflict Resolution:** The system shall use a "Last-Write-Wins" (LWW) strategy by default, but critical clinical fields will require a "Manual Merge" prompt if a conflict is detected during sync.
- **Background Sync Worker:** Using Service Workers, the app will detect when the network status returns to `online`. It will then trigger a sequential upload of the pending queue.
- **Visual Indicators:** A "Syncing..." status bar must be visible when the app is reconciling local data with the server.
- **Priority Queue:** Critical alerts (e.g., emergency patient updates) must be synced before routine administrative changes.

**Technical Approach:**
The team will implement a "Write-Ahead Log" (WAL) in the browser. Each transaction is assigned a UUID and a timestamp. When the sync worker activates, it posts these transactions to the `/api/sync` endpoint in batches of 50 to avoid overloading the server.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Description:**
To protect the shared infrastructure from "noisy neighbor" syndrome—where one tenant's aggressive API usage degrades performance for all others—a robust rate-limiting layer is required.

**Detailed Functional Requirements:**
- **Tiered Limiting:** Rates will be set based on the tenant's subscription level (e.g., Basic: 100 req/min, Premium: 1,000 req/min).
- **Sliding Window Algorithm:** Implement a sliding window counter using Redis to prevent bursts of traffic at the start of a new minute.
- **Analytics Dashboard:** The Admin MFE must display a real-time graph of API usage per tenant, highlighting those hitting their limits.
- **HTTP 429 Response:** When a limit is reached, the API must return a `429 Too Many Requests` status with a `Retry-After` header.

**Technical Approach:**
A middleware layer in Next.js will intercept all requests. It will extract the `tenant_id` from the JWT and query Redis. If the count exceeds the threshold, the request is terminated before reaching the business logic. *Note: This is currently blocked due to a missing Redis cluster configuration in the staging environment.*

### 3.3 Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** In Progress

**Description:**
Onboarding new clinics requires migrating data from legacy systems. Quorum must support importing patient records from various formats without requiring the user to manually specify the file type.

**Detailed Functional Requirements:**
- **Auto-Detection:** The system must analyze the first 1KB of an uploaded file to determine if it is CSV, JSON, or XML.
- **Schema Mapping:** A UI must allow users to map their legacy columns (e.g., "Patient_Name") to Quorum fields (e.g., "fullName").
- **Asynchronous Processing:** Large imports (>10MB) must be processed as background jobs to avoid timing out the HTTP request.
- **Export Options:** Users can export their data in JSON or CSV format for portability and backup.

**Technical Approach:**
The backend will use a "Strategy Pattern" for parsers. Depending on the detected mime-type, the system will instantiate a `CsvParser`, `JsonParser`, or `XmlParser`. The processed data will be staged in a `temporary_imports` table for review before being merged into the primary patient tables.

### 3.4 Customer-Facing API (Versioning & Sandbox)
**Priority:** Low (Nice to Have) | **Status:** In Progress

**Description:**
To allow third-party healthcare integrations, Quorum will provide a public API. To ensure stability, this API must be versioned and include a safe environment for testing.

**Detailed Functional Requirements:**
- **Semantic Versioning:** The API will be accessed via `/api/v1/...`. When breaking changes occur, `/api/v2/` will be released, and v1 will be deprecated after 6 months.
- **Sandbox Environment:** A separate database instance where developers can test API calls without affecting real patient data.
- **API Key Management:** A self-service portal for customers to generate, rotate, and revoke API keys.
- **Documentation:** Auto-generated Swagger/OpenAPI documentation.

**Technical Approach:**
We will use a dedicated route group in Next.js (`/api/v1`) to isolate public endpoints from internal application endpoints. The sandbox environment will be a mirrored deployment of the production stack but pointed to a `sandbox_db` PostgreSQL instance.

### 3.5 Multi-tenant Data Isolation (Shared Infrastructure)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
As a healthcare application, data leakage between different clinics is a catastrophic failure. Quorum must ensure strict isolation while utilizing a shared PostgreSQL instance to keep costs low.

**Detailed Functional Requirements:**
- **Row-Level Security (RLS):** Use PostgreSQL RLS policies to ensure that a query can only return rows where the `tenant_id` matches the authenticated user's tenant.
- **Tenant Context:** Every request must be wrapped in a tenant context derived from the session token.
- **Shared Schema:** All tenants share the same tables, but are separated by the `tenant_id` column.
- **Audit Logging:** Every access to a patient record must be logged with the `tenant_id` and `user_id` for compliance.

**Technical Approach:**
Prisma will be extended with a middleware that automatically appends a `where: { tenant_id: currentTenant }` clause to every find, update, and delete operation. Additionally, we will implement a "Safety Check" interceptor that throws a 500 error if a query is attempted without a `tenant_id` filter.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Header: `Authorization: Bearer <JWT>`.

### 4.1 Patient Management
**GET `/api/v1/patients`**
- **Description:** Retrieve a list of patients for the current tenant.
- **Request Params:** `limit` (int), `offset` (int), `search` (string).
- **Success Response (200 OK):**
  ```json
  {
    "data": [
      { "id": "p_123", "fullName": "John Doe", "dob": "1985-05-12" },
      { "id": "p_456", "fullName": "Jane Smith", "dob": "1990-11-20" }
    ],
    "pagination": { "total": 150, "next": "/api/v1/patients?offset=20" }
  }
  ```

**POST `/api/v1/patients`**
- **Description:** Create a new patient record.
- **Request Body:** `{ "fullName": "string", "dob": "ISO-Date", "gender": "string" }`
- **Success Response (201 Created):**
  ```json
  { "id": "p_789", "status": "created", "createdAt": "2023-10-24T10:00:00Z" }
  ```

### 4.2 Scheduling & Appointments
**GET `/api/v1/appointments`**
- **Description:** Fetch all appointments for the authenticated provider.
- **Success Response (200 OK):**
  ```json
  {
    "appointments": [
      { "id": "app_1", "patientId": "p_123", "time": "2023-11-01T10:00Z", "status": "confirmed" }
    ]
  }
  ```

**PATCH `/api/v1/appointments/{id}`**
- **Description:** Update appointment status (e.g., "cancelled", "completed").
- **Request Body:** `{ "status": "completed" }`
- **Success Response (200 OK):**
  ```json
  { "id": "app_1", "status": "completed", "updatedAt": "2023-10-24T12:00:00Z" }
  ```

### 4.3 Data Synchronization
**POST `/api/sync`**
- **Description:** Bulk upload of offline changes.
- **Request Body:**
  ```json
  {
    "batchId": "sync_999",
    "changes": [
      { "action": "UPDATE", "table": "patients", "id": "p_123", "data": { "phone": "555-0123" }, "timestamp": 1698144000 }
    ]
  }
  ```
- **Success Response (200 OK):**
  ```json
  { "processed": 1, "conflicts": 0, "status": "synchronized" }
  ```

### 4.4 System Administration
**GET `/api/admin/usage`**
- **Description:** Returns API usage metrics for a specific tenant.
- **Request Params:** `tenantId` (string).
- **Success Response (200 OK):**
  ```json
  { "tenantId": "t_001", "requestsPerMinute": 85, "limit": 100, "utilization": "85%" }
  ```

**POST `/api/admin/export`**
- **Description:** Triggers a full data export for a tenant.
- **Request Body:** `{ "tenantId": "t_001", "format": "JSON" }`
- **Success Response (202 Accepted):**
  ```json
  { "jobId": "job_abc123", "status": "queued", "estimatedCompletion": "5 minutes" }
  ```

**GET `/api/admin/export/{jobId}`**
- **Description:** Check status and get download link for export.
- **Success Response (200 OK):**
  ```json
  { "jobId": "job_abc123", "status": "completed", "downloadUrl": "https://s3.duskfall.com/export_123.json" }
  ```

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL. The schema is designed for multi-tenancy using a `tenant_id` on every primary table.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `tenant_id` | N/A | `name`, `subscription_tier`, `createdAt` | Root entity for data isolation. |
| `Users` | `user_id` | `tenant_id` | `email`, `password_hash`, `role` (Admin/Doc/Nurse) | System users belonging to a tenant. |
| `Patients` | `patient_id` | `tenant_id` | `fullName`, `dob`, `gender`, `address` | Core patient demographic data. |
| `Appointments` | `app_id` | `tenant_id`, `patient_id`, `user_id` | `startTime`, `endTime`, `status`, `notes` | Scheduling data. |
| `ClinicalNotes` | `note_id` | `tenant_id`, `patient_id`, `user_id` | `content`, `category`, `createdAt` | Medical records/notes. |
| `AuditLogs` | `log_id` | `tenant_id`, `user_id` | `action`, `resourceId`, `timestamp`, `ipAddress` | Compliance tracking for all data access. |
| `SyncQueue` | `sync_id` | `tenant_id`, `user_id` | `payload`, `status` (pending/done), `retryCount` | Tracks offline sync operations. |
| `ApiKeys` | `key_id` | `tenant_id` | `hashed_key`, `permissions`, `expiresAt` | Keys for the customer-facing API. |
| `ImportJobs` | `job_id` | `tenant_id` | `fileName`, `status`, `rowCount`, `errorLog` | Tracking for data migration. |
| `UsageMetrics` | `metric_id` | `tenant_id` | `timestamp`, `requestCount`, `errorCount` | Daily usage stats for rate limiting. |

### 5.2 Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many (A tenant has many users).
- **Tenants $\rightarrow$ Patients:** One-to-Many (A tenant manages many patients).
- **Patients $\rightarrow$ Appointments:** One-to-Many (A patient has multiple appointments).
- **Users $\rightarrow$ Appointments:** One-to-Many (A provider manages multiple appointments).
- **Patients $\rightarrow$ ClinicalNotes:** One-to-Many (A patient has a history of notes).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and initial integration.
- **Deployment:** Continuous Deployment (CD) from the `develop` branch.
- **Database:** Shared development database with mock data.
- **Access:** All team members.

#### 6.1.2 Staging (Stage)
- **Purpose:** Final QA, User Acceptance Testing (UAT), and stability verification.
- **Deployment:** Triggered by a merge to the `release` branch.
- **Database:** A sanitized clone of production data.
- **Access:** Team members and select Beta customers.

#### 6.1.3 Production (Prod)
- **Purpose:** Live healthcare operations.
- **Deployment:** Manual QA gate required. Only approved releases from Staging are promoted.
- **Database:** High-availability PostgreSQL cluster.
- **Access:** End customers and SREs only.

### 6.2 The Deployment Pipeline
Every deployment follows a strict 2-day turnaround process:
1. **Day 1: Merge & Stage:** Feature is merged into the `release` branch and deployed to Staging.
2. **Day 1: QA Cycle:** Paz Stein (DevOps) and the team perform manual regression testing and smoke tests.
3. **Day 2: Approval & Prod:** Once the "QA Gate" is signed off in Slack, the build is promoted to Production via Vercel's production alias.

### 6.3 Infrastructure Tooling
- **Hosting:** Vercel (Frontend and Serverless Functions).
- **Database:** PostgreSQL (Neon/Vercel Postgres).
- **Caching:** Redis (Upstash) for rate limiting.
- **CI/CD:** GitHub Actions for linting, type-checking, and deployment triggers.

---

## 7. TESTING STRATEGY

To ensure "zero critical security incidents," Quorum employs a three-tiered testing pyramid.

### 7.1 Unit Testing
- **Scope:** Individual functions, Prisma hooks, and utility helpers.
- **Tooling:** Jest and Vitest.
- **Requirement:** Minimum 80% code coverage on business logic.
- **Example:** Testing the `calculateAge` helper or the `rateLimitCheck` logic.

### 7.2 Integration Testing
- **Scope:** Interaction between the API and the database, and between MFEs.
- **Tooling:** Supertest and Prisma Mock.
- **Focus:** Ensuring that `tenant_id` filters are correctly applied to all queries and that the sync worker correctly handles database commits.
- **Requirement:** All "Critical" priority features must have end-to-end integration tests.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "Create Patient $\rightarrow$ Schedule Appointment $\rightarrow$ Add Note").
- **Tooling:** Playwright.
- **Focus:** Testing the offline-first mode by simulating network disconnection in the browser and verifying that data persists and eventually syncs.

### 7.4 Security Testing
- **Penetration Testing:** Conducted quarterly by an external security firm.
- **Static Analysis:** Snyk is integrated into the GitHub pipeline to detect vulnerable dependencies.
- **Manual Review:** Devika Santos reviews all changes to the authentication and multi-tenancy middleware.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | **Scope Creep:** Stakeholders adding 'small' features continuously. | High | Medium | **Parallel-Path:** Create a rapid prototype of the requested feature while continuing the primary build. If the prototype proves value, it is scheduled for the next sprint; otherwise, it is rejected. |
| R2 | **Performance Gap:** 10x capacity reqs with no extra budget. | Medium | High | **Board Escalation:** Raise as a formal blocker in the next board meeting. Present data showing the current infrastructure limits vs. projected load. |
| R3 | **Data Leakage:** Failure in multi-tenant isolation. | Low | Critical | **Double-Layer Defense:** Implement both Prisma middleware and PostgreSQL RLS. Quarterly third-party security audits. |
| R4 | **Sync Conflicts:** High volume of overlapping offline edits. | Medium | Medium | **LWW Strategy:** Default to Last-Write-Wins but implement a "Conflict Flag" for medical records requiring manual human review. |
| R5 | **Tech Debt:** Hardcoded config values in 40+ files. | High | Low | **Config Migration:** Systematic migration to a centralized `.env` and `config.ts` architecture over 3 sprints. |

**Risk Matrix:**
- **Critical:** Immediate action required.
- **High:** Priority mitigation.
- **Medium:** Monitor and manage.
- **Low:** Acceptable risk.

---

## 9. TIMELINE & MILESTONES

The project is an 18-month effort. The current phase focuses on the transition from the monolith.

### 9.1 Phase Overview (Gantt Style)

**Phase 1: Foundation (Months 1–6)**
- [X] Infrastructure setup (Vercel, Postgres).
- [X] Multi-tenant core logic.
- [ ] Offline-first design (Current).
- [ ] Initial API Rate Limiting logic.

**Phase 2: Core Migration (Months 7–12)**
- [ ] Data import/export tools.
- [ ] Migration of Patient and Appointment modules.
- [ ] Internal Alpha Release.

**Phase 3: Optimization & Launch (Months 13–18)**
- [ ] Customer-facing API rollout.
- [ ] Full monolith decommissioning.
- [ ] Final security audit.

### 9.2 Key Milestones

| Milestone | Deliverable | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| **M1** | Internal Alpha Release | 2025-04-15 | Completion of Offline-First & Multi-tenancy. |
| **M2** | Post-launch Stability Confirmed | 2025-06-15 | 30 days of 99.9% uptime in production. |
| **M3** | Security Audit Passed | 2025-08-15 | Completion of quarterly pen-test. |

---

## 10. MEETING NOTES

*Note: These notes are extracted from the shared 200-page running document. The document remains unsearchable and chronological.*

### Meeting 1: Architecture Alignment
**Date:** 2023-11-12  
**Attendees:** Devika, Paz, Kaia, Chandra  
**Discussion:**
- Devika proposed the Micro-frontend (MFE) approach to avoid the "big ball of mud" experienced in the legacy monolith.
- Paz expressed concern regarding deployment complexity. Devika countered that Vercel’s preview deployments would mitigate this.
- Kaia noted that users in the field are complaining about the "loading spinner" when the network drops.
- **Decision:** We will commit to "Offline-First" as a launch blocker. This means no release until the background sync is rock solid.
- **Action:** Devika to draft the sync protocol.

### Meeting 2: The "Small Feature" Storm
**Date:** 2023-12-05  
**Attendees:** Devika, Paz, Kaia, Stakeholders (Execs)  
**Discussion:**
- Stakeholders requested a "Patient Chat" feature and "AI Diagnosis" as "small additions."
- Devika reminded the team that the current priority is the 10x performance requirement and multi-tenancy.
- There was a tension regarding the infrastructure budget; the board is unwilling to increase the $3M cap.
- **Decision:** Use the "Parallel-Path" mitigation for the Chat feature. We will prototype it in a separate repo without slowing down the core build.
- **Action:** Devika to flag the performance/budget gap as a blocker for the next board meeting.

### Meeting 3: Sync Implementation Sync
**Date:** 2024-01-20  
**Attendees:** Devika, Paz, Chandra  
**Discussion:**
- Chandra (Intern) found that hardcoded config values are scattered across 42 different files, making it impossible to switch between staging and prod easily.
- Paz suggested a global `config.ts` file that reads from `process.env`.
- Discussion on the `api/sync` endpoint: should it be a single endpoint or multiple?
- **Decision:** Single endpoint `/api/sync` using a JSON array of "changes" to reduce HTTP overhead.
- **Action:** Chandra to start the audit of all hardcoded values and migrate them to `.env`.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000  
**Duration:** 18 Months

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 12-person team (including Tech Lead, DevOps, UX, and Intern). |
| **Infrastructure** | 15% | $450,000 | Vercel Enterprise, PostgreSQL (Neon), Redis (Upstash), S3. |
| **Tools & Security** | 10% | $300,000 | Snyk, Playwright Cloud, Quarterly Pen-Testing fees. |
| **Contingency** | 10% | $300,000 | Reserved for emergency scaling or critical bug fixes. |

**Personnel Detail:**
- Tech Lead (Devika Santos): High-level architecture and review.
- DevOps (Paz Stein): Pipeline and Infrastructure.
- UX Researcher (Kaia Costa): User journeys and usability.
- Intern (Chandra Oduya): Tech debt cleanup and unit tests.
- 8x Full-stack Engineers (TypeScript/Next.js).

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (Offline Sync)
When a record is synced, the server compares the `timestamp` of the incoming change with the `updatedAt` timestamp in the PostgreSQL database.
1. **T_client > T_server:** The server accepts the change (Last-Write-Wins).
2. **T_client < T_server:** The change is rejected, and the client is sent the current server state.
3. **Medical Field Override:** If the field is marked as `critical` (e.g., `medication_dosage`), the record is flagged as `CONFLICT` and moved to a review queue for the doctor, regardless of the timestamp.

### Appendix B: Tenant Isolation Verification Process
To verify that data isolation is working, Paz Stein will run a "Cross-Tenant Leak Test" every sprint:
1. Create two tenants (Tenant A and Tenant B).
2. Create a patient record in Tenant A.
3. Attempt to access that patient record using a JWT issued for Tenant B.
4. **Success Criteria:** The API must return `404 Not Found` or `403 Forbidden`. If a `200 OK` is returned, the deployment is immediately rolled back and a "P0" incident is opened.