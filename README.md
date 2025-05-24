```
ResearchAgent: AI Assistant for Research Workflows (v2.4)
=========================================================

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Version 2.4 Highlights:**
* **Fully Functional `DeepResearchTool`**: A multi-phase tool for comprehensive investigations (search, source curation, content extraction, and report synthesis).
* **Enhanced Agent Stability**: Significant improvements in the reliability of multi-step plan execution, especially for tasks requiring the agent's LLM to generate content directly.
* **Tavily API Integration**: Utilizes Tavily for primary web search capabilities.
* **Advanced P-C-E-E Pipeline**: Employs a Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and retry mechanisms.
* **Configurable LLMs**: Supports Google Gemini and local Ollama models, with role-specific configurations.

Core Architecture & Workflow
----------------------------

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps to achieve the user's goal, selecting appropriate tools.
3.  **User Confirmation (for plans)**: The proposed plan is shown to the user for approval.
4.  **Execution**: The agent executes each step, involving a Controller (to validate and prepare actions), an Executor (a ReAct agent to perform actions using tools or its own LLM), and a Step Evaluator (to assess step success and suggest retries).
5.  **Overall Evaluation**: A final assessment of the plan's success is provided.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`.

Key Current Capabilities & Features
-----------------------------------

1.  **UI & User Interaction:**
    * Task Management (create, select, delete, rename).
    * Chat Interface with Markdown rendering and input history.
    * Role-Specific LLM Selection (session overrides).
    * Monitor Panel for structured logs.
    * Artifact Viewer for text/image outputs with live updates (including `_plan.md`).
    * Plan Display & Confirmation.
    * Token Usage Tracking.
2.  **Backend Architecture & Logic:**
    * Modular Python backend using `aiohttp` (HTTP) and `websockets`.
    * LangChain for core agent logic.
    * Task-specific, isolated workspaces with persistent history (SQLite).
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

Tech Stack
----------

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`, `langchain-tavily`, etc.
-   **Containerization:** Docker, Docker Compose.

(For a full list of dependencies, see `requirements.txt`)

Project Structure
-----------------

```

ResearchAgent/

├── backend/

│ ├── tools/

│ │ ├── standard_tools.py

│ │ ├── tavily_search_tool.py

│ │ └── deep_research_tool.py

│ ├── (other .py files like agent.py, server.py, etc.)

├── css/

├── database/ (GITIGNORED)

├── js/

├── workspace/ (GITIGNORED)

├── .env

├── Dockerfile

├── README.md

└── (other project files)

```

Setup Instructions
------------------
*(This section can remain largely as is, ensuring it's accurate)*
1.  Clone Repository
2.  Prerequisites: Python 3.10+ (3.12 recommended), Docker & Docker Compose (for Docker-based run).
3.  Install `uv` (Recommended Python package installer).
4.  Create and Activate Virtual Environment.
5.  Install Dependencies: `uv pip install -r requirements.txt`.
6.  Configure Environment Variables (`.env` from `.env.example`), especially `TAVILY_API_KEY`, `GOOGLE_API_KEY`.
7.  (Optional) Install Playwright browser binaries if developing that tool locally: `playwright install --with-deps chromium`.

Running the Application
-----------------------
*(This section can remain largely as is)*

### Using Docker (Recommended Method)
1.  Build and Run Backend: `docker compose up --build`
2.  Start Frontend Server (separate terminal): `python3 -m http.server 8000` (or your preferred simple HTTP server)
3.  Access UI: `http://localhost:8000`

Known Issues
------------
-   Agent Cancellation (STOP Button): May not always be instantaneous for long-running tool operations.
-   `_Exception` Tool Calls: The ReAct agent might occasionally call an internal `_Exception` tool if it struggles with its own output formatting or interpreting complex tool results. Recent improvements have significantly reduced this for direct LLM generation steps, but it's monitored.

Security Warnings
-----------------
-   Tools like `python_package_installer`, `Python_REPL`, and `workspace_shell` execute code/commands. Use with extreme caution, especially outside of Docker.

Next Steps & Future Perspectives
--------------------------------
The project is actively being enhanced. Key future directions include:

* **Advanced Agent Capabilities:** Further improving error handling, self-correction mechanisms, and refining the integration of complex tools.
* **User-in-the-Loop (UITL) Interactivity:** Introducing mechanisms for users to guide plan execution, provide input at intermediate steps, and potentially modify plans dynamically.
* **Expanded Toolset & Knowledge Integration:** Adding new granular tools for more specific tasks (e.g., advanced file operations, data extraction) and enabling the agent to leverage workspace documents more deeply (e.g., through RAG).
* **Ongoing UX/UI Refinements.**

For a detailed, evolving roadmap and ongoing brainstorming, please see **`BRAINSTORM.md`**.

```