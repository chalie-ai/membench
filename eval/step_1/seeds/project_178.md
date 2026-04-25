# PROJECT SPECIFICATION: PROJECT GANTRY
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Owner:** Tundra Analytics  
**Project Lead:** Nyla Stein (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Gantry is a comprehensive platform modernization effort undertaken by Tundra Analytics. The primary objective is to transition the existing legacy monolithic architecture—which has served the company’s educational collaboration tools for several years—into a distributed microservices architecture. This transition is slated for an 18-month delivery cycle, aimed at improving scalability, developer velocity, and system resilience. 

Gantry is not merely a refactor but a strategic pivot toward a "cloud-native" posture. By leveraging Go, gRPC, and CockroachDB, Tundra Analytics seeks to eliminate the "single point of failure" inherent in the monolith and enable independent scaling of high-traffic educational tools, such as real-time collaborative whiteboards and shared document editors.

### 1.2 Business Justification
The legacy system has reached a "critical mass" of technical debt. Deployment cycles are currently monthly, fraught with risk, and require manual intervention. In the education sector, where seasonal spikes (e.g., the start of a semester) create massive fluctuations in load, the monolith's inability to scale specific components independently has led to unacceptable latency and occasional downtime during peak enrollment periods.

Furthermore, as Tundra Analytics expands its footprint, the necessity for HIPAA compliance has become non-negotiable to enter the healthcare-education crossover market (medical school training platforms). The current monolith lacks the granular encryption and audit capabilities required for such certification. Project Gantry implements these security requirements at the infrastructure level.

### 1.3 ROI Projection
The financial and operational return on investment for Project Gantry is projected across three primary vectors:

1.  **Infrastructure Cost Reduction:** By moving to a Kubernetes-based orchestration on GCP and utilizing CockroachDB for optimized data distribution, Tundra Analytics projects a **35% reduction in cost per transaction**. The legacy system over-provisions resources to handle peak loads; Gantry will utilize horizontal pod autoscaling (HPA) to scale only the services under pressure.
2.  **Developer Velocity:** The move to a micro-frontend architecture allows independent teams to deploy features without waiting for a global release cycle. We project a 40% increase in "feature-to-production" speed.
3.  **Market Expansion:** Attaining HIPAA compliance unlocks a projected $1.2M in new annual recurring revenue (ARR) from the specialized medical education market.

With a modest budget of $400,000, the ROI is expected to break even within 14 months post-launch, driven primarily by the reduction in operational overhead and the acquisition of high-value institutional clients.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Philosophy
Gantry adopts a "Shared-Nothing" architecture where services communicate via gRPC for low-latency, typed internal communication. The frontend is decoupled into a micro-frontend (MFE) architecture, where the "Shell" application dynamically loads remote modules. This ensures that the "Reporting" team can deploy updates to the PDF generator without affecting the "Collaboration" team’s whiteboard service.

### 2.2 Technology Stack
- **Backend:** Go (Golang) 1.21+ for all microservices due to its concurrency model and efficient memory management.
- **Communication:** gRPC for inter-service communication; REST/JSON for external client-facing APIs.
- **Database:** CockroachDB (Distributed SQL) to ensure strong consistency and high availability across GCP regions.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
- **Frontend:** React with Module Federation for micro-frontend implementation.
- **Security:** TLS 1.3 for transit; AES-256 for data at rest; HIPAA-compliant IAM roles.

### 2.3 Architecture Diagram (ASCII)

```text
[ User Browser / Client ] 
          |
          v
    [ GCP Cloud Load Balancer ]
          |
          +-----> [ API Gateway / BFF ] (Auth, Rate Limiting, Routing)
                        |
                        | (gRPC / Protobuf)
                        v
    +-------------------+-------------------+-------------------+
    |                   |                   |                   |
[ Auth Service ]   [ Collab Service ]   [ Report Service ]   [ Audit Service ]
    |                   |                   |                   |
    +-------------------+-------------------+-------------------+
                        |
                        v
              [ CockroachDB Cluster ] 
              (Multi-Region Deployment)
              /         |          \
     [ Node US-East ] [ Node US-West ] [ Node EU-West ]
```

### 2.4 Deployment Strategy
Gantry utilizes a strict **Weekly Release Train**. Every Wednesday at 10:00 AM UTC, all merged and tested code is promoted to production. 
- **No Hotfixes:** To maintain stability, hotfixes are prohibited outside the release train unless a "Severity 1" (Total Outage) event occurs.
- **Canary Deployments:** New services are rolled out to 5% of traffic initially, monitored for 2 hours, and then scaled to 100%.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging (Priority: Medium | Status: In Design)
**Description:** 
The Audit Trail system must capture every state-changing action within the Gantry platform. Because the tool is used in educational environments with strict compliance needs, the logs must be "tamper-evident." This means that once a log is written, it cannot be altered or deleted without leaving a detectable trace.

**Functional Requirements:**
- Every API request that modifies data (POST, PUT, DELETE, PATCH) must trigger an audit event.
- The event must capture: UserID, Timestamp (UTC), Action, Previous State (JSON), New State (JSON), and IP Address.
- **Tamper-Evidence:** Logs will be stored using a cryptographic chain (Hash-chaining). Each log entry will contain the SHA-256 hash of the previous entry, ensuring that any deletion or modification of a historical record breaks the chain.
- Logs must be stored in a separate, read-only CockroachDB bucket with strict IAM policies.

**Technical Implementation:**
The `AuditService` will act as a gRPC listener. Other services will push events to a Kafka topic, which the `AuditService` consumes asynchronously to avoid blocking the main request path. To ensure HIPAA compliance, PII (Personally Identifiable Information) within the logs will be encrypted using a rotation-based key management system (GCP KMS).

**Success Metric:** 100% of state-changing operations are logged; audit verification tool can detect a single-bit change in the log history.

---

### 3.2 A/B Testing Framework (Priority: Medium | Status: In Review)
**Description:** 
Instead of building a separate tool, the A/B testing framework is integrated directly into the existing feature flag system. This allows the product team to toggle features for specific cohorts of users without redeploying code.

**Functional Requirements:**
- **Cohort Definition:** Ability to define users based on attributes (e.g., "Institution = University of X", "Role = Professor").
- **Traffic Splitting:** Ability to assign a percentage of users to "Variant A" (Control) or "Variant B" (Experimental).
- **Metric Tracking:** Integration with the analytics engine to track conversion rates or engagement levels for each variant.
- **Dynamic Toggle:** Changes to flag assignments must propagate to the client within 60 seconds without requiring a page refresh.

**Technical Implementation:**
The framework uses a `FlagService` implemented in Go. When a client requests a feature state, the service calculates the bucket using a deterministic hash of the `UserID + FeatureID`. This ensures that a user stays in the same variant across sessions. The configurations are stored in a Redis cache for millisecond retrieval, with CockroachDB as the source of truth.

**Success Metric:** Ability to launch a new feature variant to 10% of users and track the delta in engagement with < 50ms overhead on request latency.

---

### 3.3 PDF/CSV Report Generation (Priority: High | Status: In Review)
**Description:** 
Education administrators require periodic reports on student collaboration and progress. Gantry must generate high-fidelity PDF and CSV reports based on filtered data sets and deliver them via scheduled emails or direct download.

**Functional Requirements:**
- **Templating:** Support for custom HTML/CSS templates that are converted to PDF using a headless Chrome instance (Puppeteer).
- **Scheduled Delivery:** A cron-like scheduler allowing users to set reports for "Weekly," "Monthly," or "Custom" intervals.
- **Data Filtering:** Reports must support the same faceted filtering used in the advanced search (e.g., "All students in Grade 10 who contributed > 50 edits").
- **Asynchronous Processing:** Since PDF generation is resource-intensive, requests must be queued. Users receive a notification when the report is ready.

**Technical Implementation:**
A dedicated `ReportService` will be deployed. It will utilize a worker pool pattern. When a report is requested, a job is placed in a priority queue. A worker picks up the job, queries the necessary microservices for data, generates the file, uploads it to a signed Google Cloud Storage (GCS) bucket, and sends a notification via the `NotificationService`.

**Success Metric:** Generation of a 100-page PDF report in under 30 seconds; 0% failure rate for scheduled deliveries.

---

### 3.4 API Rate Limiting & Usage Analytics (Priority: Medium | Status: Blocked)
**Description:** 
To prevent API abuse and provide a basis for "Tiered Pricing" (e.g., Basic vs. Premium education licenses), Gantry requires a robust rate-limiting mechanism and a way to track API usage per tenant.

**Functional Requirements:**
- **Tiered Limits:** Support for different limits based on the API key (e.g., 1,000 requests/hour for Basic, 10,000 for Premium).
- **Sliding Window Algorithm:** Implementation of a sliding window log to prevent "bursting" at the edge of a minute/hour.
- **Usage Dashboard:** A view for administrators to see their current quota consumption.
- **HTTP 429 Handling:** Standardized "Too Many Requests" response with a `Retry-After` header.

**Technical Implementation:**
Rate limiting will be implemented at the API Gateway level using a Redis-based counter. Each request will check the `tenant_id` against the current count in Redis. Usage analytics will be streamed via gRPC to an `AnalyticsService` which aggregates the data into a time-series format in CockroachDB.

**Success Metric:** Successful blocking of requests exceeding the quota with < 5ms latency added to the request pipeline.

---

### 3.5 Advanced Search with Faceted Filtering (Priority: Low | Status: Blocked)
**Description:** 
Users need to find specific collaborations or documents across thousands of entries. The search must support full-text indexing and the ability to "drill down" using facets (e.g., Date, Subject, User, Status).

**Functional Requirements:**
- **Full-Text Search:** Support for fuzzy matching, stemming, and stop-word removal.
- **Faceted Navigation:** Dynamic count of results per category (e.g., "Math (42), Science (12)").
- **Indexing:** Near real-time indexing of new documents (latency < 5 seconds).
- **Complex Queries:** Ability to combine Boolean operators (AND, OR, NOT).

**Technical Implementation:**
Because CockroachDB is not optimized for full-text search at scale, Gantry will implement an inverted index using an ElasticSearch or Meilisearch cluster. The `SearchService` will listen to database Change Data Capture (CDC) events from CockroachDB and update the search index asynchronously.

**Success Metric:** Search results returned in < 200ms for a dataset of 1 million documents.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 Authentication & Authorization
**`POST /auth/login`**
- **Description:** Authenticates user and returns a JWT.
- **Request:** `{"email": "user@tundra.edu", "password": "hashed_password"}`
- **Response:** `{"token": "jwt_string", "expires_at": "2025-07-20T12:00:00Z"}`

**`GET /auth/session`**
- **Description:** Validates current session.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `{"user_id": "uid_123", "role": "admin", "tenant_id": "tid_456"}`

### 4.2 Collaboration Services
**`POST /collab/document`**
- **Description:** Creates a new real-time collaborative document.
- **Request:** `{"title": "Semester Project", "visibility": "private", "members": ["uid_1", "uid_2"]}`
- **Response:** `{"doc_id": "doc_999", "url": "/docs/doc_999"}`

**`PATCH /collab/document/{id}`**
- **Description:** Updates document metadata.
- **Request:** `{"title": "Updated Semester Project"}`
- **Response:** `{"status": "success", "updated_at": "2025-07-16T10:00:00Z"}`

### 4.3 Reporting & Analytics
**`POST /reports/generate`**
- **Description:** Triggers an asynchronous report generation.
- **Request:** `{"type": "pdf", "filter": {"date_range": "last_30_days", "subject": "Biology"}}`
- **Response:** `{"job_id": "job_abc_123", "status": "queued", "eta": "45s"}`

**`GET /reports/status/{job_id}`**
- **Description:** Checks the status of a report job.
- **Request:** `job_id` in path.
- **Response:** `{"status": "completed", "download_url": "https://storage.gcp.com/signed-url"}`

### 4.4 Audit & System
**`GET /audit/logs`**
- **Description:** Retrieves audit logs for a specific resource.
- **Request:** `{"resource_id": "doc_999", "start_date": "2025-01-01"}`
- **Response:** `[{"event_id": "evt_1", "action": "UPDATE", "user": "uid_123", "hash": "sha256..."}]`

**`GET /system/quota`**
- **Description:** Returns current API usage for the tenant.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `{"limit": 10000, "used": 4500, "remaining": 5500, "reset_at": "2025-07-17T00:00:00Z"}`

---

## 5. DATABASE SCHEMA

The system utilizes CockroachDB for distributed SQL capabilities. All primary keys are `UUID` to prevent collisions across nodes.

### 5.1 Table Definitions

1.  **`tenants`**: The top-level entity (e.g., a school or university).
    - `tenant_id` (UUID, PK)
    - `name` (String)
    - `subscription_tier` (Enum: Basic, Premium, Enterprise)
    - `created_at` (Timestamp)

2.  **`users`**: Individual users linked to a tenant.
    - `user_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `email` (String, Unique)
    - `password_hash` (String)
    - `role` (Enum: Admin, Teacher, Student)

3.  **`documents`**: Collaborative files.
    - `doc_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `title` (String)
    - `content_ref` (String) - Pointer to blob storage.
    - `created_by` (UUID, FK -> users)

4.  **`document_members`**: Mapping of users to documents.
    - `doc_id` (UUID, FK -> documents)
    - `user_id` (UUID, FK -> users)
    - `permission_level` (Enum: Read, Edit, Owner)
    - `joined_at` (Timestamp)

5.  **`audit_logs`**: Tamper-evident log chain.
    - `log_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `user_id` (UUID, FK -> users)
    - `action` (String)
    - `payload_before` (JSONB)
    - `payload_after` (JSONB)
    - `prev_hash` (String) - Hash of the previous record.
    - `current_hash` (String) - SHA-256 of this record + prev_hash.

6.  **`feature_flags`**: Definitions of A/B tests.
    - `flag_id` (UUID, PK)
    - `key` (String, Unique)
    - `description` (String)
    - `is_enabled` (Boolean)

7.  **`flag_variants`**: Specific variants for A/B testing.
    - `variant_id` (UUID, PK)
    - `flag_id` (UUID, FK -> feature_flags)
    - `variant_name` (String)
    - `weight` (Integer) - Percentage of traffic.

8.  **`report_jobs`**: Tracking for PDF/CSV generation.
    - `job_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `user_id` (UUID, FK -> users)
    - `status` (Enum: Queued, Processing, Completed, Failed)
    - `file_url` (String)

9.  **`usage_metrics`**: Aggregated API usage.
    - `metric_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `endpoint` (String)
    - `request_count` (BigInt)
    - `window_start` (Timestamp)

10. **`schedules`**: Recurring report triggers.
    - `schedule_id` (UUID, PK)
    - `tenant_id` (UUID, FK -> tenants)
    - `cron_expression` (String)
    - `report_config` (JSONB)

### 5.2 Relationships
- `tenants` (1 : N) $\rightarrow$ `users`
- `tenants` (1 : N) $\rightarrow$ `documents`
- `documents` (1 : N) $\rightarrow$ `document_members`
- `users` (1 : N) $\rightarrow$ `audit_logs`
- `feature_flags` (1 : N) $\rightarrow$ `flag_variants`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Gantry utilizes three distinct environments to ensure stability.

| Environment | Purpose | Deployment Trigger | Data Source |
| :--- | :--- | :--- | :--- |
| **Development** | Feature work & Unit testing | Every commit to `feat/*` branch | Mock/Seed Data |
| **Staging** | QA, Integration & UAT | Merge to `develop` branch | Sanitized Prod Snapshot |
| **Production** | End-user traffic | Weekly Release Train (Wed 10am) | Live Production DB |

### 6.2 Infrastructure Components
- **Kubernetes (GKE):**
    - **Cluster:** Regional cluster across 3 zones for high availability.
    - **Namespace:** Segregated by service (`auth-ns`, `collab-ns`, `report-ns`).
    - **HPA:** Horizontal Pod Autoscalers configured to trigger at 70% CPU utilization.
- **Networking:**
    - **Ingress:** Google Cloud Load Balancer with SSL termination.
    - **Service Mesh:** Istio for mTLS (mutual TLS) between all microservices, ensuring HIPAA compliance for data-in-transit.
- **Storage:**
    - **CockroachDB:** 3-node cluster with multi-region replication.
    - **GCS (Google Cloud Storage):** Used for storing generated PDFs and CSVs with Lifecycle Management policies to auto-delete reports after 30 days.

### 6.3 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1. **Build:** Go binaries are compiled and packaged into Docker images.
2. **Test:** Unit tests $\rightarrow$ Integration tests $\rightarrow$ Linting.
3. **Deploy (Staging):** Automated deployment to Staging upon merge to `develop`.
4. **Deploy (Prod):** Manual trigger by Nyla Stein on Wednesday mornings.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Each Go microservice must maintain $\ge 80\%$ code coverage.
- **Tooling:** `go test` and `testify`.
- **Scope:** Focus on business logic, utility functions, and gRPC handlers.
- **Mocking:** Use of `mockgen` for gRPC client interfaces to isolate service dependencies.

### 7.2 Integration Testing
Verification of communication between two or more services.
- **Scope:** API Gateway $\rightarrow$ Auth Service; Collab Service $\rightarrow$ CockroachDB.
- **Environment:** Run in a dedicated integration namespace in K8s using ephemeral databases.
- **Approach:** Testing "Happy Path" and "Failure Path" (e.g., how the system behaves when the `ReportService` is down).

### 7.3 End-to-End (E2E) Testing
Validation of the entire user journey from the Micro-frontend to the Database.
- **Tooling:** Playwright.
- **Critical Paths:** 
    1. User Login $\rightarrow$ Document Creation $\rightarrow$ Real-time edit.
    2. Admin $\rightarrow$ Schedule Report $\rightarrow$ Verify email delivery.
    3. User $\rightarrow$ Trigger Rate Limit $\rightarrow$ Verify 429 response.

### 7.4 Regression Testing & Technical Debt
**Critical Note:** Currently, the **Core Billing Module** has 0% test coverage due to previous deadline pressure.
- **Immediate Action:** A "Debt Sprint" is scheduled for 2025-08-01 to implement 100% coverage for the billing module before the production launch.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Project sponsor rotating out of role | High | High | Hire a specialized contractor to document sponsor's vision and reduce "bus factor." |
| **R2** | Regulatory requirements change | Medium | High | De-scope affected features if unresolved by Milestone date to avoid timeline slippage. |
| **R3** | CockroachDB Latency in EU-West | Low | Medium | Implement local read-replicas in the EU region. |
| **R4** | MFE Complexity (Version Mismatch) | Medium | Medium | Enforce strict semantic versioning for all remote module entries. |
| **R5** | Billing Module Failure | High | Critical | Prioritize the "Debt Sprint" to add test coverage to the billing module. |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required.
- **High:** Weekly monitoring.
- **Medium:** Monthly review.
- **Low:** Logged for awareness.

---

## 9. TIMELINE & MILESTONES

### 9.1 Project Phases

**Phase 1: Foundation (Months 1-6)**
- Focus on Kubernetes setup, API Gateway, and the Auth Service.
- Implementation of the gRPC communication layer.
- *Dependency:* Infrastructure must be provisioned before microservices can be deployed.

**Phase 2: Core Features (Months 7-12)**
- Development of Collab Service and Report Service.
- Transition of legacy data to CockroachDB.
- *Dependency:* Data migration scripts must be validated in Staging.

**Phase 3: Refinement & Compliance (Months 13-18)**
- Audit Trail implementation, HIPAA hardening, and A/B Testing framework.
- Final Performance Tuning.
- *Dependency:* Third-party HIPAA audit must be passed.

### 9.2 Critical Milestones

| Milestone | Description | Target Date | Status |
| :--- | :--- | :--- | :--- |
| **M1** | Architecture Review Complete | 2025-07-15 | Pending |
| **M2** | Performance Benchmarks Met | 2025-09-15 | Pending |
| **M3** | Production Launch | 2025-11-15 | Pending |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-10-25  
**Attendees:** Nyla Stein, Kaia Oduya, Wren Liu, Jules Park  
**Discussion:**
- Debate over using a Monolithic DB vs. Database-per-service. 
- Nyla argued that database-per-service would introduce too much complexity for a team of 8. 
- Decision: Use a single CockroachDB cluster but enforce "logical separation" via schemas and restricted user roles.
- Wren raised concerns about the "Weekly Release Train" being too rigid for critical bugs.
- Decision: Stick to the train; however, a "Severity 1" emergency bypass is permitted if Nyla and the sponsor both approve.

**Action Items:**
- [Nyla] Finalize gRPC Protobuf definitions for Auth service. (Due: 2023-11-01)
- [Kaia] Set up the initial CockroachDB cluster on GCP. (Due: 2023-11-05)

---

### Meeting 2: Reporting Service Deep Dive
**Date:** 2023-11-12  
**Attendees:** Nyla Stein, Wren Liu, Jules Park  
**Discussion:**
- Discussion on the PDF generation engine. Jules noted that the legacy system's PDFs were often misaligned.
- Nyla proposed using Puppeteer for "HTML-to-PDF" to ensure CSS precision.
- Wren expressed concern about the memory consumption of headless Chrome in K8s.
- Decision: Deploy `ReportService` on a separate node pool with high-memory machine types to prevent OOM (Out of Memory) kills affecting other services.

**Action Items:**
- [Jules] Create sample HTML templates for "Student Progress Report." (Due: 2023-11-20)
- [Wren] Define the load-test parameters for the report generator. (Due: 2023-11-25)

---

### Meeting 3: HIPAA & Security Review
**Date:** 2023-12-05  
**Attendees:** Nyla Stein, Kaia Oduya  
**Discussion:**
- Review of encryption-at-rest. Kaia confirmed that GCP Disk Encryption is active.
- Discussion on the "Audit Trail." Nyla emphasized the need for the hash-chaining to prevent DB admins from altering logs.
- Kaia pointed out that the current Billing Module has no tests and could be a security vulnerability.
- Decision: Acknowledge the debt. The team will not touch the billing module until the "Debt Sprint" in August 2025.

**Action Items:**
- [Kaia] Implement the SHA-256 chaining logic in the `AuditService`. (Due: 2023-12-15)
- [Nyla] Draft the HIPAA compliance checklist for the external auditor. (Due: 2023-12-20)

---

## 11. BUDGET BREAKDOWN

The total budget for Project Gantry is **$400,000**. This is a modest budget for a project of this scale, requiring a lean approach to tooling and a high-trust, low-ceremony team dynamic.

| Category | Allocation | Amount | Description |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $260,000 | Salaries/Contractors (Including the risk-mitigation contractor). |
| **Infrastructure** | 20% | $80,000 | GCP Credits, GKE Nodes, CockroachDB Cloud licenses. |
| **Tools & Software** | 10% | $40,000 | GitHub Enterprise, Playwright Cloud, Monitoring (Datadog). |
| **Contingency** | 5% | $20,000 | Emergency buffer for unforeseen regulatory changes. |
| **Total** | **100%** | **$400,000** | |

**Budget Notes:**
- Personnel costs are optimized by leveraging the existing internal team (8 members).
- Infrastructure costs are projected to decrease as the team optimizes the HPA settings and utilizes preemptible VMs for the `ReportService` worker pool.

---

## 12. APPENDICES

### Appendix A: gRPC Protobuf Definition (Sample)
To ensure type safety between the `CollabService` and the `AuditService`, the following protobuf definition is used:

```protobuf
syntax = "proto3";

package gantry.audit;

service AuditLogger {
  rpc LogEvent (AuditEventRequest) returns (AuditEventResponse);
}

message AuditEventRequest {
  string tenant_id = 1;
  string user_id = 2;
  string action = 3;
  string payload_before = 4;
  string payload_after = 5;
  string timestamp = 6;
}

message AuditEventResponse {
  bool success = 1;
  string log_id = 2;
}
```

### Appendix B: HIPAA Compliance Mapping
This table maps Gantry's technical features to the HIPAA Security Rule requirements.

| HIPAA Requirement | Gantry Implementation | Technical Component |
| :--- | :--- | :--- |
| **Access Control** | JWT-based Auth with Role-Based Access Control (RBAC). | `AuthService` |
| **Audit Controls** | Tamper-evident hash-chained logging. | `AuditService` |
| **Integrity** | Digital signatures on data exports; SHA-256 for logs. | `AuditService` |
| **Transmission Security** | Forced TLS 1.3 and mTLS via Istio Service Mesh. | GKE / Istio |
| **Data Encryption** | AES-256 at rest via GCP KMS and CockroachDB encryption. | GCP Infrastructure |