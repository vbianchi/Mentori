# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
**Targeting Version 2.5.3**

**Recent Developments (Leading to v2.5.3 Target):**

* **Core Bug Fixes & Feature Verification (Complete):**
    * Resolved critical `IndentationError` issues in `backend/message_processing/agent_flow_handlers.py`.
    * `deep_research_synthesizer` & `write_file` Flow Fully Functional.
* **Chat UI/UX Refinement (Design Solidified, Backend & Frontend Implementation Next):**
    * **New Vision (Inspired by `manus.ai` and iterative refinement, target: `simulation_option6.html`):** Aiming for a highly intuitive and clear chat interface. This involves:
        * **User Messages:** Right-aligned with a bubble and a right-hand side-line matching the user's accent color.
        * **System Messages (Status, Plan Proposals, Final Agent Response):** These messages (e.g., "Loading history...", plan proposal blocks, final agent summary) will feature a unified blue outer left-hand side-line. Plan proposals and final agent responses will have distinct background bubbles.
        * **Major Step Announcements:** Messages like "Step 1/N: Doing X" will appear left-aligned *without* a side-line or background bubble, with the title in bold.
        * **Nested Sub-Statuses & Agent Thoughts:**
            * Significant agent sub-statuses (e.g., "Controller: Validating step...", "Executor: Using tool Y...") will appear as new, sequential messages *indented under their parent major step announcement*. They will be italicized, have no background bubble, and feature a component-specific colored left-hand side-line.
            * Verbose "thoughts" or preliminary outputs from agent components (e.g., Controller's reasoning) will also be displayed indented under the relevant major step. They will have normal font, no bubble, a component-specific colored left-hand side-line, a label (e.g., "Controller thought:"), and their content presented in a distinct dark box (similar to a `<pre>` block).
        * **Persistent Bottom "Thinking" Line:** A single line at the very bottom of the scrollable chat area for low-level, rapidly updating "Thinking (LLM)..." statuses. This line will update in place and feature a dynamic, component-specific colored left-hand side-line.
    * **Backend Support (Partially Implemented, Enhancements Required):**
        * `callbacks.py` and `agent_flow_handlers.py` send structured `agent_thinking_update` messages with `component_hint` and new `agent_major_step_announcement` types.
        * **Persistence Strategy:** Backend logic (in `server.py`, `task_handlers.py`, `db_utils.py`) will be enhanced to save all new message types (major steps, sub-statuses, agent thoughts) to the database with appropriate structures and `message_type` identifiers. These will be reloaded with chat history to ensure full persistence.
* **Plan Proposal UI & Persistence (Complete):** Remains functional.
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
    * Chat Interface with Markdown rendering, input history, interactive plan proposals.
    * **Chat UI Target (v2.5.3):** A refined interface as per `simulation_option6.html` (detailed above and in `BRAINSTORM.md`), featuring clear visual hierarchy for steps, sub-statuses, agent thoughts, and a persistent bottom thinking line. All chat elements will be persistent across sessions.
    * Role-Specific LLM Selection.
    * Monitor Panel for structured agent logs.
    * Artifact Viewer for text/image/PDF outputs.
    * Token Usage Tracking.
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend with refactored message handlers.
    * LangChain for P-C-E-E pipeline.
    * Task-specific, isolated workspaces with persistent history (SQLite).
    * **Tool Integration Fixed:** Robust input and output handling for complex tools.
    * **Message Structure & Persistence:** Refined WebSocket messages (`agent_major_step_announcement`, `agent_thinking_update` with `component_hint` and `sub_type`) to support the new UI vision. All chat-relevant messages, including steps, sub-statuses, and thoughts, will be saved to and reloaded from the database.
3.  **Tool Suite (`backend/tools/`):**
    * `deep_research_synthesizer` and `write_file` are working correctly in sequence. Other tools remain functional.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

## Project Structure

(Key files for upcoming Chat UI changes: `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/css/style.css`. Backend: `backend/db_utils.py`, `backend/message_processing/task_handlers.py`, `backend/message_processing/agent_flow_handlers.py`, `backend/callbacks.py`)


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
└── simulation_option6.html                # Conceptual: Visual mock-up of the target chat UI (described in BRAINSTORM.md)
```

## Setup Instructions & Running the Application

(No changes - these remain the same as provided by the user)

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Fixes)

* **IMPLEMENT (High Priority): New Chat UI Rendering & Persistence:**
    * **Issue:** Current chat UI does not yet reflect the `simulation_option6.html` design (unified outer blue lines, no line on major steps, nested/indented component-specific lines for sub-statuses & thoughts, user message right line, persistent bottom thinking line, consistent thought styling, and full message persistence).
    * **Goal:** Update `script.js`, `chat_ui.js`, and `style.css` based on the vision captured in `simulation_option6.html` and our detailed plan. Implement backend changes for saving and loading all new message structures to ensure full persistence.
    * **Status:** Backend sends some foundational messages. Significant frontend implementation and backend persistence enhancements are the next major tasks.
* **BUG FIX (Medium Priority): Chat Input Unresponsive:**
    * **Issue:** After a task completes, chat input sometimes remains disabled.
    * **Goal:** Ensure `StateManager.isAgentRunning` is correctly reset and UI re-enables input.
* **DEBUG (Medium Priority): Monitor Log Color-Coding:**
    * **Issue:** Visual differentiation by `log_source` in the Monitor Log is not yet appearing correctly.
    * **Goal:** Implement effective color-coding.
    * **Action:** Create/Debug CSS rules in `style.css`.
* **Fix (Low Priority): `<strong>` Tag Rendering in Chat:**
    * **Issue:** User noted some HTML tags (like `<strong>`) not rendering correctly.
    * **Goal:** Ensure `innerHTML` is consistently used for content processed by `formatMessageContentInternal` in `chat_ui.js`.

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on implementing the new Chat UI rendering logic on the frontend and the corresponding persistence mechanisms on the backend. Following that, efforts will target the remaining known issues.
For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
