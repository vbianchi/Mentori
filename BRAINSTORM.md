BRAINSTORM.md - ResearchAgent Project (v2.5.1)
==============================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project. For longer-term plans and phased development, please see `ROADMAP.md`.

**Current Version & State (v2.5.1 - Key Fixes & Refactoring Progress):** The ResearchAgent is at v2.5.1. Recent key advancements:

-   **Agent Logic:** The "poem discrepancy" is **fixed**; the Controller now correctly uses the output from a previous generative step as input for subsequent tool calls (e.g., writing the generated poem to a file).

-   **Message Persistence:** The Overall Plan Evaluator's final assessment message is now correctly saved and reloaded in the chat history.

-   **Frontend Refactoring:** Substantial progress with `state_manager.js` and modular UI components. `script.js` is acting more as an orchestrator.

-   **Backend Refactoring:**  `message_handlers.py` has been successfully modularized into the `message_processing` sub-package.

-   **Stability:** Numerous backend errors (`TypeError`, `NameError`, `SyntaxError`) have been resolved, leading to more stable operation.

-   **UI Functionality:** Task management, file uploads, and artifact viewing (including navigation) are working reliably.

**Immediate Focus & User Feedback:**

1.  **Plan Confirmation UI (High Priority - Blocked):**

    -   **Issue:** The backend now sends a new `propose_plan_for_confirmation` message type, but the frontend (`script.js`) does not yet handle it. This means the UI currently doesn't display any plan for user confirmation, effectively halting plan-based interactions after the intent is classified as "PLAN".

    -   **Log Indication:**  `[SYSTEM] Unknown message type received: propose_plan_for_confirmation`

    -   **Goal:** Implement the frontend handling for this new message to display a concise plan proposal with "Confirm," "View Details," and "Cancel" options.

2.  **Chat Clutter & Plan Display Format (High Priority - Post above fix):**

    -   **User Feedback:** The current chat UI (when the full plan was displayed) is too cluttered with intermediate step outputs and the detailed plan itself. The goal is a cleaner interface, more like the `manus.ai` example, distinguishing clearly between direct agent-user messages and status/progress updates. The detailed plan, when shown, was also obtrusive and not persistent on refresh.

    -   **Proposed Solution (being implemented):**

        -   **Concise Plan Proposal:** Show a brief summary with action buttons (Confirm, View Details, Cancel).

        -   **"View Details":** Link to the `_plan_proposal_<ID>.md` (and later `_plan_<ID>.md`) artifact in the Artifact Viewer. This makes the detailed plan persistent and non-intrusive in the chat.

        -   **Intermediate Outputs:** Route most intermediate execution details (thoughts, tool outputs) to the Monitor Log. The main chat should show high-level progress via the "Agent Thinking" status line and final answers.

3.  **Color-Coding Agent Workspace & LLM Selectors (Medium Priority):**

    -   **User Idea:** Visually differentiate messages in the Agent Workspace (Monitor Log) based on the agent component (Planner, Controller, Executor, Evaluator) using background tints or border colors.

    -   **Extension:** Link these colors to the LLM selector dropdowns in the chat header to show which LLM is configured for which colored component.

    -   **Benefit:** Improved readability, traceability, and intuitive understanding of the agent's operations and configuration.

**Current Workflow (Poem Example - with fixes working):**

1.  User: "Create a file called poem.txt and write in it a small poem about stars."

2.  Intent Classifier: PLAN.

3.  Planner: Generates a plan (e.g., Step 1: Generate poem, Expected: "The text of a small poem about stars."; Step 2: Write poem to poem.txt).

    -   *Backend now sends `propose_plan_for_confirmation` (Frontend needs to handle this).*

4.  User Confirms (once UI is fixed).

5.  Backend saves `_plan_<ID>.md`.

6.  **Step 1: Generate Poem**

    -   Controller (receives `previous_step_output=None`): Validates, decides "No Tool".

    -   Executor (ReAct Agent): Receives directive. Generates the poem as `Final Answer`.

        -   *This poem (Executor's `Final Answer`) is currently sent as an `agent_message` to chat.*

    -   Step Evaluator: Confirms poem matches expected outcome.

    -   `last_successful_step_output` in `agent_flow_handlers.py` now stores this poem.

7.  **Step 2: Write File**

    -   Controller (receives poem from Step 1 via `previous_step_output`): Validates, decides `write_file` tool. **Crucially, it now uses the provided poem to formulate the `tool_input` for `write_file` (e.g., `poem.txt:::Twinkling lights...`).**

    -   Executor (ReAct Agent): Calls `write_file` with the correct poem.

    -   Step Evaluator: Confirms file written with correct content.

8.  Overall Plan Evaluator: Assesses overall success. This assessment is sent as an `agent_message` and saved to DB.

This document will be updated as we address these UI/UX items and any new ideas emerge.