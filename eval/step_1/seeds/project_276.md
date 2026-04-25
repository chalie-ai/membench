# PROJECT SPECIFICATION DOCUMENT: PROJECT JUNIPER
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Classification:** Internal / Proprietary  
**Company:** Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
Project Juniper is a strategic initiative by Coral Reef Solutions to transition a high-impact internal productivity tool—originally conceived as a hackathon prototype—into a robust, enterprise-grade data pipeline and analytics platform. Currently serving 500 daily active users (DAU) within the food and beverage industry, Juniper aims to centralize fragmented data streams, automate repetitive operational workflows, and provide real-time analytics to optimize supply chain and distribution efficiency.

The platform is designed to solve the "data silo" problem prevalent in food and beverage logistics, where inventory, sales, and delivery data reside in disparate legacy systems. By providing a unified interface for data orchestration and a visual rule-builder for automation, Juniper empowers non-technical operational managers to create complex logic without developer intervention.

### 1.2 Business Justification
The food and beverage sector operates on razor-thin margins. Current manual data entry and fragmented reporting result in a "latency gap" of 48 to 72 hours between a warehouse event and a management decision. Juniper reduces this gap to near real-time. 

The core business driver is the reduction of operational overhead. By implementing the Workflow Automation Engine, Coral Reef Solutions expects to eliminate approximately 1,200 man-hours per month previously spent on manual data reconciliation. Furthermore, the move toward a standardized data pipeline allows the company to scale its client base without a linear increase in administrative headcount.

### 1.3 ROI Projection
The project is allocated a budget of $800,000 for a six-month build cycle. The projected Return on Investment (ROI) is calculated based on two primary levers:

1.  **Direct Cost Reduction:** The primary success metric is a 35% reduction in cost per transaction compared to the legacy system. Based on current transaction volumes, this is projected to save the company $210,000 annually in compute and labor costs.
2.  **Revenue Acceleration:** By enabling FedRAMP authorization, Juniper opens a new market segment: government contracts for food service and logistics. The Total Addressable Market (TAM) for government food-service analytics is estimated at $12M. Capturing even 5% of this market in the first year would yield $600,000 in new ARR.

**Projected 3-Year NPV:** $1.4M  
**Payback Period:** 14 months post-MVP launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Pattern: Hexagonal Architecture
Project Juniper employs a **Hexagonal Architecture (Ports and Adapters)**. This ensures that the core business logic (the "Domain") remains isolated from external dependencies such as the database, third-party APIs, and the UI layer. This is critical for the project given the risk of changing regulatory requirements; the domain logic can remain stable while adapters are swapped to comply with new laws.

-   **Domain Layer:** Contains the business entities (e.g., `Workflow`, `Rule`, `User`, `Metric`) and use-case interactors.
-   **Ports:** Interfaces that define how the domain communicates with the outside world.
-   **Adapters:** Concrete implementations of ports (e.g., `PrismaUserRepository` for PostgreSQL, `VercelDeploymentAdapter` for infrastructure).

### 2.2 Technology Stack
-   **Frontend:** Next.js 14 (App Router) with TypeScript.
-   **Backend:** TypeScript/Node.js running on Vercel Serverless Functions.
-   **ORM:** Prisma (for type-safe database access).
-   **Database:** PostgreSQL 15 (managed instance).
-   **Authentication:** Custom implementation with support for hardware security keys (WebAuthn).
-   **Deployment:** Vercel (Manual deployment pipeline).

### 2.3 ASCII Architecture Diagram
```text
[ EXTERNAL CLIENTS ] <--> [ VERCEL EDGE / NEXT.JS FRONTEND ]
                                      |
                                      v
                          [ ADAPTER LAYER (HTTP/REST) ]
                                      |
      ________________________________|_________________________________
     |                                                                  |
     |                         [ DOMAIN LAYER ]                         |
     |  (Business Logic) -> (Workflow Engine) -> (Analytics Processor)   |
     |_________________________________________________________________|
                                      |
      ________________________________|_________________________________
     |                                                                  |
 [ PORT: Persistence ]        [ PORT: External API ]        [ PORT: Auth ]
     |                               |                                  |
 [ ADAPTER: Prisma ]          [ ADAPTER: Webhooks ]         [ ADAPTER: WebAuthn ]
     |                               |                                  |
 [ PostgreSQL DB ]            [ 3rd Party Tools ]           [ Hardware Keys ]
```

### 2.4 Infrastructure Constraints
The system currently suffers from a "Bus Factor of 1." All deployment activities are handled by a single DevOps specialist. This creates a bottleneck and a high-risk failure point. Furthermore, the CI pipeline is currently unoptimized, resulting in a 45-minute build time, which slows the development velocity of the solo developer.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:**
The Workflow Automation Engine is the heart of Juniper. It allows users to define "If-This-Then-That" (IFTTT) logic to automate data movements and notifications. The visual rule builder is a drag-and-drop canvas where users can connect triggers (e.g., "Inventory level drops below 10%") to actions (e.g., "Send alert to procurement manager").

**Technical Details:**
The engine utilizes a directed acyclic graph (DAG) to represent workflow steps. Each "node" in the graph represents a logic gate or an action. The rules are stored in PostgreSQL as JSONB blobs to allow for flexible schema evolution without requiring migrations for every new rule type.

**Functionality:**
-   **Trigger System:** Supports event-based triggers (webhook arrival) and polling triggers (checking a database value every 5 minutes).
-   **Conditional Logic:** Supports boolean operators (AND, OR, NOT) and comparison operators (>, <, ==, contains).
-   **Action Suite:** Integration with email, Slack, and internal dashboard alerts.
-   **Validation:** The visual builder prevents circular dependencies, ensuring that no workflow enters an infinite loop.

**User Workflow:**
A user drags a "Webhook Trigger" node onto the canvas $\rightarrow$ connects it to a "Filter" node $\rightarrow$ connects that to a "Postgres Update" action node. The engine then compiles this visual map into a JSON execution plan.

---

### 3.2 Webhook Integration Framework
**Priority:** Medium | **Status:** Blocked (Pending budget approval for critical tool purchase)

**Description:**
This framework allows Juniper to ingest data from third-party food-beverage logistics tools (e.g., SAP, Oracle NetSuite, or smaller Shopify-based storefronts). It acts as a flexible listener that can normalize incoming heterogeneous data into the Juniper standard format.

**Technical Details:**
The framework requires a dedicated "Ingestion Gateway" that can handle high-concurrency bursts of HTTP POST requests. It must support signature verification (HMAC) to ensure the authenticity of the payload.

**Detailed Requirements:**
-   **Dynamic Endpoints:** Each user is assigned a unique webhook URL (e.g., `/api/webhooks/v1/[unique_id]`).
-   **Payload Normalization:** A mapping layer that converts `external_field_name` to `internal_field_name` based on a user-defined mapping schema.
-   **Retry Logic:** Implement an exponential backoff strategy for failed downstream processing.
-   **Dead Letter Queue (DLQ):** Any payload that fails normalization after 3 attempts must be moved to a DLQ for manual review by Haruki Moreau.

**Blocker Detail:**
The team requires a specialized middleware tool for payload validation and schema registry. Budget approval for this $12,000/year subscription is currently pending approval from the CFO's office.

---

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** Complete

**Description:**
To meet FedRAMP authorization requirements for government clients, Juniper must implement a high-assurance authentication mechanism. While standard TOTP (Time-based One-Time Passwords) are supported, the platform specifically includes support for FIDO2/WebAuthn hardware keys (e.g., YubiKey).

**Technical Details:**
The implementation uses the `WebAuthn` API. During registration, the server generates a challenge that the user signs using their hardware key. The public key is then stored in the `UserSecurityKeys` table.

**Detailed Requirements:**
-   **Enforcement:** 2FA can be mandated at the organizational level by the administrator.
-   **Recovery:** Implementation of one-time recovery codes (10 codes, 12 characters each) to prevent lockout if a hardware key is lost.
-   **Session Management:** Hardware key authentication extends the session duration but requires re-authentication for "high-sensitivity" actions (e.g., changing billing details).
-   **Audit Logging:** Every successful and failed 2FA attempt is logged with IP address and device fingerprint.

---

### 3.4 Offline-First Mode with Background Sync
**Priority:** High | **Status:** Not Started

**Description:**
Warehouse environments often have "dead zones" with poor Wi-Fi connectivity. Users must be able to input data and trigger workflows while offline, with the system automatically synchronizing changes once a connection is re-established.

**Technical Details:**
This will be implemented using a combination of IndexedDB (for client-side storage) and a synchronization protocol based on Version Vectors to resolve conflicts.

**Detailed Requirements:**
-   **Local-First Storage:** Use `Dexie.js` to wrap IndexedDB, mirroring the critical tables of the PostgreSQL schema.
-   **Change Tracking:** Every mutation is recorded as a "Change Event" in a local queue.
-   **Conflict Resolution:** Use a "Last-Write-Wins" (LWW) strategy by default, with an option for "Manual Merge" for complex workflow rule changes.
-   **Background Sync API:** Leverage the browser's `ServiceWorker` and `Background Sync API` to push data even if the browser tab is closed.
-   **Visual Cues:** The UI must clearly indicate the "Sync Status" (e.g., "3 changes pending upload").

---

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** Low (Nice to Have) | **Status:** In Progress

**Description:**
As Juniper moves toward an external beta, it must protect its resources from abuse. This feature implements a quota system to limit the number of requests per user/API key and provides a dashboard for users to see their usage trends.

**Technical Details:**
The rate limiter will be implemented using a "Token Bucket" algorithm stored in a Redis cache for low-latency checks.

**Detailed Requirements:**
-   **Tiered Quotas:**
    -   *Free/Beta:* 1,000 requests/day.
    -   *Premium:* 100,000 requests/day.
-   **Header Responses:** Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` in all API responses.
-   **Analytics Pipeline:** Each request is logged to a separate `ApiUsage` table. A background job aggregates these logs hourly into a `DailyUsageSummary` table.
-   **Alerting:** Automatically notify the user when they hit 80% of their daily quota.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and return JSON. Base URL: `https://api.juniper.coralreef.io/v1`

### 4.1 Authentication Endpoints
**POST `/auth/login`**
-   **Request:** `{ "email": "user@example.com", "password": "hashed_password" }`
-   **Response:** `200 OK { "token": "jwt_token", "requires_2fa": true }`

**POST `/auth/2fa/verify`**
-   **Request:** `{ "token": "jwt_token", "assertion": "webauthn_assertion_payload" }`
-   **Response:** `200 OK { "session_token": "final_session_token" }`

### 4.2 Workflow Engine Endpoints
**GET `/workflows`**
-   **Description:** Retrieve all workflows for the authenticated user.
-   **Response:** `200 OK [ { "id": "wf_123", "name": "Inventory Alert", "status": "active" } ]`

**POST `/workflows/execute`**
-   **Description:** Manually trigger a workflow.
-   **Request:** `{ "workflow_id": "wf_123", "payload": { "item_id": "SKU-99" } }`
-   **Response:** `202 Accepted { "execution_id": "exec_456" }`

**PUT `/workflows/:id/rules`**
-   **Description:** Update the logic gates of a specific workflow.
-   **Request:** `{ "nodes": [...], "edges": [...] }`
-   **Response:** `200 OK { "status": "updated", "version": 4 }`

### 4.3 Analytics & Data Endpoints
**GET `/analytics/transactions/cost`**
-   **Description:** Returns the cost per transaction over a specified time range.
-   **Query Params:** `?start=2023-01-01&end=2023-06-01`
-   **Response:** `200 OK { "average_cost": 0.45, "currency": "USD", "period": "H1" }`

**GET `/analytics/usage`**
-   **Description:** Returns API usage statistics for the account.
-   **Response:** `200 OK { "total_requests": 4500, "limit": 10000, "remaining": 5500 }`

### 4.4 System & Integration Endpoints
**POST `/webhooks/register`**
-   **Description:** Create a new webhook listener for an external tool.
-   **Request:** `{ "source": "Shopify", "target_workflow": "wf_123" }`
-   **Response:** `201 Created { "webhook_url": "https://api.juniper.io/webhooks/v1/abc-123" }`

**GET `/system/health`**
-   **Description:** Health check for the platform.
-   **Response:** `200 OK { "status": "healthy", "database": "connected", "redis": "connected" }`

---

## 5. DATABASE SCHEMA

The database is implemented using PostgreSQL 15 via Prisma ORM.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `Users` | `id (UUID)`, `email`, `password_hash` | 1:N `UserSecurityKeys`, 1:N `Workflows` | Core user identity and account data. |
| `UserSecurityKeys` | `id`, `userId (FK)`, `publicKey`, `credentialId` | N:1 `Users` | Stores WebAuthn public keys for 2FA. |
| `Workflows` | `id`, `userId (FK)`, `name`, `config (JSONB)` | N:1 `Users`, 1:N `WorkflowLogs` | Stores the visual rule builder configurations. |
| `WorkflowLogs` | `id`, `workflowId (FK)`, `status`, `executionTime` | N:1 `Workflows` | Audit trail of every workflow execution. |
| `ExternalTools` | `id`, `toolName`, `apiCategory` | 1:N `WebhookConfigs` | Registry of supported 3rd party tools. |
| `WebhookConfigs` | `id`, `toolId (FK)`, `secretKey`, `targetWorkflowId` | N:1 `ExternalTools`, N:1 `Workflows` | Mapping of external webhooks to internal logic. |
| `Transactions` | `id`, `amount`, `timestamp`, `userId (FK)` | N:1 `Users` | Operational data for cost-per-transaction metrics. |
| `ApiUsage` | `id`, `userId (FK)`, `endpoint`, `timestamp` | N:1 `Users` | Raw logs for rate limiting analytics. |
| `DailyUsageSummary`| `id`, `userId (FK)`, `date`, `totalRequests` | N:1 `Users` | Aggregated usage for performance. |
| `AuditLogs` | `id`, `userId (FK)`, `action`, `ipAddress` | N:1 `Users` | FedRAMP required security audit trail. |

### 5.2 Key Relationships & Constraints
-   **Cascade Deletes:** Deleting a `User` cascades to `UserSecurityKeys` and `Workflows`.
-   **JSONB Indexing:** GIN indexes are applied to `Workflows.config` to allow efficient querying of specific rule patterns within the JSON blobs.
-   **Foreign Key Integrity:** Strict constraints ensure no `WebhookConfig` can point to a non-existent `Workflow`.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Juniper utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (Dev)
-   **Purpose:** Rapid prototyping and feature development.
-   **Host:** Localhost / Vercel Preview Deployments.
-   **Database:** Local PostgreSQL Docker container.
-   **Deployment:** Automatic on every git push to `feature/*` branches.

#### 6.1.2 Staging (Staging)
-   **Purpose:** Pre-production testing and UAT (User Acceptance Testing).
-   **Host:** `staging.juniper.coralreef.io` (Vercel).
-   **Database:** Staging PostgreSQL instance (anonymized production dump).
-   **Deployment:** Manual trigger by the developer upon merging to `develop` branch.

#### 6.1.3 Production (Prod)
-   **Purpose:** Live environment for 500+ users.
-   **Host:** `app.juniper.coralreef.io` (Vercel).
-   **Database:** Production PostgreSQL (High-availability cluster).
-   **Deployment:** Manual deployments performed by the sole DevOps person. This process involves a manual check of the staging environment, a production database backup, and a `git tag` trigger in Vercel.

### 6.2 Infrastructure Bottlenecks
-   **CI Pipeline:** The current pipeline takes 45 minutes. This is due to the monolithic nature of the TypeScript compilation and a lack of test parallelization.
-   **Bus Factor:** The deployment process is not documented outside the head of one individual. If that person is unavailable, production updates are impossible.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
-   **Framework:** Jest.
-   **Scope:** All Domain layer logic, particularly the Workflow Rule Engine and the Rate Limiter.
-   **Requirement:** Minimum 80% code coverage for the domain layer.
-   **Mocking:** Use of `jest.mock` to isolate business logic from Prisma database calls.

### 7.2 Integration Testing
-   **Framework:** Vitest.
-   **Scope:** Testing the "Adapters." Specifically, verifying that the Prisma repositories correctly interact with the PostgreSQL schema and that the WebAuthn flow completes across the API boundary.
-   **Approach:** Use of a dedicated "Test Database" that is wiped and seeded before every test suite run.

### 7.3 End-to-End (E2E) Testing
-   **Framework:** Playwright.
-   **Scope:** Critical user journeys:
    1.  User logs in with 2FA $\rightarrow$ creates a workflow $\rightarrow$ triggers it $\rightarrow$ verifies the result.
    2.  User attempts to exceed the API rate limit $\rightarrow$ receives 429 error.
    3.  User enters offline mode $\rightarrow$ makes a change $\rightarrow$ goes online $\rightarrow$ verifies sync.
-   **Environment:** Executed against the Staging environment.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Regulatory requirements for FedRAMP change. | High | High | **Parallel-Pathing:** Prototype alternative security architectures simultaneously to ensure rapid pivoting. |
| **R-02** | Competitor is 2 months ahead in feature set. | Medium | High | **External Audit:** Engage an independent consultant to identify "gap features" and prioritize high-value differentiators. |
| **R-03** | DevOps person leaves the company. | Medium | Critical | **Documentation Sprint:** Immediately document the deployment process and automate the pipeline via GitHub Actions. |
| **R-04** | CI Pipeline delays slow development. | High | Medium | **Optimization:** Implement Turborepo and parallelize Jest tests to reduce build time from 45m to <10m. |

### 8.1 Impact Matrix
-   **Critical:** Potential project failure or total system outage.
-   **High:** Significant delay in milestones or failure to meet success criteria.
-   **Medium:** Noticeable impact on velocity but manageable.
-   **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

The project is structured across three primary phases over a 6-month window.

### 9.1 Phase 1: Foundation and Core Logic (Now - April 15, 2025)
-   **Focus:** Finalizing the Workflow Engine and preparing for external eyes.
-   **Dependencies:** Completion of the 2FA module.
-   **Milestone 1 (2025-04-15):** **External beta with 10 pilot users.**
    -   Success criteria: Users can create at least one functional workflow and experience zero critical crashes.

### 9.2 Phase 2: Infrastructure and Scaling (April 16 - June 15, 2025)
-   **Focus:** Implementing the Offline-First mode and resolving the Webhook blocker.
-   **Dependencies:** Budget approval for the middleware tool.
-   **Milestone 2 (2025-06-15):** **Internal alpha release.**
    -   Success criteria: 500 internal users migrated from the hackathon prototype to the new architecture.

### 9.3 Phase 3: Hardening and Compliance (June 16 - August 15, 2025)
-   **Focus:** API Rate limiting, usage analytics, and FedRAMP audit preparation.
-   **Dependencies:** Completion of the audit log system.
-   **Milestone 3 (2025-08-15):** **MVP feature-complete.**
    -   Success criteria: Pass external audit on first attempt; 35% reduction in transaction costs.

---

## 10. MEETING NOTES

### Meeting 1: Technical Architecture Alignment
**Date:** 2023-11-01  
**Attendees:** Ines Kim, Haruki Moreau, Thiago Costa, Ren Stein  
**Discussion:**
-   Ines emphasized the need for the Hexagonal Architecture to mitigate the risk of changing government regulations.
-   Haruki raised concerns about the 45-minute CI pipeline. He argued that the solo developer is spending 15% of their day waiting for builds.
-   Thiago presented the initial UX mockups for the visual rule builder; the team agreed on a node-based interface.

**Action Items:**
-   Haruki to research `Turborepo` for CI optimization. (Owner: Haruki)
-   Ren to draft the initial Prisma schema for the `Workflows` table. (Owner: Ren)

---

### Meeting 2: Budget and Blocker Review
**Date:** 2023-12-15  
**Attendees:** Ines Kim, Haruki Moreau  
**Discussion:**
-   Haruki reported that the Webhook Integration Framework is officially blocked. The team cannot implement the payload validation without the "SchemaGuard" tool.
-   Ines confirmed that the request is with the CFO. The $12,000 expense is within the $800k budget, but it requires a specific sign-off.
-   Discussion on the competitor's progress. Reports suggest they have a similar "rule builder" already in beta.

**Action Items:**
-   Ines to escalate the budget approval request to the CFO. (Owner: Ines)
-   Ines to contact an external consultant for a competitive gap analysis. (Owner: Ines)

---

### Meeting 3: FedRAMP and Security Review
**Date:** 2024-01-20  
**Attendees:** Ines Kim, Ren Stein, Haruki Moreau  
**Discussion:**
-   Ren presented the 2FA implementation. The team verified that the hardware key support (WebAuthn) satisfies the "Multi-Factor Authentication" requirement for government clients.
-   Haruki noted that while 2FA is complete, the "Audit Logs" are still basic and need to be expanded to meet the strict FedRAMP logging standards (including original IP, user-agent, and timestamp of every mutation).
-   Agreement to prioritize the `AuditLogs` table expansion over the API Rate Limiting feature.

**Action Items:**
-   Ren to update `AuditLogs` table to include `request_payload` and `user_agent`. (Owner: Ren)
-   Haruki to create a "Security Checklist" mapped to FedRAMP requirements. (Owner: Haruki)

---

## 11. BUDGET BREAKDOWN

The total budget of **$800,000** is allocated for the 6-month build cycle.

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $520,000 | Solo Developer (Full-time), UX Researcher (Part-time), Contractor (Milestone-based). |
| **Infrastructure** | 15% | $120,000 | Vercel Enterprise, AWS/PostgreSQL Managed Instance, Redis Cloud. |
| **Tools & Licensing** | 10% | $80,000 | SchemaGuard (Pending), Jest/Playwright licenses, Security Auditing software. |
| **Contingency** | 10% | $80,000 | Reserve for regulatory changes or emergency contractor scaling. |

**Total:** **$800,000**

---

## 12. APPENDICES

### Appendix A: FedRAMP Compliance Mapping
The following technical implementations are designed to satisfy specific FedRAMP High/Moderate controls:
-   **AC-2 (Account Management):** Handled by the `Users` and `UserSecurityKeys` tables with strict role-based access control (RBAC).
-   **AU-2 (Event Logging):** Handled by the `AuditLogs` table, capturing all privileged actions.
-   **IA-2 (Identification and Authentication):** Handled by the hardware-key 2FA implementation.

### Appendix B: Conflict Resolution Logic for Offline Mode
When the system detects a conflict during background sync (i.e., the same Workflow rule was edited on two different devices), the following logic is applied:
1.  **Timestamp Check:** The system compares the `updated_at` timestamp of the local change vs. the server change.
2.  **LWW Strategy:** By default, the most recent timestamp is accepted.
3.  **User Intervention:** If the changes occur within the same 5-second window, the system marks the record as `CONFLICT_PENDING` and notifies the user via the UI to manually choose the correct version.