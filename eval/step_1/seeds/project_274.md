Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Project Specification Document (PSD). To ensure the depth requested, every section has been expanded with the required technical granularities, specific paths, schemas, and organizational logic.

***

# PROJECT SPECIFICATION DOCUMENT: IRONCLAD
**Project Code:** IC-2025-TI  
**Version:** 1.0.4 (Draft for Implementation)  
**Date:** October 24, 2024  
**Company:** Talus Innovations  
**Industry:** Renewable Energy  
**Classification:** Restricted / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Ironclad" represents a critical platform modernization effort for Talus Innovations. As a leader in the renewable energy sector—managing sprawling grids of wind, solar, and hydroelectric assets—Talus Innovations requires a cybersecurity monitoring dashboard that can keep pace with the escalating threat landscape of Industrial Control Systems (ICS) and Supervisory Control and Data Acquisition (SCADA) networks. 

The current legacy system is a monolithic entity that has reached its scaling limit. Ironclad is designed to transition this capability into a modernized architecture. While the immediate implementation utilizes a "clean monolith" approach (modular monolith) to maintain velocity, the overarching 18-month roadmap mandates a gradual transition to a microservices architecture. This ensures that the system can scale horizontally as Talus expands its energy portfolio globally.

### 1.2 Business Justification
The renewable energy sector is currently a primary target for state-sponsored cyber-attacks. A failure in monitoring could lead to catastrophic grid instability or physical damage to turbine/panel infrastructure. The "Ironclad" dashboard will centralize security telemetry, providing real-time visibility into anomalies, unauthorized access attempts, and system health across all renewable assets.

By consolidating security monitoring into a single, high-performance pane of glass, Talus Innovations reduces the "Mean Time to Detect" (MTTD) and "Mean Time to Respond" (MTTR). Currently, security analysts must pivot between four different legacy tools; Ironclad collapses this into one, increasing analyst efficiency by an estimated 40%.

### 1.3 ROI Projection
The financial justification for Ironclad is based on risk mitigation and operational efficiency. 
- **Direct Cost Reduction:** By moving to a modernized Microsoft stack (Azure Functions and Azure SQL), Talus expects a 15% reduction in on-premise server maintenance costs.
- **Risk Avoidance:** The projected cost of a single successful breach of a renewable energy hub is estimated at $4.2M (including regulatory fines, cleanup, and downtime). Ironclad’s ability to block unauthorized access through SSO and hardware-backed MFA reduces the probability of a breach by an estimated 65%.
- **Scalability Value:** The ability to onboard 10,000 monthly active users (MAUs) within six months of launch allows Talus to offer "Security-as-a-Service" to its subsidiary energy partners, creating a new revenue stream estimated at $200k ARR per partner.

### 1.4 Strategic Alignment
Ironclad aligns with the "Digital Transformation 2026" initiative at Talus Innovations, emphasizing cloud-native scalability, strict adherence to international data laws (GDPR/CCPA), and the transition from reactive to proactive security postures.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Philosophy
Ironclad utilizes a **Clean Monolith** architecture. The system is built as a single deployable unit but maintains strict logical boundaries between modules (e.g., Identity, Reporting, Telemetry, Analytics). This prevents the "spaghetti code" common in legacy systems while avoiding the operational complexity of microservices during the initial launch phase. Over the next 18 months, these boundaries will be used as "seams" to extract microservices into Azure Functions.

### 2.2 The Technology Stack
- **Language/Framework:** C# .NET 8.0 (LTS)
- **Database:** Azure SQL Database (Hyperscale tier for scalability)
- **Compute:** Azure App Service (for the API/Web core) and Azure Functions (for asynchronous tasks like report generation and telemetry processing)
- **Authentication:** Azure Active Directory (Azure AD) / Microsoft Entra ID
- **Deployment:** Azure DevOps Pipelines (CI/CD)
- **Infrastructure as Code (IaC):** Terraform

### 2.3 ASCII Architectural Diagram
Below is the logical flow of the Ironclad environment:

```text
[ User Browser / Client ] 
          |
          v
[ Azure Front Door / WAF ] <--- (DDoS Protection & SSL Termination)
          |
          v
[ Azure App Service (The Clean Monolith) ]
|-----------------------------------------------------------------------|
|  [ API Gateway Layer ]  --> [ Rate Limiting / Usage Analytics ]        |
|          |                                                            |
|  [ Module: Identity ]    --> [ SSO / SAML / OIDC Integration ]        |
|          |                                                            |
|  [ Module: Telemetry ]   --> [ Real-time Monitoring / Alerting ]        |
|          |                                                            |
|  [ Module: Reporting ]   --> [ PDF/CSV Engine / Scheduled Tasks ]      |
|-----------------------------------------------------------------------|
          |                                      |
          v                                      v
[ Azure SQL Database ] <----------------- [ Azure Functions (Background) ]
(Multi-tenant Tables)                     (Report Generation / Data Sync)
          |
          v
[ Azure Blob Storage ] <--- (Stored PDFs and CSV exports)
```

### 2.3 Data Residency and Compliance
To satisfy **GDPR and CCPA** requirements, all production data resides exclusively in the **Azure North Europe (Ireland)** and **Azure West Europe (Netherlands)** regions. No data is replicated to US-based regions. The database employs "Row-Level Security" (RLS) to ensure that data from a specific tenant is never visible to another, meeting the strict isolation requirements of the renewable energy sector.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Single Sign-On (SSO) Integration
**Priority:** Critical | **Status:** In Review | **Requirement:** Launch Blocker

**Description:**
Ironclad must support seamless authentication via SAML 2.0 and OpenID Connect (OIDC). As Talus Innovations operates as a corporate entity with various subsidiaries, the dashboard must integrate with multiple external Identity Providers (IdPs) including Azure AD, Okta, and Ping Identity.

**Technical Details:**
The SSO module will implement a "Service Provider Initiated" (SP-Initiated) flow. Upon hitting the `/auth/login` endpoint, the system will identify the user's organization based on their email domain and redirect them to the corresponding IdP. The system must handle the exchange of SAML assertions and JWT (JSON Web Tokens) for OIDC.

**Functional Requirements:**
- **Attribute Mapping:** The system must map IdP claims (e.g., `groups`, `role`, `email`) to internal Ironclad permissions.
- **Just-In-Time (JIT) Provisioning:** If a user is authenticated via SSO but does not exist in the local Azure SQL database, a profile must be created automatically based on the provided claims.
- **Session Management:** Sessions must be managed via encrypted cookies with a maximum TTL (Time-to-Live) of 8 hours, after which a re-authentication event is triggered.

**Acceptance Criteria:**
- Users can log in using their corporate credentials from at least three different IdPs.
- The system correctly maps "Admin" roles from the IdP to "SuperAdmin" in Ironclad.
- Unauthorized attempts to access the dashboard without a valid SSO token are redirected to the login page.

---

### 3.2 Multi-Tenant Data Isolation
**Priority:** High | **Status:** In Progress

**Description:**
Ironclad serves multiple distinct energy entities (tenants). To prevent data leakage and ensure regulatory compliance, the system must implement a shared-infrastructure, isolated-data model. 

**Technical Details:**
Isolation is achieved through a "Discriminator Column" approach combined with Azure SQL Row-Level Security (RLS). Every table in the database contains a `TenantId` (GUID). A session-level context variable `SESSION_CONTEXT(N'TenantId')` is set upon every API request. The database engine then automatically filters all `SELECT`, `UPDATE`, and `DELETE` queries to only those rows matching the current `TenantId`.

**Functional Requirements:**
- **Tenant Onboarding:** A super-administrator must be able to create a new tenant, assign a unique GUID, and define the tenant's subscription tier.
- **Cross-Tenant Leakage Prevention:** No query shall be permitted to execute without a `WHERE TenantId = @CurrentTenant` clause, enforced by the RLS policy.
- **Shared Infrastructure:** All tenants share the same compute resources (App Service), but their data is logically separated.

**Acceptance Criteria:**
- A user from Tenant A cannot access data from Tenant B, even if they possess the direct URL/ID of Tenant B's assets.
- The system handles 500+ concurrent tenants without performance degradation in query response times.

---

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** Not Started

**Description:**
To protect the system from Denial of Service (DoS) attacks and to monitor the consumption of resources by different tenants, Ironclad requires a robust rate-limiting layer and an analytics engine.

**Technical Details:**
Rate limiting will be implemented using a "Token Bucket" algorithm. Limits will be defined per API key or per User Session. These limits will be stored in a distributed cache (Azure Cache for Redis) to ensure consistency across multiple app service instances. Usage analytics will be captured via a middleware component that logs every request to a telemetry table in Azure SQL.

**Functional Requirements:**
- **Tiered Limits:** "Standard" tenants are limited to 1,000 requests per hour; "Enterprise" tenants are limited to 10,000 requests per hour.
- **HTTP 429 Response:** When a limit is exceeded, the API must return a `429 Too Many Requests` status code, including a `Retry-After` header.
- **Analytics Dashboard:** A view for administrators showing the most active API endpoints and the top 10 users by request volume.

**Acceptance Criteria:**
- The system successfully blocks requests exceeding the defined threshold.
- The Redis cache updates the token count in real-time (< 50ms latency).
- Usage reports can be generated for any 24-hour window.

---

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** Blocked (Pending Security Review)

**Description:**
Given the sensitivity of renewable energy infrastructure, standard password/email 2FA is insufficient. Ironclad must support FIDO2/WebAuthn standards to allow the use of physical hardware keys (e.g., YubiKey, Google Titan).

**Technical Details:**
The implementation will use the WebAuthn API. The server will generate a challenge that the hardware key signs with its private key. The resulting signature is then verified by the server using the previously registered public key.

**Functional Requirements:**
- **Hardware Registration:** Users can register multiple hardware keys to their account.
- **Fallback Mechanisms:** Users may configure a secondary "Recovery Code" list (one-time use) in case a hardware key is lost.
- **Enforcement:** Admins can mandate hardware 2FA for users with "Write" access to the energy grid configurations.

**Acceptance Criteria:**
- A user cannot log in to a high-privilege account without a successful hardware key handshake.
- The system supports the latest FIDO2 specifications.

---

### 3.5 PDF/CSV Report Generation and Scheduled Delivery
**Priority:** Medium | **Status:** Not Started

**Description:**
The dashboard must be able to export complex security telemetry and audit logs into professional PDF and CSV formats. These reports must be deliverable via email on a scheduled basis (daily, weekly, monthly).

**Technical Details:**
Due to the resource-intensive nature of PDF generation, this feature will be decoupled from the main API. A request for a report will be placed in an Azure Storage Queue. An Azure Function (Triggered by the queue) will pull the data from Azure SQL, use a library like `QuestPDF` or `iTextSharp` to generate the document, upload it to Azure Blob Storage, and send a secure link via SendGrid.

**Functional Requirements:**
- **Custom Templates:** Users can choose between "Executive Summary" (PDF) and "Detailed Technical Log" (CSV).
- **Scheduling Engine:** A Cron-job style scheduler (Azure Functions Timer Trigger) to automate delivery.
- **Secure Delivery:** Reports must not be sent as raw attachments; instead, a time-limited, authenticated link to the blob storage must be emailed.

**Acceptance Criteria:**
- A PDF report is generated within 60 seconds of a request.
- Scheduled reports arrive at the correct timestamp across different time zones.
- CSV exports handle 100,000+ rows without timing out.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 Endpoint: `GET /telemetry/alerts`
**Description:** Retrieves a list of security alerts for the authenticated tenant.
- **Request Params:** `severity` (optional), `startTime` (ISO 8601), `endTime` (ISO 8601).
- **Success Response:** `200 OK`
- **Example Response:**
```json
[
  {
    "alertId": "AL-9902",
    "timestamp": "2025-01-12T14:22:01Z",
    "severity": "Critical",
    "message": "Unauthorized access attempt on Turbine-04 Controller",
    "sourceIp": "192.168.1.45"
  }
]
```

### 4.2 Endpoint: `POST /auth/sso/callback`
**Description:** Handles the SAML/OIDC callback from the Identity Provider.
- **Request Body:** `SAMLRequest` or `OIDC Token`.
- **Success Response:** `200 OK` + JWT Token.
- **Example Response:**
```json
{
  "accessToken": "eyJhbGci...[truncated]",
  "expiresIn": 28800,
  "tokenType": "Bearer"
}
```

### 4.3 Endpoint: `POST /reports/generate`
**Description:** Triggers an asynchronous report generation task.
- **Request Body:** `{"type": "PDF", "format": "Executive", "startDate": "2024-10-01"}`.
- **Success Response:** `202 Accepted`.
- **Example Response:**
```json
{
  "jobId": "job_882104",
  "status": "Queued",
  "estimatedCompletion": "2025-10-24T15:00:00Z"
}
```

### 4.4 Endpoint: `GET /reports/download/{jobId}`
**Description:** Retrieves the final report link.
- **Success Response:** `200 OK`.
- **Example Response:**
```json
{
  "jobId": "job_882104",
  "downloadUrl": "https://storage.azure.com/reports/x92j...?",
  "expiry": "2025-10-24T18:00:00Z"
}
```

### 4.5 Endpoint: `GET /tenant/settings`
**Description:** Fetches the current configuration and rate limit status for the tenant.
- **Success Response:** `200 OK`.
- **Example Response:**
```json
{
  "tenantName": "WindFarm-North",
  "tier": "Enterprise",
  "rateLimitRemaining": 8420,
  "region": "EU-West"
}
```

### 4.6 Endpoint: `PUT /tenant/settings`
**Description:** Updates tenant-level configurations.
- **Request Body:** `{"updateRegion": "EU-North", "contactEmail": "admin@windfarm.com"}`.
- **Success Response:** `200 OK`.

### 4.7 Endpoint: `GET /analytics/usage`
**Description:** Returns usage statistics for the current tenant's API consumption.
- **Success Response:** `200 OK`.
- **Example Response:**
```json
{
  "period": "Last 30 Days",
  "totalRequests": 150000,
  "peakRequestHour": "2025-10-10T02:00:00Z",
  "errorRate": "0.04%"
}
```

### 4.8 Endpoint: `POST /auth/mfa/register`
**Description:** Registers a new FIDO2 hardware key.
- **Request Body:** `{"publicKey": "...", "credentialId": "..."}`.
- **Success Response:** `201 Created`.

---

## 5. DATABASE SCHEMA

The database is an Azure SQL instance. All tables use `NVARCHAR(MAX)` for flexibility and `DATETIMEOFFSET` for timezone-aware timestamps.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` | None | `Name`, `TierId`, `CreatedDate` | Core tenant identity |
| `Users` | `UserId` | `TenantId` | `Email`, `Username`, `PasswordHash` | User account storage |
| `UserRoles` | `RoleId` | `UserId` | `RoleName`, `PermissionLevel` | RBAC mapping |
| `SsoProviders` | `ProviderId` | `TenantId` | `ProviderType`, `EntityId`, `Cert` | SAML/OIDC config |
| `TelemetryLogs` | `LogId` | `TenantId` | `EventSource`, `Payload`, `Timestamp` | Raw security events |
| `Alerts` | `AlertId` | `LogId`, `TenantId` | `Severity`, `IsResolved`, `ResolvedDate` | Escalated telemetry |
| `MfaKeys` | `KeyId` | `UserId` | `PublicKey`, `KeyType`, `RegisteredDate` | Hardware key storage |
| `ReportJobs` | `JobId` | `UserId`, `TenantId` | `ReportType`, `Status`, `BlobUrl` | Async report tracking |
| `ApiUsage` | `UsageId` | `UserId`, `TenantId` | `Endpoint`, `Timestamp`, `ResponseCode` | Rate limiting logs |
| `Tiers` | `TierId` | None | `TierName`, `RequestLimit`, `Price` | Subscription levels |

### 5.2 Key Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many (A tenant has many users).
- **Users $\rightarrow$ MfaKeys:** One-to-Many (A user can have multiple hardware keys).
- **Tenants $\rightarrow$ TelemetryLogs:** One-to-Many (Strictly isolated by `TenantId`).
- **TelemetryLogs $\rightarrow$ Alerts:** One-to-One (A specific log entry triggers a specific alert).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and initial unit testing.
- **Configuration:** Low-tier Azure App Service (B1), Azure SQL Basic.
- **Deployment:** Triggered on every push to the `develop` branch.
- **Data:** Synthetic data only; no real PII (Personally Identifiable Information).

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing, UAT (User Acceptance Testing), and Performance Benchmarking.
- **Configuration:** Mirrors Production (P2v3 App Service, Hyperscale SQL).
- **Deployment:** Triggered on merge to the `release` branch.
- **Data:** Anonymized production snapshots.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user traffic.
- **Configuration:** High-availability (HA) cluster, Multi-region failover, Azure Front Door.
- **Deployment:** Continuous Deployment (CD). Every PR merged into `main` is deployed to Production after passing the Staging smoke tests.
- **Data:** Real production data; strict GDPR residency in EU.

### 6.2 CI/CD Pipeline
The pipeline is managed via Azure DevOps.
1. **Build Phase:** `.NET build` $\rightarrow$ `NuGet restore` $\rightarrow$ `Unit Test Execution`.
2. **Analysis Phase:** SonarQube scan for security vulnerabilities and code smells.
3. **Deployment Phase:** Terraform apply to update infrastructure $\rightarrow$ Kudu deploy to App Service.
4. **Validation Phase:** Automated Selenium smoke tests for critical paths (Login, Dashboard Load).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Every business logic class must have a corresponding test class using xUnit and Moq.
- **Coverage Goal:** 80% code coverage on the `Core` and `Services` layers.
- **Frequency:** Run on every commit.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the API and Azure SQL. We use "Testcontainers" to spin up a temporary SQL instance to ensure the RLS (Row-Level Security) policies are correctly filtering data.
- **Focus:** API Endpoint $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ DB.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Using Playwright to simulate user journeys.
- **Critical Paths:**
    - SSO Login $\rightarrow$ Navigate to Dashboard $\rightarrow$ Generate Report.
    - Admin $\rightarrow$ Create New Tenant $\rightarrow$ Assign User $\rightarrow$ Verify Access.
    - User $\rightarrow$ Register Hardware Key $\rightarrow$ Perform 2FA Login.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance requirements are 10x current system capacity with no extra budget. | High | High | **Accept Risk.** Monitor weekly via Azure Monitor. Optimize queries and implement Redis caching to squeeze performance from existing hardware. |
| **R2** | Budget may be cut by 30% in the next fiscal quarter. | Medium | High | **Contingency Planning.** Document "Lite" versions of features. Prioritize "Critical" features (SSO) over "Medium" (PDF reports). Share workaround documents with team. |
| **R3** | Legal review of the Data Processing Agreement (DPA) is delayed. | High | Medium | **Current Blocker.** Weekly follow-up with Legal. Proceed with development using dummy data, but delay Production deployment. |
| **R4** | Technical debt (Hardcoded config in 40+ files). | High | Medium | **Refactoring Sprint.** Schedule a "Debt Cleanup" sprint every 4th iteration to move values to Azure Key Vault. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Month 1-6):** Focus on the Clean Monolith setup, Multi-tenant isolation, and SSO integration.
- **Phase 2: Expansion (Month 7-12):** Implementation of 2FA, API analytics, and the Reporting engine.
- **Phase 3: Optimization & Migration (Month 13-18):** Gradual extraction of services into Azure Functions (Microservices transition) and final scaling.

### 9.2 Key Milestones

| Milestone | Target Date | Dependency | Success Criteria |
| :--- | :--- | :--- | :--- |
| **M1: Performance Benchmarks** | 2025-04-15 | Multi-tenant logic | System handles 10k req/sec with <200ms latency. |
| **M2: External Beta** | 2025-06-15 | SSO Integration | 10 pilot users successfully onboarded and using the system. |
| **M3: Security Audit** | 2025-08-15 | 2FA Implementation | External auditor signs off on GDPR compliance and penetration tests. |

---

## 10. MEETING NOTES (Shared Running Document)
*Note: This is an excerpt from the 200-page unsearchable shared document. The style is conversational and disorganized.*

### Meeting 1: 2024-11-05 — Architecture Sync
**Attendees:** Manu Oduya, Meera Jensen, Devika Moreau, Sanjay Nakamura.
- **Discussion:** Manu expressed concern about the 18-month timeline for the microservices shift. Meera suggested that we don't jump straight into K8s (Kubernetes) and instead use the "Clean Monolith" approach first. 
- **Decision:** Agreed. We will build it as one project but use separate folders/namespaces for "Identity", "Reports", and "Telemetry". This allows us to split them into Azure Functions later without rewriting the whole thing.
- **Action Item:** Meera to set up the Azure App Service environment.

### Meeting 2: 2024-12-12 — The "Budget Panic"
**Attendees:** Manu Oduya, Meera Jensen, Devika Moreau, Sanjay Nakamura.
- **Discussion:** Manu warned the team that the next fiscal quarter might see a 30% budget cut. Devika asked if this means we lose the budget for the hardware keys. 
- **Decision:** Manu said we keep the priority on SSO (the launch blocker). If the budget is cut, we might postpone the PDF report generation or use a cheaper library. 
- **Sanjay's Note:** Sanjay mentioned that the hardcoded config values are becoming a nightmare; he found them in 42 different files today. 
- **Action Item:** Everyone to stop adding hardcoded strings; move them to `appsettings.json` immediately.

### Meeting 3: 2025-01-20 — Legal Blocker Update
**Attendees:** Manu Oduya, Meera Jensen, Devika Moreau, Sanjay Nakamura.
- **Discussion:** The team is frustrated that they can't move to the production environment because the Data Processing Agreement (DPA) is still with the legal team. 
- **Decision:** We will keep developing in the Staging environment using "scrubbed" data. Devika will perform a "pre-audit" to make sure we don't fail the official August audit.
- **Action Item:** Manu to escalate the DPA review to the COO.

---

## 11. BUDGET BREAKDOWN

Budget is released in tranches based on the completion of milestones. Total budget is variable, but the current allocation for the first 12 months is as follows:

| Category | Allocation (USD) | Details |
| :--- | :--- | :--- |
| **Personnel** | $1,200,000 | 8 members (avg $150k/year including benefits). |
| **Infrastructure** | $180,000 | Azure App Service, Azure SQL Hyperscale, Redis Cache. |
| **Security Tools** | $45,000 | SonarQube, Snyk, External Pen-Testing firm. |
| **Licensing** | $25,000 | SendGrid (for reports), Microsoft Entra ID Premium. |
| **Contingency** | $100,000 | Reserved for emergency scaling or legal compliance costs. |
| **Total (Year 1)** | **$1,550,000** | |

---

## 12. APPENDICES

### Appendix A: Data Residency Mapping
To comply with GDPR, the following mapping is enforced:
- **EU Tenant Data** $\rightarrow$ Azure North Europe (Ireland) $\rightarrow$ SQL DB Instance `ironclad-eu-sql-01`
- **EU Backup Data** $\rightarrow$ Azure West Europe (Netherlands) $\rightarrow$ Storage Account `ironclad-eu-backup`
- **Global Config** $\rightarrow$ Read-only replication across regions.
- **US Access** $\rightarrow$ Strictly prohibited via Azure Firewall policies.

### Appendix B: Hardware Key Specification
The system supports the following WebAuthn requirements:
- **Algorithm:** ECDSA with P-256 curve.
- **User Verification:** Required for all "Write" operations.
- **Attestation:** Indirect attestation allowed for general hardware keys; direct attestation required for government-issued keys.
- **Timeout:** The challenge-response window is set to 60 seconds. If the hardware key is not tapped within this window, the session expires and the user must restart the 2FA flow.