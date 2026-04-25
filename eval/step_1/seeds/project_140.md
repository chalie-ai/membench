# PROJECT SPECIFICATION: PROJECT GANTRY
**Document Version:** 1.0.4  
**Status:** Formal Specification / Active Reference  
**Company:** Tundra Analytics  
**Date:** October 24, 2023  
**Project Lead:** Nyla Oduya (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

**Project Gantry** represents a strategic pivot for Tundra Analytics. While the company has a storied history in generalized data processing, Gantry is a greenfield venture specifically designed for the **Retail Industry**. This project marks the company's first entry into a specialized retail analytics market, aiming to provide a high-performance data pipeline and analytics platform that empowers retail operators to synchronize inventory, analyze sales velocity, and predict demand with granular precision.

**Business Justification**  
The retail sector is currently experiencing a massive transition toward "unified commerce," where online and offline channels must merge into a single source of truth. Current legacy systems in the mid-market retail space are fragmented, often relying on brittle ETL processes that fail during peak loads (e.g., Black Friday). Gantry addresses this by implementing a high-availability, offline-first architecture that ensures data integrity even in low-connectivity warehouse environments.

The strategic goal is to capture a significant share of the mid-sized retail market by offering a platform that is more agile than enterprise ERPs but more robust than basic SaaS dashboarding tools. By targeting government-adjacent retail contracts (e.g., military commissaries or state-run logistics), Gantry will utilize its FedRAMP authorization to create a competitive moat that other retail analytics startups cannot easily cross.

**ROI Projection**  
The total project budget is set at **$800,000**, which is deemed comfortable for a 6-month development cycle. The projected Return on Investment is calculated based on two primary drivers:
1. **Cost Reduction:** Through the optimization of data ingestion pipelines and the replacement of inefficient legacy middleware, we project a **35% reduction in cost per transaction**. Given an estimated volume of 50 million transactions per month across the target customer base, this translates to significant operational savings.
2. **User Acquisition:** The success metric for the first six months post-launch is **10,000 Monthly Active Users (MAU)**. Based on a projected Average Revenue Per User (ARPU) of $15/month for the base tier and $120/month for the enterprise tier, the platform is expected to reach a break-even point within 14 months of the 2026-03-15 launch date.

The long-term value proposition lies in the proprietary data indexing method developed for Gantry, which allows for near-instantaneous faceted filtering across petabytes of retail SKU data, providing a unique selling point (USP) for the "Advanced Search" feature set.

---

## 2. TECHNICAL ARCHITECTURE

Gantry is built upon a **Hexagonal Architecture (Ports and Adapters)**. This design choice is critical because Tundra Analytics is entering a new market; the business logic (the "Core") must remain isolated from the external technologies (the "Adapters") to allow for rapid pivoting without rewriting the entire codebase.

### 2.1 The Stack
- **Language/Framework:** Python 3.11 / Django 4.2 (LTS)
- **Primary Database:** PostgreSQL 15.4 (Relational data, transactional integrity)
- **Caching/Queue:** Redis 7.2 (Session management, task queuing via Celery)
- **Deployment:** AWS ECS (Elastic Container Service) using Fargate for serverless scaling.
- **Security Standard:** FedRAMP High Baseline (Required for government retail contracts).

### 2.2 Architectural Diagram (ASCII Description)

```text
[ EXTERNAL CLIENTS ] <--> [ API GATEWAY / AWS ALB ]
                                |
                                v
                _______________________________________
               |       ADAPTER LAYER (Infrastructure)  |
               |---------------------------------------|
               | [REST API] [SAML/OIDC] [AWS S3] [Redis]|
               |_______________________________________|
                                |
                                v
                _______________________________________
               |       PORT LAYER (Interfaces)         |
               |---------------------------------------|
               | [IUserRepository] [IReportService]     |
               | [IDataPipeline]   [ISyncManager]      |
               |_______________________________________|
                                |
                                v
                _______________________________________
               |       CORE DOMAIN (Business Logic)    |
               |---------------------------------------|
               | [RetailAnalyticsEngine]                |
               | [InventoryAggregator]                  |
               | [UserAuthDomain]                      |
               |_______________________________________|
                                |
                                v
                _______________________________________
               |       ADAPTER LAYER (Persistence)      |
               |---------------------------------------|
               | [PostgreSQL Adapter] [File System API] |
               |_______________________________________|
```

### 2.3 Design Philosophy
The "Core" contains the business rules of retail analytics. For example, the logic that determines if a SKU is "under-stocked" exists only in the Core. The "Port" defines how that data is requested. The "Adapter" handles the actual SQL query to PostgreSQL. If the team decides to move from PostgreSQL to a NoSQL solution for specific telemetry data, only the Adapter changes; the Core remains untouched.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Complete

**Description:**  
Retail environments (warehouses, rural storefronts) often suffer from intermittent connectivity. This feature allows users to perform data entry and analytics queries while offline, caching all mutations locally and synchronizing them once a connection is re-established.

**Technical Implementation:**  
Gantry utilizes a "Local-First" approach using IndexedDB in the browser and a synchronization engine on the backend. Every record is assigned a Global Unique Identifier (GUID) and a Vector Clock to handle conflict resolution. 

When a user is offline:
1. All writes are directed to a local `PendingSync` queue.
2. Read operations pull from a local cache of the most recently synced state.
3. A Service Worker monitors the `navigator.onLine` event.

Upon reconnection:
1. The system initiates a "Handshake" with the `/api/v1/sync/handshake` endpoint.
2. The client sends a batch of mutations.
3. The server uses a "Last-Write-Wins" (LWW) strategy unless the record is flagged as "Critical," in which case a manual merge conflict is triggered for the user.
4. Background sync is managed via a Web Worker to ensure the UI remains responsive at 60fps.

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**  
Retail managers require automated snapshots of performance. This feature allows for the generation of complex PDF and CSV reports based on custom date ranges and filtered datasets, delivered via email or S3 bucket.

**Technical Implementation:**  
The report engine is decoupled from the main request-response cycle to prevent timeouts. 
- **Generation:** We use `WeasyPrint` for PDF rendering and `Pandas` for CSV aggregation.
- **Scheduling:** A Celery Beat scheduler triggers tasks based on a Cron expression stored in the `ReportSchedule` table.
- **Pipeline:** 
    1. `Trigger` $\rightarrow$ `Task Queue (Redis)` $\rightarrow$ `Worker (ECS)` $\rightarrow$ `Data Fetch (PostgreSQL)` $\rightarrow$ `PDF/CSV Rendering` $\rightarrow$ `Storage (S3)` $\rightarrow$ `Notification (SES)`.
- **Delivery:** Users can specify delivery cadence (Daily, Weekly, Monthly) and recipients. The system generates a signed S3 URL with a 7-day expiration period for secure access.

### 3.3 SSO Integration (SAML and OIDC)
**Priority:** High | **Status:** Not Started

**Description:**  
For enterprise and government retail clients, manual password management is a security risk. Gantry must integrate with Single Sign-On (SSO) providers such as Okta, Azure AD, and Google Workspace.

**Technical Implementation:**  
The implementation will utilize the `python-social-auth` and `django-allauth` libraries.
- **SAML 2.0:** The system will act as a Service Provider (SP). We will provide the client with a Metadata XML file containing our Assertion Consumer Service (ACS) URL.
- **OIDC:** Integration will follow the Authorization Code Flow with PKCE (Proof Key for Code Exchange) to ensure security for the frontend application.
- **User Provisioning:** "Just-in-Time" (JIT) provisioning will be implemented; if a user authenticates via SSO and does not exist in the Gantry database, a profile will be created automatically based on the SAML assertions (Email, Role, Department).

### 3.4 Advanced Search with Faceted Filtering
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:**  
Users need to find specific products or transactions across millions of rows. This requires more than simple SQL `LIKE` queries; it requires full-text indexing and the ability to "drill down" via facets (e.g., Filter by Region $\rightarrow$ Filter by Category $\rightarrow$ Filter by Price Range).

**Technical Implementation:**  
We will implement an ElasticSearch cluster alongside PostgreSQL.
- **Indexing:** A "Change Data Capture" (CDC) pipeline will be built using Debezium to stream updates from PostgreSQL to ElasticSearch in real-time.
- **Faceted Search:** Using ElasticSearch "Aggregations," the API will return not just the results, but the count of documents for each facet (e.g., "Electronics (450)").
- **Indexing Strategy:** We will implement "N-gram" tokenization to support partial matches (e.g., searching for "Sams" returns "Samsung").

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:**  
Retailers often migrate from legacy CSV, XML, or JSON formats. This feature allows users to upload files without specifying the format; Gantry will "sniff" the file header and structure to determine the correct import logic.

**Technical Implementation:**  
- **Auto-Detection:** The system will use a "probabilistic parser" that checks for common delimiters (commas, tabs, semicolons) and magic bytes (e.g., `0x7B` for JSON).
- **Mapping Engine:** A UI-based mapping tool will allow users to map their source columns (e.g., "Prod_ID") to Gantry's internal schema ("sku_id").
- **Validation:** Imports will be processed in a "Staging Table." A validation pass will check for data type mismatches and orphaned foreign keys before committing the data to the production tables via a single transaction.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests/responses use `application/json`.

### 4.1 `POST /auth/login`
Authenticates a user and returns a JWT.
- **Request:** `{"username": "user123", "password": "password123"}`
- **Response:** `{"token": "eyJhbG...", "expires_at": "2023-10-24T12:00:00Z"}`

### 4.2 `GET /analytics/summary`
Retrieves a high-level summary of retail performance.
- **Params:** `?start_date=2023-01-01&end_date=2023-01-31`
- **Response:** `{"total_revenue": 450000.00, "transaction_count": 1200, "avg_order_value": 375.00}`

### 4.3 `POST /sync/push`
Pushes offline-cached data to the server.
- **Request:** `{"batch_id": "b-992", "payload": [{"id": "uuid-1", "action": "update", "data": {...}}]}`
- **Response:** `{"status": "success", "synced_count": 42, "conflicts": []}`

### 4.4 `GET /reports/schedule/{id}`
Retrieves details of a scheduled report.
- **Response:** `{"id": 101, "name": "Weekly Inventory", "cron": "0 0 * * 0", "format": "PDF"}`

### 4.5 `POST /reports/generate`
Triggers an immediate manual report generation.
- **Request:** `{"report_type": "sales_velocity", "filters": {"region": "North"}`}`
- **Response:** `{"job_id": "job-abc-123", "status": "queued"}`

### 4.6 `GET /inventory/search`
Performs a faceted search on the product catalog.
- **Params:** `?q=wireless headphones&category=electronics`
- **Response:** `{"results": [...], "facets": {"brand": {"Sony": 10, "Bose": 5}}}`

### 4.7 `POST /import/upload`
Uploads a data file for auto-detection and processing.
- **Request:** Multipart form data (File upload)
- **Response:** `{"upload_id": "up-445", "status": "analyzing"}`

### 4.8 `PUT /user/profile`
Updates user settings and preferences.
- **Request:** `{"timezone": "UTC-5", "notifications_enabled": true}`
- **Response:** `{"status": "updated"}`

---

## 5. DATABASE SCHEMA

The database is implemented in PostgreSQL 15.4. All tables use UUIDs for primary keys to facilitate offline synchronization and merge operations.

### 5.1 Tables and Relationships

1. **`Users`**: Core identity table.
   - `user_id` (UUID, PK), `email` (VARCHAR, Unique), `password_hash` (TEXT), `sso_provider` (VARCHAR), `created_at` (TIMESTAMP).
2. **`Organizations`**: Multi-tenant isolation.
   - `org_id` (UUID, PK), `org_name` (VARCHAR), `billing_plan` (VARCHAR), `fedramp_status` (BOOLEAN).
3. **`UserOrganizationMap`**: Many-to-Many link between users and orgs.
   - `user_id` (FK), `org_id` (FK), `role` (VARCHAR: Admin, Viewer, Editor).
4. **`Products`**: Retail SKU catalog.
   - `product_id` (UUID, PK), `org_id` (FK), `sku` (VARCHAR, Unique), `name` (VARCHAR), `category` (VARCHAR), `unit_price` (DECIMAL).
5. **`Inventory`**: Stock levels across locations.
   - `inv_id` (UUID, PK), `product_id` (FK), `location_id` (FK), `quantity` (INT), `last_updated` (TIMESTAMP).
6. **`Locations`**: Physical store or warehouse data.
   - `location_id` (UUID, PK), `org_id` (FK), `address` (TEXT), `location_type` (VARCHAR: Store, DC).
7. **`Transactions`**: Sales records.
   - `tx_id` (UUID, PK), `product_id` (FK), `location_id` (FK), `quantity` (INT), `total_amount` (DECIMAL), `tx_timestamp` (TIMESTAMP).
8. **`ReportSchedules`**: Automation metadata.
   - `schedule_id` (UUID, PK), `org_id` (FK), `cron_expression` (VARCHAR), `format` (VARCHAR: PDF, CSV), `delivery_email` (VARCHAR).
9. **`SyncLog`**: Tracking offline sync history.
   - `sync_id` (UUID, PK), `user_id` (FK), `device_id` (VARCHAR), `last_sync_timestamp` (TIMESTAMP).
10. **`AuditLogs`**: FedRAMP required logging.
    - `log_id` (BIGINT, PK), `user_id` (FK), `action` (TEXT), `ip_address` (INET), `timestamp` (TIMESTAMP).

**Relationships:**
- `Organizations` $\rightarrow$ `Products` (1:N)
- `Organizations` $\rightarrow$ `Locations` (1:N)
- `Products` $\rightarrow$ `Inventory` (1:N)
- `Locations` $\rightarrow$ `Inventory` (1:N)
- `Products` $\rightarrow$ `Transactions` (1:N)
- `Users` $\rightarrow$ `UserOrganizationMap` $\rightarrow$ `Organizations` (M:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry utilizes three distinct environments to ensure stability. Every merged Pull Request (PR) automatically deploys to production following a successful pass through the pipeline.

| Environment | Purpose | Infrastructure | Access |
| :--- | :--- | :--- | :--- |
| **Development** | Feature iteration | ECS Fargate (Small), Shared RDS | All Devs |
| **Staging** | Pre-prod / QA | ECS Fargate (Medium), Mirror of Prod RDS | QA, Project Lead |
| **Production** | Live Client Traffic | ECS Fargate (Auto-scaling), Multi-AZ RDS | SRE, Project Lead |

### 6.2 Continuous Deployment (CD) Pipeline
1. **Commit:** Developer pushes to `main`.
2. **CI Stage:** GitHub Actions runs `pytest` and `flake8`.
3. **Build Stage:** Docker image is built and pushed to AWS ECR.
4. **Deploy Stage:** AWS ECS updates the service using a "Rolling Update" strategy (max surge 20%, max unavailable 0).
5. **Smoke Test:** A health check endpoint `/health` must return 200 OK for the deployment to be finalized.

### 6.3 Infrastructure Specifics
- **AWS Region:** `us-gov-west-1` (Required for FedRAMP).
- **VPC:** Private subnets for RDS and Redis; public subnets for the ALB (Application Load Balancer).
- **Storage:** S3 buckets with AES-256 encryption at rest for all generated reports.

---

## 7. TESTING STRATEGY

To mitigate the risk of the team's unfamiliarity with the stack, Gantry employs a "Testing Pyramid" approach.

### 7.1 Unit Testing
- **Focus:** Individual business logic functions in the Core domain.
- **Tool:** `pytest` with `unittest.mock`.
- **Requirement:** 80% minimum code coverage. All "Core" logic must be 100% covered.

### 7.2 Integration Testing
- **Focus:** Interaction between Ports and Adapters (e.g., ensuring the PostgreSQL adapter correctly saves a Product).
- **Method:** Using `testcontainers-python` to spin up a real PostgreSQL instance in Docker during the test run.
- **Key Scenarios:** 
    - Sync conflict resolution (LWW vs. Manual).
    - SSO Token validation flow.
    - Report generation timing and S3 upload success.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys from the browser to the database.
- **Tool:** `Playwright`.
- **Critical Paths:**
    - User logs in $\rightarrow$ creates a report schedule $\rightarrow$ receives email.
    - User goes offline $\rightarrow$ adds inventory $\rightarrow$ reconnects $\rightarrow$ data appears in dashboard.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor EOL announcement | High | Critical | Develop a contingency plan with a fallback architecture (Alternative vendor migration path). |
| **R-02** | Team unfamiliarity with Python/Django/AWS | High | Medium | Maintain a "Wiki of Workarounds" and hold bi-weekly "Knowledge Share" sessions. |
| **R-03** | FedRAMP compliance failure | Medium | High | Monthly audits by a certified third-party compliance officer. |
| **R-04** | Third-party API Rate Limiting | High | Medium | Implement a Redis-based request queue and exponential backoff. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt.
- **High:** Major delay or significant budget overrun.
- **Medium:** manageable through documented workarounds.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with strict dependencies.

### Phase 1: Foundation & Sync (Month 1-2)
- **Focus:** Hexagonal architecture setup, DB schema implementation, and Offline-First mode.
- **Dependency:** Infrastructure must be provisioned in AWS GovCloud.
- **Milestone:** Core sync engine operational.

### Phase 2: Reporting & Security (Month 3-4)
- **Focus:** PDF/CSV generation and SSO integration.
- **Dependency:** Sync engine must be stable to ensure reports use correct data.
- **Milestone:** Report generator "In Review" status.

### Phase 3: Polish & Launch (Month 5-6)
- **Focus:** Search, Import/Export, and FedRAMP auditing.
- **Dependency:** Final stability checks of Phase 1 & 2.
- **Milestone 1: Production Launch (Target: 2026-03-15)**

### Post-Launch Phase
- **Milestone 2: Stability Confirmed (Target: 2026-05-15)**: No P0 bugs for 30 consecutive days.
- **Milestone 3: First Paying Customer (Target: 2026-07-15)**: Successful onboarding of one enterprise retail client.

---

## 10. MEETING NOTES

*Note: These notes are extracted from the shared running document (currently 200 pages and unsearchable).*

### Meeting A: Architecture Alignment (2023-11-02)
- **Attendees:** Nyla Oduya, Hiro Stein, Leandro Nakamura.
- **Discussion:** Leandro raised concerns about the complexity of Hexagonal Architecture for a junior dev. Nyla insisted on the pattern to prevent the "God Class" issue seen in the legacy system.
- **Decision:** Hiro will create a "Template Adapter" for Leandro to follow. All new features must be reviewed against the Ports/Adapters checklist.

### Meeting B: The "God Class" Crisis (2023-12-15)
- **Attendees:** Nyla Oduya, Hiro Stein.
- **Discussion:** Discovery of a 3,000-line class `AuthLogEmailManager`. It handles authentication, logging, and email sending. This is a massive technical debt liability.
- **Decision:** This class is marked for decomposition. It will be split into three separate services: `AuthService`, `AuditLogger`, and `NotificationDispatcher` over the next two sprints.

### Meeting C: API Rate Limit Blockers (2024-01-20)
- **Attendees:** Nyla Oduya, Hiro Stein, Kai Stein.
- **Discussion:** Testing is currently blocked. The third-party retail data API is returning `429 Too Many Requests`. Kai noted that UX tests are stalled because mock data is insufficient.
- **Decision:** Hiro to implement a local "Mock API Server" that mimics the third-party's responses, allowing the team to continue development while Nyla negotiates a higher rate limit with the vendor.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | Salaries for 20+ people across 3 departments. |
| **Infrastructure** | 15% | $120,000 | AWS GovCloud, RDS, ECS, ElasticSearch. |
| **Tools/Licenses** | 5% | $40,000 | IDEs, FedRAMP auditing tools, SAML provider fees. |
| **Contingency** | 10% | $80,000 | Reserve for vendor EOL transition or emergency scaling. |

---

## 12. APPENDICES

### Appendix A: FedRAMP Control Mapping
To achieve FedRAMP authorization, Gantry maps the following technical implementations to NIST SP 800-53 controls:
- **AC-2 (Account Management):** Handled by the `Users` and `UserOrganizationMap` tables with strict role-based access control (RBAC).
- **AU-2 (Event Logging):** Implemented via the `AuditLogs` table, capturing all `INET` addresses and timestamps.
- **SC-28 (Protection of Data at Rest):** AWS EBS and S3 volumes are encrypted using KMS (Key Management Service).

### Appendix B: Conflict Resolution Logic (Pseudocode)
The following logic is used by the Sync Manager to handle offline collisions:

```python
def resolve_conflict(local_record, remote_record):
    if local_record.version_clock > remote_record.version_clock:
        # Local is newer
        return local_record
    elif local_record.version_clock < remote_record.version_clock:
        # Remote is newer
        return remote_record
    else:
        # Same clock version: Check for "Critical" flag
        if local_record.is_critical:
            trigger_manual_merge(local_record, remote_record)
        else:
            # Default to Last-Write-Wins based on timestamp
            return max(local_record, remote_record, key=lambda x: x.updated_at)
```