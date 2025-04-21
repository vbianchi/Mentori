# Manus AI UI Clone & LangChain Backend

This project is a functional clone of the user interface for an AI agent system, inspired by a screenshot of Manus AI. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain** to create a basic AI agent. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (Shell, Web Search, Web Reader, File Read/Write) to perform actions.

## Project Goal

The initial goal was to replicate the UI structure. The project has now progressed to include a live WebSocket connection to a backend that can leverage LLMs for basic task planning, use tools, remember conversation context, and execute simple commands and file operations, laying the groundwork for a more complex AI agent system for specific domains like bioinformatics.

## Screenshot (Target UI)

(Please place the `image_917c03.jpg` file in the root of this repository for the image below to display correctly)

![Manus AI Screenshot](./image_917c03.jpg)

## Current Features

* **Three-Panel UI:** Replicates the Task List (left), Chat/Interaction (center), and Agent Workspace (right - Monitor) panels.
* **Styling:** Dark theme implemented with CSS.
* **Basic Interactivity:** Clickable task list, functional chat input.
* **Dynamic Content:** Chat and Monitor panels updated dynamically via WebSockets with agent steps, tool outputs, and final answers.
* **WebSocket Communication:** Real-time connection between frontend and backend.
* **LangChain Agent Backend:**
    * Uses LangChain framework for agent logic.
    * Includes basic conversation memory (remembers recent interactions within a session).
    * Initializes an LLM wrapper (Gemini or Ollama) based on configuration.
    * Defines tools the agent can use (currently `ShellTool`, `DuckDuckGoSearchRun`, `WebPageReaderTool`, `ReadFileTool`, `WriteFileTool` [custom]).
    * Uses a LangChain Agent Executor (ReAct Chat based) to process user tasks.
    * Streams agent actions, tool inputs/outputs, and final answers back to the UI via WebSockets using a custom Callback Handler.
* **Workspace:** File operations using `ReadFileTool` and `WriteFileTool` are restricted to a `workspace/` directory for safety. `ShellTool` still operates from the project root.
* **Dependency Management:** Uses `uv` and `requirements.txt`.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:**
    * Python 3.x, `asyncio`, `websockets`
    * **LangChain Core:** `langchain`
    * **LLM Integrations:** `langchain-google-genai`, `langchain-ollama`
    * **Tools:** `langchain-community` (for ShellTool, File Tools, Search), `langchain-experimental` (required by ShellTool)
    * **Prompts:** `langchainhub`
    * **Config:** `python-dotenv`
    * **HTTP:** `httpx`
    * **Web Parsing:** `beautifulsoup4`, `lxml`
    * **Async File I/O:** `aiofiles`
    * **Plotting (Example):** `matplotlib` (if using plot generation tools/examples)
* **Environment:** `uv`
* **Protocol:** WebSockets (WS)

## Project Structure

```
manus-ai-ui-clone/
├── backend/
│   ├── init.py       # Makes 'backend' a package
│   ├── agent.py          # Creates the LangChain agent executor
│   ├── callbacks.py      # WebSocket callback handler for LangChain
│   ├── config.py         # Loads configuration (.env, env vars)
│   ├── llm_setup.py      # Initializes LangChain LLM wrappers
│   ├── server.py         # Python WebSocket backend server (using LangChain agent)
│   └── tools.py          # Defines LangChain tools for the agent
├── workspace/            # Safe directory for agent file operations (Ignored by Git)
├── css/
│   └── style.css         # Frontend CSS styling
├── js/
│   └── script.js         # Frontend JavaScript logic
├── .venv/                # Python virtual environment (Ignored by Git)
├── .gitignore            # Files ignored by Git
├── index.html            # Main HTML structure for the UI
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd manus-ai-ui-clone
    ```
2.  **Install `uv` (if needed):** See [https://astral.sh/uv#installation](https://astral.sh/uv#installation).
3.  **Create `.env` File:**
    * Create `.env` in the project root. Add `GOOGLE_API_KEY=YOUR_ACTUAL_GOOGLE_API_KEY`.
    * See Configuration section for optional variables (`AI_PROVIDER`, etc.).
    * Ensure `.env` is in `.gitignore`.
4.  **Create Workspace Directory:**
    ```bash
    mkdir workspace
    ```
    *(Ensure `workspace/` is added to your `.gitignore` file)*
5.  **Create Virtual Environment:** `uv venv`
6.  **Activate Virtual Environment:** `source .venv/bin/activate`
7.  **Install Dependencies:** `uv pip install -r requirements.txt`
8.  **(If using Ollama)** Ensure Ollama is running and the desired model is pulled.
9.  **Create Backend Package Marker:** `touch backend/__init__.py` (if not already present).

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
    * Keep running. Observe logs for agent activity.

2.  **Terminal 2: Start Frontend HTTP Server**
    * (Optional) Activate environment: `source .venv/bin/activate`
    * Run server: `python3 -m http.server 8000`
    * Keep running.

3.  **Access the UI:** Open browser to `http://localhost:8000`.

## Basic Testing

* Send a chat message with a task (e.g., "What is the capital of France?", "List files in the current directory.").
* Observe the Monitor panel for detailed steps: Agent thoughts, tool calls (e.g., ShellTool input), tool outputs (observations).
* Observe the Chat panel for status updates and the final answer from the agent.
* **Test File Read:** Manually create a file `workspace/hello.txt` with text. Ask: `"Read the file hello.txt"`. Check Monitor for `ReadFileTool` usage and Chat for content.
* **Test File Write:** Ask: `"Write 'Test successful' to a file named output.txt"`. Agent should use `write_file` tool with input `'output.txt:::Test successful'`. Check `workspace/output.txt`.
* **Test Search:** Ask: `"Search the web for bioinformatics news"`. Check Monitor for `duckduckgo_search` usage.
* **Test Web Reader:** Ask: `"Summarize the content of https://ollama.com/"`. Check Monitor for `web_page_reader` usage.

## Future Development

* Create custom shell tool operating within the workspace directory.
* Add more execution capabilities (Python REPL, more complex file I/O, API calls).
* Implement plan execution logic (iterating through steps generated by AI).
* Improve state management and error handling.
* Refine AI interaction and prompt engineering.
* Add UI elements for task management (left panel).
* Implement UI history cycling for chat input.
* Implement Playwright integration for visual feedback in Monitor panel.
