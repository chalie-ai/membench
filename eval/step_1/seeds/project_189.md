Due to the extensive length requirement (6,000–8,000 words), this document is presented as a comprehensive, formal Technical Specification Document (TSD). It is designed to serve as the single source of truth for the development team at Talus Innovations.

***

# PROJECT FATHOM: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Active / High Urgency  
**Last Updated:** 2025-05-20  
**Project Lead:** Matteo Kim  
**Company:** Talus Innovations  
**Confidentiality:** Level 4 (Internal/Restricted)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Fathom" is a mission-critical fintech payment processing system developed by Talus Innovations specifically for the Media and Entertainment (M&E) industry. The project is categorized as an urgent regulatory compliance initiative. The primary driver for Fathom is a hard legal deadline mandated by entertainment industry financial regulators, requiring a complete overhaul of how royalties, licensing fees, and streaming residuals are processed and reported. Failure to deploy a compliant system by the hard deadline (November 15, 2026) would result in significant legal penalties and potential loss of operating licenses in key global markets.

### 1.2 Business Justification
The legacy system currently used by Talus Innovations is unable to handle the complexity of modern multi-territory digital distribution. The current infrastructure suffers from high transaction costs and an inability to support the diverse localization requirements of an international clientele. Fathom aims to replace this legacy architecture with a modern, scalable, and SOC 2 Type II compliant system. 

The core business justification lies in the transition from a monolithic, opaque payment structure to a transparent, multi-tenant environment where media entities can track payments with granular precision. By automating the compliance checks and utilizing a more efficient processing engine, Talus Innovations expects to eliminate the manual overhead currently required to satisfy regulatory audits.

### 1.3 ROI Projection and Success Metrics
The financial viability of Fathom is tied to two primary Key Performance Indicators (KPIs). 

**Metric 1: Revenue Growth.** The product is projected to attract $500,000 in new revenue within 12 months post-launch. This will be achieved by onboarding high-tier entertainment studios that previously avoided the platform due to the legacy system's lack of compliance and localization capabilities.

**Metric 2: Operational Efficiency.** A primary goal is to reduce the cost per transaction by 35% compared to the legacy system. This will be realized through the implementation of a more efficient Python/FastAPI backend and the elimination of redundant third-party middleware.

**Budgetary Overview:** The project has been allocated a budget of $800,000. Given the lean team size (2 full-time engineers plus a contractor), this budget is considered comfortable for the 6-month build cycle, allowing for high-quality tooling and a contingency reserve for the regulatory shifts.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
Fathom utilizes a modern, asynchronous stack designed for high throughput and rapid iteration.

*   **Language/Framework:** Python 3.11 with FastAPI. Chosen for its asynchronous capabilities and native support for Pydantic data validation, which is critical for financial accuracy.
*   **Database:** MongoDB (Version 6.0). A document-oriented database was selected to handle the varying schemas of different media payment types (e.g., royalties vs. flat-fee licenses).
*   **Task Queue:** Celery with Redis as a broker. Used for asynchronous report generation and batch payment processing.
*   **Containerization:** Docker Compose for local development and orchestration.
*   **Hosting:** Self-hosted on private cloud infrastructure to maintain strict control over data residency for regulatory compliance.

### 2.2 Architecture Design: Micro-Frontend (MFE)
Fathom adopts a micro-frontend architecture. Despite the backend being a set of coordinated services, the frontend is split into independent modules owned by separate functional domains. This allows the "Payment Dashboard" team and the "Compliance Reporting" team to deploy updates without affecting the entire user experience.

**Ownership Model:**
- **Module A (Payments):** Owned by the Backend/Security lead.
- **Module B (User Management/Localization):** Owned by the Contractor.
- **Module C (Reporting):** In design phase.

### 2.3 ASCII System Diagram
Below is the logical flow of a transaction through the Fathom system:

```text
[ Client Browser ]  --> [ Micro-Frontend Layer (S3/CDN) ]
                                |
                                v
                      [ FastAPI Gateway (Port 8000) ]
                                |
        ---------------------------------------------------------
        |                        |                              |
 [ Auth Service ]      [ Payment Engine ]            [ Localization Svc ]
        |                        |                              |
        v                        v                              v
 [ MongoDB Cluster ] <--- [ Celery Worker Queue ] <--- [ Redis Broker ]
        |                        |
        |                        v
        |              [ PDF/CSV Generator ] --> [ Secure S3 Bucket ]
        |
 [ SOC 2 Audit Logs ] <--- [ Security Middleware ]
```

### 2.4 Deployment Strategy
The project currently relies on a "Bus Factor of 1." All deployments are performed manually by a single DevOps engineer. This presents a significant operational risk. 

- **Deployment Process:** Manual `git pull` on production servers followed by `docker-compose restart`.
- **Environment Isolation:** Strict separation between Dev, Staging, and Prod, though the deployment scripts are shared.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (i18n/l10n)
**Priority:** High | **Status:** In Progress

**Description:**
The M&E industry operates globally. Fathom must support 12 distinct languages and regional formatting for currencies, dates, and legal disclosures. This is not merely a translation task but a structural requirement for regulatory compliance in different jurisdictions.

**Functional Requirements:**
1. **Dynamic Translation Layer:** Use of a key-value mapping system (JSON) where the UI fetches strings based on the user's `locale_id` stored in the MongoDB user profile.
2. **Currency Formatting:** Integration of the `Babel` library to handle the formatting of payments. For example, a payment of 1,000.00 USD must be displayed differently than 1.000,00 € in Germany.
3. **Right-to-Left (RTL) Support:** The CSS architecture must support RTL flipping for languages such as Arabic.
4. **Timezone Normalization:** All timestamps in MongoDB are stored in UTC, but the API must provide a `localized_timestamp` based on the tenant's registered headquarters.

**Technical Implementation:**
A middleware is implemented in FastAPI that intercepts every request. It checks the `Accept-Language` header and the user's profile. If a mismatch is found, it updates the session state. The frontend utilizes a custom hook `useTranslation()` to wrap all text components.

---

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Medium | **Status:** Complete

**Description:**
Clients migrating from legacy systems often have data in varying formats (CSV, XLSX, JSON, XML). Fathom provides a robust ingestion engine that detects the file format and maps it to the internal payment schema.

**Functional Requirements:**
1. **Magic Byte Detection:** The system does not rely on file extensions. It reads the first 2048 bytes of the uploaded file to determine the MIME type.
2. **Schema Mapping:** A "Mapping UI" allows users to drag-and-drop headers from their uploaded file to Fathom's required fields (e.g., "Payment_Amt" $\rightarrow$ `transaction_amount`).
3. **Validation Pipeline:** Uploaded data is placed in a `pending_import` collection in MongoDB. A Celery task validates the data against SOC 2 constraints before merging it into the main `transactions` collection.
4. **Export Logic:** Users can export any filtered view of their data into CSV or JSON.

**Technical Implementation:**
The `ImportService` class utilizes `pandas` for data manipulation and `python-magic` for file type identification. The process is asynchronous to prevent timeout on large files (>50MB).

---

### 3.3 Advanced Search with Faceted Filtering
**Priority:** Medium | **Status:** Blocked

**Description:**
Given the volume of transactions in the entertainment industry, users need to find specific payments using a combination of full-text search and faceted filters (e.g., "Filter by Studio" $\rightarrow$ "Filter by Date Range" $\rightarrow$ "Search for ' residuals'").

**Functional Requirements:**
1. **Full-Text Indexing:** Implementation of a MongoDB Atlas Search index to allow fuzzy matching on payment descriptions.
2. **Dynamic Facets:** The sidebar should update in real-time to show the count of transactions per category (e.g., Royalties: 450, Licensing: 120).
3. **Boolean Logic:** Support for `AND`/`OR` operators within the search bar.
4. **Pagination:** Use of cursor-based pagination to ensure performance remains consistent regardless of result set size.

**Blocker Detail:**
This feature is currently blocked due to a design disagreement between the Product Lead and the Engineering Lead. Product wants a "Google-style" omni-search bar, while Engineering argues that the current MongoDB index strategy cannot support a global omni-search without severe latency spikes.

---

### 3.4 Multi-tenant Data Isolation
**Priority:** Low | **Status:** In Progress

**Description:**
Fathom must support multiple media companies (tenants) on the same physical infrastructure while ensuring that no tenant can ever access another tenant's financial data.

**Functional Requirements:**
1. **Logical Isolation:** Every document in MongoDB must contain a `tenant_id` field.
2. **Query Enforcement:** A FastAPI dependency is being developed that automatically injects `{"tenant_id": current_user.tenant_id}` into every MongoDB query.
3. **Shared Resource Management:** Implementing rate limiting per `tenant_id` to prevent a single large studio from exhausting the system's API capacity.
4. **Tenant Onboarding:** A dedicated administrative workflow to provision new tenant IDs and associated encryption keys.

**Technical Implementation:**
The team is implementing "Silo-style" logical isolation. While the database is shared, the application layer enforces a strict boundary. The security engineer (Mosi Nakamura) is currently reviewing the "leakage" risk where a developer might forget to add the `tenant_id` filter to a custom aggregation pipeline.

---

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low | **Status:** In Design

**Description:**
Regulators require monthly and quarterly financial snapshots. This feature automates the generation of these reports and delivers them via secure email or SFTP.

**Functional Requirements:**
1. **Template Engine:** Use of Jinja2 to generate HTML templates which are then converted to PDF via `WeasyPrint`.
2. **Scheduling Engine:** Use of `Celery Beat` to trigger report generation on the 1st of every month.
3. **Secure Delivery:** Reports must be encrypted with AES-256 before being emailed or uploaded to the client's S3 bucket.
4. **Customizable Parameters:** Users can define which facets (from Feature 3.3) are included in their scheduled report.

**Design Notes:**
The current design specifies a "Report Queue" where users can see the status of their generated files (Pending $\rightarrow$ Processing $\rightarrow$ Delivered).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /payments/process`
Processes a new payment transaction.
- **Request Body:**
  ```json
  {
    "amount": 1500.00,
    "currency": "USD",
    "recipient_id": "rec_9921",
    "tenant_id": "tenant_abc",
    "metadata": { "project": "Movie_X", "type": "royalty" }
  }
  ```
- **Response (201 Created):**
  ```json
  { "transaction_id": "txn_550e8400", "status": "pending", "est_completion": "2026-06-01T12:00:00Z" }
  ```

### 4.2 `GET /payments/search`
Retrieves transactions based on faceted filters.
- **Query Params:** `?query=residuals&studio=warner&start_date=2026-01-01`
- **Response (200 OK):**
  ```json
  {
    "results": [ { "txn_id": "txn_1", "amount": 500.00 } ],
    "facets": { "studios": { "warner": 10, "disney": 5 } },
    "next_cursor": "cur_xyz123"
  }
  ```

### 4.3 `POST /import/upload`
Uploads a file for auto-detection and ingestion.
- **Request:** Multipart/form-data (`file` field).
- **Response (202 Accepted):**
  ```json
  { "job_id": "job_8872", "status": "detecting_format" }
  ```

### 4.4 `GET /import/status/{job_id}`
Checks the progress of a data import.
- **Response (200 OK):**
  ```json
  { "job_id": "job_8872", "progress": "75%", "errors": [] }
  ```

### 4.5 `GET /localization/config`
Fetches translation keys for the current session.
- **Response (200 OK):**
  ```json
  { "locale": "fr-FR", "strings": { "pay_now": "Payer maintenant", "balance": "Solde" } }
  ```

### 4.6 `POST /reports/schedule`
Sets up a recurring report delivery.
- **Request Body:**
  ```json
  { "frequency": "monthly", "format": "pdf", "email": "cfo@studio.com" }
  ```
- **Response (201 Created):**
  ```json
  { "schedule_id": "sch_441" }
  ```

### 4.7 `GET /tenants/verify`
Validates the tenant's current compliance status.
- **Response (200 OK):**
  ```json
  { "tenant_id": "tenant_abc", "compliant": true, "last_audit": "2026-01-10" }
  ```

### 4.8 `PATCH /payments/{txn_id}`
Updates the status or metadata of an existing transaction.
- **Request Body:** `{ "status": "completed" }`
- **Response (200 OK):**
  ```json
  { "txn_id": "txn_550e8400", "updated_at": "2026-06-01T14:00:00Z" }
  ```

---

## 5. DATABASE SCHEMA

Fathom uses MongoDB. While schemaless by nature, the application enforces the following structure.

### 5.1 Collection: `Tenants`
- `_id`: ObjectId (PK)
- `name`: String (e.g., "Paramount Global")
- `region`: String (ISO 3166-1)
- `api_key_hash`: String
- `compliance_level`: String ("SOC2", "GDPR", "None")
- `created_at`: ISODate

### 5.2 Collection: `Users`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ Tenants)
- `email`: String (Unique)
- `password_hash`: String
- `role`: String ("Admin", "Analyst", "Viewer")
- `preferred_locale`: String (e.g., "en-US")

### 5.3 Collection: `Transactions`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ Tenants)
- `amount`: Decimal128
- `currency`: String (ISO 4217)
- `status`: String ("pending", "completed", "failed", "flagged")
- `recipient_id`: String
- `timestamp`: ISODate
- `metadata`: Map (Dynamic fields for royalty types)

### 5.4 Collection: `ImportJobs`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ Tenants)
- `file_hash`: String
- `status`: String ("uploading", "validating", "imported", "failed")
- `row_count`: Integer
- `error_log`: Array of Strings

### 5.5 Collection: `LocalizationCache`
- `_id`: ObjectId (PK)
- `locale_id`: String (Unique)
- `translations`: Map (Key $\rightarrow$ Value)
- `version`: Integer

### 5.6 Collection: `ReportSchedules`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ Tenants)
- `cron_expression`: String
- `format`: String ("PDF", "CSV")
- `destination`: String (Email/SFTP)

### 5.7 Collection: `AuditLogs` (Critical for SOC 2)
- `_id`: ObjectId (PK)
- `actor_id`: ObjectId (FK $\rightarrow$ Users)
- `action`: String (e.g., "UPDATE_PAYMENT")
- `resource_id`: String
- `previous_state`: JSON
- `new_state`: JSON
- `timestamp`: ISODate

### 5.8 Collection: `Currencies`
- `_id`: String (PK, e.g., "USD")
- `symbol`: String
- `precision`: Integer
- `exchange_rate_to_usd`: Decimal128

### 5.9 Collection: `Recipients`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ Tenants)
- `legal_name`: String
- `tax_id`: String (Encrypted)
- `bank_details`: JSON (Encrypted)

### 5.10 Collection: `PaymentCategories`
- `_id`: ObjectId (PK)
- `name`: String (e.g., "Streaming Residuals")
- `tax_code`: String
- `default_percentage`: Decimal128

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Definitions

#### 6.1.1 Development (Dev)
- **Purpose:** Local iteration and unit testing.
- **Infrastructure:** Docker Compose running on developer laptops.
- **Database:** Local MongoDB container with a seed script.
- **Deployment:** Manual `docker-compose up`.

#### 6.1.2 Staging (Staging)
- **Purpose:** UAT (User Acceptance Testing) and SOC 2 pre-audit.
- **Infrastructure:** Single-node Linux VPS (Ubuntu 22.04).
- **Database:** MongoDB Atlas (Shared Tier) for mirroring production behavior.
- **Deployment:** Manual `git pull` by the DevOps engineer.

#### 6.1.3 Production (Prod)
- **Purpose:** Live transaction processing.
- **Infrastructure:** Self-hosted clustered environment.
- **Database:** MongoDB Replica Set (3 nodes) for high availability.
- **Deployment:** Manual `docker-compose` updates.
- **Security:** All traffic routed through an Nginx Reverse Proxy with SSL termination (Let's Encrypt).

### 6.2 SOC 2 Type II Compliance Requirements
Since SOC 2 is required before launch, the infrastructure includes:
- **Encryption at Rest:** MongoDB encrypted storage engine.
- **Encryption in Transit:** TLS 1.3 for all internal and external communication.
- **Access Control:** SSH key-based access only; no password-based logins for the production server.
- **Immutable Logging:** All `AuditLogs` are mirrored to a write-once-read-many (WORM) storage volume to prevent tampering.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`.
- **Scope:** Every FastAPI endpoint must have a corresponding test file.
- **Coverage Goal:** 80% minimum.
- **Focus:** Business logic validation, especially currency calculations and localization string fetching.
- **Mocking:** Use of `mongomock` to simulate database interactions without requiring a running MongoDB instance.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between FastAPI $\rightarrow$ Celery $\rightarrow$ MongoDB.
- **Approach:** Running a dedicated "Test" container environment using Docker Compose.
- **Scenario Tests:**
    - Import a 10k row CSV $\rightarrow$ Verify `ImportJob` status $\rightarrow$ Verify `Transactions` count.
    - Trigger a scheduled report $\rightarrow$ Check if the PDF exists in the S3 mock.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scope:** Critical user journeys (The "Happy Path").
- **Key Scenarios:**
    - User logs in $\rightarrow$ Changes language to French $\rightarrow$ Uploads a file $\rightarrow$ Verifies the payment is processed.
    - Admin creates a new tenant $\rightarrow$ Tenant logs in $\rightarrow$ Verifies they cannot see another tenant's data.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R1 | Regulatory requirements change before Nov 15 | High | High | Implement "Strategy Pattern" in backend to allow quick swapping of compliance logic. | Matteo Kim |
| R2 | Performance needs exceed 10x current capacity | Medium | High | Dedicated performance tracking; implement Redis caching for search facets. | Ilya Moreau |
| R3 | "Bus Factor of 1" for DevOps | High | Critical | Document all deployment steps in Wiki; cross-train Mosi on basic Docker commands. | Mosi Nakamura |
| R4 | Disagreement between Product and Eng | High | Medium | Escalate to Executive Stakeholders for a final decision on "Omni-search" UI. | Matteo Kim |
| R5 | SOC 2 Audit failure | Low | Critical | Weekly internal audits; use of automated compliance scanning tools. | Mosi Nakamura |

---

## 9. TIMELINE

### 9.1 Phase 1: Foundation (May 2025 - Oct 2025)
- **Focus:** Core API, MongoDB Schema, Localization Engine.
- **Dependency:** Finalization of basic regulatory requirements.
- **Milestone:** Data Import/Export complete.

### 9.2 Phase 2: Scaling & Security (Nov 2025 - Apr 2026)
- **Focus:** Multi-tenancy, SOC 2 Hardening, Search Indexing.
- **Dependency:** Resolution of Product/Eng design conflict.
- **Milestone:** Security audit pass.

### 9.3 Phase 3: Reporting & Polish (May 2026 - Aug 2026)
- **Focus:** PDF Generation, Scheduled Delivery, UI Refinement.
- **Dependency:** Successful stability tests of the payment engine.
- **Milestone: Stakeholder demo and sign-off (Target: 2026-09-15).**

### 9.4 Phase 4: Deployment & Hypercare (Sept 2026 - Nov 2026)
- **Focus:** Production migration, load testing, final compliance sign-off.
- **Milestone: Production launch (Target: 2026-11-15).**
- **Milestone: Post-launch stability confirmed (Target: 2026-07-15 - *Note: Adjusted for post-launch cycle*).**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2025-06-12)
- $\text{Matteo}$: MongoDB vs Postgres.
- $\text{Ilya}$: MongoDB better for metadata.
- $\text{Mosi}$: Need SOC 2 logs.
- $\text{Decision}$: Go with MongoDB; implement separate `AuditLogs` collection.
- $\text{Note}$: Matteo and Ilya argued about the API structure for 20 mins. No resolution on naming conventions.

### Meeting 2: The "Search" Conflict (2025-08-05)
- $\text{Product}$: Wants one search bar for everything.
- $\text{Ilya}$: Not possible with current Mongo setup. Too slow.
- $\text{Matteo}$: Suggests Elasticsearch.
- $\text{Product}$: No budget for new infra.
- $\text{Outcome}$: Blocked. No agreement.

### Meeting 3: Localization Sprint (2025-10-20)
- $\text{Udo}$: 12 languages is a lot.
- $\text{Matteo}$: Use JSON files.
- $\text{Mosi}$: Make sure the translator doesn't have DB access.
- $\text{Decision}$: Use a separate `LocalizationCache` collection to avoid reloading files on every request.

---

## 11. BUDGET BREAKDOWN

**Total Budget: $800,000**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | 2 FTEs + 1 Contractor (Udo) for 6 months. |
| **Infrastructure** | 15% | $120,000 | Self-hosted servers, MongoDB Atlas backup, Redis. |
| **Tools & Licenses** | 10% | $80,000 | SOC 2 audit fees, IDEs, Security Scanning tools. |
| **Contingency** | 10% | $80,000 | Reserve for regulatory changes or emergency scaling. |

---

## 12. APPENDICES

### Appendix A: SOC 2 Control Mapping
| Control ID | Requirement | Fathom Implementation |
| :--- | :--- | :--- |
| CC 6.1 | Logical Access | JWT-based authentication with role-based access control (RBAC). |
| CC 6.7 | Encryption | AES-256 for sensitive bank details in the `Recipients` collection. |
| CC 7.1 | System Monitoring | Integration of Prometheus/Grafana for real-time alerting on 5xx errors. |

### Appendix B: Data Migration Logic
To migrate from the legacy system to Fathom, the following logic is applied during the `ImportJob` process:
1. **Normalization:** All currency values are converted to `Decimal128` to prevent floating-point errors.
2. **De-duplication:** Use of a composite key `(tenant_id, original_txn_id)` to ensure no duplicate payments are ingested.
3. **Audit Trail:** Every imported record is tagged with the `job_id` of the import process that created it.