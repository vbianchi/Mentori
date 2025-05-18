ResearchAgent: AI Assistant for Research Workflows (v2.1+ with Step Evaluation)
===============================================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

Version 2.1+ introduces an advanced Planner-Controller-Executor-Evaluator architecture with per-step evaluation and a retry mechanism for enhanced task completion. The agent also includes an Intent Classifier to differentiate simple queries from complex tasks. It uses configurable LLMs (Google Gemini or local Ollama) for reasoning and various tools to perform actions within isolated task workspaces. Backend message handling has also been refactored for improved modularity.

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

            -   Plan Persistence (Initial Save): Upon confirmation, a unique, timestamped Markdown file (e.g., `_plan_YYYYMMDD_HHMMSS_ffffff.md`) is created in the task's workspace. This file lists all plan steps with initial `[ ]` checkboxes. The filename is stored in the session.

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

                    -   Assesses if the current step's specific goal was achieved.

                    -   If `step_achieved_goal` is `false` but `is_recoverable_via_retry` is `true` (and retries remain):

                        -   Provides `suggested_new_tool_for_retry` and `suggested_new_input_instructions_for_retry`.

                        -   The inner loop continues, feeding these suggestions to the Controller for the next attempt of *this same step*.

                    -   If `step_achieved_goal` is `true`, the inner loop breaks, and the step is marked successful.

                    -   If the step fails and is not recoverable or retries are exhausted, the step is marked failed, and the entire plan execution halts.

            -   Live Plan Update: After each step attempt (and its final determination), the `_plan_<ID>.md` file is updated with the step's status (`[x]`, `[!]`, or `[-]`). The artifact viewer is triggered to refresh.

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

    -   Role-Specific LLM Selection (Session Override):

        -   Main "Executor LLM" selector in the chat header.

        -   Dropdowns for Intent Classifier, Planner, Controller, and Evaluator LLMs, allowing selection of specific models or "Use System Default".

        -   Selections are stored in `localStorage` and sent to the backend for the current session.

    -   Monitor Panel: Detailed logs of agent thoughts, tool calls, errors, system messages, and outputs from Intent Classifier, Planner, Controller, Step Evaluator, and Overall Plan Evaluator.

    -   Status Indicator: Visual feedback on agent state (Idle, Running, Cancelling, Error, Disconnected).

    -   STOP Button: Allows user to request cancellation of ongoing operations.

    -   File Upload: Upload files to the current task's workspace.

    -   Artifact Viewer:

        -   Displays images and text files.

        -   PDFs are listed with a link to open in a new tab.

        -   Auto-refreshes when new artifacts are created or existing ones (like `_plan.md`) are updated.

        -   Navigation for multiple artifacts.

    -   Plan Display & Confirmation: Generated plans are shown for user confirmation and remain visible (disabled) during execution.

    -   Token Usage Tracking: Per-call and per-task token counts displayed.

2.  Backend Architecture & Logic:

    -   Modular Design: `server.py` (WebSockets, session management), `message_handlers.py` (message processing), and component modules (`intent_classifier.py`, `planner.py`, `controller.py`, `agent.py` for Executor, `evaluator.py`).

    -   Role-Specific LLM Configuration (`config.py`, `.env`): Defines different LLMs for each component, with fallback to `DEFAULT_LLM_ID`.

    -   LLM Initialization with Fallback (`llm_setup.py`): `get_llm` attempts primary LLM, then system default on failure. Logging includes the role for which an LLM is being initialized.

    -   Callbacks (`callbacks.py`): `WebSocketCallbackHandler` sends detailed LangChain events to UI and DB. Handles `AgentCancelledException`. Attempts to log specific tool names on error.

    -   Database (`db_utils.py`): SQLite stores task details and comprehensive message history.

    -   Task Workspaces (`tools.py`): Isolated directories (`workspace/<task_id>/`) for each task.

    -   Plan Persistence & Live Update (`message_handlers.py`):

        -   Confirmed plans saved to `_plan_<timestamp>.md` with Markdown checklist syntax.

        -   Step statuses (`[ ]`, `[x]`, `[!]`, `[-]`) are updated in this file during execution.

        -   The file is treated as an artifact, and UI refreshes to show changes.

3.  Tool Suite (`tools.py`):

    -   Web Search: `duckduckgo_search`.

    -   Web Page Reader: `web_page_reader`.

    -   PubMed Search: `pubmed_search`.

    -   File I/O: `read_file` (text, PDF text extraction), `write_file`.

    -   Shell Execution: `workspace_shell`.

    -   Python Package Installer: `python_package_installer` (uses `uv pip` or `pip`). *(Security Warning)*

    -   Python REPL: `Python_REPL`. *(Security Warning)*

4.  Configuration (`config.py`, `.env`):

    -   Centralized settings for API keys, LLM IDs, Ollama URL, agent parameters, tool limits, server options.

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
│   ├── agent.py        # Agent creation logic (Executor base)
│   ├── callbacks.py    # WebSocket callback handler
│   ├── config.py       # Configuration loading
│   ├── controller.py   # Controller/Validator logic
│   ├── db_utils.py     # SQLite database functions
│   ├── evaluator.py    # Step Evaluator & Overall Plan Evaluator logic
│   ├── intent_classifier.py # Intent classification logic
│   ├── llm_setup.py    # LLM initialization
│   ├── message_handlers.py # WebSocket message handlers
│   ├── planner.py      # Planner logic
│   ├── server.py       # Main WebSocket & File server logic
│   └── tools.py        # Tool definitions and factory
├── css/
│   └── style.css
├── database/           # SQLite database storage (GITIGNORED)
│   └── agent_history.db
├── js/
│   └── script.js
├── workspace/          # Base directory for task workspaces (GITIGNORED)
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

*(Refer to your existing detailed setup instructions - assuming these are largely unchanged)*

1.  Clone Repository

2.  Prerequisites (Python 3.10+)

3.  Install `uv` (Recommended)

4.  Create and Activate Virtual Environment

5.  Install Dependencies (`uv pip install -r requirements.txt` or `pip install -r requirements.txt`)

6.  Configure Environment Variables (`.env` file based on `.env.example`)

7.  (If using Ollama) Install and run Ollama, pull models.

Running the Application
-----------------------

*(Refer to your existing Docker or direct run instructions)*

Usage & Testing
---------------

*(This section should be updated with test cases for the new step evaluation and retry logic, in addition to existing tool tests.)*

-   Test Step Retry:

    -   Formulate a query where an intermediate step is likely to fail but be correctable. E.g., "Search for X, write to `correct_file.txt`, then try to read `incorrect_file.txt`."

    -   Observe monitor logs for Step Evaluator identifying the failure, suggesting a correction (e.g., to read `correct_file.txt`), and the Executor retrying the step successfully.

    -   Verify the `_plan.md` checklist updates correctly (`[!]` then `[x]`).

-   Test Unrecoverable Step Failure:

    -   Query for an action that will definitively fail (e.g., "Install package `non_existent_package_xyz123`").

    -   Observe Step Evaluator marking it unrecoverable, plan halting, and `_plan.md` showing `[!]`.

-   ... (other existing test cases for tools, LLM switching, etc.)

Known Issues
------------

-   DuckDuckGo Rate Limiting: The `duckduckgo_search` tool may be subject to rate limits, which can interrupt tests or normal operation. The Step Evaluator has been prompted to consider these as not immediately retryable.

-   Agent Cancellation (STOP Button): Interrupts between major steps/LLM calls, not always instantaneous.

-   Markdown Rendering in Chat: Basic; complex Markdown might not render perfectly.

-   Ollama Token Counts: Can be less precise than API-based models.

Security Warnings
-----------------

-   `python_package_installer` & `Python_REPL` Tools: Execute code/install packages in the backend environment. Significant security risk if exposed. Run in Docker for isolation.

-   `workspace_shell` Tool: Executes shell commands. Use with caution.

Future Perspectives & Ideas (Post v2.1+ Step Evaluation)
--------------------------------------------------------

-   Web Search Robustness: Integrate an API-key based search tool (e.g., Google Custom Search, Tavily, Serper) or develop a Playwright-based tool for more resilient web searching and interaction.

-   Advanced Re-planning:

    -   Allow user-initiated re-planning based on Overall Plan Evaluator suggestions.

    -   Enable the Planner to be re-invoked by the system if the Overall Plan Evaluator deems the entire strategy flawed, using its suggestions as input for a new plan.

-   Interactive Plan Modification (Pre-Execution & In-Flight):

    -   UI for users to edit, re-order, add/delete steps from a proposed plan *before* execution.

    -   Mechanisms for users to pause and inject feedback/guidance *during* plan execution.

-   Permission Gateway for Sensitive Tools: Implement explicit, step-specific user confirmation in the UI before executing actions with `workspace_shell`, `python_package_installer`, or `Python_REPL`, even if the overall plan was approved.

-   Enhanced Artifact Interaction & Generation:

    -   Workspace file tree viewer in the UI.

    -   Render structured data (CSV/JSON) as interactive tables.

    -   Direct interactive plot rendering.

    -   Dedicated "Report Generation" tool/step to synthesize findings.

-   UI/UX Enhancements:

    -   Live display of the `_plan.md` content directly within a chat message, updating as the plan progresses.

    -   Drag & Drop file upload.

    -   Collapsible/resizable UI panels.

-   Domain-Specific Tools & Knowledge: Further expand tools relevant to bioinformatics/epidemiology.

-   Streaming Output: Token-by-token streaming for LLM responses (thoughts and final answers).