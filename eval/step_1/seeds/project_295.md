# PROJECT SPECIFICATION: PROJECT PINNACLE
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Project Code:** PIN-2026  
**Status:** Active/In-Development  
**Classification:** Internal - Deepwell Data  

---

## 1. EXECUTIVE SUMMARY

Project Pinnacle is a strategic architectural overhaul of Deepwell Data’s primary internal productivity tool. Originally conceived as a rapid-prototype hackathon project, the application has experienced unexpected organic growth, now supporting 500 daily active users (DAU) within the renewable energy sector. While the current monolithic structure served the initial discovery phase, it has reached a ceiling of scalability and maintainability. The objective of Project Pinnacle is to migrate this legacy system into a distributed microservices architecture governed by a centralized API Gateway, ensuring the tool can scale alongside Deepwell Data’s growth in the renewable energy market.

### Business Justification
The current system suffers from "success-induced fragility." As a tool used for coordinating renewable energy assets, any downtime results in operational blindness for field engineers and data analysts. The transition to a microservices architecture allows for independent scaling of high-load components (such as the search and notification engines) without requiring a full redeployment of the application. This migration eliminates the "single point of failure" risk inherent in the current monolith, where a bug in a minor reporting module can crash the entire productivity suite.

### ROI Projection
With a budget allocation of $5.2M, Project Pinnacle is a flagship initiative reported directly to the board. The projected ROI is calculated based on three primary levers:
1. **Operational Efficiency:** By reducing the CI/CD pipeline time (currently 45 minutes) and improving system stability, we estimate a 15% increase in developer velocity, reclaiming approximately 1,200 engineering hours per year.
2. **Risk Mitigation:** Preventing a single catastrophic outage of the productivity tool is estimated to save the company $450,000 in lost operational productivity and potential regulatory reporting delays.
3. **Scalability:** The architecture is designed to support a growth from 500 to 5,000 users without requiring a rewrite of the core data access layer.

The long-term goal is to transform a "hackathon project" into an enterprise-grade asset that provides a competitive advantage in the renewable energy data management space.

---

## 2. TECHNICAL ARCHITECTURE

Project Pinnacle utilizes a full Microsoft stack, leveraging Azure’s cloud ecosystem to provide a resilient, event-driven environment. The core of the system is the **Azure API Management (APIM)** gateway, which acts as the single entry point for all client requests, handling authentication, rate limiting, and request routing.

### The Microservices Stack
- **Backend:** C# .NET 8 (Long Term Support)
- **Compute:** Azure Functions (Serverless) for event-driven tasks and Azure App Services for core business logic.
- **Database:** Azure SQL Database (Hyperscale tier) for relational data.
- **Messaging:** Apache Kafka (Confluent Cloud) for asynchronous communication between services.
- **Frontend:** React 18 (integrated via Azure Static Web Apps).

### Architecture Logic
The system follows the **Saga Pattern** for distributed transactions. When a user triggers an action (e.g., importing a large dataset), the API Gateway routes the request to the Import Service. The Import Service persists the initial state in Azure SQL and emits a `DataImportInitiated` event to Kafka. The Notification Service and File Processing Service subscribe to this topic to trigger their respective workflows independently.

### ASCII Architecture Diagram
```text
[ Client Browser / Mobile ]
           |
           v
    [ Azure API Gateway ] <--- (Auth / Rate Limiting / Routing)
           |
    ------------------------------------------------------------------
    |                |                |                |             |
    v                v                v                v             v
[Auth Service] [Search Service] [Notify Service] [Import Service] [File Service]
    |                |                |                |             |
    ------------------------------------------------------------------
           |                |                |                |
           v                v                v                v
    [ Azure SQL ] <--- [ Kafka Event Bus ] ---> [ Azure Blob Storage ]
    (Relational)       (Async Messaging)         (Unstructured Data)
           |                                                   |
           ------------------------------------------------------
                                   |
                                   v
                        [ CDN (Azure Front Door) ]
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System
**Priority:** High | **Status:** In Review
**Description:** A multi-channel delivery engine designed to alert users of critical energy threshold breaches and system updates.
**Technical Requirements:**
The system must decouple the "trigger" from the "delivery." A dedicated `NotificationService` will maintain a user preference matrix in Azure SQL. When a service emits a `NotificationEvent` to Kafka, the `NotificationService` will determine the target channels based on user settings.
- **Email:** Integrated via SendGrid API. Must support HTML templates.
- **SMS:** Integrated via Twilio. Must handle international formatting for global energy sites.
- **In-App:** Real-time updates delivered via SignalR hubs.
- **Push:** Azure Notification Hubs for iOS/Android.
**Logic Flow:** 
1. Event received from Kafka $\rightarrow$ 2. Fetch User Preferences $\rightarrow$ 3. Determine Channel $\rightarrow$ 4. Dispatch to Provider $\rightarrow$ 5. Update `NotificationLog` table with `DeliveryStatus`.

### 3.2 Advanced Search with Faceted Filtering
**Priority:** High | **Status:** In Progress
**Description:** A high-performance search interface allowing users to filter renewable energy assets by type, region, and output capacity.
**Technical Requirements:**
Because Azure SQL is inefficient for full-text searching at scale, we are implementing an indexing layer using Azure Cognitive Search.
- **Full-Text Indexing:** All asset descriptions and metadata will be indexed into a search index.
- **Faceted Filtering:** The UI will provide dynamic facets (e.g., "Wind Turbines," "Solar Arrays," "Hydroelectric") based on the current result set.
- **Performance:** Search queries must return results in < 200ms.
**Indexing Strategy:** An Azure Function will trigger on any `AssetUpdated` event in Kafka to update the search index in near real-time, ensuring the search remains consistent with the source of truth in Azure SQL.

### 3.3 A/B Testing Framework (Feature Flag System)
**Priority:** Medium | **Status:** In Progress
**Description:** A system allowing the product team to toggle features for specific user segments without redeploying code.
**Technical Requirements:**
Built atop a custom feature flag provider, this framework will support "Canary Releases" and "A/B Tests."
- **Segmenting:** Users can be grouped by `Role`, `Region`, or a random `Hash(UserId)`.
- **Persistence:** Flag states are stored in a Redis cache for sub-millisecond retrieval.
- **Metrics:** The framework must integrate with Azure Application Insights to track which version (A or B) leads to higher user engagement.
**Implementation:** The C# code will utilize a `IFeatureManager` interface. If `FeatureManager.IsEnabled("NewSearchUI", userContext)` returns true, the user sees the new interface.

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** Not Started
**Description:** A utility for importing large datasets from various energy monitoring tools (CSV, JSON, XML).
**Technical Requirements:**
The system must detect the file format automatically upon upload.
- **Auto-Detection:** The service will read the first 1KB of the file to identify magic bytes or structural markers (e.g., `[` for JSON, `<?xml` for XML).
- **Processing:** Large files will be processed using a "chunking" strategy via Azure Batch to avoid memory overflows.
- **Export:** Users can export filtered search results into Excel or CSV formats.
**Error Handling:** If a file fails validation, a detailed error report (row number and column) must be generated and sent via the Notification System.

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Progress
**Description:** Secure handling of site blueprints and energy reports.
**Technical Requirements:**
- **Virus Scanning:** All uploaded files must be passed through an Azure Function integrated with a ClamAV or Defender for Cloud instance before being committed to permanent storage.
- **Storage:** Files are stored in Azure Blob Storage with private access.
- **Distribution:** For high-traffic documents, Azure Front Door (CDN) will cache the content globally to reduce latency.
- **Security:** Files will be served via "Shared Access Signatures" (SAS) with short expiration windows (e.g., 15 minutes) to prevent unauthorized sharing.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a Bearer Token in the Authorization header.

### 4.1 Notifications API
**Endpoint:** `POST /api/v1/notifications/send`
- **Description:** Manually trigger a notification to a user.
- **Request Body:**
  ```json
  {
    "userId": "USR-9921",
    "channel": "SMS",
    "message": "Warning: Turbine 04 overheating.",
    "priority": "High"
  }
  ```
- **Response (202 Accepted):**
  ```json
  { "notificationId": "NOTIF-12345", "status": "Queued" }
  ```

**Endpoint:** `GET /api/v1/notifications/preferences/{userId}`
- **Description:** Retrieve user-specific notification settings.
- **Response (200 OK):**
  ```json
  {
    "userId": "USR-9921",
    "emailEnabled": true,
    "smsEnabled": false,
    "pushEnabled": true
  }
  ```

### 4.2 Search API
**Endpoint:** `GET /api/v1/search?q={query}&facet={facetName}&value={value}`
- **Description:** Perform faceted search across energy assets.
- **Response (200 OK):**
  ```json
  {
    "results": [{ "id": "AST-101", "name": "North Wind Farm", "type": "Wind" }],
    "facets": { "type": { "Wind": 45, "Solar": 30 } },
    "total": 75
  }
  ```

### 4.3 Feature Flag API
**Endpoint:** `GET /api/v1/features/status`
- **Description:** Retrieve all active feature flags for the current user.
- **Response (200 OK):**
  ```json
  {
    "search_v2": true,
    "beta_export": false,
    "new_dashboard": true
  }
  ```

**Endpoint:** `PATCH /api/v1/features/toggle`
- **Description:** Admin endpoint to toggle a feature flag.
- **Request Body:** `{ "featureKey": "beta_export", "enabled": true }`
- **Response (200 OK):** `{ "status": "Updated" }`

### 4.4 File Management API
**Endpoint:** `POST /api/v1/files/upload`
- **Description:** Upload a file for scanning and storage.
- **Request:** Multipart/form-data (File binary).
- **Response (201 Created):**
  ```json
  { "fileId": "FILE-887", "scanStatus": "Pending", "url": "/api/v1/files/download/FILE-887" }
  ```

**Endpoint:** `GET /api/v1/files/download/{fileId}`
- **Description:** Generate a temporary SAS URL for a file.
- **Response (200 OK):**
  ```json
  { "downloadUrl": "https://deepwell.blob.core.windows.net/assets/FILE-887?sig=xyz..." }
  ```

**Endpoint:** `DELETE /api/v1/files/{fileId}`
- **Description:** Remove a file from the system.
- **Response (204 No Content)**

---

## 5. DATABASE SCHEMA

The system utilizes a relational model in Azure SQL. All tables use `UniqueIdentifier` (GUID) for primary keys to facilitate distributed data merging.

### Tables and Relationships

| Table Name | Primary Key | Key Fields | Foreign Keys | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Users** | `UserId` | `Email`, `FullName`, `Role`, `LastLogin` | None | Core user identity. |
| **UserPreferences** | `PrefId` | `UserId`, `EmailEnabled`, `SmsEnabled` | `UserId` $\rightarrow$ Users | Notification settings. |
| **Assets** | `AssetId` | `AssetName`, `AssetType`, `Location`, `Capacity` | None | Renewable energy units. |
| **AssetLogs** | `LogId` | `AssetId`, `Timestamp`, `MetricValue` | `AssetId` $\rightarrow$ Assets | Telemetry data. |
| **Notifications** | `NotifId` | `UserId`, `Message`, `Channel`, `SentDate` | `UserId` $\rightarrow$ Users | History of alerts. |
| **FeatureFlags** | `FlagId` | `FeatureKey`, `IsGlobalEnabled`, `Version` | None | Definition of flags. |
| **UserFeatureOverrides**| `OverrideId`| `FlagId`, `UserId`, `IsEnabled` | `FlagId`, `UserId` | User-specific flag state. |
| **Files** | `FileId` | `FileName`, `StoragePath`, `ScanStatus` | None | Metadata for uploads. |
| **FilePermissions** | `PermId` | `FileId`, `UserId`, `AccessLevel` | `FileId`, `UserId` | Who can access which file. |
| **AuditLogs** | `AuditId` | `UserId`, `Action`, `Timestamp`, `IPAddress` | `UserId` $\rightarrow$ Users | Security trail. |

**Key Relationships:**
- `Users` $\rightarrow$ `UserPreferences` (1:1)
- `Users` $\rightarrow$ `Notifications` (1:N)
- `Assets` $\rightarrow$ `AssetLogs` (1:N)
- `FeatureFlags` $\rightarrow$ `UserFeatureOverrides` (1:N)
- `Files` $\rightarrow$ `FilePermissions` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### Environment Strategy
Project Pinnacle utilizes a three-tier environment strategy to ensure stability before production releases.

1. **Development (Dev):**
   - **Purpose:** Iterative coding and unit testing.
   - **Configuration:** Shared Azure SQL instance, mocked Kafka topics.
   - **Deployment:** Continuous deployment (CD) on every commit to the `develop` branch.

2. **Staging (Staging):**
   - **Purpose:** Integration testing and Regulatory Review.
   - **Configuration:** Mirror of Production hardware and data volume.
   - **Deployment:** Triggered by merges to the `release` branch. This is where the "Regulatory Review" occurs.

3. **Production (Prod):**
   - **Purpose:** End-user access (500 DAU).
   - **Configuration:** High-availability (HA) clusters across two Azure regions.
   - **Deployment:** Quarterly release cycle.

### Deployment Pipeline
The current CI pipeline is a significant point of friction, taking **45 minutes** per run. The roadmap includes:
- **Phase 1:** Parallelizing the test suite (splitting unit tests across 4 agents).
- **Phase 2:** Implementing Docker layer caching for the .NET build process.
- **Phase 3:** Moving to "Incremental Builds" to avoid recompiling unchanged microservices.

### Infrastructure as Code (IaC)
All infrastructure is managed via **Terraform**. This ensures that the Staging and Production environments are identical in configuration, eliminating "it works on my machine" discrepancies.

---

## 7. TESTING STRATEGY

To achieve the success criterion of 99.9% uptime, a rigorous three-layered testing approach is mandated.

### 7.1 Unit Testing
- **Tooling:** xUnit and Moq.
- **Requirement:** Minimum 80% code coverage for all business logic in microservices.
- **Focus:** Edge cases in the `NotificationService` (e.g., invalid phone numbers) and `SearchService` (e.g., empty query strings).

### 7.2 Integration Testing
- **Tooling:** Postman and Azure Test Plans.
- **Focus:** Validating the contract between the API Gateway and the microservices.
- **Kafka Validation:** Testing the "Eventual Consistency" model. For example, ensuring that when an asset is updated in the `AssetService`, the `SearchService` index is updated within 5 seconds.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Focus:** Critical user journeys.
  - *Journey 1:* User uploads a file $\rightarrow$ File is scanned $\rightarrow$ User receives a "Scan Complete" notification.
  - *Journey 2:* User searches for "Solar" $\rightarrow$ Applies "Texas" facet $\rightarrow$ Results filter correctly.
- **Frequency:** Run once per release cycle in the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotating out of role | Medium | High | Accept the risk. Monitor weekly through Hessa Gupta's reporting to ensure board-level visibility remains high. |
| **R-02** | Scope creep from stakeholders | High | Medium | Engage external consultant for independent assessment of feature requests; strictly enforce the "Low Priority" bucket for "nice-to-have" features. |
| **R-03** | Technical Debt: CI Pipeline Speed | High | Medium | Allocate 10% of each sprint to "Pipeline Optimization" to reduce the 45-minute build time. |
| **R-04** | Resource Constraint: Medical Leave | High | High | Current blocker. Redistribution of tasks across the remaining 3 members; Asha Liu (Contractor) to take on additional backend tickets. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required (Medical Leave).
- **Medium/High:** Close monitoring (Sponsor Rotation).
- **High/Medium:** Planned mitigation (Scope Creep/CI Pipeline).

---

## 9. TIMELINE AND MILESTONES

Project Pinnacle follows a structured timeline aligned with quarterly regulatory review cycles.

### Phase 1: Foundation & Migration (Now $\rightarrow$ 2026-04)
- **Objective:** Establish API Gateway and migrate core data to Azure SQL.
- **Dependency:** Completion of the basic microservice skeleton.
- **Key Task:** Setup Kafka clusters and Azure APIM.

### Phase 2: Feature Implementation (2026-04 $\rightarrow$ 2026-07)
- **Objective:** Implement Search, Notifications, and File Uploads.
- **Dependency:** Stability of the API Gateway routing.
- **Key Task:** Integration of Azure Cognitive Search and SendGrid/Twilio.

### Phase 3: Launch & Stabilization (2026-07 $\rightarrow$ 2026-11)
- **Objective:** Production rollout and performance tuning.
- **Dependency:** Successful Regulatory Review in Staging.

### Critical Milestones
- **Milestone 1: Production Launch**
  - **Target Date:** 2026-07-15
  - **Definition:** System live for 500 users with all High Priority features.
- **Milestone 2: MVP Feature-Complete**
  - **Target Date:** 2026-09-15
  - **Definition:** Medium and Low priority features (A/B testing, Import/Export) fully deployed.
- **Milestone 3: Post-Launch Stability Confirmed**
  - **Target Date:** 2026-11-15
  - **Definition:** 90 days of 99.9% uptime achieved.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team protocol, no formal meeting minutes are kept. The following are synthesized summaries of decision-making threads from the `#proj-pinnacle` Slack channel.

### Thread 1: The "Pipeline Pain" Discussion
**Date:** 2023-11-12  
**Participants:** Hessa, Celine, Asha  
**Discussion:** Celine pointed out that the 45-minute CI pipeline is causing developers to switch contexts too often, leading to productivity loss. Asha suggested moving to a containerized build agent.  
**Decision:** Hessa approved a two-week "Tech Debt Sprint" focused solely on pipeline parallelization. Celine will implement Docker layer caching by the end of the month.

### Thread 2: Notification Channel Scope
**Date:** 2023-12-05  
**Participants:** Hessa, Ayo, Asha  
**Discussion:** Ayo (UX) argued that push notifications are intrusive for internal tools. Asha noted that for "Critical Overheat" alerts, push is the only way to ensure immediate response from field engineers.  
**Decision:** The system will support all four channels, but "Push" will be disabled by default and require a manual "Opt-In" via the user preference center.

### Thread 3: The Sponsor Rotation Crisis
**Date:** 2024-01-15  
**Participants:** Hessa, Celine, Ayo, Asha  
**Discussion:** Hessa informed the team that the primary project sponsor is rotating out of their role. The team expressed concern about budget stability for the $5M+ fund.  
**Decision:** The team decided to "accept and monitor." Hessa will increase the frequency of board-level reporting to ensure the new sponsor inherits a clear understanding of the project's value and current status.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$5,250,000 USD**

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $3,100,000 | 4-person team (Full-time salaries + Asha Liu's contract fees) over 3 years. |
| **Infrastructure** | $850,000 | Azure Consumption (SQL Hyperscale, Kafka Confluent Cloud, APIM, Blob Storage). |
| **External Consulting**| $400,000 | Independent assessment consultant to mitigate scope creep. |
| **Tooling & Licenses**| $200,000 | SendGrid, Twilio, Azure DevOps, Playwright Enterprise licenses. |
| **Contingency** | $700,000 | Reserve for unforeseen technical hurdles or extended medical leaves. |

**Budget Notes:**
- Personnel costs include a 15% buffer for cost-of-living adjustments.
- Infrastructure costs are projected based on a 10x growth in data volume from current levels.

---

## 12. APPENDICES

### Appendix A: Kafka Topic Definitions
To ensure event consistency, the following topics have been defined with a 7-day retention policy:
1. `asset-events`: Tracks all changes to energy assets (Created, Updated, Deleted).
2. `notification-requests`: Queue for the `NotificationService` to process outgoing alerts.
3. `file-scan-results`: Results from the virus scanning function to trigger file accessibility.
4. `system-audit-trail`: Global stream of all administrative actions for the AuditLog table.

### Appendix B: Regulatory Review Cycle
Because Deepwell Data operates in the renewable energy sector, all production releases must undergo a "Regulatory Compliance Review."
- **Review Period:** 2 weeks prior to each quarterly release.
- **Audit Focus:** Data residency (ensuring data stays within specified Azure regions) and access control (ensuring the "Principle of Least Privilege" is applied to the API Gateway).
- **Sign-off:** Requires a digital signature from the Legal and Compliance department before the `release` branch can be merged into `main`.