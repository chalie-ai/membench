Due to the extreme length requirement (6,000–8,000 words), this document is structured as a comprehensive, industrial-grade Project Specification Document (PSD). It expands every provided detail into granular technical requirements, architectural blueprints, and operational workflows.

***

# PROJECT SPECIFICATION: ZENITH
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Owner:** Anouk Gupta, VP of Product  
**Company:** Stratos Systems  
**Classification:** Internal R&D (Confidential)  
**Last Updated:** October 24, 2024

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Zenith" is a strategic moonshot initiative by Stratos Systems designed to revolutionize the agricultural technology (AgTech) landscape. While the current market for AgTech is dominated by fragmented data silos—where soil telemetry, crop yield projections, and supply chain logistics exist in separate applications—Zenith aims to provide a unified, real-time collaboration tool. This platform is not merely a document editor or a chat tool, but a geospatial and data-driven workspace where agronomists, farm managers, and corporate stakeholders can collaborate in real-time on live data streams.

The objective is to create a "Single Pane of Glass" for agricultural operations. This allows for the immediate synchronization of field observations with corporate strategy, reducing the latency between "sensing" a problem in the field and "executing" a solution via a centralized command structure.

### 1.2 Business Justification
The AgTech industry is currently undergoing a digital transformation. Stratos Systems has a strong foothold in telemetry hardware, but lacks a cohesive software layer for human collaboration. Zenith bridges this gap. By integrating real-time collaboration, Stratos Systems can transition from a hardware vendor to a Platform-as-a-Service (PaaS) provider. 

The "moonshot" nature of this project stems from the uncertainty of the ROI; the agricultural sector is notoriously slow to adopt new software paradigms. However, the executive sponsorship is robust, recognizing that if Zenith succeeds, it creates a "lock-in" effect where competitors cannot displace Stratos hardware because the collaboration and data history are embedded in the Zenith ecosystem.

### 1.3 ROI Projection and Success Metrics
The project is funded with a modest but focused budget of $400,000. Because this is an R&D effort, the ROI is measured not by immediate profitability but by market penetration and strategic positioning.

**Primary Success Metrics:**
1.  **Direct Revenue:** The target is $500,000 in new attributed revenue within the first 12 months post-launch. This will be achieved through a tiered subscription model:
    *   *Basic:* $200/month per farm.
    *   *Enterprise:* Custom pricing for corporate conglomerates.
2.  **Technical Performance:** To ensure a seamless "real-time" feel, the API response time (p95) must remain under 200ms at peak load (defined as 10,000 concurrent WebSocket connections).
3.  **User Retention:** A target of 60% Weekly Active User (WAU) retention among the initial beta cohort.

### 1.4 Strategic Alignment
Zenith aligns with the Stratos Systems 2025 goal of "Data Democratization." By moving collaboration from email threads and fragmented PDFs into a real-time environment, Zenith reduces operational waste and increases the speed of decision-making in the field.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Zenith utilizes a "Clean Monolith" architecture. While the industry trend is toward microservices, the small team size (4 members) makes a distributed system an operational liability. Instead, Zenith uses a modular monolith approach where boundaries are strictly enforced through TypeScript modules and directory structures, allowing for a future migration to microservices if the product scales.

**The Stack:**
*   **Frontend:** Next.js 14 (App Router) using TypeScript for type safety.
*   **State Management:** Zustand for global client state and React Query for server-state synchronization.
*   **Backend:** Next.js API routes and Server Actions, interfacing with a PostgreSQL database.
*   **ORM:** Prisma (used for type-safe database access and migrations).
*   **Database:** PostgreSQL 15 (managed via AWS RDS).
*   **Deployment:** Vercel for the frontend/API edge, with rolling deployments managed via GitLab CI.
*   **Containerization:** Kubernetes (K8s) for the heavy-lift backend processes (virus scanning, webhook dispatchers).

### 2.2 ASCII Architectural Diagram

```text
[ CLIENT LAYER ]               [ API & EDGE LAYER ]           [ DATA & SERVICE LAYER ]
+-------------------+          +---------------------+        +-----------------------+
|  Web Browser       | <------> |  Vercel Edge Network | <----> |  PostgreSQL Database   |
|  (Next.js/TS)     |          |  (API Gateway/Auth)  |        |  (Prisma ORM)          |
+---------^---------+          +----------^----------+        +-----------^-------------+
         |                                |                               |
         |                        +-------v-------+               +-------v-------+
         |                        | GitLab CI/CD  |               | K8s Cluster    |
         |                        | (Rolling Dep) |               | (Worker Nodes) |
         |                        +-------^-------+               +-------^-------+
         |                                |                               |
         +-------------------------------|-------------------------------+
                                         |
                             [ EXTERNAL INTEGRATIONS ]
                             | - Third Party Ag-APIs  |
                             | - S3 Bucket (Storage)   |
                             | - Virus Scanning API   |
                             +-----------------------+
```

### 2.3 Module Boundaries
To prevent the "Big Ball of Mud" pattern, the monolith is split into the following domains:
1.  **`@zenith/auth`**: Handles session management, JWTs, and identity.
2.  **`@zenith/collaboration`**: Manages real-time state synchronization and WebSocket events.
3.  **`@zenith/integration`**: Manages the webhook framework and external API connectors.
4.  **`@zenith/storage`**: Handles file uploads, CDN distribution, and virus scanning.
5.  **`@zenith/i18n`**: Manages translation keys and locale-specific formatting.

### 2.4 Security Posture
As an internal R&D project, Zenith does not currently require SOC2 or HIPAA compliance. Security is managed via internal audits conducted by Petra Oduya. The security focus is on:
*   **JWT-based Authentication:** Secure cookies with `HttpOnly` and `SameSite=Strict` flags.
*   **Input Validation:** Zod for strict schema validation on all API endpoints.
*   **Network:** Private VPC for the PostgreSQL instance, accessible only via the K8s cluster and Vercel.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** Not Started | **Owner:** Isadora Stein

**Overview:**
Agricultural data often involves large imagery (satellite maps, drone footage) and PDF reports. This feature provides a secure pipeline for uploading these files, ensuring they are clean of malware before being distributed to other collaborators via a Global CDN.

**Technical Requirements:**
*   **Upload Pipeline:** The frontend will use "Presigned URLs" to upload files directly to an S3-compatible bucket. This prevents the Next.js API from becoming a bottleneck for large binary transfers.
*   **Virus Scanning:** Once a file is uploaded, an S3 Trigger will fire a Lambda function (or K8s Job) that sends the file hash to a virus scanning service (e.g., ClamAV or an external API). 
*   **State Management:** Files will be marked as `PENDING_SCAN` in the database. They will remain inaccessible to other users until the scan returns a `CLEAN` status.
*   **CDN Distribution:** Upon successful scanning, the file is mirrored to a CloudFront CDN. This ensures that a user in Brazil and a user in the US can both access high-resolution satellite imagery with minimal latency.

**User Workflow:**
1. User drags a `.tif` file into the Zenith workspace.
2. File uploads to S3; the UI shows a "Scanning for threats..." progress bar.
3. Backend validates the scan results.
4. File is marked as "Available," and the CDN link is generated for all project collaborators.

### 3.2 Webhook Integration Framework for Third-Party Tools
**Priority:** Medium | **Status:** Complete | **Owner:** Eshan Gupta

**Overview:**
To become an ecosystem player, Zenith must communicate with other AgTech tools (e.g., John Deere Operations Center, Climate FieldView). This framework allows Zenith to push real-time events to external URLs.

**Technical Requirements:**
*   **Event Registry:** A database table that maps specific Zenith events (e.g., `FIELD_UPDATE_CREATED`, `USER_ANNOTATION_ADDED`) to user-defined destination URLs.
*   **Payload Structure:** All webhooks follow a standardized JSON schema including `event_id`, `timestamp`, `payload`, and a `signature` for security.
*   **Delivery Mechanism:** A Redis-backed queue (BullMQ) handles the dispatching. If a third-party endpoint is down, Zenith implements an exponential backoff retry strategy (5 attempts over 24 hours).
*   **Security:** HMAC signatures are included in the header (`X-Zenith-Signature`) so the receiving party can verify the authenticity of the request.

**Current State:** 
The framework is fully operational. It currently supports 15 distinct event types and has been tested against Mockbin and internal Stratos endpoints.

### 3.3 A/B Testing Framework (Feature Flag Integrated)
**Priority:** Low | **Status:** In Progress | **Owner:** Anouk Gupta / Isadora Stein

**Overview:**
To optimize the UX for non-technical farm users, Zenith needs to test different interface paradigms. Instead of a standalone A/B tool, this is baked into the existing feature flag system.

**Technical Requirements:**
*   **Flag Logic:** The system uses a "Bucket" approach. A user's ID is hashed, and the modulo of that hash determines which variant (A or B) they see.
*   **Persistence:** The assigned variant is stored in the user's profile to ensure a consistent experience across sessions.
*   **Telemetry:** Every action taken within a "flagged" feature is tagged with the variant ID in the analytics pipeline.
*   **Control Panel:** A simple admin UI where Anouk can shift the percentage of traffic from Variant A to Variant B (e.g., 90/10 split).

**Expected Outcome:**
This will allow the team to test if a "Map-First" navigation is more intuitive than a "List-First" navigation for regional managers.

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Review | **Owner:** Eshan Gupta

**Overview:**
For corporate clients, Zenith must offer a way to programmatically extract collaboration data and push field updates without using the UI.

**Technical Requirements:**
*   **Versioning:** The API uses URI versioning (e.g., `/api/v1/...`). When breaking changes are introduced, `/api/v2/` is deployed, and v1 is deprecated after a 6-month window.
*   **Sandbox Environment:** A completely isolated database instance (`zenith-sandbox-db`) where developers can test API calls without affecting production data.
*   **Authentication:** API Key-based authentication using `Bearer` tokens. Keys are hashed in the database using bcrypt.
*   **Rate Limiting:** To prevent abuse (and solve current blocker issues), a tiered rate limit is applied:
    *   Sandbox: 100 requests/hour.
    *   Production: 5,000 requests/hour.

**Documentation:**
The API is documented using OpenAPI 3.0 (Swagger), providing an interactive playground for developers.

### 3.5 Localization and Internationalization (i18n) for 12 Languages
**Priority:** High | **Status:** In Design | **Owner:** Isadora Stein / Petra Oduya

**Overview:**
Agriculture is global. Zenith must support 12 languages, including English, Spanish, Portuguese, French, Mandarin, and Hindi, to cater to the primary agricultural hubs.

**Technical Requirements:**
*   **Library:** `next-intl` is used for server-side and client-side translation.
*   **Translation Management:** JSON translation files are stored in GitLab, but the team is evaluating a Headless CMS (like Phrase or Lokalise) for non-technical translators to edit strings.
*   **Dynamic Routing:** Locale is handled via the URL path (e.g., `zenith.app/es/dashboard`).
*   **Formatting:** Implementation of the `Intl` JavaScript API for locale-specific date, number, and currency formatting (crucial for crop pricing and soil metrics).

**Supported Languages:**
English (US/UK), Spanish (MX/ES), Portuguese (BR), French, Mandarin (CN), Hindi, German, Vietnamese, Thai, Indonesian, Arabic, and Japanese.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are based on `https://api.zenith.stratos.com/v1`.

### 4.1 Collaboration Endpoints

#### `POST /collaboration/session`
Creates a new real-time session for a specific field map.
*   **Request:** 
    ```json
    { "field_id": "field_882", "user_id": "user_01", "session_name": "Spring Planting 2025" }
    ```
*   **Response (201 Created):** 
    ```json
    { "session_id": "sess_99a12", "websocket_url": "wss://ws.zenith.stratos.com/socket", "token": "jwt_token_here" }
    ```

#### `GET /collaboration/events/{session_id}`
Retrieves a history of all changes made during a session.
*   **Response (200 OK):** 
    ```json
    { "events": [ { "id": "ev_1", "type": "ANNOTATION_ADD", "user": "Petra", "data": { "lat": 45.1, "lng": -93.2, "text": "Pest sighting" } } ] }
    ```

### 4.2 File Management Endpoints

#### `POST /files/upload-url`
Requests a presigned S3 URL for a secure upload.
*   **Request:** 
    ```json
    { "filename": "drone_map_v1.tif", "content_type": "image/tiff", "size": 10485760 }
    ```
*   **Response (200 OK):** 
    ```json
    { "upload_url": "https://s3.amazon.aws.com/bucket/...", "file_id": "file_5521" }
    ```

#### `GET /files/{file_id}/status`
Checks the virus scan status of a file.
*   **Response (200 OK):** 
    ```json
    { "file_id": "file_5521", "status": "CLEAN", "cdn_url": "https://cdn.zenith.stratos.com/file_5521" }
    ```

### 4.3 Integration & Webhook Endpoints

#### `POST /webhooks/subscribe`
Registers a third-party URL for specific events.
*   **Request:** 
    ```json
    { "target_url": "https://client-api.com/webhook", "events": ["FIELD_UPDATE_CREATED"] }
    ```
*   **Response (201 Created):** 
    ```json
    { "subscription_id": "sub_772", "status": "active" }
    ```

#### `DELETE /webhooks/unsubscribe/{subscription_id}`
Removes a webhook registration.
*   **Response (204 No Content)**

### 4.4 Admin & User Endpoints

#### `GET /users/me`
Returns the profile and current feature flags for the authenticated user.
*   **Response (200 OK):** 
    ```json
    { "id": "user_01", "name": "Anouk", "flags": { "new_map_ui": "variant_b" }, "locale": "en-US" }
    ```

#### `PATCH /users/settings`
Updates user preferences, including language and notification settings.
*   **Request:** 
    ```json
    { "locale": "pt-BR", "notifications": { "email": true, "push": false } }
    ```
*   **Response (200 OK):** 
    ```json
    { "status": "updated" }
    ```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15 instance managed by Prisma.

### 5.1 Table Definitions

1.  **`User`**
    *   `id` (UUID, PK)
    *   `email` (String, Unique)
    *   `password_hash` (String)
    *   `full_name` (String)
    *   `locale` (String, default: 'en-US')
    *   `created_at` (Timestamp)

2.  **`Organization`** (Represents a farming conglomerate or individual farm)
    *   `id` (UUID, PK)
    *   `org_name` (String)
    *   `billing_plan` (Enum: BASIC, ENTERPRISE)
    *   `created_at` (Timestamp)

3.  **`UserOrganization`** (Many-to-Many join table)
    *   `user_id` (UUID, FK)
    *   `org_id` (UUID, FK)
    *   `role` (Enum: OWNER, MANAGER, VIEWER)

4.  **`Field`** (The physical land area being collaborated on)
    *   `id` (UUID, PK)
    *   `org_id` (UUID, FK)
    *   `name` (String)
    *   `boundary_geojson` (JSONB)
    *   `last_updated` (Timestamp)

5.  **`CollaborationSession`**
    *   `id` (UUID, PK)
    *   `field_id` (UUID, FK)
    *   `started_at` (Timestamp)
    *   `ended_at` (Timestamp, Nullable)

6.  **`EventLog`** (Stores every action for real-time replay)
    *   `id` (UUID, PK)
    *   `session_id` (UUID, FK)
    *   `user_id` (UUID, FK)
    *   `event_type` (String)
    *   `payload` (JSONB)
    *   `created_at` (Timestamp)

7.  **`FileMetadata`**
    *   `id` (UUID, PK)
    *   `uploader_id` (UUID, FK)
    *   `s3_key` (String)
    *   `status` (Enum: PENDING_SCAN, CLEAN, INFECTED)
    *   `mime_type` (String)
    *   `size` (BigInt)

8.  **`WebhookSubscription`**
    *   `id` (UUID, PK)
    *   `org_id` (UUID, FK)
    *   `target_url` (String)
    *   `secret` (String)
    *   `active` (Boolean)

9.  **`FeatureFlag`**
    *   `id` (UUID, PK)
    *   `flag_key` (String, Unique)
    *   `description` (Text)
    *   `is_enabled` (Boolean)

10. **`UserFlagAssignment`**
    *   `user_id` (UUID, FK)
    *   `flag_id` (UUID, FK)
    *   `variant` (String) (e.g., "A", "B")

### 5.2 Relationships
*   `User` $\leftrightarrow$ `Organization`: Many-to-Many via `UserOrganization`.
*   `Organization` $\rightarrow$ `Field`: One-to-Many.
*   `Field` $\rightarrow$ `CollaborationSession`: One-to-Many.
*   `CollaborationSession` $\rightarrow$ `EventLog`: One-to-Many.
*   `User` $\rightarrow$ `FileMetadata`: One-to-Many.
*   `Organization` $\rightarrow$ `WebhookSubscription`: One-to-Many.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Zenith utilizes three distinct environments to ensure stability.

#### 6.1.1 Development (Dev)
*   **Purpose:** Feature experimentation and unit testing.
*   **Hosting:** Vercel Preview Deployments.
*   **Database:** Local Dockerized PostgreSQL and a shared `dev` RDS instance.
*   **CI/CD:** Every commit to a feature branch triggers a preview deployment.

#### 6.1.2 Staging (Staging)
*   **Purpose:** Pre-production validation and QA. This is where Petra Oduya performs regression testing.
*   **Hosting:** Dedicated Kubernetes Namespace (`zenith-staging`).
*   **Database:** A sanitized clone of the production database.
*   **CI/CD:** Merges to the `develop` branch trigger automatic deployment to staging.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live user traffic.
*   **Hosting:** Vercel (Frontend/Edge) + Kubernetes (Backend Workers).
*   **Deployment Strategy:** Rolling Deployments. New pods are spun up and health-checked before old pods are terminated to ensure zero-downtime.
*   **Database:** Multi-AZ AWS RDS PostgreSQL with automated snapshots every 6 hours.

### 6.2 Infrastructure Components
*   **GitLab CI:** The backbone of the pipeline. It handles linting, type-checking, and the deployment triggers.
*   **Vercel:** Chosen for its seamless integration with Next.js and global edge network, which is critical for the localization and API response time goals.
*   **Kubernetes (K8s):** Used for non-HTTP tasks, specifically the BullMQ worker processes that handle webhook deliveries and the virus scanning logic.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tooling:** Vitest.
*   **Focus:** Pure functions, utility helpers, and the `@zenith/auth` logic.
*   **Requirement:** All new PRs must maintain a minimum of 80% code coverage on business logic.

### 7.2 Integration Testing
*   **Tooling:** Jest + Prisma Mock.
*   **Focus:** API endpoint validation. Testing the flow from the API route $\rightarrow$ Prisma $\rightarrow$ Database.
*   **Scenario:** A test will simulate a file upload request and verify that the `FileMetadata` entry is created with the `PENDING_SCAN` status.

### 7.3 End-to-End (E2E) Testing
*   **Tooling:** Playwright.
*   **Focus:** Critical user journeys (The "Happy Path").
*   **Core Flows:**
    1.  User Login $\rightarrow$ Field Selection $\rightarrow$ Real-time Annotation $\rightarrow$ Logout.
    2.  File Upload $\rightarrow$ Wait for Scan $\rightarrow$ CDN Access.
    3.  Webhook Setup $\rightarrow$ Trigger Event $\rightarrow$ Verify External Request.

### 7.4 QA Process
Petra Oduya leads the QA effort. Every feature must pass a "Bug Bash" in the staging environment before being promoted to production. Since the team is small, Petra utilizes a "Risk-Based Testing" approach, focusing heavily on the high-priority API and localization features.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Key Architect is leaving in 3 months | High | High | Accept risk. Monitor weekly. Eshan is being cross-trained on architecture to bridge the gap. |
| **R-02** | Project Sponsor rotating out of role | Medium | High | De-scope low-priority features (like A/B testing) if executive support wavers before Milestone 3. |
| **R-03** | Third-party API rate limits (Blocker) | High | Medium | Implement a local caching layer and request queuing to reduce external calls. |
| **R-04** | Technical Debt (God Class) | High | Medium | Incremental refactoring. Break the 3,000-line class into `AuthService`, `LogService`, and `EmailService` over the next 2 sprints. |
| **R-05** | Localization complexity (12 languages) | Medium | Medium | Use a professional translation agency for the final Polish; rely on AI-assisted translation for early design. |

---

## 9. TIMELINE

### 9.1 Project Phases

#### Phase 1: Foundation & Core API (Now $\rightarrow$ 2025-03-01)
*   **Focus:** API Versioning, Sandbox environment, and Database schema finalization.
*   **Dependencies:** Completion of the API review process.
*   **Key Deliverable:** Functional Customer API (v1).

#### Phase 2: Real-time & Global Reach (2025-03-02 $\rightarrow$ 2025-05-15)
*   **Focus:** i18n implementation for 12 languages and real-time session logic.
*   **Dependencies:** Successful API stabilization.
*   **Key Deliverable:** **Milestone 1 (MVP Feature-Complete).**

#### Phase 3: Hardening & Security (2025-05-16 $\rightarrow$ 2025-07-15)
*   **Focus:** File upload pipeline, virus scanning, and CDN optimization.
*   **Dependencies:** Infrastructure scaling on K8s.
*   **Key Deliverable:** **Milestone 2 (Post-launch Stability Confirmed).**

#### Phase 4: Polish & Launch (2025-07-16 $\rightarrow$ 2025-09-15)
*   **Focus:** A/B testing framework, final QA regression, and marketing alignment.
*   **Dependencies:** User feedback from Beta.
*   **Key Deliverable:** **Milestone 3 (Production Launch).**

### 9.2 Gantt Chart Representation (Conceptual)
`[ API/Sandbox ] >>> [ i18n/Realtime ] >>> [ Uploads/Scan ] >>> [ A/B Testing ]`
`S-Now -------- 2025-03 -------- 2025-05 -------- 2025-07 -------- 2025-09`

---

## 10. MEETING NOTES (Slack-Sourced Decisions)

As per team protocol, formal meeting notes are not kept; decisions live in Slack. The following are summaries of critical decision threads.

### 10.1 Thread: `#zenith-dev` — Topic: The "God Class" Problem
**Date:** November 12, 2024
*   **Eshan:** "I'm spending 2 hours just trying to find where the email trigger is in the `SystemManager` class. It's 3,000 lines long. Can we rewrite it?"
*   **Anouk:** "We don't have time for a full rewrite, but we can't let it block us. Eshan, start extracting the email logic into a separate service. Do it incrementally."
*   **Petra:** "Agree. If we don't split it, the unit tests are becoming impossible to maintain."
*   **Decision:** Team agreed to a "strangler pattern" approach to break down the God class over the next 3 sprints.

### 10.2 Thread: `#zenith-prod` — Topic: API Rate Limiting Blocker
**Date:** December 5, 2024
*   **Isadora:** "The third-party Ag-API is capping us at 10 requests per second in the sandbox. We can't run the E2E tests for the collaboration sync."
*   **Anouk:** "I'll reach out to the vendor for a higher limit, but for now, let's implement a mock server for the E2E pipeline."
*   **Eshan:** "I can set up a Prism mock server by tomorrow."
*   **Decision:** Implement a mock server for testing to bypass external rate limits; Anouk to negotiate higher limits for production.

### 10.3 Thread: `#zenith-design` — Topic: Localization Strategy
**Date:** January 15, 2025
*   **Petra:** "Adding 12 languages is going to break the UI layout, especially for German and Arabic (RTL)."
*   **Isadora:** "I'll use Flexbox/Grid with logical properties (`margin-inline-start` instead of `margin-left`) to handle RTL automatically."
*   **Anouk:** "Prioritize Spanish and Portuguese first, as those are our biggest growth markets in AgTech."
*   **Decision:** Adopt `next-intl` and prioritize a "Core 3" (English, Spanish, Portuguese) before rolling out the remaining 9.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$400,000**

### 11.1 Personnel Costs ($310,000)
*   **Anouk Gupta (VP Product/Lead):** $80,000 (Partial allocation)
*   **Isadora Stein (Frontend Lead):** $90,000
*   **Petra Oduya (QA Lead):** $70,000
*   **Eshan Gupta (Junior Dev):** $70,000

### 11.2 Infrastructure & Tools ($50,000)
*   **Vercel Enterprise Plan:** $12,000/year
*   **AWS RDS (PostgreSQL) & S3:** $15,000/year
*   **Kubernetes Cluster Hosting:** $12,000/year
*   **Virus Scanning API Credits:** $5,000/year
*   **GitLab Premium:** $6,000/year

### 11.3 Third-Party Services ($20,000)
*   **Localization Agency (Final Review):** $15,000
*   **Ag-API Enterprise Licenses:** $5,000

### 11.4 Contingency Fund ($20,000)
*   Reserved for unexpected scaling costs or emergency contractor hiring if the key architect's departure creates a critical gap.

---

## 12. APPENDICES

### Appendix A: Technical Debt Log
The `SystemManager.ts` class is the primary source of technical debt. It currently handles:
1.  **Authentication:** Session validation and token refreshing.
2.  **Logging:** Writing to the PostgreSQL `EventLog`.
3.  **Email:** Sending notifications via SendGrid.
4.  **Database:** Direct Prisma calls for user updates.

**Refactoring Plan:**
*   Sprint 12: Extract `EmailService.ts`.
*   Sprint 13: Extract `LoggerService.ts`.
*   Sprint 14: Extract `AuthService.ts`.

### Appendix B: CDN Distribution Logic
To minimize latency for high-resolution Ag-imagery, Zenith uses a "Pull-through" cache strategy.
1.  **Origin:** S3 Bucket in `us-east-1`.
2.  **Edge:** CloudFront distribution with 12 edge locations globally.
3.  **Cache Policy:**
    *   `Cache-Control: max-age=31536000` for scanned imagery (files are immutable).
    *   `Cache-Control: no-cache` for user-specific session data.
4.  **Invalidation:** When a file is updated, the system triggers a CloudFront Invalidation request for that specific object path to ensure users see the latest version.