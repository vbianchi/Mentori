ResearchAgent: Project Roadmap (v2.5.3 Target Base)
===================================================

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

Guiding Principles for Development
----------------------------------

-   Accuracy & Reliability Over Speed

-   User-in-the-Loop (UITL/HITL)

-   Modularity & Maintainability

-   Extensibility

Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.5.2)
---------------------------------------------------------------------------------

(Details largely unchanged, reflects the solid foundation)

-   UI Framework: Three-panel layout.

-   Backend Infrastructure: Python, WebSockets, `aiohttp`.

-   Task Management: Persistent storage, UI updates.

-   Core Agent Flow (P-C-E-E Pipeline): Intent Classification, Planner, Controller, Executor, Step Evaluator, Overall Plan Evaluator.

-   Key Fixes Incorporated (Controller output usage, persistent evaluations, robust JSON parsing, ReAct prompt refinements).

-   Core Tools Implemented & Refined (`Tavily`, `DuckDuckGo`, `DeepResearchTool` v1, File I/O, `workspace_shell`, `python_package_installer`, `Python_REPL`, `pubmed_search`, `web_page_reader`).

-   LLM Configuration: Google Gemini & Ollama, role-specific selection.

-   Frontend & Backend Refactoring (Modularization).

-   Backend Plan Proposal Mechanism (v2.5.2 - v2.5.3 target): `propose_plan_for_confirmation`, artifact saving, cancellation handling, `confirmed_plan_log` for history.

Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus - Targeting v2.5.3)
-----------------------------------------------------------------------------------------------------

1.  **UI for Plan Proposal Interaction & Persistence (COMPLETE)**

    -   Goal: Clean, user-friendly, persistent plan review and confirmation in chat.

    -   Status:

        -   Inline "View Details" for plan proposals: **Implemented.** (Toggles visibility of `structured_plan` within the chat block).

        -   Transform Proposal to Persistent Message on Confirmation: **Implemented.** (Interactive block changes to static display with summary and expanded steps).

        -   Load Confirmed Plan from History: **Implemented.** (Backend `confirmed_plan_log` messages now render as static confirmed plans from history).

2.  **Refine Intermediate Step Chat Output & Final Message Delivery (High Priority - In Progress)**

    -   Goal: Cleaner chat (`manus.ai` style) with primary interactions; verbose details in Monitor. Ensure final, user-facing answers are clearly presented in chat for both Direct QA and successful Plans.

    -   Details & Status:

        -   Backend (`callbacks.py`): **Modified** to route most intermediate outputs (tool I/O, detailed thoughts) to `monitor_log`. Sends structured `agent_thinking_update` messages for concise chat status. No longer sends `agent_message` from `on_agent_finish` for intermediate steps.

        -   Frontend (`script.js`, `chat_ui.js`): **Updated** to handle structured `agent_thinking_update` and display concise status. `addChatMessageToUI` now focuses on user, final agent, and critical status messages.

        -   **PENDING/VERIFY:** Ensure `agent_flow_handlers.py` correctly constructs and sends the *final*  `agent_message` to the user after Direct QA completion or Overall Plan Evaluation.

        -   **PENDING/VERIFY:** Ensure `agent-thinking-status` UI element accurately reflects all stages and correctly resets to "Idle" or "Completed" to prevent input lock-up.

3.  **Color-Coding UI Elements (Medium Priority - In Progress)**

    -   Goal: Visually differentiate Monitor Log messages by source.

    -   Details & Status:

        -   Backend (`callbacks.py`): **Modified** to include `log_source` in `monitor_log` payloads.

        -   Frontend (`monitor_ui.js`): **Updated** to attempt adding CSS classes based on `log_source`.

        -   **PENDING/DEBUG:** CSS rules in `style.css` need to be created/debugged to ensure visual differentiation. Review if all `add_monitor_log_func` calls in backend consistently provide `log_source`.

4.  **BUG FIXES (High Priority - Actively Addressing)**

    -   **`deep_research_synthesizer` Input Errors:**

        -   Issue: Controller sometimes sends plain string instead of JSON; subsequent retries had `query` vs. `topic` mismatch with the tool's Pydantic schema.

        -   **PENDING:** Modify `controller.py` prompt for robust JSON string generation. Ensure `deep_research_tool.py` schema is definitively using `query` and this version is active.

    -   **Chat Input Unresponsive:**

        -   Issue: Chat input can lock up after a task completes or errors out, requiring a task switch to re-enable.

        -   **PENDING:** Ensure agent status flags (`isAgentRunning` in `StateManager`) are correctly reset and final "Idle" `agent_thinking_update` messages are consistently sent and handled.

5.  **Tool Enhancements & Features (Mid Priority)**

    -   **FEATURE: Save `deep_research_synthesizer` Output:**

        -   **Implemented (in `deep_research_tool.py` v3):** Tool now saves its Markdown report to a file in the task workspace.

        -   **VERIFY:** Ensure artifact refresh correctly lists this new file.

        -   **CONSIDER:** How to best present this saved file to the user (e.g., link in final agent message).

    -   Advanced Step Self-Correction & Error Handling (Current retry mechanism is basic).

    -   User-in-the-Loop (UITL/HITL) - Foundational Interaction Points (Design phase).

6.  **Further `script.js` Refinement (Phase 3.2 Completion - Medium Priority - Ongoing)**

    -   Goal: Ensure `script.js` is a lean orchestrator.

    -   Status: Ongoing as new UI interactions are developed.

Phase 3: Advanced Interactivity & Tooling (Mid-Term)
----------------------------------------------------

(No changes to this section's general goals yet)

-   Advanced User-in-the-Loop (UITL/HITL) Capabilities (Editable plans, step-level intervention).

-   New Tools & Tool Enhancements (Code Interpreter, Data Visualization, DB Querying, Playwright activation).

-   Workspace RAG.

-   Improved Agent Memory & Context Management.

Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
-------------------------------------------------------------------------

(No changes to this section's general goals yet)

-   Advanced Re-planning & Self-Correction.

-   User Permissions & Resource Gateway.

-   Streaming Output.

-   Specialized Agent Personas & Workflows.

-   Collaborative Features.

This roadmap will guide our development efforts. Feedback and adjustments are welcome.