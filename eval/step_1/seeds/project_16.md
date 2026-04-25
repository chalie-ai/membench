# Project Specification: Gantry Supply Chain Management System
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Status:** Draft / In-Review  
**Project Lead:** Brigid Kim (Tech Lead)  
**Company:** Tundra Analytics  

---

## 1. Executive Summary

### 1.1 Project Overview
**Gantry** is a specialized supply chain management (SCM) system engineered by Tundra Analytics to penetrate the high-growth Agriculture Technology (AgTech) sector. The system is designed to solve complex logistics, inventory tracking, and distribution challenges inherent in large-scale agricultural operations, where volatility in crop yields and perishability requires real-time data precision.

### 1.2 Business Justification
The impetus for Gantry is a strategic enterprise partnership with a single anchor client—a global agricultural conglomerate—that has committed to a recurring annual contract value (ACV) of $2,000,000. This guaranteed revenue stream provides the financial bedrock for Tundra Analytics to build a new product vertical. By developing Gantry, Tundra Analytics moves from a pure data-analytics firm to a platform provider, diversifying its market position and creating a scalable product that can be licensed to other AgTech firms globally.

### 1.3 ROI Projection
With a total project budget of $3,000,000, the project is positioned for a rapid return on investment. 
- **Direct Revenue:** The $2M annual payment from the lead client ensures that the initial investment is recouped within 1.5 years of launch, assuming standard operational overheads.
- **Indirect Gains:** By reducing the cost per transaction by 35% compared to the client's legacy system, Gantry provides a tangible value proposition that justifies premium pricing for future clients.
- **Market Expansion:** Target growth includes scaling to 10,000 Monthly Active Users (MAU) within six months of launch, creating a massive data flywheel for Tundra’s other analytics products.

### 1.4 Strategic Objectives
The primary goal is to deliver a FedRAMP-compliant, secure, and scalable infrastructure that can handle the rigorous demands of government-regulated agricultural supply chains. The success of Gantry will be measured by its ability to maintain a high-availability environment while providing granular audit trails and seamless integration via SSO and API rate-limiting to ensure system stability.

---

## 2. Technical Architecture

### 2.1 Architectural Philosophy
Gantry employs a **Microservices Architecture** driven by **Event-Driven Communication**. Given the nature of supply chain data—where a change in a shipment status must trigger updates in inventory, billing, and reporting—an asynchronous approach is critical. We utilize **Apache Kafka** as the central nervous system for all inter-service communication, ensuring that services remain decoupled and resilient.

### 2.2 The Technology Stack
- **Backend:** Python 3.11 with **FastAPI**. FastAPI was chosen for its high performance, asynchronous capabilities, and automatic OpenAPI documentation.
- **Database:** **MongoDB**. A document-oriented database is essential for the flexible schemas required by diverse agricultural product types (e.g., seeds, fertilizers, livestock).
- **Task Queue:** **Celery** with Redis as a broker for handling long-running tasks such as PDF generation and report scheduling.
- **Containerization:** **Docker Compose** for local development and orchestration, ensuring environment parity across the 20+ person team.
- **Deployment:** Self-hosted infrastructure to maintain strict control over data residency, managed via **GitHub Actions** for CI/CD.
- **Security:** Implementation of **FedRAMP** standards, including encryption at rest (AES-256) and in transit (TLS 1.3).

### 2.3 Infrastructure Diagram (ASCII Representation)

```text
[ Client Layer ]  --> [ Cloudflare WAF / Load Balancer ]
                                  |
                                  v
[ API Gateway ] <---------- [ Auth Service (OIDC/SAML) ]
       |                           |
       +---------------------------+
       |                           |
       v                           v
[ Order Service ]          [ Inventory Service ]  <-- (Microservices)
       |                           |
       +------------+--------------+
                    |
                    v
            [ Apache Kafka ] <--- (Event Bus: "OrderCreated", "StockUpdated")
                    |
       +------------+--------------+
       |                            |
       v                            v
[ Report Service ]          [ Audit Logger Service ]
(Celery Workers)            (Tamper-Evident Storage)
       |                            |
       +------------+--------------+
                    |
                    v
            [ MongoDB Cluster ] <--- (Persistent Storage)
```

### 2.4 Data Flow and Communication
When a user creates a shipment, the `Order Service` writes to MongoDB and publishes an `Order_Created` event to Kafka. The `Inventory Service` consumes this event to decrement stock levels, and the `Audit Logger` records the transaction in a read-only immutable log. This ensures that if the Report Service is down, the core transaction is not blocked.

---

## 3. Detailed Feature Specifications

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
To prevent system degradation and ensure fair usage across the 10,000 expected MAUs, Gantry requires a sophisticated rate-limiting mechanism. This is not merely a global limit but a tiered system based on the user's organization level.

**Functional Specifications:**
- **Tiered Limits:** Implementation of "Bronze," "Silver," and "Gold" tiers. For example, Gold users (the enterprise client) may have 10,000 requests per hour, while Bronze users have 1,000.
- **Sliding Window Algorithm:** To prevent "bursting" at the turn of the hour, the system will use a sliding window log to track requests.
- **Headers:** All API responses must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Dashboard:** A dedicated view for administrators to see which API endpoints are most utilized and identify users hitting limits frequently.

**Technical Implementation:**
Rate limiting will be implemented as a FastAPI middleware using Redis as the counter store. When a request arrives, the middleware checks the `org_id` in the JWT. If the count exceeds the threshold in Redis, a `429 Too Many Requests` error is returned. Usage analytics will be streamed via Kafka to a separate MongoDB collection specifically for telemetry.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** In Review

**Description:**
Given the FedRAMP requirements and the high value of agricultural commodities, every change to the system must be logged in a way that cannot be altered or deleted by any user, including administrators.

**Functional Specifications:**
- **Comprehensive Capture:** Every `POST`, `PUT`, `PATCH`, and `DELETE` request must be logged, capturing the user ID, timestamp, original state, new state, and IP address.
- **Immutability:** Logs must be stored in a "Write Once, Read Many" (WORM) fashion.
- **Hash Chaining:** To ensure tamper-evidence, each log entry will contain a SHA-256 hash of the previous entry, creating a cryptographic chain. Any alteration of a historical record will break the chain.
- **Audit Search:** A read-only interface for compliance officers to search logs by entity ID or date range.

**Technical Implementation:**
A dedicated `Audit Service` will subscribe to all Kafka events. It will write records to a MongoDB collection with a "locked" flag. Periodically, the system will generate a "root hash" (Merkle Tree) of the daily logs and sign it with a private key stored in a Hardware Security Module (HSM).

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** In Design

**Description:**
Enterprise clients require high-level summaries of supply chain efficiency, waste metrics, and delivery timelines, delivered automatically to their inbox.

**Functional Specifications:**
- **Template Engine:** Users can define report templates (e.g., "Weekly Waste Report") selecting specific KPIs.
- **Scheduled Delivery:** A cron-like interface allowing users to schedule reports (Daily, Weekly, Monthly).
- **Formats:** Support for professional PDF layout (via ReportLab) and raw CSV exports for further analysis in Excel.
- **Delivery Channels:** Integration with SMTP for email and an S3-compatible bucket for downloadable archives.

**Technical Implementation:**
The `Report Service` will use Celery Beat to trigger scheduled tasks. A worker will query the MongoDB database, aggregate data using the Aggregation Framework, and render the document. Since PDF generation is CPU-intensive, these workers will be scaled independently of the FastAPI web servers.

### 3.4 SSO Integration with SAML and OIDC Providers
**Priority:** Medium | **Status:** Complete

**Description:**
To support the enterprise client's security posture, Gantry must integrate with their existing Identity Provider (IdP) such as Okta, Azure AD, or Ping Identity.

**Functional Specifications:**
- **SAML 2.0 Support:** Full support for Service Provider (SP) initiated and IdP initiated SSO.
- **OIDC (OpenID Connect):** Support for modern OAuth2 based authentication flows.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user account in Gantry upon their first successful SSO login based on SAML assertions.
- **Role Mapping:** Mapping SAML attributes (e.g., `groups`) to Gantry internal roles (e.g., `Warehouse_Manager`, `Regional_Director`).

**Technical Implementation:**
Integration was achieved using the `python-saml` and `authlib` libraries. The system acts as the Service Provider, redirecting users to the configured IdP. Upon successful authentication, a JWT is issued by Gantry, containing the user's scoped permissions and session expiry.

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low | **Status:** In Design

**Description:**
As Gantry scales globally, it must support users in different geographic regions with diverse languages.

**Functional Specifications:**
- **12 Language Support:** Initial rollout to include English, Spanish, French, Mandarin, Portuguese, German, Japanese, Hindi, Arabic, Vietnamese, Thai, and Dutch.
- **Dynamic Content Switching:** The UI must change languages without requiring a page reload.
- **Locale-Aware Formatting:** Date formats (DD/MM/YYYY vs MM/DD/YYYY), currency symbols, and number separators must adjust based on the user's locale.
- **RTL Support:** Proper CSS mirroring for Right-to-Left languages like Arabic.

**Technical Implementation:**
Frontend (React) will utilize `i18next` for translation management. Translation keys will be stored in JSON files and served via a CDN. The backend will support the `Accept-Language` HTTP header to return error messages and system emails in the user's preferred language.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1`. Authentication is required via Bearer Token (JWT).

### 4.1 Create Shipment
- **Endpoint:** `POST /shipments`
- **Description:** Initiates a new movement of goods in the supply chain.
- **Request Body:**
```json
{
  "origin_id": "WH-402",
  "destination_id": "DIST-10",
  "items": [
    {"sku": "SEED-CORN-01", "quantity": 500, "unit": "bags"},
    {"sku": "FERT-N-05", "quantity": 20, "unit": "tons"}
  ],
  "priority": "high",
  "estimated_arrival": "2025-05-20T14:00:00Z"
}
```
- **Response (201 Created):**
```json
{
  "shipment_id": "SHIP-99821",
  "status": "pending",
  "created_at": "2025-05-10T09:00:00Z"
}
```

### 4.2 Update Inventory
- **Endpoint:** `PATCH /inventory/{item_id}`
- **Description:** Adjusts the stock level of a specific item.
- **Request Body:**
```json
{
  "adjustment": -50,
  "reason": "spoilage",
  "operator_id": "USER-772"
}
```
- **Response (200 OK):**
```json
{
  "item_id": "SEED-CORN-01",
  "new_balance": 450,
  "timestamp": "2025-05-11T10:15:00Z"
}
```

### 4.3 Get Audit Logs
- **Endpoint:** `GET /audit/logs`
- **Description:** Retrieves a paginated list of tamper-evident logs.
- **Query Params:** `entity_type=shipment`, `entity_id=SHIP-99821`, `page=1`, `limit=20`
- **Response (200 OK):**
```json
{
  "logs": [
    {
      "log_id": "LOG-1002",
      "timestamp": "2025-05-10T09:00:05Z",
      "action": "CREATE",
      "user": "Brigid Kim",
      "prev_hash": "a8f2...12b",
      "curr_hash": "b9e1...44c"
    }
  ],
  "pagination": { "total": 1, "next": null }
}
```

### 4.4 Schedule Report
- **Endpoint:** `POST /reports/schedule`
- **Description:** Sets up a recurring PDF/CSV report.
- **Request Body:**
```json
{
  "template_id": "waste_summary_v1",
  "frequency": "weekly",
  "delivery_day": "Monday",
  "recipients": ["manager@client.com", "ops@client.com"],
  "format": "pdf"
}
```
- **Response (201 Created):**
```json
{ "schedule_id": "SCHED-441", "next_run": "2025-05-12T08:00:00Z" }
```

### 4.5 Get Usage Analytics
- **Endpoint:** `GET /analytics/usage`
- **Description:** Returns API consumption metrics for the organization.
- **Response (200 OK):**
```json
{
  "org_id": "ORG-CORP-01",
  "total_requests_24h": 450000,
  "rate_limit_hits": 12,
  "top_endpoints": [
    {"path": "/shipments", "calls": 200000},
    {"path": "/inventory", "calls": 150000}
  ]
}
```

### 4.6 Get User Profile (SSO Linked)
- **Endpoint:** `GET /users/me`
- **Description:** Fetches current authenticated user details from the OIDC provider.
- **Response (200 OK):**
```json
{
  "user_id": "UID-9912",
  "email": "orla.fischer@tundra.com",
  "roles": ["DevOps_Lead", "Admin"],
  "provider": "Okta"
}
```

### 4.7 Update Shipment Status
- **Endpoint:** `PUT /shipments/{shipment_id}/status`
- **Description:** Updates the current stage of a shipment (e.g., Shipped, In Transit, Delivered).
- **Request Body:**
```json
{
  "status": "delivered",
  "actual_arrival": "2025-05-20T15:30:00Z",
  "notes": "Delivered to West Gate Warehouse."
}
```
- **Response (200 OK):**
```json
{ "shipment_id": "SHIP-99821", "status": "delivered" }
```

### 4.8 Trigger Immediate Report
- **Endpoint:** `POST /reports/generate-now`
- **Description:** Manually triggers a report generation task.
- **Request Body:**
```json
{ "template_id": "inventory_snapshot", "format": "csv" }
```
- **Response (202 Accepted):**
```json
{ "task_id": "celery-task-abc-123", "status": "queued" }
```

---

## 5. Database Schema

Gantry utilizes MongoDB. While schemaless, the application enforces the following logical structures.

### 5.1 Collections and Fields

| Collection | Purpose | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `Organizations` | Tenant data | `_id`, `name`, `subscription_tier`, `saml_config` | 1:N with Users |
| `Users` | User profiles | `_id`, `org_id`, `email`, `role`, `last_login` | N:1 with Organizations |
| `Warehouses` | Physical locations | `_id`, `org_id`, `name`, `address`, `capacity` | 1:N with Inventory |
| `Inventory` | Stock tracking | `_id`, `warehouse_id`, `sku`, `quantity`, `unit` | N:1 with Warehouses |
| `Shipments` | Logistics tracking | `_id`, `origin_id`, `dest_id`, `status`, `items[]` | N:1 with Warehouses |
| `ShipmentItems` | Itemized shipment detail | `_id`, `shipment_id`, `sku`, `qty_shipped` | N:1 with Shipments |
| `AuditLogs` | Tamper-evident trail | `_id`, `user_id`, `action`, `timestamp`, `prev_hash` | N:1 with Users |
| `Reports` | Generated files | `_id`, `user_id`, `template_id`, `file_url`, `created_at` | N:1 with Users |
| `ReportSchedules`| Recurring jobs | `_id`, `user_id`, `cron_expression`, `format` | N:1 with Users |
| `ApiTelemetry` | Rate limit tracking | `_id`, `org_id`, `endpoint`, `timestamp`, `response_code` | N:1 with Organizations |

### 5.2 Relationship Logic
- **Multi-Tenancy:** All collections (except global system logs) contain an `org_id`. Every query is scoped by `org_id` to ensure data isolation between different enterprise clients.
- **Inventory-Shipment Link:** When a `Shipment` is created, the `Inventory` collection is updated via a transaction to ensure atomicity.
- **Audit Chain:** The `AuditLogs` collection uses a sequential pointer where `log[n].prev_hash == hash(log[n-1])`.

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Gantry utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and internal testing.
- **Infrastructure:** Shared Docker Compose cluster on a local server.
- **Data:** Mock data, sanitized subsets of production.
- **Deployment:** Automatic deploy on every push to `develop` branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of Production, self-hosted on a dedicated staging VPC.
- **Data:** Anonymized production clones.
- **Deployment:** Manual trigger from `develop` to `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live enterprise operations.
- **Infrastructure:** High-availability (HA) cluster with redundant nodes.
- **Deployment:** **Blue-Green Deployment**. New versions are deployed to a "Green" environment. After health checks pass, the load balancer switches traffic from "Blue" to "Green," allowing for zero-downtime updates and instant rollback.

### 6.2 CI/CD Pipeline
We use **GitHub Actions** for orchestration. 
- **Stage 1: Linting & Testing:** Runs `flake8` and `pytest`.
- **Stage 2: Containerization:** Builds Docker images and pushes to a private registry.
- **Stage 3: Deployment:** Triggers the Blue-Green switch.
- **Current Issue:** The pipeline currently takes 45 minutes due to sequential test execution. A priority for the DevOps engineer (Orla Fischer) is to implement parallel test shards.

### 6.3 FedRAMP Compliance Layer
To achieve FedRAMP authorization, the infrastructure implements:
- **FIPS 140-2** validated encryption modules.
- **Strict Access Control:** No direct SSH access to production; all changes via CI/CD or a bastion host with MFA.
- **Continuous Monitoring:** Integration with a SIEM (Security Information and Event Management) tool to monitor logs in real-time.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Scope:** Individual functions, API utility methods, and business logic.
- **Tooling:** `pytest`.
- **Requirement:** Minimum 80% code coverage. Every PR must pass all unit tests before being eligible for review.

### 7.2 Integration Testing
- **Scope:** Interaction between services (e.g., FastAPI $\rightarrow$ Kafka $\rightarrow$ Audit Service).
- **Approach:** Use of **Testcontainers** to spin up temporary MongoDB and Kafka instances during the test run to avoid "dirty" shared databases.
- **Focus:** Ensuring that event-driven messages are correctly produced and consumed.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Create Shipment $\rightarrow$ Verify Inventory Decrease $\rightarrow$ Check Audit Log").
- **Tooling:** Playwright for UI-driven flows and Python `requests` for API-driven flows.
- **Frequency:** Run once daily against the Staging environment.

### 7.4 Performance and Load Testing
- **Scope:** Validating the system can handle 10,000 MAUs.
- **Tooling:** Locust.
- **Metric:** Response time must remain $< 200ms$ for 95% of requests under a load of 500 concurrent users.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut of 30% in next fiscal quarter | Medium | High | Escalate to steering committee; identify "must-have" vs "nice-to-have" features to prune scope if needed. |
| R-02 | Key Architect leaving in 3 months | High | Critical | Immediate knowledge transfer sessions; document all architecture decisions in Confluence; raise as a blocker in the next board meeting to prioritize a replacement. |
| R-03 | Medical leave of key team member (6 weeks) | Current | Medium | Redistribute workload among remaining 20+ staff; adjust sprint velocity expectations. |
| R-04 | CI Pipeline Bottleneck (45min build) | Certain | Medium | Implement parallelization in GitHub Actions and optimize Docker layer caching. |
| R-05 | FedRAMP Audit Failure | Low | Critical | Engage a third-party compliance consultant for a pre-audit gap analysis. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate action required. (R-02)
- **High:** Regular monitoring and active mitigation. (R-01)
- **Medium:** Managed through standard project processes. (R-03, R-04)
- **Low:** Monitored periodically. (R-05)

---

## 9. Timeline and Phases

### 9.1 Phase 1: Foundation & Core API (Now - 2025-04-15)
- **Focus:** Base microservices, MongoDB schema setup, Kafka event bus implementation.
- **Dependencies:** SSO integration must be finalized.
- **Milestone 1:** Architecture review complete (Target: 2025-04-15).

### 9.2 Phase 2: Feature Expansion & Beta (2025-04-16 - 2025-06-15)
- **Focus:** Report generation, Audit logging, and API rate limiting.
- **Dependencies:** Completion of core shipment and inventory logic.
- **Milestone 2:** External beta with 10 pilot users (Target: 2025-06-15).

### 9.3 Phase 3: Hardening & Compliance (2025-06-16 - 2025-08-15)
- **Focus:** FedRAMP authorization, security hardening, and L10n/I18n.
- **Dependencies:** Stability in Beta users' feedback.
- **Milestone 3:** Security audit passed (Target: 2025-08-15).

### 9.4 Phase 4: Scale & Launch (2025-08-16 - Launch)
- **Focus:** Load testing, final documentation, and onboarding the enterprise client.
- **Success Metric:** Achieving 10,000 MAU within 6 months.

---

## 10. Meeting Notes

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Brigid Kim, Orla Fischer, Chandra Stein, Luna Kim  
**Discussion:**
- Brigid presented the move to Kafka for event-driven communication. Orla raised concerns about the overhead of managing Kafka in a self-hosted environment.
- Chandra noted that the UX needs to reflect "pending" states while Kafka events are processing (asynchronous UI).
- Luna asked about the database choice; Brigid clarified that MongoDB's flexibility is required for varying agricultural product attributes.

**Action Items:**
- [Orla] Draft the Docker Compose configuration for the Kafka cluster. (Due: 2023-11-10)
- [Brigid] Finalize the event schema for `Order_Created`. (Due: 2023-11-05)
- [Chandra] Create wireframes for the "Async Status" indicators in the UI. (Due: 2023-11-15)

### Meeting 2: Security and Compliance Sync
**Date:** 2023-12-15  
**Attendees:** Brigid Kim, Orla Fischer, External Security Consultant  
**Discussion:**
- The consultant highlighted that the current logging system is not "tamper-evident."
- Discussion on using hash-chaining (similar to a blockchain) to ensure logs cannot be altered.
- Orla mentioned the 45-minute CI pipeline is hindering the ability to push security patches quickly.

**Action Items:**
- [Brigid] Design the hash-chaining logic for the Audit Logger. (Due: 2023-12-22)
- [Orla] Investigate GitHub Action parallelization to reduce build time. (Due: 2024-01-05)
- [Brigid] Map out the FedRAMP controls required for the "High" impact level. (Due: 2024-01-15)

### Meeting 3: Budget and Resource Review
**Date:** 2024-01-10  
**Attendees:** Brigid Kim, Tundra Analytics Execs  
**Discussion:**
- The executive team warned of a possible 30% budget cut in the next quarter due to company-wide belt-tightening.
- Brigid highlighted that the key architect is leaving in 3 months, creating a massive knowledge gap.
- Discussion on the medical leave of a key developer; the team is currently absorbing the work, but velocity is down 15%.

**Action Items:**
- [Brigid] Escalate the budget risk to the steering committee to protect the $3M investment. (Due: 2024-01-15)
- [Execs] Approve a recruitment budget to replace the departing architect. (Due: 2024-01-20)
- [Brigid] Adjust the Q1 roadmap to account for the team member's medical leave. (Due: 2024-01-12)

---

## 11. Budget Breakdown

**Total Budget:** $3,000,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $2,100,000 | Salaries for 20+ staff (Devs, DevOps, UX, Project Lead, Intern) over the project lifecycle. |
| **Infrastructure** | $400,000 | Self-hosted server hardware, high-availability clusters, and networking gear. |
| **Tools & Licenses** | $200,000 | MongoDB Enterprise, Kafka licenses, Security Scanning tools (Snyk, SonarQube), and GitHub Enterprise. |
| **Compliance & Audit** | $150,000 | Third-party FedRAMP auditors and security consultants. |
| **Contingency** | $150,000 | Reserved for emergency hiring or unexpected infrastructure scaling needs. |

---

## 12. Appendices

### Appendix A: Detailed Hash-Chaining Algorithm for Audit Logs
To ensure the "tamper-evident" nature of the Audit Trail, the `Audit Service` implements the following logic:
1. For the first log entry ($L_0$), calculate $H_0 = \text{SHA256}(\text{data}_0)$.
2. For every subsequent entry ($L_n$):
   - Retrieve the hash of the previous entry $H_{n-1}$.
   - Combine the current data and the previous hash: $\text{combined\_string} = \text{data}_n + H_{n-1}$.
   - Calculate the new hash: $H_n = \text{SHA256}(\text{combined\_string})$.
3. Store $H_n$ in the `curr_hash` field and $H_{n-1}$ in the `prev_hash` field.
4. **Verification:** A validator script iterates through the collection, recalculating hashes. If any recalculated $H_n$ does not match the stored value, the audit trail is marked as "compromised."

### Appendix B: FedRAMP Authorization Checklist
Gantry must adhere to the following controls for government certification:
- **AC-2 (Account Management):** Automated account disabling after 30 days of inactivity.
- **AU-2 (Event Logging):** All security-relevant events must be logged to the Audit Service.
- **IA-2 (Identification and Authentication):** Multi-factor authentication (MFA) is mandatory for all administrative access.
- **SC-8 (Transmission Confidentiality):** All data in transit must use TLS 1.3 with approved cipher suites.
- **CP-2 (Contingency Plan):** Proof of a tested Disaster Recovery (DR) plan with a Recovery Time Objective (RTO) of 4 hours.