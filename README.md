ResearchAgent: AI Assistant for Research Workflows (v2.2)
=========================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

Version 2.2 reflects recent bug fixes and a refined agent architecture, including an advanced Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and a retry mechanism for enhanced task completion. The agent also includes an Intent Classifier to differentiate simple queries from complex tasks. It uses configurable LLMs (Google Gemini or local Ollama) for reasoning and various tools to perform actions within isolated task workspaces.

Core Architecture & Workflow
----------------------------

The system processes user queries through a sophisticated pipeline:

1.  User Input: The user provides a query via the web UI.

2.  Intent Classification (`intent_classifier.py`):

    -   A designated "Intent Classifier LLM" (configurable via `.env` and session overrides) analyzes the query.

    -   Output: Classifies the intent as either:

        -   `DIRECT_QA`: For simple questions, explanations, or single-tool tasks.

        -   `PLAN`: For complex tasks requiring decomposition and multiple tool uses.

3.  Request Handling (`message_handlers.py`):

    -   If `DIRECT_QA`:

        -   The system bypasses the Planner and Controller.

        -   The Executor (a ReAct agent via `agent.py`) is directly invoked.

        -   The Executor uses its configured LLM (session override > `EXECUTOR_DEFAULT_LLM_ID` > `DEFAULT_LLM_ID`) and available tools to generate an answer.

        -   Callbacks send logs and the final answer to the UI.

    -   If `PLAN`: The system engages the full planning and execution cycle:

        1.  Planner (`planner.py`):

            -   Uses its designated "Planner LLM" (session override > `PLANNER_LLM_ID` > `DEFAULT_LLM_ID`).

            -   Takes the user query and a summary of available tools.

            -   Generates a multi-step plan (`List[PlanStep]`) including step descriptions, tool hints, input instructions, and expected outcomes.

            -   Provides a human-readable summary of the plan.

        2.  User Confirmation (UI):

            -   The plan summary and detailed steps are displayed in the chat.

            -   User can "Confirm & Run Plan" or "Cancel Plan".

            -   The plan UI remains visible (but disabled) during execution.

        3.  Execution Loop (`message_handlers.process_execute_confirmed_plan`):

            -   Plan Persistence (Initial Save): Upon confirmation, a unique, timestamped Markdown file (e.g., `_plan_YYYYMMDD_HHMMSS_ffffff.md`) is created in the task's workspace. This file lists all plan steps with initial `- [ ]` checkboxes (e.g., `- [ ] 1. **Step Description**`). The filename is stored in the session.

            -   The system iterates through each confirmed `PlanStep`.

            -   Inner Retry Loop (for each step, max `MAX_STEP_RETRIES` times):

                -   Controller/Validator (`controller.py`):

                    -   Uses its "Controller LLM" (session override > `CONTROLLER_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Receives the current `PlanStep` (or correction hints on retry), original query, and available tools.

                    -   Validates/chooses the tool and formulates the precise `tool_input`.

                    -   Returns tool name, input, reasoning, and confidence.

                -   Executor (`agent.py` - ReAct agent):

                    -   Uses its "Executor LLM" (session override > `EXECUTOR_DEFAULT_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Receives a directive based on the Controller's output (specific tool use or direct answer).

                    -   Executes the step.

                -   Step Evaluator (`evaluator.py` - `evaluate_step_outcome_and_suggest_correction`):

                    -   Uses "Evaluator LLM" (session override > `EVALUATOR_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Assesses if the current step's specific goal was achieved. The prompt for this evaluator has been refined to better handle external errors like rate limits, marking them as not immediately recoverable by a simple retry.

                    -   If `step_achieved_goal` is `false` but `is_recoverable_via_retry` is `true` (and retries remain):

                        -   Provides `suggested_new_tool_for_retry` and `suggested_new_input_instructions_for_retry`.

                        -   The inner loop continues, feeding these suggestions to the Controller for the next attempt of *this same step*.

                    -   If `step_achieved_goal` is `true`, the inner loop breaks, and the step is marked successful.

                    -   If the step fails and is not recoverable or retries are exhausted, the step is marked failed, and the entire plan execution halts.

            -   Live Plan Update: After each step attempt (and its final determination), the `_plan_<ID>.md` file is updated with the step's status (`[x]`, `[!]`, or `[-]`). The artifact viewer is triggered to refresh its artifact list and display the updated plan content.

        4.  Overall Plan Evaluator (`evaluator.py` - `evaluate_plan_outcome`):

            -   Called after all plan steps are attempted or the plan halts.

            -   Uses its "Evaluator LLM".

            -   Receives the original query, a summary of all executed step details (including attempts and errors), and the preliminary final answer.

            -   Assesses `overall_success`, provides a textual `assessment`, identifies `missing_information`, and can offer `suggestions_for_replan`.

            -   The Evaluator's `assessment` becomes the final message sent to the user.

Key Current Capabilities & Features
-----------------------------------

1.  UI & User Interaction:

    -   Task Management: Create, select, delete, and rename tasks with persistent history.

    -   Chat Interface: Standard chat UI with input history and Markdown rendering.

    -   Role-Specific LLM Selection (Session Override): Dropdowns for Intent Classifier, Planner, Controller, Executor, and Evaluator LLMs.

    -   Monitor Panel: Detailed logs of agent thoughts, tool calls (with improved tool name identification on error), errors, system messages, and outputs from all agent components.

    -   Status Indicator: Visual feedback on agent state.

    -   STOP Button: Allows user to request cancellation of ongoing operations.

    -   File Upload: Upload files to the current task's workspace.

    -   Artifact Viewer:

        -   Displays images, text files (including live-updating `_plan.md`), and PDF links.

        -   Auto-refreshes reliably when artifacts are created or updated, with fixes for previous duplication and caching issues.

        -   Navigation for multiple artifacts.

    -   Plan Display & Confirmation: Generated plans are shown for user confirmation and remain visible (disabled) during execution.

    -   Token Usage Tracking: Per-call and per-task token counts.

2.  Backend Architecture & Logic:

    -   Modular Design: `server.py`, `message_handlers.py`, and component modules.

    -   Role-Specific LLM Configuration: Via `.env` and `config.py`.

    -   LLM Initialization with Fallback (`llm_setup.py`): With improved logging for role context.

    -   Callbacks (`callbacks.py`): `WebSocketCallbackHandler` sends detailed events; improved tool name logging in `on_tool_error`.

    -   Database (`db_utils.py`): SQLite for persistent history.

    -   Task Workspaces (`tools.py`): Isolated directories.

    -   Plan Persistence & Live Update (`message_handlers.py`):

        -   `_plan_<timestamp>.md` saved with correct Markdown checklist format.

        -   Step statuses are correctly updated in this file during execution.

3.  Tool Suite (`tools.py`):

    -   Web Search: `duckduckgo_search` (currently subject to external rate limits).

    -   Web Page Reader: `web_page_reader`.

    -   PubMed Search: `pubmed_search`.

    -   File I/O: `read_file`, `write_file`.

    -   Shell Execution: `workspace_shell`. *(Security Warning)*

    -   Python Package Installer: `python_package_installer`. *(Security Warning)*

    -   Python REPL: `Python_REPL`. *(Security Warning)*

4.  Configuration (`config.py`, `.env`): Centralized settings.

Tech Stack
----------

-   Frontend: HTML5, CSS3, Vanilla JavaScript (ES6+)

-   Backend:

    -   Python 3.10+ (`asyncio`, `websockets`)

    -   Web Server: `aiohttp`, `aiohttp-cors`

    -   LangChain Core: `langchain`, `langchain-core`

    -   LLM Integrations: `langchain-google-genai`, `langchain-ollama`

    -   Tools: `langchain-community` (Search), `langchain-experimental` (Python REPL), `biopython` (PubMed)

    -   Config: `python-dotenv`

    -   HTTP: `httpx`

    -   Web Parsing: `beautifulsoup4`, `lxml`

    -   Async File I/O: `aiofiles`

    -   PDF Reading: `pypdf`

    -   Database: `aiosqlite`

-   Environment: `venv` with `pip` (or `uv`)

-   Protocol: WebSockets (WS), HTTP (for file upload/serving)

Project Structure
-----------------

```
ResearchAgent/
├── .venv/
├── backend/
│   ├── __init__.py
│   ├── agent.py
│   ├── callbacks.py
│   ├── config.py
│   ├── controller.py
│   ├── db_utils.py
│   ├── evaluator.py
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── planner.py
│   ├── server.py
│   └── tools.py
├── css/
│   └── style.css
├── database/
│   └── agent_history.db
├── js/
│   └── script.js
├── workspace/
│   └── <task_id>/
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── index.html
├── requirements.txt
└── README.md

```

Setup Instructions
------------------

*(Refer to your existing detailed setup instructions)*

Running the Application
-----------------------

*(Refer to your existing Docker or direct run instructions)*

Known Issues
------------

-   DuckDuckGo Rate Limiting: The `duckduckgo_search` tool is susceptible to external rate limits. While the Step Evaluator is now better at not retrying these immediately, this can still halt plan execution if search is a critical early step. This highlights the need for more robust search solutions.

-   Agent Cancellation (STOP Button): Interrupts primarily between major steps/LLM calls; not always instantaneous within a long-running tool or LLM call.

-   Markdown Rendering in Chat: Basic; complex Markdown might not render perfectly.

-   Ollama Token Counts: Can be less precise than API-based models.

Security Warnings
-----------------

-   `python_package_installer` & `Python_REPL` Tools: Execute code/install packages in the backend environment. Significant security risk if exposed. Run in Docker for isolation.

-   `workspace_shell` Tool: Executes shell commands. Use with caution.

Future Perspectives & Ideas
---------------------------

1.  Playwright Integration for Web Search (High Priority):

    -   Develop a new LangChain tool using Playwright to perform web searches (e.g., on Google or DuckDuckGo) and extract results.

    -   This aims to provide a more robust and reliable alternative to the current `duckduckgo_search` tool, especially to mitigate rate-limiting issues.

    -   Phased Approach:

        -   Phase 1: Basic search and extraction of titles/links.

        -   Phase 2: Snippet extraction, more robust error handling (timeouts, CAPTCHAs).

        -   Phase 3: Configuration options (search engine choice, number of results).

    -   Requires adding `playwright` to dependencies and updating Dockerfile/setup for browser binaries.

2.  Advanced Re-planning & User Interaction:

    -   Allow user-initiated re-planning based on Overall Plan Evaluator suggestions.

    -   Enable the main Planner to be re-invoked by the system if the Overall Plan Evaluator deems the entire strategy flawed.

    -   UI for users to edit, re-order, add/delete steps from a proposed plan *before* execution.

    -   Mechanisms for users to pause and inject feedback/guidance *during* plan execution.

3.  Enhanced Security & Usability:

    -   Permission Gateway for Sensitive Tools: Implement explicit, step-specific user confirmation in the UI before executing actions with `workspace_shell`, `python_package_installer`, or `Python_REPL`.

    -   Live Plan in Chat UI: Display the content of the `_plan.md` file directly within a chat message, updating it live as the plan progresses, in addition to the artifact viewer.

4.  Further Artifact & Tool Enhancements:

    -   Workspace file tree viewer in the UI.

    -   Render structured data (CSV/JSON) from files as interactive tables.

    -   Direct interactive plot rendering from Python REPL outputs.

    -   Dedicated "Report Generation" tool/step to synthesize findings.

    -   Expand domain-specific tools for bioinformatics/epidemiology.

5.  UI/UX Refinements:

    -   Drag & Drop file upload.

    -   Collapsible/resizable UI panels.

    -   Streaming output for LLM thoughts and final answers.