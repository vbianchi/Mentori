# ResearchAgent: An Advanced AI-Powered Research Assistant

## 1. Overview

ResearchAgent is a sophisticated, AI-powered agent designed to handle complex, multi-step tasks in software engineering and scientific research. Built with a Python/LangGraph backend, it leverages a unique **Plan-Controller-Executor-Evaluator (PCEE)** architecture to autonomously create, execute, and evaluate plans to fulfill high-level user requests.

The core philosophy is built on **transparency and adaptive execution**. The agent creates detailed, structured plans and executes them step-by-step within a secure, sandboxed workspace. It is designed to understand the outcome of its actions and adapt its approach, providing a foundation for robust, self-correcting problem-solving.

## 2. Folder Structure

Here is the complete structure of the project's backend and configuration files:

```
ResearchAgent

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
├── .env.example # Template for environment variables
├── .gitignore # Specifies files to ignore for version control
├── docker-compose.yml # Orchestrates the Docker container
├── Dockerfile # Defines the application's Docker image
└── requirements.txt # Python dependencies

```

## 3. Setup and Installation

This project is designed to be run inside a Docker container for security, consistency, and ease of setup.

### Prerequisites

* **Docker:** Ensure Docker and Docker Compose are installed on your system. [Official Docker Installation Guide](https://docs.docker.com/engine/install/)

### Step-by-Step Instructions

1.  **Clone the Repository:**
    If this project were on GitHub, you would clone it. For now, ensure all the files listed in the structure above are in a single project directory.

2.  **Configure Environment Variables:**
    Your API keys and other secrets must be configured before running the application.
    ```bash
    # Create the .env file from the example template
    cp .env.example .env
    ```
    Now, open the newly created `.env` file with a text editor and fill in the required values, at a minimum:
    * `GOOGLE_API_KEY`: Your API key for Google Gemini models.
    * `TAVILY_API_KEY`: Your API key for the Tavily search tool.
    * `ENTREZ_EMAIL`: Your email for the PubMed tool (if you add it later).
3.  **Build and Run the Application:**
    Navigate to the project's root directory in your terminal and run the following Docker Compose command:
    ```bash
    # This command builds the Docker image and starts the backend server.
    # The --build flag is only necessary the first time or after changing
    # dependencies or the Dockerfile.
    docker compose up --build
    ```
    Docker will now build the image (installing all Python dependencies from `requirements.txt` using `uv`) and start the backend service. You will see the server logs in your terminal, ending with a line like:
    `INFO - Starting ResearchAgent WebSocket server at ws://0.0.0.0:8765`

    The server is now running and ready to accept connections.

## 4. Testing the Agent

Since we do not yet have a frontend UI, you can interact with the agent directly using a command-line WebSocket client.

### Prerequisites

* **wscat:** A simple command-line client for WebSockets, installable via `npm`.
    ```bash
    # Install wscat globally
    npm install -g wscat
    ```

### Connecting to the Agent

1.  Leave the terminal with the running Docker container open.
2.  Open a **new, separate terminal**.
3.  Connect to the agent using the following command:
    ```bash
    wscat -c ws://localhost:8765
    ```
4.  You will see a `Connected (press CTRL+C to quit)` message and a `>` prompt. You can now send requests to the agent.

### Example Test Cases

* **Test Case A (Direct QA):**
    ```
    > What is the speed of light?
    ```

* **Test Case B (File System Task):**
    ```
    > Write a python script that prints 'Hello, World!' to a file named 'hello.py', then list all the files in the workspace.
    ```

You will see a real-time stream of JSON events from the agent as it thinks and executes its plan.
