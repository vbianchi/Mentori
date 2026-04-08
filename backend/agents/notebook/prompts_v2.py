"""
Prompts for Notebook Coder V2.

Design principle: Each prompt is SHORT and focused on ONE task.
Complexity is in code orchestration, not prompts.
"""

# =============================================================================
# PHASE 0: REQUEST ANALYSIS
# =============================================================================

ANALYSIS_PROMPT = """Analyze this user request for a Jupyter notebook coding task.

**User Request**: {user_request}

**Current Notebook**: {notebook_summary}

**Previous Work** (from memory):
{memory_context}

**Cell Registry** (cells created in previous sessions):
{cell_registry_summary}

Classify the request:

1. **TRIVIAL**: Re-running or minor tweaks to EXISTING cells only
   - "Run cell 3 again"
   - "Re-execute the last cell"
   - "Show me the first 10 rows" (if dataframe already exists)
   TRIVIAL requires existing cells/variables. If notebook is empty, it's NOT trivial.

2. **MODIFY**: User wants to change an EXISTING cell's code
   - "Change the clustering algorithm to ward"
   - "Use a different color scheme for the heatmap"
   - "Update the threshold to 0.5"
   MODIFY requires existing cells in the registry. If no cells exist, it's COMPLEX.

3. **COMPLEX**: Creating NEW code, data, or visualizations
   - "Create 100 random numbers" -> COMPLEX (creating new data)
   - "Load the data and create a visualization" -> COMPLEX
   - "Perform correlation analysis" -> COMPLEX
   - "Build a prediction model" -> COMPLEX
   - "Plot a scatter chart" -> COMPLEX (unless modifying existing plot)
   ANY request that requires generating new code is COMPLEX.

4. **CLARIFICATION**: Request is too ambiguous
   - "Analyze the data" (which data? what analysis?)
   - "Make it better" (what specifically?)

IMPORTANT: If the notebook is empty or has no relevant cells, classification must be COMPLEX, not TRIVIAL.

Return JSON:
```json
{{
    "classification": "trivial|modify|complex|clarification",
    "detected_intent": "brief description of what user wants",
    "relevant_cells": ["cell_id1", "cell_id2"],
    "modification_target": "cell_id if classification is modify",
    "clarification_question": "question to ask if classification is clarification"
}}
```"""


# =============================================================================
# PHASE 1: ALGORITHM GENERATION
# =============================================================================

ALGORITHM_PROMPT = """Create a step-by-step algorithm for this Jupyter notebook task.

**User Request**: {user_request}

**Current Notebook State**:
{notebook_state}

**Kernel Variables Available**:
{kernel_state}

**Previous Work in This Task**:
{memory_context}

Create an algorithm where EACH STEP has a CONCRETE expected output that can be verified.

Return JSON:
```json
{{
    "task_summary": "One sentence describing the overall goal",
    "prerequisites": ["required files, variables, or conditions"],
    "steps": [
        {{
            "step_number": 1,
            "description": "What to do in this step",
            "expected_output": "SPECIFIC verifiable result (e.g., 'DataFrame displayed with shape shown')",
            "validation_criteria": ["criterion 1", "criterion 2"],
            "cell_type": "code",
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    "expected_final_output": "What the completed task should produce (files, visualizations, etc.)"
}}
```

**RULES**:
1. Each step = ONE logical operation (typically 5-15 lines of code)
2. `expected_output` must be SPECIFIC and VERIFIABLE - avoid vague terms like "data processed"
3. Include data exploration/validation steps before complex operations
4. For visualizations, specify what should be visible (axes, title, data patterns)
5. `keywords` should include: libraries used, plot types, analysis methods, variable names
6. Keep it practical - 3-7 steps for most tasks"""


# =============================================================================
# PHASE 2: STEP EXECUTION
# =============================================================================

STEP_EXECUTION_PROMPT = """Implement this step in the Jupyter notebook.

## TASK OVERVIEW
{algorithm_context}

## WORKSPACE FILES
{environment_context}

## CURRENT STEP: {step_number} of {total_steps}
**Description**: {description}
**Expected Output**: {expected_output}

**Validation Criteria**:
{validation_criteria}

## ALREADY COMPLETED (in kernel memory)
{previous_steps_summary}

## CURRENT KERNEL STATE
Variables available (DO NOT recreate these):
{kernel_state}

{api_scratchpad_section}{retry_section}

## CRITICAL RULES
1. **ALWAYS create exactly ONE cell for THIS step** - every step MUST have its own cell
2. DO NOT re-import libraries that were imported in previous steps
3. DO NOT recreate variables/data that already exist in the kernel
4. REUSE existing DataFrames, arrays, and variables from previous cells
5. Only add NEW code specific to THIS step's requirements
6. The kernel has already executed all previous cells - their variables are available
7. DO NOT combine multiple algorithm steps into one cell - each step = one cell

## YOUR TASK
Write code for THIS step only ({description}). Your code should:
- Use variables already defined in the kernel (listed above)
- Only import NEW libraries not yet imported
- Focus ONLY on this step's specific task
- Be concise - do NOT repeat work from previous cells

Available tools:
- `add_cell(source, cell_type)` - Add a new cell ("code" or "markdown")
- `execute_cell(cell_id)` - Execute a cell and get output
- `edit_cell(cell_id, source)` - Modify an existing cell

**IMPORTANT**: You MUST call `add_cell` and then `execute_cell` for this step. Every step needs its own cell."""


STEP_EXECUTION_RETRY_SECTION = """
**RETRY ATTEMPT {attempt}**
Previous attempt failed. Error:
{feedback}

{recovery_hint}
Fix the issues and try again. You may edit the existing cell or create a new one."""


# =============================================================================
# PHASE 2.5: CELL EVALUATION
# =============================================================================

CELL_EVALUATION_PROMPT = """Evaluate if this cell output matches the expected outcome.

**Expected Output**: {expected_output}

**Validation Criteria**:
{validation_criteria}

**Actual Cell Source**:
```python
{cell_source}
```

**Actual Cell Output**:
```
{cell_output}
```

**Cell Errors** (if any):
{cell_errors}

Compare the actual output against what was expected.

Return JSON:
```json
{{
    "score": 0-100,
    "meets_expectations": true or false,
    "should_retry": true or false,
    "feedback": "Specific actionable feedback if retry needed",
    "matched_criteria": ["criteria that were satisfied"],
    "missing_criteria": ["criteria that were NOT satisfied"],
    "issues": ["specific problems found"]
}}
```

**Scoring Guide**:
- 90-100: Output exceeds expectations, all criteria met
- 70-89: Output meets expectations, most criteria met
- 50-69: Output partially meets expectations (acceptable but not ideal)
- 30-49: Output has significant issues (retry recommended)
- 0-29: Output fails completely (retry required)

**Important**:
- An empty output when data/visualization was expected = score 0-30
- Errors/exceptions = score 0-20 unless the error message itself was the expected output
- Be specific in feedback - what exactly needs to change?"""


CELL_EVALUATION_VISION_PROMPT = """Evaluate this visualization output.

**Expected Visualization**: {expected_output}

**Validation Criteria**:
{validation_criteria}

Look at the image and verify:
1. Is there actual data displayed (not a blank/empty plot)?
2. Are axes labeled appropriately?
3. Is there a title or legend if expected?
4. Does the visualization type match what was expected (heatmap, scatter, line, etc.)?
5. Is the data pattern/content visible and interpretable?

Return JSON:
```json
{{
    "has_data": true or false,
    "visualization_type": "detected type (heatmap, scatter, line, bar, etc.)",
    "has_labels": true or false,
    "has_title": true or false,
    "visual_quality": "good|acceptable|poor",
    "matches_expected": true or false,
    "issues": ["any visual problems detected"],
    "score": 0-100
}}
```"""


# =============================================================================
# =============================================================================
# MODIFICATION REQUEST
# =============================================================================

MODIFICATION_PROMPT = """Modify an existing notebook cell.

**User Request**: {user_request}

**Target Cell** ({cell_id}):
```python
{cell_source}
```

**Cell Purpose**: {cell_purpose}

**Current Output**:
{cell_output}

**Kernel Variables Available**:
{kernel_state}

Modify the cell to address the user's request:
1. Use `edit_cell(cell_id, new_source)` to update the code
2. Use `execute_cell(cell_id)` to run the updated code
3. Verify the output matches expectations

Keep changes minimal - only modify what's needed to address the request."""


# =============================================================================
# HELPER: BUILD CONTEXT STRINGS
# =============================================================================

def build_notebook_summary(notebook_state: dict) -> str:
    """Build concise notebook summary for prompts."""
    if not notebook_state:
        return "Empty notebook"

    cells = notebook_state.get("cells_summary", [])
    if not cells:
        return "Empty notebook"

    lines = [f"Notebook: {notebook_state.get('notebook_name', 'Untitled')} ({len(cells)} cells)"]

    for cell in cells[:10]:  # Limit to first 10 cells
        cell_type = cell.get("cell_type", "code")
        status = cell.get("status", "idle")
        status_icon = {"success": "✅", "error": "❌", "running": "🔄"}.get(status, "⚪")
        source_preview = cell.get("source", "")[:60].replace("\n", " ")
        cell_id = cell.get("id", "?")[:8]

        lines.append(f"  {status_icon} [{cell_id}] {cell_type}: {source_preview}...")

    if len(cells) > 10:
        lines.append(f"  ... and {len(cells) - 10} more cells")

    return "\n".join(lines)


def build_kernel_state_summary(kernel_state: dict) -> str:
    """Build concise kernel state summary for prompts."""
    if not kernel_state:
        return "No variables in kernel"

    variables = kernel_state.get("variables", [])
    if not variables:
        return "No variables in kernel"

    # Group by type
    dataframes = []
    arrays = []
    others = []

    for var in variables:
        name = var.get("name", "?")
        var_type = var.get("type", "unknown")
        shape = var.get("shape", "")

        if "DataFrame" in var_type:
            shape_str = f" {shape}" if shape else ""
            dataframes.append(f"{name}{shape_str}")
        elif "array" in var_type.lower() or "ndarray" in var_type:
            shape_str = f" {shape}" if shape else ""
            arrays.append(f"{name}{shape_str}")
        else:
            others.append(f"{name}: {var_type}")

    lines = []
    if dataframes:
        lines.append(f"DataFrames: {', '.join(dataframes[:5])}")
    if arrays:
        lines.append(f"Arrays: {', '.join(arrays[:5])}")
    if others:
        lines.append(f"Other: {', '.join(others[:5])}")

    return "\n".join(lines) if lines else "No significant variables"


def build_validation_criteria_string(criteria: list) -> str:
    """Format validation criteria as bullet list."""
    if not criteria:
        return "- Output should match expected result"

    return "\n".join(f"- {c}" for c in criteria)


def build_algorithm_context(algorithm: dict, current_step: int) -> str:
    """
    Build algorithm context string showing the full task and progress.

    This gives the agent visibility into:
    - What the overall task is
    - What all the steps are
    - Where we are in the process
    """
    if not algorithm:
        return "No algorithm defined"

    task_summary = algorithm.get("task_summary", "Complete the task")
    steps = algorithm.get("steps", [])
    final_output = algorithm.get("expected_final_output", "")

    lines = [
        f"**Goal**: {task_summary}",
        "",
        "**Algorithm Steps**:",
    ]

    for step in steps:
        step_num = step.get("step_number", 0)
        desc = step.get("description", "")

        # Mark completed, current, and pending steps
        if step_num < current_step:
            status = "✅ DONE"
        elif step_num == current_step:
            status = "👉 CURRENT"
        else:
            status = "⏳ pending"

        lines.append(f"  {step_num}. [{status}] {desc}")

    if final_output:
        lines.append("")
        lines.append(f"**Final Expected Output**: {final_output}")

    return "\n".join(lines)


def build_previous_steps_with_code(step_results: list) -> str:
    """
    Build detailed summary of previous step results INCLUDING actual code.

    This ensures the agent knows exactly what code has been executed
    and can avoid duplicating work.
    """
    if not step_results:
        return "No previous steps executed yet. This is the first step."

    lines = ["The following code has already been executed in the kernel:\n"]

    for i, result in enumerate(step_results):
        if not result:
            continue

        success = result.success if hasattr(result, 'success') else result.get('success', False)
        status = "✅" if success else "❌"

        lines.append(f"### Step {i + 1} {status}")

        # Include the actual cell source code
        cells_created = result.cells_created if hasattr(result, 'cells_created') else result.get('cells_created', [])
        for cell in cells_created:
            source = cell.source if hasattr(cell, 'source') else cell.get('source', '')
            cell_type = cell.cell_type if hasattr(cell, 'cell_type') else cell.get('cell_type', 'code')

            if cell_type == "code" and source:
                # Truncate very long cells but show enough for context
                if len(source) > 600:
                    source = source[:600] + "\n# ... (truncated)"
                lines.append(f"```python\n{source}\n```")

        # Show variables created
        vars_created = result.variables_created if hasattr(result, 'variables_created') else result.get('variables_created', [])
        if vars_created:
            lines.append(f"**Variables created**: {', '.join(vars_created)}")

        # Show files created
        files_created = result.files_created if hasattr(result, 'files_created') else result.get('files_created', [])
        if files_created:
            lines.append(f"**Files created**: {', '.join(files_created)}")

        lines.append("")  # Blank line between steps

    return "\n".join(lines)
