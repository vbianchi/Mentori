# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-6: Core Engine, UI & Stability

-   \[x\] **Core Backend Engine:** The foundational PCEE architecture with Router, Planner, Controller, Executor, and Evaluator nodes is stable.
-   \[x\] **Core Frontend & Workspace:** The UI is fully functional with a live event stream, interactive workspace, artifact viewer, and file uploading.
-   \[x\] **Advanced Controls & Stability:** Dynamic model selection is implemented, and the agent is stable for both simple QA and complex, long-running plans.

### Phase 7: Persistence, History & Task Management \[UP NEXT\]

-   \[ \] **Stateful Sessions:** Transition from a stateless model to stateful "Tasks". Each new conversation will be a persistent task with its own unique workspace and history.
-   \[ \] **Task Management UI:** Implement the UI for managing tasks in the left-hand panel. This will include creating a new task and listing existing ones.
-   \[ \] **Backend Task Logic:** Update the backend WebSocket handler to manage tasks. It will receive a `task_id` and either create a new workspace or resume work in an existing one.
-   \[ \] **Conversational Memory:** Feed the chat history for a given task back into the agent's prompts. This will give the agent the context of previous turns, allowing for follow-up questions and iterative work.
-   \[ \] **Basic User Abstraction:** Introduce a concept of a `user_id` to associate tasks with a specific user, laying the groundwork for future multi-user support.

### Phase 8: Advanced Self-Correction & Environment Management

-   \[ \] **Smarter Evaluator:** Enhance the `Project_Supervisor` with more nuanced analysis of tool output.
-   \[ \] **Correction Sub-Loop:** Implement the logic for the agent to attempt corrective actions when a step fails.
-   \[ \] **Python Virtual Environments:** Implement full dependency sandboxing with per-task `.venv` directories.

### Phase 9: Human-in-the-Loop (HITL) Integration

-   \[ \] **Stop/Pause Button:** Implement controls to pause and resume the agent's execution loop.
-   \[ \] **High-Stakes Confirmation:** Create a special `HITL` node for actions that require user confirmation.

### Phase 10: Full Database Integration & Reproducibility

-   \[ \] **Database Integration:** Replace the in-memory/file-based session storage with a robust database (e.g., SQLite or PostgreSQL) to store all session data.
-   \[ \] **Task Archiving & History:** Store and retrieve the full state of previous tasks, allowing for perfect reproducibility.
