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
-   **The Active Toolbox:** A global UI panel allows users to enable/disable any available tool at any time. The agent's capabilities are instantly updated to reflect the user's selection.
-   **Blueprint Loading & Expansion:** The backend can now load multi-step JSON "Blueprint Tools", and the agent's planner can correctly expand them into an executable plan for the user to approve.
-   **Interactive Canvas v1:** The Tool Forge now features a visual canvas where users can reorder steps via drag-and-drop, add new tools to the plan, and delete steps from the plan.

## 🚀 NEXT FOCUS: Phase 14.2: Visual Data Piping

_**Vision:** Evolve the interactive canvas into a true visual programming environment by allowing users to define the flow of data between nodes._

### The "Data Piping" Concept

We need to enable users to graphically connect the output of one tool to the input of another. This is the key to creating truly useful and reusable automations.

**Example Use Case:**
A user wants to create a blueprint that takes a `topic` as input, researches it, and saves the result to a filename also provided by the user.

1.  The user adds a `web_search` node and a `write_file` node to the canvas.
2.  The user can then click and drag from an **output anchor** on the `web_search` node to an **input anchor** on the `write_file` node.
3.  This visual connection would modify the plan's JSON to specify that the output of the first step should be "piped" into the `content` argument of the second step.
4.  The user would also need a way to define which arguments of the overall blueprint (like `topic` and `filename`) are exposed to the end-user.

### The Data Model Evolution

To support this, our `plan` data structure needs to evolve from a simple array of steps into a more explicit graph structure, likely containing:
1.  A list of **`nodes`**, where each node is a tool call.
2.  A list of **`edges`**, where each edge defines a connection from an `output` of one node to an `input` of another.

This structure is much more flexible and will allow for more complex workflows, including the conditional loops (`GOTO`, `IF/ELSE`) that we have discussed.

**Visual Representation:**

+-----------+       +----------------+       +----------+

\[START\] o--->| web\_search|--o-o-->| write\_file |--o-o-->| END |

+-----------+ +----------------+ +----------+

| ^

| |

+------------------+ (Data Pipe)


This is a significant architectural step that will unlock the full potential of the ResearchAgent as an automation platform.
