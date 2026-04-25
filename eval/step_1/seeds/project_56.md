# PROJECT SPECIFICATION: PROJECT QUORUM
**Document Version:** 1.0.4  
**Status:** Final Baseline  
**Date:** October 24, 2023  
**Company:** Hearthstone Software  
**Project Lead:** Gideon Stein (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

**Project Overview**
Project "Quorum" is a high-visibility strategic initiative by Hearthstone Software to develop a specialized e-commerce marketplace tailored for the education industry. Unlike generic e-commerce platforms, Quorum is designed as a strategic partnership integration, necessitating deep synchronization with an external partner's API. The platform's primary objective is to facilitate the exchange of educational resources, curriculum modules, and certifications between institutions and independent providers.

**Business Justification**
The education sector is currently experiencing a fragmented digital transformation. Institutions possess high-quality content but lack the distribution infrastructure to monetize or share it efficiently. Hearthstone Software identifies a market gap for a "curated exchange" where trust is verified and content is delivered via a robust, scalable pipeline. By integrating with the external partner’s API, Quorum leverages an existing ecosystem of educational providers, reducing the cold-start problem typically associated with marketplaces.

**ROI Projection**
With a total investment of $3,000,000, the project is projected to achieve a break-even point within 22 months post-launch. ROI is calculated based on a tiered commission model (15% per transaction) and a monthly subscription fee for institutional "Power Users." 
- **Projected Year 1 Revenue:** $1.2M
- **Projected Year 2 Revenue:** $4.8M
- **Strategic Value:** Beyond direct revenue, Quorum establishes Hearthstone Software as the primary infrastructure layer for educational resource distribution, creating a moat against general-purpose competitors.

**Strategic Alignment**
The project is a high-executive visibility venture. The success of Quorum will determine the company's ability to penetrate the EdTech vertical. Consequently, the project emphasizes stability and strategic partnerships over rapid, unmanaged feature growth.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
To ensure rapid development and ease of maintenance for a distributed team, the project utilizes a "deliberately simple" stack:
- **Backend:** Ruby on Rails 7.1 (Monolith)
- **Database:** MySQL 8.0
- **Hosting:** Heroku (Private Spaces)
- **Frontend:** Micro-frontend architecture utilizing independent modules deployed via Module Federation.

### 2.2 Micro-Frontend Strategy
Despite the monolithic backend, the frontend is split into independent domains (e.g., `Checkout`, `CourseCatalog`, `UserDashboard`). This allows the distributed team of 15 (across 5 countries) to own specific slices of the UI without causing merge conflicts in a single massive React/Vue repository.

### 2.3 System Diagram (ASCII Representation)
```text
[ User Browser ] <--- (HTTPS/TLS) ---> [ Heroku Load Balancer ]
                                              |
                                              v
                                [ Rails Monolith (App Server) ]
                                /             |              \
          ____________________/               |                \____________________
         |                                    |                                    |
 [ MySQL Database ]                   [ Redis Cache ]                      [ External Partner API ]
 (Persistence)                      (Session/Jobs)                      (Sync/Educational Data)
         |                                    |                                    |
 [ S3 Bucket / CDN ] <------------------------/                                    |
 (File Storage/Assets)                                                             |
         ^                                                                          |
         \------------------- [ Virus Scanning Service (ClamAV) ] <----------------/
```

### 2.4 Deployment Pipeline
Quorum operates on a strict **Weekly Release Train**.
- **Release Cycle:** Every Thursday at 04:00 UTC.
- **Cut-off:** Wednesday 23:59 UTC.
- **Constraint:** No hotfixes are permitted outside the release train. If a critical bug is found, it must be queued for the next train unless the Project Lead (Gideon Stein) authorizes an emergency rollback to the previous stable version.

### 2.5 Security Posture
The project follows an internal-only security audit model. No external compliance certifications (e.g., SOC2, HIPAA) are required for the initial launch. Security focuses on OWASP Top 10 mitigation and the internal audit conducted by the Hearthstone Software security team.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:** 
Educational marketplaces rely on the exchange of PDFs, ZIP files, and video lectures. To prevent the platform from becoming a vector for malware, every file uploaded must be scanned and then distributed via a Global CDN for low-latency access.

**Detailed Requirements:**
1. **Upload Pipeline:** Users upload files via a multipart request to `/api/v1/uploads`. The file is temporarily stored in a "Quarantine" S3 bucket.
2. **Virus Scanning:** An asynchronous worker triggers a scan using ClamAV. If a virus is detected, the file is immediately deleted, and the user is notified via a `422 Unprocessable Entity` response.
3. **CDN Integration:** Once cleared, files are moved to the "Production" S3 bucket and cached via CloudFront. 
4. **Access Control:** Signed URLs must be used to ensure only paying customers can access the files.
5. **Performance:** Maximum upload size is 500MB. Scanning must complete within 30 seconds per file.

**Technical Constraint:** The scanning process must not block the main Rails thread; it must be handled by a Sidekiq background job.

### 3.2 Automated Billing and Subscription Management
**Priority:** High | **Status:** Not Started

**Description:**
A comprehensive billing engine to handle one-time course purchases and recurring institutional subscriptions.

**Detailed Requirements:**
1. **Subscription Tiers:** Three tiers (Basic: $29/mo, Professional: $99/mo, Institutional: $499/mo).
2. **Payment Gateway:** Integration with Stripe for credit card processing and automated invoicing.
3. **Automated Billing:** Monthly recurring charges handled via Stripe Billing. The system must handle "Dunning" processes (retrying failed payments 3 times over 14 days).
4. **Tax Calculation:** Automated VAT/Sales Tax calculation based on the buyer's geography using a tax-calculation API.
5. **Invoicing:** PDF invoices must be automatically generated and emailed to the customer upon successful payment.

**Workflow:** When a subscription expires, the `User#subscription_status` must be updated to `expired`, revoking access to premium resources immediately.

### 3.3 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Progress

**Description:**
To allow institutional partners to integrate Quorum into their own Learning Management Systems (LMS), a robust public API is required.

**Detailed Requirements:**
1. **Versioning:** Versioning will be handled via the URL path (e.g., `/api/v1/`, `/api/v2/`). Version 1 is deprecated once Version 2 has been stable for 90 days.
2. **Authentication:** API Key-based authentication using Header `X-Quorum-API-Key`.
3. **Sandbox Environment:** A dedicated sandbox environment (`sandbox.quorum.hearthstone.com`) where developers can test endpoints without impacting real financial data or live courses.
4. **Rate Limiting:** 1,000 requests per hour per API key to prevent DDoS and API abuse.
5. **Documentation:** Auto-generated Swagger/OpenAPI documentation.

**Current Progress:** The basic routing structure and authentication layer are complete. The endpoint logic for course retrieval is currently being developed.

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Medium | **Status:** In Review

**Description:**
Users must be able to find specific educational content across thousands of entries using complex filters.

**Detailed Requirements:**
1. **Full-Text Indexing:** Use of an indexing engine (e.g., Elasticsearch or PgSearch) to allow for fuzzy matching and stem-based searching.
2. **Faceted Filtering:** Ability to filter results by:
    - Category (e.g., Mathematics, History, CS)
    - Price Range (Sliding scale)
    - Rating (4 stars and up)
    - Certification Level (Undergraduate, Graduate, Professional)
3. **Ranking Algorithm:** Search results should be ranked based on a combination of "Relevance," "Average Rating," and "Recentness."
4. **Autocomplete:** A "search-as-you-type" suggest feature to improve UX.

**Review Note:** The current implementation is facing latency issues when filtering by more than three facets simultaneously.

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
A tool for educators to co-author course materials in real-time within the Quorum platform.

**Detailed Requirements:**
1. **Concurrency:** Use of Operational Transformation (OT) or CRDTs (Conflict-free Replicated Data Types) to ensure that two users editing the same paragraph do not overwrite each other's work.
2. **WebSocket Integration:** Utilizing ActionCable for real-time state synchronization between clients.
3. **Presence Indicators:** Visual indicators showing who is currently active in the document (cursors and avatars).
4. **Conflict Resolution:** Automatic merging of changes; in the event of a hard collision, the system prompts the user to choose the "Winning" version.
5. **Auto-Save:** Changes are persisted to MySQL every 5 seconds or upon every 50 characters typed.

**Verification:** This feature has passed QA and is considered "Production Ready."

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under the base URL: `https://api.quorum.hearthstone.com/v1`

### 4.1 GET `/courses`
**Description:** Retrieve a paginated list of available courses.
- **Request Params:** `page` (int), `per_page` (int), `q` (string search term).
- **Example Response:**
```json
{
  "data": [
    { "id": "crs_101", "title": "Intro to Quantum Mechanics", "price": 49.99, "currency": "USD" }
  ],
  "meta": { "total_pages": 12, "current_page": 1 }
}
```

### 4.2 POST `/courses`
**Description:** Create a new course listing.
- **Request Body:** `{ "title": "String", "description": "String", "price": "Decimal" }`
- **Response:** `201 Created` with course object.

### 4.3 GET `/courses/:id`
**Description:** Get detailed information for a specific course.
- **Response:** Returns full course metadata including author and syllabus.

### 4.4 POST `/subscriptions`
**Description:** Initialize a new subscription for the authenticated user.
- **Request Body:** `{ "plan_id": "plan_basic", "payment_method_id": "pm_xxx" }`
- **Response:** `200 OK` with subscription status.

### 4.5 GET `/user/profile`
**Description:** Retrieve authenticated user account details.
- **Response:** `{ "username": "jdoe", "email": "jdoe@edu.com", "tier": "Professional" }`

### 4.6 PUT `/user/profile`
**Description:** Update user account details.
- **Request Body:** `{ "email": "newemail@edu.com" }`
- **Response:** `200 OK`.

### 4.7 POST `/uploads`
**Description:** Upload a file for virus scanning and storage.
- **Request:** Multipart form-data.
- **Response:** `{ "upload_id": "up_789", "status": "scanning" }`

### 4.8 GET `/uploads/:id/status`
**Description:** Check if a file has passed the virus scan.
- **Response:** `{ "upload_id": "up_789", "status": "clean", "cdn_url": "https://cdn.quorum.../file.pdf" }`

---

## 5. DATABASE SCHEMA

The system uses MySQL 8.0. All tables use `bigint` for primary keys and `timestamp` for auditing.

### 5.1 Tables and Relationships

1. **`users`**
   - `id` (PK), `email` (unique), `password_digest`, `role` (enum: admin, educator, student), `created_at`, `updated_at`.
2. **`profiles`**
   - `id` (PK), `user_id` (FK), `full_name`, `bio`, `avatar_url`.
3. **`courses`**
   - `id` (PK), `educator_id` (FK -> users), `title`, `description`, `price`, `status` (draft, published), `created_at`.
4. **`enrollments`**
   - `id` (PK), `user_id` (FK), `course_id` (FK), `enrolled_at`, `completion_status`.
5. **`subscriptions`**
   - `id` (PK), `user_id` (FK), `stripe_subscription_id`, `plan_id`, `status` (active, canceled), `current_period_end`.
6. **`plans`**
   - `id` (PK), `name`, `monthly_cost`, `features_json`.
7. **`files`**
   - `id` (PK), `course_id` (FK), `storage_path`, `virus_scan_status` (pending, clean, infected), `content_type`.
8. **`transactions`**
   - `id` (PK), `user_id` (FK), `amount`, `currency`, `stripe_transaction_id`, `created_at`.
9. **`api_keys`**
   - `id` (PK), `user_id` (FK), `key_hash`, `last_used_at`, `expires_at`.
10. **`search_indices`**
    - `id` (PK), `target_id` (FK), `index_content` (text), `category_tag`.

### 5.2 Relationship Map
- `users` (1:1) $\rightarrow$ `profiles`
- `users` (1:N) $\rightarrow$ `courses` (as educator)
- `users` (1:N) $\rightarrow$ `enrollments` (as student)
- `courses` (1:N) $\rightarrow$ `enrollments`
- `courses` (1:N) $\rightarrow$ `files`
- `users` (1:1) $\rightarrow$ `subscriptions`

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum utilizes three distinct environments hosted on Heroku.

**1. Development (Dev)**
- **URL:** `dev.quorum.hearthstone.com`
- **Purpose:** Individual developer testing and feature branch integration.
- **Data:** Anonymized seed data.
- **Deployment:** Automatic on merge to `develop` branch.

**2. Staging (Stage)**
- **URL:** `staging.quorum.hearthstone.com`
- **Purpose:** Final QA, User Acceptance Testing (UAT), and external partner API integration testing.
- **Data:** Mirror of production (scrubbed of PII).
- **Deployment:** Manual trigger via GitHub Actions on the `release` branch.

**3. Production (Prod)**
- **URL:** `app.quorum.hearthstone.com`
- **Purpose:** Live customer traffic.
- **Data:** Live customer data.
- **Deployment:** Thursday Release Train.

### 6.2 Infrastructure Components
- **Heroku Dynos:** Performance-M dynos to handle the Rails monolith.
- **Redis:** Used for Sidekiq background processing and session caching.
- **MySQL:** Managed via Heroku Postgres/MySQL add-ons with daily snapshots.
- **S3/CloudFront:** AWS integration for file distribution.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** RSpec.
- **Approach:** Each model and service object must have 90%+ coverage.
- **Focus:** Business logic, validation rules, and edge cases in the billing engine.

### 7.2 Integration Testing
- **Framework:** RSpec Request Specs.
- **Approach:** Testing the interaction between the API and the database.
- **Focus:** API endpoint correctness, authorization levels, and external API sync simulations.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Cypress.
- **Approach:** Critical user paths (The "Happy Path") are tested weekly.
- **Key Flows:**
    - User registration $\rightarrow$ Course purchase $\rightarrow$ File download.
    - Educator upload $\rightarrow$ Virus scan $\rightarrow$ Course publication.
    - Subscription upgrade $\rightarrow$ Payment success $\rightarrow$ Access grant.

### 7.4 Performance Testing
- **Tool:** k6.
- **Target:** The system must support 500 concurrent users with a p95 response time of $< 300\text{ms}$.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding 'small' features. | High | High | Escalate all new requests to the Steering Committee for funding/timeline adjustment. |
| R-02 | Team lacks experience with the specific Ruby/Rails stack. | Medium | Medium | Engage an external Rails consultant for a monthly architectural assessment. |
| R-03 | Infrastructure provisioning delays by cloud provider. | High | Medium | Diversify hosting options or request priority support from Heroku. |
| R-04 | Technical debt: 3 different date formats in codebase. | High | Low | Implement a `DateNormalization` service layer before Milestone 1. |
| R-05 | External Partner API downtime. | Medium | High | Implement a robust caching layer and a "Degraded Mode" UI. |

**Probability/Impact Matrix:**
- High Probability / High Impact $\rightarrow$ Immediate attention.
- Low Probability / Low Impact $\rightarrow$ Monitor.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Core Infrastructure (Current - 2024-12)
- **Focus:** Finalizing the Collaborative Editing tool and stabilizing the API.
- **Dependencies:** Infrastructure provisioning must be resolved.
- **Key Deliverable:** Functional MVP with internal alpha testers.

### 9.2 Phase 2: Payment and Distribution (2025-01 - 2025-03)
- **Focus:** Implementing the File Upload/Virus Scanning pipeline and the Billing Engine.
- **Dependencies:** Completion of the User Profile and API layers.
- **Milestone 1 (2025-03-15):** Post-launch stability confirmed.

### 9.3 Phase 3: Market Expansion (2025-04 - 2025-06)
- **Focus:** Advanced Search and Faceted Filtering optimization.
- **Dependencies:** Sufficient course volume in the database.
- **Milestone 2 (2025-05-15):** First paying customer onboarded.

### 9.4 Phase 4: Hardening and Audit (2025-07 - 2025-09)
- **Focus:** Final internal security audit and performance tuning.
- **Dependencies:** All features in "Complete" status.
- **Milestone 3 (2025-07-15):** Security audit passed.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team dynamic, formal meeting notes are not recorded. The following are transcripts of critical decision threads from the `#quorum-dev` Slack channel.

**Thread 1: The "No Hotfix" Rule**
- **Gideon Stein:** "I'm seeing too many 'quick fixes' hitting prod on Tuesdays. From now on, we follow the Thursday Release Train. No exceptions."
- **Uri Stein:** "What if there is a P0 bug?"
- **Gideon Stein:** "If it's a P0, we roll back the whole deploy to the previous version. No cherry-picking fixes. We need predictability over speed."
- **Decision:** Weekly release train established; no mid-week hotfixes.

**Thread 2: Date Format Chaos**
- **Uri Stein:** "I've found ISO8601 in the API, Unix timestamps in the DB, and `MM/DD/YYYY` in the frontend. This is a nightmare."
- **Hugo Stein (Intern):** "I can write a script to convert them?"
- **Uri Stein:** "No, we need a normalization layer. Let's create a `DateTimeHelper` that all services must use."
- **Decision:** Technical debt acknowledged; normalization layer to be built before Milestone 1.

**Thread 3: API Sandbox Logic**
- **Lev Moreau:** "Users are complaining that they are accidentally charging their real cards while testing the API."
- **Gideon Stein:** "We need a full sandbox environment. Not just a flag, but a separate DB and app instance."
- **Uri Stein:** "Agreed. I'll spin up `sandbox.quorum.hearthstone.com` on a separate Heroku app."
- **Decision:** Sandbox environment created to isolate test transactions from production.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $2,100,000 | Salaries for 15 distributed staff (Avg $140k/yr for 1 year). |
| **Infrastructure** | $350,000 | Heroku Private Spaces, AWS S3, CloudFront, Redis, MySQL. |
| **External Consulting** | $150,000 | Specialist Rails consultant for architectural audit. |
| **Tooling & Software** | $100,000 | Stripe fees, ClamAV enterprise, GitHub Enterprise, Slack, Jira. |
| **Contingency** | $300,000 | Reserve for scope creep escalation or emergency scaling. |

---

## 12. APPENDICES

### Appendix A: Virus Scanning Implementation Details
The virus scanning service operates as a decoupled micro-service. 
1. **Trigger:** An `AfterCommit` hook in the `File` model triggers a `VirusScanJob`.
2. **Mechanism:** The job streams the file from S3 to a ClamAV daemon running in a separate container.
3. **Hash Verification:** The system stores a SHA-256 hash of every scanned file. If a file with the same hash is uploaded again, the system skips the scan and marks it "Clean" based on the previous result.

### Appendix B: Conflict Resolution Logic (Collaborative Editing)
The real-time editor utilizes a Hybrid-CRDT approach:
- **LWW-Element-Set (Last-Write-Wins):** Used for metadata and simple field updates.
- **RGA (Replicated Growable Array):** Used for the main text body to ensure that character insertions and deletions are consistent across all clients regardless of network latency.
- **State Vector:** Each client maintains a state vector to track the version of the document they have acknowledged, minimizing the amount of data sent over ActionCable.