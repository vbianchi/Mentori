# ResearchAgent: Project Roadmap (V1.0 Go-Live Target & Beyond)

This document outlines the planned development path for the ResearchAgent project. [cite: 257] It is a living document and will be updated as the project evolves. [cite: 258]

## Guiding Principles for Development

-   **User-Centricity:** Prioritize features and fixes that directly improve the user's ability to conduct research efficiently and effectively. [cite: 259]

-   **Stability & Reliability:** Ensure the core system is robust before adding complex new features. [cite: 260]

-   **Modularity:** Design components that are as independent as possible to facilitate easier development, testing, and maintenance. [cite: 261]

-   **Iterative Improvement:** Release updates incrementally, gathering feedback and refining features along the way. [cite: 262]

## Phase 1: Core Functionality, Initial UI & Foundational Tool System (Completed)

-   Basic three-panel UI structure (Tasks, Chat, Monitor/Artifacts). [cite: 263]

-   WebSocket communication for real-time updates. [cite: 263]

-   Task creation, selection, deletion, renaming, and basic persistent history via SQLite. [cite: 264]

-   Initial agent flow (Intent Classification, Planning, Execution, Evaluation - PCEE). [cite: 265]

-   Basic tool integration. [cite: 265]

-   Role-specific LLM configurations. [cite: 265]

-   Significant UI/UX improvements (collapsible steps, agent avatars, improved font sizes, LLM selector styling, dark theme refinements), fixes for `read_file` tool output, implementation of Token Counter, File Upload, and enhanced In-Chat Tool Feedback. [cite: 266]

-   **Architectural Refactor: "Plug and Play" Tool System (COMPLETE & STABLE):** [cite: 267]

    -   Implemented a dynamic tool loading mechanism using `tool_config.json`. [cite: 268]

    -   `tool_loader.py` parses the config and instantiates tools. [cite: 269]

    -   All 9 tools dynamically loaded and operational. [cite: 270, 161, 300]

    -   Scalable foundation for future tool development. [cite: 271]

-   **Pydantic v2 Migration (Largely Completed):** [cite: 272]

    -   Migrated most Pydantic models for Tool Argument Schemas and LLM Output Schemas to v2. [cite: 273, 274, 163]

    -   Resolved associated Pydantic v2 strictness issues. [cite: 275]

    -   `deep_research_tool.py` Pydantic model validator updated.

## Phase 2: V1.0 Go-Live (Target: Within 2 Months - MUST HAVE Focus) [cite: 277]

This phase focuses on delivering a stable, reliable, and core-efficient ResearchAgent.

1\.  **CRITICAL: Agent Task Cancellation & STOP Button:** [cite: 278]

    * **Goal:** Ensure agent tasks are reliably cancelled (via STOP button or context switch). Make STOP button fully functional. [cite: 34, 35, 66, 175, 278]

    * **Effort:** ~7/10

    * **Time Est.:** ~9-12 hours

2\.  **HIGH: BUG - ARTIFACT VIEWER REFRESH:** [cite: 279]

    * **Goal:** Ensure reliable auto-update of the artifact viewer after file writes. [cite: 37, 67, 176]

    * **Effort:** ~4/10

    * **Time Est.:** ~4-6 hours

3\.  **HIGH: AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:** [cite: 280]

    * **Goal:** Ensure the PCEE loop's Evaluator component reliably assesses step success and retry mechanism is effective. [cite: 68, 177, 178, 281]

    * **Effort:** ~7/10

    * **Time Est.:** ~8-12 hours

4\.  **HIGH: DEV OPS / STABILITY - Comprehensive Testing:** [cite: 283]

    * **Goal:** Expand unit and integration tests for critical backend and frontend components. [cite: 68, 179]

    * **Effort:** ~6/10 (Initial batch)

    * **Time Est.:** ~10-15 hours (Initial batch)

## Phase 3: V1.x Enhancements (Post Go-Live - SHOULD HAVE Focus) [cite: 284]

This phase aims to enhance the agent's capabilities, user control, and overall experience.

1\.  **Make Tavily Search Optional:**

    * **Goal:** Add configuration to disable Tavily search for privacy, with user notification.

    * **Effort:** ~5/10

    * **Time Est.:** ~3-5 hours

2\.  **UI/UX: Finalize "View [artifact] in Artifacts" Links:** [cite: 293]

    * **Goal:** Fully implement links from chat to artifacts in the viewer. [cite: 72, 182]

    * **Effort:** ~3/10

    * **Time Est.:** ~2-3 hours

3\.  **"Plug and Play" Tool System Enhancements:** [cite: 286]

    * **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` to formal JSON Schemas. [cite: 287, 71, 181]

        * **Effort:** ~5/10

        * **Time Est.:** ~4-6 hours

    * **Develop New Tool Integration Guide:** Create documentation and templates for adding new tools. [cite: 288, 71, 181]

        * **Effort:** ~4/10

        * **Time Est.:** ~3-5 hours

4\.  **UI/UX: Artifact Viewer - Folder Link/View (Simple Version):**

    * **Goal:** Provide links to task workspace folders or a simple list of contents.

    * **Effort:** ~2/10

    * **Time Est.:** ~2-3 hours

5\.  **Enhanced Agent Capabilities & Efficiency (from previous roadmap):** [cite: 289]

    * Improved Agent Memory / Workspace RAG (Basic). [cite: 289]

    * Streaming LLM Responses (Final Answers). [cite: 290]

    * Refined Error Parsing & Reporting. [cite: 290]

    * Robust Asynchronous Task Cancellation (Advanced - may be partially covered by Phase 2). [cite: 290, 183]

6\.  **Multi-Tasking & User Control (from previous roadmap):** [cite: 291]

    * Asynchronous Background Task Processing (Basic Stop/Switch). [cite: 291, 44]

    * Optional Tools (via `tool_config.json` `enabled` flag or UI - Tavily optionality is a start). [cite: 292, 183]

7\.  **Advanced User-in-the-Loop (UITL/HITL) Capabilities.** [cite: 293, 184]

8\.  **Low Priority Bug Fixes & UI Polish:**

    * UI BUG: Copy button placement for simple messages. (Effort: 2, Time: 1-2h)

    * UI/UX POLISH: Global "agent-thinking-status" line behavior. (Effort: 2, Time: 1-2h) [cite: 38]

    * UI/UX POLISH: Styling for agent step announcements. (Effort: 2, Time: 1-2h) [cite: 39]

    * WARNING: PLAN FILE STATUS UPDATE: Fix warnings about not finding step patterns. (Effort: 3, Time: 2h) [cite: 41]

    * REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES: Confirm handling. (Effort: 1, Time: 1h) [cite: 42]

    * DEBUG: Monitor Log Color-Coding: Verify/implement CSS. (Effort: 1, Time: 1-2h) [cite: 43]

## Phase 4: Future Iterations (NICE TO HAVE Focus) [cite: 294]

This phase will focus on adding more advanced features, expanding the tool ecosystem, and further polishing the UI/UX.

1\.  **Advanced Agent Reasoning & Self-Correction (Full).** [cite: 294, 185]

2\.  **Comprehensive Tool Ecosystem Expansion (Leveraging "Plug and Play"):** [cite: 295, 185]

    * **Rscript Execution Tool:** (Effort: ~6/10, Time Est.: ~8-12h) [cite: 73, 295]

    * **Data_Comparator:** (Effort: ~5/10, Time Est.: ~6-10h)

    * **Data_Compiler:** (Effort: ~6/10, Time Est.: ~8-12h)

    * **Data_Filter:** (Effort: ~5/10, Time Est.: ~6-10h)

    * **Data_Formatter:** (Effort: ~4/10, Time Est.: ~4-8h)

    * **Domain_Analysis (e.g., InterProScan wrapper):** (Effort: ~7/10, Time Est.: ~10-15h)

    * **Information_Extractor (schema-based):** (Effort: ~7/10, Time Est.: ~10-15h)

    * **Keyword_Extractor:** (Effort: ~4/10, Time Est.: ~4-6h)

    * **Knowledge_Lookup:** (Effort: ~6/10, Time Est.: ~8-12h)

    * **Report_Generator (general, structured):** (Effort: ~8/10, Time Est.: ~12-20h)

    * **Sequence_Search (e.g., BLAST wrapper):** (Effort: ~7/10, Time Est.: ~10-15h)

    * **Specialized_DB_Search (ClinVar, dbSNP, KEGG, etc.):** (Effort: ~7/10 per DB, Time Est.: ~10-15h per DB)

    * **Text_Summarizer (standalone):** (Effort: ~4/10, Time Est.: ~4-8h)

    * **Text_Synthesizer (standalone):** (Effort: ~5/10, Time Est.: ~6-10h)

    * Enhanced PDF Parsing. [cite: 296]

    * More bioinformatics tools, data analysis/visualization tools, document preparation tools. [cite: 296, 74]

3\.  **UI/UX & Workspace Enhancements (Folder Viewer, Dedicated Steps Panel, etc.).** [cite: 297, 186, 75]

4\.  **Backend & Architecture (Scalability, Personas).** [cite: 297, 186, 75]

5\.  **Deployment & DevOps.** [cite: 297, 187, 76]

## Phase 5: Advanced Agent Autonomy & Specialized Applications (Longer-Term)

(Content remains the same as previous full README: Enhanced Agent Self-Correction, Long-Term Memory, Cloud Deployment, etc.)

## Completed Milestones (Summary up to current state)

-   **v2.0-v2.4 (approx):** Initial architecture, core agent loop (PCEE), basic UI (3-panel), SQLite history, foundational tool integration, modular JS frontend, initial UI enhancements. [cite: 298]

-   **v2.5.0 - v2.5.2 (approx):** Significant UI/UX improvements, Token Counter, File Upload, In-Chat Tool Feedback, Plan Proposal UI. [cite: 299]

-   **v2.5.3 (Current Focus - In Progress):**

    -   **"Plug and Play" Tool System Refactor (COMPLETE):** All 9 tools dynamically loaded via `tool_config.json`. [cite: 300, 161]

    -   **Pydantic v2 Migration (Largely Complete):** Migrated models for tool arguments, intent classifier, planner, controller, and addressed `deep_research_tool.py` validator. [cite: 301, 164, 273, 274] `evaluator.py` models previously Pydantic v1, now assumed v2 or compatible.

    -   Resolved numerous import and runtime errors related to tool loading and Pydantic integration. [cite: 302]

    -   ReAct agent prompt improved for direct content output.

    -   History handling for `monitor_user_input` warning resolved.

    -   Ongoing: Critical bug fixes (Agent Task Cancellation, Artifact Viewer Refresh), Agent Capability enhancements (Step Evaluation/Retry), and comprehensive testing. [cite: 303]

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses. [cite: 304]