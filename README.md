# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements Nearing Completion)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
Targeting Version 2.5.3

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete):**
    -   Resolved critical `IndentationError` issues in backend.
    -   `deep_research_synthesizer` & `write_file` Flow: Core logic for actual execution is now in place, replacing placeholder outputs.
    -   `UnboundLocalError` in `callbacks.py` related to token usage parsing: **FIXED.**
-   **Chat UI/UX Refinement (Significant Progress):**
    -   **Visual Design (Target: `simulation_option6.html` as base, now significantly enhanced):**
        -   User messages with right side-lines. System/status messages use a blue outer left side-line (RA final answers and Plan Proposals now have this line removed). No side-lines for major step announcements. Nested/indented component-specific lines for sub-statuses & agent thoughts are implemented.
        -   Improved message alignment with consistent and deeper sub-step indentation.
        -   Increased general UI font size for better readability. Token Usage area font size specifically increased.
        -   HTML tags (`<strong>`, `<em>`) are now rendering correctly in the chat.
    -   **Interactivity & Layout:**
        -   Collapsible major agent steps implemented.
        -   Adjusted message bubble widths: User messages, final RA answers (now fit-to-content up to max), and Plan Proposals use ~60% of panel width; sub-components within steps (thoughts, tool outputs, sub-statuses) use ~40%. Step titles also wrap at ~60%.
        -   Agent Avatar ("RA") added to final agent answer messages.
        -   Blue left-hand line removed from final RA messages and Plan Proposal blocks.
        -   Role LLM selector labels in the chat header are now white with a small colored square indicator matching agent step colors for better visual association.
    -   **Backend Support & Persistence:**
        -   Backend sends structured messages for steps, sub-statuses, and thoughts.
        -   Persistence for these new message types in the database and reloading into history is implemented.
        -   **FIXED:** Ensured visual consistency and correct rendering for persisted (reloaded) confirmed plans.
    -   **Plan Proposal UI & Persistence (Complete):** Remains functional.
    -   **Token Counter UI & Functionality (FIXED & ENHANCED):** Expandable UI for token breakdown by role is implemented. Token counting functionality now works for all individual agent/LLM roles and is accurately displayed. Persistence for displayed totals per task is working. Font size increased for better readability.
    -   **File Upload Functionality (FIXED):** File uploads to the task workspace are now functional.
    -   **In-Chat Tool Feedback & Usability (Core Functionality Implemented & Refined):**
        -   Tool action confirmations (e.g., for file writes) and output snippets (e.g., for file reads including `read_file`, search results) are now displayed correctly directly in chat and correctly nested.
        -   Longer tool outputs in chat are collapsible by clicking their label.
        -   "Copy to Clipboard" functionality has been added for tool outputs, agent thoughts, final agent answers, and code blocks.
        -   Planner prompting has been refined to encourage more comprehensive final summary messages from the agent.
    -   **Chat Behavior Fixes:**
        * Fixed issue where chat would unnecessarily scroll to the bottom when expanding/collapsing message bubbles.

## Core Architecture & Workflow

(No changes to this section)

## Key Current Capabilities & Features

1.  **UI & User Interaction:**
    -   Task Management: Creation, deletion, renaming functional. Workspace folders managed correctly.
    -   Chat Interface:
        -   **Rendering & Readability:** Correctly displays styled HTML tags. Implements the visual hierarchy for steps, sub-statuses, and thoughts with improved alignment, indentation, and increased font sizes. Step titles wrap appropriately.
        -   **Collapsible Elements:** Major agent steps are collapsible. Tool outputs in chat are collapsible via their labels.
        -   **In-Chat Tool Feedback:** Displays tool action confirmations and output snippets (including `read_file` content) directly in chat, correctly nested, with collapsible sections for longer outputs.
        -   **Copy to Clipboard:** Allows copying content from tool outputs, agent thoughts, final agent answers, and code blocks.
        -   **Visual Cues:** Agent avatar ("RA") distinguishes final agent answers. Blue side-line removed from RA final answers and plan proposals. Role LLM selectors have color-coded indicators.
        -   **Message Widths:** User messages, RA final answers (fit-to-content), and Plan Proposals use ~60% width. Sub-components within agent steps use ~40% width.
        -   **Persistence:** All chat message types, including structured steps, thoughts, tool outputs, and confirmed plans are saved and reloaded with consistent visual styling.
        -   **Planned Enhancements (UI/UX Polish):**
            -   Review and refine chat message visual density and spacing further if needed.
            -   Finalize "View [artifact] in Artifacts" links from tool output messages.
            -   Review and refine the behavior and appearance of the global "agent-thinking-status" line.
            -   Restyle agent step announcements (e.g., boxing, copy button) if current collapsible title is not final.
    -   Role-Specific LLM Selection (with color-coded labels).
    -   Monitor Panel for structured agent logs.
    -   Artifact Viewer.
    -   Token Usage Tracking (FIXED & COMPLETE): Accurately tracks and displays token usage per LLM call, broken down by agent role, and aggregated per task. UI font size increased.
    -   File Upload Capability (FIXED): Users can upload files to the active task's workspace.
2.  **Backend Architecture & Logic:**
    -   Modular Python backend. LangChain for P-C-E-E pipeline.
    -   Task-specific, isolated workspaces with persistent history (SQLite).
    -   Actual Plan Execution: Backend now attempts full execution of plan steps.
    -   **Message Structure & Persistence:** Implemented for all chat-relevant messages, including new `tool_result_for_chat` messages and `confirmed_plan_log`.
    -   **Enhanced Callbacks:** `callbacks.py` now sends `tool_result_for_chat` messages from `on_tool_end`.
    -   **Refined Planner Prompting:** Planner prompt updated to guide the agent towards generating more comprehensive final summary messages.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

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
│   └── style.css                # Enhanced for new tool message bubbles, copy buttons, alignment, widths, collapsible steps, fonts, selector colors.
├── js/
│   ├── script.js                # Handles new tool_result_for_chat messages.
│   ├── state_manager.js
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── chat_ui.js           # Enhanced for tool bubbles, collapsibility (labels & major steps), copy buttons, avatar, plan rendering, nesting fixes.
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
-   **UI/UX POLISH (Low Priority - Most critical items addressed):**
    -   Finalize "View [artifact] in Artifacts" links from tool output messages.
    -   Review and refine the behavior and appearance of the global "agent-thinking-status" line.
    -   Consider if further styling (e.g., boxing, copy button) is needed for agent step announcements beyond current collapsible titles.
-   **DEBUG: Monitor Log Color-Coding (Low Priority):** Verify/implement CSS for log differentiation by source.
-   **WARNING: PLAN FILE STATUS UPDATE (Low Priority):** Backend logs still show warnings about not finding step patterns to update status checkboxes in the `_plan_{id}.md` artifact.
-   **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Review):** Some internal system message types are logged to the monitor from history; confirm this is the desired behavior for all such types.

**Previously Fixed/Implemented in v2.5.3 development cycle:**
-   **ENHANCEMENT: In-Chat Tool Feedback & Usability (Core Functionality Implemented & Refined):** Tool outputs (including `read_file`) in chat, copy-to-clipboard, refined planner prompting, collapsible tool outputs.
-   **ENHANCEMENT: Chat UI/UX Major Improvements:** Collapsible major steps, agent avatar, improved alignment and message width consistency (including fit-to-content for RA messages), removal of unnecessary blue lines, increased font sizes, color-coded LLM role selectors.
-   **BUG FIX: `read_file` output visibility in chat.**
-   **BUG FIX: Chat scroll jump on bubble expand/collapse.**
-   **BUG FIX: Plan persistence and consistent rendering from history.**
-   **FILE UPLOAD (FIXED):** File upload functionality is now working.
-   **TOKEN COUNTER (FIXED & ENHANCED):** The UI token counter is now correctly updating for all agent roles, font size increased.

## Security Warnings

(No changes - these remain the same as provided by the user)

## Next Steps & Future Perspectives

The immediate focus is on addressing the artifact viewer refresh bug and any remaining minor UI/UX polish. For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
