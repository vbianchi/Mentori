BRAINSTORM.md - ResearchAgent Project (v2.5)
============================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project. For longer-term plans and phased development, please see `ROADMAP.md`.

Current Version & State (v2.5 - Frontend Refactoring & Agent Stability):

The ResearchAgent is at v2.5. Key recent advancements include:

-   Frontend Codebase Refactoring: Significant modularization of the frontend JavaScript into a `state_manager.js`, `websocket_manager.js`, and distinct `ui_modules` for tasks, chat, monitor, artifacts, LLM selectors, token usage, and file uploads. This enhances maintainability and prepares for future UI feature development.

-   `DeepResearchTool`: Fully functional across all its phases (search, curation, extraction, and report synthesis).

-   Planner Refinements:

    -   Improved granularity for "No Tool" steps: Complex generation tasks are broken down by the Planner.

    -   Final Answer Synthesis: For multi-part user queries, the Planner adds a final "No Tool" step for comprehensive answers.

-   Agent Execution Stability:

    -   Refined ReAct agent prompt for clearer `Final Answer` formatting, reducing `_Exception` tool calls.

    -   Executor directive includes 'precise expected outcome' for better adherence to step goals.

-   Successful Complex Plan Execution: Demonstrated success with multi-step plans involving chained "No Tool" generations, file I/O, and information extraction.

-   All previously listed UI (task management, chat, monitor, artifact viewer), Backend (Python, WebSockets, SQLite), Agent Architecture (P-C-E-E, Intent Classifier), LLM Configuration (Gemini, Ollama, role-specific), Callbacks, and Core Tool functionalities remain operational.

Current Complex Task Flow (Illustrative - Post-Refinements):

The P-C-E-E pipeline is more robust due to the Planner and Executor enhancements. For instance, generating a Markdown table and then using it now involves:

1.  Intent Classification: User query is identified as requiring a "PLAN".

2.  Planner:

    -   Step 1 (No Tool): Generate data (e.g., as JSON). Expected outcome: "Intermediate data for table in JSON format."

    -   Step 2 (No Tool): Format JSON to Markdown table. Expected outcome: "Markdown table string."

    -   Step 3 (`write_file`): Save Markdown table to a file. Expected outcome: "File 'table.md' created."

    -   (Potentially a final synthesis step if this was part of a multi-part query).

3.  User Confirmation: Plan is displayed in UI.

4.  Execution Loop (per step):

    -   Controller: Validates the current step (e.g., for Step 2, confirms "No Tool" is appropriate and the input from Step 1's output is ready).

    -   Executor (ReAct Agent):

        -   Receives directive: "Your current sub-task is: 'Format JSON to Markdown table'. The precise expected output for THIS sub-task is: 'Markdown table string'. The Controller has determined no specific tool is required. Provide a direct answer..."

        -   Processes input (output from Step 1) and generates the Markdown table as its `Final Answer`.

    -   Step Evaluator: Assesses if the Executor's output (the Markdown table string) matches the step's `expected_outcome`. If successful, proceeds. If failed but recoverable, suggests retry parameters (up to `AGENT_MAX_STEP_RETRIES`).

5.  Overall Evaluator (Post-Plan): Assesses if the entire sequence of operations successfully addressed the original user query.

(This flow benefits from the Planner's ability to break down complex "No Tool" steps and the Executor's clearer directives, leading to fewer ReAct agent errors.)

User Observations & Feedback (Outstanding/New):

-   `_Exception` Tool Calls: Continue monitoring for any residual `_Exception` tool calls by the ReAct agent, especially after outputs from complex tools or with less common LLMs.

-   UI - Plan Visibility: User feedback indicates a desire for the approved plan to remain easily accessible/visible during execution for better context. (Partially addressed by `_plan.md` in artifact viewer; could be enhanced).

-   UI - Artifact Viewer:

    -   Feature Request: Implement a file/folder structure view for the workspace.

    -   Feature Request: Improve PDF viewing capabilities (e.g., direct rendering if possible, beyond just a link).

-   User Priority: Strong emphasis on accuracy over speed.

-   User Priority: High desire for User-in-the-Loop (UITL/HITL) capabilities.

Immediate Brainstorming / Next Small UX Considerations:

-   Refining Status Messages: Ensure status messages in the monitor header are consistently clear and don't overflow awkwardly.

-   Visual Feedback for File Uploads: While functional, could add more distinct visual feedback in the UI during the upload process itself (e.g., progress per file if feasible, or clearer success/failure indicators per file in the chat/monitor).

-   Error Display: Ensure errors from the agent or tools are presented in a user-friendly way in the chat, perhaps with a "details" toggle to see raw error messages in the monitor.

This document will be used for jotting down new ideas and tracking immediate concerns. Major features and long-term planning are now in `ROADMAP.md`.