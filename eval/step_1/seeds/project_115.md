# Project Specification: Project Canopy
**Document Version:** 1.0.4  
**Status:** Active/Draft  
**Company:** Coral Reef Solutions  
**Date:** October 24, 2023  
**Confidentiality:** Proprietary / Internal Use Only  

---

## 1. Executive Summary

**Project Name:** Canopy  
**Project Type:** Machine Learning Model Deployment  
**Industry:** Media and Entertainment  
**Company:** Coral Reef Solutions  

### Business Justification
Project Canopy is a high-stakes, "moonshot" R&D initiative designed to revolutionize the delivery of machine learning (ML) models within the media and entertainment sector. At its core, Canopy aims to solve the latency and accessibility bottleneck associated with complex ML inferencing in content creation pipelines. By deploying models at the edge via Cloudflare Workers and utilizing a Rust-based backend for high-performance execution, Coral Reef Solutions intends to provide an industry-first "intelligent canvas" where ML models can interact with media assets in real-time without the round-trip latency of centralized cloud servers.

The strategic importance of Canopy lies in its potential to disrupt the current market where competitors rely on heavy-weight Python-based backends that struggle with scalability and real-time response. While the project is categorized as R&D, the executive sponsorship is strong, driven by a desire to pivot the company from a service-provider model to a product-led growth (PLG) model.

### ROI Projection
Due to the experimental nature of the project, the Return on Investment (ROI) is currently classified as "uncertain." However, the internal financial model projects three potential trajectories:

1.  **Conservative (Break-even):** The tool serves as a high-end internal utility for Coral Reef Solutions' premium clients, offsetting R&D costs through increased service fees over 36 months.
2.  **Moderate (SaaS Transition):** Conversion to a B2B SaaS model targeting mid-sized media houses. Projected Annual Recurring Revenue (ARR) of $1.2M by EOFY 2027, with a break-even point at Month 18 post-launch.
3.  **Aggressive (Industry Standard):** The technology becomes the foundational layer for edge-ML in media, leading to a potential acquisition or a dominant market share in "Real-time ML Production," with projected valuations in the $15M - $25M range.

The funding structure is variable and milestone-based. Capital is released in tranches upon the successful completion of predefined technical hurdles, ensuring that the company does not over-invest in a failing hypothesis.

### Core Objectives
*   Deploy a robust, Rust-powered ML inference engine.
*   Ensure absolute compliance with EU data residency laws (GDPR/CCPA).
*   Maintain a high-performance, low-latency user experience via a React frontend.
*   Establish a viable pathway to the first paying customer by July 2026.

---

## 2. Technical Architecture

Project Canopy is designed as a **Clean Monolith**. While it employs modular boundaries to allow for future microservice decomposition, the current phase prioritizes development velocity and simplicity of deployment.

### The Stack
*   **Frontend:** React 18.2 (TypeScript) utilizing Tailwind CSS for styling and Vite for build tooling.
*   **Backend:** Rust (Axum framework) for the core logic and API orchestration.
*   **Edge Layer:** Cloudflare Workers (WASM) for low-latency model triggering and request routing.
*   **Database (Edge/Local):** SQLite 3.39 for local state and edge caching.
*   **Database (Primary):** PostgreSQL 15 (managed via Supabase for EU residency).
*   **Infrastructure:** Cloudflare Tunnel and Pages.

### Architecture Diagram (ASCII)

```text
[ User Browser ] <--- HTTPS/WSS ---> [ Cloudflare Workers ]
      |                                     |
      | (React State/SQLite)                | (WASM / Edge Logic)
      v                                     v
[ Edge Cache (SQLite) ] <----------> [ Rust Backend (Axum) ]
                                            |
                                            | (gRPC / Internal)
                                            v
                            [ PostgreSQL (EU-West-1) ] <--- [ ML Model Weights ]
                                            |
                                            +---> [ S3 Compatible Store ]
```

### Architectural Decisions
1.  **Rust for Backend:** Chosen for memory safety and C-level performance, critical for handling large media tensors.
2.  **Cloudflare Workers:** To minimize "Time to First Byte" (TTFB) for global users, utilizing the global network to move ML logic closer to the user.
3.  **SQLite for Edge:** Implements a "local-first" feel, allowing users to perform basic operations without waiting for a central DB sync.
4.  **Clean Monolith:** To avoid the "distributed monolith" trap, all logic resides in one repository with strict module boundaries (`/core`, `/api`, `/edge`, `/ui`).

---

## 3. Detailed Feature Specifications

### 3.1 Data Import/Export with Format Auto-Detection
*   **Priority:** Critical (Launch Blocker)
*   **Status:** In Design
*   **Description:**
    The system must allow users to ingest large datasets of media assets (JSON, CSV, XML, and proprietary `.crf` formats) and export them for use in other tools. The "Auto-Detection" engine must analyze the file header and first 1KB of data to determine the encoding and schema without requiring user input.
*   **Detailed Requirements:**
    - **Ingestion Pipeline:** Files are uploaded to a temporary staging area in S3. A Rust-based parser validates the schema against the `media_assets` table.
    - **Format Detection:** Uses a magic-byte check and a regex-based pattern matcher to distinguish between JSON and CSV.
    - **Validation:** If a schema mismatch is detected, the system must generate a "Conflict Report" allowing the user to map fields manually.
    - **Export:** Supports "Snapshot Export," where the current state of the ML model parameters and asset metadata are bundled into a compressed `.canopy` archive.
*   **Technical Constraint:** Must handle files up to 2GB. The parser must operate in a streaming fashion to avoid OOM (Out of Memory) errors on the Rust backend.

### 3.2 Localization and Internationalization (L10n/I18n)
*   **Priority:** Medium
*   **Status:** In Review
*   **Description:**
    The interface must be accessible in 12 primary languages (English, French, German, Spanish, Chinese-Simplified, Japanese, Korean, Portuguese, Italian, Arabic, Russian, and Hindi).
*   **Detailed Requirements:**
    - **Implementation:** Use `react-i18next` for the frontend. Translation keys are stored in JSON files hosted on a CDN for dynamic updates.
    - **RTL Support:** The UI must support Right-to-Left (RTL) mirroring for Arabic.
    - **Date/Currency:** All timestamps must be localized based on the user's browser locale, defaulting to UTC for the database.
    - **Dynamic Interpolation:** Translation strings must support variables (e.g., `"Hello, {userName}"`) to maintain grammatical correctness across languages.
*   **Verification:** Each translation must be reviewed by a native speaker; currently, the team is using an automated LLM-based translation for the initial "In Review" phase.

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
*   **Priority:** Medium
*   **Status:** Blocked (Due to design disagreement between product/engineering)
*   **Description:**
    A powerful search interface allowing users to find specific ML-processed assets using a combination of keywords, metadata filters, and range sliders (e.g., "Model confidence > 80%").
*   **Detailed Requirements:**
    - **Indexing:** Use PostgreSQL `tsvector` and `tsquery` for full-text search across asset descriptions.
    - **Faceting:** The UI must display a sidebar with dynamic counts for categories (e.g., "Asset Type: Video (45), Image (120)").
    - **Performance:** Search queries must return results in < 200ms for datasets up to 1 million records.
    - **Boolean Logic:** Support for `AND`, `OR`, and `NOT` operators in the search bar.
*   **Current Blocker:** Product wants a "Google-style" omnibar, while Engineering argues for a structured filter-first approach to reduce DB load.

### 3.4 Offline-First Mode with Background Sync
*   **Priority:** Low (Nice to Have)
*   **Status:** In Progress
*   **Description:**
    Allow users to continue tagging and organizing assets while disconnected from the internet, with automatic synchronization once a connection is re-established.
*   **Detailed Requirements:**
    - **Storage:** Use SQLite via WASM in the browser to persist local changes.
    - **Sync Logic:** Implementation of a "Last-Write-Wins" (LWW) conflict resolution strategy.
    - **Queue Management:** Outgoing changes are queued in an IndexedDB store. The `SyncManager` worker polls for connectivity and flushes the queue via a series of PATCH requests.
    - **UI Indicators:** A "Syncing..." spinner and a "Local-only" badge must appear when the device is offline.
*   **Technical Challenge:** Ensuring that ML model updates (which are large) are not synced over mobile data without explicit user permission.

### 3.5 Webhook Integration Framework
*   **Priority:** Low (Nice to Have)
*   **Status:** Complete
*   **Description:**
    A framework allowing third-party tools (e.g., Slack, Zapier, custom internal scripts) to be notified when an ML model completes a processing task.
*   **Detailed Requirements:**
    - **Event Trigger:** The backend emits events (e.g., `model.inference.completed`, `asset.import.finished`).
    - **Payload:** JSON payload containing the Event ID, Timestamp, Asset ID, and a signed HMAC signature for security.
    - **Retry Logic:** Exponential backoff for failed deliveries (attempts at 1m, 5m, 15m, 1h).
    - **User Management:** A dashboard to create, delete, and test webhook URLs.
*   **Implementation:** Handled by a dedicated Rust worker that listens to the PostgreSQL `NOTIFY` channel.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1`. Authentication is handled via Bearer Tokens (JWT).

### 4.1 Asset Management
**`POST /assets/import`**
*   **Description:** Uploads a media asset for ML processing.
*   **Request Body:** `multipart/form-data` (file, metadata_json).
*   **Response:** `202 Accepted` `{ "asset_id": "uuid", "status": "queued" }`

**`GET /assets/{id}`**
*   **Description:** Retrieves metadata for a specific asset.
*   **Response:** `200 OK` `{ "id": "uuid", "name": "string", "ml_score": 0.95, "tags": ["forest", "green"] }`

### 4.2 ML Model Control
**`POST /models/execute`**
*   **Description:** Triggers an ML inference task.
*   **Request Body:** `{ "model_id": "string", "asset_id": "uuid", "params": {} }`
*   **Response:** `200 OK` `{ "job_id": "uuid", "estimated_time": "30s" }`

**`GET /models/status/{job_id}`**
*   **Description:** Polls the status of a specific ML job.
*   **Response:** `200 OK` `{ "job_id": "uuid", "state": "processing|completed|failed", "result_url": "url" }`

### 4.3 Search & Filter
**`GET /search`**
*   **Description:** Executes a faceted search query.
*   **Query Params:** `q=string`, `facet_type=string`, `min_conf=float`.
*   **Response:** `200 OK` `{ "results": [], "total": 150, "facets": { "type": { "video": 10, "image": 140 } } }`

### 4.4 System & Integration
**`POST /webhooks/register`**
*   **Description:** Registers a new webhook URL.
*   **Request Body:** `{ "url": "https://...", "events": ["model.completed"] }`
*   **Response:** `201 Created` `{ "webhook_id": "uuid" }`

**`GET /health`**
*   **Description:** System health check for load balancers.
*   **Response:** `200 OK` `{ "status": "healthy", "version": "1.0.4", "db_connected": true }`

**`POST /user/settings/locale`**
*   **Description:** Updates the user's preferred language.
*   **Request Body:** `{ "locale": "fr-FR" }`
*   **Response:** `200 OK` `{ "updated": true }`

---

## 5. Database Schema

The database is PostgreSQL 15. Due to performance requirements, 30% of queries bypass the ORM for raw SQL.

### Table Definitions

1.  **`users`**
    *   `id`: UUID (PK)
    *   `email`: VARCHAR(255) (Unique)
    *   `password_hash`: TEXT
    *   `locale`: VARCHAR(10)
    *   `created_at`: TIMESTAMP

2.  **`organizations`**
    *   `id`: UUID (PK)
    *   `name`: VARCHAR(255)
    *   `billing_plan`: VARCHAR(50)
    *   `region`: VARCHAR(20) (e.g., 'EU-West-1')

3.  **`user_org_mapping`**
    *   `user_id`: UUID (FK -> users.id)
    *   `org_id`: UUID (FK -> organizations.id)
    *   `role`: VARCHAR(50) (Admin, Editor, Viewer)

4.  **`ml_models`**
    *   `id`: UUID (PK)
    *   `version`: VARCHAR(20)
    *   `model_type`: VARCHAR(50)
    *   `weights_path`: TEXT
    *   `is_active`: BOOLEAN

5.  **`assets`**
    *   `id`: UUID (PK)
    *   `org_id`: UUID (FK -> organizations.id)
    *   `file_path`: TEXT
    *   `mime_type`: VARCHAR(100)
    *   `created_at`: TIMESTAMP

6.  **`inference_results`**
    *   `id`: UUID (PK)
    *   `asset_id`: UUID (FK -> assets.id)
    *   `model_id`: UUID (FK -> ml_models.id)
    *   `confidence_score`: FLOAT
    *   `output_data`: JSONB
    *   `processed_at`: TIMESTAMP

7.  **`tags`**
    *   `id`: UUID (PK)
    *   `label`: VARCHAR(100)
    *   `language`: VARCHAR(10)

8.  **`asset_tags`**
    *   `asset_id`: UUID (FK -> assets.id)
    *   `tag_id`: UUID (FK -> tags.id)
    *   `confidence`: FLOAT

9.  **`webhooks`**
    *   `id`: UUID (PK)
    *   `org_id`: UUID (FK -> organizations.id)
    *   `target_url`: TEXT
    *   `secret_token`: TEXT
    *   `active`: BOOLEAN

10. **`sync_logs`**
    *   `id`: UUID (PK)
    *   `user_id`: UUID (FK -> users.id)
    *   `last_sync_at`: TIMESTAMP
    *   `status`: VARCHAR(20)

### Relationships
*   **One-to-Many:** `organizations` $\rightarrow$ `assets`
*   **Many-to-Many:** `assets` $\leftrightarrow$ `tags` (via `asset_tags`)
*   **One-to-Many:** `ml_models` $\rightarrow$ `inference_results`
*   **One-to-Many:** `users` $\rightarrow$ `sync_logs`

---

## 6. Deployment and Infrastructure

### Infrastructure Overview
The deployment strategy is currently centralized around a single DevOps engineer. This creates a **bus factor of 1**, meaning the project is at significant risk if this individual is unavailable.

### Environment Descriptions

#### 1. Development (`dev`)
*   **Host:** Local Docker containers.
*   **Database:** Local PostgreSQL instance.
*   **ML Models:** Mocked or lightweight versions of the models.
*   **Deployment:** Triggered manually by developers on their local machines.

#### 2. Staging (`staging`)
*   **Host:** Cloudflare Pages (Preview) + Single EC2 Instance (EU-West-1).
*   **Database:** Shared Staging DB.
*   **ML Models:** Full-scale models but with limited throughput.
*   **Deployment:** Manual deploy via shell script executed by DevOps.

#### 3. Production (`prod`)
*   **Host:** Cloudflare Workers (Global) + High-Availability Cluster (EU-West-1).
*   **Database:** Managed PostgreSQL with Read Replicas in EU.
*   **ML Models:** Fully optimized WASM/Rust binaries.
*   **Deployment:** Manual deployment pipeline. No CI/CD automation currently exists.

### Security and Compliance
*   **Data Residency:** All primary databases and S3 buckets are locked to the `eu-central-1` and `eu-west-1` regions to comply with GDPR.
*   **Encryption:** All data is encrypted at rest using AES-256 and in transit via TLS 1.3.
*   **CCPA Compliance:** An automated "Request for Erasure" script has been developed to prune all user-related data across the 10 database tables.

---

## 7. Testing Strategy

### 7.1 Unit Testing
*   **Backend (Rust):** Using `cargo test`. Every module in `/core` must have > 80% line coverage. Focus is on the data parsing logic and ML post-processing algorithms.
*   **Frontend (React):** Using `Vitest` and `React Testing Library`. Focus on component state transitions and localization key rendering.

### 7.2 Integration Testing
*   **API Layer:** Use of `Postman` collections and a custom Rust-based test suite that hits the `/api/v1` endpoints in the staging environment.
*   **Database:** Testing raw SQL queries against a cloned production schema to ensure that the 30% of bypassed ORM queries do not break during migrations.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** `Playwright`.
*   **Critical Paths:**
    1.  User Login $\rightarrow$ Upload Asset $\rightarrow$ Trigger Model $\rightarrow$ View Result.
    2.  Import Large CSV $\rightarrow$ Auto-Detection $\rightarrow$ Data Validation.
    3.  Switch Language to Arabic $\rightarrow$ Verify RTL Layout.
*   **QA Role:** A dedicated QA specialist manually validates E2E flows and reports bugs via Slack.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Budget cut by 30% next fiscal quarter | High | High | Negotiate timeline extensions; prioritize critical "launch blocker" features over "nice to haves". |
| R2 | Team lack of experience with Rust/WASM | Medium | Medium | De-scope affected features if milestones are missed; provide internal training. |
| R3 | Bus Factor of 1 (DevOps) | High | Critical | Document deployment scripts; cross-train Sergei Park on deployment steps. |
| R4 | Raw SQL migration failure | Medium | High | Implement strict DB snapshotting before any migration; add manual QA check for all raw SQL. |
| R5 | Design conflict between Product/Eng | High | Medium | Escalate to Executive Sponsor for a final decision on search UI. |

### Probability/Impact Matrix
*   **Critical:** (R3) - Immediate project halt if DevOps is absent.
*   **High:** (R1, R4) - Threatens timeline and data integrity.
*   **Medium:** (R2, R5) - Causes friction and slight delays.

---

## 9. Timeline

### Phase 1: Foundation (Current - 2024-12)
*   Establish Rust backend and Cloudflare Worker routing.
*   Implement basic user/org authentication.
*   **Dependency:** Model weight optimization must be complete.

### Phase 2: Feature Expansion (2025-01 - 2025-12)
*   Complete "Data Import/Export" (Critical).
*   Finalize "Localization" (Medium).
*   Resolve "Advanced Search" design conflict (Medium).
*   **Dependency:** Agreement on search UI between product and engineering.

### Phase 3: Beta & Stabilization (2026-01 - 2026-07)
*   Implementation of "Offline-first" and "Webhooks".
*   External audit for GDPR/CCPA compliance.
*   **Target Milestone 1:** First paying customer onboarded by **2026-07-15**.

### Phase 4: Post-Launch Growth (2026-08 - 2026-11)
*   Stability monitoring and bug fixing.
*   **Target Milestone 2:** Post-launch stability confirmed by **2026-09-15**.
*   **Target Milestone 3:** MVP feature-complete by **2026-11-15**.

---

## 10. Meeting Notes

### Meeting 1: Architecture Review
*   **Date:** 2023-11-02
*   **Attendees:** Sergei, Ingrid, Callum
*   **Notes:**
    *   Rust vs Go debate. Sergei wins.
    *   SQLite for edge is a go.
    *   Callum worried about borrow checker. Sergei to help.
    *   Cloudflare Workers might be too restrictive for some models.

### Meeting 2: Feature Prioritization
*   **Date:** 2023-12-15
*   **Attendees:** Sergei, Wanda, Ingrid
*   **Notes:**
    *   Import/Export is a blocker. Must be priority 1.
    *   Localization: 12 languages needed. Wanda says 12 is too many, but execs want it.
    *   Search is blocked. Product wants "magic bar". Ingrid says "no way".

### Meeting 3: Budget and Risk
*   **Date:** 2024-01-20
*   **Attendees:** Sergei, Exec Sponsors
*   **Notes:**
    *   30% cut possible in Q3.
    *   Sergei asks for more time if money drops.
    *   Sponsors okay with delay if first customer is onboarded by July '26.
    *   Discussion on "Bus Factor" - they are worried about DevOps person.

---

## 11. Budget Breakdown

The budget is released in tranches based on milestone achievement. Total projected spend for the MVP phase is $2.4M.

### 11.1 Personnel ($1.8M)
*   **Tech Lead (Sergei Park):** $220,000 / yr
*   **Data Engineer (Ingrid Fischer):** $160,000 / yr
*   **UX Researcher (Wanda Costa):** $140,000 / yr
*   **Junior Dev (Callum Park):** $90,000 / yr
*   **QA Specialist (Dedicated):** $110,000 / yr
*   **DevOps Specialist (External):** $180,000 / yr (Contract)
*   *Note: Personnel costs cover a 3-year trajectory leading to 2026.*

### 11.2 Infrastructure ($350,000)
*   **Cloudflare Enterprise Plan:** $60,000 / yr
*   **Supabase (EU Hosted) + S3 Storage:** $120,000 / yr
*   **GPU Compute for Model Training:** $170,000 (One-time burst)

### 11.3 Tools and Licenses ($100,000)
*   **IDE Licenses (JetBrains/VSCode):** $5,000
*   **Localization Services (API based):** $25,000
*   **Security Audit (External):** $70,000

### 11.4 Contingency ($150,000)
*   Reserve fund for emergency infrastructure scaling or specialized consulting for Rust/WASM optimization.

---

## 12. Appendices

### Appendix A: Raw SQL Performance Hotspots
Due to the ORM's inefficiency with large-scale joins in the `inference_results` and `asset_tags` tables, the following queries are executed as raw SQL:
1.  **Global Search Aggregate:** `SELECT tag_id, COUNT(*) FROM asset_tags GROUP BY tag_id` - Used for faceted counts.
2.  **Bulk Asset Import:** `INSERT INTO assets (...) VALUES (...)` - Using PostgreSQL `COPY` command for $O(1)$ speed.
3.  **Complex Confidence Filtering:** Custom JOINs between `users` $\rightarrow$ `orgs` $\rightarrow$ `assets` $\rightarrow$ `inference_results` with a `WHERE` clause on `confidence_score`.

### Appendix B: Data Residency Mapping
| Data Type | Storage Location | Compliance Standard | Encryption |
| :--- | :--- | :--- | :--- |
| User PII | PostgreSQL (Frankfurt) | GDPR | AES-256 |
| Media Assets | S3 (Ireland) | GDPR / CCPA | AES-256 |
| Model Weights | S3 (Ireland) | Internal | None (Read-only) |
| Local State | Browser SQLite (Edge) | Local Device | Client-side Key |

### Appendix C: Deployment Checklist (The "Bus Factor" Document)
1.  Pull latest `main` branch from GitHub.
2.  Run `cargo build --release` for the backend.
3.  Deploy WASM binaries to Cloudflare via `wrangler publish`.
4.  Run `migrations/apply_latest.sql` on the production database.
5.  Update the `VERSION` file in the `/prod` bucket to trigger CDN cache purge.