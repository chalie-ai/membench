Due to the extreme length requirement of 6,000–8,000 words, this document is presented as a comprehensive, professional Project Specification Document (PSD). It is designed to serve as the "Single Source of Truth" (SSoT) for the development team at Hearthstone Software.

***

# PROJECT SPECIFICATION DOCUMENT: PARAPET (v1.0.4)
**Project Code Name:** Parapet  
**Company:** Hearthstone Software  
**Document Status:** Final / Active  
**Last Updated:** October 24, 2023  
**Classification:** Confidential / PCI DSS Level 1 Sensitive  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Parapet" represents a strategic pivot and a total architectural rebuild of Hearthstone Software’s existing renewable energy e-commerce marketplace. The current legacy platform has suffered a catastrophic failure in user sentiment, characterized by high churn rates, critical performance bottlenecks during peak load, and a user interface that customers have described as "impenetrable." In the renewable energy sector—where ticket sizes are high and regulatory compliance is stringent—trust is the primary currency. The existing system's instability has eroded that trust.

The objective of Parapet is to replace the failing legacy system with a high-performance, resilient, and scalable marketplace that allows users to procure solar panels, wind turbines, and battery storage systems with seamless efficiency. By utilizing a cutting-edge stack (Rust, React, Cloudflare Workers), the project aims to reduce latency by 60% and increase conversion rates by 25%.

### 1.2 ROI Projection and Financial Objectives
With a shoestring budget of $150,000, the project is focused on lean efficiency. The ROI is projected based on the following metrics:
- **Customer Retention:** Increasing the retention rate from 40% to 75% through improved UX and stability.
- **Transaction Volume:** An anticipated 20% increase in Gross Merchandise Value (GMV) within the first six months post-launch due to the removal of checkout frictions.
- **Operational Cost Reduction:** By migrating to an event-driven microservices architecture on Cloudflare Workers, we expect a 30% reduction in monthly cloud infrastructure overhead compared to the legacy monolithic VM approach.
- **Market Positioning:** Closing the gap with the primary competitor who currently holds a 2-month lead in feature parity.

The projected break-even point for the $150k investment is 14 months post-launch, assuming a conservative growth of 500 new active tenants per quarter.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Parapet utilizes a highly distributed architecture designed for global low-latency access. The core philosophy is "Compute at the Edge."

**The Stack:**
- **Frontend:** React 18.x with TypeScript, using Tailwind CSS for styling.
- **Backend:** Rust (Axum framework) for high-performance microservices.
- **Edge Layer:** Cloudflare Workers acting as the routing and execution layer.
- **State/Persistence:** SQLite for edge-level caching and local state, with a centralized PostgreSQL instance for the primary system of record.
- **Communication:** Event-driven asynchronous messaging via Apache Kafka.

### 2.2 ASCII Architecture Diagram
The following diagram describes the request flow from the user to the data persistence layer:

```text
[ User Browser ] <---> [ Cloudflare Edge (React SPA) ]
                               |
                               v
                    [ Cloudflare Workers (Rust WASM) ]
                               |
         -------------------------------------------------------
         |                     |                               |
 [ Auth Service ]      [ Order Service ]              [ Tenant Service ]
 (SAML/OIDC)           (PCI DSS Compliant)            (Data Isolation)
         |                     |                               |
         -------------------------------------------------------
                               |
                               v
                    [ Apache Kafka Event Bus ]
                               |
         -------------------------------------------------------
         |                     |                               |
 [ PDF/CSV Generator ]  [ Sync Service ]             [ Analytics Engine ]
         |                     |                               |
         -------------------------------------------------------
                               |
                               v
                    [ Primary DB (PostgreSQL) ] <---> [ SQLite Edge Cache ]
```

### 2.3 Data Flow and Communication
Communication between microservices is primarily asynchronous. When a user places an order, the `Order Service` publishes an `ORDER_CREATED` event to Kafka. The `Tenant Service` and `Notification Service` consume this event to update tenant-specific quotas and alert the user, respectively. This ensures that a failure in the notification system does not block the checkout process.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: SSO Integration with SAML and OIDC
- **Priority:** Medium | **Status:** Complete
- **Description:** To cater to enterprise renewable energy firms, Parapet must support Single Sign-On (SSO). This allows corporate clients to manage employee access via their own identity providers (IdPs) such as Azure AD, Okta, or Google Workspace.
- **Detailed Specs:**
    - **SAML 2.0 Support:** Implementation of Service Provider (SP) initiated flows. The system must support XML-based metadata exchange.
    - **OIDC Support:** Integration with OpenID Connect for modern OAuth2-based flows, utilizing JWT (JSON Web Tokens) for session management.
    - **User Provisioning:** Just-in-Time (JIT) provisioning is enabled. When a user authenticates via SSO for the first time, the system automatically creates a local user profile mapped to the SAML/OIDC unique identifier.
    - **Mapping:** Custom attribute mapping to allow the IdP to define the user's role (e.g., `Admin`, `Buyer`, `Viewer`) within the Parapet marketplace.
- **Technical Constraint:** All tokens must be encrypted using AES-256 and stored in the encrypted session store.

### 3.2 Feature 2: Multi-Tenant Data Isolation
- **Priority:** Critical (Launch Blocker) | **Status:** Complete
- **Description:** Parapet is a B2B marketplace. Each company (tenant) must have its data completely isolated from others to prevent data leakage—a non-negotiable requirement for legal compliance.
- **Detailed Specs:**
    - **Isolation Strategy:** The system employs a "Shared Database, Separate Schema" approach. Every query executed by the Rust backend must include a `tenant_id` filter.
    - **Context Injection:** A middleware layer in the Rust backend extracts the `tenant_id` from the JWT provided by the SSO service and injects it into the database connection context.
    - **Row-Level Security (RLS):** At the database level, PostgreSQL RLS policies are implemented to ensure that even if a developer forgets a `WHERE` clause, the database will refuse to return rows belonging to a different `tenant_id`.
    - **Shared Infrastructure:** While data is isolated, the compute (Cloudflare Workers) and messaging (Kafka) are shared to minimize costs.
- **Validation:** A "Tenant Leak Test" is integrated into the CI/CD pipeline, attempting to access Tenant B's data using Tenant A's token; the build fails if any data is returned.

### 3.3 Feature 3: Offline-First Mode with Background Sync
- **Priority:** Medium | **Status:** Blocked
- **Description:** Renewable energy technicians often operate in remote areas (wind farms, rural solar arrays) with intermittent connectivity. The app must allow them to draft orders and upload site surveys offline.
- **Detailed Specs:**
    - **Client-Side Storage:** Use of IndexedDB via a wrapper to store pending transactions and state changes.
    - **Conflict Resolution:** A "Last-Write-Wins" strategy for simple fields, and a "Semantic Merge" for complex order documents.
    - **Background Sync:** Implementation of the Service Worker Background Sync API. When the browser detects a regained connection, the worker pushes the queued transactions to the `/sync` endpoint.
    - **User UI Indicators:** A "Connectivity Status" badge in the UI and a "Pending Sync" icon next to items not yet persisted to the server.
- **Blocker:** Current failure in the SQLite-WASM integration causing memory leaks in Chrome on iOS.

### 3.4 Feature 4: PDF/CSV Report Generation & Scheduled Delivery
- **Priority:** High | **Status:** In Review
- **Description:** Enterprise users require monthly procurement reports and tax-compliant invoices in PDF and CSV formats.
- **Detailed Specs:**
    - **Generator Service:** A dedicated Rust microservice that consumes data from the database and uses the `headless-chrome` or `typst` library to render high-fidelity PDFs.
    - **CSV Export:** Streamed CSV generation to handle large datasets (100k+ rows) without overloading the memory of the worker.
    - **Scheduling:** A cron-like trigger system using Cloudflare Workers Scheduled Events. Users can set a frequency (Daily, Weekly, Monthly).
    - **Delivery:** Integration with SendGrid for email delivery, with the report hosted on a short-lived, signed S3 URL.
- **Review Point:** Legal is currently reviewing whether the reports must be digitally signed (e-signature) for compliance in the EU market.

### 3.5 Feature 5: A/B Testing Framework via Feature Flags
- **Priority:** Low | **Status:** Blocked
- **Description:** To avoid the catastrophic feedback of the previous version, the team wants to test new UI elements on a small subset of users before a full rollout.
- **Detailed Specs:**
    - **Feature Flag System:** Integration of a custom toggle system where flags are stored in the SQLite edge cache for millisecond retrieval.
    - **Bucketing Logic:** Users are assigned a consistent hash based on their `user_id`. For example, `hash(user_id) % 100 < 10` puts the user in the 10% test group.
    - **Telemetry:** Every action taken by a user must be tagged with the active version of the feature flag to allow for downstream analysis of conversion rates.
    - **Integration:** The React frontend uses a `useFeatureFlag('flag_name')` hook to conditionally render components.
- **Blocker:** The budget has been exhausted for the current sprint; this is deferred until Milestone 3.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer <JWT>` token.

### 4.1 `POST /auth/sso/callback`
- **Purpose:** Handles the redirection from the SAML/OIDC provider.
- **Request Body:** `{ "saml_response": "string", "relay_state": "string" }`
- **Response:** `200 OK { "token": "jwt_string", "user": { "id": "uuid", "name": "string" } }`

### 4.2 `GET /tenant/profile`
- **Purpose:** Retrieves the current tenant's configuration and branding.
- **Request:** None (Uses `tenant_id` from JWT).
- **Response:** `200 OK { "tenant_id": "uuid", "company_name": "SolarCorp", "tier": "Enterprise" }`

### 4.3 `POST /orders`
- **Purpose:** Places a new order for renewable energy equipment.
- **Request Body:** `{ "items": [{ "sku": "PV-100", "qty": 50 }], "payment_method_id": "pm_123" }`
- **Response:** `201 Created { "order_id": "ord_999", "status": "processing" }`

### 4.4 `GET /orders/{order_id}`
- **Purpose:** Retrieves specific order details.
- **Response:** `200 OK { "order_id": "ord_999", "total": 15000.00, "items": [...] }`

### 4.5 `POST /reports/generate`
- **Purpose:** Manually triggers a PDF/CSV report.
- **Request Body:** `{ "type": "PROCUREMENT_MONTHLY", "format": "PDF", "startDate": "2023-01-01", "endDate": "2023-01-31" }`
- **Response:** `202 Accepted { "job_id": "job_abc", "eta": "30s" }`

### 4.6 `GET /reports/status/{job_id}`
- **Purpose:** Checks the status of a background report generation job.
- **Response:** `200 OK { "status": "completed", "download_url": "https://s3.amazon.../report.pdf" }`

### 4.7 `PUT /sync/batch`
- **Purpose:** The endpoint for the offline-first background sync.
- **Request Body:** `{ "batch_id": "uuid", "operations": [{ "op": "create", "entity": "order", "data": {...} }] }`
- **Response:** `200 OK { "synced_count": 12, "conflicts": 1 }`

### 4.8 `GET /catalog/products`
- **Purpose:** Lists available renewable energy products.
- **Query Params:** `?category=solar&sort=price_asc`
- **Response:** `200 OK { "products": [{ "id": "p1", "name": "Monocrystalline Panel", "price": 200.00 }] }`

---

## 5. DATABASE SCHEMA

The primary database is PostgreSQL 15. All tables utilize UUIDs as primary keys.

### 5.1 Table Definitions

1.  **`tenants`**
    - `id` (UUID, PK): Unique identifier for the company.
    - `name` (VARCHAR): Company name.
    - `domain` (VARCHAR): Custom URL for the tenant.
    - `created_at` (TIMESTAMP): Registration date.
    - `plan_level` (ENUM): 'Basic', 'Professional', 'Enterprise'.

2.  **`users`**
    - `id` (UUID, PK): Unique identifier.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id): Isolation key.
    - `email` (VARCHAR, Unique): User email.
    - `sso_provider_id` (VARCHAR): ID from the IdP.
    - `role` (ENUM): 'Admin', 'User'.

3.  **`products`**
    - `id` (UUID, PK): Product identifier.
    - `sku` (VARCHAR, Unique): Stock Keeping Unit.
    - `name` (VARCHAR): Product name.
    - `description` (TEXT): Detailed specifications.
    - `category` (VARCHAR): e.g., "Solar", "Wind".
    - `unit_price` (DECIMAL): Cost per unit.

4.  **`orders`**
    - `id` (UUID, PK): Order identifier.
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id): Isolation key.
    - `user_id` (UUID, FK $\rightarrow$ users.id): Who placed the order.
    - `status` (ENUM): 'Pending', 'Paid', 'Shipped', 'Cancelled'.
    - `total_amount` (DECIMAL): Total cost.
    - `created_at` (TIMESTAMP).

5.  **`order_items`**
    - `id` (UUID, PK).
    - `order_id` (UUID, FK $\rightarrow$ orders.id).
    - `product_id` (UUID, FK $\rightarrow$ products.id).
    - `quantity` (INT).
    - `price_at_purchase` (DECIMAL).

6.  **`payments`**
    - `id` (UUID, PK).
    - `order_id` (UUID, FK $\rightarrow$ orders.id).
    - `transaction_id` (VARCHAR): Gateway reference.
    - `method` (ENUM): 'CreditCard', 'WireTransfer'.
    - `amount` (DECIMAL).
    - `status` (ENUM): 'Succeeded', 'Failed'.

7.  **`tenant_settings`**
    - `tenant_id` (UUID, PK, FK $\rightarrow$ tenants.id).
    - `currency` (VARCHAR): e.g., "USD", "EUR".
    - `timezone` (VARCHAR).
    - `logo_url` (TEXT).

8.  **`sso_configs`**
    - `tenant_id` (UUID, PK, FK $\rightarrow$ tenants.id).
    - `provider_type` (ENUM): 'SAML', 'OIDC'.
    - `entity_id` (VARCHAR).
    - `certificate` (TEXT): Public key for SAML.

9.  **`report_jobs`**
    - `id` (UUID, PK).
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id).
    - `report_type` (VARCHAR).
    - `status` (ENUM): 'Queued', 'Processing', 'Completed', 'Failed'.
    - `file_path` (TEXT).

10. **`feature_flags`**
    - `flag_key` (VARCHAR, PK): The name of the flag.
    - `is_enabled` (BOOLEAN).
    - `rollout_percentage` (INT): 0-100.
    - `updated_at` (TIMESTAMP).

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `tenants` $\rightarrow$ `orders`, `orders` $\rightarrow$ `order_items`.
- **One-to-One:** `tenants` $\rightarrow$ `tenant_settings`, `tenants` $\rightarrow$ `sso_configs`.
- **Many-to-One:** `order_items` $\rightarrow$ `products`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We utilize a three-tier environment strategy to ensure stability and PCI compliance.

**1. Development (Dev):**
- **Purpose:** Rapid iteration and feature testing.
- **Infrastructure:** Local Docker containers and a shared `dev` Cloudflare Worker namespace.
- **Data:** Mocked data; no real user data is ever present in Dev.
- **Deployment:** Auto-deploy on every push to the `develop` branch via GitHub Actions.

**2. Staging (QA):**
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Infrastructure:** Mirrors Production exactly (Cloudflare Workers, Kafka, PostgreSQL).
- **Data:** Anonymized production snapshots.
- **Deployment:** Manual trigger via GitHub Actions from `develop` to `release` branch.

**3. Production (Prod):**
- **Purpose:** Live customer traffic.
- **Infrastructure:** Multi-region Cloudflare deployment with a managed PostgreSQL cluster on AWS RDS (PCI DSS compliant region).
- **Deployment:** Blue-Green deployment. The "Green" environment is spun up and tested; if successful, traffic is shifted 100% via the Cloudflare DNS layer.

### 6.2 CI/CD Pipeline (GitHub Actions)
The pipeline consists of four stages:
1.  **Lint & Test:** `cargo fmt`, `cargo clippy`, and `npm test`.
2.  **Build:** Rust code is compiled to WASM for Cloudflare Workers.
3.  **Security Scan:** Snyk scan for dependencies and a custom PCI-compliance check for hardcoded secrets.
4.  **Deploy:** Push to Cloudflare Workers via `wrangler` and migrate DB schemas using `diesel` migrations.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust unit tests using the `#[test]` attribute. Focus on business logic, specifically the multi-tenant isolation filters.
- **Frontend:** Jest and React Testing Library for component-level verification.
- **Coverage Requirement:** 80% minimum line coverage for all critical services.

### 7.2 Integration Testing
- **API Testing:** Use of `supertest` or `Insomnia` to verify that endpoints return the correct status codes and payloads.
- **Event Testing:** Mocking Kafka producers and consumers to ensure that an `ORDER_CREATED` event correctly triggers the `Report Generator`.
- **Database Testing:** Running migrations against a temporary PostgreSQL container to ensure schema integrity.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Critical Paths:**
    - User logs in via SSO $\rightarrow$ Navigates to Catalog $\rightarrow$ Adds item to cart $\rightarrow$ Completes Checkout.
    - Admin creates a scheduled report $\rightarrow$ Verifies email delivery.
    - User goes offline $\rightarrow$ Creates order $\rightarrow$ Regains connection $\rightarrow$ Order syncs.

### 7.4 PCI DSS Compliance Testing
Quarterly vulnerability scans and annual penetration tests are mandatory. We utilize a "Tokenization" strategy where the Rust backend never sees the raw credit card number; it only handles tokens provided by the PCI-compliant gateway.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead | High | High | Negotiate timeline extensions with stakeholders; prioritize the "Critical" launch blockers over "Nice-to-haves." | Brigid Fischer |
| R-02 | Team lacks experience in Rust/WASM | Medium | High | Assign Orin Santos as the "Tech Lead" for Rust; implement a weekly internal "knowledge share" session. | Orin Santos |
| R-03 | Budget exhaustion ($150k limit) | High | Critical | Strict scrutiny of every AWS/Cloudflare bill; use of open-source alternatives for internal tooling. | Brigid Fischer |
| R-04 | Legal delay on Data Processing Agreement | Medium | Medium | Maintain aggressive communication with the legal team; proceed with development using "mock" agreements. | Legal Dept |
| R-05 | Lack of structured logging (Tech Debt) | High | Medium | Implement `tracing` crate in Rust immediately to replace `stdout` logging. | Anouk Kim |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required.
- **High:** Regular monitoring and active mitigation.
- **Medium:** Manage via standard project procedures.

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project is divided into three primary milestones over a 16-month window.

### Phase 1: Foundation (October 2023 - May 2026)
- **Focus:** Architecture setup, SSO, and Multi-tenancy.
- **Dependencies:** Legal approval of Data Processing Agreement must be finalized before Milestone 1.
- **Deliverable:** Internal Alpha release (2026-05-15).

### Phase 2: Feature Build-out (May 2026 - July 2026)
- **Focus:** Order management, PDF/CSV generation, and Catalog.
- **Dependencies:** Feature 2 (Multi-tenancy) must be 100% verified.
- **Deliverable:** MVP Feature-Complete (2026-07-15).

### Phase 3: Optimization & Hardening (July 2026 - September 2026)
- **Focus:** Performance tuning, load testing, and finalizing the Offline-first mode.
- **Dependencies:** Successful completion of MVP feature set.
- **Deliverable:** Performance Benchmarks Met (2026-09-15).

---

## 10. MEETING NOTES

### Meeting 1: Technical Stack Alignment
**Date:** 2023-11-02  
**Attendees:** Brigid Fischer, Orin Santos, Mosi Santos, Anouk Kim  
**Minutes:**
- Brigid expressed concern over the "shoestring" budget. The team agreed that using Cloudflare Workers would significantly reduce server costs compared to traditional EC2 instances.
- Orin raised a point about the team's lack of Rust experience. He suggested a "learning sprint" for Anouk.
- **Decision:** The stack is finalized as Rust/React/SQLite/Kafka.
- **Action Item:** Orin to set up the initial GitHub repository and CI/CD boilerplate. (Owner: Orin Santos)

### Meeting 2: Data Isolation Strategy
**Date:** 2023-12-15  
**Attendees:** Brigid Fischer, Orin Santos, Mosi Santos  
- Mosi presented a scenario where a developer might forget a `WHERE tenant_id = ?` clause in a complex query.
- Orin proposed using PostgreSQL Row-Level Security (RLS) as a secondary safety net.
- **Decision:** Implement RLS on all tables containing `tenant_id`.
- **Action Item:** Mosi to write a set of "leak tests" for the QA suite to verify isolation. (Owner: Mosi Santos)

### Meeting 3: Offline Mode Blocker Review
**Date:** 2024-03-10  
**Attendees:** Orin Santos, Anouk Kim, Mosi Santos  
- Anouk reported that the SQLite-WASM integration is crashing on iOS Safari due to memory limits.
- The team discussed whether to move the state to IndexedDB instead.
- **Decision:** Feature 3 is officially marked as "Blocked" until a stable WASM memory management strategy is found.
- **Action Item:** Anouk to research the `sql.js` alternative for smaller datasets. (Owner: Anouk Kim)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 USD (Fixed)

| Category | Allocated Amount | Percentage | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $110,000 | 73.3% | Distributed team of 15; primarily contract-based. |
| **Infrastructure** | $15,000 | 10.0% | Cloudflare Workers, AWS RDS, Kafka Managed Cluster. |
| **Tools/Licensing** | $10,000 | 6.7% | GitHub Enterprise, Snyk, SendGrid, JetBrains IDEs. |
| **Contingency** | $15,000 | 10.0% | Reserved for emergency fixes or legal consulting. |

**Budgetary Constraint:** Every expense over $500 requires a signed approval from Brigid Fischer.

---

## 12. APPENDICES

### Appendix A: Performance Benchmarks
To meet Milestone 3, the following metrics must be achieved:
- **P99 Latency:** All API responses must be under 200ms globally.
- **Throughput:** The system must handle 5,000 concurrent requests per second without degradation.
- **Cold Start:** Cloudflare Worker cold start must be under 50ms.
- **Sync Speed:** Offline synchronization of 100 items must complete in under 2 seconds upon reconnection.

### Appendix B: PCI DSS Level 1 Implementation Details
Since Parapet processes credit card data directly, the following strict rules apply:
- **Encryption:** All data in transit must use TLS 1.3.
- **Storage:** No raw PAN (Primary Account Number) or CVV may be stored in the PostgreSQL database. Only the gateway token is stored.
- **Access Control:** Access to the Production database is restricted to the Project Lead and Senior Backend Engineer via a bastion host with MFA.
- **Logging:** While the system currently lacks structured logging, the "Audit Log" for payment transactions is stored in a separate, read-only Immutable Ledger to satisfy auditors.