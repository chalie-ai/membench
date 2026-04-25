Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive Technical Specification Document (TSD). It serves as the "Single Source of Truth" for the Helix project.

***

# PROJECT SPECIFICATION: HELIX
**Project Code:** HELIX-2025-LOG  
**Version:** 1.0.4-BETA  
**Date:** October 24, 2023  
**Owner:** Emeka Nakamura, Engineering Manager  
**Classification:** Proprietary / Confidential – Stratos Systems  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Helix is a strategic platform modernization effort initiated by Stratos Systems to overhaul the existing IoT device network used in logistics and shipping operations. For the past decade, Stratos has relied on a legacy monolithic architecture that has become a bottleneck for scaling and a liability for maintenance. Helix represents the transition from this monolith to a distributed microservices architecture over an 18-month window, aimed at increasing system resilience, improving data throughput for IoT sensors, and enabling faster feature iteration.

The core objective is to move away from a single, fragile codebase and toward a decoupled system utilizing Hexagonal Architecture. This ensures that the core business logic (the "Domain") remains isolated from external dependencies such as the Oracle database, hardware interfaces, and third-party shipping APIs.

### 1.2 Business Justification
In the current logistics climate, real-time visibility is no longer a luxury but a requirement. The existing monolith suffers from "cascading failures"—where a bug in the PDF reporting module could crash the entire sensor ingestion engine. By decoupling these concerns into microservices, Stratos Systems ensures that critical data ingestion (the primary revenue driver) remains operational even if peripheral features fail.

Furthermore, the industry is shifting toward multi-tenancy. Currently, Stratos manages separate instances for large clients, leading to massive operational overhead. Helix introduces shared infrastructure with strict data isolation, allowing Stratos to onboard new clients in minutes rather than weeks.

### 1.3 ROI Projection
The financial justification for the $800,000 investment is based on three primary levers:
1. **Operational Expenditure (OpEx) Reduction:** By consolidating fragmented instances into a multi-tenant architecture, we expect a 30% reduction in server maintenance costs and a 50% reduction in DevOps man-hours spent on deployment.
2. **Revenue Growth through Scalability:** The ability to handle 10x the current device density per tenant allows Stratos to move up-market to global shipping conglomerates.
3. **Risk Mitigation:** Reducing the "bus factor" and eliminating the monolithic failure points reduces the projected cost of downtime, which is currently estimated at $12,000 per hour of outage.

The projected Break-Even Point (BEP) is 14 months post-launch, with an estimated Year 2 ROI of 215% based on increased client acquisition and decreased churn.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Helix utilizes a Hexagonal Architecture to ensure the business logic is independent of the infrastructure. This is critical given the requirement for an on-premise data center and the use of a specific Oracle DB version.

**The layers are defined as follows:**
- **The Domain (Core):** Contains entities, value objects, and domain services. It has zero dependencies on external frameworks.
- **Ports:** Interfaces that define how the outside world can interact with the domain (Inbound Ports) and how the domain interacts with the outside world (Outbound Ports).
- **Adapters:** Implementations of the ports. (e.g., a `PersistenceAdapter` that implements a `DeviceRepository` port using Oracle SQL).

### 2.2 ASCII Architecture Diagram
```text
[ EXTERNAL WORLD ]          [ ADAPTERS LAYER ]          [ DOMAIN CORE ]
       |                           |                           |
(IoT Device) ----> [ REST Controller / MQTT ] ----> [ Device Service ]
                                   |                           |
(Admin UI)   ----> [ REST API Adapter ] ----------> [ Tenant Manager ]
                                   |                           |
                                   v                           v
                          [ OUTBOUND ADAPTERS ] <--- [ PORT INTERFACES ]
                                   |                           |
                                   +---> [ Oracle DB Adapter ]-+
                                   +---> [ PDF Gen Adapter ]   +
                                   +---> [ Hardware Key Auth ] +
                                   |                           |
                          [ ON-PREMISE INFRASTRUCTURE ] <------+
```

### 2.3 Technology Stack
- **Language:** Java 17 (LTS)
- **Framework:** Spring Boot 3.2.x
- **Database:** Oracle Database 19c (Enterprise Edition)
- **Messaging:** RabbitMQ (Internal on-premise cluster)
- **Deployment:** On-premise Bare Metal / Virtual Machines (No Cloud)
- **CI/CD:** Jenkins (Self-hosted)

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Critical - Launch Blocker)
**Status:** In Design | **Priority:** Critical

**Description:** 
The system must support multiple logistics companies (tenants) on a shared infrastructure while ensuring that no tenant can ever access another tenant's data. This is the foundation of the Helix platform. Given the "shared infrastructure" requirement, we are implementing a **Discriminator Column Approach** (Shared Schema), where every table contains a `tenant_id`.

**Functional Requirements:**
- Every API request must be authenticated and associated with a `tenant_id`.
- The persistence layer must automatically append a `WHERE tenant_id = ?` clause to all queries.
- Administrative users must be able to manage tenant quotas (e.g., max number of devices).
- Data leakage between tenants must be prevented at the service level through the use of a `TenantContext` thread-local variable.

**Technical Implementation:**
We will implement a Spring Security filter that extracts the `X-Tenant-ID` from the header or resolves it via the JWT claims. This ID is then stored in a `TenantContext` holder. A Hibernate `Filter` will be applied globally to all entities extending the `BaseTenantEntity` class.

**Acceptance Criteria:**
- A request with Tenant A's token cannot retrieve data belonging to Tenant B.
- The system supports at least 500 concurrent tenants without performance degradation.
- Database indexes are optimized for `(tenant_id, primary_id)` composite keys.

### 3.2 Advanced Search with Faceted Filtering (High)
**Status:** In Review | **Priority:** High

**Description:**
Users need to locate specific IoT devices across global shipping lanes. A simple keyword search is insufficient. This feature provides full-text indexing and "facets" (filters) based on device status, location, battery level, and shipping company.

**Functional Requirements:**
- Full-text search across device names, serial numbers, and shipment IDs.
- Faceted navigation allowing users to narrow results (e.g., "Show only devices in 'Critical' state in the 'North Atlantic' region").
- Search latency must be under 200ms for datasets up to 1 million records.
- Support for "wildcard" searching (e.g., `SENS-***-2023`).

**Technical Implementation:**
Since cloud-based search (ElasticSearch/Algolia) is prohibited, we will utilize **Oracle Text** for full-text indexing. We will create a materialized view for the faceted counts to avoid expensive `COUNT(*)` queries on the main device table during every search request.

**Acceptance Criteria:**
- Users can filter by at least 5 different dimensions simultaneously.
- Search results are paginated (20 records per page).
- Full-text index updates in near real-time (under 5 seconds from data entry).

### 3.3 Two-Factor Authentication (2FA) with Hardware Keys (Medium)
**Status:** In Design | **Priority:** Medium

**Description:**
To secure high-value logistics data, standard passwords are insufficient. Helix will implement 2FA, specifically prioritizing hardware-based keys (FIDO2/WebAuthn) to prevent phishing attacks.

**Functional Requirements:**
- Users can register multiple FIDO2-compliant hardware keys (e.g., YubiKey).
- Support for fallback methods (TOTP via Google Authenticator).
- Enforced 2FA for users with "Administrator" or "Super-User" roles.
- Audit logging of all 2FA attempts, including failure reasons.

**Technical Implementation:**
Integration of the `webauthn4j` library within the Spring Security flow. The server will challenge the hardware key, and the response will be verified against the stored public key in the `user_security_keys` table.

**Acceptance Criteria:**
- Successful login requires both a password and a hardware key touch.
- Hardware key registration is intuitive and follows the WebAuthn standard.
- Session timeout triggers a re-authentication prompt.

### 3.4 PDF/CSV Report Generation (Medium)
**Status:** In Review | **Priority:** Medium

**Description:**
Logistics managers require periodic reports on fleet health, energy consumption, and delivery timelines. This feature handles the generation and scheduled delivery of these documents.

**Functional Requirements:**
- Generation of PDF summaries and CSV raw data exports.
- Ability to schedule reports (Daily, Weekly, Monthly).
- Delivery via internal email system (SMTP).
- Custom templates for PDF layout.

**Technical Implementation:**
Using **JasperReports** for PDF generation and **OpenCSV** for CSV exports. A Spring Batch job will run as a cron task, querying the Oracle DB for the specified period, generating the file in a temporary secure directory, and emailing it to the tenant's registered contact.

**Acceptance Criteria:**
- Reports are generated within 60 seconds for datasets up to 10,000 rows.
- CSVs are UTF-8 encoded and compatible with Microsoft Excel.
- Scheduled emails are delivered reliably without duplicates.

### 3.5 Data Import/Export with Format Auto-Detection (Low)
**Status:** Blocked | **Priority:** Low

**Description:**
A "nice-to-have" feature allowing users to migrate data from legacy systems by uploading files. The system should automatically detect if the file is JSON, XML, or CSV.

**Functional Requirements:**
- Upload portal for bulk device registration.
- Auto-detection of file MIME type and internal structure.
- Validation of data before commit (Dry-run mode).
- Error report generation for failed rows.

**Technical Implementation:**
Implementation of a `FileAnalyzer` strategy pattern. The system will read the first 1KB of the file to detect markers (e.g., `{` for JSON, `<` for XML, `,` for CSV). Once the format is detected, the corresponding `ImportStrategy` will be invoked to map fields to the `Device` entity.

**Acceptance Criteria:**
- Correctly identifies and parses three different file formats.
- Successfully imports 5,000 records in under 30 seconds.
- Provides a line-by-line error report for malformed data.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests must include the `X-Tenant-ID` header.

### 4.1 Device Management
**1. GET `/devices`**
- **Description:** Retrieve a paginated list of devices for the current tenant.
- **Request Params:** `page` (int), `size` (int), `filter` (string)
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "content": [{ "id": "DEV-101", "status": "ACTIVE", "lastSeen": "2023-10-24T10:00Z" }],
    "totalElements": 150,
    "totalPages": 8
  }
  ```

**2. POST `/devices`**
- **Description:** Register a new IoT device.
- **Request Body:** `{ "serialNumber": "SN-998", "model": "X-100", "region": "EMEA" }`
- **Response:** `201 Created`
- **Example Response:** `{ "id": "DEV-102", "status": "PROVISIONED" }`

**3. PATCH `/devices/{id}`**
- **Description:** Update device metadata.
- **Request Body:** `{ "status": "MAINTENANCE" }`
- **Response:** `200 OK`

### 4.2 Tenant Administration
**4. GET `/tenant/config`**
- **Description:** Get current tenant limits and settings.
- **Response:** `200 OK`
- **Example Response:** `{ "tenantName": "Global Shipping Co", "maxDevices": 5000, "currentUsage": 1200 }`

**5. POST `/tenant/keys/register`**
- **Description:** Register a new hardware security key for 2FA.
- **Request Body:** `{ "challenge": "...", "publicKey": "..." }`
- **Response:** `200 OK`

### 4.3 Reporting & Search
**6. POST `/search/devices`**
- **Description:** Execute a faceted search.
- **Request Body:** `{ "query": "Atlantic", "facets": { "status": ["ACTIVE", "WARN"] } }`
- **Response:** `200 OK`

**7. POST `/reports/generate`**
- **Description:** Trigger an immediate report generation.
- **Request Body:** `{ "type": "PDF", "startDate": "2023-01-01", "endDate": "2023-01-31" }`
- **Response:** `202 Accepted` (Returns a job ID)

**8. GET `/reports/status/{jobId}`**
- **Description:** Check the status of a background report job.
- **Response:** `200 OK`
- **Example Response:** `{ "jobId": "JOB-123", "status": "COMPLETED", "downloadUrl": "/api/v1/reports/download/JOB-123" }`

---

## 5. DATABASE SCHEMA

The database is hosted on Oracle 19c. All tables use `RAW(16)` for UUIDs to optimize storage and indexing.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | None | `name`, `created_at`, `plan_level` | Core tenant metadata. |
| `users` | `user_id` | `tenant_id` | `username`, `email`, `role_id` | System users mapped to tenants. |
| `roles` | `role_id` | None | `role_name`, `permissions_mask` | RBAC role definitions. |
| `devices` | `device_id` | `tenant_id` | `serial_num`, `model_id`, `status` | Registered IoT hardware. |
| `device_models`| `model_id` | None | `model_name`, `manufacturer` | Hardware specifications. |
| `telemetry` | `telemetry_id`| `device_id` | `timestamp`, `payload`, `metric_type`| High-volume sensor data. |
| `security_keys`| `key_id` | `user_id` | `public_key`, `credential_id` | FIDO2 hardware key data. |
| `reports` | `report_id` | `tenant_id` | `report_type`, `generated_at`, `file_path` | History of generated reports. |
| `report_schedules`| `sched_id` | `tenant_id` | `cron_expression`, `recipient_email`| Scheduled delivery logic. |
| `audit_logs` | `log_id` | `user_id` | `action`, `timestamp`, `ip_address` | Security and compliance trail. |

### 5.2 Relationships
- `tenants` $\rightarrow$ `users` (One-to-Many)
- `tenants` $\rightarrow$ `devices` (One-to-Many)
- `users` $\rightarrow$ `security_keys` (One-to-Many)
- `devices` $\rightarrow$ `telemetry` (One-to-Many)
- `tenants` $\rightarrow$ `reports` (One-to-Many)

### 5.3 Indexing Strategy
- Composite index on `devices(tenant_id, status)` for fast faceted filtering.
- Partitioning on `telemetry(timestamp)` by month to ensure query performance as data grows.
- B-Tree index on `users(email)` for fast authentication lookup.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Definitions
Because cloud services are forbidden, all environments are hosted within the Stratos Systems on-premise data center.

**1. Development (DEV):**
- **Hardware:** 2x Virtual Machines (8 vCPU, 32GB RAM).
- **Database:** Single Oracle XE instance.
- **Purpose:** Individual developer testing and feature branch integration.
- **Deployment:** Automated via Jenkins on every commit.

**2. Staging (STG):**
- **Hardware:** 3x Virtual Machines (16 vCPU, 64GB RAM).
- **Database:** Oracle Standard Edition (Mirror of Production schema).
- **Purpose:** Pre-production validation, UAT (User Acceptance Testing), and quarterly regulatory review.
- **Deployment:** Triggered manually by the Project Lead after DEV sign-off.

**3. Production (PROD):**
- **Hardware:** 5x Bare Metal Servers (64 vCPU, 256GB RAM).
- **Database:** Oracle Enterprise Edition (RAC Cluster for High Availability).
- **Purpose:** Live traffic.
- **Deployment:** Quarterly release cycle. Only deployed during maintenance windows.

### 6.2 Release Cycle
Helix follows a strict quarterly release cadence aligned with regulatory review cycles.
- **Week 1-8:** Development and Unit Testing.
- **Week 9-10:** Integration Testing in STG.
- **Week 11:** Regulatory Review and External Audit.
- **Week 12:** Production Deployment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** JUnit 5, Mockito.
- **Requirement:** Minimum 80% line coverage for Domain services.
- **Focus:** Business logic, validation rules, and state transitions. All mocks must be used for external ports.

### 7.2 Integration Testing
- **Tool:** Testcontainers (with Oracle-XE image).
- **Requirement:** All Repository adapters must be tested against a real database instance.
- **Focus:** SQL query correctness, transaction boundaries, and multi-tenant filter verification.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Selenium / Playwright.
- **Requirement:** Critical paths (Login $\rightarrow$ Device Registration $\rightarrow$ Report Generation) must be automated.
- **Focus:** User journeys and cross-service communication (REST $\rightarrow$ RabbitMQ $\rightarrow$ DB).

### 7.4 Penetration Testing
- **Frequency:** Quarterly.
- **Scope:** API vulnerability scanning, SQL injection attempts, and 2FA bypass attempts.
- **Execution:** Conducted by Hiro Costa (Security Engineer) using internal tools and simulated attack vectors.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead in market release. | High | High | Hire a specialized contractor to increase development velocity and reduce "bus factor." | Emeka N. |
| R-02 | Regulatory requirements change mid-build. | Medium | High | Assign a dedicated owner to track regulatory changes weekly and adjust specs. | Farah F. |
| R-03 | Key team member on medical leave (6 weeks). | High | Medium | Redistribute critical tasks among remaining 3 members; prioritize "Critical" features. | Emeka N. |
| R-04 | Technical Debt: 3 different date formats. | High | Low | Implement a normalization layer (ISO-8601) in the adapter layer during migration. | Zia S. |
| R-05 | On-prem hardware failure during launch. | Low | Critical | Implement Oracle RAC and redundant power supplies in the DC. | Zia S. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required (R-01).
- **High/Medium:** Monitor and mitigate (R-03, R-04).
- **Medium/High:** Proactive planning (R-02).
- **Low/Critical:** Contingency planning (R-05).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
**Phase 1: Core Foundation (Months 1-4)**
- Focus: Multi-tenancy, Hexagonal Architecture setup, Oracle DB Schema.
- Dependency: DB hardware provisioning.

**Phase 2: Feature Acceleration (Months 5-8)**
- Focus: Advanced Search, 2FA, and Report Generation.
- Dependency: Completion of the Multi-tenant isolation layer.

**Phase 3: Hardening & Compliance (Months 9-12)**
- Focus: Performance tuning, Pen-testing, Regulatory Audit.
- Dependency: Feature complete MVP.

**Phase 4: Transition & Migration (Months 13-18)**
- Focus: Moving legacy data from monolith to microservices.

### 9.2 Key Milestones
- **Milestone 1: Stakeholder Demo and Sign-off** $\rightarrow$ **Target: 2025-07-15**
- **Milestone 2: MVP Feature-Complete** $\rightarrow$ **Target: 2025-09-15**
- **Milestone 3: Post-launch Stability Confirmed** $\rightarrow$ **Target: 2025-11-15**

---

## 10. MEETING NOTES

*Note: All meetings are recorded via video call. Per team culture, these recordings are archived but rarely re-watched. The following are summarized decisions from the recordings.*

### Meeting 1: Architecture Alignment (2023-11-02)
- **Attendees:** Emeka, Zia, Hiro, Farah.
- **Discussion:** Debate over using a shared database vs. separate schemas for tenants.
- **Decision:** Zia argued that managing 500 separate schemas in Oracle would be a DevOps nightmare. Emeka approved the "Discriminator Column" (Shared Schema) approach with Hibernate Filters for isolation.
- **Action Item:** Zia to create the base entity class with `tenant_id`.

### Meeting 2: 2FA Strategy (2023-12-15)
- **Attendees:** Emeka, Hiro, Farah.
- **Discussion:** Whether to support SMS-based 2FA.
- **Decision:** Hiro strongly opposed SMS due to SIM-swapping risks and the lack of a reliable on-prem SMS gateway. The team decided to support only FIDO2 Hardware Keys and TOTP.
- **Action Item:** Hiro to research `webauthn4j` implementation.

### Meeting 3: The "Date Format" Crisis (2024-01-20)
- **Attendees:** Emeka, Zia, Farah.
- **Discussion:** Discovery that the monolith uses `MM-DD-YYYY`, `YYYY/MM/DD`, and Unix timestamps interchangeably.
- **Decision:** The team decided NOT to do a global find-and-replace (too risky). Instead, they will build a `DateNormalizationAdapter` that converts all incoming legacy dates to ISO-8601 before they hit the Domain layer.
- **Action Item:** Farah to document all known legacy date formats.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000 (6-month intensive build phase)

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $450,000 | 4 Full-time employees for 6 months. |
| **Contractor (Mitigation R-01)** | $120,000 | Senior Java dev to reduce bus factor. |
| **Infrastructure (On-Prem)** | $150,000 | Bare metal servers, Oracle Licenses, Rack space. |
| **Tools & Licenses** | $30,000 | JasperReports Commercial, IDEs, Pen-test tools. |
| **Contingency Fund** | $50,000 | For emergency hardware or regulatory shifts. |

**Total Spent to Date:** $0.00 (Project Initialization Phase)

---

## 12. APPENDICES

### Appendix A: Data Normalization Layer Details
The "Technical Debt" regarding date formats is handled via the following logic in the `PersistenceAdapter`:
1. **Input:** String from legacy system.
2. **Regex Check:** Matches against `^\d{2}-\d{2}-\d{4}$` (US) or `^\d{4}/\d{2}/\d{2}$` (ISO).
3. **Conversion:** All formats are parsed into `java.time.OffsetDateTime`.
4. **Storage:** Stored in Oracle as `TIMESTAMP WITH TIME ZONE`.

### Appendix B: Regulatory Review Checklist
To pass the "External Audit on First Attempt" (Success Criterion 2), the following must be verified:
- [ ] All `tenant_id` filters are applied to every DB query.
- [ ] Audit logs capture the `user_id`, `timestamp`, and `action` for every write operation.
- [ ] 2FA is enforced for all accounts with `ROLE_ADMIN`.
- [ ] Data is encrypted at rest using Oracle Transparent Data Encryption (TDE).
- [ ] Quarterly penetration test report is signed off by Hiro Costa.