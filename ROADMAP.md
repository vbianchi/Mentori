### Project Vision:

To build a transformative, AI-powered workbench. The platform will be powerful enough for scientific research and general enough for power users, with a core architecture that allows users to easily add their own tools and capabilities. The system is designed for privacy and efficiency, with a clear path to running on local LLMs.

### ✅ COMPLETED: Phase 12: The Interactive Workbench

-   \[x\] **Result:** Evolved the workspace from a simple file list into a full-featured, interactive file explorer with a smart backend API, folder navigation, breadcrumbs, core interactivity (create, rename, delete), drag-and-drop uploads, and a smart previewer for images, Markdown, and CSVs.

### 🚀 UPCOMING PHASES 🚀

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

#### Phase 15: UI/UX Polish & Advanced Previews (NEW)

_Goal: Refine the user experience with modern, fluid interactions and expand file preview capabilities._

-   \[ \] **Advanced Document Previews:** Implement client-side rendering for PDFs (using `PDF.js`) and server-side conversion for Word documents (`.docx`) to enable in-app viewing.
-   \[ \] **Inline File/Folder Creation:** Refactor the creation process to instantly add a new item to the UI in an "editing" state, only calling the backend API after the user confirms the name.
-   \[ \] **Drag-and-Drop File Moving:** Add support for dragging files and dropping them onto folders to trigger a move/rename operation.
-   \[ \] **Inline Renaming:** Unify the renaming experience by refactoring the file explorer to support in-place renaming, consistent with the task list.
