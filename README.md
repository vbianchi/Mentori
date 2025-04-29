# ResearchAgent: AI Assistant for Research Workflows

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain**. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (Shell, Web Search, Web Reader, File Read/Write, Package Installer, Python REPL, PubMed Search) to perform actions within isolated task workspaces.

## Features

* **Task Management:** Create, select, and delete tasks. Each task maintains its own context and workspace.
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
* **Persistence:** Task list and chat/monitor history are stored locally using SQLite in the `database/` directory.
* **Task Workspaces:** File/Shell tools operate within isolated directories for each task (`workspace/<task_id>/`).

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
    * **(Optional):** Uncomment and modify other settings (`AI_PROVIDER`, `OLLAMA_MODEL`, etc.) if needed.
    * **Security:** The `.env` file is listed in `.gitignore` to prevent accidental commits of your secrets.

7.  **(If using Ollama)**
    * Install Ollama: [https://ollama.com/](https://ollama.com/)
    * Ensure the Ollama service is running.
    * Pull required models: `ollama pull <model_name>` (e.g., `ollama pull gemma:2b`).

## Configuration Details (`env` file)

* `GOOGLE_API_KEY`: **Required if using Gemini.** Your API key from [Google AI for Developers](https://ai.google.dev/).
* `ENTREZ_EMAIL`: **Required for PubMed Tool.** Your email address for NCBI API identification (they use it to contact you if there are issues with your requests).
* `AI_PROVIDER`: (Optional) `gemini` (default) or `ollama`.
* `GEMINI_MODEL`: (Optional) Default `gemini-1.5-flash-latest`.
* `OLLAMA_BASE_URL`: (Optional) Default `http://localhost:11434`.
* `OLLAMA_MODEL`: (Optional) Default `gemma:2b`. Ensure this model is pulled in Ollama.

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
        * Build the Docker image using the specifications in `Dockerfile` (including installing all Python dependencies).
        * Start the backend service defined in `docker-compose.yml`.
    * You will see logs from the backend server in this terminal. The WebSocket server will be available at `ws://localhost:8765` and the file server at `http://localhost:8766` (mapping from inside the container).
    * Keep this terminal running. Use `Ctrl+C` to stop the container gracefully when you are finished.
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

* **Create Task:** Click "+ New Task". "Task - 1" is created automatically on first launch if no tasks exist.
* **Select Task:** Click a task to load its history and set its workspace.
* **Chat:** Interact with the agent. Use Up/Down arrows for input history.
* **Monitor:** Observe structured logs (tool usage, system messages).
* **Artifact Viewer:** View generated images or text files using the Prev/Next buttons.
* **Test PubMed Search:** Ask: `"Search PubMed for recent articles on CRISPR gene editing."`
* **Test Package Installation:** Ask: `"Install the 'numpy' python package."`
* **Test Python REPL:** Ask: `"Use the Python REPL tool to calculate 15 factorial."`
* **Test Image Generation:** Ask: `"Write a python script named 'plot.py' that uses matplotlib to create a simple sine wave plot and saves it as 'sine_wave.png'. Then execute the script using python."` (Ensure `matplotlib` is installed first).
* **Delete Task:** Click the trash icon (confirmation required).

## Security Warnings

* **`python_package_installer` Tool:** Installs packages directly into the backend server's Python environment.
* **`PythonREPLTool` Tool:** Executes arbitrary Python code directly in the backend server's environment. This is a **significant security risk**.
* **Recommendation:** **Strongly consider running the backend server inside a Docker container (Phase 2)**, especially when using the `python_package_installer` or `PythonREPLTool`, to isolate execution and mitigate risks.

## Future Perspectives & Ideas

* **Containerization (Recommended Next Step):** Run the backend in Docker.
* **ERIC/DOAJ Tools:** Add tools for searching these free databases.
* **Task Renaming.**
* **Enhanced Monitor/Artifact Viewer:** Filtering, search, more file types, download.
* **More Robust Formatting:** Use a dedicated Markdown library.
* **Domain-Specific Tools:** PubMed Central, BLAST, VCF/FASTA parsing, etc.
* **User Authentication.**
* **UI Polish.**
