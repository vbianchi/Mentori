BRAINSTORM.md - ResearchAgent Project (v2.4)
============================================

This document tracks the current workflow, brainstorming ideas, user feedback, and the proposed roadmap for the ResearchAgent project.

**Current Version & State (v2.4 - Enhanced Stability & Accuracy):**
The ResearchAgent is at v2.4. Key recent advancements include:
-   **`DeepResearchTool`**: Fully functional across all its phases (search, curation, extraction, and report synthesis).
-   **Planner Refinements**:
    -   Improved granularity for "No Tool" steps: Complex generation tasks (e.g., creating Markdown tables) are now broken down by the Planner into simpler sub-steps (e.g., data generation, then formatting).
    -   Final Answer Synthesis: For user queries requiring multiple distinct pieces of information, the Planner now adds a final "No Tool" step to synthesize these into a comprehensive answer.
-   **Agent Execution Stability**:
    -   The ReAct agent's main prompt (`backend/agent.py`) has been refined for clearer `Final Answer` formatting, significantly reducing `_Exception` tool calls, especially in "No Tool" generation steps.
    -   The directive to the Executor for each plan step now includes the 'precise expected outcome', enhancing adherence to intermediate step goals.
-   **Successful Complex Plan Execution**: The agent has demonstrated successful execution of multi-step plans involving chained "No Tool" generations, file I/O (`write_file`, `read_file`), and information extraction, culminating in a correct, synthesized final answer.
-   **Tool Updates**: `read_file` operation has been verified. The `Python_REPL` tool description has been refined for clarity on appropriate use cases.
-   All previously listed UI, Backend, Agent Architecture, LLM Configuration, Callbacks, and Core Tool functionalities remain operational.

**Current Complex Task Flow (Illustrative - Post-Refinements):**
The P-C-E-E pipeline is more robust due to the Planner and Executor enhancements mentioned above. For instance, generating a Markdown table and then using it now involves:
1.  Planner: Step 1 (No Tool) - Generate data (e.g., as JSON). Step 2 (No Tool) - Format JSON to Markdown. Step 3 - `write_file`, etc.
2.  Executor: Handles these simpler "No Tool" steps with fewer ReAct formatting errors. Each step is guided by its specific `expected_outcome`.
(The rest of the P-C-E-E flow description as previously outlined remains conceptually the same but benefits from these improvements).

**User Observations & Feedback (Outstanding/New):**
1.  `_Exception` Tool Calls: While significantly reduced for "No Tool" generation steps, continued monitoring is needed for other contexts (e.g., after outputs from certain complex tools, or if the Executor LLM still occasionally misformats its `Final Answer`).
2.  Feature Request (Plan Visibility - UI): The approved plan could be made to remain visible (perhaps collapsed) in the UI after confirmation for better user context.
3.  Feature Request (Artifact Viewer - File Structure): Implement a file/folder structure view for the workspace.
4.  Feature Request (Artifact Viewer - PDF): Improve PDF viewing.
5.  **User Priority:** Strong emphasis on **accuracy over speed**, accepting more granular plan steps ("overkill") if it improves reliability.
6.  **User Priority:** High desire for **User-in-the-Loop (UITL/HITL)** capabilities, including the ability for researchers to provide input *during* plan execution and potentially modify the plan.

**Proposed Roadmap & Areas for Improvement**

### Phase 1: Core `DeepResearchTool` Functionality **(COMPLETED)**
-   The `DeepResearchTool` is fully functional, including all four phases: Initial Search, Source Curation, Deep Content Extraction, and Information Synthesis & Report Generation.

### Phase 2: Agent Integration & Refinement (Ongoing Priority)

1.  **Test `DeepResearchTool` via Full Agent UI Flow (DONE)**
    -   Successfully validated that the Planner selects `DeepResearchTool` appropriately and that it integrates into the P-C-E-E pipeline.
2.  **Continue Monitoring & Mitigating `_Exception` Tool Calls**
    -   **Status:** Significantly improved for "No Tool" generation steps due to Planner and ReAct prompt refinements.
    -   **Next Action:** Monitor for `_Exception` calls in new scenarios or with different LLMs/complex tool outputs. If persistent, further analyze the ReAct agent prompt (`backend/agent.py`) and specific tool output formats. Consider if certain complex tool outputs need a "post-processing/simplification" step or tool.
3.  **Implement Advanced Step Self-Correction via Evaluator-Driven Revision (High Priority)**
    -   **Goal:** Enhance accuracy and autonomous error recovery by enabling the Step Evaluator to revise a failed step's *description/objective* for a more effective retry.
    -   **Action:**
        -   Update `STEP_EVALUATOR_SYSTEM_PROMPT_TEMPLATE` to instruct the LLM to propose a `suggested_revised_step_description`.
        -   Add `suggested_revised_step_description: Optional[str]` to the `StepCorrectionOutcome` Pydantic model in `evaluator.py`.
        -   Modify `message_handlers.py` to use this revised description during retries.
    -   **(New Consideration based on user feedback):** Explore an optional "Quality Assurance" check by an Evaluator LLM after critical "No Tool" generation steps (even if no overt error occurred) to verify if the output meets quality/accuracy criteria defined in the plan step's expected outcome, before the plan proceeds.
4.  **Refine Retry Logic for "No Tool" Plan Steps (Medium Priority)**
    -   **Goal:** Ensure robust retries if "No Tool" steps still fail for reasons other than ReAct formatting (e.g., LLM refuses to answer, content policy issues for the generation).
    -   **Action:** Review and potentially enhance the `Step Evaluator`'s suggestions and the retry loop's handling for these specific "No Tool" failures.

### Phase 3: Interactive Plan Execution (User-in-the-Loop - UITL/HITL) **(Next Major Development Focus)**

-   **Goal:** Enable the agent to request user input, clarification, or decisions at specific points *during* plan execution, and empower the user to view and request modifications to the plan, aligning with the need for researcher oversight and control.
-   **Key Capabilities to Develop (Staged Approach):**
    1.  **Agent-Initiated Interaction Points (Foundation):**
        -   Planner: Generates special "interaction steps" defining the prompt/question for the user and the type of input expected.
        -   Backend: Pauses plan execution, sends interaction requests (with necessary data like file lists or summaries) to UI, and processes user responses.
        -   UI: Renders interaction requests (e.g., selection lists, text inputs, confirmations) and sends user input back.
        -   *Examples:* User selects relevant files from a list, chooses from search result themes, confirms a summary.
    2.  **User-Initiated Plan Review & Modification (Advanced):**
        -   UI: Allows user to view upcoming plan steps (e.g., during an agent-initiated pause or via a dedicated "review plan" button).
        -   UI: Provides interface for users to request edits (modify description/inputs, reorder, add, delete upcoming steps).
        -   Backend: Mechanism to receive, validate, and apply plan modifications, then resume execution intelligently.
-   **Core Components for Development:** `PlanStep` model updates, Planner prompt enhancements, backend execution loop modifications in `message_handlers.py` (for pausing, state management, processing responses/edits), new WebSocket message types, and new UI components in `script.js`.

### Phase 4: New Tool Development for Granularity & Accuracy (Important Ongoing Initiative)

-   **Goal:** Create more specialized tools to make plan steps more focused, improve reliability by offloading specific tasks from general "No Tool" LLM steps, and enhance data handling, supporting the "accuracy over speed" philosophy.
-   **Proposed New Tools (Wishlist - To Be Prioritized and Designed):**
    -   `list_files_tool`: Lists files/directories in the workspace (safer than raw `ls`). Output: Formatted string or JSON.
    -   `find_file_tool`: Searches for files by name pattern or other criteria in the workspace. Output: List of paths.
    -   `download_files_tool`: Downloads files from given URLs directly to the workspace.
    -   `extract_text_segment_tool`: (LLM-driven) Extracts specific sections or information from a larger text based on instructions (e.g., "Extract 'Executive Summary' section").
    -   `format_data_tool`: (Deterministic or Focused LLM) Converts data between simple formats (e.g., JSON to Markdown table, list to bullet points).
    -   `structured_data_query_tool`: Queries structured data from files (e.g., CSV, JSON) using simple query languages.
    -   `summarize_text_tool`: (Dedicated LLM) Summarizes text with more control over length, focus.
    -   `validate_data_format_tool`: Checks if generated text conforms to an expected format (e.g., JSON, specific CSV structure).
    -   **Workspace Document Indexing & Search (RAG-style Tools - Longer Term Integration):**
        -   `ingest_workspace_documents_tool`: Chunks, embeds, and indexes workspace files.
        -   `search_indexed_workspace_tool`: Performs semantic search over indexed task documents.

### Phase 5: Playwright & Advanced Web Interaction (Parked)
(Details as before - revisit when specific complex web automation tasks are identified)

### Phase 6: Further UX Enhancements & Advanced Features (Longer Term)
-   Interactive Plan Modification (Pre-Execution) - (May be partially covered by advanced UITL in Phase 3).
-   Permission Gateway for Sensitive Tools.
-   Improved PDF Viewing & Artifact Navigation (User Points 3 & 4).
-   Live Plan in Chat UI (User Observation 2 - Advanced).
-   Advanced Re-planning based on Overall Evaluator feedback (e.g., full plan regeneration if current approach fails).
-   Streaming output for LLM responses to the UI.

This updated `BRAINSTORM.MD` reflects our current successes and sets a clear path forward, prioritizing agent stability, accuracy, and increased researcher interaction and control.

**Our immediate technical focus should be:**
1.  Continuing to monitor for any residual `_Exception` scenarios.
2.  Beginning the design and implementation of **"Advanced Step Self-Correction via Evaluator-Driven Revision"** (Phase 2.3).
3.  Concurrently, starting the detailed design for the foundational stage of **"Interactive Plan Execution (User-in-the-Loop)"** (Phase 3.1: Agent-Initiated Interaction Points).
