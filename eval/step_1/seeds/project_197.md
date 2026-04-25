# PROJECT SPECIFICATION DOCUMENT: PROJECT DRIFT
**Version:** 1.0.4  
**Status:** Active/Development  
**Date:** October 24, 2025  
**Company:** Pivot North Engineering  
**Project Lead:** Xander Jensen  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project "Drift" represents a critical strategic pivot for Pivot North Engineering. The existing cybersecurity monitoring dashboard—the legacy "SentryView" system—has suffered from catastrophic user feedback. Client churn has increased by 22% over the last two quarters, with primary complaints centered on UI latency, a lack of actionable alerting, and an opaque onboarding process. In the high-stakes fintech industry, where real-time visibility into security posture is non-negotiable, the failure of the current product poses an existential threat to our market share.

Drift is not a mere iteration; it is a complete product rebuild. By stripping away the bloated legacy codebase and implementing a modern CQRS (Command Query Responsibility Segregation) architecture, Drift aims to transform a liability into a competitive advantage. The objective is to provide fintech clients with a high-performance, reliable, and intuitive monitoring interface that integrates seamlessly into their security operations center (SOC) workflows.

### 1.2 ROI Projection
The financial justification for the $400,000 investment is based on three primary levers:
1. **Churn Reduction:** By addressing the "catastrophic" feedback, we project a reduction in annual churn from 22% to under 5%. Based on an average contract value (ACV) of $50,000 per client across 100 clients, this saves $8.5M in annual recurring revenue (ARR).
2. **New Market Acquisition:** The introduction of a customer-facing API and a sandbox environment allows us to target "API-first" fintech startups, expanding our Total Addressable Market (TAM) by approximately 15%.
3. **Operational Efficiency:** Replacing the manual support burden (currently managed by Omar Moreau) with automated billing and self-service API tools will reduce support tickets per customer by 40%.

The projected Break-Even Point (BEP) for Project Drift is estimated at 4.5 months post-launch, assuming the successful onboarding of the first paying customer by August 15, 2026.

### 1.3 Scope Statement
Drift will provide a centralized hub for cybersecurity event monitoring, featuring a robust notification engine, an extensible API, and high-performance data visualization. The product will be hosted exclusively on-premise to satisfy strict fintech data residency requirements.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Drift utilizes a Java/Spring Boot backend paired with an Oracle Database. To ensure the auditability required for fintech security, the system implements **CQRS with Event Sourcing**. 

In this architecture, the "Write" side (Command) handles state changes and persists them as a series of immutable events in an Event Store. The "Read" side (Query) consumes these events to build optimized projections (read models) in the Oracle DB, allowing for the p95 response times required by the success criteria.

### 2.2 Architecture Diagram (ASCII Description)
```text
[ Client Browser ] <---> [ Load Balancer ] <---> [ Spring Boot Application Nodes ]
                                                          |
       ___________________________________________________|___________________________________________________
      |                                                   |                                                   |
[ COMMAND SIDE (Write) ]                         [ EVENT BUS / KAFKA ]                        [ QUERY SIDE (Read) ]
- Request Validation                             - Event Store (Oracle)                       - Materialized Views
- Business Logic                                 - Event Publishing                            - Read-only Repositories
- Event Generation                               - Event Subscriptions                         - P95 Optimization
      |                                                   |                                                   |
      └---------------------------------------------------┴---------------------------------------------------┘
                                                          |
                                              [ ORACLE DATABASE (On-Premise) ]
                                              - Tables: Events, Projections, Users, Billing
```

### 2.3 Tech Stack Detail
- **Backend:** Java 21, Spring Boot 3.2.x
- **Database:** Oracle DB 21c (Enterprise Edition), hosted on-premise.
- **Messaging:** Internal Spring Events / Kafka (On-prem cluster).
- **Frontend:** React 18 with TypeScript, Tailwind CSS.
- **Deployment:** LaunchDarkly (Feature Flags), Canary Deployment via Nginx/HAProxy.
- **Infrastructure:** Bare-metal servers in the Pivot North Data Center. No cloud providers (AWS/Azure/GCP) are permitted due to strict internal security constraints.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: Critical | Status: Blocked)
**Description:** A multi-channel alerting engine designed to notify security analysts of critical threats in real-time. This is a launch-blocker; the product cannot go to beta without guaranteed delivery of alerts.

**Functional Requirements:**
- **Multi-Channel Delivery:** The system must support four distinct delivery vectors:
    - **Email:** Integration with internal SMTP servers using SendGrid-compatible templates.
    - **SMS:** Integration with Twilio (On-prem gateway).
    - **In-App:** Real-time WebSocket notifications via STOMP.
    - **Push:** Web-push notifications via Service Workers.
- **Alert Routing Logic:** Users must be able to define "Alert Profiles." For example, "Critical" alerts go to SMS and Push, while "Informational" alerts only trigger In-App notifications.
- **Notification Deduplication:** The system must suppress duplicate alerts for the same event within a 5-minute window to prevent "alert fatigue."
- **Audit Trail:** Every single notification attempt must be logged in the `notification_logs` table, including timestamp, channel, and delivery status (Sent/Failed).

**Technical Constraints:**
- Must support a throughput of 1,000 notifications per second.
- Must integrate with the Event Sourcing layer to trigger alerts based on specific `SecurityEvent` types.

### 3.2 Offline-First Mode with Background Sync (Priority: Low | Status: Blocked)
**Description:** A "nice to have" feature allowing analysts to maintain a local cache of the dashboard for use during intermittent network outages common in secure data centers.

**Functional Requirements:**
- **Local Storage:** Utilize IndexedDB to store the last 24 hours of monitoring data.
- **Optimistic UI:** When a user acknowledges an alert while offline, the UI should reflect the change immediately.
- **Background Synchronization:** Use Service Workers to queue "Commands" (in CQRS terms). Once connectivity is restored, the system must replay these commands to the server in the original sequence to maintain data integrity.
- **Conflict Resolution:** Implement a "Last Write Wins" strategy, though the event store will maintain the original sequence for auditing.

**Technical Constraints:**
- Maximum local cache size: 50MB.
- Sync must occur in the background without blocking the main UI thread.

### 3.3 Data Import/Export with Format Auto-Detection (Priority: High | Status: In Progress)
**Description:** A tool allowing customers to migrate historical security logs from legacy systems or export data for external audits.

**Functional Requirements:**
- **Auto-Detection Engine:** The system must analyze the first 100 lines of an uploaded file to detect the format (CSV, JSON, XML, or Syslog).
- **Mapping Interface:** A UI tool allowing users to map their source columns (e.g., "src_ip") to Drift's internal schema ("source_ip_address").
- **Bulk Import:** Use Spring Batch to process files larger than 1GB without crashing the JVM.
- **Export Engine:** Ability to export any filtered view of the dashboard into a signed PDF or CSV.

**Technical Constraints:**
- Validation must occur pre-import; any row failing schema validation must be logged in a "DLQ" (Dead Letter Queue) file for the user to download and fix.
- Import process must be asynchronous with a progress bar in the UI.

### 3.4 Automated Billing and Subscription Management (Priority: Medium | Status: Complete)
**Description:** An internal module to handle client licensing and automated invoicing.

**Functional Requirements:**
- **Tiered Pricing:** Support for Basic, Professional, and Enterprise tiers.
- **Auto-Invoicing:** Integration with the internal accounting system to generate monthly PDF invoices.
- **Subscription Lifecycle:** Automated handling of trial expiration, upgrades, downgrades, and churn (account suspension).
- **Usage Tracking:** Track the number of "monitored endpoints" per client to trigger overage charges.

**Technical Constraints:**
- The billing module is decoupled from the core monitoring engine to ensure that a billing failure does not stop security monitoring.

### 3.5 Customer-Facing API with Versioning and Sandbox (Priority: Medium | Status: Complete)
**Description:** A RESTful API allowing clients to integrate Drift data into their own SIEM (Security Information and Event Management) tools.

**Functional Requirements:**
- **Versioning:** Use URI versioning (e.g., `/api/v1/events`). All versions must be supported for 12 months before deprecation.
- **Sandbox Environment:** A mirrored, non-production environment where clients can test their API integrations without affecting real data.
- **API Key Management:** Self-service portal for generating, rotating, and revoking API keys.
- **Rate Limiting:** Implement bucket-based rate limiting (e.g., 100 requests/minute for Basic, 1000 for Enterprise).

**Technical Constraints:**
- All API responses must be in JSON format.
- Authentication via Bearer Tokens (JWT).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Base URL: `https://drift.pivotnorth.internal/api/v1`

### 4.1 Get Security Events
- **Path:** `GET /events`
- **Description:** Retrieves a list of security events.
- **Query Params:** `severity` (Optional), `startTime` (ISO8601), `endTime` (ISO8601).
- **Request Example:** `GET /events?severity=CRITICAL&startTime=2026-01-01T00:00:00Z`
- **Response (200 OK):**
```json
[
  {
    "eventId": "evt-99283",
    "timestamp": "2026-01-01T10:15:00Z",
    "severity": "CRITICAL",
    "message": "Unauthorized SSH attempt from 192.168.1.50",
    "source": "Firewall-01"
  }
]
```

### 4.2 Create Alert Rule
- **Path:** `POST /alerts/rules`
- **Description:** Define a new trigger for the notification system.
- **Request Body:**
```json
{
  "ruleName": "SSH Brute Force",
  "condition": "failed_logins > 5",
  "window": "60s",
  "channels": ["SMS", "EMAIL"]
}
```
- **Response (201 Created):** `{"ruleId": "rule-441", "status": "active"}`

### 4.3 Acknowledge Event
- **Path:** `PATCH /events/{eventId}/status`
- **Description:** Mark an event as acknowledged or resolved.
- **Request Body:** `{"status": "ACKNOWLEDGED", "user": "zsantos"}`
- **Response (200 OK):** `{"eventId": "evt-99283", "updatedAt": "2026-01-01T10:20:00Z"}`

### 4.4 Export Data
- **Path:** `POST /export`
- **Description:** Request a data dump for a specific time range.
- **Request Body:** `{"format": "CSV", "range": "last_30_days"}`
- **Response (202 Accepted):** `{"jobId": "job-112", "status": "processing", "downloadUrl": "/api/v1/export/download/job-112"}`

### 4.5 Get Subscription Status
- **Path:** `GET /billing/subscription`
- **Description:** Returns the current plan and usage.
- **Response (200 OK):**
```json
{
  "plan": "Professional",
  "endpointsUsed": 450,
  "endpointLimit": 500,
  "nextBillingDate": "2026-02-01"
}
```

### 4.6 Update Notification Settings
- **Path:** `PUT /user/settings/notifications`
- **Description:** Update user contact info for alerts.
- **Request Body:** `{"email": "admin@client.com", "phone": "+1555010999"}`
- **Response (200 OK):** `{"status": "updated"}`

### 4.7 Get Sandbox Health
- **Path:** `GET /sandbox/health`
- **Description:** Checks the status of the sandbox environment.
- **Response (200 OK):** `{"status": "healthy", "version": "1.0.4-beta"}`

### 4.8 Delete API Key
- **Path:** `DELETE /api/keys/{keyId}`
- **Description:** Revokes a specific API key.
- **Response (204 No Content):** (Empty Body)

---

## 5. DATABASE SCHEMA

The Oracle DB is split into two schemas: `DRIFT_COMMAND` (for event sourcing) and `DRIFT_QUERY` (for projections).

### 5.1 Table Definitions

| Table Name | Schema | Key Fields | Purpose | Relationship |
| :--- | :--- | :--- | :--- | :--- |
| `event_store` | Command | `event_id` (PK), `aggregate_id`, `version`, `payload` (JSON), `created_at` | The source of truth for all state changes. | 1:M with `event_projections` |
| `users` | Query | `user_id` (PK), `username`, `password_hash`, `role_id` (FK) | User account and auth data. | M:1 with `roles` |
| `roles` | Query | `role_id` (PK), `role_name`, `permissions` | Role-based access control. | 1:M with `users` |
| `clients` | Query | `client_id` (PK), `company_name`, `billing_tier_id` (FK) | Top-level tenant information. | 1:M with `users` |
| `billing_tiers`| Query | `tier_id` (PK), `tier_name`, `monthly_cost`, `endpoint_limit` | Pricing plan definitions. | 1:M with `clients` |
| `security_events`| Query | `event_id` (PK), `client_id` (FK), `severity`, `message`, `timestamp` | Optimized view of events for the dashboard. | M:1 with `clients` |
| `notification_rules`| Query | `rule_id` (PK), `client_id` (FK), `condition`, `channel_mask` | Alert triggers and delivery paths. | M:1 with `clients` |
| `notification_logs`| Query | `log_id` (PK), `rule_id` (FK), `channel`, `status`, `sent_at` | Audit trail of all notifications. | M:1 with `notification_rules` |
| `api_keys` | Query | `key_id` (PK), `client_id` (FK), `key_hash`, `created_at`, `expires_at` | API authentication tokens. | M:1 with `clients` |
| `import_jobs` | Query | `job_id` (PK), `client_id` (FK), `file_name`, `status`, `rows_processed` | Tracking for large data imports. | M:1 with `clients` |

### 5.2 Key Relationships
- **Tenant Isolation:** Every table in the `DRIFT_QUERY` schema (except `billing_tiers` and `roles`) contains a `client_id` to ensure strict data partitioning between fintech customers.
- **Event Chain:** The `event_store` table uses the `aggregate_id` and `version` columns to ensure a strict chronological sequence of events, preventing race conditions during state reconstruction.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

#### Development (DEV)
- **Purpose:** Individual developer testing and feature branching.
- **Infrastructure:** Local Docker containers (Oracle XE, Spring Boot) and a shared DEV server in the data center.
- **Data:** Anonymized synthetic data.

#### Staging (STG)
- **Purpose:** QA testing, UAT, and integration testing.
- **Infrastructure:** A mirrored replica of production hardware.
- **Deployment:** Every merge to `main` triggers an automatic deploy to Staging. This environment is where the "Dedicated QA" person performs regression testing.

#### Production (PROD)
- **Purpose:** Live customer traffic.
- **Infrastructure:** High-availability cluster of bare-metal servers.
- **Deployment Strategy:** 
    - **Canary Releases:** Traffic is shifted in increments (5% $\rightarrow$ 25% $\rightarrow$ 100%) using the Nginx load balancer.
    - **Feature Flags:** LaunchDarkly is used to toggle features (e.g., enabling the Notification System) without requiring a full redeploy.

### 6.2 The CI/CD Pipeline Problem
The current CI pipeline is a significant bottleneck, taking **45 minutes** to complete. This is due to a sequential execution of 4,000+ unit tests and a slow Oracle DB container spin-up.
- **Proposed Fix:** Parallelize the test suite into 4 shards and implement a "warm" database container for integration tests.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic in Spring Services and Domain models.
- **Tooling:** JUnit 5, Mockito.
- **Requirement:** 80% code coverage for all new "Command" handlers.

### 7.2 Integration Testing
- **Focus:** Database interactions and API contract validation.
- **Tooling:** Testcontainers (Oracle), RestAssured.
- **Strategy:** Tests must run against a real Oracle instance to validate complex SQL projections and event sourcing logic.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user journeys (e.g., "User creates alert rule $\rightarrow$ Event occurs $\rightarrow$ User receives SMS").
- **Tooling:** Cypress.
- **Frequency:** Executed on Staging prior to any Canary release to Production.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget may be cut by 30% in next fiscal quarter. | Medium | High | Accept the risk; monitor weekly budget burn. Prioritize critical features (Notifications) over low-priority ones (Offline mode). |
| R-02 | Competitor is building similar product; 2 months ahead. | High | High | Assign Saoirse Jensen as dedicated owner to track competitor feature releases and accelerate the API roadmap. |
| R-03 | CI Pipeline inefficiency (45 min) delays delivery. | High | Medium | Implement test parallelization in Q1 2026. |
| R-04 | On-premise hardware failure. | Low | High | Redundant server clusters and nightly Oracle backups to off-site tape storage. |

---

## 9. TIMELINE

### 9.1 Phases and Dependencies

**Phase 1: Foundation & Core API (Current - April 2026)**
- *Focus:* Completing the data import engine and finalizing the API/Billing modules.
- *Dependency:* None.
- **Milestone 1: External Beta (2026-04-15).** 10 pilot users onboarded.

**Phase 2: Notification Engine & Stabilization (April 2026 - June 2026)**
- *Focus:* Breaking the block on the Notification System (Critical).
- *Dependency:* Stable Event Store implementation.
- **Milestone 2: Architecture Review (2026-06-15).** Full audit of CQRS implementation.

**Phase 3: Commercial Launch (June 2026 - August 2026)**
- *Focus:* Polishing the UI based on beta feedback and finalizing the billing pipeline.
- *Dependency:* Success of Milestone 1 and 2.
- **Milestone 3: First Paying Customer (2026-08-15).**

---

## 10. MEETING NOTES

### Meeting 1: 2025-11-02 (Weekly Sync)
- *Attendees:* Xander, Zev, Saoirse, Omar.
- Notification system still blocked.
- Zev says UI looks "cleaner."
- Omar mentioned billing is finally working.
- Xander: "Keep it lean."

### Meeting 2: 2025-11-16 (Architecture Deep Dive)
- *Attendees:* Xander, Saoirse, Zev.
- Oracle DB projections taking too long.
- Saoirse suggests materialized views.
- Xander: "Just do it."
- Zev wants to use a new CSS library; Xander said no.

### Meeting 3: 2025-12-01 (Risk Assessment)
- *Attendees:* Xander, Omar.
- Budget cut rumor.
- Omar: "We might lose the QA contractor if this happens."
- Xander: "We'll monitor weekly."
- Discussed the 45-minute CI build. Xander called it "embarrassing."

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Salaries for 6 team members (inc. QA) for the project duration. |
| **Infrastructure**| $45,000 | On-premise server hardware upgrades and Oracle licensing. |
| **Tools** | $25,000 | LaunchDarkly subscription, Twilio/SendGrid credits, Jira/Slack. |
| **Contingency** | $50,000 | Reserve for emergency hardware or outsourced security auditing. |

---

## 12. APPENDICES

### Appendix A: Event Sourcing Schema Example
To reconstruct the state of a `NotificationRule`, the system replays events from the `event_store`:
1. `RuleCreatedEvent` $\rightarrow$ Set ID, Name, and Initial Conditions.
2. `RuleModifiedEvent` $\rightarrow$ Update `channel_mask` from `EMAIL` to `EMAIL, SMS`.
3. `RuleDisabledEvent` $\rightarrow$ Set `status` to `INACTIVE`.

The final state is then projected into the `notification_rules` table for fast querying.

### Appendix B: API Rate Limit Logic
Drift uses a "Token Bucket" algorithm implemented via Spring Interceptors.
- **Bucket Size:** 1,000 tokens (Enterprise).
- **Refill Rate:** 10 tokens per second.
- **Header Response:** 
    - `X-RateLimit-Limit`: Total tokens.
    - `X-RateLimit-Remaining`: Tokens left in current window.
    - `X-RateLimit-Reset`: Seconds until bucket is full.