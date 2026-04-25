# PROJECT SPECIFICATION DOCUMENT: PROJECT LATTICE
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 24, 2023  
**Company:** Clearpoint Digital  
**Classification:** Internal/Confidential  

---

## 1. EXECUTIVE SUMMARY

**Project Lattice** represents a mission-critical strategic pivot for Clearpoint Digital. The project is a comprehensive rebuild of the existing cybersecurity monitoring dashboard, specifically tailored for the healthcare industry. This initiative was catalyzed by catastrophic user feedback regarding the legacy system, which was cited by key healthcare providers as unintuitive, slow, and failing to provide the real-time visibility required to maintain patient data safety and HIPAA-adjacent security postures.

The healthcare sector is currently experiencing an unprecedented surge in ransomware and data exfiltration attacks. For Clearpoint Digital, the legacy dashboard had become a liability; churn rates were increasing as customers found the interface cumbersome and the reporting capabilities insufficient for compliance auditing. Lattice is not merely a UI refresh but a foundational architectural overhaul designed to move the product from a monolithic, fragile state to a scalable, serverless, and data-driven ecosystem.

**Business Justification**
The primary business driver is customer retention and market expansion. By delivering a high-performance, modern dashboard, Clearpoint Digital aims to recapture the trust of its flagship healthcare accounts and attract new enterprise-level medical groups. The shift to a serverless architecture using Azure Functions is designed to drastically reduce the operational overhead associated with idling servers, moving the cost model from a fixed capital expenditure to a variable operational expenditure.

**ROI Projection**
With a budget exceeding $5 million, the board expects a return on investment (ROI) based on three primary levers:
1. **Churn Reduction:** A projected 25% decrease in customer attrition by improving the Net Promoter Score (NPS) from -12 to +40.
2. **Operational Efficiency:** A targeted 35% reduction in cost per transaction compared to the legacy system, achieved through the migration to Azure Functions and optimized Azure SQL indexing.
3. **Market Expansion:** The ability to onboard larger tenants (10,000+ endpoints) who were previously unable to use the legacy system due to performance bottlenecks.

The financial success of Lattice is tied directly to the "Production Launch" milestone on May 15, 2025. Failure to meet this date risks further loss of market share to emerging cybersecurity startups.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Overview
Project Lattice is built on a full Microsoft stack, utilizing a serverless-first approach to ensure elasticity and high availability. The core logic is decoupled into independent Azure Functions, orchestrated by an Azure API Management (APIM) gateway.

### 2.2 Architectural Component Stack
- **Frontend:** React 18 (TypeScript) hosted via Azure Static Web Apps.
- **API Layer:** Azure API Management (APIM) acting as the single entry point.
- **Compute:** C#/.NET 8 Azure Functions (Isolated Worker Process).
- **Database:** Azure SQL Database (Hyperscale tier) for relational data and audit logs.
- **Configuration/Feature Management:** LaunchDarkly for real-time toggle management and A/B testing.
- **Security:** Quarterly third-party penetration testing; Managed Identities for all service-to-service communication.

### 2.3 ASCII Architecture Diagram
```text
[ User Browser ] <--> [ Azure Static Web Apps ]
                             |
                             v
                  [ Azure API Management (APIM) ]
                             |
        _____________________|_____________________
       |                     |                     |
[ Auth Function ]    [ Monitoring Function ] [ Reporting Function ]
       |                     |                     |
       |_____________________|_____________________|
                             |
                             v
                  [ Azure SQL Database (Hyperscale) ]
                             |
                  [ Azure Blob Storage (PDF/CSV) ]
```

### 2.4 Data Flow and Orchestration
When a user requests a dashboard update, the request hits the APIM gateway, which handles rate limiting and authentication. The request is routed to the `Monitoring Function`. This function queries the Azure SQL database using optimized stored procedures. Because the project utilizes serverless functions, scaling is automatic based on the request volume, preventing the "freeze" experienced in the legacy system during peak healthcare reporting cycles.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Priority: Critical | Status: In Review)
**Description:** 
Lattice requires a built-in A/B testing framework integrated directly into the feature flag system. This allows the product team to roll out new dashboard widgets to a subset of users (e.g., 10% of healthcare providers) to measure engagement and performance before a full rollout.

**Detailed Requirements:**
- **Integration with LaunchDarkly:** The framework must leverage LaunchDarkly’s targeting rules. The C# backend must be able to pass user context (TenantID, UserRole, Region) to LaunchDarkly to determine which variant a user sees.
- **Metric Tracking:** Each A/B test must be tied to a specific telemetry event. If "Variant B" of the security alert widget is shown, the system must log the click-through rate (CTR) and the time-to-action (TTA).
- **Automated Rollback:** If the error rate for a specific variant exceeds 2%, the system must trigger an automatic flag flip to the "Control" version.
- **Client-Side Implementation:** The React frontend must handle the conditional rendering of components based on the flag value received from the `ConfigFunction`.

**Success Criteria:** Ability to deploy a UI change to 5% of the user base and analyze the impact on the "Time to Detect" (TTD) metric within 48 hours.

### 3.2 Multi-Tenant Data Isolation (Priority: Low | Status: In Design)
**Description:** 
To support a diverse range of healthcare providers, Lattice must ensure that data from one hospital system is never visible to another, despite sharing the same underlying Azure SQL infrastructure.

**Detailed Requirements:**
- **Row-Level Security (RLS):** Implementation of Azure SQL Row-Level Security. Every table must contain a `TenantId` column. The database session context must be set upon every connection to filter results automatically.
- **Tenant Validation:** The `AuthFunction` must validate the user's `TenantId` against the JWT (JSON Web Token) and pass this ID as a header to downstream functions.
- **Shared Infrastructure:** To maintain cost efficiency, a "Shared Schema" approach is used rather than a "Database-per-Tenant" approach, necessitating rigorous testing of the RLS predicates.
- **Cross-Tenant Leakage Testing:** Quarterly automated scripts must attempt to query data using an invalid `TenantId` to ensure the API returns a 403 Forbidden.

**Success Criteria:** Zero instances of cross-tenant data leakage during the quarterly penetration tests.

### 3.3 PDF/CSV Report Generation (Priority: Critical | Status: Blocked)
**Description:** 
Healthcare administrators require scheduled, tamper-proof reports for compliance audits. These reports must be generated as PDFs or CSVs and delivered via email or stored in a secure portal.

**Detailed Requirements:**
- **Scheduling Engine:** An Azure Function triggered by a Timer Trigger (Cron job) that identifies which reports are due for delivery.
- **Asynchronous Processing:** Because report generation for 10,000+ endpoints is resource-intensive, the system must use an Azure Queue Storage pattern. The `ReportingFunction` will drop a message into a queue, and a background worker will process the PDF.
- **Template Engine:** Use of a .NET PDF library (e.g., QuestPDF) to generate branded reports including security posture summaries, incident counts, and resolution times.
- **Delivery Mechanism:** Integration with SendGrid for email delivery, containing a secure, time-limited link to the report stored in Azure Blob Storage (with SAS tokens).

**Current Blocker:** The reporting engine is currently unable to fetch the necessary telemetry data due to third-party API rate limits during the testing phase, preventing the generation of a full report.

**Success Criteria:** Ability to generate a 50-page PDF report for a tenant with 5,000 endpoints in under 60 seconds.

### 3.4 Audit Trail Logging (Priority: Medium | Status: Blocked)
**Description:** 
Every administrative action within the Lattice dashboard (e.g., changing a security threshold, adding a user) must be logged in a tamper-evident audit trail.

**Detailed Requirements:**
- **Immutable Storage:** Logs must be written to an Azure SQL table with a "Write-Once-Read-Many" (WORM) philosophy.
- **Hashing:** Each log entry must contain a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody to ensure that logs have not been deleted or altered.
- **Capture Scope:** Every `POST`, `PUT`, and `DELETE` request must trigger a log entry containing: UserID, Timestamp, IP Address, Action, Old Value, and New Value.
- **Retrieval API:** A dedicated endpoint for auditors to export the audit trail for a specific time range.

**Current Blocker:** The team has identified that the current database write speeds are too slow to handle the volume of audit logs without impacting the main dashboard performance.

**Success Criteria:** A verified audit trail where any modification to a historical log entry is detectable via hash mismatch.

### 3.5 Customer-Facing API (Priority: Low | Status: In Progress)
**Description:** 
To allow healthcare providers to integrate Lattice data into their own internal dashboards, a versioned public API is required.

**Detailed Requirements:**
- **Versioning:** The API must follow semantic versioning in the URL path (e.g., `/api/v1/alerts`).
- **Sandbox Environment:** A separate "Sandbox" Azure Function App and Database instance where customers can test their integrations without affecting production data.
- **API Key Management:** A system for customers to generate and rotate their own API keys, with the ability to set IP whitelists.
- **Documentation:** An automated Swagger/OpenAPI specification page accessible to authenticated developers.

**Success Criteria:** A developer can successfully authenticate and retrieve a list of security alerts in the sandbox environment within 15 minutes of receiving an API key.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `https://api.lattice.clearpoint.com`.

### 4.1 GET /v1/dashboard/summary
- **Description:** Retrieves a high-level overview of security posture.
- **Request Headers:** `Authorization: Bearer <token>`, `X-Tenant-Id: <id>`
- **Response (200 OK):**
  ```json
  {
    "total_alerts": 142,
    "critical_issues": 12,
    "system_health": "stable",
    "last_updated": "2025-01-10T14:30:00Z"
  }
  ```

### 4.2 GET /v1/alerts
- **Description:** Fetches a paginated list of security alerts.
- **Query Params:** `page=1`, `pageSize=50`, `severity=critical`
- **Response (200 OK):**
  ```json
  {
    "data": [
      { "id": "ALRT-992", "type": "Unauthorized Access", "severity": "critical", "timestamp": "2025-01-10T12:00:00Z" }
    ],
    "pagination": { "total": 142, "pages": 3 }
  }
  ```

### 4.3 POST /v1/alerts/{id}/resolve
- **Description:** Marks a specific alert as resolved.
- **Request Body:**
  ```json
  { "resolution_note": "False positive; patched firewall rule.", "resolved_by": "user_123" }
  ```
- **Response (200 OK):** `{ "status": "resolved", "updated_at": "2025-01-10T15:00:00Z" }`

### 4.4 POST /v1/reports/generate
- **Description:** Triggers a manual PDF report generation.
- **Request Body:** `{ "report_type": "compliance_monthly", "format": "pdf", "tenant_id": "T-882" }`
- **Response (202 Accepted):** `{ "job_id": "job_abc_123", "status": "queued" }`

### 4.5 GET /v1/reports/status/{job_id}
- **Description:** Checks the status of a report generation job.
- **Response (200 OK):** `{ "job_id": "job_abc_123", "status": "completed", "download_url": "https://storage.clearpoint.com/report.pdf?token=xyz" }`

### 4.6 GET /v1/audit/logs
- **Description:** Retrieves the audit trail for the tenant.
- **Query Params:** `startDate=2025-01-01`, `endDate=2025-01-10`
- **Response (200 OK):**
  ```json
  [
    { "timestamp": "2025-01-01T08:00:00Z", "user": "admin_1", "action": "UPDATE_THRESHOLD", "diff": "from 10 to 20" }
  ]
  ```

### 4.7 GET /v1/config/flags
- **Description:** Returns the current active feature flags for the user session (used by React frontend).
- **Response (200 OK):** `{ "new_dashboard_layout": true, "beta_reporting": false }`

### 4.8 POST /v1/sandbox/test-connection
- **Description:** Validates API key and connectivity in the sandbox environment.
- **Request Headers:** `X-API-Key: <sandbox_key>`
- **Response (200 OK):** `{ "status": "connected", "environment": "sandbox" }`

---

## 5. DATABASE SCHEMA

The database is an Azure SQL Hyperscale instance. All tables use `BIGINT` for primary keys and `datetimeoffset` for timestamps to ensure global timezone consistency.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` | None | `TenantName`, `Industry`, `CreatedAt` | Master tenant record |
| `Users` | `UserId` | `TenantId` | `Email`, `PasswordHash`, `Role` | User account and role mapping |
| `SecurityAlerts` | `AlertId` | `TenantId` | `Severity`, `AlertType`, `Status` | Core monitoring data |
| `AlertDetails` | `DetailId` | `AlertId` | `RawPayload`, `SourceIp`, `DestinationIp` | Verbose alert metadata |
| `AuditLogs` | `LogId` | `TenantId`, `UserId` | `Action`, `PreviousHash`, `NewHash` | Tamper-evident audit trail |
| `Reports` | `ReportId` | `TenantId` | `ReportType`, `BlobUrl`, `ScheduledDate` | Metadata for generated reports |
| `ReportSchedules` | `ScheduleId` | `TenantId` | `CronExpression`, `Format` (PDF/CSV) | Recurring report settings |
| `FeatureFlags` | `FlagId` | None | `FlagKey`, `DefaultValue`, `IsActive` | Internal flag mapping |
| `UserSessions` | `SessionId` | `UserId` | `Token`, `ExpiryDate`, `IpAddress` | Active session tracking |
| `ApiKeys` | `KeyId` | `UserId` | `KeyHash`, `Environment` (Prod/Sandbox) | API access credentials |

**Relationships:**
- `Tenants` $\rightarrow$ `Users` (1:N)
- `Tenants` $\rightarrow$ `SecurityAlerts` (1:N)
- `SecurityAlerts` $\rightarrow$ `AlertDetails` (1:1)
- `Users` $\rightarrow$ `AuditLogs` (1:N)
- `Tenants` $\rightarrow$ `Reports` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lattice utilizes a three-tier environment strategy to ensure stability and security.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and unit testing.
- **Infrastructure:** Shared Azure Function App (Consumption Plan), Azure SQL (Basic Tier).
- **Deployment:** Automatic deploy from `develop` branch on GitHub.
- **Data:** Mock data and anonymized subsets of production data.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation, UAT, and penetration testing.
- **Infrastructure:** Mirrored Production setup (Premium Plan) to ensure performance parity.
- **Deployment:** Manual trigger from `release` branch.
- **Data:** Full-scale synthetic datasets.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Infrastructure:** Azure Function App (Premium Plan), Azure SQL (Hyperscale), APIM.
- **Deployment:** Canary releases managed via LaunchDarkly and GitHub Actions.
- **Data:** Live healthcare tenant data.

### 6.2 Release Process
We employ **Canary Releases**. A new version of a function is deployed to a "Canary" slot. Using LaunchDarkly, 5% of traffic is routed to the new version. If telemetry shows no increase in 5xx errors, the traffic is ramped up to 25%, 50%, and finally 100%.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Coverage Target:** 80% line coverage for all business logic in Azure Functions.
- **Focus:** Validation logic, data transformation, and edge-case handling for the reporting engine.

### 7.2 Integration Testing
- **Framework:** Postman / Newman.
- **Focus:** Verifying the flow between APIM, Azure Functions, and Azure SQL.
- **Schedules:** Automated runs every 4 hours in the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Focus:** Critical user journeys (e.g., "User logs in $\rightarrow$ views critical alert $\rightarrow$ marks as resolved $\rightarrow$ generates report").
- **Environment:** Executed against Staging before every production release.

### 7.4 Security Testing
- **Penetration Testing:** Conducted quarterly by an external firm.
- **Static Analysis:** SonarQube integrated into the CI/CD pipeline to catch common vulnerabilities (OWASP Top 10).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor is about to rotate out of their role | High | High | Accept the risk; monitor weekly and ensure secondary sign-off from VP of Product. |
| R-02 | Regulatory requirements for healthcare may change | Medium | High | Assign dedicated owner (Compliance Officer) to track changes and update requirements. |
| R-03 | Third-party API rate limits blocking testing | High | Medium | Implement a local mock server for API responses to unblock development. |
| R-04 | Technical debt: Lack of structured logging | High | Medium | Implement Serilog with Azure Application Insights to replace `stdout` logging. |
| R-05 | Distributed team coordination lag | Medium | Low | Maintain async standups and strict adherence to Jira ticket documentation. |

**Impact Matrix:**
- **High:** Potential project delay $>1$ month or budget overage $>10\%$.
- **Medium:** Feature delay or performance degradation.
- **Low:** Minor UI bugs or documentation gaps.

---

## 9. TIMELINE

### 9.1 Phases and Dependencies

**Phase 1: Foundation & Core API (Oct 2023 - Feb 2024)**
- Establish Azure infrastructure and SQL Schema.
- Implement `AuthFunction` and `MonitoringFunction`.
- *Dependency:* Database schema must be finalized before API development.

**Phase 2: Feature Implementation (Mar 2024 - Dec 2024)**
- Develop A/B Testing framework (Critical).
- Develop Report Generation (Critical - currently blocked).
- Implement Multi-tenant isolation.
- *Dependency:* Feature flag system must be stable before A/B testing implementation.

**Phase 3: Stabilization & Audit (Jan 2025 - May 2025)**
- Full E2E testing.
- Fix technical debt (structured logging).
- Final UAT with selected healthcare clients.
- **Milestone 1: Production Launch (2025-05-15)**

**Phase 4: Post-Launch Validation (May 2025 - Sept 2025)**
- **Milestone 2: Security Audit Passed (2025-07-15)**
- Performance tuning for cost per transaction.
- **Milestone 3: Stability Confirmed (2025-09-15)**

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Per team culture, recordings are archived but rarely rewatched. Notes below are the condensed takeaways from the transcripts.*

### Meeting 1: Architectural Review (Nov 12, 2023)
- **Attendees:** Suki Costa, Xena Kim, Ibrahim Oduya
- **Discussion:** Xena raised concerns about the "shared infrastructure" for multi-tenancy. She argued that a database-per-tenant would be safer. Suki overruled, citing the $5M budget constraints and the need to reduce cost per transaction by 35%.
- **Decision:** Stick with Azure SQL Hyperscale and implement Row-Level Security (RLS).
- **Action Item:** Xena to provide a POC of RLS by next Friday.

### Meeting 2: Feature Priority Sync (Jan 15, 2024)
- **Attendees:** Suki Costa, Xiomara Kim, Ibrahim Oduya
- **Discussion:** Ibrahim presented the new UI mockups. Xiomara noted that the PDF report generation is currently blocked because the third-party security API is rate-limiting the Dev environment. Suki emphasized that reports are a "launch blocker."
- **Decision:** Xiomara to build a "Mock API" to simulate data so the PDF layout can be finalized while the rate-limit issue is negotiated with the vendor.
- **Action Item:** Xiomara to implement the Mock API by Jan 20.

### Meeting 3: Risk Management Call (Mar 05, 2024)
- **Attendees:** Suki Costa, Team
- **Discussion:** Suki informed the team that the project sponsor is rotating out. The team expressed concern about budget stability. Suki confirmed that the board has already earmarked the $5M+ and the rotation will not affect funding.
- **Decision:** The risk is accepted. Suki will maintain weekly updates to the board to ensure continuity.
- **Action Item:** Suki to set up a monthly board reporting cadence.

---

## 11. BUDGET BREAKDOWN

Total Budget: $5,000,000+

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | Distributed team of 15 (Developers, Designers, Data Engineers) over 24 months. |
| **Infrastructure** | $800,000 | Azure Hyperscale SQL, Function App Premium, APIM, Blob Storage. |
| **Tools & Licenses** | $300,000 | LaunchDarkly (Enterprise), GitHub Enterprise, SendGrid, SonarQube. |
| **Security Audits** | $200,000 | Quarterly external penetration tests and final certification. |
| **Contingency** | $500,000 | Reserve for regulatory changes or extended development cycles. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The legacy system's lack of structured logging has migrated into the early versions of Lattice. Currently, developers rely on `Console.WriteLine` (stdout), which makes debugging production issues in Azure Functions an arduous process of searching through the Log Stream.
- **Proposed Fix:** Transition all functions to use `ILogger` with a Serilog provider, pushing logs to Azure Application Insights. This will allow for KQL (Kusto Query Language) queries to isolate tenant-specific errors.

### Appendix B: Data Retention Policy
Given the healthcare industry context, Lattice will implement the following data retention rules:
- **Security Alerts:** Retained for 7 years (Compliance requirement).
- **Audit Logs:** Retained for 10 years; moved to "Cold" Azure Blob Storage after 2 years.
- **Sandbox Data:** Wiped every 30 days to maintain environment cleanliness.
- **User Sessions:** Expire after 8 hours of inactivity.