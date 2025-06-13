# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-6: Core Engine, UI & Stability

-   \[x\] **Core Backend Engine:** The foundational PCEE architecture with Router, Planner, Controller, Executor, and Evaluator nodes is stable.
-   \[x\] **Core Frontend & Workspace:** The UI is fully functional with a stateless event stream, interactive workspace, artifact viewer, and file uploading.
-   \[x\] **Advanced Controls & Stability:** Dynamic model selection is implemented, and the agent is stable for both simple QA and complex, long-running plans.

### ✔️ Phase 7: Stateful Task Management & UI Refinement

-   \[x\] **Stateful Sessions:** Transitioned from a stateless model to stateful "Tasks". Each new conversation is a persistent task with its own unique workspace and history stored in the browser.
-   \[x\] **Backend Task Logic:** The backend WebSocket handler now manages the full lifecycle of tasks, including creating and deleting their workspaces on the file system.
-   \[x\] **Task Management UI:** Implemented a fully functional UI for creating, selecting, renaming, and deleting tasks.
-   \[x\] **Advanced UI Rendering:** Refactored the frontend into a component-based architecture. Implemented a sophisticated and unified UI for displaying the full conversation, including the user's prompt and the distinct contributions of the Architect, Foreman, and Editor agents, complete with real-time step execution status.

### Phase 8: Conversational Memory & Contextual Awareness \[UP NEXT\]

-   \[ \] **Full Conversational History:** The complete chat history for a given task will be fed back into the agent's prompts. This is the final step to give the agent true contextual memory, allowing for iterative work and follow-up commands (e.g., "now refactor the script you just wrote").
-   \[ \] **Smarter Tool Usage:** The agent will learn to use the output of previous steps as input for subsequent steps without explicit user instruction (e.g., using a search result to inform a file-writing action).
-   \[ \] **Basic User Abstraction:** Introduce a concept of a `user_id` to associate tasks with a specific user, laying the groundwork for future multi-user support.

### Phase 9: Advanced Self-Correction & Environment Management

-   \[ \] **Self-Correction Sub-Loop:** Implement the logic for the agent to attempt corrective actions when a step fails. This will involve a new `Correction_Planner` node that analyzes the Supervisor's feedback and formulates a fix.
-   \[ \] **Smarter Evaluator:** Enhance the `Project_Supervisor` with more nuanced analysis to provide more detailed and actionable feedback for the correction loop.
-   \[ \] **Python Virtual Environments:** Implement full dependency sandboxing with per-task `.venv` directories to isolate Python tool executions.

### Phase 10: Human-in-the-Loop (HITL) Integration & Advanced UI

-   \[ \] **HITL Node & Plan Approval:** Create a special graph node that pauses execution and requires user confirmation before proceeding with high-stakes actions. This will first be implemented as an "Approve Plan" step after the Architect's proposal is displayed.
-   \[ \] **Enhanced File Viewer:** Upgrade the workspace file viewer to intelligently render different file types, including Markdown (`.md`), images (`.png`, `.jpg`), and potentially PDFs.
-   \[ \] **Real-time Stop/Pause Button:** Implement UI controls to safely interrupt and resume the agent's execution loop.

### Phase 11: Full Database Integration & Reproducibility

-   \[ \] **Database Integration:** Replace the browser-based `localStorage` with a robust database backend (e.g., SQLite) to store all task and message data, making it persistent across server restarts.
-   \[ \] **Task Archiving & History:** Store and retrieve the full state of previous tasks, allowing for perfect reproducibility and analysis of past runs.
