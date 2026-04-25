Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. It is structured to be the "Single Source of Truth" (SSOT) for the Quorum development team.

***

# PROJECT SPECIFICATION: QUORUM (v1.0.4)
**Company:** Stratos Systems  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Document Owner:** Omar Liu (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Quorum began as a high-energy hackathon project designed to solve a specific pain point within the agriculture technology sector: the fragmentation of field data and administrative productivity. In its current state, Quorum has organically grown to 500 daily active users (DAU) within Stratos Systems. This internal adoption proves a critical market fit; users are gravitating toward the tool because it bridges the gap between complex agricultural telemetry and day-to-day project management.

The transition from a "hackathon prototype" to a formal SaaS platform is necessitated by the demand for stability, scalability, and monetization. The agriculture industry is currently undergoing a digital transformation, with a CAGR of approximately 12% in AgTech software. By formalizing Quorum, Stratos Systems is not merely building a tool but creating a proprietary asset that increases the operational efficiency of field agents and corporate managers.

### 1.2 Project Objectives
The primary objective is to evolve Quorum from a fragile internal tool into a robust, multi-tenant SaaS platform capable of supporting 10,000 monthly active users (MAU) by early 2026. This requires the implementation of enterprise-grade authentication, a sustainable billing engine, and a transition from a monolithic structure to a modular architecture that allows for independent scaling of high-load services.

### 1.3 ROI Projection
The projected budget for Quorum is $400,000. The Return on Investment (ROI) is calculated based on three primary streams:
1. **Direct Revenue:** Target onboarding of the first paying customer by December 15, 2025, with a projected Annual Recurring Revenue (ARR) of $45,000 for the initial pilot customer.
2. **Operational Efficiency:** An estimated 15% reduction in administrative overhead for field operations, valued at approximately $120,000/year in saved man-hours.
3. **Market Positioning:** establishing Stratos Systems as a leader in AgTech productivity, enabling the company to upsell other telemetry services.

The break-even point is projected for Q3 2026, assuming a growth rate of 1,500 new users per month following the production launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
Quorum is built on the full Microsoft ecosystem to ensure maximum integration and support.
- **Backend:** C# / .NET 8 (Latest LTS)
- **Database:** Azure SQL Database (Hyperscale tier for scalability)
- **Compute:** Azure Functions (Serverless for event-driven tasks) and Azure App Service (for the core API)
- **Frontend:** Blazor WebAssembly (WASM) for a rich, C#-driven client experience.
- **Caching:** Azure Cache for Redis.

### 2.2 Architecture Pattern: Modular Monolith to Microservices
To avoid the "distributed monolith" trap, Quorum utilizes a **Modular Monolith** approach. The codebase is organized into distinct bounded contexts (Billing, Auth, FileManagement, UserManagement). 

**The Transition Path:**
- **Phase 1:** All modules reside in one deployable unit but maintain strict boundary separation via internal interfaces.
- **Phase 2:** High-load modules (e.g., File Distribution) will be extracted into independent Azure Functions or Microservices.

### 2.3 System Architecture Diagram (ASCII)
```text
[ Client Layer ] <------> [ Azure Front Door / CDN ]
       |                               |
       v                               v
[ Blazor WASM UI ] <---> [ Azure App Service (API Gateway) ]
                                      |
         _____________________________|_____________________________
        |                             |                             |
 [ Auth Module ]             [ Billing Module ]            [ File Module ]
        |                             |                             |
        v                             v                             v
 [ Azure AD / SAML ]         [ Stripe / Azure SQL ]         [ Azure Blob Storage ]
        |                             |                             |
        |_____________________________|_____________________________|
                                      |
                            [ Azure SQL Database ]
                            (Centralized Schema)
```

### 2.4 Data Flow and Synchronization
The system employs an asynchronous event pattern for non-critical paths. For example, when a user uploads a file, the API accepts the upload, pushes a message to an Azure Service Bus, and an Azure Function triggers the virus scan and CDN propagation in the background.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority: High | Status: Not Started**

**Description:**
The system requires a fully automated billing engine to transition from a free internal tool to a commercial SaaS product. This module must handle multi-tier subscription plans (Basic, Pro, Enterprise), automated invoicing, and grace-period management for failed payments.

**Functional Requirements:**
- **Tier Management:** Administration must be able to define price points and feature flags associated with each tier.
- **Payment Gateway Integration:** Integration with Stripe API for credit card processing and recurring billing.
- **Dunning Process:** Automated emails to users when a payment fails, with a 7-day grace period before account suspension.
- **Invoice Generation:** PDF generation of monthly invoices stored in the user's account history.

**Technical Implementation:**
The billing module will utilize a "Subscription" table linked to the "Organization" entity. A daily Azure Function (Cron Job) will poll for expiring subscriptions and trigger the Stripe renewal process. We will implement a Webhook listener to handle `invoice.paid` and `customer.subscription.deleted` events from Stripe.

**Acceptance Criteria:**
- Users can successfully sign up for a paid tier.
- The system automatically restricts access to "Pro" features if a subscription lapses.
- Admins can view a dashboard of Monthly Recurring Revenue (MRR).

---

### 3.2 User Authentication and Role-Based Access Control (RBAC)
**Priority: Medium | Status: Not Started**

**Description:**
A comprehensive security layer to manage identity and access. Since Quorum handles sensitive agricultural data, a granular RBAC system is required to ensure users only see data relevant to their assigned region or organization.

**Functional Requirements:**
- **Identity Management:** Support for email/password sign-up and profile management.
- **Role Hierarchy:** Definition of roles: `SuperAdmin`, `OrgAdmin`, `FieldAgent`, and `Viewer`.
- **Permission Mapping:** Mapping roles to specific API permissions (e.g., `FieldAgent` can edit field reports but cannot change billing details).
- **Session Management:** JWT (JSON Web Tokens) with a 1-hour expiration and refresh token rotation.

**Technical Implementation:**
Implementation will utilize ASP.NET Core Identity. The RBAC will be enforced via custom `[Authorize(Roles = "OrgAdmin")]` attributes on controllers. A custom `IAuthorizationHandler` will be developed to check for "Resource Ownership"—ensuring that a `FieldAgent` from Org A cannot access data from Org B, even if they have the correct role.

**Acceptance Criteria:**
- Unauthorized users are redirected to the login page.
- A `Viewer` cannot trigger a `POST` or `DELETE` request to the API.
- Role changes take effect upon the next token refresh.

---

### 3.3 SSO Integration with SAML and OIDC Providers
**Priority: Medium | Status: In Review**

**Description:**
Enterprise customers in AgTech often utilize centralized identity providers (Azure AD, Okta, PingIdentity). Quorum must support Single Sign-On (SSO) to allow these organizations to manage their users centrally.

**Functional Requirements:**
- **SAML 2.0 Support:** Ability to exchange XML-based assertions for user authentication.
- **OIDC Support:** Implementation of OpenID Connect flows for modern identity providers.
- **Configuration Portal:** A secure area for `OrgAdmins` to upload their metadata XML or enter Client IDs and Secrets.
- **Just-In-Time (JIT) Provisioning:** Automatically creating a user account in the Quorum database upon their first successful SSO login.

**Technical Implementation:**
We will integrate `Microsoft.AspNetCore.Authentication.OpenIdConnect` and a third-party SAML library (such as Sustainsys.SAML2). The system will maintain a `SsoConfiguration` table mapping `OrganizationId` to the specific provider's endpoints.

**Acceptance Criteria:**
- A user can log in using their corporate credentials via Okta.
- The system correctly maps SAML group claims to Quorum internal roles.
- SSO configurations can be updated without restarting the service.

---

### 3.4 Offline-First Mode with Background Sync
**Priority: Low (Nice to Have) | Status: In Progress**

**Description:**
Field agents often work in "dead zones" with no cellular connectivity. This feature allows users to continue entering data while offline, which is then synchronized once a connection is restored.

**Functional Requirements:**
- **Local Storage:** Use of IndexedDB in the browser to cache data locally.
- **Conflict Resolution:** A "Last-Write-Wins" strategy by default, with a manual override prompt for critical data conflicts.
- **Sync Queue:** A background worker that monitors network status and pushes queued changes to the server.
- **State Indicators:** UI indicators showing "Syncing...", "Synced", or "Offline - Changes Pending".

**Technical Implementation:**
Blazor WASM will be used to implement a Service Worker. We will create a `LocalStore` service that intercepts API calls when `navigator.onLine` is false. Data will be serialized into JSON and stored in IndexedDB. Upon reconnection, a synchronization loop will iterate through the queue, sending payloads to a `/sync` endpoint.

**Acceptance Criteria:**
- Users can save a field report while in Airplane Mode.
- Data is automatically uploaded when the device reconnects to Wi-Fi.
- The UI accurately reflects the sync status of the local data.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority: Low (Nice to Have) | Status: In Design**

**Description:**
Users need to upload site photos and PDF reports. Because these files are sourced from various external agents, a security layer is required to prevent malware from entering the Stratos Systems ecosystem.

**Functional Requirements:**
- **Secure Upload:** Multipart upload support for files up to 50MB.
- **Automated Scanning:** Integration with an antivirus API (e.g., Windows Defender or ClamAV) to scan files upon upload.
- **CDN Delivery:** Files should be served via Azure CDN to reduce latency for global users.
- **Access Control:** Files are private by default; access is granted via Shared Access Signatures (SAS).

**Technical Implementation:**
Files will be uploaded to an "Incoming" Azure Blob Storage container. An Azure Function trigger will pick up the new file and send it to the scanning service. If clean, the file is moved to the "Production" container. The API will generate a time-limited SAS URL when a user requests a file.

**Acceptance Criteria:**
- A file containing a known virus is blocked and the user is notified.
- Files are served from a CDN edge location rather than the origin server.
- Unauthorized users cannot access files by guessing the URL.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. Base URL: `https://api.quorum.stratos.com/api/v1/`

### 4.1 Authentication
**POST `/auth/login`**
- **Request:** `{ "email": "user@stratos.com", "password": "password123" }`
- **Response:** `200 OK` `{ "token": "eyJ...", "refreshToken": "abc...", "expiresIn": 3600 }`
- **Error:** `401 Unauthorized` `{ "message": "Invalid credentials" }`

**POST `/auth/refresh`**
- **Request:** `{ "refreshToken": "abc..." }`
- **Response:** `200 OK` `{ "token": "eyJ...", "expiresIn": 3600 }`

### 4.2 Billing
**GET `/billing/subscription`**
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `200 OK` `{ "plan": "Pro", "status": "Active", "nextBillingDate": "2025-11-01" }`

**POST `/billing/upgrade`**
- **Request:** `{ "planId": "plan_pro_99" }`
- **Response:** `202 Accepted` `{ "status": "Processing", "transactionId": "txn_123" }`

### 4.3 Users & RBAC
**GET `/users/profile`**
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `200 OK` `{ "userId": "u1", "fullName": "Omar Liu", "role": "SuperAdmin" }`

**PUT `/users/roles/{userId}`**
- **Request:** `{ "role": "FieldAgent" }`
- **Response:** `200 OK` `{ "userId": "u1", "newRole": "FieldAgent" }`

### 4.4 File Management
**POST `/files/upload`**
- **Request:** `multipart/form-data` (File, FileName, OrgId)
- **Response:** `202 Accepted` `{ "fileId": "f99", "status": "Scanning" }`

**GET `/files/download/{fileId}`**
- **Request:** (Header: Authorization Bearer Token)
- **Response:** `302 Found` (Redirect to Azure CDN SAS URL)

### 4.5 Sync (Offline Mode)
**POST `/sync/push`**
- **Request:** `[ { "action": "create", "entity": "Report", "data": { ... } }, ... ]`
- **Response:** `200 OK` `{ "processed": 12, "conflicts": 1, "conflictIds": ["rep_44"] }`

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions
The database uses Azure SQL. All tables include `CreatedAt` and `UpdatedAt` timestamps.

1. **Organizations**
   - `OrgId` (PK, Guid)
   - `OrgName` (NVarChar 255)
   - `SsoConfigId` (FK to SsoConfigs)
   - `CreatedAt` (DateTime2)

2. **Users**
   - `UserId` (PK, Guid)
   - `OrgId` (FK to Organizations)
   - `Email` (NVarChar 255, Unique)
   - `PasswordHash` (VarBinary)
   - `Role` (NVarChar 50)
   - `IsActive` (Bit)

3. **RolesPermissions**
   - `RoleId` (PK, Guid)
   - `RoleName` (NVarChar 50)
   - `PermissionKey` (NVarChar 100)

4. **Subscriptions**
   - `SubscriptionId` (PK, Guid)
   - `OrgId` (FK to Organizations)
   - `StripeCustomerId` (NVarChar 100)
   - `PlanTier` (NVarChar 50)
   - `StartDate` (DateTime2)
   - `EndDate` (DateTime2)

5. **BillingEvents**
   - `EventId` (PK, Guid)
   - `SubscriptionId` (FK to Subscriptions)
   - `Amount` (Decimal 18,2)
   - `TransactionStatus` (NVarChar 50)
   - `EventDate` (DateTime2)

6. **SsoConfigs**
   - `SsoConfigId` (PK, Guid)
   - `ProviderType` (NVarChar 20) - (SAML/OIDC)
   - `MetadataUrl` (NVarChar 500)
   - `ClientId` (NVarChar 255)
   - `ClientSecret` (NVarChar 500, Encrypted)

7. **Files**
   - `FileId` (PK, Guid)
   - `OrgId` (FK to Organizations)
   - `BlobPath` (NVarChar 500)
   - `ScanStatus` (NVarChar 20) - (Pending, Clean, Infected)
   - `FileSize` (BigInt)

8. **FieldReports**
   - `ReportId` (PK, Guid)
   - `UserId` (FK to Users)
   - `OrgId` (FK to Organizations)
   - `Content` (NVarChar(MAX))
   - `LastModified` (DateTime2)

9. **SyncQueue**
   - `QueueId` (PK, Guid)
   - `UserId` (FK to Users)
   - `Payload` (NVarChar(MAX))
   - `Timestamp` (DateTime2)

10. **AuditLogs**
    - `LogId` (PK, Guid)
    - `UserId` (FK to Users)
    - `Action` (NVarChar 100)
    - `Timestamp` (DateTime2)
    - `IpAddress` (NVarChar 45)

### 5.2 Relationships
- **Organizations (1:N) Users**: One organization has many users.
- **Organizations (1:1) SsoConfigs**: One organization has one SSO configuration.
- **Organizations (1:1) Subscriptions**: An organization has one active subscription.
- **Subscriptions (1:N) BillingEvents**: One subscription has many payment events.
- **Users (1:N) FieldReports**: One user can create many reports.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum utilizes a three-tier environment strategy to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and rapid iteration.
- **Deployment:** Automatic deployment from `develop` branch via GitHub Actions.
- **Database:** Azure SQL (Basic Tier).
- **Access:** Restricted to the core development team.

#### 6.1.2 Staging (QA)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Deployment:** Manual trigger from `release` branch.
- **Database:** Azure SQL (Standard Tier, mirrored prod schema).
- **Gate:** Every deployment requires a manual QA sign-off by Xavi Moreau.
- **Turnaround:** 2-day window for testing before promotion to Production.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Deployment:** Manual approval by Omar Liu.
- **Database:** Azure SQL (Hyperscale).
- **Scaling:** Auto-scaling enabled for App Services (Minimum 2 instances).

### 6.2 Deployment Pipeline
1. **CI Stage:** GitHub Actions runs unit tests $\rightarrow$ Build Artifact $\rightarrow$ NuGet Package.
2. **Staging Stage:** Artifact deployed to Staging $\rightarrow$ Integration Tests run $\rightarrow$ Xavi validates UX.
3. **QA Gate:** Manual checkmark in GitHub Actions.
4. **Production Stage:** Blue/Green deployment to minimize downtime.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Scope:** All business logic in the `Domain` and `Application` layers.
- **Coverage Target:** 80% code coverage for critical modules (Billing, Auth).
- **Execution:** Run on every commit via CI pipeline.

### 7.2 Integration Testing
- **Framework:** WebApplicationFactory.
- **Scope:** API endpoint verification, Database constraint validation, and External API mocks (Stripe, Azure Blob).
- **Execution:** Run during the Staging deployment phase.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scope:** Critical user journeys:
    - Login $\rightarrow$ Create Report $\rightarrow$ Upload File.
    - Upgrade Subscription $\rightarrow$ Access Pro Feature.
    - SSO Login $\rightarrow$ Dashboard Access.
- **Execution:** Weekly scheduled runs on the Staging environment.

### 7.4 Penetration Testing
- **Frequency:** Quarterly.
- **Scope:** OWASP Top 10 check, focusing on SQL Injection in report queries and Insecure Direct Object References (IDOR) in file downloads.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Team lack of experience with .NET/Azure stack | High | High | Build a contingency "Fallback Architecture" (Node.js/Postgres) and schedule weekly "Deep Dive" learning sessions. | Omar Liu |
| **R-02** | Key Architect leaving in 3 months | Medium | Critical | Immediate knowledge transfer sessions. Assign Tala (Intern) to document all architectural decisions in the Wiki. | Omar Liu |
| **R-03** | Budget approval for critical tools pending | Medium | Medium | Identify open-source alternatives for the pending tool to maintain momentum. | Stratos Mgmt |
| **R-04** | Technical Debt: Date format inconsistency | High | Medium | Implement a `DateTimeNormalization` middleware layer to standardize all API inputs to ISO-8601. | Kaia Santos |

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Description
- **Phase 1: Foundation (Now - June 2025)**
  - Focus: RBAC, SSO, and Database stabilization.
  - Dependency: Budget approval for core tool.
- **Phase 2: Commercialization (June 2025 - August 2025)**
  - Focus: Automated Billing, Stripe Integration, and Production hardening.
  - Dependency: Completion of RBAC.
- **Phase 3: Expansion (August 2025 - December 2025)**
  - Focus: Offline-first mode, CDN, and User growth.
  - Dependency: Production launch.

### 9.2 Key Milestone Dates
| Milestone | Target Date | Success Criteria |
| :--- | :--- | :--- |
| **Production Launch** | 2025-08-15 | System live, 500 internal users migrated, p95 < 200ms. |
| **Internal Alpha Release** | 2025-10-15 | Beta group (20 external users) testing billing and SSO. |
| **First Paying Customer** | 2025-12-15 | First successful Stripe transaction from an external org. |

---

## 10. MEETING NOTES (Sourced from Slack)

*Note: Per company policy, formal minutes are not kept. The following are reconstructed from the `#quorum-dev` Slack channel.*

### Meeting 1: Tech Stack Anxiety (Date: 2023-11-02)
- **Participants:** Omar, Kaia, Xavi
- **Discussion:** Kaia expressed concern that the team is too lean for the complexity of .NET Hyperscale. Xavi noted that the UX might suffer if the API response times lag due to poorly optimized C# queries.
- **Decision:** Omar decided to implement a "Modular Monolith" approach. This allows them to stay simple for now but move to microservices if the performance hits a wall.
- **Action Item:** Omar to create a "Learning Roadmap" for the team.

### Meeting 2: The Date Format Disaster (Date: 2023-11-15)
- **Participants:** Omar, Kaia, Tala
- **Discussion:** Tala discovered that the hackathon code uses `MM-DD-YYYY` in the frontend, `YYYY-MM-DD` in the DB, and `Unix Timestamps` in the Azure Functions.
- **Decision:** No immediate rewrite. They will implement a `NormalizationLayer` in the API that converts all incoming dates to UTC ISO-8601 before it hits the service layer.
- **Action Item:** Kaia to draft the middleware logic.

### Meeting 3: Budgetary Roadblocks (Date: 2023-12-01)
- **Participants:** Omar, Stratos Finance Rep
- **Discussion:** Omar requested budget for a specialized security scanning tool. Finance stated approval is "pending review" due to end-of-year budget freezes.
- **Decision:** The team will use an open-source scanner (ClamAV) as a temporary measure until the $400k budget is fully unlocked.
- **Action Item:** Omar to track the budget approval weekly.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Salaries for Tech Lead, Data Engineer, UX Researcher, and Intern. |
| **Infrastructure** | 15% | $60,000 | Azure Consumption (SQL Hyperscale, App Services, CDN, Functions). |
| **Tools & Licences** | 10% | $40,000 | Stripe Fees, IDE Licences, Security Scanning Software. |
| **Contingency** | 10% | $40,000 | Buffer for unexpected architecture pivots or emergency scaling. |

---

## 12. APPENDICES

### Appendix A: Date Normalization Logic
To resolve the technical debt of disparate date formats, the following logic will be applied in the `DateNormalizationMiddleware.cs`:
1. **Input Capture:** All requests are scanned for date-like strings.
2. **Format Detection:** Regex patterns identify `MM-DD-YYYY`, `YYYY-MM-DD`, and `Unix`.
3. **Conversion:** All values are cast to `DateTimeOffset` (UTC).
4. **Storage:** Only `DateTimeOffset` is permitted in the Azure SQL `DateTime2` columns.

### Appendix B: Performance Benchmarking Setup
To meet the success criterion of **p95 < 200ms**, the team will use **Azure Load Testing** with the following profile:
- **Virtual Users:** 1,000 concurrent users.
- **Test Scenario:** 40% Read (Reports), 30% Write (Sync), 20% Auth, 10% Billing.
- **Monitoring:** Azure Monitor + Application Insights will be used to track the "Dependency Duration" to identify if the bottleneck is the SQL query or the App Service logic.