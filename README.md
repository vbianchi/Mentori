# Mentor::i: An Advanced AI-Powered Research Assistant

## 1. Overview

Mentor::i is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend and a modern JavaScript frontend (Vite + Preact), it leverages a unique **"Three-Track Brain"** architecture and a persistent **"Memory Vault"** to autonomously classify, plan, and execute high-level user requests with full conversational context.

The core philosophy is built on **transparency, adaptive execution, and security**. The agent first uses a `Router` to determine if a request is a simple question, a single tool command, or a complex project. For complex tasks, it generates a detailed blueprint which the user can interactively edit and approve before execution begins within a secure, sandboxed workspace.

## 2. Key Features

-   **Stateful, Multi-Turn Tasks:** The application is built around persistent tasks. Users can create, rename, delete, and switch between tasks, with each one maintaining its own independent chat history and sandboxed workspace.
-   **Structured Agent Memory:** Each task features a "Memory Vault," a structured JSON knowledge base that the agent updates in real-time. This allows for robust, multi-turn conversational context and recall of specific facts, preferences, and relationships between concepts.
-   **"Three-Track Brain" Architecture:** For maximum efficiency, an intelligent router classifies requests:
    -   **Direct Q&A:** Simple questions are answered directly by the `Editor` using its memory and reasoning abilities.
    -   **Simple Tool Use:** Single commands are executed by a lightweight `Handyman` agent.
    -   **Complex Projects:** Multi-step tasks engage the full "Company Model" for robust planning and execution.
-   **Secure, Per-Task Virtual Environments:** Every task is automatically provisioned with its own isolated Python virtual environment (`.venv`), ensuring that software dependencies for one project cannot conflict with another.
-   **Extensible Tool System:** The agent is equipped with a suite of robust tools, including web search, a sandboxed file system, and a secure package manager (`pip_install`). The system is designed to be easily extensible with new capabilities.
-   **Interactive GUI Plan Editor:** For complex projects, the agent presents its plan in a user-friendly GUI. Users can edit instructions, change tools for each step, add or remove steps, and then approve the final plan before execution.
-   **Interactive & Transparent Frontend:** A responsive user interface built with Preact and Vite, designed to provide clear, real-time visibility into the agent's complex operations.
    -   **Hierarchical Agent Trace:** See the agent's thought process as a clear, threaded conversation.
    -   **Live Step Execution:** Watch each step of a plan update in real-time from "pending" to "in-progress" to "completed" or "failed".
    -   **Task Management Panel:** A dedicated sidebar for managing the entire lifecycle of your research tasks.
    -   **Dynamic Model Selection:** Configure the LLM for each agent role directly from the UI.
    -   **Full-Featured File Explorer:** Browse, view, and manage files within the agent's sandboxed workspace. The explorer supports folder navigation, file-specific icons, rich previews for images and markdown, and interactive features like folder creation and drag-and-drop uploads.

## 3. Project Structure

```

.

├── backend/
│ ├── tools/
│ │ ├── ... (Modular tool files)
│ ├── langgraph\_agent.py # Core agent logic
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
