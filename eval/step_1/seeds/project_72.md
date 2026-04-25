# PROJECT SPECIFICATION: PROJECT BEACON
**Document Version:** 1.0.4  
**Last Updated:** 2024-05-22  
**Status:** Active / In-Development  
**Project Lead:** Mosi Park  
**Organization:** Iron Bay Technologies  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Beacon is a mission-critical initiative by Iron Bay Technologies to modernize the foundational real-time collaboration infrastructure used across the enterprise. For over 15 years, the company has relied on a monolithic legacy system for managing real estate transactions, listing collaborations, and client communications. This legacy system has become a significant bottleneck, characterized by sluggish performance, frequent crashes, and a lack of modern integration capabilities. Beacon is designed to replace this system entirely with a high-performance, scalable, real-time collaboration tool tailored specifically for the complexities of the real estate industry.

### 1.2 Business Justification
The current legacy system represents a significant operational risk. Due to its age, the cost of maintenance is escalating, and the lack of modern API support prevents Iron Bay Technologies from integrating with third-party real estate data aggregators and CRM tools. Furthermore, the system’s instability during peak listing periods results in lost productivity and potential revenue leakage.

The primary business driver for Beacon is "Zero Downtime Tolerance." Because the entire company depends on this system for daily operations, any outage during the transition from the legacy system to Beacon would result in immediate financial losses and operational paralysis. Therefore, the project employs a phased strangler-fig migration pattern, ensuring the new micro-frontend architecture can coexist with the old system until a full cut-over is achieved.

### 1.3 ROI Projection and Success Metrics
The financial success of Project Beacon is measured against two primary Key Performance Indicators (KPIs):

1.  **Revenue Generation:** Beacon is projected to facilitate $500,000 in new revenue within the first 12 months of full deployment. This will be achieved by enabling faster transaction turn-around times and providing a superior collaboration experience that attracts higher-value commercial real estate clients.
2.  **Operational Efficiency:** A target reduction of 35% in the cost per transaction. By automating manual synchronization tasks and replacing the expensive maintenance of the legacy server stack with Azure’s scalable cloud infrastructure, the cost to process a single real estate listing/transaction is expected to drop significantly.

### 1.4 Strategic Alignment
Beacon aligns with Iron Bay Technologies' goal of digital transformation. By moving to a full Microsoft stack (C#/.NET, Azure SQL, Azure Functions), the company leverages its existing enterprise agreements and ensures a talent pipeline of developers proficient in these technologies.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Beacon utilizes a **Micro-Frontend (MFE) Architecture**. Unlike traditional monoliths, the UI is split into independent modules owned by different sub-teams. This prevents a single point of failure in the UI layer and allows for independent deployment of features without needing to re-deploy the entire application.

### 2.2 The Technology Stack
- **Backend:** C# / .NET 8
- **Database:** Azure SQL (Hyperscale tier for high availability)
- **Compute:** Azure Functions (Serverless) for asynchronous processing; Azure App Services for the core API.
- **Frontend:** React with Module Federation for MFE implementation.
- **Communication:** SignalR for real-time WebSocket communication.
- **Storage:** Azure Blob Storage for documents, integrated with Azure CDN.
- **Security:** Internal Security Audit (No external compliance required per project mandate).

### 2.3 Infrastructure Diagram (ASCII Representation)

```text
[ USER BROWSER ] <---> [ Azure Front Door / CDN ]
                                |
                                v
                    [ Micro-Frontend Shell ]
                    /           |           \
       [Module: Collab]  [Module: Files]  [Module: Admin]
              |                 |                |
              +-----------------+----------------+
                                |
                                v
                    [ Azure API Gateway / App Service ]
                    /           |           \
        [SignalR Hub]    [Azure Functions]  [Business Logic Layer]
              |                 |                |
              v                 v                v
       [Real-time State]  [Virus Scan API]  [Azure SQL Database]
       (Redis Cache)      (Defender for Cloud) (Tables/Schemas)
                                |
                                v
                        [ Azure Blob Storage ]
```

### 2.4 Data Flow and State Management
Real-time collaboration is handled via SignalR. When a user edits a document, the delta is sent to the SignalR hub, which broadcasts the change to all connected clients currently viewing that specific real estate asset. The state is eventually persisted to Azure SQL via an asynchronous queue (Azure Service Bus) to ensure that UI responsiveness is not hindered by database latency.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
The core of Beacon is the ability for multiple real estate agents and brokers to edit the same property listing or contract simultaneously. This feature ensures that "last-write-wins" scenarios are avoided, preventing the accidental deletion of critical contract terms.

**Functional Requirements:**
- **Operational Transformation (OT):** The system implements an OT-based approach to handle concurrent edits. Every keystroke is treated as an operation (Insert, Delete, Retain).
- **Conflict Resolution:** When two users edit the same character index, the system uses a deterministic tie-breaking algorithm based on user IDs to ensure all clients converge on the same state.
- **Presence Indicators:** Users must see who else is currently editing the document, indicated by colored cursors with name labels.
- **Latency Compensation:** Local changes are applied immediately to the UI (optimistic UI) and synchronized in the background.

**Technical implementation:**
The feature utilizes SignalR for the transport layer. The state is maintained in a Redis cache for milliseconds-level access before being flushed to Azure SQL every 30 seconds or upon document "save" triggers.

---

### 3.2 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
Real estate involves the exchange of large volumes of PDFs, high-resolution images, and legal documents. Beacon provides a secure pipeline for uploading these files, ensuring they are clean of malware and accessible globally with low latency.

**Functional Requirements:**
- **Secure Upload:** Files are uploaded via a signed URL to Azure Blob Storage to prevent unauthorized access to the storage account.
- **Virus Scanning:** Every uploaded file triggers an Azure Function that invokes Microsoft Defender for Cloud's malware scanning API. Files flagged as malicious are immediately quarantined and the user is notified.
- **CDN Distribution:** To ensure that agents in different regions can view property images instantly, files are cached via Azure CDN.
- **Version Control:** If a file is updated, the system maintains a version history, allowing users to roll back to previous versions of a contract.

**Technical Implementation:**
The workflow is: `Client -> API Gateway -> Signed URL -> Blob Storage -> Event Grid Trigger -> Virus Scan Function -> CDN Purge/Update`.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Review

**Description:**
In the real estate industry, legal accountability is paramount. Every change made to a property listing, price change, or contract must be logged in a way that cannot be altered after the fact.

**Functional Requirements:**
- **Immutable Logs:** Logs must be written to a "Write Once, Read Many" (WORM) storage tier in Azure.
- **Tamper-Evidence:** Each log entry contains a cryptographic hash of the previous entry (Blockchain-lite), ensuring that if any record is deleted or modified, the chain is broken and an alert is triggered.
- **Granular Tracking:** Logs must capture the User ID, Timestamp, IP Address, Old Value, and New Value.
- **Searchability:** An administrative dashboard must allow the Project Lead to query logs by Asset ID or User ID.

**Technical Implementation:**
The system uses an Azure Function to intercept all `UPDATE` and `DELETE` commands on critical tables. These events are formatted as JSON and pushed to Azure Immutable Blob Storage.

---

### 3.4 Notification System (Email, SMS, In-App, and Push)
**Priority:** High | **Status:** Blocked

**Description:**
The notification system keeps users informed of updates to listings, bid approvals, and system alerts. It must be multi-channel to ensure agents are reached regardless of their location.

**Functional Requirements:**
- **Multi-Channel Routing:** A single event (e.g., "Offer Accepted") can trigger an in-app toast, an email via SendGrid, and an SMS via Twilio.
- **Preference Management:** Users can toggle which notifications they receive per channel (e.g., Email: ON, SMS: OFF).
- **Push Notifications:** Integration with Firebase Cloud Messaging (FCM) for mobile browsers.
- **Aggregation:** To prevent "notification fatigue," the system should aggregate multiple small updates into a single "Daily Digest" email.

**Current Blocker:**
The development is currently blocked by third-party API rate limits. The Twilio and SendGrid sandbox accounts have hit their daily limits during stress testing, and the procurement of production-grade API keys is pending budget approval for the next tranche.

---

### 3.5 SSO Integration with SAML and OIDC Providers
**Priority:** Low (Nice to Have) | **Status:** Complete

**Description:**
To simplify onboarding and offboarding, Beacon integrates with Iron Bay Technologies' existing corporate identity providers.

**Functional Requirements:**
- **SAML 2.0 Support:** Integration with Azure Active Directory (Azure AD) for corporate login.
- **OIDC Support:** Support for OpenID Connect for external contractor access.
- **Automatic Provisioning:** Upon first successful SSO login, a user profile is automatically created in the Beacon database.
- **Session Management:** Centralized session timeout management; if a user is disabled in Azure AD, their Beacon session is invalidated within 5 minutes.

**Technical Implementation:**
Implemented using the `.NET Identity` framework and `Microsoft.Identity.Web`.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 Asset Management
**Endpoint:** `GET /assets/{assetId}`
- **Description:** Retrieves full details of a real estate asset.
- **Request:** `GET /api/v1/assets/RE-99283`
- **Response (200 OK):**
  ```json
  {
    "assetId": "RE-99283",
    "address": "123 Iron Bay Way",
    "currentValue": 450000,
    "status": "Active",
    "lastModified": "2024-05-20T10:00:00Z"
  }
  ```

**Endpoint:** `PATCH /assets/{assetId}`
- **Description:** Partially updates asset details.
- **Request:** `PATCH /api/v1/assets/RE-99283` | Body: `{"currentValue": 460000}`
- **Response (200 OK):**
  ```json
  { "status": "success", "updatedFields": ["currentValue"] }
  ```

### 4.2 Collaboration and Real-time
**Endpoint:** `POST /collab/session/join`
- **Description:** Registers a user into a real-time editing session.
- **Request:** `POST /api/v1/collab/session/join` | Body: `{"assetId": "RE-99283", "userId": "U101"}`
- **Response (200 OK):**
  ```json
  { "signalRConnectionId": "conn_abc123", "token": "jwt_signalr_token" }
  ```

**Endpoint:** `POST /collab/operation`
- **Description:** Sends a single OT operation to the server.
- **Request:** `POST /api/v1/collab/operation` | Body: `{"op": "insert", "pos": 12, "char": "A", "version": 45}`
- **Response (200 OK):**
  ```json
  { "acknowledgedVersion": 46, "status": "synced" }
  ```

### 4.3 File Management
**Endpoint:** `GET /files/upload-url`
- **Description:** Generates a SAS token for secure Azure Blob upload.
- **Request:** `GET /api/v1/files/upload-url?filename=contract.pdf`
- **Response (200 OK):**
  ```json
  { "uploadUrl": "https://ironbaystorage.blob.core.windows.net/uploads/contract.pdf?sig=...", "fileId": "file_556" }
  ```

**Endpoint:** `DELETE /files/{fileId}`
- **Description:** Requests deletion of a file (triggers audit log).
- **Request:** `DELETE /api/v1/files/file_556`
- **Response (204 No Content):** No body.

### 4.4 Audit and Administration
**Endpoint:** `GET /audit/logs/{assetId}`
- **Description:** Retrieves the tamper-evident history of an asset.
- **Request:** `GET /api/v1/audit/logs/RE-99283`
- **Response (200 OK):**
  ```json
  [
    { "timestamp": "2024-05-20T10:00:00Z", "userId": "U101", "action": "PriceChange", "old": 440000, "new": 450000, "hash": "a1b2c3..." },
    { "timestamp": "2024-05-21T11:00:00Z", "userId": "U102", "action": "StatusChange", "old": "Pending", "new": "Active", "hash": "d4e5f6..." }
  ]
  ```

**Endpoint:** `GET /admin/system/health`
- **Description:** Checks the health of all micro-services and DB connections.
- **Request:** `GET /api/v1/admin/system/health`
- **Response (200 OK):**
  ```json
  { "status": "Healthy", "services": { "sql": "UP", "blob": "UP", "signalr": "UP" } }
  ```

---

## 5. DATABASE SCHEMA

The database is hosted on Azure SQL. All tables use `Guid` for primary keys to facilitate easier merging and synchronization across distributed environments.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Description | Key Fields |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `UserId` | None | User identity and profile | `Email`, `FullName`, `Role`, `SsoProviderId` |
| `Assets` | `AssetId` | `CreatedBy` | Real estate properties | `Address`, `Valuation`, `Status`, `CreatedBy` |
| `CollabSessions` | `SessionId` | `AssetId` | Active editing sessions | `AssetId`, `StartTime`, `LastActiveTime` |
| `SessionParticipants`| `ParticipantId`| `SessionId`, `UserId`| Users in a session | `SessionId`, `UserId`, `CursorPosition` |
| `DocumentVersions` | `VersionId` | `AssetId` | Historical snapshots | `AssetId`, `BlobPath`, `VersionNumber`, `Timestamp` |
| `AuditLogs` | `LogId` | `AssetId`, `UserId` | Tamper-evident changes | `AssetId`, `UserId`, `ChangeJson`, `PrevHash`, `CurrentHash` |
| `Files` | `FileId` | `AssetId`, `UploadedBy`| Metadata for uploads | `AssetId`, `BlobUrl`, `MimeType`, `ScanStatus` |
| `Notifications` | `NotifId` | `UserId` | Outbound notifications | `UserId`, `Channel`, `Message`, `IsRead`, `SentDate` |
| `UserPreferences` | `PrefId` | `UserId` | Notification settings | `UserId`, `EmailEnabled`, `SmsEnabled`, `PushEnabled` |
| `BillingModule` | `BillId` | `AssetId` | Transaction costs | `AssetId`, `CostAmount`, `BillingPeriod`, `InvoiceStatus` |

### 5.2 Relationships and Constraints
- **Assets $\rightarrow$ AuditLogs:** One-to-Many. Every asset can have thousands of audit entries.
- **Users $\rightarrow$ Assets:** One-to-Many (Owner relationship).
- **CollabSessions $\rightarrow$ SessionParticipants:** One-to-Many.
- **Files $\rightarrow$ Assets:** Many-to-One. Multiple images/docs per property.
- **BillingModule $\rightarrow$ Assets:** One-to-Many. Tracking multiple cost events per asset.

### 5.3 Indexing Strategy
- **Clustered Index:** All primary keys.
- **Non-Clustered Index:** `AuditLogs.AssetId` for fast retrieval of history.
- **Non-Clustered Index:** `Assets.Status` for filtering active listings.
- **Non-Clustered Index:** `Notifications.UserId` where `IsRead = 0` to optimize the "Unread" count.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Deployment Strategy
Beacon employs a **Continuous Deployment (CD)** model. Any Pull Request (PR) merged into the `main` branch is automatically deployed to production. This high-velocity approach is supported by the micro-frontend architecture, which isolates failures.

### 6.2 Environment Descriptions

#### 6.2.1 Development (Dev)
- **Purpose:** Individual developer testing.
- **Infrastructure:** Local Docker containers for SQL and Redis; Azure Functions Core Tools.
- **Data:** Mocked data; no real client information.

#### 6.2.2 Staging (Staging)
- **Purpose:** Integration testing and QA validation.
- **Infrastructure:** Mirror of Production (Azure App Service, Azure SQL).
- **Data:** Anonymized production data snapshots.
- **Gate:** Requires QA sign-off before PRs are merged to `main`.

#### 6.2.3 Production (Prod)
- **Purpose:** Live business operations.
- **Infrastructure:** High-availability Azure SQL Hyperscale, Azure Front Door for global traffic management.
- **Deployment:** Automatic via GitHub Actions.
- **Zero Downtime:** Achieved through Blue-Green deployment slots in Azure App Service.

### 6.3 CI/CD Pipeline Detail
1. **Commit:** Developer pushes to a feature branch.
2. **PR Review:** Peer review (though often rushed due to team dysfunction).
3. **Build:** GitHub Actions runs `.NET build` and `npm run build`.
4. **Test:** Unit tests execute (Note: Billing module is currently skipped).
5. **Deploy to Staging:** Automatic deployment to the staging slot.
6. **Merge to Main:** Deployment to Production slot.
7. **Swap:** Azure App Service swaps Staging $\rightarrow$ Production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Using xUnit and Moq.
- **Coverage Goal:** 80% across business logic layers.
- **Current Gap:** The **Core Billing Module** has **0% test coverage**. It was deployed under extreme deadline pressure. This is the highest technical debt item in the project.

### 7.2 Integration Testing
- **Approach:** Postman collections automated via Newman.
- **Focus:** Verifying that Azure Functions correctly trigger after a file upload and that SignalR messages are delivered to the correct session groups.
- **Environment:** Staging.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Playwright for browser automation.
- **Scenarios:**
    - User A edits a property name $\rightarrow$ User B sees the update in < 200ms.
    - User uploads a file $\rightarrow$ Virus scan fails $\rightarrow$ File is deleted $\rightarrow$ User receives notification.
    - SSO login $\rightarrow$ Redirect to Beacon Dashboard.

### 7.4 QA Process
The dedicated QA engineer performs manual regression testing on the "Critical" features (Collaboration and File Upload) before every major milestone. Because the Project Lead and PM do not communicate, the QA engineer often acts as the sole bridge, documenting bugs in Jira that both parties eventually see.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | High | High | Hire a contractor (Celine Stein) to reduce the "bus factor" and handle overflow work. |
| R-02 | Project sponsor rotates out of role | Medium | High | Document all workarounds and architectural decisions; share them widely with the team via Slack. |
| R-03 | Third-party API rate limits (Twilio/SendGrid) | High | Medium | (Current Blocker) Implement a request queue and caching layer to reduce API calls. |
| R-04 | Legacy system crash during migration | Low | Critical | Implement a "Kill Switch" to route traffic back to legacy if Beacon fails. |
| R-05 | Billing module failure due to lack of tests | High | Medium | Schedule a "Technical Debt Sprint" specifically to write tests for the billing module. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project failure or company-wide outage.
- **High:** Significant delay in milestone achievement or revenue loss.
- **Medium:** Manageable delay; requires workaround.
- **Low:** Minimal impact on timeline.

---

## 9. TIMELINE AND PHASES

The project is structured into three primary milestones with specific target dates. Dependencies are managed through the micro-frontend delivery pipeline.

### 9.1 Phase 1: Core Infrastructure (Completed $\rightarrow$ Milestone 1)
- **Objective:** Establish the C#/.NET foundation and real-time engine.
- **Key Deliverable:** Collaborative editing and File upload.
- **Milestone 1: Performance benchmarks met.**
- **Target Date:** 2025-08-15.
- **Dependency:** Azure SQL Hyperscale provisioning.

### 9.2 Phase 2: Security and Hardening (In Progress $\rightarrow$ Milestone 2)
- **Objective:** Ensure the system is tamper-proof and secure.
- **Key Deliverable:** Audit trail logging and Internal Security Audit.
- **Milestone 2: Security audit passed.**
- **Target Date:** 2025-10-15.
- **Dependency:** Completion of the Audit Trail logging feature.

### 9.3 Phase 3: Enterprise Integration (Upcoming $\rightarrow$ Milestone 3)
- **Objective:** Finalize the ecosystem and transition from legacy.
- **Key Deliverable:** Notification system and final Architecture Review.
- **Milestone 3: Architecture review complete.**
- **Target Date:** 2025-12-15.
- **Dependency:** Resolution of third-party API rate limit blockers.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per company culture, Beacon does not maintain formal meeting minutes. The following are reconstructed from Slack threads in the `#beacon-dev` and `#beacon-leadership` channels.*

### Meeting 1: The "Billing Debt" Discussion
**Date:** 2024-03-12
**Participants:** Mosi Park, Cassius Moreau
- **Mosi:** "The billing module is live. I know there are no tests, but the sponsor was breathing down my neck. We had to merge it to meet the funding tranche."
- **Cassius:** "This is a disaster waiting to happen. If we break the billing logic, we don't even know it's broken until the end of the month."
- **Decision:** Mosi decides to defer tests until the "Performance Benchmark" milestone is met. No tickets created in Jira.

### Meeting 2: The SSO/SAML Conflict
**Date:** 2024-04-05
**Participants:** Hiro Costa, Celine Stein
- **Hiro:** "The UX for the SSO login is confusing. Users are getting redirected to a blank page after Azure AD auth."
- **Celine:** "It's a callback URL issue in the Azure Portal. I've fixed it in Dev, but I can't push to Prod because Mosi hasn't approved the PR."
- **Hiro:** "Mosi isn't replying to the PM, so the PM isn't approving the release. I'll just leave a note in the thread."
- **Decision:** Celine pushes the fix via a "hotfix" branch that bypasses the standard review process.

### Meeting 3: API Rate Limit Crisis
**Date:** 2024-05-10
**Participants:** Mosi Park, Cassius Moreau, Celine Stein
- **Cassius:** "We're getting 429 errors from Twilio. We can't test the notification system."
- **Celine:** "We need to upgrade to the paid tier, but the budget for this month is already spent on the Azure SQL Hyperscale upgrade."
- **Mosi:** "Just mock the responses for now. We can't afford another budget request this quarter or the sponsor will start asking why the PM and I aren't in the same meetings."
- **Decision:** Notification system is officially marked as "Blocked."

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches upon the completion of milestones. The total budget is variable, but the current allocation is as follows:

| Category | Allocated Amount | Spent to Date | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel (Full Time)** | $650,000 | $320,000 | Mosi, Cassius, Hiro, and QA. |
| **Personnel (Contractor)** | $120,000 | $60,000 | Celine Stein (Mitigation for Risk R-01). |
| **Azure Infrastructure** | $80,000 | $45,000 | Hyperscale SQL and App Services. |
| **Tooling & Licenses** | $15,000 | $12,000 | GitHub Enterprise, JetBrains, Postman. |
| **Contingency Fund** | $50,000 | $10,000 | Reserved for emergency scaling. |
| **Total** | **$915,000** | **$447,000** | |

**Funding Note:** If the projected 30% budget cut occurs in Q3, the Contingency Fund will be absorbed first, followed by a reduction in contractor hours.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Algorithm (Pseudo-code)
To ensure consistency in real-time editing, Beacon uses the following logic for Operational Transformation:

```csharp
public Operation Transform(Operation localOp, Operation remoteOp) {
    if (localOp.Type == OpType.Insert && remoteOp.Type == OpType.Insert) {
        if (localOp.Position < remoteOp.Position) {
            return localOp; // Local remains, remote shifts
        } else if (localOp.Position > remoteOp.Position) {
            return localOp.ShiftPosition(+1); // Local shifts right
        } else {
            // Tie-breaker: User with lower Alphabetical ID wins
            return (localOp.UserId < remoteOp.UserId) ? localOp : localOp.ShiftPosition(+1);
        }
    }
    // Additional logic for Delete/Delete and Insert/Delete...
}
```

### Appendix B: Virus Scanning Workflow Detail
The virus scanning process is decoupled from the upload to ensure the user doesn't experience a "hanging" UI.

1. **Blob Upload:** User uploads `document.pdf` to `uploads-temp` container.
2. **Event Grid Trigger:** Azure Event Grid detects `Microsoft.Storage.BlobCreated`.
3. **Scan Function:** Azure Function `fn-virus-scan` is triggered.
4. **Defender Scan:** The function calls the `Microsoft Defender for Storage` API.
5. **Result Handling:**
    - **Clean:** File is moved from `uploads-temp` to `assets-production` and CDN is purged.
    - **Infected:** File is moved to `quarantine` folder; `AuditLogs` table is updated with "Malware Detected"; Notification is sent to the user.