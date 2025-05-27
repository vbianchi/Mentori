# ResearchAgent: Project Roadmap (v2.5.3 Target Base)

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

## Guiding Principles for Development

-   Accuracy & Reliability Over Speed
-   User-in-the-Loop (UITL/HITL)
-   Modularity & Maintainability
-   Extensibility

## Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.5.2)

-   UI Framework: Three-panel layout.
-   Backend Infrastructure: Python, WebSockets, `aiohttp`.
-   Task Management: Persistent storage, UI updates.
-   Core Agent Flow (P-C-E-E Pipeline): Intent Classification, Planner, Controller, Executor, Step Evaluator, Overall Plan Evaluator.
-   Core Tools Implemented & Refined.
-   LLM Configuration: Google Gemini & Ollama, role-specific selection.
-   Frontend & Backend Refactoring (Modularization).
-   Backend Plan Proposal Mechanism.

## Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus - Targeting v2.5.3)

1.  Core Agent Execution Stability & Feature Verification (COMPLETE)
    -   `deep_research_synthesizer` & `write_file` Flow: RESOLVED.
    -   Controller Prompt Formatting `KeyError`: RESOLVED.
    -   Backend `IndentationError` in `agent_flow_handlers.py`: RESOLVED.
2.  Refine Chat UI/UX & Message Flow (High Priority - Frontend & Backend Implementation Next)
    -   **Goal:** Implement a highly intuitive and clear chat interface as detailed in `BRAINSTORM.md` and visually represented by `simulation_option6.html`. This includes:
        -   **Visual Hierarchy:** User messages with right side-lines; unified blue outer left side-lines for system/plan/final messages; no side-lines for major step announcements.
        -   **Nested Information:** Indented sub-statuses and agent thoughts, each with their own component-specific colored left side-lines. Agent thoughts displayed with a label and content in a dark box.
        -   **Persistent Bottom Thinking Line:** Last scrollable item in chat, with dynamic component-specific side-line.
        -   **Full Persistence:** All new message structures (major steps, sub-statuses, thoughts) saved to and reloaded from the database.
    -   **Backend Support Status:** Partially complete. Needs enhancements for saving/loading new message types and structuring `agent_thinking_update` with `sub_type`.
        -   `callbacks.py` & `agent_flow_handlers.py`: Update to send/handle new message structures (e.g., `agent_thinking_update` with `sub_type` for thoughts/sub-statuses). Implement DB saving for these.
        -   `db_utils.py`, `server.py`, `task_handlers.py`: Implement DB schema/logic for new message types and ensure they are loaded correctly into history.
    -   **Frontend Implementation Status:** PENDING.
        -   Update `style.css` (from user-provided baseline) for all new message appearances, side-lines (left, right, nested, unified outer), and dark box for thoughts.
        -   Update `chat_ui.js` (from user-provided baseline) to:
            -   Render user messages with right side-lines.
            -   Render system/plan/final messages with unified blue outer left side-lines.
            -   Implement `displayMajorStepAnnouncementUI` for steps without side-lines, including a container for nested content.
            -   Refactor `showAgentThinkingStatusInUI` to append nested sub-statuses and thoughts (with their specific side-lines and styling) to the current major step's container, or update the bottom thinking line.
            -   Ensure `formatMessageContentInternal` handles Markdown for thoughts correctly.
            -   Handle rendering of all historical message types.
        -   Update `script.js` (from user-provided baseline) to dispatch all new and historical message types/structures to the appropriate `chat_ui.js` functions.
3.  BUG FIX (Medium Priority): Chat Input Unresponsive
    -   Issue: Chat input can lock up after a task completes or errors out.
    -   PENDING: Ensure agent status flags (`isAgentRunning` in `StateManager`) are correctly reset and UI re-enables input, potentially tied to the final "Idle" state of the persistent bottom thinking line.
4.  DEBUG (Medium Priority): Monitor Log Color-Coding
    -   Goal: Visually differentiate Monitor Log messages by source.
    -   PENDING/DEBUG: CSS rules in `style.css` need to be created/verified.
5.  Fix (Low Priority): `<strong>` Tag Rendering in Chat
    -   Issue: User noted some HTML tags (like `<strong>`) not rendering correctly.
    -   PENDING: To be addressed during the `chat_ui.js` update by ensuring `innerHTML` is consistently used.

## Phase 3: Advanced Interactivity & Tooling (Mid-Term)

(No changes to this section's general goals yet)

-   Advanced User-in-the-Loop (UITL/HITL) Capabilities.
-   New Tools & Tool Enhancements.
-   Workspace RAG.
-   Improved Agent Memory & Context Management.

## Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)

(No changes to this section's general goals yet)

-   Advanced Re-planning & Self-Correction.
-   User Permissions & Resource Gateway.
-   Streaming Output.
-   Specialized Agent Personas & Workflows.
-   Collaborative Features.

This roadmap will guide our development efforts. Feedback and adjustments are welcome.
