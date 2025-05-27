# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
**Targeting Version 2.5.3**

**Recent Developments (Leading to v2.5.3 Target):**

* **Core Bug Fixes & Feature Verification (Complete):**
    * Resolved critical `IndentationError` issues in `backend/message_processing/agent_flow_handlers.py`, enabling stable plan execution.
    * **`deep_research_synthesizer` & `write_file` Flow Fully Functional:**
        * The Controller now robustly provides correctly formatted JSON string input to `deep_research_synthesizer`.
        * The ReAct agent (`agent.py`) prompt has been significantly improved to ensure it outputs the direct raw content from tools as its `Final Answer` for a step.
        * The Step Evaluator (`evaluator.py`) prompt is stricter in verifying actual content generation against expected outcomes.
        * End-to-end execution of plans involving `deep_research_synthesizer` (generating a report) followed by `write_file` (saving that report) is now working correctly, with the actual content being saved to the file.
* **Chat UI/UX Refinement (Design Solidified, Backend Ready, Frontend Implementation Next):**
    * **New Vision (Inspired by `manus.ai` and User Feedback):** Aiming for a cleaner, more intuitive chat interface. This involves:
        * **Sequential Main Messages:** User inputs, major plan step announcements (e.g., "Step 1/N: Doing X"), and significant agent sub-statuses (e.g., "Controller: Validating step...", "Executor: Using tool Y...", "Evaluator: Step Z complete.") will appear sequentially in the main chat area. Each of these messages will have a colored side-line indicating the source/component (e.g., Planner blue, Controller orange, Executor green, Tool teal, Evaluator purple, System grey) and will *not* have a background bubble (except for user messages and the final agent conclusive message).
        * **Persistent Bottom "Thinking" Line:** A single, unobtrusive line at the very bottom of the chat area will be dedicated to displaying low-level, rapidly updating "Thinking (LLM)...", "LLM complete.", or "Tool X processing..." statuses from `callbacks.py`. This line will update in place and also feature a colored side-line corresponding to the active component.
        * **Final Agent Message:** Will appear in a distinct, styled bubble with its own colored side-line.
    * **`simulation.html` (Conceptual Guide):** The vision for this UI is captured in a conceptual HTML/Markdown mock-up (which could be saved as `simulation.html` or is detailed in `BRAINSTORM.md`). It illustrates the desired flow with user messages (bubbled), agent major step announcements (left-aligned, no bubble, component-colored side-line, bold title), sequential significant sub-status updates (also left-aligned, no bubble, italicized, with component-colored side-lines), the persistent bottom thinking line, and the final agent response in a distinct bubble.
    * **Backend Support Implemented:**
        * `callbacks.py`: Updated to send more structured `agent_thinking_update` messages with `component_hint` for frontend styling. Error reporting refined.
        * `agent_flow_handlers.py`: Updated to send new `agent_major_step_announcement` message type for each plan step. `agent_thinking_update` messages now also include `component_hint`. Final plan output logic improved.
        * **Status Message Persistence (Backend Complete):** Backend logic (in `server.py` and `task_handlers.py`) has been updated to save `status_message` types to the database and reload them with chat history, making them persistent across page refreshes.
* **Plan Proposal UI & Persistence (Complete):** Remains functional as previously developed.
* **Monitor Log Enhancements (Ongoing):**
    * Backend sends `log_source`. Frontend `monitor_ui.js` adds CSS classes. CSS styling for colors is the next step here.

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps.
3.  **User Confirmation (for plans)**: The proposed plan is shown to the user for approval.
4.  **Execution**: A Controller validates each step, and an Executor (ReAct agent) carries out the action, using tools as needed. A Step Evaluator assesses each step's outcome, allowing for retries.
5.  **Overall Evaluation**: A final assessment of the plan's success is provided.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`.
For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    * Task Management with persistent storage and reliable UI updates.
    * Chat Interface with Markdown rendering, input history, interactive plan proposals, and agent status updates.
    * **Chat UI Target:** Aiming for a `manus.ai`-style flow with sequential step/status messages and a persistent bottom thinking line, as detailed in the conceptual `simulation.html` (described in `BRAINSTORM.md`).
    * Role-Specific LLM Selection.
    * Monitor Panel for structured agent logs.
    * Artifact Viewer for text/image/PDF outputs.
    * Token Usage Tracking.
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend with refactored message handlers.
    * LangChain for P-C-E-E pipeline.
    * Task-specific, isolated workspaces with persistent history (SQLite).
    * **Tool Integration Fixed:** Robust input and output handling for complex tools like `deep_research_synthesizer` and `write_file`.
    * **Message Structure:** Refined WebSocket messages (`agent_major_step_announcement`, `agent_thinking_update` with `component_hint`) to support the new UI vision.
    * **Persistent Status Messages:** Critical status messages (e.g., "Loading history", "Plan stopped") are now saved and reloaded with chat history.
3.  **Tool Suite (`backend/tools/`):**
    * `deep_research_synthesizer` and `write_file` are working correctly in sequence. Other tools remain functional.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

## Project Structure

(Key files recently focused on: `backend/callbacks.py`, `backend/agent_flow_handlers.py`, `backend/server.py`, `backend/message_processing/task_handlers.py`. Next: `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/css/style.css`)

```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # Updated ReAct prompt for direct tool output
│   ├── callbacks.py         # Updated for structured thinking updates & log_source
│   ├── config.py
│   ├── controller.py        # Enhanced prompt for JSON tool inputs
│   ├── db_utils.py
│   ├── evaluator.py         # Stricter prompt for content verification
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py # Sends 'agent_major_step_announcement', refined thinking updates
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py     # Updated to load/save status_messages from history
│   ├── planner.py
│   ├── server.py                # Updated to save status_messages
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py # Input schema `query`, saves report
│       ├── playwright_search.py
│       ├── standard_tools.py
│       └── tavily_search_tool.py
├── css/
│   └── style.css                # Next: To be updated for new chat UI styles
├── js/
│   ├── script.js                # Next: To dispatch new message types to chat_ui.js
│   └── ui_modules/
│       └── chat_ui.js           # Next: To implement new rendering logic
├── BRAINSTORM.md                  # Updated with new UI vision
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                      # This file
├── ROADMAP.md                     # Updated with new UI vision
└── simulation.html                # Conceptual: Visual mock-up of the target chat UI (described in BRAINSTORM.md)
```

## Setup Instructions & Running the Application

(No changes - these remain the same as provided by the user)

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Fixes)

* **IMPLEMENT (High Priority): New Chat UI Rendering:**
    * **Issue:** Current chat UI does not yet reflect the `manus.ai`-inspired design (sequential steps, significant sub-statuses as distinct messages, persistent bottom thinking line).
    * **Goal:** Update `script.js`, `chat_ui.js`, and `style.css` based on the vision captured in the conceptual `simulation.html` (described in `BRAINSTORM.md`) and our discussions.
    * **Status:** Backend now sends appropriate messages (`agent_major_step_announcement`, thinking updates with `component_hint`, persistent status messages). Frontend implementation is the next major task.
* **BUG FIX (Medium Priority): Chat Input Unresponsive:**
    * **Issue:** After a task completes, chat input sometimes remains disabled.
    * **Goal:** Ensure `StateManager.isAgentRunning` is correctly reset and UI re-enables input.
* **DEBUG (Medium Priority): Monitor Log Color-Coding:**
    * **Issue:** Visual differentiation by `log_source` in the Monitor Log is not yet appearing correctly.
    * **Goal:** Implement effective color-coding.
    * **Action:** Create/Debug CSS rules in `style.css`. Verify `log_source` consistency from all backend logging points.
* **Fix (Low Priority): `<strong>` Tag Rendering in Chat:**
    * **Issue:** User noted some HTML tags (like `<strong>`) not rendering correctly in specific chat messages.
    * **Goal:** Ensure `innerHTML` is consistently used for content processed by `formatMessageContentInternal` in `chat_ui.js`.

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on implementing the new Chat UI rendering logic on the frontend, using the user-provided baseline files for `script.js`, `chat_ui.js`, and `style.css` as the starting point. Following that, efforts will target the remaining known issues like chat input responsiveness and monitor log styling.
For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
