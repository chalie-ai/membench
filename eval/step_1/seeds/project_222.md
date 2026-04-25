Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. It is structured as the primary source of truth for the development team at Hearthstone Software.

***

# PROJECT SPECIFICATION: PROJECT GANTRY
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Last Updated:** 2024-10-24  
**Document Owner:** Dmitri Kim, Engineering Manager  
**Classification:** Internal – Confidential  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Gantry represents the most critical infrastructure overhaul in the history of Hearthstone Software. For 15 years, our logistics and shipping operations have relied on a legacy monolithic system—a "black box" of procedural code and aging Oracle triggers. While this system served the company during its growth phase, it has now become a bottleneck to scalability. The legacy system's fragility means that a single bug in the shipping manifest module can crash the entire global routing engine, leading to catastrophic operational downtime.

In the current logistics market, agility is the primary competitive advantage. The legacy system prevents the company from implementing rapid changes to routing logic and prohibits the introduction of modern API integrations with third-party carriers. Furthermore, the operational cost of maintaining the legacy hardware and the "tribal knowledge" required to keep it running is unsustainable.

Project Gantry is the strategic migration of this legacy monolith into a modern, API-driven microservices architecture. By introducing an API Gateway (the "Gantry"), we decouple the client-facing interfaces from the backend business logic, allowing us to strangle the monolith incrementally. We are moving from a rigid, single-tier application to a modular monolith that will eventually evolve into a fully distributed microservices mesh.

### 1.2 ROI Projection and Financial Impact
The project is backed by a $1.5M budget. The Return on Investment (ROI) is calculated based on three primary pillars:

1.  **Reduction in Transactional Costs:** The legacy system processes requests via inefficient, long-running stored procedures that lock database tables. By migrating to Spring Boot services with optimized connection pooling and a refined data access layer, we project a **35% reduction in cost per transaction**. This is achieved through lower CPU overhead per request and reduced database contention.
2.  **Operational Uptime:** With zero downtime tolerance, the move to blue-green deployments eliminates the "maintenance windows" that currently cost the company approximately $12,000 per hour in lost productivity during updates.
3.  **Market Agility:** The ability to deploy new features (such as the Workflow Automation Engine) in days rather than months allows Hearthstone to capture market share from competitors who are currently bogged down by legacy debt.

**Projected 3-Year ROI:** 215% based on reduced infrastructure overhead and increased shipment throughput.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architecture Philosophy
Project Gantry utilizes the **Strangler Fig Pattern**. We will not perform a "big bang" migration. Instead, we will place an API Gateway in front of the legacy system. New features will be built as microservices; existing features will be migrated one module at a time.

### 2.2 Technical Stack
- **Language/Framework:** Java 21, Spring Boot 3.2.x (Spring Cloud Gateway)
- **Database:** Oracle DB 19c (On-premise)
- **Infrastructure:** Dedicated on-premise data center (No cloud/AWS/Azure per corporate policy)
- **CI/CD:** GitHub Actions (Self-hosted runners)
- **Deployment:** Blue-Green Deployment strategy via Nginx load balancers
- **Communication:** REST for external APIs, gRPC for internal service-to-service communication

### 2.3 Architecture Diagram (ASCII Representation)

```text
[ Client Tier ] ----> [ Load Balancer (Nginx) ]
                              |
                              v
                    [ Gantry API Gateway ] <--- (Spring Cloud Gateway)
                              |
         _____________________|_____________________
        |                     |                     |
        v                     v                     v
[ Service: Workflow ]  [ Service: Offline/Sync ]  [ Service: Audit ]
        |                     |                     |
        |                     |                     |
        +---------------------+---------------------+
                              |
                              v
                    [ Oracle DB 19c Cluster ] <--- (Shared Data Layer)
                              |
                              +---> [ Legacy Monolith Database Tables ]
```

### 2.4 System Components
- **The Gantry Gateway:** Handles authentication, rate limiting, and request routing. It acts as the single entry point.
- **Modular Monolith Transition:** Initially, services share the Oracle DB schema to avoid complex distributed transactions (Saga pattern) during the early migration phase.
- **On-Premise Constraints:** Since no cloud is allowed, we utilize physical blade servers with VMware virtualization to simulate environment isolation.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
The Workflow Automation Engine allows logistics managers to define "If-Then-Else" logic for shipment routing without writing code. For example: *"If shipment weight > 500kg AND destination is International, THEN assign to Heavy-Lift Carrier X."*

**Functional Requirements:**
1.  **Visual Rule Builder:** A drag-and-drop interface (implemented in React) that compiles into a JSON-based rule definition.
2.  **Rule Engine:** A backend evaluator using a modified version of the Drools engine or a custom expression language (SpEL) to process shipment data against the rules.
3.  **Trigger Events:** Rules can be triggered by API calls, database changes (via Change Data Capture), or scheduled intervals.
4.  **Version Control:** Each rule set must be versioned. Changes to a workflow must be saved as a new version to allow rollbacks.

**Technical Detail:**
The engine will utilize a `WorkflowDefinition` table in Oracle. When a shipment enters the system, the `WorkflowService` fetches the active rule set, parses the shipment's attributes, and executes the logic sequence. 

**Acceptance Criteria:**
- Ability to create a rule with 5 nested conditions.
- Execution time for rule evaluation must be < 100ms.
- Visual builder must synchronize in real-time with the JSON definition.

---

### 3.2 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Logistics personnel often work in warehouses with "dead zones" (no Wi-Fi/Cellular). This feature ensures the application remains fully functional offline, syncing data once a connection is re-established.

**Functional Requirements:**
1.  **Local Persistence:** Use IndexedDB in the browser to store a local copy of the shipment manifests and current tasks.
2.  **Change Tracking:** Every mutation performed offline must be queued in an "Outbox" table within the local browser storage, timestamped and sequenced.
3.  **Background Synchronization:** A service worker that monitors network connectivity. Upon reconnection, it pushes the Outbox queue to the Gantry API.
4.  **Conflict Resolution:** A "Last-Write-Wins" strategy by default, with a prompt for manual resolution if a record was modified by another user during the offline period.

**Technical Detail:**
The API must support "Idempotency Keys." When the background sync pushes a batch of updates, the server uses these keys to ensure that a network flicker doesn't result in duplicate shipment entries.

**Acceptance Criteria:**
- User can create a shipment manifest while Airplane Mode is enabled.
- Upon disabling Airplane Mode, data is synced to the Oracle DB within 5 seconds.
- No data loss during intermittent connectivity transitions.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Not Started

**Description:**
For legal and compliance reasons in shipping, every change to a shipment’s status must be logged. This system must be "tamper-evident," meaning any attempt to alter the logs must be detectable.

**Functional Requirements:**
1.  **Immutable Logs:** Once a log entry is written, it cannot be updated or deleted.
2.  **Cryptographic Chaining:** Each log entry will contain a SHA-256 hash of the previous entry, creating a chain (similar to a blockchain).
3.  **Automatic Capture:** All `POST`, `PUT`, and `DELETE` requests passing through the Gantry Gateway are automatically mirrored to the Audit Service.
4.  **Audit Viewer:** A read-only interface for administrators to verify the integrity of the logs.

**Technical Detail:**
The `AuditLog` table will store the `payload`, `timestamp`, `userId`, and `previous_hash`. A nightly cron job will verify the hash chain from the start of the day to the end. If a hash mismatch is found, an alert is sent to the Project Lead.

**Acceptance Criteria:**
- Ability to reconstruct the history of a shipment across 10 different status changes.
- Verification script must detect a single bit-flip in the database logs.

---

### 3.4 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Low (Nice to Have) | **Status:** In Design

**Description:**
Allow multiple dispatchers to edit the same shipment manifest simultaneously, seeing each other's cursors and changes in real-time.

**Functional Requirements:**
1.  **WebSocket Integration:** Use Spring WebSockets (STOMP) to push updates to all connected clients.
2.  **Operational Transformation (OT):** Implement a basic OT algorithm to handle concurrent text edits in the "Notes" section of a shipment.
3.  **Presence Indicators:** Show who is currently viewing/editing a specific record.
4.  **Locking Mechanism:** For critical fields (like "Final Destination"), implement a "soft lock" where the first person to click the field gains editing rights.

**Technical Detail:**
The system will maintain a "Shadow Document" on the server. Client updates are sent as "diffs." The server applies the diff and broadcasts it to other clients.

**Acceptance Criteria:**
- Two users editing the same note should see changes within 200ms of each other.
- No "ghost" text or overlapping characters during simultaneous typing.

---

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low (Nice to Have) | **Status:** Blocked

**Description:**
Expand the system to support 12 different languages to accommodate global shipping hubs (English, Mandarin, Spanish, French, German, Japanese, Korean, Arabic, Portuguese, Hindi, Russian, Dutch).

**Functional Requirements:**
1.  **Resource Bundles:** Use Java `ResourceBundle` for all static UI text.
2.  **Dynamic Content Translation:** Integration with a translation API for shipment descriptions.
3.  **Locale Detection:** Automatically detect user language based on browser headers or user profile settings.
4.  **RTL Support:** Support for Right-to-Left (RTL) layouts for Arabic.

**Technical Detail:**
Database tables for "Product Categories" and "Carrier Names" will be moved to a translated schema: `Category` -> `Category_Translations` (with `locale_id` as a foreign key).

**Acceptance Criteria:**
- Switching language in the settings menu updates the entire UI without a page reload.
- Correct rendering of non-Latin characters (UTF-8).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Base URL: `https://gantry.internal.hearthstone.com/api/v1/`

### 4.1 Shipment Management

**Endpoint 1: Create Shipment**
- **Path:** `POST /shipments`
- **Description:** Creates a new shipping manifest.
- **Request Body:**
  ```json
  {
    "origin": "HOU-01",
    "destination": "LON-04",
    "weight": 450.5,
    "priority": "HIGH",
    "items": ["SKU-101", "SKU-202"]
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "shipmentId": "SHIP-992834",
    "status": "PENDING",
    "createdAt": "2025-01-10T10:00:00Z"
  }
  ```

**Endpoint 2: Get Shipment Details**
- **Path:** `GET /shipments/{id}`
- **Description:** Retrieves detailed info for a specific shipment.
- **Response (200 OK):**
  ```json
  {
    "id": "SHIP-992834",
    "currentLocation": "Warehouse-A",
    "estimatedArrival": "2025-01-15",
    "workflowStatus": "ROUTING"
  }
  ```

**Endpoint 3: Update Shipment Status**
- **Path:** `PATCH /shipments/{id}/status`
- **Description:** Updates the current status (e.g., from PENDING to SHIPPED).
- **Request Body:**
  ```json
  {
    "status": "SHIPPED",
    "updatedBy": "USER-44"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "shipmentId": "SHIP-992834",
    "newStatus": "SHIPPED"
  }
  ```

### 4.2 Workflow Automation

**Endpoint 4: Create Workflow Rule**
- **Path:** `POST /workflows/rules`
- **Description:** Defines a new automation rule.
- **Request Body:**
  ```json
  {
    "ruleName": "Heavy-Lift Logic",
    "conditions": {
      "field": "weight",
      "operator": "GREATER_THAN",
      "value": 500
    },
    "action": "ASSIGN_CARRIER_X"
  }
  ```
- **Response (201 Created):**
  ```json
  { "ruleId": "RULE-001", "status": "ACTIVE" }
  ```

**Endpoint 5: Trigger Workflow Manually**
- **Path:** `POST /workflows/execute/{shipmentId}`
- **Description:** Manually forces the workflow engine to evaluate a shipment.
- **Response (200 OK):**
  ```json
  { "result": "ASSIGNED", "carrier": "Carrier-X" }
  ```

### 4.3 Sync and Audit

**Endpoint 6: Background Sync Batch**
- **Path:** `POST /sync/batch`
- **Description:** Accepts a list of offline mutations.
- **Request Body:**
  ```json
  {
    "batchId": "B-882",
    "mutations": [
      { "action": "UPDATE", "id": "SHIP-1", "data": { "status": "DELIVERED" }, "timestamp": "2025-01-10T12:00:00Z" },
      { "action": "CREATE", "id": "SHIP-2", "data": { "origin": "NYC" }, "timestamp": "2025-01-10T12:05:00Z" }
    ]
  }
  ```
- **Response (207 Multi-Status):**
  ```json
  { "processed": 2, "failures": 0 }
  ```

**Endpoint 7: Get Audit Log**
- **Path:** `GET /audit/logs/{shipmentId}`
- **Description:** Returns the immutable history of a shipment.
- **Response (200 OK):**
  ```json
  [
    { "timestamp": "...", "change": "STATUS_CHANGE", "old": "PENDING", "new": "SHIPPED", "hash": "a1b2c3..." },
    { "timestamp": "...", "change": "WEIGHT_UPDATE", "old": "400", "new": "450", "hash": "d4e5f6..." }
  ]
  ```

**Endpoint 8: System Health Check**
- **Path:** `GET /health`
- **Description:** Returns status of Gantry Gateway and connectivity to Oracle DB.
- **Response (200 OK):**
  ```json
  { "status": "UP", "database": "CONNECTED", "uptime": "45d 12h" }
  ```

---

## 5. DATABASE SCHEMA (ORACLE 19c)

The database is a shared Oracle cluster. We use a schema-per-service approach but maintain foreign keys for data integrity during the migration.

### 5.1 Tables and Relationships

| Table Name | Description | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `SHIPMENTS` | Primary shipment data | `shipment_id` (PK), `origin_id`, `dest_id`, `weight`, `status` | FK to `LOCATIONS` |
| `LOCATIONS` | Shipping hubs/warehouses | `location_id` (PK), `city`, `country_code`, `timezone` | - |
| `WORKFLOW_RULES` | Defined automation rules | `rule_id` (PK), `rule_name`, `json_definition`, `version` | - |
| `WORKFLOW_LOGS` | Execution history of rules | `log_id` (PK), `shipment_id` (FK), `rule_id` (FK), `result` | FK to `SHIPMENTS`, `WORKFLOW_RULES` |
| `AUDIT_TRAIL` | Tamper-evident logs | `audit_id` (PK), `entity_id`, `entity_type`, `payload`, `prev_hash` | - |
| `USERS` | System users/staff | `user_id` (PK), `username`, `role`, `email` | - |
| `USER_SESSIONS` | Active session tracking | `session_id` (PK), `user_id` (FK), `last_active` | FK to `USERS` |
| `SYNC_QUEUE` | Tracking background syncs | `sync_id` (PK), `batch_id`, `status`, `processed_at` | - |
| `CARRIERS` | Third party shipping companies | `carrier_id` (PK), `name`, `service_level`, `api_key` | - |
| `SHIPMENT_ITEMS` | Items within a shipment | `item_id` (PK), `shipment_id` (FK), `sku`, `quantity` | FK to `SHIPMENTS` |

### 5.2 Key Constraints and Indices
- **B-Tree Index** on `SHIPMENTS(status)` to optimize the Workflow Engine’s polling.
- **Unique Constraint** on `AUDIT_TRAIL(audit_id)` to prevent duplication.
- **Foreign Key** from `SHIPMENT_ITEMS` to `SHIPMENTS` with `ON DELETE CASCADE` to maintain cleanup.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We maintain three distinct environments on our on-premise hardware.

#### 6.1.1 Development (DEV)
- **Purpose:** Individual feature development and unit testing.
- **Config:** Single instance of Spring Boot, H2 In-Memory DB (for some tests), and a shared Oracle DEV instance.
- **Deployment:** Automatic trigger on push to `develop` branch via GitHub Actions.

#### 6.1.2 Staging (STG)
- **Purpose:** QA, Integration testing, and User Acceptance Testing (UAT).
- **Config:** Mirror of Production hardware. Full Oracle DB cluster.
- **Deployment:** Manual trigger after QA approval of the `release` branch.

#### 6.1.3 Production (PROD)
- **Purpose:** Live shipping operations.
- **Config:** High-availability cluster. 3x Application Nodes, 2x Oracle RAC Nodes.
- **Deployment:** Blue-Green strategy.
    - **Blue:** Current stable version.
    - **Green:** New version deployed and smoke-tested.
    - **Switch:** Nginx swaps traffic to Green. If errors spike, Nginx reverts to Blue in < 1 second.

### 6.2 CI/CD Pipeline
1. **Commit:** Developer pushes to GitHub.
2. **Build:** GitHub Actions runs Maven build and executes JUnit tests.
3. **Scan:** Static analysis via SonarQube (On-prem).
4. **Artifact:** Docker image is built and pushed to the internal Docker Registry.
5. **Deploy:** Ansible scripts push the image to the target environment (DEV/STG/PROD).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5, Mockito.
- **Coverage Goal:** 80% line coverage.
- **Focus:** Business logic in the Workflow Engine and data mapping in the API Gateway.

### 7.2 Integration Testing
- **Framework:** Testcontainers (using an Oracle XE container).
- **Focus:** API endpoint contracts, database transaction integrity, and gRPC communication between services.
- **Scenario:** Test a "Sync Batch" to ensure it handles partial failures (e.g., 1 success, 1 failure).

### 7.3 End-to-End (E2E) Testing
- **Framework:** Playwright.
- **Focus:** The "Happy Path" of a shipment from creation $\rightarrow$ Workflow Assignment $\rightarrow$ Shipping $\rightarrow$ Audit.
- **Critical Test:** "The Tunnel Test" — Simulate a network disconnect, perform 5 updates in the UI, reconnect, and verify all 5 updates appear in the Oracle DB.

### 7.4 Performance Testing
- **Tool:** JMeter.
- **Target:** 500 requests per second (RPS) with a 95th percentile latency of < 200ms.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Competitor is 2 months ahead in product delivery. | High | High | Negotiate timeline extension with stakeholders to ensure quality; prioritize "Launch Blockers" over "Nice to Haves." |
| **R2** | Team lacks experience with Spring Boot/Oracle 19c. | Medium | High | Engage an external consultant for a 4-week architectural audit and weekly mentorship sessions. |
| **R3** | Legacy system crashes during the "Strangler" phase. | Low | Critical | Implement a "Kill Switch" in the API Gateway to route all traffic back to the legacy system instantly. |
| **R4** | On-prem hardware failure during migration. | Low | Medium | Ensure full RAID-10 redundancy and daily off-site backups of the Oracle DB. |

**Probability/Impact Matrix:**
- **Critical:** Immediate escalation to Dmitri Kim.
- **High:** Weekly monitoring in Slack.
- **Medium/Low:** Addressed during Sprint Planning.

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation (Now $\rightarrow$ 2024-12-31)
- **Focus:** API Gateway setup, Oracle DB schema migration, and core "Launch Blocker" features.
- **Dependencies:** Hardware provisioning must be complete.
- **Key Deliverable:** Gantry Gateway routing traffic to the legacy system.

### 9.2 Phase 2: Pilot Onboarding (2025-01-01 $\rightarrow$ 2025-03-15)
- **Focus:** Finalizing Workflow Engine and Offline Sync.
- **Milestone 1:** First paying customer onboarded (Target: 2025-03-15).
- **Dependencies:** Completion of E2E "Tunnel Test."

### 9.3 Phase 3: Beta Expansion (2025-03-16 $\rightarrow$ 2025-05-15)
- **Focus:** Stability, Audit Trail implementation, and performance tuning.
- **Milestone 2:** External beta with 10 pilot users (Target: 2025-05-15).
- **Dependencies:** Success of Milestone 1.

### 9.4 Phase 4: Hardening and Launch (2025-05-16 $\rightarrow$ 2025-07-15)
- **Focus:** Bug fixing and final stability checks.
- **Milestone 3:** Post-launch stability confirmed (Target: 2025-07-15).
- **Dependencies:** 80% feature adoption rate among pilot users.

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per team culture, no formal minutes are kept. The following are synthesized from the #project-gantry Slack channel.*

### Thread 1: The "Cloud Question" (2024-09-12)
**Dmitri Kim:** "Can we move the Audit service to a managed cloud instance for better scaling?"
**Freya Oduya:** "Legal says absolutely not. No cloud allowed for any part of the Gantry project. Everything must stay on-prem."
**Anouk Oduya:** "That means we need to handle our own backups and scaling for the audit logs. I'll start looking at RAID configurations."
**Decision:** Project remains 100% on-premise.

### Thread 2: Workflow Priority (2024-10-05)
**Ola Moreau:** "The Visual Rule Builder is still buggy. We can't launch with the current UI."
**Dmitri Kim:** "Agreed. It's a launch blocker. Freya, can we pivot the contractor (Anouk) to help with the backend logic of the engine while you focus on the React components?"
**Freya Oduya:** "Works for me. Anouk has the Oracle experience we need for the rule-storage triggers."
**Decision:** Workflow Engine prioritized as a critical launch blocker.

### Thread 3: The "Competitor Panic" (2024-11-01)
**Dmitri Kim:** "Intelligence says our main competitor is about 2 months ahead of us on a similar API gateway."
**Anouk Oduya:** "Should we cut the Collaborative Editing feature to catch up?"
**Dmitri Kim:** "Yes. Collaborative editing and Localization are now 'Low Priority/Nice to Have.' We focus purely on the Workflow Engine and Offline Sync. I will negotiate a timeline extension with stakeholders to ensure we don't ship a broken product."
**Decision:** Feature set narrowed to ensure stability; "Nice to Haves" moved to the bottom of the backlog.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $950,000 | 8 staff members (inc. Senior Backend, QA Lead, Contractor) for 12 months. |
| **Infrastructure** | $300,000 | On-prem blade servers, Oracle 19c Licensing, VMware licenses. |
| **External Tools** | $100,000 | SonarQube, Playwright Enterprise, JMeter plugins, GitHub Actions self-hosted runners. |
| **Consultancy** | $50,000 | Independent architectural assessment for the chosen tech stack. |
| **Contingency** | $100,000 | Emergency hardware replacement or additional contractor hours. |

**Budget Status:** On track. No overages reported.

---

## 12. APPENDICES

### Appendix A: Conflict Resolution Logic for Offline Sync
The system utilizes a **Vector Clock** mechanism to track causality. Each update to a shipment is tagged with a version number and a client ID. When syncing:
1. The server compares the client's version number with the database version.
2. If `client_version == db_version + 1`, the update is applied automatically.
3. If `client_version <= db_version`, a conflict is flagged.
4. For conflicts, the "Last-Write-Wins" (LWW) policy is applied unless the field is marked as "Critical," in which case the record is moved to a `MANUAL_RESOLUTION` table for human review.

### Appendix B: Tamper-Evidence Algorithm
The Audit Trail uses the following hashing logic for every entry:
$\text{Hash}_n = \text{SHA-256}(\text{Payload}_n + \text{Timestamp}_n + \text{Hash}_{n-1})$

To verify the chain, the system runs a linear scan:
```java
public boolean verifyIntegrity(List<AuditEntry> logs) {
    for (int i = 1; i < logs.size(); i++) {
        String calculatedHash = calculateHash(logs.get(i), logs.get(i-1).getHash());
        if (!calculatedHash.equals(logs.get(i).getHash())) {
            return false; // Tampering detected
        }
    }
    return true;
}
```
This ensures that any modification to a historical log entry invalidates all subsequent hashes in the chain.