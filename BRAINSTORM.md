BRAINSTORM.md - ResearchAgent Project (v2.4)
============================================

This document tracks the current workflow, brainstorming ideas, user feedback, and the proposed roadmap for the ResearchAgent project.

Current Version: v2.4 (Tavily integrated, `DeepResearchTool` fully functional, improved Planner granularity for "No Tool" steps, and enhanced ReAct agent prompt for better `Final Answer` formatting, leading to increased stability in multi-step "No Tool" generations and successful complex plan execution).

Current Complex Task Flow (v2.4 Baseline - Enhanced Stability)
--------------------------------------------------------------

The process for handling a complex task, once classified as "PLAN" intent:

1.  User Input: User provides a complex query.

2.  Intent Classifier (`intent_classifier.py`): Classifies the query. If "PLAN", proceeds.

3.  Planner (`planner.py`):

    -   Takes the user query and a summary of available tools.

    -   Generates a multi-step plan (list of `PlanStep` objects).

        -   Enhanced: For "No Tool" steps requiring complex structured text output (e.g., Markdown tables), the Planner is now guided to break this into:

            1.  An initial "No Tool" step to generate core data/content (e.g., as JSON).

            2.  A subsequent "No Tool" step to format this data into the desired complex structure.

        -   Enhanced: If the user query implies multiple distinct pieces of information for the final answer, the Planner adds a final "No Tool" step to synthesize these into a single, comprehensive response.

    -   Presents a human-readable summary and the structured plan to the user.

4.  User Confirmation (UI): User confirms or cancels the plan.

5.  Execution Loop (Backend - `message_handlers.process_execute_confirmed_plan`):

    -   Plan Persistence: Saves the confirmed plan to a `_plan_<ID>.md` file.

    -   Iterates through each step:

        -   Controller/Validator (`controller.py`): Validates/chooses the tool and formulates `tool_input`.

        -   Executor (`agent.py` - `create_agent_executor`):

            -   Receives a directive prompt (now including the step's `expected_outcome`).

            -   Executes the step using its ReAct cycle.

                -   Enhanced: The ReAct agent's main prompt (`backend/agent.py`) provides clearer instructions on `Final Answer` formatting, especially for multi-line/structured output, reducing `_Exception` tool calls.

            -   Callbacks (`callbacks.WebSocketCallbackHandler`) send detailed logs.

        -   Step Evaluator (`evaluator.py`): Assesses step outcome. If `is_recoverable_via_retry` is true, the step is retried.

        -   Live Plan Update: The `_plan_<ID>.md` file is updated.

    -   The loop continues unless a step definitively fails or the plan is cancelled.

6.  Evaluator (Overall Plan - `evaluator.evaluate_plan_outcome`):

    -   Called after the execution loop.

    -   Assesses overall goal achievement and provides a final assessment/summary.

Current State & User Feedback (Post v2.4 Stability Enhancements)
----------------------------------------------------------------

The agent now incorporates:

-   (All previously listed features)

-   Improved Planner logic for decomposing complex "No Tool" generation tasks.

-   Improved Planner logic for adding a final synthesis step for multi-part user queries.

-   Refined ReAct agent prompt in `backend/agent.py` leading to more stable "No Tool" step execution and fewer `_Exception` tool calls.

-   Successful execution of complex multi-step plans involving generation, file I/O, and data extraction, including the "Alzheimer's drug candidates" test case.

User Observations & Feedback (Outstanding/New):

1.  `_Exception` Tool Calls: While significantly reduced for "No Tool" generation steps, we should continue to monitor if they appear in other contexts (e.g., after specific tool outputs that might be complex or unexpected by the ReAct agent).

2.  Feature Request (Plan Visibility - UI): The approved plan could be made to remain visible (perhaps collapsed) in the UI after confirmation for better user context.

3.  Feature Request (Artifact Viewer - File Structure): Implement a file/folder structure view for the workspace.

4.  Feature Request (Artifact Viewer - PDF): Improve PDF viewing.

Proposed Roadmap & Areas for Improvement
----------------------------------------

### Phase 1: Core `DeepResearchTool` Functionality (Completed)

(Details as before)

### Phase 2: Agent Integration & Refinement (Ongoing)

1.  Test `DeepResearchTool` via Full Agent UI Flow (DONE)

2.  Address `_Exception` Tool Calls (User Observation 1) (Partially Addressed)

    -   Status: Significantly improved for "No Tool" generation steps due to Planner and ReAct prompt refinements.

    -   Next Action: Continue to monitor for `_Exception` calls in other scenarios, particularly after complex tool outputs. If they persist, further analyze the ReAct agent prompt (`backend/agent.py`) and specific tool output formats.

3.  Refine Retry Logic for "No Tool" Plan Steps

    -   Goal: Ensure robust retries if "No Tool" steps still fail for reasons other than ReAct formatting.

    -   Action: Review and potentially enhance the `Step Evaluator`'s suggestions for "No Tool" step retries.

4.  Implement Advanced Step Self-Correction via Evaluator-Driven Revision

    -   Goal: Enable the Step Evaluator to revise a failed step's *description/objective* for a more effective retry.

    -   Action:

        -   Update `STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE` to instruct the LLM to propose a `suggested_revised_step_description`.

        -   Add `suggested_revised_step_description: Optional[str]` to `StepCorrectionOutcome` model.

        -   Modify `message_handlers.py` to use this revised description during retries.

        -   (New Idea): Consider an optional "Quality Assurance" check by an Evaluator LLM after critical "No Tool" generation steps, even if no overt error occurred, to verify if the output meets quality/accuracy criteria defined in the plan step's expected outcome.

### Phase 3: Interactive Plan Execution (User-in-the-Loop - UITL/HITL) (Next Major Focus)

-   Goal: Enable the agent to request user input, clarification, or decisions at specific points *during* plan execution, and allow the user to view and request modifications to the plan.

-   Rationale: Crucial for researcher-centric AI, allowing for guidance, course correction, and leveraging domain expertise. Aligns with the priority of accuracy and user control.

-   Key Capabilities to Develop (Staged Approach):

    1.  Agent-Initiated Interaction Points:

        -   Planner generates special "interaction steps."

        -   Backend pauses, sends interaction request (prompt, data) to UI.

        -   UI renders interaction (e.g., selection from list, text input, confirmation).

        -   User responds; UI sends response to backend.

        -   Backend resumes plan using user's input.

        -   *Example interaction points:* Selecting relevant files from a list, choosing from search result themes, confirming a summary before further use.

    2.  User-Initiated Plan Review & Modification (Advanced UITL):

        -   Allow user to request viewing the current (upcoming) plan steps while the agent is paused or between steps.

        -   Provide UI for user to:

            -   Edit descriptions/inputs of upcoming steps.

            -   Reorder steps.

            -   Add new steps (potentially with suggestions for tools/inputs).

            -   Delete upcoming steps.

        -   Backend mechanism to receive, validate, and apply these plan modifications before resuming.

-   Core Components & Actions:

    -   Planner Enhancement (`planner.py`): Update prompts to generate interaction steps and define interaction parameters.

    -   `PlanStep` Model: Add fields for interaction type, prompt, data keys.

    -   Backend Execution Loop (`message_handlers.py`): Implement logic for pausing, sending/receiving interaction messages, managing state, and handling plan modifications.

    -   UI Development (`js/script.js`, `index.html`): Create UI elements for presenting interactions, capturing user input, and displaying/editing plans.

    -   New WebSocket Message Types: For all UITL communication.

### Phase 4: New Tool Development for Granularity & Accuracy

-   Goal: Create more specialized tools to make plan steps more focused, improve reliability of "No Tool" steps by offloading specific tasks, and enhance data handling.

-   Rationale: Aligns with the "accuracy over speed" and "overkill in subtasks if it helps" philosophy. Reduces ambiguity for LLMs.

-   Proposed New Tools (Wishlist - to be prioritized and designed):

    -   `list_files_tool`:

        -   Input: `path: Optional[str]`, `options: Optional[List[str]]` (e.g., recursive, details).

        -   Output: Formatted string or JSON list of files/directories in workspace.

    -   `find_file_tool`:

        -   Input: `name_pattern: str`, `search_path: Optional[str]`, `options: Optional[Dict]`.

        -   Output: List of matching file paths.

    -   `download_files_tool`:

        -   Input: `urls: Union[str, List[str]]`, `target_filenames: Optional[Union[str, List[str]]]`.

        -   Output: List of successfully downloaded file paths.

    -   `extract_text_segment_tool` (LLM-driven, focused):

        -   Input: `text_content: str`, `extraction_instruction: str` (e.g., "Extract section 'Executive Summary'").

        -   Output: `extracted_text: str`.

    -   `format_data_tool` (Deterministic or Focused LLM):

        -   Input: `data: Union[str, Dict, List]`, `target_format: str` (e.g., "markdown_table", "bullet_list", "json_string_from_dict").

        -   Output: Formatted string. (Replaces complex "No Tool" formatting steps).

    -   `structured_data_query_tool` (e.g., for CSV/JSON files):

        -   Input: `file_path: str`, `query: str` (e.g., SQL-like for CSV, JSONPath for JSON).

        -   Output: Query result.

    -   `summarize_text_tool` (Dedicated, Focused LLM):

        -   Input: `text_content: str`, `desired_length: Optional[str]`, `focus_keywords: Optional[List[str]]`.

        -   Output: `summary_text: str`.

    -   `validate_data_format_tool` (Deterministic or Focused LLM):

        -   Input: `text_content: str`, `expected_format: str`, `schema_definition: Optional[Dict]`.

        -   Output: `is_valid: bool`, `error_messages: Optional[List[str]]`.

    -   Workspace Document Indexing & Search (RAG-style):

        -   `ingest_workspace_documents_tool`: Chunks, embeds, and indexes specified workspace files into a task-specific vector store.

        -   `search_indexed_workspace_tool`: Performs semantic search over the indexed task documents.

### Phase 5: Playwright & Advanced Web Interaction (Parked for now, but setup is ready)

(Details as before)

### Phase 6: Further UX Enhancements & Advanced Features (Longer Term)

(Details as before, e.g., Interactive Plan Modification (Pre-Execution) can be merged/refined with Phase 3's advanced UITL)

This updated BRAINSTORM.md reflects our successful stability improvements and sets a clear direction for making the ResearchAgent more accurate, interactive, and powerful. The immediate next step is to continue monitoring for any remaining `_Exception` scenarios and then begin detailed design for Phase 3 (User-in-the-Loop, starting with agent-initiated interactions).