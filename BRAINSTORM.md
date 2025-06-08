# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project. It's a space for high-level thinking, separate from the formal `ROADMAP.md`.

## Core Agent Architecture: The "Company" Model

Our evolution from a simple ReAct agent to a more sophisticated, multi-node graph has been a key insight. We can think of our agent less like a single entity and more like a small, efficient company with specialized roles.

-   **The "Chief Architect" (Planner):**
    -   This is our `structured_planner_node`.
    -   It's responsible for high-level strategic thinking.
    -   It takes a complex user request and breaks it down into a detailed, structured JSON "blueprint" (the plan).
    -   Its key skill is decomposition and foresight, creating a complete project plan before any "work" begins.
-   **The "Site Foreman" (Controller):**
    -   This will be our new, smarter `controller_node`.
    -   It's the project manager, responsible for executing the Planner's blueprint step-by-step.
    -   **Key Responsibilities:**
        -   Reading the current step from the plan.
        -   **Data Piping:** Connecting the output of previous steps to the input of the current step (e.g., taking a file path from a `list_files` call and passing it to `read_file`).
        -   **Validation:** Performing basic checks to ensure the plan step is valid before execution.
        -   **Sub-Loops:** Managing a "self-correction" loop if a step fails, trying to fix it before giving up.
-   **The "Worker" (Executor):**
    -   Our current `executor_node`.
    -   It's the hands-on specialist. It does one thing: it takes a precise tool call from the Controller and executes it perfectly.
    -   It has no high-level understanding; it just does its job.
-   **The "Project Supervisor" (Evaluator):**
    -   Our `evaluator_node`.
    -   It's the quality assurance inspector.
    -   **Key Responsibilities:**
        -   Assessing if a completed step _truly_ met the goal of the instruction, using the tool output and the Controller's intent as context.
        -   It has executive power to halt the entire plan if something goes fundamentally wrong.
        -   Future capability: It could potentially order the Planner to create a _new_ plan from scratch if the current one proves unworkable.

## Workspace & Security: The Sandbox Model

This was a critical architectural decision. To ensure security and support multiple users and tasks, every agent run must be contained within a secure, isolated sandbox.

-   **Hierarchical Structure:** A top-level `/workspace` directory, with subdirectories for each user, and further subdirectories for each unique task or chat session (e.g., `/workspace/<user_id>/<task_id>/`).
-   **Scoped Tools:** All file system tools (`write_file`, `read_file`, `list_files`, `workspace_shell`) **must** be workspace-aware. They will receive the unique `workspace_path` for the current task and ensure all operations are contained within that directory. This prevents any possibility of the agent accessing or modifying files outside its designated sandbox.
-   **Virtual Environments:** For tasks requiring library installations, the agent should first create a Python virtual environment _inside_ the task's workspace (e.g., `/workspace/<user_id>/<task_id>/.venv/`). All subsequent `pip install` and `python` commands would be run from within this venv, ensuring complete dependency isolation.

## Advanced Self-Correction Ideas

Our current agent stops on failure. The next evolution is to attempt self-correction.

-   **Dependency Installation:** If the agent tries to run a Python script and gets a `ModuleNotFoundError`, the Evaluator should not just fail. It should recognize the specific error and recommend a new step to the Controller: `pip install <missing_library>`.
-   **Command Retries:** If a shell command fails, could the Controller retry it with a slight modification? For example, adding `sudo` (with user permission via HITL), or correcting a common typo.
-   **Re-Planning:** If the Evaluator determines the entire plan is flawed (e.g., the Planner chose to write a Python script when a simple `curl` command would have worked), it could trigger a "re-plan" event, sending the task back to the Planner with additional context about what went wrong.

## Human-in-the-Loop (HITL) Features

This is the goal of Phase 5. The user must have ultimate control.

-   **Pause & Resume:** The user should be able to pause the agent's execution loop between any two steps.
-   **Plan Editing:** While paused, the user could be presented with the remaining steps in the plan and have the ability to edit, reorder, or delete them.
-   **High-Stakes Confirmation:** For potentially destructive or costly actions (e.g., `rm -rf`, using an expensive API, `git push --force`), the agent should route to a special `HITL` node, pause, and wait for explicit user confirmation before proceeding.

## Future Tool Development

Our current toolset is a great start, but a true research assistant would benefit from more specialized tools:

-   **Git Tool:** A dedicated tool for `git clone`, `git status`, `git add`, `git commit`, and `git push`. This is essential for software engineering tasks.
-   **Database Tool:** A `sql_query` tool that can connect to a database and execute queries.
-   **Advanced Web Browser:** A tool that uses Selenium or Playwright to interact with dynamic websites that require JavaScript, filling out forms, and clicking buttons.
-   **Scientific Tools:** Wrappers for common command-line bioinformatics or data science tools (e.g., BLAST, Rscript execution).
