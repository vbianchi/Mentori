ResearchAgent Development Plan: UITL & UI Enhancements
======================================================

This plan outlines the development phases for enhancing the ResearchAgent project, focusing on User-in-the-Loop (UITL) capabilities and User Interface/User Experience (UI/UX) improvements, drawing inspiration from Magentic-UI and Manus.ai.

Phase 1: Immediate Focus - Enhancing Core Agent Stability & Foundational UITL
-----------------------------------------------------------------------------

Goal: Improve the agent's ability to self-correct and introduce basic mechanisms for the agent to request user input.

1.  Advanced Step Self-Correction via Evaluator-Driven Revision

    -   Context: `BRAINSTORM.md` Phase 2.3.

    -   Tasks:

        -   Backend (`evaluator.py`):

            -   Modify the `StepCorrectionOutcome` Pydantic model to include `suggested_revised_step_description: Optional[str]`.

            -   Update the `STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE` to instruct the LLM to generate this `suggested_revised_step_description` when `is_recoverable_via_retry` is true.

        -   Backend (`message_handlers.py`):

            -   In the plan execution loop, if a step retry is triggered based on the `StepCorrectionOutcome`, use the `suggested_revised_step_description` (if provided) as the new description for the Controller when retrying the step.

    -   Magentic-UI Relevance: Reinforces the importance of robust error handling and re-planning capabilities for agent stability.

2.  Implement Foundational Agent-Initiated Interaction Points

    -   Context: `BRAINSTORM.md` Phase 3.1; Inspired by Magentic-UI's Co-Tasking & Action Guards.

    -   Goal: Enable the agent to pause and request user clarification or approval.

    -   Tasks:

        -   Backend (`planner.py`):

            -   Define a new type or add a field to `PlanStep` (e.g., `interaction_type: Optional[str]`, `interaction_prompt: Optional[str]`) to signify an "interaction required" step.

            -   Modify `generate_plan` to allow the Planner LLM to output these interaction steps when it deems user input is necessary (e.g., for ambiguity resolution or sensitive action approval).

        -   Backend (`message_handlers.py`):

            -   When the Controller processes a plan step flagged as requiring interaction:

                -   Pause the plan execution loop.

                -   Construct a payload containing the `interaction_prompt` and any necessary context (e.g., list of files if user selection is needed).

                -   Send a new WebSocket message (e.g., type `request_user_input`) to the UI with this payload.

            -   Implement logic to wait for a `user_input_response` WebSocket message from the UI.

            -   Process the user's response and resume plan execution or re-plan as appropriate.

        -   Backend (`server.py` or dedicated WebSocket utils):

            -   Define new WebSocket message types: `request_user_input` (backend to frontend) and `user_input_response` (frontend to backend).

        -   Frontend (`js/script.js`):

            -   Add a WebSocket message listener for `request_user_input`.

            -   On receiving `request_user_input`, display a modal or an inline prompt in the chat area to present the `interaction_prompt` to the user and capture their input (text, selection, confirmation).

            -   Send the captured user input back to the backend via a `user_input_response` WebSocket message.

        -   Initial Use Case 1: Action Approval (Basic):

            -   Identify a sensitive tool (e.g., `workspace_shell`).

            -   Modify the `Controller` (`controller.py`): When it prepares to use this tool, instead of directly forming the input for the Executor, it should recognize the sensitivity. The Planner might preemptively create an interaction step, or the Controller could be enhanced to request an interaction if a sensitive tool is selected for a step. For simplicity, start with the Planner generating an interaction step for approval *before* the sensitive tool step.

            -   The interaction prompt would be: "The agent proposes to use the `workspace_shell` tool with the command: `[command]`. Do you approve? (Yes/No)".

        -   Initial Use Case 2: Clarification Request (Basic):

            -   Modify `planner.py`: If the Planner LLM detects high ambiguity in the user query that prevents effective plan generation, it should generate a plan with a single `interaction_required_step` asking for specific clarification.

Phase 2: Mid-Term - Expanding UITL, Tooling, and UI Chat Clarity
----------------------------------------------------------------

Goal: Allow users to view plan progress, improve chat readability, and add more specialized tools.

1.  User-Initiated Plan Review (Display Only, During Execution)

    -   Context: `BRAINSTORM.md` Phase 3.2, User Observation 2.

    -   Tasks:

        -   Frontend (`js/script.js`):

            -   Add a "View Current Plan" button or a dedicated area in the UI.

            -   When clicked (or when an agent-initiated pause occurs), fetch and display the `current_plan_structured` (remaining steps with their statuses if available from `_plan_<ID>.md` or backend state).

        -   Backend (`server.py` / `message_handlers.py`):

            -   Ensure the full current plan (with statuses of completed/pending steps) is accessible, perhaps by sending it to the UI upon plan confirmation or providing an endpoint/message to request it.

            -   Live updates to the `_plan_<ID>.md` file should trigger a WebSocket message to the UI to refresh its displayed plan view if open.

2.  Visually Distinct Message Components in Chat UI

    -   Context: Inspired by Manus.ai; `BRAINSTORM.md` (Comprehensive Update).

    -   Tasks:

        -   Backend (`callbacks.py` - `WebSocketCallbackHandler`):

            -   Send new, more granular WebSocket message types or add specific metadata to existing messages for:

                -   `agent_action_status` (e.g., "Planner: Generating plan...", "Controller: Validating step 'X'...", "Executor: Attempting tool 'Y'...")

                -   `tool_attempt` (e.g., "Using Tool: `TavilyAPISearchTool` with input: `{'query': 'AI research'}`")

                -   `tool_result_summary` (e.g., "Read 'report.pdf' (2500 words).")

                -   `plan_step_update` (e.g., "Executing Step 3: Write summary to file.", "Step 3 Succeeded.", "Step 3 Failed: File not found.")

        -   Frontend (`js/script.js`):

            -   Modify `addChatMessage` or create new rendering functions in `script.js` to handle these new message types/metadata.

            -   Apply distinct CSS classes to these elements for styling.

        -   CSS (`css/style.css`):

            -   Define CSS styles for these new message components (e.g., smaller font, different background, icons).

3.  Develop New Granular Tools

    -   Context: `BRAINSTORM.md` Phase 4; Inspired by Magentic-UI `FileSurfer`.

    -   Tasks (Backend - `tools/standard_tools.py` or new files):

        -   Implement `list_files_tool`: Lists files/directories in the current task's workspace. Output: Formatted string or JSON.

        -   Implement `find_file_tool`: Searches for files by name/pattern in the current task's workspace. Output: List of matching paths.

        -   Implement `download_files_tool`: Downloads files from given URLs directly to the current task's workspace.

    -   Safety: Ensure all file system tools operate strictly within the designated task workspace and have robust path validation.

Phase 3: Longer-Term - Advanced UX, Planning, and Tooling
---------------------------------------------------------

Goal: Implement more sophisticated user interactions, plan management, and advanced tool capabilities.

1.  Interactive Plan Modification (Pre-Execution & During Pauses)

    -   Context: `BRAINSTORM.md` Phase 3.2; Magentic-UI's plan editor.

    -   Tasks:

        -   Extend the "View Current Plan" UI to allow users to suggest modifications (edit description, reorder, add, delete steps) *before* initial execution or *during* an agent-initiated pause.

        -   Backend logic to receive, validate, and apply these plan modifications, then resume/start execution.

2.  Plan Gallery / Reusability

    -   Context: Inspired by Magentic-UI's Plan Learning and Retrieval.

    -   Tasks:

        -   Mechanism for users to save successfully executed or manually refined plans.

        -   UI to browse, select, and adapt saved plans for new tasks.

3.  Permission Gateway for Sensitive Tools

    -   Context: Inspired by Magentic-UI `ActionGuards`.

    -   Tasks:

        -   Develop a more formal permission system for tools flagged as sensitive (e.g., `workspace_shell`, `python_package_installer`).

        -   Users could grant/deny permissions per session or per task.

4.  Advanced Tooling (RAG-style)

    -   Context: `BRAINSTORM.md` Phase 4.

    -   Tasks:

        -   `ingest_workspace_documents_tool`: For indexing content within the task workspace.

        -   `search_indexed_workspace_tool`: For semantic search over indexed documents.

This plan provides a roadmap. We will start with Phase 1, Item 1 (Advanced Step Self-Correction) as it builds upon existing components and directly addresses agent stability. Concurrently, we can begin detailed design and backend work for Phase 1, Item 2 (Foundational Agent-Initiated Interaction Points) as this is a core UITL feature.