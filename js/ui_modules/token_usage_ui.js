// js/ui_modules/token_usage_ui.js

/**
 * Manages the Token Usage Display UI.
 * - Updates the display for last call tokens and task total tokens (overall and per-role).
 * - Handles expand/collapse of the detailed view.
 * - Resets the display.
 */

// DOM Elements
let tokenUsageAreaElementUI; // The main container
let tokenUsageHeaderElementUI; // Clickable header
let taskTotalTokensOverallElementUI; // Span for overall total in header
let tokenExpandBtnElementUI; // Span for [+] / [-]
let tokenUsageDetailsElementUI; // Div for detailed content (Last Call + Roles)
let lastCallTokensElementUI; // Span for "Last Call" info
let roleTokenBreakdownElementUI; // Div to hold per-role paragraphs

// Mapping for backend role_hints to display-friendly names
const ROLE_DISPLAY_NAMES = {
    "INTENT_CLASSIFIER": "Intent Classifier",
    "PLANNER": "Planner",
    "CONTROLLER": "Controller",
    "EXECUTOR": "Executor",
    "DIRECTQA_EXECUTOR": "Direct QA", // Assuming this might be a role_hint
    "EVALUATOR_STEP": "Step Evaluator",
    "EVALUATOR_OVERALL": "Overall Evaluator",
    "LLM_CORE": "LLM Core (Agent/Tool)", // Default for direct LLM calls not otherwise specified
    "TOOL_INTERNAL_LLM": "Tool (Internal LLM)", // If a tool itself makes an LLM call and we can tag it
    // Add more mappings as needed
};

function getDisplayRoleName(roleHint) {
    return ROLE_DISPLAY_NAMES[roleHint] || roleHint.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Default formatting
}


/**
 * Initializes the Token Usage UI module.
 * @param {object} elements - DOM elements from script.js
 */
function initTokenUsageUI(elements) {
    console.log("[TokenUsageUI] Initializing...");
    // Get references to all necessary elements based on the new HTML structure
    tokenUsageAreaElementUI = document.getElementById('token-usage-area');
    tokenUsageHeaderElementUI = document.getElementById('token-usage-header');
    taskTotalTokensOverallElementUI = document.getElementById('task-total-tokens-overall');
    tokenExpandBtnElementUI = document.getElementById('token-expand-btn');
    tokenUsageDetailsElementUI = document.getElementById('token-usage-details');
    lastCallTokensElementUI = document.getElementById('last-call-tokens'); // This is inside token-usage-details
    roleTokenBreakdownElementUI = document.getElementById('role-token-breakdown'); // This is inside token-usage-details

    if (!tokenUsageAreaElementUI || !tokenUsageHeaderElementUI || !taskTotalTokensOverallElementUI ||
        !tokenExpandBtnElementUI || !tokenUsageDetailsElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI) {
        console.error("[TokenUsageUI] One or more token usage UI elements not found in the DOM!");
        return;
    }

    // Event listener for expand/collapse
    if (tokenUsageHeaderElementUI && tokenExpandBtnElementUI && tokenUsageDetailsElementUI) {
        tokenUsageHeaderElementUI.addEventListener('click', () => {
            const isHidden = tokenUsageDetailsElementUI.style.display === 'none';
            tokenUsageDetailsElementUI.style.display = isHidden ? 'block' : 'none';
            tokenExpandBtnElementUI.textContent = isHidden ? '[-]' : '[+]';
            tokenExpandBtnElementUI.title = isHidden ? 'Hide Details' : 'Show Details';
        });
    }
    
    console.log("[TokenUsageUI] Initialized.");
    resetTokenDisplayUI(); // Initialize with default/empty values
}

/**
 * Updates the token display elements in the UI.
 * @param {object|null} lastCallUsage - Object from backend: { model_name, role_hint, input_tokens, output_tokens, total_tokens, source } or null.
 * @param {object} currentTaskTotals - Object from StateManager: { overall: {input, output, total}, roles: {"ROLE": {input, output, total}, ...} }.
 */
function updateTokenDisplayUI(lastCallUsage, currentTaskTotals) {
    console.log("[TokenUsageUI] updateTokenDisplayUI called. Last Call:", JSON.stringify(lastCallUsage), "Task Totals:", JSON.stringify(currentTaskTotals));
    if (!taskTotalTokensOverallElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI) {
        console.error("[TokenUsageUI] Token display elements not initialized for update.");
        return;
    }

    // Update Last Call
    if (lastCallUsage && lastCallUsage.model_name) {
        const roleName = getDisplayRoleName(lastCallUsage.role_hint || 'LLM_CORE');
        const modelName = lastCallUsage.model_name.replace('gemini::', '').replace('ollama::', ''); // Clean up model name
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

    // Update Per-Role Breakdown
    roleTokenBreakdownElementUI.innerHTML = ''; // Clear previous breakdown
    if (currentTaskTotals && currentTaskTotals.roles) {
        const sortedRoles = Object.keys(currentTaskTotals.roles).sort(); // Sort roles alphabetically for consistent order

        if (sortedRoles.length === 0) {
            const noRolesP = document.createElement('p');
            noRolesP.textContent = "No specific role usage tracked yet.";
            noRolesP.style.fontStyle = "italic";
            roleTokenBreakdownElementUI.appendChild(noRolesP);
        } else {
            sortedRoles.forEach(roleKey => {
                const roleData = currentTaskTotals.roles[roleKey];
                const p = document.createElement('p');
                
                const labelSpan = document.createElement('span');
                labelSpan.className = 'token-label-role';
                labelSpan.textContent = `${getDisplayRoleName(roleKey)}:`;
                p.appendChild(labelSpan);

                const valueSpan = document.createElement('span');
                valueSpan.className = 'token-value-role';
                valueSpan.textContent = ` In: ${roleData.input || 0}, Out: ${roleData.output || 0}, Total: ${roleData.total || 0}`;
                p.appendChild(valueSpan);
                
                roleTokenBreakdownElementUI.appendChild(p);
            });
        }
    } else {
         const noRolesP = document.createElement('p');
         noRolesP.textContent = "Role breakdown not available.";
         noRolesP.style.fontStyle = "italic";
         roleTokenBreakdownElementUI.appendChild(noRolesP);
    }
}

/**
 * Resets the token display elements to their initial state.
 */
function resetTokenDisplayUI() {
    if (!taskTotalTokensOverallElementUI || !lastCallTokensElementUI || !roleTokenBreakdownElementUI || !tokenUsageDetailsElementUI || !tokenExpandBtnElementUI) {
        console.warn("[TokenUsageUI] Token display elements not fully initialized for reset, or called too early.");
        return;
    }
    lastCallTokensElementUI.textContent = "N/A";
    taskTotalTokensOverallElementUI.textContent = "0";
    roleTokenBreakdownElementUI.innerHTML = '<p style="font-style: italic;">No specific role usage tracked yet.</p>';
    
    // Collapse details view
    tokenUsageDetailsElementUI.style.display = 'none';
    tokenExpandBtnElementUI.textContent = '[+]';
    tokenExpandBtnElementUI.title = 'Show Details';
    console.log("[TokenUsageUI] Display reset and details collapsed.");
}

