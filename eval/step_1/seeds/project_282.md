# PROJECT SPECIFICATION DOCUMENT: PROJECT BEACON
**Document Version:** 1.0.4  
**Status:** Final Baseline  
**Date:** October 24, 2025  
**Classification:** Confidential – Internal Hearthstone Software Use Only  
**Project Lead:** Yves Gupta (Tech Lead)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Beacon" is a strategic initiative by Hearthstone Software to enter the high-stakes cybersecurity collaboration market. Beacon is designed as a real-time collaboration tool specifically engineered for security operations centers (SOCs), incident response teams, and government cybersecurity agencies. Unlike general-purpose collaboration tools, Beacon integrates deep auditing, FedRAMP-compliant security controls, and high-availability synchronization to allow analysts to coordinate responses to active threats in real-time without compromising the chain of custody for evidence.

### 1.2 Business Justification
The driver for Beacon is a high-value partnership with a single enterprise client—a major government contractor—who has committed to a Service Level Agreement (SLA) providing $2,000,000 in annual recurring revenue (ARR). The client requires a tool that bridges the gap between secure chat and formal incident reporting, ensuring that all collaborative actions are immutable and auditable.

The entry into this vertical allows Hearthstone Software to pivot from general enterprise software into the specialized cybersecurity domain, creating a moat of "security-first" engineering that can be leveraged to attract further government and defense contracts.

### 1.3 ROI Projection
The financial viability of Beacon is exceptionally strong due to the immediate anchor tenant.
- **Initial Investment:** $800,000 (Total Budget).
- **Year 1 Revenue:** $2,000,000 (Guaranteed by anchor client).
- **Gross Profit (Year 1):** $1,200,000.
- **Return on Investment (ROI):** 150% within the first 12 months.
- **Long-term Projection:** By expanding the product to four additional government entities at a similar price point, the vertical is projected to generate $10M ARR by Year 3, with a marginal cost of maintenance estimated at 15% of revenue.

### 1.4 Strategic Alignment
Beacon aligns with Hearthstone’s mission to provide "Hardened Infrastructure for Critical Workflows." By implementing a CQRS (Command Query Responsibility Segregation) architecture and event sourcing, the project sets a new internal standard for data integrity and auditability across all company products.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Beacon is built on a "Mixed Stack" strategy. Because Hearthstone is leveraging existing internal libraries and legacy modules to accelerate development, the system must interoperate across three distinct technology stacks:
1. **Legacy Core (Java/Spring Boot):** Handles heavy-duty data processing and legacy database connectors.
2. **Real-time Layer (Node.js/TypeScript):** Manages WebSocket connections and the collaboration engine using Socket.io.
3. **Frontend (React/TypeScript):** A modern SPA providing a low-latency, responsive interface.

### 2.2 CQRS and Event Sourcing
To satisfy the extreme audit requirements of the cybersecurity industry, Beacon utilizes **Command Query Responsibility Segregation (CQRS)**. 

- **Command Side:** Every action (e.g., "Update Incident Status") is treated as a command. These commands are validated and then persisted as an immutable sequence of events in an **Event Store**.
- **Query Side:** Event handlers listen to the event stream and update "Read Models" (materialized views) in a separate database optimized for fast retrieval.
- **Auditability:** Because the state is derived from events, the system can "replay" the state of a collaboration session at any specific millisecond, providing a perfect forensic trail.

### 2.3 ASCII Architecture Diagram
The following diagram represents the flow of a user action through the system.

```text
[ User Client ] <---(WebSocket/HTTPS)---> [ API Gateway/Nginx ]
                                              |
                                              v
                        +---------------------------------------------+
                        |             Orchestration Layer             |
                        | (Node.js / Spring Boot Hybrid / LaunchDarkly)|
                        +---------------------------------------------+
                               /                              \
                     [ Command Service ]                [ Query Service ]
                            |                                  |
                            v                                  v
                +-----------------------+            +-----------------------+
                |    Event Store (DB)   |            |   Read Models (DB)   |
                | (Append-only Journal) |            | (Optimized for UI)    |
                +-----------------------+            +-----------------------+
                            |                                  ^
                            +----[ Event Projectionist ]-------+
                                     (Updates Read Model)
```

### 2.4 Deployment Strategy
Deployment is managed via a sophisticated pipeline to ensure zero downtime and risk mitigation:
- **Feature Flags:** All new logic is wrapped in **LaunchDarkly** flags. This allows the team to decouple deployment (pushing code to prod) from release (turning the feature on for users).
- **Canary Releases:** New versions are deployed to 5% of the user base initially. Metrics are monitored for 2 hours; if error rates increase by >1%, the canary is automatically killed.
- **Environment Isolation:** Strictly separated Dev, Staging, and Production environments, with the Production environment residing in a FedRAMP-authorized AWS GovCloud region.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Priority: High | Status: In Progress)
**Description:**
The A/B testing framework is not a standalone product but is "baked into" the existing LaunchDarkly feature flag system. It allows the product team to serve different versions of a feature to specific user segments to determine which version improves security analyst efficiency.

**Functional Specifications:**
- **Segment Definition:** Ability to define cohorts based on user roles (e.g., "Tier 1 Analyst" vs "SOC Manager").
- **Variant Assignment:** The system will assign users to `Variant A` (Control) or `Variant B` (Test) based on a deterministic hash of the UserID to ensure consistency across sessions.
- **Telemetry Integration:** Every event emitted by the client must include the current active feature flag variant ID.
- **Metric Tracking:** Integration with the internal analytics engine to track "Time to Resolution" (TTR) as the primary KPI for A/B tests.

**Technical Implementation:**
- Use the LaunchDarkly SDK to fetch target segments.
- Implement a middleware in the Node.js layer that intercepts requests and attaches the active variant ID to the request context.
- A custom dashboard in the React frontend will display the delta in TTR between variants.

**Acceptance Criteria:**
- A user must consistently see the same variant across different devices.
- The system must support up to 5 variants per feature flag.
- Statistical significance (p < 0.05) must be calculable via the analytics export.

---

### 3.2 Data Import/Export with Format Auto-Detection (Priority: Critical | Status: Not Started)
**Description:**
This is a **launch blocker**. Security analysts often need to ingest logs, incident reports, and evidence from various external tools (Splunk, CrowdStrike, ServiceNow) and export them for legal discovery.

**Functional Specifications:**
- **Auto-Detection Engine:** The system must analyze the first 10KB of an uploaded file to determine its format (JSON, CSV, XML, STIX, or TAXII).
- **Mapping Engine:** A configurable mapping layer that translates external fields (e.g., `src_ip` from Splunk) to Beacon’s internal schema (`source_address`).
- **Bulk Export:** Ability to export entire collaboration threads, including event history and attached artifacts, into a cryptographically signed PDF or JSON bundle.
- **Validation:** Automatic validation of imported data against the internal schema to prevent "poisoning" the event store.

**Technical Implementation:**
- **Backend:** A Python-based microservice using `pandas` for data manipulation and `magic` for MIME-type detection.
- **Pipeline:** Import $\rightarrow$ Auto-detect $\rightarrow$ Mapping $\rightarrow$ Validation $\rightarrow$ Event Store Commit.
- **API:** Use a multipart upload endpoint with a streaming parser to handle files up to 2GB.

**Acceptance Criteria:**
- Successfully detect and import 5 standard cybersecurity formats.
- Exported files must include a SHA-256 checksum for integrity verification.
- Import errors must provide line-specific feedback (e.g., "Row 45: Invalid IP address format").

---

### 3.3 Localization and Internationalization (Priority: Critical | Status: Not Started)
**Description:**
This is a **launch blocker**. To meet government requirements and global deployment targets, Beacon must support 12 languages (English, French, German, Spanish, Chinese, Japanese, Korean, Arabic, Russian, Portuguese, Italian, and Dutch).

**Functional Specifications:**
- **Dynamic Switching:** Users can change their language preference in settings without refreshing the page.
- **RTL Support:** Full support for Right-to-Left (RTL) layouts for Arabic.
- **Date/Time Localization:** All timestamps must be displayed in the user's local timezone but stored in UTC.
- **Translation Management:** Integration with a translation management system (TMS) to allow non-developers to update copy.

**Technical Implementation:**
- **Frontend:** Use `react-i18next` for translation management.
- **Storage:** Translation keys stored in JSON files, hosted on a CDN for fast updates.
- **Backend:** The `Accept-Language` header will be used to send localized error messages from the server.

**Acceptance Criteria:**
- No "hard-coded" strings in the UI.
- UI elements must not break/overlap when longer German or Russian strings are used.
- RTL layout must correctly mirror the navigation sidebar and chat windows.

---

### 3.4 Customer-Facing API with Versioning and Sandbox (Priority: Low | Status: Not Started)
**Description:**
A "nice-to-have" feature that allows enterprise clients to automate the creation of "Beacon Rooms" or ingest alerts from their own proprietary software.

**Functional Specifications:**
- **API Versioning:** Use URL-based versioning (e.g., `/api/v1/`, `/api/v2/`).
- **Sandbox Environment:** A separate, isolated environment where clients can test API calls without affecting production data.
- **API Key Management:** A self-service portal for generating, rotating, and revoking API keys.
- **Rate Limiting:** Tiered rate limiting (e.g., 100 requests/min for standard, 1000 for premium).

**Technical Implementation:**
- **Gateway:** Use Kong or AWS API Gateway for rate limiting and key validation.
- **Documentation:** Auto-generated Swagger/OpenAPI documentation.
- **Sandbox:** A mirrored deployment of the stack using a separate "Sandbox" database instance.

**Acceptance Criteria:**
- Ability to create a collaboration room via POST request.
- Sandbox API calls must never write to the Production Event Store.
- API keys must be encrypted at rest using AES-256.

---

### 3.5 User Authentication and RBAC (Priority: Medium | Status: In Progress)
**Description:**
A secure identity management system that ensures only authorized personnel can access sensitive cybersecurity data.

**Functional Specifications:**
- **Multi-Factor Authentication (MFA):** Mandatory MFA using TOTP (Time-based One-Time Password) or hardware keys (YubiKey).
- **Role-Based Access Control (RBAC):** Granular permissions (e.g., `Viewer`, `Editor`, `Administrator`, `Auditor`).
- **SSO Integration:** Support for SAML 2.0 and OIDC (OpenID Connect) for integration with Active Directory.
- **Session Management:** Absolute session timeouts (8 hours) and idle timeouts (30 minutes).

**Technical Implementation:**
- **Identity Provider:** Integration with Keycloak for managing identities and roles.
- **JWTs:** Use signed JSON Web Tokens for session state, with short expiration times and refresh tokens stored in `httpOnly` cookies.
- **Policy Enforcement:** A middleware layer that checks the user's role against the required permission for every API endpoint.

**Acceptance Criteria:**
- Users without the `Auditor` role cannot access the Event Store replay logs.
- SSO login must redirect successfully to the corporate identity provider.
- MFA must be enforced upon the first login.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow RESTful principles. Base URL: `https://api.beacon.hearthstone.io/v1`

### 4.1 `POST /auth/login`
- **Purpose:** Authenticate user and return session tokens.
- **Request:** `{ "username": "ygupta", "password": "********", "mfa_code": "123456" }`
- **Response (200 OK):** `{ "token": "eyJhb...", "refresh_token": "def456...", "user": { "id": "u1", "role": "Admin" } }`

### 4.2 `GET /rooms`
- **Purpose:** Retrieve a list of collaboration rooms the user has access to.
- **Request:** Headers: `Authorization: Bearer <token>`
- **Response (200 OK):** `[ { "id": "room_01", "name": "Incident-2026-A", "status": "Active" }, ... ]`

### 4.3 `POST /rooms`
- **Purpose:** Create a new collaboration room.
- **Request:** `{ "name": "New Threat Hunt", "visibility": "private", "members": ["u2", "u3"] }`
- **Response (201 Created):** `{ "id": "room_02", "createdAt": "2026-01-12T10:00:00Z" }`

### 4.4 `POST /rooms/{roomId}/events`
- **Purpose:** Append a new event (command) to the room's event stream.
- **Request:** `{ "type": "CHAT_MESSAGE", "payload": { "text": "Analyzing malware sample..." }, "timestamp": "2026-01-12T10:05:00Z" }`
- **Response (202 Accepted):** `{ "eventId": "evt_998", "status": "queued" }`

### 4.5 `GET /rooms/{roomId}/state`
- **Purpose:** Get the current materialized state of a room (Query side of CQRS).
- **Request:** `/rooms/room_01/state`
- **Response (200 OK):** `{ "room": "room_01", "current_status": "Containment", "last_updated": "..." }`

### 4.6 `POST /import/detect`
- **Purpose:** Upload a snippet of data to detect format.
- **Request:** Binary file upload (multipart/form-data).
- **Response (200 OK):** `{ "detected_format": "STIX", "confidence": 0.98, "suggested_mapping": "stix_to_beacon_v1" }`

### 4.7 `GET /audit/logs/{roomId}`
- **Purpose:** Retrieve the full event history for a specific room.
- **Request:** `/audit/logs/room_01?start=...&end=...`
- **Response (200 OK):** `[ { "seq": 1, "user": "u1", "action": "CREATE", "timestamp": "..." }, ... ]`

### 4.8 `PATCH /user/settings/locale`
- **Purpose:** Update the user's preferred language.
- **Request:** `{ "language": "de-DE" }`
- **Response (200 OK):** `{ "status": "updated", "current_locale": "de-DE" }`

---

## 5. DATABASE SCHEMA

Beacon utilizes a polyglot persistence strategy: **PostgreSQL** for the Event Store and Read Models, and **Redis** for real-time session caching.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Description | Relationship |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `mfa_secret`, `role_id` | User identity and credentials. | 1:1 with `user_profiles` |
| `roles` | `role_id` | `role_name`, `permissions_json` | Definition of RBAC roles. | 1:N with `users` |
| `user_profiles` | `profile_id` | `user_id`, `display_name`, `timezone`, `locale` | Non-auth user metadata. | 1:1 with `users` |
| `rooms` | `room_id` | `room_name`, `created_at`, `created_by`, `status` | Collaboration space metadata. | 1:N with `room_events` |
| `room_members` | `membership_id`| `room_id`, `user_id`, `joined_at`, `access_level` | Map of who has access to which room. | N:M `users` $\leftrightarrow$ `rooms` |
| `event_store` | `event_id` | `room_id`, `seq_num`, `event_type`, `payload_json`, `created_at` | **Immutable** journal of all actions. | 1:N with `rooms` |
| `read_model_rooms` | `room_id` | `current_state_json`, `last_event_id`, `version` | Materialized view of room state. | 1:1 with `rooms` |
| `audit_logs` | `log_id` | `user_id`, `action`, `ip_address`, `timestamp` | High-level system access logs. | 1:N with `users` |
| `api_keys` | `key_id` | `user_id`, `hashed_key`, `expires_at`, `is_active` | Tokens for the customer API. | 1:N with `users` |
| `feature_flags` | `flag_id` | `flag_name`, `variant_config`, `enabled_segments` | Local cache of LaunchDarkly states. | N/A |

### 5.2 Relationships
- **Event Sourcing Flow:** The `event_store` is the source of truth. A background process reads `event_store` $\rightarrow$ calculates state $\rightarrow$ updates `read_model_rooms`.
- **Authorization Flow:** Request $\rightarrow$ `users` $\rightarrow$ `roles` $\rightarrow$ `room_members` $\rightarrow$ Grant/Deny access.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

#### 6.1.1 Development (Dev)
- **Purpose:** Individual developer testing and feature integration.
- **Infrastructure:** Dockerized containers running on local workstations or a shared "Dev Cluster" (AWS EKS).
- **Database:** Mocked data or a sanitized subset of staging data.
- **Deployment:** Triggered by push to `develop` branch.

#### 6.1.2 Staging (QA/UAT)
- **Purpose:** Final validation, QA testing, and client UAT.
- **Infrastructure:** Mirror of Production (AWS GovCloud), but scaled down (2 nodes instead of 10).
- **Security:** Full RBAC and MFA enabled; simulates the FedRAMP environment.
- **Deployment:** Triggered by merge to `release` branch.

#### 6.1.3 Production (Prod)
- **Purpose:** Live client environment.
- **Infrastructure:** High-availability AWS GovCloud deployment across 3 Availability Zones.
- **Scale:** Auto-scaling groups for the Node.js API layer; RDS Multi-AZ for the PostgreSQL Event Store.
- **Controls:** No direct SSH access; all changes via CI/CD pipeline.

### 6.2 The FedRAMP Pipeline
Since FedRAMP authorization is required, the infrastructure includes:
- **Encryption:** AES-256 at rest for all databases; TLS 1.3 for all data in transit.
- **Logging:** All system logs are forwarded to a centralized, immutable log aggregator (Splunk Gov).
- **Boundary:** A strict Virtual Private Cloud (VPC) boundary with no public internet access except through the API Gateway.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Target:** Individual functions, mapping logic, and event handlers.
- **Tooling:** Jest (Node.js), JUnit (Java).
- **Requirement:** 80% code coverage minimum for all new features.
- **Frequency:** Executed on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Target:** Interaction between the three stacks (e.g., React $\rightarrow$ Node.js $\rightarrow$ Java $\rightarrow$ DB).
- **Focus:** CQRS consistency. Tests must verify that an event written to the `event_store` is correctly reflected in the `read_model_rooms` within 500ms.
- **Tooling:** Postman/Newman for API contract testing.

### 7.3 End-to-End (E2E) Testing
- **Target:** Critical user paths (e.g., "Login $\rightarrow$ Create Room $\rightarrow$ Import File $\rightarrow$ Export PDF").
- **Tooling:** Playwright/Cypress.
- **Environment:** Run exclusively in the Staging environment.

### 7.4 Security Testing (The "Hardening" Phase)
- **Penetration Testing:** Monthly internal "Red Team" exercises by Beatriz Moreau.
- **SAST/DAST:** Static analysis using SonarQube and dynamic analysis using OWASP ZAP.
- **Audit Simulation:** A full "mock audit" performed 30 days before the official Milestone 1 date.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter. | Medium | High | **Accept Risk.** Monitor weekly. If cut occurs, deprioritize "Nice to Have" API (Feature 4) and reduce contractor spend. |
| R-02 | Scope creep from stakeholders adding 'small' features. | High | Medium | **External Consultant.** Engage a third-party analyst to evaluate all new requests against the original project charter. |
| R-03 | FedRAMP authorization delay. | Low | Critical | **Pre-emptive Audit.** Implement all controls from Day 1 and use a specialized FedRAMP consultant for guidance. |
| R-04 | Performance bottleneck in Event Store replay. | Medium | Medium | **Snapshotting.** Implement periodic state snapshots every 1,000 events to avoid replaying the entire history. |

**Impact Matrix:**
- **Probability:** Low (10-30%), Medium (30-60%), High (60%+).
- **Impact:** Low (Minor delay), Medium (Feature cut), High (Budget/Timeline failure), Critical (Project cancellation).

---

## 9. TIMELINE AND PHASES

The project follows a 6-month build cycle (Feb 2026 - Aug 2026).

### Phase 1: Foundation & Hardening (Feb - April)
- **Focus:** Infrastructure setup, RBAC implementation, and Event Store core.
- **Dependencies:** AWS GovCloud account provisioning.
- **Key Milestone:** **Milestone 1: Security Audit Passed (2026-04-15)**.

### Phase 2: Core Feature Development (April - June)
- **Focus:** Data Import/Export, Localization, and Real-time sync.
- **Dependencies:** Success of Milestone 1.
- **Key Milestone:** **Milestone 2: Internal Alpha Release (2026-06-15)**.

### Phase 3: Refinement & Launch (June - August)
- **Focus:** Bug fixing, A/B testing tuning, and API Sandbox.
- **Dependencies:** Alpha feedback from anchor client.
- **Key Milestone:** **Milestone 3: Production Launch (2026-08-15)**.

**Gantt-style Summary:**
- `Feb [====]` Core Auth / RBAC
- `Mar [====]` Event Store / CQRS Setup
- `Apr [====]` $\rightarrow$ **Audit (M1)**
- `May [====]` Import/Export & Localization
- `Jun [====]` $\rightarrow$ **Alpha (M2)**
- `Jul [====]` A/B Testing / API Sandbox
- `Aug [====]` $\rightarrow$ **Production (M3)**

---

## 10. MEETING NOTES

### Meeting 1: Kickoff & Tech Stack Alignment
**Date:** 2025-11-02  
**Attendees:** Yves, Saoirse, Beatriz, Devika  
- Mixed stacks. Need a way to talk. $\rightarrow$ Decision: Use gRPC for internal Java $\leftrightarrow$ Node communication.
- FedRAMP is scary. $\rightarrow$ Beatriz to lead on this.
- Devika (Intern) to handle the initial mapping for the import engine.
- Use LaunchDarkly. No more manual config files.

### Meeting 2: CQRS Architecture Deep-Dive
**Date:** 2025-12-15  
**Attendees:** Yves, Saoirse, Beatriz  
- Event store too slow for reads. $\rightarrow$ Use PostgreSQL for store, Redis for "current state" cache.
- Need to ensure "Read Model" is eventually consistent.
- Discussed "Snapshotting" every 1000 events to save CPU.
- Agreed on a "Command" pattern for all room updates.

### Meeting 3: Budget and Scope Review
**Date:** 2026-02-10  
**Attendees:** Yves, Stakeholders  
- Budget looks okay for now, but $240k might vanish next quarter. $\rightarrow$ Yves to keep a "cut list" of features.
- Stakeholders wanting "AI summaries" of rooms. $\rightarrow$ Yves pushed back. Too much scope creep.
- Decision: External consultant to vet all new feature requests from now on.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000  
**Duration:** 6 Months

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $540,000 | 6 developers/QA (avg $15k/mo per head $\times$ 6 months). |
| **Infrastructure** | $120,000 | AWS GovCloud, Redis Enterprise, Managed PostgreSQL. |
| **Tools & Licenses** | $40,000 | LaunchDarkly (Enterprise), SonarQube, Snyk, Splunk. |
| **External Consultant** | $50,000 | Scope management and FedRAMP pre-audit assessment. |
| **Contingency Fund** | $50,000 | Emergency buffer for unexpected technical blockers. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Registry
The project inherits a critical piece of technical debt from the initial prototype phase: **Lack of Structured Logging**.
- **Issue:** Currently, all logs are written to `stdout` as plain text.
- **Impact:** Debugging production issues in the Node.js layer requires manual `grep` on log files, which is slow and error-prone.
- **Remediation Plan:** Transition all logs to JSON format using the `Winston` logger, including `correlation_id` for every request to allow cross-service tracing.

### Appendix B: Data Import Format Specifications
The "Auto-Detection" engine must support the following specific cybersecurity formats:
1. **STIX 2.1 (Structured Threat Information Expression):** JSON-based format for sharing cyber threat intelligence.
2. **TAXII (Trusted Automated Exchange of Intelligence Information):** HTTPS-based protocol for STIX transport.
3. **CSV (Comma Separated Values):** Generic log exports from SIEM tools.
4. **JSON (Generic):** Standard API responses from cloud providers.
5. **XML (Cyber Observable):** Older forensic tool exports.

**Detection Logic:**
- If file contains `{"type": "bundle", "objects": [...]}` $\rightarrow$ STIX 2.1.
- If file contains `<stix:Package>` $\rightarrow$ STIX 1.x.
- If first line contains `timestamp,src_ip,dest_ip` $\rightarrow$ CSV.