Due to the extensive length requirement (6,000–8,000 words), this document is structured as a comprehensive **Master Project Specification**. It serves as the single source of truth for the Lodestar project.

***

# PROJECT SPECIFICATION: PROJECT LODESTAR
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Document Owner:** Chioma Moreau, Engineering Manager  
**Status:** Draft / Under Review  
**Classification:** Confidential – Hearthstone Software Internal

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Lodestar** is a strategic platform modernization initiative commissioned by Hearthstone Software. The objective is to transition a legacy monolithic real estate e-commerce marketplace—currently characterized by rigid scaling limitations and high maintenance overhead—into a modern, microservices-oriented architecture. While the project begins as a "clean monolith" with strict module boundaries to ensure stability, the long-term roadmap involves a gradual decomposition into independent services over an 18-month transition period.

The real estate marketplace industry is currently shifting toward "hyper-local" instantaneous transactions. The legacy system cannot support the concurrency required for real-time listing updates or the complex workflow automations demanded by modern brokers. Lodestar aims to bridge this gap by implementing a high-performance C#/.NET stack hosted on Microsoft Azure.

### 1.2 Business Justification
The existing platform has reached a state of technical stagnation. Current operational costs are increasing by 15% annually due to the inefficiency of the monolithic codebase, and the "time-to-market" for new features has slowed from two weeks to two months. 

The business justification for Lodestar rests on three pillars:
1. **Scalability:** Moving to Kubernetes-based deployments allows the platform to handle seasonal spikes in real estate activity (e.g., the spring buying season) without manual server provisioning.
2. **Compliance:** The requirement for SOC 2 Type II compliance is non-negotiable for entering the enterprise real estate market, which requires rigorous auditing of data access and security.
3. **Competitive Parity:** A direct competitor is currently building a near-identical product and is estimated to be two months ahead in development. Failure to launch Lodestar with the specified feature set will result in a projected loss of 20% of the current market share within the first year.

### 1.3 ROI Projection
With a total budget investment of **$3,000,000**, Hearthstone Software projects the following returns over a 36-month horizon:
- **Operational Efficiency:** A 50% reduction in manual processing time for end-users (brokers and agents), equating to an estimated saving of $450,000 per year in labor costs.
- **Revenue Growth:** By targeting 10,000 Monthly Active Users (MAU) within six months of launch, the platform expects to generate $1.2M in annual recurring revenue (ARR) through new subscription tiers.
- **Risk Mitigation:** The migration to Azure SQL and Kubernetes reduces the risk of catastrophic downtime, which currently costs the company approximately $12,000 per hour of outage.
- **Projected Break-even:** Month 22 post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: The Clean Monolith
Lodestar utilizes a **Clean Monolith** architecture. This approach acknowledges that a full microservices jump is risky for a small team of four. Instead, the application is built as a single deployable unit, but internally structured into "Silos" or "Bounded Contexts" (following Domain-Driven Design). Each module (Billing, User Management, Listings, Reporting) communicates via internal interfaces. This ensures that when the 18-month migration to microservices begins, these modules can be extracted into separate Azure Functions or Container Apps with minimal code changes.

### 2.2 The Technology Stack
- **Backend:** C# / .NET 8.0 (LTS)
- **Database:** Azure SQL Database (Hyperscale tier)
- **Serverless:** Azure Functions (for asynchronous tasks and event-driven triggers)
- **Containerization:** Docker & Azure Kubernetes Service (AKS)
- **CI/CD:** GitLab CI (Rolling deployments)
- **Identity:** Azure Active Directory (Azure AD) / MSAL
- **Frontend:** React 18 (TypeScript)

### 2.3 High-Level Architecture Diagram (ASCII)
```text
[ Client Layer ] ----> [ Azure Front Door / WAF ]
                                |
                                v
                    [ Azure Kubernetes Service (AKS) ]
                    +-----------------------------------+
                    |  [ API Gateway / YARP ]           |
                    +---------|-------------------------+
                              |
      ________________________|________________________
     |                        |                        |
[ User Module ]        [ Listing Module ]       [ Workflow Module ]
     |                        |                        |
     +-----------+------------+-----------+------------+
                 |                        |
                 v                        v
        [ Azure SQL DB ] <----------> [ Azure Blob Storage ]
        (Structured Data)             (PDFs, CSVs, Images)
                 ^                        ^
                 |                        |
        [ Azure Functions ] <--- [ Service Bus / Queue ]
        (Background Jobs)       (Async Processing)
```

### 2.4 Technical Debt & Constraints
A critical architectural risk is the current state of the Data Access Layer. Approximately **30% of queries bypass the ORM (Entity Framework Core)** and use raw SQL strings for performance optimization in high-traffic listing searches. 
- **Impact:** This makes database migrations dangerous, as schema changes may break raw SQL strings that are not caught by the compiler.
- **Constraint:** All new features must use EF Core unless a performance benchmark proves a $\ge 50\%$ improvement with raw SQL, in which case the query must be encapsulated in a stored procedure to decouple the code from the schema.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** Not Started
**Description:** Real estate agents often operate in areas with poor connectivity (e.g., basements of properties, rural areas). The platform must allow users to create listings, take notes, and upload photos while offline, then synchronize data once a connection is restored.

**Detailed Requirements:**
- **Client-Side Storage:** Implementation of IndexedDB for persisting state. All "Write" operations must be queued in a Local-First queue.
- **Conflict Resolution:** The system shall use "Last-Write-Wins" (LWW) based on a UTC timestamp for simple fields. For complex entities (like listing descriptions), a version-clocking mechanism will be implemented. If a conflict occurs, the user will be prompted with a "Conflict Resolver" UI showing both versions.
- **Background Sync Process:**
    1. Service Worker detects `navigator.onLine` state.
    2. Pushes queued requests to the `/api/v1/sync` endpoint in chronological order.
    3. The server processes the batch and returns a `SyncManifest` indicating successful IDs and failed IDs.
- **Payload Optimization:** Delta-updates only. Instead of sending the whole object, the client sends a JSON Patch (RFC 6902) to reduce bandwidth.

### 3.2 SSO Integration (SAML & OIDC)
**Priority:** High | **Status:** In Design
**Description:** To attract enterprise-level real estate firms, Lodestar must support Single Sign-On (SSO), allowing firms to manage their agents' access via their own identity providers (IdPs) like Okta, PingIdentity, or Azure AD.

**Detailed Requirements:**
- **OIDC Flow:** Implementation of the Authorization Code Flow with PKCE (Proof Key for Code Exchange) for the React frontend.
- **SAML 2.0 Support:** A dedicated metadata exchange portal where administrators can upload their IdP's XML metadata file and configure the Entity ID and Reply URL.
- **Just-In-Time (JIT) Provisioning:** When a user logs in via SSO for the first time, the system must automatically create a user profile in the Azure SQL database based on the claims (email, first name, last name, role) provided in the SAML assertion or OIDC token.
- **Token Management:** JWTs (JSON Web Tokens) will be used for session management with a 15-minute expiry and a secure refresh token rotated every 24 hours.

### 3.3 Workflow Automation Engine (Visual Rule Builder)
**Priority:** High | **Status:** Blocked
**Description:** A "No-Code" tool allowing users to create triggers and actions (e.g., "If a listing price drops by >10%, send an email to all interested buyers").

**Detailed Requirements:**
- **Trigger Definitions:** The engine must support triggers based on:
    - Data Changes (Field value changes)
    - Time-based events (Cron schedules)
    - External Webhooks.
- **Visual Builder:** A drag-and-drop interface using a node-based logic system (similar to Zapier or Node-RED). Users connect "Trigger Nodes" to "Action Nodes" via edges.
- **Execution Engine:** A distributed worker system using Azure Functions. When a trigger is fired, the event is placed in an Azure Service Bus queue. The Worker reads the "Rule Blueprint" from the DB and executes the corresponding action.
- **Guardrails:** To prevent infinite loops (e.g., Action A triggers Action B, which triggers Action A), the engine must have a maximum recursion depth of 5.

### 3.4 PDF/CSV Report Generation
**Priority:** Medium | **Status:** Not Started
**Description:** Management needs the ability to generate high-fidelity market analysis reports in PDF format and raw data exports in CSV for external auditing.

**Detailed Requirements:**
- **Template Engine:** Use of a server-side rendering engine (e.g., Puppeteer or QuestPDF) to convert HTML/CSS templates into branded PDFs.
- **Scheduled Delivery:** A scheduler utilizing Azure Functions' Timer Trigger. Users can select "Weekly," "Monthly," or "Custom" intervals.
- **Delivery Channels:** Reports must be delivered via Email (SendGrid integration) or uploaded to a secure, time-limited Azure Blob Storage link.
- **Performance:** Generation of reports with $>10,000$ rows must be handled asynchronously. The user receives a "Processing" notification and an email once the file is ready for download.

### 3.5 Automated Billing and Subscription Management
**Priority:** Low | **Status:** In Design
**Description:** A system to manage tiered pricing plans (Basic, Professional, Enterprise) and handle monthly recurring billing.

**Detailed Requirements:**
- **Stripe Integration:** Use of Stripe Billing for subscription lifecycles, including trial periods, grace periods for failed payments, and automated invoicing.
- **Tier Enforcement:** A middleware layer in the API that checks the user's current subscription level before allowing access to specific features (e.g., only "Enterprise" users can access the Workflow Engine).
- **Proration Logic:** Automatic calculation of credits when a user upgrades or downgrades their plan mid-cycle.
- **Dunning Process:** An automated sequence of emails (Day 1, Day 3, Day 7) sent to users with expired credit cards before account suspension.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions, utilize JSON for request/response bodies, and require a Bearer Token in the Authorization header.

### 4.1 Auth & Identity
**Endpoint:** `POST /api/v1/auth/sso/callback`
- **Description:** Handles the return trip from the OIDC/SAML provider.
- **Request Body:** `{ "code": "string", "state": "string" }`
- **Response:** `200 OK` $\rightarrow$ `{ "accessToken": "jwt_string", "refreshToken": "jwt_string", "user": { "id": "guid", "role": "string" } }`

### 4.2 Listing Management
**Endpoint:** `GET /api/v1/listings`
- **Description:** Retrieves a paginated list of real estate properties.
- **Query Params:** `page=int`, `pageSize=int`, `filter=string`, `sort=string`
- **Response:** `200 OK` $\rightarrow$ `{ "data": [ { "id": "guid", "address": "string", "price": "decimal" } ], "totalCount": 1250 }`

**Endpoint:** `POST /api/v1/listings`
- **Description:** Creates a new property listing.
- **Request Body:** `{ "address": "string", "price": "decimal", "description": "string", "ownerId": "guid" }`
- **Response:** `201 Created` $\rightarrow$ `{ "id": "guid", "status": "Pending" }`

**Endpoint:** `PATCH /api/v1/listings/{id}`
- **Description:** Partially updates a listing (used by the Offline Sync engine).
- **Request Body:** `[ { "op": "replace", "path": "/price", "value": 450000 } ]` (JSON Patch)
- **Response:** `200 OK` $\rightarrow$ `{ "id": "guid", "updatedAt": "timestamp" }`

### 4.3 Synchronization
**Endpoint:** `POST /api/v1/sync`
- **Description:** Bulk synchronization endpoint for offline-first mode.
- **Request Body:** `{ "deviceId": "string", "payload": [ { "action": "create|update|delete", "entity": "listing", "data": { ... }, "timestamp": "iso8601" } ] }`
- **Response:** `200 OK` $\rightarrow$ `{ "processedIds": [ "guid" ], "conflicts": [ { "id": "guid", "serverVersion": { ... } } ] }`

### 4.4 Workflow Automation
**Endpoint:** `POST /api/v1/workflows`
- **Description:** Saves a new visual rule configuration.
- **Request Body:** `{ "name": "string", "trigger": { "type": "price_drop", "threshold": 0.1 }, "actions": [ { "type": "email", "target": "buyers_list" } ] }`
- **Response:** `201 Created` $\rightarrow$ `{ "workflowId": "guid" }`

**Endpoint:** `GET /api/v1/workflows/{id}/logs`
- **Description:** Returns the execution history of a specific workflow.
- **Response:** `200 OK` $\rightarrow$ `{ "executions": [ { "timestamp": "iso8601", "status": "success|failed", "errorMessage": "string" } ] }`

### 4.5 Reporting
**Endpoint:** `POST /api/v1/reports/generate`
- **Description:** Requests an immediate generation of a report.
- **Request Body:** `{ "reportType": "market_analysis", "format": "pdf|csv", "filters": { ... } }`
- **Response:** `202 Accepted` $\rightarrow$ `{ "jobId": "guid", "estimatedWait": "seconds" }`

---

## 5. DATABASE SCHEMA

The database is hosted on Azure SQL. All tables use `UNIQUEIDENTIFIER` (GUID) for primary keys to facilitate easier synchronization and merging in the offline-first mode.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `Users` | `UserId` (PK), `Email`, `PasswordHash`, `SsoProviderId` | 1:N with `Listings` | Core user identity and credentials. |
| `UserRoles` | `RoleId` (PK), `RoleName` | N:M with `Users` | Defines permissions (Admin, Agent, Client). |
| `Listings` | `ListingId` (PK), `OwnerId` (FK), `Address`, `Price`, `Status` | N:1 with `Users` | The primary real estate assets. |
| `ListingHistory` | `HistoryId` (PK), `ListingId` (FK), `OldValue`, `NewValue` | N:1 with `Listings` | Audit trail for price/status changes. |
| `WorkflowRules` | `RuleId` (PK), `OwnerId` (FK), `TriggerJson`, `ActionJson` | N:1 with `Users` | Store for the visual rule builder config. |
| `WorkflowLogs` | `LogId` (PK), `RuleId` (FK), `ExecutionTime`, `Status` | N:1 with `WorkflowRules` | History of workflow executions. |
| `Subscriptions` | `SubId` (PK), `UserId` (FK), `StripeId`, `PlanLevel`, `Expiry` | N:1 with `Users` | Billing and tier management. |
| `Reports` | `ReportId` (PK), `UserId` (FK), `BlobUrl`, `GeneratedAt` | N:1 with `Users` | Metadata for generated PDF/CSVs. |
| `SyncSessions` | `SessionId` (PK), `DeviceId`, `LastSyncTime` | N:1 with `Users` | Tracks offline sync state per device. |
| `AuditLogs` | `AuditId` (PK), `UserId` (FK), `Action`, `Timestamp`, `IpAddress` | N:1 with `Users` | Required for SOC 2 Compliance. |

### 5.2 Relationship Diagram (Logic)
- **Users** $\rightarrow$ **Listings**: One user can own many listings.
- **Users** $\rightarrow$ **Subscriptions**: One user has one active subscription.
- **Listings** $\rightarrow$ **ListingHistory**: One listing has many historical change records.
- **WorkflowRules** $\rightarrow$ **WorkflowLogs**: One rule generates many execution logs.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lodestar utilizes a three-tier environment strategy to ensure stability and compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Configuration:** Azure SQL (Basic), Single-node AKS cluster.
- **Deployment:** Automatic trigger on push to `develop` branch in GitLab.
- **Data:** Mock data generated via scripts.

#### 6.1.2 Staging (Stage)
- **Purpose:** User Acceptance Testing (UAT) and Beta testing.
- **Configuration:** Mirror of Production (Azure SQL Hyperscale, Multi-node AKS).
- **Deployment:** Triggered by Merge Request to `release` branch.
- **Data:** Anonymized snapshot of production data.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Configuration:** High Availability (HA) zone redundancy, Azure Front Door, SOC 2 compliant logging.
- **Deployment:** Rolling updates via GitLab CI. A "Blue-Green" deployment strategy is used to allow instant rollback.
- **Security:** Private endpoints for all database connections; no public IP for the SQL server.

### 6.2 CI/CD Pipeline (GitLab)
1. **Build Phase:** `.NET build` $\rightarrow$ `NuGet restore` $\rightarrow$ `Docker image build`.
2. **Test Phase:** Run Unit Tests $\rightarrow$ Run Integration Tests $\rightarrow$ Static Analysis (SonarQube).
3. **Deploy Phase:** `kubectl apply` to AKS $\rightarrow$ Health check probe $\rightarrow$ Traffic shift.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Target:** 80% code coverage.
- **Tooling:** xUnit, Moq.
- **Focus:** Business logic in the "Domain" layer. All calculations for commission and pricing must have exhaustive boundary tests.

### 7.2 Integration Testing
- **Target:** All API endpoints.
- **Tooling:** Postman/Newman, TestContainers.
- **Focus:** Validating that the API correctly interacts with Azure SQL and Azure Blob Storage. Specifically, the "Offline Sync" logic must be tested with simulated network latency.

### 7.3 End-to-End (E2E) Testing
- **Target:** Critical User Journeys (e.g., "Create Listing" $\rightarrow$ "Offline Mode" $\rightarrow$ "Sync" $\rightarrow$ "Verify in DB").
- **Tooling:** Playwright.
- **Focus:** UI-to-Backend flow.

### 7.4 SOC 2 Compliance Testing
- **Vulnerability Scanning:** Weekly scans using Azure Defender for Cloud.
- **Penetration Testing:** Quarterly third-party audit.
- **Audit Log Verification:** Automated tests to ensure every `POST/PATCH/DELETE` action generates a corresponding entry in the `AuditLogs` table.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | Medium | High | Accept risk; establish strong ties with the next-level VP to ensure funding continuity. Weekly updates to the board. | Chioma M. |
| R-02 | Competitor 2 months ahead in dev | High | High | Assign a dedicated "Competitive Intelligence" owner to track their feature releases and pivot the roadmap to "leapfrog" them. | Chioma M. |
| R-03 | Medical leave of key member | High | High | Current blocker. Reallocate tasks to Asha (Contractor) and prioritize only "Critical" features. | Chioma M. |
| R-04 | Raw SQL breaking migrations | Medium | High | Implement a "SQL Audit" check in CI/CD that flags any raw SQL strings during schema updates. | Felix S. |
| R-05 | SOC 2 Audit Failure | Low | Critical | Engage a compliance consultant early (Month 6) to perform a gap analysis. | Chioma M. |

**Probability/Impact Matrix:**
- High Probability + High Impact $\rightarrow$ **Immediate Action Required**
- Medium Probability + High Impact $\rightarrow$ **Active Monitoring**
- Low Probability + Critical Impact $\rightarrow$ **Contingency Planning**

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Oct 2023 - May 2025)**
    - Establish AKS cluster and Clean Monolith structure.
    - Implement SSO and Core Listing CRUD.
    - **Goal:** MVP Feature Complete.
- **Phase 2: Stabilization & Beta (May 2025 - July 2025)**
    - Finalize Offline-First Sync.
    - Launch External Beta with 10 pilot users.
    - **Goal:** User validation and bug squashing.
- **Phase 3: Hardening & Compliance (July 2025 - Sept 2025)**
    - Finalize Reporting and Billing.
    - Conduct SOC 2 Type II audit.
    - **Goal:** Production readiness.

### 9.2 Gantt-Style Dependency Map
```text
[Foundation] ---------------------> [MVP Complete (2025-05-15)]
      |                                     |
      | (Dependency: SSO & Sync)             v
      +------------------------------> [Beta Launch (2025-07-15)]
                                            |
                                            | (Dependency: Security Audit)
                                            v
                                     [Security Passed (2025-09-15)]
                                            |
                                            v
                                     [FULL MARKET LAUNCH]
```

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment
**Date:** 2023-11-02  
**Attendees:** Chioma Moreau, Felix Santos, Kira Gupta, Asha Fischer  
**Discussion:**
- Felix raised concerns about the use of EF Core for the search page, citing a 3-second latency on large datasets.
- Chioma insisted on a "Clean Monolith" approach to prevent premature microservices fragmentation.
- Kira presented the initial UX research showing that agents struggle with the current "Save" button layout when on mobile.
- **Tension:** Chioma and the Lead Engineer (referenced in team dynamic) had a disagreement regarding the deployment frequency; Chioma wants daily, the Lead wants bi-weekly. They stopped speaking for the remainder of the call.

**Action Items:**
- [Felix] Benchmark raw SQL vs EF Core for the `/listings` endpoint. (Due: 2023-11-10)
- [Kira] Create wireframes for the "Offline Sync" conflict resolver. (Due: 2023-11-15)

### Meeting 2: Priority Re-evaluation & Blocker Analysis
**Date:** 2023-12-15  
**Attendees:** Chioma Moreau, Felix Santos, Asha Fischer  
**Discussion:**
- **Urgent:** Confirmation that a key team member is on medical leave for 6 weeks.
- The team discussed how to handle the "Workflow Automation Engine" (High Priority). Since it's blocked by the medical leave and technical complexity, Chioma decided to shift Asha (Contractor) to help Felix with the database migrations.
- Discussion on the competitor's new "Instant Offer" feature. Felix suggested we prioritize the Offline-First mode to differentiate our product as "The most reliable in the field."

**Action Items:**
- [Chioma] Update the project roadmap to reflect the medical leave delay. (Due: 2023-12-18)
- [Asha] Take over the `SyncSessions` table implementation. (Due: 2023-12-30)

### Meeting 3: SOC 2 Compliance Strategy
**Date:** 2024-01-20  
**Attendees:** Chioma Moreau, Felix Santos, Kira Gupta  
**Discussion:**
- Chioma outlined the requirements for SOC 2 Type II.
- Felix noted that current `AuditLogs` are not immutable. He proposed moving audit logs to a "Write-Once-Read-Many" (WORM) storage in Azure Blob Storage to prevent tampering.
- Kira questioned if the SOC 2 requirements would impact the UX (e.g., forcing more frequent password changes or MFA). Chioma confirmed MFA will be mandatory via OIDC.

**Action Items:**
- [Felix] Implement WORM storage for `AuditLogs`. (Due: 2024-02-15)
- [Chioma] Contact the SOC 2 auditor for a preliminary gap analysis. (Due: 2024-02-01)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000  
**Period:** 18 Months

| Category | Allocated Amount | Percentage | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | $1,800,000 | 60% | Salaries for 3 FTEs + Contractor (Asha) for 18 months. |
| **Infrastructure** | $450,000 | 15% | Azure SQL Hyperscale, AKS, Azure Functions, Front Door. |
| **Tools & Licenses** | $200,000 | 6.7% | GitLab Ultimate, SonarQube, SendGrid, Stripe Enterprise. |
| **Compliance/Audit** | $250,000 | 8.3% | SOC 2 Type II certification and external pen-testing. |
| **Contingency** | $300,000 | 10% | Reserved for emergency hiring or infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: Database Migration Strategy
Because 30% of the system uses raw SQL, the following migration protocol is mandatory:
1. **Step 1:** Create a "Shadow Table" with the new schema.
2. **Step 2:** Implement a "Dual-Write" mechanism where the application writes to both the old and new tables.
3. **Step 3:** Run a background job to migrate historical data from the old table to the new one.
4. **Step 4:** Update all raw SQL queries to point to the new table.
5. **Step 5:** Drop the old table after a 2-week stability period.

### Appendix B: Offline-First Sync Algorithm (Pseudocode)
```csharp
public async Task SyncData(IEnumerable<SyncItem> clientItems) {
    foreach(var item in clientItems) {
        var serverItem = await _db.GetById(item.Id);
        if (serverItem == null) {
            await _db.Insert(item); // New record
        } else if (item.Timestamp > serverItem.LastUpdated) {
            await _db.Update(item); // Client is newer
        } else {
            AddConflictToManifest(item, serverItem); // Server is newer - Conflict!
        }
    }
}
```