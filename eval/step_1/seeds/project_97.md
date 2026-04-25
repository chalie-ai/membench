# PROJECT SPECIFICATION DOCUMENT: PROJECT AQUEDUCT
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 26, 2023  
**Company:** Crosswind Labs  
**Project Lead:** Nadira Kim (CTO)  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Aqueduct is a specialized supply chain management (SCM) system engineered specifically for the legal services industry. Unlike traditional SCMs designed for physical goods, Aqueduct treats "legal deliverables," "expert witness procurement," and "document discovery flows" as the primary units of supply. Crosswind Labs aims to revolutionize how large-scale legal firms manage the procurement of external legal resources, ensuring a seamless flow of intellectual capital from acquisition to final court submission.

**Business Justification**  
The legal services industry currently relies on a fragmented mix of antiquated ERPs, email chains, and manual spreadsheets to manage their supply chain of external counsel and consultants. This leads to significant leakage in billable hours, missed deadlines in discovery, and a lack of transparency in vendor performance. Aqueduct addresses this by providing a centralized, high-performance hub for managing the lifecycle of legal service procurement.

As a "moonshot" R&D project, Aqueduct is designed to test a hypothesis: *Can a streamlined, modern SCM framework reduce operational overhead in legal procurement by 20%?* While the ROI is currently uncertain due to the novelty of the application in this sector, the project carries strong executive sponsorship. The strategic goal is to pivot Crosswind Labs from a generalist software house into a specialized legal-tech powerhouse.

**ROI Projection**  
The financial target for Aqueduct is aggressive but focused. The primary success metric is the generation of **$500,000 in new revenue** attributed directly to the product within 12 months of the production launch (Target: July 15, 2025). 

The projected ROI is calculated based on a tiered subscription model targeting "Big Law" firms. At a projected price point of $2,500/month per firm, the product requires only 17 active enterprise clients to hit the revenue target. Given the efficiency gains—estimated at 15-20% reduction in procurement leakage—the value proposition for the client is an estimated $100k+ in annual savings per firm, making the $30k annual subscription a high-value investment. With a shoestring budget of $150,000, the project is lean; if the revenue target is met, the ROI on initial capital expenditure will be approximately 233% within the first year post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Aqueduct utilizes a **Clean Monolith** architecture. We have eschewed microservices to avoid the "distributed monolith" trap, given our small team size (12 people). Instead, we enforce strict module boundaries within a single TypeScript/Next.js codebase. Each module (e.g., `Procurement`, `Billing`, `Compliance`) has its own domain logic and data access layer, ensuring that if the system needs to be split into microservices in the future, the boundaries are already predefined.

### 2.2 The Tech Stack
- **Frontend/Backend Framework:** Next.js 14 (App Router) with TypeScript.
- **ORM:** Prisma (with targeted raw SQL overrides for performance).
- **Database:** PostgreSQL 15 (Managed via AWS RDS for EU residency).
- **Deployment:** Vercel (Frontend/Edge) and Kubernetes (Backend/Workers) via GitLab CI.
- **State Management:** React Query for server-state; Zustand for client-state.
- **Infrastructure:** Vercel for the edge, AWS EKS for heavy-lifting background jobs.

### 2.3 System Diagram (ASCII)

```text
[ User Browser ] <---> [ Vercel Edge Network ] <---> [ Next.js Application ]
                                                             |
                                                             | (Module Boundaries)
                                      _______________________|_______________________
                                     |                       |                       |
                            [ Procurement Mod ]     [ Compliance Mod ]      [ API Gateway Mod ]
                                     |                       |                       |
                                     |_______________________|_______________________|
                                                             |
                                                     [ Prisma ORM Layer ]
                                                             |
                                          ___________________|___________________
                                         |                                        |
                                  [ PostgreSQL DB ]                      [ S3 Bucket / CDN ]
                                  (EU-Central-1)                         (Virus Scanned)
                                         |
                                [ GitLab CI/CD Pipeline ] ---> [ Kubernetes Cluster ]
```

### 2.4 Security & Data Residency
Due to the nature of legal data, the system must be **GDPR and CCPA compliant**. 
- **Data Residency:** All production databases and backups are pinned to the `eu-central-1` (Frankfurt) region.
- **Encryption:** AES-256 at rest; TLS 1.3 in transit.
- **Access Control:** Role-Based Access Control (RBAC) implemented at the middleware level.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Integrated Feature Flags)
**Priority:** Medium | **Status:** Not Started

**Description:**  
The A/B testing framework is not a standalone tool but is baked directly into the existing feature flag system. The goal is to allow Nadira and the product team to toggle features for specific percentages of the user base to measure the impact on procurement velocity.

**Functional Specifications:**
- **Bucket Assignment:** When a user logs in, the system assigns them to a "bucket" (A or B) based on a deterministic hash of their `userId` and the `experimentId`. This ensures consistency across sessions.
- **Flag Integration:** Integration with the Next.js middleware to serve different UI components based on the flag state.
- **Telemetry:** Every interaction within an A/B test must be logged with the `experimentId` and `variantId` to the analytics table.
- **Rollout Controls:** A management dashboard allowing the CTO to shift the traffic split (e.g., from 10% B / 90% A to 50% B / 50% A) without a code redeploy.

**Technical Implementation:**
The framework will use a Redis cache to store active experiments to avoid hitting the main PostgreSQL DB on every page load. The logic will reside in a `useExperiment` hook that returns the active variant.

---

### 3.2 Real-time Collaborative Editing (Conflict Resolution)
**Priority:** Low | **Status:** Not Started

**Description:**  
Legal procurement documents often require simultaneous input from multiple partners. This feature allows multiple users to edit a "Procurement Request" or "Service Agreement" in real-time.

**Functional Specifications:**
- **Cursor Tracking:** Users must see the presence and cursor position of other active editors.
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to handle simultaneous edits to the same paragraph.
- **State Sync:** Real-time updates via WebSockets.
- **Version History:** A "Snapshot" system that allows users to revert to any previous state of the document.

**Technical Implementation:**
We will evaluate `yjs` or `automerge` for the CRDT implementation. To avoid overloading the main Next.js server, we will deploy a dedicated Node.js WebSocket server on Kubernetes to handle the synchronization traffic, which will then periodically persist the "final" state back to PostgreSQL via Prisma.

---

### 3.3 Customer-Facing API (Versioning & Sandbox)
**Priority:** Low | **Status:** Complete

**Description:**  
To allow large legal firms to integrate Aqueduct into their own internal portals, a robust, versioned API is required.

**Functional Specifications:**
- **Versioning:** URI-based versioning (e.g., `/api/v1/...`). Version 1 is currently locked.
- **Sandbox Environment:** A mirrored environment (`sandbox.aqueduct.crosswind.io`) where users can test API calls against mock data without affecting production records.
- **Authentication:** API Key-based authentication with rotating secrets.
- **Rate Limiting:** Tiered rate limiting based on the firm's subscription level (100 requests/min for Standard, 1,000 for Enterprise).

**Technical Implementation:**
The API is built using Next.js Route Handlers. The sandbox is a separate Kubernetes namespace that shares the codebase but points to a dedicated `sandbox_db` PostgreSQL instance.

---

### 3.4 File Upload with Virus Scanning & CDN
**Priority:** Low | **Status:** In Review

**Description:**  
Legal services involve the transfer of massive amounts of sensitive PDFs and Word documents. These must be scanned for malware and distributed efficiently.

**Functional Specifications:**
- **Upload Pipeline:** Files are uploaded to a "quarantine" S3 bucket.
- **Scanning:** An AWS Lambda trigger invokes a ClamAV-based scanning service. If a virus is detected, the file is deleted and the user is notified.
- **CDN Distribution:** Once cleared, files are moved to a "production" bucket and served via CloudFront with signed URLs (expiring every 15 minutes).
- **Integrity:** SHA-256 checksums are generated for every file to ensure data integrity during transit.

**Technical Implementation:**
The frontend uses `Uppy.js` for resumable uploads. The backend manages the S3 presigned URLs. The "In Review" status refers to the current legal audit of the ClamAV scanning latency.

---

### 3.5 Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** Blocked

**Description:**  
Legal professionals often work in environments with poor connectivity (e.g., courthouses). Aqueduct must allow them to continue working offline.

**Functional Specifications:**
- **Local Persistence:** Use of IndexedDB to store the current working state of the application.
- **Queueing:** All mutations (POST/PUT/DELETE) are queued in a local "Outbox" when offline.
- **Background Sync:** Use of Service Workers to detect when the connection is restored and flush the Outbox.
- **Conflict Detection:** If a record was changed on the server while the user was offline, the system must trigger a "Manual Resolve" prompt upon reconnection.

**Technical Implementation:**
Currently blocked by the Legal Review of the Data Processing Agreement (DPA) regarding the storage of sensitive legal data on local device storage (IndexedDB). If approved, we will implement `TanStack Query`'s offline mutations.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require an `Authorization: Bearer <TOKEN>` header. Base URL: `https://api.aqueduct.crosswind.io/v1`

### 4.1 `GET /procurement/requests`
- **Description:** Retrieve a list of all supply chain requests.
- **Query Params:** `status` (filter), `page` (pagination).
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "req_123", "title": "Expert Witness - Forensic Accounting", "status": "PENDING", "budget": 5000 }
  ],
  "pagination": { "total": 1, "page": 1 }
}
```

### 4.2 `POST /procurement/requests`
- **Description:** Create a new procurement request.
- **Request Body:** `{ "title": string, "description": string, "budget": number, "deadline": "ISO8601" }`
- **Response (201 Created):**
```json
{ "id": "req_124", "status": "CREATED", "createdAt": "2023-10-26T10:00:00Z" }
```

### 4.3 `GET /vendors/{vendorId}/performance`
- **Description:** Get performance metrics for a specific legal vendor.
- **Response (200 OK):**
```json
{
  "vendorId": "ven_99",
  "score": 4.8,
  "completedDeliverables": 12,
  "averageTurnaroundDays": 4.2
}
```

### 4.4 `PATCH /vendors/{vendorId}/status`
- **Description:** Update vendor status (e.g., Active to Blacklisted).
- **Request Body:** `{ "status": "BLACKLISTED", "reason": "Conflict of Interest" }`
- **Response (200 OK):** `{ "status": "updated" }`

### 4.5 `GET /compliance/audit-log`
- **Description:** Retrieve a GDPR-compliant audit trail of all data access.
- **Response (200 OK):**
```json
{
  "logs": [
    { "timestamp": "...", "userId": "user_1", "action": "READ", "resource": "doc_456" }
  ]
}
```

### 4.6 `POST /files/upload-url`
- **Description:** Request a presigned URL for file upload.
- **Request Body:** `{ "filename": "evidence_01.pdf", "mimeType": "application/pdf" }`
- **Response (200 OK):**
```json
{ "uploadUrl": "https://s3.eu-central-1.amazonaws.com/...", "fileId": "file_789" }
```

### 4.7 `GET /billing/invoices`
- **Description:** Retrieve all pending invoices for procurement items.
- **Response (200 OK):**
```json
{
  "invoices": [
    { "id": "inv_001", "amount": 1200.00, "status": "UNPAID", "dueDate": "2023-11-15" }
  ]
}
```

### 4.8 `DELETE /sandbox/reset`
- **Description:** Wipe all data in the sandbox environment (Admin only).
- **Response (204 No Content):** `Empty`

---

## 5. DATABASE SCHEMA

**Database Engine:** PostgreSQL 15  
**ORM:** Prisma  
**Consistency:** Strong Consistency (ACID)

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `Users` | `userId` (UUID) | `email`, `passwordHash`, `role`, `firmId` | Many-to-One `Firms` |
| `Firms` | `firmId` (UUID) | `firmName`, `region`, `subscriptionTier` | One-to-Many `Users` |
| `Vendors` | `vendorId` (UUID) | `companyName`, `specialty`, `rating`, `status` | One-to-Many `Deliverables` |
| `Requests` | `requestId` (UUID) | `title`, `budget`, `status`, `creatorId` | Many-to-One `Users` |
| `Deliverables` | `delId` (UUID) | `requestId`, `vendorId`, `fileId`, `dueDate` | Many-to-One `Requests`, `Vendors` |
| `Files` | `fileId` (UUID) | `s3Path`, `checksum`, `scanStatus`, `isVirusFree` | One-to-One `Deliverables` |
| `AuditLogs` | `logId` (BigInt) | `userId`, `action`, `timestamp`, `ipAddress` | Many-to-One `Users` |
| `FeatureFlags` | `flagId` (String) | `key`, `isEnabled`, `percentageRollout` | N/A |
| `Experiments` | `expId` (UUID) | `flagId`, `variantA_Config`, `variantB_Config` | Many-to-One `FeatureFlags` |
| `Invoices` | `invId` (UUID) | `delId`, `amount`, `status`, `issuedDate` | Many-to-One `Deliverables` |

### 5.2 Relationship Detail
- **Firm $\rightarrow$ User:** A Law Firm has many employees (Users). Each User belongs to exactly one Firm.
- **Request $\rightarrow$ Deliverable:** A Procurement Request can result in multiple Deliverables (e.g., one request for a "Case Review" might result in a "Summary Report" and a "Witness List").
- **Vendor $\rightarrow$ Deliverable:** A Vendor provides many Deliverables across various Requests.
- **Deliverable $\rightarrow$ Invoice:** Each single deliverable is tied to one invoice for billing clarity.

---

## 6. DEPLOYMENT & INFRASTRUCTURE

### 6.1 Environment Strategy

#### Development (`dev`)
- **URL:** `dev.aqueduct.crosswind.io`
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Shared Kubernetes namespace, ephemeral database.
- **Deployment:** Automatic deploy on every push to `develop` branch.

#### Staging (`staging`)
- **URL:** `staging.aqueduct.crosswind.io`
- **Purpose:** Pre-production QA, User Acceptance Testing (UAT).
- **Infrastructure:** Mirrors Production (AWS RDS EU-Central-1), sanitized data.
- **Deployment:** Triggered by Merge Request to `release` branch.

#### Production (`prod`)
- **URL:** `app.aqueduct.crosswind.io`
- **Purpose:** Live client traffic.
- **Infrastructure:** Full Kubernetes cluster with auto-scaling, Multi-AZ RDS, CloudFront CDN.
- **Deployment:** Rolling deployment via GitLab CI. Manual approval required from Nadira Kim.

### 6.2 CI/CD Pipeline
1. **Lint/Test Phase:** Runs `npm run lint` and `npm test` (Vitest).
2. **Build Phase:** Next.js build optimized for production.
3. **Security Scan:** Snyk scan for vulnerable dependencies.
4. **Deploy Phase:**
   - Update Kubernetes image tags.
   - Execute Prisma migrations (wrapped in a transaction).
   - Health check probe; if failed, automatic rollback to the previous stable image.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** Vitest.
- **Coverage Target:** 80% for domain logic (Services/Utils).
- **Focus:** Testing the logic of the A/B testing bucket assignment and the conflict resolution algorithms.

### 7.2 Integration Testing
- **Tool:** Playwright.
- **Focus:** Critical paths:
  - User Login $\rightarrow$ Create Request $\rightarrow$ Assign Vendor $\rightarrow$ Upload File.
  - API Sandbox $\rightarrow$ Endpoint Call $\rightarrow$ Database Verification.
- **Frequency:** Run on every merge request to `staging`.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress.
- **Focus:** High-level business flows. Specifically, the "Virus Scan" flow where a file is uploaded, scanned, and then made available via CDN.
- **Environment:** Performed exclusively in `staging`.

### 7.4 Performance Testing
- **Tool:** k6.
- **Target:** Handle 500 concurrent users with a p95 response time of < 200ms for API calls.
- **Note:** Special attention is paid to the raw SQL queries used in 30% of the system to ensure they outperform the Prisma ORM.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding 'small' features | High | High | Maintain a strict "Feature Freeze" window 4 weeks before milestones. Build a fallback architecture that allows modular additions without core rewrites. |
| **R2** | Key Architect leaving in 3 months | Medium | Critical | Engage an external consultant for an independent assessment of the architecture now. Ensure all architectural decisions are documented in GitLab Wiki. |
| **R3** | ORM Bypass (Technical Debt) | High | Medium | 30% of queries use raw SQL. Implement a rigorous "Migration Review" process where any schema change is manually checked against raw SQL queries. |
| **R4** | Legal Blockage (DPA) | Medium | High | Maintain a "Server-Only" fallback for the offline mode. If the DPA isn't signed, the offline-first mode is downgraded to "Read-Only Cached." |

**Impact Matrix:**
- **Critical:** Project stoppage or data breach.
- **High:** Significant delay in milestones or loss of revenue.
- **Medium:** Increased technical debt or minor performance dip.

---

## 9. TIMELINE

### 9.1 Phase Description

**Phase 1: Core Stabilization (Now $\rightarrow$ May 15, 2025)**
- **Focus:** Resolving the raw SQL migration risks and finalizing the file upload pipeline.
- **Dependency:** Legal review of DPA must be completed to unblock Offline-Mode.
- **Milestone 1:** Post-launch stability confirmed.

**Phase 2: Production Hardening (May 16 $\rightarrow$ July 15, 2025)**
- **Focus:** Full E2E testing, Security Audit (External), and final UI polish by Renzo Costa.
- **Dependency:** Successful completion of Milestone 1.
- **Milestone 2:** Production Launch.

**Phase 3: Optimization & Growth (July 16 $\rightarrow$ Sept 15, 2025)**
- **Focus:** A/B testing framework deployment and performance tuning.
- **Dependency:** Revenue data from initial launch.
- **Milestone 3:** Performance benchmarks met.

### 9.2 Gantt-Style Sequence
`[Jan-Mar]: API Finalization $\rightarrow$ [Mar-May]: Stability Testing $\rightarrow$ [May-Jul]: Hardening/Audit $\rightarrow$ [Jul 15]: LAUNCH $\rightarrow$ [Aug-Sep]: Perf Tuning`

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per project culture, formal notes are not taken. Decisions are captured in Slack threads. Below are the transcriptions of the three most critical decision-making threads.

### Thread 1: The ORM Debate
**Date:** 2023-11-12  
**Participants:** Nadira Kim, Lev Costa, Sage Nakamura  
**Discussion:**  
- *Sage:* "I'm seeing a lot of `prisma.$queryRaw` in the procurement module. Why aren't we using the ORM?"
- *Lev:* "Prisma is too slow for the complex joins we need for vendor performance scoring. The raw SQL is 4x faster."
- *Nadira:* "We can't sacrifice performance, but we can't have migrations breaking the app. Lev, you need to document every raw query in the `sql-map.md` file so we know what to update during migrations."
- **Decision:** Keep raw SQL for performance-critical queries; mandatory documentation in `sql-map.md`.

### Thread 2: Offline Mode Blockage
**Date:** 2023-12-05  
**Participants:** Nadira Kim, Renzo Costa, Legal Counsel (External)  
**Discussion:**  
- *Renzo:* "The UX for offline mode is ready, but I can't implement the sync logic if we don't know if we can store data locally."
- *Legal:* "We are still reviewing the DPA. Storing PII in IndexedDB on a lawyer's laptop might violate the EU data residency requirement if the laptop leaves the EU."
- *Nadira:* "Mark 'Offline-First' as **Blocked**. We don't move a single line of code on this until Legal signs off."
- **Decision:** Feature 5 (Offline Mode) moved to "Blocked" status.

### Thread 3: Budget Constraints
**Date:** 2024-01-20  
**Participants:** Nadira Kim, Executive Sponsor  
**Discussion:**  
- *Sponsor:* "The $150k is a hard cap. No more."
- *Nadira:* "Understood. I'm cutting the 'Real-time Collaborative Editing' to 'Low Priority' to save on dev hours. We'll focus on the API and File Scanning first."
- *Sponsor:* "Agreed. If we hit the $500k revenue target, I'll unlock more for the R&D phase."
- **Decision:** Re-prioritize features to protect the budget; Collaborative Editing downgraded to "Nice to have."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (USD)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $105,000 | 12-person team (Hybrid/Contract mix) |
| **Infrastructure** | 15% | $22,500 | AWS RDS, Vercel Enterprise, EKS |
| **Tools/Licenses** | 5% | $7,500 | GitLab Premium, Snyk, ClamAV licenses |
| **Contingency** | 10% | $15,000 | Reserved for external consultant (Risk R2) |

**Budgetary Control:** Every expenditure over $500 must be approved by Nadira Kim via Slack.

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Safety Protocol
Because 30% of the system bypasses the Prisma ORM, the following protocol is mandatory for all schema changes:
1. **Query Audit:** The developer must search the codebase for all `prisma.$queryRaw` calls.
2. **Impact Analysis:** Determine if a column rename or type change breaks the raw SQL.
3. **Shadow Deployment:** Run the migration on a shadow database with a copy of production data to verify that no query returns an error.
4. **Manual Verification:** Lev Costa must sign off on all raw SQL changes before they are merged into the `release` branch.

### Appendix B: Virus Scanning Workflow Detail
The file upload process follows this precise sequence:
1. **Client $\rightarrow$ API:** Request presigned URL (`POST /files/upload-url`).
2. **Client $\rightarrow$ S3:** Upload file to `s3://aqueduct-quarantine/`.
3. **S3 $\rightarrow$ Lambda:** S3 `ObjectCreated` event triggers the `VirusScanLambda`.
4. **Lambda $\rightarrow$ ClamAV:** The Lambda streams the file to a ClamAV container for scanning.
5. **Lambda $\rightarrow$ DB:** 
   - If Clean: Update `Files` table `scanStatus = 'CLEARED'`, move file to `s3://aqueduct-prod/`.
   - If Infected: Delete file, update `Files` table `scanStatus = 'INFECTED'`, trigger user notification.
6. **Client $\rightarrow$ CDN:** User requests file via CloudFront; system verifies `isVirusFree == true` before issuing the signed URL.