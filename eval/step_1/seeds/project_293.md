Due to the extreme length requirement of this document (6,000–8,000 words), the following is a comprehensive, formal project specification for **Project Quorum**. This document serves as the "Single Source of Truth" (SSoT) for Pivot North Engineering.

***

# PROJECT SPECIFICATION: QUORUM
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Active/In-Development  
**Classification:** Confidential – Internal Only  
**Lead Authority:** Freya Gupta (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Quorum is a strategic initiative by Pivot North Engineering to modernize the core IoT infrastructure powering the company's retail operations. The existing legacy system, implemented 15 years ago, has become a critical liability. It is characterized by monolithic architecture, undocumented proprietary protocols, and a failure rate that is increasing as hardware ages. Because the entire retail operation depends on this system for inventory tracking, point-of-sale synchronization, and sensor-based warehouse management, there is a **zero-downtime tolerance** policy. Any failure in the migration process would result in an immediate cessation of retail operations, leading to catastrophic revenue loss.

The primary goal of Quorum is to transition from a rigid, fragile legacy environment to a cloud-native, event-driven architecture using the Microsoft stack. This will allow for greater scalability, improved security posture (GDPR/CCPA), and the ability to iterate on features without risking the stability of the entire network.

### 1.2 ROI Projection and Success Metrics
The financial justification for Quorum is centered on operational efficiency and cost reduction. The legacy system currently incurs high maintenance costs due to the scarcity of engineers familiar with the 15-year-old codebase and the expensive specialized hardware required to run the on-premise servers.

**Key Success Metrics:**
1.  **Cost Reduction:** The primary financial KPI is a **35% reduction in cost per transaction**. This will be achieved by migrating from expensive on-premise hardware to Azure’s consumption-based pricing model (Azure Functions) and optimizing the data pipeline via Kafka.
2.  **User Growth:** The system is designed to scale to **10,000 monthly active users (MAU)** within six months of the July 2025 launch.
3.  **Reliability:** Achieve 99.99% availability during the transition phase, ensuring no "dark periods" for retail stores.

**Projected ROI:**
Based on current operational expenditures (OpEx) of $1.2M annually for legacy maintenance, a 35% reduction in transaction costs, coupled with the elimination of on-site server maintenance, is projected to save Pivot North Engineering approximately $420,000 per year starting in FY2026. This ensures that the initial $400,000 investment is recouped within the first 12 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Stack
Quorum utilizes a full Microsoft ecosystem to ensure seamless integration and enterprise-grade support.
- **Language:** C# / .NET 8
- **Cloud Provider:** Microsoft Azure
- **Compute:** Azure Functions (Serverless) for event processing; Azure App Service for the API layer.
- **Database:** Azure SQL Database (Hyperscale tier) for relational data.
- **Messaging/Event Streaming:** Apache Kafka (Azure Event Hubs with Kafka surface).
- **Security:** Azure Active Directory (Azure AD) and Azure Key Vault.

### 2.2 Architectural Pattern
The system follows a **Microservices Architecture** with **Event-Driven Communication**. Instead of synchronous REST calls between internal services—which would create tight coupling and potential bottlenecks—services communicate by producing and consuming events via Kafka.

**ASCII Architecture Diagram:**
```text
[IoT Devices] ----(MQTT/HTTPS)----> [Azure IoT Hub]
                                        |
                                        v
[Kafka Event Bus] <---------------- [Ingestion Service]
       |
       +-----> [Device Management Service] ----> [Azure SQL]
       |
       +-----> [Billing/Transaction Service] --> [Azure SQL]
       |
       +-----> [Notification Service] ---------> [SendGrid/SMS]
       |
       +-----> [Analytics Service] -----------> [Azure Data Lake]
                                        ^
                                        |
[Customer API] <---(REST/OAuth2)--- [API Gateway]
```

### 2.3 Data Residency and Compliance
To comply with **GDPR (General Data Protection Regulation)** and **CCPA (California Consumer Privacy Act)**, Quorum implements a strict data residency policy. All primary data stores and backup vaults are located within the **Azure North Europe (Ireland)** and **West Europe (Netherlands)** regions. No PII (Personally Identifiable Information) is to be mirrored to US-based regions.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox
**Priority:** Critical | **Status:** Complete | **Launch Blocker:** Yes

The Customer-Facing API is the primary gateway for external vendors and internal retail partners to interact with the Quorum network. Because this is a launch blocker, the implementation focuses on extreme stability and backward compatibility.

**Specification:**
- **Versioning:** The API uses URI versioning (e.g., `/v1/devices`, `/v2/devices`). When a breaking change is introduced, a new version is spawned. The previous version is deprecated only after a 6-month sunset period.
- **Sandbox Environment:** A fully isolated "Sandbox" environment is provided. This mirrors the production environment but uses a mocked data layer. This allows customers to test their integrations without affecting real-world IoT hardware or incurring costs.
- **Authentication:** Secured via OAuth 2.0 and OpenID Connect.
- **Rate Limiting:** Implemented via Azure API Management (APIM) to prevent DDoS attacks and ensure fair usage (1,000 requests/min per client).

**Implementation Detail:**
The API is built as a series of .NET 8 Web APIs deployed to Azure App Service. Each endpoint is documented via Swagger/OpenAPI 3.0.

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Medium | **Status:** Complete

Given the critical nature of the retail infrastructure, standard password-based authentication is insufficient. Quorum implements a robust 2FA system to prevent unauthorized access to device configurations.

**Specification:**
- **Standard 2FA:** Support for TOTP (Time-based One-Time Password) via apps like Google Authenticator or Microsoft Authenticator.
- **Hardware Key Support:** Integration with FIDO2/WebAuthn standards, allowing the use of hardware keys (e.g., YubiKey). This is mandatory for users with "Administrator" or "Security Officer" roles.
- **Recovery Flow:** In the event of a lost hardware key, a secure recovery process involving the validation of two separate "Authorized Recovery Officers" (via a quorum-based approval system) is required.

**Implementation Detail:**
Authentication is handled by Azure AD B2C, with custom claims used to enforce the requirement of hardware keys for high-privileged accounts.

### 3.3 A/B Testing Framework within Feature Flag System
**Priority:** Medium | **Status:** Complete

To mitigate the risk of deploying new features to the entire retail network simultaneously, Quorum incorporates an A/B testing framework directly into its feature flagging logic.

**Specification:**
- **Feature Flags:** Managed via a centralized configuration service. Flags can be toggled globally or for specific subsets of devices/users.
- **A/B Logic:** The system can assign users to "Bucket A" (Control) or "Bucket B" (Experimental) based on a hash of their UserID.
- **Metric Tracking:** The framework integrates with the Analytics Service to track whether "Bucket B" results in a higher conversion rate or lower error rate compared to "Bucket A".
- **Gradual Rollout:** Support for "Canary Releases," where a feature is enabled for 1%, 5%, 10%, and then 100% of the network.

**Implementation Detail:**
Implemented using a custom C# middleware that intercepts requests and evaluates the user's assigned bucket against the current state of the `FeatureFlags` table in Azure SQL.

### 3.4 Advanced Search with Faceted Filtering and Full-Text Indexing
**Priority:** Low | **Status:** Complete

As the number of IoT devices grows into the thousands, simple keyword searches become inefficient. Quorum provides a high-performance search interface for administrators.

**Specification:**
- **Full-Text Indexing:** Utilizes Azure Cognitive Search for indexing device metadata, logs, and user profiles.
- **Faceted Filtering:** Allows users to filter devices by "Status" (Online/Offline), "Region" (EU-North/EU-West), "Device Type" (Sensor/Actuator), and "Firmware Version."
- **Search Latency:** The system is tuned to return results within <200ms for queries across 1 million records.

**Implementation Detail:**
The search service is a standalone microservice that syncs data from the Azure SQL database to the Azure Cognitive Search index via an event-driven trigger in Kafka.

### 3.5 Localization and Internationalization (L10n/I18n)
**Priority:** Low | **Status:** Blocked

The goal is to support 12 different languages to accommodate the global nature of the retail company's workforce.

**Specification:**
- **Target Languages:** English, French, German, Spanish, Italian, Dutch, Polish, Swedish, Finnish, Danish, Portuguese, and Turkish.
- **Mechanism:** Use of `.resx` files in .NET for static strings and a `LocalizedStrings` table in Azure SQL for dynamic content.
- **UTF-8 Compliance:** Full support for non-Latin character sets.

**Current Blocker:** This feature is currently blocked due to the delay in receiving translated string assets from the external localization agency and the ongoing infrastructure provisioning delays from the cloud provider, which prevents the setup of the multi-region content delivery network (CDN).

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 `GET /devices`
**Description:** Retrieves a list of all IoT devices the user has permission to view.
- **Request Parameters:** `?status=online`, `?region=EU-North`, `?page=1`, `?pageSize=50`
- **Response (200 OK):**
```json
[
  {
    "deviceId": "DEV-9901",
    "status": "Online",
    "lastSeen": "2023-10-24T10:00:00Z",
    "firmwareVersion": "2.4.1"
  }
]
```

### 4.2 `POST /devices`
**Description:** Provisions a new device into the Quorum network.
- **Request Body:**
```json
{
  "deviceModel": "SENSE-X1",
  "locationId": "STORE-442",
  "initialConfig": { "sampleRate": "10s" }
}
```
- **Response (201 Created):**
```json
{ "deviceId": "DEV-10234", "provisioningStatus": "Pending" }
```

### 4.3 `PATCH /devices/{deviceId}`
**Description:** Updates the configuration of a specific device.
- **Request Body:**
```json
{ "sampleRate": "30s", "powerMode": "Eco" }
```
- **Response (200 OK):**
```json
{ "deviceId": "DEV-10234", "updatedAt": "2023-10-24T12:00:00Z" }
```

### 4.4 `GET /analytics/transactions`
**Description:** Returns cost-per-transaction metrics for a specific time range.
- **Request Parameters:** `?start=2023-01-01&end=2023-06-01`
- **Response (200 OK):**
```json
{
  "averageCostPerTransaction": 0.042,
  "totalTransactions": 1250000,
  "currency": "EUR"
}
```

### 4.5 `POST /auth/2fa/setup`
**Description:** Initiates the setup of a hardware key or TOTP app.
- **Request Body:** `{ "method": "FIDO2" }`
- **Response (200 OK):**
```json
{ "challenge": "aB3jK...92z", "setupUrl": "https://auth.quorum.io/setup" }
```

### 4.6 `GET /search/devices`
**Description:** Full-text search for devices using faceted filters.
- **Request Parameters:** `?q=sensor&facet=status:online`
- **Response (200 OK):**
```json
{
  "results": [{ "deviceId": "DEV-11", "matchScore": 0.98 }],
  "facets": { "status": { "online": 450, "offline": 20 } }
}
```

### 4.7 `POST /sandbox/reset`
**Description:** Resets the sandbox environment to a clean state for testing.
- **Request Body:** `{ "scenario": "fresh_install" }`
- **Response (202 Accepted):**
```json
{ "status": "Resetting", "estimatedCompletion": "30s" }
```

### 4.8 `GET /system/health`
**Description:** Returns the health status of the microservices mesh.
- **Response (200 OK):**
```json
{
  "status": "Healthy",
  "services": {
    "ingestion": "Up",
    "billing": "Up",
    "search": "Degraded"
  }
}
```

---

## 5. DATABASE SCHEMA

The Quorum system uses a normalized relational schema in Azure SQL. Below are the 10 primary tables.

### 5.1 Table: `Devices`
- `DeviceId` (PK, GUID): Unique identifier.
- `ModelId` (FK): Reference to `Models` table.
- `StoreId` (FK): Reference to `Stores` table.
- `FirmwareVersion` (Varchar): Current version.
- `Status` (Int): 0=Offline, 1=Online, 2=Error.
- `CreatedAt` (DateTime): Timestamp.
- `LastHeartbeat` (DateTime): Last contact time.

### 5.2 Table: `Models`
- `ModelId` (PK, Int): ID of the hardware model.
- `Manufacturer` (Varchar): Hardware vendor.
- `SpecSheetUrl` (Varchar): Link to documentation.
- `PowerRating` (Decimal): Voltage/Wattage.

### 5.3 Table: `Stores`
- `StoreId` (PK, Int): Unique store identifier.
- `StoreName` (Varchar): Human-readable name.
- `RegionId` (FK): Reference to `Regions` table.
- `Address` (Varchar): Physical location.

### 5.4 Table: `Regions`
- `RegionId` (PK, Int): ID.
- `RegionName` (Varchar): e.g., "North Europe".
- `DataResidencyLaw` (Varchar): GDPR/CCPA/etc.

### 5.5 Table: `Transactions`
- `TransactionId` (PK, GUID): Unique ID.
- `DeviceId` (FK): The device that triggered the transaction.
- `Amount` (Decimal): Cost of the transaction.
- `Timestamp` (DateTime): Exact time of occurrence.
- `ProcessingTimeMs` (Int): Latency for cost analysis.

### 5.6 Table: `Users`
- `UserId` (PK, GUID): Unique user ID.
- `Email` (Varchar, Unique): User email.
- `PasswordHash` (Varchar): Argon2 hashed password.
- `Role` (Varchar): Admin, Operator, Viewer.

### 5.7 Table: `UserSecurity`
- `UserId` (FK): Reference to `Users`.
- `TwoFactorEnabled` (Bool): Status.
- `HardwareKeyId` (Varchar): Public key ID for FIDO2.
- `RecoveryCode` (Varchar): Encrypted recovery key.

### 5.8 Table: `FeatureFlags`
- `FlagId` (PK, Int): Unique flag ID.
- `FeatureName` (Varchar): e.g., "NewDashboardV2".
- `IsActive` (Bool): Global toggle.
- `RolloutPercentage` (Int): 0-100.

### 5.9 Table: `FeatureAssignments`
- `AssignmentId` (PK, GUID): ID.
- `UserId` (FK): Reference to `Users`.
- `FlagId` (FK): Reference to `FeatureFlags`.
- `AssignedBucket` (Char): 'A' or 'B'.

### 5.10 Table: `AuditLogs`
- `LogId` (PK, BigInt): ID.
- `UserId` (FK): Who performed the action.
- `Action` (Varchar): e.g., "UpdateFirmware".
- `DeviceId` (FK): Target device.
- `Timestamp` (DateTime): When it happened.
- `IpAddress` (Varchar): Source IP.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Quorum employs a strict three-tier environment isolation strategy.

1.  **Development (DEV):**
    - **Purpose:** Rapid iteration and unit testing.
    - **Data:** Mocked or anonymized data.
    - **Deployment:** Continuous Integration (CI) on every git push to `develop` branch.

2.  **Staging (STG):**
    - **Purpose:** Pre-production validation and UAT (User Acceptance Testing).
    - **Data:** Sanitized copy of production data.
    - **Deployment:** Triggered once per week upon a successful build of the release candidate.

3.  **Production (PROD):**
    - **Purpose:** Live retail operations.
    - **Data:** Actual retail and device data.
    - **Deployment:** Weekly release train.

### 6.2 The Weekly Release Train
To ensure the "Zero Downtime" requirement and maintain stability, Quorum adheres to a **Weekly Release Train**.
- **Schedule:** Deployments occur every Wednesday at 03:00 UTC (lowest traffic window).
- **No Hotfixes:** There are no exceptions for hotfixes outside the release train. If a critical bug is found on Thursday, it must be fixed, tested in STG, and deployed the following Wednesday.
- **Blue-Green Deployment:** Azure App Service slots are used. The new version is deployed to the "Stage" slot, warmed up, and then swapped with "Production" to ensure zero-second downtime.

### 6.3 Infrastructure Provisioning
Infrastructure is managed as code (IaC) using **Terraform**. 
- **Current State:** Blocked.
- **Issue:** The cloud provider has delayed the provisioning of the specialized Kafka clusters in the West Europe region.
- **Impact:** Integration testing between the Ingestion Service and the Billing Service is currently stalled.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** xUnit / Moq.
- **Requirement:** All new business logic must have $\ge 80\%$ code coverage.
- **Execution:** Runs automatically on every Pull Request via GitHub Actions.

### 7.2 Integration Testing
- **Focus:** Testing the communication between microservices via Kafka.
- **Method:** "Contract Testing" using Pact. We ensure that the `Ingestion Service` produces messages in a format the `Billing Service` can consume.
- **Frequency:** Runs nightly in the DEV environment.

### 7.3 End-to-End (E2E) Testing
- **Tooling:** Playwright for the admin dashboard; Postman/Newman for API flows.
- **Scenario:** A "Happy Path" test simulating a device sending a heartbeat, the system recording a transaction, and the API reflecting the updated cost.
- **Frequency:** Once per release train in the STG environment.

### 7.4 Performance Testing
- **Tooling:** JMeter.
- **Target:** Verify that the system can handle 5,000 concurrent device connections without increasing API response times beyond 500ms.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Scope creep from stakeholders adding "small" features. | High | Medium | Hire a contractor to increase capacity and reduce the "bus factor" of the solo developer. | Freya Gupta |
| R-02 | Budget cut of 30% in next fiscal quarter. | Medium | High | Assign a dedicated owner to track spending and optimize Azure costs (Reserved Instances). | Vivaan Liu |
| R-03 | Cloud provider infrastructure delays. | High | High | Explore multi-cloud fallback or pressure account manager for expedited provisioning. | Viktor Nakamura |
| R-04 | Legacy system failure during migration. | Low | Critical | Implement a "Parallel Run" phase where both systems operate simultaneously. | Ibrahim Jensen |

**Impact Matrix:**
- **Critical:** Immediate business stoppage.
- **High:** Significant delay in launch or budget overrun.
- **Medium:** Feature delay or minor performance degradation.
- **Low:** Negligible impact on timeline.

---

## 9. TIMELINE AND PHASES

The project follows a phased approach with a hard deadline for production launch.

### Phase 1: Core Infrastructure (Now – March 2025)
- **Focus:** Kafka setup, Azure SQL schema implementation, and API versioning.
- **Dependency:** Resolution of cloud provider provisioning blocker.
- **Key Milestone:** **Milestone 1: Security Audit Passed (2025-03-15).**

### Phase 2: Feature Integration & Beta (March 2025 – May 2025)
- **Focus:** Integrating 2FA, A/B testing framework, and faceted search.
- **Activity:** Internal beta testing with select retail stores.
- **Key Milestone:** **Milestone 2: Post-launch Stability Confirmed (2025-05-15).**

### Phase 3: Migration and Cutover (May 2025 – July 2025)
- **Focus:** Gradual migration of devices from legacy to Quorum.
- **Strategy:** 10% of stores $\rightarrow$ 30% $\rightarrow$ 60% $\rightarrow$ 100%.
- **Key Milestone:** **Milestone 3: Production Launch (2025-07-15).**

---

## 10. MEETING NOTES

### Meeting 1: 2023-11-02 (Sprint Planning)
- **Attendance:** Freya, Vivaan, Viktor, Ibrahim.
- **Notes:**
    - Legacy system acting up in Germany store.
    - Kafka lag in DEV.
    - Need to check GDPR residency again.
    - Freya says: "No hotfixes. Stick to the train."
    - Ibrahim concerned about documentation.

### Meeting 2: 2023-12-15 (Budget Review)
- **Attendance:** Freya, Vivaan.
- **Notes:**
    - $400k is tight.
    - Rumors of 30% cut in Q3.
    - Vivaan to track Azure spend.
    - Need contractor for C# work.
    - "Bus factor is too high."

### Meeting 3: 2024-01-10 (Technical Deep Dive)
- **Attendance:** Freya, Viktor, Vivaan.
- **Notes:**
    - FIDO2 keys working.
    - Search index is slow.
    - Provider still delaying Kafka.
    - "Just mock it for now" - Freya.
    - L10n blocked by agency.

---

## 11. BUDGET BREAKDOWN

The total budget is **$400,000**. Due to the solo developer nature of the core build, personnel costs are focused on the core team and the strategic addition of a contractor.

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $240,000 | Solo developer salary + specialized contractor for scope creep mitigation. |
| **Infrastructure** | 25% | $100,000 | Azure SQL, Azure Functions, Kafka (Event Hubs), and Cognitive Search. |
| **Tools/Licensing** | 5% | $20,000 | JIRA, GitHub Enterprise, Postman, and Security Audit fees. |
| **Contingency** | 10% | $40,000 | Reserved for emergency hardware needs or budget cuts. |

---

## 12. APPENDICES

### Appendix A: Data Mapping (Legacy $\rightarrow$ Quorum)
The legacy system uses a flat-file binary format for device logs. The mapping logic for the `Ingestion Service` is as follows:
- `Legacy_Field_01` $\rightarrow$ `DeviceId` (Guid conversion)
- `Legacy_Field_02` $\rightarrow$ `Timestamp` (Epoch to DateTime)
- `Legacy_Field_03` $\rightarrow$ `TransactionAmount` (Fixed-point decimal)
- `Legacy_Field_04` $\rightarrow$ `Status` (Bit-flag mapping)

### Appendix B: Hardware Key Specification
The 2FA system must support the following WebAuthn parameters to be compliant with Pivot North Engineering security standards:
- **Authenticator Attachment:** Platform or Cross-Platform.
- **User Verification:** Required (Biometric or PIN).
- **Algorithm:** ES256 (ECDSA with SHA-256).
- **Timeout:** 60,000ms.