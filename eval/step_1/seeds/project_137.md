# PROJECT SPECIFICATION DOCUMENT: PROJECT GLACIER
**Document Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active / In-Development  
**Classification:** Confidential – Internal Use Only  
**Company:** Hearthstone Software  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Glacier represents a critical strategic modernization effort for Hearthstone Software. The current healthcare e-commerce infrastructure operates on a legacy monolithic architecture that has reached its ceiling for scalability, maintainability, and security. In the highly regulated healthcare sector, the inability to pivot quickly to new compliance standards or integrate with emerging medical device ecosystems represents a significant business risk. 

The core objective of Glacier is the systematic decomposition of this monolith into a distributed microservices architecture over an 18-month transition period. By moving toward a CQRS (Command Query Responsibility Segregation) pattern and implementing event sourcing, Hearthstone Software ensures an immutable audit trail—a non-negotiable requirement for healthcare regulatory bodies. This transition allows for independent scaling of high-traffic services (such as product catalogs) without impacting sensitive transactional services (such as payment and patient data management).

### 1.2 ROI Projection
The projected Return on Investment (ROI) for Glacier is calculated based on three primary drivers:
1.  **Reduction in Operational Overhead:** By moving to microservices, the time-to-market for new features is expected to drop from 6 months to 6 weeks. This increased agility is estimated to capture an additional 12% in market share within the first 24 months.
2.  **Risk Mitigation (Compliance):** The implementation of strict GDPR and CCPA compliance, combined with EU-based data residency, eliminates the risk of potential fines which can reach up to 4% of global annual turnover under GDPR.
3.  **Infrastructure Efficiency:** While the project remains on-premise, the move to a streamlined microservices stack allows for better resource allocation within the data center, reducing hardware wastage by approximately 15%.

**Total Budget Allocation:** $1,500,000.00.
**Projected 3-Year Net Gain:** $3.2M based on increased throughput and reduced maintenance costs.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Glacier utilizes a Java/Spring Boot ecosystem deployed on an on-premise data center. To meet strict healthcare audit requirements, the architecture employs **CQRS (Command Query Responsibility Segregation)**. This separates the "Write" model (Commands) from the "Read" model (Queries), allowing each to scale independently and ensuring that the audit log (Event Store) is the single source of truth.

**Event Sourcing Implementation:**
Every state change in the system is captured as an event in an immutable Event Store. For example, instead of updating a "Patient Address" record, the system stores a `PatientAddressChanged` event. This allows for "time-travel" debugging and a perfect audit trail for regulatory inspections.

### 2.2 ASCII Architecture Diagram
```text
[ CLIENT LAYER ]
       |
       v
[ API GATEWAY (Spring Cloud Gateway) ]
       |
       +-----------------------+-----------------------+
       |                       |                       |
[ COMMAND SERVICE ]     [ QUERY SERVICE ]      [ AUTH SERVICE ]
(Write Model)            (Read Model)            (RBAC/2FA)
       |                       |                       |
       v                       v                       v
[ EVENT STORE (Oracle DB) ] <--- [ PROJECTION ENGINE ] <---+
       |                                                |
       +------------------------------------------------+
                               |
                    [ ON-PREMISE DATA CENTER ]
                    (EU Region - Strict Residency)
```

### 2.3 Technical Stack Specifications
- **Language:** Java 17 (LTS)
- **Framework:** Spring Boot 3.x, Spring Cloud
- **Database:** Oracle Database 21c (Enterprise Edition)
- **Messaging:** Apache Kafka (On-premise cluster) for event distribution
- **Build Tool:** Maven 3.8
- **Containerization:** Docker with on-premise Kubernetes (k8s) orchestration

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** High | **Status:** In Progress
**Description:** 
To meet healthcare security standards, the system must implement a robust 2FA mechanism. While software-based TOTP (Time-based One-Time Password) is standard, Glacier requires support for physical hardware keys (FIDO2/WebAuthn), such as YubiKeys, to prevent phishing attacks on high-privilege accounts.

**Functional Requirements:**
- Users must be able to register multiple hardware keys as backups.
- The system must support the WebAuthn API for browser-based hardware key authentication.
- Fallback mechanisms must be strictly defined; SMS is forbidden due to security vulnerabilities.
- Session timeouts must be enforced every 30 minutes of inactivity for administrative roles.

**Technical Implementation:**
The `AuthService` will manage the public key registration and challenge-response cycle. When a user attempts to login, the server generates a unique challenge. The hardware key signs this challenge using a private key, and the server verifies the signature against the stored public key in the Oracle DB.

**Acceptance Criteria:**
- Successful login using a YubiKey.
- Denial of access when an unregistered key is used.
- Ability for a user to revoke a lost hardware key via a secure recovery process.

---

### 3.2 Webhook Integration Framework
**Priority:** High | **Status:** In Review
**Description:** 
Glacier must allow third-party healthcare tools (e.g., electronic health record systems, billing software) to receive real-time notifications about marketplace events (e.g., `Order.Placed`, `Payment.Confirmed`, `Shipment.Delivered`).

**Functional Requirements:**
- A visual dashboard for users to register their webhook URLs.
- Support for "Secret" signatures (HMAC-SHA256) to allow the receiver to verify the authenticity of the payload.
- Automatic retry logic with exponential backoff (1min, 5min, 15min, 1hr).
- Delivery logs providing the exact payload and HTTP response code from the third party.

**Technical Implementation:**
A dedicated `WebhookDispatcher` service will listen to the Kafka event stream. When a relevant event occurs, the dispatcher retrieves the registered URLs from the Oracle DB, signs the payload using a shared secret, and transmits it via an asynchronous HTTP client.

**Acceptance Criteria:**
- Webhook fires within 5 seconds of the event occurring.
- Third-party tool correctly verifies the HMAC signature.
- System marks a webhook as "Disabled" after 10 consecutive failed delivery attempts.

---

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Medium | **Status:** In Review
**Description:** 
Allow non-technical administrators to create "If-This-Then-That" rules for order processing. For example: "If order value > $5,000 AND customer is in EU, then require Manual Compliance Review."

**Functional Requirements:**
- A drag-and-drop visual interface to define triggers and actions.
- Support for logical operators (AND, OR, NOT).
- Ability to test rules against a "Dry Run" dataset before deploying to production.
- Versioning of rules to allow rollbacks to previous logic.

**Technical Implementation:**
The engine will use a Rule-Engine pattern. Rules are stored as JSON logic trees in the database. The `WorkflowService` evaluates these trees against the current state of an order entity. The visual builder will be a React-based frontend that translates blocks into the JSON schema.

**Acceptance Criteria:**
- A rule created in the visual builder executes the correct action in the backend.
- The system correctly handles circular dependencies (e.g., Rule A triggers Rule B, which triggers Rule A).

---

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** In Progress
**Description:** 
Implementation of a secure identity management system to ensure that users only access data relevant to their role (e.g., Vendor, Customer, Compliance Officer, System Admin).

**Functional Requirements:**
- Granular permissions (e.g., `READ_PATIENT_DATA`, `UPDATE_INVENTORY`).
- Role hierarchy (Admin > Manager > Staff).
- Integration with the 2FA system for high-privilege role access.
- Audit logging of all permission changes.

**Technical Implementation:**
Utilizing Spring Security with a custom `UserDetailsService`. Roles and permissions are stored in a many-to-many relationship in the Oracle DB. JWT (JSON Web Tokens) will be used for session management, containing the user's roles in the claims section to minimize database hits on every request.

**Acceptance Criteria:**
- A user with the 'Customer' role is blocked from accessing the `/admin` endpoints.
- An administrator can assign a new role to a user and the change takes effect upon the next token refresh.

---

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low | **Status:** In Progress
**Description:** 
Expansion of the marketplace to support 12 specific languages (English, French, German, Spanish, Italian, Portuguese, Dutch, Polish, Swedish, Norwegian, Danish, and Finnish) to cater to the EU healthcare market.

**Functional Requirements:**
- Dynamic translation of all UI elements based on the `Accept-Language` header.
- Support for local currency formatting and date/time patterns.
- Right-to-left (RTL) support readiness (though not required for the initial 12 languages).
- Ability for admins to override specific translation keys via a management console.

**Technical Implementation:**
Standard Java `ResourceBundle` approach. Translation keys are stored in `.properties` files, with a fallback to English. For dynamic content (product descriptions), the Oracle DB uses a translation table linked by a `LanguageID` and `EntityID`.

**Acceptance Criteria:**
- Switching the language toggle updates all text on the page without a full reload.
- Prices are correctly formatted for the selected locale (e.g., using commas vs. periods for decimals).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned under `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 `POST /api/v1/auth/hardware-key/register`
**Description:** Registers a new FIDO2 hardware key for the authenticated user.
- **Request:**
  ```json
  {
    "keyId": "string",
    "publicKey": "string",
    "credentialId": "string",
    "transport": "usb|nfc|ble"
  }
  ```
- **Response (201 Created):**
  ```json
  { "status": "success", "keyId": "key_9928374" }
  ```

### 4.2 `POST /api/v1/auth/hardware-key/verify`
**Description:** Verifies a hardware key signature during login.
- **Request:**
  ```json
  {
    "challenge": "string",
    "signature": "string",
    "credentialId": "string"
  }
  ```
- **Response (200 OK):**
  ```json
  { "token": "jwt_access_token_here", "expiresIn": 3600 }
  ```

### 4.3 `POST /api/v1/webhooks/subscribe`
**Description:** Subscribes a third-party URL to a specific event.
- **Request:**
  ```json
  {
    "eventType": "ORDER_PLACED",
    "targetUrl": "https://client-api.com/webhook",
    "secret": "string_secret_key"
  }
  ```
- **Response (201 Created):**
  ```json
  { "subscriptionId": "sub_12345", "status": "active" }
  ```

### 4.4 `GET /api/v1/webhooks/logs/{subscriptionId}`
**Description:** Retrieves delivery logs for a specific webhook.
- **Response (200 OK):**
  ```json
  [
    { "timestamp": "2023-10-24T10:00:00Z", "statusCode": 200, "payload": "{...}" },
    { "timestamp": "2023-10-24T10:05:00Z", "statusCode": 500, "payload": "{...}" }
  ]
  ```

### 4.5 `POST /api/v1/workflow/rules`
**Description:** Creates a new automation rule.
- **Request:**
  ```json
  {
    "ruleName": "High Value EU Review",
    "trigger": "ORDER_CREATED",
    "conditions": { "all": [ { "fact": "amount", "operator": "greaterThan", "value": 5000 } ] },
    "action": "SET_STATUS_PENDING_REVIEW"
  }
  ```
- **Response (201 Created):**
  ```json
  { "ruleId": "rule_abc123", "status": "draft" }
  ```

### 4.6 `GET /api/v1/products`
**Description:** Retrieves a list of products (Query side of CQRS).
- **Query Params:** `lang=en`, `currency=EUR`
- **Response (200 OK):**
  ```json
  [ { "id": "prod_1", "name": "Medical Grade Scalpel", "price": 45.00, "currency": "EUR" } ]
  ```

### 4.7 `POST /api/v1/orders`
**Description:** Places a new order (Command side of CQRS).
- **Request:**
  ```json
  { "customerId": "cust_99", "items": [ { "productId": "prod_1", "qty": 1 } ] }
  ```
- **Response (202 Accepted):**
  ```json
  { "orderId": "ord_5544", "status": "processing" }
  ```

### 4.8 `PATCH /api/v1/users/roles`
**Description:** Updates the roles assigned to a user.
- **Request:**
  ```json
  { "userId": "user_77", "roles": ["VENDOR", "COMPLIANCE_OFFICER"] }
  ```
- **Response (200 OK):**
  ```json
  { "userId": "user_77", "updatedRoles": ["VENDOR", "COMPLIANCE_OFFICER"] }
  ```

---

## 5. DATABASE SCHEMA

The system uses an Oracle 21c database. Due to the CQRS pattern, we maintain separate tables for the Event Store (Immutable) and the Read Projections (Optimized for queries).

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationship | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `mfa_enabled` | 1:M with `user_roles` | Core user identity |
| `roles` | `role_id` | `role_name`, `permission_level` | M:M with `users` | RBAC role definitions |
| `user_roles` | `link_id` | `user_id`, `role_id` | Bridge Table | Maps users to roles |
| `hardware_keys` | `key_id` | `user_id`, `public_key`, `credential_id` | M:1 with `users` | FIDO2 key storage |
| `products` | `product_id`| `sku`, `base_price`, `category_id` | 1:M with `prod_trans` | Product master data |
| `prod_trans` | `trans_id` | `product_id`, `lang_id`, `translated_name`| M:1 with `products` | I18n Product translations |
| `orders` | `order_id` | `customer_id`, `total_amount`, `status` | 1:M with `order_items` | Order header (Read model) |
| `order_items` | `item_id` | `order_id`, `product_id`, `quantity` | M:1 with `orders` | Individual items in order |
| `event_store` | `event_id` | `aggregate_id`, `event_type`, `payload_json`, `timestamp`| N/A | **The Source of Truth** |
| `webhook_subs` | `sub_id` | `target_url`, `event_type`, `secret_key`, `status` | N/A | Third-party integrations |

### 5.2 Schema Constraints
- **Data Residency:** All tables are hosted on an Oracle RAC cluster located physically within the EU.
- **Auditability:** The `event_store` table is "Insert-Only." No UPDATE or DELETE operations are permitted on this table by any application user.
- **Indexing:** B-Tree indexes are applied to `user_id` and `order_id` to ensure sub-100ms query responses for the Read Model.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Glacier utilizes three distinct on-premise environments. Cloud-based alternatives (AWS/Azure/GCP) are strictly prohibited due to healthcare data residency requirements.

#### 6.1.1 Development (DEV)
- **Purpose:** Integration testing and feature development.
- **Specs:** 2x Virtual Machines, 16GB RAM, shared Oracle instance.
- **Deployment:** Automated via Jenkins pipeline on commit to `develop` branch.

#### 6.1.2 Staging (STG)
- **Purpose:** Final QA gate and UAT (User Acceptance Testing).
- **Specs:** Mirrors Production hardware (4x VMs, 64GB RAM, Dedicated Oracle instance).
- **Deployment:** Manual trigger from Jenkins after successful DEV tests.

#### 6.1.3 Production (PROD)
- **Purpose:** Live healthcare marketplace.
- **Specs:** High-Availability Cluster (8x VMs), Dual-node Oracle RAC for failover.
- **Deployment:** Manual QA Gate. All releases require a signed-off QA report. Turnaround for deployment is 2 business days.

### 6.2 Deployment Pipeline
1. **Build:** Maven compiles Java code $\rightarrow$ Docker image created.
2. **Dev Deploy:** Image pushed to on-premise registry $\rightarrow$ deployed to DEV.
3. **QA Gate:** Manual testing by the QA team in STG.
4. **Production Approval:** Tech Lead (Taj Liu) and PM sign-off.
5. **Prod Deploy:** Rolling update via Kubernetes to ensure zero downtime.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Target:** 80% minimum code coverage.
- **Focus:** Business logic within the Command handlers and Rule Engine logic.
- **Execution:** Runs on every push to the repository via CI.

### 7.2 Integration Testing
- **Framework:** Testcontainers (using an on-premise Oracle image).
- **Focus:** Database migrations, Kafka event propagation, and API endpoint connectivity.
- **Execution:** Runs once per day as a nightly build.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium and Playwright.
- **Focus:** Critical user journeys (e.g., "User logs in with 2FA $\rightarrow$ Places Order $\rightarrow$ Webhook fires").
- **Execution:** Manual QA gate in the Staging environment.

### 7.4 Security Testing
- **Penetration Testing:** Quarterly internal audits of the API Gateway.
- **Compliance Checks:** Automated scripts to verify that no data leaves the EU data center boundaries.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor is rotating out of their role | Medium | High | Hire a specialized contractor to broaden knowledge base and reduce "bus factor." |
| R-02 | Primary vendor product announced End-of-Life (EOL) | High | High | Engage an external consultant for an independent assessment of alternatives. |
| R-03 | Legal delay on Data Processing Agreement (DPA) | High | Medium | **CURRENT BLOCKER:** Escalate to Executive VP of Legal for expedited review. |
| R-04 | Team dysfunction (PM and Lead not speaking) | High | High | Mandatory mediated weekly syncs; documentation as the primary communication channel. |
| R-05 | On-premise hardware failure | Low | High | Implement Oracle RAC and redundant power/networking in the data center. |

**Probability/Impact Matrix:**
- **High/High:** Immediate Action (R-02, R-04)
- **Medium/High:** Close Monitoring (R-01)
- **High/Medium:** Management Escalation (R-03)

---

## 9. TIMELINE AND PHASES

### 9.1 Phase Breakdown
The project is divided into three primary phases over 18 months.

**Phase 1: Foundation & Core Services (Months 1-8)**
- Setup of on-premise K8s and Oracle RAC.
- Implementation of User Auth and RBAC (Priority Low).
- Development of the Event Store and CQRS baseline.
- *Dependency:* Completion of Legal DPA review.

**Phase 2: High-Security & Integration (Months 9-14)**
- Implementation of 2FA Hardware Key support (Priority High).
- Development of the Webhook Framework (Priority High).
- Initial rollout of Workflow Engine (Priority Medium).
- *Dependency:* Hardware key procurement for testing.

**Phase 3: Global Reach & Optimization (Months 15-18)**
- Implementation of I18n/L10n for 12 languages (Priority Low).
- Final performance tuning of Read Models.
- Full system stress testing.

### 9.2 Key Milestones
- **Milestone 1: MVP Feature-Complete** $\rightarrow$ Target: 2026-08-15
- **Milestone 2: External Beta (10 Pilot Users)** $\rightarrow$ Target: 2026-10-15
- **Milestone 3: Architecture Review Complete** $\rightarrow$ Target: 2026-12-15

---

## 10. MEETING NOTES

*Note: All meetings are recorded via video call. No team members currently rewatch these recordings. These notes are synthesized from the video transcripts.*

### Meeting 1: Architecture Alignment (2023-11-02)
- **Attendees:** Taj Liu, Vera Jensen, Camila Park.
- **Discussion:** Taj insisted on CQRS to ensure auditability. Vera expressed concern about the complexity of managing two different data models in Oracle.
- **Decision:** Taj overruled concerns; Event Sourcing is mandatory for healthcare compliance.
- **Conflict:** PM (absent) had previously suggested a simpler CRUD approach. Taj refuses to discuss this with the PM.

### Meeting 2: Security Review (2023-12-15)
- **Attendees:** Taj Liu, Omar Liu.
- **Discussion:** Discussion on whether SMS-based 2FA should be supported. Omar suggested it for "user ease."
- **Decision:** Taj rejected SMS completely, citing security risks. Only hardware keys and TOTP will be supported.
- **Outcome:** The team will begin sourcing YubiKeys for the beta phase.

### Meeting 3: Localization Strategy (2024-01-20)
- **Attendees:** Vera Jensen, Camila Park.
- **Discussion:** Camila noted that 12 languages are required, but the current budget for translation is low. Vera suggested using a hybrid of machine translation and manual review.
- **Decision:** L10n is marked as "Low Priority." The team will implement the framework first and populate the actual translations later.
- **Note:** No one informed the PM of this decision.

---

## 11. BUDGET BREAKDOWN

**Total Project Budget:** $1,500,000.00

| Category | Allocated Amount | Percentage | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | $850,000.00 | 56.7% | Tech Lead, Data Engineer, UX, Support, and Contractor. |
| **Infrastructure** | $300,000.00 | 20.0% | On-premise server hardware, Oracle Enterprise Licensing. |
| **Tools & Software** | $150,000.00 | 10.0% | Monitoring tools, Security scanners, FIDO2 hardware. |
| **External Consultants**| $100,000.00 | 6.7% | Vendor EOL assessment and Legal compliance audit. |
| **Contingency** | $100,000.00 | 6.6% | Reserved for emergency hardware replacement or legal fees. |

---

## 12. APPENDICES

### Appendix A: Event Schema Examples
To maintain the Event Store, all events must follow a strict JSON schema:
- `eventId`: UUID
- `aggregateId`: UUID (The ID of the entity, e.g., OrderID)
- `eventType`: String (e.g., `ORDER_SHIPPED`)
- `payload`: JSON Object (The actual change)
- `timestamp`: ISO-8601
- `version`: Integer (To track the sequence of events for a specific aggregate)

**Example Payload for `ORDER_PLACED`:**
```json
{
  "customerId": "cust_123",
  "items": [{"sku": "MED-SCA-01", "qty": 1}],
  "total": 45.00,
  "currency": "EUR"
}
```

### Appendix B: Hardware Key Integration Flow
1. **Registration Phase:**
   - Server sends `Challenge` $\rightarrow$ User taps Hardware Key $\rightarrow$ Key signs `Challenge` with private key $\rightarrow$ Server stores Public Key.
2. **Authentication Phase:**
   - Server sends `Challenge` $\rightarrow$ User taps Hardware Key $\rightarrow$ Key signs `Challenge` $\rightarrow$ Server verifies signature against stored Public Key $\rightarrow$ JWT Issued.
3. **Security Guard:**
   - All `/admin` requests are intercepted by a Spring Security Filter that checks if the JWT contains the `mfa_verified` claim. If absent, the request is redirected to the 2FA challenge page.