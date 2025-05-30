// js/ui_modules/llm_selector_ui.js

/**
 * Manages the LLM Selector UI elements.
 * - Populates Executor LLM and Role-Specific LLM dropdowns.
 * - Handles change events on these selectors.
 * - Interacts with localStorage for persistence of selections.
 */

// DOM Elements (will be passed during initialization)
let executorLlmSelectElementUI;
let roleSelectorsMetaUI = []; // Array of { element, role, storageKey, label }

// Callbacks to be set by the main script
let onExecutorLlmChangeCallback = (selectedId) => console.warn("onExecutorLlmChangeCallback not set in llm_selector_ui.js");
let onRoleLlmChangeCallback = (role, selectedId) => console.warn("onRoleLlmChangeCallback not set in llm_selector_ui.js");

/**
 * Initializes the LLM Selector UI module.
 * @param {object} elements - Object containing DOM elements { executorLlmSelect, roleSelectors }
 * @param {object} callbacks - Object containing callback functions { onExecutorLlmChange, onRoleLlmChange }
 */
function initLlmSelectorsUI(elements, callbacks) {
    console.log("[LlmSelectorUI] Initializing...");
    executorLlmSelectElementUI = elements.executorLlmSelect;
    roleSelectorsMetaUI = elements.roleSelectors; // Expects the full array with element, role, storageKey

    if (!executorLlmSelectElementUI) console.error("[LlmSelectorUI] Executor LLM select element not provided!");
    if (!roleSelectorsMetaUI || roleSelectorsMetaUI.length === 0) console.warn("[LlmSelectorUI] Role selectors meta array not provided or empty.");

    onExecutorLlmChangeCallback = callbacks.onExecutorLlmChange;
    onRoleLlmChangeCallback = callbacks.onRoleLlmChange;

    // Setup event listeners
    if (executorLlmSelectElementUI) {
        executorLlmSelectElementUI.addEventListener('change', (event) => {
            const selectedId = event.target.value;
            localStorage.setItem('selectedExecutorLlmId', selectedId); // Persist selection
            onExecutorLlmChangeCallback(selectedId);
        });
    }

    roleSelectorsMetaUI.forEach(selInfo => {
        if (selInfo.element) {
            selInfo.element.addEventListener('change', (event) => {
                const selectedLlmId = event.target.value;
                localStorage.setItem(selInfo.storageKey, selectedLlmId); // Persist selection
                onRoleLlmChangeCallback(selInfo.role, selectedLlmId);
            });
        } else {
            console.error(`[LlmSelectorUI] Element for role ${selInfo.role} is missing in roleSelectorsMetaUI.`);
        }
    });
    console.log("[LlmSelectorUI] Initialized.");
}

/**
 * Populates a single LLM selector dropdown.
 * @param {HTMLSelectElement} selectElement - The <select> element to populate.
 * @param {object} availableModelsData - Object like { gemini: [], ollama: [] }.
 * @param {string} currentSelectedValue - The value that should be pre-selected.
 * @param {string} defaultOptionText - Text for the default/empty option.
 * @param {string|null} backendConfiguredDefaultLlmId - The default LLM ID configured on the backend for this selector.
 */
function populateSingleLlmSelectorUI(selectElement, availableModelsData, currentSelectedValue, defaultOptionText = "Use System Default", backendConfiguredDefaultLlmId = null) {
    if (!selectElement) {
        console.error("[LlmSelectorUI] populateSingleLlmSelectorUI: selectElement is null for text:", defaultOptionText);
        return;
    }
    selectElement.innerHTML = ''; // Clear existing options

    const defaultOpt = document.createElement('option');
    defaultOpt.value = ""; // Empty value for "Use System Default"
    defaultOpt.textContent = defaultOptionText;
    selectElement.appendChild(defaultOpt);

    if ((!availableModelsData.gemini || availableModelsData.gemini.length === 0) &&
        (!availableModelsData.ollama || availableModelsData.ollama.length === 0)) {
        const noModelsOpt = document.createElement('option');
        noModelsOpt.value = ""; // Keep value empty
        noModelsOpt.textContent = "No LLMs Available";
        noModelsOpt.disabled = true;
        // If defaultOpt is the only one, update it instead of adding another disabled one
        if (selectElement.options.length === 1 && selectElement.options[0].value === "") {
             selectElement.options[0].textContent = "No LLMs Available";
             selectElement.options[0].disabled = true;
        } else {
            selectElement.appendChild(noModelsOpt);
        }
        selectElement.disabled = true;
        return;
    }

    if (availableModelsData.gemini && availableModelsData.gemini.length > 0) {
        const geminiGroup = document.createElement('optgroup');
        geminiGroup.label = 'Gemini';
        availableModelsData.gemini.forEach(modelId => {
            const option = document.createElement('option');
            option.value = `gemini::${modelId}`;
            option.textContent = modelId;
            geminiGroup.appendChild(option);
        });
        selectElement.appendChild(geminiGroup);
    }

    if (availableModelsData.ollama && availableModelsData.ollama.length > 0) {
        const ollamaGroup = document.createElement('optgroup');
        ollamaGroup.label = 'Ollama';
        availableModelsData.ollama.forEach(modelId => {
            const option = document.createElement('option');
            option.value = `ollama::${modelId}`;
            option.textContent = modelId;
            ollamaGroup.appendChild(option);
        });
        selectElement.appendChild(ollamaGroup);
    }

    // Determine the actual value to set
    let valueToSet = ""; // Default to "Use System Default"
    // Priority: 1. currentSelectedValue (from localStorage or state), 2. backendConfiguredDefaultLlmId
    if (currentSelectedValue && selectElement.querySelector(`option[value="${currentSelectedValue}"]`)) {
        valueToSet = currentSelectedValue;
    } else if (backendConfiguredDefaultLlmId && selectElement.querySelector(`option[value="${backendConfiguredDefaultLlmId}"]`)) {
        // This case is mostly for initial load if localStorage is empty.
        // If currentSelectedValue was explicitly "", it means user selected "Use System Default", so don't override.
        if (currentSelectedValue === null || typeof currentSelectedValue === 'undefined') { // Only if currentSelectedValue wasn't set
             valueToSet = backendConfiguredDefaultLlmId;
        }
    }
    selectElement.value = valueToSet;
    selectElement.disabled = false;
}

/**
 * Populates all LLM selector dropdowns.
 * Called from script.js when 'available_models' message is received.
 * @param {object} availableModelsData - From backend: { gemini: [], ollama: [] }
 * @param {string|null} backendDefaultExecutorLlmId - Default Executor LLM from backend config.
 * @param {object} backendRoleDefaults - Defaults for roles from backend config, e.g., { planner: "gemini::model-x" }
 */
function populateAllLlmSelectorsUI(availableModelsData, backendDefaultExecutorLlmId, backendRoleDefaults = {}) {
    if (!executorLlmSelectElementUI) {
        console.error("[LlmSelectorUI] Cannot populate: Executor LLM select element not initialized.");
        return;
    }
    console.log("[LlmSelectorUI] Populating all LLM selectors. Backend default executor:", backendDefaultExecutorLlmId);

    // Executor LLM
    const lastSelectedExecutor = localStorage.getItem('selectedExecutorLlmId');
    // If localStorage has a value (even empty string for "Use System Default"), use it. Otherwise, use backend default.
    const initialExecutorValue = lastSelectedExecutor !== null ? lastSelectedExecutor : backendDefaultExecutorLlmId;
    populateSingleLlmSelectorUI(executorLlmSelectElementUI, availableModelsData, initialExecutorValue, "Use System Default (Executor)", backendDefaultExecutorLlmId);
    // Notify main script of the initial effective value (could be from localStorage or backend default)
    onExecutorLlmChangeCallback(executorLlmSelectElementUI.value);


    // Role-Specific LLMs
    roleSelectorsMetaUI.forEach(selInfo => {
        if (selInfo.element) {
            const lastSelectedRoleOverride = localStorage.getItem(selInfo.storageKey);
            const backendRoleDefaultFromServer = backendRoleDefaults[selInfo.role] || ""; // Default from backend for this role

            // If localStorage has a value (even empty string for "Use System Default"), use it.
            // Otherwise, use the backend's default for that role.
            const initialRoleValue = lastSelectedRoleOverride !== null ? lastSelectedRoleOverride : backendRoleDefaultFromServer;

            populateSingleLlmSelectorUI(selInfo.element, availableModelsData, initialRoleValue, "Use System Default", backendRoleDefaultFromServer);
            // Notify main script of the initial effective value for this role
            onRoleLlmChangeCallback(selInfo.role, selInfo.element.value);
        } else {
            console.error(`[LlmSelectorUI] Element for role ${selInfo.role} is missing during populateAll.`);
        }
    });
    console.log("[LlmSelectorUI] All LLM selectors populated.");
}

/**
 * Disables all LLM selector dropdowns, typically on connection error.
 */
function disableAllLlmSelectorsUI() {
    console.log("[LlmSelectorUI] Disabling all LLM selectors.");
    if (executorLlmSelectElementUI) {
        executorLlmSelectElementUI.innerHTML = '<option value="">Connection Error</option>';
        executorLlmSelectElementUI.disabled = true;
    }
    roleSelectorsMetaUI.forEach(selInfo => {
        if (selInfo.element) {
            selInfo.element.innerHTML = '<option value="">Connection Error</option>';
            selInfo.element.disabled = true;
        }
    });
}
