Due to the extreme length requirements (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification. It serves as the primary source of truth for the development team at Flintrock Engineering.

***

# PROJECT SPECIFICATION: WAYFINDER (V1.0.0)
**Company:** Flintrock Engineering  
**Industry:** Media and Entertainment  
**Project Lead:** Juno Oduya (CTO)  
**Date of Issue:** October 24, 2023  
**Status:** Active/In-Development  
**Classification:** Confidential / Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
The "Wayfinder" project represents a strategic pivot for Flintrock Engineering. The current iteration of the customer-facing application has suffered a catastrophic failure in user reception, characterized by critical stability issues, an unintuitive user interface, and systemic performance bottlenecks. User feedback indicates a "fundamental disconnect" between the product's functionality and the needs of the media and entertainment sector.

The business justification for this rebuild is based on the urgent need to stop churn and recapture market share. The existing legacy system is an architectural liability, utilizing monolithic patterns that cannot scale. Wayfinder is not merely a "skin" update but a total structural rebuild. By migrating to a modern, event-driven microservices architecture using the Microsoft stack, Flintrock Engineering intends to transition from a reactive maintenance posture to a proactive feature-delivery model.

### 1.2 ROI Projection and Financial Impact
The total investment for Wayfinder is budgeted at $3,000,000. The Return on Investment (ROI) is projected across three primary vectors:

1.  **Operational Cost Reduction:** The legacy system’s inefficiency results in high cloud overhead. The new architecture targets a 35% reduction in cost per transaction. Based on current volumes, this is projected to save the company approximately $450,000 annually in Azure consumption costs.
2.  **Customer Acquisition and Retention:** By hitting the target of 10,000 Monthly Active Users (MAU) within six months of launch, the company expects a 20% increase in subscription-based revenue within the media entertainment segment.
3.  **Development Velocity:** The transition to microservices and Kafka-driven communication will reduce the time-to-market for new features from quarterly cycles to bi-weekly sprints, reducing the "cost of delay" for high-value features.

The project is characterized by high executive visibility. Failure to deliver the "critical" launch blockers—specifically the customizable dashboard and the secure file upload system—will be viewed as a failure of the engineering organization to address the core issues that led to the previous version's collapse.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Overview
Wayfinder is built on a fully integrated Microsoft stack to ensure maximum compatibility and support. The system follows a microservices architecture where each domain (User Management, Content Delivery, Analytics, Billing) is isolated.

**Core Stack:**
- **Backend:** C# / .NET 7/8
- **Database:** Azure SQL Database (Hyperscale tier)
- **Compute:** Azure Functions (Serverless) for event processing; Azure Kubernetes Service (AKS) for long-running services.
- **Messaging/Event Stream:** Apache Kafka (Confluent Cloud)
- **Frontend:** Mobile application developed via .NET MAUI for cross-platform deployment (iOS/Android).

### 2.2 Event-Driven Communication
To avoid tight coupling between services, Wayfinder utilizes a "choreography" pattern via Kafka. When a user uploads a file, the `FileService` publishes a `FileUploaded` event. The `VirusScanService` and `CDNService` consume this event independently, ensuring that a failure in the CDN distribution does not block the virus scanning process.

### 2.3 ASCII Architecture Diagram
```text
[ Mobile Client (.NET MAUI) ]
          |
          v
[ Azure Front Door / API Gateway ]
          |
          +---------------------------------------+
          |                |                      |
[ User Service ]    [ Content Service ]    [ Analytics Service ]
 (Azure Function)    (Azure Function)       (Azure Function)
          |                |                      |
          +----------------+----------------------+
                           |
                 [ Kafka Event Bus ] <--- (Event Streams)
                           |
          +----------------+----------------------+
          |                |                      |
[ Virus Scan Svc ]  [ CDN Distributor ]    [ Notification Svc ]
                           |
                    [ Azure Blob Storage ]
                           |
                    [ Azure SQL DB ] <--- (Multi-tenant Schema)
```

### 2.4 Data Residency and Compliance
Due to GDPR (EU) and CCPA (California) requirements, all user PII (Personally Identifiable Information) must reside in the `North Europe` and `West Europe` Azure regions. The architecture employs a "Silo" pattern for high-value tenants and a "Pool" pattern for standard users to ensure strict data isolation.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Review
*   **Functional Requirement:** The landing screen must allow users to personalize their experience by adding, removing, and rearranging widgets (e.g., "Recent Uploads," "Industry Trends," "Account Health").
*   **Technical Detail:** The dashboard state is persisted as a JSON blob in the `UserPreferences` table. The frontend uses a grid-based layout engine where each widget is a separate component.
*   **Interaction Model:** Users enter "Edit Mode," allowing them to long-press a widget to drag it across a 12-column grid.
*   **Constraints:** A maximum of 12 widgets can be active simultaneously to prevent mobile performance degradation. Widgets must be responsive to both portrait and landscape orientations.
*   **Acceptance Criteria:** User can drag Widget A to Position B, refresh the app, and see Widget A still in Position B.

### 3.2 Multi-Tenant Data Isolation with Shared Infrastructure
*   **Priority:** Medium
*   **Status:** In Review
*   **Functional Requirement:** The system must support multiple corporate clients (tenants) on a shared set of Azure SQL databases without the risk of cross-tenant data leakage.
*   **Technical Detail:** Wayfinder utilizes a "Discriminator Column" approach. Every table in the database contains a `TenantId` (GUID). All database queries are intercepted by a Global Query Filter in the .NET Entity Framework Core layer, automatically appending `WHERE TenantId = @CurrentTenantId` to every request.
*   **Security Logic:** The `TenantId` is extracted from the JWT (JSON Web Token) claims upon authentication. If a user attempts to access a resource with a mismatched `TenantId`, the system must return a `403 Forbidden` and log a security alert in Azure Monitor.
*   **Acceptance Criteria:** A user from Tenant A cannot access any record belonging to Tenant B, even if the exact Primary Key is known.

### 3.3 API Rate Limiting and Usage Analytics
*   **Priority:** High
*   **Status:** Blocked (Dependent on 3rd party API stability)
*   **Functional Requirement:** To prevent abuse and ensure fair resource allocation, the system must throttle requests based on the user's subscription tier.
*   **Technical Detail:** Implementation uses a "Leaky Bucket" algorithm. Rate limits are stored in an Azure Cache for Redis instance to ensure sub-millisecond latency during check. 
    - *Tier 1 (Free):* 100 requests/hour.
    - *Tier 2 (Pro):* 5,000 requests/hour.
    - *Tier 3 (Enterprise):* Unlimited/Custom.
*   **Analytics:** Every request is logged to an `ApiUsage` table via a Kafka stream to generate monthly billing reports.
*   **Acceptance Criteria:** When the 101st request is made by a Free user within one hour, the API returns a `429 Too Many Requests` response with a `Retry-After` header.

### 3.4 File Upload with Virus Scanning and CDN Distribution
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Progress
*   **Functional Requirement:** Users must be able to upload large media files (up to 2GB) which are scanned for malware before being distributed globally via CDN.
*   **Technical Detail:** 
    1. **Upload:** The app requests a Shared Access Signature (SAS) token from the `FileService`. The app uploads directly to Azure Blob Storage (Cold Tier) to avoid overloading the API gateway.
    2. **Scanning:** An Azure Function is triggered by the `BlobCreated` event. It forwards the file to a ClamAV-based scanning cluster.
    3. **Distribution:** Once the `ScanResult` is "Clean," a Kafka event triggers the `CDNService` to move the file to the Hot Tier and invalidate the CDN cache.
*   **Acceptance Criteria:** A file containing the EICAR test virus must be quarantined and the user notified via an in-app alert.

### 3.5 Offline-First Mode with Background Sync
*   **Priority:** Medium
*   **Status:** Blocked
*   **Functional Requirement:** Users must be able to perform basic dashboard updates and file metadata edits while offline.
*   **Technical Detail:** The application implements a local SQLite database using the "Outbox Pattern." Changes are stored in a `LocalQueue` table. A background worker (using .NET MAUI's background tasking) monitors connectivity. Upon reconnection, the worker pushes the queued changes to the server in a single transactional batch.
*   **Conflict Resolution:** The system uses "Last Write Wins" based on a UTC timestamp. If a record was changed on the server and the client simultaneously, the most recent timestamp persists.
*   **Acceptance Criteria:** User can edit a "Project Name" while in Airplane Mode; upon disabling Airplane Mode, the change reflects on the server within 30 seconds.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and return JSON. Base URL: `https://api.wayfinder.flintrock.io/v1/`

### 4.1 User Authentication
- **Endpoint:** `POST /auth/login`
- **Request:** `{ "email": "string", "password": "string" }`
- **Response:** `200 OK { "token": "JWT_STRING", "expires": "ISO8601_DATE" }`
- **Description:** Authenticates user and returns a scoped JWT.

### 4.2 Dashboard Layout Persistence
- **Endpoint:** `PUT /user/dashboard/layout`
- **Request:** `{ "layout_id": "GUID", "widgets": [ { "id": "widget_1", "pos_x": 0, "pos_y": 0 } ] }`
- **Response:** `204 No Content`
- **Description:** Saves the drag-and-drop positions of dashboard widgets.

### 4.3 SAS Token Request (Upload)
- **Endpoint:** `POST /files/upload-request`
- **Request:** `{ "fileName": "string", "fileSize": "long" }`
- **Response:** `201 Created { "uploadUrl": "HTTPS_AZURE_BLOB_URL", "uploadId": "GUID" }`
- **Description:** Generates a temporary secure URL for direct-to-cloud upload.

### 4.4 File Status Query
- **Endpoint:** `GET /files/status/{uploadId}`
- **Request:** Path Parameter `uploadId`
- **Response:** `200 OK { "status": "Scanning|Clean|Infected", "cdnUrl": "string|null" }`
- **Description:** Checks if the virus scan is complete.

### 4.5 Tenant Management (Admin)
- **Endpoint:** `POST /admin/tenants`
- **Request:** `{ "companyName": "string", "region": "EU|US", "tier": "string" }`
- **Response:** `201 Created { "tenantId": "GUID" }`
- **Description:** Creates a new isolated tenant environment.

### 4.6 Rate Limit Status
- **Endpoint:** `GET /user/quota`
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK { "remaining": 450, "resetTime": "ISO8601_DATE" }`
- **Description:** Returns the user's current API usage quota.

### 4.7 Content Metadata Update
- **Endpoint:** `PATCH /content/{contentId}`
- **Request:** `{ "title": "string", "tags": ["string"] }`
- **Response:** `200 OK { "updatedAt": "ISO8601_DATE" }`
- **Description:** Updates metadata for a specific media asset.

### 4.8 System Health Check
- **Endpoint:** `GET /health`
- **Request:** None
- **Response:** `200 OK { "status": "Healthy", "db": "Connected", "kafka": "Connected" }`
- **Description:** Used by Azure Load Balancer for health probing.

---

## 5. DATABASE SCHEMA

The system uses Azure SQL. The following tables are core to the Wayfinder ecosystem.

### 5.1 Table Definitions

| Table Name | Key Field | Type | Relationship | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` (PK) | GUID | 1:N with `Users` | The root entity for multi-tenancy. |
| `Users` | `UserId` (PK) | GUID | N:1 with `Tenants` | User profiles and authentication data. |
| `UserPreferences` | `PrefId` (PK) | GUID | 1:1 with `Users` | Stores JSON blob for dashboard layout. |
| `Files` | `FileId` (PK) | GUID | N:1 with `Users` | Metadata for uploaded media assets. |
| `ScanResults` | `ScanId` (PK) | GUID | 1:1 with `Files` | Results of ClamAV scanning process. |
| `ApiUsage` | `LogId` (PK) | BIGINT | N:1 with `Users` | Audit trail of every API call made. |
| `TenantsConfig` | `ConfigId` (PK) | GUID | 1:1 with `Tenants` | Regional settings and compliance flags. |
| `Widgets` | `WidgetId` (PK) | INT | N:M with `UserPreferences` | Registry of available system widgets. |
| `AuditLogs` | `EventId` (PK) | BIGINT | N:1 with `Users` | Security logs for GDPR compliance. |
| `SubscriptionTiers` | `TierId` (PK) | INT | 1:N with `Tenants` | Definitions of rate limits and pricing. |

### 5.2 Key Relationships and Constraints
- **Foreign Key Constraint:** All tables (except `Tenants`) must have a `TenantId` column. A composite index is applied to `(TenantId, PrimaryKey)` to optimize partitioned queries.
- **Data Integrity:** The `ScanResults` table has a check constraint preventing a `cdnUrl` from being populated if the `ScanStatus` is not 'Clean'.
- **Performance Note:** 30% of queries in the legacy system bypassed the ORM. In Wayfinder, raw SQL is permitted only in the `ApiUsage` reporting service and must be reviewed by Sienna Kim for SQL injection risks.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Wayfinder utilizes three distinct environments to ensure stability.

1.  **Development (Dev):**
    - Used by developers for feature iteration.
    - Automated deployment via GitHub Actions upon merge to `develop` branch.
    - Mocked Kafka streams for cost efficiency.
2.  **Staging (QA):**
    - Mirror of Production.
    - **Manual QA Gate:** No code enters production without a signed-off QA report.
    - 2-day turnaround for bug fixes found during the gate process.
    - Full data residency simulation in EU regions.
3.  **Production (Prod):**
    - High-availability cluster across Azure availability zones.
    - Blue-Green deployment strategy to ensure zero downtime.
    - Managed by Juno Oduya and Sienna Kim.

### 6.2 CI/CD Pipeline
The pipeline is managed via Azure DevOps. The workflow is:
`Feature Branch` $\rightarrow$ `Pull Request` $\rightarrow$ `Develop Branch` $\rightarrow$ `QA Branch` $\rightarrow$ `Manual Gate` $\rightarrow$ `Main Branch` $\rightarrow$ `Production`.

### 6.3 Infrastructure as Code (IaC)
All infrastructure is defined using Terraform. This ensures that the EU and US environments are identical, preventing "environment drift" and simplifying the audit process for GDPR compliance.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit / Moq.
- **Requirement:** 80% code coverage minimum.
- **Focus:** Business logic within Azure Functions and domain services.

### 7.2 Integration Testing
- **Framework:** Postman / Newman.
- **Focus:** Testing the "Happy Path" of the Kafka event stream. For example, simulating a file upload and verifying that the `ScanResults` table is updated correctly.
- **Frequency:** Executed daily in the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Appium.
- **Focus:** User journeys on the mobile app.
    - *Scenario A:* User logs in $\rightarrow$ Uploads file $\rightarrow$ Checks dashboard for status.
    - *Scenario B:* User enters "Edit Mode" $\rightarrow$ Drags widget $\rightarrow$ Saves $\rightarrow$ Refreshes.
- **Gate:** Must pass 100% of E2E critical paths before the 2-day QA gate is closed.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Budget cut by 30% in next fiscal quarter | Medium | High | Negotiate timeline extension with stakeholders; prioritize "Critical" features over "Medium." |
| **R2** | Integration partner API is undocumented/buggy | High | Medium | De-scope affected features if unresolved by Milestone 2; implement a "Wrapper" layer to sanitize partner data. |
| **R3** | Data residency breach (GDPR) | Low | Critical | Quarterly audits by Sienna Kim; strict Azure Policy restrictions on resource location. |
| **R4** | Technical debt from raw SQL migrations | Medium | Medium | Mandatory peer review for all raw SQL; implement a migration script validation tool. |

**Probability/Impact Matrix:**
- **High Impact/High Probability:** (None currently, but R2 is approaching).
- **High Impact/Low Probability:** R3.
- **Medium Impact/High Probability:** R2.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with strict target dates.

### 9.1 Phase 1: Foundation (Now – June 2026)
- Focus on Core Infrastructure, Tenant Isolation, and the File Upload system.
- **Milestone 1: Post-launch stability confirmed.**
- **Target Date:** 2026-06-15.
- **Success Criteria:** 99.9% uptime for 30 consecutive days; zero critical security vulnerabilities.

### 9.2 Phase 2: Monetization (June 2026 – August 2026)
- Focus on API Rate Limiting and Billing Integration.
- **Milestone 2: First paying customer onboarded.**
- **Target Date:** 2026-08-15.
- **Success Criteria:** Successful transaction processing and tenant-specific quota enforcement.

### 9.3 Phase 3: Scaling (August 2026 – October 2026)
- Focus on Offline-First mode and External Beta.
- **Milestone 3: External beta with 10 pilot users.**
- **Target Date:** 2026-10-15.
- **Success Criteria:** Positive feedback from 7/10 pilot users; MAU growth trajectory confirmed.

---

## 10. MEETING NOTES (Running Log)

*Note: This is a truncated extract from the 200-page unsearchable shared document.*

### Meeting Date: 2023-11-12
**Attendees:** Juno, Hiro, Sienna, Ren
**Topic:** Dashboard Widgets vs. Performance
- **Hiro:** Expressed concern that the drag-and-drop interface in .NET MAUI might lag on older Android devices.
- **Juno:** Agreed. Suggested limiting the number of active widgets to 12.
- **Ren:** Asked if we should use a third-party library for the grid.
- **Decision:** Hiro will implement a custom lightweight grid to avoid dependency bloat.
- **Action Item:** Hiro to provide a prototype by next Friday.

### Meeting Date: 2023-12-05
**Attendees:** Juno, Sienna, Ren
**Topic:** The "Raw SQL" Performance Problem
- **Sienna:** Warned that the current use of raw SQL in 30% of queries is creating a "migration nightmare."
- **Juno:** Acknowledged. The legacy ORM was too slow for the `ApiUsage` reports.
- **Ren:** Suggested using Dapper as a middle ground.
- **Decision:** Dapper will be the standard for performance-critical queries. Raw SQL strings are now banned in the codebase.
- **Action Item:** Ren to refactor the `ApiUsage` query using Dapper.

### Meeting Date: 2024-01-20
**Attendees:** Juno, Hiro, Sienna
**Topic:** Third-Party API Blocker
- **Juno:** Reported that the integration partner's API is returning 429s during basic load tests.
- **Sienna:** Noted that this is blocking the "API Rate Limiting" feature from being fully tested.
- **Hiro:** Suggested we implement a mock server to bypass the partner for now.
- **Decision:** Implement a "Mock Partner Service" to allow development to continue. If the partner doesn't provide documentation by Milestone 2, the feature will be de-scoped.
- **Action Item:** Sienna to build the Mock API.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,800,000 | 15 distributed engineers across 5 countries. |
| **Azure Infrastructure** | 20% | $600,000 | SQL Hyperscale, AKS, Kafka (Confluent), Blob Storage. |
| **Software & Tools** | 10% | $300,000 | JIRA, GitHub Enterprise, Appium, ClamAV Enterprise. |
| **Contingency Fund** | 10% | $300,000 | Reserved for R1 (Budget cuts) and R2 (Partner issues). |

**Financial Note:** The personnel cost includes a "geographic weighting" to account for different cost-of-living standards across the 5 countries where the team is distributed.

---

## 12. APPENDICES

### Appendix A: JSON Schema for Dashboard Layout
The following schema defines how the `UserPreferences` table stores the dashboard state:
```json
{
  "userId": "GUID",
  "theme": "dark|light",
  "layout": [
    {
      "widgetId": 101,
      "position": { "x": 0, "y": 0, "w": 6, "h": 4 },
      "settings": { "refreshRate": "5m", "showNotifications": true }
    },
    {
      "widgetId": 202,
      "position": { "x": 6, "y": 0, "w": 6, "h": 4 },
      "settings": { "filter": "recent_only" }
    }
  ]
}
```

### Appendix B: Virus Scanning Workflow Detail
The `VirusScanService` operates as an asynchronous pipeline:
1. **Trigger:** `BlobCreated` $\rightarrow$ Azure Function.
2. **Processing:** File is streamed to the ClamAV cluster via a secure internal VNET.
3. **Decision Tree:**
    - *Clean:* Update `ScanResults` $\rightarrow$ Send `FileClean` event to Kafka $\rightarrow$ CDNDistribution.
    - *Infected:* Update `ScanResults` $\rightarrow$ Delete Blob $\rightarrow$ Send `FileInfected` event to Kafka $\rightarrow$ NotificationService.
    - *Error:* Retry 3 times $\rightarrow$ Move to `ManualReview` queue.