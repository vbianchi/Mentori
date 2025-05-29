# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project. Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (Improved):
    -   Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic.
-   Chat UI/UX Refinement (Significant Progress, Nearing Completion for this phase):
    -   **Visual Design Achieved & Enhanced (based on `simulation_option6.html` as a foundation):**
        -   User messages with right side-lines. System/status messages use a blue outer left side-line (RA final answers and Plan Proposals now have this line removed). No side-lines for major step announcements. Nested/indented component-specific lines for sub-statuses & agent thoughts are rendering.
        -   **Improved Alignment & Indentation:** Sub-steps (thoughts, tool outputs, sub-statuses) within major agent steps now have a more consistent and deeper indentation (increased to ~40px).
        -   **Font Sizes:** General UI font size increased. Token Usage area font size specifically increased.
        -   HTML tags (`<strong>`, `<em>`) now render correctly.
    -   **Interactivity & Layout Enhancements:**
        -   **Collapsible Elements:** Major agent steps are now collapsible. Tool outputs in chat are collapsible by clicking their label.
        -   **Message Bubble Widths Adjusted:** User messages, final RA answers (now fit-to-content up to max), and Plan Proposals use ~60% of the central panel width. Sub-components within agent steps (thoughts, tool outputs, sub-statuses) use ~40% width. Major step titles also wrap and adhere to ~60% width.
        -   **Agent Avatar:** An "RA" avatar is now displayed next to final agent answer messages.
        -   **Blue Line Removal:** The left blue line has been removed from final RA messages and Plan Proposal blocks.
        -   **Role LLM Selectors:** Labels in chat header are now white with small colored square indicators matching agent step colors.
    -   **Persistence Implemented & Refined:**
        -   All new message structures (major steps, sub-statuses, thoughts, tool outputs) are saved to the database and reloaded into chat history.
        -   **FIXED:** Confirmed plans loaded from history now render with visual consistency to plans confirmed live (correct width, no blue line, correct status text).
    -   **Bug Fixes:**
        -   **`read_file` Tool Output:** Content from the `read_file` tool is now correctly displayed in its chat bubble and nested correctly.
        -   **Chat Scroll Behavior:** Fixed issue where chat would unnecessarily scroll to the bottom when expanding/collapsing message bubbles (like tool outputs).
        -   **Sub-step Nesting:** Ensured tool outputs, thoughts, and sub-statuses are correctly nested within their parent major step and collapse/expand with it.
-   Plan Proposal UI & Persistence (COMPLETE).
-   Token Counter UI & Functionality (FIXED & ENHANCED): Expandable UI for token breakdown by role is in place. Token counting functionality now works for all individual agent/LLM roles. Font size increased.
-   File Upload Functionality (FIXED): File uploads to the task workspace are now functional.
-   **FEATURE: Enhanced In-Chat Tool Feedback & Usability (Core Functionality Implemented & Refined):**
    -   **Backend:** Sends `tool_result_for_chat` WebSocket messages from `callbacks.py` upon tool completion.
    -   **Persistence:** These `tool_result_for_chat` messages are saved to the database and reloaded into history.
    -   **Frontend Rendering:**
        -   `tool_result_for_chat` messages are displayed in a new, distinct chat bubble style, similar to "thought" messages, and correctly nested within their parent step.
        -   Longer tool outputs are collapsible by clicking their label.
        -   Placeholder for "View \[artifact\_filename\] in Artifacts" button if `artifact_filename` is present in payload (functionality pending).
    -   **Copy to Clipboard:** Functionality added for:
        -   Tool output messages.
        -   Agent thoughts.
        -   Final agent answers.
        -   `<pre>` (code) blocks within any message.
    -   **Planner Prompting:** Refined for better final summary messages from the agent, encouraging synthesis of actions and outcomes.

Immediate Focus & User Feedback / Known Issues / Proposed Enhancements:

1.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Resumes):**
    -   **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files mid-plan. Updates correctly at the end of the full plan.
    -   **Status:** Debugging paused. Backend triggers appear to send refresh messages correctly. The issue is likely related to frontend JavaScript event loop contention when the agent is busy, delaying the processing of `update_artifacts` messages.
    -   **Next Step:** Resume debugging, focusing on frontend message processing and potential optimizations when the agent is active.
2.  **UI/UX POLISH & REVIEW (Low Priority - Most critical items addressed):**
    -   **A. Chat Message Visuals & Density (Largely Addressed):**
        -   **Status:** Significantly improved. Sub-step indentation is now deeper and more consistent. Collapsible major steps help manage density. Font sizes increased.
        -   **Proposal (Remaining if needed):** Minor review of overall vertical spacing between different message types.
    -   **B. Button Placement & Consistency (Largely Addressed):**
        -   **Status:** Tool output expansion is now primarily by label click; major steps are collapsible via their titles. Copy buttons are generally consistent.
        -   **Proposal (Remaining if needed):** Final visual audit of any remaining interactive elements.
    -   **C. Monitor Log Readability:**
        -   **Problem:** While color-coding is planned/partially implemented, overall scannability and contrast for different log types in the Monitor Panel could be improved.
        -   **Proposal:** Finalize and test CSS rules for Monitor Log color-coding. Ensure sufficient text contrast and clear visual differentiation between log sources (system, LLM, tool, error, etc.).
    -   **D. "Agent Thinking Status" Line Review:**
        -   **Problem:** The global "agent-thinking-status" line at the bottom of the chat might be redundant or slightly confusing now that more granular sub-statuses and thoughts appear within agent steps.
        -   **Proposal:** Review the necessity and behavior of the global status line. Consider if it should only be active when no specific step-level status is available (e.g., initial planning, overall evaluation).
    -   **E. "View in Artifacts" Link for Tool Outputs (Pending):**
        -   **Problem:** Placeholder logic currently, needs full implementation.
        -   **Proposal:** Implement the functionality for the "View \[artifact\_filename\] in Artifacts" button within `tool_result_for_chat` messages. Clicking this should smoothly highlight or open the relevant artifact in the Artifact Viewer panel. (Depends on Artifact Viewer refresh bug being addressed).
    -   **F. Agent Step Announcement Styling (Pending - from `prompt.txt` \[source: 27\]):**
        -   **Request:** Restyle agent step announcements (e.g., "Step X/Y: Description") to be boxed and include a copy button, similar to thoughts/tool outputs.
        -   **Status:** Currently, step titles are not boxed and do not have individual copy buttons. They are collapsible.
        -   **Proposal:** Evaluate if boxing and adding a copy button to step titles is still desired or if the current collapsible title is sufficient.
3.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**
    -   **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.`
    -   **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly.
4.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):**
    -   **Issue:** Backend logs warnings for some DB message types during history load.
    -   **Status:** Mostly addressed by better categorization in `task_handlers.py`.
    -   **Check:** Confirm current behavior is adequate and all necessary historical message types are handled appropriately for replay to chat or monitor.

Future Brainstorming / More Complex Enhancements:

-   **Advanced Chat Information Management (Future):**
    -   **Problem:** Very verbose agent interactions (many tool uses, long thoughts for a single step) can still lead to information overload in the chat, even with current collapsibility.
    -   **Idea 1 (Filtering/Toggling):** Explore adding UI controls to filter the chat view (e.g., toggle visibility of all "thoughts", all "tool outputs", or all "sub-statuses") to allow users to focus on major steps or final answers.
    -   **Idea 2 (Smart Chat Summaries for Tools):** For very verbose tool outputs (e.g., search results), consider if the default in-chat display could be an even more concise summary _generated by an LLM specifically for the chat_, with the "Expand" button revealing the full tool output we currently render.
-   **Ongoing Planner & Executor Prompt Engineering:**
    -   **Problem:** Ensuring the Planner consistently creates optimal plans (especially the final synthesis step) and that the Executor robustly follows complex instructions requires continuous refinement.
    -   **Proposal:** Periodically review agent performance on complex queries involving multiple file generations, multi-part answers, or error recovery. Collect failure cases and use them to iterate on the Planner's system prompt and the Executor's ReAct prompt.

Chat UI Simulation Details (Target: simulation_option6.html - Achieved Visually as a Base, with further enhancements):
(No changes to this section)