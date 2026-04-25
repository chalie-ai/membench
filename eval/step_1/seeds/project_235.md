Due to the extreme length requirement of 6,000 to 8,000 words, this document is presented as a comprehensive, industrial-grade Project Specification. It is structured as the "Single Source of Truth" for the development team at Nightjar Systems.

***

# PROJECT SPECIFICATION: PARAPET (v1.0.4)
**Company:** Nightjar Systems  
**Document Status:** Active / Living Document  
**Classification:** Confidential - Internal Use Only  
**Last Updated:** 2025-10-12  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Vision
Project Parapet is a high-stakes, moonshot R&D initiative commissioned by Nightjar Systems to revolutionize data accessibility and collaborative clinical documentation within the healthcare industry. At its core, Parapet is designed to solve the "fragmentation gap" in healthcare—where critical patient data exists across disparate systems but lacks a unified, real-time collaborative interface for providers. 

Unlike standard Electronic Health Record (EHR) systems, Parapet is positioned as a "high-velocity overlay," providing a seamless mobile experience that allows clinicians to interact with complex datasets using advanced search and real-time synchronization. Because this is an R&D effort, the project acknowledges a high degree of technical uncertainty and an unproven ROI. However, it carries the full weight of executive sponsorship and board-level visibility, making its success a strategic priority for Nightjar Systems' expansion into the healthcare vertical.

### 1.2 Business Justification
The healthcare market is currently shifting toward "Value-Based Care," where the speed and accuracy of information retrieval directly correlate to patient outcomes and provider reimbursement rates. Current tools are often desktop-bound and sluggish. Parapet aims to capture the "mobile clinician" segment—doctors and nurses who need immediate, high-fidelity access to patient records during rounds.

The business justification rests on three pillars:
1. **Market Differentiation:** By integrating real-time collaborative editing (Feature 4), Parapet will be the first mobile healthcare app to allow multi-provider synchronization on a single patient chart without "save-and-refresh" lag.
2. **Operational Efficiency:** Advanced faceted search (Feature 3) reduces the time spent looking for specific labs or notes by an estimated 40%.
3. **Strategic Foothold:** Even if the ROI is initially uncertain, the intellectual property developed regarding GDPR/CCPA compliant serverless architectures in healthcare will provide Nightjar Systems with a competitive moat.

### 1.3 ROI Projection and Financials
The budget for Parapet is set at $5.2M for the initial development and launch phase. While the ROI is considered "uncertain" in the short term, the long-term projection assumes a B2B SaaS model targeting mid-to-large hospital networks.

*   **Conservative Projection:** 15 hospital networks, 2,000 seats per network, $45/user/month. Projected Annual Recurring Revenue (ARR): $16.2M.
*   **Break-even Analysis:** Based on the $5.2M initial investment and an estimated $1.1M annual maintenance cost, the project is expected to reach the break-even point within 14 months of the first paying customer onboarding (Target: 2026-09-15).
*   **Intangible ROI:** The "Moonshot" nature of the project means that a 20% adoption rate among pilot users would validate the architectural hypothesis, potentially unlocking further funding for a Version 2.0 enterprise suite.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Overview
Parapet utilizes a fully serverless, event-driven architecture leveraging the Microsoft Azure ecosystem. The goal is to ensure maximum scalability and minimize the operational overhead for the small team of four.

**The Stack:**
- **Frontend:** .NET MAUI (C#) for cross-platform mobile deployment.
- **Backend:** Azure Functions (C#) acting as a set of microservices.
- **Orchestration:** Azure API Management (APIM) acting as the API Gateway.
- **Database:** Azure SQL Database (Serverless tier) with Geo-Replication.
- **State Management:** Redis Cache for real-time synchronization.
- **Configuration:** LaunchDarkly for feature flags and canary deployments.

### 2.2 System Topology (ASCII Diagram)
```text
[ Mobile App (iOS/Android) ]
          |
          v (HTTPS / TLS 1.3)
[ Azure API Management (Gateway) ] <--- [ LaunchDarkly (Feature Flags) ]
          |
          +---------------------------------------+
          | (Routing)                             | (Routing)
          v                                       v
[ Azure Function: Auth/Identity ]      [ Azure Function: Search/Index ]
          |                                       |
          +-------------------+-------------------+
                              |
                              v
                    [ Azure SQL Database ] <--- [ EU Data Residency Zone ]
                              |
                    [ Azure Blob Storage ] (Audit Logs/Documents)
```

### 2.3 Data Residency and Compliance
Per the GDPR and CCPA requirements, Parapet implements a "Strict Residency" policy. 
- **EU Region:** All data for EU-based users is stored exclusively in `northeurope` and `westeurope` Azure regions.
- **US Region:** All data for US-based users is stored in `eastus2`.
- **Cross-Border Logic:** The API Gateway inspects the user's `TenantID` and routes requests to the specific regional Azure Function app. No patient-identifiable information (PII) is permitted to cross regional boundaries.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Two-Factor Authentication (2FA) with Hardware Key Support
- **Priority:** Low (Nice to have)
- **Status:** Complete
- **Version:** v1.0.0
- **Description:** A security layer requiring users to provide two forms of identification before gaining access to the healthcare data. While standard TOTP (Time-based One-Time Password) is supported, the primary value-add is the integration of FIDO2 hardware keys (e.g., YubiKey).
- **Technical Logic:**
    - The system implements the WebAuthn standard. During the "Registration" phase, the mobile app invokes a challenge from the Azure Function. The hardware key signs this challenge, and the public key is stored in the `UserSecurityKeys` table.
    - During "Authentication," the server sends a nonce; the hardware key signs it, and the server validates the signature.
- **User Flow:** User enters credentials $\rightarrow$ System detects 2FA enabled $\rightarrow$ System prompts for hardware key touch $\rightarrow$ Access granted.
- **Validation:** Must be compatible with NFC-enabled YubiKeys for mobile proximity sensing.

### 3.2 API Rate Limiting and Usage Analytics
- **Priority:** Low (Nice to have)
- **Status:** Complete
- **Version:** v1.0.0
- **Description:** To prevent denial-of-service attacks and ensure fair usage among tenants, the API Gateway implements a tiered rate-limiting strategy. Simultaneously, every single request is logged to a telemetry sink for usage analytics.
- **Technical Logic:**
    - **Rate Limiting:** Implemented via Azure API Management (APIM) policies. Limits are set at the `API Key` level.
        - Tier 1 (Pilot): 1,000 requests/minute.
        - Tier 2 (Standard): 5,000 requests/minute.
    - **Analytics:** An Azure Function trigger captures the `RequestID`, `Timestamp`, `Endpoint`, and `UserID`, piping them into an Azure Log Analytics workspace.
- **Business Value:** Allows the team to identify "power users" and detect anomalous behavior that might indicate a security breach or a bug in the frontend loop.

### 3.3 Advanced Search with Faceted Filtering and Full-Text Indexing
- **Priority:** Critical (Launch Blocker)
- **Status:** Complete
- **Version:** v1.1.0
- **Description:** Healthcare providers need to find specific data points (e.g., "Potassium levels over 5.0 in patients aged 60-70 with Diabetes") instantly. This feature provides a Google-like search experience within the patient record.
- **Technical Logic:**
    - **Indexing:** The system utilizes Azure SQL Full-Text Search (FTS) and a custom indexing service that flattens nested JSON medical notes into a searchable `SearchIndex` table.
    - **Faceted Filtering:** The UI allows users to toggle "Facets" (e.g., Date Range, Department, Diagnosis Code). The backend constructs a dynamic SQL query using a `WHERE` clause builder based on the selected facets.
    - **Ranking:** Search results are ranked by "Recency" and "Relevance" (keyword density).
- **Performance Target:** Search results must return in $< 400ms$ for a dataset of 1 million records.

### 3.4 Real-Time Collaborative Editing with Conflict Resolution
- **Priority:** Critical (Launch Blocker)
- **Status:** Blocked
- **Version:** v1.2.0 (Planned)
- **Description:** Multiple providers must be able to edit a patient's clinical note simultaneously. This prevents the "Last Write Wins" problem where one doctor's notes are accidentally overwritten by another.
- **Technical Logic (Proposed):**
    - The system will implement **Operational Transformation (OT)** or **Conflict-free Replicated Data Types (CRDTs)**.
    - When a user types, a "delta" is sent via WebSockets (Azure Web PubSub) to the server.
    - The server sequences these deltas and broadcasts them to all other active collaborators.
    - **Conflict Resolution:** If two users edit the same character offset, the server uses a timestamp-based resolution to determine the final state.
- **Blocker:** Currently blocked by infrastructure provisioning delays from the cloud provider regarding the specific Web PubSub SKU required for the EU region.

### 3.5 A/B Testing Framework (Integrated with LaunchDarkly)
- **Priority:** Medium
- **Status:** In Design
- **Version:** v1.3.0 (Planned)
- **Description:** A framework to test different UI layouts or clinical workflows. For example, testing whether a "Quick-Action" button on the search page increases feature adoption.
- **Technical Logic:**
    - Integration with LaunchDarkly's "Experimentation" module.
    - The app requests a feature flag state at startup. LaunchDarkly assigns the user to a "bucket" (A or B) based on their `UserUUID`.
    - The frontend conditionally renders components based on the flag.
    - Usage analytics (Feature 3.2) are tagged with the `ExperimentID` to measure the conversion rate.
- **Success Metric:** A feature is considered "winning" if it increases the task-completion rate by $\ge 15\%$.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are hosted under `https://api.parapet.nightjar.io/v1/`. Authentication requires a Bearer Token in the header.

### 4.1 `POST /auth/login`
- **Description:** Authenticates user and initiates 2FA challenge.
- **Request Body:**
  ```json
  { "username": "hpark_vp", "password": "hashed_password" }
  ```
- **Response (200 OK):**
  ```json
  { "temp_token": "abc-123", "requires_2fa": true, "challenge": "fido2_challenge_string" }
  ```

### 4.2 `POST /auth/verify-2fa`
- **Description:** Validates the hardware key signature.
- **Request Body:**
  ```json
  { "temp_token": "abc-123", "signature": "signed_challenge_blob" }
  ```
- **Response (200 OK):**
  ```json
  { "access_token": "jwt_token_here", "expires_in": 3600 }
  ```

### 4.3 `GET /patients/search`
- **Description:** Performs a faceted search across the patient database.
- **Query Parameters:** `q` (query), `facet_dept` (department), `facet_age` (min-max).
- **Example:** `/patients/search?q=diabetes&facet_dept=cardiology`
- **Response (200 OK):**
  ```json
  { "results": [ { "patient_id": "P101", "name": "John Doe", "relevance": 0.98 } ], "total": 1 }
  ```

### 4.4 `GET /patients/{id}/chart`
- **Description:** Retrieves the full clinical chart for a specific patient.
- **Response (200 OK):**
  ```json
  { "patient_id": "P101", "notes": [...], "labs": [...], "vitals": [...] }
  ```

### 4.5 `PATCH /patients/{id}/notes`
- **Description:** Updates a specific note (Used by Collaborative Editing).
- **Request Body:**
  ```json
  { "note_id": "N55", "delta": "Added: Patient reports mild nausea", "version": 12 }
  ```
- **Response (200 OK):**
  ```json
  { "status": "success", "new_version": 13 }
  ```

### 4.6 `GET /analytics/usage`
- **Description:** Returns usage statistics for the current tenant.
- **Response (200 OK):**
  ```json
  { "daily_active_users": 450, "avg_search_time": "320ms" }
  ```

### 4.7 `GET /system/health`
- **Description:** Checks heartbeat of serverless functions and DB connection.
- **Response (200 OK):**
  ```json
  { "status": "healthy", "region": "northeurope", "latency": "12ms" }
  ```

### 4.8 `POST /admin/feature-flags`
- **Description:** Manually overrides a feature flag for a specific test user.
- **Request Body:**
  ```json
  { "userId": "user_99", "flag": "realtime_edit_enabled", "value": true }
  ```
- **Response (200 OK):** `{ "updated": true }`

---

## 5. DATABASE SCHEMA

The database is an Azure SQL instance. Relationships are enforced via Foreign Keys, though some are "soft" to support the serverless scaling nature.

### 5.1 Table Definitions

| Table Name | Key Field | Description | Relationships |
| :--- | :--- | :--- | :--- |
| `Tenants` | `TenantID` (PK) | Hospital networks/clinics. | 1:N with `Users` |
| `Users` | `UserID` (PK) | Clinician profiles and roles. | N:1 with `Tenants` |
| `UserSecurityKeys` | `KeyID` (PK) | FIDO2 public keys for 2FA. | N:1 with `Users` |
| `Patients` | `PatientID` (PK) | Core patient demographic data. | N:1 with `Tenants` |
| `ClinicalNotes` | `NoteID` (PK) | The actual text of medical records. | N:1 with `Patients` |
| `NoteVersions` | `VersionID` (PK) | Audit trail of all note edits. | N:1 with `ClinicalNotes` |
| `LabResults` | `LabID` (PK) | Quantitative lab data. | N:1 with `Patients` |
| `SearchIndex` | `IndexID` (PK) | Flattened text for FTS. | 1:1 with `ClinicalNotes` |
| `AuditLogs` | `LogID` (PK) | GDPR compliance access logs. | N:1 with `Users` |
| `FeatureAssignments`| `AssignID` (PK) | Mapping users to A/B test buckets. | N:1 with `Users` |

### 5.2 Key Schema Detail: `ClinicalNotes` $\rightarrow$ `NoteVersions`
To support the "Critical" collaborative editing feature, the `ClinicalNotes` table acts as the current "head," while `NoteVersions` stores every incremental change (delta).
- `NoteVersions` fields: `VersionID` (GUID), `NoteID` (FK), `UserID` (FK), `DeltaText` (NVARCHAR(MAX)), `Timestamp` (DateTimeOffset).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Parapet employs a three-tier environment strategy to ensure that no unverified code reaches the clinical environment.

1.  **Development (Dev):**
    - **Purpose:** Feature development and unit testing.
    - **Infrastructure:** Shared Azure Function App, local SQL Express for developers.
    - **Deployment:** Triggered on every push to the `develop` branch.
2.  **Staging (Staging):**
    - **Purpose:** Integration testing and Stakeholder Demos.
    - **Infrastructure:** Mirrors Production exactly (Serverless SQL, APIM).
    - **Deployment:** Triggered by a Merge Request to `release/vX.X`.
3.  **Production (Prod):**
    - **Purpose:** Live clinical use.
    - **Infrastructure:** Geo-replicated Azure SQL, Multi-region Functions.
    - **Deployment:** Canary releases via LaunchDarkly. Only 5% of users see a new feature initially.

### 6.2 CI/CD Pipeline
The pipeline is managed via GitHub Actions:
- **Build:** Compiles C# code $\rightarrow$ Runs Unit Tests $\rightarrow$ Packages into Zip for Azure Functions.
- **Deploy:** Pushes to the designated slot (Blue/Green deployment).
- **Smoke Test:** An automated script hits `/system/health` and `/auth/login` to verify connectivity.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Focus:** Business logic within Azure Functions.
- **Tooling:** xUnit and Moq.
- **Requirement:** 80% code coverage on all "Critical" priority features.
- **Example:** Testing the `SearchQueryBuilder` to ensure that null facets do not result in `WHERE 1=0` queries.

### 7.2 Integration Testing
- **Focus:** The interaction between the API Gateway, Azure Functions, and Azure SQL.
- **Approach:** Postman collection scripts run against the Staging environment.
- **Key Scenario:** Verify that a user in the EU region cannot access a patient record hosted in the US region.

### 7.3 End-to-End (E2E) Testing
- **Focus:** The complete user journey from login to data retrieval.
- **Tooling:** Appium (for mobile automation).
- **Critical Path:** Login $\rightarrow$ 2FA $\rightarrow$ Search for Patient $\rightarrow$ Open Note $\rightarrow$ Edit Note $\rightarrow$ Save.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Regulatory requirements (GDPR/CCPA) change. | High | High | Hire a specialized healthcare compliance contractor to reduce "bus factor" and ensure policy alignment. |
| **R2** | Competitor is 2 months ahead in feature parity. | Medium | High | De-scope non-essential "Nice to have" features (e.g., usage analytics) to accelerate the "Critical" features. |
| **R3** | Cloud provider latency in EU region. | Medium | Medium | Implement aggressive caching via Azure Redis Cache for frequently accessed charts. |
| **R4** | Technical debt from hardcoded configs. | High | Medium | Dedicate Sprint 8 entirely to "Configuration Refactoring" (moving 40+ files to Azure App Configuration). |

**Probability/Impact Matrix:**
- **High/High:** Immediate action required (R1, R2).
- **High/Medium:** Planned mitigation (R4).
- **Medium/Medium:** Monitored (R3).

---

## 9. TIMELINE AND GANTT DESCRIPTION

The project is divided into four primary phases. All dates are targets.

### Phase 1: Foundation (Now $\rightarrow$ 2026-05-15)
- **Focus:** Core infrastructure, Auth, and Database setup.
- **Dependency:** Infrastructure provisioning (Current Blocker).
- **Key Milestone:** **Milestone 1: Architecture review complete (2026-05-15).**

### Phase 2: Capability Build (2026-05-16 $\rightarrow$ 2026-07-15)
- **Focus:** Search implementation, Collaborative Editing (once unblocked), and UI polishing.
- **Dependency:** Completion of Phase 1.
- **Key Milestone:** **Milestone 2: Stakeholder demo and sign-off (2026-07-15).**

### Phase 3: Pilot & Hardening (2026-07-16 $\rightarrow$ 2026-09-15)
- **Focus:** Onboarding first pilot users, A/B testing, and bug fixing.
- **Dependency:** Sign-off from Milestone 2.
- **Key Milestone:** **Milestone 3: First paying customer onboarded (2026-09-15).**

### Phase 4: Scale (2026-09-16 $\rightarrow$ 2027-03-15)
- **Focus:** Reaching 10,000 MAU, refining the A/B testing framework, and expanding regional data residency.

---

## 10. MEETING NOTES

### Meeting 1: Initial Team Sync (2025-11-01)
- **Attendees:** Hiro, Hessa, Uri, Nyla.
- **Notes:**
    - Team is new. Trust building is a goal.
    - Hiro emphasizes "Moonshot" nature. High risk, high reward.
    - Uri concerned about GDPR.
    - Hessa wants to use .NET MAUI.
    - Decision: Go with full Microsoft stack for speed.

### Meeting 2: The "Blocker" Discussion (2026-01-15)
- **Attendees:** Hiro, Uri.
- **Notes:**
    - EU Web PubSub SKU not appearing in portal.
    - Ticket opened with Azure support.
    - "Critical" feature 4 is now officially BLOCKED.
    - Hiro: "We can't launch without real-time editing. Push Azure."

### Meeting 3: Tech Debt Review (2026-03-10)
- **Attendees:** Hessa, Nyla, Uri.
- **Notes:**
    - Nyla found hardcoded DB strings in 40+ files.
    - "Nightmare for rotation."
    - Agree to use Azure App Configuration.
    - Schedule a "cleanup sprint" after Milestone 1.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,200,000

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,120,000 | 4 FTEs over 18 months + specialized contractor. |
| **Infrastructure** | 20% | $1,040,000 | Azure Consumption (SQL, Functions, APIM, Redis). |
| **Tools & Licensing**| 10% | $520,000 | LaunchDarkly Enterprise, Appium, GitHub Enterprise. |
| **Contingency** | 10% | $520,000 | For regulatory pivots or urgent hiring. |

**Personnel Detail:**
- VP Product (Hiro): $250k/yr
- Frontend Lead (Hessa): $180k/yr
- Security Engineer (Uri): $180k/yr
- Junior Dev (Nyla): $90k/yr
- Compliance Contractor: $150k flat fee.

---

## 12. APPENDICES

### Appendix A: Data Encryption Standard
Parapet utilizes **AES-256** for data at rest within Azure SQL. For data in transit, **TLS 1.3** is mandatory. The "Encryption Key" for each tenant is managed via **Azure Key Vault**, ensuring that Nightjar Systems employees cannot access patient data without an explicit, audited request.

### Appendix B: Conflict Resolution Logic (Pseudo-code)
For the blocked Collaborative Editing feature, the intended logic is as follows:
```csharp
public class ConflictResolver {
    public string Resolve(Delta local, Delta remote) {
        if (local.Offset == remote.Offset) {
            return (local.Timestamp > remote.Timestamp) ? local.Text : remote.Text;
        }
        return MergeSequential(local, remote);
    }
}
```
*Note: This logic will be replaced by a full CRDT implementation upon unblocking of the infrastructure.*