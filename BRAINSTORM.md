BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)
=====================================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.
**Current Version & State (Targeting v2.5.3):** [cite: 1542]

Recent key advancements and fixes:

* **Core Agent Logic & Tool Integration (Significant Improvements):**
    * **Controller `KeyError` Resolved:** Fixed critical bug in `controller.py` related to prompt formatting with unescaped curly braces.
    * **`deep_research_synthesizer` Input Handling Resolved:**
        * Controller now correctly formulates the required JSON string input (e.g., `{"query": "..."}`) for the `deep_research_synthesizer` tool. [cite: 1556, 1557]
        * The ReAct agent (`agent.py`) prompt has been updated to ensure it passes the direct output of tools like `deep_research_synthesizer` as its `Final Answer` for a step.
        * The Step Evaluator (`evaluator.py`) prompt is now stricter in verifying actual content generation against expected outcomes.
        * Plans involving research with `deep_research_synthesizer` and subsequent file saving with `write_file` are now executing successfully end-to-end.
* **Plan Proposal UI & Persistence (COMPLETE):**
    * Backend correctly sends `propose_plan_for_confirmation` message. [cite: 1542]
    * Plan proposal UI appears in chat with inline "View Details". [cite: 1543]
    * "Cancel Plan Proposal" functionality implemented. [cite: 1544]
    * Confirmed plans transform to a static message in chat. [cite: 1544]
    * Confirmed plans (`confirmed_plan_log`) load correctly from chat history. [cite: 1545]
* **Chat UI & Agent Feedback Refinements (In Progress):**
    * **Direct QA Output:** Final answers for Direct QA intents are displayed in the main chat. [cite: 1546]
    * **Agent Thinking Updates:** Backend (`callbacks.py`) sends structured `agent_thinking_update` messages for concise status. [cite: 1547] Frontend (`script.js`, `chat_ui.js`) handles these. [cite: 1548]
    * **Final Plan Output in Chat (Partially Improved):** The final `agent_message` from a successful plan now includes the output of the last plan step. Further refinement is needed to ensure the *most relevant* artifact (e.g., the research report itself) is prioritized for chat display if it's not the last step's direct output.
    * **Reduced Chat Clutter:** `callbacks.py` revised to route verbose intermediate agent thoughts/tool I/O to Monitor Log. [cite: 1548] `on_agent_finish` for individual ReAct steps no longer sends `agent_message` to chat. [cite: 1549]
* **Monitor Log Enhancements (Initial):**
    * Backend (`callbacks.py`) includes `log_source` in `monitor_log` payloads. [cite: 1550]
    * Frontend (`monitor_ui.js`) updated to add CSS classes based on `log_source` (styling pending debug). [cite: 1551]
* **Tool Enhancements (Ongoing):**
    * `deep_research_synthesizer`: Input schema confirmed as `query`. Tool successfully generates reports based on Controller's JSON input.
    * `write_file`: Successfully saves content passed from previous steps (e.g., `deep_research_synthesizer` report).

**Immediate Focus & User Feedback / Known Issues:**

1.  **BUG FIX (High Priority): Chat Input Unresponsive:**
    * **Issue:** After a task completes (Direct QA or Plan), the chat input sometimes doesn't re-enable. [cite: 1559]
    * **Goal:** Ensure agent status flags (`isAgentRunning`) are correctly reset and a final "Idle" `agent_thinking_update` is consistently sent/handled. [cite: 1560]

2.  **UX Refinement (High Priority): Final Message Delivery & Chat Flow:**
    * **User Feedback:** Aim for a cleaner chat interface, similar to `manus.ai`. [cite: 1561]
    * **Current Status:** Final plan message shows last step's output. `agent_thinking_update` provides concise statuses.
    * **Goal:**
        * Ensure the *most relevant primary output* of a plan (e.g., the content of a generated report, not just a "file saved" message) is clearly presented or linked in the chat.
        * Further refine the chat flow for plan execution to provide clear step-by-step progress without clutter (see "Brainstorming: Enhanced Chat UI" below).
        * Refine how recoverable errors during step execution are communicated in chat (avoiding alarming red messages if retries are in progress).

3.  **DEBUG (Medium Priority): Monitor Log Color-Coding:**
    * **Issue:** Visual differentiation by `log_source` is not yet appearing. [cite: 1565]
    * **Goal:** Implement effective color-coding based on `log_source`. [cite: 1566]
    * **Next Steps:** Create/Debug CSS rules in `style.css`. [cite: 1567] Ensure all backend calls to `add_monitor_log_func` provide consistent and useful `log_source` values. [cite: 1568]

4.  **Brainstorming: Enhanced Chat UI & Message Flow (Inspired by `manus.ai`):**
    * **Categorize Monitor Log Messages**: Identify distinct types of system/agent messages (e.g., user interactions, core agent flow, planning, controller, executor, tool I/O, evaluations, system events).
    * **Define Chat-Worthy Messages**: Based on the categories, decide which messages should appear in the main chat UI for optimal user experience.
        * User input.
        * Agent's final answers/results.
        * Interactive Plan UI.
        * **New**: Major Plan Step Announcements (e.g., "Starting Step 1: Researching topic X...").
        * **Refined**: Concise sub-status updates (`agent_thinking_update`) potentially displayed contextually under the major step announcement.
        * Critical (terminal) failure notifications.
    * **Filter Out Verbosity**: Keep detailed traces, LLM core logs, granular tool I/O, internal errors, etc., primarily in the Monitor Log.

**Current Workflow Example (Heatmap Generation - Target State):**
(This example largely remains a good target, with emphasis on the *type* of messages in chat vs. monitor)

1.  User: "Create a heatmap..."
2.  `agent_thinking_update` (Chat status line): "Classifying intent..."
3.  Monitor: `[SYS_INTENT_CLASSIFIED] PLAN` (or similar `log_source`)
4.  `agent_thinking_update` (Chat status line): "Generating plan..."
5.  Monitor: `[SYS_PLAN_GENERATED] Plan details...` (or `PLANNER_OUTPUT`)
6.  Chat: Interactive Plan Proposal UI. [cite: 1571]
7.  User Confirms.
8.  Chat: Plan UI transforms to "Confirmed Plan... Execution Started..."
9.  Monitor: `[SYS_PLAN_CONFIRMED] ...`
    * **Step 1: Install Packages**
        * Chat: **(New Style Idea)** "[Agent] Step 1/N: Installing required packages (e.g., seaborn, pandas)."
        * `agent_thinking_update` (Chat status line, or sub-status under Step 1 message): "Using python_package_installer..."
        * Monitor: `[CONTROLLER_START] ...`, `[CONTROLLER_OUTPUT] Tool='python_package_installer' ...`, `[TOOL_START_PYTHON_PACKAGE_INSTALLER] ...`, `[TOOL_STDOUT_PYTHON_PACKAGE_INSTALLER] ...pip logs...`, `[TOOL_OUTPUT_PYTHON_PACKAGE_INSTALLER] ...`, `[STEP_EVAL_START] ...`, `[STEP_EVAL_OUTPUT] ...`
        * `agent_thinking_update` (Chat status line/sub-status): "Packages installed." [cite: 1572]
    * **(Similar flow for other steps: Write Script, Execute Script)**
        * Chat: Major step announcements.
        * `agent_thinking_update`: Concise sub-statuses for each phase. [cite: 1573]
        * All detailed logs go to Monitor. [cite: 1574]
10. `agent_thinking_update` (Chat status line): "Finalizing result..."
11. Monitor: `[SYS_EVALUATOR_START_OVERALL] Overall Plan Eval...`, `[SYS_EVALUATOR_OUTPUT_OVERALL] ...Assessment: Heatmap generated successfully...`
12. Chat: `[Agent]` "The heatmap was successfully generated and saved as `heatmap.png` in your workspace. You can view it in the Artifacts panel." (This is the final, user-facing message, potentially with a direct link or preview if possible in future). [cite: 1574]
13. `agent_thinking_update` (Chat status line): "Idle. Ready for next query." [cite: 1575]

This refined workflow aims for the `manus.ai` style of keeping the chat clean and focused on the primary dialogue and outcomes. [cite: 1576]
