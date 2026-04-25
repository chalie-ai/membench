# PROJECT SPECIFICATION DOCUMENT: TRELLIS (v1.0.4)

**Date:** October 26, 2024  
**Project Code:** BW-TRELLIS-2025  
**Owner:** Bellweather Technologies  
**Classification:** Internal / Confidential  
**Status:** Active / Urgent  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Trellis" is a high-priority mobile application initiative developed by Bellweather Technologies to address an urgent regulatory compliance mandate within the real estate sector. The real estate industry is currently facing a transition toward stringent digital transparency and reporting standards. Failure to implement the specific compliance features mandated by the governing regulatory bodies will result in severe legal penalties, potential loss of operational licenses in key jurisdictions, and significant reputational damage.

The primary driver for Trellis is the "Hard Legal Deadline" occurring exactly six months from the project kickoff. This deadline is non-negotiable. The application serves as the primary interface for agents, brokers, and compliance officers to submit, track, and audit real estate transactions in real-time. By digitizing the compliance workflow, Bellweather Technologies transforms a liability (regulatory risk) into a competitive advantage, ensuring that all transactions are "compliant by design."

### 1.2 Project Objectives
The objective is to deliver a stable, secure, and scalable mobile platform that integrates legacy data streams into a modern, hexagonal architecture. The project must bridge three disparate inherited technology stacks, ensuring that the resulting application provides a seamless user experience while maintaining a tamper-evident audit trail of all regulatory filings.

### 1.3 ROI Projection
The Return on Investment (ROI) for Trellis is calculated through risk mitigation and operational efficiency:
1. **Penalty Avoidance:** The primary ROI is the avoidance of non-compliance fines, estimated at $250,000 per quarter for non-compliance across the company's portfolio.
2. **Operational Efficiency:** By automating the compliance check process, the manual audit time is projected to decrease by 40%, reducing the need for additional compliance staff.
3. **Market Positioning:** Providing a "certified compliant" tool to real estate partners is expected to increase partner retention by 15% over the next 24 months.
4. **Cost Efficiency:** By utilizing a focused team of six and a modest budget of $400,000, the project aims to deliver a high-impact solution without the overhead of massive enterprise software procurement.

### 1.4 Strategic Alignment
Trellis aligns with Bellweather Technologies' broader goal of "Digital Transformation in Real Estate." It moves the company away from fragmented, siloed data and toward a unified, service-oriented architecture that can be expanded into other regulatory domains in the future.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal (Ports and Adapters)
Trellis employs a Hexagonal Architecture to decouple the core business logic (the Domain) from the external technical details (the Infrastructure). Given that the project inherits three different legacy stacks (a legacy Java SOAP service, a Node.js middleware layer, and a Python-based data lake), this pattern is critical for interoperability.

- **The Core (Domain):** Contains the business entities (e.g., Property, Transaction, ComplianceReport) and use cases. It has no knowledge of databases or APIs.
- **Ports:** Interfaces that define how the core interacts with the outside world (e.g., `IUserRepository`, `INotificationService`).
- **Adapters:** Concrete implementations of ports. For example, a `SqlUserRepository` adapter connects the core to the PostgreSQL database, while a `TwilioSmsAdapter` connects the core to the SMS gateway.

### 2.2 Infrastructure Stack
- **Mobile Frontend:** React Native (cross-platform iOS/Android).
- **Backend:** Mixed-stack (Node.js TypeScript for the API Gateway, Python for data processing).
- **Database:** PostgreSQL 15 (Relational) and MongoDB 6.0 (for unstructured audit logs).
- **Caching:** Redis 7.0 for session management and API response caching.
- **Deployment:** CI/CD via GitHub Actions, deploying directly to AWS EKS (Elastic Kubernetes Service).

### 2.3 ASCII Architecture Diagram
```text
[ USER INTERFACE ] <---(JSON/REST)---> [ API GATEWAY (Adapter) ]
                                              |
                                              v
                                  [  APPLICATION CORE  ]
                                  [ (Business Logic)    ]
                                  [   Use-Case Layer     ]
                                              |
          ____________________________________|___________________________________
          |                                   |                                  |
    [ PORT: Storage ]                 [ PORT: Messaging ]                [ PORT: Legacy Integration ]
          |                                   |                                  |
    (Adapter: Postgres)               (Adapter: SendGrid/Twilio)         (Adapter: Legacy SOAP/REST)
          |                                   |                                  |
    [ DATABASE LAYER ]                 [ NOTIFICATION SERVICES ]         [ EXTERNAL STACKS A, B, C ]
```

### 2.4 Interoperability Strategy
To handle the three inherited stacks, the "Integration Adapter" layer will perform data normalization. Each legacy stack is treated as an external service. The adapter translates the legacy response (often XML or inconsistent JSON) into a standardized Domain Object used by the Trellis core.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System
**Priority:** Critical (Launch Blocker) | **Status:** Complete | **Version:** 1.0.0

**Description:**
The notification system is the primary mechanism for alerting users of compliance deadlines and filing approvals. It must operate across four distinct channels: Email, SMS, In-App, and Push.

**Functional Requirements:**
- **Multi-Channel Routing:** The system must determine the optimal channel based on user preference and alert urgency.
- **Template Engine:** A centralized system for managing localized message templates (Handlebars.js).
- **Retry Logic:** Exponential backoff for failed deliveries to ensure critical regulatory alerts are received.
- **Notification History:** A user-accessible log of all sent notifications within the app.

**Technical Implementation:**
The system uses a `NotificationDispatcher` port. The `EmailAdapter` utilizes SendGrid, the `SmsAdapter` utilizes Twilio, and the `PushAdapter` utilizes Firebase Cloud Messaging (FCM). In-app notifications are stored in a PostgreSQL table and fetched via a polling mechanism or WebSocket.

**Verification:**
All channels were verified via integration tests. The p95 latency for notification triggering is < 150ms.

---

### 3.2 Advanced Search with Faceted Filtering
**Priority:** Low (Nice to Have) | **Status:** Blocked | **Version:** 1.1.0

**Description:**
This feature allows users to perform complex queries across the real estate portfolio using full-text indexing and multifaceted filters (e.g., filtering by region, property type, compliance status, and date range simultaneously).

**Functional Requirements:**
- **Full-Text Search:** Ability to search through property descriptions and legal notes using natural language.
- **Faceted Navigation:** A sidebar providing counts of records per category (e.g., "Pending (45)", "Approved (120)").
- **Dynamic Query Building:** The UI must allow users to add/remove filters without reloading the page.

**Technical Implementation:**
The proposed implementation involves integrating Elasticsearch. The data engineer (Dina Jensen) will build a synchronization pipeline from PostgreSQL to Elasticsearch. The `SearchPort` will define the query interface, and the `ElasticsearchAdapter` will handle the DSL queries.

**Blocker:**
Currently blocked due to the pending budget approval for the Elasticsearch managed service license.

---

### 3.3 Localization and Internationalization (L10n/I18n)
**Priority:** High | **Status:** Blocked | **Version:** 1.2.0

**Description:**
Trellis must support 12 different languages to comply with regulations in various international territories where Bellweather operates. This includes right-to-left (RTL) support for certain markets.

**Functional Requirements:**
- **Dynamic Language Switching:** Users can change the language in settings; the app reflects changes immediately without a restart.
- **Regional Formatting:** Dates, currencies, and number formats must adapt to the selected locale.
- **Translation Management:** Integration with a Translation Management System (TMS) for external linguists.

**Technical Implementation:**
The frontend uses `i18next` for React Native. The backend provides a `/localize` endpoint that delivers translation bundles based on the `Accept-Language` header. 

**Blocker:**
Blocked pending the finalization of the legal terminology translation for 4 of the 12 languages; the legal team has not signed off on the translated compliance terms.

---

### 3.4 Audit Trail Logging
**Priority:** High | **Status:** Blocked | **Version:** 1.3.0

**Description:**
A critical regulatory requirement is a tamper-evident audit log. Every change to a compliance record must be logged with a timestamp, user ID, and the "before" and "after" state of the data.

**Functional Requirements:**
- **Immutability:** Once a log is written, it cannot be edited or deleted.
- **Hashing:** Each log entry must contain a cryptographic hash of the previous entry (Blockchain-lite) to ensure no entries were removed.
- **Quick Retrieval:** Ability for auditors to export a full history of a specific record into a PDF/CSV.

**Technical Implementation:**
The `AuditLogger` port will implement a write-ahead log. The `MongoAuditAdapter` will store these logs in a MongoDB capped collection. A background process will calculate a Merkle Tree root daily and store it in a secure, read-only S3 bucket for verification.

**Blocker:**
Blocked by the departure of the key architect, who is the only team member with the specific cryptographic implementation knowledge required for the tamper-evident logic.

---

### 3.5 Data Import/Export
**Priority:** Medium | **Status:** Not Started | **Version:** 1.4.0

**Description:**
Users need to move large batches of property data into Trellis and export reports for external regulatory bodies. The system must auto-detect the file format.

**Functional Requirements:**
- **Format Auto-Detection:** Support for CSV, JSON, and XML. The system should analyze the file header to determine the format.
- **Validation Pipeline:** Data must be validated against the domain schema before being committed to the database.
- **Asynchronous Processing:** Large imports (10,000+ rows) must be processed in the background with a progress bar.

**Technical Implementation:**
A `FileProcessor` service will handle the uploads. It will utilize a strategy pattern to select the correct `Parser` (CsvParser, JsonParser, XmlParser). Processing will be handled via a Celery worker queue in Python.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the Authorization header.

### 4.1 GET `/properties`
- **Description:** Retrieves a list of properties.
- **Request Params:** `limit` (int), `offset` (int), `status` (string).
- **Response (200 OK):**
  ```json
  {
    "data": [
      { "id": "prop_123", "address": "123 Maple St", "status": "compliant" },
      { "id": "prop_456", "address": "456 Oak Ave", "status": "pending" }
    ],
    "pagination": { "total": 150, "next": "/api/v1/properties?offset=20" }
  }
  ```

### 4.2 POST `/properties`
- **Description:** Creates a new property record.
- **Request Body:**
  ```json
  {
    "address": "789 Pine Rd",
    "owner_id": "user_99",
    "valuation": 450000
  }
  ```
- **Response (201 Created):** `{ "id": "prop_789", "created_at": "2025-01-10T10:00:00Z" }`

### 4.3 GET `/compliance/status/{property_id}`
- **Description:** Checks the regulatory status of a specific property.
- **Response (200 OK):**
  ```json
  {
    "property_id": "prop_123",
    "is_compliant": true,
    "last_audit": "2024-12-01",
    "expiry_date": "2025-12-01"
  }
  ```

### 4.4 PUT `/compliance/update/{property_id}`
- **Description:** Updates the compliance status.
- **Request Body:** `{ "status": "approved", "auditor_id": "user_01", "notes": "All docs verified" }`
- **Response (200 OK):** `{ "status": "success", "timestamp": "2025-01-15T08:30:00Z" }`

### 4.5 GET `/notifications/unread`
- **Description:** Fetches all unread notifications for the current user.
- **Response (200 OK):**
  ```json
  {
    "unread_count": 3,
    "notifications": [
      { "id": "notif_1", "message": "Deadline approaching", "type": "urgent" }
    ]
  }
  ```

### 4.6 POST `/notifications/mark-read`
- **Description:** Marks one or more notifications as read.
- **Request Body:** `{ "notification_ids": ["notif_1", "notif_2"] }`
- **Response (200 OK):** `{ "updated": 2 }`

### 4.7 GET `/audit/logs/{property_id}`
- **Description:** Retrieves the tamper-evident log for a property.
- **Response (200 OK):**
  ```json
  {
    "logs": [
      { "seq": 1, "action": "CREATE", "hash": "a1b2c3...", "timestamp": "..." },
      { "seq": 2, "action": "UPDATE", "hash": "d4e5f6...", "timestamp": "..." }
    ]
  }
  ```

### 4.8 POST `/data/import`
- **Description:** Uploads a file for bulk data import.
- **Request Body:** Multipart form-data (file).
- **Response (202 Accepted):** `{ "job_id": "job_888", "status": "processing" }`

---

## 5. DATABASE SCHEMA

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | None | `email`, `role`, `password_hash` | User account and auth data. |
| `Properties` | `prop_id` | `owner_id` | `address`, `valuation`, `zip_code` | Core property records. |
| `ComplianceDocs` | `doc_id` | `prop_id`, `user_id` | `doc_type`, `file_url`, `verified` | Regulatory documents. |
| `AuditLogs` | `log_id` | `prop_id`, `user_id` | `action`, `prev_hash`, `payload` | Tamper-evident change logs. |
| `Notifications` | `notif_id` | `user_id` | `channel`, `message`, `is_read` | User alerts. |
| `UserPreferences` | `pref_id` | `user_id` | `lang_code`, `timezone`, `notif_opt_in` | Localization and UI settings. |
| `Regions` | `region_id` | None | `name`, `regulatory_body`, `country_code` | Geographic regulatory zones. |
| `PropertyRegion` | `id` | `prop_id`, `region_id` | `assigned_date` | Linking properties to regions. |
| `AuditSessions` | `session_id` | `user_id` | `start_time`, `end_time`, `scope` | Tracks auditor activity. |
| `ImportJobs` | `job_id` | `user_id` | `filename`, `status`, `rows_processed` | Tracks bulk import progress. |

### 5.2 Relationships
- **Users $\rightarrow$ Properties:** One-to-Many (An owner can have many properties).
- **Properties $\rightarrow$ ComplianceDocs:** One-to-Many (A property has multiple required documents).
- **Properties $\rightarrow$ AuditLogs:** One-to-Many (Every change creates a log).
- **Users $\rightarrow$ Notifications:** One-to-Many.
- **Regions $\rightarrow$ Properties:** Many-to-Many via `PropertyRegion` table.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Trellis utilizes three distinct environments to ensure stability before production release.

1. **Development (Dev):**
   - **Purpose:** Sandbox for developers.
   - **Deployment:** Triggered on every push to a `feature/*` branch.
   - **Data:** Mock data and anonymized samples.
   - **URL:** `dev.trellis.bellweather.io`

2. **Staging (Staging):**
   - **Purpose:** Pre-production validation and QA.
   - **Deployment:** Triggered on merge to the `develop` branch.
   - **Data:** Mirror of production data (obfuscated).
   - **URL:** `staging.trellis.bellweather.io`

3. **Production (Prod):**
   - **Purpose:** End-user access.
   - **Deployment:** Continuous Deployment (CD). Every merged Pull Request (PR) to the `main` branch is automatically deployed to production after passing the full test suite.
   - **URL:** `app.trellis.bellweather.io`

### 6.2 Infrastructure Components
- **Cluster:** AWS EKS with Auto-scaling groups.
- **Load Balancer:** AWS ALB distributing traffic across pods.
- **Secret Management:** AWS Secrets Manager for API keys and DB credentials.
- **Storage:** AWS S3 for document uploads and audit hashes.
- **Monitoring:** Datadog for p95 response time tracking and error logging.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Approach:** Each domain service and utility function must have 100% coverage of critical paths.
- **Tools:** Jest (Frontend/Node), PyTest (Python).
- **Requirement:** No PR can be merged unless unit tests pass.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between the Core and Adapters. Specifically, verifying that the legacy stack adapters correctly translate data.
- **Tools:** Supertest for API endpoint verification.
- **Focus:** Validating that the `NotificationDispatcher` correctly triggers the external Twilio/SendGrid APIs.

### 7.3 End-to-End (E2E) Testing
- **Approach:** User-flow simulation from login to compliance submission.
- **Tools:** Detox for React Native mobile automation.
- **Critical Paths:**
  - User logs in $\rightarrow$ searches for property $\rightarrow$ uploads doc $\rightarrow$ receives notification.
  - Auditor logs in $\rightarrow$ reviews doc $\rightarrow$ marks as compliant $\rightarrow$ audit log created.

### 7.4 QA Process
A dedicated QA engineer is assigned to the team of 6. QA performs manual regression testing on the staging environment for every release candidate and signs off on the "Definition of Done" for each sprint ticket.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key Architect leaving in 3 months | High | Critical | Negotiate timeline extension with stakeholders; begin immediate knowledge transfer sessions. |
| R-02 | Perf requirements 10x current capacity | Medium | High | Engage external consultant for independent assessment of infrastructure. |
| R-03 | Budget approval for tools pending | High | Medium | Escalate to Lina Moreau (VP) for urgent sign-off; seek open-source alternatives if blocked. |
| R-04 | Team trust still forming | Medium | Medium | Implement "Sprint Retrospectives" and pair programming to build cohesion. |
| R-05 | Legacy stack instability | Medium | High | Implement aggressive circuit breakers in the Adapter layer to prevent system-wide failure. |

**Impact Matrix:**
- **Critical:** Blockers that prevent legal compliance.
- **High:** Major feature degradation or performance failure.
- **Medium:** Workaround available, but increases technical debt.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Months 1-2)
- **Focus:** Core architecture and notification system.
- **Key Tasks:** Setup Hexagonal ports, integrate legacy stacks, finalize notification logic.
- **Dependency:** Budget approval for base infrastructure.
- **Milestone 1:** Architecture review complete (Target: 2025-07-15).

### 9.2 Phase 2: Core Compliance (Months 3-4)
- **Focus:** Audit trails and data import/export.
- **Key Tasks:** Implement MongoDB audit logs, build file auto-detection logic.
- **Dependency:** Success of knowledge transfer from departing architect.
- **Milestone 2:** External beta with 10 pilot users (Target: 2025-09-15).

### 9.3 Phase 3: Globalization & Polishing (Months 5-6)
- **Focus:** L10n/I18n and advanced search.
- **Key Tasks:** Implement 12-language bundles, deploy Elasticsearch.
- **Dependency:** Legal sign-off on translations.
- **Milestone 3:** Stakeholder demo and sign-off (Target: 2025-11-15).

---

## 10. MEETING NOTES

### Meeting 1: Kickoff & Architecture
**Date:** 2024-11-01  
**Attendees:** Lina, Dina, Zia, Aaliya  
- Hexagonal agreed.
- Mixed stacks = nightmare. Use adapters.
- CD is mandatory. Every PR to prod.
- Budget is tight. $400k total.

### Meeting 2: Notification Sync
**Date:** 2024-11-15  
**Attendees:** Lina, Zia, Aaliya  
- Push notifications failing on Android 14.
- Zia to fix FCM token refresh.
- SMS costs too high? Check Twilio tiers.
- Status: Notifications now "Complete."

### Meeting 3: Risk Review
**Date:** 2024-12-05  
**Attendees:** Lina, Dina, Zia  
- Architect leaving. Huge gap in crypto knowledge.
- Dina can't do the audit log alone.
- Need external consultant for 10x load issue.
- Tool budget still pending. Lina to push VP.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $280,000 | 5 FTEs + 1 Contractor (Aaliya). |
| **Infrastructure** | 15% | $60,000 | AWS EKS, RDS, S3, MongoDB Atlas. |
| **Tools & Licenses**| 10% | $40,000 | Elasticsearch, Datadog, SendGrid, Twilio. |
| **Contingency** | 5% | $20,000 | For external consultant / emergency fixes. |

---

## 12. APPENDICES

### Appendix A: Data Normalization Map
Because Trellis inherits three stacks, data must be mapped as follows:
- **Legacy Stack A (SOAP):** `<PropVal>` $\rightarrow$ `valuation` (Float)
- **Legacy Stack B (Node/JSON):** `estimated_price` $\rightarrow$ `valuation` (Float)
- **Legacy Stack C (Python/Lake):** `val_usd` $\rightarrow$ `valuation` (Float)

### Appendix B: Performance Benchmarks
The following p95 targets are mandatory for sign-off:
- **Property Retrieval:** < 200ms
- **Notification Trigger:** < 150ms
- **Audit Log Write:** < 100ms
- **Search Query:** < 400ms (due to index complexity)