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

## 🚀 NEXT FOCUS: Phase 12.5: Concurrent Agent Execution & Control (REVISED PLAN)

_**Vision:** Refactor the server's core execution logic to enable true parallel processing of multiple agent tasks and give the user explicit control to stop any running task._

### The Concurrency Bug & Revised Plan

-   **The Problem:** Testing has revealed two critical flaws: 1) The agent process terminates itself when it pauses for human approval. 2) Closing a browser tab (and its WebSocket connection) incorrectly cancels the associated background agent task. The core issue is that the agent's lifecycle is too tightly coupled to the WebSocket connection's lifecycle.
-   **The New Plan (Per Project Lead's Direction):**
    1.  **Isolate & Simplify:** We will first create a new, minimal test script (`test_concurrency.py`) to solve the core problem in isolation. This script will not use LangGraph.
    2.  **Prove the Pattern:** The test script will demonstrate a robust producer-consumer pattern where a background `worker` task can run to completion, totally independent of WebSocket connections opening or closing. It will use an `asyncio.Queue` to hold messages.
    3.  **Implement in Main App:** Once the pattern is proven in the simple test script, we will confidently transfer that exact architecture back into `server.py`. This ensures we are building on a solid foundation.

### Technical Blueprint for `test_concurrency.py`

-   **Global State:** A dictionary to hold references to running worker tasks and another to hold message queues for each task (`WORKER_QUEUES`).
-   **`worker` function:** An `async` function that simulates a long job (e.g., looping for 10 seconds). In each loop, it prints a message to the console and `puts` a message into its dedicated queue.
-   **`message_sender` function:** An `async` function that runs per-connection. It continuously `gets` messages from all active queues and sends them to the client.
-   **`main_handler` function:** The main WebSocket handler. It will:
    -   On connection, start a `message_sender` task for that client.
    -   On receiving a "start" message, it will use `asyncio.create_task` to launch a new `worker` in the background, ensuring it is _not_ cancelled when the client disconnects.
    -   On disconnection, it will _only_ clean up the `message_sender` task, leaving the `worker` tasks untouched.
