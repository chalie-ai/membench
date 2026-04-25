Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, industrial-grade Project Specification. It expands every provided constraint into a professional engineering blueprint.

***

# PROJECT SPECIFICATION: GANTRY (v1.4.2)
**Company:** Crosswind Labs  
**Industry:** Retail IoT  
**Status:** Active Development  
**Last Updated:** October 24, 2025  
**Classification:** Internal / Confidential / FedRAMP Target  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Gantry is a specialized IoT device network designed to optimize retail productivity through real-time hardware telemetry and asset orchestration. What began as a high-concept hackathon project has rapidly evolved into a mission-critical internal productivity tool. Currently, Gantry supports 500 daily active users (DAU) within Crosswind Labs, providing a centralized layer for managing sensor arrays, inventory beacons, and retail automation hardware.

The core value proposition of Gantry lies in its ability to abstract the complexity of heterogeneous IoT protocols into a unified API, allowing retail operators to automate store-floor logistics without requiring deep firmware expertise.

### 1.2 Business Justification
In the current retail landscape, the gap between physical inventory and digital tracking leads to significant revenue leakage. Gantry closes this gap by providing a high-availability network that monitors device health and data flow in real-time. By transitioning from a "hackathon prototype" to a production-grade system, Crosswind Labs aims to productize this internal success and offer it as a B2B SaaS offering to external retail partners.

The primary driver for the current development phase is the requirement for FedRAMP authorization. As Crosswind Labs pursues government contracts (specifically for logistics and military retail supply chains), the system must migrate from a "convenience-first" architecture to a "security-first" framework.

### 1.3 ROI Projection and Success Criteria
The financial goal for Gantry is aggressive given the shoestring budget of $150,000. However, the projected ROI is based on the following metrics:
- **Direct Revenue:** The project is targeted to drive $500,000 in new attributed revenue within 12 months post-launch. This will be achieved through tiered subscription licenses for pilot retail partners.
- **Operational Efficiency:** A target p95 API response time of <200ms at peak load is mandated. Reducing latency in IoT command-and-control loops directly correlates to a decrease in retail "out-of-stock" events.
- **Market Expansion:** Successful FedRAMP certification will unlock the "Government Retail" sector, expanding the Total Addressable Market (TAM) by approximately 22%.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Stack
Gantry utilizes a modern, event-driven microservices architecture designed for horizontal scalability on AWS.

- **Language/Framework:** Python 3.11 / Django 4.2 (utilizing Django REST Framework for API layers).
- **Primary Database:** PostgreSQL 15 (Relational data, device registries, user accounts).
- **Caching/Queueing:** Redis 7.0 (Session management, transient state, and caching).
- **Event Streaming:** Apache Kafka (Decoupling device telemetry from business logic).
- **Orchestration:** AWS ECS (Elastic Container Service) using Fargate for serverless compute.
- **CI/CD:** GitHub Actions for automated linting, testing, and deployment.
- **Deployment Strategy:** Blue-Green deployments via AWS CodeDeploy to ensure zero-downtime updates.

### 2.2 Architectural Diagram (ASCII)
The following represents the data flow from a retail IoT device to the Gantry dashboard.

```text
[Retail IoT Devices] 
       |
       | (MQTT/HTTPS)
       v
[AWS Application Load Balancer]
       |
       +------> [Auth Service (Django)] <---> [PostgreSQL (Users/Permissions)]
       |                                 |
       |                                 v
       +------> [Telemetry Service (Django)] <---> [Redis (Hot Cache)]
       |               |
       |               v
       |        [Kafka Topic: device_events]
       |               |
       |               +------> [Analysis Engine (Worker)] ----> [PostgreSQL (History)]
       |               +------> [Notification Service] --------> [Webhooks/Email]
       |
       +------> [Admin API / Dashboard] <---> [React Frontend]
```

### 2.3 Infrastructure Detail
The system is partitioned into three distinct environments:
1. **Development (dev):** Local Dockerized environments and a shared AWS account for feature testing.
2. **Staging (stg):** A mirrored production environment used for UAT and security scanning.
3. **Production (prod):** The hardened, FedRAMP-compliant environment.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: High)
**Status:** In Design
**Description:** 
The current search functionality is a basic `LIKE` query in PostgreSQL, which is insufficient for the 500+ users managing thousands of devices. The "Advanced Search" feature will implement full-text indexing and faceted navigation to allow users to drill down into device telemetry.

**Technical Requirements:**
- **Indexing:** Implementation of PostgreSQL GIN (Generalized Inverted Index) for full-text search on device metadata.
- **Faceting:** The API must return a count of devices per category (e.g., "Status: Offline (42)", "Model: Sensor-X (110)") in the response metadata.
- **Filtering:** Support for complex boolean logic (AND/OR) across hardware IDs, firmware versions, and geographic location tags.
- **Performance:** Search queries must return results in under 150ms for datasets up to 1 million records.

**User Workflow:**
The user enters "Temp-Sensor" in the search bar. The system returns all matches and a sidebar showing facets: *Firmware v2.1 (10), Firmware v2.0 (5), Location: Warehouse A (12), Location: Store B (3).*

### 3.2 SSO Integration with SAML and OIDC (Priority: Medium)
**Status:** In Design
**Description:** 
To meet FedRAMP and corporate retail standards, Gantry must move away from local password storage toward Single Sign-On (SSO). This feature will integrate Gantry with external Identity Providers (IdPs) such as Okta, Azure AD, and Google Workspace.

**Technical Requirements:**
- **SAML 2.0:** Implement a Service Provider (SP) initiated flow. The system must handle SAML assertions and map group memberships to internal Django roles.
- **OIDC (OpenID Connect):** Implement the Authorization Code Flow with PKCE for secure authentication.
- **User Provisioning:** Support Just-In-Time (JIT) provisioning, where a user account is created automatically upon their first successful SSO login.
- **Session Management:** Redis will store the SSO session tokens with a configurable TTL (Time To Live) based on the client's security policy.

**Security Implications:**
All SSO configurations must be encrypted at rest. The `sso_config` table in PostgreSQL will store the metadata URLs and public keys of the IdP.

### 3.3 Two-Factor Authentication (2FA) with Hardware Keys (Priority: Medium)
**Status:** Blocked
**Description:** 
As a requirement for high-security retail environments, 2FA is mandatory. This feature expands beyond SMS/Email OTP to include FIDO2/WebAuthn support for physical hardware keys (e.g., Yubikeys).

**Blocker:** 
The project is currently waiting on the legal review of the Data Processing Agreement (DPA) regarding how biometric/hardware-key metadata is stored and processed across international borders.

**Technical Requirements:**
- **WebAuthn API:** Integration of the browser-based WebAuthn API to allow device registration.
- **Fallback Mechanisms:** Support for TOTP (Time-based One-Time Password) via apps like Google Authenticator.
- **Recovery:** A secure system for "Recovery Codes" that are generated upon 2FA setup and stored as salted hashes.
- **Enforcement:** Ability for administrators to mandate 2FA for all users in a specific organization.

### 3.4 Data Import/Export with Format Auto-Detection (Priority: Low)
**Status:** In Design
**Description:** 
Retail clients often migrate from legacy systems. Gantry requires a robust utility to import device lists and historical telemetry without manual formatting.

**Technical Requirements:**
- **Auto-Detection:** A Python-based sniffing utility to identify if an uploaded file is CSV, JSON, or XML.
- **Schema Mapping:** A UI-driven mapping tool where users can associate a column in their CSV (e.g., "Device_Serial") with a Gantry field (e.g., `hardware_uuid`).
- **Asynchronous Processing:** Imports must be handled by a Celery worker to avoid blocking the main request thread.
- **Export:** Ability to export filtered device lists in JSON and CSV formats for audit purposes.

**Performance Target:** 
Imports of up to 50,000 records should complete within 60 seconds.

### 3.5 Webhook Integration Framework (Priority: Low)
**Status:** Complete
**Description:** 
Gantry can now push real-time events to third-party tools (e.g., Slack, PagerDuty, custom retail dashboards) when specific device triggers occur.

**Technical Requirements:**
- **Trigger System:** Users can define "Event Triggers" (e.g., `device.status == "offline"`).
- **Payload Delivery:** POST requests sent to a user-defined URL with a JSON payload.
- **Retry Logic:** Exponential backoff for failed deliveries (1min, 5min, 15min, 1hr).
- **Security:** Implementation of HMAC signatures in the `X-Gantry-Signature` header so receivers can verify the request came from Crosswind Labs.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. All requests require a `Bearer <token>` header.

### 4.1 Device Management

**GET `/api/v1/devices/`**
- **Description:** Retrieve a list of all devices with optional filtering.
- **Query Params:** `search`, `status`, `model`.
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "count": 2,
    "results": [
      {"id": "dev-001", "status": "online", "model": "Temp-X1"},
      {"id": "dev-002", "status": "offline", "model": "Temp-X1"}
    ]
  }
  ```

**POST `/api/v1/devices/`**
- **Description:** Register a new IoT device.
- **Request Body:** `{"name": "Store-1-North", "model": "Temp-X1", "mac_address": "00:1A:2B:3C:4D:5E"}`
- **Response:** `201 Created`
- **Example Response:** `{"id": "dev-003", "status": "provisioning"}`

**PATCH `/api/v1/devices/{id}/`**
- **Description:** Update device metadata or status.
- **Request Body:** `{"status": "maintenance"}`
- **Response:** `200 OK`

### 4.2 Telemetry and Search

**GET `/api/v1/telemetry/{device_id}/`**
- **Description:** Get recent telemetry for a specific device.
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "device_id": "dev-001",
    "readings": [
      {"timestamp": "2025-10-24T10:00:00Z", "value": 22.5, "unit": "Celsius"},
      {"timestamp": "2025-10-24T10:05:00Z", "value": 22.6, "unit": "Celsius"}
    ]
  }
  ```

**GET `/api/v1/search/faceted/`**
- **Description:** Returns search results and associated filter counts.
- **Query Params:** `q` (query string).
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "results": [...],
    "facets": {
      "status": {"online": 400, "offline": 100},
      "model": {"Temp-X1": 300, "Humidity-Y2": 200}
    }
  }
  ```

### 4.3 System and Security

**POST `/api/v1/auth/sso/login/`**
- **Description:** Initiates the SAML/OIDC handshake.
- **Request Body:** `{"provider": "okta"}`
- **Response:** `302 Found` (Redirect to IdP).

**POST `/api/v1/webhooks/register/`**
- **Description:** Create a new webhook subscription.
- **Request Body:** `{"url": "https://client.com/hook", "events": ["device.offline"]}`
- **Response:** `201 Created`

**GET `/api/v1/health/`**
- **Description:** System health check for AWS Load Balancer.
- **Response:** `200 OK` $\rightarrow$ `{"status": "healthy", "db": "connected", "redis": "connected"}`

---

## 5. DATABASE SCHEMA

The database uses PostgreSQL 15. All tables use UUIDs as primary keys to prevent ID enumeration attacks.

### 5.1 Table Definitions

1.  **`users`**: Stores user account data.
    - `id` (UUID, PK), `email` (String, Unique), `password_hash` (String), `is_active` (Bool), `last_login` (Timestamp).
2.  **`organizations`**: Retail client entities.
    - `id` (UUID, PK), `org_name` (String), `billing_plan` (String), `created_at` (Timestamp).
3.  **`user_org_mapping`**: Many-to-many link between users and orgs.
    - `user_id` (FK), `org_id` (FK), `role` (Enum: Admin, Viewer, Editor).
4.  **`devices`**: The core IoT registry.
    - `id` (UUID, PK), `org_id` (FK), `mac_address` (String, Unique), `model_id` (FK), `status` (Enum), `firmware_version` (String), `last_seen` (Timestamp).
5.  **`device_models`**: Definitions of hardware types.
    - `id` (UUID, PK), `model_name` (String), `manufacturer` (String), `specifications` (JSONB).
6.  **`telemetry_logs`**: High-volume time-series data (Partitioned by month).
    - `id` (BigInt, PK), `device_id` (FK), `timestamp` (Timestamp), `payload` (JSONB), `metric_value` (Numeric).
7.  **`sso_configs`**: Configuration for SAML/OIDC providers.
    - `id` (UUID, PK), `org_id` (FK), `provider_type` (Enum), `metadata_url` (String), `public_cert` (Text).
8.  **`two_factor_keys`**: Stores WebAuthn/TOTP secrets.
    - `id` (UUID, PK), `user_id` (FK), `key_type` (Enum), `secret_hash` (String), `created_at` (Timestamp).
9.  **`webhooks`**: Third-party integration targets.
    - `id` (UUID, PK), `org_id` (FK), `target_url` (String), `secret_token` (String), `is_active` (Bool).
10. **`webhook_events`**: Audit log of all sent webhooks.
    - `id` (UUID, PK), `webhook_id` (FK), `event_type` (String), `response_code` (Int), `sent_at` (Timestamp).

### 5.2 Relationships
- **One-to-Many:** `organizations` $\rightarrow$ `devices`.
- **One-to-Many:** `devices` $\rightarrow$ `telemetry_logs`.
- **Many-to-Many:** `users` $\leftrightarrow$ `organizations` via `user_org_mapping`.
- **One-to-One:** `users` $\rightarrow$ `two_factor_keys` (typically).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry utilizes a strict environment promotion pipeline to ensure stability.

| Environment | Purpose | Data Source | Deployment Method |
| :--- | :--- | :--- | :--- |
| **Dev** | Feature development | Mock/Anonymized | Manual Docker / GitHub Action |
| **Staging** | UAT & Security Audits | Sanitized Prod Clone | Blue-Green via GitHub Actions |
| **Prod** | Live Retail Operations | Production DB | Blue-Green via AWS CodeDeploy |

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1. **Lint/Test Phase:** `flake8` and `pytest` run on every push to `develop` or `main`.
2. **Build Phase:** Docker image is built and pushed to AWS ECR (Elastic Container Registry).
3. **Deploy Phase:**
    - **Staging:** Automatic deploy on merge to `develop`.
    - **Production:** Manual trigger on merge to `main` following a peer-reviewed Release Note.
4. **Verification:** A suite of Smoke Tests runs against the "Green" environment before the Load Balancer switches traffic.

### 6.3 FedRAMP Compliance Measures
To achieve FedRAMP authorization, the production environment implements:
- **FIPS 140-2:** All encryption in transit uses FIPS-validated modules.
- **VPC Isolation:** The database and Kafka clusters are in private subnets with no direct internet access.
- **Audit Logging:** All API calls are logged to AWS CloudWatch with immutable logs enabled.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual Python functions and Django models.
- **Tooling:** `pytest` with `pytest-django`.
- **Coverage Target:** 85% minimum line coverage.
- **Frequency:** Executed on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** Communication between microservices (e.g., Django $\rightarrow$ Kafka $\rightarrow$ Worker).
- **Tooling:** `TestContainers` to spin up a real PostgreSQL and Redis instance during the test run.
- **Focus:** Ensuring that event-driven messages are correctly serialized and consumed.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "User logs in $\rightarrow$ Searches for device $\rightarrow$ Updates status").
- **Tooling:** `Playwright` for headless browser testing.
- **Frequency:** Run nightly on the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Primary vendor announced EOL for hardware API | High | Critical | Escalate to steering committee for additional funding to migrate to a new vendor. |
| **R2** | Key Architect leaving in 3 months | Medium | High | Implement a "Knowledge Transfer" sprint; document all workarounds in the internal Wiki. |
| **R3** | Legal delay on DPA (Blocker) | High | Medium | Maintain current 2FA block; focus on non-blocked features (Search/SSO). |
| **R4** | Technical Debt: Hardcoded configs | High | Medium | Implement a `config.py` manager and migrate values to AWS Secrets Manager. |

**Probability/Impact Matrix:**
- *Critical:* Immediate project failure or revenue loss.
- *High:* Significant delay or cost increase.
- *Medium:* Manageable with extra effort.

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach from October 2025 through November 2026.

### 9.1 Phase 1: Core Hardening (Oct 2025 - Feb 2026)
- **Focus:** Removing technical debt (hardcoded values), refining the Kafka event bus, and completing the Advanced Search design.
- **Dependencies:** Infrastructure stability.

### 9.2 Phase 2: External Integration (Mar 2026 - July 2026)
- **Focus:** Implementing SSO, completing 2FA (pending legal), and preparing the pilot environment.
- **Milestone 1: External Beta (Target: 2026-07-15).** 10 pilot users from selected retail partners.

### 9.3 Phase 3: Compliance & Audit (July 2026 - Sept 2026)
- **Focus:** FedRAMP hardening, penetration testing, and documentation.
- **Milestone 2: Security Audit Passed (Target: 2026-09-15).**

### 9.4 Phase 4: Launch (Sept 2026 - Nov 2026)
- **Focus:** Load testing p95 response times and scaling ECS clusters.
- **Milestone 3: Production Launch (Target: 2026-11-15).**

---

## 10. MEETING NOTES (Running Document)

*Note: The following is an excerpt from the shared running document (currently 200 pages and unsearchable).*

**Meeting Date: 2025-08-12**
- **Attendees:** Uma, Dina, Kira, Vera.
- **Discussion:** Discussed the "hardcoded config" issue. Dina noted that there are over 40 files with `API_KEY = "12345"` hardcoded.
- **Decision:** Uma decided not to stop feature development but tasked Vera (Intern) with creating a spreadsheet of all hardcoded values to be migrated to AWS Secrets Manager in Phase 1.
- **Action Item:** Vera to audit `/services/telemetry/` by Friday.

**Meeting Date: 2025-09-05**
- **Attendees:** Uma, Dina, Kira.
- **Discussion:** The primary vendor sent the EOL (End of Life) notice. We are effectively on a countdown.
- **Decision:** We cannot afford a new vendor on the current $150k budget. Uma will escalate this to the Steering Committee. Until then, we "patch and pray."
- **Action Item:** Uma to draft the funding request for an additional $50k for vendor migration.

**Meeting Date: 2025-10-10**
- **Attendees:** Uma, Dina, Kira, Vera.
- **Discussion:** 2FA is blocked. Legal hasn't signed off on the DPA for hardware key metadata.
- **Decision:** Shift focus to Advanced Search. Kira to finish the Figma mocks for faceted filtering by next Tuesday.
- **Action Item:** Dina to investigate PostgreSQL GIN indexes for the search implementation.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Shoestring)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Adjusted for intern stipend and partial senior contractor hours. |
| **Infrastructure** | 20% | $30,000 | AWS ECS, RDS, and Kafka Managed Service (MSK). |
| **Tools & Licenses** | 10% | $15,000 | GitHub Enterprise, Snyk, and Okta Dev accounts. |
| **Contingency** | 10% | $15,000 | Reserved for emergency vendor patches or legal fees. |

**Budget Constraint:** Every dollar is scrutinized. No unplanned AWS instance upgrades are permitted without Uma's direct sign-off.

---

## 12. APPENDICES

### Appendix A: Kafka Topic Specifications
To ensure event-driven consistency, the following Kafka topics are defined:
- `device.telemetry.raw`: Raw JSON dumps from devices. Partitioned by `device_id`.
- `device.status.change`: Events triggered when a device moves from `online` $\rightarrow$ `offline`.
- `system.alerts`: High-priority alerts for hardware failure.
- `user.audit.log`: Every administrative action taken via the API.

### Appendix B: FedRAMP Control Mapping
| Control ID | Gantry Implementation | Evidence |
| :--- | :--- | :--- |
| AC-2 | Account Management | SSO Integration with OIDC/SAML |
| AU-2 | Event Logging | All API calls piped to CloudWatch |
| IA-2 | Identification & Auth | 2FA with Hardware Keys (Pending Legal) |
| SC-8 | Transmission Confidentiality | TLS 1.3 for all internal/external traffic |

---

**End of Specification**