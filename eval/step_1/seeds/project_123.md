# PROJECT SPECIFICATION: PROJECT CORNICE
**Document Version:** 1.0.4  
**Status:** Draft / Formal Specification  
**Date:** October 24, 2023  
**Project Lead:** Callum Liu (Tech Lead)  
**Classification:** Confidential – Bridgewater Dynamics Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Cornice is a strategic, high-stakes R&D initiative undertaken by Bridgewater Dynamics to modernize the foundational digital infrastructure of our legal services platform. The project involves the migration of a monolithic legacy system into a distributed microservices architecture, governed by a custom-built API Gateway. By transitioning to a micro-frontend architecture, Bridgewater Dynamics aims to decouple the user interface into independent modules, allowing for rapid iteration and team ownership of specific legal service domains (e.g., litigation, corporate compliance, intellectual property).

### 1.2 Business Justification
The current legacy system is a "black box" of interdependent C# code that has become a bottleneck for business growth. As Bridgewater Dynamics scales its legal services globally, the inability to deploy updates without risking total system failure has become a critical liability. Project Cornice is designed as a "moonshot" project. While the immediate Return on Investment (ROI) is difficult to quantify due to the R&D nature of the architectural shift, the long-term strategic value is immense.

The primary business driver is the necessity for SOC 2 Type II compliance. Current infrastructure cannot meet the stringent audit requirements for data isolation and access control. By implementing a centralized API Gateway, we can enforce strict security policies, audit logging, and rate limiting at the edge, ensuring that sensitive legal data is handled according to international standards.

### 1.3 ROI Projection and Strategic Goals
The projected ROI is centered on operational efficiency and market expansion.
- **Efficiency Gain:** The primary success metric is a **50% reduction in manual processing time** for end users. By automating the routing of legal documents through a microservices layer, we expect to reduce the "time-to-completion" for standard legal filings from 14 business days to 7.
- **Revenue Growth:** Through the implementation of localization for 12 languages and an automated billing system, the project opens the door to non-English speaking markets (EU and APAC), with a projected revenue increase of $2.1M in the first 18 months post-launch.
- **Risk Mitigation:** The migration removes the "single point of failure" inherent in the monolith, reducing the cost of downtime from an estimated $50k/hour to less than $5k/hour.

Despite the uncertainty of the immediate ROI, the project carries strong executive sponsorship from the Board of Directors, viewing it as a flagship initiative to position Bridgewater Dynamics as a "Legal-Tech" leader rather than a traditional service provider.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Cornice utilizes a **Micro-Frontend (MFE)** architecture paired with a **Microservices Backend**. The goal is to ensure that the frontend teams (led by Anders Kim) can deploy UI updates independently of the backend services (led by Callum Liu). 

The stack is exclusively the Microsoft Ecosystem:
- **Language:** C# (.NET 8)
- **Database:** Azure SQL (Hyperscale)
- **Compute:** Azure Functions (Serverless) and Azure Kubernetes Service (AKS)
- **Gateway:** Custom .NET-based API Gateway leveraging YARP (Yet Another Reverse Proxy)

### 2.2 System Layout (ASCII Diagram Description)
The following represents the traffic flow from the end-user to the data layer:

```text
[ User Browser ] <---> [ Micro-Frontend Shell (React/TypeScript) ]
                               |
                               v
                    [ Azure Front Door / WAF ]
                               |
                               v
                    [ PROJECT CORNICE API GATEWAY ] 
             (Auth | Rate Limiting | Routing | Analytics)
                               |
        _______________________|_________________________
       |                       |                        |
[ Service: Billing ]    [ Service: Legal Docs ]   [ Service: User Mgmt ]
       |                       |                        |
[ Azure SQL DB 1 ]      [ Azure SQL DB 2 ]       [ Azure SQL DB 3 ]
       |_______________________|________________________|
                               |
                    [ Azure Service Bus / Event Grid ]
                               |
                    [ Analytics & Logging Engine ]
```

### 2.3 The API Gateway Logic
The Gateway acts as the "brains" of the system. It intercepts all incoming requests and performs the following sequence:
1. **Authentication:** Validates JWT tokens via Azure Active Directory.
2. **Rate Limiting:** Checks the `UsageAnalytics` table to see if the client has exceeded their tier (Critical Priority).
3. **Feature Flagging:** Checks the `FeatureFlags` table to determine if the user belongs to an A/B test group (High Priority).
4. **Routing:** Maps the request to the appropriate Azure Function or AKS pod.
5. **Transformation:** Normalizes date formats (addressing the technical debt of three disparate formats) before passing data to the client.

### 2.4 Deployment Strategy: The Weekly Release Train
To maintain stability and SOC 2 compliance, Cornice adheres to a **Strict Weekly Release Train**.
- **Schedule:** Deployments occur every Tuesday at 03:00 UTC.
- **The Rule:** If a feature misses the "cutoff" (Sunday 23:59 UTC), it waits for the next train.
- **No Hotfixes:** There are no emergency hotfixes outside the train. If a critical bug is found, it must be patched in the next Tuesday cycle. This ensures that the QA Lead (Wyatt Moreau) has a consistent window for regression testing.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 API Rate Limiting and Usage Analytics
**Priority:** Critical | **Status:** Not Started | **Launch Blocker:** Yes

**Description:**
The system must implement a sophisticated rate-limiting mechanism to prevent API abuse and ensure fair usage across different subscription tiers. This feature is the primary launch blocker because the current third-party API dependencies are triggering 429 (Too Many Requests) errors during testing, stalling the development of other services.

**Functional Requirements:**
- **Tiered Limits:** Implement three levels of access: *Basic* (100 requests/min), *Professional* (1,000 requests/min), and *Enterprise* (Unlimited/Custom).
- **Sliding Window Algorithm:** Use a sliding window counter to prevent "bursting" at the start of a minute.
- **Analytics Dashboard:** A real-time view for administrators to see which API keys are hitting limits most frequently.
- **Header Response:** Every API response must include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

**Technical Implementation:**
The Gateway will use a Redis cache (Azure Cache for Redis) to store request counts per API key. The logic will be implemented as a Middleware component in the .NET Gateway. When a request arrives, the middleware increments the key in Redis; if the value exceeds the tier threshold, it returns a `429 Too Many Requests` response.

**Success Criteria:**
- Zero 429 errors from downstream third-party providers (by implementing a queue-based throttle).
- Latency overhead for the rate-limiting check must be $< 15\text{ms}$.

---

### 3.2 A/B Testing Framework (Integrated Feature Flags)
**Priority:** High | **Status:** In Design

**Description:**
Instead of a standalone A/B testing tool, Cornice will bake experimentation directly into the feature flag system. This allows the product team to toggle features for specific percentages of the user base to measure the impact on the "Manual Processing Time" metric.

**Functional Requirements:**
- **Percentage Rollout:** Ability to enable a feature for $X\%$ of users.
- **User Segmentation:** Ability to target users based on their jurisdiction (e.g., only users in New York State).
- **Metric Tracking:** Integration with the Usage Analytics engine to compare the performance of "Version A" vs "Version B."
- **Automatic Kill-Switch:** If a feature flag causes a spike in 500-series errors, the system must automatically disable the flag.

**Technical Implementation:**
The `FeatureFlag` table in Azure SQL will contain a `RolloutPercentage` column and a `SegmentCriteria` JSON column. The API Gateway will hash the `UserId` and compare it against the percentage to determine which version of a microservice to route the request to.

**Success Criteria:**
- Ability to deploy a feature to 5% of the user base and promote it to 100% without a code deployment.

---

### 3.3 Localization and Internationalization (L10n/I18n)
**Priority:** Medium | **Status:** In Review

**Description:**
Bridgewater Dynamics is expanding into 12 languages (English, French, German, Spanish, Mandarin, Japanese, Korean, Italian, Portuguese, Arabic, Dutch, and Russian). This is not merely translating text but adapting date formats, currency, and legal terminology.

**Functional Requirements:**
- **Dynamic Resource Loading:** The Micro-Frontend shell must load translation files based on the user's `Accept-Language` header or profile settings.
- **UTF-8 Compliance:** Entire pipeline (SQL to Frontend) must support multi-byte characters (specifically for Mandarin and Arabic).
- **Right-to-Left (RTL) Support:** The UI must mirror for Arabic.
- **Legal Terminology Mapping:** A specialized dictionary to ensure "Attorney" is translated to the correct local legal equivalent.

**Technical Implementation:**
Use `.resx` files in .NET for backend messages and `i18next` for the React micro-frontends. A centralized `LocalizationService` will handle the mapping of legal terms.

**Success Criteria:**
- Full UI consistency across all 12 languages.
- Zero "mojibake" (character corruption) in the Azure SQL database.

---

### 3.4 Webhook Integration Framework
**Priority:** Medium | **Status:** In Design

**Description:**
To allow third-party legal tools (e.g., Clio, MyCase) to interact with Cornice, a webhook framework is required. This will allow Cornice to push real-time updates to external systems when a legal document status changes.

**Functional Requirements:**
- **Event Subscription:** A portal where users can register a URL and select which events they want to listen to (e.g., `document.signed`, `payment.received`).
- **Retry Logic:** Exponential backoff for failed deliveries (Retry at 1m, 5m, 30m, 2h).
- **Security:** HMAC signatures in the header of every webhook request to allow the receiver to verify the sender.
- **Delivery Logs:** A log of every webhook attempt and the response received from the third party.

**Technical Implementation:**
Azure Functions will be triggered by an Event Grid. The function will fetch the registered webhook URLs from the `WebhookSubscriptions` table and dispatch the payload via `HttpClient`.

**Success Criteria:**
- Delivery of 10,000 events per hour with a success rate of $99.9\%$.

---

### 3.5 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** In Review

**Description:**
The transition from a flat-fee model to a tiered subscription model requires an automated billing engine integrated into the API Gateway.

**Functional Requirements:**
- **Subscription Tiers:** Logic to manage *Basic*, *Professional*, and *Enterprise* plans.
- **Usage-Based Billing:** Integration with the Usage Analytics engine to charge per-request for "overages."
- **Invoice Generation:** Monthly PDF generation for clients.
- **Automatic Suspension:** If a payment fails twice, the API Gateway must automatically downgrade the user to "Read-Only" mode.

**Technical Implementation:**
Integration with Stripe API via a dedicated `BillingService`. The `SubscriptionStatus` will be cached in the API Gateway to avoid a database hit on every request.

**Success Criteria:**
- Zero manual intervention required for monthly billing cycles.
- Accurate reflection of usage-based charges in the final invoice.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints follow the base path: `https://api.bridgewater-dynamics.com/v1/`

### 4.1 Rate Limit Query
- **Endpoint:** `GET /gateway/usage/{apiKey}`
- **Description:** Returns current consumption for a specific key.
- **Request:** `GET /gateway/usage/bd_test_99283`
- **Response:**
  ```json
  {
    "apiKey": "bd_test_99283",
    "currentUsage": 450,
    "limit": 1000,
    "resetTime": "2026-03-15T12:00:00Z",
    "tier": "Professional"
  }
  ```

### 4.2 Update Feature Flag
- **Endpoint:** `POST /admin/feature-flags/update`
- **Description:** Updates the rollout percentage of a feature.
- **Request:**
  ```json
  {
    "featureId": "new-billing-ui",
    "rolloutPercentage": 25,
    "targetSegment": "US-East"
  }
  ```
- **Response:** `200 OK`

### 4.3 Localization Resource Fetch
- **Endpoint:** `GET /loc/strings/{langCode}`
- **Description:** Fetches translation keys for the frontend.
- **Request:** `GET /loc/strings/fr-CA`
- **Response:**
  ```json
  {
    "common.save": "Enregistrer",
    "legal.attorney": "Avocat",
    "billing.invoice": "Facture"
  }
  ```

### 4.4 Webhook Subscription
- **Endpoint:** `POST /webhooks/subscribe`
- **Description:** Registers a new endpoint for event notifications.
- **Request:**
  ```json
  {
    "callbackUrl": "https://client-app.com/webhook",
    "events": ["doc.signed", "doc.rejected"],
    "secret": "shh_secret_key"
  }
  ```
- **Response:** `201 Created`

### 4.5 Billing Tier Upgrade
- **Endpoint:** `PATCH /billing/subscription`
- **Description:** Upgrades the current user's plan.
- **Request:**
  ```json
  {
    "userId": "user_882",
    "newTier": "Enterprise",
    "paymentMethodId": "pm_12345"
  }
  ```
- **Response:** `200 OK`

### 4.6 Document Status Update (Internal)
- **Endpoint:** `PUT /docs/status/{docId}`
- **Description:** Updates status and triggers webhooks.
- **Request:**
  ```json
  {
    "status": "Signed",
    "timestamp": "2026-03-15T10:00:00Z"
  }
  ```
- **Response:** `200 OK`

### 4.7 Audit Log Export
- **Endpoint:** `GET /audit/logs?start=...&end=...`
- **Description:** Exports logs for SOC 2 compliance.
- **Request:** `GET /audit/logs?start=2026-01-01&end=2026-01-31`
- **Response:** `200 OK` (Returns CSV Stream)

### 4.8 User Profile Normalization
- **Endpoint:** `GET /users/profile/{id}`
- **Description:** Returns user data with normalized dates.
- **Request:** `GET /users/profile/101`
- **Response:**
  ```json
  {
    "name": "John Doe",
    "createdAt": "2026-03-15T00:00:00Z", 
    "lastLogin": "2026-03-14T22:15:00Z"
  }
  ```
  *(Note: Gateway ensures all dates are ISO 8601, regardless of source database format).*

---

## 5. DATABASE SCHEMA

The system utilizes Azure SQL with a distributed schema approach. Each microservice has its own logical schema to prevent coupling.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `UserId` | - | `Email`, `PasswordHash`, `MFAEnabled` | Core user identity. |
| `Subscriptions` | `SubId` | `UserId` | `TierId`, `StartDate`, `EndDate` | User's current plan. |
| `Tiers` | `TierId` | - | `TierName`, `MaxRequestsPerMin`, `MonthlyCost` | Definitions of Basic/Pro/Ent. |
| `UsageLogs` | `LogId` | `UserId` | `Timestamp`, `EndpointPath`, `ResponseCode` | Raw hit data for analytics. |
| `FeatureFlags` | `FlagId` | - | `FeatureName`, `IsActive`, `RolloutPct` | A/B testing controls. |
| `Localization` | `KeyId` | - | `LangCode`, `TranslationKey`, `Value` | Translation dictionary. |
| `Webhooks` | `WebhookId` | `UserId` | `TargetUrl`, `SecretKey`, `IsActive` | Third-party endpoint regs. |
| `WebhookEvents` | `EventId` | `WebhookId` | `Payload`, `AttemptCount`, `Status` | Delivery tracking logs. |
| `LegalDocuments` | `DocId` | `UserId` | `FilePath`, `CurrentStatus`, `Version` | Metadata for legal files. |
| `AuditTrail` | `AuditId` | `UserId` | `Action`, `IpAddress`, `Timestamp` | SOC 2 compliance logs. |

### 5.2 Key Relationships
- `Users` $\to$ `Subscriptions` (1:1)
- `Users` $\to$ `UsageLogs` (1:N)
- `Users` $\to$ `Webhooks` (1:N)
- `Webhooks` $\to$ `WebhookEvents` (1:N)
- `Tiers` $\to$ `Subscriptions` (1:N)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Specifications

#### Dev Environment (`dev.cornice.bd`)
- **Purpose:** Feature development and unit testing.
- **Infrastructure:** Shared Azure Function App, Smallest Azure SQL tier.
- **Data:** Anonymized sample data.
- **Deployment:** Continuous Integration (CI) trigger on every commit to `develop` branch.

#### Staging Environment (`stg.cornice.bd`)
- **Purpose:** Integration testing, QA validation, and UAT.
- **Infrastructure:** Mirror of Production (Sized at 50% capacity).
- **Data:** Sanitized production clones.
- **Deployment:** Deployment occurs every Monday for the "Weekly Release Train" verification.

#### Production Environment (`api.bridgewater-dynamics.com`)
- **Purpose:** Live legal services.
- **Infrastructure:** Multi-region Azure Kubernetes Service (AKS) with Azure SQL Hyperscale.
- **Data:** Live client data.
- **Deployment:** Tuesday 03:00 UTC via the Release Train.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is managed via **Terraform**. No manual changes in the Azure Portal are permitted. This ensures that the environment can be recreated from scratch in case of a regional failure, satisfying SOC 2 availability requirements.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Every single business logic method in the `.NET` services.
- **Tooling:** xUnit and Moq.
- **Requirement:** 80% code coverage is mandatory. Any PR that lowers coverage will be automatically blocked.

### 7.2 Integration Testing
- **Scope:** The interaction between the API Gateway and the Microservices.
- **Tooling:** Postman collections and Newman.
- **Focus:** Ensuring that the Rate Limiter and Feature Flags correctly intercept and route requests.
- **Critical Path:** Testing the "Three Date Format" normalization layer to ensure the Gateway consistently outputs ISO 8601.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "User signs up $\to$ Uploads Doc $\to$ Payment Processed $\to$ Webhook Fired").
- **Tooling:** Playwright.
- **Execution:** Run against the Staging environment every Monday.

### 7.4 SOC 2 Compliance Audit
Before the Production Launch (Milestone 2), an external audit firm will perform a penetration test and access review. The "AuditTrail" table must be proven immutable (no DELETE or UPDATE permissions for standard service accounts).

---

## 8. RISK REGISTER

| Risk | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Budget Cut (30%)** | High | High | **Contingency Plan:** If budget is cut, we will pivot to a "Thin Gateway" approach, removing the custom analytics engine and using Azure API Management (APIM) off-the-shelf. |
| **Vendor EOL** | Medium | High | **Consultant Engagement:** Engage an external architect to evaluate the feasibility of switching to an open-source alternative for the legacy dependency. |
| **Team Dysfunction** | High | Medium | **Siloed Communication:** Project Lead (Callum) and PM will communicate only via the shared running document to avoid conflict. |
| **Rate Limit Blockers** | High | Medium | **Virtualization:** Use WireMock to simulate third-party APIs during development to bypass current 429 limits. |
| **SOC 2 Failure** | Low | Critical | **Pre-Audit:** Perform a monthly "internal mock audit" starting in January 2026. |

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phases
- **Phase 1: Foundation (Oct 2023 - March 2026)**
  - Setup Gateway infrastructure.
  - Implement Rate Limiting.
  - Resolve date-format technical debt.
- **Phase 2: Feature Expansion (March 2026 - May 2026)**
  - Roll out A/B testing and Localization.
  - Integrate Billing and Webhooks.
- **Phase 3: Validation (May 2026 - July 2026)**
  - SOC 2 Audit.
  - Pilot user beta.

### 9.2 Key Milestones
| Milestone | Description | Target Date | Dependency |
| :--- | :--- | :--- | :--- |
| **M1** | Performance benchmarks met (Latency < 100ms) | 2026-03-15 | Rate Limiting Complete |
| **M2** | Production Launch (Full Release) | 2026-05-15 | SOC 2 Audit Pass |
| **M3** | External Beta (10 Pilot Users) | 2026-07-15 | Production Stability |

---

## 10. MEETING NOTES (Excerpt from Shared Document)

*Note: These notes are part of a 200-page unsearchable running document. The following are the most recent entries.*

### Meeting 1: 2023-11-12
**Attendees:** Callum Liu, Anders Kim, Wyatt Moreau, Mila Santos
**Topic:** The Date Format Crisis
- **Discussion:** Mila pointed out that the legacy system stores dates in `MM-DD-YYYY`, `YYYY/MM/DD`, and `Ticks`. This is causing the Frontend to crash randomly.
- **Decision:** Callum decided we will not fix this in the database. Instead, the API Gateway will have a "Normalization Layer" that converts everything to ISO 8601 before it hits the client.
- **Conflict:** Anders mentioned that the Frontend team doesn't trust the Gateway's logic. Callum stopped speaking and ended the meeting.

### Meeting 2: 2023-12-05
**Attendees:** Callum Liu, Wyatt Moreau, Mila Santos
**Topic:** Third-Party API Blockage
- **Discussion:** Wyatt reported that all E2E tests are failing because the third-party legal API is rate-limiting the staging environment.
- **Decision:** Since the Rate Limiter feature is "Not Started," we have no way to throttle our own requests. 
- **Action:** Callum will look into "Virtualizing" the API, but he needs the budget for a Mocking tool.

### Meeting 3: 2024-01-20
**Attendees:** Callum Liu, Anders Kim, Mila Santos
**Topic:** L10n vs I18n
- **Discussion:** Anders wants to use a third-party translation service to speed up the 12-language requirement.
- **Decision:** Callum rejected this due to SOC 2 concerns (sending legal data to a third-party translation API). We will use static `.resx` files.
- **Note:** Anders and Callum did not speak directly; all communication was routed through Mila.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,250,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,150,000 | 4 FTEs over 2.5 years, including benefits. |
| **Infrastructure** | 20% | $1,050,000 | Azure SQL Hyperscale, AKS, Redis, Front Door. |
| **Tools & Licenses** | 10% | $525,000 | Terraform Cloud, New Relic, Stripe Enterprise. |
| **Contingency** | 10% | $525,000 | Reserved for the 30% budget cut risk. |

---

## 12. APPENDICES

### Appendix A: Technical Debt Detail (Date Normalization)
The legacy system currently uses the following formats:
1. `System.DateTime.Ticks` (Long integer) - Used in the `AuditTrail` table.
2. `MM/dd/yyyy` - Used in the `Users` table.
3. `yyyy-MM-dd HH:mm:ss` - Used in the `LegalDocuments` table.

**Normalization Logic:**
The Gateway will utilize a `DateNormalizer` class:
```csharp
public string Normalize(object input) {
    if (input is long ticks) return DateTime.FromBinary(ticks).ToString("O");
    if (input is string s && s.Contains("/")) return DateTime.ParseExact(s, "MM/dd/yyyy", ...).ToString("O");
    // ... remaining logic
}
```

### Appendix B: SOC 2 Type II Control Mapping
To pass the audit, Project Cornice maps the following technical controls:
- **Control CC6.1 (Access Control):** API Gateway validates JWT tokens against Azure AD; no direct database access allowed from the internet.
- **Control CC6.7 (System Monitoring):** `UsageLogs` and `AuditTrail` tables capture all administrative changes.
- **Control CC7.1 (Vulnerability Management):** Weekly release train includes a mandatory Snyk scan for all NuGet dependencies.