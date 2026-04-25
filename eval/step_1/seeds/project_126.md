Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity Technical Project Specification. It is structured as the "Single Source of Truth" (SSOT) for the Stratos Systems engineering team.

***

# PROJECT SPECIFICATION: PINNACLE
**Document Version:** 1.0.4  
**Status:** Draft/Active  
**Owner:** Wren Nakamura (Engineering Manager)  
**Date:** October 24, 2023  
**Classification:** Confidential – Stratos Systems Internal

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Pinnacle" is a strategic mobile application initiative designed to position Stratos Systems as a leader in the high-end Food and Beverage (F&B) sector. The application is not merely a consumer-facing tool but a sophisticated strategic partnership integration. The primary objective is to synchronize Stratos Systems' internal operational data with a critical external partner’s proprietary API, creating a seamless ecosystem for supply chain transparency, billing, and resource management.

### 1.2 Business Justification
The F&B industry is currently experiencing a shift toward "Precision Logistics." By integrating deeply with our partner’s infrastructure, Stratos Systems can reduce procurement leakage and automate vendor payments. The high executive visibility of this project stems from the fact that Pinnacle serves as the blueprint for all future strategic integrations. Failure to execute this integration effectively would result in a loss of market share to competitors who are already adopting automated API-driven supply chains.

### 1.3 ROI Projection and Success Metrics
With a total investment of $3,000,000, the project is targeted to yield a high Return on Investment through both operational efficiency and new revenue streams.

*   **Direct Revenue Goal:** The project is mandated to generate $500,000 in new attributed revenue within the first 12 months post-launch. This will be achieved through the introduction of "Premium Tier" subscription models for partner entities.
*   **Operational Efficiency:** Reducing manual billing reconciliation from 14 business days to <24 hours via the Automated Billing module.
*   **Performance Benchmark:** The system must maintain an API response time (p95) of under 200ms at peak load (defined as 5,000 concurrent requests per second).

### 1.4 Strategic Alignment
Pinnacle aligns with the Stratos Systems "2026 Digital Core" initiative, moving away from fragmented legacy systems toward a unified, SOC 2 compliant on-premise infrastructure.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
To ensure the system remains decoupled from the external partner's API (which is subject to change on their timeline), Pinnacle utilizes **Hexagonal Architecture (Ports and Adapters)**.

*   **The Domain Core:** Contains the business logic, entities, and use cases. It has no knowledge of the database or the external API.
*   **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `BillingPort`, `PartnerApiPort`).
*   **Adapters:** Concrete implementations of the ports. For example, the `OracleDbAdapter` implements the persistence port, and the `PartnerRestAdapter` implements the external API port.

### 2.2 Technical Stack
*   **Backend:** Java 17 / Spring Boot 3.x
*   **Database:** Oracle Database 19c (Enterprise Edition)
*   **Infrastructure:** On-premise Data Center (Air-gapped from public cloud)
*   **Orchestration:** Kubernetes (K8s) on-premise cluster
*   **CI/CD:** GitLab CI
*   **Security:** SOC 2 Type II compliant encryption at rest and in transit (TLS 1.3)

### 2.3 ASCII Architecture Diagram
```text
       [ External Partner API ] <----(HTTPS/JSON)----> [ Partner Adapter ]
                                                              |
                                                              v
 [ Mobile App (UI) ] <---(REST)---> [ API Gateway ] <---> [ Input Ports ]
                                                              |
                                                              v
                                                     [ DOMAIN BUSINESS LOGIC ]
                                                     [ (Use Cases/Entities) ]
                                                              |
                                                              v
 [ Oracle DB ] <---(JDBC/SQL)---> [ Persistence Adapter ] <--- [ Output Ports ]
                                                              |
                                                              v
                                                     [ GitLab CI / K8s Pods ]
```

### 2.4 Deployment Strategy
The project utilizes **Rolling Deployments** via Kubernetes. This ensures that the "Pinnacle" application remains available during updates. The GitLab CI pipeline triggers an automated build, runs a suite of 2,000+ unit tests, and pushes a Docker image to the internal registry.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:** 
Given the reliance on a third-party API with strict quotas, Pinnacle must implement a sophisticated rate-limiting layer to prevent "noisy neighbor" syndrome and avoid being blacklisted by the partner.

**Technical Specifics:**
The system uses a **Token Bucket Algorithm** implemented via a distributed cache (Redis, on-premise) to track requests per tenant.
*   **Tier 1 (Standard):** 100 requests/minute.
*   **Tier 2 (Premium):** 500 requests/minute.
*   **Tier 3 (Enterprise):** 1,000 requests/minute.

The Usage Analytics engine captures every request/response metadata (excluding sensitive payloads) and streams it into an Oracle-backed analytics table. This allows the business to identify which partners are hitting limits and trigger upsell workflows.

**Success Criteria:** 
The system must correctly reject requests (HTTP 429) when limits are exceeded and log the event in < 50ms.

### 3.2 Multi-Tenant Data Isolation
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:** 
Pinnacle must support multiple F&B corporate clients on a shared infrastructure while ensuring that no client can ever access another client's data. This is a prerequisite for SOC 2 Type II compliance.

**Technical Specifics:**
The team will implement a **Discriminator Column Approach** (Shared Schema). Every table in the Oracle DB will contain a `tenant_id` column.
*   **Row-Level Security (RLS):** We will leverage Oracle Virtual Private Database (VPD) to automatically append `WHERE tenant_id = :current_tenant` to every query executed by the application.
*   **Context Propagation:** The `tenant_id` will be extracted from the JWT (JSON Web Token) at the API Gateway and stored in a `ThreadLocal` security context throughout the request lifecycle.

**Implementation Plan:**
1. Define the `Tenant` entity and schema.
2. Implement the `TenantInterceptor` in Spring Boot.
3. Configure Oracle VPD policies for all 10+ primary tables.

### 3.3 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** In Design

**Description:** 
This module automates the financial lifecycle of a partnership, from initial onboarding to monthly recurring revenue (MRR) collection.

**Technical Specifics:**
The system must sync with the external partner's usage data to calculate "overage" fees. 
*   **Billing Engine:** A scheduled Spring Batch job that runs on the 1st of every month.
*   **Subscription States:** `TRIAL`, `ACTIVE`, `PAST_DUE`, `CANCELED`.
*   **Integration:** The module will interface with an internal Stratos Finance API to generate invoices.

**Logic Flow:**
1. Fetch usage metrics from the Analytics module.
2. Compare usage against the subscription tier.
3. Calculate the delta and apply the pricing multiplier defined in the `Pricing_Tiers` table.
4. Generate a PDF invoice and trigger a notification to the client.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** In Progress

**Description:** 
A mobile-responsive dashboard allowing F&B managers to visualize their supply chain health.

**Technical Specifics:**
The frontend will use a grid-layout system where widget positions are stored as JSON coordinates in the database.
*   **Available Widgets:** "Daily Spend," "API Latency," "Partner Health," "Pending Invoices."
*   **State Persistence:** When a user drags a widget, a `PATCH` request is sent to `/api/v1/dashboard/layout` to save the new coordinates.

**User Experience:**
The dashboard must load in under 1.5 seconds. To achieve this, widget data is cached for 5 minutes using an internal Caffeine cache.

### 3.5 Workflow Automation Engine (Visual Rule Builder)
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:** 
A "Low-Code" engine allowing users to create "If-This-Then-That" (IFTTT) rules for their F&B operations.

**Technical Specifics:**
The engine will utilize a Directed Acyclic Graph (DAG) to represent rules.
*   **Triggers:** e.g., "API Response Time > 500ms," "Inventory Level < 10%."
*   **Actions:** e.g., "Send Email Alert," "Trigger Re-order API."

**Architecture:**
The visual builder will send a JSON representation of the rule to the backend, which will be parsed by a `RuleEvaluator` service. Because this is low priority, it will be built as a separate micro-service to avoid impacting the core billing and tenant logic.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned (`/v1/`) and require a Bearer Token.

### 4.1 Tenant Management
**Endpoint:** `POST /api/v1/tenants`
*   **Description:** Creates a new corporate tenant.
*   **Request:** `{"company_name": "GlobalCafe", "industry": "F&B", "plan": "Enterprise"}`
*   **Response:** `201 Created` | `{"tenant_id": "T-9982", "status": "provisioning"}`

**Endpoint:** `GET /api/v1/tenants/{tenant_id}/status`
*   **Description:** Retrieves current operational status of a tenant.
*   **Response:** `200 OK` | `{"tenant_id": "T-9982", "status": "active", "soc2_compliant": true}`

### 4.2 Billing & Subscription
**Endpoint:** `GET /api/v1/billing/invoice/{invoice_id}`
*   **Description:** Fetches a specific invoice.
*   **Response:** `200 OK` | `{"invoice_id": "INV-101", "amount": 4500.00, "due_date": "2026-01-01"}`

**Endpoint:** `PUT /api/v1/subscriptions/update`
*   **Description:** Upgrades or downgrades a tenant's plan.
*   **Request:** `{"tenant_id": "T-9982", "new_plan": "Premium"}`
*   **Response:** `200 OK` | `{"status": "updated", "next_billing_cycle": "2026-02-01"}`

### 4.3 Usage Analytics
**Endpoint:** `GET /api/v1/analytics/usage`
*   **Description:** Returns usage metrics for the current month.
*   **Response:** `200 OK` | `{"requests_sent": 45000, "requests_blocked": 120, "avg_latency": "145ms"}`

**Endpoint:** `GET /api/v1/analytics/latency-p95`
*   **Description:** Returns the 95th percentile latency for partner API calls.
*   **Response:** `200 OK` | `{"p95_latency": "188ms", "timestamp": "2023-10-24T10:00:00Z"}`

### 4.4 Dashboard Configuration
**Endpoint:** `PATCH /api/v1/dashboard/layout`
*   **Description:** Updates the position of dashboard widgets.
*   **Request:** `{"widget_id": "w1", "x": 0, "y": 1, "w": 2, "h": 2}`
*   **Response:** `200 OK` | `{"status": "saved"}`

**Endpoint:** `GET /api/v1/dashboard/widgets`
*   **Description:** Lists all available widgets for the tenant.
*   **Response:** `200 OK` | `[{"id": "w1", "name": "Daily Spend"}, {"id": "w2", "name": "Health"}]`

---

## 5. DATABASE SCHEMA

The database is hosted on Oracle 19c. All tables use `VARCHAR2` for strings and `NUMBER` for precision decimals.

### 5.1 Table Definitions

1.  **`TENANTS`**
    *   `tenant_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `company_name` (VARCHAR2(255)): Legal entity name.
    *   `created_at` (TIMESTAMP): Record creation date.
    *   `is_active` (NUMBER(1)): Boolean flag.
2.  **`SUBSCRIPTIONS`**
    *   `sub_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `plan_type` (VARCHAR2(50)): Standard, Premium, Enterprise.
    *   `start_date` (DATE): Subscription start.
    *   `end_date` (DATE): Subscription expiration.
3.  **`API_QUOTAS`**
    *   `quota_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `plan_type` (VARCHAR2(50)): Linked to subscription plan.
    *   `request_limit` (NUMBER): Max requests per minute.
    *   `burst_limit` (NUMBER): Maximum allowed burst.
4.  **`USAGE_LOGS`**
    *   `log_id` (PK, NUMBER): Sequence-generated ID.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `endpoint_called` (VARCHAR2(255)): The partner API path.
    *   `response_time_ms` (NUMBER): Latency of the call.
    *   `timestamp` (TIMESTAMP): Exact time of request.
5.  **`BILLING_INVOICES`**
    *   `invoice_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `amount` (NUMBER(19,4)): Total cost.
    *   `status` (VARCHAR2(20)): Paid, Unpaid, Overdue.
    *   `issued_date` (DATE): Generation date.
6.  **`DASHBOARD_CONFIGS`**
    *   `config_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `user_id` (VARCHAR2(36)): Specific user layout.
    *   `layout_json` (CLOB): JSON string of widget positions.
7.  **`WIDGET_METADATA`**
    *   `widget_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `widget_name` (VARCHAR2(100)): Display name.
    *   `data_source_query` (VARCHAR2(1000)): SQL used to fetch widget data.
8.  **`AUTOMATION_RULES`**
    *   `rule_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `rule_definition` (CLOB): JSON representation of the rule DAG.
    *   `is_enabled` (NUMBER(1)): Boolean flag.
9.  **`PARTNER_API_KEYS`**
    *   `key_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `encrypted_key` (VARCHAR2(512)): Encrypted API key for the external partner.
    *   `last_rotated` (TIMESTAMP): Last key rotation date.
10. **`USER_ACCOUNTS`**
    *   `user_id` (PK, VARCHAR2(36)): Unique identifier.
    *   `tenant_id` (FK): Links to `TENANTS`.
    *   `email` (VARCHAR2(255)): User email.
    *   `role` (VARCHAR2(50)): Admin, Viewer, Editor.

### 5.2 Relationships
*   **One-to-Many:** `TENANTS` $\rightarrow$ `SUBSCRIPTIONS`, `USAGE_LOGS`, `BILLING_INVOICES`, `USER_ACCOUNTS`.
*   **One-to-One:** `TENANTS` $\rightarrow$ `DASHBOARD_CONFIGS` (per user).
*   **Many-to-One:** `SUBSCRIPTIONS` $\rightarrow$ `API_QUOTAS`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Architecture
Due to strict security constraints, no cloud providers (AWS, Azure, GCP) are permitted. All infrastructure is hosted in the Stratos Systems on-premise data center.

#### 6.1.1 Development Environment (`dev`)
*   **Purpose:** Sandbox for developers to merge features.
*   **Infrastructure:** Single-node Kubernetes cluster.
*   **Database:** Oracle XE (Express Edition) for lightweight testing.
*   **Deployment:** Triggered on every commit to `develop` branch.

#### 6.1.2 Staging Environment (`staging`)
*   **Purpose:** Mirror of production for QA and UAT (User Acceptance Testing).
*   **Infrastructure:** 3-node Kubernetes cluster.
*   **Database:** Full Oracle 19c instance with scrubbed production data.
*   **Deployment:** Triggered on merge to `release` branch.

#### 6.1.3 Production Environment (`prod`)
*   **Purpose:** Live customer-facing application.
*   **Infrastructure:** High-availability (HA) 12-node Kubernetes cluster across two physical racks.
*   **Database:** Oracle RAC (Real Application Clusters) for zero-downtime failover.
*   **Deployment:** Rolling deployments via GitLab CI with manual approval gates.

### 6.2 CI/CD Pipeline
The pipeline is configured as follows:
1.  **Build Phase:** Maven compiles Java code $\rightarrow$ JUnit tests $\rightarrow$ SonarQube analysis.
2.  **Package Phase:** Docker image created $\rightarrow$ Scanned for vulnerabilities $\rightarrow$ Pushed to internal registry.
3.  **Deploy Phase:** Helm chart updates the Kubernetes deployment $\rightarrow$ Readiness probes verify health $\rightarrow$ Traffic shifted.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** JUnit 5 and Mockito.
*   **Requirement:** 80% minimum code coverage on all business logic in the Domain Core.
*   **Focus:** Testing pure functions and use-case logic without database dependencies.

### 7.2 Integration Testing
*   **Framework:** SpringBootTest and Testcontainers.
*   **Approach:** Testing the "Adapters" against a real Oracle instance running in a Docker container.
*   **Focus:** Verifying SQL queries, transaction management, and API contract adherence.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Appium (for mobile UI) and Postman/Newman (for API flows).
*   **Approach:** Simulating a complete user journey (e.g., Onboarding $\rightarrow$ Subscription $\rightarrow$ Dashboard usage).
*   **Focus:** Critical path verification and "Happy Path" testing.

### 7.4 Performance & Stress Testing
*   **Tool:** JMeter.
*   **Target:** Verify p95 latency $< 200$ms under 5,000 concurrent users.
*   **Scenario:** "Black Friday" simulation where API requests spike by 400%.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Project sponsor rotation out of role | High | Critical | Escalate to the steering committee to secure additional funding and new executive sponsorship. |
| **R-02** | Regulatory requirements changes | Medium | High | Engage an external SOC 2 consultant for independent assessment and monthly audits. |
| **R-03** | External API downtime | High | Medium | Implement a circuit breaker pattern (Resilience4j) and local caching of critical data. |
| **R-04** | On-premise hardware failure | Low | Critical | Utilize Oracle RAC and K8s multi-rack distribution for redundancy. |

**Impact Matrix:**
*   **Critical:** Total project stoppage or legal non-compliance.
*   **High:** Significant delay in milestones or budget overrun.
*   **Medium:** Feature degradation or minor timeline slip.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach with dependencies on the external partner's API release schedule.

### 9.1 Phase 1: Foundation (Now – March 2026)
*   **Focus:** Multi-tenant isolation and API rate limiting.
*   **Dependencies:** External API Specification v2.1.
*   **Milestone 1:** **Internal Alpha Release (2026-03-15)**. Feature set: Basic API connectivity and tenant creation.

### 9.2 Phase 2: Feature Expansion (March 2026 – May 2026)
*   **Focus:** Billing engine and Dashboard widgets.
*   **Dependencies:** Sign-off on billing logic from Finance.
*   **Milestone 2:** **Stakeholder Demo and Sign-off (2026-05-15)**. Feature set: Full billing lifecycle and visual dashboard.

### 9.3 Phase 3: Hardening & Launch (May 2026 – July 2026)
*   **Focus:** SOC 2 compliance audit and performance tuning.
*   **Dependencies:** External consultant's final report.
*   **Milestone 3:** **Post-launch Stability Confirmed (2026-07-15)**. Feature set: Fully optimized production system with zero critical bugs.

---

## 10. MEETING NOTES

### Meeting 1: Sprint Planning (2023-11-02)
*   Attendees: Wren, Gael, Ira, Uri.
*   Budget check: $3M still intact.
*   Gael: API rate limits are killing the test suite.
*   Wren: Need a mock server.
*   Uri: "I'll look into it."
*   *Note: Tense atmosphere; Gael and Wren did not interact directly during the meeting.*

### Meeting 2: Architecture Review (2023-12-15)
*   Attendees: Wren, Gael, Ira.
*   Hexagonal arch discussed.
*   Ira: Worried about Oracle DB bottlenecks with multi-tenancy.
*   Gael: Suggests VPD (Virtual Private Database).
*   Wren: "Approved. Move to implementation."
*   *Note: Gael left the meeting immediately after approval.*

### Meeting 3: Risk Alignment (2024-01-20)
*   Attendees: Wren, Stakeholders, Ira.
*   Sponsor rotating out soon.
*   Steering committee needs to be notified.
*   External consultant for SOC 2 requested.
*   Budget for consultant: $150k from contingency.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | 20+ staff across 3 departments (Engineering, QA, Product). |
| **Infrastructure** | $600,000 | Oracle Licenses, On-premise Server Hardware, K8s nodes. |
| **Tools & Licensing** | $200,000 | GitLab Premium, SonarQube, Appium Cloud, JMeter licenses. |
| **External Consulting** | $150,000 | SOC 2 Type II Compliance Auditor. |
| **Contingency** | $250,000 | Reserved for scope creep or hardware emergency. |

---

## 12. APPENDICES

### Appendix A: SOC 2 Compliance Checklist
To achieve SOC 2 Type II, the following must be evidenced:
1.  **Access Control:** MFA for all GitLab and Kubernetes access.
2.  **Change Management:** Every PR must have two approvals; no direct pushes to `main`.
3.  **Encryption:** AES-256 for `PARTNER_API_KEYS` in the database.
4.  **Monitoring:** Centralized logging via ELK stack (on-premise).

### Appendix B: Partner API Integration Details
The external partner uses a RESTful API with the following characteristics:
*   **Auth:** OAuth2 Client Credentials Flow.
*   **Format:** JSON (UTF-8).
*   **Rate Limit Headers:** 
    *   `X-RateLimit-Limit`: Total quota.
    *   `X-RateLimit-Remaining`: Remaining requests.
    *   `X-RateLimit-Reset`: Seconds until reset.
*   **Timeout:** The system must implement a 5-second timeout for all partner calls to avoid thread exhaustion.