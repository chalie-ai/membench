Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document (PSD). 

***

# PROJECT SPECIFICATION: PROJECT GLACIER
**Document Version:** 1.0.4  
**Date:** October 24, 2024  
**Status:** Baseline / Active  
**Company:** Nightjar Systems  
**Classification:** Confidential / Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project "Glacier" represents a strategic pivot for Nightjar Systems. For the first time in company history, Nightjar is entering the Renewable Energy sector, specifically targeting the e-commerce marketplace niche. The goal is to build a "greenfield" product—a high-performance, scalable marketplace where providers of renewable energy hardware (solar arrays, wind turbines, battery storage) and professional installation services can connect with B2B and B2C consumers.

Unlike previous Nightjar ventures, Glacier is not an iteration of an existing tool but a ground-up build. The marketplace aims to standardize the procurement of green energy technology, reducing the friction of sourcing specialized components and ensuring regulatory compliance across different jurisdictions.

### 1.2 Business Justification
The global transition toward net-zero emissions has created a fragmented market of boutique renewable energy suppliers. There is currently no dominant "Amazon-style" marketplace that integrates logistics, installation certifications, and hardware procurement specifically for the renewable sector. By leveraging Nightjar Systems' expertise in high-availability systems, Glacier will bridge this gap.

The business justification rests on three pillars:
1. **Market Capture:** Entering a high-growth industry with an untapped digital procurement layer.
2. **Ecosystem Locking:** By providing the webhook framework for third-party energy management tools, Glacier becomes the "central nervous system" for energy procurement.
3. **Scalability:** The micro-frontend architecture allows Nightjar to spin up new "verticals" (e.g., Hydrogen, Geothermal) without rewriting the core engine.

### 1.3 ROI Projection
The budget for Project Glacier is set at $800,000. This is categorized as a "comfortable" budget for a 6-month build cycle. The ROI is projected based on a Transaction Fee Model (3.5% per transaction) and a Subscription Model for premium vendors.

*   **Conservative Projection:** 10,000 Monthly Active Users (MAU) within 6 months, leading to a Break-Even Point (BEP) at Month 14.
*   **Aggressive Projection:** 25,000 MAU within 6 months, with a BEP at Month 9.
*   **Net Present Value (NPV):** Estimated at $2.4M over 3 years, assuming a steady CAGR of 15% in the renewable energy hardware market.

### 1.4 Strategic Constraints
The project is constrained by a strict 2-person core execution team (despite a 4-person total allocation), a complex legacy stack inheritance, and a rigid requirement for EU data residency to satisfy GDPR and CCPA mandates.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Overview
Glacier utilizes a **Micro-Frontend (MFE) Architecture**. This design is critical because Nightjar Systems is inheriting three different legacy stacks (Stack A: React/TypeScript, Stack B: Vue/Node, Stack C: Angular/Java). Rather than a costly rewrite, these stacks will be encapsulated as independent micro-frontends communicating via a shared Event Bus and a Global State Manager.

### 2.2 Infrastructure Stack
- **Frontend:** Module Federation (Webpack 5) orchestrating the three inherited stacks.
- **Backend:** Distributed microservices utilizing gRPC for internal communication and REST/JSON for external API consumers.
- **Database:** PostgreSQL 15 (Primary), Redis 7.0 (Caching/Session), MongoDB 6.0 (Catalog/Product Metadata).
- **Deployment:** Continuous Deployment (CD) via GitLab CI/CD. Every merged PR to the `main` branch triggers an automated pipeline that deploys to production.
- **Data Residency:** All production databases are hosted in `eu-central-1` (Frankfurt) to ensure compliance with GDPR and CCPA.

### 2.3 ASCII Architecture Diagram
```text
[ USER BROWSER ] 
       |
       v
[ EDGE GATEWAY / LOAD BALANCER ] <--- (AWS CloudFront / Nginx)
       |
       +---------------------------------------+
       | [ SHELL APPLICATION (React) ]         | <--- Host App
       +---------------------------------------+
       |       |               |             |
 [ MFE 1: Shop ] [ MFE 2: Admin ] [ MFE 3: User ] <--- (Inherited Stacks)
 (Vue/Node)      (Angular/Java)  (React/TS)
       |               |               |
       +---------------+---------------+
                       |
              [ API GATEWAY / BFF ] <--- (BFF: Backend for Frontend)
                       |
       +---------------------------------------+
       | [ MICROSERVICES LAYER ]              |
       |  - Order Service (Java)              |
       |  - Payment Service (Node)             |
       |  - User Service (Go)                  |
       |  - Notification Service (Python)      |
       +---------------------------------------+
                       |
       +---------------------------------------+
       | [ DATA LAYER ]                       |
       | - PostgreSQL (RDBMS)                 | <--- (Raw SQL for Performance)
       | - MongoDB (Document Store)            |
       | - Redis (Caching)                    |
       +---------------------------------------+
```

### 2.4 The "Mixed Stack" Challenge
Because the team is inheriting three different stacks, the **Shell Application** acts as the orchestrator. It handles authentication and routing. When a user navigates to `/shop`, the Shell loads the Vue-based MFE. When they navigate to `/admin`, the Angular-based MFE is injected. This prevents the need for a massive migration while allowing the 2-person team to maintain independence.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Webhook Integration Framework (Priority: Critical)
**Status:** Not Started | **Launch Blocker:** Yes

**Description:**
The Webhook Integration Framework is the most critical component of Glacier. It allows third-party renewable energy management software (e.g., smart grid monitors, solar inverter dashboards) to receive real-time updates from the Glacier marketplace.

**Detailed Requirements:**
- **Event Triggering:** The system must support events such as `order.created`, `order.shipped`, `payment.failed`, and `vendor.updated`.
- **Payload Specification:** Every webhook must send a POST request with a JSON payload containing a `timestamp`, `event_type`, `object_id`, and the `data` payload.
- **Security (Signing):** To prevent spoofing, every request must include a `X-Glacier-Signature` header, which is an HMAC-SHA256 hash of the payload using a shared secret.
- **Retry Logic:** The system must implement an exponential backoff retry strategy. If a 3rd party endpoint returns a 5xx error, Glacier will retry at intervals of 1m, 5m, 15m, 1h, and 6h.
- **Developer Portal:** A UI within the Admin MFE where users can generate secret keys, register target URLs, and view a "Delivery Log" showing the response code of the last 100 attempts.

**Acceptance Criteria:**
- Ability to register a URL and receive a "Test Ping."
- Successful delivery of an `order.created` event within 2 seconds of a transaction.
- Automatic disabling of a webhook if it fails 10 consecutive times.

---

### 3.2 A/B Testing Framework (Priority: Medium)
**Status:** In Progress | **Launch Blocker:** No

**Description:**
The A/B testing framework is integrated directly into the Feature Flag system. This allows the team to roll out new UI components to a percentage of users without deploying new code.

**Detailed Requirements:**
- **Traffic Splitting:** The framework must support "Percentage-based Rollouts" (e.g., 10% of users see Version B).
- **Bucket Assignment:** Users must be consistently assigned to a bucket based on a hash of their `user_id`. This ensures a user does not see Version A on mobile and Version B on desktop.
- **Metric Tracking:** Integration with the analytics engine to track Conversion Rate (CR) and Average Order Value (AOV) for each variant.
- **Flag Overrides:** Ability for the Tech Lead (Vivaan) to force a specific user (by email) into a specific variant for QA testing.
- **Persistence:** Bucket assignments must be stored in Redis for fast lookup and persisted in PostgreSQL for long-term analysis.

**Acceptance Criteria:**
- A new feature flag can be created in the admin panel and assigned to 50% of the audience.
- No flicker during page load when the variant is applied.
- Analytics reports correctly separate the "Control" group from the "Treatment" group.

---

### 3.3 Notification System (Priority: Medium)
**Status:** Not Started | **Launch Blocker:** No

**Description:**
A centralized notification hub that manages all outbound communications across four channels: Email, SMS, In-app, and Push.

**Detailed Requirements:**
- **Template Engine:** Support for Handlebars.js templates. Templates must be stored in the database and editable by the Product Designer (Paz) without developer intervention.
- **Channel Routing:** A "Preference Center" where users can opt-out of specific channels (e.g., "Email: Yes", "SMS: No").
- **Queueing:** All notifications must be pushed to a RabbitMQ queue to prevent blocking the main request-response cycle.
- **Provider Agnostic:** The system must use a Strategy Pattern to switch between providers (e.g., SendGrid for email, Twilio for SMS, Firebase for Push).
- **Localization Integration:** Integration with the L10n system to ensure the notification is sent in the user's preferred language.

**Acceptance Criteria:**
- A "Payment Confirmed" email is sent within 30 seconds of a successful transaction.
- SMS notifications are only sent if the user has a verified phone number and has opted-in.
- In-app notifications appear in a "Bell" dropdown in the Shell Application.

---

### 3.4 Localization & Internationalization (Priority: Low)
**Status:** In Review | **Launch Blocker:** No

**Description:**
Support for 12 primary languages to facilitate the expansion of the renewable energy marketplace across Europe and North America.

**Detailed Requirements:**
- **Resource Bundles:** Use of JSON-based translation files (i18next) stored in a CDN for fast loading.
- **Dynamic Switching:** Users can change language via a dropdown in the footer. The change must be reflected immediately without a full page reload (using React Context or Vuex).
- **Currency Handling:** Automatic conversion of prices based on the locale. This requires integration with an exchange rate API.
- **Right-to-Left (RTL) Support:** The CSS framework must support RTL mirroring for languages such as Arabic.
- **Date/Time Formatting:** Use of `Intl.DateTimeFormat` to ensure dates are displayed according to local customs (DD/MM/YYYY vs MM/DD/YYYY).

**Acceptance Criteria:**
- All 12 supported languages are available in the UI.
- Price displays change from USD ($) to EUR (€) when the locale is switched to Germany.
- No "hard-coded" strings remain in the frontend codebase.

---

### 3.5 Workflow Automation Engine (Priority: Low)
**Status:** Blocked | **Launch Blocker:** No

**Description:**
A visual "If-This-Then-That" (IFTTT) rule builder allowing vendors to automate their store management.

**Detailed Requirements:**
- **Visual Rule Builder:** A drag-and-drop interface (likely using React Flow) where users can connect "Triggers" to "Actions."
- **Example Workflow:** "IF `Order Value` > $5,000 THEN `Send Email to Account Manager` AND `Set Priority to High`."
- **Rule Evaluation Engine:** A background worker that evaluates rules against incoming events from the Webhook framework.
- **Variable Injection:** Ability to use variables like `{{customer_name}}` or `{{order_total}}` within actions.
- **Conflict Resolution:** Logic to prevent infinite loops (e.g., Rule A triggers Rule B, which triggers Rule A).

**Acceptance Criteria:**
- User can create a rule and save it.
- The rule triggers the intended action within 5 minutes of the event.
- Error handling prevents the system from crashing when a rule contains a logical contradiction.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. All requests require a Bearer Token in the `Authorization` header.

### 4.1 `POST /api/v1/orders`
**Description:** Creates a new order in the marketplace.
- **Request Body:**
  ```json
  {
    "customer_id": "cust_9921",
    "items": [
      {"product_id": "solar_panel_01", "qty": 10},
      {"product_id": "bracket_kit_05", "qty": 1}
    ],
    "shipping_address_id": "addr_4412",
    "payment_method_id": "pm_8821"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "order_id": "ord_55012",
    "status": "pending",
    "total_amount": 4500.00,
    "currency": "USD",
    "estimated_delivery": "2025-08-10"
  }
  ```

### 4.2 `GET /api/v1/products`
**Description:** Retrieves a paginated list of products.
- **Query Params:** `page=1`, `limit=20`, `category=solar`, `sort=price_asc`
- **Response (200 OK):**
  ```json
  {
    "data": [
      {"id": "solar_panel_01", "name": "EcoSun 400W", "price": 250.00}
    ],
    "pagination": { "total": 150, "pages": 8 }
  }
  ```

### 4.3 `PUT /api/v1/webhooks/register`
**Description:** Registers a third-party URL for event notifications.
- **Request Body:**
  ```json
  {
    "target_url": "https://partner.com/webhooks/glacier",
    "events": ["order.created", "payment.failed"],
    "description": "Main ERP Sync"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "webhook_id": "wh_12345",
    "secret": "whsec_abc123xyz789"
  }
  ```

### 4.4 `GET /api/v1/users/me`
**Description:** Returns the profile of the currently authenticated user.
- **Response (200 OK):**
  ```json
  {
    "user_id": "usr_112",
    "email": "vivaan@nightjar.com",
    "role": "admin",
    "preferences": { "lang": "en-US", "currency": "USD" }
  }
  ```

### 4.5 `POST /api/v1/payments/capture`
**Description:** Finalizes a payment authorization.
- **Request Body:** `{"payment_intent_id": "pi_9988", "amount": 4500.00}`
- **Response (200 OK):** `{"status": "captured", "transaction_id": "txn_554"}`

### 4.6 `DELETE /api/v1/cart/{cart_id}`
**Description:** Clears a user's shopping cart.
- **Response (204 No Content):** Empty body.

### 4.7 `GET /api/v1/analytics/nps`
**Description:** Returns the current aggregated NPS score for the quarter.
- **Response (200 OK):** `{"current_nps": 42, "response_count": 1200}`

### 4.8 `PATCH /api/v1/feature-flags/{flag_id}`
**Description:** Updates the rollout percentage for a specific feature.
- **Request Body:** `{"rollout_percentage": 25}`
- **Response (200 OK):** `{"flag_id": "new_checkout_flow", "status": "updated"}`

---

## 5. DATABASE SCHEMA

The database is a hybrid model. Relational data (Orders, Users) is stored in PostgreSQL, while product catalogs (highly variable attributes) are stored in MongoDB.

### 5.1 PostgreSQL Tables (Relational)

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `password_hash`, `role`, `created_at` | Core user identity. |
| `addresses` | `addr_id` | `user_id` | `street`, `city`, `country`, `postal_code` | Shipping/Billing info. |
| `orders` | `order_id` | `user_id`, `addr_id` | `total_amount`, `status`, `created_at` | Order header. |
| `order_items` | `item_id` | `order_id`, `prod_id` | `quantity`, `unit_price` | Line items for orders. |
| `payments` | `pay_id` | `order_id` | `amount`, `provider`, `status`, `txn_id` | Transaction ledger. |
| `webhooks` | `wh_id` | `user_id` | `target_url`, `secret_hash`, `is_active` | Webhook configs. |
| `webhook_logs` | `log_id` | `wh_id` | `request_body`, `response_code`, `timestamp` | Audit trail for webhooks. |
| `feature_flags` | `flag_id` | None | `flag_name`, `rollout_pct`, `is_enabled` | A/B test controls. |
| `user_buckets` | `bucket_id` | `user_id`, `flag_id` | `variant` (A or B) | User-to-flag assignment. |
| `notification_prefs`| `pref_id` | `user_id` | `channel` (SMS/Email), `enabled` | Opt-in/out settings. |

### 5.2 MongoDB Collections (Document)
- **`products`**: Stores product details. Fields include `sku`, `name`, `description`, and a dynamic `attributes` object (e.g., `{"wattage": "400W", "cell_type": "Monocrystalline"}`).
- **`categories`**: Hierarchical structure for energy product categorization.

### 5.3 Critical Technical Debt Note
**Warning:** 30% of the queries in the `orders` and `payments` tables bypass the ORM using raw SQL for performance reasons. This makes any schema migration (e.g., adding a column to `orders`) highly dangerous, as the ORM-managed migrations will not update the raw SQL strings.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Glacier utilizes a three-tier environment system.

1. **Development (Dev):**
   - Used by developers for local and shared feature testing.
   - Database is reset weekly.
   - Deployments occur on every commit to feature branches.

2. **Staging (Stage):**
   - A mirror of the production environment.
   - Used for QA and Product Designer (Paz) approval.
   - Contains anonymized production data.
   - Deployments occur upon merge to the `develop` branch.

3. **Production (Prod):**
   - The live user-facing environment.
   - **Region:** `eu-central-1` (AWS Frankfurt) for GDPR compliance.
   - **CD Pipeline:** Every merged PR to `main` triggers an automated deployment.
   - **Blue-Green Deployment:** The system maintains two identical environments; traffic is shifted only after health checks pass.

### 6.2 Infrastructure as Code (IaC)
Terraform is used to manage the infrastructure. This ensures that the environment can be recreated from scratch in the event of a catastrophic failure.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Business logic, utility functions, and individual MFE components.
- **Tooling:** Jest for Frontend, JUnit for Java, PyTest for Python.
- **Requirement:** 80% code coverage minimum for all new services.

### 7.2 Integration Testing
- **Scope:** API contracts and service-to-service communication (e.g., Order $\rightarrow$ Payment).
- **Tooling:** Postman/Newman and Supertest.
- **Focus:** Ensuring the "Mixed Stack" interoperability is seamless.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Landing Page $\rightarrow$ Product Search $\rightarrow$ Checkout $\rightarrow$ Confirmation").
- **Tooling:** Cypress.
- **Frequency:** Run on every PR before it can be merged to `main`.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team has no experience with the mixed tech stack (React/Vue/Angular). | High | High | Build a contingency plan with a fallback monolithic architecture if MFEs fail. |
| R-02 | Performance requirements are 10x current capacity with $0 extra budget. | Medium | High | Engage an external consultant for an independent performance assessment. |
| R-03 | Raw SQL technical debt leads to migration failure. | High | Medium | Mandatory peer review for any schema change; use of a SQL migration tool with strict versioning. |
| R-04 | EU Data Residency laws change or become stricter. | Low | High | Use an abstracted data layer to allow moving residency to different regions quickly. |

**Probability/Impact Matrix:**
- **High/High:** Immediate attention required (R-01).
- **Medium/High:** Close monitoring required (R-02).
- **High/Medium:** Process-based mitigation (R-03).

---

## 9. TIMELINE & MILESTONES

### 9.1 Project Phases
- **Phase 1: Foundation (Month 1-2):** Set up the Shell Application, configure the three inherited stacks, and establish the CD pipeline.
- **Phase 2: Core Commerce (Month 3-4):** Implementation of the Product Catalog, Cart, and Order systems. Integration of Webhooks (Critical).
- **Phase 3: Optimization & Scale (Month 5-6):** A/B testing, Notification systems, L10n, and Performance tuning.

### 9.2 Critical Milestones
| Milestone | Target Date | Dependency | Success Criteria |
| :--- | :--- | :--- | :--- |
| M1: Performance Benchmarks | 2025-07-15 | IaC Setup | System handles 1k requests/sec with <200ms latency. |
| M2: Security Audit | 2025-09-15 | GDPR Config | Zero "Critical" or "High" vulnerabilities found by 3rd party auditor. |
| M3: Internal Alpha | 2025-11-15 | Webhook Framework | Internal staff can complete a full purchase cycle. |

---

## 10. MEETING NOTES

*Note: These are excerpts from the 200-page shared running document. The document is currently unsearchable due to its format.*

### Meeting 1: Architecture Alignment (Date: 2024-11-01)
**Attendees:** Vivaan, Tala, Paz, Eshan
- **Discussion:** Paz expressed concern that the UI consistency would suffer because of the three different frameworks (Vue, Angular, React).
- **Decision:** Vivaan decided to implement a shared CSS design system (Tailwind) that all MFEs must import. This ensures a unified "look and feel" regardless of the underlying framework.
- **Action Item:** Paz to deliver the Figma design system by Nov 10.

### Meeting 2: Performance Crisis (Date: 2024-12-15)
**Attendees:** Vivaan, Tala, Eshan
- **Discussion:** Tala reported that the ORM is causing massive bottlenecks in the `orders` table. Eshan suggested rewriting the queries in raw SQL to bypass the ORM abstraction.
- **Decision:** Vivaan approved the use of raw SQL for the 30% most critical queries to hit the M1 performance benchmark.
- **Warning:** Vivaan noted this increases the risk of future migrations failing.

### Meeting 3: Resource Planning (Date: 2025-01-20)
**Attendees:** Vivaan, Paz
- **Discussion:** A key developer (not listed in the primary team, but supporting infra) is on medical leave for 6 weeks.
- **Impact:** This has created a blocker for the Webhook framework's deployment pipeline.
- **Decision:** Eshan will be shifted from "UI Polish" to "Infra Support" to cover the gap, though he will require heavy supervision from Vivaan.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocated Amount | Description |
| :--- | :--- | :--- |
| **Personnel** | $550,000 | Salaries for Vivaan, Tala, Paz, and Eshan over 6 months. |
| **Infrastructure** | $120,000 | AWS EU-Central-1 hosting, MongoDB Atlas, Redis Cloud. |
| **Tools & Licenses** | $30,000 | JIRA, GitLab Premium, SendGrid, Twilio, Figma. |
| **Consultancy** | $40,000 | External Performance Consultant (Mitigation for Risk R-02). |
| **Contingency** | $60,000 | Reserve for emergency scaling or staffing gaps. |

---

## 12. APPENDICES

### Appendix A: Data Residency & GDPR Compliance Map
To ensure compliance, the following data mapping is implemented:
- **PII (Personally Identifiable Information):** Stored in `users` and `addresses` tables. Encrypted at rest using AES-256.
- **Right to be Forgotten:** A specialized script `purge_user_data.sql` is maintained to delete all associated records across PostgreSQL and MongoDB when a user requests account deletion.
- **Data Localization:** AWS Service Control Policies (SCPs) are configured to prevent any resource creation outside the `eu-central-1` region.

### Appendix B: Fallback Architecture Plan (Risk R-01 Mitigation)
In the event that the Micro-Frontend (MFE) approach leads to unmanageable latency or "dependency hell," the team will pivot to the following:
1. **The "Big Freeze":** Freeze all updates to the inherited stacks.
2. **The "Strangler Fig" Pattern:** Instead of a shell app, we will use a reverse proxy (Nginx) to route traffic.
3. **Gradual Migration:** One by one, the legacy stacks will be rewritten into a single React monolith, starting with the most critical path (the Shop).
4. **Timeline Impact:** This pivot would delay the Internal Alpha (M3) by approximately 8 weeks.