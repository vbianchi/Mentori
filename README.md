# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - Critical Fixes & Tool System Refactor)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.

**Targeting Version 2.5.3 (Post-initial "Plug and Play" Tool Refactor).**

**Recent Developments (Leading to current state):**

-   **Architectural Refactor: "Plug and Play" Tool System (Core Implemented):**
    * Successfully refactored the tool management system.
    * General-purpose tools (e.g., web search, web page reading, package installation, PubMed search, Python REPL, deep research synthesis) are now defined in individual Python scripts (`backend/tools/your_tool_name_tool.py`).
    * Tools are dynamically loaded at startup based on a central JSON configuration file (`backend/tool_config.json`).
    * This new architecture streamlines the integration of new tools and improves system maintainability.
    * Task-specific tools (file system operations: `read_file`, `write_file`, `workspace_shell`) are also integrated into this loading mechanism via runtime context injection managed by the `tool_loader`.
    * All 6 general-purpose tools and 3 task-specific tools are confirmed to be loading and available to the agent's core components (Planner, Controller).
-   **Core Bug Fixes & Feature Verification (Ongoing).**
-   **Chat UI/UX Refinement (Significant Progress - features as previously listed in `prompt.txt`):**
    * Visual Design & Readability: Improved message alignment, consistent sub-step indentation, increased general and token area font sizes, HTML tag rendering.
    * Interactivity & Layout: Collapsible major agent steps and tool outputs (via label click). Adjusted message bubble widths (User/RA/Plan ~60% fit-to-content, Sub-steps ~40%, Step titles ~60% with wrap). Agent Avatar for final RA messages. Blue line removed from RA/Plan messages. Role LLM selectors styled with color indicators.
    * Persistence & Consistency: Ensured correct rendering and visual consistency for persisted (reloaded) confirmed plans.
    * Functionality Fixes: `read_file` tool output now displays correctly and is properly nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat is now working. Final synthesized answer from agent correctly displayed.
    * Completed Features: Token Counter, File Upload, core In-Chat Tool Feedback, Plan Proposal UI & Persistence.

**Known Issues & Immediate Next Steps (Targeting V1.0 Go-Live within 2 Months - priorities adjusted post-tool refactor):**

-   **CRITICAL (MUST HAVE): BUG & RE-ENGINEERING: Agent Task Cancellation & STOP Button:**
    * Current behavior: Switching UI tasks or using the STOP button does not reliably cancel/stop the agent processing the current task. Status updates from a backgrounded task can bleed into a newly selected task's view. The STOP button is not fully functional.
    * **Goal for V1.0:** Implement robust agent task cancellation. Ensure the STOP button reliably terminates the actively processing agent task. Solidify cancellation logic when switching UI task context. This is crucial for system stability and usability.
-   **HIGH (MUST HAVE): BUG: ARTIFACT VIEWER REFRESH:**
    * Artifact viewer does not consistently or immediately auto-update after file writes mid-plan. Reliable viewing of generated artifacts is essential.
-   **HIGH (MUST HAVE): AGENT CAPABILITIES: Robust Step Evaluation & Basic Retry:**
    * Ensure the PCEE loop's Evaluator component reliably assesses step success, particularly checking if actual content was produced vs. a description of it.
    * Ensure the retry mechanism (currently `agent_max_step_retries=1`) effectively uses evaluator feedback for simple retries, especially for "No Tool" steps where the LLM needs to provide direct content. This is key for improving the efficiency of scientific results.
-   **HIGH (MUST HAVE): DEV OPS / STABILITY: Comprehensive Testing (Core Functionality):**
    * Implement/expand unit and integration tests for critical backend and frontend components, especially task cancellation, agent lifecycle, and core tool usage (including newly refactored tools).
-   **MEDIUM (SHOULD HAVE): "Plug and Play" Tool System Refinements:**
    * **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas for more robust validation and to aid agent understanding (leveraging Pydantic `args_schema`).
    * **Develop New Tool Integration Guide:** Create documentation and templates for adding new tools to the system, explaining the `tool_config.json` structure and `BaseTool` class requirements.
-   **MEDIUM (SHOULD HAVE): UI/UX: Finalize "View [artifact] in Artifacts" Links:**
    * Complete functionality for links from tool output messages to the artifact viewer to enhance workflow efficiency.
-   **LOW (NICE TO HAVE) UI/UX POLISH:**
    * Review global "agent-thinking-status" line behavior and appearance.
    * Consider further styling for agent step announcements (e.g., boxing, copy button for step title).
    * Fix small bug: Copy button sometimes centered in chat UI after simple message.
    * **UI for Tool Status (Traffic Lights):** Display configured tools and their load status in Agent Workspace based on backend data from new tool loader (as per `BRAINSTORM.md`).
-   **LOW (NICE TO HAVE) DEBUGGING & REVIEWS:**
    * **DEBUG: Monitor Log Color-Coding:** Verify/implement CSS for log differentiation.
    * **WARNING: PLAN FILE STATUS UPDATE:** Address backend logs warnings about not finding step patterns.
    * **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES:** Confirm handling of internal DB message types (e.g., `monitor_user_input`).

**Future Considerations & Enhancements (Post V1.0 Go-Live):**

This section outlines features and improvements that will enhance ResearchAgent's capabilities beyond the initial V1.0 release, focusing on user-centricity and scientific efficiency.

**SHOULD HAVE (Important for V1.x releases):**

-   **Enhanced Agent Capabilities & Efficiency:**
    * **Improved Agent Memory / Workspace RAG (Basic):** Implement basic retrieval from current task workspace files to improve contextual understanding for the agent. Focus on making `read_file` and tool outputs more seamlessly available to subsequent steps.
    * **Streaming LLM Responses (Final Answers):** Implement token-by-token streaming for agent's final answers for better perceived responsiveness.
    * **Refined Error Parsing & Reporting:** Improve how the agent understands and reports errors from tools or LLM calls, making it easier to debug or for the evaluator to suggest corrections.
    * **Robust Asynchronous Task Cancellation (Advanced):** Post initial STOP button fix, explore more advanced `asyncio` patterns (e.g., `asyncio.Event`, `asyncio.shield`) for deeper cancellation robustness.
-   **Multi-Tasking & User Control:**
    * **Asynchronous Background Task Processing (Basic Stop/Switch):** Ensure that if full background processing is deferred, task switching at least reliably stops the previous task and cleans up its state to prevent interference. Global chat input disabling if any task is processing.
    * **Optional Tools (e.g., Web Search):** Allow users to enable/disable tools (via `tool_config.json` `enabled` flag or UI) for privacy/cost. Backend to respect choices and UI to communicate impact.
-   **Advanced User-in-the-Loop (UITL/HITL) Capabilities:**
    * Introduce more sophisticated mechanisms for users to intervene, guide, or correct the agent during plan execution.

**NICE TO HAVE (Valuable additions for future iterations):**

-   **Advanced Agent Reasoning & Self-Correction (Full):**
    * Explore full meta-cognition, self-debugging/rewriting capabilities, and dynamic plan adjustment.
    * Long-term learning from failure.
-   **Comprehensive Tool Ecosystem Expansion (Leveraging new "Plug and Play" system):**
    * **Enhanced PDF Parsing:** Improve `read_file` for more structured PDF content extraction if needed.
    * **Rscript Execution:** Add secure support for running R scripts (this will be a new tool).
    * Further tools for literature review (NER, Relation Extraction), advanced data analysis/visualization, specialized bioinformatics tasks (BLAST, etc.), and document preparation (Pandoc, citation).
-   **UI/UX & Workspace Enhancements:**
    * **Integrated Folder Viewer:** Enhance the artifact panel for better workspace management.
    * **Dedicated "Agent Activity/Steps" Panel:** Create a separate UI area for a structured, real-time view of the agent's plan steps.
    * Direct artifact manipulation from UI (delete, rename).
    * Further chat information management (filtering, searching, summarizing).
-   **Backend & Architecture:**
    * Scalability improvements for handling more users/agents.
    * Specialized Agent Personas/Configurations.
    * **Pydantic v2 Migration:** Update codebase to use Pydantic v2 directly, addressing LangChain deprecation warnings.
-   **Deployment & DevOps:**
    * Broader local/cloud deployment options.

## Core Architecture & Workflow
(No changes to this section - Assuming it's up-to-date unless specified from `prompt.txt`)

## Key Current Capabilities & Features
(Update to reflect tool refactor and other fixes)
1.  **UI & User Interaction:**
    -   Task Management: Create, delete, rename.
    -   Chat Interface:
        -   **Rendering & Readability:** Improved alignment, indentation, font sizes. Step titles wrap.
        -   **Collapsible Elements:** Major agent steps & tool outputs.
        -   **In-Chat Tool Feedback:** Tool outputs (including `read_file`) displayed, nested, and collapsible.
        -   **Copy to Clipboard:** For thoughts, tool outputs, final answers, code.
        -   **Visual Cues:** Agent avatar. Color-coded LLM role selectors.
        -   **Message Widths:** User/RA/Plan ~60% (RA fit-to-content). Sub-steps ~40%.
        -   **Persistence:** All message types, including confirmed plans, saved and reloaded consistently.
    -   Role-Specific LLM Selection.
    -   Monitor Panel & Artifact Viewer.
    -   Token Usage Tracking (FIXED & ENHANCED).
    -   File Upload Capability (FIXED).
2.  **Backend Architecture & Logic:**
    -   Python server using WebSockets (`websockets`) and `aiohttp`.
    -   Uses LangChain; supports Gemini & Ollama.
    -   Task-specific workspaces and SQLite for persistent history.
    -   Modularized `message_handlers.py`.
    -   Token counting for all agent roles.
    -   File upload endpoint and processing logic.
    -   Structured `tool_result_for_chat` messages for in-chat tool output display.
    -   **"Plug and Play" Tool System:** General-purpose and task-specific tools are dynamically loaded from `tool_config.json`, allowing easier integration and management. Each tool typically resides in its own Python module.

## Tech Stack
(No changes - Assuming it's up-to-date unless specified from `prompt.txt`)

## Project Structure
(Reflects new tool files and configuration)

ResearchAgent/
├── .env                       # Environment variables (GITIGNORED)
├── .env.example               # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py
│   ├── callbacks.py           # Handles tool_result_for_chat, persistence
│   ├── config.py
│   ├── controller.py          # Refined for "No Tool" synthesis steps
│   ├── db_utils.py
│   ├── evaluator.py           # Updated for final_answer_content handling
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── __init__.py
│   │   ├── agent_flow_handlers.py # Updated for tool summary, cancellation logic (target)
│   │   ├── config_handlers.py
│   │   ├── operational_handlers.py
│   │   └── task_handlers.py
│   ├── planner.py
│   ├── server.py                # Manages agent tasks, cancellation (target)
│   ├── tool_config.json       # **NEW**: Central configuration for dynamic tool loading
│   ├── tool_loader.py         # **NEW**: Module for loading tools from tool_config.json
│   └── tools/
│       ├── __init__.py
│       ├── standard_tools.py    # Core tool logic, get_dynamic_tools, task-specific tool classes, helper functions
│       ├── tavily_search_tool.py
│       ├── web_page_reader_tool.py
│       ├── python_package_installer_tool.py
│       ├── pubmed_search_tool.py
│       ├── python_repl_tool.py
│       └── deep_research_tool.py
├── css/
│   └── style.css                # Enhanced for all recent UI refinements
├── js/
│   ├── script.js                # Orchestrator, handles STOP button (target for robust cancellation)
│   ├── state_manager.js         # Manages UI state
│   └── ui_modules/
│       ├── artifact_ui.js
│       ├── chat_ui.js           # All recent rendering, collapsibility, avatar, plan fixes
│       ├── file_upload_ui.js
│       ├── llm_selector_ui.js
│       ├── monitor_ui.js
│       ├── task_ui.js
│       └── token_usage_ui.js
├── BRAINSTORM.md                # Updated with current focus
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                    # This file
├── ROADMAP.md                   # Updated with refactor completion
├── UI_UX_style.md               # UI/UX refinement notes
└── simulation_option6.html      # UI simulation/sandbox

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/vbianchi/ResearchAgent.git](https://github.com/vbianchi/ResearchAgent.git)
    cd ResearchAgent
    ```
2.  **Configure environment variables:**
    Copy the example `.env` file:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` with your API keys (GOOGLE_API_KEY, TAVILY_API_KEY, etc.) and other settings.
3.  **Build and run with Docker Compose:**
    ```bash
    docker compose up --build
    ```
4.  **Access the application:**
    * UI: `http://localhost:8000`
    * Backend WebSocket server: `ws://localhost:8765`
    * Backend File server: `http://localhost:8766` (internal, used by backend)

## Security Warnings
(Standard security considerations apply. Ensure API keys and sensitive configurations are managed securely and not exposed publicly. Review dependencies for vulnerabilities.)

## Contributing
(Contributions are welcome! Please follow standard practices for pull requests, issue reporting, and coding style. More detailed guidelines to be added.)

## License
(Specify your project's license here, e.g., MIT, Apache 2.0.)
