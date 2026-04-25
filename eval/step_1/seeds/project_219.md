# PROJECT SPECIFICATION DOCUMENT: PROJECT AQUEDUCT
**Document Version:** 1.0.4  
**Status:** Active/Development  
**Last Updated:** 2024-05-20  
**Company:** Pivot North Engineering  
**Classification:** Confidential – Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Aqueduct is a strategic machine learning model deployment and tool consolidation initiative undertaken by Pivot North Engineering. In the current operational landscape, the organization relies on four redundant internal tools to handle the lifecycle of ML model monitoring, inference auditing, and financial reporting. These legacy tools—referred to internally as "The Silos"—create significant operational friction, data duplication, and escalating maintenance costs. Aqueduct seeks to collapse these four disparate systems into a single, unified platform.

### 1.2 Business Justification
The primary driver for Aqueduct is cost reduction. Currently, Pivot North pays for four separate cloud hosting instances and allocates approximately 1.5 full-time equivalents (FTEs) just to maintain the synchronization of data between these tools. By consolidating these into a single Next.js and PostgreSQL stack, the company will realize immediate savings in infrastructure overhead and a drastic reduction in "cognitive load" for the data science and financial auditing teams.

From a competitive standpoint, the fintech industry is moving toward real-time ML observability. Our current fragmented setup prevents us from achieving the latency targets required for our high-frequency trading support models. Aqueduct will centralize the ML model deployment pipeline, ensuring that model updates are propagated across all environments simultaneously rather than in staggered waves across four different tools.

### 1.3 ROI Projection
The total budget allocated for Project Aqueduct is $1.5M. The projected Return on Investment (ROI) is calculated over a 24-month horizon:

*   **Infrastructure Savings:** Elimination of three redundant AWS clusters and associated licenses is projected to save $120,000 per annum.
*   **Operational Efficiency:** The primary success metric is a 50% reduction in manual processing time for end-users. Based on current labor costs, this efficiency gain is valued at approximately $450,000 in recovered productivity per year.
*   **Risk Mitigation:** By achieving SOC 2 Type II compliance (a prerequisite for launch), Pivot North avoids potential regulatory fines and opens the door to Enterprise-tier clients, with a projected revenue increase of $200,000 in Year 1 post-launch.

The total projected 24-month savings and revenue gain are estimated at $1.3M, meaning the project will reach a break-even point shortly after the first full year of production operation.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: CQRS and Event Sourcing
Aqueduct employs a Command Query Responsibility Segregation (CQRS) architecture. Given the fintech nature of the project, auditability is non-negotiable. Every change to a model’s configuration or a user’s permission set is treated as an immutable event.

*   **Command Side:** Handles the "write" operations. When a user updates a model hyperparameter, a command is issued, validated, and stored in the `EventStore` table.
*   **Query Side:** A read-optimized projection of the current state. This ensures that the dashboard (Next.js) can query the current state of a model without replaying thousands of events from the log.
*   **Event Sourcing:** This allows the team to "time travel" through the state of the system. If a model begins drifting in production, auditors can reconstruct the exact state of the system at the moment the model was deployed.

### 2.2 The Tech Stack
*   **Frontend/Backend:** TypeScript and Next.js (App Router). This provides a unified type system from the database to the UI.
*   **ORM:** Prisma. Used for strict schema enforcement and type-safe database queries.
*   **Database:** PostgreSQL 15.4 (Managed via Vercel Postgres/Neon).
*   **Deployment:** Vercel. Utilizing Edge Functions for low-latency API responses.
*   **Authentication:** NextAuth.js integrated with the corporate SSO.

### 2.3 Architecture Diagram (ASCII Representation)

```text
[ User / Client ]  <--->  [ Vercel Edge Network ]
                                   |
                                   v
                      [ Next.js API Routes (TS) ]
                                   |
          _________________________|_________________________
         |                         |                         |
 [ Command Handler ]        [ Query Handler ]        [ Event Store ]
         |                         |                         |
         |                         |                         |
         v                         v                         v
 [ Validation Logic ] ---> [ Prisma ORM ] <--- [ PostgreSQL Database ]
                                   |
                                   | (Async Projection)
                                   v
                         [ Read-Optimized Views ]
```

### 2.4 Data Flow
1.  **Ingestion:** Data enters via the Customer API or internal webhooks.
2.  **Command:** The request is validated against the current schema.
3.  **Persistence:** The event is appended to the `EventStore` table.
4.  **Projection:** A background worker (or Prisma middleware) updates the `CurrentState` tables.
5.  **Delivery:** The Next.js frontend fetches the state from the read-optimized views via Server Components.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-facing API with Versioning and Sandbox (Priority: High)
**Status:** In Progress  
**Description:** The core of Aqueduct is the ability for external partners and internal teams to programmatically interact with the ML models. This feature requires a robust API gateway that supports both a "Sandbox" environment (for testing) and a "Production" environment.

**Functional Requirements:**
*   **Versioning:** The API must support URI versioning (e.g., `/v1/`, `/v2/`). This prevents breaking changes when the ML model schema evolves.
*   **Sandbox Environment:** A mirrored version of the production environment where users can test payloads without affecting production metrics or triggering real-world financial transactions.
*   **Rate Limiting:** Implementation of a tiered rate-limiting system (100 requests/min for Sandbox, 5,000 requests/min for Production).
*   **Authentication:** API Key-based authentication with rotating secret keys.

**Technical Implementation:**
The API is built using Next.js Route Handlers. The sandbox is logically separated in the PostgreSQL database using a `tenant_id` or `environment_id` flag. The versioning is handled via a middleware layer that maps requests to the appropriate controller version.

**Success Criteria:**
Users can successfully authenticate and receive a prediction from a model in the sandbox environment without altering the production state.

---

### 3.2 PDF/CSV Report Generation with Scheduled Delivery (Priority: Medium)
**Status:** In Review  
**Description:** Fintech stakeholders require immutable snapshots of model performance for compliance. This feature automates the generation of these reports and delivers them via email or S3 upload.

**Functional Requirements:**
*   **Format Support:** Ability to export data into `.pdf` (for executives) and `.csv` (for data analysts).
*   **Scheduling:** A cron-based scheduler allowing users to set reports for "Daily," "Weekly," or "Monthly" delivery.
*   **Templating:** Use of a predefined HTML/CSS template that is converted to PDF via a headless browser (Puppeteer).
*   **Delivery:** Integration with SendGrid for email delivery and AWS S3 for long-term archival.

**Technical Implementation:**
The system uses a background worker (via Vercel Cron Jobs) that triggers a report generation function. The function queries the read-optimized views of the CQRS architecture, formats the data into a table, and uses a PDF generation library to create the final document.

**Success Criteria:**
A scheduled report is generated and delivered to the stakeholder's email inbox within 15 minutes of the scheduled trigger time.

---

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets (Priority: Medium)
**Status:** Blocked  
**Description:** A visual interface allowing users to build their own monitoring cockpit. Users can add widgets such as "Model Accuracy Gauge," "Latency Histogram," and "Error Rate Table."

**Functional Requirements:**
*   **Drag-and-Drop:** Users can rearrange widgets using a grid system (e.g., React-Grid-Layout).
*   **Widget Library:** A set of pre-built components that can be configured with different data sources (different models or timeframes).
*   **Persistence:** The dashboard layout must be saved to the user's profile in the database so it persists across sessions.
*   **Real-time Updates:** Use of SWR or React Query to poll for updated ML metrics without refreshing the page.

**Technical Implementation:**
The frontend uses a JSON-based layout schema stored in the `UserDashboards` table. When the page loads, the system fetches the JSON, iterates through the widget list, and dynamically renders the corresponding React components.

**Current Blocker:** This feature is currently blocked due to third-party API rate limits. The visualization widgets rely on high-frequency data fetches from the ML inference engine, which is currently triggering 429 (Too Many Requests) errors during the testing phase.

---

### 3.4 Data Import/Export with Format Auto-detection (Priority: Low)
**Status:** In Progress  
**Description:** A utility to migrate data from the four legacy tools into Aqueduct. The system must be able to distinguish between JSON, CSV, and XML files automatically.

**Functional Requirements:**
*   **Auto-detection:** The system analyzes the first 1KB of an uploaded file to determine the MIME type and structure.
*   **Mapping Interface:** A UI that allows users to map columns from the uploaded file to the Aqueduct database schema.
*   **Validation:** Pre-import validation to ensure data types (e.g., ensuring a "timestamp" column actually contains dates).
*   **Bulk Export:** Ability to export the entire dataset for a specific model in a compressed `.zip` format.

**Technical Implementation:**
Using a combination of `multer` for file uploads and a custom detection script. The mapping is stored as a temporary JSON object before being committed to the database via a Prisma `createMany` transaction.

**Success Criteria:**
A user can upload a CSV file from "Silo Tool 1" and "Silo Tool 2," and the system correctly imports the data into the unified `ModelMetrics` table.

---

### 3.5 Webhook Integration Framework for Third-Party Tools (Priority: Low)
**Status:** Complete  
**Description:** A framework that allows Aqueduct to push events to external systems (e.g., Slack, PagerDuty, or custom internal dashboards) when specific ML thresholds are breached.

**Functional Requirements:**
*   **Event Triggers:** Ability to define triggers (e.g., "Accuracy < 85%").
*   **Payload Configuration:** Users can define a custom JSON payload to be sent to the destination URL.
*   **Retry Logic:** Exponential backoff for failed webhook deliveries (max 5 retries).
*   **Security:** Signing of webhook payloads using an HMAC signature to allow the receiver to verify the sender.

**Technical Implementation:**
A dedicated `Webhook` table stores the target URLs and event types. When a trigger is hit, an event is pushed to a queue (using a simple Postgres-based queue) which is then processed by a background worker that executes the HTTP POST request.

**Success Criteria:**
An alert is triggered in a test Slack channel within 30 seconds of a simulated model accuracy drop.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under `https://api.pivotnorth.com/v1/`. All requests require an `X-API-Key` header.

### 4.1 Get Model Status
`GET /models/:id/status`  
Returns the current health and deployment status of a specific ML model.
*   **Request:** `GET /models/mod_7721/status`
*   **Response (200 OK):**
    ```json
    {
      "model_id": "mod_7721",
      "status": "healthy",
      "uptime": "99.98%",
      "last_deployed": "2024-05-10T12:00:00Z"
    }
    ```

### 4.2 Create Prediction Request
`POST /predict`  
Sends data to the ML model for an inference result.
*   **Request:**
    ```json
    {
      "model_id": "mod_7721",
      "features": [0.5, 1.2, -0.3, 0.8],
      "environment": "sandbox"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "prediction_id": "pred_9901",
      "value": 0.87,
      "confidence": 0.94,
      "latency_ms": 42
    }
    ```

### 4.3 Trigger Manual Report
`POST /reports/generate`  
Forces the immediate generation of a PDF/CSV report.
*   **Request:**
    ```json
    {
      "model_id": "mod_7721",
      "format": "pdf",
      "timeframe": "last_30_days"
    }
    ```
*   **Response (202 Accepted):**
    ```json
    {
      "job_id": "job_abc123",
      "status": "queued",
      "estimated_completion": "2024-05-20T14:05:00Z"
    }
    ```

### 4.4 Update Model Config
`PATCH /models/:id/config`  
Updates hyperparameters or deployment settings.
*   **Request:**
    ```json
    {
      "hyperparameters": { "learning_rate": 0.001 },
      "version": "2.1.0"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "model_id": "mod_7721",
      "updated_at": "2024-05-20T10:00:00Z",
      "event_id": "evt_5544"
    }
    ```

### 4.5 List Dashboard Widgets
`GET /dashboards/widgets`  
Retrieves all available widgets for the current user's layout.
*   **Request:** `GET /dashboards/widgets`
*   **Response (200 OK):**
    ```json
    [
      { "id": "w_1", "type": "gauge", "name": "Accuracy" },
      { "id": "w_2", "type": "line_chart", "name": "Latency" }
    ]
    ```

### 4.6 Set Webhook Trigger
`POST /webhooks/triggers`  
Configures a new event-driven notification.
*   **Request:**
    ```json
    {
      "event": "model_drift",
      "threshold": 0.05,
      "target_url": "https://hooks.slack.com/services/T000/B000/XXXX"
    }
    ```
*   **Response (201 Created):**
    ```json
    { "webhook_id": "wh_123", "status": "active" }
    ```

### 4.7 Import Legacy Data
`POST /import/legacy`  
Uploads a file for auto-detection and ingestion.
*   **Request:** Multipart/form-data containing `file` and `source_tool_id`.
*   **Response (200 OK):**
    ```json
    {
      "import_id": "imp_887",
      "rows_detected": 15000,
      "status": "processing"
    }
    ```

### 4.8 Delete Model Version
`DELETE /models/:id/versions/:version_id`  
Removes a specific version of a model from the registry.
*   **Request:** `DELETE /models/mod_7721/versions/v1.0.2`
*   **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL instance managed via Prisma. Due to the CQRS architecture, the schema is split between "Event" tables (Immutable) and "State" tables (Mutable).

### 5.1 Tables and Definitions

1.  **`Users`**
    *   `id`: UUID (PK)
    *   `email`: String (Unique)
    *   `role`: Enum (ADMIN, VIEWER, OPERATOR)
    *   `created_at`: Timestamp
2.  **`Models`** (The Current State)
    *   `id`: UUID (PK)
    *   `name`: String
    *   `current_version`: String
    *   `status`: Enum (ACTIVE, DEPRECATED, TESTING)
    *   `created_by`: UUID (FK -> Users)
3.  **`EventStore`** (The Source of Truth)
    *   `id`: BigInt (PK)
    *   `aggregate_id`: UUID (The Model/User ID being changed)
    *   `event_type`: String (e.g., "MODEL_UPDATED")
    *   `payload`: JSONB (The actual change data)
    *   `timestamp`: Timestamp (Indexed)
4.  **`ModelMetrics`** (Read-optimized)
    *   `id`: UUID (PK)
    *   `model_id`: UUID (FK -> Models)
    *   `accuracy`: Decimal
    *   `latency`: Integer (ms)
    *   `timestamp`: Timestamp
5.  **`UserDashboards`**
    *   `id`: UUID (PK)
    *   `user_id`: UUID (FK -> Users)
    *   `layout_json`: JSONB (Stores widget positions and sizes)
    *   `updated_at`: Timestamp
6.  **`Reports`**
    *   `id`: UUID (PK)
    *   `model_id`: UUID (FK -> Models)
    *   `file_url`: String (S3 Link)
    *   `format`: Enum (PDF, CSV)
    *   `generated_at`: Timestamp
7.  **`ReportSchedules`**
    *   `id`: UUID (PK)
    *   `user_id`: UUID (FK -> Users)
    *   `cron_expression`: String (e.g., "0 0 * * 1")
    *   `target_email`: String
8.  **`Webhooks`**
    *   `id`: UUID (PK)
    *   `target_url`: String
    *   `secret`: String (Hashed)
    *   `is_active`: Boolean
9.  **`WebhookEvents`**
    *   `id`: UUID (PK)
    *   `webhook_id`: UUID (FK -> Webhooks)
    *   `status`: Enum (SENT, FAILED, RETRYING)
    *   `attempt_count`: Integer
10. **`ImportLogs`**
    *   `id`: UUID (PK)
    *   `source_tool`: String
    *   `rows_processed`: Integer
    *   `error_log`: Text
    *   `completed_at`: Timestamp

### 5.2 Relationships
*   **One-to-Many:** `Users` $\rightarrow$ `Models` (A user can create many models).
*   **One-to-Many:** `Models` $\rightarrow$ `ModelMetrics` (A model has thousands of metric entries).
*   **One-to-Many:** `Models` $\rightarrow$ `EventStore` (Each model change generates one or more events).
*   **One-to-One:** `Users` $\rightarrow$ `UserDashboards` (Each user has one primary dashboard configuration).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Aqueduct utilizes a three-tier environment strategy to ensure stability and SOC 2 compliance.

#### 6.1.1 Development (`dev`)
*   **Purpose:** Rapid iteration and feature development.
*   **Infrastructure:** Vercel Preview Deployments.
*   **Database:** Shared development PostgreSQL instance with mocked ML data.
*   **Deployment:** Automatic on every push to a feature branch.

#### 6.1.2 Staging (`staging`)
*   **Purpose:** Final QA, UAT (User Acceptance Testing), and SOC 2 audit verification.
*   **Infrastructure:** Dedicated Vercel staging project.
*   **Database:** A sanitized clone of the production database.
*   **Deployment:** Triggered by merging a feature branch into the `staging` branch. **Requirement:** Manual QA gate. A developer must sign off on the staging build before it can be promoted to production.

#### 6.1.3 Production (`prod`)
*   **Purpose:** Live customer-facing environment.
*   **Infrastructure:** Vercel Production with multi-region edge caching.
*   **Database:** High-availability PostgreSQL with automated backups every 6 hours.
*   **Deployment:** 2-day turnaround. Deployment occurs only after the QA gate is passed and the Security Engineer (Lior Stein) approves the change set.

### 6.2 Infrastructure as Code (IaC)
While Vercel handles the frontend and serverless functions, the database and S3 buckets are managed via Terraform. This ensures that the environment can be replicated exactly in the event of a regional outage.

### 6.3 SOC 2 Compliance Requirements
Before the Production launch on 2025-10-15, the following must be implemented:
*   **Audit Logs:** All `EventStore` entries must be immutable and backed up in a WORM (Write Once, Read Many) storage.
*   **Encryption:** All data at rest must be encrypted via AES-256; all data in transit must use TLS 1.3.
*   **Access Control:** Role-Based Access Control (RBAC) enforced at the API level.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tooling:** Vitest.
*   **Focus:** Business logic, data transformation functions, and API request validators.
*   **Coverage Goal:** 80% of all utility functions and controllers.
*   **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
*   **Tooling:** Playwright and Supertest.
*   **Focus:** The interaction between the Next.js API and the PostgreSQL database via Prisma.
*   **Scenario:** Testing the CQRS flow—issuing a command, verifying the `EventStore` entry, and then querying the projected state to ensure consistency.
*   **Execution:** Run during the staging deployment phase.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Focus:** Critical user paths (e.g., "User logs in $\rightarrow$ navigates to dashboard $\rightarrow$ exports a PDF report").
*   **Environment:** Staging environment.
*   **Execution:** Full suite run before the manual QA gate sign-off.

### 7.4 Performance Testing
*   **Tooling:** k6.
*   **Focus:** API latency under load, specifically for the `/predict` endpoint.
*   **Goal:** Maintain $<100\text{ms}$ latency for 95% of requests at 500 requests per second.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Scope creep from stakeholders adding 'small' features. | High | Medium | Hire a contractor to reduce the bus factor and increase velocity. |
| R2 | Competitor is building the same product and is 2 months ahead. | Medium | High | Raise as a critical blocker in the next board meeting to secure more resources. |
| R3 | SOC 2 audit failure on first attempt. | Low | High | Conduct a pre-audit internal review with Lior Stein's security team. |
| R4 | Data loss during migration from legacy tools. | Medium | High | Implement a "Dual Write" period where data is written to both old and new systems. |
| R5 | Vercel Cold Starts affecting API latency. | Medium | Medium | Implement "Warm-up" pings or upgrade to Vercel's Pro/Enterprise dedicated concurrency. |

**Probability/Impact Matrix:**
*   **High/High:** Immediate Action Required.
*   **High/Medium:** Active Monitoring.
*   **Low/High:** Contingency Planning.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with a strict dependency on the SOC 2 audit.

### 9.1 Phase 1: Core Infrastructure (Jan 2025 – Aug 2025)
*   **Objective:** Build the CQRS foundation and Customer API.
*   **Dependencies:** Finalization of the ML model schema.
*   **Milestone 1:** **Internal Alpha Release (2025-08-15)**.
    *   *Deliverable:* Functional API and basic dashboard for internal Pivot North staff.

### 9.2 Phase 2: Feature Completion & Compliance (Aug 2025 – Oct 2025)
*   **Objective:** Complete reporting, import/export, and security hardening.
*   **Dependencies:** Successful "Sandbox" testing of the API.
*   **Milestone 2:** **Production Launch (2025-10-15)**.
    *   *Deliverable:* Full production deployment after passing SOC 2 Type II audit.

### 9.3 Phase 3: Optimization & Sign-off (Oct 2025 – Dec 2025)
*   **Objective:** Polish UI/UX and ensure stakeholders are satisfied.
*   **Dependencies:** Production telemetry data to prove 50% reduction in manual processing.
*   **Milestone 3:** **Stakeholder Demo and Sign-off (2025-12-15)**.
    *   *Deliverable:* Final project handover and budget reconciliation.

---

## 10. MEETING NOTES

*Note: The following are excerpts from the shared running document (200+ pages). The document is currently unsearchable and maintained as a linear chronological log.*

### Meeting 1: Project Kickoff (2024-05-01)
**Attendees:** Thiago Moreau, Paloma Kim, Lior Stein, Chioma Nakamura.
*   **Thiago:** Emphasized that $1.5M is a healthy budget, but we cannot afford a delayed launch. The board is watching the competitor's progress.
*   **Paloma:** Raised concerns about the state of the data in the 4 legacy tools. Suggested a "data cleaning" phase before the import feature is built.
*   **Lior:** Stated clearly that SOC 2 is non-negotiable. If we don't have the audit trails in the database, we won't launch.
*   **Decision:** Agreed on CQRS. It solves Lior's audit requirements and Paloma's data consistency issues.

### Meeting 2: Technical Pivot (2024-06-15)
**Attendees:** Thiago Moreau, Paloma Kim, Chioma Nakamura.
*   **Chioma:** Reported that support tickets for the legacy tools are spiking. Users are frustrated by the manual data sync.
*   **Thiago:** Asked why the dashboard is blocked.
*   **Paloma:** Explained the 429 rate limit issues with the third-party API. We are hitting the limit because the dashboard polls every 5 seconds.
*   **Decision:** Move the dashboard to a lower priority for now. Focus on the Customer API to get the "plumbing" right first.

### Meeting 3: Resource Review (2024-08-02)
**Attendees:** Thiago Moreau, Lior Stein.
*   **Thiago:** Noted that the project is essentially a "solo developer" effort currently, which is a massive risk (bus factor).
*   **Lior:** Agreed. If the lead developer is unavailable for a week, the entire timeline slips.
*   **Thiago:** Proposed hiring a specialized TypeScript/Prisma contractor for 3 months to handle the "nice to have" features (webhooks and imports).
*   **Decision:** Approved budget for a contractor. Thiago will handle the sourcing.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$1,500,000.00**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Lead Developer + Contractor | $850,000 | Includes base salary, bonuses, and contractor fees. |
| **Infrastructure** | Vercel Enterprise + AWS S3 + Neon DB | $120,000 | Projected for 2 years of operation. |
| **Security & Audit** | SOC 2 Certification Firm | $200,000 | External auditors and compliance software. |
| **Software Tools** | GitHub, SendGrid, Datadog, Jira | $30,000 | Annual licensing. |
| **Contingency** | Emergency Fund | $300,000 | For scope creep or unexpected infrastructure costs. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The following items are acknowledged as technical debt that must be addressed before Milestone 3:
1.  **Structured Logging:** Currently, the system has no structured logging. Debugging production issues requires reading `stdout` from Vercel logs, which is inefficient. *Action: Implement Winston or Pino logging with JSON output.*
2.  **Database Indexing:** Several query-side views are performing full table scans. *Action: Add composite indexes to `ModelMetrics` and `EventStore`.*
3.  **Type Casting:** Some legacy data imports use `any` types in TypeScript. *Action: Refactor to strict Zod schemas.*

### Appendix B: Model Deployment Pipeline
The deployment of an ML model follows this sequence:
1.  **Model Registry:** Model is uploaded to the internal registry.
2.  **Canary Stage:** Model is deployed to 5% of traffic.
3.  **Observation:** System monitors `ModelMetrics` for 24 hours.
4.  **Promotion:** If accuracy is $\ge$ previous version and latency is $\le 100\text{ms}$, the model is promoted to `ACTIVE`.
5.  **Event Log:** An event `MODEL_PROMOTED` is written to the `EventStore`.