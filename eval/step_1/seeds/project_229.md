# PROJECT SPECIFICATION: PROJECT GANTRY
**Document Version:** 1.0.4  
**Status:** Draft for Engineering Review  
**Date:** October 24, 2024  
**Owner:** Ilya Oduya (VP of Product, Bridgewater Dynamics)  
**Classification:** Internal / Proprietary  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Justification
Project Gantry represents a strategic pivot for Bridgewater Dynamics. Historically, the company has excelled in domestic asset management; however, Gantry is a greenfield venture designed to penetrate the global logistics and shipping industry. The objective is to establish a proprietary IoT device network capable of tracking high-value freight across international borders in real-time, providing visibility into telemetry (temperature, humidity, shock) and location.

The logistics industry is currently fragmented, relying on legacy EDI systems and disparate hardware. Gantry aims to disrupt this by providing a unified, cloud-native platform that integrates hardware telemetry with a high-performance SaaS dashboard. By owning the full stack—from the device network to the billing layer—Bridgewater Dynamics can capture a significant portion of the "Cold Chain" and "High-Value Asset" markets.

### 1.2 ROI Projection
The projected Return on Investment (ROI) for Gantry is based on a three-year horizon. With an initial capital expenditure of $400,000, the project targets a Year 1 Annual Recurring Revenue (ARR) of $1.2M, based on a projected customer base of 50 mid-sized shipping firms paying a monthly subscription for device management and data analytics.

**Financial Projections:**
*   **Year 1:** Revenue $1.2M | OpEx $600K | Net $600K
*   **Year 2:** Revenue $3.5M | OpEx $1.1M | Net $2.4M
*   **Year 3:** Revenue $8.0M | OpEx $2.2M | Net $5.8M

The primary value driver is the reduction in cargo loss (shrinkage) and insurance premiums for clients. By providing real-time alerts and forensic-level telemetry, Gantry expects to reduce cargo loss by 15-20% for its users, creating a sticky ecosystem and high switching costs.

### 1.3 Strategic Alignment
Despite the team's lack of experience with the chosen stack, the decision to use TypeScript/Next.js and Kafka allows for rapid iteration and scalability. This project positions Bridgewater Dynamics as a technology leader in a market they have never operated in before, diversifying the company's revenue streams away from traditional domestic services.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
Gantry utilizes a microservices architecture designed for high throughput and eventual consistency. The system is built on a foundation of TypeScript, leveraging Next.js for the frontend and administrative portals, and a suite of Node.js microservices for backend processing. Communication between services is handled via an event-driven model using Apache Kafka, ensuring that device telemetry spikes do not crash the API layer.

### 2.2 The Stack
*   **Frontend:** Next.js 14 (App Router), Tailwind CSS, TanStack Query.
*   **Backend:** Node.js (TypeScript) microservices.
*   **Database:** PostgreSQL (Primary), Prisma (ORM).
*   **Messaging:** Apache Kafka (Event streaming for device telemetry).
*   **Deployment:** Vercel (Frontend/Serverless Functions).
*   **Feature Management:** LaunchDarkly (Canary releases and A/B testing).
*   **Security:** PCI DSS Level 1 compliance for direct credit card processing.

### 2.3 Architecture Diagram (ASCII Description)
```text
[ IoT Device Network ]  --> (MQTT/TCP) --> [ IoT Gateway Service ]
                                               |
                                               v
[ Kafka Event Bus ] <------------------- [ Telemetry Processor ]
       |                                        |
       +--> [ Notification Service ] <----------+
       |                                        |
       +--> [ Billing/Subscription Svc ] <-----+
       |                                        |
       +--> [ Device Registry Service ] <-------+
                                               |
                                               v
[ Vercel / Next.js Frontend ] <---> [ Prisma ORM ] <---> [ PostgreSQL DB ]
       ^                                        ^
       |                                        |
[ LaunchDarkly (Feature Flags) ] <-------------+
```

### 2.4 Data Flow and Consistency
The system employs an "Event Sourcing" pattern for device telemetry. When a device sends a packet, the Gateway Service validates the packet and pushes a `TelemetryReceived` event to Kafka. The Telemetry Processor consumes this event, calculates anomalies, and updates the PostgreSQL database via Prisma. This ensures that the API response times remain low (p95 < 200ms) because the heavy processing is decoupled from the request-response cycle.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Offline-First Mode with Background Sync
**Priority:** Critical (Launch Blocker) | **Status:** In Review

**Description:**
Logistics personnel often operate in "dead zones" (warehouses, ship holds, remote ports) where cellular connectivity is nonexistent. The Gantry dashboard must allow users to perform critical actions—such as marking a shipment as "Received" or updating device configurations—while offline.

**Functional Requirements:**
*   **Local State Persistence:** Use IndexedDB via a wrapper (like Dexie.js) to store pending mutations on the client side.
*   **Conflict Resolution:** Implement a "Last Write Wins" (LWW) strategy for simple fields, and a version-vector approach for complex configuration changes.
*   **Background Sync:** Utilize Service Workers and the Background Sync API to detect when connectivity is restored and push queued mutations to the `/sync` endpoint.
*   **UI Indicators:** A clear visual indicator (e.g., a "Syncing..." toast or a cloud icon with a slash) must inform the user of their current connectivity status and the number of pending updates.

**Technical Implementation:**
The client will maintain a `sync_queue` table in IndexedDB. Each entry will contain the target endpoint, the payload, a timestamp, and a unique idempotency key. Upon reconnection, the client will iterate through the queue, sending batches of 10 requests to the backend to avoid overloading the API.

---

### 3.2 A/B Testing Framework (Integrated with Feature Flags)
**Priority:** High | **Status:** In Progress

**Description:**
To optimize the user experience for diverse logistics roles (e.g., Warehouse Managers vs. Fleet Operators), the team requires a way to test different UI layouts and workflows without deploying new code. This framework is baked directly into the LaunchDarkly implementation.

**Functional Requirements:**
*   **User Segmentation:** The ability to bucket users based on attributes (e.g., `company_size`, `region`, `user_role`).
*   **Variant Assignment:** Each user is assigned to a "Control" or "Treatment" group for a specific feature flag.
*   **Telemetry Integration:** The system must log which variant a user saw when a specific action was performed, allowing for conversion rate analysis.
*   **Automatic Rollout:** Support for gradual rollouts (e.g., 5% $\rightarrow$ 20% $\rightarrow$ 100%) based on stability metrics.

**Technical Implementation:**
A custom React hook `useABTest(flagKey)` will be developed. This hook interfaces with the LaunchDarkly SDK to retrieve the variant. The result is then passed to a `TelemetryEvent` logger that sends the variant ID to the analytics database, enabling the team to compare the p95 task completion time between Variant A and Variant B.

---

### 3.3 File Upload with Virus Scanning and CDN Distribution
**Priority:** Medium | **Status:** In Review

**Description:**
Users must be able to upload customs documentation, bills of lading, and device manuals. Because these files are uploaded by third parties and accessed globally, security and latency are paramount.

**Functional Requirements:**
*   **Secure Upload Path:** Files are uploaded to a temporary "Quarantine" S3 bucket.
*   **Automated Scanning:** An asynchronous trigger (AWS Lambda) invokes a virus scanning service (ClamAV) upon upload.
*   **CDN Distribution:** Once cleared, files are moved to a "Production" bucket backed by a global CDN (CloudFront) for low-latency access.
*   **Access Control:** Signed URLs must be used to ensure that only authorized users can access specific shipment documents.

**Technical Implementation:**
1. Frontend requests a pre-signed URL from the `/files/upload-url` endpoint.
2. File is uploaded directly to S3.
3. S3 Event Notification triggers a Lambda function for scanning.
4. If the scan returns `CLEAN`, the file is replicated to the distribution bucket and the database record is updated to `status: 'available'`. If `INFECTED`, the file is deleted, and a notification is sent to the admin.

---

### 3.4 Automated Billing and Subscription Management
**Priority:** Medium | **Status:** In Design

**Description:**
Gantry operates on a per-device subscription model. The system must handle recurring billing, prorated upgrades, and automated suspension of service for non-payment.

**Functional Requirements:**
*   **PCI DSS Compliance:** The system must process credit card data directly. This requires the environment to meet Level 1 compliance, including strict network segmentation and quarterly vulnerability scans.
*   **Tiered Pricing:** Support for "Basic" (10 devices), "Professional" (100 devices), and "Enterprise" (Unlimited) tiers.
*   **Dunning Process:** Automated email sequences for failed payments, with a grace period of 7 days before device telemetry is restricted.
*   **Invoicing:** Generation of PDF invoices monthly, available for download in the user portal.

**Technical Implementation:**
A dedicated `BillingService` microservice will interface with the payment gateway. The database will track `subscription_id`, `current_period_end`, and `payment_status`. A cron job running every 24 hours will identify expired subscriptions and trigger the `restrict_device_access` event via Kafka.

---

### 3.5 Notification System (Multi-Channel)
**Priority:** Critical (Launch Blocker) | **Status:** Not Started

**Description:**
Real-time alerts are the core value proposition of Gantry. Users must be notified immediately when a device reports a critical anomaly (e.g., temperature spike in a pharmaceutical shipment).

**Functional Requirements:**
*   **Omni-channel Delivery:** Support for Email (SendGrid), SMS (Twilio), In-App notifications (WebSockets), and Push Notifications (Firebase).
*   **Preference Center:** Users can toggle which channels they want for specific alert types (e.g., "Critical Alerts" $\rightarrow$ SMS/Push; "Weekly Reports" $\rightarrow$ Email).
*   **Escalation Logic:** If a critical alert is not acknowledged within 30 minutes, the system must escalate the notification to the next manager in the hierarchy.
*   **Templating:** Dynamic templates that inject device ID, location, and current telemetry values.

**Technical Implementation:**
The `NotificationService` listens to the `AlertGenerated` topic in Kafka. It queries the user preference database to determine the target channels. It then pushes the message to a queue (RabbitMQ or similar) to handle the asynchronous nature of external API calls to Twilio and SendGrid, ensuring that a slow external API doesn't block the alert pipeline.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests require a Bearer Token in the header.

### 4.1 Device Management

**1. GET `/devices`**
*   **Description:** Retrieve a list of all devices associated with the organization.
*   **Request:** `GET /api/v1/devices?status=active&limit=50`
*   **Response (200 OK):**
    ```json
    [
      {
        "deviceId": "DEV-9921",
        "status": "active",
        "lastSeen": "2025-03-10T14:22:01Z",
        "battery": 82
      }
    ]
    ```

**2. POST `/devices/configure`**
*   **Description:** Update the polling interval and alert thresholds for a device.
*   **Request:** 
    ```json
    {
      "deviceId": "DEV-9921",
      "config": { "pollInterval": 300, "tempThreshold": 4.5 }
    }
    ```
*   **Response (202 Accepted):** `{"status": "pending_sync", "requestId": "req-445"}`

### 4.2 Telemetry and Tracking

**3. GET `/telemetry/{deviceId}/latest`**
*   **Description:** Get the most recent telemetry packet for a specific device.
*   **Response (200 OK):**
    ```json
    {
      "deviceId": "DEV-9921",
      "timestamp": "2025-03-10T14:25:00Z",
      "data": { "temp": 3.2, "humidity": 45, "lat": 40.7128, "lng": -74.0060 }
    }
    ```

**4. POST `/telemetry/batch`**
*   **Description:** Endpoint for devices to upload cached telemetry data.
*   **Request:**
    ```json
    {
      "deviceId": "DEV-9921",
      "packets": [
        { "ts": "...", "temp": 3.1, "lat": 40.7, "lng": -74.0 },
        { "ts": "...", "temp": 3.2, "lat": 40.8, "lng": -74.1 }
      ]
    }
    ```
*   **Response (201 Created):** `{"processed": 2, "errors": 0}`

### 4.3 Billing and Account

**5. POST `/billing/subscription/update`**
*   **Description:** Change the current subscription tier.
*   **Request:** `{"planId": "plan_enterprise_2025"}`
*   **Response (200 OK):** `{"newPlan": "Enterprise", "nextBillingDate": "2025-04-01"}`

**6. POST `/billing/payment-method`**
*   **Description:** Update credit card details (PCI DSS Compliant).
*   **Request:** `{"token": "tok_visa_4432", "billingAddress": "..."}`
*   **Response (200 OK):** `{"status": "updated"}`

### 4.4 File Management

**7. GET `/files/upload-url`**
*   **Description:** Get a pre-signed S3 URL for a secure upload.
*   **Request:** `{"fileName": "customs_doc_A1.pdf", "fileType": "application/pdf"}`
*   **Response (200 OK):** `{"uploadUrl": "https://s3.amazonaws.com/...", "fileId": "file-123"}`

**8. GET `/files/download/{fileId}`**
*   **Description:** Retrieve a temporary signed download link for a scanned file.
*   **Response (200 OK):** `{"downloadUrl": "https://cdn.gantry.io/...", "expiresIn": 3600}`

---

## 5. DATABASE SCHEMA

The database is hosted on PostgreSQL and managed via Prisma.

### 5.1 Table Definitions

1.  **`Organizations`**
    *   `id`: UUID (PK)
    *   `name`: VARCHAR(255)
    *   `industry`: VARCHAR(100)
    *   `createdAt`: TIMESTAMP
    *   `subscriptionTier`: ENUM ('basic', 'pro', 'enterprise')

2.  **`Users`**
    *   `id`: UUID (PK)
    *   `orgId`: UUID (FK $\rightarrow$ Organizations.id)
    *   `email`: VARCHAR(255) (Unique)
    *   `passwordHash`: TEXT
    *   `role`: ENUM ('admin', 'operator', 'viewer')
    *   `mfaEnabled`: BOOLEAN

3.  **`Devices`**
    *   `id`: UUID (PK)
    *   `orgId`: UUID (FK $\rightarrow$ Organizations.id)
    *   `serialNumber`: VARCHAR(50) (Unique)
    *   `firmwareVersion`: VARCHAR(20)
    *   `status`: ENUM ('active', 'inactive', 'maintenance')
    *   `lastHeartbeat`: TIMESTAMP

4.  **`Telemetry`**
    *   `id`: BIGINT (PK)
    *   `deviceId`: UUID (FK $\rightarrow$ Devices.id)
    *   `timestamp`: TIMESTAMP (Indexed)
    *   `temperature`: DECIMAL(5,2)
    *   `humidity`: DECIMAL(5,2)
    *   `latitude`: DECIMAL(9,6)
    *   `longitude`: DECIMAL(9,6)
    *   `batteryLevel`: INTEGER

5.  **`Alerts`**
    *   `id`: UUID (PK)
    *   `deviceId`: UUID (FK $\rightarrow$ Devices.id)
    *   `severity`: ENUM ('low', 'medium', 'critical')
    *   `message`: TEXT
    *   `isAcknowledged`: BOOLEAN
    *   `acknowledgedAt`: TIMESTAMP

6.  **`NotificationPreferences`**
    *   `userId`: UUID (FK $\rightarrow$ Users.id, PK)
    *   `emailEnabled`: BOOLEAN
    *   `smsEnabled`: BOOLEAN
    *   `pushEnabled`: BOOLEAN
    *   `criticalOnly`: BOOLEAN

7.  **`Subscriptions`**
    *   `id`: UUID (PK)
    *   `orgId`: UUID (FK $\rightarrow$ Organizations.id)
    *   `stripeCustomerId`: VARCHAR(255)
    *   `planId`: VARCHAR(50)
    *   `status`: ENUM ('active', 'past_due', 'canceled')
    *   `currentPeriodEnd`: TIMESTAMP

8.  **`PaymentMethods`**
    *   `id`: UUID (PK)
    *   `orgId`: UUID (FK $\rightarrow$ Organizations.id)
    *   `paymentToken`: TEXT
    *   `lastFour`: VARCHAR(4)
    *   `expiryDate`: DATE

9.  **`Files`**
    *   `id`: UUID (PK)
    *   `orgId`: UUID (FK $\rightarrow$ Organizations.id)
    *   `fileName`: VARCHAR(255)
    *   `s3Key`: TEXT
    *   `scanStatus`: ENUM ('pending', 'clean', 'infected')
    *   `uploadedAt`: TIMESTAMP

10. **`AuditLogs`**
    *   `id`: BIGINT (PK)
    *   `userId`: UUID (FK $\rightarrow$ Users.id)
    *   `action`: TEXT
    *   `entityId`: UUID
    *   `timestamp`: TIMESTAMP
    *   `ipAddress`: VARCHAR(45)

### 5.2 Relationships
*   **Organization $\rightarrow$ User:** One-to-Many.
*   **Organization $\rightarrow$ Device:** One-to-Many.
*   **Device $\rightarrow$ Telemetry:** One-to-Many (High volume).
*   **Device $\rightarrow$ Alert:** One-to-Many.
*   **User $\rightarrow$ NotificationPreference:** One-to-One.
*   **Organization $\rightarrow$ Subscription:** One-to-One.

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

### 6.1 Environment Strategy
Gantry utilizes three distinct environments to ensure stability and security.

**1. Development (`dev`)**
*   **Purpose:** Feature development and internal testing.
*   **Hosting:** Vercel (Preview deployments).
*   **DB:** Local PostgreSQL / Shared Dev DB.
*   **CI/CD:** Automatic deployment on every push to `develop` branch.
*   **Kafka:** Single-node local Kafka cluster.

**2. Staging (`staging`)**
*   **Purpose:** Pre-production validation, UAT, and QA.
*   **Hosting:** Vercel (Staging project).
*   **DB:** Managed PostgreSQL (RDS) mirroring production schema.
*   **CI/CD:** Deployment upon merge to `release` branch.
*   **Kafka:** Multi-node cluster mimicking production architecture.
*   **Data:** Anonymized production data dumps.

**3. Production (`prod`)**
*   **Purpose:** Live customer traffic.
*   **Hosting:** Vercel (Production project).
*   **DB:** High-Availability Managed PostgreSQL (Multi-AZ).
*   **Security:** Hardened VPC, PCI DSS compliant network segment for billing.
*   **CI/CD:** Manual trigger via GitHub Actions after staging sign-off.
*   **Rollout:** Canary releases via LaunchDarkly.

### 6.2 Infrastructure as Code (IaC)
All infrastructure is managed via Terraform. This ensures that the staging and production environments are identical, reducing "it works on my machine" errors. Felix Liu is the primary owner of the Terraform state files.

### 6.3 Scalability and Performance
To achieve the p95 < 200ms response time, the following are implemented:
*   **Redis Caching:** Frequently accessed device statuses are cached in Redis to avoid expensive SQL joins.
*   **Database Indexing:** B-tree indexes on `deviceId` and `timestamp` in the Telemetry table.
*   **Edge Functions:** Use of Vercel Edge Functions for routing and basic authentication to reduce latency for global users.

---

## 7. TESTING STRATEGY

### 7.1 Unit Testing
*   **Framework:** Jest.
*   **Coverage Goal:** 80% for business logic and utility functions.
*   **Focus:** Individual functions, Prisma middleware, and Kafka event transformers.
*   **Frequency:** Executed on every commit via GitHub Actions.

### 7.2 Integration Testing
*   **Framework:** Supertest + TestContainers.
*   **Focus:** API endpoints, database transactions, and Kafka producer/consumer loops.
*   **Approach:** Spin up a temporary PostgreSQL and Kafka container, run a series of API calls, and verify the final state of the database.
*   **Example:** Testing the `Telemetry $\rightarrow$ Alert $\rightarrow$ Notification` pipeline.

### 7.3 End-to-End (E2E) Testing
*   **Framework:** Playwright.
*   **Focus:** Critical user journeys (e.g., "User logs in $\rightarrow$ views device $\rightarrow$ triggers alert $\rightarrow$ acknowledges alert").
*   **Environment:** Run against the Staging environment.
*   **Frequency:** Weekly or before every single production release.

### 7.4 Security and Compliance Testing
*   **PCI Audit:** External quarterly audit to maintain Level 1 certification.
*   **Penetration Testing:** Bi-annual third-party pen-tests focusing on the `/api/v1` endpoints.
*   **Dependency Scanning:** Using `npm audit` and Snyk to detect vulnerable packages in the TypeScript stack.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Team lack of experience with TypeScript/Next.js/Kafka | High | High | Hire a specialized contractor (Joelle Liu) to act as a technical consultant and reduce the bus factor. |
| **R2** | Integration partner's API is undocumented and buggy | High | High | Elevate to the board meeting as a critical blocker; request a dedicated technical account manager from the partner. |
| **R3** | Failure to pass PCI DSS Level 1 audit | Medium | Critical | Implement strict network isolation for billing; employ a PCI compliance consultant. |
| **R4** | Hardwares fail to sync in dead zones | Medium | High | Implement robust offline-first IndexedDB queuing and background sync. |
| **R5** | Kafka lag leading to delayed alerts | Low | High | Implement horizontal scaling for consumer groups and monitor consumer lag via Prometheus. |

### 8.1 Probability/Impact Matrix
*   **High Probability / High Impact:** R1, R2 (Immediate priority)
*   **Medium Probability / High Impact:** R3, R4 (Constant monitoring)
*   **Low Probability / High Impact:** R5 (Architectural safeguard)

---

## 9. TIMELINE AND PHASES

### 9.1 Phase Descriptions
*   **Phase 1: Foundation (Now $\rightarrow$ March 2025)**
    *   Establish VPC and basic CI/CD pipelines.
    *   Implement Device Registry and Telemetry ingestion.
    *   Develop a basic MVP for the stakeholder demo.
*   **Phase 2: Core Features (March $\rightarrow$ May 2025)**
    *   Build the Offline-First sync engine.
    *   Implement the Notification system and Kafka event logic.
    *   Integrate the A/B testing framework.
*   **Phase 3: Compliance & Hardening (May $\rightarrow$ July 2025)**
    *   Complete the PCI DSS Level 1 implementation.
    *   Finalize the automated billing system.
    *   Conduct external security audits and load testing.

### 9.2 Key Milestones
| Milestone | Target Date | Dependency | Deliverable |
| :--- | :--- | :--- | :--- |
| **M1: Stakeholder Demo** | 2025-03-15 | Telemetry MVP | Functional dashboard with live device data. |
| **M2: Architecture Review**| 2025-05-15 | Core Features | Signed-off technical design doc and stability report. |
| **M3: Production Launch** | 2025-07-15 | PCI Audit Pass | Live system with paying customers. |

---

## 10. MEETING NOTES (SLACK THREAD ARCHIVE)

*As per company policy, formal meeting minutes are not kept. The following is a curated archive of decisions made within the `#project-gantry` Slack channel.*

### Thread 1: Technology Stack Selection (2024-11-12)
**Ilya Oduya:** "I know we've all used Python/Django in the past, but for Gantry, I want the speed of Next.js and the scalability of Kafka. We need this to feel like a modern SaaS product."
**Felix Liu:** "I'm concerned about the learning curve. We've never touched Kafka in production. If the cluster goes down, who's fixing it?"
**Ilya Oduya:** "That's why we're bringing in Joelle Liu as a contractor. She's a Kafka veteran. She'll mentor us and set up the initial infrastructure."
**Decision:** Adopt TypeScript/Next.js and Kafka; hire Joelle Liu to mitigate the "bus factor" risk.

### Thread 2: The Third-Party API Crisis (2024-12-05)
**Matteo Kim:** "The integration partner's API is a disaster. The documentation says it's a POST request, but it only responds to GET. Also, we're hitting 429 Rate Limit errors every 10 minutes during basic testing."
**Felix Liu:** "I tried to implement a retry logic with exponential backoff, but the rate limits are so aggressive that we're essentially blocked from testing the telemetry pipeline."
**Ilya Oduya:** "This is now a formal blocker. I'm adding this to the agenda for the next board meeting. We cannot hit M1 if we can't even pull data from the devices."
**Decision:** Raise the API instability and rate limits as a blocker at the board level.

### Thread 3: Configuration Debt (2025-01-20)
**Joelle Liu:** "I've been auditing the codebase. There are hardcoded API keys and database strings scattered across 40+ files. This is a security nightmare and will make the transition to staging/prod impossible."
**Felix Liu:** "Yeah, we were moving fast for the demo. I'll start migrating everything to `.env` and a secret manager."
**Ilya Oduya:** "Prioritize this. I don't want a single hardcoded value in the codebase before the architecture review."
**Decision:** Immediate cleanup of hardcoded configuration values; implement centralized secret management.

---

## 11. BUDGET BREAKDOWN

**Total Budget:** $400,000

### 11.1 Personnel ($280,000)
*   **Internal Salaries (Allocated):** $180,000
    *   *Distributed team of 15 across 5 countries (pro-rated for project time).*
*   **Specialist Contractor (Joelle Liu):** $70,000
    *   *Focused on Kafka architecture and TypeScript mentorship.*
*   **Compliance Consultant:** $30,000
    *   *PCI DSS Level 1 certification guidance and audit preparation.*

### 11.2 Infrastructure ($60,000)
*   **Vercel Enterprise:** $12,000
*   **AWS (RDS, S3, Managed Kafka/MSK):** $35,000
*   **Redis Cloud:** $8,000
*   **CDN (CloudFront):** $5,000

### 11.3 Tools & Software ($30,000)
*   **LaunchDarkly (Professional Tier):** $10,000
*   **Twilio/SendGrid Credits:** $8,000
*   **Snyk/Security Scanning:** $7,000
*   **Miscellaneous SaaS:** $5,000

### 11.4 Contingency Fund ($30,000)
*   **Reserve:** $30,000
    *   *Reserved for emergency infrastructure scaling or additional contractor hours if M2 is delayed.*

---

## 12. APPENDICES

### Appendix A: PCI DSS Compliance Checklist
To achieve Level 1 compliance for direct credit card processing, Gantry must adhere to the following:
1.  **Firewall Configuration:** Implement a dedicated firewall between the Vercel environment and the PostgreSQL database.
2.  **No Defaults:** All default vendor passwords must be changed before the production launch.
3.  **Data Encryption:** Credit card data must be encrypted using AES-256 at rest and TLS 1.2+ in transit.
4.  **Access Control:** Use the "Principle of Least Privilege" (PoLP). Database access is restricted to the `BillingService` only.
5.  **Logging:** All access to the payment database must be logged to an immutable log server (AWS CloudWatch/CloudTrail).

### Appendix B: Kafka Topic Topology
The event-driven system relies on the following Kafka topics:

| Topic Name | Partition Key | Description | Consumer Services |
| :--- | :--- | :--- | :--- |
| `telemetry.raw` | `deviceId` | Raw packets from the gateway. | Telemetry Processor |
| `telemetry.processed` | `deviceId` | Cleaned and validated data. | Dashboard API, Alert Service |
| `alerts.generated` | `alertId` | New anomaly detected. | Notification Service |
| `billing.events` | `orgId` | Subscription changes or payment failures. | Notification Service, Device Registry |
| `system.audit` | `userId` | All admin actions for auditing. | Audit Log Service |

**Partitioning Strategy:**
All telemetry-related topics are partitioned by `deviceId`. This ensures that all data for a single device is processed in chronological order by the same consumer instance, preventing race conditions during the "Offline Sync" process.