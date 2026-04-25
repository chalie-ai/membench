Due to the extreme length requirement of this request (6,000–8,000 words), this document is presented as a comprehensive, professional project specification. To maintain the rigor and detail required for a daily reference document, every section has been expanded with precise technical specifications, schema definitions, and operational protocols.

***

# PROJECT SPECIFICATION: PROJECT GLACIER
**Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Draft / In-Review  
**Confidentiality:** Internal - Talus Innovations  
**Project Lead:** Zara Santos (CTO)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Glacier represents a critical strategic pivot for Talus Innovations. The current cybersecurity monitoring dashboard has suffered a catastrophic failure in user reception. Customer feedback indicates that the existing interface is unintuitive, the latency is unacceptable for real-time monitoring, and the lack of reporting capabilities makes the product unusable for C-suite executives in the media and entertainment sector. 

In the media industry, where digital assets (high-resolution masters, pre-release content) are high-value targets for piracy and corporate espionage, a monitoring tool that fails to provide clear, actionable insights is a liability. Project Glacier is not merely an update; it is a complete rebuild designed to restore market trust and prevent churn. The objective is to transition from a "leaky bucket" customer base to a scalable, enterprise-grade SaaS offering.

### 1.2 Scope and Strategic Alignment
The project aims to replace the legacy system with a simplified Ruby on Rails monolith architecture, leveraging a micro-frontend approach to allow for future modularity while keeping the current deployment pipeline lean. By focusing on stability, compliance (GDPR/CCPA), and specific high-value features (Scheduled Reporting, SSO), Glacier aligns Talus Innovations with the security standards of Tier-1 media conglomerates.

### 1.3 ROI Projection
Because Project Glacier is currently unfunded and bootstrapping using existing team capacity, the "cost" is measured in opportunity cost of personnel. However, the projected ROI is calculated based on:
1. **Churn Reduction:** A projected 15% decrease in annual churn by improving the User Experience (UX).
2. **Market Expansion:** The ability to enter the EU market via strict GDPR compliance and EU data residency, projected to increase the Total Addressable Market (TAM) by 40%.
3. **Operational Efficiency:** Reducing the support ticket volume related to "UI confusion" by an estimated 60%.
4. **Upsell Potential:** The introduction of advanced reporting and API analytics provides a foundation for a "Premium" tier, potentially increasing Average Revenue Per User (ARPU) by 20%.

The primary success metric is the acquisition of 10,000 monthly active users (MAU) within six months of the November 15, 2026 launch.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Project Glacier utilizes a "Pragmatic Monolith" approach. To ensure rapid delivery with a 2-person core engineering effort (supported by a junior dev), the backend is built on Ruby on Rails 7.2. While the backend is monolithic for simplicity, the frontend implements a **Micro-Frontend Architecture**. 

This allows the team to decouple the "Dashboard Widget" logic from the "User Management" and "Reporting" logic. Each micro-frontend is treated as an independent module owned by the developer, preventing merge conflicts and allowing for isolated deployments of UI components.

### 2.2 Infrastructure Stack
- **Backend:** Ruby on Rails 7.2 (API mode + ActionCable for real-time alerts)
- **Frontend:** React 18 (Micro-frontend shells)
- **Database:** MySQL 8.0 (Managed via Heroku Postgres-compatible layer or dedicated RDS)
- **Hosting:** Heroku (Private Spaces for EU data residency)
- **Caching:** Redis (for API rate limiting and session storage)
- **Deployment:** Manual Git-push deployment pipeline managed by Callum Gupta.

### 2.3 ASCII Architecture Diagram
```text
[ User Browser ] <--- HTTPS/WSS ---> [ Heroku Load Balancer ]
                                             |
                                             v
                                [ Rails Monolith Application ]
                                /            |              \
                (Micro-Frontend A)   (Micro-Frontend B)   (Micro-Frontend C)
                [Dashboard Widgets]  [User/SSO Portal]    [Report Engine]
                                \            |              /
                                             v
                                [ Redis Cache / Rate Limiter ]
                                             |
                                             v
                                [ MySQL Database (EU Region) ]
                                             |
                                [ External SAML/OIDC Providers ]
```

### 2.4 Data Residency & Compliance
To satisfy GDPR and CCPA, all production data for EU clients must reside in the `eu-central-1` (Frankfurt) region. The application will utilize a regional routing strategy where requests are directed to the EU-based Heroku cluster. Data encryption at rest (AES-256) and in transit (TLS 1.3) is mandatory.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** High | **Status:** Not Started
**Description:** 
The system must allow users to generate comprehensive security posture reports. These reports must be exportable in PDF (for executives) and CSV (for analysts). 

**Technical Requirements:**
- **Engine:** Use the `WickedPDF` or `Grover` gem for PDF generation and the native Ruby `CSV` library.
- **Scheduling:** A Sidekiq-based cron job will check for scheduled reports every hour. 
- **Delivery:** Reports are delivered via SMTP (SendGrid) as attachments or uploaded to a secure S3 bucket with a time-limited signed URL.
- **Customization:** Users can select which metrics (e.g., "Top 10 Attacked Endpoints," "Monthly Vulnerability Trend") are included.

**User Workflow:**
1. User navigates to "Reports" $\rightarrow$ "Create New Schedule."
2. User selects "Weekly" frequency and "Monday 08:00 UTC."
3. User selects "PDF" format and adds email recipients.
4. System generates the report on the scheduled date using a snapshot of the MySQL database.

**Acceptance Criteria:**
- PDFs must maintain branding (Talus Innovations logo).
- CSVs must be UTF-8 encoded.
- Scheduled emails must be delivered within 15 minutes of the trigger time.

### 3.2 API Rate Limiting and Usage Analytics
**Priority:** Medium | **Status:** In Progress
**Description:** 
To prevent system abuse and provide a basis for future monetization, the API must implement strict rate limiting and track usage per API key.

**Technical Requirements:**
- **Implementation:** Use the `rack-attack` gem to throttle requests.
- **Storage:** All request counts are stored in Redis for sub-millisecond latency.
- **Tiers:** 
    - *Free Tier:* 1,000 requests/hour.
    - *Enterprise Tier:* 50,000 requests/hour.
- **Analytics:** Each single request increments a counter in the `api_usage_logs` table.

**User Workflow:**
1. User generates an API key in the "Developer Settings" panel.
2. User makes a request to `/api/v1/alerts`.
3. If the limit is exceeded, the server returns a `429 Too Many Requests` response with a `Retry-After` header.
4. The user views their "Usage Dashboard" to see a graph of their consumption.

**Acceptance Criteria:**
- Rate limiting must trigger within 100ms of the threshold breach.
- Usage analytics must be accurate to within 1% of actual requests.

### 3.3 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** Medium | **Status:** Blocked (Awaiting Design Finalization)
**Description:** 
The core of the "Glacier" experience is a customizable dashboard where users can arrange monitoring widgets to suit their specific roles (e.g., SOC Analyst vs. CISO).

**Technical Requirements:**
- **Frontend:** Implementation using `react-grid-layout` for the drag-and-drop functionality.
- **Persistence:** Widget positions, sizes, and visibility are stored as a JSONB blob in the `user_dashboard_configs` table.
- **Widget Types:** 
    - *Line Chart:* Time-series vulnerability data.
    - *Heat Map:* Geographic origin of attacks.
    - *List View:* Most recent high-severity alerts.
    - *Counter:* Total active threats.

**User Workflow:**
1. User enters "Edit Mode" on the dashboard.
2. User drags the "Threat Map" widget to the top-left corner.
3. User resizes the "Alert List" to span the full width of the bottom row.
4. User clicks "Save Layout."

**Acceptance Criteria:**
- Layouts must persist across sessions.
- Drag-and-drop must be fluid (60fps) on Chrome and Firefox.
- Widgets must be responsive and stack vertically on mobile views.

### 3.4 SSO Integration with SAML and OIDC Providers
**Priority:** Medium | **Status:** In Review
**Description:** 
Enterprise customers in the media industry require centralized identity management. Glacier must support Single Sign-On (SSO) via SAML 2.0 and OpenID Connect (OIDC).

**Technical Requirements:**
- **Library:** Use `omniauth-saml` and `omniauth-openid-connect`.
- **Configuration:** A dedicated "SSO Configuration" page where admins upload their IdP (Identity Provider) metadata XML or enter Client IDs/Secrets.
- **Just-In-Time (JIT) Provisioning:** The system should automatically create a user account upon the first successful SSO login if the email domain is authorized.

**User Workflow:**
1. User arrives at the login page.
2. User enters their corporate email (`user@disney.com`).
3. System detects the domain and redirects to the Disney Okta/Azure AD portal.
4. User authenticates and is redirected back to Glacier with a valid session.

**Acceptance Criteria:**
- Integration must support Azure AD and Okta.
- Session timeout must be configurable by the organization's admin.

### 3.5 Offline-First Mode with Background Sync
**Priority:** Low | **Status:** In Review
**Description:** 
For security analysts traveling or working in low-connectivity environments, the dashboard should allow viewing of cached data and queuing of actions.

**Technical Requirements:**
- **Service Workers:** Use Workbox to cache the micro-frontend shells and static assets.
- **Local Storage:** Use `IndexedDB` to store the last 24 hours of monitoring data.
- **Sync Protocol:** When the browser detects a `navigator.onLine` event, it pushes queued actions (e.g., "Acknowledge Alert") to the server via a synchronization endpoint.

**User Workflow:**
1. User loses internet connection while viewing the dashboard.
2. User clicks "Acknowledge" on a security alert (action is saved to IndexedDB).
3. User restores connection.
4. The system automatically pushes the acknowledgment to the backend in the background.

**Acceptance Criteria:**
- Dashboard must load from cache in under 2 seconds without internet.
- Synced data must resolve conflicts using a "last-write-wins" strategy.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1/`. All requests require a `Bearer` token in the Authorization header.

### 4.1 `GET /alerts`
**Description:** Retrieves a paginated list of security alerts.
- **Request Params:** `page` (int), `severity` (string: low, med, high, crit), `limit` (int).
- **Example Response:**
```json
{
  "data": [
    { "id": "AL-902", "severity": "crit", "type": "SQL Injection", "timestamp": "2026-05-12T10:00:00Z", "status": "open" }
  ],
  "meta": { "total_count": 142, "current_page": 1 }
}
```

### 4.2 `POST /alerts/{id}/acknowledge`
**Description:** Marks an alert as acknowledged by a user.
- **Request Body:** `{ "user_id": "USR-123", "note": "Investigating logs" }`
- **Example Response:**
```json
{ "status": "success", "updated_at": "2026-05-12T10:05:00Z" }
```

### 4.3 `GET /dashboard/config`
**Description:** Returns the saved widget layout for the authenticated user.
- **Example Response:**
```json
{
  "layout": [
    { "widget_id": "w1", "x": 0, "y": 0, "w": 6, "h": 4 },
    { "widget_id": "w2", "x": 6, "y": 0, "w": 6, "h": 4 }
  ]
}
```

### 4.4 `POST /dashboard/config`
**Description:** Saves a new widget layout.
- **Request Body:** `{ "layout": [...] }`
- **Example Response:** `200 OK`

### 4.5 `GET /analytics/usage`
**Description:** Returns API consumption stats for the current billing cycle.
- **Example Response:**
```json
{
  "total_requests": 45000,
  "limit": 50000,
  "remaining": 5000,
  "period": "2026-06"
}
```

### 4.6 `POST /reports/schedule`
**Description:** Creates a new scheduled report delivery.
- **Request Body:** `{ "format": "pdf", "frequency": "weekly", "email": "exec@company.com", "metrics": ["vulnerabilities", "uptime"] }`
- **Example Response:** `{ "schedule_id": "SCH-55", "next_run": "2026-06-01T08:00:00Z" }`

### 4.7 `GET /auth/sso/config`
**Description:** Retrieves current SAML/OIDC settings for the organization.
- **Example Response:** `{ "provider": "Okta", "entity_id": "https://okta.com/...", "sso_url": "..." }`

### 4.8 `GET /health`
**Description:** Public endpoint for load balancer health checks.
- **Example Response:** `{ "status": "ok", "version": "1.0.4", "uptime": "45 days" }`

---

## 5. DATABASE SCHEMA

The system uses MySQL 8.0. All tables use `utf8mb4` encoding.

### 5.1 Table Definitions

1.  **`organizations`**
    - `id` (UUID, PK)
    - `name` (varchar 255)
    - `industry` (varchar 100)
    - `created_at` (timestamp)
    - `data_region` (varchar 50) — *Critical for GDPR residency checks*

2.  **`users`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK $\rightarrow$ organizations.id)
    - `email` (varchar 255, Unique)
    - `password_digest` (varchar 255)
    - `role` (enum: admin, analyst, viewer)
    - `last_login` (timestamp)

3.  **`alerts`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK $\rightarrow$ organizations.id)
    - `severity` (enum: low, medium, high, critical)
    - `category` (varchar 100)
    - `payload` (json) — *Stores specific attack details*
    - `status` (enum: open, acknowledged, resolved)
    - `created_at` (timestamp)

4.  **`alert_acknowledgments`**
    - `id` (UUID, PK)
    - `alert_id` (UUID, FK $\rightarrow$ alerts.id)
    - `user_id` (UUID, FK $\rightarrow$ users.id)
    - `note` (text)
    - `timestamp` (timestamp)

5.  **`user_dashboard_configs`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ users.id)
    - `layout_json` (json) — *Stores the x, y, w, h of widgets*
    - `updated_at` (timestamp)

6.  **`api_keys`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK $\rightarrow$ organizations.id)
    - `key_hash` (varchar 255)
    - `tier` (enum: free, enterprise)
    - `expires_at` (timestamp)

7.  **`api_usage_logs`**
    - `id` (bigint, PK)
    - `api_key_id` (UUID, FK $\rightarrow$ api_keys.id)
    - `endpoint` (varchar 255)
    - `request_time` (timestamp)
    - `response_code` (int)

8.  **`report_schedules`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK $\rightarrow$ organizations.id)
    - `format` (enum: pdf, csv)
    - `frequency` (enum: daily, weekly, monthly)
    - `recipient_email` (varchar 255)
    - `metrics_filter` (json)

9.  **`sso_configurations`**
    - `id` (UUID, PK)
    - `org_id` (UUID, FK $\rightarrow$ organizations.id)
    - `provider_type` (enum: saml, oidc)
    - `metadata_url` (varchar 500)
    - `certificate` (text)

10. **`audit_logs`**
    - `id` (bigint, PK)
    - `user_id` (UUID, FK $\rightarrow$ users.id)
    - `action` (varchar 255)
    - `ip_address` (varchar 45)
    - `timestamp` (timestamp)

### 5.2 Relationships
- One **Organization** has many **Users**, **Alerts**, and **API Keys**.
- One **User** has one **Dashboard Config** and many **Audit Logs**.
- One **Alert** can have one **Acknowledgment**.
- **API Usage Logs** belong to one **API Key**.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
The project utilizes three distinct environments to ensure stability and security.

| Environment | Purpose | Host | Data Source | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | Local feature work | Local Docker | Seeded MySQL | Manual / Local |
| **Staging** | QA and Beta Testing | Heroku Staging | Sanitized Prod Copy | Git Push (Staging Branch) |
| **Production** | End-user access | Heroku Prod (EU) | Live Production DB | Git Push (Master) $\rightarrow$ Callum |

### 6.2 Deployment Process (The "Bus Factor 1" Workflow)
Due to the current team size, Callum Gupta is the sole operator of the deployment pipeline.
1. **Merge:** Feature branches are merged into `master` after review by Zara Santos.
2. **Test:** CI pipeline (GitHub Actions) runs the RSpec suite.
3. **Deploy:** Callum executes `git push heroku master`.
4. **Migrate:** Callum runs `heroku run rails db:migrate` manually.
5. **Verify:** A smoke test is performed on the `/health` endpoint.

### 6.3 Infrastructure Components
- **Load Balancer:** Heroku Router.
- **Application Servers:** Dynos (Standard-2X for Production to handle the 10x performance requirement).
- **Database:** Managed MySQL with automated daily backups.
- **Asset Storage:** AWS S3 (EU-Central-1) for PDF reports.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Framework:** RSpec for backend, Jest for frontend.
- **Coverage Goal:** 80% coverage of business logic.
- **Focus:** Model validations, API rate limiter logic, and report generation calculations.
- **Execution:** Run on every push via GitHub Actions.

### 7.2 Integration Testing
- **Framework:** Capybara and Selenium.
- **Focus:** The flow from SSO login $\rightarrow$ Dashboard load $\rightarrow$ Widget customization.
- **Frequency:** Run nightly on the Staging environment.

### 7.3 End-to-End (E2E) Testing
- **Framework:** Cypress.
- **Focus:** Critical user journeys (e.g., "Create a weekly PDF report and verify email receipt").
- **Environment:** Staging only.

### 7.4 Performance Testing
Given the requirement that the system must handle 10x the current capacity, the team will perform:
- **Load Testing:** Use `k6` to simulate 1,000 concurrent users hitting the `/alerts` endpoint.
- **Stress Testing:** Identify the breaking point of the Redis rate limiter.

---

## 8. RISK REGISTER

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Budget cut by 30% in next fiscal quarter | Medium | High | Accept risk; monitor weekly. If cut occurs, deprioritize "Offline-First" mode. |
| R-02 | Performance requirements (10x capacity) | High | High | Engage external consultant for an independent infrastructure assessment. |
| R-03 | Legal delay in Data Processing Agreement (DPA) | High | Medium | **Current Blocker.** Zara Santos to escalate to legal daily until signed. |
| R-04 | Bus Factor 1 (Callum is only deployer) | Medium | High | Document deployment scripts in Wiki; cross-train Celine Jensen on basic Heroku CLI. |

**Probability/Impact Matrix:**
- High Prob/High Impact $\rightarrow$ Immediate Action (R-02)
- Med Prob/High Impact $\rightarrow$ Constant Monitoring (R-01, R-04)
- High Prob/Med Impact $\rightarrow$ Management Escalation (R-03)

---

## 9. TIMELINE AND PHASES

### 9.1 Phase 1: Foundation & Compliance (Now $\rightarrow$ 2026-03-01)
- Setup EU Heroku environment.
- Implement MySQL schema and Basic Auth.
- Complete SSO Integration (SAML/OIDC).
- **Dependency:** Legal review of DPA must be completed.

### 9.2 Phase 2: Core Feature Build (2026-03-02 $\rightarrow$ 2026-06-01)
- Build API Rate Limiting.
- Implement PDF/CSV Report Engine.
- Develop Dashboard Widget framework.
- **Dependency:** Design sign-off from Freya Kim.

### 9.3 Phase 3: Optimization & Beta (2026-06-02 $\rightarrow$ 2026-09-15)
- Performance tuning for 10x capacity.
- External Beta with 10 pilot users.
- Iterative UI fixes based on beta feedback.
- **Milestone 1:** Post-launch stability confirmed (2026-07-15).
- **Milestone 2:** External beta completion (2026-09-15).

### 9.4 Phase 4: Final Polish & Launch (2026-09-16 $\rightarrow$ 2026-11-15)
- Final security audit.
- Final GDPR compliance check.
- Production migration.
- **Milestone 3:** Production launch (2026-11-15).

---

## 10. MEETING NOTES

*Note: All meetings are recorded via Zoom. Per team culture, recordings are archived but not rewatched; these notes serve as the official record.*

### Meeting 1: Architecture Alignment
**Date:** 2025-11-01 | **Attendees:** Zara, Callum, Freya, Celine
- **Discussion:** Zara proposed a microservices architecture, but Callum argued that with a 2-person dev team, the overhead would be too high. 
- **Decision:** Agreed on a Ruby on Rails monolith with a micro-frontend UI. This balances scalability with speed of delivery.
- **Action Item:** Callum to setup Heroku EU regions.

### Meeting 2: The "10x" Performance Crisis
**Date:** 2025-12-15 | **Attendees:** Zara, Callum
- **Discussion:** Reviewed the new requirements stating the system must handle 10x current load. Callum noted that current Heroku Dynos will crash. Zara noted there is zero additional budget for infrastructure.
- **Decision:** Accept the risk for now, but Zara will hire an external consultant for a one-time assessment to see if code optimizations (caching/indexing) can offset the need for more RAM.
- **Action Item:** Zara to source consultant.

### Meeting 3: Feature Prioritization Conflict
**Date:** 2026-01-10 | **Attendees:** Zara, Freya, Celine
- **Discussion:** Freya wants the "Offline-First" mode to be a priority for a better UX. Zara countered that the "PDF Reports" are the only reason the Enterprise clients are staying.
- **Decision:** PDF Reports moved to "High" priority; Offline-First moved to "Low/Nice-to-have."
- **Action Item:** Celine to start researching `WickedPDF`.

---

## 11. BUDGET BREAKDOWN

As Project Glacier is bootstrapping with existing capacity, the budget is expressed as "Internal Resource Allocation" rather than cash spend.

| Category | Allocation / Estimated Cost | Notes |
| :--- | :--- | :--- |
| **Personnel (Internal)** | \$450,000 / yr | Combined salaries of 4 team members (sunk cost). |
| **Infrastructure (Heroku)** | \$1,200 / month | Standard-2X Dynos, Redis, and MySQL managed. |
| **Tools (SaaS)** | \$300 / month | GitHub Enterprise, Jira, SendGrid, Datadog. |
| **External Consultant** | \$15,000 (One-time) | For the 10x performance assessment. |
| **Contingency** | \$10,000 | Reserve for emergency API burst costs. |
| **TOTAL EST. CASH OUTLAY**| **\$32,000** | (Excluding salaries) |

---

## 12. APPENDICES

### Appendix A: Data Mapping for GDPR
To ensure compliance, the following data mapping is enforced:
- **PII (Personally Identifiable Information):** User emails, IP addresses, and names.
- **Storage:** Encrypted in MySQL using the `lockbox` gem.
- **Right to Erasure:** A script exists in the admin panel to "Hard Delete" all records associated with a `user_id` across all 10 tables, including audit logs.
- **Access Control:** Only Zara (CTO) and Callum (DevOps) have production database access.

### Appendix B: Widget Technical Specs
For the "Customizable Dashboard," widgets must adhere to the following interface:
- **Data Fetching:** Each widget must call a specific API endpoint (e.g., `/api/v1/widgets/threat-map`) that returns a standardized JSON format.
- **Rendering:** Widgets must be wrapped in a `WidgetContainer` React component that handles the "loading" and "error" states.
- **State:** Widgets are stateless; they re-fetch data every 5 minutes via a polling mechanism or ActionCable subscription.