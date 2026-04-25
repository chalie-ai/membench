Due to the extreme length requirement (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification Document. It is structured to serve as the "Single Source of Truth" (SSOT) for the development team at Iron Bay Technologies.

***

# PROJECT SPECIFICATION: SENTINEL
**Project Code:** SENT-2025-IBT  
**Version:** 1.0.4 (Baseline)  
**Status:** Active/Development  
**Classification:** Confidential - Internal Use Only  
**Last Updated:** October 24, 2023  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project **Sentinel** is a high-stakes, customer-facing rebuild of the healthcare records platform for Iron Bay Technologies. Operating within the retail health sector, Iron Bay Technologies provides critical record management for a vast network of retail clinics and pharmacy hubs. The project is born out of necessity: the current legacy system has suffered catastrophic user feedback, characterized by extreme latency, unintuitive UX, and systemic instability. Sentinel is not merely a version update but a complete architectural overhaul designed to restore customer trust and establish a scalable foundation for the next decade of growth.

### 1.2 Business Justification
The retail healthcare market demands instantaneous access to patient data. The legacy system's failure to provide performant search and reliable data portability has led to a documented 14% churn rate in enterprise contracts over the last three fiscal quarters. The board has designated Sentinel as the company’s flagship initiative for 2024-2025, with a dedicated budget exceeding $5,000,000.

The business objective is twofold: first, to eliminate the "performance gap" that has alienated the user base, and second, to transition the infrastructure from a rigid legacy monolith to a flexible, modular architecture that can support rapid feature iteration. By improving the user experience and operational efficiency, Iron Bay Technologies aims to recapture lost market share and increase the Average Revenue Per User (ARPU) by offering higher-tier automation tools.

### 1.3 ROI Projection and Financial Impact
The financial success of Sentinel will be measured by two primary drivers: cost reduction and retention. 

1. **Operational Efficiency:** The current system is plagued by inefficient queries and redundant data processing. A core success criterion for Sentinel is a **35% reduction in cost per transaction**. By optimizing the Oracle DB indexing and streamlining the Spring Boot application layer, we expect to reduce the compute overhead per request, translating to a projected annual savings of $420,000 in operational overhead.
2. **Customer Retention:** By resolving the "catastrophic" feedback issues—specifically the search latency and import errors—Sentinel is projected to reduce churn by 60% within the first year of full deployment.
3. **Revenue Growth:** The introduction of the Workflow Automation Engine (Priority: Medium) will allow Iron Bay to move from a "Standard" pricing model to a "Premium" tiered model, projecting an incremental revenue increase of $1.2M in Year 2.

The Total Cost of Ownership (TCO) for this project is capped at $5M. With the projected efficiency gains and retention improvements, the Break-Even Point (BEP) is estimated at 18 months post-launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Sentinel is built on a **Java/Spring Boot** ecosystem utilizing an **Oracle Database** backend. Due to strict regulatory requirements and internal corporate policy, the system must reside entirely within the company's **on-premise data center**. No cloud providers (AWS, GCP, Azure) are permitted for production data storage or processing.

The architecture follows a **Modular Monolith** pattern. This approach allows the team to maintain a single deployment pipeline for stability while logically separating domains (Search, Identity, Data Management, Automation) into distinct modules. This structure facilitates an incremental transition to a full microservices architecture as the system matures.

### 2.2 Architectural Diagram (ASCII)

```text
[ CLIENT LAYER ] 
       |
       ▼
[ LOAD BALANCER / REVERSE PROXY (Nginx) ]
       |
       ▼
[ SENTINEL APPLICATION SERVER (Spring Boot) ]
+-----------------------------------------------------------------------+
| [ API Gateway / Security Filter (ISO 27001 Compliant) ]                |
+-----------------------+-----------------------+-----------------------+
| [ Search Module ]     | [ Data Import Module ] | [ Auth/Identity Mod ] |
|  - ElasticSearch-like|  - Format Detector    |  - 2FA / Hardware Keys |
|  - Faceted Logic      |  - ETL Pipelines      |  - Session Mgmt       |
+-----------------------+-----------------------+-----------------------+
| [ Automation Module ] | [ Feature Flag Engine ] | [ Admin Module ]    |
|  - Rule Builder       |  - A/B Testing Logic   |  - Audit Logs        |
+-----------------------+-----------------------+-----------------------+
       |                                               |
       ▼                                               ▼
[ DATA PERSISTENCE LAYER ]                      [ FILE SYSTEM / BLOB ]
+--------------------------------------+       +----------------------+
| Oracle DB (19c)                      |       | On-Premise SAN        |
| - Patient Records (Relational)        | <---> | - PDF Exports        |
| - Index Tables (Full-Text)           |       | - XML/CSV Raw Imports |
| - Audit Trails (Immutable)           |       +----------------------+
+--------------------------------------+
```

### 2.3 Infrastructure Constraints
The environment must be **ISO 27001 certified**. This necessitates strict network segmentation, encrypted data-at-rest using AES-256, and encrypted data-in-transit via TLS 1.3. The deployment process is gated by a manual QA process, ensuring that no code reaches production without a signed-off UAT (User Acceptance Testing) report, resulting in a standard 2-day deployment turnaround.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: Critical)
**Status: Not Started | Launch Blocker**

**Description:**
The primary failure of the legacy system was its inability to handle complex queries across millions of healthcare records. Sentinel will implement a high-performance search engine utilizing full-text indexing. Users must be able to search for patient records using keywords, dates, or specific medical codes, with the ability to narrow results through a "faceted" interface (e.g., filtering by clinic location, age range, or diagnosis type).

**Functional Requirements:**
- **Full-Text Indexing:** Implement an inverted index within Oracle DB (Oracle Text) to allow for lightning-fast keyword searches across patient notes and histories.
- **Faceted Navigation:** The API must return not only the search results but also a count of records available per category (e.g., "Diabetes: 450", "Hypertension: 300").
- **Boolean Logic:** Support for AND, OR, and NOT operators in the search bar.
- **Performance Target:** All search queries must return results in < 200ms (p95) regardless of the filter complexity.

**Technical Implementation:**
The search module will utilize a specialized `SearchService` in Spring Boot that translates user-facing facets into optimized SQL queries. To avoid table scans, the system will leverage materialized views for the most common filter combinations.

---

### 3.2 Data Import/Export with Format Auto-Detection (Priority: High)
**Status: In Progress**

**Description:**
Healthcare records arrive in various formats (HL7, FHIR, CSV, XML). The current system requires users to manually specify the format, leading to frequent import failures. Sentinel will introduce an "Intelligence Layer" that analyzes the file header and structure to automatically detect the format and map it to the internal schema.

**Functional Requirements:**
- **Auto-Detection:** The system must identify the file type based on magic bytes and structural patterns.
- **Mapping Engine:** A configurable mapping layer that allows administrators to define how external fields map to Oracle DB columns.
- **Bulk Processing:** Support for files up to 2GB, processed via an asynchronous queue to prevent request timeouts.
- **Export Versatility:** Ability to export any patient record set into the same supported formats.

**Technical Implementation:**
A `FileAnalysisService` will use a strategy pattern to attempt parsing the file with different "Detectors." Once the format is identified, a `TransformationService` (using Apache Camel) will convert the data into the internal Canonical Data Model (CDM) before persisting it to the database.

---

### 3.3 Two-Factor Authentication with Hardware Key Support (Priority: Medium)
**Status: In Design**

**Description:**
Given the sensitivity of healthcare data, password-based authentication is insufficient. Sentinel will implement a robust MFA (Multi-Factor Authentication) system. While standard TOTP (Time-based One-Time Password) apps will be supported, the primary requirement is support for hardware security keys (FIDO2/WebAuthn) to prevent phishing attacks.

**Functional Requirements:**
- **Hardware Integration:** Support for YubiKey and Google Titan keys via the WebAuthn API.
- **Fallback Mechanism:** Secure email/SMS backup codes for users who lose their hardware keys.
- **Enforced Enrollment:** Mandatory 2FA setup for all administrative and clinical roles during the first login after migration.

**Technical Implementation:**
The `SecurityModule` will integrate the `spring-security-webauthn` library. The database will store public keys associated with user accounts, and the authentication flow will require a signed challenge from the hardware device before granting a JWT (JSON Web Token) for session access.

---

### 3.4 A/B Testing Framework for Feature Flags (Priority: Medium)
**Status: Blocked**

**Description:**
To avoid the "catastrophic" rollout failures of the past, Sentinel will bake A/B testing directly into the feature flag system. This allows the team to release new features to a small percentage of the user base (e.g., 5% of clinics) and measure performance/feedback before a global rollout.

**Functional Requirements:**
- **Percentage-Based Rollout:** Ability to toggle features for a specific % of users.
- **User Segmenting:** Targeted flags based on user role, region, or clinic size.
- **Telemetry Integration:** Automated tracking of the "success metric" for the B-variant compared to the A-variant.

**Technical Implementation:**
A `FeatureFlagService` will maintain a mapping of `FeatureKey -> UserID -> Variant`. This will be cached in Redis (on-prem) to ensure that checking a flag does not add latency to the request.

---

### 3.5 Workflow Automation Engine with Visual Rule Builder (Priority: Medium)
**Status: Blocked**

**Description:**
The "flagship" value-add for Sentinel is the ability for clinic administrators to automate repetitive tasks (e.g., "If patient is over 65 and has not had a checkup in 6 months, send a notification to the nurse"). This will be achieved via a visual "drag-and-drop" rule builder.

**Functional Requirements:**
- **Visual Logic Flow:** A frontend canvas where users can link "Triggers" $\rightarrow$ "Conditions" $\rightarrow$ "Actions."
- **Rule Validation:** Real-time checking to prevent infinite loops or conflicting rules.
- **Execution Engine:** A background worker that evaluates rules against incoming data events.

**Technical Implementation:**
The engine will use a Drools-based rule evaluation system. The visual builder will generate a JSON representation of the logic, which is then parsed into Drools' `.drl` format for execution.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All responses are in JSON format.

### 4.1 Search Endpoints
**`GET /search/patients`**
- **Description:** Executes a faceted search for patients.
- **Request Params:** `q` (query string), `facet_location` (string), `facet_age_min` (int), `facet_age_max` (int).
- **Response:**
  ```json
  {
    "results": [{ "id": "P123", "name": "John Doe", "score": 0.98 }],
    "facets": {
      "locations": { "NorthClinic": 120, "SouthClinic": 85 },
      "diagnoses": { "Hypertension": 45, "Diabetes": 30 }
    },
    "total": 205
  }
  ```

**`GET /search/suggestions`**
- **Description:** Provides autocomplete suggestions as the user types.
- **Request Params:** `term` (string).
- **Response:** `["John Doe", "Jane Smith", "Johnathan Apple"]`

### 4.2 Data Management Endpoints
**`POST /import/upload`**
- **Description:** Uploads a file for processing.
- **Request:** Multipart File.
- **Response:** `{ "jobId": "JOB_9982", "status": "processing", "detectedFormat": "HL7" }`

**`GET /import/status/{jobId}`**
- **Description:** Polls the status of a specific import job.
- **Response:** `{ "jobId": "JOB_9982", "progress": "65%", "errors": 0 }`

**`POST /export/generate`**
- **Description:** Triggers a data export.
- **Request:** `{ "patientIds": ["P1", "P2"], "format": "CSV" }`
- **Response:** `{ "downloadUrl": "/api/v1/export/download/XYZ123" }`

### 4.3 Identity & Security Endpoints
**`POST /auth/register-key`**
- **Description:** Registers a FIDO2 hardware key.
- **Request:** `{ "userId": "U1", "publicKey": "..." }`
- **Response:** `{ "status": "success", "deviceId": "KEY_001" }`

**`POST /auth/verify-mfa`**
- **Description:** Validates the second factor during login.
- **Request:** `{ "userId": "U1", "token": "123456" }`
- **Response:** `{ "sessionToken": "JWT_ABC_123", "expires": "2025-10-24T12:00:00Z" }`

**`GET /user/profile`**
- **Description:** Retrieves current authenticated user details.
- **Response:** `{ "username": "tmoreau", "role": "CTO", "mfaEnabled": true }`

---

## 5. DATABASE SCHEMA

The system utilizes an Oracle 19c database. All tables use `VARCHAR2` for strings and `NUMBER` for numeric values.

### 5.1 Table Definitions

| Table Name | Purpose | Primary Key | Key Relationships |
| :--- | :--- | :--- | :--- |
| `USERS` | User account and auth data | `user_id` | $\rightarrow$ `USER_KEYS` |
| `USER_KEYS` | FIDO2 Public Keys | `key_id` | $\rightarrow$ `USERS` |
| `PATIENTS` | Core patient demographics | `patient_id` | $\rightarrow$ `MEDICAL_RECORDS` |
| `MEDICAL_RECORDS` | Clinical notes and data | `record_id` | $\rightarrow$ `PATIENTS` |
| `CLINICS` | Retail location details | `clinic_id` | $\rightarrow$ `PATIENTS` |
| `IMPORT_JOBS` | Tracking file imports | `job_id` | $\rightarrow$ `USERS` (created_by) |
| `IMPORT_ERRORS` | Log of failed import rows | `error_id` | $\rightarrow$ `IMPORT_JOBS` |
| `FEATURE_FLAGS` | State of system flags | `flag_id` | N/A |
| `USER_FLAG_MAP` | Which user sees which variant | `map_id` | $\rightarrow$ `USERS`, `FEATURE_FLAGS` |
| `AUTOMATION_RULES` | Defined workflow logic | `rule_id` | $\rightarrow$ `USERS` (owner) |

### 5.2 Detailed Fields (Example: `PATIENTS` Table)
- `patient_id` (NUMBER, PK): Unique identifier.
- `first_name` (VARCHAR2 100): Patient's first name.
- `last_name` (VARCHAR2 100): Patient's last name.
- `dob` (DATE): Date of birth.
- `clinic_id` (NUMBER, FK): Reference to `CLINICS` table.
- `last_updated` (TIMESTAMP): Audit timestamp.
- `search_vector` (Oracle Text): Full-text index vector for rapid search.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Sentinel utilizes a three-tier environment strategy. All environments are hosted in the Iron Bay on-premise data center.

1. **Development (DEV):**
   - **Purpose:** Active feature development and unit testing.
   - **Access:** Full access for the team of 8.
   - **Database:** Shared Oracle instance with mocked data.
2. **Staging (STG):**
   - **Purpose:** Pre-production validation and UAT.
   - **Access:** Limited to QA and Project Lead (Tomas Moreau).
   - **Database:** Mirror of production schema with scrubbed (anonymized) production data.
3. **Production (PROD):**
   - **Purpose:** Live customer-facing environment.
   - **Access:** Restricted. Deployments occur via a gated pipeline.
   - **Database:** High-availability Oracle RAC cluster.

### 6.2 Deployment Process (The "QA Gate")
Deployments to Production are not automated via CI/CD but follow a **Manual QA Gate** process:
1. Code is merged to `main` and deployed to STG.
2. A full regression suite is run.
3. The Project Lead (Tomas Moreau) and the Security Engineer (Nia Liu) must sign off on the UAT report.
4. Upon approval, a manual deployment trigger is activated.
5. **Turnaround:** Total time from STG approval to PROD deployment is 2 business days.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Requirement:** 80% minimum code coverage for all new services.
- **Focus:** Testing business logic in isolation from the Oracle DB.

### 7.2 Integration Testing
- **Framework:** SpringBootTest with Testcontainers (Oracle XE).
- **Focus:** Validating the interaction between the Spring Boot services and the Oracle DB, specifically focusing on the complex SQL joins required for faceted search.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium / Playwright.
- **Scenario Focus:**
  - User logs in $\rightarrow$ Performs faceted search $\rightarrow$ Views patient record.
  - Admin uploads 500MB CSV $\rightarrow$ Polls status $\rightarrow$ Verifies data in DB.
  - User registers YubiKey $\rightarrow$ Logs out $\rightarrow$ Logs in using MFA.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Primary vendor end-of-life for core library | High | Critical | Build a contingency "Abstraction Layer" to allow swapping the vendor library without rewriting business logic. |
| **R-02** | Performance reqs (10x) without extra budget | High | High | Implement aggressive caching (Redis) and optimize Oracle indexing; document workarounds for peak load. |
| **R-03** | Infrastructure provisioning delays | Medium | High | (Current Blocker) Negotiate with on-prem hardware team; use temporary virtualized environments for DEV. |
| **R-04** | ISO 27001 Compliance failure | Low | Critical | Weekly security audits conducted by Nia Liu. |

### 8.1 Probability/Impact Matrix
- **Critical:** System cannot launch (Search, Security).
- **High:** Significant degradation of user experience (Import/Export).
- **Medium:** Delayed roadmap items (Automation, A/B Testing).

---

## 9. TIMELINE

### 9.1 Phase Descriptions
- **Phase 1: Core Foundation (Jan 2025 - July 2025)**
  - Focus: Search Engine and Data Import.
  - Dependency: Hardware provisioning.
- **Phase 2: Security & Hardening (July 2025 - Nov 2025)**
  - Focus: MFA and ISO 27001 audit.
  - Dependency: Stable Core Foundation.
- **Phase 3: Advanced Features (Nov 2025 - March 2026)**
  - Focus: A/B Testing and Automation Engine.

### 9.2 Key Milestones
- **2025-07-15:** Performance benchmarks met (p95 < 200ms).
- **2025-09-15:** Internal alpha release (Limited to Iron Bay staff).
- **2025-11-15:** Security audit passed (Official ISO 27001 Certification).

---

## 10. MEETING NOTES (SLACK ARCHIVE)

As per team policy, formal minutes are not taken. The following are syntheses of key decisions from Slack threads.

### Meeting 1: Architecture Alignment (Thread: #sentinel-dev-sync)
- **Discussion:** Veda argued for a full microservices approach from Day 1 to handle the 10x load. Tomas (CTO) countered that the team size (8) is too small to manage the operational overhead of 20+ services.
- **Decision:** Adopt a **Modular Monolith**. Maintain one deployment unit but strictly separate packages by domain. This allows for easier transition to microservices in 2026.

### Meeting 2: Search Performance Crisis (Thread: #sentinel-search-perf)
- **Discussion:** Lior (Intern) discovered that the standard `LIKE` queries were taking 12 seconds on the 1M record test set.
- **Decision:** Veda and Lior will pivot to using **Oracle Text** for full-text indexing. This removes the need for an external ElasticSearch cluster, keeping the project within the on-prem budget and simplifying the stack.

### Meeting 3: Infrastructure Blocker (Thread: #sentinel-ops)
- **Discussion:** Nia reported that the on-prem server rack provisioning was delayed because the "cloud provider" (internal private cloud team) had a backlog.
- **Decision:** Tomas will escalate to the board. In the meantime, the team will use localized Docker containers to simulate the Oracle environment to avoid blocking the `Data Import` feature progress.

---

## 11. BUDGET BREAKDOWN

Total Budget: **$5,000,000+**

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,000,000 | 8 FTEs for 18 months (including CTO, Security, Data Eng). |
| **Infrastructure** | 20% | $1,000,000 | On-prem Oracle licenses, SAN storage, Server hardware. |
| **Tools & Licenses** | 10% | $500,000 | IDEs, Security scanning tools, ISO Certification audits. |
| **Contingency** | 10% | $500,000 | Reserve for vendor EOL fallback architecture. |

---

## 12. APPENDICES

### Appendix A: Data Import Format Matrix
This table defines how the `FormatAutoDetector` identifies incoming files.

| Format | Magic Bytes / Pattern | Validation Rule |
| :--- | :--- | :--- |
| **HL7 v2** | `MSH^~\` | Must start with MSH segment. |
| **FHIR (JSON)** | `{ "resourceType":` | Must contain valid JSON and `resourceType` key. |
| **CSV** | Comma-delimited text | Header must match known patient field set. |
| **XML** | `<?xml version=...` | Must validate against XSD schema. |

### Appendix B: Hardware Key Specification (WebAuthn)
To maintain ISO 27001 compliance, the following hardware specifications are required for the 2FA system:
- **Algorithm:** ECDSA with P-256 curve.
- **Attestation:** Direct attestation required for all clinical staff.
- **User Verification:** PIN or Biometric must be enabled on the hardware key to prevent unauthorized use of a stolen key.
- **Browser Support:** Minimum Chrome 66, Firefox 60, Safari 13.