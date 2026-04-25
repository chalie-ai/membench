# PROJECT SPECIFICATION DOCUMENT: QUORUM (v1.0.4)

**Project Name:** Quorum  
**Project Type:** Supply Chain Management System (SCMS)  
**Industry:** Real Estate  
**Company:** Bellweather Technologies  
**Document Version:** 1.0.4  
**Date of Issue:** October 24, 2025  
**Classification:** Internal / Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Bellweather Technologies operates in a high-velocity real estate environment where the procurement of materials, coordination of subcontractors, and management of site logistics are critical to profitability. Historically, the company relied on a fragmented ecosystem of spreadsheets, legacy emails, and manual tracking. Project "Quorum" originated as a hackathon project designed to solve the "last-mile" communication gap between site managers and procurement officers. 

Since its inception, the tool has organically grown to 500 daily active users (DAUs) within the company. This grassroots adoption proves a critical market-fit: internal stakeholders are actively seeking a centralized, real-time system to manage supply chains. The lack of a formal system has led to "dark procurement" (untracked spending) and significant material waste. By formalizing Quorum into a production-grade enterprise tool, Bellweather Technologies aims to eliminate these inefficiencies.

The primary business driver is the reduction of lead-time variability. In real estate development, a delay in the delivery of critical components (e.g., HVAC units or structural steel) can cost the company upwards of $15,000 per day in idling labor and penalty clauses. Quorum provides the visibility necessary to mitigate these risks through predictive tracking and automated workflow triggers.

### 1.2 ROI Projection
The projected budget for Quorum is $800,000 over a 6-month development cycle. The Return on Investment (ROI) is calculated based on three primary vectors:

1.  **Waste Reduction:** By implementing a visual rule builder and real-time tracking, Bellweather expects a 12% reduction in material over-ordering. Based on current annual spends, this represents a projected saving of $1.2M per year.
2.  **Labor Efficiency:** The transition from manual spreadsheets to a centralized dashboard is estimated to save each site manager 5 hours per week. Across 50 site managers, this totals 2,500 man-hours annually.
3.  **Risk Mitigation:** Reducing the occurrence of "stock-out" events by 20% will prevent an estimated $400,000 in project delay penalties annually.

**Projected Year 1 Net Benefit:** $1.6M (Savings/Gains) - $800k (Dev Cost) = $800,000 net profit, yielding a 100% ROI within the first 12 months of full deployment.

### 1.3 Scope Statement
Quorum will serve as the authoritative source of truth for all supply chain movements within Bellweather’s real estate portfolio. It will integrate with existing edge-computing nodes at construction sites using SQLite and synchronize via Cloudflare Workers to a centralized Rust-based orchestration layer.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level System Overview
Quorum utilizes a modern, distributed architecture designed for high availability and low latency at the network edge. The system is built on a "Serverless First" philosophy, leveraging Cloudflare Workers to handle requests as close to the user as possible.

**The Tech Stack:**
- **Backend:** Rust (compiled to WASM for Cloudflare Workers).
- **Frontend:** React 18.x with Tailwind CSS and Framer Motion for the drag-and-drop interface.
- **Edge Database:** SQLite (via Cloudflare D1) for local site data and fast read access.
- **Orchestration:** API Gateway pattern managing routing between serverless functions.
- **Deployment:** Weekly Release Train (WRT).

### 2.2 Architectural Diagram (ASCII)

```text
[ Client Layer ]          [ Edge Layer ]               [ Core Logic Layer ]
+----------------+       +-------------------+        +-----------------------+
| React Frontend | <---> | Cloudflare Worker | <----> | Rust API Orchestrator |
| (User Browser) |       | (Edge Middleware) |        | (WASM Runtime)        |
+----------------+       +-------------------+        +-----------------------+
                                |                               |
                                v                               v
                      +-------------------+          +-----------------------+
                      | SQLite (D1 Edge)  | <------> | Central State Store   |
                      | (Local Site Data) |          | (Global Consensus)    |
                      +-------------------+          +-----------------------+
                                |
                                v
                      +-------------------+
                      | Third-Party APIs  | (Logistics/Vendors)
                      | [CRITICAL BLOCKER] |
                      +-------------------+
```

### 2.3 Data Flow and Synchronization
Quorum employs an **Offline-First** approach. When a site manager enters data in a low-connectivity area (common in real estate construction), the React frontend interacts with a local SQLite instance. Once a network connection is established, a background sync process triggers. The sync logic uses a "Last-Write-Wins" (LWW) conflict resolution strategy, though moving toward Vector Clocks in v2.0.

### 2.4 Security Posture
While no specific compliance framework (like SOC2 or HIPAA) is currently mandated, the system undergoes quarterly penetration testing. All API requests are validated through a JWT-based authentication layer. The Rust backend ensures memory safety, significantly reducing the risk of buffer overflow attacks.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and RBAC
**Priority:** Low | **Status:** Complete  
**Description:** A comprehensive identity management system providing secure access to Quorum.  
**Functional Requirements:**
- Users must be able to log in using corporate SSO (Single Sign-On).
- Role-Based Access Control (RBAC) must define three primary roles: `Administrator`, `Procurement Manager`, and `Site Supervisor`.
- `Administrators` have full system access.
- `Procurement Managers` can edit vendor contracts and approve purchase orders.
- `Site Supervisors` can update delivery statuses and report material discrepancies but cannot change pricing.
- The system must support session expiration every 24 hours.
**Technical Detail:** The system uses JWTs (JSON Web Tokens) stored in `httpOnly` cookies to prevent XSS. The Rust backend validates the token signature on every request to the API Gateway.

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** Not Started  
**Description:** A highly flexible user interface that allows users to curate their own operational view.  
**Functional Requirements:**
- Users must be able to add/remove widgets from a library of predefined components (e.g., "Pending Deliveries," "Budget Burn-down," "Vendor Performance").
- A drag-and-drop interface must allow users to resize and reposition widgets.
- Dashboard layouts must be persisted in the database so they remain consistent across sessions.
- Widgets must support "Live Update" via WebSocket or polling to reflect real-time supply chain changes.
**Technical Detail:** The frontend will utilize `react-grid-layout` for the positioning logic. Widget states will be stored as a JSON blob in the `user_preferences` table. Each widget will correspond to a specific Rust API endpoint that returns a summarized data set.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** In Progress  
**Description:** A mechanism to protect system stability and monitor the consumption of third-party API quotas.  
**Functional Requirements:**
- The system must implement a "Token Bucket" algorithm for rate limiting.
- Different tiers of rate limits must apply based on the user role (e.g., Admins have higher limits).
- All API calls must be logged with a timestamp, user ID, endpoint path, and response time.
- An analytics dashboard must be available for the Engineering Manager to identify "noisy" clients.
**Technical Detail:** Rate limiting is handled at the Cloudflare Worker layer using a fast-access KV (Key-Value) store to track request counts per IP/User. Analytics data is piped to an asynchronous logger to avoid blocking the main request thread.

### 3.4 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Complete  
**Description:** Ensuring productivity in remote real estate sites with intermittent internet access.  
**Functional Requirements:**
- The application must load and remain functional without an active internet connection.
- All data mutations performed offline must be queued in a local SQLite database.
- When connectivity is restored, the system must automatically sync queued changes to the server.
- The UI must clearly indicate "Syncing..." or "Offline" status to the user.
- Conflict resolution must prioritize the most recent timestamp.
**Technical Detail:** This uses Service Workers to cache the React frontend shell. SQLite is used as the client-side storage engine. The synchronization logic uses a `sync_queue` table that tracks the operation type (POST/PUT/DELETE) and the payload.

### 3.5 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** Blocked  
**Description:** A "no-code" engine that allows users to automate supply chain actions.  
**Functional Requirements:**
- Users must be able to create "If-This-Then-That" (IFTTT) rules (e.g., "IF delivery is 24h late, THEN email the vendor").
- A visual canvas must allow users to connect triggers to actions.
- The engine must support multiple triggers: Time-based, Status-change, or Threshold-crossing.
- Rules must be testable in a "Simulation Mode" before being deployed to production.
**Technical Detail:** The backend will implement a Finite State Machine (FSM) in Rust. The visual builder will generate a JSON representation of the logic graph, which is then parsed by the Rust engine into a series of executable tasks. *Current Blocker: Third-party API rate limits are preventing the testing of automation triggers.*

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 `GET /dashboard/widgets`
- **Description:** Retrieves the current user's saved widget configuration.
- **Request Header:** `Authorization: Bearer <token>`
- **Response Example:**
  ```json
  {
    "user_id": "user_882",
    "layout": [
      {"id": "delivery_clock", "x": 0, "y": 0, "w": 4, "h": 2},
      {"id": "budget_chart", "x": 4, "y": 0, "w": 4, "h": 4}
    ]
  }
  ```

### 4.2 `POST /dashboard/widgets/save`
- **Description:** Saves the current layout configuration.
- **Request Body:** `{"layout": [...]}`
- **Response:** `200 OK`

### 4.3 `GET /supply/orders`
- **Description:** Lists all supply orders for the current user's project.
- **Response Example:**
  ```json
  [
    {"order_id": "ORD-101", "status": "shipped", "eta": "2026-06-01"},
    {"order_id": "ORD-102", "status": "pending", "eta": "2026-06-05"}
  ]
  ```

### 4.4 `PATCH /supply/orders/{id}/status`
- **Description:** Updates the status of a specific order.
- **Request Body:** `{"status": "delivered"}`
- **Response:** `200 OK`

### 4.5 `GET /analytics/usage`
- **Description:** Returns API usage statistics for the administrator.
- **Response Example:**
  ```json
  {
    "total_requests": 150000,
    "p99_latency": "120ms",
    "error_rate": "0.04%"
  }
  ```

### 4.6 `POST /automation/rules`
- **Description:** Creates a new automation rule.
- **Request Body:** `{"trigger": "delay_24h", "action": "email_vendor", "target": "vendor_id_44"}`
- **Response:** `201 Created`

### 4.7 `GET /sync/pending`
- **Description:** Checks for pending updates to be synced to the edge.
- **Response Example:**
  ```json
  {"pending_updates": 14, "last_sync": "2025-10-23T10:00:00Z"}
  ```

### 4.8 `DELETE /user/session`
- **Description:** Terminates the current user session (Logout).
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system utilizes a relational model hosted on Cloudflare D1 (SQLite).

### 5.1 Table Definitions

1.  **`users`**
    - `user_id` (UUID, PK)
    - `email` (VARCHAR, Unique)
    - `password_hash` (TEXT)
    - `role_id` (INT, FK -> roles.role_id)
    - `created_at` (TIMESTAMP)

2.  **`roles`**
    - `role_id` (INT, PK)
    - `role_name` (VARCHAR) — (e.g., 'Administrator', 'Site Supervisor')
    - `permissions` (JSON)

3.  **`projects`**
    - `project_id` (UUID, PK)
    - `project_name` (VARCHAR)
    - `location` (TEXT)
    - `budget_ceiling` (DECIMAL)

4.  **`vendors`**
    - `vendor_id` (UUID, PK)
    - `vendor_name` (VARCHAR)
    - `contact_email` (VARCHAR)
    - `reliability_score` (FLOAT)

5.  **`orders`**
    - `order_id` (UUID, PK)
    - `project_id` (UUID, FK -> projects.project_id)
    - `vendor_id` (UUID, FK -> vendors.vendor_id)
    - `status` (VARCHAR) — (pending, shipped, delivered, cancelled)
    - `total_cost` (DECIMAL)
    - `created_at` (TIMESTAMP)

6.  **`order_items`**
    - `item_id` (UUID, PK)
    - `order_id` (UUID, FK -> orders.order_id)
    - `sku` (VARCHAR)
    - `quantity` (INT)
    - `unit_price` (DECIMAL)

7.  **`deliveries`**
    - `delivery_id` (UUID, PK)
    - `order_id` (UUID, FK -> orders.order_id)
    - `actual_arrival` (TIMESTAMP)
    - `discrepancy_notes` (TEXT)

8.  **`user_preferences`**
    - `pref_id` (UUID, PK)
    - `user_id` (UUID, FK -> users.user_id)
    - `dashboard_layout` (JSON)
    - `theme` (VARCHAR)

9.  **`automation_rules`**
    - `rule_id` (UUID, PK)
    - `trigger_type` (VARCHAR)
    - `action_type` (VARCHAR)
    - `condition_json` (JSON)
    - `is_active` (BOOLEAN)

10. **`api_logs`**
    - `log_id` (BIGINT, PK)
    - `user_id` (UUID, FK -> users.user_id)
    - `endpoint` (VARCHAR)
    - `response_time` (INT)
    - `timestamp` (TIMESTAMP)

### 5.2 Relationships
- `users` $\rightarrow$ `roles` (Many-to-One)
- `orders` $\rightarrow$ `projects` (Many-to-One)
- `orders` $\rightarrow$ `vendors` (Many-to-One)
- `order_items` $\rightarrow$ `orders` (Many-to-One)
- `deliveries` $\rightarrow$ `orders` (One-to-One)
- `user_preferences` $\rightarrow$ `users` (One-to-One)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum utilizes three distinct environments to ensure stability.

| Environment | Purpose | Trigger | Persistence |
| :--- | :--- | :--- | :--- |
| **Dev** | Local feature development | Git Push to `feature/*` | Local SQLite / Mock API |
| **Staging** | Integration & QA testing | Git Push to `develop` | Cloudflare D1 (Staging) |
| **Prod** | Live internal tool | Release Train (Weekly) | Cloudflare D1 (Production) |

### 6.2 The Weekly Release Train (WRT)
The project adheres to a strict **Weekly Release Train**.
- **Cut-off:** Every Wednesday at 12:00 PM EST. All merged code in the `release` branch is packaged.
- **Deployment:** Every Thursday at 03:00 AM EST.
- **Strict Rule:** No hotfixes are permitted outside the train. If a bug is found on Friday, it must be fixed and deployed the following Thursday. This ensures that the QA lead (Adaeze Fischer) has a predictable window for regression testing.

### 6.3 Infrastructure Components
- **Compute:** Cloudflare Workers (Rust WASM).
- **Storage:** Cloudflare D1 for relational data; Cloudflare KV for session and rate-limit caching.
- **CI/CD:** GitHub Actions pipeline that runs `cargo test`, `npm test`, and then deploys via `wrangler`.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `#[test]` modules. Target coverage: 80%. Focus on business logic and state transitions in the automation engine.
- **Frontend:** Jest and React Testing Library for individual component rendering and hook logic.

### 7.2 Integration Testing
- **API Testing:** Postman collections executed via GitHub Actions to verify endpoint contracts.
- **Database Migration Tests:** Verification that SQLite schema updates do not destroy existing data.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scenarios:**
    - Full user flow: Login $\rightarrow$ Add Order $\rightarrow$ Change Status $\rightarrow$ Log out.
    - Offline Simulation: Disabling network in browser and verifying that data persists in the local SQLite store and syncs upon reconnection.
    - RBAC Verification: Ensuring a `Site Supervisor` cannot access the `Administrator` billing page.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor dependency EOL (End-of-Life) | High | High | Accept the risk. Monitor weekly for alternative providers. |
| **R-02** | Competitor is 2 months ahead in product build | Medium | High | Raise in next board meeting as a critical blocker to secure more resources. |
| **R-03** | Third-party API rate limit exhaustion | High | Medium | Implement aggressive caching and rate-limiting on the client side. |
| **R-04** | Lack of structured logging causing slow debugging | High | Medium | Technical Debt: Prioritize implementing `tracing` crate in Rust for production logs. |

**Probability/Impact Matrix:**
- **High/High:** Immediate Action Required.
- **Medium/High:** Weekly Monitoring.
- **High/Medium:** Planned Improvement.

---

## 9. TIMELINE

### 9.1 Project Phases

**Phase 1: Foundation & Core Logic (Current - May 2026)**
- Focus: Completing the Dashboard and API Rate Limiting.
- Dependency: Resolution of the third-party API blocker.
- **Milestone 1: MVP Feature-Complete $\rightarrow$ 2026-05-15**

**Phase 2: Pilot Expansion (May 2026 - July 2026)**
- Focus: External Beta testing with 10 pilot users (selected from senior site managers).
- Activity: Feedback loops, UI polishing, and bug squashing.
- **Milestone 2: External Beta $\rightarrow$ 2026-07-15**

**Phase 3: Optimization & Scale (July 2026 - Sept 2026)**
- Focus: Performance tuning and meeting latency benchmarks (<200ms p99).
- Activity: Database indexing, Rust optimization.
- **Milestone 3: Performance Benchmarks Met $\rightarrow$ 2026-09-15**

---

## 10. MEETING NOTES

### Meeting 1: Weekly Sync (2025-10-10)
- Attendees: Dina, Beatriz, Adaeze, Elara.
- Dashboard is a blocker.
- Elara struggling with `react-grid-layout`.
- Beatriz says Cloudflare D1 is slow on large queries.
- Action: Dina to review dashboard specs.

### Meeting 2: Tech Debt Review (2025-10-17)
- Attendees: Dina, Beatriz.
- Production logs are a mess.
- Reading stdout is not sustainable.
- Beatriz wants `tracing` crate.
- Decision: Add to backlog, but WRT takes priority.

### Meeting 3: Board Prep (2025-10-24)
- Attendees: Dina.
- Competitor "SteelFlow" is 2 months ahead.
- Need to push for Milestone 1.
- Third-party API is still capping us.
- Action: Raise as blocker at the board meeting.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000  
**Duration:** 6 Months

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $600,000 | 20+ people across Engineering, DevOps, QA. |
| **Infrastructure** | 10% | $80,000 | Cloudflare Workers, D1, KV, and GitHub Enterprise. |
| **Tools & Licenses** | 5% | $40,000 | JIRA, Postman, Playwright Cloud, Pen-testing firms. |
| **Contingency** | 10% | $80,000 | Reserved for emergency vendor pivot or scaling. |

---

## 12. APPENDICES

### Appendix A: Rust Compilation Profile
To optimize for Cloudflare Workers, the project uses the following `Cargo.toml` profile to minimize WASM binary size:
```toml
[profile.release]
opt-level = 'z'     # Optimize for size
lto = true          # Link Time Optimization
codegen-units = 1   # Reduce parallel code generation
panic = 'abort'     # Remove stack unwinding
```

### Appendix B: Sync Conflict Resolution Logic
The `sync_engine.rs` module implements the following pseudocode for conflict resolution:
1. Fetch `local_timestamp` and `remote_timestamp`.
2. If `local_timestamp > remote_timestamp`:
   - Push local state to Cloudflare D1.
   - Update `last_synced_at` marker.
3. If `remote_timestamp > local_timestamp`:
   - Overwrite local SQLite state.
   - Notify user via Toast notification ("Data updated from server").
4. If timestamps are identical:
   - No action taken.