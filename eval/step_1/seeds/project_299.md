Due to the extreme length requirements (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity professional specification. Given the constraints of a single output, I have expanded every requirement into a deep-dive technical manual.

***

# PROJECT SPECIFICATION: PROJECT PARAPET
**Document Version:** 1.0.4  
**Status:** Draft / In-Review  
**Date:** October 24, 2023  
**Owner:** Esme Moreau, VP of Product  
**Classification:** Confidential – Stratos Systems Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Parapet is a strategic initiative by Stratos Systems to enter the e-commerce marketplace vertical. Unlike generic retail platforms, Parapet is engineered as a high-compliance, enterprise-grade marketplace designed to bridge the gap between government procurement and private sector retail agility. The project is primarily driven by a single anchor enterprise client (referred to as "Client Alpha") who has committed to a recurring annual contract value (ACV) of $2,000,000 USD.

### 1.2 Business Justification
The retail industry is currently underserved in the "high-compliance" sector. Most marketplaces (Shopify, Amazon) do not meet the rigorous security standards required for government-adjacent procurement. Parapet aims to capture this niche by implementing FedRAMP-authorized infrastructure.

The ROI projection is based on the $2M annual commitment from Client Alpha. Given that the project is currently bootstrapping using existing team capacity (unfunded budget), the "cost" is primarily opportunity cost of the 20+ staff members across three departments. However, once the initial version is deployed and the $2M revenue stream is realized, the projected Net Present Value (NPV) over three years is estimated at $4.2M, assuming a 20% growth in tenant acquisition post-beta.

### 1.3 Strategic Objectives
1. **Market Entry:** Establish a footprint in the enterprise retail vertical.
2. **Compliance Leadership:** Become the first marketplace in the portfolio to achieve FedRAMP authorization.
3. **Operational Efficiency:** Reduce manual procurement processing time for end-users by 50%.
4. **Scalability:** Reach 10,000 Monthly Active Users (MAU) within six months of the general release.

### 1.4 Project Constraints
The project faces significant headwinds: a dysfunctional leadership dynamic where the VP of Product (Esme Moreau) and the lead backend engineering efforts (Vera Oduya) are currently in a state of коммуникационный breakdown. Furthermore, the lack of a dedicated budget means the team is relying on existing infrastructure and "stolen" cycles from other Stratos projects.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Parapet utilizes a traditional Three-Tier Architecture to ensure clear separation of concerns, facilitating the strict auditing requirements of FedRAMP.

1. **Presentation Tier:** A React-based frontend (communicating via REST API).
2. **Business Logic Tier:** A Python/FastAPI application layer handling orchestration, validation, and state management.
3. **Data Tier:** A MongoDB cluster for flexible product catalogs, supplemented by Redis for caching and Celery for asynchronous task processing.

### 2.2 System Diagram (ASCII Description)
```text
[ USER BROWSER ] <--- HTTPS (TLS 1.3) ---> [ LOAD BALANCER / NGINX ]
                                                   |
                                                   v
                                       [ KUBERNETES PODS (FastAPI) ]
                                        /          |           \
          _____________________________/            |            \____________________________
         |                                          |                                          |
 [ AUTH SERVICE (SAML/OIDC) ]             [ BUSINESS LOGIC / ORM ]                  [ CELERY WORKERS ]
         |                                          |                                          |
         |                                          v                                          v
 [ MONGODB CLUSTER ] <-------------------- [ DATA PERSISTENCE ] ---------------------> [ REDIS QUEUE ]
 (Collections: Users, Products, Orders, Tenants, AuditLogs, I18n, Flags, Imports, Exports, Config)
```

### 2.3 Technology Stack
- **Language:** Python 3.11 (FastAPI)
- **Database:** MongoDB 6.0 (Community Edition, moving to Enterprise for FedRAMP)
- **Task Queue:** Celery 5.3 with Redis 7.0 as the broker.
- **Containerization:** Docker Compose for local dev; Kubernetes (K8s) for production.
- **CI/CD:** GitLab CI using rolling deployments to minimize downtime.
- **Hosting:** Self-hosted on Stratos Systems private cloud.

### 2.4 Compliance & Security
To meet FedRAMP requirements, the architecture implements:
- **FIPS 140-2 Validated Encryption:** All data at rest and in transit.
- **Strict IAM:** Integration with SAML/OIDC for identity management.
- **Audit Logging:** Every API call is logged to a non-mutable MongoDB collection.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Low | Status: In Progress)
**Description:** The system must support multiple enterprise tenants on a shared infrastructure while ensuring that no tenant can access another's data.

**Technical Detail:**
Parapet implements a "Logical Isolation" strategy. Every document in MongoDB contains a `tenant_id` field. The FastAPI middleware intercepts every request, extracts the `tenant_id` from the JWT (JSON Web Token), and injects it into the database query filter.

**Detailed Requirements:**
- **Tenant Provisioning:** An administrative API must be able to create new `Tenant` documents, assigning a unique UUID.
- **Data Leakage Prevention:** A mandatory global filter must be applied to all MongoDB queries. If a query is executed without a `tenant_id` filter, the application must throw a `SecurityException` and log the event.
- **Infrastructure Sharing:** Tenants share the same MongoDB cluster and FastAPI pods to keep costs low (bootstrapping constraint), but are isolated at the application layer.
- **Customization:** Tenants can override global marketplace settings (e.g., currency, brand colors) stored in a `tenant_config` collection.

**Current Status:** The middleware is partially implemented. Vera Oduya is refining the query interceptor to ensure that raw SQL-like MongoDB aggregations are also filtered.

---

### 3.2 SSO Integration with SAML and OIDC (Priority: High | Status: Blocked)
**Description:** For enterprise and government clients, traditional email/password logins are insufficient. Parapet requires Single Sign-On (SSO) capabilities.

**Technical Detail:**
The system will implement a pluggable authentication layer. It must support:
- **SAML 2.0:** For legacy government systems and Active Directory.
- **OIDC (OpenID Connect):** For modern cloud-based identity providers (Okta, Azure AD).

**Detailed Requirements:**
- **Service Provider (SP) Metadata:** Parapet must provide a metadata XML file for tenants to upload to their Identity Provider (IdP).
- **Attribute Mapping:** A mapping interface must exist where admins can map IdP attributes (e.g., `givenName`, `mail`) to Parapet user fields.
- **Session Management:** SSO tokens must be exchanged for short-lived JWTs (1 hour) with sliding window expiration.
- **Just-In-Time (JIT) Provisioning:** If a user is authenticated via SSO but does not exist in the Parapet database, an account should be automatically created based on the SAML assertions.

**Blocker:** This feature is currently blocked pending budget approval for a third-party SSO orchestration tool (e.g., Auth0 or Okta) as building a FedRAMP-compliant SAML stack from scratch is deemed too high-risk by the QA lead, Luciano Costa.

---

### 3.3 Data Import/Export with Format Auto-Detection (Priority: Critical | Status: In Design)
**Description:** This is a launch-blocker. Client Alpha has 50,000+ SKUs in various formats (CSV, JSON, XML, XLSX). The system must ingest these with minimal manual configuration.

**Technical Detail:**
A "Pipeline" pattern will be used. The `ImportService` will take a raw file upload, pass it to a `FormatDetector`, and then route it to the appropriate `Parser`.

**Detailed Requirements:**
- **Format Auto-Detection:** The system must analyze the first 1KB of the file to detect the mime-type and structure.
- **Schema Mapping:** Users must be able to map "Source Columns" to "Target Fields" via a UI. For example, "Item_Name" in a CSV $\rightarrow$ `product_title` in MongoDB.
- **Asynchronous Processing:** Given the file size, imports must be handled by Celery workers. The user should receive a notification via WebSocket when the import is complete.
- **Validation Engine:** Before committing to the DB, the system must perform a "dry run," flagging rows with invalid data types or missing required fields.
- **Export Capability:** Data must be exportable in the same formats, ensuring portability.

**Current Status:** Fleur Gupta is currently drafting the parser logic. The design phase is focusing on how to handle encoding issues (UTF-8 vs ISO-8859-1).

---

### 3.4 Localization and Internationalization (L10n/I18n) (Priority: High | Status: Not Started)
**Description:** To support global retail, the platform must support 12 different languages, including Right-to-Left (RTL) support for Arabic.

**Technical Detail:**
Parapet will use a "Translation Key" approach. The frontend will request a JSON bundle of keys based on the user's locale.

**Detailed Requirements:**
- **Supported Languages:** English, Spanish, French, German, Chinese (Simplified), Japanese, Arabic, Portuguese, Italian, Korean, Russian, and Dutch.
- **Dynamic Translation:** Product descriptions must be stored in a localized format:
  `description: { "en": "Blue Shirt", "fr": "Chemise Bleue" }`.
- **Currency Conversion:** Integration with an exchange rate API to dynamically convert prices based on the user's locale.
- **RTL Support:** The CSS framework must include a mirrored layout for Arabic, flipping the sidebar and navigation elements.
- **Date/Time Formatting:** Use of the `Babel` library to ensure dates and times are formatted according to regional standards.

---

### 3.5 A/B Testing Framework (Priority: Critical | Status: Complete)
**Description:** A built-in system to test different UI layouts or pricing strategies. This is integrated directly into the feature flag system.

**Technical Detail:**
The system utilizes a "Bucket" logic. When a user requests a page, the `FeatureFlagService` calculates a hash of the `user_id` and the `experiment_id`. This hash determines if the user falls into the Control (A) or Variant (B) group.

**Detailed Requirements:**
- **Deterministic Assignment:** A user must always see the same variant for a given experiment to ensure a consistent UX.
- **Weighting:** Admins can set the percentage split (e.g., 90% Control, 10% Variant).
- **Metric Tracking:** The system automatically logs interaction events (clicks, conversions) tagged with the experiment variant.
- **Kill Switch:** A global toggle to instantly disable a variant if it causes a critical failure.

**Status:** This feature is fully developed and verified by Luciano Costa.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the header.

### 4.1 `POST /auth/sso/login`
**Description:** Initiates the SSO handshake.
- **Request Body:**
  ```json
  { "tenant_id": "uuid-1234", "provider": "saml" }
  ```
- **Response (200 OK):**
  ```json
  { "redirect_url": "https://idp.client-alpha.com/saml/login?relayState=..." }
  ```

### 4.2 `GET /products`
**Description:** Retrieves a paginated list of products for the current tenant.
- **Query Params:** `page`, `limit`, `search`, `category_id`.
- **Response (200 OK):**
  ```json
  {
    "data": [
      { "id": "prod_01", "title": "Industrial Valve", "price": 150.00, "currency": "USD" }
    ],
    "pagination": { "total": 1050, "current_page": 1 }
  }
  ```

### 4.3 `POST /products/import`
**Description:** Uploads a file for asynchronous import.
- **Request Body:** `multipart/form-data` (File upload).
- **Response (202 Accepted):**
  ```json
  { "job_id": "celery-job-987", "status": "queued" }
  ```

### 4.4 `GET /imports/status/{job_id}`
**Description:** Checks the progress of a data import.
- **Response (200 OK):**
  ```json
  { "job_id": "celery-job-987", "progress": "65%", "errors": [] }
  ```

### 4.5 `PATCH /products/{id}`
**Description:** Updates product details.
- **Request Body:**
  ```json
  { "price": 145.00, "stock_level": 20 }
  ```
- **Response (200 OK):** `{ "status": "success", "updated_at": "2023-10-24T10:00:00Z" }`

### 4.6 `GET /tenants/config`
**Description:** Retrieves the configuration for the active tenant.
- **Response (200 OK):**
  ```json
  { "tenant_name": "Client Alpha", "theme": "dark", "default_language": "en-US" }
  ```

### 4.7 `POST /experiments/create`
**Description:** Sets up a new A/B test.
- **Request Body:**
  ```json
  { "name": "Checkout-Button-Color", "variants": ["blue", "green"], "split": [0.5, 0.5] }
  ```
- **Response (201 Created):** `{ "experiment_id": "exp_44" }`

### 4.8 `GET /analytics/conversion`
**Description:** Returns conversion rates for A/B variants.
- **Response (200 OK):**
  ```json
  { "experiment_id": "exp_44", "results": { "blue": "3.2%", "green": "4.1%" } }
  ```

---

## 5. DATABASE SCHEMA

Parapet uses MongoDB. While schemaless, the following document structures are enforced via Pydantic models in the FastAPI layer.

### 5.1 Collection: `tenants`
- `_id`: ObjectId (PK)
- `name`: String
- `domain`: String (Unique)
- `fedramp_status`: Boolean
- `created_at`: ISODate
- `settings`: Object (JSON)

### 5.2 Collection: `users`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `email`: String
- `sso_id`: String (Unique)
- `role`: String (Admin, Buyer, Vendor)
- `locale`: String (e.g., "en-GB")

### 5.3 Collection: `products`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `sku`: String
- `title`: Object (Localized keys)
- `description`: Object (Localized keys)
- `price`: Decimal128
- `category_id`: ObjectId (FK $\rightarrow$ categories)
- `metadata`: Object (Dynamic attributes)

### 5.4 Collection: `categories`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `name`: String
- `parent_id`: ObjectId (Self-reference)

### 5.5 Collection: `orders`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `items`: Array (Product IDs, quantities)
- `total_amount`: Decimal128
- `status`: String (Pending, Shipped, Delivered)

### 5.6 Collection: `audit_logs`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `action`: String
- `timestamp`: ISODate
- `ip_address`: String
- `payload`: Object

### 5.7 Collection: `feature_flags`
- `_id`: ObjectId (PK)
- `flag_name`: String (Unique)
- `is_enabled`: Boolean
- `rules`: Object (Targeting logic)

### 5.8 Collection: `experiments`
- `_id`: ObjectId (PK)
- `name`: String
- `variants`: Array
- `split_percentage`: Array
- `status`: String (Running, Finished)

### 5.9 Collection: `import_jobs`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `filename`: String
- `status`: String (Pending, Processing, Completed, Failed)
- `error_log`: Array (Strings)

### 5.10 Collection: `i18n_bundles`
- `_id`: ObjectId (PK)
- `language_code`: String (Unique)
- `translations`: Object (Key-Value pairs)

**Relationship Summary:**
The `tenant_id` is the primary pivot. Every operational collection (Products, Users, Orders, etc.) maintains a hard link to the `tenants` collection to ensure the multi-tenant isolation required by the project scope.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Parapet utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (`dev`)
- **Purpose:** Rapid iteration and feature development.
- **Hosting:** Individual developer Docker Compose setups and a shared "Dev" K8s namespace.
- **Data:** Mock data and sanitized snapshots of production.
- **Deployment:** Triggered on every commit to `develop` branch via GitLab CI.

#### 6.1.2 Staging (`staging`)
- **Purpose:** QA, UAT (User Acceptance Testing), and Architecture Reviews.
- **Hosting:** K8s cluster mirroring production specs.
- **Data:** Clone of production data (anonymized).
- **Deployment:** Triggered on merge to `release` branch. This environment is where Luciano Costa performs final sign-offs.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live environment for Client Alpha and pilot users.
- **Hosting:** FedRAMP-compliant, self-hosted K8s cluster with high-availability (HA) nodes.
- **Deployment:** Rolling deployments via GitLab CI. New pods are spun up and health-checked before old pods are terminated.

### 6.2 CI/CD Pipeline
1. **Lint/Test:** Pylint and PyTest are run on every push.
2. **Build:** Docker image is built and pushed to the Stratos internal registry.
3. **Deploy:** Kubernetes manifests are applied via `kubectl` within the GitLab runner.
4. **Smoke Test:** Automated health check of `/health` endpoint.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** PyTest.
- **Coverage Goal:** 80% of business logic.
- **Focus:** Testing individual FastAPI dependencies and Pydantic validation models.
- **Execution:** Run on every GitLab CI pipeline.

### 7.2 Integration Testing
- **Tool:** PyTest with MongoDB Memory Server.
- **Focus:** Testing the flow between the API layer and the Database. Specifically, verifying that the `tenant_id` filter is correctly applied across all queries.
- **Critical Path:** Testing the Celery worker's ability to process import jobs without timing out.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Critical user journeys:
  - SSO Login $\rightarrow$ Product Search $\rightarrow$ Checkout.
  - Admin Login $\rightarrow$ File Upload $\rightarrow$ Data Import $\rightarrow$ Product Verification.
- **Execution:** Run nightly in the Staging environment.

### 7.4 Security Testing
- **Penetration Testing:** Manual audits conducted by the security team to ensure no cross-tenant data leakage.
- **FedRAMP Audit:** Formal validation of encryption standards and audit log immutability.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | Critical | Negotiate timeline extension and secure a new executive champion immediately. |
| R-02 | Competitor 2 months ahead | Medium | High | De-scope non-essential features (like L10n) to accelerate the launch of the core import/export engine. |
| R-03 | Budget approval for SSO tool pending | High | Medium | Evaluate open-source alternatives (Keycloak), though this may delay FedRAMP. |
| R-04 | Raw SQL Technical Debt | High | Medium | Implement a phased migration to the ORM; prioritize the most dangerous queries first. |
| R-05 | Team Dysfunction (Esme $\leftrightarrow$ Vera) | Critical | High | Establish a strict "ticket-only" communication protocol via Jira to minimize interpersonal friction. |

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase 1: Foundation (Current $\rightarrow$ March 2026)
- **Focus:** Finalizing the A/B framework and completing the Data Import engine.
- **Dependency:** Budget approval for SSO tools.
- **Target:** **Milestone 1 (2026-03-15): External beta with 10 pilot users.**

### 9.2 Phase 2: Hardening (March $\rightarrow$ May 2026)
- **Focus:** Architecture review, FedRAMP documentation, and L10n implementation.
- **Dependency:** Beta feedback from pilot users.
- **Target:** **Milestone 2 (2026-05-15): Architecture review complete.**

### 9.3 Phase 3: Delivery (May $\rightarrow$ July 2026)
- **Focus:** Final UI polish, stress testing, and stakeholder demos.
- **Dependency:** Successful Architecture Review sign-off.
- **Target:** **Milestone 3 (2026-07-15): Stakeholder demo and sign-off.**

---

## 10. MEETING NOTES

### Meeting 1: Sprint Alignment (2023-10-12)
- **Attendees:** Esme, Vera, Luciano, Fleur.
- **Notes:**
  - Import/Export is the main blocker.
  - Fleur struggling with CSV encoding.
  - Vera says the DB is too slow for raw imports.
  - Esme wants a "prettier" dashboard.
  - Vera doesn't respond to the dashboard comment.

### Meeting 2: Technical Debt Review (2023-10-19)
- **Attendees:** Vera, Luciano.
- **Notes:**
  - 30% of queries use raw SQL.
  - Migration script failed in Staging.
  - Luciano worried about data integrity.
  - Need to fix ORM or accept risk.
  - Decision: Keep raw SQL for performance, document as "Danger Zones."

### Meeting 3: Stakeholder Pressure Sync (2023-10-26)
- **Attendees:** Esme, Project Sponsor.
- **Notes:**
  - Sponsor might be leaving in Q1.
  - Client Alpha is asking for a demo.
  - Budget for SSO tool still "pending."
  - Esme claims we are "on track" (despite blocks).
  - Action: Send revised timeline.

---

## 11. BUDGET BREAKDOWN

Since the project is bootstrapping, these figures represent the **Internal Resource Allocation (IRA)** and the **Requested Out-of-Pocket (OOP)** funds.

| Category | Item | Estimated Cost (Annual) | Source |
| :--- | :--- | :--- | :--- |
| **Personnel** | 20+ Staff (Allocated Capacity) | $3,200,000 | Existing Payroll |
| **Infrastructure** | Self-hosted K8s + MongoDB | $120,000 | Existing IT Budget |
| **Tools** | SSO Orchestration Tool (Requested) | $45,000 | **Pending Approval** |
| **Tools** | MongoDB Enterprise License | $60,000 | **Pending Approval** |
| **Contingency** | FedRAMP Audit Fees | $100,000 | Corporate Reserve |
| **TOTAL** | | **$3,525,000** | |

**ROI Note:** The $2M annual payment from Client Alpha covers the direct tool/license costs and contributes to the payroll overhead of the 20-person team.

---

## 12. APPENDICES

### Appendix A: The "Raw SQL" Danger Zones
The following areas of the code bypass the ORM for performance reasons. Any changes to the MongoDB schema in these areas must be manually verified by Vera Oduya:
1. `services/import_engine.py` $\rightarrow$ Bulk insert operations.
2. `services/analytics_engine.py` $\rightarrow$ Aggregation pipelines for A/B testing.
3. `services/search_service.py` $\rightarrow$ Complex regex-based product searches.

### Appendix B: FedRAMP Control Mapping
To achieve authorization, Parapet maps the following technical features to NIST 800-53 controls:
- **AC-2 (Account Management):** Handled by SSO/SAML integration.
- **AU-2 (Event Logging):** Handled by the `audit_logs` collection.
- **SC-28 (Protection of Information at Rest):** Handled by AES-256 encryption on the MongoDB volume.
- **IA-2 (Identification and Authentication):** Handled by OIDC/SAML multi-factor authentication.