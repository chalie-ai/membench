# PROJECT SPECIFICATION: PROJECT MERIDIAN
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / Drafting  
**Company:** Flintrock Engineering  
**Project Lead:** Dante Santos (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Meridian is a strategic initiative by Flintrock Engineering to develop a high-performance, enterprise-grade fintech payment processing system tailored specifically for the retail sector. Unlike previous general-purpose tooling developed by the firm, Meridian is a dedicated product vertical designed to capture and maintain a high-value partnership with a single anchor enterprise client. 

The system is designed to handle high-volume retail transactions, providing a robust bridge between legacy retail Point-of-Sale (POS) systems and modern digital payment gateways. By leveraging a Go-based microservices architecture and a globally distributed database, Meridian aims to provide the low latency and high availability required for real-time retail operations.

### 1.2 Business Justification
The primary driver for Project Meridian is a confirmed commitment from a Tier-1 retail enterprise willing to pay an annual recurring revenue (ARR) of $2,000,000 upon successful deployment and sign-off. This represents a significant shift in Flintrock Engineering's business model, moving from a project-based consultancy approach to a product-centric recurring revenue model.

The retail industry is currently experiencing a fragmented transition toward "Omnichannel" payments. The anchor client requires a system that can unify physical store payments, e-commerce transactions, and mobile wallet integrations into a single, HIPAA-compliant audit trail. The strategic importance of this project extends beyond the immediate revenue; it serves as a blueprint for a scalable retail payment product that Flintrock can later white-label for other mid-to-large scale retailers.

### 1.3 ROI Projection
Given that the project is currently "unfunded" in terms of a dedicated capital budget—bootstrapping instead through the utilization of existing 12-person cross-functional team capacity—the ROI is exceptionally high. 

**Financial Projections:**
*   **Year 1 Revenue:** $2,000,000 (Single Client)
*   **Estimated Operational Cost (Infrastructure + Overhead):** $150,000 - $250,000
*   **Personnel Cost (Internal Allocation):** Absorbed into existing payroll.
*   **Net Projected Profit (Year 1):** ~$1,750,000.

The ROI calculation is further bolstered by the "Zero Customer Acquisition Cost" (CAC) for the initial launch, as the client has already committed to the partnership. The long-term goal is to scale the system to 5 additional clients by Year 3, projecting a total ARR of $10M.

### 1.4 Compliance and Regulatory Scope
Due to the nature of payment processing and the specific requirements of the anchor client (which includes health-related retail items and insurance-linked payments), the system must be strictly HIPAA compliant. This necessitates end-to-end encryption (E2EE), strict Access Control Lists (ACLs), and an immutable audit trail.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Philosophy
Meridian utilizes a "Modular Monolith to Microservices" migration strategy. To ensure rapid initial development and reduced network overhead during the MVP phase, the system is built as a modular monolith. However, the boundaries are strictly defined via gRPC interfaces, allowing the team to split services into independent Kubernetes pods as load increases or as specific domains (e.g., Report Generation) require independent scaling.

### 2.2 The Stack
*   **Language:** Go 1.21+ (chosen for concurrency primitives and execution speed).
*   **Communication:** gRPC for internal service-to-service calls; REST/JSON for external API consumers.
*   **Database:** CockroachDB (distributed SQL for strong consistency and global scale).
*   **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
*   **Security:** TLS 1.3 for all transit; AES-256 for data at rest.

### 2.3 Architecture Diagram (ASCII Description)

```text
[ External Client/POS ] 
       |
       v
[ GCP Load Balancer ] ----> [ Cloud Armor WAF ]
       |
       v
[ Kubernetes Cluster (GKE) ]
       |
       +-- [ API Gateway (Go) ] <--- (Authentication / Rate Limiting)
       |         |
       |         +-----> [ Payment Core Module ] ----+
       |         |                                   |
       |         +-----> [ Collaborative Editor ]    |  (gRPC)
       |         |                                   |
       |         +-----> [ Reporting Engine ] <------+
       |         |                                   |
       |         +-----> [ Localization Service ]    |
       |                                              |
       +---------------------------------------------+
                                |
                                v
                      [ CockroachDB Cluster ] 
                      (Multi-Region Deployment)
                                |
                                v
                      [ Tamper-Evident Log Store ] 
                      (Immutable Storage / Write-Once)
```

### 2.4 Data Flow and Security
All incoming requests are terminated at the GKE Load Balancer and passed through a Go-based API Gateway. The Gateway validates JWT tokens and scrubs inputs. Since the system is HIPAA compliant, PII (Personally Identifiable Information) is encrypted at the application layer before being committed to CockroachDB using keys managed via GCP KMS (Key Management Service).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Real-time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Not Started

**Description:**
The Meridian dashboard allows multiple administrators to edit payment routing rules, merchant configurations, and promotional discount logic simultaneously. To prevent data loss and "last-write-wins" scenarios, the system must implement a robust conflict resolution mechanism.

**Detailed Requirements:**
*   **Operational Transformation (OT) or CRDTs:** The system will implement Conflict-free Replicated Data Types (CRDTs), specifically using LWW-Element-Set (Last-Write-Wins) and G-Counters for numerical fields.
*   **WebSocket Integration:** A persistent WebSocket connection will be established between the client and the `CollaborationService`. Every keystroke or change event will be broadcast to all active session participants in < 100ms.
*   **Cursor Tracking:** The UI must show the real-time position of other users' cursors and current highlights to prevent overlapping edits.
*   **Versioning:** Every collaborative session must generate a snapshot every 30 seconds, allowing administrators to revert the entire state to a previous point in time.
*   **Conflict Resolution Logic:** In the event of a concurrent update to the same field, the system will use a hybrid logical clock (HLC) to determine the absolute causal ordering of events.

**Acceptance Criteria:**
*   Two users editing the same routing rule simultaneously see each other's changes in real-time.
*   No data is lost during a network partition (reconnection syncs state correctly).
*   Latency for updates across regions is under 250ms.

### 3.2 Feature 2: Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Blocked

**Description:**
For HIPAA compliance and financial auditing, every single mutation in the system must be logged. These logs cannot be modified or deleted, even by a database administrator.

**Detailed Requirements:**
*   **Immutable Log Append:** The system will utilize a "Write-Once-Read-Many" (WORM) storage pattern. Logs are hashed and chained (similar to a blockchain) where each log entry contains the SHA-256 hash of the previous entry.
*   **Tamper Detection:** A background process will periodically verify the hash chain. If a hash mismatch is detected, an immediate critical alert is triggered to the Security team.
*   **Granularity:** Logs must capture: `Timestamp`, `UserID`, `IP Address`, `Action`, `Previous State (JSON)`, `New State (JSON)`, and `RequestID`.
*   **Storage Layer:** Logs will be streamed via Kafka to a dedicated CockroachDB table with "restricted update" permissions and mirrored to a GCP Cloud Storage bucket with "Object Lock" enabled.

**Blocker Details:** The current blocking issue is the lack of a finalized schema for the "Previous State" capture, as the modular monolith is still evolving, making snapshotting inconsistent.

**Acceptance Criteria:**
*   Successful verification of the hash chain across 1,000,000 entries.
*   Zero ability for a DB admin to modify a log entry without breaking the chain.

### 3.3 Feature 3: Localization and Internationalization (L10n/I18n)
**Priority:** Medium | **Status:** Not Started

**Description:**
Meridian must support 12 languages to accommodate the global retail footprint of the anchor client, covering regions in North America, EMEA, and APAC.

**Detailed Requirements:**
*   **Language Support:** English (US/UK), Spanish (ES/MX), French (FR/CA), German, Italian, Portuguese (BR), Chinese (Simplified), Japanese, Korean, Arabic, Hindi, and Dutch.
*   **Dynamic Translation Keys:** The system will use a key-based translation system (e.g., `payment.success_message`) stored in a cached Redis layer.
*   **Right-to-Left (RTL) Support:** The UI must dynamically flip the layout for Arabic.
*   **Currency and Date Formatting:** Implementation of the ICU (International Components for Unicode) standard to ensure dates and currency symbols ($ vs € vs ¥) are placed correctly based on the user's locale.
*   **UTF-8 Enforcement:** All database columns must be strictly UTF-8 to support non-Latin character sets.

**Acceptance Criteria:**
*   Toggle between any of the 12 languages without page refresh.
*   Correct currency formatting for at least 5 different global currencies.

### 3.4 Feature 4: PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Blocked

**Description:**
Retail managers require daily, weekly, and monthly reconciliation reports. The system must generate these as downloadable files and email them to designated stakeholders.

**Detailed Requirements:**
*   **Asynchronous Processing:** Reports will be handled by a background worker pool to avoid blocking the main API. Users request a report $\rightarrow$ system queues job $\rightarrow$ system notifies user via email/webhook upon completion.
*   **Formats:** 
    *   **PDF:** High-fidelity, branded documents for executive review.
    *   **CSV:** Raw data dumps for import into Excel/Tableau.
*   **Scheduling Engine:** A cron-like scheduler within the `ReportingService` that allows users to define schedules (e.g., "Every Monday at 08:00 UTC").
*   **Delivery Mechanisms:** Integration with SendGrid for email delivery and S3-compatible buckets for secure link sharing.

**Blocker Details:** Currently blocked by the "Data Import/Export" finalization; reporting cannot be validated until the import/export logic for large datasets is fully stress-tested.

**Acceptance Criteria:**
*   Generation of a 10,000-row CSV in under 30 seconds.
*   Successful scheduled delivery of a PDF to three different email addresses.

### 3.5 Feature 5: Data Import/Export with Format Auto-Detection
**Priority:** Critical | **Status:** Complete

**Description:**
To facilitate onboarding, the system must allow the client to migrate legacy transaction data from various formats. The system must automatically detect the file type and map fields to the Meridian schema.

**Detailed Requirements:**
*   **Supported Formats:** JSON, CSV, XML, and Fixed-Width Text files.
*   **Auto-Detection Logic:** The system reads the first 1KB of the file, checks for magic bytes (JSON/XML) or delimiter patterns (CSV), and suggests a mapping profile.
*   **Mapping Engine:** A visual mapper where users can link "Legacy Column A" to "Meridian Field B."
*   **Validation Pipeline:** All imported data passes through a validation gate that checks for HIPAA compliance, data types, and mandatory fields before committing to CockroachDB.
*   **Export Capabilities:** Full dump of all merchant data in the user's choice of format.

**Technical Implementation:** Implemented using Go's `encoding/csv` and `encoding/json` packages with a custom reflection-based mapper.

**Acceptance Criteria:**
*   Successful import of a 500MB CSV file with 99.9% accuracy.
*   Automatic detection of JSON vs XML files with 100% accuracy.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication requires a `Bearer <JWT>` token in the header.

### 4.1 Payment Processing Endpoints

**1. Create Transaction**
*   **Path:** `POST /payments/execute`
*   **Description:** Initiates a new retail payment.
*   **Request:**
    ```json
    {
      "merchant_id": "merch_9921",
      "amount": 150.50,
      "currency": "USD",
      "payment_method": "credit_card",
      "metadata": { "store_id": "nyc_01" }
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "transaction_id": "tx_8823110",
      "status": "processing",
      "timestamp": "2023-10-24T10:00:00Z"
    }
    ```

**2. Get Transaction Status**
*   **Path:** `GET /payments/{tx_id}/status`
*   **Description:** Retrieves the current state of a payment.
*   **Response (200 OK):**
    ```json
    {
      "transaction_id": "tx_8823110",
      "status": "completed",
      "settlement_date": "2023-10-25"
    }
    ```

**3. Refund Transaction**
*   **Path:** `POST /payments/{tx_id}/refund`
*   **Description:** Processes a full or partial refund.
*   **Request:** `{ "amount": 50.00, "reason": "customer_return" }`
*   **Response (200 OK):** `{ "refund_id": "ref_1122", "status": "refunded" }`

### 4.2 Collaborative Routing Endpoints

**4. Update Routing Rule**
*   **Path:** `PATCH /routing/rules/{rule_id}`
*   **Description:** Updates a payment routing rule via the collaborative editor.
*   **Request:** `{ "target_gateway": "stripe_v3", "priority": 1 }`
*   **Response (200 OK):** `{ "rule_id": "rule_44", "version": 12, "status": "synced" }`

**5. Get Active Collaborators**
*   **Path:** `GET /routing/sessions/{session_id}/users`
*   **Description:** Lists all users currently editing a specific rule set.
*   **Response (200 OK):** `[ { "user_id": "user_1", "name": "Dante Santos", "color": "#FF5733" } ]`

### 4.3 Reporting and Admin Endpoints

**6. Request Report**
*   **Path:** `POST /reports/generate`
*   **Description:** Triggers a PDF/CSV report generation.
*   **Request:** `{ "type": "reconciliation", "format": "pdf", "start_date": "2023-01-01", "end_date": "2023-01-31" }`
*   **Response (202 Accepted):** `{ "job_id": "job_abc123", "eta": "60s" }`

**7. Download Report**
*   **Path:** `GET /reports/download/{job_id}`
*   **Description:** Retrieves the generated file.
*   **Response:** Binary stream of PDF/CSV file.

**8. Import Legacy Data**
*   **Path:** `POST /admin/import`
*   **Description:** Uploads a file for auto-detection and import.
*   **Request:** `Multipart/form-data (file upload)`
*   **Response (202 Accepted):** `{ "import_id": "imp_778", "detected_format": "csv", "rows_found": 5000 }`

---

## 5. DATABASE SCHEMA

The system uses CockroachDB. All tables utilize UUIDs as primary keys to support global distribution.

### 5.1 Table Definitions

1.  **`merchants`**
    *   `merchant_id` (UUID, PK): Unique identifier.
    *   `company_name` (String): Legal entity name.
    *   `api_key_hash` (String): Hashed key for authentication.
    *   `created_at` (Timestamp): Record creation date.
2.  **`transactions`**
    *   `tx_id` (UUID, PK): Unique transaction ID.
    *   `merchant_id` (UUID, FK $\rightarrow$ merchants): Merchant who processed the payment.
    *   `amount` (Decimal): Total value.
    *   `currency` (String): ISO 4217 code.
    *   `status` (Enum): [pending, processing, completed, failed, refunded].
    *   `encrypted_pii` (Blob): HIPAA-encrypted customer data.
3.  **`refunds`**
    *   `refund_id` (UUID, PK): Unique refund ID.
    *   `tx_id` (UUID, FK $\rightarrow$ transactions): Original transaction.
    *   `amount` (Decimal): Refunded amount.
    *   `processed_at` (Timestamp).
4.  **`routing_rules`**
    *   `rule_id` (UUID, PK): Rule identifier.
    *   `priority` (Int): Execution order.
    *   `condition` (JSONB): Logic for when this rule applies.
    *   `target_gateway` (String): Destination gateway.
    *   `version` (Int): Incrementing version for conflict resolution.
5.  **`audit_logs`**
    *   `log_id` (UUID, PK): Log entry ID.
    *   `tx_id` (UUID, FK $\rightarrow$ transactions, nullable): Associated transaction.
    *   `user_id` (UUID): Actor who performed the change.
    *   `action` (String): The operation performed.
    *   `payload_before` (JSONB): State before change.
    *   `payload_after` (JSONB): State after change.
    *   `chain_hash` (String): SHA-256 hash of (current entry + previous hash).
6.  **`users`**
    *   `user_id` (UUID, PK): User identifier.
    *   `email` (String, Unique).
    *   `password_hash` (String).
    *   `role` (Enum): [admin, operator, auditor].
7.  **`localization_strings`**
    *   `string_id` (String, PK): The key (e.g., `err_insufficient_funds`).
    *   `lang_code` (String, PK): ISO language code.
    *   `translation` (Text): The translated string.
8.  **`report_jobs`**
    *   `job_id` (UUID, PK): Job identifier.
    *   `user_id` (UUID, FK $\rightarrow$ users): Requester.
    *   `status` (Enum): [queued, running, completed, failed].
    *   `file_path` (String): Path to GCP bucket.
9.  **`report_schedules`**
    *   `schedule_id` (UUID, PK): Schedule identifier.
    *   `cron_expression` (String): Standard cron format.
    *   `report_type` (String).
    *   `recipient_emails` (Array of Strings).
10. **`collaboration_sessions`**
    *   `session_id` (UUID, PK): Session identifier.
    *   `resource_id` (UUID): The ID of the rule being edited.
    *   `active_users` (Array of UUIDs).
    *   `last_heartbeat` (Timestamp).

### 5.2 Relationships
*   **One-to-Many:** `merchants` $\rightarrow$ `transactions`.
*   **One-to-One:** `transactions` $\rightarrow$ `refunds` (maximum one full refund per transaction).
*   **Many-to-Many:** `users` $\rightarrow$ `collaboration_sessions` (tracked via the `active_users` array).
*   **One-to-Many:** `transactions` $\rightarrow$ `audit_logs`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Meridian utilizes three distinct environments to ensure stability and HIPAA compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature iteration and unit testing.
*   **Infrastructure:** Single GKE cluster with preemptible nodes.
*   **Database:** Local CockroachDB instance (single-node).
*   **Deployment:** Automated via CI/CD pipeline upon merge to `develop` branch.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Pre-production validation and stakeholder UAT (User Acceptance Testing).
*   **Infrastructure:** Mirrored production configuration (3-node GKE cluster).
*   **Database:** CockroachDB 3-node cluster with anonymized production data.
*   **Deployment:** Manual trigger from `release` branch.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live retail transaction processing.
*   **Infrastructure:** Multi-region GKE deployment (US-East, US-West, Europe-West).
*   **Database:** Multi-region CockroachDB cluster with survival goals set to `region`.
*   **Deployment:** **Manual deployments** performed exclusively by Rafik Park (DevOps Engineer). This creates a "Bus Factor of 1" risk, which is noted in the Risk Register.

### 6.2 Infrastructure as Code (IaC)
Infrastructure is managed via Terraform. All GCP resources (Compute Engine, GKE, Cloud Storage, KMS) are defined in `.tf` files.

### 6.3 HIPAA Security Controls
*   **Encryption in Transit:** All gRPC and REST traffic is forced over TLS 1.3.
*   **Encryption at Rest:** All CockroachDB disks are encrypted using GCP's default encryption and application-level encryption via AES-256 for PII fields.
*   **Network Isolation:** The GKE cluster resides in a VPC with no public IP addresses for worker nodes. Access is managed via a Bastion Host and Cloud IAP (Identity-Aware Proxy).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Approach:** Every Go package must have corresponding `_test.go` files.
*   **Coverage Target:** 80% line coverage.
*   **Tooling:** `go test -cover`.
*   **Focus:** Business logic in the "Core" modules, CRDT resolution logic, and localization string parsing.

### 7.2 Integration Testing
*   **Approach:** Testing the interaction between microservices via gRPC.
*   **Tooling:** Docker Compose to spin up Mock Gateways and a CockroachDB container.
*   **Focus:** 
    *   Ensuring the API Gateway correctly routes requests to the Payment Core.
    *   Verifying that `audit_logs` are written immediately following a `transaction` update.
    *   Validating the "Import/Export" pipeline against malformed files.

### 7.3 End-to-End (E2E) Testing
*   **Approach:** Black-box testing of the entire flow from POS request to Report generation.
*   **Tooling:** Playwright for UI testing, Postman/Newman for API suite testing.
*   **Scenario Example:** 
    1.  Create a transaction $\rightarrow$ 2. Trigger a refund $\rightarrow$ 3. Verify audit log entry $\rightarrow$ 4. Generate a reconciliation report $\rightarrow$ 5. Verify PDF contains the transaction.

### 7.4 Performance Testing
*   **Tooling:** k6 (Grafana) for load testing.
*   **Target:** p95 response time $< 200$ms for `POST /payments/execute` under a load of 5,000 Requests Per Second (RPS).

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Integration partner API is undocumented and buggy | High | High | Build a "Gateway Adapter" layer to abstract the partner API; develop a fallback architecture using a secondary provider. |
| **R-02** | Project sponsor rotating out of role | Medium | High | Engage an external consultant for an independent assessment of the project's value to the company, ensuring the new sponsor sees the $2M ARR. |
| **R-03** | Bus Factor: Only Rafik Park can deploy to Prod | High | Medium | Document all Terraform and K8s manifests; implement a "Deployment Playbook" for Dante Santos to follow in emergencies. |
| **R-04** | Technical Debt: No structured logging | High | Medium | Transition from `fmt.Println` (stdout) to `uber-go/zap` for structured JSON logging in the next sprint. |
| **R-05** | HIPAA compliance failure | Low | Critical | Quarterly third-party security audits and automated vulnerability scanning using Snyk. |

### 8.1 Probability/Impact Matrix
*   **High/High:** Immediate priority (R-01).
*   **High/Medium:** Tactical priority (R-03, R-04).
*   **Medium/High:** Strategic priority (R-02).
*   **Low/Critical:** Guardrail priority (R-05).

---

## 9. TIMELINE

### 9.1 Phases and Dependencies

**Phase 1: Foundation & Core Import (Oct 2023 - Feb 2024)**
*   *Dependency:* None.
*   *Key Deliverable:* Data Import/Export module (Complete).
*   *Objective:* Establish the database schema and core API connectivity.

**Phase 2: MVP Feature Build-out (Feb 2024 - Apr 2024)**
*   *Dependency:* Foundation must be stable.
*   *Focus:* Collaborative Editing (High Priority), Reporting Engine (High Priority).
*   *Target:* **Milestone 1 (MVP feature-complete) by 2025-04-15.**

**Phase 3: Compliance & Localization (Apr 2024 - June 2024)**
*   *Dependency:* Feature set must be locked.
*   *Focus:* Audit Trail (Medium Priority), L10n/I18n (Medium Priority).
*   *Target:* **Milestone 2 (Stakeholder demo and sign-off) by 2025-06-15.**

**Phase 4: Hardening & Optimization (June 2024 - Aug 2024)**
*   *Dependency:* Sign-off from Phase 3.
*   *Focus:* p95 latency tuning, stress testing, security penetration tests.
*   *Target:* **Milestone 3 (Performance benchmarks met) by 2025-08-15.**

### 9.2 Gantt-Style Summary
*   **Q4 2023:** Setup $\rightarrow$ Import/Export $\checkmark$
*   **Q1 2024:** Collaborative Editing $\rightarrow$ Reporting Engine $\rightarrow$ MVP Finish.
*   **Q2 2024:** Audit Logs $\rightarrow$ Localization $\rightarrow$ Client Demo.
*   **Q3 2024:** Optimization $\rightarrow$ Performance Tuning $\rightarrow$ Go-Live.

---

## 10. MEETING NOTES

### 10.1 Meeting: Weekly Sync (2023-11-02)
*   **Attendees:** Dante, Rafik, Emeka, Saoirse.
*   **Notes:**
    *   Import/Export is done.
    *   Emeka says UI for collaborative editing needs a "presence" indicator.
    *   Rafik warns about GCP quota limits in `us-east1`.
    *   Saoirse asking about where to put the `localization.json` files.
*   **Decision:** Use a dedicated GCS bucket for translation files; Rafik to request quota increase.

### 10.2 Meeting: Technical Deep Dive: CRDTs (2023-11-09)
*   **Attendees:** Dante, Rafik.
*   **Notes:**
    *   Discussed OT vs CRDT.
    *   OT too complex for the current team size.
    *   Going with LWW-Element-Set for simplicity.
    *   Need to ensure CockroachDB timestamps are synchronized.
*   **Decision:** Use Hybrid Logical Clocks (HLC) for event ordering.

### 10.3 Meeting: Sponsor Status Update (2023-11-16)
*   **Attendees:** Dante, Project Sponsor, External Consultant.
*   **Notes:**
    *   Sponsor might leave in Q1.
    *   Consultant says the product is "highly viable."
    *   $2M contract is signed, but needs new sign-off if sponsor leaves.
    *   Dante stressed the importance of the April MVP date.
*   **Decision:** Consultant will write a formal "Value Proposition" document to present to the upcoming executive board.

---

## 11. BUDGET BREAKDOWN

Since the project is bootstrapping with existing capacity, "Personnel" costs are internal allocations. However, the projected operational budget for the first year is as follows:

| Category | Item | Annual Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 12-person Cross-functional Team | $1,440,000 | Internal allocation (Avg $10k/mo per person) |
| **Infrastructure** | GCP (GKE, CockroachDB, Cloud Storage) | $120,000 | Estimated $10k/month for multi-region |
| **Tools** | GitHub Enterprise, Snyk, Datadog, SendGrid | $25,000 | Annual licenses |
| **Consulting** | External Assessment Specialist | $15,000 | One-time fee for sponsor transition |
| **Contingency** | Emergency Infrastructure / Bursting | $20,000 | For peak load testing phases |
| **TOTAL** | | **$1,620,000** | |

**Net Budgetary Position:**
*   Expected Revenue: $2,000,000
*   Total Cost: $1,620,000
*   **Projected Net Gain: $380,000** (assuming internal salaries are recovered).

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (Technical Detail)
The `CollaborationService` utilizes a state-based CRDT. For a routing rule modification, the system stores a set of tuples: `(Field, Value, Timestamp)`. 
When merging two states $S_1$ and $S_2$:
1.  For each field $F$, compare the timestamps $T_1$ and $T_2$.
2.  The value associated with $\max(T_1, T_2)$ is preserved.
3.  In the event of a timestamp tie, the value with the lexicographically higher `UserID` is chosen to ensure convergence across all nodes.

### Appendix B: HIPAA Encryption Workflow
1.  **Input:** User submits PII (e.g., Patient Name) via `POST /payments/execute`.
2.  **Encryption:** The `SecurityModule` calls the GCP KMS `encrypt` API using the `meridian-pii-key`.
3.  **Storage:** The resulting ciphertext is stored in the `encrypted_pii` blob column in CockroachDB.
4.  **Decryption:** Only users with the `auditor` role can trigger the `decrypt` call, which is logged in the `audit_logs` table with a "High Severity" flag, notifying the security lead.