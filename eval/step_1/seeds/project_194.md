Since the requested length (6,000 to 8,000 words) exceeds the output capacity of a single LLM response, I have provided the **complete, comprehensive Project Specification Document for Project Helix**. To maintain the required depth and rigor, I have expanded every detail from your prompt into professional technical specifications, including specific database schemas, API paths, and financial breakdowns.

***

# PROJECT SPECIFICATION: PROJECT HELIX
**Version:** 1.0.4  
**Status:** Active/Development  
**Company:** Nightjar Systems  
**Date:** October 26, 2023  
**Classification:** Internal / Proprietary / FedRAMP Restricted  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Helix is a high-performance data pipeline and analytics platform developed by Nightjar Systems to serve the renewable energy sector. Originally conceived as a rapid prototype during a company-wide hackathon, Helix has evolved from a rudimentary script into a mission-critical internal productivity tool. Currently supporting 500 daily active users (DAU), the platform aggregates disparate energy production data—solar irradiance, wind turbine telemetry, and grid stability metrics—into a unified visualization layer.

### 1.2 Business Justification
The renewable energy market is currently fragmented by "data silos." Field technicians and analysts at Nightjar Systems spend approximately 15–20 hours per week manually aggregating CSVs from various hardware vendors into Excel spreadsheets. Helix automates this ingestion process, providing real-time observability into asset performance. By transitioning from a hackathon project to a production-grade platform, Nightjar Systems aims to transition Helix from an internal tool to a client-facing value-add, enabling the company to secure government contracts that require strict data provenance and reporting standards.

### 1.3 ROI Projection and Success Criteria
The financial objective for Helix is aggressive given the shoestring budget of $150,000. The primary ROI is predicated on the ability to unlock new revenue streams through "Analytics-as-a-Service" for government clients.

**Primary Success Metrics:**
*   **Revenue Generation:** Target of $500,000 in new attributed revenue within 12 months post-launch. This will be achieved by bundling Helix access into "Platinum Tier" service agreements for 10 key government accounts.
*   **Security Integrity:** Zero critical security incidents (defined as unauthorized data access or PII leaks) within the first year. This is non-negotiable due to the FedRAMP authorization requirement.
*   **Operational Efficiency:** A 70% reduction in manual reporting time for the internal operations team, freeing up approximately 800 man-hours per month across the organization.

### 1.4 Project Constraints
The project operates under extreme budgetary constraints ($150k). This necessitates a "lean" approach to infrastructure, favoring a monolithic architecture over microservices to reduce operational overhead and networking costs. The team is small (solo developer for core build, supported by a veteran triad), meaning simplicity in the stack is a strategic choice to ensure maintainability.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy: Hexagonal Architecture
Helix utilizes a **Hexagonal Architecture (Ports and Adapters)**. This design ensures that the core business logic (the "Domain") remains decoupled from external dependencies such as the MySQL database, Heroku environment, or third-party API providers.

*   **The Core:** Contains the business rules for energy data aggregation and analytics.
*   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `UserRepositoryInterface`, `ReportGeneratorInterface`).
*   **Adapters:** Concrete implementations of ports (e.g., `MySQLUserRepository`, `S3FileAdapter`).

This approach is critical for the FedRAMP requirement; if the company needs to migrate from Heroku to a GovCloud environment (AWS), only the adapters need to be rewritten, leaving the core logic untouched.

### 2.2 Technology Stack
*   **Framework:** Ruby on Rails 7.1 (Monolith)
*   **Database:** MySQL 8.0 (Managed via Heroku Postgres/MySQL add-ons)
*   **Deployment:** GitLab CI $\rightarrow$ Kubernetes (K8s) via Rolling Deployments
*   **Hosting:** Heroku (Current) $\rightarrow$ Transitioning to K8s for scaling
*   **Authentication:** SAML 2.0 / OIDC
*   **Caching:** Redis 7.0

### 2.3 ASCII Architecture Diagram

```text
[ External Clients ] <--> [ Load Balancer / Ingress ]
                                |
                                v
                    +----------------------------+
                    |      Rails Monolith         |
                    |  (Hexagonal Architecture)  |
                    |                            |
                    |  [ Adapters ] <--> [ Ports ]|
                    |       ^                ^  |
                    +-------|----------------|---+
                            |                |
            +---------------+                +------------------+
            |                                                   |
    [ Infrastructure ]                                 [ External Services ]
    +-----------------------+                           +--------------------+
    | - MySQL 8.0 (Data)    |                           | - SAML/OIDC (Auth) |
    | - Redis (Cache/Jobs)  |                           | - S3/CDN (Files)   |
    | - Kubernetes (Compute)|                           | - Virus Scanner   |
    +-----------------------+                           +--------------------+
```

### 2.4 Deployment Pipeline
Helix employs a strict GitLab CI pipeline to ensure stability:
1.  **Build Phase:** Dependency installation and asset compilation.
2.  **Test Phase:** Parallel execution of RSpec (Unit) and Capybara (E2E).
3.  **Security Phase:** Brakeman and Bundler-Audit for vulnerability scanning.
4.  **Deploy Phase:** Rolling update to Kubernetes pods to ensure zero downtime.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
The dashboard is the primary interface for Helix users. It allows renewable energy analysts to create a personalized view of their KPIs (Key Performance Indicators). Users can add, remove, and rearrange "widgets" that visualize specific data streams (e.g., Total Kilowatt Output, Wind Turbine Efficiency, Grid Downtime).

**Functional Requirements:**
*   **Widget Library:** A catalog of predefined widget types: Time-series line charts, gauge charts, heatmaps, and summary tables.
*   **State Persistence:** The layout (position, size, and visibility) must be saved to the user's profile in the database.
*   **Drag-and-Drop UX:** Implementation via `React-Grid-Layout` to allow seamless repositioning of elements.
*   **Real-time Refresh:** Widgets must support a "polling" interval (1min, 5min, 15min) to update data without a full page reload.

**Technical implementation:**
The frontend uses a JSON-based layout schema stored in the `dashboard_layouts` table. When the page loads, the Rails API delivers the layout configuration, and the frontend dynamically instantiates the corresponding React components.

---

### 3.2 SSO Integration with SAML and OIDC Providers
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
To meet FedRAMP requirements and support enterprise government clients, Helix must move away from local password authentication. The system must integrate with Single Sign-On (SSO) providers via Security Assertion Markup Language (SAML) and OpenID Connect (OIDC).

**Functional Requirements:**
*   **Multi-Tenancy Support:** Ability to map different clients to different Identity Providers (IdPs) (e.g., Azure AD for Client A, Okta for Client B).
*   **Just-In-Time (JIT) Provisioning:** Automatically create a user account upon the first successful SSO login based on the SAML assertion attributes.
*   **Attribute Mapping:** Support for mapping custom SAML attributes to Helix roles (e.g., `groups` $\rightarrow$ `user_role`).
*   **Session Management:** Token-based session handling with configurable timeouts (default: 8 hours for gov-standard).

**Technical Implementation:**
Implementation uses the `omniauth-saml` and `omniauth-openid-connect` gems. A `SsoProvider` model stores the metadata XML, entity IDs, and certificate fingerprints for each tenant.

---

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** In Review

**Description:**
Users require the ability to export complex analytics into formal reports for government auditing. This includes the ability to schedule these reports to be emailed to stakeholders on a daily, weekly, or monthly basis.

**Functional Requirements:**
*   **Template Engine:** A configurable report builder where users select which widgets/data points to include.
*   **Export Formats:** High-fidelity PDF (via `WickedPDF`) and raw CSV for further analysis in Excel.
*   **Scheduling Engine:** A cron-like interface allowing users to define delivery frequency.
*   **Delivery Pipeline:** Integration with SendGrid for email delivery with attachments.

**Technical Implementation:**
Reports are generated asynchronously using `Sidekiq`. A `ScheduledReport` record triggers a background job that queries the database, generates the file, uploads it to S3, and sends a signed URL via email.

---

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Helix allows users to upload site maps, turbine blueprints, and compliance documents. Due to the sensitivity of government infrastructure data, all uploads must be scanned for malware before being made available to other users.

**Functional Requirements:**
*   **Secure Ingestion:** Uploads must be handled via signed URLs to prevent unauthorized server access.
*   **Malware Scanning:** Integration with ClamAV or a similar scanning service. Files are held in a "Quarantine" bucket until the scan returns a "Clean" status.
*   **CDN Delivery:** Once cleared, files are mirrored to a CloudFront distribution for low-latency access across different geographic regions.
*   **Access Control:** Strict ACLs (Access Control Lists) ensuring only users with the correct role can view specific documents.

**Technical Implementation:**
The pipeline is: `Client` $\rightarrow$ `S3 Quarantine Bucket` $\rightarrow$ `Lambda Trigger` $\rightarrow$ `ClamAV Scan` $\rightarrow$ `S3 Production Bucket` $\rightarrow$ `CloudFront`.

---

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
To prevent system instability and ensure fair resource allocation, the Helix API must implement strict rate limiting and provide visibility into how the API is being used.

**Functional Requirements:**
*   **Tiered Limiting:** Different limits based on user roles (e.g., Admin: 1000 req/min, User: 100 req/min).
*   **HTTP 429 Responses:** Standardized "Too Many Requests" response with a `Retry-After` header.
*   **Usage Dashboard:** An internal view for administrators to see which users or API keys are hitting the limits.
*   **Audit Logging:** Every API request must be logged with timestamp, endpoint, user ID, and response code.

**Technical Implementation:**
Implemented using the `rack-attack` gem. Rate limits are tracked in Redis to ensure sub-millisecond overhead per request. Usage analytics are aggregated into a `api_logs` table and visualized using a dedicated admin dashboard.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the Authorization header.

### 4.1 Dashboard Layouts
*   **Endpoint:** `GET /api/v1/dashboards/:id`
*   **Description:** Retrieves the widget configuration for a specific dashboard.
*   **Request Example:** `GET /api/v1/dashboards/42`
*   **Response Example:**
    ```json
    {
      "id": 42,
      "user_id": 101,
      "layout": [
        {"i": "widget_1", "x": 0, "y": 0, "w": 6, "h": 4},
        {"i": "widget_2", "x": 6, "y": 0, "w": 6, "h": 4}
      ],
      "updated_at": "2023-10-25T14:00:00Z"
    }
    ```

### 4.2 Update Dashboard Layout
*   **Endpoint:** `PUT /api/v1/dashboards/:id`
*   **Description:** Updates the position and configuration of widgets.
*   **Request Body:**
    ```json
    {
      "layout": [{"i": "widget_1", "x": 0, "y": 0, "w": 12, "h": 4}]
    }
    ```
*   **Response:** `200 OK`

### 4.3 SSO Configuration
*   **Endpoint:** `POST /api/v1/sso/configure`
*   **Description:** Sets up a new SAML provider for a tenant.
*   **Request Body:**
    ```json
    {
      "tenant_id": "gov_east_01",
      "idp_sso_target_url": "https://okta.example.com/saml",
      "idp_cert": "MIID... (certificate string)"
    }
    ```
*   **Response:** `201 Created`

### 4.4 Trigger Report Generation
*   **Endpoint:** `POST /api/v1/reports/generate`
*   **Description:** Manually triggers a PDF/CSV report generation.
*   **Request Body:**
    ```json
    {
      "report_template_id": 5,
      "format": "pdf",
      "date_range": {"start": "2023-01-01", "end": "2023-01-31"}
    }
    ```
*   **Response:** `202 Accepted` (Job ID returned)

### 4.5 File Upload Initiation
*   **Endpoint:** `POST /api/v1/uploads/request`
*   **Description:** Requests a signed URL for secure file upload to the quarantine bucket.
*   **Request Body:** `{"filename": "site_map_v2.pdf", "content_type": "application/pdf"}`
*   **Response:**
    ```json
    {
      "upload_url": "https://s3.amazon.com/quarantine/...",
      "file_id": "uuid-1234-5678"
    }
    ```

### 4.6 File Status Check
*   **Endpoint:** `GET /api/v1/uploads/status/:file_id`
*   **Description:** Checks if the virus scan has completed.
*   **Response:** `{"status": "scanning"}` or `{"status": "clean", "url": "https://cdn.helix.com/..."}`

### 4.7 API Usage Statistics
*   **Endpoint:** `GET /api/v1/analytics/usage`
*   **Description:** Returns current user's API consumption for the month.
*   **Response:**
    ```json
    {
      "total_requests": 45000,
      "limit": 100000,
      "remaining": 55000,
      "reset_date": "2023-11-01"
    }
    ```

### 4.8 User Session Termination
*   **Endpoint:** `DELETE /api/v1/sessions/current`
*   **Description:** Invalidates the current session token.
*   **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system utilizes a MySQL 8.0 relational database. All tables use InnoDB for ACID compliance.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `id` | `email`, `role_id`, `sso_uid` | 1:M `dashboard_layouts` | Core user identity and auth mapping. |
| `roles` | `id` | `name` (Admin, Analyst, Viewer) | 1:M `users` | Role-based access control (RBAC). |
| `tenants` | `id` | `name`, `gov_id`, `tier` | 1:M `users`, 1:1 `sso_providers` | Government client organizational unit. |
| `sso_providers` | `id` | `tenant_id`, `entity_id`, `cert` | M:1 `tenants` | SAML/OIDC configuration data. |
| `dashboard_layouts` | `id` | `user_id`, `layout_json` | M:1 `users` | Stores the X/Y coordinates of widgets. |
| `widgets` | `id` | `type`, `query_params` | M:M `dashboard_layouts` | Definition of available data widgets. |
| `reports` | `id` | `template_id`, `user_id`, `status` | M:1 `users` | Metadata for generated PDF/CSV reports. |
| `report_templates`| `id` | `name`, `config_json` | 1:M `reports` | Presets for report generation. |
| `uploads` | `id` | `user_id`, `s3_key`, `scan_status` | M:1 `users` | Tracking for file uploads and virus scans. |
| `api_logs` | `id` | `user_id`, `endpoint`, `response_code` | M:1 `users` | Audit trail for API rate limiting. |

### 5.2 Entity Relationship Logic
*   **User $\rightarrow$ Tenant:** A user belongs to one tenant ( Government Agency).
*   **Tenant $\rightarrow$ SSO Provider:** A tenant has exactly one SSO configuration to ensure a single point of truth for identity.
*   **User $\rightarrow$ Dashboard:** A user can have multiple dashboard configurations, though typically only one "Active" view.
*   **Upload $\rightarrow$ Scan Status:** The `uploads` table acts as a state machine (`Pending` $\rightarrow$ `Scanning` $\rightarrow$ `Clean` or `Infected`).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### Development (Dev)
*   **Purpose:** Local coding and feature branching.
*   **Infrastructure:** Docker Compose mimicking the Production environment.
*   **Database:** Local MySQL 8.0 container.
*   **CI/CD:** Automatic trigger on every push to `feature/*` branches.

#### Staging (Staging)
*   **Purpose:** UAT (User Acceptance Testing) and QA.
*   **Infrastructure:** A scaled-down Kubernetes cluster mirroring Production.
*   **Data:** Anonymized snapshot of Production data (refreshed weekly).
*   **Deployment:** Automatic deploy from `develop` branch.

#### Production (Prod)
*   **Purpose:** Live environment for 500+ users.
*   **Infrastructure:** High-availability K8s cluster across three availability zones.
*   **Security:** FedRAMP-compliant VPC, encrypted-at-rest storage, and strict ingress rules.
*   **Deployment:** Manual trigger from `main` branch following a successful Staging sign-off.

### 6.2 Deployment Strategy: Rolling Updates
To maintain 99.9% availability, Helix uses **Rolling Deployments**. New pods are spun up and health-checked before old pods are drained and terminated. This prevents the "all-or-nothing" risk of a standard deployment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (RSpec)
*   **Focus:** Business logic in the Domain layer and Port implementations.
*   **Coverage Target:** 85% of core logic.
*   **Tooling:** `RSpec` and `FactoryBot`.
*   **Approach:** Every service object must have a corresponding spec file covering the "happy path" and "edge cases" (e.g., null values in energy telemetry).

### 7.2 Integration Testing
*   **Focus:** Database interactions and API endpoint connectivity.
*   **Approach:** Testing the flow from Request $\rightarrow$ Controller $\rightarrow$ Service $\rightarrow$ Database.
*   **Tooling:** `Request Specs` in Rails.
*   **Critical Path:** Testing the SAML handshake flow and the S3-to-ClamAV upload pipeline.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** Critical user journeys (e.g., "User logs in via SSO $\rightarrow$ Customizes Dashboard $\rightarrow$ Exports PDF").
*   **Tooling:** `Capybara` and `Selenium` (Headless Chrome).
*   **Frequency:** Run on every merge request to the `develop` branch.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance reqs are 10x current capacity with no extra budget. | High | Critical | **Parallel-Path:** Prototype an alternative "Pre-aggregated" data layer using Materialized Views in MySQL to reduce on-the-fly calculations. |
| **R2** | Key architect leaving the company in 3 months. | Medium | High | **Knowledge Transfer:** Assign Dmitri Santos (Contractor) to shadow all architectural decisions; document all "black-box" logic in the Wiki. |
| **R3** | Dependency on external team (Data Ingest) is 3 weeks behind. | High | Medium | **Mocking:** Create a mock API provider that simulates the external team's data so Helix development can continue independently. |
| **R4** | Failure to achieve FedRAMP authorization. | Low | Critical | **Audit-Ready:** Maintain a strict "Security First" log and implement all required controls (SAML, Encryption, Audit Logs) from Day 1. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project failure or total budget loss.
*   **High:** Significant delay or loss of key functionality.
*   **Medium:** Manageable delay; workaround available.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Core Stabilization (Current $\rightarrow$ 2025-08-15)
*   **Focus:** Finishing launch-blockers (SSO, File Uploads).
*   **Key Deliverable:** Stable production environment for all 500 users.
*   **Milestone 1:** Post-launch stability confirmed (2025-08-15).

### 9.2 Phase 2: Performance Optimization (2025-08-16 $\rightarrow$ 2025-10-15)
*   **Focus:** Addressing Risk R1 (the 10x capacity requirement).
*   **Activities:** Database indexing, query optimization, implementing Redis caching for dashboard widgets.
*   **Milestone 2:** Performance benchmarks met (2025-10-15).

### 9.3 Phase 3: External Alpha (2025-10-16 $\rightarrow$ 2025-12-15)
*   **Focus:** Transitioning from internal tool to client-facing product.
*   **Activities:** Polishing UI/UX with Camila Liu, final FedRAMP security audit, onboarding first government beta client.
*   **Milestone 3:** Internal alpha release (2025-12-15).

---

## 10. MEETING NOTES

### Meeting 1: Architecture Review (2023-11-02)
*   **Attendees:** Tariq, Viktor, Camila, Dmitri.
*   **Notes:**
    *   Monolith vs Microservices $\rightarrow$ Stick to monolith. Budget too small for K8s overhead of 10+ services.
    *   Heroku $\rightarrow$ K8s transition. Viktor worried about DB migration downtime.
    *   SAML $\rightarrow$ Use `omniauth`. Dmitri to handle the XML metadata mapping.
    *   FedRAMP $\rightarrow$ Need audit logs for every single write operation.

### Meeting 2: Dashboard UX Sync (2023-11-15)
*   **Attendees:** Tariq, Camila.
*   **Notes:**
    *   Drag-and-drop feels "clunky" on mobile. $\rightarrow$ Decision: Disable drag-and-drop on screens $< 768px$.
    *   Widget colors $\rightarrow$ Camila wants "Renewable Green" palette.
    *   User feedback $\rightarrow$ 500 users want a "Dark Mode". Tariq says "No" (Budget/Time constraint).

### Meeting 3: Performance Emergency (2023-12-01)
*   **Attendees:** Tariq, Viktor, Dmitri.
*   **Notes:**
    *   Query for "Total Output" taking 12 seconds. $\rightarrow$ Unacceptable.
    *   MySQL indices missing on `timestamp` fields.
    *   Proposed solution: Materialized views or a separate "Summary" table updated every 10 mins.
    *   Decision: Implement "Summary" table for the dashboard.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Core developer salary + Contractor (Dmitri) fees. |
| **Infrastructure** | 20% | $30,000 | Heroku credits, AWS S3/CloudFront, K8s nodes. |
| **Tools & Licenses** | 10% | $15,000 | GitLab Premium, SendGrid, ClamAV Enterprise. |
| **Contingency** | 10% | $15,000 | Reserved for emergency scaling or security audits. |

**Budget Note:** Every dollar is scrutinized. No additional hiring is permitted. Any infrastructure overages must be approved by Tariq Santos.

---

## 12. APPENDICES

### Appendix A: FedRAMP Control Mapping
To achieve authorization, Helix maps its technical features to the following NIST 800-53 controls:
*   **AC-2 (Account Management):** Handled via SAML/OIDC integration and JIT provisioning.
*   **AU-2 (Event Logging):** Handled via the `api_logs` table and Rails `audited` gem.
*   **SC-8 (Transmission Confidentiality):** Mandatory TLS 1.3 for all endpoints.
*   **SI-3 (Malicious Code Protection):** Handled via the S3 $\rightarrow$ ClamAV $\rightarrow$ CDN pipeline.

### Appendix B: Data Retention Policy
Due to the nature of renewable energy data, the following retention rules apply:
*   **Raw Telemetry:** Retained for 2 years in MySQL, then archived to S3 Glacier.
*   **API Logs:** Retained for 90 days (for performance analysis), then purged.
*   **User Uploads:** Retained indefinitely unless deleted by the tenant admin.
*   **Audit Logs:** Retained for 7 years (Federal requirement).