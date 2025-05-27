/**
 * This script acts as the main orchestrator for the AI Agent UI. [cite: 1154]
 * - Initializes StateManager and UI modules. [cite: 1154]
 * - Manages the core application lifecycle. [cite: 1155]
 * - Routes events/messages between UI modules, StateManager, and WebSocket communication. [cite: 1156]
 * - Handles WebSocket message dispatching. [cite: 1156]
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready! Initializing StateManager...");
    
    if (typeof StateManager === 'undefined' || typeof StateManager.initStateManager !== 'function') { // [cite: 1157]
        console.error("FATAL: StateManager is not loaded or initStateManager is not a function. Ensure state_manager.js is loaded before script.js.");
        alert("Application critical error: State manager failed to load. Please check console and refresh.");
        return;
    }
    StateManager.initStateManager(); // [cite: 1157]
    console.log("[Script.js] StateManager initialized."); // [cite: 1157]

    // DOM Element References
    const taskListUl = document.getElementById('task-list'); // [cite: 1158]
    const newTaskButton = document.getElementById('new-task-button'); // [cite: 1158]
    const chatMessagesContainer = document.getElementById('chat-messages'); // [cite: 1158]
    const monitorLogAreaElement = document.getElementById('monitor-log-area'); // [cite: 1158]
    const monitorArtifactArea = document.getElementById('monitor-artifact-area'); // [cite: 1158]
    const artifactNav = document.querySelector('.artifact-nav'); // [cite: 1159]
    const artifactPrevBtn = document.getElementById('artifact-prev-btn'); // [cite: 1159]
    const artifactNextBtn = document.getElementById('artifact-next-btn'); // [cite: 1159]
    const artifactCounterElement = document.getElementById('artifact-counter'); // [cite: 1159]
    const chatTextarea = document.querySelector('.chat-input-area textarea'); // [cite: 1160]
    const chatSendButton = document.querySelector('.chat-input-area button'); // [cite: 1160]
    const currentTaskTitleElement = document.getElementById('current-task-title'); // [cite: 1160]
    const statusDotElement = document.getElementById('status-dot'); // [cite: 1160]
    const monitorStatusTextElement = document.getElementById('monitor-status-text'); // [cite: 1161]
    const stopButtonElement = document.getElementById('stop-button'); // [cite: 1161]
    const fileUploadInputElement = document.getElementById('file-upload-input'); // [cite: 1161]
    const uploadFileButtonElement = document.getElementById('upload-file-button'); // [cite: 1161]
    const agentThinkingStatusElement = document.getElementById('agent-thinking-status'); // [cite: 1161]
    const lastCallTokensElement = document.getElementById('last-call-tokens'); // [cite: 1162]
    const taskTotalTokensElement = document.getElementById('task-total-tokens'); // [cite: 1162]
    const executorLlmSelectElement = document.getElementById('llm-select'); // [cite: 1162]
    const intentLlmSelectElement = document.getElementById('intent-llm-select'); // [cite: 1162]
    const plannerLlmSelectElement = document.getElementById('planner-llm-select'); // [cite: 1162]
    const controllerLlmSelectElement = document.getElementById('controller-llm-select'); // [cite: 1163]
    const evaluatorLlmSelectElement = document.getElementById('evaluator-llm-select'); // [cite: 1163]

    const roleSelectorsMetaForInit = [
        { element: intentLlmSelectElement, role: 'intent_classifier', storageKey: 'sessionIntentClassifierLlmId', label: 'Intent Classifier' }, // [cite: 1163]
        { element: plannerLlmSelectElement, role: 'planner', storageKey: 'sessionPlannerLlmId', label: 'Planner' }, // [cite: 1163]
        { element: controllerLlmSelectElement, role: 'controller', storageKey: 'sessionControllerLlmId', label: 'Controller' }, // [cite: 1163]
        { element: evaluatorLlmSelectElement, role: 'evaluator', storageKey: 'sessionEvaluatorLlmId', label: 'Evaluator' } // [cite: 1163]
    ];
    const httpBackendBaseUrl = 'http://localhost:8766'; // [cite: 1163]
    let isLoadingHistory = false; // [cite: 1164]

    window.dispatchWsMessage = (message) => {
        try {
            // console.log("[Script.js] Dispatching WS Message:", message.type, message.content); // [cite: 1164]
            switch (message.type) { // [cite: 1164]
                // <<< START CHANGE 4.1 >>>
                case 'session_established':
                    if (message.content && message.content.session_id && typeof StateManager !== 'undefined' && typeof StateManager.setCurrentSessionId === 'function') {
                        StateManager.setCurrentSessionId(message.content.session_id);
                        console.log(`[Script.js] Full session ID established via 'session_established': ${message.content.session_id}`);
                    }
                    break;
                // <<< END CHANGE 4.1 >>>
                case 'history_start': 
                    isLoadingHistory = true; // [cite: 1165]
                    // clearChatMessagesUI and clearMonitorLogUI are called by handleTaskSelection before context_switch [cite: 1165]
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Loading history...", "status_message", { component_hint: "SYSTEM"}); // [cite: 1166]
                    updateGlobalMonitorStatus('running', 'Loading History...'); // [cite: 1167]
                    break;
                case 'history_end': 
                    isLoadingHistory = false; // [cite: 1168]
                    const loadingMsgWrapper = Array.from(chatMessagesContainer.querySelectorAll('.message-outer-blue-line')) // [cite: 1168]
                                               .find(wrapper => wrapper.querySelector('.message-system-status-content')?.textContent.startsWith("Loading history...")); // [cite: 1168]
                    if (loadingMsgWrapper) { // [cite: 1169]
                        loadingMsgWrapper.remove(); // [cite: 1170]
                    } 
                    if (typeof scrollToBottomChat === 'function') scrollToBottomChat(); // [cite: 1171]
                    if (typeof scrollToBottomMonitorLog === 'function') scrollToBottomMonitorLog(); // [cite: 1171]
                    
                    if (!StateManager.getIsAgentRunning()) { // [cite: 1172]
                        updateGlobalMonitorStatus('idle', 'Idle'); // [cite: 1172]
                        if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1173]
                            showAgentThinkingStatusInUI(true, { message: "Idle.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1174]
                        }
                    } else {
                        console.log("[Script.js] History loaded, but agent is already running. Not setting to Idle."); // [cite: 1175]
                    }
                    break;
                case 'agent_major_step_announcement': // [cite: 1176]
                    if (message.content && typeof message.content.description === 'string') { // [cite: 1177]
                        if (typeof displayMajorStepAnnouncementUI === 'function') { // [cite: 1177]
                            displayMajorStepAnnouncementUI(message.content); // [cite: 1177]
                        }
                    } else {
                        console.warn("[Script.js] Invalid agent_major_step_announcement data:", message.content); // [cite: 1178]
                    }
                    break;
                case 'agent_thinking_update': // [cite: 1179]
                    if (message.content && typeof message.content === 'object' && (message.content.message || message.content.sub_type)) { // [cite: 1179]
                        if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1179]
                            showAgentThinkingStatusInUI(true, message.content); // [cite: 1180]
                        }
                    } else if (message.content && typeof message.content.status === 'string') { // [cite: 1180]
                         if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1181]
                            showAgentThinkingStatusInUI(true, { message: message.content.status, status_key: "LEGACY_STATUS", component_hint: "SYSTEM" }); // [cite: 1181]
                        }
                    }
                    break;
                case 'agent_message': // [cite: 1182]
                    if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); // [cite: 1183]
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, message.type, { component_hint: message.content.component_hint || 'DEFAULT' }); // [cite: 1183]
                    updateGlobalMonitorStatus('idle', 'Idle'); // [cite: 1183]
                    if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Idle.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1184]
                    break;
                case 'confirmed_plan_log': // [cite: 1185]
                    if (typeof addChatMessageToUI === 'function') { // [cite: 1186]
                        addChatMessageToUI(message.content, message.type); // [cite: 1186]
                    }
                    break;
                case 'llm_token_usage': // [cite: 1187]
                    if (message.content && typeof message.content === 'object') { // [cite: 1187]
                        handleTokenUsageUpdate(message.content); // [cite: 1188]
                    } 
                    break;
                case 'propose_plan_for_confirmation': // [cite: 1189]
                    if (message.content && message.content.human_summary && message.content.structured_plan && message.content.plan_id) { // [cite: 1189]
                        StateManager.setCurrentDisplayedPlan(message.content.structured_plan); // [cite: 1190]
                        StateManager.setCurrentPlanProposalId(message.content.plan_id); // [cite: 1190]
                
                        if (typeof addChatMessageToUI === 'function') { // [cite: 1190]
                            const planDataForUI = { // [cite: 1191]
                                ...message.content, // [cite: 1191]
                                onConfirm: handlePlanConfirmRequest, // [cite: 1191]
                                onCancel: handlePlanCancelRequest, // [cite: 1192]
                                onViewDetails: handlePlanViewDetailsRequest // [cite: 1192]
                            };
                            addChatMessageToUI(planDataForUI, message.type); // [cite: 1192]
                        }
                        updateGlobalMonitorStatus('idle', 'Awaiting Plan Confirmation'); // [cite: 1193]
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Awaiting plan confirmation...", status_key: "AWAITING_PLAN_CONFIRMATION", component_hint: "SYSTEM" }); // [cite: 1194]
                    } else {
                        console.error("[Script.js] Invalid propose_plan_for_confirmation data received:", message.content); // [cite: 1195]
                        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received invalid plan proposal from backend.", "status_message", { component_hint: "ERROR", isError: true }); // [cite: 1196]
                    }
                    break;
                case 'user': // [cite: 1197]
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(message.content, message.type); // [cite: 1198]
                    break;
                case 'status_message': // [cite: 1198]
                    let statusText = ""; // [cite: 1199]
                    let statusComponentHint = "SYSTEM"; // [cite: 1199]
                    let isErrorStatus = false; // [cite: 1199]

                    if (typeof message.content === 'string') { // [cite: 1200]
                        statusText = message.content; // [cite: 1200]
                    } else if (message.content && typeof message.content.text === 'string') { // [cite: 1200]
                        statusText = message.content.text; // [cite: 1201]
                        statusComponentHint = message.content.component_hint || statusComponentHint; // [cite: 1201]
                    } else if (message.content) { // [cite: 1201]
                        statusText = String(message.content); // [cite: 1202]
                    }

                    const lowerStatusText = statusText.toLowerCase(); // [cite: 1203]
                    isErrorStatus = lowerStatusText.includes("error"); // [cite: 1203]

                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI(statusText, message.type, { component_hint: statusComponentHint, isError: isErrorStatus }); // [cite: 1204]
                    if (isErrorStatus) { // [cite: 1204]
                        updateGlobalMonitorStatus('error', statusText); // [cite: 1205]
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Error occurred.", status_key: "ERROR", component_hint: "ERROR" }); // [cite: 1206]
                    } else if (lowerStatusText.includes("complete") || lowerStatusText.includes("cancelled") || lowerStatusText.includes("plan proposal cancelled") || lowerStatusText.includes("task context ready")) { // [cite: 1206]
                        updateGlobalMonitorStatus('idle', 'Idle'); // [cite: 1207]
                        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Idle.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1208]
                    }
                    break;
                case 'monitor_log': // [cite: 1209]
                    if (message.content && typeof message.content.text === 'string') { // [cite: 1209]
                        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(message.content); // [cite: 1210]
                    } else {
                        if (typeof message.content === 'string' && typeof addLogEntryToMonitor === 'function') { // [cite: 1210]
                             addLogEntryToMonitor({ text: message.content, log_source: "UNKNOWN_STRING_LOG" }); // [cite: 1211]
                        }
                    }
                    break;
                case 'update_artifacts': // [cite: 1212]
                    if (Array.isArray(message.content)) { // [cite: 1212]
                        const oldArtifacts = StateManager.getCurrentTaskArtifacts(); // [cite: 1213]
                        const oldIndex = StateManager.getCurrentArtifactIndex(); // [cite: 1213]
                        const oldCurrentArtifactFilename = (oldIndex >= 0 && oldIndex < oldArtifacts.length) ? oldArtifacts[oldIndex]?.filename : null; // [cite: 1213]
                        StateManager.setCurrentTaskArtifacts(message.content); // [cite: 1213]
                        let newIndexToSet = -1; // [cite: 1214]
                        const newArtifacts = StateManager.getCurrentTaskArtifacts(); // [cite: 1214]
                        if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_proposal_") && oldCurrentArtifactFilename.endsWith(".md")) { // [cite: 1214]
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename); // [cite: 1215]
                            if (foundNewIndex !== -1) { newIndexToSet = foundNewIndex; // [cite: 1215]
                            } else { const latestPlanProposal = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_proposal_") && art.filename.endsWith(".md")); // [cite: 1216]
                                newIndexToSet = latestPlanProposal ? newArtifacts.indexOf(latestPlanProposal) : (newArtifacts.length > 0 ? 0 : -1); // [cite: 1216]
                            } // [cite: 1217]
                        } else if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_") && oldCurrentArtifactFilename.endsWith(".md")) { // [cite: 1217]
                            const foundNewIndex = newArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename); // [cite: 1218]
                            if (foundNewIndex !== -1) { newIndexToSet = foundNewIndex; // [cite: 1218]
                            } else { const latestPlan = newArtifacts.find(art => art.filename && art.filename.startsWith("_plan_") && art.filename.endsWith(".md")); // [cite: 1219]
                                newIndexToSet = latestPlan ? newArtifacts.indexOf(latestPlan) : (newArtifacts.length > 0 ? 0 : -1); // [cite: 1220]
                            }
                        } else if (newArtifacts.length > 0) { newIndexToSet = 0; // [cite: 1221]
                        } 
                        StateManager.setCurrentArtifactIndex(newIndexToSet); // [cite: 1222]
                        if(typeof updateArtifactDisplayUI === 'function') { updateArtifactDisplayUI(newArtifacts, StateManager.getCurrentArtifactIndex()); } // [cite: 1222]
                    } 
                    break;
                case 'trigger_artifact_refresh': // [cite: 1223]
                    const taskIdToRefresh = message.content?.taskId; // [cite: 1224]
                    if (taskIdToRefresh && taskIdToRefresh === StateManager.getCurrentTaskId()) { // [cite: 1224]
                        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_EVENT] File event detected for task ${taskIdToRefresh}, requesting artifact list update...`, log_source: "SYSTEM_EVENT"}); // [cite: 1225]
                        if (typeof sendWsMessage === 'function') sendWsMessage('get_artifacts_for_task', { taskId: StateManager.getCurrentTaskId() }); // [cite: 1226]
                    } 
                    break;
                case 'available_models': // [cite: 1227]
                    if (message.content && typeof message.content === 'object') { // [cite: 1227]
                        StateManager.setAvailableModels({gemini: message.content.gemini || [], ollama: message.content.ollama || []}); // [cite: 1228]
                        const backendDefaultExecutorLlmId = message.content.default_executor_llm_id || null; // [cite: 1228]
                        const backendRoleDefaults = message.content.role_llm_defaults || {}; // [cite: 1229]
                        if (typeof populateAllLlmSelectorsUI === 'function') { populateAllLlmSelectorsUI(StateManager.getAvailableModels(), backendDefaultExecutorLlmId, backendRoleDefaults); } // [cite: 1229]
                    } 
                    break;
                case 'error_parsing_message': // [cite: 1230]
                    console.error("Error parsing message from WebSocket:", message.content); // [cite: 1231]
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_ERROR] Error parsing WebSocket message: ${message.content}`, log_source: "SYSTEM_ERROR"}); // [cite: 1231]
                    if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Received an unreadable message from the backend.", "status_message", {component_hint: "ERROR", isError: true}); // [cite: 1232]
                    break;
                default: // [cite: 1233]
                    console.warn("[Script.js] Received unknown message type:", message.type, "Content:", message.content); // [cite: 1234]
                    if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_WARNING] Unknown message type received: ${message.type}`, log_source: "SYSTEM_WARNING"}); // [cite: 1234]
            } // [cite: 1235]
        } catch (error) {
            console.error("[Script.js] Failed to process dispatched WS message:", error, "Original Message:", message); // [cite: 1236]
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_ERROR] Error processing dispatched message: ${error.message}.`, log_source: "SYSTEM_ERROR"}); // [cite: 1236]
            updateGlobalMonitorStatus('error', 'Processing Error'); // [cite: 1236]
            if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); // [cite: 1237]
        }
    };
    function updateGlobalMonitorStatus(status, text) { // [cite: 1238]
        StateManager.setIsAgentRunning(status === 'running' || status === 'cancelling'); // [cite: 1239]
        if (typeof updateMonitorStatusUI === 'function') { // [cite: 1239]
            updateMonitorStatusUI(status, text, StateManager.getIsAgentRunning()); // [cite: 1240]
        } 
    }
    function handleTokenUsageUpdate(lastCallUsage = null) { // [cite: 1240]
        StateManager.updateCurrentTaskTotalTokens(lastCallUsage); // [cite: 1241]
        if (typeof updateTokenDisplayUI === 'function') { // [cite: 1241]
            updateTokenDisplayUI(lastCallUsage, StateManager.getCurrentTaskTotalTokens()); // [cite: 1242]
        } 
    }
    function resetTaskTokenTotalsGlobally() { // [cite: 1242]
        StateManager.resetCurrentTaskTotalTokens(); // [cite: 1243]
        if (typeof resetTokenDisplayUI === 'function') { // [cite: 1243]
            resetTokenDisplayUI(); // [cite: 1244]
        } 
    }
    function clearChatAndMonitor(addLog = true) { // [cite: 1244]
        if (typeof clearChatMessagesUI === 'function') clearChatMessagesUI(); // [cite: 1245]
        if (typeof clearMonitorLogUI === 'function') clearMonitorLogUI(); // [cite: 1245]
        StateManager.setCurrentTaskArtifacts([]); // [cite: 1245]
        StateManager.setCurrentArtifactIndex(-1); // [cite: 1246]
        if (typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); // [cite: 1246]
        if (addLog && typeof addLogEntryToMonitor === 'function') { // [cite: 1246]
            addLogEntryToMonitor({text: "[SYSTEM_EVENT] Cleared context.", log_source: "SYSTEM_EVENT"}); // [cite: 1247]
        } 
        resetTaskTokenTotalsGlobally(); // [cite: 1247]
        StateManager.setCurrentDisplayedPlan(null); // [cite: 1247]
        StateManager.setCurrentPlanProposalId(null); // [cite: 1247]
    };
    const handleTaskSelection = (taskId) => { // [cite: 1248]
        console.log(`[MainScript] Task selection requested for: ${taskId}`); // [cite: 1249]
        const previousActiveTaskId = StateManager.getCurrentTaskId(); // [cite: 1249]
        
        StateManager.setIsAgentRunning(false); // [cite: 1250]
        const selectedTaskObjectForTitle = StateManager.getTasks().find(t => t.id === taskId); // [cite: 1250]
        const taskTitleForStatus = selectedTaskObjectForTitle ? selectedTaskObjectForTitle.title : (taskId ? 'Selected Task' : 'New Task'); // [cite: 1251]
        
        updateGlobalMonitorStatus('idle', `Initializing ${taskTitleForStatus}...`); // [cite: 1252]
        if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1252]
            showAgentThinkingStatusInUI(true, { // [cite: 1252]
                message: `Initializing ${taskTitleForStatus}...`, // [cite: 1253]
                status_key: "TASK_INIT", 
                component_hint: "SYSTEM" 
            }); // [cite: 1253]
        }
        if (typeof clearCurrentMajorStepUI === 'function') { 
             clearCurrentMajorStepUI(); // [cite: 1254]
        }

        StateManager.selectTask(taskId); // [cite: 1255]
        const newActiveTaskId = StateManager.getCurrentTaskId(); // [cite: 1255]
        console.log(`[MainScript] StateManager updated. Previous active: ${previousActiveTaskId}, New active: ${newActiveTaskId}`); // [cite: 1256]
        if (typeof renderTaskList === 'function') { renderTaskList(StateManager.getTasks(), newActiveTaskId); } // [cite: 1256]
        resetTaskTokenTotalsGlobally(); // [cite: 1256]
        const selectedTaskObject = StateManager.getTasks().find(t => t.id === newActiveTaskId); // [cite: 1257]
        
        if (newActiveTaskId && selectedTaskObject) { // [cite: 1257]
            clearChatAndMonitor(false); // [cite: 1258]
            if (typeof sendWsMessage === 'function') sendWsMessage("context_switch", { task: selectedTaskObject.title, taskId: selectedTaskObject.id }); // [cite: 1259]
            // [cite: 1260]
            // [cite: 1261]
        } else if (!newActiveTaskId) { // [cite: 1261]
            clearChatAndMonitor(); // [cite: 1262]
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("No task selected.", "status_message", {component_hint: "SYSTEM"}); // [cite: 1262]
            if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM_EVENT] No task selected.", log_source: "SYSTEM_EVENT"}); // [cite: 1263]
            updateGlobalMonitorStatus('idle', 'No Task'); // [cite: 1263]
            if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1264]
                showAgentThinkingStatusInUI(true, { message: "No task selected.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1265]
            }
        }
    };
    const handleNewTaskCreation = () => { const newTask = StateManager.addTask(); handleTaskSelection(newTask.id); }; // [cite: 1266]
    const handleTaskDeletion = (taskId, taskTitle) => { const wasActiveTask = StateManager.getCurrentTaskId() === taskId; StateManager.deleteTask(taskId); // [cite: 1267]
        if (typeof sendWsMessage === 'function') sendWsMessage("delete_task", { taskId: taskId }); if (wasActiveTask) { handleTaskSelection(StateManager.getCurrentTaskId()); // [cite: 1268, 1269]
        } else { if (typeof renderTaskList === 'function') { renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); } } }; // [cite: 1269]
    const handleTaskRename = (taskId, oldTitle, newTitle) => { if (StateManager.renameTask(taskId, newTitle)) { if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); // [cite: 1270]
        if (taskId === StateManager.getCurrentTaskId()) { if (typeof updateCurrentTaskTitleUI === 'function') updateCurrentTaskTitleUI(StateManager.getTasks(), StateManager.getCurrentTaskId()); // [cite: 1271]
        } if (typeof sendWsMessage === 'function') sendWsMessage("rename_task", { taskId: taskId, newName: newTitle }); } }; // [cite: 1272]
    const handleSendMessageFromUI = (messageText) => { // [cite: 1273]
        if (!StateManager.getCurrentTaskId()) { alert("Please select or create a task first."); // [cite: 1274]
            return; } // [cite: 1274]
        if (StateManager.getIsAgentRunning()) { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Agent is currently busy. Please wait or stop the current process.", "status_message", {component_hint: "SYSTEM"}); // [cite: 1275]
            return; } // [cite: 1275]
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI(messageText, 'user'); // [cite: 1275]
        if (typeof addMessageToInputHistory === 'function') addMessageToInputHistory(messageText); // [cite: 1276]
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(false); // [cite: 1277]
        if (typeof sendWsMessage === 'function') sendWsMessage("user_message", { content: messageText }); // [cite: 1278]
        else { if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Cannot send message. Connection issue.", "status_message", {component_hint: "ERROR", isError: true});} // [cite: 1278]
        updateGlobalMonitorStatus('running', 'Classifying intent...'); // [cite: 1278]
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Classifying intent...", status_key: "INTENT_CLASSIFICATION_START", component_hint: "INTENT_CLASSIFIER" }); // [cite: 1279]
    };
    const handlePlanConfirmRequest = (planId) => { // [cite: 1280]
        console.log(`[Script.js] Plan confirmed by user for plan ID: ${planId}`); // [cite: 1281]
        const currentPlan = StateManager.getCurrentDisplayedPlan(); // [cite: 1281]
        if (!currentPlan) { // [cite: 1281]
            console.error(`[Script.js] Cannot confirm plan ${planId}: No plan found in state.`); // [cite: 1282]
            if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Error: Could not find plan to confirm.", "status_message", {component_hint: "ERROR", isError: true}); // [cite: 1282]
            updateGlobalMonitorStatus('error', 'Plan Confirmation Error'); // [cite: 1283]
            return;
        }
        if (typeof sendWsMessage === 'function') { // [cite: 1283]
            sendWsMessage('execute_confirmed_plan', { plan_id: planId, confirmed_plan: currentPlan }); // [cite: 1284]
        }
        if (typeof transformToConfirmedPlanUI === 'function') { // [cite: 1284]
            transformToConfirmedPlanUI(planId); // [cite: 1285]
        }
        updateGlobalMonitorStatus('running', 'Executing Plan...'); // [cite: 1285]
    };
    const handlePlanCancelRequest = (planId) => { // [cite: 1286]
        console.log(`[Script.js] Plan cancelled by user for plan ID: ${planId}`); // [cite: 1287]
        if (typeof sendWsMessage === 'function') { // [cite: 1287]
            sendWsMessage('cancel_plan_proposal', { plan_id: planId }); // [cite: 1288]
        }
        const planConfirmContainer = chatMessagesContainer.querySelector(`.plan-confirmation-wrapper[data-plan-id="${planId}"]`); // [cite: 1289]
        if (planConfirmContainer) { // [cite: 1289]
            planConfirmContainer.remove(); // [cite: 1290]
        }
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Plan proposal cancelled by user.", "status_message", {component_hint: "SYSTEM"}); // [cite: 1290]
        updateGlobalMonitorStatus('idle', 'Idle'); // [cite: 1291]
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Idle.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1291]
        StateManager.setCurrentDisplayedPlan(null); // [cite: 1291]
        StateManager.setCurrentPlanProposalId(null); // [cite: 1291]
    };
    const handlePlanViewDetailsRequest = (planId, isNowVisible) => { if (typeof addLogEntryToMonitor === 'function') { addLogEntryToMonitor({text: `[UI_ACTION] User toggled plan details for proposal ${planId}. Details are now ${isNowVisible ? 'visible' : 'hidden'}.`, log_source: "UI_EVENT"}); // [cite: 1292]
    } }; // [cite: 1293]
    const handleStopAgentRequest = () => { if (StateManager.getIsAgentRunning()) { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM_EVENT] Stop request sent by user.", log_source: "SYSTEM_EVENT"}); // [cite: 1293]
        if (typeof sendWsMessage === 'function') sendWsMessage("cancel_agent", {}); updateGlobalMonitorStatus('cancelling', 'Cancelling...'); if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Cancelling...", status_key: "CANCELLING", component_hint: "SYSTEM" }); // [cite: 1294]
    } }; // [cite: 1295]
    const handleArtifactNavigation = (direction) => { let currentIndex = StateManager.getCurrentArtifactIndex(); const currentArtifacts = StateManager.getCurrentTaskArtifacts(); let newIndex = currentIndex; // [cite: 1295]
        if (direction === "prev") { if (currentIndex > 0) newIndex = currentIndex - 1; // [cite: 1296]
        } else if (direction === "next") { if (currentIndex < currentArtifacts.length - 1) newIndex = currentIndex + 1; // [cite: 1297]
        } if (newIndex !== currentIndex) { StateManager.setCurrentArtifactIndex(newIndex); if(typeof updateArtifactDisplayUI === 'function') { updateArtifactDisplayUI(currentArtifacts, newIndex); } } }; // [cite: 1298]
    const handleExecutorLlmChange = (selectedId) => { StateManager.setCurrentExecutorLlmId(selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_llm", { llm_id: selectedId }); }}; // [cite: 1299]
    const handleRoleLlmChange = (role, selectedId) => { StateManager.setRoleLlmOverride(role, selectedId); if (typeof sendWsMessage === 'function') { sendWsMessage("set_session_role_llm", { role: role, llm_id: selectedId }); // [cite: 1300]
    }}; // [cite: 1301]
    const handleThinkingStatusClick = () => { if (typeof scrollToBottomMonitorLog === 'function') { scrollToBottomMonitorLog(); } }; // [cite: 1302]
    const handleWsOpen = (event) => { // [cite: 1302]
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_CONNECTION] WebSocket connection established.`, log_source: "SYSTEM_CONNECTION"}); // [cite: 1303]
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("Connected to backend.", "status_message", {component_hint: "SYSTEM"}); // [cite: 1303]
        updateGlobalMonitorStatus('idle', 'Idle'); // [cite: 1303]
        if (typeof sendWsMessage === 'function') { // [cite: 1304]
            sendWsMessage("get_available_models", {}); // [cite: 1305]
            const activeTaskFromStorage = StateManager.getTasks().find(task => task.id === StateManager.getCurrentTaskId()); // [cite: 1305]
            if (StateManager.getCurrentTaskId() && activeTaskFromStorage) { // [cite: 1305]
                console.log(`[Script.js] WS Open: Active task ${activeTaskFromStorage.id} found. Sending context_switch.`); // [cite: 1307]
                StateManager.setIsAgentRunning(false); // [cite: 1307]
                 if (typeof showAgentThinkingStatusInUI === 'function') { // [cite: 1307]
                    showAgentThinkingStatusInUI(true, { // [cite: 1308]
                        message: `Initializing Task: ${activeTaskFromStorage.title}...`, // [cite: 1308]
                        status_key: "TASK_INIT", // [cite: 1309]
                        component_hint: "SYSTEM" 
                    }); // [cite: 1309]
                }
                sendWsMessage("context_switch", { task: activeTaskFromStorage.title, taskId: activeTaskFromStorage.id }); // [cite: 1310]
            } else { 
                console.log("[Script.js] WS Open: No active task found in StateManager on initial load."); // [cite: 1311]
                updateGlobalMonitorStatus('idle', 'No Task'); // [cite: 1311]
                if(typeof clearArtifactDisplayUI === 'function') clearArtifactDisplayUI(); // [cite: 1311]
                resetTaskTokenTotalsGlobally(); // [cite: 1311]
                if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "No task selected.", status_key: "IDLE", component_hint: "SYSTEM" }); // [cite: 1312]
            } 
        } 
    };
    const handleWsClose = (event) => { let reason = event.reason || 'No reason given'; let advice = ""; // [cite: 1313]
        if (event.code === 1000 || event.wasClean) { reason = "Normal"; } else { reason = `Abnormal (Code: ${event.code})`; // [cite: 1314]
            advice = " Backend down or network issue?"; } if (typeof addChatMessageToUI === 'function') addChatMessageToUI(`Connection closed.${advice}`, "status_message", {component_hint: "ERROR", isError: true}); // [cite: 1315]
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_CONNECTION] WebSocket disconnected. ${reason}`, log_source: "SYSTEM_CONNECTION"}); updateGlobalMonitorStatus('disconnected', 'Disconnected');  if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); // [cite: 1316]
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Disconnected.", status_key: "DISCONNECTED", component_hint: "ERROR" }); }; // [cite: 1317]
    const handleWsError = (event, isCreationError = false) => { const errorMsg = isCreationError ? "FATAL: Failed to initialize WebSocket connection." // [cite: 1318]
        : "ERROR: Cannot connect to backend."; if (typeof addChatMessageToUI === 'function') addChatMessageToUI(errorMsg, "status_message", {component_hint: "ERROR", isError: true}); // [cite: 1319]
        if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[SYSTEM_ERROR] WebSocket error occurred.`, log_source: "SYSTEM_ERROR"}); // [cite: 1320]
        updateGlobalMonitorStatus('error', isCreationError ? 'Connection Init Failed' : 'Connection Error'); if (typeof disableAllLlmSelectorsUI === 'function') disableAllLlmSelectorsUI(); // [cite: 1321]
        if (typeof showAgentThinkingStatusInUI === 'function') showAgentThinkingStatusInUI(true, { message: "Connection Error.", status_key: "ERROR", component_hint: "ERROR" }); }; // [cite: 1322]
    // Initialize UI Modules // [cite: 1323]
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskCreation); // [cite: 1324]
    }
    document.body.addEventListener('click', event => { if (event.target.classList.contains('action-btn')) { const commandText = event.target.textContent.trim(); if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: `[UI_ACTION] Clicked: ${commandText}`, log_source: "UI_EVENT"}); if (typeof sendWsMessage === 'function') sendWsMessage("action_command", { command: commandText }); } }); // [cite: 1324]
    if (typeof initTaskUI === 'function') { initTaskUI( { taskListUl: taskListUl, currentTaskTitleEl: currentTaskTitleElement, uploadFileBtn: uploadFileButtonElement }, { onTaskSelect: handleTaskSelection, onNewTask: handleNewTaskCreation, onDeleteTask: handleTaskDeletion, onRenameTask: handleTaskRename }); // [cite: 1325]
        if (typeof renderTaskList === 'function') renderTaskList(StateManager.getTasks(), StateManager.getCurrentTaskId()); } // [cite: 1326]
    if (typeof initChatUI === 'function') { initChatUI( { chatMessagesContainer: chatMessagesContainer, agentThinkingStatusEl: agentThinkingStatusElement, chatTextareaEl: chatTextarea, chatSendButtonEl: chatSendButton }, { onSendMessage: handleSendMessageFromUI, onThinkingStatusClick: handleThinkingStatusClick }); // [cite: 1326]
    } // [cite: 1327]
    if (typeof initMonitorUI === 'function') { initMonitorUI( { monitorLogArea: monitorLogAreaElement, statusDot: statusDotElement, monitorStatusText: monitorStatusTextElement, stopButton: stopButtonElement }, { onStopAgent: handleStopAgentRequest }); // [cite: 1328]
    }
    if (typeof initArtifactUI === 'function') { initArtifactUI( { monitorArtifactArea: monitorArtifactArea, artifactNav: artifactNav, prevBtn: artifactPrevBtn, nextBtn: artifactNextBtn, counterEl: artifactCounterElement }, { onNavigate: handleArtifactNavigation }); // [cite: 1329]
        if(typeof updateArtifactDisplayUI === 'function') updateArtifactDisplayUI(StateManager.getCurrentTaskArtifacts(), StateManager.getCurrentArtifactIndex()); } // [cite: 1329]
    if (typeof initLlmSelectorsUI === 'function') { initLlmSelectorsUI( { executorLlmSelect: executorLlmSelectElement, roleSelectors: roleSelectorsMetaForInit }, { onExecutorLlmChange: handleExecutorLlmChange, onRoleLlmChange: handleRoleLlmChange }); // [cite: 1330]
    }
    if (typeof initTokenUsageUI === 'function') { initTokenUsageUI({ lastCallTokensEl: lastCallTokensElement, taskTotalTokensEl: taskTotalTokensElement }); resetTaskTokenTotalsGlobally(); // [cite: 1330]
    } // [cite: 1331]
    if (typeof initFileUploadUI === 'function') { initFileUploadUI( { fileUploadInputEl: fileUploadInputElement, uploadFileButtonEl: uploadFileButtonElement }, { httpBackendBaseUrl: httpBackendBaseUrl }, { getCurrentTaskId: StateManager.getCurrentTaskId, addLog: (logData) => { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor(logData); }, addChatMsg: (msgText, msgType, options) => { if (typeof addChatMessageToUI === 'function') addChatMessageToUI(msgText, msgType, options); } }); // [cite: 1332]
    }

    // Establish WebSocket Connection
    if (typeof connectWebSocket === 'function') { if (typeof addLogEntryToMonitor === 'function') addLogEntryToMonitor({text: "[SYSTEM_CONNECTION] Attempting to connect to backend...", log_source: "SYSTEM_CONNECTION"}); // [cite: 1333]
        updateGlobalMonitorStatus('disconnected', 'Connecting...'); connectWebSocket(handleWsOpen, handleWsClose, handleWsError); // [cite: 1333]
    } else { console.error("connectWebSocket function not found."); // [cite: 1334]
        if (typeof addChatMessageToUI === 'function') addChatMessageToUI("ERROR: WebSocket manager not loaded.", "status_message", {component_hint: "ERROR", isError: true}); updateGlobalMonitorStatus('error', 'Initialization Error'); } // [cite: 1334]
}); // [cite: 1335]