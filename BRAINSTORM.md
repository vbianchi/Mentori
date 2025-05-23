BRAINSTORM.md - ResearchAgent Project (v2.4)
============================================

This document tracks the current workflow, brainstorming ideas, user feedback, and the proposed roadmap for the ResearchAgent project.

Current Version: v2.4 (Tavily integrated, DeepResearchTool functional through content extraction, various bug fixes implemented).

Current Complex Task Flow (v2.4 Baseline)
-----------------------------------------

The process for handling a complex task, once classified as "PLAN" intent:

1.  User Input: User provides a complex query.

2.  Intent Classifier (`intent_classifier.py`): Classifies the query. If "PLAN", proceeds.

3.  Planner (`planner.py`):

    -   Takes the user query and a summary of available tools (including `tavily_search_api` and `deep_research_synthesizer`).

    -   Generates a multi-step plan (list of `PlanStep` objects).

    -   Presents a human-readable summary and the structured plan to the user.

4.  User Confirmation (UI): User confirms or cancels the plan.

5.  Execution Loop (Backend - `message_handlers.process_execute_confirmed_plan`):

    -   Plan Persistence: Saves the confirmed plan to a `_plan_<ID>.md` file in the task's workspace. This file uses Markdown checklist syntax.

    -   Iterates through each step:

        -   Controller/Validator (`controller.py` - `validate_and_prepare_step_action`):

            -   Receives the current `PlanStep`, original query, and available tools.

            -   Validates/chooses the tool and formulates the precise `tool_input` (which is now always a string; JSON string for structured inputs).

            -   Returns a `ValidatedStepAction` object (or raises `ToolException`).

        -   Executor (`agent.py` - `create_agent_executor`):

            -   Receives a directive prompt based on the Controller's output.

            -   Executes the step using its ReAct cycle. For tools with `args_schema`, LangChain handles parsing the JSON string `tool_input` back to a dictionary.

            -   Callbacks (`callbacks.WebSocketCallbackHandler`) send detailed logs (including corrected tool names on error).

        -   Step Evaluator (`evaluator.py` - `evaluate_step_outcome_and_suggest_correction`):

            -   Assesses if the step's goal was achieved.

            -   If `is_recoverable_via_retry` is true and `retry_count < AGENT_MAX_STEP_RETRIES` (from `settings`), the step is retried with suggestions fed back to the Controller. (Handling of "No Tool" step retries needs verification/refinement).

        -   Live Plan Update: The `_plan_<ID>.md` file is updated with the step's status (`[x]`, `[!]`, `[-]`).

    -   The loop continues unless a step definitively fails or the plan is cancelled.

6.  Evaluator (Overall Plan - `evaluator.evaluate_plan_outcome`):

    -   Called after the execution loop.

    -   Assesses overall goal achievement and provides a final assessment/summary to the user.

Current State & User Feedback (Post v2.3 Implementation)
--------------------------------------------------------

The agent now incorporates:

-   Intent Classification.

-   Planner, Controller, Executor Loop.

-   Step Evaluator (per-step evaluation is active; refined for rate-limit errors).

-   Overall Evaluator.

-   Role-Specific LLM Configuration (via `.env` and UI overrides).

-   Refactored Backend.

-   Tavily Search API (`TavilyAPISearchTool`) as the primary web search tool, returning structured data (`List[Dict]`). DuckDuckGo is a fallback.

-   `DeepResearchTool` (`deep_research_synthesizer`):

    -   Phase 1 (Initial Search using Tavily): Functional.

    -   Phase 2 (Source Curation using Curator LLM): Functional.

    -   Phase 3 (Deep Content Extraction using `fetch_and_parse_url`): Functional.

    -   Phase 4 (Information Synthesis & Report Generation): Next to be implemented.

-   Bug Fixes Implemented:

    -   Workspace Deletion Bug (User Point 1 from previous list): Fixed.

    -   LLM Retry/Fallback Logic (User Point 4): `get_llm` has fallback.

    -   Plan Persistence to `_plan.md` (User Point 5 - Basic): Implemented and working, including status updates.

    -   UI for Role-Specific LLM Selection (User Point 3): Implemented.

    -   `model_json_schema` `AttributeError` for Pydantic v1 schemas: Fixed for `TavilySearchInput` and `DeepResearchToolInput`.

    -   "Unknown Tool" error logging in callbacks: Fixed.

    -   Artifact viewer duplication: Fixed.

    -   Various `NameError` and `TypeError` issues during tool development: Resolved.

    -   `AGENT_MAX_STEP_RETRIES` setting added to config and `.env`.

User Observations & Feedback (Outstanding/New):

1.  `_Exception` Tool Calls: The ReAct agent (Executor) sometimes still calls the internal `_Exception` tool after a successful tool run (e.g., after Tavily search in the "CRISPR" query example). While it often recovers, this indicates the LLM might be struggling with the format/length of the tool output or deciding the immediate next step.

2.  Feature Request (Plan Visibility - UI): The approved plan could be made to remain visible (perhaps collapsed) in the UI after confirmation for better user context. (Currently, it disappears, but the `_plan.md` artifact appears).

3.  Feature Request (Artifact Viewer - File Structure): Implement a file/folder structure view for the workspace.

4.  Feature Request (Artifact Viewer - PDF): Improve PDF viewing (currently just listed as a link).

Proposed Roadmap & Areas for Improvement
----------------------------------------

### Phase 1: Complete Core `DeepResearchTool` Functionality

1.  Implement `DeepResearchTool` - Phase 4: Information Synthesis & Report Generation

    -   Goal: Take the extracted content (summarized if necessary) and use a "Writer" LLM to generate a structured Markdown report.

    -   Action:

        -   Finalize the `WRITER_SYSTEM_PROMPT_TEMPLATE` and `DeepResearchReportOutput` Pydantic model in `deep_research_tool.py`.

        -   Implement logic in `_arun` to:

            -   Calculate total token estimates for extracted content.

            -   Conditionally call `_summarize_content` for each source if `estimated_total_tokens > max_total_tokens_for_writer`.

            -   Prepare the (summarized or full) content for the Writer LLM.

            -   Invoke the Writer LLM chain (Prompt | LLM | JsonOutputParser for `DeepResearchReportOutput`).

            -   Format the structured output into a final Markdown report string.

            -   Append a "Sources Consulted" section.

        -   Thoroughly test this full flow with the direct script run (`python3 -m backend.tools.deep_research_tool`).

### Phase 2: Agent Integration & Refinement

1.  Test `DeepResearchTool` via Full Agent UI Flow

    -   Goal: Ensure the Planner selects `deep_research_synthesizer`, the Controller provides correct input, and the full report is returned to the UI.

    -   Action: Perform end-to-end tests from the UI with queries designed to trigger the `DeepResearchTool`.

2.  Address `_Exception` Tool Calls (User Observation 1)

    -   Goal: Make the agent's processing of tool outputs (especially from Tavily and the new `DeepResearchTool`) smoother.

    -   Action:

        -   Review the exact string format returned by `TavilyAPISearchTool`'s `_format_results_to_string` method (if the agent is still using this string version for some reason) and the `DeepResearchTool`'s final Markdown report.

        -   Consider if these outputs need further simplification or clearer "end of output" markers for the Executor LLM.

        -   Potentially refine the ReAct agent's main prompt in `backend/agent.py` to better handle multi-part observations or complex string outputs.

3.  Refine Retry Logic for "No Tool" Plan Steps

    -   Goal: Ensure that if the Step Evaluator suggests a retry for a "No Tool" step (like Step 2 in the "Valerio Bianchi" plan), the retry mechanism correctly feeds the evaluator's `suggested_new_input_instructions_for_retry` back to the Executor.

    -   Action:

        -   In `message_handlers.py` (`process_execute_confirmed_plan`), when `last_step_correction_suggestion.is_recoverable_via_retry` is true for a "No Tool" step:

            -   The `plan_step_for_controller_call.tool_input_instructions` should be updated with the suggestion.

            -   The `controller.validate_and_prepare_step_action` should pass this new instruction through its `reasoning` (or a dedicated field if we modify `ValidatedStepAction`).

            -   The `agent_input_for_executor` prompt for "No Tool" retries needs to incorporate these specific retry instructions from the Controller/Evaluator.

### Phase 3: Playwright & Advanced Web Interaction (Parked for now, but setup is ready)

1.  Develop Playwright for Targeted Web Automation

    -   Goal: Use Playwright for tasks requiring complex browser interaction beyond simple search/read (e.g., logging into specific databases, form filling, navigating JS-heavy sites).

    -   Action: Revisit `backend/tools/playwright_search.py`. Focus on a specific, well-defined task that needs Playwright. Develop robust selectors and interaction logic for that task.

### Phase 4: UX Enhancements & Further Features (Longer Term)

-   Interactive Plan Modification (Pre-Execution): Allow users to edit, reorder, add/delete steps.

-   Permission Gateway for Sensitive Tools: Explicit UI confirmation.

-   Improved PDF Viewing & Artifact Navigation (User Points 6 & 7).

-   Live Plan in Chat UI (User Point 5 - Advanced).

-   Advanced Re-planning based on Overall Evaluator feedback.

-   Streaming output for LLM responses.

This updated BRAINSTORM.md should accurately reflect our current position and the immediate next steps. The very next action is to complete the synthesis phase of the `DeepResearchTool`.