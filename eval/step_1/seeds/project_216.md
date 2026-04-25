Due to the extreme length requirement (6,000–8,000 words), this document is structured as a Comprehensive Project Specification. To maintain the level of detail required for a development team's daily reference, it expands the provided constraints into a full-scale engineering manual.

***

# PROJECT SPECIFICATION: DRIFT LMS
**Document Version:** 1.0.4  
**Last Updated:** 2024-05-22  
**Status:** Active/Development  
**Classification:** Internal - Tundra Analytics Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Drift" is a strategic initiative by Tundra Analytics designed to dominate the educational training sector within the renewable energy industry. As the global transition to green energy accelerates, there is a critical shortage of certified technicians and engineers. Tundra Analytics is pivoting from a pure data-services firm to an ecosystem provider by launching Drift, a Learning Management System (LMS) specifically tailored for the high-compliance, high-technicality requirements of wind, solar, and hydrogen energy sectors.

The core value proposition of Drift lies in its strategic partnership integration. Unlike generic LMS platforms (e.g., Moodle, Canvas), Drift is designed to sync in real-time with an external industry-standard API provided by a strategic partner. This allows Drift to pull real-time certification requirements and regulatory updates, ensuring that the educational content is always compliant with current energy laws.

### 1.2 ROI Projection and Strategic Goals
Tundra Analytics has allocated a budget of $1.5M for the development and launch of Drift. The projected Return on Investment (ROI) is calculated based on a B2B SaaS model targeting mid-to-large scale energy firms.

*   **Projected Revenue:** Estimated $3.2M in Annual Recurring Revenue (ARR) by Year 2.
*   **Customer Acquisition Cost (CAC):** Projected at $12,000 per enterprise client.
*   **Lifetime Value (LTV):** Estimated at $140,000 per client over a 3-year contract.
*   **Payback Period:** 14 months post-launch.

The primary business driver is the "First Mover" advantage in the renewable energy niche. While competitors are building similar tools, Drift’s integration with the external partner API creates a "moat" that makes the platform indispensable for compliance officers.

### 1.3 Project Scope
The scope encompasses the development of a three-tier architecture capable of handling multi-tenant educational content, rigorous security protocols (SOC 2), and a complex interoperability layer between three inherited legacy stacks. The project will transition from a design-blocked state into an MVP by September 2025, culminating in a pilot program with 10 high-value energy firms.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Drift utilizes a traditional three-tier architecture:
1.  **Presentation Tier:** A responsive React-based frontend utilizing Tailwind CSS for rapid UI iteration.
2.  **Business Logic Tier:** A mixed-stack backend consisting of a legacy Node.js service (inherited), a Python/FastAPI service (for data processing), and a Go-based API Gateway.
3.  **Data Tier:** A PostgreSQL primary database for relational data, Redis for caching/session management, and an S3-compatible bucket for course material (PDFs, Videos).

### 2.2 The "Mixed Stack" Challenge
Because Tundra Analytics is inheriting three different stacks, the architecture focuses on an **API-First Orchestration** model. The Go Gateway acts as the primary entry point, routing requests to the appropriate micro-service based on the endpoint path. Communication between services is handled via REST and asynchronous events via RabbitMQ.

### 2.3 ASCII Architecture Diagram
```text
[ Client Browser/App ] 
        |
        v (HTTPS / TLS 1.3)
[ Cloudflare WAF / Load Balancer ]
        |
        v
[ Go API Gateway (Auth / Rate Limiting) ] <--- [ Redis Cache ]
        |
        +-----------------------+-----------------------+
        |                       |                       |
[ Node.js Legacy Service ] [ Python FastAPI ] [ Go Core Service ]
(Course Management)        (Data Analytics)    (User/Billing)
        |                       |                       |
        +-----------------------+-----------------------+
                                |
                                v
                    [ PostgreSQL Primary Cluster ]
                                |
                    [ S3 Course Material Storage ]
                                |
                    [ External Partner API Sync ]
```

### 2.4 Deployment Pipeline
Drift utilizes **GitLab CI** for a fully automated pipeline. 
- **Build Phase:** Docker images are built and pushed to a private registry.
- **Test Phase:** Automated unit and integration tests must pass (100% success rate) before promotion.
- **Deployment Phase:** Rolling updates to a **Kubernetes (K8s)** cluster. This ensures zero-downtime deployments. If a health check fails, K8s automatically rolls back to the previous stable version.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** 
Security is paramount given the SOC 2 Type II requirement. Drift must implement a robust 2FA system that goes beyond SMS/Email codes, supporting FIDO2/WebAuthn standards for hardware keys (e.g., YubiKey).

**Technical Requirements:**
- **WebAuthn Integration:** Implementation of the `navigator.credentials.create` and `navigator.credentials.get` APIs for hardware key registration.
- **Fallback Mechanisms:** While hardware keys are preferred, users must be able to register TOTP (Time-based One-Time Password) apps (Google Authenticator, Authy).
- **Recovery Codes:** Generation of 10 one-time use recovery codes upon 2FA activation.
- **Session Management:** 2FA must be validated at every login and again for "High-Privilege" actions (e.g., changing billing details or deleting courses).

**Business Logic:** 
Users are prompted to set up 2FA upon their first login. For enterprise clients, the administrator can "Force 2FA," preventing any user from accessing the platform until a hardware key or TOTP app is linked.

**Current Blocker:** There is a design disagreement between the Product Lead and Engineering Lead regarding the "Enrollment UX." Product wants a "skip for now" option, while Engineering argues this violates the SOC 2 security posture required for the July 15th audit.

### 3.2 Localization and Internationalization (L10n/i18n)
**Priority:** Low | **Status:** In Progress
**Description:** 
To serve the global renewable energy market, Drift must support 12 languages, including English, Spanish, German, Mandarin, French, Arabic, Portuguese, Japanese, Korean, Hindi, Dutch, and Italian.

**Technical Requirements:**
- **i18next Framework:** Implementation of the `i18next` library for the frontend.
- **Translation Keys:** All hardcoded strings must be replaced by keys (e.g., `common.welcome_message`) mapping to JSON translation files.
- **Right-to-Left (RTL) Support:** The CSS architecture must support `dir="rtl"` for Arabic, requiring a mirroring of the layout grid.
- **Dynamic Content Translation:** Integration with a translation API (e.g., DeepL) to provide "draft" translations for course content created by users.

**Logic:** 
The system will detect the browser's locale by default but allow users to manually override the language in their profile settings. Dates and currencies must be formatted according to the selected locale using the `Intl` JavaScript API.

### 3.3 Automated Billing and Subscription Management
**Priority:** Low | **Status:** Not Started
**Description:** 
Drift requires a multi-tier subscription model (Basic, Professional, Enterprise) with automated recurring billing.

**Technical Requirements:**
- **Stripe Integration:** Integration via Stripe Billing for subscription lifecycle management (trial, active, past_due, canceled).
- **Webhooks:** A dedicated `/api/webhooks/stripe` endpoint to process events such as `invoice.payment_succeeded` and `customer.subscription.deleted`.
- **Proration Logic:** Ability to handle mid-cycle seat additions (e.g., adding 50 students to an enterprise account mid-month).
- **Invoice Generation:** Automated PDF invoice generation delivered via email and stored in the user's "Billing History" tab.

**Logic:** 
The platform will utilize a "Seat-Based" pricing model. Admins are billed per active user. A "Grace Period" of 7 days will be implemented for failed payments before account suspension.

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Blocked
**Description:** 
To protect the system from abuse and to provide data for the "Enterprise" tier, Drift must implement strict rate limiting and a detailed analytics dashboard for API usage.

**Technical Requirements:**
- **Token Bucket Algorithm:** Implementation of the token bucket algorithm at the Go Gateway level.
- **Tiers of Access:** 
    - Free: 100 requests/hour.
    - Pro: 5,000 requests/hour.
    - Enterprise: Custom limits.
- **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Pipeline:** Usage logs are streamed via Fluentd to an ElasticSearch cluster for visualization in a Kibana dashboard.

**Current Blocker:** The blocking issue is the lack of a finalized "Usage Policy" from the legal team, as the rate limits must be contractually binding for Enterprise clients.

### 3.5 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** In Design
**Description:** 
Users must be able to migrate students and course data from legacy systems into Drift.

**Technical Requirements:**
- **MIME Type Detection:** Use of the `magic` library to detect file types (CSV, JSON, XML, XLSX) regardless of the file extension.
- **Mapping Interface:** A UI-based "Field Mapper" where users can map their CSV columns (e.g., "Student_Name") to Drift's schema ("full_name").
- **Asynchronous Processing:** Large imports (>10MB) must be processed as background jobs using Celery (Python) to avoid blocking the HTTP thread.
- **Validation Phase:** A "Pre-flight" check that scans the data for errors (e.g., invalid email formats) and reports them before the actual import begins.

**Logic:** 
Export functionality will allow users to download their entire organizational data dump in JSON format, ensuring data portability and compliance with GDPR/CCPA.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a Bearer Token in the `Authorization` header.

### 4.1 User Authentication
- **Endpoint:** `POST /auth/login`
- **Description:** Authenticates user and returns a JWT.
- **Request:**
  ```json
  {
    "email": "user@tundra.com",
    "password": "securepassword123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGci... ",
    "expires_at": "2025-05-22T12:00:00Z",
    "requires_2fa": true
  }
  ```

### 4.2 2FA Verification
- **Endpoint:** `POST /auth/verify-2fa`
- **Description:** Validates the hardware key or TOTP code.
- **Request:**
  ```json
  {
    "user_id": "uuid-12345",
    "code": "543210"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "verified",
    "session_token": "sess_abc123"
  }
  ```

### 4.3 Course Retrieval
- **Endpoint:** `GET /courses/{course_id}`
- **Description:** Fetches detailed metadata for a specific course.
- **Response (200 OK):**
  ```json
  {
    "id": "course-99",
    "title": "Wind Turbine Maintenance 101",
    "modules": 12,
    "certification_id": "CERT-WIND-01",
    "status": "published"
  }
  ```

### 4.4 Student Enrollment
- **Endpoint:** `POST /enrollments`
- **Description:** Enrolls a student in a course.
- **Request:**
  ```json
  {
    "student_id": "uuid-789",
    "course_id": "course-99",
    "enrollment_date": "2025-06-01"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "enrollment_id": "enr-555",
    "status": "active"
  }
  ```

### 4.5 Billing Tier Update
- **Endpoint:** `PATCH /billing/subscription`
- **Description:** Updates the subscription level for an organization.
- **Request:**
  ```json
  {
    "plan_id": "plan_enterprise_monthly",
    "seat_count": 150
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "new_monthly_total": 4500.00,
    "currency": "USD"
  }
  ```

### 4.6 Language Preference
- **Endpoint:** `PUT /user/settings/locale`
- **Description:** Updates the user's preferred language.
- **Request:**
  ```json
  {
    "language_code": "de-DE",
    "timezone": "Europe/Berlin"
  }
  ```
- **Response (204 No Content)**

### 4.7 API Usage Stats
- **Endpoint:** `GET /analytics/usage`
- **Description:** Returns the current month's API consumption.
- **Response (200 OK):**
  ```json
  {
    "total_requests": 125000,
    "peak_rps": 45,
    "error_rate": "0.02%"
  }
  ```

### 4.8 Data Export Request
- **Endpoint:** `POST /export/request`
- **Description:** Triggers an asynchronous data export.
- **Request:**
  ```json
  {
    "format": "json",
    "scope": "all_students"
  }
  ```
- **Response (202 Accepted):**
  ```json
  {
    "job_id": "job-abc-123",
    "estimated_completion": "2025-05-22T14:00:00Z"
  }
  ```

---

## 5. DATABASE SCHEMA

Drift uses a PostgreSQL 15 relational database. All tables utilize UUIDs as primary keys to ensure compatibility across the mixed-stack services.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK)
    - `email` (VARCHAR, Unique, Indexed)
    - `password_hash` (TEXT)
    - `mfa_enabled` (BOOLEAN)
    - `mfa_secret` (TEXT, Encrypted)
    - `locale` (VARCHAR(5))
    - `created_at` (TIMESTAMP)

2.  **`organizations`**
    - `id` (UUID, PK)
    - `org_name` (VARCHAR)
    - `subscription_plan` (ENUM: 'basic', 'pro', 'enterprise')
    - `stripe_customer_id` (VARCHAR)
    - `tax_id` (VARCHAR)

3.  **`courses`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK -> organizations.id)
    - `title` (VARCHAR)
    - `description` (TEXT)
    - `version` (INT)
    - `is_published` (BOOLEAN)

4.  **`modules`**
    - `id` (UUID, PK)
    - `course_id` (UUID, FK -> courses.id)
    - `order_index` (INT)
    - `content_url` (TEXT)
    - `module_type` (ENUM: 'video', 'quiz', 'reading')

5.  **`enrollments`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `course_id` (UUID, FK -> courses.id)
    - `progress_percent` (DECIMAL)
    - `completion_date` (TIMESTAMP, Nullable)

6.  **`certifications`**
    - `id` (UUID, PK)
    - `external_api_ref` (VARCHAR, Indexed)
    - `cert_name` (VARCHAR)
    - `validity_months` (INT)

7.  **`user_certifications`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `cert_id` (UUID, FK -> certifications.id)
    - `issued_at` (TIMESTAMP)
    - `expires_at` (TIMESTAMP)

8.  **`api_usage_logs`**
    - `id` (BIGINT, PK)
    - `user_id` (UUID, FK -> users.id)
    - `endpoint` (VARCHAR)
    - `response_code` (INT)
    - `timestamp` (TIMESTAMP)

9.  **`billing_invoices`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK -> organizations.id)
    - `amount` (DECIMAL)
    - `status` (ENUM: 'paid', 'pending', 'failed')
    - `invoice_date` (DATE)

10. **`import_jobs`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK -> users.id)
    - `status` (ENUM: 'pending', 'processing', 'completed', 'failed')
    - `error_log` (TEXT)

### 5.2 Relationships
- **One-to-Many:** `Organizations` $\rightarrow$ `Users`, `Organizations` $\rightarrow$ `Courses`, `Courses` $\rightarrow$ `Modules`.
- **Many-to-Many:** `Users` $\leftrightarrow$ `Courses` (via `Enrollments`), `Users` $\leftrightarrow$ `Certifications` (via `User_Certifications`).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Drift maintains three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and internal testing.
- **Deployment:** Automatic trigger on any commit to the `develop` branch.
- **Database:** Shared Dev DB with mocked external API data.
- **Scaling:** Single pod per service to minimize costs.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation, QA testing, and UAT (User Acceptance Testing).
- **Deployment:** Triggered by Merge Requests to the `release` branch.
- **Database:** A sanitized clone of production data (PII stripped).
- **Scaling:** Mirrors production architecture (3 pods per service) to test load balancing.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer traffic.
- **Deployment:** Manual approval required in GitLab CI; rolling updates.
- **Database:** High-Availability (HA) PostgreSQL cluster with synchronous replication.
- **Scaling:** Horizontal Pod Autoscaler (HPA) based on CPU/Memory utilization.

### 6.2 Infrastructure as Code (IaC)
The entire stack is provisioned using **Terraform**. This ensures that if a regional outage occurs, the entire environment can be spun up in a different AWS region within 30 minutes.

### 6.3 Security Hardening
To meet **SOC 2 Type II** compliance:
- **Network Isolation:** All backend services are in a private subnet; only the Go Gateway is exposed via the Load Balancer.
- **Encryption:** Data at rest is encrypted using AES-256. Data in transit is forced over TLS 1.3.
- **Audit Logs:** Every administrative action is logged to a read-only S3 bucket with Object Lock enabled.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Goal:** Verify individual functions and logic in isolation.
- **Tooling:** `Jest` (Node.js), `PyTest` (Python), `go test` (Go).
- **Requirement:** 80% minimum code coverage for all new business logic.
- **Execution:** Run on every GitLab push.

### 7.2 Integration Testing
- **Goal:** Ensure services communicate correctly across the "Mixed Stack."
- **Approach:** Contract Testing. Using **Pact**, we define the expected request/response between the Go Gateway and the Python/Node.js services.
- **Focus:** Specifically testing the sync with the External Partner API to ensure that a change in their schema doesn't crash the Drift pipeline.

### 7.3 End-to-End (E2E) Testing
- **Goal:** Validate complete user journeys (e.g., "User signs up $\rightarrow$ Enrolls in Course $\rightarrow$ Completes Quiz $\rightarrow$ Receives Certificate").
- **Tooling:** **Playwright** for browser automation.
- **Execution:** Run on the Staging environment before every release.

### 7.4 QA Process
Nadira Costa (QA Lead) manages the "Bug Bash" sessions every Friday. All critical bugs found in E2E testing must be resolved before the `release` branch can be merged into `main`.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with mixed tech stack | High | Medium | Weekly technical reviews; accept risk and monitor. | Lior Jensen |
| R-02 | Competitor is 2 months ahead in market | Medium | High | Dedicated owner to track competitor features and pivot. | Lior Jensen |
| R-03 | External API downtime/instability | Medium | High | Implement aggressive caching and circuit breaker patterns. | Selin Oduya |
| R-04 | Failure to achieve SOC 2 compliance | Low | Critical | Early engagement with auditors; strict audit logging. | Nadira Costa |
| R-05 | Budget overrun due to K8s costs | Low | Medium | Implement strict resource limits and auto-scaling. | Asha Jensen |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure.
- **High:** Significant delay or budget increase.
- **Medium:** Manageable with effort.
- **Low:** Negligible impact.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation & Security (Now $\rightarrow$ 2025-07-15)
- **Focus:** Core infrastructure, Go Gateway, and the SOC 2 audit.
- **Key Dependency:** Resolution of the 2FA design disagreement.
- **Milestone 1:** Security Audit Passed (Target: 2025-07-15).

### 9.2 Phase 2: MVP Development (2025-07-16 $\rightarrow$ 2025-09-15)
- **Focus:** Course management, Student enrollment, and External API sync.
- **Key Dependency:** Stable API documentation from the strategic partner.
- **Milestone 2:** MVP Feature-Complete (Target: 2025-09-15).

### 9.3 Phase 3: Beta & Refinement (2025-09-16 $\rightarrow$ 2025-11-15)
- **Focus:** Pilot user onboarding, performance tuning, and bug fixing.
- **Key Dependency:** Recruitment of 10 pilot organizations.
- **Milestone 3:** External Beta with 10 users (Target: 2025-11-15).

### 9.4 Phase 4: Scaling & Polishing (2025-11-16 $\rightarrow$ Launch)
- **Focus:** L10n, Billing automation, and Usage analytics.

---

## 10. MEETING NOTES

*Note: These notes are extracted from the shared 200-page running document (unsearchable). Dates are approximate based on project trajectory.*

### Meeting 1: The "Stack Clash" Discussion
**Date:** 2024-06-10  
**Attendees:** Lior, Selin, Nadira, Asha  
**Discussion:** Selin expressed concern that maintaining three different languages (Go, Python, Node) is a "maintenance nightmare." Lior reminded the team that these were inherited and we cannot rewrite them all without blowing the budget.  
**Decision:** The team agreed to a "low-ceremony" approach. We will not rewrite the legacy Node.js service unless it becomes a critical performance bottleneck. All new business logic will be written in Go for the Gateway and Python for data-heavy tasks.  
**Action Item:** Selin to map out all legacy endpoints.

### Meeting 2: 2FA Design Deadlock
**Date:** 2024-07-02  
**Attendees:** Lior, Nadira  
**Discussion:** Heated debate over the "Skip for Now" button on the 2FA setup screen. Lior (Product) wants it to reduce churn. Nadira (QA/Security) argues that if they skip it now, they will never do it, and the SOC 2 audit will fail.  
**Decision:** No decision made. Lior requested a compromise where users can skip for 24 hours, but the account is locked until 2FA is enabled.  
**Status:** Current Blocker.

### Meeting 3: The "Stdout" Crisis
**Date:** 2024-08-12  
**Attendees:** Lior, Asha, Selin  
**Discussion:** Asha spent 6 hours trying to debug a production crash because the system has no structured logging. He had to read raw stdout logs from the K8s pods, which were interleaved and unreadable.  
**Decision:** Acknowledge as significant Technical Debt.  
**Action Item:** Selin to implement `Zap` (Go) and `Structlog` (Python) across all services by the end of the month.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$1,500,000 USD**

### 11.1 Personnel ($950,000)
- **Lior Jensen (CTO/Lead):** $250,000 (Salary + Equity)
- **Selin Oduya (Data Eng):** $220,000
- **Nadira Costa (QA Lead):** $210,000
- **Asha Jensen (Support Eng):** $180,000
- **Contractor (SOC 2 Auditor):** $90,000 (Flat fee)

### 11.2 Infrastructure & Tooling ($320,000)
- **AWS/K8s Cluster:** $120,000 (Annual projection)
- **GitLab Ultimate License:** $15,000
- **Stripe/DeepL/External API Fees:** $45,000
- **Security Tooling (Snyk, SonarQube):** $30,000
- **Hardware Keys (Yubikeys for internal testing):** $10,000
- **Misc. SaaS (Slack, Jira, etc.):** $100,000

### 11.3 Contingency ($230,000)
- **Emergency Buffer:** $230,000 (Reserved for timeline slips or critical architectural pivots).

---

## 12. APPENDICES

### Appendix A: Performance Success Metrics
To be considered a "success," the system must meet the following KPIs during the 90-day post-launch window:
1.  **p95 Response Time:** $\le 200\text{ms}$ for all `GET` requests at a load of 500 concurrent users.
2.  **Uptime:** $99.9\%$ (Allowing for only 43 minutes of downtime over 90 days).
3.  **Error Rate:** $< 0.1\%$ of all requests resulting in 5xx errors.

### Appendix B: SOC 2 Compliance Checklist
The following items must be verified by Nadira Costa before the July 15th audit:
- [ ] Encryption of all PII in the `users` table.
- [ ] MFA enforced for all administrative accounts.
- [ ] Quarterly access reviews for production environment.
- [ ] Documented Disaster Recovery (DR) plan with a tested RTO (Recovery Time Objective) of 4 hours.
- [ ] Evidence of "Least Privilege" access for the 4-person team.