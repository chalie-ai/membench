# PROJECT SPECIFICATION: PROJECT BASTION
**Document Version:** 1.0.4  
**Date:** October 24, 2025  
**Project Status:** Active/Development  
**Classification:** Confidential - Talus Innovations Internal  
**Owner:** Freya Moreau (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Bastion is a strategic "moonshot" R&D initiative commissioned by Talus Innovations. The objective is to develop a specialized e-commerce marketplace tailored specifically for the aerospace industry. Unlike consumer-grade marketplaces, Bastion is designed to handle high-value, low-volume transactions involving complex regulatory requirements, aerospace-grade certifications (AS9100), and long-lead-time procurement cycles.

The aerospace supply chain is currently fragmented, relying on legacy EDI systems and manual procurement. Bastion aims to modernize this by providing a real-time, collaborative procurement environment where engineers and procurement officers can synchronize specifications and pricing in real-time.

### 1.2 Business Justification
The primary justification for Bastion is the strategic positioning of Talus Innovations as a platform provider rather than just a component manufacturer. By controlling the marketplace where aerospace parts are traded, Talus gains unprecedented visibility into market demand, pricing trends, and competitor availability. 

While the Return on Investment (ROI) is currently categorized as "uncertain" due to the experimental nature of the marketplace model in the aerospace sector, the project enjoys strong executive sponsorship. The mandate is to build a "technological moat" that makes it prohibitively expensive for competitors to enter the digital aerospace procurement space.

### 1.3 ROI Projection and Financial Targets
The financial success of Bastion is not measured by immediate profitability, but by operational efficiency and market capture.
- **Target ROI:** Expected break-even by Q4 2027.
- **Primary Metric:** Reduction of transaction cost by 35% compared to the current legacy procurement system (which currently averages $1,200 per transaction in administrative overhead).
- **Secondary Metric:** Onboarding of 15 tier-1 aerospace suppliers within the first 12 months.
- **Projected Revenue Stream:** A 1.5% transaction fee on all marketplace trades, supplemented by a monthly "Premium Supplier" subscription fee of $2,500/month.

### 1.4 Strategic Constraints
The project is constrained by a fixed budget of $800,000 for a 6-month build cycle. The timeline is aggressive, with the first paying customer targeted for mid-June 2026. The high-risk nature of the project is compounded by a team that is unfamiliar with the chosen Elixir/Phoenix stack, requiring a steep learning curve during the initial sprints.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Bastion utilizes a **Modular Monolith** architecture. This approach allows the team to develop features rapidly within a single codebase while maintaining strict boundary separations between domains (e.g., `Bastion.Auth`, `Bastion.Catalog`, `Bastion.Payments`). As the system scales and the team matures, these modules will be incrementally extracted into independent microservices.

### 2.2 The Tech Stack
- **Language/Framework:** Elixir / Phoenix Framework (v1.7+).
- **Frontend:** Phoenix LiveView for real-time, stateful interactions without full-page refreshes.
- **Database:** PostgreSQL 15 (Relational data, JSONB for flexible aerospace part specifications).
- **Infrastructure:** Fly.io (Global distribution, managed Kubernetes).
- **CI/CD:** GitLab CI utilizing rolling deployments to ensure zero-downtime updates.
- **Compliance:** SOC 2 Type II (Security, Availability, and Confidentiality).

### 2.3 Architectural Diagram (ASCII Description)
The following diagram describes the request flow from the client to the data persistence layer:

```text
[ CLIENT BROWSER ] 
       |
       | (WebSocket / HTTPS)
       v
[ FLY.IO LOAD BALANCER ]
       |
       v
[ PHOENIX APP CLUSTER ] <---- [ GitLab CI / CD ]
       |      |      |
       |      |      +------> [ LiveView State / GenServer ]
       |      |
       |      +--------------> [ Modular Monolith Logic ]
       |                            |
       |                            | (Ecto / SQL)
       v                            v
[ POSTGRESQL DB ] <---------- [ REDIS / CACHE ]
       |
       +--> [ Table: Users ]
       +--> [ Table: Parts ]
       +--> [ Table: Orders ]
       +--> [ Table: Audits ]
```

### 2.4 Design Philosophy
The architecture prioritizes **Concurrency** and **Fault Tolerance**. By leveraging the Erlang VM (BEAM), Bastion can handle thousands of simultaneous real-time collaborative sessions (critical for the collaborative editing feature) without the overhead of traditional threading models.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical | **Status:** Blocked | **Requirement:** Launch Blocker

**Description:**
Aerospace procurement involves complex "Request for Quote" (RFQ) documents where multiple stakeholders (Engineer, Procurement Lead, Vendor) must edit the same specification document simultaneously. This feature requires a shared-state editor where changes are reflected in real-time across all connected clients.

**Functional Specifications:**
- **Operational Transformation (OT) / CRDT:** The system must implement Conflict-free Replicated Data Types (CRDTs) to ensure that concurrent edits to a part specification do not result in data loss or divergent states.
- **Presence Tracking:** Using Phoenix Presence, users must see who else is currently viewing/editing the document (cursors and avatars).
- **Locking Mechanism:** While CRDTs handle merging, a "soft-lock" mechanism will be implemented for specific critical fields (e.g., "Maximum Tolerances") to prevent accidental overwrites.
- **Version History:** Every change must be attributed to a user and timestamped, allowing for a "Time Machine" style rollback.

**Technical Implementation:**
- Use `Phoenix.LiveView` for the UI layer.
- Implement a `GenServer` on the backend to manage the state of active documents.
- State synchronization will happen over WebSockets.
- Conflict resolution will be handled via a LWW (Last Write Wins) element set for simple fields and a sequence-based CRDT for text blocks.

**Acceptance Criteria:**
- Two users can edit the same field and the system resolves the state within 200ms.
- No data is lost during a network disconnection and subsequent reconnection.

---

### 3.2 Data Import/Export with Format Auto-Detection
**Priority:** High | **Status:** Not Started

**Description:**
Aerospace vendors currently store part lists in a variety of legacy formats (CSV, XML, XLS, JSON). Bastion must allow users to upload these files and have the system automatically detect the format and map the columns to the internal aerospace schema.

**Functional Specifications:**
- **Auto-Detection Engine:** The system must analyze the first 10 lines of an uploaded file to determine the MIME type and delimiter.
- **Mapping Interface:** If the system cannot 100% match the columns to the database schema (e.g., "Part_Num" vs "SKU"), it must present the user with a drag-and-drop mapping interface.
- **Validation Pipeline:** Imported data must pass through a validation gate (regex checks for part numbers, range checks for dimensions) before being committed to the database.
- **Export Engine:** Support for exporting current marketplace listings into CSV and PDF formats for regulatory auditing.

**Technical Implementation:**
- Use the `NimbleCSV` library for high-performance CSV parsing.
- Implement a strategy pattern for different file handlers (`Import.CSV`, `Import.XML`).
- Use a background job worker (`Oban`) to process large files (10,000+ rows) to prevent blocking the main process.

**Acceptance Criteria:**
- Correctly identify and import a 5,000-row CSV file in under 10 seconds.
- Provide a detailed error report highlighting exactly which rows failed validation.

---

### 3.3 Notification System (Email, SMS, In-App, Push)
**Priority:** Medium | **Status:** Not Started

**Description:**
Given the high value of aerospace transactions, stakeholders must be notified immediately of status changes (e.g., "Quote Accepted", "Shipping Delayed", "Certification Expired").

**Functional Specifications:**
- **Multi-Channel Routing:** Users can configure their preferences per notification type (e.g., "Critical Alerts" via SMS, "Weekly Reports" via Email).
- **Template Engine:** Admin users must be able to edit notification templates using a Markdown-based editor.
- **Notification Queue:** To ensure reliability, all notifications must be queued and retried upon failure.
- **In-App Notification Center:** A real-time bell icon showing unread alerts, powered by Phoenix PubSub.

**Technical Implementation:**
- **Email:** Integration with SendGrid API.
- **SMS:** Integration with Twilio API.
- **Push:** Integration with Firebase Cloud Messaging (FCM).
- **Queue:** Use `Oban` with PostgreSQL as the backend to ensure "at-least-once" delivery.

**Acceptance Criteria:**
- Notifications are delivered to the chosen channel within 30 seconds of the triggering event.
- System can handle 1,000 concurrent notification bursts without degrading API performance.

---

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** In Review

**Description:**
Corporate procurement officers require weekly and monthly summaries of spend, vendor performance, and procurement lead times to present to executive boards.

**Functional Specifications:**
- **Report Builder:** Users can select which metrics to include in their report (e.g., Total Spend, Average Lead Time, Vendor Reliability Score).
- **Scheduling Engine:** Ability to set reports to "Daily," "Weekly," or "Monthly" delivery via email.
- **PDF Rendering:** Generation of professional, branded PDF documents containing tables and charts.
- **Archival:** All generated reports must be stored in an S3-compatible bucket for 7 years to meet aerospace regulatory requirements.

**Technical Implementation:**
- Use `Chromium` (via a headless wrapper) or `PdfGenerator` for high-fidelity PDF rendering.
- Use `Quantum` (cron-like scheduler for Elixir) to trigger scheduled reports.
- Reports will be generated as background jobs to avoid timeouts.

**Acceptance Criteria:**
- Scheduled reports are delivered exactly at the specified time.
- PDF output is compatible with all major PDF readers and maintains consistent formatting.

---

### 3.5 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** In Review (Nice to have)

**Description:**
A secure system to manage identities across different organizations (Buyers, Sellers, Auditors). Note: This is currently a lower priority as the team is focused on the core marketplace engine.

**Functional Specifications:**
- **Multi-Tenant Isolation:** Users must only see data belonging to their organization.
- **Role Hierarchy:** 
    - *Admin:* Full system access.
    - *Buyer:* Can create RFQs and purchase.
    - *Seller:* Can respond to RFQs and manage inventory.
    - *Auditor:* Read-only access to transaction logs.
- **MFA (Multi-Factor Authentication):** Requirement for TOTP (Time-based One Time Password) for all administrative accounts.

**Technical Implementation:**
- Use `phx.gen.auth` for the foundation of authentication.
- Implement a custom `Permission` table that maps roles to specific actions (e.g., `can_edit_price`, `can_approve_shipment`).
- JWT (JSON Web Tokens) for stateless API authentication.

**Acceptance Criteria:**
- A user with "Buyer" role cannot access the "Seller" dashboard.
- MFA challenge is triggered upon login for any user with the "Admin" role.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1`. All requests require a `Bearer` token in the header.

### 4.1 `POST /api/v1/parts/import`
- **Description:** Initiates the data import process for a part list.
- **Request Body:** `multipart/form-data` (File upload).
- **Response:** `202 Accepted`
- **Response Example:**
  ```json
  {
    "job_id": "job_abc_123",
    "status": "processing",
    "estimated_completion": "2026-06-15T10:00:00Z"
  }
  ```

### 4.2 `GET /api/v1/parts`
- **Description:** Retrieves a list of aerospace parts with filtering.
- **Query Params:** `?category=avionics&min_price=1000`
- **Response:** `200 OK`
- **Response Example:**
  ```json
  [
    { "id": 501, "name": "Altimeter X-1", "price": 1200.00, "status": "available" }
  ]
  ```

### 4.3 `PATCH /api/v1/rfq/{id}`
- **Description:** Updates a Request for Quote (RFQ) document.
- **Request Body:** `application/json`
  ```json
  { "specifications": "Tolerances updated to +/- 0.001mm" }
  ```
- **Response:** `200 OK`
- **Response Example:**
  ```json
  { "id": 88, "updated_at": "2026-06-15T12:00:00Z", "version": 4 }
  ```

### 4.4 `GET /api/v1/reports/scheduled`
- **Description:** Lists all active scheduled reports for the user.
- **Response:** `200 OK`
- **Response Example:**
  ```json
  [
    { "report_id": 10, "frequency": "weekly", "next_run": "2026-06-21" }
  ]
  ```

### 4.5 `POST /api/v1/notifications/preferences`
- **Description:** Sets user preferences for notification channels.
- **Request Body:**
  ```json
  { "email": true, "sms": false, "push": true }
  ```
- **Response:** `204 No Content`

### 4.6 `GET /api/v1/auth/session`
- **Description:** Validates the current session and returns user roles.
- **Response:** `200 OK`
- **Response Example:**
  ```json
  { "user_id": 123, "role": "buyer", "org": "Boeing-North" }
  ```

### 4.7 `POST /api/v1/orders/create`
- **Description:** Finalizes a purchase from a quote.
- **Request Body:**
  ```json
  { "quote_id": 554, "quantity": 10, "payment_method": "net_30" }
  ```
- **Response:** `201 Created`

### 4.8 `DELETE /api/v1/parts/{id}`
- **Description:** Soft-deletes a part from the marketplace.
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system uses PostgreSQL. All tables use `UUID` for primary keys to ensure scalability and security.

### 5.1 Table Definitions

1.  **`organizations`**
    - `id`: UUID (PK)
    - `name`: VARCHAR(255)
    - `tax_id`: VARCHAR(50)
    - `created_at`: TIMESTAMP
2.  **`users`**
    - `id`: UUID (PK)
    - `org_id`: UUID (FK -> organizations)
    - `email`: VARCHAR(255) (Unique)
    - `password_hash`: VARCHAR(255)
    - `role`: VARCHAR(20)
3.  **`parts`**
    - `id`: UUID (PK)
    - `seller_id`: UUID (FK -> users)
    - `part_number`: VARCHAR(100) (Index)
    - `description`: TEXT
    - `specs`: JSONB (For flexible aerospace attributes)
    - `price`: DECIMAL(12,2)
4.  **`rfqs` (Request for Quotes)**
    - `id`: UUID (PK)
    - `buyer_id`: UUID (FK -> users)
    - `status`: VARCHAR(20) (Draft, Open, Closed)
    - `content`: TEXT
    - `version`: INTEGER
5.  **`quotes`**
    - `id`: UUID (PK)
    - `rfq_id`: UUID (FK -> rfqs)
    - `seller_id`: UUID (FK -> users)
    - `proposed_price`: DECIMAL(12,2)
    - `valid_until`: TIMESTAMP
6.  **`orders`**
    - `id`: UUID (PK)
    - `quote_id`: UUID (FK -> quotes)
    - `quantity`: INTEGER
    - `total_amount`: DECIMAL(12,2)
    - `order_date`: TIMESTAMP
7.  **`notifications`**
    - `id`: UUID (PK)
    - `user_id`: UUID (FK -> users)
    - `channel`: VARCHAR(10) (Email, SMS, Push)
    - `message`: TEXT
    - `read_at`: TIMESTAMP
8.  **`report_schedules`**
    - `id`: UUID (PK)
    - `user_id`: UUID (FK -> users)
    - `frequency`: VARCHAR(20)
    - `metrics`: JSONB
9.  **`audit_logs`**
    - `id`: UUID (PK)
    - `user_id`: UUID (FK -> users)
    - `action`: VARCHAR(100)
    - `entity_id`: UUID
    - `timestamp`: TIMESTAMP
10. **`permissions`**
    - `id`: UUID (PK)
    - `role`: VARCHAR(20)
    - `action`: VARCHAR(50)
    - `allowed`: BOOLEAN

### 5.2 Relationships
- `Organizations` $\rightarrow$ `Users` (One-to-Many)
- `Users` $\rightarrow$ `Parts` (One-to-Many as Sellers)
- `Users` $\rightarrow$ `RFQs` (One-to-Many as Buyers)
- `RFQs` $\rightarrow$ `Quotes` (One-to-Many)
- `Quotes` $\rightarrow$ `Orders` (One-to-One)
- `Users` $\rightarrow$ `Notifications` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Bastion utilizes three distinct environments to ensure stability and SOC 2 compliance.

#### Development (Dev)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Local Docker containers and a shared "Dev" cluster on Fly.io.
- **Data:** Mock data only. No real customer PII.
- **Deployment:** Triggered on every push to a feature branch.

#### Staging (Staging)
- **Purpose:** Integration testing, QA, and UAT (User Acceptance Testing).
- **Infrastructure:** Exact mirror of Production on Fly.io.
- **Data:** Anonymized snapshot of production data.
- **Deployment:** Triggered by merge to the `develop` branch.

#### Production (Prod)
- **Purpose:** Live end-user environment.
- **Infrastructure:** High-availability Fly.io cluster with auto-scaling and multi-region failover.
- **Data:** Live encrypted data.
- **Deployment:** Triggered by tagged releases in GitLab CI. Rolling deployments are used to ensure zero downtime.

### 6.2 CI/CD Pipeline
1. **Build Stage:** Compile Elixir code, run `mix compile`.
2. **Test Stage:** Run `ex_unit` tests and static analysis (`Credo`).
3. **Security Stage:** Scan for dependency vulnerabilities (Audit) and run SOC 2 compliance checks.
4. **Deploy Stage:** Push Docker image to Fly.io registry $\rightarrow$ Rolling update to K8s pods.

### 6.3 Compliance and Security
To achieve **SOC 2 Type II**, the following infrastructure controls are implemented:
- **Encryption at Rest:** All PostgreSQL volumes are encrypted using AES-256.
- **Encryption in Transit:** TLS 1.3 for all API and WebSocket traffic.
- **Audit Trail:** Every mutation in the database is logged in the `audit_logs` table.
- **Access Control:** SSH access to production servers is disabled; all changes must go through the CI/CD pipeline.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Testing individual functions and modules (e.g., the CRDT logic in `Bastion.Collaboration`).
- **Tooling:** `ExUnit` (built-in Elixir).
- **Target:** 80% code coverage.
- **Requirement:** Every bug fix must be accompanied by a regression test.

### 7.2 Integration Testing
- **Scope:** Testing the interaction between modules and the database.
- **Tooling:** `Ecto.Schema` tests and database transactions.
- **Focus:** Ensuring that a "Quote" cannot be created without a valid "RFQ".

### 7.3 End-to-End (E2E) Testing
- **Scope:** Testing the entire user flow from login to order completion.
- **Tooling:** `Wallaby` (for browser automation).
- **Scenario:** "User uploads a CSV $\rightarrow$ Maps columns $\rightarrow$ Creates RFQ $\rightarrow$ Seller responds $\rightarrow$ Order placed."

### 7.4 Performance Testing
- **Scope:** Validating the 99.9% uptime and real-time latency.
- **Tooling:** `K6` for load testing.
- **Metric:** Response time for LiveView updates must remain under 200ms with 500 concurrent users.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Budget cut by 30% next quarter | High | High | Build a contingency plan; identify "Core" vs "Nice-to-have" features to cut if needed. Transition to a leaner hosting plan. |
| R2 | Team lacks Elixir/Phoenix experience | High | Medium | Assign Alejandro Fischer as the "Tech Lead" for stack-specific blockers. Budget for 2 weeks of intensive training. |
| R3 | Legal review of Data Processing Agreement (DPA) delays launch | Medium | High | Maintain daily communication with Legal. Implement a "restricted data" mode that allows dev to continue without PII. |
| R4 | The 3,000-line 'God Class' causes system failure | Medium | Medium | Schedule "Refactor Sprints" every 4th week to decompose the class into smaller, testable modules. |
| R5 | SOC 2 Compliance failure | Low | Critical | Engage a 3rd party auditor for a "pre-audit" 2 months before the target launch. |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required.
- **High/Medium:** Regular monitoring.
- **Low/Critical:** Contingency plan required.

---

## 9. TIMELINE

### 9.1 Project Phases

**Phase 1: Foundation (Month 1-2)**
- Setup Fly.io environment.
- Implement basic User Auth (though priority is low, it's needed for other features).
- Develop the "God Class" workaround to allow initial feature building.
- *Dependency:* Legal review of DPA must be completed.

**Phase 2: Core Engine (Month 3-4)**
- Build Data Import/Export engine.
- Implement Collaborative Editing (The launch blocker).
- Develop the RFQ and Quote workflow.
- *Dependency:* Success of CRDT implementation.

**Phase 3: Ecosystem & Compliance (Month 5-6)**
- Notification system implementation.
- Report generation and scheduling.
- SOC 2 final audit and remediation.
- *Dependency:* Full stability of Core Engine.

### 9.2 Key Milestones
- **2026-06-15:** Milestone 1: First paying customer onboarded. (Focus on "Happy Path" only).
- **2026-08-15:** Milestone 2: Internal alpha release. (Full feature set available for internal testing).
- **2026-10-15:** Milestone 3: Post-launch stability confirmed. (99.9% uptime over 30 days).

---

## 10. MEETING NOTES

*Note: These notes are extracted from the 200-page shared document. They are transcribed verbatim to capture team dynamics.*

### Meeting 1: Sprint 0 Kickoff (2025-11-01)
**Attendees:** Freya, Alejandro, Viktor, Yael.
- **Freya:** We are going with Elixir. It's the only way to hit the real-time requirements for the collaborative editor.
- **Alejandro:** None of us know Elixir. Why are we doing this?
- **Freya:** It's a moonshot. We learn as we go.
- **Yael:** I can handle the frontend if we use LiveView, but I'll need the API specs finalized first.
- **Viktor:** I'm concerned about the SOC 2 requirement. If we're just "learning as we go," we're going to fail the audit. We need a security-first approach from day one.
- **Decision:** Freya maintains the stack choice. Alejandro is tasked with setting up the Fly.io pipeline.

### Meeting 2: The "God Class" Crisis (2025-12-15)
**Attendees:** Freya, Alejandro, Viktor.
- **Alejandro:** I can't merge the new import logic because it conflicts with the `AuthAndLogAndEmail` class. It's 3,000 lines long. I can't even read the file in my IDE without it lagging.
- **Freya:** We don't have time to refactor. Just add your method to the bottom of the class.
- **Alejandro:** (Silence)
- **Viktor:** This is a security nightmare. The logging logic is intertwined with the password hashing. If one fails, the other might leak a hash to the logs.
- **Freya:** We'll fix it in Phase 3. Just get the import working.
- **Note:** Alejandro and Freya stop speaking for the remainder of the meeting.

### Meeting 3: The Blocked State (2026-01-20)
**Attendees:** Freya, Yael, Viktor.
- **Yael:** I'm blocked on the collaborative editing feature. I can't test the conflict resolution without the DPA being signed because we can't use real data in the staging environment.
- **Freya:** Legal is still reviewing the DPA. They're worried about the "data residency" clause in the Fly.io terms.
- **Viktor:** I've told Legal that we can restrict the region to US-East, but they aren't responding to my emails.
- **Yael:** If I don't have a way to simulate the multi-user environment, this is going to be a launch blocker.
- **Freya:** Just use mock data.
- **Yael:** The mock data doesn't simulate the latency we're seeing in the real-world aerospace network. It's useless.
- **Decision:** Feature 4 (Collaborative Editing) moved to "Blocked" status.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$800,000**

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $550,000 | 12-person team (including contractor Yael Liu) for 6 months. |
| **Infrastructure** | $80,000 | Fly.io managed K8s, PostgreSQL managed instances, S3 buckets. |
| **Tools & Licensing** | $40,000 | GitLab Premium, SendGrid, Twilio, SOC 2 Auditor fees. |
| **Training** | $30,000 | Specialized Elixir/Phoenix training and certifications for the team. |
| **Contingency** | $100,000 | Reserved for Risk R1 (Budget cut) or emergency scaling. |

**Budget Note:** The personnel cost is the primary driver. In the event of a 30% budget cut, the contingency fund will be exhausted first, followed by a reduction in contractor hours (Yael Liu).

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic (CRDT Detail)
To solve the "Launch Blocker" in Feature 4, the team will implement a **LWW-Element-Set (Last-Write-Wins)** for the part specifications. Each piece of data is stored as a tuple: `(value, timestamp)`.
When two users update a value:
1. The system compares the timestamps of the incoming update and the existing value.
2. The update with the higher timestamp is persisted.
3. For text blocks (e.g., "Engineering Notes"), a **RGA (Replicated Growable Array)** will be used to allow insertions and deletions of characters without overwriting other users' work.

### Appendix B: SOC 2 Compliance Checklist
The following items must be verified by Viktor Costa before the October 15th stability milestone:
- [ ] **Access Control:** Quarterly review of user permissions.
- [ ] **Change Management:** All production changes tied to a GitLab Merge Request with two approvals.
- [ ] **Incident Response:** Documented process for reporting and remediating data breaches.
- [ ] **Vendor Management:** Verified SOC 2 reports for Fly.io and SendGrid.
- [ ] **Data Encryption:** Verification that all `password_hash` fields use Argon2id.