Due to the extreme length requirement of this document (6,000–8,000 words), this specification is presented as a comprehensive, professional engineering manual. It is designed to serve as the "Single Source of Truth" (SSOT) for the Aqueduct development team at Ridgeline Platforms.

***

# PROJECT SPECIFICATION: PROJECT AQUEDUCT
**Document Version:** 1.0.4  
**Status:** Draft for Review  
**Last Updated:** October 24, 2023  
**Classification:** Confidential – Internal Use Only (PCI DSS Level 1)  
**Owner:** Greta Santos (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Aqueduct represents a strategic pivot for Ridgeline Platforms. As a leader in the renewable energy sector, Ridgeline Platforms manages critical infrastructure that is increasingly targeted by sophisticated cyber-adversaries. The current monitoring system is a legacy monolith—a "black box" that is difficult to scale, impossible to update without total downtime, and lacks the granularity required for modern threat detection.

The objective of Aqueduct is a comprehensive platform modernization. By transitioning from a monolithic architecture to a microservices-based ecosystem over an 18-month period, Ridgeline Platforms will achieve operational agility and systemic resilience. This is not merely a technical upgrade but a business imperative; the ability to monitor cybersecurity threats in real-time across distributed renewable energy grids (wind, solar, hydro) directly impacts the stability of the power grid and the safety of physical assets.

### 1.2 Scope and Strategic Alignment
Aqueduct will provide a centralized cybersecurity monitoring dashboard. The platform must handle high-throughput telemetry data while adhering to the strictest security standards. Because Ridgeline Platforms processes credit card data directly for subscription-based energy management services, the entire environment must be PCI DSS Level 1 compliant. This necessitates a rigorous "no-cloud" policy; all data must reside in an on-premise data center to maintain absolute physical and logical control over the Cardholder Data Environment (CDE).

### 1.3 ROI Projection and Success Metrics
The total investment for Aqueduct is $3,000,000. The financial justification is predicated on two primary drivers: the reduction of operational risk and the opening of new revenue streams through "Security-as-a-Service" offerings for partner utilities.

**Success Metric 1: Revenue Growth**
The project targets $500,000 in new attributed revenue within the first 12 months post-launch. This will be achieved by offering premium monitoring tiers to external partners, utilizing the new automated billing and subscription management module.

**Success Metric 2: Risk Mitigation**
The primary non-financial KPI is the achievement of zero critical security incidents in the first year of operation. By moving to a microservices architecture, the "blast radius" of any single vulnerability is significantly reduced, and the implementation of role-based access control (RBAC) ensures that the principle of least privilege is enforced across all administrative actions.

The ROI is calculated not only in direct revenue but in the avoidance of catastrophic fines associated with PCI DSS non-compliance or critical infrastructure failure, which could potentially cost the company tens of millions in liabilities.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Aqueduct is moving from a "Big Ball of Mud" monolith to a decentralized architecture leveraging serverless functions. Despite being on-premise, the architecture mimics cloud-native patterns using a localized API Gateway for orchestration. This ensures that individual services (e.g., Billing, Auth, Monitoring) can be scaled or patched independently.

### 2.2 System Component Diagram (ASCII)
```text
[ USER BROWSER / DASHBOARD ]
          |
          v
[ ON-PREMISE NETWORK FIREWALL (PCI DSS ZONE) ]
          |
          v
[ API GATEWAY (Orchestration Layer) ] <---- [ LAUNCHDARKLY (Feature Flags) ]
          |
          +---------------------------------------+
          |                   |                   |
          v                   v                   v
[ AUTH SERVICE ]      [ MONITORING SVC ]    [ BILLING SERVICE ]
(Spring Boot)         (Spring Boot)         (Spring Boot)
          |                   |                   |
          +-------------------+-------------------+
                              |
                              v
                    [ ORACLE DATABASE 19c ]
                    (Encrypted Tablespaces)
                    (PCI CDE Segmented)
```

### 2.3 Technical Stack
- **Backend:** Java 17 with Spring Boot 3.x.
- **Database:** Oracle DB 19c (Standard Edition 2) with Advanced Security Option (Transparent Data Encryption).
- **Orchestration:** On-premise API Gateway (Spring Cloud Gateway).
- **Execution Model:** Serverless functions implemented via Spring Cloud Function, triggered by the Gateway.
- **Deployment Strategy:** Canary releases via LaunchDarkly. Feature flags are used to toggle functionality without redeploying code.
- **Security Standard:** PCI DSS Level 1. This requires physical isolation of the servers, multi-factor authentication (MFA) for all admin access, and rigorous logging of all access to the Oracle DB.

### 2.4 Data Flow and Communication
Communication between the API Gateway and the serverless functions occurs via REST over HTTPS (TLS 1.3). Internal service-to-service communication is handled through a private virtual network. Because no cloud is allowed, all "serverless" abstractions are managed via an internal Kubernetes cluster (K8s) running on bare-metal servers in the Ridgeline data center.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** In Design

**Description:**
The Advanced Search feature allows security analysts to query millions of logs across the renewable energy grid. Unlike a simple keyword search, this feature implements faceted filtering (similar to an e-commerce sidebar), allowing users to drill down by "Severity," "Asset Type," "Geographic Region," and "Time Window."

**Technical Specifications:**
- **Indexing:** Since the project uses Oracle DB, we will implement *Oracle Text* for full-text indexing. This prevents the performance degradation associated with `LIKE %keyword%` queries.
- **Faceted Logic:** The system will execute a primary search query and simultaneously run "count" queries for each facet category. These counts will update dynamically as filters are applied.
- **User Interface:** A search bar with auto-suggest capabilities, coupled with a collapsible left-hand navigation pane for facets.
- **Performance Requirement:** Search results must be returned in $<2$ seconds for datasets up to 10 million records.

**Use Case:**
An analyst notices a spike in "unauthorized access" attempts. They use the search bar for "Unauthorized," then filter by "Region: Southwest" and "Asset: Wind Turbine," quickly isolating the attack to a specific wind farm in Texas.

### 3.2 Feature 2: User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Review

**Description:**
Given the PCI DSS Level 1 requirements, the authentication system is the most critical security component. Aqueduct must ensure that only authorized personnel can access sensitive credit card data or change system configurations.

**Technical Specifications:**
- **Authentication:** Implementation of OpenID Connect (OIDC) utilizing an on-premise identity provider. Multi-Factor Authentication (MFA) is mandatory for all users.
- **RBAC Model:** A hierarchical role system:
    - `SuperAdmin`: Full system access, including billing and user management.
    - `SecurityAnalyst`: Read/Write access to monitoring data, no access to billing.
    - `Auditor`: Read-only access to logs and reports.
    - `BillingManager`: Access to subscription and payment modules only.
- **Session Management:** JWT (JSON Web Tokens) with a maximum lifespan of 15 minutes, refreshed via a secure refresh token stored in an HTTP-only cookie.

**PCI DSS Compliance:**
All authentication attempts (success and failure) must be logged to a read-only audit table in the Oracle DB, including the source IP and timestamp.

### 3.3 Feature 3: Offline-First Mode with Background Sync
**Priority:** Low | **Status:** Complete

**Description:**
Field engineers often visit remote renewable energy sites (e.g., remote solar arrays) where connectivity is intermittent. This feature allows them to continue using the dashboard to log incidents and view cached data while offline.

**Technical Specifications:**
- **Local Storage:** Use of IndexedDB in the browser to cache the last 50MB of relevant monitoring data.
- **Sync Engine:** A Service Worker intercepts network requests. If the network is down, requests are queued in an "Outbox" table within IndexedDB.
- **Conflict Resolution:** "Last-Write-Wins" (LWW) strategy is employed for synchronization. When the device reconnects, the Service Worker pushes the Outbox queue to the API Gateway.
- **Background Sync:** Utilizing the `Background Sync API` to ensure data is uploaded even if the user closes the browser tab.

**Status Note:** This feature was completed early in the development cycle as a proof-of-concept for the field engineering team.

### 3.4 Feature 4: A/B Testing Framework (via Feature Flags)
**Priority:** Critical | **Status:** In Design (Launch Blocker)

**Description:**
To optimize the user experience for security analysts, the team requires a way to test two different dashboard layouts simultaneously. This framework is "baked into" the existing LaunchDarkly integration.

**Technical Specifications:**
- **Targeting Logic:** Users are randomly assigned to "Group A" (Control) or "Group B" (Variant) based on their `userID` hash.
- **Integration:** The Spring Boot backend will check the LaunchDarkly flag status during the request cycle. The API response will include a `ui_version` header to tell the frontend which component to render.
- **Metric Tracking:** The system must track "Time to Resolution" (TTR) for both groups. The A/B test is successful if Group B shows a statistically significant reduction in TTR.
- **Rollout Strategy:** 10% of users $\rightarrow$ 25% $\rightarrow$ 50% $\rightarrow$ 100%.

**Why this is a Launch Blocker:** Without this, we cannot validate the effectiveness of the new monitoring UI, which is a core requirement for the $500K revenue goal.

### 3.5 Feature 5: Automated Billing and Subscription Management
**Priority:** Low | **Status:** In Review

**Description:**
To monetize Aqueduct, a billing engine is required to handle monthly subscriptions for external partners. This module processes credit card payments directly.

**Technical Specifications:**
- **Payment Processing:** Integration with an on-premise payment gateway. Credit card numbers must be encrypted at the application level using AES-256 before hitting the database.
- **Subscription Tiers:**
    - *Basic*: 1 site, 1 user, basic logs.
    - *Professional*: 10 sites, 5 users, advanced search.
    - *Enterprise*: Unlimited sites, unlimited users, full A/B testing access.
- **Invoicing:** Automated generation of PDF invoices using JasperReports, delivered via email.
- **Billing Cycle:** Monthly recurring billing with automatic retry logic for failed payments.

**Technical Debt Warning:** As noted in the risk register, this module currently has 0% test coverage and was deployed to the dev environment under extreme pressure.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `Bearer <JWT>` token in the Authorization header.

### 4.1 Auth Endpoints
**Endpoint:** `POST /auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request:** `{ "username": "string", "password": "string", "mfa_code": "string" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_in": 900 }`

**Endpoint:** `POST /auth/refresh`
- **Description:** Refreshes an expired access token.
- **Request:** `{ "refresh_token": "string" }`
- **Response:** `200 OK { "token": "eyJ...", "expires_in": 900 }`

### 4.2 Monitoring Endpoints
**Endpoint:** `GET /monitor/alerts`
- **Description:** Retrieves a list of active security alerts.
- **Request Parameters:** `?severity=critical&limit=50`
- **Response:** `200 OK [ { "id": "AL-101", "msg": "Brute force detected", "timestamp": "2023-10-24T10:00Z" } ]`

**Endpoint:** `GET /monitor/search`
- **Description:** Full-text search for logs.
- **Request Parameters:** `?q=unauthorized&region=southwest`
- **Response:** `200 OK { "results": [...], "facets": { "severity": { "high": 12, "low": 45 } } }`

**Endpoint:** `PATCH /monitor/alerts/{id}`
- **Description:** Updates the status of an alert (e.g., marking it as "Resolved").
- **Request:** `{ "status": "RESOLVED", "notes": "False positive" }`
- **Response:** `200 OK { "id": "AL-101", "status": "RESOLVED" }`

### 4.3 Billing Endpoints
**Endpoint:** `GET /billing/subscription`
- **Description:** Retrieves the current user's subscription plan.
- **Response:** `200 OK { "plan": "Professional", "next_billing_date": "2023-11-01" }`

**Endpoint:** `POST /billing/payment-method`
- **Description:** Updates credit card information (PCI DSS Sensitive).
- **Request:** `{ "card_number": "encrypted_string", "expiry": "MM/YY", "cvv": "encrypted_string" }`
- **Response:** `201 Created { "status": "Success", "method_id": "met_998" }`

**Endpoint:** `GET /billing/invoices`
- **Description:** Fetches history of billing invoices.
- **Response:** `200 OK [ { "invoice_id": "INV-001", "amount": 150.00, "date": "2023-09-01" } ]`

---

## 5. DATABASE SCHEMA

The database is hosted on Oracle 19c. All tables use `VARCHAR2` for strings and `TIMESTAMP WITH TIME ZONE` for dates.

### 5.1 Tables and Relationships

1.  **`USERS`**: Stores primary identity data.
    - `user_id` (PK, UUID)
    - `username` (Unique)
    - `password_hash` (Bcrypt)
    - `mfa_secret` (Encrypted)
    - `created_at` (Timestamp)
2.  **`ROLES`**: Defines system roles.
    - `role_id` (PK)
    - `role_name` (e.g., 'SUPER_ADMIN', 'ANALYST')
3.  **`USER_ROLES`**: Mapping table for RBAC.
    - `user_id` (FK $\rightarrow$ USERS)
    - `role_id` (FK $\rightarrow$ ROLES)
4.  **`ALERTS`**: Cybersecurity events.
    - `alert_id` (PK)
    - `severity` (Low, Med, High, Critical)
    - `source_ip` (String)
    - `description` (CLOB)
    - `status` (Open, In-Progress, Resolved)
    - `created_at` (Timestamp)
5.  **`ASSETS`**: Renewable energy hardware.
    - `asset_id` (PK)
    - `asset_type` (e.g., 'WIND_TURBINE', 'SOLAR_INVERTER')
    - `location_id` (FK $\rightarrow$ LOCATIONS)
    - `ip_address` (String)
6.  **`LOCATIONS`**: Geographic site data.
    - `location_id` (PK)
    - `region` (e.g., 'Southwest', 'Northeast')
    - `city` (String)
    - `state` (String)
7.  **`SUBSCRIPTIONS`**: Billing plans.
    - `sub_id` (PK)
    - `user_id` (FK $\rightarrow$ USERS)
    - `plan_type` (Basic, Pro, Ent)
    - `start_date` (Date)
    - `end_date` (Date)
8.  **`PAYMENT_METHODS`**: PCI Sensitive data.
    - `payment_id` (PK)
    - `user_id` (FK $\rightarrow$ USERS)
    - `encrypted_card_data` (BLOB)
    - `last_four` (String)
    - `expiry_date` (Date)
9.  **`INVOICES`**: Billing history.
    - `invoice_id` (PK)
    - `sub_id` (FK $\rightarrow$ SUBSCRIPTIONS)
    - `amount` (Decimal)
    - `payment_status` (Paid, Pending, Failed)
    - `issued_at` (Timestamp)
10. **`AUDIT_LOGS`**: PCI compliance tracking.
    - `log_id` (PK)
    - `user_id` (FK $\rightarrow$ USERS)
    - `action` (String)
    - `timestamp` (Timestamp)
    - `ip_address` (String)

### 5.2 Key Relationships
- **One-to-Many:** `USERS` $\rightarrow$ `SUBSCRIPTIONS` (A user can have multiple historical subscriptions).
- **Many-to-Many:** `USERS` $\leftrightarrow$ `ROLES` (via `USER_ROLES`).
- **One-to-Many:** `LOCATIONS` $\rightarrow$ `ASSETS` (One site contains many turbines/panels).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Since no cloud is permitted, all environments are physically partitioned within the Ridgeline Platforms on-premise data center.

#### 6.1.1 Development (DEV)
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** 2x Small Bare-Metal Servers.
- **Database:** Shared Oracle instance with "Dev" schema.
- **Deployment:** Automatic trigger from GitLab CI/CD runner.

#### 6.1.2 Staging (STAGING)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Infrastructure:** Mirrors Production hardware specifications.
- **Database:** Dedicated Oracle instance with anonymized production data.
- **Deployment:** Manual trigger after successful Dev merge.

#### 6.1.3 Production (PROD)
- **Purpose:** Live environment.
- **Infrastructure:** High-availability (HA) cluster across two physical racks for redundancy.
- **Database:** Oracle RAC (Real Application Clusters) for zero-downtime failover.
- **Deployment:** Canary release pattern. 5% of traffic is routed to the new version via the API Gateway; if error rates remain $<0.1\%$, the rollout expands.

### 6.2 Feature Flag Management
We use **LaunchDarkly** (On-Premise Relay Proxy). This allows Greta Santos to toggle features (like the A/B testing framework) without a full redeploy. If a critical bug is found in a new feature, it can be "killed" instantly by flipping a switch in the LaunchDarkly dashboard.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** JUnit 5, Mockito.
- **Requirement:** 80% code coverage on all new microservices.
- **Focus:** Business logic within `@Service` classes.
- **Exception:** The Billing Module currently has 0% coverage (Technical Debt).

### 7.2 Integration Testing
- **Tool:** Testcontainers (using an Oracle-XE container).
- **Focus:** Testing the interaction between the API Gateway and serverless functions, and ensuring database queries return correct results.
- **Frequency:** Run on every Merge Request.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Focus:** Critical user journeys (e.g., "Login $\rightarrow$ Search for Alert $\rightarrow$ Resolve Alert").
- **Frequency:** Run nightly against the Staging environment.

### 7.4 PCI DSS Compliance Testing
- **Vulnerability Scanning:** Monthly scans using Nessus.
- **Penetration Testing:** Semi-annual external audit by a PCI-certified QSA (Qualified Security Assessor).
- **Log Verification:** Weekly checks to ensure `AUDIT_LOGS` are being written and are immutable.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements for renewable energy may change. | High | Medium | Accept risk; monitor weekly via regulatory sync calls. |
| R-02 | Competitor is building same product (2 months ahead). | Medium | High | De-scope non-essential features if not resolved by Milestone 1. |
| R-03 | PCI DSS audit failure. | Low | Critical | Strict adherence to Level 1 standards; monthly internal audits. |
| R-04 | Lack of test coverage in Billing Module. | High | High | Allocate a "Debt Sprint" after Milestone 1 to write tests. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt/failure.
- **High:** Significant delay or budget overrun.
- **Medium:** Manageable impact with minor adjustments.
- **Low:** Negligible impact.

**Current Blocker:**
Infrastructure provisioning for the Staging environment has been delayed. Although we are on-premise, the "cloud provider" (internal IT Infrastructure team) is delayed in racking the physical servers.

---

## 9. TIMELINE AND MILESTONES

The project spans 18 months. The following are the critical milestones for the current phase.

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Months 1-6):** Core infrastructure, API Gateway setup, and Auth service.
- **Phase 2: Core Monitoring (Months 7-12):** Implementation of alerting and search.
- **Phase 3: Monetization & Polish (Months 13-18):** Billing, A/B testing, and final security audits.

### 9.2 Milestone Gantt Description
- **Milestone 1: MVP Feature-Complete (Target: 2025-04-15)**
    - *Dependencies:* Auth service, basic monitoring endpoints, and basic UI.
    - *Status:* On track, pending infrastructure provisioning.
- **Milestone 2: Security Audit Passed (Target: 2025-06-15)**
    - *Dependencies:* Full PCI DSS Level 1 implementation, audit logs enabled.
    - *Status:* High risk due to Billing module technical debt.
- **Milestone 3: Architecture Review Complete (Target: 2025-08-15)**
    - *Dependencies:* Transition of all legacy monolith functions to serverless.
    - *Status:* In progress.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02 | **Attendees:** Greta, Kai, Dante, Luciano
**Discussion:**
The team debated the use of a cloud-based database. Greta reminded everyone that PCI DSS Level 1 requirements for Ridgeline Platforms forbid cloud storage for credit card data. Kai raised concerns about managing serverless functions on-premise.
**Decisions:**
- Confirmed use of on-premise Kubernetes (K8s) to simulate serverless behavior.
- Agreed to use Oracle RAC for production high availability.
**Action Items:**
- Kai: Provision K8s cluster in DEV $\rightarrow$ Due 2023-11-10.
- Dante: Create initial wireframes for the dashboard $\rightarrow$ Due 2023-11-15.

### Meeting 2: Billing Module Crisis
**Date:** 2023-12-12 | **Attendees:** Greta, Kai, Luciano
**Discussion:**
Luciano (Intern) pointed out that the billing module was pushed to the dev environment without a single unit test. The team admitted that deadline pressure led to this shortcut.
**Decisions:**
- The billing module is marked as "High Risk" in the risk register.
- No new features will be added to the billing module until a 40% test coverage baseline is met.
**Action Items:**
- Luciano: Write initial test suite for `SubscriptionService.java` $\rightarrow$ Due 2023-12-20.

### Meeting 3: A/B Testing Strategy
**Date:** 2024-01-05 | **Attendees:** Greta, Dante, Kai
**Discussion:**
Dante presented two versions of the alert dashboard. The team discussed how to track which version performs better. Greta insisted that this must be a "launch blocker" because the ROI depends on user efficiency.
**Decisions:**
- Integration with LaunchDarkly will handle the bucketization of users.
- "Time to Resolution" (TTR) will be the primary metric for the A/B test.
**Action Items:**
- Greta: Define the exact TTR telemetry event $\rightarrow$ Due 2024-01-12.
- Kai: Configure LaunchDarkly relay proxy $\rightarrow$ Due 2024-01-15.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,800,000 | 8 staff over 18 months (inc. benefits/taxes). |
| **Infrastructure** | 20% | $600,000 | Bare-metal servers, Oracle Licenses, Networking. |
| **Tools & Licensing** | 10% | $300,000 | LaunchDarkly, Nessus, GitLab Premium. |
| **Contingency** | 10% | $300,000 | Reserved for regulatory changes/emergency hires. |

**Personnel Detail:**
- Tech Lead (Greta): $180k/year
- DevOps (Kai): $150k/year
- Designer (Dante): $130k/year
- Intern (Luciano): $40k/year
- 4x Mid-level Developers: $400k/year total.

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Implementation Details
To achieve Level 1 compliance, Aqueduct implements the following:
1. **Network Segmentation:** The CDE (Cardholder Data Environment) is on a separate VLAN with no direct internet access.
2. **Encryption:** Data at rest is encrypted using Oracle TDE. Data in transit uses TLS 1.3 with strong cipher suites (AES-256-GCM).
3. **Access Control:** All administrative access requires a jump host (bastion server) and MFA.
4. **Logging:** All `INSERT`, `UPDATE`, and `DELETE` operations on the `PAYMENT_METHODS` table are captured by Oracle Fine-Grained Auditing (FGA).

### Appendix B: Feature Flag Logic Flow
When a request hits the API Gateway:
1. The Gateway extracts the `user_id`.
2. The Gateway queries the **LaunchDarkly Relay Proxy**.
3. The Proxy returns the current state of the flag (e.g., `ab_test_dashboard = "variant_B"`).
4. The Gateway injects this value into the request header `X-Feature-Variant`.
5. The Frontend reads the header and renders the corresponding React component.
6. Telemetry is sent back to the backend to track the user's interaction with "variant_B".