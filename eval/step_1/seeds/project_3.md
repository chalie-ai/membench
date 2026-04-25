Due to the extreme length requirements of this request (6,000–8,000 words), this document is structured as a comprehensive, professional Project Specification Manual. It is designed to serve as the "Single Source of Truth" (SSOT) for the development team at Pivot North Engineering.

***

# PROJECT SPECIFICATION: FATHOM LMS
**Version:** 1.0.4  
**Document Status:** Baseline  
**Date:** October 24, 2023  
**Project Lead:** Valentina Blackwood-Diallo  
**Company:** Pivot North Engineering  
**Classification:** Proprietary / FedRAMP Sensitive  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Pivot North Engineering operates at the vanguard of aerospace innovation. However, the company’s intellectual capital and employee certification tracking are currently managed by a 15-year-old legacy Learning Management System (LMS). This system, referred to internally as "The Monolith," has become a systemic risk. With no longer supported dependencies, frequent unplanned outages, and a database structure that cannot scale to current aerospace regulatory requirements, the legacy system represents a single point of failure for the entire company.

The "Fathom" project is the strategic replacement of this legacy system. Because Pivot North depends on continuous certification for flight-safety compliance, there is a **zero-downtime tolerance** for the transition. Any gap in training records could lead to the grounding of aerospace assets or loss of government contracts.

### 1.2 Project Goals
Fathom is not merely a replacement but a modernization. The goal is to transition from a monolithic, on-premise architecture to a distributed, event-driven microservices platform capable of supporting 10,000+ monthly active users (MAU). The platform must ensure that aerospace engineers can access critical training modules in the field (offline-first) and that all data is handled according to FedRAMP authorization standards to maintain eligibility for US Government contracts.

### 1.3 ROI Projection and Financial Impact
The total investment for Fathom is $3,000,000. The Return on Investment (ROI) is projected across three primary vectors over a 36-month period:

1.  **Operational Efficiency (Estimated $1.2M Saving):** Reduction in manual audit preparation time. The legacy system requires three weeks of manual data aggregation per quarter for FAA/NASA audits; Fathom will automate this into a real-time dashboard.
2.  **Risk Mitigation (Avoidance of $2M+ Penalty):** The legacy system's instability risks non-compliance fines. By achieving FedRAMP authorization, Pivot North secures its $50M+ in annual government contracts.
3.  **Productivity Gain (Estimated $800k Saving):** Implementation of the "Offline-First" mode allows technicians in hangars and remote launch sites to complete certifications without returning to a networked office, increasing billable engineering hours by an estimated 12%.

The projected break-even point is 22 months post-launch, with a total projected 3-year net gain of $1.8M in recovered productivity and avoided risk.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Fathom adopts a Polyglot Microservices architecture. Due to the nature of the transition, the platform must inherit and interoperate with three existing legacy stacks (Java/Spring, Python/Django, and a legacy Node.js utility layer). To decouple these, Fathom utilizes an event-driven backbone powered by Apache Kafka.

### 2.2 The Communication Layer
All services communicate asynchronously via Kafka topics. This ensures that if the Billing module (currently experiencing high technical debt) fails, the Core Learning module remains operational.

**Event Flow Logic:**
*   **Producer:** User completes a module $\rightarrow$ `course.completed` event.
*   **Consumer A:** Certification Service updates the user's badge.
*   **Consumer B:** Analytics Service updates the corporate ROI dashboard.
*   **Consumer C:** Billing Service triggers a license renewal check.

### 2.3 ASCII System Diagram (High-Level)
```text
[ User Interface (React/Next.js) ] 
          |
          v
[ API Gateway / Kong (Rate Limiting & Auth) ]
          |
    ------------------------------------------------------------
    |                 |                   |                    |
[ Auth Service ]  [ Course Service ]  [ User Service ]  [ Billing Service ]
    |                 |                   |                    |
    ------------------------------------------------------------
          |                   |                   |              |
          v                   v                   v              v
    [ PostgreSQL ]      [ MongoDB ]         [ Redis ]       [ PostgreSQL ]
          |                   |                   |              |
          --------------------------------------------------------
                                      |
                             [ Apache Kafka Bus ]
                                      |
          --------------------------------------------------------
          |                           |                            |
    [ Audit Service ]        [ Sync Engine (Offline) ]     [ Export Service ]
          |                           |                            |
    (FedRAMP Logs)             (Local IndexedDB)             (S3 Buckets)
```

### 2.4 Tech Stack Specifications
*   **Frontend:** React 18.2, TypeScript 5.0, Tailwind CSS.
*   **Backend Services:** 
    *   *Course Management:* Go 1.21 (for high concurrency).
    *   *User/Auth:* Java 17 / Spring Boot 3.1.
    *   *Analytics:* Python 3.11 / FastAPI.
*   **Infrastructure:** Kubernetes (EKS), Terraform, GitHub Actions.
*   **Data Stores:** PostgreSQL 15 (Relational), MongoDB 6.0 (Course Content), Redis 7.0 (Caching/Session).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** Critical | **Status:** In Review | **Launch Blocker:** Yes

**Description:**
Aerospace technicians often work in "dead zones" (faraday-shielded hangars or remote runways). The system must allow users to download entire course modules, take quizzes, and upload evidence of completion while offline.

**Functional Requirements:**
*   **Local Storage:** Use IndexedDB via a Service Worker to cache course assets (PDFs, Videos, SCORM packages).
*   **Optimistic UI:** When a user submits a quiz offline, the UI must reflect a "Pending Sync" state immediately.
*   **Conflict Resolution:** The system must use "Last Write Wins" for profile updates, but "Additive Logic" for course progress. If a user completes Module A on a tablet (offline) and Module B on a desktop (online), the sync engine must merge these into a completed set.
*   **Background Sync:** Implementation of the `PeriodicSync` API to push local changes to the server the moment a stable heartbeat is detected.

**Technical Constraints:**
*   Maximum local cache size: 500MB per user.
*   Sync frequency: Every 60 seconds when online; immediate on heartbeat recovery.

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** In Review

**Description:**
To migrate from the 15-year-old legacy system, Fathom must ingest massive amounts of unstructured and semi-structured data. The system must automatically detect if a file is CSV, JSON, XML, or a proprietary legacy `.PNE` aerospace format.

**Functional Requirements:**
*   **MIME-type Detection:** Use magic-number byte analysis rather than relying on file extensions.
*   **Mapping Engine:** A UI-based mapper allowing admins to drag-and-drop "Source Column" $\rightarrow$ "Fathom Field."
*   **Validation Pipeline:** Every import must go through a "Staging Table" where data is validated against the schema. Errors must be highlighted in a red-line report before final commit.
*   **Export Formats:** Support for PDF (Certificates), CSV (Audit logs), and JSON (API integrations).

**Technical Constraints:**
*   Maximum upload size: 2GB per file.
*   Processing must happen in a background worker (Celery/RabbitMQ) to avoid timing out the API gateway.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Design

**Description:**
To prevent system instability—especially given the technical debt in the billing module—the platform must implement strict rate limiting. This protects the system from both malicious actors and poorly written internal scripts.

**Functional Requirements:**
*   **Tiered Limiting:**
    *   *Standard User:* 100 requests/minute.
    *   *Admin/Power User:* 500 requests/minute.
    *   *System Integration:* 2,000 requests/minute.
*   **Algorithm:** Use a "Token Bucket" algorithm implemented at the Kong Gateway level.
*   **Analytics Dashboard:** A real-time view for engineers to see which endpoints are under the most stress.
*   **Automatic Throttling:** If the Billing service latency exceeds 500ms, the gateway should automatically reduce the rate limit for non-essential billing queries.

**Technical Constraints:**
*   Latency overhead for rate-check must be $< 10\text{ms}$.
*   Headers must include `X-RateLimit-Remaining` and `X-RateLimit-Reset`.

### 3.4 A/B Testing Framework (Feature Flag Integrated)
**Priority:** Medium | **Status:** In Design

**Description:**
Fathom will utilize a "Canary" deployment strategy. The A/B testing framework allows the product team to roll out new UI layouts or pedagogical methods to 5% of the user base before a full release.

**Functional Requirements:**
*   **Flag Management:** A centralized dashboard to toggle features (ON/OFF/Percentage).
*   **User Segmentation:** Ability to target flags based on department (e.g., "Avionics Team" vs "Structural Team").
*   **Metric Tracking:** Integration with the Analytics service to compare completion rates between Version A and Version B.
*   **Automatic Rollback:** If the error rate for Version B exceeds 2% over a 10-minute window, the flag must automatically revert to Version A.

**Technical Constraints:**
*   Flags must be cached on the client side via Redis to avoid a round-trip request on every page load.

### 3.5 Webhook Integration Framework
**Priority:** Low | **Status:** Not Started

**Description:**
A "Nice-to-have" feature that allows third-party tools (e.g., Slack, Jira, external HR systems) to subscribe to Fathom events.

**Functional Requirements:**
*   **Subscription Portal:** Users can enter a URL and select events (e.g., `user.certified`).
*   **Retry Logic:** Exponential backoff for failed webhook deliveries (1min, 5min, 15min, 1hr).
*   **Security:** HMAC signatures in the header to allow the receiving end to verify the payload came from Fathom.
*   **Payload Customization:** Ability to choose between a "Compact" payload (ID and Event) or a "Full" payload (Complete User object).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Authentication is required via JWT in the Authorization Header.

### 4.1 User Management
**`GET /users/{userId}`**
*   **Description:** Retrieve detailed user profile and certification status.
*   **Request:** `GET /api/v1/users/USR-99281`
*   **Response (200 OK):**
    ```json
    {
      "userId": "USR-99281",
      "name": "John Doe",
      "role": "Aerospace Engineer",
      "certifications": ["FAA-101", "NASA-SOP-22"],
      "status": "active"
    }
    ```

**`POST /users/sync`**
*   **Description:** Endpoint for the Offline-First sync engine to push local changes.
*   **Request:** 
    ```json
    {
      "userId": "USR-99281",
      "changes": [
        {"module": "SOP-01", "status": "completed", "timestamp": "2026-01-10T10:00Z"}
      ]
    }
    ```
*   **Response (202 Accepted):** `{"status": "sync_queued", "jobId": "JOB-112"}`

### 4.2 Course & Learning
**`GET /courses`**
*   **Description:** List all available courses with pagination.
*   **Request:** `GET /api/v1/courses?page=1&limit=20`
*   **Response (200 OK):**
    ```json
    {
      "courses": [{"id": "CRS-01", "title": "Turbine Maintenance", "level": "Advanced"}],
      "pagination": {"total": 150, "pages": 8}
    }
    ```

**`POST /courses/{courseId}/complete`**
*   **Description:** Mark a course as complete.
*   **Request:** `POST /api/v1/courses/CRS-01/complete`
*   **Response (200 OK):** `{"completionDate": "2026-02-01", "certificateUrl": "https://fathom.pne.com/cert/123"}`

### 4.3 System & Administration
**`GET /admin/analytics/usage`**
*   **Description:** Fetch API usage statistics for rate-limiting monitoring.
*   **Request:** `GET /api/v1/admin/analytics/usage`
*   **Response (200 OK):**
    ```json
    {
      "totalRequests": 1500000,
      "peakRequestRate": "450req/sec",
      "topEndpoints": ["/users", "/courses"]
    }
    ```

**`POST /admin/import/detect`**
*   **Description:** Upload a file to detect its format before import.
*   **Request:** Multipart Form Data (File)
*   **Response (200 OK):** `{"detectedFormat": "CSV", "confidence": 0.99, "suggestedMapper": "Legacy_User_v2"}`

### 4.4 Billing & Licensing
**`GET /billing/status`**
*   **Description:** Check current license seat availability.
*   **Request:** `GET /api/v1/billing/status`
*   **Response (200 OK):** `{"seatsUsed": 850, "seatsTotal": 1000, "expiryDate": "2027-01-01"}`

**`POST /billing/update-seats`**
*   **Description:** Add or remove license seats.
*   **Request:** `{"action": "add", "quantity": 50}`
*   **Response (200 OK):** `{"newTotal": 1050, "invoiceId": "INV-2023-99"}`

---

## 5. DATABASE SCHEMA

Fathom uses a hybrid data strategy. Core user/billing data is in PostgreSQL, while course content (which varies wildly in structure) is in MongoDB.

### 5.1 PostgreSQL Schema (Relational)

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | - | `email`, `password_hash`, `mfa_secret`, `role_id` | Core user identity. |
| `roles` | `role_id` | - | `role_name`, `permissions_bitmask` | RBAC definition. |
| `certifications` | `cert_id` | `user_id`, `course_id` | `issue_date`, `expiry_date`, `issuer_id` | Tracked professional certs. |
| `billing_accounts`| `acc_id` | - | `company_name`, `tax_id`, `billing_cycle` | Corporate billing info. |
| `subscriptions` | `sub_id` | `acc_id` | `seat_count`, `plan_type`, `status` | Current license status. |
| `audit_logs` | `log_id` | `user_id` | `action`, `timestamp`, `ip_address`, `resource_id` | FedRAMP compliance logs. |
| `rate_limits` | `limit_id` | `user_id` | `request_count`, `reset_time`, `tier_id` | Real-time quota tracking. |
| `feature_flags` | `flag_id` | - | `flag_key`, `is_enabled`, `percentage_rollout` | A/B test controls. |
| `user_segments` | `seg_id` | `user_id` | `segment_name` (e.g., "Avionics") | Target groups for flags. |
| `sync_sessions` | `sess_id` | `user_id` | `last_sync_timestamp`, `device_id`, `status` | Offline sync heartbeat. |

### 5.2 MongoDB Collections (Document)
*   **`course_content`**: stores HTML, JSON, and Markdown for course modules.
    *   `_id`, `course_id`, `module_index`, `content_body`, `media_assets` (Array of S3 links).
*   **`quiz_definitions`**: stores complex questioning logic.
    *   `_id`, `course_id`, `questions` (Array of objects with logic-branching).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Fathom utilizes a three-tier environment system to ensure zero-downtime and FedRAMP compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and unit testing.
*   **Infrastructure:** Minimal K8s cluster, Mock Kafka.
*   **Deployment:** Automated push on every commit to `develop` branch.

#### 6.1.2 Staging (Staging/QA)
*   **Purpose:** Integration testing, QA validation, and User Acceptance Testing (UAT).
*   **Infrastructure:** Mirror of Production (1:1 scale).
*   **Deployment:** Triggered by `release/*` branches. This is where Saoirse Mahmoud-Reyes performs regression testing.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live end-user traffic.
*   **Infrastructure:** Multi-region EKS (AWS) with FedRAMP High baseline.
*   **Deployment Strategy:** **Blue-Green Deployment**. 
    *   The "Green" environment is spun up with the new version.
    *   Traffic is shifted gradually (10% $\rightarrow$ 50% $\rightarrow$ 100%) via the Kong API Gateway.
    *   If any 5xx errors spike, the gateway instantly routes traffic back to "Blue."

### 6.2 CI/CD Pipeline (GitHub Actions)
1.  **Lint & Test:** Run ESLint and Jest on every PR.
2.  **Build:** Dockerize microservices into images.
3.  **Security Scan:** Run Snyk and SonarQube for vulnerability detection (FedRAMP requirement).
4.  **Deploy to Staging:** Deploy to K8s staging namespace.
5.  **Manual Approval:** Project Lead (Valentina) approves the production release.
6.  **Blue-Green Shift:** Trigger Terraform script to shift traffic in Prod.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Coverage Target:** 80% minimum for all new services.
*   **Tooling:** Jest (Frontend), JUnit (Java), PyTest (Python), GoTest (Go).
*   **Focus:** Business logic, data transformation, and API request validation.

### 7.2 Integration Testing
*   **Focus:** The "Handshake" between microservices via Kafka.
*   **Method:** Use Testcontainers to spin up a real Kafka and PostgreSQL instance during the CI build.
*   **Scenario:** Verify that a `course.completed` event in the Course Service correctly updates the `certifications` table in the User Service.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Critical Path Testing:**
    *   User Login $\rightarrow$ Course Selection $\rightarrow$ Quiz Completion $\rightarrow$ Certificate Generation.
    *   Offline Mode: Simulate network loss $\rightarrow$ Complete Quiz $\rightarrow$ Restore Network $\rightarrow$ Verify Sync.
*   **QA Lead:** Saoirse Mahmoud-Reyes is the final signatory for E2E success.

### 7.4 The Billing Module Special Case
Due to the existing technical debt (zero test coverage), the Billing module will undergo a **"Strangler Fig" migration**. Instead of fixing the legacy code, new billing logic will be written in a new service, and calls will be intercepted and routed to the new service one by one until the legacy module is deprecated.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor building similar LMS, 2 months ahead. | High | High | **Parallel-Path:** Simultaneously prototype a "Lightweight" version of Fathom to beat them to market with core features. | Valentina |
| R-02 | Primary Vendor EOL (End-of-Life) announcement. | Medium | Critical | **Dedicated Owner:** Assign a team member to evaluate alternative vendors and create a migration bridge. | Kai |
| R-03 | FedRAMP Audit Failure. | Low | Critical | **Pre-Audit:** Conduct internal "Mock Audits" every quarter starting in 2025. | Saoirse |
| R-04 | Zero-Downtime Migration Failure. | Medium | High | **Blue-Green:** Use strict blue-green deployments with instant rollback capability. | Kai |
| R-05 | Design Disagreement (Product vs Eng). | High | Medium | **Escalation Path:** Bi-weekly steering committee meetings with executive sponsors. | Valentina |

**Probability/Impact Matrix:**
*   High Prob/High Impact $\rightarrow$ **Immediate Action**
*   Low Prob/Critical Impact $\rightarrow$ **Contingency Planning**

---

## 9. TIMELINE & MILESTONES

### 9.1 Phases of Development
*   **Phase 1: Foundation (Current - 2026-03)**
    *   Establish Kafka Bus.
    *   Implement Core Auth and User Services.
    *   Address Billing module debt.
*   **Phase 2: Feature Hardening (2026-03 - 2026-06)**
    *   Finalize Offline-First Sync.
    *   Deploy Data Import/Export tools.
    *   Security Hardening for FedRAMP.
*   **Phase 3: Validation & Launch (2026-06 - 2026-08)**
    *   Internal Alpha.
    *   External Beta.
    *   Final Cutover from Legacy System.

### 9.2 Key Milestones
| Milestone | Description | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| M1 | Security Audit Passed (FedRAMP) | 2026-03-15 | CI/CD Security Scans |
| M2 | External Beta (10 Pilot Users) | 2026-05-15 | Offline-First Review |
| M3 | Internal Alpha Release | 2026-07-15 | Data Import Validation |
| M4 | Full Production Cutover | 2026-09-01 | M1, M2, M3 Complete |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-12  
**Attendees:** Valentina, Kai, Gael, Saoirse  
**Discussion:**
*   Kai expressed concerns regarding the interoperation of the three legacy stacks. He argued that trying to "bridge" them would create more debt.
*   Gael (Consultant from Lisbon) suggested using Kafka as an abstraction layer to decouple the legacy systems from the new microservices.
*   Valentina agreed, provided that the latency for the "Offline-First" sync is not affected.
*   **Decision:** Fathom will use an Event-Driven Architecture (EDA) with Kafka.

**Action Items:**
*   [Kai] Draft Kafka Topic Schema for `user.events`.
*   [Valentina] Confirm budget for managed Kafka instance (Confluent).

### Meeting 2: The "Billing Debt" Crisis
**Date:** 2023-12-05  
**Attendees:** Valentina, Kai, Saoirse  
**Discussion:**
*   Saoirse reported that the billing module has 0% test coverage and is failing intermittently under load.
*   Valentina noted that the module was deployed under extreme deadline pressure during the previous project.
*   Kai proposed a full rewrite, but Valentina rejected it due to the $3M budget constraints and timeline.
*   **Decision:** Implement the "Strangler Fig" pattern. New features go into a new service; old features are migrated gradually.

**Action Items:**
*   [Kai] Identify the top 5 most critical endpoints in the billing module for migration.
*   [Saoirse] Create a regression suite for the current billing behavior.

### Meeting 3: Feature Priority Conflict
**Date:** 2024-01-20  
**Attendees:** Valentina, Kai, Gael  
**Discussion:**
*   Product Lead (External) wants the Webhook framework prioritized.
*   Engineering (Kai) insists that Offline-First mode is a "Launch Blocker" and must take priority.
*   Gael mediated, pointing out that without Offline-First, the aerospace technicians cannot use the tool in the field, rendering the product useless for 40% of the workforce.
*   **Decision:** Offline-First remains "Critical." Webhooks moved to "Low" priority.

**Action Items:**
*   [Valentina] Communicate the priority shift to the Product Lead.
*   [Kai] Update the Jira roadmap to reflect Offline-First as a blocker.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $1,800,000 | 20+ staff across 3 departments (Dev, QA, Ops) over 24 months. |
| **Infrastructure** | 20% | $600,000 | AWS FedRAMP High instances, Confluent Kafka, MongoDB Atlas. |
| **External Consulting**| 10% | $300,000 | Gael Vasquez-Okafor & specialized FedRAMP auditors. |
| **Software/Tools** | 5% | $150,000 | Snyk, SonarQube, GitHub Enterprise, Jira/Confluence. |
| **Contingency** | 5% | $150,000 | Emergency fund for critical vendor EOL replacements. |

---

## 12. APPENDICES

### Appendix A: FedRAMP Compliance Checklist
To achieve authorization, Fathom must implement the following:
1.  **FIPS 140-2 Validated Encryption:** All data at rest and in transit must use FIPS-validated modules.
2.  **Multi-Factor Authentication (MFA):** Mandatory for all users; support for PIV/CAC cards.
3.  **Continuous Monitoring:** Real-time alerting via CloudWatch and integration with a centralized SOC.
4.  **Incident Response Plan:** A documented process for reporting breaches within 1 hour of discovery.

### Appendix B: Data Migration Strategy (Legacy $\rightarrow$ Fathom)
The migration will follow a **"Parallel Run"** strategy:
1.  **Shadow Mode:** The legacy system remains the "System of Record." Fathom receives all updates via a data bridge but does not allow edits.
2.  **Comparison Phase:** A daily script compares the state of the legacy DB and the Fathom DB. Discrepancies are logged.
3.  **Write-Through Phase:** Fathom becomes the "System of Record." Changes are written to Fathom first, then synced back to the legacy system for 30 days as a safety net.
4.  **Sunset Phase:** The legacy system is set to read-only and then decommissioned.