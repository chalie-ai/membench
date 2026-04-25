Due to the length constraints of a single response, I have provided the comprehensive, formal project specification for **Project Canopy**. This document is designed as the primary source of truth for the development team, maintaining the strict constraints of the provided brief.

***

# PROJECT SPECIFICATION: PROJECT CANOPY
**Version:** 1.0.4  
**Status:** Draft/Active  
**Classification:** Internal/Confidential (Talus Innovations)  
**Date:** October 24, 2023  
**Owner:** Ira Kowalski-Nair

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Canopy represents a strategic platform modernization effort for Talus Innovations, specifically targeting the Supply Chain Management (SCM) systems used within government services. The primary objective is the systematic migration of a legacy monolithic architecture—characterized by rigid deployment cycles and high technical debt—into a scalable, resilient microservices ecosystem. This transition is slated over an 18-month horizon, aiming to decouple business logic and allow for independent scaling of critical supply chain modules.

### 1.2 Business Justification
The current monolithic system has reached a point of critical failure in terms of maintainability. Deployment cycles are currently tied to a "big bang" approach that risks total system outage during updates. In the government services sector, downtime results in significant service delivery failures for the public. By moving to a micro-frontend and microservice architecture, Talus Innovations can achieve higher availability, faster iteration cycles for specific modules, and a more robust security posture. 

The transition is critical for maintaining government contracts, as the legacy system cannot meet the evolving SOC 2 Type II compliance requirements mandated by recent regulatory updates. Failure to modernize will lead to the loss of existing government service contracts and a failure to compete for new tenders.

### 1.3 ROI Projection and Financial Model
Project Canopy is currently **unfunded**. It is being bootstrapped using existing team capacity. The ROI is calculated not through direct revenue, but through the mitigation of operational risk and the reduction of "maintenance tax."

*   **Operational Efficiency:** Reducing the deployment window from quarterly to bi-weekly (via microservices) is projected to save approximately 1,200 developer hours per year.
*   **Risk Mitigation:** Avoiding a single major outage (estimated at $150,000 per hour in penalty fees for government SLAs) provides an immediate return on investment.
*   **Infrastructure Optimization:** While remaining on-premise, the transition to microservices allows for the reallocation of hardware resources based on specific service load rather than scaling the entire monolith.
*   **Projected Gains:** We anticipate a 25% increase in throughput for supply chain processing and a 40% reduction in bug-fix turnaround time within the first 12 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Architecture
Project Canopy utilizes a **Micro-Frontend (MFE) Architecture** paired with a **Java/Spring Boot microservices backend**. The system is hosted entirely within a secure, on-premise data center to comply with strict government data sovereignty laws; cloud deployment is strictly prohibited.

### 2.2 Logic Flow (ASCII Representation)
```text
[ USER BROWSER ] 
       |
       v
[ NGINX API GATEWAY / REVERSE PROXY ] <--- [ SOC 2 Compliance Filter ]
       |
       +-------------------------------------------------------+
       |                           |                           |
[ MFE: Dashboard ]          [ MFE: Inventory ]          [ MFE: Audit ]
       |                           |                           |
       v                           v                           v
[ SERVICE: AUTH-MGMT ] <--> [ SERVICE: SUPPLY-CHAIN ] <--> [ SERVICE: LOGGING ]
       |                           |                           |
       +-------------+-------------+-------------+-------------+
                     |                           |
              [ ORACLE DB 19c ]           [ TAMPERS-EVIDENT LOG STORE ]
              (Relational Schema)         (WORM Storage/Blockchain-backed)
```

### 2.3 Technology Stack
- **Backend:** Java 17, Spring Boot 3.1, Spring Security, Spring Cloud Gateway.
- **Frontend:** React.js with Module Federation for Micro-Frontends.
- **Database:** Oracle Database 19c (Enterprise Edition).
- **Deployment:** On-premise Linux servers, Jenkins for CI/CD, Docker/Kubernetes (On-prem K8s cluster).
- **Security:** Hardware Security Modules (HSM) for 2FA keys, SOC 2 Type II auditing framework.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Progress
**Description:** To facilitate integration with government partners, Canopy must provide a robust, versioned REST API. This API allows external entities to push supply chain updates and pull status reports.

**Detailed Requirements:**
- **Versioning Strategy:** The API will use URI versioning (e.g., `/api/v1/...`). Versioning is mandatory to prevent breaking changes for government partners who cannot update their systems frequently.
- **Sandbox Environment:** A mirrored "Sandbox" instance of the Oracle DB (containing anonymized data) must be provided. This allows partners to test integrations without impacting production data.
- **Rate Limiting:** Implementation of a token-bucket algorithm to prevent API exhaustion.
- **Documentation:** Auto-generated Swagger/OpenAPI 3.0 documentation accessible via the developer portal.
- **Authentication:** API keys combined with OAuth2.0 Client Credentials flow.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker) | **Status:** In Progress
**Description:** Every state change within the supply chain (e.g., "Item Shipped" $\rightarrow$ "Item Delivered") must be recorded in a non-repudiable audit log.

**Detailed Requirements:**
- **Tamper-Evidence:** The system must use a hashing chain (Merkle Tree approach). Each log entry contains the hash of the previous entry. Any modification to a historical record will invalidate the chain.
- **Storage:** Data must be written to "Write Once, Read Many" (WORM) storage within the data center.
- **Granularity:** Must capture User ID, Timestamp (ISO-8601), Action, Old Value, New Value, and IP Address.
- **Alerting:** Any attempt to modify a locked audit record must trigger a high-priority alert to the Security Officer.

### 3.3 A/B Testing Framework within Feature Flag System
**Priority:** Critical (Launch Blocker) | **Status:** Not Started
**Description:** A system to toggle features for specific subsets of users to validate UX changes before full rollout.

**Detailed Requirements:**
- **Feature Flag Engine:** A centralized service managing flags. Flags can be "Global," "User-Specific," or "Percentage-Based."
- **A/B Logic:** The system must be able to assign a user to "Bucket A" or "Bucket B" and persist that assignment across sessions via a cookie or database record.
- **Metric Tracking:** Integration with the logging service to track which bucket resulted in higher completion rates for specific workflows.
- **Safety Switch:** A "Kill Switch" capability to instantly disable a feature for all users if a critical bug is detected.

### 3.4 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Critical (Launch Blocker) | **Status:** Blocked (Legal Review of DPA)
**Description:** A comprehensive identity management system to ensure only authorized personnel can access sensitive government supply chain data.

**Detailed Requirements:**
- **Role Hierarchy:** Define roles: `SuperAdmin`, `RegionalManager`, `SupplyOfficer`, and `ReadOnlyAuditor`.
- **Permission Mapping:** Permissions must be mapped to specific API endpoints and UI components (e.g., only `SuperAdmin` can delete a vendor).
- **Session Management:** JWT (JSON Web Tokens) with a maximum lifespan of 4 hours, requiring refresh tokens stored in secure HTTP-only cookies.
- **Identity Provider:** Integration with the internal Talus Innovations Active Directory.

### 3.5 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Critical (Launch Blocker) | **Status:** Complete
**Description:** High-security authentication requirement for all administrative roles.

**Detailed Requirements:**
- **Hardware Support:** Full support for FIDO2/WebAuthn (e.g., YubiKeys).
- **Fallback Mechanism:** TOTP (Time-based One Time Password) via approved authenticator apps as a secondary option.
- **Enforcement:** 2FA is mandatory for any user with `RegionalManager` or `SuperAdmin` privileges.
- **Recovery:** Secure recovery codes generated upon setup, requiring a manual identity verification process for resets.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`.

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and returns JWT.
- **Request:** `{"username": "string", "password": "string", "mfa_token": "string"}`
- **Response:** `200 OK {"token": "eyJ...", "expires_in": 14400}`

### 4.2 `GET /inventory/items`
- **Description:** Retrieves a list of supply chain items.
- **Request:** `?category=medical&limit=50`
- **Response:** `200 OK [{"id": "ITEM-001", "sku": "MED-123", "qty": 500}]`

### 4.3 `PATCH /inventory/items/{id}`
- **Description:** Updates quantity or status of an item.
- **Request:** `{"qty": 450, "status": "IN_TRANSIT"}`
- **Response:** `200 OK {"status": "updated", "timestamp": "2023-10-24T10:00:00Z"}`

### 4.4 `POST /audit/verify`
- **Description:** Validates the integrity of the audit chain.
- **Request:** `{"start_date": "2023-01-01", "end_date": "2023-01-31"}`
- **Response:** `200 OK {"integrity": "valid", "hash_count": 15402}`

### 4.5 `GET /sandbox/status`
- **Description:** Checks availability of the sandbox environment.
- **Request:** None
- **Response:** `200 OK {"env": "sandbox", "status": "healthy", "version": "v1.0.4-beta"}`

### 4.6 `POST /flags/toggle`
- **Description:** Changes a feature flag state (Admin only).
- **Request:** `{"flag_id": "NEW_DASHBOARD_UI", "enabled": true, "percentage": 10}`
- **Response:** `204 No Content`

### 4.7 `GET /users/profile`
- **Description:** Retrieves current authenticated user's role and profile.
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK {"username": "ikowalski", "role": "SuperAdmin", "region": "North"}`

### 4.8 `DELETE /inventory/items/{id}`
- **Description:** Soft-deletes an item (Requires SuperAdmin).
- **Request:** Header `Authorization: Bearer <token>`
- **Response:** `200 OK {"deleted": true, "audit_id": "LOG-9982"}`

---

## 5. DATABASE SCHEMA

The system utilizes an Oracle 19c relational database.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `USERS` | `user_id` | None | `username`, `pwd_hash`, `mfa_secret` | User identity and credentials. |
| `ROLES` | `role_id` | None | `role_name`, `access_level` | RBAC Role definitions. |
| `USER_ROLES` | `mapping_id` | `user_id`, `role_id` | `assigned_date` | Maps users to their respective roles. |
| `INVENTORY` | `item_id` | `vendor_id` | `sku`, `qty`, `status`, `last_updated` | Core supply chain item tracking. |
| `VENDORS` | `vendor_id` | None | `vendor_name`, `tax_id`, `contact_email` | Government-approved vendor list. |
| `AUDIT_LOGS` | `log_id` | `user_id`, `item_id` | `prev_hash`, `curr_hash`, `action_type` | Tamper-evident event log. |
| `FEATURE_FLAGS` | `flag_id` | None | `flag_name`, `is_enabled`, `rollout_pct` | Feature toggle configurations. |
| `USER_SESSIONS` | `session_id` | `user_id` | `token_hash`, `expiry_date`, `ip_address` | Active session tracking. |
| `SHIPMENTS` | `ship_id` | `item_id`, `vendor_id` | `tracking_no`, `dispatch_date` | Shipment tracking data. |
| `REGULATORY_DOCS` | `doc_id` | `vendor_id` | `doc_type`, `expiry_date`, `status` | Compliance certificates. |

### 5.2 Relationships
- `USERS` $\rightarrow$ `USER_ROLES` $\rightarrow$ `ROLES` (Many-to-Many)
- `VENDORS` $\rightarrow$ `INVENTORY` (One-to-Many)
- `VENDORS` $\rightarrow$ `REGULATORY_DOCS` (One-to-Many)
- `USERS` $\rightarrow$ `AUDIT_LOGS` (One-to-Many)
- `INVENTORY` $\rightarrow$ `AUDIT_LOGS` (One-to-Many)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Infrastructure Environment
All environments are hosted in the Talus Innovations on-premise data center. No external cloud (AWS/Azure/GCP) is permitted.

- **Development (DEV):**
  - Used by Wren Kowalski-Nair for initial coding.
  - Oracle DB: Local lightweight instance.
  - Deployment: Automated via Jenkins on a single VM.
- **Staging (STG):**
  - Mirrors production hardware. Used by Hessa Mahmoud-Reyes for QA and Zev Vasquez-Okafor for consulting review.
  - Oracle DB: Cloned production schema with scrubbed data.
  - Deployment: Quarterly release candidate builds.
- **Production (PROD):**
  - High-availability cluster.
  - Oracle DB: RAC (Real Application Clusters) for zero-downtime.
  - Deployment: Quarterly releases aligned with regulatory review cycles.

### 6.2 Release Cycle
Releases occur strictly every quarter. Each release must undergo a **Regulatory Review Cycle**, where the SOC 2 compliance officer verifies that all changes maintain the required security posture.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Requirement:** 80% minimum code coverage for all new microservices.
- **Focus:** Business logic in `@Service` layers and DTO mapping.

### 7.2 Integration Testing
- **Framework:** Spring Integration Test with Testcontainers (running local Oracle XE containers).
- **Focus:** API Gateway routing, DB transaction integrity, and inter-service communication.
- **Scope:** All `/api/v1` endpoints must be tested for correct HTTP response codes.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium and Playwright.
- **Focus:** Critical user journeys (e.g., Login $\rightarrow$ Update Inventory $\rightarrow$ Verify Audit Log).
- **Execution:** Conducted by Hessa Mahmoud-Reyes in the Staging environment before every quarterly release.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor is rotating out of role | High | High | Negotiate timeline extension with secondary stakeholders now. | Ira K-N |
| R-02 | Key Architect leaving in 3 months | Medium | Critical | Assign a dedicated owner to document all architectural decisions immediately. | Wren K-N |
| R-03 | Legal review of DPA is delayed | High | Medium | Escalate to Talus Innovations legal lead; use mock auth in DEV. | Ira K-N |
| R-04 | Date format inconsistency (Debt) | Certain | Medium | Implement a normalization layer (DateUtils) to standardize all to ISO-8601. | Wren K-N |
| R-05 | SOC 2 Compliance failure | Low | Critical | Conduct monthly internal pre-audits. | Hessa M-R |

### 8.1 Probability/Impact Matrix
- **High Probability/High Impact:** R-01, R-03
- **Low Probability/Critical Impact:** R-02, R-05
- **Certain Probability/Medium Impact:** R-04

---

## 9. TIMELINE & PHASES

### 9.1 Phase Description
- **Phase 1: Foundation (Now - Jan 2024):** Establishment of Micro-frontend shell and API Gateway. Completion of 2FA.
- **Phase 2: Core Migration (Feb 2024 - Dec 2024):** Migration of inventory and vendor modules from monolith to services. Implementation of Audit Trail.
- **Phase 3: Hardening & Compliance (Jan 2025 - May 2025):** SOC 2 Type II auditing and RBAC finalization.
- **Phase 4: Stabilization (May 2025 - Sept 2025):** Beta testing and production ramp-up.

### 9.2 Key Milestones
- **Milestone 1:** Post-launch stability confirmed $\rightarrow$ **2025-05-15**
- **Milestone 2:** MVP feature-complete $\rightarrow$ **2025-07-15**
- **Milestone 3:** Production launch $\rightarrow$ **2025-09-15**

---

## 10. MEETING NOTES

### Meeting 1: Architecture Kickoff (2023-11-02)
- Attendees: Ira, Wren, Zev.
- *Zev says Melbourne's govt systems used micro-frontends. Do it here too.*
- *Wren: concerned about Oracle DB locks during migration.*
- *Decision: Use a strangler pattern for the monolith.*
- *Ira: remind everyone about the on-prem restriction. No AWS.*

### Meeting 2: Security Review (2023-12-15)
- Attendees: Ira, Wren, Hessa.
- *Hessa: 2FA is done, but RBAC is still blocked by legal.*
- *Ira: we can't launch without RBAC.*
- *Wren: Date formats are a mess. Three different ones in the legacy code.*
- *Action: Wren to create a normalization utility.*

### Meeting 3: Stakeholder Update (2024-01-20)
- Attendees: Ira, Project Sponsor.
- *Sponsor: might be rotating out by Q3.*
- *Ira: need to extend the timeline or get a new sponsor signed off.*
- *Sponsor: just keep the JIRA updated.*
- *Decision: Negotiate timeline extensions in February.*

---

## 11. BUDGET BREAKDOWN

Since Project Canopy is **unfunded** and bootstrapping via existing capacity, the budget is expressed as "Internal Labor Cost" and "Existing Infrastructure Allocation."

| Category | Allocation | Estimated Value (Internal) | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 1 Solo Dev + 1 QA + 1 Lead | $450,000 / year | Based on internal salary bands. |
| **Infrastructure** | On-prem Server Rack 4 | $120,000 (CapEx) | Already purchased by Talus. |
| **Tools** | JIRA / Oracle License | $45,000 / year | Enterprise site license. |
| **Consulting** | External Advisor (Zev) | $15,000 / project | Fixed fee for architectural review. |
| **Contingency** | Internal Buffer | $50,000 | Allocated from general IT overhead. |
| **Total** | | **$680,000** | (Indirect Costs) |

---

## 12. APPENDICES

### Appendix A: Technical Debt Log (Date Normalization)
The system currently suffers from "Temporal Fragmentation." The following formats exist and must be normalized to `YYYY-MM-DDTHH:mm:ssZ`:
1. `MM/DD/YYYY` (Legacy Inventory Module)
2. `DD-MM-YYYY` (Vendor Management Module)
3. `YYYY/MM/DD` (Audit Logs)
**Resolution:** A `DateNormalizationInterceptor` will be implemented in the Spring Boot API layer to coerce all incoming date strings into ISO-8601 before reaching the service layer.

### Appendix B: SOC 2 Type II Compliance Checklist
To pass the launch blocker, the following must be verified:
- [x] MFA implemented for all privileged accounts.
- [ ] RBAC matrix signed off by Legal.
- [ ] Audit logs verified as immutable (tamper-evident).
- [ ] On-prem data center physical access logs reviewed.
- [ ] Quarterly penetration test results documented.