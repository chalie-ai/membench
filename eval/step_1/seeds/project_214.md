Due to the extreme length requirements of this request, this document is presented as a comprehensive, professional Project Specification Document (PSD). 

***

# PROJECT SPECIFICATION: LATTICE
**Version:** 1.0.4  
**Date:** October 24, 2024  
**Status:** Active/Draft  
**Company:** Duskfall Inc.  
**Confidentiality:** Level 4 (Strictly Confidential)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Overview
Project "Lattice" is a high-stakes strategic initiative by Duskfall Inc. While Duskfall Inc. operates primarily within the media and entertainment industry, Lattice represents a strategic pivot and partnership integration aimed at digitizing and managing healthcare records for high-net-worth individuals, talent, and production cast/crew members. This platform is designed to bridge the gap between entertainment industry logistics (insurance, medical clearances for stunts/filming) and formal healthcare record management.

The platform is designed as a strategic partnership integration. The core value proposition relies on the seamless synchronization of internal healthcare data with an external partner’s proprietary API. Because this integration is tied to the external company’s release timeline, Lattice must be architected for flexibility to accommodate shifting API endpoints and data schemas.

### 1.2 Business Justification
The entertainment industry currently relies on fragmented, antiquated systems for managing health clearances, medical waivers, and on-set health records. The "Lattice" platform centralizes these records, ensuring PCI DSS Level 1 compliance for the processing of medical insurance premiums and direct payment of healthcare services via integrated credit card processing. By streamlining this process, Duskfall Inc. intends to capture a niche market of "production-integrated healthcare," reducing the administrative overhead for studio productions by an estimated 40%.

### 1.3 ROI Projection
The budget for Lattice is set at $800,000 for a 6-month development cycle. The projected Return on Investment (ROI) is based on two primary levers:
1. **Transaction Cost Reduction:** A target reduction of 35% in cost per transaction compared to the legacy manual system, saving approximately $120,000 per annum in operational overhead.
2. **Market Penetration:** By onboarding the first paying customer by June 15, 2025, Duskfall Inc. expects a Year 1 Recurring Revenue (ARR) of $450,000.

The ROI is calculated as: 
$[(Expected Revenue - Development Cost) / Development Cost] \times 100$
Given the strategic nature of the partnership, the long-term value is estimated at $2.2M over three years, primarily driven by the ability to scale the platform across multiple production houses.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Stack Overview
Lattice utilizes a modern, high-concurrency stack designed for real-time updates and strict data integrity.
- **Language/Framework:** Elixir / Phoenix (chosen for its fault tolerance and concurrency).
- **Frontend:** Phoenix LiveView (for real-time, server-rendered interactive UIs).
- **Database:** PostgreSQL (Relational storage with JSONB for flexible record schemas).
- **Infrastructure:** Fly.io (Global distribution, simplifying the deployment of Elixir nodes).
- **Compliance:** PCI DSS Level 1 (Mandatory for direct credit card processing).

### 2.2 Architectural Pattern: The Incremental Monolith
The system is currently architected as a **Modular Monolith**. To prevent "distributed monolith" syndrome, the team is utilizing Elixir's umbrella project structure. This allows for clear boundaries between the `Accounts`, `Records`, `Billing`, and `Integration` modules. 

As the platform scales, these modules will transition into standalone microservices. The transition will be triggered when any single module exceeds 10,000 concurrent requests per second or requires a distinct scaling profile.

### 2.3 ASCII System Diagram
```text
[ User Browser ] <--- WebSocket (LiveView) ---> [ Fly.io Edge Node ]
                                                        |
                                                        v
                                            [ Phoenix Application Server ]
                                            /           |             \
                    _______________________/            |              \_______________________
                   |                                    |                                    |
        [ Auth/PCI Module ]                    [ Business Logic Layer ]                [ Integration Engine ]
                   |                                    |                                    |
         (PCI DSS Vault)                      (PostgreSQL Database)               (External Partner API)
                   |                                    |                                    |
                   \____________________________________|___________________________________/
                                                        |
                                               [ Fly.io Shared Volume ]
                                               (Encrypted PDF/CSV Storage)
```

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Advanced Search with Faceted Filtering (Priority: Critical)
**Status:** Blocked (Infrastructure Provisioning)
**Description:** 
The search system must allow healthcare administrators to query millions of records across multiple dimensions (patient name, DOB, medical code, production ID, insurance provider). 

**Functional Requirements:**
- **Full-Text Indexing:** Implementation of PostgreSQL `tsvector` and `tsquery` for lightning-fast keyword searches across medical notes.
- **Faceted Filtering:** A sidebar interface allowing users to drill down by category (e.g., "Blood Type: O+", "Status: Active," "Production: Project X").
- **Indexing Strategy:** The system must support asynchronous indexing. When a record is updated, a background job (via Oban) must refresh the search index to prevent UI lag.
- **Performance Target:** Search results must return in < 200ms for queries across 1 million records.

**Technical Constraints:**
The "Blocked" status is due to the current delay in cloud provider provisioning for the elastic search clusters. Until resolved, the team is using a mocked local PostgreSQL index, which does not support the required faceted logic at scale.

### 3.2 Real-time Collaborative Editing with Conflict Resolution (Priority: Critical)
**Status:** Blocked (Tech Stack Learning Curve)
**Description:** 
Medical records are often updated by multiple practitioners simultaneously. Lattice requires a "Google Docs-style" editing experience where changes are reflected in real-time.

**Functional Requirements:**
- **Operational Transformation (OT) / CRDT:** The system must implement Conflict-free Replicated Data Types (CRDTs) to ensure that if two doctors edit the same patient record, the state eventually converges without data loss.
- **Presence Tracking:** Using Phoenix Presence, users must see who else is currently viewing or editing a record.
- **Locking Mechanism:** For critical fields (e.g., Medication Dosage), a pessimistic locking mechanism must be implemented to prevent simultaneous edits.

**Technical Constraints:**
The team has no prior experience with CRDTs in Elixir. The current mitigation is intensive documentation of workarounds and a "learning sprint" where the team shares implementation patterns.

### 3.3 File Upload with Virus Scanning and CDN Distribution (Priority: High)
**Status:** In Review
**Description:** 
Users must upload medical PDFs, X-rays, and insurance documents. These files must be scanned for malware before being stored.

**Functional Requirements:**
- **Upload Pipeline:** File $\rightarrow$ Temporary S3 Bucket $\rightarrow$ ClamAV Scanning Service $\rightarrow$ Permanent S3 Bucket.
- **CDN Integration:** Files must be served via a CDN (Cloudflare) to ensure low latency for global production crews.
- **Encryption:** All files must be encrypted at rest using AES-256.
- **Virus Scanning:** Integration with a third-party scanning API. If a virus is detected, the file is quarantined, and an alert is triggered to the security lead.

### 3.4 PDF/CSV Report Generation with Scheduled Delivery (Priority: Medium)
**Status:** Complete
**Description:** 
The ability to generate aggregate healthcare reports for production insurance audits.

**Functional Requirements:**
- **Templating:** Use of a LaTeX or HTML-to-PDF engine to create standardized medical summaries.
- **CSV Export:** Ability to export raw patient data for external audit analysis.
- **Scheduling:** A Cron-based system (via Oban) that allows admins to schedule weekly or monthly reports to be emailed to stakeholders.
- **Delivery:** Integration with SendGrid for email delivery and AWS S3 for report archiving.

### 3.5 Notification System (Priority: Medium)
**Status:** Not Started
**Description:** 
A multi-channel alert system to notify users of critical health updates or system alerts.

**Functional Requirements:**
- **In-App Notifications:** A LiveView-based notification bell with real-time updates.
- **Email:** Transactional emails for password resets and record updates.
- **SMS:** Integration with Twilio for urgent medical alerts.
- **Push:** Web-push notifications for browser-based alerts.
- **Preference Center:** Users must be able to toggle which channels they receive for specific types of alerts.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are versioned (`/v1`) and require a Bearer Token for authentication.

### 4.1 Authentication
- **POST `/v1/auth/login`**
  - *Request:* `{ "email": "user@duskfall.com", "password": "..." }`
  - *Response:* `{ "token": "jwt_token_here", "expires_at": "2025-10-25T00:00:00Z" }`

### 4.2 Patient Records
- **GET `/v1/records`**
  - *Query Params:* `q=search_term`, `facet=blood_type:O+`
  - *Response:* `[{ "id": "rec_123", "patient_name": "John Doe", "summary": "Stable" }]`
- **POST `/v1/records`**
  - *Request:* `{ "patient_id": "pat_456", "data": { "bp": "120/80" } }`
  - *Response:* `{ "id": "rec_123", "status": "created" }`
- **PATCH `/v1/records/:id`**
  - *Request:* `{ "data": { "bp": "110/70" } }`
  - *Response:* `{ "id": "rec_123", "version": 2 }`

### 4.3 Billing (PCI DSS Compliant)
- **POST `/v1/billing/payment-method`**
  - *Request:* `{ "token": "stripe_token", "last4": "4242" }`
  - *Response:* `{ "status": "success", "method_id": "pm_987" }`
- **POST `/v1/billing/charge`**
  - *Request:* `{ "amount": 5000, "currency": "usd", "method_id": "pm_987" }`
  - *Response:* `{ "transaction_id": "tx_555", "status": "captured" }`

### 4.4 Reporting
- **GET `/v1/reports/generate`**
  - *Query Params:* `type=csv`, `start_date=2025-01-01`
  - *Response:* `{ "job_id": "job_001", "status": "processing" }`
- **GET `/v1/reports/download/:job_id`**
  - *Response:* Binary stream (PDF/CSV file)

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL 15.

### 5.1 Table Definitions

| Table Name | Key Fields | Relationships | Description |
| :--- | :--- | :--- | :--- |
| `users` | `id (UUID)`, `email`, `password_hash`, `role` | 1:N $\rightarrow$ `records` | User accounts and roles. |
| `patients` | `id (UUID)`, `full_name`, `dob`, `ssn_encrypted` | 1:N $\rightarrow$ `medical_records` | Patient demographic data. |
| `medical_records` | `id (UUID)`, `patient_id`, `content (JSONB)`, `version` | N:1 $\rightarrow$ `patients` | The core health record data. |
| `audit_logs` | `id (UUID)`, `user_id`, `action`, `timestamp` | N:1 $\rightarrow$ `users` | PCI DSS required audit trail. |
| `billing_profiles` | `id (UUID)`, `user_id`, `stripe_cust_id` | 1:1 $\rightarrow$ `users` | Payment profiles. |
| `transactions` | `id (UUID)`, `profile_id`, `amount`, `status` | N:1 $\rightarrow$ `billing_profiles` | Payment history. |
| `files` | `id (UUID)`, `uploader_id`, `s3_path`, `checksum` | N:1 $\rightarrow$ `users` | Metadata for uploaded files. |
| `virus_scans` | `id (UUID)`, `file_id`, `result`, `scanned_at` | 1:1 $\rightarrow$ `files` | Security scan results. |
| `notifications` | `id (UUID)`, `user_id`, `message`, `read_at` | N:1 $\rightarrow$ `users` | In-app alert records. |
| `partner_sync_logs` | `id (UUID)`, `external_id`, `sync_status`, `error` | N/A | Sync history with external API. |

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Lattice employs three distinct environments to ensure stability and security.

1. **Development (Dev):**
   - **Purpose:** Daily iteration and feature development.
   - **Access:** All 4 team members.
   - **Data:** Seeded with anonymized dummy data.
   - **Deployment:** Continuous integration (CI) on every push to `develop` branch.

2. **Staging (QA):**
   - **Purpose:** Final verification before production.
   - **Access:** Project Lead and QA.
   - **Data:** Mirror of production (scrubbed of PII).
   - **Deployment:** Manual trigger from `develop` to `staging`.

3. **Production (Prod):**
   - **Purpose:** Live customer traffic.
   - **Access:** Luna Costa (CTO) only.
   - **Data:** Live, encrypted healthcare and billing data.
   - **Deployment:** **Manual QA Gate.** Every release requires a sign-off from the Project Lead. The turnaround for a deployment is 2 business days to allow for rigorous regression testing.

### 6.2 Infrastructure Provisioning
Currently, the team is facing a **current blocker**: infrastructure provisioning has been delayed by the cloud provider (Fly.io region expansion). This has halted the deployment of the search cluster and the real-time WebSocket nodes.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
- **Tool:** ExUnit.
- **Requirement:** 80% coverage of business logic in the `Accounts` and `Billing` modules.
- **Focus:** Pure functions, data transformation, and API request validation.

### 7.2 Integration Testing
- **Tool:** Wallaby.js / Phoenix Integration Tests.
- **Requirement:** Every API endpoint must have a corresponding integration test that verifies the request-response cycle.
- **Focus:** Database transactions and external API mock responses.

### 7.3 End-to-End (E2E) Testing
- **Tool:** Playwright.
- **Requirement:** Critical user journeys (e.g., "Patient Onboarding," "Payment Processing") must be automated.
- **Focus:** LiveView state transitions and UI responsiveness across different browsers.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Key architect leaving in 3 months | High | High | Hire a specialized contractor immediately to reduce the "bus factor" and document system architecture. |
| R-02 | Team lack of experience with Elixir/Phoenix | High | Medium | Implement a "knowledge share" protocol; document all workarounds in the shared internal wiki. |
| R-03 | Cloud provider provisioning delay | Medium | High | Diversify infrastructure providers if the delay exceeds 14 days. |
| R-04 | PCI DSS Compliance failure | Low | Critical | Conduct quarterly external audits and use a dedicated security consultant. |
| R-05 | API timeline shifts from partner | High | Medium | Implement a "version-agnostic" adapter layer in the Integration Engine. |

**Impact Matrix:**
- High Probability $\times$ High Impact $\rightarrow$ Immediate Action Required.
- Low Probability $\times$ Critical Impact $\rightarrow$ Monitoring & Contingency Planning.

---

## 9. TIMELINE & GANTT DESCRIPTION

The project is a 6-month build starting from October 2024.

**Phase 1: Foundation & Core API (Oct 2024 - Dec 2024)**
- Setup Elixir project and Fly.io base.
- Implement basic Auth and Patient Record CRUD.
- *Dependency:* Cloud provider provisioning.

**Phase 2: Integration & Security (Jan 2025 - Mar 2025)**
- Build the external partner API sync engine.
- Implement PCI DSS Level 1 payment flows.
- *Dependency:* Partner API documentation release.

**Phase 3: Advanced Features & Optimization (Mar 2025 - May 2025)**
- Resolve Search and Collaborative Editing blockers.
- Implement File Upload and Virus Scanning.
- Internal Alpha testing.

**Phase 4: Launch & Onboarding (May 2025 - June 2025)**
- **Milestone 1: First paying customer onboarded (2025-06-15).**
- Final security audit and PCI certification.

**Post-Launch Milestones:**
- **Internal Alpha Release:** 2025-08-15.
- **Architecture Review Complete:** 2025-10-15.

---

## 10. MEETING NOTES (EXTRACTED FROM SHARED LOG)

*Note: These extracts are from the shared running document (approx. 200 pages). The document is currently unsearchable, requiring manual scrolling.*

### Meeting #42: October 30, 2024
**Attendees:** Luna, Gia, Hiro, Uma.
**Topic:** Infrastructure Delays.
**Discussion:**
- Luna noted that the Fly.io provisioning is still stuck. Gia mentioned that the "Advanced Search" is completely blocked because we can't spin up the indexer.
- Hiro suggested using a temporary local instance, but Luna worried this would create "environmental drift."
- **Decision:** The team will proceed with a mocked PostgreSQL index for now. Uma will document the differences between the mock and the intended production index to avoid future bugs.

### Meeting #58: November 15, 2024
**Attendees:** Luna, Gia, Hiro, Uma.
**Topic:** Tech Stack Learning Curve.
**Discussion:**
- Gia admitted that the LiveView state management is more complex than expected.
- Hiro is struggling with the CSS implementation inside Phoenix components.
- Uma (Intern) actually found a great resource on CRDTs in Elixir and suggested a library.
- **Decision:** The team will dedicate Friday afternoons to "Skill-Up" sessions. All workarounds discovered during this process must be documented in the shared log.

### Meeting #71: December 5, 2024
**Attendees:** Luna, Gia, Hiro, Uma.
**Topic:** Technical Debt and Hardcoding.
- Luna pointed out that there are hardcoded configuration values (API keys, timeout settings) scattered across 40+ files.
- Gia argued that they don't have time to refactor now given the 6-month deadline.
- **Decision:** The team will implement a `Config` module in January to centralize these values. This is now flagged as "Technical Debt" and will be addressed before the Internal Alpha release.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $800,000

| Category | Allocated Amount | Notes |
| :--- | :--- | :--- |
| **Personnel (Salary/Contract)** | $550,000 | 4 team members for 6 months + anticipated contractor. |
| **Infrastructure (Fly.io, S3, CDN)** | $60,000 | High-availability clusters and global CDN delivery. |
| **Software & Tools (SendGrid, Twilio, Stripe)** | $40,000 | API subscriptions and transaction fees. |
| **Security & Compliance (PCI Audit)** | $80,000 | External auditors and PCI DSS certification costs. |
| **Contingency Fund** | $70,000 | Reserved for risk mitigation (e.g., R-01 contractor). |

---

## 12. APPENDICES

### Appendix A: Technical Debt Registry
Currently, the project suffers from "Configuration Sprawl." Hardcoded values are present in:
- `/lib/lattice/integration/partner_api.ex` (API Base URL)
- `/lib/lattice/billing/stripe_client.ex` (Secret Keys)
- `/config/runtime.exs` (Partial implementation)
- Plus 37 other files.
**Remediation:** Transition to `runtime.exs` and environment variables.

### Appendix B: PCI DSS Level 1 Compliance Checklist
To maintain Level 1 status, the following must be audited:
- **Encryption:** All credit card data must be encrypted in transit (TLS 1.2+) and at rest.
- **Access Control:** Strict RBAC (Role-Based Access Control) implemented for the `billing_profiles` table.
- **Logging:** Every access to patient records must be logged in the `audit_logs` table with an immutable timestamp.
- **Network:** Production environment must be isolated from Dev/Staging via VPC.