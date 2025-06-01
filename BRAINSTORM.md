# BRAINSTORM.md - ResearchAgent Project (V1.0 Go-Live Target & Beyond)

This document tracks the current workflow, user feedback, and brainstorming ideas for the ResearchAgent project.

## Current Version & State (Targeting V1.0 Go-Live - Post Tool Refactor, Pydantic v2 Migration Underway)

**Recent Key Advancements:**

1.  **Architectural Refactor: "Plug and Play" Tool System (COMPLETE & STABLE):**
    * Implemented a dynamic tool loading mechanism using `tool_config.json`.
    * `tool_loader.py` parses the config and instantiates tools, including injecting runtime context like `task_workspace` for task-specific tools.
    * All 6 general-purpose tools (`tavily_search_api`, `web_page_reader`, `python_package_installer`, `pubmed_search`, `Python_REPL`, `deep_research_synthesizer`) migrated to individual Python scripts and are loaded via `tool_config.json`.
    * All 3 task-specific tools (`read_file`, `write_file`, `workspace_shell`) are also now fully loaded via `tool_config.json`.
    * This provides a scalable and maintainable foundation for future tool development.
2.  **Pydantic v2 Migration (IN PROGRESS):**
    * Successfully migrated Pydantic models to v2 for:
        * Tool Argument Schemas: `TavilySearchInput`, `WebPageReaderInput`, `PythonPackageInstallerInput`, `PubMedSearchInput`, `PythonREPLInput`.
        * LLM Output Schemas: `IntentClassificationOutput`, `PlanStep`, `AgentPlan`, `ControllerOutput`.
    * Resolved associated Pydantic v2 strictness issues (e.g., field naming with underscores in `TavilyAPISearchTool` and `DeepResearchTool`).
    * **Pending:** Migration for models in `evaluator.py` (`StepCorrectionOutcome`, `EvaluationResult`) and internal Pydantic models within `deep_research_tool.py`.
3.  **Core Agent Logic & Tool Integration (IMPROVED):**
    * Controller logic refined for better handling of `JsonOutputParser` results.
    * Numerous import and runtime errors resolved, leading to stable plan execution with the new tool system.
4.  **Chat UI/UX Refinement (Significant Progress - features as previously listed):**
    * Visual Design & Readability improvements.
    * Interactivity: Collapsible steps and tool outputs.
    * Persistence & Consistency for plans.
    * Bug fixes related to UI rendering and behavior.
    * Completed Features: Token Counter, File Upload, In-Chat Tool Feedback, Plan Proposal UI.

## Immediate Focus & User Feedback / Known Issues / Proposed Enhancements (V1.0 Go-Live Focus):

1.  **CRITICAL (MUST HAVE) - BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button:**
    * **Observation:** Still a primary concern. Switching UI tasks or using STOP button needs to reliably cancel/stop active agent processing.
    * **Goal:** Implement robust agent task cancellation.
2.  **HIGH (MUST HAVE) - BUG - ARTIFACT VIEWER REFRESH:**
    * Ensure consistent and immediate auto-update.
3.  **HIGH (MUST HAVE) - AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    * Ensure Evaluator accurately assesses step success (actual content vs. description of it).
    * Ensure retry mechanism uses evaluator feedback effectively.
4.  **HIGH (MUST HAVE) - DEV OPS / STABILITY - Comprehensive Testing:**
    * Expand tests for critical backend (cancellation, agent lifecycle, all tools) and frontend.
5.  **MEDIUM (SHOULD HAVE) - Complete Pydantic v2 Migration:**
    * Migrate Pydantic models in `evaluator.py` (`StepCorrectionOutcome`, `EvaluationResult`).
    * Migrate any remaining internal Pydantic models in `deep_research_tool.py`.
6.  **MEDIUM (SHOULD HAVE) - "Plug and Play" Tool System Enhancements (Post Pydantic v2 Migration):**
    * **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas (leveraging Pydantic `args_schema` from tool classes).
    * **Develop New Tool Integration Guide:** Create comprehensive documentation and templates for adding new tools to the system.
7.  **MEDIUM (SHOULD HAVE) - UI/UX - Finalize "View [artifact] in Artifacts" Links.**
8.  **LOW (NICE TO HAVE) - UI/UX POLISH & DEBUGGING (as previously listed, e.g., Monitor Log Color-Coding, Plan File Status Update Warnings).**

## Future Brainstorming / More Complex Enhancements (Post V1.0 Go-Live & Tool Refactor)

### SHOULD HAVE (Important for V1.x releases):
(Content largely same as previous full README: Enhanced Agent Capabilities, Multi-Tasking, Advanced UITL)

### NICE TO HAVE (Valuable additions for future iterations):

1.  **Advanced Agent Reasoning & Self-Correction (Full).**
2.  **Comprehensive Tool Ecosystem Expansion (Leveraging new "Plug and Play" system):**
    * **Next New Tool Candidate:** **Rscript Execution Tool** (to be developed using the new plug-and-play architecture).
    * Further tools for literature review, data analysis/visualization, specialized bioinformatics tasks, document preparation.
3.  **UI/UX & Workspace Enhancements** (Integrated Folder Viewer, Dedicated Steps Panel, etc.).
4.  **Backend & Architecture** (Scalability, Personas).
5.  **Deployment & DevOps.**

## Known Good States / Checkpoints

-   **"Plug and Play" Tool System:** Core architecture implemented and stable. All 9 tools dynamically loaded via `tool_config.json` and operational.
-   **Pydantic v2 Migration:** Progress made on several key Pydantic models.
-   Token Counting: Working.
-   File Upload: Functional.
-   In-Chat Tool Feedback & Plan Proposal UI: Complete and refined.

## Open Questions / Areas for Investigation / Architectural Considerations

-   Robustness of `asyncio.Task.cancel()` for deep LLM/tool calls (STOP button issue).
-   Best practices for `JsonOutputParser` when `pydantic_object` is specified (why it sometimes returns `dict` vs. model instance, though handled now).
-   **Finalizing Pydantic v2 Migration:** Ensuring all custom models are migrated and potential interactions with LangChain base classes are smooth.
-   **New Tool Integration Process:** Documenting and streamlining the process for adding new tools now that the foundation is laid.
