# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. [cite: 5, 90] It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain. [cite: 90]
Targeting Version 2.5.3 [cite: 91]

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete):**
    -   Resolved critical `IndentationError` issues in backend. [cite: 92]
    -   `deep_research_synthesizer` & `write_file` Flow: Core logic for actual execution is now in place, replacing placeholder outputs. [cite: 92]
    -   `UnboundLocalError` in `callbacks.py` related to token usage parsing: **FIXED.** [cite: 93]
-   **Chat UI/UX Refinement (Implementation & Fixes Ongoing):**
    -   **Visual Design (Target: `simulation_option6.html`):**
        -   User messages with right side-lines, system/plan/final messages with unified blue outer left side-lines (though blue line now removed for RA final answers & plans), no side-lines for major step announcements, and nested/indented component-specific lines for sub-statuses & agent thoughts are implemented. [cite: 94, 41]
        -   Improved message alignment with consistent sub-step indentation (sub-content now further indented).
        -   HTML tags (`<strong>`, `<em>`) are now rendering correctly in the chat. [cite: 94]
    -   **Interactivity & Layout:**
        -   Collapsible major agent steps implemented for better readability.
        -   Adjusted message bubble widths: User messages, final RA answers, and Plan Proposals now use ~60% of panel width; sub-components within steps (thoughts, tool outputs, sub-statuses) use ~40%. Step titles also wrap at ~60%.
        -   Agent Avatar ("RA") added to final agent answer messages.
        -   Blue left-hand line removed from final RA messages and Plan Proposal blocks for a cleaner look.
    -   **Backend Support & Persistence:**
        -   Backend sends structured messages for steps, sub-statuses, and thoughts. [cite: 95]
        -   Persistence for these new message types in the database and reloading into history is implemented. [cite: 96]
        -   Ensured visual consistency for persisted (reloaded) confirmed plans.
    -   **Plan Proposal UI & Persistence (Complete):** Remains functional. [cite: 97]
    -   **Token Counter UI & Functionality (FIXED):** Expandable UI for token breakdown by role is implemented. [cite: 98] Token counting functionality now works for all individual agent/LLM roles and is accurately displayed. [cite: 99] Persistence for displayed totals per task is working. [cite: 100]
    -   **File Upload Functionality (FIXED):** File uploads to the task workspace are now functional. [cite: 101]
    -   **In-Chat Tool Feedback & Usability (Core Functionality Implemented & Refined):**
        -   Tool action confirmations (e.g., for file writes) and output snippets (e.g., for file reads including `read_file`, search results) are now displayed correctly directly in chat. [cite: 102]
        -   Longer tool outputs in chat are collapsible by clicking their label. [cite: 102]
        -   "Copy to Clipboard" functionality has been added for tool outputs, agent thoughts, final agent answers, and code blocks. [cite: 103]
        -   Planner prompting has been refined to encourage more comprehensive final summary messages from the agent. [cite: 104]
    -   **Chat Behavior Fixes:**
        * Fixed issue where chat would unnecessarily scroll to the bottom when expanding/collapsing message bubbles.

## Core Architecture & Workflow

(No changes to this section)

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Creation, deletion, renaming functional. [cite: 106] Workspace folders managed correctly. [cite: 106]
    -   Chat Interface:
        -   **Rendering:** Correctly displays styled HTML tags. [cite: 107] Implements the visual hierarchy for steps, sub-statuses, and thoughts with improved alignment and indentation. Step titles wrap appropriately.
        -   **Collapsible Elements:** Major agent steps are collapsible. Tool outputs in chat are collapsible via their labels.
        -   **In-Chat Tool Feedback:** Displays tool action confirmations and output snippets (including `read_file` content) directly in chat, with collapsible sections for longer outputs. [cite: 108]
        -   **Copy to Clipboard:** Allows copying content from tool outputs, agent thoughts, final agent answers, and code blocks. [cite: 109]
        -   **Visual Cues:** Agent avatar ("RA") distinguishes final agent answers. Blue side-line removed from RA final answers and plan proposals.
        -   **Message Widths:** User messages, RA final answers, and Plan Proposals use ~60% width. Sub-components within agent steps (thoughts, tool outputs, sub-statuses) use ~40% width.
        -   **Persistence:** All chat message types, including structured steps, thoughts, tool outputs, and confirmed plans are saved and reloaded with consistent visual styling. [cite: 110]
        -   **Planned Enhancements (UI/UX Polish):** [cite: 111]
            -   Review and refine chat message visual density and spacing further if needed.
            -   Standardize copy/expand button placement and appearance (partially addressed with consistent copy buttons and label-based collapse for tools).
            -   Finalize "View [artifact] in Artifacts" links from tool output messages. [cite: 112]
    -   Role-Specific LLM Selection. [cite: 112]
    -   Monitor Panel for structured agent logs.
    -   Artifact Viewer.
    -   Token Usage Tracking (FIXED & COMPLETE): Accurately tracks and displays token usage per LLM call, broken down by agent role, and aggregated per task. [cite: 113]
    -   File Upload Capability (FIXED): Users can upload files to the active task's workspace. [cite: 114]
2.  **Backend Architecture & Logic:**
    -   Modular Python backend. LangChain for P-C-E-E pipeline. [cite: 115]
    -   Task-specific, isolated workspaces with persistent history (SQLite). [cite: 116]
    -   Actual Plan Execution: Backend now attempts full execution of plan steps. [cite: 117]
    -   **Message Structure & Persistence:** Implemented for all chat-relevant messages, including new `tool_result_for_chat` messages and `confirmed_plan_log`. [cite: 118]
    -   **Enhanced Callbacks:** `callbacks.py` now sends `tool_result_for_chat` messages from `on_tool_end`. [cite: 119]
    -   **Refined Planner Prompting:** Planner prompt updated to guide the agent towards generating more comprehensive final summary messages. [cite: 120]

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`. [cite: 121]
-   **Containerization:** Docker, Docker Compose. [cite: 122]

## Project Structure

(Key files for Chat UI: `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/css/style.css`. Backend: `backend/db_utils.py`, `backend/message_processing/task_handlers.py`, `backend/callbacks.py`, `backend/planner.py`)
(Structure as previously listed, no changes based on recent work)
```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # ReAct prompt (verified for multi-line final answers)
│   ├── callbacks.py         # Enhanced for tool_result_for_chat messages & persistence. [cite: 123]
│   ├── config.py
│   ├── controller.py
│   ├── db_utils.py          # Handles persistence of all message types. [cite: 124]
│   ├── evaluator.py
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py 
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py     # Updated to load/save tool_result_for_chat from history. [cite: 125]
│   ├── planner.py             # Enhanced for final summary steps. [cite: 126]
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py
│       ├── playwright_search.py
│       ├── standard_tools.py
│       └── tavily_search_tool.py
├── css/
│   └── style.css                # Enhanced for new tool message bubbles, copy buttons, alignment, widths, collapsible steps. [cite: 127]
├── js/
│   ├── script.js                # Handles new tool_result_for_chat messages. [cite: 128]
│   ├── state_manager.js
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── chat_ui.js           # Enhanced for tool bubbles, collapsibility (labels & major steps), copy buttons, avatar, plan rendering. [cite: 129]
│       ├── token_usage_ui.js
│       └── file_upload_ui.js
├── BRAINSTORM.md                # Updated with UI/UX polish items and completed features. [cite: 130]
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                      # This file
├── ROADMAP.md                     # Updated with completed features and next steps. [cite: 131]
└── simulation_option6.html        # Conceptual: Visual mock-up of the target chat UI (largely achieved)
```

## Setup Instructions & Running the Application

(No changes - these remain the same as provided by the user)

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Enhancements & Fixes)

-   **BUG: ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Resumes):** The artifact viewer does not consistently or immediately auto-update after a task completes and writes files. [cite: 132]
-   **UI/UX POLISH (Medium Priority - Ongoing Focus):**
    -   Review and refine chat message visual density, alignment, and spacing further based on latest feedback (see `BRAINSTORM.md`). [cite: 133] (Partially Addressed: Sub-step indentation increased, consistent bubble widths implemented).
    -   Standardize copy/expand button placement and appearance (Partially Addressed: Copy buttons are fairly consistent; tool output expansion is now primarily by label click; major steps are collapsible).
    -   Finalize "View [artifact] in Artifacts" links from tool output messages. [cite: 134]
    -   Review and refine the behavior and appearance of the global "agent-thinking-status" line. [cite: 29]
    -   Restyle agent step announcements (e.g., "Step X/Y: Description") if current title styling is not final (e.g., boxing, copy button per `prompt.txt` - currently not boxed, title wraps).
-   **DEBUG: Monitor Log Color-Coding (Low Priority):** Verify/implement CSS for log differentiation by source. [cite: 135]
-   **WARNING: PLAN FILE STATUS UPDATE (Low Priority):** Backend logs still show warnings about not finding step patterns to update status checkboxes in the `_plan_{id}.md` artifact. [cite: 136]
-   **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Review):** Some internal system message types are logged to the monitor from history; confirm this is the desired behavior for all such types. [cite: 137]

**Previously Fixed/Implemented in v2.5.3 development cycle:**
-   **ENHANCEMENT: In-Chat Tool Feedback & Usability (Core Functionality Implemented & Refined):** Tool outputs (including `read_file`) in chat, copy-to-clipboard, refined planner prompting, collapsible tool outputs. [cite: 138]
-   **ENHANCEMENT: Chat UI/UX Major Improvements:** Collapsible major steps, agent avatar, improved alignment and message width consistency, removal of unnecessary blue lines.
-   **BUG FIX: `read_file` output visibility in chat.**
-   **BUG FIX: Chat scroll jump on bubble expand/collapse.**
-   **FILE UPLOAD (FIXED):** File upload functionality is now working. [cite: 139]
-   **TOKEN COUNTER (FIXED):** The UI token counter is now correctly updating for all agent roles. [cite: 140]

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on addressing the artifact viewer refresh bug and continuing UI/UX polish based on recent feedback. [cite: 142] For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**. [cite: 143]
