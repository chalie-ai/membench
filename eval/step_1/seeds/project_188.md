Due to the extreme length requirements (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Document (PSD). It serves as the "Single Source of Truth" for the development team at Hearthstone Software.

***

# PROJECT SPECIFICATION: PROJECT KEYSTONE
**Version:** 1.0.4  
**Status:** Active/Draft  
**Last Updated:** 2025-10-20  
**Project Lead:** Nadia Jensen (CTO)  
**Classification:** Confidential – Internal Use Only

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Keystone represents a strategic pivot for Hearthstone Software, transitioning from a traditional software vendor to an e-commerce marketplace operator within the real estate sector. The core objective is to establish a high-performance marketplace that allows real estate professionals, developers, and agencies to trade digital assets, lead-generation packages, and proprietary market data. 

The project is not merely a product launch but a strategic partnership integration. Keystone relies on syncing with a third-party external partner’s API. Because this partner controls the data release timeline, Keystone must be built with an exceptionally flexible integration layer to accommodate shifting endpoints and data schemas.

The real estate industry is currently undergoing a digital transformation. By providing a centralized marketplace for high-value real estate data and services, Hearthstone Software positions itself as the "infrastructure layer" of the industry. The ability to monetize these interactions via a subscription and transaction-based model provides a scalable revenue stream that is decoupled from traditional one-time licensing fees.

### 1.2 ROI Projection
With a total investment of $3,000,000, the project is designed to achieve break-even within 18 months post-launch. The ROI is calculated based on the following projections:
*   **Transaction Fees:** A 2.5% marketplace fee on all asset trades.
*   **Subscription Revenue:** Tiered monthly access for power users (Professional: $199/mo, Enterprise: $999/mo).
*   **Data Monetization:** API access fees for third-party aggregators.

The projected Monthly Recurring Revenue (MRR) is estimated at $150,000 by Month 6, assuming the success criterion of 10,000 Monthly Active Users (MAU) is met. Given the high executive visibility of this project, failure to meet these metrics would result in a significant strategic setback for Hearthstone Software’s 2027 growth plan.

### 1.3 Scope and Strategic Alignment
The scope encompasses the development of a secure, on-premise marketplace, the integration of external real estate data, and the implementation of rigorous security protocols compliant with GDPR and CCPA. Because the data must reside in the EU, the architecture is strictly limited to our on-premise data centers, eschewing cloud providers to maintain absolute control over data residency and sovereignty.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Keystone employs a **Modular Monolith** architecture transitioning incrementally toward **Microservices**. This approach allows the team of six to maintain high velocity during the MVP phase while ensuring that the system can be decoupled as the load increases (specifically addressing the 10x capacity requirement).

### 2.2 The Stack
*   **Backend:** Java 21 with Spring Boot 3.2.
*   **Database:** Oracle Database 21c (Enterprise Edition).
*   **Infrastructure:** On-premise bare-metal servers in the EU data center.
*   **Orchestration:** Kubernetes (K8s) managed via an internal control plane.
*   **CI/CD:** GitLab CI with a pipeline configured for rolling deployments.
*   **Security:** Hardware-backed 2FA and AES-256 encryption for data at rest.

### 2.3 System Diagram (ASCII Representation)

```text
[ Client Layer ] ----> [ Load Balancer (F5 Big-IP) ]
                                |
                                v
                    [ Kubernetes Cluster (EU-DC) ]
        ________________________|_________________________
       |                        |                         |
 [ Gateway Service ]    [ Market Engine ]        [ User/Auth Service ]
 (Rate Limiting)        (Matching/Orders)         (2FA/Identity)
       |                        |                         |
       |________________________|_________________________|
                                |
                                v
                    [ Oracle DB 21c Cluster ]
        ________________________|_________________________
       |                        |                         |
 [ User Tables ]        [ Asset Tables ]         [ Audit Logs ]
 (CCPA/GDPR)            (Marketplace Data)       (Tamper-Evident)
                                ^
                                | (External Sync)
                                v
                    [ External Partner API ]
                    (External Timeline/REST)
```

### 2.4 Data Residency and Compliance
To satisfy GDPR and CCPA, the "Data Sovereignty Module" ensures that no PII (Personally Identifiable Information) leaves the EU data center. All logs are scrubbed of PII before being sent to the internal monitoring system.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Progress

**Functional Description:**
To protect the system from exhaustion—especially given the 10x performance requirement—a sophisticated rate-limiting layer is being implemented. This is not a simple "request per minute" counter but a multi-tiered bucket system.

*   **Tiered Limits:** Users are categorized into *Guest, Registered, Professional,* and *Enterprise*. Each tier has specific quotas (e.g., Guest: 100 requests/hr; Enterprise: 50,000 requests/hr).
*   **Algorithm:** Token Bucket Algorithm. This allows for short bursts of traffic while maintaining a steady average rate.
*   **Analytics Engine:** Every request is logged into a high-speed buffer (Redis) and asynchronously persisted to the Oracle DB. This allows the administration team to see real-time usage spikes and identify "noisy neighbors."
*   **Header Response:** The API must return standard headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Implementation:**
Implemented as a Spring Cloud Gateway filter. The filter intercepts every incoming request, checks the API Key/JWT against the `RateLimitConfiguration` table in Oracle, and determines if the request should be allowed or returned with a `429 Too Many Requests` status.

### 3.2 Automated Billing and Subscription Management
**Priority:** Low | **Status:** In Design

**Functional Description:**
This feature manages the financial lifecycle of the marketplace users. Since we are avoiding cloud-based payment processors for certain data residency reasons, this involves a custom integration with our corporate banking API.

*   **Subscription Engine:** Ability to create recurring billing cycles (Monthly, Quarterly, Annually).
*   **Dunning Process:** Automated email notifications and account suspension if a payment fails for more than three consecutive attempts.
*   **Invoice Generation:** Automatic PDF generation of invoices compliant with EU VAT regulations.
*   **Proration Logic:** If a user upgrades from "Professional" to "Enterprise" mid-month, the system must calculate the remaining value and apply it as a credit.

**Technical Implementation:**
A dedicated `BillingService` module. It will utilize a scheduled Spring Quartz job to run nightly, checking for expiring subscriptions and triggering the payment gateway.

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low | **Status:** Blocked

**Functional Description:**
For high-value real estate transactions, a "gold standard" audit trail is required. This means every change to a property listing or a financial transaction must be immutable.

*   **Immutability:** Once a log is written, it cannot be edited or deleted, even by a DBA.
*   **Hashing Chain:** Each log entry will contain a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody.
*   **Verification Tool:** An internal admin tool that can scan the chain and report any "breaks" in the hash sequence, indicating unauthorized data modification.
*   **Storage:** Logs are stored in a separate, read-only Oracle Tablespace with strict filesystem-level permissions.

**Blocker Detail:** This feature is currently blocked due to the unavailability of the Security Architecture Lead (on medical leave), as the hashing strategy must be vetted against corporate security standards.

### 3.4 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low | **Status:** Complete

**Functional Description:**
Given the financial nature of the marketplace, standard passwords are insufficient. This feature provides multi-layered identity verification.

*   **TOTP Support:** Integration with Google Authenticator and Authy using time-based one-time passwords.
*   **FIDO2/WebAuthn:** Support for physical hardware keys (e.g., YubiKey). This is critical for "Enterprise" users managing millions in assets.
*   **Recovery Codes:** Generation of ten 8-character recovery codes upon 2FA activation.
*   **Step-up Authentication:** The system triggers a 2FA prompt specifically when a user attempts to change their bank details or execute a trade over $10,000.

**Technical Implementation:**
Implemented using Spring Security. Hardware key support is handled via a WebAuthn library, managing public key registration and challenge-response verification.

### 3.5 A/B Testing Framework (Feature Flag System)
**Priority:** High | **Status:** Blocked

**Functional Description:**
To optimize the marketplace conversion rate, the team needs to test different UX layouts and pricing models without deploying new code.

*   **Feature Flags:** Ability to toggle features on/off for specific percentages of the user base (e.g., 10% of users see the "New Checkout" flow).
*   **Metric Tracking:** Automatic linking of A/B buckets to conversion metrics (e.g., "Did Bucket B result in more completed purchases?").
*   **Targeting Rules:** Ability to target flags by region (EU vs. Non-EU) or user tier.
*   **Dynamic Configuration:** Changes to flags should take effect in real-time without requiring a pod restart in Kubernetes.

**Blocker Detail:** Blocked by the "Risk 2" performance issue. The current overhead of checking feature flags for every request is adding 15ms of latency, which, when compounded across 10x current capacity, threatens the system's stability.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful conventions and require a `Bearer` token in the Authorization header.

### 4.1 Listing Endpoints

**`GET /api/v1/listings`**
*   **Description:** Retrieves a paginated list of real estate assets.
*   **Request Params:** `page` (int), `size` (int), `category` (string), `minPrice` (decimal).
*   **Response (200 OK):**
    ```json
    {
      "content": [
        {"id": "LIST-9921", "title": "Berlin Commercial Hub", "price": 4500000.00, "status": "available"}
      ],
      "totalElements": 1450,
      "totalPages": 15
    }
    ```

**`POST /api/v1/listings`**
*   **Description:** Creates a new asset listing.
*   **Request Body:**
    ```json
    {
      "title": "Madrid Residential Block",
      "description": "Prime location...",
      "price": 1200000.00,
      "category": "Residential"
    }
    ```
*   **Response (201 Created):** `{"id": "LIST-9922", "status": "pending_review"}`

### 4.2 Transaction Endpoints

**`POST /api/v1/trades/execute`**
*   **Description:** Initiates the purchase of a listing.
*   **Request Body:**
    ```json
    {
      "listingId": "LIST-9921",
      "paymentMethodId": "PM-441",
      "currency": "EUR"
    }
    ```
*   **Response (202 Accepted):** `{"transactionId": "TX-88102", "status": "processing"}`

**`GET /api/v1/trades/{txId}`**
*   **Description:** Checks the status of a specific transaction.
*   **Response (200 OK):** `{"transactionId": "TX-88102", "status": "completed", "timestamp": "2026-09-12T14:00:00Z"}`

### 4.3 User and Account Endpoints

**`POST /api/v1/auth/2fa/register`**
*   **Description:** Registers a new hardware key or TOTP seed.
*   **Request Body:** `{"type": "WEBAUTHN", "publicKey": "..."}`
*   **Response (200 OK):** `{"status": "registered"}`

**`GET /api/v1/users/me/usage`**
*   **Description:** Returns current API usage analytics for the user.
*   **Response (200 OK):**
    ```json
    {
      "currentPeriod": "2025-10",
      "requestsUsed": 4500,
      "limit": 10000,
      "remaining": 5500
    }
    ```

### 4.4 Subscription Endpoints

**`PUT /api/v1/subscriptions/upgrade`**
*   **Description:** Changes the user's billing tier.
*   **Request Body:** `{"newTier": "Enterprise"}`
*   **Response (200 OK):** `{"status": "upgraded", "nextBillingDate": "2025-11-01"}`

**`GET /api/v1/billing/invoices`**
*   **Description:** Retrieves a list of past invoices.
*   **Response (200 OK):**
    ```json
    [
      {"invoiceId": "INV-001", "amount": 199.00, "date": "2025-09-01", "pdfUrl": "/api/v1/billing/download/INV-001"}
    ]
    ```

---

## 5. DATABASE SCHEMA

The system utilizes Oracle DB 21c. All tables use `VARCHAR2` for strings and `NUMBER` for decimals to maintain precision for financial transactions.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `USERS` | `user_id` | `email`, `password_hash`, `tier_id`, `mfa_enabled` | 1:N with `ORDERS` |
| `USER_TIERS` | `tier_id` | `tier_name`, `monthly_rate`, `api_limit` | 1:N with `USERS` |
| `LISTINGS` | `listing_id` | `owner_id`, `title`, `price`, `status`, `category` | N:1 with `USERS` |
| `ORDERS` | `order_id` | `buyer_id`, `listing_id`, `amount`, `status` | N:1 with `USERS`, `LISTINGS` |
| `TRANSACTIONS`| `tx_id` | `order_id`, `gateway_ref`, `amount`, `currency` | 1:1 with `ORDERS` |
| `AUDIT_LOGS` | `log_id` | `entity_id`, `action`, `timestamp`, `prev_hash`, `curr_hash` | N:1 with `USERS` |
| `BILLING_SUBS`| `sub_id` | `user_id`, `tier_id`, `start_date`, `next_bill_date` | N:1 with `USERS`, `USER_TIERS` |
| `INVOICES` | `inv_id` | `sub_id`, `amount`, `vat_amount`, `issue_date` | N:1 with `BILLING_SUBS` |
| `API_USAGE` | `usage_id` | `user_id`, `endpoint`, `request_time`, `response_code` | N:1 with `USERS` |
| `HARDWARE_KEYS`| `key_id` | `user_id`, `public_key`, `credential_id`, `created_at` | N:1 with `USERS` |

### 5.2 Schema Relationships and Constraints
*   **Referential Integrity:** All foreign keys use `ON DELETE RESTRICT` to prevent accidental deletion of financial records.
*   **Indexing Strategy:** B-Tree indexes are applied to `LISTINGS(price)` and `USERS(email)`. A Bitmap index is used for `LISTINGS(status)` due to low cardinality.
*   **Partitioning:** The `AUDIT_LOGS` and `API_USAGE` tables are range-partitioned by month to ensure query performance remains stable as the volume grows to the 10x target.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Since cloud providers are forbidden, Hearthstone Software maintains three distinct physical environment clusters within the EU data center.

#### 6.1.1 Development (Dev)
*   **Purpose:** Initial feature integration and unit testing.
*   **Infrastructure:** 2x Small Kubernetes nodes.
*   **Database:** Single Oracle instance (Standard Edition).
*   **Deployment:** Automatic trigger on every merge to `develop` branch.

#### 6.1.2 Staging (Staging)
*   **Purpose:** UAT (User Acceptance Testing) and QA. Mirrors Production exactly.
*   **Infrastructure:** 4x Medium Kubernetes nodes.
*   **Database:** Oracle RAC (Real Application Clusters) mirroring Production.
*   **Deployment:** Manual trigger from `develop` to `release` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live user traffic.
*   **Infrastructure:** 12x High-performance Kubernetes nodes with NVMe storage.
*   **Database:** Oracle 21c Enterprise with Data Guard for failover.
*   **Deployment:** Rolling deployment via GitLab CI. New pods are spun up and health-checked before old pods are drained.

### 6.2 CI/CD Pipeline
The GitLab CI pipeline consists of four stages:
1.  **Build:** Compiles Java code using Maven 3.9.
2.  **Test:** Executes JUnit 5 tests and SonarQube analysis.
3.  **Package:** Wraps the application into a Docker image and pushes it to the internal registry.
4.  **Deploy:** Applies K8s manifests using `kubectl` rolling updates.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** JUnit 5 and Mockito.
*   **Requirement:** Minimum 80% line coverage for all new business logic.
*   **Focus:** Testing individual service methods and utility classes. Mocks are used to isolate the database layer.

### 7.2 Integration Testing
*   **Framework:** Spring Boot Test with Testcontainers.
*   **Requirement:** All API endpoints must have an associated integration test.
*   **Focus:** Verifying the interaction between the Spring Boot services and the Oracle DB. Tests include verifying that raw SQL queries (the 30% technical debt) produce the same results as the ORM.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Selenium and Playwright.
*   **Requirement:** Critical paths (Login $\rightarrow$ Search $\rightarrow$ Purchase) must be tested weekly.
*   **Focus:** User journey validation from the browser through the load balancer to the database.

### 7.4 Performance Testing
*   **Tool:** JMeter.
*   **Requirement:** Validate that the system can handle 10x current capacity (simulated load of 100,000 concurrent requests).
*   **Focus:** Identifying bottlenecks in the raw SQL queries and the feature flag system.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is 2 months ahead in market entry. | High | High | Develop a "Fallback Architecture" that allows for a stripped-down MVP launch to capture early market share while the full system is polished. |
| **R-02** | 10x Performance requirement with no new budget. | Medium | Critical | This is a board-level blocker. Raise as a formal risk in the next board meeting to secure additional infrastructure funds or reduce scope. |
| **R-03** | Dependency on external partner API timeline. | High | Medium | Implement an "Adapter Pattern" in the integration layer. Create "Mock API" servers that simulate the external company's expected responses. |
| **R-04** | Data residency breach (GDPR/CCPA). | Low | Critical | Strict on-premise isolation. Quarterly audits by the internal security team. |
| **R-05** | Technical debt: Raw SQL migrations. | High | Medium | Mandatory peer review for any SQL change. Implement a "Migration Sandbox" to test raw SQL against production-sized datasets. |

### 8.1 Probability/Impact Matrix
*   **Critical:** Immediate project failure if not addressed.
*   **High:** Significant delay or budget overrun.
*   **Medium:** Manageable with effort.
*   **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phased Roadmap

**Phase 1: Foundation (Jan 2026 - Aug 2026)**
*   Focus on core database schema and the Modular Monolith setup.
*   Implementation of the integration layer for the external API.
*   **Milestone 1: Architecture Review Complete (Target: 2026-08-15).**

**Phase 2: Feature Build-out (Aug 2026 - Oct 2026)**
*   Development of API rate limiting and the marketplace engine.
*   Integration of 2FA and User Management.
*   **Milestone 2: MVP Feature-Complete (Target: 2026-10-15).**

**Phase 3: Hardening and Launch (Oct 2026 - Dec 2026)**
*   Rigorous performance testing (the 10x stress test).
*   GDPR/CCPA compliance verification.
*   **Milestone 3: Security Audit Passed (Target: 2026-12-15).**

### 9.2 Gantt Chart Dependencies
*   **Dependency A:** The external API spec must be finalized before the Integration Layer can move from "Mock" to "Live."
*   **Dependency B:** The Security Audit cannot begin until the 2FA system is fully integrated and the Audit Log (currently blocked) is resolved.

---

## 10. MEETING NOTES (Running Log)

*Note: These notes are extracted from the 200-page shared document. Due to the document's unsearchable nature, the team has manually indexed these specific entries.*

### Meeting 1: Architecture Alignment
**Date:** 2025-11-12  
**Attendees:** Nadia Jensen, Nyla Oduya, Haruki Liu, Arjun Fischer  
**Discussion:**
*   Nyla expressed concerns regarding the transition from monolith to microservices. She argued that splitting the `User` and `Order` services too early would create distributed transaction nightmares (Saga pattern overhead).
*   Nadia decided that the "Modular Monolith" approach is the priority for the first 6 months.
*   Arjun asked about using MongoDB for the API logs. Nadia denied this, citing the "Oracle Only" mandate for the data center.
*   **Decision:** Stick to Oracle 21c for all data; no NoSQL allowed.

### Meeting 2: The Performance Crisis
**Date:** 2025-12-05  
**Attendees:** Nadia Jensen, Nyla Oduya, Haruki Liu  
**Discussion:**
*   The team reviewed the latest JMeter results. The system crashes at 3x capacity, let alone 10x.
*   Nyla pointed out that 30% of the codebase uses raw SQL because the Hibernate ORM was too slow for the listing queries.
*   Haruki noted that the A/B testing framework is adding significant latency to the request-response cycle.
*   **Decision:** A/B Testing framework is moved to "Blocked" status until the core performance issues are resolved. Nadia will bring the budget issue to the board.

### Meeting 3: Resource Gap & Blockers
**Date:** 2026-01-15  
**Attendees:** Nadia Jensen, Nyla Oduya, Arjun Fischer  
**Discussion:**
*   It was confirmed that the lead security engineer is on medical leave for 6 weeks.
*   Nadia noted that this blocks the "Tamper-Evident Audit Log" and the "Security Audit" preparation.
*   Arjun is being tasked with documenting the existing raw SQL queries to prepare for the migration to a more optimized schema.
*   **Decision:** Shift focus to API rate limiting and usage analytics to maintain momentum while the security lead is away.

---

## 11. BUDGET BREAKDOWN

**Total Project Budget:** $3,000,000 USD

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | Salaries for 6 team members + dedicated QA over 24 months. |
| **Infrastructure** | $600,000 | Bare-metal server procurement, Oracle Enterprise licenses, EU Data Center leasing. |
| **Tools & Software** | $200,000 | GitLab Ultimate licenses, SonarQube, JMeter Pro, Security Scanning tools. |
| **Contingency** | $400,000 | Reserved for "Risk 2" (Infrastructure expansion) and unexpected delays. |

**Financial Note:** The personnel budget includes a premium for the Senior Backend Engineer (Nyla) due to the complexity of the Oracle/Java integration.

---

## 12. APPENDICES

### Appendix A: Raw SQL Optimization Guide
Because 30% of the project bypasses the ORM, the following rules apply to all raw SQL:
1.  **Bind Variables:** Never use string concatenation for queries to prevent SQL injection.
2.  **Execution Plans:** All raw SQL must be accompanied by an `EXPLAIN PLAN` output in the JIRA ticket.
3.  **Indexing:** No raw query may perform a full table scan on tables exceeding 100,000 rows.

### Appendix B: GDPR Data Erasure Protocol
To comply with the "Right to be Forgotten," the following procedure is implemented:
1.  **Hard Delete:** User PII in the `USERS` table is deleted.
2.  **Anonymization:** Related records in `ORDERS` and `TRANSACTIONS` are not deleted (for financial audit purposes) but are linked to a "Ghost User" ID.
3.  **Log Scrubbing:** A nightly job scans the `API_USAGE` logs and removes any email addresses found in the request parameters.