# AI Agent UI Clone & LangChain Backend

This project is a functional clone of the user interface for an AI assistant system, inspired by a screenshot of Manus AI. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain** to create a basic AI agent. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (Shell, Web Search, Web Reader, File Read/Write, Package Installer, Python REPL, **PubMed Search**) to perform actions. The UI supports task management, chat history persistence via a local database, and displays generated artifacts (images, text files) in the monitor panel.

## Features

* **Task Management:** Create, select, and delete tasks. Each task maintains its own context and workspace.
* **Chat Interface:** Interact with the AI agent via a familiar chat window. Supports input history (Up/Down arrows). Basic Markdown rendering (newlines, bold, italics, code blocks).
* **Agent Workspace (Monitor):** View the agent's internal steps, tool usage, and outputs in a structured, styled log panel.
* **Artifact Viewer:** Displays generated `.png` images and previews common text files (`.txt`, `.py`, `.csv`, etc.) in a dedicated area below the monitor logs, with navigation for multiple artifacts.
* **Tool Integration:** Includes tools for:
    * Web Search (DuckDuckGo)
    * Web Page Reading
    * **NEW:** PubMed Search (Biomedical Literature)
    * File Reading (within task workspace)
    * File Writing (within task workspace)
    * Shell Command Execution (within task workspace, including `Rscript` if R is installed)
    * Python Package Installation (`pip install`) **(Security Warning!)**
    * Python Code Execution (REPL) **(Security Warning!)**
* **Backend:** Python backend using `websockets`, `aiohttp` (for file serving), and `LangChain`.
* **Frontend:** Simple HTML, CSS, and vanilla JavaScript.
* **LLM Flexibility:** Configurable to use Google Gemini (via API key) or a local Ollama instance.
* **Persistence:** Task list and chat/monitor history are stored locally using SQLite.
* **Task Workspaces:** File/Shell tools operate within isolated directories for each task (`workspace/<task_id>/`).

## Current Capabilities & Workflow

The agent operates within a task-based context. When you select a task:
1.  The backend clears the agent's short-term memory.
2.  It retrieves the chat and monitor history for that specific task from the SQLite database.
3.  The history is loaded into the UI panels, including any previously generated artifacts displayed in the artifact viewer.
When you send a message:
1.  The backend creates a dynamic agent executor configured with tools operating *only* within that task's dedicated workspace (`workspace/<task-id>/`).
2.  The agent processes the input, potentially using tools like:
    * `duckduckgo_search`: For general web information.
    * `web_page_reader`: To fetch and parse content from URLs.
    * `pubmed_search`: To search for biomedical literature abstracts.
    * `write_file`: To save text or code (Python, R, etc.) to a file within the task's workspace.
    * `read_file`: To read files from the task's workspace.
    * `workspace_shell`: To execute shell commands (like `python script.py` or `ls`) within the task's workspace.
    * `python_package_installer`: To install required Python packages using `pip`. **(Security Warning!)**
    * `PythonREPLTool`: To execute Python code snippets directly. **(Security Warning!)**
3.  All steps (tool usage, errors, final answer) are logged to the Monitor panel and saved to the database for the current task.
4.  If the agent run generates new image or text artifacts (based on file extensions) in the task's workspace, the backend detects them and sends a message to the UI to update the artifact viewer.
5.  The final answer is displayed in the Chat panel.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:**
    * Python 3.x, `asyncio`, `websockets`
    * **Web Server:** `aiohttp`, `aiohttp-cors` (for serving generated files)
    * **LangChain Core:** `langchain`
    * **LLM Integrations:** `langchain-google-genai`, `langchain-ollama`
    * **Tools:** `langchain-community` (for File Tools, Search), `langchain-experimental` (for Python REPL), **`biopython` (for PubMed)**
    * **Prompts:** `langchainhub`
    * **Config:** `python-dotenv`
    * **HTTP:** `httpx`
    * **Web Parsing:** `beautifulsoup4`, `lxml`
    * **Async File I/O:** `aiofiles`
    * **Plotting (Example):** `matplotlib` (if using plot generation tools/examples)
    * **Database:** `aiosqlite`
* **Environment:** `uv` or `pip` with `venv`
* **Protocol:** WebSockets (WS)

## Project Structure

```

manus-ai-ui-clone/
├── .venv/                  # Virtual environment
├── backend/
│   ├── init.py
│   ├── agent.py            # Agent creation logic
│   ├── callbacks.py        # WebSocket callback handler
│   ├── config.py           # Configuration loading
│   ├── db_utils.py         # SQLite database functions
│   ├── llm_setup.py        # LLM initialization (Gemini/Ollama)
│   ├── server.py           # Main WebSocket & File server logic
│   └── tools.py            # Tool definitions and factory
├── css/
│   └── style.css           # Frontend styling
├── database/               # SQLite database storage (Created automatically, GITIGNORED)
│   └── agent_history.db
├── js/
│   └── script.js           # Frontend JavaScript logic
├── workspace/              # Base directory for task workspaces (GITIGNORED)
│   └── /          # Auto-created workspace for each task
│       └── ...             # Files created by the agent for this task
├── .env                    # Environment variables (GITIGNORED)
├── .gitignore              # Git ignore rules
├── index.html              # Main HTML file for the UI
├── requirements.txt        # Python dependencies
└── README.md               # This file

```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd manus-ai-ui-clone
    ```
2.  **Prerequisites:**
    * Ensure Python 3.10+ is installed.
    * **(Optional):** Install R and ensure `Rscript` is in PATH for R script execution.
3.  **Create Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # .\ .venv\Scripts\activate # Windows
    ```
4.  **Install Dependencies:**
    ```bash
    # Using pip (ensure pip is up-to-date: python -m pip install --upgrade pip)
    pip install -r requirements.txt

    # Or using uv (faster alternative)
    # pip install uv
    # uv pip install -r requirements.txt
    ```
5.  **Create `.env` File:**
    * Create `.env` in the project root.
    * Add `GOOGLE_API_KEY=YOUR_ACTUAL_GOOGLE_API_KEY` if using Gemini.
    * **(Optional but Recommended):** Add `ENTREZ_EMAIL=your_email@example.com` (NCBI requires this for PubMed API usage). Replace with your actual email.
    * See Configuration section for other optional variables (`AI_PROVIDER`, etc.).
    * Ensure `.env` is in `.gitignore`.
6.  **(If using Ollama)** Ensure Ollama server is running and the desired model is pulled.

## Configuration

Configure via environment variables or the `.env` file:

* `GOOGLE_API_KEY` (Required if using Gemini)
* `ENTREZ_EMAIL` (Required for PubMed Tool): Your email address for NCBI API identification.
* `AI_PROVIDER` (Optional): `gemini` (default) or `ollama`.
* `GEMINI_MODEL` (Optional): Default `gemini-1.5-flash-latest`.
* `OLLAMA_BASE_URL` (Optional): Default `http://localhost:11434`.
* `OLLAMA_MODEL` (Optional): Default `gemma:2b`. Ensure model exists in Ollama.

## Running the Application

Run from the **project root directory** (`manus-ai-ui-clone/`).

1.  **Terminal 1: Start Backend Server**
    * Activate environment: `source .venv/bin/activate`
    * Run server as module: `python -m backend.server`
    * Keep running. Observe logs for WebSocket server (e.g., `ws://localhost:8765`) and File server (e.g., `http://localhost:8766`).

2.  **Terminal 2: Start Frontend HTTP Server**
    * (Optional) Activate environment: `source .venv/bin/activate`
    * Run server: `python3 -m http.server 8000`
    * Keep running.

3.  **Access the UI:** Open browser to `http://localhost:8000`.

## Usage & Testing

* **Create Task:** Click "+ New Task".
* **Select Task:** Click a task to load its history and set its workspace.
* **Chat:** Interact with the agent. Use Up/Down arrows for input history.
* **Monitor:** Observe structured logs (tool usage, system messages).
* **Artifact Viewer:** View generated images or text files using the Prev/Next buttons.
* **Test PubMed Search:**
    * Ask: `"Search PubMed for recent articles on CRISPR gene editing."`
    * Look For (Monitor): `pubmed_search` used, output showing article summaries.
* **Test Package Installation:**
    * Ask: `"Install the 'numpy' python package."`
    * Look For (Monitor): `python_package_installer` used, output showing successful installation.
* **Test Python REPL:**
    * Ask: `"Use the Python REPL tool to calculate 15 factorial."`
    * Look For (Monitor): `Python_REPL` used, output showing the result.
* **Test Image Generation:**
    * Ask: `"Write a python script named 'plot.py' that uses matplotlib to create a simple sine wave plot and saves it as 'sine_wave.png'. Then execute the script using python."` (Ensure `matplotlib` is installed first).
    * Check Monitor panel for logs and Artifact Viewer for the image.
* **Delete Task:** Click the trash icon (confirmation required).

## Security Warnings

* **`python_package_installer` Tool:** Installs packages directly into the backend server's Python environment.
* **`PythonREPLTool` Tool:** Executes arbitrary Python code directly in the backend server's environment.
* **Recommendation:** **Strongly consider running the backend server inside a Docker container (Phase 2)**, especially when using these tools, to isolate execution and mitigate risks.

## Future Perspectives & Ideas

* **Phase 2: Containerization:** Run the backend in Docker.
* **ERIC/DOAJ Tools:** Add tools for searching these free databases.
* **Task Renaming:** Allow users to rename tasks.
* **Enhanced Monitor/Artifact Viewer:** Filtering, navigation, more file types (PDF, CSV tables), download.
* **More Robust Formatting:** Use a dedicated Markdown library.
* **Domain-Specific Tools:** PubMed Central (full text), BLAST, VCF/FASTA parsing, Epi Info interaction?
* **User Authentication.**
* **UI Polish.**
