# Project Specification Document: Project Umbra
**Version:** 1.0.4  
**Date:** October 24, 2025  
**Project Status:** Active / Urgent  
**Company:** Silverthread AI  
**Classification:** Internal Confidential  

---

## 1. Executive Summary

### 1.1 Project Overview
Project Umbra is a mission-critical e-commerce marketplace initiative designed specifically for the education sector. The project is commissioned by Silverthread AI to address an urgent regulatory compliance window. The primary objective is to build a robust, scalable marketplace that allows educational providers to list, manage, and sell compliant curriculum materials and certifications. Due to a hard legal deadline imposed by educational governing bodies, the project must be fully production-ready within six months.

### 1.2 Business Justification
The education industry is currently undergoing a seismic shift in regulatory requirements regarding the distribution of digital learning materials. Failure to comply with these emerging standards by the mandated deadline will result in significant fines and the potential loss of Silverthread AI’s operating licenses in key jurisdictions. Umbra is not merely a product expansion but a survival mechanism. By providing a centralized, compliant marketplace, Silverthread AI can capture the "compliance-as-a-service" market, positioning itself as the primary infrastructure provider for educational institutions transitioning to the new regulatory framework.

### 1.3 ROI Projection and Success Metrics
The financial justification for Project Umbra is based on a modest but focused investment of $400,000. The return on investment (ROI) is projected across two primary vectors: direct revenue and risk mitigation.

**Metric 1: Revenue Generation**  
The target is to generate $500,000 in new revenue attributed specifically to the Umbra platform within the first 12 months of launch. This will be achieved through a transaction fee model (5% per sale) and monthly subscription tiers for premium educational vendors. Given the urgency of the regulatory deadline, we anticipate a high initial adoption rate as vendors rush to find compliant hosting solutions.

**Metric 2: Customer Satisfaction**  
Success will be measured by a Net Promoter Score (NPS) of >40 within the first quarter post-launch. Because the industry is currently frustrated by the complexity of these new regulations, a streamlined, intuitive user experience will be a significant competitive advantage.

**Strategic ROI**  
Beyond the $500k target, the project prevents an estimated $1.2M in potential regulatory fines and protects existing revenue streams that would be jeopardized by non-compliance.

---

## 2. Technical Architecture

### 2.1 Architecture Overview
Umbra employs a traditional three-tier architecture consisting of the Presentation Layer, Business Logic Layer, and Data Layer. However, the project is uniquely challenged by a "Mixed Stack" inheritance. The system must interoperate across three legacy stacks inherited from previous Silverthread AI acquisitions:
1. **Stack A (Legacy PHP/MySQL):** Handles legacy user profiles.
2. **Stack B (Node.js/MongoDB):** Handles the cataloging engine.
3. **Stack C (Python/PostgreSQL):** Handles the compliance and auditing engine.

The architecture focuses on a "Unified API Gateway" approach to abstract the complexities of these three disparate backends from the frontend.

### 2.2 ASCII Architectural Diagram

```text
[ USER BROWSER / MOBILE APP ]  <-- (Presentation Layer: React/TypeScript)
             |
             v
[     API GATEWAY / LOAD BALANCER     ]  <-- (Nginx / Kong)
             |
             +---------------------------------------+
             |                                       |
             v                                       v
[ BUSINESS LOGIC LAYER (Orchestration) ]    [ AUTH SERVICE (RBAC) ]
             |                                       |
             +-------------------+-------------------+
             |                   |                   |
             v                   v                   v
    [ SERVICE A (PHP) ]  [ SERVICE B (Node) ]  [ SERVICE C (Python) ]
    (User Profiles)      (Catalog/Search)     (Compliance Engine)
             |                   |                   |
             v                   v                   v
    [ MySQL DB ]         [ MongoDB Cluster ]  [ PostgreSQL DB ]
             |                   |                   |
             +-------------------+-------------------+
                                 |
                        [ DATA PERSISTENCE LAYER ]
```

### 2.3 Deployment Strategy: The Weekly Release Train
Umbra follows a strict **Weekly Release Train** deployment model. 
- **Release Cycle:** Every Thursday at 03:00 UTC.
- **Cut-off:** Wednesday 18:00 UTC. All code must be merged and passed through staging.
- **No Hotfixes:** To maintain stability during this high-pressure compliance window, there are no hotfixes outside the train. If a bug is discovered on Friday, it must wait until the following Thursday's train. This enforces a culture of rigorous testing and prevents "panic patching" which could introduce regression errors into the compliance logic.

### 2.4 Security Posture
Security is handled via an **internal security audit only**. Because the project is hosted on internal Silverthread AI infrastructure and serves a specific B2B educational niche, external third-party certifications (like SOC2 or PCI-DSS) are not required for the initial launch, though internal penetration testing will be conducted prior to Milestone 2.

---

## 3. Detailed Feature Specifications

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Umbra requires a robust authentication system to manage three distinct user personas: *Administrators* (Silverthread staff), *Vendors* (Educational institutions), and *Buyers* (Students/Schools). Because the project inherits three legacy stacks, the authentication system must act as a Single Sign-On (SSO) wrapper.

**Detailed Specifications:**
- **Authentication Flow:** Implementation of OAuth 2.0 with JWT (JSON Web Tokens) for session management. Tokens will have a 24-hour expiration with a refresh token rotation strategy.
- **Role Hierarchy:**
    - `SUPER_ADMIN`: Full system access, ability to override vendor compliance flags.
    - `VENDOR_ADMIN`: Manage store settings, upload products, view sales analytics.
    - `VENDOR_STAFF`: Edit products and fulfill orders without access to financial settings.
    - `BUYER`: Browse marketplace, purchase items, manage personal library.
- **RBAC Enforcement:** Access control will be enforced at the API Gateway level. Each request must contain a JWT. The gateway will verify the `role` claim before routing the request to the business logic layer.
- **Password Policy:** Minimum 12 characters, requiring uppercase, lowercase, numeric, and special characters, utilizing bcrypt for hashing.

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Educational vendors possess vast catalogs of materials in fragmented formats. To ensure rapid onboarding, Umbra must provide a tool that allows vendors to upload bulk data without manual mapping.

**Detailed Specifications:**
- **Supported Formats:** CSV, JSON, XML, and XLSX.
- **Auto-Detection Logic:** The system will read the first 10 lines of an uploaded file to identify the MIME type and delimiter. It will then use a "Heuristic Mapping Engine" to correlate column headers (e.g., "CourseName", "Title", "Product_Title") to the internal `product_name` database field.
- **Validation Pipeline:**
    - *Stage 1 (Schema Validation):* Check if required fields (Price, SKU, Compliance ID) are present.
    - *Stage 2 (Data Sanitization):* Strip HTML tags and trim whitespace.
    - *Stage 3 (Conflict Resolution):* If a SKU already exists, the system will prompt the user to "Overwrite" or "Skip."
- **Export Capability:** Users can export their entire catalog or filtered subsets in any of the supported formats for backup or external auditing.

### 3.3 Localization and Internationalization (L10n/I18n)
**Priority:** High | **Status:** In Progress

**Description:**
To serve the global education market, Umbra must support 12 specific languages (English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Italian, Russian, and Hindi).

**Detailed Specifications:**
- **Implementation Strategy:** Using `i18next` on the frontend and a translation key-value store in PostgreSQL on the backend.
- **Dynamic Content:** While UI elements are translated via keys, product descriptions will utilize a "Translation Table" where vendors can provide translated versions of their listings.
- **RTL Support:** The UI must support Right-to-Left (RTL) layouts for Arabic, triggering a CSS mirror shift for the entire dashboard.
- **Locale Detection:** The system will detect the user's browser language via the `Accept-Language` header and default to English if no match is found.
- **Currency Handling:** Integration of a real-time exchange rate API to display prices in the local currency of the buyer, while maintaining the vendor's base currency for accounting.

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** High | **Status:** In Design

**Description:**
With thousands of educational resources, users need a way to find specific compliant materials quickly. This requires more than a simple SQL `LIKE` query.

**Detailed Specifications:**
- **Indexing Engine:** Integration of Elasticsearch to provide full-text indexing of product titles, descriptions, and tags.
- **Faceted Filtering:** Users must be able to filter results by:
    - *Education Level* (K-12, Undergraduate, Postgraduate)
    - *Compliance Standard* (e.g., GDPR-Edu, ISO-Learn)
    - *Price Range* (Sliding scale)
    - *Vendor Rating* (1-5 stars)
- **Search Logic:** Implementation of "Fuzzy Matching" to account for typos in educational terminology.
- **Ranking Algorithm:** Search results will be ranked based on a combination of keyword relevance, vendor reliability, and "Compliant Status" (Compliant products are boosted to the top).

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:**
To protect the system from abuse and provide data on API consumption, a rate-limiting layer is required.

**Detailed Specifications:**
- **Throttling Logic:** A "Token Bucket" algorithm implemented in Redis.
- **Tiers:**
    - *Standard:* 1,000 requests per hour.
    - *Premium:* 10,000 requests per hour.
- **Analytics Tracking:** Every request will be logged to a time-series database (InfluxDB) capturing:
    - Endpoint hit.
    - Response time (latency).
    - HTTP Status code.
    - User ID.
- **Dashboard:** A simple admin view to visualize the top 10 most active API consumers and the most frequent "429 Too Many Requests" errors.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1`.

### 4.1 Auth Endpoints
**POST `/auth/login`**
- **Description:** Authenticates user and returns JWT.
- **Request Body:** `{"email": "user@edu.com", "password": "password123"}`
- **Response (200):** `{"token": "eyJhbG...", "expires_in": 86400, "role": "VENDOR_ADMIN"}`
- **Response (401):** `{"error": "Invalid credentials"}`

**POST `/auth/refresh`**
- **Description:** Rotates the refresh token for a new session.
- **Request Body:** `{"refresh_token": "ref_abc123"}`
- **Response (200):** `{"token": "eyJhbG...", "refresh_token": "ref_xyz456"}`

### 4.2 Catalog Endpoints
**GET `/catalog/search`**
- **Description:** Full-text search with filters.
- **Query Params:** `?q=calculus&level=undergrad&page=1`
- **Response (200):** `{"results": [{"id": "p1", "name": "Calc 101", "price": 49.99}], "total": 150}`

**POST `/catalog/import`**
- **Description:** Uploads a file for auto-detection import.
- **Request Body:** Multipart Form Data (File upload).
- **Response (202):** `{"job_id": "job_998", "status": "Processing"}`

### 4.3 Compliance Endpoints
**GET `/compliance/verify/{productId}`**
- **Description:** Checks if a product meets current regulatory standards.
- **Response (200):** `{"productId": "p1", "is_compliant": true, "last_audit": "2025-10-01"}`

**PATCH `/compliance/update-status`**
- **Description:** Admin update of compliance status.
- **Request Body:** `{"productId": "p1", "status": "FAILED", "reason": "Missing certification X"}`
- **Response (200):** `{"status": "Updated"}`

### 4.4 User/Profile Endpoints
**GET `/user/profile`**
- **Description:** Fetches the authenticated user's profile.
- **Response (200):** `{"id": "u1", "name": "Dr. Smith", "email": "smith@edu.com", "role": "VENDOR_ADMIN"}`

**PUT `/user/settings`**
- **Description:** Updates user preferences and localization settings.
- **Request Body:** `{"language": "fr", "currency": "EUR"}`
- **Response (200):** `{"status": "Settings saved"}`

---

## 5. Database Schema

The data layer is distributed. Below is the conceptual schema for the primary PostgreSQL instance (Compliance & Core) and references to the others.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | N/A | `email`, `password_hash`, `role` | Master user records |
| `profiles` | `profile_id` | `user_id` | `full_name`, `locale`, `timezone` | User personalization |
| `vendors` | `vendor_id` | `user_id` | `company_name`, `tax_id`, `verification_status` | Store owner details |
| `products` | `product_id` | `vendor_id` | `sku`, `base_price`, `category_id` | Core product metadata |
| `product_translations` | `trans_id` | `product_id` | `language_code`, `translated_name`, `translated_desc` | Localized content |
| `compliance_logs` | `log_id` | `product_id` | `audit_date`, `status`, `auditor_id` | Regulatory history |
| `orders` | `order_id` | `buyer_id`, `vendor_id` | `total_amount`, `order_date`, `status` | Transaction record |
| `order_items` | `item_id` | `order_id`, `product_id` | `quantity`, `price_at_purchase` | Line items for orders |
| `categories` | `cat_id` | N/A | `category_name`, `parent_id` | Product hierarchy |
| `api_keys` | `key_id` | `user_id` | `api_key_hash`, `rate_limit_tier` | API access control |

### 5.2 Relationships
- `users` $\rightarrow$ `profiles` (1:1)
- `users` $\rightarrow$ `vendors` (1:1 or 1:0)
- `vendors` $\rightarrow$ `products` (1:N)
- `products` $\rightarrow$ `product_translations` (1:N)
- `products` $\rightarrow$ `compliance_logs` (1:N)
- `orders` $\rightarrow$ `order_items` (1:N)

---

## 6. Deployment and Infrastructure

### 6.1 Environment Descriptions

#### Development (Dev)
- **Purpose:** Active feature development and unit testing.
- **Configuration:** Local Docker containers mirroring the mixed-stack environment.
- **Deployment:** Continuous integration on every push to `develop` branch.

#### Staging (Stage)
- **Purpose:** Pre-production validation, UAT, and "Release Train" staging.
- **Configuration:** Exact replica of Production (AWS t3.medium instances).
- **Deployment:** Merged on Wednesdays. This environment is where the "Internal Security Audit" takes place.

#### Production (Prod)
- **Purpose:** Live user traffic and regulatory compliance.
- **Configuration:** Auto-scaling groups across two availability zones.
- **Deployment:** Weekly Thursday 03:00 UTC release train.

### 6.2 Infrastructure Blocker
**Current Issue:** Infrastructure provisioning is currently delayed by the cloud provider. We are unable to spin up the Production VPC and the MongoDB cluster. 
**Workaround:** The team is currently using a shared "Legacy Sandbox" environment for integration tests, but this is creating a bottleneck for the Frontend Lead.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Requirement:** 80% code coverage for all new business logic.
- **Tools:** Jest (Frontend), PyTest (Python/Compliance), PHPUnit (Legacy).
- **Focus:** Testing individual functions, especially the "Heuristic Mapping Engine" for data imports.

### 7.2 Integration Testing
- **Requirement:** All API endpoints must have a corresponding integration test.
- **Focus:** Validating the flow between the three legacy stacks. Specifically, testing if a user created in Stack A can successfully purchase a product managed by Stack B and be audited by Stack C.
- **Tool:** Postman / Newman for automated collection runs.

### 7.3 End-to-End (E2E) Testing
- **Requirement:** Critical paths (Login $\rightarrow$ Search $\rightarrow$ Checkout $\rightarrow$ Compliance Check) must be automated.
- **Tool:** Cypress.
- **Frequency:** Run against Staging every Tuesday to ensure the Wednesday cut-off is viable.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements change before launch | High | High | Build a "Policy Engine" where rules can be updated via JSON config without changing core code. |
| R-02 | Primary vendor (Compliance API) EOL | Medium | High | Engage external consultant for independent assessment of open-source alternatives. |
| R-03 | Infrastructure delay prolongs | High | Medium | Utilize multi-cloud strategy (Azure failover) if current provider fails to provision. |
| R-04 | Tech Debt (Raw SQL) causes data loss | Medium | High | Implement a strict "Migration Review" phase where any raw SQL is audited for syntax and schema compatibility. |

---

## 9. Timeline

### 9.1 Phase Overview

**Phase 1: Foundation & Auth (Months 1-2)**
- *Focus:* RBAC implementation, Legacy Stack integration, Infrastructure setup.
- *Dependency:* Cloud provider provisioning.
- *Target:* Internal Alpha.

**Phase 2: Data & Localization (Months 3-4)**
- *Focus:* Import/Export engine, 12-language support, Basic Search.
- *Dependency:* Finalized regulatory data formats.
- *Target:* Milestone 1 (First paying customer) - **2026-06-15**.

**Phase 3: Refinement & Compliance (Months 5-6)**
- *Focus:* Advanced search, Faceted filtering, Full-text indexing, Security audit.
- *Dependency:* Completion of Phase 2.
- *Target:* Milestone 2 (Production Launch) - **2026-08-15**.

**Phase 4: Optimization (Post-Launch)**
- *Focus:* Rate limiting, Usage analytics, Performance tuning.
- *Target:* Milestone 3 (Performance benchmarks) - **2026-10-15**.

---

## 10. Meeting Notes (Slack Thread Archives)

*Note: As per company policy, formal notes are not taken. Decisions are extracted from Slack threads.*

### Thread: #umbra-dev-sync (2025-11-02)
**Participants:** Juno Gupta, Omar Gupta, Viktor Park
**Discussion:** Omar raised concerns that the legacy PHP stack is too slow for the frontend's new React state management. 
**Decision:** Juno decided that the API Gateway will implement a Redis cache for user profile data, reducing the number of direct hits to the PHP backend. Omar to implement the cache layer by next Thursday's train.

### Thread: #umbra-product-design (2025-11-15)
**Participants:** Viktor Park, Sol Costa
**Discussion:** Viktor presented the RTL (Right-to-Left) mockups for the Arabic locale. Sol noted that the "Compliance Badge" icon might overlap with the price tag in RTL mode.
**Decision:** Viktor will move the badge to a floating header position for RTL layouts to ensure visibility.

### Thread: #umbra-urgent-compliance (2025-12-01)
**Participants:** Juno Gupta, Sol Costa
**Discussion:** Sol discovered that 30% of the legacy queries are bypassing the ORM with raw SQL. Juno expressed concern that a schema migration for the new "Compliance" table will break these queries.
**Decision:** We will not perform a "Big Bang" migration. Instead, we will create a "Shadow Table" and sync data using triggers until the raw SQL queries can be manually refactored.

---

## 11. Budget Breakdown

**Total Budget:** $400,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Salaries for Juno, Omar, Viktor, and contract fees for Sol. |
| **Infrastructure** | 15% | $60,000 | AWS instances, MongoDB Atlas, Redis, and Elasticsearch clusters. |
| **Tools & Licenses** | 10% | $40,000 | i18n services, Postman Enterprise, IDE licenses, and Security audit tools. |
| **Contingency** | 10% | $40,000 | Reserved for external consultant (Risk R-02) and emergency cloud scaling. |

---

## 12. Appendices

### Appendix A: Raw SQL Technical Debt Map
The following tables are currently accessed via raw SQL instead of the ORM and must be handled with extreme caution during migrations:
- `users` (Legacy lookup)
- `product_catalog` (Complex joins for filtering)
- `compliance_audit_trail` (High-volume inserts)
- `vendor_payouts` (Financial calculations)

Any change to these tables requires a sign-off from Juno Gupta (Tech Lead).

### Appendix B: Localization Language Key Mapping
The 12 supported languages are mapped as follows in the system:
- `en`: English (US)
- `es`: Spanish (Spain)
- `fr`: French (France)
- `de`: German (Germany)
- `zh`: Mandarin (Simplified)
- `ja`: Japanese (Japan)
- `ko`: Korean (South Korea)
- `ar`: Arabic (Saudi Arabia) - *RTL*
- `pt`: Portuguese (Brazil)
- `it`: Italian (Italy)
- `ru`: Russian (Russia)
- `hi`: Hindi (India)