# PROJECT SPECIFICATION: PROJECT MONOLITH
**Document Version:** 1.0.4  
**Status:** Draft / Under Review  
**Date:** October 26, 2023  
**Classification:** Confidential – Stormfront Consulting Internal  
**Owner:** Arun Liu (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Monolith" represents a strategic pivot for Stormfront Consulting, moving from a generalist consultancy model to a product-driven vertical within the logistics and shipping industry. The catalyst for this initiative is a contractual agreement with a Tier-1 global logistics enterprise (the "Anchor Client"). The Anchor Client has committed to a recurring annual payment of $2,000,000 upon the successful delivery of a modernized API Gateway and a microservices-based backend capable of handling high-volume shipping telemetry and order management.

The current legacy infrastructure is a monolithic Django application that has reached its scaling ceiling. It suffers from "noisy neighbor" problems where large data imports freeze the UI for all users. To capture the $2M annual revenue and expand into the wider logistics market, Stormfront must migrate to a distributed architecture that ensures high availability, strict security compliance, and linear scalability.

### 1.2 ROI Projection and Financial Impact
The project is backed by a board-approved budget of $5,000,000+. The primary Return on Investment (ROI) is calculated across three vectors:
1. **Direct Revenue:** The $2M annual contract from the Anchor Client provides a 40% annual return on the initial $5M investment, reaching break-even within 2.5 years of launch.
2. **Operational Efficiency:** A core success metric is the reduction of cost per transaction by 35%. By migrating from expensive over-provisioned EC2 instances to a right-sized AWS ECS (Elastic Container Service) cluster with Fargate, we project a monthly infrastructure saving of $12,000.
3. **Market Positioning:** SOC 2 Type II compliance will allow Stormfront to bid for other Fortune 500 logistics contracts, potentially scaling the annual recurring revenue (ARR) from $2M to $10M within 24 months.

### 1.3 Strategic Objectives
The objective is to decompose the existing monolith into a set of event-driven microservices coordinated by a centralized API Gateway. This will allow for independent scaling of the "Data Import" service (which is resource-intensive) without affecting the "Authentication" or "Reporting" services. The transition will be managed via canary releases and feature flags to ensure zero downtime for the Anchor Client.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Project Monolith utilizes a microservices architecture deployed on AWS ECS. The system is designed to handle 10x the current load of the legacy system through asynchronous processing and horizontal scaling.

**The Stack:**
- **Language:** Python 3.11 / Django 4.2 (Framework for service logic)
- **Database:** PostgreSQL 15 (Relational storage)
- **Caching/Queueing:** Redis 7.0 (Distributed caching and task state)
- **Messaging:** Apache Kafka 3.4 (Event-driven communication)
- **Deployment:** AWS ECS Fargate, AWS ALB (Application Load Balancer)
- **Configuration:** LaunchDarkly (Feature Flagging)

### 2.2 System Flow (ASCII Diagram Description)
The request flow is designed to decouple the client from the processing logic:

```
[ Client Request ] 
       |
       v
[ AWS Application Load Balancer ]
       |
       v
[ API Gateway Service (Django) ] <---> [ Redis (Rate Limiting/Session) ]
       |
       |--- (Synchronous REST) ---> [ Auth Service ]
       |--- (Synchronous REST) ---> [ User Profile Service ]
       |
       |--- (Asynchronous Event) --> [ Kafka Topic: "incoming_data" ]
                                            |
                                            v
                                [ Data Processing Service ]
                                            |
                                            v
                                [ PostgreSQL Cluster ] <---> [ S3 Storage ]
```

### 2.3 Event-Driven Communication
To avoid the "distributed monolith" trap, services communicate primarily via Kafka. For example, when a user uploads a shipping manifest (Feature 1), the API Gateway publishes a `MANIFEST_UPLOADED` event. The Data Processing Service consumes this event, performs the auto-detection and import, and then publishes a `MANIFEST_PROCESSED` event, which the Notification Service uses to alert the user.

### 2.4 Infrastructure Constraints
A critical risk identified is that performance requirements are 10x the current system capacity, yet no additional infrastructure budget has been allocated beyond the initial $5M. To mitigate this, the team will implement:
- **Aggressive Caching:** Redis will be used to cache all static logistics lookups (port codes, carrier IDs).
- **Read Replicas:** PostgreSQL read replicas will be used to offload the reporting engine from the primary write database.
- **Connection Pooling:** PgBouncer will be implemented to manage the high volume of concurrent connections from ECS tasks.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Feature 1: Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
The system must allow logistics operators to upload bulk shipping data in various formats (CSV, JSON, XML, EDIFACT). The system must automatically detect the file format and the specific schema version without requiring the user to select the format from a dropdown.

**Functional Requirements:**
- **Auto-Detection Engine:** A Python-based utility using magic-byte analysis and regex pattern matching to identify the file type.
- **Schema Validation:** Once the format is detected, the system must validate the data against a set of predefined logistics schemas (e.g., ensuring `container_id` follows ISO 6346 standards).
- **Asynchronous Processing:** Files larger than 5MB must be streamed to S3 and processed asynchronously via Kafka to prevent API timeout.
- **Export Engine:** Users must be able to export filtered datasets back into any of the supported formats.

**Technical Detail:**
The implementation will use `pandas` for data manipulation and `pydantic` for schema enforcement. The "In Progress" status reflects the current struggle with the "Three Date Formats" technical debt; the importer is currently failing when files mix ISO-8601, US-Short, and Epoch timestamps.

### 3.2 Feature 2: API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Not Started

**Description:**
To protect the system from being overwhelmed (especially given the 10x load requirement), a sophisticated rate-limiting layer must be implemented at the API Gateway.

**Functional Requirements:**
- **Tiered Limiting:** Different limits based on the user's role (e.g., Admin: 10,000 req/hr; Standard: 1,000 req/hr).
- **Sliding Window Algorithm:** Use Redis to implement a sliding window counter to prevent "burst" traffic at the turn of the hour.
- **Usage Dashboard:** An internal analytics view for Stormfront Consulting to track which endpoints are most utilized and identify potential bottlenecks.
- **Header Feedback:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Detail:**
This will be implemented as a Django Middleware in the API Gateway service. Redis `INCR` and `EXPIRE` commands will be used to track request counts per API key.

### 3.3 Feature 3: SSO Integration (SAML and OIDC)
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Description:**
Enterprise clients require the ability to manage users through their own Identity Providers (IdP) such as Okta, Azure AD, or Ping Identity.

**Functional Requirements:**
- **SAML 2.0 Support:** Support for Service Provider (SP) initiated SSO.
- **OIDC Flow:** Implementation of the Authorization Code Flow with PKCE for secure authentication.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user account in the Monolith database upon the first successful SSO login.
- **Attribute Mapping:** Map SAML assertions (e.g., `memberOf`) to Monolith internal roles.

**Technical Detail:**
The team will utilize the `python3-saml` and `authlib` libraries. This feature is currently low priority as the Anchor Client has agreed to use standard RBAC for the initial onboard phase.

### 3.4 Feature 4: User Authentication and RBAC
**Priority:** High | **Status:** In Progress

**Description:**
A robust security layer to ensure that users can only access data relevant to their organizational unit and role.

**Functional Requirements:**
- **JWT Implementation:** Use JSON Web Tokens (JWT) for stateless authentication between the Gateway and microservices.
- **Role Hierarchy:** Implementation of roles: `SuperAdmin`, `OrgAdmin`, `Dispatcher`, and `ReadOnly`.
- **Permission Matrix:** Granular permissions (e.g., `can_edit_manifest`, `can_approve_shipment`) tied to roles.
- **Session Management:** Redis-based session revocation to allow admins to force-logout users.

**Technical Detail:**
Currently, the "In Progress" status is stalled due to the design disagreement between the Product Lead and the Engineering Lead regarding whether roles should be stored in the JWT (increasing token size) or fetched from the database on every request (increasing latency).

### 3.5 Feature 5: PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Description:**
The ability to generate complex shipping summaries and deliver them to stakeholders via email or SFTP on a schedule.

**Functional Requirements:**
- **Template Engine:** Use Jinja2 to generate HTML templates that are converted to PDF via `WeasyPrint`.
- **Scheduling Engine:** Use Celery Beat to trigger reports daily, weekly, or monthly.
- **Delivery Pipeline:** Integration with AWS SES for email delivery and an SFTP client for enterprise file drops.
- **Audit Log:** Record exactly when a report was generated and who received it.

**Technical Detail:**
This feature is **Blocked**. The blocking issue is the lack of a normalized date layer (Technical Debt). Because reports require precise "Date Range" filtering, the inconsistency between the three date formats in the database is causing reports to either omit data or duplicate entries.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 `POST /import/upload`
- **Description:** Uploads a data file for auto-detection and processing.
- **Request:** `Multipart/form-data` (File: `manifest.csv`)
- **Response (202 Accepted):**
  ```json
  {
    "job_id": "job_88231",
    "status": "processing",
    "estimated_completion": "2025-04-15T14:30:00Z"
  }
  ```

### 4.2 `GET /import/status/{job_id}`
- **Description:** Checks the progress of a specific import job.
- **Request:** `job_id` (Path variable)
- **Response (200 OK):**
  ```json
  {
    "job_id": "job_88231",
    "progress": "65%",
    "errors": [{"row": 45, "msg": "Invalid Container ID"}]
  }
  ```

### 4.3 `GET /analytics/usage`
- **Description:** Retrieves API usage statistics for the current user/org.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "total_requests": 5500,
    "rate_limit_hit_count": 12,
    "peak_hour": "2025-04-10T10:00:00Z"
  }
  ```

### 4.4 `POST /auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Request:** `{ "username": "user1", "password": "password123" }`
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGci...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
  ```

### 4.5 `GET /users/me`
- **Description:** Retrieves the current authenticated user's profile and roles.
- **Request:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "id": 101,
    "email": "op@logistics.com",
    "roles": ["Dispatcher", "OrgAdmin"]
  }
  ```

### 4.6 `POST /reports/schedule`
- **Description:** Schedules a recurring PDF report.
- **Request:** `{ "report_type": "monthly_volume", "frequency": "monthly", "recipient": "boss@logistics.com" }`
- **Response (201 Created):**
  ```json
  { "schedule_id": "sched_991", "next_run": "2025-05-01T00:00:00Z" }
  ```

### 4.7 `GET /shipments/{shipment_id}`
- **Description:** Fetches detailed shipping data for a specific ID.
- **Request:** `shipment_id` (Path variable)
- **Response (200 OK):**
  ```json
  { "id": "SHIP123", "origin": "CNSHA", "destination": "USLAX", "status": "In Transit" }
  ```

### 4.8 `PATCH /shipments/{shipment_id}`
- **Description:** Updates shipment status.
- **Request:** `{ "status": "Delivered" }`
- **Response (200 OK):**
  ```json
  { "id": "SHIP123", "status": "Delivered", "updated_at": "2025-04-15T12:00:00Z" }
  ```

---

## 5. DATABASE SCHEMA

The system uses a PostgreSQL 15 cluster. To maintain performance under 10x load, heavy indexing is applied to `shipment_id` and `org_id`.

### 5.1 Table Definitions

1. **`organizations`**
   - `id` (UUID, PK)
   - `name` (VARCHAR 255)
   - `industry_segment` (VARCHAR 50)
   - `created_at` (TIMESTAMP)
   - *Relationship: One-to-Many with Users and Shipments.*

2. **`users`**
   - `id` (UUID, PK)
   - `org_id` (UUID, FK -> organizations.id)
   - `email` (VARCHAR 255, Unique)
   - `password_hash` (TEXT)
   - `last_login` (TIMESTAMP)
   - *Relationship: Many-to-Many with Roles.*

3. **`roles`**
   - `id` (INT, PK)
   - `role_name` (VARCHAR 50) — e.g., 'SuperAdmin'
   - `description` (TEXT)

4. **`user_roles`**
   - `user_id` (UUID, FK -> users.id)
   - `role_id` (INT, FK -> roles.id)
   - *Primary Key: (user_id, role_id)*

5. **`shipments`**
   - `id` (VARCHAR 50, PK) — Shipping ID
   - `org_id` (UUID, FK -> organizations.id)
   - `origin_port` (VARCHAR 5)
   - `destination_port` (VARCHAR 5)
   - `weight` (DECIMAL)
   - `status` (VARCHAR 20)
   - `created_date` (TIMESTAMP) — *Note: Site of date format conflict.*

6. **`import_jobs`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id)
   - `file_path` (TEXT) — Path to S3 bucket
   - `status` (VARCHAR 20) — 'pending', 'processing', 'completed', 'failed'
   - `detected_format` (VARCHAR 10)
   - `row_count` (INT)

7. **`import_errors`**
   - `id` (BIGINT, PK)
   - `job_id` (UUID, FK -> import_jobs.id)
   - `row_number` (INT)
   - `error_message` (TEXT)
   - `column_name` (VARCHAR 50)

8. **`api_usage_logs`**
   - `id` (BIGINT, PK)
   - `user_id` (UUID, FK -> users.id)
   - `endpoint` (VARCHAR 255)
   - `response_code` (INT)
   - `latency_ms` (INT)
   - `timestamp` (TIMESTAMP)

9. **`report_schedules`**
   - `id` (UUID, PK)
   - `org_id` (UUID, FK -> organizations.id)
   - `report_type` (VARCHAR 50)
   - `frequency` (VARCHAR 20)
   - `recipient_email` (VARCHAR 255)
   - `last_run` (TIMESTAMP)

10. **`audit_logs`**
    - `id` (BIGINT, PK)
    - `user_id` (UUID, FK -> users.id)
    - `action` (TEXT)
    - `entity_id` (VARCHAR 50)
    - `timestamp` (TIMESTAMP)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Stormfront Consulting employs a three-tier environment strategy to ensure SOC 2 compliance and stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Individual developer testing and feature prototyping.
- **Infrastructure:** Small ECS cluster, shared PostgreSQL instance.
- **Deployment:** Triggered by merge to `develop` branch via GitHub Actions.
- **Data:** Synthetic data only.

#### 6.1.2 Staging (Staging)
- **Purpose:** QA testing, UAT (User Acceptance Testing) with the Anchor Client.
- **Infrastructure:** Mirror of Production (Production-parity).
- **Deployment:** Triggered by release tags.
- **Data:** Anonymized production snapshots.

#### 6.1.3 Production (Prod)
- **Purpose:** Live Anchor Client operations.
- **Infrastructure:** Multi-AZ ECS Fargate, RDS PostgreSQL with Multi-AZ failover, ElastiCache Redis.
- **Deployment:** Canary releases (10% $\to$ 25% $\to$ 50% $\to$ 100%) managed by AWS App Mesh.
- **Security:** All traffic encrypted via TLS 1.3; VPC private subnets for all database and Kafka traffic.

### 6.2 Feature Flagging and Canary Releases
To mitigate the risk of regression, **LaunchDarkly** is used for all new feature rollouts.
- **Flagging Logic:** New code is deployed to production but remains inactive. The PM (once the disagreement is resolved) toggles the feature for the Anchor Client's specific `org_id` first.
- **Canary Process:** 
  1. Deploy Version 1.1 to a small subset of containers.
  2. Monitor Error Rates and Latency via CloudWatch.
  3. If `5xx` errors increase by $>1\%$, automatic rollback is triggered.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** `pytest`
- **Requirement:** Minimum 80% code coverage for all new microservices.
- **Focus:** Business logic in the `services.py` layer, specifically the auto-detection regex for file formats.

### 7.2 Integration Testing
- **Tooling:** `Postman` / `Pytest-django`
- **Requirement:** All API Gateway $\to$ Microservice calls must be tested.
- **Focus:** Kafka event propagation. A test must verify that a `POST /import/upload` eventually results in a record in the `shipments` table.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** `Selenium` / `Cypress`
- **Requirement:** Critical Path Testing (The "Happy Path").
- **Focus:** The full user journey: Login $\to$ Upload Manifest $\to$ Verify Import $\to$ Generate Report.

### 7.4 Performance Testing
- **Tooling:** `Locust`
- **Requirement:** System must sustain 10x the current load (approx. 5,000 concurrent requests per second) without exceeding a 200ms p99 latency.
- **Focus:** Database lock contention during bulk imports.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Competitor is building similar product and is 2 months ahead. | High | Critical | Escalate to steering committee for additional funding to accelerate Feature 1 & 4. |
| **R2** | Performance requirements 10x current capacity with no extra budget. | High | High | Document aggressive caching and read-replica workarounds; share with team immediately. |
| **R3** | SOC 2 Type II audit failure. | Medium | Critical | Monthly internal pre-audits; engage external consultants for gap analysis. |
| **R4** | Team dysfunction (PM vs Lead Eng) stalls decision making. | High | Medium | CTO (Arun Liu) to act as final tie-breaker for all architectural disputes. |
| **R5** | Date format technical debt causes data corruption. | High | Medium | Implement a "Normalization Layer" middleware to convert all dates to UTC ISO-8601. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundation (Now – 2025-04-15)
- **Focus:** Core API Gateway, Auth, and Data Import.
- **Dependency:** Resolution of the design disagreement regarding RBAC.
- **Milestone 1:** First paying customer onboarded (Target: 2025-04-15).

### 9.2 Phase 2: Stability & Scaling (2025-04-16 – 2025-06-15)
- **Focus:** Rate limiting, Kafka optimization, and SOC 2 audit preparation.
- **Dependency:** Successful onboarding of the first customer.
- **Milestone 2:** Production launch (Target: 2025-06-15).

### 9.3 Phase 3: Feature Completion (2025-06-16 – 2025-08-15)
- **Focus:** SSO Integration and Report Generation.
- **Dependency:** Resolution of date normalization technical debt.
- **Milestone 3:** MVP feature-complete (Target: 2025-08-15).

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment
**Date:** 2023-11-02  
**Attendees:** Arun Liu, Dmitri Fischer, Malik Oduya, Matteo Nakamura, Product Lead (PL), Lead Engineer (LE).

**Discussion:**
- The PL argued that RBAC roles should be embedded in the JWT to reduce database hits.
- The LE argued that JWTs would become too large, causing header overflows in the ALB, and that roles should be cached in Redis instead.
- The discussion devolved into a personal argument; the PL and LE stopped speaking for the remainder of the meeting.

**Action Items:**
- **Arun Liu:** Review ALB header limits and make a final decision on JWT vs. Redis for roles. (Due: 2023-11-05)
- **Dmitri Fischer:** Set up the Kafka cluster in the Dev environment. (Due: 2023-11-10)

### Meeting 2: Performance Crisis Review
**Date:** 2023-11-15  
**Attendees:** Arun Liu, Dmitri Fischer, Matteo Nakamura.

**Discussion:**
- Dmitri presented the load test results: the system crashes at 3x the current load, far below the 10x requirement.
- Matteo noted that the Support team is already seeing "Timeout" tickets from the beta users.
- It was confirmed that there is $0 additional budget for larger AWS instances.
- Decision: The team will implement a "Queue-First" approach where all heavy writes are pushed to Kafka and processed in the background.

**Action Items:**
- **Dmitri Fischer:** Document the "Workaround Architecture" for the 10x load and share it with the full team. (Due: 2023-11-20)
- **Matteo Nakamura:** Create a communication template for users experiencing timeouts. (Due: 2023-11-17)

### Meeting 3: Technical Debt & SOC 2 Sync
**Date:** 2023-12-01  
**Attendees:** Arun Liu, Malik Oduya, Dmitri Fischer.

**Discussion:**
- Malik reported that the E2E tests for reports are failing because the database contains dates in `MM/DD/YYYY`, `YYYY-MM-DD`, and Unix Epoch.
- The team agreed that "Feature 5: Reporting" is officially blocked until a normalization layer is built.
- Discussed SOC 2 requirements; Dmitri noted that we need centralized logging for all administrative actions to pass the audit.

**Action Items:**
- **Malik Oduya:** Map all instances of date usage across the 12 microservices. (Due: 2023-12-10)
- **Dmitri Fischer:** Configure CloudWatch logs to retain data for 1 year per SOC 2 requirements. (Due: 2023-12-15)

---

## 11. BUDGET BREAKDOWN

The total budget of $5,000,000+ is allocated across the project lifecycle (approx. 18 months).

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,000,000 | 12-person team, including CTO and specialized DevOps/QA. |
| **Infrastructure** | 20% | $1,000,000 | AWS ECS, RDS, Kafka (MSK), Redis, S3. |
| **Tools & Licensing**| 10% | $500,000 | LaunchDarkly, Datadog, SOC 2 Audit Fees, PagerDuty. |
| **Contingency** | 10% | $500,000 | Reserved for "Risk 1" (Competitive acceleration). |
| **Total** | **100%** | **$5,000,000** | |

---

## 12. APPENDICES

### Appendix A: Date Normalization Specification
To resolve the current blocker on Feature 5, the team will implement the following normalization logic in a new shared library (`stormfront-common-utils`):

1. **Input Detection:** Use `dateutil.parser` to attempt to guess the format of incoming strings.
2. **Standardization:** All dates must be converted to `datetime.datetime` objects in UTC.
3. **Persistence:** All database writes will use `TIMESTAMP WITH TIME ZONE` in PostgreSQL.
4. **API Presentation:** All API responses will use ISO-8601 format: `YYYY-MM-DDTHH:mm:ssZ`.

### Appendix B: SOC 2 Type II Compliance Checklist
The following controls must be verified before the June 15th production launch:
- **Access Control:** All developers must use MFA for AWS Console access.
- **Change Management:** Every production deploy must be linked to a Jira ticket and a Peer Review (GitHub PR).
- **Encryption:** All data at rest in RDS must be encrypted using AWS KMS.
- **Logging:** All `DELETE` and `PATCH` requests to the `/shipments` endpoint must be logged with the UserID and Timestamp.
- **Vulnerability Scanning:** Weekly Snyk scans on all Python dependencies to ensure no critical CVEs are present.