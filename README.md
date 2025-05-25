# ResearchAgent: AI Assistant for Research Workflows (v2.5)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Version 2.5 Highlights:**
* **Major Frontend Refactoring**: JavaScript code for the UI has been modularized into a `state_manager.js`, `websocket_manager.js`, and several `ui_modules` (for tasks, chat, monitor, artifacts, LLM selectors, token usage, and file uploads) for improved maintainability and clarity.
* **Fully Functional `DeepResearchTool`**: A multi-phase tool for comprehensive investigations (search, source curation, content extraction, and report synthesis).
* **Enhanced Agent Stability**: Significant improvements in the reliability of multi-step plan execution, especially for tasks requiring the agent's LLM to generate content directly.
* **Tavily API Integration**: Utilizes Tavily for primary web search capabilities.
* **Advanced P-C-E-E Pipeline**: Employs a Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and retry mechanisms.
* **Configurable LLMs**: Supports Google Gemini and local Ollama models, with role-specific configurations.

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps to achieve the user's goal, selecting appropriate tools.
3.  **User Confirmation (for plans)**: The proposed plan is shown to the user for approval.
4.  **Execution**: The agent executes each step, involving a Controller (to validate and prepare actions), an Executor (a ReAct agent to perform actions using tools or its own LLM), and a Step Evaluator (to assess step success and suggest retries).
5.  **Overall Evaluation**: A final assessment of the plan's success is provided.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`. For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    * Task Management (create, select, delete, rename) with persistent storage.
    * Chat Interface with Markdown rendering and input history.
    * Role-Specific LLM Selection (session overrides for Intent, Planner, Controller, Executor, Evaluator).
    * Monitor Panel for structured agent logs.
    * Artifact Viewer for text/image/PDF outputs with live updates (including `_plan.md`).
    * Plan Display & Confirmation dialog in chat.
    * Token Usage Tracking (per call and per task).
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend using `aiohttp` (HTTP for file serving/uploads) and `websockets`.
    * LangChain for core agent logic and P-C-E-E pipeline.
    * Task-specific, isolated workspaces with persistent history (SQLite for tasks & messages).
    * Detailed Callbacks for logging and UI updates.
3.  **Tool Suite (`backend/tools/`):**
    * `TavilyAPISearchTool`: Primary web search.
    * `DeepResearchTool`: Fully functional multi-phase tool for in-depth investigation.
    * `DuckDuckGoSearchRun`: Fallback web search.
    * `web_page_reader`: Reads web content.
    * `pubmed_search`: Searches PubMed.
    * File I/O: `read_file`, `write_file`.
    * Execution Tools: `workspace_shell`, `python_package_installer`, `Python_REPL` (use with caution).
4.  **Configuration:**
    * Uses `.env` for settings (API keys, LLM preferences, agent parameters).
    * `config.py` (dataclass-based) for loading settings.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
    -   Modularized into `state_manager.js`, `websocket_manager.js`, and various `ui_modules/*.js` files.
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`, `langchain-tavily`, etc.
-   **Containerization:** Docker, Docker Compose.

(For a full list of Python dependencies, see `requirements.txt`)

## Project Structure

```

ResearchAgent/
├── .env # Environment variables (GITIGNORED - sensitive data)
├── .env.example # Example environment variables
├── .gitignore # Specifies intentionally untracked files
├── backend/ # Python backend code
│ ├── init.py # Makes 'backend' a Python package
│ ├── agent.py # Logic for creating the LangChain agent executor
│ ├── callbacks.py # Custom LangChain callback handlers (WebSocketCallbackHandler)
│ ├── config.py # Configuration loading (from .env) and settings
│ ├── controller.py # Agent's Controller component
│ ├── db_utils.py # Asynchronous SQLite database utility functions
│ ├── evaluator.py # Agent's Evaluator components (step & overall plan)
│ ├── intent_classifier.py # Logic for classifying user intent
│ ├── llm_setup.py # Functions for initializing LLM instances
│ ├── message_handlers.py # Handles WebSocket message types and orchestrates agent flow
│ ├── planner.py # Agent's Planner component
│ ├── server.py # Main WebSocket server and aiohttp file/upload server
│ └── tools/ # Directory for agent tools
│ ├── init.py # Makes 'tools' a Python package
│ ├── deep_research_tool.py # The multi-phase DeepResearchTool
│ ├── playwright_search.py # Playwright-based web search tool (experimental)
│ ├── standard_tools.py # Core tools (file I/O, shell, PubMed, etc.)
│ └── tavily_search_tool.py # Tavily API search tool wrapper
├── css/ # CSS stylesheets
│ └── style.css # Main stylesheet for the UI
├── database/ # Directory for SQLite database storage (GITIGNORED)
│ └── agent_history.db # SQLite database file
├── js/ # JavaScript frontend logic
│ ├── script.js # Main orchestrator, event listeners, state management calls
│ ├── state_manager.js # Manages client-side application state and localStorage
│ ├── websocket_manager.js # Handles WebSocket connection and raw message sending/receiving
│ └── ui_modules/ # Granular UI component managers
│ ├── artifact_ui.js
│ ├── chat_ui.js
│ ├── file_upload_ui.js
│ ├── llm_selector_ui.js
│ ├── monitor_ui.js
│ ├── task_ui.js
│ └── token_usage_ui.js
├── BRAINSTORM.md # Current workflow, ideas, and immediate feedback log
├── Dockerfile # Instructions for building the Docker image for the backend
├── docker-compose.yml # Docker Compose configuration for running the backend service
├── index.html # Main HTML file for the frontend UI
├── README.md # This file: Project overview, setup, and usage
├── ROADMAP.md # Detailed future development plans and phases
├── requirements.txt # Python package dependencies
└── workspace/ # Base directory for task-specific workspaces (GITIGNORED)
└── <task_id>/ # Each task gets its own subdirectory
├── plan.md # Markdown file for a confirmed plan and its live status
└── ... # Other files generated or uploaded for the task

```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/vbianchi/ResearchAgent.git](https://github.com/vbianchi/ResearchAgent.git)
    cd ResearchAgent
    ```
2.  **Prerequisites:**
    * Python 3.10+ (Python 3.12 is used in the Dockerfile).
    * Docker and Docker Compose (for the recommended Docker-based run).
3.  **Install `uv` (Recommended Python Package Installer):**
    ```bash
    pip install uv
    ```
    Or, if you prefer, you can use `pip` directly in the next step.
4.  **Create and Activate Virtual Environment (Optional but Recommended for Local Dev):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
5.  **Install Python Dependencies:**
    Using `uv`:
    ```bash
    uv pip install -r requirements.txt
    ```
    Or using `pip`:
    ```bash
    pip install -r requirements.txt
    ```
6.  **Configure Environment Variables:**
    * Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    * Edit `.env` and fill in your API keys and preferences:
        * `GOOGLE_API_KEY`: Required if using Gemini models.
        * `TAVILY_API_KEY`: Required for the `TavilyAPISearchTool`.
        * `ENTREZ_EMAIL`: Your email for PubMed searches.
        * Review other LLM and agent settings (e.g., `DEFAULT_LLM_ID`, role-specific LLMs, `OLLAMA_BASE_URL` if using local Ollama models).
7.  **Install Playwright Browsers (if developing Playwright-based tools or running locally without Docker initially):**
    The `Dockerfile` handles this for Docker builds. For local development where you might run `backend/server.py` directly:
    ```bash
    playwright install --with-deps chromium
    # Or: playwright install --with-deps  # To install all (chromium, firefox, webkit)
    ```

## Running the Application

### Using Docker (Recommended Method)

1.  **Build and Run the Backend Service:**
    From the project root directory (`ResearchAgent/`):
    ```bash
    docker compose up --build
    ```
    This will build the Docker image (if it's the first time or `Dockerfile` changed) and start the backend container. The backend WebSocket server will be available on `ws://localhost:8765` and the file server on `http://localhost:8766`.

2.  **Start the Frontend Server:**
    The frontend is a set of static HTML, CSS, and JS files. You can serve it using any simple HTTP server. In a **new terminal window**, from the project root directory:
    ```bash
    python3 -m http.server 8000
    ```
    (If `python3` isn't aliased, try `python -m http.server 8000`).

3.  **Access the UI:**
    Open your web browser and go to: `http://localhost:8000`

### Running Backend Directly (for Development)

1.  Ensure all prerequisites and Python dependencies are installed (steps 2-5 in Setup).
2.  Ensure your `.env` file is configured.
3.  Run the backend server:
    ```bash
    python -m backend.server
    ```
4.  Start the frontend server as described in step 2 of the Docker method.
5.  Access the UI at `http://localhost:8000`.

## Known Issues

* **Agent Cancellation (STOP Button):** May not always be instantaneous for long-running tool operations, especially those executed in external processes or involving network calls without fine-grained async control from within the tool.
* **`_Exception` Tool Calls:** The ReAct agent (Executor) might occasionally call an internal `_Exception` tool if it struggles with its own output formatting or interpreting complex tool results. Recent improvements have significantly reduced this for direct LLM generation steps, but it's monitored.

## Security Warnings

* Tools like `python_package_installer`, `Python_REPL`, and `workspace_shell` execute code/commands with the permissions of the backend process. Use with extreme caution, especially if the backend is not run in a properly isolated environment (Docker is recommended).
* The `workspace_shell` tool allows arbitrary shell command execution within the task's workspace.

## Next Steps & Future Perspectives

The project is actively being enhanced. Key future directions include:

* **Advanced Agent Capabilities:** Further improving error handling, self-correction mechanisms, and refining the integration of complex tools.
* **User-in-the-Loop (UITL) Interactivity:** Introducing mechanisms for users to guide plan execution, provide input at intermediate steps, and potentially modify plans dynamically.
* **Expanded Toolset & Knowledge Integration:** Adding new granular tools and enabling the agent to leverage workspace documents more deeply (e.g., through RAG).
* **Ongoing UX/UI Refinements.**

For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.