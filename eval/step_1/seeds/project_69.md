Due to the extreme length requirement (6,000–8,000 words), this document is structured as a Comprehensive Technical Specification. It serves as the "Single Source of Truth" (SSOT) for the Drift development team.

***

# PROJECT SPECIFICATION: DRIFT
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Company:** Flintrock Engineering  
**Classification:** Confidential / Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project **Drift** is a greenfield healthcare records platform developed by Flintrock Engineering. While Flintrock has a storied history of engineering excellence, Drift represents a strategic pivot: entering the legal services industry by providing a specialized tool for the management, auditing, and discovery of medical records used in legal litigation. 

The primary objective of Drift is to bridge the gap between raw Electronic Health Record (EHR) data and the evidentiary requirements of legal teams. Legal professionals often struggle with fragmented medical records, lack of version control, and stringent compliance requirements. Drift provides a secure, multi-tenant environment where legal teams can ingest medical records, collaborate on analysis, and maintain a bulletproof audit trail for court admissibility.

### 1.2 Business Justification
The legal-healthcare intersection is a high-barrier-to-entry market. By building a platform that treats healthcare records as "legal evidence" rather than just "patient data," Flintrock Engineering can capture a niche market of personal injury, medical malpractice, and insurance defense firms. 

The decision to build a greenfield product allows the team to avoid the "legacy trap" and implement modern architectural patterns—specifically CQRS and Event Sourcing—which are critical for the audit-heavy nature of legal discovery. The business justification rests on the high Average Revenue Per User (ARPU) typical of legal software and the recurring nature of litigation cycles.

### 1.3 ROI Projection
With a modest budget of $400,000, Flintrock is aiming for an aggressive lean-launch. 
- **Direct Revenue Target:** The goal is to secure 5 mid-sized law firms by Q1 2026, with an estimated Annual Contract Value (ACV) of $50,000 per firm.
- **Projected ROI:** Upon achieving the Milestone 3 beta targets, the projected Year 1 revenue is $250,000, covering over 60% of the initial development cost within the first year of full operation.
- **Long-term Value:** By establishing a footprint in the legal-healthcare sector, Flintrock creates a moat of compliance-certified infrastructure that can be expanded into other highly regulated industries.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
The architecture is designed for speed of delivery and ease of maintenance, prioritizing a "Boring Technology" approach to minimize operational overhead for a distributed team of 15.

- **Application Framework:** Ruby on Rails (v7.1+) monolith.
- **Database:** MySQL 8.0 (Amazon RDS for Heroku).
- **Hosting:** Heroku (Private Spaces for EU data residency).
- **Caching/Queue:** Redis.
- **Feature Management:** LaunchDarkly.
- **State Management:** CQRS (Command Query Responsibility Segregation) implemented via the `rails-event-store` gem.

### 2.2 Architectural Pattern: CQRS and Event Sourcing
Because the platform is used in legal contexts, the "current state" of a medical record is insufficient. We must know *how* the record reached that state. Drift utilizes Event Sourcing for all audit-critical domains (e.g., Record Modifications, Permission Changes).

- **Command Side:** Handles intents (e.g., `UpdateMedicalNoteCommand`). It validates the business logic and persists an event to the `events` table.
- **Query Side:** Projections listen to the event stream and update "Read Models" (flat MySQL tables) optimized for fast retrieval and frontend display.

### 2.3 System Diagram (ASCII Representation)

```text
[ Client Browser ] <--> [ Heroku Load Balancer ]
                                |
                                v
                    [ Rails Monolith (Web) ]
                    /           |           \
      (Commands)   /            |            \  (Queries)
      v           /             |             \      v
[ Command Handler ]      [ Redis Cache ]    [ Read-Only Views ]
      |                                              ^
      v                                              |
[ Event Store (MySQL) ] ---------------------> [ Projection Engine ]
      |                                              |
      +-----> [ Audit Log / Immutable Archive ] <----+
                                |
                        [ LaunchDarkly Flags ]
```

### 2.4 Data Residency and Compliance
To meet GDPR and CCPA requirements, Drift employs a strict data residency strategy. All production shards for EU-based legal firms are hosted on Heroku’s EU-West-1 (Ireland) region. Data isolation is handled at the application layer via a `tenant_id` scoped to every single query, ensuring no cross-pollination of sensitive healthcare data.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-tenant Data Isolation (Priority: Critical)
**Status:** Complete | **Complexity:** High

**Description:** 
This is the foundational bedrock of Drift. Since the platform hosts data for competing law firms, a "leak" between tenants would be a catastrophic business failure. We utilize a shared-infrastructure, logically-separated model.

**Functional Requirements:**
- Every table in the database (excluding global configurations) must contain a `tenant_id` column.
- The application must implement a global scope via the `acts_as_tenant` gem to ensure that all ActiveRecord queries automatically append `WHERE tenant_id = ?`.
- Authentication tokens (JWT) must embed the `tenant_id`, which is validated on every request.
- Administrative "Super-User" access is strictly limited to infrastructure maintenance and does not allow viewing of tenant-specific medical data.

**Technical Implementation:**
The isolation is enforced at the Controller level via a `before_action` filter that sets the current tenant based on the authenticated user's session. Any attempt to access a resource without a matching `tenant_id` results in a `404 Not Found` rather than a `403 Forbidden` to prevent enumeration attacks.

---

### 3.2 Webhook Integration Framework (Priority: High)
**Status:** In Progress | **Complexity:** Medium

**Description:**
Legal teams use a variety of third-party tools (Case management software, CRM, Billing). Drift provides a webhook framework allowing external systems to subscribe to specific events within the Drift ecosystem.

**Functional Requirements:**
- Users can define "Subscriptions" specifying a target URL and a set of triggers (e.g., `record.uploaded`, `audit.completed`).
- Webhooks must support HMAC signatures for security, allowing the receiver to verify that the payload originated from Drift.
- A "Retry Queue" must be implemented: if a third-party endpoint returns a non-2xx code, Drift will retry with exponential backoff (1m, 5m, 15m, 1h).
- A dashboard for users to view delivery logs and manually trigger redeliveries of failed hooks.

**Technical Implementation:**
We use a Sidekiq-based worker pattern. When a domain event is persisted to the Event Store, a `WebhookDispatcherJob` is queued. This job fetches all active subscriptions for that event type and performs an asynchronous POST request.

---

### 3.3 Real-time Collaborative Editing (Priority: High)
**Status:** Blocked | **Complexity:** Very High

**Description:**
Lawyers and paralegals often collaborate on the "summary" of a medical record simultaneously. Drift requires a real-time editing experience similar to Google Docs to prevent versioning conflicts.

**Functional Requirements:**
- Presence indicators: Show who is currently viewing or editing a specific record.
- Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to handle concurrent edits to the same text block.
- Latency-compensated local updates to ensure a snappy UI.
- Granular locking: Lock specific fields (e.g., "Diagnosis") while allowing others to edit "Patient History."

**Technical Implementation (Proposed):**
The team is evaluating `Yjs` (a CRDT framework) integrated via ActionCable (WebSockets). Because this feature is currently blocked by the dependency on the "Core Document Schema" (owned by the lagging team), implementation is paused. The proposed flow involves a WebSocket connection that syncs binary state updates to a Redis-backed temporary store before flushing the final state to MySQL.

---

### 3.4 Data Import/Export with Format Auto-Detection (Priority: Low)
**Status:** In Design | **Complexity:** Medium

**Description:**
Medical records come in myriad formats (PDF, DICOM, HL7, FHIR, CSV). Drift needs a "Smart Import" tool that can analyze an uploaded file and suggest the correct mapping.

**Functional Requirements:**
- Support for bulk upload via ZIP or individual file drops.
- Magic-byte detection to determine file type regardless of extension.
- Mapping interface: If a CSV is uploaded, the user should be able to map "Column A" to "Patient Name."
- Export functionality: Allow users to export filtered record sets into a "Legal Discovery Package" (a zipped bundle with a generated index).

**Technical Implementation:**
The system will use a pipeline of "Parsers." A `FileAnalyzer` service will detect the MIME type and route the file to the corresponding parser (e.g., `HL7Parser`, `PdfTextExtractor`). We will utilize `Tesseract OCR` for scanned PDF documents to extract text for the search index.

---

### 3.5 A/B Testing Framework (Priority: Low)
**Status:** Blocked | **Complexity:** Medium

**Description:**
To optimize the onboarding flow and the "Medical Review" dashboard, the product team wants to test different UI layouts and workflows.

**Functional Requirements:**
- Integration with LaunchDarkly to segment users into "Control" and "Treatment" groups.
- Ability to define "Success Metrics" for a test (e.g., "Time to complete first record import").
- Automatic rollout: If the Treatment group shows a 10% increase in the metric, the flag should be capable of being toggled to 100% of the population.
- Dashboard within Drift to track the conversion rates of A/B tests.

**Technical Implementation:**
The framework will wrap LaunchDarkly's Ruby SDK. We will implement a `ExperimentHelper` in Rails that allows developers to wrap blocks of code: `if experiment('new_dashboard_layout') { render 'new_v2' } else { render 'v1' } end`. This is currently blocked as the team is prioritizing the Webhook framework.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer <JWT>` token in the header. All responses are in `application/json`.

### 4.1 Authentication & Tenancy
| Endpoint | Method | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Authenticates user and returns JWT | `{ "email": "...", "password": "..." }` | `200 { "token": "...", "tenant_id": "..." }` |
| `/api/v1/tenant/config` | GET | Retrieves tenant-specific settings | None | `200 { "settings": { ... } }` |

### 4.2 Medical Records Management
| Endpoint | Method | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/records` | GET | List records for current tenant | Query Params: `?page=1&q=search` | `200 { "data": [...], "meta": {...} }` |
| `/api/v1/records` | POST | Upload a new medical record | Multipart Form Data | `201 { "id": "rec_123", "status": "processing" }` |
| `/api/v1/records/:id` | PATCH | Update record metadata | `{ "patient_name": "..." }` | `200 { "id": "rec_123", "updated_at": "..." }` |
| `/api/v1/records/:id` | DELETE | Archive record (Soft delete) | None | `204 No Content` |

### 4.3 Webhooks & Integrations
| Endpoint | Method | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/webhooks` | POST | Register a new webhook | `{ "url": "...", "events": ["record.created"] }` | `201 { "webhook_id": "wh_99" }` |
| `/api/v1/webhooks/:id` | DELETE | Remove a webhook subscription | None | `204 No Content` |

**Example Request (POST `/api/v1/records`):**
```http
POST /api/v1/records HTTP/1.1
Host: api.drift.flintrock.io
Authorization: Bearer eyJhbGci...
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="file"; filename="patient_x.pdf"
Content-Type: application/pdf

[Binary Data]
--boundary--
```

**Example Response (GET `/api/v1/records`):**
```json
{
  "data": [
    {
      "id": "rec_123",
      "patient_name": "John Doe",
      "date_of_service": "2023-01-15",
      "provider": "City General Hospital",
      "status": "reviewed"
    }
  ],
  "meta": {
    "total_count": 1,
    "page": 1,
    "per_page": 20
  }
}
```

---

## 5. DATABASE SCHEMA

### 5.1 Schema Design Principles
Drift uses a hybrid approach. Core entities use standard relational patterns, while the `events` table serves as the immutable ledger for the CQRS implementation.

### 5.2 Table Definitions

1.  **`tenants`**
    - `id` (UUID, PK)
    - `name` (String)
    - `subscription_plan` (String: 'basic', 'pro', 'enterprise')
    - `created_at` / `updated_at` (Timestamp)

2.  **`users`**
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `email` (String, Unique)
    - `password_digest` (String)
    - `role` (String: 'admin', 'lawyer', 'paralegal')

3.  **`medical_records`** (The Read Model)
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `patient_id` (String)
    - `provider_id` (String)
    - `file_url` (String)
    - `status` (String)
    - `last_modified_by` (UUID, FK $\rightarrow$ users.id)

4.  **`events`** (The Event Store)
    - `id` (BigInt, PK)
    - `tenant_id` (UUID, FK $\rightarrow$ tenants.id)
    - `aggregate_id` (UUID) - e.g., the medical_record_id
    - `event_type` (String) - e.g., 'RecordUploaded'
    - `payload` (JSONB) - The actual change data
    - `created_at` (Timestamp, Index)

5.  **`audit_logs`** (Optimized Query View)
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK)
    - `user_id` (UUID, FK)
    - `action` (String)
    - `target_id` (UUID)
    - `timestamp` (Timestamp)

6.  **`webhook_subscriptions`**
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK)
    - `target_url` (String)
    - `secret_token` (String)
    - `event_types` (Array of Strings)

7.  **`webhook_deliveries`**
    - `id` (UUID, PK)
    - `subscription_id` (UUID, FK)
    - `response_code` (Integer)
    - `request_payload` (JSONB)
    - `attempt_count` (Integer)

8.  **`patient_profiles`**
    - `id` (UUID, PK)
    - `tenant_id` (UUID, FK)
    - `full_name` (String)
    - `dob` (Date)
    - `case_number` (String)

9.  **`document_versions`**
    - `id` (UUID, PK)
    - `record_id` (UUID, FK)
    - `version_number` (Integer)
    - `s3_path` (String)
    - `created_by` (UUID, FK)

10. **`user_sessions`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK)
    - `ip_address` (String)
    - `user_agent` (String)
    - `expires_at` (Timestamp)

### 5.3 Relationships
- **Tenants $\rightarrow$ Users:** One-to-Many.
- **Tenants $\rightarrow$ Medical Records:** One-to-Many.
- **Medical Records $\rightarrow$ Document Versions:** One-to-Many.
- **Users $\rightarrow$ Events:** Many-to-Many (via the payload in the event store).
- **Webhook Subscriptions $\rightarrow$ Deliveries:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Drift utilizes a three-tier environment strategy to ensure stability and compliance.

#### 6.1.1 Development (`dev`)
- **Purpose:** Rapid iteration and feature prototyping.
- **Host:** Local Docker containers $\rightarrow$ Heroku Dev Dynos.
- **Database:** Shared MySQL instance with seed data.
- **Deployment:** Continuous Deployment (CD) from the `develop` branch.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Final QA, stakeholder demos, and UAT (User Acceptance Testing).
- **Host:** Heroku Staging App.
- **Database:** Mirror of production schema; sanitized subset of data.
- **Deployment:** Triggered by merges to the `release` branch.
- **Speciality:** This environment is where the "Stakeholder Demo" (Milestone 2) will occur.

#### 6.1.3 Production (`prod`)
- **Purpose:** Live customer traffic.
- **Host:** Heroku Private Spaces (EU-West-1).
- **Database:** Multi-AZ High Availability MySQL.
- **Deployment:** Canary releases. New code is deployed to 10% of the fleet first, monitored for 30 minutes for 5xx errors, then rolled out to 100%.
- **Feature Flags:** All new features are wrapped in LaunchDarkly flags and toggled on per-tenant.

### 6.2 Infrastructure Pipeline
1. **CI:** GitHub Actions runs RSpec and Rubocop on every push.
2. **CD:** Successful builds on `main` trigger a Heroku Pipeline deployment.
3. **Monitoring:** New Relic for APM; Papertrail for log aggregation; Sentry for error tracking.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic in Models and Services.
- **Tooling:** RSpec.
- **Requirement:** 80% code coverage.
- **Specifics:** Every `Command` in the CQRS flow must have a unit test verifying that the correct `Event` is persisted to the store.

### 7.2 Integration Testing
- **Focus:** API Endpoints and Database interactions.
- **Tooling:** Request specs in RSpec.
- **Requirement:** All 8 core API endpoints must have positive and negative test cases (e.g., testing `tenant_id` isolation by attempting to access Record A from Tenant B).

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (Onboarding $\rightarrow$ Record Upload $\rightarrow$ Review $\rightarrow$ Export).
- **Tooling:** Playwright.
- **Requirement:** Full suite run against the `staging` environment before every production release.

### 7.4 Performance Testing
- **Focus:** Raw SQL query performance.
- **Requirement:** Because 30% of the app bypasses the ORM for speed, these specific queries must be benchmarked with a dataset of 1 million records to ensure they stay under 200ms response time.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key Architect leaving in 3 months | High | High | Accept risk; monitor weekly; document all architectural decisions in this spec immediately. |
| **R2** | Stakeholder Scope Creep | High | Medium | Engage external consultant for an independent assessment of "must-have" vs "nice-to-have" features. |
| **R3** | Data Breach/Leakage | Low | Critical | Implement strict `acts_as_tenant` scoping and quarterly 3rd party penetration tests. |
| **R4** | Performance Regression (Raw SQL) | Medium | Medium | Establish a "Dangerous Query" registry; migrations must be reviewed by Bodhi Oduya. |
| **R5** | Dependency Block (Other Team) | High | Medium | Escalate to VP of Engineering if the 3-week delay extends to 5 weeks. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt if realized.
- **High:** Requires significant pivot or budget reallocation.
- **Medium:** Causes delay in milestones.
- **Low:** Manageable via standard sprint tasks.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase breakdown

**Phase 1: Foundation (Current $\rightarrow$ June 2025)**
- Setup Heroku EU Private Spaces.
- Implement Multi-tenant isolation (Complete).
- Build Event Store and CQRS base.
- Develop Core API endpoints.

**Phase 2: Integration & Beta (June 2025 $\rightarrow$ November 2025)**
- Complete Webhook framework.
- Resolve dependency on the external team for the Record Schema.
- Implement Collaborative Editing (if unblocked).
- **Milestone 1:** Onboard first paying customer (Target: 2025-07-15).
- **Milestone 2:** Stakeholder demo and sign-off (Target: 2025-09-15).
- **Milestone 3:** External beta with 10 pilot users (Target: 2025-11-15).

**Phase 3: Optimization (December 2025 $\rightarrow$ March 2026)**
- Roll out Data Import/Export auto-detection.
- Activate A/B testing framework for UX optimization.
- Perform full security audit for GDPR/CCPA.

### 9.2 Gantt-style Dependencies
- `Tenant Isolation` $\rightarrow$ `API Development` $\rightarrow$ `First Paying Customer`.
- `External Team Deliverable` $\rightarrow$ `Collaborative Editing` $\rightarrow$ `Beta Users`.
- `Webhook Framework` $\rightarrow$ `Third-party Integrations` $\rightarrow$ `Stakeholder Sign-off`.

---

## 10. MEETING NOTES (Slack Thread Archive)

*Note: Per company policy, formal minutes are not taken. The following are distilled from Slack threads in the #drift-dev channel.*

### Meeting 1: Architecture Alignment (2023-11-12)
- **Participants:** Bodhi, Elara, Veda.
- **Discussion:** Elara questioned whether a monolith was too restrictive. Bodhi argued that given the $400k budget and 15-person team, microservices would introduce "distributed system tax" that the project cannot afford.
- **Decision:** Stick to a Ruby on Rails monolith. Use CQRS only for the audit-critical paths to get the benefits of event sourcing without the complexity of a full event-driven architecture.

### Meeting 2: The "Raw SQL" Debate (2023-12-05)
- **Participants:** Bodhi, Veda, Sienna.
- **Discussion:** Sienna noticed that several complex reports were using raw SQL strings instead of ActiveRecord. Veda raised concerns about SQL injection and migration safety.
- **Decision:** Bodhi acknowledged the performance necessity for these specific views. Decision: Create a `SafeSQL` wrapper module that enforces parameter binding. Any new raw SQL must be approved by Bodhi.

### Meeting 3: Dependency Blockage (2024-01-20)
- **Participants:** Bodhi, Elara.
- **Discussion:** The team that is providing the "Medical Record Schema" is now 3 weeks behind. Elara stated that the Frontend cannot build the collaborative editor without the final schema.
- **Decision:** Frontend will build "mock" interfaces based on the draft schema. If the deliverable isn't received by Feb 10, the "Collaborative Editing" feature will be downgraded to "Priority: Low" to avoid idling the team.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 75% | $300,000 | Covers salaries for distributed team of 15 (adjusted for regional cost of living). |
| **Infrastructure** | 10% | $40,000 | Heroku Private Spaces, AWS S3, MySQL RDS (EU Region). |
| **Tools & Licenses** | 5% | $20,000 | LaunchDarkly, New Relic, Sentry, GitHub Enterprise. |
| **External Consultant** | 5% | $20,000 | Independent assessment to mitigate scope creep (Risk R2). |
| **Contingency** | 5% | $20,000 | Reserved for emergency scaling or critical security patches. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Migration Safety Protocol
Due to the 30% ORM bypass, the following protocol is mandatory for all migrations:
1. **Audit:** Search the codebase for all strings containing the target column name.
2. **Impact Analysis:** Determine if the raw SQL query is `SELECT` only or `INSERT/UPDATE`.
3. **Deployment:** Use a "Expand and Contract" pattern:
   - Step 1: Add the new column.
   - Step 2: Update raw SQL to write to both columns.
   - Step 3: Migrate data from old to new.
   - Step 4: Update raw SQL to read from new column.
   - Step 5: Remove old column.

### Appendix B: GDPR Compliance Checklist for EU Shards
- [ ] **Right to Erasure:** Implement a "Hard Delete" service that scrubs the Event Store for a specific `patient_id` (requires rewriting the event stream).
- [ ] **Data Portability:** Ensure the Export feature provides data in a machine-readable format (JSON/CSV).
- [ ] **Encryption at Rest:** All MySQL disks must be encrypted via AES-256.
- [ ] **Encryption in Transit:** TLS 1.3 required for all API calls.
- [ ] **Access Control:** Quarterly review of who has `prod` access; implement Just-In-Time (JIT) access for the Tech Lead.