# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - Critical Fixes & Enhancements In Progress)



This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Targeting Version 2.5.3 (Focus on Critical Fixes, Core Functionality, and Initial Enhancements).**

**Recent Developments (Leading to current state):**

-   **Architectural Refactor: "Plug and Play" Tool System (Complete & Stable):**
    -   Successfully refactored the tool management system.
    -   General-purpose tools (web search, web page reading, package installation, PubMed search, Python REPL, deep research synthesis) are defined in individual Python scripts (`backend/tools/your_tool_name_tool.py`).
    -   Tools are dynamically loaded at startup based on a central JSON configuration file (`backend/tool_config.json`).
    -   Task-specific tools (file system operations: `read_file`, `write_file`, `workspace_shell`) are also now fully loaded via `tool_config.json`, with runtime injection of `task_workspace` handled by `tool_loader.py`.
    -   This new architecture streamlines the integration of new tools and improves system maintainability.
    -   All 9 tools (6 general-purpose + 3 task-specific) are confirmed to be loading correctly (pending full verification of `deep_research_synthesizer` after Pydantic fix) and are available to the agent.
-   **Pydantic v2 Migration (Largely Complete):**
    -   Migration from Pydantic v1 (via `langchain_core.pydantic_v1`) to Pydantic v2 for most data models is complete.
    -   This includes Tool Argument Schemas (e.g., `WebPageReaderInput`, `TavilySearchInput`) and LLM Output Schemas (e.g., `IntentClassificationOutput`, `AgentPlan`, `ControllerOutput`).
    -   The `TypeError` in `backend/tools/deep_research_tool.py` for `CuratedSourcesOutput`'s `field_validator` has been addressed for Pydantic v2 compatibility.
-   **Core Agent Logic & Prompting (Improved):**
    -   ReAct agent prompt in `backend/agent.py` updated to enhance the reliability of direct content generation for final answers, reducing instances of the agent describing its output instead of providing it.
    -   Controller logic and parsing for Pydantic v2 models refined.
-   **Chat UI/UX Refinement (Significant Progress - features as previously listed in `prompt.txt`):**
    -   Visual Design & Readability: Improved message alignment, consistent sub-step indentation, increased general and token area font sizes, HTML tag rendering.
    -   Interactivity & Layout: Collapsible major agent steps and tool outputs (via label click). Adjusted message bubble widths. Agent Avatar for final RA messages. Role LLM selectors styled with color indicators.
    -   Persistence & Consistency: Ensured correct rendering and visual consistency for persisted (reloaded) confirmed plans.
    -   Functionality Fixes: `read_file` tool output displays correctly and is nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat now working. Final synthesized answer from agent correctly displayed (improved with recent ReAct prompt fix).
    -   Completed Features: Token Counter, File Upload, core In-Chat Tool Feedback, Plan Proposal UI & Persistence.
-   **History Handling:**
    -   Resolved "Unknown history message type" warning for `monitor_user_input` by adding it to the recognized internal types for monitor replay in `backend/message_processing/task_handlers.py`.
**Known Issues & Immediate Next Steps (Priorities & Estimates):**

**Critical Fixes & Core Functionality (v2.5.3 / V1.0 Go-Live Focus):**

1.  **Agent Task Cancellation & STOP Button (Critical):**
    -   **Issue:** Switching UI tasks or using STOP button does not reliably cancel/stop active agent processing. Status updates can bleed.
    -   **Goal:** Implement robust `asyncio.Task` cancellation. Ensure STOP button and task switching reliably terminate agent processing.
    -   **Effort:** ~7/10
    -   **Time Est.:** ~9-12 hours
2.  **BUG: ARTIFACT VIEWER REFRESH (High):**
    -   **Issue:** Artifact viewer doesn't consistently or immediately auto-update after file writes mid-plan.
    -   **Goal:** Ensure reliable and immediate auto-update.
    -   **Effort:** ~4/10
    -   **Time Est.:** ~4-6 hours
3.  **AGENT CAPABILITIES: Robust Step Evaluation & Basic Retry (High):**
    -   **Issue:** Evaluator needs to reliably assess step success (content vs. description). Retry mechanism should effectively use this feedback.
    -   **Goal:** Ensure PCEE loop's Evaluator is robust and retry mechanism is effective.
    -   **Effort:** ~7/10
    -   **Time Est.:** ~8-12 hours
4.  **DEV OPS / STABILITY: Comprehensive Testing (High):**
    -   **Goal:** Expand unit and integration tests for critical backend and frontend components.
    -   **Effort:** ~6/10 (Initial batch)
    -   **Time Est.:** ~10-15 hours (Initial batch)

Enhancements & UI Polish (Post-Critical):

5\. Make Tavily Search Optional (Medium):

\* Goal: Add config option to disable Tavily search for privacy, with user notification.

\* Effort: ~5/10

\* Time Est.: ~3-5 hours

6\. UI/UX: Finalize "View \[artifact\] in Artifacts" Links (Medium):

\* Goal: Implement full functionality for chat links to open/highlight artifacts.

\* Effort: ~3/10

\* Time Est.: ~2-3 hours

7\. "Plug and Play" Tool System Enhancements (Medium):

\* Formalize Tool Input/Output Schemas: (Effort: ~5/10, Time: ~4-6h)

\* Develop New Tool Integration Guide: (Effort: ~4/10, Time: ~3-5h)

8\. UI/UX: Artifact Viewer - Folder Link/View (Simple Version) (Medium):

\* Goal: Provide links to task workspace folders or simple content list.

\* Effort: ~2/10

\* Time Est.: ~2-3 hours

**Low Priority Bugs & Polish:**

-   **UI BUG: Copy button placement for simple messages:** (Effort: 2, Time: 1-2h)
-   **UI/UX POLISH: Global "agent-thinking-status" line behavior:** (Effort: 2, Time: 1-2h)
-   **UI/UX POLISH: Styling for agent step announcements:** (Effort: 2, Time: 1-2h)
-   **WARNING: PLAN FILE STATUS UPDATE:** Fix warnings about step patterns. (Effort: 3, Time: 2h)
-   **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES:** Confirm handling. (Effort: 1, Time: 1h)
-   **DEBUG: Monitor Log Color-Coding:** Verify CSS. (Effort: 1, Time: 1h)
**Future Considerations & Enhancements (Post V1.0 Go-Live):**

-   **Enhanced Agent Capabilities & Efficiency:**
    -   Improved Agent Memory / Workspace RAG (Basic).
    -   Streaming LLM Responses (Final Answers).
    -   Refined Error Parsing & Reporting.
-   **Multi-Tasking & User Control:**
    -   Asynchronous Background Task Processing (Basic Stop/Switch).
    -   Optional Tools (via `tool_config.json` `enabled` flag or UI).
-   **Advanced User-in-the-Loop (UITL/HITL) Capabilities.**
-   **Advanced Agent Reasoning & Self-Correction.**
-   **Comprehensive Tool Ecosystem Expansion (Leveraging "Plug and Play" system):**
    -   **Rscript Execution Tool:** (Effort: ~6/10, Time Est.: ~8-12h)
    -   **Data\_Comparator:** Comparing datasets/files. (Effort: ~5/10, Time Est.: ~6-10h)
    -   **Data\_Compiler:** Aggregating data. (Effort: ~6/10, Time Est.: ~8-12h)
    -   **Data\_Filter:** Complex filtering on structured data. (Effort: ~5/10, Time Est.: ~6-10h)
    -   **Data\_Formatter:** Converting data formats. (Effort: ~4/10, Time Est.: ~4-8h)
    -   **Domain\_Analysis (e.g., InterProScan wrapper):** (Effort: ~7/10, Time Est.: ~10-15h)
    -   **Information\_Extractor (schema-based):** (Effort: ~7/10, Time Est.: ~10-15h)
    -   **Keyword\_Extractor:** (Effort: ~4/10, Time Est.: ~4-6h)
    -   **Knowledge\_Lookup (scientific entities, protocols):** (Effort: ~6/10, Time Est.: ~8-12h)
    -   **Report\_Generator (general, structured):** (Effort: ~8/10, Time Est.: ~12-20h)
    -   **Sequence\_Search (e.g., BLAST wrapper):** (Effort: ~7/10, Time Est.: ~10-15h)
    -   **Specialized\_DB\_Search (ClinVar, dbSNP, KEGG, GenBank, etc.):** (Effort: ~7/10 per DB, Time Est.: ~10-15h per DB)
    -   **Text\_Summarizer (standalone):** (Effort: ~4/10, Time Est.: ~4-8h)
    -   **Text\_Synthesizer (standalone):** (Effort: ~5/10, Time Est.: ~6-10h)
    -   Enhanced PDF Parsing.
-   **UI/UX & Workspace Enhancements (Integrated Folder Viewer, Dedicated Steps Panel, etc.).**
-   **Backend & Architecture (Scalability, Personas).**
-   **Deployment & DevOps.**

## Core Architecture & Workflow

The ResearchAgent employs a sophisticated backend architecture centered around a modified Plan-Code-Execute-Evaluate (PCEE) loop, inspired by self-correcting LLM agent paradigms.

1.  **User Input & Task Context:** The user interacts via a chat interface, defining tasks. Each task has an isolated workspace on the server.
2.  **Intent Classification:** User queries are first classified to determine if they require a multi-step plan ("PLAN") or can be handled by a direct question-answering mechanism/single tool use ("DIRECT\_QA").
3.  **Planning (for "PLAN" intent):**
    -   An LLM (Planner) receives the user query and a summary of available tools.
    -   It generates a multi-step plan, outputting a human-readable summary and a structured list of `PlanStep` objects (Pydantic models). Each step details its description, suggested tool (or "None"), input instructions, and expected outcome.
    -   The plan includes a final "synthesis" step to consolidate results for the user.
4.  **Plan Proposal & Confirmation:** The plan summary and steps are presented to the user in the UI for review and confirmation.
5.  **Execution Loop (PCEE - upon plan confirmation):**
    -   For each step in the confirmed plan:
        -   **Controller:** An LLM (Controller) analyzes the current step's description, expected outcome, planner's tool suggestion, available tools, and (crucially) the output from the _previous_ step. It then decides the precise `tool_name` (can override planner) and formulates the exact `tool_input` string. For "None" tool steps, it formulates a directive for the Executor LLM.
        -   **Executor (ReAct Agent):** A ReAct-style agent (using another LLM) receives the Controller's decision (tool name and input, or directive for "None" tool steps).
            -   If a tool is specified, the Executor forms a thought, invokes the tool with the provided input, and receives an observation (tool output).
            -   If `tool_name` is "None", the Executor LLM directly generates the content or performs the reasoning required by the Controller's `tool_input` directive to meet the step's `expected_outcome`.
            -   The Executor's final output for the step is captured.
        -   **Step Evaluator:** An LLM (Step Evaluator) assesses if the Executor's output successfully achieved the `current_step_expected_outcome`.
            -   If successful, the plan proceeds to the next step.
            -   If failed but recoverable, it can suggest `updated_tool_name`, `updated_tool_input`, and `feedback_to_executor` for a retry (currently `agent_max_step_retries` configured in `config.py`). The Controller then uses this feedback for the retry attempt.
            -   If failed and not recoverable, the plan execution stops.
    -   **Loop Continuation:** The process repeats for all steps until the plan is complete, fails, or is cancelled.
6.  **Overall Plan Evaluation:** After the plan execution loop finishes (completes, fails, or is cancelled), an LLM (Overall Plan Evaluator) assesses the overall success in addressing the original user query based on the final outputs and the plan's intent.
7.  **Output to User:** The final synthesized answer (if generated by the plan's last step and deemed appropriate by the Overall Plan Evaluator) or the overall evaluation assessment is presented to the user.
**Key Backend Components:**

-   `server.py`: Manages WebSocket connections, task contexts, and orchestrates message handling.
-   `message_handlers.py`: Routes incoming WebSocket messages to appropriate processing functions.
-   `message_processing/`: Contains sub-modules for handling different types of messages and agent flows.
    -   `agent_flow_handlers.py`: Manages the PCEE loop, intent classification, and planning.
    -   `task_handlers.py`: Handles task creation, switching, deletion, renaming.
    -   `config_handlers.py`: Manages LLM configuration settings.
    -   `operational_handlers.py`: Handles commands like artifact refresh, direct shell execution.
-   `llm_setup.py`: Centralized LLM instance creation and management.
-   `tool_config.json` & `tool_loader.py`: Defines and loads all tools dynamically.
-   `tools/`: Directory containing individual tool scripts and `standard_tools.py` (which includes task-specific tool classes and helper functions).
-   `planner.py`, `controller.py`, `evaluator.py`, `intent_classifier.py`: Define the logic and Pydantic models for each agent component.
-   `agent.py`: Creates the LangChain ReAct agent executor.
-   `callbacks.py`: Handles WebSocket communication for agent streaming, token usage, and DB logging.
-   `db_utils.py`: Manages SQLite database interactions for task and message history.
-   `config.py`: Application settings.

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Create, delete, rename, switch context.
    -   Chat Interface: Markdown rendering, collapsible agent steps/tool outputs, in-chat feedback for tool usage, copy-to-clipboard, agent avatars, visual cues for message sources, dynamic message bubble widths, persistent chat history per task.
    -   Plan Confirmation: UI for users to review and confirm/reject proposed plans.
    -   LLM Configuration: UI for selecting LLM provider/model for different agent roles (Intent, Planner, Controller, Executor, Evaluator) per session.
    -   Monitor Panel: Displays system logs, LLM interactions, and token usage.
    -   Artifact Viewer: Lists and allows viewing of files in the current task's workspace (auto-refresh on some events, with improvements pending).
    -   Token Usage Tracking: Detailed breakdown by LLM role, updated in real-time.
    -   File Upload: Ability to upload files to the current task's workspace.
2.  **Backend Architecture & Logic:**
    -   Python server with WebSockets (`websockets`) and `aiohttp` (for file server).
    -   Powered by LangChain, supporting multiple LLM providers (Gemini, Ollama).
    -   Persistent task and message history via SQLite.
    -   Modular message handling and agent component design.
    -   **"Plug and Play" Tool System:** All tools (general-purpose and task-specific) are defined in `tool_config.json` and loaded dynamically by `tool_loader.py`. Individual Python scripts for most tools promote modularity.
    -   Task-Specific Workspaces: Isolated file system storage for each task.
    -   Structured Agent Flow (PCEE Loop):
        -   Intent Classification (PLAN vs. DIRECT\_QA).
        -   Planner LLM for generating multi-step plans.
        -   Controller LLM for selecting tools and formulating exact inputs for each step, using previous step's output as context.
        -   Executor (ReAct Agent) for executing tool actions or generating direct LLM responses for "No Tool" steps.
        -   Step Evaluator LLM for assessing success of each step and suggesting corrections for retries.
        -   Overall Plan Evaluator LLM for final assessment of goal achievement.
    -   Real-time Callbacks: For streaming thoughts, tool usage, status updates, and errors to the UI.
    -   Token Usage Tracking: Detailed accounting for each LLM call.
    -   Basic Agent Memory: `ConversationBufferWindowMemory` used by the Executor.
    -   Pydantic v2 Migration: Largely complete for data models for validation and LLM output structuring.

## Tech Stack

-   **Backend:** Python, LangChain, WebSockets (`websockets` library), `aiohttp` (for file server), SQLite.
-   **LLM Support:** Google Gemini, Ollama (via LangChain integrations).
-   **Frontend:** HTML, CSS, JavaScript (Modular).
-   **Containerization:** Docker, Docker Compose.

## Project Structure

(Reflects new tool files, configuration, and ongoing Pydantic v2 migration)

ResearchAgent/

├── .env # Environment variables (GITIGNORED)

├── .env.example # Example environment variables

├── .gitignore

├── backend/

│ ├── init.py

│ ├── agent.py # Creates ReAct agent executor

│ ├── callbacks.py # WebSocket and DB logging callbacks, AgentCancelledException

│ ├── config.py # Application settings

│ ├── controller.py # Controller LLM logic, ControllerOutput Pydantic model (migrated to v2)

│ ├── db\_utils.py # SQLite utilities

│ ├── evaluator.py # Evaluator LLM logic, EvaluationResult/StepCorrection Pydantic models (migrated to v2)

│ ├── intent\_classifier.py # Intent Classifier LLM logic, IntentClassificationOutput Pydantic model (migrated to v2)

│ ├── llm\_setup.py # Centralized LLM instantiation

│ ├── message\_handlers.py # Main router for WebSocket messages

│ ├── message\_processing/ # Sub-package for message processing modules

│ │ ├── init.py

│ │ ├── agent\_flow\_handlers.py # Orchestrates PCEE loop, planning, direct QA

│ │ ├── config\_handlers.py # Handles LLM config messages

│ │ ├── operational\_handlers.py# Handles non-agent operational messages

│ │ └── task\_handlers.py # Handles task CRUD, context switching

│ ├── planner.py # Planner LLM logic, AgentPlan/PlanStep Pydantic models (migrated to v2)

│ ├── server.py # Main WebSocket server and aiohttp file server

│ ├── tool\_config.json # Central configuration for dynamic tool loading

│ ├── tool\_loader.py # Module for loading tools from tool\_config.json, includes workspace utils

│ └── tools/

│ ├── init.py

│ ├── standard\_tools.py # ReadFileTool, WriteFileTool, TaskWorkspaceShellTool classes, helper functions

│ ├── tavily\_search\_tool.py # TavilyAPISearchTool class & TavilySearchInput (migrated to v2)

│ ├── web\_page\_reader\_tool.py# WebPageReaderTool class & WebPageReaderInput (migrated to v2)

│ ├── python\_package\_installer\_tool.py # PythonPackageInstallerTool & Input (migrated to v2)

│ ├── pubmed\_search\_tool.py # PubMedSearchTool & PubMedSearchInput (migrated to v2)

│ ├── python\_repl\_tool.py # PythonREPLTool & PythonREPLInput (migrated to v2)

│ └── deep\_research\_tool.py # DeepResearchTool & DeepResearchToolInput (Input migrated, internal models updated for v2)

├── css/

│ └── style.css # Main stylesheet

├── js/

│ ├── script.js # Main frontend orchestrator

│ ├── state\_manager.js # Manages UI and application state

│ └── ui\_modules/ # Modular UI components

│ ├── artifact\_ui.js

│ ├── chat\_ui.js

│ ├── file\_upload\_ui.js

│ ├── llm\_selector\_ui.js

│ ├── monitor\_ui.js

│ ├── task\_ui.js

│ └── token\_usage\_ui.js

├── BRAINSTORM.md

├── Dockerfile

├── docker-compose.yml

├── index.html

├── README.md # This project overview

├── ROADMAP.md

├── UI\_UX\_style.md # UI/UX refinement notes

└── simulation\_option6.html # UI simulation/sandbox (archival)

## Setup & Installation

1.  **Clone the repository.**
2.  **Configure environment variables:** Copy `.env.example` to `.env` and fill in API keys (GOOGLE\_API\_KEY, TAVILY\_API\_KEY, ENTREZ\_EMAIL) and any other necessary settings.
3.  **Build and run with Docker Compose:** `docker compose up --build`
4.  **Access:** UI at `http://localhost:8000`.

## Security Warnings

-   Ensure API keys in `.env` are kept secure and not committed to public repositories.
-   Tools like `python_package_installer` and `workspace_shell` execute commands/code in the backend environment; use with caution and be aware of the security implications, especially if exposing the agent to untrusted inputs.
-   Review dependencies for vulnerabilities regularly.

## Contributing

(Contributions are welcome! Please discuss significant changes via issues first. Standard PR practices apply.)

## License

(To be specified - MIT License is a common choice for open-source projects.)
