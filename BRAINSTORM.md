# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles. This separation of concerns is the key to its complex behavior.

-   **The "Router" (Dispatcher):** Quickly classifies user requests into one of three tracks: Direct Q&A, Simple Tool Use, or Complex Project.
-   **The "Memory Updater" (Librarian):** A critical pre-processing step that analyzes every user message to update the agent's structured JSON "Memory Vault," ensuring all new facts are stored before any action is taken.
-   **The "Handyman" (Simple Executor):** A fast-lane agent that handles simple, single-step tool commands.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for complex tasks.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, managing data piping and correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector that validates the outcome of each step in a complex plan.
-   **The "Editor" (Reporter):** The unified voice of the agent, capable of acting as a conversational assistant or a project manager to deliver context-aware final responses.

## ✅ COMPLETED FEATURES

-   **Stateful Task Management:** The application is centered around persistent "Tasks", each with a unique workspace and a complete chat history.
-   **Advanced UI Rendering & Control:** A sophisticated UI visualizes the agent's operations in real-time.
-   **Multi-Level Self-Correction:** The agent can robustly handle errors by retrying steps or creating entirely new plans.
-   **Three-Track Brain & Interactive HITL:** The agent efficiently routes requests and allows users to review and modify complex plans before execution.
-   **Robust Memory & Environments:** The agent uses a "Memory Vault" for persistent knowledge and automatically creates isolated Python virtual environments for each task.
-   **Interactive Workbench v1:** A functional file explorer with structured listing, navigation, create/rename/delete actions, drag-and-drop upload, and a smart previewer for text, images, Markdown, and CSVs.

## 🚀 NEXT FOCUS: Phase 12.5: Concurrent Agent Execution & Control

_**Vision:** Refactor the server's core execution logic to enable true parallel processing of multiple agent tasks and give the user explicit control to stop any running task._

### The Concurrency Bug & Solution

-   **The Problem:** The current WebSocket handler (`run_agent_handler`) uses `await` directly on the `agent_graph.astream_events` call. This is a _blocking_ operation. While it's running, the server cannot process any other incoming messages, such as a request to start a second agent on a different task. If a second request comes in, the first one is effectively terminated.
-   **The Solution:** We must change the handler to be non-blocking. The correct approach is to wrap the agent execution in `asyncio.create_task()`. This immediately schedules the agent to run in the background and returns control to the message handler, allowing it to process new requests. This will enable true, concurrent agent runs.

### The "Stop" Functionality

-   **Goal:** Provide a way for the user to terminate a long-running or misbehaving agent task without shutting down the server.
-   **Backend Implementation:**
    1.  **Task Tracking:** Create a global dictionary on the server (e.g., `RUNNING_TASKS = {}`).
    2.  **Store Task Reference:** When `asyncio.create_task()` is called for a new agent run, store the resulting `Task` object in the dictionary with the `task_id` as the key.
    3.  **Cleanup:** When the task finishes naturally, remove its entry from the dictionary.
    4.  **New WebSocket Handler:** Create a new handler for a `"stop_agent"` message type. This handler will receive a `task_id`.
    5.  **Cancellation:** The handler will look up the task in `RUNNING_TASKS` using the `task_id`, call the `.cancel()` method on it, and then remove it from the dictionary.
-   **Frontend Implementation:**
    1.  **Conditional Button:** In `src/App.jsx`, display a "Stop" button next to the "Send" button _only_ when the `isThinking` state is true.
    2.  **Send Message:** The `onClick` handler for this button will send a WebSocket message: `{ "type": "stop_agent", "task_id": activeTaskId }`.
    3.  The UI will naturally update to show the agent has stopped when the `isThinking` state is reset to `false` by the backend.

### Future Ideas: Pause/Resume

-   **Concept:** A true "Pause" functionality is much more complex than "Stop." It would require serializing the entire state of the LangGraph execution at the exact point it was paused and then being able to perfectly restore it later.
-   **Status:** This is a high-complexity feature to be considered for a much later version of the application.
