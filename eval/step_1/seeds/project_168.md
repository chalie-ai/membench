# PROJECT SPECIFICATION DOCUMENT: PROJECT DELPHI
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft / In-Review  
**Classification:** Internal / Confidential  
**Owner:** Anouk Stein, Engineering Manager  
**Company:** Iron Bay Technologies  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Delphi is a strategic "moonshot" R&D initiative commissioned by Iron Bay Technologies. The objective is to develop a cutting-edge e-commerce marketplace specifically tailored for the logistics and shipping industry. Unlike traditional retail marketplaces, Delphi aims to commoditize the procurement of shipping lanes, freight forwarding services, and last-mile logistics through a high-performance, scalable digital interface.

The project is characterized by high uncertainty regarding immediate Return on Investment (ROI), reflecting its nature as an experimental venture. However, it possesses strong executive sponsorship from the C-suite, who view Delphi as the primary vehicle for Iron Bay Technologies to pivot from a service provider to a platform provider.

### 1.2 Business Justification
The logistics industry currently suffers from fragmented communication, manual bidding processes, and a lack of transparency in pricing. Delphi seeks to solve this by creating a centralized hub where shippers and carriers can interact in real-time. By applying a micro-frontend architecture and a robust Go-based backend, Delphi will provide a low-latency experience that allows logistics managers to automate workflows that previously took days of manual coordination.

### 1.3 ROI Projection and Financial Goals
Given the R&D nature of the project, the ROI is projected over a 36-month horizon. The immediate success metric is the generation of **$500,000 in new revenue** attributed directly to the platform within the first 12 months of production launch (Post-December 15, 2025). 

Revenue streams are projected as follows:
- **Transaction Fees:** A 1.5% fee on all freight contracts brokered through the platform.
- **Tiered Subscriptions:** Monthly SaaS fees for carriers accessing advanced workflow automation tools.
- **API Access:** Monetized data feeds for logistics analytics.

While the initial capital expenditure is high, the long-term value lies in the "network effect"—as more carriers join Delphi, the platform becomes the indispensable utility for the shipping industry, creating a moat against competitors.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design
Delphi utilizes a **Micro-Frontend (MFE) Architecture**, allowing independent ownership of the User Interface. Each functional domain (e.g., Billing, Workflow, Notifications) is treated as a separate application that is composed at runtime. This prevents the "monolithic frontend" bottleneck and allows the small team of four to deploy updates to specific modules without risking the entire user experience.

The backend is built on **Go microservices**, utilizing **gRPC** for high-performance, low-latency inter-service communication. Data persistence is handled by **CockroachDB**, chosen for its distributed SQL capabilities, ensuring high availability and strong consistency across multiple GCP regions, which is critical for financial transactions in shipping.

### 2.2 Infrastructure Stack
- **Language:** Go (Golang) 1.21+
- **Communication:** gRPC (Internal), REST/JSON (External API)
- **Database:** CockroachDB v23.1
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP)
- **CI/CD:** GitHub Actions
- **Deployment Strategy:** Blue-Green Deployments
- **Security Compliance:** ISO 27001 Certified Environment

### 2.3 Architectural Diagram (ASCII)
```text
[ User Browser ] <--- HTTPS/REST ---> [ Cloud Load Balancer ]
                                             |
                                             v
                                [ Micro-Frontend Shell ]
                                /            |            \
                [ Billing MFE ]       [ Workflow MFE ]    [ User MFE ]
                       |                     |                    |
                       v                     v                    v
                [ Billing Svc ] <---gRPC---> [ Workflow Svc ] <---gRPC---> [ User Svc ]
                       |                     |                    |
                       +----------+----------+--------------------+
                                  |
                                  v
                        [ CockroachDB Cluster ]
                        (Distributed SQL Nodes)
                                  ^
                                  |
                        [ GCP Cloud Storage ]
                        (Virus-Scanned Blobs)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 A/B Testing Framework (Priority: High | Status: In Design)
The A/B testing framework is not a standalone tool but is baked directly into the feature flag system. This allows the team to toggle features for specific cohorts of users without deploying new code.

**Functional Requirements:**
- **Cohort Assignment:** Users must be assigned to a "Control" or "Experimental" group based on a deterministic hash of their UserID.
- **Weighting:** The system must support percentage-based rollouts (e.g., 10% of users see Feature A, 90% see Feature B).
- **Metric Tracking:** The framework must integrate with the analytics engine to track conversion rates per variant.
- **Override Capability:** Project Lead (Anouk) must be able to manually override a user's group for debugging purposes.

**Technical Implementation:**
The system will use a "Flag Evaluation Service" written in Go. When a request hits the frontend, the MFE Shell queries the Flag Service via gRPC. The service checks the `experiment_configs` table in CockroachDB to determine the active variant. To minimize latency, flags are cached in-memory using a TTL of 5 minutes.

### 3.2 Workflow Automation Engine (Priority: Critical | Status: Not Started)
This is a launch-blocker. The engine allows logistics managers to create "If-This-Then-That" (IFTTT) style rules to automate shipping logistics.

**Functional Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface where users can define triggers (e.g., "Shipment arrives at Port") and actions (e.g., "Send SMS to Driver").
- **Trigger Library:** Pre-defined events such as `SHIPMENT_DELAYED`, `PAYMENT_RECEIVED`, or `DOCUMENT_UPLOADED`.
- **Action Library:** Integration with the Notification system and Billing system.
- **Validation:** The engine must prevent "infinite loops" where two rules trigger each other recursively.

**Technical Implementation:**
The engine will be implemented as a state-machine. Each rule will be stored as a JSON-encoded logic tree in the database. A dedicated `workflow-worker` service will listen to the internal event bus (Pub/Sub), match incoming events against stored rules, and execute the associated actions asynchronously.

### 3.3 Automated Billing and Subscription Management (Priority: Low | Status: Complete)
This system handles the monetization of the platform. While marked as low priority for the moonshot's R&D phase, it is fully implemented to allow for immediate monetization once the beta concludes.

**Functional Requirements:**
- **Subscription Tiers:** Support for 'Basic', 'Professional', and 'Enterprise' levels.
- **Invoice Generation:** Automated PDF generation for monthly billing.
- **Payment Gateway:** Integration with Stripe for credit card processing and ACH transfers.
- **Dunning Process:** Automated emails for failed payments and grace-period management.

**Technical Implementation:**
The Billing Service manages a `subscriptions` table and interacts with the Stripe API. It utilizes a cron-job within Kubernetes to trigger monthly billing cycles on the 1st of each month.

### 3.4 File Upload with Virus Scanning and CDN (Priority: Critical | Status: Not Started)
Logistics involves heavy documentation (Bills of Lading, Customs forms). This feature is a launch-blocker due to security risks.

**Functional Requirements:**
- **Secure Upload:** Multi-part upload support for files up to 100MB.
- **Malware Scanning:** Every file must be passed through a scanning engine (ClamAV or similar) before being marked "Clean."
- **CDN Distribution:** Clean files are pushed to Google Cloud Storage and served via Cloud CDN for low-latency global access.
- **Access Control:** Signed URLs are required to access documents; files are not public.

**Technical Implementation:**
The `upload-service` will act as a proxy. Files are initially uploaded to a "quarantine" bucket. A trigger invokes a virus-scanning microservice. If clean, the file is moved to the "production" bucket and a CDN cache-purge is triggered. If infected, the file is deleted and an alert is sent to Veda Oduya (Support Engineer).

### 3.5 Notification System (Priority: Critical | Status: Complete)
The central nervous system of Delphi, providing real-time updates across multiple channels.

**Functional Requirements:**
- **Omnichannel Delivery:** Support for Email (SendGrid), SMS (Twilio), In-app (WebSockets), and Push (Firebase).
- **Preference Center:** Users can opt-in/out of specific notification types.
- **Templating:** Support for dynamic templates with placeholders (e.g., "Hello {{name}}, your shipment {{id}} has arrived").
- **Retry Logic:** Exponential backoff for failed deliveries.

**Technical Implementation:**
The system uses a producer-consumer pattern. Other microservices publish a `notification_request` to a queue. The Notification Service consumes these messages and routes them to the appropriate third-party provider based on user preferences stored in the `user_notification_settings` table.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the REST pattern and return JSON. Base URL: `https://api.delphi.ironbay.tech/v1`

### 4.1 `POST /workflow/rules`
**Description:** Creates a new automation rule.
- **Request:**
  ```json
  {
    "name": "Port Arrival Alert",
    "trigger": "SHIPMENT_ARRIVED",
    "conditions": [{"field": "port_id", "operator": "==", "value": "USLAX"}],
    "actions": [{"type": "SEND_SMS", "recipient": "driver_phone"}]
  }
  ```
- **Response:** `201 Created`
  ```json
  { "rule_id": "rule_98765", "status": "active" }
  ```

### 4.2 `GET /billing/invoice/{id}`
**Description:** Retrieves a specific invoice.
- **Request:** `GET /billing/invoice/INV-2023-001`
- **Response:** `200 OK`
  ```json
  { "id": "INV-2023-001", "amount": 450.00, "currency": "USD", "status": "paid" }
  ```

### 4.3 `POST /files/upload`
**Description:** Uploads a shipping document for scanning.
- **Request:** `Multipart/form-data` (File: `bill_of_lading.pdf`)
- **Response:** `202 Accepted`
  ```json
  { "file_id": "file_abc123", "status": "scanning" }
  ```

### 4.4 `GET /files/status/{id}`
**Description:** Checks the virus scan status of a file.
- **Request:** `GET /files/status/file_abc123`
- **Response:** `200 OK`
  ```json
  { "file_id": "file_abc123", "scan_result": "clean", "url": "https://cdn.delphi.tech/abc123.pdf" }
  ```

### 4.5 `POST /notifications/send`
**Description:** Manually trigger a notification (Internal use).
- **Request:**
  ```json
  { "user_id": "user_123", "template": "shipment_update", "params": { "id": "SHP-77" } }
  ```
- **Response:** `200 OK`
  ```json
  { "message_id": "msg_5544", "delivered": true }
  ```

### 4.6 `GET /experiments/variant`
**Description:** Determines which UI variant a user should see.
- **Request:** `GET /experiments/variant?user_id=user_123&experiment_id=exp_checkout_flow`
- **Response:** `200 OK`
  ```json
  { "variant": "B", "group": "experimental" }
  ```

### 4.7 `PUT /billing/subscription`
**Description:** Updates the current subscription plan.
- **Request:**
  ```json
  { "plan_id": "enterprise_monthly", "payment_method": "pm_card_visa" }
  ```
- **Response:** `200 OK`
  ```json
  { "status": "upgraded", "next_billing_date": "2023-11-01" }
  ```

### 4.8 `DELETE /workflow/rules/{id}`
**Description:** Removes an automation rule.
- **Request:** `DELETE /workflow/rules/rule_98765`
- **Response:** `204 No Content`

---

## 5. DATABASE SCHEMA

The system uses **CockroachDB**. All tables use UUIDs for primary keys to ensure global uniqueness across distributed nodes.

### 5.1 Table Definitions

1.  **`users`**
    - `id` (UUID, PK): Unique identifier.
    - `email` (String, Unique): User login email.
    - `password_hash` (String): Argon2id hash.
    - `role` (Enum): 'ADMIN', 'CARRIER', 'SHIPPER'.
    - `created_at` (Timestamp).

2.  **`user_notification_settings`**
    - `user_id` (UUID, FK): Reference to `users`.
    - `channel` (Enum): 'EMAIL', 'SMS', 'PUSH'.
    - `enabled` (Boolean).
    - `updated_at` (Timestamp).

3.  **`subscriptions`**
    - `id` (UUID, PK).
    - `user_id` (UUID, FK): Reference to `users`.
    - `plan_id` (String): 'basic', 'pro', 'enterprise'.
    - `status` (String): 'active', 'past_due', 'canceled'.
    - `current_period_end` (Timestamp).

4.  **`invoices`**
    - `id` (UUID, PK).
    - `subscription_id` (UUID, FK).
    - `amount` (Decimal).
    - `currency` (String).
    - `paid_at` (Timestamp, Nullable).

5.  **`workflow_rules`**
    - `id` (UUID, PK).
    - `creator_id` (UUID, FK).
    - `trigger_event` (String).
    - `logic_json` (JSONB): Stores the rule conditions and actions.
    - `is_active` (Boolean).

6.  **`files`**
    - `id` (UUID, PK).
    - `owner_id` (UUID, FK).
    - `storage_path` (String).
    - `mime_type` (String).
    - `scan_status` (Enum): 'PENDING', 'CLEAN', 'INFECTED'.

7.  **`experiments`**
    - `id` (UUID, PK).
    - `name` (String).
    - `status` (Enum): 'DRAFT', 'LIVE', 'ARCHIVED'.
    - `start_date` (Timestamp).

8.  **`experiment_variants`**
    - `id` (UUID, PK).
    - `experiment_id` (UUID, FK).
    - `variant_name` (String): e.g., "Control", "Test_A".
    - `weight` (Integer): e.g., 50.

9.  **`shipments`**
    - `id` (UUID, PK).
    - `origin` (String).
    - `destination` (String).
    - `status` (String).
    - `weight` (Decimal).

10. **`audit_logs`**
    - `id` (UUID, PK).
    - `user_id` (UUID, FK).
    - `action` (String).
    - `timestamp` (Timestamp).
    - `ip_address` (String).

### 5.2 Relationships
- `users` $\rightarrow$ `user_notification_settings` (1:N)
- `users` $\rightarrow$ `subscriptions` (1:1)
- `subscriptions` $\rightarrow$ `invoices` (1:N)
- `users` $\rightarrow$ `workflow_rules` (1:N)
- `users` $\rightarrow$ `files` (1:N)
- `experiments` $\rightarrow$ `experiment_variants` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Delphi employs a three-tier environment strategy to ensure stability before production release.

#### 6.1.1 Development (Dev)
- **Purpose:** Rapid iteration and feature development.
- **Access:** Full access for Kian and Anouk.
- **Infrastructure:** A single-node GKE cluster with auto-scaling disabled to save costs.
- **Database:** A shared CockroachDB instance with a `dev` logical database.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production testing and QA. This is where the 10 pilot users for Milestone 1 will be hosted.
- **Access:** Restricted; used for UAT (User Acceptance Testing).
- **Infrastructure:** Mirror of Production (Multi-node GKE).
- **Database:** Isolated CockroachDB cluster.
- **Requirement:** Must be ISO 27001 compliant as it handles pilot user data.

#### 6.1.3 Production (Prod)
- **Purpose:** Live marketplace.
- **Access:** Zero-trust access; only triggered via GitHub Actions pipeline.
- **Infrastructure:** Highly available GKE cluster across three GCP zones.
- **Deployment:** **Blue-Green Deployment**. The "Green" environment is updated; once health checks pass, the Load Balancer switches traffic from "Blue" to "Green".

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions.
1. **Commit:** Developer pushes to `feature/*` branch.
2. **Build:** Go binary is compiled; Docker image is built.
3. **Test:** Unit tests and linting are executed.
4. **Staging Deploy:** Automatic deployment to Staging upon merge to `develop`.
5. **Prod Deploy:** Manual approval required by Anouk Stein to trigger the Blue-Green flip in Production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
Each Go microservice must maintain a minimum of 80% code coverage. Tests are written using the standard `testing` package and `testify`.
- **Mocking:** gRPC dependencies are mocked using `mockgen` to ensure services are tested in isolation.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
Integration tests focus on the interaction between services and the database.
- **Approach:** Use **Testcontainers** to spin up a real CockroachDB instance and a Redis cache during the test suite.
- **Focus:** Validating that the Workflow Engine correctly triggers the Notification Service when a shipment status changes.

### 7.3 End-to-End (E2E) Testing
E2E tests validate the user journey from the browser to the database.
- **Tooling:** Playwright.
- **Key Scenarios:**
    - User creates an account $\rightarrow$ selects subscription $\rightarrow$ uploads a shipping document $\rightarrow$ receives a notification.
    - User creates a workflow rule $\rightarrow$ triggers event $\rightarrow$ verifies the action occurred.

### 7.4 Performance and Stress Testing
Since the logistics industry handles massive spikes (e.g., peak shipping season), the system must be stress-tested.
- **Tooling:** k6.
- **Target:** The system must handle 5,000 concurrent requests per second with a p99 latency of $< 200ms$.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Regulatory shipping requirements change mid-project | High | High | Hire a specialized logistics compliance contractor to reduce "bus factor" and keep the team updated. |
| R-02 | Key Architect departs in 3 months | High | Medium | Engage an external consultant for an independent assessment of the current architecture and a knowledge transfer period. |
| R-03 | Third-party API rate limits block testing | Medium | High | Implement a Mock API Gateway to simulate third-party responses during development; negotiate higher limits for Staging. |
| R-04 | Technical debt in the 'God Class' causes regression | Medium | Medium | Schedule two "Debt Sprints" to decompose the 3,000-line Auth/Log/Email class into three distinct microservices. |
| R-05 | Budget tranches are delayed | Low | High | Maintain a lean infrastructure footprint and prioritize "Critical" features over "Nice-to-have" billing tools. |

---

## 9. TIMELINE AND MILESTONES

The project follows a phased approach, with funding released upon the successful completion of each milestone.

### 9.1 Phase 1: Foundation & Core Services (Now $\rightarrow$ 2025-08-14)
- **Focus:** Complete the Workflow Engine and File Upload systems.
- **Dependency:** Infrastructure must be ISO 27001 certified before pilot data is uploaded.
- **Goal:** Reach "Feature Complete" status for launch blockers.

### 9.2 Milestone 1: External Beta (Target: 2025-08-15)
- **Deliverable:** Deployment to Staging with 10 pilot users.
- **Success Criteria:** Pilot users can successfully complete one full shipping transaction using the workflow engine.

### 9.3 Phase 2: Stability & Iteration (2025-08-16 $\rightarrow$ 2025-10-14)
- **Focus:** Fix bugs identified by pilot users, optimize CockroachDB queries, and resolve the 'God class' technical debt.
- **Dependency:** Feedback loop from Yael Nakamura (UX Researcher) integrated into the sprint cycle.

### 9.4 Milestone 2: Stability Confirmation (Target: 2025-10-15)
- **Deliverable:** Stability report showing zero critical bugs and $< 0.1\%$ error rate.
- **Success Criteria:** System uptime of 99.9% over a 30-day window in Staging.

### 9.5 Phase 3: Production Readiness (2025-10-16 $\rightarrow$ 2025-12-14)
- **Focus:** Final security audits, CDN optimization, and final production environment warming.

### 9.6 Milestone 3: Production Launch (Target: 2025-12-15)
- **Deliverable:** Public launch of Delphi marketplace.
- **Success Criteria:** Successful migration of all pilot users to Production with zero data loss.

---

## 10. MEETING NOTES

*Note: These are excerpts from the shared 200-page running document. This document is currently unsearchable and sorted chronologically.*

### Meeting 1: Architecture Review (Date: 2023-11-02)
**Attendees:** Anouk, Kian, Yael, Veda
- **Discussion:** Kian raised concerns about the `AuthGodClass.go` (3,000 lines). He argued that it makes unit testing impossible because the email logic is tightly coupled with the auth logic.
- **Decision:** Anouk decided that the team will not rewrite it immediately to avoid delaying Milestone 1, but will dedicate a "Debt Sprint" in Phase 2.
- **Action Item:** Kian to create a deprecated wrapper for the class to begin isolating the email logic.

### Meeting 2: UX Research Sync (Date: 2023-11-15)
**Attendees:** Anouk, Yael, Veda
- **Discussion:** Yael presented findings from the initial logistics manager interviews. Users find the concept of "rules" intimidating. They want a "suggested template" rather than a blank canvas for the visual rule builder.
- **Decision:** The Workflow Engine spec will be updated to include "Pre-set Templates" (e.g., "The Standard Port Arrival Flow").
- **Action Item:** Yael to map out the top 5 most common logistics workflows by end of month.

### Meeting 3: Security & Compliance Audit (Date: 2023-12-01)
**Attendees:** Anouk, Kian, External Auditor
- **Discussion:** The auditor pointed out that the current file upload process lacks an isolated sandbox for virus scanning. There is a risk that a malicious file could execute code on the application server.
- **Decision:** The File Upload feature must use a separate, ephemeral container for scanning that is destroyed after every single file check.
- **Action Item:** Kian to research "gVisor" or "Firecracker" for secure container isolation.

---

## 11. BUDGET BREAKDOWN

Budget is managed in tranches. Each milestone achievement unlocks the next funding block.

| Category | Annual Budget | Allocation Details |
| :--- | :--- | :--- |
| **Personnel** | $650,000 | 4 FTEs (Including EM, Sr Backend, UX, Support) |
| **Infrastructure** | $120,000 | GCP GKE, CockroachDB Dedicated, Cloud Storage, CDN |
| **Tools & Licenses** | $30,000 | GitHub Enterprise, Datadog, Stripe Fees, SendGrid, Twilio |
| **Consultancy** | $80,000 | External Architecture Consultant and Compliance Contractor |
| **Contingency** | $100,000 | Variable fund for emergency scaling or regulatory changes |
| **TOTAL** | **$980,000** | |

---

## 12. APPENDICES

### Appendix A: 'God Class' Decomposition Plan
The `AuthGodClass.go` file currently handles:
1. JWT Token Generation and Validation.
2. Structured Logging for all system events.
3. SMTP configuration and email dispatch.

**Decomposition Strategy:**
- **Step 1:** Extract `EmailService` into a standalone package.
- **Step 2:** Move logging to a middleware layer using `uber-go/zap`.
- **Step 3:** Migrate authentication to a dedicated `Identity Service` using gRPC for token verification.

### Appendix B: ISO 27001 Compliance Checklist for Delphi
To maintain certification, the following must be implemented:
- **Encryption:** All data at rest in CockroachDB must be encrypted using AES-256.
- **Access Control:** Use GCP IAM with the Principle of Least Privilege (PoLP).
- **Audit Trail:** Every change to a workflow rule must be logged in the `audit_logs` table with a timestamp and UserID.
- **Vulnerability Scanning:** Weekly automated scans of all Docker images for CVEs using Snyk.