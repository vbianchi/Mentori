# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.

Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (Improved):
    -   Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic.
    -   `UnboundLocalError` in `callbacks.py` (token parsing): **FIXED.**
-   Chat UI/UX Refinement (Partially Implemented, Ongoing Fixes):
    -   **Visual Design Achieved (based on `simulation_option6.html`):**
        -   User messages with right side-lines, unified blue outer left side-lines for system/plan/final messages, no side-lines for major steps, and nested/indented component-specific lines for sub-statuses & thoughts are rendering.
        -   HTML tags (`<strong>`, `<em>`) now render correctly.
    -   **Persistence Implemented:** All new message structures (major steps, sub-statuses, thoughts) are saved to the database and reloaded into chat history.
-   Plan Proposal UI & Persistence (COMPLETE).
-   Monitor Log Enhancements (Backend Ready, Frontend CSS Next - Lower Priority).

Immediate Focus & User Feedback / Known Issues (Post Initial UI Implementation):

1.  **CRITICAL BUG - NEW TASK CONNECTION (High Priority):**
    -   **Issue:** When a new task is created in the UI, it doesn't immediately establish full, functional context with the backend. The UI for the new task might appear, but interactions (like sending the first message) might fail or require a page refresh to work correctly. After refresh, it connects and shows "Idle."
    -   **Goal:** Ensure seamless backend context initialization for newly created tasks without requiring user intervention or refreshes.
    -   **Investigation:**
        -   Review `handleNewTaskCreation` and `handleTaskSelection` in `script.js`.
        -   Review `process_new_task` (if it exists, or the flow after new task selection) and `process_context_switch` in `task_handlers.py` on the backend.
        -   Check WebSocket message flow upon new task creation and subsequent selection. Is `context_switch` being sent correctly and processed fully for a brand new task ID before the user's first message attempt?
2.  **CRITICAL BUG - FILE UPLOAD (High Priority):**
    -   **Issue:** File upload results in an HTTP 501 "Not Implemented" error. Files are not copied.
    -   **Goal:** Restore file upload functionality.
    -   **Investigation:**
        -   The 501 error suggests the backend server (aiohttp file server part in `server.py`) is either not correctly routing the `/upload/{task_id}` POST request to `handle_file_upload`, or the `handle_file_upload` function itself is not correctly set up to handle POST requests in the aiohttp router, or there's an issue with how `aiohttp_cors` is configured for this route.
        -   Verify `app.router.add_resource('/upload/{task_id}').add_route('POST', handle_file_upload)` in `server.py`.
        -   Check CORS setup for this POST route.
        -   Ensure `handle_file_upload` is correctly processing multipart form data.
3.  **BUG - TOKEN COUNTER NOT UPDATING (Medium Priority):**
    -   **Issue:** The UI token counter (last call, task total) is no longer updating.
    -   **Goal:** Restore token counting functionality.
    -   **Investigation:**
        -   Verify `llm_token_usage` messages are being sent correctly from `callbacks.py` (after the `UnboundLocalError` fix).
        -   Check `dispatchWsMessage` in `script.js` to ensure it calls `handleTokenUsageUpdate`.
        -   Debug `handleTokenUsageUpdate` in `script.js` and `StateManager.updateCurrentTaskTotalTokens` to see where the update is failing.
4.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority):**
    -   **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files. Log shows "File event detected... requesting artifact list update..."
    -   **Goal:** Ensure artifact viewer reliably shows the latest files post-task completion.
    -   **Investigation:**
        -   Trace the `trigger_artifact_refresh` -> `get_artifacts_for_task` -> `update_artifacts` message flow.
        -   Is the _final_ `trigger_artifact_refresh` sent after all plan steps are complete?
        -   Is there any race condition or delay in the frontend processing the `update_artifacts` message?
5.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**
    -   **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.`
    -   **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly.
    -   **Investigation:**
        -   Compare the exact string format of a step in a generated `_plan_{id}.md` file (especially after plan execution starts and it's re-saved) with the regex in `_update_plan_file_step_status` in `agent_flow_handlers.py`. Look for subtle differences in whitespace, numbering, or Markdown.
6.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority):**
    -   **Issue:** Backend logs `Unknown history message type 'SYSTEM_INTENT_CLASSIFIED'` etc. when loading history. These are currently routed to the monitor log.
    -   **Decision:** Confirm that routing these specific internal system event markers to the monitor log (and not the main chat) is the desired long-term behavior for a clean chat UI. (Current assumption: Yes, this is fine).

Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually):

-   User Messages: Right-aligned bubble, user accent color, right-hand side-line.
-   System Status / Plan Proposal / Final Agent Message: Left-aligned, unified blue side-line.
-   Agent Major Step Announcement: Left-aligned, NO side-line, bold title.
-   Nested Sub-Content (Sub-Statuses & Agent Thoughts): Indented, each with its own component-specific colored left side-line. Thoughts in a dark box.
-   Persistent Bottom "Thinking" Line: Last scrollable item, italic, dynamic component-specific colored left side-line.
-   HTML Tag Rendering: `<strong>`, `<em>` now render correctly.
