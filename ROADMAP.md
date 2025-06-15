### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED: Phases 0-9

-   \[x\] **Result:** A stable application with a "Three-Track Brain" for efficient request handling, a robust self-correction loop, and an interactive GUI for approving and modifying complex plans.

### 🚀 UPCOMING PHASES 🚀

#### Phase 10: Foundational Memory & Context

_Goal: Give the agent a true understanding of conversational context, making it a genuine collaborative partner._

-   \[ \] **Full Conversational History:** Feed the complete chat history for the current task back into the core agent prompts. This is the top priority and a prerequisite for all subsequent features.

#### Phase 11: The Secure, Extensible Environment

_Goal: Create an isolated, user-extendable environment for each task, enabling custom tools and robust multi-user support._

-   \[ \] **Per-Task Virtual Environments:** Implement logic to create and use a dedicated Python `.venv` for each task.
-   \[ \] **Package Manager Tool:** Create a sandboxed tool to safely `pip install` user-requested libraries into the correct task's environment.

#### Phase 12: The Interactive Workbench

_Goal: Transform the workspace from a file list into an active workbench where outputs become the inputs for new actions._

-   \[ \] **Enhanced File Viewer:** Upgrade the file browser to render images (`.png`, `.jpg`), Markdown, and potentially PDFs directly in the UI.
-   \[ \] **Interactive Artifacts:** Add contextual "action" buttons next to files (e.g., "Analyze", "Run", "Visualize") that pre-populate the chat prompt with a relevant command, creating a seamless workflow.

#### Phase 13: The "Tool Forge" - A Pluggable Tool Architecture

_Goal: Allow users to create and add their own tools to the ResearchAgent without writing any backend code._

-   \[ \] **Tool Creator UI:** Build a "Tool Forge" section in the UI where users can define a tool's name, description, and input arguments via a simple form.
-   \[ \] **Dynamic Tool Generation:** The backend will take the user's definition and dynamically generate the corresponding Python tool file, making it instantly available to the agent.
-   \[ \] **Async Job Queue:** Implement a background task queue to handle tools marked as "long-running." The UI will poll for status updates, allowing users to track progress and get results without locking up the interface.

#### Phase 14: Advanced Tooling & Templates

_Goal: Equip the agent with a suite of powerful, pre-built tools for common high-value tasks._

-   \[ \] **Multi-Document Reporter Tool:** A tool that can synthesize information from multiple text files or PDFs.
-   \[ \] **Scientific Data Fetcher Tool:** A specialized tool to find and download datasets from sources like NCBI, PubMed, etc.
-   \[ \] **Website Report Generator:** A tool that can populate pre-defined website templates with data to create visual reports.

This roadmap is ambitious and exciting. It lays out a clear path from where we are now to the truly powerful platform you envision.

What do you think? Shall we proceed with **Phase 10: Full Conversational History** as our immediate next step?
