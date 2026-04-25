# PROJECT SPECIFICATION DOCUMENT: ARCHWAY LMS
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft/Active  
**Company:** Bellweather Technologies  
**Project Lead:** Lina Moreau (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
"Archway" is a greenfield Learning Management System (LMS) developed by Bellweather Technologies, specifically engineered for the Food and Beverage (F&B) industry. Unlike generic LMS platforms, Archway is designed to handle the high-turnover, compliance-heavy, and geographically dispersed nature of hospitality staff training. This project represents a strategic pivot for Bellweather Technologies, as the company is entering a market segment where it has no prior operational history. The goal is to provide a scalable, real-time educational environment that ensures food safety compliance, operational excellence, and staff certification across global franchises.

### 1.2 Business Justification
The F&B industry suffers from a chronic training gap. Traditional LMS tools are often too cumbersome for frontline workers who lack dedicated desk time. Archway solves this by utilizing a high-performance technical stack (Elixir/Phoenix) to provide a lightweight, real-time experience. By focusing on the F&B niche, Bellweather Technologies can capture a market share currently dominated by legacy systems that lack the agility and real-time synchronization required for modern kitchen and floor operations.

The strategic decision to build this as a greenfield product allows the team to avoid the "legacy drag" of previous Bellweather projects. While the company is venturing into unknown territory, the agility of the current distributed team and the robustness of the chosen architecture position Archway to disrupt the sector.

### 1.3 ROI Projection and Financial Strategy
The project is currently **unfunded**, operating under a "bootstrapping" model using existing team capacity. This means the ROI is calculated not against a capital expenditure (CapEx) budget, but against the opportunity cost of the 15-person distributed team’s time.

**Projected Revenue Streams:**
- **SaaS Subscription:** Tiered pricing based on "active learners" per month.
- **Enterprise Licensing:** Custom annual contracts for global F&B chains.
- **API Access:** Monetized access to the customer-facing API for third-party HR integration.

**ROI Forecast (3-Year):**
- **Year 1:** Product development and pilot. Expected Revenue: $0. Target: 10 pilot users.
- **Year 2:** Market entry. Target: 50 mid-sized F&B groups. Projected Revenue: $1.2M ARR.
- **Year 3:** Scaling. Target: 200+ groups. Projected Revenue: $4.5M ARR.
- **Break-even Point:** Estimated Q3 2027, once the "capacity cost" of the team is offset by recurring subscription revenue.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Archway is built on the BEAM virtual machine, utilizing **Elixir** and the **Phoenix** framework. The choice of Elixir allows for massive concurrency, which is essential for real-time training synchronization across thousands of simultaneous learners. The frontend leverages **Phoenix LiveView**, removing the need for a heavy JavaScript framework and ensuring state is managed on the server for instantaneous updates.

### 2.2 Architecture Diagram (ASCII)
The system follows a serverless-inspired orchestration layer via API Gateway, routing requests to Elixir nodes deployed on Fly.io.

```text
[ Client Browser / Mobile App ] 
          |
          v
[ Fly.io Global Edge / Load Balancer ]
          |
          v
[ API Gateway Orchestration Layer ] <--- (Auth / Rate Limiting / Routing)
          |
          +---------------------------------------+
          |                                       |
[ Elixir/Phoenix App Node A ]          [ Elixir/Phoenix App Node B ]
  | (LiveView State)                    | (LiveView State)
  |                                     |
  +------------------+------------------+
                     |
                     v
          [ PostgreSQL Database ] <--- (Persistent Storage)
                     |
          [ Redis / PubSub ] <--- (Real-time Messaging/Presence)
```

### 2.3 Infrastructure & Security
- **Deployment:** Managed via **Fly.io**, providing regional proximity to users.
- **Orchestration:** API Gateway manages the routing to serverless functions and long-running Phoenix processes.
- **Security Compliance:** The environment must be **ISO 27001 certified**. This requires strict data encryption at rest (AES-256) and in transit (TLS 1.3), regular penetration testing, and a rigorous identity and access management (IAM) policy. All logs are forwarded to a secure, immutable vault for auditing purposes.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: Critical)
**Status:** In Design | **Launch Blocker:** Yes

The search functionality is the primary discovery mechanism for the LMS content library. Given the scale of F&B training (thousands of micro-modules on hygiene, safety, and recipes), a simple SQL `LIKE` query is insufficient.

- **Functional Requirements:**
    - **Full-Text Indexing:** Implementation of PostgreSQL `tsvector` and `tsquery` for rapid indexing of course titles, descriptions, and transcriptions.
    - **Faceted Filtering:** Users must be able to filter results by:
        - *Course Category* (e.g., Food Safety, Mixology, Management).
        - *Certification Level* (e.g., Level 1, Level 2, Master).
        - *Language* (12 supported languages).
        - *Completion Status* (Not Started, In Progress, Completed).
    - **Search Suggestions:** Real-time "type-ahead" suggestions powered by LiveView.
- **Technical Implementation:** 
    - Integration of a Gin index on the `courses` table to optimize search speeds.
    - Search queries will be routed through a dedicated `SearchService` module to handle stemming and stop-word removal.
- **Acceptance Criteria:** Search results must return in under 150ms for a database of 10,000 courses.

### 3.2 Localization and Internationalization (Priority: Low)
**Status:** Complete | **Launch Blocker:** No

To serve global F&B clients, Archway supports 12 languages. The implementation focuses on a "Translation-First" approach where no hardcoded strings exist in the UI.

- **Implemented Details:**
    - **Gettext Integration:** Use of Elixir's `Gettext` for `.po` and `.pot` file management.
    - **Dynamic Locale Switching:** Users can change language preferences in their profile, which updates the session state and triggers a LiveView refresh.
    - **RTL Support:** CSS Grid and Flexbox layouts are configured to support Right-to-Left languages (e.g., Arabic) via a `.rtl` class on the body element.
    - **UTF-8 Encoding:** All database columns for content are `TEXT` with `UTF8` encoding to ensure no character corruption across the 12 supported locales.

### 3.3 Customer-Facing API with Versioning (Priority: High)
**Status:** Not Started | **Launch Blocker:** No

Enterprise clients require the ability to sync Archway data with their internal HRIS (Human Resource Information Systems).

- **Functional Requirements:**
    - **Versioning:** The API will follow semantic versioning (e.g., `/api/v1/`, `/api/v2/`). When a breaking change is introduced, the previous version remains active for 6 months.
    - **Sandbox Environment:** A mirrored "Sandbox" environment where clients can test API calls without affecting production data.
    - **Authentication:** Implementation of OAuth2 and API Key rotation.
- **Technical Specification:** 
    - Use of `Plug` for versioning routing.
    - Rate limiting implemented via a Token Bucket algorithm to prevent API abuse.
    - Response format: Standardized JSON with a consistent wrapper: `{ "data": {}, "meta": {}, "errors": [] }`.

### 3.4 Automated Billing and Subscription Management (Priority: Critical)
**Status:** Not Started | **Launch Blocker:** Yes

Since this is a commercial product, a robust billing engine is required to handle the transition from pilot users to paying customers.

- **Functional Requirements:**
    - **Subscription Tiers:** Basic, Professional, and Enterprise tiers.
    - **Automated Invoicing:** Generation of PDF invoices on the 1st of every month.
    - **Dunning Process:** Automated email alerts for failed credit card payments with a 3-attempt retry logic.
    - **Prorated Upgrades:** If a client adds 100 new learners mid-month, the system must calculate the prorated cost automatically.
- **Technical Implementation:** 
    - Integration with Stripe Billing.
    - Webhook listeners in Phoenix to update the `subscription_status` in the PostgreSQL database in real-time.
    - A `BillingWorker` using `Oban` (background job processor) to handle monthly recurring checks.

### 3.5 Offline-First Mode with Background Sync (Priority: Low)
**Status:** Blocked | **Launch Blocker:** No

F&B environments (like walk-in freezers or basements) often have poor connectivity. This feature allows users to continue learning offline.

- **Functional Requirements:**
    - **Local Caching:** Caching of course content and quiz questions via IndexedDB in the browser.
    - **Conflict Resolution:** A "Last-Write-Wins" strategy for quiz answers submitted after regaining connectivity.
    - **Background Sync:** Use of Service Workers to push local changes to the server when the `navigator.onLine` event triggers.
- **Current Blocker:** Blocked by third-party API rate limits during testing of the synchronization handshake. The external identity provider limits the number of "re-authentication" requests allowed per minute during sync bursts.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path `https://api.archway.io/v1/`.

### 4.1 Get Course List
- **Endpoint:** `GET /courses`
- **Description:** Returns a list of all available courses with optional faceted filters.
- **Request Params:** `category=food_safety`, `level=1`, `page=1`
- **Response:** 
  ```json
  {
    "data": [
      {"id": "c_101", "title": "Basic Hygiene", "duration": "30m", "category": "food_safety"}
    ],
    "meta": {"total_results": 150, "page": 1}
  }
  ```

### 4.2 Create User
- **Endpoint:** `POST /users`
- **Description:** Registers a new learner in the system.
- **Request Body:** `{"email": "chef@restaurant.com", "name": "Gordon R.", "org_id": "org_55"}`
- **Response:** `201 Created`
  ```json
  {"id": "u_998", "status": "active", "created_at": "2023-10-24T10:00:00Z"}
  ```

### 4.3 Get User Progress
- **Endpoint:** `GET /users/{id}/progress`
- **Description:** Retrieves completion percentages for all courses.
- **Response:**
  ```json
  {"user_id": "u_998", "courses": [{"course_id": "c_101", "percent": 85}]}
  ```

### 4.4 Submit Quiz Answer
- **Endpoint:** `POST /quizzes/{quiz_id}/submissions`
- **Description:** Submits a student's answers for grading.
- **Request Body:** `{"answers": {"q1": "a", "q2": "c"}}`
- **Response:** `200 OK`
  ```json
  {"score": 80, "passed": true, "certificate_id": "cert_442"}
  ```

### 4.5 Update Subscription
- **Endpoint:** `PATCH /billing/subscription`
- **Description:** Upgrades or downgrades the organization's plan.
- **Request Body:** `{"plan_id": "plan_enterprise"}`
- **Response:** `200 OK`
  ```json
  {"new_plan": "enterprise", "next_billing_date": "2023-11-01"}
  ```

### 4.6 List Organization Learners
- **Endpoint:** `GET /orgs/{org_id}/learners`
- **Description:** Lists all users associated with a specific F&B company.
- **Response:**
  ```json
  {"org_id": "org_55", "learners": [{"id": "u_998", "name": "Gordon R."}]}
  ```

### 4.7 Get Course Content (Localized)
- **Endpoint:** `GET /courses/{id}/content`
- **Description:** Fetches the localized content for a specific module.
- **Request Params:** `lang=fr`
- **Response:**
  ```json
  {"id": "c_101", "content_fr": "Bienvenue au cours d'hygiène..."}
  ```

### 4.8 Delete User Account
- **Endpoint:** `DELETE /users/{id}`
- **Description:** Permanently removes a user and their data (GDPR compliant).
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL. All tables utilize UUIDs for primary keys to ensure scalability and security.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | `org_id` | None | `name`, `subscription_tier`, `created_at` | The F&B companies using Archway. |
| `users` | `user_id` | `org_id` | `email`, `password_hash`, `locale`, `role` | Learners and Admins. |
| `courses` | `course_id` | None | `title`, `description`, `category_id`, `is_published` | The core educational content. |
| `course_translations` | `trans_id` | `course_id` | `language_code`, `translated_title`, `content` | Localization strings for 12 languages. |
| `enrollments` | `enroll_id` | `user_id`, `course_id` | `status` (started/completed), `enrolled_at` | Mapping of users to courses. |
| `quizzes` | `quiz_id` | `course_id` | `passing_score`, `time_limit` | Assessment data for a course. |
| `questions` | `quest_id` | `quiz_id` | `question_text`, `correct_option`, `points` | Individual quiz questions. |
| `submissions` | `sub_id` | `user_id`, `quiz_id` | `score`, `submitted_at`, `is_passed` | Record of a user's attempt at a quiz. |
| `subscriptions` | `sub_id` | `org_id` | `stripe_id`, `status`, `current_period_end` | Billing state for organizations. |
| `search_indices` | `index_id` | `course_id` | `ts_vector` (Full-text search data) | Pre-computed search vectors. |

**Relationships:**
- One `Organization` has many `Users` (1:N).
- One `User` has many `Enrollments` (1:N).
- One `Course` has many `CourseTranslations` (1:N).
- One `Course` has many `Quizzes` (1:N).
- One `Quiz` has many `Questions` (1:N).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Archway utilizes three distinct environments to ensure stability.

**1. Development (Dev):**
- **Purpose:** Local feature development and rapid prototyping.
- **Configuration:** Local PostgreSQL containers, Elixir in `dev` mode.
- **Deployment:** Manual by individual engineers on their local machines.

**2. Staging (Stage):**
- **Purpose:** Pre-production testing and QA. Mirrors production hardware exactly.
- **Configuration:** Fly.io staging cluster, isolated PostgreSQL instance.
- **Deployment:** Triggered via manual script by the DevOps person. This is where the 45-minute CI pipeline is most evident.

**3. Production (Prod):**
- **Purpose:** Live customer environment.
- **Configuration:** Fly.io global cluster with multi-region failover.
- **Security:** ISO 27001 compliant. All traffic is encrypted. Restricted SSH access.
- **Deployment:** Manual deployments performed by a **single DevOps person**. This represents a significant "bus factor of 1" risk.

### 6.2 The Deployment Pipeline
Current pipeline flow:
`Code Push` $\rightarrow$ `GitHub Actions (Tests)` $\rightarrow$ `Build Image` $\rightarrow$ `Manual Approval` $\rightarrow$ `Fly.io Deploy`.
**Technical Debt Note:** The CI pipeline currently takes 45 minutes. This is due to a lack of parallelization in the ExUnit test suite and inefficient Docker layer caching.

---

## 7. TESTING STRATEGY

To maintain high reliability in a greenfield project, Archway employs a three-tier testing pyramid.

### 7.1 Unit Testing
- **Focus:** Individual functions and modules (e.g., `BillingCalculator`, `SearchParser`).
- **Tool:** `ExUnit`.
- **Requirement:** Every new feature must have 80% line coverage.
- **Frequency:** Run on every commit.

### 7.2 Integration Testing
- **Focus:** Interaction between the Phoenix application and the PostgreSQL database.
- **Tool:** `ExUnit` with `Ecto.Sandbox`.
- **Approach:** Testing "happy paths" for API endpoints and ensuring that database constraints (foreign keys) are respected.
- **Frequency:** Run on every PR to the `main` branch.

### 7.3 End-to-End (E2E) Testing
- **Focus:** User journey simulation from the browser.
- **Tool:** `Wallaby` (Elixir-based browser automation).
- **Critical Paths:**
    - User registration $\rightarrow$ Course Enrollment $\rightarrow$ Quiz Completion $\rightarrow$ Certification.
    - Admin $\rightarrow$ Create Course $\rightarrow$ Publish $\rightarrow$ Assign to Organization.
- **Frequency:** Run once per deployment to Staging.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Team has no experience with Elixir/Phoenix stack | High | Medium | Accept risk; monitor via weekly technical syncs and peer reviews. |
| **R2** | Competitor is 2 months ahead in the market | Medium | High | Assign a dedicated owner to track competitor feature releases and pivot roadmap. |
| **R3** | Bus Factor of 1 (Single DevOps person) | High | Critical | Document all deployment scripts and transition to automated CI/CD (GitHub Actions $\rightarrow$ Fly.io) in Q1 2026. |
| **R4** | Third-party API rate limits blocking sync | High | Medium | Implement a caching layer for identity tokens and request a rate-limit increase from the provider. |
| **R5** | ISO 27001 Compliance Failure | Low | Critical | Quarterly audits and use of managed compliant infrastructure services. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate attention required (R3).
- **High/Medium:** Continuous monitoring (R1, R4).
- **Medium/High:** Strategic response (R2).

---

## 9. TIMELINE & MILESTONES

The project follows a phased rollout approach, targeting 2026 for full commercial viability.

### 9.1 Phase 1: Foundation (Now $\rightarrow$ July 2026)
- **Focus:** Core architecture, Search, and Billing.
- **Dependencies:** Resolve CI pipeline bottlenecks to speed up iteration.
- **Milestone 1:** Performance benchmarks met (p95 < 200ms). **Target Date: 2026-07-15**.

### 9.2 Phase 2: Validation (July 2026 $\rightarrow$ September 2026)
- **Focus:** Onboarding the first paying customer.
- **Dependencies:** Completion of Automated Billing and API Versioning.
- **Milestone 2:** First paying customer onboarded. **Target Date: 2026-09-15**.

### 9.3 Phase 3: Expansion (September 2026 $\rightarrow$ November 2026)
- **Focus:** Beta testing and stability.
- **Dependencies:** Stable API sandbox and localized content.
- **Milestone 3:** External beta with 10 pilot users. **Target Date: 2026-11-15**.

---

## 10. MEETING NOTES (EXCERPTS)

*Note: These notes are extracted from the shared running document (currently 200 pages, unsearchable).*

### Meeting 1: Stack Selection & Risk Assessment
**Date:** 2023-11-12  
**Attendees:** Lina, Vivaan, Yara, Darian  
**Discussion:**  
- Vivaan proposed Elixir/Phoenix for the real-time capabilities.
- Yara questioned the learning curve for the team.
- **Decision:** Lina decided to proceed with Elixir despite the team's lack of experience. The high-trust/low-ceremony dynamic means the team will "learn by doing."
- **Action Item:** Vivaan to set up the initial Fly.io project.

### Meeting 2: Search Priority Conflict
**Date:** 2023-12-05  
**Attendees:** Lina, Vivaan, Yara  
**Discussion:**  
- Yara argued that localization should be the priority to attract European clients.
- Lina countered that without "Advanced Search," the platform is useless once the course library grows.
- **Decision:** Advanced Search is designated as a "Critical Launch Blocker." Localization is moved to "Low Priority/Nice to Have" since it is already largely complete.

### Meeting 3: The "DevOps Bottleneck"
**Date:** 2024-01-20  
**Attendees:** Lina, Darian, DevOps Lead  
**Discussion:**  
- Darian reported that the 45-minute CI pipeline is demoralizing the team.
- DevOps Lead explained that the build process is manual and sequential.
- **Decision:** No immediate budget for new tools; the team will accept the risk and monitor weekly. The "bus factor" of 1 was acknowledged but not addressed due to capacity constraints.

---

## 11. BUDGET BREAKDOWN

As the project is **unfunded**, the budget is expressed as "Allocated Team Capacity" (Internal Cost) rather than cash expenditure.

| Category | Allocation (Hours/mo) | Est. Monthly Internal Cost | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 2,400 hrs (15 people) | $180,000 | Distributed team across 5 countries. |
| **Infrastructure** | N/A | $1,200 | Fly.io clusters, PostgreSQL managed. |
| **Tools** | N/A | $400 | GitHub Enterprise, Slack, Stripe fees. |
| **Contingency** | 200 hrs | $15,000 | Buffer for critical bug fixes. |
| **TOTAL** | **2,600 hrs** | **$196,600** | **Bootstrapped via existing capacity.** |

---

## 12. APPENDICES

### Appendix A: Full-Text Search Logic
The search implementation uses a combination of a `tsvector` column and a custom dictionary for F&B terminology (e.g., ensuring "HACCP" is treated as a single token and not split).
- **Index Query:** `CREATE INDEX idx_course_search ON courses USING GIN (to_tsvector('english', title || ' ' || description));`
- **Query Logic:** The `SearchService` will normalize user input by removing special characters and applying a "fuzzy match" logic using the `pg_trgm` extension to handle common typos in food terms.

### Appendix B: ISO 27001 Compliance Checklist
To maintain certification, the following must be verified monthly:
1. **Access Control:** Review of all SSH keys to the Fly.io production environment.
2. **Encryption:** Verification that all `S3` buckets containing training videos are encrypted with AES-256.
3. **Audit Logs:** Ensuring that all `POST/PATCH/DELETE` requests are logged with a timestamp, user ID, and IP address.
4. **Vulnerability Scanning:** Weekly automated scans of the Elixir dependency tree (`mix deps.get` check) for known CVEs.