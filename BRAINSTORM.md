# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles, creating a clear separation of concerns that enables complex behavior.

-   **The "Router" (Dispatcher):** The entry point. It quickly analyzes a user's request and decides if it's a simple question that can be answered directly or a complex task that requires the full project team.
-   **The "Librarian" (Direct QA):** The fast-response expert. Handles simple, direct questions without the overhead of the full planning process.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for each complex task.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, managing data piping and managing correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions from the Controller and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector with the power to validate steps, halt execution, or (in the future) trigger a correction loop.

## ✅ **COMPLETED:** Stateful Task Management & UI

We have successfully evolved the agent from a stateless, single-shot tool into a persistent, multi-turn assistant.

-   **Task as the Core Unit:** The application is now centered around the "Task". Each task has its own unique `task_id`, a sandboxed workspace on the file system, and a complete, ordered chat history that is persisted in the browser's `localStorage`.
-   **Advanced UI Rendering:** The frontend has been refactored into a clean, component-based architecture. It now features a sophisticated and unified UI that clearly visualizes the contributions of each agent in the "Company Model." This includes a visual thread to show the flow of information and real-time status updates (pending, in-progress, completed, failed) for each step of the execution plan.

## 🚀 **NEXT FOCUS:** True Autonomy and Intelligence

With the stateful foundation in place, our next focus is on elevating the agent's intelligence by giving it memory and the ability to recover from errors.

### **1\. Conversational Memory**

This is the highest priority. The agent's real power will come from understanding the full context of a conversation.

-   **Goal:** For every new request within a task, the _entire chat history_ for that task must be fed back into the agent's prompts, especially for the `Chief_Architect` and `Site_Foreman`.
-   **Impact:** This will unlock iterative workflows and allow the agent to understand follow-up commands like:
    -   "OK, now refactor the script you just wrote."
    -   "Analyze the 'results.csv' file you created in the previous step."
    -   "What were the results of the last command I ran?"

### **2\. Self-Correction Sub-Loop**

The agent should not fail on the first error. Our architecture is designed to support a self-healing mechanism.

-   **The Trigger:** When the `Project_Supervisor` evaluates a step and returns a `failure` status, the agent should not give up.
-   **The `Correction_Planner` Node:** We will introduce a new agent node whose sole job is to fix mistakes.
    -   **Input:** The failed step's instruction and the Supervisor's evaluation feedback (e.g., "File not found.").
    -   **Action:** Formulate a _new, single-step plan_ to fix the immediate problem (e.g., "I should use the `web_search` tool first to gather the information before trying to read a file.").
    -   **Output:** A revised tool call.
-   **The Loop:** The graph will route to this new node upon failure, execute the corrected step, and then attempt to resume the original plan.

### **3\. Human-in-the-Loop (HITL) - Plan Approval**

The user must have ultimate control. The UI we've built is the perfect foundation for introducing human oversight.

-   **The `ArchitectCard` as a Control Point:** The UI now displays the `Chief_Architect`'s proposed plan before execution begins.
-   **Goal:** Add "Approve" and "Modify" buttons to this card.
    -   **Approve:** The user agrees with the plan, and the `Site_Foreman` begins execution.
    -   **Modify:** The user can edit the plan's instructions or tool choices before execution starts. This would send the modified plan back to the backend.
-   **Backend HITL Node:** This requires a special node in the graph that pauses execution and waits for a specific "approval" event from the user via the WebSocket.

### **4\. Advanced File Viewing**

The workspace panel is functional but basic. We can make it much more powerful.

-   **Goal:** Upgrade the file viewer to be content-aware.
-   **Implementation:**
    -   `.md` files should be rendered as rich, formatted HTML using the `marked` library.
    -   `.png`, `.jpg`, `.svg` files should be rendered as images (`<img>` tags).
    -   `.pdf` files could be rendered in an `<iframe>`
