# PROJECT SPECIFICATION: PROJECT DELPHI
**Document Version:** 1.0.4  
**Status:** Draft for Approval  
**Project Code:** DELPHI-SCM-2026  
**Company:** Talus Innovations  
**Classification:** Confidential / Internal Use Only  
**Last Updated:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Delphi is a high-stakes, moonshot Research and Development (R&D) initiative undertaken by Talus Innovations. The objective is to develop a next-generation Supply Chain Management (SCM) system specifically tailored for the aerospace industry. Unlike traditional SCMs, Delphi is designed to handle the extreme complexities of aerospace procurement, including multi-decade part lifecycles, stringent regulatory compliance (AS9100), and the need for absolute traceability of components from raw material to final assembly.

The project is categorized as a "moonshot" because it seeks to disrupt current industry standards by implementing a CQRS-based event-sourcing architecture that allows for "time-travel" auditing—the ability to reconstruct the exact state of the supply chain at any microsecond in history.

### 1.2 Business Justification
The aerospace sector is currently plagued by fragmented data silos and legacy systems that cannot handle the scale of modern satellite and commercial aircraft production. Talus Innovations aims to capture this market by providing a system that reduces lead times by an estimated 15% and eliminates manual auditing overhead. 

While the ROI is currently uncertain due to the R&D nature of the project, the executive sponsorship is strong. The strategic value lies in establishing Talus Innovations as the primary software backbone for aerospace logistics. If successful, Delphi will transition from an internal R&D project to a commercial SaaS offering.

### 1.3 ROI Projection
Projected ROI is calculated based on a three-tier subscription model targeting Tier 1 and Tier 2 aerospace suppliers.
- **Year 1 (Post-Launch):** Focus on stability and onboarding. Projected revenue: $1.2M.
- **Year 2:** Scaling to 10,000 Monthly Active Users (MAUs). Projected revenue: $8.5M.
- **Year 3:** Full market penetration. Projected revenue: $22M.
The Break-Even Point (BEP) is estimated to occur in Month 14 post-launch, assuming the milestone-based funding tranches are utilized efficiently and the product hits the target NPS of 40+.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: CQRS & Event Sourcing
Project Delphi utilizes Command Query Responsibility Segregation (CQRS). This separates the "Write" model (Commands) from the "Read" model (Queries), allowing for independent scaling and optimization.

**Event Sourcing:** Instead of storing only the current state of a supply chain asset, Delphi stores every change as an immutable event in an "Event Store." This is critical for aerospace compliance, where an audit trail of *why* a part was rejected is as important as the fact that it was rejected.

### 2.2 The Stack
- **Language/Framework:** C# (.NET 8)
- **Database (Read/Write):** Azure SQL Database (Hyperscale tier)
- **Compute:** Azure Functions (Serverless) for event handlers and background processing.
- **Messaging:** Azure Service Bus for asynchronous communication between the Command and Query sides.
- **Frontend:** React 18 with TypeScript (managed by Wanda Oduya).
- **Deployment:** GitHub Actions for CI/CD pipelines.

### 2.3 ASCII Architecture Diagram
```text
[ Client (Web/Mobile) ] 
          |
          v
[ Azure API Management / Gateway ] <--- (Rate Limiting & Usage Analytics)
          |
          +-----------------------+
          |                       |
    (Command Side)            (Query Side)
          |                       |
[ Azure Function (Cmd) ]    [ Azure Function (Query) ]
          |                       |
[ Event Store (Azure SQL) ] ------> [ Materialized Views (Azure SQL) ]
          |          (Async Projection)
          |
[ Service Bus / Event Grid ]
          |
[ Notification System (Email/SMS/Push) ]
```

### 2.4 Security & Compliance
To meet the requirements for aerospace contracts, the system must achieve **SOC 2 Type II compliance** prior to the launch date. Luna Costa is the lead on this, ensuring that all data at rest is encrypted via Azure Key Vault and that all access is governed by Role-Based Access Control (RBAC).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics (Priority: High)
**Description:** 
To protect the system from denial-of-service attacks and to implement tiered pricing for future customers, Delphi requires a robust API rate-limiting mechanism coupled with granular usage analytics.

**Functional Requirements:**
- **Dynamic Throttling:** The system must support multiple throttling tiers (e.g., Basic: 100 req/min, Premium: 1,000 req/min, Enterprise: Unlimited).
- **Token Bucket Algorithm:** Implementation of the token bucket algorithm to allow for short bursts of traffic while maintaining a steady average rate.
- **Usage Dashboard:** A real-time administrative view showing the number of requests per API key, status code distribution (2xx, 4xx, 5xx), and latency percentiles (p50, p95, p99).
- **Header Feedback:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Implementation:**
The rate limiter will be implemented as a middleware component in the Azure API Management (APIM) layer. Usage analytics will be streamed via Azure Monitor and Kusto queries to a dedicated analytics table in Azure SQL to ensure that the analytics process does not impact the performance of the command side.

### 3.2 Notification System (Priority: High)
**Description:** 
A multi-channel notification engine to alert users of critical supply chain events (e.g., "Part Delay," "Quality Inspection Failure," "Budget Overrun").

**Functional Requirements:**
- **Multi-Channel Delivery:** Support for Email (via SendGrid), SMS (via Twilio), In-App Notifications (via SignalR), and Push Notifications (via Azure Notification Hubs).
- **Preference Center:** Users must be able to toggle which notifications they receive on which channel (e.g., "Critical Alerts" via SMS and Email, "Weekly Reports" via Email only).
- **Notification Templates:** A template engine allowing admins to define placeholders (e.g., `Hello {userName}, Part {partId} is delayed by {days} days`).
- **Retry Logic:** If a delivery fails, the system must attempt redelivery 3 times with exponential backoff.

**Technical Implementation:**
The system will follow a "Notification Dispatcher" pattern. An event (e.g., `PartDelayedEvent`) is published to the Service Bus. A dedicated Azure Function listens for these events, checks the user's preferences in the database, and routes the message to the appropriate provider.

### 3.3 Data Import/Export with Format Auto-Detection (Priority: Medium)
**Description:** 
Aerospace suppliers use a variety of legacy formats (CSV, XML, JSON, EDIFACT). Delphi must allow users to upload these files without manually specifying the format.

**Functional Requirements:**
- **Format Auto-Detection:** The system must analyze the first 100 bytes of an uploaded file to determine if it is CSV, JSON, or XML based on magic bytes and structure.
- **Mapping Engine:** A UI that allows users to map external columns (e.g., "Serial_Num") to internal Delphi fields (e.g., `ComponentSerialNumber`).
- **Bulk Import:** Ability to process files with up to 1 million rows without timing out the request.
- **Export Options:** Ability to export any queried dataset into the same supported formats.

**Technical Implementation:**
Importing will be handled asynchronously. The file is uploaded to Azure Blob Storage; a trigger invokes an Azure Function that performs the auto-detection and queues the parsing job. The parsing job uses a "Chunking" strategy to process data in batches of 5,000 records to avoid memory overflows.

### 3.4 File Upload with Virus Scanning and CDN Distribution (Priority: Low)
**Description:** 
Users need to upload technical drawings (CAD files, PDFs). These files must be scanned for malware and distributed globally for low-latency access.

**Functional Requirements:**
- **Malware Scanning:** Integration with an antivirus API (e.g., Windows Defender or a 3rd party API) to scan every file before it is marked as "Available."
- **CDN Integration:** Files must be served via Azure Front Door/CDN to ensure that engineers in different global regions can access large blueprints quickly.
- **Version Control:** Files must be versioned; uploading a new version of "Drawing_A.pdf" should not overwrite the old one but create a new version linked to the part.

**Technical Implementation:**
Uploads go to a "Quarantine" container in Azure Blob Storage. A trigger sends the file to the virus scanner. Upon a "Clean" result, the file is moved to the "Production" container, which is linked to the CDN.

### 3.5 Workflow Automation Engine with Visual Rule Builder (Priority: High)
**Description:** 
A "Low-Code" engine allowing users to define business logic without developer intervention (e.g., "If Part Value > $10,000 AND Supplier = 'X', then require Approval from VP").

**Functional Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface (Nodes and Edges) where users can define triggers, conditions, and actions.
- **Trigger Types:** Support for event-based triggers (e.g., `OnItemCreated`) and time-based triggers (e.g., `Every Monday at 8 AM`).
- **Condition Logic:** Support for Boolean logic (AND, OR, NOT) and comparison operators (>, <, ==, contains).
- **Action Execution:** Actions include sending notifications, updating a field, or triggering another workflow.

**Technical Implementation:**
The visual builder will be implemented using React Flow. The rules will be stored as JSON logic trees in Azure SQL. A specialized "Workflow Processor" Azure Function will evaluate these trees against the event stream using the `JsonLogic` library to execute the specified actions.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned (`/v1/`) and require a Bearer Token in the Authorization header. Base URL: `https://api.delphi.talus.io/v1`

### 4.1 `POST /assets`
**Purpose:** Create a new aerospace asset in the system.
- **Request Body:**
  ```json
  {
    "assetName": "Turbine Blade X-1",
    "partNumber": "TB-9902",
    "supplierId": "SUP-441",
    "initialQuantity": 50
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "assetId": "uuid-1234-5678",
    "status": "Pending_Inspection",
    "createdAt": "2026-01-10T10:00:00Z"
  }
  ```

### 4.2 `GET /assets/{id}/history`
**Purpose:** Retrieve the event-sourced audit trail for a specific asset.
- **Response (200 OK):**
  ```json
  [
    { "event": "AssetCreated", "timestamp": "2026-01-10T10:00Z", "user": "stein_a" },
    { "event": "InspectionPassed", "timestamp": "2026-01-12T14:20Z", "user": "costa_l" }
  ]
  ```

### 4.3 `POST /notifications/send`
**Purpose:** Manually trigger a notification (used by Workflow Engine).
- **Request Body:**
  ```json
  {
    "userId": "user-99",
    "channel": "sms",
    "templateId": "DELAY_ALERT",
    "context": { "partId": "TB-9902", "days": "5" }
  }
  ```
- **Response (202 Accepted):** `{ "jobId": "job-abc-123" }`

### 4.4 `GET /analytics/usage`
**Purpose:** Retrieve API usage stats for the current account.
- **Response (200 OK):**
  ```json
  {
    "period": "last_30_days",
    "totalRequests": 450000,
    "rateLimitHits": 120,
    "avgLatencyMs": 142
  }
  ```

### 4.5 `POST /import/detect`
**Purpose:** Upload a sample of a file to detect its format.
- **Request Body:** `Multipart/form-data` (File upload)
- **Response (200 OK):** `{ "detectedFormat": "CSV", "confidence": 0.98, "suggestedMapping": [...] }`

### 4.6 `POST /workflows/deploy`
**Purpose:** Deploy a new visual rule set.
- **Request Body:**
  ```json
  {
    "workflowName": "HighValueApproval",
    "logicTree": { "and": [{ ">": [{ "var": "value" }, 10000] }, { "==": [{ "var": "supplier" }, "X"] }] }
  }
  ```
- **Response (201 Created):** `{ "workflowId": "wf-789" }`

### 4.7 `GET /files/download/{fileId}`
**Purpose:** Securely download a file via CDN.
- **Response:** `302 Redirect` to a signed Azure CDN URL.

### 4.8 `DELETE /assets/{id}`
**Purpose:** Mark an asset as deleted (Soft delete in Event Store).
- **Response (204 No Content)**

---

## 5. DATABASE SCHEMA

The system uses a relational schema in Azure SQL, but the `EventStore` table acts as the source of truth for the Command side.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `UserId` | - | `Email`, `Role`, `MfaEnabled` | User identity and access roles. |
| `Assets` | `AssetId` | `SupplierId` | `PartNumber`, `CurrentStatus` | Current state of aerospace components. |
| `Suppliers` | `SupplierId` | - | `CompanyName`, `SertificationLevel` | Registry of approved aerospace vendors. |
| `EventStore` | `EventId` | `AssetId` | `EventType`, `Payload` (JSON), `Timestamp` | The immutable log of all system changes. |
| `Workflows` | `WorkflowId` | `CreatedById` | `LogicJson`, `IsActive` | Definition of the automation rules. |
| `Notifications` | `NotifId` | `UserId` | `Channel`, `SentAt`, `Status` | Log of all sent communications. |
| `UserPreferences`| `PrefId` | `UserId` | `ChannelType`, `IsEnabled` | User settings for notifications. |
| `Files` | `FileId` | `AssetId` | `StoragePath`, `ScanStatus`, `Version` | Metadata for technical blueprints. |
| `ApiKeys` | `KeyId` | `UserId` | `KeyHash`, `RateLimitTier`, `ExpiresAt` | API authentication and throttling keys. |
| `UsageLogs` | `LogId` | `KeyId` | `Endpoint`, `ResponseTime`, `StatusCode` | Granular telemetry for usage analytics. |

### 5.2 Relationships
- `Users` $\rightarrow$ `UserPreferences` (1:1)
- `Users` $\rightarrow$ `ApiKeys` (1:N)
- `Assets` $\rightarrow$ `EventStore` (1:N)
- `Assets` $\rightarrow$ `Files` (1:N)
- `Suppliers` $\rightarrow$ `Assets` (1:N)
- `ApiKeys` $\rightarrow$ `UsageLogs` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi utilizes a three-tier environment strategy to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Azure Functions (Consumption Plan), Azure SQL (Basic Tier).
- **Deployment:** Automatic deploy on push to `develop` branch.
- **Data:** Mock data only.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing, UAT, and SOC 2 compliance auditing.
- **Infrastructure:** Mirror of Production (Standard Tier).
- **Deployment:** Triggered via GitHub Actions upon merging `develop` into `release/vX.X`.
- **Data:** Anonymized production snapshots.

#### 6.1.3 Production (Prod)
- **Purpose:** Live end-user traffic.
- **Infrastructure:** Azure SQL Hyperscale, Premium Azure Functions, Azure Front Door.
- **Deployment:** Blue-Green deployment strategy. The "Green" environment is spun up; once health checks pass, traffic is shifted 10% $\rightarrow$ 50% $\rightarrow$ 100%.
- **Data:** Live encrypted production data.

### 6.2 CI/CD Pipeline
GitHub Actions is used for all pipelines.
1. **Build:** Compiles C# code, runs `dotnet test`.
2. **Security Scan:** Runs Static Analysis (SAST) and checks for dependency vulnerabilities.
3. **Deploy to Staging:** Deploys to the staging slot.
4. **Smoke Test:** Automated suite of 50 critical path tests.
5. **Production Swap:** Manual approval gate $\rightarrow$ Blue-Green swap.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** All business logic in Azure Functions and Domain Models.
- **Tooling:** xUnit and Moq.
- **Requirement:** Minimum 80% code coverage for the Command side.
- **Focus:** Validation logic, event payload construction, and rate-limit calculations.

### 7.2 Integration Testing
- **Scope:** Communication between Azure Functions, Service Bus, and Azure SQL.
- **Tooling:** Postman/Newman for API contract testing.
- **Requirement:** All 8 primary API endpoints must pass integration tests in the Staging environment.
- **Focus:** Ensuring the "Query" side reflects "Command" side changes within < 500ms (Eventual Consistency check).

### 7.3 End-to-End (E2E) Testing
- **Scope:** Complete user journeys (e.g., "Create Asset $\rightarrow$ Trigger Workflow $\rightarrow$ Receive SMS").
- **Tooling:** Playwright for frontend automation.
- **Requirement:** Critical paths (onboarding, import/export, workflow setup) must be tested weekly.
- **Focus:** UI responsiveness, CDN file loading speeds, and notification delivery.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is building same product and is 2 months ahead. | High | Critical | Escalate to steering committee for additional funding to accelerate dev cycles. |
| **R-02** | Performance requirements 10x current system with no extra budget. | Medium | High | De-scope "Nice to Have" features (e.g., File Uploads) if unresolved by Milestone 1. |
| **R-03** | SOC 2 Type II compliance failure. | Low | Critical | Monthly audits by Luna Costa; early engagement with external auditors. |
| **R-04** | Budget approval for critical tool purchase pending. | High | Medium | Temporary use of open-source alternatives until approval is granted. |
| **R-05** | Technical Debt: Lack of structured logging. | High | Medium | Implement Serilog/Azure Application Insights across all functions by Q1 2026. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project stoppage or failure to launch.
- **High:** Significant delay or major feature removal.
- **Medium:** Manageable delay or minor feature degradation.

---

## 9. TIMELINE

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Now - 2026-03-01):** Setup of CQRS architecture, basic API, and Event Store.
- **Phase 2: Core Features (2026-03-01 - 2026-08-01):** Implementation of Rate Limiting, Notifications, and Workflow Engine.
- **Phase 3: Optimization & Compliance (2026-08-01 - 2026-10-01):** Performance tuning, SOC 2 audit, and Data Import/Export.
- **Phase 4: Beta & Launch (2026-10-01 - 2026-12-15):** Onboarding first customer and stability monitoring.

### 9.2 Milestone Schedule
- **Milestone 1: Performance benchmarks met** $\rightarrow$ **2026-08-15**
  - *Dependency:* Completion of CQRS optimization and Azure SQL indexing.
- **Milestone 2: Post-launch stability confirmed** $\rightarrow$ **2026-10-15**
  - *Dependency:* Successful completion of SOC 2 audit and E2E testing.
- **Milestone 3: First paying customer onboarded** $\rightarrow$ **2026-12-15**
  - *Dependency:* Completion of the Data Import/Export tool for migration.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-02)
- **Attendees:** Adaeze, Wanda, Luna.
- **Notes:**
  - CQRS seems too complex?
  - Adaeze says it's non-negotiable for audit.
  - Luna worried about SOC 2 with event sourcing.
  - Decided: Use Azure SQL for both but separate schemas.
  - JIRA tickets created for Event Store.

### Meeting 2: Budget Crisis (2023-12-15)
- **Attendees:** Adaeze, Alejandro.
- **Notes:**
  - Tool purchase still pending.
  - Alejandro can't start the import engine without the parser tool.
  - Adaeze will ping the CFO again.
  - Use open source for now.

### Meeting 3: Performance Review (2024-01-20)
- **Attendees:** Adaeze, Wanda, Luna, Alejandro.
- **Notes:**
  - System is slow.
  - 10x capacity requirement is "insane."
  - Budget for new servers is zero.
  - Potential to cut the CDN feature if we can't hit the 2026-08-15 date.
  - Logging is still just stdout—terrible for debugging.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the achievement of the milestones listed in Section 9.

| Category | Allocated Amount | Funding Tranche | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $4,200,000 | Monthly | 12-person team (Avg $350k/year total load) |
| **Azure Infrastructure** | $850,000 | Quarterly | Includes Hyperscale SQL and Front Door CDN |
| **Tools & Licenses** | $120,000 | One-time/Annual | Pending approval for specialized parser tool |
| **SOC 2 Compliance Audit**| $200,000 | Milestone 2 | External auditing firm fees |
| **Contingency Fund** | $500,000 | On-Demand | To be used for Risk R-01 (Competitor acceleration) |
| **Total Budget** | **$5,870,000** | | **Variable based on executive sponsorship** |

---

## 12. APPENDICES

### Appendix A: Event Schema Detail
To ensure consistency in the `EventStore`, all event payloads must follow the CloudEvents specification.
- **Header:** `eventId`, `source`, `specversion`, `type`, `datetime`.
- **Data:** A JSON object containing the specific change.
- **Example `PartDelayed` Event:**
  ```json
  {
    "id": "ev-9988",
    "source": "/assets/TB-9902",
    "type": "com.talus.scm.part.delayed",
    "data": {
      "delayDays": 5,
      "reason": "Customs Hold",
      "updatedBy": "user-44"
    }
  }
  ```

### Appendix B: Rate Limiting Tier Definitions
The following limits are hard-coded into the APIM policy:

| Tier | Requests per Minute | Burst Capacity | Monthly Quota |
| :--- | :--- | :--- | :--- |
| **Basic** | 100 | 120 | 1,000,000 |
| **Premium** | 1,000 | 1,200 | 10,000,000 |
| **Enterprise** | 10,000 | 15,000 | Unlimited |

*Note: If a user exceeds their monthly quota, the API will return `429 Too Many Requests` until the next billing cycle or until a top-up is purchased.*