# PROJECT SPECIFICATION: PROJECT JUNIPER
**Document Version:** 1.0.4  
**Status:** Active / In-Review  
**Classification:** Confidential - Crosswind Labs  
**Date:** October 24, 2023  
**Owner:** Aaliya Costa (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Juniper is the mission-critical initiative by Crosswind Labs to modernize and replace a 15-year-old legacy firmware and control system that serves as the backbone for our retail operational infrastructure. The legacy system, while stable, has become a significant liability due to lack of maintainability, outdated hardware dependencies, and an inability to scale with current retail demands. Because the entire company depends on this system for real-time retail transactions and device management, the transition must be executed with **zero downtime tolerance**. Any service interruption during the migration will result in immediate revenue loss and operational paralysis across our retail partner network.

### 1.2 Business Justification
The legacy system currently utilizes a monolithic architecture that is prone to "cascading failures," where a single bug in a peripheral driver can crash the entire retail terminal. Maintenance costs have surged as the talent pool capable of maintaining the legacy codebase has dwindled. Furthermore, the current system lacks the agility to implement modern security protocols required for PCI DSS Level 1 compliance, exposing the firm to potential regulatory fines and security breaches.

Project Juniper transforms this monolith into a distributed, event-driven microservices architecture. By shifting to a Go-based stack and leveraging Kubernetes on GCP, we decouple the hardware-specific firmware logic from the business orchestration layer. This allows for independent scaling of services and rapid deployment of patches without requiring a full system reboot of the retail terminals.

### 1.3 ROI Projection
The financial justification for Project Juniper is rooted in three primary areas:
1.  **Operational Efficiency:** Reduction in system downtime is projected to increase retail throughput by 12%, translating to an estimated $2.4M in recaptured annual revenue across the partner network.
2.  **Maintenance Cost Reduction:** By migrating to Go and gRPC, we estimate a 40% reduction in developer hours spent on "bug-hunting" within the legacy C-based monolith.
3.  **Risk Mitigation:** Achieving PCI DSS Level 1 certification natively within the new architecture eliminates the need for expensive third-party middleware "wrappers" currently used to mask legacy vulnerabilities, saving approximately $45,000 per year in licensing fees.

The project operates on a lean budget of $150,000. While this is a "shoestring" budget for a replacement of this magnitude, the ROI is realized through the utilization of open-source technologies (CockroachDB, Kafka) and a distributed, remote-first team structure that minimizes overhead.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Juniper employs a microservices architecture designed for high availability and eventual consistency. The core logic is written in Go, chosen for its concurrency primitives and efficiency in embedded-adjacent environments. Communication between services is handled via gRPC for synchronous internal calls and Apache Kafka for asynchronous, event-driven state changes.

### 2.2 Infrastructure Stack
- **Language:** Go 1.21+
- **Communication:** gRPC (Internal), REST/JSON (External)
- **Messaging:** Apache Kafka (Event Streaming)
- **Database:** CockroachDB (Distributed SQL for global consistency)
- **Orchestration:** Kubernetes (GKE - Google Kubernetes Engine)
- **Cloud Provider:** GCP (Google Cloud Platform)
- **Security:** TLS 1.3, AES-256 encryption at rest, PCI DSS Level 1 Compliant Vaulting

### 2.3 ASCII Architecture Diagram
The following diagram represents the flow of data from the retail embedded terminal to the cloud backend.

```text
[ Retail Terminal ]  <-- (gRPC/TLS) --> [ GCP Load Balancer ]
                                               |
                                               v
                                    [ Kubernetes Cluster ]
                                    |                      |
          __________________________|______________________|__________________________
         |                          |                      |                          |
  [ Auth Service ] <--> [ Dashboard Service ] <--> [ Billing Service ] <--> [ File Service ]
         |                          |                      |                          |
         |                          |                      |                          |
         +--------------------------+-----------+----------+--------------------------+
                                               |
                                               v
                                    [ Kafka Event Bus ]
                                               |
          _____________________________________|______________________________________
         |                                      |                                      |
 [ Audit Log Service ]                 [ Analytics Service ]                 [ Notification Svc ]
         |                                      |                                      |
         v                                      v                                      v
 [ CockroachDB Cluster ] <--------------------> [ CockroachDB Cluster ] <-------------------> [ Cloud Storage ]
     (User/Auth Data)                        (Billing/Metric Data)                      (Firmware Binaries)
```

### 2.4 Data Flow Logic
When a retail terminal requests a firmware update, the **File Service** validates the request, checks the **Auth Service** for credentials, and streams the binary from the CDN. Simultaneously, an event is published to **Kafka**, which the **Analytics Service** consumes to track the update success rate and the **Billing Service** uses to calculate usage quotas.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Critical (Launch Blocker) | **Status:** In Progress
**Description:**
The dashboard is the primary interface for retail operators to monitor the health of their embedded systems. Given the complexity of the legacy system being replaced, operators require a highly flexible view to monitor different metrics (e.g., CPU temperature of terminals, transaction success rates, memory leaks) based on their specific role.

**Functional Requirements:**
- **Widget Library:** A set of predefined widgets including "Real-time Transaction Graph," "Device Health Heatmap," "Active Alerts Feed," and "System Resource Monitor."
- **Drag-and-Drop Interface:** Users must be able to reposition widgets on a grid. The layout state must be persisted in CockroachDB so the dashboard remains consistent across sessions.
- **Custom Querying:** Power users can create custom widgets by defining a gRPC query to the Analytics Service.
- **Responsiveness:** The dashboard must load in < 2 seconds, utilizing a cached version of the data from the edge CDN to avoid overloading the backend.

**Technical Implementation:**
The frontend (React) will send a JSON payload representing the grid coordinates and widget IDs to the `DashboardService`. This service will validate the user's permissions via the `AuthService` and store the layout in the `user_dashboard_configs` table. Data within the widgets is populated via a gRPC stream from the `AnalyticsService`, ensuring real-time updates without refreshing the page.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Design
**Description:**
To prevent the "noisy neighbor" effect in our multi-tenant retail environment, Juniper must implement strict API rate limiting. This prevents a single malfunctioning retail terminal from flooding the system with requests and causing a denial-of-service for other clients.

**Functional Requirements:**
- **Tiered Limiting:** Three tiers of access: *Basic* (100 req/min), *Professional* (1,000 req/min), and *Enterprise* (Unlimited/Custom).
- **Leaky Bucket Algorithm:** Implementation of a leaky bucket algorithm to handle bursts of traffic while maintaining a steady flow.
- **Usage Analytics:** A comprehensive logging system that tracks every API call, response time, and error code. This data is used for both technical debugging and billing.
- **Header Notifications:** When a limit is hit, the API must return a `429 Too Many Requests` status with `X-RateLimit-Reset` headers.

**Technical Implementation:**
The rate limiter will be implemented as a Kubernetes Sidecar proxy (Envoy) to ensure that requests are throttled before they even reach the Go microservices. The current count for each API key will be stored in a distributed Redis cache for sub-millisecond lookup. Analytics data will be asynchronously pushed to Kafka and then archived into CockroachDB for long-term reporting.

### 3.3 Automated Billing and Subscription Management
**Priority:** High | **Status:** In Design
**Description:**
The company is moving from a flat-fee legacy model to a usage-based subscription model. This system must automate the calculation of costs based on the "Usage Analytics" feature described above.

**Functional Requirements:**
- **Subscription Lifecycle:** Handling of sign-ups, upgrades, downgrades, and cancellations.
- **Automatic Invoicing:** Generation of monthly PDF invoices based on aggregated Kafka event data.
- **Dunning Management:** Automated email alerts and service suspension for failed credit card payments.
- **Tax Calculation:** Integration with a third-party tax API to ensure retail compliance across different global regions.

**Technical Implementation:**
The `BillingService` will act as a consumer of the `UsageEvents` Kafka topic. Every hour, it will aggregate usage totals and update the `billing_ledger` table in CockroachDB. For payment processing, the system will integrate with Stripe via a secure webhook. All credit card data will be tokenized; no raw PAN (Primary Account Number) data will ever touch the Juniper database, maintaining PCI DSS Level 1 compliance.

### 3.4 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Design
**Description:**
Retail terminals require periodic firmware updates. The "Juniper" system must provide a secure way for engineers to upload new binary images, ensure they are safe, and distribute them globally to thousands of devices.

**Functional Requirements:**
- **Secure Upload:** Multi-part upload support for binaries up to 500MB.
- **Automated Virus Scanning:** Integration with ClamAV or a similar engine to scan every uploaded file before it is marked as "staged."
- **CDN Integration:** Once scanned and approved, files are pushed to a Google Cloud Storage bucket with CDN enabled for edge-caching.
- **Version Control:** Ability to "roll back" to a previous version by updating the "current_stable" pointer in the database.

**Technical Implementation:**
The `FileService` will handle the initial upload to a "quarantine" bucket. A trigger will initiate a Go-based worker that runs the virus scan. If clean, the file is moved to the "production" bucket. The CDN (Cloud CDN) will then cache the binary. The terminal will request the file via a signed URL with a short expiration time to prevent unauthorized access.

### 3.5 SSO Integration with SAML and OIDC Providers
**Priority:** Low | **Status:** In Progress
**Description:**
To reduce administrative overhead, Juniper needs to allow retail partners to use their own corporate identity providers (IdPs) to manage employee access.

**Functional Requirements:**
- **SAML 2.0 Support:** Integration with legacy corporate IdPs (e.g., AD FS).
- **OIDC Support:** Integration with modern providers (e.g., Okta, Google Workspace).
- **Just-In-Time (JIT) Provisioning:** Automatically create a user profile in CockroachDB upon the first successful SSO login.
- **Role Mapping:** Map claims from the IdP (e.g., `group: admin`) to internal Juniper roles.

**Technical Implementation:**
The `AuthService` will implement a middleware layer that intercepts requests to the `/login` endpoint. If an external provider is detected, the service will redirect the user to the IdP's authorization endpoint. Upon return, the service will validate the JWT (JSON Web Token) or SAML Assertion using the provider's public key.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted under `https://api.juniper.crosswind.io/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 `GET /dashboard/layout`
- **Description:** Retrieves the current widget configuration for the authenticated user.
- **Request:** `GET /dashboard/layout`
- **Response:**
  ```json
  {
    "user_id": "usr_9982",
    "layout": [
      {"widget_id": "cpu_monitor", "x": 0, "y": 0, "w": 4, "h": 2},
      {"widget_id": "tx_graph", "x": 4, "y": 0, "w": 8, "h": 2}
    ]
  }
  ```

### 4.2 `POST /dashboard/layout`
- **Description:** Updates the widget layout for the authenticated user.
- **Request Body:**
  ```json
  {
    "layout": [{"widget_id": "cpu_monitor", "x": 0, "y": 0, "w": 4, "h": 2}]
  }
  ```
- **Response:** `200 OK` with updated layout.

### 4.3 `POST /files/upload`
- **Description:** Uploads a new firmware binary for scanning.
- **Request:** `MULTIPART/FORM-DATA` (File: binary, Version: string)
- **Response:**
  ```json
  {
    "upload_id": "up_4412",
    "status": "scanning",
    "estimated_completion": "2023-10-24T14:05:00Z"
  }
  ```

### 4.4 `GET /files/status/{upload_id}`
- **Description:** Checks if a binary has passed virus scanning.
- **Request:** `GET /files/status/up_4412`
- **Response:**
  ```json
  {
    "upload_id": "up_4412",
    "status": "clean",
    "cdn_url": "https://cdn.juniper.io/bin/v1.2.bin"
  }
  ```

### 4.5 `GET /billing/usage`
- **Description:** Returns current month's API usage for the client.
- **Request:** `GET /billing/usage`
- **Response:**
  ```json
  {
    "client_id": "cli_552",
    "requests_made": 450000,
    "limit": 1000000,
    "percentage_used": 45.0
  }
  ```

### 4.6 `POST /auth/sso/initiate`
- **Description:** Starts the SSO handshake.
- **Request Body:** `{"provider": "okta"}`
- **Response:** `302 Redirect` to the Okta authorization URL.

### 4.7 `GET /analytics/device/{device_id}`
- **Description:** Returns real-time telemetry for a specific retail terminal.
- **Request:** `GET /analytics/device/term_001`
- **Response:**
  ```json
  {
    "device_id": "term_001",
    "cpu_load": "12%",
    "mem_usage": "256MB",
    "status": "online"
  }
  ```

### 4.8 `PUT /billing/subscription`
- **Description:** Updates the subscription tier for the account.
- **Request Body:** `{"tier": "enterprise"}`
- **Response:** `200 OK` with new billing cycle dates.

---

## 5. DATABASE SCHEMA (CockroachDB)

The system utilizes a distributed SQL schema to ensure high availability across GCP regions.

### 5.1 Tables and Relationships

1.  **`users`**: Primary account table.
    - `user_id` (UUID, PK), `email` (String, Unique), `password_hash` (String), `role` (Enum: Admin, Operator, Viewer), `created_at` (Timestamp).
2.  **`devices`**: Inventory of all retail terminals.
    - `device_id` (UUID, PK), `serial_number` (String, Unique), `firmware_version` (String), `last_heartbeat` (Timestamp), `client_id` (FK $\rightarrow$ `clients.client_id`).
3.  **`clients`**: Retail companies using the system.
    - `client_id` (UUID, PK), `company_name` (String), `billing_email` (String), `subscription_tier` (String), `api_key_hash` (String).
4.  **`user_dashboard_configs`**: Stores the drag-and-drop layout.
    - `config_id` (UUID, PK), `user_id` (FK $\rightarrow$ `users.user_id`), `layout_json` (JSONB), `updated_at` (Timestamp).
5.  **`firmware_binaries`**: Catalog of available updates.
    - `bin_id` (UUID, PK), `version` (String), `checksum` (String), `scan_status` (Enum: Pending, Clean, Infected), `cdn_path` (String).
6.  **`billing_ledger`**: Records of all usage and charges.
    - `ledger_id` (UUID, PK), `client_id` (FK $\rightarrow$ `clients.client_id`), `amount` (Decimal), `billing_period` (Date), `status` (Enum: Paid, Pending, Overdue).
7.  **`api_usage_logs`**: High-volume table for analytics (Partitioned by month).
    - `log_id` (UUID, PK), `client_id` (FK $\rightarrow$ `clients.client_id`), `endpoint` (String), `response_time_ms` (Int), `timestamp` (Timestamp).
8.  **`sso_providers`**: Configuration for SAML/OIDC.
    - `provider_id` (UUID, PK), `client_id` (FK $\rightarrow$ `clients.client_id`), `provider_type` (String), `entity_id` (String), `public_cert` (Text).
9.  **`audit_logs`**: Immutable record of critical system changes (PCI Requirement).
    - `audit_id` (UUID, PK), `user_id` (FK $\rightarrow$ `users.user_id`), `action` (String), `timestamp` (Timestamp), `ip_address` (String).
10. **`device_telemetry`**: Time-series data for terminal health.
    - `telemetry_id` (UUID, PK), `device_id` (FK $\rightarrow$ `devices.device_id`), `cpu_temp` (Float), `mem_used` (Int), `timestamp` (Timestamp).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Juniper employs a three-tier environment strategy. Because we use Continuous Deployment, the path from merge to production is automated.

**1. Development (Dev):**
- **Purpose:** Sandbox for engineers.
- **Infrastructure:** Small GKE cluster (3 nodes).
- **Database:** Single-node CockroachDB instance.
- **Deployment:** Triggered on every push to a feature branch.

**2. Staging (Stage):**
- **Purpose:** Pre-production validation and QA. Mirrors production as closely as possible.
- **Infrastructure:** GKE cluster (10 nodes, multi-zone).
- **Database:** 3-node CockroachDB cluster.
- **Deployment:** Triggered on merge to the `develop` branch. This is where Devika Moreau (QA Lead) performs regression testing.

**3. Production (Prod):**
- **Purpose:** Live retail traffic. Zero downtime is the primary goal.
- **Infrastructure:** Multi-region GKE cluster with auto-scaling.
- **Database:** 9-node CockroachDB cluster across 3 GCP regions for survival of region failure.
- **Deployment:** Every merged PR to `main` is deployed via a Blue-Green deployment strategy. Traffic is shifted 10% at a time using the Load Balancer to ensure stability.

### 6.2 CI/CD Pipeline
The current pipeline is managed via GitHub Actions.
- **Build Phase:** Go binaries are compiled and wrapped in Docker containers.
- **Test Phase:** Unit tests run in parallel across 4 containers.
- **Deployment Phase:** Helm charts are used to deploy to GKE.
- **Known Issue:** The pipeline currently takes 45 minutes due to sequential execution of the integration test suite and a lack of Docker layer caching.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Every Go package must maintain $\ge 80\%$ code coverage. Unit tests focus on business logic in isolation, using `mock` libraries for gRPC clients and database connections.
- **Tooling:** `go test`, `testify/mock`.

### 7.2 Integration Testing
Integration tests verify the interaction between microservices and the database. These tests are run in the Staging environment.
- **Focus:** Kafka message delivery (ensuring a message published by the `FileService` is correctly consumed by the `AnalyticsService`) and CockroachDB transaction integrity.
- **Tooling:** Docker Compose for local integration, Kubernetes for staging.

### 7.3 End-to-End (E2E) Testing
E2E tests simulate the full user journey: a retail operator logging in via SSO, customizing their dashboard, uploading a firmware binary, and seeing the deployment status on the map.
- **Tooling:** Playwright for frontend automation; custom Go scripts for terminal emulation.

### 7.4 PCI DSS Compliance Testing
As the system processes credit card data, we undergo quarterly vulnerability scans and an annual external audit. All tests must prove that raw card data is never stored in the `billing_ledger` or `api_usage_logs`.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | High | High | Hire a specialized contractor to handle the CI pipeline optimization, reducing the "bus factor" and long-term headcount costs. |
| R-02 | Competitor is building similar product and is 2 months ahead | Medium | High | Engage an external consultant for an independent market assessment to identify gaps in the competitor's offering. |
| R-03 | CI pipeline latency (45 mins) delays critical hotfixes | High | Medium | Implement parallel test execution and Docker layer caching to reduce build time to < 15 minutes. |
| R-04 | Zero-downtime migration failure (Legacy $\rightarrow$ Juniper) | Low | Critical | Implement a "Canary" rollout where only 1% of terminals are migrated per day, with a 1-click rollback mechanism. |
| R-05 | Failure to pass PCI DSS Level 1 audit | Low | Critical | Monthly internal audits conducted by Devika Moreau and the security consultant. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases
1.  **Phase 1: Foundation (Now - April 2026):** Focus on core microservices, CockroachDB setup, and the critical Dashboard feature.
2.  **Phase 2: Hardening (April 2026 - June 2026):** Focus on security, PCI compliance, and SSO integration.
3.  **Phase 3: Rollout (June 2026 - August 2026):** Gradual migration of retail terminals from legacy to Juniper.

### 9.2 Key Milestones
- **Milestone 1: MVP Feature-Complete (2026-04-15)**
  - All 5 core features implemented.
  - Internal Alpha testing completed.
  - *Dependency:* Budget approval for critical tool purchase.
- **Milestone 2: Architecture Review Complete (2026-06-15)**
  - External security audit completed.
  - Load testing at $10\times$ expected peak traffic.
  - *Dependency:* Completion of the API rate-limiting feature.
- **Milestone 3: Post-launch Stability Confirmed (2026-08-15)**
  - 10,000 Monthly Active Users (MAU) reached.
  - Zero critical (P0) bugs in production for 30 consecutive days.
  - *Dependency:* Successful migration of all legacy terminals.

---

## 10. MEETING NOTES
*Note: These are excerpts from the shared 200-page unsearchable running document.*

### Meeting 1: Budgetary Constraints and Tooling
**Date:** 2023-11-02
**Attendees:** Aaliya Costa, Maeve Costa, Bodhi Santos
**Discussion:**
- Aaliya mentioned that the $150k budget is extremely tight. Every single GCP instance must be sized for the minimum requirement.
- Bodhi raised the issue of the "Critical Tool Purchase" (a specialized firmware debugger). Aaliya confirmed the request is still pending approval from the CFO.
- Maeve expressed frustration over the CI pipeline taking 45 minutes. Aaliya suggested that if the budget is cut, we might need a contractor specifically for DevOps to fix this, as the core team is focused on features.
- **Decision:** Focus on the Dashboard first as it is the primary launch blocker.

### Meeting 2: Competitive Pressure and Strategy
**Date:** 2023-12-15
**Attendees:** Aaliya Costa, Devika Moreau
**Discussion:**
- Aaliya warned that the competitor "ApexRetail" is roughly 2 months ahead of us in the firmware replacement race.
- Devika noted that while they are faster, their security posture is rumored to be weak. We can win on the "PCI DSS Level 1" guarantee.
- Aaliya decided to engage an external consultant to perform a gap analysis between Juniper and ApexRetail.
- **Decision:** Prioritize the "Security Audit" milestone to make it a primary marketing advantage.

### Meeting 3: Deployment Strategy for Zero Downtime
**Date:** 2024-01-20
**Attendees:** Aaliya Costa, Maeve Costa, Devika Moreau
**Discussion:**
- Maeve proposed a Blue-Green deployment using Kubernetes.
- Devika voiced concerns about data consistency during the switch. If a terminal is halfway through a transaction on the legacy system, we cannot just cut the cord.
- They discussed using a "Dual-Write" period where the legacy system and Juniper both receive data for 48 hours.
- **Decision:** Implement a "Dual-Write" bridge for the migration phase to ensure zero downtime.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$150,000.00**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $90,000 | Distributed team (Aaliya, Maeve, Devika, Bodhi + 11 others). |
| **Infrastructure** | 20% | $30,000 | GCP Credits, GKE, CockroachDB Cloud, Kafka managed services. |
| **Tools & Licensing**| 10% | $15,000 | Debugging tools (Pending Approval), IDE licenses, Security scanners. |
| **Contingency** | 10% | $15,000 | Reserved for external consultants and emergency contractor hire. |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To pass the external audit on the first attempt, Project Juniper must adhere to the following:
1.  **Network Segmentation:** The gRPC traffic for payment processing must be isolated from the dashboard telemetry traffic via Kubernetes Network Policies.
2.  **Encryption:** All data in transit must use TLS 1.3. All data at rest in CockroachDB must use AES-256.
3.  **Access Control:** The `audit_logs` table must be append-only; no user, including the `admin` role, shall have `DELETE` or `UPDATE` permissions on this table.
4.  **Key Management:** Integration with GCP KMS (Key Management Service) for rotating encryption keys every 90 days.

### Appendix B: CI Pipeline Optimization Roadmap
To address the 45-minute build time, the following tasks are scheduled for the DevOps contractor:
1.  **Parallelization:** Split the integration test suite into 4 parallel shards using GitHub Action Matrix.
2.  **Caching:** Implement `actions/cache` for Go modules and Docker layer caching using the GCR (Google Container Registry) cache.
3.  **Incremental Builds:** Modify the build script to only compile microservices that have changed in the current PR, rather than recompiling the entire monolith of services.
4.  **Expected Result:** Reduce total pipeline time from 45 minutes to $\approx 12$ minutes.