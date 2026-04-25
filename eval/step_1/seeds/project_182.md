# PROJECT SPECIFICATION DOCUMENT: SENTINEL
**Version:** 1.2.0  
**Date:** October 24, 2024  
**Project Code:** ST-SENT-2024  
**Status:** Active / Development Phase  
**Classification:** Internal / Confidential

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Sentinel" is a specialized healthcare records platform developed by Silverthread AI. While Silverthread AI primarily operates within the media and entertainment industry, the organization has recognized a critical need for internal health-tracking, wellness record management, and productivity-linked healthcare data for its workforce and contractors. What began as a high-energy hackathon project has rapidly evolved into a mission-critical internal tool, currently supporting 500 daily active users (DAU).

The transition from a prototype to a formal enterprise platform is driven by the need to standardize health data access for the company’s growing global footprint. By moving away from fragmented spreadsheets and legacy third-party trackers, Sentinel centralizes records, allowing for better workforce wellness analytics and streamlined internal health administration. Given the scale of Silverthread AI’s operations, the ability to track health-related productivity correlations (e.g., burnout markers vs. output) provides a competitive edge in talent retention.

### 1.2 ROI Projection
With a budget exceeding $5M, Sentinel is a flagship initiative reporting directly to the Board of Directors. The Return on Investment (ROI) is calculated based on three primary pillars:
1.  **Administrative Efficiency:** Reduction of manual health record processing time by an estimated 40%, saving approximately $1.2M annually in administrative overhead.
2.  **Employee Wellness/Retention:** By providing a seamless health record experience, Silverthread AI projects a 5% decrease in attrition rates among high-value engineering talent, representing a cost avoidance of $2.1M in recruiting and onboarding costs.
3.  **Data-Driven Productivity:** The integration of health records with productivity metrics is projected to increase overall operational efficiency by 3%, which, across a workforce of thousands, translates to an estimated $1.8M in reclaimed productivity.

The total projected ROI over the first 24 months post-launch is estimated at $5.1M, effectively recouping the initial capital expenditure.

### 1.3 Strategic Alignment
Sentinel aligns with the Silverthread AI "People First" initiative. By leveraging a full Microsoft stack, the project ensures seamless integration with existing corporate Active Directory and Azure ecosystems, minimizing friction for the 20+ person cross-departmental team managing the rollout.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Sentinel utilizes a **Clean Monolith** architecture. Unlike a distributed microservices approach—which would introduce unnecessary latency and operational complexity for the current team size—the clean monolith ensures a single deployment unit with strictly enforced module boundaries. This allows the team to maintain high velocity while providing a clear path toward microservices should the user base scale beyond 10,000 MAU.

### 2.2 Technology Stack
- **Language/Framework:** C# / .NET 8 (Long Term Support)
- **Database:** Azure SQL Database (Business Critical Tier)
- **Serverless Logic:** Azure Functions (for asynchronous processing and notifications)
- **Infrastructure:** Azure App Service, Azure Key Vault, Azure Blob Storage
- **Deployment/Flags:** LaunchDarkly (Feature Flagging)
- **Identity:** SAML 2.0, OIDC, Azure AD

### 2.3 System Diagram (ASCII Representation)
```text
[ Client Layer ] 
      | (HTTPS / JSON)
      v
[ Azure App Service / .NET 8 Web API ]
      |
      +--> [ Module: Identity & Access ] <--> [ Azure AD / SAML / OIDC ]
      |
      +--> [ Module: Dashboard Engine ] <--> [ Azure Cache for Redis ]
      |
      +--> [ Module: Records Management ] <--> [ Azure SQL Database ]
      |
      +--> [ Module: Notification Engine ] 
                |
                v
        [ Azure Functions ] --> [ SendGrid (Email) ]
                          --> [ Twilio (SMS) ]
                          --> [ Firebase (Push) ]
```

### 2.4 Data Flow
1.  **Request:** User requests a health record view via the React-based frontend.
2.  **Auth:** The API validates the JWT token against the Identity module.
3.  **Business Logic:** The Records Management module queries the Azure SQL DB.
4.  **Cache:** Frequent dashboard widget data is cached in Redis to meet the p95 < 200ms requirement.
5.  **Persistence:** All writes are committed to Azure SQL with a full audit trail logged in a separate telemetry table.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Blocked
*   **Description:** The central hub of Sentinel. Users must be able to personalize their home screen by adding, removing, and rearranging widgets that display health metrics, upcoming appointments, and wellness alerts.
*   **Detailed Requirements:**
    - **Widget Library:** The system shall provide a library of at least 12 pre-defined widgets (e.g., "Heart Rate Trend," "Sleep Analysis," "Vaccination Status").
    - **Drag-and-Drop Interface:** Implementation of a grid-based layout (e.g., React Grid Layout) allowing users to resize and move widgets.
    - **State Persistence:** Widget configurations (position, size, visibility) must be saved to the `UserDashboardConfig` table in Azure SQL.
    - **Data Refresh:** Each widget must support a configurable refresh interval (1 min, 5 mins, 1 hour).
    - **Custom Queries:** Power users should be able to define a "Custom Metric" widget via a simplified query builder.
*   **Blocking Issue:** Current UI framework conflict between the drag-and-drop library and the corporate CSS standard; requires a custom wrapper to prevent style bleeding.

### 3.2 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** Medium
*   **Status:** Complete
*   **Description:** A robust security layer ensuring that users only see data they are authorized to view.
*   **Detailed Requirements:**
    - **Role Hierarchy:** Implementation of four primary roles: `SystemAdmin`, `MedicalOfficer`, `StandardUser`, and `ReadOnlyGuest`.
    - **Permission Mapping:** Each API endpoint is mapped to a specific permission claim. For example, `DELETE /records/{id}` requires the `MedicalOfficer` or `SystemAdmin` claim.
    - **Session Management:** JWT-based authentication with a 15-minute sliding expiration.
    - **Account Lockout:** Automatic lockout after 5 failed login attempts to prevent brute-force attacks.
    - **Audit Logging:** Every authentication event (Login, Logout, Failed Attempt) must be logged with timestamp and IP address.

### 3.3 Notification System
*   **Priority:** Low (Nice to Have)
*   **Status:** In Review
*   **Description:** A multi-channel alerting system to notify users of health updates, appointment reminders, or system alerts.
*   **Detailed Requirements:**
    - **Email Integration:** Integration with SendGrid for transactional emails (HTML templates).
    - **SMS Integration:** Integration with Twilio for critical alerts.
    - **In-App Notifications:** A real-time notification bell using SignalR for instant updates without page refreshes.
    - **Push Notifications:** Implementation of Firebase Cloud Messaging (FCM) for mobile browser alerts.
    - **User Preferences:** A "Notification Settings" page where users can toggle each channel on/off per notification type.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
*   **Priority:** Low (Nice to Have)
*   **Status:** Blocked
*   **Description:** Enhanced security for high-privileged accounts using physical security keys.
*   **Detailed Requirements:**
    - **FIDO2/WebAuthn:** Support for YubiKey and Google Titan security keys.
    - **Fallback Method:** TOTP (Time-based One-Time Password) via apps like Microsoft Authenticator.
    - **Enrollment Workflow:** A guided onboarding process for users to register their primary and backup hardware keys.
    - **Recovery Codes:** Generation of 10 one-time use recovery codes upon 2FA activation.
*   **Blocking Issue:** Current internal security proxy interferes with WebAuthn USB handshakes; Gael Kim is investigating a proxy bypass.

### 3.5 SSO Integration with SAML and OIDC Providers
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Blocked
*   **Description:** Seamless integration with corporate identity providers to eliminate separate passwords for Sentinel.
*   **Detailed Requirements:**
    - **SAML 2.0:** Support for legacy corporate providers used by Silverthread AI's entertainment partners.
    - **OIDC (OpenID Connect):** Implementation of the Authorization Code Flow with PKCE for the modern frontend.
    - **Just-In-Time (JIT) Provisioning:** Automatically create a `User` record in the local database upon first successful SSO login.
    - **Attribute Mapping:** Map SAML attributes (e.g., `department`, `employeeId`) to internal Sentinel profile fields.
*   **Blocking Issue:** Delay in receiving the metadata XML files from the corporate identity team.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and return JSON. Base URL: `https://api.sentinel.silverthread.ai/v1/`

### 4.1 Get User Dashboard Configuration
- **Path:** `GET /user/dashboard/config`
- **Auth:** Required (JWT)
- **Request:** None
- **Response:**
  ```json
  {
    "userId": "USR-9921",
    "layout": [
      {"id": "widget_1", "x": 0, "y": 0, "w": 4, "h": 2, "type": "HeartRate"},
      {"id": "widget_2", "x": 4, "y": 0, "w": 4, "h": 2, "type": "SleepMetric"}
    ]
  }
  ```

### 4.2 Update Dashboard Layout
- **Path:** `POST /user/dashboard/config`
- **Auth:** Required (JWT)
- **Request:**
  ```json
  {
    "layout": [{"id": "widget_1", "x": 2, "y": 0, "w": 4, "h": 2, "type": "HeartRate"}]
  }
  ```
- **Response:** `200 OK`

### 4.3 Get Health Record
- **Path:** `GET /records/{recordId}`
- **Auth:** Required (Role: StandardUser, MedicalOfficer)
- **Response:**
  ```json
  {
    "recordId": "REC-550",
    "patientId": "USR-9921",
    "timestamp": "2024-10-20T10:00:00Z",
    "data": { "systolic": 120, "diastolic": 80 },
    "notes": "Normal reading"
  }
  ```

### 4.4 Create Health Record
- **Path:** `POST /records`
- **Auth:** Required (Role: MedicalOfficer)
- **Request:**
  ```json
  {
    "patientId": "USR-9921",
    "data": { "systolic": 130, "diastolic": 85 },
    "notes": "Slightly elevated"
  }
  ```
- **Response:** `201 Created`

### 4.5 Trigger Notification
- **Path:** `POST /notifications/send`
- **Auth:** Required (Role: SystemAdmin)
- **Request:**
  ```json
  {
    "userId": "USR-9921",
    "channel": "SMS",
    "message": "Your health check is tomorrow at 9 AM."
  }
  ```
- **Response:** `202 Accepted`

### 4.6 Get User Profile
- **Path:** `GET /user/profile`
- **Auth:** Required (JWT)
- **Response:**
  ```json
  {
    "username": "bram_fischer",
    "email": "b.fischer@silverthread.ai",
    "role": "FrontendLead"
  }
  ```

### 4.7 Initiate SSO Login
- **Path:** `GET /auth/sso/initiate`
- **Auth:** None
- **Response:** `302 Redirect to Provider`

### 4.8 Get System Health Status
- **Path:** `GET /system/health`
- **Auth:** None (Public)
- **Response:**
  ```json
  {
    "status": "Healthy",
    "uptime": "45 days",
    "version": "1.2.0"
  }
  ```

---

## 5. DATABASE SCHEMA

The database is hosted on Azure SQL. All tables use `bigint` for primary keys and `datetime2` for timestamps.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `UserId` | `Username`, `Email`, `PasswordHash`, `RoleID` | `RoleID` $\to$ `Roles` | Core user identity data. |
| `Roles` | `RoleID` | `RoleName`, `PermissionsBitmask` | - | Defines RBAC roles. |
| `HealthRecords` | `RecordId` | `UserId`, `Timestamp`, `RecordType` | `UserId` $\to$ `Users` | The actual medical data. |
| `RecordData` | `DataId` | `RecordId`, `MetricKey`, `MetricValue` | `RecordId` $\to$ `HealthRecords` | EAV model for flexible metrics. |
| `UserDashboardConfig`| `ConfigId` | `UserId`, `WidgetJson`, `LastUpdated` | `UserId` $\to$ `Users` | Stores drag-and-drop layout. |
| `Notifications` | `NotifId` | `UserId`, `Channel`, `Message`, `SentAt` | `UserId` $\to$ `Users` | Audit trail of sent alerts. |
| `AuditLogs` | `LogId` | `UserId`, `Action`, `IpAddress`, `Timestamp`| `UserId` $\to$ `Users` | Security and access logs. |
| `SSOProviders` | `ProviderId` | `ProviderName`, `MetadataUrl`, `ClientId` | - | Configuration for SAML/OIDC. |
| `BillingLogs` | `BillId` | `UserId`, `Amount`, `TransactionDate` | `UserId` $\to$ `Users` | Core billing module logs. |
| `HardwareKeys` | `KeyId` | `UserId`, `PublicKey`, `DeviceName` | `UserId` $\to$ `Users` | Registered 2FA keys. |

### 5.2 Schema Logic
The `HealthRecords` and `RecordData` tables utilize an Entity-Attribute-Value (EAV) pattern. This allows the platform to add new health metrics (e.g., adding "Blood Oxygen" to "Heart Rate") without requiring a schema migration for every new medical device integrated.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes three distinct environments to ensure stability.

**1. Development (Dev)**
- **Purpose:** Rapid iteration and feature experimentation.
- **Deployment:** Automatic deploy on merge to `develop` branch.
- **Database:** Shared Dev SQL Instance with mocked data.
- **Access:** Full team.

**2. Staging (Stage)**
- **Purpose:** Pre-production validation, UAT, and security audits.
- **Deployment:** Manual trigger from `release` branch.
- **Database:** Restored backup of Production (anonymized).
- **Access:** Jasper Kim, Bram Fischer, Gael Kim, and QA testers.

**3. Production (Prod)**
- **Purpose:** End-user live environment.
- **Deployment:** Canary releases via Azure App Service slots.
- **Database:** Azure SQL Business Critical with Geo-Replication.
- **Access:** Restricted to Jasper Kim and Gael Kim.

### 6.2 Deployment Pipeline
We utilize GitHub Actions for CI/CD. The pipeline includes:
1.  **Build:** .NET 8 build and NuGet restore.
2.  **Test:** Execution of unit tests (excluding billing module).
3.  **Package:** Docker image creation pushed to Azure Container Registry.
4.  **Deploy:** Deployment to the "Staging" slot.
5.  **Canary:** 10% of traffic is routed to the new version; if p95 response times stay under 200ms, the remaining 90% is shifted.

### 6.3 Feature Flagging
LaunchDarkly is integrated into the C# codebase. This allows the team to merge code for the "Notification System" (currently In Review) into production while keeping it disabled for users until the final sign-off.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Coverage Goal:** 80% overall.
- **Approach:** Testing of individual business logic classes (e.g., `RolePermissionEvaluator`).
- **Known Gap:** The **Core Billing Module** currently has 0% test coverage due to being deployed under extreme deadline pressure. This is flagged as critical technical debt.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the .NET API and Azure SQL.
- **Tooling:** Postman collections run via Newman in the CI pipeline.
- **Key Scenarios:**
    - Validating that a user with `ReadOnlyGuest` cannot call the `POST /records` endpoint.
    - Verifying that SSO token exchange correctly maps roles in the `Users` table.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scenarios:**
    - **Happy Path:** User logs in via SSO $\to$ Drags a widget on the dashboard $\to$ Views a health record.
    - **Error Path:** User attempts to access a record without permission $\to$ System displays 403 Forbidden $\to$ Log is created in `AuditLogs`.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor dependency announced EOL for their product. | High | High | **Parallel-Path:** Prototyping an alternative open-source approach simultaneously to ensure a seamless cut-over. |
| **R-02** | Team has no prior experience with .NET/Azure stack. | Medium | Medium | **Knowledge Sharing:** Documenting all "gotchas" and workarounds in the internal Wiki; weekly peer-review sessions. |
| **R-03** | Billing module failure due to lack of tests. | Medium | Critical | **Sprint Debt:** Allocating 20% of every single sprint to retroactively write tests for the billing module. |
| **R-04** | SSO Metadata delays blocking launch. | High | Medium | **Stubbing:** Using a mock OIDC provider in Staging to continue frontend development. |

### 8.1 Probability/Impact Matrix
- **High/High:** Immediate Board-level visibility (R-01).
- **Medium/Critical:** High technical risk (R-03).
- **High/Medium:** Project timeline risk (R-04).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phased Roadmap

**Phase 1: Foundation (Current - March 2025)**
- Focus on stabilizing the monolith and resolving the SSO/Dashboard blockers.
- **Milestone 1:** Performance benchmarks met (p95 < 200ms).
- **Target Date:** 2025-03-15.
- **Dependency:** Completion of Azure SQL indexing optimization.

**Phase 2: Hardening (March 2025 - May 2025)**
- Focus on security audits and 2FA integration.
- **Milestone 2:** Architecture review complete.
- **Target Date:** 2025-05-15.
- **Dependency:** Resolution of the WebAuthn proxy issue.

**Phase 3: Validation (May 2025 - July 2025)**
- Beta testing with a select group of 1,000 employees.
- **Milestone 3:** Internal alpha release.
- **Target Date:** 2025-07-15.
- **Dependency:** Successful transition from Dev to Staging environment.

### 9.2 Gantt Description
- **Month 1-3:** (Engineering) SSO Logic $\to$ Dashboard UI $\to$ Perf Tuning.
- **Month 4-5:** (Security) Hardware Key Support $\to$ Final Architecture Review.
- **Month 6-7:** (QA) E2E Testing $\to$ Alpha User Onboarding $\to$ Launch.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync
**Date:** 2024-09-12  
**Attendees:** Jasper Kim, Bram Fischer, Gael Kim  
**Discussion:**
- Jasper proposed a microservices approach, but the team disagreed, citing the small team size.
- Bram expressed concerns about the CSS framework for the drag-and-drop dashboard.
- Decision: Move forward with a "Clean Monolith" to reduce deployment overhead.
- **Action Items:**
    - Bram to research React Grid Layout wrappers. (Owner: Bram)
    - Gael to set up the Azure Key Vault for secret management. (Owner: Gael)

### Meeting 2: Security Audit & 2FA Review
**Date:** 2024-10-05  
**Attendees:** Jasper Kim, Gael Kim, Yves Fischer  
- **Discussion:**
    - Gael identified that the corporate proxy is stripping the WebAuthn headers, blocking 2FA hardware key support.
    - Yves asked if the internal audit is sufficient, or if HIPAA compliance is needed.
    - Jasper clarified: This is an internal productivity tool for Silverthread AI; only an internal security audit is required.
- **Action Items:**
    - Gael to contact the Network Team for a proxy bypass. (Owner: Gael)
    - Yves to document the current RBAC mapping. (Owner: Yves)

### Meeting 3: Budget & Board Reporting
**Date:** 2024-10-18  
**Attendees:** Jasper Kim, Silverthread AI Board Rep  
- **Discussion:**
    - Review of the $5M budget allocation.
    - The Board is concerned about the "Blocked" status of the SSO integration.
    - Jasper explained that the delay is with the corporate identity team, not the engineering team.
    - Agreed that the p95 response time is the primary KPI for the March milestone.
- **Action Items:**
    - Jasper to send a formal request for metadata to the Identity Team. (Owner: Jasper)
    - Update the Risk Register to include the vendor EOL risk. (Owner: Jasper)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,500,000

### 11.1 Personnel ($3,200,000)
- **Engineering Salaries:** $2,400,000 (20+ people across 3 departments, including Lead, Frontend, Security, and Interns).
- **Project Management:** $500,000.
- **External Consultants (Azure Experts):** $300,000.

### 11.2 Infrastructure ($1,200,000)
- **Azure Consumption:** $800,000 (SQL Business Critical, App Service, Functions).
- **SaaS Licenses:** $200,000 (LaunchDarkly, SendGrid, Twilio, Firebase).
- **Hardware:** $200,000 (YubiKeys for executive/admin accounts).

### 11.3 Tools & Software ($400,000)
- **IDE & Dev Tools:** $100,000.
- **Security Scanning Software:** $200,000.
- **Monitoring/Observability (Azure Monitor/Application Insights):** $100,000.

### 11.4 Contingency ($700,000)
- **Risk Mitigation Fund:** Reserved for the parallel-path development required by the vendor EOL risk (R-01).

---

## 12. APPENDICES

### Appendix A: Performance Tuning Specifications
To achieve the **p95 < 200ms** response time, the following technical constraints are applied:
1.  **Index Strategy:** Every query on `HealthRecords` must use a covered index on `UserId` and `Timestamp`.
2.  **Query Optimization:** No `SELECT *` queries are permitted. All API responses must use explicit DTOs (Data Transfer Objects).
3.  **Caching:** The Dashboard Engine shall implement a "Cache-Aside" pattern. If the data exists in Azure Cache for Redis, the DB is not queried. Cache TTL is set to 300 seconds.
4.  **Async Offloading:** All notification-related logic is moved to Azure Functions via a Service Bus queue to prevent blocking the main API thread.

### Appendix B: Vendor EOL Transition Plan
Regarding Risk R-01, the team is implementing the following transition strategy:
1.  **Current State:** Using "Vendor X" for healthcare data ingestion.
2.  **Prototype State:** Yves Fischer is currently developing a prototype using an open-source FHIR (Fast Healthcare Interoperability Resources) server.
3.  **Comparison Phase:** In January 2025, the team will run both the Vendor X and the FHIR prototype in parallel for 10% of users.
4.  **Cut-over:** Once the FHIR prototype meets 99.9% reliability, all traffic will be migrated, and the Vendor X subscription will be terminated.