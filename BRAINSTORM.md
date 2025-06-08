# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles:

-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for each task.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, handling data piping and managing correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions from the Controller and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector with the power to validate steps, halt execution, or even trigger a complete re-plan.

## Workspace & Security: The Sandbox Model

This is a critical architectural decision for security, reproducibility, and multi-tenancy.

-   **Hierarchical Structure:** A top-level `/workspace` directory, with subdirectories for each unique task or chat session (e.g., `/workspace/<task_id>/`).
-   **Scoped Tools:** All file system and execution tools are "workspace-aware" and operate only within the secure sandbox for the current task.
-   **File-Based Memory:** The agent passes data between steps by reading and writing to files within its workspace, providing a clear and persistent audit trail.

## Frontend & UI Design Philosophy

Our UI aims to be transparent, controllable, and professional.

-   **Target Aesthetic (`manus.ai`):** We are inspired by the clean, information-dense, dark-themed UI of `manus.ai`.
-   **Flexible Layout:** The main panels (chat/log and workspace) will be resizable, allowing the user to focus on what's important.
-   **Multi-Functional Workspace Panel:** The right-side panel will serve as both a **file browser** (listing files in the sandbox) and an **Artifact Viewer** (rendering images, markdown, code with syntax highlighting, CSVs as tables, etc.). It should also be collapsible or movable.
-   **Core UX:** The central view will remain a dynamic, hierarchical log of the agent's real-time thoughts and actions.
-   **UX Enhancements:** Small but critical features like a "Copy to Clipboard" button for code blocks and other text outputs will be integrated throughout the UI.

## Future Capabilities & Tool Development

To become a true research assistant, the agent's capabilities must grow.

-   **Scientific Tools:**
    -   PubMed search tool.
    -   Wrappers for command-line bioinformatics tools (e.g., BLAST).
    -   Connectors for scientific databases via APIs.
-   **Software Engineering Tools:**
    -   A dedicated, stateful `GitTool` for cloning, status checks, committing, and pushing.
    -   A sandboxed `Python & R Package Installer` that manages dependencies within a task-specific virtual environment.
-   **Data Interaction Tools:**
    -   A robust `File Uploader` so users can provide their own datasets.
    -   A `Database Tool` for executing SQL queries against user-provided databases.
    -   An advanced `Web Browser` tool (using Selenium/Playwright) for interacting with JavaScript-heavy websites.

## Advanced Concepts

-   **Self-Correction:** The agent should be able to recover from errors. If a Python script fails with `ModuleNotFoundError`, the agent should be able\_ to attempt a `pip install` command within the task's virtual environment and retry the step.
-   **Cost & Token Tracking:** The UI should provide transparency into token usage for each step, comparing cloud model costs versus local Ollama models.
-   **Persistence:** All chat histories, agent plans, logs, and generated artifacts must be saved to a database for true reproducibility.
