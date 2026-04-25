Due to the extreme length requirement of this specification (6,000–8,000 words), this document is structured as a comprehensive, professional technical manual. It expands every provided detail into a granular operational guide for the development team.

***

# PROJECT SPECIFICATION: PROJECT EMBER
**Document Version:** 1.0.4  
**Status:** Active/Draft  
**Last Updated:** 2024-10-25  
**Company:** Clearpoint Digital  
**Confidentiality Level:** Highly Confidential (PCI DSS Level 1)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Ember is a strategic cost-reduction initiative undertaken by Clearpoint Digital. Currently, the organization relies on four redundant internal tools to manage healthcare records within its retail-integrated health services division. These legacy systems—namely *HealthTrack v2*, *PatientSync*, *CareLog*, and *OmniRecord*—operate in silos, creating massive data duplication, inconsistent record-keeping, and an unsustainable licensing overhead. 

The primary business objective is the consolidation of these four disparate tools into a single, unified healthcare records platform. By centralizing the data layer and unifying the user interface, Clearpoint Digital aims to eliminate the redundant infrastructure costs associated with maintaining four separate database clusters and four distinct maintenance contracts. 

### 1.2 Market Context & ROI Projection
The retail health sector requires rapid agility and high security. The current fragmented system results in a "transactional drag," where the cost per transaction (CPU cycles, API calls, and human manual entry) is unnecessarily high. 

**Projected Return on Investment (ROI):**
The total budget for Project Ember is $150,000. This is a "shoestring" budget, meaning the project is designed to be lean, utilizing an existing small team of four without additional headcount. 

The ROI is calculated based on the following projections:
- **Licensing Savings:** Elimination of three legacy software subscriptions, saving approximately $42,000 per annum.
- **Infrastructure Reduction:** Consolidating four AWS RDS instances into one optimized PostgreSQL cluster on Vercel/Neon, reducing monthly spend by $1,200.
- **Operational Efficiency:** A targeted reduction in cost per transaction by 35%. If the legacy system costs $0.12 per record update, Ember aims to bring this down to $0.078.
- **Break-even Point:** The project is expected to pay for itself within 14 months of the Milestone 1 stability date (2026-05-15).

### 1.3 Strategic Alignment
Ember aligns with Clearpoint Digital’s 2025-2026 goal of "Digital Lean." By moving to a TypeScript/Next.js stack, the company reduces the technical debt associated with the legacy Java and PHP systems currently in place. Furthermore, the integration of PCI DSS Level 1 security ensures that the retail-health arm can process credit card data for telehealth services directly within the platform, bypassing third-party gateways and further reducing transaction fees.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Ember follows a traditional three-tier architecture to ensure separation of concerns and ease of maintenance for a small team.

1.  **Presentation Tier (Frontend):** Built with **Next.js 14 (App Router)** and **TypeScript**. The frontend is deployed on **Vercel**, utilizing Server Components for fast initial page loads and Client Components for interactive health record editors.
2.  **Business Logic Tier (API/Backend):** Next.js API Routes (Edge Runtime) handle the orchestration. Business logic is decoupled into service layers to ensure that the "heavy lifting" of healthcare data processing is separated from the HTTP request/response cycle.
3.  **Data Tier (Persistence):** A **PostgreSQL** database accessed via **Prisma ORM**. This provides type-safe database queries and easy schema migrations, which is critical given the complexity of consolidating four legacy schemas.

### 2.2 ASCII Architecture Diagram
```text
[ USER BROWSER ] 
       |
       v
[ VERCEL EDGE NETWORK ] <--- (CDN, SSL Termination, PCI DSS Compliance Layer)
       |
       v
[ NEXT.JS APPLICATION LAYER ]
       |-- [ API ROUTES / SERVER ACTIONS ]
       |-- [ AUTHENTICATION (JWT/Session) ]
       |-- [ BUSINESS LOGIC SERVICES ]
       |-- [ FEATURE FLAG ENGINE ]
       |
       v
[ PRISMA ORM ] <--- (Type-safe Query Layer)
       |
       v
[ POSTGRESQL DATABASE ] <--- (Relational Store)
       |-- [ RECORD TABLES ]
       |-- [ AUDIT LOGS (Tamper-Evident) ]
       |-- [ USER CONFIGS ]
       |-- [ PCI DATA VAULT (Encrypted) ]
```

### 2.3 Infrastructure Specifications
- **Runtime:** Node.js 20.x
- **Language:** TypeScript 5.x (Strict Mode)
- **Database:** PostgreSQL 15.x
- **ORM:** Prisma 5.x
- **Hosting:** Vercel Pro (with dedicated project environment)
- **Deployment Pipeline:** 
    - `dev` branch -> Development Environment
    - `staging` branch -> Staging Environment (QA Gate)
    - `main` branch -> Production Environment
- **Manual QA Gate:** No code enters Production without a sign-off from Veda Fischer. This introduces a mandatory 2-day turnaround for all production releases.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical | **Status:** In Progress | **Launch Blocker:** Yes

**Overview:**
In healthcare, an audit trail is not merely a log; it is a legal requirement. Project Ember must track every read, write, update, and delete action performed on a patient record. To prevent internal bad actors or external breaches from altering logs to hide their tracks, the system must implement "tamper-evident" storage.

**Technical Requirements:**
1.  **Immutable Log Entries:** Once a log is written to the `AuditLog` table, it cannot be updated or deleted. Any "correction" must be a new entry.
2.  **Cryptographic Chaining:** Each log entry will contain a SHA-256 hash of the previous entry, creating a blockchain-like chain. If a record in the middle of the chain is modified, the hash chain breaks, alerting the system during the daily integrity check.
3.  **Granular Capture:** The log must capture:
    - UserID and SessionID.
    - Timestamp (UTC ISO 8601).
    - Action (e.g., `RECORD_VIEW`, `RECORD_EDIT`, `SENSITIVE_DATA_ACCESS`).
    - Old Value vs. New Value (JSON diff).
    - IP Address and User-Agent.
4.  **Storage Strategy:** Logs are stored in a separate PostgreSQL schema with restricted permissions, accessible only by the `AuditService`.

**Acceptance Criteria:**
- An administrator can generate a report showing all changes to a specific record over a 30-day period.
- A script can be run to verify the SHA-256 chain integrity across 1 million records in under 5 minutes.
- Any attempt to manually update the `AuditLog` table via SQL results in a trigger-based alert.

### 3.2 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** Blocked (Waiting on Legal Review of DPA)

**Overview:**
Healthcare providers often need to update a patient's record simultaneously (e.g., a nurse updating vitals while a doctor adds notes). To prevent "last-write-wins" data loss, Ember requires real-time collaboration.

**Technical Requirements:**
1.  **Operational Transformation (OT) or CRDTs:** The system will use Conflict-free Replicated Data Types (CRDTs) via the `Yjs` library to allow concurrent edits without a central coordinator.
2.  **WebSocket Integration:** Real-time updates will be pushed via WebSockets (using a Vercel-compatible provider like Pusher or Socket.io on a separate node instance).
3.  **Presence Indicators:** Users must see who else is currently viewing/editing a record (cursors and avatars).
4.  **Conflict Resolution:** In the event of a hard conflict (e.g., two users changing a patient's blood type simultaneously), the system will flag the record for manual review by a lead clinician.

**Acceptance Criteria:**
- Two users editing the same text field see changes in <200ms latency.
- No data is lost when two users edit different fields in the same record.
- Connection recovery: If a user loses internet, their local changes are synced upon reconnection.

### 3.3 A/B Testing Framework (Integrated into Feature Flags)
**Priority:** High | **Status:** In Progress

**Overview:**
To optimize the retail-healthcare experience, the team needs to test different UI layouts and workflows without deploying new code for every experiment. This framework is baked directly into the feature flag system.

**Technical Requirements:**
1.  **Flag Definition:** Feature flags are defined in the `FeatureFlags` table with a `percentage_rollout` column (0-100).
2.  **User Bucketing:** Users are assigned to a "bucket" (A or B) based on a hash of their `UserID` and the `FlagID`. This ensures a consistent experience for the user across sessions.
3.  **Telemetry:** Every action performed under a specific flag is tagged with the `flag_version` in the telemetry logs.
4.  **Metric Tracking:** The system must track a "Success Metric" (e.g., time to complete a record) for both groups.

**Acceptance Criteria:**
- A developer can toggle a feature for 10% of users via the admin dashboard without a redeploy.
- The system correctly assigns users to cohorts and persists that assignment.
- The A/B test results can be exported as a CSV for analysis by the Project Lead.

### 3.4 Advanced Search with Faceted Filtering & Full-Text Indexing
**Priority:** Low | **Status:** In Design

**Overview:**
With the consolidation of four tools, the volume of data is significant. Users need a "Google-like" search experience to find patients across various demographics, medical histories, and retail IDs.

**Technical Requirements:**
1.  **Full-Text Search (FTS):** Utilize PostgreSQL `tsvector` and `tsquery` for efficient searching of large text fields (e.g., clinical notes).
2.  **Faceted Filtering:** A sidebar allowing users to filter by:
    - Date range (Created, Last Updated).
    - Patient Age/Gender.
    - Insurance Provider.
    - Retail Store Location.
3.  **Indexing Strategy:** GIN (Generalized Inverted Index) indexes will be applied to the search columns to maintain performance as the dataset grows.
4.  **Debounced API:** The search input will use a 300ms debounce to prevent overloading the database with requests on every keystroke.

**Acceptance Criteria:**
- Search results for a database of 100k patients return in <500ms.
- Facets update dynamically as filters are applied.
- Search supports partial matches (e.g., searching "Smit" finds "Smith").

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** Complete

**Overview:**
Different roles (Admin, Doctor, Nurse) require different data views. The dashboard allows users to customize their workspace using a library of pre-defined widgets.

**Technical Requirements:**
1.  **Widget Library:** A set of React components including "Recent Patients," "Pending Approvals," "Revenue Snapshot," and "System Health."
2.  **Drag-and-Drop Interface:** Implemented using `react-grid-layout` to allow users to resize and reposition widgets.
3.  **Persistence:** The layout configuration (X, Y coordinates, Width, Height, WidgetID) is saved as a JSON blob in the `UserPreferences` table.
4.  **Responsive Design:** The grid system must collapse logically for tablet and mobile views.

**Acceptance Criteria:**
- Users can add/remove widgets from a menu.
- Layouts persist across different devices and sessions.
- Widgets load data asynchronously so that a slow-loading widget does not block the rest of the dashboard.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a valid JWT in the `Authorization: Bearer <token>` header.

### 4.1 Patient Records Management

**1. GET `/api/v1/patients`**
- **Description:** Retrieve a list of patients with optional pagination and filtering.
- **Request Params:** `page` (int), `limit` (int), `search` (string).
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "pat_123", "name": "John Doe", "dob": "1985-05-12", "status": "active" }
  ],
  "pagination": { "total": 1050, "page": 1, "totalPages": 21 }
}
```

**2. GET `/api/v1/patients/{id}`**
- **Description:** Fetch full medical record for a specific patient.
- **Response (200 OK):**
```json
{
  "id": "pat_123",
  "medical_history": [...],
  "current_medications": [...],
  "last_visit": "2024-01-10"
}
```

**3. POST `/api/v1/patients`**
- **Description:** Create a new patient record.
- **Request Body:** `{ "name": "string", "dob": "YYYY-MM-DD", "retail_id": "string" }`
- **Response (201 Created):** `{ "id": "pat_456", "status": "created" }`

**4. PATCH `/api/v1/patients/{id}`**
- **Description:** Update existing patient details.
- **Request Body:** `{ "address": "123 Main St", "phone": "555-0199" }`
- **Response (200 OK):** `{ "id": "pat_123", "updated_at": "2024-10-25T10:00:00Z" }`

### 4.2 Audit & Security

**5. GET `/api/v1/audit/logs`**
- **Description:** Retrieve the tamper-evident log chain.
- **Request Params:** `patientId` (string), `startDate` (ISO8601).
- **Response (200 OK):**
```json
{
  "logs": [
    { "id": "log_999", "timestamp": "...", "action": "EDIT", "hash": "a1b2c3...", "prev_hash": "f5e6d7..." }
  ]
}
```

**6. POST `/api/v1/payments/process`**
- **Description:** PCI DSS Level 1 endpoint for processing credit card data.
- **Request Body:** `{ "amount": 50.00, "currency": "USD", "card_details": { "number": "...", "cvv": "..." } }`
- **Response (200 OK):** `{ "transaction_id": "tx_789", "status": "success" }`

### 4.3 System & User Prefs

**7. GET `/api/v1/user/preferences`**
- **Description:** Fetch the user's custom dashboard layout.
- **Response (200 OK):**
```json
{
  "userId": "user_1",
  "layout": [ { "i": "widget_1", "x": 0, "y": 0, "w": 4, "h": 2 } ]
}
```

**8. POST `/api/v1/user/preferences`**
- **Description:** Save the user's custom dashboard layout.
- **Request Body:** `{ "layout": [...] }`
- **Response (200 OK):** `{ "status": "saved" }`

---

## 5. DATABASE SCHEMA

The database uses PostgreSQL with Prisma. All primary keys are UUIDs to prevent ID enumeration attacks.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `User` | `userId` | `email`, `passwordHash`, `role` | 1:M $\to$ `AuditLog` | System users and authentication. |
| `Patient` | `patientId` | `fullName`, `dob`, `retailId` | 1:M $\to$ `MedicalRecord` | Core patient demographic data. |
| `MedicalRecord` | `recordId` | `patientId`, `clinicalNotes`, `updatedAt` | M:1 $\to$ `Patient` | Clinical data and history. |
| `AuditLog` | `logId` | `userId`, `patientId`, `action`, `hash`, `prevHash` | M:1 $\to$ `User` | Tamper-evident security trail. |
| `FeatureFlag` | `flagId` | `key`, `isEnabled`, `rolloutPercent` | N/A | A/B testing and feature toggles. |
| `UserPreference` | `prefId` | `userId`, `configJson`, `updatedAt` | 1:1 $\to$ `User` | Dashboard layouts and UI settings. |
| `PaymentTransaction`| `txId` | `patientId`, `amount`, `status`, `token` | M:1 $\to$ `Patient` | PCI DSS compliant payment logs. |
| `RetailStore` | `storeId` | `storeName`, `locationCode` | 1:M $\to$ `Patient` | Retail location mapping. |
| `InsuranceProvider` | `providerId` | `companyName`, `payerId` | 1:M $\to$ `Patient` | Insurance company details. |
| `Session` | `sessionId` | `userId`, `expiresAt`, `ipAddress` | M:1 $\to$ `User` | Active user session tracking. |

### 5.2 Schema Constraints & Indices
- **Index `idx_patient_retail_id`**: B-Tree index on `Patient(retailId)` for fast lookups during retail checkout.
- **Index `idx_audit_hash`**: Unique index on `AuditLog(hash)` to prevent duplicate log entries.
- **Constraint `check_rollout_range`**: CHECK constraint on `FeatureFlag(rolloutPercent)` ensuring value is between 0 and 100.
- **Foreign Key**: `MedicalRecord.patientId` $\to$ `Patient.patientId` (ON DELETE CASCADE).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ember utilizes three distinct environments to ensure stability and security.

**1. Development (`dev`)**
- **Purpose:** Iterative feature development and unit testing.
- **Database:** Local PostgreSQL Docker containers or a shared dev-cluster.
- **Deployment:** Automatic on every push to the `dev` branch.
- **Security:** Low; mock data used.

**2. Staging (`staging`)**
- **Purpose:** Pre-production validation and QA testing.
- **Database:** A sanitized clone of the production database.
- **Deployment:** Manual trigger from `dev` to `staging`.
- **Security:** High; mirrors production security settings.
- **The QA Gate:** Veda Fischer must perform a full regression test. The turnaround is 48 hours.

**3. Production (`prod`)**
- **Purpose:** Live healthcare records for retail customers.
- **Database:** High-availability PostgreSQL cluster with automated backups.
- **Deployment:** Manual merge from `staging` to `main` after QA sign-off.
- **Security:** PCI DSS Level 1 compliant. All data encrypted at rest (AES-256) and in transit (TLS 1.3).

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions and Vercel.
1. **Lint & Type Check:** Every PR triggers `npm run lint` and `tsc`.
2. **Automated Testing:** Vitest runs unit tests; Playwright runs E2E tests in `staging`.
3. **Prisma Migration:** Migrations are applied to `staging` first. If successful, they are queued for `prod`.
4. **Vercel Preview:** Every PR generates a unique preview URL for stakeholders to review UI changes.

---

## 7. TESTING STRATEGY

Given the critical nature of healthcare data and PCI compliance, a "zero-defect" approach is taken for the Audit Trail and Payment modules.

### 7.1 Unit Testing
- **Tooling:** Vitest.
- **Scope:** Individual utility functions, business logic services, and Prisma middleware.
- **Requirement:** 80% code coverage on the `services/` directory.
- **Focus:** Testing the SHA-256 hashing logic in the Audit Trail to ensure any change in data results in a different hash.

### 7.2 Integration Testing
- **Tooling:** Jest / Supertest.
- **Scope:** API endpoints and database interactions.
- **Focus:** Ensuring that a `POST /api/v1/patients` correctly creates a record in the `Patient` table and a corresponding entry in the `AuditLog` table in a single atomic transaction.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys (e.g., "Patient Onboarding," "Payment Processing," "Dashboard Customization").
- **Focus:** Testing the drag-and-drop functionality of the dashboard across Chrome, Firefox, and Safari.

### 7.4 Security Testing
- **Penetration Testing:** Semi-annual external audits.
- **PCI Compliance:** Monthly scans of the production environment to ensure no unencrypted card data is leaking into logs.
- **Role-Based Access Control (RBAC) Testing:** Verifying that a "Nurse" role cannot access "Billing" endpoints.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance requirements are 10x current capacity with $0 extra budget. | High | High | Hire a specialized contractor to optimize query performance and reduce the "bus factor" of the small team. |
| **R2** | Competitor is building a similar product and is 2 months ahead. | High | Medium | Document all technical workarounds and "quick-win" features; share these with the team to accelerate velocity. |
| **R3** | PCI DSS Level 1 audit failure. | Low | Critical | Implement strict manual QA gates and internal weekly security audits. |
| **R4** | Data loss during migration from 4 legacy tools. | Medium | High | Use a multi-phase migration strategy: Read-only mirror $\to$ Dual write $\to$ Cutover. |
| **R5** | Legal delay in Data Processing Agreement (DPA). | High | Medium | Identify non-blocked features (Dashboard, Search) to work on while waiting for legal. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project termination/Legal liability.
- **High:** Significant delay in milestones or budget overrun.
- **Medium:** Feature scope reduction.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE & GANTT DESCRIPTION

The project is divided into four phases. Dependencies are strict; Phase 2 cannot begin until the Audit Trail (Phase 1) is verified.

### Phase 1: Foundation & Security (Now $\to$ 2026-05-15)
- **Focus:** Consolidation of the 4 legacy tools into the PostgreSQL schema.
- **Key Deliverable:** Tamper-evident audit trail.
- **Dependency:** Legal review of DPA (currently blocking).
- **Milestone 1:** Post-launch stability confirmed (Target: 2026-05-15).

### Phase 2: Revenue & Onboarding (2026-05-16 $\to$ 2026-07-15)
- **Focus:** Payment integration and customer onboarding.
- **Key Deliverable:** PCI DSS Level 1 payment gateway.
- **Milestone 2:** First paying customer onboarded (Target: 2026-07-15).

### Phase 3: Hardening & Audit (2026-07-16 $\to$ 2026-09-15)
- **Focus:** Security scrubbing and performance optimization.
- **Key Deliverable:** Final security audit report.
- **Milestone 3:** Security audit passed (Target: 2026-09-15).

### Phase 4: Optimization (2026-09-16 $\to$ End of Year)
- **Focus:** Advanced Search and Real-time Collaboration (if legal permits).
- **Key Deliverable:** Full-text indexing and faceted filtering.

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff & Budget Constraint
**Date:** 2024-11-01 | **Attendees:** Eben, Elif, Veda, Yonas
**Discussion:**
Eben outlined the $150k budget. The team expressed concern that this is extremely tight for a PCI Level 1 project. Yonas pointed out that the legacy tools are currently costing more in maintenance than the total budget of Project Ember.
**Decisions:**
- All infrastructure must be hosted on Vercel/PostgreSQL to minimize DevOps overhead.
- We will not hire a full-time DevOps engineer; Yonas will handle deployment pipelines.
**Action Items:**
- Eben: Finalize budget allocation for the contractor (Risk R1). [Owner: Eben]
- Elif: Map legacy schemas to the new Prisma model. [Owner: Elif]

### Meeting 2: Technical Debt and Config Crisis
**Date:** 2024-12-15 | **Attendees:** Eben, Elif, Veda, Yonas
**Discussion:**
Elif discovered that hardcoded configuration values (API keys, DB strings, retail IDs) are scattered across 40+ files in the legacy tools. This makes consolidation nearly impossible without a systematic cleanup.
**Decisions:**
- Implement a `.env` based configuration system immediately.
- Create a `ConfigService` in TypeScript to centralize all environment variables.
**Action Items:**
- Yonas: Audit all 40+ files and list all hardcoded values. [Owner: Yonas]
- Elif: Implement the `ConfigService`. [Owner: Elif]

### Meeting 3: The "Legal Blocker" Sync
**Date:** 2025-02-10 | **Attendees:** Eben, Veda, Yonas
**Discussion:**
The real-time collaborative editing feature is blocked because the legal team has not signed the Data Processing Agreement (DPA) regarding how WebSocket data is streamed.
**Decisions:**
- Pivot development focus to the "Customizable Dashboard" and "Advanced Search" to maintain velocity.
- Eben will escalate the DPA review to the VP of Legal.
**Action Items:**
- Veda: Write test cases for the Dashboard widgets. [Owner: Veda]
- Eben: Weekly follow-up with Legal. [Owner: Eben]

---

## 11. BUDGET BREAKDOWN

The total budget is $150,000. Every dollar is scrutinized.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel (Core Team)** | $90,000 | Allocated as project bonuses/stipends for the existing 4-person team. |
| **Contractor (Performance)** | $25,000 | Short-term contract for DB optimization (Mitigation for Risk R1). |
| **Infrastructure** | $15,000 | Vercel Pro, PostgreSQL managed hosting, Pusher API. |
| **Security Audits** | $12,000 | Third-party PCI DSS Level 1 certification and penetration testing. |
| **Tools & Licensing** | $3,000 | GitHub Enterprise, Sentry for error tracking, Figma. |
| **Contingency** | $5,000 | Emergency buffer for unplanned infrastructure scaling. |
| **TOTAL** | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To meet the security requirements, Project Ember must adhere to the following:
1.  **Firewall Configuration:** Vercel's edge network must be configured to restrict access to the production database.
2.  **Encryption:** All cardholder data must be encrypted using AES-256 before being stored in the `PaymentTransaction` table.
3.  **Access Control:** Only the `PaymentService` can access the `card_details` field. All other services see a masked version (e.g., `**** 1234`).
4.  **Logging:** Every access to the payment vault must be recorded in the tamper-evident `AuditLog`.

### Appendix B: Legacy Tool Mapping Table
This table guides Elif in the data migration process.

| Legacy Tool | Table Name | Ember Target Table | Mapping Logic |
| :--- | :--- | :--- | :--- |
| HealthTrack v2 | `pt_master` | `Patient` | Direct map; normalize phone numbers. |
| PatientSync | `clinical_notes` | `MedicalRecord` | Concatenate `note_text` and `note_append`. |
| CareLog | `visit_history` | `MedicalRecord` | Map `visit_date` to `updatedAt`. |
| OmniRecord | `billing_main` | `PaymentTransaction` | Convert currency to USD cents (integer). |