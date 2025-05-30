# ResearchAgent: Project Roadmap (v2.0.0 Target & Beyond)

This document outlines the planned development path for the ResearchAgent project. It is a living document and will be updated as the project evolves.

## Guiding Principles for Development
(Unchanged)

## Phase 1: Core Stability & Foundational Tools (Largely Complete - Basis of v2.0.0)
(Unchanged)

## Phase 2: Enhanced Agent Capabilities & User Experience (Current & Near-Term Focus - Targeting v2.0.0)

1.  Core Agent Execution Stability & Feature Verification (Improved)
    -   (Unchanged)
2.  Refine Chat UI/UX & Message Flow (Significant Progress - Critical Fixes Pending)
    -   **Visual Design Goal (Achieved & Enhanced).**
    -   **Persistence (Implemented & Refined):** All message types, including confirmed plans, saved/reloaded consistently.
    -   **Key Features & Bug Fixes (v2.5.3 Development Cycle):**
        -   **FIXED: Token Counter Per Agent & UI Enhanced.**
        -   **FIXED: File Upload.**
        -   **IMPLEMENTED & REFINED: Enhanced In-Chat Tool Feedback & Usability** (Collapsible tool outputs via label, `read_file` content display, copy buttons, etc.).
        -   **ADDRESSED: Major UI/UX Polish Items:**
            -   Chat Message Visuals & Density (Improved sub-step indentation, bubble widths, step title wrapping, collapsible major steps, agent avatar, font sizes, LLM selector styling).
            -   Blue line removed from RA final answers and Plan Proposal blocks.
        -   **FIXED: `read_file` Tool Output Visibility, Nesting, and Plan Persistence Visuals.**
        -   **FIXED: Chat Scroll Behavior on expand/collapse.**
        -   **NEW HIGH PRIORITY (v2.5.3 Target): Robust Agent Task Cancellation & STOP Button:**
            * Ensure agent tasks are reliably cancelled when intended (e.g., via STOP button, or current design of context switch).
            * Make STOP button fully functional.
        -   **BUG (Medium Priority - Post Cancellation Fix): Artifact Viewer Refresh:** Ensure reliable auto-update.
        -   **WARNING (Low Priority): Plan File Status Update.**
        -   **REVIEW (Low Priority): "Unknown" History Message Types.**
3.  DEBUG (Low Priority): Monitor Log Color-Coding. (Details as before)

## Phase 3: Advanced Interactivity & Tooling (Mid-Term - Incorporating New Goals)

-   **ENHANCEMENT: Asynchronous Background Task Processing (Post v2.0.0):**
    -   Allow agent plans to continue running if the user switches UI task context.
    -   Implement UI indicators for actively running tasks in the task list.
    -   Ensure correct rendering of non-active tasks and appropriate chat input locks.
    -   Requires backend changes for task state management and message routing.
-   Advanced User-in-the-Loop (UITL/HITL) Capabilities.
-   New Tools & Tool Enhancements.
-   Workspace RAG.
-   Improved Agent Memory & Context Management.
-   Further Chat Information Management.

## Phase 4: Advanced Agent Autonomy & Specialized Applications (Longer-Term)
(Unchanged)

This roadmap will guide our development efforts. Feedback and adjustments are welcome.
