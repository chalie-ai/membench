# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Active / Development  
**Company:** Verdant Labs  
**Classification:** Confidential – Internal R&D  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Glacier is a strategic moonshot initiative by Verdant Labs designed to disrupt the healthcare e-commerce landscape. Unlike standard retail marketplaces, Glacier is engineered as a high-performance, specialized exchange for healthcare providers, medical device distributors, and pharmaceutical entities. The project aims to streamline the procurement of critical medical supplies through a modernized, real-time interface that reduces friction in the B2B healthcare supply chain.

**Business Justification**  
The healthcare procurement sector is currently dominated by legacy ERP systems and fragmented manual ordering processes. Verdant Labs identifies a significant gap in the market for a "lean" marketplace that allows for rapid onboarding of niche medical suppliers while providing buyers with real-time inventory transparency. While the ROI is currently classified as "uncertain" due to the experimental nature of the R&D phase, the project carries strong executive sponsorship from the Board of Directors. The strategic goal is not immediate profitability, but the acquisition of market data and the establishment of a technical footprint within the healthcare logistics space.

**ROI Projection**  
The financial model for Glacier is based on a transaction-fee architecture (commission per order) and a tiered subscription model for "Premium Suppliers" who require advanced reporting and API access. 
- **Year 1:** Expected net loss due to aggressive R&D and infrastructure setup.
- **Year 2:** Break-even point targeted via the acquisition of 10,000 Monthly Active Users (MAU).
- **Year 3:** Projected positive ROI of 12-15% based on a capture rate of 2% of the regional mid-market medical supply spend.

**Project Constraints**  
The project operates with a hard budget of $800,000 over a 6-month development cycle. The team is intentionally kept lean (4 members) to maintain agility, although this has introduced significant "bus factor" risks and internal friction. The success of the project depends on the ability to scale the system to 10x current capacity without an increase in the allocated infrastructure budget.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Glacier utilizes a modern, functional programming stack designed for high concurrency and fault tolerance, essential for the real-time nature of healthcare supply chains.

- **Language/Framework:** Elixir 1.15 / Phoenix 1.14.
- **Frontend:** Phoenix LiveView (for real-time state synchronization without full page reloads).
- **Database:** PostgreSQL 15 (Relational data, JSONB for flexible product attributes).
- **Hosting/Deployment:** Fly.io (Global distribution and regional proximity to healthcare hubs).
- **Feature Management:** LaunchDarkly (For canary releases and decoupling deployment from release).
- **Communication:** PubSub for real-time notifications and order updates.

### 2.2 Architectural Pattern
Glacier follows a traditional three-tier architecture to ensure clear separation of concerns and ease of maintenance for the small team:

1.  **Presentation Tier:** LiveView components rendering dynamic HTML via WebSockets.
2.  **Business Logic Tier (The "Contexts"):** Elixir modules implementing the domain logic (e.g., `Ordering`, `Inventory`, `UserManagement`).
3.  **Data Tier:** PostgreSQL for persistent storage, utilizing Ecto as the database wrapper.

### 2.3 System Topology (ASCII Description)
```text
[Client Browser] <--- WebSocket (LiveView) ---> [Fly.io Edge Load Balancer]
                                                        |
                                                        v
                                          [Phoenix Application Cluster]
                                          /             |             \
             (Feature Flags) <--- [LaunchDarkly]   [Business Logic]  ---> [External APIs]
                                                         |                      |
                                                         v                      v
                                            [PostgreSQL Cluster] <---> [Integration Partner API]
                                            (Primary / Replica)
```

### 2.4 Infrastructure Philosophy
The architecture leverages Elixir’s BEAM VM to handle thousands of concurrent connections per node. To manage the "10x capacity" requirement, the system uses horizontal scaling via Fly.io. However, because the budget is fixed, the team is focusing on optimizing database queries and utilizing PostgreSQL indexes to avoid the need for expensive managed caching layers like Redis in the early phases.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API (Priority: Medium | Status: Complete)
**Specification:**  
The Glacier API provides a programmatic interface for healthcare providers to integrate their existing Procurement Software (ERP) directly with the marketplace. The API is built on a RESTful architecture, utilizing JSON for request and response bodies.

**Key Components:**
- **Versioning:** The API uses URI versioning (e.g., `/api/v1/...`). This ensures that legacy integrations do not break when the business logic evolves. Version 1.0 is the current stable release.
- **Sandbox Environment:** A complete mirror of the production environment (`sandbox-api.glacier.verdant.io`) is provided. This environment uses a separate PostgreSQL database populated with mocked healthcare data, allowing partners to test order flows without triggering real financial transactions.
- **Authentication:** API Key-based authentication via headers (`X-Glacier-API-Key`).

**Functional Requirements:**
- Support for bulk product uploads via the `/products` endpoint.
- Real-time order status polling.
- Rate limiting: 1,000 requests per hour per API key to prevent system exhaustion.

### 3.2 Notification System (Priority: Critical | Status: In Review)
**Specification:**  
The Notification System is a launch-blocker. In the healthcare industry, delays in supply alerts (e.g., "Critical Shortage of Surgical Gauze") can have clinical implications. The system must be multi-modal and reliable.

**Delivery Channels:**
- **Email:** Handled via SendGrid. Used for formal invoices, account registrations, and weekly digests.
- **SMS:** Handled via Twilio. Used for high-priority order alerts and 2FA.
- **In-App:** Managed via Phoenix PubSub and LiveView. Real-time toast notifications appearing in the user dashboard.
- **Push:** Mobile push notifications for registered providers using WebPush protocols.

**Logic Flow:**
The system uses a "Notification Dispatcher" pattern. When an event occurs (e.g., `OrderPlaced`), the dispatcher checks the user's preference matrix in the database to determine which channels to trigger. If a notification is marked as "Urgent," the system overrides preferences and sends both an SMS and an In-App alert.

**Technical Requirements:**
- Queueing: Use of `Oban` for background job processing to ensure notifications do not block the main request thread.
- Retry Logic: Exponential backoff for failed SMS/Email deliveries.

### 3.3 PDF/CSV Report Generation (Priority: Medium | Status: In Progress)
**Specification:**  
Healthcare administrators require detailed auditing and spending reports for compliance. Glacier provides a reporting engine that generates snapshot documents of procurement activity.

**Capabilities:**
- **PDF Generation:** Using the `PdfGenerator` (Chromium-based) to create formatted invoices and monthly spend summaries.
- **CSV Generation:** Streamed output using `csv` Elixir library to handle large datasets (up to 100k rows) without crashing the VM.
- **Scheduled Delivery:** A cron-like system (implemented via Oban) that allows users to schedule reports (Daily, Weekly, Monthly) to be emailed to specific stakeholders.

**Delivery Pipeline:**
1. User defines parameters (Date range, Category, Supplier).
2. System triggers a background job.
3. Report is generated and uploaded to an S3-compatible bucket.
4. A signed URL is emailed to the user or delivered via the notification system.

### 3.4 Offline-First Mode with Background Sync (Priority: Low | Status: Complete)
**Specification:**  
Medical staff often operate in "dead zones" (e.g., shielded radiology wings). Glacier implements a "Local-First" approach for order drafting and inventory checking.

**Implementation Details:**
- **Client-Side Storage:** Uses IndexedDB via a small JavaScript wrapper to cache product catalogs and draft orders.
- **Sync Engine:** A custom reconciliation algorithm. When the connection is restored, the system compares the local timestamp with the server timestamp.
- **Conflict Resolution:** "Last Write Wins" (LWW) is applied for draft orders, while "Server Authoritative" is used for actual stock levels to prevent over-selling.

**User Experience:**
The UI displays a "Syncing..." indicator when offline and a "Synced" checkmark once the background process completes. Users can continue to add items to their cart while offline.

### 3.5 Advanced Search with Faceted Filtering (Priority: Low | Status: In Progress)
**Specification:**  
Given the vast number of SKUs in medical procurement, a basic keyword search is insufficient. This feature provides an enterprise-grade discovery experience.

**Technical Approach:**
- **Full-Text Indexing:** Utilizing PostgreSQL `tsvector` and `tsquery` for high-performance text search across product names and descriptions.
- **Faceted Filtering:** Dynamic sidebars allowing users to filter by:
    - Manufacturer (e.g., Medtronic, 3M).
    - Regulatory Class (e.g., Class I, II, III).
    - Price Range.
    - Delivery Speed.
- **Indexing Strategy:** GIN (Generalized Inverted Index) on the `search_vector` column to ensure sub-100ms response times.

**Current Status:**
The basic full-text search is functional; the faceted aggregation logic is currently being optimized to reduce database load.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require `Content-Type: application/json` and an `X-Glacier-API-Key`.

### 4.1 GET `/products`
**Description:** Retrieve a list of available medical supplies.
- **Query Params:** `q` (search term), `category` (filter), `page` (pagination).
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "prod_99", "name": "Sterile Scalpel #10", "price": 12.50, "stock": 450 }
  ],
  "meta": { "total": 1200, "page": 1 }
}
```

### 4.2 POST `/orders`
**Description:** Create a new procurement order.
- **Request Body:**
```json
{
  "supplier_id": "sup_442",
  "items": [
    { "sku": "SCALPEL-10", "quantity": 50 }
  ],
  "shipping_address_id": "addr_11"
}
```
- **Response (201 Created):**
```json
{ "order_id": "ord_7788", "status": "pending", "total": 625.00 }
```

### 4.3 GET `/orders/{id}`
**Description:** Fetch detailed status of a specific order.
- **Response (200 OK):**
```json
{
  "id": "ord_7788",
  "status": "shipped",
  "tracking_number": "GLC-123456789",
  "estimated_delivery": "2026-05-10T14:00:00Z"
}
```

### 4.4 PATCH `/orders/{id}/cancel`
**Description:** Request cancellation of an order (only if status is 'pending').
- **Response (200 OK):** `{ "status": "cancelled", "refund_processed": true }`

### 4.5 GET `/inventory/check`
**Description:** Real-time stock check for a list of SKUs.
- **Request Body:** `{ "skus": ["SCALPEL-10", "GAUZE-2X2"] }`
- **Response (200 OK):**
```json
{
  "results": [
    { "sku": "SCALPEL-10", "available": 400 },
    { "sku": "GAUZE-2X2", "available": 0 }
  ]
}
```

### 4.6 POST `/reports/generate`
**Description:** Trigger an on-demand PDF/CSV report.
- **Request Body:** `{ "type": "spend_summary", "format": "pdf", "range": "last_30_days" }`
- **Response (202 Accepted):** `{ "job_id": "job_abc123", "status": "processing" }`

### 4.7 GET `/reports/download/{job_id}`
**Description:** Retrieve the generated file via a signed URL.
- **Response (200 OK):** `{ "url": "https://s3.glacier.io/reports/xyz.pdf", "expires_at": "..." }`

### 4.8 POST `/auth/refresh`
**Description:** Refresh the session token for the API.
- **Request Body:** `{ "refresh_token": "token_xyz" }`
- **Response (200 OK):** `{ "access_token": "new_token_123", "expires_in": 3600 }`

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15. All tables use `UUID` as primary keys for better security and distributed scalability.

### 5.1 Table Definitions

1.  **`users`**: Core identity table.
    - `id` (UUID, PK), `email` (Unique), `password_hash`, `role` (admin/provider/supplier), `created_at`.
2.  **`profiles`**: Extended user data.
    - `id` (UUID, PK), `user_id` (FK), `full_name`, `phone_number`, `address_id` (FK).
3.  **`organizations`**: Healthcare facilities or supply companies.
    - `id` (UUID, PK), `name`, `tax_id`, `org_type` (Hospital/Clinic/Distributor).
4.  **`organization_members`**: Link table for users and orgs.
    - `org_id` (FK), `user_id` (FK), `permission_level` (Owner/Buyer/Viewer).
5.  **`products`**: The catalog of medical items.
    - `id` (UUID, PK), `supplier_id` (FK), `sku` (Unique), `name`, `description`, `price`, `category_id` (FK), `search_vector` (tsvector).
6.  **`inventory`**: Real-time stock tracking.
    - `product_id` (FK, PK), `quantity_on_hand`, `reserved_quantity`, `reorder_threshold`.
7.  **`orders`**: Transactional records.
    - `id` (UUID, PK), `buyer_id` (FK), `supplier_id` (FK), `status` (pending/paid/shipped/delivered), `total_amount`, `created_at`.
8.  **`order_items`**: Line items for each order.
    - `id` (UUID, PK), `order_id` (FK), `product_id` (FK), `quantity`, `unit_price`.
9.  **`notifications`**: Log of all alerts sent.
    - `id` (UUID, PK), `user_id` (FK), `channel` (email/sms/push), `message`, `is_read` (boolean), `sent_at`.
10. **`report_jobs`**: Tracking for asynchronous reports.
    - `id` (UUID, PK), `user_id` (FK), `type`, `status` (queued/processing/complete), `file_url`.

### 5.2 Relationships
- **One-to-Many:** `organizations` $\rightarrow$ `users` (via `organization_members`).
- **One-to-Many:** `suppliers` $\rightarrow$ `products`.
- **Many-to-Many:** `orders` $\leftrightarrow$ `products` (via `order_items`).
- **One-to-One:** `products` $\leftrightarrow$ `inventory`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Glacier utilizes three distinct environments to ensure stability and testing rigor.

| Environment | URL | Purpose | Data Source | Deployment Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Dev** | `dev.glacier.io` | Active development, feature testing. | Mock/Seed Data | Continuous Deployment (CI/CD) |
| **Staging** | `stg.glacier.io` | Pre-production QA, UAT. | Sanity-scrubbed Prod Data | Manual Trigger (GitHub Actions) |
| **Prod** | `app.glacier.io` | Live customer traffic. | Live Production Data | Canary Releases (Fly.io) |

### 6.2 Deployment Pipeline
1.  **Build Phase:** GitHub Actions compiles the Elixir releases into a Docker image.
2.  **Testing Phase:** Unit and Integration tests must pass 100% before the image is pushed to the registry.
3.  **Deployment Phase:**
    - **Canary Release:** The new version is deployed to 5% of the nodes.
    - **Monitoring:** Sentry and Fly.io metrics are monitored for 30 minutes.
    - **Full Rollout:** If error rates remain below 0.1%, the remaining 95% of nodes are updated.
4.  **Feature Flags:** High-risk features (like the new Search engine) are wrapped in **LaunchDarkly** flags. This allows the team to disable a feature instantly without a full rollback.

### 6.3 Infrastructure Management
- **Cluster:** Fly.io distributed nodes across `us-east-1` and `eu-west-1`.
- **Persistence:** Managed PostgreSQL with automated daily backups and point-in-time recovery (PITR).
- **Networking:** Private VPC for database communication; only the load balancer is exposed to the public internet.

---

## 7. TESTING STRATEGY

Given the critical nature of healthcare supplies, the testing strategy is rigorous, focusing on data integrity and system availability.

### 7.1 Unit Testing
- **Scope:** Individual functions, Ecto schemas, and business logic modules.
- **Tooling:** `ExUnit`.
- **Requirement:** 80% code coverage. Focus on "edge cases" (e.g., negative inventory, zero-dollar orders).

### 7.2 Integration Testing
- **Scope:** Testing the interaction between the Phoenix controllers, the business logic (Contexts), and the PostgreSQL database.
- **Approach:** Use of `DataCase` to seed a temporary database, perform a series of actions (e.g., place order $\rightarrow$ check inventory $\rightarrow$ verify notification), and assert the final state.
- **External APIs:** All external partners (Twilio, SendGrid) are mocked using `Mox` to avoid hitting real APIs during test runs.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from the browser.
- **Tooling:** `Wallaby` (for LiveView interactions).
- **Critical Paths:**
    1. User login $\rightarrow$ Product Search $\rightarrow$ Add to Cart $\rightarrow$ Checkout $\rightarrow$ Order Confirmation.
    2. Supplier Login $\rightarrow$ Inventory Update $\rightarrow$ Notification Trigger.
    3. API Key generation $\rightarrow$ Sandbox Order $\rightarrow$ Report Generation.

### 7.4 Performance Testing
- **Load Testing:** Using `K6` to simulate 10x current capacity (target: 100,000 concurrent requests).
- **Stress Testing:** Identifying the breaking point of the PostgreSQL connection pool to determine the maximum possible throughput per node.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Performance requirements (10x capacity) exceed current budget. | High | High | Hire a specialized contractor to optimize the DB and reduce the "bus factor" of the core team. |
| **R-02** | Integration partner API is undocumented and buggy. | High | Medium | Dedicate a sprint to "reverse engineering" the API; document all workarounds in a shared Wiki. |
| **R-03** | Team dysfunction leads to missed deadlines. | High | High | CTO to mediate design disagreements; move to a more structured ticket-based system. |
| **R-04** | Data breach of sensitive healthcare info. | Low | Critical | Quarterly penetration testing and strict role-based access control (RBAC). |
| **R-05** | Technical debt (lack of structured logging). | Medium | Medium | Implement `Logger` structured JSON output in the next sprint to eliminate `stdout` reading. |

**Impact Matrix:**
- **Critical:** System failure or legal liability.
- **High:** Major feature delay or significant performance degradation.
- **Medium:** Workaround exists, but efficiency is reduced.
- **Low:** Minor annoyance, no impact on delivery.

---

## 9. TIMELINE & MILESTONES

The project follows a compressed 6-month timeline with a hard launch date.

### 9.1 Phase Breakdown

**Phase 1: Foundation & API (Month 1-2)**
- *Focus:* Core database schema, API v1, Sandbox setup.
- *Dependency:* Finalization of organization types.
- *Outcome:* API Complete.

**Phase 2: Critical Communications (Month 3)**
- *Focus:* Notification system, Oban worker setup, Twilio/SendGrid integration.
- *Dependency:* User preference matrix design.
- *Outcome:* Notification System In Review.

**Phase 3: Reporting & Advanced Features (Month 4)**
- *Focus:* PDF/CSV generation, Full-text search, Faceted filtering.
- *Dependency:* Stable data in the `products` table.
- *Outcome:* Reports In Progress.

**Phase 4: Stability & Optimization (Month 5)**
- *Focus:* Offline-first sync, Performance tuning, Pen-testing.
- *Dependency:* E2E test completion.
- *Outcome:* MVP Feature-Complete.

**Phase 5: Launch & Post-Mortem (Month 6)**
- *Focus:* Canary releases, Production monitoring, Architecture review.
- *Dependency:* Executive sign-off.
- *Outcome:* Production Launch.

### 9.2 Key Milestone Dates
- **Milestone 1 (MVP Feature-Complete):** 2026-04-15
- **Milestone 2 (Production Launch):** 2026-06-15
- **Milestone 3 (Architecture Review Complete):** 2026-08-15

---

## 10. MEETING NOTES

### Meeting 1: Technical Sync (2025-11-12)
*Attendees: Callum Santos, Rosa Jensen, Amara Gupta, Yael Kim*
- API sandbox is finally working.
- Rosa hates the current layout for the order page.
- Callum says "just make it work."
- Amara concerned about the lack of logging in prod.
- Yael mentions the partner API is returning 500s for no reason.
- Action: Yael to document the bugs.

### Meeting 2: Sprint Planning (2025-12-05)
*Attendees: Callum Santos, Rosa Jensen, Amara Gupta, Yael Kim*
- Notifications are the priority.
- Design disagreement: Rosa wants a modal, Callum wants a toast.
- Discussion stalled. No decision made.
- Budget for a contractor approved to help with the 10x scaling issue.
- Amara warns that the "offline-first" mode might create race conditions.

### Meeting 3: Executive Review (2026-01-20)
*Attendees: Callum Santos, Executive Sponsor*
- ROI is still "uncertain" but sponsorship remains strong.
- 10k MAU is the target for 6 months post-launch.
- Concern over team friction.
- Callum insists the project is on track for April MVP.
- Decision: Quarterly pen-testing is mandatory.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000  
**Duration:** 6 Months

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $450,000 | Salaries for Callum, Rosa, Amara, and benefits. |
| **Personnel (Contractor)** | $120,000 | Specialized Elixir/Postgres contractor for scaling and bus-factor reduction. |
| **Infrastructure (Fly.io)** | $60,000 | Compute, managed DB, and bandwidth across 3 environments. |
| **Software Tools** | $30,000 | LaunchDarkly, SendGrid, Twilio, Sentry, GitHub Enterprise. |
| **Security Audits** | $40,000 | Quarterly external penetration testing (4 x $10k). |
| **Contingency** | $100,000 | Reserved for emergency scaling or partner API integration failures. |

---

## 12. APPENDICES

### Appendix A: Structured Logging Proposal
To resolve the current technical debt where debugging requires reading `stdout`, the team will migrate to `Logger.set_backend` with a JSON formatter.
- **Fields to include:** `request_id`, `user_id`, `timestamp`, `severity`, `module`, `message`.
- **Destination:** Logs will be streamed from Fly.io to a centralized log aggregator (e.g., Papertrail or Datadog) for searchable indexing.

### Appendix B: Integration Partner Workarounds
The partner API (MediSupply Global) has several known issues identified by Yael Kim:
1.  **Endpoint `/stock`:** Frequently returns `200 OK` but with an empty body. Workaround: Implement a retry mechanism that checks for `content-length == 0`.
2.  **Authentication:** Tokens expire every 12 hours regardless of the `expires_in` field. Workaround: Forced refresh every 11 hours.
3.  **Data Consistency:** The `price` field is sometimes sent as a string with currency symbols (e.g., "$12.50"). Workaround: Custom regex parser implemented in the `MediSupplyClient` module to strip non-numeric characters.