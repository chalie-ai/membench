# Project Specification Document: Project Canopy
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/R&D  
**Confidentiality Level:** Internal - High  
**Company:** Coral Reef Solutions  

---

## 1. Executive Summary

### 1.1 Project Vision
Project "Canopy" is a moonshot R&D initiative commissioned by Coral Reef Solutions to disrupt the intersection of e-commerce and fintech. While traditional marketplaces focus on the transaction of goods, Canopy aims to build a highly performant, secure, and collaborative ecosystem where financial instruments and high-value digital assets can be traded with the agility of a modern SaaS platform. 

The project is categorized as a "moonshot" due to its aggressive technical stack (Rust/Cloudflare Workers) and its ambition to implement complex collaborative features typically reserved for document editors, rather than e-commerce platforms. Because it is an R&D venture, the Return on Investment (ROI) is currently speculative; however, the project enjoys strong executive sponsorship, providing the team with the creative freedom to experiment with cutting-edge architecture.

### 1.2 Business Justification
The primary business driver for Canopy is the ability to capture a "high-velocity" segment of the fintech market. Current competitors are bogged down by legacy monoliths and slow deployment cycles. By utilizing a clean monolith architecture deployed at the edge, Coral Reef Solutions can offer latency levels that are virtually unmatched in the industry. 

Furthermore, the integration of a real-time collaborative environment allows B2B buyers and sellers to negotiate contracts, modify order parameters, and finalize deal structures in a shared digital space—eliminating the friction of email chains and fragmented communication. This "Collaborative Commerce" model is the core value proposition.

### 1.3 ROI Projection
Given the nature of an R&D project, ROI is projected across three horizons:
1.  **Horizon 1 (Year 1):** Technical Validation. Success is defined by the successful launch of the MVP and the validation of the Rust/SQLite edge architecture. ROI is measured in "knowledge capital."
2.  **Horizon 2 (Year 2):** Market Penetration. Targeted acquisition of 50 high-net-worth B2B merchants. Projected Revenue: $200k - $500k ARR via transaction fees.
3.  **Horizon 3 (Year 3):** Scale. Expansion into full fintech suite integration. Projected ROI: 300% of initial R&D investment based on a projected $2M GMV (Gross Merchandise Volume) flowing through the platform.

### 1.4 Budgetary Constraints
The budget is strictly capped at $150,000. This is a "shoestring" budget for a project of this complexity, meaning every dollar is scrutinized. Personnel costs are minimized through the use of a lean, veteran team and a single contractor. Infrastructure costs are kept low by leveraging Cloudflare’s free/low-tier edge capabilities.

---

## 2. Technical Architecture

### 2.1 The Stack
Canopy utilizes a modern, high-performance stack designed for minimal latency and maximum type safety.

*   **Backend:** Rust (Actix-web / Warp) – Chosen for memory safety and raw performance.
*   **Frontend:** React (TypeScript) – For a responsive, component-based UI.
*   **Database (Edge):** SQLite – Distributed via Cloudflare D1 for low-latency data access at the edge.
*   **Runtime/Deployment:** Cloudflare Workers – Serverless execution to ensure global availability.
*   **Security:** ISO 27001 certified environment. All data at rest is encrypted via AES-256, and all transit is forced via TLS 1.3.

### 2.2 Architecture Pattern: The Clean Monolith
Unlike microservices, which introduce network overhead and complexity, Canopy employs a "Clean Monolith." The codebase is a single repository, but it is strictly partitioned into modules. Each module (e.g., `billing`, `collaboration`, `inventory`) communicates via internal interfaces. This allows the team to maintain a simple deployment pipeline while retaining the ability to split the monolith into microservices in the future if the project scales.

### 2.3 System Diagram (ASCII)
```text
[ Client Browser ] <--- HTTPS/WSS ---> [ Cloudflare Edge ]
                                              |
                    __________________________|__________________________
                   |                          |                         |
          [ React Frontend ]         [ Cloudflare Worker ]      [ Cloudflare R2 ]
          (Client Side UI)           (Rust Runtime/WASM)        (File Storage)
                                              |
                                     _________|_________
                                    |                   |
                          [ SQLite (D1) ]       [ Virus Scan Service ]
                          (Edge Data Store)     (External API/Sandbox)
                                    |
                          [ ISO 27001 Boundary ]
```

### 2.4 Deployment Model
Deployment is currently manual. Zia Park (DevOps) handles all pushes to the production environment. While this creates a "bus factor of 1" (a significant risk), it ensures that every release is meticulously vetted for ISO 27001 compliance before hitting production.

---

## 3. Detailed Feature Specifications

### 3.1 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Progress
**Description:** 
This feature enables multiple users (e.g., a buyer and a seller) to edit a "Deal Sheet" simultaneously. The Deal Sheet contains pricing, quantities, and shipping terms. Unlike a standard form, this is a live document.

**Technical Implementation:**
The system uses a Conflict-free Replicated Data Type (CRDT) approach, specifically utilizing an implementation of the LWW-Element-Set (Last-Write-Wins). Because the backend is Rust, the team is implementing a custom WASM-based synchronization engine that runs on the Cloudflare Worker.

**User Workflow:**
1. User A opens a Deal Sheet.
2. User B opens the same Deal Sheet.
3. User A changes the "Unit Price" to $100.00.
4. User B simultaneously changes it to $95.00.
5. The system resolves the conflict based on the timestamp of the operation, ensuring both users eventually see the same value without refreshing the page.

**Acceptance Criteria:**
- Latency for updates must be <100ms.
- No data loss during concurrent edits by 3+ users.
- Visual indicators showing who is currently editing which field.

### 3.2 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Review
**Description:** 
Users must be able to upload contracts, product images, and compliance documents. Given the fintech nature of the project, security is paramount. No file can be served to another user without being scanned for malware.

**Technical Implementation:**
Files are uploaded to Cloudflare R2 (S3-compatible storage). Upon upload, a trigger invokes a Rust-based worker that sends the file hash/stream to a virus scanning sandbox (integrating with a third-party API like VirusTotal or a private ClamAV instance). Only after the "Clean" signal is received is the file tagged as `public` and cached via the Cloudflare CDN.

**User Workflow:**
1. User uploads `contract_v1.pdf`.
2. File is placed in a `quarantine` bucket.
3. Scanning service analyzes the file.
4. File is moved to `production` bucket and a signed URL is generated.
5. Other participants can download the file via the CDN.

**Acceptance Criteria:**
- Files up to 50MB supported.
- Scanning must complete within 5 seconds.
- Unauthorized access to quarantined files must be blocked.

### 3.3 Customer-Facing API with Versioning and Sandbox
**Priority:** Low (Nice to have) | **Status:** In Progress
**Description:** 
To attract institutional clients, Canopy provides a REST API allowing them to programmatically manage listings and orders.

**Technical Implementation:**
The API is versioned via the URL path (e.g., `/v1/orders`). A separate "Sandbox" environment is provided, utilizing a mirrored SQLite database that does not affect production data. This allows clients to test their integrations without risking financial transactions.

**API Design:**
The API utilizes JSON for requests and responses. Rate limiting is enforced at the edge using Cloudflare’s `KV` store to track requests per API key.

**Acceptance Criteria:**
- Full documentation via Swagger/OpenAPI.
- Separation of Sandbox and Production keys.
- Versioning allows v1 to remain stable while v2 is developed.

### 3.4 A/B Testing Framework Integrated into Feature Flags
**Priority:** Low (Nice to have) | **Status:** In Progress
**Description:** 
Rather than a separate tool, the A/B testing framework is baked into the feature flag system. This allows the team to toggle features on/off for specific percentages of the user base.

**Technical Implementation:**
Feature flags are stored in a global configuration table. The Rust backend evaluates the user's ID against a hash function to determine which "bucket" (A or B) the user falls into.

**Example Scenario:**
- Feature: "New Checkout Flow."
- Config: `checkout_v2: {enabled: true, rollout: 20%}`.
- User ID `123` hashes to `0.15` $\rightarrow$ Sees New Flow.
- User ID `456` hashes to `0.67` $\rightarrow$ Sees Old Flow.

**Acceptance Criteria:**
- Ability to change rollout percentage without redeploying code.
- No flickering of UI components during page load.

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low (Nice to have) | **Status:** Blocked
**Description:** 
A sophisticated engine allowing users to create "If-This-Then-That" (IFTTT) rules for their marketplace (e.g., "If order > $10,000, then notify VP of Product").

**Technical Implementation:**
The engine would use a Directed Acyclic Graph (DAG) to process rules. The "Visual Rule Builder" would be a React-based drag-and-drop interface where nodes represent triggers and actions.

**Current Blocker:** 
There is a fundamental disagreement between Idris (Product) and the Engineering lead regarding the complexity of the rule language. Idris wants a "no-code" experience, while Engineering argues for a simplified JSON-based logic system to prevent performance degradation at the edge.

**Acceptance Criteria (Once Unblocked):**
- Users can create a rule and trigger a notification.
- Rule execution time < 200ms.
- Visual builder reflects the actual logic being executed.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1/`. Base URL: `https://api.canopy.coralreef.solutions`

### 4.1 `GET /products`
**Description:** Retrieves a paginated list of available marketplace items.
- **Request:** `?page=1&limit=20&category=fintech`
- **Response (200 OK):**
```json
{
  "data": [
    {"id": "prod_01", "name": "Digital Bond A", "price": 1200.00, "currency": "USD"}
  ],
  "pagination": { "total": 150, "next": 2 }
}
```

### 4.2 `POST /orders`
**Description:** Creates a new order request.
- **Request:**
```json
{
  "product_id": "prod_01",
  "quantity": 1,
  "buyer_id": "user_99"
}
```
- **Response (201 Created):**
```json
{ "order_id": "ord_555", "status": "pending_review" }
```

### 4.3 `PATCH /deals/{deal_id}`
**Description:** Updates a specific field in a collaborative deal sheet.
- **Request:**
```json
{ "field": "unit_price", "value": 95.00, "timestamp": "2025-05-01T10:00:00Z" }
```
- **Response (200 OK):**
```json
{ "status": "synced", "version": 14 }
```

### 4.4 `POST /upload`
**Description:** Uploads a file for virus scanning.
- **Request:** `multipart/form-data` (file, description)
- **Response (202 Accepted):**
```json
{ "file_id": "file_abc", "status": "scanning" }
```

### 4.5 `GET /upload/status/{file_id}`
**Description:** Checks if a file has passed virus scanning.
- **Response (200 OK):**
```json
{ "file_id": "file_abc", "status": "clean", "url": "https://cdn.canopy.../file.pdf" }
```

### 4.6 `GET /user/profile`
**Description:** Returns the authenticated user's profile.
- **Response (200 OK):**
```json
{ "id": "user_99", "role": "merchant", "iso_certified": true }
```

### 4.7 `POST /api/sandbox/reset`
**Description:** Resets the sandbox environment for a specific API key.
- **Response (200 OK):**
```json
{ "message": "Sandbox environment purged successfully." }
```

### 4.8 `GET /admin/health`
**Description:** System health check for the Rust runtime.
- **Response (200 OK):**
```json
{ "status": "healthy", "uptime": "14d 2h", "memory_usage": "42MB" }
```

---

## 5. Database Schema

Canopy uses SQLite via Cloudflare D1. The schema is designed for high read-speeds.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID) | `email`, `password_hash`, `role`, `created_at` | One-to-Many with `orders` |
| `products` | `product_id` (UUID) | `name`, `description`, `base_price`, `stock` | One-to-Many with `order_items` |
| `orders` | `order_id` (UUID) | `buyer_id`, `total_amount`, `status`, `created_at` | Many-to-One with `users` |
| `order_items` | `item_id` (UUID) | `order_id`, `product_id`, `quantity`, `price_at_purchase` | FK to `orders`, `products` |
| `deal_sheets` | `deal_id` (UUID) | `order_id`, `current_version`, `last_modified` | One-to-One with `orders` |
| `deal_edits` | `edit_id` (UUID) | `deal_id`, `field_name`, `value`, `user_id`, `timestamp` | Many-to-One with `deal_sheets` |
| `files` | `file_id` (UUID) | `owner_id`, `filename`, `scan_status`, `r2_path` | Many-to-One with `users` |
| `feature_flags` | `flag_id` (PK) | `flag_name`, `is_enabled`, `rollout_percentage` | N/A |
| `api_keys` | `key_id` (PK) | `user_id`, `key_hash`, `environment` (prod/sandbox) | Many-to-One with `users` |
| `audit_logs` | `log_id` (PK) | `user_id`, `action`, `timestamp`, `ip_address` | Many-to-One with `users` |

### 5.2 Relational Logic
- A `User` can place multiple `Orders`.
- An `Order` contains multiple `OrderItems`.
- Each `Order` can have exactly one `DealSheet` for collaborative negotiation.
- `DealEdits` track every single change to a `DealSheet` to allow the CRDT conflict resolution to reconstruct the state.
- `AuditLogs` are immutable and track all ISO 27001 sensitive actions (e.g., password changes, file uploads).

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
To maintain the $150,000 budget, the team uses a condensed environment strategy.

#### Development (Dev)
- **Purpose:** Local iteration.
- **Host:** Localhost / Wrangler (Cloudflare CLI).
- **Database:** Local SQLite file.
- **Access:** Individual developer machines.

#### Staging (Stage)
- **Purpose:** Integration testing and stakeholder review.
- **Host:** `staging.canopy.coralreef.solutions` (Cloudflare Worker).
- **Database:** Cloudflare D1 (Staging Instance).
- **Access:** Team members and Idris Nakamura.

#### Production (Prod)
- **Purpose:** Live end-user access.
- **Host:** `app.canopy.coralreef.solutions` (Cloudflare Worker).
- **Database:** Cloudflare D1 (Production Instance).
- **Access:** Public (Authenticated).
- **Security:** ISO 27001 strict lockdown.

### 6.2 Deployment Pipeline
1. **Commit:** Developer pushes code to GitHub.
2. **CI:** GitHub Actions runs `cargo test` and `npm test`.
3. **Manual Trigger:** Zia Park (DevOps) manually triggers the `wrangler deploy` command.
4. **Verification:** Zia performs a smoke test in Staging before promoting the build to Production.

**Risk Note:** The "Bus Factor" is currently 1. If Zia Park is unavailable, deployments stop. The mitigation plan is to document the deployment scripts in the Internal Wiki.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Backend (Rust):** Every module must have associated `#[cfg(test)]` blocks. Focus is on the CRDT conflict resolution logic and the pricing calculation engine.
- **Frontend (React):** Jest and React Testing Library are used for component-level verification.

### 7.2 Integration Testing
- **API Tests:** Postman collections are used to verify the interaction between the Rust backend and the SQLite database.
- **Flow Tests:** Testing the full lifecycle of a "Deal Sheet" from creation $\rightarrow$ collaboration $\rightarrow$ order finalization.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical paths only (User Login, File Upload, Payment Processing).
- **Environment:** E2E tests run against the Staging environment before every production release.

### 7.4 Security Testing
- **Static Analysis:** Using `cargo audit` to find vulnerabilities in Rust dependencies.
- **Penetration Testing:** Quarterly manual review of the ISO 27001 boundary to ensure no data leaks from the D1 database.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for fintech may change. | High | High | Hire a part-time legal contractor to review specs monthly; build modular logic for tax/compliance. |
| R-02 | Primary vendor (Cloudflare) EOL for a specific product. | Medium | High | Document workarounds for SQLite edge storage and maintain a migration path to PostgreSQL if needed. |
| R-03 | Bus factor of 1 for DevOps (Zia Park). | High | Medium | Create detailed deployment manuals and cross-train Aaliya Moreau on basic deployment scripts. |
| R-04 | Design disagreement between Product & Eng. | High | Medium | Schedule a dedicated "Design Lock" workshop; Idris has final sign-off on UX, Eng on Performance. |
| R-05 | Technical Debt: Hardcoded config in 40+ files. | High | Low | Implement a centralized `config.toml` and use the `config` crate in Rust to load environment variables. |

**Impact Matrix:**
- **High/High:** Critical. Requires immediate executive attention.
- **High/Medium:** Warning. Requires active mitigation.
- **Medium/Low:** Monitor. Address during "tech debt" sprints.

---

## 9. Timeline and Milestones

### 9.1 Phases
- **Phase 1: Foundation (Now - April 2025):** Setup of Rust/D1 architecture, ISO 27001 environment hardening, and core API development.
- **Phase 2: Collaboration (April 2025 - June 2025):** Implementation of CRDTs, real-time sockets, and the file upload system.
- **Phase 3: Polish & Pivot (June 2025 - August 2025):** Sandbox API, A/B testing framework, and final stakeholder sign-off.

### 9.2 Key Milestones

| Milestone | Deliverable | Target Date | Dependencies |
| :--- | :--- | :--- | :--- |
| M1: Architecture Review | Technical Sign-off | 2025-04-15 | Rust Module Boundaries defined |
| M2: Stakeholder Demo | Functional MVP | 2025-06-15 | Collaboration Feature $\rightarrow$ Review |
| M3: Production Launch | Live Public Site | 2025-08-15 | ISO 27001 Audit $\rightarrow$ Pass |

---

## 10. Meeting Notes (Slack Archive)

*Note: Per company policy, formal minutes are not kept. All decisions are documented in the `#proj-canopy-core` Slack channel.*

### Meeting 1: The "Clean Monolith" Debate
**Date:** 2023-11-12  
**Participants:** Idris, Zia, Veda, Aaliya  
**Context:** Discussion on whether to move to microservices for the API.  
**Decision:** Idris pushed for speed. Zia argued that microservices would blow the $150k budget on infrastructure overhead.  
**Outcome:** Agreed on a "Clean Monolith" with strict Rust module boundaries.  
**Slack Thread:** `canopy-arch-discussion-01`

### Meeting 2: The Config Crisis
**Date:** 2024-01-05  
**Participants:** Zia, Aaliya  
**Context:** Aaliya discovered that API keys and DB strings are hardcoded in 42 different files.  
**Decision:** Zia noted that they don't have time to fix it before the M1 review but agreed to create a "Debt Registry."  
**Outcome:** Technical debt acknowledged; postponed until Phase 3.  
**Slack Thread:** `tech-debt-cleanup-jan`

### Meeting 3: The Workflow Builder Deadlock
**Date:** 2024-02-20  
**Participants:** Idris, Zia, Veda  
**Context:** Idris wants a "visual drag-and-drop" rule builder. Zia claims the Rust backend at the edge cannot efficiently parse complex visual graphs.  
**Decision:** No decision reached.  
**Outcome:** Feature status moved to "Blocked."  
**Slack Thread:** `workflow-builder-fight`

---

## 11. Budget Breakdown

**Total Budget:** $150,000 (Hard Cap)

| Category | Allocated | Actual to Date | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel (Core Team)** | $90,000 | $45,000 | Idris, Zia, Veda (Internal cost center) |
| **Contractor (Aaliya)** | $30,000 | $12,000 | Hourly rate for specialized Rust tasks |
| **Infrastructure** | $10,000 | $2,500 | Cloudflare Workers, R2, D1, ISO Env |
| **Tools & Licenses** | $5,000 | $1,200 | IDEs, Postman, GitHub Enterprise |
| **Contingency** | $15,000 | $0 | Reserved for regulatory changes (Risk R-01) |

**Financial Constraint:** Every expenditure over $500 requires a sign-off from Idris Nakamura.

---

## 12. Appendices

### Appendix A: CRDT Implementation Logic
The collaborative editing feature uses a state-based CRDT. Each field in the Deal Sheet is treated as a `LWWRegister<T>`.
- **Data Structure:** `(Timestamp, Value)`.
- **Merge Function:** `max(Timestamp_A, Timestamp_B)`.
- **Clock:** The system uses Hybrid Logical Clocks (HLC) to prevent issues with system clock drift across different Cloudflare Edge nodes.

### Appendix B: ISO 27001 Compliance Checklist
To maintain certification, the following controls are enforced for Project Canopy:
1. **Access Control:** All Production environment access is restricted to Zia Park via SSH keys.
2. **Data Encryption:** Database is encrypted with managed keys; no plain-text PII in logs.
3. **Auditability:** Every `POST/PATCH/DELETE` request is logged to the `audit_logs` table with the requesting UserID and IP.
4. **Vulnerability Management:** Weekly `cargo audit` and `npm audit` reports are generated and reviewed.