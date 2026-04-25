# PROJECT SPECIFICATION DOCUMENT: PROJECT DRIFT
**Document Version:** 1.0.4  
**Status:** Active/Baseline  
**Date:** October 24, 2024  
**Company:** Stratos Systems  
**Project Lead:** Devika Oduya (Engineering Manager)

---

## 1. EXECUTIVE SUMMARY

Project Drift is a strategic machine learning model deployment initiative commissioned by Stratos Systems to optimize operational efficiency and reduce overhead within our educational technology suite. Currently, Stratos Systems maintains four redundant internal tools—each handling disparate aspects of model versioning, inference monitoring, data validation, and deployment orchestration. This fragmentation has led to "tooling sprawl," resulting in inefficient resource allocation, redundant licensing costs, and a disjointed developer experience. 

The primary business justification for Project Drift is the consolidation of these four legacy systems into a single, unified deployment platform. By migrating to a centralized architecture, Stratos Systems expects to eliminate approximately $120,000 in annual licensing fees for third-party plugins and reduce the engineering man-hours spent on cross-tool synchronization by an estimated 30%. Furthermore, the centralization of the ML pipeline ensures that model drift (the namesake of the project) can be detected and remediated in a single pane of glass, rather than across four disconnected dashboards.

From an ROI perspective, the project is budgeted at $800,000 for a six-month build cycle. The projected return on investment is calculated based on three primary pillars:
1. **Direct Cost Savings:** Immediate cessation of legacy tool subscriptions upon MVP launch.
2. **Operational Velocity:** Reducing the "Time to Production" for new ML models from 14 days to 3 days.
3. **Risk Mitigation:** Achieving SOC 2 Type II compliance, which opens the door to high-value institutional contracts that were previously unattainable due to security gaps in the legacy tools.

The project targets a user base of 10,000 monthly active users (MAU) within six months of launch. Success is defined not just by feature parity with the four legacy tools, but by a superior user experience that enables data scientists to deploy models without manual intervention from the DevOps team. By implementing a Go-based microservices architecture on GCP, Project Drift will provide the scalability required to handle the fluctuating loads of the academic calendar (e.g., peak loads during finals week).

---

## 2. TECHNICAL ARCHITECTURE

Project Drift adheres to a traditional three-tier architecture (Presentation, Business Logic, Data) designed for high availability, strict consistency, and regulatory compliance.

### 2.1 Stack Overview
- **Language:** Go (Golang) v1.21+ for all microservices.
- **Communication:** gRPC for internal service-to-service communication to minimize latency and ensure strong typing via Protocol Buffers.
- **Database:** CockroachDB v23.1 (Distributed SQL) to ensure global consistency and high availability across GCP regions.
- **Orchestration:** Kubernetes (GKE) on Google Cloud Platform (GCP).
- **Security:** TLS 1.3 for all transit, AES-256 for data at rest, and IAM integration for SOC 2 compliance.

### 2.2 Architectural Components
1. **Presentation Tier:** A React-based frontend communicating with the backend via a Go-based API Gateway.
2. **Business Logic Tier:** A suite of Go microservices (Model Manager, Audit Service, Automation Engine, etc.) running in GKE pods.
3. **Data Tier:** A multi-region CockroachDB cluster providing the persistence layer for configuration, audit logs, and user metadata.

### 2.3 ASCII Architecture Diagram
```text
[ Client Browser / UI ] 
       |
       | (HTTPS/REST)
       v
[  API Gateway (Go)  ] <--- [ Auth Service (SOC 2) ]
       |
       | (gRPC)
       +-----------------------+-----------------------+
       |                       |                       |
[ Model Service ]      [ Audit Service ]      [ Automation Engine ]
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                    [ CockroachDB Cluster ]
                    (Multi-Region Deployment)
                               |
                               v
                    [ GCP Cloud Storage ]
                    (ML Model Binaries/Weights)
```

### 2.4 Data Flow
When a user triggers a model deployment, the request hits the API Gateway, is validated by the Auth Service, and is routed to the Model Service. The Model Service orchestrates the deployment on GKE, while the Audit Service asynchronously records the transaction in a tamper-evident CockroachDB table. All service-to-service calls are handled via gRPC to ensure the lowest possible overhead.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 Customizable Dashboard with Drag-and-Drop Widgets
**Priority:** High | **Status:** In Design
The dashboard is the central nervous system of Project Drift. Its primary goal is to provide a high-level overview of the health of all deployed ML models. The "Customizable" aspect requires that users (Data Scientists, ML Engineers) can curate their own view based on the metrics they value most.

**Functional Requirements:**
- **Widget Library:** The system must provide a library of pre-defined widgets, including:
    - *Inference Latency:* A line chart showing p50, p95, and p99 latency.
    - *Model Drift Score:* A gauge showing the divergence between training and serving data.
    - *Resource Utilization:* A bar chart showing CPU/RAM usage per pod.
    - *Throughput:* A real-time counter of requests per second (RPS).
- **Drag-and-Drop Interface:** Using a grid-based layout system (e.g., React-Grid-Layout), users must be able to resize, move, and remove widgets.
- **Persistence:** User-specific dashboard configurations must be stored in the `user_dashboards` table in CockroachDB, allowing the layout to persist across sessions.
- **Filtering:** A global time-range picker that updates all widgets on the dashboard simultaneously.

**Technical Constraints:**
The dashboard must utilize WebSockets for real-time updates to avoid constant polling of the backend. The backend Go services must aggregate metrics from Prometheus/Stackdriver and serve them via a specialized Metrics Service to avoid overloading the primary business logic services.

### 3.2 Audit Trail Logging with Tamper-Evident Storage
**Priority:** High | **Status:** In Design
Given the SOC 2 Type II compliance requirement, Project Drift must maintain an immutable record of every action taken within the system. This is not a standard application log; it is a legal audit trail.

**Functional Requirements:**
- **Comprehensive Capturing:** Every API call that modifies the state of the system (POST, PUT, DELETE) must be logged. This includes who performed the action, the timestamp, the IP address, and the "before" and "after" state of the modified resource.
- **Tamper-Evidence:** To ensure records cannot be altered by administrators, the system will implement a "hash-chain" mechanism. Each log entry will contain a cryptographic hash of the previous entry, creating a chain of custody.
- **Storage:** Logs will be stored in a read-only CockroachDB partition.
- **Search and Retrieval:** An administrative interface to query logs by user, date range, or resource ID.

**Technical Constraints:**
To prevent the audit trail from becoming a performance bottleneck, the Audit Service will use an asynchronous pattern. The primary service will publish an event to a message queue (Pub/Sub), and the Audit Service will consume and write to the database. The integrity check (hash verification) will run as a nightly cron job to ensure no entries have been modified.

### 3.3 Workflow Automation Engine with Visual Rule Builder
**Priority:** Low | **Status:** In Progress
This feature allows users to automate responses to model performance issues. For example: "If Model Drift > 0.5 and Accuracy < 80%, then trigger a re-training pipeline."

**Functional Requirements:**
- **Visual Rule Builder:** A node-based UI where users can drag "Triggers" (e.g., Metric Threshold) and connect them to "Actions" (e.g., Slack Notification, Trigger Pipeline).
- **Logic Gates:** Support for basic Boolean logic (AND, OR, NOT) to combine multiple triggers.
- **Execution Engine:** A Go-based worker that evaluates rules against incoming telemetry data every 60 seconds.
- **Manual Override:** A "Pause" button to disable automation during critical maintenance windows.

**Technical Constraints:**
The automation engine must be idempotent. If a rule is triggered multiple times within a short window, the system must implement a "cooling-off" period (default 30 minutes) to prevent "alert storms" or infinite re-training loops.

### 3.4 Webhook Integration Framework for Third-Party Tools
**Priority:** Medium | **Status:** Blocked
This framework allows Project Drift to communicate with external education-tech tools, such as student management systems or external labeling services.

**Functional Requirements:**
- **Outbound Webhooks:** The ability to send JSON payloads to a user-specified URL when specific events occur (e.g., `model.deployed`, `alert.triggered`).
- **Inbound Webhooks:** Exposed endpoints that allow external tools to trigger actions within Project Drift (e.g., triggering a model rollout based on an external QA sign-off).
- **Secret Management:** Use of shared secrets (HMAC signatures) to verify the authenticity of incoming webhook requests.
- **Retry Logic:** An exponential backoff strategy for failed outbound webhook deliveries.

**Technical Constraints:**
Currently blocked by third-party API rate limits during testing. The implementation must include a request queuing system (using Redis or CockroachDB) to buffer outbound requests and adhere to the rate limits of external vendors.

### 3.5 Real-time Collaborative Editing with Conflict Resolution
**Priority:** Critical | **Status:** Not Started
This is a launch-blocker. Because ML model configuration files (YAML/JSON) are often managed by teams, multiple engineers need to be able to edit deployment manifests simultaneously without overwriting each other's changes.

**Functional Requirements:**
- **Concurrent Editing:** Multiple users must be able to open the same configuration file and see each other's cursors in real-time.
- **Conflict Resolution:** Implementation of Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) to merge changes seamlessly.
- **Presence Indicators:** Visual cues showing who is currently active in the document.
- **Version History:** A "Time Machine" feature allowing users to revert to any previous state of the configuration.

**Technical Constraints:**
Due to the requirement for sub-100ms latency for cursor movements, this feature requires a dedicated WebSocket server. The state will be managed in-memory for active sessions and persisted to CockroachDB upon "save" or session termination. Given the complexity, this is the highest risk item in the project.

---

## 4. API ENDPOINT DOCUMENTATION

All endpoints are prefixed with `/api/v1`. All requests and responses use `application/json`.

### 4.1 GET `/models`
**Description:** Retrieves a list of all deployed ML models.
- **Request:** `GET /api/v1/models?status=active&limit=20`
- **Response (200 OK):**
```json
[
  {
    "model_id": "mod-8821",
    "name": "Student_Grade_Predictor",
    "version": "2.4.1",
    "status": "active",
    "created_at": "2025-01-10T10:00:00Z"
  }
]
```

### 4.2 POST `/models/deploy`
**Description:** Initiates the deployment of a new model version.
- **Request:** 
```json
{
  "model_id": "mod-8821",
  "version": "2.4.2",
  "image_url": "gcr.io/stratos-systems/grade-pred:v2.4.2",
  "resources": { "cpu": "2", "memory": "4Gi" }
}
```
- **Response (202 Accepted):**
```json
{
  "deployment_id": "dep-9901",
  "status": "provisioning",
  "estimated_completion": "2025-10-24T14:30:00Z"
}
```

### 4.3 GET `/audit/logs`
**Description:** Fetches audit trails for a specific resource.
- **Request:** `GET /api/v1/audit/logs?resource_id=mod-8821`
- **Response (200 OK):**
```json
[
  {
    "log_id": "log-112",
    "user_id": "user-devika",
    "action": "UPDATE_VERSION",
    "timestamp": "2025-10-24T12:00:00Z",
    "hash": "a3f2b1..."
  }
]
```

### 4.4 PUT `/dashboard/layout`
**Description:** Saves a user's customized dashboard configuration.
- **Request:**
```json
{
  "user_id": "user-dmitri",
  "layout": [
    { "widget_id": "latency-chart", "x": 0, "y": 0, "w": 6, "h": 4 },
    { "widget_id": "drift-gauge", "x": 6, "y": 0, "w": 6, "h": 4 }
  ]
}
```
- **Response (200 OK):** `{"status": "success"}`

### 4.5 POST `/automation/rules`
**Description:** Creates a new automation rule.
- **Request:**
```json
{
  "rule_name": "HighDriftAlert",
  "trigger": { "metric": "drift_score", "operator": ">", "value": 0.5 },
  "action": { "type": "slack_notification", "channel": "#ml-alerts" }
}
```
- **Response (201 Created):** `{"rule_id": "rule-441"}`

### 4.6 GET `/metrics/health`
**Description:** Returns the real-time health status of the deployment cluster.
- **Request:** `GET /api/v1/metrics/health`
- **Response (200 OK):**
```json
{
  "cluster_status": "healthy",
  "active_pods": 42,
  "error_rate": "0.02%"
}
```

### 4.7 DELETE `/models/{model_id}`
**Description:** Tears down a model deployment.
- **Request:** `DELETE /api/v1/models/mod-8821`
- **Response (204 No Content):** (Empty body)

### 4.8 POST `/webhooks/register`
**Description:** Registers a third-party URL for event notifications.
- **Request:**
```json
{
  "event": "model.deployed",
  "target_url": "https://partner-api.com/webhooks",
  "secret_key": "sk_test_9921"
}
```
- **Response (201 Created):** `{"webhook_id": "wh-552"}`

---

## 5. DATABASE SCHEMA

The project utilizes CockroachDB to ensure consistency across regions. Below are the primary tables.

### 5.1 Tables and Relationships

| Table Name | Primary Key | Foreign Keys | Key Fields | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_id` | None | `email`, `role`, `timezone` | User identity and access |
| `models` | `model_id` | None | `name`, `description`, `category` | Metadata for ML models |
| `model_versions` | `version_id` | `model_id` | `version_string`, `image_url`, `weights_path` | Specific versions of a model |
| `deployments` | `deploy_id` | `version_id`, `user_id` | `cluster_id`, `status`, `created_at` | Active deployment state |
| `audit_logs` | `log_id` | `user_id` | `action`, `payload_before`, `payload_after`, `prev_hash` | Tamper-evident trail |
| `user_dashboards` | `config_id` | `user_id` | `layout_json`, `last_updated` | Saved widget configurations |
| `automation_rules` | `rule_id` | `user_id` | `trigger_json`, `action_json`, `is_enabled` | Logic for auto-remediation |
| `webhooks` | `webhook_id` | `user_id` | `target_url`, `event_type`, `secret_hash` | 3rd party integrations |
| `metrics_snapshots` | `snap_id` | `version_id` | `drift_score`, `latency_p99`, `timestamp` | Historical performance data |
| `collaboration_sessions` | `session_id` | `model_id` | `active_users_count`, `session_start` | Real-time editing state |

### 5.2 Relationships Logic
- **One-to-Many:** `users` $\rightarrow$ `deployments` (One user can initiate many deployments).
- **One-to-Many:** `models` $\rightarrow$ `model_versions` (One model has many versions).
- **One-to-Many:** `model_versions` $\rightarrow$ `deployments` (One version can be deployed to multiple environments).
- **One-to-One:** `user_id` $\rightarrow$ `user_dashboards` (Each user has one primary dashboard config).

---

## 6. DEPLOYMENT AND INFRASTRUCTURE

Project Drift follows a strict promotion pipeline to ensure stability and SOC 2 compliance.

### 6.1 Environment Descriptions

#### Development (`dev`)
- **Purpose:** Rapid iteration and feature testing.
- **Infrastructure:** A single-node GKE cluster with auto-scaling disabled.
- **Database:** A local CockroachDB instance.
- **CI/CD:** Triggered on every merge to the `develop` branch. Deployment is automatic.

#### Staging (`staging`)
- **Purpose:** Pre-production validation, QA, and SOC 2 audit testing.
- **Infrastructure:** A mirrored environment of production (3-node cluster) in a separate GCP project.
- **Database:** A managed CockroachDB cluster with anonymized production data.
- **CI/CD:** Triggered by a release tag. Requires approval from Wes Park (QA Lead).

#### Production (`prod`)
- **Purpose:** End-user serving.
- **Infrastructure:** Multi-region GKE cluster with Horizontal Pod Autoscalers (HPA).
- **Database:** Fully distributed CockroachDB cluster across three GCP regions (us-east1, us-west1, europe-west1).
- **CI/CD:** Quarterly releases aligned with regulatory review cycles. Manual "big bang" deployments with a 20% canary rollout.

### 6.2 Infrastructure Management
Infrastructure is managed as code (IaC) using Terraform. Any change to the GKE cluster configuration must be submitted as a PR to the `infra-drift` repository and approved by Devika Oduya.

---

## 7. TESTING STRATEGY

To ensure 99.9% uptime, Project Drift employs a multi-layered testing approach.

### 7.1 Unit Testing
- **Scope:** Individual Go functions and gRPC handlers.
- **Requirement:** Minimum 80% code coverage across all microservices.
- **Tooling:** `go test` with `testify/assert` for validations. Mocking of CockroachDB calls using `sqlmock`.

### 7.2 Integration Testing
- **Scope:** Service-to-service communication and database transactions.
- **Approach:** Spinning up ephemeral environments using Docker Compose to test the interaction between the Model Service, Audit Service, and CockroachDB.
- **Focus:** Ensuring that gRPC contracts are honored and that the hash-chain in the audit log is correctly formed.

### 7.3 End-to-End (E2E) Testing
- **Scope:** Full user journeys from the React frontend to the backend and back.
- **Approach:** Using Cypress for browser-based automation.
- **Critical Path Tests:** 
    - Deploying a model $\rightarrow$ Verifying pod status $\rightarrow$ Checking audit log.
    - Customizing dashboard $\rightarrow$ Refreshing page $\rightarrow$ Verifying layout persistence.
    - Collaborative editing $\rightarrow$ Simultaneous edits $\rightarrow$ Verifying merged state.

### 7.4 Performance Benchmarking
- **Target:** Support 10,000 MAU with a p99 latency of $<200\text{ms}$ for API requests.
- **Tooling:** k6 for load testing.
- **Frequency:** Benchmarks are run weekly in the staging environment to detect performance regressions.

---

## 8. RISK REGISTER

| Risk ID | Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| R-01 | Team lack of experience with Go/gRPC/CockroachDB | High | Medium | Negotiate timeline extension with stakeholders; provide internal training. |
| R-02 | Competitor is 2 months ahead in product development | Medium | High | Document existing workarounds for legacy tools and share with the team to accelerate parity. |
| R-03 | SOC 2 Audit failure | Low | Critical | Weekly security reviews; early engagement with auditors; strict adherence to the Audit Trail spec. |
| R-04 | Real-time editing complexity leads to launch delay | High | High | Isolate the feature in its own microservice; consider a simplified "locking" mechanism if CRDTs prove too complex. |

**Probability/Impact Matrix:**
- **High Probability / High Impact:** R-04 (Critical Focus)
- **High Probability / Medium Impact:** R-01 (Managed via timeline)
- **Medium Probability / High Impact:** R-02 (Managed via agility)

---

## 9. TIMELINE

The build is scheduled for 6 months, ending in August 2025.

### 9.1 Phase 1: Foundation (October 2024 - January 2025)
- **Focus:** Infrastructure setup, gRPC contracts, and basic Model Service.
- **Dependencies:** GKE Cluster provisioning $\rightarrow$ Database Schema migration $\rightarrow$ API Gateway.

### 9.2 Phase 2: Core Feature Build (January 2025 - April 2025)
- **Focus:** Dashboard, Audit Trail, and Webhooks.
- **Dependencies:** Auth Service $\rightarrow$ Audit Service $\rightarrow$ Dashboard UI.
- **Milestone 1:** Security audit passed (Target: 2025-04-15).

### 9.3 Phase 3: Advanced Features & Stabilization (April 2025 - June 2025)
- **Focus:** Collaborative Editing and Automation Engine.
- **Dependencies:** WebSocket Server $\rightarrow$ CRDT Implementation $\rightarrow$ E2E Testing.
- **Milestone 2:** MVP feature-complete (Target: 2025-06-15).

### 9.4 Phase 4: Optimization & Launch (June 2025 - August 2025)
- **Focus:** Performance tuning, load testing, and regulatory sign-off.
- **Dependencies:** k6 Benchmarks $\rightarrow$ SOC 2 Final Report $\rightarrow$ Production Deployment.
- **Milestone 3:** Performance benchmarks met (Target: 2025-08-15).

---

## 10. MEETING NOTES

*Note: Following the team's "low-ceremony" culture, these are synthesized from Slack threads.*

### Thread 1: `#drift-dev-ops` (Nov 12, 2024)
**Topic:** Choosing CockroachDB vs. Standard Postgres.
- **Dmitri:** Argued that standard Postgres would require manual sharding as we hit 10k users.
- **Devika:** Agreed that the multi-region requirement for the education sector (GDPR compliance) makes CockroachDB a better fit.
- **Decision:** Adopt CockroachDB v23.1. Dmitri to lead the schema design.

### Thread 2: `#drift-frontend` (Dec 05, 2024)
**Topic:** Dashboard Widget Framework.
- **Sanjay:** Suggested using a proprietary library for the drag-and-drop interface to save time.
- **Wes:** Objected, citing potential licensing costs and SOC 2 compatibility.
- **Decision:** Use `react-grid-layout` (Open Source) to maintain control and avoid additional costs.

### Thread 3: `#drift-general` (Jan 20, 2025)
**Topic:** Webhook Blockers.
- **Sanjay:** Reported that the third-party API for "EduLink" is rate-limiting us to 5 requests per second during testing, blocking the integration framework.
- **Devika:** Decided that the team should not wait for the vendor to increase limits. Instead, build a request queue in the backend to throttle requests.
- **Decision:** Implement a Redis-backed queue to manage outbound webhook traffic.

---

## 11. BUDGET BREAKDOWN

The total budget is **$800,000**, allocated for a 6-month development cycle.

| Category | Allocated Amount | Details |
| :--- | :--- | :--- |
| **Personnel** | $550,000 | Salaries for 7 FTEs + 1 Contractor (Sanjay). |
| **Infrastructure** | $120,000 | GCP GKE costs, CockroachDB Cloud licenses, Cloud Storage. |
| **Tooling & Software** | $40,000 | IDE licenses, CI/CD tools, Security scanning software (Snyk/SonarQube). |
| **SOC 2 Compliance** | $50,000 | External auditor fees and compliance documentation software. |
| **Contingency** | $40,000 | Reserved for emergency scaling or unexpected contractor extensions. |

**Budget Status:** Comfortable. The team is currently trending $15,000 under budget due to the use of open-source frontend libraries.

---

## 12. APPENDICES

### Appendix A: Protocol Buffer Definition (Snippet)
The following is a sample of the `.proto` file used for communication between the API Gateway and the Model Service.

```protobuf
syntax = "proto3";

package drift.models;

service ModelDeploymentService {
  rpc DeployModel (DeployRequest) returns (DeployResponse);
  rpc GetModelState (StateRequest) returns (StateResponse);
}

message DeployRequest {
  string model_id = 1;
  string version = 2;
  string image_url = 3;
  map<string, string> resources = 4;
}

message DeployResponse {
  string deployment_id = 1;
  string status = 2;
  string estimated_completion = 3;
}
```

### Appendix B: SOC 2 Compliance Mapping
To meet the SOC 2 Type II requirements, Project Drift maps its features to the following Trust Services Criteria:

- **Security (Common Criteria 6.0):** Addressed by the Audit Trail logging and the gRPC TLS implementation.
- **Availability (Availability Criteria):** Addressed by the multi-region CockroachDB cluster and GKE auto-scaling.
- **Confidentiality (Confidentiality Criteria):** Addressed by AES-256 encryption at rest and GCP IAM role-based access control (RBAC).
- **Processing Integrity:** Addressed by the E2E testing suite and the tamper-evident hash-chaining of all system state changes.