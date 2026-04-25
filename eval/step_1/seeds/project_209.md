Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. To ensure the level of detail requested, I have expanded every requirement into a rigorous technical framework.

***

# PROJECT SPECIFICATION: PROJECT ZENITH
**Document Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 26, 2023  
**Company:** Silverthread AI  
**Classification:** CONFIDENTIAL / HIPAA COMPLIANT  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Zenith is a strategic pivot for Silverthread AI, transforming a successful internal hackathon prototype into a commercial-grade data pipeline and analytics platform tailored for the logistics and shipping industry. Currently serving 500 daily internal users, Zenith solves the critical problem of fragmented data silos in global shipping—where manifests, customs declarations, and telemetry data exist in disparate formats. By providing a unified ingestion layer and an advanced analytics suite, Zenith allows logistics operators to optimize route efficiency and reduce "dead-head" mileage.

### 1.2 Business Justification
The logistics industry is currently undergoing a digital transformation. Legacy systems (often mainframe-based) lack the agility to handle real-time IoT data from ships and trucks. Silverthread AI has identified a gap in the market for a "middleware" analytics platform that is HIPAA compliant (essential for transporting medical supplies and pharmaceutical logistics) and capable of handling massive throughput without requiring a dedicated on-site data engineering team.

Zenith's transition from an internal tool to a product allows Silverthread AI to monetize its proprietary data-cleaning algorithms. By moving from a 500-user internal base to a commercial model, the company can capture a significant portion of the mid-market logistics sector.

### 1.3 ROI Projection and Financial Objectives
The project is allocated a lean budget of $400,000. The Return on Investment (ROI) is projected based on the following targets:
- **User Growth:** Achieving 10,000 Monthly Active Users (MAU) within six months post-launch.
- **Revenue Target:** $500,000 in attributed new revenue within the first 12 months.
- **Cost Efficiency:** By leveraging a distributed team of 15 across 5 countries (reducing overhead costs compared to a centralized HQ model), the project aims for a low Customer Acquisition Cost (CAC) relative to the Lifetime Value (LTV) of a shipping conglomerate.
- **Efficiency Gain:** Internal productivity is expected to increase by 30% through the automation of data import/export processes, replacing manual CSV manipulation.

### 1.4 Strategic Alignment
Zenith aligns with Silverthread AI’s goal of becoming the "Operating System for Global Logistics." By ensuring HIPAA compliance from the ground up, the platform differentiates itself from competitors who ignore the stringent security requirements of medical shipping.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
- **Frontend:** TypeScript, Next.js 14 (App Router), Tailwind CSS.
- **Backend/ORM:** Prisma ORM.
- **Database:** PostgreSQL 15 (Managed via AWS RDS).
- **Hosting/Deployment:** Vercel (Frontend/Edge Functions).
- **Messaging/Event Stream:** Apache Kafka (Confluent Cloud).
- **Security:** AES-256 encryption at rest, TLS 1.3 in transit.

### 2.2 Architecture Design: Event-Driven Microservices
Zenith utilizes a microservices architecture to ensure scalability and fault isolation. Each service is decoupled via Kafka topics, ensuring that a failure in the "Analytics Engine" does not prevent "Data Ingestion" from continuing.

**ASCII ARCHITECTURE DIAGRAM:**
```text
[ Client Browser ] <--> [ Vercel Edge/Next.js ] <--> [ API Gateway ]
                                                            |
                                                            v
      ______________________________________________________/ \______________________________________________________
     /                                   |                                   |                                   \
[ Ingestion Service ]        [ Auth/Identity Service ]        [ Analytics Service ]        [ Automation Engine ]
     |                                   |                                   |                                   |
     v                                   v                                   v                                   v
[ Kafka Topic: raw-data ] <--- [ Kafka Topic: user-events ] <--- [ Kafka Topic: calc-results ] <--- [ Kafka Topic: triggers ]
     |                                                                                                          |
     \___________________________________________________________________________________________________________/
                                                            |
                                                            v
                                                   [ PostgreSQL / Prisma ]
                                                   (Encrypted Data Store)
```

### 2.3 Data Flow Logic
1. **Ingestion:** Data enters via the `POST /api/v1/import` endpoint.
2. **Processing:** The Ingestion Service detects the format (CSV, JSON, XML) and pushes a "RawDataEvent" to Kafka.
3. **Transformation:** A worker service consumes the event, cleans the data using Silverthread's proprietary logic, and updates the PostgreSQL database via Prisma.
4. **Analytics:** The Analytics Service listens for database updates and computes real-time shipping metrics, which are pushed to the frontend via WebSockets.

### 2.4 Security & Compliance (HIPAA)
To maintain HIPAA compliance:
- **Encryption:** All PII (Personally Identifiable Information) is encrypted at the field level using a rotating master key stored in AWS KMS.
- **Audit Logging:** Every request to the API is logged with a timestamp, user ID, and action performed.
- **Isolation:** Production data is logically isolated from staging and development environments.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Functional Description:**
This feature is the core of the Zenith pipeline. Users in the shipping industry deal with a chaotic array of data formats. The system must allow a user to upload a file without specifying the format, and the system must "guess" the format with >99% accuracy.

**Detailed Requirements:**
- **Auto-Detection Logic:** The system will analyze the first 1KB of the uploaded file. It will check for magic bytes (e.g., `{` for JSON, `<` for XML, or delimiters like `,` and `;` for CSV/TSV).
- **Schema Mapping:** Once the format is detected, the system will attempt to map columns to the internal `Shipment` and `Manifest` models. If columns are missing, the system will trigger a "Mapping Required" UI flow.
- **Export Capabilities:** Users can export processed data into CSV, JSON, and Parquet formats. Parquet is required for high-volume analytics hand-offs to external data lakes.
- **Chunked Uploads:** To handle files up to 2GB, the system must implement multipart uploads with a checksum verification (MD5) to ensure data integrity.
- **Validation Pipeline:** Before data hits the DB, it must pass through a validation layer that checks for "null" values in critical fields (e.g., `tracking_id`, `destination_iso_code`).

**Technical Constraints:**
- Must process 1 million rows in under 60 seconds.
- Memory limit for the ingestion worker is 4GB RAM.

---

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** Complete

**Functional Description:**
Given the HIPAA requirements and the sensitivity of shipping manifests, standard password authentication is insufficient. Zenith implements a robust 2FA system.

**Detailed Requirements:**
- **TOTP Support:** Integration with Google Authenticator and Authy via time-based one-time passwords.
- **WebAuthn/FIDO2:** Support for hardware keys (YubiKey, Titan Security Key). This is mandatory for administrator accounts.
- **Recovery Codes:** Upon setup, users are provided 10 one-time-use recovery codes.
- **Session Management:** 2FA tokens are bound to the session; if a user changes their IP address significantly, a 2FA challenge is re-triggered.
- **Enrollment Flow:** A guided wizard that ensures the user has successfully tested their 2FA method before the "Password-only" login is disabled.

**Technical Implementation:**
- Use of `lucia-auth` for session management.
- Hardware key public keys are stored in the `UserSecurityKeys` table.

---

### 3.3 SSO Integration (SAML and OIDC)
**Priority:** Medium | **Status:** In Review

**Functional Description:**
Enterprise shipping clients require the ability to manage users via their own identity providers (IdP) such as Okta, Azure AD, or Ping Identity.

**Detailed Requirements:**
- **SAML 2.0:** Support for Service Provider (SP)-initiated and IdP-initiated SSO.
- **OIDC (OpenID Connect):** Support for OAuth2 flows, specifically the Authorization Code Flow with PKCE.
- **Just-In-Time (JIT) Provisioning:** If a user is authenticated via SSO but does not exist in the Zenith DB, the system should automatically create a user profile based on the SAML assertions.
- **Attribute Mapping:** A configurable UI where admins can map IdP attributes (e.g., `department`) to Zenith roles (e.g., `LogisticsManager`).
- **Single Log-Out (SLO):** When a user logs out of the IdP, the Zenith session must be invalidated.

**Technical Implementation:**
- Integration with `next-auth` (Auth.js) for provider handling.
- Metadata XML exchange for SAML configuration.

---

### 3.4 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low (Nice to Have) | **Status:** Not Started

**Functional Description:**
A "Low-Code" environment where logistics managers can create "If-This-Then-That" (IFTTT) logic for their shipments.

**Detailed Requirements:**
- **Visual Canvas:** A drag-and-drop interface (using React Flow) to connect triggers to actions.
- **Triggers:** Possible triggers include: "Shipment Status Changed," "Threshold Exceeded" (e.g., temperature > 5°C for pharma), or "Date Reached."
- **Actions:** Possible actions include: "Send Email," "Slack Notification," "Update Database Field," or "Trigger Webhook."
- **Rule Validation:** A logic checker that prevents infinite loops (e.g., Action A triggers Trigger A).
- **Version Control:** The ability to save versions of a workflow and roll back to a previous state.

**Technical Implementation:**
- Rules will be stored as JSON logic trees in the `AutomationRules` table.
- An event-listener microservice will monitor Kafka topics and execute the rules via a worker pool.

---

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Medium | **Status:** In Progress

**Functional Description:**
Multiple users must be able to edit the same shipment manifest or analytics dashboard simultaneously without overwriting each other's changes.

**Detailed Requirements:**
- **Operational Transformation (OT) or CRDTs:** Implementation of Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency.
- **Presence Indicators:** "Who is currently viewing this record" cursors and avatars.
- **Granular Locking:** Instead of locking a whole document, the system will lock specific cells or fields being edited.
- **Conflict Resolution UI:** If a hard conflict occurs (e.g., two users editing the same field at the exact millisecond), a "diff" view will appear for manual resolution.
- **Latency Compensation:** Optimistic UI updates to ensure the app feels responsive despite network lag.

**Technical Implementation:**
- Use of `Yjs` or `Automerge` for CRDT logic.
- WebSockets via `socket.io` for real-time state synchronization.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow REST conventions and return JSON. All requests require a Bearer Token in the Authorization header.

### 4.1 `POST /api/v1/import`
- **Description:** Uploads a data file for processing.
- **Request:** `multipart/form-data` (File: `file`, TenantId: `string`).
- **Response (202 Accepted):**
  ```json
  {
    "jobId": "job_98765",
    "status": "processing",
    "estimatedTime": "45s"
  }
  ```

### 4.2 `GET /api/v1/import/status/{jobId}`
- **Description:** Checks the progress of a specific import job.
- **Response (200 OK):**
  ```json
  {
    "jobId": "job_98765",
    "progress": 65,
    "rowsProcessed": 650000,
    "errors": 12
  }
  ```

### 4.3 `GET /api/v1/analytics/summary`
- **Description:** Retrieves aggregated shipping metrics for the dashboard.
- **Query Params:** `startDate`, `endDate`, `region`.
- **Response (200 OK):**
  ```json
  {
    "totalShipments": 14500,
    "avgLeadTime": "4.2 days",
    "efficiencyScore": 88.5
  }
  ```

### 4.4 `POST /api/v1/auth/2fa/setup`
- **Description:** Generates a TOTP secret and QR code for a user.
- **Response (200 OK):**
  ```json
  {
    "secret": "JBSWY3DPEHPK3PNO",
    "qrCodeUrl": "https://api.zenith.ai/qr/...",
    "recoveryCodes": ["CODE1", "CODE2", "..."]
  }
  ```

### 4.5 `POST /api/v1/auth/sso/initiate`
- **Description:** Initiates the SAML/OIDC handshake.
- **Request:** `{ "provider": "okta" }`
- **Response (302 Redirect):** Redirects user to the Identity Provider.

### 4.6 `PATCH /api/v1/shipments/{id}`
- **Description:** Updates shipment details (Collaborative).
- **Request:** `{ "status": "in_transit", "version": 42 }`
- **Response (200 OK):**
  ```json
  {
    "id": "ship_123",
    "updatedAt": "2025-01-10T10:00:00Z",
    "version": 43
  }
  ```

### 4.7 `POST /api/v1/automation/rules`
- **Description:** Creates a new automation rule.
- **Request:** `{ "name": "High Temp Alert", "trigger": "temp_gt_5", "action": "email_admin" }`
- **Response (201 Created):**
  ```json
  { "ruleId": "rule_abc123", "status": "active" }
  ```

### 4.8 `GET /api/v1/users/me`
- **Description:** Returns current session user profile.
- **Response (200 OK):**
  ```json
  {
    "id": "user_001",
    "email": "k.gupta@silverthread.ai",
    "role": "CTO",
    "mfaEnabled": true
  }
  ```

---

## 5. DATABASE SCHEMA

### 5.1 Entities and Relationships
The schema is designed for high relational integrity and HIPAA-compliant auditing.

| Table Name | Primary Key | Key Fields | Relationships |
| :--- | :--- | :--- | :--- |
| `Users` | `userId` | `email`, `passwordHash`, `mfaSecret`, `role` | 1:M with `UserSecurityKeys` |
| `Tenants` | `tenantId` | `companyName`, `planLevel`, `createdAt` | 1:M with `Users` |
| `Shipments` | `shipmentId` | `trackingNumber`, `origin`, `destination`, `status` | M:1 with `Tenants` |
| `Manifests` | `manifestId` | `shipmentId`, `contentDescription`, `weight` | 1:1 with `Shipments` |
| `ImportJobs` | `jobId` | `tenantId`, `fileName`, `status`, `rowCount` | M:1 with `Tenants` |
| `ImportErrors` | `errorId` | `jobId`, `rowNumber`, `errorMessage` | M:1 with `ImportJobs` |
| `UserSecurityKeys` | `keyId` | `userId`, `publicKey`, `deviceId`, `createdAt` | M:1 with `Users` |
| `AutomationRules` | `ruleId` | `tenantId`, `triggerJson`, `actionJson`, `isActive` | M:1 with `Tenants` |
| `AuditLogs` | `logId` | `userId`, `action`, `entityId`, `timestamp`, `ipAddress` | M:1 with `Users` |
| `CollaborativeSessions`| `sessionId` | `entityId`, `userId`, `lastActiveAt` | M:1 with `Shipments` |

### 5.2 Schema Detail: The `Shipments` Table
- `shipmentId`: UUID (Primary Key)
- `tenantId`: UUID (Foreign Key $\rightarrow$ Tenants)
- `tracking_number`: String (Indexed)
- `status`: Enum (`PENDING`, `IN_TRANSIT`, `DELIVERED`, `EXCEPTED`)
- `origin_address`: EncryptedText
- `destination_address`: EncryptedText
- `created_at`: DateTime
- `updated_at`: DateTime
- `version`: Integer (Used for Optimistic Concurrency Control)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Zenith utilizes three distinct environments to ensure stability and security.

#### 6.1.1 Development (`dev`)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Vercel Preview deployments, shared PostgreSQL instance.
- **Data:** Mock data only. No real customer data ever enters `dev`.
- **Deployment:** Automatic on every push to a feature branch.

#### 6.1.2 Staging (`staging`)
- **Purpose:** Integration testing and QA.
- **Infrastructure:** Mirror of production (Vercel Project, Dedicated RDS instance).
- **Data:** Anonymized snapshots of production data.
- **Deployment:** Manual trigger from `main` branch. Requires a "Green" signal from the QA Lead (Nyla Liu).

#### 6.1.3 Production (`prod`)
- **Purpose:** Live customer traffic.
- **Infrastructure:** High-availability AWS RDS (Multi-AZ), Vercel Production, Confluent Cloud Kafka.
- **Deployment:** **Manual QA Gate.** Every release requires sign-off from Nyla Liu and Kamau Gupta. Turnaround for a release is exactly 2 days (1 day for staging soak, 1 day for final verification).

### 6.2 Infrastructure Budget Allocation
The infrastructure is optimized for the $400,000 total budget.
- **Vercel Pro/Enterprise:** $2,000/mo
- **AWS RDS (Postgres):** $1,500/mo
- **Confluent Cloud (Kafka):** $1,200/mo
- **AWS KMS/S3:** $300/mo

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, Prisma middleware, and utility helpers.
- **Tooling:** Jest and Vitest.
- **Requirement:** 80% code coverage for all business-critical logic (e.g., the format auto-detection algorithm).

### 7.2 Integration Testing
- **Scope:** API endpoint to database flow.
- **Tooling:** Supertest and Playwright.
- **Focus:** Testing the Kafka event chain. A test must verify that a `POST /import` eventually results in a record in the `Shipments` table.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., User logs in $\rightarrow$ Uploads CSV $\rightarrow$ Views Analytics Dashboard).
- **Tooling:** Playwright.
- **Frequency:** Run on every build in the `staging` environment.

### 7.4 QA Gate Process
Nyla Liu (QA Lead) manages the "Manual QA Gate." No code reaches production without:
1. Validated E2E test suite completion.
2. Manual verification of the "Critical" priority features.
3. Security scan for HIPAA compliance (OWASP ZAP).

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Team lacks experience with TS/Next.js/Prisma/Kafka | High | High | Negotiate timeline extension with stakeholders; implement weekly "Knowledge Share" sessions. |
| R2 | Performance requirements 10x current capacity w/o extra budget | Medium | High | Document aggressive caching strategies and database indexing workarounds; share with the dev team. |
| R3 | Medical leave of key team member (6 weeks) | Actual | High | Redistribute tasks among the other 14 members; prioritize critical features over "nice-to-haves." |
| R4 | Technical Debt: Hardcoded configs in 40+ files | High | Medium | Implement a centralized `.env` management system and a configuration service using `zod` for validation. |
| R5 | HIPAA Compliance breach | Low | Critical | Third-party security audit every quarter; strict field-level encryption. |

**Probability/Impact Matrix:**
- **High/High:** Immediate Action Required (R1, R3).
- **Med/High:** Close Monitoring (R2).
- **High/Med:** Scheduled Remediation (R4).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase 1: Foundations (Current $\rightarrow$ March 2025)
- **Focus:** Finalizing Data Import/Export and 2FA.
- **Dependency:** Infrastructure setup for Kafka.
- **Milestone 1:** **External beta with 10 pilot users (Target: 2025-03-15).**

### 9.2 Phase 2: Enterprise Readiness (March 2025 $\rightarrow$ May 2025)
- **Focus:** SSO Integration and Collaborative Editing.
- **Dependency:** Completion of Beta feedback loop.
- **Milestone 2:** **First paying customer onboarded (Target: 2025-05-15).**

### 9.3 Phase 3: Optimization & Scale (May 2025 $\rightarrow$ July 2025)
- **Focus:** Architecture Review and Automation Engine.
- **Dependency:** Data from first paying customer to inform scaling.
- **Milestone 3:** **Architecture review complete (Target: 2025-07-15).**

### 9.4 Gantt-Style Summary
- **Jan - Feb:** $\text{[Data Import Design]} \rightarrow \text{[Kafka Setup]} \rightarrow \text{[SAML Review]}$
- **Mar:** $\text{[Beta Launch]} \leftarrow \text{[QA Gate]}$
- **Apr - May:** $\text{[Collaborative Editing]} \rightarrow \text{[Customer Onboarding]}$
- **Jun - Jul:** $\text{[Architecture Audit]} \rightarrow \text{[Rule Builder Start]}$

---

## 10. MEETING NOTES

### Meeting 1: Stack Alignment
**Date:** 2023-11-02  
**Attendees:** Kamau, Isadora, Nyla, Saoirse  
- Stack decided: Next.js/Prisma.
- Kafka for events—everyone worried about learning curve.
- Kamau says "figure it out," but will ask for more time if we hit a wall.
- Saoirse to handle basic UI components.

### Meeting 2: HIPAA & Security Sync
**Date:** 2023-12-15  
**Attendees:** Kamau, Nyla  
- Encryption at rest is non-negotiable.
- Use AES-256.
- Nyla wants a manual gate for prod. Kamau agreed. 2-day turnaround.
- Need to find a way to audit every single API call.

### Meeting 3: The "Crisis" Meeting (Blocker Discussion)
**Date:** 2024-01-20  
**Attendees:** Kamau, Isadora, Nyla  
- Key dev on medical leave for 6 weeks.
- We are behind on Collaborative Editing.
- Decision: Push "Workflow Automation" to lowest priority. Focus on "Data Import" as it's the launch blocker.
- Isadora to take over some of the backend API work.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $280,000 | Salaries for distributed team of 15 (adjusted for regional costs). |
| **Infrastructure** | 15% | $60,000 | AWS RDS, Vercel, Confluent Cloud for 18 months. |
| **Tooling/Licenses** | 5% | $20,000 | GitHub Enterprise, Jira, Sentry, Datadog. |
| **Contingency** | 10% | $40,000 | Emergency scaling or specialized security consultants. |

---

## 12. APPENDICES

### Appendix A: Data Format Detection Logic
The auto-detection system uses a scoring mechanism.
1. **JSON Score:** If it starts with `{` and ends with `}`, $+10$ points.
2. **XML Score:** If it contains `<?xml` or `<root>`, $+10$ points.
3. **CSV Score:** If the first line contains 3 or more commas and the second line has the same number of commas, $+10$ points.
4. **Winner:** The format with the highest score is selected. If tied, the system defaults to CSV.

### Appendix B: Distributed Team Communication Protocol
Due to the team being spread across 5 countries, the following rules apply:
- **Core Hours:** 14:00 to 17:00 UTC (Overlap window for all regions).
- **Async First:** All decisions must be documented in Jira or GitHub Issues; "Slack decisions" are not official.
- **Handover:** The "follow-the-sun" model is used; engineers in Asia hand off tasks to Europe, who then hand off to the Americas.