Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document (PSD). It is structured for daily reference by the engineering, product, and QA teams at Ridgeline Platforms.

***

# PROJECT SPECIFICATION DOCUMENT: PROJECT TRELLIS
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Date:** October 24, 2023  
**Classification:** Internal / Confidential  
**Company:** Ridgeline Platforms

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project Trellis is a strategic "moonshot" R&D initiative commissioned by Ridgeline Platforms. The objective is to develop a high-scale, enterprise-grade e-commerce marketplace specifically tailored for the food and beverage (F&B) industry. Unlike traditional retail platforms, Trellis is designed to handle the complexities of perishable goods, temperature-controlled logistics, and stringent food safety regulatory compliance.

### 1.2 Business Justification
The F&B sector is currently undergoing a digital transformation, shifting from legacy EDI (Electronic Data Interchange) systems to agile, API-driven marketplaces. Ridgeline Platforms seeks to capture this transition by providing a robust infrastructure that allows producers, distributors, and retailers to interact in a seamless digital ecosystem. While the project is currently classified as an R&D venture with an uncertain immediate Return on Investment (ROI), it carries strong executive sponsorship. The strategic value lies in the intellectual property (IP) development and the potential to disrupt the B2B food supply chain.

### 1.3 ROI Projection
Given the "moonshot" nature of Trellis, traditional ROI calculations are volatile. However, the projected value is based on two primary drivers:
1. **Market Capture:** If Trellis captures 2% of the regional B2B F&B distribution market within 24 months post-launch, the projected annual recurring revenue (ARR) is estimated at $4.2M.
2. **Operational Efficiency:** By automating the procurement process, the platform aims to reduce the cost of goods sold (COGS) for participants by 12% through optimized logistics.

The project is currently bootstrapping using existing team capacity, meaning there is no direct capital outlay for payroll, reducing the financial risk of the "moonshot" approach.

### 1.4 Strategic Goals
- Establish a secure, on-premise marketplace capable of handling millions of SKUs.
- Ensure 100% compliance with EU data residency laws (GDPR) and CCPA.
- Achieve a customer Net Promoter Score (NPS) of >40 within Q1 post-launch.
- Reduce manual order processing time for end-users by 50%.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Trellis utilizes a hybrid approach. While the core business logic is written in Java/Spring Boot for stability and type safety, the execution model leverages serverless functions orchestrated via an API Gateway. This provides the scalability of microservices while maintaining the centralized control required by our on-premise data center constraints.

**Critical Constraint:** No cloud providers (AWS, Azure, GCP) are permitted. All infrastructure must reside within the Ridgeline Platforms on-premise data center.

### 2.2 The Tech Stack
- **Backend:** Java 17 / Spring Boot 3.1
- **Database:** Oracle DB 19c (Enterprise Edition)
- **Orchestration:** Proprietary API Gateway (Internal Ridgeline Implementation)
- **Runtime:** Serverless function wrappers deployed via internal Kubernetes (K8s) clusters.
- **Security:** SAML 2.0 / OIDC for Identity Management.
- **Frontend:** React 18 with TypeScript.

### 2.3 ASCII Architecture Diagram
The following diagram describes the request flow from the end-user to the data layer.

```text
[ User Browser ] <--> [ HTTPS / TLS 1.3 ] <--> [ Internal Load Balancer ]
                                                         |
                                                         v
                                             [ API Gateway Orchestrator ]
                                             /           |           \
                    ________________________/            |            \________________________
                   |                                     |                                    |
         [ Function: Auth/SSO ]                [ Function: Marketplace ]            [ Function: File Manager ]
         (SAML/OIDC Validation)                 (Order/Product Logic)                 (Virus Scan/CDN Sync)
                   |                                     |                                    |
                   |_____________________________________|____________________________________|
                                                         |
                                             [ Connection Pool (HikariCP) ]
                                                         |
                                             [ Oracle DB 19c (On-Prem) ]
                                             /           |           \
                          [ User Tables ] <---> [ Order Tables ] <---> [ Product Tables ]
```

### 2.4 Data Residency and Security
To comply with GDPR and CCPA, all data for EU citizens must be stored on physically separate hardware clusters located in the Frankfurt data center. The API Gateway handles routing based on the user's `region_id` to ensure data never leaves its designated jurisdiction.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Localization and Internationalization (L10n/I18n)
- **Priority:** Low (Nice to have)
- **Status:** Blocked
- **Description:** Support for 12 distinct languages (English, French, German, Spanish, Italian, Portuguese, Dutch, Polish, Swedish, Danish, Norwegian, and Finnish).
- **Detailed Specification:** 
  The system must implement a dynamic resource bundle mechanism. Instead of hard-coding strings, the frontend will call a `/api/v1/localization/{lang}` endpoint to fetch a JSON map of keys and values.
  - **Dynamic Switching:** Users can change their language preference in the profile settings. The application must update the UI in real-time without a full page reload.
  - **Date/Currency Formatting:** The system must utilize the `java.time` and `java.util.Currency` libraries to format dates and prices based on the user's locale (e.g., DD/MM/YYYY for EU, MM/DD/YYYY for US).
  - **Right-to-Left (RTL) Support:** While not currently required for the 12 target languages, the CSS framework must be designed to support RTL if Arabic or Hebrew are added in later versions.
- **Blocking Issue:** Current disagreement between the Product Lead (Finn) and Engineering regarding whether translation files should be stored in the Oracle DB or as flat files in the filesystem for performance reasons.

### 3.2 Feature 2: SSO Integration with SAML and OIDC
- **Priority:** High
- **Status:** In Progress
- **Description:** Integration with corporate identity providers to allow Single Sign-On.
- **Detailed Specification:**
  The authentication module must support both SAML 2.0 (for legacy enterprise partners) and OpenID Connect (OIDC) for modern integrations.
  - **SAML Workflow:** The system will act as the Service Provider (SP). It will generate an AuthnRequest, redirect the user to the Identity Provider (IdP), and process the signed SAML Assertion upon return.
  - **OIDC Workflow:** Implementation of the Authorization Code Flow with PKCE. The system will redirect to the OIDC provider, receive an authorization code, and exchange it for an ID Token and Access Token.
  - **User Provisioning:** Upon first successful SSO login, the system must "Just-In-Time" (JIT) provision a user account in the Oracle DB, mapping SAML attributes (email, department, role) to internal user roles.
  - **Session Management:** JWTs (JSON Web Tokens) will be used for session persistence, with a maximum TTL of 8 hours and a mandatory refresh token rotation policy.

### 3.3 Feature 3: Customizable Dashboard with Drag-and-Drop Widgets
- **Priority:** Low (Nice to have)
- **Status:** Complete
- **Description:** A user-centric landing page where vendors and buyers can organize their view using widgets.
- **Detailed Specification:**
  The dashboard uses a grid-based coordinate system (X, Y, Width, Height). 
  - **Widget Library:** Pre-defined widgets include "Total Sales Today," "Pending Shipments," "Low Stock Alerts," and "Recent Orders."
  - **Persistence:** The layout state is saved as a JSON blob in the `user_dashboard_configs` table. When a user logs in, the system retrieves the blob and renders the React components accordingly.
  - **Drag-and-Drop Logic:** Implemented via `react-grid-layout`. The system captures the `onLayoutChange` event and debounces a PATCH request to the backend to update the user's preferences.
  - **Customization:** Users can resize widgets or hide them entirely. The "Add Widget" modal allows users to browse available components and drag them onto the canvas.

### 3.4 Feature 4: File Upload with Virus Scanning and CDN Distribution
- **Priority:** High
- **Status:** Complete
- **Description:** Secure upload of product images and regulatory documents with automated security scrubbing.
- **Detailed Specification:**
  The upload pipeline is designed to prevent the introduction of malware into the on-premise environment.
  - **Upload Process:** Files are uploaded via a multipart POST request to `/api/v1/files/upload`.
  - **Virus Scanning:** The file is temporarily staged in a "quarantine" directory. An internal ClamAV instance scans the file. If a threat is detected, the file is immediately deleted, and a `422 Unprocessable Entity` response is returned.
  - **CDN Distribution:** Once cleared, the file is moved to the permanent storage volume and mirrored to the internal CDN (Content Delivery Network) nodes located in regional data centers to reduce latency for image loading.
  - **Content-Type Validation:** Only specific MIME types (PDF, JPG, PNG, TIFF) are allowed. Magic-byte validation is performed to prevent users from bypassing filters by renaming `.exe` files to `.jpg`.

### 3.5 Feature 5: Data Import/Export with Format Auto-Detection
- **Priority:** Low (Nice to have)
- **Status:** Complete
- **Description:** Tools for bulk uploading product catalogs and exporting sales reports.
- **Detailed Specification:**
  This feature allows vendors to migrate their inventory into Trellis without manual entry.
  - **Auto-Detection:** The system utilizes a "sniffer" service that reads the first 1KB of the uploaded file to detect the format (CSV, JSON, or XML) based on delimiters and structural markers.
  - **Mapping Engine:** A UI-based mapper allows users to link their source columns (e.g., "Prod_Name") to Trellis internal fields (e.g., `product_title`).
  - **Validation Layer:** Before committing to the database, the system performs a "dry run." It validates data types (e.g., ensuring prices are numeric) and checks for duplicate SKUs.
  - **Export Engine:** Exports are processed asynchronously. The system generates a CSV/JSON file, uploads it to the secure file store, and notifies the user via an internal notification bell when the download link is ready.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/` and require a valid Bearer Token in the header.

### 4.1 `POST /auth/sso/saml`
- **Purpose:** Process incoming SAML assertions from the IdP.
- **Request Body:** `{ "samlResponse": "base64_encoded_string" }`
- **Response (200 OK):** `{ "token": "jwt_access_token", "refresh_token": "jwt_refresh_token", "user_id": "12345" }`
- **Example Error (401):** `{ "error": "INVALID_SIGNATURE", "message": "The SAML assertion signature is invalid." }`

### 4.2 `POST /auth/sso/oidc`
- **Purpose:** Exchange OIDC authorization code for tokens.
- **Request Body:** `{ "code": "auth_code_from_idp", "code_verifier": "pkce_verifier" }`
- **Response (200 OK):** `{ "token": "jwt_access_token", "expires_in": 28800 }`

### 4.3 `POST /files/upload`
- **Purpose:** Secure file upload with virus scanning.
- **Request Body:** `multipart/form-data` (File: `document`, Type: `string`)
- **Response (201 Created):** `{ "file_id": "uuid-987", "url": "https://cdn.ridgeline.internal/files/uuid-987", "status": "scanned" }`
- **Example Error (422):** `{ "error": "VIRUS_DETECTED", "message": "File failed security scan." }`

### 4.4 `GET /products`
- **Purpose:** Retrieve a list of food/beverage products.
- **Query Params:** `page`, `size`, `category`, `search`
- **Response (200 OK):** 
  ```json
  {
    "content": [
      { "id": 101, "name": "Organic Almond Milk", "price": 4.50, "stock": 500 }
    ],
    "totalElements": 1500,
    "totalPages": 15
  }
  ```

### 4.5 `POST /orders`
- **Purpose:** Place a new order in the marketplace.
- **Request Body:** `{ "items": [{ "sku": "ALM-01", "qty": 10 }], "shipping_address_id": "addr_55" }`
- **Response (201 Created):** `{ "order_id": "ORD-2023-001", "status": "PENDING", "estimated_delivery": "2023-11-01" }`

### 4.6 `PATCH /user/dashboard/layout`
- **Purpose:** Save a new widget layout configuration.
- **Request Body:** `{ "layout": [{ "i": "widget_1", "x": 0, "y": 0, "w": 2, "h": 2 }] }`
- **Response (200 OK):** `{ "status": "saved", "timestamp": "2023-10-24T10:00:00Z" }`

### 4.7 `POST /import/catalog`
- **Purpose:** Bulk upload of product data with auto-detection.
- **Request Body:** `multipart/form-data` (File: `catalog_file`)
- **Response (202 Accepted):** `{ "job_id": "job_abc_123", "status": "processing", "eta_seconds": 30 }`

### 4.8 `GET /export/reports/sales`
- **Purpose:** Trigger a sales report export.
- **Query Params:** `startDate`, `endDate`, `format` (CSV/JSON)
- **Response (200 OK):** `{ "download_url": "https://cdn.ridgeline.internal/exports/report_xyz.csv", "expires_at": "2023-10-25T00:00:00Z" }`

---

## 5. DATABASE SCHEMA

The system uses an Oracle 19c relational database. All tables use `VARCHAR2` for strings and `NUMBER` for numeric values to maintain Oracle standards.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role_id` | 1:N with `orders` | User account details |
| `roles` | `role_id` | `role_name`, `permissions_bitmask` | 1:N with `users` | RBAC definitions |
| `products` | `product_id` | `sku`, `title`, `price`, `category_id` | N:1 with `categories` | Master product catalog |
| `categories` | `category_id` | `category_name`, `parent_id` | Self-referencing | F&B categories (Dairy, Grains, etc.) |
| `orders` | `order_id` | `user_id`, `order_date`, `total_amount` | N:1 with `users` | Header-level order data |
| `order_items` | `item_id` | `order_id`, `product_id`, `quantity` | N:1 with `orders`, `products` | Line items for orders |
| `inventory` | `inv_id` | `product_id`, `warehouse_id`, `stock_qty` | N:1 with `products` | Stock levels per location |
| `warehouses` | `warehouse_id` | `location_name`, `region_code` | 1:N with `inventory` | Physical storage sites |
| `user_dashboard_configs` | `config_id` | `user_id`, `layout_json`, `updated_at` | N:1 with `users` | Widget layout state |
| `files` | `file_id` | `filename`, `storage_path`, `mime_type`, `is_scanned` | N:1 with `users` (uploader) | Document metadata |

### 5.2 Entity Relationship (ER) Logic
- **User $\to$ Order:** One-to-Many. A user can place multiple orders over time.
- **Order $\to$ OrderItems:** One-to-Many. Each order consists of multiple product line items.
- **Product $\to$ Inventory:** One-to-Many. A single product may be stored in multiple warehouses across different EU regions.
- **User $\to$ DashboardConfig:** One-to-One. Each user has exactly one active dashboard layout configuration.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Trellis follows a strict promotion path to ensure stability and regulatory compliance.

#### 6.1.1 Development (DEV)
- **Purpose:** Initial feature coding and unit testing.
- **Hardware:** Small-footprint VM cluster.
- **Database:** Shared Oracle instance with mocked data.
- **Deployment:** Continuous Integration (CI) triggers automatic deploy upon merge to `develop` branch.

#### 6.1.2 Staging (STG)
- **Purpose:** Pre-production testing, QA validation, and User Acceptance Testing (UAT).
- **Hardware:** Mirror of Production hardware.
- **Database:** Sanitized copy of production data.
- **Deployment:** Weekly builds from `release` branch.

#### 6.1.3 Production (PROD)
- **Purpose:** Live user traffic.
- **Hardware:** High-availability (HA) cluster with load balancing across three physical nodes.
- **Database:** Oracle RAC (Real Application Clusters) for zero downtime.
- **Deployment:** **Quarterly Releases.** Aligned with regulatory review cycles to ensure compliance with F&B laws.

### 6.2 Infrastructure Constraints
- **Network:** All traffic is routed through an internal corporate firewall. No public internet access is allowed for the database layer.
- **Storage:** High-performance SAN (Storage Area Network) for the Oracle DB and a separate distributed file system for the CDN mirrors.
- **Backup:** Nightly snapshots of the database with a 30-day retention period.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Requirement:** All new code in the `auth` and `files` modules must maintain $\geq 80\%$ line coverage.
- **Note:** The core billing module currently has **0% coverage** (Technical Debt). This is a critical risk.

### 7.2 Integration Testing
- **Focus:** API Gateway orchestration and Oracle DB persistence.
- **Approach:** Using Testcontainers to spin up a temporary Oracle instance for each test suite to ensure a clean state.
- **Key Scenarios:** SAML handshake flows, file upload $\to$ virus scan $\to$ CDN move.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium and Playwright.
- **Scope:** Critical user paths (The "Happy Path"):
  1. Login via SSO $\to$ Search Product $\to$ Add to Cart $\to$ Checkout.
  2. Vendor Login $\to$ Upload Catalog $\to$ Verify Inventory Update.
  3. User Login $\to$ Reorganize Dashboard $\to$ Refresh Page $\to$ Verify Layout.

### 7.4 QA Lead Oversight
Isadora Fischer oversees all test cycles. No release may move from Staging to Production without a signed "QA Readiness Report" and a zero-critical-bug count.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for F&B are shifting. | High | High | Build a "Strategy Pattern" into the architecture to allow fallback/alternative logic without rewriting the core. |
| R-02 | Integration partner API is buggy/undocumented. | High | Medium | Engage an external consultant for a 4-week independent assessment and reverse-engineering of the API. |
| R-03 | Lack of test coverage on billing module. | Medium | Critical | Schedule a "Technical Debt Sprint" in Q1 2024 to retroactively apply unit tests to the billing logic. |
| R-04 | On-premise hardware capacity limits. | Low | Medium | Maintain a hardware requisition list to trigger procurement 6 months before capacity hits 80%. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt.
- **High:** Significant delay or cost increase.
- **Medium:** Manageable with current resources.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

Trellis follows a phased approach leading up to the 2026 production launch.

### 9.1 Phase 1: Foundation (Current – 2024-12)
- Setup of on-premise serverless environment.
- Completion of SSO (SAML/OIDC) integration.
- Finalization of Oracle DB schema.
- **Dependency:** Resolution of design disagreement between Finn and Engineering.

### 9.2 Phase 2: Feature Build-out (2025-01 – 2025-12)
- Implementation of Marketplace logic.
- Integration of Virus Scanning and CDN.
- Dashboard widget finalization.
- Initial regulatory audit.

### 9.3 Phase 3: Hardening & Beta (2026-01 – 2026-05)
- Stress testing (load tests up to 10k concurrent users).
- Final bug scrubbing.
- Deployment to Production.

### 9.4 Key Milestones
- **Milestone 1: Production Launch** $\to$ **Target: 2026-05-15**
- **Milestone 2: Post-launch Stability Confirmed** $\to$ **Target: 2026-07-15** (Measured by 99.9% uptime over 60 days).
- **Milestone 3: External Beta (10 Pilot Users)** $\to$ **Target: 2026-09-15**

---

## 10. MEETING NOTES

*Note: The following are summaries of recorded video calls. Per team culture, these calls are recorded but rarely re-watched; these summaries serve as the official record.*

### Meeting 1: Architecture Sync (Date: 2023-08-12)
- **Attendees:** Finn Nakamura, Nia Nakamura, Engineering Team.
- **Discussion:** Discussion on whether to use a cloud-native approach for the CDN.
- **Outcome:** Finn reiterated the "No Cloud" mandate from executive sponsorship. The team agreed to build an internal CDN using regional on-premise mirrors.
- **Decision:** The project will use Oracle DB 19c for all persistence.

### Meeting 2: The "Design Deadlock" (Date: 2023-09-05)
- **Attendees:** Finn Nakamura, Engineering Lead, Nia Nakamura.
- **Discussion:** Heatly debate over the Localization (L10n) implementation. Finn wants the translations stored in the database for "instant updates." Engineering argues for flat files to prevent database bloat and increase cache hits.
- **Outcome:** No agreement reached.
- **Decision:** Feature 1 (Localization) is officially marked as **Blocked**.

### Meeting 3: Technical Debt Review (Date: 2023-10-01)
- **Attendees:** Isadora Fischer, Camila Kim, Finn Nakamura.
- **Discussion:** Isadora raised a red flag regarding the billing module. It was deployed to the dev environment without a single unit test to meet an internal milestone.
- **Outcome:** Finn acknowledged the pressure but insisted the timeline cannot move.
- **Decision:** The technical debt is documented in the risk register. Camila will monitor for billing bugs in the support queue as a "manual" safety net.

---

## 11. BUDGET BREAKDOWN

Because the project is bootstrapping with existing team capacity, the "Budget" refers to allocated internal resources and operational expenses rather than new capital.

| Category | Allocation | Details | Annual Estimated Cost |
| :--- | :--- | :--- | :--- |
| **Personnel** | Internal Capacity | 20+ staff across 3 departments | $3,200,000 (Sunk Cost) |
| **Infrastructure** | On-Prem Server Cost | Power, cooling, rack space in EU/US | $150,000 |
| **Software Licenses** | Oracle Enterprise | Licensing for Oracle DB 19c | $200,000 |
| **Tools** | Security/Scanning | ClamAV (Open Source) + Proprietary Tools | $25,000 |
| **Contingency** | External Consultant | Budget for API partner assessment | $50,000 |
| **TOTAL** | | | **$3,625,000** |

---

## 12. APPENDICES

### Appendix A: Data Residency Mapping
To comply with GDPR, the following routing logic is implemented at the API Gateway:
- `If user.region == 'EU' $\to$ Route to Frankfurt Cluster (FRA-01)`
- `If user.region == 'US' $\to$ Route to Ashburn Cluster (ASH-02)`
- `If user.region == 'APAC' $\to$ Route to Singapore Cluster (SGP-03)`
Cross-region data replication is disabled for `user_profile` and `order_history` tables to prevent illegal data transfer.

### Appendix B: Virus Scanning Pipeline Logic
The sequence for Feature 4 is as follows:
1. **Inbound:** Request arrives $\to$ `POST /files/upload`.
2. **Staging:** File written to `/tmp/quarantine/`.
3. **Scan:** Trigger `clamscan --infected /tmp/quarantine/[file_id]`.
4. **Evaluation:**
   - If exit code $\neq 0 \to$ Delete file $\to$ Return 422.
   - If exit code $= 0 \to$ Move file to `/mnt/storage/cdn_origin/`.
5. **Distribution:** Signal CDN nodes to pull the new object via internal webhook.