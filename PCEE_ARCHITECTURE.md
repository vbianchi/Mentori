# The ResearchAgent's Advanced PCEE Architecture: A Detailed Blueprint

## 1. Introduction & Guiding Philosophy

This document details the advanced agent architecture we have designed for the ResearchAgent. Our goal is to move beyond simple, single-step agents (like the ReAct model) and create a robust, resilient system capable of handling complex, multi-step scientific and software engineering tasks.

The core philosophy is to model the agent not as a single monolithic brain, but as a small, specialized **"company"** or project team. Each member of the team has a distinct role and responsibility, creating a clear and logical flow of work from high-level strategy to hands-on execution and quality assurance. This separation of concerns is the key to achieving the adaptive execution and self-correction capabilities outlined in our project brief.

## 2. The "Company Model": Our Cast of Agents

Our system is composed of four primary intelligent nodes, each with a clear title and purpose, working within a secure, sandboxed environment.

* **The "Chief Architect" (Planner Node):** The strategic thinker. Given a high-level user request, its sole job is to create a comprehensive, structured, step-by-step "blueprint" for the entire project. This plan is generated as a detailed JSON object.

* **The "Site Foreman" (Controller Node):** The project manager. This is the heart of the execution loop. It reads the Architect's blueprint one step at a time, prepares the necessary tools and materials (data piping), and hands off precise instructions to the Worker. It is responsible for managing the state of the project.

* **The "Worker" (Executor Node):** The hands-on specialist. It is not designed to think strategically. It receives a single, explicit command from the Foreman and executes it perfectly. Its only job is to run the tool it is given with the input it receives.

* **The "Project Supervisor" (Evaluator Node):** The quality assurance inspector. After the Worker completes a task, the Supervisor inspects the result. It determines if the task *truly* met the goal of the plan step, considering not just the raw output but also the Foreman's intent. It has the power to declare a step a success or a failure.

## 3. The End-to-End Workflow: From Query to Completion

Here is the step-by-step flow of a complex user request through our system.

**User Request Example:** `"Please find the latest version of the 'scikit-learn' library and write a Python script that installs it and prints the version."`

---

#### **Step 1: The Request & Sandbox Creation (`prepare_inputs_node`)**

1.  The user submits the request through the UI.
2.  The backend `server.py` receives the message.
3.  The LangGraph workflow begins at the `prepare_inputs_node`.
4.  This node immediately creates a unique, secure, sandboxed directory for this specific task (e.g., `/workspace/task_id_12345/`).
5.  It initializes the `GraphState`, populating it with the user's input and the unique `workspace_path`.

---

#### **Step 2: The Blueprint (`structured_planner_node`)**

1.  The graph transitions to the "Chief Architect."
2.  **Inputs:** The Planner receives the user's request and a list of all available tools and their descriptions.
3.  **Action:** It uses a powerful LLM (e.g., Gemini 2.5 Pro) and a specialized prompt to decompose the user's request into a detailed, structured JSON plan.
4.  **Output:** A JSON object is added to the `GraphState`. For our example, this blueprint would look something like this:

    ```json
    {
      "plan": [
        {
          "step_id": 1,
          "instruction": "Search the web to find the latest version number for the 'scikit-learn' Python package.",
          "tool_name": "tavily_search",
          "tool_input": "scikit-learn latest version pypi"
        },
        {
          "step_id": 2,
          "instruction": "Create a Python script named 'install_and_verify.py' that will install the version found in the previous step and then print it.",
          "tool_name": "write_file",
          "tool_input": {
            "file": "install_and_verify.py",
            "content": "import os\nimport subprocess\n\nversion = '{step_1_output}'\nsubprocess.run(['pip', 'install', f'scikit-learn=={version}'], check=True)\nprint(f'Successfully installed scikit-learn version {version}')"
          }
        },
        {
          "step_id": 3,
          "instruction": "Execute the 'install_and_verify.py' script to perform the installation and confirm the version.",
          "tool_name": "workspace_shell",
          "tool_input": "python install_and_verify.py"
        }
      ]
    }
    ```
    *Notice the `{step_1_output}` placeholder. This is a crucial instruction for the Controller.*

---

#### **Step 3: The Execution Loop (Controller -> Executor -> Evaluator)**

The graph now enters the main loop, managed by the "Site Foreman."

**LOOP 1:**

* **3a. Controller:** Reads Step 1 from the plan. It sees the `tool_input` is a simple string and requires no data piping. It prepares the tool call: `tavily_search("scikit-learn latest version pypi")`.
* **3b. Executor:** Receives the command and runs the Tavily search tool.
* **3c. Evaluator:** Receives the search results. It confirms that the output contains a plausible version number (e.g., "1.5.1"). It declares the step a **`success`** and records the raw search result to the state.
* **3d. Router (`should_continue`):** Sees the success and that the plan is not finished. It routes the graph to the `increment_step_node`.
* **3e. Incrementer:** The `current_step_index` is incremented to `1`. The graph loops back to the Controller.

**LOOP 2:**

* **3a. Controller:** Reads Step 2 from the plan. It sees the `tool_input` for the `write_file` tool contains the placeholder `{step_1_output}`.
    * **Data Piping:** The Controller accesses its memory and replaces the placeholder with the actual version number it got from the output of Step 1.
    * It prepares the final tool call with the "hydrated" content.
* **3b. Executor:** Receives the command and runs the `write_file` tool, creating `install_and_verify.py` in the sandboxed workspace.
* **3c. Evaluator:** Sees that the tool reported a success message. It declares the step a **`success`**.
* **3d. Router:** Sees success, loops back via the incrementer.

**LOOP 3:**

* **3a. Controller:** Reads Step 3. The `tool_input` is simple. It prepares the tool call: `workspace_shell("python install_and_verify.py")`.
* **3b. Executor:** Runs the command inside the sandboxed workspace.
* **3c. Evaluator:** Sees that the command output includes "Successfully installed scikit-learn version 1.5.1" and the exit code was 0. It declares the step a **`success`**.
* **3d. Router:** Sees success, but also sees that `current_step_index` now equals the length of the plan. It routes to **`END`**.

---

#### **Step 4: Task Completion**

The agent's work is done. The final `GraphState` contains the full plan, the complete history of every action taken, and all generated artifacts (the Python script) are available in the secure workspace for the user to inspect or download.

## 4. The Future: The Self-Correction Sub-Loop

The next evolution of this architecture (our **Phase 6**) is to make the "Site Foreman" (Controller) even smarter. In the future, if the "Project Supervisor" (Evaluator) reports a `failure`, the `should_continue` router will not just end the process. It will instead route to a new **`correction_planner_node`**.

This "Correction Planner" will receive the failed step, the error message, and the execution history. Its job is to create a *new, short-term plan* specifically to fix the error. For example:
* **Error:** `ModuleNotFoundError: No module named 'scikit-learn'`
* **Correction Plan:** `["pip install scikit-learn"]`

The Controller would then execute this sub-plan. If the correction succeeds, it would then retry the original failed step. This creates a powerful, nested loop for self-healing and is the key to creating a truly autonomous and reliable agent.
