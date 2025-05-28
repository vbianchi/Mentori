# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.
Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

  - Core Agent Logic & Tool Integration (Improved):
      - Plan execution now attempts actual tool use and LLM generation for steps, replacing previous placeholder logic.
  - Chat UI/UX Refinement (Partially Implemented, Ongoing Fixes):
      - **Visual Design Achieved (based on `simulation_option6.html`):**
          - User messages with right side-lines, unified blue outer left side-lines for system/plan/final messages, no side-lines for major steps, and nested/indented component-specific lines for sub-statuses & thoughts are rendering.
      - HTML tags (`<strong>`, `<em>`) now render correctly.
      - **Persistence Implemented:** All new message structures (major steps, sub-statuses, thoughts) are saved to the database and reloaded into chat history.
      - Plan Proposal UI & Persistence (COMPLETE).
      - **Token Counter UI (Partially Implemented):** Expandable UI for token breakdown by role is in place. Persistence for displayed totals per task is working. `EXECUTOR` and `EXECUTOR_DirectQA` roles report tokens. `INTENT_CLASSIFIER` is now also reporting tokens after backend fixes.
  - Monitor Log Enhancements (Backend Ready, Frontend CSS Next - Lower Priority).
  - History Loading: Refined in `task_handlers.py` to better categorize internal DB message types, reducing "Unknown history message type" warnings for known system/internal logs.

Immediate Focus & User Feedback / Known Issues (Post Initial UI Implementation):

1.  **BUG - TOKEN COUNTER - INCOMPLETE PER-ROLE BREAKDOWN (Medium Priority):**

      - **Issue:** While the UI for token breakdown is implemented and `EXECUTOR`, `EXECUTOR_DirectQA`, and `INTENT_CLASSIFIER` roles are now reporting token usage (as per latest tests and logs showing `INTENT_CLASSIFIER` callbacks firing and sending token data), tokens for `PLANNER`, `CONTROLLER`, and `EVALUATOR` roles are still not appearing in the UI.
      - **Goal:** Ensure token counting functionality works for all remaining individual agent/LLM roles (Planner, Controller, Evaluator) and is accurately displayed in the UI's per-role breakdown, completing the feature.
      - **Investigation & Next Steps (Backend):**
          - Confirm that the `WebSocketCallbackHandler` instance is correctly passed to and used by the LLM instances within `planner.py`, `controller.py`, and `evaluator.py`. This involves ensuring:
              - Their main functions (e.g., `generate_plan`, `validate_and_prepare_step_action`, etc.) accept the `callback_handler` passed from `agent_flow_handlers.py`.
              - `get_llm` is called with this `callback_handler` (via its `callbacks` parameter) for LLM instantiation within these components.
              - The `chain.ainvoke` calls within these components use a `RunnableConfig` that includes this `callback_handler` list and the correct `component_name` metadata. (This acts as a fallback or reinforcement if the LLM-level callback doesn't cover everything in the chain).
          - Verify with `CRITICAL_DEBUG` logs (similar to how we confirmed for `INTENT_CLASSIFIER`) that `on_llm_start` and `on_llm_end` methods in `callbacks.py` are triggered for `PLANNER`, `CONTROLLER`, and `EVALUATOR_*` roles.
          - If callbacks are triggered, inspect the `LLMResult` object (specifically `response.llm_output` and `response.generations`) passed to `on_llm_end` for these roles to confirm token usage data is present and in a parsable format. The current parsing in `callbacks.py` (checking `llm_output.token_usage`, `llm_output.usage_metadata`, and `generations[0].message.usage_metadata`) should be robust if the data is in one of these standard locations.
          - Ensure `llm_token_usage` messages with the correct `role_hint` are being sent from `callbacks.py` for these remaining roles.
      - **Investigation (Frontend - If backend sends data but UI doesn't update for these roles):**
          - Verify `StateManager.updateCurrentTaskTotalTokens` correctly processes incoming `llm_token_usage` messages for these new roles.
          - Verify `token_usage_ui.js` correctly maps these `role_hint`s to display names and renders their token counts.

2.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority):**

      - **Issue:** Artifact viewer doesn't consistently auto-update immediately after a task finishes writing files. Log shows "File event detected... requesting artifact list update..."
      - **Goal:** Ensure artifact viewer reliably shows the latest files post-task completion.
      - **Investigation:**
          - Trace the `trigger_artifact_refresh` -\> `get_artifacts_for_task` -\> `update_artifacts` message flow.
          - Is the *final* `trigger_artifact_refresh` sent after all plan steps are complete?
          - Is there any race condition or delay in the frontend processing the `update_artifacts` message?

3.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):**

      - **Issue:** Backend logs `Step X pattern not found in plan file ... for status update.`
      - **Goal:** Ensure `_plan_{id}.md` artifact checkboxes are updated correctly.
      - **Investigation:**
          - Compare the exact string format of a step in a generated `_plan_{id}.md` file (especially after plan execution starts and it's re-saved) with the regex in `_update_plan_file_step_status` in `agent_flow_handlers.py`. Look for subtle differences in whitespace, numbering, or Markdown.

4.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):**

      - **Issue:** Backend logs warnings for some DB message types during history load.
      - **Status:** The history loading in `task_handlers.py` was updated (Canvas `ResearchAgent_TokenCounter_TaskHandlerHistoryFix_Canvas1`) to better categorize internal DB message types. Many are now explicitly routed to the monitor log with a `[History]` prefix.
      - **Check:** Confirm this refined behavior is adequate and that no critical "unknown" types remain for chat replay. Minor types like `tool_input_write_file` or `tool_output_write_file` might still appear as "Unknown" if not added to `INTERNAL_DB_MESSAGE_TYPES_FOR_MONITOR_REPLAY_ONLY` set in `task_handlers.py`; decide if these also should be routed only to monitor log.

Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually):

  - User Messages: Right-aligned bubble, user accent color, right-hand side-line.
  - System Status / Plan Proposal / Final Agent Message: Left-aligned, unified blue side-line.
  - Agent Major Step Announcement: Left-aligned, NO side-line, bold title.
  - Nested Sub-Content (Sub-Statuses & Agent Thoughts): Indented, each with its own component-specific colored left side-line. Thoughts in a dark box.
  - Persistent Bottom "Thinking" Line: Last scrollable item, italic, dynamic component-specific colored left side-line.
  - HTML Tag Rendering: `<strong>`, `<em>` now render correctly.
