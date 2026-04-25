Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). It serves as the "Single Source of Truth" for Project Rampart.

***

# PROJECT RAMPART: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Finalized / Approved  
**Classification:** Confidential – Stratos Systems Internal  
**Project Lead:** Wanda Santos (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Rampart represents a strategic pivot for Stratos Systems. While the company has historically dominated the industrial energy management sector, it has never operated within the specialized "Greenfield Renewable Integration" market. This market is characterized by fragmented data silos from solar, wind, and geothermal providers that require a unified gateway for reporting and regulatory compliance.

The business justification for Rampart is rooted in the urgent need to capture early market share in the decentralized energy resource (DER) sector. Currently, the industry lacks a standardized API gateway capable of handling the high-frequency telemetry data required for grid stability monitoring while maintaining the rigorous security standards demanded by national energy regulators. By building a custom API gateway and transitioning from a modular monolith to a microservices architecture, Stratos Systems can offer a scalable, secure, and high-performance platform that integrates diverse energy sources into a single pane of glass.

### 1.2 ROI Projection and Financial Objectives
The project operates on a "shoestring" budget of $150,000, necessitating an extremely lean development approach. However, the projected return on investment is substantial. The primary financial objective is to secure $500,000 in new attributed revenue within the first 12 months of launch.

**ROI Calculation:**
*   **Initial Investment:** $150,000 (Capex)
*   **Projected Year 1 Revenue:** $500,000
*   **Operating Expenses (OpEx):** Estimated at $60,000/year for on-prem maintenance.
*   **Net Gain:** $340,000
*   **ROI:** ~226% in Year 1.

Beyond direct revenue, Rampart serves as a hedge against competitor encroachment. A primary competitor is currently estimated to be two months ahead in product development. The ROI is therefore not merely financial but strategic; failure to launch Rampart would result in a loss of market positioning that could cost Stratos Systems millions in potential long-term contracts.

### 1.3 Success Metrics
The success of Rampart will be measured by two primary Key Performance Indicators (KPIs):
1.  **Customer Satisfaction:** Achieving a Net Promoter Score (NPS) of >40 within the first quarter post-launch. This will be measured via quarterly user surveys focusing on the dashboard's utility and the speed of data import.
2.  **Revenue Generation:** $500,000 in attributed revenue within 12 months, validated through signed contracts for the renewable energy management module.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Rampart is transitioning from a **Modular Monolith** to a **Microservices Architecture**. This approach allows for the continued stability of existing business logic while enabling the independent scaling of high-load features (such as file scanning and report generation).

The system is strictly **On-Premise**. Due to regulatory constraints and corporate policy, no cloud providers (AWS, Azure, GCP) are permitted for production data. All services are hosted within the Stratos Systems private data center.

### 2.2 Technology Stack
*   **Backend:** Java 17 / Spring Boot 3.2.x
*   **API Gateway:** Spring Cloud Gateway (integrated with custom filter chains for SOC 2 compliance)
*   **Database:** Oracle Database 19c (Enterprise Edition)
*   **Cache:** Redis 7.0 (On-prem instance for session management and widget state)
*   **Message Broker:** RabbitMQ 3.12 (For asynchronous report generation and virus scanning)
*   **Build Tool:** Maven 3.9
*   **CI/CD:** Jenkins (On-prem) deploying via Ansible to RHEL 9 servers.

### 2.3 System Diagram (ASCII Description)
The following represents the flow of a request from a client through the Rampart Gateway to the internal microservices.

```text
[ Client Browser/App ] 
       |
       v (HTTPS / TLS 1.3)
+-------------------------------------------------------+
|              RAMPART API GATEWAY (Spring Cloud)       |
|  [ Auth Filter ] -> [ Rate Limiter ] -> [ SOC 2 Logger ]|
+-------------------------------------------------------+
       |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+-------------------+   +-------------------+   +-------------------+
|  User/Auth Service |   |  Data Import Svc  |   | Dashboard Service |
|  (Port: 8081)      |   |  (Port: 8082)     |   | (Port: 8083)      |
+-------------------+   +-------------------+   +-------------------+
       |                       |                       |
       +-----------+-----------+-----------+-----------+
                   |                       |
                   v                       v
        +-------------------+    +-----------------------+
        |  Oracle DB 19c    |    | RabbitMQ / Redis Cache |
        | (Central Schema)   |    | (Async Processing)    |
        +-------------------+    +-----------------------+
```

### 2.4 Transition Strategy
The migration follows the "Strangler Fig Pattern." New features (like the Dashboard) are built as microservices from day one. Legacy logic remains in the modular monolith, but is exposed via the API Gateway. As legacy modules are refactored, they are extracted into separate Spring Boot services.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Design

**Functional Description:**
The system must allow users to upload technical documentation and energy site maps. Because these files are stored on-premise but accessed globally by regional technicians, a localized CDN (Content Delivery Network) is required. Every file must be scanned for malware before being committed to permanent storage.

**Detailed Workflow:**
1.  **Ingestion:** Files are uploaded via `POST /api/v1/files/upload`. The API Gateway validates the file size (max 50MB) and MIME type.
2.  **Quarantine:** The file is temporarily stored in a "Quarantine" directory on the filesystem.
3.  **Asynchronous Scanning:** The `FileUploadService` publishes a `FILE_UPLOADED` event to RabbitMQ. The `VirusScanService` (integrating with ClamAV) consumes this event.
4.  **Validation:** If the scan returns "Clean," the file is moved to the "Production" storage volume. If "Infected," the file is deleted immediately, and a security alert is triggered to Cora Park (Security Engineer).
5.  **Distribution:** Once cleaned, the file metadata is indexed in the Oracle DB, and the file is synchronized to the internal Stratos CDN nodes located in the regional data centers.

**Technical Constraints:**
*   Virus scanning must complete within 10 seconds for files < 5MB.
*   The CDN must use a pull-through cache mechanism to avoid overloading the primary storage server.

### 3.2 Feature 2: Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** In Progress

**Functional Description:**
Renewable energy providers use varying formats (CSV, XML, JSON, and proprietary XLS). Rampart must provide a "Smart Import" tool that detects the file format and maps it to the internal energy metric schema without requiring manual user mapping for common templates.

**Detailed Workflow:**
1.  **Upload:** User uploads a data file via `POST /api/v1/import`.
2.  **Magic Byte Analysis:** The `ImportService` reads the first 2KB of the file to identify the file signature (Magic Bytes).
3.  **Schema Matching:**
    *   If CSV: The system analyzes header strings (e.g., "kWh", "Voltage", "Timestamp") using fuzzy string matching to map columns to the `ENERGY_METRICS` table.
    *   If XML/JSON: The system validates against known XSD or JSON schemas.
4.  **Staging Area:** Data is first loaded into a `TMP_IMPORT_STAGING` table in Oracle DB.
5.  **User Review:** The user is presented with a "Preview" screen showing the detected mapping.
6.  **Commit:** Upon approval, data is moved from staging to production tables.

**Technical Constraints:**
*   Maximum import size: 100,000 rows per file.
*   Auto-detection accuracy must exceed 90% for the top 5 most common industry templates.

### 3.3 Feature 3: Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Functional Description:**
The primary interface for the end-user is a dynamic dashboard. Users must be able to configure their own view of energy production metrics, system health, and regulatory alerts using a grid-based drag-and-drop system.

**Detailed Workflow:**
1.  **Widget Library:** The system provides a set of pre-defined widgets (e.g., "Real-time Power Output Gauge," "Weekly Efficiency Graph," "Active Alerts List").
2.  **Configuration:** Users drag widgets from a sidebar onto a 12-column grid.
3.  **State Persistence:** The layout (X-coordinate, Y-coordinate, Width, Height, WidgetID) is saved as a JSON blob in the `USER_DASHBOARD_CONFIG` table.
4.  **Data Binding:** Each widget makes a specific API call to the `DashboardService` to fetch its data. For example, the Power Output Gauge calls `GET /api/v1/metrics/power-current`.
5.  **Real-time Updates:** Widgets use WebSockets (via Spring Boot STOMP) to receive push updates for critical metrics without page refreshes.

**Technical Constraints:**
*   Dashboard state must load in under 2 seconds.
*   The layout must be responsive, adapting the grid from 12 columns (Desktop) to 1 column (Mobile).

### 3.4 Feature 4: Localization and Internationalization (L10n/I18n) for 12 Languages
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Functional Description:**
To operate in the global renewable market, Rampart must support 12 languages (including English, Spanish, Mandarin, German, French, and Japanese). This extends beyond simple translation to include date formats, currency symbols, and measurement units (Metric vs. Imperial).

**Detailed Workflow:**
1.  **Resource Bundles:** All UI text is extracted into `messages_xx.properties` files within the Spring Boot application.
2.  **User Preference:** The `UserPreference` table stores the `locale_id` for each user.
3.  **Interceptor:** A Spring `HandlerInterceptor` detects the user's locale from the `Accept-Language` header or user profile and sets the `LocaleContextHolder`.
4.  **Dynamic Formatting:**
    *   Dates: Use `java.time.format.DateTimeFormatter` based on the locale.
    *   Numbers: Use `NumberFormat` to handle comma/period decimal separators.
5.  **Translation Pipeline:** A structured workflow where Zola Moreau provides the English keys, and professional translators provide the 11 corresponding translations.

**Technical Constraints:**
*   Zero hardcoded strings in the frontend or backend.
*   Support for Right-to-Left (RTL) languages (e.g., Arabic) if added in future iterations, though the current 12 are primarily LTR.

### 3.5 Feature 5: PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** Not Started

**Functional Description:**
Regulatory bodies require monthly and quarterly reports on energy output and carbon offsets. Rampart must generate these reports and deliver them via email or SFTP.

**Detailed Workflow:**
1.  **Template Definition:** Reports are defined using JasperReports templates (.jrxml).
2.  **Scheduling:** Users define a schedule in the `REPORT_SCHEDULE` table (e.g., "First Monday of every month at 08:00 AM").
3.  **Job Execution:** A Quartz Scheduler triggers a background job.
4.  **Data Fetching:** The `ReportService` executes a complex Oracle SQL query to aggregate metrics for the requested period.
5.  **Generation:** The data is piped into the JasperReports engine to produce a PDF or CSV.
6.  **Delivery:** The `NotificationService` sends the file as an attachment via SMTP or uploads it to a client-specified SFTP folder.

**Technical Constraints:**
*   Report generation must not block the main application thread.
*   Maximum report size: 200 pages.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is handled via JWT tokens passed in the `Authorization: Bearer <token>` header.

### 4.1 Endpoint: User Authentication
*   **Path:** `POST /auth/login`
*   **Request:**
    ```json
    {
      "username": "zmoreau_dev",
      "password": "securepassword123"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1...",
      "expiresIn": 3600,
      "userId": "USR-9921"
    }
    ```

### 4.2 Endpoint: File Upload
*   **Path:** `POST /files/upload`
*   **Request:** `multipart/form-data` (File: `site_map.pdf`, Type: `application/pdf`)
*   **Response (202 Accepted):**
    ```json
    {
      "uploadId": "UP-55021",
      "status": "Scanning",
      "estimatedWait": "15s"
    }
    ```

### 4.3 Endpoint: Get File Status
*   **Path:** `GET /files/status/{uploadId}`
*   **Response (200 OK):**
    ```json
    {
      "uploadId": "UP-55021",
      "status": "Clean",
      "cdnUrl": "https://cdn.stratos.internal/files/site_map.pdf"
    }
    ```

### 4.4 Endpoint: Import Data
*   **Path:** `POST /import/upload`
*   **Request:** `multipart/form-data` (File: `metrics_q3.csv`)
*   **Response (201 Created):**
    ```json
    {
      "importId": "IMP-101",
      "detectedFormat": "CSV",
      "mappingStatus": "Pending_Review"
    }
    ```

### 4.5 Endpoint: Confirm Import Mapping
*   **Path:** `POST /import/confirm/{importId}`
*   **Request:**
    ```json
    {
      "mappings": [
        {"source": "kWh_Total", "target": "energy_consumption"},
        {"source": "Peak_kW", "target": "peak_load"}
      ]
    }
    ```
*   **Response (200 OK):** `{"status": "Imported", "rowsProcessed": 4500}`

### 4.6 Endpoint: Save Dashboard Layout
*   **Path:** `PUT /dashboard/layout`
*   **Request:**
    ```json
    {
      "layoutId": "L-882",
      "widgets": [
        {"id": "W1", "x": 0, "y": 0, "w": 4, "h": 2},
        {"id": "W2", "x": 4, "y": 0, "w": 8, "h": 2}
      ]
    }
    ```
*   **Response (200 OK):** `{"status": "Saved"}`

### 4.7 Endpoint: Fetch Metric Data
*   **Path:** `GET /metrics/power-current?siteId=SITE-01`
*   **Response (200 OK):**
    ```json
    {
      "timestamp": "2023-10-24T10:00:00Z",
      "value": 450.2,
      "unit": "kW",
      "status": "Stable"
    }
    ```

### 4.8 Endpoint: Schedule Report
*   **Path:** `POST /reports/schedule`
*   **Request:**
    ```json
    {
      "reportType": "MONTHLY_CARBON",
      "cron": "0 0 8 1 * *",
      "deliveryMethod": "EMAIL",
      "recipient": "compliance@energyreg.gov"
    }
    ```
*   **Response (201 Created):** `{"scheduleId": "SCH-441"}`

---

## 5. DATABASE SCHEMA

The system utilizes an Oracle 19c database. Relationships are enforced via foreign keys, and performance is optimized via B-tree indexing on all ID columns.

### 5.1 Table Definitions

1.  **`USERS`**
    *   `user_id` (PK, VARCHAR2 50)
    *   `username` (UNIQUE, VARCHAR2 100)
    *   `password_hash` (VARCHAR2 255)
    *   `role` (VARCHAR2 20) - (ADMIN, ANALYST, VIEWER)
    *   `created_at` (TIMESTAMP)

2.  **`USER_PREFERENCES`**
    *   `pref_id` (PK, NUMBER)
    *   `user_id` (FK -> USERS, VARCHAR2 50)
    *   `locale_id` (VARCHAR2 10) - (e.g., 'en_US', 'zh_CN')
    *   `timezone` (VARCHAR2 50)
    *   `unit_system` (VARCHAR2 10) - (METRIC, IMPERIAL)

3.  **`USER_DASHBOARD_CONFIG`**
    *   `config_id` (PK, NUMBER)
    *   `user_id` (FK -> USERS, VARCHAR2 50)
    *   `layout_json` (CLOB) - Stores the widget coordinates and IDs.
    *   `last_updated` (TIMESTAMP)

4.  **`ENERGY_METRICS`**
    *   `metric_id` (PK, NUMBER)
    *   `site_id` (VARCHAR2 50)
    *   `timestamp` (TIMESTAMP)
    *   `metric_type` (VARCHAR2 50) - (e.g., 'KWH', 'VOLTAGE')
    *   `value` (NUMBER(19,4))
    *   `status` (VARCHAR2 20)

5.  **`TMP_IMPORT_STAGING`**
    *   `staging_id` (PK, NUMBER)
    *   `import_id` (VARCHAR2 50)
    *   `raw_data` (CLOB)
    *   `column_index` (NUMBER)
    *   `detected_value` (VARCHAR2 1000)

6.  **`FILE_METADATA`**
    *   `file_id` (PK, VARCHAR2 50)
    *   `filename` (VARCHAR2 255)
    *   `storage_path` (VARCHAR2 500)
    *   `mime_type` (VARCHAR2 100)
    *   `scan_status` (VARCHAR2 20) - (CLEAN, INFECTED, PENDING)
    *   `uploaded_by` (FK -> USERS, VARCHAR2 50)

7.  **`REPORT_SCHEDULE`**
    *   `schedule_id` (PK, NUMBER)
    *   `report_type` (VARCHAR2 50)
    *   `cron_expression` (VARCHAR2 100)
    *   `delivery_target` (VARCHAR2 255) - (Email or SFTP path)
    *   `is_active` (NUMBER(1))

8.  **`SITES`**
    *   `site_id` (PK, VARCHAR2 50)
    *   `site_name` (VARCHAR2 200)
    *   `region` (VARCHAR2 100)
    *   `capacity_mw` (NUMBER(10,2))

9.  **`AUDIT_LOGS` (SOC 2 Requirement)**
    *   `log_id` (PK, NUMBER)
    *   `timestamp` (TIMESTAMP)
    *   `user_id` (FK -> USERS, VARCHAR2 50)
    *   `action` (VARCHAR2 200)
    *   `ip_address` (VARCHAR2 45)
    *   `resource_accessed` (VARCHAR2 200)

10. **`WIDGET_DEFINITIONS`**
    *   `widget_id` (PK, VARCHAR2 20)
    *   `widget_name` (VARCHAR2 100)
    *   `api_endpoint` (VARCHAR2 255)
    *   `default_width` (NUMBER)
    *   `default_height` (NUMBER)

### 5.2 Key Relationships
*   `USERS` $\rightarrow$ `USER_PREFERENCES` (1:1)
*   `USERS` $\rightarrow$ `USER_DASHBOARD_CONFIG` (1:1)
*   `USERS` $\rightarrow$ `FILE_METADATA` (1:N)
*   `SITES` $\rightarrow$ `ENERGY_METRICS` (1:N)
*   `USERS` $\rightarrow$ `AUDIT_LOGS` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Description
Project Rampart utilizes three distinct on-premise environments.

#### 6.1.1 Development (DEV)
*   **Purpose:** Feature development and unit testing.
*   **Hardware:** 2x Virtual Machines (16GB RAM, 8 vCPU).
*   **Database:** Oracle Express Edition (XE).
*   **Deployment:** Automated via Jenkins on every commit to `develop` branch.

#### 6.1.2 Staging (STAGING)
*   **Purpose:** Integration testing, SOC 2 pre-audit, and stakeholder demos.
*   **Hardware:** 3x Virtual Machines (32GB RAM, 16 vCPU). Mirror of production spec.
*   **Database:** Oracle 19c (Standard Edition) - subset of production data.
*   **Deployment:** Bi-weekly builds from `release` branch.

#### 6.1.3 Production (PROD)
*   **Purpose:** Live operations.
*   **Hardware:** 5x Physical Servers in the Stratos Data Center (64GB RAM, 32 vCPU).
*   **Database:** Oracle 19c (Enterprise Edition) with RAC (Real Application Clusters) for High Availability.
*   **Deployment:** Quarterly releases. Requires manual sign-off from Wanda Santos and Cora Park.

### 6.2 Infrastructure Provisioning (The Blocker)
Currently, there is a critical blocker regarding infrastructure provisioning. While the project is on-premise, the initial VM orchestration layer (VMware) is managed by a third-party cloud-service provider that handles our physical data center management. This provider has delayed the provisioning of the Staging environment by 3 weeks, delaying integration testing for Feature 2.

### 6.3 Deployment Pipeline
1.  **Build:** Maven compiles code and runs unit tests.
2.  **Package:** JAR file is created and versioned (e.g., `rampart-service-1.0.4-SNAPSHOT.jar`).
3.  **Artifact Storage:** JAR is pushed to on-prem Nexus repository.
4.  **Provisioning:** Ansible scripts push the JAR to RHEL servers.
5.  **Validation:** Health check endpoints (`/actuator/health`) are pinged to ensure service availability.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tool:** JUnit 5, Mockito.
*   **Scope:** All business logic in `@Service` and `@Component` classes.
*   **Requirement:** 80% minimum line coverage.
*   **Execution:** Run on every Jenkins build.

### 7.2 Integration Testing
*   **Tool:** Testcontainers (for Oracle DB and RabbitMQ).
*   **Scope:** API Gateway routing, Database Repository layers, and Message Queue producers/consumers.
*   **Focus:** Validating that the `FileUploadService` correctly interacts with the `VirusScanService` via RabbitMQ.

### 7.3 End-to-End (E2E) Testing
*   **Tool:** Selenium / Playwright.
*   **Scope:** Critical User Journeys (CUJs).
    *   *CUJ 1:* User logs in $\rightarrow$ Uploads CSV $\rightarrow$ Confirms Mapping $\rightarrow$ Views updated Dashboard.
    *   *CUJ 2:* User configures a Monthly Report $\rightarrow$ Report generates $\rightarrow$ Email is sent.
*   **Execution:** Run in Staging environment prior to every quarterly release.

### 7.4 Security Testing
*   **Static Analysis:** SonarQube for vulnerability detection (OWASP Top 10).
*   **Dynamic Analysis:** OWASP ZAP scans on the Staging environment.
*   **SOC 2 Compliance:** Cora Park will perform a quarterly audit of the `AUDIT_LOGS` table to ensure all privileged actions are tracked.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding "small" features. | High | Medium | Build a contingency plan with a fallback architecture; strict JIRA-based change request process. | Wanda Santos |
| R-02 | Competitor is 2 months ahead in the market. | Medium | High | Assign dedicated owner to track competitor moves; prioritize "Critical" launch blockers over "Medium" features. | Zola Moreau |
| R-03 | Infrastructure provisioning delay by provider. | High | Medium | Use local Docker containers for development until VMs are provisioned. | Cassius Stein |
| R-04 | Technical debt: Hardcoded configs in 40+ files. | High | Low | Implement Spring Cloud Config or a centralized `application.yml` strategy in Sprint 2. | Zola Moreau |
| R-05 | SOC 2 Compliance failure before launch. | Low | Critical | Bi-weekly security reviews with Cora Park; automated audit logging. | Cora Park |

**Probability/Impact Matrix:**
*   High Probability + High Impact $\rightarrow$ Immediate Action Required.
*   Low Probability + High Impact $\rightarrow$ Monitoring/Planning.

---

## 9. TIMELINE AND PHASES

The project follows a phased approach aligned with quarterly regulatory cycles.

### Phase 1: Foundation & Gateway (Current - 2026-03-01)
*   **Focus:** API Gateway setup, Oracle DB schema initialization, Authentication.
*   **Dependencies:** Infrastructure provisioning (Blocked).
*   **Key Deliverables:** Working Auth service, API Gateway routing.

### Phase 2: Core Data Engine (2026-03-01 - 2026-06-15)
*   **Focus:** Feature 2 (Data Import), Feature 1 (File Upload/Virus Scan).
*   **Dependencies:** Phase 1 completion.
*   **Key Deliverables:** **Milestone 1 (Stakeholder demo and sign-off on 2026-06-15).**

### Phase 3: User Interface & Localization (2026-06-16 - 2026-08-15)
*   **Focus:** Feature 3 (Customizable Dashboard), Feature 4 (L10n/I18n).
*   **Dependencies:** Feature 2 (for data to populate dashboard).
*   **Key Deliverables:** **Milestone 2 (MVP feature-complete on 2026-08-15).**

### Phase 4: Reporting & Beta (2026-08-16 - 2026-10-15)
*   **Focus:** Feature 5 (PDF/CSV Reports), Beta user onboarding.
*   **Dependencies:** SOC 2 Type II certification.
*   **Key Deliverables:** **Milestone 3 (External beta with 10 pilot users on 2026-10-15).**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-05 | **Attendees:** Wanda, Zola, Cora, Cassius
**Discussion:**
The team debated between a full microservices approach and a modular monolith. Zola argued that a full microservices jump would be too risky given the budget and team size. Wanda decided on a hybrid "modular monolith transitioning incrementally" approach to minimize operational overhead.
**Decisions:**
*   Use Spring Cloud Gateway as the entry point.
*   No cloud services allowed; strictly on-prem.
**Action Items:**
*   Draft the initial Oracle schema (Zola) - *Completed*.
*   Define SOC 2 logging requirements (Cora) - *In Progress*.

### Meeting 2: Budget Review & Risk Assessment
**Date:** 2023-12-12 | **Attendees:** Wanda, Zola
**Discussion:**
Wanda highlighted the $150,000 budget constraint. Zola noted that the current hardcoded configuration across 40+ files is a ticking time bomb for the quarterly release cycle. They discussed the competitor's progress, noting the competitor has already launched a basic version of the dashboard.
**Decisions:**
*   Prioritize the Dashboard (Feature 3) as a "Launch Blocker."
*   Shift budget from "Tooling" to "Contractor hours" for Cassius to accelerate the Import engine.
**Action Items:**
*   Create a mapping for all hardcoded values to be moved to `application.properties` (Zola).

### Meeting 3: Infrastructure Blocker Update
**Date:** 2024-01-20 | **Attendees:** Wanda, Cassius
**Discussion:**
Cassius reported that the cloud provider managing the on-prem VMs has not yet delivered the Staging environment. This is preventing the team from testing the RabbitMQ integration for the virus scanner.
**Decisions:**
*   Cassius will set up a temporary "Dockerized Staging" on a local dev server to unblock development.
*   Wanda will escalate the ticket to the provider's account manager.
**Action Items:**
*   Deploy temporary RabbitMQ container for testing (Cassius) - *Completed*.
*   Draft the escalation email to the provider (Wanda) - *Completed*.

---

## 11. BUDGET BREAKDOWN

The budget is $150,000. Given the "shoestring" nature, all expenditures are strictly monitored.

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Senior Backend / Security / Lead | $90,000 | Salaries/Allocated internal cost. |
| **Contracting** | Cassius Stein (Contractor) | $35,000 | Specialized import/export development. |
| **Infrastructure** | Oracle Licenses / On-prem Hardware | $15,000 | Annual license and server maintenance. |
| **Tools** | SonarQube / JasperReports Lic. | $5,000 | Professional tiers for security/reporting. |
| **Contingency** | Emergency Buffer | $5,000 | For critical hardware replacement. |
| **Total** | | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: SOC 2 Type II Compliance Matrix
To meet SOC 2 requirements, the following technical controls are implemented:
1.  **Access Control:** All API access is gated by JWTs with a maximum 1-hour lifespan.
2.  **Audit Trails:** The `AUDIT_LOGS` table captures `(Who, What, When, Where)` for every `PUT`, `POST`, and `DELETE` operation.
3.  **Encryption:** All data at rest in Oracle DB is encrypted using Transparent Data Encryption (TDE). Data in transit is encrypted via TLS 1.3.
4.  **Change Management:** No code enters Production without a JIRA ticket and a peer-reviewed Pull Request.

### Appendix B: Localization Key Mapping Example
To ensure consistency across the 12 supported languages, the following key-value structure is used:

| Key | English (en_US) | Spanish (es_ES) | Mandarin (zh_CN) |
| :--- | :--- | :--- | :--- |
| `dash.widget.power` | Real-time Power | Potencia en tiempo real | 实时功率 |
| `import.error.format` | Invalid File Format | Formato de archivo inválido | 文件格式无效 |
| `report.gen.success` | Report Generated | Informe generado | 报告已生成 |
| `auth.login.fail` | Invalid Credentials | Credenciales inválidas | 凭据无效 |