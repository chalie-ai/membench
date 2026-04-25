Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Document (PSD). It is designed to serve as the "Single Source of Truth" (SSOT) for the development team at Stratos Systems.

***

# PROJECT SPECIFICATION: DELPHI
**Version:** 1.0.4  
**Status:** Draft for Review  
**Date:** October 24, 2023  
**Owner:** Callum Kim (Engineering Manager)  
**Company:** Stratos Systems  
**Confidentiality:** Level 4 (Internal/Restricted)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Delphi" is a strategic mobile application initiative commissioned by Stratos Systems to address operational inefficiencies within the retail vertical. Currently, the organization relies on four disparate internal tools for inventory management, pricing analysis, vendor coordination, and customer loyalty tracking. This fragmentation has led to data silos, redundant subscription costs for four different SaaS backends, and a degraded user experience for field agents.

The primary objective of Delphi is a comprehensive cost-reduction initiative. By consolidating these four redundant tools into a single, unified mobile application, Stratos Systems aims to eliminate overlapping license fees and reduce the overhead associated with maintaining four separate codebases and database schemas. 

### 1.2 Business Justification
The current architectural overhead is unsustainable. Each of the four legacy tools requires separate maintenance windows, separate security audits, and distinct API integrations. Furthermore, the lack of a unified data layer means that reporting currently requires manual CSV exports and manipulation in Excel, leading to a 15% error rate in retail forecasting.

Delphi will centralize these operations into a single TypeScript/Next.js ecosystem. By migrating to a serverless architecture hosted on Vercel with a PostgreSQL backbone via Prisma, the company will reduce infrastructure spend by an estimated 30% through the elimination of idle server costs associated with the legacy VM-based tools.

### 1.3 ROI Projection and Success Metrics
The financial justification for Delphi is twofold: immediate OpEx reduction and long-term revenue generation.

**Direct Cost Savings:** 
- Elimination of 4 legacy tool subscriptions: $85,000/year.
- Reduction in DevOps man-hours: ~1,200 hours/year.

**Revenue Generation:**
The application is designed not just as an internal tool, but as a potential white-label offering for retail partners. 
- **Metric 1:** $500,000 in new revenue attributed to the product within 12 months of launch.
- **Metric 2:** 10,000 Monthly Active Users (MAU) within 6 months of launch.

With a total project budget of $400,000, the project reaches a break-even point within approximately 9 months of the "First Paying Customer" milestone (2025-08-15), provided the revenue targets are met. The ROI is projected at 225% over a 24-month horizon.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Delphi utilizes a modern, type-safe stack to ensure rapid iteration and scalability.
- **Frontend/Backend:** Next.js (TypeScript) utilizing App Router.
- **ORM:** Prisma (Type-safe database client).
- **Database:** PostgreSQL (Managed instance).
- **Deployment/Hosting:** Vercel (Edge functions and static asset hosting).
- **Security Standard:** PCI DSS Level 1 Compliance (Mandatory for direct credit card processing).

### 2.2 Architectural Pattern
The system employs a serverless architecture. Instead of a monolithic API, Delphi utilizes Vercel Serverless Functions coordinated by an API Gateway. This allows for independent scaling of the "Billing" module (high compute) vs. the "Data Import" module (high memory).

#### ASCII Architecture Diagram: Request Flow
```text
[ User Mobile App ]  --> [ Vercel Edge Network ] 
                                 |
                                 v
                        [ API Gateway / Middleware ]
                                 |
       __________________________|__________________________
      |                          |                          |
[ Auth Service ]        [ Business Logic Layer ]    [ External Integrations ]
(NextAuth.js)            (Serverless Functions)     (Stripe / Webhooks)
      |                          |                          |
      |__________________________|__________________________|
                                 |
                        [ Prisma ORM Layer ]
                                 |
                        [ PostgreSQL Database ]
                        (RDS/Managed Cluster)
```

### 2.3 Data Flow and State Management
State management is handled via React Context for global UI state and TanStack Query (React Query) for server-state synchronization. This ensures that the mobile interface remains responsive even when dealing with the large datasets typical of retail inventory.

### 2.4 Security Architecture
Given the PCI DSS Level 1 requirement, the architecture implements "Strict Isolation." Credit card data is never stored in the primary PostgreSQL database. Instead, it is tokenized via a secure vault. All serverless functions communicating with the payment gateway are isolated in a VPC (Virtual Private Cloud) with restricted egress.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox (Priority: Critical)
**Status: Complete**

The Customer-Facing API is the primary gateway for external retail partners to integrate their own systems with Delphi. This feature is a launch blocker; without it, the $500K revenue goal cannot be achieved as partners cannot programmatically interact with the platform.

**Functional Requirements:**
- **Versioning:** The API must support semantic versioning (e.g., `/v1/`, `/v2/`). When a new version is deployed, the previous version must remain supported for a minimum of 6 months.
- **Sandbox Environment:** A mirrored, non-production environment where developers can test API calls without affecting real-world inventory or billing. The sandbox uses a separate PostgreSQL schema (`schema_sandbox`).
- **Authentication:** API Key-based authentication using rotating secrets. Keys are hashed using SHA-256 before storage.
- **Rate Limiting:** Implementation of a "leaky bucket" algorithm to prevent DDoS attacks, limiting partners to 1,000 requests per minute per API key.

**Technical Implementation:**
The API is built using Next.js Route Handlers. The sandbox environment is achieved through a separate Vercel project deployment (`delphi-sandbox.stratos.io`) connected to a staging database.

---

### 3.2 Webhook Integration Framework (Priority: Critical)
**Status: In Review**

The Webhook Framework allows Delphi to push real-time updates to third-party retail tools (e.g., Shopify, Square) when specific events occur (e.g., `inventory.low`, `order.completed`).

**Functional Requirements:**
- **Event Subscription:** Users can define a target URL and a list of events they wish to subscribe to via the Delphi admin dashboard.
- **Payload Standardization:** All webhooks must follow a standardized JSON envelope containing `event_type`, `timestamp`, `version`, and `data`.
- **Retry Logic:** If the receiving server returns a non-200 status code, Delphi must implement an exponential backoff retry strategy (attempts at 1m, 5m, 30m, 2h, 12h).
- **Security:** Every webhook payload must be signed with an `X-Delphi-Signature` HMAC header using a shared secret to allow the receiver to verify the authenticity of the request.

**Technical Implementation:**
A dedicated `WebhookQueue` table in PostgreSQL tracks pending deliveries. A cron job (triggered via Vercel Cron) processes the queue and dispatches requests using the `fetch` API.

---

### 3.3 Automated Billing and Subscription Management (Priority: High)
**Status: Not Started**

This module handles the monetization of the platform. It must manage monthly subscriptions, per-user pricing, and one-time setup fees.

**Functional Requirements:**
- **Subscription Tiers:** Support for "Basic," "Professional," and "Enterprise" tiers with different feature flags.
- **Automated Invoicing:** Generation of PDF invoices on the 1st of every month.
- **Dunning Management:** Automated emails to users whose credit cards have expired or failed, with a 7-day grace period before account suspension.
- **PCI Compliance:** Implementation of the "Payment Intent" flow to ensure sensitive card data never hits the Stratos Systems servers.

**Technical Implementation:**
Integration with Stripe Billing. The system will utilize Stripe Webhooks to update the `Subscription` table in the PostgreSQL database. 
*Note: This module currently has zero test coverage and is flagged as a high-risk area of technical debt.*

---

### 3.4 Audit Trail Logging with Tamper-Evident Storage (Priority: Low)
**Status: In Progress**

To meet retail compliance standards, every mutation (Create, Update, Delete) in the system must be logged.

**Functional Requirements:**
- **Granular Logging:** Capture the `user_id`, `timestamp`, `ip_address`, `action`, and a `diff` of the record before and after the change.
- **Tamper-Evidence:** Use a cryptographic chaining mechanism (similar to a blockchain) where each log entry contains a hash of the previous entry. If any record is deleted or altered, the chain breaks.
- **Retention:** Logs must be stored for 7 years to satisfy regulatory requirements.
- **Searchability:** Admin users must be able to filter logs by date range or specific resource ID.

**Technical Implementation:**
Logs are written to a `AuditLog` table. A separate background process calculates the SHA-256 hash of the current row + previous row's hash.

---

### 3.5 Data Import/Export with Format Auto-Detection (Priority: Low)
**Status: In Design**

This feature allows users to migrate data from the 4 legacy tools into Delphi without manual entry.

**Functional Requirements:**
- **Auto-Detection:** The system must analyze the first 10 rows of an uploaded file to determine if it is CSV, JSON, or XML.
- **Schema Mapping:** A UI-based mapper where users can drag and drop legacy columns (e.g., "Prod_Name") to Delphi columns (e.g., "product_title").
- **Validation:** Pre-import validation to check for data types (e.g., ensuring a price column contains only numbers).
- **Bulk Export:** Ability to export any filtered view of the data into the same three formats.

**Technical Implementation:**
Implementation of a streaming parser (using `csv-parse`) to handle files up to 500MB without crashing the serverless function's memory limit.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Base URL: `https://api.delphi.stratos.io/api/v1`.

### 4.1 Authentication
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| POST | `/auth/login` | Exchange credentials for JWT | None |
| POST | `/auth/refresh` | Refresh expired session token | JWT |

**Request Example (`/auth/login`):**
```json
{
  "email": "user@stratos.com",
  "password": "securepassword123"
}
```
**Response Example:**
```json
{
  "token": "eyJhbGci... ",
  "expires_at": "2023-10-25T12:00:00Z"
}
```

### 4.2 Inventory Management
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| GET | `/inventory` | List all retail items | API Key/JWT |
| POST | `/inventory` | Create new inventory item | API Key/JWT |
| PATCH | `/inventory/:id` | Update stock levels | API Key/JWT |

**Request Example (`POST /inventory`):**
```json
{
  "sku": "S-100-BLK",
  "name": "Stratos T-Shirt Black",
  "quantity": 50,
  "price": 25.00
}
```
**Response Example:**
```json
{
  "id": "inv_98765",
  "status": "created",
  "created_at": "2023-10-24T10:00:00Z"
}
```

### 4.3 Billing & Subscriptions
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| GET | `/billing/status` | Check current subscription | JWT |
| POST | `/billing/upgrade` | Change subscription tier | JWT |
| GET | `/billing/invoices` | List all past invoices | JWT |

**Request Example (`POST /billing/upgrade`):**
```json
{
  "tier_id": "enterprise_monthly"
}
```
**Response Example:**
```json
{
  "new_tier": "Enterprise",
  "next_billing_date": "2023-11-01",
  "prorated_amount": 45.00
}
```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL relational store. All tables use UUIDs as primary keys for distributed system compatibility.

### 5.1 Table Definitions

1.  **`Users`**: Core identity table.
    - `id` (UUID, PK), `email` (String, Unique), `password_hash` (String), `role` (Enum: ADMIN, USER, READ_ONLY), `created_at` (Timestamp).
2.  **`Organizations`**: Retail entities using the app.
    - `id` (UUID, PK), `org_name` (String), `tax_id` (String), `industry_sector` (String).
3.  **`UserOrgMapping`**: Many-to-many link between users and orgs.
    - `user_id` (FK), `org_id` (FK), `access_level` (Integer).
4.  **`InventoryItems`**: Consolidated product data.
    - `id` (UUID, PK), `org_id` (FK), `sku` (String), `title` (String), `quantity` (Integer), `unit_price` (Decimal).
5.  **`Subscriptions`**: Billing state.
    - `id` (UUID, PK), `org_id` (FK), `stripe_subscription_id` (String), `plan_type` (Enum), `status` (Enum: ACTIVE, PAST_DUE, CANCELED).
6.  **`Invoices`**: Financial records.
    - `id` (UUID, PK), `subscription_id` (FK), `amount` (Decimal), `billed_at` (Timestamp), `paid` (Boolean).
7.  **`WebhookSubscriptions`**: Third-party integration targets.
    - `id` (UUID, PK), `org_id` (FK), `target_url` (String), `event_mask` (String), `secret_token` (String).
8.  **`WebhookLogs`**: Audit of outgoing webhooks.
    - `id` (UUID, PK), `webhook_id` (FK), `payload` (JSONB), `response_code` (Integer), `attempt_count` (Integer).
9.  **`AuditLogs`**: Tamper-evident change history.
    - `id` (UUID, PK), `user_id` (FK), `entity_type` (String), `entity_id` (UUID), `change_diff` (JSONB), `prev_hash` (String), `row_hash` (String).
10. **`ApiKeys`**: Access control for the customer API.
    - `id` (UUID, PK), `org_id` (FK), `key_hash` (String), `last_used` (Timestamp), `expires_at` (Timestamp).

### 5.2 Relationships
- `Organizations` 1:N `InventoryItems`
- `Organizations` 1:1 `Subscriptions`
- `Subscriptions` 1:N `Invoices`
- `Users` 1:N `AuditLogs`
- `Organizations` 1:N `ApiKeys`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi utilizes three distinct environments to ensure stability.

| Environment | Purpose | Trigger | Database |
| :--- | :--- | :--- | :--- |
| **Development** | Local feature work | Manual | Local Dockerized PG |
| **Staging** | QA and UAT | Merge to `develop` branch | Staging PG Cluster |
| **Production** | End-user access | Merge to `main` branch | Production PG Cluster |

### 6.2 Continuous Deployment (CD)
We employ a "Continuous Deployment" model. Every Pull Request (PR) that passes the automated CI pipeline and receives a peer review is merged into `main` and automatically deployed to production via Vercel.

**CI Pipeline Steps:**
1. `npm run lint` (Code style check)
2. `npm run type-check` (TypeScript validation)
3. `prisma generate` (Client synchronization)
4. `npm run test` (Unit tests—currently failing for billing module)
5. `vercel deploy --prod`

### 6.3 Infrastructure as Code (IaC)
Infrastructure is managed via Terraform to ensure that the PostgreSQL cluster and Vercel project settings are reproducible. This prevents "configuration drift" between staging and production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** Jest.
- **Focus:** Pure logic functions (e.g., pricing calculations, webhook signature generation).
- **Target:** 80% line coverage.

### 7.2 Integration Testing
- **Tooling:** Vitest + Prisma Mock.
- **Focus:** API endpoints and database transactions. We test the "Happy Path" and "Edge Case Path" for every endpoint in the API documentation.
- **Special Case:** The Billing module is currently missing these tests, which is the primary technical debt item.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Focus:** Critical user journeys (e.g., User Login $\rightarrow$ Inventory Update $\rightarrow$ Invoice Generation).
- **Frequency:** Run against the Staging environment before every production release.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is building same product and is 2 months ahead. | High | High | Hire a specialized contractor to accelerate the Webhook and API features, reducing the "bus factor" and increasing velocity. |
| R-02 | Key Architect leaving company in 3 months. | Medium | High | De-scope non-critical features (e.g., Data Import) if architectural knowledge transfer is not complete by Milestone 1. |
| R-03 | Billing module deployed without tests. | High | Critical | Immediate sprint dedicated to "Test Debt" before the first paying customer onboarding (Milestone 3). |
| R-04 | PCI DSS compliance failure. | Low | Critical | Quarterly third-party security audits by Celine Nakamura. |

**Impact Matrix:**
- **High/Critical:** Could stop the launch or cause legal liability.
- **Medium:** Delays milestone dates.
- **Low:** Minor feature degradation.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundation (Now – 2025-04-15)
- Focus on core architecture and security.
- Dependency: Architecture review must be signed off by Callum Kim.
- **Milestone 1: Architecture review complete (Target: 2025-04-15).**

### 9.2 Phase 2: Integration & Beta (2025-04-16 – 2025-06-15)
- Finalize Webhook framework.
- Beta testing with 5 select retail partners.
- Focus on stability and bug squashing.
- **Milestone 2: Post-launch stability confirmed (Target: 2025-06-15).**

### 9.3 Phase 3: Monetization (2025-06-16 – 2025-08-15)
- Implement the automated billing module.
- Shift from beta to "Paid" status.
- Onboard the first official paying customer.
- **Milestone 3: First paying customer onboarded (Target: 2025-08-15).**

---

## 10. MEETING NOTES

### Meeting 1: Kickoff & Team Alignment
**Date:** 2023-10-10
- Budget: $400k. 
- 12 people. 
- Consolidating 4 tools.
- Concern: New team, need to build trust.
- Action: Weekly 1:1s between Callum and lead devs.

### Meeting 2: Technical Friction
**Date:** 2023-11-05
- Product wants a more "flexible" API.
- Engineering wants "strict" versioning.
- Current Blocker: Disagreement on API design.
- Decision: Compromise on semantic versioning; Product gets the sandbox environment they requested.

### Meeting 3: Crisis/Debt Review
**Date:** 2023-12-12
- Billing module pushed to prod without tests.
- "Deadline pressure" cited as reason.
- Risk: High.
- Decision: Mark as Technical Debt; prioritize in Q1 2024.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salaries for 12-person team (prorated for project duration). |
| **Infrastructure** | $40,000 | Vercel Pro, Managed PostgreSQL, AWS VPC. |
| **Tools & Licenses** | $20,000 | Stripe fees, Monitoring (Sentry/Datadog), IDE licenses. |
| **Contractors** | $30,000 | Specialist hire to mitigate "Bus Factor" risk (R-01). |
| **Contingency** | $30,000 | Emergency fund for scope creep or security patches. |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To maintain Level 1 certification, Delphi must adhere to the following technical constraints:
1. **Encryption:** All data in transit must be TLS 1.2+.
2. **Key Management:** Encryption keys must be rotated every 90 days.
3. **Access Control:** Role-Based Access Control (RBAC) must be enforced at the database level.
4. **Vulnerability Scanning:** Monthly automated scans of all serverless endpoints.

### Appendix B: Legacy Tool Mapping
The following mappings are used during the consolidation process:
- **Tool A (Inventory) $\rightarrow$** `InventoryItems` table.
- **Tool B (Pricing) $\rightarrow$** `InventoryItems.unit_price` logic.
- **Tool C (Vendors) $\rightarrow$** `Organizations` table.
- **Tool D (Loyalty) $\rightarrow$** `UserOrgMapping` and `Users` table.