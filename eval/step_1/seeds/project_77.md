# PROJECT SPECIFICATION: PROJECT QUORUM
**Document Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 26, 2025  
**Classification:** Confidential – Internal Use Only  
**Company:** Bridgewater Dynamics  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Quorum is a mission-critical fintech payment processing system developed by Bridgewater Dynamics. The primary objective is to facilitate secure, scalable, and compliant financial transactions specifically tailored for the renewable energy sector. The renewable energy market is currently experiencing rapid expansion, necessitating a robust system capable of handling high-volume subsidies, carbon credit settlements, and equipment procurement payments.

### 1.2 Business Justification
The project is driven by an urgent regulatory compliance mandate. New federal and international laws regarding the transparency of green energy financing require all transactional data to be audit-ready and securely stored. Failure to implement this system by the hard legal deadline (6 months from project initiation) would expose Bridgewater Dynamics to catastrophic legal liabilities, potential loss of operating licenses in key jurisdictions, and fines exceeding $12.5M per quarter of non-compliance.

### 1.3 ROI Projection
While the primary driver is compliance (risk mitigation), Quorum is projected to generate significant operational ROI:
- **Operational Efficiency:** Automation of settlement processes is expected to reduce manual reconciliation labor by 65%, saving an estimated $1.2M annually in administrative overhead.
- **Transaction Speed:** Transitioning from legacy batch processing to a Go-based microservices architecture will reduce settlement latency from 48 hours to near real-time (< 2 seconds).
- **Market Penetration:** The ability to offer multi-tenant data isolation allows Bridgewater Dynamics to act as a payment processor for third-party energy startups, opening a new B2B revenue stream projected at $4.5M in Year 1.

### 1.4 Strategic Alignment
Quorum aligns with Bridgewater Dynamics’ goal of becoming the "financial backbone" of the renewable energy transition. By ensuring HIPAA-level security (extending health-grade privacy to financial data) and leveraging a distributed database, the system ensures high availability (99.999%) across global energy grids.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy: Hexagonal Architecture
Quorum utilizes **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external dependencies. This is critical given the volatility of integration partners in the fintech space.

- **The Core:** Contains the pure domain logic (e.g., payment validation, currency conversion, compliance checks). It has no knowledge of databases or APIs.
- **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `PaymentRepository` interface).
- **Adapters:** Concrete implementations of ports (e.g., `CockroachDBAdapter` for persistence, `gRPCAdapter` for communication).

### 2.2 Technical Stack
- **Language:** Go (Golang) 1.21+ for high-concurrency performance.
- **Communication:** gRPC with Protocol Buffers (proto3) for low-latency inter-service communication.
- **Database:** CockroachDB (Distributed SQL) for strong consistency and global scalability.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
- **Security:** AES-256 encryption at rest; TLS 1.3 in transit; HIPAA-compliant data masking.

### 2.3 System Diagram (ASCII Description)
```text
[ External Clients ] <--> [ GCP Load Balancer ] <--> [ GKE Ingress ]
                                                          |
                                            ______________________________|______________________________
                                           |                              |                              |
                                   [ Auth Service ]               [ Payment Service ]             [ Tenant Service ]
                                           |                              |                              |
                                    (Port: AuthRepo)              (Port: PaymentRepo)             (Port: TenantRepo)
                                           |                              |                              |
                                   (Adapter: CockroachDB)         (Adapter: CockroachDB)            (Adapter: CockroachDB)
                                           |______________________________|______________________________|
                                                                          |
                                                                  [ CockroachDB Cluster ]
                                                                  (Multi-Region Deployment)
```

### 2.4 Data Flow
1. A request hits the GCP Load Balancer.
2. The gRPC gateway validates the JWT via the **Auth Service**.
3. The **Payment Service** processes the transaction logic using the Hexagonal core.
4. State is persisted in **CockroachDB**, ensuring atomic commits across regions.
5. Every PR merged to the `main` branch triggers a Jenkins pipeline that deploys to Production via a Canary strategy.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
- **Priority:** Critical (Launch Blocker)
- **Status:** In Design
- **Description:** 
A comprehensive identity management system ensuring that only authorized personnel can initiate, approve, or audit payments. Given the regulatory nature of Quorum, "Least Privilege" is the governing principle.

**Functional Requirements:**
- **Identity Provider:** Integration with an OIDC provider.
- **Role Hierarchy:** 
    - `SuperAdmin`: Full system access, tenant creation.
    - `ComplianceOfficer`: Read-only access to all transactions, audit log export.
    - `PaymentOperator`: Ability to initiate payments; cannot approve own payments (Four-Eyes Principle).
    - `Approver`: Ability to authorize payments above $10,000.
- **Session Management:** Stateless JWTs with short expiration (15 mins) and sliding window refresh tokens.
- **Audit Trail:** Every authentication attempt and privilege escalation must be logged with a timestamp, IP address, and device fingerprint.

**Technical Implementation:**
The Auth service will implement a middleware wrapper for all gRPC calls. The RBAC logic will be stored in a `roles` and `permissions` table in CockroachDB, cached in Redis for performance.

---

### 3.2 Multi-Tenant Data Isolation
- **Priority:** Medium
- **Status:** Not Started
- **Description:** 
To support various renewable energy firms, Quorum must isolate data so that Company A cannot see Company B's transactions, even though they share the same physical database infrastructure.

**Functional Requirements:**
- **Logical Isolation:** Use of a `tenant_id` column on every table.
- **Row-Level Security (RLS):** Implementation of CockroachDB policies to ensure queries automatically filter by the active `tenant_id`.
- **Tenant Onboarding:** A streamlined process for the `SuperAdmin` to create a new tenant, assign a quota, and set up a dedicated encryption key.
- **Custom Branding:** Ability for tenants to define their own payment portal labels and logos.

**Technical Implementation:**
Every request must carry a `X-Tenant-ID` header. The `TenantService` will validate this ID against the authenticated user's profile. The database adapter will inject the `tenant_id` into every `WHERE` clause via a Go interceptor to prevent "cross-tenant leak" bugs.

---

### 3.3 Offline-First Mode with Background Sync
- **Priority:** Low (Nice to Have)
- **Status:** In Design
- **Description:** 
Field engineers at remote solar farms often lack stable internet. This feature allows them to record payment triggers or equipment receipts offline.

**Functional Requirements:**
- **Local Storage:** Use of IndexedDB in the frontend to queue transactions.
- **Conflict Resolution:** "Last Write Wins" (LWW) strategy for metadata, but "Strict Sequential" for financial transactions to prevent double-spending.
- **Sync Queue:** A background worker that polls for connectivity and flushes the queue via gRPC streaming.
- **State Indicator:** A visual cue (Green/Yellow/Red) showing the sync status of the local cache.

**Technical Implementation:**
The frontend will implement a "Outbox Pattern." Transactions are written to a local `pending_sync` table. Upon reconnection, the client sends a batch request. The server assigns a global sequence number to resolve temporal conflicts.

---

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
- **Priority:** Low (Nice to Have)
- **Status:** Blocked
- **Description:** 
Compliance officers need to find specific transactions across millions of records using complex criteria (e.g., "All payments between $50k and $100k in the wind sector during Q3").

**Functional Requirements:**
- **Full-Text Search:** Ability to search by invoice IDs, vendor names, or internal notes.
- **Facets:** Sidebar filters for Date Range, Currency, Status (Pending/Paid/Failed), and Tenant.
- **Indexing:** High-performance indexing to ensure search results return in < 500ms.

**Technical Implementation:**
Due to the scale, we will implement an ELK stack (Elasticsearch, Logstash, Kibana) or use CockroachDB's inverted indexes. This is currently blocked pending the delivery of the "Data Export Module" from the external integration team.

---

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
- **Priority:** Low (Nice to Have)
- **Status:** Not Started
- **Description:** 
High-value transactions (>$1M) require a secondary layer of authentication beyond passwords.

**Functional Requirements:**
- **TOTP Support:** Integration with Google Authenticator/Authy.
- **WebAuthn/FIDO2:** Support for physical keys like YubiKeys.
- **Recovery Codes:** Generation of 10 single-use recovery codes during setup.
- **Step-up Authentication:** Triggering a 2FA prompt specifically when a "Critical" action is taken, even if the user is already logged in.

**Technical Implementation:**
The Auth service will be extended to include a `mfa_methods` table. For hardware keys, the system will implement the WebAuthn challenge-response flow.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are served via gRPC; however, they are exposed through a REST Gateway for frontend compatibility. Base URL: `https://api.quorum.bridgewater.io/v1`

### 4.1 `POST /auth/login`
- **Purpose:** Authenticate user and return JWT.
- **Request:**
  ```json
  {
    "email": "user@bridgewater.com",
    "password": "hashed_password",
    "mfa_token": "123456" 
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "token": "eyJhbG...",
    "expires_at": "2026-04-15T12:00:00Z",
    "role": "PaymentOperator"
  }
  ```

### 4.2 `POST /payments/initiate`
- **Purpose:** Create a new payment request.
- **Request:**
  ```json
  {
    "amount": 15000.00,
    "currency": "USD",
    "recipient_id": "vendor_99",
    "tenant_id": "tenant_alpha",
    "description": "Solar Panel Batch #4"
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "payment_id": "pay_887766",
    "status": "PENDING_APPROVAL",
    "estimated_settlement": "2026-04-18"
  }
  ```

### 4.3 `PATCH /payments/{id}/approve`
- **Purpose:** Approve a pending payment (Requires `Approver` role).
- **Request:**
  ```json
  {
    "approver_id": "user_123",
    "notes": "Verified against invoice #44"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "payment_id": "pay_887766",
    "status": "AUTHORIZED"
  }
  ```

### 4.4 `GET /tenants/{id}/balance`
- **Purpose:** Retrieve current balance for a specific tenant.
- **Response:** `200 OK`
  ```json
  {
    "tenant_id": "tenant_alpha",
    "available_funds": 1250000.00,
    "currency": "USD"
  }
  ```

### 4.5 `GET /audit/logs`
- **Purpose:** Stream audit logs for compliance.
- **Params:** `?start_date=2026-01-01&end_date=2026-01-31`
- **Response:** `200 OK`
  ```json
  [
    {"timestamp": "...", "user": "user_1", "action": "PAYMENT_INIT", "target": "pay_887766"}
  ]
  ```

### 4.6 `POST /tenants/create`
- **Purpose:** Initialize a new multi-tenant environment.
- **Request:**
  ```json
  {
    "company_name": "EcoWind Ltd",
    "contact_email": "admin@ecowind.com",
    "region": "EU-West-1"
  }
  ```
- **Response:** `201 Created`
  ```json
  { "tenant_id": "tenant_beta", "api_key": "sk_live_..." }
  ```

### 4.7 `GET /search/payments`
- **Purpose:** Faceted search for transactions.
- **Params:** `?q=solar&min_amount=1000&status=PAID`
- **Response:** `200 OK`
  ```json
  {
    "results": [...],
    "facets": { "status": { "PAID": 150, "PENDING": 20 } }
  }
  ```

### 4.8 `DELETE /auth/logout`
- **Purpose:** Invalidate the current session token.
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

Quorum uses **CockroachDB** with a distributed schema. All tables use `UUID` as primary keys for global uniqueness.

### 5.1 Table Definitions

1. **`tenants`**
   - `tenant_id` (UUID, PK)
   - `name` (String)
   - `created_at` (Timestamp)
   - `status` (Enum: ACTIVE, SUSPENDED)
   - `encryption_key_id` (String)

2. **`users`**
   - `user_id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants)
   - `email` (String, Unique)
   - `password_hash` (String)
   - `mfa_secret` (String, Encrypted)
   - `last_login` (Timestamp)

3. **`roles`**
   - `role_id` (UUID, PK)
   - `role_name` (String, Unique) - e.g., "SuperAdmin"
   - `description` (Text)

4. **`user_roles`**
   - `user_id` (UUID, FK -> users)
   - `role_id` (UUID, FK -> roles)
   - `assigned_at` (Timestamp)

5. **`payments`**
   - `payment_id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants)
   - `amount` (Decimal 19,4)
   - `currency` (String 3)
   - `status` (Enum: PENDING, AUTHORIZED, PAID, FAILED)
   - `creator_id` (UUID, FK -> users)
   - `approver_id` (UUID, FK -> users)
   - `created_at` (Timestamp)
   - `updated_at` (Timestamp)

6. **`payment_audit_trail`**
   - `audit_id` (UUID, PK)
   - `payment_id` (UUID, FK -> payments)
   - `action` (String)
   - `user_id` (UUID, FK -> users)
   - `previous_state` (JSONB)
   - `new_state` (JSONB)
   - `timestamp` (Timestamp)

7. **`vendors`**
   - `vendor_id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants)
   - `legal_name` (String)
   - `tax_id` (String)
   - `bank_account_encrypted` (Text)

8. **`currency_exchange_rates`**
   - `pair` (String, PK) - e.g., "USD/EUR"
   - `rate` (Decimal 19,9)
   - `last_updated` (Timestamp)

9. **`api_keys`**
   - `key_id` (UUID, PK)
   - `tenant_id` (UUID, FK -> tenants)
   - `key_hash` (String)
   - `scopes` (Array)
   - `expires_at` (Timestamp)

10. **`system_configs`**
    - `config_key` (String, PK)
    - `config_value` (String)
    - `environment` (String) - e.g., "PROD", "STAGING"

### 5.2 Relationships
- **Tenants 1:N Users**: One tenant has many users.
- **Tenants 1:N Payments**: One tenant has many transactions.
- **Users N:M Roles**: Users can have multiple roles through `user_roles`.
- **Payments 1:N AuditTrail**: Every payment change generates a new audit log.
- **Tenants 1:N Vendors**: Vendors are associated with the tenant that hires them.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Bridgewater Dynamics employs a **Continuous Deployment (CD)** model. Every merged PR to the `main` branch is automatically deployed to production after passing a rigorous test suite.

#### 6.1.1 Development (Dev)
- **Purpose:** Sandbox for solo developer and team experimentation.
- **Infrastructure:** Small GKE cluster (3 nodes), single-node CockroachDB.
- **CI/CD:** Triggered by every commit to `feature/*` branches.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
- **Infrastructure:** Mirrors Production (3-node cluster), multi-region CockroachDB.
- **CI/CD:** Triggered by merges to the `develop` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live regulatory processing.
- **Infrastructure:** High-availability GKE cluster across 3 GCP regions (us-east1, europe-west1, asia-east1).
- **CI/CD:** Triggered by merges to `main`. Uses Canary releases (10% traffic $\rightarrow$ 50% $\rightarrow$ 100%).

### 6.2 Infrastructure as Code (IaC)
Terraform is used to manage all GCP resources. All configuration values (previously hardcoded) are being migrated to **Google Secret Manager** and **ConfigMaps**.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing (The Foundation)
- **Scope:** Core domain logic in the Hexagonal center.
- **Target:** 90% code coverage.
- **Tooling:** `go test`, `testify`.
- **Approach:** Mocking ports (interfaces) to isolate business logic from the database.

### 7.2 Integration Testing
- **Scope:** Interaction between services and the database.
- **Target:** All API endpoints and gRPC calls.
- **Tooling:** Docker Compose to spin up a local CockroachDB instance.
- **Approach:** "Black box" testing of the Adapters to ensure the DB schema matches the code expectations.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Initiate Payment $\rightarrow$ Approve Payment").
- **Tooling:** Playwright (Frontend) and Postman/Newman (API).
- **Approach:** Deployed in the Staging environment. Tests run against a mirrored production dataset.

### 7.4 Security Testing
- **Penetration Testing:** Quarterly external audits.
- **Static Analysis:** `gosec` and `SonarQube` integrated into the CI pipeline to catch vulnerabilities before merge.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R1** | Project sponsor rotation | High | High | Escalate to steering committee for funding guarantee. | Rafik Liu |
| **R2** | Integration API is buggy/undocumented | High | Medium | Assign dedicated owner to reverse-engineer and document. | Bodhi Kim |
| **R3** | Hardcoded configs in 40+ files | Medium | Low | Systematic migration to Secret Manager in Sprint 4. | Solo Dev |
| **R4** | Regulatory deadline miss | Low | Critical | Strict adherence to milestone dates; cut "Nice-to-Have" features. | Rafik Liu |
| **R5** | Team trust/cohesion issues | Medium | Medium | Weekly syncs; iterative wins to build confidence. | All |

### 8.1 Probability/Impact Matrix
- **High/High:** Immediate action required. (Sponsor Rotation)
- **High/Medium:** Monitor closely. (Integration API)
- **Medium/Low:** Schedule for future sprints. (Tech Debt)

---

## 9. TIMELINE AND PHASES

The project has a strict 6-month window. The timeline is broken into four primary phases.

### 9.1 Phase 1: Foundation (Month 1-2)
- **Focus:** Infrastructure setup, Auth Service, and Core Payment logic.
- **Dependencies:** GKE cluster provisioning.
- **Key Milestone:** **Internal Alpha Release (2026-04-15)**.
- **Deliverables:** Basic login, payment initiation, and database schema baseline.

### 9.2 Phase 2: Compliance & Hardening (Month 3-4)
- **Focus:** RBAC, Multi-tenancy, and HIPAA encryption.
- **Dependencies:** Completion of Auth Service.
- **Key Milestone:** **Architecture Review Complete (2026-06-15)**.
- **Deliverables:** Role-based access, tenant isolation, encrypted storage.

### 9.3 Phase 3: Optimization & Scaling (Month 5)
- **Focus:** Performance tuning, gRPC optimization, and load testing.
- **Dependencies:** Stable internal alpha.
- **Key Milestone:** **Performance Benchmarks Met (2026-08-15)**.
- **Deliverables:** < 2s settlement time, 99.99% availability.

### 9.4 Phase 4: Final Audit & Go-Live (Month 6)
- **Focus:** E2E testing, final regulatory audit, and production cutover.
- **Dependencies:** All previous phases.
- **Deliverables:** Fully compliant payment system live in production.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per team dynamic, formal notes are not kept. The following are curated summaries of key decision threads in the `#project-quorum-core` Slack channel.*

### 10.1 Thread: "The Integration Nightmare" (2025-11-12)
- **Participants:** Rafik, Bodhi
- **Discussion:** Bodhi reported that the external payment partner's API returns `500 Internal Server Error` for 15% of valid requests and lacks a sandbox environment.
- **Decision:** Rafik decided that Bodhi will act as the "Dedicated API Owner." Bodhi will create a wrapper service that implements aggressive retries and a circuit breaker to insulate the Quorum core from the partner's instability.

### 10.2 Thread: "Multi-tenancy vs. Performance" (2025-12-05)
- **Participants:** Rafik, Thiago, Orla
- **Discussion:** Orla raised concerns that the faceted search might be slow if `tenant_id` is not indexed correctly. Thiago suggested separate databases per tenant.
- **Decision:** Rafik rejected separate DBs due to maintenance overhead. Decision made to use a single shared CockroachDB cluster with strict Row-Level Security (RLS) and composite indexes on `(tenant_id, created_at)`.

### 10.3 Thread: "The Hardcoded Config Crisis" (2026-01-20)
- **Participants:** Solo Dev, Rafik
- **Discussion:** The developer noted that during the alpha rush, API keys and DB strings were hardcoded in 42 files. This is a major security risk.
- **Decision:** Rafik prioritized a "Cleanup Sprint." All hardcoded values must be moved to GCP Secret Manager before the Architecture Review (Milestone 2).

---

## 11. BUDGET BREAKDOWN

Budget is variable and released in tranches based on the achievement of milestones. Total projected budget: **$2,400,000**.

| Category | Allocated Amount | Details | Funding Tranche |
| :--- | :--- | :--- | :--- |
| **Personnel** | $1,500,000 | Solo Dev (Senior), Contractor (Bodhi), UX/Lead overhead. | Split across 3 Milestones |
| **Infrastructure** | $400,000 | GCP (GKE, Cloud SQL, Secret Manager, Logging). | Monthly Opex |
| **Tools/Licensing** | $150,000 | CockroachDB Enterprise, SonarQube, Playwright Cloud. | Upfront |
| **Contingency** | $350,000 | Buffer for regulatory changes or partner failure. | Released upon request |

**Funding Trigger:**
- Tranche 1 (30%): Upon Internal Alpha (2026-04-15)
- Tranche 2 (40%): Upon Architecture Review (2026-06-15)
- Tranche 3 (30%): Upon Performance Benchmarks (2026-08-15)

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Mapping
Since Quorum requires HIPAA-level security for its financial data:
- **Access Control:** Implemented via RBAC and OIDC.
- **Audit Controls:** Every change to a payment record is stored in `payment_audit_trail` with an immutable timestamp.
- **Integrity:** SHA-256 hashing used for verifying data consistency.
- **Transmission Security:** All gRPC calls use mTLS (mutual TLS) with certificates rotated every 30 days.

### Appendix B: Performance Benchmarks
To meet Milestone 3, the system must adhere to the following:
- **P99 Latency:** Payment initiation request $\rightarrow$ response in $< 200ms$.
- **Throughput:** Ability to process 5,000 transactions per second (TPS) without degradation.
- **Recovery Time Objective (RTO):** $< 15$ minutes in case of a regional GCP outage.
- **Recovery Point Objective (RPO):** $0$ seconds (Zero data loss due to CockroachDB's synchronous replication).