# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-4: Core Backend Engine

-   \[x\] **Project Setup:** Established the complete project structure, including Docker, dependencies, and all documentation.
-   \[x\] **Agent Foundation:** Built the core WebSocket server and a basic LangGraph agent.
-   \[x\] **Advanced PCEE Architecture:** Successfully implemented the full Plan-Controller-Executor-Evaluator loop with memory and data piping between steps.
-   \[x\] **Core Capabilities:** The agent can autonomously create and execute structured, multi-step plans using web search, shell commands, and file I/O.
-   \[x\] **Sandboxing:** Implemented the foundational system for creating and using secure, per-task workspaces. **Status: Completed**

### ✔️ Phase 5: Core Frontend & Workspace Interaction

-   \[x\] **Build System & Initial UI:** Set up a modern frontend environment (Vite + Preact) and rendered the initial UI structure.
-   \[x\] **Live Event Stream:** Implemented JavaScript logic to connect to the WebSocket and render the agent's real-time event stream.
-   \[x\] **Workspace File Browser:** Implemented a UI component that fetches and displays the file list from the agent's workspace.
-   \[x\] **Artifact Viewer:** Enhanced the file browser so that clicking a file renders its content directly in the panel.
-   \[x\] **File Upload Tool:** Created a new tool and a UI component to allow users to upload files into the agent's workspace.
-   \[x\] **Copy to Clipboard:** Added a "copy" button to code blocks and other relevant UI elements. **Status: Completed**

### Phase 6: UI Polish & Advanced Controls

-   \[x\] **Layout & Styling:** Refine the UI to more closely match the `manus.ai` aesthetic, including implementing resizable and collapsible panels.
-   \[ \] **Token Consumption Tracking:** Implement backend logic and UI elements to display token usage estimates for each step.
-   \[x\] **Dynamic Model Selection:** Add UI controls (e.g., dropdowns) to allow the user to change the LLM for each agent role (Planner, Controller, etc.) on the fly. **Status: Up Next** (Partially complete, we need to add also the ROUTER Agent in there)

### Phase 7: Advanced Self-Correction & Environment Management

-   \[ \] **Smarter Evaluator:** Enhance the `evaluator_node` to use an LLM to analyze the outcome of a step and provide structured feedback (success/failure and reasoning).
-   \[ \] **Correction Sub-Loop:** Implement the logic for the agent to attempt corrective actions when a step fails (e.g., installing a missing dependency).
-   \[ \] **Python Virtual Environments:** Implement the full sandboxing plan by having the agent create and use a unique `.venv` for each task. **Status: Not Started**

### Phase 8: Human-in-the-Loop (HITL) Integration

-   \[ \] **Stop/Pause Button:** Implement the backend logic and frontend button to allow pausing and resuming of the agent's execution loop.
-   \[ \] **High-Stakes Confirmation:** Create a special `HITL` node in the graph for potentially destructive actions, requiring user confirmation via the UI before proceeding.
-   \[ \] **Plan Editing:** A future goal to allow users to edit the agent's plan while it is paused.

### Phase 9: Persistence & Reproducibility

-   \[ \] **Database Integration:** Integrate a database (e.g., SQLite) to store all session data.
-   \[ \] **Persistent Chat History:** Save and load user conversations and agent responses.
-   \[ \] **Task Archiving:** Store the full agent state, including the plan, step history, and generated artifacts for every task, allowing for perfect reproducibility.

### Phase 10: Ongoing Capability Expansion

-   \[ \] **New Tools:** Continuously add new tools as outlined in the `BRAINSTORM.md`
