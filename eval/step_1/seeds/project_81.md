# PROJECT SPECIFICATION: PROJECT TRELLIS
**Version:** 1.0.4-BETA  
**Date:** October 24, 2024  
**Project Owner:** Lior Moreau, VP of Product  
**Company:** Crosswind Labs  
**Classification:** Confidential / R&D Moonshot  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Trellis is a high-stakes research and development initiative by Crosswind Labs designed to establish a next-generation IoT device network specifically tailored for the renewable energy sector. The renewable energy landscape is currently fragmented; wind turbines, solar arrays, and hydroelectric sensors often operate on proprietary, siloed protocols. Trellis aims to act as the "connective tissue" (hence the name) that aggregates diverse telemetry data from disparate energy assets into a single, interoperable stream.

As a "moonshot" project, Trellis is not designed for immediate, guaranteed profitability. Instead, it is positioned as a strategic hedge. By developing a hardware-agnostic network layer, Crosswind Labs can move from being a component provider to a platform provider. The executive sponsorship for Trellis is rooted in the belief that the first company to standardize the "Energy-IoT" interface will capture a dominant share of the smart-grid management market.

### 1.2 ROI Projection and Financial Objectives
The ROI for Trellis is categorized as "High Variance." While the initial investment is significant, the projected upside involves a shift from one-time hardware sales to recurring SaaS-based monitoring subscriptions. 

**Financial Success Metric:** The primary target is to realize **$500,000 in new revenue** attributed directly to Trellis features or subscriptions within the first 12 months of general availability. This revenue is expected to stem from three primary sources:
1. **Pilot Program Fees:** Paid access for the 10 initial beta users.
2. **Integration Licenses:** Charging third-party hardware vendors to be "Trellis Certified."
3. **Premium Analytics:** Tiered pricing for the visual rule builder and automation engine.

### 1.3 Strategic Objectives
The project intends to bridge the gap between legacy energy infrastructure and modern cloud computing. By focusing on a modular monolith architecture that evolves into microservices, the project maintains the agility of a small team (4 members) while ensuring the scalability required for industrial-grade energy grids. The core goal is to prove that a unified IoT layer can reduce operational downtime in wind and solar farms by 15% through predictive automation.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Philosophy
Trellis is built upon a "Mixed Stack" inheritance. Due to previous acquisitions and legacy prototypes, the system must interoperate across three distinct technology bases:
1. **Legacy Stack A (C++/Embedded):** Low-level device firmware and MQTT brokers.
2. **Legacy Stack B (Python/Django):** Data processing pipelines and administrative tooling.
3. **Legacy Stack C (Node.js/TypeScript):** The modern user-facing API and real-time dashboard.

The architecture is currently a **Modular Monolith**. This allows the small team to maintain a single deployment pipeline while enforcing strict boundary separation between modules (e.g., the "Billing Module" cannot directly query the "Device Telemetry" database table without going through the Telemetry Service layer). As the system scales and performance benchmarks are met, these modules will be decoupled into independent microservices.

### 2.2 ASCII Architecture Diagram
```text
[IoT Device Layer] ----> [MQTT Broker (Stack A)] ----> [Ingestion Engine]
                                                              |
                                                              v
[User Interface] <---- [API Gateway (Stack C)] <---- [Modular Monolith]
      ^                         |                            |
      |                         |                            v
[LaunchDarkly] <----------------+------------------> [PostgreSQL DB / TimescaleDB]
(Feature Flags)                                        (Telemetry & State)
                                                              |
                                                              v
                                                     [S3 Bucket / PDF Gen]
                                                     (Report Generation)
```

### 2.3 Infrastructure and Communication
*   **Communication:** Asynchronous communication is handled via RabbitMQ to ensure that spikes in telemetry data do not crash the API gateway.
*   **State Management:** Redis is utilized for caching rate-limit counters and session tokens.
*   **Deployment Strategy:** We employ **Canary Releases**. New code is deployed to 5% of the device network first. If telemetry errors increase, the version is automatically rolled back.
*   **Feature Gating:** All new features (especially the Rule Builder and Localization) are wrapped in **LaunchDarkly** feature flags. This allows the VP of Product to toggle features for specific pilot users without requiring a full redeployment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:** 
To prevent "noisy neighbor" syndrome and protect the system from DDoS attacks or malfunctioning IoT sensors, Trellis requires a robust rate-limiting layer. This system must track requests per second (RPS) per API key and provide a detailed analytics dashboard for administrators.

**Functional Requirements:**
- **Sliding Window Algorithm:** Implement a sliding window log to prevent bursts of traffic at the edge of a fixed-time window.
- **Tiered Limits:** 
    - *Free Tier:* 100 requests/minute.
    - *Pilot Tier:* 1,000 requests/minute.
    - *Enterprise Tier:* 10,000 requests/minute.
- **HTTP 429 Responses:** When a limit is exceeded, the API must return a `429 Too Many Requests` header including `X-RateLimit-Reset` (timestamp).
- **Analytics Tracking:** Every request must be logged to a time-series database, tracking:
    - Endpoint hit.
    - Response code.
    - Latency (ms).
    - Client ID.

**Technical Logic:**
The rate limiter will be implemented as a middleware in the Node.js API Gateway. It will query Redis using a key composed of the `api_key` and the current `minute_timestamp`. If the count exceeds the threshold stored in the `UserTiers` table, the request is rejected before hitting the backend monolith.

---

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:** 
Renewable energy data comes in various formats (JSON, XML, CSV, and proprietary binary formats from old turbines). Trellis must allow users to upload historical data files and have the system "guess" the format and map the columns to the internal schema.

**Functional Requirements:**
- **Auto-Detection Engine:** The system must read the first 1KB of any uploaded file to detect magic bytes or structural markers (e.g., `{` for JSON, `<` for XML, or comma-delimited patterns for CSV).
- **Schema Mapping Interface:** If the system is unsure of a column (e.g., is "Temp_C" the same as "Celsius_Reading"?), it must present a UI for the user to manually map the source column to the Trellis standard field.
- **Bulk Import Pipeline:** To prevent timeouts, imports must be processed as background jobs using Celery.
- **Export Capabilities:** Users must be able to export filtered datasets in `.json`, `.csv`, and `.parquet` formats for use in external data science tools (like Pandas or R).

**Technical Logic:**
The backend will utilize a "Strategy Pattern" for importers. A `BaseImporter` class will be extended by `JsonImporter`, `CsvImporter`, and `XmlImporter`. The `FormatDetector` service will analyze the file header and instantiate the appropriate strategy.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** Blocked

**Description:** 
The core value proposition of Trellis is the ability to automate responses to environmental data. For example: "If wind speed > 80km/h AND turbine_brake = False, then trigger Brake_Solenoid AND send alert to Engineer."

**Functional Requirements:**
- **Visual Drag-and-Drop Interface:** A React-based canvas where users can drag "Triggers" (e.g., Sensor Threshold) and "Actions" (e.g., MQTT Command).
- **Boolean Logic Support:** Support for AND, OR, and NOT operators within the rule builder.
- **Execution Engine:** A high-performance listener that evaluates rules in real-time as telemetry packets arrive.
- **Conflict Resolution:** A mechanism to prevent contradictory rules (e.g., one rule saying "Turn On" and another saying "Turn Off" for the same device simultaneously).

**Technical Logic:**
Rules will be stored in the database as JSON-logic trees. The execution engine will compile these trees into a temporary cached bytecode that is evaluated against incoming telemetry streams in the Ingestion Engine. *Current Blocker: The team is waiting on the final hardware API specs for the Brake Solenoid from the manufacturer.*

---

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Not Started

**Description:** 
Industrial clients require formal reports for regulatory compliance. Trellis must generate professional PDFs and CSVs summarizing energy production and system health.

**Functional Requirements:**
- **Template Engine:** Ability to create custom report templates with placeholders for graphs, tables, and company logos.
- **Scheduling Logic:** A cron-based scheduler allowing users to receive reports (Daily, Weekly, Monthly) via email.
- **Aggregation Queries:** The system must perform heavy aggregations (SUM, AVG, MAX) over large datasets in TimescaleDB to populate reports without crashing the API.
- **Delivery Integration:** Integration with SendGrid for email delivery and S3 for long-term storage of generated PDFs.

**Technical Logic:**
A dedicated "Reporting Service" will be created. It will use `Puppeteer` to render HTML templates into PDFs. To avoid performance degradation during the "Monday Morning Report Rush," the service will use a priority queue, processing "Critical" reports before "Standard" reports.

---

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:** 
Crosswind Labs operates globally. Trellis must support 12 different languages to accommodate operators in Europe, Asia, and the Americas.

**Functional Requirements:**
- **12 Supported Languages:** English, Spanish, French, German, Mandarin, Japanese, Korean, Portuguese, Arabic, Hindi, Dutch, and Italian.
- **Dynamic Translation Keys:** No hard-coded strings in the UI; all text must be referenced via keys (e.g., `dashboard.welcome_message`) in JSON translation files.
- **Right-to-Left (RTL) Support:** The UI must support RTL layouts for Arabic.
- **Locale-Aware Formatting:** Dates, currency ($ vs €), and units (Metric vs Imperial) must adjust based on the user's profile settings.

**Technical Logic:**
Using `i18next` for the frontend and a database-backed translation table for dynamic content. A middleware will detect the `Accept-Language` header from the browser and serve the corresponding locale.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 Device Management
**1. GET `/v1/devices`**
*   **Description:** Retrieve a list of all registered IoT devices.
*   **Request:** `GET /v1/devices?status=active`
*   **Response (200 OK):**
    ```json
    [
      {"id": "dev_001", "type": "wind_turbine", "status": "active", "last_seen": "2024-10-24T10:00Z"},
      {"id": "dev_002", "type": "solar_inverter", "status": "offline", "last_seen": "2024-10-23T15:00Z"}
    ]
    ```

**2. POST `/v1/devices`**
*   **Description:** Register a new device in the network.
*   **Request Body:** `{"device_name": "Turbine_North_01", "model": "X-100", "location": {"lat": 45.5, "lng": -122.6}}`
*   **Response (201 Created):** `{"id": "dev_003", "status": "provisioning"}`

### 4.2 Telemetry and Data
**3. GET `/v1/telemetry/{device_id}`**
*   **Description:** Get the most recent telemetry readings for a device.
*   **Request:** `GET /v1/telemetry/dev_001?limit=10`
*   **Response (200 OK):**
    ```json
    {
      "device_id": "dev_001",
      "readings": [
        {"timestamp": "2024-10-24T10:01Z", "wind_speed": 12.4, "output_kw": 2.1},
        {"timestamp": "2024-10-24T10:02Z", "wind_speed": 13.1, "output_kw": 2.3}
      ]
    }
    ```

**4. POST `/v1/telemetry/batch`**
*   **Description:** Bulk upload telemetry data (used by the Import feature).
*   **Request Body:** `[{"device_id": "dev_001", "ts": "...", "val": 10.5}, {...}]`
*   **Response (202 Accepted):** `{"job_id": "job_abc123", "status": "processing"}`

### 4.3 Automation and Rules
**5. POST `/v1/rules`**
*   **Description:** Create a new automation rule.
*   **Request Body:** `{"name": "High Wind Stop", "trigger": {"field": "wind_speed", "op": ">", "val": 80}, "action": "stop_turbine"}`
*   **Response (201 Created):** `{"rule_id": "rule_99", "status": "enabled"}`

**6. DELETE `/v1/rules/{rule_id}`**
*   **Description:** Remove an automation rule.
*   **Response (204 No Content):** (Empty)

### 4.4 Analytics and Reporting
**7. GET `/v1/analytics/usage`**
*   **Description:** Retrieve API usage stats for the current billing cycle.
*   **Response (200 OK):** `{"total_requests": 45000, "limit": 50000, "percentage_used": 90.0}`

**8. POST `/v1/reports/generate`**
*   **Description:** Manually trigger a PDF report generation.
*   **Request Body:** `{"report_type": "monthly_efficiency", "device_group": "north_sector", "format": "pdf"}`
*   **Response (202 Accepted):** `{"download_url": "https://s3.crosswind.io/reports/rep_789.pdf", "expires_in": 3600}`

---

## 5. DATABASE SCHEMA

The project uses a hybrid approach: **PostgreSQL** for relational data and **TimescaleDB** (extension of Postgres) for time-series telemetry data.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | - | `email`, `password_hash`, `role` | User accounts and authentication. |
| `Organizations` | `org_id` | - | `org_name`, `billing_address` | Company entities owning the devices. |
| `UserOrgMap` | `map_id` | `user_id`, `org_id` | `permission_level` | Maps users to organizations. |
| `Devices` | `device_id` | `org_id` | `model_no`, `firmware_ver`, `status` | Registry of all IoT hardware. |
| `DeviceMetrics` | `metric_id` | `device_id` | `metric_name`, `unit` | Definition of what a device measures. |
| `Telemetry` | `ts` (Hypertable) | `device_id` | `value`, `quality_code` | Time-series data (TimescaleDB). |
| `AutomationRules` | `rule_id` | `org_id` | `logic_json`, `is_active` | Store for the visual rule builder. |
| `AuditLogs` | `log_id` | `user_id` | `action`, `timestamp`, `ip_addr` | Tracking all admin changes. |
| `ApiKeys` | `key_id` | `org_id` | `key_hash`, `rate_limit_tier` | Tokens for external API access. |
| `ReportSchedules` | `sched_id` | `org_id` | `cron_expression`, `email_dest` | Scheduled report delivery settings. |

### 5.2 Relationships
*   **One-to-Many:** `Organizations` $\rightarrow$ `Devices`. One company manages many turbines.
*   **Many-to-Many:** `Users` $\leftrightarrow$ `Organizations` via `UserOrgMap`.
*   **One-to-Many:** `Devices` $\rightarrow$ `Telemetry`. One device generates millions of data points.
*   **One-to-Many:** `Organizations` $\rightarrow$ `AutomationRules`. Rules are scoped to the org level.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Trellis utilizes three distinct environments to ensure stability.

**1. Development (Dev):**
*   **Purpose:** Feature experimentation and unit testing.
*   **Infrastructure:** Local Docker Compose setups and a shared "Dev" cloud instance.
*   **Database:** Mock data; wiped weekly.
*   **CI/CD:** Triggered on every push to `develop` branch.

**2. Staging (Staging):**
*   **Purpose:** Integration testing and UAT (User Acceptance Testing) for pilot users.
*   **Infrastructure:** Mirror of Production (AWS t3.medium instances).
*   **Database:** Anonymized snapshot of production data.
*   **Deployment:** Triggered on merge to `release` branch. This is where **Canary Releases** are first validated.

**3. Production (Prod):**
*   **Purpose:** Live customer operations.
*   **Infrastructure:** AWS Auto-scaling groups, Multi-AZ deployment.
*   **Database:** High-availability PostgreSQL cluster with daily backups to S3.
*   **Deployment:** Manual trigger after Staging approval. Feature flags via **LaunchDarkly** control the final rollout.

### 6.2 CI/CD Pipeline and Technical Debt
The current CI pipeline is a significant point of friction.
*   **Current State:** The pipeline takes **45 minutes** to complete. This is due to a sequential execution of the test suite and a slow image build process.
*   **Debt Identification:** No parallelization has been implemented. The pipeline runs integration tests for all three inherited stacks in a single thread.
*   **Immediate Goal:** Reduce pipeline time to <10 minutes by implementing GitHub Action runners with parallel job matrices and caching `node_modules` and `pip` dependencies.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions, utility classes, and logic gates.
*   **Tools:** `Jest` (Node.js), `PyTest` (Python), `GoogleTest` (C++).
*   **Requirement:** 80% code coverage for all new "Trellis" modules. Legacy stacks are tested on a "fix-as-you-touch" basis.

### 7.2 Integration Testing
*   **Focus:** Interoperability between the three inherited stacks.
*   **Scenario:** A telemetry packet is sent from the C++ MQTT broker $\rightarrow$ processed by the Python engine $\rightarrow$ served via the Node.js API.
*   **Tools:** `Postman/Newman` for API contract testing.
*   **Frequency:** Run on every merge to the `develop` branch.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** User journeys (e.g., "User creates a rule and the device reacts").
*   **Tools:** `Playwright` for browser automation.
*   **Environment:** Only run in Staging.
*   **Critical Path:** The "Launch Blocker" features (Rate Limiting, Import, Rule Builder, Localization) must have 100% E2E pass rates before Milestone 1.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect leaving in 3 months | High | Critical | Escalate to steering committee for immediate funding to hire a replacement or provide a retention bonus. |
| **R-02** | 10x Perf requirements vs 0 budget | Medium | High | Document technical workarounds (e.g., aggressive caching, data downsampling) and share with the team to manage expectations. |
| **R-03** | Inherited Stack Conflict | Medium | Medium | Maintain strict API contracts between stacks to prevent "leaky abstractions." |
| **R-04** | Rule Builder Blockage | High | High | Parallelize development by using a "mock" hardware API until the manufacturer provides the final specs. |

**Probability/Impact Matrix:**
*   **High/Critical:** Immediate action required. (R-01)
*   **Medium/High:** Closely monitored. (R-02, R-04)
*   **Medium/Medium:** Managed via standard process. (R-03)

---

## 9. TIMELINE

### 9.1 Phase Descriptions

**Phase 1: Foundation (Current - March 2025)**
*   **Focus:** Resolving launch blockers.
*   **Dependencies:** Localization files must be completed before the UI can be finalized for beta users.
*   **Key Target:** Milestone 1 (External Beta) on **2025-03-15**.

**Phase 2: Stabilization (March 2025 - May 2025)**
*   **Focus:** Refining the Modular Monolith and cleaning up the CI pipeline.
*   **Dependencies:** Performance benchmarks must be baseline-tested before the architecture review.
*   **Key Target:** Milestone 2 (Architecture Review) on **2025-05-15**.

**Phase 3: Scale and Optimize (May 2025 - July 2025)**
*   **Focus:** Transitioning critical paths to microservices.
*   **Dependencies:** High-load simulation must be completed.
*   **Key Target:** Milestone 3 (Performance Benchmarks) on **2025-07-15**.

### 9.2 Gantt-Style Summary
`[Jan] ---- [Feb] ---- [Mar] ---- [Apr] ---- [May] ---- [Jun] ---- [Jul]`
`[---Blocker Fixes---] [Beta Launch] [---Refinement---] [Arch Review] [---Scaling---] [Perf Benchmarks]`
`| (L10n, RateLim, Imp) | (M1) | | | (M2) | | (M3) |`

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project norms, formal meeting minutes are not kept. The following are synthesized from decision threads in the `#trellis-dev` Slack channel.*

### Thread 1: The "CI Pipeline Pain" (2024-11-02)
**Kai Santos:** "Is it just me or is the CI taking forever? I waited 45 minutes for a typo fix to deploy to dev."
**Selin Kim:** "It's not just you. It's the sequential test runs. We're running the C++ tests, then Python, then Node in one long line."
**Emeka Stein:** "We can't skip them, but we can parallelize. If we split the runners, we could get this down to 10 mins."
**Lior Moreau:** "Agreed. Kai, prioritize the pipeline optimization this sprint. I'll handle the budget for the additional GitHub Action runners."
**Decision:** Implement parallel test matrices in CI to reduce build time.

### Thread 2: The "Architect Exit" Panic (2024-11-15)
**Lior Moreau:** "Just got off the phone with HR. Our lead architect is leaving in 3 months. This is a huge risk for the microservices transition."
**Selin Kim:** "We're not ready to lead the transition without that expertise. Who's going to oversee the data sharding strategy?"
**Emeka Stein:** "We need more hands. Not just an architect, but maybe another senior backend."
**Lior Moreau:** "I'm escalating this to the steering committee today. I'll request a special budget tranche to bring in a contractor or a new full-time hire immediately. Stand by."
**Decision:** Escalate to steering committee for emergency funding/headcount.

### Thread 3: Rule Builder Blocker (2024-12-01)
**Kai Santos:** "Still no word from the turbine manufacturer on the Brake Solenoid API. I can't finish the rule builder logic without knowing if the command is a boolean or a float."
**Selin Kim:** "We can't let this block the whole feature. Let's just assume it's a boolean `true/false` for now."
**Emeka Stein:** "I can write the QA tests against a mock API that returns a boolean. If they change it to a float later, we only change the mock and the adapter."
**Lior Moreau:** "Do it. Don't wait for the manufacturer. Build the 'Trellis Mock' and move forward."
**Decision:** Use mock API for Rule Builder development to unblock progress.

---

## 11. BUDGET BREAKDOWN

Funding for Project Trellis is released in **milestone-based tranches**. Each tranche is unlocked upon the successful completion and sign-off of the associated milestone.

| Category | Allocated Amount (USD) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $420,000 | Salaries for 4-person team (Lior, Selin, Emeka, Kai). |
| **Infrastructure** | $45,000 | AWS (EC2, RDS, S3), TimescaleDB Cloud. |
| **Tools** | $12,000 | LaunchDarkly (Enterprise), SendGrid, GitHub Actions. |
| **Contingency** | $60,000 | Reserved for R-01 (Emergency hiring/contractors). |
| **Total Projected** | **$537,000** | *Subject to change based on steering committee approval.* |

---

## 12. APPENDICES

### Appendix A: Penetration Testing Schedule
Since Trellis does not follow a specific compliance framework (like SOC2 or HIPAA), security is maintained through aggressive quarterly penetration testing.
*   **Q4 2024:** Focus on API Gateway and Rate Limiter bypasses.
*   **Q1 2025:** Focus on MQTT broker vulnerabilities and "Man-in-the-Middle" attack vectors between sensors and the gateway.
*   **Q2 2025:** Focus on the Rule Builder (checking for "Remote Code Execution" via logic injection).
*   **Q3 2025:** Full system audit and external red-team simulation.

### Appendix B: Localization Key Map (Example)
To ensure consistency across the 12 languages, the following naming convention is enforced for the `i18n` JSON files:

`[Page] . [Component] . [Element] . [State]`

**Examples:**
*   `dashboard.sidebar.nav_home.active` $\rightarrow$ "Home" / "Inicio" / "Accueil"
*   `settings.profile.email_label.default` $\rightarrow$ "Email Address" / "Dirección de correo" / "Adresse e-mail"
*   `rules.builder.error.invalid_operator` $\rightarrow$ "Invalid Operator Selected" / "Operador no válido" / "Opérateur invalide"

This structured approach allows the translation team to update strings without needing access to the source code.