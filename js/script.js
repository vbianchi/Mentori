/**
 * This script acts as the main orchestrator for the AI Agent UI.
 * - Initializes StateManager and UI modules.
 * - Manages the core application lifecycle.
 * - Routes events/messages between UI modules, StateManager, and WebSocket communication.
 * - Handles WebSocket message dispatching.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready! Initializing StateManager...");
    
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
    
    const httpBackendBaseUrl = 'http://localhost:8766';

    window.dispatchWsMessage = (message) => {
        try {
            switch (message.type) {
                case 'history_start': isLoadingHistory = true; if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI(); if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI(); if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Loading history...`, "status"); updateGlobalMonitorStatus('running', 'Loading History...'); break;
                case 'history_end': isLoadingHistory = false; const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child'); if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); } if (typeof scrollToBottomChat === 'function') scrollToBottomChat(); if (typeof scrollToBottomMonitorLog === 'function') scrollToBottomMonitorLog(); updateGlobalMonitorStatus('idle', 'Idle'); break;
                case 'agent_thinking_update': if (message.content && message.content.status) { if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, message.content.status); } break;
                case 'agent_message': if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'agent'); break;
                case 'llm_token_usage': if (message.content && typeof message.content === 'object') { handleTokenUsageUpdate(message.content); } break;
                case 'display_plan_for_confirmation': if (message.content && message.content.human_summary && message.content.structured_plan) { StateManager.setCurrentDisplayedPlan(message.content.structured_plan); if (typeof displayPlanInUI === 'function') { displayPlanInUI(message.content.human_summary, StateManager.getCurrentDisplayedPlan(), handlePlanConfirm, handlePlanCancel); } if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); } else { console.error("Invalid plan data received:", message.content); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received invalid plan from backend.", "status"); } break;
                case 'user': if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'user'); break;
                case 'status_message': const lowerContent = message.content.toLowerCase(); if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, 'status'); if (lowerContent.includes("error")) { updateGlobalMonitorStatus('error', message.content); } else if (lowerContent.includes("complete") || lowerContent.includes("cancelled") || lowerContent.includes("plan confirmed")) { if (!lowerContent.includes("plan confirmed. executing steps...")) { updateGlobalMonitorStatus('idle', 'Idle'); } } if (lowerContent.includes("complete") || lowerContent.includes("error") || lowerContent.includes("cancelled")) { if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); } break;
                case 'monitor_log': if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(message.content); if (message.content.includes("[Agent Finish]") || message.content.includes("Error]")) { if(StateManager.getIsAgentRunning() && !message.content.includes("PLAN EXECUTION LOOP NOT YET IMPLEMENTED")) { updateGlobalMonitorStatus('idle', 'Idle'); } if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); } break;
                case 'update_artifacts':
                    if (Array.isArray(message.content)) {
                        console.log("[Script.js] Received 'update_artifacts' with content:", message.content);
                        const oldArtifacts = StateManager.getCurrentTaskArtifacts();
                        const oldIndex = StateManager.getCurrentArtifactIndex();
                        const oldCurrentArtifactFilename = (oldIndex >= 0 && oldIndex < oldArtifacts.length) ? oldArtifacts[oldIndex]?.filename : null;
                        
                        StateManager.setCurrentTaskArtifacts(message.content);
                        let newIndexToSet = -1;
                        const newArtifacts = StateManager.getCurrentTaskArtifacts(); // Get the newly set artifacts

                        if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_") && oldCurrentArtifactFilename.endsWith(".md")) {
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename);
                            if (foundNewIndex !== -1) { newIndexToSet = foundNewIndex; }
                            else { const latestPlan = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_") && art.filename.endsWith(".md"));
                                   newIndexToSet = latestPlan ? newArtifacts.indexOf(latestPlan) : (newArtifacts.length > 0 ? 0 : -1); }
                        } else if (newArtifacts.length > 0) { newIndexToSet = 0; }
                        
                        StateManager.setCurrentArtifactIndex(newIndexToSet);
                        console.log(`[Script.js] After 'update_artifacts': New Index: ${StateManager.getCurrentArtifactIndex()}, New Artifacts Count: ${newArtifacts.length}`);
                        
                        if(typeof updateArtifactDisplayUI === 'function') {
                            updateArtifactDisplayUI(newArtifacts, StateManager.getCurrentArtifactIndex());
                        } else {
                            console.error("updateArtifactDisplayUI (from artifact_ui.js) is not defined.");
                        }
                    }
                    break;
                case 'trigger_artifact_refresh': const taskIdToRefresh = message.content?.taskId; if (taskIdToRefresh && taskIdToRefresh === StateManager.getCurrentTaskId()) { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] File event detected for task ${taskIdToRefresh}, requesting artifact list update...`); if (typeof sendWsMessage === 'function') sendWsMessage('get_artifacts_for_task', { taskId: StateManager.getCurrentTaskId() }); } break;
                case 'available_models': if (message.content && typeof message.content === 'object') { StateManager.setAvailableModels({gemini: message.content.gemini || [], ollama: message.content.ollama || []}); const backendDefaultExecutorLlmId = message.content.default_executor_llm_id || null; const backendRoleDefaults = message.content.role_llm_defaults || {}; if (typeof populateAllLlmSelectorsUI === 'function') { populateAllLlmSelectorsUI(StateManager.getAvailableModels(), backendDefaultExecutorLlmId, backendRoleDefaults); } } break;
                case 'error_parsing_message': console.error("Error parsing message from WebSocket:", message.content); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Error parsing WebSocket message: ${message.content}`); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received an unreadable message from the backend.", "status"); break;
                default: console.warn("Received unknown message type:", message.type, "Content:", message.content); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Unknown message type received: ${message.type}`);
            }
        } catch (error) {
            console.error("Failed to process dispatched WS message:", error, "Original Message:", message);
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] Error processing dispatched message: ${error.message}.`);
            updateGlobalMonitorStatus('error', 'Processing Error');
            if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
        }
    };

    function updateGlobalMonitorStatus(status, text) { StateManager.setIsAgentRunning(status === 'running' || status === 'cancelling'); if (typeof updateMonitorStatusUI === 'function') { updateMonitorStatusUI(status, text, StateManager.getIsAgentRunning()); } else { console.error("updateMonitorStatusUI (from monitor_ui.js) is not defined."); } };
    function handleTokenUsageUpdate(lastCallUsage = null) { StateManager.updateCurrentTaskTotalTokens(lastCallUsage); if (typeof updateTokenDisplayUI === 'function') { updateTokenDisplayUI(lastCallUsage, StateManager.getCurrentTaskTotalTokens()); } else { console.error("updateTokenDisplayUI (from token_usage_ui.js) not found."); } }
    function resetTaskTokenTotalsGlobally() { StateManager.resetCurrentTaskTotalTokens(); if (typeof resetTokenDisplayUI === 'function') { resetTokenDisplayUI(); } else { console.error("resetTokenDisplayUI (from token_usage_ui.js) not found."); } }
    function clearChatAndMonitor(addLog = true) { if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI(); if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI(); StateManager.setCurrentTaskArtifacts([]); StateManager.setCurrentArtifactIndex(-1); if (typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); if (addLog && typeof addLogEntryToMonitor === 'function') { addLogEntryToMonitor("[SYSTEM] Cleared context."); } console.log("Cleared chat and monitor."); resetTaskTokenTotalsGlobally(); StateManager.setCurrentDisplayedPlan(null); };

    const handleTaskSelection = (taskId) => {
        console.log(`[MainScript] Task selected: ${taskId}`);
        const currentActiveTask = StateManager.getCurrentTaskId();
        if (currentActiveTask === taskId && taskId !== null) { return; }
        
        StateManager.selectTask(taskId); 
        const newActiveTaskId = StateManager.getCurrentTaskId();
        console.log(`[MainScript] After StateManager.selectTask, currentTaskId is: ${newActiveTaskId}. Tasks for render:`, StateManager.getTasks());

        if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), newActiveTaskId);
        
        resetTaskTokenTotalsGlobally(); 
        const selectedTask = StateManager.getTasks().find(t => t.id === newActiveTaskId);

        if (newActiveTaskId && selectedTask) {
            clearChatAndMonitor(false); 
            if (typeof sendWsMessage === 'function') sendWsMessage("context_switch", { task: selectedTask.title, taskId: selectedTask.id });
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Switching task context...", "status");
            updateGlobalMonitorStatus('running', 'Switching Task...');
        } else if (!newActiveTaskId) { 
            clearChatAndMonitor(); 
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("No task selected.", "status");
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] No task selected.");
            updateGlobalMonitorStatus('idle', 'No Task');
        }
    };

    const handleNewTaskCreation = () => { const newTask = StateManager.addTask(); handleTaskSelection(newTask.id); };
    const handleTaskDeletion = (taskId, taskTitle) => { const wasActiveTask = StateManager.getCurrentTaskId() === taskId; StateManager.deleteTask(taskId); if (typeof sendWsMessage === 'function') sendWsMessage("delete_task", { taskId: taskId }); if (wasActiveTask) { handleTaskSelection(StateManager.getCurrentTaskId()); } else { if (typeof renderTaskList === 'function') { renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); } } };
    const handleTaskRename = (taskId, oldTitle, newTitle) => { if (StateManager.renameTask(taskId, newTitle)) { if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); if (taskId === StateManager.getCurrentTaskId()) { if (typeof updateCurrentTaskTitleUI === 'function') updateCurrentTaskTitleUI(StateManager.getTasks(), StateManager.getCurrentTaskId()); } if (typeof sendWsMessage === 'function') sendWsMessage("rename_task", { taskId: taskId, newName: newTitle }); } else { console.error(`Task ${taskId} not found by StateManager for renaming.`); } };
    const handleSendMessageFromUI = (messageText) => { if (!StateManager.getCurrentTaskId()) { alert("Please select or create a task first."); return; } if (StateManager.getIsAgentRunning()) { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Agent is currently busy. Please wait or stop the current process.", "status"); return; } if (typeof addChatMessageToUI === 'function') addChatMessageToUI(messageText, 'user'); if (typeof addMessageToInputHistory === 'function') addMessageToInputHistory(messageText);  if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); if (typeof sendWsMessage === 'function') sendWsMessage("user_message", { content: messageText }); else { console.error("sendWsMessage is not available to send user message."); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Cannot send message. Connection issue.", "status");} updateGlobalMonitorStatus('running', 'Classifying intent...'); };
    const handlePlanConfirm = (confirmedPlanSteps) => { if (typeof sendWsMessage === 'function') { sendWsMessage('execute_confirmed_plan', { confirmed_plan: StateManager.getCurrentDisplayedPlan() }); } else { console.error("sendWsMessage is not available to execute plan."); } if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan confirmed. Starting execution...", "status"); updateGlobalMonitorStatus('running', 'Executing Plan...'); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, 'Executing plan step 1...'); };
    const handlePlanCancel = () => { if (typeof sendWsMessage === 'function') { sendWsMessage('cancel_plan', {}); } else { console.error("sendWsMessage is not available to cancel plan."); } if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan cancelled by user.", "status"); updateGlobalMonitorStatus('idle', 'Idle'); StateManager.setCurrentDisplayedPlan(null); };
    const handleStopAgentRequest = () => { if (StateManager.getIsAgentRunning()) { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] Stop request sent by user."); if (typeof sendWsMessage === 'function') sendWsMessage("cancel_agent", {}); else console.error("sendWsMessage is not available to cancel agent."); updateGlobalMonitorStatus('cancelling', 'Cancelling...'); } };
    
    const handleArtifactNavigation = (direction) => {
        console.log(`[MainScript] Artifact navigation requested: ${direction}`);
        let currentIndex = StateManager.getCurrentArtifactIndex();
        const currentArtifacts = StateManager.getCurrentTaskArtifacts();
        let newIndex = currentIndex;

        if (direction === "prev") {
            if (currentIndex > 0) newIndex = currentIndex - 1;
        } else if (direction === "next") {
            if (currentIndex < currentArtifacts.length - 1) newIndex = currentIndex + 1;
        }
        
        if (newIndex !== currentIndex) {
            StateManager.setCurrentArtifactIndex(newIndex);
            if(typeof updateArtifactDisplayUI === 'function') {
                // Pass the current list and the new index
                updateArtifactDisplayUI(currentArtifacts, newIndex);
            } else {
                console.error("updateArtifactDisplayUI (from artifact_ui.js) is not defined.");
            }
        }
    };

    const handleExecutorLlmChange = (selectedId) => { StateManager.setCurrentExecutorLlmId(selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_llm", { llm_id: selectedId }); }};
    const handleRoleLlmChange = (role, selectedId) => { StateManager.setRoleLlmOverride(role, selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_session_role_llm", { role: role, llm_id: selectedId }); }};
    const handleWsOpen = (event) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket connection established.`); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Connected to backend.", "status"); updateGlobalMonitorStatus('idle', 'Idle'); if (typeof sendWsMessage === 'function') { sendWsMessage("get_available_models", {}); const currentTaskFromState = StateManager.getTasks().find(task => task.id === StateManager.getCurrentTaskId()); if (StateManager.getCurrentTaskId() && currentTaskFromState) { sendWsMessage("context_switch", { task: currentTaskFromState.title, taskId: currentTaskFromState.id }); } else { updateGlobalMonitorStatus('idle', 'No Task'); if(typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); resetTaskTokenTotalsGlobally(); } } };
    const handleWsClose = (event) => { let reason = event.reason || 'No reason given'; let advice = ""; if (event.code === 1000 || event.wasClean) { reason = "Normal"; } else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down or network issue?"; } if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Connection closed.${advice}`, "status", true); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket disconnected. ${reason}`); updateGlobalMonitorStatus('disconnected', 'Disconnected');  if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); };
    const handleWsError = (event, isCreationError = false) => { const errorMsg = isCreationError ? "FATAL: Failed to initialize WebSocket connection." : "ERROR: Cannot connect to backend."; if (typeof addChatMessageToUI === 'function') addChatMessageToUI(errorMsg, "status", true); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[SYSTEM] WebSocket error occurred.`); updateGlobalMonitorStatus('error', isCreationError ? 'Connection Init Failed' : 'Connection Error'); if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); };

    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskCreation); }
    if (uploadFileButtonElement && fileUploadInputElement) { uploadFileButtonElement.addEventListener('click', () => { fileUploadInputElement.click(); }); }
    document.body.addEventListener('click', event => { if (event.target.classList.contains('action-btn')) { const commandText = event.target.textContent.trim(); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(`[USER_ACTION] Clicked: ${commandText}`); if (typeof sendWsMessage === 'function') sendWsMessage("action_command", { command: commandText }); } });

    // --- Initial Load and UI Modules Initialization ---
    // StateManager.initStateManager(); // Called at the top

    if (typeof initTaskUI === 'function') { initTaskUI( { taskListUl: taskListUl, currentTaskTitleEl: currentTaskTitleElement, uploadFileBtn: uploadFileButtonElement }, { onTaskSelect: handleTaskSelection, onNewTask: handleNewTaskCreation, onDeleteTask: handleTaskDeletion, onRenameTask: handleTaskRename }); if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); }
    if (typeof initChatUI === 'function') { initChatUI( { chatMessagesContainer: chatMessagesContainer, agentThinkingStatusEl: agentThinkingStatusElement, chatTextareaEl: chatTextarea, chatSendButtonEl: chatSendButton }, { onSendMessage: handleSendMessageFromUI }); }
    if (typeof initMonitorUI === 'function') { initMonitorUI( { monitorLogArea: monitorLogAreaElement, statusDot: statusDotElement, monitorStatusText: monitorStatusTextElement, stopButton: stopButtonElement }, { onStopAgent: handleStopAgentRequest }); }
    if (typeof initArtifactUI === 'function') { initArtifactUI( { monitorArtifactArea: monitorArtifactArea, artifactNav: artifactNav, prevBtn: artifactPrevBtn, nextBtn: artifactNextBtn, counterEl: artifactCounterElement }, {}, { onNavigate: handleArtifactNavigation }); if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI(StateManager.getCurrentTaskArtifacts(), StateManager.getCurrentArtifactIndex()); }
    if (typeof initLlmSelectorsUI === 'function') { initLlmSelectorsUI( { executorLlmSelect: executorLlmSelectElement, roleSelectors: roleSelectorsMetaForInit }, { onExecutorLlmChange: handleExecutorLlmChange, onRoleLlmChange: handleRoleLlmChange }); }
    if (typeof initTokenUsageUI === 'function') { initTokenUsageUI({ lastCallTokensEl: lastCallTokensElement, taskTotalTokensEl: taskTotalTokensElement }); resetTaskTokenTotalsGlobally(); }
    if (typeof initFileUploadUI === 'function') { initFileUploadUI( { fileUploadInputEl: fileUploadInputElement, uploadFileButtonEl: uploadFileButtonElement }, { httpBaseUrl: httpBackendBaseUrl }, { getCurrentTaskId: StateManager.getCurrentTaskId, addLog: (logText) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(logText); }, addChatMsg: (msgText, msgType, scroll) => { if (typeof addChatMessageToUI === 'function') addChatMessageToUI(msgText, msgType, scroll); } }); }

    if (typeof connectWebSocket === 'function') { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor("[SYSTEM] Attempting to connect to backend..."); updateGlobalMonitorStatus('disconnected', 'Connecting...'); connectWebSocket(handleWsOpen, handleWsClose, handleWsError);
    } else { console.error("connectWebSocket function not found."); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("ERROR: WebSocket manager not loaded.", "status"); updateGlobalMonitorStatus('error', 'Initialization Error'); }
});
