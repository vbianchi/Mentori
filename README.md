    ResearchAgent: AI Assistant for Research Workflows (v2.3)
=========================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

Version 2.3 successfully integrates the Tavily Search API as the primary web search tool, offering more reliable and LLM-optimized search results. It builds upon the v2.2 architecture, which includes an advanced Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and a retry mechanism. The agent uses an Intent Classifier and configurable LLMs (Google Gemini or local Ollama) for reasoning, with tools operating in isolated task workspaces.

Core Architecture & Workflow
----------------------------

The system processes user queries through a sophisticated pipeline:

1.  User Input: The user provides a query via the web UI.

2.  Intent Classification (`intent_classifier.py`):

    -   A designated "Intent Classifier LLM" analyzes the query.

    -   Output: Classifies the intent as `DIRECT_QA` or `PLAN`.

3.  Request Handling (`message_handlers.py`):

    -   If `DIRECT_QA`: The Executor (ReAct agent) is directly invoked.

    -   If `PLAN`:

        1.  Planner (`planner.py`): Generates a multi-step plan.

        2.  User Confirmation (UI): User confirms or cancels the plan.

        3.  Execution Loop (`message_handlers.process_execute_confirmed_plan`):

            -   Plan Persistence: Saves the plan to a `_plan_<ID>.md` file.

            -   Iterates through steps, each involving:

                -   Controller/Validator (`controller.py`): Validates/chooses the tool and formulates `tool_input`.

                -   Executor (`agent.py`): Executes the step.

                -   Step Evaluator (`evaluator.py`): Assesses step outcome. If failed but recoverable, hints are passed back to the Controller for a retry attempt (up to `MAX_STEP_RETRIES`). If unrecoverable or retries exhausted, the plan halts.

            -   Live Plan Update: The `_plan_<ID>.md` file status is updated.

        4.  Overall Plan Evaluator (`evaluator.py`): Assesses the final outcome.

Key Current Capabilities & Features
-----------------------------------

1.  UI & User Interaction:

    -   Task Management, Chat Interface, Role-Specific LLM Selection, Monitor Panel, Status Indicator, STOP Button, File Upload, Artifact Viewer (with reliable live updates for `_plan.md`), Plan Display & Confirmation, Token Usage Tracking.

2.  Backend Architecture & Logic:

    -   Modular Design, Role-Specific LLM Configuration, LLM Initialization with Fallback, Callbacks (with improved tool name logging), SQLite Database, Task Workspaces, Plan Persistence & Live Update.

3.  Tool Suite (`backend/tools/`):

    -   Web Search: `tavily_search_api` (Primary) - Uses Tavily Search API for robust web searching.

    -   Web Search (Fallback): `duckduckgo_search` - Still available if Tavily is not configured.

    -   Web Page Reader: `web_page_reader`.

    -   PubMed Search: `pubmed_search`.

    -   File I/O: `read_file`, `write_file`.

    -   Shell Execution: `workspace_shell`. *(Security Warning)*

    -   Python Package Installer: `python_package_installer`. *(Security Warning)*

    -   Python REPL: `Python_REPL`. *(Security Warning)*

4.  Configuration (`config.py`, `.env`): Centralized settings, including `TAVILY_API_KEY`.

Tech Stack
----------

-   Frontend: HTML5, CSS3, Vanilla JavaScript (ES6+)

-   Backend:

    -   Python 3.10+ (Python 3.12 used in Dockerfile)

    -   LangChain, `langchain-tavily`, `langchain-google-genai`, `langchain-ollama`, etc.

    -   Web Server: `aiohttp`, `websockets`

    -   Web Automation (for potential future tools): `playwright` (dependency added)

-   *(Other backend dependencies as previously listed)*

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
│   └── tools/
│       ├── __init__.py
│       ├── standard_tools.py     # Common tools, tool factory (get_dynamic_tools)
│       ├── tavily_search_tool.py # Tavily API search tool
│       └── playwright_search.py  # Playwright tool (initial structure)
├── css/
│   └── style.css
├── database/                   # SQLite database storage (GITIGNORED)
│   └── agent_history.db
├── js/
│   └── script.js
├── workspace/                  # Base directory for task workspaces (GITIGNORED)
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

1.  Clone Repository

2.  Prerequisites: Python 3.10+ (3.12 recommended).

3.  Install `uv` (Recommended)

4.  Create and Activate Virtual Environment

5.  Install Dependencies: `uv pip install -r requirements.txt` (or `pip ...`)

6.  Install Playwright Browser Binaries (if NOT using Docker & planning to use Playwright tool later):

    ```
    playwright install --with-deps chromium

    ```

7.  Configure Environment Variables (`.env`):

    -   Copy `.env.example` to `.env`.

    -   Crucially, add your `TAVILY_API_KEY="tvly-..."`.

    -   Fill in `GOOGLE_API_KEY`, `ENTREZ_EMAIL`, and other LLM configurations as needed.

8.  (If using Ollama) Setup Ollama and pull models.

Running the Application
-----------------------

### Using Docker (Recommended Method)

1.  Prerequisites: Docker and Docker Compose.

2.  Build and Run Backend: `docker compose up --build`

3.  Start Frontend Server (separate terminal): `python3 -m http.server 8000`

4.  Access UI: `http://localhost:8000`

### Alternative: Running Directly on Host (Advanced)

*(Follow previous instructions, ensuring virtual env is active and dependencies installed).*

Known Issues
------------

-   Agent Cancellation (STOP Button): May not be instantaneous.

-   `_Exception` Tool Calls: The agent sometimes invokes an internal `_Exception` tool after a successful tool call (like Tavily search). While it usually recovers, this indicates the LLM might occasionally struggle with parsing tool output or deciding the immediate next step. Further refinement of tool output formatting or agent prompting might reduce this.

Security Warnings
-----------------

-   `python_package_installer`, `Python_REPL`, `workspace_shell` tools execute code/commands directly. Use with extreme caution, preferably in Docker.

Future Perspectives & Ideas
---------------------------

1.  Playwright Integration for Advanced Web Interaction (Next Major Consideration):

    -   Current Status: Basic structure for `playwright_search.py` exists. Dependency and Docker setup for Playwright are in place.

    -   Goal: Develop the Playwright tool to handle:

        -   Web searches on engines where APIs are not preferred or available (potentially using the existing selector debugging process).

        -   More complex web page interactions (e.g., logging into sites, filling forms, navigating multi-page articles) if specific research tasks require it. This is where Playwright's true power lies beyond simple search.

    -   Consideration: General web search via Playwright is prone to CAPTCHAs and site layout changes, making it less reliable than APIs like Tavily for that specific purpose. Prioritize Playwright for tasks that *require* browser automation.

2.  Advanced Re-planning & User Interaction: (User-initiated re-planning, Planner re-invocation, UI for plan editing, in-flight feedback).

3.  Enhanced Security & Usability: (Permission Gateway for sensitive tools, Live Plan in Chat UI).

4.  Further Artifact & Tool Enhancements: (Workspace file tree, structured data rendering, report generation, more domain-specific tools).

5.  UI/UX Refinements: (Drag & Drop upload, resizable panels, streaming output).