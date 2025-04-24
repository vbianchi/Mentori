# AI Agent UI Clone & LangChain Backend

This project is a functional clone of the user interface for an AI agent system, inspired by a screenshot of Manus AI. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain** to create a basic AI agent. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (Shell, Web Search, Web Reader, File Read/Write, Package Installer, **Python REPL**) to perform actions. The UI supports task management, chat history persistence via a local database, and displays generated artifacts (images, text files) in the monitor panel.

## Features

* **Task Management:** Create, select, and delete tasks. Each task maintains its own context and workspace.
* **Chat Interface:** Interact with the AI agent via a familiar chat window. Supports input history (Up/Down arrows). Basic Markdown rendering (newlines, bold, italics, code blocks).
* **Agent Workspace (Monitor):** View the agent's internal steps, tool usage, and outputs in a structured, styled log panel.
* **Artifact Viewer:** Displays generated `.png` images and previews common text files (`.txt`, `.py`, `.csv`, etc.) in a dedicated area below the monitor logs, with navigation for multiple artifacts.
* **Tool Integration:** Includes tools for:
    * Web Search (DuckDuckGo)
    * Web Page Reading
    * File Reading (within task workspace)
    * File Writing (within task workspace)
    * Shell Command Execution (within task workspace)
    * Python Package Installation (`pip install`) **(Security Warning!)**
    * **NEW:** Python Code Execution (REPL) **(Security Warning!)**
* **Backend:** Python backend using `websockets`, `aiohttp` (for file serving), and `LangChain`.
* **Frontend:** Simple HTML, CSS, and vanilla JavaScript.
* **LLM Flexibility:** Configurable to use Google Gemini (via API key) or a local Ollama instance.
* **Persistence:** Task list and chat/monitor history are stored locally using SQLite.
* **Task Workspaces:** File/Shell tools operate within isolated directories for each task (`workspace/<task_id>/`).

## Screenshot (Target UI)

(Please place the `image_917c03.jpg` file in the root of this repository for the image below to display correctly)

![Manus AI Screenshot](./image_917c03.jpg)

## Current Capabilities & Workflow

The agent operates within a task-based context. When you select a task:
1.  The backend clears the agent's short-term memory.
2.  It retrieves the chat and monitor history for that specific task from the SQLite database.
3.  The history is loaded into the UI panels, including any previously generated artifacts displayed in the artifact viewer.
When you send a message:
1.  The backend creates a dynamic agent executor configured with tools operating *only* within that task's dedicated workspace (`workspace/<task_id>/`).
2.  The agent processes the input, potentially using tools like:
    * `duckduckgo_search`: For current web information.
    * `web_page_reader`: To fetch and parse content from URLs.
    * `write_file`: To save text or code to a file (e.g., `script.py`) within the task's workspace.
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
    * **Tools:** `langchain-community` (for File Tools, Search), `langchain-experimental` (for Python REPL)
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
├── .venv/ # Virtual environment
├── backend/
│ ├── init.py
│ ├── agent.py # Agent creation logic
│ ├── callbacks.py # WebSocket callback handler
│ ├── config.py # Configuration loading
│ ├── db_utils.py # SQLite database functions
│ ├── llm_setup.py # LLM initialization (Gemini/Ollama)
│ ├── server.py # Main WebSocket & File server logic
│ └── tools.py # Tool definitions and factory
├── css/
│ └── style.css # Frontend styling
├── database/ # SQLite database storage (Created automatically, GITIGNORED)
│ └── agent_history.db
├── js/
│ └── script.js # Frontend JavaScript logic
├── workspace/ # Base directory for task workspaces (GITIGNORED)
│ └── / # Auto-created workspace for each task
│ └── ... # Files created by the agent for this task
├── .env # Environment variables (GITIGNORED)
├── .gitignore # Git ignore rules
├── index.html # Main HTML file for the UI
├── requirements.txt # Python dependencies
└── README.md # This file

```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd manus-ai-ui-clone
    ```
2.  **Create Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # .\ .venv\Scripts\activate # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    # Using pip (ensure pip is up-to-date: python -m pip install --upgrade pip)
    pip install -r requirements.txt

    # Or using uv (faster alternative)
    # pip install uv
    # uv pip install -r requirements.txt
    ```
4.  **Create `.env` File:**
    * Create `.env` in the project root.
    * Add `GOOGLE_API_KEY=YOUR_ACTUAL_GOOGLE_API_KEY` if using Gemini.
    * See Configuration section for optional variables (`AI_PROVIDER`, etc.).
    * Ensure `.env` is in `.gitignore`.
5.  **(If using Ollama)** Ensure Ollama server is running and the desired model is pulled.

## Configuration

Configure via environment variables or the `.env` file:

* `GOOGLE_API_KEY` (Required if using Gemini)
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
* **Test Package Installation:**
    * Ask: `"Install the 'numpy' python package."`
    * Look For (Monitor): `python_package_installer` used, output showing successful installation.
* **Test Python REPL:**
    * Ask: `"Use the Python REPL tool to calculate 15 factorial."`
    * Look For (Monitor): `PythonREPLTool` used with input like `import math; print(math.factorial(15))`, output showing the result.
* **Test Image Generation:**
    * Ask: `"Write a python script named 'plot.py' that uses matplotlib to create a simple sine wave plot and saves it as 'sine_wave.png'. Then execute the script using python."` (Ensure `matplotlib` is installed first).
    * Check Monitor panel for logs and Artifact Viewer for the image.
* **Delete Task:** Click the trash icon (confirmation required).

## Security Warnings

* **`python_package_installer` Tool:** Installs packages directly into the backend server's Python environment. This can break dependencies or install unwanted software if the agent is manipulated.
* **`PythonREPLTool` Tool:** Executes arbitrary Python code directly in the backend server's environment. This is a **significant security risk** if the agent is prompted with malicious code. It can access files, make network requests, or potentially damage the system.
* **Recommendation:** **Strongly consider running the backend server inside a Docker container (Phase 2)**, especially when using the `python_package_installer` or `PythonREPLTool`, to isolate execution and mitigate risks.

## Future Perspectives & Ideas

* **Phase 2: Containerization:** Run the backend in Docker for proper isolation of package installations/code execution and enhanced security.
* **Task Renaming:** Allow users to rename tasks in the left panel.
* **Enhanced Monitor:** Add filtering/search, step navigation.
* **Enhanced Artifact Viewer:** Support more file types (PDF previews?), allow downloading artifacts.
* **More Robust Formatting:** Use a dedicated Markdown library (like Marked.js) in the frontend for richer chat formatting (lists, links, tables).
* **Domain-Specific Tools:** Integrate tools relevant to bioinformatics/epidemiology (PubMed search, BLAST execution, VCF/FASTA parsing).
* **User Authentication:** Secure the application if needed.
* **UI Polish:** Improve overall aesthetics, add loading indicators, better error displays.
