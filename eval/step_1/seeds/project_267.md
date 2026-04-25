# Project Specification: Harbinger
**Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2025  
**Company:** Duskfall Inc.  
**Project Lead:** Yonas Costa  

---

## 1. Executive Summary

### 1.1 Project Overview
Harbinger is a greenfield real-time collaboration tool specifically engineered for the media and entertainment industry. Developed by Duskfall Inc., this product represents a strategic pivot for the company, entering a market segment where it has no prior operational history. The goal is to provide a high-performance environment where creative professionals (editors, scriptwriters, and producers) can collaborate on complex assets in real-time without the latency or versioning conflicts typical of legacy media tools.

### 1.2 Business Justification
The media and entertainment sector is currently undergoing a transition toward decentralized, remote production. Existing tools are either general-purpose (Google Docs, Notion) and lack the specialized needs of media workflows, or are high-end enterprise suites that are prohibitively expensive for mid-sized production houses. Harbinger aims to occupy the "mid-tier professional" gap. By offering a tool that balances high-end real-time synchronization with streamlined billing and industry-standard security (GDPR/CCPA), Duskfall Inc. can establish a beachhead in a high-growth vertical.

### 1.3 ROI Projection
Given the "shoestring" budget of $150,000, the project is designed for high capital efficiency. The projected Return on Investment (ROI) is based on a SaaS subscription model. 

*   **Target Customer Acquisition:** 50 boutique production houses in Year 1.
*   **Projected ARPU (Average Revenue Per User):** $45/month.
*   **Break-even Point:** Estimated at 14 months post-launch, assuming a churn rate of <5%.
*   **Strategic Value:** Beyond direct revenue, Harbinger serves as a R&D vehicle for Duskfall Inc. to master real-time synchronization technologies, which can be leveraged across other company product lines.

### 1.4 Constraints and Strategic Approach
The project is constrained by a tight budget and a small, remote-first team. To mitigate these risks, the team is employing a disciplined micro-frontend architecture to allow independent ownership and a quarterly release cycle to align with rigorous regulatory reviews. Success is defined not by feature density, but by absolute stability (99.9% uptime) and security (zero critical incidents).

---

## 2. Technical Architecture

### 2.1 System Overview
Harbinger utilizes a decoupled architecture designed for scalability and regulatory compliance. The backend is powered by Python/Django, leveraging PostgreSQL for relational data and Redis for real-time state management and caching. The frontend is implemented as a micro-frontend architecture, allowing the team to deploy specific modules (e.g., the Editor, the Billing Dashboard, the Search Interface) independently.

### 2.2 Architecture Diagram (ASCII Description)
```text
[ User Browser / Client ]
       |
       v
[ AWS CloudFront (CDN) ] ----> [ S3 Bucket (Static Assets) ]
       |
       v
[ AWS Application Load Balancer ]
       |
       +---------------------------------------+
       |                                       |
[ ECS Cluster (Django API) ] <---> [ Redis (Pub/Sub & Cache) ]
       |                                       |
       +---------------------------------------+
       |                                       |
[ PostgreSQL (RDS - EU Region) ] <--- [ Data Residency Boundary ]
       |
       v
[ External Integrations ] (SAML Providers / Stripe / Search Index)
```

### 2.3 Technology Stack Details
*   **Backend:** Python 3.11 / Django 4.2 (REST Framework).
*   **Frontend:** React 18 with a Module Federation approach for micro-frontends.
*   **Database:** PostgreSQL 15 (Amazon RDS) with Multi-AZ deployment for high availability.
*   **Caching/Real-time:** Redis 7.0 for WebSocket message brokering and session storage.
*   **Infrastructure:** AWS ECS (Fargate) for serverless container orchestration.
*   **Deployment:** Dockerized containers managed via GitHub Actions CI/CD.

### 2.4 Data Residency and Security
To comply with GDPR and CCPA, all primary data stores and backups are restricted to the `eu-central-1` (Frankfurt) region. No PII (Personally Identifiable Information) is permitted to leave the EU boundary. Encryption at rest is handled via AWS KMS, and encryption in transit is enforced via TLS 1.3.

---

## 3. Detailed Feature Specifications

### 3.1 SSO Integration (SAML and OIDC)
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:**
To enter the enterprise media market, Harbinger must support Single Sign-On (SSO). Users must be able to authenticate using their corporate identity providers (IdPs) via SAML 2.0 and OpenID Connect (OIDC).

**Functional Requirements:**
1.  **Multi-Provider Support:** The system must support multiple concurrent IdPs (e.g., Okta, Azure AD, Google Workspace).
2.  **Just-In-Time (JIT) Provisioning:** Users should be automatically created in the Harbinger database upon their first successful SSO login, provided they belong to a recognized corporate domain.
3.  **Attribute Mapping:** The system must map SAML assertions (email, first_name, last_name, group_membership) to internal User profiles.
4.  **Session Management:** Implementation of secure JWT (JSON Web Tokens) for session maintenance, with refresh tokens stored in secure, HttpOnly cookies.
5.  **Fallback Authentication:** A limited "Emergency Admin" local login must exist for the initial setup of the SSO configuration.

**Technical Implementation:**
The integration will use `django-auth-adfs` and `python3-saml`. The flow involves a service provider (SP) initiated request where Harbinger redirects the user to the IdP. Upon successful authentication, the IdP posts a SAML response to the `/auth/sso/acs` endpoint.

---

### 3.2 A/B Testing Framework (Feature Flag System)
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Given the "greenfield" nature of the project, Duskfall Inc. requires a data-driven approach to feature rollout. This system allows the team to toggle features on/off and split-test different UX implementations without deploying new code.

**Functional Requirements:**
1.  **Dynamic Toggling:** Ability to enable/disable features for specific user IDs, groups, or percentages of the total population.
2.  **Experiment Definition:** Admins can define an "Experiment" with a control group (A) and a treatment group (B).
3.  **Metric Tracking:** Integration with the analytics layer to track which group converts better on specific KPIs (e.g., "Time to first edit").
4.  **Persistence:** A user's assignment to a group (A or B) must be persistent across sessions to avoid UX flickering.
5.  **Automatic Cleanup:** A system of "stale flag" alerts to ensure that once an A/B test is concluded, the losing code path is removed.

**Technical Implementation:**
Feature flags will be stored in Redis for sub-millisecond lookup. A middleware layer in Django will evaluate the user's context and inject the active flag set into the request object. Frontend micro-frontends will query the `/api/v1/flags` endpoint on initialization.

---

### 3.3 Automated Billing and Subscription Management
**Priority:** Critical (Launch Blocker) | **Status:** In Design

**Description:**
A fully automated pipeline for handling subscriptions, invoicing, and payment failures to ensure no manual intervention is required for revenue collection.

**Functional Requirements:**
1.  **Tiered Pricing:** Support for "Starter," "Professional," and "Enterprise" tiers.
2.  **Prorated Upgrades:** If a user upgrades mid-month, the system must calculate the remaining value of the current plan and apply it as a credit to the new plan.
3.  **Dunning Process:** Automated email sequence for failed payments (1st fail, 3rd fail, 7th fail) before account suspension.
4.  **Tax Compliance:** Integration with a tax engine (e.g., Stripe Tax) to handle VAT in the EU and Sales Tax in the US.
5.  **Self-Service Portal:** Users must be able to update credit cards, download PDF invoices, and cancel subscriptions via the UI.

**Technical Implementation:**
Integration with Stripe as the primary payment gateway. Use of Stripe Webhooks to synchronize payment status with the internal `Subscription` table in PostgreSQL.

---

### 3.4 Real-time Collaborative Editing (Conflict Resolution)
**Priority:** Medium | **Status:** In Review

**Description:**
The core value proposition of Harbinger is the ability for multiple users to edit a document simultaneously without overwriting each other's work.

**Functional Requirements:**
1.  **Low Latency Sync:** Changes must be reflected across all clients in <100ms.
2.  **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to ensure eventual consistency.
3.  **Presence Indicators:** Visual cues (cursors, highlighted names) showing where other users are currently editing.
4.  **Version History:** A linear timeline of changes allowing users to revert to a specific state.
5.  **Offline Mode:** Basic local caching of changes that are synced upon reconnection.

**Technical Implementation:**
WebSockets via Django Channels will be used for the transport layer. Redis will act as the backplane for broadcasting messages. For conflict resolution, Yjs (a CRDT implementation) will be utilized on the frontend and synced to the backend via a specialized WebSocket handler.

---

### 3.5 Advanced Search (Faceted Filtering & Full-Text Indexing)
**Priority:** Medium | **Status:** Blocked

**Description:**
Users need to find specific assets, scripts, or collaborators across thousands of projects using complex filters.

**Functional Requirements:**
1.  **Full-Text Search:** Support for fuzzy matching and stemming (e.g., searching for "editing" finds "editor").
2.  **Faceted Filtering:** Ability to filter by date, project owner, asset type, and tag.
3.  **Instant Suggestions:** A "search-as-you-type" dropdown providing the most likely matches.
4.  **Permission-Aware Results:** Users must only see search results for documents they have permission to access.
5.  **Index Synchronization:** The search index must be updated in near real-time as documents are created or edited.

**Technical Implementation:**
Implementation of PostgreSQL Full Text Search (FTS) using GIN indexes for the MVP. If performance degrades, the path is outlined to migrate to Elasticsearch. Currently blocked by the delay in infrastructure provisioning of the dedicated search cluster.

---

## 4. API Endpoint Documentation

All endpoints are prefixed with `/api/v1/` and require a Bearer Token in the Authorization header.

### 4.1 Authentication & SSO
**Endpoint:** `POST /auth/sso/login`
*   **Description:** Initiates the SSO handshake.
*   **Request:** `{ "provider": "okta", "tenant_id": "duskfall-prod-01" }`
*   **Response:** `200 OK { "redirect_url": "https://okta.com/auth/..." }`

**Endpoint:** `POST /auth/sso/acs`
*   **Description:** Assertion Consumer Service endpoint for SAML responses.
*   **Request:** `SAMLResponse` (XML encoded)
*   **Response:** `200 OK { "token": "jwt_token_here", "user": { "id": 123, "email": "user@company.com" } }`

### 4.2 Collaboration & Documents
**Endpoint:** `GET /docs/{doc_id}`
*   **Description:** Retrieve document metadata and current state.
*   **Request:** Header `Authorization: Bearer <token>`
*   **Response:** `200 OK { "id": "doc_1", "title": "Scene 1 Script", "content": "...", "version": 45 }`

**Endpoint:** `PATCH /docs/{doc_id}`
*   **Description:** Update document properties.
*   **Request:** `{ "title": "Revised Scene 1" }`
*   **Response:** `200 OK { "status": "updated" }`

### 4.3 Feature Flags & A/B Testing
**Endpoint:** `GET /flags`
*   **Description:** Retrieve all active feature flags for the current user.
*   **Response:** `200 OK { "flags": { "new_editor_ui": true, "beta_search": false, "ab_test_group": "B" } }`

### 4.4 Billing & Subscription
**Endpoint:** `GET /billing/subscription`
*   **Description:** Check current subscription status.
*   **Response:** `200 OK { "plan": "Professional", "status": "active", "next_billing_date": "2026-01-15" }`

**Endpoint:** `POST /billing/upgrade`
*   **Description:** Trigger a plan upgrade.
*   **Request:** `{ "new_plan_id": "plan_ent_001" }`
*   **Response:** `201 Created { "invoice_url": "https://stripe.com/inv_..." }`

### 4.5 Search
**Endpoint:** `GET /search`
*   **Description:** Faceted search for assets.
*   **Request:** `?q=script&filter[type]=pdf&filter[date]=2025`
*   **Response:** `200 OK { "results": [...], "facets": { "type": { "pdf": 10, "docx": 5 } } }`

---

## 5. Database Schema

The system uses a relational schema in PostgreSQL. All tables utilize UUIDs as primary keys for security and distributed compatibility.

### 5.1 Table Definitions

1.  **`users`**
    *   `id`: UUID (PK)
    *   `email`: VARCHAR(255) (Unique)
    *   `full_name`: VARCHAR(255)
    *   `sso_provider`: VARCHAR(50)
    *   `created_at`: TIMESTAMP
2.  **`organizations`**
    *   `id`: UUID (PK)
    *   `org_name`: VARCHAR(255)
    *   `domain`: VARCHAR(255)
    *   `billing_email`: VARCHAR(255)
3.  **`organization_members`**
    *   `org_id`: UUID (FK $\rightarrow$ organizations.id)
    *   `user_id`: UUID (FK $\rightarrow$ users.id)
    *   `role`: VARCHAR(20) (Owner, Admin, Editor, Viewer)
4.  **`documents`**
    *   `id`: UUID (PK)
    *   `org_id`: UUID (FK $\rightarrow$ organizations.id)
    *   `title`: VARCHAR(255)
    *   `content`: TEXT (or JSONB for CRDT state)
    *   `created_by`: UUID (FK $\rightarrow$ users.id)
    *   `updated_at`: TIMESTAMP
5.  **`document_versions`**
    *   `id`: UUID (PK)
    *   `doc_id`: UUID (FK $\rightarrow$ documents.id)
    *   `snapshot`: TEXT
    *   `version_num`: INTEGER
    *   `created_at`: TIMESTAMP
6.  **`subscriptions`**
    *   `id`: UUID (PK)
    *   `org_id`: UUID (FK $\rightarrow$ organizations.id)
    *   `stripe_sub_id`: VARCHAR(255)
    *   `plan_tier`: VARCHAR(50)
    *   `status`: VARCHAR(20) (Active, Past_Due, Canceled)
7.  **`invoices`**
    *   `id`: UUID (PK)
    *   `sub_id`: UUID (FK $\rightarrow$ subscriptions.id)
    *   `amount`: DECIMAL(10,2)
    *   `pdf_url`: TEXT
    *   `paid_at`: TIMESTAMP
8.  **`feature_flags`**
    *   `flag_key`: VARCHAR(100) (PK)
    *   `is_enabled`: BOOLEAN
    *   `rollout_percentage`: INTEGER
    *   `description`: TEXT
9.  **`user_flag_overrides`**
    *   `user_id`: UUID (FK $\rightarrow$ users.id)
    *   `flag_key`: VARCHAR(100) (FK $\rightarrow$ feature_flags.flag_key)
    *   `value`: BOOLEAN
10. **`audit_logs`**
    *   `id`: UUID (PK)
    *   `user_id`: UUID (FK $\rightarrow$ users.id)
    *   `action`: VARCHAR(100)
    *   `timestamp`: TIMESTAMP
    *   `ip_address`: VARCHAR(45)

### 5.2 Relationships
*   **One-to-Many:** `organizations` $\rightarrow$ `organization_members` $\rightarrow$ `users`.
*   **One-to-Many:** `organizations` $\rightarrow$ `documents`.
*   **One-to-Many:** `documents` $\rightarrow$ `document_versions`.
*   **One-to-One:** `organizations` $\rightarrow$ `subscriptions`.
*   **One-to-Many:** `subscriptions` $\rightarrow$ `invoices`.

---

## 6. Deployment and Infrastructure

### 6.1 Environment Strategy
Harbinger maintains three distinct environments to ensure stability and regulatory compliance.

| Environment | Purpose | Deployment Trigger | Data Source |
| :--- | :--- | :--- | :--- |
| **Dev** | Feature development | Merge to `develop` branch | Mock/Anonymized Data |
| **Staging** | Pre-release QA & UAT | Merge to `release` branch | Sanitized Prod Copy |
| **Prod** | Live customer traffic | Manual trigger (Quarterly) | Live EU Production Data |

### 6.2 Infrastructure Details
*   **Compute:** AWS ECS Fargate. We utilize a "Cluster per Environment" model.
*   **Networking:** VPC with private subnets for the application and database layers. A public ALB (Application Load Balancer) handles incoming HTTPS traffic.
*   **Storage:** Amazon S3 for static asset hosting and PostgreSQL RDS for relational data.
*   **Scaling:** Auto-scaling is configured based on CPU utilization (threshold 70%), though limited by the fixed budget.

### 6.3 Deployment Cycle
Releases are conducted **quarterly**. This is a mandatory constraint to allow for regulatory review cycles and security audits required by the media industry's enterprise clients. Each release follows a "Freeze $\rightarrow$ Audit $\rightarrow$ Deploy" cadence.

---

## 7. Testing Strategy

### 7.1 Unit Testing
*   **Scope:** Every Django view, model method, and frontend component.
*   **Tooling:** `pytest` for Python, `Jest` for React.
*   **Requirement:** 80% minimum code coverage. Unit tests must be passed in the CI pipeline before any merge to `develop`.

### 7.2 Integration Testing
*   **Scope:** API endpoint chains and database transactions.
*   **Approach:** Testing the interaction between the Django API and the PostgreSQL/Redis layers.
*   **Critical Path:** SSO flow (mocking SAML responses), Subscription lifecycle (mocking Stripe webhooks).

### 7.3 End-to-End (E2E) Testing
*   **Scope:** Critical user journeys (e.g., "Login $\rightarrow$ Create Doc $\rightarrow$ Edit $\rightarrow$ Save").
*   **Tooling:** Playwright.
*   **Execution:** Run on the Staging environment prior to every quarterly release.

### 7.4 Performance Testing
*   **Scope:** Real-time sync latency and search response times.
*   **Benchmark:** 10x current system capacity (as per risk assessment).
*   **Tooling:** Locust.io for load simulation.

---

## 8. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Integration partner API is undocumented/buggy | High | Medium | Accept the risk; monitor weekly via integration logs. |
| **R-02** | Performance reqs are 10x current capacity | Medium | High | De-scope affected features if unresolved by Milestone 3. |
| **R-03** | Infrastructure provisioning delay | High | Medium | Use local Docker-compose for dev until cloud provider resolves. |
| **R-04** | Budget exhaustion ($150k limit) | Medium | Critical | Strict scrutiny of every dollar; prioritize "Launch Blockers" only. |
| **R-05** | EU Data Residency breach | Low | Critical | Automated region-locking in AWS IAM and RDS policies. |

### 8.1 Probability/Impact Matrix
*   **Critical:** High Impact + Medium/High Probability (Requires immediate action).
*   **Major:** High Impact + Low Probability (Requires contingency plan).
*   **Minor:** Low Impact + Any Probability (Monitored).

---

## 9. Timeline and Milestones

### 9.1 Project Phases
1.  **Phase 1: Foundation (Oct 2025 - Jan 2026)**
    *   Infrastructure setup, Base API, SSO Design.
2.  **Phase 2: Core Collaboration (Feb 2026 - May 2026)**
    *   CRDT Implementation, Real-time sync, Feature Flag system.
3.  **Phase 3: Enterprise Readiness (Jun 2026 - Sep 2026)**
    *   Billing integration, Security Audits, Search indexing.
4.  **Phase 4: Launch Hardening (Oct 2026 - Nov 2026)**
    *   Load testing, Final UAT, Regulatory sign-off.

### 9.2 Key Milestones
*   **Milestone 1: Stakeholder demo and sign-off**
    *   **Target Date:** 2026-07-15
    *   **Dependency:** Completion of SSO and Basic Editor.
*   **Milestone 2: Security audit passed**
    *   **Target Date:** 2026-09-15
    *   **Dependency:** Completion of GDPR/CCPA data residency checks.
*   **Milestone 3: MVP feature-complete**
    *   **Target Date:** 2026-11-15
    *   **Dependency:** Billing system and A/B framework operational.

---

## 10. Meeting Notes

### Meeting 1: Architecture Kickoff (2025-10-15)
*   **Attendees:** Yonas, Anders, Fleur, Dayo
*   **Notes:**
    *   Micro-frontends confirmed.
    *   Yonas: "Budget is tight, no gold-plating."
    *   Anders: "SAML is a pain, need library."
    *   Fleur: "EU users need clear data deletion UI."
    *   Decision: Use AWS ECS Fargate for simplicity.

### Meeting 2: Feature Prioritization (2025-11-02)
*   **Attendees:** Yonas, Anders, Fleur, Dayo
*   **Notes:**
    *   Search is blocked. Infrastructure lag.
    *   Billing is a "must-have" for launch.
    *   A/B testing needs to be baked in, not added later.
    *   Dayo: "CRDTs are complex, need more time."
    *   Decision: Move Search to 'Medium' priority; SSO/Billing remain 'Critical'.

### Meeting 3: Risk Review (2025-12-10)
*   **Attendees:** Yonas, Anders, Fleur, Dayo
*   **Notes:**
    *   Partner API is a mess.
    *   Yonas: "We can't fix their API. Just log errors and move on."
    *   Performance check: 10x load is worrying.
    *   Fleur: "User testing shows confusion on billing tiers."
    *   Decision: Accept partner API risk; monitor weekly.

---

## 11. Budget Breakdown

The total budget is **$150,000**. Every expenditure must be approved by Yonas Costa.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $110,000 | 4-person team (Contract/Internal split) |
| **Infrastructure** | $20,000 | AWS ECS, RDS (EU), Redis, S3, CloudFront |
| **Tools & Licenses** | $10,000 | Stripe Fees, SAML Libraries, Github Enterprise |
| **Contingency** | $10,000 | Emergency bug fixes, audit overages |
| **Total** | **$150,000** | |

---

## 12. Appendices

### Appendix A: Conflict Resolution Logic (CRDT)
To ensure real-time consistency, Harbinger uses a LWW-Element-Set (Last-Write-Wins) approach for simple properties and a Sequence CRDT for text editing. Each character in a document is assigned a unique identifier consisting of a `(client_id, counter)` pair. This ensures that regardless of the order in which edits arrive at the server, all clients converge to the same state.

### Appendix B: Regulatory Compliance Matrix

| Requirement | Harbinger Implementation | Verification Method |
| :--- | :--- | :--- |
| **Right to be Forgotten** | User deletion trigger $\rightarrow$ Cascade delete in DB | DB Audit Log |
| **Data Residency** | AWS `eu-central-1` only | Infrastructure as Code (Terraform) |
| **Access Control** | Role-Based Access Control (RBAC) via `organization_members` | Unit Tests |
| **Data Encryption** | AES-256 at rest; TLS 1.3 in transit | AWS KMS Config |