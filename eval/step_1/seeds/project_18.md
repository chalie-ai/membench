Due to the extreme length requirements and the complexity of the technical specifications, this document is presented as a comprehensive, formal Project Specification.

***

# PROJECT SPECIFICATION: GANTRY
**Project Code:** GANT-2025-CRS  
**Version:** 1.0.4-BETA  
**Company:** Coral Reef Solutions  
**Industry:** Healthcare Fintech  
**Classification:** CONFIDENTIAL / PCI DSS LEVEL 1  
**Status:** Active / Critical Path  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Gantry" is a mission-critical fintech payment processing system developed by Coral Reef Solutions to serve the specialized needs of the healthcare sector. The primary driver for this project is a hard legal and regulatory compliance deadline occurring in exactly six months. Failure to deploy a compliant system by this date will result in severe legal penalties and the potential loss of operating licenses within several key healthcare jurisdictions.

The system is designed to handle sensitive medical billing data and direct credit card processing. Because the project handles Primary Account Number (PAN) data directly, the system must adhere to PCI DSS Level 1 standards, the most stringent level of payment security certification.

### 1.2 Business Justification
The current legacy payment infrastructure at Coral Reef Solutions is inefficient, utilizing manual reconciliation and outdated batch processing. This results in high overhead costs and significant revenue leakage. Gantry aims to automate the end-to-end billing lifecycle—from patient insurance verification to final credit card settlement.

By transitioning to Gantry, the organization will eliminate third-party intermediary fees for certain transaction types and reduce the manual labor required for subscription management in healthcare provider contracts.

### 1.3 ROI Projection and Success Metrics
The budget for Gantry is set at $800,000, which is considered comfortable for a six-month accelerated build. The investment is justified by two primary success metrics:
1. **Direct Revenue Growth:** The system is projected to enable $500,000 in new revenue within the first 12 months post-launch through the introduction of streamlined subscription models for healthcare practitioners.
2. **Operational Efficiency:** A target reduction of 35% in the cost per transaction compared to the legacy system. This will be achieved through the automation of reconciliation and the reduction of "failed payment" churn.

### 1.4 Strategic Alignment
Gantry aligns with the corporate goal of "Digital Transformation of Health-Pay." By moving to a modern C#/.NET stack on Azure, Coral Reef Solutions ensures scalability and accessibility while maintaining the rigorous data isolation required by HIPAA and PCI DSS.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: The Clean Monolith
Gantry utilizes a "Clean Monolith" architecture. While the system is deployed as a single unit to simplify deployment and reduce network latency between services, it is strictly partitioned into logical modules with clear boundaries. This prevents the "Big Ball of Mud" scenario and allows for a potential future transition to microservices if the scale demands it.

**Core Layers:**
- **Presentation Layer:** Azure Functions (HTTP Triggers) providing the REST API.
- **Application Layer:** Command/Query handlers managing business logic.
- **Domain Layer:** Pure POCOs (Plain Old CLR Objects) containing the business rules of healthcare billing.
- **Infrastructure Layer:** Azure SQL implementation, Entity Framework Core, and PCI-compliant encryption services.

### 2.2 Technology Stack
- **Language:** C# 12 / .NET 8
- **Database:** Azure SQL Database (Hyperscale tier for high availability)
- **Compute:** Azure Functions (Premium Plan for VNET integration)
- **Identity:** Azure Active Directory (integrated via custom RBAC)
- **Encryption:** Azure Key Vault for managed keys (AES-256 for data at rest)

### 2.3 System Diagram (ASCII Representation)
```text
[ Client / Healthcare Portal ] 
             |
             v (HTTPS / TLS 1.3)
    +-----------------------+
    |   Azure API Gateway    | <--- Rate Limiting / WAF
    +----------+------------+
               |
               v
    +-----------------------+      +-----------------------+
    |    Azure Functions     | <--> |  Azure Key Vault       |
    | (Business Logic Layer) |      | (Encryption Keys/Secrets)|
    +----------+------------+      +-----------------------+
               |
       +-------+-------+
       |               |
       v               v
+-------------+  +-------------+
| Azure SQL    |  | Azure Blob  |
| (Tenant Data)|  | (PDF Reports)|
+-------------+  +-------------+
       ^               ^
       |               |
       +-------+-------+
               |
    [ Weekly Release Train ]
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** High | **Status:** Complete
**Description:** This module handles the recurring billing cycles for healthcare providers. It manages the transition from "Trial" to "Active" subscriptions and handles the automatic charging of credit cards based on predefined intervals (Monthly/Annual).

**Functional Specifics:**
- **Billing Engine:** A scheduled Azure Function triggers on the 1st of every month. It scans the `Subscriptions` table for active accounts and generates `Invoice` records.
- **Grace Period Logic:** If a payment fails, the system enters a "Dunning State." It will attempt to retry the card every 3 days for a total of 3 attempts before flagging the account as "Suspended."
- **Proration Logic:** When a user upgrades their plan mid-cycle, the system calculates the remaining value of the current plan and applies it as a credit to the new invoice.
- **PCI Handling:** Credit card numbers are never stored in plaintext. The system uses a "Vault" approach where the PAN is encrypted using a key stored in Azure Key Vault and stored in a separate, highly restricted schema.

### 3.2 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:** Implementation of a secure login system and a hierarchy of permissions to ensure that interns cannot access financial reports and that administrators cannot modify audit logs.

**Functional Specifics:**
- **Role Hierarchy:** 
    - `SuperAdmin`: Full system access.
    - `FinanceManager`: Access to reports and billing, no system config.
    - `Practitioner`: Access to their own patient billing only.
    - `Auditor`: Read-only access to all transaction logs.
- **JWT Implementation:** Using Azure AD tokens. The system validates the `scp` (scope) claim in the token to determine access to specific API endpoints.
- **MFA Requirement:** Per PCI DSS, any user accessing the "Card Management" screen must authenticate via Multi-Factor Authentication (MFA).

### 3.3 Localization and Internationalization (L10n/I18n)
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:** Support for 12 different languages to accommodate global healthcare providers.

**Functional Specifics:**
- **Resource Files:** Use of `.resx` files in .NET to store translations.
- **Supported Languages:** English (US), English (UK), Spanish, French, German, Mandarin, Japanese, Portuguese, Italian, Arabic, Hindi, and Korean.
- **Dynamic Formatting:** Implementation of `CultureInfo` for currency formatting. For example, a payment in the US is formatted as `$1,000.00`, while in Germany, it is formatted as `1.000,00 €`.
- **UTF-8 Compliance:** The Azure SQL database is configured with `Latin1_General_100_CI_AS_SC_UTF8` collation to support non-Latin characters.

### 3.4 Multi-tenant Data Isolation
**Priority:** High | **Status:** In Progress
**Description:** Gantry uses a "Shared Database, Shared Schema" approach with a strict `TenantId` filter on every query to ensure that Hospital A cannot see the billing data of Hospital B.

**Functional Specifics:**
- **Tenant Context:** An `ITenantProvider` service extracts the `TenantId` from the authenticated user's JWT claim.
- **Query Filtering:** A Global Query Filter is implemented in Entity Framework Core: `modelBuilder.Entity<Invoice>().HasQueryFilter(i => i.TenantId == _tenantProvider.GetTenantId());`.
- **Isolation Leak Prevention:** To prevent "Cross-Tenant Data Leakage," a secondary check is performed at the service layer. If a request asks for `InvoiceId 500`, the system verifies that `Invoice 500` belongs to the requesting `TenantId` before returning the data.
- **Performance Tuning:** To mitigate the performance hit of the `TenantId` filter, all tables are clustered by `TenantId` first, then `PrimaryKey`.

### 3.5 PDF/CSV Report Generation and Scheduled Delivery
**Priority:** Low (Nice to Have) | **Status:** In Review
**Description:** Generation of monthly financial summaries for healthcare administrators, delivered via email or available for download.

**Functional Specifics:**
- **Generation Engine:** Uses the `QuestPDF` library for PDF generation and `CsvHelper` for CSV exports.
- **Scheduling:** Azure Functions utilize Timer Triggers to run report jobs at 02:00 AM on the 1st of each month.
- **Storage:** Reports are uploaded to a private Azure Blob Storage container with "Shared Access Signatures" (SAS) that expire after 24 hours.
- **Delivery:** Integration with SendGrid to email the SAS link to the `FinanceManager` of each tenant.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 POST `/billing/subscriptions`
**Description:** Creates a new subscription for a healthcare provider.
- **Request Body:**
```json
{
  "tenantId": "T-9921",
  "planId": "PLAN_PRO_MONTHLY",
  "paymentMethodId": "pm_123456",
  "startDate": "2025-07-01T00:00:00Z"
}
```
- **Response (201 Created):**
```json
{
  "subscriptionId": "SUB-88721",
  "status": "Active",
  "nextBillingDate": "2025-08-01T00:00:00Z"
}
```

### 4.2 GET `/billing/invoices/{invoiceId}`
**Description:** Retrieves a specific invoice.
- **Response (200 OK):**
```json
{
  "invoiceId": "INV-554",
  "amount": 1200.00,
  "currency": "USD",
  "status": "Paid",
  "issuedDate": "2025-06-01"
}
```

### 4.3 PUT `/billing/payment-methods/{methodId}`
**Description:** Updates credit card expiration or billing address.
- **Request Body:**
```json
{
  "expiryMonth": 12,
  "expiryYear": 2027,
  "billingZip": "90210"
}
```
- **Response (200 OK):** `{ "status": "Updated" }`

### 4.4 POST `/billing/pay-now`
**Description:** Manually triggers an immediate charge for an outstanding balance.
- **Request Body:**
```json
{
  "invoiceId": "INV-554",
  "paymentMethodId": "pm_123456"
}
```
- **Response (200 OK):** `{ "transactionId": "TXN-99812", "result": "Success" }`

### 4.5 GET `/reports/summary?tenantId={id}&month=06`
**Description:** Returns a summary of revenue for a specific month.
- **Response (200 OK):**
```json
{
  "totalRevenue": 45000.00,
  "failedTransactions": 12,
  "successfulTransactions": 1420
}
```

### 4.6 POST `/reports/export-pdf`
**Description:** Triggers an immediate PDF export of the current billing cycle.
- **Response (202 Accepted):** `{ "jobId": "JOB-112", "status": "Processing" }`

### 4.7 GET `/auth/me`
**Description:** Returns the current user's identity and assigned roles.
- **Response (200 OK):**
```json
{
  "userId": "U-441",
  "userName": "Suki Oduya",
  "role": "SeniorBackendEngineer",
  "tenantId": "T-001"
}
```

### 4.8 DELETE `/billing/subscriptions/{subscriptionId}`
**Description:** Cancels a subscription (effective at the end of the current period).
- **Response (204 No Content):** No body.

---

## 5. DATABASE SCHEMA

The system uses a relational model in Azure SQL. Due to performance requirements, 30% of the system interacts with these tables via raw SQL (bypassing EF Core).

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` | - | `TenantName`, `Region`, `CreatedAt` | Top-level organization entity. |
| `Users` | `UserId` | `TenantId` | `Email`, `PasswordHash`, `Role` | System users and their RBAC roles. |
| `Subscriptions` | `SubId` | `TenantId`, `PlanId` | `Status`, `StartDate`, `NextBillDate` | Tracks recurring billing status. |
| `Plans` | `PlanId` | - | `PlanName`, `MonthlyCost`, `Currency` | Definition of available billing tiers. |
| `Invoices` | `InvoiceId` | `SubId`, `TenantId` | `TotalAmount`, `DueDate`, `Status` | Individual billing statements. |
| `InvoiceItems` | `ItemId` | `InvoiceId` | `Description`, `UnitPrice`, `Quantity` | Line items within a single invoice. |
| `PaymentMethods`| `MethodId` | `TenantId` | `ProviderToken`, `LastFour`, `Expiry` | PCI-compliant payment references. |
| `Transactions` | `TxnId` | `InvoiceId`, `MethodId`| `Amount`, `Timestamp`, `ResponseCode`| Ledger of all payment attempts. |
| `AuditLogs` | `LogId` | `UserId` | `Action`, `Timestamp`, `IpAddress` | Immutable record of system changes. |
| `ReportJobs` | `JobId` | `TenantId` | `ReportType`, `Status`, `BlobUrl` | Tracking for asynchronous PDF/CSV jobs. |

### 5.2 Relationships
- `Tenants` $\to$ `Users` (1:N)
- `Tenants` $\to$ `Subscriptions` (1:N)
- `Subscriptions` $\to$ `Invoices` (1:N)
- `Invoices` $\to$ `InvoiceItems` (1:N)
- `Invoices` $\to$ `Transactions` (1:N)
- `PaymentMethods` $\to$ `Transactions` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry follows a strict three-tier environment promotion strategy.

1. **Development (DEV):**
   - **Purpose:** Sandbox for the solo developer and intern.
   - **Database:** Azure SQL (Basic Tier).
   - **Deployment:** Auto-deploy from `develop` branch.
   - **Data:** Mock data only. No real PCI data.

2. **Staging (STG):**
   - **Purpose:** Pre-production validation and QA.
   - **Database:** Azure SQL (Standard Tier), mirrored schema of PROD.
   - **Deployment:** Manual trigger from `release` branch.
   - **Data:** Anonymized production snapshots.

3. **Production (PROD):**
   - **Purpose:** Live healthcare billing.
   - **Database:** Azure SQL (Hyperscale Tier) with Geo-Replication.
   - **Deployment:** Weekly Release Train.
   - **Data:** Real encrypted PCI data.

### 6.2 The Weekly Release Train
To maintain stability and compliance, Gantry adheres to a **Weekly Release Train**.
- **Cut-off:** Wednesday at 5:00 PM.
- **Deployment Window:** Thursday at 10:00 AM.
- **Rule:** No hotfixes are permitted outside of the train. If a critical bug is found on Friday, it must wait until the following Thursday's train unless it is a "Total System Outage" (Severity 1), which requires approval from Greta Fischer.

### 6.3 PCI DSS Level 1 Infrastructure
- **Network Isolation:** All Azure Functions are deployed within a Virtual Network (VNET).
- **Data Encryption:** Use of Always Encrypted in Azure SQL for the `PaymentMethods` table.
- **Access Control:** Just-In-Time (JIT) access via Azure Bastion for any database maintenance.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** xUnit and Moq.
- **Coverage Goal:** 80% of domain logic.
- **Focus:** Testing the proration logic in the `BillingEngine` and the role-validation logic in the `RBACService`.

### 7.2 Integration Testing
- **Tool:** Postman and Azure Dev Ops Pipelines.
- **Approach:** Testing the interaction between the Azure Functions and Azure SQL.
- **Crucial Test:** Verifying that a query for `Tenant A` never returns data for `Tenant B` (Cross-Tenant Leakage Test).

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Scenario:** A full "Happy Path" where a user creates an account, attaches a credit card, is billed for a month, and downloads a PDF report.
- **Frequency:** Executed once per release train on the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team has no experience with .NET/Azure stack | High | High | **Parallel-Path:** Developer is prototyping alternative lightweight approaches while learning the main stack. |
| R-02 | Key Architect leaving company in 3 months | Medium | Critical | **Knowledge Transfer:** Assign a dedicated owner to document all architectural decisions and resolve pending design debts. |
| R-03 | PCI DSS Audit failure | Low | Critical | Strict adherence to Level 1 standards; weekly internal security audits. |
| R-04 | Performance degradation due to EF Core | Medium | Medium | Bypass ORM with raw SQL for high-traffic queries (Current technical debt). |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure / Legal action.
- **High:** Milestone missed / Budget overrun.
- **Medium:** Performance issues / Feature delayed.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases
- **Phase 1: Foundations (Month 1-2):** Focus on Multi-tenancy and Billing Engine.
- **Phase 2: Hardening (Month 3-4):** PCI DSS compliance, RBAC implementation, and Performance tuning.
- **Phase 3: Finalization (Month 5-6):** Localization, Reporting, and Final Audit.

### 9.2 Key Milestones
- **Milestone 1: Performance benchmarks met**
  - **Target Date:** 2025-06-15
  - **Criteria:** System must process 1,000 transactions per second with $<200\text{ms}$ latency.
- **Milestone 2: MVP feature-complete**
  - **Target Date:** 2025-08-15
  - **Criteria:** Billing, Multi-tenancy, and basic Auth are fully functional.
- **Milestone 3: Post-launch stability confirmed**
  - **Target Date:** 2025-10-15
  - **Criteria:** Zero Severity-1 bugs for 30 consecutive days.

### 9.3 Dependencies
- **External Blocker:** The "Patient Portal" team's API is currently 3 weeks behind. This prevents full E2E testing of the billing flow.
- **Internal Dependency:** The completion of the `TenantId` filter must precede the development of the Reporting module.

---

## 10. MEETING NOTES

*Note: These notes are extracted from the shared 200-page running document. Search functionality is not available.*

### Meeting 1: 2025-03-10 (Project Kickoff)
**Attendees:** Greta, Suki, Kenji, Farid.
**Discussion:**
- Greta emphasized the 6-month deadline.
- Suki expressed concern that the team has never used .NET before.
- Greta dismissed the concern, stating the budget is comfortable.
- Farid asked where the documentation is; Greta pointed him to the running document.
- **Decision:** Use a clean monolith to avoid over-engineering.

### Meeting 2: 2025-04-12 (Architecture Review)
**Attendees:** Greta, Suki, Farid. (Kenji absent)
**Discussion:**
- Suki complained that the ORM is too slow for the `Transactions` table.
- Greta and Suki entered a heated argument regarding "architectural purity." They stopped speaking for the remainder of the meeting.
- Suki decided to use raw SQL for 30% of the queries to meet performance benchmarks.
- Farid noted that this makes migrations dangerous.
- **Decision:** Raw SQL is permitted for performance, but must be documented in the codebase.

### Meeting 3: 2025-05-05 (Risk Mitigation)
**Attendees:** Greta, Suki, Kenji.
**Discussion:**
- Announcement that the Lead Architect is leaving in 3 months.
- Greta suggests Suki takes over, but Suki refuses unless the "communication issues" are addressed.
- Discussion shifted to the Patient Portal team being 3 weeks behind.
- Kenji mentioned that the UX for localization is missing for Arabic (RTL support).
- **Decision:** Assign a "Shadow Architect" to track the leaving architect's knowledge.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $550,000 | Salaries for 1 Senior BE, 1 UX, 1 Intern, plus Project Lead overhead. |
| **Infrastructure** | $120,000 | Azure Consumption (SQL Hyperscale, Functions Premium, Key Vault). |
| **Tooling & Licenses** | $40,000 | QuestPDF Professional, SendGrid, PCI Compliance Scanning Tools. |
| **Contingency** | $90,000 | Buffer for potential legal consultants or emergency contractor hires. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Protocol
Due to the 30% raw SQL usage, the following protocol must be followed for all database changes:
1. **Schema Snapshot:** Take a full snapshot of the database before any migration.
2. **Manual Audit:** A developer must manually search the codebase for any `string` based SQL queries that reference the changed column.
3. **Verification:** Run the "Regression Suite" in Staging to ensure raw SQL queries are not throwing `SqlException`.

### Appendix B: PCI DSS Level 1 Compliance Checklist
- [x] **Encryption:** PAN data encrypted with AES-256.
- [x] **Isolation:** VNET implemented for all compute resources.
- [x] **Logging:** All access to the `PaymentMethods` table is logged in `AuditLogs`.
- [ ] **Rotation:** Key rotation in Azure Key Vault (Scheduled for Month 4).
- [ ] **Audit:** Third-party QSA (Qualified Security Assessor) audit (Scheduled for Month 6).