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
-   **Architectural Refactor: "Plug and Play" Tool System (Core Implemented):**
    -   Implemented dynamic tool loading via `tool_config.json` and `tool_loader.py`.
    -   Migrated all 6 general-purpose tools to individual class-based scripts loadable via config.
    -   Integrated task-specific file tools (`read_file`, `write_file`, `workspace_shell`) into the dynamic loading mechanism with runtime context injection.
    -   Established a scalable foundation for future tool development.

## Phase 2: V1.0 Go-Live (Target: Within 2 Months - MUST HAVE Focus)

This phase focuses on delivering a stable, reliable, and core-efficient ResearchAgent.

1.  **CRITICAL (MUST HAVE) - BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button:**
    -   Ensure agent tasks are reliably cancelled when intended (e.g., via STOP button, or context switch).
    -   Make STOP button fully functional. Address issues with `asyncio.Task.cancel()` not reliably interrupting (exploring `asyncio.Event`).
2.  **HIGH (MUST HAVE) - BUG - ARTIFACT VIEWER REFRESH:**
    -   Ensure reliable auto-update of the artifact viewer after file writes.
3.  **HIGH (MUST HAVE) - AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    -   Improve Evaluator to accurately check if actual content was produced vs. a description.
    -   Ensure the retry mechanism (`agent_max_step_retries`) effectively uses evaluator feedback for simple retries, especially for "No Tool" steps needing direct LLM content output.
4.  **HIGH (MUST HAVE) - DEV OPS / STABILITY - Comprehensive Testing (Core Functionality):**
    -   Implement/expand unit and integration tests for critical backend (task cancellation, agent lifecycle, core tools including dynamically loaded ones) and frontend components.

## Phase 3: V1.x Enhancements (Post Go-Live - SHOULD HAVE Focus)

This phase aims to enhance the agent's capabilities, user control, and overall experience, building upon the new tool architecture.

1.  **"Plug and Play" Tool System Refinements:**
    -   **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas (leveraging Pydantic `args_schema` from tool classes) for more robust validation and to aid agent understanding.
    -   **Develop New Tool Integration Guide:** Create comprehensive documentation and templates for adding new tools to the system, detailing the `tool_config.json` structure, `BaseTool` class requirements, and best practices.
2.  **Enhanced Agent Capabilities & Efficiency:**
    -   **Improved Agent Memory / Workspace RAG (Basic):** Basic retrieval from current task workspace files.
    -   **Streaming LLM Responses (Final Answers):** Token-by-token streaming for agent's final answers.
    -   **Refined Error Parsing & Reporting:** Improve agent's understanding and reporting of errors.
    -   **Robust Asynchronous Task Cancellation (Advanced):** Explore advanced `asyncio` patterns (`asyncio.Event`, `asyncio.shield`).
3.  **Multi-Tasking & User Control:**
    -   **Asynchronous Background Task Processing (Basic Stop/Switch):** Ensure reliable stop/cleanup of previous task on UI switch. Global chat input disabling if any task is active.
    -   **Optional Tools (e.g., Web Search):** Allow users to enable/disable tools (via `tool_config.json` `enabled` flag or UI) for privacy/cost. Backend to respect choices, UI to communicate impact.
4.  **UI/UX:**
    -   **Finalize "View \[artifact\] in Artifacts" Links:** Complete functionality for links from tool output messages to the artifact viewer.
5.  **Advanced User-in-the-Loop (UITL/HITL) Capabilities:**
    -   Introduce more sophisticated mechanisms for users to intervene, guide, or correct the agent.

## Phase 4: Future Iterations (NICE TO HAVE Focus)

This phase will focus on adding more advanced features, expanding the tool ecosystem using the new plug-and-play system, and further polishing the UI/UX.

1.  **Advanced Agent Reasoning & Self-Correction (Full):**
    -   Meta-Cognitive Loop, Self-Debugging/Rewriting, Dynamic Plan Adjustment, Learning from Failure.
2.  **Comprehensive Tool Ecosystem Expansion (Leveraging "Plug and Play"):**
    -   **Rscript Execution Tool:** Develop and integrate as a new plug-and-play tool.
    -   **Enhanced PDF Parsing:** More structured PDF content extraction (if current `read_file` proves insufficient).
    -   Tools for advanced literature review (NER, Relation Extraction), data analysis/visualization, specialized bioinformatics tasks (BLAST, etc.), document preparation (Pandoc).
3.  **UI/UX & Workspace Enhancements:**
    -   **Global "Agent Thinking Status" Line Review.**
    -   **Agent Step Announcement Styling.**
    -   **Copy Button Centering Bug Fix.**
    -   **Monitor Log Color-Coding.**
    -   **Integrated Folder Viewer.**
    -   **Dedicated "Agent Activity/Steps" Panel.**
    -   **Further Chat Information Management.**
    -   Direct artifact manipulation from UI.
    -   **UI for Tool Status (Traffic Lights):** Display configured tools and their load status.
4.  **Backend/Debug (Low Priority):**
    -   **Plan File Status Update Warnings.**
    -   **"Unknown" History Message Types Review.**
5.  **Backend & Architecture:**
    -   Scalability improvements.
    -   Specialized Agent Personas/Configurations.
    -   **Pydantic v2 Migration:** Fully migrate codebase to Pydantic v2, addressing all LangChain deprecation warnings.
6.  **Deployment & DevOps:**
    -   Broader local/cloud deployment options.
    -   Mature CI/CD pipeline.

## Phase 5: Advanced Agent Autonomy & Specialized Applications (Longer-Term)

_(This phase remains for very long-term goals, largely similar to original document)_

-   Enhanced Agent Self-Correction & Re-planning (beyond Phase 4).
-   Long-Term Cross-Task Memory.
-   Optimize for handling multiple concurrent users/sessions more effectively.
-   Explore robust cloud deployment options and strategies.
-   More specialized agent personas/configurations.

## Completed Milestones (Summary up to current state)

-   **v2.0-v2.4 (approx):** Initial architecture, core agent loop (PCEE), basic UI (3-panel), SQLite history, foundational tool integration (search, file I/O, PubMed, Python REPL, Shell), modular JS frontend, initial UI enhancements (Markdown rendering, plan confirmation flow).
-   **v2.5.0 - v2.5.2 (approx):** Significant UI/UX improvements (collapsible steps, agent avatars, improved font sizes, LLM selector styling, dark theme refinements), fixes for `read_file` tool output, implementation of Token Counter, File Upload, and enhanced In-Chat Tool Feedback.
-   **v2.5.3 (Current Focus - In Progress):**
    -   **"Plug and Play" Tool System Refactor (Core Implemented):** Successfully refactored general-purpose and task-specific tools to be dynamically loadable via `tool_config.json` and `tool_loader.py`.
    -   Ongoing: Critical bug fixes (Agent Task Cancellation, Artifact Viewer Refresh), Agent Capability enhancements (Step Evaluation/Retry), and comprehensive testing.

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses.
