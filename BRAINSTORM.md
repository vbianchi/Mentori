Current Complex Task Flow (v2.1 Baseline)
-----------------------------------------

The current process for handling a complex task, once classified as "PLAN" intent, generally follows these stages:

1.  User Input: User provides a complex query.

2.  Intent Classifier: Classifies the query. If "PLAN", proceeds.

3.  Planner:

    -   Takes the user query and a summary of available tools.

    -   Generates a multi-step plan (list of `PlanStep` objects: description, tool hint, input instructions, expected outcome).

    -   Presents a human-readable summary and the structured plan to the user via the UI.

4.  User Confirmation (UI):

    -   User reviews the plan (summary and details).

    -   User clicks "Confirm & Run Plan" or "Cancel Plan". (Currently no modification options).

5.  Execution Loop (Backend - `message_handlers.process_execute_confirmed_plan`):

    -   Iterates through each step from the confirmed plan.

    -   Controller/Validator (`controller.validate_and_prepare_step_action`):

        -   Receives the current `PlanStep`, original user query, available tools, and an LLM.

        -   Validates/chooses the tool and formulates the precise `tool_input` string.

        -   Returns the validated tool name, input, reasoning, and a confidence score.

        -   Logs its decision and confidence.

    -   Executor (`agent.create_agent_executor` - ReAct agent):

        -   Receives a directive prompt based on the Controller's output (e.g., "Use tool X with input Y" or "Answer directly based on description Z").

        -   Executes the step using its internal ReAct cycle (Thought, Action, Observation).

        -   Callbacks (`callbacks.WebSocketCallbackHandler`) send detailed logs of the ReAct process (thoughts, tool use, outputs, errors) to the UI monitor.

        -   Step execution details (description, controller action, executor input/output, errors) are collected.

    -   The loop continues to the next step unless a step fails critically or the plan is cancelled.

6.  Evaluator (Overall Plan - `evaluator.evaluate_plan_outcome`):

    -   Called after the execution loop finishes (all steps attempted or plan halted).

    -   Receives the original user query, a formatted summary of all executed step details (including outcomes/errors), the preliminary final answer (often the output of the last successful step or an error message), and an LLM.

    -   Assesses if the overall user goal was met.

    -   Provides:

        -   `overall_success` (boolean).

        -   A textual `assessment` of the outcome.

        -   `missing_information` (if any).

        -   `suggestions_for_replan` (if applicable).

        -   A `confidence_score` for the evaluation.

    -   The `assessment` from the Evaluator is sent as the final message to the user in the chat.

    -   Evaluator's findings (assessment, suggestions) are logged.

Brainstorming Areas for Improvement & Further Development
---------------------------------------------------------

Here's a breakdown of potential areas to enhance the system's capabilities for complex tasks:

### 0\. Role-Specific LLM Configuration (NEW - User Suggestion)

-   Concept: Assign different LLM models to different agent components (Intent Classifier, Planner, Controller, Executor, Evaluator) based on the complexity and nature of their tasks.

-   Benefits:

    -   Optimized Capability: Use the most powerful/creative LLMs for planning, instruction-following LLMs for control, robust LLMs for evaluation, and potentially faster/cheaper LLMs for intent classification or simpler execution steps.

    -   Cost Efficiency: Reserve expensive, high-tier models for tasks that absolutely require them, using more economical models for other components.

    -   Resource Management & Speed: Potentially improve overall speed and reduce load on any single LLM endpoint.

-   Implementation:

    -   Add new `.env` configuration variables (e.g., `INTENT_CLASSIFIER_LLM_ID`, `PLANNER_LLM_ID`, `CONTROLLER_LLM_ID`, `EVALUATOR_LLM_ID`). The `EXECUTOR_LLM_ID` could default to the UI-selected LLM or also be a configurable default.

    -   Update `config.py` to load these new settings.

    -   Modify the points in `message_handlers.py` (and potentially `intent_classifier.py`, `planner.py`, `controller.py`, `evaluator.py` if LLM initialization is pushed down) where LLMs are initialized for each component to use these role-specific LLM IDs from the settings.

### 1\. Intent Classification & Initial Interaction

-   Granular Intents: Beyond "PLAN" vs. "DIRECT_QA", could we have more specific plan types (e.g., "RESEARCH_SYNTHESIS_PLAN", "DATA_ANALYSIS_PLAN", "CODE_GENERATION_PLAN") that might trigger different Planner prompts or default behaviors?

-   Confidence-Based Actions: If intent classification confidence is low, should the agent ask the user for clarification (e.g., "Are you asking a quick question, or do you want me to perform a series of actions?")?

-   Clarifying Questions (Pre-Planning): If a query is deemed complex but too ambiguous, allow the Planner (or a pre-planner LLM call) to ask clarifying questions *before* attempting to generate a full plan.

### 2\. Planning Phase (Planner Component)

-   Iterative Planning with User:

    -   Instead of just confirm/reject, allow users to provide feedback on the initial plan, and have the Planner refine it.

    -   "This step looks good, but for step 3, can you try using X tool instead?"

-   User Constraints & Preferences: Allow users to specify constraints during the initial query or plan review (e.g., "prioritize free tools," "limit web searches to 3," "use Python for scripting").

-   Alternative Plans: Could the Planner generate 2-3 high-level strategic approaches for complex tasks, allowing the user to pick one before detailed step generation?

-   Dynamic Tool Prompting: Improve how tools are presented to the Planner. Instead of just a summary, could it be more dynamic based on the query?

-   Sub-Planning: For very complex steps within a plan, the Planner (or a dedicated sub-planner) could break that step down further.

### 3\. User Plan Interaction (Pre-Execution Review)

-   Full Plan Editing:

    -   Allow users to directly edit step descriptions.

    -   Change the suggested tool for a step.

    -   Modify the `tool_input_instructions` that the Controller will use.

    -   Re-order steps.

    -   Add new steps manually.

    -   Delete steps.

-   Saving/Loading Plans: Allow users to save a (potentially modified) plan to reuse or refine later.

### 4\. Controller/Validator Enhancements

-   Richer Tool Schema Use: More deeply leverage `tool.args_schema` for validation (e.g., data types, required fields) and for guiding the LLM in formulating inputs.

-   Low Confidence Handling:

    -   If Controller's confidence for a step's action is low:

        -   Present the Controller's proposed action (tool & input) to the user for explicit confirmation for *that specific step*.

        -   Flag the step for more detailed scrutiny by the per-step Evaluator.

        -   Trigger a "micro-replan" for just that step, asking the Planner/Controller to try an alternative.

-   Resource Pre-Checks: Where feasible, add pre-flight checks before tool execution (e.g., URL validity, file existence if not intrinsic to the tool).

-   Permission Gateway: Integrate a clear permission request step here for sensitive tools (`workspace_shell`, `python_package_installer`, `Python_REPL`), even if the overall plan was approved. The request should detail the exact command/action.

### 5\. Executor Enhancements

-   Context Management Between Steps: How effectively is information passed from one step's output to the next step's input formulation (via Controller) or direct execution?

    -   Maintain a "plan scratchpad" or "step results context" that accumulates key outputs.

    -   Allow the Controller/Planner to explicitly reference outputs from previous steps when formulating input for future steps.

-   Direct Execution Mode: For some validated steps (e.g., a simple, safe shell command fully formulated by the Controller with high confidence), could the Executor run it directly without the full ReAct loop, for efficiency? (Requires careful security considerations).

### 6\. Evaluator Enhancements (Per-Step & Overall)

-   Per-Step Evaluation & Correction Loop:

    -   After each (or critical) step execution, invoke the Evaluator focused on that step's sub-goal.

    -   Automated Retry with Fixes: If the Evaluator identifies a fixable error (e.g., minor script bug, wrong parameter), it could:

        -   Provide the corrected input/script to the Controller.

        -   The Controller re-validates.

        -   The Executor attempts the step again.

    -   User Intervention Point: If automated correction fails or is not confident, present the Evaluator's analysis to the user: "Step X failed. The Evaluator thinks the issue is Y and suggests Z. How would you like to proceed? (Retry with suggestion / Edit step / Skip step / Abort plan)".

-   Sophisticated Overall Evaluation:

    -   More nuanced comparison of the collective outcome of all steps against the original multi-faceted user query.

    -   Ability to identify if all parts of the query were addressed.

-   Feedback Loop to Planner: If the overall evaluation is negative, the Evaluator's `suggestions_for_replan` should be used to:

    -   Automatically trigger a new planning cycle with the Planner, providing the feedback as context.

    -   Present the suggestions to the user, asking if they want to try a new plan based on them.

-   Synthesis of Results: The Evaluator could guide a final "synthesis" step, instructing the agent (perhaps via a new plan step) to combine key findings from successful steps into a coherent final answer or report.

### 7\. Error Handling and Robustness (Cross-Cutting)

-   Max Retries per Step: Implement a maximum number of retries for a failing step, even with Evaluator-suggested modifications.

-   Step Criticality: Allow the Planner to mark steps as "critical" or "optional." Failure of an optional step might not halt the entire plan.

-   User-Defined Error Handling: Allow users to specify preferences for how to handle errors (e.g., "always ask me," "try to fix automatically up to X times then ask").

### 8\. User Steering & Collaboration (In-Flight)

-   Pause/Resume: Allow users to pause a long-running plan.

-   Feedback Injection: While paused or even between steps, allow users to provide feedback like "That's not the right direction, focus on X instead" or "The last result was good, make sure to use it in the next step." This feedback would need to be incorporated by the Controller/Planner for subsequent steps.

-   Dynamic Plan Adjustment: Based on user feedback or unexpected intermediate results, allow the Planner to be re-invoked to adjust the *remainder* of the plan.

### 9\. Output Generation & Presentation

-   Dedicated Report Generation Tool/Agent: Trigger this after a successful (or partially successful, with user approval) plan execution.

-   Content Selection for Reports: The Evaluator's output or a dedicated LLM call could determine which artifacts and summaries are most relevant for inclusion in a final report.

-   Template-Based Reporting: Utilize predefined HTML/CSS templates for different report styles (as initially envisioned).




Current State & User Feedback (Post v2.1 Implementation)
--------------------------------------------------------

The agent now incorporates:

-   **Intent Classification:** Distinguishes simple queries from complex tasks.

-   **Planner, Controller, Executor Loop:** For complex tasks.

-   **Evaluator (Overall):** Assesses the final outcome of a plan.

-   **Role-Specific LLM Configuration:** Allows different LLMs for different components (though not yet fully utilized by all components via session settings).

-   **Refactored Backend:** Message handling is now modular in `message_handlers.py`.

**User Observations & Feedback:**

1.  **Bug:** Deleting a task in the UI does not delete the corresponding workspace folder on the backend.

2.  **Positive:** The system feels faster and smoother, likely due to role-specific LLMs and refactoring.

3.  **Feature Request (UI/UX):** Allow users to select/change the LLM for each specific role (Planner, Controller, Evaluator, etc.) directly from the UI, not just a single LLM for the Executor.

4.  **Feature Request (Resilience):** If a role-specific LLM fails (e.g., due to usage limits), the system should attempt a retry using the `DEFAULT_LLM_ID`.

5.  **Feature Request (Plan Visibility & Persistence):**

    -   The approved plan should remain visible in the UI after confirmation (perhaps collapsed).

    -   The plan should be saved to a file (e.g., `plan.md` or `plan.json`) in the task's workspace, making it an artifact.

    -   This file could be updated with step statuses (e.g., a checklist like `[x]`, `[ ]`, `[!]`).

    -   This could allow for breaking down plan steps into further sub-tasks.

6.  **Feature Request (Artifact Viewer):** Implement a file/folder structure view for the workspace within the Artifact Viewer.

7.  **Feature Request (Artifact Viewer):** Improve PDF viewing (currently just listed, not rendered).

Proposed Roadmap & Areas for Improvement
----------------------------------------

Based on the feedback and our v2.0 vision, here's a potential roadmap, prioritizing bug fixes, core enhancements, and then UX/feature additions:

### Phase 1: Stability & Core Loop Enhancement

1.  **Bug Fix: Workspace Deletion (User Point 1)**

    -   **Goal:** Ensure deleting a task properly removes its workspace folder.

    -   **Action:** Review and refine `process_delete_task` in `message_handlers.py` to ensure `shutil.rmtree` is effective and errors are handled/logged.

2.  **Implement LLM Retry/Fallback Logic (User Point 4)**

    -   **Goal:** Improve resilience if a configured role-specific LLM fails.

    -   **Action:** Modify `get_llm` (in `llm_setup.py`) or the points where it's called for each role. If the primary role-specific LLM fails, attempt to use the `DEFAULT_LLM_ID`. Log when fallbacks occur.

3.  **Enhance Plan Visibility & Persistence (User Point 5 - Basic)**

    -   **Goal:** Make the confirmed plan accessible.

    -   **Action (Backend):** In `process_execute_confirmed_plan` (message_handlers.py), after plan confirmation, save the `structured_plan_steps` to a `plan.md` (or `.json`) file in the task's workspace. This makes it an artifact.

    -   **Action (Frontend - `script.js`):** Modify `displayPlanForConfirmation` to *not* remove the plan UI upon confirmation. Instead, it could be collapsed or styled differently to indicate it's the "active plan." (More advanced UI for this can come later).

### Phase 2: User Control & Collaboration

1.  **UI for Role-Specific LLM Selection (User Point 3)**

    -   **Goal:** Allow users to override default role LLMs per session via the UI.

    -   **Action (UI - `index.html` & `script.js`):** Design a UI section (e.g., an "Advanced Settings" modal or a dedicated panel) with dropdowns for Planner LLM, Controller LLM, Evaluator LLM, etc.

    -   **Action (Backend - `server.py`, `message_handlers.py`):**

        -   Extend `session_data` to store these UI-selected role LLMs.

        -   Create a new WebSocket message type (e.g., `set_role_llm`) for the UI to send these selections.

        -   Update `intent_classifier.py`, `planner.py`, `controller.py`, `evaluator.py`, and the Executor/DirectQA paths in `message_handlers.py` to prioritize session-selected role LLMs, then `.env` role LLMs, then `DEFAULT_LLM_ID`.

2.  **Interactive Plan Modification (Expanding on User Point 5)**

    -   **Goal:** Allow users to edit the plan before execution.

    -   **Action (UI - `script.js`):** Enhance the plan confirmation UI to allow editing step descriptions, reordering, deleting steps, or (advanced) adding new steps.

    -   **Action (Backend):** The `execute_confirmed_plan` message would then receive the (potentially modified) plan from the UI.

### Phase 3: Advanced Features & UX Polish

1.  **Evaluator-Driven Re-planning/Correction (Core v2.0 Goal)**

    -   **Goal:** Make the agent learn from failed steps and improve.

    -   **Action:**

        -   If `EvaluationResult.overall_success` is `False` and `suggestions_for_replan` exist:

            -   Option 1 (Simpler): Present suggestions to the user, ask if they want to try a new plan based on them.

            -   Option 2 (Advanced): Automatically feed suggestions back to the Planner to generate a revised plan, then present *that* to the user.

        -   Implement per-step evaluation for critical steps.

2.  **PDF Artifact Viewing (User Point 7 - Simple)**

    -   **Goal:** Allow users to view PDFs.

    -   **Action (Frontend - `script.js`):** For PDF artifacts, render a simple link (`<a target="_blank">`) that opens the PDF in a new tab.

3.  **Workspace File Structure Viewer (User Point 6)**

    -   **Goal:** Improve artifact navigation.

    -   **Action (Backend - `tools.py` or `server.py`):**  `get_artifacts` needs to scan recursively and return paths.

    -   **Action (Frontend - `script.js`):** Implement a tree-like display for artifacts.

4.  **Plan as an Updatable Checklist (User Point 5 - Advanced)**

    -   **Goal:** Live tracking of plan progress.

    -   **Action:**

        -   When saving `plan.md`, use Markdown checklist syntax.

        -   After each step execution (in `process_execute_confirmed_plan`), update the `plan.md` file to mark the step as done (`[x]`), failed (`[!]`), or skipped.

        -   The Artifact Viewer would need to re-fetch/re-render this `plan.md` to show live updates.

5.  **Permission Gateway for Critical Steps (Core v2.0 Goal)**

    -   **Goal:** Enhance safety and user trust.

    -   **Action:** Before the Executor runs a sensitive tool (shell, package installer, Python REPL), even if validated by the Controller, send a specific confirmation request to the UI detailing the exact command.