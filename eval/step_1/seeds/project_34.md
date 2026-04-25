# PROJECT SPECIFICATION: PROJECT IRONCLAD
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 26, 2023  
**Company:** Coral Reef Solutions  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Ironclad" is a strategic internal enterprise tool developed by Coral Reef Solutions within the automotive sector. The primary objective of Ironclad is to establish a robust, scalable, and secure integration layer that syncs Coral Reef Solutions' internal data ecosystems with a strategic partner's external API. Unlike standard internal tools, Ironclad is governed by an external timeline dictated by the partner's API release schedule, necessitating a highly flexible and adaptive development approach.

### 1.2 Business Justification
The automotive industry is currently undergoing a rapid transition toward integrated digital services. Coral Reef Solutions currently relies on a fragmented legacy system for partner data exchange, which involves manual CSV uploads and asynchronous email confirmations. This inefficiency leads to data latency of up to 48 hours, resulting in missed logistics opportunities and procurement errors. 

Ironclad replaces this legacy sprawl with a real-time, event-driven synchronization engine. By integrating directly with the partner’s API, Coral Reef Solutions will automate the supply chain hand-off, reduce manual data entry errors by an estimated 92%, and ensure that the internal inventory reflects partner availability in real-time.

### 1.3 ROI Projection
Despite being an unfunded project bootstrapping with existing team capacity, the projected Return on Investment (ROI) is significant. The primary financial driver is the reduction of the "cost per transaction." Currently, the legacy process costs approximately $4.20 per transaction when accounting for labor and error correction. Ironclad aims to reduce this to $2.73 (a 35% reduction).

**Financial Projections (Post-Launch Year 1):**
- **Expected Volume:** 1.2 million transactions per annum.
- **Gross Savings:** $1.76 million in operational efficiency.
- **Personnel Cost (Bootstrapped):** Absorbed into existing Opex (15 FTEs across 5 countries).
- **Infrastructure Spend:** Estimated at $12,000/month for Azure resources.
- **Net Projected Benefit:** ~$1.6 million in the first year of full operation.

### 1.4 Strategic Alignment
Ironclad aligns with the corporate goal of "Digital Transformation 2025," moving the company away from monolithic legacy software toward a cloud-native, hexagonal architecture. This ensures that as other partners are onboarded, the "adapters" can be swapped or added without rewriting the core business logic.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Ironclad utilizes a Hexagonal Architecture to decouple the core business logic from external dependencies (the partner API, the database, and the UI). This is critical because the partner API is subject to change on their timeline, and we must be able to update the "Adapter" without affecting the "Domain."

**Core Components:**
- **The Domain (Core):** Contains the business entities and domain services. It has no knowledge of Azure, SQL, or the external API.
- **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IPartnerApiPort`, `IUserRepository`).
- **Adapters:** Concrete implementations of the ports (e.g., `PartnerApiAzureAdapter`, `SqlUserRepository`).

### 2.2 Tech Stack
- **Language/Framework:** C# / .NET 8 (LTS)
- **Cloud Provider:** Microsoft Azure
- **Database:** Azure SQL Database (Hyperscale Tier)
- **Compute:** Azure Functions (Serverless) for event-driven triggers; Azure App Service for the API layer.
- **Configuration/Toggles:** LaunchDarkly for feature flags and canary deployments.
- **Messaging:** Azure Service Bus for asynchronous communication between modules.
- **Identity:** Azure Active Directory (Azure AD) integration.

### 2.3 System Diagram (ASCII Description)

```text
[ External Partner API ] <---> [ Partner Adapter ] <--- (Port) --- [ Domain Logic ] --- (Port) ---> [ Persistence Adapter ] <---> [ Azure SQL ]
                                                                        ^
                                                                        |
[ Internal Client UI ] <---> [ Web API Adapter ] <--- (Port) -----------+----------- (Port) ---> [ Notification Adapter ] <---> [ SendGrid/Twilio ]
                                                                        |
                                                                 [ LaunchDarkly ]
                                                               (Feature Flags/Canary)
```

### 2.4 Data Flow
1. **Ingestion:** An Azure Function triggers on a timer or webhook from the partner API.
2. **Adaptation:** The `PartnerAdapter` translates the external JSON payload into a Domain Entity.
3. **Processing:** The Domain Logic validates the entity and applies business rules (e.g., automotive part compatibility checks).
4. **Persistence:** The `PersistenceAdapter` saves the state to Azure SQL.
5. **Notification:** The `NotificationAdapter` triggers alerts to internal users via the Notification System.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Progress

**Description:**
The system must ensure that only authorized personnel within Coral Reef Solutions can access specific modules of Ironclad. Given the distributed nature of the team and the sensitivity of automotive procurement data, a granular RBAC system is required.

**Functional Requirements:**
- **Identity Integration:** Integration with Azure AD using OpenID Connect (OIDC).
- **Role Hierarchy:**
    - `SuperAdmin`: Full system access, including LaunchDarkly flag management and user auditing.
    - `ProcurementManager`: Access to partner API sync logs, report generation, and vendor management.
    - `SupportEngineer`: Access to read-only logs and the ability to trigger manual syncs.
    - `Viewer`: Read-only access to the dashboard.
- **Session Management:** JWT (JSON Web Tokens) with a 15-minute expiration and sliding window renewal.
- **Audit Logging:** Every privilege escalation or role change must be logged in the `AuditLogs` table with a timestamp and the actor's ID.

**Technical Implementation:**
The system implements a custom `ClaimsTransformation` in .NET to map Azure AD Groups to internal Ironclad Roles. The `AuthorizationHandler` will check for specific permissions (e.g., `CAN_SYNC_PARTNER_DATA`) rather than just roles to allow for future flexibility.

---

### 3.2 Notification System (Email, SMS, In-App, Push)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Ironclad requires a multi-channel notification engine to alert users of critical failures in the partner API sync or high-priority business events (e.g., "Inventory Critical Low"). This is a launch blocker because without it, the 15-person distributed team will not know when the automated syncs fail.

**Functional Requirements:**
- **Channel Routing:** Users can configure their preferred channel per notification type.
    - *Critical Errors:* SMS and Push.
    - *Daily Summaries:* Email.
    - *System Updates:* In-App.
- **Template Engine:** Use of Handlebars.NET for dynamic email and SMS templates.
- **Retry Logic:** Exponential backoff for failed notifications via Azure Service Bus dead-letter queues.
- **Throttling:** Prevent "notification storms" by aggregating multiple similar errors into a single digest.

**Technical Implementation:**
A `NotificationDispatcher` service will implement the Strategy Pattern. Depending on the `NotificationPreference` retrieved from the database, the dispatcher will route the payload to the `EmailAdapter` (SendGrid), `SmsAdapter` (Twilio), or `PushAdapter` (Azure Notification Hubs).

---

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** In Review

**Description:**
To protect against credential theft in a remote-first environment, 2FA is mandatory for all `SuperAdmin` and `ProcurementManager` roles. This includes support for FIDO2 hardware keys (e.g., YubiKey).

**Functional Requirements:**
- **Enrollment Flow:** A guided wizard for users to register their primary and backup 2FA methods.
- **Hardware Key Support:** Implementation of WebAuthn API to allow FIDO2/U2F devices.
- **Fallback Mechanisms:** Time-based One-Time Passwords (TOTP) via Google Authenticator or Microsoft Authenticator as a secondary option.
- **Recovery Codes:** Generation of 10 one-time-use recovery codes provided to the user upon setup.

**Technical Implementation:**
The 2FA layer sits between the primary authentication and the issuance of the final JWT. The system will track the `AuthLevel` of the session. A session with `AuthLevel = 1` (Password only) cannot access "Sensitive" endpoints; it must be upgraded to `AuthLevel = 2` via a successful 2FA challenge.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** Complete

**Description:**
Users must be able to upload technical specification documents (PDFs, CAD files) related to automotive parts. These files are then distributed to internal teams via a CDN for low-latency access.

**Functional Requirements:**
- **Secure Upload:** Files are uploaded to a "Quarantine" Azure Blob Storage container.
- **Virus Scanning:** Triggering an Azure Function that invokes a scanning API (e.g., Windows Defender or a third-party ClamAV wrapper) to check for malware.
- **CDN Distribution:** Once cleared, files are moved to a "Production" container integrated with Azure CDN.
- **File Type Validation:** Only `.pdf`, `.dwg`, `.step`, and `.xlsx` are permitted.

**Technical Implementation:**
The process follows a Pipeline pattern: `Upload` $\rightarrow$ `Scan` $\rightarrow$ `Move` $\rightarrow$ `Notify`. The metadata (file hash, scan result, CDN URL) is stored in the `DocumentMetadata` table.

---

### 3.5 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:**
Ironclad provides a set of endpoints that internal "customers" (other departments within Coral Reef Solutions) use to consume the synced partner data. This API must be professional, versioned, and provide a safe sandbox for testing.

**Functional Requirements:**
- **Versioning:** URI-based versioning (e.g., `/api/v1/inventory`, `/api/v2/inventory`).
- **Sandbox Environment:** A mirrored environment with mocked data where internal teams can test their integrations without affecting production data.
- **Rate Limiting:** Implementation of a "Leaky Bucket" algorithm to prevent a single internal department from overwhelming the system.
- **API Documentation:** Automated Swagger/OpenAPI 3.0 documentation hosted at `/swagger`.

**Technical Implementation:**
The API is built using ASP.NET Core Minimal APIs for performance. The Sandbox is a separate Azure App Service instance pointing to a "Sandbox" SQL database, utilizing a separate set of Azure AD service principals for authentication.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Header: `Authorization: Bearer <token>`.

### 4.1 `GET /api/v1/sync/status`
- **Description:** Retrieves the current status of the partner API synchronization.
- **Request:** None.
- **Response (200 OK):**
```json
{
  "lastSyncTime": "2023-10-26T14:30:00Z",
  "status": "Success",
  "recordsProcessed": 4500,
  "errors": 0
}
```

### 4.2 `POST /api/v1/sync/trigger`
- **Description:** Manually triggers a synchronization event. (Restricted to `ProcurementManager`).
- **Request:** `{"forceFullSync": true}`
- **Response (202 Accepted):**
```json
{
  "jobId": "abc-123-xyz",
  "estimatedCompletion": "2023-10-26T14:45:00Z"
}
```

### 4.3 `GET /api/v1/inventory/{partNumber}`
- **Description:** Fetches the current availability of a specific automotive part from the synced partner data.
- **Request:** `partNumber` (Path parameter).
- **Response (200 OK):**
```json
{
  "partNumber": "CRS-9901-X",
  "quantity": 150,
  "location": "Warehouse-B",
  "lastUpdated": "2023-10-26T10:00:00Z"
}
```

### 4.4 `PUT /api/v1/users/{userId}/preferences`
- **Description:** Updates notification preferences for a user.
- **Request:** `{"email": true, "sms": false, "push": true}`
- **Response (200 OK):**
```json
{
  "status": "Updated",
  "userId": "user-789"
}
```

### 4.5 `POST /api/v1/documents/upload`
- **Description:** Uploads a technical file for virus scanning.
- **Request:** Multipart Form Data (File).
- **Response (202 Accepted):**
```json
{
  "trackingId": "file-upload-456",
  "status": "Scanning"
}
```

### 4.6 `GET /api/v1/documents/{trackingId}/status`
- **Description:** Checks if a file has passed virus scanning and is available on the CDN.
- **Request:** `trackingId` (Path parameter).
- **Response (200 OK):**
```json
{
  "status": "Clean",
  "cdnUrl": "https://cdn.coralreef.com/docs/abc.pdf"
}
```

### 4.7 `POST /api/v1/auth/mfa/register`
- **Description:** Registers a new FIDO2 hardware key.
- **Request:** `{"challenge": "base64-challenge-string"}`
- **Response (200 OK):**
```json
{
  "registrationId": "reg-112233",
  "status": "PendingVerification"
}
```

### 4.8 `DELETE /api/v1/cache/flush`
- **Description:** Clears the internal Redis cache for partner data. (Restricted to `SuperAdmin`).
- **Request:** None.
- **Response (200 OK):**
```json
{
  "message": "Cache cleared successfully"
}
```

---

## 5. DATABASE SCHEMA

The database is an Azure SQL instance. All tables utilize `DateTimeOffset` for timestamps to support the distributed team across 5 time zones.

### 5.1 Table Definitions

1. **`Users`**
   - `UserId` (PK, Guid)
   - `AzureAdObjectId` (Unique, String)
   - `Email` (String)
   - `FullName` (String)
   - `CreatedAt` (DateTimeOffset)
   - `LastLogin` (DateTimeOffset)

2. **`Roles`**
   - `RoleId` (PK, Int)
   - `RoleName` (String) - (e.g., 'SuperAdmin', 'Viewer')
   - `Description` (String)

3. **`UserRoles`**
   - `UserId` (FK, Guid)
   - `RoleId` (FK, Int)
   - `AssignedAt` (DateTimeOffset)

4. **`PartnerInventory`**
   - `InventoryId` (PK, Guid)
   - `PartNumber` (Indexed, String)
   - `Quantity` (Int)
   - `Price` (Decimal)
   - `PartnerId` (FK, Int)
   - `SyncTimestamp` (DateTimeOffset)

5. **`SyncLogs`**
   - `LogId` (PK, BigInt)
   - `StartTime` (DateTimeOffset)
   - `EndTime` (DateTimeOffset)
   - `Status` (String) - (Success/Failure)
   - `RecordsProcessed` (Int)
   - `ErrorMessage` (Text, Nullable)

6. **`NotificationPreferences`**
   - `PreferenceId` (PK, Guid)
   - `UserId` (FK, Guid)
   - `EmailEnabled` (Bit)
   - `SmsEnabled` (Bit)
   - `PushEnabled` (Bit)

7. **`DocumentMetadata`**
   - `DocId` (PK, Guid)
   - `FileName` (String)
   - `CdnUrl` (String)
   - `VirusScanStatus` (String) - (Pending, Clean, Infected)
   - `UploadedBy` (FK, Guid)
   - `UploadDate` (DateTimeOffset)

8. **`MfaDevices`**
   - `DeviceId` (PK, Guid)
   - `UserId` (FK, Guid)
   - `DeviceType` (String) - (FIDO2, TOTP)
   - `PublicKey` (Text)
   - `CreatedAt` (DateTimeOffset)

9. **`AuditLogs`**
   - `AuditId` (PK, BigInt)
   - `UserId` (FK, Guid)
   - `Action` (String)
   - `ResourceImpacted` (String)
   - `Timestamp` (DateTimeOffset)
   - `IpAddress` (String)

10. **`FeatureFlags`**
    - `FlagId` (PK, Guid)
    - `FlagKey` (String) - (Matches LaunchDarkly key)
    - `IsEnabled` (Bit)
    - `LastModified` (DateTimeOffset)

### 5.2 Relationships
- `Users` $\rightarrow$ `UserRoles` (1:N)
- `Roles` $\rightarrow$ `UserRoles` (1:N)
- `Users` $\rightarrow$ `NotificationPreferences` (1:1)
- `Users` $\rightarrow$ `DocumentMetadata` (1:N)
- `Users` $\rightarrow$ `MfaDevices` (1:N)
- `Users` $\rightarrow$ `AuditLogs` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments to ensure stability.

| Environment | Purpose | Database | Deployment Method |
| :--- | :--- | :--- | :--- |
| **Dev** | Active development & unit testing | Dev-SQL (Small) | Auto-deploy from `develop` branch |
| **Staging** | QA, UAT, and Sandbox API testing | Staging-SQL (Medium) | Manual trigger from `release` branch |
| **Prod** | Live internal enterprise tool | Prod-SQL (Hyperscale) | Canary release via LaunchDarkly |

### 6.2 Deployment Pipeline
1. **CI Phase:** GitHub Actions runs .NET build and executes unit tests. If tests fail, the build is rejected.
2. **CD Phase:** Artifacts are pushed to Azure Container Registry.
3. **Canary Release:** 
    - New code is deployed to a small subset of servers.
    - LaunchDarkly flags are used to route 5% of internal traffic to the new version.
    - Metrics (Error rate, Latency) are monitored for 2 hours.
    - If stable, traffic is increased to 25%, 50%, then 100%.

### 6.3 Infrastructure as Code (IaC)
The entire environment is provisioned using **Terraform**. This allows Gael Fischer (DevOps) to recreate the environment in a different Azure region if necessary for disaster recovery.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Requirement:** 80% code coverage on the Domain layer.
- **Focus:** Business logic, validation rules, and data mapping.
- **Execution:** Run on every Pull Request via GitHub Actions.

### 7.2 Integration Testing
- **Framework:** TestContainers for .NET.
- **Approach:** Spin up a temporary Azure SQL Docker container and a mock Partner API (using WireMock.Net).
- **Focus:** Database migrations, API endpoint connectivity, and the "Adapter" logic.
- **Execution:** Run nightly against the Dev environment.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Approach:** Automated browser tests simulating a user journey (e.g., "User logs in $\rightarrow$ Uploads file $\rightarrow$ Verifies scan status").
- **Focus:** Critical user paths and UI/UX stability.
- **Execution:** Run on the Staging environment prior to every Production release.

### 7.4 Penetration Testing
Since no specific compliance framework (like SOC2 or HIPAA) is required, the company mandates **Quarterly Penetration Testing**. This is handled by an external security firm that attempts to breach the API, bypass RBAC, or inject malicious files via the upload feature.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotation | High | High | Hire a specialized contractor to distribute knowledge and reduce "bus factor." | Felix Jensen |
| R-02 | Competitor is 2 months ahead | Medium | High | Assign a dedicated "Market Watch" owner to track competitor features and accelerate critical path. | Joelle Stein |
| R-03 | Partner API breaking changes | High | Medium | Implement the Hexagonal architecture to isolate changes to a single Adapter. | Gael Fischer |
| R-04 | Budget depletion (Bootstrapped) | Low | Medium | Maintain strict lean development; utilize Azure Free Tier/Reserved instances where possible. | Felix Jensen |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **High/Medium:** Closely monitored.
- **Low/Medium:** Accepted risk.

---

## 9. TIMELINE AND MILESTONES

The project follows an iterative approach, but is bound by three hard milestones.

### 9.1 Phase Breakdown

**Phase 1: Foundation (Oct 2023 - March 2025)**
- Core Domain development.
- Implementation of File Upload and Virus Scanning (Complete).
- Initial RBAC and Auth setup.
- **Milestone 1: Architecture Review Complete (Target: 2025-03-15)**
    - *Dependency:* All ports and adapters must be documented and signed off by Felix Jensen.

**Phase 2: Integration & Stability (March 2025 - May 2025)**
- Development of the Notification System (Critical Path).
- Finalizing the Customer-Facing API and Sandbox.
- Implementation of 2FA and Hardware Key support.
- **Milestone 2: Production Launch (Target: 2025-05-15)**
    - *Dependency:* Notification system must be 100% operational; Penetration test must be passed.

**Phase 3: Optimization & Expansion (May 2025 - July 2025)**
- User onboarding and training.
- Monitoring and tuning the "cost per transaction" metric.
- Scaling the API to handle 10k MAU.
- **Milestone 3: Internal Alpha Release (Target: 2025-07-15)**
    - *Note:* This "Alpha" refers to the v2.0 expansion features for wider internal use.

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment
**Date:** 2023-11-02  
**Attendees:** Felix, Gael, Joelle, Javier  
**Discussion:**
- Discussion on whether to use a Monolith or Microservices. Felix insisted on Hexagonal Architecture to prevent the "Big Ball of Mud" and to accommodate the partner API's volatility.
- Joelle raised concerns about the complexity of 2FA for non-technical users. Decision made to include a "Recovery Code" system.
- Javier noted that the legacy system is failing daily, increasing the urgency of the "Sync Status" API.

**Action Items:**
- [Gael] Set up the Azure SQL Hyperscale instance. (Due: 2023-11-10)
- [Felix] Draft the Port interfaces for the Partner API. (Due: 2023-11-12)

---

### Meeting 2: The "God Class" Crisis
**Date:** 2023-12-15  
**Attendees:** Felix, Gael, Javier  
**Discussion:**
- The team identified a 3,000-line class (`AuthAndLogManager.cs`) that handles authentication, logging, and email. This is causing massive merge conflicts and regression bugs.
- Decision: Implement a "Strangler Fig" pattern. We will not rewrite it all at once but will peel off the Email logic into a new `NotificationService` first.
- Javier reported that third-party API rate limits are blocking the current integration tests.

**Action Items:**
- [Javier] Request a rate-limit increase from the partner company. (Due: 2023-12-20)
- [Gael] Create a separate project for the `NotificationService` to begin the decoupling. (Due: 2023-12-22)

---

### Meeting 3: Launch Blocker Review
**Date:** 2024-01-20  
**Attendees:** Felix, Joelle, Gael, Javier  
**Discussion:**
- Review of the "Critical" priority list. The Notification System is still "Not Started," which is a major risk for the May launch.
- Joelle presented the designs for the Sandbox environment. The team agreed that a "Mock Mode" toggle in the API is the most efficient way to implement the sandbox.
- Discussion on the competitor's progress. The competitor has released a similar tool. Felix decided to assign Joelle as the "Market Watch" owner to identify any missing features in Ironclad.

**Action Items:**
- [Felix] Reallocate 50% of Javier's time from support to the Notification System development. (Due: 2024-01-25)
- [Joelle] Create a feature-gap analysis report against the competitor. (Due: 2024-02-01)

---

## 11. BUDGET BREAKDOWN

As an unfunded project, the "Budget" represents the internal cost of resources and the direct Azure spend.

| Category | Detail | Annual Est. Cost | Funding Source |
| :--- | :--- | :--- | :--- |
| **Personnel** | 15 FTEs (Distributed) | $2,100,000 | Existing Opex / Payroll |
| **Infrastructure** | Azure SQL, Functions, App Service | $144,000 | Departmental Cloud Budget |
| **Tools** | LaunchDarkly, SendGrid, Twilio | $22,000 | Engineering Tooling Budget |
| **Contingency** | Contractor for "Bus Factor" Risk | $85,000 | Emergency Reserve |
| **Total Estimated** | | **$2,351,000** | |

**Budgetary Note:** Since personnel costs are absorbed, the actual "out-of-pocket" cash expenditure for Ironclad is approximately $251,000 per year.

---

## 12. APPENDICES

### Appendix A: The "God Class" Refactoring Map
The current `AuthAndLogManager.cs` will be decomposed as follows:
1. **Authentication Logic** $\rightarrow$ `IdentityService.cs` (Domain Layer)
2. **Logging Logic** $\rightarrow$ `StructuredLoggingAdapter.cs` (Infrastructure Layer)
3. **Email Logic** $\rightarrow$ `EmailNotificationAdapter.cs` (Infrastructure Layer)
4. **Session Handling** $\rightarrow$ `SessionManager.cs` (Application Layer)

### Appendix B: Partner API Rate Limit Specifications
The current blocker is based on the following partner constraints:
- **Request Limit:** 100 requests per minute per API Key.
- **Daily Cap:** 50,000 requests.
- **Burst Limit:** 10 requests per second.
- **Current Ironclad Usage:** During full sync, the system attempts 1,200 requests per minute, resulting in `429 Too Many Requests` errors.
- **Solution:** Implementation of a `Polly` retry policy with jitter and a local queue to smooth out the request spikes.