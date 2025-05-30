# ResearchAgent: AI Assistant for Research Workflows (v2.5.3 - UI/UX Refinements & Multi-Tasking Considerations)

This project provides a functional user interface and backend for an AI agent system designed to assist with research tasks, particularly in fields like bioinformatics and epidemiology. It features a three-panel layout (Tasks, Chat, Monitor/Artifact Viewer) and connects via WebSockets to a Python backend powered by LangChain.
Targeting Version 2.5.3 (with considerations for future multi-tasking enhancements)

**Recent Developments (Leading to v2.5.3 Target):**

-   **Core Bug Fixes & Feature Verification (Largely Complete).**
-   **Chat UI/UX Refinement (Significant Progress):**
    -   **Visual Design & Readability:** Improved message alignment, consistent sub-step indentation, increased general and token area font sizes, HTML tag rendering.
    -   **Interactivity & Layout:** Collapsible major agent steps and tool outputs (via label click). Adjusted message bubble widths (User/RA/Plan ~60% fit-to-content, Sub-steps ~40%). Agent Avatar for final RA messages. Blue line removed from RA/Plan messages. Role LLM selectors styled with color indicators.
    -   **Persistence & Consistency:** Ensured correct rendering and visual consistency for persisted (reloaded) confirmed plans.
    -   **Functionality Fixes:** `read_file` tool output now displays correctly and is properly nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat is now working.
    -   **Completed Features:** Token Counter, File Upload, core In-Chat Tool Feedback.

**Known Issues & Immediate Next Steps (Targeting v2.5.3 Enhancements & Fixes):**

-   **BUG: Agent Task Cancellation & STOP Button (High Priority):**
    * Current behavior: Switching tasks does not reliably cancel the ongoing agent process in the previous task. The STOP button is not fully functional.
    * **Goal:** Implement robust agent task cancellation. Ensure the STOP button reliably terminates the actively processing agent task. Solidify cancellation logic when switching UI task context (current design intends to cancel, but this is not effective).
-   **BUG: ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Resumes):** Artifact viewer inconsistent auto-update.
-   **UI/UX POLISH (Low Priority - Most critical items addressed):**
    * Finalize "View [artifact] in Artifacts" links.
    * Review global "agent-thinking-status" line behavior.
    * Consider further styling for step announcements (e.g., boxing).
-   **DEBUG: Monitor Log Color-Coding (Low Priority).**
-   **WARNING: PLAN FILE STATUS UPDATE (Low Priority).**
-   **REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority).**

**Future Considerations (Post v2.5.3 - Based on Recent Brainstorming):**
-   Allow agent tasks to continue running in the background if the user switches UI context to another task.
-   Implement a visual indicator in the task list for actively processing tasks.
-   Ensure UI for non-processing tasks renders correctly while another task runs in the background (requires message filtering).
-   Refine chat input disabling logic based on global agent activity.

## Core Architecture & Workflow
(No changes to this section)

## Key Current Capabilities & Features
(Update to reflect fixes and completed items from "Recent Developments")
1.  **UI & User Interaction:**
    -   Task Management: Create, delete, rename.
    -   Chat Interface:
        -   **Rendering & Readability:** Improved alignment, indentation, font sizes. Step titles wrap.
        -   **Collapsible Elements:** Major agent steps & tool outputs.
        -   **In-Chat Tool Feedback:** Tool outputs (including `read_file`) displayed, nested, and collapsible.
        -   **Copy to Clipboard:** For thoughts, tool outputs, final answers, code.
        -   **Visual Cues:** Agent avatar. Color-coded LLM role selectors. No blue line on RA/Plan messages.
        -   **Message Widths:** User/RA/Plan ~60% (RA fit-to-content). Sub-steps ~40%.
        -   **Persistence:** All message types, including confirmed plans, saved and reloaded consistently.
    -   Role-Specific LLM Selection.
    -   Monitor Panel & Artifact Viewer.
    -   Token Usage Tracking (FIXED & ENHANCED).
    -   File Upload Capability (FIXED).
2.  **Backend Architecture & Logic:**
    -   (No major changes here from previous summary, core PCEE pipeline remains)

## Tech Stack
(No changes)

## Project Structure
(CSS and JS file descriptions updated for clarity on recent enhancements)
```
ResearchAgent/
├── .env                   # Environment variables (GITIGNORED)
├── .env.example           # Example environment variables
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── agent.py
│   ├── callbacks.py         # Handles tool_result_for_chat, persistence
│   ├── config.py
│   ├── controller.py        # Refined for "No Tool" synthesis steps
│   ├── db_utils.py
│   ├── evaluator.py         # Updated for final_answer_content handling
│   ├── intent_classifier.py
│   ├── llm_setup.py
│   ├── message_handlers.py
│   ├── message_processing/
│   │   ├── agent_flow_handlers.py # Updated for final answer display, cancellation logic (target)
│   │   └── ... (other handlers)
│   ├── planner.py
│   ├── server.py            # Manages agent tasks, cancellation (target)
│   └── tools/
│       └── ...
├── css/
│   └── style.css                # Enhanced for all recent UI refinements
├── js/
│   ├── script.js                # Orchestrator, handles STOP button (target for robust cancellation)
│   ├── state_manager.js         # To manage activeProcessingTaskId (future)
│   └── ui_modules/
│       ├── chat_ui.js           # All recent rendering, collapsibility, avatar, plan fixes
│       ├── task_ui.js           # Target for running task indicator (future)
│       └── ...
├── BRAINSTORM.md                # Updated with multi-tasking ideas
├── Dockerfile
├── docker-compose.yml
├── index.html
├── README.md                      # This file
├── ROADMAP.md                     # Updated with multi-tasking goals
└── simulation_option6.html
```

## Setup Instructions & Running the Application
(No changes)

## Previously Fixed/Implemented in v2.5.3 development cycle:
-   **ENHANCEMENT: In-Chat Tool Feedback & Usability.**
-   **ENHANCEMENT: Chat UI/UX Major Improvements:** Collapsible steps & tool outputs, agent avatar, alignment, widths, font sizes, LLM selector colors, no blue lines on RA/Plan.
-   **BUG FIX: `read_file` output visibility & nesting.**
-   **BUG FIX: Chat scroll jump on expand/collapse.**
-   **BUG FIX: Plan persistence and consistent rendering from history.**
-   **FILE UPLOAD (FIXED).**
-   **TOKEN COUNTER (FIXED & ENHANCED).**

## Security Warnings
(No changes)

## Next Steps & Future Perspectives
The immediate high-priority focus is to **implement robust agent task cancellation and ensure the STOP button is fully functional.** Subsequently, we will address the artifact viewer refresh bug. Longer-term considerations include allowing background task processing. For details, see **`ROADMAP.md`** and **`BRAINSTORM.md`**.
