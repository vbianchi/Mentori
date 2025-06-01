// js/ui_modules/token_usage_ui.js

/**
 * Manages the Token Usage Display UI.
 * - Updates the display for last call tokens and task total tokens (overall and per-role).
 * - Handles expand/collapse of the detailed view.
 * - Resets the display.
 */

// DOM Elements - these will be fetched by ID within initTokenUsageUI
let tokenUsageAreaElementUI;
let tokenUsageHeaderElementUI;
let taskTotalTokensOverallElementUI;
let tokenExpandBtnElementUI;
let tokenUsageDetailsElementUI;
let lastCallTokensElementUI;
let roleTokenBreakdownElementUI;

// Mapping for backend role_hints to display-friendly names
const ROLE_DISPLAY_NAMES = {
    "INTENT_CLASSIFIER": "Intent Classifier",
    "PLANNER": "Planner",
    "CONTROLLER": "Controller",
    "EXECUTOR": "Executor", // Covers agent execution steps
    "DIRECTQA_EXECUTOR": "Direct QA", // If we distinguish this specifically
    "EVALUATOR_STEP": "Step Evaluator",
    "EVALUATOR_OVERALL": "Overall Evaluator",
    "LLM_CORE": "LLM Core (General)", // Default for direct LLM calls not otherwise specified by component_name
    "TOOL_INTERNAL_LLM": "Tool (Internal LLM)", // Example if a tool makes its own LLM calls
    // Add more specific role hints if they are sent from the backend
};

/**
 * Gets a display-friendly name for a role hint.
 * @param {string} roleHint - The role hint from the backend (e.g., "PLANNER", "LLM_CORE").
 * @returns {string} - The display-friendly name.
 */
function getDisplayRoleName(roleHint) {
    if (!roleHint) return "Unknown Role";
    return ROLE_DISPLAY_NAMES[roleHint.toUpperCase()] || roleHint.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Initializes the Token Usage UI module.
 * @param {object} elements - (Currently unused, elements are fetched by ID)
 */
function initTokenUsageUI(elements) { // elements param kept for signature consistency if script.js passes it
    console.log("[TokenUsageUI] Initializing...");
    tokenUsageAreaElementUI = document.getElementById('token-usage-area');
    tokenUsageHeaderElementUI = document.getElementById('token-usage-header');
    taskTotalTokensOverallElementUI = document.getElementById('task-total-tokens-overall');
    tokenExpandBtnElementUI = document.getElementById('token-expand-btn');
    tokenUsageDetailsElementUI = document.getElementById('token-usage-details');
    lastCallTokensElementUI = document.getElementById('last-call-tokens');
    roleTokenBreakdownElementUI = document.getElementById('role-token-breakdown');

    if (!tokenUsageAreaElementUI || !tokenUsageHeaderElementUI || !taskTotalTokensOverallElementUI ||
        !tokenExpandBtnElementUI || !tokenUsageDetailsElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI) {
        console.error("[TokenUsageUI] One or more token usage UI elements not found in the DOM! Check IDs in index.html.");
        return;
    }

    // Event listener for expand/collapse
    tokenUsageHeaderElementUI.addEventListener('click', () => {
        const isHidden = tokenUsageDetailsElementUI.style.display === 'none';
        tokenUsageDetailsElementUI.style.display = isHidden ? 'block' : 'none';
        tokenExpandBtnElementUI.textContent = isHidden ? '[-]' : '[+]';
        tokenExpandBtnElementUI.title = isHidden ? 'Hide Details' : 'Show Details';
        console.log(`[TokenUsageUI] Token details toggled. Now ${isHidden ? 'visible' : 'hidden'}.`);
    });
    
    console.log("[TokenUsageUI] Initialized and event listener for expand/collapse set.");
    resetTokenDisplayUI(); // Initialize with default/empty values and collapsed state
}

/**
 * Updates the token display elements in the UI.
 * @param {object|null} lastCallUsage - Object from backend: { model_name, role_hint, input_tokens, output_tokens, total_tokens, source } or null.
 * @param {object} currentTaskTotals - Object from StateManager: { overall: {input, output, total}, roles: {"ROLE_HINT": {input, output, total}, ...} }.
 */
function updateTokenDisplayUI(lastCallUsage, currentTaskTotals) {
    console.log("[TokenUsageUI] updateTokenDisplayUI called. Last Call:", JSON.stringify(lastCallUsage), "Task Totals:", JSON.stringify(currentTaskTotals));
    if (!taskTotalTokensOverallElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI) {
        console.error("[TokenUsageUI] Token display elements not initialized for update.");
        return;
    }

    // Update Last Call section (inside the details div)
    if (lastCallUsage && lastCallUsage.model_name) {
        const roleName = getDisplayRoleName(lastCallUsage.role_hint);
        const modelName = (lastCallUsage.model_name || "Unknown Model").replace(/^(gemini::|ollama::)/, ''); // Clean up provider prefix
        const lastInput = lastCallUsage.input_tokens || 0;
        const lastOutput = lastCallUsage.output_tokens || 0;
        const lastTotal = lastCallUsage.total_tokens || (lastInput + lastOutput);
        lastCallTokensElementUI.textContent = `${roleName} - ${modelName}: In: ${lastInput}, Out: ${lastOutput}, Total: ${lastTotal}`;
    } else {
        lastCallTokensElementUI.textContent = "N/A";
    }

    // Update Overall Task Total in Header
    if (currentTaskTotals && currentTaskTotals.overall) {
        taskTotalTokensOverallElementUI.textContent = currentTaskTotals.overall.total || 0;
    } else {
        taskTotalTokensOverallElementUI.textContent = "0";
    }

    // Update Per-Role Breakdown (inside the details div)
    roleTokenBreakdownElementUI.innerHTML = ''; // Clear previous breakdown
    if (currentTaskTotals && currentTaskTotals.roles && Object.keys(currentTaskTotals.roles).length > 0) {
        const sortedRoleKeys = Object.keys(currentTaskTotals.roles).sort(); 

        sortedRoleKeys.forEach(roleKey => {
            const roleData = currentTaskTotals.roles[roleKey];
            const roleDisplayName = getDisplayRoleName(roleKey);

            const roleP = document.createElement('p');
            roleP.className = 'role-token-entry'; // For potential specific styling

            const roleLabelSpan = document.createElement('span');
            roleLabelSpan.className = 'token-label-role';
            roleLabelSpan.textContent = `${roleDisplayName}:`;
            roleP.appendChild(roleLabelSpan);

            // Container for In/Out/Total to allow better layout (e.g., table-like)
            const valuesDiv = document.createElement('div');
            valuesDiv.className = 'role-token-values';

            const inP = document.createElement('span');
            inP.className = 'token-value-item';
            inP.innerHTML = `<span class="token-sublabel">In:</span> ${roleData.input || 0}`;
            valuesDiv.appendChild(inP);

            const outP = document.createElement('span');
            outP.className = 'token-value-item';
            outP.innerHTML = `<span class="token-sublabel">Out:</span> ${roleData.output || 0}`;
            valuesDiv.appendChild(outP);
            
            const totalP = document.createElement('span');
            totalP.className = 'token-value-item total';
            totalP.innerHTML = `<span class="token-sublabel">Total:</span> ${roleData.total || 0}`;
            valuesDiv.appendChild(totalP);

            roleP.appendChild(valuesDiv);
            roleTokenBreakdownElementUI.appendChild(roleP);
        });
    } else {
         const noRolesP = document.createElement('p');
         noRolesP.textContent = "No specific role usage tracked yet for this task.";
         noRolesP.style.fontStyle = "italic";
         roleTokenBreakdownElementUI.appendChild(noRolesP);
    }
}

/**
 * Resets the token display elements to their initial state and collapses details.
 */
function resetTokenDisplayUI() {
    if (!taskTotalTokensOverallElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI || !tokenUsageDetailsElementUI || !tokenExpandBtnElementUI) {
        console.warn("[TokenUsageUI] Token display elements not fully initialized for reset, or called too early.");
        return;
    }
    lastCallTokensElementUI.textContent = "N/A";
    taskTotalTokensOverallElementUI.textContent = "0";
    roleTokenBreakdownElementUI.innerHTML = '<p style="font-style: italic;">No specific role usage tracked yet.</p>';
    
    tokenUsageDetailsElementUI.style.display = 'none';
    tokenExpandBtnElementUI.textContent = '[+]';
    tokenExpandBtnElementUI.title = 'Show Details';
    console.log("[TokenUsageUI] Display reset and details collapsed.");
}
