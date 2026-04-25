# Project Specification: Project Eclipse
**Version:** 1.0.4  
**Date:** October 24, 2025  
**Status:** Active / In-Development  
**Company:** Deepwell Data  
**Industry:** Healthcare Cybersecurity  
**Classification:** Confidential / PCI DSS Level 1 Compliant  

---

## 1. Executive Summary

### Business Justification
Project Eclipse represents a critical strategic pivot for Deepwell Data. Following the release of our legacy cybersecurity monitoring dashboard, the company received catastrophic user feedback. Clients reported that the interface was non-intuitive, the data latency was unacceptable for high-stakes healthcare environments, and the reporting tools were insufficient for HIPAA compliance audits. In the healthcare sector, where milliseconds can be the difference between containing a ransomware attack and a total system blackout, a failure in monitoring is a failure in patient safety.

The legacy system suffered from a monolithic architecture that prevented rapid iteration and scaled poorly. Project Eclipse is not merely an update but a total rebuild designed to restore market confidence and reclaim our position as a leader in healthcare security telemetry. By migrating to a micro-frontend architecture and a robust Python/Django backend, Eclipse will provide the modularity required to evolve alongside the rapidly shifting threat landscape.

### ROI Projection and Strategic Goals
The primary financial driver for Eclipse is the reduction of churn among our Tier-1 healthcare providers. We project that by addressing the usability failures of the previous version, we will increase customer retention by 40% over the next 18 months. 

Furthermore, the transition to a shared-infrastructure multi-tenant model is designed to optimize cloud spend. The target is a **35% reduction in cost per transaction** compared to the legacy system. By optimizing how we handle telemetry data in PostgreSQL and leveraging Redis for high-frequency caching, we expect to lower our AWS ECS operational costs significantly.

The return on investment (ROI) is calculated based on:
1. **Churn Mitigation:** Saving an estimated $1.2M in annual recurring revenue (ARR) from at-risk accounts.
2. **Operational Efficiency:** Lowering the cost of support tickets (currently high due to the legacy UI's complexity).
3. **Market Competitiveness:** Closing the gap with a primary competitor who is currently two months ahead in feature parity.

The budget of $800,000 is allocated to ensure a high-quality, security-first build over a six-month window, focusing on stability, PCI DSS compliance, and a superior user experience.

---

## 2. Technical Architecture

### Architectural Philosophy
Project Eclipse utilizes a **Micro-Frontend (MFE) Architecture**. This approach decouples the UI into independent, domain-driven modules. Each module is owned by a specific logic stream, allowing the solo developer to iterate on specific features (e.g., Reporting vs. Authentication) without risking regression across the entire dashboard.

### The Stack
- **Backend:** Python 3.11 / Django 4.2 (REST Framework)
- **Database:** PostgreSQL 15 (Primary Store)
- **Caching/Queue:** Redis 7.0 (Session management, Celery task broker)
- **Deployment:** AWS ECS (Fargate)
- **CI/CD:** GitHub Actions $\rightarrow$ AWS ECR $\rightarrow$ ECS
- **Security Standard:** PCI DSS Level 1 (Required for direct credit card processing for subscription billing)

### System Topology (ASCII Diagram Description)
The architecture follows a request-response flow through a secure gateway.

```text
[ Client Browser ] 
       |
       v
[ AWS Application Load Balancer ] <--- SSL Termination (TLS 1.3)
       |
       +-----------------------+-----------------------+
       |                        |                       |
[ MFE: Auth Module ]    [ MFE: Monitoring ]    [ MFE: Reporting ]
       |                        |                       |
       +-----------------------+-----------------------+
                               |
                    [ Django API Gateway / App Layer ]
                               |
       +-----------------------+-----------------------+
       |                        |                       |
[ Redis Cache ]        [ PostgreSQL DB ]        [ Third-Party APIs ]
(Session/Queue)        (Multi-tenant Data)      (Threat Intelligence)
```

### Data Isolation Strategy
To satisfy healthcare privacy requirements, Eclipse implements a "Shared Infrastructure, Isolated Data" model. Every table in the PostgreSQL database contains a `tenant_id` UUID. A Django middleware layer intercepts every request to ensure that the `tenant_id` of the authenticated user matches the `tenant_id` of the requested data, preventing cross-tenant data leakage.

---

## 3. Detailed Feature Specifications

### 3.1 User Authentication and Role-Based Access Control (RBAC)
**Priority:** Low | **Status:** Not Started | **Requirement ID:** FEAT-001

**Description:**
Despite its low priority relative to data isolation, RBAC is the foundation of the security posture. The system must support granular permissions for three primary roles: `SuperAdmin` (Deepwell Data staff), `OrgAdmin` (Hospital IT Director), and `SecurityAnalyst` (Daily operator).

**Functional Specifications:**
- **Identity Management:** Integration with Django’s `AbstractUser` model. Users must be mapped to a `Organization` entity.
- **Permission Matrix:** 
    - `SuperAdmin`: Full system access, billing management, global configuration.
    - `OrgAdmin`: User management within their tenant, report scheduling, API key generation.
    - `SecurityAnalyst`: Read-only access to dashboards, ability to acknowledge alerts.
- **Session Management:** Redis-backed session storage with a hard timeout of 30 minutes of inactivity to comply with healthcare security standards.
- **Audit Logging:** Every permission change must be logged in the `audit_logs` table, recording the actor, the action, the timestamp, and the IP address.

**Acceptance Criteria:**
- A user cannot access an endpoint if their role lacks the required permission.
- Changing a role in the admin panel reflects in the user's session within 60 seconds.

### 3.2 Two-Factor Authentication (2FA) with Hardware Key Support
**Priority:** Low | **Status:** In Progress | **Requirement ID:** FEAT-002

**Description:**
To satisfy PCI DSS Level 1 and healthcare security mandates, 2FA is required for all privileged accounts. While software tokens (TOTP) are standard, Eclipse must support hardware-based authentication (FIDO2/WebAuthn) to prevent session hijacking via phishing.

**Functional Specifications:**
- **WebAuthn Integration:** Implementation of the `python-fido2` library to handle registration and authentication of YubiKeys and Titan keys.
- **Fallback Mechanism:** If a hardware key is lost, `OrgAdmin` users can trigger a recovery process involving a verified secondary email and a manual identity check.
- **Enforcement Policy:** The system must allow `OrgAdmins` to mandate 2FA for all users within their organization.
- **Enrollment Flow:** A guided wizard during the first login that prompts the user to register at least one hardware key or TOTP app.

**Acceptance Criteria:**
- Users cannot bypass the 2FA screen after providing a valid password if 2FA is enabled.
- Hardware keys are successfully registered and verified using the WebAuthn standard.

### 3.3 Offline-First Mode with Background Sync
**Priority:** High | **Status:** In Progress | **Requirement ID:** FEAT-003

**Description:**
Healthcare environments often have "dead zones" or unstable network conditions within hospitals. The dashboard must remain functional when the connection is lost, allowing analysts to view cached data and queue actions (such as acknowledging alerts) for later synchronization.

**Functional Specifications:**
- **Client-Side Storage:** Utilization of IndexedDB via a service worker to cache the last 24 hours of telemetry data.
- **Sync Queue:** A local "Outbox" pattern where any POST/PATCH request made while offline is stored as a JSON blob in IndexedDB.
- **Background Synchronization:** Using the `ServiceWorker` Background Sync API to push queued requests to the server as soon as the `navigator.onLine` event fires.
- **Conflict Resolution:** A "Last-Write-Wins" strategy for simple alerts, and a "Server-Authoritative" strategy for configuration changes.

**Acceptance Criteria:**
- The dashboard loads and displays the last cached state when the browser is in Airplane Mode.
- Actions performed offline are automatically pushed to the server upon reconnection without user intervention.

### 3.4 Multi-Tenant Data Isolation with Shared Infrastructure
**Priority:** High | **Status:** In Review | **Requirement ID:** FEAT-004

**Description:**
To keep the budget viable and the infrastructure manageable, the project uses a single PostgreSQL instance and a single ECS cluster. However, data must be logically isolated so that Hospital A can never see Hospital B's data, even in the event of a SQL injection or API leak.

**Functional Specifications:**
- **Row-Level Security (RLS):** Implementation of PostgreSQL RLS policies. Every query must be filtered by `tenant_id`.
- **Tenant Context Middleware:** A Django middleware that extracts the `tenant_id` from the authenticated JWT and sets a session variable in PostgreSQL: `SET app.current_tenant = 'uuid-here'`.
- **Schema Design:** All primary tables (e.g., `alerts`, `devices`, `logs`) must include a non-nullable `tenant_id` foreign key.
- **Isolation Validation:** An automated test suite that attempts to access Record X (Tenant A) using a Token from Tenant B; the test must return a 404 or 403.

**Acceptance Criteria:**
- Zero instances of cross-tenant data leakage during penetration testing.
- Performance overhead of RLS must be less than 5% compared to standard queries.

### 3.5 PDF/CSV Report Generation with Scheduled Delivery
**Priority:** Medium | **Status:** In Progress | **Requirement ID:** FEAT-005

**Description:**
Compliance officers require monthly and weekly summaries of security incidents. The system must generate high-fidelity PDF and CSV reports and deliver them via encrypted email or SFTP.

**Functional Specifications:**
- **Asynchronous Generation:** Use of Celery workers to handle PDF rendering (via WeasyPrint) to avoid blocking the main request thread.
- **Templating:** Jinja2 templates for PDF layouts, ensuring the Deepwell Data branding is consistent.
- **Scheduling Engine:** A cron-like scheduler within Django (using `django-celery-beat`) allowing users to set "Every Monday at 8 AM" for report delivery.
- **Delivery Pipelines:** Integration with AWS SES for email delivery and a custom SFTP agent for enterprise clients.

**Acceptance Criteria:**
- Reports generate within 30 seconds for datasets up to 10,000 rows.
- Scheduled reports are delivered within 15 minutes of the target time.

---

## 4. API Endpoint Documentation

All endpoints are versioned under `/api/v1/`. All requests require a Bearer Token in the Authorization header.

### 4.1 Authentication & Users
| Endpoint | Method | Description | Request Example | Response Example |
| :--- | :--- | :--- | :--- | :--- |
| `/auth/login/` | POST | Returns JWT and session ID | `{"username": "jdoe", "password": "..."}` | `{"token": "eyJ...", "refresh": "..."}` |
| `/auth/2fa/verify/` | POST | Verifies WebAuthn assertion | `{"credentialId": "...", "signature": "..."}` | `{"status": "verified"}` |

### 4.2 Monitoring & Telemetry
| Endpoint | Method | Description | Request Example | Response Example |
| :--- | :--- | :--- | :--- | :--- |
| `/telemetry/alerts/` | GET | List alerts for current tenant | `?severity=high&limit=20` | `[{"id": 101, "msg": "Unauthorized SSH"}]` |
| `/telemetry/alerts/{id}/` | PATCH | Update alert status (Ack/Close) | `{"status": "acknowledged"}` | `{"id": 101, "status": "acknowledged"}` |
| `/telemetry/devices/` | GET | List all monitored endpoints | `?status=active` | `[{"id": "dev_1", "ip": "10.0.0.1"}]` |
| `/telemetry/stats/` | GET | Aggregated health metrics | `?range=24h` | `{"uptime": 99.9, "threats": 12}` |

### 4.3 Reporting & Billing
| Endpoint | Method | Description | Request Example | Response Example |
| :--- | :--- | :--- | :--- | :--- |
| `/reports/generate/` | POST | Trigger immediate report | `{"type": "pdf", "range": "last_30_days"}` | `{"job_id": "celery_abc123"}` |
| `/reports/schedule/` | POST | Create a recurring report | `{"cron": "0 8 * * 1", "email": "..."}` | `{"schedule_id": "sched_789"}` |

---

## 5. Database Schema

The database uses PostgreSQL 15. All tables utilize UUIDs as primary keys to prevent ID enumeration attacks.

### Table Definitions

1. **`organizations`**
   - `id` (UUID, PK): Primary Identifier
   - `name` (Varchar): Hospital/Clinic Name
   - `pci_compliance_level` (Int): 1, 2, or 3
   - `created_at` (Timestamp)

2. **`users`**
   - `id` (UUID, PK): Primary Identifier
   - `org_id` (UUID, FK $\rightarrow$ organizations): Tenant link
   - `email` (Varchar, Unique): Login identifier
   - `password_hash` (Varchar): Argon2id hash
   - `role` (Enum): SuperAdmin, OrgAdmin, SecurityAnalyst

3. **`user_2fa_keys`**
   - `id` (UUID, PK)
   - `user_id` (UUID, FK $\rightarrow$ users)
   - `public_key` (Text): WebAuthn public key
   - `sign_count` (Int): Replay attack prevention
   - `created_at` (Timestamp)

4. **`devices`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ organizations): RLS Key
   - `hostname` (Varchar)
   - `ip_address` (Inet)
   - `last_seen` (Timestamp)

5. **`alerts`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ organizations): RLS Key
   - `device_id` (UUID, FK $\rightarrow$ devices)
   - `severity` (Enum): Low, Medium, High, Critical
   - `message` (Text)
   - `status` (Enum): New, Acknowledged, Resolved
   - `timestamp` (Timestamp)

6. **`audit_logs`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ organizations)
   - `user_id` (UUID, FK $\rightarrow$ users)
   - `action` (Varchar): e.g., "USER_ROLE_CHANGE"
   - `payload` (JSONB): Previous and New values
   - `ip_address` (Inet)
   - `timestamp` (Timestamp)

7. **`report_schedules`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ organizations)
   - `cron_expression` (Varchar)
   - `report_type` (Enum): PDF, CSV
   - `delivery_method` (Enum): Email, SFTP
   - `recipient_email` (Varchar)

8. **`generated_reports`**
   - `id` (UUID, PK)
   - `schedule_id` (UUID, FK $\rightarrow$ report_schedules)
   - `s3_url` (Varchar): Link to the encrypted file in AWS S3
   - `generated_at` (Timestamp)

9. **`billing_subscriptions`**
   - `id` (UUID, PK)
   - `tenant_id` (UUID, FK $\rightarrow$ organizations)
   - `stripe_customer_id` (Varchar): PCI DSS payment link
   - `plan_level` (Varchar)
   - `next_billing_date` (Date)

10. **`sync_logs`**
    - `id` (UUID, PK)
    - `user_id` (UUID, FK $\rightarrow$ users)
    - `sync_timestamp` (Timestamp)
    - `records_synced` (Int)
    - `status` (Enum): Success, Partial, Failed

### Relationships
- **One-to-Many:** `Organization` $\rightarrow$ `Users`, `Devices`, `Alerts`, `Schedules`.
- **One-to-One:** `User` $\rightarrow$ `2FA_Keys` (though users can have multiple, we treat the primary as the link).
- **Many-to-One:** `Alerts` $\rightarrow$ `Devices`.
- **Many-to-One:** `Generated_Reports` $\rightarrow$ `Schedules`.

---

## 6. Deployment and Infrastructure

### Infrastructure as Code (IaC)
The entire environment is provisioned via Terraform. This ensures that the staging and production environments are identical clones, minimizing "works on my machine" bugs.

### Environment Descriptions

#### Development (Dev)
- **Purpose:** Local iteration and feature branch testing.
- **Configuration:** Docker Compose running Python, PostgreSQL, and Redis.
- **Deployment:** Manual trigger on local machine.
- **Data:** Mocked data; no real PII (Personally Identifiable Information).

#### Staging (Staging)
- **Purpose:** Pre-production validation and QA.
- **Configuration:** AWS ECS Fargate (Small instance size).
- **Deployment:** Automated via GitHub Actions on merge to `develop` branch.
- **Data:** Sanitized production snapshots (scrubbed of PII).

#### Production (Prod)
- **Purpose:** Live customer traffic.
- **Configuration:** AWS ECS Fargate (Auto-scaling enabled, Multi-AZ deployment).
- **Deployment:** Continuous Deployment (CD). Every PR merged to `main` is deployed immediately after passing the full test suite.
- **Security:** AWS WAF (Web Application Firewall) protecting against SQLi and XSS; AWS KMS for encrypting data at rest.

### CI/CD Pipeline Flow
1. **Commit:** Developer pushes to a feature branch.
2. **Lint/Unit Test:** GitHub Actions runs `flake8` and `pytest`.
3. **Review:** Peer review required.
4. **Merge:** PR merged to `main`.
5. **Build:** Docker image built and pushed to AWS ECR.
6. **Deploy:** ECS service updated via rolling update (zero downtime).
7. **Health Check:** ALB verifies `/health` endpoint before shifting traffic.

---

## 7. Testing Strategy

### 7.1 Unit Testing
- **Scope:** Individual functions, utility classes, and Django models.
- **Tooling:** `pytest` and `unittest.mock`.
- **Requirement:** 90% code coverage for all new business logic.
- **Frequency:** Every commit.

### 7.2 Integration Testing
- **Scope:** API endpoints and Database interactions.
- **Tooling:** `Django Test Client` and `Postman/Newman`.
- **Focus:** 
    - Ensuring that the `tenant_id` middleware correctly filters data.
    - Verifying that Celery tasks correctly transition from `PENDING` to `SUCCESS`.
    - Testing the WebAuthn handshake between the frontend and the backend.
- **Frequency:** Every merge to `develop`.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ View Alert $\rightarrow$ Acknowledge $\rightarrow$ Generate Report").
- **Tooling:** `Playwright` or `Cypress`.
- **Focus:** Testing the Micro-Frontend interaction. Since each MFE is independent, E2E tests ensure that the "shell" application orchestrates them correctly.
- **Frequency:** Once per day in Staging.

### 7.4 Security Testing
- **Penetration Testing:** Quarterly external audits.
- **Static Analysis:** `Bandit` used to scan Python code for common security vulnerabilities.
- **PCI Compliance:** Monthly scans of the network to ensure no unencrypted credit card data is hitting the logs.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Project sponsor rotating out of role | Medium | High | **Parallel-Path:** Maintain a detailed prototype and design document so a new sponsor can be onboarded in $<1$ week. |
| R-02 | Competitor is 2 months ahead | High | Medium | **Workaround Documentation:** Document current competitor gaps and share with the sales team to position Eclipse as the "more stable" alternative. |
| R-03 | Third-party API rate limits | High | Medium | **Current Blocker:** Implement a Redis-based request queue and a caching layer to reduce API calls during testing. |
| R-04 | PCI DSS Audit failure | Low | Critical | **Strict Compliance:** Use a dedicated PCI-compliant vault for card data; strictly forbid card data in the main PostgreSQL DB. |
| R-05 | Solo developer burnout | Medium | High | **Disciplined Debt Mgmt:** Spend every second Friday on "Technical Debt Day" to prevent codebase rot. |

### Probability/Impact Matrix
- **Critical:** Immediate project failure or legal catastrophe.
- **High:** Significant delay or loss of key feature.
- **Medium:** Noticeable impact, but manageable through effort.
- **Low:** Minor inconvenience.

---

## 9. Timeline

The project is scheduled for a 6-month build cycle.

### Phase 1: Foundation & Architecture (Months 1-2)
- **Focus:** Establishing the MFE shell, PostgreSQL RLS, and the basic Django API.
- **Dependency:** Architecture review must be signed off.
- **Key Date:** **Milestone 1: Architecture review complete (2026-08-15).**

### Phase 2: Core Feature Build-Out (Months 3-4)
- **Focus:** Offline-first sync, Multi-tenant isolation, and Reporting engine.
- **Dependency:** Completion of the database schema and API contracts.
- **Activity:** Daily sprints with JIRA tracking.

### Phase 3: Hardening & Launch (Months 5-6)
- **Focus:** 2FA integration, RBAC finalization, and PCI DSS certification.
- **Dependency:** Successful E2E test runs in Staging.
- **Key Date:** **Milestone 2: Production launch (2026-10-15).**

### Phase 4: Post-Launch Iteration (Post-Launch)
- **Focus:** Pilot user feedback and feature adoption tracking.
- **Key Date:** **Milestone 3: Internal alpha release (2026-12-15)** (This represents the v2.0 "Alpha" for new feature sets).

---

## 10. Meeting Notes

**Meeting 1: Kickoff / Architecture Alignment**
*Date: 2025-11-01*
*Attendees: Emeka Nakamura, Farah Costa, Beatriz Costa*
- MFE decided. 
- Django for backend.
- Postgres RLS discussed.
- Budget $800k approved.
- Focus on "catastrophic" feedback from v1.

**Meeting 2: Sync & Offline Mode Technicals**
*Date: 2025-11-15*
*Attendees: Emeka Nakamura, Solo Dev, Amira Fischer*
- IndexedDB for cache.
- Background sync API.
- Conflict resolution: Last-Write-Wins.
- Blocked by API limits.
- Need workaround for testing.

**Meeting 3: PCI DSS & Security Review**
*Date: 2025-12-05*
*Attendees: Emeka Nakamura, Solo Dev, Farah Costa*
- Hardware keys required.
- WebAuthn vs TOTP.
- Stripe integration for payments.
- RLS policies in review.
- Sponsor rotation risk mentioned.

---

## 11. Budget Breakdown

**Total Budget:** $800,000

| Category | Allocation | Amount | Justification |
| :--- | :--- | :--- | :--- |
| **Personnel** | 70% | $560,000 | Solo developer salary + Project Lead/Design/Eng overhead. |
| **Infrastructure** | 15% | $120,000 | AWS ECS, RDS, Redis, S3, and WAF costs for 1 year. |
| **Tools & Licenses** | 5% | $40,000 | GitHub Enterprise, Sentry, Datadog, Stripe Fees. |
| **Contingency** | 10% | $80,000 | Buffer for API overages or unexpected security audit costs. |

---

## 12. Appendices

### Appendix A: PCI DSS Compliance Checklist
To maintain Level 1 compliance, Project Eclipse adheres to the following:
1. **Encryption:** All data in transit uses TLS 1.3. Data at rest is encrypted using AES-256.
2. **Access Control:** RBAC is enforced; no shared accounts.
3. **Network Segregation:** The production ECS cluster is in a private subnet; only the ALB is public-facing.
4. **Logging:** All access to the cardholder data environment (CDE) is logged and sent to a write-once storage bucket.

### Appendix B: Technical Debt Management Protocol
To prevent the "legacy mess" that led to the rebuild of Eclipse, the following protocol is enforced:
1. **Debt Identification:** Any "hack" or temporary workaround is tagged in JIRA as `TECH-DEBT`.
2. **Sprint Allocation:** 20% of every sprint's velocity is dedicated to resolving `TECH-DEBT` tickets.
3. **Refactor Trigger:** If a module's complexity score (Cyclomatic Complexity) exceeds 15, a mandatory refactor is triggered before any new features are added to that module.