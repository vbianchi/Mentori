# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project.

### ✔️ Phase 0-8: Core Engine, Stateful UI & Self-Correction

-   \[x\] **Core Backend Engine:** The foundational PCEE architecture with self-correction and escalation logic is stable.
-   \[x\] **Stateful Task Management & UI:** The UI is fully functional, centered on persistent tasks with independent workspaces and a sophisticated, component-based rendering of the agent's activity.

### ✔️ Phase 9: The "Three-Track Brain" & Interactive HITL

-   \[x\] **Three-Track Router:** Implemented an intelligent router to classify requests as `DIRECT_QA`, `SIMPLE_TOOL_USE`, or `COMPLEX_PROJECT`.
-   \[x\] **Handyman Path:** Built the new `Handyman` path for efficient single-step tool commands.
-   \[x\] **Unified Editor:** The `Editor` node now serves as the single, consistent voice of the agent for all three tracks.
-   \[x\] **Interactive GUI Plan Editor:** Replaced the raw JSON editing with a user-friendly, per-step GUI editor, allowing users to intuitively modify plans before approval.
-   \[x\] **UI Polish:** Addressed several UI/UX refinements, including cleaning up the settings panel and improving layout consistency.

### 🚀 UP NEXT: Phase 10: Advanced Context & Environment

-   \[ \] **Full Conversational History:** The complete chat history for a given task will be fed back into the agent's prompts. This is the top priority to give the agent true contextual memory, allowing for iterative work and follow-up commands (e.g., "now refactor the script you just wrote").
-   \[ \] **Smarter Tool Usage:** The agent will learn to use the output of previous steps as input for subsequent steps without explicit user instruction.
-   \[ \] **Python Virtual Environments:** Implement full dependency sandboxing with per-task `.venv` directories to isolate Python tool executions.

### Future Phases

-   \[ \] **Enhanced File Viewer:** Upgrade the workspace file viewer to intelligently render different file types, including images (`.png`, `.jpg`) and potentially PDFs.
-   \[ \] **Real-time Stop/Pause Button:** Implement UI controls to safely interrupt and resume the agent's execution loop.
-   \[ \] **Full Database Integration:** Replace browser `localStorage` with a robust database backend (e.g., SQLite) for persistent tasks and history.
