ResearchAgent: Project Roadmap (v2.5.3 Target Base)
===================================================

This document outlines the planned development path for the ResearchAgent project. [cite: 1630] It is a living document and will be updated as the project evolves.

Guiding Principles for Development
----------------------------------
-   Accuracy & Reliability Over Speed
-   User-in-the-Loop (UITL/HITL)
-   Modularity & Maintainability
-   Extensibility

Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.5.2)
---------------------------------------------------------------------------------
(Details largely unchanged, reflects the solid foundation)
-   UI Framework: Three-panel layout. [cite: 1631]
-   Backend Infrastructure: Python, WebSockets, `aiohttp`. [cite: 1632]
-   Task Management: Persistent storage, UI updates. [cite: 1632]
-   Core Agent Flow (P-C-E-E Pipeline): Intent Classification, Planner, Controller, Executor, Step Evaluator, Overall Plan Evaluator. [cite: 1633]
    -   Key Controller/Agent/Evaluator prompt refinements for robust tool input (JSON strings) and output handling. [cite: 1634]
-   Core Tools Implemented & Refined (`Tavily`, `DuckDuckGo`, `DeepResearchTool` v2 with fixed input, File I/O, `workspace_shell`, `python_package_installer`, `Python_REPL`, `pubmed_search`, `web_page_reader`). [cite: 1635]
-   LLM Configuration: Google Gemini & Ollama, role-specific selection. [cite: 1636]
-   Frontend & Backend Refactoring (Modularization).
-   Backend Plan Proposal Mechanism (v2.5.2 - v2.5.3 target): `propose_plan_for_confirmation`, artifact saving, cancellation handling, `confirmed_plan_log` for history. [cite: 1637]

Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus - Targeting v2.5.3)
-----------------------------------------------------------------------------------------------------

1.  **UI for Plan Proposal Interaction & Persistence (COMPLETE)**
    * Goal: Clean, user-friendly, persistent plan review and confirmation in chat. [cite: 1638]
    * Status:
        * Inline "View Details" for plan proposals: **Implemented.** [cite: 1639]
        * Transform Proposal to Persistent Message on Confirmation: **Implemented.** [cite: 1640]
        * Load Confirmed Plan from History: **Implemented.** [cite: 1641]

2.  **Core Agent Execution Stability (LARGELY RESOLVED / CONTINUOUS IMPROVEMENT)**
    * **`deep_research_synthesizer` Input & Execution:**
        * **Status: RESOLVED.** Controller now correctly guides the agent to produce JSON string input for the tool. [cite: 1657] The tool successfully executes and returns its report. Subsequent steps (e.g., `write_file`) correctly process this output.
    * **Controller Prompt Formatting `KeyError`:**
        * **Status: RESOLVED.** Implemented escaping for dynamic content in prompt templates.

3.  **Refine Chat UI/UX & Final Message Delivery (High Priority - In Progress)**
    * Goal: Cleaner chat (`manus.ai` style) with primary interactions; [cite: 1642] verbose details in Monitor. Ensure final, user-facing answers are clearly and relevantly presented in chat for both Direct QA and successful Plans. [cite: 1643]
    * Details & Status:
        * Backend (`callbacks.py`): **Modified** to route most intermediate outputs to `monitor_log`. Sends structured `agent_thinking_update`. [cite: 1645]
        * Frontend (`script.js`, `chat_ui.js`): **Updated** to handle `agent_thinking_update`. [cite: 1646]
        * `agent_flow_handlers.py`: **Modified** to send the output of the last successful plan step as the final `agent_message`.
        * **PENDING/UX Design:**
            * Further refine which *specific content* from a plan is most useful for the final chat message (e.g., the deep research report itself vs. a "file saved" confirmation).
            * Design and implement a clearer step-by-step chat flow for plan execution (inspired by `manus.ai`), possibly with major step announcements in chat and contextual sub-statuses.
            * Refine how recoverable errors are presented in chat to be less alarming.

4.  **BUG FIX (High Priority - Next): Chat Input Unresponsive**
    * Issue: Chat input can lock up after a task completes or errors out. [cite: 1659]
    * **PENDING:** Ensure agent status flags (`isAgentRunning` in `StateManager`) are correctly reset and final "Idle" `agent_thinking_update` messages are consistently sent/handled. [cite: 1660]

5.  **Color-Coding Monitor Log (Medium Priority - Debugging)**
    * Goal: Visually differentiate Monitor Log messages by source. [cite: 1650]
    * Details & Status:
        * Backend (`callbacks.py`): Includes `log_source`. [cite: 1651]
        * Frontend (`monitor_ui.js`): Attempts adding CSS classes. [cite: 1652]
        * **PENDING/DEBUG:** CSS rules in `style.css` need to be created/debugged. [cite: 1653] Verify `log_source` consistency from backend. [cite: 1654]

6.  **Tool Enhancements & Features (Mid Priority - Ongoing)**
    * **FEATURE: Save `deep_research_synthesizer` Output:**
        * **Status: VERIFIED/COMPLETE.** The `deep_research_synthesizer` generates a report, and a subsequent `write_file` step in a plan can correctly save this report to the task workspace. Artifact refresh lists the file. [cite: 1661, 1662]
    * Advanced Step Self-Correction & Error Handling (Current retry mechanism is basic). [cite: 1664]
    * User-in-the-Loop (UITL/HITL) - Foundational Interaction Points (Design phase). [cite: 1665]

7.  **Further `script.js` Refinement (Medium Priority - Ongoing)**
    * Goal: Ensure `script.js` is a lean orchestrator. [cite: 1666]
    * Status: Ongoing as new UI interactions are developed. [cite: 1667]

Phase 3: Advanced Interactivity & Tooling (Mid-Term)
----------------------------------------------------
(No changes to this section's general goals yet)
-   Advanced User-in-the-Loop (UITL/HITL) Capabilities (Editable plans, step-level intervention). [cite: 1668]
-   New Tools & Tool Enhancements (Code Interpreter, Data Visualization, DB Querying, Playwright activation). [cite: 1669]
-   Workspace RAG. [cite: 1670]
-   Improved Agent Memory & Context Management. [cite: 1670]

Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
-------------------------------------------------------------------------
(No changes to this section's general goals yet)
-   Advanced Re-planning & Self-Correction. [cite: 1671]
-   User Permissions & Resource Gateway. [cite: 1672]
-   Streaming Output. [cite: 1672]
-   Specialized Agent Personas & Workflows. [cite: 1673]
-   Collaborative Features.

This roadmap will guide our development efforts. [cite: 1674] Feedback and adjustments are welcome.
