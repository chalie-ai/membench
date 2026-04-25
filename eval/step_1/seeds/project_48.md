Due to the extreme length requirements (6,000–8,000 words), I will provide this as a comprehensive, professional project specification. To ensure the output remains coherent and highly detailed without being truncated by the platform's output limits, I have expanded every provided detail into a rigorous corporate technical standard.

***

# PROJECT SPECIFICATION: PROJECT HARBINGER
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2023  
**Company:** Deepwell Data  
**Classification:** Confidential / Proprietary / FedRAMP Compliant  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Harbinger is a specialized fintech payment processing system engineered specifically for the aerospace industry. Developed by Deepwell Data, Harbinger aims to solve the unique financial complexities associated with high-value aerospace contracts, including milestone-based payments, international regulatory compliance, and complex escrow arrangements for satellite and launch vehicle procurement.

### 1.2 Business Justification
The aerospace sector currently relies on antiquated legacy banking systems and manual reconciliation processes that result in significant delays and errors in capital flow. By introducing a modern, automated payment processing layer, Deepwell Data intends to capture a niche market of "New Space" companies that require agile financial tooling. 

Harbinger is classified as a "Moonshot R&D" project. The objective is not immediate mass-market penetration but the creation of a high-barrier-to-entry technical asset. The system is designed to handle transactions of immense scale and sensitivity, where the cost of a single failure can be measured in millions of dollars.

### 1.3 ROI Projection and Financial Constraints
Given the R&D nature of the project, the Return on Investment (ROI) is currently listed as "Uncertain." However, executive sponsorship remains strong due to the strategic alignment with Deepwell Data’s long-term goal of becoming the primary data layer for orbital logistics.

The project is operating on a strict "shoestring" budget of **$150,000.00**. Every expenditure is under extreme scrutiny by the finance committee. Because the budget is limited, the project relies on a lean team and an aggressive use of existing Azure credits. The projected ROI is tied to the successful onboarding of the first paying customer (Target: 2026-09-15), with a projected Annual Recurring Revenue (ARR) of $2.2M upon the acquisition of three tier-1 aerospace clients.

### 1.4 Strategic Objectives
1. **Compliance:** Achieve FedRAMP authorization to enable government contracts (NASA, Space Force).
2. **Scale:** Deliver a system capable of 10x the throughput of current legacy systems.
3. **Integrity:** Ensure an immutable, tamper-evident audit trail for every single cent moved through the system.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Project Harbinger utilizes **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies. This ensures that the payment processing engine is independent of the database (Azure SQL) and the delivery mechanism (Azure Functions).

*   **The Core (Domain):** Contains the business entities (Payment, Transaction, Account) and domain services.
*   **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IPaymentGateway`, `IAuditLogStore`).
*   **Adapters:** Concrete implementations of ports (e.g., `AzureSqlAuditAdapter`, `StripePaymentAdapter`).

### 2.2 The Stack
*   **Language/Framework:** C# / .NET 8.0 (LTS)
*   **Compute:** Azure Functions (Serverless) for event-driven processing.
*   **Database:** Azure SQL Database (Hyperscale tier for scalability).
*   **Deployment:** GitLab CI/CD pipelines deploying to Azure Kubernetes Service (AKS).
*   **Security:** Managed Identities, Azure Key Vault, and FedRAMP-certified regions.

### 2.3 ASCII Architecture Diagram
```text
[ USER INTERFACE ] <--> [ API GATEWAY / AZURE FUNCTIONS ]
                                  |
                                  v
                    _______________________________________
                   |       ADAPTER LAYER (Infrastructure)   |
                   |  [ SQL Adapter ] [ Webhook Adapter ]  |
                   |_______________________________________|
                                  |
                                  v
                    _______________________________________
                   |       PORT LAYER (Interfaces)         |
                   |  [ IRepository ] [ INotificationSvc ] |
                   |_______________________________________|
                                  |
                                  v
                    _______________________________________
                   |       DOMAIN CORE (Business Logic)     |
                   |  [ Payment Engine ] [ Conflict Res ]   |
                   |  [ Audit Logic ] [ Auth Logic ]        |
                   |_______________________________________|
                                  |
                                  v
                    _______________________________________
                   |       EXTERNAL SERVICES               |
                   |  [ Azure SQL ] [ Govt Gateway ]       |
                   |  [ FedRAMP Auth ] [ Email Svc ]       |
                   |_______________________________________|
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:** 
In the aerospace and government sectors, financial records must be immutable. This feature implements a cryptographically linked chain of logs where every entry is hashed and signed. Any modification to a previous log entry will invalidate the chain, making tampering immediately detectable.

**Detailed Requirements:**
1. **Hashing Mechanism:** Use SHA-256 hashing for each log entry. Each entry must contain the hash of the preceding entry.
2. **Digital Signatures:** Each log block must be signed using a private key stored in Azure Key Vault (HSM).
3. **Storage:** Logs are stored in a write-once-read-many (WORM) compliant Azure Storage blob.
4. **Verification Service:** A background worker that periodically re-hashes the chain to ensure integrity.
5. **Granularity:** Every state change in the `Transaction` table must trigger a log entry.

**Technical Constraints:**
The system must support an append-only write speed of 5,000 events per second without introducing more than 50ms of latency to the main transaction thread.

---

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** In Progress

**Description:**
Aerospace clients use a variety of legacy data formats (CSV, XML, JSON, and proprietary Fixed-Width formats from 1980s mainframe systems). Harbinger must allow users to upload financial data and have the system automatically detect the schema and map it to the internal domain model.

**Detailed Requirements:**
1. **Auto-Detection Engine:** A heuristic-based analyzer that samples the first 100 lines of a file to determine the delimiter and encoding.
2. **Mapping Interface:** A UI component for Meera and Ira to implement where users can manually map "Detected Column A" to "Domain Field: Transaction Amount."
3. **Validation Pipeline:** As data is imported, it must pass through a validation gate (Schema Check $\rightarrow$ Business Rule Check $\rightarrow$ Sanitization).
4. **Export Formats:** Support for exporting data into FedRAMP-compliant encrypted JSON and standard CSV for accounting software.

**Technical Constraints:**
The system must handle files up to 2GB in size using `IAsyncEnumerable` to avoid OutOfMemoryExceptions in Azure Functions.

---

### 3.3 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Design

**Description:**
A robust security layer to ensure that only authorized personnel can initiate payments or view audit logs. Due to the FedRAMP requirement, this must support Multi-Factor Authentication (MFA) and strictly defined roles.

**Detailed Requirements:**
1. **Role Definitions:**
    *   `Administrator`: Full system access.
    *   `FinancialOfficer`: Can approve payments and export data.
    *   `Auditor`: Read-only access to audit trails.
    *   `Operator`: Can initiate payment requests but not approve them.
2. **JWT Implementation:** Use OpenID Connect (OIDC) via Azure AD (Entra ID).
3. **Session Management:** Tokens must expire every 60 minutes with a mandatory re-authentication for "high-value" transactions (>$100k).
4. **Permission Matrix:** A database-driven mapping of roles to specific API endpoints.

**Technical Constraints:**
RBAC checks must be performed at the Middleware level in .NET, ensuring that unauthorized requests are rejected before reaching the Domain Core.

---

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Review

**Description:**
Financial controllers often work together on a single payment batch or invoice. This feature allows multiple users to edit a transaction record simultaneously without overwriting each other's changes.

**Detailed Requirements:**
1. **Concurrency Control:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs).
2. **WebSocket Integration:** Use Azure SignalR Service to push real-time updates to the frontend.
3. **Conflict Resolution UI:** When a "hard conflict" occurs (e.g., two users change the same amount to different values), the system must present a "Diff View" for the lead user to resolve.
4. **Presence Indicators:** Show which users are currently viewing or editing a specific record.

**Technical Constraints:**
Latency for updates must be $<200\text{ms}$ to prevent "ghosting" or visual stuttering for the users.

---

### 3.5 Webhook Integration Framework
**Priority:** Medium | **Status:** Blocked (Awaiting Legal Review)

**Description:**
A framework that allows third-party tools (like ERP systems or satellite telemetry monitors) to receive real-time notifications when payment milestones are met.

**Detailed Requirements:**
1. **Subscription Management:** A UI where users can register a URL and select events (e.g., `payment.succeeded`, `audit.failure`).
2. **Retry Logic:** Exponential backoff for failed delivery attempts (1m, 5m, 15m, 1h).
3. **Security:** Every webhook payload must be signed with an `X-Harbinger-Signature` header for the receiver to verify.
4. **Dead Letter Queue:** Failed webhooks after 5 attempts must be moved to a DLQ for manual intervention.

**Technical Constraints:**
The framework must be completely decoupled from the payment engine to ensure that a slow third-party webhook does not block the core transaction processing.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is required via Bearer Token in the Header.

### 4.1 `POST /payments/initiate`
Initiates a new payment request.
*   **Request Body:**
    ```json
    {
      "amount": 500000.00,
      "currency": "USD",
      "recipient_id": "ACC-99283",
      "milestone_id": "MILE-402",
      "description": "Satellite Housing Phase 1"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "transaction_id": "TXN-7712834",
      "status": "PendingApproval",
      "timestamp": "2026-07-15T10:00:00Z"
    }
    ```

### 4.2 `GET /payments/{transaction_id}`
Retrieves the current status and details of a transaction.
*   **Response (200 OK):**
    ```json
    {
      "transaction_id": "TXN-7712834",
      "amount": 500000.00,
      "status": "Approved",
      "audit_hash": "a3f2...e11",
      "approver": "Isadora Jensen"
    }
    ```

### 4.3 `POST /payments/{transaction_id}/approve`
Approves a pending transaction.
*   **Request Body:**
    ```json
    {
      "approver_id": "USER-101",
      "digital_signature": "SIG-88271"
    }
    ```
*   **Response (200 OK):**
    ```json
    { "status": "Processed", "completion_date": "2026-07-15T12:00:00Z" }
    ```

### 4.4 `GET /audit/verify`
Returns the integrity status of the global audit chain.
*   **Response (200 OK):**
    ```json
    {
      "integrity_status": "Valid",
      "last_verified_block": 450291,
      "verification_date": "2026-07-15T00:00:00Z"
    }
    ```

### 4.5 `POST /import/upload`
Uploads a file for auto-detection and processing.
*   **Request:** Multipart/form-data (File upload)
*   **Response (202 Accepted):**
    ```json
    { "job_id": "JOB-9921", "estimated_completion": "30s" }
    ```

### 4.6 `GET /import/status/{job_id}`
Checks the progress of a data import.
*   **Response (200 OK):**
    ```json
    { "job_id": "JOB-9921", "progress": "85%", "errors": 0 }
    ```

### 4.7 `POST /webhooks/subscribe`
Registers a new webhook endpoint.
*   **Request Body:**
    ```json
    {
      "url": "https://client-erp.com/webhooks",
      "events": ["payment.succeeded"]
    }
    ```
*   **Response (201 Created):**
    ```json
    { "subscription_id": "SUB-112", "secret": "whsec_abc123" }
    ```

### 4.8 `DELETE /webhooks/unsubscribe/{subscription_id}`
Removes a webhook subscription.
*   **Response (204 No Content):** (Empty)

---

## 5. DATABASE SCHEMA

The system utilizes an Azure SQL Database. All tables utilize `DATETIMEOFFSET` for global aerospace timestamps.

### 5.1 Tables and Relationships

1.  **`Users`**: Stores user profiles and credentials.
    *   `UserId` (PK, GUID), `Username` (String), `Email` (String), `PasswordHash` (String), `MfaSecret` (String).
2.  **`Roles`**: Defines system roles.
    *   `RoleId` (PK, Int), `RoleName` (String - e.g., "Administrator").
3.  **`UserRoles`**: Junction table for RBAC.
    *   `UserId` (FK), `RoleId` (FK).
4.  **`Accounts`**: Financial accounts for clients.
    *   `AccountId` (PK, GUID), `AccountName` (String), `Balance` (Decimal 19,4), `Currency` (String 3).
5.  **`Transactions`**: The primary ledger.
    *   `TransactionId` (PK, GUID), `SourceAccountId` (FK), `DestAccountId` (FK), `Amount` (Decimal 19,4), `Status` (Int), `CreatedAt` (DateTimeOffset).
6.  **`AuditLogs`**: The tamper-evident chain.
    *   `LogId` (PK, BigInt), `TransactionId` (FK), `PreviousHash` (String), `CurrentHash` (String), `Payload` (JSON), `Timestamp` (DateTimeOffset).
7.  **`Milestones`**: Aerospace-specific payment triggers.
    *   `MilestoneId` (PK, GUID), `ProjectName` (String), `TriggerCondition` (String), `Amount` (Decimal).
8.  **`ImportJobs`**: Tracking for data ingestion.
    *   `JobId` (PK, GUID), `UserId` (FK), `FileName` (String), `Status` (String), `RowsProcessed` (Int).
9.  **`WebhookSubscriptions`**: External integration settings.
    *   `SubscriptionId` (PK, GUID), `TargetUrl` (String), `Secret` (String), `IsActive` (Bit).
10. **`WebhookEvents`**: Log of every single webhook attempt.
    *   `EventId` (PK, BigInt), `SubscriptionId` (FK), `Payload` (JSON), `ResponseCode` (Int), `AttemptCount` (Int).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Harbinger utilizes three distinct environments to ensure stability and FedRAMP compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Rapid iteration and feature development.
*   **Infrastructure:** Low-cost Azure Function (Consumption Plan), Azure SQL (Basic Tier).
*   **Deployment:** Automatic trigger on merge to `develop` branch.
*   **Data:** Seeded with anonymized mock data.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Pre-production validation and QA.
*   **Infrastructure:** Mirror of Production (Standard Plan), Azure SQL (General Purpose).
*   **Deployment:** Triggered on merge to `release` branch.
*   **Data:** Sanitized production snapshots.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live client operations.
*   **Infrastructure:** Azure Kubernetes Service (AKS) with auto-scaling, Azure SQL (Hyperscale), Geo-redundant storage.
*   **Deployment:** Rolling deployments via GitLab CI with a 20% canary rollout.
*   **Data:** Live financial data; encrypted at rest and in transit.

### 6.2 CI/CD Pipeline
The pipeline is managed in GitLab CI:
1.  **Build:** `.NET build` $\rightarrow$ Unit Tests $\rightarrow$ Static Analysis (SonarQube).
2.  **Package:** Dockerize the application $\rightarrow$ Push to Azure Container Registry (ACR).
3.  **Deploy:** Helm chart application to AKS $\rightarrow$ Smoke tests $\rightarrow$ Traffic shift.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Approach:** Every domain service must have 90% code coverage.
*   **Tooling:** xUnit and Moq.
*   **Focus:** Business logic in the Core, ensuring that payment calculations and hash chains are mathematically correct.

### 7.2 Integration Testing
*   **Approach:** Test the "Adapters" against real (or containerized) infrastructure.
*   **Tooling:** TestContainers for Azure SQL.
*   **Focus:** Database migrations, API endpoint connectivity, and Azure Key Vault secret retrieval.

### 7.3 End-to-End (E2E) Testing
*   **Approach:** Simulate a full user journey (e.g., "Create User $\rightarrow$ Upload File $\rightarrow$ Approve Payment $\rightarrow$ Verify Audit Log").
*   **Tooling:** Playwright for frontend/API orchestration.
*   **Focus:** User experience, race conditions in collaborative editing, and FedRAMP authentication flows.

### 7.4 Performance Testing
*   **Target:** 10x current capacity.
*   **Tooling:** JMeter.
*   **Metric:** Throughput must sustain 1,000 transactions per second with a $p99$ latency of $<200\text{ms}$.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | High | Accept risk; maintain weekly updates to the executive board to ensure broad visibility. |
| R-02 | Performance requirements (10x) exceed budget | Medium | Critical | Engage external consultant for an independent assessment of the SQL Hyperscale tuning. |
| R-03 | FedRAMP authorization failure | Low | Critical | Follow NIST 800-53 guidelines strictly; use Azure Government cloud regions. |
| R-04 | Legal review of DPA delays webhook launch | High | Medium | Block feature development on webhooks; pivot team focus to Audit Trail refinement. |
| R-05 | Technical debt (God Class) causes system crash | Medium | Medium | Allocate 20% of each sprint to refactoring the `AuthLoggingEmailSvc` class. |

---

## 9. TIMELINE AND PHASES

### Phase 1: Foundation (Now – 2026-07-15)
*   **Focus:** Infrastructure setup and core engine development.
*   **Dependencies:** FedRAMP region provisioning.
*   **Critical Path:** Audit Trail $\rightarrow$ RBAC $\rightarrow$ Performance Tuning.
*   **Milestone 1:** Performance benchmarks met (Target: 2026-07-15).

### Phase 2: Client Readiness (2026-07-16 – 2026-09-15)
*   **Focus:** Data Import/Export and UX polishing.
*   **Dependencies:** Legal review of Data Processing Agreement (DPA).
*   **Critical Path:** Import Engine $\rightarrow$ UX Research $\rightarrow$ Beta Testing.
*   **Milestone 2:** First paying customer onboarded (Target: 2026-09-15).

### Phase 3: Scaling & Optimization (2026-09-16 – 2026-11-15)
*   **Focus:** Collaborative editing and Webhooks.
*   **Dependencies:** SignalR scaling.
*   **Critical Path:** Conflict Resolution $\rightarrow$ Webhook Framework.
*   **Milestone 3:** Internal alpha release (Target: 2026-11-15).

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment
**Date:** 2023-11-05  
**Attendees:** Isadora Jensen, Meera Nakamura, Ira Stein, Kian Oduya  

**Discussion:**
The team discussed the "God class" problem. Kian noted that `AuthLoggingEmailSvc.cs` has grown to 3,000 lines and is becoming a bottleneck for merges. Isadora insisted that the hexagonal architecture must be strictly enforced to prevent this from happening in the new modules.

**Decisions:**
- All new logic must be placed in the Domain Core; no logic in the Azure Function triggers.
- The God class will be refactored incrementally rather than in one "big bang" rewrite to avoid regressions.

**Action Items:**
- [Kian] Create a refactoring plan for the God class. (Due: 2023-11-12)
- [Isadora] Define the specific FedRAMP compliance checklist. (Due: 2023-11-15)

---

### Meeting 2: Budget and Performance Review
**Date:** 2023-12-10  
**Attendees:** Isadora Jensen, Finance Representative, Kian Oduya  

**Discussion:**
Finance questioned the cost of the Azure SQL Hyperscale tier. Isadora argued that the 10x performance requirement necessitates this tier. There was a heated debate regarding the $150k budget. The team concluded that we cannot afford an external DevOps engineer and Kian must handle the GitLab CI pipelines.

**Decisions:**
- Budget is capped at $150,000.00; no additional headcount.
- We will use a specialized external consultant (one-time fee) to verify the performance benchmarks.

**Action Items:**
- [Isadora] Source a consultant for the performance audit. (Due: 2024-01-05)
- [Kian] Optimize current query plans to reduce DTU consumption. (Due: 2024-01-10)

---

### Meeting 3: UX and Collaborative Editing
**Date:** 2024-01-20  
**Attendees:** Meera Nakamura, Ira Stein, Isadora Jensen  

**Discussion:**
Ira presented research showing that financial controllers often "clash" when editing the same payment batch. Meera suggested using SignalR for real-time presence. The team debated between OT and CRDTs for conflict resolution. Given the complexity of financial data, soon-to-be-decided "Last Write Wins" was rejected in favor of a "Manual Resolution" UI.

**Decisions:**
- Implement a "Diff View" for conflict resolution.
- Priority for collaborative editing is set to "Medium" as it is not a launch blocker.

**Action Items:**
- [Ira] Create wireframes for the Conflict Resolution screen. (Due: 2024-02-01)
- [Meera] Prototype the SignalR connection logic. (Due: 2024-02-15)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000.00

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $90,000.00 | Internal labor allocation for solo dev and part-time support. |
| **Infrastructure** | $30,000.00 | Azure SQL Hyperscale, Azure Functions, AKS, Key Vault. |
| **Tools & Licensing** | $10,000.00 | GitLab Premium, SonarQube, Playwright Enterprise. |
| **External Consultant** | $15,000.00 | Performance assessment and FedRAMP gap analysis. |
| **Contingency** | $5,000.00 | Emergency buffer for unexpected API cost overruns. |

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (CRDTs)
For the collaborative editing feature, Harbinger will implement a LWW-Element-Set (Last-Write-Wins) for simple fields and a Sequence-based CRDT for the "Notes" section of payments. 
*   **State Vector:** Each client maintains a vector clock to track the causality of edits.
*   **Merge Function:** When two states diverge, the merge function compares the vector clocks. If timestamps are identical, the system defaults to the user with the higher `RoleId` (Administrator $\rightarrow$ Financial Officer $\rightarrow$ Operator).

### Appendix B: FedRAMP Authorization Mapping
To meet FedRAMP High requirements, the following mappings are applied:
1.  **AC-2 (Account Management):** Handled by Azure AD Entra ID with mandatory MFA.
2.  **AU-2 (Audit Events):** Handled by the `AuditLogs` table and WORM storage.
3.  **SC-8 (Transmission Confidentiality):** All traffic is forced over TLS 1.3.
4.  **IA-2 (Identification and Authentication):** Implementation of OIDC and JWT with short-lived tokens.