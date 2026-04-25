Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, industrial-grade Technical Specification. It expands every provided constraint into a rigorous operational manual.

***

# PROJECT SPECIFICATION: WAYFINDER (v2.0.0)
**Company:** Crosswind Labs  
**Document Version:** 1.0.4  
**Classification:** Confidential / Internal  
**Last Updated:** October 24, 2023  
**Project Lead:** Brigid Liu  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Wayfinder is the flagship customer-facing mobile application for Crosswind Labs, designed to provide seamless legal service management for end-users. The current iteration of the product has suffered a catastrophic failure in user adoption and satisfaction, characterized by critical feedback regarding UI latency, unintuitive navigation, and systemic instability. Market research indicates that the legal services industry is shifting toward "self-service" models; however, Crosswind Labs' current offering is an obstacle to this growth rather than an accelerator.

The "Wayfinder Rebuild" is not merely a UI refresh but a total architectural pivot. The goal is to transform a fragmented legacy system into a streamlined, high-performance mobile experience that reduces the "time-to-value" for a new client from 14 days to under 24 hours. By rebuilding the core engine, we aim to eliminate the friction points that led to the current negative feedback loop, thereby preventing churn and capturing a larger share of the mid-market legal sector.

### 1.2 ROI Projection
The financial objective of the Wayfinder rebuild is centered on two primary levers: User Acquisition and Operational Efficiency.

**A. User Growth & Revenue:**
With a target of 10,000 Monthly Active Users (MAU) within six months of launch, we project a monthly recurring revenue (MRR) increase of $120,000, assuming a conservative Average Revenue Per User (ARPU) of $12.00. This represents a 300% increase over the current failing version.

**B. Cost Reduction:**
The current system requires significant manual intervention from the legal operations team to resolve billing errors and workflow glitches. By implementing the "Workflow Automation Engine" and "Automated Billing," we project a reduction in manual support tickets by 65%, saving approximately $4,000 per month in operational overhead.

**C. Projected Payback Period:**
Given the $400,000 investment, the break-even point is estimated at 14 months post-launch, assuming the growth targets are met. The long-term ROI over three years is projected at 210%, driven by the scalability of the new clean monolith architecture.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 The "Mixed-Stack" Challenge
Wayfinder inherits three disparate technology stacks from previous acquisitions and legacy iterations:
1. **Stack A (Legacy Core):** Java/Spring Boot (Handling the heavy-lift legal logic).
2. **Stack B (Billing Module):** Node.js/TypeScript (Integrating with payment gateways).
3. **Stack C (Frontend/Mobile):** React Native (The current failing UI layer).

The architecture is designed as a **Clean Monolith**. While the stacks are mixed, they will operate within a single deployment boundary with strictly defined module boundaries to prevent "spaghetti" dependencies. Communication between the mixed stacks occurs via an internal event bus and shared memory spaces where possible, or local REST calls for decoupled services.

### 2.2 Architectural Diagram (ASCII)

```text
[ MOBILE CLIENT (React Native) ]
           |
           | (HTTPS/TLS 1.3)
           v
[ API GATEWAY / AUTH LAYER ] <--- [ PCI DSS COMPLIANCE WALL ]
           |
           +---------------------------------------+
           |                                       |
[ MODULE: USER & ACCESS ]               [ MODULE: BILLING & SUBS ]
(Java / Spring Boot)                    (Node.js / TypeScript)
   |-- RBAC Engine                         |-- Stripe/Braintree API
   |-- Session Mgr                         |-- Subscription Logic
           |                                       |
           +-------------------+-------------------+
                               |
                    [ MODULE: WORKFLOW ENGINE ]
                    (Java / Spring Boot / Drools)
                               |
                               v
                    [ SHARED PERSISTENCE LAYER ]
                    (PostgreSQL / Redis Cache)
                               |
                               v
                    [ LEGACY DATA LAKE / EXTERNAL API ]
                    (Undocumented Integration Partner)
```

### 2.3 Security & Compliance
The application must adhere to **PCI DSS Level 1** standards because it processes credit card data directly. 
- **Encryption:** All data at rest is encrypted using AES-256. Data in transit utilizes TLS 1.3.
- **Isolation:** Credit card data is handled in a "Cardholder Data Environment" (CDE) physically and logically isolated from the rest of the application.
- **Audit Trails:** Every modification to a user's billing status or legal document is logged with an immutable timestamp and user ID.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Workflow Automation Engine with Visual Rule Builder
**Priority:** Critical | **Status:** In Progress | **Launch Blocker:** Yes

The Workflow Automation Engine is the heart of Wayfinder. It allows legal professionals and clients to automate the progression of a legal case (e.g., "If document X is signed, then move case to 'Review' status and notify Attorney Y").

**Functional Specifications:**
- **Visual Rule Builder:** A drag-and-drop interface where users can create "If-This-Then-That" (IFTTT) logic. The builder must support boolean operators (AND, OR, NOT) and nested conditions.
- **Trigger Events:** Triggers include "Document Upload," "Payment Received," "Date Reached," and "Field Value Changed."
- **Action Executions:** Actions include "Send Email," "Change Case Status," "Generate PDF," and "Create Task."
- **State Machine:** The engine will utilize a finite state machine (FSM) to ensure that a case cannot skip mandatory legal steps.

**Technical Implementation:**
The engine is built using a combination of Java and the Drools rule engine. The visual builder in the frontend will emit a JSON representation of the logic, which is then parsed and stored in the `workflow_rules` table. To ensure performance, rules are compiled into executable bytecode at the time of saving.

**Acceptance Criteria:**
- A user can create a 3-step automated workflow without writing code.
- The engine processes triggers in < 200ms.
- Conflict resolution prevents "infinite loops" (e.g., Rule A triggers Rule B, which triggers Rule A).

### 3.2 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** Blocked

The dashboard is the primary landing page for the user. To address previous feedback regarding "clutter," the new dashboard is entirely modular.

**Functional Specifications:**
- **Widget Library:** Users can choose from a set of pre-defined widgets: *Case Progress Tracker, Upcoming Deadlines, Recent Documents, Billing Summary, and Message Alerts.*
- **Drag-and-Drop Interface:** Users can reposition widgets using a grid-based system (similar to Notion or iOS widgets).
- **Widget Configuration:** Each widget has a "settings" gear where users can filter the data shown (e.g., the "Recent Documents" widget can be filtered to show only "Urgent" files).
- **Persistence:** Dashboard layouts are saved per user in the database, ensuring a consistent experience across devices.

**Technical Implementation:**
Implemented via `react-grid-layout`. The frontend calculates the coordinates (x, y, w, h) of each widget and sends a `PUT` request to `/api/v1/user/dashboard/layout` to save the configuration.

**Acceptance Criteria:**
- Layouts persist after logout/login.
- Drag-and-drop functionality is smooth on both iOS and Android.
- Widgets load asynchronously to prevent blocking the main UI thread.

### 3.3 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Blocked

Legal documents require multiple stakeholders to review and edit simultaneously. This feature eliminates the "versioning nightmare" of email attachments.

**Functional Specifications:**
- **Concurrent Editing:** Multiple users can edit a document in real-time. Presence indicators (colored cursors) show who is editing which line.
- **Conflict Resolution:** The system will implement **Operational Transformation (OT)** to merge changes. If two users edit the same character simultaneously, the system resolves it based on the server's timestamp.
- **Version History:** A complete snapshot of the document is taken every 5 minutes, allowing users to revert to any previous state.
- **Commenting:** Users can highlight text and leave threaded comments.

**Technical Implementation:**
Using WebSockets (Socket.io) for real-time transport. The server maintains a shadow copy of the document to validate transformations before broadcasting them to other clients.

**Acceptance Criteria:**
- Latency between users is < 100ms.
- No data loss occurs during simultaneous edits by 5+ users.
- Document recovery is possible from any 5-minute snapshot.

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** In Progress

Access to legal data is highly sensitive. A robust RBAC system ensures that users only see what they are legally permitted to see.

**Functional Specifications:**
- **Multi-Factor Authentication (MFA):** Support for SMS and Authenticator App (TOTP).
- **Role Hierarchy:** Four primary roles: `SuperAdmin`, `Attorney`, `Paralegal`, and `Client`.
- **Permission Granularity:** Permissions are mapped to specific actions (e.g., `can_edit_billing`, `can_view_case_files`).
- **Session Management:** JWT-based authentication with 15-minute sliding expiration.

**Technical Implementation:**
This feature is currently battling the "God Class" technical debt. The goal is to migrate the logic from the 3,000-line `AuthManager` class into a set of decoupled services: `IdentityService`, `PermissionService`, and `SessionService`.

**Acceptance Criteria:**
- A `Client` cannot access `Attorney` endpoints.
- MFA is mandatory for all `SuperAdmin` accounts.
- Tokens are successfully invalidated upon logout.

### 3.5 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** Blocked

This feature automates the invoicing process, reducing the manual labor involved in legal billing.

**Functional Specifications:**
- **Subscription Tiers:** Three tiers: *Basic, Professional, and Enterprise.*
- **Automatic Invoicing:** Monthly invoices are generated on the 1st of every month based on the user's plan.
- **Payment Gateway Integration:** Integration with Stripe for credit card processing and automated retries for failed payments.
- **Usage-Based Billing:** Ability to bill for "extra" documents or hours beyond the tier limit.

**Technical Implementation:**
Built using the Node.js stack. It utilizes a webhook listener to process payments from Stripe and update the `subscription_status` in the database.

**Acceptance Criteria:**
- Payments are processed securely according to PCI DSS Level 1.
- Invoices are automatically emailed to the user in PDF format.
- Subscription upgrades/downgrades are reflected in real-time.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints reside under `https://api.wayfinder.crosswind.io/v1`.

### 4.1 Authentication
**`POST /auth/login`**
- **Request:** `{ "email": "user@law.com", "password": "hashed_password" }`
- **Response:** `{ "token": "eyJhbG...", "expires_at": "2025-10-24T10:00:00Z" }`
- **Description:** Authenticates user and returns a JWT.

**`POST /auth/mfa/verify`**
- **Request:** `{ "token": "eyJhbG...", "code": "123456" }`
- **Response:** `{ "status": "verified", "session_id": "sess_987" }`
- **Description:** Verifies the 6-digit MFA code.

### 4.2 Workflow Engine
**`POST /workflow/rules`**
- **Request:** `{ "trigger": "doc_upload", "condition": "file_type == 'PDF'", "action": "notify_user", "target_id": "user_123" }`
- **Response:** `{ "rule_id": "rule_abc123", "status": "active" }`
- **Description:** Creates a new automation rule.

**`GET /workflow/status/{case_id}`**
- **Request:** Path parameter `case_id`
- **Response:** `{ "current_state": "Awaiting_Signature", "next_steps": ["Attorney_Review"], "last_updated": "2025-01-01" }`
- **Description:** Retrieves the current state of a legal case.

### 4.3 Dashboard
**`GET /dashboard/config`**
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `[ { "id": "widget_1", "pos": { "x": 0, "y": 0, "w": 2, "h": 2 }, "type": "progress_bar" }, ... ]`
- **Description:** Fetches the user's saved dashboard layout.

**`PUT /dashboard/config`**
- **Request:** `[ { "id": "widget_1", "pos": { "x": 2, "y": 0, "w": 2, "h": 2 }, "type": "progress_bar" }, ... ]`
- **Response:** `{ "status": "updated" }`
- **Description:** Saves a new dashboard layout.

### 4.4 Billing
**`POST /billing/subscribe`**
- **Request:** `{ "plan_id": "plan_pro_monthly", "payment_method_id": "pm_card_visa" }`
- **Response:** `{ "subscription_id": "sub_555", "next_billing_date": "2025-11-01" }`
- **Description:** Initializes a new subscription.

**`GET /billing/invoices`**
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `[ { "invoice_id": "inv_1", "amount": 49.99, "date": "2025-10-01", "url": "https://...pdf" } ]`
- **Description:** Returns a list of historical invoices.

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL instance with a normalized structure.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `mfa_secret` | Central user identity table. |
| `roles` | `role_id` | None | `role_name`, `permission_level` | Definitions of roles (Admin, Client, etc). |
| `user_roles` | `mapping_id` | `user_id`, `role_id` | `assigned_at` | Junction table for User $\rightarrow$ Role. |
| `cases` | `case_id` | `lead_attorney_id` | `case_name`, `current_status`, `created_at` | Legal case tracking. |
| `workflow_rules` | `rule_id` | `case_id` (opt) | `trigger_event`, `condition_json`, `action_type` | Logic for the automation engine. |
| `documents` | `doc_id` | `case_id`, `owner_id` | `s3_url`, `checksum`, `version_number` | Metadata for legal files. |
| `doc_versions` | `ver_id` | `doc_id` | `delta_blob`, `created_by`, `timestamp` | Stores OT deltas for collaboration. |
| `subscriptions`| `sub_id` | `user_id` | `stripe_customer_id`, `plan_id`, `status` | Billing state. |
| `plans` | `plan_id` | None | `price`, `monthly_limit`, `feature_set` | Subscription tier definitions. |
| `audit_logs` | `log_id` | `user_id` | `action`, `ip_address`, `timestamp` | Immutable security log for PCI DSS. |

### 5.2 Relationships
- **Users to Roles:** Many-to-Many via `user_roles`.
- **Cases to Documents:** One-to-Many (One case has many documents).
- **Documents to Versions:** One-to-Many (One document has many version increments).
- **Users to Subscriptions:** One-to-One (Standard users have one active plan).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To maintain PCI DSS compliance and stability, Wayfinder uses three distinct environments:

**1. Development (Dev)**
- **Purpose:** Daily iteration and feature experimentation.
- **Infrastructure:** Local Docker containers and a shared "Dev" Kubernetes namespace.
- **Data:** Synthetic data only. No real client data.
- **Deployment:** Continuous Deployment (CD) on every merge to the `develop` branch.

**2. Staging (Staging)**
- **Purpose:** Pre-production validation and QA testing.
- **Infrastructure:** Mirrors Production architecture exactly (AWS EKS).
- **Data:** Sanitized production snapshots (PII removed).
- **Deployment:** Weekly merges from `develop` to `staging`.

**3. Production (Prod)**
- **Purpose:** Live customer traffic.
- **Infrastructure:** Multi-region AWS deployment with Auto-Scaling Groups.
- **Data:** Encrypted live data.
- **Deployment:** **Quarterly Releases**. Deployments are frozen during regulatory review cycles.

### 6.2 PCI DSS Compliance Wall
The production environment implements a "CDE (Cardholder Data Environment) Isolation" strategy. The Node.js billing module runs in a separate VPC (Virtual Private Cloud) with strictly controlled ingress/egress. Only the billing module can communicate with the Stripe API. All other modules communicate with the billing module via a secure internal API proxy.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Coverage Target:** 80% of the business logic.
- **Tooling:** JUnit (Java), Jest (Node.js/React).
- **Frequency:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** Inter-stack communication (e.g., Java $\rightarrow$ Node.js $\rightarrow$ Postgres).
- **Strategy:** Use "Testcontainers" to spin up ephemeral database and Redis instances.
- **Frequency:** Run on every Pull Request.

### 7.3 End-to-End (E2E) Testing
- **Focus:** Critical user paths (e.g., "Client signs document $\rightarrow$ Workflow triggers $\rightarrow$ Billing invoice sent").
- **Tooling:** Detox (for React Native mobile testing) and Cypress (for admin web views).
- **Frequency:** Run nightly on the Staging environment.

### 7.4 Performance Benchmarking
Due to the 10x capacity requirement, the team will perform "Stress Tests" using JMeter.
- **Target:** 1,000 concurrent requests per second (RPS) without latency exceeding 500ms.
- **Constraint:** Must be achieved within the current fixed infrastructure budget.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Performance requirements are 10x current capacity with no extra budget. | High | Critical | Hire a specialized performance contractor to optimize the DB and JVM; implement aggressive Redis caching. |
| **R2** | Integration partner's API is undocumented and buggy. | High | High | Engage an external consultant for an independent assessment and build a robust "Adapter" layer to sanitize inputs. |
| **R3** | "God Class" technical debt leads to regressions during RBAC update. | Medium | High | Implement "Strangler Fig" pattern: gradually move logic out of `AuthManager` into micro-services. |
| **R4** | PCI DSS audit failure. | Low | Critical | Weekly internal audits and use of a qualified Security Officer (QSA) for pre-audit. |
| **R5** | Team member on medical leave (6 weeks) creates a knowledge vacuum. | High | Medium | Distribute the leave-member's tasks across the team; document all undocumented logic immediately. |

---

## 9. TIMELINE

### 9.1 Phase 1: Foundation (Jan 2025 – March 2025)
- **Focus:** Decoupling the "God Class" and setting up the Clean Monolith.
- **Dependencies:** Completion of RBAC module.
- **Goal:** Stabilize authentication and user roles.

### 9.2 Phase 2: Core Engine (April 2025 – June 2025)
- **Focus:** Workflow Automation Engine and visual builder.
- **Dependencies:** Stable API Gateway.
- **Goal:** Reach "Critical" feature stability.

### 9.3 Phase 3: Launch & Polish (July 2025 – Sept 2025)
- **Milestone 1 (2025-07-15):** **Production Launch.**
- **Focus:** Final PCI DSS audit and deployment.
- **Milestone 2 (2025-09-15):** **MVP Feature-Complete.**
- **Goal:** Dashboard and Billing operational.

### 9.4 Phase 4: Optimization (Oct 2025 – Nov 2025)
- **Focus:** Performance tuning and real-time editing.
- **Milestone 3 (2025-11-15):** **Performance Benchmarks Met.**
- **Goal:** System handles 10x load.

---

## 10. MEETING NOTES (Archive)

*Note: These notes are extracted from the 200-page shared running document. Search is not supported.*

**Meeting 1: 2024-11-12 | Topic: "The God Class Problem"**
- **Attendees:** Brigid, Meera, Anders
- **Discussion:** Brigid pointed out that `AuthManager.java` has reached 3,000 lines. It is now handling email templates and logging, which is causing merge conflicts every single day.
- **Decision:** We cannot delete it yet, but we will stop adding to it. Meera will create a new `NotificationService` to take over the email logic.
- **Action:** Meera to create a Jira ticket for the migration.

**Meeting 2: 2024-12-05 | Topic: "Integration Partner API Chaos"**
- **Attendees:** Brigid, Anouk, Anders
- **Discussion:** Anders reported that the partner API returns a `200 OK` even when the request fails, with the error hidden in a string field inside the JSON. This is breaking the workflow engine.
- **Decision:** We will not try to "fix" their API. Instead, we will build an "API Sanitizer" layer that translates their buggy responses into standard HTTP error codes.
- **Action:** Brigid to find an external consultant for an audit of the partner's API.

**Meeting 3: 2025-01-15 | Topic: "Resource Shortage"**
- **Attendees:** Brigid, Meera, Anouk
- **Discussion:** A key developer is on medical leave for 6 weeks. This blocks the "Automated Billing" feature.
- **Decision:** We are not hiring a full-time replacement due to the $400k budget. We will shift Anders (Contractor) to help Meera with the frontend widgets to keep the momentum, and delay the billing feature until the member returns.
- **Action:** Brigid to update the Gantt chart.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel (Internal)** | $220,000 | Salaries for Brigid, Meera, Anouk, and supporting staff. |
| **Personnel (Contractor)** | $80,000 | Anders Gupta's contract and the performance optimization specialist. |
| **Infrastructure (AWS)** | $40,000 | EKS, RDS, S3, and Redis (Projected for 1 year). |
| **Tools & Licenses** | $20,000 | GitHub Enterprise, Jira, Slack, Stripe Fees, Security Auditing Tooling. |
| **External Consultants** | $25,000 | Integration API assessment and PCI DSS pre-audit. |
| **Contingency Fund** | $15,000 | Reserved for emergency scaling or unforeseen API costs. |

---

## 12. APPENDICES

### Appendix A: Operational Transformation (OT) Logic
The collaborative editing feature utilizes the following transformation function to resolve conflicts:
If two operations $O_1$ (insert at position $p_1$) and $O_2$ (insert at position $p_2$) occur simultaneously:
- If $p_1 < p_2$, $O_2$ is shifted by the length of $O_1$.
- If $p_1 = p_2$, priority is given to the user with the lower alphabetical UserID.
This ensures all clients converge to the same document state.

### Appendix B: PCI DSS Level 1 Control Mapping
| Control | Wayfinder Implementation |
| :--- | :--- |
| **Firewall Configuration** | AWS Security Groups limiting ingress to Port 443 only for the CDE. |
| **Password Policy** | Minimum 12 characters, mixed case, symbol required, rotated every 90 days. |
| **Encryption** | AWS KMS (Key Management Service) managing AES-256 keys. |
| **Physical Security** | Outsourced to AWS (SOC2 compliant data centers). |
| **Vulnerability Scanning** | Weekly automated scans using Nessus and quarterly manual penetration tests. |