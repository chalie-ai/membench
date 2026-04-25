# PROJECT SPECIFICATION DOCUMENT: PROJECT RAMPART
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / Reference  
**Owner:** Devika Stein (Engineering Manager)  
**Company:** Duskfall Inc.

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project "Rampart" is a strategic greenfield initiative by Duskfall Inc. aimed at developing a robust, secure, and scalable healthcare records platform tailored for government services. This project represents a significant pivot for Duskfall Inc., as the organization is entering a market sector—government healthcare—where it has no prior operational footprint. The objective is to build a system capable of managing sensitive patient data with high availability, an "offline-first" capability for field workers, and a developer-centric API for third-party government integrations.

**Business Justification**  
The government healthcare sector is currently plagued by legacy monolithic systems that lack interoperability and mobile accessibility. By deploying a modern, three-tier architecture utilizing Python/FastAPI and MongoDB, Rampart will offer a lightweight yet powerful alternative. The core value proposition lies in the platform's ability to synchronize data in low-connectivity environments (Offline-First) and provide seamless identity management through SSO integration. By capturing this market early, Duskfall Inc. can establish itself as a trusted vendor for digital transformation within government health agencies.

**ROI Projection and Success Metrics**  
Given the shoestring budget of $150,000, the project is designed for extreme lean operations. The Return on Investment (ROI) is predicated on a rapid transition from Alpha to a commercially viable product. 

The primary success metrics are:
1.  **Revenue Generation:** The platform must attribute $500,000 in new revenue within the first 12 months of launch. This will be achieved through a tiered subscription model for government agencies and per-user licensing fees.
2.  **Security Integrity:** Zero critical security incidents in the first year. In the healthcare sector, a single data breach can lead to total contract termination and legal liability; thus, security is not just a feature but a business survival requirement.

**Strategic Alignment**  
Rampart aligns with Duskfall Inc.’s broader goal of diversifying its portfolio into high-stakes government contracting. While the budget is tight, the high-trust, low-ceremony nature of the current team allows for rapid iteration. The project will serve as a blueprint for future government service products.

---

## 2. TECHNICAL ARCHITECTURE

Rampart utilizes a traditional three-tier architecture to ensure a clean separation of concerns, facilitating easier maintenance and scaling.

### 2.1 The Three-Tier Model
1.  **Presentation Tier:** A responsive frontend (React/TypeScript) communicating via REST API. It manages the local state for offline-first functionality using IndexedDB.
2.  **Business Logic Tier (Application Layer):** A Python-based backend using the FastAPI framework. This layer handles request validation, business rules, authentication, and asynchronous task orchestration via Celery.
3.  **Data Tier:** A MongoDB cluster providing a flexible, document-oriented schema capable of handling the varied and evolving nature of healthcare records.

### 2.2 Technical Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI (Asynchronous)
- **Database:** MongoDB 6.0 (Self-hosted)
- **Task Queue:** Celery with Redis as the message broker
- **Containerization:** Docker Compose for orchestration across all environments
- **Deployment:** Continuous Deployment (CD) pipeline where merged PRs trigger automatic deployment to production.

### 2.3 ASCII Architecture Diagram
```text
[ CLIENT LAYER ]          [ APPLICATION LAYER ]          [ DATA LAYER ]
+----------------+        +---------------------+        +-----------------+
| Web Browser     | <----> | FastAPI Gateways    | <----> | MongoDB Cluster  |
| (React/TS)      |        | (Auth/Validation)  |        | (Patient Docs)   |
+----------------+        +----------^----------+        +-----------------+
       |                             |                             |
       | [Local Storage]             | [Celery Workers]            | [Backups]
       +-----------------------------+----------------------------+
                             | (Redis Broker) |
                             +----------------+
```

### 2.4 Infrastructure Philosophy
The system is self-hosted to maintain strict control over data residency, a common requirement for government services. By avoiding managed cloud services (like Atlas or AWS Lambda), the team minimizes monthly recurring costs to stay within the $150,000 budget.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Not Started

**Description:**  
Healthcare providers often operate in "dead zones" (rural clinics, emergency transport). Rampart must allow users to create, read, and update healthcare records without an active internet connection.

**Technical Implementation:**  
The frontend will implement a "Local-First" approach using IndexedDB. When a user performs an action offline, the change is committed to a local queue. A "Sync Manager" service will monitor the network status using the `navigator.onLine` API. Once a connection is re-established, the Sync Manager will push the queued changes to the backend using a timestamp-based reconciliation strategy.

**Conflict Resolution:**  
To prevent data loss, Rampart will use a "Last Write Wins" (LWW) strategy for simple fields and a "Version Vector" approach for complex medical histories. If two providers edit the same record offline, the system will flag the record for manual review by the administrator if the timestamps differ by less than 5 seconds.

**User Experience:**  
Users will see a "Syncing..." status indicator in the header. An "Offline Mode" banner will appear when the heartbeat to the FastAPI server fails, notifying the user that their changes are being saved locally.

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Design

**Description:**  
To integrate with other government systems, Rampart provides a public-facing REST API. This allows third-party agencies to pull patient records (with permission) and push diagnostic data.

**Versioning Strategy:**  
The API will use URI-based versioning (e.g., `/api/v1/patients`). This ensures that when breaking changes are introduced in `v2`, existing government integrations do not break. Versions will be supported for a minimum of 18 months.

**Sandbox Environment:**  
A dedicated sandbox environment (`sandbox-api.rampart.gov`) will be provided. This environment mirrors production but contains synthetic, anonymized data. It allows third-party developers to test their integrations without risking real patient data.

**Authentication:**  
API access is managed via API Keys and OAuth2 Client Credentials flow. Each key is scoped to specific resources (e.g., `read:patients`, `write:records`).

### 3.3 SSO Integration (SAML and OIDC)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**  
Government employees must use their existing corporate credentials to log in. Rampart must support Security Assertion Markup Language (SAML 2.0) and OpenID Connect (OIDC).

**Technical Implementation:**  
The backend will integrate `python3-saml` and `authlib`. The system will act as a Service Provider (SP), redirecting users to the government’s Identity Provider (IdP). Upon successful authentication, the IdP returns a signed assertion/token containing the user's unique identifier and role.

**Mapping and Provisioning:**  
Upon the first successful SSO login, Rampart will "Just-In-Time" (JIT) provision a user account in MongoDB, mapping the IdP roles (e.g., "MD_LEVEL_1") to internal Rampart roles ("Clinical_Admin").

**Failure Recovery:**  
A secondary "Emergency Admin" account (non-SSO) will be maintained via an encrypted vault to ensure the system remains accessible if the IdP goes offline.

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Blocked

**Description:**  
To protect the self-hosted infrastructure from DDoS attacks or inefficient third-party scripts, the API must implement strict rate limiting and provide transparency into usage.

**Rate Limiting Logic:**  
Using a "Token Bucket" algorithm implemented in Redis, the system will limit requests based on the API key. 
- **Tier 1 (Standard):** 1,000 requests/hour.
- **Tier 2 (Premium):** 10,000 requests/hour.
When a limit is exceeded, the API returns a `429 Too Many Requests` response with a `Retry-After` header.

**Analytics Pipeline:**  
Every API request will trigger an asynchronous Celery task that logs the endpoint, response time, and consumer ID to an `api_logs` collection in MongoDB. A dashboard will be built for administrators to visualize spikes in traffic and identify the most utilized endpoints.

**Blocker Note:**  
This feature is currently blocked pending the finalization of the Redis cluster memory allocation, as the current server is running low on RAM.

### 3.5 Real-time Collaborative Editing
**Priority:** High | **Status:** Not Started

**Description:**  
Medical records are often updated by multiple specialists (e.g., a nurse and a doctor) simultaneously. Rampart requires a way to edit a patient record in real-time without overwriting changes.

**Implementation Detail:**  
The system will utilize WebSockets via FastAPI's `WebSocket` class. When a user opens a record, they join a "Room" associated with that Patient ID. All keystrokes are transmitted as "Ops" (Operations) based on a simplified Operational Transformation (OT) framework.

**Conflict Resolution:**  
The server acts as the single source of truth. It sequences all incoming Ops and broadcasts them to all connected clients. If two users edit the same character, the server's sequence determines the final state.

**Performance Optimization:**  
To prevent WebSocket flooding, updates are debounced on the client side and batched into 100ms windows before being sent to the server.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 Patient Management

**Endpoint:** `GET /patients/{patient_id}`  
**Description:** Retrieve full medical profile for a patient.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:** `200 OK`
```json
{
  "patient_id": "PAT-9928",
  "name": "John Doe",
  "dob": "1985-05-12",
  "records": ["REC-1", "REC-2"],
  "last_updated": "2023-10-20T14:00:00Z"
}
```

**Endpoint:** `POST /patients`  
**Description:** Create a new patient record.  
**Request:** 
```json
{
  "name": "Jane Smith",
  "dob": "1990-01-01",
  "government_id": "GOV-12345"
}
```
**Response:** `201 Created` | `{ "patient_id": "PAT-9929" }`

### 4.2 Medical Records

**Endpoint:** `POST /records/{patient_id}`  
**Description:** Add a clinical note or observation.  
**Request:** 
```json
{
  "clinician_id": "DOC-55",
  "note": "Patient reports mild hypertension.",
  "timestamp": "2023-10-24T09:00:00Z"
}
```
**Response:** `201 Created` | `{ "record_id": "REC-882" }`

**Endpoint:** `PUT /records/{record_id}`  
**Description:** Update an existing record.  
**Request:** `{ "note": "Updated: Hypertension stabilized." }`  
**Response:** `200 OK`

### 4.3 Authentication & Identity

**Endpoint:** `POST /auth/sso/saml`  
**Description:** Initiates the SAML handshake.  
**Request:** `{ "idp_entity_id": "gov-idp.service.gov" }`  
**Response:** `302 Redirect` to IdP Login Page.

**Endpoint:** `POST /auth/token/refresh`  
**Description:** Refreshes an expired JWT.  
**Request:** `{ "refresh_token": "xyz123..." }`  
**Response:** `200 OK` | `{ "access_token": "new_jwt...", "expires_in": 3600 }`

### 4.4 System & Analytics

**Endpoint:** `GET /analytics/usage`  
**Description:** Returns API usage stats for the current authenticated key.  
**Request:** Header `Authorization: Bearer <token>`  
**Response:** `200 OK`
```json
{
  "total_requests": 4500,
  "rate_limit_remaining": 550,
  "period": "2023-10-24"
}
```

**Endpoint:** `GET /health`  
**Description:** Liveness and readiness probe for Docker/K8s.  
**Response:** `200 OK` | `{ "status": "healthy", "db": "connected", "redis": "connected" }`

---

## 5. DATABASE SCHEMA (MongoDB)

Since Rampart uses MongoDB, the "tables" are collections. Relationships are maintained via references (Manual Refs) to avoid heavy `$lookup` operations.

### 5.1 Collections Overview

| Collection Name | Description | Primary Key | Key Fields |
| :--- | :--- | :--- | :--- |
| `users` | System users & roles | `_id` | `email`, `role`, `sso_provider_id`, `last_login` |
| `patients` | Core patient demographic data | `_id` | `full_name`, `dob`, `gov_id`, `created_at` |
| `medical_records` | Clinical notes/observations | `_id` | `patient_id` (ref), `doctor_id` (ref), `content`, `timestamp` |
| `audit_logs` | Immutable change history | `_id` | `user_id` (ref), `action`, `resource_id`, `timestamp` |
| `api_keys` | Third-party access tokens | `_id` | `key_hash`, `owner_id` (ref), `scope`, `rate_limit_tier` |
| `sync_queues` | Pending offline updates | `_id` | `user_id` (ref), `payload`, `retry_count`, `status` |
| `sessions` | Active user sessions | `_id` | `user_id` (ref), `token`, `ip_address`, `expiry` |
| `organizations` | Government agencies | `_id` | `agency_name`, `billing_contact`, `region` |
| `attachments` | Metadata for uploaded files | `_id` | `record_id` (ref), `file_path`, `mime_type`, `size` |
| `system_configs` | Global app settings | `_id` | `config_key`, `config_value`, `updated_by` |

### 5.2 Relationships
- **Patients $\to$ Medical Records:** One-to-Many. A patient has many records.
- **Users $\to$ Medical Records:** One-to-Many. A doctor/nurse creates many records.
- **Users $\to$ API Keys:** One-to-Many. A user may generate multiple keys for different integrations.
- **Organizations $\to$ Users:** One-to-Many. Each user belongs to one government agency.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### Development (`dev`)
- **Purpose:** Active feature development and unit testing.
- **Infrastructure:** Local Docker Compose on developer machines.
- **Deployment:** Manual.
- **Data:** Mock data generated via Python scripts.

#### Staging (`staging`)
- **Purpose:** Integration testing and QA verification.
- **Infrastructure:** A single virtual private server (VPS) mirroring production specs.
- **Deployment:** Automatic deployment upon merge to `develop` branch.
- **Data:** Anonymized production snapshots.

#### Production (`prod`)
- **Purpose:** Live government services.
- **Infrastructure:** High-availability cluster of self-hosted Linux servers.
- **Deployment:** Continuous Deployment. Every PR merged to `main` is automatically deployed.
- **Data:** Live, encrypted patient data.

### 6.2 CI/CD Pipeline
We utilize a simplified GitHub Actions pipeline:
1. **Lint/Test:** Runs `flake8` and `pytest`.
2. **Build:** Creates a Docker image with the latest FastAPI code.
3. **Push:** Pushes image to the internal registry.
4. **Deploy:** Signals the production server to `docker-compose pull` and `docker-compose up -d`.

### 6.3 Logging & Monitoring
**Current State:** Technical debt exists; the system lacks structured logging. Production debugging currently requires reading `stdout` via `docker logs`.
**Future State:** Implementation of the ELK stack (Elasticsearch, Logstash, Kibana) to replace stdout reading.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Scope:** Each FastAPI route and business logic function must have a corresponding unit test.
- **Coverage Goal:** 80% coverage.
- **Execution:** Triggered on every PR. Failure blocks the merge.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between FastAPI and MongoDB.
- **Approach:** Using a dedicated "Test MongoDB" container. Tests verify that data is correctly persisted and retrieved, ensuring that schema-less documents still adhere to the expected application-level structure.
- **Focus:** Focuses heavily on the SSO handshake and the Celery task queue.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright
- **Scope:** Critical user paths: "Login $\to$ Find Patient $\to$ Edit Record $\to$ Sync Offline".
- **Execution:** Weekly regression runs in the Staging environment.

### 7.4 Penetration Testing
Given the lack of a formal compliance framework (e.g., HIPAA/GDPR), Rampart relies on **Quarterly Penetration Testing**. An external security firm is hired every three months to attempt to breach the system, with the results used to prioritize the security backlog.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory requirements change mid-dev | High | High | Hire a specialized government contractor to reduce "bus factor" and provide guidance. | Devika |
| R-02 | Project sponsor rotates out of role | Medium | High | Assign a dedicated owner to track and resolve stakeholder alignment. | Devika |
| R-03 | Budget exhaustion due to hardware costs | Medium | Medium | Use self-hosted open-source tools; strict scrutiny of every dollar spent. | Devika |
| R-04 | Data loss during offline sync | Low | Critical | Implement version vectors and mandatory manual review for conflicts. | Dayo |
| R-05 | Performance degradation at scale | Medium | Medium | Establish performance benchmarks by 2025-03-15. | Vivaan |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required.
- **High:** Priority mitigation.
- **Medium:** Monitor and manage.
- **Low:** Accept risk.

---

## 9. TIMELINE

The project follows a phased approach with three primary milestones.

### Phase 1: Foundation & Core Identity (Oct 2023 - March 2025)
- **Focus:** SSO Integration, Database Schema, Basic API.
- **Dependency:** SAML/OIDC provider access from government partners.
- **Milestone 1:** Performance benchmarks met (Target: 2025-03-15).

### Phase 2: Alpha Expansion (March 2025 - May 2025)
- **Focus:** Offline-first mode, Collaborative editing, Sandbox API.
- **Dependency:** Stable core API.
- **Milestone 2:** Internal alpha release (Target: 2025-05-15).

### Phase 3: Hardening & Launch (May 2025 - July 2025)
- **Focus:** Rate limiting, Analytics, Final Security Audit.
- **Dependency:** Alpha feedback loop.
- **Milestone 3:** Security audit passed (Target: 2025-07-15).

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team dynamic, decisions are made in Slack. Below are the three most critical decision threads.

### Thread 1: The "Budget vs. Managed" Debate
**Participants:** Devika, Dayo
**Date:** 2023-11-02
- **Dayo:** "Can we please use MongoDB Atlas? Managing our own cluster is a nightmare and we're going to spend more on engineering hours than we save on the subscription."
- **Devika:** "Budget is $150k. We're on a shoestring. The sponsor is watching every cent. We go self-hosted on Docker. We'll deal with the overhead."
- **Decision:** Self-hosted MongoDB via Docker Compose. No cloud managed services.

### Thread 2: The SSO Blocker
**Participants:** Devika, Dayo, Vivaan
**Date:** 2023-12-15
- **Vivaan:** "The SAML integration is failing for the 'Dept of Health' test case. It's a launch blocker."
- **Dayo:** "The IdP is sending an unexpected attribute format for the user role."
- **Devika:** "Fix this first. I don't care about the collaborative editing feature right now. SSO is the only thing that matters for the review."
- **Decision:** Pivot all backend resources to resolve SAML attribute mapping.

### Thread 3: Logging Debt
**Participants:** Devika, Petra
**Date:** 2024-01-20
- **Petra:** "I spent 4 hours today just grepping through `docker logs` to find why the sync failed for one user. We really need structured logging."
- **Devika:** "I agree, but we're pushing for the alpha. For now, just make sure you're including the `patient_id` in the print statements. We'll add a logging framework after the security audit."
- **Decision:** Structured logging postponed. Continue using stdout for now.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000  
**Currency:** USD

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $110,000 | Partial allocation for the team of 8 (internal cost center). |
| **Infrastructure** | $15,000 | Self-hosted VPS rentals and hardware disks. |
| **Tools & Licenses** | $10,000 | Security scanning tools, IDE licenses, SAML testing tools. |
| **Contractor Fee** | $10,000 | Specialist contractor for regulatory/compliance guidance. |
| **Contingency** | $5,000 | Emergency hardware replacement or urgent API tools. |

**Financial Constraint:** Every expense over $200 requires direct approval from Devika Stein.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Algorithm
The "Last Write Wins" (LWW) strategy for Rampart is implemented as follows:
1. Each document field contains a hidden metadata field: `_last_modified_timestamp`.
2. When a sync request arrives, the server compares the incoming timestamp with the existing timestamp.
3. If `incoming_timestamp > existing_timestamp`, the field is updated.
4. If timestamps are identical, the server prioritizes the update based on the alphabetical order of the user's UUID.

### Appendix B: Penetration Testing Checklist
The quarterly audit will focus on the following vectors:
- **JWT Hijacking:** Testing for weak signing keys or lack of expiration.
- **BOLA (Broken Object Level Authorization):** Attempting to access `/patients/{id}` using a valid token for a different patient.
- **SAML XML Signature Wrapper Attacks:** Ensuring the SAML assertion cannot be modified after signing.
- **MongoDB Injection:** Testing API inputs for NoSQL injection patterns.
- **Rate Limit Bypass:** Attempting to bypass the Token Bucket using header spoofing.