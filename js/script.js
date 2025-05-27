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
    const agentThinkingStatusElement = document.getElementById('agent-thinking-status'); // Global status line
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
    let isLoadingHistory = false; 

    window.dispatchWsMessage = (message) => {
        try {
            switch (message.type) {
                case 'history_start': 
                    isLoadingHistory = true;
                    if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI(); 
                    if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI(); 
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Loading history...", "status_message", {component_hint: "SYSTEM"}); // Pass component_hint
                    updateGlobalMonitorStatus('running', 'Loading History...'); 
                    break;
                case 'history_end': 
                    isLoadingHistory = false;
                    const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child'); 
                    if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); } 
                    if (typeof scrollToBottomChat === 'function') scrollToBottomChat();
                    if (typeof scrollToBottomMonitorLog === 'function') scrollToBottomMonitorLog(); 
                    updateGlobalMonitorStatus('idle', 'Idle'); 
                    break;
                // <<< --- START NEW CODE --- >>>
                case 'agent_major_step_announcement':
                    if (message.content && typeof message.content.description === 'string') {
                        if (typeof displayMajorStepAnnouncementUI === 'function') {
                            displayMajorStepAnnouncementUI(message.content); // Pass full content obj
                        }
                        // Hide global thinking status when a major step is announced, as sub-statuses will appear under it
                        if (typeof showAgentThinkingStatusInUI === 'function') {
                           showAgentThinkingStatusInUI(false);
                        }
                    } else {
                        console.warn("[Script.js] Invalid agent_major_step_announcement data:", message.content);
                    }
                    break;
                // <<< --- END NEW CODE --- >>>
                case 'agent_thinking_update': 
                    if (message.content && typeof message.content === 'object' && message.content.message) { 
                        if (typeof showAgentThinkingStatusInUI === 'function') {
                            showAgentThinkingStatusInUI(true, message.content); // message.content is statusUpdateObject
                        }
                    } else if (message.content && typeof message.content.status === 'string') { // Legacy
                         if (typeof showAgentThinkingStatusInUI === 'function') {
                            showAgentThinkingStatusInUI(true, { message: message.content.status, status_key: "LEGACY_STATUS", component_hint: "SYSTEM" });
                        }
                    }
                    break;
                case 'agent_message': // This is now for the FINAL agent output
                    if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); // Hide thinking status
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, message.type, { component_hint: message.content.component_hint || "DEFAULT" }); // Pass content as messageData
                    updateGlobalMonitorStatus('idle', 'Idle'); // Agent has finished if it sent a final message
                    break;
                case 'confirmed_plan_log':
                    if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                    if (typeof addChatMessageToUI === 'function') {
                        // Confirmed plan log already has component_hint (PLANNER) set in chat_ui.js
                        addChatMessageToUI(message.content, message.type); 
                    }
                    break;
                case 'llm_token_usage': 
                    if (message.content && typeof message.content === 'object') { 
                        handleTokenUsageUpdate(message.content);
                    } 
                    break;
                case 'propose_plan_for_confirmation':
                    if (message.content && message.content.human_summary && message.content.structured_plan && message.content.plan_id) {
                        StateManager.setCurrentDisplayedPlan(message.content.structured_plan);
                        StateManager.setCurrentPlanProposalId(message.content.plan_id);         
                
                        if (typeof displayPlanConfirmationUI === 'function') { 
                            // Pass the callbacks directly, as message.content can't hold functions
                            const planDataForUI = {
                                ...message.content,
                                onConfirm: handlePlanConfirmRequest,
                                onCancel: handlePlanCancelRequest,
                                onViewDetails: handlePlanViewDetailsRequest
                            };
                            addChatMessageToUI(planDataForUI, message.type); // Let addChatMessageToUI call displayPlanConfirmationUI
                        }
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false);
                        updateGlobalMonitorStatus('idle', 'Awaiting Plan Confirmation'); 
                    } else {
                        console.error("[Script.js] Invalid propose_plan_for_confirmation data received:", message.content);
                        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received invalid plan proposal from backend.", "status_message", { component_hint: "ERROR" });
                    }
                    break;
                case 'user': 
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, message.type, { component_hint: "USER" }); // User messages don't need backend hint
                    break;
                case 'status_message':
                    let statusText = "";
                    let statusComponentHint = "SYSTEM"; // Default for status messages
                    if (typeof message.content === 'string') {
                        statusText = message.content;
                    } else if (message.content && typeof message.content.text === 'string') {
                        statusText = message.content.text;
                        statusComponentHint = message.content.component_hint || statusComponentHint;
                    } else if (message.content) {
                        statusText = String(message.content);
                        console.warn("[Script.js] status_message content was not a string or expected object, converted to string:", statusText);
                    }

                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(statusText, message.type, { component_hint: statusComponentHint });
                    
                    const lowerStatusText = statusText.toLowerCase();
                    if (lowerStatusText.includes("error")) { 
                        updateGlobalMonitorStatus('error', statusText);
                    } else if (lowerStatusText.includes("complete") || lowerStatusText.includes("cancelled") || lowerStatusText.includes("plan confirmed") || lowerStatusText.includes("plan proposal cancelled")) { 
                        if (!lowerStatusText.includes("plan confirmed. executing steps...")) { 
                            updateGlobalMonitorStatus('idle', 'Idle');
                        }
                    } 
                    if (lowerStatusText.includes("complete") || lowerStatusText.includes("error") || lowerStatusText.includes("cancelled") || lowerStatusText.includes("plan proposal cancelled")) { 
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false, {component_hint: statusComponentHint}); // Pass hint for final "Idle" state
                    }
                    break;
                case 'monitor_log': 
                    if (message.content && typeof message.content.text === 'string') {
                        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(message.content); // Pass whole object
                        
                        const monitorTextLower = message.content.text.toLowerCase();
                        // Check for specific phrases that imply the agent has finished or a major flow change
                        const terminalMonitorPhrases = ["[agent finish]", "error]", "cancelled by user", "plan execution stopped", "plan proposal cancelled by user", "[executor_step_output]", "final overall outcome sent to user"];
                        if (terminalMonitorPhrases.some(phrase => monitorTextLower.includes(phrase))) {
                            // If it's an error or cancellation, the status might already be error/idle.
                            // If it's a successful completion phrase, ensure UI reflects idle.
                            if (monitorTextLower.includes("[agent finish]") || monitorTextLower.includes("final overall outcome sent to user")) {
                                // if(StateManager.getIsAgentRunning()) { // Only update if it was running
                                // updateGlobalMonitorStatus('idle', 'Idle');
                                // }
                                // showAgentThinkingStatusInUI(false) is usually handled by agent_message or specific status_key updates
                            }
                        } 
                    } else {
                        console.warn("[Script.js] monitor_log message content is not in expected object format or text is missing:", message.content);
                        if (typeof message.content === 'string' && typeof addLogEntryToMonitor === 'function') {
                             addLogEntryToMonitor({ text: message.content, log_source: "UNKNOWN_STRING_LOG" });
                        }
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
                        if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_proposal_") && oldCurrentArtifactFilename.endsWith(".md")) { 
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename);
                            if (foundNewIndex !== -1) { 
                                newIndexToSet = foundNewIndex;
                            } else { 
                                const latestPlanProposal = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_proposal_") && art.filename.endsWith(".md"));
                                newIndexToSet = latestPlanProposal ? newArtifacts.indexOf(latestPlanProposal) : (newArtifacts.length > 0 ? 0 : -1);
                            } 
                        } else if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_") && oldCurrentArtifactFilename.endsWith(".md")) { 
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename);
                            if (foundNewIndex !== -1) {
                                newIndexToSet = foundNewIndex;
                            } else {
                                const latestPlan = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_") && art.filename.endsWith(".md"));
                                newIndexToSet = latestPlan ? newArtifacts.indexOf(latestPlan) : (newArtifacts.length > 0 ? 0 : -1);
                            }
                        } else if (newArtifacts.length > 0) { 
                            newIndexToSet = 0;
                        } 
                        StateManager.setCurrentArtifactIndex(newIndexToSet);
                        if(typeof updateArtifactDisplayUI === 'function') { updateArtifactDisplayUI(newArtifacts, StateManager.getCurrentArtifactIndex()); } 
                    } 
                    break;
                case 'trigger_artifact_refresh': 
                    const taskIdToRefresh = message.content?.taskId;
                    if (taskIdToRefresh && taskIdToRefresh === StateManager.getCurrentTaskId()) { 
                        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] File event detected for task ${taskIdToRefresh}, requesting artifact list update...`, log_source: "SYSTEM_EVENT"});
                        if (typeof sendWsMessage === 'function') sendWsMessage('get_artifacts_for_task', { taskId: StateManager.getCurrentTaskId() });
                    } 
                    break;
                case 'available_models': 
                    if (message.content && typeof message.content === 'object') { 
                        StateManager.setAvailableModels({gemini: message.content.gemini || [], ollama: message.content.ollama || []});
                        const backendDefaultExecutorLlmId = message.content.default_executor_llm_id || null; 
                        const backendRoleDefaults = message.content.role_llm_defaults || {};
                        if (typeof populateAllLlmSelectorsUI === 'function') { populateAllLlmSelectorsUI(StateManager.getAvailableModels(), backendDefaultExecutorLlmId, backendRoleDefaults); } 
                    } 
                    break;
                case 'error_parsing_message': 
                    console.error("Error parsing message from WebSocket:", message.content);
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] Error parsing WebSocket message: ${message.content}`, log_source: "SYSTEM_ERROR"});
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received an unreadable message from the backend.", "status_message", {component_hint: "ERROR"}); 
                    break;
                default: 
                    console.warn("[Script.js] Received unknown message type:", message.type, "Content:", message.content);
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] Unknown message type received: ${message.type}`, log_source: "SYSTEM_WARNING"});
            }
        } catch (error) {
            console.error("[Script.js] Failed to process dispatched WS message:", error, "Original Message:", message);
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] Error processing dispatched message: ${error.message}.`, log_source: "SYSTEM_ERROR"});
            updateGlobalMonitorStatus('error', 'Processing Error');
            if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); 
        }
    };
    function updateGlobalMonitorStatus(status, text) { StateManager.setIsAgentRunning(status === 'running' || status === 'cancelling'); if (typeof updateMonitorStatusUI === 'function') { updateMonitorStatusUI(status, text, StateManager.getIsAgentRunning()); } }
    function handleTokenUsageUpdate(lastCallUsage = null) { StateManager.updateCurrentTaskTotalTokens(lastCallUsage); if (typeof updateTokenDisplayUI === 'function') { updateTokenDisplayUI(lastCallUsage, StateManager.getCurrentTaskTotalTokens()); } }
    function resetTaskTokenTotalsGlobally() { StateManager.resetCurrentTaskTotalTokens(); if (typeof resetTokenDisplayUI === 'function') { resetTokenDisplayUI(); } }
    function clearChatAndMonitor(addLog = true) { if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI(); if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI(); StateManager.setCurrentTaskArtifacts([]); StateManager.setCurrentArtifactIndex(-1); if (typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); if (addLog && typeof addLogEntryToMonitor === 'function') { addLogEntryToMonitor({text: "[SYSTEM] Cleared context.", log_source: "SYSTEM_EVENT"}); } resetTaskTokenTotalsGlobally(); StateManager.setCurrentDisplayedPlan(null); StateManager.setCurrentPlanProposalId(null); };
    const handleTaskSelection = (taskId) => { 
        console.log(`[MainScript] Task selection requested for: ${taskId}`);
        const previousActiveTaskId = StateManager.getCurrentTaskId();
        StateManager.selectTask(taskId); 
        const newActiveTaskId = StateManager.getCurrentTaskId(); 
        console.log(`[MainScript] StateManager updated. Previous active: ${previousActiveTaskId}, New active: ${newActiveTaskId}`);
        console.log("[MainScript] Tasks from StateManager for rendering:", StateManager.getTasks());
        if (typeof renderTaskList === 'function') { renderTaskList(StateManager.getTasks(), newActiveTaskId); } 
        else { console.error("renderTaskList (from task_ui.js) is not defined."); }
        resetTaskTokenTotalsGlobally(); 
        const selectedTaskObject = StateManager.getTasks().find(t => t.id === newActiveTaskId);
        if (newActiveTaskId && selectedTaskObject) {
            clearChatAndMonitor(false);
            if (typeof sendWsMessage === 'function') sendWsMessage("context_switch", { task: selectedTaskObject.title, taskId: selectedTaskObject.id });
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Switching task context...", "status_message", {component_hint: "SYSTEM"});
            updateGlobalMonitorStatus('running', 'Switching Task...');
        } else if (!newActiveTaskId) { 
            console.log("[MainScript] handleTaskSelection: newActiveTaskId is null. Clearing UI for no task selected.");
            clearChatAndMonitor(); 
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("No task selected.", "status_message", {component_hint: "SYSTEM"});
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM] No task selected.", log_source: "SYSTEM_EVENT"});
            updateGlobalMonitorStatus('idle', 'No Task');
        }
        console.log(`[MainScript] Finished handleTaskSelection for: ${newActiveTaskId}`);
    };
    const handleNewTaskCreation = () => { const newTask = StateManager.addTask(); handleTaskSelection(newTask.id); };
    const handleTaskDeletion = (taskId, taskTitle) => { const wasActiveTask = StateManager.getCurrentTaskId() === taskId; StateManager.deleteTask(taskId); if (typeof sendWsMessage === 'function') sendWsMessage("delete_task", { taskId: taskId }); if (wasActiveTask) { handleTaskSelection(StateManager.getCurrentTaskId()); } else { if (typeof renderTaskList === 'function') { renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); } } };
    const handleTaskRename = (taskId, oldTitle, newTitle) => { if (StateManager.renameTask(taskId, newTitle)) { if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); if (taskId === StateManager.getCurrentTaskId()) { if (typeof updateCurrentTaskTitleUI === 'function') updateCurrentTaskTitleUI(StateManager.getTasks(), StateManager.getCurrentTaskId()); } if (typeof sendWsMessage === 'function') sendWsMessage("rename_task", { taskId: taskId, newName: newTitle }); } };
    const handleSendMessageFromUI = (messageText) => { if (!StateManager.getCurrentTaskId()) { alert("Please select or create a task first."); return; } if (StateManager.getIsAgentRunning()) { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Agent is currently busy. Please wait or stop the current process.", "status_message", {component_hint: "SYSTEM_WARNING"}); return; } if (typeof addChatMessageToUI === 'function') addChatMessageToUI(messageText, 'user'); if (typeof addMessageToInputHistory === 'function') addMessageToInputHistory(messageText); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); if (typeof sendWsMessage === 'function') sendWsMessage("user_message", { content: messageText }); else { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Cannot send message. Connection issue.", "status_message", {component_hint: "ERROR"});} updateGlobalMonitorStatus('running', 'Classifying intent...'); };
    const handlePlanConfirmRequest = (planId) => {
        console.log(`[Script.js] Plan confirmed by user for plan ID: ${planId}`);
        const currentPlan = StateManager.getCurrentDisplayedPlan(); 
        if (!currentPlan) {
            console.error(`[Script.js] Cannot confirm plan ${planId}: No plan found in state.`);
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Could not find plan to confirm. Please try again.", "status_message", {component_hint: "ERROR"});
            updateGlobalMonitorStatus('error', 'Plan Confirmation Error');
            return;
        }
        if (typeof sendWsMessage === 'function') {
            sendWsMessage('execute_confirmed_plan', { plan_id: planId, confirmed_plan: currentPlan });
        }

        if (typeof transformToConfirmedPlanUI === 'function') {
            transformToConfirmedPlanUI(planId);
        } else {
            console.warn("[Script.js] transformToConfirmedPlanUI function not found in chat_ui.js.");
            const planConfirmContainer = chatMessagesContainer.querySelector(`.plan-confirmation-container[data-plan-id="${planId}"]`);
            if (planConfirmContainer) {
                planConfirmContainer.querySelectorAll('button').forEach(btn => btn.disabled = true);
                planConfirmContainer.style.opacity = "0.7";
                let statusP = planConfirmContainer.querySelector('.plan-execution-status');
                if (!statusP) {
                    statusP = document.createElement('p');
                    statusP.className = 'plan-execution-status'; 
                    statusP.style.fontSize = '0.85em';
                    statusP.style.marginTop = '8px';
                    statusP.style.fontStyle = 'italic';
                    const actionsDiv = planConfirmContainer.querySelector('.plan-actions');
                    if (actionsDiv) actionsDiv.insertAdjacentElement('afterend', statusP);
                }
                statusP.textContent = 'Plan confirmed. Execution started...';
                statusP.style.color = 'var(--accent-color)'; 
            } else {
                 if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan confirmed. Executing steps...", "status_message", {component_hint: "SYSTEM"});
            }
        }
        updateGlobalMonitorStatus('running', 'Executing Plan...');
        // No need to call showAgentThinkingStatusInUI(true) here, 
        // backend will send agent_major_step_announcement or agent_thinking_update
    };
    const handlePlanCancelRequest = (planId) => {
        console.log(`[Script.js] Plan cancelled by user for plan ID: ${planId}`);
        if (typeof sendWsMessage === 'function') {
            sendWsMessage('cancel_plan_proposal', { plan_id: planId });
        }
        const planConfirmContainer = chatMessagesContainer.querySelector(`.plan-confirmation-container[data-plan-id="${planId}"]`);
        if (planConfirmContainer) {
            planConfirmContainer.remove();
        }
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan proposal cancelled by user.", "status_message", {component_hint: "SYSTEM"});
        updateGlobalMonitorStatus('idle', 'Idle'); 
        StateManager.setCurrentDisplayedPlan(null);
        StateManager.setCurrentPlanProposalId(null);
    };

    const handlePlanViewDetailsRequest = (planId, isNowVisible) => {
        console.log(`[Script.js] View Details action for plan ID: ${planId}. Inline details are now ${isNowVisible ? 'visible' : 'hidden'}.`);
        if (typeof addLogEntryToMonitor === 'function') {
            addLogEntryToMonitor({text: `[UI_ACTION] User toggled plan details for proposal ${planId}. Details are now ${isNowVisible ? 'visible' : 'hidden'}.`, log_source: "UI_EVENT"});
        }
    };
    
    const handleStopAgentRequest = () => { if (StateManager.getIsAgentRunning()) { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM] Stop request sent by user.", log_source: "SYSTEM_EVENT"}); if (typeof sendWsMessage === 'function') sendWsMessage("cancel_agent", {}); updateGlobalMonitorStatus('cancelling', 'Cancelling...'); } };
    const handleArtifactNavigation = (direction) => { let currentIndex = StateManager.getCurrentArtifactIndex(); const currentArtifacts = StateManager.getCurrentTaskArtifacts(); let newIndex = currentIndex; if (direction === "prev") { if (currentIndex > 0) newIndex = currentIndex - 1; } else if (direction === "next") { if (currentIndex < currentArtifacts.length - 1) newIndex = currentIndex + 1; } if (newIndex !== currentIndex) { StateManager.setCurrentArtifactIndex(newIndex); if(typeof updateArtifactDisplayUI === 'function') { updateArtifactDisplayUI(currentArtifacts, newIndex); } } };
    const handleExecutorLlmChange = (selectedId) => { StateManager.setCurrentExecutorLlmId(selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_llm", { llm_id: selectedId }); }};
    const handleRoleLlmChange = (role, selectedId) => { StateManager.setRoleLlmOverride(role, selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_session_role_llm", { role: role, llm_id: selectedId }); }};
    const handleThinkingStatusClick = () => { if (typeof scrollToBottomMonitorLog === 'function') { scrollToBottomMonitorLog(); } };
    const handleWsOpen = (event) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] WebSocket connection established.`, log_source: "SYSTEM_CONNECTION"}); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Connected to backend.", "status_message", {component_hint: "SYSTEM"}); updateGlobalMonitorStatus('idle', 'Idle'); if (typeof sendWsMessage === 'function') { sendWsMessage("get_available_models", {}); const currentTaskFromState = StateManager.getTasks().find(task => task.id === StateManager.getCurrentTaskId()); if (StateManager.getCurrentTaskId() && currentTaskFromState) { sendWsMessage("context_switch", { task: currentTaskFromState.title, taskId: currentTaskFromState.id }); } else { updateGlobalMonitorStatus('idle', 'No Task'); if(typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); resetTaskTokenTotalsGlobally(); } } };
    const handleWsClose = (event) => { let reason = event.reason || 'No reason given'; let advice = ""; if (event.code === 1000 || event.wasClean) { reason = "Normal"; } else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down or network issue?"; } if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Connection closed.${advice}`, "status_message", {component_hint: "ERROR", isError: true}); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] WebSocket disconnected. ${reason}`, log_source: "SYSTEM_CONNECTION"}); updateGlobalMonitorStatus('disconnected', 'Disconnected');  if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); };
    const handleWsError = (event, isCreationError = false) => { const errorMsg = isCreationError ? "FATAL: Failed to initialize WebSocket connection." : "ERROR: Cannot connect to backend."; if (typeof addChatMessageToUI === 'function') addChatMessageToUI(errorMsg, "status_message", {component_hint: "ERROR", isError: true}); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM] WebSocket error occurred.`, log_source: "SYSTEM_ERROR"}); updateGlobalMonitorStatus('error', isCreationError ? 'Connection Init Failed' : 'Connection Error'); if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); };

    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskCreation); }
    document.body.addEventListener('click', event => { if (event.target.classList.contains('action-btn')) { const commandText = event.target.textContent.trim(); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[USER_ACTION] Clicked: ${commandText}`, log_source: "UI_EVENT"}); if (typeof sendWsMessage === 'function') sendWsMessage("action_command", { command: commandText }); } });
    if (typeof initTaskUI === 'function') { initTaskUI( { taskListUl: taskListUl, currentTaskTitleEl: currentTaskTitleElement, uploadFileBtn: uploadFileButtonElement }, { onTaskSelect: handleTaskSelection, onNewTask: handleNewTaskCreation, onDeleteTask: handleTaskDeletion, onRenameTask: handleTaskRename }); if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); }
    if (typeof initChatUI === 'function') { initChatUI( { chatMessagesContainer: chatMessagesContainer, agentThinkingStatusEl: agentThinkingStatusElement, chatTextareaEl: chatTextarea, chatSendButtonEl: chatSendButton }, { onSendMessage: handleSendMessageFromUI, onThinkingStatusClick: handleThinkingStatusClick }); }
    if (typeof initMonitorUI === 'function') { initMonitorUI( { monitorLogArea: monitorLogAreaElement, statusDot: statusDotElement, monitorStatusText: monitorStatusTextElement, stopButton: stopButtonElement }, { onStopAgent: handleStopAgentRequest }); }
    if (typeof initArtifactUI === 'function') { initArtifactUI( { monitorArtifactArea: monitorArtifactArea, artifactNav: artifactNav, prevBtn: artifactPrevBtn, nextBtn: artifactNextBtn, counterEl: artifactCounterElement }, { onNavigate: handleArtifactNavigation }); if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI(StateManager.getCurrentTaskArtifacts(), StateManager.getCurrentArtifactIndex()); }
    if (typeof initLlmSelectorsUI === 'function') { initLlmSelectorsUI( { executorLlmSelect: executorLlmSelectElement, roleSelectors: roleSelectorsMetaForInit }, { onExecutorLlmChange: handleExecutorLlmChange, onRoleLlmChange: handleRoleLlmChange }); }
    if (typeof initTokenUsageUI === 'function') { initTokenUsageUI({ lastCallTokensEl: lastCallTokensElement, taskTotalTokensEl: taskTotalTokensElement }); resetTaskTokenTotalsGlobally(); }
    if (typeof initFileUploadUI === 'function') { initFileUploadUI( { fileUploadInputEl: fileUploadInputElement, uploadFileButtonEl: uploadFileButtonElement }, { httpBackendBaseUrl: httpBackendBaseUrl }, { getCurrentTaskId: StateManager.getCurrentTaskId, addLog: (logData) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(logData); }, addChatMsg: (msgText, msgType, scroll) => { if (typeof addChatMessageToUI === 'function') addChatMessageToUI(msgText, msgType, {component_hint: "SYSTEM"}, scroll); } }); }

    if (typeof connectWebSocket === 'function') { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM] Attempting to connect to backend...", log_source: "SYSTEM_CONNECTION"}); updateGlobalMonitorStatus('disconnected', 'Connecting...'); connectWebSocket(handleWsOpen, handleWsClose, handleWsError);
    } else { console.error("connectWebSocket function not found."); if (typeof addChatMessageToUI === 'function') addChatMessageToUI("ERROR: WebSocket manager not loaded.", "status_message", {component_hint: "ERROR"}); updateGlobalMonitorStatus('error', 'Initialization Error'); }
});
