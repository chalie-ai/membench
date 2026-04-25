Due to the extensive length requirements (6,000–8,000 words), this document is presented as a comprehensive, professional project specification. It is designed to serve as the "Single Source of Truth" for Stormfront Consulting’s development team.

***

# PROJECT SPECIFICATION: PROJECT RAMPART
**Document Version:** 1.0.4  
**Last Updated:** 2023-10-27  
**Status:** Draft/Review  
**Classification:** Confidential – Stormfront Consulting Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Rampart is a high-stakes, moonshot R&D initiative commissioned by Stormfront Consulting. The objective is the development of a specialized Educational Learning Management System (LMS) tailored specifically for the aerospace industry. Unlike generic LMS platforms, Rampart is designed to handle the rigorous certification requirements, complex technical documentation, and high-security environments inherent to aerospace engineering and pilot training.

### 1.2 Business Justification
The aerospace industry is currently facing a critical talent gap and an aging workforce. Traditional training methods are insufficient for the rapid deployment of new safety protocols and the integration of next-generation propulsion systems. Stormfront Consulting aims to pivot from a pure consultancy model to a Product-as-a-Service (PaaS) model. By building Rampart, the company seeks to capture a niche market of Tier-1 aerospace manufacturers and government contractors who require a platform that meets stringent regulatory compliance (FAA, EASA) while providing a modern, serverless user experience.

### 1.3 ROI Projection and Financial Model
As a moonshot project, the immediate Return on Investment (ROI) is categorized as "Uncertain." However, executive sponsorship from the C-suite remains strong due to the strategic value of establishing a footprint in aerospace digital infrastructure.

**Projected ROI Timeline:**
- **Years 1-2 (Investment Phase):** Negative cash flow due to high R&D costs and the complexity of integrating three disparate legacy stacks.
- **Year 3 (Market Entry):** Target acquisition of three "Anchor Clients" with annual contract values (ACV) of $1.2M each.
- **Year 5 (Scaling):** Projected annual recurring revenue (ARR) of $15M with a gross margin of 72%, assuming a successful transition from a bespoke build to a multi-tenant SaaS architecture.

The funding model for Rampart is variable. Instead of a lump-sum budget, funds are released in tranches based on the successful completion of the three primary milestones (Production Launch, Stakeholder Sign-off, and Performance Benchmarking). This "milestone-gate" approach mitigates financial risk while maintaining the agility required for R&D.

### 1.4 Strategic Objectives
- **Modernization:** Replace fragmented legacy training silos with a unified API-orchestrated platform.
- **Compliance:** Ensure 100% adherence to GDPR and CCPA, with strict data residency in the EU.
- **Scalability:** Utilize a serverless architecture to handle bursts of high activity during certification cycles.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The "Hybrid Legacy" Stack
Rampart is unique and challenging because it inherits three different existing technical stacks that must interoperate seamlessly:
1. **Legacy A (The Core):** A monolithic Java/Spring application handling user records.
2. **Legacy B (The Content):** A Python/Django system managing aerospace course materials and PDF blobs.
3. **Legacy C (The Portal):** A Node.js/React frontend used for client-facing dashboards.

To unify these, Rampart employs a **Serverless Orchestration Layer**. Instead of a traditional monolith, all business logic is migrated to serverless functions (AWS Lambda / Azure Functions) coordinated by an API Gateway.

### 2.2 Architecture Diagram (ASCII Description)
The following represents the request-response flow of the Rampart ecosystem:

```text
[Client Layer] 
      | (HTTPS/TLS 1.3)
      v
[API Gateway (The Orchestrator)] 
      |
      +-----> [Auth Service] ----> (OAuth2 / JWT / RBAC)
      |
      +-----> [Lambda: Course Logic] ----> [Legacy B: Django API]
      |
      +-----> [Lambda: User Logic] ----> [Legacy A: Spring API]
      |
      +-----> [Lambda: Analytics] ----> [DynamoDB / Timestream]
      |
      +-----> [Event Bridge] ----> [Notification System (SNS/SQS)]
      |
[Data Residency Layer (EU-Central-1)]
      |
      +--> [PostgreSQL (RDS)]
      +--> [S3 Bucket (Encrypted)]
      +--> [Redis Cache]
```

### 2.3 Deployment Strategy
The platform utilizes a **CI/CD pipeline via GitHub Actions**. To ensure zero downtime and minimize risk during updates, a **Blue-Green Deployment** strategy is employed.
- **Blue Environment:** Current production version.
- **Green Environment:** New version being tested.
Traffic is shifted via the API Gateway once the Green environment passes all health checks.

### 2.4 Security and Compliance
Given the aerospace context, security is paramount.
- **GDPR/CCPA:** All personally identifiable information (PII) is encrypted at rest using AES-256.
- **Data Residency:** All database instances and S3 buckets are physically located in the EU (Frankfurt/Ireland regions) to meet legal requirements.
- **Network:** All serverless functions operate within a Private VPC; only the API Gateway is public-facing.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Review

**Description:** 
To protect the system from DDoS attacks and to manage the load on the inherited legacy stacks, Rampart requires a robust rate-limiting mechanism. This feature is not merely a security measure but a business tool for tiered pricing (e.g., "Standard" vs. "Enterprise" API limits).

**Functional Requirements:**
- **Throttling:** Implement a "Token Bucket" algorithm. Users are assigned a bucket of tokens that refills at a constant rate.
- **Tiers:**
    - *Tier 1 (Student):* 100 requests/minute.
    - *Tier 2 (Instructor):* 500 requests/minute.
    - *Tier 3 (Admin/System):* Unlimited.
- **Analytics Dashboard:** A real-time view for administrators showing the number of 429 (Too Many Requests) errors and peak usage times.
- **Headers:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Implementation:**
The rate limiter will be implemented as a "Lambda Authorizer" at the API Gateway level. It will query a Redis (ElastiCache) instance to track request counts per API Key/User ID. The usage data will be streamed via Kinesis to a Timestream database for long-term analytics.

**Acceptance Criteria:**
- The system must successfully reject requests exceeding the threshold with a 429 status code.
- The latency overhead added by the rate limiter must be $< 20\text{ms}$.

---

### 3.2 Feature 2: User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** Not Started

**Description:** 
The core of the LMS is its ability to distinguish between different user personas (Student, Instructor, Auditor, Administrator). RBAC must be granular enough to allow "Course-level" permissions.

**Functional Requirements:**
- **Authentication:** Integration with Corporate Single Sign-On (SSO) via SAML 2.0 and OpenID Connect (OIDC).
- **Roles:**
    - *Student:* Can view assigned courses, take quizzes, and track progress.
    - *Instructor:* Can create content, grade assignments, and view student analytics.
    - *Auditor:* Read-only access to audit trails and completion certificates for regulatory compliance.
    - *Administrator:* Full system control, including user management and API key issuance.
- **Session Management:** Stateless authentication using JWT (JSON Web Tokens) with a 15-minute expiration and a secure refresh token stored in an HttpOnly cookie.

**Technical Implementation:**
The RBAC logic will be centralized in a dedicated `Auth-Service` Lambda. This service will interface with the Legacy A (Spring) database to validate user identities. Permissions will be stored as a bitmask in the user profile to allow for rapid checking of complex permission sets.

**Acceptance Criteria:**
- A user with the 'Student' role must be unable to access the `/admin/settings` endpoint.
- SSO login must redirect back to the LMS dashboard within 3 seconds of successful authentication.

---

### 3.3 Feature 3: Notification System (Email, SMS, In-App, Push)
**Priority:** Low | **Status:** In Design

**Description:** 
An omni-channel notification system to alert users of course deadlines, grade updates, and system maintenance.

**Functional Requirements:**
- **Channel Selection:** Users can opt-in/out of specific channels (e.g., "Email for grades, Push for reminders").
- **Templates:** Support for dynamic templates (Handlebars.js) to allow instructors to personalize messages.
- **Scheduling:** Ability to schedule notifications (e.g., "Send reminder 24 hours before course expiry").
- **Priority Queuing:** "Critical" notifications (e.g., system downtime) must bypass the standard queue to ensure immediate delivery.

**Technical Implementation:**
A decoupled event-driven architecture. When an event occurs (e.g., `COURSE_COMPLETED`), the event is pushed to an AWS SNS Topic. Multiple SQS queues (one for each channel) subscribe to this topic. Specialized worker Lambdas then process these queues:
- *Email:* Via AWS SES.
- *SMS:* Via Twilio API.
- *Push:* Via Firebase Cloud Messaging (FCM).
- *In-App:* Via a WebSocket connection managed by API Gateway.

**Acceptance Criteria:**
- Notifications must be delivered within 60 seconds of the trigger event.
- The system must handle a burst of 10,000 simultaneous notifications without dropping messages.

---

### 3.4 Feature 4: Audit Trail Logging with Tamper-Evident Storage
**Priority:** Low | **Status:** In Design

**Description:** 
In the aerospace industry, "who did what and when" is a legal requirement. Rampart needs a non-repudiable log of all critical actions (e.g., changing a grade, modifying a safety certification).

**Functional Requirements:**
- **Immutable Logs:** Once a log is written, it cannot be edited or deleted, even by an administrator.
- **Coverage:** Every API call that modifies data (POST, PUT, DELETE) must be logged.
- **Metadata:** Logs must capture User ID, Timestamp, IP Address, Request Payload, and the specific Resource ID affected.
- **Integrity Verification:** A mechanism to prove that logs have not been altered since they were written.

**Technical Implementation:**
Logs will be written to an S3 bucket with "Object Lock" enabled (WORM - Write Once Read Many). To ensure tamper-evidence, the system will implement a **Merkle Tree** hashing strategy. Every hour, the system will generate a root hash of all logs created in that window and commit that hash to a private blockchain or a digitally signed ledger.

**Acceptance Criteria:**
- An auditor must be able to verify the integrity of a log entry using the root hash.
- The logging process must not increase the API response time by more than 50ms.

---

### 3.5 Feature 5: Workflow Automation Engine with Visual Rule Builder
**Priority:** Low | **Status:** Not Started

**Description:** 
A high-level tool allowing instructors to create "If-This-Then-That" (IFTTT) logic for student progression. (Example: "If student fails Quiz A twice, then enroll them in Remedial Module B and notify their supervisor").

**Functional Requirements:**
- **Visual Designer:** A drag-and-drop interface for building logic flows.
- **Triggers:** Events such as `Course_Complete`, `Quiz_Fail`, `Login_Inactivity_30_Days`.
- **Actions:** Actions such as `Send_Email`, `Unlock_Content`, `Assign_Role`.
- **Validation:** The engine must prevent infinite loops (e.g., Action A triggers Event B, which triggers Action A).

**Technical Implementation:**
The visual builder will be a React-based canvas using `React Flow`. The logic will be stored as a JSON graph in a NoSQL database. A "Workflow Engine" Lambda will act as a listener to the system's Event Bridge. When an event occurs, the engine will traverse the JSON graph to determine the subsequent action.

**Acceptance Criteria:**
- A non-technical instructor must be able to create a three-step workflow without writing code.
- The engine must execute the resulting action within 5 seconds of the trigger event.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned (`/v1/`) and require a Bearer Token in the Authorization header. Base URL: `https://api.rampart.stormfront.io/v1`

### 4.1 `GET /courses`
**Description:** Retrieves a list of all available courses.
- **Query Params:** `category` (string), `level` (string).
- **Request Example:** `GET /v1/courses?category=avionics`
- **Response (200 OK):**
```json
[
  {
    "courseId": "AV-101",
    "title": "Introduction to Avionics",
    "instructor": "Dr. Aris Thorne",
    "status": "active"
  }
]
```

### 4.2 `POST /courses/{courseId}/enroll`
**Description:** Enrolls the authenticated user in a specific course.
- **Request Body:** `{ "userId": "string" }`
- **Request Example:** `POST /v1/courses/AV-101/enroll` Body: `{"userId": "user_99"}`
- **Response (201 Created):**
```json
{
  "enrollmentId": "enr_5543",
  "enrollmentDate": "2023-11-01T10:00:00Z",
  "status": "enrolled"
}
```

### 4.3 `PUT /users/profile`
**Description:** Updates user profile information.
- **Request Body:** `{ "firstName": "string", "lastName": "string", "timezone": "string" }`
- **Response (200 OK):**
```json
{
  "userId": "user_99",
  "updatedAt": "2023-11-01T12:00:00Z",
  "status": "success"
}
```

### 4.4 `GET /analytics/usage`
**Description:** Returns API usage statistics (Admin only).
- **Response (200 OK):**
```json
{
  "totalRequests": 1500000,
  "rateLimitHits": 450,
  "peakConcurrentUsers": 1200,
  "period": "2023-10-01 to 2023-10-31"
}
```

### 4.5 `POST /auth/login`
**Description:** Authenticates user and returns JWT.
- **Request Body:** `{ "username": "string", "password": "password" }`
- **Response (200 OK):**
```json
{
  "accessToken": "eyJhbGci...",
  "refreshToken": "def456...",
  "expiresIn": 900
}
```

### 4.6 `GET /audit/logs`
**Description:** Fetches audit logs based on filters (Auditor role required).
- **Query Params:** `resourceId` (string), `startDate` (ISO Date).
- **Response (200 OK):**
```json
[
  {
    "logId": "log_882",
    "timestamp": "2023-10-25T14:20:00Z",
    "action": "GRADE_CHANGE",
    "user": "instr_01",
    "hash": "sha256:a1b2c3..."
  }
]
```

### 4.7 `POST /notifications/send`
**Description:** Triggers a manual notification to a user.
- **Request Body:** `{ "userId": "string", "channel": "sms|email|push", "message": "string" }`
- **Response (202 Accepted):**
```json
{
  "notificationId": "notif_771",
  "status": "queued"
}
```

### 4.8 `GET /courses/{courseId}/content`
**Description:** Retrieves the curriculum structure for a course.
- **Response (200 OK):**
```json
{
  "courseId": "AV-101",
  "modules": [
    { "id": "m1", "title": "Basic Electronics", "files": ["doc1.pdf", "vid1.mp4"] },
    { "id": "m2", "title": "Circuitry", "files": ["doc2.pdf"] }
  ]
}
```

---

## 5. DATABASE SCHEMA

The system utilizes a polyglot persistence strategy. Primary relational data is stored in **PostgreSQL**, while event logs and session data are in **DynamoDB/Redis**.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | None | `email`, `password_hash`, `role_id`, `mfa_enabled` | Central user directory |
| `Roles` | `role_id` | None | `role_name`, `permission_mask` | RBAC role definitions |
| `Courses` | `course_id` | `creator_id` | `title`, `description`, `version`, `is_published` | Course metadata |
| `Modules` | `module_id` | `course_id` | `order_index`, `title`, `content_type` | Course structure |
| `Enrollments` | `enroll_id` | `user_id`, `course_id` | `enroll_date`, `completion_status`, `final_grade` | User-course mapping |
| `Assessments`| `assessment_id`| `module_id` | `type` (quiz/exam), `passing_score`, `max_attempts` | Test configurations |
| `User_Scores`| `score_id` | `user_id`, `assessment_id`| `score`, `attempt_number`, `timestamp` | Grade tracking |
| `Audit_Logs` | `log_id` | `user_id` | `action_type`, `resource_id`, `payload_hash`, `timestamp` | Tamper-evident trail |
| `Notifications`| `notif_id` | `user_id` | `channel`, `message`, `is_read`, `sent_at` | Communication history |
| `Workflows` | `wf_id` | `creator_id` | `json_definition`, `is_active`, `trigger_event` | Automation rules |

### 5.2 Relationships
- **Users $\to$ Enrollments:** One-to-Many.
- **Courses $\to$ Modules:** One-to-Many.
- **Modules $\to$ Assessments:** One-to-Many.
- **Users $\to$ Audit\_Logs:** One-to-Many.
- **Enrollments $\to$ User\_Scores:** One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

#### 6.1.1 Development Environment (`dev`)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Localized Docker containers and a shared "sandbox" AWS account.
- **Data:** Anonymized sample data.
- **Deployment:** Automatic deploy on push to `develop` branch.

#### 6.1.2 Staging Environment (`stg`)
- **Purpose:** Integration testing, UAT (User Acceptance Testing), and Pre-production validation.
- **Infrastructure:** Mirror of production (Serverless + RDS EU-Central-1).
- **Data:** Sanitized copies of production data.
- **Deployment:** Triggered by merge to `release` branch.

#### 6.1.3 Production Environment (`prod`)
- **Purpose:** Live end-user traffic.
- **Infrastructure:** High-availability, multi-AZ deployment in the EU.
- **Data:** Live encrypted production data.
- **Deployment:** Blue-Green shift via GitHub Actions after manual sign-off from Lina Jensen.

### 6.2 Infrastructure as Code (IaC)
The entire stack is defined using **Terraform**. This ensures that the environment can be replicated exactly across regions if the data residency requirements change or if a disaster recovery site is needed in a secondary EU region.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual Lambda functions and utility classes.
- **Tooling:** Jest (Node.js), PyTest (Python), JUnit (Java).
- **Requirement:** 80% minimum code coverage.
- **Execution:** Runs on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Inter-service communication (e.g., API Gateway $\to$ Lambda $\to$ Legacy Database).
- **Tooling:** Postman/Newman and Supertest.
- **Focus:** Validating that the "Hybrid Stack" communicates correctly across different protocols (REST, gRPC).
- **Execution:** Runs on the `stg` environment before any release.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., Student logs in $\to$ completes course $\to$ receives certificate).
- **Tooling:** Cypress.io.
- **Focus:** UI/UX stability and cross-browser compatibility.
- **Execution:** Weekly regression suite.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Team lacks experience with the mixed serverless/legacy stack. | High | High | **Contingency Plan:** Maintain a fallback architecture using a standard Kubernetes (EKS) cluster if serverless orchestration proves too complex. |
| **R2** | Integration partner's API is undocumented and buggy. | High | Medium | **Ownership:** Sergei Gupta is assigned as the "Integration Lead" to document the API manually and build a wrapper layer to handle errors. |
| **R3** | Legal review of Data Processing Agreement (DPA) is delayed. | Medium | High | **Blocker Management:** Use mock data in staging and avoid actual PII until legal sign-off is received. |
| **R4** | CI Pipeline inefficiency (45-min build time). | High | Medium | **Technical Debt:** Implement parallelization of test suites and cache Docker layers in GitHub Actions. |

### 8.1 Probability/Impact Matrix
- **High/High:** Immediate action required (R1).
- **High/Medium:** Planned mitigation (R2, R4).
- **Medium/High:** Executive escalation (R3).

---

## 9. TIMELINE AND PHASES

The project follows a phased approach leading up to the 2026 launch.

### Phase 1: Foundation & Integration (Current - 2025-03-01)
- Setup IaC and CI/CD pipelines.
- Create the API Gateway orchestration layer.
- Connect Legacy A, B, and C.
- **Dependency:** Legal sign-off on DPA.

### Phase 2: Core Feature Implementation (2025-03-02 - 2025-12-31)
- Develop RBAC and Auth systems.
- Implement Rate Limiting and Analytics.
- Build Course Management API.
- **Dependency:** Successful integration of Legacy B.

### Phase 3: Advanced Features & Polishing (2026-01-01 - 2026-04-14)
- Build Audit Trail and Notification system.
- Final UI polish.
- Full E2E regression testing.

### Phase 4: Deployment & Stabilization (2026-04-15 - 2026-08-15)
- **Milestone 1 (2026-04-15):** Production Launch.
- **Milestone 2 (2026-06-15):** Stakeholder Demo and Sign-off.
- **Milestone 3 (2026-08-15):** Performance Benchmarks Met (Latency $< 200\text{ms}$ 95th percentile).

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per project standards, no formal minutes are kept; decisions are captured in Slack threads.

### Meeting 1: Stack Alignment (Thread: #proj-rampart-arch)
**Participants:** Lina Jensen, Sergei Gupta, Saoirse Liu
- **Sergei:** "The Legacy A Spring app is throwing 504s when the Lambda hits it too hard. We can't just point the Gateway at it."
- **Lina:** "Do we need a queue?"
- **Saoirse:** "Yes, but only for writes. For reads, let's implement a Redis cache in the orchestration layer. That should protect the legacy core."
- **Decision:** Implement Redis caching for all User-Profile reads. Sergei to lead.

### Meeting 2: Compliance Deep-Dive (Thread: #proj-rampart-security)
**Participants:** Lina Jensen, Saoirse Liu, Maren Jensen (Intern)
- **Saoirse:** "The client is insisting on EU data residency. If we use AWS US-East-1 for any part of the pipeline, we're non-compliant."
- **Maren:** "Can we use a multi-region setup?"
- **Saoirse:** "No, the data itself must stay in the EU. I'm locking the Terraform providers to `eu-central-1`."
- **Decision:** All S3 and RDS resources will be strictly pinned to Frankfurt.

### Meeting 3: Pipeline Frustrations (Thread: #proj-rampart-devops)
**Participants:** Sergei Gupta, Maren Jensen
- **Sergei:** "The CI pipeline is taking 45 minutes. I'm losing half my day just waiting for builds."
- **Maren:** "I noticed the unit tests for the Legacy B stack are running sequentially. I can try to parallelize them using a matrix strategy in GitHub Actions."
- **Sergei:** "Do it. This is a major blocker for velocity."
- **Decision:** Maren to optimize CI pipeline; target build time $< 15$ minutes.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches. Total projected budget for the R&D phase: **$4,200,000**.

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel** | $2,800,000 | 20+ staff across 3 departments (Dev, Security, QA). |
| **Infrastructure** | $600,000 | AWS Consumption (Lambda, RDS, S3, Redis) + License fees. |
| **Tools & Software** | $150,000 | GitHub Enterprise, Jira, Datadog, Twilio, Snyk. |
| **Contingency** | $650,000 | Reserved for R1/R2 mitigation (e.g., hiring external consultants). |

**Funding Tranche Schedule:**
- **Tranche 1 (Current):** $1.5M for Foundation and Integration.
- **Tranche 2 (Post-Launch):** $1.5M released upon successful 2026-04-15 launch.
- **Tranche 3 (Post-Benchmark):** $1.2M released upon Milestone 3 completion.

---

## 12. APPENDICES

### Appendix A: Legacy Stack Mapping
For the development team, the following mapping is used when referencing the mixed stacks in Jira tickets:
- **L-S-01 (Legacy Spring):** Handles `Users`, `Roles`, `Permissions`.
- **L-D-01 (Legacy Django):** Handles `CourseContent`, `PDF_Blobs`, `Video_Metadata`.
- **L-N-01 (Legacy Node):** Handles `Frontend_State`, `Session_Cache`.

### Appendix B: Performance Benchmark Requirements
To satisfy Milestone 3 (2026-08-15), the platform must meet the following metrics:
1. **Cold Start Latency:** Lambda functions must initialize in $< 500\text{ms}$.
2. **API Response Time:** 95% of all `GET` requests must resolve in $< 200\text{ms}$.
3. **Throughput:** Support 5,000 concurrent users without a degradation in response time beyond 10%.
4. **Uptime:** 99.9% availability across the first 90 days post-launch.