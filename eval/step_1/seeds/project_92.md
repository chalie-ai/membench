Due to the constraints of this platform's output length per message, I have provided the full, comprehensive Project Specification for **Project Helix**. To meet the strict word count and detail requirements, this document is structured as a professional technical manual.

***

# PROJECT SPECIFICATION: HELIX LMS
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Project Code:** HELIX-AGRI-2024  
**Owner:** Cassius Stein, VP of Product  
**Company:** Oakmount Group  
**Date:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Helix represents a mission-critical strategic pivot for the Oakmount Group. Following the launch of the legacy agricultural learning management system (LMS), the company received catastrophic user feedback citing systemic instability, an archaic user interface, and a failure to meet the specific pedagogical needs of agriculture technology specialists. Project Helix is not a mere update, but a complete ground-up rebuild of the customer-facing product.

The goal of Helix is to position Oakmount Group as the primary educational infrastructure provider for the AgTech industry. By integrating advanced workflow automation, high-performance search, and HIPAA-compliant data handling, Helix will enable large-scale agricultural enterprises to certify their workforce and manage complex regulatory training requirements across global jurisdictions.

### 1.2 Business Justification
The AgTech sector is currently experiencing a regulatory surge. New mandates regarding pesticide application, GMO handling, and sustainable soil management require documented, verifiable training. The legacy system's failure to provide reliable audit trails and a seamless user experience led to a 22% churn rate in Q3 of the previous year. 

Helix addresses these failures by implementing a Hexagonal Architecture, ensuring that the business logic is decoupled from external dependencies. This allows the platform to remain agile as regulatory requirements change. By moving to a modern TypeScript/Next.js stack, the platform will reduce page load times by an estimated 60% and increase user retention through a modernized UX.

### 1.3 ROI Projection and Financial Impact
With a total investment of $3,000,000, the Oakmount Group expects a full recovery of capital within 18 months post-launch.

*   **Customer Acquisition:** By providing a "Best-in-Class" UX, we project a 40% increase in new contract wins within the first year.
*   **Churn Reduction:** The transition from the legacy system to Helix is expected to reduce churn from 22% to under 5%.
*   **Operational Efficiency:** The implementation of the Workflow Automation Engine will reduce the manual onboarding time for new corporate clients from 14 days to 2 days.
*   **Projected Annual Recurring Revenue (ARR) Increase:** Estimated at $4.5M in Year 1 post-launch, driven by a new tiered pricing model based on the number of active certifications managed.

### 1.4 Success Metrics
The project's success will be measured by two primary Key Performance Indicators (KPIs):
1.  **Security Integrity:** Zero critical security incidents (CVEs with CVSS > 7.0) in the first 12 months of production.
2.  **Feature Adoption:** An 80% adoption rate of the "Workflow Automation" and "Advanced Search" tools among the initial 10 pilot users.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Helix utilizes a Hexagonal Architecture to ensure that the core business domain is isolated from the infrastructure. This prevents "vendor lock-in" and allows for easier testing.

*   **The Core (Domain):** Contains business entities, domain services, and business rules. It has no knowledge of the database or the web framework.
*   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `ICourseRepository`, `IEmailService`).
*   **Adapters:** Concrete implementations of the ports. For example, the `PrismaCourseRepository` is an adapter that connects the core to the PostgreSQL database.

### 2.2 ASCII Architecture Diagram
```text
[ EXTERNAL CLIENTS ] <--- HTTP/HTTPS ---> [ ADAPTERS (Next.js API Routes) ]
                                                        |
                                                        v
                                           [ PORTS (Interface Definitions) ]
                                                        |
                                                        v
      -----------------------------------------------------------------------------------
      |                                   DOMAIN CORE                                    |
      |  [ Domain Entities ] <---> [ Use Case Interactors ] <---> [ Domain Services ]   |
      -----------------------------------------------------------------------------------
                                                        |
                                                        v
                                           [ PORTS (Infrastructure Interfaces) ]
                                                        |
                                                        v
[ EXTERNAL SERVICES ] <--- Adapters ---> [ ADAPTERS (Prisma / Vercel / S3 / Auth0) ]
       |                                                 |
  (Virus Scanner)                                  (PostgreSQL DB)
```

### 2.3 Technology Stack
*   **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS.
*   **Backend:** Next.js Server Actions and API Routes.
*   **ORM:** Prisma (Type-safe database access).
*   **Database:** PostgreSQL (Hosted on Vercel Postgres/Neon).
*   **Deployment:** Vercel (CI/CD pipeline integrated with GitHub).
*   **Storage:** AWS S3 with CloudFront CDN for asset distribution.
*   **Security:** AES-256 encryption for data at rest; TLS 1.3 for data in transit.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Critical - Launch Blocker)
**Status:** Complete | **Priority:** Critical

**Description:**
The advanced search is the primary gateway for users to find educational content across thousands of agricultural modules. It must support full-text indexing to ensure that queries for complex chemical compounds or regional farming regulations return accurate results instantaneously.

**Technical Specifications:**
*   **Indexing:** Implementation of PostgreSQL Full-Text Search (FTS) using `tsvector` and `tsquery`.
*   **Faceted Filtering:** Users can filter results by:
    *   Certification Level (Basic, Intermediate, Expert).
    *   Crop Category (Grains, Legumes, Fruits, etc.).
    *   Regulatory Body (USDA, EU Agri, etc.).
    *   Date of Publication.
*   **Search Logic:** The search employs a "weighted" ranking system. Matches in the "Course Title" carry a weight of 1.0, "Course Description" 0.6, and "Tags" 0.4.

**User Workflow:**
1. User enters a query (e.g., "Nitrogen runoff prevention").
2. The system triggers a debounced API call to the search endpoint.
3. Results are returned with highlighted keywords.
4. User selects "Region: Midwest" from the facet sidebar; the result set updates dynamically without a full page reload.

### 3.2 Workflow Automation Engine with Visual Rule Builder (High)
**Status:** In Progress | **Priority:** High

**Description:**
This feature allows administrators to automate the learner's journey. For example, "If a user fails the 'Soil Safety' quiz twice, automatically assign the 'Remedial Geology' module and notify their supervisor."

**Technical Specifications:**
*   **Rule Engine:** A JSON-based logic tree that evaluates triggers and actions.
*   **Visual Builder:** A drag-and-drop interface using `React Flow` to allow non-technical admins to map out workflows.
*   **Triggers:** Event-driven triggers (e.g., `COURSE_COMPLETED`, `QUIZ_FAILED`, `LOGIN_INACTIVITY_30_DAYS`).
*   **Actions:** Automated responses (e.g., `ASSIGN_COURSE`, `SEND_EMAIL_NOTIFICATION`, `UPDATE_USER_STATUS`).

**Implementation Detail:**
The engine operates on an asynchronous queue. When an event occurs, it is pushed to a queue; the Workflow Service then evaluates all active rules against that event and executes the corresponding adapters.

### 3.3 Localization and Internationalization (L10n/i18n) (High)
**Status:** In Progress | **Priority:** High

**Description:**
Helix must support 12 primary languages to serve global agricultural markets (including English, Spanish, Mandarin, Portuguese, French, German, Hindi, Arabic, Japanese, Korean, Russian, and Vietnamese).

**Technical Specifications:**
*   **Framework:** `next-intl` for routing and translation management.
*   **Storage:** Translations are stored in JSON files for static content and in the PostgreSQL `translations` table for dynamic course content.
*   **Dynamic Detection:** The system detects the user's locale via the `Accept-Language` header and user profile settings.
*   **Right-to-Left (RTL) Support:** CSS logic to flip the layout for Arabic and Hebrew.

**Scope:**
All system messages, navigation elements, and course metadata must be translated. Content generated by users (e.g., forum posts) will be passed through a Google Cloud Translation API integration for "on-the-fly" translation.

### 3.4 File Upload with Virus Scanning and CDN Distribution (Medium)
**Status:** In Review | **Priority:** Medium

**Description:**
Educators need to upload large PDF manuals, video lectures, and datasets. Given the HIPAA compliance requirements, these files must be scanned for malware and served securely.

**Technical Specifications:**
*   **Upload Pipeline:** Client $\rightarrow$ Next.js API $\rightarrow$ ClamAV (Virus Scanner) $\rightarrow$ AWS S3.
*   **Virus Scanning:** All uploads are piped through a ClamAV container. Files flagged as malicious are immediately deleted, and an alert is sent to the Security Officer.
*   **Distribution:** Files are served via CloudFront CDN with "Signed URLs" to ensure that only authenticated users can access specific documents.
*   **Compression:** Automatic image optimization via `next/image` and video transcoding via AWS Elemental MediaConvert.

**Performance Goal:**
Uploads up to 500MB must be supported with a resumable upload mechanism (S3 Multipart Upload).

### 3.5 Audit Trail Logging with Tamper-Evident Storage (Medium)
**Status:** Blocked | **Priority:** Medium

**Description:**
For regulatory compliance, every action taken within the LMS (grade changes, course completions, user access) must be logged in a way that cannot be altered by administrators.

**Technical Specifications:**
*   **Logging Mechanism:** An interceptor in the Application Layer that captures all state-changing requests.
*   **Tamper-Evidence:** Each log entry contains a SHA-256 hash of the previous entry, creating a cryptographic chain.
*   **Storage:** Logs are written to a "Write Once, Read Many" (WORM) storage bucket in AWS.
*   **Audit View:** A read-only dashboard for compliance officers to export logs as signed PDFs.

**Current Blocker:**
The team is currently debating the storage implementation—whether to use a dedicated Ledger Database (like Amazon QLDB) or a custom hashing implementation in PostgreSQL.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the header.

### 4.1 `GET /search`
**Description:** Performs a faceted search across courses.
*   **Query Parameters:** `q` (string), `category` (string), `level` (string), `page` (int).
*   **Example Request:** `GET /api/v1/search?q=irrigation&category=water_mgmt`
*   **Example Response:**
    ```json
    {
      "results": [
        { "id": "crs_123", "title": "Modern Irrigation Techniques", "score": 0.98 }
      ],
      "facets": {
        "levels": { "Beginner": 10, "Advanced": 2 }
      },
      "total": 12
    }
    ```

### 4.2 `POST /workflows/rule`
**Description:** Creates a new automation rule.
*   **Example Request:**
    ```json
    {
      "name": "Failure Alert",
      "trigger": "QUIZ_FAILED",
      "conditions": { "attempt_count": { "gt": 2 } },
      "action": "SEND_EMAIL",
      "action_params": { "template": "failure_notice" }
    }
    ```
*   **Example Response:** `201 Created` { "ruleId": "rule_998" }

### 4.3 `POST /uploads/sign-url`
**Description:** Generates a signed S3 URL for secure client-side upload.
*   **Example Request:** `{ "filename": "manual.pdf", "contentType": "application/pdf" }`
*   **Example Response:** `{ "url": "https://s3.amazon...?", "fields": { ... } }`

### 4.4 `GET /audit/logs`
**Description:** Retrieves tamper-evident logs for a specific user.
*   **Example Request:** `GET /api/v1/audit/logs?userId=usr_456`
*   **Example Response:**
    ```json
    [
      { "timestamp": "2024-01-01T10:00Z", "action": "GRADE_CHANGE", "prevHash": "0xabc...123", "hash": "0xdef...456" }
    ]
    ```

### 4.5 `PATCH /courses/localization`
**Description:** Updates the translation for a specific course field.
*   **Example Request:** `{ "courseId": "crs_1", "lang": "es", "field": "title", "value": "Técnicas de Riego" }`
*   **Example Response:** `200 OK`

### 4.6 `GET /users/profile`
**Description:** Fetches the authenticated user's profile and settings.
*   **Example Response:** `{ "userId": "usr_1", "name": "John Doe", "preferredLang": "en-US" }`

### 4.7 `POST /courses/enroll`
**Description:** Enrolls a user in a course.
*   **Example Request:** `{ "userId": "usr_1", "courseId": "crs_10" }`
*   **Example Response:** `200 OK` { "status": "enrolled" }

### 4.8 `DELETE /workflows/rule/:id`
**Description:** Deletes an automation rule.
*   **Example Request:** `DELETE /api/v1/workflows/rule/rule_998`
*   **Example Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system uses a relational PostgreSQL schema. All primary keys are UUIDs to prevent ID enumeration attacks.

### 5.1 Table Definitions

1.  **`Users`**: Stores core identity.
    *   `id` (UUID, PK), `email` (Unique), `password_hash`, `role` (Admin, Instructor, Learner), `created_at`, `updated_at`.
2.  **`Courses`**: Main educational modules.
    *   `id` (UUID, PK), `creator_id` (FK $\rightarrow$ Users), `slug` (Unique), `is_published` (Boolean), `version` (Int).
3.  **`Course_Translations`**: Localization data.
    *   `id` (UUID, PK), `course_id` (FK $\rightarrow$ Courses), `language_code` (String), `translated_title` (String), `translated_desc` (Text).
4.  **`Enrollments`**: Maps users to courses.
    *   `id` (UUID, PK), `user_id` (FK $\rightarrow$ Users), `course_id` (FK $\rightarrow$ Courses), `status` (Active, Completed, Dropped), `completion_date` (Timestamp).
5.  **`Modules`**: Sub-sections within a course.
    *   `id` (UUID, PK), `course_id` (FK $\rightarrow$ Courses), `order_index` (Int), `content_type` (Video, Quiz, Text).
6.  **`Quizzes`**: Assessment definitions.
    *   `id` (UUID, PK), `module_id` (FK $\rightarrow$ Modules), `passing_score` (Int), `retry_limit` (Int).
7.  **`Quiz_Attempts`**: User performance tracking.
    *   `id` (UUID, PK), `user_id` (FK $\rightarrow$ Users), `quiz_id` (FK $\rightarrow$ Quizzes), `score` (Int), `attempted_at` (Timestamp).
8.  **`Workflow_Rules`**: Automation logic.
    *   `id` (UUID, PK), `name` (String), `trigger_event` (String), `logic_json` (JSONB), `is_active` (Boolean).
9.  **`Audit_Logs`**: Tamper-evident record.
    *   `id` (UUID, PK), `user_id` (FK $\rightarrow$ Users), `action` (String), `payload` (JSONB), `hash` (String), `previous_hash` (String), `created_at` (Timestamp).
10. **`Assets`**: CDN-tracked files.
    *   `id` (UUID, PK), `s3_key` (String), `mime_type` (String), `size_bytes` (BigInt), `virus_scan_status` (Clean, Infected, Pending).

### 5.2 Key Relationships
*   `Users` $\rightarrow$ `Enrollments` (One-to-Many)
*   `Courses` $\rightarrow$ `Course_Translations` (One-to-Many)
*   `Courses` $\rightarrow$ `Modules` (One-to-Many)
*   `Modules` $\rightarrow$ `Quizzes` (One-to-One)
*   `Quizzes` $\rightarrow$ `Quiz_Attempts` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Helix employs a three-tier environment strategy to ensure stability and regulatory compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature development and unit testing.
*   **Deploy:** Triggered on every push to the `develop` branch.
*   **Database:** Isolated Dev PostgreSQL instance.
*   **Access:** Internal team only.

#### 6.1.2 Staging (Staging)
*   **Purpose:** User Acceptance Testing (UAT) and Quality Assurance (QA).
*   **Deploy:** Triggered on merge to `release` branch.
*   **Database:** Sanitized copy of production data.
*   **Access:** Internal team + selected Pilot Users.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer-facing application.
*   **Deploy:** Quarterly releases following a formal Regulatory Review Cycle.
*   **Database:** High-availability PostgreSQL cluster with automated backups every 6 hours.
*   **Access:** Public (Authenticated).

### 6.2 Infrastructure Details
*   **Hosting:** Vercel (Edge Functions for low-latency global access).
*   **CDN:** CloudFront for static assets and video streaming.
*   **Encryption:** 
    *   **At Rest:** AWS KMS (Key Management Service) manages the encryption keys for the S3 buckets and PostgreSQL disks.
    *   **In Transit:** Forced HTTPS with HSTS (HTTP Strict Transport Security).
*   **HIPAA Compliance:** All PII (Personally Identifiable Information) is encrypted using application-level encryption before being stored in the database.

---

## 7. TESTING STRATEGY

To maintain the stability of the $3M investment, a rigorous testing pyramid is implemented.

### 7.1 Unit Testing
*   **Tool:** Vitest.
*   **Scope:** Domain logic, utility functions, and individual adapters.
*   **Requirement:** Minimum 80% code coverage for the `domain` folder.
*   **Example:** Testing that the `CourseCompletionService` correctly calculates if a user has passed all required modules.

### 7.2 Integration Testing
*   **Tool:** Jest + Prisma Mock.
*   **Scope:** Testing the interaction between the Application Layer and the Database/External APIs.
*   **Focus:** Ensuring the `WorkflowEngine` correctly triggers an email via the `EmailAdapter` when a quiz failure is recorded.

### 7.3 End-to-End (E2E) Testing
*   **Tool:** Playwright.
*   **Scope:** Critical user journeys (e.g., "User logs in $\rightarrow$ Searches for Course $\rightarrow$ Enrolls $\rightarrow$ Completes Quiz").
*   **Execution:** Run against the Staging environment prior to every quarterly release.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Integration partner API is undocumented/buggy | High | High | Negotiate timeline extensions; implement a "Buffer Adapter" to sanitize partner data. |
| R-02 | Primary vendor EOL (End-of-Life) announced | Medium | Critical | De-scope affected features if replacement not found by Milestone 2. |
| R-03 | Design disagreement (Product vs. Eng) | High | Medium | Weekly alignment meetings with Cassius Stein as final arbiter. |
| R-04 | HIPAA Compliance failure during audit | Low | Critical | Third-party security audit 30 days before Milestone 1. |
| R-05 | Localization delays for 12 languages | Medium | Medium | Use a mix of professional translation and AI-assisted translation for non-critical paths. |

**Probability/Impact Matrix:**
*   **High/Critical:** Immediate attention required.
*   **Medium/High:** Monitor weekly.
*   **Low/Medium:** Log and review monthly.

---

## 9. TIMELINE AND PHASES

### 9.1 Gantt-Style Phase Description

**Phase 1: Core Foundation (Now $\rightarrow$ Jan 2025)**
*   *Dependencies:* Architecture Review.
*   *Activities:* Database schema finalization, implementation of Advanced Search, setup of Hexagonal structure.

**Phase 2: Automation & Localization (Jan 2025 $\rightarrow$ March 2025)**
*   *Dependencies:* Phase 1 completion.
*   *Activities:* Build Visual Rule Builder, implement L10n for the first 6 languages.
*   **Milestone 1 (2025-03-15): First paying customer onboarded.**

**Phase 3: Beta Testing & Security Hardening (March 2025 $\rightarrow$ May 2025)**
*   *Dependencies:* Phase 2 completion.
*   *Activities:* External beta deployment, virus scanning implementation, HIPAA audit.
*   **Milestone 2 (2025-05-15): External beta with 10 pilot users.**

**Phase 4: Final Polish & Regulatory Review (May 2025 $\rightarrow$ July 2025)**
*   *Dependencies:* Beta feedback integration.
*   *Activities:* Final 6 languages localization, audit trail completion, performance tuning.
*   **Milestone 3 (2025-07-15): Architecture review complete.**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02 | **Attendees:** Cassius, Leandro, Hessa
*   Hexagonal architecture agreed.
*   Leandro concerned about Prisma overhead $\rightarrow$ decided to use raw SQL for complex search queries.
*   Hessa wants "dark mode" $\rightarrow$ Cassius says "out of scope for MVP."
*   JIRA tickets for Search functionality created.

### Meeting 2: Integration Crisis
**Date:** 2023-12-15 | **Attendees:** Cassius, Paloma, Leandro
*   Partner API returning 500s on basic requests.
*   Docs are 2 years old.
*   Paloma reports support tickets increasing for legacy system.
*   Decision: Request extension on Partner API delivery date.
*   Leandro to build a mock server to prevent blocking the frontend.

### Meeting 3: Design Blockage
**Date:** 2024-01-20 | **Attendees:** Cassius, Hessa, Engineering Lead
*   Disagreement on Workflow Builder UI.
*   Eng wants a list-based rule set (easier to build).
*   Product wants visual nodes (better for user).
*   Cassius rules: Visual nodes are required for the "wow" factor in sales.
*   Eng to research `React Flow`.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $1,800,000 | 20+ staff across Product, Eng, and UX (Annual salaries + benefits). |
| **Infrastructure** | $450,000 | Vercel Enterprise, AWS (S3, CloudFront, KMS), PostgreSQL Managed Instance. |
| **Tools & Licenses** | $200,000 | JIRA, GitHub Enterprise, ClamAV Enterprise, Translation API services. |
| **Security/Compliance** | $250,000 | Third-party HIPAA audit, Penetration Testing, SSL/TLS certificates. |
| **Contingency** | $300,000 | 10% reserve for vendor EOL replacements or scope creep. |

---

## 12. APPENDICES

### Appendix A: Virus Scanning Workflow
To ensure the system remains HIPAA compliant and secure, the following pipeline is executed for every file upload:
1.  **Ingestion:** File is uploaded to a "Quarantine" S3 Bucket.
2.  **Trigger:** S3 Event Notification triggers an AWS Lambda function.
3.  **Scan:** Lambda sends the file stream to a ClamAV instance.
4.  **Verdict:** 
    *   If `Clean`: File is moved to "Production" S3 Bucket and marked `Clean` in the `Assets` table.
    *   If `Infected`: File is deleted; record is marked `Infected`; an email is sent to the security team.

### Appendix B: Localization Implementation Detail
The translation system follows the "Key-Value" pair approach.
*   **Static Content:** Managed via `.json` files in the `/locales` directory (e.g., `en.json`, `es.json`).
*   **Dynamic Content:** The `Course_Translations` table allows for updates to course names without updating the core course record.
*   **Fallback Logic:** If a translation is missing for `fr-CA` (French Canadian), the system falls back to `fr` (French), and finally to `en` (English).