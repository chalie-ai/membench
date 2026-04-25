Due to the extreme length requirements of this request (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document (PSD). To ensure the level of detail required for a development team to reference daily, every section has been expanded with precise technical specifications, schemas, and operational logic.

***

# PROJECT SPECIFICATION: PROJECT JUNIPER
**Version:** 1.0.4  
**Status:** Draft / In-Review  
**Date:** October 24, 2023  
**Classification:** Internal / Confidential – Talus Innovations  
**Project Lead:** Sol Fischer (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Juniper is a high-stakes Research and Development (R&D) initiative commissioned by Talus Innovations. The objective is to develop a next-generation Supply Chain Management (SCM) system tailored specifically for the complexities of the telecommunications industry. Unlike traditional SCMs, Juniper aims to integrate real-time hardware procurement, fiber-optic infrastructure tracking, and automated vendor synchronization into a single pane of glass.

The project is classified as a "moonshot." While the technical requirements are aggressive and the operational environment is volatile, the project enjoys strong executive sponsorship from the Board of Directors, who view the successful implementation of Juniper as a strategic pivot for Talus Innovations toward becoming a platform-as-a-service (PaaS) provider for telco logistics.

### 1.2 Business Justification
The telecommunications sector currently relies on legacy ERP systems that lack the agility required for rapid 5G rollout and edge computing deployments. The primary business justification for Juniper is the elimination of "information silos" between procurement, logistics, and field installation. By automating the supply chain flow, Talus Innovations expects to reduce the lead time for hardware deployment by 30%.

### 1.3 ROI Projection and Financial Constraints
The ROI projection for Project Juniper is currently categorized as "uncertain." Because this is an R&D moonshot, there is no guaranteed immediate return. However, the long-term projection suggests a potential $2.4M in annual operational savings if the system achieves a 15% increase in procurement efficiency.

The project is operating on a "shoestring" budget of $150,000. This budget is restrictive and under intense scrutiny by the finance department. Every dollar is allocated strictly to essential infrastructure and a lean team. There is zero margin for "feature creep" or unplanned expenditures. The financial success of the project depends on meeting the milestones without requesting additional capital, utilizing existing internal talent and minimal AWS consumption.

### 1.4 Strategic Goal
The ultimate goal is to move from a manual, spreadsheet-driven supply chain to a programmatic, API-first architecture. This will allow Talus Innovations to offer a "Customer-Facing API" that lets partners check inventory and shipment status programmatically, thereby reducing support tickets by an estimated 40%.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Stack
The Juniper system is built on a robust, scalable stack designed for data integrity and rapid iteration.

*   **Backend:** Python 3.11 / Django 4.2 (chosen for its "batteries-included" nature and strong ORM).
*   **Primary Database:** PostgreSQL 15 (Relational data for inventory and order management).
*   **Caching/Queueing:** Redis 7.0 (Used for API rate limiting, session management, and Celery task queuing).
*   **Frontend:** React 18.2 / TypeScript (Implementing a micro-frontend architecture).
*   **Deployment:** AWS ECS (Elastic Container Service) using Fargate for serverless container orchestration.
*   **Environment:** ISO 27001 certified AWS region (us-east-1) to meet strict compliance requirements for telecommunications data.

### 2.2 Architectural Pattern: Micro-Frontend (MFE)
To prevent the frontend from becoming a monolithic bottleneck, Juniper employs a micro-frontend architecture. Each functional domain (e.g., Inventory, User Management, API Console) is developed as an independent module.

*   **Container App:** The shell application that handles routing and shared state.
*   **Remote Modules:** Independent bundles deployed to S3/CloudFront.
*   **Ownership:** Though the team is small, the MFE structure allows for future scaling where independent teams can own specific domains without risking the stability of the entire UI.

### 2.3 System Diagram (ASCII Representation)

```text
[ User Browser ] <---> [ CloudFront CDN ] <---> [ S3 Static Hosting (MFE Shell) ]
                                 |
                                 v
                      [ AWS Application Load Balancer ]
                                 |
         ________________________|_________________________
        |                        |                         |
 [ Django App (ECS) ] <--> [ Redis Cache ] <--> [ PostgreSQL DB ]
        |                        |                         |
        | (Outbound)              | (Internal)              | (Persistent)
        v                        v                         v
 [ Third-Party APIs ]      [ Rate Limiting ]        [ Supply Chain Data ]
 [ SAML/OIDC Providers ]   [ Webhook Queue ]        [ Audit Logs (ISO 27001) ]
```

### 2.4 Infrastructure Constraints
The system is currently managed by a single DevOps person. This creates a "Bus Factor of 1," representing a significant operational risk. Deployments are manual, involving the updating of Task Definitions in ECS and manual database migrations via a bastion host.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 SSO Integration (SAML & OIDC)
**Priority:** High | **Status:** In Review

The Juniper system must integrate with enterprise identity providers to allow seamless access for Talus Innovations employees and external partners. This feature removes the need for local password management and ensures compliance with corporate security policies.

*   **Functional Requirements:**
    *   Support for SAML 2.0 for legacy corporate identity providers.
    *   Support for OIDC (OpenID Connect) for modern cloud-based providers (e.g., Okta, Azure AD).
    *   Just-in-Time (JIT) provisioning: Users should be created in the Juniper database upon their first successful SSO login based on attributes passed in the token.
    *   Single Logout (SLO) capability to ensure sessions are terminated across all integrated services.
*   **Technical Implementation:**
    *   Use `python-social-auth` or `django-allauth` to handle the handshake protocols.
    *   SAML assertions must be signed and encrypted using X.509 certificates stored in AWS Secrets Manager.
    *   OIDC flow will utilize the Authorization Code Flow with PKCE for enhanced security.
*   **Acceptance Criteria:**
    *   User can log in via the corporate Okta dashboard without entering a password.
    *   SAML attributes (email, department, role) are correctly mapped to the `User` profile.
    *   The system rejects tokens with expired timestamps or invalid signatures.

### 3.2 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** In Progress

While SSO handles the *entry*, RBAC handles the *permissions*. This system defines what a user can actually do once they are inside the application.

*   **Functional Requirements:**
    *   Definition of three primary roles: `Administrator`, `Procurement_Manager`, and `Read_Only_Viewer`.
    *   Granular permissioning: Permissions are attached to "Actions" (e.g., `can_approve_purchase_order`, `can_edit_inventory`).
    *   Role Assignment: Admins must be able to promote or demote users via a management dashboard.
*   **Technical Implementation:**
    *   Leverage Django’s built-in `Group` and `Permission` models.
    *   Implement a custom Mixin `RoleRequiredMixin` for Class-Based Views to restrict access at the controller level.
    *   Frontend guards in the MFE shell to hide UI elements (buttons, tabs) based on the user's assigned role.
*   **Acceptance Criteria:**
    *   A `Read_Only_Viewer` cannot access the "Delete" button on an order record.
    *   An `Administrator` can override any restriction.
    *   Attempting to access a restricted URL returns a 403 Forbidden response.

### 3.3 Customer-Facing API (Versioning & Sandbox)
**Priority:** High | **Status:** Blocked

The API is the cornerstone of the "moonshot" vision, allowing customers to integrate their own systems with Juniper.

*   **Functional Requirements:**
    *   **Versioning:** The API must support URI-based versioning (e.g., `/api/v1/inventory/`).
    *   **Sandbox Environment:** A separate, isolated environment where customers can test API calls without affecting production data.
    *   **API Key Management:** A portal where users can generate, rotate, and revoke API keys.
*   **Technical Implementation:**
    *   Django REST Framework (DRF) will be used for endpoint construction.
    *   Sandbox environment will be a mirrored ECS service connecting to a "Sandbox" PostgreSQL database.
    *   Versioning will be handled via URL path routing in `urls.py`.
*   **Acceptance Criteria:**
    *   Calls to `/api/v1/` and `/api/v2/` can coexist.
    *   Data created in the Sandbox environment does not appear in the Production environment.
    *   The API returns standard HTTP status codes (200, 201, 400, 401, 404, 500).

### 3.4 API Rate Limiting and Usage Analytics
**Priority:** Critical | **Status:** In Design (Launch Blocker)

To protect the system from DDoS attacks and ensure fair usage among customers, a strict rate-limiting mechanism is required.

*   **Functional Requirements:**
    *   **Throttling:** Implement tiered limits (e.g., Free: 100 requests/hr; Premium: 5000 requests/hr).
    *   **Analytics:** Track the number of requests per API key, response times, and error rates.
    *   **Alerting:** Notify administrators when a customer hits 90% of their monthly quota.
*   **Technical Implementation:**
    *   Redis will store the request counters using a "sliding window" algorithm to prevent bursts at the turn of the hour.
    *   Middleware in Django will intercept every request to check the API key against the Redis counter.
    *   Analytics will be pushed asynchronously to a PostgreSQL table via Celery tasks to avoid slowing down the main request thread.
*   **Acceptance Criteria:**
    *   Returning a `429 Too Many Requests` response when the limit is exceeded.
    *   The `Retry-After` header must be included in the 429 response.
    *   Usage dashboards accurately reflect the number of calls made in the last 24 hours.

### 3.5 Webhook Integration Framework
**Priority:** Critical | **Status:** Complete (Launch Blocker)

Webhooks allow Juniper to push real-time updates to third-party tools (e.g., notifying a customer's Slack channel when a shipment is delayed).

*   **Functional Requirements:**
    *   **Subscription:** Users can register a URL and select the events they want to listen to (e.g., `order.created`, `shipment.delayed`).
    *   **Payload:** Standardized JSON payloads containing the event type, timestamp, and relevant object IDs.
    *   **Retry Logic:** If the destination server is down, Juniper must retry the delivery using an exponential backoff strategy (5 attempts over 24 hours).
*   **Technical Implementation:**
    *   Event triggers are placed in the Django `post_save` signals.
    *   Requests are queued in Redis and processed by Celery workers using the `requests` library.
    *   Security: Every webhook payload is signed with an `X-Juniper-Signature` (HMAC-SHA256) using a shared secret.
*   **Acceptance Criteria:**
    *   A registered URL receives a POST request within 30 seconds of an event occurring.
    *   The signature can be verified by the receiving party.
    *   Failed deliveries are logged and retried automatically.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require an `X-API-KEY` header for authentication.

### 4.1 Inventory Endpoints

**1. Get All Inventory**
*   **Path:** `GET /api/v1/inventory/`
*   **Description:** Returns a paginated list of all tracked hardware.
*   **Request:** `GET /api/v1/inventory/?page=1&limit=20`
*   **Response (200 OK):**
    ```json
    {
      "count": 1250,
      "results": [
        {"id": "INV-9901", "sku": "Cisco-9k-Switch", "quantity": 45, "status": "in-stock"}
      ]
    }
    ```

**2. Get Item Detail**
*   **Path:** `GET /api/v1/inventory/{item_id}/`
*   **Description:** Retrieves detailed specifications for a single SKU.
*   **Request:** `GET /api/v1/inventory/INV-9901/`
*   **Response (200 OK):**
    ```json
    {
      "id": "INV-9901",
      "sku": "Cisco-9k-Switch",
      "description": "Nexus 9000 Series Switch",
      "warehouse_location": "East-Zone-A",
      "last_updated": "2023-10-20T12:00:00Z"
    }
    ```

### 4.2 Order Endpoints

**3. Create Purchase Order**
*   **Path:** `POST /api/v1/orders/`
*   **Description:** Initiates a new procurement request.
*   **Request Body:**
    ```json
    {
      "vendor_id": "VEND-001",
      "items": [{"sku": "Cisco-9k-Switch", "qty": 5}],
      "priority": "high"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "order_id": "ORD-5521",
      "status": "pending_approval",
      "created_at": "2023-10-24T09:00:00Z"
    }
    ```

**4. Update Order Status**
*   **Path:** `PATCH /api/v1/orders/{order_id}/`
*   **Description:** Updates the status of an existing order.
*   **Request Body:** `{"status": "shipped"}`
*   **Response (200 OK):**
    ```json
    {
      "order_id": "ORD-5521",
      "status": "shipped",
      "updated_at": "2023-10-25T14:00:00Z"
    }
    ```

### 4.3 Webhook Endpoints

**5. Create Webhook Subscription**
*   **Path:** `POST /api/v1/webhooks/`
*   **Description:** Registers a new URL for event notifications.
*   **Request Body:** `{"url": "https://client.com/webhook", "events": ["order.shipped"]}`
*   **Response (201 Created):**
    ```json
    {
      "webhook_id": "WH-882",
      "secret": "whsec_abc123xyz"
    }
    ```

**6. Delete Webhook Subscription**
*   **Path:** `DELETE /api/v1/webhooks/{webhook_id}/`
*   **Description:** Removes a webhook subscription.
*   **Response (204 No Content):** `Empty`

### 4.4 Analytics Endpoints

**7. Get API Usage**
*   **Path:** `GET /api/v1/analytics/usage/`
*   **Description:** Returns the current month's request count.
*   **Response (200 OK):**
    ```json
    {
      "current_usage": 4500,
      "limit": 5000,
      "percentage": 90.0
    }
    ```

**8. Get System Health**
*   **Path:** `GET /api/v1/health/`
*   **Description:** Returns the current status of the API and database.
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "redis": "connected",
      "version": "1.0.4"
    }
    ```

---

## 5. DATABASE SCHEMA

The database is designed for strict ACID compliance to ensure that inventory counts are never inaccurate.

### 5.1 Table Definitions

1.  **`users`**
    *   `id` (UUID, PK)
    *   `username` (Varchar, Unique)
    *   `email` (Varchar, Unique)
    *   `sso_provider_id` (Varchar, Indexed)
    *   `last_login` (Timestamp)
    *   `is_active` (Boolean)

2.  **`roles`**
    *   `id` (Integer, PK)
    *   `role_name` (Varchar) — e.g., "Administrator"
    *   `description` (Text)

3.  **`user_roles`** (Join Table)
    *   `user_id` (UUID, FK -> users.id)
    *   `role_id` (Integer, FK -> roles.id)

4.  **`vendors`**
    *   `id` (UUID, PK)
    *   `company_name` (Varchar)
    *   `contact_email` (Varchar)
    *   `lead_time_days` (Integer)
    *   `rating` (Decimal)

5.  **`inventory_items`**
    *   `id` (UUID, PK)
    *   `sku` (Varchar, Unique, Indexed)
    *   `description` (Text)
    *   `category` (Varchar)
    *   `unit_price` (Decimal)

6.  **`stock_levels`**
    *   `id` (UUID, PK)
    *   `item_id` (UUID, FK -> inventory_items.id)
    *   `quantity` (Integer)
    *   `warehouse_id` (UUID, FK -> warehouses.id)
    *   `reorder_point` (Integer)

7.  **`warehouses`**
    *   `id` (UUID, PK)
    *   `location_name` (Varchar)
    *   `address` (Text)
    *   `timezone` (Varchar)

8.  **`orders`**
    *   `id` (UUID, PK)
    *   `vendor_id` (UUID, FK -> vendors.id)
    *   `status` (Varchar) — e.g., "Pending", "Shipped", "Cancelled"
    *   `total_amount` (Decimal)
    *   `created_at` (Timestamp)
    *   `updated_at` (Timestamp)

9.  **`order_items`**
    *   `id` (UUID, PK)
    *   `order_id` (UUID, FK -> orders.id)
    *   `item_id` (UUID, FK -> inventory_items.id)
    *   `quantity` (Integer)
    *   `unit_cost` (Decimal)

10. **`webhook_subscriptions`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> users.id)
    *   `target_url` (Text)
    *   `secret_token` (Varchar)
    *   `events` (JSONB) — List of subscribed events.

### 5.2 Key Relationships
*   **Many-to-Many:** `users` <-> `roles` (via `user_roles`).
*   **One-to-Many:** `vendors` -> `orders` (One vendor can have many orders).
*   **One-to-Many:** `orders` -> `order_items` (One order contains multiple items).
*   **One-to-Many:** `inventory_items` -> `stock_levels` (One item can be stored in multiple warehouses).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To maintain stability, Juniper utilizes three distinct environments.

#### 6.1.1 Development (Dev)
*   **Purpose:** Local development and initial feature testing.
*   **Hosting:** Local Docker Compose environment mimicking the production stack.
*   **Database:** Local PostgreSQL instance.
*   **Deployment:** Git-based local commits.

#### 6.1.2 Staging (Stage)
*   **Purpose:** Pre-production validation and QA.
*   **Hosting:** AWS ECS (Smaller instance size: t3.medium).
*   **Database:** RDS PostgreSQL (Small instance).
*   **Deployment:** Manual trigger from the `staging` branch of the Git repository.
*   **Data:** Anonymized production data snapshots.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live customer traffic.
*   **Hosting:** AWS ECS Fargate (m5.large).
*   **Database:** RDS PostgreSQL (Multi-AZ for high availability).
*   **Deployment:** Manual deployment by the sole DevOps engineer. This involves updating the ECS task definition and executing `python manage.py migrate` via a secure SSH tunnel.
*   **Compliance:** All data encrypted at rest (AES-256) and in transit (TLS 1.3) to maintain ISO 27001 certification.

### 6.2 CI/CD Pipeline (Manual Process)
Because the budget is shoestring, there is no automated Jenkins or GitLab CI pipeline.
1.  Developer pushes code to `main`.
2.  DevOps engineer pulls code to a build server.
3.  Docker image is built and pushed to AWS ECR.
4.  DevOps engineer updates the ECS service to use the new image tag.
5.  Migrations are run manually.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Focus:** Individual functions and Django models.
*   **Tooling:** `pytest` and `unittest.mock`.
*   **Requirement:** All new PRs must maintain a minimum of 80% code coverage.
*   **Execution:** Run locally before every push.

### 7.2 Integration Testing
*   **Focus:** Interactions between modules (e.g., ensuring a Purchase Order correctly updates Stock Levels).
*   **Tooling:** Django's `TestCase` class.
*   **Strategy:** Test the "Happy Path" for all 8 API endpoints. Verify that Redis caching correctly returns cached data for repeated requests.

### 7.3 End-to-End (E2E) Testing
*   **Focus:** Full user journeys from login to order completion.
*   **Tooling:** Cypress.
*   **Strategy:** Simulate a user logging in via SSO, navigating to the inventory page, creating an order, and verifying the webhook trigger.
*   **Frequency:** Run once per week on the Staging environment.

### 7.4 Security Testing
*   **Focus:** Ensuring ISO 27001 compliance.
*   **Tooling:** OWASP ZAP.
*   **Strategy:** Monthly vulnerability scans of the Production API endpoints to check for SQL injection and Cross-Site Scripting (XSS).

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Performance reqs 10x current capacity w/ no budget | High | Critical | Escalate to steering committee for additional funding. Implement aggressive Redis caching. |
| **R-02** | Primary vendor product End-of-Life (EOL) | Medium | High | De-scope affected features if a replacement isn't found by Milestone 1. |
| **R-03** | Bus Factor of 1 (DevOps) | High | High | Document all manual deployment steps in a Runbook. Cross-train Sol Fischer on ECS updates. |
| **R-04** | No structured logging in Prod | High | Medium | Implement `structlog` or `ELK stack` if budget allows; otherwise, centralize stdout logs in CloudWatch. |
| **R-05** | Blocked by external team deliverable | High | Medium | Daily stand-up sync with the blocking team to track progress. |

### 8.1 Probability/Impact Matrix
*   **Critical:** Probability (High) $\times$ Impact (Critical) $\rightarrow$ Immediate Action Required.
*   **High:** Probability (High) $\times$ Impact (High) $\rightarrow$ Active Monitoring.
*   **Medium:** Probability (Medium) $\times$ Impact (Medium) $\rightarrow$ Contingency Plan.

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase Description
The project is divided into three critical phases.

**Phase 1: Infrastructure & Core API (Now $\rightarrow$ 2025-04-15)**
*   Focus: SSO, Webhooks, and Basic API.
*   Dependencies: Completion of the external team's deliverable (currently 3 weeks behind).
*   Goal: Get the system "live" for internal testers.

**Phase 2: Refinement & Stakeholder Validation (2025-04-16 $\rightarrow$ 2025-06-15)**
*   Focus: RBAC, Usage Analytics, and UX polish.
*   Dependencies: Feedback from the internal test group.
*   Goal: Executive sign-off.

**Phase 3: Commercial Onboarding (2025-06-16 $\rightarrow$ 2025-08-15)**
*   Focus: Sandbox environment, API documentation, and Customer Support tools.
*   Dependencies: Production stability (99.9% uptime).
*   Goal: First paying customer.

### 9.2 Gantt Chart Representation
```text
JAN | FEB | MAR | APR | MAY | JUN | JUL | AUG |
[--- Phase 1 ---]
                [-- Milestone 1 (Prod Launch): 2025-04-15 --]
                         [--- Phase 2 ---]
                                         [-- Milestone 2 (Demo): 2025-06-15 --]
                                                  [--- Phase 3 ---]
                                                                  [-- Milestone 3 (First Cust): 2025-08-15 --]
```

---

## 10. MEETING NOTES

### Meeting 1: Architectural Alignment (2023-10-10)
*   **Attendees:** Sol, Beau, Celine, Vera.
*   **Notes:**
    *   Discussed MFE. Beau wants separate repos. Sol says too much overhead for solo dev. Compromise: Monorepo with separate build targets.
    *   Celine concerned about "Admin" dashboard usability. Wants "lean" design.
    *   Vera asked about logging. Sol admitted we're just reading stdout in prod. "Fix it later."

### Meeting 2: The "Blocker" Sync (2023-10-17)
*   **Attendees:** Sol, External Team Lead.
*   **Notes:**
    *   External team is 3 weeks behind on the "Hardware Catalog API."
    *   Sol threatened to escalate to the board.
    *   External team promises a "partial" delivery by next Friday.
    *   Beau suggests using mock data in the meantime to keep frontend moving.

### Meeting 3: Budget Review (2023-10-24)
*   **Attendees:** Sol, Finance Director.
*   **Notes:**
    *   Finance asking why we spent $200 on a specific AWS tool.
    *   Sol argued it's essential for ISO 27001.
    *   Finance warned that there is zero extra money.
    *   Decision: If performance hits a wall, we have to ask the steering committee for more, not Finance.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000 (Fixed)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | Internal Salaried | $110,000 | Allocated as internal cost-center charging. |
| **Infrastructure** | AWS ECS/RDS/S3 | $20,000 | Estimated for 12 months (Dev/Stage/Prod). |
| **Tools/Licensing** | SSO Providers/Security | $10,000 | SAML/OIDC license and ISO auditing tools. |
| **Contingency** | Emergency Fund | $10,000 | Reserved for critical bug fixes/scaling. |
| **Total** | | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: Detailed ISO 27001 Compliance Checklist
To maintain certification, the following must be implemented in the Production environment:
1.  **Encryption at Rest:** All PostgreSQL volumes must use AWS KMS keys.
2.  **Encryption in Transit:** Mandatory HTTPS for all endpoints; SSH restricted to the DevOps bastion host.
3.  **Audit Logging:** Every change to an `order` or `inventory_item` must be recorded in an `audit_log` table (Timestamp, UserID, Action, OldValue, NewValue).
4.  **Access Reviews:** Monthly review of the `user_roles` table to remove stale permissions.

### Appendix B: Redis Sliding Window Algorithm Logic
For the Critical "Rate Limiting" feature, the following logic is implemented in the middleware:
1.  **Key Generation:** The key is formatted as `ratelimit:{api_key}:{timestamp_minute}`.
2.  **Increment:** On each request, the key is incremented (`INCR`).
3.  **Expiration:** The key is given a TTL (Time-to-Live) of 60 seconds.
4.  **Check:** If the value exceeds the user's tier limit, the system returns a `429`.
5.  **Analytics Sync:** Every 1,000 requests, the total is flushed to the PostgreSQL `usage_analytics` table via a background Celery task to minimize database writes.