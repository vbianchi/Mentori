# BRAINSTORM.md - ResearchAgent Project (V1.0 Go-Live Target & Beyond)

This document tracks the current workflow, user feedback, and brainstorming ideas for the ResearchAgent project.

## Current Version & State (Targeting V1.0 Go-Live within 2 Months)

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (Improved).
-   Chat UI/UX Refinement (Significant Progress):
    -   **Visual Design & Readability:** Achieved consistent sub-step indentation, adjusted message bubble widths (User/RA/Plan ~60% fit-to-content, Sub-steps ~40%, Step titles ~60% with wrap). Agent Avatar for final RA messages. Blue line removed from RA/Plan messages. General UI and Token area font sizes increased. Role LLM selectors styled with color indicators.
    -   **Interactivity:** Collapsible major agent steps and tool outputs (via label click).
    -   **Persistence & Consistency:** Confirmed plans loaded from history render consistently.
    -   **Bug Fixes:** `read_file` tool output displays correctly and is nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat now works. Final synthesized answer from agent correctly displayed.
-   Plan Proposal UI & Persistence (COMPLETE).
-   Token Counter UI & Functionality (FIXED & ENHANCED).
-   File Upload Functionality (FIXED).
-   Enhanced In-Chat Tool Feedback & Usability (Core Implemented & Refined).

## Immediate Focus & User Feedback / Known Issues / Proposed Enhancements (V1.0 Go-Live Focus):

1.  **CRITICAL (MUST HAVE) - BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button:**
    -   **Observation:** Switching UI tasks or using the STOP button does not reliably stop the agent processing the previous task; its status updates can bleed into the new task view. The STOP button is currently not effective, particularly for plan execution.
    -   **Goal for V1.0:** Ensure that when a context switch _occurs in the UI_, the backend _robustly cancels_ the agent task associated with the _previous_ UI context. Make the STOP button fully functional to terminate the currently designated active agent task.
    -   **Challenge:** Requires careful management of asyncio tasks on the backend and ensuring cancellation propagates effectively. Current `asyncio.Task.cancel()` is not reliably interrupting. Exploring `asyncio.Event` for cooperative cancellation.
2.  **HIGH (MUST HAVE) - BUG - ARTIFACT VIEWER REFRESH:**
    -   Artifact viewer does not consistently or immediately auto-update after a task completes and writes files mid-plan.
3.  **HIGH (MUST HAVE) - AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    -   **Goal for V1.0:** Ensure the PCEE loop's Evaluator component reliably assesses step success, particularly checking if actual content was produced vs. a description of it. Ensure the retry mechanism (currently `agent_max_step_retries=1`) effectively uses evaluator feedback for simple retries, especially for "No Tool" steps where the LLM needs to provide direct content. This is key for improving the efficiency of scientific results.
4.  **HIGH (MUST HAVE) - DEV OPS / STABILITY - Comprehensive Testing (Core Functionality):**
    -   **Goal for V1.0:** Implement/expand unit and integration tests for critical backend and frontend components, especially task cancellation, agent lifecycle, and core tool usage.
5.  **MEDIUM (SHOULD HAVE) - UI/UX - Finalize "View \[artifact\] in Artifacts" Links:**
    -   Complete functionality for links from tool output messages to the artifact viewer.
    -   **Enhancement Idea:** Clicking this could also switch the right-hand panel to a more general "folder viewer" mode for the current task's workspace, highlighting the specific artifact.
6.  **LOW (NICE TO HAVE) - UI/UX POLISH:**
    -   **A. Global "Agent Thinking Status" Line Review:** Review behavior and appearance.
    -   **B. Agent Step Announcement Styling:** Consider further styling (e.g., boxing, copy button).
    -   **C. Copy Button Centering Bug:** Small bug: Copy button sometimes centered in chat UI.
    -   **D. Monitor Log Readability / Color-Coding:** Verify/implement CSS for log differentiation.
7.  **LOW (NICE TO HAVE) - BACKEND/DEBUG:**
    -   **A. Plan File Status Update Warnings:** Address backend logs warnings about not finding step patterns.
    -   **B. "Unknown" History Message Types Review:** Confirm handling of internal DB message types.

## Future Brainstorming / More Complex Enhancements (Post V1.0 Go-Live)

### SHOULD HAVE (Important for V1.x releases):

1.  **Enhanced Agent Capabilities & Efficiency:**
    -   **Improved Agent Memory / Workspace RAG (Basic):** Implement basic retrieval from current task workspace files to improve contextual understanding for the agent. Focus on making `read_file` and tool outputs more seamlessly available to subsequent steps.
    -   **Streaming LLM Responses (Final Answers):** Implement token-by-token streaming for agent's final answers for better perceived responsiveness.
    -   **Refined Error Parsing & Reporting:** Improve how the agent understands and reports errors from tools or LLM calls, making it easier to debug or for the evaluator to suggest corrections.
    -   **Robust Asynchronous Task Cancellation (Advanced):** Post initial STOP button fix, explore more advanced `asyncio` patterns (e.g., `asyncio.Event`, `asyncio.shield`) for deeper cancellation robustness.
2.  **Multi-Tasking & User Control:**
    -   **Asynchronous Background Task Processing (Basic Stop/Switch):** Ensure that if full background processing is deferred, task switching at least reliably stops the previous task and cleans up its state to prevent interference. Global chat input should be disabled if any task is processing.
    -   **Optional Tools (e.g., Web Search):** Allow users to enable/disable tools like Tavily web search for privacy/cost. Backend to respect choices and UI to communicate impact.
3.  **Advanced User-in-the-Loop (UITL/HITL) Capabilities:**
    -   Introduce more sophisticated mechanisms for users to intervene, guide, or correct the agent during plan execution.

### NICE TO HAVE (Valuable additions for future iterations):

1.  **Advanced Agent Reasoning & Self-Correction (Full):**
    -   **Goal:** Improve the robustness and success rate of agent operations, particularly for complex plans.
    -   **Ideas:** Meta-Cognitive Loop, Self-Debugging/Rewriting Capabilities, Dynamic Plan Adjustment, Learning from Failure (Very Long Term).
2.  **Comprehensive Tool Ecosystem Expansion:**
    -   **Goal:** Broaden the range of research tasks ResearchAgent can effectively assist with.
    -   **Potential New Task Areas & Tool Ideas:**
        -   **Literature Review & Analysis:** Enhanced PubMed/Semantic Scholar/ArXiv search, PDF parsing for specific sections, Biomedical NER, Relation Extraction.
        -   **Data Analysis & Visualization:** **Rscript Execution Tool**, Python Data Analysis Tool (beyond REPL), Statistical API/library tool.
        -   **Bioinformatics Specific Tasks:** Wrappers for BLAST, ClustalW, GATK (subset), samtools, bedtools.
        -   **Document Preparation & Formatting:** Pandoc wrapper, citation management tool interface.
3.  **UI/UX & Workspace Enhancements:**
    -   **Integrated Folder Viewer:** Right-hand panel mode for file/folder structure of task workspace.
    -   **Direct Artifact Manipulation (Future):** Basic file operations from UI (delete, rename).
    -   **Dedicated "Agent Activity/Steps" Panel:** Separate UI area for structured, real-time view of agent's plan steps.
    -   **Further Chat Information Management:** Options for filtering, searching, or summarizing long chat histories.
4.  **Backend & Architecture:**
    -   Scalability improvements for handling more users/agents.
    -   Specialized Agent Personas/Configurations.
5.  **Deployment & DevOps:**
    -   Broader local/cloud deployment options.

## Known Good States / Checkpoints

-   Token Counting: Working for all roles after callback propagation fixes.
-   File Upload: Functional.
-   In-Chat Tool Feedback: UI and backend support implemented and refined.
-   Plan Proposal UI & Persistence: Complete.

## Open Questions / Areas for Investigation

-   How to make LangChain's `ainvoke` calls (especially for LLMs) more responsive to `asyncio.Task.cancel()` when the task they are running within is cancelled.
-   The exact timing and interleaving of `asyncio` tasks when `process_cancel_agent` sets the flag versus when callbacks check it.
-   Best practices for ensuring `asyncio.CancelledError` propagates correctly through multiple layers of `await` calls, especially when third-party libraries are involved.
Chat UI Simulation Details (Target: simulation_option6.html - Achieved Visually as a Base, with further enhancements) - This section seems to refer to a specific HTML file used for UI mockups/prototyping. Assuming its content is static or managed elsewhere, it's noted here for completeness but not detailed further.


# BRAINSTORM.md - ResearchAgent Project (V1.0 Go-Live Target & Beyond)
...
## Immediate Focus & User Feedback / Known Issues / Proposed Enhancements (V1.0 Go-Live Focus):

1.  **CRITICAL (MUST HAVE) - ARCHITECTURAL REFACTORING - "Plug and Play" Tool System:**
    * **Goal for V1.0:** Implement a dynamic tool loading mechanism using a JSON configuration file (`tool_config.json`) to streamline future tool development and improve system maintainability.
    * **Approach:** Design config structure, implement `tool_loader.py`, refactor `get_dynamic_tools`, migrate `read_file` as pilot, implement robust logging for tool load status.
    * This is prioritized to build a scalable foundation before extensive new tool additions.
2.  **CRITICAL (MUST HAVE) - BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button (Following Tool Refactor):**
    * **Observation:** Switching UI tasks or using the STOP button does not reliably stop the agent processing the previous task; its status updates can bleed into the new task view. The STOP button is currently not effective, particularly for plan execution.
    * **Goal for V1.0:** Ensure that when a context switch _occurs in the UI_, the backend _robustly cancels_ the agent task associated with the _previous_ UI context. Make the STOP button fully functional to terminate the currently designated active agent task.
    * **Challenge:** Requires careful management of asyncio tasks on the backend and ensuring cancellation propagates effectively. Current `asyncio.Task.cancel()` is not reliably interrupting. Exploring `asyncio.Event` for cooperative cancellation.
3.  **HIGH (MUST HAVE) - BUG - ARTIFACT VIEWER REFRESH:**
    * Artifact viewer does not consistently or immediately auto-update after a task completes and writes files mid-plan.
4.  **HIGH (MUST HAVE) - AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    * **Goal for V1.0:** Ensure the PCEE loop's Evaluator component reliably assesses step success, particularly checking if actual content was produced vs. a description of it. Ensure the retry mechanism (currently `agent_max_step_retries=1`) effectively uses evaluator feedback for simple retries, especially for "No Tool" steps where the LLM needs to provide direct content.
5.  **HIGH (MUST HAVE) - DEV OPS / STABILITY - Comprehensive Testing (Core Functionality):**
    * **Goal for V1.0:** Implement/expand unit and integration tests for critical backend (tool loading, task cancellation, agent lifecycle, core tools) and frontend components.
6.  **MEDIUM (SHOULD HAVE) - UI/UX - Finalize "View [artifact] in Artifacts" Links:**
    * Complete functionality for links from tool output messages to the artifact viewer.
    * **Enhancement Idea:** Clicking this could also switch the right-hand panel to a more general "folder viewer" mode for the current task's workspace, highlighting the specific artifact.
7.  **LOW (NICE TO HAVE) - UI/UX POLISH:**
    * **A. Global "Agent Thinking Status" Line Review:** Review behavior and appearance.
    * **B. Agent Step Announcement Styling:** Consider further styling (e.g., boxing, copy button).
    * **C. Copy Button Centering Bug:** Small bug: Copy button sometimes centered in chat UI.
    * **D. Monitor Log Readability / Color-Coding:** Verify/implement CSS for log differentiation.
    * **E. UI for Tool Status (Traffic Lights):** Display configured tools and their load status in Agent Workspace based on backend data from new tool loader.
8.  **LOW (NICE TO HAVE) - BACKEND/DEBUG:**
    * **A. Plan File Status Update Warnings:** Address backend logs warnings about not finding step patterns.
    * **B. "Unknown" History Message Types Review:** Confirm handling of internal DB message types.

## Future Brainstorming / More Complex Enhancements (Post V1.0 Go-Live & Tool Refactor)

### SHOULD HAVE (Important for V1.x releases):
... (Content largely as before, but R-tool will be listed as "Next new tool" here or under a dedicated new tools section)

### NICE TO HAVE (Valuable additions for future iterations):
...
2.  **Comprehensive Tool Ecosystem Expansion (To leverage new "Plug and Play" system):**
    -   **Goal:** Broaden the range of research tasks ResearchAgent can effectively assist with.
    -   **Potential New Task Areas & Tool Ideas:**
        ...
        -   **Data Analysis & Visualization:** **Rscript Execution Tool (Planned post-refactor)**, Python Data Analysis Tool (beyond REPL), Statistical API/library tool.
...

## Open Questions / Areas for Investigation / Architectural Considerations

-   How to make LangChain's `ainvoke` calls (especially for LLMs) more responsive to `asyncio.Task.cancel()` when the task they are running within is cancelled.
-   The exact timing and interleaving of `asyncio` tasks when `process_cancel_agent` sets the flag versus when callbacks check it.
-   Best practices for ensuring `asyncio.CancelledError` propagates correctly through multiple layers of `await` calls, especially when third-party libraries are involved.
-   **Finalizing design for `tool_config.json` structure and dynamic `tool_loader.py` for the "Plug and Play" tool system refactoring.**
...