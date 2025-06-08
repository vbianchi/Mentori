# ResearchAgent: An Advanced AI-Powered Research Assistant

## 1. Overview

ResearchAgent is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend and a modern JavaScript frontend (Vite + Preact), it leverages a unique **Plan-Controller-Executor-Evaluator (PCEE)** architecture to autonomously create, execute, and evaluate structured plans to fulfill high-level user requests.

The core philosophy is built on **transparency, adaptive execution, and security**. The agent creates detailed, structured plans and executes them step-by-step within a secure, sandboxed workspace for each task. It is designed to understand the outcome of its actions and has a foundational architecture for future self-correction and human-in-the-loop collaboration.

## 2. Key Features

* **Advanced PCEE Architecture:** A robust, multi-node graph that separates planning, control, execution, and evaluation for complex task management.
* **Structured Planning:** The agent's "Chief Architect" (Planner) generates detailed JSON-based plans, including tool selection and expected outcomes for each step.
* **Secure Sandboxed Workspaces:** Every task is assigned a unique, isolated directory, ensuring security and preventing state-collision between different tasks.
* **Modular, "Plug-and-Play" Tools:** A flexible tool system allows for easy addition of new capabilities. Current tools include web search and a sandboxed file system (read, write, list).
* **Modern Frontend:** A responsive user interface built with Vite and Preact for real-time streaming of the agent's thought process.

## 3. Project Structure

```
.
├── backend/
│ ├── tools/
│ │ ├── init.py # Smart tool loader
│ │ ├── file\_system.py # Sandboxed file I/O tools
│ │ └── tavily\_search.py # Tavily web search tool
│ │
│ ├── init.py # Makes 'backend' a Python package
│ ├── langgraph\_agent.py # Core PCEE agent logic
│ ├── prompts.py # Centralized prompts for all agent nodes
│ └── server.py # WebSocket server entry point
│
├── src/ # Frontend source code
│ ├── App.jsx # Main UI component
│ ├── index.css # Global CSS and Tailwind directives
│ └── main.jsx # Frontend application entry point
│
├── .env.example # Template for environment variables
├── .gitignore # Specifies files to ignore for version control
├── docker-compose.yml # Orchestrates the Docker container
├── Dockerfile # Defines the application's Docker image
├── index.html # Main HTML entry point for Vite
├── package.json # Frontend dependencies and scripts
├── package-lock.json # Locked versions of frontend dependencies
├── postcss.config.js # PostCSS configuration for Tailwind
├── tailwind.config.js # Tailwind CSS configuration
├── vite.config.js # Vite build tool configuration
└── requirements.txt # Python dependencies
```

## 4. Installation & Setup

You will need two separate terminals to run the backend and frontend servers.

### Prerequisites

* **Docker:** Ensure Docker and Docker Compose are installed. [Official Docker Installation Guide](https://docs.docker.com/engine/install/)
* **Node.js & npm:** Ensure Node.js (which includes npm) is installed. [Official Node.js Website](https://nodejs.org/)

### Step 1: Backend Server

1.  **Clone the Repository:**
    If this project were on GitHub, you would clone it. For now, ensure all the files listed in the structure above are in a single project directory.

2.  **Configure Environment Variables:**
    Your API keys are required for the agent to function.
    ```bash
    # Create the .env file from the example template
    cp .env.example .env
    ```
    Open the newly created `.env` file and fill in your `GOOGLE_API_KEY` and `TAVILY_API_KEY`.

3.  **Run the Backend:**
    Navigate to the project's root directory in your **first terminal** and run:
    ```bash
    # This builds the Docker image and starts the backend WebSocket server.
    docker compose up --build
    ```
    Keep this terminal running. The backend will be available at `ws://localhost:8765`.

### Step 2: Frontend Server

1.  **Install Dependencies:**
    In your **second terminal**, navigate to the same project root directory and run:
    ```bash
    # This reads package.json and installs all frontend dependencies.
    npm install
    ```

2.  **Run the Frontend:**
    Once the installation is complete, run the development server:
    ```bash
    # This starts the Vite development server.
    npm run dev
    ```
    You will see a message indicating the server is running.

3.  **Access the Application:**
    Open your web browser and navigate to the local URL provided by Vite (usually `http://localhost:5173`). You should see the ResearchAgent UI, connected and ready for prompts.
