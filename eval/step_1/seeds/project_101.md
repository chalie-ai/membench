# PROJECT SPECIFICATION: LATTICE
**Version:** 1.0.4  
**Document Status:** FINAL / APPROVED  
**Date:** October 24, 2024  
**Project Code:** RP-LAT-2025  
**Classification:** Confidential - Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Lattice is a high-performance, cybersecurity monitoring dashboard designed specifically for the fintech sector. Developed by Ridgeline Platforms, Lattice aims to provide real-time visibility into security posture, threat detection, and automated incident response. The product is designed to serve as a centralized "glass pane" for security operations centers (SOCs), consolidating fragmented data streams into actionable intelligence.

**Business Justification**  
The impetus for Project Lattice is a strategic pivot toward a new product vertical, driven by a high-value enterprise client (Client Alpha) who has committed to a recurring annual contract value (ACV) of $2,000,000. For Ridgeline Platforms, this represents a significant diversification of revenue streams and a foothold in the specialized fintech security market. The client requires a solution that provides extreme low-latency monitoring and an intuitive interface for managing complex security workflows—capabilities that existing off-the-shelf solutions fail to provide due to their lack of specialization in fintech compliance and high-frequency data processing.

**Financial Analysis and ROI Projection**  
The project is operating under a strict, shoestring budget of $150,000. This budget covers all initial development, tooling, and infrastructure costs leading up to the primary milestones. 

*   **Initial Investment:** $150,000 (CapEx/OpEx)
*   **Annual Revenue:** $2,000,000 (Recurring)
*   **Projected Net Profit (Year 1):** $1,850,000 (excluding ongoing maintenance costs)
*   **ROI Calculation:** $(\frac{2,000,000 - 150,000}{150,000}) \times 100 = 1,233\%$

The ROI is exceptionally high due to the lean team structure and the use of serverless architecture, which minimizes idle infrastructure costs. However, the narrow budget margin means every single expenditure is scrutinized by leadership. Any cost overruns will be deducted from the contingency fund, and there is zero tolerance for "gold-plating" features.

**Strategic Goal**  
The primary objective is to successfully onboard the anchor client by June 15, 2025, while achieving SOC 2 Type II compliance. This will validate the product-market fit for the fintech vertical and allow Ridgeline Platforms to scale the solution to other tier-1 financial institutions.

---

## 2. TECHNICAL ARCHITECTURE

Lattice utilizes a modern, "edge-first" architecture to ensure minimal latency and high availability. The system is designed to process security events at the edge, filtering noise before data ever reaches the core storage layer.

### 2.1 Stack Overview
- **Backend:** Rust (Actix-web/Axum framework) for high-performance data processing and type safety.
- **Frontend:** React 18+ with TypeScript and Tailwind CSS for a responsive, widget-based UI.
- **Database:** SQLite for edge storage (via Cloudflare D1), providing localized, fast-access state management.
- **Compute:** Cloudflare Workers (Serverless) for global distribution and low-latency execution.
- **Orchestration:** API Gateway for routing, request throttling, and authentication.
- **Feature Management:** LaunchDarkly for granular feature flagging and canary deployments.

### 2.2 Architectural Diagram (ASCII Representation)

```text
[ User Browser ] <--- HTTPS/WSS ---> [ Cloudflare Global Edge ]
                                              |
                                              v
                                    [ Cloudflare Workers ] <--- [ LaunchDarkly Flags ]
                                              |
                    __________________________|__________________________
                   |                          |                          |
        [ API Gateway / Routing ]    [ Rust Logic Layer ]      [ Auth / JWT Validator ]
                   |                          |                          |
                   v                          v                          v
        [ Cloudflare D1 (SQLite) ] <--- [ Edge State Cache ] ---> [ External Security Logs ]
                   |                          |
                   |__________________________|__________________________
                                              |
                                              v
                                   [ SOC 2 Compliance Layer ]
                                   (Encryption / Audit Logs)
```

### 2.3 Data Flow
1. **Ingestion:** Security events are pushed to Cloudflare Workers via webhooks or API calls.
2. **Processing:** The Rust backend validates the payload, performs initial filtering, and determines if the event triggers a predefined automation rule.
3. **Storage:** State and configuration are stored in SQLite (D1), while high-volume time-series data is archived in cold storage.
4. **Delivery:** The React frontend polls the API Gateway or receives updates via WebSockets to refresh the dashboard widgets in real-time.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical | **Status:** Complete | **Blocker:** Launch Blocker

The Customizable Dashboard is the central nervous system of Lattice. It allows security analysts to create a personalized operational view by arranging various "widgets" that visualize different security metrics (e.g., active threats, login failures, system health).

**Functional Requirements:**
- **Drag-and-Drop Interface:** Users must be able to resize and reposition widgets using a grid-based system (React-Grid-Layout).
- **Widget Library:** A predefined set of widgets including Time-Series Graphs, Heatmaps, Alert Tables, and KPI Counters.
- **State Persistence:** Dashboard layouts are saved per user profile in the SQLite database, ensuring that when a user logs in, their specific configuration is restored.
- **Real-time Updates:** Widgets must support "Live Mode," utilizing WebSockets to update data without a full page refresh.

**Technical Implementation:**
The frontend implements a JSON-based layout schema that defines the `x, y, w, h` coordinates of each widget. When a user moves a widget, the state is debounced and sent to the `/api/v1/dashboard/layout` endpoint to update the database.

---

### 3.2 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical | **Status:** Complete | **Blocker:** Launch Blocker

The Workflow Automation Engine allows users to define "If-This-Then-That" (IFTTT) logic for security events. This reduces the mean time to respond (MTTR) by automating repetitive containment tasks.

**Functional Requirements:**
- **Visual Rule Builder:** A node-based UI (using React Flow) where users can connect "Triggers" to "Actions."
- **Triggers:** Events such as "Multiple Failed Logins from Single IP" or "Unexpected Admin Privilege Escalation."
- **Actions:** Automated responses such as "Block IP in Firewall," "Send Slack Notification," or "Force Password Reset."
- **Boolean Logic:** Support for AND/OR/NOT gates within the rule builder to allow for complex filtering.

**Technical Implementation:**
Rules are compiled into a JSON AST (Abstract Syntax Tree) and stored in the `automation_rules` table. The Rust backend evaluates incoming events against these ASTs using a high-performance matching engine, ensuring that automation triggers occur within milliseconds of event detection.

---

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** High | **Status:** Not Started

This feature provides a forensic tool for analysts to query historical security data. Unlike the dashboard, which shows current state, Advanced Search allows for deep-dive investigations.

**Functional Requirements:**
- **Full-Text Search (FTS):** Implementation of SQLite’s FTS5 module to allow for rapid searching across millions of log entries.
- **Faceted Filtering:** A sidebar allowing users to filter results by "Severity," "Source IP," "User ID," and "Timestamp Range."
- **Query Language:** A simplified query syntax (e.g., `severity:critical AND user:admin`) for power users.
- **Export Capabilities:** Ability to export filtered search results to CSV or PDF for compliance reporting.

**Technical Implementation:**
To maintain the $150k budget, we will avoid expensive external search engines (like Elasticsearch) and instead leverage SQLite’s virtual tables for full-text indexing. Data will be indexed asynchronously to prevent blocking the primary ingestion pipeline.

---

### 3.4 Webhook Integration Framework for Third-Party Tools
**Priority:** Low | **Status:** Complete | **Nice to Have**

The Webhook Framework allows Lattice to act as both a producer and consumer of data, integrating with the wider security ecosystem (e.g., Jira, PagerDuty, CrowdStrike).

**Functional Requirements:**
- **Outgoing Webhooks:** Ability to trigger an HTTP POST request to a third-party URL when a specific Lattice event occurs.
- **Incoming Webhooks:** Standardized endpoints that accept JSON payloads from external tools and convert them into Lattice events.
- **Secret Management:** HMAC signatures for all outgoing and incoming webhooks to ensure data authenticity.
- **Retry Logic:** Exponential backoff for failed webhook deliveries to ensure reliability during third-party downtime.

**Technical Implementation:**
Implemented as a set of serverless functions. Outgoing webhooks are queued using Cloudflare Queues to ensure that a slow third-party API does not hang the Lattice backend.

---

### 3.5 Customer-Facing API with Versioning and Sandbox Environment
**Priority:** High | **Status:** Blocked

This feature allows the enterprise client to programmatically interact with Lattice, automating their own internal reporting and integration workflows.

**Functional Requirements:**
- **RESTful API:** A fully documented API following OpenAPI 3.0 specifications.
- **API Versioning:** URI-based versioning (e.g., `/api/v1/`, `/api/v2/`) to prevent breaking changes for the client.
- **Sandbox Environment:** A mirrored, non-production environment where the client can test API calls without affecting real data.
- **API Key Management:** A portal for users to generate, rotate, and revoke API keys with scope-based permissions.

**Technical Implementation:**
Currently blocked due to architectural disputes between the backend and UX teams. The plan is to implement a middleware layer in Rust that handles API key validation and rate limiting before routing requests to the core business logic.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is handled via Bearer Tokens (JWT) in the Authorization header.

### 4.1 `GET /dashboard/layout`
Returns the current layout configuration for the authenticated user.
- **Request:** `Header: Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "userId": "u_987",
    "widgets": [
      {"id": "w1", "type": "chart", "x": 0, "y": 0, "w": 6, "h": 4},
      {"id": "w2", "type": "table", "x": 6, "y": 0, "w": 6, "h": 4}
    ]
  }
  ```

### 4.2 `POST /dashboard/layout`
Updates the user's dashboard configuration.
- **Request Body:**
  ```json
  {
    "widgets": [{"id": "w1", "x": 0, "y": 0, "w": 6, "h": 4}]
  }
  ```
- **Response (200 OK):** `{"status": "updated"}`

### 4.3 `GET /events`
Retrieves a list of security events with optional filtering.
- **Query Params:** `?severity=critical&limit=50`
- **Response (200 OK):**
  ```json
  {
    "data": [
      {"id": "evt_1", "timestamp": "2025-01-01T10:00Z", "type": "brute_force", "severity": "critical"}
    ],
    "pagination": {"total": 1200, "offset": 0}
  }
  ```

### 4.4 `POST /automation/rules`
Creates a new workflow automation rule.
- **Request Body:**
  ```json
  {
    "name": "Block Brute Force",
    "trigger": {"event": "auth_failure", "threshold": 5, "window": "60s"},
    "action": {"type": "firewall_block", "target": "source_ip"}
  }
  ```
- **Response (201 Created):** `{"ruleId": "rule_456", "status": "active"}`

### 4.5 `DELETE /automation/rules/{id}`
Deletes a specific automation rule.
- **Response (204 No Content):** Empty body.

### 4.6 `POST /webhooks/incoming`
Endpoint for third-party tools to push data into Lattice.
- **Request Body:**
  ```json
  {
    "source": "CrowdStrike",
    "payload": {"alert_id": "cs_123", "description": "Malware detected"},
    "signature": "hmac_sha256_hash"
  }
  ```
- **Response (202 Accepted):** `{"message": "event_queued"}`

### 4.7 `GET /search`
Performs a full-text search across indexed logs.
- **Query Params:** `?q=admin_login&start=1735689600&end=1735776000`
- **Response (200 OK):**
  ```json
  {
    "results": [{"log_id": "log_99", "text": "Admin login from 1.1.1.1"}],
    "hit_count": 1
  }
  ```

### 4.8 `POST /api-keys`
Generates a new API key for the customer.
- **Request Body:** `{"keyName": "Prod-Integration-1"}`
- **Response (201 Created):**
  ```json
  {
    "apiKey": "sk_live_xxxxxxxxxxxx",
    "expiresAt": "2026-01-01T00:00Z"
  }
  ```

---

## 5. DATABASE SCHEMA

Lattice utilizes Cloudflare D1 (SQLite). The schema is designed for high read efficiency and strict relational integrity.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Description | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` | User account and auth details | 1:M with `dashboard_layouts` |
| `orgs` | `org_id` | Enterprise client organization data | 1:M with `users` |
| `dashboard_layouts` | `layout_id` | JSON blob of widget positions | M:1 with `users` |
| `widgets` | `widget_id` | Master list of available widget types | N:M with `dashboard_layouts` |
| `events` | `event_id` | Log of security occurrences | M:1 with `orgs` |
| `automation_rules` | `rule_id` | Compiled logic for workflow triggers | M:1 with `orgs` |
| `rule_actions` | `action_id` | Specific steps within an automation rule | M:1 with `automation_rules` |
| `webhooks` | `webhook_id` | Config for 3rd party integrations | M:1 with `orgs` |
| `api_keys` | `key_id` | Hashed API keys and permissions | M:1 with `users` |
| `audit_logs` | `audit_id` | Immutable log of all admin actions | M:1 with `users` |

### 5.2 Key Field Specifications
- **`events.severity`**: Integer (1=Low, 2=Med, 3=High, 4=Critical).
- **`automation_rules.logic_ast`**: TEXT (JSON string representing the logic tree).
- **`audit_logs.action_type`**: VARCHAR (e.g., 'USER_LOGIN', 'RULE_CHANGED').
- **`api_keys.hashed_key`**: VARCHAR (SHA-256 hash of the key).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lattice employs a three-tier environment strategy to ensure stability and compliance.

**1. Development (Dev)**
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Local Rust environment and Cloudflare Wrangler (Local mode).
- **Data:** Mock data sets; no real client data.
- **Deployment:** Continuous integration via GitHub Actions on every push to `dev` branch.

**2. Staging (Stage)**
- **Purpose:** UAT (User Acceptance Testing) and SOC 2 compliance validation.
- **Infrastructure:** Cloudflare Workers (Staging Namespace) and D1 (Staging DB).
- **Data:** Anonymized production-like data.
- **Deployment:** Triggered upon merge to `staging` branch.

**3. Production (Prod)**
- **Purpose:** Live environment for the enterprise client.
- **Infrastructure:** Cloudflare Workers (Global Production) with D1 (Production DB).
- **Data:** Live, encrypted client data.
- **Deployment:** Canary releases via LaunchDarkly. New features are rolled out to 5% of traffic, then 20%, then 100% after stability confirmation.

### 6.2 Infrastructure Requirements
- **SOC 2 Type II Compliance:** All data at rest must be encrypted using AES-256. All data in transit must use TLS 1.3. Access logs for the production environment must be immutable and stored for 1 year.
- **Edge Orchestration:** All API requests must pass through the Cloudflare API Gateway for rate limiting (1,000 requests/min per API key) to prevent DDoS attacks on the SQLite layer.

---

## 7. TESTING STRATEGY

Given the "shoestring" budget and solo developer constraint, testing is prioritized by impact.

### 7.1 Unit Testing
- **Focus:** Pure logic in the Rust backend.
- **Approach:** Comprehensive test suites for the Automation Engine's AST evaluator and the API request validators.
- **Target:** 80% code coverage for core business logic.

### 7.2 Integration Testing
- **Focus:** Interaction between Rust Workers and SQLite D1.
- **Approach:** Using `miniflare` to simulate the Cloudflare environment locally. Tests will verify that a "Rule" trigger correctly results in a "Webhook" dispatch.
- **Frequency:** Run on every Pull Request.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "User logs in $\rightarrow$ drags widget $\rightarrow$ saves layout").
- **Approach:** Playwright tests running against the Staging environment.
- **Critical Paths:** 
    1. Dashboard customization flow.
    2. Rule builder creation and execution.
    3. API key generation and use.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding "small" features | High | Medium | Accept the risk; monitor weekly and track via backlog. |
| R-02 | Performance requirements 10x current capacity w/ no budget | Medium | High | Engage external consultant for independent assessment. |
| R-03 | Single point of failure (Solo Developer) | High | Critical | Maintain rigorous documentation and use standard Rust libraries. |
| R-04 | SOC 2 Compliance failure delaying launch | Low | High | Weekly audits of infrastructure and access logs. |
| R-05 | Technical debt: Lack of structured logging | High | Medium | Currently reading stdout; implement `tracing` crate in Q1 2025. |

**Probability/Impact Matrix:**
- **Critical:** Must be addressed immediately.
- **High:** Requires a documented mitigation plan.
- **Medium:** Monitored on a weekly basis.
- **Low:** Accepted risk.

---

## 9. TIMELINE

The project follows a strict sequence of milestones leading to the onboarding of the first paying customer.

### 9.1 Phase 1: Foundation (Now - Jan 2025)
- **Focus:** Core architecture and basic dashboard.
- **Dependencies:** Setup of Cloudflare Workers and D1.
- **Key Deliverable:** Working prototype of drag-and-drop widgets.

### 9.2 Phase 2: Automation & Integration (Jan 2025 - March 2025)
- **Focus:** Visual Rule Builder and Webhook framework.
- **Dependencies:** Completion of the Rust AST evaluator.
- **Key Deliverable:** Ability to trigger a webhook from a security event.

### 9.3 Phase 3: Hardening & Compliance (March 2025 - June 2025)
- **Focus:** SOC 2 audit preparation and Advanced Search implementation.
- **Dependencies:** Finalization of the SQLite FTS5 indexing.
- **Milestone 1: First paying customer onboarded (Target: 2025-06-15).**

### 9.4 Phase 4: Optimization (June 2025 - Oct 2025)
- **Focus:** API Versioning, Sandbox environment, and performance tuning.
- **Milestone 2: Architecture review complete (Target: 2025-08-15).**
- **Milestone 3: Post-launch stability confirmed (Target: 2025-10-15).**

---

## 10. MEETING NOTES

*Note: These excerpts are taken from the shared running document (currently 200 pages, unsearchable).*

### Meeting 1: 2024-11-02 - "Sprint Zero Kickoff"
**Attendees:** Noor Moreau, Umi Stein, Camila Kim, Yael Stein
- **Discussion:** Noor emphasized the $150k budget. "Every dollar is a drop of blood," she stated. 
- **Decision:** Agreed on Rust for the backend to minimize infrastructure costs through extreme efficiency.
- **Conflict:** Umi expressed concerns that the timeline for the Rule Builder is unrealistic. Noor dismissed this, stating the client already expects it.
- **Action Item:** Umi to set up the initial Cloudflare Worker project.

### Meeting 2: 2024-12-15 - "UI/UX Alignment"
**Attendees:** Noor Moreau, Camila Kim, Yael Stein
- **Discussion:** Camila presented the mockup for the drag-and-drop widgets. She argued for a "fluid" grid, but Noor insisted on a strict 12-column grid for simplicity.
- **Decision:** Strict 12-column grid adopted.
- **Note:** Umi Stein was absent; it was later discovered Umi and Noor are currently not on speaking terms following a disagreement over the database choice.
- **Action Item:** Camila to finalize widget JSON schema.

### Meeting 3: 2025-01-20 - "Performance Crisis"
**Attendees:** Noor Moreau, Umi Stein (via email/Yael as intermediary)
- **Discussion:** Yael reported that the current system cannot handle the 10x load required by the client. Umi (via email) suggested adding a Redis cache.
- **Decision:** Noor rejected the Redis suggestion due to the $0 additional budget.
- **Resolution:** Decision made to engage an external consultant for an independent assessment of the SQLite performance limits.
- **Observation:** The dysfunction between Noor and Umi is actively slowing down technical decision-making.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000.00

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $90,000.00 | Solo developer salary/contract fee (6 months) |
| **Infrastructure** | $12,000.00 | Cloudflare Workers, D1, and API Gateway |
| **Software Tools** | $8,000.00 | LaunchDarkly, GitHub Enterprise, IDE licenses |
| **Compliance** | $25,000.00 | SOC 2 Type II Audit and Certification fees |
| **Consultancy** | $10,000.00 | Performance assessment expert (one-time) |
| **Contingency** | $5,000.00 | Emergency buffer |
| **TOTAL** | **$150,000.00** | |

---

## 12. APPENDICES

### Appendix A: SOC 2 Control Mapping
To achieve SOC 2 Type II compliance, Lattice will map its technical controls as follows:
- **CC6.1 (Access Control):** Implemented via JWT and API key rotation.
- **CC7.1 (System Monitoring):** Implemented via the `audit_logs` table.
- **CC8.1 (Change Management):** Implemented via GitHub PRs and LaunchDarkly canary releases.

### Appendix B: Performance Benchmarks (Current)
- **Average Request Latency:** 45ms (Edge)
- **DB Write Throughput:** 200 tx/sec (D1)
- **DB Read Throughput:** 1,200 qps (D1)
- **Memory Usage:** < 128MB per Worker isolate.
- **Current Bottleneck:** Lack of structured logging makes production debugging an $O(n)$ search through stdout, significantly increasing MTTR (Mean Time To Repair).