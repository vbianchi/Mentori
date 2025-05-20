ResearchAgent: AI Assistant for Research Workflows (v2.2)
=========================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Version 2.2 reflects recent bug fixes and a refined agent architecture, including an advanced Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and a retry mechanism for enhanced task completion.** The agent also includes an Intent Classifier to differentiate simple queries from complex tasks. It uses configurable LLMs (Google Gemini or local Ollama) for reasoning and various tools to perform actions within isolated task workspaces.

Core Architecture & Workflow
----------------------------

The system processes user queries through a sophisticated pipeline:

1.  **User Input:** The user provides a query via the web UI.

2.  **Intent Classification (`intent_classifier.py`):**

    -   A designated "Intent Classifier LLM" (configurable via `.env` and session overrides) analyzes the query.

    -   **Output:** Classifies the intent as either:

        -   `DIRECT_QA`: For simple questions, explanations, or single-tool tasks.

        -   `PLAN`: For complex tasks requiring decomposition and multiple tool uses.

3.  **Request Handling (`message_handlers.py`):**

    -   **If `DIRECT_QA`:**

        -   The system bypasses the Planner and Controller.

        -   The **Executor** (a ReAct agent via `agent.py`) is directly invoked.

        -   The Executor uses its configured LLM (session override > `EXECUTOR_DEFAULT_LLM_ID` > `DEFAULT_LLM_ID`) and available tools to generate an answer.

        -   Callbacks send logs and the final answer to the UI.

    -   **If `PLAN`:** The system engages the full planning and execution cycle:

        1.  **Planner (`planner.py`):**

            -   Uses its designated "Planner LLM" (session override > `PLANNER_LLM_ID` > `DEFAULT_LLM_ID`).

            -   Takes the user query and a summary of available tools.

            -   Generates a multi-step plan (`List[PlanStep]`) including step descriptions, tool hints, input instructions, and expected outcomes.

            -   Provides a human-readable summary of the plan.

        2.  **User Confirmation (UI):**

            -   The plan summary and detailed steps are displayed in the chat.

            -   User can "Confirm & Run Plan" or "Cancel Plan".

            -   The plan UI remains visible (but disabled) during execution.

        3.  **Execution Loop (`message_handlers.process_execute_confirmed_plan`):**

            -   **Plan Persistence (Initial Save):** Upon confirmation, a unique, timestamped Markdown file (e.g., `_plan_YYYYMMDD_HHMMSS_ffffff.md`) is created in the task's workspace. This file lists all plan steps with initial `- [ ]` checkboxes (e.g., `- [ ] 1. **Step Description**`). The filename is stored in the session.

            -   The system iterates through each confirmed `PlanStep`.

            -   **Inner Retry Loop (for each step, max `MAX_STEP_RETRIES` times):**

                -   **Controller/Validator (`controller.py`):**

                    -   Uses its "Controller LLM" (session override > `CONTROLLER_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Receives the current `PlanStep` (or correction hints on retry), original query, and available tools.

                    -   Validates/chooses the tool and formulates the precise `tool_input`.

                    -   Returns tool name, input, reasoning, and confidence.

                -   **Executor (`agent.py` - ReAct agent):**

                    -   Uses its "Executor LLM" (session override > `EXECUTOR_DEFAULT_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Receives a directive based on the Controller's output (specific tool use or direct answer).

                    -   Executes the step.

                -   **Step Evaluator (`evaluator.py` - `evaluate_step_outcome_and_suggest_correction`):**

                    -   Uses "Evaluator LLM" (session override > `EVALUATOR_LLM_ID` > `DEFAULT_LLM_ID`).

                    -   Assesses if the current step's specific goal was achieved. The prompt for this evaluator has been refined to better handle external errors like rate limits, marking them as not immediately recoverable by a simple retry.

                    -   If `step_achieved_goal` is `false` but `is_recoverable_via_retry` is `true` (and retries remain):

                        -   Provides `suggested_new_tool_for_retry` and `suggested_new_input_instructions_for_retry`.

                        -   The inner loop continues, feeding these suggestions to the Controller for the next attempt of *this same step*.

                    -   If `step_achieved_goal` is `true`, the inner loop breaks, and the step is marked successful.

                    -   If the step fails and is not recoverable or retries are exhausted, the step is marked failed, and the entire plan execution halts.

            -   **Live Plan Update:** After each step attempt (and its final determination), the `_plan_<ID>.md` file is updated with the step's status (`[x]`, `[!]`, or `[-]`). The artifact viewer is triggered to refresh its artifact list and display the updated plan content.

        4.  **Overall Plan Evaluator (`evaluator.py` - `evaluate_plan_outcome`):**

            -   Called after all plan steps are attempted or the plan halts.

            -   Uses its "Evaluator LLM".

            -   Receives the original query, a summary of all executed step details (including attempts and errors), and the preliminary final answer.

            -   Assesses `overall_success`, provides a textual `assessment`, identifies `missing_information`, and can offer `suggestions_for_replan`.

            -   The Evaluator's `assessment` becomes the final message sent to the user.

Key Current Capabilities & Features
-----------------------------------

1.  **UI & User Interaction:**

    -   **Task Management:** Create, select, delete, and rename tasks with persistent history.

    -   **Chat Interface:** Standard chat UI with input history and Markdown rendering.

    -   **Role-Specific LLM Selection (Session Override):** Dropdowns for Intent Classifier, Planner, Controller, Executor, and Evaluator LLMs.

    -   **Monitor Panel:** Detailed logs of agent thoughts, tool calls (with improved tool name identification on error), errors, system messages, and outputs from all agent components.

    -   **Status Indicator:** Visual feedback on agent state.

    -   **STOP Button:** Allows user to request cancellation of ongoing operations.

    -   **File Upload:** Upload files to the current task's workspace.

    -   **Artifact Viewer:**

        -   Displays images, text files (including live-updating `_plan.md`), and PDF links.

        -   Auto-refreshes reliably when artifacts are created or updated, with fixes for previous duplication and caching issues.

        -   Navigation for multiple artifacts.

    -   **Plan Display & Confirmation:** Generated plans are shown for user confirmation and remain visible (disabled) during execution.

    -   **Token Usage Tracking:** Per-call and per-task token counts.

2.  **Backend Architecture & Logic:**

    -   **Modular Design:**  `server.py`, `message_handlers.py`, and component modules.

    -   **Role-Specific LLM Configuration:** Via `.env` and `config.py`.

    -   **LLM Initialization with Fallback (`llm_setup.py`):** With improved logging for role context.

    -   **Callbacks (`callbacks.py`):**  `WebSocketCallbackHandler` sends detailed events; improved tool name logging in `on_tool_error`.

    -   **Database (`db_utils.py`):** SQLite for persistent history.

    -   **Task Workspaces (`tools.py`):** Isolated directories.

    -   **Plan Persistence & Live Update (`message_handlers.py`):**

        -   `_plan_<timestamp>.md` saved with correct Markdown checklist format.

        -   Step statuses are correctly updated in this file during execution.

3.  **Tool Suite (`backend/tools/`):**

    -   Web Search: `duckduckgo_search` (currently subject to external rate limits).

    -   Web Page Reader: `web_page_reader`.

    -   PubMed Search: `pubmed_search`.

    -   File I/O: `read_file`, `write_file`.

    -   Shell Execution: `workspace_shell`. *(Security Warning)*

    -   Python Package Installer: `python_package_installer`. *(Security Warning)*

    -   Python REPL: `Python_REPL`. *(Security Warning)*

    -   **(Upcoming)** Playwright Web Search: `playwright_web_search` (under development).

4.  **Configuration (`config.py`, `.env`):** Centralized settings.

Tech Stack
----------

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)

-   **Backend:**

    -   Python 3.10+ (`asyncio`, `websockets`) (Python 3.12 used in Dockerfile)

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

    -   Web Automation: `playwright` (for upcoming feature)

-   **Environment:**  `venv` with `pip` (or `uv`)

-   **Protocol:** WebSockets (WS), HTTP (for file upload/serving)

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
│   └── tools/                    # Directory for tool implementations
│       ├── __init__.py
│       ├── standard_tools.py     # Existing tools (refactored from old tools.py)
│       └── playwright_search.py  # For the new Playwright tool (under development)
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

1.  **Clone Repository:**

    ```
    git clone https://github.com/vbianchi/ResearchAgent.git
    cd ResearchAgent

    ```

2.  **Prerequisites:**

    -   Ensure Python 3.10+ is installed (Python 3.12 is recommended and used in the Dockerfile).

    -   **(Optional):** Install R and ensure `Rscript` is in PATH if you plan to use R scripts via the `workspace_shell` tool.

3.  **Install `uv` (Recommended - Fast Package Installer):**

    -   Follow official instructions: <https://github.com/astral-sh/uv#installation>

4.  **Create and Activate Virtual Environment:**

    ```
    # Using uv (recommended)
    uv venv --python 3.12 # Or your desired Python version (e.g., 3.10, 3.11)

    # OR using standard venv
    # python3 -m venv .venv # Or python -m venv .venv

    # Activate (Linux/Mac/WSL)
    source .venv/bin/activate
    # (Windows CMD: .venv\Scripts\activate.bat)
    # (Windows PowerShell: .venv\Scripts\Activate.ps1)

    ```

5.  **Install Dependencies:**

    ```
    # Using uv (recommended)
    uv pip install -r requirements.txt

    # OR using standard pip
    # pip install -r requirements.txt

    ```

6.  **Install Playwright Browser Binaries (Required for upcoming Playwright search tool):**

    -   **If NOT using Docker for the backend:** After installing Python packages, you must install Playwright's browser binaries:

    ```
    playwright install --with-deps chromium
    # Or to install all default browsers: playwright install --with-deps
    # Or specific ones: playwright install firefox webkit

    ```

    -   The `--with-deps` flag attempts to install necessary OS-level dependencies.

    -   **If using Docker:** This step is handled within the `Dockerfile`.

7.  **Configure Environment Variables:**

    -   **Copy the example file:**  `cp .env.example .env` (or copy manually).

    -   **Edit `.env`:** Open the newly created `.env` file with a text editor.

    -   **Fill in required values:**

        -   `GOOGLE_API_KEY`: Add your Google API Key (required if using Gemini). Get one from [Google AI Studio](https://aistudio.google.com/app/apikey "null").

        -   `ENTREZ_EMAIL`: Add your email address (required for PubMed Tool). NCBI uses this to identify requests.

    -   **Configure LLMs:**

        -   Review and update `DEFAULT_LLM_ID`, `INTENT_CLASSIFIER_LLM_ID`, `PLANNER_LLM_ID`, `CONTROLLER_LLM_ID`, `EXECUTOR_DEFAULT_LLM_ID`, `EVALUATOR_LLM_ID` as needed.

        -   `GEMINI_AVAILABLE_MODELS`: List the Gemini models you want available in the UI dropdown, separated by commas (e.g., `gemini-1.5-flash,gemini-1.5-pro-latest`). Ensure these are accessible with your API key.

        -   `OLLAMA_AVAILABLE_MODELS`: List the Ollama models you want available, separated by commas (e.g., `gemma:2b,llama3:latest`). Ensure these are pulled and running in your Ollama instance (`ollama list`).

        -   `OLLAMA_BASE_URL`: Set the correct URL for your Ollama instance if you use it (e.g., `http://localhost:11434`).

    -   **(Optional) Adjust Tuning & Settings:** Modify agent parameters, tool settings, server settings, or log level as needed. See comments in `.env.example` for details.

    -   **Security:** The `.env` file is listed in `.gitignore` to prevent accidental commits of your secrets.

8.  **(If using Ollama)**

    -   Install Ollama: <https://ollama.com/>

    -   Ensure the Ollama service is running.

    -   **Important for Docker/WSL:** If Ollama runs as a systemd service, ensure it listens on all interfaces. Edit the service file (`sudo systemctl edit --full ollama.service`), add `Environment="OLLAMA_HOST=0.0.0.0"` under `[Service]`, then run `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.

    -   Pull the models listed in `OLLAMA_AVAILABLE_MODELS`: `ollama pull <model_name>` (e.g., `ollama pull llama3:latest`).

Running the Application
-----------------------

### Using Docker (Recommended Method)

Runs the backend server inside an isolated Docker container. **Highly recommended** for security and dependency management, especially with tools that execute code or install packages.

1.  **Prerequisites:** Ensure Docker and Docker Compose are installed.

2.  **Build and Run Backend:** From the project root directory (`ResearchAgent/`), run:

    ```
    docker compose up --build

    ```

    -   The `--build` flag is needed the first time or after changing `Dockerfile` or `requirements.txt`.

    -   The `docker-compose.yml` is configured to use `network_mode: host` (for simpler connection to host services like Ollama) and mounts `./backend`, `./workspace`, and `./database` as volumes. The `Dockerfile` includes steps to install Playwright browser binaries.

    -   The backend listens on host ports 8765 (WebSocket) and 8766 (File Server). Ensure these ports are free.

    -   Keep this terminal running. Use `Ctrl+C` to stop.

3.  **Start Frontend Server:** Docker Compose only runs the backend. Serve the frontend files (HTML, CSS, JS) from a ***separate*** terminal in the project root:

    ```
    python3 -m http.server 8000

    ```

    -   Keep this second terminal running.

4.  **Access the UI:** Open your web browser to `http://localhost:8000`.

**Development Workflow with Docker:**

-   **Code Changes:** Changes to `./backend` code are reflected inside the container due to the volume mount. Stop (`Ctrl+C`) and restart (`docker compose up`) the container to apply backend changes.

-   **Dependency Changes:** If `requirements.txt` changes, rebuild with `docker compose up --build`.

-   **Workspace & Database:** Persist locally due to volume mounts.

### Alternative: Running Directly on Host (Advanced / Less Secure)

**Not recommended for production or if using sensitive tools** due to security risks of `Python_REPL` and `python_package_installer` executing directly in your host environment. **Proceed with extreme caution.**

1.  **Setup Environment:** Ensure Python is installed, activate your virtual environment, and install dependencies (including Playwright browser binaries as per step 6 in "Setup Instructions").

2.  **Terminal 1: Start Backend Server:**

    ```
    python3 -m backend.server

    ```

3.  **Terminal 2: Start Frontend Server:**

    ```
    python3 -m http.server 8000

    ```

4.  **Access the UI:** Open `http://localhost:8000`.

Known Issues
------------

-   **DuckDuckGo Rate Limiting:** The `duckduckgo_search` tool is susceptible to external rate limits. The Step Evaluator has been improved to not immediately retry these, but this can still halt plan execution. This highlights the need for the upcoming Playwright search tool.

-   **Agent Cancellation (STOP Button):** Interrupts primarily between major steps/LLM calls; not always instantaneous within a long-running tool or LLM call.

-   **Markdown Rendering in Chat:** Basic; complex Markdown might not render perfectly.

-   **Ollama Token Counts:** Can be less precise than API-based models.

Security Warnings
-----------------

-   **`python_package_installer` & `Python_REPL` Tools:** Execute code/install packages in the backend environment. **Significant security risk if exposed.** Use in Docker for better isolation.

-   **`workspace_shell` Tool:** Executes shell commands. Use with caution.

Future Perspectives & Ideas
---------------------------

1.  **Playwright Integration for Web Search (Next Major Feature):**

    -   Develop a new LangChain tool (`backend/tools/playwright_search.py`) using Playwright to perform web searches (e.g., on Google or DuckDuckGo) and extract results (titles, URLs, snippets).

    -   **Goal:** Provide a more robust and reliable alternative to the current `duckduckgo_search` tool, especially to mitigate rate-limiting issues and enable interaction with more complex web pages if needed later.

    -   **Phased Approach:**

        -   Phase 1: Basic browser launch, navigation, and placeholder for result extraction (current focus).

        -   Phase 2: Implement robust selector logic for a primary search engine to extract titles, URLs, and snippets.

        -   Phase 3: Add configuration options (search engine choice, number of results), enhance error handling.

    -   Requires adding `playwright` to dependencies and updating Dockerfile/setup for browser binaries (already addressed in this plan).

2.  **Advanced Re-planning & User Interaction:**

    -   Allow user-initiated re-planning based on Overall Plan Evaluator suggestions.

    -   Enable the main Planner to be re-invoked by the system if the Overall Plan Evaluator deems the entire strategy flawed.

    -   UI for users to edit, re-order, add/delete steps from a proposed plan *before* execution.

    -   Mechanisms for users to pause and inject feedback/guidance *during* plan execution.

3.  **Enhanced Security & Usability:**

    -   **Permission Gateway for Sensitive Tools:** Implement explicit, step-specific user confirmation in the UI before executing actions with `workspace_shell`, `python_package_installer`, or `Python_REPL`.

    -   **Live Plan in Chat UI:** Display the content of the `_plan.md` file directly within a chat message, updating it live as the plan progresses, in addition to the artifact viewer.

4.  **Further Artifact & Tool Enhancements:**

    -   Workspace file tree viewer in the UI.

    -   Render structured data (CSV/JSON) from files as interactive tables.

    -   Direct interactive plot rendering from Python REPL outputs.

    -   Dedicated "Report Generation" tool/step to synthesize findings.

    -   Expand domain-specific tools for bioinformatics/epidemiology.

5.  **UI/UX Refinements:**

    -   Drag & Drop file upload.

    -   Collapsible/resizable UI panels.

    -   Streaming output for LLM thoughts and final answers.