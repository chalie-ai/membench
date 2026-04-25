# PROJECT SPECIFICATION DOCUMENT: WAYFINDER
**Version:** 1.0.4  
**Date:** October 26, 2023  
**Document Status:** Baseline  
**Project Owner:** Deepwell Data  
**Project Lead:** Beau Gupta (Tech Lead)  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
The "Wayfinder" project is a strategic imperative for Deepwell Data. For fifteen years, the company has relied on a monolithic legacy system to facilitate its legal services operations. This legacy system, while stable, has become a critical point of failure. It is built on outdated architecture that cannot scale to meet the current demands of the legal industry, specifically regarding data throughput, concurrent user access, and real-time collaboration. 

The current system is a "black box" that prevents the company from iterating on product features, slowing down the onboarding of new legal clients and limiting the ability to implement modern compliance and reporting standards. Because the entire company depends on this system for daily operations, there is a **zero downtime tolerance** policy. Any outage during the transition to Wayfinder would result in immediate revenue loss and potential legal liability for Deepwell Data.

Wayfinder is designed not merely as a replacement, but as a force multiplier. By moving to a modern stack (Rust, React, and Cloudflare Workers), Deepwell Data will transition from a centralized, sluggish database to a distributed, edge-computing model. This allows legal professionals to access case files and reports with sub-100ms latency regardless of their global location.

### 1.2 ROI Projection
The financial justification for Wayfinder is rooted in two primary drivers: operational efficiency and new market penetration. 

**Revenue Growth:** The primary success metric is the generation of $500,000 in new revenue within 12 months of the internal alpha release. This will be achieved by unlocking a "Premium Tier" of legal reporting and collaborative tools that the legacy system cannot support. By offering real-time collaborative editing and high-fidelity PDF report scheduling, Deepwell Data can move from a flat-fee model to a value-based subscription model.

**Cost Reduction:** While the project is currently unfunded and bootstrapping using existing team capacity (reducing immediate CAPEX), the long-term OPEX will decrease. The migration from legacy on-premise servers to Cloudflare Workers and SQLite at the edge will reduce infrastructure overhead by an estimated 40%.

**Risk Mitigation:** The legacy system's lack of structured logging and outdated security protocols represents a significant business risk. Wayfinder implements a CQRS (Command Query Responsibility Segregation) architecture with event sourcing, providing an immutable audit trail of every change—a non-negotiable requirement for legal services. The ROI here is the avoidance of potential multi-million dollar fines associated with data loss or audit failure.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The Stack
Wayfinder utilizes a highly decoupled, performant stack designed for low latency and high reliability.

- **Backend:** Rust. Chosen for memory safety and execution speed, ensuring the 10x performance requirement is met without additional infrastructure spend.
- **Frontend:** React. Provides a responsive, component-based UI for the complex legal dashboards.
- **Edge Layer:** Cloudflare Workers. Handles request routing, authentication, and lightweight compute at the edge to minimize latency.
- **Storage:** SQLite (Edge). Used for local caching and edge-side state management to ensure the application remains responsive even during transient network failures.
- **Architecture Pattern:** CQRS with Event Sourcing. 
    - **Command Side:** Handles updates to the system, validating business rules and emitting events.
    - **Query Side:** Specialized read-models optimized for the dashboard and reporting, updated asynchronously via the event store.

### 2.2 Architecture Diagram (ASCII Representation)
The following represents the data flow from the client to the persistent store.

```text
[ Client: React Mobile App ] 
           |
           v (HTTPS / WebSocket)
[ Cloudflare Workers (Edge Gateway) ] <---> [ SQLite Edge Cache ]
           |
           +------> [ Command Service (Rust) ] ------> [ Event Store (Append-Only) ]
           |                                                 |
           |                                                 v
           +------> [ Query Service (Rust) ] <--------- [ Projections/Read Models ]
                                                             |
                                                             v
                                                   [ PDF/CSV Export Engine ]
```

### 2.3 Design Rationale
The choice of CQRS is driven by the "audit-critical" nature of legal services. In a standard CRUD application, the current state is stored, and history is lost. In Wayfinder, every change is an event. This means we can reconstruct the state of any legal document at any specific microsecond in the past, providing an infallible audit trail.

The "Bus Factor of 1" risk is acknowledged; currently, Saoirse Nakamura is the only person capable of executing the manual deployment pipeline. To mitigate this, the deployment scripts are being versioned in Git, though the process remains manual.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Critical (Launch Blocker) | **Status:** In Progress

**Description:**
Legal professionals require the ability to generate immutable snapshots of case data in PDF and CSV formats. These reports must be capable of being scheduled for recurring delivery (e.g., "Every Monday at 8 AM") to external stakeholders via email.

**Functional Requirements:**
- **Template Engine:** Users must be able to select from pre-defined legal templates.
- **Data Extraction:** The system must query the Read-Model of the CQRS architecture to pull the latest state of a case.
- **Scheduling Logic:** A cron-based trigger within the Rust backend to initiate report generation.
- **Delivery Pipeline:** Integration with an SMTP relay to deliver the generated files as attachments.

**Technical Specifications:**
The report generation is handled by a dedicated worker thread to avoid blocking the main event loop. For PDFs, the system uses a headless Chromium instance (via a Cloudflare Worker wrapper) to render HTML to PDF. For CSVs, a streaming serializer is used to handle large datasets without overloading memory.

**Acceptance Criteria:**
- Successfully generate a PDF containing 100+ pages of legal text.
- Schedule a report to trigger at a specific UTC time and deliver within 5 minutes of that time.
- CSV exports must maintain UTF-8 encoding for international legal characters.

---

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** In Review

**Description:**
The dashboard serves as the primary landing page for legal users. Given the variety of roles (Paralegal, Partner, Auditor), a "one size fits all" view is insufficient. This feature allows users to personalize their workspace.

**Functional Requirements:**
- **Widget Library:** A set of standard widgets (e.g., "Upcoming Deadlines," "Case Load Distribution," "Recent Edits").
- **Drag-and-Drop Interface:** Ability to move widgets across a grid system (React-Grid-Layout).
- **Configuration Persistence:** The layout state must be saved to the user's profile in the database.
- **Widget Sizing:** Widgets should be resizable (Small, Medium, Large).

**Technical Specifications:**
The frontend uses a JSON-based layout schema. When a user moves a widget, a `UpdateDashboardLayout` command is sent to the Rust backend. The backend validates that the user has the permissions to view the data within that widget before persisting the change.

**Acceptance Criteria:**
- User can rearrange three widgets and have the layout persist after a page refresh.
- Dashboard loads in under 200ms by utilizing the SQLite edge cache for layout configurations.

---

### 3.3 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Review

**Description:**
Multiple legal users must be able to edit the same case document simultaneously without overwriting each other's changes.

**Functional Requirements:**
- **Presence Indicators:** Show who is currently editing the document.
- **Cursors:** Real-time cursor tracking across the document.
- **Conflict Resolution:** Use of Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency.

**Technical Specifications:**
The system implements a Yjs-based CRDT layer. The Rust backend acts as the central authority and persistence layer for the Yjs updates. Changes are streamed via WebSockets through Cloudflare Workers. Since the legacy system did not support concurrency, this represents a massive leap in functionality.

**Acceptance Criteria:**
- Two users editing the same paragraph simultaneously must see both sets of changes merge without a "Save Conflict" dialogue.
- Latency for cursor updates must be below 50ms.

---

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to have) | **Status:** In Review

**Description:**
To facilitate the migration from the legacy system, Wayfinder needs a robust way to ingest old data.

**Functional Requirements:**
- **Format Detection:** System must automatically detect if a file is CSV, JSON, or XML.
- **Mapping Tool:** A UI to map legacy column headers to Wayfinder's database fields.
- **Bulk Export:** The ability to export entire case archives for external audits.

**Technical Specifications:**
The import process is treated as a "Saga" in the event-sourcing model. An `ImportStarted` event is fired, followed by individual `RecordImported` events. If a record fails, the system logs the error and continues, providing a final "Import Summary" report.

**Acceptance Criteria:**
- Successful import of a 50MB CSV file with 10,000 rows in under 30 seconds.
- Correct identification of file type based on magic bytes rather than just extension.

---

### 3.5 A/B Testing Framework (Feature Flag System)
**Priority:** Low (Nice to have) | **Status:** In Design

**Description:**
To ensure new features don't disrupt the legal workflow, the team needs to roll out features to small percentages of the user base.

**Functional Requirements:**
- **Flag Toggles:** Ability to enable/disable features without a full deployment.
- **Percentage Rollout:** Ability to target a specific percentage of users (e.g., 10% of users see the new dashboard).
- **Analytics Integration:** Link flags to success metrics (e.g., does the new report UI reduce time-to-export?).

**Technical Specifications:**
Feature flags are stored as a configuration object in the SQLite edge cache. When the React frontend requests the app state, the Cloudflare Worker injects the active flags based on the UserID's hash.

**Acceptance Criteria:**
- Ability to toggle a feature "ON" for a specific user ID via the admin panel.
- No impact on page load time (flags must be evaluated at the edge).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the Authorization header.

### 4.1 `POST /cases`
**Description:** Creates a new legal case.
- **Request Body:**
  ```json
  {
    "case_name": "Doe vs. State",
    "client_id": "CL-9928",
    "priority": "High",
    "category": "Civil"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "case_id": "uuid-1234-5678",
    "status": "Created",
    "created_at": "2023-10-26T10:00:00Z"
  }
  ```

### 4.2 `GET /cases/{id}`
**Description:** Retrieves the current state of a specific case (Query side).
- **Response (200 OK):**
  ```json
  {
    "id": "uuid-1234-5678",
    "name": "Doe vs. State",
    "summary": "Detailed case notes...",
    "version": 42
  }
  ```

### 4.3 `POST /cases/{id}/events`
**Description:** Appends a new event to the case event stream (Command side).
- **Request Body:**
  ```json
  {
    "event_type": "NoteAdded",
    "payload": { "text": "Witness contacted on 10/25", "author": "Beau G." }
  }
  ```
- **Response (202 Accepted):**
  ```json
  { "event_id": "evt-998", "sequence": 43 }
  ```

### 4.4 `GET /reports/templates`
**Description:** Lists available PDF/CSV templates.
- **Response (200 OK):**
  ```json
  [
    { "id": "tmpl_01", "name": "Quarterly Audit", "type": "PDF" },
    { "id": "tmpl_02", "name": "Case Summary", "type": "CSV" }
  ]
  ```

### 4.5 `POST /reports/schedule`
**Description:** Schedules a recurring report delivery.
- **Request Body:**
  ```json
  {
    "template_id": "tmpl_01",
    "recipient": "legal-audit@deepwell.com",
    "cron_schedule": "0 8 * * 1"
  }
  ```
- **Response (201 Created):**
  ```json
  { "schedule_id": "sch-554", "next_run": "2023-10-30T08:00:00Z" }
  ```

### 4.6 `PATCH /user/dashboard/layout`
**Description:** Updates the drag-and-drop widget configuration.
- **Request Body:**
  ```json
  {
    "widgets": [
      { "id": "w1", "x": 0, "y": 0, "w": 6, "h": 4 },
      { "id": "w2", "x": 6, "y": 0, "w": 6, "h": 4 }
    ]
  }
  ```
- **Response (200 OK):**
  ```json
  { "status": "updated" }
  ```

### 4.7 `GET /health`
**Description:** System health check for monitoring.
- **Response (200 OK):**
  ```json
  { "status": "healthy", "version": "1.0.4", "uptime": "45d" }
  ```

### 4.8 `POST /import/detect`
**Description:** Uploads a file to detect its format without importing.
- **Request:** Multipart File Upload.
- **Response (200 OK):**
  ```json
  { "detected_format": "CSV", "confidence": 0.98, "encoding": "UTF-8" }
  ```

---

## 5. DATABASE SCHEMA

Wayfinder uses a hybrid approach: a relational store for user/config data and an event store for domain data.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role`, `timezone` | 1:M with `dashboard_configs` | System users and authentication. |
| `cases` | `case_id` | `case_name`, `client_id`, `created_at` | 1:M with `events` | Header record for a legal case. |
| `events` | `event_id` | `case_id`, `sequence_num`, `event_type`, `payload` | M:1 with `cases` | The immutable event stream (Event Sourcing). |
| `projections_case` | `case_id` | `last_updated`, `current_summary`, `total_notes` | 1:1 with `cases` | Read-model for fast case retrieval. |
| `clients` | `client_id` | `client_name`, `contact_info`, `billing_tier` | 1:M with `cases` | Legal clients. |
| `dashboard_configs` | `config_id` | `user_id`, `layout_json`, `updated_at` | M:1 with `users` | Stores the drag-and-drop layout. |
| `report_templates`| `tmpl_id` | `template_name`, `format_type`, `css_style` | - | Definitions for PDF/CSV exports. |
| `report_schedules` | `sched_id` | `tmpl_id`, `recipient_email`, `cron_expr` | M:1 with `report_templates` | Scheduled delivery rules. |
| `feature_flags` | `flag_id` | `flag_name`, `is_enabled`, `rollout_pct` | - | Controls A/B testing and feature release. |
| `audit_logs` | `log_id` | `user_id`, `action`, `timestamp`, `ip_address` | M:1 with `users` | Internal security audit trail. |

### 5.2 Relationship Mapping
The core of the system is the relationship between `cases` $\rightarrow$ `events` $\rightarrow$ `projections_case`. When a `POST /cases/{id}/events` occurs, a new row is added to `events`. An asynchronous worker then updates `projections_case` so that `GET /cases/{id}` remains lightning fast without recalculating the entire event history.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions
Due to the "Bus Factor of 1" and manual deployment nature, the environments are strictly partitioned.

- **Development (Dev):** 
    - **Host:** Local Docker containers.
    - **Purpose:** Individual developer testing.
    - **Database:** Local SQLite files.
- **Staging (Staging):** 
    - **Host:** Cloudflare Workers (Staging Namespace).
    - **Purpose:** Integration testing and stakeholder demos.
    - **Data:** Anonymized production snapshot.
- **Production (Prod):** 
    - **Host:** Cloudflare Workers (Production Namespace).
    - **Purpose:** Live legal operations.
    - **Deployment:** Manual triggers executed by Saoirse Nakamura.

### 6.2 Deployment Pipeline
1. **Commit:** Code is pushed to the `main` branch.
2. **CI:** GitHub Actions runs `cargo test` (Rust) and `npm test` (React).
3. **Approval:** Beau Gupta reviews the PR and signs off.
4. **Manual Deploy:** Saoirse Nakamura executes the Wrangler CLI scripts to push the Workers and updates the SQLite edge KV stores.

### 6.3 Infrastructure Constraints
The project is operating with **zero additional infrastructure budget**. All scaling must be achieved through code optimization (Rust) and the efficient use of the existing Cloudflare free/pro tier limits.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Backend:** Rust `#[cfg(test)]` modules for every function. Focus on event serialization and CRDT merge logic.
- **Frontend:** Jest for component logic and utility functions.
- **Requirement:** 80% code coverage on all "Critical" priority features.

### 7.2 Integration Testing
- **End-to-End Flow:** Testing the path from a React frontend request $\rightarrow$ Cloudflare Worker $\rightarrow$ Rust Backend $\rightarrow$ Event Store.
- **Tooling:** Playwright for automated browser flows.
- **Focus:** The "PDF Generation" pipeline must be tested against five different legal templates to ensure no formatting regressions.

### 7.3 End-to-End (E2E) and User Acceptance Testing (UAT)
- **Scenario-Based Testing:** Mimicking a "Day in the Life" of a legal paralegal.
- **Zero Downtime Validation:** Testing the "Blue/Green" transition from legacy to Wayfinder to ensure no data is lost and the system remains available.
- **External Audit Simulation:** A mock audit will be conducted by Freya Nakamura to ensure the event sourcing provides a complete trail.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Performance targets 10x legacy but budget is $0 for new hardware. | High | High | **Parallel-path:** Prototype alternative Rust optimization techniques simultaneously with current dev. |
| R2 | Budget cut by 30% in next fiscal quarter. | Medium | High | **Escalation:** Raise as a formal blocker in the next board meeting to secure "essential" status. |
| R3 | "Bus Factor of 1" for DevOps (Saoirse). | High | Critical | Document all manual steps in a "Runbook" and cross-train Beau Gupta on Wrangler CLI. |
| R4 | Design disagreement between Product and Engineering leads. | High | Medium | **Resolution:** Use the "Decider" framework; Beau Gupta has final sign-off on technical feasibility. |
| R5 | Legacy data corruption during import. | Medium | High | Implement a "Dry Run" import mode that validates data without writing to the DB. |

### 8.1 Probability/Impact Matrix
- **Critical:** Probability High $\times$ Impact High (e.g., R3) $\rightarrow$ Requires immediate mitigation.
- **Major:** Probability Medium $\times$ Impact High (e.g., R2) $\rightarrow$ Requires monitoring and board-level visibility.
- **Minor:** Probability High $\times$ Impact Medium (e.g., R4) $\rightarrow$ Handled via internal team meetings.

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Current - May 2025)**
    - Core CQRS implementation.
    - PDF/CSV engine development.
    - Baseline UI components.
- **Phase 2: Integration (May 2025 - July 2025)**
    - Data import tool finalization.
    - Beta testing with select power users.
    - Performance tuning for 10x capacity.
- **Phase 3: Transition (July 2025 - Sept 2025)**
    - First paying customer onboarding.
    - Parallel run with legacy system.
    - Final security audit.

### 9.2 Key Milestones
| Milestone | Target Date | Dependencies | Success Criteria |
| :--- | :--- | :--- | :--- |
| **M1: Stakeholder Demo** | 2025-05-15 | PDF Engine, Dashboard | Sign-off from Deepwell Data executives. |
| **M2: First Paying Customer**| 2025-07-15 | Import Tool, Billing Integration | Successful transaction and data migration. |
| **M3: Internal Alpha** | 2025-09-15 | Collaborative Editing, Security Audit | Full company transition to Wayfinder. |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-02  
**Attendees:** Beau Gupta, Saoirse Nakamura, Freya Nakamura, Orin Nakamura  
**Discussion:** 
- Discussion on the use of Event Sourcing. Orin expressed concern regarding the complexity of querying the event stream.
- Beau argued that for legal services, an audit trail is non-negotiable.
- Decision: Use CQRS. The "Query" side will be a flattened SQLite table for performance.
**Action Items:**
- [Beau] Define the event schema for "Case" entities. (Due: 2023-11-09)
- [Saoirse] Setup the Cloudflare Workers staging environment. (Due: 2023-11-05)

### Meeting 2: The "Performance Gap" Crisis
**Date:** 2023-11-16  
**Attendees:** Beau Gupta, Saoirse Nakamura  
**Discussion:**
- Initial benchmarks show the Rust backend is only 4x faster than legacy, not 10x.
- No budget available for higher-tier Cloudflare plans or better hardware.
- Decision: Implement a "Parallel-path" prototype. Beau will investigate `io_uring` for faster disk I/O while Saoirse optimizes the edge cache.
**Action Items:**
- [Beau] Build `io_uring` prototype. (Due: 2023-11-30)
- [Saoirse] Audit current cache hit ratios. (Due: 2023-11-20)

### Meeting 3: Design Conflict Resolution
**Date:** 2023-12-01  
**Attendees:** Beau Gupta, Product Lead (Internal)  
**Discussion:**
- Major disagreement regarding the Dashboard. Product wants highly complex visual analytics; Engineering argues this will destroy the 200ms load time target.
- Conflict reached a stalemate (Current Blocker).
- Resolution: Compromise reached. The dashboard will use "Lazy Loading" for complex widgets. The core dashboard will load instantly, and analytics will load asynchronously.
**Action Items:**
- [Beau] Update the technical spec to include async widget loading. (Due: 2023-12-05)
- [Product Lead] Provide wireframes for the "Simplified" core view. (Due: 2023-12-07)

---

## 11. BUDGET BREAKDOWN

Since the project is **unfunded** and bootstrapping, the budget represents "Allocated Capacity" (the cost of internal salaries) rather than liquid cash.

| Category | Annual Allocated Value | Notes |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $1,200,000 | Based on current salaries for 15 distributed members. |
| **Contractor (Orin)** | $150,000 | Fixed-term contract for legacy data migration support. |
| **Infrastructure** | $12,000 | Cloudflare Pro plan and basic storage (Current Spend). |
| **Tools** | $5,000 | JIRA, GitHub Enterprise, Slack. |
| **Contingency** | $0 | No liquid funds; contingency is "reduction of scope." |
| **TOTAL** | **$1,367,000** | **(Internal Capitalized Labor)** |

---

## 12. APPENDICES

### Appendix A: Structured Logging Proposal
**Current Debt:** The system currently lacks structured logging. Debugging requires reading `stdout` from the worker logs, which is unsustainable.

**Proposed Solution:**
Implementation of the `tracing` crate in Rust.
- **Log Levels:** `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`.
- **Format:** JSON logs sent to a centralized Cloudflare Logpush destination.
- **Key Fields:** `request_id`, `user_id`, `case_id`, `timestamp`, `duration_ms`.

### Appendix B: Event Sourcing State Transition Table
This table describes how the `projections_case` table is updated based on events in the `events` table.

| Event Type | Action on Projection | Field Updated |
| :--- | :--- | :--- |
| `CaseCreated` | INSERT | All header fields |
| `NoteAdded` | UPDATE | `total_notes` += 1, `last_updated` = now |
| `StatusChanged` | UPDATE | `current_status` = new_status |
| `ClientLinked` | UPDATE | `client_id` = new_client_id |
| `DocumentUploaded`| UPDATE | `file_count` += 1 |