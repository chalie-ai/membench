Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Technical Specification Document (TSD). It serves as the "Single Source of Truth" for the Gantry project.

***

# PROJECT SPECIFICATION: GANTRY
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Document Status:** Final/Approved  
**Owner:** Paloma Kim (CTO)  
**Company:** Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Overview
Gantry is a greenfield SaaS platform designed to disrupt the logistics and shipping industry. Developed by Coral Reef Solutions, Gantry aims to provide a high-efficiency coordination layer for mid-to-large scale shipping operations. Unlike previous ventures by Coral Reef Solutions, Gantry represents a strategic pivot into a market where the company has no prior operational footprint. The platform is designed to act as the "central nervous system" for shipping manifests, real-time tracking, and compliance reporting.

### 1.2 Business Justification
The logistics sector currently relies on fragmented legacy systems characterized by siloed data and manual entry. Gantry addresses this by providing a modern, cloud-native interface that integrates disparate data streams into a single pane of glass. By utilizing a CQRS (Command Query Responsibility Segregation) architecture with event sourcing, Gantry ensures that every single change to a shipment's status is immutable and auditable—a critical requirement for the highly regulated shipping and customs industry.

### 1.3 ROI Projection
With a lean development budget of $150,000, the project is structured for high capital efficiency. The primary ROI driver is the subscription-based SaaS model targeting 10,000 Monthly Active Users (MAU) within six months post-launch. 

**Projected Financials:**
- **Customer Acquisition Cost (CAC):** Estimated at $45 per user.
- **Monthly Recurring Revenue (MRR) Target:** Assuming a tiered pricing model (Basic: $15/mo, Pro: $45/mo), the target is to reach an MRR of $225,000 by Month 6.
- **Break-Even Analysis:** Based on the initial $150k investment and estimated Azure operational costs of $1,200/month, the project is projected to reach the break-even point within 4 months of the general availability (GA) release.

### 1.4 Strategic Alignment
Gantry is not merely a tool but a strategic entry point for Coral Reef Solutions into the logistics vertical. Success in this venture will prove the company's ability to scale greenfield products in unfamiliar markets, diversifying the company's portfolio and reducing reliance on previous industry verticals.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Selection
Gantry is built on the full Microsoft ecosystem to ensure maximum stability, enterprise support, and HIPAA compliance.
- **Language:** C# / .NET 8 (Long Term Support)
- **Database:** Azure SQL Database (Hyperscale tier for scaling)
- **Compute:** Azure Functions (Serverless for event-driven tasks)
- **Messaging/Event Store:** Azure Service Bus and Azure Table Storage (for event sourcing)
- **Identity:** Azure Active Directory (Azure AD) / Entra ID

### 2.2 Architecture Pattern: CQRS & Event Sourcing
To ensure a perfect audit trail for shipping manifests, Gantry implements a Command Query Responsibility Segregation (CQRS) pattern.

- **Command Side:** Handles state changes. Every "write" is stored as an immutable event in an Event Store (Azure Table Storage).
- **Query Side:** Optimized read models are projected into Azure SQL for fast retrieval.
- **Event Sourcing:** Instead of storing just the current state of a shipment, Gantry stores the sequence of events (e.g., `ShipmentCreated` $\rightarrow$ `PackageWeighed` $\rightarrow$ `CustomsCleared` $\rightarrow$ `OutForDelivery`).

### 2.3 ASCII Architecture Diagram Description
Below is the conceptual flow of the Gantry System:

```text
[ Client: Web/Mobile ] 
       |
       v
[ Azure API Management / Gateway ] <--- (Rate Limiting Layer)
       |
       +-----------------------+
       |                        |
 [ Command API ]          [ Query API ]
       |                        |
 [ Command Handler ]      [ Read Model ] <--- (Azure SQL)
       |                        |
 [ Event Store ] <--------------+
 (Azure Table Storage)
       |
 [ Azure Service Bus ] ---> [ Eventual Consistency Projector ]
       |
 [ Azure Functions ] ---> [ PDF Generation/Email Alerts ]
```

### 2.4 Security and Compliance
As a HIPAA-compliant platform, Gantry adheres to strict data handling protocols:
- **Encryption at Rest:** All Azure SQL and Table Storage data is encrypted using AES-256.
- **Encryption in Transit:** TLS 1.3 is enforced for all endpoints.
- **Data Isolation:** Tenant-based partitioning in the database to prevent cross-tenant data leakage.
- **Audit Logs:** Every API call is logged with the user ID, timestamp, and IP address.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Not Started

**Overview:**
To meet HIPAA and high-security logistics standards, Gantry requires a robust multi-factor authentication (MFA) system. This feature moves beyond simple SMS codes to support FIDO2-compliant hardware keys (e.g., Yubikey).

**Functional Requirements:**
- **Enrollment:** Users must be able to register one or more hardware keys via the `/auth/mfa/register` endpoint.
- **Challenge-Response:** Upon successful password entry, the system must issue a challenge that the hardware key signs.
- **Recovery:** Implementation of 10 one-time-use backup codes for users who lose their hardware keys.
- **Enforcement:** Admins can force MFA for specific user roles (e.g., "Customs Officer").

**Technical Logic:**
The system will utilize the WebAuthn API. When a user attempts to log in, the server generates a random challenge. The hardware key signs this challenge with a private key and returns the signature. The server verifies this against the stored public key in the `UserMFAKeys` table.

**Acceptance Criteria:**
- Successful login using a YubiKey 5 series device.
- Failure to login when an incorrect key is used.
- Ability to revoke a lost key via the admin dashboard.

---

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Review

**Overview:**
To prevent DDoS attacks and manage the costs associated with third-party API calls, Gantry requires a sophisticated rate-limiting engine. This system must track usage per API key and trigger alerts when thresholds are approached.

**Functional Requirements:**
- **Tiered Limits:** Different limits based on the subscription (e.g., Basic: 1,000 req/hr; Pro: 10,000 req/hr).
- **Sliding Window Algorithm:** Implementation of a sliding window log to prevent "bursting" at the edge of a fixed time window.
- **Analytics Dashboard:** A UI for users to see their current usage versus their limit.
- **Header Injection:** Every API response must include `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers.

**Technical Logic:**
Rate limiting is handled at the Azure API Management (APIM) layer using policies. However, the usage analytics are persisted in Azure SQL via a background Azure Function that aggregates logs every 5 minutes to avoid overloading the primary database.

**Acceptance Criteria:**
- API returns `429 Too Many Requests` when the limit is exceeded.
- Analytics dashboard reflects usage within a 5-minute latency window.
- Support for "bursting" (allowing 10% over limit for 30 seconds).

---

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** In Review

**Overview:**
Logistics managers require snapshots of shipping data for auditing and customs declarations. Gantry will provide a reporting engine that can generate complex documents and deliver them on a schedule.

**Functional Requirements:**
- **Templates:** Ability to choose between "Daily Manifest," "Monthly Audit," and "Customs Declaration" templates.
- **Scheduling:** A Cron-like interface allowing users to set reports for "Every Monday at 8 AM" or "The 1st of every month."
- **Delivery:** Delivery via encrypted email (SMTP) or direct upload to an Azure Blob Storage folder linked to the user's account.
- **Format:** High-fidelity PDF (using a library like QuestPDF) and RFC 4180 compliant CSVs.

**Technical Logic:**
A dedicated Azure Function (Timer Trigger) scans the `ReportSchedules` table. If a report is due, it triggers a "ReportJob" in a queue. A separate worker process fetches the data from the Read Model (Azure SQL), generates the file, and uploads it to Blob Storage. The user is then notified via email with a time-limited SAS (Shared Access Signature) link.

**Acceptance Criteria:**
- Reports are delivered within 15 minutes of the scheduled time.
- PDF layout remains consistent across different data volumes.
- CSV files are correctly encoded in UTF-8.

---

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Design

**Overview:**
Shipping manifests are often edited by multiple agents (e.g., a warehouse manager and a shipping agent) simultaneously. Gantry must support real-time collaboration to prevent data loss.

**Functional Requirements:**
- **Presence Indicators:** Users can see who else is currently editing a specific manifest (avatars in the header).
- **Real-time Updates:** Changes made by one user must appear for others in $<200$ms.
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to handle simultaneous edits to the same field.
- **Locking Mechanism:** Optional "Field Locking" where a user can lock a specific row to prevent others from editing it during a critical update.

**Technical Logic:**
Using Azure SignalR Service for the WebSocket layer. When a user edits a field, a "patch" event is sent to the SignalR hub. The hub broadcasts this patch to all other connected clients. To handle conflicts, the system uses a Last-Write-Wins (LWW) approach for simple fields, but a Sequence-based OT approach for text-heavy "Notes" fields.

**Acceptance Criteria:**
- Two users can edit different fields in the same manifest without interference.
- Simultaneous edits to the same field are resolved without crashing the browser.
- Latency between users is under 500ms globally.

---

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low | **Status:** Blocked

**Overview:**
The "Nice to Have" feature: a low-code engine that allows users to automate logistics tasks (e.g., "If Shipment Status = 'Delayed' AND Value > $5,000, then Email Manager").

**Functional Requirements:**
- **Visual Builder:** A drag-and-drop interface to define Triggers, Conditions, and Actions.
- **Trigger Types:** Event-based triggers (e.g., `OrderCreated`, `CustomsHold`).
- **Condition Logic:** Support for AND/OR operators and numerical comparisons.
- **Action Library:** Pre-defined actions such as "Send Email," "Update Status," and "Trigger External Webhook."

**Technical Logic:**
The engine will use a JSON-based rule definition stored in the database. An Azure Function "Evaluator" will listen to the Event Store. When an event occurs, the Evaluator checks all active rules for that tenant. If conditions are met, it pushes the defined action into the execution queue.

**Acceptance Criteria:**
- A user can create a rule that sends an email when a shipment is marked "Damaged."
- Rules are executed within 60 seconds of the trigger event.
- Visual builder prevents the creation of infinite loops (e.g., Action A triggers Rule B, which triggers Action A).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is required via Bearer Token (JWT).

### 4.1 Manifests
**Endpoint:** `GET /manifests/{manifestId}`  
**Description:** Retrieves the current state of a shipping manifest.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:**  
```json
{
  "manifestId": "MNF-99021",
  "status": "In-Transit",
  "items": 42,
  "origin": "Shanghai, CN",
  "destination": "Los Angeles, US",
  "lastUpdated": "2023-10-25T14:20:00Z"
}
```

**Endpoint:** `POST /manifests`  
**Description:** Creates a new shipping manifest.  
**Request Body:**  
```json
{
  "origin": "Singapore, SG",
  "destination": "Rotterdam, NL",
  "priority": "High",
  "items": []
}
```
**Response:** `201 Created` with the manifest object.

### 4.2 Authentication & MFA
**Endpoint:** `POST /auth/login`  
**Description:** Initial credential validation.  
**Request Body:** `{"username": "pkim", "password": "..."}`  
**Response:** `200 OK` with a temporary "MFA-Pending" token.

**Endpoint:** `POST /auth/mfa/verify`  
**Description:** Verifies the hardware key signature.  
**Request Body:** `{"mfaToken": "...", "signature": "...", "challenge": "..."}`  
**Response:** `200 OK` with a full Access Token and Refresh Token.

### 4.3 Reporting
**Endpoint:** `POST /reports/schedule`  
**Description:** Sets up a recurring report delivery.  
**Request Body:**  
```json
{
  "templateId": "DAILY_MANIFEST",
  "frequency": "Weekly",
  "dayOfWeek": "Monday",
  "deliveryEmail": "ops@shippingco.com"
}
```
**Response:** `202 Accepted`.

**Endpoint:** `GET /reports/download/{reportId}`  
**Description:** Downloads a generated report.  
**Response:** Returns a binary stream (PDF/CSV) with `Content-Type: application/pdf`.

### 4.4 Analytics
**Endpoint:** `GET /analytics/usage`  
**Description:** Returns current API usage metrics for the token holder.  
**Response:**  
```json
{
  "currentPeriod": "2023-10",
  "requestsUsed": 8500,
  "limit": 10000,
  "percentageUsed": 85.0
}
```

**Endpoint:** `GET /analytics/latency`  
**Description:** Provides performance metrics for manifest queries.  
**Response:** `{"p95_latency": "120ms", "p99_latency": "450ms"}`

---

## 5. DATABASE SCHEMA

The database is hosted on Azure SQL and uses a relational schema for the Read Model.

### 5.1 Table Definitions

| Table Name | Key Field | Description | Relationships |
| :--- | :--- | :--- | :--- |
| `Tenants` | `TenantId` (PK) | Company account details | One-to-Many with `Users` |
| `Users` | `UserId` (PK) | User profiles and credentials | Many-to-One with `Tenants` |
| `UserMFAKeys` | `KeyId` (PK) | Registered FIDO2 Public Keys | Many-to-One with `Users` |
| `Manifests` | `ManifestId` (PK) | Current state of shipments | Many-to-One with `Tenants` |
| `ManifestItems` | `ItemId` (PK) | Individual items in a manifest | Many-to-One with `Manifests` |
| `Events` | `EventId` (PK) | Immutable event log (Event Store) | Many-to-One with `Manifests` |
| `ReportSchedules` | `ScheduleId` (PK) | Cron definitions for reports | Many-to-One with `Users` |
| `ReportLogs` | `LogId` (PK) | History of generated reports | Many-to-One with `ReportSchedules` |
| `ApiUsage` | `UsageId` (PK) | Aggregated request counts | Many-to-One with `Tenants` |
| `AuditLogs` | `AuditId` (PK) | HIPAA compliant access logs | Many-to-One with `Users` |

### 5.2 Key Schema Details (SQL)
```sql
CREATE TABLE Manifests (
    ManifestId UNIQUEIDENTIFIER PRIMARY KEY,
    TenantId UNIQUEIDENTIFIER NOT NULL,
    Status VARCHAR(50),
    Origin NVARCHAR(255),
    Destination NVARCHAR(255),
    CreatedAt DATETIMEOFFSET,
    UpdatedAt DATETIMEOFFSET,
    Version INT -- Used for optimistic concurrency
);

CREATE TABLE Events (
    EventId UNIQUEIDENTIFIER PRIMARY KEY,
    AggregateId UNIQUEIDENTIFIER, -- ManifestId
    EventType VARCHAR(100),
    Payload NVARCHAR(MAX), -- JSON representation of the change
    Timestamp DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);
```

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Strategy
Gantry follows a strictly managed environment strategy. Because the budget is a "shoestring" $150,000, we avoid expensive multi-region clusters and instead rely on Azure's serverless capabilities.

### 6.2 Environment Descriptions
1. **Development (DEV):** 
   - **Purpose:** Feature development and unit testing.
   - **Configuration:** Azure Functions (Consumption Plan), Azure SQL (Basic Tier).
   - **Deployment:** Auto-deploy from `develop` branch via GitHub Actions.
2. **Staging (STG):**
   - **Purpose:** QA and UAT (User Acceptance Testing).
   - **Configuration:** Mimics Production settings.
   - **Deployment:** Manual trigger by Ren Liu.
3. **Production (PROD):**
   - **Purpose:** Live customer traffic.
   - **Configuration:** Azure SQL (Hyperscale), Azure Functions (Premium Plan for VNet integration).
   - **Deployment:** Manual deployment only.

### 6.3 The "Bus Factor" Risk
Currently, **Ren Liu** is the sole individual with access to the Production deployment pipelines and Azure Portal administrative rights. This creates a "Bus Factor of 1." 
- **Mitigation Plan:** Paloma Kim is currently documenting the deployment scripts in the project Wiki, though actual deployment remains manual to ensure stability.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Requirement:** All business logic in the Command Handlers must have $\ge 80\%$ code coverage.
- **Focus:** Validation of event generation and state transitions.

### 7.2 Integration Testing
- **Framework:** Postman / Newman.
- **Approach:** Testing the interaction between Azure Functions and Azure SQL.
- **Frequency:** Run on every Pull Request to the `develop` branch.
- **Key Scenarios:** MFA flow completion, Report generation trigger $\rightarrow$ Blob upload.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Owner:** Greta Kim (QA Lead).
- **Approach:** Full user journeys from login $\rightarrow$ manifest creation $\rightarrow$ report download.
- **Frequency:** Weekly regression suites run every Friday.

### 7.4 HIPAA Compliance Validation
- **Penetration Testing:** Semi-annual security audits focusing on data leakage.
- **Encryption Check:** Automated scripts to verify that no plain-text PII (Personally Identifiable Information) exists in the `Events` table.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with .NET/Azure stack | High | High | **Parallel-path:** Prototype alternative approach simultaneously; use intensive pair programming. |
| R-02 | Project sponsor rotation (leaving role) | Medium | Critical | **Escalation:** Raise as a blocker in the next board meeting to secure a new champion. |
| R-03 | Third-party API rate limits (Current Blocker) | High | Medium | Implement a local mock server for testing; request quota increase from provider. |
| R-04 | Single point of failure (DevOps) | Medium | High | Cross-train Veda Jensen on basic deployment tasks. |
| R-05 | Budget overrun ($150k limit) | Medium | High | Weekly budget review; prioritize "Must-Haves" over "Nice-to-Haves." |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required.
- **High:** Close monitoring and active mitigation.
- **Medium:** Acceptable with periodic review.

---

## 9. TIMELINE & MILESTONES

The project follows a phased approach with strict deadlines. All tasks are tracked in JIRA.

### 9.1 Phase 1: Foundation & Core Auth (Now $\rightarrow$ 2025-03-01)
- **Focus:** Infrastructure setup, Database schema implementation, MFA development.
- **Dependencies:** Azure environment provisioning.

### 9.2 Phase 2: Manifests & Event Sourcing (2025-03-01 $\rightarrow$ 2025-08-15)
- **Focus:** CQRS implementation, Manifest CRUD, Real-time editing.
- **Milestone 1: MVP Feature-Complete (Target: 2025-08-15).**

### 9.3 Phase 3: Optimization & Reporting (2025-08-15 $\rightarrow$ 2025-10-15)
- **Focus:** PDF/CSV engine, Rate limiting, Performance tuning.
- **Milestone 2: Performance Benchmarks Met (Target: 2025-10-15).**

### 9.4 Phase 4: Stability & Scale (2025-10-15 $\rightarrow$ 2025-12-15)
- **Focus:** Load testing, Security hardening, Final QA.
- **Milestone 3: Post-launch Stability Confirmed (Target: 2025-12-15).**

---

## 10. MEETING NOTES

*Note: Per company policy, all meetings are recorded via video calls. These notes represent the summaries of those recordings.*

### Meeting 1: Architecture Review (2023-11-02)
- **Attendees:** Paloma, Ren, Greta, Veda.
- **Discussion:** Paloma presented the CQRS and Event Sourcing model. Ren expressed concern about the complexity of maintaining two data models (Read and Write).
- **Decision:** Team agreed to proceed with CQRS due to the audit requirements of the shipping industry. Veda was assigned to research `AutoMapper` for projecting events to read models.
- **Outcome:** Architecture approved.

### Meeting 2: MFA and Security Sync (2023-11-15)
- **Attendees:** Paloma, Ren, Greta.
- **Discussion:** Greta pointed out that the current login flow does not account for hardware key failures. Paloma suggested implementing backup codes.
- **Decision:** 10 recovery codes will be generated upon MFA enrollment.
- **Outcome:** Updated the Feature Specification for 2FA.

### Meeting 3: The "God Class" Crisis (2023-12-01)
- **Attendees:** Paloma, Ren, Veda.
- **Discussion:** Veda discovered a 3,000-line class (`SystemManager.cs`) that handles authentication, logging, and email. Ren noted that this class is becoming a bottleneck for testing and causing multiple merge conflicts.
- **Decision:** The class will be marked as "Technical Debt." Refactoring will be scheduled for Phase 2, but for now, it will be wrapped in an Interface to allow for gradual decomposition.
- **Outcome:** Added to the Technical Debt log.

---

## 11. BUDGET BREAKDOWN

The total budget is **$150,000**. Every expenditure is scrutinized by the CTO.

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $110,000 | 6 members (including Intern and QA). Adjusted for project duration. |
| **Azure Infrastructure** | $18,000 | Estimated $1,500/mo for 12 months (incl. SQL Hyperscale). |
| **Tooling & Licenses** | $7,000 | JIRA Premium, GitHub Enterprise, QuestPDF License. |
| **Security Audit** | $10,000 | Third-party HIPAA compliance verification. |
| **Contingency Fund** | $5,000 | Emergency buffer for API overages. |
| **Total** | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
- **Item TD-01:** `SystemManager.cs` "God Class" (3,000 lines).
  - **Impact:** High risk of regression, difficult to unit test.
  - **Proposed Fix:** Split into `AuthService`, `LoggingService`, and `NotificationService`.
- **Item TD-02:** Manual Deployment Process.
  - **Impact:** High risk of human error; Bus Factor of 1.
  - **Proposed Fix:** Transition to Terraform for Infrastructure as Code (IaC).

### Appendix B: HIPAA Data Mapping
| Data Field | Encryption Method | Access Level | Retention Policy |
| :--- | :--- | :--- | :--- |
| User Email | AES-256 | Admin/System | 7 Years |
| Shipping Address | AES-256 | Authorized Agent | 5 Years |
| Audit Log | Hashed/Encrypted | Auditor Only | Permanent |
| MFA Public Keys | Plaintext (Public) | System | Until Revoked |

***

**End of Document**