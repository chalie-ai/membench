# PROJECT SPECIFICATION: PROJECT PARAPET
**Document Version:** 1.0.4  
**Status:** Baseline  
**Classification:** Internal/Confidential  
**Date:** October 24, 2025  
**Project Owner:** Adaeze Vasquez-Okafor  

---

## 1. EXECUTIVE SUMMARY

**Project Parapet** is a strategic architectural migration and API Gateway implementation for Deepwell Data, specifically designed to launch a new product vertical within the telecommunications sector. The project is driven by a high-value commitment from a single enterprise client—a Tier-1 government-adjacent telecom provider—who has agreed to a contract value of $2,000,000 annually upon successful delivery of the specified feature set.

The core objective of Parapet is to transition from a fragmented, monolithic legacy structure to a modern micro-frontend architecture supported by a robust API Gateway. This migration is not merely a technical upgrade but a business necessity to ensure scalability, maintainability, and the ability to meet stringent government security requirements. Because the project is currently unfunded—bootstrapped using existing team capacity—the operational efficiency of the four-person team is paramount.

**Business Justification:**
Deepwell Data currently faces significant technical friction due to "stack drift," where three disparate technology stacks are operating in parallel. This creates silos, increases the cost of feature development, and introduces critical vulnerabilities. By implementing the Parapet Gateway, Deepwell Data will abstract these legacy complexities, allowing for a seamless migration to microservices without disrupting the enterprise client’s operations.

**ROI Projection:**
The immediate Return on Investment (ROI) is anchored by the $2M annual contract. However, the long-term ROI is projected based on:
1. **Reduction in Operational Overhead:** By normalizing the three existing stacks into a unified Gateway, we anticipate a 30% reduction in developer hours spent on cross-stack debugging.
2. **Market Expansion:** Achieving FedRAMP authorization allows Deepwell Data to penetrate the federal government telecommunications market, a sector with an estimated Total Addressable Market (TAM) of $500M for our specific product vertical.
3. **Client Retention:** The implementation of high-priority features (2FA, Collaborative Editing, and A/B Testing) will lock in the enterprise client by embedding Deepwell Data’s tools into their core operational workflow.

The project's success is binary: either we achieve the FedRAMP audit and deliver the feature set to secure the $2M annual payment, or we risk the loss of the client and continued stagnation of the legacy technical debt.

---

## 2. TECHNICAL ARCHITECTURE

Project Parapet utilizes a **Micro-Frontend (MFE) Architecture** combined with an **API Gateway Pattern**. This approach allows independent team ownership of specific functional modules, ensuring that updates to the "Advanced Search" module do not inadvertently crash the "Collaborative Editing" module.

### 2.1 The "Tri-Stack" Integration
The project must interoperate across three inherited stacks:
1. **Legacy Stack A:** Java/Spring Boot 2.1 (running on on-premise VMs).
2. **Legacy Stack B:** Node.js 12 (running on early Kubernetes clusters).
3. **Legacy Stack C:** Python/Django 3.2 (running as a set of standalone Lambda functions).

The Parapet Gateway acts as the "Normalization Layer," handling request routing, protocol translation (REST to gRPC where applicable), and identity propagation.

### 2.2 Architecture Diagram (ASCII Representation)

```text
[ USER BROWSER / MFE LAYER ]
       |
       | HTTPS / JSON / WebSocket
       v
[ PARAPET API GATEWAY (Kong/Envoy) ] <--- [ AUTH SERVICE (FedRAMP Compliant) ]
       |                                      |
       |---------------------------------------|
       |               |                      |
       v               v                      v
[ MICROSERVICE 1 ] [ MICROSERVICE 2 ] [ MICROSERVICE 3 ]
(Search/Index)      (Collab/Edit)      (Billing/Usage)
       |               |                      |
       v               v                      v
[ ELASTICSEARCH ]  [ REDIS/POSTGRES ]   [ LEGACY DBs ]
       ^               ^                      ^
       |               |                      |
       ----------------------------------------
                (Legacy Stack A, B, & C)
```

### 2.3 Security & FedRAMP Compliance
To meet FedRAMP authorization, the architecture implements:
- **FIPS 140-2 Validated Encryption:** All data at rest and in transit must use validated cryptographic modules.
- **Strict IAM Policies:** Zero-trust architecture where the Gateway validates JWTs issued by the central identity provider.
- **Audit Logging:** Every request passing through the Gateway is logged to a write-once-read-many (WORM) storage system for forensic analysis.

### 2.4 Deployment Strategy
We employ a **Blue-Green Deployment** strategy via GitHub Actions. 
- **Green Environment:** The current production version.
- **Blue Environment:** The new version being deployed.
Traffic is shifted via the Load Balancer only after the QA Engineer (Sage Mahmoud-Reyes) signs off on the smoke tests in the Blue environment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering and Full-Text Indexing
*Priority: Medium | Status: In Design*

**Functional Overview:**
The search system must allow enterprise users to query millions of telecommunications records across the three legacy stacks. Unlike basic keyword search, this requires "faceted filtering," allowing users to drill down by carrier, region, date range, and signal strength.

**Technical Implementation:**
We will implement an **Elasticsearch 8.11** cluster. The Gateway will intercept search requests and route them to a dedicated "Search Microservice." This service will employ a "CQRS" (Command Query Responsibility Segregation) pattern; while data resides in the legacy databases, a synchronization worker will pipe updates into Elasticsearch in near real-time.

**Detailed Requirements:**
- **Full-Text Indexing:** Support for stemming, lemmatization, and fuzzy matching (Levenshtein distance of 2).
- **Faceted Navigation:** The API must return "aggregations" alongside search results. For example, if a user searches for "5G outages," the response should include a facet showing the count of outages per city (e.g., New York: 45, Chicago: 12).
- **Query DSL:** Implementation of a complex JSON-based query language to allow the frontend to build nested boolean queries (AND/OR/NOT).
- **Performance Target:** P99 latency for search queries must be $< 200\text{ms}$.

**User Story:**
"As a Network Administrator, I want to search for 'intermittent signal' in 'Texas' during 'July 2025' and immediately see a breakdown of affected hardware models so I can identify a faulty batch of routers."

---

### 3.2 A/B Testing Framework (Feature Flag Integration)
*Priority: High | Status: In Progress*

**Functional Overview:**
To ensure the $2M client is satisfied with new iterations, we cannot simply "push to prod." We need a robust A/B testing framework baked into our feature flag system (using an internal implementation of the Unleash/LaunchDarkly pattern).

**Technical Implementation:**
The framework will exist as a middleware component within the Parapet Gateway. When a request arrives, the Gateway checks the user's `tenant_id` and `user_id` against the "Experimentation Table" in PostgreSQL. 

**Detailed Requirements:**
- **Bucketization:** Users must be deterministically assigned to "Control" or "Treatment" groups using a hash of their UserID (e.g., `hash(userID + experimentID) % 100`).
- **Percentage Rollouts:** Ability to shift traffic from 0% to 100% in increments of 1% without redeploying code.
- **Metric Tracking:** Integration with a telemetry service to track "Conversion Rate" or "Task Completion Time" for each bucket.
- **Conflict Resolution:** Logic to handle "Overlapping Experiments"—where a user might be in Experiment A (New UI) and Experiment B (New Search Algorithm) simultaneously.

**User Story:**
"As a Product Manager, I want to deploy the new Collaborative Editor to only 10% of the pilot users to ensure it doesn't cause database deadlocks before a full rollout."

---

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
*Priority: High | Status: Blocked*

**Functional Overview:**
Due to the government nature of the client, standard SMS-based 2FA is insufficient. We require support for FIDO2/WebAuthn hardware keys (e.g., YubiKey).

**Technical Implementation:**
This feature is currently **blocked** by the integration partner's identity provider, which lacks a stable WebAuthn endpoint. Once unblocked, the system will implement a challenge-response mechanism. The server sends a random challenge; the hardware key signs it with a private key; the server verifies it with the stored public key.

**Detailed Requirements:**
- **Hardware Compatibility:** Full support for YubiKey 5 series and Google Titan keys.
- **Fallback Mechanisms:** Support for TOTP (Time-based One-Time Password) via apps like Google Authenticator as a secondary backup.
- **Recovery Codes:** Generation of ten 16-character alphanumeric recovery codes upon enrollment.
- **Session Binding:** 2FA must be re-validated every 12 hours for administrative accounts.

**User Story:**
"As a Security Auditor, I want to ensure that no one can access the telecommunications backbone without a physical hardware key, mitigating the risk of credential theft via phishing."

---

### 3.4 Real-time Collaborative Editing with Conflict Resolution
*Priority: High | Status: In Design*

**Functional Overview:**
Users must be able to edit network configuration files simultaneously. If two users change the same line, the system must resolve the conflict without data loss.

**Technical Implementation:**
We will implement **CRDTs (Conflict-free Replicated Data Types)**, specifically using the LWW-Element-Set (Last-Write-Wins) for simple fields and a Sequence CRDT for text areas. Communication will be handled via WebSockets managed by the Parapet Gateway.

**Detailed Requirements:**
- **Latency Compensation:** Implementation of "Optimistic UI" updates where the change is reflected locally before the server acknowledges it.
- **Presence Indicators:** Real-time "User X is typing..." indicators and cursor tracking using a Redis Pub/Sub backend.
- **Versioning:** Every single mutation must be stored in a history table, allowing users to "Time Travel" back to any previous state.
- **Locking Mechanism:** While CRDTs handle conflict, a "Soft Lock" will be implemented for critical system fields to prevent erratic configuration changes.

**User Story:**
"As a Network Engineer, I want to coordinate a configuration change with a colleague in real-time, seeing their cursor and changes instantly, so we don't accidentally overwrite each other's work."

---

### 3.5 API Rate Limiting and Usage Analytics
*Priority: Medium | Status: Blocked*

**Functional Overview:**
To protect the legacy stacks from being overwhelmed, the Gateway must enforce strict rate limits. Additionally, we must track usage to justify the $2M annual fee.

**Technical Implementation:**
This is currently **blocked** by third-party API rate limits during testing. We intend to implement a **Leaky Bucket Algorithm** at the Gateway level.

**Detailed Requirements:**
- **Tiered Limiting:** Different limits for different API keys (e.g., "Basic: 100 req/min", "Enterprise: 5000 req/min").
- **Burst Handling:** Allow for short bursts of traffic (up to 20% over limit) using a token bucket approach.
- **Analytics Dashboard:** A Prometheus/Grafana dashboard showing "Top 10 Most Active Endpoints" and "Error Rate per Client."
- **Header Signaling:** The API must return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

**User Story:**
"As a System Administrator, I want to limit the integration partner's API calls to 1,000 per minute so that their buggy scripts don't trigger a Denial-of-Service (DoS) event on our legacy Java stack."

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 Search Endpoint
- **Path:** `GET /search/records`
- **Description:** Performs faceted full-text search.
- **Request Params:** `q` (string), `facet_region` (string), `facet_carrier` (string), `page` (int).
- **Response Example:**
```json
{
  "results": [
    {"id": "REC-101", "status": "down", "region": "North-East"},
    {"id": "REC-102", "status": "intermittent", "region": "South-West"}
  ],
  "facets": {
    "regions": {"North-East": 45, "South-West": 12},
    "carriers": {"Verizon": 20, "AT&T": 25}
  },
  "total": 57
}
```

### 4.2 Feature Flag Toggle
- **Path:** `POST /flags/toggle`
- **Description:** Changes the status of a feature flag for a specific user group.
- **Request Body:** `{"flag_id": "collab_editing_v2", "status": "enabled", "percentage": 15}`
- **Response Example:** `{"status": "success", "updated_at": "2026-08-12T10:00:00Z"}`

### 4.3 2FA Enrollment
- **Path:** `POST /auth/2fa/enroll`
- **Description:** Registers a new hardware key.
- **Request Body:** `{"userId": "user_99", "publicKey": "MFkwEwYHKoG..."}`
- **Response Example:** `{"status": "registered", "key_id": "key_abc123"}`

### 4.4 Collaborative Document Update
- **Path:** `PATCH /collab/docs/{docId}`
- **Description:** Sends a CRDT mutation for a document.
- **Request Body:** `{"operation": "insert", "index": 45, "value": "a", "timestamp": 1712345678}`
- **Response Example:** `{"status": "acknowledged", "version": 1402}`

### 4.5 Usage Analytics Query
- **Path:** `GET /analytics/usage/{clientId}`
- **Description:** Retrieves API consumption data for a specific client.
- **Request Params:** `start_date` (ISO8601), `end_date` (ISO8601).
- **Response Example:** `{"clientId": "client_01", "total_requests": 1500000, "avg_latency": "45ms"}`

### 4.6 Rate Limit Reset
- **Path:** `POST /admin/rate-limits/reset`
- **Description:** Manually resets the quota for a client (Admin only).
- **Request Body:** `{"clientId": "client_01"}`
- **Response Example:** `{"status": "quota_reset"}`

### 4.7 Record Detail Fetch
- **Path:** `GET /records/{recordId}`
- **Description:** Fetches full details of a telecom record from legacy stacks.
- **Response Example:** `{"id": "REC-101", "timestamp": "2026-01-01", "metric": "dBm -90"}`

### 4.8 User Session Validation
- **Path:** `POST /auth/validate`
- **Description:** Validates the current JWT and FedRAMP compliance status.
- **Request Body:** `{"token": "eyJhbG..."}`
- **Response Example:** `{"valid": true, "scope": "admin", "fedramp_level": "high"}`

---

## 5. DATABASE SCHEMA

The project uses a hybrid approach: PostgreSQL for relational data and Redis for real-time state.

### 5.1 Tables and Relationships

| Table Name | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- |
| `users` | `user_id` (PK), `email`, `password_hash` | 1:M with `auth_keys` | Primary user identity store. |
| `auth_keys` | `key_id` (PK), `user_id` (FK), `pub_key` | M:1 with `users` | Stores FIDO2 public keys. |
| `tenants` | `tenant_id` (PK), `company_name`, `tier` | 1:M with `users` | Enterprise client mapping. |
| `feature_flags` | `flag_id` (PK), `name`, `is_global` | M:M with `tenants` | Definition of all feature flags. |
| `flag_assignments`| `assignment_id` (PK), `flag_id` (FK), `tenant_id` (FK), `percentage` | M:1 with `flags` | Controls rollout percentages. |
| `documents` | `doc_id` (PK), `title`, `owner_id` (FK) | 1:M with `doc_versions` | Collaborative doc metadata. |
| `doc_versions` | `version_id` (PK), `doc_id` (FK), `delta_blob` | M:1 with `documents` | Stores CRDT mutation history. |
| `api_logs` | `log_id` (PK), `clientId` (FK), `endpoint`, `latency` | M:1 with `tenants` | Audit trail for FedRAMP. |
| `rate_limits` | `limit_id` (PK), `tenant_id` (FK), `max_req_per_min` | M:1 with `tenants` | Quota definitions. |
| `search_indices` | `index_id` (PK), `stack_source`, `last_sync` | N/A | Tracks sync state with legacy stacks. |

**Critical Schema Note:** To resolve the technical debt regarding date formats, all new tables *must* use `TIMESTAMP WITH TIME ZONE` (ISO 8601). The normalization layer in the Gateway will convert legacy formats (e.g., `MM/DD/YYYY` and `YYYY-MM-DD`) into this standard before writing to the new schema.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Definitions

#### 6.1.1 Development (Dev)
- **Purpose:** Sandbox for the 4-person team.
- **Infrastructure:** Local Docker Compose and a shared "Dev" namespace in Kubernetes.
- **Data:** Anonymized subsets of legacy data.
- **Deployment:** Triggered by merge to `develop` branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production testing and FedRAMP audit preparation.
- **Infrastructure:** Mirror of Production (identical AWS GovCloud region).
- **Data:** Full-scale anonymized data.
- **Deployment:** Triggered by release candidate tags (`rc-v1.x`).

#### 6.1.3 Production (Prod)
- **Purpose:** Live environment for the enterprise client.
- **Infrastructure:** High-availability Kubernetes cluster across three availability zones.
- **Deployment:** Blue-Green deployment via GitHub Actions.

### 6.2 CI/CD Pipeline
1. **Commit:** Developer pushes code to GitHub.
2. **Test:** GitHub Actions runs unit tests (Jest/JUnit) and linting.
3. **Build:** Docker image is built and pushed to Amazon ECR.
4. **Deploy (Staging):** Image is deployed to the Staging cluster.
5. **QA Sign-off:** Sage Mahmoud-Reyes executes E2E tests.
6. **Promote (Prod):** Deployment to the "Blue" environment $\rightarrow$ Traffic switch $\rightarrow$ Monitoring $\rightarrow$ "Green" decommission.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic in microservices (e.g., CRDT resolution logic).
- **Tooling:** Jest (Node), PyTest (Python), Mockito (Java).
- **Requirement:** 80% minimum code coverage for all new Parapet services.

### 7.2 Integration Testing
- **Focus:** Communication between the Gateway and the three legacy stacks.
- **Approach:** Contract Testing using **Pact**. This ensures that if the Legacy Java stack changes its response format, the Gateway build fails immediately.
- **Validation:** Testing the "Normalization Layer" to ensure all date formats are correctly converted to ISO 8601.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "User logs in via 2FA $\rightarrow$ Searches for record $\rightarrow$ Edits record collaboratively").
- **Tooling:** Playwright.
- **Execution:** Run against the Staging environment before every production release.

### 7.4 Security Testing (FedRAMP Focused)
- **Penetration Testing:** Monthly scans using OWASP ZAP.
- **Audit Logs:** Verification that every API call generates a non-mutable log entry.
- **FIPS Validation:** Verification that all TLS connections use approved cipher suites.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding 'small' features. | High | High | All new requests must be documented in JIRA and escalated to the Steering Committee for additional funding/capacity. |
| R-02 | Integration partner API is undocumented and buggy. | High | Medium | Assign Petra Vasquez-Okafor as the dedicated "Partner Liaison" to track bugs and manually document endpoints. |
| R-03 | Third-party API rate limits blocking testing. | High | High | Implement a "Mock Gateway" for testing that simulates the partner API without making actual network calls. |
| R-04 | Failure to pass FedRAMP audit on first attempt. | Medium | Critical | Engage an external FedRAMP consultant for a "Pre-Audit" review in August 2026. |
| R-05 | Team burnout due to unfunded bootstrapping. | Medium | High | Strict adherence to the 4-person capacity; no "crunch time" without documented overtime compensation. |

**Probability/Impact Matrix:**
- **Critical:** High Probability / High Impact $\rightarrow$ Immediate Action.
- **High:** High Probability / Medium Impact $\rightarrow$ Weekly Monitoring.
- **Medium:** Low Probability / High Impact $\rightarrow$ Contingency Plan.

---

## 9. TIMELINE & GANTT DESCRIPTION

**Project Duration:** October 2025 – November 2026

### Phase 1: Foundation & Gateway Setup (Oct 2025 - Feb 2026)
- **Dependencies:** None.
- **Activities:** Setup of the API Gateway, definition of the Normalization Layer, and initial mapping of legacy stacks.
- **Key Milestone:** Gateway able to route traffic to all three legacy stacks.

### Phase 2: High Priority Feature Dev (Mar 2026 - July 2026)
- **Dependencies:** Phase 1 completion.
- **Activities:** Implementation of A/B Testing framework, 2FA (pending unblock), and Collaborative Editing.
- **Key Milestone:** **Architecture Review Complete (2026-07-15).**

### Phase 3: Beta Testing & Refinement (July 2026 - Sept 2026)
- **Dependencies:** High Priority features stable in Staging.
- **Activities:** Onboarding 10 pilot users, monitoring feature adoption, fixing "buggy" integration partner issues.
- **Key Milestone:** **External Beta Release (2026-09-15).**

### Phase 4: Finalization & Audit (Sept 2026 - Nov 2026)
- **Dependencies:** Beta feedback incorporated.
- **Activities:** Final FedRAMP audit, full-text search indexing optimization, final documentation.
- **Key Milestone:** **Internal Alpha Release (2026-11-15).**

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff
**Date:** 2025-10-28  
**Attendees:** Adaeze, Petra, Callum, Sage  
- Bootstrap mode confirmed. No new hires.
- Adaeze: "We need to be careful with the $2M client. They want everything yesterday."
- Petra: "The date formats are a mess. I found three different ones in the Java stack alone."
- Callum: "Coming from Montana, I can advise on the external API stuff, but the partner's docs are basically non-existent."
- Decision: All tasks MUST go through JIRA. No "slack-based" assignments.

### Meeting 2: Technical Deep Dive (The "Date Problem")
**Date:** 2025-11-15  
**Attendees:** Adaeze, Petra, Callum, Sage  
- Discussion on normalization.
- Petra: "If we don't fix the dates at the Gateway, the Search index will be useless."
- Sage: "I can't write a test case for a date if I don't know if it's US or ISO format."
- Callum: "The partner API sends dates in Unix epoch sometimes, and strings other times."
- Decision: Create a `DateNormalizationService` as part of the Gateway middleware.

### Meeting 3: Blockers & FedRAMP Sync
**Date:** 2026-01-10  
**Attendees:** Adaeze, Petra, Callum, Sage  
- 2FA is blocked. Partner API is returning 429s (Too Many Requests) during basic tests.
- Adaeze: "We need to escalate the rate limits. We can't test the 2FA flow if we're blocked."
- Sage: "I've tried to mock it, but the partner's response is too erratic."
- Callum: "I'll call my contact at the partner's office in Bozeman and see if they can whitelist our staging IP."
- Decision: Move 2FA and Rate Limiting to "Blocked" status in JIRA.

---

## 11. BUDGET BREAKDOWN

Since the project is unfunded and bootstrapping with existing team capacity, the "Budget" represents the **allocated internal cost center value** (Internal Labor Cost) rather than cash outlay.

| Category | Allocated Cost (Internal) | Description |
| :--- | :--- | :--- |
| **Personnel: Project Lead** | $140,000 | Adaeze Vasquez-Okafor (Salary + Interpreter overhead) |
| **Personnel: Senior Dev** | $160,000 | Petra Vasquez-Okafor (Full-time dev effort) |
| **Personnel: Consultant** | $80,000 | Callum Vasquez-Okafor (External advisory/Montana based) |
| **Personnel: QA Engineer** | $110,000 | Sage Mahmoud-Reyes (Testing & Audit prep) |
| **Infrastructure: AWS GovCloud** | $45,000 | Compute, EKS, RDS, and S3 (est. monthly $3.7k) |
| **Tooling: GitHub/JIRA/ELK** | $12,000 | Licenses for CI/CD and logging |
| **Contingency** | $25,000 | Emergency buffer for third-party API remediation |
| **TOTAL** | **$572,000** | **Projected internal cost to secure $2M revenue** |

---

## 12. APPENDICES

### Appendix A: Date Format Normalization Map
To resolve the technical debt, the following mapping is enforced at the Gateway:

| Source Stack | Format Found | Transformation Logic | Target Format (ISO 8601) |
| :--- | :--- | :--- | :--- |
| Legacy Java | `MM/DD/YYYY` | `SimpleDateFormat` $\rightarrow$ `UTC` | `YYYY-MM-DDTHH:mm:ssZ` |
| Legacy Node | `Epoch (ms)` | `new Date(ms).toISOString()` | `YYYY-MM-DDTHH:mm:ssZ` |
| Legacy Python | `YYYY-MM-DD` | `datetime.strptime` $\rightarrow$ `UTC` | `YYYY-MM-DDTHH:mm:ssZ` |
| Partner API | `Mixed/Erratic` | Regex Detection $\rightarrow$ Normalization | `YYYY-MM-DDTHH:mm:ssZ` |

### Appendix B: FedRAMP Evidence Checklist
For the audit (Target: Oct 2026), the team must provide:
1. **System Security Plan (SSP):** Detailed document describing all security controls.
2. **Plan of Action and Milestones (POA&M):** List of known vulnerabilities and the timeline to fix them.
3. **Configuration Management Plan:** Proof that all changes to Production are tracked via GitHub Actions and signed off by the Project Lead.
4. **Continuous Monitoring Plan:** Proof of real-time alerting via Prometheus/Grafana for unauthorized access attempts.