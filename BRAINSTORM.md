# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles. This separation of concerns is the key to its complex behavior.

-   **The "Router" (Dispatcher):** Quickly classifies user requests into one of three tracks: Direct Q&A, Simple Tool Use, or Complex Project.
-   **The "Memory Updater" (Librarian):** A critical pre-processing step that analyzes every user message to update the agent's structured JSON "Memory Vault," ensuring all new facts are stored before any action is taken.
-   **The "Handyman" (Simple Executor):** A fast-lane agent that handles simple, single-step tool commands.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for complex tasks.
-   **The "Site Foreman" (Controller):** The project manager that executes the blueprint step-by-step, managing data piping and correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector that validates the outcome of each step in a complex plan.
-   **The "Editor" (Reporter):** The unified voice of the agent, capable of acting as a conversational assistant or a project manager to deliver context-aware final responses.

## ✅ COMPLETED FEATURES

-   **Stateful Task Management:** The application is centered around persistent "Tasks", each with a unique workspace and a complete chat history.
-   **Advanced UI Rendering & Control:** A sophisticated UI visualizes the agent's operations in real-time.
-   **Multi-Level Self-Correction:** The agent can robustly handle errors by retrying steps or creating entirely new plans.
-   **Three-Track Brain & Interactive HITL:** The agent efficiently routes requests and allows users to review and modify complex plans before execution.
-   **Robust Memory & Environments:** The agent uses a "Memory Vault" for persistent knowledge and automatically creates isolated Python virtual environments for each task.
-   **Interactive Workbench v1:** A functional file explorer with structured listing, navigation, create/rename/delete actions, drag-and-drop upload, and a smart previewer for text, images, Markdown, and CSVs.

## 🚀 FUTURE FOCUS: UI/UX Polish & Advanced Capabilities

_**Vision:** Elevate the user experience to match professional IDEs with more fluid interactions and broader file support._

### Inline & "Create-then-Commit" Interactions

-   **Goal:** Move away from `prompt()` and `confirm()` dialogs for a smoother, more integrated experience.
-   **Inline Renaming:** Refactor the `WorkspaceItem` into its own component with an `isEditing` state, similar to `TaskItem`. Clicking "Rename" would transform the item's text label into an input field. A "blur" or "Enter" keypress would commit the change by calling the `PUT /api/workspace/items` endpoint.
-   **Inline Creation:**
    1.  **UI First:** When a user clicks "New Folder" or "New File", immediately add a temporary item to the `workspaceItems` state with a default name (e.g., `untitled_folder`) and in an `isEditing` state.
    2.  **User Input:** The user types the desired name directly in the file list.
    3.  **API Commit:** On "Enter" or "blur", the frontend makes the appropriate API call (`POST` for folders, or a `PUT` to create a new file with content).
    4.  **Refresh:** The list refreshes with the permanent item from the server.

### Advanced File Previews & Handling

-   **Goal:** Expand the Smart Previewer to handle common document formats.
-   **PDF Rendering:**
    -   **Library:** Use Mozilla's `PDF.js`.
    -   **Implementation:** When a user clicks a `.pdf` file, the `FilePreviewer` component will not fetch text content. Instead, it will initialize the `PDF.js` viewer, passing it the URL to our existing `/api/workspace/raw?path=...` endpoint. The library will handle fetching and rendering the document page by page.
-   **Word Document (`.docx`) Rendering:**
    -   **Backend Tool:** This requires a new backend tool, as browsers cannot render `.docx` files natively.
    -   **Python Library:** Use `python-docx` to read the `.docx` file's content.
    -   **Conversion:** The tool would convert the document's paragraphs and headings into a basic HTML string.
    -   **Frontend:** The frontend would call an endpoint that uses this tool and then render the resulting HTML in the preview panel.

### Drag-and-Drop File Moving

-   **Goal:** Allow users to organize files by dragging them into folders.
-   **Implementation:**
    1.  **Draggable Items:** Make file items in the explorer draggable by setting the `draggable="true"` attribute.
    2.  **Drop Zones:** Make folder items valid drop zones by adding `onDragOver` and `onDrop` event handlers.
    3.  **API Call:** When a file is dropped on a folder, the `onDrop` handler will trigger our existing `PUT /api/workspace/items` (rename) endpoint. The `old_path` would be `current_path/file.txt` and the `new_path` would be `current_path/folder_name/file.txt`.
    4.  **Refresh:** After a successful API call, refresh the current view to show the file has been moved.
