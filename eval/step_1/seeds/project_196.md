# Project Specification Document: Project Cairn
**Version:** 1.0.4  
**Status:** Final Baseline  
**Date:** October 24, 2025  
**Company:** Iron Bay Technologies  
**Classification:** Confidential / PCI DSS Level 1 Restricted  

---

## 1. Executive Summary

### 1.1 Project Overview
Project Cairn is a mission-critical embedded systems firmware initiative commissioned by Iron Bay Technologies to ensure the company’s real estate portfolio management hardware remains compliant with the impending "Real Estate Digital Standards Act of 2026." The project involves a complete overhaul of the firmware residing on edge-gateway devices used for smart-lock management, HVAC metering, and tenant billing in commercial real estate properties.

Due to the nature of the regulatory requirements, Cairn is subject to a hard legal deadline. Failure to deploy the compliant firmware by the statutory date would result in immediate cease-and-desist orders for current operations and liquidated damages estimated at $250,000 per day of non-compliance.

### 1.2 Business Justification
The legacy system currently employed by Iron Bay Technologies suffers from significant overhead, high latency, and an inability to process encrypted payment data at the edge. By transitioning to a Rust-based firmware architecture, the company aims to achieve a drastic reduction in operational costs. The transition from a monolithic legacy C++ codebase to a modular Rust framework allows for memory safety and concurrency, which are essential for the new high-throughput requirements.

The primary driver is the necessity for PCI DSS Level 1 compliance. The new system will process credit card data directly at the edge for automated tenant billing, removing the need for expensive third-party middle-ware proxies that currently inflate transaction costs.

### 1.3 ROI Projection
The Return on Investment (ROI) for Project Cairn is calculated based on two primary vectors: cost reduction and risk mitigation.

1.  **Transaction Cost Reduction:** The current legacy system incurs a processing fee of $0.45 per transaction due to outdated gateway routing. The new architecture targets a cost per transaction of $0.29 or lower, representing a **35% reduction**. Given the volume of 1.2 million transactions per month, this results in a monthly saving of $192,000.
2.  **Regulatory Cost Avoidance:** The avoidance of potential fines and the ability to continue operating in key markets (specifically the EU and North American markets) provide an intangible but critical value.
3.  **Infrastructure Optimization:** By utilizing Cloudflare Workers for the control plane, Iron Bay Technologies expects to reduce cloud compute spend by 22% annually.

The total projected ROI over the first 24 months post-launch is estimated at $5.1M, accounting for the initial development spend and hardware refresh costs.

---

## 2. Technical Architecture

### 2.1 System Overview
Project Cairn utilizes a hybrid architecture designed for high reliability and low latency. The "Edge" consists of embedded devices running a Rust-based firmware, communicating with a global control plane hosted on Cloudflare Workers.

**The Stack:**
- **Firmware/Backend:** Rust (using the `tokio` runtime for async I/O and `serde` for serialization).
- **Frontend:** React 18 (deployed as a Single Page Application for the management dashboard).
- **Edge Storage:** SQLite (used for local state persistence and write-ahead logging).
- **Cloud Layer:** Cloudflare Workers (providing a serverless API gateway and routing).
- **Database (Cloud):** Distributed SQLite/D1 for global configuration and tenant metadata.

### 2.2 Architecture Philosophy: The Incremental Modular Monolith
The system is designed as a **Modular Monolith**. This means that while the code resides in a single repository for ease of deployment and atomic commits, the internal logic is strictly decoupled into crates. As the system scales, these crates can be extracted into separate microservices without rewriting the business logic.

### 2.3 Data Flow Diagram (ASCII Representation)
```text
[Physical Device] <---(SPI/I2C)---> [Embedded Rust Firmware]
                                           |
                                           | (mTLS / HTTPS)
                                           v
[Local SQLite DB] <----------------> [Edge Logic Layer]
                                           |
                                           | (JSON-RPC over WebSocket)
                                           v
[Cloudflare Worker] <--------------> [Global State / D1 DB]
       |                                    |
       | (REST API)                         |
       v                                    v
[React Dashboard] <------------------> [Admin / Support Portal]
```

### 2.4 Security Architecture (PCI DSS Level 1)
Because Cairn processes credit card data directly, the firmware implements a "Secure Enclave" pattern. 
- **Encryption at Rest:** All SQLite databases on the edge are encrypted using AES-256-GCM.
- **Encryption in Transit:** All communication between the device and the Cloudflare Worker is encrypted via TLS 1.3 with mutual authentication (mTLS).
- **Key Management:** Hardware Security Modules (HSMs) are used to store the root of trust; keys are never exposed in the application memory space.

---

## 3. Detailed Feature Specifications

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Design

**Description:**
To prevent Denial of Service (DoS) attacks on the edge devices and to provide a billing basis for "Premium" real estate tiers, the system must implement a sophisticated rate-limiting mechanism. This feature is not merely a global cap but a tiered system based on the tenant's subscription level.

**Functional Requirements:**
- **Token Bucket Algorithm:** Implement a token bucket algorithm at the Cloudflare Worker level to track requests per API key.
- **Dynamic Quotas:** The system must support three tiers: *Basic* (100 req/min), *Professional* (1,000 req/min), and *Enterprise* (Unlimited).
- **Analytics Pipeline:** Every request must be logged with a timestamp, endpoint, latency, and status code. These logs are aggregated into the SQLite edge database and synced to the cloud every 60 seconds.
- **Over-limit Handling:** When a limit is exceeded, the API must return a `429 Too Many Requests` response with a `Retry-After` header.

**Technical Implementation:**
The rate limiter will utilize Cloudflare KV (Key-Value) storage for ultra-low latency lookups. The analytics engine will use a background worker to process logs in batches to avoid impacting the request-response cycle.

---

### 3.2 Real-time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Not Started

**Description:**
Property managers often need to configure device settings (e.g., HVAC schedules) simultaneously. The "Cairn Configurator" requires a real-time collaborative interface where multiple users can edit a single configuration file without overwriting each other's changes.

**Functional Requirements:**
- **CRDT Implementation:** Use Conflict-free Replicated Data Types (CRDTs) to ensure that all clients eventually converge to the same state regardless of the order of operations.
- **Operational Transformation (OT):** For text-based configuration notes, an OT approach will be used to handle character-level insertions and deletions.
- **Presence Indicators:** The React frontend must display "User X is editing this field" in real-time.
- **Version History:** Every converged state must be snapshotted, allowing users to roll back to a previous "known-good" configuration.

**Technical Implementation:**
The system will utilize WebSockets for the transport layer. The Rust backend will maintain a "State Tree" for each device. When a change is pushed, the backend will apply the CRDT logic and broadcast the delta to all connected clients.

---

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low | **Status:** Not Started

**Description:**
This is a "nice-to-have" feature for the end-user experience. The goal is to allow property managers to customize their primary view based on the metrics they care about most (e.g., energy consumption vs. security alerts).

**Functional Requirements:**
- **Widget Library:** Provide a set of pre-built widgets: *Device Status, Energy Graph, Recent Alerts, Tenant Billing Summary*.
- **Grid Layout:** Implement a draggable grid system (using `react-grid-layout`) where widgets can be resized and repositioned.
- **Persistence:** The layout configuration must be saved to the user's profile in the cloud database so the dashboard remains consistent across different sessions.
- **Dynamic Data Binding:** Widgets must poll the API at different intervals based on the data's volatility.

**Technical Implementation:**
The dashboard state will be stored as a JSON blob in the `user_preferences` table. The frontend will map this JSON to a set of React components, injecting the necessary API endpoints into each widget via a Context Provider.

---

### 3.4 Multi-tenant Data Isolation with Shared Infrastructure
**Priority:** Medium | **Status:** Complete

**Description:**
As a real estate solution, Cairn must host data for multiple different property management companies (tenants) on the same physical infrastructure while ensuring that no company can ever access another's data.

**Functional Requirements:**
- **Logical Isolation:** Every table in the database contains a `tenant_id` column. All queries are strictly filtered by this ID.
- **Row-Level Security (RLS):** Implement RLS at the database layer to prevent accidental data leakage.
- **Tenant-Specific Encryption Keys:** While the infrastructure is shared, the data for each tenant is encrypted using a unique key derived from the tenant's master secret.
- **Resource Quotas:** Ensure that one tenant cannot consume all the available SQLite storage on an edge device, preventing "noisy neighbor" issues.

**Technical Implementation:**
The team implemented a middleware layer in Rust that extracts the `tenant_id` from the JWT (JSON Web Token) of the request and injects it into the SQL `WHERE` clause of every single database transaction.

---

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Critical | **Status:** Not Started

**Description:**
Cairn is being deployed globally. To meet regulatory requirements in the EU and Asia, the firmware's administrative interface and the cloud dashboard must support 12 different languages. This is a launch blocker.

**Functional Requirements:**
- **Translation Keys:** All UI text must be extracted into JSON translation files (`en.json`, `fr.json`, `de.json`, etc.).
- **Dynamic Locale Switching:** Users must be able to change their language preference in the settings, with the UI updating instantly without a page reload.
- **Right-to-Left (RTL) Support:** The React frontend must support RTL layouts for languages such as Arabic.
- **Local Date/Currency Formatting:** The system must format dates, times, and currency symbols according to the user's locale (e.g., USD vs. EUR).

**Technical Implementation:**
The frontend will use `i18next` for translation management. The firmware will store a `locale` setting in the SQLite database and serve the corresponding translation bundle to the React frontend during the initial handshake.

---

## 4. API Endpoint Documentation

All endpoints are hosted under the base path: `https://api.cairn.ironbay.tech/v1/`

### 4.1 Device Heartbeat
- **Endpoint:** `POST /device/heartbeat`
- **Description:** Sent by the firmware every 30 seconds to indicate health.
- **Request:**
  ```json
  {
    "device_id": "C-99821",
    "status": "healthy",
    "uptime": 120500,
    "firmware_version": "1.0.4"
  }
  ```
- **Response:** `200 OK` | `{ "ack": true, "update_available": false }`

### 4.2 Process Payment
- **Endpoint:** `POST /payment/process`
- **Description:** Initiates a PCI-compliant transaction at the edge.
- **Request:**
  ```json
  {
    "tenant_id": "T-552",
    "amount": 1200.00,
    "currency": "USD",
    "encrypted_payload": "base64_encrypted_card_data"
  }
  ```
- **Response:** `201 Created` | `{ "transaction_id": "TX-1002", "status": "captured" }`

### 4.3 Update Configuration
- **Endpoint:** `PATCH /device/config`
- **Description:** Updates the device settings via the collaborative editor.
- **Request:**
  ```json
  {
    "config_id": "CFG-11",
    "changes": { "hvac_threshold": 22.5 },
    "version_tag": "v12"
  }
  ```
- **Response:** `200 OK` | `{ "status": "applied", "current_version": "v13" }`

### 4.4 Get Usage Analytics
- **Endpoint:** `GET /analytics/usage?tenant_id={id}`
- **Description:** Retrieves rate-limiting and usage data for a specific tenant.
- **Response:** `200 OK` | `{ "total_requests": 45000, "blocked_requests": 120, "avg_latency": "45ms" }`

### 4.5 Set Locale
- **Endpoint:** `PUT /user/settings/locale`
- **Description:** Updates the user's language preference.
- **Request:** `{ "locale": "de-DE" }`
- **Response:** `200 OK` | `{ "status": "updated", "locale": "de-DE" }`

### 4.6 Get Device List
- **Endpoint:** `GET /devices`
- **Description:** Returns all devices associated with the authenticated tenant.
- **Response:** `200 OK` | `[ { "id": "C-1", "name": "North Tower", "status": "online" }, ... ]`

### 4.7 Trigger Emergency Lock
- **Endpoint:** `POST /device/lock-all`
- **Description:** Immediate lockdown of all devices for a specific property.
- **Request:** `{ "property_id": "P-88", "reason": "Security Breach" }`
- **Response:** `202 Accepted` | `{ "job_id": "JOB-991", "status": "dispatching" }`

### 4.8 Fetch Billing History
- **Endpoint:** `GET /billing/history`
- **Description:** Retrieves a list of all transactions for the current tenant.
- **Response:** `200 OK` | `[ { "tx_id": "TX-1", "amount": 50.00, "date": "2025-10-01" }, ... ]`

---

## 5. Database Schema

The system uses a shared-schema approach with `tenant_id` for isolation.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | None | `name`, `plan_tier`, `created_at` | Root tenant identity |
| `users` | `user_id` | `tenant_id` | `email`, `password_hash`, `role` | User accounts |
| `devices` | `device_id` | `tenant_id` | `model_no`, `firmware_ver`, `ip_address` | Registered hardware |
| `device_configs` | `config_id` | `device_id` | `config_json`, `version`, `updated_at` | Device settings |
| `transactions` | `tx_id` | `tenant_id`, `device_id` | `amount`, `status`, `timestamp` | Billing records |
| `usage_logs` | `log_id` | `tenant_id` | `endpoint`, `latency`, `timestamp` | API analytics |
| `locale_settings`| `setting_id`| `user_id` | `language_code`, `timezone`, `currency` | User preferences |
| `audit_logs` | `audit_id` | `user_id` | `action`, `target_id`, `timestamp` | PCI DSS Audit trail |
| `widgets` | `widget_id` | `user_id` | `widget_type`, `position_x`, `position_y` | Dashboard layout |
| `firmware_updates`| `update_id` | None | `version_tag`, `checksum`, `release_date` | Firmware versioning |

### 5.2 Relationships
- **One-to-Many:** `tenants` $\rightarrow$ `users`, `tenants` $\rightarrow$ `devices`, `tenants` $\rightarrow$ `transactions`.
- **One-to-One:** `users` $\rightarrow$ `locale_settings`.
- **One-to-Many:** `devices` $\rightarrow$ `device_configs`.
- **Many-to-One:** `audit_logs` $\rightarrow$ `users`.

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Project Cairn utilizes a Three-Tier environment strategy to ensure stability before production release.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature iteration and unit testing.
- **Deployment:** Triggered on push to `develop` branch.
- **Infrastructure:** Local Docker containers and a shared Dev Cloudflare Worker.
- **Data:** Mock data; sanitized snapshots of production.

#### 6.1.2 Staging (Staging)
- **Purpose:** Integration testing and QA sign-off.
- **Deployment:** Triggered on merge to `release/vX.X`.
- **Infrastructure:** Mirror of production hardware (10 test devices in the lab).
- **Data:** Anonymized production data.

#### 6.1.3 Production (Prod)
- **Purpose:** Live customer operations.
- **Deployment:** Continuous Deployment (CD). Every merged PR to `main` is deployed.
- **Infrastructure:** Global Cloudflare network and field-deployed edge hardware.
- **Data:** Live encrypted tenant data.

### 6.2 Continuous Deployment Pipeline
The pipeline is managed via GitHub Actions:
1. **Lint/Test:** Run `cargo test` and `npm test`.
2. **Build:** Compile Rust to WebAssembly (WASM) for Workers and AArch64 for devices.
3. **Deploy:** `wrangler deploy` for Workers; Over-the-Air (OTA) update push for firmware.
4. **Smoke Test:** Automated health checks on `/device/heartbeat`.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Backend:** Every Rust module must have a corresponding `tests` module. We target 85% code coverage.
- **Frontend:** Jest and React Testing Library for component-level validation.
- **Scope:** Pure functions, data transformations, and state transitions.

### 7.2 Integration Testing
- **API Tests:** Postman/Newman collections are run against the Staging environment to verify endpoint contracts.
- **Hardware-in-the-Loop (HIL):** A dedicated test rig at Iron Bay HQ where firmware is flashed onto actual devices to test SPI/I2C communication with sensors.
- **Database Integrity:** Scripts to verify that `tenant_id` isolation is never breached (Attempting to query Tenant B data with Tenant A credentials must return `403 Forbidden`).

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright is used to simulate a property manager's journey: *Login $\rightarrow$ Dashboard $\rightarrow$ Update Config $\rightarrow$ Verify Device Status*.
- **PCI Compliance Testing:** Third-party penetration testing is scheduled for the end of Milestone 2 to ensure PCI DSS Level 1 requirements are met.

---

## 8. Risk Register

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key architect is leaving in 3 months | High | Critical | **Parallel-Path:** Prototype an alternative architecture simultaneously; aggressive knowledge transfer sessions. |
| **R-02** | Vendor EOL (End of Life) for primary chip | Medium | High | **De-scope:** Identify features dependent on the chip; if no replacement is found, remove those features from the MVP. |
| **R-03** | Design disagreement (Product vs. Eng) | High | Medium | **Arbitration:** Weekly syncs with Arun Santos to make final executive decisions on trade-offs. |
| **R-04** | Failure to pass external PCI audit | Low | Critical | **Pre-Audit:** Engage a consultant for a "mock audit" 4 weeks before the official audit. |
| **R-05** | Localization delays (12 languages) | Medium | High | **Prioritize:** Focus on top 3 languages first (English, German, French) to meet minimum viable launch. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal action.
- **High:** Significant delay or cost overrun.
- **Medium:** Minor feature compromise.
- **Low:** Negligible effect.

---

## 9. Timeline and Phases

The project is divided into three primary milestones.

### 9.1 Phase 1: Foundations & Alpha (Oct 2025 - March 2026)
- **Focus:** Core architecture, multi-tenant isolation, and basic API.
- **Dependencies:** Hardware prototype availability.
- **Target Date:** 2026-03-15 (Internal Alpha Release).
- **Key Deliverable:** Stable firmware flashing on test devices with cloud connectivity.

### 9.2 Phase 2: Compliance & Production (March 2026 - May 2026)
- **Focus:** PCI DSS implementation, L10n/I18n, and security hardening.
- **Dependencies:** External auditor availability.
- **Target Date:** 2026-05-15 (Production Launch).
- **Key Deliverable:** Passing external audit and deployment to first 100 live sites.

### 9.3 Phase 3: Feature Completion & Optimization (May 2026 - July 2026)
- **Focus:** Collaborative editing, analytics, and dashboard widgets.
- **Dependencies:** User feedback from Phase 2.
- **Target Date:** 2026-07-15 (MVP Feature-Complete).
- **Key Deliverable:** Full feature set enabled for all professional/enterprise tiers.

---

## 10. Meeting Notes

### Meeting 1: Architecture Alignment
**Date:** 2025-10-15  
**Attendees:** Arun Santos, Ilya Santos, Alejandro Costa, Brigid Fischer  
**Discussion:**  
The team discussed the transition from a monolithic C++ core to Rust. Alejandro raised concerns about the learning curve for the support team. Ilya argued that the memory safety of Rust is non-negotiable for PCI compliance. Arun noted the tension between the desire for a "perfect" microservices architecture and the hard legal deadline.  
**Decisions:**  
1. Adopt the "Modular Monolith" approach to balance speed and scalability.  
2. All new development will be in Rust; legacy C++ will be wrapped in FFI (Foreign Function Interface) only where absolutely necessary.  
**Action Items:**  
- Ilya: Set up the Rust workspace and CI/CD pipeline. (Due: 2025-10-22)  
- Alejandro: Create the initial QA test suite for the heartbeat API. (Due: 2025-10-25)

### Meeting 2: Vendor EOL Crisis Management
**Date:** 2025-11-02  
**Attendees:** Arun Santos, Ilya Santos, Brigid Fischer  
**Discussion:**  
The primary sensor vendor announced EOL for the `XJ-900` series. Brigid reported that 30% of current hardware uses these sensors. Ilya proposed a software-level abstraction layer (HAL) to allow for a quick swap to the `Y-Series` sensors from a competitor.  
**Decisions:**  
1. Create a Hardware Abstraction Layer (HAL) in Rust.  
2. If the `Y-Series` sensors are not compatible by Milestone 2, the "Advanced Metering" feature will be de-scoped.  
**Action Items:**  
- Ilya: Develop a prototype HAL for the `Y-Series` sensor. (Due: 2025-11-15)  
- Arun: Negotiate bulk pricing with the new sensor vendor. (Due: 2025-11-20)

### Meeting 3: Localization and Launch Blockers
**Date:** 2025-12-10  
**Attendees:** Arun Santos, Alejandro Costa, Brigid Fischer  
**Discussion:**  
Alejandro pointed out that the current UI is hard-coded in English, which is a blocker for the EU launch. Brigid suggested using a third-party translation service to speed up the process. Arun expressed a concern regarding the budget for professional translation across 12 languages.  
**Decisions:**  
1. Prioritize English, French, and German for the May 15th launch.  
2. Use `i18next` for the frontend.  
3. Remaining 9 languages will be added iteratively through July.  
**Action Items:**  
- Brigid: Source a translation vendor for the primary 3 languages. (Due: 2025-12-20)  
- Alejandro: Implement the locale-switching logic in the React frontend. (Due: 2026-01-05)

---

## 11. Budget Breakdown

Funding is released in tranches upon the completion of milestones.

| Category | Allocation | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Salaries & Benefits | $450,000 | 3 FTEs + Project Lead for 9 months |
| **Infrastructure** | Cloudflare, D1, KV | $45,000 | Estimated for Dev/Staging/Prod |
| **Hardware** | Prototypes & Sensors | $80,000 | Includes transition to `Y-Series` sensors |
| **Tools** | IDEs, CI/CD, Testing Tools | $12,000 | GitHub Enterprise, JetBrains, Playwright |
| **Compliance** | External PCI Audit | $60,000 | Flat fee for first-attempt certification |
| **Contingency** | Emergency Buffer | $100,000 | Reserved for critical risk mitigation |
| **Total** | | **$747,000** | |

**Funding Tranches:**
- **Tranche 1 (Alpha):** $300,000 (Released Oct 2025)
- **Tranche 2 (Production):** $300,000 (Released March 2026)
- **Tranche 3 (Completion):** $147,000 (Released May 2026)

---

## 12. Appendices

### Appendix A: Rust Crate Map
To maintain the modular monolith, the project is split into the following crates:
- `cairn-core`: Common types, error handling, and constants.
- `cairn-crypto`: AES-256-GCM and mTLS implementation.
- `cairn-edge-db`: SQLite wrappers and migration logic.
- `cairn-api`: JSON-RPC handlers and Cloudflare Worker interfaces.
- `cairn-hal`: Hardware Abstraction Layer for sensors and locks.
- `cairn-billing`: PCI-compliant payment processing logic.

### Appendix B: PCI DSS Level 1 Checklist for Firmware
The firmware must adhere to the following technical controls to pass the audit:
1. **No Plaintext PAN:** Primary Account Numbers (PAN) must never be stored in plaintext in the SQLite database.
2. **Strong Cryptography:** Use only TLS 1.3 for external communication.
3. **Unique Credentials:** Every device must have a unique certificate; shared keys are forbidden.
4. **Logging:** Every access to payment-related memory must be logged to the `audit_logs` table.
5. **Automatic Session Timeout:** Management sessions must expire after 15 minutes of inactivity.