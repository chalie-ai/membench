# PROJECT SPECIFICATION: PROJECT CAIRN
**Version:** 1.0.4  
**Status:** Formal Specification / Active  
**Company:** Nightjar Systems  
**Date:** October 24, 2024  
**Confidentiality:** Level 3 (Internal / Client Restricted)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Cairn represents a strategic pivot for Nightjar Systems, moving from a generalist energy software provider to a specialized powerhouse in the renewable energy sector. The catalyst for this migration is a singular, high-value enterprise client—a multinational renewable energy conglomerate—that has committed to a $2M annual recurring revenue (ARR) contract contingent upon the delivery of a scalable, secure, and compliant API gateway and microservices architecture.

Currently, Nightjar Systems operates on a fragmented legacy infrastructure consisting of three disparate tech stacks. While functional for small-to-medium deployments, this "Franken-stack" cannot support the 10x increase in load required by this new client. The business risk of remaining on the legacy system is twofold: the inability to meet Service Level Agreements (SLAs) for the $2M contract and the operational fragility caused by hardcoded configurations across 40+ files.

### 1.2 Project Objectives
The primary goal of Cairn is to migrate existing services into a unified API Gateway architecture utilizing a CQRS (Command Query Responsibility Segregation) pattern with Event Sourcing. This ensures that every state change in the renewable energy grid management system is auditable, a non-negotiable requirement for regulatory compliance and PCI DSS Level 1 certification.

### 1.3 ROI Projection
With a total project budget of $1.5M, the ROI is projected to be highly aggressive. The immediate return is the $2M annual contract, yielding a net positive return within the first year of production launch (December 15, 2025). Long-term ROI is calculated based on the ability to productize the Cairn architecture to attract additional enterprise clients in the renewable energy sector, potentially scaling the vertical to $10M ARR within 36 months.

### 1.4 Strategic Alignment
Cairn aligns with Nightjar’s goal of achieving market leadership in green-tech infrastructure. By implementing a robust notification system, offline-first capabilities, and multi-language support, Nightjar moves from being a tool provider to a platform provider.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Cairn utilizes a hybrid microservices architecture. To manage the complexity of inheriting three different stacks (Node.js/TypeScript, Go, and Python/Django), the project implements an API Gateway pattern to decouple the client-facing interface from the backend implementation.

**CQRS & Event Sourcing:** For audit-critical domains (billing, energy distribution logs, and user permissions), we employ CQRS.
- **Command Side:** Handles updates via an Event Store (PostgreSQL with JSONB events).
- **Query Side:** Read-optimized views stored in ElasticSearch and Redis for p95 response times under 200ms.

### 2.2 High-Level Component Diagram (ASCII)

```text
[ Client Applications ]  <-- (HTTPS/TLS 1.3)
          |
          v
[ API Gateway (Kong/Envoy) ]  <-- Auth, Rate Limiting, Routing
          |
    -----------------------------------------------------------------
    |                      |                        |               |
[ Auth Service ]    [ Notification Svc ]    [ Billing Service ] [ Energy Grid Svc ]
 (OIDC/SAML)         (Email/SMS/Push)        (PCI DSS Level 1)   (CQRS/Event Sourcing)
    |                      |                        |               |
    v                      v                        v               v
[ Redis Cache ]     [ RabbitMQ/Kafka ]       [ PostgreSQL ]    [ Event Store ]
                                                    |               |
                                            [ Stripe/Braintree ] <-- (External)
```

### 2.3 Stack Inheritance and Interoperability
The migration must bridge the following three legacy stacks:
1. **Legacy Stack A (Node.js 14 / MongoDB):** Handling user profiles and basic metadata.
2. **Legacy Stack B (Go 1.18 / PostgreSQL):** Handling high-frequency sensor data from renewable arrays.
3. **Legacy Stack C (Python 3.9 / Django / MySQL):** Handling legacy billing and reporting.

Interoperability is achieved via a standardized gRPC internal communication layer and a shared Protobuf definition repository to ensure type safety across languages.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Notification System (Priority: Critical)
**Status:** In Design | **Deadline:** 2025-08-15

The Notification System is a launch-blocker. It must provide a unified interface for dispatching alerts across four channels: Email, SMS, In-App, and Push. Given the renewable energy context, these notifications often include critical grid failure alerts that require 99.99% delivery reliability.

**Functional Requirements:**
- **Multi-Channel Routing:** A single event (e.g., `GRID_OVERLOAD`) must be routable to different channels based on user preferences.
- **Templating Engine:** Support for Handlebars templates with localization variables.
- **Retry Logic:** Exponential backoff for failed SMS/Email deliveries using a Dead Letter Queue (DLQ).
- **Preference Center:** Users must be able to toggle notifications per channel per event type.

**Technical Implementation:**
The system will use a producer-consumer pattern. The `Notification-Svc` will receive a request via the API Gateway, validate the user's notification preferences in the User Database, and push a message to RabbitMQ. Specialized workers for each provider (SendGrid for Email, Twilio for SMS, Firebase for Push) will consume these messages.

### 3.2 Offline-First Mode with Background Sync (Priority: High)
**Status:** In Design | **Deadline:** 2025-10-15

Field engineers in remote renewable energy sites often lack stable internet. The application must allow full data entry and system monitoring while offline, syncing changes once connectivity is restored.

**Functional Requirements:**
- **Local Persistence:** Use of IndexedDB (web) and SQLite (mobile) to mirror necessary state.
- **Conflict Resolution:** Implementation of "Last Write Wins" for non-critical data and "Semantic Merging" for critical grid configurations.
- **Delta Syncing:** Only modified fields (deltas) should be transmitted to reduce bandwidth usage.
- **Background Sync:** Utilization of Service Workers (Web) and WorkManager (Android) to push queued changes in the background.

**Technical Implementation:**
Every entity will include a `version_id` and a `last_modified_at` timestamp. When the client reconnects, it sends a `SyncRequest` containing a list of local changes. The server validates the `version_id`; if a conflict is detected (server version > client version), the server returns a `409 Conflict` with the current state, prompting a manual or automatic resolution based on business rules.

### 3.3 Localization and Internationalization (Priority: Medium)
**Status:** In Review | **Deadline:** 2025-10-15

To support the global nature of the enterprise client, the platform must support 12 languages, including English, Spanish, Mandarin, German, French, Japanese, Arabic, Portuguese, Hindi, Russian, Korean, and Italian.

**Functional Requirements:**
- **Dynamic Language Switching:** Ability to change language without restarting the application.
- **RTL Support:** Full UI support for Right-to-Left (RTL) languages, specifically Arabic.
- **Locale-Aware Formatting:** Proper formatting for dates, currency (USD, EUR, CNY), and units of measurement (kW vs MW).
- **Externalized Strings:** No hardcoded strings in the UI; all text must be fetched from a translation management system (TMS).

**Technical Implementation:**
We will implement the `i18next` framework. Translation files will be stored as JSON in a CDN. The API Gateway will detect the `Accept-Language` header and pass the locale context to the downstream microservices.

### 3.4 Automated Billing and Subscription Management (Priority: Low)
**Status:** Blocked | **Deadline:** 2025-12-15

This feature handles the recurring billing for the enterprise client and potential future sub-clients. It is currently blocked by pending legal review of the PCI DSS compliance scope.

**Functional Requirements:**
- **Subscription Tiers:** Support for Flat-rate, Usage-based (per kWh monitored), and Hybrid models.
- **Invoice Generation:** Automated PDF generation of monthly invoices.
- **Dunning Process:** Automated email sequences for failed payments.
- **Credit Card Vaulting:** Secure tokenization via Stripe/Braintree to avoid storing raw PANs.

**Technical Implementation:**
This service will strictly adhere to PCI DSS Level 1. No credit card data will touch Nightjar's primary database; instead, we will store `payment_method_tokens`. The billing engine will run as a cron-job every 24 hours to evaluate usage metrics from the Energy Grid service and trigger charges.

### 3.5 SSO Integration with SAML and OIDC (Priority: Medium)
**Status:** Not Started | **Deadline:** 2025-12-15

The enterprise client requires integration with their corporate identity provider (Okta/Azure AD).

**Functional Requirements:**
- **SAML 2.0 Support:** Support for Service Provider (SP) initiated SSO.
- **OIDC Integration:** Support for OpenID Connect flows for modern application access.
- **Just-In-Time (JIT) Provisioning:** Automatically create user accounts upon first successful SSO login.
- **Role Mapping:** Map SAML attributes (e.g., `groups`) to internal system roles (`Admin`, `Operator`, `Viewer`).

**Technical Implementation:**
We will integrate an identity broker (e.g., Keycloak or Auth0). The API Gateway will validate the JWT issued by the broker. For SAML, the broker will handle the XML exchange and translate the identity assertion into a standard JWT for our internal microservices.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests must include a `Authorization: Bearer <token>` header.

### 4.1 Notifications API
**POST** `/notifications/send`
- **Description:** Sends a notification to a specific user or group.
- **Request:**
  ```json
  {
    "user_id": "user_9921",
    "channel": ["email", "push"],
    "template_id": "grid_alert_01",
    "payload": { "location": "Sector 7G", "severity": "Critical" }
  }
  ```
- **Response (202 Accepted):**
  ```json
  { "notification_id": "notif_abc123", "status": "queued" }
  ```

**GET** `/notifications/preferences/{user_id}`
- **Description:** Retrieves user's notification settings.
- **Response (200 OK):**
  ```json
  {
    "user_id": "user_9921",
    "preferences": { "email": true, "sms": false, "push": true }
  }
  ```

### 4.2 Sync API
**POST** `/sync/push`
- **Description:** Pushes offline changes to the server.
- **Request:**
  ```json
  {
    "last_sync_timestamp": "2025-05-10T10:00:00Z",
    "changes": [
      { "entity": "sensor_read", "id": "s1", "action": "UPDATE", "data": { "val": 450.2 }, "version": 12 }
    ]
  }
  ```
- **Response (200 OK):**
  ```json
  { "sync_id": "sync_xyz789", "conflicts": [] }
  ```

**GET** `/sync/pull`
- **Description:** Fetches updates since the last sync.
- **Response (200 OK):**
  ```json
  {
    "server_timestamp": "2025-05-10T12:00:00Z",
    "updates": [ { "entity": "config", "id": "c1", "data": { "threshold": 500 } } ]
  }
  ```

### 4.3 Billing API
**GET** `/billing/subscription`
- **Description:** Retrieves current subscription status.
- **Response (200 OK):**
  ```json
  { "plan": "Enterprise_Platinum", "status": "active", "next_billing_date": "2025-12-01" }
  ```

**POST** `/billing/payment-method`
- **Description:** Updates the payment token.
- **Request:** `{ "payment_token": "tok_visa_123" }`
- **Response (200 OK):** `{ "status": "updated" }`

### 4.4 Identity API
**POST** `/auth/sso/saml/consume`
- **Description:** Consumes the SAML assertion from the IdP.
- **Request:** `{ "SAMLResponse": "PHNhbW...base64..." }`
- **Response (200 OK):** `{ "access_token": "jwt_token_here", "expires_in": 3600 }`

**POST** `/auth/sso/oidc/callback`
- **Description:** Handles OIDC callback code exchange.
- **Request:** `{ "code": "auth_code_123", "state": "xyz" }`
- **Response (200 OK):** `{ "access_token": "jwt_token_here" }`

---

## 5. DATABASE SCHEMA

The system utilizes a polyglot persistence strategy. Below is the relational schema for the primary PostgreSQL instance (used for the Command side and billing).

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` (UUID) | - | `email`, `password_hash`, `mfa_enabled` | Core user identity |
| `user_profiles` | `profile_id` (UUID) | `user_id` | `full_name`, `timezone`, `preferred_lang` | User metadata/localization |
| `notification_prefs` | `pref_id` (UUID) | `user_id` | `channel_type`, `is_enabled`, `event_category` | Per-user alert settings |
| `subscriptions` | `sub_id` (UUID) | `user_id` | `plan_id`, `status`, `start_date`, `end_date` | Billing status |
| `billing_plans` | `plan_id` (UUID) | - | `name`, `monthly_cost`, `currency`, `limit_kwh` | Pricing tiers |
| `payment_methods` | `pm_id` (UUID) | `user_id` | `gateway_token`, `last_four`, `expiry_date` | PCI-compliant tokens |
| `event_store` | `event_id` (BIGINT) | `aggregate_id` | `event_type`, `payload` (JSONB), `timestamp` | Audit trail/Event source |
| `grid_assets` | `asset_id` (UUID) | - | `asset_name`, `type` (Solar/Wind), `capacity` | Renewable energy assets |
| `asset_logs` | `log_id` (UUID) | `asset_id` | `value`, `timestamp`, `status_code` | Asset telemetry |
| `sso_mappings` | `map_id` (UUID) | `user_id` | `provider_id`, `external_uid`, `last_login` | SSO link to internal user |

### 5.2 Relationships
- **One-to-One:** `users` $\rightarrow$ `user_profiles`
- **One-to-Many:** `users` $\rightarrow$ `notification_prefs`
- **One-to-Many:** `users` $\rightarrow$ `subscriptions`
- **One-to-Many:** `grid_assets` $\rightarrow$ `asset_logs`
- **Many-to-One:** `event_store` $\rightarrow$ `grid_assets` (via `aggregate_id`)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Nightjar Systems employs a three-tier environment strategy to ensure stability and regulatory compliance.

**1. Development (Dev):**
- **Purpose:** Feature development and internal unit testing.
- **Infrastructure:** Dockerized containers on a local Kubernetes (minikube) or shared dev cluster.
- **Data:** Mock data and anonymized subsets of production.
- **Deployment:** Continuous Deployment (CD) on every merge to `develop` branch.

**2. Staging (Staging):**
- **Purpose:** User Acceptance Testing (UAT) and Regulatory Review.
- **Infrastructure:** Mirror of production (AWS EKS) with scaled-down nodes.
- **Data:** Sanitized production clones.
- **Deployment:** Triggered by successful release candidate (RC) tag.

**3. Production (Prod):**
- **Purpose:** Live client operations.
- **Infrastructure:** Multi-AZ AWS EKS cluster with Auto-scaling Groups. PCI-compliant VPC isolation for the billing service.
- **Data:** Encrypted at rest (AES-256) and in transit (TLS 1.3).
- **Deployment:** Quarterly releases aligned with regulatory cycles. Manual sign-off required from Olga Oduya (CTO).

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
1. **Lint/Test:** All PRs trigger `npm test` or `go test` and static analysis.
2. **Build:** Docker images are built and pushed to Amazon ECR.
3. **Deploy:** Helm charts are used to manage Kubernetes deployments.

### 6.3 Infrastructure Cost Management
Given the "no additional infrastructure budget" constraint for the 10x performance increase, we will implement:
- **Horizontal Pod Autoscaling (HPA):** Scaling based on CPU/Memory utilization.
- **Read-Replicas:** Offloading query traffic from the primary PostgreSQL instance to read-replicas.
- **Aggressive Caching:** Using Redis for the most frequent 20% of API calls (which account for 80% of traffic).

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Requirement:** 80% minimum code coverage for all new services.
- **Tools:** Jest (Node.js), Pytest (Python), Go Test (Go).
- **Focus:** Business logic, validation rules, and individual function outputs.

### 7.2 Integration Testing
- **Requirement:** All inter-service communication via gRPC/REST must be tested.
- **Tools:** Postman/Newman and Supertest.
- **Focus:** API Gateway routing, database transactions, and event propagation from the Command side to the Query side in the CQRS pattern.

### 7.3 End-to-End (E2E) Testing
- **Requirement:** Critical paths (e.g., "Payment $\rightarrow$ Subscription $\rightarrow$ Notification") must be automated.
- **Tools:** Playwright and Cypress.
- **Focus:** User journeys from the browser/mobile app through the Gateway to the backend and back.

### 7.4 Performance Testing
- **Requirement:** Validate p95 < 200ms under 10x peak load.
- **Tools:** k6.io and JMeter.
- **Scenario:** Simulate 10,000 concurrent users performing a mix of read/write operations on the energy grid assets.

### 7.5 Security Testing
- **Requirement:** Quarterly penetration testing and automated vulnerability scanning.
- **Tools:** OWASP ZAP and Snyk.
- **Focus:** PCI DSS compliance, SQL injection, and JWT hijacking.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Key architect leaving in 3 months | High | Critical | **Parallel-path:** Prototype an alternative architecture simultaneously to ensure no single point of failure in knowledge. | Olga Oduya |
| R-02 | 10x performance reqs with $0 budget increase | High | High | **Dedicated Owner:** Assign a performance lead to optimize query efficiency and implement aggressive caching/HPA. | Hessa Moreau |
| R-03 | Third-party API rate limits (Blocker) | Medium | Medium | Implement a request-queueing system and request increased limits from the provider. | Joelle Kim |
| R-04 | Hardcoded config values in 40+ files | High | Medium | **Configuration Migration:** Move all hardcoded values to AWS Secrets Manager/Parameter Store during Milestone 1. | Paz Liu |
| R-05 | PCI DSS Compliance failure | Low | Critical | Strict isolation of the billing service and quarterly external audits. | Paz Liu |

**Probability/Impact Matrix:**
- **Critical:** Potential project failure or total loss of $2M contract.
- **High:** Significant delay in milestones or failure to meet success metrics.
- **Medium:** Moderate impact on delivery; can be mitigated with extra effort.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions

**Phase 1: Foundation & Configuration (Now $\rightarrow$ 2025-08-15)**
- Focus: API Gateway setup, migrating hardcoded configurations to Parameter Store, and designing the Notification System.
- Dependency: Configuration migration must be complete before any microservice is deployed.

**Phase 2: Core Feature Implementation (2025-08-16 $\rightarrow$ 2025-10-15)**
- Focus: Notification system launch, Offline-first implementation, and Localization.
- Dependency: Notification system must be signed off by stakeholders for MVP.

**Phase 3: Compliance & Hardening (2025-10-16 $\rightarrow$ 2025-12-15)**
- Focus: SSO Integration, Billing system completion, and PCI DSS audit.
- Dependency: Staging environment must be mirrored to Production for final load tests.

### 9.2 Key Milestones

| Milestone | Target Date | Deliverable | Success Criteria |
| :--- | :--- | :--- | :--- |
| **M1: Stakeholder Demo** | 2025-08-15 | Working Gateway + Notification Prototype | Client sign-off on Notification UI/UX |
| **M2: MVP Feature-Complete**| 2025-10-15 | Full Offline-sync + 12 Languages | p95 < 200ms in Staging environment |
| **M3: Production Launch** | 2025-12-15 | Full System Deployment | PCI DSS Level 1 Certification attained |

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: Per company policy, decisions live in Slack threads. The following are synthesized summaries of critical decision threads.*

### Thread 1: The "Configuration Crisis" (Dated: 2024-11-02)
**Participants:** Olga, Hessa, Paz
- **Discussion:** Hessa pointed out that the inherited Django stack has database credentials hardcoded in `settings.py` across 12 different modules. Paz noted this is a major PCI violation.
- **Decision:** Olga decided that before any new features are built, the team must implement a `ConfigManager` class that fetches values from AWS Parameter Store.
- **Outcome:** This became a prerequisite for Milestone 1.

### Thread 2: Performance vs. Budget (Dated: 2024-11-15)
**Participants:** Olga, Hessa, Joelle
- **Discussion:** Joelle presented the load test results showing the current system crashes at 2x load. The client requires 10x. Olga confirmed there is no extra budget for larger AWS instances.
- **Decision:** Hessa proposed moving to CQRS for the `asset_logs` domain to prevent read-heavy queries from locking the primary database.
- **Outcome:** CQRS architecture adopted for audit-critical domains.

### Thread 3: The Architect Departure (Dated: 2024-12-01)
**Participants:** Olga, Paz, Hessa
- **Discussion:** The lead architect notified the company of their departure in 90 days. There is significant concern that the Event Sourcing logic is only in the architect's head.
- **Decision:** Olga mandated a "Parallel Path" strategy. While the architect finishes the current design, Hessa and Paz will build a simplified prototype using a different approach to ensure the project doesn't stall.
- **Outcome:** Risk R-01 added to register.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $975,000 | Salaries for 8 engineers across 2 time zones for 14 months. |
| **Infrastructure** | 20% | $300,000 | AWS EKS, RDS, ElastiCache, S3, and CloudFront. |
| **Tools & Licensing** | 8% | $120,000 | Datadog, Snyk, New Relic, and Twilio/SendGrid API costs. |
| **Contingency** | 7% | $105,000 | Emergency buffer for third-party API overages or hardware. |

**Financial Note:** The $2M annual contract from the enterprise client covers the $1.5M initial investment and provides a $500k profit margin in Year 1, ensuring the project is self-funding.

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist
To maintain the $2M contract, Project Cairn must adhere to the following for the Billing Service:
1. **Network Segmentation:** The billing microservice must reside in a separate VPC with strict Security Group rules.
2. **Data Encryption:** Use AES-256 for any sensitive data at rest; however, raw PANs (Primary Account Numbers) are strictly forbidden.
3. **Access Control:** MFA is required for all developers accessing the production billing environment.
4. **Logging:** All access to the `payment_methods` table must be logged to an immutable log stream (CloudWatch with S3 Glacier lock).

### Appendix B: Event Sourcing Payload Examples
For the `event_store` table, the `payload` field (JSONB) follows the following structure for Grid Asset updates:

**Event Type:** `ASSET_THRESHOLD_CHANGED`
```json
{
  "event_id": "evt_550e8400",
  "aggregate_id": "asset_solar_01",
  "timestamp": "2025-06-01T12:00:00Z",
  "version": 45,
  "data": {
    "old_value": 400.0,
    "new_value": 450.0,
    "changed_by": "user_9921",
    "reason": "Seasonal adjustment for summer peak"
  }
}
```

**Event Type:** `USER_NOTIFICATION_SETTING_UPDATED`
```json
{
  "event_id": "evt_771f9211",
  "aggregate_id": "user_9921",
  "timestamp": "2025-06-01T12:05:00Z",
  "version": 12,
  "data": {
    "channel": "sms",
    "previous_state": true,
    "new_state": false
  }
}
```