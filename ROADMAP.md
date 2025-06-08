# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-4: Core Backend Engine

-   \[x\] **Project Setup:** Established the complete project structure, including Docker configuration, dependencies, and all documentation.
-   \[x\] **Agent Foundation:** Built the core WebSocket server and a basic LangGraph agent.
-   \[x\] **Advanced PCEE Architecture:** Successfully implemented the full Plan-Controller-Executor-Evaluator loop with memory and data piping between steps.
-   \[x\] **Core Capabilities:** The agent can autonomously create and execute structured, multi-step plans using web search, shell commands, and file I/O.
-   \[x\] **Sandboxing:** Implemented the foundational system for creating and using secure, per-task workspaces.
**Status: Completed**

### Phase 5: Frontend Development & UI Integration

-   \[x\] **Build System:** Set up a modern frontend environment using Vite, Preact, and Tailwind CSS.
-   \[x\] **Initial UI:** Created the foundational `index.html`, `App.jsx`, and supporting files for the main UI structure.
-   \[x\] **Live Event Stream:** Implemented JavaScript logic to connect to the WebSocket and render the real-time stream of agent events.
-   \[ \] **Workspace File Browser:** Implement a UI component in the "Agent Workspace" panel that periodically fetches and displays the file list from the agent's current workspace directory.
-   \[ \] **Finalize UI Polish:** Refine styles, add loading states, and improve the overall user experience.
**Status: In Progress**

### Phase 6: Advanced Self-Correction & Environment Management

-   \[ \] **Smarter Evaluator:** Enhance the evaluator to understand a wider range of errors beyond simple text matching.
-   \[ \] **Correction Sub-Loop:** Upgrade the Controller to attempt corrective actions when a step fails (e.g., installing a missing dependency).
-   \[ \] **Python Virtual Environments:** Implement the full sandboxing plan by having the agent create and use a unique `.venv` for each task.
**Status: Up Next**

### Phase 7: Human-in-the-Loop (HITL) Integration

-   \[ \] Implement a `pause/resume` mechanism in the agent's execution loop.
-   \[ \] Create a special `HITL` node in the graph for high-stakes actions that require user confirmation.
**Status: Future**
