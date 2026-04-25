# PROJECT SPECIFICATION DOCUMENT: MERIDIAN
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Project Status:** Active/In-Development  
**Classification:** Confidential – Verdant Labs Internal  
**Security Level:** PCI DSS Level 1 Compliant  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project "Meridian" is a mission-critical initiative undertaken by Verdant Labs to engineer a next-generation real-time collaboration tool tailored specifically for the Media and Entertainment (M&E) industry. The primary objective of Meridian is the wholesale replacement of a 15-year-old legacy collaboration system. This legacy system, while functional, has become a significant bottleneck due to technical obsolescence, inability to scale with modern 4K/8K media workflows, and mounting maintenance costs. Because the entire company depends on this system for daily operations, the project is governed by a "zero downtime tolerance" mandate. Any interruption in service during the migration would result in immediate production halts across multiple global studios.

**Business Justification**  
The current legacy system represents a systemic risk. Its architecture cannot support modern concurrent editing, and its security protocols are outdated, posing a liability for the high-value intellectual property managed by Verdant Labs. By transitioning to Meridian, the company will realize immediate gains in operational efficiency, reducing the "time-to-delivery" for media assets by an estimated 22%. 

Furthermore, Meridian is designed not just as an internal tool but as a potential revenue generator. By implementing multi-tenant data isolation and PCI DSS Level 1 compliance, Verdant Labs can offer "Collaboration-as-a-Service" to external production partners.

**ROI Projection and Success Criteria**  
The financial viability of Meridian is anchored in two primary KPIs:
1.  **Direct Revenue Growth:** The project is projected to generate $500,000 in new revenue within the first 12 months post-launch through tiered subscription models for external partners.
2.  **Operational Risk Mitigation:** Success is defined by passing the external PCI DSS and security audits on the first attempt, avoiding the costly remediation cycles typically associated with legacy upgrades.

With a dedicated budget of $800,000, the project is positioned for a 6-month aggressive build cycle. The ROI is calculated based on the reduction of legacy maintenance costs (estimated at $120k/year) and the projected $500k revenue stream, yielding a positive return within 18 months of deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Meridian utilizes **Hexagonal Architecture (Ports and Adapters)**. This choice is critical given the requirement to replace a legacy system without downtime. By decoupling the core business logic (the Domain) from the external technologies (the Adapters), the team can swap out the legacy data sources for new Azure SQL tables without modifying the core collaboration logic.

### 2.2 The Technology Stack
- **Language/Framework:** C# / .NET 8 (Long Term Support)
- **Database:** Azure SQL Database (Hyperscale tier for high-volume media metadata)
- **Compute:** Azure Functions (Serverless for event-driven tasks like virus scanning and notification dispatch)
- **Identity:** Azure Active Directory (Microsoft Entra ID)
- **Distribution:** Azure Front Door and Azure CDN for global asset delivery
- **Messaging:** Azure Service Bus for real-time synchronization across clients

### 2.3 ASCII Architectural Diagram
The following diagram represents the flow of data from the client through the hexagonal layers to the persistence layer.

```text
[ CLIENT LAYER ] <---> [ API ADAPTER ] <---> [ APPLICATION SERVICE ]
       |                     |                        |
(React/TypeScript)    (REST / SignalR)          (Use Case Logic)
                                                      |
                                                      v
[ INFRASTRUCTURE ] <--- [ PERSISTENCE ADAPTER ] <--- [ DOMAIN CORE ]
       |                     |                        |
(Azure SQL / CDN)      (EF Core / Dapper)       (Business Entities)
       ^                     ^                        ^
       |                     |                        |
       +---------------------+------------------------+
                        [ SECURITY WRAPPER ]
                    (PCI DSS Level 1 / AES-256)
```

### 2.4 Data Flow and Synchronization
To achieve real-time collaboration, Meridian employs a combination of SignalR for WebSocket communication and Azure Service Bus for asynchronous state propagation. When a user modifies a collaborative element, the request hits an Azure Function, which validates the action against the Domain Core, updates the Azure SQL database, and broadcasts the change via SignalR to all connected clients in that tenant's scope.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**  
Meridian requires a rigorous authentication and authorization framework that integrates with Verdant Labs' existing corporate identity provider while supporting external partner identities. Because the system handles credit card data (PCI DSS), the authentication layer must enforce Multi-Factor Authentication (MFA) and strict session timeouts.

**Detailed Specifications:**
- **Identity Integration:** Integration with Azure AD via OpenID Connect (OIDC).
- **RBAC Model:** A granular permission system consisting of four primary roles: `GlobalAdmin`, `TenantAdmin`, `Editor`, and `Viewer`. 
- **Permission Mapping:** Permissions are not assigned directly to users but to roles. A `Viewer` can read assets and comments but cannot trigger "Write" operations on the database. An `Editor` can modify assets but cannot manage user invites.
- **Session Management:** Implementation of JWT (JSON Web Tokens) with a maximum lifetime of 1 hour, utilizing sliding expiration via refresh tokens stored in an encrypted Azure Cache for Redis.
- **Audit Logging:** Every authentication attempt, password change, and privilege escalation must be logged to an immutable Azure Log Analytics workspace for compliance auditing.

**Acceptance Criteria:**
- Users cannot access any API endpoint without a valid, non-expired JWT.
- Attempting to access a `TenantAdmin` endpoint with a `Viewer` token results in a `403 Forbidden` response.
- MFA is mandatory for all accounts with `GlobalAdmin` or `TenantAdmin` privileges.

---

### 3.2 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Medium | **Status:** In Design

**Description:**  
With millions of media assets, users need a way to locate content instantly. The search feature must go beyond simple keyword matching, providing "faceted" filters (e.g., Filter by Date, Resolution, Production Phase, or Director) and full-text indexing for script and metadata searches.

**Detailed Specifications:**
- **Indexing Engine:** Use of Azure Cognitive Search to index metadata stored in Azure SQL.
- **Faceted Filtering:** The system will generate dynamic facets based on the current search result set. If a search for "Desert Scene" returns 100 clips, the facets will show counts for "4K" (60), "1080p" (30), and "ProRes" (10).
- **Full-Text Indexing:** Implementation of N-gram tokenization to allow for "fuzzy" searching, ensuring that a search for "Screne" still returns results for "Scene."
- **Performance Target:** Search queries must return results in under 200ms for result sets up to 10,000 items.
- **Query Syntax:** Support for Boolean operators (AND, OR, NOT) and wildcard searches (e.g., `prod_2024_*`).

**Acceptance Criteria:**
- Users can refine search results using at least three different facets simultaneously.
- Full-text search identifies keywords within the "Description" and "Notes" fields of the media asset table.
- Search results are paginated with a default of 50 records per page.

---

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Description:**  
The dashboard serves as the landing page for users. To accommodate different roles (e.g., a Producer needs a budget overview, while an Editor needs a timeline of pending reviews), the dashboard must be customizable via a drag-and-drop interface.

**Detailed Specifications:**
- **Widget Library:** A set of predefined widgets including "Recent Assets," "Pending Approvals," "Team Activity Feed," and "Storage Quota."
- **Persistence Layer:** Dashboard layouts are stored as JSON blobs in the `UserPreferences` table, mapped to the `UserID`.
- **Layout Engine:** Use of a grid-based system (e.g., Gridstack.js or similar) to allow users to resize and reposition widgets.
- **Real-time Updates:** Widgets must utilize SignalR to update their internal state without requiring a full page refresh.
- **Default Profiles:** The system provides "Role-Based Templates" so new users start with a layout optimized for their specific job function.

**Acceptance Criteria:**
- Users can move a widget from the left column to the right column and have that position persist after a logout/login cycle.
- Users can add or remove widgets from the dashboard using a "Widget Gallery" menu.
- Dashboard loading time does not exceed 1.5 seconds.

---

### 3.4 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**  
To support external partners and different internal departments, Meridian employs a "Shared Database, Separate Schema" (or Row-Level Security) approach. This ensures that Tenant A cannot see, modify, or even know the existence of Tenant B's data, despite sharing the same Azure SQL instance.

**Detailed Specifications:**
- **Tenant Identification:** Every request must include a `TenantId` header or be derived from the user's JWT claim.
- **Row-Level Security (RLS):** Implementation of Azure SQL Row-Level Security policies. A security predicate function is applied to every table, ensuring that the `WHERE TenantId = @CurrentTenant` filter is applied at the database engine level, not just the application level.
- **Cross-Tenant Leakage Prevention:** All database queries must go through the `TenantContext` provider in the C# backend, which injects the `TenantId` into every EF Core query.
- **Infrastructure Sharing:** To optimize costs, all tenants share the same Azure Function App and API Gateway, but data is logically isolated.
- **Tenant Provisioning:** An automated workflow for creating new tenants, which includes creating the tenant record and assigning an initial `TenantAdmin`.

**Acceptance Criteria:**
- A user from Tenant A attempting to access a resource via a direct URL (`/api/assets/123` where 123 belongs to Tenant B) receives a `404 Not Found` (to prevent enumeration) or `403 Forbidden`.
- Automated tests confirm that zero records are leaked across tenant boundaries during high-concurrency stress tests.

---

### 3.5 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Design

**Description:**  
Meridian must handle massive media files. This feature encompasses the secure upload of files, an automated security scan to prevent malware infiltration, and a global distribution strategy to ensure low-latency playback for remote teams.

**Detailed Specifications:**
- **Upload Pipeline:** Implementation of "Chunked Uploads" to allow files up to 100GB. Files are uploaded to a temporary Azure Blob Storage "Landing Zone."
- **Virus Scanning:** An Azure Function is triggered upon file upload (`BlobTrigger`). This function integrates with a third-party API (e.g., Windows Defender or CrowdStrike) to scan the file.
- **Quarantine Logic:** If a file is flagged as malicious, it is immediately moved to a "Quarantine" container with restricted access, and the `TenantAdmin` is notified.
- **CDN Integration:** Once cleared, files are moved to the "Production" container and cached via Azure CDN. The system generates a "Signed URL" with a short expiration time for client access.
- **Checksum Verification:** The system computes an MD5/SHA-256 hash of the file both at the client side and the server side to ensure data integrity during transfer.

**Acceptance Criteria:**
- Files are not available for download until the virus scan returns a "Clean" status.
- Users in London can stream a file uploaded in Los Angeles with a latency under 500ms (via CDN edge nodes).
- Large files (over 2GB) are successfully uploaded using the chunking mechanism without timing out.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful principles and return JSON. Base URL: `https://api.meridian.verdantlabs.com/v1`

### 4.1 Authentication & User Management

**Endpoint:** `POST /auth/login`  
**Description:** Authenticates user and returns JWT.  
**Request:**  
```json
{
  "username": "g.fischer@verdantlabs.com",
  "password": "hashed_password_here",
  "mfa_code": "123456"
}
```
**Response:** `200 OK`  
```json
{
  "token": "eyJhbG...",
  "expires_in": 3600,
  "user_id": "USR-9982"
}
```

**Endpoint:** `GET /users/profile`  
**Description:** Retrieves current user profile and role.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:** `200 OK`  
```json
{
  "user_id": "USR-9982",
  "full_name": "Greta Fischer",
  "role": "GlobalAdmin",
  "tenant_id": "TEN-001"
}
```

### 4.2 Asset Management

**Endpoint:** `POST /assets/upload`  
**Description:** Initiates a chunked upload session.  
**Request:**  
```json
{
  "file_name": "Scene_01_Take_04.mov",
  "file_size": 536870912,
  "mime_type": "video/quicktime"
}
```
**Response:** `201 Created`  
```json
{
  "upload_id": "UP-55432",
  "upload_url": "https://upload.meridian.com/chunks/UP-55432"
}
```

**Endpoint:** `GET /assets/search`  
**Description:** Performs faceted search on media assets.  
**Request:** `GET /assets/search?q=desert&resolution=4k&status=approved`  
**Response:** `200 OK`  
```json
{
  "results": [
    { "id": "AST-101", "name": "Desert_Wide.mov", "url": "https://cdn.meridian.com/ast101" }
  ],
  "facets": {
    "resolution": { "4k": 12, "1080p": 45 },
    "status": { "approved": 10, "pending": 5 }
  }
}
```

### 4.3 Collaboration & Dashboard

**Endpoint:** `GET /dashboard/layout`  
**Description:** Retrieves the user's custom dashboard configuration.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:** `200 OK`  
```json
{
  "layout_id": "LYT-882",
  "widgets": [
    { "type": "RecentAssets", "x": 0, "y": 0, "w": 4, "h": 2 },
    { "type": "TeamActivity", "x": 4, "y": 0, "w": 4, "h": 4 }
  ]
}
```

**Endpoint:** `PUT /dashboard/layout`  
**Description:** Updates the dashboard layout.  
**Request:**  
```json
{
  "widgets": [
    { "type": "RecentAssets", "x": 0, "y": 0, "w": 6, "h": 2 }
  ]
}
```
**Response:** `204 No Content`

### 4.4 Tenant & Billing (PCI DSS Scope)

**Endpoint:** `POST /billing/payment-method`  
**Description:** Securely stores a payment method for a tenant.  
**Request:**  
```json
{
  "payment_token": "tok_visa_12345",
  "billing_email": "billing@partner-studio.com"
}
```
**Response:** `201 Created`  
```json
{
  "status": "success",
  "payment_method_id": "PM_9912"
}
```

**Endpoint:** `GET /tenant/config`  
**Description:** Retrieves tenant-specific settings and quotas.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:** `200 OK`  
```json
{
  "tenant_id": "TEN-001",
  "storage_limit_gb": 10000,
  "used_storage_gb": 4500,
  "feature_flags": { "advanced_search": true, "custom_dash": false }
}
```

---

## 5. DATABASE SCHEMA

The Meridian database is hosted on Azure SQL. The schema is designed to support multi-tenancy via the `TenantId` column present in every entity.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` | N/A | `TenantName`, `SubscriptionLevel`, `CreatedAt` | Top-level entity for multi-tenancy. |
| `Users` | `UserId` | `TenantId` | `Username`, `Email`, `PasswordHash`, `Role` | User credentials and role mapping. |
| `Roles` | `RoleId` | N/A | `RoleName`, `PermissionSet` | Definitions of RBAC roles. |
| `Permissions` | `PermId` | N/A | `PermissionKey`, `Description` | Individual granular permissions. |
| `Assets` | `AssetId` | `TenantId`, `UserId` | `FileName`, `FileUrl`, `FileSize`, `MimeType` | Metadata for uploaded media files. |
| `AssetTags` | `TagId` | `AssetId` | `TagName`, `TagCategory` | Faceted tags for search indexing. |
| `UserPreferences`| `PrefId` | `UserId` | `DashboardJson`, `Theme`, `Language` | Stores UI customizability data. |
| `AuditLogs` | `LogId` | `UserId`, `TenantId`| `Action`, `Timestamp`, `IpAddress` | Immutable log for security compliance. |
| `PaymentMethods`| `PaymentId` | `TenantId` | `ProviderToken`, `Last4`, `ExpiryDate` | PCI-compliant tokenized payment data. |
| `Collaborations`| `CollabId` | `TenantId` | `SessionId`, `StartTime`, `EndTime` | Tracks real-time session metadata. |

### 5.2 Relationships
- **Tenants $\to$ Users:** One-to-Many. A tenant has many users; a user belongs to one tenant.
- **Users $\to$ UserPreferences:** One-to-One. Each user has exactly one preference profile.
- **Tenants $\to$ Assets:** One-to-Many. Assets are isolated by TenantId.
- **Assets $\to$ AssetTags:** One-to-Many. Each asset can have multiple tags for faceted search.
- **Users $\to$ AuditLogs:** One-to-Many. All user actions are logged for compliance.

### 5.3 Data Normalization Note
Due to existing technical debt, the system currently uses three different date formats (`ISO 8601`, `Unix Timestamp`, and `MM-DD-YYYY`) across the legacy data import scripts. A `DateNormalizationLayer` has been planned for the "Ports" section of the hexagonal architecture to ensure all internal domain logic uses `DateTimeOffset` (UTC).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Meridian utilizes a three-tier environment pipeline to ensure zero downtime and maximum stability.

**1. Development (Dev)**
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Azure SQL (Basic), Azure Functions (Consumption Plan), Azure App Service (B1).
- **Deployment:** Continuous Integration (CI) trigger on every commit to the `develop` branch.

**2. Staging (QA/UAT)**
- **Purpose:** Integration testing, security scanning, and stakeholder sign-off.
- **Infrastructure:** Mirrored production environment (Azure SQL Hyperscale, Premium Functions).
- **Deployment:** Triggered upon merge from `develop` to `release` branch. This environment is used for the Milestone 2 demos.

**3. Production (Prod)**
- **Purpose:** Live company operations and external partner access.
- **Infrastructure:** High-availability (HA) cluster across two Azure regions (East US and West US) for disaster recovery.
- **Deployment:** Quarterly releases. Deployments utilize **Blue-Green Deployment** (Traffic Manager) to ensure zero downtime. Traffic is shifted 10% $\to$ 50% $\to$ 100% after health checks pass.

### 6.2 CI/CD Pipeline
- **Tooling:** Azure DevOps Pipelines.
- **Build Stage:** .NET build $\to$ Unit Tests $\to$ SonarQube Code Analysis.
- **Security Stage:** OWASP Dependency-Check $\to$ Snyk Container Scan.
- **Release Stage:** Terraform for Infrastructure-as-Code (IaC) $\to$ Kudu deployment to App Service.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Domain Core and Application Services.
- **Framework:** xUnit with Moq for dependency isolation.
- **Target:** 80% code coverage.
- **Execution:** Every PR requires a successful unit test run before merging.

### 7.2 Integration Testing
- **Scope:** API Adapters $\to$ Database / Third-party APIs.
- **Approach:** Use of **Testcontainers** to spin up a temporary Azure SQL instance during the build process.
- **Focus:** Verifying that the Row-Level Security (RLS) correctly prevents cross-tenant data access.

### 7.3 End-to-End (E2E) Testing
- **Scope:** User Journeys (e.g., "Login $\to$ Upload File $\to$ Search Asset $\to$ Edit Dashboard").
- **Tooling:** Playwright.
- **Execution:** Run weekly in the Staging environment.

### 7.4 Security & Compliance Testing
- **Penetration Testing:** Semi-annual external pen-tests focusing on PCI DSS vulnerabilities.
- **Virus Scan Validation:** Uploading "EICAR" test files to ensure the Azure Function correctly flags and quarantines malicious content.
- **Load Testing:** Using Azure Load Testing to simulate 10x the current system's concurrent user capacity.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Integration partner's API is undocumented and buggy. | High | High | Build a "Fallback Adapter" layer. Use a Mock API for development to decouple from partner instability. |
| **R2** | Performance requirements 10x current system with no extra budget. | Medium | Critical | Engage external performance consultant for an independent assessment of Azure SQL Hyperscale tuning. |
| **R3** | PCI DSS audit failure due to legacy data remnants. | Low | High | Strict data scrubbing of the legacy DB before import; dedicated security review by Kenji Fischer. |
| **R4** | Legal delay on Data Processing Agreement (DPA). | High | Medium | **Current Blocker.** Project lead (Greta) is escalating to the Legal VP. Parallelize non-DPA dependent work. |
| **R5** | Technical debt (date formats) causing data corruption. | Medium | Medium | Implement a `NormalizationAdapter` at the infrastructure layer to force all dates to UTC. |

**Probability/Impact Matrix:**
- **Critical:** High Probability $\times$ High Impact (R1, R2) $\to$ Immediate Mitigation.
- **Major:** Low Probability $\times$ High Impact (R3) $\to$ Monitoring.
- **Moderate:** High Probability $\times$ Medium Impact (R4, R5) $\to$ Managed.

---

## 9. TIMELINE

The project is scheduled for a 6-month development cycle.

### 9.1 Phase Breakdown

**Phase 1: Foundation (Month 1-2)**
- Setup of Azure Infrastructure (IaC).
- Implementation of Multi-tenant Isolation (Completed).
- Development of RBAC and Auth systems (In Progress).
- *Dependency:* Legal review of DPA (Current Blocker).

**Phase 2: Core Features (Month 3-4)**
- Build out the Asset Management pipeline (Upload/Scan/CDN).
- Implementation of Advanced Search and Indexing.
- Integration with the partner API (R1 mitigation).
- **Milestone 1: Performance benchmarks met (Target: 2026-08-15).**

**Phase 3: Refinement & Integration (Month 5)**
- Dashboard widget implementation (Low priority).
- Legacy data migration (Normalization layer).
- **Milestone 2: Stakeholder demo and sign-off (Target: 2026-10-15).**

**Phase 4: Hardening & Launch (Month 6)**
- Final security audit and PCI DSS validation.
- Blue-Green deployment to Production.
- **Milestone 3: Security audit passed (Target: 2026-12-15).**

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project style, no formal minutes are kept. The following are distilled from the `#meridian-dev` Slack channel.*

### Meeting/Thread 1: The "Zero Downtime" Strategy
**Date:** 2025-11-02
**Participants:** Greta Fischer, Umi Oduya, Kenji Fischer
**Discussion:**
- **Umi:** "If we do a hard cutover, we risk 4 hours of downtime. The legacy system is too fragile for a fast migration."
- **Greta:** "Downtime is not an option. We need a side-by-side approach."
- **Decision:** Implement a "Shadow Write" phase. For 30 days, the legacy system will continue as the primary, but all writes will be mirrored to Meridian. We will compare the data sets before flipping the read-switch.

### Meeting/Thread 2: The Date Format Nightmare
**Date:** 2025-11-15
**Participants:** Umi Oduya, Zev Moreau
**Discussion:**
- **Zev:** "I found three different date formats in the legacy SQL dumps. Some are `YYYY-MM-DD`, some are Unix epochs, and some are weird regional strings."
- **Umi:** "We can't let that hit the Domain Core. It'll break every calculation we have."
- **Decision:** Zev to build a `DateNormalizationService` in the Infrastructure layer. All incoming legacy data must be converted to `DateTimeOffset` before it reaches the Application Service.

### Meeting/Thread 3: Partner API Instability
**Date:** 2025-12-01
**Participants:** Greta Fischer, Kenji Fischer, Umi Oduya
**Discussion:**
- **Umi:** "The partner API is returning 500s for 15% of requests, and the documentation is two years out of date."
- **Kenji:** "From a security perspective, their error messages are leaking stack traces. We can't trust their endpoint directly."
- **Decision:** Build a "Circuit Breaker" using the Polly library. If the partner API fails more than 3 times in a row, the system will switch to a cached "Graceful Degradation" mode.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Salaries for Greta, Umi, Kenji, Zev, and 2 QA Engineers (6 months). |
| **Infrastructure** | 15% | $120,000 | Azure SQL Hyperscale, Azure Functions, CDN, and Front Door costs. |
| **Tools & Licensing** | 10% | $80,000 | Snyk, SonarQube, Azure DevOps, and External Security Audit fees. |
| **Contingency** | 10% | $80,000 | Reserved for external performance consultant (R2) and partner API fixes. |

**Personnel Cost Detail:**
- Lead/Senior levels: Average $12k/mo per head.
- Junior levels: Average $8k/mo per head.
- Total personnel cost calculated over a 6-month build + 1 month stabilization.

---

## 12. APPENDICES

### Appendix A: PCI DSS Compliance Checklist
To maintain Level 1 compliance, Meridian must adhere to the following technical controls:
1.  **Encryption at Rest:** All credit card tokens and PII in Azure SQL are encrypted using Transparent Data Encryption (TDE) with customer-managed keys in Azure Key Vault.
2.  **Encryption in Transit:** All traffic is forced over TLS 1.2+; SSL 3.0 and TLS 1.0/1.1 are disabled at the Azure Front Door level.
3.  **Network Segmentation:** The payment processing logic is isolated in a separate Azure VNet, with strict Network Security Group (NSG) rules allowing only necessary traffic.
4.  **Access Control:** Administrative access to the production environment requires a "Jump Box" with MFA and just-in-time (JIT) access.

### Appendix B: Performance Benchmark Targets
The following metrics must be met by 2026-08-15 to satisfy Milestone 1:
- **Concurrent Users:** Support 5,000 simultaneous active sessions without latency degradation.
- **Asset Retrieval:** Average time to first byte (TTFB) for 1GB files via CDN should be $< 100\text{ms}$.
- **API Response Time:** $95\text{th}$ percentile for all GET requests must be $< 250\text{ms}$.
- **Database Throughput:** Ability to handle 2,000 transactions per second (TPS) during peak production hours without locking the `Assets` table.