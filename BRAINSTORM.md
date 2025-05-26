BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)
====================================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project. For longer-term plans and phased development, please see `ROADMAP.md`.

**Current Version & State (v2.5.2 base, with recent fixes for v2.5.3 target):**

Recent key advancements and fixes:
* **Agent Logic & Stability:**
    * "Poem discrepancy" (Controller using previous step output) remains fixed. [cite: 2075, 2076]
    * Controller's JSON parsing from LLM output is more robust (handles Markdown wrappers).
    * ReAct agent prompt in `agent.py` refined for better tool selection formatting.
* **Message Persistence:** Overall Plan Evaluator's final assessment message correctly saved and reloaded. [cite: 2077]
* **Backend Plan Proposal:**
    * Now correctly sends `propose_plan_for_confirmation` message with `plan_id`, summary, and structured plan. [cite: 2598]
    * Saves `_plan_proposal_<plan_id>.md` artifact on proposal.
    * Handles `cancel_plan_proposal` messages from the frontend. [cite: 2598]
* **Tool Enhancements:**
    * `python_package_installer` now handles multiple space/comma-separated packages.
    * `workspace_shell` provides more reliable STDOUT.
    * `Python_REPL` description clarified to guide LLM towards simpler uses.
* **Frontend Refactoring:** Modular UI components and `StateManager` are in place. [cite: 2078]
* **Backend Refactoring:** Modularized `message_handlers` in `message_processing` sub-package. [cite: 2079]
* **UI Functionality:**
    * Task management, file uploads, artifact viewing basics are functional. [cite: 2081]
    * **Plan proposal UI is now appearing in the chat** with summary and action buttons. [cite: 2598]

**Immediate Focus & User Feedback:**

1.  **Complete UI for Plan Proposal Interaction (High Priority):**
    * **Issue (Partially Resolved):** Backend sends `propose_plan_for_confirmation`, and a basic proposal UI appears. [cite: 2598]
    * **Remaining Frontend Tasks:**
        * **Inline "View Details":** The "View Details" button currently shows an "Attempting to view artifact..." message. [cite: 2598] It needs to be changed to expand/collapse the structured plan steps *directly within the chat UI proposal block*. This is the preferred behavior for quick review.
        * **Persistent Confirmed Plan in Chat:** When a plan is confirmed, the interactive proposal block needs to transform into a static, non-interactive message in the chat, displaying the confirmed plan (summary and steps). This static representation should be saved to the database (backend already saves a `confirmed_plan_log` message) and correctly rendered from chat history on reload. [cite: 2598]
    * **Goal:** A clean, interactive, and persistent way for users to review and confirm plans directly in the chat.

2.  **Chat Clutter & Plan Display Format (High Priority - After above Plan UI fixes):**
    * **User Feedback:** The chat UI can still be too cluttered with intermediate agent thoughts/tool outputs. The goal is a cleaner interface, more like the `manus.ai` example, distinguishing clearly between direct agent-user messages and status/progress updates. [cite: 2085, 2086]
    * **Proposed Solution (being implemented iteratively):**
        * **Concise Plan Proposal:** Addressed with the new UI.
        * **"View Details":** To be changed to inline expansion (see point 1). The `_plan_proposal_<ID>.md` artifact remains for persistence. [cite: 2089]
        * **Persistent Confirmed Plan:** Addressed by point 1. The `_plan_<ID>.md` (execution log) artifact is created upon confirmation.
        * **Intermediate Outputs:** Route most intermediate execution details (thoughts, tool inputs/outputs) primarily to the Monitor Log. [cite: 2091] The main chat should show high-level progress via the "Agent Thinking" status line and final answers/key results. [cite: 2092]

3.  **Color-Coding UI Elements (Medium Priority):**
    * **User Idea:** Visually differentiate messages in the Monitor Log based on the agent component (Planner, Controller, Executor, Evaluator). [cite: 2093]
    * **Extension:** Link these colors to the LLM selector dropdowns. [cite: 2094]
    * **Benefit:** Improved readability and traceability. [cite: 2095]

**Current Workflow Example (Heatmap Generation - with recent fixes):**

1.  User: "Create a set of 50 random genes values in 6 samples. Then create a heatmap... save as png. Do not use python REPL tool." [cite: 701, 702, 703]
2.  Intent Classifier: PLAN. [cite: 705]
3.  Planner: Generates a multi-step plan (e.g., Install packages, Generate script, Write script to file, Execute script, Confirm). [cite: 706]
4.  Backend: Saves `_plan_proposal_<ID>.md`. Sends `propose_plan_for_confirmation` with summary, plan ID, and structured plan to UI. [cite: 706]
5.  Frontend: Displays proposal with "View Details" (inline expansion pending), "Confirm & Run", "Cancel" buttons.
6.  User Confirms.
7.  Frontend: Transforms proposal UI into a static "Confirmed Plan" message. Sends `execute_confirmed_plan` to backend.
8.  Backend: Saves `confirmed_plan_log` to DB. Creates `_plan_<ID>.md`. Starts execution.
    * **Step 1: Install Packages**
        * Controller -> `python_package_installer` tool with input "numpy pandas seaborn". [cite: 711, 712]
        * Executor -> Calls tool. Tool installs packages sequentially. [cite: 718, 719, 720, 721]
        * Step Evaluator -> Confirms success. [cite: 723]
    * **Step 2: Write Script File**
        * Controller -> `write_file` tool with path and script content. [cite: 726]
        * Executor -> Calls tool (may self-correct input format for `:::`). Tool writes file. [cite: 729, 730]
        * Step Evaluator -> Confirms success. [cite: 732]
    * **Step 3: Execute Script**
        * Controller -> `workspace_shell` tool with `python generate_heatmap.py`. [cite: 736]
        * Executor -> Calls tool. Script runs (output now better captured by `workspace_shell`). [cite: 742, 747]
        * Step Evaluator -> Confirms success (based on Executor's final answer claiming file creation, verified by `ls` in next step). [cite: 750]
    * ... (Other steps like confirm file, summarize)
9.  Overall Plan Evaluator: Assesses overall success. [cite: 787]
10. Final agent message sent to chat and saved. [cite: 790]
