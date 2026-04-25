# PROJECT SPECIFICATION DOCUMENT: PROJECT INGOT
**Document Version:** 1.0.4  
**Status:** Draft/In-Review  
**Date:** October 24, 2023  
**Classification:** Confidential – Deepwell Data Internal  

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview
Project Ingot represents a strategic pivot for Deepwell Data, marking the transition from a generalized data services provider to a specialized product vertical focusing on the logistics and shipping industry. The primary objective is the deployment of a sophisticated machine learning (ML) model designed to optimize routing, load balancing, and fuel efficiency for high-volume shipping corridors. Unlike previous internal tools, Ingot is designed as a commercial product, driven by a high-value partnership with a single enterprise client.

### 1.2 Business Justification
The logistics industry is currently experiencing a volatility surge in fuel costs and labor shortages. Deepwell Data has developed a proprietary ML model capable of reducing operational overhead through predictive analytics. The commercial viability of this project is anchored by a commitment from a Tier-1 shipping conglomerate willing to pay an annual recurring revenue (ARR) of $2,000,000. This partnership serves as the "anchor tenancy" for the Ingot vertical, providing the necessary capital and real-world data to refine the model before a wider market release.

### 1.3 ROI Projection
The total budget allocated for Ingot is $3,000,000. The Return on Investment (ROI) is projected based on the following financial model:
*   **Direct Revenue:** $2M ARR from the primary enterprise client.
*   **Operational Efficiency:** The project targets a 35% reduction in cost per transaction compared to the client's legacy system. For a client moving 10 million units annually, this represents an indirect value capture of millions in saved operational expenditure.
*   **Break-even Point:** Given the $3M initial investment and $2M annual revenue, the project is expected to reach a net-positive ROI by Q3 of the second year of operation, accounting for maintenance and cloud infrastructure costs.
*   **Market Expansion:** Successful deployment serves as a case study for at least five other identified prospects in the shipping sector, potentially scaling the vertical to $10M+ ARR within 24 months.

### 1.4 Strategic Objectives
The primary goal is to deliver a stable, secure, and PCI DSS Level 1 compliant environment where the ML model can ingest real-time logistics data and output actionable routing decisions. The success of the project hinges on the ability to move from a research-grade model to a production-grade enterprise service without compromising security or reliability.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Architectural Philosophy
Project Ingot utilizes a "boring technology" stack to minimize operational complexity and maximize reliability. By leveraging a Ruby on Rails monolith, the team can focus on the ML integration rather than managing a complex microservices mesh. 

**The Stack:**
*   **Language/Framework:** Ruby on Rails 7.1 (API mode)
*   **Database:** MySQL 8.0 (Amazon RDS)
*   **Infrastructure:** Heroku Enterprise
*   **ML Integration:** Python-based sidecar service interacting via a secure internal API.

### 2.2 CQRS and Event Sourcing
Due to the audit-critical nature of shipping and financial transactions, Ingot implements Command Query Responsibility Segregation (CQRS) with Event Sourcing. 

*   **Command Side:** Handles the intent to change state (e.g., `UpdateShipmentRoute`). These are validated and persisted as an immutable sequence of events in an `event_store` table.
*   **Query Side:** Projections are built from the event store into optimized MySQL tables for fast read access.
*   **Auditability:** Because every state change is an event, the system provides a perfect audit trail, essential for PCI DSS compliance and regulatory shipping oversight.

### 2.3 ASCII Architecture Diagram
The following describes the data flow and system components:

```text
[ Client Interface ]  <---> [ Heroku Load Balancer ]
                                     |
                                     v
                      [ Ruby on Rails Monolith (v7.1) ]
                      /              |               \
      (Command Path) /               |                \ (Query Path)
     [ Event Store ] <--- [ Event Processor ] ---> [ Projection Tables ]
            |                        |                      |
            +------------------------+----------------------+
                                     |
                                     v
                        [ ML Model Sidecar (Python) ]
                                     |
                        [ MySQL RDS (PCI Compliant) ]
```

### 2.4 Deployment Pipeline
The deployment process is intentionally conservative. There is no continuous deployment (CD) to production. Instead:
1.  **Development:** Local development in Docker.
2.  **Staging:** Automatic deploy on merge to `main`.
3.  **QA Gate:** A manual sign-off is required from Cora Liu or a designated QA lead.
4.  **Production:** Manual trigger.
5.  **Turnaround:** The window from "Code Complete" to "Production" is exactly 2 days to allow for rigorous regression testing.

---

## 3. DETAILED FEATURE SPECIFICATIONS

### 3.1 User Authentication and Role-Based Access Control (RBAC)
*   **Priority:** High | **Status:** Blocked
*   **Description:** This is the core security layer of the Ingot platform. The system must ensure that users from different shipping entities cannot see each other's data and that administrative privileges are strictly controlled.
*   **Functional Requirements:**