# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.
Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

  - Core Agent Logic & Tool Integration (Improved):
      - Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic.
  - Chat UI/UX Refinement (Largely Implemented, Minor Fixes Ongoing):
      - **Visual Design Achieved (based on `simulation_option6.html`):**
          - User messages with right side-lines, unified blue outer left side-lines for system/plan/final messages, no side-lines for major steps, and nested/indented component-specific lines for sub-statuses & thoughts are rendering.
      - HTML tags (`<strong>`, `<em>`) now render correctly.
      - **Persistence Implemented:** All new message structures (major steps, sub-statuses, thoughts) are saved to the database and reloaded into chat history.
  - Plan Proposal UI & Persistence (COMPLETE).
  - Token Counter UI & Functionality (FIXED): Expandable UI for token breakdown by role is in place. Token counting functionality now works for all individual agent/LLM roles.
  - File Upload Functionality (FIXED): File uploads to the task workspace are now functional.
  - **FEATURE: Enhanced In-Chat Tool Feedback & Usability (Core Functionality Implemented):**
      - **Backend:** Sends `tool_result_for_chat` WebSocket messages from `callbacks.py` upon tool completion.
      - **Persistence:** These `tool_result_for_chat` messages are saved to the database and reloaded into history.
      - **Frontend Rendering:**
          - `tool_result_for_chat` messages are displayed in a new, distinct chat bubble style, similar to "thought" messages.
          - Longer tool outputs are collapsible with "Expand" / "Collapse" functionality.
          - Placeholder for "View [artifact_filename] in Artifacts" button if `artifact_filename` is present in payload.
      - **Copy to Clipboard:** Functionality added for:
          - Tool output messages.
          - Agent thoughts.
          - Final agent answers.
          - `<pre>` (code) blocks within any message.
      - **Planner Prompting:** Refined for better final summary messages from the agent, encouraging synthesis of actions and outcomes.

Immediate Focus & User Feedback / Known Issues / Proposed Enhancements:

1.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Paused):**
    * **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files mid-plan. Updates correctly at the end of the full plan.
    * **Status:** Debugging paused. Backend triggers appear to send refresh messages correctly. The issue is likely related to frontend JavaScript event loop contention when the agent is busy, delaying the processing of `update_artifacts` messages.
    * **Next Step:** Resume debugging, focusing on frontend message processing and potential optimizations when the agent is active.

2.  **UI/UX POLISH & REVIEW (Post v2.5.3 Core - Next Focus after critical bugs):**
    * **A. Chat Message Visuals & Density:**
        * **Problem:** Current indentation for nested items (sub-status, thoughts, tool outputs within a step) can sometimes feel too deep or lead to a "jagged" appearance. Spacing between different message elements could be more consistent.
        * **Proposal:** Review and refine CSS for indentation, margins, and padding around chat messages, especially nested ones. Aim for improved scannability and a cleaner flow. Ensure clear visual distinction between thoughts and tool outputs while maintaining similarity.
    * **B. Button Placement & Consistency:**
        * **Problem:** Copy buttons and Expand/Collapse buttons are added in various contexts.
        * **Proposal:** Perform a visual audit of all interactive elements (copy, expand/collapse, plan actions) within chat messages. Ensure their placement, size, and style are consistent and intuitive across all message types where they appear.
    * **C. Monitor Log Readability:**
        * **Problem:** While color-coding is planned/partially implemented, overall scannability and contrast for different log types in the Monitor Panel could be improved.
        * **Proposal:** Finalize and test CSS rules for Monitor Log color-coding. Ensure sufficient text contrast and clear visual differentiation between log sources (system, LLM, tool, error, etc.).
    * **D. "Agent Thinking Status" Line Review:**
        * **Problem:** The global "agent-thinking-status" line at the bottom of the chat might be redundant or slightly confusing now that more granular sub-statuses and thoughts appear within agent steps.
        * **Proposal:** Review the necessity and behavior of the global status line. Consider if it should only be active when no specific step-level status is available (e.g., initial planning, overall evaluation).
    * **E. "View in Artifacts" Link for Tool Outputs:**
        * **Problem:** Placeholder logic currently, needs full implementation.
        * **Proposal:** Implement the functionality for the "View [artifact_filename] in Artifacts" button within `tool_result_for_chat` messages. Clicking this should smoothly highlight or open the relevant artifact in the Artifact Viewer panel. (Depends on Artifact Viewer refresh bug being addressed).

3.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**
    * **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.`
    * **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly.

4.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):**
    * **Issue:** Backend logs warnings for some DB message types during history load.
    * **Status:** Mostly addressed by better categorization in `task_handlers.py`.
    * **Check:** Confirm current behavior is adequate and all necessary historical message types are handled appropriately for replay to chat or monitor.

Future Brainstorming / More Complex Enhancements:

* **Advanced Chat Information Management (Future):**
    * **Problem:** Very verbose agent interactions (many tool uses, long thoughts for a single step) can still lead to information overload in the chat.
    * **Idea 1 (Filtering/Toggling):** Explore adding UI controls to filter the chat view (e.g., toggle visibility of all "thoughts", all "tool outputs", or all "sub-statuses") to allow users to focus on major steps or final answers.
    * **Idea 2 (Smart Chat Summaries for Tools):** For very verbose tool outputs (e.g., search results), consider if the default in-chat display could be an even more concise summary *generated by an LLM specifically for the chat*, with the "Expand" button revealing the full tool output we currently render.
* **Ongoing Planner & Executor Prompt Engineering:**
    * **Problem:** Ensuring the Planner consistently creates optimal plans (especially the final synthesis step) and that the Executor robustly follows complex instructions requires continuous refinement.
    * **Proposal:** Periodically review agent performance on complex queries involving multiple file generations, multi-part answers, or error recovery. Collect failure cases and use them to iterate on the Planner's system prompt and the Executor's ReAct prompt.

Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually):
 (No changes to this section)
