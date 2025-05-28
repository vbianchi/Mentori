# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. [cite: 5, 65] It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain. [cite: 65]
Targeting Version 2.5.3 [cite: 66]

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete):**
    -   Resolved critical `IndentationError` issues in backend. [cite: 67]
    -   `deep_research_synthesizer` & `write_file` Flow: Core logic for actual execution is now in place, replacing placeholder outputs. [cite: 67]
    -   `UnboundLocalError` in `callbacks.py` related to token usage parsing: **FIXED.** [cite: 68]
-   **Chat UI/UX Refinement (Implementation & Fixes Ongoing):**
    -   **Visual Design (Target: `simulation_option6.html`):**
        -   User messages with right side-lines, system/plan/final messages with unified blue outer left side-lines, no side-lines for major step announcements, and nested/indented component-specific lines for sub-statuses & agent thoughts are implemented. [cite: 69]
        -   HTML tags (`<strong>`, `<em>`) are now rendering correctly in the chat. [cite: 69]
    -   **Backend Support & Persistence:**
        -   Backend sends structured messages for steps, sub-statuses, and thoughts. [cite: 70]
        -   Persistence for these new message types in the database and reloading into history is implemented. [cite: 71]
    -   **Plan Proposal UI & Persistence (Complete):** Remains functional. [cite: 72]
    -   **Token Counter UI & Functionality (FIXED):** Expandable UI for token breakdown by role is implemented. [cite: 23] Token counting functionality now works for all individual agent/LLM roles (Intent Classifier, Planner, Controller, Executor, Evaluator) and is accurately displayed in the UI's per-role breakdown. [cite: 28, 24, 25] Persistence for displayed totals per task is working. [cite: 24]
## Core Architecture & Workflow

(No changes to this section)

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Creation, deletion, renaming functional. [cite: 74] Workspace folders managed correctly. [cite: 74]
    -   Chat Interface:
        -   **Rendering:** Correctly displays styled HTML tags. [cite: 75] Implements the new visual hierarchy for steps, sub-statuses, and thoughts as per `simulation_option6.html`. [cite: 75]
        -   **Persistence:** All chat message types, including the new structured ones, are saved and reloaded. [cite: 76]
        -   Role-Specific LLM Selection. [cite: 77]
    -   Monitor Panel for structured agent logs. [cite: 78]
    -   Artifact Viewer. [cite: 78]
    -   **Token Usage Tracking (FIXED & COMPLETE):** Accurately tracks and displays token usage per LLM call, broken down by agent role, and aggregated per task. [cite: 78, 28]
    -   File upload capability. [cite: 79]
2.  **Backend Architecture & Logic:**
    -   Modular Python backend. LangChain for P-C-E-E pipeline. [cite: 79]
    -   Task-specific, isolated workspaces with persistent history (SQLite). [cite: 80]
    -   **Actual Plan Execution:** Backend now attempts full execution of plan steps, including tool usage and LLM generation, replacing previous placeholder logic. [cite: 81]
    -   **Message Structure & Persistence:** Implemented for all chat-relevant messages. [cite: 82]
## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator) [cite: 83]
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`. [cite: 84]
-   **Containerization:** Docker, Docker Compose. [cite: 84]

## Project Structure

(Key files for upcoming Chat UI changes: `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/css/style.css`. Backend: `backend/db_utils.py`, `backend/message_processing/task_handlers.py`, `backend/message_processing/agent_flow_handlers.py`, `backend/callbacks.py`) [cite: 85, 86, 87]


```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # Updated ReAct prompt for direct tool output
│   ├── callbacks.py         # Updated for structured thinking updates & log_source, token parsing refined [cite: 85]
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
│   │   ├── operational_handlers.py [cite: 86]
│   │   └── task_handlers.py     # Updated to load/save status_messages from history [cite: 86]
│   ├── planner.py
│   ├── server.py                # Updated to save status_messages
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py # Input schema `query`, saves report
│       ├── playwright_search.py
│       ├── standard_tools.py
│       └── tavily_search_tool.py [cite: 87]
├── css/
│   └── style.css                # Updated for new chat UI styles & token counter
├── js/
│   ├── script.js                # Dispatches new message types, handles token updates
│   ├── state_manager.js         # Manages token state, including per-role
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── chat_ui.js           # Implemented new rendering logic
│       └── token_usage_ui.js    # Renders per-role token breakdown
├── BRAINSTORM.md                # Updated with new UI vision and fixed issues [cite: 88]
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                      # This file
├── ROADMAP.md                     # Updated with new UI vision and fixed issues
└── simulation_option6.html        # Conceptual: Visual mock-up of the target chat UI (described in BRAINSTORM.md)
```

## Setup Instructions & Running the Application

(No changes - these remain the same as provided by the user) [cite: 89]

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Fixes)

-   **FILE UPLOAD (High Priority):** File upload functionality is broken, resulting in an HTTP 501 "Not Implemented" error from the backend. [cite: 89]
-   **ARTIFACT VIEWER REFRESH (Medium Priority):** The artifact viewer does not consistently or immediately auto-update after a task completes and writes files, even if logs indicate a refresh was triggered. [cite: 90]
-   **TOKEN COUNTER (FIXED):** The UI token counter is now correctly updating for all agent roles. [cite: 91]
-   **PLAN FILE STATUS UPDATE (Low Priority):** Backend logs still show warnings about not finding step patterns to update status checkboxes in the `_plan_{id}.md` artifact. [cite: 92]
-   **"UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Review):** Some internal system message types are logged to the monitor from history; confirm this is the desired behavior for all such types. [cite: 93, 94]
## Security Warnings

(No changes - these remain the same as provided by the user) [cite: 95]

## Next Steps & Future Perspectives

The immediate focus is on resolving the critical bugs related to new task connection, file uploads, and then artifact viewer refresh and other minor issues. [cite: 96]
For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**. [cite: 97, 98]
