BRAINSTORM.md - ResearchAgent Project (v2.5.3 Target)
=====================================================

This document tracks the current workflow, user feedback, and immediate brainstorming ideas for the ResearchAgent project.

Current Version & State (Targeting v2.5.3):

Recent key advancements and fixes:

-   Core Agent Logic & Tool Integration (RESOLVED):

    -   `deep_research_synthesizer` & `write_file` Flow: The critical bug chain preventing the actual content from `deep_research_synthesizer` being saved by `write_file` has been resolved. This involved fixes in:

        -   `backend/controller.py`: Ensuring correct JSON string input for tools.

        -   `backend/agent.py`: Refining the ReAct agent prompt to output raw tool observations as its `Final Answer`.

        -   `backend/evaluator.py`: Making the Step Evaluator stricter about verifying actual content generation.

    -   Backend `IndentationError` issues in `agent_flow_handlers.py` have been resolved.

-   Chat UI/UX Refinement (Design Solidified, Backend Ready, Frontend Implementation Next):

    -   New Vision (Inspired by `manus.ai` and User Feedback):

        -   Sequential Main Messages: User inputs, major plan step announcements (e.g., "Step 1/N: Doing X"), and significant agent sub-statuses (e.g., "Controller: Validating step...", "Executor: Using tool Y...", "Evaluator: Step Z complete.") will appear sequentially in the main chat area. Each of these messages will have a colored side-line indicating the source/component (e.g., Planner blue, Controller orange, Executor green, Tool teal, Evaluator purple, System grey) and will *not* have a background bubble (except for user messages and the final agent conclusive message).

        -   Persistent Bottom "Thinking" Line: A single, unobtrusive line at the very bottom of the chat area will be dedicated to displaying low-level, rapidly updating "Thinking (LLM)...", "LLM complete.", or "Tool X processing..." statuses from `callbacks.py`. This line will update in place and also feature a colored side-line corresponding to the active component.

        -   Final Agent Message: Will appear in a distinct, styled bubble with its own colored side-line.

    -   `simulation.html` (Conceptual Guide): The vision for this UI is captured in a conceptual HTML/Markdown mock-up, detailed below in "Chat UI Simulation (Conceptual)". This serves as the visual target for frontend development.

    -   Backend Message Structure Ready:

        -   `callbacks.py`: Sends structured `agent_thinking_update` messages with `component_hint` (e.g., `LLM_CORE`, `TOOL_TAVILY_SEARCH_API`) for frontend styling decisions. `on_tool_error` messages are now less alarming in chat.

        -   `agent_flow_handlers.py`: Sends new `agent_major_step_announcement` WebSocket message type for each plan step (containing step number, total steps, description, component hint). Other `agent_thinking_update` messages from here also include `component_hint`.

    -   Status Message Persistence (Backend Complete):

        -   Critical `status_message` types (e.g., "Loading history...", "Plan processing stopped...") are now saved to the database by `server.py`.

        -   `task_handlers.py` now loads and sends these saved `status_message`s to the frontend when chat history is repopulated, ensuring they persist across page refreshes.

-   Plan Proposal UI & Persistence (COMPLETE): Remains functional.

-   Monitor Log Enhancements (Backend Ready, Frontend CSS Next):

    -   Backend provides `log_source` for monitor entries. Frontend `monitor_ui.js` adds CSS classes. CSS styling for colors is pending.

Immediate Focus & User Feedback / Known Issues:

1.  IMPLEMENT (High Priority): New Chat UI Rendering (Frontend Task):

    -   Issue: Current chat UI (based on user-provided baseline files) does not yet reflect the new `manus.ai`-inspired design.

    -   Goal: Update `script.js`, `chat_ui.js`, and `style.css` (from the user-provided baseline) to implement the vision captured in the "Chat UI Simulation (Conceptual)" section below.

        -   `script.js`: Ensure `agent_major_step_announcement` is correctly dispatched.

        -   `chat_ui.js`:

            -   Implement rendering for `agent_major_step_announcement` as distinct, non-bubbled messages with colored side-lines.

            -   Refactor `showAgentThinkingStatusInUI` to:

                -   Update the persistent bottom line for low-level LLM churn messages.

                -   Render significant sub-statuses as new, distinct, non-bubbled messages in the main chat flow by calling `addChatMessageToUI`.

            -   Ensure `status_message`s (live and from history) are rendered left-aligned with a system-colored side-line (fixing previous centering).

            -   Fix `<strong>` tag rendering by consistently using `innerHTML` for formatted content.

        -   `style.css`: Add all necessary CSS rules for the new message appearances and colored side-lines.

    -   Persistence Check: Verify that the newly styled status messages are indeed persistent after page refresh.

2.  BUG FIX (Medium Priority): Chat Input Unresponsive:

    -   Issue: After a task completes, chat input sometimes remains disabled.

    -   Goal: Ensure `StateManager.isAgentRunning` is correctly reset and UI re-enables input.

3.  DEBUG (Medium Priority): Monitor Log Color-Coding:

    -   Issue: Visual differentiation by `log_source` in the Monitor Log is not yet appearing correctly.

    -   Goal: Implement effective color-coding.

    -   Action: Create/Debug CSS rules in `style.css`. Verify `log_source` consistency from all backend logging points.

Chat UI Simulation (Conceptual - Represents `simulation.html` idea):

*This simulation details the target look and feel for the chat interface.*

-   User Messages: Standard bubble, right-aligned (e.g., user accent color `#0D9488`).

    -   Example: `Create a heatmap with random data and save it as "heatmap.png"`

-   Agent/System Messages (Sequential, Non-Bubbled, with Side-Lines):

    -   Intent Classifier Update: (Left-aligned, Light Blue side-line #5DADE2, no bubble, italic)

        _Intent: This task requires planning. Generating a plan..._

    -   Planner Update & Plan Proposal: (Left-aligned, Medium Blue side-line #3498DB, no bubble)

        Okay, I'll create a plan to generate a heatmap...

        Here's the proposed plan:

        (Plan Proposal Block - styled distinctly, Planner blue accent line/theme)

    -   System Status (e.g., Plan Confirmed): (Left-aligned, Grey side-line #7F8C8D, no bubble, italic)

        _Plan confirmed. Starting execution..._

    -   Agent Major Step Announcement: (Left-aligned, Controller Orange side-line #E67E22, no bubble)

        **Step 1/5: Install required Python packages (numpy, matplotlib, seaborn).**

    -   Agent Significant Sub-Status (Controller): (Left-aligned, Controller Orange side-line, no bubble, italic)

        _Controller: Validating step, preparing \python_package_installer`..._`

    -   Agent Significant Sub-Status (Executor/Tool): (Left-aligned, Tool Teal side-line #1ABC9C, no bubble, italic)

        _Executor: Installing \numpy, matplotlib, seaborn`..._`

    -   Agent Significant Sub-Status (Evaluator): (Left-aligned, Evaluator Purple side-line #9B59B6, no bubble, italic)

        _Evaluator: Packages installed successfully._

    -   *(This pattern repeats for each step and its significant sub-statuses)*

    -   Warning Example (if a recoverable error happened): (Left-aligned, Warning Amber side-line #F39C12, no bubble, italic)

        _Warning: Initial attempt for Step X failed, retrying..._

-   Agent Final Conclusive Message: (Left-aligned, Default Agent Dark Green side-line #0F766E, WITH background bubble)

    The heatmap has been successfully generated... You can find it in the Artifacts panel.

-   Persistent Bottom "Thinking" Line (Single line at the very bottom of the chat, updates in place):

    -   (Side-line color changes based on component: LLM Core grey `#7f8c8d`, Controller orange `#E67E22`, etc.)

    -   Example Text: `_Thinking (Controller LLM)..._` which then updates to `_Controller LLM complete._` or `_Idle._`

This refined workflow aims for clarity, providing a high-level sequential log of actions in the main chat, while relegating very rapid, low-level "thinking" updates to a persistent but unobtrusive bottom line.