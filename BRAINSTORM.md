# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Company" Model

Our agent operates like a small, efficient company with specialized roles. This separation of concerns is the key to its complex behavior.

-   **The "Router" (Dispatcher):** Quickly classifies user requests into one of four tracks: Direct Q&A, Simple Tool Use, Complex Project, or **Board of Experts Review**.
-   **The "Memory Updater" (Librarian):** A critical pre-processing step that analyzes every user message to update the agent's structured JSON "Memory Vault," ensuring all new facts are stored before any action is taken.
-   **The "Board of Experts" (Advisory Committee):** A dynamically formed group of AI specialist personas (e.g., 'Data Scientist', 'Forensic Accountant') proposed by the agent based on the user's request. The user must approve the board before the project proceeds.
-   **The "Chair" (BoE Moderator):** The leader of the Board of Experts. Synthesizes expert critiques and creates the initial and final strategic plans for the project.
-   **The "Expert Critic" (BoE Member):** An individual AI persona on the board that reviews and provides structured feedback on the Chair's plan in a sequential, autonomous loop.
-   **The "Chief Architect" (Planner):** A strategic thinker that creates detailed, structured JSON "blueprints" for complex tasks (for the non-BoE track).
-   **The "Site Foreman" (Controller):** The project manager that executes the final, expanded blueprint step-by-step, managing data piping and correction sub-loops.
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
