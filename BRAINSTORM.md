# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.

Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (Improved):
    -   Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic.
-   Chat UI/UX Refinement (Largely Implemented, Minor Fixes Ongoing):
    -   **Visual Design Achieved (based on `simulation_option6.html`):**
        -   User messages with right side-lines, unified blue outer left side-lines for system/plan/final messages, no side-lines for major steps, and nested/indented component-specific lines for sub-statuses & thoughts are rendering.
    -   HTML tags (`<strong>`, `<em>`) now render correctly.
    -   **Persistence Implemented:** All new message structures (major steps, sub-statuses, thoughts) are saved to the database and reloaded into chat history.
    -   Plan Proposal UI & Persistence (COMPLETE).
    -   **Token Counter UI & Functionality (FIXED):** Expandable UI for token breakdown by role is in place. Token counting functionality now works for all individual agent/LLM roles (Intent Classifier, Planner, Controller, Executor, Evaluator) and is accurately displayed in the UI's per-role breakdown. Persistence for displayed totals per task is working.
    -   **File Upload Functionality (FIXED):** File uploads to the task workspace are now functional (HTTP 501 error resolved).
-   Monitor Log Enhancements (Backend Ready, Frontend CSS Next - Lower Priority).
-   History Loading: Refined in `task_handlers.py` to better categorize internal DB message types, reducing "Unknown history message type" warnings for known system/internal logs.

Immediate Focus & User Feedback / Known Issues (Post Initial UI Implementation):

1.  **BUG - TOKEN COUNTER - INCOMPLETE PER-ROLE BREAKDOWN (FIXED):**
    -   **Issue:** Tokens for `PLANNER`, `CONTROLLER`, and `EVALUATOR` roles were not appearing in the UI.
    -   **Status: FIXED.** Token counting functionality now works for all individual agent/LLM roles.
2.  **BUG - FILE UPLOAD (FIXED):**
    -   **Issue:** File upload functionality was broken (HTTP 501 error).
    -   **Status: FIXED.**
3.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Paused):**
    -   **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files. Log shows "File event detected... requesting artifact list update..." The UI can also get confused with "Loading (previous fetch in progress)..." messages.
    -   **Goal:** Ensure artifact viewer reliably shows the latest files post-task completion and ideally after each relevant plan step.
    -   **Status:** Debugging paused. Backend triggers appear to be sending refresh messages, but frontend processing during agent busy state is likely the cause of delayed/confused updates.
4.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**
    -   **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.`
    -   **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly.
    -   **Investigation:**
        -   Compare the exact string format of a step in a generated `_plan_{id}.md` file (especially after plan execution starts and it's re-saved) with the regex in `_update_plan_file_step_status` in `agent_flow_handlers.py`. Look for subtle differences in whitespace, numbering, or Markdown.
5.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):**
    -   **Issue:** Backend logs warnings for some DB message types during history load.
    -   **Status:** The history loading in `task_handlers.py` was updated to better categorize internal DB message types. Many are now explicitly routed to the monitor log with a `[History]` prefix.
    -   **Check:** Confirm this refined behavior is adequate and that no critical "unknown" types remain for chat replay.

Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually):

-   User Messages: Right-aligned bubble, user accent color, right-hand side-line.
-   System Status / Plan Proposal / Final Agent Message: Left-aligned, unified blue side-line.
-   Agent Major Step Announcement: Left-aligned, NO side-line, bold title.
-   Nested Sub-Content (Sub-Statuses & Agent Thoughts): Indented, each with its own component-specific colored left side-line. Thoughts in a dark box.
-   Persistent Bottom "Thinking" Line: Last scrollable item, italic, dynamic component-specific colored left side-line.
-   HTML Tag Rendering: `<strong>`, `<em>` now render correctly.
