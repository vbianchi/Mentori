# ResearchAgent - Brainstorming & Ideas

This document is a living collection of ideas, architectural concepts, and potential future features for the ResearchAgent project.

## Core Agent Architecture: The "Four-Track Brain"

Our agent operates on a sophisticated four-track cognitive architecture. This separation of concerns allows for a dynamic response tailored to the complexity of the user's request.

-   **The "Router" (Dispatcher):** The central decision-maker. It analyzes every user request and directs it down one of four distinct tracks.
-   **Track 1: Direct Q&A:** For simple questions and conversational interactions. This track routes directly to the `Editor` node for a standard LLM response.
-   **Track 2: Simple Tool Use:** For single-step commands that can be fulfilled by one tool call. This track uses a `std_handyman_node` to format the tool call, which is then executed by the `std_worker_node`.
-   **Track 3: Standard Complex Project:** For multi-step tasks that require a clear plan but not deep scientific critique. This track uses a dedicated `std_chief_architect_node` to create a plan, which is then executed by the `std_site_foreman_node`, `std_worker_node`, and `std_project_supervisor_node` in a self-correcting loop.
-   **Track 4: Peer Review Session:** An advanced, user-invoked mode (`@experts`) for complex research questions. This track engages a `Board of Experts` to collaboratively debate and create a `StrategicMemo`. The memo is then executed by a dedicated set of "Company Model" nodes (`boe_chief_architect_node`, `boe_site_foreman_node`, etc.) that includes autonomous checkpoint reviews and user escalation paths.

### 🚀 Future Architectural Evolution: Production-Grade Infrastructure 🚀

_Inspired by our analysis of the Suna project, this outlines the path to evolving ResearchAgent from a powerful prototype into a robust, scalable, and multi-user-ready platform._

#### 1\. Asynchronous Task Queuing

-   **Problem:** Currently, agent tasks run as `asyncio` tasks within the main server process. If the server restarts, all running tasks are lost.
-   **Solution:** Replace the in-process execution with a dedicated task queue system (e.g., **Dramatiq with Redis**).
-   **Benefit:** Decouples the API from agent execution, allowing for resilient, long-running background jobs and better scalability.

#### 2\. Database & Persistence Layer

-   **Problem:** All agent memory and history are currently transient.
-   **Solution:** Integrate a portable, file-based database.
-   **Proposed Tech:** Use **SQLite** for maximum portability, with **SQLAlchemy** as an ORM. This allows us to start simple and provides a clear path to migrating to a larger system like Postgres if future needs require it.

### 💡 Future Platform Features & User Experience 💡

_A collection of features required to move from a single-user tool to a complete, user-friendly platform._

#### 1\. User Management & Onboarding

-   **Onboarding Flow:** A guided, multi-step process for new users to set up their account and connect their first tools.
-   **Multi-Provider Authentication:** Instead of handling passwords directly, we will use an authentication service (e.g., Supabase Auth, Auth0) to enable Single Sign-On (SSO).
-   **Secure API Key Management:** A dedicated UI section where users can securely add, view, and manage their own API keys for the tools they want to use. Keys should be encrypted at rest in the database.

#### 2\. "Committee of Critics" Tool Evolution

-   **Vision:** Evolve the `critique_document` tool into a collaborative review by a panel of AI experts.
-   **Workflow:**
    1.  **Persona Scoping:** The tool first analyzes the document to determine its field (e.g., genetics, finance). It then defines a committee of 3 relevant expert personas (e.g., "Expert Geneticist," "Scientific Writer," "Statistician"). The user can also specify these personas in the prompt.
    2.  **Parallel Criticism:** The tool runs three parallel LLM calls, providing each with the document but a different "expert" system prompt.
    3.  **Synthesized Report:** A final LLM call acts as the "chairperson," taking the three independent critiques and synthesizing them into a single, structured report for the user.
