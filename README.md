# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - Critical Fixes & Future Enhancements)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. [cite: 3244] It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain. [cite: 3244]
Targeting Version 2.5.3 (with a primary focus on critical bug fixes and considerations for future enhancements).

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Ongoing).**
-   **Chat UI/UX Refinement (Significant Progress):**
    -   **Visual Design & Readability:** Improved message alignment, consistent sub-step indentation, increased general and token area font sizes, HTML tag rendering. [cite: 3245]
    -   **Interactivity & Layout:** Collapsible major agent steps and tool outputs (via label click). [cite: 3246] Adjusted message bubble widths (User/RA/Plan ~60% fit-to-content, Sub-steps ~40%). [cite: 3247] Agent Avatar for final RA messages. [cite: 3247] Blue line removed from RA/Plan messages. [cite: 3247] Role LLM selectors styled with color indicators. [cite: 3248]
    -   **Persistence & Consistency:** Ensured correct rendering and visual consistency for persisted (reloaded) confirmed plans. [cite: 3249]
    -   **Functionality Fixes:** `read_file` tool output now displays correctly and is properly nested. [cite: 3250] Chat scroll jump on bubble expand/collapse fixed. [cite: 3251] Plan persistence in chat is now working. [cite: 3251]
    -   **Completed Features:** Token Counter[cite: 3252], File Upload[cite: 3252], core In-Chat Tool Feedback[cite: 3252].

**Known Issues & Immediate Next Steps (Targeting V1.0 Go-Live within 2 Months):**

-   **CRITICAL (MUST HAVE): BUG & RE-ENGINEERING: Agent Task Cancellation & STOP Button:**
    * Current behavior: Switching UI tasks or using the STOP button does not reliably cancel/stop the agent processing the current task. [cite: 3189, 3190, 3191] Status updates from a backgrounded task can bleed into a newly selected task's view. [cite: 3190] The STOP button is not fully functional. [cite: 3191]
    * **Goal for V1.0:** Implement robust agent task cancellation. [cite: 3191] Ensure the STOP button reliably terminates the actively processing agent task. [cite: 3192] Solidify cancellation logic when switching UI task context. [cite: 3193] This is crucial for system stability and usability.
-   **HIGH (MUST HAVE): BUG: ARTIFACT VIEWER REFRESH:**
    * Artifact viewer does not consistently or immediately auto-update after file writes mid-plan. [cite: 3195, 3257] Reliable viewing of generated artifacts is essential.
-   **HIGH (MUST HAVE): AGENT CAPABILITIES: Robust Step Evaluation & Basic Retry:**
    * Ensure the PCEE loop's Evaluator component reliably assesses step success, particularly checking if actual content was produced vs. a description of it. Ensure the retry mechanism effectively uses evaluator feedback for simple retries. This is key for improving the efficiency of scientific results.
-   **HIGH (MUST HAVE): DEV OPS / STABILITY: Comprehensive Testing (Core Functionality):**
    * Implement/expand unit and integration tests for critical backend and frontend components, especially task cancellation, agent lifecycle, and core tool usage.
-   **MEDIUM (SHOULD HAVE): UI/UX: Finalize "View [artifact] in Artifacts" Links:**
    * Complete functionality for links from tool output messages to the artifact viewer to enhance workflow efficiency. [cite: 3198, 3258]
-   **LOW (NICE TO HAVE) UI/UX POLISH:**
    * Review global "agent-thinking-status" line behavior and appearance. [cite: 3196, 3259]
    * Consider further styling for agent step announcements (e.g., boxing, copy button for step title). [cite: 3197, 3260]
    * Fix small bug: Copy button sometimes centered in chat UI after simple message.
-   **LOW (NICE TO HAVE) DEBUGGING & REVIEWS:**
    * **DEBUG: Monitor Log Color-Coding:** Verify/implement CSS for log differentiation. [cite: 3201, 3260]
    * **WARNING: PLAN FILE STATUS UPDATE:** Address backend logs warnings about not finding step patterns. [cite: 3199]
    * **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES:** Confirm handling of internal DB message types. [cite: 3200]

**Future Considerations & Enhancements (Post V1.0 Go-Live):**

This section outlines features and improvements that will enhance ResearchAgent's capabilities beyond the initial V1.0 release, focusing on user-centricity and scientific efficiency.

**SHOULD HAVE (Important for V1.x releases):**

-   **Enhanced Agent Capabilities & Efficiency:**
    * **Improved Agent Memory / Workspace RAG (Basic):** Implement basic retrieval from current task workspace files to improve contextual understanding for the agent.
    * **Streaming LLM Responses (Final Answers):** Implement token-by-token streaming for agent's final answers for better perceived responsiveness.
    * **Refined Error Parsing & Reporting:** Improve how the agent understands and reports errors from tools or LLM calls.
    * **Robust Asynchronous Task Cancellation (Advanced):** Post initial STOP button fix, explore more advanced `asyncio` patterns (e.g., `asyncio.Event`, `asyncio.shield`).
-   **Multi-Tasking & User Control:**
    * **Asynchronous Background Task Processing (Basic Stop/Switch):** Ensure that if full background processing is deferred, task switching at least reliably stops the previous task and cleans up its state. [cite: 3202] Global chat input disabling if any task is processing. [cite: 3205]
    * **Optional Tools (e.g., Web Search):** Allow users to enable/disable tools like Tavily web search for privacy/cost. Backend to respect choices and UI to communicate impact.
-   **Advanced User-in-the-Loop (UITL/HITL) Capabilities:**
    * Introduce more sophisticated mechanisms for users to intervene, guide, or correct the agent during plan execution.

**NICE TO HAVE (Valuable additions for future iterations):**

-   **Advanced Agent Reasoning & Self-Correction (Full):**
    * Explore full meta-cognition, self-debugging/rewriting capabilities, and dynamic plan adjustment.
    * Long-term learning from failure.
-   **Comprehensive Tool Ecosystem Expansion:**
    * **Enhanced PDF Parsing:** Improve `read_file` for more structured PDF content extraction.
    * **Rscript Execution:** Add secure support for running R scripts.
    * Further tools for literature review (NER, Relation Extraction), advanced data analysis/visualization, specialized bioinformatics tasks (BLAST, etc.), and document preparation (Pandoc, citation).
-   **UI/UX & Workspace Enhancements:**
    * **Integrated Folder Viewer:** Enhance the artifact panel for better workspace management.
    * **Dedicated "Agent Activity/Steps" Panel:** Create a separate UI area for a structured, real-time view of the agent's plan steps.
    * Direct artifact manipulation from UI (delete, rename).
    * Further chat information management (filtering, searching, summarizing).
-   **Backend & Architecture:**
    * Scalability improvements for handling more users/agents.
    * Specialized Agent Personas/Configurations.
-   **Deployment & DevOps:**
    * Broader local/cloud deployment options.

## Core Architecture & Workflow
(No changes to this section - Assuming it's up-to-date unless specified)

## Key Current Capabilities & Features
(Update to reflect fixes and completed items from "Recent Developments")
1.  **UI & User Interaction:**
    -   Task Management: Create, delete, rename. [cite: 3264]
    -   Chat Interface:
        -   **Rendering & Readability:** Improved alignment, indentation, font sizes. [cite: 3265] Step titles wrap. [cite: 3266]
        -   **Collapsible Elements:** Major agent steps & tool outputs. [cite: 3266]
        -   **In-Chat Tool Feedback:** Tool outputs (including `read_file`) displayed, nested, and collapsible. [cite: 3267]
        -   **Copy to Clipboard:** For thoughts, tool outputs, final answers, code. [cite: 3268]
        -   **Visual Cues:** Agent avatar. [cite: 3269] Color-coded LLM role selectors. [cite: 3269]
        -   **Message Widths:** User/RA/Plan ~60% (RA fit-to-content). [cite: 3269] Sub-steps ~40%. [cite: 3270]
        -   **Persistence:** All message types, including confirmed plans, saved and reloaded consistently. [cite: 3270]
    -   Role-Specific LLM Selection. [cite: 3271]
    -   Monitor Panel & Artifact Viewer. [cite: 3264, 3271]
    -   Token Usage Tracking (FIXED & ENHANCED). [cite: 3171, 3272]
    -   File Upload Capability (FIXED). [cite: 3172, 3272]
2.  **Backend Architecture & Logic:**
    -   Python server using WebSockets (`websockets`) and `aiohttp`. [cite: 3183]
    -   Uses LangChain; supports Gemini & Ollama. [cite: 3184]
    -   Task-specific workspaces and SQLite for persistent history. [cite: 3184]
    -   Modularized `message_handlers.py`. [cite: 3185]
    -   Token counting for all agent roles. [cite: 3185]
    -   File upload endpoint and processing logic. [cite: 3186]
    -   Structured `tool_result_for_chat` messages for in-chat tool output display. [cite: 3187]

## Tech Stack
(No changes - Assuming it's up-to-date unless specified)

## Project Structure
(CSS and JS file descriptions updated for clarity on recent enhancements)

ResearchAgent/├── .env                       # Environment variables (GITIGNORED)├── .env.example               # Example environment variables├── .gitignore├── backend/│   ├── init.py│   ├── agent.py│   ├── callbacks.py           # Handles tool_result_for_chat, persistence│   ├── config.py│   ├── controller.py          # Refined for "No Tool" synthesis steps│   ├── db_utils.py│   ├── evaluator.py           # Updated for final_answer_content handling│   ├── intent_classifier.py│   ├── llm_setup.py│   ├── message_handlers.py│   ├── message_processing/│   │   └── agent_flow_handlers.py # Updated for final answer display, cancellation logic (target)│   │   └── ... (other handlers)│   ├── planner.py│   ├── server.py                # Manages agent tasks, cancellation (target)│   └── tools/│       └── ...├── css/│   └── style.css                # Enhanced for all recent UI refinements (v2.5.3)├── js/│   ├── script.js                # Orchestrator, handles STOP button (target for robust cancellation)│   ├── state_manager.js         # To manage activeProcessingTaskId (future multi-tasking)│   └── ui_modules/│       ├── chat_ui.js           # All recent rendering, collapsibility, avatar, plan fixes (v2.5.3)│       ├── task_ui.js           # Target for running task indicator (future multi-tasking)│       └── ...├── BRAINSTORM.md                # Updated with multi-tasking ideas├── Dockerfile├── docker-compose.yml├── index.html├── README.md                    # This file├── ROADMAP.md                   # Updated with multi-tasking goals└── simulation_option6.html
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

## Future Perspectives & Ideas (Post V1.0)
*(This section is now covered by "Future Considerations & Enhancements (Post V1.0 Go-Live)" above and can be considered merged/replaced by it for brevity, or specific unique points can be integrated if necessary. The new section is more structured based on our recent prioritization.)*

## Security Warnings
(Standard security considerations apply. Ensure API keys and sensitive configurations are managed securely and not exposed publicly. Review dependencies for vulnerabilities.)

## Contributing
(Contributions are welcome! Please follow standard practices for pull requests, issue reporting, and coding style. More detailed guidelines to be added.)

## License
(Specify your project's license here, e.g., MIT, Apache 2.0.)

