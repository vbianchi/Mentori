# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

Targeting Version 2.5.3

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete):**
    -   Resolved critical `IndentationError` issues in backend.
    -   `deep_research_synthesizer` & `write_file` Flow: Core logic for actual execution is now in place, replacing placeholder outputs.
    -   `UnboundLocalError` in `callbacks.py` related to token usage parsing: **FIXED.**
-   **Chat UI/UX Refinement (Partially Implemented, Ongoing Fixes):**
    -   **Visual Design (Target: `simulation_option6.html`):**
        -   User messages with right side-lines, system/plan/final messages with unified blue outer left side-lines, no side-lines for major step announcements, and nested/indented component-specific lines for sub-statuses & agent thoughts are implemented.
        -   HTML tags (`<strong>`, `<em>`) are now rendering correctly in the chat.
    -   **Backend Support & Persistence:**
        -   Backend sends structured messages for steps, sub-statuses, and thoughts.
        -   Persistence for these new message types in the database and reloading into history is implemented.
-   **Plan Proposal UI & Persistence (Complete):** Remains functional.

## Core Architecture & Workflow

(No changes to this section)

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Creation, deletion, renaming functional. Workspace folders managed correctly.
    -   Chat Interface:
        -   **Rendering:** Correctly displays styled HTML tags. Implements the new visual hierarchy for steps, sub-statuses, and thoughts as per `simulation_option6.html`.
        -   **Persistence:** All chat message types, including the new structured ones, are saved and reloaded.
    -   Role-Specific LLM Selection.
    -   Monitor Panel for structured agent logs.
    -   Artifact Viewer.
    -   Token Usage Tracking.
    -   File upload capability.
2.  **Backend Architecture & Logic:**
    -   Modular Python backend. LangChain for P-C-E-E pipeline.
    -   Task-specific, isolated workspaces with persistent history (SQLite).
    -   **Actual Plan Execution:** Backend now attempts full execution of plan steps, including tool usage and LLM generation, replacing previous placeholder logic.
    -   **Message Structure & Persistence:** Implemented for all chat-relevant messages.

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

-   **NEW TASK CONNECTION (High Priority):** Newly created tasks do not immediately establish full context with the backend. Requires an interaction attempt (like sending a message) and then a page refresh to function correctly.
-   **ARTIFACT VIEWER REFRESH (Medium Priority):** The artifact viewer does not consistently or immediately auto-update after a task completes and writes files, even if logs indicate a refresh was triggered.
-   **TOKEN COUNTER (Medium Priority):** The UI token counter is no longer updating.
-   **FILE UPLOAD (High Priority):** File upload functionality is broken, resulting in an HTTP 501 "Not Implemented" error from the backend.
-   **PLAN FILE STATUS UPDATE (Low Priority):** Backend logs still show warnings about not finding step patterns to update status checkboxes in the `_plan_{id}.md` artifact.
-   **"UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Review):** Some internal system message types are logged to the monitor from history; confirm this is the desired behavior for all such types.

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on resolving the critical bugs related to new task connection, file uploads, and token counter functionality. Following that, artifact viewer refresh and other minor issues will be addressed.
For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
