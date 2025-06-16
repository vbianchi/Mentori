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

---

## 🚀 NEXT FOCUS: Phase 12: The Interactive Workbench

_**Vision:** Evolve the simple "Workspace" panel into a full-featured, interactive file explorer that feels like a mini-IDE, enabling complex project management and a seamless user experience._

### Sub-Phase A: The Smart Backend API

This phase focuses on refactoring the backend API in `server.py` to provide the structured data needed by a modern frontend file explorer.

1.  **Enhance the Items API:**
    * **Endpoint:** `GET /api/workspace/items`
    * **Request Query:** `?path=task_123/subfolder/` (The path is relative to the `/app/workspace` root).
    * **Success Response (200 OK):** Return a JSON object containing a list of structured items. Each item will have a `name`, `type` (`file` or `directory`), and `size` in bytes.
        ```json
        {
          "items": [
            { "name": ".venv", "type": "directory", "size": 0 },
            { "name": "results.csv", "type": "file", "size": 10240 },
            { "name": "plot.png", "type": "file", "size": 51200 }
          ]
        }
        ```
    * **Error Response (404 Not Found):** If the path does not exist.

2.  **Create Folder API:**
    * **Endpoint:** `POST /api/workspace/folders`
    * **Request Body:** A JSON object specifying the full path for the new folder.
        ```json
        { "path": "task_123/new_output_folder" }
        ```
    * **Success Response (201 Created):** `{"message": "Folder created successfully."}`
    * **Error Response (409 Conflict):** If a folder or file with that name already exists.

3.  **Create "Delete Item" API:**
    * **Endpoint:** `DELETE /api/workspace/items`
    * **Request Query:** `?path=task_123/file_to_delete.txt`
    * **Success Response (200 OK):** `{"message": "Item deleted successfully."}`

4.  **Create "Rename Item" API:**
    * **Endpoint:** `PUT /api/workspace/items`
    * **Request Body:** A JSON object with the old and new paths.
        ```json
        {
          "old_path": "task_123/old_name.txt",
          "new_path": "task_123/new_name.txt"
        }
        ```
    * **Success Response (200 OK):** `{"message": "Item renamed successfully."}`

### Sub-Phase B: The Navigable UI

This phase focuses on refactoring the "Agent Workspace" panel in `src/App.jsx` to consume the new smart API.

1.  **State Management:**
    * `currentPath`: A new state string, e.g., `task_123/subfolder`. Defaults to the active task's root.
    * `items`: A new state array to hold the list of file/folder objects from the API.
    * `isLoading`: Existing state to show a loading spinner during API calls.
2.  **Component Structure:**
    * Create a `FileExplorer` main component.
    * Create distinct `FileItem` and `FolderItem` sub-components. Each will have a unique SVG icon.
3.  **Navigation Logic:**
    * The main component will fetch items from the API whenever `activeTaskId` or `currentPath` changes.
    * Clicking a `FolderItem` will update the `currentPath` state, triggering a re-render and a new API call.
    * Implement a "Breadcrumbs" component that displays the current path (e.g., `Workspace > folder > subfolder`) and allows one-click navigation to any parent directory.

### Sub-Phase C: Core Interactivity

Add essential file management features to the UI.

1.  **Create Folder UI:**
    * Add a "New Folder" icon button to the explorer's header.
    * On click, show a modal or an inline text input field to enter the new folder's name.
    * On submit, call the `POST /api/workspace/folders` API and refresh the current view.
2.  **Context Menu (Right-Click):**
    * Implement a custom right-click context menu for both `FileItem` and `FolderItem`.
    * The menu will contain "Rename" and "Delete" options.
    * Selecting an option will trigger the appropriate API call (`PUT` or `DELETE`) and refresh the view.

### Sub-Phase D: Advanced Features & Smart Previews

Enhance the user experience with modern features.

1.  **Drag-and-Drop Uploads:**
    * Make the `FileExplorer` component a drop zone for files.
    * Use state to show a visual overlay when a file is being dragged over the component.
    * On drop, handle the file upload logic using the existing `/upload` endpoint, but now passing the `currentPath` so files land in the correct folder.
2.  **Smart File Previewer:**
    * Refactor the existing file viewer. When a file is clicked, check its extension.
    * **Markdown (`.md`):** Render using the `marked.js` library.
    * **Images (`.png`, `.jpg`, `.gif`):** Render inside an `<img>` tag.
    * **CSV/TSV (`.csv`, `.tsv`):** Parse the text and render it as an HTML `<table>`.
    * **Source Code (`.py`, `.js`, etc.):** Render inside `<pre><code>` tags, potentially with a lightweight syntax highlighting library.
