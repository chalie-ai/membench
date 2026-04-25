# PROJECT SPECIFICATION DOCUMENT: SENTINEL LMS
**Version:** 1.0.4  
**Document Status:** Baseline  
**Date:** October 24, 2024  
**Project Lead:** Nadira Kim (CTO, Hearthstone Software)  
**Classification:** Confidential / Internal Use Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Sentinel" is a comprehensive modernization initiative undertaken by Hearthstone Software to transform its legacy monolithic Learning Management System (LMS) into a scalable, microservices-based architecture tailored specifically for the real estate industry. The real estate sector requires specialized compliance training, continuing education (CE) credits, and highly secure data handling for professional licensing. The existing monolithic system has reached its scaling limit, suffering from deployment bottlenecks and architectural rigidity that prevent the company from expanding its market share.

### 1.2 Business Justification
The transition from a monolith to microservices is not merely a technical upgrade but a strategic business necessity. In the current real estate education market, the ability to rapidly deploy new course content—often dictated by changing state laws—is a competitive advantage. The legacy system requires a full-site redeploy for a single change, leading to a 4-hour deployment window and significant downtime risk. Sentinel will implement a serverless-inspired architecture using FastAPI and API Gateways, allowing independent scaling of modules (e.g., the Search service can scale independently of the Billing service during peak enrollment periods).

Furthermore, the platform must handle PCI DSS Level 1 compliance as it processes credit card payments directly. Moving to a microservices architecture allows Hearthstone to isolate the "Cardholder Data Environment" (CDE) into a single, highly secure service, reducing the audit scope and operational risk for the rest of the application.

### 1.3 ROI Projection
With a total investment of $3,000,000, Hearthstone Software projects a return on investment (ROI) based on three primary drivers:
1.  **Operational Efficiency:** A reduction in deployment time from 4 hours to <10 minutes via Continuous Deployment (CD), saving approximately 200 engineering hours per month.
2.  **Market Expansion:** The ability to support 10,000 Monthly Active Users (MAU) within six months of launch, representing a 300% increase over the legacy system's capacity.
3.  **Churn Reduction:** By implementing advanced faceted search and a modern UI (designed by Orin Kim), the platform expects a 15% increase in course completion rates, directly correlating to higher subscription renewals.

The projected break-even point is 14 months post-launch, with an estimated annual recurring revenue (ARR) increase of $1.2M attributed to the platform's improved stability and feature set.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Overview
Sentinel utilizes a "Serverless-style" architecture hosted on self-managed infrastructure using Docker Compose. While not using a public cloud provider (like AWS Lambda), the logic is partitioned into discrete, stateless functional units coordinated by a central API Gateway.

**Stack Components:**
- **Language:** Python 3.11+
- **Framework:** FastAPI (chosen for asynchronous performance and automatic OpenAPI generation)
- **Database:** MongoDB (NoSQL chosen for flexible course content schemas)
- **Task Queue:** Celery with Redis as the broker (for asynchronous virus scanning and email notifications)
- **Containerization:** Docker Compose for orchestration across self-hosted bare-metal servers.
- **Deployment:** Continuous Deployment (CD) pipeline where every merged Pull Request (PR) triggers an automated build and deployment to production.

### 2.2 System Interaction Diagram (ASCII)

```text
[ Client / Browser ] 
       |
       v
[ API Gateway (Nginx/FastAPI) ] <--- Orchestration Layer
       |
       +-------+-----------------------+-----------------------+
       |        |                       |                       |
       v        v                       v                       v
 [ Auth Svc ] [ Search Svc ] [ Billing Svc ] [ File/CDN Svc ] [ Content Svc ]
       |        |                       |                       |
       |        +----------+------------+-----------+-----------+
       |                   |                            |
       v                   v                            v
 [ MongoDB Cluster ] <--> [ Redis Cache ] <--> [ Celery Workers ]
       |                                                 |
       +-------------------------------------------------+--> [ S3-Compatible Store ]
```

### 2.3 Orchestration Logic
The API Gateway serves as the single entry point. It handles request routing, rate limiting, and initial JWT validation. Each microservice (Auth, Search, Billing, etc.) communicates via internal REST endpoints. For heavy lifting—such as virus scanning files or generating large PDF certificates—the API Gateway triggers a Celery task, which is processed asynchronously to prevent blocking the main event loop.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
The Auth service is the foundation of Sentinel. Because this is a real estate LMS, roles are complex. We require a hierarchical RBAC system to distinguish between Students, Instructors, State Regulators, and System Administrators. 

**Functional Requirements:**
- **Identity Management:** Support for email/password registration with mandatory password complexity requirements.
- **JWT Implementation:** Issue short-lived Access Tokens (15 mins) and long-lived Refresh Tokens (7 days) stored in secure, httpOnly cookies.
- **Role Hierarchy:**
    - *Student:* Can enroll in courses, view their own progress, and download certificates.
    - *Instructor:* Can create course content, grade assignments, and view student analytics.
    - *Regulator:* Read-only access to compliance reports and student certification logs for state audits.
    - *Admin:* Full system control, including tenant management and billing overrides.
- **Multi-Tenant Context:** Every authentication request must be bound to a `tenant_id`. The Auth service must verify that the user belongs to the specific real estate agency or school tenant attempting to access the resource.

**Technical Constraints:**
- All passwords must be hashed using Argon2id.
- The service must integrate with the MongoDB `users` and `roles` collections, ensuring that role changes are propagated across the system in real-time via a Redis cache invalidation signal.

### 3.2 Multi-Tenant Data Isolation (Shared Infrastructure)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Sentinel uses a "Shared Schema" multi-tenancy model. To maintain high performance and lower costs, all tenants share the same MongoDB cluster, but data isolation is enforced at the application layer to prevent "cross-tenant leakage"—a catastrophic failure in a professional licensing environment.

**Functional Requirements:**
- **Logical Isolation:** Every document in every collection (except global config) must contain a `tenant_id` field.
- **Query Middleware:** The FastAPI layer must implement a global dependency that extracts the `tenant_id` from the authenticated JWT and automatically appends `{"tenant_id": current_tenant}` to every MongoDB query.
- **Tenant Onboarding:** An automated process to generate a unique Tenant ID and initialize default roles and settings upon agency registration.
- **Cross-Tenant Administration:** A specialized "Super-Admin" mode allowing Nadira Kim and the CTO office to perform maintenance across all tenants without violating PCI DSS boundaries.

**Technical Constraints:**
- Create a MongoDB compound index on `{tenant_id: 1, _id: 1}` across all primary collections to ensure query performance does not degrade as the number of tenants grows.
- Implement a "Sentinel Guard" interceptor that logs any attempt to access a resource where the `tenant_id` in the URL does not match the `tenant_id` in the JWT.

### 3.3 Advanced Search with Faceted Filtering
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
Real estate professionals must find specific courses (e.g., "Texas Fair Housing Law 2024") across thousands of offerings. This feature provides a Google-like search experience with the ability to filter by state, credit hours, price, and certification level.

**Functional Requirements:**
- **Full-Text Indexing:** Use MongoDB Atlas Search (Lucene) to provide fuzzy matching and stemming.
- **Faceted Navigation:** A sidebar allowing users to drill down by:
    - Course Category (e.g., Legal, Finance, Ethics).
    - Credit Hours (1, 3, 6, 12+).
    - Delivery Method (Live Webinar, On-Demand).
- **Ranking Algorithm:** Results are ranked based on relevance, course rating, and "featured" status set by the administrator.
- **Search Suggestions:** An autocomplete endpoint that suggests courses as the user types.

**Technical Details:**
- Implementation uses a custom FastAPI endpoint `/api/v1/search` that maps query parameters to a MongoDB `$search` aggregation pipeline.
- Performance is optimized via a Redis cache for the top 100 most common search queries, refreshing every 60 minutes.

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** High | **Status:** Blocked

**Description:**
Instructors upload large PDFs, videos, and slide decks. Because these files are distributed to thousands of students, we need a secure pipeline that prevents malware from entering the system and ensures fast global delivery.

**Functional Requirements:**
- **Secure Upload:** Files are uploaded to a temporary "Quarantine" bucket.
- **Asynchronous Scanning:** Upon upload, a Celery worker triggers a scan using ClamAV. If a virus is detected, the file is deleted, and the instructor is notified.
- **CDN Integration:** Once cleared, files are moved to a "Public" bucket and served via a CDN (Content Delivery Network) to reduce latency.
- **Access Control:** Signed URLs are used to ensure that only enrolled students can download premium course materials.

**Technical Constraints:**
- Maximum file size limit: 500MB per upload.
- Virus scanning must complete within 30 seconds for files under 50MB.
- Integration with a self-hosted MinIO instance for S3-compatible storage.

### 3.5 Automated Billing and Subscription Management
**Priority:** Low (Nice to have) | **Status:** Blocked

**Description:**
A system to automate the recurring billing of real estate agencies and individual students. This includes tiered pricing and automatic invoice generation.

**Functional Requirements:**
- **Subscription Tiers:** Basic, Professional, and Enterprise levels.
- **Direct Credit Card Processing:** Implementation of a secure checkout flow.
- **PCI DSS Compliance:** Strict adherence to Level 1 standards, including encryption of data in transit and at rest.
- **Invoicing:** Automatic generation of PDF invoices sent via email upon successful payment.

**Technical Debt Warning:**
The current billing module was deployed under extreme deadline pressure and contains **zero test coverage**. This is a critical risk and must be refactored with a full TDD (Test Driven Development) approach before moving out of "Blocked" status.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path: `https://api.sentinel.hearthstone.com/v1`

### 4.1 Auth Service
**POST `/auth/login`**
- **Description:** Authenticates user and returns tokens.
- **Request:** `{"email": "user@example.com", "password": "hashed_password"}`
- **Response:** `200 OK` | `{"access_token": "eyJ...", "refresh_token": "eyJ...", "user": {"id": "123", "role": "Student"}}`

**POST `/auth/refresh`**
- **Description:** Rotates the access token using a refresh token.
- **Request:** `{"refresh_token": "eyJ..."}`
- **Response:** `200 OK` | `{"access_token": "eyJ..."}`

### 4.2 Search Service
**GET `/search?q={query}&category={cat}&hours={h}`**
- **Description:** Performs faceted search on courses.
- **Request Example:** `/search?q=Texas+Law&category=Legal&hours=3`
- **Response:** `200 OK` | `{"results": [...], "facets": {"categories": {"Legal": 10, "Ethics": 5}}, "total": 15}`

### 4.3 Content Service
**GET `/courses/{course_id}`**
- **Description:** Retrieves detailed course information.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK` | `{"id": "crs_01", "title": "Real Estate 101", "content": "...", "tenant_id": "tenant_A"}`

**POST `/courses/{course_id}/enroll`**
- **Description:** Enrolls the authenticated user in a course.
- **Request:** `{"payment_method": "subscription"}`
- **Response:** `201 Created` | `{"enrollment_id": "enr_99", "status": "active"}`

### 4.4 File Service
**POST `/files/upload`**
- **Description:** Uploads a file for scanning and storage.
- **Request:** Multipart Form Data `{file: binary}`
- **Response:** `202 Accepted` | `{"file_id": "file_abc", "status": "scanning"}`

**GET `/files/download/{file_id}`**
- **Description:** Returns a signed CDN URL for a file.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK` | `{"url": "https://cdn.sentinel.com/signed-link-123"}`

### 4.5 Billing Service
**GET `/billing/invoice/{invoice_id}`**
- **Description:** Retrieves a billing invoice.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK` | `{"invoice_id": "inv_001", "amount": 299.00, "status": "paid"}`

---

## 5. DATABASE SCHEMA (MongoDB)

Since Sentinel uses MongoDB, "tables" are referred to as "collections." All collections employ a `tenant_id` for logical isolation.

### 5.1 Collections Mapping

| Collection | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `tenants` | `_id` | `tenant_name`, `domain`, `subscription_plan`, `created_at` | One-to-Many with `users` |
| `users` | `_id` | `email`, `password_hash`, `role_id`, `tenant_id`, `last_login` | Belongs to `tenants` |
| `roles` | `_id` | `role_name` (Admin, etc), `permissions_list` | Referenced by `users` |
| `courses` | `_id` | `title`, `description`, `tenant_id`, `credit_hours`, `tags` | One-to-Many with `lessons` |
| `lessons` | `_id` | `course_id`, `title`, `content_type` (video/pdf), `order` | Belongs to `courses` |
| `enrollments` | `_id` | `user_id`, `course_id`, `tenant_id`, `completion_status`, `date_enrolled` | Links `users` and `courses` |
| `files` | `_id` | `filename`, `cdn_url`, `status` (scanned/unscanned), `uploader_id` | Belongs to `users` |
| `payments` | `_id` | `user_id`, `tenant_id`, `amount`, `transaction_id`, `status` | Belongs to `users` |
| `invoices` | `_id` | `payment_id`, `billing_date`, `pdf_link`, `amount_due` | Belongs to `payments` |
| `audit_logs` | `_id` | `timestamp`, `user_id`, `action`, `ip_address`, `tenant_id` | Cross-references all actions |

### 5.2 Relationships & Constraints
- **Hard Constraint:** No document may be written to a collection without a `tenant_id` except for the `tenants` collection itself.
- **Indexing:** A compound index on `(tenant_id, user_id)` is required for the `enrollments` and `payments` collections to ensure fast retrieval of user history within a specific agency's context.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes three distinct environments to ensure stability. All environments are deployed via Docker Compose on self-hosted hardware.

**1. Development (Dev):**
- **Purpose:** Individual feature development.
- **Database:** Local MongoDB instance.
- **Deployment:** Manual trigger by developers.
- **CI/CD:** Every commit to a feature branch triggers a build and a set of unit tests.

**2. Staging (Stage):**
- **Purpose:** Integration testing and UAT (User Acceptance Testing).
- **Database:** A mirrored copy of production data (anonymized).
- **Deployment:** Automatic on merge to the `develop` branch.
- **Mirroring:** Staging exactly matches Production's hardware specs to catch performance regressions.

**3. Production (Prod):**
- **Purpose:** Live user traffic.
- **Database:** High-availability MongoDB Replica Set.
- **Deployment:** **Continuous Deployment (CD)**. Every merged PR from `develop` to `main` is deployed immediately to production.
- **Security:** PCI DSS Level 1 hardened OS, encrypted disks, and restricted SSH access.

### 6.2 Infrastructure Details
- **Orchestration:** Docker Compose is used to manage the `api-gateway`, `auth-svc`, `search-svc`, `billing-svc`, `file-svc`, and `celery-worker` containers.
- **Load Balancing:** Nginx acts as the primary ingress controller, handling SSL termination and distributing traffic to the FastAPI containers.
- **Storage:** A dedicated NVMe storage array is used for MongoDB to minimize I/O wait times during heavy search indexing.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions and API endpoints in isolation.
- **Tooling:** `pytest` with `httpx` for asynchronous requests.
- **Requirement:** 80% code coverage for all new services.
- **Mocking:** External dependencies (like the CDN or Payment Gateway) are mocked using `unittest.mock`.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between microservices (e.g., Auth $\rightarrow$ Content).
- **Approach:** A dedicated integration suite runs in the Staging environment. It spins up the entire Docker Compose stack and executes "Golden Path" scenarios (e.g., User registers $\rightarrow$ Enrolls in Course $\rightarrow$ Completes Course).
- **Data Isolation Test:** A specific test suite designed to attempt "Tenant Leaking" by trying to access `tenant_B` data using a `tenant_A` token.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from the browser perspective.
- **Tooling:** Playwright.
- **Critical Paths:**
    1. Student Login $\rightarrow$ Search Course $\rightarrow$ Payment $\rightarrow$ Course Access.
    2. Instructor Login $\rightarrow$ Upload File $\rightarrow$ Verify Virus Scan $\rightarrow$ Publish Lesson.
    3. Admin Login $\rightarrow$ Generate Compliance Report $\rightarrow$ Export PDF.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Scope creep from stakeholders adding 'small' features | High | Medium | Accept the risk; monitor weekly in lead meetings. |
| R2 | Regulatory requirements for RE education change | Medium | High | Raise in next board meeting as a blocker. |
| R3 | Data leakage between tenants (Multi-tenancy failure) | Low | Critical | Implement mandatory query middleware and automated isolation tests. |
| R4 | PCI DSS Audit failure due to billing technical debt | Medium | High | Immediate refactor of billing module with TDD before launch. |
| R5 | CDN Latency for large video files | Low | Medium | Use a multi-region cache and edge-node distribution. |

**Probability/Impact Matrix:**
- **Critical:** Immediate action required; potential project failure.
- **High:** Significant impact; requires active management.
- **Medium:** Managed via standard project governance.
- **Low:** Monitor and address if probability increases.

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Foundation (Months 1-6):** Migration of the monolith core to microservices, setup of API Gateway, and implementation of Advanced Search.
- **Phase 2: Security & Isolation (Months 7-12):** Implementation of RBAC and Multi-tenant isolation. Security hardening for PCI DSS.
- **Phase 3: Optimization & Polish (Months 13-18):** File upload pipeline, billing automation, and performance tuning.

### 9.2 Key Milestones

| Milestone | Target Date | Dependency | Success Criteria |
| :--- | :--- | :--- | :--- |
| **M1: Performance Benchmarks** | 2025-05-15 | Search Svc Complete | Support 500 concurrent requests/sec with <200ms latency. |
| **M2: Architecture Review** | 2025-07-15 | M1 | CTO approval of microservice boundaries and data flow. |
| **M3: Security Audit** | 2025-09-15 | RBAC/Isolation Complete | Pass external PCI DSS Level 1 and SOC2 Type II audit. |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2024-11-02  
**Attendees:** Nadira Kim, Ira Nakamura, Orin Kim, Noor Nakamura  
**Discussion:**
- The team discussed whether to use a shared database or separate databases per tenant.
- Ira argued that separate databases would be too expensive to manage at 10k users.
- Orin expressed concern that a shared schema might lead to "noisy neighbor" performance issues.
- **Decision:** Agreed on a shared schema with mandatory `tenant_id` indexing.
- **Action Items:**
    - Ira: Define the MongoDB index strategy for tenants. [Owner: Ira]
    - Nadira: Review the API Gateway timeout settings. [Owner: Nadira]

### Meeting 2: The Billing Debt Crisis
**Date:** 2024-12-15  
**Attendees:** Nadira Kim, Noor Nakamura  
**Discussion:**
- Noor reported that the core billing module has no test coverage and is producing intermittent 500 errors in staging.
- Nadira acknowledged that it was pushed to meet a previous deadline but agreed it is now a critical risk.
- **Decision:** The billing feature is officially moved to "Blocked" status. No new features will be added to billing until 100% test coverage is achieved.
- **Action Items:**
    - Noor: Create a backlog of all known bugs in the billing module. [Owner: Noor]
    - Nadira: Inform stakeholders that billing automation is delayed. [Owner: Nadira]

### Meeting 3: Legal Blocker Review
**Date:** 2025-01-10  
**Attendees:** Nadira Kim, Orin Kim  
**Discussion:**
- The team is currently unable to finalize the File Upload service because the Data Processing Agreement (DPA) is still with the legal team.
- Without the DPA, the team cannot legally store user-uploaded content on the new infrastructure.
- **Decision:** This is now the primary project blocker.
- **Action Items:**
    - Nadira: Email the legal department and request an expedited review. [Owner: Nadira]
    - Orin: Continue working on UI mockups for the upload dashboard. [Owner: Orin]

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | 12-person team over 18 months (including benefits/taxes). |
| **Infrastructure** | 15% | $450,000 | Bare-metal servers, NVMe arrays, CDN costs, and backup storage. |
| **Software & Tools** | 10% | $300,000 | MongoDB Atlas Enterprise, ClamAV Premium, Playwright licenses. |
| **Compliance/Audit** | 5% | $150,000 | External PCI DSS Level 1 certification and security penetration testing. |
| **Contingency** | 5% | $150,000 | Reserve for scope creep and emergency hardware replacement. |

---

## 12. APPENDICES

### Appendix A: PCI DSS Compliance Checklist
Because Sentinel processes credit cards directly, the following controls are mandatory:
1. **Encryption:** All card data must be encrypted using AES-256 at rest.
2. **Network Isolation:** The Billing Service must reside in a separate VLAN from the Search and Content services.
3. **Access Logs:** Every access to the `payments` collection must be logged with the user's ID and timestamp in the `audit_logs` collection.
4. **Rotation:** All API keys for payment gateways must be rotated every 90 days.

### Appendix B: Data Migration Plan (Monolith to Microservices)
The migration will follow a "Strangler Fig" pattern:
1. **Proxy Layer:** The API Gateway is placed in front of the legacy monolith.
2. **Feature Extraction:** The Search functionality is extracted first (already complete). Requests for `/search` are routed to the new `search-svc`, while all other requests go to the monolith.
3. **Iterative Migration:** Auth, then Isolation, then File Uploads will be extracted in sequence.
4. **Decommission:** Once the Billing service is stable and tested, the monolith is shut down entirely.