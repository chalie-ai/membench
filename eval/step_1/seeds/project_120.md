Due to the extreme length requirements (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). It is designed to serve as the "Single Source of Truth" (SSOT) for the development team at Iron Bay Technologies.

***

# PROJECT AQUEDUCT: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Draft for Review  
**Date:** October 24, 2023  
**Project Lead:** Alejandro Costa (CTO)  
**Company:** Iron Bay Technologies  
**Classification:** Internal / Proprietary / FedRAMP Compliant

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Aqueduct is a strategic cost-reduction and operational efficiency initiative undertaken by Iron Bay Technologies. Currently, the organization utilizes four redundant internal tools for supply chain management (SCM): *IronLogistics*, *BayTrack*, *FinFlow-SCM*, and *NexusBridge*. Each of these tools manages a different segment of the fintech supply chain, yet they overlap in 70% of their functionality, leading to fragmented data, duplicated license costs, and an unsustainable maintenance burden on the engineering team.

The primary objective of Aqueduct is to consolidate these four disparate systems into a single, unified SCM platform. By eliminating the overhead of maintaining four separate codebases and reducing the cognitive load on end-users who must currently pivot between four different UIs, Iron Bay Technologies expects to realize significant operational gains.

### 1.2 ROI Projection
Because Project Aqueduct is currently **unfunded** and is being bootstrapped using existing team capacity, the Return on Investment (ROI) is calculated primarily through "cost avoidance" and "operational efficiency."

**Financial ROI:**
- **License Consolidation:** Elimination of three redundant third-party SaaS licenses (estimated savings: $145,000/annum).
- **Infrastructure Reduction:** Decommissioning of four legacy server clusters in favor of a unified Cloudflare Workers deployment (estimated savings: $42,000/annum).
- **Engineering Hours:** Reduction of maintenance toil from 120 man-hours/month (across 4 tools) to 40 man-hours/month (1 tool), freeing up capacity for revenue-generating features.

**Operational ROI:**
- **Manual Processing Reduction:** The target is a **50% reduction in manual processing time**. Currently, data is manually synced between the four tools; a unified system eliminates this "swivel-chair" integration.
- **System Reliability:** Target of **99.9% uptime** in the first 90 days post-launch, reducing the cost of downtime for government fintech clients.

The projected net benefit is estimated at $210,000 in direct cost savings and an additional $300,000 in reclaimed productivity within the first 18 months post-deployment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Aqueduct utilizes a modern, high-performance stack designed for the rigors of fintech and the security requirements of FedRAMP.

- **Backend:** Rust (using the Axum framework). Rust was chosen for its memory safety and performance, critical for processing high-volume supply chain transactions.
- **Frontend:** React (TypeScript) employing a **micro-frontend architecture**. This allows different modules (e.g., Inventory, Shipping, Billing) to be developed and deployed independently by sub-teams.
- **Edge Storage:** SQLite. To support offline-first capabilities and low-latency data access at the edge, SQLite is deployed within the Cloudflare environment.
- **Deployment Platform:** Cloudflare Workers. This provides global distribution and minimizes latency for our distributed team and clients.

### 2.2 Architectural Diagram (ASCII Description)
The system follows a decoupled, event-driven architecture.

```text
[ Client Browser / App ] 
       |
       v
[ Cloudflare Global Edge ] <---> [ SQLite Edge DB ]
       |
       +--- (Routing) ---> [ Micro-Frontend A: Inventory ]
       |           +-----> [ Micro-Frontend B: Shipping ]
       |           +-----> [ Micro-Frontend C: Admin ]
       |
       v
[ Rust Backend (Axum) ] <---> [ Primary Persistence Layer ]
       |
       +--- [ Auth Engine ] (The 'God Class' - Pending Refactor)
       |
       +--- [ Webhook Framework ] <---> [ Third Party APIs ]
       |
       +--- [ Data Import/Export ] <---> [ S3 / Blob Storage ]
```

### 2.3 Micro-Frontend Ownership
To maintain velocity, ownership is split. While the team is distributed across 5 countries, the micro-frontend architecture ensures that a change in the "Billing" module does not risk the stability of the "Tracking" module.

- **Module 1 (Core):** Auth, User Profile, Settings.
- **Module 2 (Logistics):** Shipping, Customs, Freight.
- **Module 3 (Financials):** Invoicing, Payments, Tax.
- **Module 4 (Warehouse):** Inventory, SKUs, Stock alerts.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Multi-Tenant Data Isolation
**Priority:** Low | **Status:** Not Started | **Owner:** Orin Kim

**Description:**
The system must support multiple distinct organizations (tenants) sharing the same underlying infrastructure while ensuring that no tenant can access another tenant's data. This is a "nice-to-have" for the initial launch but essential for long-term scalability.

**Functional Requirements:**
- **Logical Isolation:** Every table in the database must include a `tenant_id` UUID.
- **Query Interceptors:** The Rust backend must implement a middleware that automatically injects `WHERE tenant_id = X` into every SQL query based on the authenticated session.
- **Tenant Management:** A super-admin dashboard to create, suspend, and delete tenants.

**Technical Implementation:**
The isolation will be achieved at the application layer (Row-Level Security equivalent). When a request hits the backend, the JWT (JSON Web Token) will be decoded to extract the `tenant_id`. This ID will be passed into the database connection pool.

**Constraints:**
Since we are using SQLite at the edge for certain functions, the isolation must be handled carefully during synchronization to the primary persistence layer to avoid data leakage during "burst" writes.

---

### 3.2 Feature 2: Offline-First Mode with Background Sync
**Priority:** Medium | **Status:** In Review | **Owner:** Asha Gupta

**Description:**
Supply chain managers often work in warehouses with intermittent connectivity. Aqueduct must allow users to perform all critical actions (updating inventory, marking shipments as received) while offline, with automatic synchronization once a connection is restored.

**Functional Requirements:**
- **Local Persistence:** Use IndexedDB in the browser to cache the current state of the working set.
- **Conflict Resolution:** Implementation of a "Last-Write-Wins" (LWW) strategy by default, with a "Manual Review" flag for high-value financial transactions.
- **Sync Status Indicator:** A UI component showing "Synced," "Syncing," or "Offline - Changes Pending."

**Technical Implementation:**
The React frontend will utilize a service worker to intercept network requests. If the network is unavailable, the request is queued in a local SQLite (WASM) instance. Upon reconnection, a background sync process will iterate through the queue and push changes to the Rust backend via a `/sync` endpoint.

**Success Metric:**
Users should be able to perform 100% of "Warehouse Management" tasks without an active internet connection, with a synchronization lag of less than 5 seconds upon reconnection.

---

### 3.3 Feature 3: Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** Blocked | **Owner:** Asha Gupta

**Description:**
Aqueduct must be able to notify third-party fintech tools (e.g., ERPs, accounting software) when specific events occur within the supply chain (e.g., `shipment.delivered`, `invoice.paid`).

**Functional Requirements:**
- **Webhook Registration:** A UI where users can provide a Target URL and select which events they wish to subscribe to.
- **Retry Logic:** Exponential backoff for failed deliveries (attempts at 1m, 5m, 15m, 1h, 6h).
- **Security:** Implementation of HMAC signatures (SHA-256) in the header to allow the receiving party to verify the payload originated from Aqueduct.

**Technical Implementation:**
A dedicated Rust service will handle the event queue. When an event is triggered in the core logic, it is pushed to a Redis-backed queue. The Webhook Worker picks up the event, looks up registered URLs in the `webhook_subscriptions` table, and dispatches the POST request.

**Blocker Note:**
Currently blocked due to the absence of the key team member on medical leave, who owns the signature verification logic.

---

### 3.4 Feature 4: Customer-Facing API (Versioning & Sandbox)
**Priority:** Critical (Launch Blocker) | **Status:** In Review | **Owner:** Alejandro Costa

**Description:**
To transition from a tool to a platform, Aqueduct must provide a robust API that allows customers to programmatically interact with their supply chain data.

**Functional Requirements:**
- **API Versioning:** Support for URI-based versioning (e.g., `/v1/orders`, `/v2/orders`).
- **Sandbox Environment:** A mirrored "Sandbox" environment where customers can test API calls without affecting production data.
- **Rate Limiting:** Tiered rate limiting (e.g., 100 requests/min for Basic, 1000/min for Enterprise).

**Technical Implementation:**
The API will be developed using the Axum framework with a dedicated `ApiVersion` middleware. The sandbox will be a separate Cloudflare Worker environment pointing to a cloned "Sandbox" database.

**Documentation:**
Auto-generated OpenAPI 3.0 specs (Swagger) will be hosted at `/docs/api`.

---

### 3.5 Feature 5: Data Import/Export with Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** In Progress | **Owner:** Renzo Fischer

**Description:**
Since Aqueduct is consolidating four legacy tools, users must be able to migrate their historical data. The system must support CSV, JSON, and XML formats and automatically detect the schema of the uploaded file.

**Functional Requirements:**
- **Format Auto-Detection:** The system must analyze the first 10 lines of an upload to determine if it is CSV, JSON, or XML.
- **Field Mapping UI:** A drag-and-drop interface allowing users to map their legacy columns (e.g., "Ship_Date") to Aqueduct fields (e.g., `dispatch_timestamp`).
- **Validation Engine:** Pre-import check that flags data type mismatches (e.g., text in a currency field).

**Technical Implementation:**
The backend will use a streaming parser (to handle files up to 500MB) written in Rust. For auto-detection, a "magic byte" and pattern-matching algorithm will be used. Validated data will be staged in a `temp_import` table before being committed to the primary tables.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and return JSON. Base URL: `https://api.aqueduct.ironbay.tech`

### 4.1 Authentication
- **Endpoint:** `POST /v1/auth/login`
- **Request:** `{ "username": "string", "password": "string" }`
- **Response:** `200 OK { "token": "jwt_string", "expires_at": "iso_date" }`

### 4.2 Order Management
- **Endpoint:** `GET /v1/orders`
- **Request:** `Query Params: ?status=pending&limit=20`
- **Response:** `200 OK [ { "id": "uuid", "sku": "string", "quantity": 10, "status": "pending" }, ... ]`

- **Endpoint:** `POST /v1/orders`
- **Request:** `{ "sku": "string", "quantity": "int", "destination": "string" }`
- **Response:** `201 Created { "id": "uuid", "status": "created" }`

### 4.3 Inventory Control
- **Endpoint:** `GET /v1/inventory/{sku}`
- **Request:** `Path Param: sku`
- **Response:** `200 OK { "sku": "string", "stock_level": 500, "warehouse_location": "US-East-1" }`

- **Endpoint:** `PATCH /v1/inventory/{sku}`
- **Request:** `{ "adjustment": -10, "reason": "damaged" }`
- **Response:** `200 OK { "new_stock_level": 490 }`

### 4.4 Webhook Management
- **Endpoint:** `POST /v1/webhooks`
- **Request:** `{ "url": "https://client.com/hook", "events": ["order.created", "shipment.delayed"] }`
- **Response:** `201 Created { "webhook_id": "uuid" }`

- **Endpoint:** `DELETE /v1/webhooks/{id}`
- **Request:** `Path Param: id`
- **Response:** `204 No Content`

### 4.5 Data Migration
- **Endpoint:** `POST /v1/import/upload`
- **Request:** `Multipart/form-data: file`
- **Response:** `202 Accepted { "job_id": "uuid", "status": "processing" }`

---

## 5. DATABASE SCHEMA

The system uses a relational model. Primary persistence is PostgreSQL (hosted on Cloudflare Hyperdrive), with SQLite used for edge caching.

### 5.1 Table Definitions

1.  **`tenants`**: (Top-level isolation)
    - `id` (UUID, PK)
    - `name` (VARCHAR)
    - `plan_type` (ENUM: basic, enterprise)
    - `created_at` (TIMESTAMP)

2.  **`users`**:
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants.id)
    - `email` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `role` (ENUM: admin, operator, viewer)

3.  **`products`**:
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants.id)
    - `sku` (VARCHAR, Unique per tenant)
    - `description` (TEXT)
    - `unit_price` (DECIMAL)

4.  **`inventory_levels`**:
    - `product_id` (UUID, FK -> products.id)
    - `warehouse_id` (UUID, FK -> warehouses.id)
    - `quantity` (INT)
    - `last_updated` (TIMESTAMP)

5.  **`warehouses`**:
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants.id)
    - `location_code` (VARCHAR)
    - `address` (TEXT)

6.  **`orders`**:
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants.id)
    - `customer_id` (UUID, FK -> customers.id)
    - `order_date` (TIMESTAMP)
    - `total_amount` (DECIMAL)

7.  **`order_items`**:
    - `id` (UUID, PK)
    - `order_id` (UUID, FK -> orders.id)
    - `product_id` (UUID, FK -> products.id)
    - `quantity` (INT)
    - `price_at_purchase` (DECIMAL)

8.  **`shipments`**:
    - `id` (UUID, PK)
    - `order_id` (UUID, FK -> orders.id)
    - `carrier` (VARCHAR)
    - `tracking_number` (VARCHAR)
    - `status` (ENUM: pending, shipped, delivered, delayed)

9.  **`webhook_subscriptions`**:
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants.id)
    - `target_url` (TEXT)
    - `secret_key` (TEXT)

10. **`audit_logs`**:
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `action` (TEXT)
    - `timestamp` (TIMESTAMP)
    - `ip_address` (VARCHAR)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Aqueduct follows a strict promotion path to ensure stability and FedRAMP compliance.

**1. Development (Dev):**
- **Purpose:** Feature iteration and internal testing.
- **Deployments:** Automated on every push to `develop` branch.
- **Database:** Mock data / ephemeral SQLite instances.

**2. Staging (Staging):**
- **Purpose:** Pre-production validation and stakeholder demos.
- **Deployments:** Manual trigger from `develop` to `staging`.
- **Database:** Sanitized clone of production data.

**3. Production (Prod):**
- **Purpose:** Live customer traffic.
- **Deployments:** **Manual QA Gate.** Every deployment requires a sign-off from the Project Lead (Alejandro Costa) and a QA engineer.
- **Turnaround:** 2-day turnaround for any hotfix or feature release to allow for rigorous regression testing.

### 6.2 Infrastructure Components
- **Edge Runtime:** Cloudflare Workers.
- **Storage:** Cloudflare R2 for imported files; Hyperdrive for PostgreSQL acceleration.
- **Secrets Management:** Cloudflare Secrets (AES-256 encryption).
- **Security:** FedRAMP High authorization is required. This necessitates data encryption at rest and in transit, as well as strict IAM (Identity and Access Management) roles.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic in Rust.
- **Tooling:** `cargo test`.
- **Requirement:** 80% code coverage for the `core_logic` module.
- **Frequency:** Executed on every commit.

### 7.2 Integration Testing
- **Focus:** API endpoints and Database interactions.
- **Method:** Spin up a Dockerized PostgreSQL instance and run a suite of requests against the Rust backend.
- **Key Scenarios:** Tenant isolation checks (Ensuring User A cannot see User B's orders).

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "Import CSV $\rightarrow$ Verify Inventory $\rightarrow$ Create Order").
- **Tooling:** Playwright / Cypress.
- **Frequency:** Run on the Staging environment before the "Manual QA Gate" sign-off for Production.

### 7.4 FedRAMP Compliance Testing
- Quarterly vulnerability scans and penetration testing.
- Audit log verification to ensure every data mutation is tracked.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor EOL (End-of-Life) | High | Critical | Build a contingency fallback architecture using an open-source alternative. |
| R-02 | Stakeholder Scope Creep | High | Medium | Raise as a blocker in the next board meeting; strictly adhere to the "Priority" list. |
| R-03 | FedRAMP Audit Failure | Low | Critical | Implement strict auditing from day one; use a certified Cloudflare GovCloud instance. |
| R-04 | Performance Degradation (Edge) | Medium | Medium | Implement aggressive caching and optimize SQLite query indexing. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required (R-01, R-02).
- **Low/Critical:** Continuous monitoring and compliance checks (R-03).
- **Medium/Medium:** Technical optimization (R-04).

---

## 9. TIMELINE AND PHASES

Project Aqueduct is divided into four distinct phases over a 12-month period.

### Phase 1: Foundation & Migration (Jan 2025 - May 2025)
- **Focus:** Core Rust backend, Database schema implementation, and the Data Import/Export feature.
- **Key Dependency:** Completion of the "God Class" refactor.
- **Milestone 1:** Architecture review complete (**Target: 2025-05-15**).

### Phase 2: Integration & API (May 2025 - July 2025)
- **Focus:** Customer-facing API and Webhook framework.
- **Key Dependency:** Return of the team member on medical leave.
- **Milestone 2:** Stakeholder demo and sign-off (**Target: 2025-07-15**).

### Phase 3: Edge Optimization (July 2025 - Sept 2025)
- **Focus:** Offline-first mode, SQLite edge synchronization, and Performance Benchmarking.
- **Milestone 3:** Performance benchmarks met (**Target: 2025-09-15**).

### Phase 4: Compliance & Launch (Sept 2025 - Dec 2025)
- **Focus:** FedRAMP authorization, final QA gate, and decommissioning of the 4 legacy tools.
- **Goal:** Full production rollout.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per project norms, Iron Bay Technologies does not maintain formal meeting minutes. The following are summaries of critical decisions extracted from Slack threads.*

### Thread 1: #dev-aqueduct (2023-11-12)
**Participants:** Alejandro, Asha, Orin
**Discussion:** Debate over using MongoDB vs. PostgreSQL.
**Decision:** Alejandro decided on PostgreSQL via Hyperdrive. Reason: The fintech nature of the supply chain requires strict ACID compliance for financial transactions. MongoDB's flexibility is not worth the risk of data inconsistency.

### Thread 2: #dev-aqueduct (2023-12-05)
**Participants:** Alejandro, Renzo, Asha
**Discussion:** Handling the 3,000-line 'God Class' that manages Auth, Logging, and Email.
**Decision:** The team agreed not to rewrite it entirely until Phase 2. Instead, they will "wrap" it in a trait-based interface in Rust to decouple it from the new modules, reducing the risk of breaking the system while the team is short-staffed.

### Thread 3: #dev-aqueduct (2024-01-20)
**Participants:** Alejandro, Orin
**Discussion:** The announcement that the primary vendor is ending support for their API.
**Decision:** Orin is tasked with drafting a "Fallback Architecture" document. The team will prioritize a generic "Adapter Pattern" in the backend so that the vendor can be swapped out with minimal changes to the business logic.

---

## 11. BUDGET BREAKDOWN

As the project is **unfunded**, the budget represents "Internal Resource Allocation" (the cost of engineering hours) and infrastructure spend from the existing operational budget.

| Category | Estimated Annual Cost (Internal) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,200,000 | 15 engineers across 5 countries (averaged). |
| **Infrastructure** | $25,000 | Cloudflare Workers, R2, Hyperdrive. |
| **Tools** | $10,000 | IDE licenses, CI/CD tooling, Security scanners. |
| **Contingency** | $50,000 | Buffer for emergency contractor hire if medical leave extends. |
| **Total** | **$1,285,000** | **Bootstrapped Capacity** |

---

## 12. APPENDICES

### Appendix A: The 'God Class' Refactor Plan
The `SystemManager` class is currently a 3,000-line monolith. The refactor will follow these steps:
1. **Extract Email Logic:** Move to `EmailService` module.
2. **Extract Logging:** Implement a structured logging crate (`tracing` in Rust).
3. **Extract Auth:** Move to a dedicated OIDC (OpenID Connect) provider.
4. **Decommission:** Once the three above are independent, the `SystemManager` will be deleted.

### Appendix B: FedRAMP Compliance Checklist
To achieve authorization, the following must be verified by Orin Kim:
- [ ] All data encrypted using FIPS 140-2 validated modules.
- [ ] Multi-factor authentication (MFA) enforced for all admin access.
- [ ] Audit logs retained for 365 days.
- [ ] Boundary protection implemented via Cloudflare WAF.
- [ ] Formal Incident Response Plan (IRP) documented.