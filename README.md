# ResearchAgent: AI Assistant for Research Workflows (v2.5.1)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Version 2.5.1 Highlights:**
* **Major Frontend Refactoring (Phases 1, 2, 3.1 Complete):** JavaScript code for the UI has been significantly modularized into a `state_manager.js`, `websocket_manager.js`, and several `ui_modules` (for tasks, chat, monitor, artifacts, LLM selectors, token usage, and file uploads) for improved maintainability and clarity. `script.js` now acts more as an orchestrator using the `StateManager`.
* **Backend Message Handler Refactoring:** The main `message_handlers.py` has been broken down into smaller, more focused handlers within a `message_processing` sub-package, improving backend code organization.
* **Agent Logic & Stability Improvements:**
    * **Correct Inter-Step Data Flow:** Fixed a critical bug where the Controller would not use the output of a previous generative step (e.g., poem generation) as input for a subsequent step (e.g., writing to a file). The agent now correctly passes and utilizes data between steps.
    * **Persistent Final Evaluations:** The Overall Plan Evaluator's final assessment message now correctly persists in the chat history.
* **Robust UI Functionality:**
    * Task management (creation, deletion, renaming) UI updates reliably.
    * File uploads and associated workspace folder creation are working correctly.
    * Artifact viewer is fully functional with working navigation.
* **Numerous Backend Stability Fixes:** Resolved various `TypeError`s, `NameError`s, and `SyntaxError`s that arose during the refactoring process.
* **Fully Functional `DeepResearchTool`**: A multi-phase tool for comprehensive investigations.
* **Advanced P-C-E-E Pipeline**: Employs a Planner-Controller-Executor-Evaluator pipeline with per-step evaluation and retry mechanisms.
* **Configurable LLMs**: Supports Google Gemini and local Ollama models, with role-specific configurations.

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps to achieve the user's goal, selecting appropriate tools. The Planner is now better guided to define `expected_outcome` for "No Tool" generative steps to be the actual content itself.
3.  **User Confirmation (for plans)**: The proposed plan is shown to the user for approval. (UI for this is the next major improvement area).
4.  **Execution**: The agent executes each step, involving a Controller (to validate and prepare actions, now aware of previous step outputs), an Executor (a ReAct agent), and a Step Evaluator.
5.  **Overall Evaluation**: A final assessment of the plan's success is provided and persisted in the chat.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`. For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features

(Largely same as v2.5, with emphasis on fixes and stability)
1.  **UI & User Interaction:**
    * Task Management with persistent storage and reliable UI updates.
    * Chat Interface with Markdown rendering and input history (final evaluations persist).
    * Role-Specific LLM Selection.
    * Monitor Panel for structured agent logs.
    * Artifact Viewer for text/image/PDF outputs with live updates and working navigation.
    * Token Usage Tracking.
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend (refactored `message_handlers`).
    * LangChain for P-C-E-E pipeline.
    * Task-specific, isolated workspaces with persistent history (SQLite).
3.  **Tool Suite (`backend/tools/`):** (No major changes to toolset itself in this iteration)
    * `TavilyAPISearchTool`, `DeepResearchTool`, `DuckDuckGoSearchRun`, `web_page_reader`, `pubmed_search`, File I/O, Execution Tools.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`. (Refactored message handlers)
-   **Containerization:** Docker, Docker Compose.

## Project Structure

```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── init.py
│   ├── agent.py
│   ├── callbacks.py
│   ├── config.py
│   ├── controller.py      # Updated for previous_step_output
│   ├── db_utils.py
│   ├── evaluator.py       # Updated for session_data_entry
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py # Now a re-exporter
│   ├── message_processing/  # NEW: Granular message handlers
│   │   ├── init.py
│   │   ├── agent_flow_handlers.py # Updated for previous_step_output
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py
│   ├── planner.py         # Updated prompt for "No Tool" expected_outcome
│   ├── server.py          # Updated for handler_args and urllib import
│   └── tools/
│       ├── init.py
│       ├── deep_research_tool.py
│       ├── playwright_search.py
│       ├── standard_tools.py  # Updated get_task_workspace_path
│       └── tavily_search_tool.py
├── css/
│   └── style.css
├── database/
│   └── agent_history.db
├── js/
│   ├── script.js          # Main orchestrator, uses StateManager
│   ├── state_manager.js   # Manages client-side state
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── artifact_ui.js
│       ├── chat_ui.js
│       ├── file_upload_ui.js
│       ├── llm_selector_ui.js
│       ├── monitor_ui.js
│       ├── task_ui.js
│       └── token_usage_ui.js
├── BRAINSTORM.md          # Updated: Current workflow, feedback, immediate ideas
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md              # This file
├── ROADMAP.md             # Updated: Future development plans
├── requirements.txt
└── workspace/
└── <task_id>/
├── plan.md
└── ...
```

## Setup Instructions & Running the Application
(No changes from v2.5 - these remain the same)

## Known Issues
* **UI for Plan Confirmation:** The backend now sends a new message type (`propose_plan_for_confirmation`) which the frontend does not yet handle. This means plan proposals are not currently displayed to the user for confirmation. **This is the next immediate fix.**
* **Chat Clutter:** Intermediate agent thoughts and tool outputs can still make the chat verbose.
* **Agent Cancellation (STOP Button):** May not always be instantaneous.

## Security Warnings
(No changes - these remain the same)

## Next Steps & Future Perspectives
The immediate focus is on resolving the UI for plan confirmation. Following that, key efforts will be:
* **UI/UX Enhancements:** Implementing a concise plan proposal UI, reducing chat clutter by routing intermediate logs to the monitor, and improving overall plan visibility.
* **Color-Coding:** Adding visual cues to the monitor log and LLM selectors.
* **Finalizing Frontend Orchestration:** Completing the refinement of `script.js` (Phase 3.2).
* **Advanced Agent Capabilities & UITL:** As outlined in `ROADMAP.md`.

For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
