# ResearchAgent - Project Roadmap

This document outlines the phased development plan for the ResearchAgent project. Each phase represents a significant milestone in the journey toward creating a robust, autonomous research assistant.

### ✔️ Phase 0: Project Setup

-   \[x\] Define project folder structure.
-   \[x\] Create and configure `.env.example` for environment variables.
-   \[x\] Establish Python dependencies in `requirements.txt`.
-   \[x\] Create `Dockerfile` for a reproducible environment.
-   \[x\] Create `docker-compose.yml` for easy application orchestration.
-   \[x\] Create `.gitignore` to protect secrets and ignore unnecessary files.
-   \[x\] Create project documentation (`README.md`, `BRAINSTORM.md`, `ROADMAP.md`).
**Status: Completed**

### ✔️ Phase 1: The Simplest Working Server

-   \[x\] Implement a basic WebSocket server (`server.py`) that can accept connections.
-   \[x\] Verify the core communication channel with a simple echo test.
**Status: Completed**

### ✔️ Phase 2: Minimal LangGraph Agent

-   \[x\] Create the initial `langgraph_agent.py`.
-   \[x\] Implement a minimal graph with a single `direct_qa_node` for simple LLM calls.
-   \[x\] Integrate the agent into `server.py` to replace the echo logic.
**Status: Completed**

### ✔️ Phase 3: Initial Tool-Using Agent

-   \[x\] Implement a modular, plug-and-play tool loading system (`backend/tools/__init__.py`).
-   \[x\] Create initial tools (`tavily_search`, `workspace_shell`).
-   \[x\] Implement an `intent_classifier` to route between direct QA and tool-based actions.
-   \[x\] Implement a basic ReAct agent to use the tools.
**Status: Completed**

### ✔️ Phase 4: Advanced PCEE Architecture

-   \[x\] **(Planner):** Implement a `structured_planner_node` that creates a detailed, multi-step JSON plan.
-   \[x\] **(Controller):** Implement a `controller_node` to read the structured plan.
-   \[x\] **(Executor):** Implement an `executor_node` to run the tool calls specified in the plan.
-   \[x\] **(Evaluator):** Implement an `evaluator_node` to assess step outcomes.
-   \[x\] **(Memory):** Implement a `history` state to allow the agent to pass information between steps.
-   \[x\] **(Loop):** Implement a conditional router (`should_continue`) to create a full execution loop that iterates through the plan.
-   \[x\] **(Sandboxing):** Implement the foundational logic for creating and using secure, per-task workspaces.
**Status: Completed**

### Phase 5: Frontend Development & UI Integration

-   \[ \] Create the foundational `index.html` file with the main UI structure.
-   \[ \] Create a `style.css` file to define the visual appearance, focusing on clarity and usability.
-   \[ \] Create a `script.js` file to handle WebSocket communication.
-   \[ \] Implement JavaScript logic to send user prompts to the backend.
-   \[ \] Implement JavaScript logic to receive and parse the real-time stream of agent events.
-   \[ \] Build a dynamic UI that can render the hierarchical plan and the agent's "thoughts" as they happen, fulfilling our core UX vision.
**Status: Up Next**

### Phase 6: Advanced Self-Correction & Environment Management

-   \[ \] **Smarter Evaluator:** Enhance the evaluator to understand a wider range of errors beyond simple exit codes.
-   \[ \] **Correction Sub-Loop:** Upgrade the Controller. When the Evaluator reports a recoverable failure (e.g., `ModuleNotFoundError`), the Controller should attempt a corrective action (e.g., `pip install <module>`) before retrying the original step.
-   \[ \] **Python Virtual Environments:** Implement the full sandboxing plan by having the agent create and activate a `.venv` inside each task's workspace for all `pip` and `python` commands.

### Phase 7: Human-in-the-Loop (HITL) Integration

-   \[ \] Implement a `pause/resume` mechanism in the agent's execution loop.
-   \[ \] Add frontend controls (e.g., a "Pause" button) that can trigger this state.
-   \[ \] Create a special `HITL` node in the graph for high-stakes actions.
-   \[ \] When the agent routes to the `HITL` node, it will pause and send a confirmation request to the UI. Execution will only resume upon user approval.
