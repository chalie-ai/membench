Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. It expands every provided detail into a production-ready blueprint.

***

# PROJECT SPECIFICATION: PROJECT HELIX
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Active / In-Development  
**Company:** Ridgeline Platforms  
**Industry:** Telecommunications  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Helix is the strategic initiative by Ridgeline Platforms to modernize the core data pipeline and analytics infrastructure of the organization. For over 15 years, the company has relied on a legacy monolithic system (referred to as "The Monolith") for critical telecommunications data processing, billing, and customer analytics. While stable, The Monolith has become a bottleneck for growth, unable to scale with modern data volumes and lacking the flexibility required for contemporary telecom services.

Helix is designed to replace this legacy system entirely. The project is not merely a migration but a complete re-engineering of the data flow, moving toward a clean monolith architecture utilizing Elixir and Phoenix. The primary objective is to transition the entire company to the new platform with **zero downtime tolerance**, as any interruption in data processing would result in immediate revenue loss and service degradation for Ridgeline’s global client base.

### 1.2 Business Justification
The business case for Helix is driven by three primary drivers:
1.  **Operational Risk:** The legacy system is running on outdated hardware and software versions that no longer receive security patches. The risk of a catastrophic failure is increasing linearly.
2.  **Scalability Constraints:** Current performance requirements are projected to be 10x the current system's capacity. The legacy system cannot scale horizontally, meaning the company cannot onboard new enterprise clients without risking system instability.
3.  **Developer Velocity:** The 15-year-old codebase has become a "black box" where small changes lead to unpredictable regressions, slowing the release cycle to months rather than days.

### 1.3 ROI Projection
The projected Return on Investment (ROI) for Helix is calculated over a 36-month horizon following the 2026 launch.
*   **Infrastructure Cost Reduction:** By migrating from on-premise legacy servers to Fly.io, we expect a 22% reduction in monthly operational overhead.
*   **Revenue Growth:** The ability to handle 10x the data volume allows Ridgeline to pursue "Tier 1" telecom providers, projected to increase Annual Recurring Revenue (ARR) by $4.2M within the first 18 months.
*   **Labor Efficiency:** Reducing the deployment cycle from a manual, high-risk process to a streamlined QA-gated pipeline will save an estimated 1,200 engineering hours per year.
*   **Total Estimated ROI:** 310% over 3 years, with the break-even point occurring 14 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design Philosophy
Helix is built as a **Clean Monolith**. Unlike microservices, which introduce network latency and complex distributed tracing, Helix utilizes Elixir’s OTP (Open Telecom Platform) to maintain strict module boundaries. This ensures that the "Billing" domain cannot leak into the "Data Ingestion" domain without a formal interface.

### 2.2 The Stack
*   **Language:** Elixir 1.16+ (Chosen for concurrency and fault tolerance).
*   **Framework:** Phoenix 1.7 (Utilizing LiveView for the real-time analytics dashboard).
*   **Database:** PostgreSQL 16 (Relational storage for billing and user metadata).
*   **Deployment:** Fly.io (Global edge distribution to minimize latency for telecom nodes).
*   **Caching:** Redis (For rate limiting and session management).

### 2.3 Architectural Diagram (ASCII)
```text
[ External Traffic ]  --> [ Fly.io Edge Proxy ] --> [ Phoenix App (Helix) ]
                                                         |
          _______________________________________________|__________________________________
         |                      |                        |                                 |
 [ LiveView Socket ]    [ REST API Layer ]      [ Background Jobs ]               [ Data Pipeline ]
         |                      |                        |                                 |
 [ Real-time State ]    [ Auth/Rate Limit ]     [ Oban / Postgres ]               [ Virus Scan/CDN ]
         |                      |                        |                                 |
         └----------------------┴----------┬-------------┴----------------------------------┘
                                           |
                                  [ PostgreSQL DB ]
                                (Schema: Public/Billing/Audit)
```

### 2.4 Data Flow Logic
1.  **Ingestion:** Data enters via the REST API or direct file upload.
2.  **Validation:** The `Helix.Validation` module checks for schema compliance.
3.  **Processing:** The `Helix.Pipeline` processes the data using GenStage for back-pressure management.
4.  **Persistence:** Data is committed to PostgreSQL via Ecto.
5.  **Visualization:** LiveView pushes updates to the frontend via WebSockets for real-time monitoring.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** High | **Status:** Blocked
**Requirement:** Users must be able to upload large telemetry datasets (up to 5GB per file) which are scanned for malware before being distributed to global CDN nodes for fast retrieval.

**Detailed Specification:**
The system will implement a multi-stage upload pipeline. Files are first uploaded to a temporary "quarantine" bucket on S3-compatible storage. A background worker, triggered by an S3 event, will pass the file to a ClamAV-based scanning service.
*   **Virus Scanning:** The `Helix.Security.Scanner` module will interface with a ClamAV API. If a virus is detected, the file is immediately deleted, and an alert is triggered in the `AuditLogs` table.
*   **CDN Distribution:** Once cleared, the file is moved to a "production" bucket and cached across Fly.io’s global edge network. The system will generate a signed URL with a 24-hour expiration.
*   **Blocking Factor:** This feature is currently blocked pending the approval of the "Enterprise Scan Tool" budget. Without this tool, the team cannot guarantee the 100% security required for telecom-grade data.
*   **Format Handling:** The upload will support `.csv`, `.parquet`, and `.jsonl`.

### 3.2 Automated Billing and Subscription Management
**Priority:** High | **Status:** Not Started
**Requirement:** A fully automated system to handle monthly recurring revenue (MRR), tiered pricing based on data volume, and automated invoicing.

**Detailed Specification:**
The billing engine will be built as a standalone domain within the monolith (`Helix.Billing`). It must integrate with a payment gateway (Stripe) and handle the following:
*   **Tiered Pricing:** 
    *   *Basic:* Up to 1TB/month ($500/mo)
    *   *Professional:* Up to 10TB/month ($2,000/mo)
    *   *Enterprise:* Custom pricing via contract.
*   **Usage Tracking:** A daily cron job (via Oban) will aggregate the total data ingested per customer. If a customer exceeds their tier, the system will trigger an "Overage Charge" event.
*   **Invoicing:** Automated PDF generation using a LaTeX template, delivered via email on the 1st of every month.
*   **Subscription Lifecycle:** Implementation of "Grace Periods" (7 days) where services remain active after a failed payment before the account is moved to `status: suspended`.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Low | **Status:** Complete
**Requirement:** Prevent API abuse and provide customers with a dashboard showing their request volume.

**Detailed Specification:**
This feature is fully implemented using a "Token Bucket" algorithm stored in Redis.
*   **Logic:** Each API key is assigned a bucket size (e.g., 1,000 requests) and a refill rate (e.g., 10 requests per second).
*   **Headers:** Every response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
*   **Analytics:** A middleware captures every request and logs the metadata (endpoint, timestamp, response time, status code) into the `api_logs` table.
*   **Visualization:** The customer portal uses a LiveView chart to show "Requests per Hour" over a 24-hour rolling window.

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical | **Status:** Complete
**Requirement:** Multiple users must be able to edit data transformation scripts simultaneously without overwriting each other's changes.

**Detailed Specification:**
This was the highest priority "Launch Blocker" and has been solved using Operational Transformation (OT) and Phoenix Presence.
*   **Concurrency Control:** When a user opens a script, they are joined to a Phoenix Topic. Their cursor position is broadcast to all other users in the session.
*   **Conflict Resolution:** The system uses a version-vector approach. Each change is sent as a "patch" (diff). If two users edit the same line, the system applies the changes based on a server-side timestamp, but preserves the alternative edit in a "Conflict History" side-panel for manual review.
*   **State Sync:** The state is maintained in a GenServer, ensuring that the "Source of Truth" always resides on the server, while the client maintains a local optimistic update.
*   **Performance:** Latency for sync is maintained under 50ms globally.

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** In Design
**Requirement:** Ability to import data from various legacy sources and export it to modern formats, with the system automatically detecting the input format.

**Detailed Specification:**
The design phase is focusing on a "Sniffer" module (`Helix.Importer.Sniffer`).
*   **Auto-Detection Logic:** The sniffer will read the first 1KB of a file to check for magic bytes (e.g., `0x41 0x43 0x4B` for certain binary formats) or structural markers (e.g., `{` for JSON, `,` for CSV).
*   **Mapping Layer:** Once the format is detected, the system will map the fields to the internal Helix schema. If fields are missing, it will prompt the user to manually map the columns.
*   **Export Options:** Support for `.csv`, `.json`, and `.parquet`. Exports larger than 100MB will be processed as background jobs, and the user will be notified via email when the download link is ready.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication is handled via Bearer Token in the Header.

### 4.1 `POST /api/v1/upload`
*   **Description:** Uploads a data file for processing.
*   **Request Body:** `multipart/form-data` (file, category_id)
*   **Example Response (202 Accepted):**
    ```json
    {
      "upload_id": "up_7721_x9",
      "status": "scanning",
      "estimated_completion": "2026-03-15T14:00:00Z"
    }
    ```

### 4.2 `GET /api/v1/analytics/usage`
*   **Description:** Retrieves usage stats for the current billing cycle.
*   **Query Params:** `start_date`, `end_date`
*   **Example Response (200 OK):**
    ```json
    {
      "total_bytes": 450000000,
      "request_count": 12500,
      "tier_limit": 1000000000,
      "percent_used": 45.0
    }
    ```

### 4.3 `PATCH /api/v1/scripts/{id}`
*   **Description:** Updates a transformation script.
*   **Request Body:** `{"content": "string", "version": 42}`
*   **Example Response (200 OK):**
    ```json
    {
      "id": "script_123",
      "version": 43,
      "status": "saved"
    }
    ```

### 4.4 `GET /api/v1/billing/invoice/{id}`
*   **Description:** Retrieves a PDF invoice.
*   **Example Response (200 OK):** Returns binary PDF stream.

### 4.5 `POST /api/v1/import/detect`
*   **Description:** Sends a sample of a file to detect the format.
*   **Request Body:** `{"sample_data": "base64_string"}`
*   **Example Response (200 OK):**
    ```json
    {
      "detected_format": "parquet",
      "confidence": 0.98,
      "suggested_mappings": ["timestamp", "device_id", "metric"]
    }
    ```

### 4.6 `DELETE /api/v1/data/purge`
*   **Description:** Deletes all data for a specific time range (GDPR/Compliance).
*   **Request Body:** `{"start_date": "2025-01-01", "end_date": "2025-01-31"}`
*   **Example Response (204 No Content):** No body.

### 4.7 `GET /api/v1/health`
*   **Description:** System health check for Fly.io load balancer.
*   **Example Response (200 OK):** `{"status": "healthy", "db_connected": true, "redis_connected": true}`

### 4.8 `POST /api/v1/subscriptions/upgrade`
*   **Description:** Upgrades the current subscription tier.
*   **Request Body:** `{"new_tier": "professional"}`
*   **Example Response (200 OK):**
    ```json
    {
      "status": "success",
      "new_monthly_cost": 2000.00,
      "prorated_amount": 150.00
    }
    ```

---

## 5. DATABASE SCHEMA

The database is PostgreSQL 16. We use three distinct schemas: `public`, `billing`, and `audit`.

### 5.1 Tables and Relationships

| Table Name | Schema | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | public | `id (UUID)`, `email`, `password_hash` | 1:N with `accounts` | Core user identity |
| `accounts` | public | `id (UUID)`, `company_name`, `status` | N:1 with `users` | Company entity |
| `subscriptions` | billing | `id`, `account_id`, `tier_id`, `start_date` | N:1 with `accounts` | Current plan details |
| `tiers` | billing | `id`, `name`, `monthly_price`, `data_limit` | 1:N with `subscriptions` | Pricing definitions |
| `invoices` | billing | `id`, `account_id`, `amount`, `paid_at` | N:1 with `accounts` | Payment history |
| `uploads` | public | `id`, `account_id`, `filename`, `status` | N:1 with `accounts` | File tracking |
| `transformation_scripts` | public | `id`, `account_id`, `content`, `version` | N:1 with `accounts` | Collaborative scripts |
| `api_logs` | audit | `id`, `api_key_id`, `endpoint`, `latency` | N:1 with `users` | Rate limit analytics |
| `audit_events` | audit | `id`, `user_id`, `action`, `timestamp` | N:1 with `users` | Security audit trail |
| `system_config` | public | `key`, `value`, `updated_at` | N/A | Global platform settings |

### 5.2 Key Schema Constraints
*   **Foreign Keys:** All deletions in `accounts` use `ON DELETE CASCADE` for `subscriptions` and `uploads` to ensure data cleanliness.
*   **Indexing:** B-Tree indexes are applied to `api_logs.timestamp` and `uploads.status` to optimize the dashboard queries.
*   **Constraints:** `subscriptions.tier_id` has a NOT NULL constraint to prevent accounts from existing without a pricing tier.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Helix utilizes a three-tier environment strategy to ensure the "zero downtime" requirement is met.

#### 6.1.1 Development (Dev)
*   **Purpose:** Individual feature development and local testing.
*   **Configuration:** Local Docker containers simulating PostgreSQL and Redis.
*   **Deployment:** Triggered by developers on feature branches.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Integration testing and QA validation.
*   **Configuration:** A mirror of the production environment on Fly.io with a scaled-down database.
*   **Deployment:** Merges to the `develop` branch trigger an automatic deploy to Staging.
*   **Gate:** This is where Asha Kim (QA Lead) performs regression testing.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer traffic.
*   **Configuration:** High-availability cluster across three Fly.io regions (us-east, eu-west, ap-southeast) to ensure low latency.
*   **Deployment:** **Manual QA Gate.** A deployment only occurs after Asha Kim signs off on the Staging build. The turnaround for a production release is 2 days from the time the feature is marked "Ready for Prod."

### 6.2 Infrastructure Specifications
*   **Compute:** 4 vCPUs, 8GB RAM per instance (Auto-scaling based on CPU utilization > 70%).
*   **Storage:** Managed PostgreSQL with daily snapshots and point-in-time recovery (PITR) enabled.
*   **Network:** TLS 1.3 enforced for all traffic; internal communication between Phoenix nodes occurs over a private WireGuard mesh.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (The Foundation)
Every module in the `Helix` codebase must have a corresponding `.exs` test file.
*   **Tool:** ExUnit.
*   **Coverage Target:** 85% minimum.
*   **Focus:** Business logic in "Pure" functions. For example, the `Billing.Calculator` must be tested against 20 different pricing scenarios to ensure penny-perfect accuracy.

### 7.2 Integration Testing (The Connectors)
Testing the interaction between the application and external dependencies (PostgreSQL, Redis, S3).
*   **Approach:** Using "Sandbox" mode in Ecto to ensure every test runs in a transaction and is rolled back, preventing state leakage between tests.
*   **Focus:** API endpoint flows. A test must simulate a full request from `POST /upload` $\rightarrow$ `Virus Scan` $\rightarrow$ `S3 Move` $\rightarrow$ `DB Update`.

### 7.3 End-to-End (E2E) Testing (The User Experience)
Validating the critical paths from the perspective of the end user.
*   **Tool:** Wallaby / Playwright.
*   **Critical Paths:**
    1.  User login $\rightarrow$ Upload file $\rightarrow$ View analytics.
    2.  Collaborative script editing $\rightarrow$ Save $\rightarrow$ Refresh page $\rightarrow$ Verify persistence.
    3.  Subscription upgrade $\rightarrow$ Stripe payment simulation $\rightarrow$ Verify new tier limit.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements are 10x current system capacity with no additional budget. | High | Critical | Escalate to steering committee for additional funding for larger Fly.io instances. |
| R-02 | Primary vendor dependency announced End-of-Life (EOL) for their product. | Medium | High | Engage external consultant for independent assessment of alternative vendors. |
| R-03 | Budget approval for critical tool purchase (Virus Scanner) is pending. | High | Medium | (Current Blocker) Use open-source ClamAV in staging as a temporary stopgap. |
| R-04 | Technical Debt: Three different date formats used in codebase. | High | Low | Implement a `Helix.DateNormalization` layer to wrap all date queries. |
| R-05 | Zero downtime migration fails during cut-over. | Low | Critical | Use a "Parallel Run" strategy where both old and new systems process data for 2 weeks. |

**Impact Matrix:**
*   **Critical:** Total system failure or revenue loss.
*   **High:** Major feature disabled or significant performance degradation.
*   **Medium:** Workaround available, but efficiency is reduced.
*   **Low:** Cosmetic or minor inconvenience.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Months 1-2)
*   **Focus:** Core architecture, DB schema, and the Collaborative Editing feature.
*   **Dependencies:** Architecture review completion.
*   **Key Goal:** Stabilize the "Clean Monolith" boundaries.

### 9.2 Phase 2: Data & Security (Months 3-4)
*   **Focus:** File upload pipeline, virus scanning integration, and API rate limiting.
*   **Dependencies:** Budget approval for scanning tools.
*   **Key Goal:** Successfully move data from upload to CDN.

### 9.3 Phase 3: Monetization & Polish (Months 5-6)
*   **Focus:** Billing system, subscription management, and import/export tools.
*   **Dependencies:** Stripe API integration.
*   **Key Goal:** Readiness for paying customers.

### 9.4 Milestone Tracking
*   **Milestone 1 (2026-03-15):** First paying customer onboarded.
*   **Milestone 2 (2026-05-15):** Architecture review complete (Verified by external auditor).
*   **Milestone 3 (2026-07-15):** Internal security audit passed.

---

## 10. MEETING NOTES

### Meeting 1: Oct 12, 2025 (Architecture Sync)
*   **Attendees:** Priya, Camila, Asha, Adaeze.
*   **Notes:**
    *   Clean monolith vs microservices.
    *   Priya insists on Elixir for concurrency.
    *   Adaeze worried about date formats.
    *   Decision: Use `NaiveDateTime` for now; normalize later.

### Meeting 2: Nov 05, 2025 (The "Blocker" Meeting)
*   **Attendees:** Priya, Camila.
*   **Notes:**
    *   Scan tool budget still pending.
    *   Camila can't finish the upload pipeline.
    *   Priya to email the steering committee.
    *   Temporary fix: Use local ClamAV for dev.

### Meeting 3: Dec 20, 2025 (QA Review)
*   **Attendees:** Priya, Asha, Adaeze.
*   **Notes:**
    *   Collaborative editing is laggy in Asia.
    *   Fly.io regions need adjusting.
    *   Asha found bug in rate limiter (leaks tokens).
    *   Decision: Fix rate limiter before Jan 5th.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000 USD (6-Month Build)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Salaries for Priya, Camila, Asha, and Adaeze. |
| **Infrastructure** | 15% | $120,000 | Fly.io compute, Postgres managed, Redis, and CDN. |
| **Tools/Licenses** | 10% | $80,000 | Virus scanning tool, Stripe Enterprise, Monitoring. |
| **Contingency** | 10% | $80,000 | Reserved for R-01 (Performance Scaling) and consultants. |

---

## 12. APPENDICES

### Appendix A: Date Format Technical Debt Detail
The codebase currently contains three conflicting date formats:
1.  **ISO 8601** (`2025-10-24T12:00:00Z`) — used in the API layer.
2.  **Unix Epoch** (`1729761600`) — used in the legacy data imports.
3.  **Custom String** (`DD/MM/YYYY`) — used in the billing PDF generator.

**Resolution Path:**
The `Helix.DateNormalization` module will be introduced as a middleware. All data entering the system will be cast to `UTC` ISO 8601. The billing generator will use a localized formatter to convert this internal standard back to `DD/MM/YYYY` only at the final output stage.

### Appendix B: Fly.io Deployment Manifest (Simplified)
```toml
app = "helix-prod"
primary_region = "nyc1"

[deploy]
  strategy = "rolling"

[[vm]]
  cpu_kind = "performance"
  size = "shared.4vCPU"
  memory = "8gb"

[[statics]]
  guest_path = "/pub/static"
  # CDN distribution handled by Fly's edge cache
```

***

**End of Document**