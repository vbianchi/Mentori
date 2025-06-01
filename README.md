# ResearchAgent: AI Assistant for Research Workflows (v2.5.4 - Tool System Refactor & Pydantic v2 Migration Started)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Targeting Version 2.5.4 (Post-initial "Plug and Play" Tool Refactor, Pydantic v2 migration in progress).**

**Recent Developments (Leading to current state):**

-   **Architectural Refactor: "Plug and Play" Tool System (Complete & Stable):**
    * Successfully refactored the tool management system.
    * General-purpose tools (web search, web page reading, package installation, PubMed search, Python REPL, deep research synthesis) are defined in individual Python scripts (`backend/tools/your_tool_name_tool.py`).
    * Tools are dynamically loaded at startup based on a central JSON configuration file (`backend/tool_config.json`).
    * Task-specific tools (file system operations: `read_file`, `write_file`, `workspace_shell`) are also now fully loaded via `tool_config.json`, with runtime injection of `task_workspace` handled by `tool_loader.py`.
    * This new architecture streamlines the integration of new tools and improves system maintainability.
    * All 9 tools (6 general-purpose + 3 task-specific) are confirmed to be loading correctly and are fully available to the agent.
-   **Pydantic v2 Migration (In Progress):**
    * Initiated migration from Pydantic v1 (via `langchain_core.pydantic_v1`) to Pydantic v2 for improved performance and future-proofing.
    * **Completed for:**
        * `WebPageReaderInput` (`web_page_reader_tool.py`)
        * `PubMedSearchInput` (`pubmed_search_tool.py`)
        * `IntentClassificationOutput` (`intent_classifier.py`)
        * `TavilySearchInput` (and associated field name fixes in `TavilyAPISearchTool` within `tavily_search_tool.py`)
        * `PythonPackageInstallerInput` (`python_package_installer_tool.py`)
        * `PythonREPLInput` (`python_repl_tool.py`)
        * `PlanStep`, `AgentPlan` (`planner.py`)
        * `ControllerOutput` (and associated parsing logic fixes in `controller.py`)
    * **Remaining:** Models in `evaluator.py` and internal models in `deep_research_tool.py`.
-   **Core Bug Fixes & Feature Verification (Ongoing).**
-   **Chat UI/UX Refinement (Significant Progress - features as previously listed in `prompt.txt`):**
    * Visual Design & Readability: Improved message alignment, consistent sub-step indentation, increased general and token area font sizes, HTML tag rendering.
    * Interactivity & Layout: Collapsible major agent steps and tool outputs (via label click). Adjusted message bubble widths. Agent Avatar for final RA messages. Blue line removed from RA/Plan messages. Role LLM selectors styled with color indicators.
    * Persistence & Consistency: Ensured correct rendering and visual consistency for persisted (reloaded) confirmed plans.
    * Functionality Fixes: `read_file` tool output displays correctly and is nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat now working. Final synthesized answer from agent correctly displayed.
    * Completed Features: Token Counter, File Upload, core In-Chat Tool Feedback, Plan Proposal UI & Persistence.

**Known Issues & Immediate Next Steps (Priorities adjusted):**

-   **CRITICAL (MUST HAVE): BUG & RE-ENGINEERING: Agent Task Cancellation & STOP Button:**
    * Current behavior: Switching UI tasks or using the STOP button does not reliably cancel/stop the agent processing the current task. Status updates from a backgrounded task can bleed into a newly selected task's view. The STOP button is not fully functional.
    * **Goal:** Implement robust agent task cancellation. Ensure the STOP button reliably terminates the actively processing agent task. Solidify cancellation logic when switching UI task context.
-   **HIGH (MUST HAVE): BUG: ARTIFACT VIEWER REFRESH:**
    * Artifact viewer does not consistently or immediately auto-update after file writes mid-plan.
-   **HIGH (MUST HAVE): AGENT CAPABILITIES: Robust Step Evaluation & Basic Retry:**
    * Ensure the PCEE loop's Evaluator component reliably assesses step success.
    * Ensure the retry mechanism effectively uses evaluator feedback.
-   **HIGH (MUST HAVE): DEV OPS / STABILITY: Comprehensive Testing:**
    * Expand unit and integration tests for critical backend and frontend components.
-   **MEDIUM (SHOULD HAVE): Complete Pydantic v2 Migration:**
    * Migrate remaining Pydantic models in `evaluator.py` (`StepCorrectionOutcome`, `EvaluationResult`) and internal models within `deep_research_tool.py` to Pydantic v2.
-   **MEDIUM (SHOULD HAVE): "Plug and Play" Tool System Enhancements (Post Pydantic v2 Migration):**
    * **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas.
    * **Develop New Tool Integration Guide:** Create documentation and templates for adding new tools.
-   **MEDIUM (SHOULD HAVE): UI/UX: Finalize "View [artifact] in Artifacts" Links.**
-   **LOW (NICE TO HAVE) UI/UX POLISH & DEBUGGING (as previously listed).**

**Future Considerations & Enhancements (Post V1.0 Go-Live):**
(This section remains largely the same as the previous full version, outlining longer-term goals for agent capabilities, tool ecosystem expansion, UI/UX, backend architecture, and deployment.)

**SHOULD HAVE (Important for V1.x releases):**
-   Enhanced Agent Capabilities & Efficiency (Memory/RAG, Streaming, Error Parsing, Advanced Cancellation).
-   Multi-Tasking & User Control (Reliable Stop/Switch, Optional Tools via config).
-   Advanced User-in-the-Loop (UITL/HITL) Capabilities.

**NICE TO HAVE (Valuable additions for future iterations):**
-   Advanced Agent Reasoning & Self-Correction.
-   **Comprehensive Tool Ecosystem Expansion (Leveraging new "Plug and Play" system):** Rscript Execution Tool, Enhanced PDF Parsing, more bioinformatics tools, etc.
-   UI/UX & Workspace Enhancements (Folder Viewer, Dedicated Steps Panel, etc.).
-   Backend & Architecture (Scalability, Personas).
-   Deployment & DevOps.

## Core Architecture & Workflow
The ResearchAgent employs a sophisticated backend architecture centered around a modified Plan-Code-Execute-Evaluate (PCEE) loop, inspired by self-correcting LLM agent paradigms.

1.  **User Input & Task Context:** The user interacts via a chat interface, defining tasks. Each task has an isolated workspace on the server.
2.  **Intent Classification:** User queries are first classified to determine if they require a multi-step plan ("PLAN") or can be handled by a direct question-answering mechanism/single tool use ("DIRECT_QA").
3.  **Planning (for "PLAN" intent):**
    * An LLM (Planner) receives the user query and a summary of available tools.
    * It generates a multi-step plan, outputting a human-readable summary and a structured list of `PlanStep` objects (Pydantic models). Each step details its description, suggested tool (or "None"), input instructions, and expected outcome.
    * The plan includes a final "synthesis" step to consolidate results for the user.
4.  **Plan Proposal & Confirmation:** The plan summary and steps are presented to the user in the UI for review and confirmation.
5.  **Execution Loop (PCEE - upon plan confirmation):**
    * For each step in the confirmed plan:
        * **Controller:** An LLM (Controller) analyzes the current step's description, expected outcome, planner's tool suggestion, available tools, and (crucially) the output from the *previous* step. It then decides the precise `tool_name` (can override planner) and formulates the exact `tool_input` string. For "None" tool steps, it formulates a directive for the Executor LLM.
        * **Executor (ReAct Agent):** A ReAct-style agent (using another LLM) receives the Controller's decision (tool name and input, or directive for "None" tool steps).
            * If a tool is specified, the Executor forms a thought, invokes the tool with the provided input, and receives an observation (tool output).
            * If `tool_name` is "None", the Executor LLM directly generates the content or performs the reasoning required by the Controller's `tool_input` directive to meet the step's `expected_outcome`.
            * The Executor's final output for the step is captured.
        * **Step Evaluator:** An LLM (Step Evaluator) assesses if the Executor's output successfully achieved the `current_step_expected_outcome`.
            * If successful, the plan proceeds to the next step.
            * If failed but recoverable, it can suggest `updated_tool_name`, `updated_tool_input`, and `feedback_to_executor` for a retry (currently 1 retry attempt configured). The Controller then uses this feedback for the retry attempt.
            * If failed and not recoverable, the plan execution stops.
    * **Loop Continuation:** The process repeats for all steps until the plan is complete, fails, or is cancelled.
6.  **Overall Plan Evaluation:** After the plan execution loop finishes (completes, fails, or is cancelled), an LLM (Overall Plan Evaluator) assesses the overall success in addressing the original user query based on the final outputs and the plan's intent.
7.  **Output to User:** The final synthesized answer (if generated by the plan's last step) or the overall evaluation assessment is presented to the user.

**Key Backend Components:**
* `server.py`: Manages WebSocket connections, task contexts, and orchestrates message handling.
* `message_handlers.py`: Routes incoming WebSocket messages to appropriate processing functions.
* `message_processing/`: Contains sub-modules for handling different types of messages and agent flows.
    * `agent_flow_handlers.py`: Manages the PCEE loop, intent classification, and planning.
    * `task_handlers.py`: Handles task creation, switching, deletion, renaming.
    * `config_handlers.py`: Manages LLM configuration settings.
    * `operational_handlers.py`: Handles commands like artifact refresh, direct shell execution.
* `llm_setup.py`: Centralized LLM instance creation and management.
* `tool_config.json` & `tool_loader.py`: Defines and loads all tools dynamically.
* `tools/`: Directory containing individual tool scripts and `standard_tools.py` (which includes task-specific tool classes and helper functions).
* `planner.py`, `controller.py`, `evaluator.py`, `intent_classifier.py`: Define the logic and Pydantic models for each agent component.
* `agent.py`: Creates the LangChain ReAct agent executor.
* `callbacks.py`: Handles WebSocket communication for agent streaming, token usage, and DB logging.
* `db_utils.py`: Manages SQLite database interactions for task and message history.
* `config.py`: Application settings.

## Key Current Capabilities & Features
1.  **UI & User Interaction:**
    -   Task Management: Create, delete, rename, switch context.
    -   Chat Interface: Markdown rendering, collapsible agent steps/tool outputs, in-chat feedback for tool usage, copy-to-clipboard, agent avatars, visual cues for message sources, dynamic message bubble widths, persistent chat history per task.
    -   Plan Confirmation: UI for users to review and confirm/reject proposed plans.
    -   LLM Configuration: UI for selecting LLM provider/model for different agent roles (Intent, Planner, Controller, Executor, Evaluator) per session.
    -   Monitor Panel: Displays system logs, LLM interactions, and token usage.
    -   Artifact Viewer: Lists and allows viewing of files in the current task's workspace (auto-refresh on some events).
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
        -   Intent Classification (PLAN vs. DIRECT_QA).
        -   Planner LLM for generating multi-step plans.
        -   Controller LLM for selecting tools and formulating exact inputs for each step, using previous step's output as context.
        -   Executor (ReAct Agent) for executing tool actions or generating direct LLM responses for "No Tool" steps.
        -   Step Evaluator LLM for assessing success of each step and suggesting corrections for retries.
        -   Overall Plan Evaluator LLM for final assessment of goal achievement.
    -   Real-time Callbacks: For streaming thoughts, tool usage, status updates, and errors to the UI.
    -   Token Usage Tracking: Detailed accounting for each LLM call.
    -   Basic Agent Memory: `ConversationBufferWindowMemory` used by the Executor.
    -   Pydantic v2 Migration: In progress for all data models for validation and LLM output structuring.

## Tech Stack
-   **Backend:** Python, LangChain, FastAPI (implicitly via LangChain components or direct use if expanded), WebSockets (`websockets` library), `aiohttp` (for file server), SQLite.
-   **LLM Support:** Google Gemini, Ollama (via LangChain integrations).
-   **Frontend:** HTML, CSS, JavaScript (Modular).
-   **Containerization:** Docker, Docker Compose.

## Project Structure
(Reflects new tool files, configuration, and ongoing Pydantic v2 migration)

ResearchAgent/
├── .env                       # Environment variables (GITIGNORED)
├── .env.example               # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py                 # Creates ReAct agent executor
│   ├── callbacks.py             # WebSocket and DB logging callbacks, AgentCancelledException
│   ├── config.py                # Application settings
│   ├── controller.py            # Controller LLM logic, ControllerOutput Pydantic model (migrated to v2)
│   ├── db_utils.py              # SQLite utilities
│   ├── evaluator.py             # Evaluator LLM logic, EvaluationResult/StepCorrection Pydantic models (target for v2 migration)
│   ├── intent_classifier.py     # Intent Classifier LLM logic, IntentClassificationOutput Pydantic model (migrated to v2)
│   ├── llm_setup.py             # Centralized LLM instantiation
│   ├── message_handlers.py      # Main router for WebSocket messages
│   ├── message_processing/      # Sub-package for message processing modules
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py # Orchestrates PCEE loop, planning, direct QA
│   │   ├── config_handlers.py     # Handles LLM config messages
│   │   ├── operational_handlers.py# Handles non-agent operational messages
│   │   └── task_handlers.py       # Handles task CRUD, context switching
│   ├── planner.py               # Planner LLM logic, AgentPlan/PlanStep Pydantic models (migrated to v2)
│   ├── server.py                # Main WebSocket server and aiohttp file server
│   ├── tool_config.json         # Central configuration for dynamic tool loading
│   ├── tool_loader.py           # Module for loading tools from tool_config.json, includes workspace utils
│   └── tools/
│       ├── __init__.py
│       ├── standard_tools.py      # ReadFileTool, WriteFileTool, TaskWorkspaceShellTool classes, helper functions
│       ├── tavily_search_tool.py  # TavilyAPISearchTool class & TavilySearchInput (migrated to v2)
│       ├── web_page_reader_tool.py# WebPageReaderTool class & WebPageReaderInput (migrated to v2)
│       ├── python_package_installer_tool.py # PythonPackageInstallerTool & Input (migrated to v2)
│       ├── pubmed_search_tool.py    # PubMedSearchTool & PubMedSearchInput (migrated to v2)
│       ├── python_repl_tool.py      # PythonREPLTool & PythonREPLInput (migrated to v2)
│       └── deep_research_tool.py  # DeepResearchTool & DeepResearchToolInput (Input migrated, internal models pending)
├── css/
│   └── style.css                # Main stylesheet
├── js/
│   ├── script.js                # Main frontend orchestrator
│   ├── state_manager.js         # Manages UI and application state
│   └── ui_modules/              # Modular UI components
│       ├── artifact_ui.js
│       ├── chat_ui.js
│       ├── file_upload_ui.js
│       ├── llm_selector_ui.js
│       ├── monitor_ui.js
│       ├── task_ui.js
│       └── token_usage_ui.js
├── BRAINSTORM.md                # This file
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                    # Project overview
├── ROADMAP.md                   # Project roadmap
├── UI_UX_style.md               # UI/UX refinement notes
└── simulation_option6.html      # UI simulation/sandbox (archival)

## Setup & Installation
1.  **Clone the repository.**
2.  **Configure environment variables:** Copy `.env.example` to `.env` and fill in API keys (GOOGLE_API_KEY, TAVILY_API_KEY, ENTREZ_EMAIL) and any other necessary settings.
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
