# BRAINSTORM.md - ResearchAgent Project (V1.0 Go-Live Target & Beyond)

This document tracks the current workflow, user feedback, and brainstorming ideas for the ResearchAgent project.
## Current Version & State (Targeting V1.0 Go-Live)

**Recent Key Advancements:**

1.  **Architectural Refactor: "Plug and Play" Tool System (COMPLETE & STABLE):**
    * Implemented a dynamic tool loading mechanism using `tool_config.json`.
    * `tool_loader.py` parses the config and instantiates tools, including injecting runtime context like `task_workspace` for task-specific tools.
    * All 9 tools (6 general-purpose + 3 task-specific) are dynamically loaded and operational.
    * This provides a scalable and maintainable foundation for future tool development.
2.  **Pydantic v2 Migration (Largely Complete):**
    * Most Pydantic models for Tool Argument Schemas and LLM Output Schemas migrated to v2.
    * Fixes for Pydantic v2 strictness issues resolved.
    * The `TypeError` in `deep_research_tool.py` related to `field_validator` and `each_item` has been addressed.
3.  **Core Agent Logic & Tool Integration (IMPROVED):**
    * Controller logic refined.
    * Numerous import and runtime errors resolved.
    * ReAct agent prompt in `backend/agent.py` updated for more reliable direct content generation.
4.  **Chat UI/UX Refinement (Significant Progress - features as previously listed):**
    * Visual Design & Readability improvements.
    * Interactivity: Collapsible steps and tool outputs.
    * Persistence & Consistency for plans.
    * Bug fixes related to UI rendering and behavior.
    * Completed Features: Token Counter, File Upload, In-Chat Tool Feedback, Plan Proposal UI.
5.  **History Handling:**
    * Added `monitor_user_input` to known history types to resolve warnings.

## Immediate Focus & User Feedback / Known Issues / Proposed Enhancements (V1.0 Go-Live Focus):

1.  **CRITICAL: Agent Task Cancellation & STOP Button:**
    * **Issue:** Switching UI tasks or using STOP button needs to reliably cancel/stop active agent processing. Status updates can bleed between tasks.
    * **Goal:** Implement robust agent task cancellation. Ensure STOP button is fully functional and UI task switching correctly cancels the previous task.
    * **Effort:** ~7/10 (Backend: 6, Frontend: 4)
    * **Time Est.:** ~9-12 hours

2.  **HIGH: BUG - ARTIFACT VIEWER REFRESH:**
    * **Issue:** Artifact viewer does not consistently or immediately auto-update after file writes mid-plan.
    * **Goal:** Ensure reliable and immediate auto-update.
    * **Effort:** ~4/10 (Backend: 3, Frontend: 3)
    * **Time Est.:** ~4-6 hours

3.  **HIGH: AGENT CAPABILITIES - Robust Step Evaluation & Basic Retry:**
    * **Issue:** Evaluator needs to reliably assess step success (content vs. description of it). Retry mechanism should effectively use evaluator feedback.
    * **Goal:** Ensure PCEE loop's Evaluator is robust and retry mechanism is effective.
    * **Effort:** ~7/10 (Backend LLM prompting & agent flow logic)
    * **Time Est.:** ~8-12 hours

4.  **HIGH: DEV OPS / STABILITY - Comprehensive Testing:**
    * **Goal:** Expand unit and integration tests for critical backend (cancellation, agent lifecycle, all tools) and frontend components.
    * **Effort:** ~6/10 (Initial batch)
    * **Time Est.:** ~10-15 hours (Initial batch)

5.  **MEDIUM: Make Tavily Search Optional:**
    * **Goal:** Add a configuration option to disable Tavily search for privacy reasons. Inform the user about potential impacts on answer accuracy.
    * **Effort:** ~5/10 (Backend: 3, Frontend: 2)
    * **Time Est.:** ~3-5 hours

6.  **MEDIUM: UI/UX - Finalize "View [artifact] in Artifacts" Links:**
    * **Goal:** Implement full functionality for links within chat (e.g., from tool outputs) to directly open/highlight the mentioned artifact in the Artifact Viewer.
    * **Effort:** ~3/10
    * **Time Est.:** ~2-3 hours

7.  **MEDIUM: "Plug and Play" Tool System Enhancements:**
    * **Formalize Tool Input/Output Schemas:** Transition `input_schema_description` in `tool_config.json` to formal JSON Schemas (leveraging Pydantic `args_schema` from tool classes).
        * **Effort:** ~5/10
        * **Time Est.:** ~4-6 hours
    * **Develop New Tool Integration Guide:** Create comprehensive documentation and templates for adding new tools to the system.
        * **Effort:** ~4/10
        * **Time Est.:** ~3-5 hours

8.  **MEDIUM: UI/UX - Artifact Viewer - Folder Link/View (Simple Version):**
    * **Goal:** Enhance artifact viewer to provide links to open the task workspace folder or a simple list of folder contents.
    * **Effort:** ~2/10 (for simple link/listing)
    * **Time Est.:** ~2-3 hours

9.  **LOW: UI BUG - Copy button placement for simple messages:**
    * **Issue:** Copy button is sometimes centered in the chat UI after a simple message instead of being next to the chat bubble.
    * **Goal:** Adjust CSS/JS for correct placement.
    * **Effort:** ~2/10
    * **Time Est.:** ~1-2 hours

10. **LOW: UI/UX POLISH & DEBUGGING (as previously listed, e.g., Monitor Log Color-Coding, Plan File Status Update Warnings, "agent-thinking-status" line, agent step announcement styling).**
    * Review and refine the behavior and appearance of the global "agent-thinking-status" line. (Effort: 2, Time: 1-2h)
    * Consider if further styling (e.g., boxing, copy button) is needed for agent step announcements. (Effort: 2, Time: 1-2h)
    * WARNING: PLAN FILE STATUS UPDATE: Investigate and fix backend warnings about not finding step patterns. (Effort: 3, Time: 2h)
    * REVIEW: "UNKNOWN" HISTORY MESSAGE TYPES: Confirm handling of any remaining internal DB message types. (Effort: 1, Time: 1h)
    * DEBUG: Monitor Log Color-Coding: Verify/implement CSS for log differentiation. (Effort: 1, Time: 1-2h)

## Future Brainstorming / More Complex Enhancements (Post V1.0 Go-Live & Tool Refactor)

### SHOULD HAVE (Important for V1.x releases):
(Content largely same as previous full README: Enhanced Agent Capabilities, Multi-Tasking, Advanced UITL)

### NICE TO HAVE (Valuable additions for future iterations):

1.  **Advanced Agent Reasoning & Self-Correction (Full).**
2.  **Comprehensive Tool Ecosystem Expansion (Leveraging new "Plug and Play" system):**
    * **Rscript Execution Tool:** (Effort: ~6/10, Time Est.: ~8-12h)
    * **Data_Comparator:** Comparing datasets, files, or structured information. (Effort: ~5/10, Time Est.: ~6-10h)
    * **Data_Compiler:** Aggregating data from multiple sources into a unified format. (Effort: ~6/10, Time Est.: ~8-12h)
    * **Data_Filter:** Applying complex, user-defined filters to structured data. (Effort: ~5/10, Time Est.: ~6-10h)
    * **Data_Formatter:** Converting data between various structured formats. (Effort: ~4/10, Time Est.: ~4-8h)
    * **Domain_Analysis (e.g., InterProScan wrapper):** Specialized bioinformatics tool. (Effort: ~7/10, Time Est.: ~10-15h)
    * **Information_Extractor (schema-based):** Robust information extraction against a user-defined schema. (Effort: ~7/10, Time Est.: ~10-15h)
    * **Keyword_Extractor:** Dedicated tool for extracting relevant keywords/keyphrases. (Effort: ~4/10, Time Est.: ~4-6h)
    * **Knowledge_Lookup:** Querying a structured knowledge base. (Effort: ~6/10, Time Est.: ~8-12h)
    * **Report_Generator (general, structured):** More configurable and structured report generation. (Effort: ~8/10, Time Est.: ~12-20h)
    * **Sequence_Search (e.g., BLAST wrapper):** Specialized bioinformatics tool. (Effort: ~7/10, Time Est.: ~10-15h)
    * **Specialized_DB_Search (ClinVar, dbSNP, KEGG, etc.):** Wrappers for various bioinformatics databases. (Effort: ~7/10 per DB, Time Est.: ~10-15h per DB)
    * **Text_Summarizer (standalone):** General-purpose tool with more control. (Effort: ~4/10, Time Est.: ~4-8h)
    * **Text_Synthesizer (standalone):** General-purpose text synthesis tool. (Effort: ~5/10, Time Est.: ~6-10h)
    * Enhanced PDF Parsing.
    * Further tools for literature review, data analysis/visualization, specialized bioinformatics tasks, document preparation.
3.  **UI/UX & Workspace Enhancements:**
    * Integrated Folder Viewer (complex version of folder link/view).
    * Dedicated Steps Panel, etc.
4.  **Backend & Architecture (Scalability, Personas).**
5.  **Deployment & DevOps.**

## Known Good States / Checkpoints

-   **"Plug and Play" Tool System:** Core architecture implemented and stable. All 9 tools dynamically loaded via `tool_config.json` and operational (pending full verification of `deep_research_synthesizer` after Pydantic fix).
-   **Pydantic v2 Migration:** Largely complete for models in tools and agent components.
-   Token Counting: Working.
-   File Upload: Functional.
-   In-Chat Tool Feedback & Plan Proposal UI: Complete and refined.

## Open Questions / Areas for Investigation / Architectural Considerations

-   Robustness of `asyncio.Task.cancel()` for deep LLM/tool calls (STOP button issue).
-   Best practices for `JsonOutputParser` when `pydantic_object` is specified (handled, but good to keep in mind).
-   **New Tool Integration Process:** Documenting and streamlining the process for adding new tools now that the foundation is laid.
