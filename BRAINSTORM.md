# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles, creating a clear separation of concerns that enables complex behavior.

-   **The "Router" (Dispatcher):** The entry point. It quickly analyzes a user's request and decides if it's a simple question that can be answered directly or a complex task that requires the full project team.
-   **The "Librarian" (Direct QA):** The fast-response expert. Handles simple, direct questions without the overhead of the full planning process.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for each complex task.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, handling data piping and managing correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions from the Controller and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector with the power to validate steps, halt execution, or (in the future) trigger a correction loop.

## Tooling Philosophy: Resilience over Rigidity

-   **Initial Approach:** Relied heavily on prompt engineering to ensure the LLM used the exact argument names defined by the tool functions.
-   **Current Approach (More Robust):** Tools should be designed to be more flexible. While our current implementation uses standardized argument names for clarity, a more advanced approach would involve using Pydantic schemas with `alias` fields. This would allow a tool function to internally use a clean, canonical argument name (e.g., `file_path`) while accepting multiple "hallucinated" variations from the LLM (e.g., `file`, `path`, `filename`). This makes the system far more resilient to minor LLM inconsistencies.


## New Focus: Persistence & Stateful Task Management

This is the next major evolution of the agent, moving it from a single-shot tool to a true assistant.

-   **Task as the Core Unit:** The central concept is the "Task" or "Session." Each task will have:
    -   A unique `task_id`.
    -   A persistent, sandboxed workspace directory on the file system.
    -   A complete, ordered chat history (`[ {user: ...}, {agent: ...} ]`).
    -   A history of all executed plans and their outcomes.
-   **Contextual Memory:** The agent's real power will come from memory. For every new request within a task, the full chat history must be fed into the Planner and Controller prompts. This will allow the agent to understand follow-up commands like:
    -   "OK, now refactor the script you just wrote."
    -   "Analyze the 'results.csv' file you created in the previous step."
    -   "What were the results of the last command I ran?"
-   **User Abstraction:** We will introduce a `user_id`. Initially, this can be a simple, randomly generated ID stored in the browser's `localStorage` to associate a user with their set of tasks. This paves the way for a full login system later.
-   **Database Backend:** While the initial implementation can use in-memory dictionaries or simple JSON files for persistence, the ultimate goal (previously Phase 9) is to migrate this to a proper database like SQLite. This is essential for performance, scalability, and preventing data loss when the server restarts. The schema would include tables for `users`, `tasks`, `messages`, and `artifacts`

## Frontend & UI Design Philosophy

Our UI aims to be transparent, controllable, and professional, inspired by information-dense tools like `manus.ai`.

-   **Dynamic & Hierarchical Event Log:** The main panel successfully streams the agent's thought process in real-time for both simple QA and complex plans.
-   **Multi-Functional Workspace Panel:** The right-side panel serves as both a file browser and an Artifact Viewer (rendering text, markdown, code, etc.). Future goal: render images, PDFs, and other complex types.
-   **Advanced Controls:** The dynamic model selection panel is a key success, giving the user fine-grained control over the "brain" used for each agent role. Future goal: Add a `STOP/PAUSE` button and token consumption display.

## Future Capabilities & Advanced Concepts

-   **Self-Correction:** The core goal of Phase 7. The agent should be able to recover from errors. If a Python script fails with `ModuleNotFoundError`, the agent should be able to diagnose the error, formulate a correction plan (e.g., `pip install <module>`), execute the fix within the task's virtual environment, and then retry the original failed step.
-   **Cost & Token Tracking:** The UI should provide transparency into token usage for each step, comparing cloud model costs versus local Ollama models. This is critical for production use.
-   **Persistence & Reproducibility:**


## New Focus: The Path to a Fully Stateful UI

We have successfully implemented the backend logic and the frontend UI for creating and deleting tasks. However, the main chat panel is not yet connected to this state. The final step of Phase 7 is to make the chat history visible and persistent for each task.

Here is the detailed, step-by-step plan to achieve this in `App.jsx`:

#### **The Core Problem: Connecting State to UI**

The `tasks` array in our frontend state now holds a `history` array for each task. Our goal is to make the UI _render_ the contents of the active task's `history`.
#### **The Step-by-Step Implementation Plan**
We will modify `App.jsx` in small, testable increments.
**Step 1: Display the User's Prompt \[IN PROGRESS\]**
-   **Goal:** When a user sends a message, it should immediately appear in the chat panel for the active task.
-   **A. Define the `PromptCard` Component:** Create a simple React component designed to display the user's prompt text.
-   **B. Add the Prompt to History:** In the `handleSendMessage` function, when a message is sent, we add an object like `{ type: 'prompt', content: message }` to the active task's `history` array.
-   **C. Render from History:** The main chat panel's render logic will be updated to map over the active task's history. If it finds an item with `type: 'prompt'`, it will render a `PromptCard` with the content.
**Step 2: Display Agent Events (The Plan)**

-   **Goal:** When the agent creates a plan, the plan should appear in the chat panel.
-   **A. Define `PlanCard` and `StepCard` Components:** Create components to display the overall plan and the individual steps within it.
-   **B. Handle WebSocket Events:** The `onmessage` handler for our WebSocket will be updated. When it receives an `agent_event` from the `Chief_Architect`, it will add a `{ type: 'plan', plan: [...] }` object to the active task's history.
-   **C. Render the Plan:** The render logic from Step 1 will be expanded. When it sees an item with `type: 'plan'`, it will render the `PlanCard`.
**Step 3: Update Plan Steps in Real-Time**

-   **Goal:** As the agent executes each step of the plan, the `StepCard` components should update their status (e.g., from "pending" to "in-progress" to "completed").
-   **A. Handle `Worker` Events:** The `onmessage` handler will be enhanced. When it receives events from the `Site_Foreman` and `Worker`, it will find the corresponding `plan` object in the history and update the `status` of the relevant step.
-   **B. Immutability is Key:** This update must be done immutably. We will create a _new copy_ of the history array and the plan object to avoid the "blank screen" bug from previous attempts.
**Step 4: Display Final Answers**

-   **Goal:** Display the final synthesized summary from "The Editor" or the direct answer from "The Librarian".
-   **A. Handle Final Answer Events:** The `onmessage` handler will listen for the `final_answer` and `direct_answer` message types from the backend.
-   **B. Add to History:** It will add a corresponding object, like `{ type: 'final_answer', content: '...' }`, to the active task's history.
-   **C. Render Final Cards:** The render logic will be updated to display a `FinalAnswerCard` or `DirectAnswerCard` when it encounters these history types.
