// js/ui_modules/token_usage_ui.js

/**
 * Manages the Token Usage Display UI.
 * - Updates the display for last call tokens and task total tokens.
 * - Resets the display.
 */

let lastCallTokensElementUI;
let taskTotalTokensElementUI;

/**
 * Initializes the Token Usage UI module.
 * @param {object} elements - DOM elements { lastCallTokensEl, taskTotalTokensEl }
 */
function initTokenUsageUI(elements) {
    console.log("[TokenUsageUI] Initializing...");
    lastCallTokensElementUI = elements.lastCallTokensEl;
    taskTotalTokensElementUI = elements.taskTotalTokensEl;

    if (!lastCallTokensElementUI) console.error("[TokenUsageUI] Last call tokens element not provided!");
    if (!taskTotalTokensElementUI) console.error("[TokenUsageUI] Task total tokens element not provided!");
    
    console.log("[TokenUsageUI] Initialized.");
}

/**
 * Updates the token display elements in the UI.
 * Called by script.js after the main state for tokens has been updated.
 * @param {object|null} lastCallUsage - Object with { input_tokens, output_tokens, total_tokens, model_name } or null.
 * @param {object} currentTaskTotals - Object with { input, output, total } for the current task.
 */
// <<< START MODIFICATION - Phase 2, Action 2.4 >>>
function updateTokenDisplayUI(lastCallUsage, currentTaskTotals) {
    console.log("[TokenUsageUI] updateTokenDisplayUI called. Last Call:", JSON.stringify(lastCallUsage), "Task Totals:", JSON.stringify(currentTaskTotals));
    if (!lastCallTokensElementUI || !taskTotalTokensElementUI) {
        console.error("[TokenUsageUI] Token display elements not initialized for update.");
        return;
    }

    if (lastCallUsage) {
        const lastInput = lastCallUsage.input_tokens || 0;
        const lastOutput = lastCallUsage.output_tokens || 0;
        const lastTotal = lastCallUsage.total_tokens || (lastInput + lastOutput);
        lastCallTokensElementUI.textContent = `In: ${lastInput}, Out: ${lastOutput}, Total: ${lastTotal} (${lastCallUsage.model_name || 'N/A'})`;
    }
    taskTotalTokensElementUI.textContent = `In: ${currentTaskTotals.input}, Out: ${currentTaskTotals.output}, Total: ${currentTaskTotals.total}`;
}
// <<< END MODIFICATION >>>

/**
 * Resets the token display elements to their initial state.
 * Called by script.js after the main state for tokens has been reset.
 */
function resetTokenDisplayUI() {
    if (!lastCallTokensElementUI || !taskTotalTokensElementUI) {
        console.error("[TokenUsageUI] Token display elements not initialized for reset.");
        return;
    }
    lastCallTokensElementUI.textContent = "N/A";
    taskTotalTokensElementUI.textContent = `In: 0, Out: 0, Total: 0`;
}