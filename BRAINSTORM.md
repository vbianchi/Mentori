# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.
Current Version & State (Targeting v2.5.3): [cite: 20]

Recent key advancements and fixes:

  - Core Agent Logic & Tool Integration (Improved):
      - Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic. [cite: 20]
  - Chat UI/UX Refinement (Largely Implemented, Minor Fixes Ongoing):
      - **Visual Design Achieved (based on `simulation_option6.html`):**
          - User messages with right side-lines, unified blue outer left side-lines for system/plan/final messages, no side-lines for major steps, and nested/indented component-specific lines for sub-statuses & thoughts are rendering. [cite: 21]
      - HTML tags (`<strong>`, `<em>`) now render correctly. [cite: 22]
      - **Persistence Implemented:** All new message structures (major steps, sub-statuses, thoughts) are saved to the database and reloaded into chat history. [cite: 22]
      - Plan Proposal UI & Persistence (COMPLETE). [cite: 23]
      - **Token Counter UI & Functionality (FIXED):** Expandable UI for token breakdown by role is in place. [cite: 23] Token counting functionality now works for all individual agent/LLM roles (Intent Classifier, Planner, Controller, Executor, Evaluator) and is accurately displayed in the UI's per-role breakdown. [cite: 28, 24, 25] Persistence for displayed totals per task is working. [cite: 24]
  - Monitor Log Enhancements (Backend Ready, Frontend CSS Next - Lower Priority). [cite: 25]
  - History Loading: Refined in `task_handlers.py` to better categorize internal DB message types, reducing "Unknown history message type" warnings for known system/internal logs. [cite: 26]
Immediate Focus & User Feedback / Known Issues (Post Initial UI Implementation):

1.  **BUG - TOKEN COUNTER - INCOMPLETE PER-ROLE BREAKDOWN (FIXED):**
    -   **Issue:** Tokens for `PLANNER`, `CONTROLLER`, and `EVALUATOR` roles were not appearing in the UI. [cite: 27]
    -   **Status: FIXED.** Token counting functionality now works for all individual agent/LLM roles (Intent Classifier, Planner, Controller, Executor, Evaluator) and is accurately displayed in the UI's per-role breakdown, completing the feature. [cite: 28]

2.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority):**
    -   **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files. [cite: 40] Log shows "File event detected... requesting artifact list update..." [cite: 41]
    -   **Goal:** Ensure artifact viewer reliably shows the latest files post-task completion. [cite: 41]
    -   **Investigation:**
          - Trace the `trigger_artifact_refresh` -> `get_artifacts_for_task` -> `update_artifacts` message flow. [cite: 42]
          - Is the *final* `trigger_artifact_refresh` sent after all plan steps are complete? [cite: 43]
          - Is there any race condition or delay in the frontend processing the `update_artifacts` message? [cite: 44]

3.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**
    -   **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.` [cite: 45]
    -   **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly. [cite: 45]
    -   **Investigation:**
          - Compare the exact string format of a step in a generated `_plan_{id}.md` file (especially after plan execution starts and it's re-saved) with the regex in `_update_plan_file_step_status` in `agent_flow_handlers.py`. [cite: 46] Look for subtle differences in whitespace, numbering, or Markdown. [cite: 47]

4.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):**
    -   **Issue:** Backend logs warnings for some DB message types during history load. [cite: 47]
    -   **Status:** The history loading in `task_handlers.py` was updated (Canvas `ResearchAgent_TokenCounter_TaskHandlerHistoryFix_Canvas1`) to better categorize internal DB message types. [cite: 48] Many are now explicitly routed to the monitor log with a `[History]` prefix. [cite: 49]
    -   **Check:** Confirm this refined behavior is adequate and that no critical "unknown" types remain for chat replay. [cite: 50] Minor types like `tool_input_write_file` or `tool_output_write_file` might still appear as "Unknown" if not added to `INTERNAL_DB_MESSAGE_TYPES_FOR_MONITOR_REPLAY_ONLY` set in `task_handlers.py`; [cite: 51] decide if these also should be routed only to monitor log. [cite: 52]
Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually):

  - User Messages: Right-aligned bubble, user accent color, right-hand side-line. [cite: 53]
  - System Status / Plan Proposal / Final Agent Message: Left-aligned, unified blue side-line. [cite: 54]
  - Agent Major Step Announcement: Left-aligned, NO side-line, bold title. [cite: 55]
  - Nested Sub-Content (Sub-Statuses & Agent Thoughts): Indented, each with its own component-specific colored left side-line. [cite: 56] Thoughts in a dark box. [cite: 57]
  - Persistent Bottom "Thinking" Line: Last scrollable item, italic, dynamic component-specific colored left side-line. [cite: 57]
  - HTML Tag Rendering: `<strong>`, `<em>` now render correctly. [cite: 58]

