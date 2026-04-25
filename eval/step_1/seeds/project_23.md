Due to the extreme length requirements of this request, the following is a comprehensive, formal Project Specification Document for **Project Rampart**. This document is designed to serve as the "Single Source of Truth" (SSoT) for the development team, adhering to all constraints, budgets, and technical mandates.

***

# PROJECT SPECIFICATION: PROJECT RAMPART
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Classification:** Confidential – Ridgeline Platforms Internal  
**Owner:** Ilya Stein (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Rampart is the strategic initiative to modernize the core educational infrastructure of Ridgeline Platforms. The company currently relies on a 15-year-old legacy system (referred to as "The Monolith") which serves as the operational backbone for all student data, curriculum delivery, and administrative processing. The legacy system has reached a state of technical insolvency; maintenance costs are escalating, and the fragility of the codebase prevents the introduction of new features.

The business justification for Rampart is centered on **Operational Continuity**. Because the entire company depends on this system, the project carries a "Zero Downtime Tolerance" mandate. Any failure during the transition would result in total business paralysis. The goal is to replace the legacy system with a modern, mobile-first application that scales linearly and reduces the overhead of manual data entry and processing.

### 1.2 ROI Projection and Success Metrics
The financial viability of Rampart is predicated on a lean budget of $150,000. Given the "shoestring" nature of the funding, the ROI is calculated primarily through operational efficiency rather than direct revenue generation.

**Key Performance Indicators (KPIs):**
*   **Metric 1: Transaction Cost Reduction.** The target is a 35% reduction in the cost per transaction. This will be achieved by moving from expensive legacy mainframe licensing to a containerized, cloud-native architecture and optimizing the data pipeline.
*   **Metric 2: Manual Processing Efficiency.** The project aims for a 50% reduction in manual processing time for end users. By automating workflow triggers and implementing real-time collaborative tools, administrative staff will spend less time on "data cleaning" and more time on educational delivery.

**Financial Projection:**
Over a 36-month horizon, the reduction in operational overhead is projected to save the company approximately $420,000 in labor and licensing costs, representing a ~280% ROI on the initial $150,000 investment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy: Hexagonal (Ports and Adapters)
To mitigate the risk of inheriting three disparate legacy stacks, Rampart utilizes a **Hexagonal Architecture**. This decouples the core business logic (the "Domain") from the external technologies (the "Infrastructure").

*   **The Core (Domain):** Contains the business entities and use cases. It has no knowledge of databases, APIs, or UI frameworks.
*   **Ports:** Interfaces that define how the core communicates with the outside world (e.g., `UserRepository` interface).
*   **Adapters:** Concrete implementations of ports (e.g., `PostgresUserRepository` or `LegacySoapAdapter`).

This allows the solo developer to swap out legacy integration points without rewriting business logic.

### 2.2 Stack Integration
The application must interoperate across three inherited stacks:
1.  **Legacy Stack A (Java/Spring 2.x):** Handles authentication and legacy user roles.
2.  **Legacy Stack B (Python/Django 1.11):** Manages the legacy content repository.
3.  **Legacy Stack C (PHP/Custom):** Handles the ancient reporting engine.

### 2.3 ASCII Architecture Diagram
```text
[ External Clients ] <---> [ API Gateway / Load Balancer ]
                                      |
                                      v
                        +----------------------------+
                        |      PRIMARY ADAPTERS       |
                        | (REST Controllers, GraphQL) |
                        +-------------+--------------+
                                      |
                                      v
                        +----------------------------+
                        |      APPLICATION CORE      |
                        |  (Use Cases & Domain Logic) |
                        +-------------+--------------+
                                      |
                                      v
                        +----------------------------+
                        |      INFRASTRUCTURE PORTS |
                        | (Repositories, MessageBus)  |
                        +-------------+--------------+
                                      |
             +------------------------+------------------------+
             |                        |                        |
      [ Adapter: Postgres ]    [ Adapter: Legacy API ]    [ Adapter: S3/CDN ]
      (Modern Data Store)       (Stack A/B/C Bridge)      (File Distribution)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox
*   **Priority:** High | **Status:** In Review
*   **Description:** A robust RESTful API that allows external partners and institutional clients to programmatically access their data.
*   **Detailed Specs:**
    *   **Versioning:** The API must use URI versioning (e.g., `/v1/`, `/v2/`). Versioning is critical because legacy clients cannot be forced to upgrade simultaneously.
    *   **Sandbox Environment:** A mirrored "Staging" environment where users can test API calls without affecting production data. This requires a separate database instance with a "Seed" script to populate mock educational data.
    *   **Authentication:** Implementation of OAuth2 with JWT (JSON Web Tokens). Tokens must expire every 60 minutes with a refresh token mechanism.
    *   **Rate Limiting:** To protect the shoestring infrastructure, a rate limit of 1,000 requests per hour per API key will be enforced via Redis.
    *   **Documentation:** OpenAPI 3.0 (Swagger) specification must be automatically generated and hosted at `/docs`.
*   **Acceptance Criteria:** A developer can register an API key, successfully make a GET request to the sandbox, and receive a 429 error when exceeding the rate limit.

### 3.2 Real-time Collaborative Editing with Conflict Resolution
*   **Priority:** High | **Status:** Complete
*   **Description:** Allows multiple educators to edit course materials simultaneously without overwriting each other's changes.
*   **Detailed Specs:**
    *   **Conflict Resolution:** Implementation of **Operational Transformation (OT)**. Each keystroke is sent as an "operation" (Insert, Delete, Retain) rather than the full document state.
    *   **WebSockets:** The system uses Socket.io for full-duplex communication. The server acts as the central authority for sequencing operations.
    *   **Cursor Tracking:** Real-time broadcasting of user cursor positions $(x, y)$ within the document coordinates.
    *   **State Persistence:** Changes are cached in Redis and flushed to the primary database every 5 seconds to minimize DB writes.
    *   **Concurrency Control:** When two users edit the same character, the "Server Timestamp" determines the winner, with the loser's change shifted by the length of the winning operation.
*   **Acceptance Criteria:** Two users can open the same document; User A's edits appear on User B's screen in $<200\text{ms}$.

### 3.3 File Upload with Virus Scanning and CDN Distribution
*   **Priority:** High | **Status:** Not Started
*   **Description:** A secure pipeline for uploading educational assets (PDFs, Videos) and delivering them globally with low latency.
*   **Detailed Specs:**
    *   **Upload Flow:** Client $\to$ Signed URL $\to$ S3 Bucket (Temporary).
    *   **Virus Scanning:** A Lambda function is triggered upon upload. It utilizes **ClamAV** to scan the binary. If a virus is detected, the file is moved to a "Quarantine" bucket and the user is notified via a webhook.
    *   **CDN Integration:** Once cleared, the file is moved to a "Production" bucket linked to **CloudFront**. Edge locations must cache assets for 24 hours.
    *   **File Constraints:** Max file size 500MB. Supported MIME types: `application/pdf`, `video/mp4`, `image/jpeg`, `image/png`.
    *   **Metadata:** Each file must be indexed in the database with a checksum (SHA-256) to prevent duplicate uploads.
*   **Acceptance Criteria:** A user uploads a 10MB PDF; the file is scanned, moved to CDN, and available via a public URL within 10 seconds.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
*   **Priority:** Low | **Status:** Complete
*   **Description:** A personalized landing page for users to track their educational metrics.
*   **Detailed Specs:**
    *   **Widget Engine:** A grid-based layout system using `react-grid-layout`.
    *   **Persistence:** The coordinates $(x, y, w, h)$ of each widget are stored in a JSONB column in the `user_preferences` table.
    *   **Available Widgets:** 
        1. *Course Progress Bar* (fetches data from `/api/v1/progress`).
        2. *Upcoming Deadlines* (fetches data from `/api/v1/calendar`).
        3. *Recent Activity Feed* (fetches data from `/api/v1/activity`).
    *   **Interaction:** Users can drag widgets to rearrange them. The "Save Layout" button triggers a PATCH request to the preferences endpoint.
*   **Acceptance Criteria:** A user can move the "Course Progress" widget from the top-left to the bottom-right and have the layout persist after a page refresh.

### 3.5 Advanced Search with Faceted Filtering and Full-Text Indexing
*   **Priority:** Medium | **Status:** Complete
*   **Description:** A high-performance search engine for finding students, courses, and documents.
*   **Detailed Specs:**
    *   **Indexing:** Integration of **Elasticsearch**. Data is synced from Postgres via a Change Data Capture (CDC) pipeline.
    *   **Full-Text Search:** Implementation of "Fuzzy Matching" (Levenshtein distance of 2) to handle typos in student names.
    *   **Faceted Filtering:** Users can filter results by "Grade Level," "Subject," "Enrollment Date," and "Status."
    *   **Ranking:** Results are ranked based on a combination of TF-IDF and "Recency" (newer documents rank higher).
    *   **Performance:** Search queries must return results in $<300\text{ms}$ for a dataset of 1 million records.
*   **Acceptance Criteria:** Searching for "Algeba" (typo) returns results for "Algebra," and filtering by "Grade 10" correctly narrows the list.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under `https://api.rampart.ridgeline.com/v1/`.

| Endpoint | Method | Description | Request Body | Response (200 OK) |
| :--- | :--- | :--- | :--- | :--- |
| `/auth/login` | POST | Authenticates user | `{"user": "...", "pass": "..."}` | `{"token": "jwt_abc123", "expires": "..."}` |
| `/users/{id}` | GET | Retrieves user profile | N/A | `{"id": 1, "name": "John Doe", "role": "Teacher"}` |
| `/courses` | GET | List all courses (faceted) | `?subject=math&grade=10` | `{"courses": [...], "total": 45}` |
| `/courses/{id}/edit` | PATCH | Update course content | `{"content": "..."}` | `{"status": "success", "version": 4}` |
| `/files/upload-url` | POST | Request S3 Signed URL | `{"filename": "test.pdf"}` | `{"url": "https://s3...", "id": "file_99"}` |
| `/files/scan/{id}` | GET | Check virus scan status | N/A | `{"id": "file_99", "status": "clean"}` |
| `/dashboard/layout` | GET | Get user widget config | N/A | `{"widgets": [{"id": "prog", "x": 0, "y": 0}]}` |
| `/search` | GET | Full-text search | `?q=calculus&facet=grade` | `{"results": [...], "facets": {...}}` |

**Example Request (`/courses/{id}/edit`):**
```json
PATCH /v1/courses/502/edit
Content-Type: application/json
Authorization: Bearer eyJhbGci...

{
  "content": "Updated lesson on Quadratic Equations",
  "last_modified_by": "user_88"
}
```
**Example Response:**
```json
{
  "status": "success",
  "version": 4,
  "timestamp": "2026-07-12T14:22:01Z"
}
```

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL 15. To achieve performance targets, 30% of queries bypass the ORM and use raw SQL.

### 5.1 Tables and Relationships

1.  **`users`**: Primary user identity.
    *   `id` (UUID, PK), `email` (VARCHAR, Unique), `password_hash` (TEXT), `role_id` (FK), `created_at` (TIMESTAMP).
2.  **`roles`**: RBAC definitions.
    *   `id` (INT, PK), `role_name` (VARCHAR), `permissions` (JSONB).
3.  **`courses`**: Educational units.
    *   `id` (UUID, PK), `title` (VARCHAR), `description` (TEXT), `teacher_id` (FK $\to$ users.id), `version` (INT).
4.  **`enrollments`**: Many-to-Many relationship between users and courses.
    *   `id` (BIGINT, PK), `user_id` (FK), `course_id` (FK), `enrolled_at` (TIMESTAMP).
5.  **`documents`**: File metadata.
    *   `id` (UUID, PK), `course_id` (FK), `s3_key` (TEXT), `checksum` (VARCHAR), `status` (ENUM: 'scanning', 'clean', 'infected').
6.  **`document_versions`**: Version history for collaborative editing.
    *   `id` (BIGINT, PK), `doc_id` (FK), `content_delta` (JSONB), `user_id` (FK), `timestamp` (TIMESTAMP).
7.  **`user_preferences`**: Dashboard and UI settings.
    *   `user_id` (FK, PK), `layout_json` (JSONB), `theme` (VARCHAR), `updated_at` (TIMESTAMP).
8.  **`api_keys`**: For external partner access.
    *   `key_hash` (VARCHAR, PK), `user_id` (FK), `rate_limit` (INT), `is_sandbox` (BOOLEAN).
9.  **`audit_logs`**: SOC 2 Compliance tracking.
    *   `id` (BIGINT, PK), `user_id` (FK), `action` (VARCHAR), `ip_address` (INET), `timestamp` (TIMESTAMP).
10. **`tags`**: For faceted search.
    *   `id` (INT, PK), `tag_name` (VARCHAR), `category` (VARCHAR).

### 5.2 Key Relationships
*   `users` $\to$ `enrollments` (1:N) $\to$ `courses` (N:1).
*   `courses` $\to$ `documents` (1:N) $\to$ `document_versions` (1:N).
*   `users` $\to$ `user_preferences` (1:1).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Due to regulatory review cycles, releases are **quarterly**.

| Environment | Purpose | Infrastructure | Data Source |
| :--- | :--- | :--- | :--- |
| **Dev** | Feature development | Local Docker / K8s Namespace | Mock Data / Seeded DB |
| **Staging** | External Beta/QA | AWS EKS (m5.large) | Sanitized Prod Clone |
| **Prod** | Live Education System | AWS EKS (m5.xlarge $\times$ 3) | Primary Production DB |

### 6.2 Deployment Pipeline
1.  **CI/CD:** GitHub Actions triggers on merge to `main`.
2.  **Artifact:** Docker image pushed to AWS ECR.
3.  **Deployment:** Helm charts deploy to EKS.
4.  **Regulatory Gate:** Every quarter, a manual "Compliance Sign-off" is required by Ilya Stein and the SOC 2 auditor before the `prod` tag is updated.

### 6.3 Infrastructure Tools
*   **Containerization:** Docker / Kubernetes.
*   **Caching:** Redis (Cluster mode).
*   **Storage:** AWS S3 + CloudFront.
*   **Monitoring:** Prometheus + Grafana (Alerts configured for 5xx errors $> 1\%$).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (PyTest / Jest)
*   **Coverage Target:** 80% for Domain Logic.
*   **Focus:** Testing the "Core" in the hexagonal architecture. Mock adapters are used to isolate business rules.

### 7.2 Integration Testing
*   **Focus:** Port-to-Adapter communication.
*   **Method:** Using **Testcontainers** to spin up real PostgreSQL and Redis instances during the build process to ensure raw SQL queries are compatible with the current schema version.

### 7.3 End-to-End (E2E) Testing (Playwright)
*   **Focus:** Critical "Happy Paths" (e.g., User Login $\to$ Course Selection $\to$ Document Edit $\to$ Save).
*   **Frequency:** Executed nightly on the Staging environment.

### 7.4 SOC 2 Compliance Testing
*   **Penetration Testing:** Quarterly external audit.
*   **Access Logs:** Automated script to verify that `audit_logs` table is capturing every administrative action.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Budget cut by 30% next quarter | Medium | High | Accept risk; monitor weekly. If cut occurs, pivot "Low" priority features (Dashboard) to maintenance only. |
| **R2** | Integration partner API is undocumented/buggy | High | Medium | Assign dedicated owner (Solo Dev) to map endpoints via packet sniffing/trial-and-error. |
| **R3** | Raw SQL causes migration failure | High | Critical | Implement strict `sql-migrate` versioning and mandatory "Dry Run" on Staging before Prod deployment. |
| **R4** | Zero downtime breach during cutover | Low | Critical | Use a "Blue-Green" deployment strategy with a gradual traffic shift (5% $\to$ 25% $\to$ 100%). |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Description
*   **Phase 1: Foundation (Jan 2026 - June 2026):** Setting up the Hexagonal scaffolding and legacy adapters.
*   **Phase 2: Core Feature Parity (July 2026 - Oct 2026):** Implementing the collaborative editor and search.
*   **Phase 3: Hardening & Compliance (Nov 2026 - Dec 2026):** SOC 2 auditing and performance tuning.

### 9.2 Milestone Schedule
*   **Milestone 1: Architecture Review Complete**
    *   **Target Date:** 2026-06-15
    *   **Dependency:** Completion of Legacy Stack A/B/C mapping.
*   **Milestone 2: External Beta (10 Pilot Users)**
    *   **Target Date:** 2026-08-15
    *   **Dependency:** Sandbox API and Collaborative Editing stable.
*   **Milestone 3: Performance Benchmarks Met**
    *   **Target Date:** 2026-10-15
    *   **Dependency:** Full-text indexing and raw SQL optimization complete.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync
**Date:** 2023-11-02
**Attendees:** Ilya, Tariq, Alejandro
*   Hexagonal is a go.
*   Tariq worries about K8s overhead on a $150k budget.
*   Decided: Use small instances, scale horizontally only during peak school hours.
*   Alejandro says the legacy UI is "offensive"; agreed to prioritize a clean mobile-first shell.

### Meeting 2: Integration Crisis
**Date:** 2023-12-15
**Attendees:** Ilya, Solo Dev (Contractor)
*   Partner API returns 500s randomly.
*   No docs available.
*   Action: Solo dev to write a wrapper that implements "Exponential Backoff" retry logic.
*   Ilya: "Just make it work, don't ask them for docs again, they won't answer."

### Meeting 3: Budget Review
**Date:** 2024-01-20
**Attendees:** Ilya, Finance Lead
*   Budget is tight. $150k total.
*   Finance suggests cutting the "Customizable Dashboard."
*   Ilya: "It's already done. Leave it."
*   Warning: 30% cut possible in Q3. We just monitor it for now.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000.00

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Solo Developer / Contractor | $95,000 | Fixed-fee contract for 12 months. |
| **Infrastructure** | AWS (Compute, S3, RDS, EKS) | $25,000 | Optimized for "shoestring" (Spot instances). |
| **Tools** | Github, Slack, Sentry, ClamAV | $10,000 | Annual subscriptions. |
| **Compliance** | SOC 2 Audit & Certification | $15,000 | External auditor fee. |
| **Contingency** | Emergency Buffer | $5,000 | Reserved for critical API failures. |

---

## 12. APPENDICES

### Appendix A: Raw SQL Performance Optimization
Due to the ORM overhead, the following query pattern is used for the `enrollments` table to avoid "N+1" problems:
```sql
-- Bypassing ORM for performance
SELECT u.email, c.title 
FROM users u 
JOIN enrollments e ON u.id = e.user_id 
JOIN courses c ON e.course_id = c.id 
WHERE c.version = (SELECT MAX(version) FROM courses WHERE id = c.id)
AND u.role_id = 2;
```
*Note: This query must be manually updated if the `users` table is renamed during migration.*

### Appendix B: SOC 2 Type II Control Matrix
| Control ID | Requirement | Implementation in Rampart |
| :--- | :--- | :--- |
| CC6.1 | Access Control | OAuth2 + JWT with role-based access (RBAC). |
| CC7.2 | System Monitoring | Prometheus alerts for 5xx errors + CloudWatch logs. |
| CC8.1 | Change Management | Quarterly release cycles with mandatory sign-off in GitHub. |
| CC6.6 | Vulnerability Mgmt | ClamAV scanning for all user-uploaded files via Lambda. |