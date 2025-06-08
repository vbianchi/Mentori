# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-4: Core Backend Engine

-   \[x\] **Project Setup:** Established the complete project structure, including Docker, dependencies, and all documentation.
-   \[x\] **Agent Foundation:** Built the core WebSocket server and a basic LangGraph agent.
-   \[x\] **Advanced PCEE Architecture:** Successfully implemented the full Plan-Controller-Executor-Evaluator loop with memory and data piping between steps.
-   \[x\] **Core Capabilities:** The agent can autonomously create and execute structured, multi-step plans using web search, shell commands, and file I/O.
-   \[x\] **Sandboxing:** Implemented the foundational system for creating and using secure, per-task workspaces.
**Status: Completed**

### Phase 5: Core Frontend & Workspace Interaction

-   \[x\] **Build System & Initial UI:** Set up a modern frontend environment (Vite + Preact) and rendered the initial UI structure.
-   \[x\] **Live Event Stream:** Implemented JavaScript logic to connect to the WebSocket and render the agent's real-time event stream.
-   \[ \] **Workspace File Browser:** Implement a UI component in the "Agent Workspace" panel that periodically fetches and displays the file list from the agent's current workspace directory.
-   \[ \] **Artifact Viewer:** Enhance the file browser so that clicking a file (e.g., an image, `.md`, `.py`) renders its content directly in the panel.
-   \[ \] **File Upload Tool:** Create a new tool and a UI component to allow users to upload files into the agent's workspace.
-   \[ \] **Copy to Clipboard:** Add a "copy" button to code blocks and other relevant UI elements.
**Status: In Progress**

### Phase 6: UI Polish & Advanced Controls

-   \[ \] **Layout & Styling:** Refine the UI to more closely match the `manus.ai` aesthetic, including implementing resizable and collapsible panels.
-   \[ \] **Token Consumption Tracking:** Implement backend logic and UI elements to display token usage estimates for each step.
-   \[ \] **Dynamic Model Selection:** Add UI controls (e.g., dropdowns) to allow the user to change the LLM for each agent role (Planner, Controller, etc.) on the fly.
**Status: Up Next**

### Phase 7: Human-in-the-Loop (HITL) Integration

-   \[ \] **Stop/Pause Button:** Implement the backend logic and frontend button to allow pausing and resuming of the agent's execution loop.
-   \[ \] **High-Stakes Confirmation:** Create a special `HITL` node in the graph for potentially destructive actions, requiring user confirmation via the UI before proceeding.
-   \[ \] **Plan Editing:** A future goal to allow users to edit the agent's plan while it is paused.

### Phase 8: Persistence & Reproducibility

-   \[ \] **Database Integration:** Integrate a database (e.g., SQLite) to store all session data.
-   \[ \] **Persistent Chat History:** Save and load user conversations and agent responses.
-   \[ \] **Task Archiving:** Store the full agent state, including the plan, step history, and generated artifacts for every task, allowing for perfect reproducibility.

### Phase 9: Ongoing Capability Expansion

-   \[ \] **New Tools:** Continuously add new tools as outlined in the `BRAINSTORM.md` file (e.g., Git, PubMed, Package Installers).
