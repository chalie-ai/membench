# PROJECT SPECIFICATION DOCUMENT: PROJECT INGOT
**Version:** 1.0.4  
**Status:** Active/Draft  
**Company:** Crosswind Labs  
**Date:** October 26, 2023  
**Classification:** Confidential – Internal Use Only  
**Compliance Standard:** ISO 27001

---

## 1. EXECUTIVE SUMMARY

**Project Overview**  
Project "Ingot" is a strategic digital transformation initiative spearheaded by Crosswind Labs to revolutionize the operational efficiency of its real estate portfolio management. Currently, the organization relies on four separate, redundant internal tools for property valuation, tenant tracking, lease management, and compliance auditing. These legacy systems—developed haphazardly over a decade—create significant data silos, duplicate entry requirements, and high maintenance costs. Ingot aims to consolidate these four tools into a single, unified mobile application, providing a "single source of truth" for field agents, property managers, and executive leadership.

**Business Justification**  
The current fragmented ecosystem costs Crosswind Labs approximately $450,000 annually in licensing fees, server maintenance, and labor hours spent on manual data reconciliation. By consolidating these tools, Ingot will eliminate these redundant costs and reduce the "time-to-insight" for real estate analysts from three days to near real-time. Furthermore, the current tools lack mobile optimization, forcing field agents to use tablets with clunky web wrappers. Ingot will be a native-feeling mobile experience, increasing field data entry accuracy by an estimated 30%.

**ROI Projection**  
With a total budget of $1.5M, the project is designed for high stability and scalability. The projected Return on Investment (ROI) is calculated based on the following three-year window:
1. **Direct Cost Savings:** Elimination of 4 legacy tool licenses ($450k/year $\times$ 3 years = $1.35M).
2. **Operational Efficiency:** Reduction of 15% in manual administrative labor across the portfolio management team (Estimated value: $200k/year).
3. **Risk Mitigation:** Reducing the likelihood of regulatory fines via the automated compliance module (Estimated risk avoidance: $100k/year).

The break-even point is projected for Month 14 post-launch. The primary financial objective is to transition the internal cost center into a value-driver that can potentially be white-labeled for external real estate firms.

**Success Metrics**  
- **MAU Growth:** Achieve 10,000 monthly active users within 6 months of the general release.
- **User Satisfaction:** Maintain a customer Net Promoter Score (NPS) above 40 within the first quarter of production deployment.
- **System Performance:** API response times under 200ms for 95% of requests.

---

## 2. TECHNICAL ARCHITECTURE

Project Ingot utilizes a modern, decoupled architecture designed for high availability and strict security compliance. The system follows a microservices pattern to ensure that failure in one domain (e.g., report generation) does not crash the core property search functionality.

### 2.1 Technology Stack
- **Backend:** Python 3.11 / Django 4.2 (REST Framework)
- **Database:** PostgreSQL 15 (Primary Relational Store)
- **Caching/Queueing:** Redis 7.0 (Session management and caching)
- **Event Streaming:** Apache Kafka (Asynchronous communication between services)
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless compute.
- **Security:** ISO 27001 certified environment with AWS KMS for encryption at rest and TLS 1.3 for data in transit.

### 2.2 Architectural Diagram (ASCII)

```text
[ Mobile Client (iOS/Android) ]
            |
            v
[ AWS Application Load Balancer ]
            |
            +-----------------------+-----------------------+
            |                       |                       |
    [ API Gateway Service ]  [ Auth/IAM Service ]  [ Edge Cache (Redis) ]
            |                       |                       |
            +-----------+-----------+-----------+-----------+
                        | (REST / gRPC)
                        v
            [ Microservices Layer (AWS ECS) ]
            +-----------------------------------------------+
            |  [ Search Svc ]  [ Collab Svc ]  [ Report Svc ] |
            |       |                |               |       |
            +-------|----------------|---------------|-------+
                    |                |               |
                    v                v               v
            [ Event Bus: Apache Kafka (Message Broker) ]
                    |                |               |
            +-------v----------------v---------------v-------+
            | [ Data Persistence Layer ]                     |
            |   - PostgreSQL (Main DB)                        |
            |   - ElasticSearch (Indexing)                   |
            |   - S3 (PDF/CSV Storage)                        |
            +------------------------------------------------+
```

### 2.3 Communication Pattern
The architecture employs an **Event-Driven Architecture (EDA)**. When a property record is updated in the Core Service, a `PROPERTY_UPDATED` event is published to a Kafka topic. The Search Service and the Report Service subscribe to this topic to update their respective indices and cached reports without requiring a synchronous call, ensuring the UI remains responsive.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: High | Status: Complete)
**Description:**
This feature provides the core navigation for the Ingot application, allowing users to find properties across a global portfolio using complex criteria. Unlike simple keyword searches, the faceted filtering allows users to narrow results by multiple dimensions (e.g., "Location: New York", "Status: Under Lease", "Valuation: >$1M").

**Functional Requirements:**
- **Full-Text Indexing:** Implementation of ElasticSearch to allow for "fuzzy" matching on property addresses and tenant names.
- **Faceted Navigation:** Dynamic filters that update their counts based on the current search result set.
- **Saved Searches:** Ability for users to save a specific combination of filters and receive push notifications when a new property matches those criteria.
- **Geospatial Search:** Integration with MapBox to allow "search by radius" functionality.

**Technical Implementation:**
The search service indexes PostgreSQL data into an ElasticSearch cluster. When a user submits a query, the API Gateway routes the request to the Search Service, which constructs a Boolean query for ElasticSearch. The response is then hydrated with metadata from the PostgreSQL database before being returned to the mobile client.

**Acceptance Criteria:**
- Search results must return in under 300ms for a dataset of 50,000 properties.
- Facets must update in real-time as filters are toggled.
- Full-text search must handle typos (e.g., "Manhatten" should find "Manhattan").

---

### 3.2 Localization and Internationalization (Priority: High | Status: Blocked)
**Description:**
To support Crosswind Labs' global expansion, Ingot must support 12 different languages and regional formats (dates, currencies, number separators). This is not merely a translation of strings but a comprehensive "L10n" strategy.

**Functional Requirements:**
- **Dynamic Language Switching:** Users can change their preferred language in settings without restarting the app.
- **RTL Support:** The UI must support Right-to-Left (RTL) mirroring for Arabic and Hebrew.
- **Currency Conversion:** Integration with a real-time FX rate API to display property valuations in the user's local currency.
- **Regional Compliance:** Different data display formats based on the locale (e.g., DD/MM/YYYY vs MM/DD/YYYY).

**Technical Implementation:**
The system uses `i18next` on the frontend and Django’s `ugettext` on the backend. Translation keys are stored in JSON files managed by a translation management system (TMS). A middleware layer intercepts requests to determine the `Accept-Language` header and serves the corresponding translation bundle.

**Blocker Details:**
Currently blocked by the Third-Party API rate limits. The translation verification service used to validate legal terminology across 12 languages is throttling requests, preventing the final verification of the "Legal/Compliance" terminology bundles.

---

### 3.3 Real-Time Collaborative Editing (Priority: Medium | Status: In Review)
**Description:**
Property managers and analysts often need to update a property's valuation or status simultaneously. This feature prevents "last-write-wins" data loss by implementing real-time synchronization.

**Functional Requirements:**
- **Presence Indicators:** Users should see who else is currently viewing or editing a specific property record (avatars in the header).
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to merge concurrent edits.
- **Locking Mechanism:** Ability to "Lock" a specific field (e.g., "Final Valuation") to prevent other users from editing during a critical review.
- **Audit Trail:** A detailed log of who changed what value and when.

**Technical Implementation:**
The feature utilizes WebSockets (via Django Channels) to maintain a persistent connection between the client and the server. When a change is made, the delta is sent as a JSON patch. The server validates the patch and broadcasts it to all other connected clients observing that object.

**Acceptance Criteria:**
- Latency for synchronization between two users on the same network must be $<100\text{ms}$.
- No data loss should occur during simultaneous edits to different fields of the same record.

---

### 3.4 A/B Testing Framework (Priority: Medium | Status: In Design)
**Description:**
To optimize user engagement and conversion within the app, the team requires a framework to test different UI layouts, onboarding flows, and feature sets without deploying new code for every experiment.

**Functional Requirements:**
- **Feature Flagging:** Ability to toggle features on/off for specific user segments (e.g., "Beta Users," "Internal Staff").
- **Traffic Splitting:** Randomly assign users to "Control" or "Treatment" groups (e.g., 50/50 or 90/10 split).
- **Metric Tracking:** Integration with analytics to track which variant performs better against a specific KPI (e.g., "Time to complete property entry").
- **Dynamic Configuration:** Changes to flags must propagate to the app in real-time via a configuration endpoint.

**Technical Implementation:**
The framework will be integrated into the existing feature flag system. A dedicated `Experiment` table in PostgreSQL will map users to specific variants. A middleware will check the user's assigned variant and inject the corresponding configuration into the API response.

**Acceptance Criteria:**
- The framework must support at least 5 concurrent experiments.
- Users must remain in their assigned group across sessions (sticky bucketing).

---

### 3.5 PDF/CSV Report Generation (Priority: Low | Status: In Review)
**Description:**
Executives require scheduled, high-fidelity reports of portfolio performance. This feature automates the extraction of data and its delivery in professional formats.

**Functional Requirements:**
- **Custom Templates:** Ability to choose from different report layouts (Executive Summary, Detailed Audit, Tax Compliance).
- **Scheduled Delivery:** Users can set reports to be emailed weekly, monthly, or quarterly.
- **Mass Export:** Capability to export up to 10,000 records to CSV without timing out.
- **Secure Delivery:** PDFs must be encrypted or delivered via a secure, time-limited S3 signed URL.

**Technical Implementation:**
Given the heavy resource load, report generation is handled asynchronously. A Celery worker picks up the request from a Redis queue, generates the PDF using `ReportLab` or `WeasyPrint`, uploads the file to AWS S3, and then triggers an SNS notification to email the user the link.

**Acceptance Criteria:**
- PDF generation for a 50-page report must complete in under 30 seconds.
- Scheduled reports must trigger within 15 minutes of the scheduled time.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. Authentication is handled via JWT in the `Authorization: Bearer <token>` header.

### 4.1 Property Search
- **Endpoint:** `GET /properties/search`
- **Description:** Performs a faceted search for properties.
- **Query Parameters:** `q` (string), `min_val` (float), `max_val` (float), `status` (enum), `locale` (string).
- **Example Request:** `GET /api/v1/properties/search?q=Manhattan&min_val=1000000&status=active`
- **Example Response:**
  ```json
  {
    "results": [
      {"id": "prop_123", "address": "123 Wall St", "valuation": 1500000, "status": "active"}
    ],
    "facets": {
      "status": {"active": 120, "pending": 45, "closed": 300},
      "region": {"NY": 50, "CA": 30}
    },
    "total": 465
  }
  ```

### 4.2 Property Detail Retrieval
- **Endpoint:** `GET /properties/{property_id}`
- **Description:** Fetches full details for a single property.
- **Example Response:**
  ```json
  {
    "id": "prop_123",
    "details": { "sqft": 5000, "year_built": 1920, "last_inspection": "2023-01-12" },
    "valuation_history": [{"date": "2022-01-01", "value": 1400000}]
  }
  ```

### 4.3 Collaborative Edit Patch
- **Endpoint:** `PATCH /properties/{property_id}/sync`
- **Description:** Sends a delta update for real-time collaboration.
- **Request Body:**
  ```json
  {
    "field": "valuation",
    "old_value": 1400000,
    "new_value": 1450000,
    "timestamp": "2023-10-26T10:00:00Z"
  }
  ```
- **Example Response:** `200 OK` with updated object state.

### 4.4 Report Trigger
- **Endpoint:** `POST /reports/generate`
- **Description:** Manually triggers a report generation task.
- **Request Body:**
  ```json
  {
    "template_id": "exec_summary_01",
    "filters": {"region": "North_America"},
    "format": "pdf"
  }
  ```
- **Example Response:** `202 Accepted` with `{"job_id": "job_abc_123", "status": "queued"}`.

### 4.5 Report Status Check
- **Endpoint:** `GET /reports/status/{job_id}`
- **Description:** Polls the status of a background report job.
- **Example Response:** `{"status": "completed", "download_url": "https://s3.aws.../report.pdf"}`.

### 4.6 Language Preference Update
- **Endpoint:** `PUT /user/settings/locale`
- **Description:** Updates the user's language and regional settings.
- **Request Body:** `{"locale": "fr-FR", "currency": "EUR"}`.
- **Example Response:** `200 OK`.

### 4.7 Feature Flag Query
- **Endpoint:** `GET /config/flags`
- **Description:** Retrieves the list of active feature flags for the current user.
- **Example Response:** `{"flags": {"new_search_ui": true, "collab_editing": false}}`.

### 4.8 Audit Log Retrieval
- **Endpoint:** `GET /properties/{property_id}/audit`
- **Description:** Returns the history of changes for a specific property.
- **Example Response:**
  ```json
  [
    {"user": "Zev N.", "action": "update_val", "timestamp": "2023-10-25T14:00:00Z"}
  ]
  ```

---

## 5. DATABASE SCHEMA

The database is a PostgreSQL 15 instance. Relationships are enforced via foreign keys, and indexing is applied to all high-frequency search columns.

### 5.1 Table Definitions

| Table Name | Primary Key | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | `email`, `password_hash`, `role_id`, `locale` | M:1 `roles` | User account data and preferences. |
| `roles` | `role_id` | `role_name`, `permissions_mask` | 1:M `users` | RBAC role definitions. |
| `properties` | `prop_id` | `address`, `city`, `country`, `valuation`, `status` | M:1 `portfolios` | Core real estate asset data. |
| `portfolios` | `port_id` | `name`, `manager_id`, `region` | 1:M `properties` | Logical grouping of assets. |
| `valuations` | `val_id` | `prop_id`, `value`, `date`, `appraiser_id` | M:1 `properties` | Historical valuation tracking. |
| `leases` | `lease_id` | `prop_id`, `tenant_id`, `start_date`, `end_date` | M:1 `properties` | Lease agreement details. |
| `tenants` | `tenant_id` | `name`, `contact_email`, `credit_score` | 1:M `leases` | Tenant profile information. |
| `audit_logs` | `log_id` | `prop_id`, `user_id`, `change_delta`, `timestamp` | M:1 `properties` | Record of every change. |
| `reports` | `report_id` | `user_id`, `template_id`, `s3_path`, `created_at` | M:1 `users` | Meta-data for generated reports. |
| `feature_flags`| `flag_id` | `flag_key`, `is_enabled`, `rollout_percentage`| N/A | Global feature toggle settings. |

### 5.2 Entity Relationship Summary
- A **User** belongs to a **Role** and manages multiple **Portfolios**.
- A **Portfolio** contains multiple **Properties**.
- A **Property** has many **Valuations** over time and can have multiple **Leases**.
- A **Lease** links a **Property** to a **Tenant**.
- All changes to **Properties** are logged in **Audit Logs**.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
To ensure the ISO 27001 compliance, Ingot uses three strictly isolated environments.

**1. Development (Dev)**
- **Purpose:** Rapid iteration and feature development.
- **Infrastructure:** Shared ECS cluster, small PostgreSQL instance.
- **Data:** Anonymized subsets of production data.
- **Deployment:** Automated on every merge to `develop` branch.

**2. Staging (Staging/QA)**
- **Purpose:** Pre-production validation, UAT, and QA testing.
- **Infrastructure:** Mirror of production architecture (Multi-AZ).
- **Data:** Full snapshot of production data (masked for PII).
- **Deployment:** Triggered by release candidate tags.

**3. Production (Prod)**
- **Purpose:** End-user live environment.
- **Infrastructure:** High-availability AWS ECS Fargate, RDS Multi-AZ, Redis Cluster.
- **Security:** Strict VPC isolation, WAF (Web Application Firewall) enabled, CloudTrail logging.
- **Deployment:** Quarterly releases aligned with regulatory review cycles.

### 6.2 CI/CD Pipeline
- **Source Control:** GitHub Enterprise.
- **Pipeline:** GitHub Actions $\rightarrow$ AWS CodeBuild $\rightarrow$ AWS ECR $\rightarrow$ AWS ECS.
- **Verification:** Every PR requires two approvals (one from Zev Nakamura) and a successful run of the full test suite.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, utility classes, and Django models.
- **Tooling:** `pytest`, `unittest.mock`.
- **Target:** 85% code coverage.
- **Execution:** Runs on every commit in the CI pipeline.

### 7.2 Integration Testing
- **Scope:** API endpoints, database transactions, and Kafka message delivery.
- **Tooling:** `Postman/Newman`, `Pytest-django`.
- **Focus:** Validating that the Search Service correctly interacts with the ElasticSearch index and that the Report Service successfully writes to S3.
- **Execution:** Runs on merge to `develop`.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys (e.g., "Login $\rightarrow$ Search Property $\rightarrow$ Edit Valuation $\rightarrow$ Generate Report").
- **Tooling:** `Appium` (for mobile native testing), `Selenium` (for admin web portal).
- **QA Role:** Dedicated QA engineer manages the E2E suite, manually validating edge cases not covered by automation.
- **Execution:** Weekly regression runs on Staging.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Integration partner's API is undocumented and buggy. | High | High | Hire a specialized contractor to reverse-engineer the API and build a wrapper layer to reduce bus factor. |
| R-02 | Budget may be cut by 30% in the next fiscal quarter. | Medium | High | Maintain a "Tier 2" feature list. De-scope PDF reporting and A/B testing if budget is reduced. |
| R-03 | Third-party API rate limits blocking testing. | High | Medium | Implement a mock-server for the integration partner to allow QA to proceed without hitting live limits. |
| R-04 | Hardcoded configuration values in 40+ files. | High | Medium | Sprint 0 objective: migrate all hardcoded values to AWS Secrets Manager and Environment Variables. |
| R-05 | ISO 27001 Certification failure. | Low | Critical | Conduct monthly internal security audits with Dmitri Oduya. |

**Probability/Impact Matrix:**
- **High/High:** Critical (R-01) $\rightarrow$ Immediate Action.
- **Medium/High:** Serious (R-02) $\rightarrow$ Contingency Planning.
- **High/Medium:** Moderate (R-03, R-04) $\rightarrow$ Iterative Fix.

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Breakdown
- **Phase 1: Foundation (Now – April 2025)**
  - Focus: Schema finalization, API Gateway setup, and Search Service completion.
  - Dependency: Infrastructure setup by Elara Moreau.
- **Phase 2: Integration & Collaboration (April 2025 – June 2025)**
  - Focus: Real-time sync, localization (once unblocked), and internal beta.
  - Dependency: Resolution of API rate limits.
- **Phase 3: Validation & Launch (June 2025 – August 2025)**
  - Focus: External beta, performance tuning, and final regulatory review.
  - Dependency: Successful Beta with 10 pilot users.

### 9.2 Key Milestones
| Milestone | Target Date | Deliverable | Success Criteria |
| :--- | :--- | :--- | :--- |
| M1: Architecture Review | 2025-04-15 | Signed-off Design Doc | Approved by Tech Lead and Security Engineer. |
| M2: External Beta | 2025-06-15 | Beta App Build | 10 pilot users completing core workflows. |
| M3: First Paid Customer| 2025-08-15 | Production Deployment | Onboarding of first paying client. |

---

## 10. MEETING NOTES

### Meeting 1: Architecture Kickoff (2023-11-02)
- Zev: Kafka for events.
- Elara: ECS Fargate better than EC2.
- Dmitri: Needs ISO 27001. No public S3 buckets.
- Anouk: Asking about Django vs FastAPI.
- Decision: Stick with Django for the admin panel and ORM.

### Meeting 2: API Crisis (2023-12-15)
- Dmitri: Partner API returning 429s.
- Zev: Blocked localization tests.
- Anouk: Found 12 files with hardcoded keys.
- Action: Dmitri to contact partner; Zev to assign Anouk to config cleanup.

### Meeting 3: Budgetary Review (2024-01-20)
- Management: Possible 30% cut next Q.
- Zev: Priority 1 (Search) and 2 (L10n) are non-negotiable.
- Elara: DevOps costs are stable.
- Decision: If cut happens, move Report Generation to "Phase 4" (Post-launch).

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $1,500,000

| Category | Allocation | Amount | Details |
| :--- | :--- | :--- | :--- |
| **Personnel** | 65% | $975,000 | 6 Full-time employees (inc. Intern) for 18 months. |
| **Infrastructure** | 15% | $225,000 | AWS ECS, RDS, Kafka Managed Service, Redis. |
| **Tools & Licenses**| 5% | $75,000 | MapBox, ElasticSearch license, TMS tool. |
| **Contractors** | 5% | $75,000 | API reverse-engineering specialist. |
| **Contingency** | 10% | $150,000 | Reserved for budget volatility/emergencies. |

---

## 12. APPENDICES

### Appendix A: ISO 27001 Compliance Checklist
To maintain certification, the following must be verified monthly:
1. **Access Control:** Quarterly review of IAM roles.
2. **Encryption:** All S3 buckets must use AES-256 encryption.
3. **Logging:** CloudWatch logs must be retained for 365 days.
4. **Vulnerability Scanning:** Weekly Snyk scans on all container images.

### Appendix B: Data Migration Strategy (Legacy $\rightarrow$ Ingot)
Since Ingot replaces four tools, data migration is a critical risk.
- **ETL Process:** Extract $\rightarrow$ Transform $\rightarrow$ Load.
- **Step 1:** Dump legacy SQL data to CSV.
- **Step 2:** Python scripts to sanitize data and map old IDs to new `prop_id` UUIDs.
- **Step 3:** Batch upload to Staging for validation.
- **Step 4:** Production cutover via a "read-only" window of 4 hours on the launch date.