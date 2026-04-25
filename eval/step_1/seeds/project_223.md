Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Technical Specification. 

***

# PROJECT ARCHWAY: TECHNICAL SPECIFICATION DOCUMENT
**Version:** 1.0.4  
**Status:** Draft for Review  
**Date:** October 24, 2025  
**Project Lead:** Kenji Oduya  
**Company:** Clearpoint Digital  
**Classification:** Confidential / FedRAMP Sensitive  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Archway is a critical strategic pivot for Clearpoint Digital. Following the launch of our current renewable energy management platform, the company received catastrophic user feedback. NPS scores plummeted to -42, and churn rates among Tier-1 government contractors increased by 28% in Q3. Users cited an unstable interface, frequent timeouts, and a complete lack of notification transparency.

The current monolith is unable to scale to meet the demands of high-resolution energy telemetry data. Archway represents a complete rebuild—migrating from a legacy monolithic architecture to a modern, serverless microservices architecture orchestrated via a robust API Gateway. By decoupling the frontend (Next.js) from the backend logic and implementing a strict API Gateway, Clearpoint Digital will ensure a responsive, modular, and secure environment capable of handling the rigors of the renewable energy sector.

### 1.2 Strategic Objectives
The primary objective is to restore market trust and achieve FedRAMP authorization, allowing Clearpoint to bid on larger US federal energy contracts. The migration focuses on reliability, security, and a "notification-first" user experience.

### 1.3 ROI Projection
The projected Return on Investment (ROI) for Project Archway is calculated over a 36-month horizon:
- **Churn Reduction:** We anticipate a 15% reduction in annual churn, preserving approximately $4.2M in Annual Recurring Revenue (ARR).
- **Operational Efficiency:** Moving to Vercel and serverless functions is expected to reduce infrastructure overhead costs by 22% through automated scaling.
- **Market Expansion:** FedRAMP authorization unlocks a projected $12M in untapped federal government opportunities.
- **Total Projected Net Gain:** $14.8M by FY 2028, with a break-even point estimated at 14 months post-MVP launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Archway utilizes a "BFF" (Backend for Frontend) pattern implemented via Next.js API routes acting as an orchestration layer, which then communicates with a series of serverless microservices.

**The Stack:**
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS.
- **Backend/API:** Vercel Serverless Functions (Node.js 20.x).
- **ORM:** Prisma (v5.10+).
- **Database:** PostgreSQL 16 (Managed via Neon/Vercel Postgres).
- **Infrastructure:** Vercel for hosting and edge routing.
- **Identity:** SAML 2.0 / OIDC (Auth0 integration).

### 2.2 Architecture Diagram (ASCII)

```text
[ Client Browser / Mobile App ]
            |
            v
    [ Vercel Edge Network ] <--- SSL Termination / DDoS Protection
            |
            v
    [ API Gateway (Next.js) ] <--- Rate Limiting, Auth Validation, Routing
            |
    -----------------------------------------------------------------------
    |                   |                   |                    |
    v                   v                   v                    v
[ Auth Service ]    [ Notification ]    [ Reporting ]       [ Energy Data ]
 (SAML/OIDC)        (SMS/Email/Push)    (PDF/CSV Gen)        (Telemetry)
    |                   |                   |                    |
    -----------------------------------------------------------------------
            |
            v
    [ Prisma ORM Layer ] <--- (Warning: 30% Raw SQL bypass for performance)
            |
            v
    [ PostgreSQL Cluster ] <--- Relational Data / FedRAMP Compliant Storage
```

### 2.3 Orchestration Logic
The API Gateway is not a separate piece of software but a set of middleware and route handlers within the Next.js project. It handles:
- **Request Transformation:** Mapping client-side JSON to internal service calls.
- **Authentication:** Intercepting requests to verify JWTs issued by the OIDC provider.
- **Circuit Breaking:** Implementing timeouts to prevent a failure in the Reporting service from cascading to the Notification system.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: High | Status: In Design)
**Overview:** A multi-channel alert system to notify energy grid operators of threshold breaches, system failures, or scheduled maintenance.

**Functional Requirements:**
- **Multi-Channel Delivery:** Support for Email (SendGrid), SMS (Twilio), In-App (WebSockets/Pusher), and Push (Firebase Cloud Messaging).
- **Preference Center:** Users must be able to toggle notification channels per event type (e.g., "Critical Alerts" via SMS and Email, "Monthly Reports" via Email only).
- **Queueing Logic:** Notifications must be processed asynchronously. The API Gateway will push an event to a queue; a background worker will handle the delivery to prevent blocking the UI.
- **Retry Mechanism:** Exponential backoff for failed SMS/Email deliveries.

**Technical Constraints:**
- All notifications must be logged in the `NotificationLogs` table for audit purposes (FedRAMP requirement).
- Latency from trigger to delivery must be < 2 seconds for "Critical" priority alerts.

**User Story:** *As a Grid Manager, I want to receive an immediate SMS alert when a solar inverter drops below 10% efficiency so that I can dispatch a technician immediately.*

---

### 3.2 Webhook Integration Framework (Priority: Medium | Status: In Design)
**Overview:** A framework allowing third-party energy auditing tools and government monitoring software to receive real-time data from Clearpoint.

**Functional Requirements:**
- **Endpoint Registration:** Users can register a destination URL and a secret key.
- **Event Selection:** Users choose which events trigger a webhook (e.g., `report.generated`, `alert.triggered`, `user.created`).
- **Payload Standardization:** All webhooks must follow a standardized JSON schema to ensure compatibility.
- **Signature Verification:** Every request sent by Archway must include an `X-Archway-Signature` header (HMAC-SHA256) so the receiver can verify the sender.

**Technical Constraints:**
- Implementation of a "Dead Letter Queue" (DLQ) for webhooks that fail after 5 attempts.
- Rate limiting of outgoing webhooks to avoid being flagged as spam by receiving servers.

**User Story:** *As a 3rd party Auditor, I want my external system to be notified via a webhook whenever a new quarterly compliance report is finalized in Archway.*

---

### 3.3 PDF/CSV Report Generation (Priority: Critical | Status: In Review)
**Overview:** The generation of high-fidelity energy consumption and carbon credit reports. This is a **launch blocker**.

**Functional Requirements:**
- **Scheduled Delivery:** Users can schedule reports (Daily, Weekly, Monthly) via a Cron-like interface.
- **Export Formats:** High-resolution PDF for official government submission and CSV for data analysis.
- **Data Aggregation:** Reports must aggregate data from the `Telemetry` and `MeterReadings` tables, involving complex joins across millions of rows.
- **Asynchronous Processing:** Generation occurs in a background lambda; the user is notified via the Notification System (Feature 3.1) when the file is ready for download.

**Technical Constraints:**
- PDF generation must use a headless browser (e.g., Puppeteer) running in a serverless environment.
- Large CSVs must be streamed to S3/Blob storage to avoid memory overflow in the Lambda function.

**User Story:** *As a Compliance Officer, I need a scheduled monthly PDF report of total carbon offset to submit to the EPA, delivered to my email on the 1st of every month.*

---

### 3.4 SSO Integration (Priority: Medium | Status: Complete)
**Overview:** Centralized authentication for corporate and government entities using SAML and OIDC.

**Functional Requirements:**
- **SAML 2.0 Support:** Integration with Azure AD and Okta for government clients.
- **OIDC Support:** Standardized identity layer for smaller partners.
- **Just-In-Time (JIT) Provisioning:** Automatically create a user record in the `Users` table upon first successful SSO login.
- **Role Mapping:** Map SAML attributes (e.g., `memberOf`) to internal Archway roles (`ADMIN`, `VIEWER`, `OPERATOR`).

**Technical Constraints:**
- Must adhere to FedRAMP guidelines for session timeouts (max 12 hours) and mandatory MFA for administrative roles.
- Encryption of identity tokens at rest.

**User Story:** *As a Government Employee, I want to log into Archway using my existing agency credentials so that I don't have to manage another password.*

---

### 3.5 Advanced Search with Faceted Filtering (Priority: Low | Status: In Review)
**Overview:** A powerful search interface to find specific assets (wind turbines, solar panels) across global installations.

**Functional Requirements:**
- **Full-Text Indexing:** Search across asset names, descriptions, and technician notes.
- **Faceted Filtering:** Allow users to narrow results by "State," "Manufacturer," "Installation Date," and "Output Capacity."
- **Instant Search:** UI must provide "search-as-you-type" suggestions.

**Technical Constraints:**
- Implementation of PostgreSQL `tsvector` and `tsquery` for full-text search to avoid introducing a separate Elasticsearch cluster (reducing cost and complexity).
- Caching of common filter combinations via Redis to improve response times.

**User Story:** *As a Regional Manager, I want to search for all "Siemens" turbines in "Texas" that were installed between 2018 and 2020.*

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`.

### 4.1 Notification Endpoints
**POST `/notifications/send`**
- **Description:** Triggers a manual notification.
- **Request:** `{ "userId": "uuid", "channel": "sms", "message": "Grid Alert: Sector 7", "priority": "high" }`
- **Response:** `202 Accepted` | `{ "notificationId": "uuid", "status": "queued" }`

**GET `/notifications/preferences`**
- **Description:** Retrieves user's channel preferences.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK` | `{ "userId": "uuid", "preferences": { "email": true, "sms": false } }`

### 4.2 Webhook Endpoints
**POST `/webhooks/register`**
- **Description:** Registers a new third-party callback URL.
- **Request:** `{ "targetUrl": "https://api.client.com/webhook", "events": ["report.generated"] }`
- **Response:** `201 Created` | `{ "webhookId": "uuid", "secret": "whsec_..." }`

**DELETE `/webhooks/:id`**
- **Description:** Removes a webhook registration.
- **Response:** `204 No Content`

### 4.3 Report Endpoints
**POST `/reports/generate`**
- **Description:** Manually triggers a PDF/CSV report.
- **Request:** `{ "type": "carbon_offset", "format": "pdf", "dateRange": "2025-Q1" }`
- **Response:** `202 Accepted` | `{ "jobId": "job_123", "estimatedTime": "45s" }`

**GET `/reports/download/:jobId`**
- **Description:** Retrieves the generated file.
- **Response:** `302 Redirect` to signed S3 URL.

### 4.4 Search Endpoints
**GET `/search/assets`**
- **Description:** Faceted search for hardware assets.
- **Query Params:** `?q=siemens&state=TX&capacity=100MW`
- **Response:** `200 OK` | `{ "results": [...], "facets": { "states": ["TX", "CA"], "brands": ["Siemens", "GE"] } }`

**GET `/search/logs`**
- **Description:** Full-text search through system event logs.
- **Query Params:** `?q=critical error`
- **Response:** `200 OK` | `{ "logs": [...] }`

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 16 cluster. Relationships are managed via Prisma, though 30% of performance-critical paths use raw SQL.

### 5.1 Tables and Fields

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `Users` | `id (PK)`, `email`, `sso_id`, `role_id` | 1:1 with `UserProfiles` | Core user identity. |
| `UserProfiles` | `id (PK)`, `user_id (FK)`, `timezone`, `phone` | 1:1 with `Users` | Metadata and contact info. |
| `Roles` | `id (PK)`, `role_name`, `permissions` | 1:N with `Users` | RBAC definitions. |
| `Assets` | `id (PK)`, `name`, `type`, `location_id` | N:1 with `Locations` | Energy hardware (Turbines, etc). |
| `Locations` | `id (PK)`, `address`, `region`, `country` | 1:N with `Assets` | Geographic sites. |
| `Telemetry` | `id (PK)`, `asset_id (FK)`, `value`, `timestamp` | N:1 with `Assets` | High-frequency sensor data. |
| `Notifications`| `id (PK)`, `user_id (FK)`, `content`, `channel`| N:1 with `Users` | History of alerts sent. |
| `WebhookConfigs`| `id (PK)`, `url`, `secret`, `user_id (FK)` | N:1 with `Users` | Third-party integration settings. |
| `Reports` | `id (PK)`, `user_id (FK)`, `status`, `file_url` | N:1 with `Users` | Metadata for generated PDFs/CSVs. |
| `AuditLogs` | `id (PK)`, `action`, `userId (FK)`, `timestamp` | N:1 with `Users` | FedRAMP compliance log. |

### 5.2 Schema Constraints
- **Telemetry Table:** Due to the volume of data, the `Telemetry` table is partitioned by month. Raw SQL is used for all aggregations to avoid Prisma's overhead.
- **Indexing:** B-Tree indexes on `userId` across all tables; GIN index on `Assets.name` for full-text search.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We maintain three distinct environments to ensure stability and compliance.

**1. Development (Dev)**
- **Purpose:** Feature iteration and unit testing.
- **Deployment:** Automatic deployments via GitHub Actions on push to `develop` branch.
- **Database:** Shared development DB with anonymized data.

**2. Staging (Staging)**
- **Purpose:** Integration testing, UX review (Tala Moreau), and Pre-Audit checks.
- **Deployment:** Manual trigger by Tech Lead (Kenji Oduya).
- **Database:** Mirror of production schema; sanitized data.

**3. Production (Prod)**
- **Purpose:** Customer-facing live environment.
- **Deployment:** **Manual deployment by a single DevOps person.** (Note: This is a critical risk—Bus Factor of 1).
- **Database:** FedRAMP compliant, encrypted at rest, multi-region failover enabled.

### 6.2 Infrastructure Components
- **Compute:** Vercel Serverless Functions (Node.js runtime).
- **Storage:** AWS S3 (FedRAMP region) for PDF/CSV storage.
- **Caching:** Vercel Edge Config for global flag management.
- **CI/CD:** GitHub Actions for linting and testing; Vercel for deployment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** Jest and Vitest.
- **Scope:** Logic-heavy utility functions, SAML attribute mapping, and notification payload builders.
- **Requirement:** Minimum 80% code coverage for all new microservices.

### 7.2 Integration Testing
- **Tooling:** Supertest and Prisma Mock.
- **Scope:** Validating the flow from the API Gateway $\rightarrow$ Service $\rightarrow$ Database.
- **Focus:** Ensuring that the "Raw SQL" queries do not break when the Prisma schema is migrated.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright.
- **Scope:** Critical user journeys:
    1. SSO Login $\rightarrow$ Dashboard.
    2. Report Request $\rightarrow$ Notification Receipt $\rightarrow$ File Download.
    3. Search $\rightarrow$ Filter Asset $\rightarrow$ View Telemetry.

### 7.4 Security Testing
- **FedRAMP Audit:** Monthly vulnerability scans and penetration testing.
- **Static Analysis:** Snyk integration in GitHub Actions to catch vulnerable NPM packages.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lacks experience with Next.js/Prisma/Vercel stack. | High | High | Escalate to steering committee for additional training budget/external consultants. |
| R-02 | Project sponsor is rotating out of their role shortly. | Medium | High | Raise as a critical blocker in the next board meeting to secure a successor. |
| R-03 | "Bus Factor of 1" for deployments (Single DevOps person). | High | Critical | Cross-train Xavi Park on deployment scripts; document the process in the internal Wiki. |
| R-04 | Raw SQL (30%) makes migrations dangerous. | High | Medium | Implement a "Migration Validation" suite that runs raw SQL queries against a staging DB before prod deployment. |
| R-05 | Dependency on external team (3 weeks behind). | High | Medium | Daily syncs with the external team; pivot development to non-dependent features (e.g., SSO). |

**Impact Matrix:**
- **Critical:** Project failure or total data loss.
- **High:** Significant delay in milestones or security breach.
- **Medium:** Feature degradation or minor delay.
- **Low:** Cosmetic issues or minor performance lag.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases of Execution
- **Phase 1: Foundation (Now – June 2026):** Focus on SSO, API Gateway setup, and Security Audit.
- **Phase 2: Core Utility (June 2026 – August 2026):** Implementation of Reporting and Notification systems.
- **Phase 3: Optimization (August 2026 – October 2026):** Search implementation, performance tuning, and Alpha testing.

### 9.2 Milestone Schedule

| Milestone | Target Date | Dependency | Deliverable |
| :--- | :--- | :--- | :--- |
| **M1: Security Audit Passed** | 2026-06-15 | SSO Completion | FedRAMP Authorization Certification |
| **M2: Internal Alpha Release**| 2026-08-15 | Reporting System | Functional app for internal Clearpoint staff |
| **M3: MVP Feature-Complete** | 2026-10-15 | Notification System | Production-ready build for select clients |

---

## 10. MEETING NOTES (ARCHIVE)

*Note: These are excerpts from the 200-page unsearchable shared document.*

### Meeting 1: Stack Alignment (2025-11-05)
**Attendees:** Kenji, Xavi, Sanjay, Tala.
- **Discussion:** Xavi raised concerns about using Prisma for the telemetry data, noting that `prisma.telemetry.findMany()` is too slow for 100k+ records.
- **Decision:** Kenji approved the use of Raw SQL for the Telemetry service. 
- **Action Item:** Sanjay to create a "Raw SQL Guide" so other developers don't accidentally break the schema during migrations.
- **Tension Note:** The team is still forming; Sanjay was hesitant to speak up, but Kenji encouraged him. Trust is building.

### Meeting 2: The "Sponsor Crisis" (2025-12-12)
**Attendees:** Kenji, Project Sponsor (Rotating).
- **Discussion:** Sponsor mentioned they are moving to a different division in Q1. Kenji expressed concern about funding stability for the tranches.
- **Decision:** The current sponsor will attempt to lock in the budget for M1 and M2 before leaving, but M3 is "at risk."
- **Action Item:** Kenji to prepare a slide deck for the board meeting to justify the "variable budget" model.

### Meeting 3: The Blockage Sync (2026-01-20)
**Attendees:** Kenji, Xavi, External Team Lead (Mark).
- **Discussion:** The external team providing the Energy Telemetry API is now 3 weeks behind. Xavi cannot test the Reporting tool without the API.
- **Decision:** Xavi will build a "Mock API" using JSON Server to simulate the telemetry data so development can continue.
- **Action Item:** Mark to provide a firm delivery date by Friday.

---

## 11. BUDGET BREAKDOWN

Budget is released in tranches based on the completion of the three primary milestones.

### 11.1 Personnel Costs (Annualized)
| Role | Count | Avg. Rate | Total |
| :--- | :--- | :--- | :--- |
| Tech Lead (Kenji) | 1 | $160k | $160,000 |
| Senior Backend (Xavi) | 1 | $140k | $140,000 |
| UX Researcher (Tala) | 1 | $110k | $110,000 |
| Junior Developer (Sanjay)| 1 | $75k | $75,000 |
| Distributed Engineers | 11 | $110k (avg) | $1,210,000 |
| **Total Personnel** | **15** | | **$1,695,000** |

### 11.2 Infrastructure & Tooling (Monthly)
| Item | Cost | Note |
| :--- | :--- | :--- |
| Vercel Enterprise | $4,000 | Includes FedRAMP compliance options |
| Neon Postgres | $1,200 | Autoscale storage |
| Auth0 (Enterprise) | $2,500 | SAML/OIDC support |
| AWS S3/Cloudfront | $800 | Report storage and delivery |
| SendGrid/Twilio | $600 | Notification volume |
| **Total Monthly** | **$9,100** | **($109,200 / year)** |

### 11.3 Contingency & Miscellaneous
- **Training Fund:** $50,000 (Specifically allocated for the "Lack of Experience" risk mitigation).
- **Audit Fees:** $120,000 (External FedRAMP certification costs).
- **Emergency Buffer:** $100,000 (To cover potential delays from the external team).

**Total Estimated Project Budget (Year 1): ~$2,034,200**

---

## 12. APPENDICES

### Appendix A: Raw SQL Performance Patterns
Because 30% of the project bypasses the ORM, the following patterns are mandatory to prevent SQL injection and ensure performance:
1. **Parameterized Queries:** All raw SQL must use `$queryRaw` with template literals in Prisma.
2. **Indexing Strategy:** Every raw query must be checked against the `EXPLAIN ANALYZE` plan to ensure it uses an existing index.
3. **Transaction Isolation:** Raw SQL updates to the `Users` and `AuditLogs` tables must use `SERIALIZABLE` isolation levels to prevent race conditions during SSO provisioning.

### Appendix B: FedRAMP Compliance Checklist
The following technical controls must be verified before Milestone 1 (2026-06-15):
- **Encryption in Transit:** All endpoints must enforce TLS 1.2+.
- **Encryption at Rest:** AES-256 encryption for the PostgreSQL cluster.
- **Access Control:** Multi-factor authentication (MFA) required for all users with `ADMIN` roles.
- **Audit Logging:** Every `POST`, `PUT`, and `DELETE` request must generate a record in the `AuditLogs` table including the timestamp, actor ID, and the specific resource modified.
- **Data Residency:** All data must be stored in AWS GovCloud regions.