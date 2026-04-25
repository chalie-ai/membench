# PROJECT SPECIFICATION: PROJECT HELIX
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2025  
**Project Lead:** Zara Oduya (Engineering Manager)  
**Company:** Hearthstone Software  
**Classification:** Internal / Confidential

---

## 1. EXECUTIVE SUMMARY

Project Helix represents a strategic pivot for Hearthstone Software, moving the organization into the high-growth agricultural technology (AgTech) vertical. The primary driver for this initiative is a cornerstone enterprise client—a global leader in seed distribution and crop management—who has committed to a recurring annual contract value (ACV) of $2,000,000. This commitment transforms Helix from a mere internal tool into a high-yield product vertical capable of scaling across the wider AgTech market.

The business justification for Helix is rooted in the urgent need for a centralized, secure, and multi-tenant platform that can manage complex agricultural data cycles while adhering to stringent regulatory standards. Currently, the client relies on fragmented legacy systems that lack real-time visibility and fail to meet modern security audits. By delivering a cohesive, ISO 27001-compliant environment, Hearthstone Software will not only secure the $2M annual revenue stream but also establish a competitive moat in the precision agriculture space.

The ROI projection is exceptionally high due to the lean nature of the initial investment. With a project budget of $150,000—a shoestring amount designed to minimize burn while maximizing delivery speed—the projected First Year Return on Investment (ROI) is approximately 1,233% (calculated as $[2M \text{ Revenue} - (\$150k \text{ Budget} + \text{Operational Overhead})] / \$150k \text{ Budget}$). 

However, the project is not without significant tension. We are operating in a high-pressure environment where a primary competitor is currently estimated to be two months ahead of our current development velocity. This creates a "winner-takes-all" dynamic for the enterprise client's long-term loyalty. To mitigate this, the team is prioritizing the core architectural integrity (multi-tenancy and security) over "nice-to-have" features. 

Helix will be delivered by a distributed team of 15 professionals across five countries, coordinated by Zara Oduya. The engineering philosophy is one of "disciplined agility," focusing on a clean monolith architecture to reduce deployment complexity while ensuring that module boundaries are strictly enforced to allow for future microservices decomposition if the product scales. Success will be measured by a customer Net Promoter Score (NPS) of >40 within the first quarter post-launch and the maintenance of a zero-critical-incident security record for the first twelve months.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Helix is designed as a **Clean Monolith**. We have consciously avoided the complexity of a distributed microservices architecture given the small budget and the distributed nature of the team. To prevent the monolith from becoming a "big ball of mud," the system is partitioned into logical modules (e.g., `Helix.Identity`, `Helix.Tenancy`, `Helix.Notifications`, `Helix.Search`). Communication between these modules occurs through internal service interfaces, ensuring that the business logic is decoupled from the infrastructure.

### 2.2 Technology Stack
*   **Language/Framework:** C# 12 / .NET 8 (Long Term Support)
*   **Database:** Azure SQL Database (Hyperscale tier for multi-tenant scaling)
*   **Compute:** Azure Functions (Serverless for background tasks and event-driven triggers)
*   **Identity:** Azure Active Directory (Entra ID) integration with custom hardware key support.
*   **Security:** ISO 27001 certified Azure environment; data encrypted at rest using AES-256 and in transit via TLS 1.3.
*   **CI/CD:** Azure DevOps Pipelines with automated gating.

### 2.3 System Diagram (ASCII Representation)

```text
[ Client Interface ] <--- HTTPS/TLS 1.3 ---> [ Azure Application Gateway ]
                                                        |
                                                        v
                                           [ Azure App Service (Helix Monolith) ]
                                           |      (C# / .NET 8)               |
                                           |----------------------------------|
                                           | [Module: Identity] <--- Auth/2FA  |
                                           | [Module: Tenancy]  <--- Isolation |
                                           | [Module: Search]    <--- Indexing |
                                           | [Module: Notify]    <--- Messaging |
                                           |----------------------------------|
                                                        |
          ________________________________________________|_______________________________________
         |                                                |                                       |
 [ Azure SQL Database ]                      [ Azure Functions ]                      [ External Services ]
 | - Tenant_A Schema                     |    | - Email Worker (SendGrid)           |    | - SMS Gateway (Twilio) |
 | - Tenant_B Schema                     |    | - Push Notification Worker         |    | - Hardware Key Auth   |
 | - Shared Global Tables                |    | - Search Indexer (Azure AI Search) |    | - Regulatory API     |
 |_______________________________________|    |_____________________________________|    |_______________________|
```

### 2.4 Data Isolation Strategy
To meet the "High Priority" requirement for multi-tenant data isolation, Helix utilizes a **Hybrid Sharding Model**. 
1.  **Shared Catalog:** A global database contains the `Tenants` table, mapping Client IDs to specific database shards or schema identifiers.
2.  **Logical Isolation:** Each tenant’s data is tagged with a `TenantId` (GUID). Every database query is passed through a Global Query Filter (implemented at the Entity Framework Core level) to ensure no data leakage between clients.
3.  **Physical Isolation (Optional):** For high-tier requirements, the architecture allows for a "Database-per-Tenant" configuration by updating the connection string in the `Tenants` catalog.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Multi-Tenant Data Isolation (Priority: High | Status: In Progress)
**Description:** The core foundation of Helix. This feature ensures that data belonging to different enterprise customers is logically and physically separated, preventing "cross-talk" or accidental data exposure.

**Technical Requirements:**
*   **Tenant Resolver:** A custom middleware must intercept every incoming request to extract the `TenantId` from the JWT (JSON Web Token) or a custom header (`X-Helix-Tenant-ID`).
*   **DbContext Filtering:** The .NET Entity Framework Core implementation must use `HasQueryFilter` on all entity types implementing `ITenantEntity`. This ensures that `SELECT * FROM Orders` automatically becomes `SELECT * FROM Orders WHERE TenantId = 'current-tenant-id'`.
*   **Schema Validation:** A nightly audit script must run to check for any records in the database that lack a `TenantId` or possess an invalid one.

**User Impact:** From the end-user perspective, this is invisible. However, for the administrator, it ensures that a user from "Farm A" can never possibly view the soil nutrient reports of "Farm B," even if they possess a direct URL to the resource.

**Implementation Detail:** The system will utilize Azure SQL's Row-Level Security (RLS) as a secondary layer of defense. We will define a security policy that restricts access to rows based on the `SESSION_CONTEXT` set by the application layer upon connection.

### 3.2 Two-Factor Authentication with Hardware Key Support (Priority: Medium | Status: In Progress)
**Description:** To meet the ISO 27001 requirements, Helix must implement a robust 2FA system. While standard TOTP (Time-based One-Time Password) is required, the enterprise client specifically demands support for hardware security keys (FIDO2/WebAuthn).

**Technical Requirements:**
*   **WebAuthn API:** Implementation of the FIDO2 protocol to allow users to register YubiKeys or Google Titan keys.
*   **Fallback Mechanism:** If a hardware key is lost, a secondary "Recovery Code" system (10 x 12-character alphanumeric codes) must be provided.
*   **Session Management:** 2FA must be challenged upon initial login and every 30 days thereafter, or if a login attempt is detected from a new IP address.

**User Flow:**
1. User enters username/password.
2. System detects 2FA is enabled.
3. User is prompted: "Insert your security key and tap the button."
4. The browser communicates with the hardware key via the WebAuthn API.
5. The server verifies the signed challenge and grants access.

**Security Note:** All 2FA secrets must be stored using an encrypted column in Azure SQL, with the encryption key managed by Azure Key Vault.

### 3.3 Advanced Search with Faceted Filtering (Priority: Medium | Status: In Design)
**Description:** Users need to navigate millions of agricultural data points (e.g., seed batches, weather logs, yield reports). A standard SQL `LIKE` query is insufficient.

**Technical Requirements:**
*   **Indexing Engine:** Integration with Azure AI Search (formerly Cognitive Search).
*   **Full-Text Indexing:** Implementation of an inverted index for all "Notes" and "Description" fields.
*   **Faceted Navigation:** The UI must provide a sidebar allowing users to filter by "Region," "Crop Type," "Date Range," and "Yield Bracket."
*   **Synchronization:** An Azure Function will trigger on `Insert/Update` events in the SQL database to update the search index in near real-time (latency < 5 seconds).

**Search Logic:**
The search will support "fuzzy matching" (Levenshtein distance of 2) to account for typos in botanical names or location identifiers. Results will be ranked based on relevance scores determined by the Azure AI Search algorithm.

### 3.4 Notification System (Priority: Medium | Status: Not Started)
**Description:** An omnichannel alerting system to notify users of critical events (e.g., "Frost Warning in Sector 4" or "Regulatory Deadline Approaching").

**Technical Requirements:**
*   **Dispatch Engine:** A centralized `NotificationService` that determines the priority of the message and selects the appropriate channel.
*   **Channels:**
    *   **Email:** Integrated via SendGrid.
    *   **SMS:** Integrated via Twilio.
    *   **In-App:** SignalR for real-time toast notifications.
    *   **Push:** Azure Notification Hubs for mobile devices.
*   **Preference Center:** A user-facing settings page where individuals can toggle which notifications they receive per channel.

**Example Scenario:** An automated sensor detects moisture levels below 10%. The system triggers a "Critical" alert. The engine sends a Push notification to the field manager's phone and an Email to the regional supervisor.

### 3.5 Customer-Facing API with Sandbox (Priority: Low | Status: Blocked)
**Description:** A set of RESTful endpoints allowing the client to integrate Helix data into their own internal dashboards. This includes a "Sandbox" environment where they can test calls without affecting production data.

**Technical Requirements:**
*   **Versioning:** All endpoints must be versioned (e.g., `/api/v1/crops`).
*   **Rate Limiting:** Implementation of a "leaky bucket" algorithm to limit requests to 1,000 per hour per API key.
*   **Sandbox Environment:** A separate Azure SQL database (replica) containing anonymized data where the client can perform destructive testing.
*   **Documentation:** Auto-generated Swagger/OpenAPI documentation.

**Current Blocker:** This feature is blocked pending the Legal Review of the Data Processing Agreement (DPA). The client is hesitant to open API access until the liability for data transit is legally codified.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a `Bearer` token in the Authorization header and a `X-Helix-Tenant-ID` header.

### 4.1 Authentication & Identity
**POST `/api/v1/auth/login`**
*   **Request:** `{ "username": "zara_oduya", "password": "********" }`
*   **Response:** `200 OK { "token": "eyJ...", "mfa_required": true }`

**POST `/api/v1/auth/mfa/verify`**
*   **Request:** `{ "mfa_token": "123456", "hardware_key_sig": "..." }`
*   **Response:** `200 OK { "token": "final_access_token_here" }`

### 4.2 Tenant & Data Management
**GET `/api/v1/tenants/profile`**
*   **Response:** `200 OK { "tenant_name": "Global AgCorp", "tier": "Enterprise", "region": "North America" }`

**GET `/api/v1/crops`**
*   **Request Params:** `?cropType=Corn&region=Midwest`
*   **Response:** `200 OK [ { "id": "C1", "type": "Corn", "yield": "180bu/ac" }, ... ]`

**POST `/api/v1/crops`**
*   **Request:** `{ "type": "Soybean", "planting_date": "2025-05-10", "batch_id": "B-99" }`
*   **Response:** `201 Created { "id": "C102" }`

### 4.3 Search & Notifications
**GET `/api/v1/search`**
*   **Request Params:** `?q=nutrient+deficiency&facet=region`
*   **Response:** `200 OK { "results": [...], "facets": { "region": { "Iowa": 50, "Nebraska": 30 } } }`

**POST `/api/v1/notifications/settings`**
*   **Request:** `{ "email_enabled": true, "sms_enabled": false, "push_enabled": true }`
*   **Response:** `200 OK { "status": "updated" }`

**GET `/api/v1/notifications/unread`**
*   **Response:** `200 OK [ { "id": "N1", "message": "Frost warning", "priority": "High" } ]`

---

## 5. DATABASE SCHEMA

The database uses a relational model. All tables except `GlobalTenants` and `SystemConfig` include a `TenantId` for isolation.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `GlobalTenants` | `TenantId (PK)`, `Name`, `CreatedAt` | 1:N $\rightarrow$ Users | Registry of all paying clients. |
| `Users` | `UserId (PK)`, `TenantId (FK)`, `Email` | N:1 $\rightarrow$ GlobalTenants | User account details. |
| `AuthKeys` | `KeyId (PK)`, `UserId (FK)`, `PublicKey` | N:1 $\rightarrow$ Users | FIDO2 public keys for 2FA. |
| `Crops` | `CropId (PK)`, `TenantId (FK)`, `Variety` | N:1 $\rightarrow$ GlobalTenants | Catalog of crop types. |
| `FieldPlots` | `PlotId (PK)`, `TenantId (FK)`, `GeoCoord` | N:1 $\rightarrow$ GlobalTenants | Physical location data. |
| `SoilReadings` | `ReadingId (PK)`, `PlotId (FK)`, `pHLevel` | N:1 $\rightarrow$ FieldPlots | Sensor data points. |
| `Notifications` | `NotifId (PK)`, `UserId (FK)`, `Content` | N:1 $\rightarrow$ Users | Log of all sent alerts. |
| `SearchIndexMap` | `MapId (PK)`, `EntityId`, `EntityType` | N:A | Links SQL IDs to AI Search IDs. |
| `AuditLogs` | `LogId (PK)`, `UserId (FK)`, `Action` | N:1 $\rightarrow$ Users | ISO 27001 required activity log. |
| `SystemConfig` | `ConfigKey (PK)`, `ConfigValue` | N:A | Global app settings. |

### 5.2 Relationship Logic
*   **Strict Multi-Tenancy:** Every query to `Crops`, `FieldPlots`, and `SoilReadings` must join on `GlobalTenants` or filter by `TenantId`.
*   **Cascading Deletes:** If a `GlobalTenant` is deleted, all associated `Users`, `Crops`, and `FieldPlots` must be purged (Hard Delete for GDPR/compliance).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
We utilize a three-tier environment strategy to ensure stability and compliance.

#### 6.1.1 Development (Dev)
*   **Purpose:** Daily integration and feature experimentation.
*   **Data:** Mocked data; no real client data is permitted here.
*   **Deployment:** Continuous deployment (CD) from the `develop` branch.
*   **Resources:** Low-cost B1-tier Azure App Service.

#### 6.1.2 Staging (QA/Pre-Prod)
*   **Purpose:** Final verification and UAT (User Acceptance Testing).
*   **Data:** Anonymized subsets of production data.
*   **Deployment:** Triggered by a Pull Request to the `release` branch.
*   **Resources:** Mirror of Production specifications to ensure performance parity.

#### 6.1.3 Production (Prod)
*   **Purpose:** Live client operations.
*   **Data:** Actual enterprise client data.
*   **Deployment:** Quarterly releases aligned with the regulatory review cycle.
*   **Resources:** High-availability (HA) cluster with geo-redundancy.

### 6.2 Release Cycle
Due to the agricultural industry's regulatory nature, we cannot use a "deploy daily" model. We follow a **Quarterly Release Train**:
1.  **Month 1:** Feature development and unit testing.
2.  **Month 2:** Integration testing and Internal QA.
3.  **Month 3:** Regulatory Review $\rightarrow$ Client Sign-off $\rightarrow$ Production Deployment.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Target:** 80% code coverage for business logic.
*   **Framework:** xUnit with Moq for dependency injection.
*   **Focus:** Validation logic, tenant resolution algorithms, and calculation engines for crop yields.

### 7.2 Integration Testing
*   **Target:** All API endpoints and Database interactions.
*   **Approach:** Using `WebApplicationFactory` to run an in-memory version of the API.
*   **Focus:** Ensuring that a request with `TenantA` credentials cannot return `TenantB` data (Cross-tenant leakage tests).

### 7.3 End-to-End (E2E) Testing
*   **Target:** Critical user paths (The "Happy Path").
*   **Framework:** Playwright.
*   **Focus:** User login $\rightarrow$ 2FA Challenge $\rightarrow$ Search for Crop $\rightarrow$ Trigger Notification.

### 7.4 Performance Testing
*   **Tool:** Azure Load Testing.
*   **Benchmark:** System must support 500 concurrent users with a response time $< 200\text{ms}$ for 95% of requests.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Competitor is 2 months ahead in market delivery. | High | Critical | Hire a specialized contractor to accelerate the Notification and Search modules, reducing the "bus factor" and increasing velocity. |
| R-02 | Key Architect leaving the company in 3 months. | Certain | High | Immediate implementation of a "Knowledge Transfer" sprint. Document all architectural workarounds in the internal Wiki and hold pair-programming sessions with Farah Moreau. |
| R-03 | Legal review of DPA causes delay in API launch. | Medium | Medium | Proceed with internal development of the API; use mocked data in the sandbox so the code is "ready-to-ship" the moment legal signs off. |
| R-04 | Budget overrun due to Azure costs. | Medium | Medium | Implement strict resource quotas and utilize "Reserved Instances" for the SQL database to lower costs. |
| R-05 | Distributed team communication breakdown. | Medium | Medium | Mandatory daily async updates in Slack; bi-weekly synchronous "Sync-Up" calls. |

---

## 9. TIMELINE & MILESTONES

### 9.1 Phase 1: Foundation (Oct 2025 - Mar 2026)
*   **Focus:** Multi-tenant isolation and 2FA.
*   **Dependencies:** Azure Environment setup, ISO 27001 audit.
*   **Milestone 1:** Stakeholder demo and sign-off (Target: 2026-03-15).

### 9.2 Phase 2: Feature Expansion (Mar 2026 - May 2026)
*   **Focus:** Advanced Search and Notification System.
*   **Dependencies:** Completion of the core data model.
*   **Milestone 2:** External beta with 10 pilot users (Target: 2026-05-15).

### 9.3 Phase 3: Stabilization & Handover (May 2026 - July 2026)
*   **Focus:** API Sandbox (pending legal), Bug scrubbing, Performance tuning.
*   **Dependencies:** Beta user feedback.
*   **Milestone 3:** Post-launch stability confirmed (Target: 2026-07-15).

---

## 10. MEETING NOTES

*Note: As per company culture, these are summaries of recorded video calls that are rarely rewatched.*

### Meeting 1: Architectural Alignment (Nov 12, 2025)
*   **Attendees:** Zara, Rafik, Luna, Farah.
*   **Discussion:** Debate over Microservices vs. Monolith. Farah expressed concern that a monolith would be harder to scale. Zara overruled, citing the $150k budget and the need for rapid delivery.
*   **Decision:** Proceed with a "Clean Monolith." Rafik to set up the Azure SQL Hyperscale instance to allow for future scaling.

### Meeting 2: The "Competitor Panic" Sync (Dec 05, 2025)
*   **Attendees:** Zara, Luna, Farah.
*   **Discussion:** News surfaced that "AgriCore" (competitor) has already demoed a similar search feature to the client. The team discussed cutting the API sandbox to focus on Search.
*   **Decision:** Keep the API as "Low Priority/Blocked" but move Search to "In Design." Zara approved hiring a contractor for a 3-month burst to catch up on the search indexer.

### Meeting 3: Security Review & 2FA (Jan 20, 2026)
*   **Attendees:** Zara, Rafik, Luna.
*   **Discussion:** Review of ISO 27001 requirements. Luna pointed out that the current UI for 2FA is clunky. Rafik mentioned that hardware key support (WebAuthn) is taking longer than expected due to browser compatibility issues in the client's legacy environments.
*   **Decision:** Implement a fallback TOTP (Authenticator App) option to ensure the client can at least log in while hardware key bugs are ironed out.

---

## 11. BUDGET BREAKDOWN

The total budget of **$150,000** is extremely tight for a team of 15. This budget covers *direct project expenses* (cloud and tools) and *contractor surge capacity*, while baseline salaries are covered by the general company overhead.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel (Contractors)** | $85,000 | 1x Senior Search Engineer (3 months) to mitigate Risk R-01. |
| **Azure Infrastructure** | $35,000 | SQL Hyperscale, App Services, AI Search, Functions (estimated for 1 year). |
| **Software Tools** | $12,000 | SendGrid, Twilio, JetBrains licenses, Playwright Cloud. |
| **Security Certification** | $10,000 | External ISO 27001 audit and compliance documentation. |
| **Contingency** | $8,000 | Emergency bug fixing or critical infrastructure scaling. |
| **TOTAL** | **$150,000** | |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist for Helix
To maintain certification, the following must be verified before the Milestone 1 demo:
1.  **Access Control:** All administrative access to the Production environment must be gated via Just-In-Time (JIT) access requests.
2.  **Encryption:** All database connection strings must be stored in Azure Key Vault, not in `appsettings.json`.
3.  **Logging:** All `DELETE` and `UPDATE` operations on `Crops` and `Users` tables must be mirrored to the `AuditLogs` table.
4.  **Backup:** Weekly full backups and daily incremental backups with a 30-day retention period.

### Appendix B: Hardware Key (FIDO2) Integration Details
The hardware key implementation will follow the **WebAuthn Level 2** specification.
*   **Registration:** The server generates a random challenge. The client (browser) passes this to the YubiKey. The YubiKey signs the challenge with its private key and returns a public key and signature.
*   **Authentication:** The server sends a new challenge. The YubiKey signs it. The server verifies the signature using the stored public key.
*   **Supported Keys:** YubiKey 5 Series, Google Titan, and Windows Hello/Apple TouchID.