# Project Specification: Project Nexus
**Version:** 1.0.4  
**Status:** Draft / Under Review  
**Date:** October 24, 2023  
**Document Owner:** Sage Moreau, Engineering Manager  
**Confidentiality Level:** Internal / HIPAA Compliant

---

## 1. Executive Summary

**Project Nexus** represents the strategic evolution of Deepwell Data’s internal productivity suite. Originally conceived as a high-energy hackathon project to streamline food and beverage logistics and inventory tracking, the tool has organically scaled to support 500 daily active users (DAU). However, the current "monolithic hack" architecture has reached a critical inflection point. To transition from an internal utility to a scalable, commercially viable product capable of onboarding external paying customers, Project Nexus will migrate the existing codebase into a distributed microservices architecture governed by a centralized API Gateway.

**Business Justification**
The current system suffers from significant technical debt, most notably a 3,000-line "God Class" that conflates authentication, logging, and email dispatch. This fragility creates a high risk of systemic failure; a bug in the email notification logic can inadvertently crash the entire authentication flow. As Deepwell Data seeks to enter the broader food and beverage market, the inability to support multi-tenancy and internationalization is a direct barrier to revenue. Furthermore, because the tool handles sensitive data, maintaining strict HIPAA compliance is non-negotiable to avoid catastrophic legal liabilities and fines.

**ROI Projection**
The primary financial objective of Nexus is the transition from a cost-center (internal tool) to a profit-center (SaaS product). 
1. **Operational Efficiency:** By achieving a 50% reduction in manual processing time for end-users, we estimate an indirect labor saving of $120,000 per year across the internal organization.
2. **Revenue Generation:** With the target of onboarding the first paying customer by June 15, 2025, the projected Year 1 ARR (Annual Recurring Revenue) is estimated at $250,000, based on a tiered subscription model.
3. **Risk Mitigation:** Moving to a microservices architecture reduces the "blast radius" of failures, decreasing downtime-related productivity loss by an estimated 30%.

**Financial Strategy**
The project is currently unfunded. We are bootstrapping the development using existing team capacity. The team consists of Sage Moreau (EM), Noor Jensen (Senior Backend), Aaliya Jensen (Security), and Mosi Liu (Intern). While this minimizes immediate cash outlay, it creates a "capacity risk" where feature development competes with maintenance of other company assets.

---

## 2. Technical Architecture

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Project Nexus utilizes a **Hexagonal Architecture** to decouple the core business logic from external dependencies. This ensures that the core domain—the rules governing food and beverage productivity—remains agnostic of the database (MongoDB), the messaging queue (Celery), or the external API delivery mechanism (FastAPI).

**Core Components:**
- **The Domain:** Contains entities, value objects, and domain services. It is pure Python and has no dependencies on frameworks.
- **Ports:** Interfaces that define how the domain interacts with the outside world (e.g., `IUserRepository`, `INotificationPort`).
- **Adapters:** Concrete implementations of ports. For example, a `MongoUserRepository` implements the `IUserRepository` port to persist data to MongoDB.

### 2.2 Infrastructure Stack
- **Language/Framework:** Python 3.11+ / FastAPI (Asynchronous request handling).
- **Database:** MongoDB 6.0 (Document store for flexible schema evolution).
- **Task Queue:** Celery 5.3 with Redis 7.0 as the broker.
- **Containerization:** Docker Compose for local development and orchestration.
- **Hosting:** Self-hosted on dedicated Ubuntu 22.04 LTS servers within a VPC.
- **Security:** AES-256 encryption at rest; TLS 1.3 for all data in transit.

### 2.3 System Diagram (ASCII Representation)

```text
[ Client (Web/Mobile) ] 
          |
          v (HTTPS / TLS 1.3)
+---------------------------------------+
|            API GATEWAY (Nexus)         | <--- Auth, Rate Limiting, 
+---------------------------------------+      Routing, Feature Flags
          |                 |
          v                 v
+-----------------+   +---------------------+
|  User Service   |   |   Inventory Service |  <--- Microservices
| (FastAPI / Mongo)|   | (FastAPI / Mongo)  |
+-----------------+   +---------------------+
          |                 |
          +--------+--------+
                  |
                  v
        +-------------------+
        |   Celery Worker    | <--- Async Tasks (Emails, Scanning)
        +-------------------+
                  |
                  v
        +-------------------+
        |   Redis Broker    |
        +-------------------+
```

---

## 3. Detailed Feature Specifications

### 3.1 Multi-Tenant Data Isolation (Priority: High | Status: In Progress)
**Requirement:** The system must support multiple organizational entities (tenants) sharing a single set of infrastructure while ensuring that no tenant can ever access another tenant's data.

**Technical Implementation:**
Nexus will employ a **Discriminator Column (TenantID)** strategy within shared MongoDB collections. Every document in the database will contain a `tenant_id` field.
- **Enforcement:** A FastAPI dependency will be implemented as a middleware that extracts the `tenant_id` from the JWT (JSON Web Token) provided in the request header.
- **Query Filtering:** Every database query must pass through a "Tenant Filter" layer. Direct access to the MongoDB driver is forbidden; developers must use the `TenantAwareRepository` which automatically appends `{ "tenant_id": current_tenant_id }` to all find, update, and delete operations.
- **Isolation Leak Prevention:** A specialized integration test suite will attempt to perform "cross-tenant" queries using stolen IDs to ensure a 403 Forbidden response is returned.

### 3.2 User Authentication and RBAC (Priority: Medium | Status: In Progress)
**Requirement:** A robust identity management system that handles user login, session management, and Role-Based Access Control (RBAC) to restrict feature access.

**Technical Implementation:**
- **Authentication:** Implementation of OAuth2 with JWT (JSON Web Tokens). Tokens will be signed using RS256.
- **Role Hierarchy:** The system will support four primary roles: `SuperAdmin` (Global), `OrgAdmin` (Tenant level), `Manager`, and `Staff`.
- **Permission Matrix:** Permissions are mapped to roles. For example, `Staff` can read inventory but cannot modify price lists.
- **RBAC Middleware:** A Python decorator `@require_permission("inventory:write")` will be applied to FastAPI endpoints. If the user's token does not contain the required permission claim, the API Gateway will reject the request before it reaches the microservice.

### 3.3 A/B Testing Framework & Feature Flags (Priority: Critical | Status: Not Started)
**Requirement:** A system to toggle features on/off for specific user segments and run controlled experiments (A/B tests) to validate UI changes. **This is a launch blocker.**

**Technical Implementation:**
- **Feature Flag Store:** A dedicated MongoDB collection `feature_flags` storing the state of flags (Enabled/Disabled) and their targeting rules (e.g., `tenant_id` in [X, Y, Z] or `user_role` == 'Manager').
- **A/B Logic:** The framework will utilize a deterministic hashing algorithm (MurmurHash3) on the `user_id` to assign users to a "Bucket" (Control vs. Treatment).
- **Integration:** The API Gateway will inject the active flag set into the request header as `X-Nexus-Flags`, allowing downstream microservices to behave differently without calling the flag service repeatedly.
- **Evaluation:** The framework must log which user saw which variant to allow for NPS and productivity metric analysis.

### 3.4 Localization and Internationalization (Priority: High | Status: In Design)
**Requirement:** Support for 12 languages to enable global expansion in the food and beverage industry.

**Technical Implementation:**
- **Storage:** Use of the `gettext` standard for static strings. Translation files (.po / .mo) will be stored in the version control system.
- **Dynamic Content:** For database-driven content (e.g., product descriptions), a "Translation Table" approach will be used where each entry has a `language_code` (ISO 639-1).
- **Detection:** The system will determine the user's language via the `Accept-Language` HTTP header, falling back to a user-profile preference, and finally to English (US) as the default.
- **UI Adaptation:** The frontend must support Right-to-Left (RTL) mirroring for languages such as Arabic, ensuring the layout remains functional.

### 3.5 File Upload with Virus Scanning and CDN Distribution (Priority: Medium | Status: In Review)
**Requirement:** Ability for users to upload product images, menus, and compliance documents securely, with automatic malware scanning and fast global delivery.

**Technical Implementation:**
- **Upload Flow:** Files are uploaded to a temporary "Quarantine" S3 bucket.
- **Virus Scanning:** A Celery worker triggers a scan using ClamAV. If a threat is detected, the file is immediately deleted, and the user is notified via a security alert.
- **CDN Integration:** Once cleared, the file is moved to a "Production" bucket and cached via CloudFront.
- **Security:** Files are served via "Signed URLs" with a 15-minute expiration to prevent unauthorized hotlinking and ensure HIPAA-compliant access control.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request:** `{"username": "user@deepwell.com", "password": "securepassword123"}`
- **Response (200 OK):** `{"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}`
- **Response (401 Unauthorized):** `{"error": "Invalid credentials"}`

### 4.2 `GET /tenants/profile`
- **Description:** Retrieves the current tenant's configuration.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** `{"tenant_id": "T-992", "name": "BrewMasters Co", "plan": "Enterprise", "region": "NA-East"}`

### 4.3 `GET /inventory/items`
- **Description:** Lists all inventory items for the authenticated tenant.
- **Query Params:** `category=beverages`, `limit=50`
- **Response (200 OK):** `[{"id": "itm_1", "name": "Arabica Beans", "stock": 500, "unit": "kg"}]`

### 4.4 `POST /inventory/items`
- **Description:** Creates a new inventory item.
- **Request:** `{"name": "Organic Honey", "stock": 20, "unit": "liters", "category": "sweeteners"}`
- **Response (201 Created):** `{"id": "itm_55", "status": "created"}`

### 4.5 `PATCH /inventory/items/{id}`
- **Description:** Updates stock levels.
- **Request:** `{"stock_adjustment": -5}`
- **Response (200 OK):** `{"id": "itm_1", "new_stock": 495}`

### 4.6 `POST /files/upload`
- **Description:** Uploads a file for virus scanning.
- **Request:** Multipart/form-data (File)
- **Response (202 Accepted):** `{"file_id": "file_abc123", "status": "scanning"}`

### 4.7 `GET /files/status/{file_id}`
- **Description:** Checks if a file has passed the virus scan.
- **Response (200 OK):** `{"file_id": "file_abc123", "status": "clean", "url": "https://cdn.nexus.io/..."}`

### 4.8 `GET /admin/flags`
- **Description:** Lists all active feature flags (SuperAdmin only).
- **Response (200 OK):** `[{"flag_name": "new_dashboard_v2", "enabled": true, "percentage": 25}]`

---

## 5. Database Schema (MongoDB)

Since MongoDB is schema-less, the following represent the **required document structures** enforced at the application level via Pydantic models.

### 5.1 `tenants` (Collection)
- `_id`: ObjectId (PK)
- `tenant_name`: String
- `subscription_level`: String (Free, Pro, Enterprise)
- `created_at`: DateTime
- `is_active`: Boolean

### 5.2 `users` (Collection)
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `email`: String (Unique)
- `password_hash`: String
- `role`: String (Staff, Manager, OrgAdmin)
- `mfa_enabled`: Boolean

### 5.3 `permissions` (Collection)
- `_id`: ObjectId (PK)
- `role_name`: String
- `allowed_actions`: Array [String] (e.g., `["inventory:read", "inventory:write"]`)

### 5.4 `inventory_items` (Collection)
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `sku`: String
- `name`: String
- `quantity`: Decimal
- `unit`: String
- `last_updated`: DateTime

### 5.5 `audit_logs` (Collection)
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `action`: String
- `timestamp`: DateTime
- `ip_address`: String

### 5.6 `feature_flags` (Collection)
- `_id`: ObjectId (PK)
- `flag_key`: String (Unique)
- `is_enabled`: Boolean
- `rollout_percentage`: Integer (0-100)
- `target_tenants`: Array [ObjectId]

### 5.7 `translations` (Collection)
- `_id`: ObjectId (PK)
- `key`: String
- `language_code`: String (e.g., "fr-FR")
- `translated_text`: String

### 5.8 `uploaded_files` (Collection)
- `_id`: ObjectId (PK)
- `tenant_id`: ObjectId (FK $\rightarrow$ tenants)
- `original_filename`: String
- `s3_path`: String
- `scan_status`: String (Pending, Clean, Infected)
- `mime_type`: String

### 5.9 `ab_tests` (Collection)
- `_id`: ObjectId (PK)
- `test_name`: String
- `variant_a_config`: JSON
- `variant_b_config`: JSON
- `start_date`: DateTime
- `end_date`: DateTime

### 5.10 `user_sessions` (Collection)
- `_id`: ObjectId (PK)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `session_token`: String
- `expires_at`: DateTime
- `user_agent`: String

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
To maintain HIPAA compliance and system stability, Project Nexus utilizes three distinct environments.

**Development (Dev):**
- **Purpose:** Feature development and unit testing.
- **Data:** Synthetic data only; no real PII (Personally Identifiable Information).
- **Deployment:** Auto-deployed on every commit to the `develop` branch.

**Staging (Staging):**
- **Purpose:** Final QA, integration testing, and UAT (User Acceptance Testing).
- **Data:** Sanitized production snapshots.
- **Deployment:** Manual trigger. This is where the **Manual QA Gate** resides.
- **QA Gate Process:** A 48-hour (2-day) window where Noor Jensen and Aaliya Jensen must sign off on the stability and security of the build.

**Production (Prod):**
- **Purpose:** Live end-user traffic.
- **Data:** Encrypted production data.
- **Deployment:** Manual deployment following Staging sign-off. High-availability configuration with MongoDB Replica Sets.

### 6.2 Deployment Workflow
1. **CI Pipeline:** GitHub Actions runs `pytest` and `flake8`.
2. **Artifact:** Docker image is built and pushed to a private registry.
3. **Staging Deploy:** `docker-compose pull && docker-compose up -d`.
4. **QA Window:** 2-day turnaround for manual verification.
5. **Prod Deploy:** Blue-Green deployment strategy to ensure zero downtime.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Scope:** Domain logic and individual port adapters.
- **Tooling:** `pytest` with `pytest-mock`.
- **Requirement:** 80% code coverage for the `/domain` directory. No network calls allowed in unit tests.

### 7.2 Integration Testing
- **Scope:** Interaction between microservices, API Gateway, and MongoDB.
- **Tooling:** `TestContainers` (running a real MongoDB instance in Docker).
- **Focus:** Testing the `TenantAwareRepository` to ensure no cross-tenant data leakage.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Upload File $\rightarrow$ Update Inventory").
- **Tooling:** Playwright / Pytest.
- **Frequency:** Run against the Staging environment before every production release.

### 7.4 Security Testing
- **Penetration Testing:** Aaliya Jensen will perform quarterly "Chaos Security" tests, attempting to bypass RBAC or inject malicious scripts.
- **Scanning:** Automated dependency scanning using `Snyk` to detect vulnerable Python packages.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Key architect leaving in 3 months | High | High | **Contingency Plan:** Document all architectural decisions in this spec. Create a "Fallback Architecture" utilizing a simpler monolithic approach if microservices prove too complex for the remaining team. |
| **R2** | Team lacks experience with FastAPI/Mongo | High | Medium | **Blocker:** This will be raised at the next board meeting. Action: Allocate 10% of weekly sprint time to "learning spikes" and professional training courses. |
| **R3** | HIPAA compliance breach | Low | Critical | **Rigid Protocol:** All data must be encrypted via AES-256. Aaliya Jensen must review every schema change. |
| **R4** | "God Class" creates regression | High | Medium | **Refactoring Plan:** Slowly carve out functionality from the God Class into the new microservices. Do not rewrite it all at once (Strangler Fig Pattern). |

---

## 9. Timeline

### Phase 1: Foundation (Jan 2024 - May 2025)
- **Jan - Mar:** Refactor God Class, implement API Gateway basics.
- **Apr - May:** Finalize Multi-tenant isolation and RBAC.
- **Dependency:** Completion of Legal review for Data Processing Agreement (DPA).

### Phase 2: Commercial Readiness (May 2025 - June 2025)
- **May:** Implement A/B testing framework (Launch Blocker).
- **June:** Final QA for first customer.
- **Target:** **2025-06-15: First paying customer onboarded.**

### Phase 3: Scaling & Optimization (July 2025 - August 2025)
- **July:** Optimization of MongoDB indexes and Celery worker tuning.
- **August:** Load testing to meet performance benchmarks.
- **Target:** **2025-08-15: Performance benchmarks met.**

### Phase 4: Beta Expansion (Sept 2025 - Oct 2025)
- **Sept:** Localization rollout (12 languages).
- **Oct:** Pilot program onboarding.
- **Target:** **2025-10-15: External beta with 10 pilot users.**

---

## 10. Meeting Notes

### Meeting 1: Architectural Alignment
**Date:** 2023-11-02  
**Attendees:** Sage Moreau, Noor Jensen, Aaliya Jensen, Mosi Liu  
**Discussion:**
- Noor expressed concern regarding the "God Class." It currently handles `Auth`, `Logging`, and `SMTP` logic in one 3,000-line file.
- Sage proposed the Hexagonal Architecture to prevent this from happening in the new services.
- Aaliya insisted that the API Gateway must be the only entry point to ensure HIPAA-compliant logging of all access.
**Action Items:**
- [Noor] Create a map of all dependencies within the God Class. (Due: 2023-11-09)
- [Sage] Draft the initial API Gateway routing table. (Due: 2023-11-09)

### Meeting 2: Security & HIPAA Compliance
**Date:** 2023-11-15  
**Attendees:** Sage Moreau, Aaliya Jensen  
**Discussion:**
- Aaliya noted that the current "bootstrapping" approach means we are using a shared Redis instance for both caching and Celery. This is a security risk if tenant data is cached.
- Decision: Move to separate Redis instances for the Production environment.
- Discussion on the Data Processing Agreement (DPA) blocker. Legal has not yet signed off on the third-party CDN usage.
**Action Items:**
- [Aaliya] Update the infrastructure YAML to include separate Redis containers. (Due: 2023-11-20)
- [Sage] Email Legal to expedite the DPA review. (Due: Immediate)

### Meeting 3: A/B Testing & Launch Blockers
**Date:** 2023-12-01  
**Attendees:** Sage Moreau, Noor Jensen, Mosi Liu  
**Discussion:**
- Mosi presented a prototype for the A/B testing framework. It uses a simple random split.
- Noor argued that randomness is insufficient; we need "sticky" assignments so a user doesn't see Version A on mobile and Version B on desktop.
- Decision: Implement MurmurHash3 on `user_id` to ensure deterministic bucket assignment.
- Sage reminded the team that this feature is a **launch blocker** for the June milestone.
**Action Items:**
- [Mosi] Implement the hashing logic in the Feature Flag service. (Due: 2023-12-15)
- [Noor] Review the performance impact of the hashing on the API Gateway. (Due: 2023-12-20)

---

## 11. Budget Breakdown

As the project is bootstrapping with existing team capacity, the budget focuses on infrastructure and tool overhead rather than new salaries.

| Category | Item | Estimated Annual Cost | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Internal Team Capacity | $0.00 (Absorbed) | 4 FTEs working on existing salaries. |
| **Infrastructure** | Self-Hosted Servers | $4,800 | 3x High-spec Ubuntu nodes + Backups. |
| **Infrastructure** | S3 / CloudFront | $2,400 | CDN for file distribution. |
| **Tools** | MongoDB Atlas (Backup) | $1,200 | Managed backup for disaster recovery. |
| **Tools** | Snyk / Security Scanning | $600 | Annual subscription for vulnerability scans. |
| **Contingency** | Emergency Hardware | $2,000 | Buffer for server failure/replacement. |
| **Total** | | **$11,000** | |

---

## 12. Appendices

### Appendix A: The "God Class" Refactor Map
The existing `CoreManager` class (3,000 lines) will be decomposed as follows:
- `CoreManager.authenticate()` $\rightarrow$ `UserService.auth`
- `CoreManager.send_email()` $\rightarrow$ `NotificationService.dispatch`
- `CoreManager.log_event()` $\rightarrow$ `AuditService.record`
- `CoreManager.validate_session()` $\rightarrow$ `APIGateway.middleware`

### Appendix B: HIPAA Encryption Standards
To maintain compliance, the following standards are enforced:
1. **At Rest:** All MongoDB volumes are encrypted using LUKS (Linux Unified Key Setup) with AES-256.
2. **In Transit:** All internal service-to-service communication occurs over a private virtual network (VPC) using mTLS (Mutual TLS).
3. **Key Management:** Encryption keys are rotated every 90 days and stored in a secure, vaulted environment separate from the application servers.