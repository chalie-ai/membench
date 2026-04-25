# PROJECT SPECIFICATION: PROJECT LODESTAR
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Last Updated:** 2024-10-24  
**Classification:** Internal Confidential – Duskfall Inc.  
**Owner:** Fleur Santos (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Lodestar is a greenfield strategic initiative by Duskfall Inc. aimed at diversifying the company's portfolio. While Duskfall Inc. is established in the aerospace sector, Lodestar represents an entry into a completely new market vertical—specifically, the integration of high-precision aerospace telemetry data for third-party logistics and autonomous drone fleet management. This is an internal enterprise tool designed to provide a centralized platform for external partners to manage flight data, billing, and fleet synchronization without requiring manual intervention from Duskfall’s core engineering teams.

### 1.2 Business Justification
The aerospace industry is shifting toward a "Data-as-a-Service" (DaaS) model. Currently, Duskfall Inc. captures immense amounts of telemetry data that remains siloed in proprietary formats. Lodestar intends to monetize this data by providing a scalable, multi-tenant interface where clients can import their own flight parameters, utilize Duskfall’s proprietary analysis engines, and manage their subscriptions autonomously. 

Entering this market is a high-risk, high-reward move. Because this is a market Duskfall has never operated in, Lodestar serves as the "wedge" product. By providing a tool that solves the immediate pain point of telemetry fragmentation, Duskfall can establish a footprint in the logistics sector, creating a recurring revenue stream that is decoupled from the long-cycle government aerospace contracts that typically define the company’s income.

### 1.3 ROI Projection
Since the project is currently unfunded and bootstrapping with existing team capacity, the initial "cost" is measured in opportunity cost of engineering hours. 

**Projected Financial Gains:**
- **Year 1:** Target acquisition of 5 pilot enterprise clients with an average annual contract value (ACV) of $120,000.
- **Year 2:** Expansion to 50 clients, targeting a Monthly Recurring Revenue (MRR) of $600,000.
- **Cost Savings:** Reduction in manual onboarding time for new telemetry partners from 4 weeks to 2 hours via the automated import and billing modules.

**Projected ROI:**
Given the bootstrapping nature of the project, the ROI is calculated based on the Delta between the current manual support costs and the projected automated revenue. We estimate a 300% ROI by the end of the second fiscal year following the MVP launch.

### 1.4 Strategic Alignment
Lodestar aligns with the "Duskfall 2030" initiative to transition from a hardware-centric aerospace company to a software-enabled intelligence firm. It leverages the company's existing technical prowess in low-latency data processing (Rust) and edge computing (Cloudflare/SQLite) to create a competitive advantage over legacy logistics software.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Lodestar utilizes a Hexagonal Architecture to ensure that the core business logic remains decoupled from external dependencies. This is critical given the volatility of the project's budget and the potential for shifting infrastructure providers.

**The Domain Layer:** Contains the pure business logic, entities, and use cases (e.g., `BillingEngine`, `TelemetryProcessor`). It has no knowledge of the database or the API framework.
**The Ports:** Interfaces that define how the core logic interacts with the outside world (e.g., `UserRepository`, `PaymentGatewayPort`).
**The Adapters:** Concrete implementations of the ports. 
- *Input Adapters:* Cloudflare Workers handlers, REST API controllers.
- *Output Adapters:* SQLite wrappers for edge storage, Stripe API implementation for billing.

### 2.2 Technology Stack
- **Backend:** Rust (using the `Axum` framework for the API and `Serde` for serialization). Rust was chosen for memory safety and performance, essential for handling high-frequency aerospace data.
- **Frontend:** React 18 with TypeScript, utilizing Tailwind CSS for the UI layer.
- **Edge Layer:** Cloudflare Workers. This allows the application to run close to the user, reducing latency for global aerospace partners.
- **Database:** SQLite for edge-side persistence. Data is synchronized back to a central durable store via a distributed log mechanism.
- **Feature Management:** LaunchDarkly. This allows the team to toggle "in-progress" features (like collaborative editing) without redeploying code.
- **Deployment Strategy:** Canary releases. New versions are rolled out to 5% of users, monitored for errors, and then scaled.

### 2.3 System Diagram (ASCII Representation)

```text
                                   [ USER BROWSER ]
                                          |
                                  (HTTPS / JSON / WASM)
                                          |
                                [ CLOUDFLARE WORKER ] <--- [ LaunchDarkly Flags ]
                                          |
             _____________________________|_____________________________
            |                             |                             |
    [ INPUT ADAPTERS ]             [ CORE DOMAIN ]              [ OUTPUT ADAPTERS ]
    | - REST API Handler |  --->  | - Billing Logic    |  --->  | - SQLite Edge DB   |
    | - WebSocket Port   |        | - Data Import Sync |        | - Stripe Gateway   |
    | - Auth Middleware   |       | - Tenant Isolation  |        | - S3 Telemetry Buck|
            |_____________________________|_____________________________|
                                          |
                                  [ INFRASTRUCTURE ]
                                 (Global Edge Network)
```

### 2.4 Data Flow
1. Request enters via Cloudflare Worker.
2. The Input Adapter parses the request and validates the JWT.
3. The request is passed to a Domain Use Case (e.g., `ProcessSubscription`).
4. The Domain Logic interacts with an Output Port (e.g., `IBillingRepository`).
5. The SQLite Adapter executes the query and returns the result to the Domain.
6. The Domain returns a result to the Adapter, which formats the JSON response.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** High | **Status:** In Progress | **Owner:** Dina Liu

**Description:** 
The core revenue engine for Lodestar. This feature manages the entire lifecycle of a customer subscription, from initial signup to monthly recurring billing and tier upgrades. Given that Duskfall has never operated in this market, the billing system must be flexible enough to handle both "pay-as-you-go" telemetry usage and "flat-fee" enterprise tiers.

**Functional Requirements:**
- **Tier Logic:** Implement three tiers: *Starter* (10GB data/mo), *Professional* (100GB data/mo), and *Enterprise* (Unlimited).
- **Automatic Invoicing:** Generation of PDF invoices on the 1st of every month using a background worker.
- **Dunning Process:** Automated email notifications when a payment fails, with a 3-day grace period before account suspension.
- **Usage Tracking:** A middleware that intercepts all data import requests and increments the tenant's usage counter in the SQLite database.

**Technical Implementation:**
The billing module is implemented as a standalone domain service. It utilizes the `BillingRepository` port to track usage and the `PaymentGateway` port to interact with the external payment processor. 

**Critical Debt Note:** Due to deadline pressure, this module was deployed without unit test coverage. This represents a significant risk to financial integrity. Future sprints must prioritize the `test/billing` directory.

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** In Review | **Owner:** Sanjay Fischer

**Description:** 
Aerospace data comes in various formats (CSV, JSON, XML, and proprietary binary formats like ARINC 429). This feature allows users to upload raw files, which the system then analyzes to determine the format and map it to the Lodestar internal schema.

**Functional Requirements:**
- **Magic Number Detection:** The system must read the first 1KB of any uploaded file to detect the file signature (magic numbers) to distinguish between JSON and binary formats.
- **Schema Mapping:** A UI-based mapper where users can drag-and-drop source columns to target fields (e.g., "ALT_FT" $\rightarrow$ "altitude_feet").
- **Asynchronous Processing:** Large files (>50MB) must be processed via a background queue to avoid timing out the Cloudflare Worker (15-second limit).
- **Export Options:** Support for exporting filtered datasets back into CSV or JSON.

**Technical Implementation:**
A Rust-based "Parser Engine" is used. It employs a strategy pattern where different parsers are instantiated based on the detected file type. The `AutoDetect` service iterates through a list of registered format signatures before handing the stream to the specific parser.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Blocked | **Owner:** Dina Liu

**Description:** 
To protect the shared infrastructure from "noisy neighbor" effects, Lodestar requires a robust rate-limiting mechanism. Additionally, users need a dashboard to see their API consumption patterns.

**Functional Requirements:**
- **Token Bucket Algorithm:** Implement a token bucket rate limiter per API key.
- **Tiered Limits:** Starter users get 1,000 requests/hour; Enterprise users get 100,000 requests/hour.
- **Analytics Dashboard:** A React-based visualization showing requests per second (RPS) and error rates (4xx/5xx).
- **Alerting:** Notify the tenant via email when they reach 80% of their monthly quota.

**Blocker:** This feature is currently blocked pending budget approval for a critical Redis-compatible distributed cache tool for global rate-limit state synchronization. Without this tool, rate limiting can only be performed locally per worker node, which is insufficient.

### 3.4 Multi-tenant Data Isolation (Shared Infrastructure)
**Priority:** Low | **Status:** In Design | **Owner:** Fleur Santos

**Description:** 
Lodestar uses a "Shared Schema" approach where all tenant data resides in the same database but is logically separated by a `tenant_id`. This is the most cost-effective way to bootstrap the product.

**Functional Requirements:**
- **Row-Level Security (RLS) Simulation:** Every query must explicitly include a `WHERE tenant_id = ?` clause.
- **Tenant Context Middleware:** A wrapper that extracts the `tenant_id` from the JWT and injects it into the domain request context.
- **Isolation Validation:** A set of automated "leak tests" that attempt to query data using a different tenant's ID to ensure the system returns a 403 Forbidden.

**Technical Implementation:**
The design proposes a "Tenant-Aware Repository" wrapper in Rust. Instead of calling the database directly, the domain logic calls the wrapper, which automatically appends the tenant filter to all SQL queries, preventing developer error from causing data leaks.

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low | **Status:** In Design | **Owner:** Adaeze Liu

**Description:** 
Allow multiple users from the same organization to edit telemetry mapping configurations and flight plans simultaneously, similar to Google Docs.

**Functional Requirements:**
- **Operational Transformation (OT) or CRDTs:** Implementation of Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency across distributed clients.
- **Presence Indicators:** Show who is currently editing a specific field (cursors and avatars).
- **Locking Mechanism:** An optional "Hard Lock" mode for critical configuration changes where only one user can edit at a time.
- **Version History:** The ability to roll back to a previous state if a collaborative session introduces errors.

**Technical Implementation:**
The proposal involves using WebSockets for real-time communication. Given the edge nature of the app, we will utilize Cloudflare Durable Objects to maintain the state of the "Editing Session" in a single location, preventing the need for a centralized heavy database for every keystroke.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Base URL: `https://api.lodestar.duskfall.com`.

### 4.1 Authentication & Tenant Management

**POST `/auth/login`**
- **Description:** Authenticates user and returns a JWT.
- **Request:** `{"email": "user@example.com", "password": "password123"}`
- **Response (200):** `{"token": "eyJ...", "expires_at": "2025-03-16T00:00:00Z"}`

**GET `/tenant/profile`**
- **Description:** Returns the current tenant's configuration and tier.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200):** `{"tenant_id": "T-99", "name": "SkyNet Logistics", "tier": "Professional"}`

### 4.2 Billing & Subscriptions

**GET `/billing/usage`**
- **Description:** Retrieves current month's data usage.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200):** `{"bytes_used": 450000000, "limit": 1073741824, "percent": 41.9}`

**POST `/billing/upgrade`**
- **Description:** Requests a tier upgrade.
- **Request:** `{"target_tier": "Enterprise"}`
- **Response (201):** `{"status": "pending_payment", "invoice_id": "INV-2024-001"}`

### 4.3 Telemetry Data Import/Export

**POST `/data/import`**
- **Description:** Uploads a telemetry file for processing.
- **Request:** `multipart/form-data` (file: `flight_001.bin`)
- **Response (202):** `{"job_id": "job_abc_123", "status": "processing"}`

**GET `/data/import/status/{job_id}`**
- **Description:** Checks the progress of a data import job.
- **Response (200):** `{"job_id": "job_abc_123", "status": "completed", "rows_imported": 15000}`

**GET `/data/export`**
- **Description:** Generates a download link for filtered data.
- **Query Params:** `?format=csv&start_date=2024-01-01&end_date=2024-01-31`
- **Response (200):** `{"download_url": "https://s3.duskfall.com/export/xyz.csv", "expires_in": 3600}`

### 4.4 Collaborative Tools

**POST `/collab/session/join`**
- **Description:** Joins a real-time editing session for a specific configuration.
- **Request:** `{"config_id": "cfg_789"}`
- **Response (200):** `{"session_id": "sess_456", "websocket_url": "wss://edge.lodestar.com/collab"}`

---

## 5. DATABASE SCHEMA

The system utilizes an edge-distributed SQLite architecture. While the data is distributed, the schema is unified.

### 5.1 Tables and Relationships

1.  **`tenants`**
    - `id` (UUID, PK)
    - `company_name` (VARCHAR)
    - `created_at` (TIMESTAMP)
    - `tier_id` (FK $\rightarrow$ `subscription_tiers.id`)
    - `status` (ENUM: 'active', 'suspended', 'pending')

2.  **`users`**
    - `id` (UUID, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `email` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `role` (ENUM: 'admin', 'editor', 'viewer')

3.  **`subscription_tiers`**
    - `id` (INT, PK)
    - `tier_name` (VARCHAR)
    - `monthly_price` (DECIMAL)
    - `data_limit_bytes` (BIGINT)

4.  **`billing_cycles`**
    - `id` (UUID, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `start_date` (DATE)
    - `end_date` (DATE)
    - `amount_billed` (DECIMAL)
    - `payment_status` (ENUM: 'paid', 'unpaid', 'failed')

5.  **`usage_logs`**
    - `id` (BIGINT, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `timestamp` (TIMESTAMP)
    - `bytes_processed` (BIGINT)
    - `endpoint_hit` (VARCHAR)

6.  **`telemetry_imports`**
    - `id` (UUID, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `filename` (VARCHAR)
    - `status` (ENUM: 'queued', 'processing', 'completed', 'failed')
    - `error_log` (TEXT)

7.  **`data_mappings`**
    - `id` (UUID, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `source_field` (VARCHAR)
    - `target_field` (VARCHAR)
    - `transformation_rule` (TEXT)

8.  **`flight_data`**
    - `id` (BIGINT, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `timestamp` (TIMESTAMP)
    - `altitude` (FLOAT)
    - `velocity` (FLOAT)
    - `latitude` (FLOAT)
    - `longitude` (FLOAT)

9.  **`api_keys`**
    - `id` (UUID, PK)
    - `tenant_id` (FK $\rightarrow$ `tenants.id`)
    - `key_hash` (VARCHAR)
    - `last_used` (TIMESTAMP)

10. **`collab_sessions`**
    - `id` (UUID, PK)
    - `config_id` (VARCHAR)
    - `active_users` (INTEGER)
    - `last_modified` (TIMESTAMP)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy

| Environment | Purpose | Access | Deployment Method |
| :--- | :--- | :--- | :--- |
| **Development** | Local feature dev | All Devs | Local Docker / Wrangler |
| **Staging** | QA and Pre-release | Devs, QA | Automatic on merge to `develop` |
| **Production** | End-user live environment | SRE / CTO | Manual trigger via Canary |

### 6.2 Infrastructure Details
- **Compute:** Cloudflare Workers (V8 Isolation).
- **Storage:** Cloudflare R2 (for raw telemetry file uploads) and SQLite via Durable Objects for stateful data.
- **CI/CD:** GitHub Actions.
    - **Step 1:** Run Rust tests (`cargo test`).
    - **Step 2:** Run React build (`npm run build`).
    - **Step 3:** Deploy to Staging.
    - **Step 4:** Run E2E Cypress tests in Staging.
    - **Step 5:** Deploy to Production Canary (5% $\rightarrow$ 25% $\rightarrow$ 100%).

### 6.3 Feature Flagging
LaunchDarkly is integrated into both the React frontend and Rust backend. 
- **Flag `lodestar-collab-beta`**: Controls visibility of the collaborative editing panel.
- **Flag `lodestar-new-billing-engine`**: Diverts traffic from the legacy billing logic to the new automated system for a subset of users.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `cargo test` is used for domain logic. Every new use case in the Hexagonal core must have 100% branch coverage.
- **Frontend:** Jest and React Testing Library for individual component validation.

### 7.2 Integration Testing
- Focuses on the "Adapters." Tests are written to ensure the `SQLiteAdapter` correctly translates Rust types to SQL queries.
- Integration tests are run against a temporary SQLite in-memory database.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Cypress.
- **Scope:** Critical user journeys (e.g., "User logs in $\rightarrow$ Uploads File $\rightarrow$ Checks Billing").
- **Frequency:** Run on every deployment to Staging.

### 7.4 Penetration Testing
As there is no formal compliance framework (e.g., SOC2) currently required, Duskfall Inc. will perform **Quarterly Penetration Testing**.
- **Q1 Focus:** JWT hijacking and Tenant ID spoofing.
- **Q2 Focus:** SQL injection via the `data_mappings` table.
- **Q3 Focus:** Denial of Service (DoS) on the upload endpoint.
- **Q4 Focus:** Privilege escalation from 'viewer' to 'admin'.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Budget cut by 30% next quarter | High | High | Escalate to steering committee for permanent funding; prioritize MVP features. |
| R2 | Project sponsor rotation | Medium | Medium | Document all workarounds and institutional knowledge; share with the wider executive team. |
| R3 | Billing module instability | High | High | Immediately assign Dina Liu to write retroactive tests for the core billing logic. |
| R4 | Edge DB synchronization lag | Medium | Low | Implement an optimistic UI update strategy in React. |
| R5 | Market mismatch (No product-market fit) | Medium | High | Launch pilot with 5 users early to gather feedback before full scale. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required (R1, R3).
- **Medium/High:** Close monitoring (R5).
- **Medium/Medium:** Documented workaround (R2).

---

## 9. TIMELINE & GANTT DESCRIPTION

### Phase 1: Foundation (Now - 2025-03-15)
- **Goal:** Finalize the skeletal architecture.
- **Key Activity:** Setting up the Hexagonal structure in Rust, configuring Cloudflare Workers, and establishing the SQLite schema.
- **Dependency:** All team members must agree on the Port interfaces.
- **Milestone 1:** Architecture Review Complete (2025-03-15).

### Phase 2: Core Feature Build (2025-03-16 - 2025-05-15)
- **Goal:** Deliver the MVP.
- **Key Activity:** Completing the Automated Billing module (High Priority) and Data Import/Export (Medium Priority).
- **Dependency:** Budget approval for Redis-compatible cache for rate limiting.
- **Milestone 2:** MVP Feature-Complete (2025-05-15).

### Phase 3: Hardening & Scaling (2025-05-16 - 2025-07-15)
- **Goal:** Performance optimization and stability.
- **Key Activity:** Load testing the telemetry imports and refining the multi-tenant isolation logic.
- **Dependency:** Successful pilot user onboarding.
- **Milestone 3:** Performance Benchmarks Met (2025-07-15).

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2024-11-02)
- *Attendees:* Fleur, Dina, Adaeze, Sanjay.
- Rust backend decided.
- Hexagonal architecture approved.
- Adaeze asks about UI for a feature that doesn't exist yet.
- Dina ignores the question.
- Fleur reminds team about bootstrapping budget.

### Meeting 2: Billing Sprint Review (2024-12-15)
- *Attendees:* Fleur, Dina, Sanjay.
- Billing module "done."
- No tests.
- Sanjay asks if this is safe.
- Dina says "it works in dev."
- Fleur approves deployment to staging despite lack of tests to meet the internal demo date.

### Meeting 3: Budget Crisis & Blockers (2025-01-10)
- *Attendees:* Fleur, Adaeze, Sanjay.
- (Dina absent).
- Redis tool purchase still pending.
- Rate limiting is blocked.
- Discussion on potential 30% budget cut.
- Fleur suggests escalating to steering committee.
- Adaeze mentions the sponsor is leaving; no one knows who takes over.

---

## 11. BUDGET BREAKDOWN

Since the project is currently bootstrapping, the "Budget" refers to the allocated internal resource cost and the pending requests for tooling.

| Category | Annualized Cost (Est.) | Notes |
| :--- | :--- | :--- |
| **Personnel** | $780,000 | 6 Full-time employees (Blended rate). |
| **Infrastructure** | $12,000 | Cloudflare Workers, R2, and Durable Objects. |
| **Tools** | $8,500 | LaunchDarkly (Enterprise), GitHub Actions. |
| **Pending Purchase** | $4,000 | Redis-compatible Distributed Cache (Blocked). |
| **Contingency** | $25,000 | Reserved for emergency penetration testing. |
| **TOTAL** | **$829,500** | *Note: Currently unfunded; absorbing into OpEx.* |

---

## 12. APPENDICES

### Appendix A: Rust-to-SQL Mapping Details
To ensure the "Multi-tenant isolation" is maintained, the following Rust trait is implemented across all repositories:

```rust
pub trait TenantAwareRepository<T> {
    fn find_by_tenant(&self, tenant_id: Uuid, id: Uuid) -> Result<T, RepositoryError>;
    fn save_for_tenant(&self, tenant_id: Uuid, entity: T) -> Result<(), RepositoryError>;
}
```
All implementations of this trait must use parameterized queries to prevent SQL injection and ensure the `tenant_id` is always verified against the session context.

### Appendix B: Telemetry Format Signatures (Magic Numbers)
The `AutoDetect` service uses the following byte sequences to identify files:
- **JSON:** Starts with `0x7B` (`{`) or `0x5B` (`[`).
- **CSV:** Heuristic check for commas in the first 100 bytes.
- **ARINC 429 (Binary):** Look for the specific parity bit patterns and label headers at the start of the stream.
- **Custom Duskfall Binary:** Starts with the sequence `0x44 0x55 0x53 0x4B` ("DUSK").