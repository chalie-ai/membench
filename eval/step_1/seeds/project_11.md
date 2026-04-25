Due to the extreme length requirements (6,000–8,000 words), this document is presented as a comprehensive, high-fidelity Technical Specification Document (TSD). It is structured to serve as the "Single Source of Truth" for the development team at Coral Reef Solutions.

***

# PROJECT CITADEL: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Draft/Active  
**Last Updated:** October 24, 2023  
**Owner:** Anouk Moreau (Tech Lead)  
**Confidentiality Level:** Internal / High (SOC 2 Bound)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project Citadel represents the strategic modernization of Coral Reef Solutions' IoT device network. As the company scales within the real estate sector, the legacy monolithic architecture—originally designed for a smaller set of managed properties—has reached its operational limit. Citadel is the initiative to decompose this monolith into a distributed microservices architecture over an 18-month transition period. 

The primary objective is to transition from a "single-server" mentality to a cloud-native, event-driven ecosystem capable of managing tens of thousands of IoT sensors (temperature, humidity, occupancy, and security) across high-density commercial real estate portfolios.

### 1.2 Business Justification
The current system suffers from "scaling fragility." A failure in the reporting module can crash the entire device heartbeat listener, leading to data gaps that violate Service Level Agreements (SLAs) with enterprise clients. By moving to a microservices architecture, Coral Reef Solutions isolates failures and allows independent scaling of high-load components (such as the device ingestion engine) without scaling the entire platform.

Furthermore, the real estate market is shifting toward "Smart Building" certifications (LEED, WELL). To maintain a competitive edge, Citadel introduces a high-performance, customer-facing API that allows third-party property management software to integrate directly with Coral Reef’s hardware.

### 1.3 ROI Projection
The $3M investment is projected to yield a significant return based on three pillars:
1. **Operational Efficiency:** Reducing the time to onboard a new property from 14 days to 48 hours through automated provisioning.
2. **Customer Acquisition:** The introduction of the Sandbox API environment is expected to increase the B2B sales pipeline by 25% by allowing prospective clients to test integrations before signing contracts.
3. **Risk Mitigation:** Avoiding the catastrophic cost of data loss or breach. With SOC 2 Type II compliance, Coral Reef Solutions can move up-market to Fortune 500 tenants who require strict security audits.

**Financial Projection:**
- **Year 1 (Investment):** -$3,000,000 (Capex/Opex)
- **Year 2 (Realized Gains):** +$1,200,000 (Reduced churn, new enterprise contracts)
- **Year 3 (Realized Gains):** +$2,500,000 (Scale efficiency and API monetization)
- **Break-even Point:** Month 30 post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
- **Frontend/BFF:** Next.js (TypeScript) deployed on Vercel.
- **Backend Services:** TypeScript (Node.js) using a microservices pattern.
- **ORM:** Prisma.
- **Database:** PostgreSQL (Managed via AWS RDS for production).
- **Event Bus:** Apache Kafka (for Event Sourcing and CQRS).
- **Deployment:** Vercel (Frontend/API) and Docker/K8s (Core Services).

### 2.2 CQRS and Event Sourcing
To meet the stringent requirements for audit trails in real estate (where changes to lock access or temperature limits must be legally defensible), Citadel implements **Command Query Responsibility Segregation (CQRS)**.

- **Command Side:** Handles state changes (e.g., `UpdateDeviceThreshold`). It validates the command and writes an event to the Event Store.
- **Event Store:** A PostgreSQL-backed immutable log of every state change.
- **Query Side:** Projections are built from the Event Store into read-optimized tables for the UI to consume via Next.js.

### 2.3 ASCII Architecture Diagram
```text
[IoT Devices] ----> [MQTT Broker] ----> [Ingestion Service] 
                                              |
                                              v
[Client UI] <---- [Vercel/Next.js] <---- [Read Model (Postgres)]
                                              ^
                                              | (Event Projection)
                                              |
[Command API] ----> [Validation] ----> [Event Store (Postgres)]
                                              |
                                              v
                                     [Audit Log / Cold Storage]
                                     (Tamper-Evident Storage)
```

### 2.4 Deployment Strategy
Citadel utilizes a **Continuous Deployment (CD)** pipeline. Every merged Pull Request (PR) into the `main` branch is automatically deployed to production via Vercel and GitHub Actions. To mitigate risk, we employ:
- **Feature Flags:** All new features are wrapped in flags.
- **Canary Releases:** Traffic is shifted incrementally to new service versions.
- **Automated Rollbacks:** Triggered by a spike in 5xx errors in the Vercel logs.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox
**Priority:** Medium | **Status:** In Design
**Description:**
A public-facing REST API that allows external developers (clients) to programmatically interact with their IoT device network. The API must be versioned to ensure backward compatibility as the platform evolves.

**Detailed Specifications:**
- **Versioning:** We will use URI versioning (e.g., `/v1/devices`, `/v2/devices`). Deprecation of a version requires a 6-month notice period.
- **Sandbox Environment:** A mirrored environment (`sandbox-api.citadel.coralreef.io`) where clients can perform "dry-run" requests. This environment uses a mock database and does not trigger physical device actions.
- **Authentication:** API Key based authentication with rotating secrets.
- **Documentation:** Auto-generated OpenAPI (Swagger) documentation integrated into the developer portal.
- **Rate Limiting Logic:** Tied to the client's subscription tier (e.g., Gold: 1000 req/min, Silver: 100 req/min).

**Success Criteria:** A developer can successfully authenticate and retrieve a device list in the sandbox within 15 minutes of account creation.

### 3.2 SSO Integration (SAML and OIDC)
**Priority:** Low | **Status:** Not Started
**Description:**
Integration of Single Sign-On (SSO) to allow enterprise clients to manage their users via their own identity providers (Okta, Azure AD, Google Workspace).

**Detailed Specifications:**
- **Protocols:** Support for SAML 2.0 and OpenID Connect (OIDC).
- **User Provisioning:** Just-in-Time (JIT) provisioning will be used to create user profiles in the Citadel database upon the first successful SSO login.
- **Mapping:** Custom attribute mapping to allow clients to map "Group: Admin" in Azure AD to "Role: SuperUser" in Citadel.
- **Fallback:** Standard email/password login remains available for small-scale users.
- **Session Management:** JWT-based sessions with a 12-hour expiration and refresh token rotation.

**Success Criteria:** Users can log in using a corporate Okta account without creating a separate Citadel password.

### 3.3 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** Blocked
**Description:**
A middleware layer to protect the infrastructure from DDoS attacks and "noisy neighbors" by enforcing request quotas and providing transparency on usage.

**Detailed Specifications:**
- **Mechanism:** Sliding window counter implemented via Redis.
- **Headers:** Every response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Pipeline:** Every API call is logged as a lightweight event to a ClickHouse database for real-time usage analytics.
- **Alerting:** Automated alerts when a client hits 80% of their monthly quota.
- **Granularity:** Limiting is applied per API Key, per endpoint.

**Current Blocker:** The Redis cluster configuration is pending a security review by the infrastructure team; until approved, the rate-limiter cannot be deployed to staging.

**Success Criteria:** The system successfully drops requests (429 Too Many Requests) when the threshold is exceeded.

### 3.4 A/B Testing Framework (Feature Flagged)
**Priority:** Low | **Status:** In Progress
**Description:**
A system to roll out features to a subset of users to measure performance and engagement before a full release.

**Detailed Specifications:**
- **Integration:** Baked into the existing feature flag system (LaunchDarkly or custom internal tool).
- **Bucket Logic:** Users are hashed by `userId` into buckets (A, B, or Control) to ensure consistent experience across sessions.
- **Metrics Tracking:** Integration with the analytics pipeline to track conversion rates (e.g., "Does the new dashboard layout lead to fewer support tickets?").
- **Dynamic Config:** Flags can be toggled in real-time without a code redeploy.
- **Clean-up Process:** Each A/B test must have a "sunset date" to ensure technical debt (dead code branches) is removed.

**Success Criteria:** Ability to serve two different UI layouts to two different groups of 5% of users.

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** Blocked
**Description:**
A non-repudiable log of all administrative actions within the system, ensuring that no record can be altered or deleted without detection.

**Detailed Specifications:**
- **Immutability:** Use of a Write-Once-Read-Many (WORM) storage strategy.
- **Cryptographic Chaining:** Each log entry contains a SHA-256 hash of the previous entry, creating a blockchain-like chain of custody.
- **Storage:** Logs are mirrored to an AWS S3 bucket with "Object Lock" enabled.
- **Coverage:** Every change to device configuration, user permissions, or security settings must trigger an audit event.
- **Verification Tool:** A utility to periodically re-calculate hashes to verify that the log has not been tampered with.

**Current Blocker:** The medical leave of the lead security architect has delayed the finalization of the hashing algorithm and the S3 bucket policy.

**Success Criteria:** A successful audit where a modified log entry is detected as "corrupt" by the verification tool.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the pattern: `https://api.citadel.coralreef.io/v1/...`

### 4.1 `GET /devices`
**Description:** Retrieve a list of all IoT devices associated with the authenticated account.
- **Request Params:** `?status=online`, `?limit=50`, `?offset=0`
- **Response (200 OK):**
```json
{
  "data": [
    { "id": "dev_123", "type": "thermometer", "status": "online", "last_seen": "2023-10-24T10:00Z" }
  ],
  "pagination": { "total": 145, "next": "/v1/devices?offset=50" }
}
```

### 4.2 `POST /devices/{id}/command`
**Description:** Send a command to a specific device (e.g., change temperature).
- **Request Body:**
```json
{
  "action": "set_temperature",
  "value": 22.5,
  "unit": "celsius"
}
```
- **Response (202 Accepted):**
```json
{ "job_id": "job_abc_987", "status": "queued" }
```

### 4.3 `GET /devices/{id}/telemetry`
**Description:** Retrieve historical sensor data for a device.
- **Request Params:** `?start=2023-10-01&end=2023-10-15`
- **Response (200 OK):**
```json
{
  "deviceId": "dev_123",
  "readings": [
    { "timestamp": "2023-10-01T12:00Z", "value": 21.1 },
    { "timestamp": "2023-10-01T12:15Z", "value": 21.3 }
  ]
}
```

### 4.4 `PATCH /devices/{id}`
**Description:** Update device metadata (e.g., room name, building floor).
- **Request Body:**
```json
{ "room_name": "Conference Room B", "floor": 4 }
```
- **Response (200 OK):**
```json
{ "id": "dev_123", "updated_at": "2023-10-24T11:00Z" }
```

### 4.5 `GET /audit/logs`
**Description:** Retrieve the tamper-evident audit trail.
- **Request Params:** `?userId=user_456`, `?severity=critical`
- **Response (200 OK):**
```json
{
  "logs": [
    { "eventId": "evt_001", "timestamp": "...", "action": "USER_PERMISSION_CHANGE", "hash": "a1b2c3d4..." }
  ]
}
```

### 4.6 `POST /auth/sso/initiate`
**Description:** Initiate the SAML/OIDC handshake.
- **Request Body:** `{ "provider": "okta", "tenantId": "tenant_789" }`
- **Response (302 Redirect):** Redirects user to the Identity Provider (IdP).

### 4.7 `GET /analytics/usage`
**Description:** Retrieve API usage statistics for the current billing cycle.
- **Response (200 OK):**
```json
{
  "total_requests": 45000,
  "quota_limit": 100000,
  "percent_used": 45.0
}
```

### 4.8 `POST /sandbox/reset`
**Description:** Reset the sandbox environment to a clean state.
- **Response (200 OK):**
```json
{ "status": "reset_complete", "timestamp": "2023-10-24T12:00Z" }
```

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL with Prisma ORM. The schema is designed to support the CQRS pattern by separating the "Event Store" from the "Current State" (Read Model).

### 5.1 Table Definitions

1.  **`Users`**
    - `id` (UUID, PK): Unique identifier.
    - `email` (String, Unique): User's email.
    - `password_hash` (String): Hashed password.
    - `role` (Enum): ADMIN, MANAGER, VIEWER.
    - `sso_provider` (String, Nullable): 'okta', 'azure', etc.
    - `created_at` (DateTime).

2.  **`Organizations`** (The Real Estate Firm/Client)
    - `id` (UUID, PK): Unique identifier.
    - `name` (String): Legal name of the entity.
    - `tier` (Enum): GOLD, SILVER, BRONZE.
    - `billing_email` (String).
    - `api_key_hash` (String): Hashed key for API authentication.

3.  **`Properties`** (Buildings)
    - `id` (UUID, PK): Unique identifier.
    - `org_id` (UUID, FK): Link to Organizations.
    - `address` (Text).
    - `timezone` (String).
    - `total_devices` (Int).

4.  **`Devices`** (The IoT Hardware)
    - `id` (UUID, PK): Unique identifier.
    - `property_id` (UUID, FK): Link to Properties.
    - `mac_address` (String, Unique).
    - `device_type` (String): e.g., "HVAC_SENSOR".
    - `firmware_version` (String).
    - `status` (Enum): ONLINE, OFFLINE, ERROR.

5.  **`Telemetry`** (Time-series data - Read Model)
    - `id` (BigInt, PK).
    - `device_id` (UUID, FK): Link to Devices.
    - `value` (Float).
    - `timestamp` (DateTime, Indexed).
    - `metric_type` (String): e.g., "TEMP".

6.  **`EventStore`** (The Heart of CQRS)
    - `sequence_id` (BigInt, PK): Global monotonically increasing ID.
    - `aggregate_id` (UUID): ID of the entity being changed (e.g., Device ID).
    - `event_type` (String): e.g., "DeviceTemperatureUpdated".
    - `payload` (JSONB): The actual change data.
    - `created_at` (DateTime).

7.  **`AuditLogs`** (Tamper-Evident Table)
    - `id` (UUID, PK).
    - `user_id` (UUID, FK): Link to Users.
    - `action` (String).
    - `previous_hash` (String): Hash of the prior row.
    - `current_hash` (String): SHA-256 of (previous_hash + action + timestamp).
    - `timestamp` (DateTime).

8.  **`FeatureFlags`**
    - `flag_name` (String, PK).
    - `is_enabled` (Boolean).
    - `rollout_percentage` (Int): 0-100.
    - `target_groups` (JSONB): List of user IDs or Org IDs.

9.  **`ApiUsage`**
    - `api_key_id` (UUID, FK).
    - `endpoint` (String).
    - `request_count` (Int).
    - `window_start` (DateTime).

10. **`SsoConfigurations`**
    - `org_id` (UUID, FK).
    - `entity_id` (String).
    - `sso_url` (String).
    - `public_certificate` (Text).

### 5.2 Relationships
- **Organization $\to$ User:** One-to-Many.
- **Organization $\to$ Property:** One-to-Many.
- **Property $\to$ Device:** One-to-Many.
- **Device $\to$ Telemetry:** One-to-Many (High volume).
- **EventStore $\to$ Device:** One-to-Many (The EventStore records all history for a Device).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We maintain three distinct environments to ensure stability before production deployment.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Host:** Local Docker containers / Vercel Preview branches.
- **Database:** Local PostgreSQL instance.
- **CI/CD:** Triggered on every commit to a feature branch.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing and UAT (User Acceptance Testing).
- **Host:** `staging.citadel.coralreef.io` on Vercel.
- **Database:** A mirrored instance of production data (anonymized).
- **CI/CD:** Triggered on merge to the `develop` branch.
- **Requirement:** Must pass all integration tests before promotion to production.

#### 6.1.3 Production (Prod)
- **Purpose:** Live client traffic.
- **Host:** `app.citadel.coralreef.io` on Vercel.
- **Database:** AWS RDS PostgreSQL (Multi-AZ for high availability).
- **CI/CD:** Triggered on merge to `main`.
- **Compliance:** SOC 2 Type II monitored environment.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is managed via **Terraform**. This ensures that the staging environment is an exact replica of production, preventing "it works on my machine" bugs.

### 6.3 Vercel Edge Network
To reduce latency for global real estate portfolios, we utilize Vercel Edge Functions for the API Gateway, allowing rate-limiting checks and authentication to happen closer to the user.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, utility classes, and Prisma resolvers.
- **Tooling:** Jest + ts-jest.
- **Requirement:** 80% code coverage minimum for all new microservices.
- **Execution:** Runs on every PR in the GitHub Actions pipeline.

### 7.2 Integration Testing
- **Scope:** Interactions between microservices, API $\to$ Database, and Event Bus $\to$ Projection.
- **Tooling:** Supertest + Testcontainers (to spin up real Postgres/Redis instances).
- **Requirement:** Every critical path (e.g., Device Command $\to$ Event Store $\to$ Read Model) must have a corresponding integration test.
- **Execution:** Runs in the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "User logs in $\to$ selects property $\to$ changes thermostat").
- **Tooling:** Playwright.
- **Requirement:** Critical "Happy Path" tests must pass before any merge to `main`.
- **Execution:** Runs against the Staging environment prior to Production release.

### 7.4 Performance Testing
- **Scope:** Load testing to ensure the 10x capacity requirement is met.
- **Tooling:** k6.
- **Metric:** P99 latency must remain under 200ms for 95% of all API requests under a load of 5,000 concurrent users.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Performance requirements are 10x current capacity with no extra budget. | High | High | Negotiate timeline extension with stakeholders to allow for architecture optimization. |
| **R-02** | Primary vendor EOL (End of Life) announcement for critical component. | Medium | Critical | Raise as a blocker in the next board meeting; begin scouting alternative vendors immediately. |
| **R-03** | SOC 2 Compliance failure during audit. | Low | High | Conduct monthly internal "pre-audits" and utilize a compliance automation tool (e.g., Vanta). |
| **R-04** | Data loss during monolith $\to$ microservice migration. | Medium | Critical | Implement a "Dual Write" strategy: write to both old and new systems for 30 days before cutting over. |
| **R-05** | Team burnout due to aggressive deadlines. | Medium | Medium | Maintain the disciplined approach to technical debt; schedule "Cool-down" sprints every 4 sprints. |

---

## 9. TIMELINE AND PHASES

The project is structured over 18 months, divided into four primary phases.

### Phase 1: Foundation & Decomposition (Months 1–6)
- **Goal:** Establish the microservices skeleton and the Event Store.
- **Key Activities:** 
    - Setup Kafka and PostgreSQL RDS.
    - Decompose "User Management" and "Device Registry" from the monolith.
    - Implement the basic CQRS pattern.
- **Dependency:** Completion of infrastructure setup.

### Phase 2: Feature Acceleration (Months 7–12)
- **Goal:** Implement high-priority features.
- **Key Activities:**
    - Build Customer-Facing API (v1).
    - Develop Audit Trail Logging (High Priority).
    - Implement Rate Limiting (once Redis is approved).
- **Milestone 1:** Performance benchmarks met (**2025-08-15**).

### Phase 3: Beta and Hardening (Months 13–16)
- **Goal:** External validation and security compliance.
- **Key Activities:**
    - Launch External Beta.
    - SOC 2 Type II Audit window.
    - SSO Integration.
- **Milestone 2:** External beta with 10 pilot users (**2025-10-15**).

### Phase 4: Scale and Transition (Months 17–18)
- **Goal:** Full production cut-over.
- **Key Activities:**
    - Final migration of the legacy monolith.
    - A/B Testing framework deployment.
    - Performance tuning for 10x load.
- **Milestone 3:** Production launch (**2025-12-15**).

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-02)
**Attendees:** Anouk, Celine, Sol, Lior
- CQRS vs CRUD?
- Anouk says audit is non-negotiable $\to$ Event Sourcing it is.
- Sol worried about UI latency with projections $\to$ use Vercel Edge for caching.
- Lior to research Kafka vs RabbitMQ.
- Decision: Kafka for the event bus.

### Meeting 2: Security Review (2023-12-15)
**Attendees:** Anouk, Celine
- SOC 2 needs a "tamper-evident" log.
- Celine suggests SHA-256 chaining in the `AuditLogs` table.
- Blocker: Need a security architect to sign off on the salt/hash strategy.
- Note: Lead architect on medical leave; everything paused until return.

### Meeting 3: Sprint Planning - Q1 (2024-01-10)
**Attendees:** Anouk, Celine, Sol, Lior
- Budget is $3M $\to$ high visibility.
- Performance target is 10x.
- Celine says current RDS instance won't handle it.
- No more money for bigger servers?
- Anouk: we'll have to optimize the queries or ask for a timeline shift.
- Lior to start on Sandbox API mocks.

---

## 11. BUDGET BREAKDOWN

The total budget of **$3,000,000** is allocated across personnel, infrastructure, and operational overhead.

### 11.1 Personnel (Annualized)
| Role | Count | Avg Salary | Total |
| :--- | :--- | :--- | :--- |
| Tech Lead (Anouk) | 1 | $180,000 | $180,000 |
| Sr. Backend (Celine) | 1 | $160,000 | $160,000 |
| Product Designer (Sol) | 1 | $130,000 | $130,000 |
| Intern (Lior) | 1 | $60,000 | $60,000 |
| Other Engineers (3) | 3 | $140,000 | $420,000 |
| **Total Personnel (Year 1)** | **7** | | **$950,000** |
*(Note: Budget extends over 18 months; total personnel cost projected at $1.42M)*

### 11.2 Infrastructure (Monthly/Yearly)
| Item | Provider | Monthly Cost | Yearly Total |
| :--- | :--- | :--- | :--- |
| Vercel Enterprise | Vercel | $2,000 | $24,000 |
| AWS RDS (Postgres) | AWS | $3,500 | $42,000 |
| Kafka Managed (MSK) | AWS | $2,000 | $24,000 |
| Redis Cloud | Redis | $500 | $6,000 |
| S3 (WORM Storage) | AWS | $800 | $9,600 |
| **Total Infrastructure** | | | **$105,600** |

### 11.3 Tools & Compliance
| Item | Purpose | Cost |
| :--- | :--- | :--- |
| Vanta/Drata | SOC 2 Automation | $15,000 |
| LaunchDarkly | Feature Flags | $12,000 |
| External Security Audit | SOC 2 Certification | $40,000 |
| **Total Tools** | | **$67,000** |

### 11.4 Budget Summary
- **Personnel (18 mo):** $1,425,000
- **Infrastructure (18 mo):** $158,400
- **Tools/Compliance:** $67,000
- **Contingency (45%):** $1,349,600
- **TOTAL:** **$3,000,000**

*(The high contingency is intentionally set to handle the "10x performance" risk and potential vendor replacement costs.)*

---

## 12. APPENDICES

### Appendix A: Data Migration Strategy (Monolith $\to$ Microservices)
To migrate data without downtime, the team will implement the **Strangler Fig Pattern**:
1. **Intercept:** Route a small percentage of traffic to the new microservice using the Vercel Edge Middleware.
2. **Shadow Write:** The new service writes to the new PostgreSQL DB but the legacy monolith remains the "source of truth."
3. **Compare:** A background job compares the data in the monolith and the microservice to ensure parity.
4. **Cutover:** Once parity is verified for 7 consecutive days, the microservice becomes the source of truth, and the monolith's write-path is disabled.

### Appendix B: SOC 2 Type II Control Mapping
| Requirement | Citadel Implementation | Verification Method |
| :--- | :--- | :--- |
| Access Control | SSO (SAML/OIDC) + Role-Based Access Control (RBAC) | Quarterly Access Review |
| Change Management | GitHub PRs $\to$ Vercel CD $\to$ Automated Tests | Git Commit Logs |
| Data Encryption | AES-256 at rest (AWS RDS), TLS 1.3 in transit | Configuration Audit |
| Availability | Multi-AZ RDS + Vercel Global Edge | Uptime Monitoring (99.9%) |
| Auditability | Tamper-Evident `AuditLogs` table with SHA-256 | Hash Verification Script |