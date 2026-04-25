# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Date:** October 24, 2025  
**Owner:** Xena Park, Tech Lead  
**Classification:** Confidential – Duskfall Inc.

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Glacier represents a strategic pivot for Duskfall Inc., marking the company's entry into a new product vertical specifically engineered for the high-end retail sector. The project involves the deployment of a sophisticated machine learning (ML) model designed to automate complex retail logistics and demand forecasting. Unlike previous general-market offerings, Glacier is driven by a specific, high-value enterprise client engagement. This client has committed to a contractual annual recurring revenue (ARR) of $2,000,000, provided the system meets rigorous performance and security benchmarks.

**Business Justification**  
The retail industry is currently facing an unprecedented crisis in manual processing overhead. The target client currently employs hundreds of analysts to manually reconcile inventory drifts and forecast seasonal demand. By deploying the Glacier ML model, Duskfall Inc. aims to transition this process from manual human intervention to automated, model-driven decision-making. The primary value proposition is the drastic reduction of "operational friction"—reducing the time between data ingestion and actionable insight.

**ROI Projection**  
The financial viability of Project Glacier is anchored by the $2M annual contract. With a solo developer managing the core implementation (supported by a specialized project team), the operational expenditure (OpEx) is optimized. 

*   **Direct Revenue:** $2,000,000 / year.
*   **Projected OpEx:** Estimated at $450,000 (Infrastructure + Personnel overhead).
*   **Net Profit Margin:** Approximately 77.5% post-launch.
*   **Operational ROI:** The client expects a 50% reduction in manual processing time. If the client reduces their manual workforce by 20 FTEs at an average cost of $70k/year, the client realizes $1.4M in annual savings, justifying the $2M price point through efficiency gains and error reduction.

**Strategic Alignment**  
Glacier serves as a "lighthouse project." Success here allows Duskfall Inc. to productize the ML deployment framework for other retail giants, potentially scaling the vertical from a single client to a multi-million dollar business unit. The commitment to SOC 2 Type II compliance ensures that the product is "Enterprise Ready" from day one, removing the primary barrier to entry for Fortune 500 retail firms.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
Project Glacier is built on a unified Microsoft ecosystem to ensure seamless integration, rapid deployment, and minimized latency between the application layer and the data store.

*   **Language/Framework:** C# / .NET 8 (LTS)
*   **Compute:** Azure Functions (Serverless)
*   **Database:** Azure SQL Database (Hyperscale tier)
*   **Orchestration:** Azure API Management (APIM)
*   **Storage:** Azure Blob Storage (Hot/Cool tiers)
*   **Content Delivery:** Azure Front Door / CDN
*   **Security:** Azure Key Vault, Microsoft Entra ID (formerly Azure AD)

### 2.2 Architectural Pattern
The system utilizes a **Serverless Micro-Kernel Architecture**. Instead of a monolithic API, the system is decomposed into discrete Azure Functions triggered by the API Gateway. This allows for independent scaling of high-load endpoints (like the ML inference trigger) without scaling the entire management suite.

### 2.3 ASCII Architecture Diagram
```text
[ Client Request ] 
       |
       v
[ Azure Front Door / CDN ] <--- (Static Assets / Cached Responses)
       |
       v
[ Azure API Management (APIM) ] <--- (Authentication, Throttling, Versioning)
       |
       +---------------------------------------------------+
       |                      |                          |
       v                      v                          v
[ Func: Data Ingest ]   [ Func: ML Inference ]    [ Func: Admin/Audit ]
       |                      |                          |
       +-----------+----------+------------+-------------+
                   |                      |
                   v                      v
         [ Azure SQL Database ]    [ Azure Blob Storage ]
         (Multi-tenant Schema)     (ML Models & User Files)
                   |                      |
                   +----------------------+
                               |
                               v
                      [ Azure Key Vault ]
                      (Secrets & Certs)
```

### 2.4 Data Flow Logic
1.  **Ingestion:** Data is uploaded via the CDN-backed upload function.
2.  **Validation:** The system triggers a virus scan and format detection.
3.  **Isolation:** The `TenantId` is injected into every SQL query to ensure data isolation.
4.  **Processing:** The Azure Function passes the cleaned data to the ML model (hosted as a separate containerized service or optimized function).
5.  **Persistence:** Results are written to Azure SQL and an immutable log is created in the audit trail.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-Tenant Data Isolation (Priority: Critical)
**Status:** In Progress | **Blocker:** Launch Blocker

**Description:** 
Project Glacier must support multiple retail clients (tenants) on a shared infrastructure while guaranteeing that no tenant can ever access another tenant's data. This is a "Hard Isolation" requirement.

**Technical Implementation:**
The system will employ a **Row-Level Security (RLS)** strategy within Azure SQL. Every table in the database will contain a `TenantId` column (GUID). 
- **Contextual Filtering:** Upon authentication via Entra ID, the API Gateway extracts the `tenant_id` claim from the JWT. 
- **Session Context:** The Azure Function will execute `EXEC sp_set_session_context 'TenantId', @TenantId` before any data operation.
- **Security Policies:** A SQL Server Security Policy will be applied to all tables: `CREATE SECURITY POLICY TenantFilter ADD FILTER PREDICATE dbo.fn_securitypredicate(TenantId) ON dbo.RetailData`.

**Success Criteria:**
- Penetration tests must confirm that a modified JWT cannot access data from a different `TenantId`.
- Zero cross-tenant leakage during integration testing.

---

### 3.2 Data Import/Export with Format Auto-Detection (Priority: Critical)
**Status:** Blocked | **Blocker:** Launch Blocker

**Description:** 
Retailers provide data in disparate formats (CSV, JSON, XML, Parquet). Glacier must automatically detect the file type and map it to the internal canonical schema without manual user configuration for every upload.

**Technical Implementation:**
- **Magic Number Analysis:** The system will read the first 2048 bytes of the file stream to identify the file signature (Magic Numbers).
- **Schema Inference:** For CSV/JSON, the system will utilize a "probabilistic sampling" approach, scanning the first 100 rows to determine data types (Integer, Float, DateTime, String).
- **Mapping Engine:** A C#-based mapping layer will translate external headers (e.g., "SKU_ID" or "Prod_Num") to the internal `ProductCode` field using a weighted Levenshtein distance algorithm.
- **Export Engine:** Users can request an export in any supported format. The system will trigger a background Azure Function (Queue Trigger) to generate the file and place it in a secure Blob Storage container with a SAS (Shared Access Signature) token.

**Dependencies:** 
Currently blocked by the "Data Schema Team" (external dependency), which is 3 weeks behind on providing the final retail canonical model.

---

### 3.3 File Upload with Virus Scanning and CDN Distribution (Priority: High)
**Status:** Complete

**Description:** 
High-volume upload of product imagery and dataset files, ensured to be malware-free and delivered with low latency globally.

**Technical Implementation:**
- **Upload Path:** Client $\rightarrow$ Azure Front Door $\rightarrow$ Azure Function (Upload) $\rightarrow$ Blob Storage.
- **Virus Scanning:** Integration with an Azure-native virus scanning solution (e.g., Defender for Storage). Every file is scanned upon the `BlobCreated` event. If a threat is detected, the file is moved to a quarantine container and the user is notified.
- **Distribution:** Static assets and ML-generated reports are cached at the Azure CDN edge locations.
- **Chunking:** Supports multipart uploads for files larger than 100MB to prevent timeout in serverless functions.

**Validation:**
Verified via successful upload of 1GB datasets and simulated malware injection (EICAR test file), which was successfully quarantined.

---

### 3.4 Audit Trail Logging with Tamper-Evident Storage (Priority: Medium)
**Status:** In Progress

**Description:** 
To meet SOC 2 Type II requirements, every modification to the system's state must be logged in a way that proves the logs have not been altered by an administrator.

**Technical Implementation:**
- **Event Sourcing:** All "Write" operations are captured as events.
- **Hashing Chain:** Each log entry contains a SHA-256 hash of the current record concatenated with the hash of the previous record (a blockchain-lite approach).
- **Immutable Storage:** Logs are written to Azure Blob Storage with a "WORM" (Write Once, Read Many) policy enabled.
- **Audit Scope:** Captures `Timestamp`, `UserIdentity`, `Action`, `ResourceId`, `OldValue`, and `NewValue`.

**Success Criteria:**
- Audit logs must be recoverable and verifiable via a checksum script.
- Logs must be retained for 7 years per retail compliance standards.

---

### 3.5 Customer-Facing API with Versioning and Sandbox (Priority: Low)
**Status:** In Progress

**Description:** 
A public-facing REST API allowing the client to integrate Glacier's ML insights into their own dashboards.

**Technical Implementation:**
- **Versioning:** URI-based versioning (e.g., `/v1/insights`, `/v2/insights`).
- **Sandbox Environment:** A separate Azure Resource Group mirroring production but populated with synthetic "dummy" data. This allows the client to test integrations without impacting production metrics.
- **Throttling:** API Management (APIM) policies limit requests to 1,000 calls per minute per tenant.
- **Documentation:** Swagger/OpenAPI 3.0 specifications hosted via a developer portal.

**Success Criteria:**
- Ability to switch between `sandbox.glacier.duskfall.com` and `api.glacier.duskfall.com` via header configuration.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token (JWT) in the Authorization header. Base URL: `https://api.glacier.duskfall.com/v1`

### 4.1 `POST /data/upload`
- **Purpose:** Upload a dataset file for ML processing.
- **Request:** `multipart/form-data` (File: `blob`, TenantId: `string`)
- **Response:** `202 Accepted`
- **Example Response:**
  ```json
  { "jobId": "job_88231", "status": "Scanning", "estimatedTime": "45s" }
  ```

### 4.2 `GET /data/upload/status/{jobId}`
- **Purpose:** Check the status of a file upload/scan.
- **Request:** Path parameter `{jobId}`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  { "jobId": "job_88231", "status": "Completed", "virusScan": "Clean" }
  ```

### 4.3 `POST /ml/inference/predict`
- **Purpose:** Trigger the ML model to generate a forecast based on uploaded data.
- **Request:** `application/json` `{ "datasetId": "ds_991", "horizonDays": 30 }`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  { "predictionId": "pred_112", "forecast": [ {"date": "2026-01-01", "value": 450.5} ] }
  ```

### 4.4 `GET /ml/inference/results/{predictionId}`
- **Purpose:** Retrieve a specific prediction result.
- **Request:** Path parameter `{predictionId}`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  { "predictionId": "pred_112", "confidence": 0.94, "data": [...] }
  ```

### 4.5 `GET /audit/logs`
- **Purpose:** Retrieve a list of all actions taken within the tenant.
- **Request:** Query params `startDate`, `endDate`, `userId`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  [ { "timestamp": "2026-05-01T10:00Z", "action": "FILE_UPLOAD", "user": "admin_1" } ]
  ```

### 4.6 `POST /tenants/config`
- **Purpose:** Update tenant-specific ML hyperparameters.
- **Request:** `application/json` `{ "learningRate": 0.01, "smoothing": "exponential" }`
- **Response:** `204 No Content`

### 4.7 `GET /health`
- **Purpose:** System heartbeat check.
- **Request:** None
- **Response:** `200 OK`
- **Example Response:**
  ```json
  { "status": "Healthy", "uptime": "14d 2h", "version": "1.0.4" }
  ```

### 4.8 `DELETE /data/dataset/{datasetId}`
- **Purpose:** Hard delete a dataset (triggers audit log).
- **Request:** Path parameter `{datasetId}`
- **Response:** `200 OK`
- **Example Response:**
  ```json
  { "message": "Dataset permanently removed", "auditId": "log_772" }
  ```

---

## 5. DATABASE SCHEMA

The system utilizes a relational model in Azure SQL. All tables use `UniqueIdentifier` (GUID) for primary keys to support distributed generation and multi-tenancy.

### 5.1 Table Definitions

1.  **`Tenants`**
    - `TenantId` (PK, GUID)
    - `TenantName` (NVARCHAR 255)
    - `SubscriptionTier` (INT)
    - `CreatedAt` (DateTimeOffset)
    - `IsActive` (BIT)

2.  **`Users`**
    - `UserId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `Email` (NVARCHAR 255)
    - `PasswordHash` (VARBINARY 64)
    - `Role` (NVARCHAR 50)

3.  **`Datasets`**
    - `DatasetId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `BlobUri` (NVARCHAR 2048)
    - `Format` (NVARCHAR 20)
    - `RowCount` (BIGINT)
    - `UploadDate` (DateTimeOffset)

4.  **`ML_Models`**
    - `ModelId` (PK, GUID)
    - `Version` (NVARCHAR 20)
    - `HyperparameterJson` (NVARCHAR(MAX))
    - `TrainingDate` (DateTimeOffset)
    - `AccuracyMetric` (FLOAT)

5.  **`InferenceJobs`**
    - `JobId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `DatasetId` (FK $\rightarrow$ Datasets)
    - `ModelId` (FK $\rightarrow$ ML_Models)
    - `Status` (NVARCHAR 20)
    - `StartedAt` (DateTimeOffset)
    - `CompletedAt` (DateTimeOffset)

6.  **`Predictions`**
    - `PredictionId` (PK, GUID)
    - `JobId` (FK $\rightarrow$ InferenceJobs)
    - `ResultJson` (NVARCHAR(MAX))
    - `ConfidenceScore` (FLOAT)

7.  **`AuditLogs`**
    - `LogId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `UserId` (FK $\rightarrow$ Users)
    - `Action` (NVARCHAR 100)
    - `Payload` (NVARCHAR(MAX))
    - `HashChain` (VARBINARY 32)
    - `Timestamp` (DateTimeOffset)

8.  **`FileMetadata`**
    - `FileId` (PK, GUID)
    - `DatasetId` (FK $\rightarrow$ Datasets)
    - `OriginalFileName` (NVARCHAR 512)
    - `FileSize` (BIGINT)
    - `VirusScanStatus` (NVARCHAR 20)

9.  **`ApiKeys`**
    - `KeyId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `HashedKey` (VARBINARY 64)
    - `ExpiresAt` (DateTimeOffset)

10. **`SandboxConfigs`**
    - `ConfigId` (PK, GUID)
    - `TenantId` (FK $\rightarrow$ Tenants)
    - `IsMockDataEnabled` (BIT)
    - `MockLatencyMs` (INT)

### 5.2 Relationships
- **One-to-Many:** `Tenants` $\rightarrow$ `Users`, `Datasets`, `InferenceJobs`, `AuditLogs`.
- **One-to-Many:** `Datasets` $\rightarrow$ `FileMetadata`.
- **One-to-One:** `InferenceJobs` $\rightarrow$ `Predictions`.
- **Many-to-One:** `InferenceJobs` $\rightarrow$ `ML_Models`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Glacier employs a three-tier environment strategy to ensure stability.

| Environment | Purpose | Deployment Trigger | Data Source |
| :--- | :--- | :--- | :--- |
| **Dev** | Active development / Unit Testing | Merge to `develop` branch | Mock Data / LocalDB |
| **Staging** | Integration Testing / Client UAT | Merge to `release` branch | Anonymized Production Snapshot |
| **Prod** | Enterprise Client Live System | Merge to `main` branch | Live Production SQL |

### 6.2 Continuous Deployment (CD) Pipeline
The project uses **GitHub Actions** integrated with **Azure DevOps**. 
- **Pipeline Flow:** $\text{Commit} \rightarrow \text{Pull Request} \rightarrow \text{CI Build} \rightarrow \text{Automated Tests} \rightarrow \text{Approval} \rightarrow \text{Deploy}$.
- **The "Merged PR" Rule:** Every merged PR into the `main` branch is automatically deployed to production. This requires a 100% pass rate on the integration test suite.

### 6.3 Infrastructure as Code (IaC)
The infrastructure is defined using **Bicep** files. This ensures that the Dev, Staging, and Prod environments are identical in configuration, preventing "it works on my machine" issues.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit and Moq.
- **Target:** All business logic within Azure Functions and Service Layers.
- **Coverage Goal:** 80% minimum line coverage.
- **Execution:** Runs on every push to the repository.

### 7.2 Integration Testing
- **Approach:** "Black-box" testing of the API Gateway.
- **Tooling:** Postman / Newman.
- **Focus:** Validating the interaction between the Azure Function, the SQL Database, and the Blob Storage.
- **Key Scenario:** Uploading a file $\rightarrow$ Checking virus scan $\rightarrow$ Triggering ML $\rightarrow$ Retrieving result.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Simulating the full user journey from the UI (provided by Gemma Oduya) to the back-end.
- **Tooling:** Playwright.
- **Focus:** Verifying that the "50% reduction in manual processing time" is technically achievable by measuring the time from file upload to result retrieval.

### 7.4 Security Testing
- **SOC 2 Validation:** Quarterly audits of the `AuditLogs` table to ensure no gaps in the hash chain.
- **Static Analysis:** Snyk used to scan for vulnerable NuGet packages.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements are 10x current capacity with no extra budget | High | Critical | Escalate to steering committee for additional funding (Compute upgrade). |
| R-02 | Team has no experience with C#/.NET/Azure stack | Medium | High | De-scope affected features if unresolved by Milestone 2 date. |
| R-03 | SOC 2 Compliance failure | Low | Critical | Engage external auditors for a "pre-audit" gap analysis in June 2026. |
| R-04 | ML Model Drift (Accuracy loss) | Medium | Medium | Implement a monthly model retraining pipeline with a human-in-the-loop check. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or contractual breach.
- **High:** Significant delay in milestone delivery.
- **Medium:** Feature degradation or minor delay.
- **Low:** Cosmetic or non-essential issues.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with hard-coded milestone dates.

### 9.1 Phase 1: Foundation (Jan 2026 - July 2026)
- Focus on multi-tenant isolation and core infrastructure.
- **Milestone 1: Security audit passed**
  - **Target Date:** 2026-07-15
  - **Criteria:** SOC 2 Type II readiness verification.

### 9.2 Phase 2: Optimization (July 2026 - Sept 2026)
- Focus on ML model tuning and throughput optimization.
- **Milestone 2: Performance benchmarks met**
  - **Target Date:** 2026-09-15
  - **Criteria:** p95 API response time < 200ms at peak load.

### 9.3 Phase 3: Completion (Sept 2026 - Nov 2026)
- Focus on the API sandbox and final data import/export features.
- **Milestone 3: MVP feature-complete**
  - **Target Date:** 2026-11-15
  - **Criteria:** All "Critical" and "High" priority features passing E2E tests.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Review (2025-11-12)
- **Attendees:** Xena, Zia, Hugo
- **Notes:**
  - Zia concerned about SQL latency.
  - Xena suggested Hyperscale tier.
  - Hugo asked about C# versions.
  - Decision: .NET 8.
  - Action: Zia to prototype RLS.

### Meeting 2: Blockers Sync (2026-02-05)
- **Attendees:** Xena, Gemma
- **Notes:**
  - Data Import blocked.
  - Other team is 3 weeks late.
  - Gemma needs mock data for UI.
  - Xena to email steering committee.
  - Decision: Use temporary JSON schema for mocks.

### Meeting 3: Budget & Risk Alignment (2026-04-20)
- **Attendees:** Xena, Zia, Hugo
- **Notes:**
  - Performance 10x higher than expected.
  - No budget for more RAM.
  - Xena to escalate.
  - Hugo struggling with Azure Functions.
  - Decision: Peer review every Wednesday.

---

## 11. BUDGET BREAKDOWN

The budget is released in tranches upon the successful completion of milestones.

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Solo Dev + Team Overhead | $320,000 | Salary, benefits, and management. |
| **Infrastructure** | Azure Consumption | $85,000 | Hyperscale SQL and Front Door. |
| **Tools/Licensing** | SOC 2 Audit + Software | $40,000 | Third-party auditors and IDE licenses. |
| **Contingency** | Performance Escalation | $5,000 | Reserved for emergency resource spikes. |
| **Total** | | **$450,000** | Total OpEx for the development phase. |

---

## 12. APPENDICES

### Appendix A: ML Model Inference Logic
The model is deployed as an ONNX (Open Neural Network Exchange) runtime within the Azure Function. This allows the C# code to execute the model with high efficiency without requiring a full Python environment. The input tensor consists of 42 features derived from the retail dataset, including `HistoricalSales`, `SeasonalityIndex`, and `PromotionFlag`.

### Appendix B: SOC 2 Type II Compliance Checklist
To achieve compliance, the following must be evidenced:
1.  **Access Control:** All production access is logged; no developer has direct access to production SQL.
2.  **Change Management:** Every change is linked to a JIRA ticket and a merged PR.
3.  **Availability:** 99.9% uptime SLA backed by Azure Availability Zones.
4.  **Confidentiality:** All data encrypted at rest using AES-256 and in transit using TLS 1.3.