# PROJECT SPECIFICATION DOCUMENT: PROJECT VANGUARD
**Version:** 1.0.4  
**Date:** October 24, 2023  
**Status:** Draft / Internal Review  
**Document Owner:** Gideon Park (Engineering Manager)  
**Confidentiality Level:** Highly Confidential (Silverthread AI Internal)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Vanguard represents Silverthread AI’s strategic entry into the healthcare SaaS sector. Historically, Silverthread AI has operated in general-purpose AI and data analytics; however, the healthcare vertical presents a significant opportunity for high-margin, long-term contracts due to the criticality of the data and the high barrier to entry regarding compliance and security. Vanguard is designed as a greenfield product, meaning it is built from the ground up to avoid the legacy constraints of the company’s previous offerings.

The healthcare market is currently underserved in terms of integrated, real-time collaborative data management that adheres to strict on-premise residency requirements. By positioning Vanguard as a "sovereign" SaaS—where data never leaves the client’s controlled on-premise data center environment—Silverthread AI can capture a segment of the market that is terrified of the public cloud (AWS/Azure/GCP) due to regulatory scrutiny and the risk of data leaks.

### 1.2 ROI Projection
The project is funded with a modest budget of $400,000. Given the niche nature of the on-premise healthcare requirement, Silverthread AI anticipates a high Average Revenue Per User (ARPU). 

**Financial Projections:**
- **Year 1 (Development & Pilot):** Net Loss of $400k (CAPEX).
- **Year 2 (Market Entry):** Target of 12 enterprise clients with an average annual contract value (ACV) of $150,000. Projected Revenue: $1.8M.
- **Year 3 (Scaling):** Expansion to 30 clients. Projected Revenue: $4.5M.

The Break-Even Point (BEP) is estimated to occur in Month 14 post-launch (approximately August 2026). The primary ROI driver is the "stickiness" of the product; once a healthcare provider integrates their patient data and audit trails into the Vanguard system on their own servers, the switching costs become prohibitively high, ensuring a Customer Lifetime Value (CLV) that far exceeds the initial acquisition cost.

### 1.3 Strategic Objectives
1. **Market Penetration:** Establish a foothold in the EU healthcare market.
2. **Compliance Leadership:** Achieve a gold standard in GDPR and CCPA compliance through physical data residency.
3. **Technical Validation:** Prove that a serverless orchestration model can function effectively within a traditional on-premise Oracle DB environment.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 High-Level Design
Vanguard utilizes a hybrid architecture that combines the flexibility of serverless functions with the stability of a traditional on-premise data center. Because the client mandates that no data may reside in the cloud, all "serverless" functions are implemented via a private container orchestration layer (Knative/Kubernetes) residing within the on-premise facility.

**The Stack:**
- **Backend:** Java 17 with Spring Boot 3.x.
- **Database:** Oracle Database 19c (Enterprise Edition).
- **Orchestration:** API Gateway (Kong) managing requests to discrete Spring Boot functions.
- **Storage:** Local SAN for file uploads and Oracle Tablespaces for structured data.

### 2.2 Architecture Diagram (ASCII Description)
```text
[ USER BROWSER / CLIENT APP ] 
          |
          v
[ ON-PREMISE FIREWALL / LOAD BALANCER ]
          |
          v
[ KONG API GATEWAY (Orchestration Layer) ]
          |
          +---------------------------------------------------+
          |                           |                       |
 [ FUNCTION: AUTH/LOGGING ]  [ FUNCTION: FILE MGMT ]  [ FUNCTION: COLLAB ]
          |                           |                       |
          +---------------------------+-----------------------+
                                      |
                                      v
                       [ ORACLE DB 19c (On-Prem) ]
                                      |
                       [ TAMPER-EVIDENT LOG STORE ]
                                      |
                       [ LOCAL CDN / FILE STORAGE ]
```

### 2.3 Technical Constraints & Decisions
- **No Cloud:** All components must be deployable via `.jar` or Docker images to a private server.
- **Serverless Orchestration:** To maintain scalability, the system avoids a monolithic Spring Boot app. Instead, it uses "function-style" microservices.
- **The "God Class" Debt:** Current implementation contains a `SystemCoreManager.java` file (approx. 3,000 lines). This class currently handles `AuthService`, `LoggerService`, and `EmailDispatcher`. It is a critical piece of technical debt that must be refactored into separate services to avoid system-wide crashes during updates.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customer-Facing API with Versioning & Sandbox
**Priority:** Medium | **Status:** In Progress
**Description:** Vanguard must provide a robust API for healthcare partners to integrate their own Electronic Health Record (EHR) systems with the platform.

**Functional Specifications:**
- **Versioning:** The API will use URI versioning (e.g., `/api/v1/...`). When a new version is released, the previous version must be supported for 6 months.
- **Sandbox Environment:** A mirrored, non-production environment where developers can test API calls against mocked patient data without affecting real records.
- **Rate Limiting:** To prevent on-premise server exhaustion, the API Gateway will enforce a limit of 1,000 requests per minute per API key.
- **Authentication:** OAuth2 with JWT (JSON Web Tokens) signed by the internal `SystemCoreManager` (pending refactor).

**Technical Detail:**
The sandbox will utilize a separate Oracle schema (`VANGUARD_SANDBOX`) to ensure complete logical isolation. Any data written to the sandbox is wiped every 30 days.

### 3.2 File Upload with Virus Scanning and CDN Distribution
**Priority:** Critical | **Status:** In Progress (Launch Blocker)
**Description:** Healthcare providers need to upload medical imagery (DICOM, PDF) and lab results. Given the sensitivity, these files must be scanned for malware before being stored.

**Functional Specifications:**
- **Upload Pipeline:** Files are uploaded to a temporary "Quarantine" directory.
- **Virus Scanning:** Integration with an on-premise ClamAV instance. Files are scanned synchronously; if a threat is detected, the file is deleted, and a security alert is triggered.
- **CDN Distribution:** Since public CDNs (Cloudflare/Akamai) are forbidden, Vanguard implements a "Private CDN"—a set of cached edge servers within the client's internal network to reduce latency for large image files.
- **File Types:** Support for `.pdf`, `.jpg`, `.png`, `.dicom`, and `.csv`.

**Technical Detail:**
The upload function will utilize a multipart request handled by a Spring Boot service. The "Private CDN" logic involves a Nginx cache layer that intercepts requests for static assets from the Oracle DB's BLOB storage.

### 3.3 Notification System (Email, SMS, In-App, Push)
**Priority:** High | **Status:** In Review
**Description:** A multi-channel notification engine to alert clinicians of critical patient updates or system alerts.

**Functional Specifications:**
- **Email:** Integration with the internal corporate SMTP server.
- **SMS:** Integration via a local GSM gateway or approved healthcare SMS provider (e.g., Twilio via a secure proxy).
- **In-App:** A WebSocket-based notification bell in the UI.
- **Push:** Integration with mobile device managers (MDM) used by hospital staff.
- **Preference Center:** Users can opt-out of specific channels (e.g., "No SMS for non-critical alerts").

**Technical Detail:**
The system will use a "Notification Queue" (RabbitMQ on-prem) to ensure that a failure in the SMS gateway doesn't block the delivery of an urgent email.

### 3.4 Real-Time Collaborative Editing with Conflict Resolution
**Priority:** High | **Status:** Not Started
**Description:** Multiple clinicians must be able to edit a patient's care plan simultaneously without overwriting each other's changes.

**Functional Specifications:**
- **Operational Transformation (OT):** The system must implement OT or CRDTs (Conflict-free Replicated Data Types) to handle concurrent edits.
- **Presence Indicators:** Users must see who else is currently editing the document (avatars with "typing..." indicators).
- **Locking Mechanism:** For critical fields (e.g., Medication Dosage), a "pessimistic lock" is required—the first person to click the field locks it for others.
- **Version History:** Every "Save" creates a snapshot of the document.

**Technical Detail:**
This will be implemented using Spring WebSockets (STOMP). The state will be cached in an on-premise Redis instance before being persisted to the Oracle DB to avoid excessive disk I/O.

### 3.5 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Medium | **Status:** Not Started
**Description:** For legal compliance (GDPR/CCPA), every single action in the system must be logged in a way that proves the logs haven't been altered.

**Functional Specifications:**
- **Granularity:** Log must capture: User ID, Timestamp, IP Address, Action, Old Value, New Value.
- **Tamper-Evidence:** Each log entry will contain a cryptographic hash of the previous entry (a linear hash chain).
- **Immutable Storage:** Logs will be written to a "Write-Once-Read-Many" (WORM) storage volume on the on-premise SAN.
- **Reporting:** An admin interface to export audit logs as signed PDFs.

**Technical Detail:**
The hashing will be performed using SHA-256. The `SystemCoreManager` currently handles basic logging, but this feature requires a new `AuditService` to avoid adding to the "God Class" complexity.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a `Bearer <JWT>` token in the header.

### 4.1 User Management
**Endpoint:** `POST /users/create`
- **Description:** Creates a new healthcare provider account.
- **Request Body:**
  ```json
  {
    "email": "dr.smith@hospital.eu",
    "role": "CLINICIAN",
    "department": "Cardiology",
    "region": "EU-WEST"
  }
  ```
- **Response (201 Created):**
  ```json
  { "userId": "USR-9921", "status": "PENDING_VERIFICATION" }
  ```

**Endpoint:** `GET /users/{userId}/profile`
- **Description:** Retrieves profile details for a specific user.
- **Response (200 OK):**
  ```json
  { "userId": "USR-9921", "name": "Dr. Smith", "role": "CLINICIAN" }
  ```

### 4.2 File Management
**Endpoint:** `POST /files/upload`
- **Description:** Uploads a medical file for virus scanning.
- **Request:** Multipart Form Data (File, PatientId).
- **Response (202 Accepted):**
  ```json
  { "fileId": "FILE-101", "scanStatus": "QUEUED" }
  ```

**Endpoint:** `GET /files/{fileId}/status`
- **Description:** Checks if the virus scan is complete.
- **Response (200 OK):**
  ```json
  { "fileId": "FILE-101", "status": "CLEAN", "url": "/cdn/files/FILE-101.pdf" }
  ```

### 4.3 Patient Records (Collaborative)
**Endpoint:** `GET /patients/{patientId}/care-plan`
- **Description:** Fetches the current collaborative care plan.
- **Response (200 OK):**
  ```json
  { "patientId": "PAT-55", "content": "...", "version": 12 }
  ```

**Endpoint:** `PATCH /patients/{patientId}/care-plan`
- **Description:** Sends a delta update for real-time editing.
- **Request Body:**
  ```json
  { "delta": "insert 'dosage 5mg' at index 142", "version": 12 }
  ```
- **Response (200 OK):** `{ "status": "MERGED", "newVersion": 13 }`

### 4.4 Audit & Compliance
**Endpoint:** `GET /audit/logs?userId={userId}`
- **Description:** Retrieves audit history for a specific user.
- **Response (200 OK):**
  ```json
  [
    { "timestamp": "2023-10-24T10:00Z", "action": "VIEW_RECORD", "hash": "a1b2c3d4..." }
  ]
  ```

**Endpoint:** `POST /audit/verify-integrity`
- **Description:** Triggers a full hash-chain verification of the audit logs.
- **Response (200 OK):** `{ "integrity": "VALID", "lastVerified": "2023-10-24" }`

---

## 5. DATABASE SCHEMA

**Database:** Oracle 19c  
**Schema Name:** `VANGUARD_PROD`

### 5.1 Tables and Relationships

1.  **`USERS`**
    - `USER_ID` (PK, VARCHAR2(50))
    - `EMAIL` (UNIQUE, VARCHAR2(255))
    - `PASSWORD_HASH` (VARCHAR2(512))
    - `ROLE_ID` (FK $\rightarrow$ `ROLES.ROLE_ID`)
    - `CREATED_AT` (TIMESTAMP)

2.  **`ROLES`**
    - `ROLE_ID` (PK, INT)
    - `ROLE_NAME` (VARCHAR2(50)) - (e.g., Admin, Clinician, Auditor)
    - `PERMISSIONS` (CLOB) - JSON string of permission flags.

3.  **`PATIENTS`**
    - `PATIENT_ID` (PK, VARCHAR2(50))
    - `FULL_NAME` (VARCHAR2(255))
    - `DOB` (DATE)
    - `REGION` (VARCHAR2(10)) - (EU, US, etc.)
    - `SENSITIVITY_LEVEL` (INT)

4.  **`CARE_PLANS`**
    - `PLAN_ID` (PK, VARCHAR2(50))
    - `PATIENT_ID` (FK $\rightarrow$ `PATIENTS.PATIENT_ID`)
    - `CONTENT` (CLOB)
    - `VERSION` (INT)
    - `LAST_MODIFIED` (TIMESTAMP)

5.  **`PLAN_VERSIONS`** (History table for conflict resolution)
    - `VERSION_ID` (PK, INT)
    - `PLAN_ID` (FK $\rightarrow$ `CARE_PLANS.PLAN_ID`)
    - `SNAPSHOT` (CLOB)
    - `MODIFIED_BY` (FK $\rightarrow$ `USERS.USER_ID`)
    - `TIMESTAMP` (TIMESTAMP)

6.  **`FILES`**
    - `FILE_ID` (PK, VARCHAR2(50))
    - `PATIENT_ID` (FK $\rightarrow$ `PATIENTS.PATIENT_ID`)
    - `FILE_PATH` (VARCHAR2(500))
    - `FILE_TYPE` (VARCHAR2(20))
    - `SCAN_STATUS` (VARCHAR2(20)) - (Clean, Infected, Pending)

7.  **`NOTIFICATIONS`**
    - `NOTIF_ID` (PK, INT)
    - `USER_ID` (FK $\rightarrow$ `USERS.USER_ID`)
    - `CHANNEL` (VARCHAR2(20)) - (SMS, Email, Push)
    - `MESSAGE` (VARCHAR2(1000))
    - `READ_STATUS` (BOOLEAN)

8.  **`AUDIT_LOGS`**
    - `LOG_ID` (PK, BIGINT)
    - `USER_ID` (FK $\rightarrow$ `USERS.USER_ID`)
    - `ACTION` (VARCHAR2(100))
    - `OLD_VALUE` (CLOB)
    - `NEW_VALUE` (CLOB)
    - `PREVIOUS_HASH` (VARCHAR2(64))
    - `CURRENT_HASH` (VARCHAR2(64))
    - `TIMESTAMP` (TIMESTAMP)

9.  **`SESSIONS`**
    - `SESSION_ID` (PK, VARCHAR2(128))
    - `USER_ID` (FK $\rightarrow$ `USERS.USER_ID`)
    - `IP_ADDRESS` (VARCHAR2(45))
    - `EXPIRY` (TIMESTAMP)

10. **`API_KEYS`**
    - `KEY_ID` (PK, VARCHAR2(50))
    - `CLIENT_NAME` (VARCHAR2(100))
    - `SECRET_HASH` (VARCHAR2(255))
    - `RATE_LIMIT` (INT)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Descriptions

**Development (Dev):**
- **Infrastructure:** Local workstations and a shared internal dev server.
- **Database:** Oracle XE (Express Edition).
- **Deployment:** Local Maven build and manual run.
- **Purpose:** Rapid iteration and unit testing.

**Staging (Staging):**
- **Infrastructure:** A mirrored slice of the on-premise data center.
- **Database:** Oracle 19c (Standard Edition).
- **Deployment:** Manual deployment by the DevOps lead via SSH/SCP.
- **Purpose:** User Acceptance Testing (UAT) and integration testing with the partner API.

**Production (Prod):**
- **Infrastructure:** High-availability (HA) cluster in the client's on-premise data center.
- **Database:** Oracle 19c (Enterprise Edition) with RAC (Real Application Clusters).
- **Deployment:** Manual deployment by the single DevOps person.
- **Purpose:** Live healthcare operations.

### 6.2 The Deployment Bottleneck
The "Bus Factor of 1" is a critical risk. All deployment scripts, SSH keys, and environment variables are held by a single DevOps engineer. There is currently no CI/CD pipeline; deployments are performed via manual shell scripts. If this individual is unavailable, no updates can be pushed to Production.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5 and Mockito.
- **Requirement:** Minimum 70% code coverage for all new serverless functions.
- **Focus:** Business logic in the service layer, specifically the conflict resolution algorithms for the collaborative editor.

### 7.2 Integration Testing
- **Focus:** The interaction between the API Gateway, the Spring Boot functions, and the Oracle DB.
- **Approach:** Use Testcontainers to spin up a temporary Oracle instance for database integration tests.
- **Partner API Testing:** Since the partner API is buggy and undocumented, the team will build a "Mock Partner Server" that simulates various failure modes (500 errors, malformed JSON) to ensure Vanguard doesn't crash.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium with Java.
- **Scenarios:** 
    1. Upload a file $\rightarrow$ Wait for scan $\rightarrow$ View file via CDN.
    2. Two users editing the same care plan $\rightarrow$ Verify merge.
    3. Trigger a critical alert $\rightarrow$ Verify SMS delivery.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Integration partner API is undocumented/buggy | High | High | Hire a specialized contractor to reverse-engineer the API and document the endpoints. |
| R2 | Primary vendor EOL (End-of-Life) announcement | Medium | High | De-scope features dependent on this vendor if a replacement isn't found by Milestone 2. |
| R3 | Bus Factor of 1 (DevOps) | High | Critical | Document deployment steps; cross-train Ingrid Kim (Junior Dev) on basic deployments. |
| R4 | "God Class" Technical Debt | High | Medium | Scheduled refactoring sprints to break `SystemCoreManager` into 4 distinct services. |
| R5 | GDPR/CCPA Compliance Breach | Low | Critical | Weekly security audits and physical verification of on-premise residency. |

**Impact Matrix:**
- **Probability:** Low (1-33%), Medium (34-66%), High (67-100%).
- **Impact:** Low (Minor annoyance), Medium (Delay in timeline), High (Feature failure), Critical (Project failure/Legal action).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown

**Phase 1: Core Infrastructure (Now $\rightarrow$ 2026-03-01)**
- Establish on-premise serverless orchestration.
- Refactor the `SystemCoreManager` God Class.
- Implement basic API versioning and sandbox.

**Phase 2: Critical Feature Delivery (2026-03-02 $\rightarrow$ 2026-07-14)**
- Complete the File Upload/Virus Scan pipeline.
- Deploy Private CDN.
- Implement the Notification System.

**Phase 3: Advanced Collaboration (2026-07-15 $\rightarrow$ 2026-09-14)**
- Build the real-time collaborative editor.
- Implement the tamper-evident audit log.
- Perform internal stress tests.

### 9.2 Key Milestones
- **Milestone 1: Post-launch stability confirmed (Target: 2026-07-15)**
    - Criteria: System uptime $>$ 99.9% for 30 days in Staging. No critical bugs in the File Upload system.
- **Milestone 2: External beta with 10 pilot users (Target: 2026-09-15)**
    - Criteria: 10 external clinicians performing real-world data entry; 80% feature adoption rate achieved.
- **Milestone 3: Security audit passed (Target: 2026-11-15)**
    - Criteria: Third-party audit confirms zero "Critical" or "High" vulnerabilities; GDPR compliance certificate issued.

---

## 10. MEETING NOTES (EXCERPTS FROM THE 200-PAGE DOCUMENT)

*Note: These notes are taken from the shared "Vanguard_Sync_Master_Doc" which is unsearchable and contains overlapping timelines.*

### Meeting 1: Architecture Review (2023-11-12)
**Attendees:** Gideon Park, Kamau Jensen, Yael Gupta, Ingrid Kim.
- **Discussion:** Kamau raised concerns about the "serverless" approach on-premise. He argues that the overhead of the API Gateway might introduce latency for the collaborative editor.
- **Decision:** Gideon decided to proceed with the API Gateway regardless. Kamau expressed disagreement but stopped speaking when Gideon interrupted.
- **Action Item:** Kamau to optimize the Oracle indexing for the `AUDIT_LOGS` table.

### Meeting 2: The "God Class" Crisis (2023-12-05)
**Attendees:** Gideon Park, Ingrid Kim.
- **Discussion:** Ingrid attempted to add a new email template to `SystemCoreManager.java` and accidentally broke the authentication logic for all users in the Dev environment.
- **Decision:** The team agreed that the 3,000-line class is a "ticking time bomb." 
- **Conflict:** Gideon mentioned that the PM (Project Manager) is demanding the Notification System be finished by January. Gideon refuses to speak to the PM about the technical debt, stating, "The PM doesn't understand Java, why should I explain it?"
- **Result:** No refactoring scheduled; Ingrid told to "be more careful" with the God Class.

### Meeting 3: Vendor EOL and Budget Blocker (2024-01-20)
**Attendees:** Gideon Park, Kamau Jensen, Yael Gupta.
- **Discussion:** The vendor for the virus scanning engine announced EOL for their current version. If not upgraded, we lose support by mid-2026.
- **Issue:** Upgrade requires a $12,000 license fee. Budget approval is still pending from the finance department.
- **Yael's Input:** Yael noted that pilot users will hate the system if the upload speed is too slow due to the on-prem CDN configuration.
- **Decision:** Gideon will send one more email to finance. If no approval by Friday, we will "hope for the best" and continue using the EOL version.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $280,000 | Distributed team of 15 (Mixed salaries across 5 countries). |
| **Infrastructure** | $60,000 | On-premise server leases, Oracle DB Licenses, SAN storage. |
| **Tools & Licenses** | $30,000 | Virus scanner, SMS Gateway, IDE licenses. |
| **Contractors** | $20,000 | Specialized API consultant to handle the buggy partner API. |
| **Contingency** | $10,000 | Emergency fund for critical tool purchases. |

**Budget Note:** The current $12,000 tool purchase for the virus scanner is currently contesting the $10,000 contingency fund, creating a $2,000 deficit.

---

## 12. APPENDICES

### Appendix A: GDPR Data Residency Mapping
To satisfy the EU residency requirements, the following mapping is implemented:
- **Physical Location:** The data center is located in Frankfurt, Germany.
- **Data Isolation:** Each client is assigned a unique Oracle Tablespace.
- **Encryption:** All data at rest is encrypted using AES-256.
- **Access Control:** Access to the physical servers is restricted to authorized Silverthread AI personnel with biometric verification.

### Appendix B: Conflict Resolution Logic (OT Pseudocode)
For the collaborative editing feature, the following logic will be applied to the `CARE_PLANS` content:
1. **Operation:** `Insert(position, character, version)`
2. **Incoming Operation:** `Insert(position_prime, character_prime, version)`
3. **Transformation:**
   - If `position < position_prime`, the original position remains.
   - If `position >= position_prime`, the original position is incremented by 1.
4. **Persistence:** The transformed operation is then applied to the Oracle DB and broadcasted to all other connected clients via WebSocket.