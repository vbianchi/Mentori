### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED PHASES

-   \[x\] **Phase 12: The Interactive Workbench:** Evolved the workspace from a simple file list into a full-featured, interactive file explorer.
-   \[x\] **Phase 12.5: Concurrent Agent Execution & Control:** Refactored the backend server to handle multiple, simultaneous agent runs and provided users with the ability to stop a running task.
-   \[x\] **Phase 13: The "Tool Forge" (v1):** Implemented the foundational "LLM as an Engine" Tool Forge.
-   \[x\] **Phase 14: UI & Agent Simplification:** Refactored the UI and removed early blueprint logic to focus on core tooling.
-   \[x\] **Phase 15: Advanced Tooling (v1):** Equipped the agent with a suite of powerful, pre-built tools for common high-value tasks, including `query_files` and `critique_document`.
-   \[x\] **Phase 16: UI Polish & Enhanced File Interaction:** Overhauled the UI with a high-contrast theme, redesigned settings panels, and implemented inline file/folder creation, multi-file uploads, and other UX improvements.

### 🚀 UPCOMING PHASES 🚀

#### Phase 17: Production-Grade Backend Infrastructure

_Goal: Evolve the backend from a prototype to a scalable, resilient, and persistent system, inspired by best practices from projects like Suna._

-   \[ \] **Task 1: Database Integration:** Integrate **SQLite** for portable and simple persistence. Use the **SQLAlchemy ORM** to abstract database interactions, allowing for a future migration to a larger system like Postgres if needed.
-   \[ \] **Task 2: Task Queue Integration:** Replace the current `asyncio` background tasks with a robust task queue system like **Dramatiq with a Redis broker**. This will decouple the API from long-running agent jobs.
-   \[ \] **Task 3: State Migration:** Refactor the agent and server to read and write all state (chat history, agent memory, task definitions) to the new SQLite database instead of being transient.

#### Phase 18: User Management & Authentication

_Goal: Transform the application from a single-user tool to a secure, multi-user platform._

-   \[ \] **Task 1: Authentication Service:** Integrate a flexible authentication provider (e.g., Supabase Auth, Auth0) to handle user logins.
-   \[ \] **Task 2: Multi-Provider SSO:** Configure the authentication service to support multiple OAuth providers, specifically **Microsoft, Google, and GitHub**.
-   \[ \] **Task 3: Secure API Key Management:** Build a UI and backend system for users to securely store their own API keys, encrypted at rest in the database.

#### Phase 19: Advanced Sandboxing & Collaboration

_Goal: Implement full isolation between tasks and introduce foundational collaboration features._

-   \[ \] **Task 1: Per-Task Docker Sandboxes:** Refactor the task queue worker to use the **Docker SDK for Python** to programmatically start and stop isolated containers for each agent task, mounting the appropriate workspace directory.
-   \[ \] **Task 2: The "Organization" Model:** Implement the database schema and backend logic for "Organizations" to enable multi-tenancy, laying the groundwork for shared tasks.

#### Phase 20: Intelligent Agent Capabilities

_Goal: Enhance the core intelligence and capabilities of the agent itself._

-   \[ \] **Task 1: The Intelligent Blueprint System:** Implement the full blueprint architecture, including the `plan_expander_node`, to allow the agent to discover and use pre-defined multi-step plans as high-level tools.
-   \[ \] **Task 2: The "Committee of Critics":** Evolve the `critique_document` tool into the advanced multi-persona system we brainstormed, where a panel of AI experts collaborates to provide a comprehensive review.
-   \[ \] **Task 3: MCP Tool Integration:** Develop a wrapper to allow the agent to connect to the Model Context Protocol (MCP) tool ecosystem, dramatically expanding its available tools.
