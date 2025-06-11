# ResearchAgent: An Advanced AI-Powered Research Assistant

## 1\. Overview

ResearchAgent is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend and a modern JavaScript frontend (Vite + Preact), it leverages a unique **Plan-Controller-Executor-Evaluator (PCEE)** architecture to autonomously create, execute, and evaluate structured plans to fulfill high-level user requests.

The core philosophy is built on **transparency, adaptive execution, and security**. The agent first uses a `Router` to determine if a request requires a simple answer or a complex plan. For complex tasks, it generates a detailed blueprint and executes it step-by-step within a secure, sandboxed workspace. It is designed to understand the outcome of its actions and has a foundational architecture for future self-correction and human-in-the-loop collaboration.

## 2\. Key Features

-   **Advanced PCEE Architecture:** A robust, multi-node graph that separates routing, planning, control, execution, and evaluation for complex task management.
-   **Intelligent Task Routing:** A `Router` node classifies user requests to either provide a direct answer for simple questions or trigger the full planning engine for complex tasks.
-   **Structured JSON Planning:** The agent's "Chief Architect" (Planner) generates detailed JSON-based plans, including tool selection and expected outcomes for each step.
-   **Secure Sandboxed Workspaces:** Every task is assigned a unique, isolated directory, ensuring security and preventing state-collision between different tasks.
-   **Modular & Resilient Tools:** A flexible tool system allows for easy addition of new capabilities. Current tools include web search, a sandboxed file system (read, write, list), and a sandboxed shell.
-   **Interactive Frontend:** A responsive user interface built with Vite and Preact that provides real-time visibility into the agent's operations.
    -   **Live Event Stream:** See the agent's thought process and actions as they happen, for both plans and direct answers.
    -   **Dynamic** Model **Selection:** Configure the LLM for each agent role (Router, Planner, etc.) directly from the UI.
    -   **Interactive Workspace:** Browse, view, and upload files directly within the agent's sandboxed workspace.
    -   **Artifact Viewer:** Click on generated files like code, markdown, or text to view their contents instantly.

## 3\. Project Structure

```
.
├── backend/
│ ├── tools/
│ │ ├── init.py # Smart tool loader
│ │ ├── file_system.py # Sandboxed file I/O tools
│ │ ├── tavily_search.py # Tavily web search tool
│ │ └── workspace_shell.py # Tool to execute bash commands
│ │
│ ├── init.py # Makes 'backend' a Python package
│ ├── langgraph_agent.py # Core PCEE agent logic with Router
│ ├── prompts.py # Centralized prompts for all agent nodes
│ ├── server.py # WebSocket server entry point
│ └── visualize_graph.py # Script to generate a graph diagram
│
├── src/ # Frontend source code
│ ├── App.jsx # Main UI component
│ ├── index.css # Global CSS and Tailwind directives
│ └── main.jsx # Frontend application entry point
│
├── .env.example # Template for environment variables
├── .gitignore # Specifies files to ignore for version control
├── BRAINSTORM.md # Document for future ideas
├── docker-compose.yml # Orchestrates the Docker container
├── Dockerfile # Defines the application's Docker image
├── index.html # Main HTML entry point for Vite
├── package.json # Frontend dependencies and scripts
├── PCEE_ARCHITECTURE.md # Document detailing the agent's design
├── postcss.config.js # PostCSS configuration
├── tailwind.config.js # Tailwind CSS configuration
├── vite.config.js # Vite build tool configuration
├── ROADMAP.md # Project development plan
└── README.md # This document
```

## 4\. Installation & Setup

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
3.  **Access the Application:**
