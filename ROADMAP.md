### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED PHASES

-   \[x\] **Phase 0-16:** Core Engine, Advanced Tooling, & UI Foundation.
-   \[x\] **Phase 17 (Tasks 1 & 2):** Board of Experts proposal, user approval gates, and autonomous planning loop.

### 🚀 UPCOMING PHASES 🚀

#### Phase 17: The Autonomous Board of Experts & Company Model

_Goal: Implement the full, two-part agent architecture where the Board of Experts acts as an autonomous strategic planner and the Company Model acts as a resilient execution engine, communicating the entire process through a clear, chronological UI narrative._

-   \[x\] **Task 1: Initial User Authorization Gates.**
-   \[x\] **Task 2: Autonomous Sequential Plan Refinement.**
-   \[ \] **Task 3: Hierarchical Execution & Self-Correction Loop (NEW INCREMENTAL PLAN)**
    -   **Our Philosophy:** We will build the execution engine one node at a time. After adding each node, we will test it to ensure a corresponding card appears correctly in the UI before proceeding to the next.
    -   \[ \] **Sub-task 3.1: The Master Router.** Implement the `master_router` as the entry point after plan approval. It will read the first strategic step and route to the `chief_architect_node`.
    -   \[ \] **Sub-task 3.2: The Chief Architect.** Implement the `chief_architect_node`. It will receive one strategic step and expand it into a hardcoded, placeholder "tactical plan." It will then route to the `site_foreman_node`.
    -   \[ \] **Sub-task 3.3: The Site Foreman.** Implement the `site_foreman_node`. It will read the first step of the tactical plan and prepare the tool call for the `worker_node`.
    -   \[ \] **Sub-task 3.4: The Worker.** Implement the `worker_node`. It will receive the prepared tool call and execute it using the `tool_executor`.
    -   \[ \] **Sub-task 3.5: The Project Supervisor.** Implement the `project_supervisor_node`. It will receive the worker's output and make a hardcoded "success" evaluation.
    -   \[ \] **Sub-task 3.6: The Tactical Router & Loop.** Implement the `tactical_step_router` and the incrementers to correctly loop through all tactical steps. Once the tactical plan is complete, it will route back to the `master_router`.
-   \[ \] **Task 4: Autonomous Checkpoint Review Cycle.**
-   \[ \] **Task 5: The User Guidance Escalation Path.**

#### Phase 18: Production-Grade Backend Infrastructure

_Goal: Evolve the backend from a prototype to a scalable, resilient, and persistent system._

-   \[ \] Task 1: Database Integration (SQLite & SQLAlchemy): Integrate a portable database for all state persistence.
-   \[ \] Task 2: Task Queue Integration (Dramatiq & Redis): Decouple the API from long-running agent jobs.

#### Phase 19: User Management & Authentication

_Goal: Transform the application into a secure, multi-user platform._

-   \[ \] Task 1: Authentication Service: Integrate a provider to handle logins.
-   \[ \] Task 2: Secure API Key Management: Build a system for users to store their own encrypted API keys.

#### Phase 20: Intelligent Agent Capabilities

_Goal: Enhance the core intelligence and capabilities of the agent itself._

-   \[ \] **Task 1: The Intelligent Blueprint System:** Implement the full blueprint architecture, including the `plan_expander_node`, to allow the agent to discover and use pre-defined multi-step plans as high-level tools.
-   \[ \] **Task 2: The "Committee of Critics":** Evolve the `critique_document` tool into the advanced multi-persona system we brainstormed, where a panel of AI experts collaborates to provide a comprehensive review.
-   \[ \] **Task 3: MCP Tool Integration:** Develop a wrapper to allow the agent to connect to the Model Context Protocol (MCP) tool ecosystem, dramatically expanding its available tools.
