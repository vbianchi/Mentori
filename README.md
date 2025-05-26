# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Targeting Version 2.5.3**

**Recent Developments (Leading to v2.5.3 Target):**

* **Plan Proposal UI & Persistence (Complete):**
    * Frontend now correctly receives and processes `propose_plan_for_confirmation` messages from the backend.
    * Plan proposal UI (summary, "Confirm & Run", "Cancel", "View Details" buttons) appears in the chat.
    * "View Details" button now correctly toggles the visibility of the `structured_plan` (detailed steps) directly *within* the plan proposal chat block, and the button text toggles ("View Details" / "Hide Details").
    * When a plan is confirmed, the interactive proposal block transforms into a static, non-interactive "Confirmed Plan" message in the chat, displaying the summary and expanded steps.
    * Confirmed plans (logged by backend as `confirmed_plan_log`) are now correctly rendered as persistent static plan blocks when chat history is loaded.
* **Chat UI & Agent Feedback Refinements (In Progress):**
    * **Direct QA Output:** Final answers for Direct QA intents (e.g., poem generation) are now correctly displayed in the main chat window.
    * **Agent Thinking Updates:** Backend (`callbacks.py`) now sends more structured `agent_thinking_update` messages to provide concise status feedback in the chat UI (e.g., "Classifying intent...", "Using X tool..."). Frontend (`script.js`, `chat_ui.js`) updated to handle these.
    * **Monitor Log Content:** `callbacks.py` has been revised to route more verbose intermediate agent thoughts, tool inputs/outputs to the Monitor Log, aiming to declutter the main chat.
* **Monitor Log Source Identification (Initial Implementation):**
    * Backend (`callbacks.py`) now includes a `log_source` field in `monitor_log` message payloads.
    * Frontend (`monitor_ui.js`) attempts to use this `log_source` to add CSS classes for potential color-coding (styling/CSS rules pending debug).
* **Backend Stability & Tool Improvements (Ongoing):**
    * Controller (`controller.py`) JSON parsing from LLM outputs improved (handles Markdown backticks).
    * `python_package_installer` handles multiple packages.
    * `TaskWorkspaceShellTool` output handling improved.
    * `Python_REPL` description clarified.

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps.
3.  **User Confirmation (for plans)**: The proposed plan (summary and steps) is shown to the user for approval via the chat interface.
4.  **Execution**: The agent executes each step, involving a Controller, an Executor, and a Step Evaluator.
5.  **Overall Evaluation**: A final assessment of the plan's success is provided.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`.
For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features (Reflecting recent updates)

1.  **UI & User Interaction:**
    * Task Management with persistent storage and reliable UI updates.
    * Chat Interface with Markdown rendering, input history, interactive plan proposals (with inline details and static confirmed state), and improved agent status updates.
    * Role-Specific LLM Selection.
    * Monitor Panel for structured agent logs (with backend support for source identification).
    * Artifact Viewer for text/image/PDF outputs.
    * Token Usage Tracking.
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend with refactored message handlers.
    * LangChain for P-C-E-E pipeline.
    * Task-specific, isolated workspaces with persistent history (SQLite).
    * Refined plan proposal, confirmation, and cancellation flow.
    * Improved message routing in callbacks for clearer chat vs. monitor distinction.
3.  **Tool Suite (`backend/tools/`):**
    * Includes `TavilyAPISearchTool`, `DeepResearchTool` (input schema under review), `DuckDuckGoSearchRun`, `web_page_reader`, `pubmed_search`, File I/O, `python_package_installer`, `workspace_shell`, and `Python_REPL`.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

## Project Structure
(No major changes to overall structure, but individual files like `callbacks.py`, `controller.py`, `agent_flow_handlers.py`, `deep_research_tool.py`, `script.js`, `chat_ui.js`, `monitor_ui.js` have been recently updated.)


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

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Fixes)

* **BUG (Highest Priority): `deep_research_synthesizer` Input Errors:**
    * The Controller, on its first attempt, still sometimes provides a plain string instead of a JSON string to the `deep_research_synthesizer` tool.
    * The tool's input schema (expecting `query`) and the Controller's prompt need to be perfectly aligned to prevent validation errors.
* **BUG (High Priority): Chat Input Unresponsive:** After a task completes (Direct QA or Plan), the chat input sometimes becomes unresponsive until a task switch. This is likely due to agent status flags not being reset correctly.
* **DEBUG (Medium Priority): Monitor Log Color-Coding:**
    * While `log_source` is sent from the backend and classes are added in `monitor_ui.js`, the visual differentiation (colors) is not yet appearing. Requires debugging CSS rules and ensuring `add_monitor_log_func` calls in various backend modules consistently provide `log_source`.
* **VERIFY/REFINE (Medium Priority): Final Plan Output in Chat:** Ensure that for successfully completed plans, a clear and concise summary of the outcome (e.g., executive summary from a report, or key findings) is presented in the chat, not just the `OverallPlanEvaluator`'s assessment text if it's too generic.
* **FEATURE (Planned): Save `deep_research_synthesizer` Output to File:** The tool has been updated to save its report as a `.md` file in the task workspace and prepend a success message about the save to its string output. Artifact refresh should show this file.
* **Refine Intermediate Step Chat Output (Ongoing):** Continue to ensure `agent_thinking_update` messages are concise and provide good awareness, while verbose details go to the Monitor Log.

## Security Warnings
(No changes - these remain the same)

## Next Steps & Future Perspectives
The immediate focus is on resolving the critical bugs with `deep_research_synthesizer` input and chat input responsiveness. Following that, efforts will target debugging the monitor log color-coding and further refining the user experience for plan outputs and agent status updates.

For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
