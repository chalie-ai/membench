# Project Specification Document: Wayfinder
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Approved / Active  
**Project Lead:** Niko Stein (VP of Product)  
**Company:** Ridgeline Platforms  
**Classification:** Confidential / Proprietary

---

## 1. Executive Summary

**Business Justification**
Wayfinder is the strategic flagship initiative for Ridgeline Platforms, designed to replace a critical, 15-year-old legacy system currently serving as the operational backbone for the company’s food and beverage logistics and management. The legacy system, hereafter referred to as "The Monolith," has reached a state of technical insolvency. It suffers from extreme fragility, lacks a modern API layer, and relies on hardware that is no longer supported by the original manufacturer. Because the entire company depends on this system for daily operations—including order fulfillment, inventory management, and client billing—the risk of a catastrophic failure is high. 

The primary objective of Project Wayfinder is to transition these operations to a modern, scalable SaaS platform hosted within the Ridgeline on-premise data center. Due to the nature of the business and the criticality of the services, there is a **zero downtime tolerance** policy. Any outage during the migration or subsequent operation would result in immediate revenue loss and potential contractual penalties with government-level food and beverage contracts.

**ROI Projection**
The budget for Wayfinder is allocated at $5M+, representing a significant board-level investment. The Return on Investment (ROI) is calculated based on three primary drivers:
1. **Operational Efficiency:** By replacing the legacy manual entry and batch-processing systems with a real-time Java/Spring Boot architecture, Ridgeline expects a 25% reduction in operational overhead costs within the first 12 months.
2. **Risk Mitigation:** The elimination of the legacy system removes the "single point of failure" risk associated with end-of-life hardware and software.
3. **Revenue Expansion:** By achieving FedRAMP authorization, Wayfinder allows Ridgeline Platforms to bid on high-value government contracts that were previously inaccessible due to security non-compliance.

The projected ROI is an estimated $12M in recovered operational costs and new contract revenue over a three-year horizon, yielding a 240% return on the initial $5M investment.

---

## 2. Technical Architecture

Wayfinder utilizes a traditional three-tier architecture to ensure stability, maintainability, and strict separation of concerns. Due to strict regulatory and security constraints, **no cloud services (AWS, Azure, GCP) are permitted**. All infrastructure must reside within the Ridgeline on-premise data center.

### 2.1 The Three-Tier Model
1. **Presentation Tier:** A modern React-based frontend managed by Cassius Park. This layer communicates with the business logic tier via RESTful APIs. It is designed for responsiveness and accessibility, adhering to WCAG 2.1 standards.
2. **Business Logic Tier:** A Java/Spring Boot application server. This layer handles all orchestration, validation, and complex business rules. It leverages Spring Security for access control and Hibernate for ORM.
3. **Data Tier:** A centralized Oracle Database (19c). This tier is responsible for persistent storage, transaction management, and data integrity.

### 2.2 ASCII Architecture Diagram Description
The architectural flow is represented as follows:

```text
[ USER BROWSER ] <--- HTTPS/TLS 1.3 ---> [ LOAD BALANCER (F5 Big-IP) ]
                                                 |
                                                 v
                                    [ WEB SERVER (Nginx / Static Assets) ]
                                                 |
                                                 v
[ SSO PROVIDER ] <--- SAML/OIDC ---> [ APP SERVER (Spring Boot Cluster) ]
                                                 |
                                                 | (JDBC / Oracle Net)
                                                 v
                                    [ DATA TIER (Oracle DB 19c Cluster) ]
                                                 |
                                                 v
                                    [ BACKUP TIER (SAN / Tape Backup) ]
```

### 2.3 Technical Constraints
- **Runtime:** OpenJDK 17.
- **Framework:** Spring Boot 3.1.x.
- **Database:** Oracle DB 19c with RAC (Real Application Clusters) for high availability.
- **Deployment:** Continuous Deployment (CD). Every merged Pull Request (PR) is automatically deployed to production via the internal Jenkins pipeline.
- **Security:** Must meet FedRAMP High baseline requirements. This includes FIPS 140-2 validated cryptography and strict auditing.

---

## 3. Detailed Feature Specifications

### 3.1 SSO Integration with SAML and OIDC (Priority: Critical)
**Status:** In Progress | **Launch Blocker:** Yes

**Description:**
Wayfinder must act as a Service Provider (SP) capable of integrating with multiple external Identity Providers (IdPs). Given the diverse client base in the food and beverage industry—ranging from small private firms to large government agencies—the platform must support both SAML 2.0 (Security Assertion Markup Language) and OIDC (OpenID Connect).

**Detailed Requirements:**
- **SAML 2.0 Flow:** The system must support SP-initiated and IdP-initiated SSO. It must handle XML metadata exchange and support encrypted assertions to prevent interception.
- **OIDC Flow:** Support for the Authorization Code Flow with PKCE (Proof Key for Code Exchange) to ensure secure token exchange for the frontend application.
- **User Provisioning:** Implementation of Just-In-Time (JIT) provisioning. When a user logs in via SSO for the first time, the system must automatically create a local user profile based on the attributes passed in the SAML/OIDC claim.
- **Session Management:** Integration with a centralized session store (Redis) to allow for seamless session failover across the Spring Boot cluster.
- **Administrative Console:** A secure interface for the Project Lead (Niko Stein) and Security Engineer (Amara Santos) to upload IdP metadata, configure entity IDs, and manage trust certificates.

**Success Criteria:** A user from a government agency can log into Wayfinder using their agency credentials without creating a separate password, with the system correctly mapping their role to "Admin" or "User" based on the SAML attribute `memberOf`.

### 3.2 Notification System (Priority: Low)
**Status:** In Review | **Launch Blocker:** No

**Description:**
The notification system is a cross-cutting concern designed to alert users of critical events (e.g., shipment delays, inventory shortages, or security alerts). It must support four distinct channels: Email, SMS, In-App, and Push.

**Detailed Requirements:**
- **Email Engine:** Integration with the corporate SMTP relay. Support for HTML templates using Thymeleaf to ensure branding consistency.
- **SMS Gateway:** Integration via a secure on-premise SMS gateway. Messages must be capped at 160 characters to avoid multi-part splitting.
- **In-App Notifications:** A WebSocket-based system (using Spring Message Broker) that pushes real-time alerts to the React frontend without requiring a page refresh.
- **Push Notifications:** Integration with browser-level Push APIs for desktop alerts.
- **Preference Center:** A user-facing settings page allowing individuals to toggle specific notification types (e.g., "Receive SMS for Critical Alerts" = True; "Receive Email for Weekly Reports" = False).
- **Queueing Logic:** Use of an internal message queue (RabbitMQ) to ensure that a failure in the SMS gateway does not block the execution of the business logic.

**Success Criteria:** When a "Critical Stock" event is triggered in the database, the system successfully sends an email and an in-app alert to the Inventory Manager within 30 seconds.

### 3.3 Multi-tenant Data Isolation (Priority: Low)
**Status:** In Progress | **Launch Blocker:** No

**Description:**
While Wayfinder uses a shared infrastructure model, it must maintain strict data isolation between different clients (tenants) to prevent "noisy neighbor" issues and data leakage.

**Detailed Requirements:**
- **Shared Schema Approach:** Implementation of a `tenant_id` column on every single table within the Oracle DB.
- **Row-Level Security (RLS):** Utilization of Oracle Virtual Private Database (VPD) to automatically append a `WHERE tenant_id = :current_tenant` clause to all queries, ensuring that developers cannot accidentally leak data across tenants.
- **Tenant Resolver:** A Spring Interceptor that extracts the tenant ID from the request header or the SSO token and injects it into the `TenantContext` (ThreadLocal).
- **Infrastructure Sharing:** All tenants share the same JVM and Connection Pool to optimize resource utilization on the on-premise hardware.
- **Tenant Management API:** Endpoints to allow the creation of new tenants, assigning them to specific regional data clusters, and decommissioning tenants upon contract termination.

**Success Criteria:** A query executed by User A (Tenant 1) must never return a result belonging to User B (Tenant 2), even if the developer forgets to add a filter to the SQL query.

### 3.4 API Rate Limiting and Usage Analytics (Priority: Critical)
**Status:** In Design | **Launch Blocker:** Yes

**Description:**
To ensure the stability of the on-premise environment and prevent Denial of Service (DoS) attacks (whether intentional or due to buggy client scripts), Wayfinder must implement a sophisticated rate-limiting mechanism.

**Detailed Requirements:**
- **Bucket Algorithm:** Implementation of the "Token Bucket" algorithm. Each tenant is assigned a bucket of tokens; each API call consumes one token. Tokens refill at a defined rate.
- **Tiered Limits:** Support for different tiers (e.g., Basic: 100 requests/min, Premium: 1000 requests/min).
- **Header Reporting:** Every response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Engine:** A background process that aggregates API usage data into an `api_usage_logs` table. This data will be used by the business team for billing and capacity planning.
- **Circuit Breaker:** Implementation of Resilience4j to "trip" the circuit if a downstream dependency (like the Oracle DB) becomes unresponsive, preventing the system from cascading failure.

**Success Criteria:** When a client exceeds their limit of 100 requests/minute, the system must return a `429 Too Many Requests` response and log the event for audit.

### 3.5 Audit Trail Logging (Priority: High)
**Status:** Not Started | **Launch Blocker:** No

**Description:**
Given the FedRAMP requirements and the nature of the food and beverage industry (FDA compliance), every change to sensitive data must be recorded in a tamper-evident audit trail.

**Detailed Requirements:**
- **Event Capture:** Implementation of a Spring AOP (Aspect-Oriented Programming) interceptor that logs the User ID, Timestamp, Action (Create/Update/Delete), Old Value, New Value, and IP Address.
- **Tamper-Evident Storage:** Logs must be written to a "Write Once, Read Many" (WORM) storage volume.
- **Cryptographic Hashing:** Each log entry must contain a SHA-256 hash of the current entry concatenated with the hash of the previous entry (creating a blockchain-like chain). This ensures that if a log entry is deleted or modified, the chain is broken.
- **Searchable Archive:** A dedicated admin UI to search audit logs by date range, user, or entity ID.
- **Retention Policy:** Logs must be archived for 7 years to comply with government regulations, then automatically purged.

**Success Criteria:** An auditor can verify that the "Price Change" log for Order #12345 has not been modified since its original creation timestamp.

---

## 4. API Endpoint Documentation

All endpoints are versioned under `/api/v1/`. Authentication via Bearer Token is required for all calls.

### 4.1 Authentication & Identity
**`POST /api/v1/auth/login`**
- **Description:** Initiates the SSO handshake.
- **Request:** `{"provider": "okta", "clientId": "RIDGELINE_01"}`
- **Response:** `200 OK` $\rightarrow$ `{"token": "eyJ...", "expires_in": 3600}`

**`GET /api/v1/auth/me`**
- **Description:** Returns the currently authenticated user's profile.
- **Response:** `200 OK` $\rightarrow$ `{"userId": "USR-99", "name": "Jane Doe", "role": "Admin"}`

### 4.2 Order Management
**`GET /api/v1/orders`**
- **Description:** Retrieves a paginated list of orders for the tenant.
- **Params:** `page=0&size=20&status=PENDING`
- **Response:** `200 OK` $\rightarrow$ `{"content": [...], "totalElements": 450}`

**`POST /api/v1/orders`**
- **Description:** Creates a new food/beverage order.
- **Request:** `{"customerId": "C-101", "items": [{"sku": "BEV-01", "qty": 50}], "priority": "HIGH"}`
- **Response:** `201 Created` $\rightarrow$ `{"orderId": "ORD-7782", "status": "CREATED"}`

### 4.3 Inventory Control
**`GET /api/v1/inventory/{sku}`**
- **Description:** Checks stock levels for a specific SKU.
- **Response:** `200 OK` $\rightarrow$ `{"sku": "BEV-01", "quantity": 1200, "warehouse": "North-01"}`

**`PATCH /api/v1/inventory/{sku}/adjust`**
- **Description:** Adjusts stock levels (used for wastage or manual overrides).
- **Request:** `{"adjustment": -10, "reason": "Spillage"}`
- **Response:** `200 OK` $\rightarrow$ `{"newQuantity": 1190}`

### 4.4 System & Administration
**`GET /api/v1/admin/usage-stats`**
- **Description:** Returns API consumption metrics for the current tenant.
- **Response:** `200 OK` $\rightarrow$ `{"totalRequests": 50000, "limit": 100000, "percentUsed": 50}`

**`GET /api/v1/admin/audit-logs`**
- **Description:** Retrieves the tamper-evident audit trail.
- **Params:** `entityId=ORD-7782`
- **Response:** `200 OK` $\rightarrow$ `{"logs": [{"timestamp": "...", "action": "UPDATE", "user": "Niko Stein"}]}`

---

## 5. Database Schema

The system utilizes an Oracle DB 19c schema. All tables include a `tenant_id` for isolation.

### 5.1 Schema Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | None | `name`, `domain`, `status` | Top-level organization data |
| `users` | `user_id` | `tenant_id` | `username`, `email`, `role_id` | Platform user accounts |
| `roles` | `role_id` | None | `role_name`, `permissions` | RBAC role definitions |
| `orders` | `order_id` | `tenant_id`, `user_id` | `order_date`, `total_amount`, `status` | Header for F&B orders |
| `order_items` | `item_id` | `order_id`, `sku_id` | `quantity`, `unit_price` | Line items for each order |
| `products` | `sku_id` | `tenant_id` | `sku_name`, `category`, `unit_measure` | Product catalog |
| `inventory` | `inv_id` | `sku_id`, `warehouse_id` | `quantity_on_hand`, `reorder_point` | Real-time stock levels |
| `warehouses` | `warehouse_id` | `tenant_id` | `location_code`, `address` | Physical storage locations |
| `audit_logs` | `log_id` | `tenant_id`, `user_id` | `action`, `old_val`, `new_val`, `hash` | Tamper-evident event log |
| `api_usage` | `usage_id` | `tenant_id` | `endpoint`, `timestamp`, `response_code` | Rate limiting analytics |

### 5.2 Relationships
- `tenants` $\rightarrow$ `users` (1:N)
- `users` $\rightarrow$ `orders` (1:N)
- `orders` $\rightarrow$ `order_items` (1:N)
- `products` $\rightarrow$ `order_items` (1:N)
- `products` $\rightarrow$ `inventory` (1:N)
- `tenants` $\rightarrow$ `audit_logs` (1:N)

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
To ensure zero downtime, Wayfinder utilizes three strictly isolated environments within the on-premise data center.

**1. Development (DEV)**
- **Purpose:** Feature development and unit testing.
- **Configuration:** Single-node Spring Boot instance, shared Oracle DB instance (pluggable database).
- **Deployment:** Triggered by every commit to the `develop` branch.

**2. Staging (STG)**
- **Purpose:** User Acceptance Testing (UAT) and FedRAMP compliance scanning.
- **Configuration:** Mirror of production hardware. Full Oracle RAC cluster.
- **Deployment:** Triggered by merge from `develop` $\rightarrow$ `release`.

**3. Production (PROD)**
- **Purpose:** Live business operations.
- **Configuration:** High-availability cluster across two physical server racks.
- **Deployment:** Continuous Deployment via Jenkins. Merges to `main` are automatically deployed.

### 6.2 CI/CD Pipeline (The "Bottleneck")
The current pipeline is a critical pain point.
- **Process:** Checkout $\rightarrow$ Maven Compile $\rightarrow$ JUnit Tests $\rightarrow$ SonarQube Analysis $\rightarrow$ Oracle Migration (Flyway) $\rightarrow$ Deployment.
- **Current Performance:** 45 minutes.
- **Issue:** Lack of parallelization. All tests run sequentially.
- **Optimization Plan:** Implementing parallel test execution and caching dependencies in a local Artifactory mirror to reduce time to $<15$ minutes.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Tooling:** JUnit 5, Mockito.
- **Requirement:** Minimum 80% line coverage.
- **Focus:** Business logic in the Service layer and utility classes.

### 7.2 Integration Testing
- **Tooling:** Spring Boot Test, Testcontainers (using Oracle XE image).
- **Focus:** Ensuring that the JPA layer correctly maps to the Oracle schema and that the `tenant_id` filter is applied to all queries.
- **Frequency:** Run on every PR merge.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Cypress.
- **Focus:** Critical user journeys (e.g., "Login via SSO $\rightarrow$ Create Order $\rightarrow$ Check Inventory $\rightarrow$ Log Out").
- **Environment:** Performed exclusively in the Staging environment.

### 7.4 Security Testing
- **Penetration Testing:** Quarterly audits conducted by Amara Santos.
- **FedRAMP Scanning:** Weekly vulnerability scans using Nessus to ensure the on-premise environment remains compliant.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Primary vendor announces EOL for legacy support tool | High | Critical | Negotiate timeline extension with vendor and stakeholders. |
| R-02 | Key Architect leaving the company in 3 months | Medium | High | De-scope non-critical features (e.g., Notification System) if no replacement is found. |
| R-03 | Budget approval for critical tool pending | High | Medium | Escalate to Niko Stein for board-level intervention. |
| R-04 | CI Pipeline failure/slowness delays deployment | High | Low | Parallelize JUnit tests and optimize Maven build. |
| R-05 | Data leakage between tenants | Low | Critical | Implement Oracle VPD (Virtual Private Database) for hard isolation. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt or total data loss.
- **High:** Significant delay to Milestone 2.
- **Medium:** Impact on "nice-to-have" features.
- **Low:** Minor inconvenience.

---

## 9. Timeline

Wayfinder follows a strict milestone-based delivery schedule. All dates are fixed due to the legacy system's EOL constraints.

### 9.1 Phases
- **Phase 1: Foundation (Oct 2023 - June 2025)**
    - Core architecture setup.
    - SSO Integration development.
    - Database schema migration from legacy.
- **Phase 2: Beta & Hardening (June 2025 - Aug 2025)**
    - Internal alpha testing.
    - FedRAMP security hardening.
    - Final API rate limiting tuning.
- **Phase 3: Cutover & Stability (Aug 2025 - Oct 2025)**
    - Parallel run of legacy and new system.
    - Final cutover (Zero-Downtime).
    - Stability monitoring.

### 9.2 Milestone Dates
- **Milestone 1: Internal Alpha Release** $\rightarrow$ **2025-06-15**
- **Milestone 2: Production Launch** $\rightarrow$ **2025-08-15**
- **Milestone 3: Post-launch Stability Confirmed** $\rightarrow$ **2025-10-15**

---

## 10. Meeting Notes

**Meeting Date: 2023-11-02**
- **Attendees:** Niko, Cassius, Amara
- **Notes:**
    - SSO is lagging.
    - Amara says SAML metadata is messy.
    - Niko wants a weekly JIRA report.
    - Discussion on OIDC vs SAML.

**Meeting Date: 2023-11-16**
- **Attendees:** Niko, Gael, Amara
- **Notes:**
    - Budget for tool X still not approved.
    - Gael mentions the 45-min build time is a joke.
    - Oracle DB RAC setup is delayed by hardware shipping.
    - Amara warns about FedRAMP audit in Q1.

**Meeting Date: 2023-12-01**
- **Attendees:** Niko, Cassius, Gael
- **Notes:**
    - Architect leaving soon.
    - Need to document the "secret sauce" of the legacy DB.
    - Cassius needs final Figma for the admin console.
    - Decision: Move Notification System to "Low Priority" if dates slip.

---

## 11. Budget Breakdown

**Total Budget: $5,250,000**

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | 20+ Full-time staff, contractor fees (Gael Costa), VP oversight. |
| **Infrastructure** | $1,100,000 | On-premise Oracle licenses, F5 Load Balancer, Physical Server Racks. |
| **Tools & Licensing** | $450,000 | SonarQube, Jenkins Enterprise, Nessus, Artifactory. |
| **Contingency** | $500,000 | Emergency staffing, hardware replacements, vendor extensions. |

---

## 12. Appendices

### Appendix A: FedRAMP Compliance Checklist
To achieve FedRAMP authorization for government clients, Wayfinder must implement the following:
- **AC-2 (Account Management):** Automated account disabling after 90 days of inactivity.
- **AU-2 (Event Logging):** Integration of the Audit Trail (Feature 3.5) into the corporate SIEM.
- **IA-2 (Identification and Authentication):** Mandatory MFA (Multi-Factor Authentication) for all users.
- **SC-8 (Transmission Confidentiality):** TLS 1.3 mandatory for all internal and external traffic.

### Appendix B: Legacy Data Migration Plan
The migration from the 15-year-old system will follow a **Parallel Run Strategy**:
1. **Shadow Write:** For 30 days, all new data will be written to both the Legacy DB and the Wayfinder Oracle DB.
2. **Verification:** A daily reconciliation script will compare records between the two systems.
3. **Read-Switch:** The frontend will switch to reading from Wayfinder while still writing to the Legacy system.
4. **Final Cutover:** The Legacy system will be put into read-only mode and eventually decommissioned after Milestone 3.