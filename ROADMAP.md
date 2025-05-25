ResearchAgent: Project Roadmap (v2.5 Base)
==========================================

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

Guiding Principles for Development
----------------------------------

-   Accuracy & Reliability Over Speed: Prioritize robust and correct execution of tasks, even if it means more granular planning or slightly longer execution times.

-   User-in-the-Loop (UITL/HITL): Empower the researcher with control and the ability to guide the agent.

-   Modularity & Maintainability: Continue to build and refine the codebase with clear separation of concerns.

-   Extensibility: Design the system to easily accommodate new tools, LLMs, and agent capabilities.

Phase 1: Core Stability & Foundational Tools (Largely Completed - Basis of v2.4/v2.5)
-------------------------------------------------------------------------------------

-   UI Framework: Three-panel layout (Tasks, Chat, Monitor/Artifacts).

-   Backend Infrastructure: Python, WebSockets, HTTP file server.

-   Task Management: Creation, selection, deletion, renaming, persistent storage.

-   Basic Agent Flow: Intent Classification, P-C-E-E pipeline (Planner, Controller, Executor, Evaluator).

-   Core Tools: Web search (Tavily, DuckDuckGo), file I/O, PubMed search, basic web page reader.

-   `DeepResearchTool` v1: Functional multi-phase deep research capability.

-   LLM Configuration: Support for Gemini & Ollama, role-specific LLM assignments.

-   Frontend Refactoring (v2.5): Modularized JavaScript for improved UI code management.

Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus)
----------------------------------------------------------------------------------

1.  Advanced Step Self-Correction (High Priority)

    -   Goal: Improve autonomous error recovery.

    -   Details: Enable the Step Evaluator to not only identify failures but also to propose revised step descriptions or parameters for a more effective retry. This involves updating prompts and Pydantic models for the Evaluator and modifying `message_handlers.py` to use these revisions.

    -   Status: Design phase / Initial implementation considerations.

2.  User-in-the-Loop (UITL/HITL) - Foundational (High Priority)

    -   Goal: Introduce agent-initiated interaction points during plan execution.

    -   Details:

        -   Planner: Generate special "interaction steps" (e.g., asking user to select from a list, confirm a summary, provide input).

        -   Backend: Pause plan execution, send interaction requests to UI, process user responses.

        -   UI: Render interaction prompts and capture user input.

    -   Status: Design phase.

3.  Improved "No Tool" Step Reliability & Granularity (Ongoing)

    -   Goal: Ensure the Executor LLM can reliably perform generation, summarization, and formatting tasks without tool errors.

    -   Details: Continue refining Planner prompts to break down complex "No Tool" tasks. Monitor ReAct agent behavior for `_Exception` calls and refine prompts or agent architecture as needed.

    -   Status: Ongoing refinement.

4.  UI/UX Refinements for Clarity & Control

    -   Goal: Make agent operations more transparent and user-friendly.

    -   Details:

        -   Better visualization of the active plan and current step (building on artifact viewer for `_plan.md`).

        -   Improved artifact viewer (file/folder structure, enhanced PDF view).

        -   Consider UI elements for the upcoming UITL features.

    -   Status: Ongoing, iterative improvements.

Phase 3: Advanced Interactivity & Tooling (Mid-Term)
----------------------------------------------------

1.  User-in-the-Loop (UITL/HITL) - Advanced Plan Modification

    -   Goal: Allow users to review and request modifications to an *upcoming* plan before or during execution.

    -   Details: UI to display upcoming steps, interface for edit requests (modify, reorder, add, delete), backend logic to validate and apply plan changes.

    -   Status: Future development post-foundational UITL.

2.  New Granular Tool Development

    -   Goal: Enhance agent precision and offload specific tasks from general LLM steps.

    -   Wishlist (to be prioritized & designed):

        -   `list_files_tool`: Safer listing of workspace files.

        -   `download_files_tool`: Download files from URLs to workspace.

        -   `extract_text_segment_tool`: LLM-driven extraction from larger texts.

        -   `format_data_tool`: Deterministic or focused LLM for simple data conversions (e.g., JSON to Markdown table).

        -   `structured_data_query_tool`: Query structured data (CSV, JSON) in files.

        -   `summarize_text_tool`: Dedicated summarization with more control.

    -   Status: Ideation.

3.  Workspace Document Indexing & RAG (Retrieval Augmented Generation)

    -   Goal: Enable the agent to "read" and search across all documents within the current task's workspace.

    -   Details:

        -   `ingest_workspace_documents_tool`: Chunk, embed, and index workspace files.

        -   `search_indexed_workspace_tool`: Perform semantic search over indexed documents.

    -   Status: Longer-term research and integration.

Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
-------------------------------------------------------------------------

1.  Advanced Re-planning & Meta-Cognition

    -   Goal: Enable the agent to re-evaluate its overall plan based on holistic evaluation and potentially regenerate the entire plan if the current approach is failing.

    -   Status: Research.

2.  Permission Gateway for Sensitive Tools

    -   Goal: Add a confirmation step before executing potentially risky tools (`workspace_shell`, `python_package_installer`).

    -   Status: Future enhancement.

3.  Streaming Output for LLM Responses

    -   Goal: Improve perceived responsiveness by streaming LLM outputs to the UI.

    -   Status: Future enhancement.

4.  Specialized Agent Personas/Workflows

    -   Goal: Explore pre-configured agent setups optimized for specific research sub-domains (e.g., genomic data analysis, literature review synthesis).

    -   Status: Exploration.

This roadmap will guide our development efforts. Feedback and adjustments are welcome as the project progresses.