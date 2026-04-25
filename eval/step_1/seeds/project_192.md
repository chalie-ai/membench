# PROJECT SPECIFICATION DOCUMENT: PROJECT MONOLITH
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Status:** Active / In-Development  
**Confidentiality:** Level 4 (Internal/Executive Only)  
**Company:** Ridgeline Platforms  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Monolith" is the strategic initiative by Ridgeline Platforms to modernize the foundational infrastructure of its supply chain management. For over 15 years, Ridgeline has relied on a legacy system—a brittle, monolithic application written in an obsolete framework—that currently manages the movement of materials, contractor procurement, and asset tracking across the company's real estate portfolio. As the company scales, the legacy system has become a primary bottleneck, characterized by extreme fragility and a lack of API connectivity.

The objective of Monolith is the complete replacement of this legacy system. Given that the entire company depends on this system for daily operations, the project mandates a **zero-downtime transition**. Any outage in the supply chain would result in immediate site shutdowns and liquidated damages in the millions of dollars.

### 1.2 Business Justification
The current legacy system suffers from "technical sclerosis." Data is siloed, updates take weeks to deploy, and the cost of maintaining the hardware is skyrocketing. Furthermore, the lack of a modern API layer means that any integration with new real estate fintech tools requires manual CSV exports and imports, introducing human error and security vulnerabilities.

By transitioning to a Python/Django-based modular monolith, Ridgeline Platforms will achieve:
1. **Operational Agility:** The ability to deploy updates daily via a CI/CD pipeline rather than quarterly.
2. **Scalability:** The capacity to handle a 400% increase in transaction volume as the real estate portfolio expands.
3. **Compliance:** Moving to a PCI DSS Level 1 compliant architecture to handle credit card transactions directly, removing the need for expensive third-party payment intermediaries.

### 1.3 ROI Projection and Success Metrics
The project is backed by a **$3,000,000 budget**. The return on investment is calculated based on two primary success metrics:

*   **Metric 1: Transaction Cost Reduction.** By eliminating manual intermediaries and optimizing the supply chain route via the new system, the goal is to reduce the cost per transaction by **35%**. Based on current annual volumes, this represents an estimated saving of $850,000 per annum.
*   **Metric 2: Efficiency Gains.** The legacy system requires extensive manual data entry for procurement. Monolith aims for a **50% reduction in manual processing time**. This will free up approximately 4,200 man-hours per year across the procurement and logistics teams.

The total projected ROI is expected to break even within 22 months of full deployment, with long-term gains stemming from the ability to integrate third-party AI tools via the planned webhook framework.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Monolith is designed as a **Modular Monolith transitioning to Microservices**. The system is built using Python 3.11 and Django 4.2, utilizing a PostgreSQL 15 database for relational data and Redis 7.0 for caching and asynchronous task queuing.

The "Modular Monolith" approach ensures that the codebase is logically separated into domains (e.g., `Procurement`, `Logistics`, `Payments`, `Identity`). This allows the team to extract specific modules into independent microservices via AWS ECS as the load increases, without requiring a complete rewrite of the system.

### 2.2 Architecture Diagram (ASCII)
```text
[ Client Layer ]  --> [ AWS CloudFront / Route 53 ]
                               |
                               v
[ Security Layer ] --> [ AWS ALB (Application Load Balancer) ]
                               |
                               v
[ Application Layer ] --> [ AWS ECS (Django Clusters) ] <--> [ Redis Cache/Celery ]
                               |                              |
                               | (SQL / Raw SQL)               | (Async Tasks)
                               v                              v
[ Data Layer ]       --> [ PostgreSQL RDS (Primary/Replica) ] [ S3 Bucket (Reports) ]
                               |
                               v
[ External Layer ]   --> [ Third Party APIs / PCI DSS Gateway ]
```

### 2.3 Infrastructure Stack
*   **Language/Framework:** Python 3.11 / Django 4.2 (with Django Rest Framework).
*   **Database:** PostgreSQL 15 (Amazon RDS) with a read-replica for reporting.
*   **Caching/Queue:** Redis 7.0 (Amazon ElastiCache) for session management and Celery task brokerage.
*   **Deployment:** AWS ECS (Elastic Container Service) using Fargate for serverless compute.
*   **CI/CD:** GitHub Actions. Every merged Pull Request (PR) is automatically deployed to production.
*   **Security:** PCI DSS Level 1 compliance. All credit card data is encrypted at rest using AWS KMS and transmitted via TLS 1.3.

### 2.4 Performance Trade-offs (Technical Debt)
To maintain performance under the heavy load of the real estate supply chain, the development team has bypassed the Django ORM in **30% of all queries**, utilizing raw SQL. This was necessary to optimize complex joins across multi-million row tables. 
**WARNING:** This creates significant risk during database migrations, as the Django migration tool cannot detect dependencies within raw SQL strings. All migrations must be manually audited by the Lead Engineer.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Complete
**Description:** 
Given the critical nature of the supply chain, the system must protect itself from Denial-of-Service (DoS) attacks and "noisy neighbor" syndrome where one integration exhausts all system resources. This feature implements a sliding-window rate limiting algorithm to throttle requests based on API key and IP address.

**Technical Specification:**
*   **Mechanism:** The system utilizes Redis to track request counts over a 60-second window.
*   **Tiers:** 
    *   *Standard User:* 100 requests/minute.
    *   *Enterprise Integration:* 1,000 requests/minute.
    *   *Internal System:* Unlimited.
*   **Analytics:** Every request is logged into a `usage_logs` table, capturing the endpoint hit, response time, and status code.
*   **Headers:** All API responses must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
*   **Failure Mode:** When a limit is exceeded, the system returns a `429 Too Many Requests` status code with a JSON body indicating the retry-after duration.

**Business Value:** This ensures the system remains available for high-priority transactions during peak real estate procurement cycles and provides the data necessary to charge for "overage" usage in future billing models.

### 3.2 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Complete
**Description:** 
Real estate stakeholders require weekly and monthly supply chain snapshots. This feature allows users to define custom reports (columns, filters, date ranges) and schedule them for automated delivery via email.

**Technical Specification:**
*   **Generation Engine:** Reports are generated asynchronously using Celery workers to avoid blocking the main request-response cycle. PDFs are generated via `WeasyPrint` and CSVs via Python's `csv` module.
*   **Scheduling:** The system uses `django-celery-beat` to manage cron-like schedules.
*   **Storage:** Generated files are uploaded to an encrypted AWS S3 bucket with a 30-day TTL (Time-to-Live) policy.
*   **Delivery:** Links to these reports are dispatched via AWS SES (Simple Email Service).
*   **Report Types:**
    *   *Procurement Summary:* Total spend per vendor.
    *   *Inventory Velocity:* Rate of material consumption.
    *   *Audit Log:* List of all modified transactions for a specific period.

**Business Value:** Reduces the manual effort of the finance team, who previously spent 10+ hours a week manually exporting data from the legacy system.

### 3.3 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:** 
The system requires a granular permissions model to ensure that a warehouse manager cannot approve a $1M procurement request, and a vendor cannot see the pricing of another vendor.

**Technical Specification:**
*   **Authentication:** JWT (JSON Web Tokens) are used for session management.
*   **Roles:** 
    *   `SuperAdmin`: Full system access.
    *   `ProcurementManager`: Can create/edit orders and approve budgets.
    *   `LogisticsCoordinator`: Can update shipment statuses.
    *   `ExternalVendor`: Can only view orders assigned to their OrgID.
*   **RBAC Implementation:** Permissions are checked at the View level using Django's `@permission_classes` and at the Object level using a custom `UserPermission` mixin.
*   **Current State:** Basic login/logout is functional. Granular permission mapping for the "Vendor" role is currently being developed.

**Business Value:** Essential for long-term security and regulatory compliance, although the current MVP relies on a limited set of users.

### 3.4 Webhook Integration Framework
**Priority:** Medium | **Status:** Blocked
**Description:** 
To allow the supply chain to interact with third-party real estate tools (e.g., CRM, Project Management software), Monolith requires a system to "push" events to external URLs when specific triggers occur.

**Technical Specification:**
*   **Event Types:** `ORDER_CREATED`, `SHIPMENT_DELAYED`, `PAYMENT_RECEIVED`.
*   **Mechanism:** When an event triggers, a Celery task is dispatched to POST a JSON payload to the registered webhook URL.
*   **Retry Logic:** Exponential backoff (1min, 5min, 15min, 1hr) if the receiving server returns a non-200 status.
*   **Security:** Each payload includes an `X-Monolith-Signature` (HMAC-SHA256) to allow the receiver to verify the authenticity of the data.
*   **Blocking Factor:** The feature is currently blocked pending the legal review of the Data Processing Agreement (DPA), as sending data to third-party URLs may violate current privacy contracts with vendors.

**Business Value:** Transform Monolith from a standalone tool into a platform, allowing it to trigger actions in other company software.

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low (Nice to Have) | **Status:** In Design
**Description:** 
For PCI DSS and real estate audit requirements, every change to a financial record must be logged. This log must be "tamper-evident," meaning it cannot be altered by a database administrator.

**Technical Specification:**
*   **Capturing:** Use of a Django Signal (`post_save`) to capture the "before" and "after" state of any model in the `Payments` or `Procurement` apps.
*   **Storage:** While the primary log is in PostgreSQL, a cryptographic hash of the log entry is sent to an immutable AWS S3 Glacier vault.
*   **Verification:** A background process periodically re-calculates the hashes to ensure no records in the primary database have been modified.
*   **Fields:** `timestamp`, `user_id`, `action_type`, `entity_id`, `previous_state` (JSON), `new_state` (JSON).

**Business Value:** Mitigates internal fraud risks and ensures the company can pass annual external audits without manual data reconciliation.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 `POST /api/v1/auth/login`
*   **Description:** Authenticates user and returns JWT.
*   **Request Body:** `{"username": "astrid_j", "password": "..."}`
*   **Response (200 OK):** `{"access_token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 3600}`
*   **Response (401):** `{"error": "Invalid credentials"}`

### 4.2 `GET /api/v1/orders/`
*   **Description:** Retrieves a list of supply chain orders.
*   **Query Params:** `?status=shipped&limit=20&offset=0`
*   **Response (200 OK):** 
    ```json
    {
      "count": 150,
      "results": [
        {"id": "ORD-101", "vendor": "SteelCorp", "total": 45000.00, "status": "shipped"}
      ]
    }
    ```

### 4.3 `POST /api/v1/orders/create`
*   **Description:** Creates a new procurement order.
*   **Request Body:** `{"vendor_id": 502, "items": [{"sku": "BEAM-01", "qty": 20}], "budget_code": "B-2025-NY"}`
*   **Response (201 Created):** `{"order_id": "ORD-102", "status": "pending_approval"}`

### 4.4 `PATCH /api/v1/orders/{id}/status`
*   **Description:** Updates the status of an order.
*   **Request Body:** `{"status": "delivered"}`
*   **Response (200 OK):** `{"id": "ORD-101", "new_status": "delivered", "updated_at": "2025-01-10T10:00Z"}`

### 4.5 `GET /api/v1/reports/generate`
*   **Description:** Triggers a manual PDF report generation.
*   **Request Body:** `{"report_type": "inventory_velocity", "date_range": "2024-Q4"}`
*   **Response (202 Accepted):** `{"task_id": "celery-task-998", "status": "processing"}`

### 4.6 `GET /api/v1/reports/download/{task_id}`
*   **Description:** Downloads the generated report.
*   **Response (200 OK):** Binary stream of PDF/CSV file.

### 4.7 `POST /api/v1/payments/process`
*   **Description:** Processes a credit card payment (PCI DSS Level 1).
*   **Request Body:** `{"order_id": "ORD-101", "card_token": "tok_visa_...", "amount": 45000.00}`
*   **Response (200 OK):** `{"transaction_id": "TXN-7765", "status": "success"}`

### 4.8 `GET /api/v1/analytics/usage`
*   **Description:** Returns API usage metrics for the current authenticated key.
*   **Response (200 OK):** `{"total_requests": 1200, "rate_limit_hits": 5, "avg_latency": "145ms"}`

---

## 5. DATABASE SCHEMA

The system utilizes a PostgreSQL 15 database. All primary keys are UUIDs to facilitate future migration to microservices.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email`, `password_hash`, `role_id` | User identity and auth |
| `roles` | `role_id` | - | `role_name`, `permissions_json` | RBAC role definitions |
| `vendors` | `vendor_id` | - | `company_name`, `tax_id`, `contact_email` | Third-party supplier data |
| `products` | `product_id` | `vendor_id` | `sku`, `description`, `unit_price` | Catalog of supply materials |
| `orders` | `order_id` | `user_id`, `vendor_id` | `total_amount`, `status`, `created_at` | Main procurement records |
| `order_items` | `item_id` | `order_id`, `product_id` | `quantity`, `price_at_purchase` | Line items for each order |
| `shipments` | `shipment_id` | `order_id` | `tracking_number`, `carrier`, `eta` | Logistics tracking |
| `payments` | `payment_id` | `order_id` | `amount`, `transaction_ref`, `status` | Financial transaction logs |
| `reports` | `report_id` | `user_id` | `file_path`, `report_type`, `generated_at` | Metadata for generated files |
| `usage_logs` | `log_id` | `user_id` | `endpoint`, `response_time`, `timestamp` | API analytics |

### 5.2 Schema Relationships
*   `users` $\rightarrow$ `roles` (Many-to-One)
*   `orders` $\rightarrow$ `users` (Many-to-One: Order created by user)
*   `orders` $\rightarrow$ `vendors` (Many-to-One: Order assigned to vendor)
*   `order_items` $\rightarrow$ `orders` (Many-to-One: Items belonging to order)
*   `order_items` $\rightarrow$ `products` (Many-to-One: Item refers to catalog product)
*   `payments` $\rightarrow$ `orders` (One-to-One: Each order has one primary payment record)
*   `shipments` $\rightarrow$ `orders` (Many-to-One: An order can have multiple shipments)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Monolith utilizes three distinct environments to ensure stability and zero downtime.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and unit testing.
*   **Infrastructure:** Small ECS cluster, shared PostgreSQL instance.
*   **Deployment:** Triggered on every push to a feature branch.
*   **Data:** Anonymized sample data.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Quality Assurance (QA), UAT, and Integration testing.
*   **Infrastructure:** Mirror of Production (Small scale).
*   **Deployment:** Triggered on merge to the `develop` branch.
*   **Data:** Recent snapshot of production data (scrubbed of PII).

#### 6.1.3 Production (Prod)
*   **Purpose:** Live company operations.
*   **Infrastructure:** High-availability ECS cluster across three Availability Zones (AZs).
*   **Deployment:** Continuous Deployment. Every merged PR to `main` is deployed.
*   **Zero-Downtime Mechanism:** Blue-Green Deployment. The ALB routes traffic to the "Green" version only after health checks pass, and the "Blue" version is kept for 1 hour for immediate rollback.

### 6.2 CI/CD Pipeline
1. **Linting:** Flake8 and Black check for PEP 8 compliance.
2. **Unit Tests:** PyTest suite runs (Must be 100% pass).
3. **Security Scan:** Bandit scans for common Python security vulnerabilities.
4. **Build:** Docker image created and pushed to AWS ECR.
5. **Deploy:** AWS ECS updates the service; health checks performed; traffic shifted.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions and business logic.
*   **Tools:** `pytest`, `unittest.mock`.
*   **Requirement:** 80% code coverage minimum.
*   **Frequency:** Run on every commit.

### 7.2 Integration Testing
*   **Focus:** Interactions between modules (e.g., `Orders` $\rightarrow$ `Payments`).
*   **Tools:** Django Test Client.
*   **Scope:** Testing the API endpoints against a real PostgreSQL test database.
*   **Frequency:** Run during the Staging deployment phase.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** Critical user journeys (e.g., "Create Order $\rightarrow$ Process Payment $\rightarrow$ Generate Invoice").
*   **Tools:** Playwright / Selenium.
*   **Scope:** Browser-based tests simulating a real user in the Staging environment.
*   **Frequency:** Run once per day.

### 7.4 Regression Testing for Raw SQL
Because 30% of the system uses raw SQL, a specific "SQL Regression Suite" is maintained. This suite runs a set of complex queries and compares the results against the ORM outputs to ensure that database migrations haven't broken the raw SQL logic.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Scope creep from stakeholders adding "small" features. | High | Medium | Hire a dedicated contractor to increase throughput and reduce the "bus factor" (dependence on key staff). |
| **R-02** | Integration partner's API is undocumented and buggy. | High | High | Escalate to the next board meeting as a critical blocker to ensure executive pressure on the partner. |
| **R-03** | Database migration failure due to raw SQL usage. | Medium | High | Implement a mandatory peer-review process for all migrations; run the SQL Regression Suite. |
| **R-04** | PCI DSS compliance failure during audit. | Low | Critical | Quarterly internal audits and use of AWS KMS for all sensitive data encryption. |
| **R-05** | Team dysfunction (Astrid and Lead Engineer not speaking). | High | High | Project Lead to implement structured weekly syncs; use Jira/GitHub as the sole source of truth for decisions. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project halt / Data breach.
*   **High:** Significant delay in milestones / Financial loss.
*   **Medium:** Minor delay / Increased cost.
*   **Low:** Negligible impact.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Timeline

| Phase | Duration | Key Focus | Dependencies |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Oct 2023 - Jan 2025 | Core API, Auth, Database Schema | Legal DPA Approval |
| **Phase 2: Core Feature Set** | Jan 2025 - Apr 2025 | Reporting, Payments, Rate Limiting | Phase 1 Completion |
| **Phase 3: Beta Testing** | Apr 2025 - Jun 2025 | Pilot users, Bug fixing, Performance tuning | MVP Feature Complete |
| **Phase 4: Full Rollout** | Jun 2025 - Aug 2025 | Final migrations, Legacy shutdown | External Beta Sign-off |

### 9.2 Key Milestones
*   **Milestone 1: MVP Feature-Complete**
    *   **Target Date:** 2025-04-15
    *   **Criteria:** All "High" and "Critical" priority features are passing E2E tests.
*   **Milestone 2: External Beta with 10 Pilot Users**
    *   **Target Date:** 2025-06-15
    *   **Criteria:** 10 selected real estate vendors successfully processing orders in the Staging environment.
*   **Milestone 3: First Paying Customer Onboarded**
    *   **Target Date:** 2025-08-15
    *   **Criteria:** Successful live transaction through the PCI-compliant payment gateway.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per team policy, there are no formal meeting minutes. The following are synthesized summaries of decision-making threads from the `#proj-monolith-dev` Slack channel.*

### Thread 1: The "Raw SQL" Debate
**Date:** November 12, 2023
**Participants:** Astrid Jensen (VP Product), Farid Costa (Frontend Lead), Lead Engineer (Anonymous)
**Discussion:**
*   Lead Engineer argues that the Django ORM is too slow for the `inventory_ledger` table, which has 12 million rows.
*   Astrid expresses concern about "unmaintainable code" and "magic strings" in the codebase.
*   Lead Engineer demonstrates a 10x performance increase using raw SQL window functions.
*   **Decision:** Raw SQL is permitted for performance-critical queries, but must be documented in the `sql_performance.md` file.

### Thread 2: The "Integration Partner" Crisis
**Date:** December 5, 2023
**Participants:** Astrid Jensen, Yonas Costa (Support Engineer)
**Discussion:**
*   Yonas reports that the external API from the primary steel vendor is returning 500 errors for 30% of requests and the documentation hasn't been updated since 2019.
*   Astrid is frustrated that the team is spending 20% of their sprint fixing the partner's bugs.
*   **Decision:** This is too big for the dev team to solve. Astrid will raise this as a blocker at the next board meeting to force the partner to assign a dedicated engineer to the integration.

### Thread 3: Webhook Blockage
**Date:** January 14, 2024
**Participants:** Astrid Jensen, Noor Jensen (Product Designer), Legal Counsel
**Discussion:**
*   Noor presents the UI for the Webhook management dashboard.
*   Legal Counsel interrupts, stating that the current Data Processing Agreement (DPA) with vendors does not allow "automated push notifications to third-party endpoints" without an explicit opt-in.
*   Astrid asks if we can bypass this for "Internal" tools. Legal says no.
*   **Decision:** The Webhook framework is moved to "Blocked" status until the legal review of the DPA is completed.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

### 11.1 Personnel ($2,100,000)
*   **Internal Salaries:** $1,500,000 (12-person team for 18 months).
*   **Contractor (Bus Factor Mitigation):** $400,000 (Senior Python Consultant to support the Lead Engineer).
*   **Benefits/Overhead:** $200,000.

### 11.2 Infrastructure ($450,000)
*   **AWS ECS/Fargate:** $150,000 (Compute and scaling).
*   **AWS RDS (PostgreSQL):** $120,000 (High-availability multi-AZ instances).
*   **AWS S3/Glacier:** $80,000 (Archival and audit storage).
*   **Redis/ElastiCache:** $100,000.

### 11.3 Tools and Licensing ($150,000)
*   **GitHub Enterprise:** $30,000.
*   **Sentry/Datadog:** $60,000 (Monitoring and error tracking).
*   **PCI Compliance Certification/Audit:** $60,000.

### 11.4 Contingency ($300,000)
*   **Emergency Buffer:** $300,000 (Reserved for unforeseen technical debt, hardware spikes, or extension of the contractor's term).

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Implementation Details
To maintain Level 1 compliance, Project Monolith implements the following:
1.  **Tokenization:** Credit card numbers are never stored in the PostgreSQL database. We use a "Vault" approach where the card data is exchanged for a token via the payment gateway.
2.  **Encryption:** All data in transit is encrypted via TLS 1.3. All data at rest (even tokens) is encrypted using AES-256 via AWS KMS.
3.  **Network Isolation:** The payment processing logic is isolated in a separate ECS service task with restricted ingress/egress rules, separate from the general API.

### Appendix B: Data Migration Strategy (Legacy $\rightarrow$ Monolith)
The transition from the 15-year-old system will follow a "Strangler Fig" pattern:
1.  **Read-Only Sync:** The new system will initially act as a read-only mirror of the legacy database.
2.  **Write-Through:** For specific modules (starting with `Reports`), the new system will handle the write, then sync back to the legacy system.
3.  **Full Cutover:** Once the `Payments` module is verified, the legacy system's payment logic will be disabled, and Monolith becomes the "System of Record."
4.  **Legacy Decommission:** After 90 days of zero-error operation, the legacy servers will be archived and shut down.