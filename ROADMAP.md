ResearchAgent: Project Roadmap (v2.5.3 Target Base)
===================================================

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

Guiding Principles for Development
----------------------------------

-   Accuracy & Reliability Over Speed: Prioritize correct and dependable agent behavior.

-   User-in-the-Loop (UITL/HITL): Design for human oversight and intervention capabilities.

-   Modularity & Maintainability: Build components that are easy to understand, update, and debug.

-   Extensibility: Architect the system to easily accommodate new tools, LLMs, and agent capabilities.

Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.5.2)
---------------------------------------------------------------------------------

-   UI Framework: Three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) with a dark theme.

-   Backend Infrastructure: Python, WebSockets, `aiohttp` file server.

-   Task Management: Create, select, delete, rename tasks with persistent storage (SQLite) and reliable UI updates.

-   Core Agent Flow (P-C-E-E Pipeline):

    -   Intent Classification ("PLAN" vs. "DIRECT_QA").

    -   Planner (LLM-based, generates step-by-step plans).

    -   Controller (LLM-based, validates steps, selects tools, formulates inputs, uses previous step outputs correctly).

    -   Executor (ReAct agent, executes steps using tools or direct LLM generation).

    -   Step Evaluator (LLM-based, assesses individual step success, suggests retries).

    -   Overall Plan Evaluator (LLM-based, assesses final plan outcome).

-   Key Fixes Incorporated:

    -   Controller correctly uses previous step's output for subsequent steps (e.g., "poem discrepancy" fixed).

    -   Overall Plan Evaluator's final assessment message persists in chat history.

    -   Controller's JSON parsing from LLM output made more robust (handles Markdown wrappers, `NameError` for `json` fixed).

    -   ReAct agent prompt in `agent.py` refined for better tool selection formatting by the Executor.

-   Core Tools Implemented & Refined:

    -   Web search (Tavily, DuckDuckGo).

    -   `DeepResearchTool` v1 (functional).

    -   File I/O (`read_file`, `write_file` with correct `:::` parsing).

    -   `workspace_shell` (STDOUT reporting improved).

    -   `python_package_installer` (now handles multiple space/comma-separated packages).

    -   `Python_REPL` (description clarified to guide LLM towards simpler, single-expression uses).

    -   `pubmed_search`, `web_page_reader`.

-   LLM Configuration: Google Gemini & local Ollama models supported, role-specific LLM selection via UI and `.env`. Fallback logic in `get_llm`.

-   Frontend Refactoring (v2.5.1 - v2.5.2): JavaScript modularized (`state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`). `script.js` as orchestrator.

-   Backend Refactoring (v2.5.1 - v2.5.2): `message_handlers.py` modularized into `message_processing` sub-package.

-   Backend Plan Proposal Mechanism (v2.5.2 - v2.5.3 target):

    -   Correctly sends `propose_plan_for_confirmation` message with `plan_id`, `human_summary`, and `structured_plan`.

    -   Saves `_plan_proposal_<plan_id>.md` artifact on proposal.

    -   Handles `cancel_plan_proposal` messages from the frontend.

    -   On plan execution, creates `_plan_<ID>.md` execution log artifact.

    -   Saves a `confirmed_plan_log` message to DB on plan confirmation for chat history persistence.

-   Frontend Plan Proposal Display (v2.5.2 - v2.5.3 target):

    -   Receives and processes `propose_plan_for_confirmation`.

    -   Basic UI for plan proposal (summary and action buttons) now appears in chat.

Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus)
----------------------------------------------------------------------------------

1.  Complete UI for Plan Proposal Interaction & Persistence (High Priority - In Progress)

    -   Goal: Create a clean, user-friendly, and persistent way to review, confirm, and track plans directly within the chat interface.

    -   Details & Status (Frontend Work):

        -   Inline "View Details" (PENDING):

            -   Modify `js/ui_modules/chat_ui.js` (`displayPlanConfirmationUI`): The "View Details" button should toggle the visibility of the `structured_plan` (detailed steps) directly *within* the plan proposal chat block.

            -   The `structured_plan` div will be initially hidden.

            -   Button text should toggle ("View Details" / "Hide Details").

            -   Simplify `js/script.js` (`handlePlanViewDetailsRequest`) as the primary logic moves to `chat_ui.js`.

        -   Transform Proposal to Persistent Message on Confirmation (PENDING):

            -   Modify `js/script.js` (`handlePlanConfirmRequest`): After sending `execute_confirmed_plan`, call a new function in `chat_ui.js` (e.g., `transformToConfirmedPlanUI`) to convert the interactive proposal block.

            -   Modify `js/ui_modules/chat_ui.js`: Create `transformToConfirmedPlanUI`. This function will:

                -   Find the existing interactive plan proposal block.

                -   Change its title (e.g., "Confirmed Plan:").

                -   Remove "View Details", "Confirm & Run", "Cancel" buttons.

                -   Ensure `human_summary` and the (now expanded) `structured_plan` are visible.

                -   Add a status like "Execution started..." or a timestamp.

        -   Load Confirmed Plan from History (PENDING):

            -   Modify `js/ui_modules/chat_ui.js` (`addChatMessageToUI`): Implement rendering logic for messages of type `confirmed_plan_log` (already saved by backend). This will display the historic confirmed plan (summary + expanded steps) in a static, non-interactive format.

            -   Ensure `js/script.js` (`dispatchWsMessage`) correctly passes these messages to `addChatMessageToUI`.

    -   Overall Status: Backend sends correct proposal message. Basic proposal UI appears. Key remaining work is frontend: inline details, transformation to persistent message, and history loading for confirmed plans.

2.  Refine Intermediate Step Chat Output (High Priority - After Plan UI Interaction is Polished)

    -   Goal: Keep main chat focused on primary user-agent interactions; move detailed step-by-step execution logs and verbose agent thoughts to the Monitor panel. This aims for a cleaner chat experience, similar to the `manus.ai` example.

    -   Details:

        -   Backend (`callbacks.py`): Review all `send_ws_message` calls. Ensure most intermediate outputs (tool inputs, full tool outputs unless it's the final answer, detailed LLM thoughts not part of a final answer) are consistently sent with `monitor_log` type or a new monitor-specific type.

        -   Only key user-facing results (e.g., the final generated content if that was the goal, final plan evaluation, critical errors) should be sent as `agent_message` for the chat.

        -   Frontend (`js/script.js` - `dispatchWsMessage`): Based on backend changes, strictly route messages. "Monitor-only" types should only call `addLogEntryToMonitor`.

        -   Use `agentThinkingStatusElement` in `chat_ui.js` for concise, transient updates like "Using tool X...", "Tool X finished."

    -   Status: Design clear. Implementation pending plan UI interaction finalization.

3.  Color-Coding UI Elements (Medium Priority)

    -   Goal: Visually differentiate agent component messages in the Monitor Log (e.g., Planner, Controller, Executor, Evaluator, specific tools) and potentially link these colors to the LLM selector dropdowns in the chat header.

    -   Details:

        -   Backend (`callbacks.py`): When sending `monitor_log` messages, include a `log_source` field in the payload.

        -   Frontend (`monitor_ui.js` - `addLogEntryToMonitor`): Use the `log_source` to add specific CSS classes (e.g., `log-source-planner`, `log-source-tool-write-file`) to the log entry `div`.

        -   Frontend (`css/style.css`): Add CSS rules for these new classes to apply distinct background tints, border colors, or text colors.

    -   Status: Planned.

4.  Further `script.js` Refinement (Phase 3.2 Completion - Medium Priority)

    -   Goal: Ensure `script.js` is a lean orchestrator, with most UI logic encapsulated in `ui_modules/*.js` and state managed via `StateManager`.

    -   Details: Conduct a final review of `script.js` to identify and move any residual complex UI manipulation or direct DOM access (that isn't simple event listener setup or element retrieval for module initialization) into the appropriate UI modules. Ensure all shared client-side state is accessed and mutated through `StateManager` methods.

    -   Status: Partially complete from earlier refactoring. A final pass is needed.

5.  Advanced Step Self-Correction & Error Handling (Medium Priority)

    -   Goal: Improve the agent's ability to autonomously recover from errors during step execution.

    -   Details:

        -   Step Evaluator: Enhance its ability to not just identify failures but to propose more specific and actionable `suggested_new_tool_for_retry` and `suggested_new_input_instructions_for_retry`.

        -   Controller: Improve its interpretation of these suggestions for retries.

        -   Agent Executor: Explore more sophisticated error parsing and retry mechanisms within LangChain if default `handle_parsing_errors` is insufficient.

    -   Status: Design phase. Current retry mechanism is basic.

6.  User-in-the-Loop (UITL/HITL) - Foundational Interaction Points (Medium Priority)

    -   Goal: Allow the agent to pause during plan execution and explicitly ask the user for clarification, input, or decisions before proceeding.

    -   Details:

        -   Planner: Needs to be able to generate "interaction steps" in the plan (e.g., "Ask user to confirm parameter X", "Request user to upload file Y").

        -   Backend (`agent_flow_handlers.py`): When an interaction step is reached, pause execution and send a specific message type to the frontend (e.g., `request_user_input`) with the prompt/question.

        -   Frontend (`chat_ui.js` / `script.js`): Display this prompt to the user (perhaps with input fields or choice buttons). User's response is sent back to the backend.

        -   Backend: Resumes plan execution using the user's input.

    -   Status: Design phase.

Phase 3: Advanced Interactivity & Tooling (Mid-Term)
----------------------------------------------------

1.  Advanced User-in-the-Loop (UITL/HITL) Capabilities:

    -   Editable Plans: Allow users to modify proposed plans (reorder, edit, add, delete steps) via the UI before execution.

    -   Step-Level Intervention: Allow users to pause an ongoing plan, inspect intermediate results, and potentially modify upcoming steps or provide corrective input.

    -   Tool Parameterization UI: For complex tools, provide a UI for users to set/override parameters if the agent requests it or if the user wants to fine-tune.

2.  New Tools & Tool Enhancements:

    -   Code Interpreter with Execution & State: A more robust sandboxed environment for Python execution that can maintain state between calls (unlike the current REPL). Could involve `jupyter_kernel_gateway` or similar.

    -   Data Visualization Tools: Integrate libraries for generating charts/plots directly as artifacts beyond just saving images (e.g., interactive plots using Plotly.js if feasible).

    -   Database Querying Tool: Allow the agent to connect to and query SQL/NoSQL databases (with strict security and configuration).

    -   Long-Running Task/Background Tool Execution: Support for tools that might take a significant time to complete, with progress updates.

    -   PlaywrightSearchTool Activation: Fully integrate and debug the existing `PlaywrightSearchTool` for more complex web interactions if Tavily/DDG are insufficient.

3.  Workspace RAG (Retrieval Augmented Generation):

    -   Implement vector search over documents within the current task's workspace.

    -   Allow the agent to "read" all relevant documents in its workspace to answer questions or synthesize information based on that context.

4.  Improved Agent Memory & Context Management:

    -   Explore more sophisticated memory mechanisms beyond `ConversationBufferWindowMemory` if needed for very long interactions or cross-task context (though tasks are meant to be isolated).

    -   Allow users to manually "pin" or "save" important pieces of information from the chat or monitor to a "scratchpad" or "notes" area for the current task.

Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
-------------------------------------------------------------------------

1.  Advanced Re-planning & Self-Correction:

    -   Agent can significantly modify or discard its current plan if it encounters persistent failures or if new information suggests a better approach.

    -   More sophisticated learning from failed steps to improve future planning.

2.  User Permissions & Resource Gateway:

    -   For multi-user scenarios or more sensitive tools, implement a permission system.

    -   Agent requests permission before using certain tools or accessing specific resources.

3.  Streaming Output for Tools & LLM Responses:

    -   Stream partial outputs from tools or LLM `Final Answer` generation to the UI for better perceived responsiveness, especially for long-running tasks or verbose outputs.

4.  Specialized Agent Personas & Workflows:

    -   Develop pre-configured agent personas with specific toolsets and system prompts tailored for particular research domains (e.g., "Bioinformatics Analyst", "Epidemiology Modeler").

    -   Allow users to define and save custom agent configurations/workflows.

5.  Collaborative Features:

    -   (Very long-term) Explore possibilities for multiple users to interact with the same research task or agent instance.

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses.