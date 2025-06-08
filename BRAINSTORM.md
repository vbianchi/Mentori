# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project. It's a space for high-level thinking, separate from the formal `ROADMAP.md`.

## Core Agent Architecture: The "Company" Model

Our evolution from a simple agent to a sophisticated, multi-node graph is the core of this project. We think of our agent less like a single entity and more like a small, efficient company with specialized roles.

-   **The "Chief Architect" (Planner):** Our `structured_planner_node`. It's a strategic thinker that takes a complex user request and breaks it down into a detailed, structured JSON "blueprint" (the plan), including tool choices and expected outcomes.
-   **The "Site Foreman" (Controller):** Our new `controller_node`. It's the project manager, executing the Planner's blueprint step-by-step. Its key job is to manage the execution loop and perform **data piping** by substituting placeholders like `{step_1_output}` with actual results from previous steps.
-   **The "Worker" (Executor):** Our `executor_node`. It's the hands-on specialist that simply takes a precise tool call from the Controller and executes it.
-   **The "Project Supervisor" (Evaluator):** Our `evaluator_node`. It's the quality assurance inspector that assesses if a completed step truly met its goal. It has the power to halt the plan if something goes wrong.

## Workspace & Security: The Sandbox Model

This is a critical architectural decision for security and multi-tenancy.

-   **Hierarchical Structure:** A top-level `/workspace` directory, with subdirectories for each unique task or chat session (e.g., `/workspace/<task_id>/`). In a full multi-user system, this would become `/workspace/<user_id>/<task_id>/`.
-   **Scoped Tools:** All file system tools **must** be workspace-aware, receiving the unique `workspace_path` to ensure all operations are contained within the sandbox.
-   **File-Based Memory:** Instead of passing large data blobs in the agent's state, the agent's plan should rely on reading and writing to files within its workspace (e.g., "Step 1: Save search results to `step_1_output.json`", "Step 2: Read `step_1_output.json` to extract the data.").

## Frontend & UI

-   **Tech Stack:** We have successfully implemented a modern frontend stack using **Vite + Preact + Tailwind CSS**. This provides a fast development server, a robust component model, and a powerful utility-first styling framework.
-   **Dynamic Event Log:** The core of the UI is a real-time log that visualizes the stream of events from the agent, showing the hierarchical structure of the plan as it executes.
-   **Workspace File Browser:** A key upcoming feature is a live-updating panel that displays the contents of the agent's current sandboxed workspace. This is crucial for user transparency and debugging.

## Advanced Self-Correction Ideas

This is the next frontier after our basic loop and UI are stable.

-   **Dependency Installation:** If the agent gets a `ModuleNotFoundError`, the Evaluator should not just fail. It should recognize the error and trigger a correction sub-loop, instructing the Controller to `pip install <missing_library>` into a task-specific virtual environment.
-   **Smarter Evaluation & Re-Planning:** If the Evaluator determines a step succeeded technically but failed logically (e.g., it got the wrong information), it could trigger a "re-plan" event, sending the task back to the Planner with new context about what went wrong.

## Human-in-the-Loop (HITL) Features

This is a long-term goal for making the agent truly collaborative.

-   **Pause & Resume:** The user should be able to pause the agent's execution loop between any two steps.
-   **High-Stakes Confirmation:** For potentially destructive or costly actions (e.g., `rm -rf`, `git push --force`), the agent should route to a special `HITL` node, pause, and wait for explicit user confirmation before proceeding.
