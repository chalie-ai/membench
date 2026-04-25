# PROJECT SPECIFICATION DOCUMENT: PROJECT INGOT
**Version:** 1.0.4  
**Status:** Active / Baseline  
**Date:** October 24, 2023  
**Project Lead:** Beau Park (CTO)  
**Company:** Oakmount Group  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Ingot represents a strategic pivot for Oakmount Group, moving from general services into a specialized healthcare supply chain management (SCM) vertical. The healthcare industry is currently experiencing significant fragmentation in procurement and distribution, leading to critical shortages of medical supplies and inefficient inventory management. Ingot is designed to bridge this gap by providing a high-integrity, audit-ready platform that ensures the provenance, transport, and delivery of medical grade supplies.

The catalyst for this project is a high-value enterprise client—a regional healthcare consortium—that has expressed a willingness to commit to a $2M annual recurring revenue (ARR) contract upon successful delivery of the system. This provides an immediate and guaranteed market fit, removing the traditional risk associated with new product development. By building a system tailored to the needs of this anchor client, Oakmount Group can establish a blueprint for a scalable SaaS product that can be marketed to other healthcare providers globally.

### 1.2 ROI Projection
The financial outlook for Project Ingot is highly favorable. With a total development budget of $1.5M, the project is positioned to reach break-even within the first quarter of production launch.

*   **Immediate Revenue:** $2M ARR from the anchor client.
*   **Cost of Development:** $1.5M (CapEx).
*   **Projected Year 1 Net:** $500,000 profit, assuming the anchor client onboarded on schedule.
*   **Long-term Scaling:** By leveraging the infrastructure built for the anchor client, Oakmount Group anticipates acquiring three additional mid-sized clients in Year 2, projecting an ARR increase to $5M.

The ROI is not merely financial; the technical assets created (specifically the event-sourced audit trail) provide a competitive moat in the healthcare sector where regulatory compliance and data integrity are paramount.

### 1.3 Strategic Objectives
The primary objective is to deliver a robust SCM system that eliminates manual tracking and reduces procurement errors. Because the system handles critical healthcare logistics, "zero-fail" reliability is the baseline. The project aims to achieve a 80% feature adoption rate among pilot users, ensuring that the software is intuitive enough to replace legacy spreadsheets and manual processes.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Project Ingot employs a modern, type-safe stack designed for rapid iteration and high reliability. The core is built on **TypeScript** and **Next.js**, providing a unified language across the frontend and backend. Data persistence is handled by **PostgreSQL**, interfaced through **Prisma ORM** for type-safe database queries.

### 2.2 Architectural Pattern: CQRS and Event Sourcing
Due to the audit-critical nature of healthcare supply chains, Ingot does not use a simple CRUD (Create, Read, Update, Delete) pattern for its core domains. Instead, it implements **Command Query Responsibility Segregation (CQRS)** with **Event Sourcing**.

*   **Command Side:** Handles the intent to change state. Every action (e.g., `ShipOrder`, `UpdateInventory`) is recorded as an immutable event in an `EventStore` table.
*   **Query Side:** Projections of these events are materialized into read-optimized tables. If an audit is required, the system can "replay" events from the `EventStore` to reconstruct the state of any entity at any point in time.

### 2.3 ASCII Architecture Diagram
```text
[ Client Browser ] <--> [ Vercel Edge Network ]
                                |
                                v
                        [ Next.js Application ]
                        /        |            \
          (Command API)   (Query API)   (File Upload API)
               |                 |                |
               v                 v                v
        [ Event Store ] --> [ Projections ]    [ AWS S3/CDN ]
               |                 |                |
               +-----------------+----------------+
                                 |
                          [ PostgreSQL DB ]
                                 |
                        [ Prisma ORM Layer ]
```

### 2.4 Security Posture
As per the project mandate, the system will undergo an **internal security audit only**. External compliance (such as HIPAA or GDPR) is not required for the initial launch, allowing the team to focus on functional stability. However, standard security practices—including JWT-based authentication, bcrypt password hashing, and strict CORS policies—will be enforced.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Medium | **Status:** Blocked
**Description:** A comprehensive identity management system that ensures only authorized personnel can access sensitive supply chain data.

The RBAC system must support four primary roles: `SuperAdmin`, `ProcurementOfficer`, `WarehouseManager`, and `ReadOnlyAuditor`. Access is managed via a middleware layer that checks the user's role against the required permissions for a specific route or API endpoint.

**Functional Requirements:**
*   **Authentication:** Implementation of a secure login flow using OpenID Connect (OIDC) principles.
*   **Session Management:** JWTs stored in HttpOnly cookies to prevent XSS attacks.
*   **Role Mapping:** A mapping table connecting `UserIDs` to `RoleIDs` and `PermissionIDs`.
*   **Audit Logging:** Every authentication attempt (success/failure) must be logged in the Event Store.

**Technical Constraint:** Currently, this feature is blocked by the existence of a 3,000-line "God class" that handles authentication, logging, and email. This class must be refactored into separate services before RBAC can be safely implemented.

### 3.2 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** The ability for users to upload shipping manifests, medical certifications, and invoices.

Because the system operates in a healthcare environment, uploaded files could potentially contain malware that could compromise the internal network. The pipeline must be: `Upload` $\rightarrow$ `Quarantine` $\rightarrow$ `Scan` $\rightarrow$ `Store` $\rightarrow$ `Distribute`.

**Functional Requirements:**
*   **Multipart Uploads:** Support for files up to 500MB using S3 presigned URLs.
*   **Virus Scanning:** Integration with a scanning engine (e.g., ClamAV) that triggers upon upload. Files flagged as "infected" must be immediately deleted and the user notified.
*   **CDN Integration:** Validated files are moved to a public-facing CDN (CloudFront/Vercel Blob) for fast retrieval by global stakeholders.
*   **Metadata Tracking:** Every file must be linked to a `TransactionID` in the database.

**Technical Constraint:** Currently blocked due to the absence of the DevOps environment configuration for the scanning microservice.

### 3.3 A/B Testing Framework (Feature Flag Integrated)
**Priority:** Critical (Launch Blocker) | **Status:** Blocked
**Description:** A system to roll out new features to a subset of users to measure impact and stability before a full release.

Rather than a separate tool, the A/B testing framework is baked directly into the Feature Flag system. This allows the team to toggle features based on user IDs, organization IDs, or random percentage cohorts.

**Functional Requirements:**
*   **Flag Definition:** A UI for the CTO (Beau Park) to create flags (e.g., `new_inventory_view`) and assign weights (e.g., 10% Group A, 90% Group B).
*   **Client-Side Evaluation:** The Next.js app must evaluate the flag on the server side (SSR) to prevent "flicker" during page load.
*   **Telemetry:** Integration with the analytics engine to track if "Group A" has a higher task-completion rate than "Group B".
*   **Kill Switch:** Ability to instantly disable a feature for all users if a critical bug is detected.

**Technical Constraint:** Blocked pending the completion of the RBAC system, as feature flags must be assigned based on user roles.

### 3.4 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have) | **Status:** In Progress
**Description:** A user-centric landing page where users can arrange "widgets" (Kpis, Charts, Recent Activities) to suit their specific role.

The dashboard utilizes a grid-based layout (React-Grid-Layout) allowing users to resize and reposition components.

**Functional Requirements:**
*   **Widget Library:** A set of pre-defined widgets including "Pending Shipments," "Low Stock Alerts," and "Recent Audit Logs."
*   **Persistence:** User layout configurations must be saved in the PostgreSQL database as a JSONB blob.
*   **Real-time Updates:** Widgets must use SWR or React Query to poll for updates without refreshing the page.
*   **Customization:** Users can add/remove widgets based on their role permissions.

### 3.5 Customer-Facing API with Versioning and Sandbox
**Priority:** Low (Nice to Have) | **Status:** In Review
**Description:** A public-facing REST API that allows the anchor client to integrate Ingot data into their own internal ERP systems.

**Functional Requirements:**
*   **API Versioning:** Endpoints must be versioned (e.g., `/v1/orders`, `/v2/orders`) to ensure backward compatibility.
*   **Sandbox Environment:** A mirrored environment with mock data where clients can test their integrations without affecting production data.
*   **API Key Management:** A dashboard for users to generate, rotate, and revoke API keys.
*   **Rate Limiting:** Implementation of a leaky-bucket algorithm to prevent API abuse (e.g., 100 requests per minute).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api`. All requests and responses use `application/json`.

### 4.1 Authentication & User Management
**POST `/api/v1/auth/login`**
*   **Request:** `{ "email": "user@oakmount.com", "password": "password123" }`
*   **Response (200):** `{ "token": "eyJhbG...", "user": { "id": "u1", "role": "ProcurementOfficer" } }`

**GET `/api/v1/users/me`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (200):** `{ "id": "u1", "email": "user@oakmount.com", "role": "ProcurementOfficer", "lastLogin": "2023-10-24T10:00Z" }`

### 4.2 Inventory & Supply Chain
**GET `/api/v1/inventory`**
*   **Request:** Header `Authorization: Bearer <token>`, Query params `?category=surgical`
*   **Response (200):** `[ { "sku": "SKU-100", "quantity": 500, "status": "in-stock", "location": "Warehouse-A" } ]`

**POST `/api/v1/inventory/adjust`**
*   **Request:** `{ "sku": "SKU-100", "adjustment": -10, "reason": "Damaged during transit", "operatorId": "u1" }`
*   **Response (201):** `{ "transactionId": "tx-999", "newQuantity": 490, "timestamp": "2023-10-24T11:00Z" }`

**GET `/api/v1/orders/{orderId}`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (200):** `{ "orderId": "ord-55", "status": "shipped", "items": [...], "trackingUrl": "https://cdn.ingot.com/track/55" }`

**PATCH `/api/v1/orders/{orderId}/status`**
*   **Request:** `{ "status": "delivered", "confirmationCode": "CONF-123" }`
*   **Response (200):** `{ "orderId": "ord-55", "updatedAt": "2023-10-24T12:00Z" }`

### 4.3 File & Document Management
**POST `/api/v1/files/upload`**
*   **Request:** Multipart form-data with file and `associatedEntityId`.
*   **Response (202):** `{ "fileId": "f-77", "status": "scanning", "eta": "30s" }`

**GET `/api/v1/files/{fileId}/status`**
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response (200):** `{ "fileId": "f-77", "status": "clean", "url": "https://cdn.ingot.com/files/f-77.pdf" }`

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL and managed via Prisma. It utilizes a mix of relational tables for state and an event store for history.

### 5.1 Schema Definition

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `userId` | `roleId` | `email`, `passwordHash`, `isActive` | User accounts and credentials. |
| `Roles` | `roleId` | - | `roleName`, `permissionsJson` | Definition of RBAC roles. |
| `UserRoles` | `mappingId` | `userId`, `roleId` | `assignedAt` | Junction table for users and roles. |
| `Products` | `productId` | - | `sku`, `name`, `description`, `category` | Catalog of medical supplies. |
| `Inventory` | `invId` | `productId` | `quantity`, `locationId`, `lastUpdated` | Current stock levels. |
| `Warehouses` | `locationId` | - | `warehouseName`, `address`, `capacity` | Physical storage sites. |
| `Orders` | `orderId` | `userId` | `status`, `totalAmount`, `createdAt` | Procurement orders. |
| `OrderItems` | `itemId` | `orderId`, `productId` | `quantity`, `unitPrice` | Line items for each order. |
| `Documents` | `docId` | `orderId` | `s3Key`, `virusScanStatus`, `mimeType` | File metadata and scan results. |
| `EventStore` | `eventId` | `entityId` | `eventType`, `payloadJson`, `timestamp` | Immutable log of all system changes. |

### 5.2 Relationships
*   **One-to-Many:** `Users` $\rightarrow$ `Orders` (One user can place many orders).
*   **Many-to-Many:** `Users` $\leftrightarrow$ `Roles` (via `UserRoles` junction table).
*   **One-to-Many:** `Orders` $\rightarrow$ `OrderItems` (One order contains multiple products).
*   **One-to-One:** `OrderItems` $\rightarrow$ `Documents` (Usually one manifest per item/order).
*   **Polymorphic:** `EventStore` $\rightarrow$ Any entity (The `entityId` refers to any other table in the DB).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Project Ingot utilizes three distinct environments to ensure stability and rigorous testing.

#### 6.1.1 Development (`dev`)
*   **Purpose:** Active feature development and unit testing.
*   **Deployment:** Auto-deployed from the `develop` branch via GitLab CI.
*   **Database:** Isolated PostgreSQL instance with seed data.
*   **Configuration:** Debugging enabled, mock virus scanning service.

#### 6.1.2 Staging (`staging`)
*   **Purpose:** QA testing, UAT (User Acceptance Testing), and internal alpha.
*   **Deployment:** Deployed from `release/*` branches.
*   **Database:** A sanitized snapshot of production data.
*   **Configuration:** Mirror of production settings; uses the real virus scanning pipeline.

#### 6.1.3 Production (`prod`)
*   **Purpose:** Live client environment.
*   **Deployment:** Rolling deployments to Kubernetes clusters via GitLab CI.
*   **Database:** High-availability PostgreSQL cluster with automated backups every 6 hours.
*   **Configuration:** Strict security headers, optimized CDN caching, and full telemetry.

### 6.2 CI/CD Pipeline
The pipeline is managed via **GitLab CI**.
1.  **Build Phase:** TypeScript compilation and Next.js build.
2.  **Test Phase:** Running Jest unit tests and Playwright E2E tests.
3.  **Security Phase:** Static analysis (SAST) for vulnerability scanning.
4.  **Deploy Phase:** Kubernetes rolling update $\rightarrow$ Health check $\rightarrow$ Traffic shift.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Tool:** Jest
*   **Scope:** Business logic in the Command handlers and utility functions.
*   **Requirement:** 80% code coverage on all new services.
*   **Focus:** Ensuring that the Event Sourcing logic correctly transforms an event into a state change.

### 7.2 Integration Testing
*   **Tool:** Vitest + Prisma Mock
*   **Scope:** Database queries and API endpoint orchestration.
*   **Requirement:** All `POST`, `PATCH`, and `DELETE` endpoints must have a corresponding integration test.
*   **Focus:** Verifying that the RBAC middleware correctly blocks unauthorized requests.

### 7.3 End-to-End (E2E) Testing
*   **Tool:** Playwright
*   **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Create Order $\rightarrow$ Upload Manifest").
*   **Requirement:** Full regression suite must pass before any deployment to `staging`.
*   **Focus:** Testing the drag-and-drop functionality of the dashboard across Chrome, Firefox, and Safari.

### 7.4 QA Process
Uri Santos (QA Lead) manages the "Quality Gate." No feature is marked "Complete" until it has:
1.  A passing set of unit tests.
2.  A signed-off UAT (User Acceptance Test) from the Project Lead.
3.  A verified fix for any "Blocker" or "Critical" bugs found during the staging phase.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead in market. | High | High | Hire a specialized contractor to accelerate development and reduce the "bus factor" for key modules. |
| R-02 | Budget cut of 30% in next fiscal quarter. | Medium | Medium | De-scope "Nice to Have" features (Dashboard, Public API) if the budget is not secured by Milestone 1. |
| R-03 | Key team member on medical leave (6 weeks). | Actual | High | Redistribution of tasks to Ingrid Kim and Beau Park; prioritize "critical" blockers over "medium" features. |
| R-04 | Technical debt (God Class) prevents RBAC. | Actual | High | Allocate a dedicated "Refactor Sprint" to decompose the 3,000-line class into modular services. |
| R-05 | Failure to pass external audit. | Low | Critical | Implement strict event-sourcing and immutable logs from Day 1 to ensure a perfect audit trail. |

**Probability/Impact Matrix:**
*   **Critical:** Immediate project failure or launch delay.
*   **High:** Significant delay or loss of functionality.
*   **Medium:** Manageable impact with minor adjustments.
*   **Low:** Negligible impact.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions

**Phase 1: Foundation & Refactoring (Current $\rightarrow$ 2026-01-01)**
*   Decompose the "God Class."
*   Establish the PostgreSQL/Prisma schema.
*   Set up GitLab CI and Kubernetes environments.
*   *Dependency:* Refactoring must be complete before RBAC development starts.

**Phase 2: Core Feature Build (2026-01-01 $\rightarrow$ 2026-07-15)**
*   Implement RBAC and User Authentication.
*   Build the File Upload and Virus Scanning pipeline.
*   Implement the A/B Testing framework.
*   *Milestone 1:* MVP Feature-Complete (Target: 2026-07-15).

**Phase 3: Stabilization & Alpha (2026-07-16 $\rightarrow$ 2026-11-15)**
*   Internal Alpha release to Oakmount staff.
*   Bug scrubbing and performance tuning.
*   Final internal security audit.
*   *Milestone 3:* Internal Alpha Release (Target: 2026-11-15).

**Phase 4: Production Launch (2026-09-15)**
*   *Note:* The production launch target (2026-09-15) precedes the Alpha release date in the timeline, indicating a "Soft Launch" for the anchor client while the broader internal alpha continues for polish.
*   Full data migration.
*   Client onboarding.
*   *Milestone 2:* Production Launch (Target: 2026-09-15).

---

## 10. MEETING NOTES

### Meeting 1: Project Kickoff & Architecture Review
**Date:** 2023-10-10  
**Attendees:** Beau Park, Udo Nakamura, Uri Santos, Ingrid Kim  
**Discussion:**
*   Beau introduced the $2M anchor client and the need for an audit-ready system.
*   Udo proposed the CQRS/Event Sourcing model to ensure no data is ever truly deleted.
*   Ingrid raised concerns about the current "God Class" in the legacy codebase, noting it makes testing nearly impossible.
*   Uri emphasized that "Critical" features must be the priority to avoid launch delays.

**Action Items:**
*   **Udo:** Set up the Kubernetes cluster and GitLab CI pipelines. (Owner: Udo | Due: 2023-10-20)
*   **Beau:** Draft the initial Prisma schema. (Owner: Beau | Due: 2023-10-15)
*   **Ingrid:** Map out the dependencies of the "God Class" for refactoring. (Owner: Ingrid | Due: 2023-10-17)

---

### Meeting 2: Resource Crisis & Blockers
**Date:** 2023-11-02  
**Attendees:** Beau Park, Udo Nakamura, Uri Santos, Ingrid Kim  
**Discussion:**
*   Notification that a key backend engineer (non-core team member but critical for infra) is on medical leave for 6 weeks.
*   The team discussed the impact on the "File Upload" and "A/B Testing" features, which are both currently blocked.
*   Beau suggested hiring a contractor to mitigate the "bus factor" and keep the project moving.
*   Uri warned that if the virus scanning pipeline isn't finished, the project cannot launch.

**Action Items:**
*   **Beau:** Post a job listing for a contract DevOps/Backend engineer. (Owner: Beau | Due: 2023-11-05)
*   **Udo:** Review if there are open-source alternatives for the virus scanner to reduce custom build time. (Owner: Udo | Due: 2023-11-10)

---

### Meeting 3: Budget & Scope Alignment
**Date:** 2023-11-20  
**Attendees:** Beau Park, Udo Nakamura, Uri Santos  
**Discussion:**
*   Review of the $1.5M budget. Beau noted that while well-funded, a potential 30% cut in the next fiscal quarter is a possibility.
*   The team agreed that the "Customizable Dashboard" and "Public API" are lower priorities.
*   Decision: If the budget is cut, these two features will be moved to "Phase 5" (Post-Launch) or dropped entirely.
*   Uri reported that the internal security audit needs to be scheduled for Q2 2026.

**Action Items:**
*   **Beau:** Update the Risk Register to include the budget cut mitigation. (Owner: Beau | Due: 2023-11-21)
*   **Uri:** Define the "External Audit" success criteria (Metric 1). (Owner: Uri | Due: 2023-11-25)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000 USD

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $1,050,000 | Salaries for 4 core members + planned contractor. |
| **Infrastructure** | 15% | $225,000 | Vercel Enterprise, AWS S3, PostgreSQL Managed Instance, Kubernetes. |
| **Tools & Licensing** | 5% | $75,000 | GitLab Premium, Playwright, Virus Scanning Licenses, Monitoring tools. |
| **Contingency** | 10% | $150,000 | Reserved for emergency hiring or hardware scale-up. |

**Personnel Breakdown (Approximate):**
*   Project Lead (Beau): $300k
*   DevOps (Udo): $250k
*   QA Lead (Uri): $200k
*   Junior Dev (Ingrid): $150k
*   Contractor (TBD): $150k

---

## 12. APPENDICES

### Appendix A: Event Store Payload Examples
To ensure the audit trail is consistent, all events in the `EventStore` table must follow this JSON schema:

**Event: `InventoryAdjusted`**
```json
{
  "eventId": "evt-12345",
  "entityId": "prod-sku-100",
  "eventType": "INVENTORY_ADJUSTED",
  "timestamp": "2023-10-24T15:30:00Z",
  "userId": "u1",
  "payload": {
    "previousQuantity": 500,
    "newQuantity": 490,
    "delta": -10,
    "reason": "Damaged during transit"
  },
  "metadata": {
    "ipAddress": "192.168.1.50",
    "userAgent": "Mozilla/5.0..."
  }
}
```

### Appendix B: Refactoring Plan for the "God Class"
The 3,000-line class `SystemCore.ts` is identified as the primary technical debt. The refactoring strategy is as follows:

1.  **Phase 1: Isolation.** Wrap the `SystemCore` calls in a facade to prevent further direct dependencies.
2.  **Phase 2: Extraction.** 
    *   Extract `AuthLogic` $\rightarrow$ `AuthService.ts`
    *   Extract `LogWriter` $\rightarrow$ `LoggerService.ts`
    *   Extract `EmailDispatcher` $\rightarrow$ `NotificationService.ts`
3.  **Phase 3: Dependency Injection.** Use a DI container to inject these services into the Next.js API routes, removing the singleton pattern currently used in `SystemCore`.
4.  **Phase 4: Deletion.** Once all calls are routed to the new services, `SystemCore.ts` will be deleted.