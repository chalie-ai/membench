Due to the extreme length requirement (6,000–8,000 words) and the complexity of the requested technical specifications, this document is presented as a comprehensive, high-fidelity Project Specification. 

***

# PROJECT SPECIFICATION: PROJECT GANTRY
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Draft / Internal Review  
**Classification:** Confidential – Clearpoint Digital  
**Project Code:** CPD-GANTRY-2026  

---

## 1. EXECUTIVE SUMMARY

**Business Justification**
Project Gantry is the strategic response to a systemic failure of the current legacy payment processing system at Clearpoint Digital. Following the Q3 2025 User Experience Audit, the existing system received "catastrophic" feedback from our primary retail client base. Users reported inconsistent transaction states, an unintuitive interface that led to high error rates in manual reconciliation, and a complete lack of transparency regarding transaction failures. This resulted in a 14% churn rate among mid-market retail partners over the last six months.

The business justification for Gantry is not merely an upgrade, but a total product rebuild. The current infrastructure has become a liability; the inability to scale and the fragility of the codebase have made it impossible to introduce new features without risking systemic outages. To regain market trust and prevent further attrition, Clearpoint Digital is investing in a robust, secure, and highly performant payment processing engine.

**Strategic Goals**
Gantry aims to redefine the retail payment experience by transitioning from a fragmented legacy system to a "clean monolith" architecture. By prioritizing API stability and rate limiting, the system will ensure that high-volume retail events (e.g., Black Friday, Cyber Monday) do not lead to the systemic crashes experienced in the previous version. 

**ROI Projection**
With a total budget allocation exceeding $5M, the project is positioned as a flagship initiative with direct reporting lines to the Board of Directors. The projected ROI is calculated based on three primary levers:
1. **Churn Reduction:** By eliminating the "catastrophic" UX failures, we project a reduction in churn from 14% to <2% annually, preserving approximately $1.2M in Annual Recurring Revenue (ARR).
2. **Operational Efficiency:** The implementation of the Workflow Automation Engine will reduce the manual intervention required for transaction disputes by 40%, saving an estimated $450k in operational overhead per year.
3. **Market Expansion:** The new API-first approach allows Clearpoint Digital to enter the "Enterprise Retail" tier, with a projected increase in new customer acquisition of 20% over 24 months.

The break-even point for the $5M investment is estimated at 32 months post-launch, assuming the success criteria of a p95 response time under 200ms is met, allowing for higher transaction density per server instance.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Gantry is designed as a **Clean Monolith**. While the industry trend favors microservices, the constraints of the on-premise data center and the specific requirements of the retail payment domain necessitate a monolithic approach to avoid the network latency and distributed transaction complexity (Saga patterns, etc.) that would plague a distributed system in an on-prem environment.

The system is divided into strictly bounded contexts (Modules) to ensure that the monolith remains maintainable and that dependencies are unidirectional.

### 2.2 The Technology Stack
- **Language:** Java 21 (LTS)
- **Framework:** Spring Boot 3.3.x
- **Database:** Oracle DB 21c (Enterprise Edition)
- **Deployment Environment:** On-premise Clearpoint Digital Data Center (No Cloud Allowed)
- **Security Standard:** ISO 27001 Certified Environment
- **Logging:** Standard Out (stdout) currently; structured logging implementation is a known technical debt item.

### 2.3 ASCII Architecture Diagram
```text
[ USER LAYER ]          [ API GATEWAY / LOAD BALANCER ]
      |                               |
      |                       (SSL Termination / Rate Limiting)
      v                               v
[ RETAIL CLIENTS ] <---> [ GANTRY MONOLITH (Spring Boot) ]
                                     |
         ____________________________|____________________________
        |                            |                            |
 [ CORE PAYMENT MOD ]        [ WORKFLOW ENGINE ]       [ ANALYTICS MOD ]
        |                            |                            |
        |----------------------------|----------------------------|
                                     |
                          [ ORACLE DB 21c CLUSTER ]
                          (Shared Infrastructure)
                                     |
                          [ ISO 27001 SECURE ZONE ]
```

### 2.4 Module Boundaries
1. **Payment Core:** Handles the lifecycle of a transaction from initiation to settlement.
2. **Tenant Manager:** Manages the isolation of retail clients within the shared infrastructure.
3. **Automation Engine:** Processes business rules and triggers automated actions.
4. **Integration Bridge:** Manages the buggy third-party partner API connections.
5. **Audit & Analytics:** Tracks API usage and system performance.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics (Priority: Critical)
**Status:** In Progress | **Impact:** Launch Blocker

**Description:**
To prevent system instability and "noisy neighbor" syndromes in a shared infrastructure, Gantry must implement a sophisticated rate-limiting mechanism. This feature is critical because the previous system crashed under peak retail load due to a lack of request throttling.

**Functional Requirements:**
- **Bucket Algorithm:** Implementation of the Token Bucket algorithm to allow for bursts while maintaining a steady-state average.
- **Tiered Limits:** Different limits based on the retail client's subscription tier (e.g., Bronze: 100 req/sec, Silver: 500 req/sec, Gold: 2,000 req/sec).
- **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Dashboard:** A backend view for administrators to see which clients are hitting their limits most frequently.

**Technical Implementation:**
Rate limiting will be implemented via a Spring Boot Interceptor. Since cloud-native tools like Redis are prohibited, the state for the token buckets will be maintained in a high-performance concurrent map within the JVM, synchronized across the cluster using a lightweight heartbeat mechanism via the Oracle DB.

**Success Criteria:**
- p95 response time remains under 200ms even when rate limiting is active.
- Zero "Out of Memory" errors during peak load simulations (10k concurrent requests).

---

### 3.2 Workflow Automation Engine with Visual Rule Builder (Priority: High)
**Status:** In Review | **Impact:** Strategic Value

**Description:**
Retailers need the ability to automate payment behaviors (e.g., "If a transaction > $500 fails three times, flag for manual review and notify the manager"). The Workflow Automation Engine allows the creation of these rules without requiring code changes.

**Functional Requirements:**
- **Visual Builder:** A drag-and-drop interface (React-based) where users can map "Triggers" to "Actions."
- **Trigger Types:** Payment Success, Payment Failure, High-Value Transaction, New Customer Onboarding.
- **Action Types:** Send Email, Update Transaction Status, Trigger Webhook (pending integration), Create Internal Ticket.
- **Rule Versioning:** Ability to save drafts of rules and roll back to previous versions.

**Technical Implementation:**
The engine uses a Domain Specific Language (DSL) stored in the Oracle DB as JSONB. A "Rule Processor" service evaluates these conditions during the payment lifecycle. The Visual Rule Builder compiles the GUI layout into the JSON DSL.

**Success Criteria:**
- Rules must be evaluated in < 50ms to avoid impacting the core payment loop.
- Ability to support up to 50 active rules per tenant without performance degradation.

---

### 3.3 File Upload with Virus Scanning and CDN Distribution (Priority: Low)
**Status:** In Design | **Impact:** Nice to Have

**Description:**
Retailers need to upload bulk transaction CSVs or supporting documentation for disputes. This requires a secure pipeline to ensure malicious files do not enter the on-premise data center.

**Functional Requirements:**
- **Secure Upload:** Multi-part upload via API.
- **Virus Scanning:** Integration with an on-premise ClamAV cluster. Files are quarantined until the "Clean" signal is received.
- **CDN Distribution:** While the data center is on-premise, static assets and approved documents will be pushed to a corporate-managed CDN for faster retrieval by the retail client's global offices.
- **Retention Policy:** Automatic deletion of files after 90 days.

**Technical Implementation:**
Files are uploaded to a temporary "Landing Zone" (NFS mount). A background worker triggers the virus scan. Upon success, the file is moved to the "Permanent Store" and a CDN invalidation request is sent.

**Success Criteria:**
- 100% of files must be scanned before being accessible via the API.
- Upload latency should not exceed 2 seconds for files up to 10MB.

---

### 3.4 Multi-tenant Data Isolation with Shared Infrastructure (Priority: Low)
**Status:** In Design | **Impact:** Nice to Have

**Description:**
Gantry operates on a shared infrastructure model to minimize costs. However, for regulatory and security reasons, data from Retailer A must never be visible to Retailer B.

**Functional Requirements:**
- **Logical Isolation:** Use of a `tenant_id` column on every single table in the Oracle DB.
- **Row-Level Security (RLS):** Implementation of Oracle Virtual Private Database (VPD) to ensure the database engine itself filters queries based on the session's tenant context.
- **Tenant Context Provider:** A Spring Security filter that extracts the `tenant_id` from the API key and injects it into the ThreadLocal context.

**Technical Implementation:**
Every DAO (Data Access Object) will append a `WHERE tenant_id = :currentTenant` clause. The system will support "Super Admin" roles that can override this isolation for support purposes.

**Success Criteria:**
- Zero cross-tenant data leakage during internal penetration testing.
- No more than a 5% performance hit due to RLS.

---

### 3.5 Webhook Integration Framework for Third-Party Tools (Priority: Low)
**Status:** Blocked | **Impact:** Nice to Have

**Description:**
Allows Gantry to push real-time events to external retail software (e.g., ERP systems, Inventory Management).

**Functional Requirements:**
- **Subscription Management:** Users can define a URL and a set of events they wish to subscribe to.
- **Retry Logic:** Exponential backoff for failed deliveries (1m, 5m, 15m, 1h).
- **Signing:** All webhooks must be signed with a HMAC-SHA256 signature to allow the receiver to verify the source.
- **Delivery Logs:** A log of every attempt, including response codes and payloads.

**Technical Implementation:**
A dedicated `WebhookDispatcher` service will poll an "Outbox" table in the Oracle DB. This ensures that webhooks are only sent if the primary transaction is successfully committed (Transactional Outbox Pattern).

**Current Blocker:**
Integration is currently blocked due to the lack of a standardized internal network gateway for outbound requests from the secure zone to the public internet.

**Success Criteria:**
- Delivery of events within 5 seconds of the trigger event.
- Successful verification of signatures by 100% of pilot users.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. Authentication is handled via Bearer Tokens in the Authorization header.

### 4.1 Create Payment
**Path:** `POST /payments`  
**Description:** Initiates a new payment transaction.  
**Request:**
```json
{
  "amount": 150.00,
  "currency": "USD",
  "payment_method": "CREDIT_CARD",
  "tenant_id": "RET_9921",
  "metadata": { "order_id": "ORD-123" }
}
```
**Response (201 Created):**
```json
{
  "transaction_id": "TXN_550e8400",
  "status": "PENDING",
  "created_at": "2026-01-12T10:00:00Z"
}
```

### 4.2 Get Payment Status
**Path:** `GET /payments/{transaction_id}`  
**Description:** Retrieves the current state of a specific transaction.  
**Response (200 OK):**
```json
{
  "transaction_id": "TXN_550e8400",
  "status": "COMPLETED",
  "amount": 150.00,
  "updated_at": "2026-01-12T10:05:00Z"
}
```

### 4.3 Update Rate Limit
**Path:** `PATCH /admin/rate-limits/{tenant_id}`  
**Description:** Adjusts the request limit for a specific tenant.  
**Request:**
```json
{
  "requests_per_second": 1000
}
```
**Response (200 OK):**
```json
{ "status": "updated", "new_limit": 1000 }
```

### 4.4 Trigger Workflow Rule
**Path:** `POST /workflows/execute`  
**Description:** Manually triggers a rule for testing purposes.  
**Request:**
```json
{ "rule_id": "RULE_441", "tenant_id": "RET_9921" }
```
**Response (202 Accepted):**
```json
{ "job_id": "JOB_8821", "status": "QUEUED" }
```

### 4.5 Upload Document
**Path:** `POST /documents/upload`  
**Description:** Uploads a file for virus scanning and storage.  
**Request:** `multipart/form-data` (File, TenantID)  
**Response (202 Accepted):**
```json
{ "file_id": "FILE_001", "status": "SCANNING" }
```

### 4.6 Get File Status
**Path:** `GET /documents/status/{file_id}`  
**Description:** Checks if the virus scan is complete.  
**Response (200 OK):**
```json
{ "file_id": "FILE_001", "status": "CLEAN", "cdn_url": "https://cdn.clearpoint.com/f/001" }
```

### 4.7 Get Usage Analytics
**Path:** `GET /analytics/usage?tenant_id={id}&period=daily`  
**Description:** Returns API consumption metrics.  
**Response (200 OK):**
```json
{
  "tenant_id": "RET_9921",
  "total_requests": 450000,
  "rate_limit_hits": 1200,
  "p95_latency": "185ms"
}
```

### 4.8 Register Webhook
**Path:** `POST /webhooks/subscribe`  
**Description:** Subscribes a URL to specific payment events.  
**Request:**
```json
{
  "url": "https://client-api.com/webhooks",
  "events": ["payment.success", "payment.failed"]
}
```
**Response (201 Created):**
```json
{ "subscription_id": "SUB_123" }
```

---

## 5. DATABASE SCHEMA

**Database Engine:** Oracle DB 21c  
**Schema Name:** `GANTRY_CORE`

### Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `TENANTS` | `tenant_id` (PK), `name`, `tier_id` | 1:N with `PAYMENTS` | Stores retail client profiles. |
| `TENANT_TIERS` | `tier_id` (PK), `rate_limit`, `monthly_fee` | 1:N with `TENANTS` | Defines service levels. |
| `PAYMENTS` | `txn_id` (PK), `tenant_id` (FK), `amount`, `status` | N:1 with `TENANTS` | Primary transaction ledger. |
| `PAYMENT_LOGS` | `log_id` (PK), `txn_id` (FK), `event_type`, `ts` | N:1 with `PAYMENTS` | Audit trail for state changes. |
| `WORKFLOW_RULES` | `rule_id` (PK), `tenant_id` (FK), `dsl_config` | N:1 with `TENANTS` | Automation logic (JSON). |
| `RULE_EXECUTIONS` | `exec_id` (PK), `rule_id` (FK), `status` | N:1 with `WORKFLOW_RULES` | History of rule triggers. |
| `DOCUMENTS` | `file_id` (PK), `tenant_id` (FK), `status`, `path` | N:1 with `TENANTS` | File metadata and scan status. |
| `WEBHOOK_SUBS` | `sub_id` (PK), `tenant_id` (FK), `url`, `events` | N:1 with `TENANTS` | Webhook endpoints. |
| `WEBHOOK_LOGS` | `log_id` (PK), `sub_id` (FK), `response_code` | N:1 with `WEBHOOK_SUBS` | Outbound delivery history. |
| `API_METRICS` | `metric_id` (PK), `tenant_id` (FK), `endpoint`, `latency` | N:1 with `TENANTS` | Performance data for analytics. |

**Key Relationships:**
- `TENANTS` $\rightarrow$ `PAYMENTS` (One-to-Many): Critical for data isolation.
- `TENANTS` $\rightarrow$ `WORKFLOW_RULES` (One-to-Many): Allows custom automation per client.
- `PAYMENTS` $\rightarrow$ `PAYMENT_LOGS` (One-to-Many): Ensures full auditability for ISO 27001.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications
Since cloud providers are forbidden, all environments are hosted on physical hardware in the Clearpoint Digital Data Center.

| Environment | Purpose | Hardware Profile | Data Isolation |
| :--- | :--- | :--- | :--- |
| **DEV** | Feature development & unit tests | 2x VM (16GB RAM, 4 vCPU) | Local H2 / Shared Oracle Dev |
| **STAGING** | Integration & UAT | 4x VM (32GB RAM, 8 vCPU) | Oracle Staging Instance |
| **PROD** | Live Retail Traffic | 12x Physical Blade Servers | Oracle RAC Cluster (High Avail) |

### 6.2 The "Release Train"
Gantry adheres to a strict **Weekly Release Train** deployment model.
- **Cycle:** Tuesday 02:00 AM UTC.
- **Cut-off:** All PRs must be merged and verified in Staging by Monday 12:00 PM UTC.
- **No Hotfixes:** There are no emergency hotfixes outside the train. If a critical bug is found, it must wait for the next Tuesday release or the entire system must be rolled back to the previous weekly version.
- **Verification:** Every release requires a signed-off "Go/No-Go" checklist from Amara Park (Tech Lead).

### 6.3 Security & Compliance
- **ISO 27001:** The environment is air-gapped from the public internet except via the API Gateway. 
- **Data at Rest:** Oracle Transparent Data Encryption (TDE) is enabled for all PII columns.
- **Data in Transit:** TLS 1.3 required for all internal and external communication.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5, Mockito.
- **Coverage Requirement:** Minimum 80% line coverage for the `Payment Core` and `Tenant Manager` modules.
- **Execution:** Triggered on every Git push via the internal Jenkins pipeline.

### 7.2 Integration Testing
- **Focus:** Database interactions and the Integration Bridge (Partner API).
- **Approach:** Use of Testcontainers to spin up a local Oracle XE instance to validate SQL queries and RLS policies.
- **Partner Simulation:** Due to the buggy nature of the partner API, a "Mock Partner Server" has been developed to simulate various failure modes (timeouts, 500 errors, malformed JSON).

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full "Happy Path" from payment initiation $\rightarrow$ workflow trigger $\rightarrow$ webhook notification.
- **Tooling:** Selenium for the Visual Rule Builder; Postman Collections for the API suite.
- **Environment:** Executed exclusively in the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Integration partner API is undocumented and buggy | High | High | Accept the risk; implement aggressive error handling and monitor logs weekly. |
| **R-02** | Team has no experience with Java/Spring/Oracle | High | Medium | Engage external consultant for a monthly independent architectural assessment. |
| **R-03** | Release Train rigidity prevents critical fixes | Medium | High | Improve Staging test coverage to catch bugs before the Monday cut-off. |
| **R-04** | On-premise hardware failure | Low | Critical | Use Oracle RAC for database high availability and load-balanced application nodes. |

**Impact Matrix:**
- **High/High:** Immediate attention required (R-01).
- **High/Medium:** Continuous monitoring (R-02).
- **Medium/High:** Process improvement needed (R-03).

---

## 9. TIMELINE & MILESTONES

### 9.1 Project Phases

**Phase 1: Foundation (Oct 2025 - Mar 2026)**
- Setup of on-premise servers and Oracle DB installation.
- Development of Core Payment Module and Rate Limiting (Critical).
- Establishment of the Weekly Release Train.
- *Dependency: Hardware provisioning must be completed.*

**Phase 2: Automation & Beta (Mar 2026 - May 2026)**
- Implementation of the Workflow Automation Engine.
- Internal Alpha testing.
- Integration of the (buggy) partner API.
- *Dependency: Milestone 1 completion.*

**Phase 3: Hardening & Launch (May 2026 - July 2026)**
- External Beta with 10 pilot users.
- Performance tuning for p95 < 200ms.
- Final ISO 27001 audit.
- *Dependency: Milestone 2 completion.*

### 9.2 Key Milestone Dates
- **Milestone 1 (Internal Alpha):** 2026-03-15
- **Milestone 2 (External Beta):** 2026-05-15
- **Milestone 3 (First Paying Customer):** 2026-07-15

---

## 10. MEETING NOTES

*Note: These notes are extracted from the "Project Gantry Master Log," a 200-page shared document. The document is currently unsearchable and formatted as a continuous stream of consciousness.*

**Meeting #142: Technical Alignment (2025-11-02)**
- **Attendees:** Amara Park, Yuki Jensen, Adaeze Kim.
- **Discussion:** Adaeze raised concerns that the `tenant_id` is being missed in several new queries in the `Analytics Mod`. Amara told her to "just fix it" and not to bring it up in the general meeting. 
- **Conflict:** Yuki noted that the infrastructure provisioning is delayed because the "cloud provider" (which should not be used) is still being contacted by a junior procurement officer. Amara and the PM spent 20 minutes arguing about who owns the procurement ticket; they eventually stopped speaking to each other for the remainder of the meeting.
- **Decision:** Proceed with H2 for local dev, but the Prod environment remains a mystery.

**Meeting #158: Partner API Crisis (2025-12-15)**
- **Attendees:** Amara Park, Kenji Moreau, Yuki Jensen.
- **Discussion:** The partner API returned a `418 I'm a teapot` error for three hours. There is no documentation for this. 
- **Decision:** Amara decided we will "accept the risk" and simply log the error and move on. Kenji argued that this will lead to catastrophic user feedback again. Amara ignored the comment.
- **Action Item:** Yuki to set up a weekly monitor for 4xx/5xx errors from the partner.

**Meeting #175: Release Train Review (2026-01-20)**
- **Attendees:** All Team.
- **Discussion:** Adaeze accidentally pushed a change to Staging on Tuesday afternoon (after the cut-off). 
- **Decision:** The release was rolled back entirely. The team lost a week of progress.
- **Outcome:** Amara reiterated that "no exceptions, no hotfixes." The team spent the rest of the meeting in silence.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,250,000 (Board Approved)

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,150,000 | Salaries for 15 distributed members across 5 countries. |
| **Infrastructure** | 20% | $1,050,000 | On-premise blade servers, Oracle Enterprise Licenses, Networking. |
| **External Consulting**| 10% | $525,000 | Independent tech assessment for the Java/Oracle stack. |
| **Tools & Software** | 5% | $262,500 | IDE licenses, Jenkins on-prem, ClamAV Enterprise. |
| **Contingency** | 5% | $262,500 | Emergency fund for hardware failures or audit gaps. |

---

## 12. APPENDICES

### Appendix A: Performance Benchmarking Parameters
To achieve the success criterion of **p95 < 200ms**, the following constraints are applied to the JVM:
- **Heap Size:** 32GB (Xmx32g) to minimize Garbage Collection pauses.
- **GC Algorithm:** ZGC (Z Garbage Collector) to keep pause times under 10ms.
- **Oracle Connection Pool:** HikariCP with a maximum pool size of 100 connections per node.
- **Testing Load:** Peak load is defined as 5,000 Transactions Per Second (TPS) across 12 nodes.

### Appendix B: ISO 27001 Compliance Checklist
The following must be verified by the external auditor prior to Milestone 3:
1. **Access Control:** All SSH access to the on-prem servers must be logged and routed through a Bastion host.
2. **Encryption:** All sensitive data in the `PAYMENTS` table (e.g., card tokens) must be encrypted using AES-256.
3. **Audit Logs:** The `PAYMENT_LOGS` table must be read-only for application users and only writable by the system service account.
4. **Physical Security:** Data center access must be restricted to badge-entry only with 24/7 CCTV.