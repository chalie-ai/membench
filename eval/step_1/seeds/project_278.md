Due to the extreme length requirements of this request (6,000–8,000 words), this document is presented as a comprehensive, professional Project Specification. It is structured as a living technical manual for the development team at Silverthread AI.

***

# PROJECT SPECIFICATION: IRONCLAD
**Version:** 1.0.4  
**Status:** Active/In-Development  
**Date:** October 24, 2023  
**Project Code:** IRON-2024-LOG  
**Owner:** Valentina Oduya (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project "Ironclad" is a strategic initiative by Silverthread AI to penetrate the logistics and shipping sector. This represents a greenfield venture, marking the company's first foray into a domain characterized by high-volume data streams, complex supply chain telemetry, and stringent regulatory requirements. Ironclad is designed as a high-performance data pipeline and analytics platform capable of ingesting massive quantities of shipment data, processing it in real-time, and providing actionable business intelligence to logistics providers.

### 1.2 Business Justification
The logistics industry is currently undergoing a digital transformation. Legacy systems are failing to handle the surge in global shipping volumes and the requirement for real-time visibility. Silverthread AI seeks to capture this market by providing a platform that offers superior throughput and uncompromising security. The primary value proposition is the transition from manual, error-prone data entry and processing to an automated, AI-driven pipeline.

### 1.3 ROI Projection and Financial Impact
With a budget exceeding $5M, Ironclad is a flagship initiative with direct board-level reporting. The projected Return on Investment (ROI) is calculated based on two primary levers:
1. **Market Acquisition:** Capturing a 5% share of the mid-market logistics provider segment within 24 months, projected to generate $12M in Annual Recurring Revenue (ARR).
2. **Operational Efficiency:** By achieving a 50% reduction in manual processing time for end users, clients are expected to reduce their operational overhead by an estimated $200k–$500k per annum per site.

The project is positioned not just as a product, but as a strategic asset that establishes Silverthread AI's capability in the "Industrial AI" space, opening doors to further expansions into warehousing and last-mile delivery analytics.

### 1.4 Strategic Alignment
Ironclad aligns with the company’s 2025 goal of diversifying revenue streams away from general-purpose AI services and toward industry-specific vertical solutions. The decision to deploy on-premise, despite the industry trend toward cloud, is a strategic move to appeal to high-security government and defense shipping contracts where data sovereignty is non-negotiable.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Ironclad is engineered as a **Modular Monolith**. This approach allows the team to maintain a single deployment unit to reduce complexity during the initial greenfield phase while ensuring that domain boundaries (Import, Notification, Reporting, API) are strictly enforced via Java packages. As the system scales and the "10x performance" requirement manifests, the architecture is designed to be incrementally decomposed into microservices.

### 2.2 Technology Stack
- **Backend:** Java 17, Spring Boot 3.2.x
- **Database:** Oracle DB 19c (Enterprise Edition)
- **Infrastructure:** On-premise Data Center (Air-gapped capability)
- **Orchestration:** Kubernetes (K8s) on bare metal
- **CI/CD:** GitLab CI
- **Security:** PCI DSS Level 1 Compliant modules for credit card processing

### 2.3 High-Level System Diagram (ASCII)
```text
[ External Data Sources ] --> [ API Gateway / Load Balancer ]
                                       |
                                       v
                        +-----------------------------------+
                        |      IRONCLAD MODULAR MONOLITH    |
                        |                                   |
                        |  +-----------+    +-------------+  |
                        |  | Data Ingest|-->| Logic Engine||  |
                        |  +-----------+    +-------------+  |
                        |        |                  |       |
                        |        v                  v       |
                        |  +------------+    +-------------+ |
                        |  | Report Gen  |    | Notification|| |
                        |  +------------+    +-------------+ |
                        |        |                  |       |
                        +--------|------------------|-------+
                                 |                  |
                                 v                  v
                        +-------------------+  +-------------------+
                        |   Oracle DB 19c    |  |  K8s Rolling Dep  |
                        | (PCI DSS Encrypted)|  |  (GitLab Pipeline)|
                        +-------------------+  +-------------------+
```

### 2.4 Data Flow and Processing
Data enters via the Customer API or File Import. The "Data Ingest" module performs format auto-detection and normalization. Validated data is committed to the Oracle DB. The "Logic Engine" triggers asynchronous events via an internal event bus, which the "Notification System" and "Report Generation" modules consume to deliver outputs to the end-user.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Data Import/Export with Format Auto-Detection
**Priority:** Low | **Status:** Complete | **Version:** 1.0.0
This feature provides the entry point for all logistics data into the Ironclad ecosystem. Given the fragmentation of the shipping industry, the system must handle CSV, JSON, XML, and EDIFACT formats without requiring the user to specify the file type manually.

**Technical Implementation:**
The system utilizes a "Strategy Pattern" combined with a "Magic Byte" detection mechanism. When a file is uploaded via the `/import` endpoint, the `FormatDetector` class reads the first 1024 bytes of the stream to identify signatures. 
- **CSV:** Detects delimiter frequency (comma, semicolon, tab).
- **JSON/XML:** Detects starting braces `{` or tags `<`.
- **EDIFACT:** Matches standard UN/EDIFACT segment headers.

Once detected, the file is passed to the corresponding `ImportStrategy` implementation. For export, the system allows users to query data and export it in any of the supported formats. The logic ensures that the data integrity is maintained during conversion, employing a strict schema validation layer before writing to the Oracle DB. Because this is marked as "Complete," the focus is now on maintaining the parser as new shipping standards emerge.

### 3.2 Notification System (Email, SMS, In-App, Push)
**Priority:** High | **Status:** Not Started | **Version:** 1.1.0
The Notification System is a critical component for real-time logistics tracking. It must alert users to shipment delays, payment failures, or system alerts across four distinct channels.

**Functional Requirements:**
1. **Email:** Integration with an on-premise SMTP relay for corporate communications and detailed reports.
2. **SMS:** Integration with a secure SMS gateway (via HTTPS POST) for urgent transit alerts.
3. **In-App:** A WebSocket-based notification bell within the dashboard for real-time updates.
4. **Push:** Integration with Firebase Cloud Messaging (FCM) or an on-prem alternative for mobile app alerts.

**Technical Design:**
The system will follow a "Publisher-Subscriber" model. The `NotificationEngine` will receive a `NotificationRequest` object containing the payload and the target user's preferences. The `ChannelRouter` will then determine which channels are active for that specific user. To prevent system bottlenecks, all notifications will be processed asynchronously using a Spring `@Async` task executor and a persistent queue in Oracle DB to ensure "at-least-once" delivery.

### 3.3 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Complete | **Version:** 1.0.0
The platform provides complex analytics reports that must be delivered to stakeholders on a recurring basis.

**Technical Implementation:**
Reporting is handled by a dedicated `ReportingService`. For PDF generation, the system utilizes the iText library to create high-fidelity, brand-compliant documents. CSV reports are generated using OpenCSV for memory-efficient streaming of large datasets.

**Scheduling Logic:**
A Quartz Scheduler is implemented within the monolith to handle cron-like triggers. Users can define schedules (e.g., "Every Monday at 08:00 UTC"). The scheduler triggers a background job that:
1. Executes a pre-defined Oracle SQL query.
2. Maps the result set to a report template.
3. Generates the file in the `tmp/reports` directory.
4. Forwards the file to the Notification System for delivery via email.

### 3.4 Customer-Facing API with Versioning and Sandbox
**Priority:** High | **Status:** In Review | **Version:** 1.0.0-beta
The API is the primary interface for enterprise clients to integrate their internal ERPs with Ironclad.

**Versioning Strategy:**
The API employs URI versioning (e.g., `/api/v1/shipments`). This allows the team to introduce breaking changes in `v2` while maintaining backward compatibility for existing clients.

**Sandbox Environment:**
A mirrored "Sandbox" environment is provided. This environment uses a separate Oracle schema (`IRONCLAD_SBX`) and contains anonymized mock data. All API keys are scoped to either `PRODUCTION` or `SANDBOX` to prevent accidental data corruption in the live environment.

**Current Status:**
The API is currently in the "In Review" phase. The team is finalizing the OpenAPI 3.0 documentation and conducting a security audit on the OAuth2 implementation to ensure it meets the PCI DSS requirements for handling sensitive data.

### 3.5 A/B Testing Framework in Feature Flag System
**Priority:** Medium | **Status:** In Design | **Version:** 1.2.0
To ensure data-driven product evolution, the platform requires a way to toggle features and run experiments on specific user segments.

**Design Specifications:**
The framework will be built on top of a `FeatureFlag` table in the database. Each flag will have a `state` (Enabled, Disabled, Experimental). 

**A/B Testing Logic:**
When a flag is set to `Experimental`, the system will utilize a "Consistent Hashing" algorithm based on the `UserID`. 
- **Group A (Control):** Receives the legacy experience.
- **Group B (Variant):** Receives the new feature.

The `ExperimentTracker` will log all user interactions associated with the flag. These logs will be aggregated into the analytics pipeline to determine if the new feature improves the "Manual Processing Time" metric. This design avoids the need for an external service like LaunchDarkly, keeping all data on-premise.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require an `Authorization: Bearer <Token>` header.

### 4.1 `POST /api/v1/import`
- **Description:** Uploads a shipping data file for ingestion.
- **Request:** `multipart/form-data` (file: binary)
- **Response:** `202 Accepted`
- **Example Response:**
  ```json
  {
    "jobId": "job_99283",
    "status": "processing",
    "detectedFormat": "EDIFACT"
  }
  ```

### 4.2 `GET /api/v1/shipments/{id}`
- **Description:** Retrieves detailed telemetry for a specific shipment.
- **Request:** Path variable `id` (UUID)
- **Response:** `200 OK`
- **Example Response:**
  ```json
  {
    "shipmentId": "uuid-123",
    "status": "in_transit",
    "currentLocation": "Port of Rotterdam",
    "estimatedArrival": "2025-07-12T14:00:00Z"
  }
  ```

### 4.3 `POST /api/v1/notifications/settings`
- **Description:** Updates user preferences for alert channels.
- **Request Body:**
  ```json
  {
    "email": true,
    "sms": false,
    "push": true,
    "inApp": true
  }
  ```
- **Response:** `204 No Content`

### 4.4 `GET /api/v1/reports/schedule`
- **Description:** Lists all active report schedules for the authenticated account.
- **Response:** `200 OK`
- **Example Response:**
  ```json
  [
    { "reportId": "rep_01", "frequency": "weekly", "nextRun": "2025-01-05T08:00:00Z" }
  ]
  ```

### 4.5 `POST /api/v1/reports/generate`
- **Description:** Triggers an immediate ad-hoc report generation.
- **Request Body:** `{ "format": "PDF", "reportType": "MONTHLY_SUMMARY" }`
- **Response:** `201 Created`

### 4.6 `GET /api/v1/sandbox/status`
- **Description:** Checks the health and connectivity of the sandbox environment.
- **Response:** `200 OK`
- **Example Response:** `{ "environment": "sandbox", "status": "healthy", "version": "1.0.0-beta" }`

### 4.7 `PUT /api/v1/shipments/{id}/payment`
- **Description:** Updates payment status for a shipment (PCI DSS scope).
- **Request Body:** `{ "paymentToken": "tok_abc123", "amount": 1500.00, "currency": "USD" }`
- **Response:** `200 OK`

### 4.8 `DELETE /api/v1/notifications/clear`
- **Description:** Marks all in-app notifications as read.
- **Response:** `200 OK`

---

## 5. DATABASE SCHEMA

### 5.1 Schema Design
The database is implemented in Oracle 19c. All tables are owned by the `IRONCLAD_ADMIN` schema.

### 5.2 Tables and Relationships

1.  **`users`**: Stores account details.
    - `user_id` (PK, UUID)
    - `username` (VARCHAR2 50, Unique)
    - `email` (VARCHAR2 100)
    - `password_hash` (VARCHAR2 255)
    - `created_at` (TIMESTAMP)

2.  **`shipments`**: The core entity for logistics tracking.
    - `shipment_id` (PK, UUID)
    - `tracking_number` (VARCHAR2 50, Unique)
    - `origin_id` (FK -> locations.loc_id)
    - `destination_id` (FK -> locations.loc_id)
    - `status` (VARCHAR2 20)
    - `weight` (NUMBER)
    - `created_at` (TIMESTAMP)

3.  **`locations`**: Warehouse and port coordinates.
    - `loc_id` (PK, UUID)
    - `loc_name` (VARCHAR2 100)
    - `country_code` (CHAR 2)
    - `lat` (NUMBER)
    - `lon` (NUMBER)

4.  **`notifications`**: Audit log of all alerts sent.
    - `notification_id` (PK, UUID)
    - `user_id` (FK -> users.user_id)
    - `channel` (VARCHAR2 10) // EMAIL, SMS, etc.
    - `message_body` (CLOB)
    - `sent_at` (TIMESTAMP)
    - `is_read` (NUMBER 1)

5.  **`notification_prefs`**: User settings for alerts.
    - `user_id` (PK, FK -> users.user_id)
    - `email_enabled` (NUMBER 1)
    - `sms_enabled` (NUMBER 1)
    - `push_enabled` (NUMBER 1)

6.  **`reports`**: Metadata for generated reports.
    - `report_id` (PK, UUID)
    - `user_id` (FK -> users.user_id)
    - `file_path` (VARCHAR2 500)
    - `format` (VARCHAR2 10) // PDF, CSV
    - `generated_at` (TIMESTAMP)

7.  **`report_schedules`**: Cron-style schedules.
    - `schedule_id` (PK, UUID)
    - `user_id` (FK -> users.user_id)
    - `cron_expression` (VARCHAR2 50)
    - `report_type` (VARCHAR2 50)
    - `last_run` (TIMESTAMP)

8.  **`payments`**: Encrypted credit card processing data (PCI DSS Level 1).
    - `payment_id` (PK, UUID)
    - `shipment_id` (FK -> shipments.shipment_id)
    - `encrypted_card_data` (BLOB)
    - `transaction_status` (VARCHAR2 20)
    - `amount` (NUMBER 10,2)

9.  **`feature_flags`**: Controls for A/B testing and toggles.
    - `flag_key` (PK, VARCHAR2 50)
    - `flag_state` (VARCHAR2 20) // ENABLED, DISABLED, EXPERIMENTAL
    - `rollout_percentage` (NUMBER 3)

10. **`experiment_logs`**: Tracks user interaction with A/B variants.
    - `log_id` (PK, UUID)
    - `user_id` (FK -> users.user_id)
    - `flag_key` (FK -> feature_flags.flag_key)
    - `variant` (VARCHAR2 10) // A, B
    - `timestamp` (TIMESTAMP)

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ironclad utilizes three distinct environments, all hosted within the Silverthread AI on-premise data center.

#### 6.1.1 Development (DEV)
- **Purpose:** Feature iteration and unit testing.
- **Infrastructure:** Shared Kubernetes namespace, lightweight Oracle XE instance.
- **Deployment:** Automatic trigger on every commit to `develop` branch.

#### 6.1.2 Staging (STG)
- **Purpose:** QA validation, UAT, and performance benchmarking.
- **Infrastructure:** Production-mirror (Bare metal K8s, Oracle 19c Enterprise).
- **Deployment:** Manual trigger from `develop` to `release` branch.
- **Data:** Anonymized production snapshots.

#### 6.1.3 Production (PROD)
- **Purpose:** Live client traffic.
- **Infrastructure:** High-availability cluster with redundant Oracle RAC nodes.
- **Deployment:** Rolling updates via GitLab CI. A "Blue-Green" strategy is employed to ensure zero downtime.
- **Security:** Strictly air-gapped from the public internet except for defined API gateway ports.

### 6.2 CI/CD Pipeline
The pipeline is managed via `.gitlab-ci.yml`:
1. **Build:** Maven compile and test.
2. **Analysis:** SonarQube scan for technical debt and security vulnerabilities.
3. **Containerize:** Docker image creation and push to internal registry.
4. **Deploy:** Helm chart application to K8s cluster.
5. **Verify:** Smoke tests against the `/health` endpoint.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** JUnit 5, Mockito.
- **Requirement:** Minimum 80% code coverage for all business logic in the `service` layer.
- **Execution:** Run on every GitLab pipeline commit.

### 7.2 Integration Testing
- **Focus:** Database interactions and external API calls.
- **Approach:** Use **Testcontainers** to spin up a temporary Oracle DB instance during the build process. This ensures that SQL queries are tested against a real engine rather than an H2 mock.
- **Scope:** Testing the `FormatDetector` with various corrupt and valid file types.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Selenium and RestAssured.
- **Scenarios:**
    - User uploads a CSV $\rightarrow$ System detects format $\rightarrow$ Shipment record created $\rightarrow$ Notification sent.
    - User schedules a report $\rightarrow$ Quartz triggers $\rightarrow$ PDF generated $\rightarrow$ Email sent.
- **Execution:** Weekly regression suite run in the Staging environment.

### 7.4 Performance Testing
- **Tool:** JMeter.
- **Target:** 10x current system capacity.
- **Focus:** Testing the ingestion pipeline's ability to handle 10,000 concurrent shipments per second without increasing DB lock contention.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Performance requirements 10x current capacity with $0 extra budget | High | High | **Parallel-Path:** Prototype an asynchronous Kafka-based ingestion layer simultaneously with the monolith to prove scalability. |
| R-02 | Integration partner's API is undocumented and buggy | Medium | High | **Escalation:** Raise as a critical blocker in the next board meeting to force partner cooperation. |
| R-03 | PCI DSS Audit failure | Low | Critical | **Pre-Audit:** Conduct internal "mock audits" every sprint; use a third-party security consultant for quarterly reviews. |
| R-04 | Dependency on Team X (3 weeks behind) | High | Medium | **Decoupling:** Implement a "Mock Service" layer to simulate Team X's deliverables and continue development. |

**Impact Matrix:**
- **Low:** Negligible impact on timeline.
- **Medium:** Delay of 1-2 weeks.
- **High:** Delay of 1 month or failure of a milestone.
- **Critical:** Project cancellation or legal liability.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Project Phases
- **Phase 1: Foundation (Oct 2023 - Feb 2024):** Core monolith setup, Oracle schema design, and basic import/export.
- **Phase 2: Feature Expansion (Mar 2024 - May 2025):** Development of Notification system, Reporting, and A/B framework.
- **Phase 3: Hardening (Jun 2025 - Aug 2025):** External beta, bug fixing, and security audits.
- **Phase 4: Scale & Launch (Sep 2025 - Oct 2025):** Performance benchmarking and final sign-off.

### 9.2 Critical Milestones
- **Milestone 1: External beta with 10 pilot users**
    - **Target Date:** 2025-06-15
    - **Dependency:** Customer API must be stable and Sandbox environment live.
- **Milestone 2: Stakeholder demo and sign-off**
    - **Target Date:** 2025-08-15
    - **Dependency:** Reporting and Notification systems must be fully operational.
- **Milestone 3: Performance benchmarks met**
    - **Target Date:** 2025-10-15
    - **Dependency:** Load tests showing 10x capacity increase.

---

## 10. MEETING NOTES

### Meeting 1: Architecture Sync (2023-11-02)
**Attendees:** Valentina, Wyatt, Dante, Esme
- Monolith vs Microservices.
- Decision: Start monolith $\rightarrow$ split later.
- Oracle DB: Version 19c decided.
- PCI DSS: Need to isolate payment tables.
- Wyatt concerned about memory leaks in PDF gen.

### Meeting 2: API Review (2024-02-15)
**Attendees:** Valentina, Wyatt, Esme
- Sandbox environment needs its own DB.
- Versioning: `/v1/` preferred over headers.
- Rate limiting: Add 100 req/min for sandbox users.
- Esme to finish OpenAPI spec by Friday.

### Meeting 3: Performance Crisis (2024-05-20)
**Attendees:** Valentina, Wyatt, Dante
- Benchmarks failing. 10x target not hit.
- No budget for new hardware.
- Decision: Prototype "Parallel-Path" approach.
- Dante to write stress tests for the import pipeline.
- Integration partner API is still buggy.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $5,250,000 (Flagship Initiative)

| Category | Allocation | Amount | Notes |
| :--- | :--- | :--- | :--- |
| **Personnel** | 60% | $3,150,000 | 6 FTEs (including Valentina and Wyatt) + QA and Contractor (Esme). |
| **Infrastructure**| 20% | $1,050,000 | On-prem servers, Oracle Enterprise Licenses, K8s hardware. |
| **Tools & Software**| 10% | $525,000 | GitLab Premium, SonarQube, iText License, SMS Gateway fees. |
| **Contingency** | 10% | $525,000 | Reserved for emergency hardware or external security consultants. |

---

## 12. APPENDICES

### Appendix A: PCI DSS Level 1 Compliance Measures
To maintain PCI DSS Level 1 compliance while processing credit card data directly, Ironclad implements the following:
1. **Encryption at Rest:** All data in the `payments` table is encrypted using AES-256. The keys are stored in a Hardware Security Module (HSM).
2. **Network Segmentation:** The payment processing module runs in a restricted K8s namespace with strict NetworkPolicies, allowing communication only with the HSM and the Oracle DB.
3. **Audit Trails:** Every access to the `payments` table is logged to a read-only audit log that is mirrored to a secondary secure server.
4. **No Local Storage:** Credit card numbers are never logged in plain text in the application logs.

### Appendix B: Data Import Format Signatures
The `FormatDetector` uses the following byte-patterns for auto-detection:
- **JSON:** First non-whitespace character is `{` or `[`.
- **XML:** First non-whitespace character is `<`.
- **CSV:** Analyzes the first three lines. If the count of `,`, `;`, or `\t` is consistent across all three lines and exceeds 2, it is classified as CSV.
- **EDIFACT:** Search for `UNA` (Universal Native Alphabet) or `UNB` (Interchange Header) segments within the first 100 characters.