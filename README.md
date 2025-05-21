ResearchAgent: AI Assistant for Research Workflows (v2.4)
=========================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

Version 2.4 introduces the `DeepResearchTool`, a multi-phase tool designed for comprehensive investigations. The initial search, source curation, and content extraction phases of this tool are now functional, using `TavilyAPISearchTool` as its core search mechanism. This version builds upon the v2.2/v2.3 architecture, which includes an advanced Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and a retry mechanism. The agent uses an Intent Classifier and configurable LLMs (Google Gemini or local Ollama) for reasoning, with tools operating in isolated task workspaces.

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

        1.  Planner (`planner.py`): Generates a multi-step plan. If the query implies in-depth research, the Planner may suggest using the `deep_research_synthesizer` tool.

        2.  User Confirmation (UI): User confirms or cancels the plan.

        3.  Execution Loop (`message_handlers.process_execute_confirmed_plan`):

            -   Plan Persistence: Saves the plan to a `_plan_<ID>.md` file.

            -   Iterates through each confirmed `PlanStep`.

            -   Inner Retry Loop (for each step):

                -   Controller/Validator (`controller.py`): Validates/chooses the tool and formulates `tool_input`. For `DeepResearchTool`, this would be the `topic` and other parameters.

                -   Executor (`agent.py`): Executes the step (e.g., calls `DeepResearchTool._arun`).

                -   Step Evaluator (`evaluator.py`): Assesses step outcome. If failed but recoverable, hints are passed back to the Controller for a retry.

            -   Live Plan Update: The `_plan_<ID>.md` file status is updated.

        4.  Overall Plan Evaluator (`evaluator.py`): Assesses the final outcome.

Key Current Capabilities & Features
-----------------------------------

1.  UI & User Interaction:

    -   Task Management, Chat Interface, Role-Specific LLM Selection, Monitor Panel, Status Indicator, STOP Button, File Upload, Artifact Viewer (with reliable live updates for `_plan.md`), Plan Display & Confirmation, Token Usage Tracking.

2.  Backend Architecture & Logic:

    -   Modular Design, Role-Specific LLM Configuration, LLM Initialization with Fallback, Callbacks (with improved tool name logging), SQLite Database, Task Workspaces, Plan Persistence & Live Update.

3.  Tool Suite (`backend/tools/`):

    -   `TavilyAPISearchTool` (Primary Web Search): Uses Tavily Search API for robust web searching, returning structured results.

    -   `DeepResearchTool` (Multi-Phase Investigation - In Progress):

        -   Phase 1 (Search): Uses `TavilyAPISearchTool` for broad information gathering. (Functional)

        -   Phase 2 (Curation): Uses an LLM to select the most relevant sources from the initial search. (Functional)

        -   Phase 3 (Extraction): Uses `fetch_and_parse_url` to get full content from curated URLs. (Functional)

        -   Phase 4 (Synthesis): (Next to be implemented) Will use an LLM to synthesize extracted/summarized content into a report.

    -   `DuckDuckGoSearchRun` (Fallback Web Search).

    -   `web_page_reader` (Reads web content, used by `DeepResearchTool`).

    -   `pubmed_search` (Searches PubMed).

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

    -   This includes `langchain-tavily`.

6.  Install Playwright Browser Binaries (if planning to develop Playwright tool later and NOT using Docker):

    ```
    playwright install --with-deps chromium

    ```

7.  Configure Environment Variables (`.env`):

    -   Copy `.env.example` to `.env`.

    -   Crucially, add your `TAVILY_API_KEY="tvly-..."`.

    -   Fill in `GOOGLE_API_KEY`, `ENTREZ_EMAIL`, and other LLM configurations.

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

-   `_Exception` Tool Calls: The ReAct agent might occasionally call an internal `_Exception` tool if it misinterprets a tool's output. This usually resolves itself but indicates areas for potential prompt/output refinement.

-   Playwright for General Search: The `playwright_search.py` tool is parked due to the challenges of CAPTCHAs and selector volatility for general search engines. Playwright is better suited for targeted web automation tasks.

Security Warnings
-----------------

-   `python_package_installer`, `Python_REPL`, `workspace_shell` tools execute code/commands directly. Use with extreme caution, preferably in Docker.

Next Steps & Future Perspectives
--------------------------------

1.  Complete `DeepResearchTool` - Phase 4: Information Synthesis:

    -   Implement the "Writer" LLM logic within `DeepResearchTool` to take the extracted (and potentially summarized) content and generate a structured Markdown report.

    -   This involves defining a robust prompt for the writer, handling context window limits (potentially by summarizing content before synthesis), and formatting the LLM's output.

2.  Playwright for Targeted Web Automation:

    -   Revisit `playwright_search.py` not for general search, but for specific tasks that require browser automation (e.g., logging into a specific database, navigating complex JavaScript-heavy sites, filling forms to download data).

3.  Advanced Re-planning & User Interaction: (User-initiated re-planning, Planner re-invocation, UI for plan editing, in-flight feedback).

4.  Enhanced Security & Usability: (Permission Gateway for sensitive tools, Live Plan in Chat UI).

5.  Further Artifact & Tool Enhancements: (Workspace file tree, structured data rendering, report generation, more domain-specific tools).

6.  UI/UX Refinements: (Drag & Drop upload, resizable panels, streaming output).