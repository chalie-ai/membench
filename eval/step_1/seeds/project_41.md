# PROJECT SPECIFICATION DOCUMENT: PROJECT DELPHI
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Project Owner:** Coral Reef Solutions  
**Status:** Active/In-Development  
**Classification:** Confidential – PCI DSS Level 1 Compliant

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Delphi is a strategic platform modernization initiative undertaken by Coral Reef Solutions to transition its core e-commerce marketplace, specializing in the food and beverage industry, from a legacy monolithic architecture to a scalable microservices-oriented ecosystem. The primary objective is to eliminate technical debt and scale the platform to handle an increasing volume of high-frequency transactions while maintaining the rigorous security standards required for food-grade logistics and financial transactions.

The modernization effort is structured as an 18-month transition. The "Delphi" phase represents the foundational pivot, moving the current Ruby on Rails monolith toward a CQRS (Command Query Responsibility Segregation) pattern with event sourcing for audit-critical domains. This ensures that every change to a food order or financial transaction is immutable and traceable, a non-negotiable requirement for the industry's regulatory landscape.

### 1.2 Business Justification
The legacy system has reached a "critical mass" of complexity where the cost of maintaining the monolith outweighs the cost of rebuilding. Current deployment cycles are sluggish, and the lack of data isolation between tenants creates a risk of data leakage. In the food and beverage sector, where supply chain transparency and vendor isolation are paramount, the ability to offer multi-tenant isolation on shared infrastructure is a competitive necessity.

Furthermore, the decision to process credit card data directly necessitates PCI DSS Level 1 compliance. By modernizing the architecture, Coral Reef Solutions can implement tighter security controls at the service level rather than the application level, reducing the scope of PCI audits and lowering the risk of catastrophic data breaches.

### 1.3 ROI Projection
With a total budget allocation of $1.5M, the projected Return on Investment (ROI) is calculated based on three primary drivers:
1. **Operational Efficiency:** Reduction in deployment-related downtime and hotfix emergency patches (currently averaging 12 hours/month) by implementing a strict weekly release train.
2. **Market Expansion:** The ability to onboard enterprise-level food distributors who require dedicated data isolation, projected to increase Monthly Recurring Revenue (MRR) by 22% within the first year post-MVP.
3. **Risk Mitigation:** Avoiding potential PCI non-compliance fines, which can range from $5,000 to $100,000 per month.

The projected break-even point for the $1.5M investment is 22 months post-launch, with a projected 3-year NPV (Net Present Value) of $4.2M.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
The Delphi architecture prioritizes simplicity and developer velocity. The current stack consists of:
- **Language/Framework:** Ruby on Rails (v7.1)
- **Database:** MySQL 8.0 (Amazon RDS)
- **Hosting:** Heroku Private Spaces (for PCI compliance and dedicated networking)
- **Cache/Queue:** Redis (Heroku Data for Redis)
- **Search Engine:** Elasticsearch (Self-hosted on AWS EC2 for faceted filtering)

### 2.2 Architectural Pattern: CQRS and Event Sourcing
To handle audit-critical domains (Payments, Order Fulfillment, Inventory), Delphi employs Command Query Responsibility Segregation (CQRS). 

- **Command Side:** Handles writes. When a user places an order, a "Command" is issued. Instead of updating a row in a table, the system appends an event to an `event_store` table (e.g., `OrderCreated`, `PaymentAuthorized`).
- **Query Side:** Handles reads. An asynchronous projector listens to the event stream and updates a "Read Model" (a denormalized MySQL table) optimized for fast retrieval.

This ensures a perfect audit trail. If a dispute arises regarding a food shipment, the team can replay events to see exactly when a status changed.

### 2.3 Architecture Diagram (ASCII Representation)
```text
[ Client: Web/Mobile ] 
       |
       v
[ Heroku Load Balancer / SSL Termination ]
       |
       v
[ Rails Monolith (Application Layer) ]
       |
       +---[ Command Path ]---> [ Event Store (MySQL) ] ---> [ Event Bus (Redis) ]
       |                                                            |
       |                                                            v
       +---[ Query Path ] <--- [ Read Model (MySQL) ] <--- [ Projections/Workers ]
       |
       +---[ Integration Path ] ---> [ External API Partners ] (Risk: Buggy/Undocumented)
       |
       +---[ Search Path ] ---------> [ Elasticsearch ] (Faceted Indexing)
```

### 2.4 Deployment Strategy
Delphi utilizes a **Weekly Release Train**. 
- **Schedule:** All code merged by Thursday 00:00 UTC is deployed on Friday 09:00 UTC.
- **The "No Hotfix" Rule:** No code enters production outside the release train unless it is a P0 security vulnerability approved by Maren Liu. This prevents "drift" between environments and ensures QA can validate the full release candidate.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Status: Complete)
**Priority:** High | **Requirement ID:** FEAT-002

**Description:** 
The platform must ensure that data belonging to different food vendors (tenants) is logically isolated, even though they share the same physical database and infrastructure. This prevents "cross-talk" where Vendor A might accidentally see Vendor B's customer list.

**Technical Implementation:**
The system implements a "Row-Level Isolation" strategy. Every table in the database (with the exception of global config tables) contains a `tenant_id` foreign key. 
- **Scoped Queries:** A global `Current.tenant` object is set during the request lifecycle via a middleware that identifies the tenant from the subdomain or API key.
- **Default Scopes:** All ActiveRecord models include a `default_scope` that automatically appends `WHERE tenant_id = ?` to every query.
- **Validation:** A secondary guard layer is implemented in the Controller level to ensure that any ID passed in a URL (e.g., `/orders/123`) actually belongs to the `Current.tenant`.

**Acceptance Criteria:**
- A user logged into Tenant A cannot access any resource belonging to Tenant B by manually changing the ID in the URL.
- Database migrations must enforce the presence of `tenant_id` on all new business-logic tables.
- Performance overhead for the default scope must be less than 5ms per query.

### 3.2 Two-Factor Authentication with Hardware Key Support (Status: In Design)
**Priority:** Medium | **Requirement ID:** FEAT-001

**Description:** 
Due to the sensitivity of PCI DSS Level 1 data, standard password authentication is insufficient. Delphi requires 2FA for all administrative and vendor accounts, specifically supporting FIDO2/WebAuthn hardware keys (e.g., YubiKey) in addition to TOTP (Time-based One-Time Passwords).

**Technical Implementation:**
- **WebAuthn Integration:** Integration with the `webauthn` Ruby gem to handle challenge-response authentication.
- **Authentication Flow:** 
    1. User submits username/password.
    2. System identifies if 2FA is enabled.
    3. System sends a challenge to the browser.
    4. User taps the hardware key; the browser sends the signed challenge back to the server.
    5. Server verifies the signature against the stored public key.
- **Recovery:** Generation of 10 one-time use backup codes, stored hashed in the database.

**Acceptance Criteria:**
- Support for YubiKey 5 series and Google Titan keys.
- Fallback to TOTP (Google Authenticator/Authy) if a hardware key is unavailable.
- 2FA must be mandatory for all users with "Admin" or "Billing" roles.

### 3.3 Data Import/Export with Format Auto-Detection (Status: In Progress)
**Priority:** Medium | **Requirement ID:** FEAT-005

**Description:** 
Food vendors often migrate from legacy spreadsheets. Delphi must allow users to upload product lists in CSV, JSON, and XML formats. The system must automatically detect the format and map the columns to the internal schema.

**Technical Implementation:**
- **Detection Engine:** A MIME-type checker combined with a "magic byte" analysis to determine the file format.
- **Mapping Layer:** A "Schema Mapper" that uses fuzzy string matching (Levenshtein distance) to suggest mappings between the uploaded header (e.g., "Prod_Name") and the system field ("product_name").
- **Background Processing:** Large imports are handled via Sidekiq jobs to prevent request timeouts. Files are uploaded to S3, and the processing happens asynchronously.
- **Validation:** A pre-flight check validates data types (e.g., ensuring the "Price" column contains numeric values) before committing to the database.

**Acceptance Criteria:**
- Correct detection of `.csv`, `.json`, and `.xml` files.
- Ability to map at least 50,000 rows within 2 minutes of processing.
- Error report generation listing exactly which rows failed and why.

### 3.4 Advanced Search with Faceted Filtering (Status: In Progress)
**Priority:** Low | **Requirement ID:** FEAT-004

**Description:** 
Buyers need to filter food products by category (e.g., "Organic," "Gluten-Free"), price range, and vendor rating. Standard SQL `LIKE` queries are insufficient for the expected catalog size.

**Technical Implementation:**
- **Elasticsearch Integration:** Implementation of a search cluster. Data is synced from MySQL to Elasticsearch using a "Search Indexer" worker.
- **Faceted Search:** Utilizing Elasticsearch "Aggregations" to calculate the count of products per filter category in real-time.
- **Full-Text Indexing:** Implementation of n-gram tokenization to allow for partial matches (e.g., searching "apple" finds "applesauce").
- **Ranking:** A custom scoring algorithm that boosts products based on "Popularity" and "Vendor Rating."

**Acceptance Criteria:**
- Search results returned in under 200ms for a catalog of 1 million items.
- Facets update dynamically as filters are selected.
- Support for "did you mean?" suggestions for misspelled queries.

### 3.5 Automated Billing and Subscription Management (Status: In Review)
**Priority:** Low | **Requirement ID:** FEAT-003

**Description:** 
The marketplace requires a system to bill vendors based on their subscription tier (Basic, Pro, Enterprise) and a percentage-based transaction fee on sales.

**Technical Implementation:**
- **Subscription Engine:** A state machine managing subscription statuses (`active`, `past_due`, `canceled`).
- **Billing Cycles:** A daily cron job (Sidekiq-scheduler) that identifies accounts due for billing.
- **Invoice Generation:** Automated PDF generation of invoices using the `wicked_pdf` gem, emailed to the tenant administrator.
- **Payment Gateway:** Direct integration with the internal PCI-compliant vault to trigger charges against stored tokens.

**Acceptance Criteria:**
- Automated monthly billing triggers on the anniversary of sign-up.
- Automatic account suspension if a payment is failed for 3 consecutive attempts.
- Support for pro-rated upgrades between tiers.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a `X-Tenant-ID` header and a Bearer Token for authentication.

### 4.1 Order Management
**Endpoint:** `POST /api/v1/orders`  
**Description:** Creates a new food order.  
**Request Example:**
```json
{
  "customer_id": "cust_9988",
  "items": [
    {"product_id": "prod_123", "quantity": 10, "unit": "kg"},
    {"product_id": "prod_456", "quantity": 2, "unit": "case"}
  ],
  "payment_method_token": "tok_visa_4455"
}
```
**Response Example:** `201 Created`
```json
{
  "order_id": "ord_776655",
  "status": "pending",
  "total_amount": 450.00,
  "estimated_delivery": "2026-11-01"
}
```

**Endpoint:** `GET /api/v1/orders/{id}`  
**Description:** Retrieves order details.  
**Response Example:** `200 OK`
```json
{
  "id": "ord_776655",
  "tenant_id": "tenant_foodco_1",
  "status": "shipped",
  "tracking_number": "TRK123456789"
}
```

### 4.2 Product Catalog
**Endpoint:** `GET /api/v1/products`  
**Description:** List products with faceted filters.  
**Params:** `?category=organic&min_price=10&q=honey`  
**Response Example:** `200 OK`
```json
{
  "results": [
    {"id": "prod_123", "name": "Raw Organic Honey", "price": 15.00}
  ],
  "facets": {
    "categories": {"organic": 12, "conventional": 45},
    "ratings": {"5_star": 2, "4_star": 10}
  },
  "total_count": 12
}
```

**Endpoint:** `POST /api/v1/products/import`  
**Description:** Triggers the data import process.  
**Request:** Multipart form-data (File upload).  
**Response Example:** `202 Accepted`
```json
{
  "job_id": "import_job_abc123",
  "status": "processing",
  "polling_url": "/api/v1/imports/abc123"
}
```

### 4.3 User & Security
**Endpoint:** `POST /api/v1/auth/2fa/register`  
**Description:** Registers a new hardware security key.  
**Request Example:**
```json
{
  "credentialId": "base64_encoded_id",
  "publicKey": "base64_encoded_key",
  "signCount": 0
}
```
**Response Example:** `200 OK`
```json
{ "status": "registered", "key_nickname": "YubiKey-Office" }
```

**Endpoint:** `POST /api/v1/auth/2fa/verify`  
**Description:** Verifies a 2FA challenge.  
**Request Example:**
```json
{
  "credentialId": "...",
  "signature": "...",
  "clientDataJSON": "..."
}
```
**Response Example:** `200 OK`
```json
{ "token": "jwt_access_token_xyz" }
```

### 4.4 Billing
**Endpoint:** `GET /api/v1/billing/invoice/{id}`  
**Description:** Retrieves a PDF invoice.  
**Response:** `application/pdf`

**Endpoint:** `PATCH /api/v1/billing/subscription`  
**Description:** Changes the tenant's subscription tier.  
**Request Example:**
```json
{ "tier": "enterprise" }
```
**Response Example:** `200 OK`
```json
{ "new_tier": "enterprise", "next_billing_date": "2026-12-01" }
```

---

## 5. DATABASE SCHEMA

The database is hosted on MySQL 8.0. All tables use InnoDB with UTF8mb4 encoding.

### 5.1 Table Definitions

1. **`tenants`**
   - `id` (UUID, PK)
   - `name` (Varchar)
   - `subdomain` (Varchar, Unique)
   - `status` (Enum: active, suspended, pending)
   - `created_at` / `updated_at` (Timestamp)

2. **`users`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants.id)
   - `email` (Varchar, Unique)
   - `password_digest` (Varchar)
   - `role` (Enum: admin, staff, viewer)
   - `two_fa_enabled` (Boolean)

3. **`products`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants.id)
   - `sku` (Varchar)
   - `name` (Varchar)
   - `description` (Text)
   - `price` (Decimal 12,2)
   - `category_id` (UUID, FK)

4. **`categories`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK)
   - `name` (Varchar)
   - `parent_id` (UUID, FK -> categories.id)

5. **`orders`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK)
   - `customer_id` (UUID, FK)
   - `total_amount` (Decimal)
   - `status` (Varchar)
   - `created_at` (Timestamp)

6. **`order_items`**
   - `id` (UUID, PK)
   - `order_id` (UUID, FK -> orders.id)
   - `product_id` (UUID, FK -> products.id)
   - `quantity` (Integer)
   - `unit_price` (Decimal)

7. **`event_store`** (The CQRS heart)
   - `id` (BigInt, PK)
   - `aggregate_id` (UUID) - e.g., the Order ID
   - `event_type` (Varchar) - e.g., "OrderPaid"
   - `payload` (JSON) - The actual data change
   - `version` (Integer) - For optimistic locking
   - `created_at` (Timestamp)

8. **`auth_keys`** (For 2FA)
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `public_key` (Text)
   - `sign_count` (Integer)
   - `last_used_at` (Timestamp)

9. **`subscriptions`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK)
   - `tier` (Enum: basic, pro, enterprise)
   - `start_date` (Date)
   - `end_date` (Date)

10. **`invoices`**
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK)
    - `amount` (Decimal)
    - `status` (Enum: paid, unpaid, void)
    - `pdf_url` (Varchar)

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `products`, `orders`, `subscriptions`.
- **One-to-Many:** `orders` $\rightarrow$ `order_items`.
- **Many-to-One:** `products` $\rightarrow$ `categories`.
- **One-to-Many:** `users` $\rightarrow$ `auth_keys`.
- **Event Sourcing:** `event_store` relates to any business entity via `aggregate_id`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Delphi utilizes three distinct environments to ensure stability and PCI compliance.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** Individual developer Heroku apps + shared staging DB for integration tests.
- **Data:** Seeded with anonymized "dummy" food data. No real PII (Personally Identifiable Information).
- **Deployment:** Continuous Deployment from the `develop` branch.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation and QA. This environment is a mirror image of Production.
- **Infrastructure:** Heroku Private Space.
- **Data:** Sanatized snapshot of production data (scrubbed of credit card info).
- **Deployment:** Weekly Release Train. Merges from `develop` to `release` branch trigger the staging deploy.

#### 6.1.3 Production (Prod)
- **Purpose:** Live user traffic.
- **Infrastructure:** Heroku Private Space with dedicated VPC and Shield.
- **Data:** Real customer and financial data.
- **Compliance:** PCI DSS Level 1. Restricted access via VPN and Bastion host.
- **Deployment:** Friday 09:00 UTC release train. No hotfixes except P0.

### 6.2 Infrastructure Configuration
- **Auto-scaling:** Dynos scale based on memory utilization (threshold 70%).
- **Backups:** Daily automated snapshots of MySQL RDS with 30-day retention.
- **Monitoring:** New Relic for APM (Application Performance Monitoring) and LogDNA for centralized logging.
- **CI/CD:** GitHub Actions for running the test suite; Heroku Pipelines for deployment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** RSpec.
- **Focus:** Business logic in models and services. Every new feature must have $>90\%$ line coverage.
- **Approach:** Use "Mocks" and "Stubs" for external API calls to avoid hitting the buggy integration partner API during tests.

### 7.2 Integration Testing
- **Tool:** RSpec Request Specs.
- **Focus:** API endpoint contracts. Testing the flow from `POST /api/v1/orders` through the Event Store to the Read Model.
- **Verification:** Ensure that the `tenant_id` filter is correctly applied across all integrated services.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress.
- **Focus:** Critical user journeys (e.g., "Vendor Onboarding $\rightarrow$ Product Upload $\rightarrow$ Order Receipt").
- **Frequency:** Run against the Staging environment as part of the Weekly Release Train validation.

### 7.4 Security Testing
- **PCI Scanning:** Quarterly vulnerability scans by an Approved Scanning Vendor (ASV).
- **Penetration Testing:** Annual white-box penetration test focused on the multi-tenant isolation layer.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | Integration partner's API is undocumented and buggy. | High | High | Escalate to steering committee for additional funding to build a robust "Adapter Layer" that sanitizes partner data. |
| **RISK-02** | Primary vendor dependency announced EOL for product. | Medium | High | Audit all affected features. De-scope or replace the vendor dependency if unresolved by Milestone 2. |
| **RISK-03** | Legal review of Data Processing Agreement (DPA) is stalled. | High | Medium | **Current Blocker.** Maren Liu to ping Legal daily; prepare contingency to delay pilot launch if DPA is not signed. |
| **RISK-04** | Technical debt: Hardcoded config in 40+ files. | High | Low | Dedicate "Debt Friday" every third week to migrate constants to `credentials.yml.enc` or environment variables. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **High/Low:** Monitor and schedule.
- **Medium/High:** Contingency plan needed.

---

## 9. TIMELINE

### 9.1 Phase Description
The project is divided into three primary phases over 18 months.

#### Phase 1: Foundation & Isolation (Months 1-6)
- Focus: Multi-tenant isolation, PCI compliance setup, and the transition to CQRS.
- Dependency: Legal review of DPA (Blocker).
- **Key Target:** Stability of the core platform.

#### Phase 2: Feature Expansion (Months 7-12)
- Focus: 2FA implementation, Advanced Search, and Data Import tools.
- Dependency: Successful stability confirmation from Phase 1.
- **Key Target:** MVP feature-completeness.

#### Phase 3: Optimization & Scaling (Months 13-18)
- Focus: Automated Billing, Performance tuning of Elasticsearch, and final Architecture Review.
- Dependency: User feedback from pilot users.
- **Key Target:** Full production rollout and scale.

### 9.2 Milestone Schedule
- **Milestone 1:** Post-launch stability confirmed $\rightarrow$ **Target Date: 2026-08-15**
- **Milestone 2:** MVP feature-complete $\rightarrow$ **Target Date: 2026-10-15**
- **Milestone 3:** Architecture review complete $\rightarrow$ **Target Date: 2026-12-15**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Pivot (2023-11-02)
**Attendees:** Maren Liu, Nia Moreau, Renzo Kim, Valentina Gupta.
**Discussion:**
- Valentina expressed concern that the monolith is becoming too "heavy" for the new multi-tenant requirements.
- Nia proposed the CQRS pattern to separate the complex food-audit logic from the simple product browsing logic.
- The team debated using Kafka, but Maren decided on Redis for the event bus to keep the stack "deliberately simple."
**Decisions:**
- Adopt CQRS for the Order and Payment domains.
- Use MySQL as the event store.
**Action Items:**
- Nia: Design the `event_store` table schema. (Due: 2023-11-09)
- Renzo: Update the UI wireframes to support multi-tenant branding. (Due: 2023-11-12)

### Meeting 2: Security & 2FA Strategy (2023-12-15)
**Attendees:** Maren Liu, Valentina Gupta.
**Discussion:**
- Valentina highlighted that some vendors use older browser versions that may not support WebAuthn.
- Maren insisted that PCI DSS Level 1 requires hardware-level security for admins.
- Agreed to implement a "Tiered 2FA" approach: Hardware keys for Admins (mandatory), TOTP for Staff (optional).
**Decisions:**
- Integration of the `webauthn` gem for hardware support.
- Backup codes will be provided for all 2FA users.
**Action Items:**
- Valentina: Prototype the 2FA registration flow. (Due: 2024-01-05)

### Meeting 3: Integration Partner Crisis (2024-01-20)
**Attendees:** Maren Liu, Nia Moreau.
**Discussion:**
- Nia reported that the integration partner's API is returning `500 Internal Server Error` for 30% of requests and the documentation is outdated.
- Discussed the risk of project delay if this is not solved.
- Maren suggested that we cannot fix their API, so we must build a "Circuit Breaker" to prevent their failures from crashing the Delphi platform.
**Decisions:**
- Implement the `stoplight` gem for circuit breaking.
- Escalate the API instability to the steering committee to demand a dedicated technical contact from the partner.
**Action Items:**
- Maren: Draft escalation email to steering committee. (Due: 2024-01-21)
- Nia: Implement the circuit breaker in the `PartnerClient` service. (Due: 2024-01-27)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000 USD

| Category | Allocated Amount | Percentage | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | $950,000 | 63.3% | 8 members (Full-time + Contractor Valentina). Includes payroll and benefits. |
| **Infrastructure** | $220,000 | 14.7% | Heroku Private Spaces, AWS RDS, Elasticsearch clusters, New Relic. |
| **Tools & Licensing** | $80,000 | 5.3% | PCI Compliance audits, Security software, GitHub Enterprise, Slack. |
| **Contingency** | $250,000 | 16.7% | Reserved for "Risk 1" (Partner API fixes) and unexpected infrastructure spikes. |

**Spending Note:** Personnel costs are front-loaded during the "Foundation" phase (Months 1-6) due to the high demand for data engineering (Nia) and architectural design.

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To maintain the required security posture, Project Delphi adheres to the following:
- **Data Encryption:** All credit card data is encrypted at rest using AES-256.
- **Network Isolation:** The production environment resides in a Heroku Private Space, isolated from the public internet via a secure gateway.
- **Access Control:** Use of Just-In-Time (JIT) access for database modifications.
- **Audit Logs:** All administrative actions are logged to an immutable log stream (Event Store).

### Appendix B: Event Sourcing Workflow Example
*Example: Changing an Order Status from "Pending" to "Shipped"*
1. **Command:** `ShipOrderCommand(order_id: "ord_123", tracking_no: "TRK99")`
2. **Validation:** System checks if order is in a shippable state.
3. **Event Created:** An event `OrderShipped` is written to the `event_store` table.
4. **Projection:** The `OrderReadModelWorker` picks up the event and updates the `orders` table (the read model) `status` column to "Shipped".
5. **Notification:** An asynchronous trigger sends a "Your food is on the way!" email to the customer.