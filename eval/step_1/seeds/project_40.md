# PROJECT SPECIFICATION DOCUMENT: DRIFT
**Document Version:** 1.0.4  
**Status:** Baseline Approved  
**Project Code:** TA-DRIFT-2026  
**Company:** Tundra Analytics  
**Date:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Drift" is a strategic e-commerce marketplace initiative developed by Tundra Analytics, specifically tailored for the education industry. Unlike traditional retail marketplaces, Drift is designed as a strategic partnership integration. The core objective is to facilitate the exchange of educational resources, certifications, and instructional tooling through a highly scalable, secure, and performant platform. A critical component of the project is the synchronization with a third-party external partner's API, meaning the development timeline must remain flexible to align with the partner's release schedule.

### 1.2 Business Justification
Tundra Analytics identifies a significant gap in the education sector: the lack of a secure, FedRAMP-compliant marketplace where government-backed educational institutions can procure specialized analytics tools and curricula. Current solutions lack the necessary data isolation and security auditing required for government contracts. By building Drift, Tundra Analytics positions itself as the primary infrastructure provider for this niche, leveraging its expertise in data analytics to provide a curated marketplace.

The strategic partnership integration is the primary value driver. By syncing with the external partner’s API, Drift will gain immediate access to a pre-existing catalog of high-value educational assets, reducing the "cold start" problem typical of new marketplaces.

### 1.3 ROI Projection
With a total budget of $800,000 over a 6-month build, Tundra Analytics projects a Return on Investment (ROI) based on the following metrics:
*   **Direct Revenue:** A transaction fee of 5% on all marketplace sales. With an estimated initial Gross Merchandise Volume (GMV) of $2M in the first year post-beta, the project expects $100,000 in direct fees.
*   **Indirect Revenue:** The FedRAMP authorization acts as a moat, allowing Tundra Analytics to charge a premium "Security Compliance Fee" to vendors, estimated at $5,000 per vendor per year.
*   **Operational Efficiency:** A projected 50% reduction in manual processing time for end users (from onboarding to deployment), which reduces the cost of customer success operations by an estimated $40,000 annually.
*   **Projected Break-even:** Month 14 post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design Philosophy
Drift utilizes a modern, high-performance stack designed for the "edge." Given the global nature of education and the need for low-latency access to materials, the architecture moves computation as close to the user as possible using Cloudflare Workers.

**The Stack:**
*   **Backend:** Rust (compiled to WebAssembly for Cloudflare Workers). Rust was chosen for its memory safety and performance, which is critical for meeting the 10x capacity requirement.
*   **Frontend:** React (deployed via a micro-frontend architecture). This allows different parts of the marketplace (e.g., User Profile, Catalog, Checkout) to be developed and deployed independently.
*   **Database:** SQLite for edge (via Cloudflare D1). This provides local-first data access with global synchronization.
*   **Orchestration:** Cloudflare Workers.

### 2.2 Architecture Diagram (ASCII)

```text
[ USER BROWSER ] <--- HTTPS/WSS ---> [ CLOUDFLARE EDGE ]
                                            |
                                            v
                          +---------------------------------------+
                          |       CLOUDFLARE WORKERS (RUST/WASM)   |
                          +---------------------------------------+
                                /           |             \
             (Micro-Frontend A)    (Micro-Frontend B)    (Micro-Frontend C)
             [ Catalog UI ]         [ User Dashboard ]    [ Admin Console ]
                                            |
                                            v
                          +---------------------------------------+
                          |       DATA & INTEGRATION LAYER        |
                          +---------------------------------------+
                                /           |             \
                    [ SQLite/D1 ]    [ LaunchDarkly ]   [ External API ]
                    (Edge Storage)    (Feature Flags)    (Partner Sync)
                                            |
                                            v
                          +---------------------------------------+
                          |      FEDRAMP COMPLIANCE LAYER          |
                          | (Audit Logs / Tamper-Evident Storage)  |
                          +---------------------------------------+
```

### 2.3 Micro-Frontend Strategy
The frontend is split into three primary ownership areas:
1.  **Discovery:** Search, Filtering, Product Pages.
2.  **Transaction:** Cart, Checkout, Payment Processing.
3.  **Management:** User Profile, Order History, Vendor Dashboard.

Each module is deployed as an independent bundle. This prevents a bug in the "User Profile" section from crashing the "Checkout" flow and allows the 2-person team to deploy updates to specific features without a full site rebuild.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox (Priority: Medium | Status: In Design)
The Drift API allows third-party educational institutions to automate the procurement of assets. To ensure stability, the API must support semantic versioning (e.g., `/v1/`, `/v2/`).

**Functional Requirements:**
*   **Versioning:** Every request must specify a version header. If omitted, it defaults to the oldest supported stable version to prevent breaking changes for legacy clients.
*   **Sandbox Environment:** A mirrored environment (sandbox.drift.tundra.io) where users can test API calls without spending real credits or affecting production data. Sandbox data is wiped every 30 days.
*   **Developer Portal:** A self-service portal where users can generate API keys and view documentation.

**Technical Implementation:**
The Rust backend will implement a routing layer that intercepts the version header and directs the request to the appropriate controller logic. The sandbox will utilize a separate D1 database instance to ensure total isolation from production data.

### 3.2 Audit Trail Logging with Tamper-Evident Storage (Priority: Medium | Status: In Design)
Due to FedRAMP requirements, every state-changing action in the marketplace must be logged in a way that is cryptographically verifiable.

**Functional Requirements:**
*   **Immutability:** Logs cannot be deleted or modified, even by administrators.
*   **Hashing:** Each log entry must contain a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody.
*   **Coverage:** Must capture all API key rotations, payment status changes, and data access requests for government users.

**Technical Implementation:**
We will implement a "Write-Once-Read-Many" (WORM) storage pattern. Logs are written to a dedicated SQLite table where the `UPDATE` and `DELETE` permissions are stripped at the database level. A daily background worker will sign the day's log hash and store the root hash in a secure external vault.

### 3.3 A/B Testing Framework (Priority: Medium | Status: Blocked)
The A/B testing framework is designed to be baked directly into the LaunchDarkly feature flag system to determine which UI variants drive higher conversion.

**Functional Requirements:**
*   **Variant Assignment:** Users are randomly assigned to a "Control" or "Test" group based on their `userId`.
*   **Metric Tracking:** The system must track the conversion rate of the test variant vs. the control.
*   **Automatic Rollback:** If a variant causes a >5% increase in 5xx errors, the flag must automatically toggle off.

**Current Blocker:** The team is waiting for the LaunchDarkly Enterprise API integration keys to be approved by the legal department for the specific government-cloud region.

### 3.4 API Rate Limiting and Usage Analytics (Priority: Critical | Status: In Review)
This is a launch blocker. Without rate limiting, the edge workers are vulnerable to DDoS attacks and uncontrolled costs.

**Functional Requirements:**
*   **Tiered Limits:** 
    *   *Free Tier:* 100 requests/hour.
    *   *Professional Tier:* 5,000 requests/hour.
    *   *Enterprise Tier:* 50,000 requests/hour.
*   **Burst Handling:** Allow short bursts of 10 requests/second.
*   **Analytics Dashboard:** Vendors must be able to see their API usage spikes in real-time.

**Technical Implementation:**
We will use a "Token Bucket" algorithm implemented in Cloudflare Workers KV (Key-Value store). The KV store will track the current token count for each API key. If the bucket is empty, the system returns a `429 Too Many Requests` response with a `Retry-After` header.

### 3.5 Multi-Tenant Data Isolation (Priority: Medium | Status: In Progress)
Drift must support multiple educational organizations on shared infrastructure while ensuring that Org A can never see Org B's data.

**Functional Requirements:**
*   **Logical Isolation:** Every table must contain an `org_id` column.
*   **Row-Level Security (RLS):** The application layer must automatically append `WHERE org_id = ?` to every query.
*   **Tenant Sharding:** While infrastructure is shared, high-volume tenants can be migrated to their own dedicated D1 database instance if required.

**Technical Implementation:**
A middleware wrapper in Rust will extract the `org_id` from the JWT (JSON Web Token) provided in the request. This ID is then passed as a mandatory parameter to all database repository methods, making it programmatically impossible to query data without an organization filter.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under `api.drift.tundra.io`. All requests require a `X-Drift-API-Key` header.

### 4.1 GET /v1/products
Retrieve a list of available educational assets.
*   **Query Params:** `category` (string), `price_max` (float), `page` (int).
*   **Response (200 OK):**
    ```json
    {
      "data": [
        {"id": "prod_01", "name": "Advanced Calculus Course", "price": 49.99, "provider": "EduCorp"}
      ],
      "pagination": {"next": "/v1/products?page=2"}
    }
    ```

### 4.2 POST /v1/orders
Create a new purchase.
*   **Request Body:**
    ```json
    {
      "product_id": "prod_01",
      "quantity": 1,
      "payment_method_id": "pm_9988"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "order_id": "ord_5544", "status": "pending", "total": 49.99
    }
    ```

### 4.3 GET /v1/account/usage
Get current API quota usage.
*   **Response (200 OK):**
    ```json
    {
      "tier": "Professional",
      "used": 1200,
      "limit": 5000,
      "reset_at": "2026-08-20T00:00:00Z"
    }
    ```

### 4.4 POST /v1/sandbox/test-payment
Simulate a payment for testing.
*   **Request Body:** `{"amount": 10.00, "currency": "USD"}`
*   **Response (200 OK):** `{"status": "simulated_success", "transaction_id": "txn_test_123"}`

### 4.5 GET /v1/audit/logs
Retrieve tamper-evident logs for the current organization.
*   **Query Params:** `start_date` (ISO8601), `end_date` (ISO8601).
*   **Response (200 OK):**
    ```json
    {
      "logs": [
        {"timestamp": "2026-01-01T10:00Z", "action": "API_KEY_ROTATED", "hash": "a1b2c3d4..."}
      ]
    }
    ```

### 4.6 PATCH /v1/products/{id}
Update product details (Vendor only).
*   **Request Body:** `{"price": 59.99}`
*   **Response (200 OK):** `{"id": "prod_01", "updated": true}`

### 4.7 GET /v1/org/config
Get tenant-specific configuration.
*   **Response (200 OK):**
    ```json
    {
      "org_name": "University of State",
      "compliance_level": "FedRAMP-High",
      "region": "us-east-1"
    }
    ```

### 4.8 DELETE /v1/account/api-key
Revoke an existing API key.
*   **Request Body:** `{"key_id": "key_8877"}`
*   **Response (204 No Content):** Empty.

---

## 5. DATABASE SCHEMA

The system uses SQLite (Cloudflare D1). All timestamps are stored as ISO8601 strings to mitigate the current technical debt of mixed date formats.

### 5.1 Tables and Relationships

1.  **`organizations`**
    *   `id` (UUID, PK)
    *   `name` (TEXT)
    *   `compliance_tier` (TEXT) - e.g., 'FedRAMP'
    *   `created_at` (TEXT)

2.  **`users`**
    *   `id` (UUID, PK)
    *   `org_id` (UUID, FK -> organizations.id)
    *   `email` (TEXT, Unique)
    *   `role` (TEXT) - e.g., 'admin', 'student'

3.  **`api_keys`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> users.id)
    *   `hashed_key` (TEXT)
    *   `tier` (TEXT) - 'Free', 'Pro', 'Enterprise'
    *   `last_used` (TEXT)

4.  **`products`**
    *   `id` (UUID, PK)
    *   `vendor_id` (UUID, FK -> organizations.id)
    *   `title` (TEXT)
    *   `description` (TEXT)
    *   `price` (DECIMAL)
    *   `version` (TEXT)

5.  **`orders`**
    *   `id` (UUID, PK)
    *   `buyer_id` (UUID, FK -> users.id)
    *   `product_id` (UUID, FK -> products.id)
    *   `amount` (DECIMAL)
    *   `status` (TEXT) - 'pending', 'completed', 'refunded'
    *   `created_at` (TEXT)

6.  **`audit_logs`**
    *   `id` (INTEGER, PK)
    *   `org_id` (UUID, FK -> organizations.id)
    *   `action` (TEXT)
    *   `payload` (JSON)
    *   `previous_hash` (TEXT)
    *   `current_hash` (TEXT)
    *   `timestamp` (TEXT)

7.  **`rate_limits`**
    *   `api_key_id` (UUID, PK, FK -> api_keys.id)
    *   `current_tokens` (INTEGER)
    *   `last_refill` (TEXT)

8.  **`feature_flags`**
    *   `flag_key` (TEXT, PK)
    *   `enabled` (BOOLEAN)
    *   `variant` (TEXT) - 'A' or 'B'

9.  **`external_sync_state`**
    *   `resource_id` (TEXT, PK)
    *   `external_hash` (TEXT)
    *   `last_synced` (TEXT)

10. **`tenants_config`**
    *   `org_id` (UUID, PK, FK -> organizations.id)
    *   `custom_domain` (TEXT)
    *   `auth_provider` (TEXT)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Drift utilizes three distinct environments to ensure stability and FedRAMP compliance.

| Environment | Purpose | Infrastructure | Data Source |
| :--- | :--- | :--- | :--- |
| **Development** | Active feature coding | CF Workers (Dev Namespace) | Dev SQLite (Mock Data) |
| **Staging** | QA and User Acceptance | CF Workers (Staging Namespace) | Staging SQLite (Anonymized) |
| **Production** | Live traffic | CF Workers (Prod Namespace) | Production SQLite (Encrypted) |

### 6.2 Deployment Pipeline
1.  **CI/CD:** GitHub Actions triggers on push to `main`.
2.  **Canary Release:** New code is deployed to 5% of users via Cloudflare Workers' "Deployment" feature.
3.  **Health Check:** System monitors for 5xx errors for 10 minutes.
4.  **Full Rollout:** If health checks pass, the version is promoted to 100% of traffic.
5.  **Feature Gating:** All new features are wrapped in LaunchDarkly flags, allowing the team to disable a feature instantly without a full redeploy.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (Rust)
Focuses on the business logic within the Rust modules.
*   **Tooling:** `cargo test`.
*   **Coverage Target:** 80% of the core API logic.
*   **Focus:** Token bucket calculations, hash chain validation for audit logs, and permission checks.

### 7.2 Integration Testing
Focuses on the interaction between the Rust backend and the SQLite D1 database.
*   **Tooling:** `wrangler dev` with a local SQLite instance.
*   **Scenario:** "Create Product $\rightarrow$ Purchase Product $\rightarrow$ Verify Audit Log Entry."

### 7.3 End-to-End (E2E) Testing (React)
Focuses on the critical user journeys.
*   **Tooling:** Playwright.
*   **Key Journeys:**
    1.  Vendor onboarding and API key generation.
    2.  Customer searching for a product and completing a checkout.
    3.  Admin reviewing audit logs for a specific organization.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key Architect leaving in 3 months | High | Critical | Create a "Fallback Architecture" document immediately. Document all undocumented Rust macros. Cross-train Luna Costa on the backend. |
| **R2** | Performance 10x current capacity | Medium | High | Raise as a blocker in the next board meeting. Propose an increase in infrastructure budget for dedicated Cloudflare Workers plans. |
| **R3** | Partner API timeline slippage | High | Medium | Design the synchronization layer as an adapter pattern, allowing for a "mock partner" to be used for internal development. |
| **R4** | FedRAMP Audit Failure | Low | Critical | Engage a third-party compliance consultant for a pre-audit gap analysis in Month 4. |

---

## 9. TIMELINE

### 9.1 Phase Breakdown

**Phase 1: Foundation (Month 1-2)**
*   Set up Cloudflare Workers and D1 Schema.
*   Implement Basic Multi-tenancy logic.
*   **Dependency:** Initial API spec from external partner.

**Phase 2: Core Marketplace (Month 3-4)**
*   Build Product Catalog and Checkout flows.
*   Implement Rate Limiting (Critical Path).
*   Develop Audit Trail system.
*   **Dependency:** Legal approval for LaunchDarkly keys.

**Phase 3: Hardening & Sync (Month 5-6)**
*   Integrate External Partner API.
*   Final FedRAMP hardening and Security Review.
*   Beta testing with 10 pilot users.

### 9.2 Key Milestones
*   **2026-08-15:** First paying customer onboarded.
*   **2026-10-15:** Performance benchmarks met (10x capacity validation).
*   **2026-12-15:** External beta completion (10 pilot users).

---

## 10. MEETING NOTES

*Note: The following are excerpts from the 200-page shared running document. Note that this document is currently unsearchable.*

**Meeting 2023-11-05: Architecture Sync**
*   **Attendees:** Rosa, Luna, Meera.
*   **Discussion:** Meera raised concerns that using SQLite at the edge might lead to data consistency issues during high-concurrency writes. Rosa argued that D1's eventual consistency is acceptable for product catalogs but not for audit logs.
*   **Decision:** Use a synchronous write-ahead log for the `audit_logs` table and an asynchronous cache for product views.
*   **Action Item:** Luna to prototype the micro-frontend shells.

**Meeting 2023-12-12: The "Date Format" Crisis**
*   **Attendees:** Rosa, Luna, Meera, Ingrid.
*   **Discussion:** Ingrid pointed out that the codebase currently uses Unix timestamps, ISO8601, and "MM-DD-YYYY" in different modules. This is causing `Panic` errors in the Rust backend.
*   **Decision:** No time for a full migration. Implement a `DateNormalization` trait in Rust that converts all incoming formats to ISO8601 before database insertion.
*   **Action Item:** Meera to write the normalization trait.

**Meeting 2024-01-20: Budget and Performance**
*   **Attendees:** Rosa, Tundra Analytics Board.
*   **Discussion:** Rosa presented the current benchmarks. The system is hitting a wall at 1/10th of the required capacity for government-scale traffic.
*   **Decision:** The board refused additional infrastructure budget. Rosa declared this a "Blocker" for the 10x capacity requirement.
*   **Action Item:** Rosa to draft a proposal for "Cold Storage" of old audit logs to save on D1 costs.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $550,000 | Salaries for Rosa, Luna, Meera, and Ingrid (6 months). |
| **Infrastructure** | $120,000 | Cloudflare Workers, D1, and KV storage fees. |
| **Tools** | $30,000 | LaunchDarkly Enterprise, Playwright Cloud, GitHub Enterprise. |
| **Compliance** | $50,000 | FedRAMP certification fees and 3rd party audit. |
| **Contingency** | $50,000 | Emergency buffer for partner API changes. |

---

## 12. APPENDICES

### Appendix A: Date Normalization Logic
To address the technical debt of three different date formats, the following Rust pseudo-logic is implemented in the `normalization` crate:

```rust
pub trait NormalizeDate {
    fn to_iso8601(&self) -> String;
}

impl NormalizeDate for IncomingRequest {
    fn to_iso8601(&self) -> String {
        if self.date.contains("-") && self.date.len() == 10 {
            // Handle MM-DD-YYYY
            convert_mdy_to_iso(&self.date)
        } else if self.date.chars().all(|c| c.is_numeric()) {
            // Handle Unix Timestamp
            convert_unix_to_iso(&self.date)
        } else {
            // Assume ISO8601
            self.date.clone()
        }
    }
}
```

### Appendix B: FedRAMP Data Isolation Checklist
The following checks must be passed before the 2026-12-15 Beta:
1.  **Encryption at Rest:** All D1 data encrypted using AES-256.
2.  **Encryption in Transit:** TLS 1.3 mandatory for all API calls.
3.  **Access Control:** MFA required for all admin access to the Cloudflare Console.
4.  **Auditability:** Every `DELETE` or `UPDATE` operation must have a corresponding entry in `audit_logs` with a verified hash.
5.  **Tenant Leakage Test:** Automated script that attempts to query Org B's data using Org A's API key (Must return 403).