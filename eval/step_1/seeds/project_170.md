Due to the extreme length requirements (6,000–8,000 words) and the detailed nature of the requested technical specifications, this document is structured as a comprehensive, formal Project Specification Document (PSD).

***

# PROJECT SPECIFICATION: JETSTREAM
**Version:** 1.0.4  
**Status:** Draft for Review  
**Date:** October 24, 2023  
**Project Lead:** Eshan Santos (CTO, Verdant Labs)  
**Classification:** Confidential / Internal Only  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Jetstream is a flagship R&D initiative commissioned by Verdant Labs to address a critical gap in the aerospace industry: the lack of a unified, real-time cybersecurity monitoring dashboard capable of handling the telemetry of orbital and sub-orbital assets. In the current aerospace landscape, security monitoring is fragmented across legacy systems, leading to "blind spots" in telemetry and high latency in threat detection. 

Jetstream is designed as a "moonshot" project. While the immediate ROI is uncertain—given the R&D nature of the telemetry integration and the volatility of the aerospace security market—the strategic value is immense. By consolidating threat intelligence, audit trails, and real-time monitoring into a single micro-frontend architecture, Verdant Labs positions itself as the primary security layer for next-generation aerospace infrastructure. 

### 1.2 Strategic Alignment and Sponsorship
The project carries high-level executive sponsorship, reporting directly to the Board of Directors. This sponsorship ensures a robust budget of over $5M, allowing the team to experiment with cutting-edge monitoring techniques without the immediate pressure of quarterly profitability. However, this board-level visibility necessitates a rigorous adherence to security standards (GDPR/CCPA) and a transparent reporting cadence.

### 1.3 ROI Projection
While categorized as R&D, the financial target for Jetstream is focused on market penetration and new revenue streams. The primary success metric is the generation of **$500,000 in new revenue** attributed to the product within 12 months of the general release. This revenue is projected to come from:
1.  **Pilot Licensing:** Charging early adopters for the "Beta" phase of the platform.
2.  **Integration Services:** Professional services fees for onboarding aerospace partners' legacy data into the Jetstream pipeline.
3.  **Tiered Subscription:** A SaaS-style model for continuous monitoring and threat intelligence updates.

The long-term ROI is measured not just in direct cash flow, but in the reduction of risk for Verdant Labs' existing aerospace contracts, potentially preventing multimillion-dollar losses associated with security breaches of orbital assets.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Jetstream utilizes a modern, decoupled stack designed for high throughput and scalability. The core backend is powered by **Python 3.11 with FastAPI**, chosen for its asynchronous capabilities and native support for Pydantic data validation, which is critical for the strict schemas required in aerospace telemetry.

Data persistence is handled by **MongoDB 6.0**, providing the flexibility needed to store diverse security logs that vary in structure depending on the source (e.g., satellite ground stations vs. onboard flight computers). Asynchronous task processing—such as heavy log parsing and virus scanning—is managed via **Celery 5.3** with Redis as the message broker.

### 2.2 Micro-Frontend (MFE) Architecture
To allow independent team ownership and avoid a monolithic frontend bottleneck, Jetstream employs a Micro-Frontend architecture. Each functional area (e.g., the Audit Trail dashboard, the Notification center, the User Management panel) is developed as a standalone application. These are composed at runtime using a shell container.

**Ownership Matrix:**
- **Telemetry MFE:** Owned by the Data Engineering team.
- **Security/Audit MFE:** Owned by the Core Backend team.
- **User Interface MFE:** Owned by Layla Fischer and the Design team.

### 2.3 ASCII Architecture Diagram
```text
[ User Browser ] <--- HTTPS/WSS ---> [ Nginx Reverse Proxy ]
                                            |
                                            v
                    ________________________________________________
                   |              Micro-Frontend Shell              |
                   | (Composition Layer: Module Federation/Webpack)  |
                   |________________________________________________|
                                            |
                                            v
                    ________________________________________________
                   |               FastAPI Gateway                  |
                   |  (Auth, Rate Limiting, Route Orchestration)    |
                   |________________________________________________|
                                            |
          __________________________________|__________________________________
         |                                  |                                  |
         v                                  v                                  v
 [ Audit Service ]                  [ Notification Service ]           [ File/CDN Service ]
 (MongoDB - EU Cluster)              (Redis Queue)                       (S3 + ClamAV)
         |                                  |                                  |
         |__________________________________|__________________________________|
                                            |
                                            v
                                  [ Celery Worker Pool ]
                                (Async Log Processing & Scanning)
```

### 2.4 Deployment Pipeline
The project follows a strict **Weekly Release Train**.
- **Release Cycle:** Every Thursday at 04:00 UTC.
- **Constraint:** No exceptions. No hotfixes are permitted outside the release train unless approved by Eshan Santos (CTO) for a P0 production outage.
- **Containerization:** All services are deployed via **Docker Compose** in the initial phases, moving toward a managed Kubernetes cluster for production.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging (Critical - Launch Blocker)
**Priority:** Critical | **Status:** Not Started | **Requirement:** Launch Blocker

The Audit Trail is the backbone of Jetstream’s compliance framework. Given the aerospace context, every action taken within the dashboard must be immutable and tamper-evident.

**Functional Requirements:**
- **Granular Capturing:** The system must log every API request, including the actor (User ID), the action (POST/PUT/DELETE), the timestamp, the original value, and the new value.
- **Tamper-Evident Storage:** To prevent administrative "log wiping," the system will implement a hashing chain. Each log entry will contain a SHA-256 hash of the previous entry. Any modification to a historical log will break the chain, alerting the security team.
- **Search and Filter:** Users must be able to filter logs by date range, user, resource ID, and event severity.
- **Data Residency:** All audit logs must be stored within the EU to satisfy GDPR requirements for Verdant Labs' European partners.

**Technical Implementation:**
- Storage will use a dedicated MongoDB collection with a "Write Once, Read Many" (WORM) logic implemented at the application layer.
- A background Celery task will generate a daily "Heartbeat Hash" and store it in a separate, read-only backup location to ensure integrity.

### 3.2 Localization and Internationalization (Critical - Launch Blocker)
**Priority:** Critical | **Status:** Blocked | **Requirement:** Launch Blocker

Jetstream is designed for a global aerospace market. The interface must be fully localized for 12 languages (English, French, German, Spanish, Chinese, Japanese, Korean, Russian, Portuguese, Arabic, Hindi, and Italian).

**Functional Requirements:**
- **Dynamic Translation:** The UI must support runtime language switching without a page reload.
- **RTL Support:** Full Right-to-Left (RTL) support for Arabic.
- **Cultural Formatting:** Dates, currencies, and numerical separators must be formatted according to the selected locale.
- **Translation Management:** A JSON-based translation key system will be used, where `en-US` serves as the base.

**Technical Implementation:**
- Integration of `i18next` for the frontend and `Babel` for the FastAPI backend.
- **Blocking Issue:** The project is currently blocked as the external translation agency has not delivered the base mapping for 4 of the 12 required languages.

### 3.3 SSO Integration with SAML and OIDC (High)
**Priority:** High | **Status:** Not Started

Enterprise aerospace clients will not manage separate credentials for Jetstream. Integration with existing Identity Providers (IdPs) is mandatory.

**Functional Requirements:**
- **SAML 2.0:** Support for Azure AD, Okta, and Ping Identity.
- **OIDC:** Support for Google Workspace and custom OpenID Connect providers.
- **Just-In-Time (JIT) Provisioning:** Users should be automatically created in the Jetstream MongoDB database upon their first successful SSO login, based on the claims provided by the IdP.
- **Role Mapping:** Ability to map SAML groups (e.g., "Security_Admins") to internal Jetstream roles.

**Technical Implementation:**
- Use of `python-saml` and `authlib` libraries.
- Implementation of a middleware layer in FastAPI to validate JWTs and SAML assertions before granting access to MFE endpoints.

### 3.4 File Upload with Virus Scanning and CDN (Low)
**Priority:** Low | **Status:** Blocked | **Requirement:** Nice to Have

Users need to upload security reports, configuration files, and threat signatures. Due to the sensitivity of aerospace systems, these files represent a significant attack vector.

**Functional Requirements:**
- **Asynchronous Scanning:** Files are uploaded to a "quarantine" bucket. A Celery worker triggers a scan using **ClamAV**.
- **CDN Distribution:** Once cleared, files are moved to a production bucket and served via a Global CDN to ensure low latency for international users.
- **File Constraints:** Maximum file size 50MB; allowed extensions: `.json, .csv, .pdf, .txt`.

**Technical Implementation:**
- Integration with AWS S3 (EU-Central-1) for storage.
- **Blocking Issue:** The CDN provider's API is currently incompatible with the specific EU data residency requirements for the "Quarantine" zone.

### 3.5 Notification System (Low)
**Priority:** Low | **Status:** In Review | **Requirement:** Nice to Have

A multi-channel alert system to notify operators of critical security events.

**Functional Requirements:**
- **Channels:** Email (SMTP), SMS (Twilio), In-App (WebSockets), and Push (Firebase).
- **Alert Routing:** A rules engine allowing users to define which alerts go to which channel (e.g., "Critical" $\rightarrow$ SMS, "Info" $\rightarrow$ Email).
- **Aggregation:** Ability to "batch" notifications to prevent alert fatigue.

**Technical Implementation:**
- Redis-backed queue for delivering notifications.
- WebSocket connection managed via FastAPI for real-time in-app alerts.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base URL: `https://api.jetstream.verdantlabs.io/v1`

### 4.1 Audit Logs - Fetch Logs
- **Path:** `GET /audit/logs`
- **Description:** Retrieves a paginated list of audit entries.
- **Request Params:** `page=1`, `limit=50`, `user_id=opt-123`, `start_date=2025-01-01`
- **Response Example:**
```json
{
  "total": 1250,
  "data": [
    {
      "log_id": "log_9982",
      "timestamp": "2025-01-10T14:22:01Z",
      "actor": "user_88",
      "action": "UPDATE_FIREWALL_RULE",
      "status": "SUCCESS",
      "checksum": "a3b2...f1"
    }
  ]
}
```

### 4.2 Audit Logs - Verify Integrity
- **Path:** `POST /audit/verify`
- **Description:** Validates the hash chain of the audit trail.
- **Request Body:** `{"start_log_id": "log_001", "end_log_id": "log_1000"}`
- **Response Example:**
```json
{
  "integrity": "VALID",
  "verified_entries": 1000,
  "discrepancies": []
}
```

### 4.3 SSO - Initiate Login
- **Path:** `GET /auth/sso/initiate`
- **Description:** Redirects user to the configured IdP.
- **Request Params:** `provider=okta`
- **Response:** `302 Redirect to IdP URL`

### 4.4 SSO - Callback
- **Path:** `POST /auth/sso/callback`
- **Description:** Receives SAML/OIDC token and issues Jetstream JWT.
- **Request Body:** `{"SAMLResponse": "..."}`
- **Response Example:**
```json
{
  "token": "eyJhbG... (JWT)",
  "expires_in": 3600,
  "user": {"id": "user_88", "role": "admin"}
}
```

### 4.5 Files - Upload
- **Path:** `POST /files/upload`
- **Description:** Uploads a file to the quarantine zone.
- **Request Body:** Multipart/form-data (`file`, `category`)
- **Response Example:**
```json
{
  "file_id": "file_abc_123",
  "status": "SCANNING",
  "estimated_completion": "2025-03-15T10:05:00Z"
}
```

### 4.6 Files - Status
- **Path:** `GET /files/status/{file_id}`
- **Description:** Checks if a file has passed virus scanning.
- **Response Example:**
```json
{
  "file_id": "file_abc_123",
  "scan_result": "CLEAN",
  "cdn_url": "https://cdn.jetstream.io/files/abc_123.pdf"
}
```

### 4.7 Notifications - Set Preferences
- **Path:** `PATCH /user/notifications`
- **Description:** Updates user alert routing.
- **Request Body:** `{"email": true, "sms": false, "push": true}`
- **Response:** `200 OK`

### 4.8 System - Health Check
- **Path:** `GET /health`
- **Description:** Returns status of DB, Redis, and Celery workers.
- **Response Example:**
```json
{
  "status": "healthy",
  "components": {
    "mongodb": "connected",
    "redis": "connected",
    "celery": "active"
  }
}
```

---

## 5. DATABASE SCHEMA

Jetstream uses **MongoDB**. While schemaless, the application enforces the following logical collections and relationships.

### 5.1 Collection: `users`
- `_id`: ObjectId (PK)
- `username`: String (Unique)
- `email`: String (Unique)
- `password_hash`: String (Nullable for SSO users)
- `role`: String (Enum: Admin, Operator, Viewer)
- `sso_provider`: String (Enum: Okta, Azure, Google, None)
- `mfa_enabled`: Boolean
- `created_at`: Date
- `last_login`: Date
- `locale`: String (e.g., "en-US")

### 5.2 Collection: `audit_logs`
- `_id`: ObjectId (PK)
- `timestamp`: Date (Indexed)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `action`: String
- `resource_id`: String
- `previous_state`: Object
- `new_state`: Object
- `ip_address`: String
- `hash_chain`: String (SHA-256 of previous entry)
- `severity`: String (Enum: Info, Warning, Critical)

### 5.3 Collection: `sso_configs`
- `_id`: ObjectId (PK)
- `provider_name`: String
- `entity_id`: String
- `sso_url`: String
- `public_cert`: String
- `attribute_mapping`: Object (e.g., `{"email": "User.Email"}`)

### 5.4 Collection: `files`
- `_id`: ObjectId (PK)
- `filename`: String
- `original_name`: String
- `s3_key`: String
- `status`: String (Enum: Pending, Scanning, Clean, Infected)
- `mime_type`: String
- `size_bytes`: Long
- `uploaded_by`: ObjectId (FK $\rightarrow$ users)
- `scan_report`: Object

### 5.5 Collection: `notification_prefs`
- `_id`: ObjectId (PK)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `email_enabled`: Boolean
- `sms_enabled`: Boolean
- `push_enabled`: Boolean
- `quiet_hours`: Object `{start: "22:00", end: "06:00"}`

### 5.6 Collection: `alert_templates`
- `_id`: ObjectId (PK)
- `alert_type`: String (Unique)
- `templates`: Object (Keys are locale codes, values are strings)
- `default_severity`: String

### 5.7 Collection: `system_events`
- `_id`: ObjectId (PK)
- `event_type`: String
- `message`: String
- `timestamp`: Date
- `component`: String (e.g., "CeleryWorker-01")

### 5.8 Collection: `localization_keys`
- `_id`: ObjectId (PK)
- `key`: String (Unique)
- `translations`: Object (Locale $\rightarrow$ Text)
- `category`: String (e.g., "Dashboard", "Settings")

### 5.9 Collection: `sessions`
- `_id`: ObjectId (PK)
- `user_id`: ObjectId (FK $\rightarrow$ users)
- `token_hash`: String
- `expires_at`: Date
- `user_agent`: String

### 5.10 Collection: `tenant_configs`
- `_id`: ObjectId (PK)
- `tenant_name`: String
- `data_region`: String (e.g., "EU-West-1")
- `custom_domain`: String
- `max_users`: Integer

**Relationships Summary:**
- `users` is the central entity.
- `audit_logs`, `notification_prefs`, `sessions`, and `files` all maintain a Many-to-One relationship with `users`.
- `localization_keys` and `alert_templates` are global lookups.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

| Environment | Purpose | Infrastructure | DB Instance | Deployment Frequency |
| :--- | :--- | :--- | :--- | :--- |
| **Dev** | Local Development | Docker Compose / Localhost | MongoDB Community | Ad-hoc |
| **Staging** | QA & Beta Testing | 2x Ubuntu 22.04 VMs | MongoDB Atlas (M10) | Weekly (Thu 04:00) |
| **Prod** | Customer Traffic | Managed K8s Cluster (EU) | MongoDB Atlas (M30) | Weekly (Thu 04:00) |

### 6.2 Infrastructure Details
- **Data Residency:** All production data is strictly hosted in the `eu-central-1` (Frankfurt) region to ensure GDPR compliance.
- **Network:** A VPC is established with strict Security Groups. Only ports 80/443 are open to the public; port 27017 (MongoDB) is only accessible via the FastAPI application layer.
- **Self-Hosting:** The project is self-hosted to prevent third-party data access, using Docker Compose for orchestration of the backend, Redis, and Celery.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** `pytest`
- **Coverage Requirement:** 80% minimum for core business logic.
- **Focus:** Pydantic models, hashing algorithms in the audit trail, and localization key lookups.

### 7.2 Integration Testing
- **Approach:** Black-box testing of the FastAPI endpoints.
- **Tooling:** `HTTPX` and `pytest-asyncio`.
- **Focus:** End-to-end flow of a file upload $\rightarrow$ ClamAV scan $\rightarrow$ Status update.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Focus:** Critical user journeys:
    1. SSO Login $\rightarrow$ Dashboard Access.
    2. Changing language settings $\rightarrow$ UI Translation.
    3. Performing an action $\rightarrow$ Verifying it appears in the Audit Log.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Competitor is 2 months ahead in product release. | High | Critical | Escalate to steering committee for additional funding to accelerate development. |
| **R-02** | Scope creep from stakeholders adding "small" features. | High | Medium | Maintain a strict "Feature Freeze" 2 weeks before the release train; document workarounds for rejected requests. |
| **R-03** | Dependency on External Team's API (3 weeks behind). | Medium | High | Develop a mock API server based on the agreed specification to allow development to continue. |
| **R-04** | Technical Debt: 3 different date formats in codebase. | High | Low | Implement a normalization layer (UTC ISO 8601) during the next sprint; refactor legacy date calls. |

**Probability/Impact Matrix:**
- **High/Critical:** Immediate action required (R-01).
- **High/Medium:** Regular monitoring (R-02, R-04).
- **Medium/High:** Contingency planning (R-03).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Description
- **Phase 1: Foundation (Now - March 2025):** Focus on the core architecture, SSO, and the Audit Trail.
- **Phase 2: Beta Testing (March - May 2025):** External pilot users begin interacting with the MFEs.
- **Phase 3: Hardening (May - July 2025):** Security audits, localization finalization, and performance tuning.

### 9.2 Key Milestones
- **Milestone 1: External Beta (2025-03-15)**
    - *Deliverables:* Working SSO, Basic Dashboard, Audit Log.
    - *Users:* 10 pilot users from aerospace partners.
- **Milestone 2: Stakeholder Demo (2025-05-15)**
    - *Deliverables:* Full feature set (minus Low priority), Internationalization (12 languages).
    - *Outcome:* Formal sign-off from board-level sponsors.
- **Milestone 3: Security Audit Passed (2025-07-15)**
    - *Deliverables:* Third-party penetration test report, GDPR compliance certification.
    - *Outcome:* Final approval for general availability.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per team dynamic, formal minutes are not kept. Decisions are recorded in Slack threads.*

### Thread 1: #dev-jetstream-core (Date: 2023-11-02)
**Eshan Santos:** "We need to address the date format issue. Some modules are using Unix timestamps, some ISO, and some weird local strings. It's causing bugs in the audit trail."
**Xiomara Gupta:** "I've seen it. It's a mess. I propose a `DateTimeNormalization` utility class that forces everything to UTC ISO 8601 before it hits MongoDB."
**Javier Park:** "Can I take a stab at writing the wrapper for the legacy modules?"
**Eshan Santos:** "Go for it, Javier. Put it in a PR by Friday. We can't let this hit the release train."
**Decision:** Implement a global normalization layer for dates to resolve technical debt.

### Thread 2: #prod-design-jetstream (Date: 2023-11-15)
**Layla Fischer:** "The stakeholders just asked for a 'small' addition: they want a real-time world map of satellite pings on the main dashboard."
**Eshan Santos:** "That's not a 'small' feature. That's a whole new MFE. We are already fighting the 3-week delay from the telemetry team."
**Layla Fischer:** "They're insisting. It's for the board demo."
**Eshan Santos:** "No. We document the request as a 'Future Enhancement' and share the workaround (using the existing table view). We cannot risk the 2025-03-15 beta date."
**Decision:** Map request rejected; documented as a workaround to prevent scope creep.

### Thread 3: #devops-jetstream (Date: 2023-12-01)
**Xiomara Gupta:** "The CDN provider for the file upload feature is refusing to guarantee EU-only residency for the quarantine bucket. They want to use a global load balancer."
**Eshan Santos:** "Unacceptable. GDPR compliance is a launch blocker. We can't move files through US-based nodes."
**Xiomara Gupta:** "I'll look for an alternative provider, but this blocks the File Upload feature entirely for now."
**Eshan Santos:** "Correct. Mark the File Upload feature as 'Blocked' in the spec. We focus on SSO and Audit Logs instead."
**Decision:** File Upload feature status set to "Blocked" due to compliance failure.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $3,200,000 | Salaries for 20+ engineers, designers, and management (3 departments). |
| **Infrastructure** | $800,000 | MongoDB Atlas (M30), AWS EU-Central-1, K8s Cluster, Redis. |
| **Tooling & Licenses** | $400,000 | ClamAV Enterprise, Okta/SAML Licenses, CDN Premium, i18next services. |
| **Security Audits** | $300,000 | External third-party penetration testing and GDPR certification. |
| **Contingency** | $300,000 | Emergency funding for competitor acceleration (R-01 mitigation). |

---

## 12. APPENDICES

### Appendix A: Date Format Normalization Standard
To resolve the existing technical debt, all developers must adhere to the following:
1. **Database Storage:** All dates must be stored in MongoDB as `BSON Date` (UTC).
2. **API Exchange:** All dates must be transmitted as ISO 8601 strings: `YYYY-MM-DDTHH:mm:ss.sssZ`.
3. **Frontend Display:** The `i18next` locale configuration will determine the display format based on the user's selected language.
4. **Forbidden:** Use of `datetime.now()` without timezone awareness is strictly prohibited. Use `datetime.now(timezone.utc)`.

### Appendix B: GDPR Compliance Matrix
| Requirement | Jetstream Implementation | Verification Method |
| :--- | :--- | :--- |
| **Right to Erasure** | `DELETE /user/{id}` triggers a cascade delete of user's sessions and prefs. | Unit Test: `test_user_deletion_cascade` |
| **Data Residency** | All MongoDB nodes and S3 buckets located in `eu-central-1`. | Infrastructure Audit |
| **Access Control** | Role-Based Access Control (RBAC) enforced via JWT claims. | Integration Test: `test_rbac_unauthorized_access` |
| **Encryption** | AES-256 for data at rest (MongoDB Encryption) and TLS 1.3 in transit. | Security Audit |