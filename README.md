# Manus AI UI Clone & Basic Backend

This project is a functional clone of the user interface for an AI agent system, inspired by a screenshot of Manus AI (see below). It features a three-panel layout (Tasks, Chat, Monitor) and connects via WebSockets to a basic Python backend capable of handling initial task descriptions and executing shell commands.

## Project Goal

The initial goal was to replicate the UI structure and basic functionality shown in the screenshot. The project has now progressed to include a live WebSocket connection to a simple backend, laying the groundwork for building a more complex AI agent system.

## Current Features

* **Three-Panel UI:** Replicates the Task List (left), Chat/Interaction (center), and Agent Monitor (right) panels.
* **Styling:** Dark theme implemented with CSS, approximating the look and feel of the screenshot.
* **Basic Interactivity:**
    * Clickable task list items.
    * Functional chat input area (sends messages to backend).
    * Placeholder buttons log actions to the console.
* **Dynamic Content:** Chat and Monitor panels are updated dynamically with content received from the backend.
* **WebSocket Communication:** Real-time, bidirectional communication between the frontend (browser) and the Python backend using the `websockets` library.
* **Basic Backend Logic:**
    * Accepts WebSocket connections.
    * Handles initial `user_message` as a task goal.
    * Handles subsequent `user_message`s as follow-ups (basic acknowledgment).
    * Handles `run_command` messages to execute shell commands asynchronously using `asyncio.subprocess`.
    * Streams `stdout` and `stderr` from executed commands back to the frontend Monitor panel.
    * Acknowledges other basic message types (`context_switch`, `new_task`, `action_command`).
* **Dependency Management:** Python dependencies managed using `requirements.txt` and `uv` virtual environments.

## Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Backend:** Python 3.x, `asyncio`, `websockets` library
* **Environment:** `uv` (for Python virtual environment and package installation)
* **Protocol:** WebSockets (WS)

## Project Structure
```
manus-ai-ui-clone/
├── backend/
│   └── server.py         # Python WebSocket backend server
├── css/
│   └── style.css         # Frontend CSS styling
├── js/
│   └── script.js         # Frontend JavaScript logic
├── .venv/                # Python virtual environment (Created by uv, ignored by Git)
├── .gitignore            # Files/directories ignored by Git
├── image_917c03.jpg      # Screenshot image file (Add this manually)
├── index.html            # Main HTML structure for the UI
├── README.md             # This file
└── requirements.txt      # Python dependencies
```
## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd manus-ai-ui-clone
    ```
    (Replace `<your-repository-url>` with the actual URL if you host it on GitHub/GitLab etc.)

2.  **Install `uv` (if needed):**
    Follow the official instructions: [https://astral.sh/uv#installation](https://astral.sh/uv#installation)
    (Usually `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)

3.  **Create Virtual Environment:**
    Make sure you are in the project root directory (`manus-ai-ui-clone`).
    ```bash
    uv venv
    ```

4.  **Activate Virtual Environment:**
    ```bash
    # On Linux/macOS/WSL
    source .venv/bin/activate
    ```
    (Your terminal prompt should change to indicate the active environment, e.g., `(.venv)`)

5.  **Install Python Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

6.  **(Optional) Add Screenshot:** Place the `image_917c03.jpg` file into the root directory of the project.

## Running the Application

You need to run two servers simultaneously in separate terminals: the backend WebSocket server and the frontend HTTP server.

1.  **Terminal 1: Start Backend Server**
    * Navigate to the project root: `cd /path/to/manus-ai-ui-clone`
    * Activate the virtual environment: `source .venv/bin/activate`
    * Navigate to the backend directory: `cd backend`
    * Run the server: `python server.py`
    * Keep this terminal running. You should see output like `WebSocket server started on ws://localhost:8765`.

2.  **Terminal 2: Start Frontend HTTP Server**
    * Navigate to the project root: `cd /path/to/manus-ai-ui-clone`
    * (Optional but recommended) Activate the virtual environment: `source .venv/bin/activate`
    * Run the simple Python HTTP server (serves `index.html`, `css`, `js`): `python3 -m http.server 8000`
    * Keep this terminal running.

3.  **Access the UI:**
    * Open your web browser (Chrome, Firefox, Edge) and navigate to: `http://localhost:8000`

## Basic Testing

* Send a chat message through the UI input. Observe the backend logs and the UI updates indicating the task was received.
* Send subsequent chat messages to see the follow-up logic.
* (Requires Browser Console) Test command execution:
    1.  Open browser developer console (F12).
    2.  Ensure WebSocket is connected by typing `socket.readyState` (should return `1`).
    3.  Send a command: `socket.send(JSON.stringify({ type: "run_command", command: "ls -l" }));` (use appropriate commands for your OS).
    4.  Observe the command output streamed to the Monitor panel in the UI.

## Future Development

The next steps involve enhancing the backend server's agent logic:

* Implementing a proper planning module (potentially using an LLM API like Claude, Gemini, or OpenAI).
* Building out the execution module for different step types (e.g., web Browse with Playwright, file I/O, API calls).
* Developing more robust state management for tasks and plans.
* Implementing error handling and replanning capabilities.