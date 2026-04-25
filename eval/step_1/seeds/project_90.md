# PROJECT SPECIFICATION: PROJECT HALCYON
**Document Version:** 1.0.4  
**Status:** Active / In-Development  
**Last Updated:** October 26, 2023  
**Classification:** Confidential – Internal Use Only (PCI DSS Level 1 Compliant)  
**Company:** Coral Reef Solutions  

---

## 1. EXECUTIVE SUMMARY

Project Halcyon represents a critical platform modernization effort for Coral Reef Solutions, an aerospace logistics and component provider. The primary objective is the strategic migration of the company’s legacy monolith architecture—currently struggling under technical debt and scaling limitations—into a high-performance microservices ecosystem. This migration is not merely a technical upgrade but a business necessity; the legacy system cannot support the projected growth in transaction volume nor the stringent latency requirements of modern aerospace procurement.

**Business Justification**  
The aerospace industry is shifting toward just-in-time (JIT) procurement and real-time inventory tracking. Our current monolith, while stable, suffers from "deployment dread," where a change in the billing module can inadvertently crash the inventory search engine. By transitioning to a Go-based microservices architecture orchestrated via Kubernetes on Google Cloud Platform (GCP), Coral Reef Solutions will achieve independent scalability, improved fault isolation, and a significantly faster time-to-market for new features.

**ROI Projection**  
The financial justification for Halcyon is driven by two primary KPIs: operational cost reduction and revenue enablement. 
1. **Cost Reduction:** The transition to CockroachDB and a containerized Go environment is projected to reduce the cost per transaction by 35%. By optimizing resource utilization and moving away from expensive legacy licensing, we anticipate a direct saving of $12,000/month in infrastructure overhead.
2. **Revenue Enablement:** The introduction of a customer-facing API with a dedicated sandbox environment will allow third-party aerospace partners to integrate directly with our catalog. We project that 80% feature adoption among pilot users will lead to a 15% increase in B2B order volume within the first six months post-launch.

With a stringent budget of $150,000, Halcyon is a "shoestring" operation. Every dollar is scrutinized. The project leverages a high-trust, low-ceremony team dynamic, utilizing an agile, Slack-driven decision process to avoid the overhead of excessive documentation and bureaucratic approvals. The 18-month roadmap ensures a gradual strangler-fig migration, minimizing risk to the existing revenue stream while steadily carving out functionality from the monolith.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Halcyon adopts a "Clean Monolith to Microservices" transition. The existing monolith has been logically partitioned into clear module boundaries, which allows the team to extract services without rewriting the entire business logic from scratch. 

**The Stack:**
- **Language:** Go (Golang) 1.21+ for all new microservices due to its concurrency primitives and low memory footprint.
- **Communication:** gRPC for internal service-to-service communication to ensure strict typing and high performance (Protocol Buffers v3).
- **Database:** CockroachDB (v23.1) for a distributed, SQL-compliant data store that ensures strong consistency across GCP regions.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform.
- **Gateway:** A custom Go-based API Gateway handling authentication, rate limiting, and request routing.

### 2.2 High-Level Component Diagram (ASCII)

```text
[ Client Apps / Third Party APIs ]
               |
               v
     +-----------------------+
     |  API Gateway (Go)     | <--- (Authentication, Versioning, Rate Limiting)
     +-----------------------+
               |
      _________|_______________________________________
     |                 |                |              |
     v                 v                v              v
[ Auth Service ] [ Search Service ] [ Order Service ] [ Tenant Service ]
     | (gRPC)           | (gRPC)           | (gRPC)           | (gRPC)
     |___________________|_________________|___________________|
                               |
                               v
                    +-----------------------+
                    | CockroachDB Cluster   | (Distributed SQL)
                    +-----------------------+
                               |
                    [ GCP Managed Storage / GCS ]
```

### 2.3 Data Flow and Security
Because Coral Reef Solutions processes credit card data directly, the architecture must adhere to **PCI DSS Level 1**. The "Order Service" and "Payment Module" are isolated in a restricted Kubernetes namespace with strict Network Policies. No other service has direct access to the payment tables in CockroachDB. All data at rest is encrypted using AES-256, and all data in transit is secured via TLS 1.3.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox (Priority: Critical | Status: Complete)
The core of Halcyon's external value is the developer portal and API. This system allows aerospace partners to query inventory and place orders programmatically.

**Detailed Specifications:**
- **Versioning Strategy:** The API uses URI versioning (e.g., `/v1/orders`). This ensures that breaking changes do not disrupt partner integrations.
- **Sandbox Environment:** A mirrored environment (`sandbox-api.coralreef.com`) is provided. It uses a separate CockroachDB cluster populated with synthetic data. This allows partners to test their integration without affecting production data.
- **API Keys:** Implementation of an `X-API-Key` header. Keys are rotated every 90 days per PCI DSS requirements.
- **Throttling:** Tiered rate limiting (Bronze: 100 req/min, Silver: 1000 req/min, Gold: 5000 req/min) implemented via a Redis-backed leaky bucket algorithm at the Gateway level.
- **Documentation:** Auto-generated Swagger/OpenAPI 3.0 specifications accessible via the developer portal.

### 3.2 Advanced Search with Faceted Filtering and Full-Text Indexing (Priority: Critical | Status: In Design)
Aerospace components often have thousands of permutations (part numbers, material grades, certifications). A standard SQL `LIKE` query is insufficient.

**Detailed Specifications:**
- **Indexing Engine:** Implementation of an inverted index strategy. While CockroachDB handles the primary data, the search service will utilize a sidecar pattern to synchronize data into a full-text search index.
- **Faceted Filtering:** Users must be able to filter by `Manufacturer`, `Certification` (e.g., AS9100), `Material`, and `Lead Time`. Each facet must return the count of matching items.
- **Full-Text Search:** Support for partial matches and "fuzzy" searching (Levenshtein distance) to account for common typos in part numbers.
- **Performance Target:** Search results must be returned in $< 200\text{ms}$ for queries across 10 million SKUs.
- **Caching:** Result sets for common searches (e.g., "Titanium Bolts") will be cached for 15 minutes in a distributed cache to reduce DB load.

### 3.3 Two-Factor Authentication (2FA) with Hardware Key Support (Priority: High | Status: Blocked)
Given the sensitivity of aerospace procurement and the PCI DSS Level 1 requirement, standard passwords are insufficient.

**Detailed Specifications:**
- **Multi-Modal Auth:** Support for TOTP (Time-based One-Time Password) via apps like Google Authenticator and hardware-based authentication via WebAuthn/FIDO2 (e.g., YubiKey).
- **Hardware Key Flow:** The system will prompt for a hardware key touch during high-value transactions (>$5,000) or when accessing administrative panels.
- **Recovery Codes:** Generation of 10 single-use recovery codes upon 2FA enrollment, stored using bcrypt hashing.
- **Session Management:** JWT (JSON Web Tokens) with a 15-minute expiration and a refresh token stored in a secure, HttpOnly cookie.
- **Blocker Note:** Currently blocked due to a disagreement between Tariq (Product) and the Engineering lead regarding whether to build a custom WebAuthn implementation or pay for a third-party identity provider (Okta/Auth0), given the tight budget.

### 3.4 Multi-Tenant Data Isolation with Shared Infrastructure (Priority: Medium | Status: In Review)
To scale, Coral Reef Solutions must support multiple sub-organizations (tenants) within a single installation without leaking data between them.

**Detailed Specifications:**
- **Isolation Strategy:** "Shared Schema, Discriminator Column." Every table in CockroachDB will include a `tenant_id` UUID. 
- **Row-Level Security (RLS):** Implementation of RLS policies at the database level to ensure that a request context carrying `tenant_id = A` can never see rows where `tenant_id = B`.
- **Tenant Provisioning:** A dedicated `Tenant Service` to handle the creation of new organizations, assigning them unique IDs and default configuration sets.
- **Resource Quotas:** Ability to limit the number of API requests or storage space per tenant to prevent "noisy neighbor" syndrome.
- **Migration Path:** A script to migrate existing monolith users into a "Default Tenant" to maintain backward compatibility.

### 3.5 Workflow Automation Engine with Visual Rule Builder (Priority: Medium | Status: Not Started)
A tool allowing users to automate procurement workflows (e.g., "If inventory of Part X falls below 10, notify Purchasing Manager and create a draft PO").

**Detailed Specifications:**
- **Rule Engine:** A Go-based interpreter that evaluates boolean logic expressions.
- **Visual Builder:** A frontend component (React) allowing users to drag and drop "Triggers" (e.g., Inventory Change) and "Actions" (e.g., Send Email).
- **Event-Driven Architecture:** Integration with a message bus (NATS or RabbitMQ) to trigger rules asynchronously when state changes occur in other microservices.
- **Cron Scheduling:** Support for time-based triggers (e.g., "Every Friday at 5 PM, generate a shortage report").
- **Audit Log:** Every automated action must be logged with a reference to the rule that triggered it for compliance auditing.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted under `api.coralreef.com`. Headers required for all: `Content-Type: application/json`, `X-API-Key: <key>`.

### 4.1 `GET /v1/catalog/search`
**Description:** Search for aerospace components using faceted filters.
- **Query Params:** `q` (string), `facet_material` (string), `facet_cert` (string), `page` (int).
- **Request Example:** `GET /v1/catalog/search?q=titanium+bolt&facet_cert=AS9100`
- **Response (200 OK):**
```json
{
  "results": [
    {"id": "part_992", "name": "Ti-6Al-4V Bolt", "price": 45.00, "stock": 120}
  ],
  "facets": {
    "material": {"Titanium": 12, "Steel": 45},
    "cert": {"AS9100": 5, "NADCAP": 2}
  },
  "total": 17
}
```

### 4.2 `POST /v1/orders`
**Description:** Create a new procurement order.
- **Request Body:**
```json
{
  "items": [{"part_id": "part_992", "qty": 10}],
  "shipping_address_id": "addr_441",
  "payment_method_token": "tok_pci_998877"
}
```
- **Response (201 Created):**
```json
{
  "order_id": "ord_556677",
  "status": "pending_payment",
  "estimated_delivery": "2025-05-01"
}
```

### 4.3 `GET /v1/orders/{order_id}`
**Description:** Retrieve status and details of a specific order.
- **Response (200 OK):**
```json
{
  "order_id": "ord_556677",
  "status": "shipped",
  "tracking_number": "FEDEX12345",
  "items": [...]
}
```

### 4.4 `POST /v1/auth/2fa/enroll`
**Description:** Begin the enrollment process for hardware keys.
- **Request Body:** `{"preferred_method": "webauthn"}`
- **Response (200 OK):**
```json
{
  "challenge": "base64_challenge_string",
  "user_id": "user_123"
}
```

### 4.5 `POST /v1/auth/2fa/verify`
**Description:** Verify a 2FA token or hardware key signature.
- **Request Body:** `{"token": "123456", "device_signature": "..."}`
- **Response (200 OK):** `{"authenticated": true, "session_token": "jwt_token_here"}`

### 4.6 `GET /v1/tenants/{tenant_id}/config`
**Description:** Retrieve tenant-specific configuration.
- **Response (200 OK):**
```json
{
  "tenant_id": "tenant_abc",
  "settings": {"currency": "USD", "region": "North America", "allow_sandbox": true}
}
```

### 4.7 `POST /v1/automation/rules`
**Description:** Create a new workflow automation rule.
- **Request Body:**
```json
{
  "name": "Low Stock Alert",
  "trigger": {"type": "inventory_below", "threshold": 10},
  "action": {"type": "email", "recipient": "procurement@company.com"}
}
```
- **Response (201 Created):** `{"rule_id": "rule_001", "status": "active"}`

### 4.8 `DELETE /v1/catalog/items/{item_id}`
**Description:** Remove an item from the catalog (Admin only).
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The system utilizes CockroachDB for global distribution and strong consistency. All tables use `UUID` as the primary key to avoid sequential ID predictability and facilitate merges.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `tenants` | `tenant_id` | `name`, `created_at`, `status` | One-to-Many with `users` | Core organization data |
| `users` | `user_id` | `tenant_id`, `email`, `password_hash` | Many-to-One with `tenants` | User account management |
| `user_mfa` | `mfa_id` | `user_id`, `method`, `secret_key` | One-to-One with `users` | 2FA state and keys |
| `products` | `product_id` | `tenant_id`, `sku`, `name`, `desc` | Many-to-One with `tenants` | Catalog items |
| `product_attrs`| `attr_id` | `product_id`, `key`, `value` | Many-to-One with `products`| Faceted attributes |
| `orders` | `order_id` | `tenant_id`, `user_id`, `status` | Many-to-One with `users` | Order header information |
| `order_items` | `item_id` | `order_id`, `product_id`, `qty` | Many-to-One with `orders` | Line items for orders |
| `payments` | `pay_id` | `order_id`, `token`, `amount`, `status` | One-to-One with `orders` | PCI sensitive payment refs |
| `automation_rules`| `rule_id` | `tenant_id`, `trigger_json`, `action_json`| Many-to-One with `tenants` | Workflow definitions |
| `audit_logs` | `log_id` | `tenant_id`, `user_id`, `action`, `ts` | Many-to-One with `users` | Compliance traceability |

### 5.2 Schema Relationships
- **Tenant Isolation:** The `tenant_id` is present in every primary table (`tenants`, `users`, `products`, `orders`, `automation_rules`, `audit_logs`). This is the primary key for the Row Level Security (RLS) implementation.
- **Payment Isolation:** The `payments` table is stored in a separate encrypted tablespace within CockroachDB, logically linked to `orders` but restricted by the Kubernetes namespace policy.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Halcyon utilizes three distinct environments to ensure stability and PCI compliance.

1. **Development (Dev):**
   - **Purpose:** Rapid iteration.
   - **Infrastructure:** Small GKE cluster with preemptible nodes to save costs.
   - **Database:** Single-node CockroachDB instance.
   - **Deployment:** Automatic on merge to `develop` branch.

2. **Staging (QA):**
   - **Purpose:** Mirror of production for final validation.
   - **Infrastructure:** GKE cluster matching production specs.
   - **Database:** 3-node CockroachDB cluster.
   - **Deployment:** Manual trigger. Requires a **2-day turnaround** for QA sign-off.

3. **Production (Prod):**
   - **Purpose:** Live customer traffic.
   - **Infrastructure:** Multi-regional GKE cluster across `us-east1` and `us-west1`.
   - **Database:** 6-node CockroachDB cluster with regional survival configuration.
   - **Deployment:** Strict manual QA gate. No code reaches production without Quinn Nakamura's explicit sign-off in Slack.

### 6.2 Deployment Pipeline
We use a GitOps approach with ArgoCD.
- **CI Pipeline:** GitHub Actions $\rightarrow$ Build Go Binary $\rightarrow$ Run Unit Tests $\rightarrow$ Push Docker Image to Google Artifact Registry.
- **CD Pipeline:** ArgoCD monitors the `halcyon-manifests` repo $\rightarrow$ Deploys to GKE.
- **QA Gate:** The "2-day turnaround" includes automated regression tests followed by a manual sanity check by the QA lead.

---

## 7. TESTING STRATEGY

Given the "shoestring" budget, testing must be highly automated to avoid expensive manual regressions.

### 7.1 Unit Testing
- **Approach:** Every Go package must have corresponding `_test.go` files.
- **Requirement:** Minimum 70% code coverage.
- **Tooling:** `go test -race` to detect concurrency issues common in Go microservices.
- **Mocking:** Use of `gomock` for gRPC interface mocking.

### 7.2 Integration Testing
- **Approach:** Testing the interaction between services and CockroachDB.
- **Tooling:** `Testcontainers` for Go. This spins up a real CockroachDB container during the test suite to ensure SQL queries are compatible with the distributed nature of the DB.
- **Focus:** API Gateway $\rightarrow$ Service $\rightarrow$ DB flow.

### 7.3 End-to-End (E2E) Testing
- **Approach:** Black-box testing of the entire system from the API Gateway.
- **Tooling:** Cypress for the Visual Rule Builder and Postman/Newman for API contract testing.
- **PCI Validation:** Specific E2E tests to ensure that payment tokens are never logged to `stdout` or stored in plain text.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Performance requirements are 10x current capacity with no extra budget | High | Critical | **Parallel-Path:** Prototype a more aggressive caching layer and evaluate Go's `sync.Pool` for memory optimization simultaneously with the standard build. |
| R2 | Team has no experience with Go/gRPC/K8s/CockroachDB | High | High | **De-scope:** If the team cannot hit Milestone 2 performance targets, the "Workflow Automation Engine" (Priority: Medium) will be removed from the initial launch. |
| R3 | PCI DSS Compliance failure during audit | Low | Critical | Weekly internal audits and strict isolation of payment namespaces in K8s. |
| R4 | Budget overrun due to GCP egress costs | Medium | Medium | Implement strict egress quotas and utilize Google's internal network for inter-service communication. |

**Impact Matrix:**
- **Critical:** Project cancellation or legal liability.
- **High:** Milestone delay $> 1$ month.
- **Medium:** Feature degradation or minor delay.

---

## 9. TIMELINE AND MILESTONES

Project Halcyon follows an 18-month migration window. The current phase focuses on the critical launch blockers.

### 9.1 Phase Schedule

| Phase | Focus | Start Date | End Date | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| Phase 1 | Infrastructure & API Gateway | 2024-11-01 | 2025-02-01 | None |
| Phase 2 | Core Services Migration (Search/Order) | 2025-02-01 | 2025-04-15 | Phase 1 |
| Phase 3 | Security Hardening & 2FA | 2025-04-15 | 2025-06-15 | Phase 2 |
| Phase 4 | Beta Testing & Optimization | 2025-06-15 | 2025-08-15 | Phase 3 |

### 9.2 Key Milestones
- **Milestone 1: Stakeholder demo and sign-off**  
  **Target Date:** 2025-04-15  
  *Criteria:* Functional API Gateway, working Search and Order services, and successful demo to VP of Product.
- **Milestone 2: Internal alpha release**  
  **Target Date:** 2025-06-15  
  *Criteria:* Deployment to Staging, 2FA (if unblocked), and 100% of critical features passing QA.
- **Milestone 3: Production launch**  
  **Target Date:** 2025-08-15  
  *Criteria:* Migration of first 10% of users to the new system, PCI audit sign-off.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Alignment
**Date:** 2023-11-12  
**Attendees:** Tariq Kim, Suki Costa, Quinn Nakamura, Hana Costa  
**Discussion:**  
- Discussion on whether to use a service mesh (Istio). Suki argued it adds too much complexity for a 12-person team.
- Tariq noted the budget constraints; Istio's resource overhead might increase GCP costs.
- Decision: Eschew service mesh for now; use basic K8s services and gRPC for internal comms.
**Action Items:**
- [Tariq] Define the final list of "Critical" versus "High" priorities. (Done)
- [Hana] Set up the initial GKE cluster in the Dev project. (Done)

### Meeting 2: The 2FA Deadlock
**Date:** 2023-12-05  
**Attendees:** Tariq Kim, Engineering Lead, Quinn Nakamura  
**Discussion:**  
- Engineering Lead wants to use an external provider (Okta) to save development time and ensure PCI compliance.
- Tariq rejects the cost ($\sim \$5\text{k}$/year) given the "shoestring" budget.
- Quinn expressed concern that a custom WebAuthn implementation might fail the PCI audit.
- **Result:** Decision deferred. Feature status moved to "Blocked."
**Action Items:**
- [Tariq] Look for cheaper identity alternatives. (Pending)
- [Engineering Lead] Prototype a basic WebAuthn flow to see if it's feasible. (Pending)

### Meeting 3: Performance Crisis and Debt
**Date:** 2024-01-20  
**Attendees:** Full Team  
**Discussion:**  
- Initial load tests on the Search service show latency at $800\text{ms}$, well above the $200\text{ms}$ target.
- The team identified a major technical debt issue: "No structured logging." 
- Debugging the performance spike took 6 hours because the team had to grep through raw `stdout` in Cloud Logging.
- Decision: Immediate pivot—Spiros and Hana to implement `uber-go/zap` for structured logging across all services before any further feature work.
**Action Items:**
- [Hana] Implement Zap logging middleware for the API Gateway. (Due Friday)
- [Suki] Update frontend to handle "Search Loading" states more gracefully. (Due Friday)

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $150,000  
**Fiscal Period:** 18 Months  

| Category | Allocated Amount | Description | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel (Contract)** | $85,000 | Hana Costa & specialized contractors | Primary cost driver; focused on Go/K8s expertise. |
| **Infrastructure (GCP)** | $35,000 | GKE, CockroachDB (Managed), Cloud Storage | Includes projected egress and storage costs. |
| **Tools & Licensing** | $15,000 | GitHub Enterprise, Datadog, Sentry | Critical for monitoring given the lack of logging. |
| **Contingency** | $15,000 | Buffer for emergency scaling or audit fees | To be released only by Tariq Kim's approval. |

**Budget Constraint Note:** Every dollar is scrutinized. Any request for additional tooling must be accompanied by a cost-benefit analysis showing a reduction in developer hours or a direct increase in transaction efficiency.

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Checklist for Halcyon
To maintain compliance, the following technical controls are mandated:
1. **Network Segmentation:** The `payment-service` must reside in a separate K8s namespace.
2. **No Plaintext PAN:** Primary Account Numbers (PAN) must never be logged to `stdout`.
3. **Rotation:** API keys and database credentials must be rotated every 90 days using GCP Secret Manager.
4. **Access Control:** SSH access to production nodes is disabled. All access is via `kubectl` with IAM-based RBAC.

### Appendix B: Go Project Structure (Standard Layout)
To maintain consistency across the 12-person team, all microservices must follow this structure:
```text
/cmd
  /server          # Main entry point
/internal
  /auth            # Private business logic
  /repository      # CockroachDB queries
  /service         # gRPC service implementations
  /models          # Shared structs
/api
  /proto           # .proto files for gRPC
/pkg
  /logger          # Shared zap logger wrapper
/deploy
  /k8s             # Helm charts / YAML manifests
```