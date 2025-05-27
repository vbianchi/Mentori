# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements In Progress)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
**Targeting Version 2.5.3**

**Recent Developments (Leading to v2.5.3 Target):**

* **Core Bug Fixes (Complete):**
    * Resolved a critical `KeyError` in `backend/controller.py` related to prompt formatting with unescaped curly braces.
    * Significantly improved input handling for the `deep_research_synthesizer` tool:
        * The Controller now robustly provides a correctly formatted JSON string from the first attempt (after an initial evaluation-feedback cycle if the agent makes a mistake).
        * The ReAct agent (`agent.py`) prompt has been enhanced to ensure it outputs the direct raw content from tools like `deep_research_synthesizer` as its `Final Answer` for a step.
        * The Step Evaluator (`evaluator.py`) prompt has been made stricter to verify actual content generation against the expected outcome.
    * End-to-end execution of plans involving `deep_research_synthesizer` followed by `write_file` (to save the report) is now functional.
* **Plan Proposal UI & Persistence (Complete):**
    * Frontend now correctly receives and processes `propose_plan_for_confirmation` messages from the backend.
    * Plan proposal UI (summary, "Confirm & Run", "Cancel", "View Details" buttons) appears in the chat.
    * "View Details" button correctly toggles the visibility of the `structured_plan` directly *within* the plan proposal chat block.
    * When a plan is confirmed, the interactive proposal block transforms into a static, non-interactive "Confirmed Plan" message in the chat.
    * Confirmed plans (`confirmed_plan_log`) are correctly rendered as persistent static plan blocks when chat history is loaded.
* **Chat UI & Agent Feedback Refinements (In Progress):**
    * **Direct QA Output:** Final answers for Direct QA intents are displayed in the main chat window.
    * **Agent Thinking Updates:** Backend (`callbacks.py`) sends structured `agent_thinking_update` messages for concise status feedback. Frontend (`script.js`, `chat_ui.js`) handles these.
    * **Final Plan Output in Chat (Partially Improved):** The final message from a plan execution now prioritizes the output of the last successful step. Further refinement is planned to ensure the most relevant artifact or summary is presented.
* **Monitor Log Content:** `callbacks.py` routes verbose intermediate agent thoughts and tool I/O to the Monitor Log.
* **Monitor Log Source Identification (Initial Implementation):**
    * Backend (`callbacks.py`) includes a `log_source` field in `monitor_log` message payloads.
    * Frontend (`monitor_ui.js`) attempts to use this `log_source` to add CSS classes.
* **Backend Stability & Tool Improvements (Ongoing):**
    * Controller (`controller.py`) JSON parsing from LLM outputs improved.

## Core Architecture & Workflow

The ResearchAgent processes user queries through a sophisticated pipeline:
1.  **Intent Classification**: Determines if a query requires direct answering or multi-step planning.
2.  **Planning (if required)**: An LLM-based Planner generates a sequence of steps.
3.  **User Confirmation (for plans)**: The proposed plan is shown to the user for approval.
4.  **Execution**: A Controller validates each step, and an Executor (ReAct agent) carries out the action, using tools as needed. A Step Evaluator assesses each step's outcome, allowing for retries.
5.  **Overall Evaluation**: A final assessment of the plan's success is provided.

For more detailed information on the P-C-E-E pipeline and task flow, please refer to `BRAINSTORM.md`.
For future development plans, see `ROADMAP.md`.

## Key Current Capabilities & Features (Reflecting recent updates)

1.  **UI & User Interaction:**
    * Task Management with persistent storage and reliable UI updates.
    * Chat Interface with Markdown rendering, input history, interactive plan proposals (with inline details and static confirmed state), and agent status updates.
    * Role-Specific LLM Selection.
    * Monitor Panel for structured agent logs (with backend support for source identification).
    * Artifact Viewer for text/image/PDF outputs.
    * Token Usage Tracking.
    * File upload capability to task workspaces.
2.  **Backend Architecture & Logic:**
    * Modular Python backend with refactored message handlers.
    * LangChain for P-C-E-E pipeline (Planner, Controller, Executor, Step Evaluator, Overall Plan Evaluator).
    * Task-specific, isolated workspaces with persistent history (SQLite).
    * Refined plan proposal, confirmation, and cancellation flow.
    * Improved message routing in callbacks for clearer chat vs. monitor distinction.
    * Robust Controller logic for preparing tool inputs, including JSON strings for complex tools.
3.  **Tool Suite (`backend/tools/`):**
    * Includes `TavilyAPISearchTool`, `DeepResearchTool` (input schema expecting `{"query": "..."}` JSON string), `DuckDuckGoSearchRun`, `web_page_reader`, `pubmed_search`, File I/O (`write_file`, `read_file`), `python_package_installer`, `workspace_shell`, and `Python_REPL`.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+) (Modularized: `state_manager.js`, `websocket_manager.js`, `ui_modules/*.js`, `script.js` orchestrator)
-   **Backend:** Python 3.10+ (3.12 in Docker), LangChain, `aiohttp`, `websockets`.
-   **Containerization:** Docker, Docker Compose.

## Project Structure
(Key files recently updated: `backend/controller.py`, `backend/agent.py`, `backend/evaluator.py`, `backend/message_processing/agent_flow_handlers.py`, `backend/tools/deep_research_tool.py`, `frontend/js/script.js`, `frontend/js/ui_modules/chat_ui.js`, `frontend/js/ui_modules/monitor_ui.js`)

```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py             # Updated ReAct prompt for direct tool output
│   ├── callbacks.py
│   ├── config.py
│   ├── controller.py        # Enhanced prompt for JSON tool inputs, fixed formatting bug
│   ├── db_utils.py
│   ├── evaluator.py         # Stricter prompt for content verification
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py # Refined final message delivery
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py
│   ├── planner.py
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       ├── deep_research_tool.py # Input schema `query`
│       ├── playwright_search.py
│       ├── standard_tools.py
│       └── tavily_search_tool.py
├── css/
│   └── style.css            # Pending rules for monitor log color-coding
├── database/
│   └── agent_history.db
├── js/
│   ├── script.js
│   ├── state_manager.js
│   ├── websocket_manager.js
│   └── ui_modules/
│       ├── artifact_ui.js
│       ├── chat_ui.js
│       ├── file_upload_ui.js
│       ├── llm_selector_ui.js
│       ├── monitor_ui.js      # Awaiting CSS for color-coding
│       ├── task_ui.js
│       └── token_usage_ui.js
├── BRAINSTORM.md
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                # This file
├── ROADMAP.md
├── requirements.txt
└── workspace/
    └── <task_id>/
        ├── _plan_proposal_<ID>.md
        ├── _plan_<ID>.md
        └── ... # Tool outputs, e.g., generated reports
```

## Setup Instructions & Running the Application
(No changes from v2.5 - these remain the same)

## Known Issues / Immediate Next Steps (Targeting v2.5.3 Fixes)

* **BUG (High Priority): Chat Input Unresponsive:** After a task completes (Direct QA or Plan), the chat input sometimes becomes unresponsive until a task switch. Likely due to agent status flags (`isAgentRunning`) not being reset correctly.
* **DEBUG (Medium Priority): Monitor Log Color-Coding:** While `log_source` is sent and classes are added in `monitor_ui.js`, the visual differentiation (colors) is not yet appearing. Requires CSS rules in `style.css` and verification of `log_source` consistency.
* **UX (Medium Priority): Refine Final Plan Output in Chat & Chat Flow:**
    * Ensure the most relevant output of a successful plan (e.g., the content of a generated report, not just a success message) is clearly presented in the chat.
    * Improve the overall chat message flow for plan execution to be clearer and less cluttered (e.g., `manus.ai` style discussion).
    * Refine how recoverable errors during step execution are communicated in the chat (avoiding overly alarming messages if retries are in progress).
* **Refine Intermediate Step Chat Output (Ongoing):** Continue to ensure `agent_thinking_update` messages are concise and provide good awareness, while verbose details go to the Monitor Log.

## Security Warnings
(No changes - these remain the same)

## Next Steps & Future Perspectives
The immediate focus is on resolving the chat input responsiveness bug and implementing monitor log color-coding. Following that, efforts will target further refining the user experience for plan outputs and the overall chat message flow.
For a detailed, evolving roadmap and ongoing brainstorming, please see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
