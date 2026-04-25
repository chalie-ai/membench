Due to the extreme length requirements (6,000-8,000 words) and the depth of technical specification requested, this document is structured as a Comprehensive Project Specification (CPS). It serves as the primary "Source of Truth" for the development team at Verdant Labs.

***

# PROJECT SPECIFICATION: PROJECT EMBER
**Document Version:** 1.0.4  
**Last Updated:** October 24, 2023  
**Status:** Draft/Active  
**Classification:** Internal / Restricted (FedRAMP Compliance Pending)  
**Project Lead:** Farah Stein (VP of Product)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ember is a greenfield initiative by Verdant Labs to develop a state-of-the-art cybersecurity monitoring dashboard specifically tailored for the government services sector. Unlike Verdant Labs' existing portfolio, which focuses on commercial enterprise tooling, Ember represents a strategic pivot into the public sector—a market characterized by high barriers to entry, stringent regulatory requirements, and long-term contract stability.

The goal of Ember is to provide government agencies with a centralized, real-time visibility layer over their security posture, aggregating logs and alerts into an actionable, high-fidelity dashboard. By transitioning from disparate log files to a unified visual interface, agencies can reduce their Mean Time to Detect (MTTD) and Mean Time to Respond (MTTR).

### 1.2 Business Justification
The government services market is currently undergoing a massive digital transformation, shifting from legacy on-premise systems to cloud-native architectures. However, there is a significant gap in tooling that combines modern UX with the rigorous security standards required for government authorization (FedRAMP). 

Verdant Labs is leveraging its expertise in high-scale data engineering to fill this gap. By entering this market, the company diversifies its revenue streams, reducing reliance on the volatile commercial sector. The "greenfield" nature of the project allows the team to build a clean, monolith-first architecture without the burden of legacy technical debt, ensuring that the product is purpose-built for the stringent security requirements of federal entities.

### 1.3 ROI Projection
The financial model for Ember is based on a milestone-funded tranche system. Initial funding is allocated for the development of the Minimum Viable Product (MVP), with subsequent funding released upon the successful completion of production launch and pilot user adoption.

**Projected Financial Impact:**
- **Year 1 (Development/Launch):** Estimated spend of $2.4M across personnel and AWS infrastructure.
- **Year 2 (Scaling):** Target acquisition of 5 government agency contracts with an Average Contract Value (ACV) of $450,000.
- **Year 3 (Expansion):** Projected ARR of $6.5M as the product expands from the 10 pilot users to broader agency deployment.
- **ROI Calculation:** We anticipate a break-even point by Month 18 post-launch, with a projected 300% ROI by the end of Year 3, driven by the low churn rates typical of government contracts.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Ember is designed as a "Clean Monolith." While the industry trend is toward microservices, the government sector's requirement for strict auditability and reduced attack surfaces makes a well-structured monolith more desirable. By utilizing clear module boundaries within the Django application, the team can maintain a high velocity of development while ensuring that the system remains easy to deploy and monitor.

### 2.2 The Tech Stack
- **Language/Framework:** Python 3.11 / Django 4.2 (LTS). Django was chosen for its "batteries-included" approach to security and its robust ORM.
- **Database:** PostgreSQL 15. This serves as the primary relational store for configuration, user data, and audit trails.
- **Caching/Queueing:** Redis 7.0. Used for session management, caching frequently accessed dashboard metrics, and as the broker for Celery asynchronous tasks.
- **Infrastructure:** AWS ECS (Elastic Container Service) using Fargate for serverless container execution. This removes the overhead of managing EC2 instances.
- **Deployment:** Continuous Deployment (CD) via GitHub Actions. Every merged PR to the `main` branch triggers a deployment to production after passing the automated test suite.

### 2.3 Architecture Diagram (ASCII Representation)
```text
[ External Traffic ]  --> [ AWS Application Load Balancer ]
                                      |
                                      v
                          [ AWS ECS Cluster (Fargate) ]
                          |---------------------------|
                          |  Django App (Monolith)     |
                          |  /                             |
                          |  --> [ Module: Auth/IAM ]      |
                          |  --> [ Module: Dashboard ]     |
                          |  --> [ Module: Audit Log ]     |
                          |  --> [ Module: Reporting ]     |
                          |---------------------------|
                                      |
            __________________________|__________________________
           |                          |                         |
           v                          v                         v
    [ PostgreSQL DB ]           [ Redis Cache/Queue ]     [ AWS S3 (Reports) ]
    (State & Audit)            (Session/Celery)         (CSV/PDF Storage)
```

### 2.4 Security & Compliance
The paramount technical constraint is **FedRAMP Authorization**. This requires:
- **Data Encryption:** AES-256 for data at rest and TLS 1.3 for data in transit.
- **Identity Management:** Integration with government-standard SAML/OIDC providers.
- **Boundary Protection:** Strict VPC configurations and security group rules to ensure the application is isolated.
- **Monitoring:** Comprehensive logging of all administrative actions (covered in Feature 5).

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Audit Trail Logging with Tamper-Evident Storage
**Priority:** Critical (Launch Blocker)  
**Status:** In Progress  

**Description:**
Government clients require an immutable record of every action taken within the system. This is not merely a "log file," but a legal record of who changed what and when. The Audit Trail must capture all "Write" operations and sensitive "Read" operations (e.g., viewing a high-security alert).

**Functional Requirements:**
- Every API request that modifies state must be logged with the User ID, Timestamp, Source IP, Request Payload, and Result.
- Logs must be stored in a "tamper-evident" manner. This is achieved by implementing a cryptographic chaining mechanism where each log entry contains a hash of the previous entry.
- Any attempt to delete or modify a log entry must trigger a critical alert to the System Administrator.
- The system must support "Legal Hold" functionality, where specific ranges of audit logs are locked and cannot be purged even by the system owner.

**Technical Implementation:**
A Django middleware component will intercept every request. For authorized requests, the middleware will extract the user's identity and the request parameters. The data will be passed to a dedicated `AuditLog` model. To ensure tamper-evidence, the application will generate a SHA-256 hash of the current log record concatenated with the hash of the preceding record. This chain will be stored in a dedicated PostgreSQL schema with restricted "INSERT only" permissions for the application user.

---

### 3.2 Localization and Internationalization (L10n/I18n)
**Priority:** Critical (Launch Blocker)  
**Status:** In Design  

**Description:**
Ember will be deployed across various government agencies, some of which operate in multi-lingual environments or support international partners. The system must be fully localized for 12 languages (including English, Spanish, French, German, Mandarin, Japanese, Korean, Arabic, Russian, Portuguese, Italian, and Hindi).

**Functional Requirements:**
- The UI must support Dynamic Language Switching without requiring a page reload.
- Support for Right-to-Left (RTL) layouts for languages like Arabic.
- All date, time, and currency formats must be localized based on the user's profile settings.
- The system must support "pseudo-localization" during the testing phase to identify UI truncation issues caused by longer strings in languages like German.

**Technical Implementation:**
We will utilize Django’s built-in `i18n` framework and `gettext`. All strings in the frontend (React) and backend (Django) will be wrapped in translation functions. Translation files (.po and .mo) will be managed via an external translation management system (TMS) to allow non-technical linguists to edit copy. The User profile model will be extended to include a `preferred_language` field, which will be used to set the locale in the middleware.

---

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Low (Nice to Have)  
**Status:** Complete  

**Description:**
To cater to different personas (e.g., SOC Analysts vs. CISO), the dashboard must be flexible. Users should be able to arrange their view of security metrics according to their specific needs.

**Functional Requirements:**
- Users can add, remove, and resize widgets from a library of available security components (e.g., "Top 10 Attacking IPs," "System Health," "Open Critical Alerts").
- A "Drag-and-Drop" interface for rearranging widgets on a grid.
- Ability to save "Dashboard Layouts" as templates and share them with other team members.
- Widgets must be responsive and maintain their layout across different screen resolutions.

**Technical Implementation:**
The frontend utilizes `react-grid-layout` to handle the drag-and-drop functionality. The layout state (x, y, w, h coordinates for each widget) is serialized as a JSON blob and stored in the `UserDashboardConfiguration` table in PostgreSQL. When the dashboard loads, the backend provides the configuration, and the frontend dynamically renders the corresponding React components.

---

### 3.4 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Low (Nice to Have)  
**Status:** Blocked  

**Description:**
Government agencies require periodic reporting for compliance audits. Ember must be able to generate snapshot reports of security posture in PDF and CSV formats and deliver them via email or SFTP.

**Functional Requirements:**
- Users can define a "Report Template" selecting which widgets and data points are included.
- Scheduling engine: Reports can be sent daily, weekly, or monthly.
- Ability to trigger an "On-Demand" report generation.
- Reports must be encrypted at rest using the agency's public key.

**Technical Implementation:**
The system will use `WeasyPrint` for PDF generation and the standard `csv` Python library. A Celery Beat scheduler will trigger the generation tasks. Since the feature is currently **blocked** due to a design disagreement regarding the "Report Template" UI, the underlying data extraction logic is written, but the trigger mechanism and PDF layout are pending.

---

### 3.5 API Rate Limiting and Usage Analytics
**Priority:** Low (Nice to Have)  
**Status:** Blocked  

**Description:**
To prevent Denial of Service (DoS) attacks and ensure fair usage of system resources, the Ember API must implement strict rate limiting and provide analytics on how the API is being consumed.

**Functional Requirements:**
- Implement "Tiered Rate Limiting" (e.g., Admin: 1000 req/min, User: 100 req/min).
- Return a `429 Too Many Requests` response when limits are exceeded, including a `Retry-After` header.
- A dashboard view for administrators to see the most active API keys and the most frequently called endpoints.
- Ability to manually override rate limits for specific "VIP" service accounts.

**Technical Implementation:**
We plan to use `django-ratelimit` and a Redis-backed sliding window algorithm. Every request will be tracked in Redis using the API key as the identifier. The usage analytics will be powered by a middleware that logs request metadata to a separate `ApiUsage` table. This feature is currently **blocked** pending the finalization of the API authentication schema.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints require a Bearer Token in the Authorization header. Base URL: `https://api.ember.verdantlabs.gov/v1/`

### 4.1 GET `/dashboard/widgets`
**Description:** Retrieves the list of available widgets the user can add to their dashboard.
- **Request:** `GET /dashboard/widgets`
- **Response (200 OK):**
```json
[
  {"id": "atk_ips", "name": "Top Attacking IPs", "category": "Threats", "default_size": {"w": 4, "h": 2}},
  {"id": "sys_health", "name": "System Health", "category": "Infrastructure", "default_size": {"w": 2, "h": 2}}
]
```

### 4.2 POST `/dashboard/layout`
**Description:** Saves the current drag-and-drop layout configuration.
- **Request:** `POST /dashboard/layout`
- **Payload:**
```json
{
  "layout": [
    {"i": "atk_ips", "x": 0, "y": 0, "w": 4, "h": 2},
    {"i": "sys_health", "x": 4, "y": 0, "w": 2, "h": 2}
  ]
}
```
- **Response (201 Created):** `{"status": "success", "layout_id": "df-9921"}`

### 4.3 GET `/audit/logs`
**Description:** Retrieves audit trail entries. Supports pagination and filtering.
- **Request:** `GET /audit/logs?start_date=2023-01-01&end_date=2023-01-31&user_id=123`
- **Response (200 OK):**
```json
{
  "logs": [
    {"id": 10293, "timestamp": "2023-01-15T10:00:01Z", "user": "jsmith", "action": "UPDATE_POLICY", "hash": "a1b2c3d4..."}
  ],
  "pagination": {"next": "/audit/logs?page=2"}
}
```

### 4.4 POST `/audit/verify`
**Description:** Verifies the integrity of the audit chain.
- **Request:** `POST /audit/verify`
- **Payload:** `{"start_id": 1000, "end_id": 2000}`
- **Response (200 OK):** `{"integrity": "valid", "chain_verified": true}`

### 4.5 GET `/metrics/alerts`
**Description:** Fetches active security alerts for the dashboard.
- **Request:** `GET /metrics/alerts?severity=critical`
- **Response (200 OK):**
```json
{
  "alerts": [
    {"id": "AL-99", "severity": "critical", "message": "Unauthorized SSH attempt from 192.168.1.1", "timestamp": "2023-10-20T14:00Z"}
  ]
}
```

### 4.6 POST `/reports/generate`
**Description:** Manually triggers a report generation (Currently Blocked).
- **Request:** `POST /reports/generate`
- **Payload:** `{"template_id": "rpt-01", "format": "pdf", "email": "admin@agency.gov"}`
- **Response (503 Service Unavailable):** `{"error": "Feature blocked: Design disagreement pending"}`

### 4.7 GET `/user/preferences`
**Description:** Retrieves localization and UI preferences.
- **Request:** `GET /user/preferences`
- **Response (200 OK):**
```json
{
  "language": "fr-FR",
  "timezone": "Europe/Paris",
  "theme": "dark"
}
```

### 4.8 PATCH `/user/preferences`
**Description:** Updates user localization settings.
- **Request:** `PATCH /user/preferences`
- **Payload:** `{"language": "de-DE"}`
- **Response (200 OK):** `{"status": "updated", "language": "de-DE"}`

---

## 5. DATABASE SCHEMA

The system uses a normalized PostgreSQL schema. All tables utilize UUIDs as primary keys for security and scalability.

### 5.1 Table Definitions

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | - | `email`, `password_hash`, `role`, `preferred_lang` | User identity and auth |
| `UserProfiles` | `profile_id` | `user_id` | `full_name`, `department`, `clearance_level` | Detailed user metadata |
| `AuditLogs` | `log_id` | `user_id` | `timestamp`, `action`, `payload`, `prev_hash`, `current_hash` | Tamper-evident trail |
| `DashboardConfigs` | `config_id` | `user_id` | `layout_json`, `last_updated`, `is_default` | Widget layout state |
| `Widgets` | `widget_id` | - | `slug`, `name`, `category`, `component_ref` | Widget registry |
| `SecurityAlerts` | `alert_id` | - | `severity`, `source_ip`, `message`, `resolved_at` | Security event data |
| `ReportTemplates` | `template_id` | `created_by_id` | `name`, `config_json`, `output_format` | Report definitions |
| `ScheduledReports` | `schedule_id` | `template_id`, `user_id` | `cron_expression`, `delivery_method` | Report timing |
| `ApiKeys` | `key_id` | `user_id` | `hashed_key`, `created_at`, `expires_at` | API Authentication |
| `LanguageMappings` | `lang_id` | - | `iso_code`, `display_name`, `is_rtl` | Localization support |

### 5.2 Relationships
- **Users $\rightarrow$ UserProfiles:** 1:1 (One profile per user).
- **Users $\rightarrow$ AuditLogs:** 1:N (One user generates many logs).
- **Users $\rightarrow$ DashboardConfigs:** 1:N (Users can have multiple layout versions).
- **User $\rightarrow$ ApiKeys:** 1:N (Users can generate multiple keys).
- **ReportTemplates $\rightarrow$ ScheduledReports:** 1:N (One template can be used for many schedules).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Ember utilizes a three-tier environment strategy to ensure stability.

#### 6.1.1 Development (Dev)
- **Purpose:** Active feature development and integration.
- **Trigger:** Deployment occurs on every push to a feature branch.
- **Database:** Shared Dev DB with anonymized data.
- **Configuration:** Loose security constraints to allow for rapid debugging.

#### 6.1.2 Staging (Stage)
- **Purpose:** Pre-production validation and QA.
- **Trigger:** Deployment occurs upon merging a PR into the `develop` branch.
- **Database:** A mirror of the production schema with synthetic data.
- **Configuration:** Strict adherence to FedRAMP security settings; used for "Dry Run" FedRAMP audits.

#### 6.1.3 Production (Prod)
- **Purpose:** Live government client access.
- **Trigger:** Continuous Deployment from the `main` branch.
- **Database:** High-availability PostgreSQL cluster with multi-AZ failover.
- **Configuration:** Full FedRAMP hardening, restricted SSH access, and mandatory audit logging.

### 6.2 Infrastructure Components
- **VPC:** A private Virtual Private Cloud with public subnets for the Load Balancer and private subnets for the ECS tasks and RDS.
- **AWS ECS Fargate:** Handles the containerized Django application. Auto-scaling is configured based on CPU and Memory utilization.
- **AWS RDS (PostgreSQL):** Managed database with automated backups and encryption.
- **AWS ElastiCache (Redis):** Managed Redis for high-speed caching and Celery task brokering.
- **AWS S3:** Encrypted buckets for storing generated PDF/CSV reports.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Scope:** Individual functions, Django models, and utility classes.
- **Tooling:** `pytest` and `unittest`.
- **Requirement:** 80% minimum code coverage.
- **Execution:** Run on every commit via GitHub Actions.

### 7.2 Integration Testing
- **Scope:** API endpoints, database transactions, and Redis cache interactions.
- **Approach:** Use Django's `RequestFactory` to simulate API calls and verify the resulting state change in the database.
- **Focus:** Specifically testing the "Tamper-Evident" hash chain to ensure that a single modified record breaks the subsequent chain.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., User Login $\rightarrow$ Customize Dashboard $\rightarrow$ Log out).
- **Tooling:** Cypress.
- **Approach:** Simulated browser interactions in the Staging environment.
- **Frequency:** Run on every merge to `main`.

### 7.4 QA Role
The dedicated QA engineer is responsible for creating "Edge Case" test suites, particularly regarding localization (e.g., testing how the UI handles very long German strings or Arabic RTL text) and FedRAMP compliance checks.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | High | High | Negotiate timeline extensions early; secure buy-in from the incoming sponsor. |
| R-02 | Key Architect leaving in 3 months | Medium | Critical | Raise as a blocker in the next board meeting; initiate aggressive knowledge transfer. |
| R-03 | FedRAMP authorization delay | Medium | High | Engage a dedicated compliance consultant; implement "Security by Design" from Day 1. |
| R-04 | Design disagreement (Product vs Eng) | High | Medium | Escalate to Farah Stein for final decision; use a "Time-Boxed" debate period. |
| R-05 | Technical Debt: Lack of structured logging | High | Medium | Implement `structlog` across the monolith to replace stdout debugging. |

### 8.1 Probability/Impact Matrix
- **Critical:** Immediate action required (R-02).
- **High:** Closely monitored with active mitigation (R-01, R-03, R-04).
- **Medium:** Tracked in weekly status meetings (R-05).

---

## 9. TIMELINE AND MILESTONES

### 9.1 Phase Descriptions
- **Phase 1: Core Foundation (Now - May 2026):** Implementation of Audit Trails, L10n, and Basic Dashboard functionality.
- **Phase 2: Hardening & Compliance (May 2026 - June 2026):** Final FedRAMP security audits and performance tuning.
- **Phase 3: Launch & Stability (June 2026 - August 2026):** Production rollout and stability monitoring.
- **Phase 4: Beta Expansion (August 2026 - October 2026):** Onboarding 10 pilot users and iterative feedback.

### 9.2 Key Milestones
- **Milestone 1: Production Launch**
  - **Target Date:** 2026-06-15
  - **Dependency:** Completion of Feature 4 (L10n) and Feature 5 (Audit Trail).
- **Milestone 2: Post-launch Stability Confirmed**
  - **Target Date:** 2026-08-15
  - **Dependency:** P95 API response time < 200ms.
- **Milestone 3: External Beta with 10 Pilot Users**
  - **Target Date:** 2026-10-15
  - **Dependency:** Success of Milestone 2 and stability of the "Customizable Dashboard."

---

## 10. MEETING NOTES ( running document extract )

*Note: These extracts are taken from the 200-page shared running document, which is currently unsearchable.*

### Meeting 1: Architecture Review (2023-10-10)
**Attendees:** Farah Stein, Priya Costa, [Architect Name]
- **Discussion:** Debate over Microservices vs. Monolith. Priya argued for microservices to handle the reporting load.
- **Decision:** Farah overruled, choosing a "Clean Monolith" to simplify the FedRAMP authorization process. 
- **Action Item:** Priya to define module boundaries within the Django app.

### Meeting 2: L10n Strategy (2023-10-17)
**Attendees:** Lina Liu, Farah Stein, Paloma Jensen
- **Discussion:** Lina presented the research on 12 languages. Concern raised about RTL (Right-to-Left) support for Arabic.
- **Decision:** The team will adopt a CSS-framework that supports RTL mirroring.
- **Action Item:** Lina to provide the finalized list of 12 target languages by next Tuesday.

### Meeting 3: The "Blocker" Conflict (2023-10-24)
**Attendees:** Farah Stein, [Engineering Lead], Lina Liu
- **Discussion:** Heated disagreement regarding the "Report Generation" UI. Engineering argues that a simple "Export" button is sufficient; Product (Farah) insists on a complex "Report Builder" interface.
- **Decision:** Feature 1 (Reports) and Feature 2 (Rate Limiting) are officially marked as **Blocked**.
- **Action Item:** Farah to schedule a design sprint to resolve the Report Builder UI.

---

## 11. BUDGET BREAKDOWN

Funding is released in tranches based on milestone completion. Total projected budget for Phase 1 is $2,400,000.

### 11.1 Personnel Costs (Annualized)
| Role | Count | Avg. Salary/Contract | Total |
| :--- | :--- | :--- | :--- |
| VP of Product (Farah) | 1 | $210,000 | $210,000 |
| Data Engineer (Priya) | 1 | $160,000 | $160,000 |
| UX Researcher (Lina) | 1 | $130,000 | $130,000 |
| Support Engineer (Paloma) | 1 | $110,000 | $110,000 |
| Backend Engineers | 2 | $150,000 | $300,000 |
| Dedicated QA | 1 | $120,000 | $120,000 |
| **Total Personnel** | | | **$1,030,000** |

### 11.2 Infrastructure & Tools (Monthly)
| Item | Provider | Estimated Cost | Annual Total |
| :--- | :--- | :--- | :--- |
| AWS ECS/Fargate | AWS | $8,000 | $96,000 |
| AWS RDS (Postgres) | AWS | $4,000 | $48,000 |
| AWS ElastiCache | AWS | $2,000 | $24,000 |
| GitHub Enterprise | GitHub | $1,500 | $18,000 |
| JIRA/Confluence | Atlassian | $1,000 | $12,000 |
| Translation TMS | External | $2,500 | $30,000 |
| **Total Infrastructure** | | | **$228,000** |

### 11.3 Contingency and Other
- **FedRAMP Certification Fees:** $450,000 (Consultants + Auditors).
- **Hardware/Testing Devices:** $50,000.
- **Emergency Contingency Fund:** $642,000 (To be used for risk mitigation R-01 and R-02).
- **Total Budget:** **$2,400,000**.

---

## 12. APPENDICES

### Appendix A: FedRAMP Compliance Checklist
The following technical controls must be verified before the Production Launch on 2026-06-15:
1. **AC-2 (Account Management):** Automated account lockouts after 5 failed attempts.
2. **AU-2 (Audit Events):** Verification that the `AuditLogs` table is capturing all `POST/PATCH/DELETE` requests.
3. **SC-28 (Protection of Data at Rest):** Confirmation that the RDS instance is encrypted using AWS KMS.
4. **IA-2 (Identification and Authentication):** MFA (Multi-Factor Authentication) enforced for all administrative users.

### Appendix B: Structured Logging Migration Plan
To resolve the current technical debt (reading `stdout`), the following migration plan is in place:
1. **Week 1:** Install `structlog` and `python-json-logger`.
2. **Week 2:** Replace all `print()` and `logging.info()` statements in the `Auth` and `Dashboard` modules with structured JSON logs.
3. **Week 3:** Configure AWS CloudWatch Logs to parse the JSON format for automated alerting.
4. **Week 4:** Implement a centralized logging dashboard in CloudWatch for the engineering team.

***

**End of Specification Document.**  
*All changes to this document must be proposed via JIRA ticket and approved by Farah Stein.*