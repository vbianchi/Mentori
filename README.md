# ResearchAgent: AI Assistant for Research Workflows

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain**. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (Shell, Web Search, Web Reader, File Read/Write, Package Installer, Python REPL, PubMed Search) to perform actions within isolated task workspaces.

## Features

* **Task Management:** Create, select, delete, and **rename** tasks. Each task maintains its own context and workspace.
* **Chat Interface:** Interact with the AI agent via a familiar chat window. Supports input history (Up/Down arrows). Basic Markdown rendering (newlines, bold, italics, code blocks, links).
* **Agent Workspace (Monitor):** View the agent's internal steps, tool usage, and outputs in a structured, styled log panel.
* **Artifact Viewer:** Displays generated `.png` images and previews common text files (`.txt`, `.py`, `.csv`, etc.) in a dedicated area below the monitor logs, with navigation for multiple artifacts.
* **Tool Integration:** Includes tools for:
    * Web Search (`duckduckgo_search`)
    * Web Page Reading (`web_page_reader`)
    * PubMed Search (`pubmed_search`)
    * File Reading (`read_file` within task workspace)
    * File Writing (`write_file` within task workspace)
    * Shell Command Execution (`workspace_shell` within task workspace, including `Rscript` if R is installed)
    * Python Package Installation (`python_package_installer`) **(Security Warning!)**
    * Python Code Execution (`Python_REPL`) **(Security Warning!)**
* **Backend:** Python backend using `websockets`, `aiohttp` (for file serving), and `LangChain`.
* **Frontend:** Simple HTML, CSS, and vanilla JavaScript.
* **LLM Flexibility:** Configurable to use Google Gemini (via API key) or a local Ollama instance.
* **Persistence:** Task list (including names) and chat/monitor history are stored locally using SQLite in the `database/` directory.
* **Task Workspaces:** File/Shell tools operate within isolated directories for each task (`workspace/<task_id>/`), created upon task selection.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:**
    * Python 3.10+ (`asyncio`, `websockets`)
    * **Web Server:** `aiohttp`, `aiohttp-cors`
    * **LangChain Core:** `langchain`
    * **LLM Integrations:** `langchain-google-genai`, `langchain-ollama`
    * **Tools:** `langchain-community` (File Tools, Search), `langchain-experimental` (Python REPL), `biopython` (PubMed)
    * **Prompts:** `langchainhub`
    * **Config:** `python-dotenv`
    * **HTTP:** `httpx`
    * **Web Parsing:** `beautifulsoup4`, `lxml`
    * **Async File I/O:** `aiofiles`
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
    git clone https://github.com/vbianchi/ResearchAgent.git
    cd ResearchAgent
    ```
2.  **Prerequisites:**
    * Ensure Python 3.10+ is installed.
    * **(Optional):** Install R and ensure `Rscript` is in PATH for R script execution.

3.  **Install `uv` (Recommended - Fast Package Installer):**
    * Follow instructions: [https://github.com/astral-sh/uv#installation](https://github.com/astral-sh/uv#installation)

4.  **Create and Activate Virtual Environment:**
    ```bash
    # Using uv (recommended)
    uv venv --python 3.12 # Or your desired Python version

    # OR using standard venv
    # python -m venv .venv

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
    * **Copy the example file:** `cp .env.example .env` (or copy manually)
    * **Edit `.env`:** Open the newly created `.env` file.
    * **Fill in required values:**
        * Add your `GOOGLE_API_KEY`. You can get one from [Google AI for Developers](https://ai.google.dev/).
        * Add your `ENTREZ_EMAIL` (required for PubMed Tool).
    * **(If using Ollama):**
        * Ensure `AI_PROVIDER=ollama` is set.
        * **Important:** If running Ollama as a service within WSL 2 and using the Docker setup below, set `OLLAMA_BASE_URL=http://localhost:11434`. The `network_mode: host` in `docker-compose.yml` allows the container to access the WSL host's localhost.
        * If Ollama runs elsewhere (different machine, different Docker container), set `OLLAMA_BASE_URL` accordingly.
        * Set `OLLAMA_MODEL` to a model you have pulled (e.g., `llama3:latest`).
    * **(Optional):** Modify other settings like `GEMINI_MODEL` if needed.
    * **Security:** The `.env` file is listed in `.gitignore` to prevent accidental commits of your secrets.

7.  **(If using Ollama)**
    * Install Ollama: [https://ollama.com/](https://ollama.com/)
    * Ensure the Ollama service is running (e.g., `sudo systemctl start ollama` if installed as a service in Linux/WSL, or run the desktop app).
    * **Important for Docker/WSL:** If Ollama was installed as a systemd service, ensure it's configured to listen on all interfaces by editing the service file (e.g., `sudo systemctl edit --full ollama.service`) and adding `Environment="OLLAMA_HOST=0.0.0.0"` under `[Service]`, then run `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.
    * Pull required models: `ollama pull <model_name>` (e.g., `ollama pull llama3:latest`).

## Running the Application

### Using Docker (Recommended Method)

This method runs the backend server inside an isolated Docker container, which is **highly recommended** for security, dependency management, and reproducibility.

1.  **Prerequisites:** Ensure Docker and Docker Compose are installed on your system. (See Docker installation guides for your OS if needed).
2.  **Build and Run:** From the project root directory (`ResearchAgent/`), run the following command in your terminal:
    ```bash
    docker compose up --build
    ```
    * The `--build` flag is only strictly necessary the first time you run this or when you change the `Dockerfile` or `requirements.txt`. Subsequent runs can often just use `docker compose up`.
    * This command will:
        * Build the Docker image using the specifications in `Dockerfile` (including installing all Python dependencies and `curl` for debugging).
        * Start the backend service defined in `docker-compose.yml`.
    * **Networking Note:** The `docker-compose.yml` is configured with `network_mode: host`. This means the container shares the network of the host (your WSL environment if using Docker Desktop on Windows/Mac). The backend will listen directly on host ports 8765 (WebSocket) and 8766 (File Server). Ensure these ports are free on your host/WSL. This mode simplifies connecting to services like Ollama running directly in the same WSL environment (use `http://localhost:11434` for `OLLAMA_BASE_URL`).
    * You will see logs from the backend server in this terminal. Keep it running. Use `Ctrl+C` to stop the container gracefully.
3.  **Start Frontend Server:** Docker Compose (as configured) only runs the backend. You still need to serve the frontend files (HTML, CSS, JS). Open a ***separate*** terminal, navigate to the project root directory (`ResearchAgent/`), and run the simple Python HTTP server:
    ```bash
    python3 -m http.server 8000
    ```
    * Keep this second terminal running.
4.  **Access the UI:** Open your web browser to `http://localhost:8000`.

**Development Workflow with Docker:**

* **Code Changes:** Thanks to the volume mounts defined in `docker-compose.yml`, changes made to your Python code in the local `./backend` directory are reflected immediately inside the running container. You usually only need to stop (`Ctrl+C`) and restart (`docker compose up`) the container for the backend server process to pick up the changes.
* **Dependency Changes:** If you modify `requirements.txt`, you need to rebuild the image using `docker compose up --build`.
* **Workspace & Database:** Files created by the agent in `./workspace` and the database in `./database` will persist locally on your machine between container runs because these directories are also mounted as volumes.

### Alternative: Running Directly on Host (Advanced / Less Secure)

You can run the backend server directly on your host machine, but this is **not recommended** due to the significant security risks associated with the `Python_REPL` and `python_package_installer` tools executing code and installing packages directly in your host environment. **Proceed with caution only if you fully understand the risks.**

1.  **Setup Environment:** Ensure you have Python 3.12+ installed and have created and activated a virtual environment (e.g., using `uv venv` or `python3 -m venv .venv`) and installed all dependencies (`uv pip install -r requirements.txt` or `pip install -r requirements.txt`).
    ```bash
    # Example activation (Linux/Mac/WSL)
    source .venv/bin/activate
    ```
2.  **Terminal 1: Start Backend Server:**
    ```bash
    python3 -m backend.server
    ```
    * Keep this terminal running.
3.  **Terminal 2: Start Frontend Server:**
    ```bash
    python3 -m http.server 8000
    ```
    * Keep this second terminal running.
4.  **Access the UI:** Open your web browser to `http://localhost:8000`.

## Usage & Testing

* **Create Task:** Click "+ New Task". "Task - 1" (or subsequent number) is created automatically on first launch if no tasks exist.
* **Rename Task:** Hover over a task in the list and click the pencil icon (✏️). Enter the new name in the prompt.
* **Select Task:** Click a task to load its history and set its workspace.
* **Chat:** Interact with the agent. Use Up/Down arrows for input history.
* **Monitor:** Observe structured logs (tool usage, system messages).
* **Artifact Viewer:** View generated images or text files using the Prev/Next buttons.
* **Test PubMed Search:** Ask: `"Search PubMed for recent articles on CRISPR gene editing."`
* **Test Package Installation:** Ask: `"Install the 'numpy' python package."`
* **Test Python REPL:** Ask: `"Use the Python REPL tool to calculate 15 factorial."`
* **Test Image Generation:** Ask: `"Write a python script named 'plot.py' that uses matplotlib to create a simple sine wave plot and saves it as 'sine_wave.png'. Then execute the script using python."` (Ensure `matplotlib` is installed first).
* **Delete Task:** Click the trash icon (🗑️) next to a task (confirmation required).

## Security Warnings

* **`python_package_installer` Tool:** Installs packages directly into the backend server's Python environment.
* **`PythonREPLTool` Tool:** Executes arbitrary Python code directly in the backend server's environment. This is a **significant security risk**.
* **Recommendation:** **Strongly consider running the backend server inside a Docker container**, especially when using the `python_package_installer` or `PythonREPLTool`, to isolate execution and mitigate risks.

## Future Perspectives & Ideas

* **LLM Selection UI:** Allow users to select specific Gemini/Ollama models from a dropdown in the chat interface.
* **PDF Reading Tool:** Enhance the `read_file` tool or add a new tool to directly extract text from PDF files.
* **Drag & Drop Upload:** Allow users to drag files directly onto the UI to upload them to the current task's workspace.
* **Collapse Agent Steps:** Add UI controls to collapse/expand the agent's intermediate thought/tool usage steps in the chat for a cleaner view.
* **Configuration File:** Move more hardcoded parameters (timeouts, limits, agent settings) to the `.env` file.
* **ERIC/DOAJ Tools:** Add tools for searching these free databases.
* **Enhanced Monitor/Artifact Viewer:** Filtering, search, more file types, download button.
* **More Robust Formatting:** Use a dedicated Markdown library (e.g., `markdown-it`) for more complex rendering.
* **Domain-Specific Tools:** PubMed Central, BLAST, VCF/FASTA parsing, etc.
* **User Authentication.**
* **UI Polish.**
