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

## Section: UI/UX and User-in-the-Loop (UITL) Enhancements

This section consolidates insights from reviewing Magentic-UI and Manus.ai, focusing on improving user interaction, chat clarity, and overall UITL capabilities for the ResearchAgent project.

### Subsection 1: Learning from Magentic-UI for Core UITL Functionality

Magentic-UI is explicitly designed as a **human-centered interface** aiming for collaboration with people on web-based tasks. Their UITL approach is woven throughout the planning and execution phases and offers valuable insights for ResearchAgent.

**Key UITL Features in Magentic-UI:**

* **Co-Planning**: Users can collaboratively create and approve step-by-step plans using a chat interface and a plan editor. This allows users to add, delete, edit, and regenerate steps, iterating on the plan before execution.
* **Co-Tasking**: Users can interrupt and guide task execution directly within the embedded web browser or through chat. The system can also proactively ask for clarifications and help when needed.
* **Action Guards**: Sensitive actions are only executed with explicit user approvals. This is configurable, and users can opt to always require permission.
* **Plan Learning and Retrieval**: The system can learn from previous runs to improve future task automation and save successful plans in a gallery for later retrieval.
* **Transparency**: Intermediate progress steps are clearly displayed, and users can observe web agent actions in real-time.
* **Explicit User Control**: Human agency and oversight are foundational. Plans are only executed with user approval, and users can pause, modify, or interrupt the agent at any time.
* **Allowed Websites List**: A safety feature where the agent will ask for explicit approval before visiting websites not on a pre-defined allowed list.

The `TRANSPARENCY_NOTE.md` for Magentic-UI emphasizes that it should always be used with human supervision and is a research prototype.

**Potential Leverage for ResearchAgent:**

* **Interactive Plan Execution (Aligns with `BRAINSTORM.md` Phase 3)**:
    * Magentic-UI's "Co-Tasking" and their mechanism for the agent to ask for clarifications or help are directly relevant to our "Agent-Initiated Interaction Points" (Phase 3.1). We can study how they pause execution and structure requests to the user.
    * Their plan editing interface could inform our "User-Initiated Plan Review & Modification" (Phase 3.2).
* **Tool Development (Aligns with `BRAINSTORM.md` Phase 4)**:
    * The `FileSurfer` agent in Magentic-UI, which "can locate files in the directory... and answer questions about them", is a good reference for our planned `list_files_tool` and `find_file_tool`.
    * Their `WebSurfer`'s enhanced capabilities (tab management, file upload) could guide improvements to our `PlaywrightSearchTool` if web-based tasks become more central.
* **UI Enhancements (Aligns with `BRAINSTORM.md` Phase 6)**:
    * Magentic-UI's feature of displaying web agent actions in real-time in a browser view is something we could consider.
    * Their "Plan Learning and Retrieval" and "plan gallery" could inspire future features for saving and reusing successful research plans in ResearchAgent.
* **Safety and Control**:
    * The "Action Guards" and "Allowed Websites List" are good examples of safety mechanisms, aligning with our idea for a "Permission Gateway for Sensitive Tools" (Phase 6).

**Differences and Considerations for ResearchAgent:**

* **Primary Focus**: Magentic-UI is heavily focused on **web Browse automation**. ResearchAgent has a broader scope including deep research synthesis and varied tool use.
* **Agent Implementation**: Magentic-UI is built using AutoGen, while ResearchAgent uses LangChain. Direct code reuse will be limited, but architectural concepts are adaptable.

### Subsection 2: Improving Chat Message Clarity & Status Visualization (Inspired by Manus.ai)

**Observation (Based on `UI_pic1.jpg` - ResearchAgent v2.4):**

* The current ResearchAgent UI's central chat panel primarily displays messages from the agent as continuous blocks of text.
* While detailed logs are in the Monitor Panel, the main chat flow can be dense.
* It's challenging to quickly differentiate between agent's conversational responses, internal "thoughts", tool usage notifications, tool outputs, and discrete status updates.

**Inspiration from Manus.ai (Based on `manus_ai.jpg`):**

Manus.ai's interface presents a more granular and visually differentiated stream:

* **Distinct Message Types:** User prompts, agent replies, specific actions (e.g., "Cloning AI-Scientist repository"), and status updates (e.g., "Executing command") are separate, identifiable blocks.
* **Visual Cues:** Implied use of distinct formatting, icons, or layouts.
* **Action-Oriented Updates:** Actions like "Sterling to clone..." or "Install project dependencies" are presented as individual steps.
* **Integrated Status:** Statuses like "Executing command" are embedded directly in the flow.

**Proposed Improvements for ResearchAgent Chat UI (Leveraging Manus.ai Concepts):**

1.  **Visually Distinct Message Components for Agent Activity:**
    * Introduce new UI rendering for specific events currently in monitor logs or verbose agent messages.
    * **Agent "Thinking" / Status Updates:**
        * Render short status lines (e.g., "Attempting web search for 'X'...") with a distinct style (smaller font, icon), similar to `BRAINSTORM.md` (Agent Thinking Status Line Style) and Manus.ai's itemized actions.
    * **Tool Usage Indication:**
        * Display a clear, concise message when a tool starts: "Using Tool: `TavilyAPISearchTool` with input: `{'query': '...'}`". This could be collapsible.
    * **Tool Output/Observation Summary:**
        * Show a brief, user-friendly summary of a tool's observation in the chat, distinct from the agent's subsequent reasoning. E.g., "Successfully read 'document.pdf' (1500 words)."
    * **Plan Step Execution Markers:**
        * "Executing Step 2: Summarize findings."
        * "Step 2 completed successfully." or "Step 2 failed: [brief error]."

2.  **Technical Implementation Considerations:**
    * **WebSocket Message Types:** Define new `message.type` values (e.g., `agent_action_status`, `tool_attempt`) or add metadata to existing messages for the UI to differentiate rendering.
    * **Frontend Rendering (`script.js`):** Update `addChatMessage` or create new functions to handle these distinct message types, applying unique CSS/HTML.
    * **Callback Handler (`callbacks.py`):** `WebSocketCallbackHandler` to send these granular WebSocket messages (e.g., `on_tool_start` sends `tool_attempt`).

3.  **Benefits:**
    * **Improved Readability:** Easier to scan chat log for key actions and outcomes.
    * **Better Real-time Understanding:** Users can more easily follow the agent's process.
    * **Reduced Reliance on Monitor Panel:** Main chat becomes more informative for at-a-glance status.
    * **Enhanced UITL Potential:** Clearer status updates provide better context for user intervention, aligning with plan visibility goals.

This hybrid approach (part conversational, part structured log) should make ResearchAgent's operations more transparent and easier for researchers to follow.
