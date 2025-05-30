# BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target & Beyond)

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.
Current Version & State (Targeting v2.5.3 Foundational Fixes):

Recent key advancements and fixes:

  - Core Agent Logic & Tool Integration (Improved).
  - Chat UI/UX Refinement (Significant Progress):
      - **Visual Design & Readability:** Achieved consistent sub-step indentation, adjusted message bubble widths (User/RA/Plan ~60% fit-to-content, Sub-steps ~40%, Step titles ~60% with wrap). Agent Avatar for final RA messages. Blue line removed from RA/Plan messages. General UI and Token area font sizes increased. Role LLM selectors styled with color indicators.
      - **Interactivity:** Collapsible major agent steps and tool outputs (via label click).
      - **Persistence & Consistency:** Confirmed plans loaded from history render consistently.
      - **Bug Fixes:** `read_file` tool output displays correctly and is nested. Chat scroll jump on bubble expand/collapse fixed. Plan persistence in chat now works. Final synthesized answer from agent correctly displayed.
  - Plan Proposal UI & Persistence (COMPLETE).
  - Token Counter UI & Functionality (FIXED & ENHANCED).
  - File Upload Functionality (FIXED).
  - Enhanced In-Chat Tool Feedback & Usability (Core Implemented & Refined).

Immediate Focus & User Feedback / Known Issues / Proposed Enhancements:

1.  **BUG & RE-ENGINEERING - Agent Task Cancellation & STOP Button (NEW HIGH PRIORITY):**
    * **Observation:** Switching UI tasks does not reliably stop the agent processing the previous task; its status updates can bleed into the new task view. The STOP button is currently not effective.
    * **Short-Term Goal (v2.5.3 fix):** Ensure that when a context switch *occurs in the UI*, the backend *robustly cancels* the agent task associated with the *previous* UI context. Make the STOP button fully functional to terminate the currently designated active agent task.
    * **Challenge:** Requires careful management of asyncio tasks on the backend and ensuring cancellation propagates effectively.

2.  **BUG - ARTIFACT VIEWER REFRESH (Medium Priority - Debugging Resumes):** (Details as before)

3.  **UI/UX POLISH (Low Priority for v2.5.3 - Post Critical Fixes):**
    * **A. Chat Message Visuals & Density:** Largely Addressed. Minor review of vertical spacing if needed.
    * **B. Button Placement & Consistency:** Largely Addressed.
    * **C. Monitor Log Readability:** (Details as before - Pending)
    * **D. "Agent Thinking Status" Line Review:** (Details as before - Pending)
    * **E. "View in Artifacts" Link for Tool Outputs (Pending):** (Details as before)
    * **F. Agent Step Announcement Styling (Pending):** (Details as before)

4.  **WARNING - PLAN FILE STATUS UPDATE (Low Priority):** (Details as before)
5.  **REVIEW - "UNKNOWN" HISTORY MESSAGE TYPES (Low Priority - Mostly Addressed):** (Details as before)

Future Brainstorming / More Complex Enhancements (Post v2.5.3):

* **Advanced Multi-Tasking Agent Behavior (User Request):**
    * **Goal:** Allow an agent plan (Task A) to continue running in the background if the user switches the UI to view another task (Task B).
    * **Implications/Requirements:**
        * Backend needs to manage running task state independently of UI's viewed task.
        * WebSocket messages from background tasks must be tagged with `task_id`.
        * Frontend needs to filter incoming messages: display in main chat only if `task_id` matches viewed task.
        * UI indicator (e.g., spinner) in the task list for the actively processing task.
        * Chat input should be disabled globally if any task is processing by the agent for the current session.
        * UI for non-active tasks must render correctly (history, artifacts) without interference.
        * This relies on a fully robust STOP mechanism (see High Priority bug above).
* **Advanced Chat Information Management (Future):** (Details as before)
* **Ongoing Planner & Executor Prompt Engineering:** (Details as before)

Chat UI Simulation Details (Target: `simulation_option6.html` - Achieved Visually as a Base, with further enhancements):
 (No changes to this section)
