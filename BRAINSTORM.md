# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles. This separation of concerns is the key to its complex behavior.

-   **The "Router" (Dispatcher):** Quickly classifies user requests into one of four tracks: Direct Q&A, Simple Tool Use, Complex Project, or **Board of Experts Review**.
-   **The "Memory Updater" (Librarian):** A critical pre-processing step that analyzes every user message to update the agent's structured JSON "Memory Vault," ensuring all new facts are stored before any action is taken.
-   **The "Board of Experts" (Advisory Committee):** A dynamically formed group of AI specialist personas (e.g., 'Data Scientist', 'Forensic Accountant') proposed by the agent based on the user's request. The user must approve the board before the project proceeds.
-   **The "Chair" (BoE Moderator):** The leader of the Board of Experts. Synthesizes expert critiques and creates the initial and final strategic plans for the project. It is also responsible for optimizing the final plan by consolidating redundant steps.
-   **The "Expert Critic" (BoE Member):** An individual AI persona on the board that reviews and provides structured feedback on the Chair's plan in a sequential, autonomous loop.
-   **The "Chief Architect" (Planner):** A strategic thinker that takes a single high-level goal from the Chair's plan and expands it into a detailed, multi-step "tactical plan" of specific tool calls.
-   **The "Site Foreman" (Controller):** The project manager that executes the tactical plan step-by-step, managing data piping and correction sub-loops.
-   **The "Worker" (Executor):** The specialist that takes precise instructions and runs the tools.
-   **The "Project Supervisor" (Evaluator):** The quality assurance inspector that validates the outcome of each step in a complex plan.
-   **The "Editor" (Reporter):** The unified voice of the agent, capable of acting as a conversational assistant or a project manager to deliver context-aware final responses, checkpoint summaries, and final reports.

### 🚀 Future Architectural Evolution: Production-Grade Infrastructure 🚀

_Inspired by our analysis of the Suna project, this outlines the path to evolving ResearchAgent from a powerful prototype into a robust, scalable, and multi-user-ready platform._

#### 1\. Asynchronous Task Queuing

-   **Problem:** Currently, agent tasks run as `asyncio` tasks within the main server process. If the server restarts, all running tasks are lost.
-   **Solution:** Replace the in-process execution with a dedicated task queue system (e.g., **Dramatiq with Redis**).
-   **Benefit:** Decouples the API from agent execution, allowing for resilient, long-running background jobs and better scalability.

#### 2\. Database & Persistence Layer

-   **Problem:** All agent memory and history are currently transient.
-   **Solution:** Integrate a portable, file-based database.
-   **Proposed Tech:** Use **SQLite** for maximum portability, with **SQLAlchemy** as an ORM. This allows us to start simple and provides a clear path to migrating to a larger database like Postgres if future needs require it.

#### 3\. Advanced Per-Task Sandboxing

-   **Problem:** All tasks currently share a single Docker workspace.
-   **Solution:** Evolve to a "per-task" sandboxing model.
-   **Implementation Idea:** Use the **Docker SDK for Python** within our task queue worker to programmatically start and stop isolated Docker containers for each agent run.

### 💡 Future Platform Features & User Experience 💡

_A collection of features required to move from a single-user tool to a complete, user-friendly platform._

#### 1\. User Management & Onboarding

-   **Onboarding Flow:** A guided, multi-step process for new users to set up their account and connect their first tools.
-   **Multi-Provider Authentication:** Instead of handling passwords directly, we will use an authentication service (e.g., Supabase Auth, Auth0) to enable Single Sign-On (SSO).
    -   **Target Providers:** Microsoft (for WUR accounts via Entra ID), Google, GitHub.
-   **Secure API Key Management:** A dedicated UI section where users can securely add, view, and manage their own API keys for the tools they want to use. Keys should be encrypted at rest in the database.

#### 2\. Collaboration & Multi-Tenancy

-   **The "Organization" Concept:** Introduce a new top-level entity, the "Organization." Users can create or be invited to organizations.
-   **Shared Resources:** Tasks, workspaces, and blueprints will belong to an organization, allowing team members to view, run, and collaborate on the same projects.
-   **Roles & Permissions:** Implement a simple role-based access control system (e.g., Owner, Member) to manage what users can do within an organization.

#### 3\. A Hybrid Tool Ecosystem

-   **Strategy:** Augment our powerful, custom-built tools with a standardized library of generic "connector" tools.
-   **Our Custom "Reasoning" Tools:** Continue to build and refine specialized tools like `query_files` and `critique_document`. These are our core competency.
-   **MCP for Connectors:** Develop a wrapper to connect to the **Model Context Protocol (MCP)** tool ecosystem. This will instantly give the agent access to hundreds of pre-built tools for third-party APIs (GitHub, Google Calendar, Slack, etc.) without us needing to maintain them.

## Hierarchical Execution Loop: Node-by-Node Breakdown

This section details the precise flow and responsibility of each node in the execution engine, which begins after the user approves the final strategic plan.

### 1\. `master_router` (Conditional Edge)

-   **Purpose:** To act as the main traffic controller for the strategic plan.
-   **Inputs:** `strategic_plan`, `strategic_step_index`.
-   **Processing:**
    1.  Checks if `strategic_step_index` is less than the total number of steps in `strategic_plan`.
    2.  If yes, it checks if the current step is a `checkpoint`.
-   **Outputs:** A routing decision string.
-   **Connections:**
    -   Receives from: `human_in_the_loop_final_plan_approval` (initial entry) and `increment_strategic_step_node` (loops).
    -   Routes to:
        -   `chief_architect_node` (if more non-checkpoint steps exist).
        -   `editor_checkpoint_report_node` (if the step is a checkpoint).
        -   `Editor` (if all steps are complete).

### 2\. `chief_architect_node`

-   **Purpose:** To expand a single high-level strategic goal into a detailed, low-level tactical plan of tool calls.
-   **Inputs:** `strategic_plan`, `strategic_step_index`, `user_request`, list of available `tools`.
-   **Processing:** Makes an LLM call with a specialized prompt, asking it to create a multi-step "tactical plan" (a list of tool calls) that will accomplish the current strategic goal.
-   **Outputs:** `tactical_plan` (a list of dictionaries, where each is a tool call).
-   **Connections:**
    -   Receives from: `master_router`.
    -   Routes to: `site_foreman_node`.

### 3\. `site_foreman_node`

-   **Purpose:** To prepare a single tool call from the tactical plan for execution.
-   **Inputs:** `tactical_plan`, `tactical_step_index`, `step_outputs` (from previous steps).
-   **Processing:**
    1.  Reads the current tactical step (e.g., `tactical_plan[tactical_step_index]`).
    2.  Performs "data piping": checks the `tool_input` for any `{step_N_output}` placeholders and replaces them with the actual output from the `step_outputs` dictionary.
-   **Outputs:** `current_tool_call` (a dictionary with the final `tool_name` and hydrated `tool_input`).
-   **Connections:**
    -   Receives from: `tactical_step_router` (loops) and `chief_architect_node` (initial entry).
    -   Routes to: `worker_node`.

### 4\. `worker_node`

-   **Purpose:** To execute a single tool call, and nothing more.
-   **Inputs:** `current_tool_call`, `workspace_path`, `enabled_tools`.
-   **Processing:**
    1.  Initializes the `ToolExecutor` with the currently enabled tools.
    2.  Invokes the executor with the `current_tool_call`.
-   **Outputs:** `tool_output` (the raw string/data returned by the tool).
-   **Connections:**
    -   Receives from: `site_foreman_node`.
    -   Routes to: `project_supervisor_node`.

### 5\. `project_supervisor_node`

-   **Purpose:** To evaluate whether the tool execution successfully accomplished the step's goal.
-   **Inputs:** The original `instruction` for the tactical step, `current_tool_call`, and `tool_output`.
-   **Processing:** Makes an LLM call with a specialized prompt, asking it to assess if the `tool_output` satisfies the original `instruction`.
-   **Outputs:** `step_evaluation` (a dictionary with `status: "success" | "failure"` and `reasoning`).
-   **Connections:**
    -   Receives from: `worker_node`.
    -   Routes to: `increment_tactical_step_node`.

### 6\. `tactical_step_router` (Conditional Edge)

-   **Purpose:** To control the flow of the inner tactical loop.
-   **Inputs:** `tactical_plan`, `tactical_step_index`.
-   **Processing:** Checks if `tactical_step_index` is less than the total number of steps in `tactical_plan`.
-   **Outputs:** A routing decision string.
-   **Connections:**
    -   Receives from: `increment_tactical_step_node`.
    -   Routes to:
        -   `site_foreman_node` (to continue the loop).
        -   `increment_strategic_step_node` (when the tactical plan is complete).
