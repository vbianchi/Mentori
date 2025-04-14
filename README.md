# Manus AI UI Clone & LangChain Backend

This project is a functional clone of the user interface for an AI agent system, inspired by a screenshot of Manus AI. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend powered by **LangChain** to create a basic AI agent. The agent can use LLMs (Google Gemini or local Ollama) for reasoning and tools (currently a shell tool) to perform actions.

## Project Goal

The goal is to replicate the UI structure and build a functional backend agent capable of planning and executing tasks using LLMs and tools, laying the groundwork for a more complex AI agent system for specific domains like bioinformatics.

## Screenshot (Target UI)

(Please place the `image_917c03.jpg` file in the root of this repository for the image below to display correctly)

![Manus AI Screenshot](./image_917c03.jpg)

## Current Features

* **Three-Panel UI:** Replicates the Task List (left), Chat/Interaction (center), and Agent Monitor (right) panels.
* **Styling:** Dark theme implemented with CSS.
* **Basic Interactivity:** Clickable task list, functional chat input.
* **Dynamic Content:** Chat and Monitor panels updated dynamically via WebSockets with agent steps and outputs.
* **WebSocket Communication:** Real-time connection between frontend and backend.
* **LangChain Agent Backend:**
    * Uses LangChain framework for agent logic.
    * Initializes an LLM wrapper (Gemini or Ollama) based on configuration.
    * Defines tools the agent can use (currently `ShellTool`).
    * Uses a LangChain Agent Executor (ReAct based) to process user tasks.
    * Streams agent actions, tool inputs/outputs, and final answers back to the UI via WebSockets.
    * Configurable LLM provider and models via `.env` file / environment variables.
* **Dependency Management:** Uses `uv` and `requirements.txt`.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:**
    * Python 3.x, `asyncio`, `websockets`
    * **LangChain Core:** `langchain`
    * **LLM Integrations:** `langchain-google-genai`, `langchain-community` (for Ollama)
    * **Tools:** `langchain-community` (for ShellTool, etc.)
    * **Prompts:** `langchainhub`
    * **Config:** `python-dotenv`
    * **HTTP:** `httpx` (used internally by some LangChain components)
* **Environment:** `uv`
* **Protocol:** WebSockets (WS)

## Project Structure

```
manus-ai-ui-clone/
├── backend/
│   ├── init.py       # Makes 'backend' a package
│   ├── agent.py          # Creates the LangChain agent executor
│   ├── config.py         # Loads configuration (.env, env vars)
│   ├── llm_setup.py      # Initializes LangChain LLM wrappers
│   ├── server.py         # Python WebSocket server (using LangChain agent)
│   └── tools.py          # Defines LangChain tools for the agent
├── css/
│   └── style.css         # Frontend CSS styling
├── js/
│   └── script.js         # Frontend JavaScript logic
├── .venv/                # Python virtual environment (Ignored by Git)
├── .gitignore            # Files ignored by Git
├── image_917c03.jpg      # Screenshot image file (Optional)
├── index.html            # Main HTML structure for the UI
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

*(Note: `backend/llm_planners.py` has been replaced by `llm_setup.py`, `tools.py`, and `agent.py`)*

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
4.  **Create Virtual Environment:** `uv venv`
5.  **Activate Virtual Environment:** `source .venv/bin/activate`
6.  **Install Dependencies:** `uv pip install -r requirements.txt`
7.  **(If using Ollama)** Ensure Ollama is running and the desired model is pulled.
8.  **Create Backend Package Marker:** `touch backend/__init__.py` (if not already present).

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
* Observe the Monitor panel in the UI for detailed steps: Agent thoughts, tool calls (e.g., ShellTool input), tool outputs (observations).
* Observe the Chat panel for status updates and the final answer from the agent.

## Future Development

* Add more tools (web search, Python REPL, file I/O, custom bioinformatics tools).
* Implement more sophisticated agent types or prompt engineering.
* Add memory to the agent.
* Improve error handling and robustness.
* Enhance UI feedback based on agent state.
