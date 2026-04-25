# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Date:** October 24, 2024  
**Status:** Finalized / Baseline  
**Project Owner:** Iron Bay Technologies  
**Lead Authority:** Darian Santos (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Glacier is a strategic cost-reduction and operational consolidation initiative undertaken by Iron Bay Technologies. Currently, the organization’s legal services payment arm relies on four disparate internal tools to handle transaction routing, client invoicing, escrow management, and trust account auditing. This fragmentation has led to significant operational overhead, data duplication, and a high risk of reconciliation errors.

The primary objective of Project Glacier is to collapse these four redundant systems into a single, unified fintech payment processing platform. By consolidating the tech stack and centralizing the data flow, Iron Bay Technologies aims to eliminate the maintenance costs associated with legacy systems and reduce the manual labor required for inter-tool data migration. Given the specialized nature of the legal services industry—where trust accounting and strict audit trails are mandatory—Glacier is designed to ensure that every cent is tracked from the moment of receipt to the moment of disbursement.

### 1.2 ROI Projection and Financial Goals
The budget for Project Glacier is set at a modest but workable $400,000. This allocation covers the development efforts of a 12-person cross-functional team over the course of the development cycle. 

The Return on Investment (ROI) for Project Glacier is calculated through two primary vectors:
1. **Operational Cost Savings:** The decommissioning of four legacy tools will reduce infrastructure overhead by an estimated $120,000 annually and reclaim approximately 1,500 man-hours of developer time previously spent on patching legacy code.
2. **Revenue Generation:** A key success metric for the project is the generation of $500,000 in new revenue attributed to the product within 12 months of the post-launch stability date (July 15, 2025). This revenue is expected to stem from the ability to offer more streamlined payment options to legal clients, reducing churn and increasing the adoption of automated billing services.

### 1.3 Strategic Alignment
Glacier aligns with the broader corporate goal of "Technical Simplification." By moving to a unified C#/.NET stack hosted on Azure, Iron Bay Technologies reduces its dependency on niche legacy scripts and moves toward a scalable, cloud-native architecture. Despite the pressure from a competitor who is currently two months ahead in a similar product build, the focus of Glacier is internal efficiency and precision, which will provide a more stable foundation for long-term growth.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: CQRS and Event Sourcing
Project Glacier utilizes Command Query Responsibility Segregation (CQRS) to separate the read and write operations of the system. In the context of legal payment processing, auditability is non-negotiable. Therefore, the system implements **Event Sourcing** for all audit-critical domains (e.g., Ledger, Escrow, Disbursement).

Instead of storing only the current state of a payment, Glacier stores every state change as a sequence of immutable events in an Event Store. This allows the system to reconstruct the state of any account at any point in time, providing an infallible audit trail.

### 2.2 Technology Stack
- **Language/Framework:** C# / .NET 8
- **Database:** Azure SQL Database (Relational storage for read models)
- **Event Store:** Azure Cosmos DB (for event streams)
- **Compute:** Azure Functions (Serverless triggers for event handlers)
- **Identity:** Azure Active Directory (integrated with SAML/OIDC)
- **Messaging:** Azure Service Bus (for asynchronous communication between commands and queries)

### 2.3 System Diagram (ASCII)
The following represents the data flow for a standard payment command:

```text
[ Client UI ] ----(Command: ProcessPayment)----> [ API Gateway ]
                                                       |
                                                       v
[ Event Store ] <---(Append Event)--- [ Command Handler (.NET 8) ]
      |                                                |
      | (Asynchronous Event Trigger)                   |
      v                                                v
[ Azure Function ] ----(Update Read Model)----> [ Azure SQL DB ]
      |                                                |
      +-------------------------------------------------+
                               |
                               v
[ Client UI ] <---(Query: GetPaymentStatus)--- [ Query Handler ]
```

### 2.4 Deployment Strategy: The Release Train
Glacier adheres to a strict **Weekly Release Train**. 
- **Deployment Cycle:** Every Tuesday at 03:00 UTC.
- **Cut-off:** All merged code must be in the `release` branch by Monday 12:00 UTC.
- **Strict Policy:** No exceptions. No hotfixes are permitted outside the release train. If a critical bug is discovered on Wednesday, it must be remediated and deployed on the following Tuesday. This ensures stability and prevents the "drift" typically associated with emergency patches in fintech environments.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Complete
*   **Description:** The dashboard serves as the primary interface for legal administrators to monitor payment flows. It allows users to visualize real-time liquidity, pending escrow payments, and daily transaction volumes.
*   **Functional Requirements:**
    - Users must be able to add/remove widgets from a predefined library (e.g., "Monthly Revenue Chart," "Pending Approvals List," "Client Debt Heatmap").
    - Widgets must be repositionable via a grid-based drag-and-drop system.
    - Layout preferences must be persisted in the database per user profile.
    - Each widget must support a "refresh" interval setting (1min, 5min, 1hr).
*   **Technical Implementation:** Implemented using a React-based frontend with a JSON-based layout schema stored in the `UserDashboardConfig` table. The backend provides a specialized `GET /api/dashboard/widgets` endpoint to populate the data for each widget based on the user's permissions.

### 3.2 A/B Testing Framework (Integrated with Feature Flags)
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Description:** To optimize the payment conversion rate for legal clients, Glacier requires a built-in A/B testing framework. This is not a separate tool but is baked directly into the feature flag system.
*   **Functional Requirements:**
    - The system must allow the Product Lead to define a "Treatment Group" and a "Control Group" for specific features.
    - Users must be randomly assigned to a group upon their first login session for a specific experiment.
    - The framework must support "Weighting" (e.g., 90% Control, 10% Treatment).
    - Telemetry must be automatically captured for each group to measure the success metric (e.g., time-to-payment completion).
*   **Technical Implementation:** Feature flags are managed via a `FeatureFlags` table. The logic will be implemented as a Middleware in .NET, which intercepts requests and injects the assigned group into the `UserContext` object.

### 3.3 SSO Integration (SAML and OIDC Providers)
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Review
*   **Description:** Because Iron Bay Technologies operates within the legal sector, security and identity management are paramount. Glacier must integrate with external identity providers (IdPs) using SAML 2.0 and OpenID Connect (OIDC).
*   **Functional Requirements:**
    - Support for Azure AD, Okta, and Ping Identity.
    - Implementation of Just-in-Time (JIT) provisioning, where a user account is created upon their first successful SSO login.
    - Role-based access control (RBAC) mapping where SAML assertions map to internal Glacier roles (e.g., `Lawyer`, `Accountant`, `Administrator`).
    - Single Logout (SLO) capability to ensure sessions are terminated across all integrated providers.
*   **Technical Implementation:** Utilizing the `Microsoft.AspNetCore.Authentication` library. The system will maintain a `SAMLConfiguration` table to store metadata XMLs and entity IDs for different legal firms using the system.

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
*   **Priority:** Critical (Launch Blocker)
*   **Status:** Not Started
*   **Description:** Legal auditing requires immutable snapshots of financial records. Glacier must generate comprehensive reports that can be delivered automatically to stakeholders.
*   **Functional Requirements:**
    - Reports include: Trust Account Statements, Monthly Transaction Logs, and Tax Compliance Summaries.
    - Users must be able to schedule reports (Daily, Weekly, Monthly) via a cron-style interface.
    - Delivery must be handled via secure email attachments or direct upload to a secure Azure Blob Storage container.
    - PDF exports must be non-editable and include a digital signature for authenticity.
*   **Technical Implementation:** Use of `QuestPDF` for high-performance PDF generation and `CsvHelper` for CSVs. The scheduling will be managed by an Azure Function Timer Trigger that queries the `ReportSchedules` table and triggers a background job in the `ReportProcessingQueue`.

### 3.5 Localization and Internationalization (L10n/I18n)
*   **Priority:** Low (Nice to Have)
*   **Status:** In Design
*   **Description:** To expand the service to international legal firms, the system must support 12 different languages and regional formatting for currency and dates.
*   **Functional Requirements:**
    - Support for 12 languages (English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, Dutch, Russian).
    - Dynamic currency switching based on the client's locale.
    - Date/Time formatting according to ISO 8601 but displayed in regional preferences (e.g., MM/DD/YYYY vs DD/MM/YYYY).
    - Support for Right-to-Left (RTL) layout for Arabic.
*   **Technical Implementation:** Use of `.resx` resource files in .NET and `i18next` on the frontend. A `UserLocale` table will store the preferred language and timezone for each user.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and require a Bearer Token in the Authorization header.

### 4.1 Payment Processing Endpoints

**1. POST `/api/v1/payments/initiate`**
- **Description:** Initializes a new payment request.
- **Request:**
  ```json
  {
    "clientId": "C-99283",
    "amount": 1250.00,
    "currency": "USD",
    "paymentMethod": "ACH",
    "referenceId": "INV-2024-001"
  }
  ```
- **Response (202 Accepted):**
  ```json
  {
    "transactionId": "TXN-8827110",
    "status": "Pending",
    "expiryDate": "2024-11-01T12:00:00Z"
  }
  ```

**2. GET `/api/v1/payments/{transactionId}/status`**
- **Description:** Retrieves the current status of a transaction.
- **Response (200 OK):**
  ```json
  {
    "transactionId": "TXN-8827110",
    "status": "Completed",
    "processedAt": "2024-10-25T09:15:00Z"
  }
  ```

**3. PATCH `/api/v1/payments/{transactionId}/void`**
- **Description:** Voids a pending transaction.
- **Response (200 OK):**
  ```json
  {
    "transactionId": "TXN-8827110",
    "status": "Voided",
    "voidReason": "Client Requested"
  }
  ```

### 4.2 Reporting and Dashboard Endpoints

**4. GET `/api/v1/reports/generate`**
- **Description:** Manually triggers the generation of a report.
- **Request Params:** `type=Monthly`, `format=PDF`, `startDate=2024-01-01`, `endDate=2024-01-31`
- **Response (201 Created):**
  ```json
  {
    "reportId": "REP-554",
    "downloadUrl": "https://blob.core.windows.net/glacier/reports/rep554.pdf"
  }
  ```

**5. GET `/api/v1/dashboard/widgets`**
- **Description:** Fetches the configuration for the user's custom dashboard.
- **Response (200 OK):**
  ```json
  {
    "userId": "U-101",
    "widgets": [
      { "id": "w1", "type": "RevenueChart", "position": { "x": 0, "y": 0, "w": 6, "h": 4 } },
      { "id": "w2", "type": "PendingList", "position": { "x": 6, "y": 0, "w": 6, "h": 4 } }
    ]
  }
  ```

### 4.3 Administration and Security Endpoints

**6. POST `/api/v1/auth/sso/callback`**
- **Description:** Handles the SAML/OIDC callback from the identity provider.
- **Request:** `SAMLResponse` or `AuthCode` as a POST body.
- **Response (200 OK):** JWT Token for session management.

**7. GET `/api/v1/flags/active`**
- **Description:** Returns all active feature flags and A/B test assignments for the current user.
- **Response (200 OK):**
  ```json
  {
    "flags": {
      "NewPaymentUI": "Treatment_B",
      "AdvancedReporting": "Enabled"
    }
  }
  ```

**8. DELETE `/api/v1/admin/config/flush`**
- **Description:** Clears the cached configuration values (used to resolve hardcoded value debt).
- **Response (204 No Content).**

---

## 5. DATABASE SCHEMA

Project Glacier utilizes a hybrid approach: Azure SQL for relational data (Read Models) and Cosmos DB for the Event Store. The following tables describe the Azure SQL schema.

### 5.1 Table Definitions

1.  **`Users`**
    - `UserId` (PK, Guid)
    - `Email` (Varchar 255, Unique)
    - `FullName` (Varchar 255)
    - `Role` (Enum: Admin, Accountant, Lawyer)
    - `CreatedAt` (DateTime)
2.  **`Clients`**
    - `ClientId` (PK, Guid)
    - `LegalFirmId` (FK, Guid)
    - `ClientName` (Varchar 255)
    - `TaxId` (Varchar 50)
    - `DefaultCurrency` (Char 3)
3.  **`Transactions`**
    - `TransactionId` (PK, Guid)
    - `Amount` (Decimal 18,2)
    - `Currency` (Char 3)
    - `Status` (Enum: Pending, Completed, Voided, Failed)
    - `ClientId` (FK, Guid)
    - `CreatedAt` (DateTime)
4.  **`LedgerEntries`**
    - `EntryId` (PK, BigInt)
    - `TransactionId` (FK, Guid)
    - `AccountType` (Enum: Trust, Operating, Escrow)
    - `DebitAmount` (Decimal 18,2)
    - `CreditAmount` (Decimal 18,2)
    - `Timestamp` (DateTime)
5.  **`UserDashboardConfig`**
    - `ConfigId` (PK, Guid)
    - `UserId` (FK, Guid)
    - `LayoutJson` (NVARCHAR(MAX))
    - `LastModified` (DateTime)
6.  **`FeatureFlags`**
    - `FlagKey` (PK, Varchar 50)
    - `IsActive` (Boolean)
    - `Variant` (Varchar 20) - Used for A/B testing (e.g., "Control", "Treatment")
    - `RolloutPercentage` (Int)
7.  **`SAMLConfiguration`**
    - `ConfigId` (PK, Guid)
    - `FirmId` (FK, Guid)
    - `IdpMetadataUrl` (Varchar 500)
    - `EntityId` (Varchar 255)
    - `SsoServiceUrl` (Varchar 500)
8.  **`ReportSchedules`**
    - `ScheduleId` (PK, Guid)
    - `UserId` (FK, Guid)
    - `ReportType` (Varchar 50)
    - `CronExpression` (Varchar 50)
    - `DeliveryMethod` (Enum: Email, Blob)
9.  **`AuditLogs`**
    - `LogId` (PK, BigInt)
    - `UserId` (FK, Guid)
    - `Action` (Varchar 100)
    - `OldValue` (Text)
    - `NewValue` (Text)
    - `Timestamp` (DateTime)
10. **`UserLocale`**
    - `UserId` (PK/FK, Guid)
    - `LanguageCode` (Char 5) - e.g., "en-US", "zh-CN"
    - `TimeZone` (Varchar 50)
    - `DateFormat` (Varchar 20)

### 5.2 Key Relationships
- `Users` $\to$ `UserDashboardConfig` (1:1)
- `Users` $\to$ `UserLocale` (1:1)
- `Clients` $\to$ `Transactions` (1:N)
- `Transactions` $\to$ `LedgerEntries` (1:N)
- `Users` $\to$ `ReportSchedules` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### 6.1.1 Development (Dev)
- **Purpose:** Sandbox for engineers to merge feature branches.
- **Deployment:** Continuous Integration (CI) triggers on every merge to the `develop` branch.
- **Data:** Anonymized subsets of production data.
- **Resource Scale:** B1ms Azure Virtual Machines; Basic Tier SQL Database.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and QA Lead (Esme Liu) sign-off.
- **Deployment:** Every Monday, as part of the release train preparation.
- **Data:** Full mirror of production data (scrubbed for PII).
- **Resource Scale:** Standard Tier SQL Database; Multi-instance Azure Functions.

#### 6.1.3 Production (Prod)
- **Purpose:** Live environment for legal service payments.
- **Deployment:** Every Tuesday at 03:00 UTC.
- **Data:** Live transactional data.
- **Resource Scale:** Premium Tier SQL Database; Geo-redundant Azure Functions; Azure Front Door for global routing.

### 6.2 Infrastructure as Code (IaC)
The entire environment is provisioned using Bicep templates. This ensures that the staging and production environments are identical in configuration, reducing the "works on my machine" phenomenon.

### 6.3 Configuration Management
To address the technical debt of hardcoded values across 40+ files, Glacier is migrating to **Azure App Configuration** and **Azure Key Vault**. All hardcoded strings, API keys, and connection strings are being moved to a centralized key-value store, accessible via the `.NET Configuration` provider.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Business logic in Command Handlers and Domain Models.
- **Tooling:** xUnit, Moq.
- **Requirement:** 80% minimum code coverage for all new feature sets.
- **Execution:** Run on every Pull Request (PR) via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Interaction between the API, Azure SQL, and Azure Service Bus.
- **Tooling:** Testcontainers for .NET (to spin up ephemeral SQL instances).
- **Requirement:** All critical paths (Payment Initiation $\to$ Ledger Entry) must be tested.
- **Execution:** Run daily on the `develop` branch.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from the dashboard to payment confirmation.
- **Tooling:** Playwright.
- **Requirement:** 100% pass rate for "Critical" priority features before any Tuesday release train.
- **Execution:** Managed by Esme Liu (QA Lead) in the Staging environment.

### 7.4 Security Testing
As specified, Project Glacier will undergo an **Internal Security Audit only**. There is no requirement for external PCI-DSS or SOC2 compliance for this phase. The audit will focus on:
- SAML token validation.
- SQL Injection prevention via Entity Framework Core.
- Least-privileged access for Azure Functions.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is building same product; 2 months ahead. | High | Medium | Accept risk; monitor competitor feature set weekly in status meetings. |
| **R-02** | Budget cut by 30% in next fiscal quarter. | Medium | High | Engage external consultant for an independent assessment to prove ROI to stakeholders. |
| **R-03** | Design disagreement between Product and Engineering. | High | High | Escalation to Darian Santos (CTO) for final binding decision. |
| **R-04** | Technical Debt: Hardcoded values in 40+ files. | High | Medium | Migration to Azure App Configuration as a priority task in Sprint 1-3. |
| **R-05** | Release Train instability causing downtime. | Low | High | Strict adherence to Staging sign-off by Esme Liu; no hotfixes. |

**Probability/Impact Matrix:**
- High/High: Immediate Action Required.
- Medium/High: Active Monitoring.
- High/Medium: Scheduled Remediation.

---

## 9. TIMELINE AND PHASES

The project follows a phased approach leading up to the final sign-off in September 2025.

### 9.1 Phase 1: Foundation & Debt Clearance (Now - May 2025)
- **Focus:** Resolving hardcoded configuration values and building the CQRS skeleton.
- **Key Dependency:** Completion of Azure SQL schema.
- **Milestone 1:** **Internal Alpha Release (2025-05-15).**

### 9.2 Phase 2: Core Feature Implementation (May 2025 - July 2025)
- **Focus:** Completing SSO, Reporting, and A/B Testing framework.
- **Key Dependency:** SAML/OIDC provider access for testing.
- **Milestone 2:** **Post-launch Stability Confirmed (2025-07-15).**

### 9.3 Phase 3: Optimization & Sign-off (July 2025 - September 2025)
- **Focus:** Localization (Low priority) and final performance tuning.
- **Key Dependency:** Stakeholder availability for the final demo.
- **Milestone 3:** **Stakeholder Demo and Sign-off (2025-09-15).**

### 9.4 Gantt-Style Sequence
- **Jan - Feb:** Infrastructure Setup $\to$ Config Debt Cleanup.
- **Mar - Apr:** Dashboard $\to$ SSO Integration.
- **May:** Alpha Release $\to$ QA Cycle 1.
- **Jun - Jul:** Report Gen $\to$ A/B Testing $\to$ Stability Window.
- **Aug - Sep:** L10n $\to$ Final Audit $\to$ Stakeholder Sign-off.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per team dynamic, formal notes are not taken; decisions are archived from Slack threads.*

### Thread 1: [Config-Debt-Cleanup]
**Date:** 2024-11-02
- **Sanjay Jensen:** "I found another 12 files in the legacy payment module with hardcoded Azure keys. This is a nightmare for the rotation policy."
- **Darian Santos:** "Agreed. Stop all feature work on the payment module for 48 hours. Sanjay, move everything to Azure Key Vault. No more secrets in code."
- **Decision:** All hardcoded secrets must be migrated to Key Vault before the Alpha release.

### Thread 2: [SSO-Provider-Conflict]
**Date:** 2024-12-15
- **Esme Liu:** "The OIDC flow is failing for the Okta test group. It seems there is a mismatch in the claim mapping for roles."
- **Meera Park:** "I'm seeing this in support tickets for the beta users too. They are getting 'Unauthorized' despite having the Admin role in Okta."
- **Sanjay Jensen:** "It's a case-sensitivity issue in the mapping table. I'll normalize the strings to lowercase."
- **Decision:** Implement case-insensitive role mapping for all SSO providers.

### Thread 3: [The-Release-Train-Incident]
**Date:** 2025-01-10
- **Meera Park:** "We have a critical bug in the dashboard widget. It's crashing for users with more than 50 clients. Can we push a hotfix today?"
- **Darian Santos:** "No. The release train is on Tuesday. Fix it, test it in staging, and it goes out on Tuesday."
- **Meera Park:** "But the users are complaining!"
- **Darian Santos:** "The policy is no hotfixes. Stability over speed. Esme, please verify the fix in staging by Monday noon."
- **Decision:** Policy upheld. No hotfix deployed; bug resolved in the next scheduled release.

---

## 11. BUDGET BREAKDOWN

The total budget is **$400,000**. This is a lean budget for a 12-person team, requiring strict management of resource hours.

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $300,000 | Salaries/Contractor fees for the 12-person cross-functional team. |
| **Infrastructure** | 12% | $48,000 | Azure SQL, Cosmos DB, Azure Functions, and Front Door costs. |
| **Tools & Licensing** | 5% | $20,000 | JIRA, GitHub Enterprise, QuestPDF license, and SAML testing tools. |
| **Contingency** | 8% | $32,000 | Reserve for the external consultant (Risk R-02) and emergency scaling. |
| **Total** | **100%** | **$400,000** | |

---

## 12. APPENDICES

### Appendix A: Event Sourcing State Machine
For the `Payment` domain, the following event sequence is required to move a transaction to the "Completed" state:
1. `PaymentInitiatedEvent` $\to$ (Amount, Currency, ClientId)
2. `PaymentMethodValidatedEvent` $\to$ (ProviderResponse, ValidationTimestamp)
3. `FundsReservedEvent` $\to$ (ReserveId, AccountId)
4. `PaymentCapturedEvent` $\to$ (TransactionId, FinalAmount)
5. `LedgerUpdatedEvent` $\to$ (EntryId, BalanceAfter)

Any attempt to trigger `PaymentCapturedEvent` without a preceding `FundsReservedEvent` will result in a `DomainValidationException`.

### Appendix B: Audit Compliance Checklist (Internal)
To pass the internal audit (Success Metric 1), the following must be verified:
- [ ] **Immutability:** Verify that no one can edit the `LedgerEntries` table manually (Read-only permissions for all users).
- [ ] **Traceability:** Every transaction in `Transactions` must have a corresponding `AuditLog` entry showing who initiated it.
- [ ] **Data Isolation:** Ensure that `LegalFirm A` cannot access any `Client` data belonging to `LegalFirm B` via API parameter tampering.
- [ ] **Recovery:** Perform a full restore of the Azure SQL DB from a backup to verify RTO (Recovery Time Objective) is under 4 hours.