# ResearchAgent: Project Roadmap (V1.0 Go-Live Target & Beyond)

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

## Guiding Principles for Development

-   **User-Centricity:** Prioritize features and fixes that directly improve the user's ability to conduct research efficiently and effectively.
-   **Stability & Reliability:** Ensure the core system is robust before adding complex new features.
-   **Modularity:** Design components that are as independent as possible to facilitate easier development, testing, and maintenance.
-   **Iterative Improvement:** Release updates incrementally, gathering feedback and refining features along the way.

## Phase 1: Core Functionality, Initial UI & Foundational Tool System (Completed)

-   Basic three-panel UI structure (Tasks, Chat, Monitor/Artifacts).
-   WebSocket communication for real-time updates.
-   Task creation, selection, deletion, renaming, and basic persistent history via SQLite.
-   Initial agent flow (Intent Classification, Planning, Execution, Evaluation - PCEE).
-   Basic tool integration (e.g., web search, file I/O).
-   Role-specific LLM configurations.
-   Significant UI/UX improvements (collapsible steps, agent avatars, improved font sizes, LLM selector styling, dark theme refinements), fixes for `read_file` tool output, implementation of Token Counter, File Upload, and enhanced In-Chat Tool Feedback.
-   **Architectural Refactor: "Plug and Play" Tool System (COMPLETE & STABLE):**
    -   Implemented a dynamic tool loading mechanism using `tool_config.json`.
    -   `tool_loader.py` parses the config and instantiates tools, including injecting runtime context like `task_workspace` for task-specific tools.
    -   All 6 general-purpose tools (`tavily_search_api`, `web_page_reader`, `python_package_installer`, `pubmed_search`, `Python_REPL`, `deep_research_synthesizer`) migrated to individual Python scripts and are loaded via `tool_config.json`.
    -   All 3 task-specific tools (`read_file`, `write_file`, `workspace_shell`) are also now fully loaded via `tool_config.json`.
    -   This provides a scalable foundation for future tool development and improves system maintainability.
-   **Pydantic v2 Migration (Partially Completed):**
    -   Successfully migrated Pydantic models to v2 for:
        -   Tool Argument Schemas: `TavilySearchInput`, `WebPageReaderInput`, `PythonPackageInstallerInput`, `PubMedSearchInput`, `PythonREPLInput`.
        -   LLM Output Schemas: `IntentClassificationOutput` (in `intent_classifier.py`), `PlanStep`, `AgentPlan` (in `planner.py`), `ControllerOutput` (in `controller.py`).
    -   Resolved associated Pydantic v2 strictness issues (e.g., field naming with underscores in `TavilyAPISearchTool` and `DeepResearchTool`).
    -   Corrected import errors and parsing logic in `controller.py` related to Pydantic v2 usage.

## Phase 2: V1.0 Go-Live (Target: Within 2 Months - MUST HAVE Focus)

This phase focuses on delivering a stable, reliable, and core-efficient ResearchAgent.

1.  **CRITICAL (MUST HAVE) - BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button:**
    -   Ensure agent tasks are reliably cancelled when intended (e.g., via STOP button, or context switch).
    -   Make STOP button fully functional.
2.  **HIGH (MUST HAVE) - BUG - ARTIFACT VIEWER REFRESH:**
    -   Ensure reliable auto-update of the artifact viewer after file writes.
3.  **HIGH (MUST HAVE) - AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    -   Ensure the PCEE loop's Evaluator component reliably assesses step success.
    -   Ensure the retry mechanism effectively uses evaluator feedback.
    -   **Note:** Pydantic v2 migration for `evaluator.py` models (`StepCorrectionOutcome`, `EvaluationResult`) is pending and will be addressed as part of this or the subsequent phase.
4.  **HIGH (MUST HAVE) - DEV OPS / STABILITY - Comprehensive Testing:**
    -   Expand unit and integration tests for critical backend and frontend components.

## Phase 3: V1.x Enhancements (Post Go-Live - SHOULD HAVE Focus)

This phase aims to enhance the agent's capabilities, user control, and overall experience.

1.  **Complete Pydantic v2 Migration:**
    -   Migrate remaining Pydantic models in `evaluator.py` (`StepCorrectionOutcome`, `EvaluationResult`).
    -   Migrate any remaining internal Pydantic models in `deep_research_tool.py`.
2.  **"Plug and Play" Tool System Enhancements (Post Pydantic v2 Migration):**
    -   **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas.
    -   **Develop New Tool Integration Guide:** Create comprehensive documentation and templates for adding new tools.
3.  **Enhanced Agent Capabilities & Efficiency:**
    -   Improved Agent Memory / Workspace RAG (Basic).
    -   Streaming LLM Responses (Final Answers).
    -   Refined Error Parsing & Reporting.
    -   Robust Asynchronous Task Cancellation (Advanced).
4.  **Multi-Tasking & User Control:**
    -   Asynchronous Background Task Processing (Basic Stop/Switch).
    -   Optional Tools (via `tool_config.json` `enabled` flag or UI).
5.  **UI/UX:**
    -   Finalize "View \[artifact\] in Artifacts" Links.
6.  **Advanced User-in-the-Loop (UITL/HITL) Capabilities.**

## Phase 4: Future Iterations (NICE TO HAVE Focus)

This phase will focus on adding more advanced features, expanding the tool ecosystem, and further polishing the UI/UX.

1.  **Advanced Agent Reasoning & Self-Correction (Full).**
2.  **Comprehensive Tool Ecosystem Expansion (Leveraging "Plug and Play"):**
    -   Rscript Execution Tool.
    -   Enhanced PDF Parsing.
    -   More bioinformatics tools, data analysis/visualization tools, document preparation tools.
3.  **UI/UX & Workspace Enhancements** (Folder Viewer, Dedicated Steps Panel, etc.).
4.  **Backend & Architecture** (Scalability, Personas).
5.  **Deployment & DevOps.**

## Phase 5: Advanced Agent Autonomy & Specialized Applications (Longer-Term)

(Content remains the same as previous full README: Enhanced Agent Self-Correction, Long-Term Memory, Cloud Deployment, etc.)

## Completed Milestones (Summary up to current state)

-   **v2.0-v2.4 (approx):** Initial architecture, core agent loop (PCEE), basic UI (3-panel), SQLite history, foundational tool integration, modular JS frontend, initial UI enhancements.
-   **v2.5.0 - v2.5.2 (approx):** Significant UI/UX improvements, Token Counter, File Upload, In-Chat Tool Feedback, Plan Proposal UI.
-   **v2.5.3 (Current Focus - In Progress):**
    -   **"Plug and Play" Tool System Refactor (COMPLETE):** All 9 tools dynamically loaded via `tool_config.json`.
    -   **Pydantic v2 Migration (Partially Complete):** Migrated models for tool arguments, intent classifier, planner, and controller. `evaluator.py` models pending.
    -   Resolved numerous import and runtime errors related to tool loading and Pydantic integration.
    -   Ongoing: Critical bug fixes (Agent Task Cancellation, Artifact Viewer Refresh), Agent Capability enhancements (Step Evaluation/Retry), and comprehensive testing.

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses.
