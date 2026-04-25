# PROJECT SPECIFICATION: PROJECT UMBRA
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 24, 2023  
**Company:** Duskfall Inc.  
**Project Lead:** Orla Kim (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Duskfall Inc., a leading provider of educational infrastructure, currently operates four disparate internal tools for managing its supply chain: *EduLogistics*, *VendorTrack*, *AssetFlow*, and *CampusStock*. These systems are redundant, fragmented, and create significant operational friction. Data silos between these tools result in manual double-entry, inconsistent reporting, and an average of 14 hours per week spent per administrator on manual reconciliation.

Project **Umbra** is a strategic cost-reduction initiative designed to consolidate these four legacy tools into a single, unified supply chain management system. By centralizing the procurement, tracking, and distribution of educational materials, Duskfall Inc. aims to eliminate the licensing costs of four separate vendor contracts and the overhead of maintaining four distinct codebases.

### 1.2 ROI Projection
The budget for Project Umbra is set at $3,000,000. This is a substantial investment with high executive visibility, reflecting the critical nature of the supply chain to the company's bottom line. The projected ROI is calculated based on the following factors:
- **Direct Cost Savings:** Elimination of four legacy software licenses and maintenance contracts, estimated at $450,000 annually.
- **Operational Efficiency:** A target metric of a 50% reduction in manual processing time for end-users. Based on current labor costs, this translates to an estimated $1.2M in reclaimed productivity over 24 months.
- **Risk Mitigation:** By moving to a single, FedRAMP-authorized system, Duskfall Inc. can penetrate higher-value government education contracts, potentially increasing annual recurring revenue (ARR) by 15-20%.

The project is not merely a technical upgrade but a business transformation. The successful delivery of Umbra will allow Duskfall Inc. to scale its operations without a linear increase in administrative headcount.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Umbra is built as a **clean monolith**. While the industry trend favors microservices, the team of 8 across 2 time zones requires a simplified deployment and development model to maintain agility. To prevent the monolith from becoming "spaghetti code," the system utilizes strict **module boundaries**. Each core domain (Billing, Inventory, User Management, Workflow) is isolated within its own Django app with restricted imports to ensure that logic does not leak across boundaries.

### 2.2 Technology Stack
- **Backend:** Python 3.11 / Django 4.2 (Long Term Support)
- **Database:** PostgreSQL 15 (Primary relational store)
- **Caching/Queue:** Redis 7.0 (Used for session management and Celery task queuing)
- **Deployment:** AWS ECS (Elastic Container Service) using Fargate for serverless scaling.
- **Infrastructure as Code:** Terraform for environment provisioning.
- **CI/CD:** GitHub Actions triggering automatic deployments to production upon PR merge.

### 2.3 System Diagram (ASCII Representation)

```text
[ User Browser / API Client ] 
           |
           v
    [ AWS Application Load Balancer ]
           |
           v
    [ AWS ECS Fargate Cluster ] <--- (Continuous Deployment)
    |-------------------------|
    |   Django Web Server     | <--- [ Redis Cache ]
    |   (Clean Monolith)      |
    |-------------------------|
           |           |
           v           v
    [ PostgreSQL ]  [ AWS S3 ]
    (Relational)    (Document Storage)
           ^
           |
    [ FedRAMP Compliance Layer ] (Encryption at Rest/Transit)
```

### 2.4 Security and Compliance
Because Duskfall Inc. services government clients, **FedRAMP authorization** is a non-negotiable requirement.
- **Encryption:** All data is encrypted at rest using AWS KMS and in transit via TLS 1.3.
- **Access Control:** Role-Based Access Control (RBAC) is implemented at the database and application levels.
- **Auditability:** The system must support comprehensive logging (see Feature 1).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:** 
Given that supply chain coordinators often work on the same procurement lists simultaneously, Umbra implements a real-time collaborative environment. This prevents "last-write-wins" data loss and allows team members to see updates in real-time.

**Technical Implementation:**
The system utilizes a combination of WebSockets (via Django Channels) and Operational Transformation (OT). When a user edits a field in a procurement record, the change is broadcast to all connected clients. To handle conflicts, the system employs a version-vectoring mechanism: each change is timestamped and assigned a sequence number. If two users edit the same field simultaneously, the system applies the change with the higher sequence number but flags the conflict for the user if the delta is significant.

**Functional Requirements:**
- Presence indicators showing which users are currently viewing a specific record.
- Cursor tracking to show where other users are editing.
- Automatic merging of non-overlapping field changes.
- Conflict notification UI when overlapping changes occur.

---

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Users have varying needs based on their role (e.g., a Warehouse Manager needs different data than a CFO). This feature allows users to build a personalized landing page using a library of pre-defined widgets.

**Technical Implementation:**
The frontend will use a grid-based layout system (React-Grid-Layout). The configuration for each user's dashboard (widget ID, coordinates, and dimensions) will be stored as a JSON blob in the `UserPreference` table in PostgreSQL. Widgets will be implemented as independent components that fetch data via specific API endpoints.

**Functional Requirements:**
- Library of widgets: "Pending Approvals," "Low Stock Alerts," "Spending Trends," and "Recent Activity."
- Drag-and-drop interface to rearrange widgets.
- Resizable widget containers.
- "Save Layout" and "Reset to Default" functionality.
- Role-based widget availability (e.g., only Admins see "Budget Overruns").

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** In Review

**Description:**
To replace manual processing, Umbra includes an engine that allows users to define "If-This-Then-That" (IFTTT) rules for supply chain events. For example: "If inventory of iPads drops below 10, then create a purchase request for 50 units and notify the Procurement Lead."

**Technical Implementation:**
The engine consists of a Rule Parser and a Task Executor. The Visual Rule Builder (frontend) generates a JSON representation of the logic, which is stored in the `WorkflowRule` table. The backend utilizes a Celery worker that listens for "Signal" events emitted by the Django models. When a signal is triggered, the engine evaluates all active rules associated with that event.

**Functional Requirements:**
- Visual interface for building rules (Trigger $\rightarrow$ Condition $\rightarrow$ Action).
- Support for multiple triggers (e.g., `on_stock_change`, `on_order_received`).
- Conditional logic (And/Or/Not).
- Action execution: Email notifications, API calls to vendors, or status updates within Umbra.

---

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Medium | **Status:** In Design

**Description:**
To facilitate integration with external vendors, Umbra provides a RESTful API. This allows vendors to push shipping updates or pull order requirements directly into the system.

**Technical Implementation:**
The API is built using Django REST Framework (DRF). To ensure backward compatibility, versioning is handled via the URL path (e.g., `/api/v1/`). A separate "Sandbox" environment is deployed on a different ECS cluster, using a sanitized copy of the production database, allowing customers to test integrations without affecting live data.

**Functional Requirements:**
- API Key management and rotation.
- Rate limiting (1,000 requests per hour per key).
- Comprehensive Swagger/OpenAPI documentation.
- Sandbox environment with mock data for testing.
- Versioning strategy: v1 remains supported for 12 months after v2 release.

---

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low | **Status:** Blocked

**Description:**
For FedRAMP compliance and internal security, every change to a financial or inventory record must be logged. These logs must be "tamper-evident," meaning that once a log is written, it cannot be altered without detection.

**Technical Implementation:**
The system will implement a write-once, read-many (WORM) storage strategy. Each log entry will contain a cryptographic hash of the previous entry, creating a blockchain-like ledger. These logs will be streamed to an AWS S3 bucket with "Object Lock" enabled, preventing deletion or modification for a set retention period.

**Functional Requirements:**
- Logging of the "Who, What, When, and Where" for every `POST`, `PUT`, and `DELETE` request.
- Snapshotting of the record state before and after the change.
- Ability to regenerate the hash chain to verify log integrity.
- Searchable audit interface for compliance officers.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base URL: `https://api.umbra.duskfall.com/v1/`

### 4.1 `GET /orders/`
**Description:** Retrieve a list of all supply chain orders.
- **Request Parameters:** `status` (optional), `page` (optional).
- **Response:** 
  ```json
  {
    "count": 120,
    "results": [
      {"id": "ORD-101", "status": "shipped", "total": 4500.00, "created_at": "2023-10-01T10:00Z"}
    ]
  }
  ```

### 4.2 `POST /orders/`
**Description:** Create a new procurement order.
- **Request Body:** 
  ```json
  {
    "vendor_id": "VND-99",
    "items": [{"sku": "LAP-01", "qty": 10}, {"sku": "MOU-02", "qty": 20}],
    "requested_by": "user_123"
  }
  ```
- **Response:** `201 Created` with the order object.

### 4.3 `GET /inventory/{sku}/`
**Description:** Check real-time stock levels for a specific SKU.
- **Response:**
  ```json
  {
    "sku": "LAP-01",
    "quantity": 45,
    "warehouse_location": "Zone-B4",
    "status": "in-stock"
  }
  ```

### 4.4 `PATCH /inventory/{sku}/`
**Description:** Update stock levels (used by warehouse scanners).
- **Request Body:** `{"quantity_change": -5}`
- **Response:** `200 OK` with the updated quantity.

### 4.5 `GET /vendors/`
**Description:** List all approved vendors.
- **Response:**
  ```json
  {
    "vendors": [{"id": "VND-99", "name": "Global Edu Supplies", "rating": 4.8}]
  }
  ```

### 4.6 `POST /workflow/rules/`
**Description:** Create a new automation rule.
- **Request Body:**
  ```json
  {
    "name": "Low Stock Alert",
    "trigger": "stock_low",
    "action": "email_notification",
    "params": {"recipient": "procurement@duskfall.com"}
  }
  ```
- **Response:** `201 Created`.

### 4.7 `GET /dashboard/widgets/`
**Description:** Get the list of available widgets for the user.
- **Response:**
  ```json
  {
    "available_widgets": ["spend_chart", "pending_approvals", "stock_alerts"]
  }
  ```

### 4.8 `DELETE /api-keys/{key_id}/`
**Description:** Revoke an API key.
- **Response:** `204 No Content`.

---

## 5. DATABASE SCHEMA

The system uses a PostgreSQL relational database. Relationships are strictly enforced via foreign keys.

### 5.1 Tables and Fields

1.  **`Users`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `role` (Enum: Admin, Manager, Staff)
    - `last_login` (DateTime)
2.  **`Vendors`**
    - `id` (UUID, PK)
    - `company_name` (String)
    - `contact_email` (String)
    - `payment_terms` (String)
    - `is_approved` (Boolean)
3.  **`Products`**
    - `id` (UUID, PK)
    - `sku` (String, Unique)
    - `name` (String)
    - `category` (String)
    - `unit_price` (Decimal)
4.  **`Inventory`**
    - `id` (UUID, PK)
    - `product_id` (FK $\rightarrow$ Products)
    - `quantity` (Integer)
    - `warehouse_location` (String)
    - `reorder_point` (Integer)
5.  **`Orders`**
    - `id` (UUID, PK)
    - `vendor_id` (FK $\rightarrow$ Vendors)
    - `user_id` (FK $\rightarrow$ Users)
    - `order_date` (DateTime)
    - `status` (Enum: Pending, Approved, Shipped, Received)
    - `total_amount` (Decimal)
6.  **`OrderItems`**
    - `id` (UUID, PK)
    - `order_id` (FK $\rightarrow$ Orders)
    - `product_id` (FK $\rightarrow$ Products)
    - `quantity` (Integer)
    - `price_at_purchase` (Decimal)
7.  **`WorkflowRules`**
    - `id` (UUID, PK)
    - `name` (String)
    - `trigger_event` (String)
    - `logic_json` (JSONB)
    - `is_active` (Boolean)
8.  **`UserPreferences`**
    - `user_id` (FK $\rightarrow$ Users, PK)
    - `dashboard_layout` (JSONB)
    - `theme` (String)
9.  **`AuditLogs`**
    - `id` (UUID, PK)
    - `timestamp` (DateTime)
    - `user_id` (FK $\rightarrow$ Users)
    - `action` (String)
    - `entity_id` (UUID)
    - `previous_state` (JSONB)
    - `new_state` (JSONB)
    - `hash` (String)
10. **`BillingInvoices`**
    - `id` (UUID, PK)
    - `order_id` (FK $\rightarrow$ Orders)
    - `invoice_date` (DateTime)
    - `amount_due` (Decimal)
    - `paid_status` (Boolean)

### 5.2 Key Relationships
- **One-to-Many:** `Vendors` $\rightarrow$ `Orders` (One vendor can have many orders).
- **Many-to-Many:** `Orders` $\leftrightarrow$ `Products` (via `OrderItems`).
- **One-to-One:** `Users` $\rightarrow$ `UserPreferences`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and initial integration testing.
- **Deployment:** Triggered on merge to the `develop` branch.
- **Data:** Mock data, frequently wiped and reset.
- **Access:** Full access for all 8 team members.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Deployment:** Triggered on merge to the `release` branch.
- **Data:** Anonymized snapshot of production data.
- **Access:** Developers and QA; mirrored exactly to production hardware specs.

#### 6.1.3 Production (Prod)
- **Purpose:** Live system for Duskfall Inc. and government clients.
- **Deployment:** Continuous Deployment (CD). Every PR merged into `main` is automatically deployed via GitHub Actions to AWS ECS.
- **Data:** Live customer data, encrypted and backed up hourly to RDS snapshots.
- **Access:** Highly restricted; managed via AWS IAM and Just-In-Time (JIT) access.

### 6.2 CI/CD Pipeline
The pipeline is configured as follows:
1. **Linting/Static Analysis:** Flake8 and Black run on every commit.
2. **Unit Tests:** PyTest suite runs; must achieve 80% coverage (except for the billing module—see Technical Debt).
3. **Containerization:** Docker image is built and pushed to AWS ECR.
4. **Deployment:** ECS service is updated using a rolling update strategy to ensure zero downtime.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Unit tests focus on the business logic within the Django modules. Each service method is tested in isolation using `unittest.mock` to simulate database calls and external API responses. 
- **Target:** 80% coverage across the monolith.
- **Tool:** PyTest.

### 7.2 Integration Testing
Integration tests verify the interaction between the Django app, PostgreSQL, and Redis. These tests are run in a containerized environment that mirrors production.
- **Key Areas:** Order lifecycle (from creation $\rightarrow$ approval $\rightarrow$ shipping), Workflow rule triggering, and API endpoint connectivity.
- **Tool:** Django Test Framework.

### 7.3 End-to-End (E2E) Testing
E2E tests simulate actual user journeys using a headless browser.
- **Critical Paths:** 
  1. User logs in $\rightarrow$ Navigates to Dashboard $\rightarrow$ Creates Order $\rightarrow$ Verifies Inventory Decrease.
  2. User opens Rule Builder $\rightarrow$ Creates Automation $\rightarrow$ Triggers Event $\rightarrow$ Verifies Email Arrival.
- **Tool:** Playwright / Cypress.

### 7.4 Special Case: Billing Module
Due to deadline pressure, the **core billing module was deployed without tests**. This is officially logged as high-priority technical debt. A "Stabilization Sprint" is scheduled for Q3 2024 to retrofit this module with 100% test coverage.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor announced EOL (End of Life) for a core dependency. | High | Medium | Accept the risk for now. Monitor vendor updates weekly and evaluate alternatives if EOL affects core stability. |
| **R-02** | Competitor is building a similar product and is 2 months ahead. | Medium | High | Escalate to the board meeting as a blocker. Accelerate "Critical" feature delivery to close the gap. |
| **R-03** | Failure to achieve FedRAMP authorization. | Low | Critical | Maintain strict adherence to the security spec; engage a 3rd party auditor for a pre-audit gap analysis. |
| **R-04** | Technical debt in billing module leads to financial errors. | Medium | High | Schedule immediate "Stabilization Sprint" for test coverage. Implement manual auditing for all invoices in the interim. |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required; project failure risk.
- **High:** Serious impact; requires active management.
- **Medium:** Manageable; monitor closely.
- **Low:** Minor impact; accept and track.

---

## 9. TIMELINE AND MILESTONES

Project Umbra follows an aggressive timeline to consolidate legacy tools before the next fiscal year.

### 9.1 Phases
- **Phase 1: Foundation (Oct 2023 - Feb 2024):** Architecture setup, database schema finalization, and implementation of "Real-time Collaborative Editing."
- **Phase 2: Core Feature Build (Mar 2024 - May 2024):** Development of Dashboards, Workflow Engine, and API.
- **Phase 3: Compliance & Hardening (May 2024 - Sept 2024):** FedRAMP audit preparation, audit trail implementation, and billing module test retrofitting.

### 9.2 Key Milestones
- **Milestone 1: Production Launch**
  - **Target Date:** 2025-05-15
  - **Dependencies:** Dashboard and Collaborative Editing must be 100% complete.
- **Milestone 2: First Paying Customer Onboarded**
  - **Target Date:** 2025-07-15
  - **Dependencies:** API Sandbox must be operational; Legal review of DPA must be complete.
- **Milestone 3: Internal Alpha Release**
  - **Target Date:** 2025-09-15
  - **Dependencies:** Full migration of data from the 4 legacy tools.

---

## 10. MEETING NOTES

### 10.1 Meeting: Architecture Review
**Date:** 2023-11-12  
**Participants:** Orla Kim, Taj Stein, Malik Liu, Zia Nakamura  
**Discussion:** 
The team debated whether to split the monolith into microservices. Taj argued that the overhead of managing 5+ services would slow down the team of 8. Orla decided on a "Clean Monolith" approach with strict module boundaries to balance scalability and velocity. Malik raised concerns about the UX of the dashboard widgets, suggesting they be customizable per user rather than per role.

**Action Items:**
- [Taj] Set up AWS ECS Fargate cluster for Dev environment. (Completed)
- [Malik] Create low-fidelity wireframes for the drag-and-drop dashboard. (Due: 2023-11-20)
- [Orla] Confirm FedRAMP requirements with the legal team. (In Progress)

---

### 10.2 Meeting: Priority Alignment & Risk Assessment
**Date:** 2023-12-05  
**Participants:** Orla Kim, Taj Stein, Zia Nakamura  
**Discussion:**
Orla informed the team that a competitor is roughly 2 months ahead of them in the market. The team discussed shifting resources to the "Customizable Dashboard" to provide a competitive edge. Zia pointed out that the billing module is currently "flying blind" without tests. Orla acknowledged the risk but insisted on pushing for the launch blockers first.

**Action Items:**
- [Orla] Raise the competitor threat as a blocker in the next board meeting. (Scheduled)
- [Zia] Document all known bugs in the billing module for the future stabilization sprint. (Ongoing)
- [Taj] Implement Redis caching for the order list API to improve performance. (Due: 2023-12-15)

---

### 10.3 Meeting: Legal & Compliance Sync
**Date:** 2024-01-10  
**Participants:** Orla Kim, Zia Nakamura, External Legal Counsel  
**Discussion:**
The discussion focused on the Data Processing Agreement (DPA) required for government contracts. Legal noted that the current DPA doesn't sufficiently cover the cross-region data transfer requirements for FedRAMP. This has become the primary project blocker. Zia explained that the audit trail (Feature 1) is technically ready for design but blocked by the legal definitions of "tamper-evident" storage.

**Action Items:**
- [Legal] Revise Section 4.2 of the DPA regarding data residency. (Blocked)
- [Orla] Follow up with the CTO's office regarding the DPA review timeline. (Urgent)
- [Zia] Draft the technical requirements for the S3 Object Lock implementation. (Due: 2024-01-25)

---

## 11. BUDGET BREAKDOWN

The total budget of **$3,000,000** is allocated across the following categories for the duration of the project (through Sept 2025).

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | Salaries for 8 team members, including benefits and bonuses. |
| **Infrastructure** | 15% | $450,000 | AWS ECS, RDS, S3, and Redis costs (inclusive of FedRAMP GovCloud premiums). |
| **Software & Tools** | 5% | $150,000 | GitHub Enterprise, Terraform Cloud, Datadog, and Jira. |
| **External Audits** | 10% | $300,000 | FedRAMP certification costs and 3rd party security penetration testing. |
| **Contingency** | 5% | $150,000 | Reserved for emergency scaling or vendor replacement. |

**Budgetary Note:** Any variance exceeding 10% of a category must be approved by Orla Kim and the Board.

---

## 12. APPENDICES

### Appendix A: Data Migration Strategy
Since Umbra is replacing four redundant tools (*EduLogistics, VendorTrack, AssetFlow, CampusStock*), data migration is a critical path.
1. **Extraction:** ETL scripts will extract data from the four legacy SQL databases into a temporary staging area.
2. **Transformation:** Data will be cleaned to remove duplicates (e.g., the same vendor appearing in three different tools) and mapped to the new Umbra schema.
3. **Loading:** Data will be loaded into the `Prod` environment using a phased approach, starting with the least critical tool (*CampusStock*) and ending with the most critical (*EduLogistics*).
4. **Validation:** A checksum comparison will be performed to ensure no records were lost during migration.

### Appendix B: FedRAMP Compliance Checklist
To achieve authorization, the development team must adhere to the following:
- **FIPS 140-2:** All cryptographic modules must be FIPS-validated.
- **MFA:** Multi-factor authentication is mandatory for all administrative access to the AWS Console and the Umbra Admin panel.
- **Vulnerability Scanning:** Weekly automated scans using AWS Inspector and monthly manual penetration tests.
- **Incident Response:** A documented plan for reporting breaches within 24 hours to the government contracting office.
- **Continuous Monitoring:** Implementation of CloudWatch alerts for all unauthorized access attempts to the database.