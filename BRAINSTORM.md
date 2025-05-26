BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)
=====================================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.

**Current Version & State (Targeting v2.5.3):**

Recent key advancements and fixes:

-   **Plan Proposal UI & Persistence (COMPLETE):**

    -   Backend correctly sends `propose_plan_for_confirmation` message.

    -   Plan proposal UI appears in chat with inline "View Details" (toggles structured plan visibility).

    -   "Cancel Plan Proposal" functionality implemented.

    -   Confirmed plans transform to a static message in chat.

    -   Confirmed plans (`confirmed_plan_log`) now load correctly from chat history as static displays.

-   **Chat UI & Agent Feedback Refinements (In Progress):**

    -   **Direct QA Output:** Final answers for Direct QA intents (e.g., poem generation) are now displayed in the main chat.

    -   **Agent Thinking Updates:** Backend (`callbacks.py`) sends structured `agent_thinking_update` messages (with `status_key`, `message`) for concise status feedback in chat. Frontend (`script.js`, `chat_ui.js`) updated to handle these.

    -   **Reduced Chat Clutter:**  `callbacks.py` revised to route more verbose intermediate agent thoughts, tool I/O to Monitor Log. `on_agent_finish` for individual ReAct steps no longer sends `agent_message` to chat.

-   **Monitor Log Enhancements (Initial):**

    -   Backend (`callbacks.py`) now includes `log_source` in `monitor_log` message payloads to identify the component (Planner, Controller, Tool, etc.).

    -   Frontend (`monitor_ui.js`) updated to add CSS classes based on `log_source` (styling itself is pending debug).

-   **Agent Logic & Stability (Ongoing):**

    -   Controller's JSON parsing from LLM output improved.

    -   ReAct agent prompt in `agent.py` refined.

-   **Tool Enhancements (Ongoing):**

    -   `python_package_installer` handles multiple packages.

    -   `workspace_shell` provides more reliable STDOUT.

    -   `Python_REPL` description clarified.

    -   `deep_research_synthesizer`: Input schema changed from `topic` to `query`. Now saves its report to a file. (Currently debugging Controller input to this tool).

**Immediate Focus & User Feedback / Known Issues:**

1.  **BUG FIXES (Highest Priority):**

    -   **`deep_research_synthesizer` Input Handling:**

        -   **Issue:** Controller's first attempt to call `deep_research_synthesizer` still sends a plain string instead of the required JSON string, causing a `JSONDecodeError`. The subsequent retry (after Step Evaluator guidance) uses JSON but previously had a `query` vs. `topic` field mismatch (the `topic` vs `query` in the tool schema itself is now fixed to `query`).

        -   **Goal:** Ensure Controller's prompt (`controller.py`) robustly guides it to produce the correct JSON string `{"query": "..."}` for this tool from the first attempt.

    -   **Chat Input Unresponsive:**

        -   **Issue:** After a task completes (Direct QA success, or Plan completion/error), the chat input sometimes doesn't re-enable, requiring a task switch.

        -   **Goal:** Ensure agent status flags (`isAgentRunning`) are correctly reset and a final "Idle" `agent_thinking_update` is consistently sent and handled to re-enable input.

2.  **Refine Chat Clutter & Final Message Delivery (High Priority - Ongoing):**

    -   **User Feedback:** Aim for a cleaner chat interface, similar to `manus.ai`.

    -   **Status:** Significant progress by moving intermediate details from `callbacks.py` to Monitor Log and using `agent_thinking_update` for concise statuses.

    -   **Remaining Goal:** Ensure the *final user-facing message* for both successful Direct QA and successful Plan Executions is clearly and effectively presented in the chat. For plans, this might be the `OverallPlanEvaluator`'s assessment or a summary of key outputs.

3.  **Monitor Log Color-Coding (Medium Priority - Debugging):**

    -   **Issue:** Visual differentiation by `log_source` is not yet appearing in the Monitor Log.

    -   **Goal:** Implement effective color-coding (or other visual cues) based on the `log_source` to improve readability.

    -   **Next Steps:** Debug CSS rules in `style.css`. Ensure all backend calls to `add_monitor_log_func` (especially from `server.py` and `agent_flow_handlers.py`) are updated to pass a `log_source` and send the structured object payload.

4.  **`deep_research_synthesizer` Output Handling (Feature Verification):**

    -   **Status:** The tool now saves its output to a `.md` file in the task workspace and prepends a message about the save to its string output.

    -   **Goal:** Verify the file is created, artifact refresh shows it, and consider how to best present this (e.g., link in final agent message) to the user.

**Current Workflow Example (Heatmap Generation - Target State):**

1.  User: "Create a heatmap..."

2.  `agent_thinking_update`: "Classifying intent..."

3.  Monitor: `[SYS_INTENT_CLASSIFIED] PLAN`

4.  `agent_thinking_update`: "Generating plan..."

5.  Monitor: `[SYS_PLAN_GENERATED] Plan details...`

6.  Chat: Interactive Plan Proposal UI.

7.  User Confirms.

8.  Chat: Plan UI transforms to "Confirmed Plan... Execution Started..."

9.  Monitor: `[SYS_PLAN_CONFIRMED] ...`

    -   **Step 1: Install Packages**

        -   `agent_thinking_update`: "Step 1/N: Installing packages..."

        -   Monitor: `[SYS_CONTROLLER_START] ...`, `[SYS_CONTROLLER_OUTPUT] Tool='python_package_installer' ...`, `[TOOL_START...] ...`, `[TOOL_STDOUT] ...pip logs...`, `[TOOL_OUTPUT...] ...`, `[SYS_STEP_EVAL_START] ...`, `[SYS_STEP_EVAL_OUTPUT] ...`

        -   `agent_thinking_update`: "Packages installed." (or similar concise update from `on_tool_end` or `on_step_evaluator_end`)

    -   **(Similar flow for other steps: Write Script, Execute Script)**

        -   Concise `agent_thinking_update` messages for each phase (e.g., "Step 2/N: Preparing script...", "Script saved.", "Step 3/N: Generating heatmap...", "Heatmap generated.").

        -   All detailed logs go to Monitor.

10. `agent_thinking_update`: "Finalizing result..."

11. Monitor: `[SYS_EVALUATOR_START] Overall Plan Eval...`, `[SYS_EVALUATOR_OUTPUT] ...Assessment: Heatmap generated successfully...`

12. Chat: `[Agent]` "The heatmap was successfully generated and saved as `heatmap.png` in your workspace." (This is the final, user-facing message).

13. `agent_thinking_update`: "Idle. Ready for next query."

This refined workflow aims for the `manus.ai` style of keeping the chat clean and focused on the primary dialogue and outcomes.