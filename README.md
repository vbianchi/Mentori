# ResearchAgent: AI Assistant for Research Workflows

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by **LangChain**. The agent can use configurable LLMs (Google Gemini or local Ollama) for reasoning and various tools (Shell, Web Search, Web Reader, File Read/Write, Package Installer, Python REPL, PubMed Search) to perform actions within isolated task workspaces.

## Features

* **Task Management:** Create, select, delete, and rename tasks. Each task maintains its own context and workspace.
* **Chat Interface:** Interact with the AI agent via a familiar chat window. Supports input history (Up/Down arrows). Basic Markdown rendering (newlines, bold, italics, code blocks, links).
* **LLM Selection:** Choose the specific language model (Gemini or Ollama models configured in `.env`) to use for the current session directly from the chat header.
* **Agent Workspace (Monitor):** View the agent's internal steps, tool usage, and outputs in a structured, styled log panel.
* **Artifact Viewer:** Displays generated `.png` images and previews common text files (`.txt`, `.py`, `.csv`, etc.) in a dedicated area below the monitor logs, with navigation for multiple artifacts.
* **Tool Integration:** Includes tools for:
    * Web Search (`duckduckgo_search`)
    * Web Page Reading (`web_page_reader`)
    * PubMed Search (`pubmed_search`)
    * File Reading (`read_file` within task workspace - **Supports text and PDF files**)
    * File Writing (`write_file` within task workspace)
    * Shell Command Execution (`workspace_shell` within task workspace, including `Rscript` if R is installed)
    * Python Package Installation (`python_package_installer`) **(Security Warning!)**
    * Python Code Execution (`Python_REPL`) **(Security Warning!)**
* **Backend:** Python backend using `websockets`, `aiohttp` (for file serving), and `LangChain`.
* **Frontend:** Simple HTML, CSS, and vanilla JavaScript.
* **Configuration:** Extensive configuration via `.env` file (API keys, available models, agent tuning, tool settings, server options).
* **Persistence:** Task list (including names) and chat/monitor history are stored locally using SQLite in the `database/` directory.
* **Task Workspaces:** File/Shell tools operate within isolated directories for each task (`workspace/<task_id>/`), created upon task selection.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:**
    * Python 3.10+ (`asyncio`, `websockets`)
    * **Web Server:** `aiohttp`, `aiohttp-cors`
    * **LangChain Core:** `langchain`
    * **LLM Integrations:** `langchain-google-genai`, `langchain-ollama`
    * **Tools:** `langchain-community` (Search), `langchain-experimental` (Python REPL), `biopython` (PubMed)
    * **Prompts:** `langchainhub`
    * **Config:** `python-dotenv`
    * **HTTP:** `httpx`
    * **Web Parsing:** `beautifulsoup4`, `lxml`
    * **Async File I/O:** `aiofiles`
    * **PDF Reading:** `pypdf`
    * **Plotting (Example):** `matplotlib`
    * **Database:** `aiosqlite`
* **Environment:** `venv` with `pip` (or `uv`)
* **Protocol:** WebSockets (WS)

## Project Structure

```

ResearchAgent/
├── .venv/              # Virtual environment
├── backend/
│   ├── init.py
│   ├── agent.py        # Agent creation logic
│   ├── callbacks.py    # WebSocket callback handler
│   ├── config.py       # Configuration loading
│   ├── db_utils.py     # SQLite database functions
│   ├── llm_setup.py    # LLM initialization (Gemini/Ollama)
│   ├── server.py       # Main WebSocket & File server logic
│   └── tools.py        # Tool definitions and factory
├── css/
│   └── style.css       # Frontend styling
├── database/           # SQLite database storage (Created automatically, GITIGNORED)
│   └── agent_history.db
├── js/
│   └── script.js       # Frontend JavaScript logic
├── workspace/          # Base directory for task workspaces (GITIGNORED)
│   └── <task_id>/      # Auto-created workspace for each task
│       └── ...         # Files created by the agent for this task
├── .env                # Environment variables (GITIGNORED)
├── .env.example        # Example environment file
├── .gitignore          # Git ignore rules
├── Dockerfile          # Docker build instructions
├── docker-compose.yml  # Docker compose configuration
├── index.html          # Main HTML file for the UI
├── requirements.txt    # Python dependencies
└── README.md           # This file

```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/vbianchi/ResearchAgent.git](https://github.com/vbianchi/ResearchAgent.git)
    cd ResearchAgent
    ```
2.  **Prerequisites:**
    * Ensure Python 3.10+ is installed.
    * **(Optional):** Install R and ensure `Rscript` is in PATH for R script execution via the shell tool.

3.  **Install `uv` (Recommended - Fast Package Installer):**
    * Follow instructions: [https://github.com/astral-sh/uv#installation](https://github.com/astral-sh/uv#installation)

4.  **Create and Activate Virtual Environment:**
    ```bash
    # Using uv (recommended)
    uv venv --python 3.12 # Or your desired Python version

    # OR using standard venv
    # python -m venv .env

    # Activate (Linux/Mac/WSL)
    source .venv/bin/activate
    # (Windows CMD: .venv\Scripts\activate.bat)
    # (Windows PowerShell: .venv\Scripts\Activate.ps1)
    ```

5.  **Install Dependencies:**
    ```bash
    # Using uv (recommended)
    uv pip install -r requirements.txt

    # OR using standard pip
    # pip install -r requirements.txt
    ```

6.  **Configure Environment Variables:**
    * **Copy the example file:** `cp .env.example .env` (or copy manually).
    * **Edit `.env`:** Open the newly created `.env` file with a text editor.
    * **Fill in required values:**
        * `GOOGLE_API_KEY`: Add your Google API Key (required if using Gemini). Get one from [Google AI Studio](https://aistudio.google.com/app/apikey).
        * `ENTREZ_EMAIL`: Add your email address (required for PubMed Tool). NCBI uses this to identify requests.
    * **Configure LLMs:**
        * `DEFAULT_LLM_ID`: Set the default model the UI should use on startup (e.g., `gemini::gemini-1.5-flash`).
        * `GEMINI_AVAILABLE_MODELS`: List the Gemini models you want available in the UI dropdown, separated by commas (e.g., `gemini-1.5-flash,gemini-1.5-pro-latest`). Ensure these are accessible with your API key.
        * `OLLAMA_AVAILABLE_MODELS`: List the Ollama models you want available, separated by commas (e.g., `gemma:2b,llama3:latest`). Ensure these are pulled and running in your Ollama instance (`ollama list`).
        * `OLLAMA_BASE_URL`: Set the correct URL for your Ollama instance if you use it (e.g., `http://localhost:11434`).
    * **(Optional) Adjust Tuning & Settings:** Modify agent parameters (`AGENT_MAX_ITERATIONS`, `AGENT_MEMORY_WINDOW_K`, temperatures), tool settings (timeouts, limits), server settings, or log level as needed. See comments in `.env.example` for details.
    * **Security:** The `.env` file is listed in `.gitignore` to prevent accidental commits of your secrets.

7.  **(If using Ollama)**
    * Install Ollama: [https://ollama.com/](https://ollama.com/)
    * Ensure the Ollama service is running.
    * **Important for Docker/WSL:** If Ollama runs as a systemd service, ensure it listens on all interfaces. Edit the service file (`sudo systemctl edit --full ollama.service`), add `Environment="OLLAMA_HOST=0.0.0.0"` under `[Service]`, then run `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.
    * Pull the models listed in `OLLAMA_AVAILABLE_MODELS`: `ollama pull <model_name>` (e.g., `ollama pull llama3:latest`).

## Running the Application

### Using Docker (Recommended Method)

Runs the backend server inside an isolated Docker container. **Highly recommended** for security and dependency management.

1.  **Prerequisites:** Ensure Docker and Docker Compose are installed.
2.  **Build and Run Backend:** From the project root directory (`ResearchAgent/`), run:
    ```bash
    docker compose up --build
    ```
    * The `--build` flag is needed the first time or after changing `Dockerfile` or `requirements.txt`.
    * Uses `network_mode: host` in `docker-compose.yml`, meaning the container shares the host network. The backend listens directly on host ports 8765 (WebSocket) and 8766 (File Server). Ensure these ports are free. This simplifies connecting to services like Ollama running directly on the host/WSL (use `http://localhost:11434` for `OLLAMA_BASE_URL`).
    * Keep this terminal running. Use `Ctrl+C` to stop.
3.  **Start Frontend Server:** Docker Compose only runs the backend. Serve the frontend files (HTML, CSS, JS) from a ***separate*** terminal in the project root:
    ```bash
    python3 -m http.server 8000
    ```
    * Keep this second terminal running.
4.  **Access the UI:** Open your web browser to `http://localhost:8000`.

**Development Workflow with Docker:**

* **Code Changes:** Changes to `./backend` code are reflected inside the container. Stop (`Ctrl+C`) and restart (`docker compose up`) the container to apply backend changes.
* **Dependency Changes:** If `requirements.txt` changes, rebuild with `docker compose up --build`.
* **Workspace & Database:** `./workspace` and `./database` are mounted as volumes, so data persists locally.

### Alternative: Running Directly on Host (Advanced / Less Secure)

**Not recommended** due to security risks of `Python_REPL` and `python_package_installer` executing directly in your host environment. **Proceed with extreme caution.**

1.  **Setup Environment:** Ensure Python 3.12+ is installed, activate a virtual environment (e.g., `uv venv`), and install dependencies (`uv pip install -r requirements.txt`).
    ```bash
    # Example activation (Linux/Mac/WSL)
    source .venv/bin/activate
    ```
2.  **Terminal 1: Start Backend Server:**
    ```bash
    python3 -m backend.server
    ```
3.  **Terminal 2: Start Frontend Server:**
    ```bash
    python3 -m http.server 8000
    ```
4.  **Access the UI:** Open `http://localhost:8000`.

## Usage & Testing

* **Create Task:** Click "+ New Task".
* **Rename Task:** Hover over a task, click the pencil icon (✏️).
* **Select Task:** Click a task to load its history.
* **Select LLM:** Use the dropdown in the chat header to choose the model for the current session.
* **Chat:** Interact with the agent. Use Up/Down arrows for input history.
* **Monitor:** Observe agent logs.
* **Artifact Viewer:** View generated images/text files using Prev/Next buttons.
* **Test PubMed Search:** Ask: `"Search PubMed for recent articles on CRISPR gene editing."`
* **Test Package Installation:** Ask: `"Install the 'numpy' python package."`
* **Test Python REPL:** Ask: `"Use the Python REPL tool to calculate 15 factorial."`
* **Test Image Generation:** Ask: `"Write a python script named 'plot.py' that uses matplotlib to create a simple sine wave plot and saves it as 'sine_wave.png'. Then execute the script using python."` (Ensure `matplotlib` is installed first).
* **Test File/PDF Reading:** Ask: `"Read the file named 'my_document.txt'"` or `"Read the file named 'research_paper.pdf'"` (assuming these files exist in the task workspace).
* **Test LLM Switching:** Select one model, ask a question. Select a different model, ask another question. Observe the agent's responses and potentially different styles.
* **Delete Task:** Click the trash icon (🗑️) next to a task (confirmation required).

## Security Warnings

* **`python_package_installer` Tool:** Installs packages directly into the backend server's Python environment. **Significant security risk if exposed.**
* **`PythonREPLTool` Tool:** Executes arbitrary Python code directly in the backend server's environment. **Significant security risk if exposed.**
* **Recommendation:** **Strongly consider running the backend server inside a Docker container**, especially when using the `python_package_installer` or `PythonREPLTool`, to isolate execution and mitigate risks. Do not expose the backend ports directly to the internet without proper authentication and authorization layers.

## Future Perspectives & Ideas

* **Streaming Output:** Ensure agent responses consistently stream token-by-token to the UI.
* **PDF Reading Enhancements:** Add options for page ranges, improve handling of complex layouts/images.
* **Drag & Drop Upload:** Allow users to upload files to the current task's workspace via drag and drop.
* **Collapse Agent Steps:** Add UI controls to collapse/expand intermediate thought/tool steps in the chat/monitor.
* **More Robust Formatting:** Use a dedicated Markdown library (e.g., `markdown-it`) for more complex rendering.
* **Domain-Specific Tools:** PubMed Central, BLAST, VCF/FASTA parsing, etc.
* **User Authentication.**
* **UI Polish & Error Handling:** Improve visual feedback and handle edge cases more gracefully.
* **Per-Task LLM Preference:** Store the last used LLM for each task.
* **Tool Configuration UI:** Allow enabling/disabling tools per task or globally.
