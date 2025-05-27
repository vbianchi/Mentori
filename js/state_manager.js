// js/state_manager.js

/**
 * Manages the client-side application state.
 * Provides getters and setters for various parts of the state.
 * Handles persistence of relevant state to localStorage.
 */

const STORAGE_KEY_TASKS = 'aiAgentTasks'; //
const STORAGE_KEY_TASK_COUNTER = 'aiAgentTaskCounter'; //
const STORAGE_KEY_ACTIVE_TASK_ID = 'aiAgentTasks_active'; //
const STORAGE_KEY_EXECUTOR_LLM = 'selectedExecutorLlmId'; //
const STORAGE_KEY_ROLE_LLM_PREFIX = 'session'; //

// Internal state object
const _state = {
    tasks: [], //
    currentTaskId: null, //
    taskCounter: 0, //
    availableModels: { gemini: [], ollama: [] }, //
    currentExecutorLlmId: "", //
    sessionRoleLlmOverrides: { //
        intent_classifier: "", 
        planner: "", 
        controller: "", 
        evaluator: "" 
    },
    isAgentRunning: false, //
    currentTaskArtifacts: [], //
    currentArtifactIndex: -1, //
    currentTaskTotalTokens: { input: 0, output: 0, total: 0 }, //
    currentDisplayedPlan: null, //
    currentPlanProposalId: null, //
    // <<< START CHANGE 3.1.1 >>>
    currentSessionId: null, // To store the WebSocket session ID from the backend
    // <<< END CHANGE 3.1.1 >>>
}; //

// --- Private Helper Functions for localStorage ---
function _loadTasksFromLocalStorage() {
    const storedTasks = localStorage.getItem(STORAGE_KEY_TASKS); //
    if (storedTasks) { //
        try {
            const parsedTasks = JSON.parse(storedTasks); //
            if (Array.isArray(parsedTasks)) { //
                return parsedTasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)); //
            }
        } catch (e) {
            console.error("[StateManager] Failed to parse tasks from localStorage:", e); //
            localStorage.removeItem(STORAGE_KEY_TASKS); //
        }
    }
    return []; //
}

function _saveTasksToLocalStorage() {
    try {
        _state.tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)); //
        localStorage.setItem(STORAGE_KEY_TASKS, JSON.stringify(_state.tasks)); //
    } catch (e) {
        console.error("[StateManager] Failed to save tasks to localStorage:", e); //
    }
}

function _loadTaskCounterFromLocalStorage() {
    const storedCounter = localStorage.getItem(STORAGE_KEY_TASK_COUNTER); //
    const counter = storedCounter ? parseInt(storedCounter, 10) : 0; //
    return isNaN(counter) ? 0 : counter; //
}

function _saveTaskCounterToLocalStorage() {
    localStorage.setItem(STORAGE_KEY_TASK_COUNTER, _state.taskCounter.toString()); //
}

function _loadActiveTaskIdFromLocalStorage() {
    return localStorage.getItem(STORAGE_KEY_ACTIVE_TASK_ID); //
}

function _saveActiveTaskIdToLocalStorage() {
    if (_state.currentTaskId) {
        localStorage.setItem(STORAGE_KEY_ACTIVE_TASK_ID, _state.currentTaskId); //
    } else {
        localStorage.removeItem(STORAGE_KEY_ACTIVE_TASK_ID); //
    }
}

function _loadExecutorLlmIdFromLocalStorage() {
    return localStorage.getItem(STORAGE_KEY_EXECUTOR_LLM) || ""; //
}

function _saveExecutorLlmIdToLocalStorage() {
    localStorage.setItem(STORAGE_KEY_EXECUTOR_LLM, _state.currentExecutorLlmId); //
}

function _loadRoleLlmOverrideFromLocalStorage(role) {
    const key = `${STORAGE_KEY_ROLE_LLM_PREFIX}${role.charAt(0).toUpperCase() + role.slice(1)}LlmId`; //
    return localStorage.getItem(key) || ""; //
}

function _saveRoleLlmOverrideToLocalStorage(role) {
    const key = `${STORAGE_KEY_ROLE_LLM_PREFIX}${role.charAt(0).toUpperCase() + role.slice(1)}LlmId`; //
    localStorage.setItem(key, _state.sessionRoleLlmOverrides[role]); //
}


// --- Initialization ---
function initStateManager() {
    console.log("[StateManager] Initializing state...");
    _state.tasks = _loadTasksFromLocalStorage(); //
    _state.taskCounter = _loadTaskCounterFromLocalStorage(); //
    const activeId = _loadActiveTaskIdFromLocalStorage(); //

    if (activeId && _state.tasks.some(task => task.id === activeId)) { //
        _state.currentTaskId = activeId; //
    } else if (_state.tasks.length > 0) { //
        _state.currentTaskId = _state.tasks[0].id; //
        _saveActiveTaskIdToLocalStorage(); //
    } else {
        _state.currentTaskId = null; //
    }

    // Load LLM preferences
    _state.currentExecutorLlmId = _loadExecutorLlmIdFromLocalStorage(); //
    for (const role in _state.sessionRoleLlmOverrides) { //
        _state.sessionRoleLlmOverrides[role] = _loadRoleLlmOverrideFromLocalStorage(role); //
    }

    // Create a default task if none exist on first load
    if (_state.tasks.length === 0) { //
        console.log("[StateManager] No tasks found, creating a default first task."); //
        _state.taskCounter = 1; //
        const firstTask = { 
            id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, 
            title: `Task - ${_state.taskCounter}`, 
            timestamp: Date.now() 
        }; //
        _state.tasks.unshift(firstTask); //
        _state.currentTaskId = firstTask.id; //
        _saveTasksToLocalStorage(); //
        _saveTaskCounterToLocalStorage(); //
        _saveActiveTaskIdToLocalStorage(); //
    }
    console.log("[StateManager] Initial state loaded:", JSON.parse(JSON.stringify(_state))); //
}

// --- Getters ---
function getTasks() { return [..._state.tasks]; } //
function getCurrentTaskId() { return _state.currentTaskId; } //
function getTaskCounter() { return _state.taskCounter; } //
function getAvailableModels() { return JSON.parse(JSON.stringify(_state.availableModels)); } //
function getCurrentExecutorLlmId() { return _state.currentExecutorLlmId; } //
function getSessionRoleLlmOverrides() { return JSON.parse(JSON.stringify(_state.sessionRoleLlmOverrides)); } //
function getIsAgentRunning() { return _state.isAgentRunning; } //
function getCurrentTaskArtifacts() { return [..._state.currentTaskArtifacts]; } //
function getCurrentArtifactIndex() { return _state.currentArtifactIndex; } //
function getCurrentTaskTotalTokens() { return JSON.parse(JSON.stringify(_state.currentTaskTotalTokens)); } //
function getCurrentDisplayedPlan() { return _state.currentDisplayedPlan ? JSON.parse(JSON.stringify(_state.currentDisplayedPlan)) : null; } //
function getCurrentPlanProposalId() { return _state.currentPlanProposalId; } //
// <<< START CHANGE 3.1.2 >>>
function getCurrentSessionId() { return _state.currentSessionId; }
// <<< END CHANGE 3.1.2 >>>


// --- Setters / Updaters ---
function addTask(taskTitle) {
    _state.taskCounter++; //
    const newTask = {
        id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, //
        title: taskTitle || `Task - ${_state.taskCounter}`, //
        timestamp: Date.now() //
    };
    _state.tasks.unshift(newTask); //
    _saveTasksToLocalStorage(); //
    _saveTaskCounterToLocalStorage(); //
    return newTask; //
}

function selectTask(taskId) {
    const taskExists = _state.tasks.some(t => t.id === taskId); //
    if (taskExists) { //
        _state.currentTaskId = taskId; //
        _saveActiveTaskIdToLocalStorage(); //
        _state.currentTaskArtifacts = []; //
        _state.currentArtifactIndex = -1; //
        _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 }; //
        _state.currentDisplayedPlan = null; //
        _state.currentPlanProposalId = null; //
        console.log(`[StateManager] Task selected: ${taskId}. Task-specific state reset.`); //
        return true; //
    } else if (taskId === null) { //
        _state.currentTaskId = null; //
        _saveActiveTaskIdToLocalStorage(); //
        _state.currentTaskArtifacts = []; //
        _state.currentArtifactIndex = -1; //
        _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 }; //
        _state.currentDisplayedPlan = null; //
        _state.currentPlanProposalId = null; //
        console.log(`[StateManager] No task selected. Task-specific state reset.`); //
        return true; //
    }
    console.warn(`[StateManager] Attempted to select non-existent task: ${taskId}`); //
    return false; //
}

function deleteTask(taskId) {
    const taskIndex = _state.tasks.findIndex(task => task.id === taskId); //
    if (taskIndex !== -1) { //
        _state.tasks.splice(taskIndex, 1); //
        _saveTasksToLocalStorage(); //
        if (_state.currentTaskId === taskId) { //
            _state.currentTaskId = _state.tasks.length > 0 ? _state.tasks[0].id : null; //
            _saveActiveTaskIdToLocalStorage(); //
            _state.currentTaskArtifacts = []; //
            _state.currentArtifactIndex = -1; //
            _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 }; //
            _state.currentDisplayedPlan = null; //
            _state.currentPlanProposalId = null; //
        }
        return true; //
    }
    return false; //
}

function renameTask(taskId, newTitle) {
    const task = _state.tasks.find(task => task.id === taskId); //
    if (task) { //
        task.title = newTitle; //
        task.timestamp = Date.now(); //
        _saveTasksToLocalStorage(); //
        return true; //
    }
    return false; //
}

function setAvailableModels(models) { 
    if (models && typeof models.gemini !== 'undefined' && typeof models.ollama !== 'undefined') { //
        _state.availableModels = JSON.parse(JSON.stringify(models)); //
    } else {
        console.warn("[StateManager] Invalid format for setAvailableModels. Expected { gemini: [], ollama: [] }"); //
    }
}

function setCurrentExecutorLlmId(id) {
    _state.currentExecutorLlmId = id || ""; //
    _saveExecutorLlmIdToLocalStorage(); //
}

function setRoleLlmOverride(role, id) {
    if (_state.sessionRoleLlmOverrides.hasOwnProperty(role)) { //
        _state.sessionRoleLlmOverrides[role] = id || ""; //
        _saveRoleLlmOverrideToLocalStorage(role); //
    } else {
        console.warn(`[StateManager] Attempted to set LLM override for invalid role: ${role}`); //
    }
}

function setIsAgentRunning(isRunning) {
    _state.isAgentRunning = !!isRunning; 
}

function setCurrentTaskArtifacts(artifacts) {
    if (Array.isArray(artifacts)) { //
        _state.currentTaskArtifacts = [...artifacts]; //
    } else {
        console.warn("[StateManager] setCurrentTaskArtifacts expects an array."); //
        _state.currentTaskArtifacts = []; //
    }
}

function setCurrentArtifactIndex(index) {
    if (typeof index === 'number' && index >= -1 && index < _state.currentTaskArtifacts.length) { //
        _state.currentArtifactIndex = index; //
    } else {
        console.warn(`[StateManager] Invalid artifact index: ${index}. Max allowed: ${_state.currentTaskArtifacts.length - 1}`); //
    }
}

function updateCurrentTaskTotalTokens(lastCallUsage) { 
    if (lastCallUsage) { //
        _state.currentTaskTotalTokens.input += lastCallUsage.input_tokens || 0; //
        _state.currentTaskTotalTokens.output += lastCallUsage.output_tokens || 0; //
        _state.currentTaskTotalTokens.total += (lastCallUsage.total_tokens || ((lastCallUsage.input_tokens || 0) + (lastCallUsage.output_tokens || 0))); //
    }
}

function resetCurrentTaskTotalTokens() {
    _state.currentTaskTotalTokens = { input: 0, output: 0, total: 0 }; //
}

function setCurrentDisplayedPlan(plan) { 
    _state.currentDisplayedPlan = plan ? JSON.parse(JSON.stringify(plan)) : null; //
}

function setCurrentPlanProposalId(planId) { 
    _state.currentPlanProposalId = planId; //
}

// <<< START CHANGE 3.1.3 >>>
function setCurrentSessionId(sessionId) {
    _state.currentSessionId = sessionId;
    console.log(`[StateManager] Session ID set to: ${sessionId}`);
}
// <<< END CHANGE 3.1.3 >>>


// Expose functions 
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
    getCurrentPlanProposalId,       
    // <<< START CHANGE 3.1.4 >>>
    getCurrentSessionId,
    // <<< END CHANGE 3.1.4 >>>
    addTask,
    selectTask,
    deleteTask,
    renameTask,
    setAvailableModels,
    setCurrentExecutorLlmId, //
    setRoleLlmOverride,
    setIsAgentRunning,
    setCurrentTaskArtifacts,
    setCurrentArtifactIndex,
    updateCurrentTaskTotalTokens,
    resetCurrentTaskTotalTokens,
    setCurrentDisplayedPlan,
    setCurrentPlanProposalId,       
    // <<< START CHANGE 3.1.5 >>>
    setCurrentSessionId,
    // <<< END CHANGE 3.1.5 >>>
};
console.log("[StateManager] Loaded."); //