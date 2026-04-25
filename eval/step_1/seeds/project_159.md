# PROJECT SPECIFICATION DOCUMENT: PROJECT CAIRN
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 24, 2023  
**Project Lead:** Yara Kim, Engineering Manager  
**Classification:** Confidential – Ridgeline Platforms Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Cairn is a strategic architectural overhaul initiated by Ridgeline Platforms to address critical operational inefficiencies within the cybersecurity toolchain. Currently, the organization maintains four redundant internal tools—legacy billing engines, disparate search indices, fragmented tenant managers, and siloed automation scripts. These tools result in significant "technical sprawl," incurring high maintenance costs, duplicated licensing fees, and fragmented data silos that hinder the company's ability to respond to cybersecurity threats with agility.

The primary objective of Project Cairn is to consolidate these four redundant tools into a single, unified API Gateway and Microservices architecture. By migrating to a modern stack (Rust, React, Cloudflare Workers), Ridgeline Platforms aims to eliminate the overhead of maintaining four separate codebases, reducing the total cost of ownership (TCO) for internal tooling.

### 1.2 ROI Projection
The $3M investment in Project Cairn is projected to yield a positive ROI within 18 months of full deployment. The financial recovery is calculated based on three primary drivers:
1. **Infrastructure Reduction:** Decommissioning four legacy server clusters and moving to an edge-computing model (Cloudflare Workers) is expected to reduce monthly cloud spend by $42,000.
2. **Engineering Efficiency:** Consolidating the codebase reduces the "cognitive load" on the engineering team. We estimate a 20% increase in developer velocity by eliminating cross-tool synchronization efforts.
3. **Operational Risk Mitigation:** As a cybersecurity firm, the cost of a data breach or HIPAA non-compliance is catastrophic. By unifying security protocols and ensuring HIPAA compliance across a single gateway, we mitigate the risk of "leakage" common in fragmented legacy systems.

The project is high-visibility; executive leadership expects not only cost reduction but a scalable foundation that can support the company's projected 5x growth in client volume over the next three years.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Overview
Project Cairn utilizes a distributed, edge-first architecture designed for ultra-low latency and high security. The system is built as a micro-frontend architecture, allowing independent team ownership of specific functional domains.

**The Tech Stack:**
- **Backend:** Rust (using the Axum framework) for high-performance, memory-safe microservices.
- **Frontend:** React 18.2+ using a Module Federation approach for micro-frontends.
- **Edge Layer:** Cloudflare Workers for request routing, authentication, and global distribution.
- **Edge Storage:** SQLite (via Cloudflare D1) for low-latency state management at the edge.
- **Compliance:** AES-256 encryption for data at rest; TLS 1.3 for data in transit (HIPAA compliant).

### 2.2 Architectural Diagram (ASCII)

```text
[ Client Layer ] 
       |
       v
[ Cloudflare Global Edge ] <--- (Authentication / Rate Limiting)
       |
       +---- [ Cloudflare Workers ] ----+
       |            |                  |
       |            v                  v
       |    [ SQLite Edge Cache ]    [ Global KV Store ]
       |
       v
[ API Gateway (Rust/Axum) ] <--- (The "Cairn" Core)
       |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
[ Billing Service ]     [ Search Service ]      [ Automation Service ]
(Rust / PostgreSQL)     (Rust / Meilisearch)    (Rust / Redis)
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                    [ Encrypted Data Lake ]
                    (HIPAA Compliant S3)
```

### 2.3 Component Details
- **The Gateway:** The Rust-based gateway acts as the central nervous system, handling request transformation, protocol translation, and central logging.
- **Micro-Frontends:** The UI is split into "Apps" (Billing App, Search App, Admin App). Each is deployed independently, preventing a bug in the Billing UI from crashing the Search functionality.
- **Data Isolation:** Each tenant is assigned a unique `tenant_id` which is injected into every database query at the gateway level, ensuring strict logical isolation.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Automated Billing and Subscription Management
**Priority:** High | **Status:** In Progress
**Description:** A unified system to manage tiered subscriptions, automated invoicing, and payment processing for Ridgeline’s cybersecurity suites.

This feature replaces three legacy billing scripts. It must support "grandfathered" pricing models while allowing for new tiered structures. The system will utilize a state-machine approach to handle subscription lifecycles (Trial $\rightarrow$ Active $\rightarrow$ Past Due $\rightarrow$ Cancelled).

**Functional Requirements:**
- **Automated Invoicing:** Generation of PDF invoices on the 1st of every month.
- **Tier Logic:** Dynamic calculation of costs based on "Seats" and "Data Volume."
- **Dunning Process:** Automated email sequences for failed payments.
- **Integration:** Integration with Stripe API for payment processing.

**Technical Constraints:**
- Must implement an idempotency key for all payment requests to prevent double-charging.
- Must log all billing changes to an immutable audit trail for HIPAA compliance.

### 3.2 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** A high-performance search engine allowing users to query massive cybersecurity datasets with millisecond latency.

This is the core value proposition of the consolidation. Users need to search across logs, user profiles, and incident reports simultaneously. The system must support "faceting" (e.g., filter by "Severity: High" and "Region: EMEA").

**Functional Requirements:**
- **Full-Text Search:** Support for fuzzy matching and stemming.
- **Faceted Navigation:** Sidebar filters that update counts in real-time.
- **Indexing Pipeline:** An asynchronous pipeline that indexes new data within 30 seconds of ingestion.
- **Boolean Logic:** Support for complex queries (e.g., `status:active AND (type:firewall OR type:endpoint)`).

**Technical Constraints:**
- Must handle 10x the current system's query volume.
- Blocked currently by third-party API rate limits during stress testing of the indexing engine.

### 3.3 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Medium | **Status:** Complete
**Description:** A robust mechanism to ensure that Customer A cannot see Customer B's data, even though they share the same database clusters.

This feature uses a "Shared Schema, Discriminator Column" approach. Every table contains a `tenant_id` UUID.

**Functional Requirements:**
- **Row-Level Security (RLS):** Implementation of PostgreSQL RLS policies to ensure data isolation at the database level.
- **Tenant Provisioning:** API endpoints to create new tenants and assign them to specific regions.
- **Context Propagation:** The `tenant_id` must be extracted from the JWT at the Gateway and passed through all downstream microservice calls.

**Technical Constraints:**
- Zero-leakage tolerance. Any query missing a `tenant_id` filter must be rejected by the database.

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** High | **Status:** In Review
**Description:** A "no-code" interface allowing security analysts to build "If This, Then That" (IFTTT) rules for incident response.

**Functional Requirements:**
- **Visual Canvas:** A drag-and-drop interface for defining triggers and actions.
- **Trigger Library:** Pre-defined triggers (e.g., "New Critical Vulnerability Detected").
- **Action Library:** Pre-defined actions (e.g., "Send Slack Alert," "Isolate Endpoint").
- **Rule Versioning:** Ability to save drafts and roll back to previous versions of a workflow.

**Technical Constraints:**
- The engine must be asynchronous; rules are processed via a message queue (RabbitMQ) to avoid blocking the main API.
- Must include a "dry run" mode to simulate rule execution without affecting production data.

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to Have) | **Status:** Not Started
**Description:** A utility to migrate data from legacy tools into Cairn and export data for external audits.

**Functional Requirements:**
- **Auto-Detection:** The system should detect if an uploaded file is CSV, JSON, or XML.
- **Schema Mapping:** A UI for users to map their legacy columns to Cairn's standardized fields.
- **Bulk Export:** Ability to export all tenant data into a single encrypted ZIP file.

**Technical Constraints:**
- Large file uploads must be handled via S3 multipart uploads to avoid gateway timeouts.
- Exported files must be encrypted with a user-provided public key.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication is handled via Bearer Tokens (JWT).

### 4.1 Billing Endpoints
**Endpoint:** `POST /billing/subscriptions`  
**Description:** Create a new subscription for a tenant.  
**Request:**
```json
{
  "tenant_id": "uuid-12345",
  "plan_id": "enterprise_gold",
  "payment_method_id": "pm_98765",
  "billing_cycle": "monthly"
}
```
**Response (201 Created):**
```json
{
  "subscription_id": "sub_abc123",
  "status": "active",
  "next_billing_date": "2023-11-01T00:00:00Z"
}
```

**Endpoint:** `GET /billing/invoices/{invoice_id}`  
**Description:** Retrieve a specific invoice.  
**Response (200 OK):**
```json
{
  "invoice_id": "inv_555",
  "amount": 1200.00,
  "currency": "USD",
  "pdf_url": "https://cdn.ridgeline.io/inv_555.pdf"
}
```

### 4.2 Search Endpoints
**Endpoint:** `POST /search/query`  
**Description:** Execute a faceted search query.  
**Request:**
```json
{
  "query": "sql injection",
  "filters": {
    "severity": ["critical", "high"],
    "date_range": { "start": "2023-01-01", "end": "2023-10-24" }
  },
  "page": 1,
  "limit": 20
}
```
**Response (200 OK):**
```json
{
  "results": [...],
  "facets": {
    "severity": { "critical": 45, "high": 112 },
    "region": { "US-East": 20, "EU-West": 30 }
  },
  "total_hits": 157
}
```

**Endpoint:** `PUT /search/index/refresh`  
**Description:** Manually trigger a re-index of specific tenant data.  
**Request:** `{ "tenant_id": "uuid-12345" }`  
**Response (202 Accepted):** `{ "job_id": "job_999", "status": "queued" }`

### 4.3 Automation Endpoints
**Endpoint:** `POST /automation/rules`  
**Description:** Save a new automation workflow.  
**Request:**
```json
{
  "rule_name": "Critical Alert Sync",
  "trigger": { "event": "incident_created", "condition": "severity == 'critical'" },
  "actions": [ { "type": "slack_notify", "channel": "#alerts" } ]
}
```
**Response (201 Created):** `{ "rule_id": "rule_001", "status": "active" }`

**Endpoint:** `DELETE /automation/rules/{rule_id}`  
**Description:** Remove an automation rule.  
**Response (204 No Content)**

### 4.4 Tenant Endpoints
**Endpoint:** `GET /tenants/{tenant_id}/config`  
**Description:** Retrieve tenant-specific configuration.  
**Response (200 OK):**
```json
{
  "tenant_id": "uuid-12345",
  "region": "us-east-1",
  "features_enabled": ["advanced_search", "automation_engine"]
}
```

**Endpoint:** `PATCH /tenants/{tenant_id}/settings`  
**Description:** Update tenant settings.  
**Request:** `{ "max_users": 500 }`  
**Response (200 OK):** `{ "updated": true }`

---

## 5. DATABASE SCHEMA

The system utilizes a hybrid approach: PostgreSQL for relational data and SQLite (D1) for edge caching. All tables below refer to the primary PostgreSQL cluster.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | N/A | `name`, `created_at`, `region` | Core tenant identity |
| `users` | `user_id` | `tenant_id` | `email`, `password_hash`, `role` | User authentication |
| `subscriptions` | `sub_id` | `tenant_id` | `plan_id`, `status`, `start_date` | Billing state |
| `plans` | `plan_id` | N/A | `name`, `monthly_cost`, `limit_seats` | Pricing tiers |
| `invoices` | `inv_id` | `sub_id` | `amount`, `paid_status`, `due_date` | Billing history |
| `search_indices` | `index_id` | `tenant_id` | `last_indexed`, `document_count` | Search metadata |
| `automation_rules`| `rule_id` | `tenant_id` | `trigger_json`, `action_json`, `is_active`| Workflow logic |
| `workflow_logs` | `log_id` | `rule_id` | `execution_time`, `status`, `error_msg` | Execution audit |
| `audit_logs` | `audit_id` | `user_id`, `tenant_id`| `action`, `timestamp`, `ip_address` | HIPAA Compliance trail |
| `api_keys` | `key_id` | `tenant_id` | `hashed_key`, `expires_at`, `scopes` | API Authentication |

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users` (One tenant has many users).
- **One-to-One:** `tenants` $\rightarrow$ `subscriptions` (One active sub per tenant).
- **One-to-Many:** `subscriptions` $\rightarrow$ `invoices` (One sub generates many invoices).
- **One-to-Many:** `tenants` $\rightarrow$ `automation_rules` (One tenant has many rules).
- **Many-to-One:** `workflow_logs` $\rightarrow$ `automation_rules`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Cairn utilizes a strictly gated promotion pipeline. No code reaches production without a manual QA sign-off.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and initial integration.
- **Deployment:** Automated CI/CD on every merge to `develop` branch.
- **Database:** Shared dev instance with anonymized data.
- **Access:** All developers.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Deployment:** Triggered by a release candidate (RC) tag.
- **Database:** Clone of production schema with scrubbed data.
- **QA Gate:** Requires a 48-hour "soak period." Manual sign-off from Yara Kim and a QA lead is required.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live customer traffic.
- **Deployment:** Manual trigger after Staging sign-off. 2-day turnaround for deployment window.
- **Infrastructure:** Multi-region Cloudflare Workers + Distributed PostgreSQL.
- **Monitoring:** Prometheus and Grafana for real-time alerting.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is managed via Terraform.
- **State Management:** Terraform Cloud.
- **Version Control:** All `.tf` files are stored in the `/infra` directory of the mono-repo.
- **Secret Management:** HashiCorp Vault for encryption keys and API secrets.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend (Rust):** Using `cargo test`. Every new function must have $\ge 80\%$ coverage. Focus on business logic and data transformation.
- **Frontend (React):** Using Vitest and React Testing Library. Focus on component rendering and hook logic.

### 7.2 Integration Testing
- **API Contract Testing:** Using Prism to validate that the API Gateway matches the OpenAPI 3.0 specification.
- **Database Integration:** Testing the RLS (Row Level Security) policies to ensure that a query for `tenant_A` never returns `tenant_B` data.
- **Edge Testing:** Using `wrangler dev` to simulate Cloudflare Worker environments.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Critical Paths:**
    - User Login $\rightarrow$ Subscription Upgrade $\rightarrow$ Payment Confirmation.
    - Complex Search Query $\rightarrow$ Facet Selection $\rightarrow$ Result Refinement.
    - Automation Rule Creation $\rightarrow$ Trigger Event $\rightarrow$ Slack Notification.
- **Execution:** E2E tests run nightly in the staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements 10x current capacity with no extra budget | High | Critical | Escalate to steering committee for additional funding; optimize Rust binaries for memory. | Yara Kim |
| R-02 | Scope creep from stakeholders adding 'small' features | High | Medium | Assign dedicated owner to track/resolve; strict Change Request (CR) process. | Yara Kim |
| R-03 | HIPAA compliance failure during audit | Low | Critical | Quarterly 3rd party security audits; AES-256 encryption for all at-rest data. | Devika Park |
| R-04 | Third-party API rate limits blocking testing | High | High | Implement a mock-server for testing; negotiate higher limits for the staging environment. | Devika Park |
| R-05 | Micro-frontend version mismatch (dependency hell) | Medium | Medium | Enforce strict versioning of shared libraries via a private NPM registry. | Zev Santos |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or legal failure.
- **High:** Major delay or significant budget overrun.
- **Medium:** Minor delay, workaround possible.
- **Low:** Negligible impact on timeline.

---

## 9. TIMELINE & PHASES

Project Cairn is divided into four major phases. All tracking is managed via JIRA.

### 9.1 Phase 1: Foundation (Jan 2025 - May 2025)
- **Focus:** API Gateway setup, Rust core development, and Tenant Isolation.
- **Dependency:** Infrastructure provisioning (Terraform).
- **Key Deliverable:** Working Gateway with Auth and Tenant routing.

### 9.2 Phase 2: Feature Implementation (June 2025 - Dec 2025)
- **Focus:** Billing, Search, and Automation engines.
- **Dependency:** Successful completion of Phase 1.
- **Milestone: MVP feature-complete (Target: 2025-12-15).**

### 9.3 Phase 3: Stabilization & QA (Dec 2025 - Aug 2026)
- **Focus:** Performance tuning and HIPAA audit.
- **Dependency:** MVP feature-complete.
- **Milestone: Post-launch stability confirmed (Target: 2025-08-15 - *Note: This is the post-launch stability window after the initial soft-launch*).**

### 9.4 Phase 4: Governance & Review (Aug 2026 - Oct 2026)
- **Focus:** Final architecture review and handover.
- **Milestone: Architecture review complete (Target: 2025-10-15).**

---

## 10. MEETING NOTES

### Meeting 1: Kickoff (2023-11-01)
- **Attendees:** Yara, Devika, Zev, Freya.
- **Notes:**
    - Project Cairn name finalized.
    - Rust for backend—Devika concerned about learning curve.
    - Budget is $3M—executive eyes on this.
    - Formal flow: JIRA only. No Slack requests for tasks.
    - HIPAA compliance non-negotiable.

### Meeting 2: Search Blocker Sync (2024-02-15)
- **Attendees:** Yara, Devika.
- **Notes:**
    - Search is blocked. 
    - Third party API hitting rate limits.
    - Devika suggests mock server.
    - Yara says escalate to steering committee if we need more budget for API tiers.
    - Full-text indexing is a launch blocker.

### Meeting 3: UX Review - Automation Engine (2024-05-10)
- **Attendees:** Yara, Zev, Freya.
- **Notes:**
    - Visual rule builder is "too complex."
    - Zev wants to simplify the drag-and-drop.
    - Freya suggested a template library for common rules.
    - Yara approved templates. 
    - Status moved to "In Review."

---

## 11. BUDGET BREAKDOWN

Total Budget: **$3,000,000**

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 12-person cross-functional team for 18 months. |
| **Infrastructure** | 15% | $450,000 | Cloudflare Workers, PostgreSQL clusters, S3 storage. |
| **Tools & Licenses**| 10% | $300,000 | Meilisearch Enterprise, Terraform Cloud, Datadog, Jira. |
| **Contingency** | 10% | $300,000 | Buffer for scope creep and unexpected infra costs. |

---

## 12. APPENDICES

### Appendix A: Performance Benchmarks
To meet the 10x capacity requirement, the following benchmarks are mandated for the Rust microservices:
- **P99 Latency:** $< 50ms$ for all GET requests.
- **Throughput:** $10,000$ requests per second (RPS) per cluster.
- **Memory Footprint:** Each service instance must stay under $512MB$ RAM.

### Appendix B: HIPAA Compliance Checklist
To maintain compliance, the following must be verified during every manual QA gate:
1. **Data Encryption:** Verify that all PII (Personally Identifiable Information) is encrypted using AES-256.
2. **Audit Logging:** Ensure every `UPDATE` or `DELETE` operation is logged in the `audit_logs` table with the user's identity.
3. **Access Control:** Verify that the `tenant_id` is strictly enforced via RLS in the database.
4. **Transmission:** Verify that no HTTP (unencrypted) traffic is allowed; all endpoints must be HTTPS/TLS 1.3.