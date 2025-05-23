BRAINSTORM.md - ResearchAgent Project (v2.4)
============================================

This document tracks the current workflow, brainstorming ideas, user feedback, and the proposed roadmap for the ResearchAgent project.

Current Version: v2.4 (Tavily integrated, **`DeepResearchTool` fully functional including Phase 4 synthesis and report generation**, various bug fixes implemented).

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
            -   If `is_recoverable_via_retry` is true and `retry_count < AGENT_MAX_STEP_RETRIES` (from `settings`), the step is retried with suggestions fed back to the Controller.
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
    -   Phase 3 (Deep Content Extraction using `Workspace_and_parse_url`): Functional.
    -   Phase 4 (Information Synthesis & Report Generation): **Functional.**
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

### Phase 1: Core `DeepResearchTool` Functionality **(Completed)**

1.  Implement `DeepResearchTool` - Phase 4: Information Synthesis & Report Generation **(DONE)**
    -   The logic to take extracted/summarized content and use a "Writer" LLM to generate a structured Markdown report, including a "Sources Consulted" section, is implemented in `backend/tools/deep_research_tool.py`.

### Phase 2: Agent Integration & Refinement

1.  **Test `DeepResearchTool` via Full Agent UI Flow**
    -   Goal: Ensure the Planner selects `deep_research_synthesizer`, the Controller provides correct input, and the full report is returned to the UI.
    -   Action: Perform end-to-end tests from the UI with queries designed to trigger the `DeepResearchTool`.
2.  **Address `_Exception` Tool Calls (User Observation 1)**
    -   Goal: Make the agent's processing of tool outputs (especially from Tavily and the `DeepResearchTool`) smoother.
    -   Action:
        -   Review the exact string format returned by `TavilyAPISearchTool` and the `DeepResearchTool`'s final Markdown report.
        -   Consider if these outputs need further simplification or clearer "end of output" markers for the Executor LLM.
        -   Potentially refine the ReAct agent's main prompt in `backend/agent.py` to better handle multi-part observations or complex string outputs.
3.  **Refine Retry Logic for "No Tool" Plan Steps**
    -   Goal: Ensure that if the Step Evaluator suggests a retry for a "No Tool" step, the retry mechanism correctly feeds the evaluator's `suggested_new_input_instructions_for_retry` back to the Executor.
    -   Action:
        -   In `message_handlers.py` (`process_execute_confirmed_plan`), when `last_step_correction_suggestion.is_recoverable_via_retry` is true for a "No Tool" step:
            -   The `plan_step_for_controller_call.tool_input_instructions` should be updated with the suggestion.
            -   The `controller.validate_and_prepare_step_action` should pass this new instruction through its `reasoning`.
            -   The `agent_input_for_executor` prompt for "No Tool" retries needs to incorporate these specific retry instructions.
4.  **Implement Advanced Step Self-Correction via Evaluator-Driven Revision**
    -   **Goal:** Enhance the agent's autonomy and error recovery capabilities by enabling the Step Evaluator to not just suggest new inputs/tools but also to revise the description/objective of a failed step for a more effective retry.
    -   **Rationale:** Sometimes, a step fails because its original description was ambiguous, too broad, or led the Controller/Executor astray. A simple input tweak might not be enough for a successful retry.
    -   **Key Components & Actions:**
        -   **Step Evaluator Enhancement (`evaluator.py`):**
            -   Update `STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE` to instruct the LLM to propose a `suggested_revised_step_description` if it deems the original step formulation problematic yet recoverable. This revised description should aim to clarify the step's goal or approach.
            -   Add `suggested_revised_step_description: Optional[str]` to the `StepCorrectionOutcome` Pydantic model.
        -   **Backend Retry Loop Modification (`message_handlers.py` - `process_execute_confirmed_plan`):**
            -   When a retry is triggered based on the Step Evaluator's feedback:
                -   If `suggested_revised_step_description` is provided by the Evaluator, update the current `PlanStep`'s description (for the scope of the retry attempt) with this revised text before calling the Controller.
        -   **Controller Awareness (`controller.py`):** The Controller will implicitly benefit by receiving a clearer, revised step description when formulating its `ValidatedStepAction` for the retry.

### Phase 3: Interactive Plan Execution (User-in-the-Loop)

-   **Goal:** Enable the agent to request user input, clarification, or decisions at specific points *during* the execution of a multi-step plan, fostering a more collaborative research process.
-   **Rationale:** Many research tasks benefit from human guidance at intermediate stages, such as selecting from multiple options (e.g., which discovered files to process), refining queries based on initial findings, or confirming a sub-strategy before committing to extensive processing.
-   **Key Components & Actions:**
    -   **Planner Enhancement (`planner.py`):**
        -   Modify the Planner to identify steps suitable for user interaction (e.g., when multiple paths are possible, or when specific domain knowledge for selection is needed).
        -   Enable the Planner to generate special "interaction steps" in the plan. These steps would define:
            -   The prompt/question to present to the user.
            -   The type of input expected (e.g., selection from a list, text input, confirmation).
            -   Data from previous steps that needs to be shown to the user to make an informed decision (e.g., a list of file names, summaries of search results).
        -   Update the `PlanStep` Pydantic model to include fields for these interaction details (e.g., `is_interaction_step: bool`, `interaction_prompt: str`, `interaction_data_keys: List[str]`).
    -   **Backend Execution Loop Modification (`message_handlers.py` - `process_execute_confirmed_plan`):**
        -   When an "interaction step" is encountered:
            -   Pause the plan execution.
            -   Send a specific WebSocket message (e.g., `ui_interaction_required`) to the UI, providing the interaction prompt and any necessary data (e.g., list of files, summaries).
            -   Store the paused state of the plan, including context from prior steps.
        -   Implement a handler for a new WebSocket message type from the UI (e.g., `user_interaction_response`).
        -   Upon receiving the user's response:
            -   Treat the user's input as the "output" or result of the interaction step.
            -   Potentially format or process this user input.
            -   Resume plan execution, making the user's input available as context or direct input for subsequent plan steps.
    -   **UI Development (`js/script.js`, `index.html`, `css/style.css`):**
        -   Develop UI components (e.g., modals, inline forms, selection lists) to render interaction requests received from the backend.
        -   Enable users to provide the requested input clearly and easily.
        -   Send the user's input back to the backend via the new WebSocket message type.
    -   **State Management:** Ensure robust management of the agent's state when a plan is paused awaiting user input, including handling potential timeouts or errors.
-   **Example Interaction Points:**
    -   After a `list_workspace_files` tool runs, asking the user: "I found these files: [A.pdf, B.txt, C.md]. Which ones should I analyze for your research on X?"
    -   After an initial web search: "I found these 3 main themes in the initial search results: [Theme1, Theme2, Theme3]. Which theme should I prioritize for deeper investigation, or would you like to provide a more specific query?"
    -   Before synthesizing a large report: "I have gathered information from 5 web sources and 2 of your uploaded documents. Are there any specific sections you'd like me to ensure are in the final report?"

### Phase 4: Playwright & Advanced Web Interaction (Parked for now, but setup is ready)

1.  Develop Playwright for Targeted Web Automation
    -   Goal: Use Playwright for tasks requiring complex browser interaction beyond simple search/read (e.g., logging into specific databases, form filling, navigating JS-heavy sites).
    -   Action: Revisit `backend/tools/playwright_search.py`. Focus on a specific, well-defined task that needs Playwright. Develop robust selectors and interaction logic for that task.

### Phase 5: Further UX Enhancements & Advanced Features (Longer Term)

-   Interactive Plan Modification (Pre-Execution): Allow users to edit, reorder, add/delete steps *before* confirming the initial plan.
-   Permission Gateway for Sensitive Tools: Explicit UI confirmation before executing tools like `workspace_shell`.
-   Improved PDF Viewing & Artifact Navigation (User Points 3 & 4).
-   Live Plan in Chat UI (User Observation 2 - Advanced).
-   Advanced Re-planning based on Overall Evaluator feedback (e.g., if the overall plan fails, the agent attempts to generate a new, different plan).
-   Streaming output for LLM responses to the UI.

This updated BRAINSTORM.md should accurately reflect our current position and the immediate next steps, as well as the exciting new features we plan to incorporate. The very next action is to **test the `DeepResearchTool` via the full agent UI flow** as outlined in Phase 2.
