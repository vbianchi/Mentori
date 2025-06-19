### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED PHASES

-   \[x\] **Phase 12: The Interactive Workbench:** Evolved the workspace from a simple file list into a full-featured, interactive file explorer with a smart backend API, folder navigation, breadcrumbs, core interactivity (create, rename, delete), drag-and-drop uploads, and a smart previewer for images, Markdown, and CSVs.
-   \[x\] **Phase 12.5: Concurrent Agent Execution & Control:** Refactored the backend server to handle multiple, simultaneous agent runs and provided users with the ability to stop a running task. The architecture now correctly decouples agent execution from the client connection.
-   \[x\] **Phase 13: The "Tool Forge" (v1):** Implemented the foundational "LLM as an Engine" Tool Forge. Users can now define custom tools with typed arguments through a UI, which generates functional Python tool files on the backend that are immediately available to the agent without a server restart.
-   \[x\] **Phase 14.1: The Active Toolbox:** Implemented a global UI panel to enable/disable any available tool. The agent's capabilities are now filtered in real-time based on the user's selection for all subsequent operations.

### 🚀 UPCOMING PHASES 🚀

#### Phase 14.2: The "Blueprint Canvas" - Visual Workflow Editor

_Goal: Evolve the Tool Forge into a visual, node-based editor where users can create, save, and reuse complex, multi-step plans as new, high-level tools._

-   \[x\] **Task 1: Foundational UI:** Re-architected the Tool Forge UI into a two-panel layout, with a list of available tools on the left and a main editor/viewer panel on the right.
-   \[x\] **Task 2: Read-Only Plan Visualizer:** Upgraded the UI to render an agent's multi-step plan as a static, read-only graph of nodes. The backend now correctly loads and expands blueprint tools to be displayed.
-   \[x\] **Task 3: The Interactive Canvas:** Transformed the visualizer into a full-featured editor, allowing users to reorder steps with drag-and-drop, add new tools from the panel, and remove steps from the canvas.
-   \[ \] **Task 4: Visual Data Piping:** Introduce input/output anchors on each node. Implement the UI and backend logic to allow users to visually draw connections between nodes to define the data flow (e.g., piping the output of a `web_search` into the input of a `summarize` tool).
-   \[ \] **Task 5: Blueprint Execution Engine:** Implement the "Plan Substitution" logic on the backend. This will enable the agent to execute a saved JSON blueprint by pausing the main plan, running the blueprint's sub-plan, and then seamlessly resuming the main plan.

#### Phase 15: Advanced Tooling & Templates

_Goal: Equip the agent with a suite of powerful, pre-built tools for common high-value tasks._

-   \[ \] **Multi-Document Reporter Tool:** A tool that can synthesize information from multiple text files or PDFs.
-   \[ \] **Scientific Data Fetcher Tool:** A specialized tool to find and download datasets from sources like NCBI, PubMed, etc.
-   \[ \] **Website Report Generator:** A tool that can populate pre-defined website templates with data to create visual reports.

#### Phase 16: UI/UX Polish & Advanced Previews

_Goal: Refine the user experience with modern, fluid interactions and expand file preview capabilities._

-   \[ \] **Advanced Document Previews:** Implement client-side rendering for PDFs (using `PDF.js`) and server-side conversion for Word documents (`.docx`) to enable in-app viewing.
-   \[ \] **Inline File/Folder Creation:** Refactor the creation process to instantly add a new item to the UI in an "editing" state, only calling the backend API after the user confirms the name.
-   \[ \] **Drag-and-Drop File Moving:** Add support for dragging files and dropping them onto folders to trigger a move/rename operation.
-   \[ \] **Inline Renaming:** Unify the renaming experience by refactoring the file explorer to support in-place renaming, consistent with the task list.
-   \[ \] **Running Task Indicator:** Add a visual indicator (e.g., a spinning loader icon) next to the name of any non-active task in the sidebar that currently has a running agent process.
