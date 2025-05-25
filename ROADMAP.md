ResearchAgent: Project Roadmap (v2.5.1 Base)
============================================

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

Guiding Principles for Development
----------------------------------

-   **Accuracy & Reliability Over Speed**

-   **User-in-the-Loop (UITL/HITL)**

-   **Modularity & Maintainability**

-   **Extensibility**

Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.5.1)
---------------------------------------------------------------------------------

-   **UI Framework:** Three-panel layout.

-   **Backend Infrastructure:** Python, WebSockets, HTTP file server.

-   **Task Management:** Create, select, delete (UI fixed), rename tasks with persistent storage.

-   **Basic Agent Flow:** Intent Classification, P-C-E-E pipeline.

    -   **Poem Discrepancy Fixed:** Controller now correctly uses previous step's output.

    -   **Evaluator Message Persistence Fixed.**

-   **Core Tools:** Web search, file I/O, PubMed, web reader.

-   **`DeepResearchTool` v1:** Functional.

-   **LLM Configuration:** Gemini & Ollama, role-specific.

-   **Frontend Refactoring (v2.5.1):** Modularized JavaScript (`state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`). `script.js` acts as orchestrator.

-   **Backend Refactoring (v2.5.1):**  `message_handlers.py` modularized into `message_processing` sub-package.

-   **Numerous Stability Fixes:** Addressed various backend errors.

Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus)
----------------------------------------------------------------------------------

1.  **Implement UI for Concise Plan Proposal & Interaction (High Priority - Partially Blocked by Frontend Handler)**

    -   **Goal:** Create a clean, user-friendly way to confirm plans, reducing chat clutter.

    -   **Details:**

        -   **Backend:** Sends `propose_plan_for_confirmation` with summary, plan ID, and full plan. Saves proposal as `_plan_proposal_<ID>.md` artifact. Handles `cancel_plan_proposal`. (Backend part for sending new message type is done).

        -   **Frontend:**

            -   **FIX NEEDED:** Handle `propose_plan_for_confirmation` in `script.js`.

            -   `chat_ui.js`: Display concise summary with "Confirm", "View Details", "Cancel" buttons.

            -   "Confirm": Sends `execute_confirmed_plan`.

            -   "View Details": Focuses artifact viewer on `_plan_proposal_<ID>.md`.

            -   "Cancel": Sends `cancel_plan_proposal`.

        -   Ensure interaction is logged to DB for chat history.

    -   **Status:** Backend ready to send new message. **Frontend needs handler for this message type.**

2.  **Refine Intermediate Step Chat Output (High Priority - Post Plan UI Fix)**

    -   **Goal:** Keep main chat focused; move detailed step-by-step execution logs to Monitor.

    -   **Details:**

        -   Backend (`callbacks.py`): Ensure most intermediate outputs (thoughts, tool logs) are `monitor_log`. Only key user-facing results (like the generated poem, final evaluation) are `agent_message`.

        -   Frontend (`chat_ui.js`, `script.js`): Use `agentThinkingStatusElement` for transient updates. Route messages correctly.

    -   **Status:** Design complete, implementation pending plan UI fix.

3.  **Color-Coding UI Elements (Medium Priority)**

    -   **Goal:** Visually differentiate agent component messages in Monitor and link to LLM selectors.

    -   **Details:** CSS classes, backend to send `log_source`, frontend modules (`monitor_ui.js`, `llm_selector_ui.js`) to apply styles.

    -   **Status:** Planned.

4.  **Further `script.js` Refinement (Phase 3.2 Completion - Medium Priority)**

    -   **Goal:** Ensure `script.js` is a lean orchestrator.

    -   **Details:** Final review to move any residual UI logic/DOM manipulation to modules and ensure all state via `StateManager`.

    -   **Status:** Partially complete, final pass needed.

5.  **Advanced Step Self-Correction (Medium Priority)**

    -   **Goal:** Improve autonomous error recovery by Step Evaluator.

    -   **Details:** Step Evaluator to propose revised step descriptions/parameters for retries.

    -   **Status:** Design phase.

6.  **User-in-the-Loop (UITL/HITL) - Foundational (Medium Priority)**

    -   **Goal:** Agent-initiated interaction points during plan execution.

    -   **Details:** Planner to generate "interaction steps"; backend to pause & send requests; UI to render prompts.

    -   **Status:** Design phase.

Phase 3: Advanced Interactivity & Tooling (Mid-Term)
----------------------------------------------------

(Items remain the same as previous roadmap: Advanced UITL, New Tools, Workspace RAG)

Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
-------------------------------------------------------------------------

(Items remain the same: Advanced Re-planning, Permission Gateway, Streaming Output, Specialized Personas)

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses.