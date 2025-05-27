# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.

Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (RESOLVED):
    -   `deep_research_synthesizer` & `write_file` Flow: Fully resolved.
    -   Backend `IndentationError` issues: Resolved.
-   Chat UI/UX Refinement (Design Solidified based on `simulation_option6.html`, Backend & Frontend Implementation Next):
    -   **New Vision (Target: `simulation_option6.html`):**
        -   **User Messages:** Right-aligned bubble with a right-hand side-line matching the user's accent color.
        -   **Unified Blue Outer Side-Lines:** General system status messages (e.g., "Loading history...", "Plan confirmed..."), plan proposal blocks, and the final agent conclusive message will feature a consistent blue left-hand side-line.
        -   **Major Step Announcements:** Messages like "Step 1/N: Doing X" will be left-aligned, bold, and will _not_ have a side-line or background bubble.
        -   **Nested Sub-Statuses:** Significant agent sub-statuses (e.g., "Controller: Validating...", "Executor: Using tool...") will appear as new, sequential messages _indented under their parent major step announcement_. They will be italicized, have no background bubble, and feature a component-specific colored left-hand side-line (e.g., Controller orange, Tool teal).
        -   **Nested Agent Thoughts/Verbose Outputs:** More detailed "thoughts" or preliminary outputs from agent components will also be displayed indented under the relevant major step. They will have normal font, no bubble, a component-specific colored left-hand side-line, a label (e.g., "Controller thought:"), and their content presented in a distinct dark box (similar to a `<pre>` block, especially for code-like content).
        -   **Persistent Bottom "Thinking" Line:** A single line at the very bottom of the _scrollable chat area_ for low-level, rapidly updating "Thinking (LLM)..." statuses. This line will update in place and feature a dynamic, component-specific colored left-hand side-line.
        -   **Final Agent Message:** Will appear in a distinct, styled bubble with the unified blue left-hand side-line.
    -   **Backend Message Structure & Persistence Strategy (Enhancements Required):**
        -   `callbacks.py` & `agent_flow_handlers.py`: Will send structured `agent_thinking_update` messages with `component_hint` and a new `sub_type` field (e.g., `'sub_status'`, `'thought'`) to differentiate rendering on the frontend. `agent_major_step_announcement` messages are already defined.
        -   **Persistence:** All new message structures (major steps, sub-statuses, thoughts) will be saved to the database (`db_utils.py`, `server.py`) with distinct `message_type` identifiers. `task_handlers.py` will be updated to load and send these historical messages to the frontend, ensuring they are correctly dispatched and rendered with their specific styling and nesting.
    -   **Status Message Persistence (Backend Partially Complete):** Critical `status_message` types are saved. This will be extended for the new message structures.
-   Plan Proposal UI & Persistence (COMPLETE): Remains functional, will adopt the unified blue outer side-line.
-   Monitor Log Enhancements (Backend Ready, Frontend CSS Next):
    -   Backend provides `log_source`. CSS styling for colors is pending.

Immediate Focus & User Feedback / Known Issues:

1.  **IMPLEMENT (High Priority): New Chat UI Rendering & Persistence (Frontend & Backend Task):**
    -   **Issue:** Current chat UI does not yet reflect the `simulation_option6.html` design. Full persistence for all message types is not yet implemented.
    -   **Goal:** Update frontend (`script.js`, `chat_ui.js`, `style.css`) and backend (`db_utils.py`, `server.py`, `task_handlers.py`, `agent_flow_handlers.py`, `callbacks.py`) to implement the vision.
        -   **`style.css`:**
            -   Add styles for user message right side-line.
            -   Implement unified blue outer left side-line for system status, plan proposals, final agent messages.
            -   Remove side-lines from major step announcement elements.
            -   Add styles for indented, component-colored side-lines for sub-statuses and agent thoughts.
            -   Style agent thought content (label + dark box).
            -   Ensure persistent bottom thinking line is styled correctly and placed as the last scrollable item.
            -   Define all component-specific side-line color classes.
        -   **`chat_ui.js`:**
            -   `addChatMessageToUI`: Modify to handle wrapper divs for messages needing the unified blue outer line. Correctly render user messages with the right side-line. Delegate rendering of sub-statuses and thoughts.
            -   `displayMajorStepAnnouncementUI`: Render major steps without side-lines. Create a container within for nested sub-content. Set `currentMajorStepDiv`.
            -   `showAgentThinkingStatusInUI`:
                -   If `currentMajorStepDiv` is set and `statusUpdateObject.sub_type` is 'sub\_status' or 'thought', append the new message (sub-status or thought with its specific styling and side-line) to the sub-content container of `currentMajorStepDiv`.
                -   Otherwise, update the persistent bottom `#agent-thinking-status` line with its dynamic component side-line.
                -   Reset `currentMajorStepDiv` when a final state (Idle, Error, Cancelled) is reached or a new final agent message is displayed.
            -   `formatMessageContentInternal`: Ensure robust Markdown to HTML conversion, especially for code blocks within thoughts.
            -   Ensure all historical messages (including new types) are rendered correctly when loaded.
        -   **`script.js`:**
            -   `dispatchWsMessage`: Correctly route `agent_major_step_announcement` to `displayMajorStepAnnouncementUI`. Route `agent_thinking_update` (with `sub_type`) to `showAgentThinkingStatusInUI`. Ensure final `agent_message` updates the bottom thinking line to "Idle". Handle new historical message types.
        -   **Backend:** Implement saving and loading for `db_major_step_announcement`, `db_agent_sub_status`, `db_agent_thought` message types. Ensure WebSocket messages for historical items are structured for correct frontend dispatch.
    -   **Persistence Check:** Verify that all styled messages (steps, sub-statuses, thoughts, etc.) are persistent after page refresh.
2.  **BUG FIX (Medium Priority): Chat Input Unresponsive:**
    -   **Issue:** After a task completes, chat input sometimes remains disabled.
    -   **Goal:** Ensure `StateManager.isAgentRunning` is correctly reset and UI re-enables input, tied to the "Idle" state of the bottom thinking line.
3.  **DEBUG (Medium Priority): Monitor Log Color-Coding:**
    -   **Issue:** Visual differentiation by `log_source` in the Monitor Log is not yet appearing correctly.
    -   **Goal:** Implement effective color-coding in `style.css`.
4.  **Fix (Low Priority): `<strong>` Tag Rendering in Chat:**
    -   **Issue:** User noted some HTML tags (like `<strong>`) not rendering correctly.
    -   **Goal:** Ensure `innerHTML` is consistently used for content processed by `formatMessageContentInternal`.

Chat UI Simulation Details (Based on `simulation_option6.html`):

-   **User Messages:** Right-aligned bubble, user accent color, right-hand side-line (darker user accent).
-   **System Status / Plan Proposal / Final Agent Message:** Left-aligned, unified blue side-line. Bubbles for proposal and final agent message.
-   **Agent Major Step Announcement:** Left-aligned, NO side-line, bold title (e.g., "Step 1/5: Action...").
-   **Nested Sub-Content (under Major Step):**
    -   **Sub-Statuses:** Indented, italic, component-specific colored left side-line (e.g., "Controller: Validating...").
    -   **Agent Thoughts:** Indented, normal font, component-specific colored left side-line, label ("Controller thought:"), content in dark box.
-   **Persistent Bottom "Thinking" Line:** Last scrollable item, italic, dynamic component-specific colored left side-line (e.g., "Thinking (LLM Core)...", "Idle.").
