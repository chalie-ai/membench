# PROJECT SPECIFICATION: PROJECT UMBRA
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Company:** Coral Reef Solutions  
**Classification:** Internal / Confidential  
**Project Lead:** Yves Nakamura (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project Umbra is a high-stakes strategic initiative by Coral Reef Solutions to enter the healthcare records management sector. Positioned at the intersection of healthcare and cybersecurity, Umbra is designed as a secure, distributed, and highly resilient platform for the storage, retrieval, and auditing of sensitive patient health information (PHI). Unlike generic Electronic Health Record (EHR) systems, Umbra focuses on the *security layer*—providing a tamper-evident, high-performance backbone that ensures data integrity and availability across geographically dispersed nodes.

**Business Justification**  
The catalyst for Project Umbra is a cornerstone partnership with a single enterprise client (Codename: "Titan Health") who has committed to a recurring annual contract of $2,000,000. This provides a guaranteed revenue stream that justifies the initial $3,000,000 investment. By building a product tailored to the extreme requirements of Titan Health, Coral Reef Solutions intends to create a blueprint for a new product vertical, allowing the company to pivot from a pure cybersecurity services provider to a high-margin Software-as-a-Service (SaaS) product company.

**ROI Projection**  
The Return on Investment (ROI) for Project Umbra is calculated over a 36-month window. With an initial capital expenditure (CapEx) of $3M and a guaranteed annual recurring revenue (ARR) of $2M from the primary client, the project reaches a break-even point at Month 18. However, the strategic ROI extends beyond the primary client. By leveraging the "Titan" implementation as a case study, Coral Reef Solutions projects the acquisition of four additional mid-sized healthcare enterprises by Year 3, potentially increasing ARR to $6M–$8M.

**Strategic Objectives**  
The primary objective is the delivery of a production-ready platform by December 15, 2026. The platform must maintain a p95 response time of under 200ms to meet the high-frequency demands of clinical environments. Furthermore, given the industry, "Zero Critical Security Incidents" in the first year of operation is a non-negotiable success criterion. The project is managed by a distributed team of 15 experts across five countries, utilizing a remote-first, asynchronous communication model to maximize productivity across time zones.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design Philosophy
Umbra is built on a **Microservices Architecture** utilizing **Go (Golang)** for high-concurrency performance and low latency. To manage the complexity of healthcare data—where history and lineage are as important as the current state—the platform implements **CQRS (Command Query Responsibility Segregation)** combined with **Event Sourcing**.

In this model, the "Write" side (Command) captures every change as an immutable event in an Event Store, while the "Read" side (Query) projects these events into optimized views for fast retrieval. This is critical for the audit-critical domains of the platform, ensuring that no record is ever truly "overwritten," only appended.

### 2.2 Technology Stack
- **Language:** Go 1.22+ (Standard library + gRPC-go)
- **Communication:** gRPC for inter-service communication; REST/JSON for external API gateways.
- **Database:** CockroachDB (Distributed SQL) for global consistency and survival of regional failures.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
- **Event Bus:** NATS JetStream for event sourcing and asynchronous messaging.
- **Caching:** Redis 7.0 for session management and rate-limit counters.

### 2.3 ASCII Architecture Diagram
```text
[ Client Applications ]  --> [ GCP Global Load Balancer ]
                                     |
                                     v
                          [ API Gateway / Envoy Proxy ]
                                     |
          ___________________________|___________________________
         |                           |                            |
 [ Rate Limit Service ]    [ Patient Record Service ]    [ Audit Log Service ]
 (Redis Backend)           (CQRS / Go / gRPC)            (Event Store / Go)
         |                           |                            |
         |___________________________|____________________________|
                                     |
                          [ CockroachDB Cluster ]
                          (Multi-Region Deployment)
                                     |
                          [ GCS Bucket - Backups ]
```

### 2.4 Data Flow: Command vs. Query
1. **Command Path:** A request to update a record arrives $\rightarrow$ API Gateway $\rightarrow$ Record Service $\rightarrow$ Validation $\rightarrow$ Event Store (CockroachDB) $\rightarrow$ Event Published to NATS $\rightarrow$ Success Response.
2. **Query Path:** A request to view a record arrives $\rightarrow$ API Gateway $\rightarrow$ Read Model (Optimized Table) $\rightarrow$ Response.
3. **Projection:** An asynchronous worker listens to NATS events and updates the Read Model in real-time.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Functional Description:**  
To prevent Denial-of-Service (DoS) attacks and ensure fair resource allocation among multi-tenant users, Umbra requires a sophisticated rate-limiting engine. This system must handle "bursty" healthcare traffic patterns where a clinic might synchronize thousands of records in a short window.

**Technical Specifications:**  
The system will implement a **Generic Cell Rate Algorithm (GCRA)** using Redis as the central state store. Every incoming request will be keyed by `API_KEY` and `ENDPOINT_PATH`. 
- **Tiers:** Three tiers of service (Basic: 100 req/min, Pro: 1,000 req/min, Enterprise: 10,000 req/min).
- **Analytics:** Every request, whether allowed or throttled, must be logged to an analytics pipeline (BigQuery) to track usage trends.

**Requirements:**
- Must support "sliding window" counters to prevent edge-of-window spikes.
- Must return HTTP 429 (Too Many Requests) with a `Retry-After` header.
- Analytics must provide a dashboard showing top 10 most active users and most throttled endpoints.

### 3.2 Localization and Internationalization (L10n/I18n)
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Functional Description:**  
To support global expansion, the platform must support 12 languages, including English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Portuguese, Hindi, Russian, and Italian.

**Technical Specifications:**  
Umbra will use the `golang.org/x/text` package for localization. All user-facing strings must be extracted into JSON translation files stored in a centralized localization repository.
- **Detection:** The system will determine the language via the `Accept-Language` HTTP header or a user-profile preference.
- **Dynamic Content:** Support for Right-to-Left (RTL) layouts for Arabic.
- **Date/Currency:** Use the CLDR (Common Locale Data Repository) standard for formatting dates and medical units of measure.

**Requirements:**
- Translation files must be hot-reloadable without requiring a pod restart in Kubernetes.
- Support for UTF-8 encoding across all database fields.

### 3.3 Advanced Search with Faceted Filtering
**Priority:** Low (Nice to Have) | **Status:** Complete

**Functional Description:**  
Users must be able to locate specific healthcare records across millions of entries using complex criteria (e.g., "All patients aged 40-60 with Type 2 Diabetes in the New York region").

**Technical Specifications:**  
This feature utilizes a full-text index implemented via a specialized index in CockroachDB and an auxiliary Elasticsearch cluster for complex tokenization.
- **Faceted Filtering:** The API returns "facets" (counts of records per category) allowing users to drill down.
- **Full-Text Indexing:** Implementation of "fuzzy search" to account for medical terminology misspellings.

**Requirements:**
- Query latency for filtered searches must remain under 500ms for datasets up to 10M records.
- Support for boolean operators (AND, OR, NOT) in the search query string.

### 3.4 Notification System
**Priority:** Low (Nice to Have) | **Status:** In Progress

**Functional Description:**  
An omni-channel notification engine to alert healthcare providers of critical record updates, system alerts, or security breaches.

**Technical Specifications:**  
A dedicated `Notification Service` will act as a dispatcher. It consumes events from the NATS bus and routes them to specific providers.
- **Email:** Integration via SendGrid.
- **SMS:** Integration via Twilio.
- **In-App:** WebSocket connections via a Go-based Hub.
- **Push:** Firebase Cloud Messaging (FCM).

**Requirements:**
- Notification preferences must be granular (e.g., "Email for critical, Push for info").
- A "Retry Queue" must be implemented to handle transient provider failures (Exponential Backoff).

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Blocked

**Functional Description:**  
Given the cybersecurity nature of the project, every single read or write operation on a healthcare record must be logged in a way that cannot be altered, even by a database administrator.

**Technical Specifications:**  
The system will implement a **Merkle Tree-based hashing mechanism**. Each audit log entry will contain a hash of the previous entry, creating a cryptographic chain.
- **Storage:** Logs are stored in a dedicated CockroachDB table with `READ-ONLY` permissions for the application service; only a specialized "Audit Writer" service can append.
- **Verification:** A daily job will recalculate the hashes to ensure no records have been deleted or modified (Tamper Detection).

**Requirements:**
- Storage must be immutable (Write-Once-Read-Many).
- Blocked by: Infrastructure provisioning delay; the dedicated secure storage volume in GCP is not yet available.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the `/api/v1/` prefix. All requests and responses use `application/json`.

### 4.1 `GET /api/v1/records/{patient_id}`
**Description:** Retrieves the current state of a patient's healthcare record.
- **Request:** `GET /api/v1/records/PAT-9901`
- **Response (200 OK):**
```json
{
  "patient_id": "PAT-9901",
  "last_updated": "2026-01-12T14:20:00Z",
  "data": {
    "blood_type": "O+",
    "allergies": ["Penicillin", "Peanuts"],
    "current_medications": ["Lisinopril"]
  },
  "version": 42
}
```

### 4.2 `POST /api/v1/records/{patient_id}`
**Description:** Updates a patient record (Command).
- **Request:** `POST /api/v1/records/PAT-9901`
- **Body:**
```json
{
  "update_type": "MEDICATION_CHANGE",
  "change_set": { "current_medications": ["Lisinopril", "Metformin"] },
  "clinician_id": "DOC-442"
}
```
- **Response (202 Accepted):** `{"status": "processing", "event_id": "evt_8821"}`

### 4.3 `GET /api/v1/audit/trail/{patient_id}`
**Description:** Retrieves the full history of changes for a specific patient.
- **Request:** `GET /api/v1/audit/trail/PAT-9901`
- **Response (200 OK):**
```json
[
  { "version": 1, "timestamp": "2025-01-01", "action": "CREATE", "hash": "0xabc123..." },
  { "version": 2, "timestamp": "2025-02-10", "action": "UPDATE", "hash": "0xdef456..." }
]
```

### 4.4 `GET /api/v1/search`
**Description:** Faceted search across the record database.
- **Request:** `GET /api/v1/search?q=diabetes&age_min=40&region=east`
- **Response (200 OK):**
```json
{
  "results": [ { "patient_id": "PAT-123", "score": 0.98 } ],
  "facets": { "region": { "east": 450, "west": 300 }, "age_group": { "40-50": 120 } }
}
```

### 4.5 `POST /api/v1/notifications/settings`
**Description:** Updates a user's notification preferences.
- **Request:** `POST /api/v1/notifications/settings`
- **Body:** `{"user_id": "USR-11", "channel": "SMS", "enabled": true}`
- **Response (200 OK):** `{"status": "updated"}`

### 4.6 `GET /api/v1/usage/analytics`
**Description:** Retrieves API usage statistics for the current account.
- **Request:** `GET /api/v1/usage/analytics?period=last_30_days`
- **Response (200 OK):**
```json
{
  "total_requests": 150000,
  "throttled_requests": 1200,
  "p95_latency": "185ms"
}
```

### 4.7 `DELETE /api/v1/records/{patient_id}`
**Description:** Marks a record for deletion (Soft delete via event).
- **Request:** `DELETE /api/v1/records/PAT-9901`
- **Response (204 No Content):** `Empty Body`

### 4.8 `GET /api/v1/health`
**Description:** Liveness and readiness probe for Kubernetes.
- **Request:** `GET /api/v1/health`
- **Response (200 OK):** `{"status": "healthy", "db": "connected", "nats": "connected"}`

---

## 5. DATABASE SCHEMA

The database is implemented in **CockroachDB**. We use a mix of relational tables and JSONB columns for flexible medical data.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID) | `email`, `password_hash`, `role` | 1:N `api_keys` | Auth and User Mgmt |
| `api_keys` | `key_id` (UUID) | `hashed_key`, `tier_id` | N:1 `users` | Rate limiting lookup |
| `tiers` | `tier_id` (INT) | `tier_name`, `req_per_min` | 1:N `api_keys` | Rate limit definitions |
| `patients` | `patient_id` (UUID) | `external_id`, `created_at` | 1:N `record_events` | Patient Registry |
| `record_events` | `event_id` (UUID) | `patient_id`, `payload`, `version` | N:1 `patients` | Event Store (Write Side) |
| `record_snapshots` | `snap_id` (UUID) | `patient_id`, `current_data` | N:1 `patients` | Read Model (Query Side) |
| `audit_logs` | `log_id` (BIGINT) | `patient_id`, `prev_hash`, `hash` | N:1 `patients` | Tamper-evident log |
| `notifications` | `notif_id` (UUID) | `user_id`, `channel`, `status` | N:1 `users` | Delivery Tracking |
| `search_index` | `idx_id` (UUID) | `patient_id`, `tokens` | N:1 `patients` | Optimized Search |
| `system_configs` | `cfg_key` (STR) | `cfg_value`, `updated_at` | N/A | Global App Settings |

### 5.2 Schema Relationships and Constraints
- **Event Sourcing Constraint:** The `record_events` table is strictly append-only. Any "update" creates a new row with an incremented `version` number.
- **Referential Integrity:** Foreign keys are enforced between `users` and `api_keys` to ensure that key deletion immediately revokes access.
- **Indexing:** A GIN (Generalized Inverted Index) is applied to the `current_data` JSONB column in `record_snapshots` to support high-speed filtering.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Umbra employs three distinct environments to ensure stability and safety.

**1. Development (Dev)**
- **Purpose:** Feature development and initial integration.
- **Infrastructure:** Single-node Kubernetes cluster in GCP.
- **Database:** Small CockroachDB instance.
- **Deploy Cycle:** Continuous Deployment (CD) on every merge to `develop` branch.

**2. Staging (Staging)**
- **Purpose:** Pre-production validation, QA testing, and Security Audits.
- **Infrastructure:** Mirror of Production (Multi-region GKE).
- **Database:** Fully replicated CockroachDB cluster.
- **Deploy Cycle:** Weekly release train (see Section 6.2).

**3. Production (Prod)**
- **Purpose:** Live traffic for Titan Health.
- **Infrastructure:** Highly available, multi-zone GKE cluster across three GCP regions.
- **Database:** CockroachDB with 3-way replication and regional survival goals.
- **Deploy Cycle:** Weekly release train.

### 6.2 The Release Train
The project strictly adheres to a **Weekly Release Train**.
- **Cut-off:** Wednesday 23:59 UTC.
- **Deployment:** Thursday 02:00 UTC.
- **Rule:** No hotfixes are permitted outside the train. If a bug is discovered, it is queued for the next train unless it is a "Site Down" (P0) emergency, which requires approval from Yves Nakamura and the CTO.

### 6.3 Infrastructure Provisioning (Current State)
Currently, the project is facing a **blocker**: the cloud provider has delayed the provisioning of the specialized `Secure-SSD` volumes required for the Audit Trail's tamper-evident storage. Until these are available, the Audit Service is running in a "mocked" state in Dev/Staging.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (Layer 1)
- **Approach:** Every Go package must have a corresponding `_test.go` file.
- **Requirement:** Minimum 80% code coverage.
- **Focus:** Business logic, gRPC request validation, and data transformation.
- **Tooling:** `go test`, `stretchr/testify`.

### 7.2 Integration Testing (Layer 2)
- **Approach:** Test the interaction between microservices and the database.
- **Requirement:** Use **Testcontainers** to spin up actual CockroachDB and NATS instances during the CI pipeline.
- **Focus:** Event propagation from `record_events` $\rightarrow$ `record_snapshots` and API gateway routing.

### 7.3 End-to-End (E2E) Testing (Layer 3)
- **Approach:** Black-box testing of the entire system via the API Gateway.
- **Requirement:** Suite of 50 critical "Golden Path" scenarios (e.g., User creates account $\rightarrow$ Updates record $\rightarrow$ Searches record $\rightarrow$ Verifies Audit Log).
- **Tooling:** Postman/Newman integrated into the Jenkins pipeline.

### 7.4 Performance Testing
- **Load Testing:** Using **k6**, simulate 10,000 concurrent users to verify p95 response times under 200ms.
- **Stress Testing:** Pushing the system until failure to identify the breaking point of the gRPC load balancer.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Budget cut by 30% in next fiscal quarter | Medium | High | **Parallel-Path:** Prototype a "Lite" version of the architecture using a simpler Postgres setup instead of CockroachDB to reduce costs. |
| **R-02** | Project sponsor rotates out of their role | High | Medium | **Independent Assessment:** Engage an external consultant to validate project progress and value, ensuring the new sponsor inherits a "winning" project. |
| **R-03** | Cloud provisioning delay (Current Blocker) | High | High | Shift focus to the Notification and Search features while the infrastructure team escalates with GCP support. |
| **R-04** | Dangerous Migrations (Technical Debt) | Medium | High | **Audit SQL:** 30% of queries bypass the ORM for performance. All raw SQL must be peer-reviewed by two senior devs before migration. |

**Probability/Impact Matrix:**
- **High/High:** Immediate Action Required (R-03)
- **Med/High:** Active Monitoring (R-01, R-04)
- **High/Med:** Management Intervention (R-02)

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown

**Phase 1: Foundation & Core Services (Current - 2026-05)**
- Setup GKE Cluster $\rightarrow$ Implement gRPC Framework $\rightarrow$ Establish CockroachDB Schema.
- *Dependency:* Cloud provider provisioning of SSD volumes.

**Phase 2: Security & Audit Hardening (2026-05 - 2026-08)**
- Finalize Tamper-Evident Storage $\rightarrow$ Implementation of Rate Limiting $\rightarrow$ Internal Security Audit.
- **Milestone 1: Security Audit Passed (Target: 2026-08-15)**

**Phase 3: Beta & User Validation (2026-08 - 2026-10)**
- Deploy to Staging $\rightarrow$ Onboard 10 pilot users $\rightarrow$ Collect feedback on Search and Notifications.
- **Milestone 2: External Beta with 10 Pilot Users (Target: 2026-10-15)**

**Phase 4: Production Readiness (2026-10 - 2026-12)**
- Final Load Testing $\rightarrow$ Disaster Recovery Drills $\rightarrow$ Cut-over to Production.
- **Milestone 3: Production Launch (Target: 2026-12-15)**

---

## 10. MEETING NOTES (SLACK THREAD ARCHIVE)

As per the project's "no formal notes" policy, the following summaries are distilled from Slack threads.

### Thread: `#umbra-eng-sync` (2025-11-12)
**Topic:** Raw SQL vs. ORM Performance
- **Kaia Liu:** "We're seeing 300ms latency on the patient history query. The ORM is generating 12 joins. I'm proposing we bypass it and write raw SQL for this specific endpoint."
- **Yves Nakamura:** "Agreed, but we need to document this. If we change the schema in CockroachDB, these raw queries will break silently. Let's create a `raw_sql_registry.md` file."
- **Decision:** Bypass ORM for performance-critical reads; maintain a registry of raw SQL queries to avoid migration disasters.

### Thread: `#umbra-infra-blockers` (2025-12-05)
**Topic:** GCP Provisioning Delay
- **Kaia Liu:** "Still no word from GCP on the Secure-SSD volumes for the Audit Trail. The ticket has been open for 14 days."
- **Elif Jensen:** "This is blocking QA for the audit feature. Can we mock the storage using standard disks for now?"
- **Yves Nakamura:** "Yes, mock it in Dev/Staging. We cannot delay the rest of the sprint. I'll escalate to the account manager tomorrow."
- **Decision:** Implement a Mock Storage Provider for the Audit Trail to allow QA to proceed.

### Thread: `#umbra-product-roadmap` (2026-01-20)
**Topic:** Budget Risk and Parallel Pathing
- **Yves Nakamura:** "Heard rumors that the next fiscal quarter budget might be slashed by 30%. We need a Plan B."
- **Jules Kim:** "What does Plan B look like?"
- **Yves Nakamura:** "We keep the current high-spec architecture but start a parallel prototype using a single-region Postgres setup. If the budget is cut, we pivot to the Lite version."
- **Decision:** Initiate a "Lite" prototype concurrently with the primary build to mitigate financial risk.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 15 engineers/QA/Support over 18 months. |
| **Infrastructure** | 20% | $600,000 | GKE, CockroachDB Cloud, Redis, NATS, GCP Egress. |
| **Tools & Licenses** | 5% | $150,000 | SendGrid, Twilio, Datadog, Snyk, GitHub Enterprise. |
| **Contingency** | 10% | $300,000 | Reserve for emergency scaling or external consultants. |

**Financial Note:** The $2M annual payment from Titan Health is intended to offset these costs starting in the first year of production.

---

## 12. APPENDICES

### Appendix A: gRPC Service Definitions (.proto)
The core of Umbra's communication is defined by Protocol Buffers. Example for the Record Service:
```protobuf
syntax = "proto3";
package umbra.records;

service RecordService {
  rpc GetPatientRecord(PatientRequest) returns (PatientResponse);
  rpc UpdatePatientRecord(UpdateRequest) returns (UpdateResponse);
}

message PatientRequest {
  string patient_id = 1;
  string request_token = 2;
}

message PatientResponse {
  string patient_id = 1;
  bytes data = 2; // JSON encoded
  int32 version = 3;
}
```

### Appendix B: Disaster Recovery Plan (DRP)
In the event of a total regional failure in GCP:
1. **Detection:** Health checks on the Global Load Balancer will fail for the primary region.
2. **Failover:** Traffic is automatically routed to the secondary region via the GCP Load Balancer.
3. **Data Integrity:** CockroachDB's consensus mechanism (Raft) ensures that as long as 2 out of 3 regions are active, no data is lost and the database remains writable.
4. **Recovery Time Objective (RTO):** < 30 seconds for traffic redirection.
5. **Recovery Point Objective (RPO):** 0 seconds (Zero data loss due to synchronous replication).