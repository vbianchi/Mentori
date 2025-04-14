# Manus AI UI Clone & Basic Backend

This project is a functional clone of the user interface for an AI agent system, inspired by a screenshot of Manus AI. It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a Python backend capable of generating task plans using AI (Google Gemini or local Ollama) and executing shell commands.

## Project Goal

The initial goal was to replicate the UI structure. The project has now progressed to include a live WebSocket connection to a backend that can leverage LLMs for basic task planning and execute simple commands, laying the groundwork for a more complex AI agent system.

## Screenshot (Target UI)

(Please place the `image_917c03.jpg` file in the root of this repository for the image below to display correctly)

![Manus AI Screenshot](./image_917c03.jpg)

## Current Features

* **Three-Panel UI:** Replicates the Task List (left), Chat/Interaction (center), and Agent Monitor (right) panels.
* **Styling:** Dark theme implemented with CSS.
* **Basic Interactivity:** Clickable task list, functional chat input, basic button actions.
* **Dynamic Content:** Chat and Monitor panels updated dynamically via WebSockets.
* **WebSocket Communication:** Real-time connection between frontend and backend.
* **AI Planning:**
    * Accepts initial user message as a task goal.
    * Calls a configured LLM (Google Gemini or Ollama) to generate a step-by-step plan.
    * Displays the generated plan in the chat.
    * Configurable via `.env` file / environment variables.
* **Command Execution:** Handles `run_command` messages to execute shell commands asynchronously, streaming output to the Monitor panel.
* **Dependency Management:** Uses `uv` and `requirements.txt`.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:** Python 3.x, `asyncio`, `websockets`, `google-generativeai`, `python-dotenv`, `httpx`
* **Environment:** `uv`
* **Protocol:** WebSockets (WS)

## Project Structure

```
manus-ai-ui-clone/
├── backend/
│   ├── init.py       # Makes 'backend' a package
│   ├── config.py         # Loads configuration (.env, env vars)
│   ├── llm_planners.py   # LLM interaction logic (Gemini, Ollama)
│   └── server.py         # Python WebSocket backend server
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

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd manus-ai-ui-clone
    ```
2.  **Install `uv` (if needed):** See [https://astral.sh/uv#installation](https://astral.sh/uv#installation).
3.  **Create `.env` File:**
    * Create a file named `.env` in the project root (`manus-ai-ui-clone/`).
    * Add your Google Gemini API key:
        ```env
        GOOGLE_API_KEY=YOUR_ACTUAL_GOOGLE_API_KEY
        ```
    * **(Optional)** Add other configuration variables to override defaults (see Configuration section below).
    * **Important:** Do NOT commit the `.env` file to Git. Ensure it's listed in `.gitignore`.
4.  **Create Virtual Environment:**
    ```bash
    uv venv
    ```
5.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
6.  **Install Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```
7.  **(If using Ollama)** Ensure your Ollama instance is running and the desired model (e.g., `gemma:2b`, `llama3:8b`) is pulled (`ollama pull gemma:2b`).
8.  **Create Backend Package Marker:** *(Added Step)*
    ```bash
    touch backend/__init__.py
    ```

## Configuration

The backend behaviour can be configured using environment variables or by setting them in the `.env` file:

* `GOOGLE_API_KEY` (Required if using Gemini): Your API key from Google AI Studio or Google Cloud.
* `AI_PROVIDER` (Optional): Set to `gemini` (default) or `ollama` to choose the planning LLM.
* `GEMINI_MODEL` (Optional): Specify the Gemini model name (default: `gemini-1.5-flash-latest`).
* `OLLAMA_BASE_URL` (Optional): The base URL for your running Ollama instance (default: `http://localhost:11434`).
* `OLLAMA_MODEL` (Optional): The name of the Ollama model to use (default: `gemma:2b`). Make sure this model is available in your Ollama instance.

## Running the Application

Run the backend and frontend servers in separate terminals from the **project root directory** (`manus-ai-ui-clone/`).

1.  **Terminal 1: Start Backend Server**
    * Make sure you are in the project root directory (`manus-ai-ui-clone/`).
    * Activate environment: `source .venv/bin/activate`
    * **Run server as a module:** *(Changed Command)*
      ```bash
      python -m backend.server
      ```
    * Keep running.

2.  **Terminal 2: Start Frontend HTTP Server**
    * Make sure you are in the project root directory (`manus-ai-ui-clone/`).
    * (Optional) Activate environment: `source .venv/bin/activate`
    * Run server: `python3 -m http.server 8000`
    * Keep running.

3.  **Access the UI:** Open browser to `http://localhost:8000`.

## Basic Testing

* Send your first chat message. This will be treated as the task goal. Observe the status messages and monitor logs. The backend should call the configured AI (Gemini by default) to generate a plan, which will then be displayed in the chat.
* (Requires Browser Console) Test command execution:
    1.  Check connection: `socket.readyState` (should be `1`).
    2.  Send command: `socket.send(JSON.stringify({ type: "run_command", command: "ls -la" }));`
    3.  Observe output streamed to the Monitor panel.

## Future Development

* Implement plan execution logic (iterate through steps generated by AI).
* Add more execution capabilities (web browsing via Playwright, file I/O).
* Improve state management and error handling.
* Refine AI interaction and prompt engineering.