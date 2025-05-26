# ResearchAgent: AI Assistant for Research Workflows (v2.5.2 - Plan UI Fixes In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Version 2.5.2 Highlights (Foundation for Current Work):**
* **Major Frontend Refactoring (Phases 1, 2, 3.1 Complete):** JavaScript code for the UI has been significantly modularized. [cite: 2116]
* **Backend Message Handler Refactoring:** The main `message_handlers.py` has been broken down into smaller, more focused handlers. [cite: 2118]
* **Agent Logic & Stability Improvements:**
    * Correct inter-step data flow fixed (Controller now uses previous step outputs). [cite: 2119, 2120]
    * Persistent final evaluations in chat history. [cite: 2121]
* **Robust UI Functionality (Base):** Task management, file uploads, artifact viewer were functional. [cite: 2122, 2123]
* **Numerous Backend Stability Fixes:** Resolved various errors. [cite: 2124]
* **Advanced P-C-E-E Pipeline** with configurable LLMs (Gemini & Ollama). [cite: 2126, 2127]

**Recent Developments (Leading to v2.5.3 Target):**

* **Backend Plan Proposal Mechanism:**
    * The backend now correctly sends a `propose_plan_for_confirmation` message (instead of `display_plan_for_confirmation`). This message includes a `plan_id`, `human_summary`, and the `structured_plan`.
    * Upon plan generation, a `_plan_proposal_<plan_id>.md` artifact is created in the task's workspace.
    * A backend handler for `cancel_plan_proposal` has been implemented to clear server-side state related to a pending proposal.
* **Controller Robustness:**
    * Fixed a `NameError` for `json` and improved JSON parsing by stripping Markdown backticks from LLM outputs in `backend/controller.py`.
* **Tool Enhancements (`backend/tools/standard_tools.py`):**
    * `python_package_installer`: Now correctly handles multiple space- or comma-separated package names in its input string. Its description has been updated to reflect this.
    * `TaskWorkspaceShellTool`: Modified to always include STDOUT in its result if present, providing more accurate feedback to the agent.
    * `Python_REPL`: Tool description significantly rewritten to emphasize its use for simple, straightforward Python operations and to discourage its use for complex scripts or file I/O, guiding the LLM to choose more appropriate tools like `write_file` + `workspace_shell` for scripts.
* **Frontend Plan Proposal Display (Initial):**
    * The frontend (`js/script.js`) now correctly receives and processes the `propose_plan_for_confirmation` message.
    * The basic UI for plan proposal (summary and buttons) is now appearing in the chat interface. [cite: 2598]

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning. [cite: 2128]
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps.
3.  **User Confirmation (for plans)**: The proposed plan (summary and steps) is shown to the user for approval via the chat interface. [cite: 2131]
4.  **Execution**: The agent executes each step, involving a Controller, an Executor, and a Step Evaluator.
5.  **Overall Evaluation**: A final assessment of the plan's success is provided. [cite: 2133]

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`.
For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features (Reflecting recent updates)

1.  **UI & User Interaction:**
    * Task Management with persistent storage and reliable UI updates. [cite: 2135]
    * Chat Interface with Markdown rendering, input history, and **now displays interactive plan proposals**.
    * Role-Specific LLM Selection. [cite: 2136]
    * Monitor Panel for structured agent logs. [cite: 2137]
    * Artifact Viewer for text/image/PDF outputs (including plan proposal artifacts). [cite: 2137]
    * Token Usage Tracking. [cite: 2138]
    * File upload capability to task workspaces. [cite: 2139]
2.  **Backend Architecture & Logic:**
    * Modular Python backend with refactored message handlers. [cite: 2139]
    * LangChain for P-C-E-E pipeline. [cite: 2139]
    * Task-specific, isolated workspaces with persistent history (SQLite). [cite: 2140]
    * Corrected plan proposal messaging and cancellation handling.
3.  **Tool Suite (`backend/tools/`):**
    * Includes `TavilyAPISearchTool`, `DeepResearchTool`, `DuckDuckGoSearchRun`, `web_page_reader`, `pubmed_search`, File I/O, `python_package_installer` (multi-package capable), `workspace_shell` (improved STDOUT), and `Python_REPL` (clarified scope). [cite: 2063]

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator) [cite: 2141]
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`. [cite: 2141]
-   **Containerization:** Docker, Docker Compose. [cite: 2142]

## Project Structure
(No major changes to overall structure, but individual files like `controller.py`, `standard_tools.py`, `evaluator.py`, `agent.py`, `agent_flow_handlers.py` have been updated. The `message_processing` sub-package remains key.)

```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # Updated ReAct prompt
│   ├── callbacks.py
│   ├── config.py
│   ├── controller.py        # Updated JSON parsing, tool_input handling
│   ├── db_utils.py
│   ├── evaluator.py         # Updated STEP_EVALUATOR_SYSTEM_PROMPT
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py  # Re-exports from message_processing
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py # Updated for propose_plan_for_confirmation, cancel_plan_proposal
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py
│   ├── planner.py
│   ├── server.py            # Updated message_handler_map
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py
│       ├── playwright_search.py
│       ├── standard_tools.py  # Updated python_package_installer, workspace_shell, Python_REPL desc.
│       └── tavily_search_tool.py
├── css/
│   └── style.css
├── database/
│   └── agent_history.db
├── js/
│   ├── script.js            # Updated for propose_plan_for_confirmation, plan callbacks
│   ├── state_manager.js     # Updated for plan_id storage
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── artifact_ui.js
│       ├── chat_ui.js         # Plan proposal display, inline details (pending)
│       ├── file_upload_ui.js
│       ├── llm_selector_ui.js
│       ├── monitor_ui.js
│       ├── task_ui.js
│       └── token_usage_ui.js
├── BRAINSTORM.md            # This file
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                # This file
├── ROADMAP.md
├── requirements.txt
└── workspace/
    └── <task_id>/
        ├── _plan_proposal_<ID>.md # Created on plan proposal
        ├── _plan_<ID>.md          # Created on plan execution
        └── ...
```

## Setup Instructions & Running the Application
(No changes from v2.5 - these remain the same)

## Known Issues / Immediate Next Steps

* **Frontend Plan Interaction Refinements (High Priority):**
    * **Inline "View Details":** The "View Details" button for plan proposals currently attempts to show an artifact. This needs to be changed to expand/collapse the structured plan details directly within the chat UI proposal block. [cite: 2598]
    * **Persistent Confirmed Plan in Chat:** When a plan is confirmed, the interactive proposal block should transform into a static, non-interactive message displaying the confirmed plan (summary and steps). This static representation needs to be saved to the database by the backend (as `confirmed_plan_log`) and correctly rendered from chat history on reload. [cite: 2598]
* **Refine Intermediate Step Chat Output (High Priority - Post Plan UI Fixes):**
    * Chat can still be cluttered with intermediate agent thoughts/tool outputs. [cite: 2068]
    * Goal: Route most intermediate details to Monitor Log, keeping chat for primary interactions (user messages, agent final answers/key results, concise status updates). [cite: 2069]
* **Color-Coding UI Elements (Medium Priority):**
    * Visually differentiate Monitor Log messages (Planner, Controller, Executor, Evaluator) and link colors to LLM selectors. [cite: 2070]
* **Further `script.js` Refinement (Phase 3.2 Completion - Medium Priority):**
    * Ensure `script.js` is a lean orchestrator, with UI logic in modules and state via `StateManager`. [cite: 2071]

## Security Warnings
(No changes - these remain the same)

## Next Steps & Future Perspectives
The immediate focus is on completing the frontend implementation for plan proposal interaction (inline details, persistent confirmed plan message). Following that, efforts will target chat clutter reduction and monitor color-coding, along with ongoing `script.js` refinement.

For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
