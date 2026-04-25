# PROJECT SPECIFICATION DOCUMENT: PROJECT HARBINGER
**Document Version:** 1.0.4  
**Status:** Draft for Board Review  
**Date:** October 24, 2023  
**Classification:** Confidential - Internal Use Only  
**Company:** Talus Innovations  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project Harbinger is a mission-critical embedded systems firmware initiative designed to revolutionize the productivity and monitoring capabilities of renewable energy assets managed by Talus Innovations. Originally conceived as a high-intensity hackathon project to solve immediate telemetry gaps, Harbinger has evolved into a robust internal tool currently supporting 500 daily active users (DAU). As Talus Innovations scales its footprint in the renewable energy sector—specifically within solar and wind grid integration—the need for a professional-grade, secure, and scalable firmware management layer has become paramount.

### 1.2 Business Justification
The current landscape of renewable energy requires millisecond-precision monitoring and the ability to push over-the-air (OTA) updates to thousands of remote endpoints. The "hackathon" version of Harbinger proved the concept: reducing manual configuration time by 70% and increasing uptime by 12% across pilot sites. However, the transition from a prototype to a flagship production system is required to support the company's strategic growth. 

The primary business driver is the transition from internal productivity to a commercializable platform. By formalizing the firmware distribution and monitoring pipeline, Talus Innovations can offer "Firmware-as-a-Service" (FaaS) to partner energy cooperatives, creating a new recurring revenue stream.

### 1.3 ROI Projection
With a dedicated budget of $5.2M, Project Harbinger is projected to yield a significant return on investment over a 36-month horizon. 
- **Cost Reduction:** By automating the audit trail and multi-tenant isolation, we project a reduction in operational overhead by $400k annually.
- **Revenue Generation:** The customer-facing API will allow external partners to integrate their dashboards with Harbinger’s telemetry. Projecting an average contract value (ACV) of $50k per partner across 40 partners, this represents $2M in annual recurring revenue (ARR).
- **Risk Mitigation:** Implementing PCI DSS Level 1 compliance prevents potential fines and data breach liabilities which, in the energy sector, could exceed $10M in regulatory penalties.
- **Projected ROI:** Estimated at 215% by the end of Year 3, driven by the transition from a cost-center tool to a revenue-generating product.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Harbinger utilizes a hybrid architecture. At its core, it is a **modular monolith** designed for rapid development and deployment, but it is currently undergoing a strategic, incremental transition toward a **microservices architecture**. This allows the team to decouple high-load services (like the telemetry ingestion engine) from administrative services (like user management).

The stack consists of:
- **Backend:** Python 3.11 with FastAPI for high-performance asynchronous API endpoints.
- **Database:** MongoDB (v6.0) for flexible, document-oriented storage of device configurations and telemetry.
- **Task Queue:** Celery 5.2 with Redis as a broker to handle asynchronous firmware pushes and virus scanning.
- **Containerization:** Docker Compose for orchestrated deployment across self-hosted bare-metal servers.
- **Security:** PCI DSS Level 1 compliant vaulting for credit card processing (used for partner subscriptions).

### 2.2 Architectural Diagram (ASCII Description)
The following describes the data flow from the Embedded Device to the User Interface.

```text
[Embedded Device/Firmware] 
       |
       | (HTTPS/TLS 1.3)
       v
[Nginx Reverse Proxy / Load Balancer]
       |
       +-----> [FastAPI Gateway (The Monolith)]
                    |
                    |-- (Auth/JWT) --> [MongoDB Cluster]
                    |
                    |-- (Async Task) --> [Celery Worker]
                                           |
                                           |--> [Virus Scanner (ClamAV)]
                                           |--> [CDN (Cloudfront/S3)]
                                           |--> [Audit Log (Immutable)]
                    |
                    |-- (External) --> [Partner API (v1/v2)]
                                           |
                                           |--> [LaunchDarkly (Feature Flags)]
```

### 2.3 Deployment Strategy
We employ a **Canary Release** strategy. New firmware versions or API changes are deployed to a small subset (5%) of devices/users. If telemetry indicates no increase in error rates, the rollout expands. This is managed via **LaunchDarkly**, allowing the team to toggle features in real-time without redeploying code.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Localization and Internationalization (L10n/I18n)
**Priority:** Critical (Launch Blocker) | **Status:** Complete  
**Description:** To support global renewable energy markets, Harbinger must support 12 languages (English, Spanish, French, German, Mandarin, Japanese, Portuguese, Arabic, Hindi, Korean, Italian, and Dutch).

The implementation utilizes the `gettext` standard for Python and a custom translation middleware in FastAPI. All user-facing strings are extracted into `.po` files. The system detects the user's locale via the `Accept-Language` HTTP header or a manual preference setting in the user profile. 

**Technical Specifics:**
- **Unicode Support:** Full UTF-8 encoding across the MongoDB layer to ensure non-Latin characters are stored without corruption.
- **Dynamic Formatting:** Implementation of the `Babel` library to handle locale-specific date, time, and currency formatting (critical for energy billing).
- **RTL Support:** The UI (designed by Luciano Gupta) includes a mirrored CSS layout for Arabic and Hebrew, ensuring the dashboard remains intuitive.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Design  
**Description:** Given the critical nature of energy infrastructure, every change to firmware configuration must be logged in a tamper-evident manner. This is a regulatory requirement for PCI DSS and energy sector compliance.

The design involves a "Write-Once-Read-Many" (WORM) approach. Every API call that modifies system state triggers a Celery task that writes a signed hash of the event to a dedicated audit collection in MongoDB.

**Technical Specifics:**
- **Hashing:** Each log entry contains a SHA-256 hash of the current event plus the hash of the previous entry (creating a hash chain).
- **Storage:** Logs are mirrored to an immutable S3 bucket with "Object Lock" enabled, preventing any deletion or modification for 7 years.
- **Verification:** A background "Integrity Checker" service runs every 6 hours to validate the hash chain. Any break in the chain triggers an immediate P0 alert to the CTO.

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Review  
**Description:** Firmware binaries are uploaded by developers and distributed to thousands of devices. To prevent the "supply chain attack" vector, all binaries must be scanned for malware before distribution.

**Technical Specifics:**
- **Pipeline:** File $\rightarrow$ FastAPI $\rightarrow$ Temporary Encrypted Volume $\rightarrow$ ClamAV Scan $\rightarrow$ S3 Bucket $\rightarrow$ CloudFront CDN.
- **Virus Scanning:** We use an asynchronous Celery worker to run ClamAV. If a threat is detected, the file is quarantined, and the uploader is notified via a webhook.
- **Distribution:** Binaries are cached at the edge via a CDN to reduce latency for remote wind farms in low-connectivity areas.
- **Checksums:** Upon upload, the system generates an MD5 and SHA-256 checksum, which is embedded in the firmware metadata for the device to verify upon download.

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** Critical (Launch Blocker) | **Status:** In Review  
**Description:** To enable partner integrations, Harbinger provides a RESTful API. To prevent breaking changes, we implement strict semantic versioning and a mirrored sandbox environment.

**Technical Specifics:**
- **Versioning:** Versioning is handled via URL paths (e.g., `/api/v1/devices` and `/api/v2/devices`). The deprecated version is supported for 12 months after a new version launch.
- **Sandbox:** A separate MongoDB instance and Docker Compose stack are maintained as the "Sandbox." It contains synthetic data and allows partners to test their integrations without affecting production energy assets.
- **Rate Limiting:** Implemented via Redis to prevent API abuse, with tiered limits based on the partner's subscription level.

### 3.5 Multi-Tenant Data Isolation
**Priority:** Medium | **Status:** In Review  
**Description:** Harbinger supports multiple energy providers on shared infrastructure. We must ensure that Provider A cannot see or modify the firmware configurations of Provider B.

**Technical Specifics:**
- **Logical Isolation:** Every document in MongoDB contains a `tenant_id`. All FastAPI queries are wrapped in a dependency that injects a `tenant_filter` based on the authenticated user's organization.
- **Encryption:** Sensitive tenant data is encrypted at rest using AES-256, with tenant-specific keys managed by a secure Key Management Service (KMS).
- **Shared Infrastructure:** To optimize costs, we use a shared MongoDB cluster but utilize "Database Per Tenant" for the highest-tier enterprise customers who require physical isolation.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Authorization header.

### 4.1 `POST /api/v1/firmware/upload`
**Description:** Uploads a new firmware binary for scanning and distribution.
- **Request Body:** `multipart/form-data` (file, version_string, target_hardware_rev)
- **Response (202 Accepted):** 
  ```json
  { "job_id": "celery-12345", "status": "scanning", "eta": "30s" }
  ```

### 4.2 `GET /api/v1/firmware/status/{job_id}`
**Description:** Checks the status of the virus scan and CDN propagation.
- **Response (200 OK):**
  ```json
  { "job_id": "celery-12345", "status": "completed", "cdn_url": "https://cdn.talus.io/f/v2.1.bin" }
  ```

### 4.3 `GET /api/v1/devices`
**Description:** Retrieves a list of all embedded devices associated with the tenant.
- **Query Params:** `status` (online/offline), `version` (string)
- **Response (200 OK):**
  ```json
  [ { "device_id": "HW-992", "version": "2.0.1", "last_seen": "2023-10-23T12:00:00Z" } ]
  ```

### 4.4 `PATCH /api/v1/devices/{id}/update`
**Description:** Schedules a firmware update for a specific device.
- **Request Body:** `{ "target_version": "2.1.0", "force": false }`
- **Response (200 OK):**
  ```json
  { "update_id": "upd-778", "scheduled_time": "2023-10-24T02:00:00Z" }
  ```

### 4.5 `GET /api/v1/audit/logs`
**Description:** Fetches the tamper-evident log chain for compliance review.
- **Query Params:** `start_date`, `end_date`
- **Response (200 OK):**
  ```json
  [ { "timestamp": "...", "action": "FIRMWARE_PUSH", "user": "akim", "hash": "abc123...", "prev_hash": "def456..." } ]
  ```

### 4.6 `POST /api/v1/billing/payment-method`
**Description:** Processes credit card data (PCI DSS Level 1 compliant).
- **Request Body:** `{ "card_number": "...", "expiry": "...", "cvv": "..." }`
- **Response (201 Created):**
  ```json
  { "payment_method_id": "pm_9982", "status": "verified" }
  ```

### 4.7 `GET /api/v1/tenants/config`
**Description:** Retrieves tenant-specific configuration overrides.
- **Response (200 OK):**
  ```json
  { "tenant_id": "t-101", "region": "EU-West", "max_devices": 5000 }
  ```

### 4.8 `DELETE /api/v1/sandbox/reset`
**Description:** Wipes the sandbox environment for a partner to start fresh testing.
- **Response (204 No Content):** `null`

---

## 5. DATABASE SCHEMA (MONGODB)

Since MongoDB is schema-less, the following represents the **enforced document structures** used by the FastAPI Pydantic models.

### 5.1 Collection: `tenants`
- `_id`: ObjectId (PK)
- `name`: String
- `api_key`: String (Hashed)
- `tier`: String (Free, Pro, Enterprise)
- `created_at`: DateTime

### 5.2 Collection: `users`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `email`: String (Unique)
- `password_hash`: String
- `role`: String (Admin, Operator, Viewer)

### 5.3 Collection: `devices`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `serial_number`: String (Unique)
- `current_version`: String
- `hardware_rev`: String
- `last_heartbeat`: DateTime
- `status`: String (Active, Maintenance, Decommissioned)

### 5.4 Collection: `firmware_binaries`
- `_id`: ObjectId (PK)
- `version`: String (Unique)
- `checksum_sha256`: String
- `cdn_url`: String
- `scan_status`: String (Pending, Clean, Infected)
- `uploaded_by`: ObjectId (FK $\rightarrow$ users)

### 5.5 Collection: `deployment_jobs`
- `_id`: ObjectId (PK)
- `binary_id`: ObjectId (FK $\rightarrow$ firmware_binaries)
- `target_devices`: Array[ObjectId]
- `status`: String (Scheduled, In-Progress, Completed, Failed)
- `started_at`: DateTime

### 5.6 Collection: `audit_logs`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `action`: String
- `payload_snapshot`: Object
- `hash`: String (Current Block Hash)
- `prev_hash`: String (Pointer to previous log)

### 5.7 Collection: `subscriptions`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `payment_method_id`: String (PCI Token)
- `amount`: Decimal
- `next_billing_date`: DateTime

### 5.8 Collection: `api_keys`
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `key_value`: String (Encrypted)
- `scopes`: Array[String]
- `expires_at`: DateTime

### 5.9 Collection: `system_configs`
- `_id`: ObjectId (PK)
- `key`: String (Unique)
- `value`: String
- `environment`: String (Dev, Staging, Prod)

### 5.10 Collection: `virus_scan_reports`
- `_id`: ObjectId (PK)
- `binary_id`: ObjectId (FK $\rightarrow$ firmware_binaries)
- `threat_name`: String
- `severity`: String
- `scan_duration`: Float

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

| Feature | Development (Dev) | Staging (QA) | Production (Prod) |
| :--- | :--- | :--- | :--- |
| **Hosting** | Local Docker Compose | Dedicated Staging VPS | Bare Metal Cluster (Self-Hosted) |
| **Database** | MongoDB Community (Single) | MongoDB Replica Set | MongoDB Sharded Cluster |
| **Data** | Mock/Synthetic | Sanitized Prod Copy | Live Tenant Data |
| **Traffic** | Internal Team | Internal QA / Beta Users | Global Public (via Nginx) |
| **Logging** | Console/File | ELK Stack (Basic) | ELK Stack + Immutable S3 |
| **PCI Status** | Not Compliant | PCI-Audit Mode | PCI DSS Level 1 Certified |

### 6.2 CI/CD Pipeline
We use a Git-flow based approach.
1. **Feature Branch** $\rightarrow$ Pull Request $\rightarrow$ Automated Unit Tests.
2. **Develop Branch** $\rightarrow$ Deploys to **Dev Environment**.
3. **Release Branch** $\rightarrow$ Deploys to **Staging**.
4. **Main Branch** $\rightarrow$ Deploys to **Production** via Canary.

### 6.3 Infrastructure Tooling
- **Containerization:** Docker + Docker Compose.
- **Orchestration:** Simple script-based rolling restarts (transitioning to Kubernetes in 2027).
- **Secret Management:** HashiCorp Vault for managing MongoDB credentials and API keys.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Coverage Goal:** 85% of business logic.
- **Focus:** Validating the L10n translation logic and the hash-chaining algorithm for audit logs.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** Database queries and Celery task hand-offs.
- **Approach:** We use `testcontainers` to spin up a real MongoDB and Redis instance during the test suite to avoid "mock-drift."
- **Scenario:** Testing the flow from `POST /upload` $\rightarrow$ `Celery Scan` $\rightarrow$ `Update MongoDB Status`.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Scenario:** A full user journey: *Login $\rightarrow$ Upload Firmware $\rightarrow$ Assign to Device $\rightarrow$ Verify Audit Log Entry*.
- **Frequency:** Weekly regression suite run on the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Key architect leaving company in 3 months | High | Critical | Negotiate timeline extension with stakeholders; initiate intensive knowledge transfer sessions. |
| R2 | Integration partner API is undocumented/buggy | High | Medium | Engage external consultant for an independent assessment and reverse-engineering of the API. |
| R3 | PCI DSS Audit failure | Low | High | Monthly internal pre-audits and strict adherence to the security specification. |
| R4 | MongoDB scaling bottleneck | Medium | Medium | Implement sharding strategy for `devices` and `audit_logs` collections. |

**Risk Matrix:**
- **Critical:** Immediate action required (R1).
- **High:** Weekly monitoring (R2).
- **Medium:** Monthly review (R4).

---

## 9. TIMELINE & MILESTONES

The project follows a phased approach, with dependencies heavily linked to legal and technical sign-offs.

### 9.1 Phase 1: Stabilization (Now - August 2026)
- **Focus:** Completing critical launch blockers (Audit trail, API, L10n).
- **Dependencies:** Legal review of Data Processing Agreement (DPA).
- **Milestone 1 (2026-08-15):** **Production Launch.** Full system availability for internal users.

### 9.2 Phase 2: Validation (August 2026 - October 2026)
- **Focus:** Stability monitoring and stakeholder feedback.
- **Dependencies:** Successful production soak test.
- **Milestone 2 (2026-10-15):** **Stakeholder Demo and Sign-off.** Presentation to the Board of Directors.

### 9.3 Phase 3: Expansion (October 2026 - December 2026)
- **Focus:** External partner onboarding.
- **Dependencies:** Final PCI DSS certification.
- **Milestone 3 (2026-12-15):** **External Beta.** Launch with 10 selected pilot users.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per team dynamic, formal minutes are not kept. The following are reconstructed decisions from Slack threads.*

### Thread: `#dev-harbinger` | Date: 2023-09-12
**Participants:** Chioma Kim, Astrid Jensen, Luciano Gupta
- **Discussion:** Astrid raised concerns about the hardcoded `API_KEY` and `DB_URL` values across 40+ files.
- **Decision:** We cannot stop feature development for a full refactor right now. We will move them to a `.env` file managed by HashiCorp Vault in a "Cleanup Sprint" after Milestone 1.
- **Action:** Astrid to create a list of all files containing hardcoded secrets.

### Thread: `#prod-design` | Date: 2023-10-05
**Participants:** Luciano Gupta, Javier Park, Chioma Kim
- **Discussion:** Javier noted that the Arabic translation for "Firmware Update" is breaking the UI container.
- **Decision:** Luciano will implement a "flexible-width" container system and support RTL (Right-to-Left) mirroring for the dashboard.
- **Action:** Luciano to update the Figma prototypes by Friday.

### Thread: `#mgmt-updates` | Date: 2023-11-02
**Participants:** Chioma Kim, Astrid Jensen
- **Discussion:** The integration partner's API is returning 500 errors for 30% of requests, and their documentation is 2 years old.
- **Decision:** We cannot rely on the partner's internal support. Chioma approved a $15k budget for an external consultant to audit the API and provide a mapping document.
- **Action:** Chioma to source the consultant.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,200,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,120,000 | Salaries for CTO, Sr. Backend, Designer, Intern, and future hires. |
| **Infrastructure** | 20% | $1,040,000 | Bare metal servers, MongoDB Enterprise licenses, S3/CDN costs. |
| **Tools & SaaS** | 5% | $260,000 | LaunchDarkly, HashiCorp Vault, ClamAV Enterprise. |
| **Consulting** | 5% | $260,000 | External API audit and PCI DSS compliance consultants. |
| **Contingency** | 10% | $520,000 | Reserve for timeline extensions and emergency scaling. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Register
The project currently contains significant technical debt inherited from its "hackathon" origins.
1. **Hardcoded Configuration:** $\approx 42$ files contain hardcoded URLs and secrets.
2. **Monolithic Bloat:** The `app.py` file has grown to 4,500 lines; needs decomposition into `routers/` and `services/`.
3. **Lack of Type Hinting:** Approximately 30% of the legacy Python code lacks type hints, leading to intermittent `TypeError` in production.

### Appendix B: PCI DSS Level 1 Compliance Checklist
To maintain the processing of credit card data, the following controls are implemented:
- **Network Segmentation:** The payment processing logic is isolated in a separate Docker network.
- **Encryption:** All card data is encrypted using AES-256 before being passed to the payment gateway.
- **Access Control:** Access to the production database is restricted to the CTO (Chioma Kim) and Astrid Jensen, requiring MFA.
- **Logging:** All access to the `subscriptions` collection is logged in the tamper-evident audit trail.