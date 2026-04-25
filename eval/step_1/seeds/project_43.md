Due to the extreme length requirement of this document (6,000–8,000 words), the following is a comprehensive, professional Project Specification Document. To ensure the highest level of detail, this document is structured as a living technical manual for the development team at Crosswind Labs.

***

# PROJECT SPECIFICATION: FATHOM
**Version:** 1.0.4  
**Status:** Active / High Urgency  
**Last Updated:** October 24, 2024  
**Classification:** Confidential / Internal  
**Project Lead:** Zia Moreau (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Fathom" is a mission-critical IoT device network deployment designed specifically for the education sector. Developed by Crosswind Labs, Fathom serves as a regulatory compliance bridge, ensuring that educational institutions can monitor, report, and manage IoT hardware (sensors, access controllers, and environment monitors) in accordance with new, stringent legal mandates.

The project is characterized by a hard legal deadline. Failure to launch by the specified date (June 15, 2025) will result in severe regulatory penalties for the end-users and potential legal liability for Crosswind Labs. Given the "shoestring" budget of $150,000, the project operates under extreme fiscal scrutiny, requiring a lean development approach and a strict adherence to the "Critical" priority features.

### 1.2 Business Justification
The educational technology market is currently facing a shift toward mandatory real-time monitoring for safety and energy compliance. Institutions that fail to implement these IoT networks will lose federal funding and accreditation. Fathom provides an out-of-the-box solution that integrates disparate IoT hardware into a unified, compliant reporting system. 

The primary business driver is the "Compliance Gap." By providing a certified SOC 2 Type II compliant platform, Crosswind Labs allows schools to outsource the risk of data mismanagement and hardware failure to a managed service.

### 1.3 ROI Projection
While the initial budget is limited, the long-term Return on Investment (ROI) is projected based on a B2B SaaS subscription model.
*   **Direct Revenue:** Expected Annual Recurring Revenue (ARR) of $450,000 from the first 20 pilot districts.
*   **Cost Savings:** A projected 50% reduction in manual processing time for school administrators (who currently manually log sensor data), translating to an estimated saving of 1,200 man-hours per district per year.
*   **Market Positioning:** Establishing a first-mover advantage in the regulatory IoT space for education, creating a moat against larger competitors who cannot pivot as quickly to these specific legal requirements.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Fathom is built on a traditional three-tier architecture using a full Microsoft ecosystem to ensure stability, rapid deployment, and seamless integration.

*   **Presentation Layer:** ASP.NET Core Blazor WebAssembly (WASM) for the administrative dashboard, providing a responsive, single-page application (SPA) experience.
*   **Business Logic Layer:** C#/.NET 8 Web API hosted on Azure App Services and Azure Functions for asynchronous event-driven processing.
*   **Data Layer:** Azure SQL Database (PaaS) for relational data and Azure Blob Storage for raw telemetry logs.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ IoT Devices ]  --> [ MQTT Broker / Azure IoT Hub ] 
                               |
                               v
                    [ Azure Functions (Ingestion) ] 
                               |
                               v
                    [ Business Logic Layer ] <--> [ Azure SQL Database ]
                    (C# .NET 8 Web API / Core)      (Relational Schema)
                               |
                               v
                    [ Presentation Layer ] <--> [ Azure Active Directory ]
                    (Blazor WASM / Frontend)       (AuthN / AuthZ)
                               |
                               v
                    [ External Notification ] <--> [ Twilio / SendGrid ]
                    (Email, SMS, Push, In-App)
```

### 2.3 Data Flow and Logic
1.  **Ingestion:** IoT devices push telemetry data via MQTT to Azure IoT Hub.
2.  **Processing:** Azure Functions trigger upon message arrival, normalizing the data (addressing the current technical debt of inconsistent date formats) before persisting it to the SQL database.
3.  **Consumption:** The Blazor frontend queries the Web API, which implements business rules for regulatory compliance (e.g., triggering an alert if a temperature sensor exceeds a legal limit).
4.  **Output:** The Notification System (Critical Priority) monitors the data stream and pushes alerts to administrators via the multi-channel system.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: Critical | Status: In Progress)
**Description:** A robust, multi-channel alerting system designed to ensure that regulatory breaches are communicated to school administrators immediately.

**Functional Requirements:**
*   **Multi-Channel Delivery:** The system must support four distinct channels:
    *   *Email:* Triggered via SendGrid API for formal documentation.
    *   *SMS:* Triggered via Twilio for urgent, immediate attention.
    *   *In-App:* Real-time notifications via SignalR hubs within the Blazor dashboard.
    *   *Push:* Mobile push notifications via Azure Notification Hubs.
*   **Escalation Logic:** If an "Urgent" alert is not acknowledged within 15 minutes via in-app notification, the system must automatically escalate to SMS, then Email.
*   **User Preferences:** Users must be able to toggle specific channels for different alert severity levels (Low, Medium, High, Critical).
*   **Audit Trail:** Every notification must be logged in the `NotificationLogs` table with a timestamp of delivery and a timestamp of user acknowledgment.

**Technical Implementation:**
The system will utilize a "Notification Dispatcher" pattern. The Business Logic layer will publish a `NotificationRequested` event to an Azure Service Bus. A dedicated `NotificationWorker` (Azure Function) will subscribe to this bus and determine the correct provider to use based on the user's settings.

**Launch Blocker Status:** This feature is a launch blocker because regulatory compliance requires "verifiable notification" that a fault has occurred. Without this, the system cannot be legally certified.

### 3.2 Multi-Tenant Data Isolation (Priority: Low | Status: In Design)
**Description:** Implementation of a shared infrastructure model where multiple educational districts share a single database instance but cannot access each other's data.

**Functional Requirements:**
*   **Tenant Partitioning:** Every table in the database must contain a `TenantId` (GUID).
*   **Row-Level Security (RLS):** Implementation of Azure SQL Row-Level Security to ensure that a query executed by User A (Tenant 1) can never return data belonging to Tenant 2.
*   **Tenant Management:** An administrative interface for Zia Moreau’s team to provision new tenants and assign license limits.

**Technical Implementation:**
A "Shared Database, Separate Schema" approach is being evaluated, but for budget reasons, a "Shared Schema" approach using a Global Query Filter in Entity Framework Core is the preferred path. This ensures that every `SELECT` statement automatically appends `WHERE TenantId = @CurrentTenantId`.

### 3.3 Real-time Collaborative Editing (Priority: Low | Status: Not Started)
**Description:** A feature allowing multiple administrators to edit compliance reports or device configurations simultaneously without overwriting each other's changes.

**Functional Requirements:**
*   **Presence Indicators:** Users should see who else is currently viewing/editing a specific record.
*   **Conflict Resolution:** Implementation of "Last Write Wins" (LWW) or Operational Transformation (OT) to handle simultaneous edits.
*   **Locking Mechanism:** Ability to lock a specific field while a user is typing to prevent collisions.

**Technical Implementation:**
This will require the integration of SignalR for real-time state synchronization. Given the "Low" priority and the tight budget, this feature is currently deferred and will only be addressed if the "Critical" path finishes ahead of schedule.

### 3.4 A/B Testing Framework (Priority: Medium | Status: Blocked)
**Description:** A system integrated into the feature flag architecture to test different UI layouts or notification cadences against different user groups.

**Functional Requirements:**
*   **Bucket Assignment:** Users must be randomly assigned to Group A or Group B upon login.
*   **Metric Tracking:** The system must track "Time to Acknowledge Notification" for both groups to determine which layout is more effective.
*   **Dynamic Toggle:** The ability to shift 100% of users to the winning variant without a code redeploy.

**Technical Implementation:**
The framework will utilize `Microsoft.FeatureManagement`. However, this is currently **Blocked** because the third-party API rate limits are preventing the telemetry data required to measure the A/B test results from being ingested.

### 3.5 Localization and Internationalization (Priority: Critical | Status: Complete)
**Description:** Full support for 12 different languages to accommodate the distributed nature of the client base and the distributed team.

**Functional Requirements:**
*   **Language Support:** English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, Dutch, and Russian.
*   **Dynamic Switching:** Users can change their language preference in the user profile settings.
*   **Right-to-Left (RTL) Support:** The UI must support RTL layouts for Arabic.

**Technical Implementation:**
Implemented using `.resx` resource files in .NET and the `IStringLocalizer` interface. The Blazor frontend uses a custom `LocalizationService` that loads the appropriate JSON translation file based on the user's culture setting. This is the only critical feature currently marked as "Complete."

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are secured via OAuth2 / Azure AD. Base URL: `https://api.fathom-iot.crosswindlabs.io/v1/`

### 4.1 Get Device Status
*   **Endpoint:** `GET /devices/{deviceId}/status`
*   **Description:** Retrieves current telemetry and health status of a specific IoT device.
*   **Request Example:** `GET /devices/dev-9982/status`
*   **Response (200 OK):**
```json
{
  "deviceId": "dev-9982",
  "status": "Active",
  "lastHeartbeat": "2024-10-24T14:22:00Z",
  "telemetry": { "temp": 22.5, "humidity": 45 },
  "complianceStatus": "Compliant"
}
```

### 4.2 Trigger Notification
*   **Endpoint:** `POST /notifications/send`
*   **Description:** Manually trigger a multi-channel notification.
*   **Request Body:**
```json
{
  "userId": "user-123",
  "severity": "Critical",
  "message": "Device dev-9982 is offline!",
  "channels": ["SMS", "Push"]
}
```
*   **Response (202 Accepted):** `{"notificationId": "notif-554", "status": "Queued"}`

### 4.3 Update Tenant Config
*   **Endpoint:** `PATCH /tenants/{tenantId}/config`
*   **Description:** Update tenant-level settings (localization, limits).
*   **Request Body:** `{"language": "fr-FR", "maxDevices": 500}`
*   **Response (200 OK):** `{"status": "Updated", "updatedAt": "2024-10-24T15:00:00Z"}`

### 4.4 Get Compliance Report
*   **Endpoint:** `GET /reports/compliance/{tenantId}`
*   **Description:** Generates a PDF-ready JSON object of all compliance breaches.
*   **Response (200 OK):**
```json
{
  "tenantId": "tenant-abc",
  "period": "2024-Q3",
  "breaches": [
    {"deviceId": "dev-1", "issue": "Temp Exceeded", "timestamp": "2024-08-01T10:00:00Z"}
  ]
}
```

### 4.5 Device Onboarding
*   **Endpoint:** `POST /devices/onboard`
*   **Description:** Registers a new IoT device into the network.
*   **Request Body:** `{"macAddress": "00:1A:2B:3C:4D", "model": "Sensor-X1", "tenantId": "tenant-abc"}`
*   **Response (201 Created):** `{"deviceId": "dev-9983", "provisioningKey": "key-7788"}`

### 4.6 Acknowledge Alert
*   **Endpoint:** `POST /notifications/{notifId}/acknowledge`
*   **Description:** Marks a notification as read/handled.
*   **Response (200 OK):** `{"status": "Acknowledged", "timestamp": "2024-10-24T16:00:00Z"}`

### 4.7 Get User Profile
*   **Endpoint:** `GET /users/{userId}/profile`
*   **Description:** Retrieves user preferences and localization settings.
*   **Response (200 OK):** `{"userId": "user-123", "name": "Elara Oduya", "timezone": "UTC+1"}`

### 4.8 Heartbeat Ping
*   **Endpoint:** `POST /devices/{deviceId}/heartbeat`
*   **Description:** IoT device check-in to prevent "Device Offline" alerts.
*   **Response (204 No Content)**

---

## 5. DATABASE SCHEMA

The system utilizes Azure SQL. All tables use `datetimeoffset` to mitigate the "Technical Debt" of mixed date formats.

### 5.1 Table Definitions

1.  **Tenants**
    *   `TenantId` (PK, GUID)
    *   `TenantName` (nvarchar(200))
    *   `CreatedAt` (datetimeoffset)
    *   `SubscriptionTier` (int)
2.  **Users**
    *   `UserId` (PK, GUID)
    *   `TenantId` (FK)
    *   `Email` (nvarchar(255))
    *   `PasswordHash` (varbinary(max))
    *   `PreferredLanguage` (nvarchar(10))
3.  **Devices**
    *   `DeviceId` (PK, GUID)
    *   `TenantId` (FK)
    *   `MacAddress` (nvarchar(17))
    *   `ModelNumber` (nvarchar(50))
    *   `LastHeartbeat` (datetimeoffset)
4.  **Telemetry**
    *   `TelemetryId` (PK, bigint)
    *   `DeviceId` (FK)
    *   `Value` (float)
    *   `MetricType` (nvarchar(50)) — e.g., "Temperature"
    *   `Timestamp` (datetimeoffset)
5.  **Notifications**
    *   `NotificationId` (PK, GUID)
    *   `UserId` (FK)
    *   `Message` (nvarchar(max))
    *   `Severity` (int)
    *   `ChannelUsed` (nvarchar(20))
6.  **NotificationLogs**
    *   `LogId` (PK, bigint)
    *   `NotificationId` (FK)
    *   `SentAt` (datetimeoffset)
    *   `AcknowledgedAt` (datetimeoffset, nullable)
7.  **ComplianceRules**
    *   `RuleId` (PK, int)
    *   `TenantId` (FK)
    *   `MetricType` (nvarchar(50))
    *   `ThresholdValue` (float)
    *   `IsCritical` (bit)
8.  **ComplianceBreaches**
    *   `BreachId` (PK, bigint)
    *   `DeviceId` (FK)
    *   `RuleId` (FK)
    *   `Timestamp` (datetimeoffset)
9.  **FeatureFlags**
    *   `FeatureKey` (PK, nvarchar(100))
    *   `IsEnabled` (bit)
    *   `RolloutPercentage` (int)
10. **AuditLogs**
    *   `AuditId` (PK, bigint)
    *   `UserId` (FK)
    *   `Action` (nvarchar(500))
    *   `Timestamp` (datetimeoffset)

### 5.2 Relationships
*   `Tenants` $\rightarrow$ `Users` (1:N)
*   `Tenants` $\rightarrow$ `Devices` (1:N)
*   `Devices` $\rightarrow$ `Telemetry` (1:N)
*   `Devices` $\rightarrow$ `ComplianceBreaches` (1:N)
*   `Users` $\rightarrow$ `Notifications` (1:N)
*   `Notifications` $\rightarrow$ `NotificationLogs` (1:1)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Fathom utilizes three distinct environments to ensure stability before the legal deadline.

**1. Development (Dev):**
*   **Purpose:** Feature development and unit testing.
*   **Deployment:** Automatic CI/CD via GitHub Actions on push to `develop` branch.
*   **Database:** Shared Dev SQL instance.

**2. Staging (QA):**
*   **Purpose:** Integration testing and User Acceptance Testing (UAT).
*   **Deployment:** Manual trigger. This is the "Manual QA Gate."
*   **Constraint:** All deployments to Staging require a 2-day turnaround for full regression testing by Paz Kim and Zia Moreau.
*   **Database:** Mirror of Production (sanitized data).

**3. Production (Prod):**
*   **Purpose:** Live end-user access.
*   **Deployment:** High-ceremony deployment. Requires sign-off from the Project Lead and a successful SOC 2 audit check.
*   **Infrastructure:** Azure Region: East US 2 (for latency optimization).

### 6.2 SOC 2 Type II Compliance
Before the June 15th launch, the infrastructure must pass a SOC 2 Type II audit. This involves:
*   **Encryption:** All data encrypted at rest (Azure Disk Encryption) and in transit (TLS 1.3).
*   **Access Control:** Just-In-Time (JIT) access for engineers; no permanent admin access to Production.
*   **Monitoring:** Azure Monitor and Log Analytics enabled for all resource groups.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** xUnit.
*   **Target:** 80% code coverage for the Business Logic Layer.
*   **Focus:** Validation logic for compliance rules and date normalization helpers.

### 7.2 Integration Testing
*   **Approach:** Automated tests utilizing `WebApplicationFactory` to simulate API calls.
*   **Focus:** Testing the flow from `Telemetry Ingestion` $\rightarrow$ `Compliance Check` $\rightarrow$ `Notification Dispatch`.
*   **External Mocks:** Use of WireMock to simulate the third-party API to bypass current rate-limiting blockers.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Scenario:** "A sensor exceeds temperature limit $\rightarrow$ Admin receives SMS $\rightarrow$ Admin acknowledges in Blazor Dashboard."
*   **Frequency:** Performed weekly on the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Integration partner's API is undocumented/buggy | High | High | Escalate to steering committee for additional funding to hire a specialist integrator. |
| R-02 | Project sponsor rotation (Leaving role) | Medium | High | Engage external consultant for an independent assessment to maintain continuity and authority. |
| R-03 | Third-party API rate limits (Current Blocker) | High | Medium | Implement a local caching layer and request queuing system to reduce API hits. |
| R-04 | Technical debt (Date formats) | High | Low | Implement a `DateNormalizationService` in the Business Logic layer to standardize all inputs to UTC. |
| R-05 | Budget overruns | Medium | High | Strict "Feature Freeze" on any "Low" priority items if "Critical" items slip by more than 10%. |

**Impact Matrix:**
*   **High:** Blocks launch or causes legal non-compliance.
*   **Medium:** Degrades performance or slows development.
*   **Low:** Cosmetic or minor operational inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown

**Phase 1: Foundations (Oct 2024 - Dec 2024)**
*   Core DB Schema implementation.
*   Localization (Complete).
*   Initial Azure Infrastructure setup.
*   *Dependency:* SOC 2 Gap Analysis.

**Phase 2: Critical Path (Jan 2025 - March 2025)**
*   Notification System development (In Progress).
*   IoT Hub integration.
*   Compliance rule engine.
*   *Dependency:* Third-party API rate limit resolution.

**Phase 3: Validation & Onboarding (April 2025 - May 2025)**
*   Internal Alpha tests.
*   First paying customer onboarding.
*   UAT on Staging.

**Phase 4: Compliance & Launch (June 2025)**
*   Final SOC 2 Certification.
*   Production cut-over.

### 9.2 Key Milestone Dates
*   **Milestone 1: First paying customer onboarded** $\rightarrow$ **2025-04-15**
*   **Milestone 2: Production launch** $\rightarrow$ **2025-06-15**
*   **Milestone 3: Internal alpha release** $\rightarrow$ **2025-08-15** (Note: This is a post-launch stability release for extended feature sets).

---

## 10. MEETING NOTES

### Meeting 1: Sprint Alignment & Blocker Review
**Date:** 2024-11-02  
**Attendees:** Zia Moreau, Elara Oduya, Chandra Fischer, Paz Kim  
**Discussion:**
*   Elara reported that the third-party API is returning 429 (Too Many Requests) errors during load testing of the notification system.
*   Chandra noted that the current UI for the 12 languages is clunky, specifically the Arabic RTL layout.
*   Zia emphasized the $150k budget; no one is to procure new tools without written approval.
**Action Items:**
*   **Elara:** Research caching strategies for the API. (Owner: Elara)
*   **Chandra:** Refine CSS for RTL support. (Owner: Chandra)
*   **Zia:** Reach out to the steering committee regarding API funding. (Owner: Zia)

### Meeting 2: SOC 2 Compliance Strategy
**Date:** 2024-11-15  
**Attendees:** Zia Moreau, Elara Oduya, External Consultant  
**Discussion:**
*   The external consultant warned that the "manual QA gate" is a strength for SOC 2, but the "three different date formats" in the code are a risk for data integrity audits.
*   Decision made to implement a global `IDateTimeProvider` to normalize all timestamps.
*   Paz Kim raised concerns about the "Shared Infrastructure" model for multi-tenancy; the consultant agreed that RLS is mandatory.
**Action Items:**
*   **Elara:** Implement `IDateTimeProvider` across all services. (Owner: Elara)
*   **Paz:** Map out the RLS security predicates for Azure SQL. (Owner: Paz)

### Meeting 3: Budgetary Review & Priority Pivot
**Date:** 2024-12-01  
**Attendees:** Zia Moreau, Project Sponsor  
**Discussion:**
*   Sponsor revealed they will be rotating out of their role in February.
*   Zia requested a "contingency buffer" from the remaining budget to ensure the transition doesn't stall the project.
*   Agreement reached to move "Collaborative Editing" to the bottom of the backlog.
**Action Items:**
*   **Zia:** Draft the transition document for the incoming sponsor. (Owner: Zia)
*   **Zia:** Allocate $5,000 from the contingency fund for the independent assessment. (Owner: Zia)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000.00 USD

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $97,500 | Distributed team (15 members) including contractors like Paz Kim. |
| **Infrastructure** | 15% | $22,500 | Azure SQL, Functions, IoT Hub, App Services. |
| **Tools & Licensing** | 10% | $15,000 | SendGrid, Twilio, SOC 2 Audit fees. |
| **Contingency** | 10% | $15,000 | Reserved for API issues and Sponsor transition assessment. |

**Fiscal Constraint:** Every dollar spent must be mapped to a "Critical" or "Medium" priority feature. Any spending on "Low" priority features is prohibited until the Production Launch (June 15, 2025) is successful.

---

## 12. APPENDICES

### Appendix A: Date Normalization Specification
To resolve the technical debt of three different date formats, all developers must adhere to the following:
*   **Storage:** All dates in Azure SQL must be `datetimeoffset`.
*   **API Layer:** All JSON responses must use ISO 8601 format (`YYYY-MM-DDThh:mm:ssZ`).
*   **Frontend:** The `FathomDateHelper` class in Blazor will handle conversion to the user's local timezone based on their profile settings.

### Appendix B: Third-Party API Mapping
Since the integration partner's API is undocumented, the team has reverse-engineered the following common mappings:
*   `GET /v1/device_sync` $\rightarrow$ Corresponds to `DeviceId` and `MacAddress`.
*   `POST /v1/alert_trigger` $\rightarrow$ Requires a `Bearer` token and a JSON body containing `alert_id` and `timestamp`.
*   **Known Bug:** The API occasionally returns a 200 OK with an empty body instead of a 404 when a device is not found. The backend must check for `null` responses.