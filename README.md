# ResearchAgent: An Advanced AI-Powered Research Assistant

## 1. Overview

ResearchAgent is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend and a modern JavaScript frontend (Vite + Preact), it leverages a unique **"Four-Track Brain"** architecture and a persistent **"Memory Vault"** to autonomously classify, plan, and execute high-level user requests with full conversational context.

The core philosophy is built on **transparency, adaptive execution, and security**. The agent first uses a `Router` to determine the complexity of a request. For the most complex tasks, it can invoke a **Board of Experts**—a team of dynamically generated AI personas—to collaboratively create, critique, and refine a plan before execution begins within a secure, sandboxed workspace.

## 2. Key Features

-   **Stateful, Multi-Turn Tasks:** The application is built around persistent tasks. Users can create, rename, delete, and switch between tasks, with each one maintaining its own independent chat history and sandboxed workspace.
-   **Structured Agent Memory:** Each task features a "Memory Vault," a structured JSON knowledge base that the agent updates in real-time. This allows for robust, multi-turn conversational context and recall of specific facts.
-   **"Four-Track Brain" Architecture:** For maximum efficiency and analytical depth, an intelligent router classifies requests:
    -   **Track 1: Direct Q&A:** Simple questions are answered directly by the `Editor`.
    -   **Track 2: Simple Tool Use:** Single commands are executed by a lightweight `Handyman` agent.
    -   **Track 3: Complex Projects:** Multi-step tasks engage a `Chief Architect` for robust planning and execution.
    -   **Track 4: Board of Experts Review:** For requests requiring deep analysis, the user can invoke `@experts`. The agent proposes a board of AI specialists for user approval. This board then autonomously collaborates to create, critique, and refine a strategic plan, ensuring a higher level of analytical rigor before execution.
-   **Interactive Authorization Gates:** The Board of Experts track includes user-in-the-loop checkpoints, requiring explicit user approval for the proposed expert personas and the final strategic plan before any work is done.
-   **Secure, Per-Task Virtual Environments:** Every task is automatically provisioned with its own isolated Python virtual environment (`.venv`), ensuring that software dependencies for one project cannot conflict with another.
-   **Extensible Tool System:** The agent is equipped with a suite of robust tools, including web search, a sandboxed file system, a secure package manager (`pip_install`), and advanced document analysis capabilities.
-   **Interactive & Transparent Frontend:** A responsive user interface designed to provide clear, real-time visibility into the agent's complex operations, including a hierarchical agent trace, live step execution monitoring, and a full-featured file explorer.

## 3. Project Structure

```

.

├── backend/
│ ├── tools/
│ │ ├── ... (Modular tool files)
│ ├── langgraph_agent.py # Core agent logic & all graph nodes
│ ├── prompts.py # Centralized prompts for all agent nodes
│ └── server.py # WebSocket server entry point
│
├── src/
│ ├── components/
│ │ ├── AgentCards.jsx # Components for each agent's response
│ │ ├── Common.jsx # Shared components like buttons
│ │ └── Icons.jsx # All SVG icon components
│ │
│ ├── hooks/
│ │ ├── useAgent.js # WebSocket & agent communication
│ │ ├── useSettings.js # Global settings management
│ │ ├── useTasks.js # Task state management
│ │ └── useWorkspace.js # Filesystem interaction
│ │
│ ├── App.jsx # Main UI component and state management
│ ├── index.css # Global CSS and Tailwind directives
│ └── main.jsx # Frontend application entry point
│
├── .env.example # Template for environment variables
├── .gitignore # Specifies files to ignore for version control
├── docker-compose.yml # Orchestrates the Docker container
├── Dockerfile # Defines the application's Docker image
├── package.json # Frontend dependencies and scripts
└── tailwind.config.js # Tailwind CSS configuration

```

## 4. Installation & Setup

You will need two separate terminals to run the backend and frontend servers.

### Prerequisites

-   **Docker:** Ensure Docker and Docker Compose are installed.
-   **Node.js & npm:** Ensure Node.js (which includes npm) is installed.

### Step 1: Backend Server

1.  **Configure Environment Variables:** Create a `.env` file from the `.env.example` template and add your API keys (`GOOGLE_API_KEY`, `TAVILY_API_KEY`). You can also specify which models to use for each agent role here.
2.  **Run the Backend:** In your first terminal, run `docker compose up --build`.

### Step 2: Frontend Server

1.  **Install Dependencies:** In your second terminal, run `npm install`.
2.  **Run the Frontend:** Run `npm run dev`.
3.  **Access the Application:** Open your browser and navigate to the local URL provided by Vite (usually `http://localhost:5173`).

