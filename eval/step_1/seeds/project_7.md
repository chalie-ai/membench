# PROJECT SPECIFICATION: PROJECT GANTRY
**Version:** 1.0.4  
**Status:** Draft / Active  
**Last Updated:** October 24, 2023  
**Classification:** Internal / Confidential (ISO 27001)  
**Company:** Flintrock Engineering  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Gantry represents a critical pivot for Flintrock Engineering. Originally conceived as a rapid-prototype hackathon project to visualize cybersecurity telemetry, Gantry has evolved into an internal productivity tool that now supports 500 daily active users (DAU) within the retail operations sector. In the current retail landscape, where supply chain integrity and Point-of-Sale (POS) security are paramount, the ability to monitor threats in real-time is not merely a convenience—it is a business continuity requirement.

Currently, Flintrock’s security analysts rely on fragmented log files and manual query execution across legacy Oracle instances. This manual processing creates a significant bottleneck, delaying threat detection and remediation. Gantry centralizes these telemetry streams into a high-performance monitoring dashboard, allowing for proactive rather than reactive security postures. By automating the aggregation of security events, Gantry transforms raw data into actionable intelligence.

### 1.2 ROI Projection
With a budget exceeding $5 million, Gantry is designated as a flagship initiative with board-level reporting obligations. The Return on Investment (ROI) is calculated based on two primary drivers: operational efficiency and risk mitigation.

**Operational Efficiency:** The primary success metric is a 50% reduction in manual processing time for end users. Based on current analyst salaries and the volume of manual reports generated per week, this reduction is projected to save approximately 12,000 man-hours annually. At an average burdened cost of $85/hour, this represents a direct productivity gain of ~$1.02M per year.

**Risk Mitigation:** The retail industry faces an average breach cost of $4.45M per incident. By reducing the Mean Time to Detect (MTTD) and Mean Time to Respond (MTTR) through the Gantry dashboard, Flintrock aims to reduce the probability of a catastrophic data breach by 20%. This risk-adjusted saving is valued at approximately $890k per annum.

Combined, the projected annual benefit is ~$1.91M, suggesting a break-even point within 32 months of full deployment, excluding the long-term strategic value of enhanced ISO 27001 compliance.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Gantry is built on a "Modular Monolith" pattern, currently transitioning to a microservices architecture incrementally. This approach allows the team to maintain a single deployment pipeline while decoupling domain logic into distinct modules (Auth, Logging, API, UI) to prevent the "Big Ball of Mud" syndrome.

### 2.2 The Stack
- **Backend:** Java 17 with Spring Boot 3.1.x.
- **Database:** Oracle DB 19c (Enterprise Edition).
- **Frontend:** React 18 with TypeScript and Tailwind CSS.
- **Infrastructure:** On-premise data center (Strictly no cloud; air-gapped production segment).
- **Security:** ISO 27001 certified environment.

### 2.3 System Topology (ASCII Diagram Description)
The system follows a layered architecture. 

```text
[ External Users ] <--> [ Load Balancer (F5 Big-IP) ]
                               |
                               v
[ DMZ Layer ] <--> [ API Gateway / Spring Cloud Gateway ]
                               |
                               v
[ App Layer ] <--> [ Gantry Core (Modular Monolith) ]
                               |      |
         ______________________|      |______________________
        |                              |                      |
 [ Auth Module ]               [ Telemetry Module ]    [ Audit Module ]
        |                              |                      |
        |______________________________|______________________|
                               |
                               v
 [ Persistence Layer ] <--> [ Oracle DB 19c Cluster ]
                               |
                               v
 [ Storage Layer ] <--> [ Tamper-Evident WORM Storage ]
```

**Topology Details:**
1. **Load Balancer:** Handles SSL termination and distributes traffic to the on-premise application servers.
2. **API Gateway:** Manages request routing, rate limiting, and the versioning logic for the customer-facing API.
3. **Gantry Core:** The Java/Spring Boot application. It contains the "God Class" (currently `SecurityOrchestrator.java`) which is slated for decomposition.
4. **Persistence Layer:** Oracle DB handles structured data, user profiles, and configuration.
5. **WORM Storage:** Write-Once-Read-Many storage is utilized for the audit trail to ensure tamper-evidence.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and RBAC (Priority: Medium | Status: Blocked)
**Requirement:** A robust internal authentication system that assigns permissions based on organizational roles (e.g., Analyst, Admin, Auditor).

**Detailed Specification:**
The system must implement a Role-Based Access Control (RBAC) model where users are assigned to one or more roles, and roles are mapped to specific permissions (e.g., `READ_DASHBOARD`, `EXECUTE_REMEDIATION`, `MANAGE_USERS`). This requires a many-to-many relationship between users and roles.

The current implementation is blocked due to the "God Class" (`SecurityOrchestrator.java`), which tightly couples authentication logic with email dispatch and logging. Any change to the RBAC logic currently risks breaking the email notification system for security alerts. The goal is to extract the authentication logic into a standalone `AuthService`.

**Functional Requirements:**
- Users must be able to log in via a secure credentials page.
- Password hashing must use Argon2 with a minimum salt of 16 bytes.
- Session management must utilize secure, HTTP-only cookies with a maximum TTL of 8 hours.
- Role escalation must be prevented through server-side validation of every API request.

**Acceptance Criteria:**
- A user with the "Analyst" role cannot access the "Admin" panel.
- An administrator can revoke access for any user in real-time.
- Failed login attempts are logged to the audit trail.

---

### 3.2 SSO Integration with SAML and OIDC (Priority: High | Status: In Design)
**Requirement:** Integration with corporate Identity Providers (IdP) to allow seamless access for the 500+ users.

**Detailed Specification:**
Gantry must support both Security Assertion Markup Language (SAML 2.0) for legacy corporate identity and OpenID Connect (OIDC) for modern authentication flows. This integration will remove the need for Gantry to store passwords locally, shifting the burden of identity verification to the corporate IdP.

The design phase involves mapping SAML assertions and OIDC claims to internal Gantry roles. For example, an LDAP group `SEC_OPS_L2` should automatically map to the `Analyst` role within Gantry.

**Functional Requirements:**
- Support for SP-initiated and IdP-initiated SSO flows.
- Implementation of a "Just-in-Time" (JIT) provisioning system to create local user profiles upon the first successful SSO login.
- Support for Single Log-Out (SLO) to ensure sessions are terminated across all integrated services.
- OIDC implementation must support the Authorization Code Flow with PKCE for increased security.

**Acceptance Criteria:**
- Users can log in using their corporate credentials without being prompted for a second password.
- Token expiration is synchronized with the corporate IdP settings.
- The system correctly handles "User Not Found" responses from the IdP.

---

### 3.3 Audit Trail Logging with Tamper-Evident Storage (Priority: High | Status: In Design)
**Requirement:** An immutable record of every action taken within the Gantry platform to meet ISO 27001 requirements.

**Detailed Specification:**
The audit trail is not a standard log; it is a legal record of activity. Every "Write" or "Delete" operation, as well as any "Read" of sensitive PII, must be recorded. The storage mechanism must be tamper-evident, meaning that any attempt to modify or delete a log entry must be detectable.

This will be achieved by using a cryptographic chaining mechanism (similar to a blockchain) where each log entry contains a hash of the previous entry. These hashes are then periodically anchored to a write-once-read-many (WORM) storage appliance.

**Functional Requirements:**
- Every log entry must include: Timestamp (UTC), UserID, Action, ResourceID, Old Value, New Value, and Source IP.
- The system must support "Audit Export" for compliance officers in CSV and JSON formats.
- Integration with the `SecurityOrchestrator.java` (post-refactor) to ensure all critical events are captured.
- Automatic alerting if a gap in the hash chain is detected during a system integrity check.

**Acceptance Criteria:**
- An auditor can prove that no logs were deleted from the last 90 days.
- The audit trail capture adds less than 50ms latency to any user action.
- Log entries are stored in an encrypted state at rest using AES-256.

---

### 3.4 Customer-Facing API with Versioning and Sandbox (Priority: Critical | Status: In Progress)
**Requirement:** A public-facing interface allowing external retail partners to pull security telemetry into their own dashboards.

**Detailed Specification:**
This is the primary launch blocker. Gantry must provide a RESTful API that is decoupled from the internal UI. To ensure stability for partners, the API must be versioned (e.g., `/v1/`, `/v2/`). 

A critical component of this feature is the **Sandbox Environment**. Partners cannot test their integrations against live production telemetry. The sandbox will be a mirrored environment using anonymized/synthetic data, allowing partners to validate their API calls without risking production stability.

**Functional Requirements:**
- API Key management system (Create, Rotate, Revoke).
- Rate limiting (Throttling) based on the partner's tier (e.g., 100 requests/min for Basic, 1000 for Premium).
- Comprehensive Swagger/OpenAPI 3.0 documentation.
- Sandbox environment that mimics production behavior but returns mock data.
- Versioning strategy: Deprecated versions will be supported for 6 months after a new version release.

**Acceptance Criteria:**
- A partner can successfully authenticate and retrieve telemetry via the `/v1/telemetry` endpoint.
- Requests to the sandbox environment do not affect the production Oracle DB.
- The API returns standard HTTP status codes (200 OK, 401 Unauthorized, 429 Too Many Requests).

---

### 3.5 A/B Testing Framework for Feature Flags (Priority: Medium | Status: Not Started)
**Requirement:** A system to toggle features on/off and run experiments on different user groups.

**Detailed Specification:**
To avoid "big bang" releases, Gantry requires a feature flag system. This framework will allow the development team to deploy code to production but keep it hidden behind a toggle. Once the feature is stable, it can be rolled out to a small percentage of users (A/B Testing) to measure impact on productivity.

The framework will be integrated into the Spring Boot application as a configuration service. Feature flags will be stored in a dedicated Oracle table, allowing administrators to change flags without restarting the application.

**Functional Requirements:**
- Ability to define flags based on user attributes (e.g., `role == 'Admin'`).
- Percentage-based rollout (e.g., 10% of users see the new dashboard layout).
- Telemetry tracking to compare the "A" group (control) and "B" group (variant) in terms of task completion speed.
- a "Kill Switch" capability to instantly disable a feature if it causes a system outage.

**Acceptance Criteria:**
- The team can enable a feature for 5 specific users without deploying new code.
- The system can track how many clicks it takes to reach a report in Version A vs Version B.
- Feature flags are automatically removed from the code after a feature is 100% rolled out.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. Base URL: `https://gantry.flintrock.internal/api/v1`.

### 4.1 `GET /telemetry/summary`
**Description:** Returns a high-level summary of current security alerts.
- **Request Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
```json
{
  "total_alerts": 142,
  "critical": 12,
  "warning": 45,
  "info": 85,
  "last_updated": "2023-10-24T14:00:00Z"
}
```

### 4.2 `GET /telemetry/alerts/{alertId}`
**Description:** Retrieves detailed information for a specific alert.
- **Request Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
```json
{
  "id": "ALRT-9902",
  "severity": "CRITICAL",
  "source": "POS-Terminal-04",
  "description": "Unauthorized access attempt detected via SSH",
  "timestamp": "2023-10-24T13:45:12Z"
}
```

### 4.3 `POST /audit/logs`
**Description:** Manually injects an event into the audit trail (used by internal services).
- **Request Body:**
```json
{
  "userId": "USR-102",
  "action": "UPDATE_CONFIG",
  "resource": "FIREWALL_RULES",
  "oldValue": "Allow All",
  "newValue": "Allow Port 80, 443"
}
```
- **Response (201 Created):** `{"status": "logged", "logId": "LOG-7781"}`

### 4.4 `GET /users/profile`
**Description:** Returns the current authenticated user's profile and roles.
- **Response (200 OK):**
```json
{
  "username": "ablackwood",
  "email": "aiko@flintrock.com",
  "roles": ["PROJECT_LEAD", "ADMIN"],
  "lastLogin": "2023-10-24T08:00:00Z"
}
```

### 4.5 `POST /auth/sso/login`
**Description:** Initiates the SSO handshake with the IdP.
- **Request Body:** `{"provider": "okta"}`
- **Response (302 Redirect):** Redirects user to the IdP authentication page.

### 4.6 `PUT /config/feature-flags/{flagId}`
**Description:** Updates the state of a feature flag (Admin only).
- **Request Body:** `{"enabled": true, "percentage": 25}`
- **Response (200 OK):** `{"flagId": "new-ui-layout", "status": "updated"}`

### 4.7 `GET /sandbox/telemetry`
**Description:** Retrieves synthetic telemetry data for partner testing.
- **Response (200 OK):** Returns a JSON array of mock alerts.

### 4.8 `DELETE /users/sessions/{sessionId}`
**Description:** Terminates a specific user session (Force logout).
- **Response (204 No Content):** Empty body.

---

## 5. DATABASE SCHEMA

The database is hosted on Oracle DB 19c. All tables use `VARCHAR2` for strings and `TIMESTAMP` for time tracking.

### 5.1 Table Definitions

1.  **`USERS`**: Core user identity.
    - `USER_ID` (PK, UUID)
    - `USERNAME` (Unique, VARCHAR2(50))
    - `EMAIL` (Unique, VARCHAR2(100))
    - `PASSWORD_HASH` (VARCHAR2(255))
    - `MFA_ENABLED` (Boolean)
    - `CREATED_AT` (Timestamp)

2.  **`ROLES`**: Defined system roles.
    - `ROLE_ID` (PK, Int)
    - `ROLE_NAME` (Unique, VARCHAR2(30)) — e.g., 'ADMIN', 'ANALYST'
    - `DESCRIPTION` (VARCHAR2(255))

3.  **`USER_ROLES`**: Mapping table for RBAC.
    - `USER_ID` (FK -> USERS)
    - `ROLE_ID` (FK -> ROLES)

4.  **`TELEMETRY_EVENTS`**: Raw security events.
    - `EVENT_ID` (PK, UUID)
    - `SOURCE_DEVICE` (VARCHAR2(100))
    - `EVENT_TYPE` (VARCHAR2(50))
    - `SEVERITY` (VARCHAR2(20))
    - `RAW_PAYLOAD` (CLOB)
    - `OCCURRED_AT` (Timestamp)

5.  **`AUDIT_TRAIL`**: Tamper-evident log.
    - `LOG_ID` (PK, Long)
    - `USER_ID` (FK -> USERS)
    - `ACTION` (VARCHAR2(100))
    - `RESOURCE_ID` (VARCHAR2(100))
    - `PREVIOUS_STATE` (CLOB)
    - `NEW_STATE` (CLOB)
    - `HASH_CHAIN` (VARCHAR2(64)) — SHA-256 hash of previous row
    - `TIMESTAMP` (Timestamp)

6.  **`API_KEYS`**: Partner access keys.
    - `KEY_ID` (PK, UUID)
    - `PARTNER_NAME` (VARCHAR2(100))
    - `KEY_HASH` (VARCHAR2(128))
    - `SALIENCE_LEVEL` (Int) — Rate limit tier
    - `IS_ACTIVE` (Boolean)
    - `EXPIRY_DATE` (Timestamp)

7.  **`FEATURE_FLAGS`**: Toggles for A/B testing.
    - `FLAG_ID` (PK, VARCHAR2(50))
    - `SATE` (Boolean)
    - `ROLLOUT_PERCENT` (Int)
    - `TARGET_ROLE` (FK -> ROLES)
    - `UPDATED_AT` (Timestamp)

8.  **`SAML_CONFIG`**: SSO Identity Provider settings.
    - `CONFIG_ID` (PK, Int)
    - `IDP_ENTITY_ID` (VARCHAR2(255))
    - `SAML_SPO_CERT` (CLOB)
    - `SAML_ENDPOINT` (VARCHAR2(255))

9.  **`SANDBOX_DATA`**: Mock data for API testing.
    - `MOCK_ID` (PK, UUID)
    - `SAMPLED_FROM_ID` (FK -> TELEMETRY_EVENTS)
    - `ANONYMIZED_PAYLOAD` (CLOB)

10. **`SESSION_STORE`**: Active user sessions.
    - `SESSION_ID` (PK, VARCHAR2(128))
    - `USER_ID` (FK -> USERS)
    - `LOGIN_IP` (VARCHAR2(45))
    - `EXPIRES_AT` (Timestamp)

### 5.2 Relationships
- `USERS` has a many-to-many relationship with `ROLES` via `USER_ROLES`.
- `USERS` has a one-to-many relationship with `AUDIT_TRAIL` and `SESSION_STORE`.
- `TELEMETRY_EVENTS` is the source for `SANDBOX_DATA`.
- `ROLES` is referenced by `FEATURE_FLAGS` for role-based feature gating.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry utilizes a Continuous Deployment (CD) pipeline where every merged Pull Request (PR) to the `main` branch is automatically deployed to production. This requires an extremely high level of automated test coverage.

#### 6.1.1 Development (Dev)
- **Purpose:** Feature development and initial integration.
- **Hardware:** Virtualized developer workstations and a shared Dev Oracle instance.
- **Data:** Synthetic data only.
- **Access:** All internal developers.

#### 6.1.2 Staging (Staging/QA)
- **Purpose:** Final validation, QA testing by Alejandro Lindqvist-Tanaka, and UAT.
- **Hardware:** Mimics production hardware (On-prem servers).
- **Data:** Scrubbed production data (PII removed).
- **Access:** Developers, QA, and Project Lead.

#### 6.1.3 Production (Prod)
- **Purpose:** Live operation for 500+ users and external partners.
- **Hardware:** High-availability Oracle Cluster, F5 Load Balancers, and WORM storage.
- **Data:** Live production telemetry.
- **Access:** Strictly limited. Deployment is automated via Jenkins pipeline. ISO 27001 audited.

### 6.2 Infrastructure Blocker
**Current Issue:** Infrastructure provisioning for the new API Gateway has been delayed. Although we are an on-premise project, we utilize a specific "Cloud-Adjacent" managed hardware provider for our networking stack. This provider has failed to deliver the physical load balancer units for the API sandbox, creating a critical path blocker for Milestone 2.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual methods and classes in the Spring Boot application.
- **Tooling:** JUnit 5, Mockito.
- **Target:** 80% code coverage.
- **Requirement:** Every PR must pass all unit tests before the merge is permitted.

### 7.2 Integration Testing
- **Scope:** Interaction between modules (e.g., Auth $\rightarrow$ Oracle DB) and API endpoint validation.
- **Tooling:** Testcontainers (to spin up temporary Oracle DB instances), Postman/Newman.
- **Focus:** Ensuring the "God Class" refactor does not break existing functionality.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Complete user journeys (e.g., "Login $\rightarrow$ View Dashboard $\rightarrow$ Export Audit Log").
- **Tooling:** Selenium / Cypress.
- **Frequency:** Run nightly against the Staging environment.

### 7.4 Performance Benchmarking
- **Scope:** Response times for the `/telemetry/summary` endpoint and Oracle query optimization.
- **Metric:** 99th percentile latency must be $< 200\text{ms}$ for dashboard loads.
- **Tooling:** JMeter.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor for telemetry ingestion announces EOL (End-of-Life). | High | Critical | Hire an external contractor to build a custom ingestion layer, reducing the "bus factor" and vendor dependency. |
| **R-02** | 30% budget cut in next fiscal quarter due to retail downturn. | Medium | High | Document all current workarounds and architectural shortcuts; prioritize critical features over "nice-to-have" (e.g., A/B testing). |
| **R-03** | Team dysfunction leads to development stalls (PM/Lead Eng conflict). | High | High | Project Lead (Aiko) to facilitate weekly mediated syncs; shift to asynchronous decision-making via Slack. |
| **R-04** | "God Class" refactor introduces regression in production. | Medium | Medium | Implement strict feature flags; roll out refactored code to 5% of users first. |
| **R-05** | Failure to meet ISO 27001 audit. | Low | Critical | Weekly compliance reviews with Lina Blackwood-Diallo (External Consultant). |

**Probability/Impact Matrix:**
- **Critical:** Immediate project failure or legal breach.
- **High:** Major milestone delay or significant budget loss.
- **Medium:** Manageable delay or performance degradation.
- **Low:** Minor inconvenience.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Stabilization (Now $\rightarrow$ June 2025):** Focus on decomposing the `SecurityOrchestrator` God class and completing the API sandbox.
- **Phase 2: Onboarding (June 2025 $\rightarrow$ August 2025):** Integration of SSO and onboarding the first external paying customer.
- **Phase 3: Optimization (August 2025 $\rightarrow$ October 2025):** Performance tuning and final ISO 27001 certification.

### 9.2 Key Milestones

| Milestone | Target Date | Dependencies | Success Criteria |
| :--- | :--- | :--- | :--- |
| **Internal Alpha** | 2025-06-15 | RBAC, API v1, Basic Dashboard | 500 internal users can log in and view telemetry. |
| **First Paying Customer** | 2025-08-15 | SSO, API Sandbox, Billing Integration | Successful data pull by partner via API. |
| **Perf Benchmarks** | 2025-10-15 | Oracle Indexing, Load Balancer tuning | 99.9% uptime; $<200\text{ms}$ latency. |

---

## 10. MEETING NOTES (SLACK ARCHIVE)

*Note: As per project culture, there are no formal minutes. The following are synthesized from the `#gantry-dev` and `#gantry-leadership` Slack channels.*

### Meeting 1: The "God Class" Confrontation
**Date:** 2023-11-12  
**Participants:** Aiko Blackwood-Diallo, Hana Vasquez-Okafor  
**Thread Summary:**
- **Hana:** "I can't implement the RBAC updates because `SecurityOrchestrator.java` is 3,000 lines of spaghetti. If I touch the auth logic, the email alerts for the retail POS systems stop working. It's a mess."
- **Aiko:** "We don't have time for a full rewrite. Just patch it for now."
- **Hana:** "Patching it is why it's 3,000 lines. We need two weeks of pure refactoring or this project will collapse under its own weight."
- **Decision:** Hana is granted a "refactor sprint" starting next Monday, but Aiko insists that the API sandbox must still be delivered by the end of the month. (Hana stopped responding to the thread after this).

### Meeting 2: The Helsinki Consultation
**Date:** 2023-12-05  
**Participants:** Aiko Blackwood-Diallo, Lina Blackwood-Diallo  
**Thread Summary:**
- **Lina:** "I've reviewed the ISO 27001 requirements for the on-prem data center. The audit trail is currently insufficient. You cannot simply log to a table; you need WORM (Write-Once-Read-Many) storage."
- **Aiko:** "Can we just use a separate Oracle instance?"
- **Lina:** "No. An admin with DB privileges can still modify those logs. You need the cryptographic chaining I proposed in the architecture doc."
- **Decision:** The audit trail specification is updated to include SHA-256 hash chaining and external WORM storage.

### Meeting 3: Budget Panic
**Date:** 2024-01-20  
**Participants:** Aiko Blackwood-Diallo, Alejandro Lindqvist-Tanaka  
**Thread Summary:**
- **Aiko:** "Heads up, the board is looking at the retail losses. There is a 30% chance our budget gets slashed next quarter. We need to be lean."
- **Alejandro:** "Does that affect the QA hardware? I still don't have the mirrored environment for the API sandbox."
- **Aiko:** "Probably. If the cut happens, we might have to use a software-simulated load balancer instead of the F5 hardware."
- **Decision:** Alejandro to document all "lean" workarounds for the sandbox environment to ensure the launch blocker is mitigated even if funding drops.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,000,000+ (Flagship Initiative)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,000,000 | 20+ staff across 3 departments, including Senior Devs and QA. |
| **Infrastructure** | 25% | $1,250,000 | On-prem servers, Oracle 19c licenses, WORM storage, F5 hardware. |
| **Tools & Licenses** | 10% | $500,000 | IDEs, Jenkins licenses, Security scanning tools (Snyk/SonarQube). |
| **Contingency** | 5% | $250,000 | Reserve for emergency contractor hiring (e.g., for EOL vendor risk). |

---

## 12. APPENDICES

### Appendix A: The "God Class" (`SecurityOrchestrator.java`) Decomposition Plan
To resolve the current blocker for RBAC, the `SecurityOrchestrator` will be split into the following services:
1. **`AuthenticationService`**: Handles password validation, SSO tokens, and session creation.
2. **`AuthorizationService`**: Manages RBAC permission checks and role mapping.
3. **`NotificationService`**: Handles the email and SMS dispatch logic.
4. **`AuditLogService`**: Handles the hashing and writing of events to the WORM storage.

### Appendix B: ISO 27001 Compliance Mapping
| Control | Gantry Implementation |
| :--- | :--- |
| **A.9.2.2** | User access provisioning via OIDC/SAML and RBAC. |
| **A.12.4.1** | Tamper-evident audit logging with cryptographic chaining. |
| **A.12.4.3** | Use of WORM storage to prevent log alteration. |
| **A.13.1.1** | Network segregation between the API Gateway (DMZ) and Oracle DB (Internal). |
| **A.18.1.1** | Quarterly compliance reviews led by external consultant (Lina B-D). |