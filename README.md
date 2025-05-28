# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
Targeting Version 2.5.3

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete):**
    -   Resolved critical `IndentationError` issues in backend.
    -   `deep_research_synthesizer` & `write_file` Flow: Core logic for actual execution is now in place, replacing placeholder outputs.
    -   `UnboundLocalError` in `callbacks.py` related to token usage parsing: **FIXED.**
-   **Chat UI/UX Refinement (Implementation & Fixes Ongoing):**
    -   **Visual Design (Target: `simulation_option6.html`):**
        -   User messages with right side-lines, system/plan/final messages with unified blue outer left side-lines, no side-lines for major step announcements, and nested/indented component-specific lines for sub-statuses & agent thoughts are implemented.
    -   HTML tags (`<strong>`, `<em>`) are now rendering correctly in the chat.
    -   **Backend Support & Persistence:**
        -   Backend sends structured messages for steps, sub-statuses, and thoughts.
        -   Persistence for these new message types in the database and reloading into history is implemented.
    -   **Plan Proposal UI & Persistence (Complete):** Remains functional.
    -   **Token Counter UI & Functionality (FIXED):** Expandable UI for token breakdown by role is implemented. Token counting functionality now works for all individual agent/LLM roles and is accurately displayed. Persistence for displayed totals per task is working.
    -   **File Upload Functionality (FIXED):** File uploads to the task workspace are now functional.
    -   **In-Chat Tool Feedback & Usability (Core Functionality Implemented):**
        -   Tool action confirmations (e.g., for file writes) and output snippets (e.g., for file reads, search results) are now displayed directly in chat.
        -   Longer tool outputs in chat are collapsible.
        -   "Copy to Clipboard" functionality has been added for tool outputs, agent thoughts, final agent answers, and code blocks.
        -   Planner prompting has been refined to encourage more comprehensive final summary messages from the agent.

## Core Architecture & Workflow

(No changes to this section)

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Creation, deletion, renaming functional. Workspace folders managed correctly.
    -   Chat Interface:
        -   **Rendering:** Correctly displays styled HTML tags. Implements the visual hierarchy for steps, sub-statuses, and thoughts.
        -   **In-Chat Tool Feedback:** Displays tool action confirmations and output snippets directly in chat, with collapsible sections for longer outputs.
        -   **Copy to Clipboard:** Allows copying content from tool outputs, agent thoughts, final agent answers, and code blocks.
        -   **Persistence:** All chat message types, including structured steps, thoughts, and tool outputs, are saved and reloaded.
        -   **Planned Enhancements (UI/UX Polish):**
            -   Review and refine chat message visual density, indentation, and spacing.
            -   Standardize copy/expand button placement and appearance.
            -   Finalize "View [artifact] in Artifacts" links from tool output messages.
    -   Role-Specific LLM Selection.
    -   Monitor Panel for structured agent logs.
    -   Artifact Viewer.
    -   Token Usage Tracking (FIXED & COMPLETE): Accurately tracks and displays token usage per LLM call, broken down by agent role, and aggregated per task.
    -   File Upload Capability (FIXED): Users can upload files to the active task's workspace.
2.  **Backend Architecture & Logic:**
    -   Modular Python backend. LangChain for P-C-E-E pipeline.
    -   Task-specific, isolated workspaces with persistent history (SQLite).
    -   Actual Plan Execution: Backend now attempts full execution of plan steps.
    -   **Message Structure & Persistence:** Implemented for all chat-relevant messages, including new `tool_result_for_chat` messages.
    -   **Enhanced Callbacks:** `callbacks.py` now sends `tool_result_for_chat` messages from `on_tool_end`.
    -   **Refined Planner Prompting:** Planner prompt updated to guide the agent towards generating more comprehensive final summary messages.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

## Project Structure

(Key files for Chat UI: `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/css/style.css`. Backend: `backend/db_utils.py`, `backend/message_processing/task_handlers.py`, `backend/callbacks.py`, `backend/planner.py`)

```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # ReAct prompt (verified for multi-line final answers)
│   ├── callbacks.py         # Enhanced for tool_result_for_chat messages & persistence.
│   ├── config.py
│   ├── controller.py
│   ├── db_utils.py          # Handles persistence of all message types.
│   ├── evaluator.py
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py 
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py     # Updated to load/save tool_result_for_chat from history.
│   ├── planner.py             # Enhanced for final summary steps.
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py
│       ├── playwright_search.py
│       ├── standard_tools.py
│       └── tavily_search_tool.py
├── css/
│   └── style.css                # Enhanced for new tool message bubbles & copy buttons.
├── js/
│   ├── script.js                # Handles new tool_result_for_chat messages.
│   ├── state_manager.js
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── chat_ui.js           # Enhanced for tool bubbles, collapsibility, copy buttons.
│       ├── token_usage_ui.js
│       └── file_upload_ui.js
├── BRAINSTORM.md                # Updated with UI/UX polish items and completed features.
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                      # This file
├── ROADMAP.md                     # Updated with completed features and next steps.
└── simulation_option6.html        # Conceptual: Visual mock-up of the target chat UI (largely achieved)
```

## Setup Instructions & Running the Application

(No changes - these remain the same as provided by the user)

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Enhancements & Fixes)

-   **BUG: ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Resumes):** The artifact viewer does not consistently or immediately auto-update after a task completes and writes files.
-   **UI/UX POLISH (Medium Priority - Next Focus):**
    -   Review and refine chat message visual density, indentation, and spacing (see `BRAINSTORM.md`).
    -   Standardize copy/expand button placement and appearance.
    -   Finalize "View [artifact] in Artifacts" links from tool output messages.
-   **DEBUG: Monitor Log Color-Coding (Low Priority):** Verify/implement CSS for log differentiation by source.
-   **WARNING: PLAN FILE STATUS UPDATE (Low Priority):** Backend logs still show warnings about not finding step patterns to update status checkboxes in the `_plan_{id}.md` artifact.
-   **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Review):** Some internal system message types are logged to the monitor from history; confirm this is the desired behavior for all such types.

**Previously Fixed/Implemented in v2.5.3 development cycle:**
-   **ENHANCEMENT: In-Chat Tool Feedback & Usability (Core Functionality Implemented):** Tool outputs in chat, copy-to-clipboard, refined planner prompting.
-   **FILE UPLOAD (FIXED):** File upload functionality is now working.
-   **TOKEN COUNTER (FIXED):** The UI token counter is now correctly updating for all agent roles.

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on addressing the artifact viewer refresh bug and undertaking UI/UX polish based on recent feedback. For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
