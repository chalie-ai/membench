Due to the extreme length requirement and the structural complexity of a formal project specification, this document is presented as a comprehensive, professional engineering blueprint. 

***

# PROJECT SPECIFICATION: JETSTREAM
**Version:** 1.0.4  
**Status:** Active / In-Development  
**Classification:** Internal – Oakmount Group Confidential  
**Last Updated:** October 24, 2023  
**Project Lead:** Alejandro Gupta  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Jetstream" is a mission-critical digital transformation initiative commissioned by Oakmount Group. The objective is the complete replacement of a 15-year-old legacy e-commerce marketplace system currently serving as the central operational hub for the company’s healthcare procurement and distribution. 

The legacy system, while functional, suffers from catastrophic technical debt, monolithic rigidity, and an inability to scale with modern healthcare regulatory requirements. Because the entire company depends on this system for daily revenue and supply chain management, Jetstream is being engineered with a **zero-downtime tolerance** mandate. Any interruption in service during the transition from legacy to Jetstream would result in immediate operational paralysis and significant financial loss.

### 1.2 Business Justification
The healthcare industry is shifting toward API-driven procurement and real-time data exchange. The current legacy system lacks the capability to integrate with modern Third-Party Logistics (3PL) providers and healthcare EDI (Electronic Data Interchange) standards. By migrating to a Python/Django-based micro-frontend architecture, Oakmount Group will transition from a reactive maintenance posture to a proactive growth posture.

The primary business drivers include:
1.  **Operational Efficiency:** Reducing the manual overhead associated with order processing and vendor reconciliation.
2.  **Regulatory Agility:** The ability to pivot system logic rapidly as healthcare regulations evolve, without risking system-wide crashes.
3.  **Developer Velocity:** Moving away from a monolithic codebase to independent team ownership via micro-frontends, allowing for faster iteration on specific marketplace modules.

### 1.3 ROI Projection
With a total investment of $3,000,000, Oakmount Group expects a full return on investment (ROI) within 24 months post-launch. The ROI is calculated based on two primary vectors:
- **Direct Labor Savings:** A projected 50% reduction in manual processing time for end users. Based on current payroll for operational staff, this is estimated to save $450,000 annually in reclaimed productivity.
- **Revenue Recovery:** The legacy system's instability currently results in an estimated 2% "leakage" in order fulfillment due to system timeouts and data corruption. Eliminating this via 99.9% uptime is projected to recover $800,000 in annual gross merchandise volume (GMV).

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Jetstream utilizes a decoupled architecture designed for high availability and scalability. The backend is built on **Python 3.11** and **Django 4.2 (LTS)**, providing a robust ORM and security framework. Data persistence is handled by **PostgreSQL 15**, with **Redis 7.0** serving as both a distributed cache and a message broker for asynchronous tasks (via Celery).

### 2.2 Micro-Frontend (MFE) Architecture
Unlike a traditional SPA, Jetstream employs a micro-frontend architecture. The user interface is split into independent domains (e.g., `OrderManagement`, `VendorPortal`, `InventoryTracking`). Each domain is owned by a specific team member and can be deployed independently, reducing the blast radius of updates.

### 2.3 Infrastructure Diagram (ASCII Representation)
```text
[ User Browser ] <--- HTTPS/TLS ---> [ AWS Application Load Balancer ]
                                            |
                                            v
                    _________________________________________________
                   |               AWS ECS CLUSTER (Fargate)         |
                   |                                                 |
                   |  [ MFE: Shell/Orchestrator ] <--- (React/Vue)    |
                   |        |               |                        |
                   |        v               v                        |
                   |  [ Django API v1 ] [ Django API v2 ] (Pods)     |
                   |________|_______________|________________________|
                            |               |
                            v               v
                   [ PostgreSQL RDS ] <---> [ Redis ElastiCache ]
                   (Primary/Replica)        (Session/Cache/Queue)
                            ^
                            |
                    [ S3 Bucket: Static Assets/Logs ]
```

### 2.4 Technology Stack Summary
| Component | Technology | Version | Reason for Selection |
| :--- | :--- | :--- | :--- |
| Language | Python | 3.11 | Rapid development, strong healthcare libraries. |
| Framework | Django | 4.2 | Built-in admin, security, and mature ORM. |
| Database | PostgreSQL | 15.3 | ACID compliance for financial transactions. |
| Cache/Queue | Redis | 7.0 | Low-latency state management. |
| Orchestration | AWS ECS | Fargate | Serverless containerization for easy scaling. |
| Frontend | Micro-Frontends | Custom | Independent ownership and deployment. |

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:** 
To protect the system from DDoS attacks and ensure fair usage across different healthcare providers, Jetstream requires a robust rate-limiting layer. This feature must track every request made to the customer-facing API and apply throttles based on the API Key's tier (e.g., Basic, Professional, Enterprise).

**Functional Requirements:**
- **Tiered Throttling:** Implement a "leaky bucket" algorithm to manage request flows.
    - *Basic:* 100 requests/minute.
    - *Professional:* 1,000 requests/minute.
    - *Enterprise:* 10,000 requests/minute.
- **Header Feedback:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Analytics Dashboard:** An internal administrative view allowing Alejandro Gupta to monitor spike patterns, identify top API consumers, and adjust limits in real-time without a code deploy.
- **Persistence:** Rate limit counters must be stored in Redis to ensure consistency across multiple ECS pods.

**Technical Constraints:**
- Latency added by the rate-limiter must not exceed 15ms per request.
- Analytics must be aggregated asynchronously via Celery to avoid blocking the request-response cycle.

### 3.2 Customer-Facing API with Versioning and Sandbox
**Priority:** Critical (Launch Blocker) | **Status:** Blocked (Legal Review)

**Description:** 
Jetstream will provide a RESTful API allowing healthcare clients to automate their ordering process. To ensure stability, the API must support strict versioning and provide a non-production "Sandbox" environment for clients to test their integrations.

**Functional Requirements:**
- **URI Versioning:** All endpoints must follow the pattern `/api/v{n}/...` (e.g., `/api/v1/orders`).
- **Sandbox Isolation:** A mirrored environment using a separate PostgreSQL database. Data in the sandbox must be anonymized to comply with healthcare privacy standards.
- **API Key Management:** A self-service portal where users can generate, revoke, and rotate their `Client_ID` and `Client_Secret`.
- **Documentation:** An auto-generated Swagger/OpenAPI 3.0 UI documenting all endpoints, request bodies, and error codes.

**Technical Constraints:**
- The system must support at least two concurrent versions (N and N-1) to allow clients time to migrate.
- Sandbox environments must be logically isolated from Production to prevent accidental order placement.

### 3.3 Webhook Integration Framework
**Priority:** Critical (Launch Blocker) | **Status:** Complete

**Description:** 
A push-based notification system that allows third-party tools (e.g., accounting software, shipping trackers) to receive real-time updates when specific events occur within the Jetstream marketplace.

**Functional Requirements:**
- **Event Subscriptions:** Users can subscribe to events such as `order.created`, `order.shipped`, and `payment.failed`.
- **Retry Logic:** If the third-party endpoint returns a non-2xx status code, Jetstream must implement an exponential backoff retry strategy (up to 5 attempts over 24 hours).
- **Secret Signing:** Every webhook payload must include an `X-Jetstream-Signature` (HMAC-SHA256) to allow the receiver to verify the authenticity of the request.
- **Delivery Logs:** A detailed log in the admin panel showing the payload sent, the response received, and the timestamp.

**Technical Constraints:**
- Webhook deliveries must be handled by a dedicated Celery queue to ensure a slow third-party endpoint does not clog the main application logic.

### 3.4 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:** 
Healthcare providers often operate in environments with unstable internet (e.g., hospital basements). This feature ensures that users can continue to draft orders and update inventory while offline, with data syncing automatically once connectivity is restored.

**Functional Requirements:**
- **Client-Side Storage:** Use IndexedDB to store pending mutations locally on the browser.
- **Conflict Detection:** Implementation of a "Last-Write-Wins" strategy combined with a manual resolution prompt for critical financial fields.
- **Background Sync:** Utilization of Service Workers to detect "Online" events and push the IndexedDB queue to the backend.
- **UI Indicators:** Clear visual cues (e.g., "Syncing...", "Offline - Changes Saved Locally") to keep the user informed of the data state.

**Technical Constraints:**
- Local storage must be encrypted to ensure that sensitive healthcare data is not accessible to unauthorized users of the device.

### 3.5 Real-Time Collaborative Editing
**Priority:** High | **Status:** Complete

**Description:** 
Allows multiple procurement officers to collaborate on a single large-scale order in real-time, preventing the "duplicate order" problem common in the legacy system.

**Functional Requirements:**
- **Operational Transformation (OT):** Use of an OT or CRDT (Conflict-free Replicated Data Type) approach to handle simultaneous edits to order quantities and shipping addresses.
- **Presence Indicators:** Visual avatars showing who is currently viewing or editing a specific field.
- **Locking Mechanism:** For highly sensitive fields (e.g., Total Price), a temporary "soft lock" is applied when a user begins typing.
- **WebSocket Integration:** Real-time communication via Django Channels and Redis.

**Technical Constraints:**
- State synchronization must occur within 200ms to avoid the perception of "lag" between collaborators.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token (`Authorization: Bearer <token>`).

### 4.1 `GET /api/v1/products`
**Description:** Retrieves a paginated list of available healthcare products.
- **Request Params:** `page` (int), `limit` (int), `category` (string)
- **Response (200 OK):**
```json
{
  "data": [
    {"id": "prod_001", "name": "Surgical Gloves", "price": 12.99, "sku": "SG-100"},
    {"id": "prod_002", "name": "Scalpel Handle", "price": 45.00, "sku": "SH-200"}
  ],
  "meta": {"total": 500, "page": 1, "limit": 20}
}
```

### 4.2 `POST /api/v1/orders`
**Description:** Creates a new procurement order.
- **Request Body:**
```json
{
  "client_id": "cl_99",
  "items": [{"product_id": "prod_001", "quantity": 10}, {"product_id": "prod_002", "quantity": 2}],
  "shipping_address_id": "addr_445"
}
```
- **Response (201 Created):**
```json
{
  "order_id": "ord_778899",
  "status": "pending",
  "total_amount": 219.90,
  "created_at": "2026-10-15T10:00:00Z"
}
```

### 4.3 `PATCH /api/v1/orders/{id}`
**Description:** Updates order details (e.g., quantity change).
- **Request Body:** `{"items": [{"product_id": "prod_001", "quantity": 15}]}`
- **Response (200 OK):** `{"order_id": "ord_778899", "status": "updated"}`

### 4.4 `GET /api/v1/inventory/{sku}`
**Description:** Checks real-time stock levels for a specific SKU.
- **Response (200 OK):** `{"sku": "SG-100", "stock_level": 450, "warehouse": "East-1"}`

### 4.5 `POST /api/v1/webhooks/subscribe`
**Description:** Registers a URL for event notifications.
- **Request Body:** `{"event": "order.shipped", "url": "https://client-webhook.com/receiver"}`
- **Response (201 Created):** `{"subscription_id": "sub_123"}`

### 4.6 `GET /api/v1/analytics/usage`
**Description:** Returns the current month's API consumption.
- **Response (200 OK):** `{"requests_made": 45000, "limit": 100000, "remaining": 55000}`

### 4.7 `DELETE /api/v1/sandbox/reset`
**Description:** Clears all data in the sandbox environment for the current user.
- **Response (204 No Content):** `{}`

### 4.8 `GET /api/v1/auth/session`
**Description:** Validates the current session and returns user permissions.
- **Response (200 OK):** `{"user": "Meera Park", "role": "Admin", "expires_at": "2026-10-15T12:00:00Z"}`

---

## 5. DATABASE SCHEMA

The database is implemented in PostgreSQL 15. All tables utilize `UUID` as the primary key to ensure scalability and prevent ID guessing.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role` | Core identity table. |
| `profiles` | `profile_id` | `user_id` | `full_name`, `phone`, `address` | Extended user metadata. |
| `products` | `product_id` | `category_id` | `sku`, `name`, `base_price` | Catalog of healthcare items. |
| `categories` | `category_id` | None | `category_name`, `description` | Product taxonomies. |
| `orders` | `order_id` | `user_id`, `status_id` | `total_price`, `created_at` | Core transaction record. |
| `order_items` | `item_id` | `order_id`, `product_id` | `quantity`, `unit_price` | Line items for each order. |
| `inventory` | `inv_id` | `product_id` | `stock_count`, `warehouse_id` | Current stock levels. |
| `warehouses` | `wh_id` | None | `location_code`, `manager_id` | Physical storage locations. |
| `api_keys` | `key_id` | `user_id` | `api_key_hash`, `tier`, `is_active` | Access control for the API. |
| `webhook_subs` | `sub_id` | `user_id` | `target_url`, `event_type` | Webhook registration list. |

### 5.2 Schema Relationships
- **Users $\rightarrow$ Profiles:** 1:1
- **Users $\rightarrow$ Orders:** 1:Many
- **Orders $\rightarrow$ OrderItems:** 1:Many
- **Products $\rightarrow$ OrderItems:** 1:Many
- **Products $\rightarrow$ Inventory:** 1:Many
- **Categories $\rightarrow$ Products:** 1:Many

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Jetstream utilizes three distinct environments to ensure that no unstable code ever reaches the healthcare providers.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature experimentation and local development.
- **Host:** Local Docker containers $\rightarrow$ Dev ECS Cluster.
- **Database:** Shared Dev PostgreSQL instance.
- **Deployment:** Continuous Integration (CI) on every git push.

#### 6.1.2 Staging (Staging)
- **Purpose:** Pre-production validation and regulatory review.
- **Host:** Staging ECS Cluster (Mirrors Prod specs).
- **Database:** Sanitized copy of Production data.
- **Deployment:** Weekly merges from `develop` branch. This environment is used for the "Regulatory Review" process.

#### 6.1.3 Production (Prod)
- **Purpose:** Live healthcare marketplace operations.
- **Host:** Production ECS Cluster across three AWS Availability Zones (AZs).
- **Database:** Multi-AZ RDS PostgreSQL with synchronous replication.
- **Deployment:** Quarterly releases. Zero-downtime deployment via Blue/Green deployment strategy.

### 6.2 Deployment Pipeline
1. **Build:** GitHub Actions compiles assets and runs unit tests.
2. **Stage:** Code is deployed to Staging for QA and UX research by Joelle Nakamura.
3. **Review:** Quarterly regulatory audit performed on the Staging environment.
4. **Promote:** After audit approval, the image is tagged `prod` and rolled out via AWS CodeDeploy using a Canary strategy (10% traffic $\rightarrow$ 100%).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tooling:** `pytest` and `django-test`.
- **Coverage Target:** 85% minimum.
- **Focus:** Logic in `services.py` and `models.py`. All API utility functions must have 100% coverage.

### 7.2 Integration Testing
- **Tooling:** `Postman` and `Pytest-Django`.
- **Focus:** Testing the flow between the API and the Database. Specifically, verifying that order creation correctly decrements inventory across multiple warehouses.
- **Mocking:** Third-party payment gateways and email services are mocked using `unittest.mock`.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** `Playwright`.
- **Focus:** Critical user journeys:
    - User Login $\rightarrow$ Product Search $\rightarrow$ Order Placement $\rightarrow$ Payment.
    - Offline mode: Disabling network in browser $\rightarrow$ Placing order $\rightarrow$ Re-enabling network $\rightarrow$ Verifying sync.
- **Execution:** Run on the Staging environment before every quarterly release.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Regulatory requirements change during development. | High | High | Hire a specialized contractor to reduce "bus factor" and ensure compliance knowledge is distributed. |
| **R2** | Budget cut of 30% in next fiscal quarter. | Medium | High | Escalate as a critical blocker in the next board meeting to secure locked funding. |
| **R3** | Data Processing Agreement (DPA) legal delay. | High | Medium | (Current Blocker) Follow up daily with Legal; implement "mock" data handlers in the interim. |
| **R4** | Technical debt: Inconsistent date formats. | High | Low | Implement a `DateTimeNormalizationLayer` middleware to standardize all inputs to ISO-8601. |
| **R5** | Zero-downtime failure during cutover. | Low | Critical | Implement a "Strangler Fig" pattern, migrating one module at a time rather than a "Big Bang" switch. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate project halt / Financial loss $> \$100k$.
- **High:** Significant delay / Requirement rewrite.
- **Medium:** Moderate delay / Budget reallocation.
- **Low:** Minor inconvenience / Technical debt.

---

## 9. TIMELINE & PHASES

Jetstream follows a phased approach to ensure stability. Due to the zero-downtime requirement, the "Cutover" phase is the most sensitive.

### 9.1 Phase 1: Foundation (Now $\rightarrow$ 2026-03-01)
- **Focus:** Infrastructure setup, Database schema finalization, and Webhook framework (Complete).
- **Dependencies:** Legal review of DPA (Blocked).

### 9.2 Phase 2: Core Feature Build (2026-03-01 $\rightarrow$ 2026-06-01)
- **Focus:** API Rate limiting, Customer API, and Offline-first mode development.
- **Milestone:** Feature freeze for the first regulatory review.

### 9.3 Phase 3: Stability & Validation (2026-06-01 $\rightarrow$ 2026-08-15)
- **Milestone 1 (2026-06-15):** Post-launch stability confirmed in Staging.
- **Milestone 2 (2026-08-15):** Architecture review complete.
- **Focus:** Load testing, security audits, and UX refinement by Joelle.

### 9.4 Phase 4: Production Rollout (2026-08-15 $\rightarrow$ 2026-10-15)
- **Milestone 3 (2026-10-15):** Full Production Launch.
- **Focus:** Blue/Green deployment, legacy data migration, and monitoring.

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom/Google Meet. Per team policy, these are not re-watched; only these summaries serve as the official record.*

### Meeting 1: Architecture Sync (2023-11-12)
- **Attendees:** Alejandro, Meera, Joelle, Sergei.
- **Discussion:** Discussion regarding the choice of micro-frontends. Meera expressed concern about state management across MFEs.
- **Decision:** Agreed to use a shared Redux store for global state and a custom event bus for inter-MFE communication.
- **Action Item:** Sergei to prototype the event bus by next Friday.

### Meeting 2: Budget and Risk Review (2023-12-05)
- **Attendees:** Alejandro, Oakmount Executive Board.
- **Discussion:** Alejandro raised the risk of a 30% budget cut in the next quarter. The board acknowledged the risk but did not provide a guarantee of funding.
- **Decision:** The budget cut is officially marked as a "Blocker" for the next phase of hiring.
- **Action Item:** Alejandro to provide a "Minimum Viable Product" (MVP) cost breakdown.

### Meeting 3: UX Research Findings (2024-01-20)
- **Attendees:** Joelle, Meera, Alejandro.
- **Discussion:** Joelle presented findings from the healthcare provider interviews. Users are frustrated with the legacy system's inability to work in low-signal areas.
- **Decision:** Prioritize the "Offline-First" mode as a critical launch blocker.
- **Action Item:** Meera to research IndexedDB integration strategies.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $3,000,000 USD

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $1,950,000 | Salaries for Alejandro, Meera, Joelle, and Contractor fees for Sergei. |
| **Infrastructure** | 15% | $450,000 | AWS ECS, RDS, ElastiCache, S3, and CloudFront costs over 3 years. |
| **Tools & Licensing** | 5% | $150,000 | IDEs, Postman Enterprise, Monitoring tools (Datadog/New Relic). |
| **Contingency** | 15% | $450,000 | Reserved for emergency contractor hires or infrastructure spikes. |

---

## 12. APPENDICES

### Appendix A: Date Normalization Layer
To resolve the technical debt of three different date formats (Epoch, ISO-8601, and `MM-DD-YYYY`), the following Python middleware is being implemented:

```python
class DateNormalizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Logic to scan request.POST and request.GET 
        # and convert all date-like strings to ISO-8601
        # before reaching the Django View.
        return self.get_response(request)
```

### Appendix B: Regulatory Review Checklist
Before any quarterly release, the following must be verified in the Staging environment:
1. **Audit Log Integrity:** Ensure all changes to order prices are logged with user IDs.
2. **Data Encryption:** Verify that all PII (Personally Identifiable Information) is encrypted at rest using AES-256.
3. **Access Control:** Confirm that "Basic" tier API keys cannot access "Enterprise" endpoints.
4. **Recovery Time Objective (RTO):** Verify that the system can be restored from backup within 4 hours.