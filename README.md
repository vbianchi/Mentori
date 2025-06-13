# ResearchAgent: An Advanced AI-Powered Research Assistant

## 1. Overview

ResearchAgent is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend and a modern JavaScript frontend (Vite + Preact), it leverages a unique **Plan-Controller-Executor-Evaluator (PCEE)** architecture to autonomously create, execute, and evaluate structured plans to fulfill high-level user requests.

The core philosophy is built on **transparency, adaptive execution, and security**. The agent first uses a `Router` to determine if a request requires a simple answer or a complex plan. For complex tasks, it generates a detailed blueprint and executes it step-by-step within a secure, sandboxed workspace for each persistent task. It is designed to understand the outcome of its actions and has a foundational architecture for future self-correction and human-in-the-loop collaboration.

## 2. Key Features

-   **Stateful, Multi-Turn Tasks:** The application is built around persistent tasks. Users can create, rename, delete, and switch between tasks, with each one maintaining its own independent chat history and sandboxed workspace.
-   **Advanced PCEE Architecture:** A robust, multi-node graph that separates routing, planning, control, execution, and evaluation for complex task management.
-   **Structured JSON Planning:** The agent's "Chief Architect" (Planner) generates detailed JSON-based plans, which are presented to the user for review before execution begins.
-   **Secure Sandboxed Workspaces:** Every task is assigned a unique, isolated directory, ensuring security and preventing state-collision between different tasks.
-   **Modular & Resilient Tools:** A flexible tool system allows for easy addition of new capabilities. Current tools include web search, a sandboxed file system (read, write, list), and a sandboxed shell.
-   **Interactive & Transparent Frontend:** A responsive user interface built with Preact and Vite, designed to provide clear, real-time visibility into the agent's complex operations.
    -   **Hierarchical Agent Trace:** See the agent's thought process as a clear, threaded conversation. The UI visualizes the handoff from the "Chief Architect's" plan, to the "Site Foreman's" execution log, to the "Editor's" final summary.
    -   **Live Step Execution:** Watch each step of the plan update in real-time from "pending" to "in-progress" to "completed" or "failed".
    -   **Task Management Panel:** A dedicated sidebar for managing the entire lifecycle of your research tasks.
    -   **Dynamic Model Selection:** Configure the LLM for each agent role (Router, Planner, etc.) directly from the UI.
    -   **Interactive Workspace & Artifact Viewer:** Browse, view, and upload files directly within the agent's sandboxed workspace for each task.

## 3. Project Structure

```

.

├── backend/

│ ├── tools/

│ │ ├── ... (Modular tool files)

│ ├── langgraph\_agent.py # Core PCEE agent logic

│ ├── prompts.py # Centralized prompts for all agent nodes

│ └── server.py # WebSocket server entry point

│

├── src/

│ ├── components/

│ │ ├── AgentCards.jsx # Components for each agent's response

│ │ ├── Common.jsx # Shared components like buttons

│ │ └── Icons.jsx # All SVG icon components

│ │

│ ├── App.jsx # Main UI component and state management

│ ├── index.css # Global CSS and Tailwind directives

│ └── main.jsx # Frontend application entry point

│

├── .env.example # Template for environment variables

├── .gitignore # Specifies files to ignore for version control

├── BRAINSTORM.md # Document for future ideas

├── docker-compose.yml # Orchestrates the Docker container

├── Dockerfile # Defines the application's Docker image

├── package.json # Frontend dependencies and scripts

├── PCEE\_ARCHITECTURE.md # Document detailing the agent's design

├── tailwind.config.js # Tailwind CSS configuration

└── ROADMAP.md # Project development plan

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

1.  **Install Dependencies:** In your second terminal, run `npm install`. This is crucial to install all dependencies, including the Tailwind CSS typography plugin.
2.  **Run the Frontend:** Run `npm run dev`.
3.  **Access the Application:** Open your browser and navigate to the local URL provided by Vite (usually `http://localhost:5173`).
