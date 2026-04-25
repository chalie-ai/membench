Due to the extreme length requirements (6,000–8,000 words), this document is presented as a comprehensive, professional technical specification. To maintain the highest level of detail, it is structured as a Master Project Specification (MPS) designed for daily developer reference.

***

# PROJECT SPECIFICATION: MERIDIAN
**Project Code:** IBT-MER-2025  
**Company:** Iron Bay Technologies  
**Industry:** Aerospace Supply Chain Management  
**Version:** 1.0.4 (Baseline)  
**Date:** October 26, 2023  
**Document Status:** Active/Controlled  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision and Business Justification
Project Meridian is a high-stakes "moonshot" Research and Development initiative commissioned by Iron Bay Technologies (IBT). The aerospace industry currently suffers from fragmented supply chain visibility, relying on legacy ERP systems that cannot handle the velocity and complexity of modern aerospace components—specifically those involving rare earth minerals and high-precision alloys. Meridian is designed to replace these legacy silos with a unified, highly scalable supply chain management system.

The business justification for Meridian lies in the strategic necessity of "Digital Thread" integration. By creating a single source of truth for parts provenance, supplier compliance, and logistics, IBT aims to reduce the lead time for aircraft assembly by 20%. While the project is classified as an R&D venture with an uncertain immediate ROI—due to the experimental nature of the mixed-stack integration and the aggressive performance targets—it carries strong executive sponsorship from the Board of Directors. The strategic goal is to transition IBT from a component manufacturer to a platform provider for the broader aerospace ecosystem.

### 1.2 ROI Projection and Financial Model
The ROI for Meridian is projected over a five-year horizon. While the initial investment is high, the projected cost reduction per transaction is 35% compared to the legacy "AeroLink" system. 

**Projected Financial Impacts:**
*   **Operational Efficiency:** Estimated savings of $4.2M annually through the reduction of manual data entry and reconciliation errors.
*   **Risk Mitigation:** Potential avoidance of $1.5M in regulatory fines per annum by automating HIPAA-compliant data handling for personnel-linked logistics.
*   **Market Expansion:** The ability to onboard external paying customers (Milestone 3) is projected to generate an ARR (Annual Recurring Revenue) of $2.5M by Year 2.

### 1.3 Project Scope
Meridian will provide a modular platform for managing vendors, tracking shipments, automating procurement, and analyzing supply chain bottlenecks. The system must handle a 10x increase in capacity over current systems without additional infrastructure spend, necessitating extreme algorithmic efficiency and optimized data structures.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Meridian is currently a "Mixed-Stack Modular Monolith." Due to the inheritance of three different legacy stacks (Java/Spring, Python/Django, and Node.js/Express), the system is designed as a series of interoperable modules that communicate via a shared event bus and a centralized API Gateway. The long-term roadmap dictates an incremental transition to a full microservices architecture as specific modules reach scale thresholds.

### 2.2 The Triple-Stack Integration (The "Inherited Mess")
The system must bridge the following:
1.  **Core Ledger (Java/Spring):** Handles financial transactions and compliance.
2.  **Logistics Engine (Python/Django):** Manages route optimization and vendor tracking.
3.  **User Interface & Real-time Notification (Node.js/Express):** Handles the frontend and WebSocket connections.

### 2.3 Architecture Diagram (ASCII Representation)
```text
[ USER BROWSER / CLIENT ] 
          |
          v
[ API GATEWAY (Kong/Nginx) ] <--- Auth/Rate Limiting (HIPAA Compliant)
          |
          +-----------------------+-----------------------+
          |                       |                       |
[ MODULE A: Core Ledger ]  [ MODULE B: Logistics ]  [ MODULE C: UI/UX ]
(Java Spring Boot)        (Python Django)          (Node.js Express)
          |                       |                       |
          +-----------+-----------+-----------+-----------+
                      |                       |
              [ SHARED EVENT BUS ] <--- (RabbitMQ/Kafka)
                      |
          +-----------+-----------+-----------+-----------+
          |                       |                       |
[ PostgreSQL DB ]         [ Redis Cache ]         [ S3 Object Store ]
(Encrypted at Rest)       (Session/State)         (Docs/Certificates)
```

### 2.4 Security and Compliance
Because the system handles sensitive aerospace personnel data and contractor health certifications, **HIPAA compliance** is mandatory. 
*   **Encryption in Transit:** TLS 1.3 for all movements.
*   **Encryption at Rest:** AES-256 encryption for all database volumes and S3 buckets.
*   **Audit Logging:** Every write operation must be logged with a timestamp, user ID, and a cryptographic hash of the previous state to prevent tampering.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Priority: Critical | Status: Complete)
**Description:**
The A/B testing framework is not a standalone tool but is baked directly into the feature flag system. This allows the team to toggle features for specific user segments (e.g., 5% of users in the "North America" region) and measure the impact on KPIs.

**Technical Implementation:**
The framework uses a "Bucket-Based" allocation system. When a user requests a feature, the system calculates a hash of the `UserID + FeatureID`. If the hash modulo 100 is less than the assigned percentage for the "Treatment" group, the user sees the new feature.

**Requirements:**
*   **Stateless Evaluation:** The A/B check must happen in $<10ms$ to avoid UI lag.
*   **Consistency:** A user must see the same variant across all devices (Session Stickiness).
*   **Metric Tracking:** Integration with the analytics engine to track "Conversion" or "Completion" events per variant.

**Developer Note:** This is a launch blocker. Any feature being deployed to production must be wrapped in a feature flag and assigned to an A/B test group unless it is a critical hotfix.

### 3.2 Data Import/Export with Auto-Detection (Priority: High | Status: Complete)
**Description:**
Aerospace vendors provide data in a chaotic variety of formats (.csv, .xlsx, .json, .xml, and legacy .txt fixed-width files). Meridian provides a universal ingestion engine that detects the format and maps it to the internal schema.

**Technical Implementation:**
The system utilizes a "Heuristic Probe" layer. Upon file upload, the system reads the first 1KB of the file to identify magic bytes and structural patterns. 
*   **CSV/XLSX:** Parsed via a streaming library to handle files up to 2GB without crashing the Node.js heap.
*   **JSON/XML:** Validated against a set of pre-defined XSD or JSON schemas.
*   **Mapping Layer:** A user-configurable mapping interface allows users to drag-and-drop source columns to target fields.

**Requirements:**
*   **Validation:** All imports must pass a "dry run" phase where errors are flagged before any data is committed to the database.
*   **Asynchronous Processing:** Large files are processed via a background worker (Celery/RabbitMQ) to prevent API timeouts.

### 3.3 Localization and Internationalization (L10n/I18n) (Priority: Medium | Status: Not Started)
**Description:**
To support global aerospace operations, the system must support 12 languages (English, Mandarin, French, German, Japanese, Spanish, Korean, Russian, Portuguese, Italian, Arabic, and Hindi).

**Technical Implementation:**
The system will implement a `i18next` based architecture. All hard-coded strings will be replaced by keys (e.g., `dashboard.welcome_message`). Translation files will be stored as JSON objects in a centralized Localization Repository.

**Requirements:**
*   **Dynamic Loading:** The UI must load the required language pack based on the `Accept-Language` header or user profile setting.
*   **RTL Support:** The CSS framework must support Right-to-Left (RTL) layouts for Arabic.
*   **Date/Currency Normalization:** Use the `Intl` JavaScript API to format dates and currencies based on locale. (Note: This must resolve the current technical debt regarding the three different date formats).

### 3.4 Webhook Integration Framework (Priority: Low | Status: In Design)
**Description:**
A framework allowing third-party tools (e.g., SAP, Oracle, Slack) to receive real-time updates from Meridian. 

**Technical Implementation:**
The framework will follow a "Publish-Subscribe" pattern. Users can define a "Webhook Subscription" by providing a target URL and selecting events (e.g., `shipment.delayed`, `inventory.low`). 

**Requirements:**
*   **Retry Logic:** If a third-party endpoint returns a 5xx error, the system will implement exponential backoff (retry at 1m, 5m, 15m, 1h).
*   **Security:** Every webhook payload must be signed with an `X-Meridian-Signature` HMAC header using a shared secret.
*   **Payload Versioning:** Webhooks must include a version header to ensure backward compatibility when the schema evolves.

### 3.5 Customizable Dashboard with Drag-and-Drop Widgets (Priority: Low | Status: Complete)
**Description:**
A user-centric cockpit where aerospace managers can arrange KPIs (e.g., "Active Shipments," "Risk Alerts," "Vendor Performance") using a grid system.

**Technical Implementation:**
Built using `react-grid-layout`. The position and size of each widget are stored as a JSON blob in the `UserPreferences` table. 

**Requirements:**
*   **Persistence:** Layouts must be saved automatically on "drop" via a debounced API call.
*   **Widget Library:** A set of standard widgets (Line Chart, Heatmap, Data Table) that can be configured with different data sources.
*   **Responsiveness:** The grid must collapse gracefully from a 12-column desktop view to a 1-column mobile view.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include a Bearer Token in the Authorization header.

### 4.1 `GET /shipments`
*   **Description:** Retrieve a list of all active shipments with filtering.
*   **Request Params:** `status` (string), `origin` (string), `limit` (int).
*   **Success Response (200 OK):**
    ```json
    {
      "data": [
        { "id": "SHIP-102", "status": "in-transit", "eta": "2025-05-12T14:00:00Z" }
      ],
      "pagination": { "total": 150, "next": "/api/v1/shipments?offset=20" }
    }
    ```

### 4.2 `POST /shipments`
*   **Description:** Create a new shipment record.
*   **Request Body:** `{ "vendor_id": "V-99", "parts": [{ "sku": "BOLT-1", "qty": 500 }], "destination": "HOUSTON-HUB" }`
*   **Success Response (201 Created):**
    ```json
    { "id": "SHIP-103", "status": "pending", "created_at": "2025-01-10T09:00:00Z" }
    ```

### 4.3 `PATCH /shipments/{id}/status`
*   **Description:** Update the status of a specific shipment.
*   **Request Body:** `{ "status": "delivered", "timestamp": "2025-01-15T10:00:00Z" }`
*   **Success Response (200 OK):**
    ```json
    { "id": "SHIP-103", "updated_status": "delivered" }
    ```

### 4.4 `GET /inventory/{sku}`
*   **Description:** Check stock levels for a specific aerospace part.
*   **Success Response (200 OK):**
    ```json
    { "sku": "WING-S4", "quantity": 42, "warehouse": "SEA-01", "reserved": 10 }
    ```

### 4.5 `POST /import/data`
*   **Description:** Upload a file for auto-detection and ingestion.
*   **Request Body:** `multipart/form-data` (File upload).
*   **Success Response (202 Accepted):**
    ```json
    { "job_id": "JOB-9921", "status": "processing", "estimated_time": "45s" }
    ```

### 4.6 `GET /analytics/performance`
*   **Description:** Fetch cost-per-transaction metrics for ROI tracking.
*   **Success Response (200 OK):**
    ```json
    { "current_cost": 1.42, "legacy_cost": 2.18, "reduction_percentage": 35.3 }
    ```

### 4.7 `POST /flags/evaluate`
*   **Description:** Evaluate which A/B variant a user should see.
*   **Request Body:** `{ "user_id": "U-123", "feature_key": "new_checkout_flow" }`
*   **Success Response (200 OK):**
    ```json
    { "variant": "treatment_b", "enabled": true }
    ```

### 4.8 `PUT /user/preferences/layout`
*   **Description:** Save the drag-and-drop dashboard configuration.
*   **Request Body:** `{ "layout": [{ "i": "widget1", "x": 0, "y": 0, "w": 6, "h": 2 }] }`
*   **Success Response (200 OK):**
    ```json
    { "status": "saved" }
    ```

---

## 5. DATABASE SCHEMA

The system uses a PostgreSQL 15 database. All tables use UUIDs for primary keys to ensure consistency across the modular monoliths.

### 5.1 Schema Definition

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | None | `email`, `role_id`, `locale` | User accounts and auth |
| `Roles` | `role_id` | None | `role_name`, `permissions` | RBAC permission sets |
| `Vendors` | `vendor_id` | None | `company_name`, `compliance_score` | Aerospace supplier data |
| `Parts` | `part_id` | `vendor_id` | `sku`, `material_grade`, `unit_cost` | Component catalog |
| `Shipments` | `shipment_id` | `vendor_id`, `user_id` | `tracking_number`, `status`, `eta` | Logistics tracking |
| `Shipment_Items`| `item_id` | `shipment_id`, `part_id` | `quantity`, `weight` | Join table for parts in shipment |
| `Audit_Logs` | `log_id` | `user_id` | `action`, `timestamp`, `prev_hash` | HIPAA compliance log |
| `Feature_Flags` | `flag_id` | None | `flag_key`, `is_enabled`, `variant_dist` | A/B test configurations |
| `User_Prefs` | `pref_id` | `user_id` | `dashboard_json`, `theme` | UI customization |
| `Webhooks` | `webhook_id` | `user_id` | `target_url`, `event_type`, `secret` | Third-party integrations |

### 5.2 Relationships
*   **Users $\to$ User_Prefs:** 1:1 relationship.
*   **Vendors $\to$ Parts:** 1:N (One vendor provides many parts).
*   **Shipments $\to$ Shipment_Items:** 1:N (One shipment contains many items).
*   **Parts $\to$ Shipment_Items:** 1:N (One part type can appear in many shipments).
*   **Users $\to$ Audit_Logs:** 1:N (One user generates many audit entries).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Strategy
Meridian employs a **Continuous Deployment (CD)** pipeline. Every Pull Request (PR) merged into the `main` branch is automatically deployed to production. This requires a robust suite of automated tests to prevent regressions.

### 6.2 Environment Descriptions

#### 6.2.1 Development (DEV)
*   **Purpose:** Feature development and unit testing.
*   **Configuration:** Shared PostgreSQL instance with mocked external aerospace APIs.
*   **Deployment:** Triggered on push to `feature/*` branches.
*   **Budget:** Minimal; uses burstable t3.medium instances.

#### 6.2.2 Staging (STAGE)
*   **Purpose:** Integration testing and UAT (User Acceptance Testing).
*   **Configuration:** Mirror of Production. Uses anonymized production data.
*   **Deployment:** Triggered on merge to `develop` branch.
*   **Note:** This is where the A/B testing framework is validated before the final push to production.

#### 6.2.3 Production (PROD)
*   **Purpose:** Live aerospace supply chain operations.
*   **Configuration:** Multi-AZ (Availability Zone) deployment for high availability.
*   **Deployment:** Automatic upon merge to `main`.
*   **Security:** Strict HIPAA-compliant VPC with no public ingress except via the API Gateway.

### 6.3 Current Infrastructure Blockers
**Critical Issue:** Provisioning of the high-performance compute clusters is currently delayed by the cloud provider. This has created a bottleneck for the 10x performance testing phase. Until resolved, the team is using a scaled-down simulation environment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions and components.
*   **Target:** 80% code coverage.
*   **Tools:** JUnit (Java), PyTest (Python), Jest (Node.js).
*   **Requirement:** No PR can be merged unless all unit tests pass in the CI pipeline.

### 7.2 Integration Testing
*   **Focus:** Inter-module communication.
*   **Scenario:** Ensuring the Node.js frontend correctly triggers a shipment update in the Java Core Ledger.
*   **Approach:** Contract Testing (using Pact) to ensure that API changes in one stack do not break the others.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** User journeys from login to shipment delivery.
*   **Tools:** Playwright/Cypress.
*   **Requirement:** Critical paths (e.g., "Import Data $\to$ Assign to Shipment $\to$ Trigger Webhook") must be automated.

### 7.4 Performance Testing
*   **Goal:** Verify the system can handle 10x the current capacity.
*   **Metric:** Response time for `GET /shipments` must remain under 200ms under a load of 5,000 concurrent requests per second.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect leaving company in 3 months | High | High | Accept risk; monitor weekly. Ensure all architectural decisions are documented in this MPS. |
| **R-02** | 10x Performance Req vs Zero Budget | Medium | High | De-scope non-essential features (e.g., complex dashboard widgets) if bottlenecks remain. |
| **R-03** | Data Inconsistency (3 Date Formats) | High | Medium | Implement a `DateNormalizationLayer` as a shared library across all 3 stacks. |
| **R-04** | HIPAA Compliance Failure | Low | Critical | Weekly third-party security audits and automated encryption checks. |
| **R-05** | Cloud Provisioning Delay | High | Medium | Use temporary local clusters for simulation; escalate to cloud provider account manager. |

**Probability/Impact Matrix:**
*   *High/High* $\to$ Immediate Action Required.
*   *Low/Critical* $\to$ Rigorous Monitoring.
*   *Medium/High* $\to$ Contingency Planning.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Overview
The project is divided into three primary phases leading to the first paying customer.

**Phase 1: Foundation & Architecture (Current $\to$ April 2025)**
*   Establish interoperability between the 3 stacks.
*   Finalize HIPAA encryption layers.
*   **Milestone 1: Architecture Review Complete (Target: 2025-04-15)**

**Phase 2: Feature Hardening & Scale (April 2025 $\to$ June 2025)**
*   Implement Localization (L10n).
*   Stress test the 10x performance requirement.
*   Resolve the "Date Format" technical debt.
*   **Milestone 2: Production Launch (Target: 2025-06-15)**

**Phase 3: Monetization & Onboarding (June 2025 $\to$ August 2025)**
*   Stabilize A/B testing for customer conversion.
*   Onboard first external partner.
*   **Milestone 3: First Paying Customer Onboarded (Target: 2025-08-15)**

### 9.2 Gantt-Style Dependency Map
`Arch Review` $\to$ `L10n Implementation` $\to$ `Performance Testing` $\to$ `Prod Launch` $\to$ `Customer Onboarding`

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-12  
**Attendees:** Anders Oduya, Greta Jensen, Sergei Moreau, Felix Santos  
**Discussion:** 
The team discussed the friction caused by the three different stacks. Felix Santos pointed out that the Java ledger is slowing down the Node.js frontend due to synchronous API calls.  
**Decisions:** 
1. Transition to an asynchronous event-driven model using RabbitMQ.
2. Move all auth to the API Gateway level to avoid redundant checks in each stack.  
**Action Items:** 
*   Greta Jensen: Setup RabbitMQ cluster in DEV. (Due: 2023-11-20)
*   Felix Santos: Refactor `/shipments` endpoint to be async. (Due: 2023-11-25)

### Meeting 2: Performance Crisis & Budget
**Date:** 2023-12-05  
**Attendees:** Anders Oduya, Greta Jensen, Sergei Moreau  
**Discussion:** 
Anders confirmed there is no additional budget for infrastructure. However, the system is failing at 3x capacity, let alone 10x. Sergei argued that the drag-and-drop dashboard is consuming too many resources.  
**Decisions:** 
1. The dashboard is "Low Priority." If performance doesn't improve, we will disable the "Real-time Refresh" on widgets.
2. Implement Redis caching for all `GET` requests on the inventory engine.  
**Action Items:** 
*   Greta Jensen: Implement Redis caching layer. (Due: 2023-12-15)
*   Sergei Moreau: Simplify dashboard widget queries. (Due: 2023-12-18)

### Meeting 3: The "Date Format" Debt
**Date:** 2024-01-10  
**Attendees:** Anders Oduya, Felix Santos, Greta Jensen  
**Discussion:** 
Felix reported a major bug where shipments are arriving "before they were sent" because the Python stack uses UTC, the Java stack uses EST, and the Node.js stack uses ISO-8601.  
**Decisions:** 
1. Mandate ISO-8601 UTC for all database entries.
2. Create a shared middleware library `MeridianDateLib` to normalize dates at the API gateway.  
**Action Items:** 
*   Felix Santos: Write the `MeridianDateLib` for Node and Python. (Due: 2024-01-20)
*   Greta Jensen: Run a migration script to normalize existing DB dates. (Due: 2024-01-25)

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on the achievement of milestones.

### 11.1 Personnel Costs (Annualized)
| Role | Type | Rate/Year | Allocation | Total |
| :--- | :--- | :--- | :--- | :--- |
| Project Lead (Anders) | Executive | $220,000 | 50% | $110,000 |
| DevOps (Greta) | Full-Time | $160,000 | 100% | $160,000 |
| Designer (Sergei) | Full-Time | $130,000 | 100% | $130,000 |
| Contractor (Felix) | Hourly | $120/hr | 40hrs/wk | $249,600 |
| QA Specialist | Full-Time | $110,000 | 100% | $110,000 |
| **Total Personnel** | | | | **$759,600** |

### 11.2 Infrastructure & Tools (Annual)
| Category | Tool/Service | Estimated Cost | Note |
| :--- | :--- | :--- | :--- |
| Cloud Compute | AWS/Azure | $85,000 | Fixed budget; no overages allowed |
| Security Audit | Third Party | $25,000 | HIPAA certification |
| Licenses | JIRA/Confluence | $12,000 | Team of 6 |
| Monitoring | Datadog/NewRelic | $18,000 | Required for 10x perf tracking |
| **Total Tools** | | **$140,000** | |

### 11.3 Contingency Fund
*   **Amount:** $100,000 (Allocated for emergency contractor scaling or critical hardware needs).
*   **Release Condition:** Requires approval from Anders Oduya and the CFO.

---

## 12. APPENDICES

### Appendix A: Date Format Normalization Logic
To resolve the technical debt, the following logic must be applied in the `MeridianDateLib`:
1.  **Input:** Any date string.
2.  **Detection:** Regex check for `YYYY-MM-DD`, `MM/DD/YYYY`, and `ISO-8601`.
3.  **Conversion:** 
    *   If `MM/DD/YYYY` $\to$ Assume EST $\to$ Convert to UTC $\to$ Store as `YYYY-MM-DDTHH:mm:ssZ`.
    *   If `YYYY-MM-DD` $\to$ Assume UTC Midnight $\to$ Store as `YYYY-MM-DDT00:00:00Z`.
4.  **Output:** Standardized ISO-8601 string.

### Appendix B: HIPAA Encryption Specification
All data in the `Users` and `Audit_Logs` tables must be encrypted using the following standard:
*   **Algorithm:** AES-256-GCM.
*   **Key Management:** Keys are stored in AWS KMS (Key Management Service) and rotated every 90 days.
*   **Access Control:** Access to the decryption key is limited to the `Core Ledger` service identity; no individual developer has access to the production master key.
*   **Transmission:** All API responses containing PII (Personally Identifiable Information) must be encrypted with a session-specific public key provided by the client.