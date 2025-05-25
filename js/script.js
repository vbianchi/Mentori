/**
 * This script acts as the main orchestrator for the AI Agent UI.
 * - Initializes StateManager and UI modules.
 * - Manages the core application lifecycle.
 * - Routes events/messages between UI modules, StateManager, and WebSocket communication.
 * - Handles WebSocket message dispatching.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready! Initializing StateManager...");
    
    // Initialize StateManager first - it handles loading from localStorage
    if (typeof StateManager === 'undefined' || typeof StateManager.initStateManager !== 'function') {
        console.error("FATAL: StateManager is not loaded or initStateManager is not a function. Ensure state_manager.js is loaded before script.js.");
        alert("Application critical error: State manager failed to load. Please check console and refresh.");
        return;
    }
    StateManager.initStateManager();
    console.log("[Script.js] StateManager initialized.");

    // --- Get references to UI elements (passed to UI modules) ---
    const taskListUl = document.getElementById('task-list');
    const newTaskButton = document.getElementById('new-task-button');
    const chatMessagesContainer = document.getElementById('chat-messages');
    const monitorLogAreaElement = document.getElementById('monitor-log-area');
    const monitorArtifactArea = document.getElementById('monitor-artifact-area');
    const artifactNav = document.querySelector('.artifact-nav');
    const artifactPrevBtn = document.getElementById('artifact-prev-btn');
    const artifactNextBtn = document.getElementById('artifact-next-btn');
    const artifactCounterElement = document.getElementById('artifact-counter');
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const currentTaskTitleElement = document.getElementById('current-task-title');
    const statusDotElement = document.getElementById('status-dot');
    const monitorStatusTextElement = document.getElementById('monitor-status-text');
    const stopButtonElement = document.getElementById('stop-button');
    const fileUploadInputElement = document.getElementById('file-upload-input');
    const uploadFileButtonElement = document.getElementById('upload-file-button');
    const agentThinkingStatusElement = document.getElementById('agent-thinking-status');
    const lastCallTokensElement = document.getElementById('last-call-tokens');
    const taskTotalTokensElement = document.getElementById('task-total-tokens');
    const executorLlmSelectElement = document.getElementById('llm-select');
    const intentLlmSelectElement = document.getElementById('intent-llm-select');
    const plannerLlmSelectElement = document.getElementById('planner-llm-select');
    const controllerLlmSelectElement = document.getElementById('controller-llm-select');
    const evaluatorLlmSelectElement = document.getElementById('evaluator-llm-select');

    const roleSelectorsMetaForInit = [
        { element: intentLlmSelectElement, role: 'intent_classifier', storageKey: 'sessionIntentLlmId', label: 'Intent Classifier' },
        { element: plannerLlmSelectElement, role: 'planner', storageKey: 'sessionPlannerLlmId', label: 'Planner' },
        { element: controllerLlmSelectElement, role: 'controller', storageKey: 'sessionControllerLlmId', label: 'Controller' },
        { element: evaluatorLlmSelectElement, role: 'evaluator', storageKey: 'sessionEvaluatorLlmId', label: 'Evaluator' }
    ];
    
    // Constants
    const httpBackendBaseUrl = 'http://localhost:8766';

    // --- WebSocket message dispatcher (called by websocket_manager.js) ---
    window.dispatchWsMessage = (message) => {
        try {
            switch (message.type) {
                case 'history_start':
                    // StateManager.setIsLoadingHistory(true); // If we move this to state
                    if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI();
                    if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI();
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Loading history...`, "status");
                    updateGlobalMonitorStatus('running', 'Loading History...');
                    break;
                case 'history_end':
                    // StateManager.setIsLoadingHistory(false);
                    const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                    if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                    if (typeof scrollToBottomChat === 'function') scrollToBottomChat();
                    if (typeof scrollToBottomMonitorLog === 'function') scrollToBottomMonitorLog();
                    updateGlobalMonitorStatus('idle', 'Idle');
                    break;
                case 'agent_thinking_update':
                    if (message.content && message.content.status) {
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, message.content.status);
                    }
                    break;
                case 'agent_message':
                    if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'agent');
                    break;
                case 'llm_token_usage':
                    if (message.content && typeof message.content === 'object') {
                        handleTokenUsageUpdate(message.content); // Uses StateManager internally
                    }
                    break;
                case 'display_plan_for_confirmation':
                    if (message.content && message.content.human_summary && message.content.structured_plan) {
                        StateManager.setCurrentDisplayedPlan(message.content.structured_plan);
                        if (typeof displayPlanInUI === 'function') {
                            displayPlanInUI(message.content.human_summary, StateManager.getCurrentDisplayedPlan(), handlePlanConfirm, handlePlanCancel);
                        }
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                    } else {
                        console.error("Invalid plan data received:", message.content);
                        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received invalid plan from backend.", "status");
                    }
                    break;
                case 'user':
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'user');
                    break;
                case 'status_message':
                    const lowerContent = message.content.toLowerCase();
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'status');
                    if (lowerContent.includes("error")) { updateGlobalMonitorStatus('error', message.content);
                    } else if (lowerContent.includes("complete") || lowerContent.includes("cancelled") || lowerContent.includes("plan confirmed")) {
                        if (!lowerContent.includes("plan confirmed. executing steps...")) { updateGlobalMonitorStatus('idle', 'Idle'); }
                    }
                    if (lowerContent.includes("complete") || lowerContent.includes("error") || lowerContent.includes("cancelled")) {
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                    }
                    break;
                case 'monitor_log':
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(message.content);
                    if (message.content.includes("[Agent Finish]") || message.content.includes("Error]")) {
                        if(StateManager.getIsAgentRunning() && !message.content.includes("PLAN EXECUTION LOOP NOT YET IMPLEMENTED")) { updateGlobalMonitorStatus('idle', 'Idle'); }
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                    }
                    break;
                case 'update_artifacts':
                    if (Array.isArray(message.content)) {
                        const oldArtifacts = StateManager.getCurrentTaskArtifacts();
                        const oldIndex = StateManager.getCurrentArtifactIndex();
                        const oldCurrentArtifactFilename = (oldIndex >= 0 && oldIndex < oldArtifacts.length) ? oldArtifacts[oldIndex]?.filename : null;
                        
                        StateManager.setCurrentTaskArtifacts(message.content);
                        let newIndexToSet = -1;
                        const newArtifacts = StateManager.getCurrentTaskArtifacts();

                        if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_") && oldCurrentArtifactFilename.endsWith(".md")) {
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename);
                            if (foundNewIndex !== -1) { newIndexToSet = foundNewIndex; }
                            else { const latestPlan = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_") && art.filename.endsWith(".md"));
                                   newIndexToSet = latestPlan ? newArtifacts.indexOf(latestPlan) : (newArtifacts.length > 0 ? 0 : -1); }
                        } else if (newArtifacts.length > 0) { newIndexToSet = 0; }
                        
                        StateManager.setCurrentArtifactIndex(newIndexToSet);
                        if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI();
                    }
                    break;
                case 'trigger_artifact_refresh':
                    const taskIdToRefresh = message.content?.taskId;
                    if (taskIdToRefresh && taskIdToRefresh === StateManager.getCurrentTaskId()) {
                        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] File event detected for task ${taskIdToRefresh}, requesting artifact list update...`);
                        if (typeof sendWsMessage === 'function') sendWsMessage('get_artifacts_for_task', { taskId: StateManager.getCurrentTaskId() });
                    }
                    break;
                case 'available_models':
                    if (message.content && typeof message.content === 'object') {
                        StateManager.setAvailableModels({gemini: message.content.gemini || [], ollama: message.content.ollama || []});
                        const backendDefaultExecutorLlmId = message.content.default_executor_llm_id || null;
                        const backendRoleDefaults = message.content.role_llm_defaults || {};
                        if (typeof populateAllLlmSelectorsUI === 'function') {
                            populateAllLlmSelectorsUI(StateManager.getAvailableModels(), backendDefaultExecutorLlmId, backendRoleDefaults);
                        }
                    }
                    break;
                case 'error_parsing_message':
                    console.error("Error parsing message from WebSocket:", message.content);
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Error parsing WebSocket message: ${message.content}`);
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received an unreadable message from the backend.", "status");
                    break;
                default:
                    console.warn("Received unknown message type:", message.type, "Content:", message.content);
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Unknown message type received: ${message.type}`);
            }
        } catch (error) {
            console.error("Failed to process dispatched WS message:", error, "Original Message:", message);
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Error processing dispatched message: ${error.message}.`);
            updateGlobalMonitorStatus('error', 'Processing Error');
            if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
        }
    };

    // --- Global UI Update Functions ---
    function updateGlobalMonitorStatus(status, text) {
        StateManager.setIsAgentRunning(status === 'running' || status === 'cancelling');
        if (typeof updateMonitorStatusUI === 'function') {
            updateMonitorStatusUI(status, text, StateManager.getIsAgentRunning());
        } else { console.error("updateMonitorStatusUI (from monitor_ui.js) is not defined."); }
    };

    function handleTokenUsageUpdate(lastCallUsage = null) {
        StateManager.updateCurrentTaskTotalTokens(lastCallUsage);
        if (typeof updateTokenDisplayUI === 'function') {
            updateTokenDisplayUI(lastCallUsage, StateManager.getCurrentTaskTotalTokens());
        } else { console.error("updateTokenDisplayUI (from token_usage_ui.js) not found."); }
    }
    
    function resetTaskTokenTotalsGlobally() {
        StateManager.resetCurrentTaskTotalTokens();
        if (typeof resetTokenDisplayUI === 'function') {
            resetTokenDisplayUI(); 
        } else { console.error("resetTokenDisplayUI (from token_usage_ui.js) not found."); }
    }

    // --- Task Management Logic (using StateManager) ---
    function clearChatAndMonitor(addLog = true) {
        if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI();
        if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI();
        StateManager.setCurrentTaskArtifacts([]);
        StateManager.setCurrentArtifactIndex(-1);
        if (typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI();
        if (addLog && typeof addLogEntryToMonitor === 'function') { addLogEntryToMonitor("[SYSTEM] Cleared context."); }
        console.log("Cleared chat and monitor."); 
        resetTaskTokenTotalsGlobally();
        StateManager.setCurrentDisplayedPlan(null);
    };

    const handleTaskSelection = (taskId) => {
        console.log(`[MainScript] Task selected via TaskUI: ${taskId}`);
        if (StateManager.getCurrentTaskId() === taskId && taskId !== null) { console.log("Task already selected."); return; }
        
        StateManager.selectTask(taskId); // This updates currentTaskId and resets task-specific state

        if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId());
        
        resetTaskTokenTotalsGlobally(); // Reset token display for the new task

        const selectedTask = StateManager.getTasks().find(t => t.id === StateManager.getCurrentTaskId());

        if (StateManager.getCurrentTaskId() && selectedTask) {
            clearChatAndMonitor(false);
            if (typeof sendWsMessage === 'function') sendWsMessage("context_switch", { task: selectedTask.title, taskId: selectedTask.id });
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Switching task context...", "status");
            updateGlobalMonitorStatus('running', 'Switching Task...');
        } else if (!StateManager.getCurrentTaskId()) {
            clearChatAndMonitor();
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("No task selected.", "status");
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] No task selected.");
            updateGlobalMonitorStatus('idle', 'No Task');
        } else if (!window.socket || window.socket.readyState !== WebSocket.OPEN) {
            clearChatAndMonitor(false);
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Switched task locally. Connect to backend to load history.", "status");
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Switched task locally to ${taskId}, but WS not open.`);
            updateGlobalMonitorStatus('disconnected', 'Disconnected');
        }
    };

    const handleNewTaskCreation = () => {
        console.log("[MainScript] New task requested via TaskUI.");
        const newTask = StateManager.addTask(); // StateManager handles counter and persistence
        console.log("New task created by StateManager:", newTask);
        handleTaskSelection(newTask.id); // Select the new task
    };

    const handleTaskDeletion = (taskId, taskTitle) => {
        console.log(`[MainScript] Deleting task via TaskUI: ${taskId} (${taskTitle})`);
        const wasActiveTask = StateManager.getCurrentTaskId() === taskId;
        StateManager.deleteTask(taskId); // StateManager handles persistence and updating currentTaskId if needed
        
        if (typeof sendWsMessage === 'function') sendWsMessage("delete_task", { taskId: taskId });
        
        if (wasActiveTask) {
            handleTaskSelection(StateManager.getCurrentTaskId()); // Select new active task (or null)
        } else {
            if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId());
        }
    };

    const handleTaskRename = (taskId, oldTitle, newTitle) => {
        console.log(`[MainScript] Renaming task via TaskUI: ${taskId} from "${oldTitle}" to "${newTitle}"`);
        if (StateManager.renameTask(taskId, newTitle)) {
            if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId());
            if (taskId === StateManager.getCurrentTaskId()) {
                if (typeof updateCurrentTaskTitleUI === 'function') updateCurrentTaskTitleUI(StateManager.getTasks(), StateManager.getCurrentTaskId());
            }
            if (typeof sendWsMessage === 'function') sendWsMessage("rename_task", { taskId: taskId, newName: newTitle });
        } else {
            console.error(`Task ${taskId} not found by StateManager for renaming.`);
        }
    };

    // --- Callbacks for ChatUI ---
    const handleSendMessageFromUI = (messageText) => {
        if (!StateManager.getCurrentTaskId()) { alert("Please select or create a task first."); return; }
        if (StateManager.getIsAgentRunning()) { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Agent is currently busy. Please wait or stop the current process.", "status"); return; }
        
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI(messageText, 'user');
        if (typeof addMessageToInputHistory === 'function') addMessageToInputHistory(messageText); 
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
        
        if (typeof sendWsMessage === 'function') sendWsMessage("user_message", { content: messageText });
        else { console.error("sendWsMessage is not available to send user message."); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Cannot send message. Connection issue.", "status");}
        updateGlobalMonitorStatus('running', 'Classifying intent...');
    };

    const handlePlanConfirm = (confirmedPlanSteps) => { // confirmedPlanSteps is passed but currentDisplayedPlan from StateManager is used
        if (typeof sendWsMessage === 'function') { sendWsMessage('execute_confirmed_plan', { confirmed_plan: StateManager.getCurrentDisplayedPlan() }); }
        else { console.error("sendWsMessage is not available to execute plan."); }
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan confirmed. Starting execution...", "status");
        updateGlobalMonitorStatus('running', 'Executing Plan...'); 
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, 'Executing plan step 1...');
    };

    const handlePlanCancel = () => {
        if (typeof sendWsMessage === 'function') { sendWsMessage('cancel_plan', {}); }
        else { console.error("sendWsMessage is not available to cancel plan."); }
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan cancelled by user.", "status");
        updateGlobalMonitorStatus('idle', 'Idle'); 
        StateManager.setCurrentDisplayedPlan(null);
    };

    // --- Callback for MonitorUI (Stop Button) ---
    const handleStopAgentRequest = () => {
        if (StateManager.getIsAgentRunning()) { 
            console.log("Stop button clicked (handler in script.js).");
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] Stop request sent by user.");
            if (typeof sendWsMessage === 'function') sendWsMessage("cancel_agent", {});
            else console.error("sendWsMessage is not available to cancel agent.");
            updateGlobalMonitorStatus('cancelling', 'Cancelling...');
        }
    };

    // --- Callback for ArtifactUI ---
    const handleArtifactIndexChange = (newIndex) => {
        console.log(`[MainScript] Artifact index changed to: ${newIndex}`);
        StateManager.setCurrentArtifactIndex(newIndex);
        if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI();
        else console.error("updateArtifactDisplayUI (from artifact_ui.js) is not defined.");
    };

    // --- Callbacks for LlmSelectorUI ---
    const handleExecutorLlmChange = (selectedId) => {
        console.log(`[MainScript] Executor LLM changed to: ${selectedId}`);
        StateManager.setCurrentExecutorLlmId(selectedId);
        if (typeof sendWsMessage === 'function') { sendWsMessage("set_llm", { llm_id: selectedId }); }
        else { console.error("sendWsMessage is not available to set LLM."); }
    };
    const handleRoleLlmChange = (role, selectedId) => {
        console.log(`[MainScript] Role LLM for '${role}' changed to: ${selectedId}`);
        StateManager.setRoleLlmOverride(role, selectedId);
        if (typeof sendWsMessage === 'function') { sendWsMessage("set_session_role_llm", { role: role, llm_id: selectedId }); }
        else { console.error("sendWsMessage is not available to set session role LLM."); }
    };

    // --- WebSocket Callbacks (passed to websocket_manager.js) ---
    const handleWsOpen = (event) => {
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket connection established.`);
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Connected to backend.", "status");
        updateGlobalMonitorStatus('idle', 'Idle');
        if (typeof sendWsMessage === 'function') {
            sendWsMessage("get_available_models", {}); 
            const currentTaskFromState = StateManager.getTasks().find(task => task.id === StateManager.getCurrentTaskId());
            if (StateManager.getCurrentTaskId() && currentTaskFromState) {
                 sendWsMessage("context_switch", { task: currentTaskFromState.title, taskId: currentTaskFromState.id });
            } else {
                 updateGlobalMonitorStatus('idle', 'No Task');
                 if(typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI();
                 resetTaskTokenTotalsGlobally();
            }
        } else { console.error("sendWsMessage is not available on WebSocket open."); }
    };
    const handleWsClose = (event) => { /* ... (implementation remains) ... */
        let reason = event.reason || 'No reason given'; let advice = ""; if (event.code === 1000 || event.wasClean) { reason = "Normal"; } else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down or network issue?"; }
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Connection closed.${advice}`, "status", true);
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket disconnected. ${reason}`);
        updateGlobalMonitorStatus('disconnected', 'Disconnected'); 
        if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); else console.error("disableAllLlmSelectorsUI not found");
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
    };
    const handleWsError = (event, isCreationError = false) => { /* ... (implementation remains) ... */
        const errorMsg = isCreationError ? "FATAL: Failed to initialize WebSocket connection." : "ERROR: Cannot connect to backend.";
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI(errorMsg, "status", true);
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket error occurred.`);
        updateGlobalMonitorStatus('error', isCreationError ? 'Connection Init Failed' : 'Connection Error');
        if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); else console.error("disableAllLlmSelectorsUI not found");
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
    };

    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskCreation); }
    if (uploadFileButtonElement && fileUploadInputElement) {
        uploadFileButtonElement.addEventListener('click', () => { fileUploadInputElement.click(); });
    }
    document.body.addEventListener('click', event => {
        if (event.target.classList.contains('action-btn')) {
            const commandText = event.target.textContent.trim();
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[USER_ACTION] Clicked: ${commandText}`);
            if (typeof sendWsMessage === 'function') sendWsMessage("action_command", { command: commandText });
        }
    });

    // --- Initial Load and UI Modules Initialization ---
    // StateManager.initStateManager(); // Already called at the very top

    // Initialize UI Modules, passing DOM elements and callbacks
    if (typeof initTaskUI === 'function') { 
        initTaskUI( { taskListUl: taskListUl, currentTaskTitleEl: currentTaskTitleElement, uploadFileBtn: uploadFileButtonElement }, { onTaskSelect: handleTaskSelection, onNewTask: handleNewTaskCreation, onDeleteTask: handleTaskDeletion, onRenameTask: handleTaskRename });
        if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId());
    } else { console.error("initTaskUI function not found."); }

    if (typeof initChatUI === 'function') { 
        initChatUI( { chatMessagesContainer: chatMessagesContainer, agentThinkingStatusEl: agentThinkingStatusElement, chatTextareaEl: chatTextarea, chatSendButtonEl: chatSendButton }, { onSendMessage: handleSendMessageFromUI });
    } else { console.error("initChatUI function not found."); }

    if (typeof initMonitorUI === 'function') { 
        initMonitorUI( { monitorLogArea: monitorLogAreaElement, statusDot: statusDotElement, monitorStatusText: monitorStatusTextElement, stopButton: stopButtonElement }, { onStopAgent: handleStopAgentRequest });
    } else { console.error("initMonitorUI function not found."); }
    
    if (typeof initArtifactUI === 'function') {
        // ArtifactUI now gets its state directly when its update function is called.
        // The init function primarily sets up DOM elements and navigation callbacks.
        initArtifactUI(
            { monitorArtifactArea: monitorArtifactArea, artifactNav: artifactNav, prevBtn: artifactPrevBtn, nextBtn: artifactNextBtn, counterEl: artifactCounterElement },
            {}, // No direct stateRefs needed for init anymore
            { onIndexChange: handleArtifactIndexChange } // Callback to script.js to update StateManager
        );
        if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI(); // Initial render
    } else { console.error("initArtifactUI function not found."); }

    if (typeof initLlmSelectorsUI === 'function') { 
        initLlmSelectorsUI( { executorLlmSelect: executorLlmSelectElement, roleSelectors: roleSelectorsMetaForInit }, { onExecutorLlmChange: handleExecutorLlmChange, onRoleLlmChange: handleRoleLlmChange });
    } else { console.error("initLlmSelectorsUI function not found."); }

    if (typeof initTokenUsageUI === 'function') { 
        initTokenUsageUI({ lastCallTokensEl: lastCallTokensElement, taskTotalTokensEl: taskTotalTokensElement });
        resetTaskTokenTotalsGlobally(); // Initialize display
    } else { console.error("initTokenUsageUI function not found."); }

    if (typeof initFileUploadUI === 'function') { 
        initFileUploadUI(
            { fileUploadInputEl: fileUploadInputElement, uploadFileButtonEl: uploadFileButtonElement },
            { httpBaseUrl: httpBackendBaseUrl },
            { getCurrentTaskId: StateManager.getCurrentTaskId, // Pass getter from StateManager
              addLog: (logText, logType) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(logText); }, // logType not used by addLogEntryToMonitor
              addChatMsg: (msgText, msgType, scroll) => { if (typeof addChatMessageToUI === 'function') addChatMessageToUI(msgText, msgType, scroll); }
            }
        );
    } else { console.error("initFileUploadUI function not found."); }

    // Connect WebSocket
    if (typeof connectWebSocket === 'function') {
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] Attempting to connect to backend...");
        updateGlobalMonitorStatus('disconnected', 'Connecting...');
        connectWebSocket(handleWsOpen, handleWsClose, handleWsError);
    } else {
        console.error("connectWebSocket function not found. Ensure websocket_manager.js is loaded correctly.");
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("ERROR: WebSocket manager not loaded.", "status");
        updateGlobalMonitorStatus('error', 'Initialization Error');
    }
});
