Due to the extreme length requirement of 6,000 to 8,000 words, this document is structured as a comprehensive, professional Technical Specification Document (TSD). It expands upon the provided constraints with exhaustive detail, technical depth, and corporate rigor.

***

# PROJECT SPECIFICATION: WAYFINDER
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/Draft  
**Classification:** Confidential – Talus Innovations Internal  
**Project Lead:** Eben Oduya (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project **Wayfinder** is the flagship supply chain management initiative for Talus Innovations, designed specifically for the education sector. The education supply chain is uniquely fragmented, characterized by cyclical purchasing patterns, rigid institutional budget cycles, and complex logistics involving thousands of disparate campus locations. Currently, Talus Innovations relies on manual data entry and legacy silos, resulting in a 15% waste rate in inventory and significant delays in educational material delivery.

Wayfinder is not merely a tool but a strategic partnership integration. The core business objective is to synchronize Talus Innovations’ internal inventory and procurement workflows with a critical external partner’s API. This integration will enable real-time visibility into the partner's logistics pipeline, allowing Talus to shift from a reactive "order-and-wait" model to a proactive "just-in-time" (JIT) delivery model. By automating the data flow between the external vendor and internal stakeholders, Wayfinder will eliminate manual reconciliation errors and reduce procurement lead times by an estimated 40%.

### 1.2 ROI Projection
With a total budget allocation exceeding $5M, the board expects a high-impact return on investment. The ROI is projected across three primary pillars:

1.  **Operational Cost Reduction:** By automating data import/export and integrating the partner API, the company expects to reduce administrative overhead by 2,500 man-hours per year, saving approximately $350,000 in labor costs.
2.  **Inventory Optimization:** Through faceted search and advanced reporting, Wayfinder will identify stagnant stock. Reducing over-ordering by 10% is projected to save $1.2M in annual warehouse and spoilage costs.
3.  **Revenue Growth via Pilot Success:** Successful deployment to the 10 pilot users in October 2025 is expected to validate the model for a wider rollout. A successful beta is projected to increase institutional contract win rates by 20% due to superior delivery reliability.

**Projected 3-Year Net Present Value (NPV):** $8.4M  
**Estimated Break-even Point:** Month 18 post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Wayfinder utilizes a **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies. This is critical given the project's reliance on an external API that may change or be replaced (especially considering the current risk of vendor EOL).

-   **The Core (Domain):** Contains the business entities (e.g., `Shipment`, `Order`, `InventoryItem`) and use cases. It has no knowledge of the database or the API.
-   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `IShipmentRepository`, `INotificationService`).
-   **Adapters:** Concrete implementations of the ports.
    -   *Persistence Adapter:* PostgreSQL implementation of the repository.
    -   *External API Adapter:* The logic that translates Talus’s internal requests into the external partner’s specific API format.
    -   *Infrastructure Adapter:* AWS ECS/S3 integration for file storage.

### 2.2 ASCII Architecture Diagram
```text
[ External Partner API ] <---> [ API Adapter ] <---+
                                                   |
[ Web/Mobile UI ] <---> [ REST Controllers ] <---+ [ CORE DOMAIN ]
                                                   | (Business Logic)
[ Redis Cache ] <---> [ Cache Adapter ] <---------+
                                                   |
[ PostgreSQL DB ] <---> [ Repository Adapter ] <---+
                                                   |
[ AWS S3 / SES ] <---> [ Infrastructure Adapter ] <+
```

### 2.3 Technology Stack
-   **Backend:** Python 3.11 / Django 4.2 (Chosen for rapid development and robust ORM).
-   **Database:** PostgreSQL 15 (Primary relational store).
-   **Caching/Queue:** Redis 7.0 (Used for session management, feature flag caching, and Celery task brokerage).
-   **Deployment:** AWS ECS (Elastic Container Service) utilizing Fargate for serverless container execution.
-   **Orchestration:** Kubernetes (EKS) for rolling deployments.
-   **CI/CD:** GitLab CI/CD with automated pipelines for linting, testing, and deployment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing & Feature Flag Framework
**Priority:** Medium | **Status:** Complete
**Description:** 
A robust system to toggle features on/off for specific user segments without requiring a code deployment. This is integrated directly into the feature flagging system to allow for "Canary" releases and A/B testing of new supply chain workflows.

**Technical Details:**
The system utilizes a Redis-backed flag store. Each user is assigned a unique `segment_id` based on their institutional role or region. The `FeatureFlagService` checks the flag status and the user's segment before returning a boolean.
-   **A/B Logic:** When a feature is marked as "A/B Test," the system uses a deterministic hash of the `user_id` to assign the user to either Group A (Control) or Group B (Experimental).
-   **Tracking:** Every action taken by a user under an A/B flag is logged to the `experiment_logs` table to allow for later conversion analysis.

**User Flow:**
1.  Product Manager creates a flag `new_inventory_view` in the admin panel.
2.  Sets a 50/50 split for users in the "California Region."
3.  The system serves the new UI to 50% of users and the old UI to the others.
4.  Data is collected on "Time to Complete Order" to determine the winning variant.

### 3.2 PDF/CSV Report Generation & Scheduled Delivery
**Priority:** Medium | **Status:** Blocked (Waiting on Legal/DPA)
**Description:** 
Automated generation of supply chain reports (Inventory Levels, Procurement Velocity, Vendor Performance) available in PDF and CSV formats. These can be triggered on-demand or scheduled for daily/weekly delivery.

**Technical Details:**
-   **Generation:** Python's `ReportLab` for PDFs and `Pandas` for CSVs.
-   **Asynchronous Processing:** Reports are processed via Celery workers to prevent blocking the main request thread.
-   **Scheduling:** `Celery Beat` handles the cron-like scheduling.
-   **Storage:** Generated files are uploaded to an AWS S3 bucket with a Time-To-Live (TTL) of 7 days.
-   **Delivery:** The system integrates with AWS SES (Simple Email Service) to mail the S3 pre-signed URL to the stakeholders.

**Blocker Analysis:** This feature is blocked because reports often contain PII (Personally Identifiable Information) of institutional contacts. The Legal team is currently reviewing the Data Processing Agreement (DPA) to ensure that emailing these reports complies with regional privacy laws.

### 3.3 Advanced Search with Faceted Filtering
**Priority:** Low (Nice to have) | **Status:** In Review
**Description:** 
A high-performance search interface allowing users to find items across the global supply chain using full-text indexing and dynamic facets (filters).

**Technical Details:**
-   **Indexing:** To avoid slamming the PostgreSQL DB with `LIKE %query%` statements, we are implementing PostgreSQL Full-Text Search (FTS) using `tsvector` and `tsquery`.
-   **Faceting:** The system calculates counts for each category (e.g., "Status: Shipped", "Category: Lab Equipment") in a single query using `GROUP BY` and `COUNT` aggregations.
-   **Performance:** Search queries are cached in Redis for 5 minutes to handle repetitive institutional queries.

**User Flow:**
1.  User enters "Centrifuge" in the search bar.
2.  The system returns all matches.
3.  The sidebar populates with facets: "Manufacturer" (ThermoFisher, Eppendorf), "Price Range" ($500-$2000), and "Availability" (In Stock, Backordered).
4.  User selects "In Stock," and the results refine instantly.

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** Not Started
**Description:** 
A tool to allow institutional partners to upload their current inventory lists or order history. The system must automatically detect if the file is CSV, JSON, or XML and map the columns to the Wayfinder schema.

**Technical Details:**
-   **Auto-Detection:** The system reads the first 1KB of the file to detect the magic bytes and structure.
-   **Schema Mapping:** A "Mapping Engine" will use fuzzy string matching (via `Levenshtein distance`) to suggest column maps (e.g., "Item_Num" $\rightarrow$ `sku`).
-   **Validation:** A two-step validation process:
    1.  *Structural Validation:* Does the file follow the detected format?
    2.  *Data Validation:* Are the values in the correct format (e.g., dates in ISO-8601)?
-   **Bulk Processing:** For files over 10,000 rows, the system will use `django-import-export` with background processing and a progress bar in the UI.

### 3.5 Multi-Channel Notification System
**Priority:** High | **Status:** Blocked
**Description:** 
A comprehensive alert system to notify users of critical supply chain events (e.g., "Shipment Delayed," "Low Stock Warning"). Notifications must be delivered via Email, SMS, In-App alerts, and Push notifications.

**Technical Details:**
-   **Dispatcher:** A central `NotificationDispatcher` that evaluates user preferences stored in the `user_notification_settings` table.
-   **Integrations:**
    -   *Email:* AWS SES.
    -   *SMS:* Twilio API.
    -   *Push:* Firebase Cloud Messaging (FCM).
    -   *In-App:* WebSocket connection via Django Channels.
-   **Priority Levels:** 
    -   *Critical:* All channels.
    -   *Warning:* Email and In-App.
    -   *Info:* In-App only.

**Blocker Analysis:** Blocked due to the same Legal/DPA review affecting the Reporting feature. The use of SMS (Twilio) requires specific consent frameworks under GDPR/CCPA which have not yet been approved by the legal team.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a Bearer Token in the Authorization header. Base URL: `https://api.wayfinder.talus.io/v1/`

### 4.1 Get Inventory Item
-   **Endpoint:** `GET /inventory/items/{item_id}/`
-   **Description:** Retrieves detailed information about a specific SKU.
-   **Request Example:** `GET /inventory/items/SKU-99281/`
-   **Response Example (200 OK):**
    ```json
    {
      "sku": "SKU-99281",
      "name": "Digital Microscope X1",
      "quantity": 45,
      "location": "Warehouse-East",
      "status": "available",
      "last_updated": "2023-10-20T14:00:00Z"
    }
    ```

### 4.2 Update Stock Levels
-   **Endpoint:** `PATCH /inventory/items/{item_id}/stock/`
-   **Description:** Updates the stock count for an item.
-   **Request Example:**
    ```json
    { "adjustment": -5, "reason": "Damage" }
    ```
-   **Response Example (200 OK):**
    ```json
    { "sku": "SKU-99281", "new_quantity": 40 }
    ```

### 4.3 Create Shipment
-   **Endpoint:** `POST /shipments/`
-   **Description:** Initiates a new shipment request.
-   **Request Example:**
    ```json
    {
      "order_id": "ORD-554",
      "destination_id": "CAMPUS-01",
      "priority": "high"
    }
    ```
-   **Response Example (201 Created):**
    ```json
    { "shipment_id": "SHIP-1002", "status": "pending", "eta": "2023-11-01" }
    ```

### 4.4 Get Shipment Tracking
-   **Endpoint:** `GET /shipments/{shipment_id}/track/`
-   **Description:** Fetches real-time tracking data from the external partner API.
-   **Response Example (200 OK):**
    ```json
    {
      "current_location": "Sorting Center - Memphis",
      "status": "in_transit",
      "estimated_delivery": "2023-10-30"
    }
    ```

### 4.5 Bulk Import Data
-   **Endpoint:** `POST /imports/upload/`
-   **Description:** Uploads a file for processing.
-   **Request:** Multipart form-data (File upload).
-   **Response Example (202 Accepted):**
    ```json
    { "job_id": "JOB-8821", "status": "processing", "estimated_time": "120s" }
    ```

### 4.6 Get Import Job Status
-   **Endpoint:** `GET /imports/jobs/{job_id}/`
-   **Description:** Checks the progress of a bulk import.
-   **Response Example (200 OK):**
    ```json
    { "job_id": "JOB-8821", "progress": "65%", "errors": 2 }
    ```

### 4.7 Trigger Report Generation
-   **Endpoint:** `POST /reports/generate/`
-   **Description:** Triggers a scheduled or on-demand report.
-   **Request Example:**
    ```json
    { "report_type": "inventory_velocity", "format": "pdf", "range": "last_30_days" }
    ```
-   **Response Example (202 Accepted):**
    ```json
    { "report_id": "REP-441", "status": "queued" }
    ```

### 4.8 Manage Feature Flags (Admin Only)
-   **Endpoint:** `POST /admin/flags/{flag_name}/`
-   **Description:** Toggles a feature flag for a specific segment.
-   **Request Example:**
    ```json
    { "enabled": true, "segment": "beta_users", "percentage": 20 }
    ```
-   **Response Example (200 OK):**
    ```json
    { "flag": "new_dashboard", "status": "active", "target": "beta_users" }
    ```

---

## 5. DATABASE SCHEMA

The system uses a relational PostgreSQL schema. Due to performance requirements, 30% of queries (specifically those involving the `ledger_entries` and `tracking_events` tables) bypass the Django ORM and use raw SQL.

### 5.1 Table Definitions

1.  **`users`**
    -   `id` (UUID, PK)
    -   `email` (String, Unique)
    -   `role` (Enum: ADMIN, MANAGER, VIEWER)
    -   `timezone` (String)
    -   `created_at` (Timestamp)

2.  **`institutions`**
    -   `id` (UUID, PK)
    -   `name` (String)
    -   `address` (Text)
    -   `billing_contact` (String)
    -   `contract_expiry` (Date)

3.  **`inventory_items`**
    -   `sku` (String, PK)
    -   `name` (String)
    -   `description` (Text)
    -   `category_id` (FK $\rightarrow$ `categories.id`)
    -   `unit_price` (Decimal)
    -   `weight` (Float)

4.  **`stock_levels`**
    -   `id` (UUID, PK)
    -   `sku` (FK $\rightarrow$ `inventory_items.sku`)
    -   `warehouse_id` (FK $\rightarrow$ `warehouses.id`)
    -   `quantity` (Integer)
    -   `reserved_quantity` (Integer)
    -   `last_counted` (Timestamp)

5.  **`warehouses`**
    -   `id` (UUID, PK)
    -   `location_code` (String, Unique)
    -   `capacity` (Integer)
    -   `manager_id` (FK $\rightarrow$ `users.id`)

6.  **`orders`**
    -   `id` (UUID, PK)
    -   `institution_id` (FK $\rightarrow$ `institutions.id`)
    -   `status` (Enum: PENDING, APPROVED, SHIPPED, DELIVERED)
    -   `total_amount` (Decimal)
    -   `created_at` (Timestamp)

7.  **`order_items`**
    -   `id` (UUID, PK)
    -   `order_id` (FK $\rightarrow$ `orders.id`)
    -   `sku` (FK $\rightarrow$ `inventory_items.sku`)
    -   `quantity` (Integer)
    -   `price_at_time_of_order` (Decimal)

8.  **`shipments`**
    -   `id` (UUID, PK)
    -   `order_id` (FK $\rightarrow$ `orders.id`)
    -   `external_tracking_id` (String, Index)
    -   `carrier` (String)
    -   `estimated_delivery` (Date)

9.  **`tracking_events`** (Raw SQL Optimized)
    -   `id` (BigInt, PK)
    -   `shipment_id` (FK $\rightarrow$ `shipments.id`)
    -   `event_timestamp` (Timestamp)
    -   `location` (String)
    -   `status_update` (String)

10. **`ledger_entries`** (Raw SQL Optimized)
    -   `id` (BigInt, PK)
    -   `sku` (FK $\rightarrow$ `inventory_items.sku`)
    -   `change_amount` (Integer)
    -   `transaction_type` (Enum: SALE, RETURN, ADJUSTMENT)
    -   `created_at` (Timestamp)

### 5.2 Relationships
-   **One-to-Many:** `institutions` $\rightarrow$ `orders`
-   **One-to-Many:** `orders` $\rightarrow$ `order_items`
-   **Many-to-One:** `inventory_items` $\rightarrow$ `categories`
-   **One-to-Many:** `shipments` $\rightarrow$ `tracking_events`
-   **One-to-Many:** `inventory_items` $\rightarrow$ `ledger_entries`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Wayfinder employs a three-tier environment strategy to ensure stability.

#### 6.1.1 Development (`dev`)
-   **Purpose:** Sandbox for engineers to iterate on features.
-   **Configuration:** Single-node ECS instance.
-   **Database:** Shared PostgreSQL instance with separate schemas per developer.
-   **Deployment:** Triggered on every push to `develop` branch.

#### 6.1.2 Staging (`staging`)
-   **Purpose:** Mirror of production for QA and stakeholder UAT (User Acceptance Testing).
-   **Configuration:** Multi-node ECS cluster with a Load Balancer.
-   **Database:** Anonymized production data snapshot.
-   **Deployment:** Triggered on merge to `release` branch.

#### 6.1.3 Production (`prod`)
-   **Purpose:** Live environment serving end-users.
-   **Configuration:** High-availability EKS cluster across three AWS Availability Zones (AZs).
-   **Scaling:** Horizontal Pod Autoscaler (HPA) based on CPU and memory thresholds.
-   **Deployment:** Rolling updates via GitLab CI. New versions are deployed to 25% of nodes first (Canary) before full rollout.

### 6.2 CI/CD Pipeline
1.  **Build Phase:** Docker image creation $\rightarrow$ Scan for vulnerabilities (Trivy) $\rightarrow$ Push to Amazon ECR.
2.  **Test Phase:** Execution of PyTest suite $\rightarrow$ Integration tests in a transient Docker environment.
3.  **Deploy Phase:** Update Kubernetes manifest $\rightarrow$ Rolling restart of pods $\rightarrow$ Health check verification.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
-   **Framework:** `PyTest` and `unittest.mock`.
-   **Coverage Requirement:** 85% minimum coverage for all domain logic.
-   **Focus:** Business rules in the Core Domain. For example, testing that an order cannot be "Shipped" if the `stock_level` for any item is $\le 0$.

### 7.2 Integration Testing
-   **Focus:** Testing the "Adapters."
-   **Approach:** Using `TestContainers` to spin up a real PostgreSQL and Redis instance during the CI process.
-   **API Testing:** Using `Schemathesis` to perform property-based testing against the OpenAPI spec to find edge cases in the REST endpoints.

### 7.3 End-to-End (E2E) Testing
-   **Framework:** `Playwright`.
-   **Critical Paths:** 
    -   User logs in $\rightarrow$ Uploads CSV $\rightarrow$ Verifies inventory update $\rightarrow$ Creates shipment.
    -   Admin toggles feature flag $\rightarrow$ Verifies UI change for specific user segment.
-   **Frequency:** Run daily on the `staging` environment.

### 7.4 Penetration Testing
As there is no specific compliance framework (like HIPAA or SOC2) mandated for Wayfinder, the team will conduct **Quarterly Penetration Tests**. These will focus on:
-   Broken Object Level Authorization (BOLA).
-   SQL Injection (especially in those 30% raw SQL queries).
-   Cross-Site Scripting (XSS) in the report generation views.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Scope creep from stakeholders adding 'small' features | High | Medium | All new requests must be documented and escalated to the Steering Committee for budget/timeline adjustment. |
| **R2** | External vendor EOL (End-of-Life) for API product | Medium | Critical | Engage external consultant for an independent assessment of alternative vendors; implement strict Adapter pattern to minimize rewrite cost. |
| **R3** | Technical debt from Raw SQL queries | High | Medium | Schedule a "Technical Debt Sprint" every 4 weeks to migrate high-risk raw SQL to optimized ORM queries or Views. |
| **R4** | Legal delay in DPA review | High | Medium | Blocked features (Reports/Notifications) are isolated from the core launch. Pivot focus to Data Import/Export. |
| **R5** | Time zone misalignment (8 people, 2 zones) | Medium | Low | Mandatory async standups in Slack; "Core Hours" (10 AM - 1 PM EST) for all sync calls. |

**Probability/Impact Matrix:**
-   **High/Critical:** Immediate attention (R2).
-   **High/Medium:** Managed via process (R1, R3, R4).
-   **Medium/Low:** Monitored (R5).

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Overview
Wayfinder follows a phased approach, moving from architectural validation to production launch and finally to external beta.

| Phase | Description | Duration | Dependency |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Hexagonal architecture setup, DB schema design, basic API | Jan 2025 - Mar 2025 | None |
| **Phase 2: Integration** | Partner API integration, Data Import/Export logic | Apr 2025 - Jun 2025 | Phase 1 |
| **Phase 3: Launch** | Production deployment, internal testing | Jun 2025 | Phase 2 |
| **Phase 4: Optimization** | Architecture review, Performance tuning (Raw SQL fix) | Jul 2025 - Aug 2025 | Phase 3 |
| **Phase 5: External Beta** | Onboarding 10 pilot users, feedback loop | Sep 2025 - Oct 2025 | Phase 4 |

### 9.2 Key Milestone Dates
-   **Milestone 1: Production Launch** $\rightarrow$ **2025-06-15**
    -   *Criteria:* Core API stable, Data Import working, ECS Production environment live.
-   **Milestone 2: Architecture Review Complete** $\rightarrow$ **2025-08-15**
    -   *Criteria:* External audit of the hexagonal implementation and security pen-test completed.
-   **Milestone 3: External Beta (10 Users)** $\rightarrow$ **2025-10-15**
    -   *Criteria:* Pilot users onboarded; NPS survey deployed; 80% feature adoption tracked.

---

## 10. MEETING NOTES (Sourced from Slack Threads)

*Since Talus Innovations does not use formal meeting minutes, the following is a synthesis of key decision threads from the `#wayfinder-dev` Slack channel.*

### Thread 1: "The Raw SQL Dilemma" (Date: 2023-11-12)
-   **Priya G:** "The ORM is killing us on the `ledger_entries` table. A simple join is taking 4 seconds. I'm moving the reporting queries to raw SQL."
-   **Eben O:** "I agree for now, but we need to be careful. Raw SQL means migrations will break if we change the schema. Can we use a Database View instead?"
-   **Priya G:** "View doesn't give me the indexing control I need for the aggregate. I'll use raw SQL but I'll document the exact columns used in a `sql_dependencies.md` file."
-   **Decision:** Raw SQL is permitted for performance-critical queries, provided they are documented outside the ORM flow.

### Thread 2: "Feature Flag vs. Config File" (Date: 2023-12-05)
-   **Wren M:** "I need to be able to change the dashboard layout for the pilot users without waiting for a deployment. Can we just use a config file in S3?"
-   **Eben O:** "Too slow. We need the A/B framework we discussed. Let's bake it into the feature flag system so we can track the metrics for the board."
-   **Selin G:** "If we use Redis for the flags, I can easily clear the cache during support tickets if a user is stuck in a 'broken' A/B variant."
-   **Decision:** Implement a Redis-backed Feature Flag system with A/B testing capabilities.

### Thread 3: "The DPA Blocker" (Date: 2024-01-20)
-   **Eben O:** "Legal is still sitting on the Data Processing Agreement. We can't trigger SMS or Email notifications without it."
-   **Selin G:** "This is blocking the Notification System and the PDF Reports. Should we pivot?"
-   **Wren M:** "The Data Import/Export is high priority and isn't blocked by the DPA because it's a user-initiated upload. Let's move the team's focus there."
-   **Decision:** Deprioritize Notification and Reporting features; accelerate Data Import/Export development.

---

## 11. BUDGET BREAKDOWN

The total budget is allocated as $5,250,000. This is a flagship initiative with board-level oversight.

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $3,800,000 | 8 Full-time engineers/designers over 20 months (approx. $237k/person avg). |
| **Infrastructure** | $650,000 | AWS ECS, EKS, RDS (PostgreSQL), Redis, and S3 costs including scaling. |
| **External Tools** | $200,000 | GitLab Premium, Twilio, Firebase, Sentry, and Datadog licenses. |
| **Consultancy** | $300,000 | Independent assessment for vendor EOL risk and quarterly pen-testing. |
| **Contingency** | $300,000 | Reserve for scope creep escalation or emergency vendor migration. |
| **Total** | **$5,250,000** | |

---

## 12. APPENDICES

### Appendix A: Data Mapping Logic (Fuzzy Matching)
The Data Import feature uses the following logic for auto-detection of columns:
1.  **Exact Match:** If column name equals `sku`, `quantity`, or `price`.
2.  **Normalized Match:** Convert column name to lowercase, remove underscores/spaces (e.g., `Item_Number` $\rightarrow$ `itemnumber`).
3.  **Levenshtein Distance:** If a normalized match fails, the system calculates the edit distance. If the distance is $\le 2$, the system suggests the match with a confidence score (e.g., "Qty" $\rightarrow$ "Quantity", Score: 0.85).

### Appendix B: Disaster Recovery Plan (DRP)
In the event of a catastrophic failure in the `prod` environment:
1.  **RPO (Recovery Point Objective):** 5 minutes.
2.  **RTO (Recovery Time Objective):** 2 hours.
3.  **Strategy:** 
    -   RDS Multi-AZ deployment provides automatic failover.
    -   S3 Cross-Region Replication for all generated reports.
    -   GitLab CI can redeploy the entire EKS cluster to a secondary AWS region (`us-west-2`) using the Terraform state files stored in a remote backend.