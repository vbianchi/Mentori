// js/state_manager.js

/**
 * Manages the client-side application state.
 * Provides getters and setters for various parts of the state.
 * Handles persistence of relevant state to localStorage.
 */

const STORAGE_KEY_TASKS = 'aiAgentTasks';
const STORAGE_KEY_TASK_COUNTER = 'aiAgentTaskCounter';
const STORAGE_KEY_ACTIVE_TASK_ID = 'aiAgentTasks_active';
const STORAGE_KEY_EXECUTOR_LLM = 'selectedExecutorLlmId';
const STORAGE_KEY_ROLE_LLM_PREFIX = 'session'; // e.g., sessionIntentLlmId

// Internal state object
const _state = {
    tasks: [],
    currentTaskId: null,
    taskCounter: 0,
    availableModels: { gemini: [], ollama: [] }, // Populated from backend
    currentExecutorLlmId: "", // Effective current executor LLM ID (after considering localStorage)
    sessionRoleLlmOverrides: { // Effective overrides (after considering localStorage)
        intent_classifier: "", 
        planner: "", 
        controller: "", 
        evaluator: "" 
    },
    isAgentRunning: false,
    currentTaskArtifacts: [],
    currentArtifactIndex: -1,
    currentTaskTotalTokens: { input: 0, output: 0, total: 0 },
    currentDisplayedPlan: null, // Holds the structured plan for confirmation
    currentPlanProposalId: null, // ADDED: Holds the ID of the current plan proposal
};

// --- Private Helper Functions for localStorage ---
function _loadTasksFromLocalStorage() {
    const storedTasks = localStorage.getItem(STORAGE_KEY_TASKS);
    if (storedTasks) {
        try {
            const parsedTasks = JSON.parse(storedTasks);
            if (Array.isArray(parsedTasks)) {
                return parsedTasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            }
        } catch (e) {
            console.error("[StateManager] Failed to parse tasks from localStorage:", e);
            localStorage.removeItem(STORAGE_KEY_TASKS);
        }
    }
    return [];
}

function _saveTasksToLocalStorage() {
    try {
        _state.tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        localStorage.setItem(STORAGE_KEY_TASKS, JSON.stringify(_state.tasks));
    } catch (e) {
        console.error("[StateManager] Failed to save tasks to localStorage:", e);
    }
}

function _loadTaskCounterFromLocalStorage() {
    const storedCounter = localStorage.getItem(STORAGE_KEY_TASK_COUNTER);
    const counter = storedCounter ? parseInt(storedCounter, 10) : 0;
    return isNaN(counter) ? 0 : counter;
}

function _saveTaskCounterToLocalStorage() {
    localStorage.setItem(STORAGE_KEY_TASK_COUNTER, _state.taskCounter.toString());
}

function _loadActiveTaskIdFromLocalStorage() {
    return localStorage.getItem(STORAGE_KEY_ACTIVE_TASK_ID);
}

function _saveActiveTaskIdToLocalStorage() {
    if (_state.currentTaskId) {
        localStorage.setItem(STORAGE_KEY_ACTIVE_TASK_ID, _state.currentTaskId);
    } else {
        localStorage.removeItem(STORAGE_KEY_ACTIVE_TASK_ID);
    }
}

function _loadExecutorLlmIdFromLocalStorage() {
    return localStorage.getItem(STORAGE_KEY_EXECUTOR_LLM) || ""; // Default to "" if not found
}

function _saveExecutorLlmIdToLocalStorage() {
    localStorage.setItem(STORAGE_KEY_EXECUTOR_LLM, _state.currentExecutorLlmId);
}

function _loadRoleLlmOverrideFromLocalStorage(role) {
    const key = `${STORAGE_KEY_ROLE_LLM_PREFIX}${role.charAt(0).toUpperCase() + role.slice(1)}LlmId`; // e.g. sessionIntentClassifierLlmId
    return localStorage.getItem(key) || ""; // Default to "" if not found
}

function _saveRoleLlmOverrideToLocalStorage(role) {
    const key = `${STORAGE_KEY_ROLE_LLM_PREFIX}${role.charAt(0).toUpperCase() + role.slice(1)}LlmId`;
    localStorage.setItem(key, _state.sessionRoleLlmOverrides[role]);
}


// --- Initialization ---
function initStateManager() {
    console.log("[StateManager] Initializing state...");
    _state.tasks = _loadTasksFromLocalStorage();
    _state.taskCounter = _loadTaskCounterFromLocalStorage();
    const activeId = _loadActiveTaskIdFromLocalStorage();

    if (activeId && _state.tasks.some(task => task.id === activeId)) {
        _state.currentTaskId = activeId;
    } else if (_state.tasks.length > 0) {
        _state.currentTaskId = _state.tasks[0].id; // Default to the most recent task
        _saveActiveTaskIdToLocalStorage(); // Save this default if activeId was invalid
    } else {
        _state.currentTaskId = null;
    }

    // Load LLM preferences
    _state.currentExecutorLlmId = _loadExecutorLlmIdFromLocalStorage();
    for (const role in _state.sessionRoleLlmOverrides) {
        _state.sessionRoleLlmOverrides[role] = _loadRoleLlmOverrideFromLocalStorage(role);
    }

    // Create a default task if none exist on first load
    if (_state.tasks.length === 0) {
        console.log("[StateManager] No tasks found, creating a default first task.");
        _state.taskCounter = 1; // Start counter at 1
        const firstTask = { 
            id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, 
            title: `Task - ${_state.taskCounter}`, 
            timestamp: Date.now() 
        };
        _state.tasks.unshift(firstTask);
        _state.currentTaskId = firstTask.id;
        _saveTasksToLocalStorage();
        _saveTaskCounterToLocalStorage();
        _saveActiveTaskIdToLocalStorage();
    }
    console.log("[StateManager] Initial state loaded:", JSON.parse(JSON.stringify(_state))); // Deep copy for logging
}

// --- Getters ---
function getTasks() { return [..._state.tasks]; } // Return a copy
function getCurrentTaskId() { return _state.currentTaskId; }
function getTaskCounter() { return _state.taskCounter; }
function getAvailableModels() { return JSON.parse(JSON.stringify(_state.availableModels)); } // Deep copy
function getCurrentExecutorLlmId() { return _state.currentExecutorLlmId; }
function getSessionRoleLlmOverrides() { return JSON.parse(JSON.stringify(_state.sessionRoleLlmOverrides)); }
function getIsAgentRunning() { return _state.isAgentRunning; }
function getCurrentTaskArtifacts() { return [..._state.currentTaskArtifacts]; } // Return a copy
function getCurrentArtifactIndex() { return _state.currentArtifactIndex; }
function getCurrentTaskTotalTokens() { return JSON.parse(JSON.stringify(_state.currentTaskTotalTokens)); }
function getCurrentDisplayedPlan() { return _state.currentDisplayedPlan ? JSON.parse(JSON.stringify(_state.currentDisplayedPlan)) : null; }
function getCurrentPlanProposalId() { return _state.currentPlanProposalId; } // ADDED getter

// --- Setters / Updaters ---
function addTask(taskTitle) {
    _state.taskCounter++;
    const newTask = {
        id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        title: taskTitle || `Task - ${_state.taskCounter}`,
        timestamp: Date.now()
    };
    _state.tasks.unshift(newTask); // Add to the beginning (most recent)
    _saveTasksToLocalStorage();
    _saveTaskCounterToLocalStorage();
    return newTask; // Return the created task
}

function selectTask(taskId) {
    const taskExists = _state.tasks.some(t => t.id === taskId);
    if (taskExists) {
        _state.currentTaskId = taskId;
        _saveActiveTaskIdToLocalStorage();
        // Reset task-specific state when a new task is selected
        _state.currentTaskArtifacts = [];
        _state.currentArtifactIndex = -1;
        _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
        _state.currentDisplayedPlan = null;
        _state.currentPlanProposalId = null; // ADDED: Reset plan proposal ID on task switch
        console.log(`[StateManager] Task selected: ${taskId}. Task-specific state reset.`);
        return true;
    } else if (taskId === null) { // Handling case where no task is selected (e.g., after deleting the last task)
        _state.currentTaskId = null;
        _saveActiveTaskIdToLocalStorage();
        _state.currentTaskArtifacts = [];
        _state.currentArtifactIndex = -1;
        _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
        _state.currentDisplayedPlan = null;
        _state.currentPlanProposalId = null; // ADDED: Reset plan proposal ID
        console.log(`[StateManager] No task selected. Task-specific state reset.`);
        return true;
    }
    console.warn(`[StateManager] Attempted to select non-existent task: ${taskId}`);
    return false;
}

function deleteTask(taskId) {
    const taskIndex = _state.tasks.findIndex(task => task.id === taskId);
    if (taskIndex !== -1) {
        _state.tasks.splice(taskIndex, 1);
        _saveTasksToLocalStorage();
        if (_state.currentTaskId === taskId) {
            _state.currentTaskId = _state.tasks.length > 0 ? _state.tasks[0].id : null;
            _saveActiveTaskIdToLocalStorage();
            // Also reset task-specific state if the active task was deleted
            _state.currentTaskArtifacts = [];
            _state.currentArtifactIndex = -1;
            _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
            _state.currentDisplayedPlan = null;
            _state.currentPlanProposalId = null; // ADDED: Reset plan proposal ID
        }
        return true;
    }
    return false;
}

function renameTask(taskId, newTitle) {
    const task = _state.tasks.find(task => task.id === taskId);
    if (task) {
        task.title = newTitle;
        task.timestamp = Date.now(); // Update timestamp to bring to top
        _saveTasksToLocalStorage();
        return true;
    }
    return false;
}

function setAvailableModels(models) { // models = { gemini: [], ollama: [] }
    if (models && typeof models.gemini !== 'undefined' && typeof models.ollama !== 'undefined') {
        _state.availableModels = JSON.parse(JSON.stringify(models)); // Deep copy
    } else {
        console.warn("[StateManager] Invalid format for setAvailableModels. Expected { gemini: [], ollama: [] }");
    }
}

function setCurrentExecutorLlmId(id) {
    _state.currentExecutorLlmId = id || ""; // Ensure it's a string, default to ""
    _saveExecutorLlmIdToLocalStorage();
}

function setRoleLlmOverride(role, id) {
    if (_state.sessionRoleLlmOverrides.hasOwnProperty(role)) {
        _state.sessionRoleLlmOverrides[role] = id || ""; // Ensure it's a string, default to ""
        _saveRoleLlmOverrideToLocalStorage(role);
    } else {
        console.warn(`[StateManager] Attempted to set LLM override for invalid role: ${role}`);
    }
}

function setIsAgentRunning(isRunning) {
    _state.isAgentRunning = !!isRunning; // Coerce to boolean
}

function setCurrentTaskArtifacts(artifacts) {
    if (Array.isArray(artifacts)) {
        _state.currentTaskArtifacts = [...artifacts]; // Store a copy
    } else {
        console.warn("[StateManager] setCurrentTaskArtifacts expects an array.");
        _state.currentTaskArtifacts = [];
    }
}

function setCurrentArtifactIndex(index) {
    if (typeof index === 'number' && index >= -1 && index < _state.currentTaskArtifacts.length) {
        _state.currentArtifactIndex = index;
    } else {
        console.warn(`[StateManager] Invalid artifact index: ${index}. Max allowed: ${_state.currentTaskArtifacts.length - 1}`);
        // _state.currentArtifactIndex = -1; // Or keep previous valid index
    }
}

function updateCurrentTaskTotalTokens(lastCallUsage) { // lastCallUsage = { input_tokens, output_tokens, total_tokens }
    if (lastCallUsage) {
        _state.currentTaskTotalTokens.input += lastCallUsage.input_tokens || 0;
        _state.currentTaskTotalTokens.output += lastCallUsage.output_tokens || 0;
        _state.currentTaskTotalTokens.total += (lastCallUsage.total_tokens || ((lastCallUsage.input_tokens || 0) + (lastCallUsage.output_tokens || 0)));
    }
}

function resetCurrentTaskTotalTokens() {
    _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
}

function setCurrentDisplayedPlan(plan) { // plan is the structured plan object
    _state.currentDisplayedPlan = plan ? JSON.parse(JSON.stringify(plan)) : null; // Deep copy or null
}

function setCurrentPlanProposalId(planId) { // ADDED setter
    _state.currentPlanProposalId = planId;
}


// Expose functions (this pattern makes them available like module exports if this file is included via <script>)
window.StateManager = {
    initStateManager,
    getTasks,
    getCurrentTaskId,
    getTaskCounter,
    getAvailableModels,
    getCurrentExecutorLlmId,
    getSessionRoleLlmOverrides,
    getIsAgentRunning,
    getCurrentTaskArtifacts,
    getCurrentArtifactIndex,
    getCurrentTaskTotalTokens,
    getCurrentDisplayedPlan,
    getCurrentPlanProposalId,       // ADDED
    addTask,
    selectTask,
    deleteTask,
    renameTask,
    setAvailableModels,
    setCurrentExecutorLlmId,
    setRoleLlmOverride,
    setIsAgentRunning,
    setCurrentTaskArtifacts,
    setCurrentArtifactIndex,
    updateCurrentTaskTotalTokens,
    resetCurrentTaskTotalTokens,
    setCurrentDisplayedPlan,
    setCurrentPlanProposalId,       // ADDED
};

console.log("[StateManager] Loaded.");
