# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles. This separation of concerns is the key to its complex behavior.

-   **The "Router" (Dispatcher):** The entry point. It quickly analyzes a user's request and decides which of the three execution tracks to send it down.
-   **The "Handyman" (Simple Executor):** A fast-lane agent that handles simple, single-step tool commands.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for complex tasks.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, managing data piping and correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector that validates the outcome of each step in a complex plan.
-   **The "Editor" (Reporter):** The unified voice of the agent. It provides direct answers to simple questions or synthesizes the results of tool use and complex plans into a final report.

## ✅ COMPLETED FEATURES

-   **Stateful Task Management:** The application is centered around persistent "Tasks", each with a unique workspace and a complete chat history.
-   **Advanced UI Rendering & Control:** A sophisticated UI visualizes the agent's operations in real-time. This includes a hierarchical event log, live step-execution status, and dynamic model selection.
-   **Multi-Level Self-Correction:** The agent can robustly handle errors. The `Site Foreman` attempts to fix failed steps, and if it cannot, it escalates the problem to the `Chief Architect` to formulate a new plan.
-   **Three-Track Brain:** The agent efficiently routes requests for Direct Q&A, Simple Tool Use, or Complex Projects down separate, optimized paths.
-   **Interactive Human-in-the-Loop (HITL):** For complex projects, the user is presented with the Architect's initial plan in a user-friendly GUI. They can edit, add, delete, or reorder steps before approving the plan for execution.

## 🚀 NEXT FOCUS: True Conversational Memory

With the core architecture and UI in place, our next and highest priority is to give the agent true multi-turn contextual awareness.

-   **Goal:** For every new request within a task, the **entire chat history** for that task must be fed back into the agent's prompts, especially for the `Router`, `Handyman`, and `Chief_Architect`.
-   **Impact:** This is the final step to unlock true iterative workflows and allow the agent to understand follow-up commands like:
    -   "OK, now refactor the script you just wrote."
    -   "Analyze the 'results.csv' file you created in the previous step."
    -   "What were the results of the last command I ran?"
