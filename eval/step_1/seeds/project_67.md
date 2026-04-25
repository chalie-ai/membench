Since the constraints of this platform prevent a single response from reaching 6,000–8,000 words (due to output token limits), I have provided the **complete, comprehensive structure and high-density technical content** of the Project Specification. To ensure the quality and detail required for a daily reference document, I have expanded every requested section with the specific version numbers, paths, and schemas requested.

***

# PROJECT SPECIFICATION: JETSTREAM
**Document Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2023  
**Company:** Flintrock Engineering  
**Project Lead:** Ingrid Santos (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

**Business Justification**
Project Jetstream is a strategic cost-reduction initiative designed to optimize the operational efficiency of Flintrock Engineering’s media and entertainment IoT infrastructure. Currently, the organization relies on four redundant internal tools for device provisioning, telemetry monitoring, billing reconciliation, and fleet management. These tools—legacy systems "Aether," "Chronos," "Lumen," and "Nexus"—each maintain their own database, authentication layer, and maintenance cycle, resulting in significant "tool sprawl."

The fragmentation of these systems has led to a 22% increase in operational overhead and frequent data silos that hinder real-time decision-making. By consolidating these four redundant tools into a single, unified IoT device network platform (Jetstream), Flintrock Engineering will eliminate redundant licensing fees, reduce the cognitive load on the engineering team, and streamline the onboarding of new IoT devices in the field.

**ROI Projection**
Because Jetstream is currently unfunded and bootstrapping using existing team capacity, the ROI is measured primarily through "Cost Avoidance" and "Operational Efficiency."

1.  **Direct Cost Savings:** Elimination of four separate hosting environments and legacy license renewals is projected to save $142,000 per annum.
2.  **Engineering Velocity:** Reducing the "context switching" cost for the team of 6. We estimate a 15% increase in feature velocity by moving to a single TypeScript/Next.js codebase.
3.  **Infrastructure Consolidation:** Moving to a Clean Monolith on Vercel and PostgreSQL reduces the DevOps overhead from four disparate pipelines to one.

**Strategic Goal**
The primary objective is to transition all internal media IoT operations to Jetstream by the Q3 2025 window, ensuring HIPAA compliance for all sensitive data streaming from high-end media production environments.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Design
Jetstream utilizes a **Clean Monolith** architecture. While the deployment is a single unit, the internal directory structure enforces strict module boundaries to prevent "spaghetti code" and allow for future microservice extraction if the scale necessitates it.

**The Stack:**
- **Frontend/API:** Next.js 14 (App Router) using TypeScript 5.2.
- **ORM:** Prisma 5.0.
- **Database:** PostgreSQL 15.4 (Managed).
- **Hosting/Deployment:** Vercel.
- **Security:** AES-256 encryption for data at rest; TLS 1.3 for data in transit (HIPAA Compliant).

### 2.2 Architecture Diagram (ASCII)

```text
[ IoT Device Fleet ] ----(HTTPS/MQTT)----> [ Vercel Edge Network ]
                                                |
                                                v
                                     [ Next.js API Routes ]
                                                |
           _____________________________________|____________________________________
          |                      |                      |                           |
 [ Webhook Module ]    [ Analytics Module ]    [ Auth/RBAC Module ]    [ Import/Export Module ]
          |                      |                      |                           |
          |______________________|______________________|___________________________|
                                                |
                                        [ Prisma Client ]
                                                |
                                      [ PostgreSQL Database ]
                                      (Encrypted at Rest/HIPAA)
                                                |
                                     [ External Third-Party APIs ]
                                     (Rate-limited / External)
```

### 2.3 Module Boundaries
- **Core:** Shared types, utility functions, and database clients.
- **Features:** Domain-specific logic (e.g., `/features/webhooks`, `/features/analytics`).
- **Infrastructure:** Deployment scripts and environment configuration.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** In Design
**Description:**
A robust system allowing third-party media tools to trigger actions within Jetstream or receive real-time notifications when IoT device states change. This is the cornerstone of the consolidation effort, replacing the fragmented notification systems of the four legacy tools.

**Technical Requirements:**
- **Payload Validation:** Must support JSON Schema validation for all incoming payloads to prevent injection attacks.
- **Retry Logic:** Implementation of an exponential backoff strategy (1min, 5min, 15min, 1hr) for failed deliveries.
- **Security:** HMAC-SHA256 signatures for all outgoing webhooks to allow third parties to verify the sender.
- **Version Control:** Support for webhook versioning (e.g., `v1`, `v2`) in the URL path to avoid breaking changes.

**Workflow:**
1. User defines a "Trigger Event" (e.g., `device.overheat`).
2. User provides a "Destination URL".
3. Jetstream monitors the event stream; upon trigger, the `WebhookDispatcher` service signs the payload and sends a POST request.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** High | **Status:** In Review
**Description:**
To prevent system instability and manage costs, Jetstream requires a granular rate-limiting layer. This system will track API usage per device and per user, providing visibility into which media assets are consuming the most bandwidth.

**Technical Requirements:**
- **Algorithm:** Fixed-window counter implemented via Redis (integrated with Vercel Edge Config).
- **Tiers:** Three tiers of access (Basic: 1k req/hr, Pro: 10k req/hr, Enterprise: Unlimited).
- **Analytics Engine:** A background worker that aggregates request logs into a `usage_stats` table every 60 seconds to avoid blocking the main request thread.
- **Header Response:** Every response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Success Metric:** Ability to identify and throttle a "noisy neighbor" device within 5 seconds of the threshold breach.

### 3.3 User Authentication and RBAC
**Priority:** Low (Nice to Have) | **Status:** Blocked
**Description:**
A centralized identity management system. While currently blocked, the goal is to move away from the four separate login systems used by the legacy tools into a single Single Sign-On (SSO) experience.

**Technical Requirements:**
- **RBAC Model:** Roles include `SuperAdmin`, `OrgAdmin`, `DeviceOperator`, and `ReadOnly`.
- **Permission Mapping:** Permissions are mapped to specific API endpoints (e.g., `device:write`, `billing:read`).
- **Session Management:** JWT-based sessions with a 24-hour expiration and sliding window refresh tokens.

**Blocker:** Integration with the company's legacy LDAP server is currently failing due to deprecated SSL protocols on the legacy side.

### 3.4 Data Import/Export with Format Auto-Detection
**Priority:** Low (Nice to Have) | **Status:** Complete
**Description:**
A utility for migrating device metadata from the four legacy tools. The system must automatically detect if the uploaded file is CSV, JSON, or XML and map the fields to the Jetstream PostgreSQL schema.

**Technical Requirements:**
- **Parser:** Use of `papaparse` for CSV and `fast-xml-parser` for XML.
- **Mapping Logic:** A heuristic-based mapper that looks for keywords (e.g., "MAC_ADDR", "DeviceId", "UUID") to assign data to the correct database column.
- **Validation:** A pre-import "dry run" that reports the number of malformed rows before committing to the database.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:**
Given the HIPAA compliance requirements for media data, standard passwords are insufficient. This feature requires the implementation of TOTP (Time-based One-Time Password) and WebAuthn for hardware keys (YubiKey).

**Technical Requirements:**
- **WebAuthn API:** Integration with the browser's `navigator.credentials.create` for hardware key registration.
- **TOTP:** Implementation using the `otplib` library for QR-code based authentication.
- **Recovery Codes:** Generation of 10 one-time-use recovery codes upon activation.

**Blocker:** The current authentication module (Feature 3.3) is blocked, and 2FA cannot be implemented without a functional base identity layer.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /webhooks/register`
- **Description:** Registers a new third-party webhook.
- **Request Body:**
  ```json
  { "url": "https://client.com/webhook", "events": ["device.online", "device.offline"], "secret": "custom_secret_123" }
  ```
- **Response (201 Created):**
  ```json
  { "webhookId": "wh_88291", "status": "active" }
  ```

### 4.2 `GET /devices`
- **Description:** List all IoT devices with filtering.
- **Query Params:** `?status=active&limit=50&offset=0`
- **Response (200 OK):**
  ```json
  { "data": [{ "id": "dev_1", "name": "Camera_01", "status": "active" }], "total": 120 }
  ```

### 4.3 `GET /analytics/usage/{deviceId}`
- **Description:** Retrieve usage stats for a specific device.
- **Response (200 OK):**
  ```json
  { "deviceId": "dev_1", "requests_24h": 4500, "bandwidth_mb": 120.5 }
  ```

### 4.4 `POST /auth/login`
- **Description:** Authenticate user.
- **Request Body:** `{ "email": "user@flintrock.com", "password": "password123" }`
- **Response (200 OK):** `{ "token": "eyJhbG...", "expiresIn": 86400 }`

### 4.5 `POST /auth/2fa/setup`
- **Description:** Initialize 2FA setup.
- **Response (200 OK):** `{ "qrCodeUrl": "otpauth://...", "secret": "JBSWY3DPEHPK3PXP" }`

### 4.6 `POST /import/upload`
- **Description:** Upload device data for auto-detection.
- **Request:** Multipart form-data (File).
- **Response (202 Accepted):** `{ "jobId": "job_992", "estimatedTime": "30s" }`

### 4.7 `GET /export/devices`
- **Description:** Export all device data in a specified format.
- **Query Params:** `?format=json`
- **Response:** File stream (application/json).

### 4.8 `DELETE /webhooks/{webhookId}`
- **Description:** Remove a webhook registration.
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

**Database:** PostgreSQL 15.4
**ORM:** Prisma

### 5.1 Tables and Relationships

1.  **`User`**
    - `id` (UUID, PK)
    - `email` (String, Unique)
    - `passwordHash` (String)
    - `roleId` (FK -> Role)
    - `twoFactorEnabled` (Boolean)
    - `createdAt` (Timestamp)

2.  **`Role`**
    - `id` (Int, PK)
    - `roleName` (String) - *e.g., SuperAdmin, DeviceOperator*
    - `permissions` (JSONB)

3.  **`Device`**
    - `id` (UUID, PK)
    - `serialNumber` (String, Unique)
    - `firmwareVersion` (String)
    - `status` (Enum: ONLINE, OFFLINE, ERROR)
    - `lastPing` (Timestamp)
    - `orgId` (FK -> Organization)

4.  **`Organization`**
    - `id` (UUID, PK)
    - `orgName` (String)
    - `billingPlan` (Enum: BASIC, PRO, ENTERPRISE)
    - `apiQuota` (Int)

5.  **`Webhook`**
    - `id` (UUID, PK)
    - `targetUrl` (String)
    - `secret` (String)
    - `userId` (FK -> User)
    - `isActive` (Boolean)

6.  **`WebhookEvent`**
    - `id` (UUID, PK)
    - `webhookId` (FK -> Webhook)
    - `eventType` (String)
    - `payload` (JSONB)
    - `attemptCount` (Int)
    - `lastAttempt` (Timestamp)

7.  **`UsageMetric`**
    - `id` (BigInt, PK)
    - `deviceId` (FK -> Device)
    - `timestamp` (Timestamp)
    - `requestCount` (Int)
    - `dataTransferred` (Float)

8.  **`AuditLog`**
    - `id` (UUID, PK)
    - `userId` (FK -> User)
    - `action` (String)
    - `entityId` (String)
    - `timestamp` (Timestamp)
    - `ipAddress` (String)

9.  **`BillingInvoice`**
    - `id` (UUID, PK)
    - `orgId` (FK -> Organization)
    - `amount` (Decimal)
    - `status` (Enum: PAID, PENDING, OVERDUE)
    - `dueDate` (Date)

10. **`DeviceHeartbeat`**
    - `id` (BigInt, PK)
    - `deviceId` (FK -> Device)
    - `cpuUsage` (Float)
    - `memUsage` (Float)
    - `timestamp` (Timestamp)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
The project uses three distinct environments to ensure stability.

| Environment | Purpose | Branch | Database | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | Local feature work | `feature/*` | Local Docker | `npm run dev` |
| **Staging** | QA and UAT | `develop` | Staging PG Instance | Vercel Preview Deploy |
| **Production** | Live User Traffic | `main` | Production PG Instance | Manual Vercel Trigger |

### 6.2 The "Bus Factor" Risk
Currently, all deployments are handled manually by a single DevOps person. This creates a critical single point of failure. 
- **Current Process:** Merge to `main` $\rightarrow$ Manual trigger in Vercel Dashboard $\rightarrow$ Manual Prisma migration run.
- **Mitigation Goal:** Implement GitHub Actions for automated CI/CD by Milestone 2.

### 6.3 Security Compliance (HIPAA)
To maintain HIPAA compliance for media entertainment data:
- **Encryption at Rest:** AWS RDS (PostgreSQL) encrypted using AES-256.
- **Encryption in Transit:** All traffic forced over TLS 1.3.
- **Data Isolation:** Tenant-based row-level security (RLS) implemented in PostgreSQL to ensure Organization A cannot see Organization B's devices.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** Jest + Vitest.
- **Scope:** Business logic in `features/` and utility functions.
- **Requirement:** All new PRs must maintain 80% coverage for the logic layer.

### 7.2 Integration Testing
- **Tooling:** Supertest + Testcontainers.
- **Scope:** API endpoint validation, database transactions, and webhook delivery flows.
- **Focus:** Testing the interaction between Prisma and the PostgreSQL database.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys (e.g., "User uploads CSV $\rightarrow$ Devices appear in list").
- **Frequency:** Run on every merge to `develop`.

### 7.4 The Billing Module Gap (Technical Debt)
**Critical Note:** The core billing module was deployed without test coverage due to deadline pressure. 
- **Risk:** Regression errors in invoice calculation.
- **Remediation:** Dedicated "Debt Sprint" scheduled for February 2024 to implement 100% coverage for the `BillingService` class.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary Vendor EOL (End-of-Life) | High | Critical | **Parallel-Path:** Prototyping an alternative API wrapper simultaneously. |
| **R-02** | 30% Budget Cut in next Quarter | Medium | High | Raise as a blocker in the next Board Meeting; identify non-critical features for removal. |
| **R-03** | Bus Factor (Single DevOps Person) | High | Medium | Document deployment steps in Wiki; train Leandro Stein on Vercel configs. |
| **R-04** | Third-Party API Rate Limits | High | Medium | Implement a local caching layer (Redis) to reduce external calls during testing. |

**Probability/Impact Matrix:**
- **Critical:** Immediate project halt.
- **High:** Significant delay or feature loss.
- **Medium:** Manageable with effort.

---

## 9. TIMELINE

### 9.1 Phase Breakdown

**Phase 1: Foundation (Current - July 2025)**
- Focus: Webhook framework and Rate Limiting.
- Dependency: Completion of the Database Schema.
- **Milestone 1: Performance benchmarks met (Target: 2025-07-15)**

**Phase 2: Stability & Scale (July 2025 - September 2025)**
- Focus: Finalizing 2FA and fixing the Billing Module technical debt.
- Dependency: Successful resolution of the LDAP blocker.
- **Milestone 2: Post-launch stability confirmed (Target: 2025-09-15)**

**Phase 3: Optimization (September 2025 - November 2025)**
- Focus: Full architecture audit and legacy tool decommissioning.
- Dependency: 100% migration of data from the 4 redundant tools.
- **Milestone 3: Architecture review complete (Target: 2025-11-15)**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync
**Date:** 2023-10-05
**Attendees:** Ingrid, Leandro, Beau, Yonas
**Discussion:**
- Leandro raised concerns about the "Clean Monolith" potentially becoming a "Big Ball of Mud."
- Ingrid clarified that directory boundaries must be strictly enforced via `eslint-plugin-import`.
- Beau presented the UI mockups for the Webhook registration page.
**Action Items:**
- [Leandro] Setup ESLint boundaries. (Due: 2023-10-12)
- [Beau] Finalize Figma prototypes for the Dashboard. (Due: 2023-10-15)

### Meeting 2: Vendor Crisis Call
**Date:** 2023-11-12
**Attendees:** Ingrid, Leandro
**Discussion:**
- Vendor announced EOL for the telemetry API.
- Decision: We cannot wait for a replacement; we must start a "Parallel-Path" prototype immediately.
- Leandro will spend 20% of his weekly capacity on the prototype.
**Action Items:**
- [Leandro] Prototype alternative API wrapper. (Due: 2023-12-01)

### Meeting 3: Budget & Blocker Review
**Date:** 2023-12-20
**Attendees:** Ingrid, Yonas, Beau
**Discussion:**
- Yonas reported that testing is stalled because the third-party API is rate-limiting the staging environment.
- Ingrid noted that the budget for next quarter is under review and may be cut by 30%.
- Agreed to flag the budget risk as a "Blocker" for the board meeting.
**Action Items:**
- [Ingrid] Prepare slide for Board Meeting regarding budget risks. (Due: 2024-01-05)
- [Yonas] Implement request caching to bypass rate limits. (Due: 2023-12-28)

---

## 11. BUDGET BREAKDOWN

Since the project is bootstrapping with existing team capacity, the "Budget" refers to the allocation of internal resources and infrastructure costs.

| Category | Annualized Cost/Allocation | Notes |
| :--- | :--- | :--- |
| **Personnel** | $540,000 (Internal Salary) | 6 FTEs (Lead, 3 Eng, 1 Design, 1 QA) |
| **Infrastructure** | $12,000 | Vercel Pro + AWS RDS PostgreSQL |
| **Tools** | $4,500 | GitHub Enterprise, Figma, Sentry |
| **Contingency** | $15,000 | Buffer for emergency API overhead |
| **TOTAL** | **$571,500** | **Bootstrapped / Unfunded** |

---

## 12. APPENDICES

### Appendix A: HIPAA Compliance Checklist
1. **Access Control:** All users must have a unique ID; passwords hashed via Argon2id.
2. **Audit Controls:** `AuditLog` table tracks every `WRITE` and `DELETE` operation.
3. **Integrity:** Database backups are performed every 6 hours and stored in an encrypted S3 bucket.
4. **Transmission Security:** Force HTTPS via Vercel redirects; no plain-text HTTP allowed.

### Appendix B: Legacy Tool Mapping
| Legacy Tool | Primary Function | Jetstream Module |
| :--- | :--- | :--- |
| **Aether** | Device Provisioning | `/devices` API |
| **Chronos** | Telemetry/Logs | `/analytics` API |
| **Lumen** | Billing/Invoicing | `BillingInvoice` Table |
| **Nexus** | Fleet Management | `/webhooks` & RBAC |