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
-   **True Concurrency & Control:** The backend server now correctly handles multiple, simultaneous agent runs without interruption. The architecture is fully decoupled, and users can stop any running task from the UI.
-   **Tool Forge v1 ("LLM as an Engine"):** Users can define custom tools with typed arguments through a UI. The backend dynamically generates functional Python tool files that use a powerful LLM to execute the described task. The system live-reloads these new tools without a server restart.
-   **The Active Toolbox:** A global UI panel allows users to enable or disable any available tool at any time. The agent's capabilities are instantly updated to reflect the user's selection.

## 🚀 NEXT FOCUS: Phase 14.2: The "Blueprint Canvas"

_**Vision:** Evolve the Tool Forge into a visual, node-based workflow editor. This will allow users to create, save, and reuse complex, multi-step plans as new, high-level tools, turning the agent into a true automation platform._

### The "Blueprint Tool" Concept

We are introducing a new type of tool called a **"Blueprint Tool"** or **"Plan Tool"**.

-   **Current Tools ("Engine Tools"):** Single-function tools where an LLM acts as the "engine."
-   **New "Blueprint Tools":** Reusable, multi-step workflows composed of existing tools. These are saved as structured JSON "blueprints," not Python files.

### The Creation Workflow

1.  **Conversational Scaffolding:** A user describes a multi-step goal in the Tool Forge (e.g., "I want to search for a topic, save the results, and then summarize them").
2.  **Architect's Draft:** The `Chief Architect` creates a draft plan using existing basic tools and identifies the required inputs for the new Blueprint (e.g., `topic`, `output_filename`).
3.  **The Visual Canvas:** This draft is rendered on a **visual, node-based canvas**. Users see nodes for each tool (`web_search`, `write_file`) connected by arrows that represent the data flow.
4.  **User-Driven Editing:** The user can fully edit this canvas:
    -   Drag and drop nodes to reorder them.
    -   Add new tools from a toolbox panel.
    -   Delete nodes to remove steps.
    -   Draw connections between tool outputs and inputs to explicitly define the data pipeline.
5.  **Saving the Blueprint:** Once finalized, the user gives the workflow a name (e.g., `research_and_summarize`), and the UI sends the complete JSON graph structure to the backend to be saved in a new `backend/tool_blueprints/` directory.

### The Execution Model: "Plan Substitution"

This is the key to elegant implementation, as suggested by the project lead. We will not build a separate execution engine for blueprints.

1.  **Discovery:** The tool loader will scan both the `tools/` and `tool_blueprints/` directories, making all tool types available to the agent.
2.  **Interception:** When the agent decides to use a Blueprint Tool, a new routing node (`Tool_Dispatcher`) intercepts the call.
3.  **State Management:** The execution follows a "function call" model:
    -   The main plan's state is pushed onto a "call stack" in the agent's `GraphState`.
    -   The sub-plan from the Blueprint's JSON file is loaded.
    -   Runtime arguments (e.g., `topic="Artificial Intelligence"`) are substituted into the sub-plan.
    -   This new sub-plan overwrites the main plan in the `GraphState`.
4.  **Seamless Execution:** The standard `Site Foreman` loop continues, executing the sub-plan's steps without knowing it's a "subroutine."
5.  **Return:** Once the sub-plan is complete, the original main plan is popped from the call stack, and execution resumes exactly where it left off.

This architecture enables **composable automation**, allowing the agent to use complex, user-defined workflows as simple, single-step tools.
