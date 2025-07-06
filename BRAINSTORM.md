### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED PHASES

-   \[x] **Phase 0-16:** Core Engine, Advanced Tooling, & UI Foundation.
-   \[x] **Phase 17 (Tasks 1 & 2):** Board of Experts proposal, user approval gates, and autonomous planning loop.

### 🚀 UPCOMING PHASES 🚀

#### Phase 17: The Autonomous Board of Experts & Company Model

_Goal: Implement the full, two-part agent architecture where the Board of Experts acts as an autonomous strategic planner and the Company Model acts as a resilient execution engine, communicating the entire process through a clear, chronological UI narrative._

-   \[x] **Task 1: Initial User Authorization Gates.**
-   \[x] **Task 2: Autonomous Sequential Plan Refinement.**
-   \[x] **Task 3: Hierarchical Execution Loop.** (Placeholder nodes are fully wired).
    -   \[x] **Sub-task 3.1: The Master Router.**
    -   \[x] **Sub-task 3.2: The Chief Architect.**
    -   \[x] **Sub-task 3.3: The Site Foreman.**
    -   \[x] **Sub-task 3.4: The Worker.**
    -   \[x] **Sub-task 3.5: The Project Supervisor.**
    -   \[x] **Sub-task 3.6: The Tactical Router & Loop.**
-   \[x] **Task 4: Autonomous Checkpoint Review Cycle.**
-   \[ \] **Task 5: The User Guidance Escalation Path (IN PROGRESS)**
    - \[ \] Implement the `escalate` decision logic in the `board_checkpoint_review_node`.
    - \[ \] Add the `human_in_the_loop_user_guidance` node and interrupt.
    - \[ \] **NEXT UP:** Fully test and debug the end-to-end user guidance workflow to ensure the UI card appears correctly and the agent resumes with the new guidance.

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
