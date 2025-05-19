/**
 * This script handles the frontend logic for the AI Agent UI.
 * Includes:
 * - WebSocket communication
 * - DOM manipulation & event handling
 * - Task management (load, save, render, select, new, delete, rename)
 * - Chat message display and input history
 * - Basic Markdown formatting for chat messages
 * - LLM selection (Executor and Role-specific overrides) and synchronization with backend
 * - Monitor status updates
 * - Agent cancellation requests
 * - File uploads
 * - Artifact viewer navigation
 * - LLM Token Usage tracking
 * - Plan display for user confirmation and execution initiation
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    const taskListUl = document.getElementById('task-list');
    const newTaskButton = document.getElementById('new-task-button');
    const chatMessagesContainer = document.getElementById('chat-messages');
    const monitorLogAreaElement = document.getElementById('monitor-log-area');
    const monitorArtifactAreaElement = document.getElementById('monitor-artifact-area');
    const artifactNavElement = document.querySelector('.artifact-nav');
    const artifactPrevBtn = document.getElementById('artifact-prev-btn');
    const artifactNextBtn = document.getElementById('artifact-next-btn');
    const artifactCounterElement = document.getElementById('artifact-counter');
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const currentTaskTitleElement = document.getElementById('current-task-title');
    const monitorStatusContainer = document.getElementById('monitor-status-container');
    const statusDotElement = document.getElementById('status-dot');
    const monitorStatusTextElement = document.getElementById('monitor-status-text');
    const stopButton = document.getElementById('stop-button');
    const fileUploadInput = document.getElementById('file-upload-input');
    const uploadFileButton = document.getElementById('upload-file-button');
    const agentThinkingStatusElement = document.getElementById('agent-thinking-status');
    const tokenUsageAreaElement = document.getElementById('token-usage-area');
    const lastCallTokensElement = document.getElementById('last-call-tokens');
    const taskTotalTokensElement = document.getElementById('task-total-tokens');

    const executorLlmSelectElement = document.getElementById('llm-select');
    const intentLlmSelectElement = document.getElementById('intent-llm-select');
    const plannerLlmSelectElement = document.getElementById('planner-llm-select');
    const controllerLlmSelectElement = document.getElementById('controller-llm-select');
    const evaluatorLlmSelectElement = document.getElementById('evaluator-llm-select');

    const roleSelectorsMeta = [
        { element: intentLlmSelectElement, role: 'intent_classifier', storageKey: 'sessionIntentLlmId', label: 'Intent Classifier' },
        { element: plannerLlmSelectElement, role: 'planner', storageKey: 'sessionPlannerLlmId', label: 'Planner' },
        { element: controllerLlmSelectElement, role: 'controller', storageKey: 'sessionControllerLlmId', label: 'Controller' },
        { element: evaluatorLlmSelectElement, role: 'evaluator', storageKey: 'sessionEvaluatorLlmId', label: 'Evaluator' }
    ];

    let tasks = [];
    let currentTaskId = null;
    let taskCounter = 0;
    const STORAGE_KEY = 'aiAgentTasks';
    const COUNTER_KEY = 'aiAgentTaskCounter';
    let isLoadingHistory = false;
    let availableModels = { gemini: [], ollama: [] };

    let currentExecutorLlmId = "";
    let sessionRoleLlmOverrides = {
        intent_classifier: "",
        planner: "",
        controller: "",
        evaluator: ""
    };

    let isAgentRunning = false;
    let chatInputHistory = [];
    const MAX_CHAT_HISTORY = 10;
    let chatHistoryIndex = -1;
    let currentInputBuffer = "";
    let currentTaskArtifacts = [];
    let currentArtifactIndex = -1;
    let currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
    let currentDisplayedPlan = null;

    // Flags to manage artifact content fetching state
    let isFetchingArtifactContent = false;
    // Stores the URL of the artifact whose content is currently being fetched or was last fetched.
    // This helps in deciding whether to re-fetch or if a fetch is already in progress for the *same* artifact URL.
    let artifactContentFetchUrl = null;


    const wsUrl = 'ws://localhost:8765';
    const httpBackendBaseUrl = 'http://localhost:8766';
    let socket;
    window.socket = null;

    const updateMonitorStatus = (status, text) => {
        if (!statusDotElement || !monitorStatusTextElement || !stopButton) return;
        statusDotElement.classList.remove('idle', 'running', 'error', 'disconnected');
        let statusText = text;
        switch (status) {
            case 'idle':
                statusDotElement.classList.add('idle'); statusText = text || 'Idle'; isAgentRunning = false;
                stopButton.style.display = 'none'; stopButton.disabled = true;
                if (agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                break;
            case 'running':
                statusDotElement.classList.add('running'); statusText = text || 'Running...'; isAgentRunning = true;
                stopButton.style.display = 'inline-block'; stopButton.disabled = false;
                break;
            case 'error':
                statusDotElement.classList.add('error'); statusText = text || 'Error'; isAgentRunning = false;
                stopButton.style.display = 'none'; stopButton.disabled = true;
                if (agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                break;
            case 'cancelling':
                statusDotElement.classList.add('running'); statusText = text || 'Cancelling...'; isAgentRunning = true;
                stopButton.disabled = true;
                if (agentThinkingStatusElement) {
                    agentThinkingStatusElement.textContent = 'Cancelling...';
                    agentThinkingStatusElement.style.display = 'block';
                }
                break;
            case 'disconnected':
            default:
                statusDotElement.classList.add('disconnected'); statusText = text || 'Disconnected'; isAgentRunning = false;
                stopButton.style.display = 'none'; stopButton.disabled = true;
                if (agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                break;
        }
        monitorStatusTextElement.textContent = statusText;
    };

    const updateTokenDisplay = (lastCallUsage = null) => {
        if (!lastCallTokensElement || !taskTotalTokensElement) return;
        if (lastCallUsage) {
            const lastInput = lastCallUsage.input_tokens || 0;
            const lastOutput = lastCallUsage.output_tokens || 0;
            const lastTotal = lastCallUsage.total_tokens || (lastInput + lastOutput);
            lastCallTokensElement.textContent = `In: ${lastInput}, Out: ${lastOutput}, Total: ${lastTotal} (${lastCallUsage.model_name || 'N/A'})`;
            currentTaskTotalTokens.input += lastInput;
            currentTaskTotalTokens.output += lastOutput;
            currentTaskTotalTokens.total += lastTotal;
        }
        taskTotalTokensElement.textContent = `In: ${currentTaskTotalTokens.input}, Out: ${currentTaskTotalTokens.output}, Total: ${currentTaskTotalTokens.total}`;
    };

    const resetTaskTokenTotals = () => {
        currentTaskTotalTokens = { input: 0, output: 0, total: 0 };
        if(lastCallTokensElement) lastCallTokensElement.textContent = "N/A";
        updateTokenDisplay();
    };

    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        addMonitorLog("[SYSTEM] Attempting to connect to backend...");
        updateMonitorStatus('disconnected', 'Connecting...');
        chatMessagesContainer.querySelectorAll('.connection-status').forEach(el => el.remove());
        try {
            if (window.socket && window.socket.readyState !== WebSocket.CLOSED) {
                window.socket.close(1000, "Reconnecting");
            }
            socket = new WebSocket(wsUrl);
            window.socket = socket;
        } catch (error) {
            console.error("Fatal Error creating WebSocket object:", error);
            addChatMessage("FATAL: Failed to initialize WebSocket connection.", "status");
            addMonitorLog(`[SYSTEM] FATAL Error creating WebSocket: ${error.message}`);
            updateMonitorStatus('error', 'Connection Failed');
            window.socket = null;
            disableAllLlmSelectors();
            return;
        }

        socket.onopen = (event) => {
            console.log("WebSocket connection opened successfully.");
            addMonitorLog(`[SYSTEM] WebSocket connection established.`);
            addChatMessage("Connected to backend.", "status");
            updateMonitorStatus('idle', 'Idle');
            sendWsMessage("get_available_models", {});
            if (currentTaskId) {
                const currentTask = tasks.find(task => task.id === currentTaskId);
                if (currentTask) {
                    sendWsMessage("context_switch", { task: currentTask.title, taskId: currentTask.id });
                } else {
                    currentTaskId = null; updateMonitorStatus('idle', 'No Task'); updateArtifactDisplay(); resetTaskTokenTotals();
                }
            } else {
                updateMonitorStatus('idle', 'No Task'); updateArtifactDisplay(); resetTaskTokenTotals();
            }
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                switch (message.type) {
                    case 'history_start':
                        isLoadingHistory = true; clearChatAndMonitor(false); addChatMessage(`Loading history...`, "status");
                        updateMonitorStatus('running', 'Loading History...');
                        break;
                    case 'history_end':
                        isLoadingHistory = false;
                        const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                        if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                        scrollToBottom(chatMessagesContainer); scrollToBottom(monitorLogAreaElement);
                        updateMonitorStatus('idle', 'Idle');
                        break;
                    case 'agent_thinking_update':
                        if (agentThinkingStatusElement && message.content && message.content.status) {
                            agentThinkingStatusElement.textContent = message.content.status;
                            agentThinkingStatusElement.style.display = 'block';
                            const lastMessage = chatMessagesContainer.querySelector('.message:last-child:not(.agent-thinking-status)');
                                if (lastMessage) {
                                    chatMessagesContainer.insertBefore(agentThinkingStatusElement, lastMessage.nextSibling);
                                } else {
                                    chatMessagesContainer.appendChild(agentThinkingStatusElement);
                                }
                            scrollToBottom(chatMessagesContainer);
                        }
                        break;
                    case 'agent_message':
                        if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                        addChatMessage(message.content, 'agent');
                        break;
                    case 'llm_token_usage':
                        if (message.content && typeof message.content === 'object') {
                            updateTokenDisplay(message.content);
                        }
                        break;
                    case 'display_plan_for_confirmation':
                        console.log("Received display_plan_for_confirmation:", message.content);
                        if (message.content && message.content.human_summary && message.content.structured_plan) {
                            currentDisplayedPlan = message.content.structured_plan;
                            displayPlanForConfirmation(message.content.human_summary, message.content.structured_plan);
                            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                        } else {
                            console.error("Invalid plan data received:", message.content);
                            addChatMessage("Error: Received invalid plan from backend.", "status");
                        }
                        break;
                    case 'user': addChatMessage(message.content, 'user'); break;
                    case 'status_message':
                        const lowerContent = message.content.toLowerCase();
                        if (lowerContent.includes("connect") || lowerContent.includes("clos") || lowerContent.includes("error")) {
                            addChatMessage(message.content, 'status');
                        }
                        if (lowerContent.includes("error")) {
                            updateMonitorStatus('error', message.content);
                        } else if (lowerContent.includes("complete") || lowerContent.includes("cancelled") || lowerContent.includes("plan confirmed")) {
                            if (!lowerContent.includes("plan confirmed. executing steps...")) {
                                updateMonitorStatus('idle', 'Idle');
                            }
                        }
                        if (lowerContent.includes("complete") || lowerContent.includes("error") || lowerContent.includes("cancelled")) {
                            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                        }
                        break;
                    case 'monitor_log':
                        addMonitorLog(message.content);
                        if (message.content.includes("[Agent Finish]") || message.content.includes("Error]")) {
                            if(isAgentRunning && !message.content.includes("PLAN EXECUTION LOOP NOT YET IMPLEMENTED")) {
                                updateMonitorStatus('idle', 'Idle');
                            }
                            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
                        }
                        break;
                    case 'update_artifacts':
                        if (Array.isArray(message.content)) {
                            const oldArtifactCount = currentTaskArtifacts.length;
                            const oldCurrentArtifactFilename = (currentArtifactIndex >= 0 && currentArtifactIndex < oldArtifactCount)
                                ? currentTaskArtifacts[currentArtifactIndex]?.filename
                                : null;

                            currentTaskArtifacts = message.content;

                            if (oldCurrentArtifactFilename && oldCurrentArtifactFilename.startsWith("_plan_") && oldCurrentArtifactFilename.endsWith(".md")) {
                                const newIndex = currentTaskArtifacts.findIndex(art => art.filename === oldCurrentArtifactFilename);
                                if (newIndex !== -1) {
                                    currentArtifactIndex = newIndex;
                                } else {
                                    const latestPlan = currentTaskArtifacts.find(art => art.filename && art.filename.startsWith("_plan_") && art.filename.endsWith(".md"));
                                    currentArtifactIndex = latestPlan ? currentTaskArtifacts.indexOf(latestPlan) : (currentTaskArtifacts.length > 0 ? 0 : -1);
                                }
                            } else if (currentTaskArtifacts.length > 0) {
                                currentArtifactIndex = 0;
                            } else {
                                currentArtifactIndex = -1;
                            }
                            isFetchingArtifactContent = false; // Reset flag before display update
                            artifactContentFetchUrl = null; // Allow re-fetch if artifact list changed or different artifact selected
                            updateArtifactDisplay();
                        }
                        break;
                    case 'trigger_artifact_refresh':
                        const taskIdToRefresh = message.content?.taskId;
                        if (taskIdToRefresh && taskIdToRefresh === currentTaskId) {
                            addMonitorLog(`[SYSTEM] File event detected for task ${taskIdToRefresh}, requesting artifact list update...`);
                            sendWsMessage('get_artifacts_for_task', { taskId: currentTaskId });
                        }
                        break;
                    case 'available_models':
                        if (message.content && typeof message.content === 'object') {
                            availableModels.gemini = message.content.gemini || [];
                            availableModels.ollama = message.content.ollama || [];

                            const backendDefaultExecutorLlmId = message.content.default_executor_llm_id || null;
                            const backendRoleDefaults = message.content.role_llm_defaults || {};

                            populateAllLlmSelectors(backendDefaultExecutorLlmId, backendRoleDefaults);
                        }
                        break;
                    default:
                        console.warn("Received unknown message type:", message.type, "Content:", message.content);
                        addMonitorLog(`[SYSTEM] Unknown message type received: ${message.type}`);
                }
            } catch (error) {
                console.error("Failed to parse/process WS message:", error, "Data:", event.data);
                addMonitorLog(`[SYSTEM] Error processing message: ${error.message}.`);
                updateMonitorStatus('error', 'Processing Error');
                if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
            }
        };

        socket.onerror = (event) => {
            console.error("WebSocket error event:", event);
            addChatMessage("ERROR: Cannot connect to backend.", "status", true);
            addMonitorLog(`[SYSTEM] WebSocket error occurred.`);
            updateMonitorStatus('error', 'Connection Error');
            window.socket = null;
            disableAllLlmSelectors();
            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
        };
        socket.onclose = (event) => {
            console.log(`WebSocket closed. Code: ${event.code}, Reason: '${event.reason || 'No reason given'}' Clean close: ${event.wasClean}`);
            let reason = event.reason || 'No reason given'; let advice = "";
            if (event.code === 1000 || event.wasClean) { reason = "Normal"; }
            else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down or network issue?"; }
            addChatMessage(`Connection closed.${advice}`, "status", true);
            addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`);
            updateMonitorStatus('disconnected', 'Disconnected');
            window.socket = null;
            disableAllLlmSelectors();
            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
        };
    };

    const disableAllLlmSelectors = () => {
        if (executorLlmSelectElement) {
            executorLlmSelectElement.innerHTML = '<option value="">Connection Error</option>';
            executorLlmSelectElement.disabled = true;
        }
        roleSelectorsMeta.forEach(selInfo => {
            if (selInfo.element) {
                selInfo.element.innerHTML = '<option value="">Connection Error</option>';
                selInfo.element.disabled = true;
            }
        });
    };

    const scrollToBottom = (element) => { if (!element) return; element.scrollTop = element.scrollHeight; };

    const formatMessageContent = (text) => {
        let formattedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => { const escapedCode = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); const langClass = lang ? ` class="language-${lang}"` : ''; return `<pre><code${langClass}>${escapedCode}</code></pre>`; });
        formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');
        formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => { const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); if (linkText.includes('&lt;') || linkText.includes('&gt;')) return match; return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`; });
        formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
        formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
        formattedText = formattedText.replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');
        const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
        for (let i = 0; i < parts.length; i += 2) { parts[i] = parts[i].replace(/\n/g, '<br>'); }
        formattedText = parts.join('');
        return formattedText;
    };

    const addChatMessage = (text, type = 'agent', doScroll = true) => {
        if (!chatMessagesContainer) { console.error("Chat container missing!"); return null; }
        if (type === 'status') {
            const lowerText = text.toLowerCase();
            if (!(lowerText.includes("connect") || lowerText.includes("clos") || lowerText.includes("error"))) {
                console.log("Skipping non-critical status message in chat:", text);
                return null;
            }
        }
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `message-${type}`);
        if (type === 'status') {
            const lowerText = text.toLowerCase();
            if (lowerText.includes("connect") || lowerText.includes("clos")) { messageElement.classList.add('connection-status'); }
            if (lowerText.includes("error")) { messageElement.classList.add('error-message'); }
        }
        if (type === 'user') { messageElement.classList.add('user-message'); }
        if (type === 'agent') { messageElement.classList.add('agent-message'); }
        messageElement.innerHTML = formatMessageContent(text);
        if (agentThinkingStatusElement && agentThinkingStatusElement.style.display !== 'none' && messageElement !== agentThinkingStatusElement) {
                chatMessagesContainer.insertBefore(agentThinkingStatusElement, null);
        }
        chatMessagesContainer.appendChild(messageElement);
        if (doScroll) scrollToBottom(chatMessagesContainer);
        return messageElement;
    };

    const displayPlanForConfirmation = (humanSummary, structuredPlan) => {
        if (!chatMessagesContainer) return;
        const existingPlanUI = chatMessagesContainer.querySelector('.plan-confirmation-container');
        if (existingPlanUI) existingPlanUI.remove();

        const planContainer = document.createElement('div');
        planContainer.className = 'message message-system plan-confirmation-container';

        const title = document.createElement('h4');
        title.textContent = "Agent's Proposed Plan:";
        planContainer.appendChild(title);

        const summaryP = document.createElement('p');
        summaryP.className = 'plan-summary';
        summaryP.innerHTML = formatMessageContent(humanSummary);
        planContainer.appendChild(summaryP);

        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'plan-steps-details';
        detailsDiv.style.display = 'none';
        const ol = document.createElement('ol');
        structuredPlan.forEach(step => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${step.step_id}. ${formatMessageContent(step.description)}</strong>
                            ${step.tool_to_use && step.tool_to_use !== "None" ? `<br><span class="step-tool">Tool: ${step.tool_to_use}</span>` : ''}
                            ${step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContent(step.tool_input_instructions)}</span>` : ''}
                            <br><span class="step-expected">Expected: ${formatMessageContent(step.expected_outcome)}</span>`;
            ol.appendChild(li);
        });
        detailsDiv.appendChild(ol);
        planContainer.appendChild(detailsDiv);

        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'plan-toggle-details-btn';
        toggleBtn.textContent = 'Show Details';
        toggleBtn.onclick = () => {
            const isHidden = detailsDiv.style.display === 'none';
            detailsDiv.style.display = isHidden ? 'block' : 'none';
            toggleBtn.textContent = isHidden ? 'Hide Details' : 'Show Details';
        };
        planContainer.appendChild(toggleBtn);


        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'plan-actions';

        const confirmBtn = document.createElement('button');
        confirmBtn.className = 'plan-confirm-btn';
        confirmBtn.textContent = 'Confirm & Run Plan';
        confirmBtn.onclick = () => {
            sendWsMessage('execute_confirmed_plan', { confirmed_plan: currentDisplayedPlan });
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;
            toggleBtn.disabled = true;
            planContainer.style.opacity = "0.7";
            planContainer.style.borderLeftColor = "var(--text-color-darker)";


            addChatMessage("Plan confirmed. Starting execution...", "status");
            updateMonitorStatus('running', 'Executing Plan...');
            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'block';
            if(agentThinkingStatusElement) agentThinkingStatusElement.textContent = 'Executing plan step 1...';
        };
        actionsDiv.appendChild(confirmBtn);

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'plan-cancel-btn';
        cancelBtn.textContent = 'Cancel Plan';
        cancelBtn.onclick = () => {
            sendWsMessage('cancel_plan', {});
            planContainer.remove();
            addChatMessage("Plan cancelled by user.", "status");
            updateMonitorStatus('idle', 'Idle');
            currentDisplayedPlan = null;
        };
        actionsDiv.appendChild(cancelBtn);

        planContainer.appendChild(actionsDiv);
        chatMessagesContainer.appendChild(planContainer);
        scrollToBottom(chatMessagesContainer);
    };

    const addMonitorLog = (fullLogText) => {
        if (!monitorLogAreaElement) { console.error("Monitor log area element (#monitor-log-area) not found!"); return; }
        const logEntryDiv = document.createElement('div');
        logEntryDiv.classList.add('monitor-log-entry');
        const logRegex = /^(\[.*?\]\[.*?\])\s*(?:\[(.*?)\])?\s*(.*)$/s;
        const match = fullLogText.match(logRegex);
        let timestampPrefix = "";
        let logTypeIndicator = "";
        let logContent = fullLogText;
        let logType = "unknown";
        if (match) {
            timestampPrefix = match[1] || "";
            logTypeIndicator = (match[2] || "").trim().toUpperCase();
            logContent = match[3] || "";
            if (logTypeIndicator.includes("TOOL START")) logType = 'tool-start';
            else if (logTypeIndicator.includes("TOOL OUTPUT")) logType = 'tool-output';
            else if (logTypeIndicator.includes("TOOL ERROR")) logType = 'tool-error';
            else if (logTypeIndicator.includes("AGENT THOUGHT (ACTION)")) logType = 'agent-thought-action';
            else if (logTypeIndicator.includes("AGENT THOUGHT (FINAL)")) logType = 'agent-thought-final';
            else if (logTypeIndicator.includes("AGENT FINISH")) logType = 'agent-finish';
            else if (logTypeIndicator.includes("ERROR") || logTypeIndicator.includes("ERR_")) logType = 'error';
            else if (logTypeIndicator.includes("HISTORY")) logType = 'history';
            else if (logTypeIndicator.includes("SYSTEM") || logTypeIndicator.includes("SYS_")) logType = 'system';
            else if (logTypeIndicator.includes("ARTIFACT")) logType = 'artifact-generated';
            else if (logTypeIndicator.includes("USER_INPUT_LOG")) logType = 'user-input-log';
            else if (logTypeIndicator.includes("LLM TOKEN USAGE")) logType = 'system';
        } else {
            if (fullLogText.toLowerCase().includes("error")) logType = 'error';
            else if (fullLogText.toLowerCase().includes("system")) logType = 'system';
        }
        logEntryDiv.classList.add(`log-type-${logType}`);
        if (timestampPrefix) {
            const timeSpan = document.createElement('span');
            timeSpan.className = 'log-timestamp';
            timeSpan.textContent = timestampPrefix;
            logEntryDiv.appendChild(timeSpan);
        }
        const contentSpan = document.createElement('span');
        contentSpan.className = 'log-content';
        if (logType === 'tool-output' || logType === 'tool-error' || logType.startsWith('agent-thought')) {
            const pre = document.createElement('pre');
            pre.textContent = logContent.trim();
            contentSpan.appendChild(pre);
        } else {
            contentSpan.textContent = logContent.trim();
        }
        logEntryDiv.appendChild(contentSpan);
        monitorLogAreaElement.appendChild(logEntryDiv);
        scrollToBottom(monitorLogAreaElement);
    };

    const updateArtifactDisplay = async () => {
        if (!monitorArtifactAreaElement || !artifactNavElement || !artifactPrevBtn || !artifactNextBtn || !artifactCounterElement) {
            console.error("Artifact display elements not found!");
            return;
        }

        // Clear previous artifact content elements (filename, image, pre, placeholder, error)
        // This selector targets all direct children of monitorArtifactAreaElement that are not the artifactNavElement itself.
        const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
        childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

        if (currentTaskArtifacts.length === 0 || currentArtifactIndex < 0 || currentArtifactIndex >= currentTaskArtifacts.length) {
            const placeholder = document.createElement('div');
            placeholder.className = 'artifact-placeholder';
            placeholder.textContent = 'No artifacts generated yet.';
            monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
            artifactNavElement.style.display = 'none';
            artifactContentFetchUrl = null; // Reset when no artifacts
            return;
        }

        const artifact = currentTaskArtifacts[currentArtifactIndex];
        if (!artifact || !artifact.url || !artifact.filename || !artifact.type) {
            console.error("Invalid artifact data:", artifact);
            const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
            monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
            artifactNavElement.style.display = 'none';
            artifactContentFetchUrl = null; // Reset on error
            return;
        }

        const filenameDiv = document.createElement('div');
        filenameDiv.className = 'artifact-filename';
        filenameDiv.textContent = artifact.filename;
        monitorArtifactAreaElement.insertBefore(filenameDiv, artifactNavElement);

        if (artifact.type === 'image') {
            artifactContentFetchUrl = null; // Images don't need the content fetch state management
            const imgElement = document.createElement('img');
            imgElement.src = artifact.url; // Browser handles image caching
            imgElement.alt = `Generated image: ${artifact.filename}`;
            imgElement.title = `Generated image: ${artifact.filename}`;
            imgElement.onerror = () => {
                console.error(`Error loading image from URL: ${artifact.url}`);
                imgElement.remove();
                const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: `Error loading image: ${artifact.filename}` });
                monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
            };
            monitorArtifactAreaElement.insertBefore(imgElement, artifactNavElement);
        } else if (artifact.type === 'text' || artifact.type === 'pdf') {
            const preElement = document.createElement('pre'); // Create a new pre element for each render
            monitorArtifactAreaElement.insertBefore(preElement, artifactNavElement); // Insert it into the DOM

            if (artifact.type === 'pdf') {
                artifactContentFetchUrl = null; // PDFs are links
                preElement.textContent = `PDF File: ${artifact.filename}`;
                const pdfLink = document.createElement('a');
                pdfLink.href = artifact.url;
                pdfLink.target = "_blank";
                pdfLink.textContent = `Open ${artifact.filename} in new tab`;
                pdfLink.style.display = "block";
                pdfLink.style.marginTop = "5px";
                preElement.appendChild(pdfLink);
            } else { // 'text' artifact
                // Only fetch if not already fetching this exact URL
                if (isFetchingArtifactContent && artifactContentFetchUrl === artifact.url) {
                    console.log(`Fetch already in progress for ${artifact.url}, existing pre-element will be updated.`);
                    preElement.textContent = 'Loading (previous fetch in progress)...'; // Update the new pre
                } else {
                    isFetchingArtifactContent = true;
                    artifactContentFetchUrl = artifact.url;
                    preElement.textContent = 'Loading text file...';
                    try {
                        console.log(`Fetching text artifact: ${artifact.url} with cache-control`);
                        const response = await fetch(artifact.url, {
                            cache: 'reload',
                            headers: {
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            }
                        });
                        if (!response.ok) {
                            console.warn(`Text artifact fetch for ${artifact.filename} not OK. Status: ${response.status} ${response.statusText}`);
                            throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                        }
                        const textContent = await response.text();
                        // Check if this is still the artifact we want to display before updating
                        if (currentTaskArtifacts[currentArtifactIndex]?.url === artifact.url) {
                            preElement.textContent = textContent;
                            console.log(`Successfully fetched and displayed ${artifact.filename}`);
                        } else {
                            console.log("Artifact changed while fetching text, not updating stale content for", artifact.filename);
                        }
                    } catch (error) {
                        console.error(`Error fetching text artifact ${artifact.filename}:`, error);
                        if (currentTaskArtifacts[currentArtifactIndex]?.url === artifact.url) {
                            preElement.textContent = `Error loading file: ${artifact.filename}\n${error.message}`;
                            preElement.classList.add('artifact-error');
                        }
                    } finally {
                        // Reset the flag only if this specific fetch operation has completed
                        if (artifactContentFetchUrl === artifact.url) {
                            isFetchingArtifactContent = false;
                        }
                    }
                }
            }
        } else {
            artifactContentFetchUrl = null; // Reset for non-text/pdf types
            console.warn(`Unsupported artifact type: ${artifact.type} for file ${artifact.filename}`);
            const unknownDiv = Object.assign(document.createElement('div'), { className: 'artifact-placeholder', textContent: `Unsupported artifact type: ${artifact.filename}` });
            monitorArtifactAreaElement.insertBefore(unknownDiv, artifactNavElement);
        }

        if (currentTaskArtifacts.length > 1) {
            artifactCounterElement.textContent = `Artifact ${currentArtifactIndex + 1} of ${currentTaskArtifacts.length}`;
            artifactPrevBtn.disabled = (currentArtifactIndex === 0);
            artifactNextBtn.disabled = (currentArtifactIndex === currentTaskArtifacts.length - 1);
            artifactNavElement.style.display = 'flex';
        } else {
            artifactNavElement.style.display = 'none';
        }
    };

    const loadTasks = () => {
        const storedCounter = localStorage.getItem(COUNTER_KEY);
        taskCounter = storedCounter ? parseInt(storedCounter, 10) : 0;
        if (isNaN(taskCounter)) taskCounter = 0;
        let firstLoad = false;
        const storedTasks = localStorage.getItem(STORAGE_KEY);
        if (storedTasks) {
            try {
                tasks = JSON.parse(storedTasks);
                if (!Array.isArray(tasks)) { tasks = []; }
                tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            } catch (e) {
                console.error("Failed to parse tasks from localStorage:", e);
                tasks = []; localStorage.removeItem(STORAGE_KEY);
            }
        } else {
            tasks = []; firstLoad = true;
        }
        if (firstLoad && tasks.length === 0) {
            taskCounter = 1;
            const firstTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: `Task - ${taskCounter}`, timestamp: Date.now() };
            tasks.unshift(firstTask); currentTaskId = firstTask.id; saveTasks();
        } else {
            const lastActiveId = localStorage.getItem(`${STORAGE_KEY}_active`);
            if (lastActiveId && tasks.some(task => task.id === lastActiveId)) {
                currentTaskId = lastActiveId;
            } else if (tasks.length > 0) {
                currentTaskId = tasks[0].id;
            } else {
                currentTaskId = null;
            }
        }
        console.log("Initial currentTaskId set to:", currentTaskId);
    };

    const saveTasks = () => {
        try {
            tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
            localStorage.setItem(COUNTER_KEY, taskCounter.toString());
            if (currentTaskId) { localStorage.setItem(`${STORAGE_KEY}_active`, currentTaskId); }
            else { localStorage.removeItem(`${STORAGE_KEY}_active`); }
        } catch (e) {
            console.error("Failed to save tasks to localStorage:", e);
            alert("Error saving task list. Changes might not persist.");
        }
    };

    const renderTaskList = () => {
        if (!taskListUl) { console.error("Task list UL element not found!"); return; }
        taskListUl.innerHTML = '';
        if (tasks.length === 0) {
            taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet.</li>';
        } else {
            tasks.forEach((task) => {
                const li = document.createElement('li'); li.className = 'task-item'; li.dataset.taskId = task.id;
                const titleSpan = document.createElement('span'); titleSpan.className = 'task-title';
                const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title;
                titleSpan.textContent = displayTitle; titleSpan.title = task.title; li.appendChild(titleSpan);
                const controlsDiv = document.createElement('div'); controlsDiv.className = 'task-item-controls';
                const editBtn = document.createElement('button'); editBtn.className = 'task-edit-btn'; editBtn.textContent = '✏️';
                editBtn.title = `Rename Task: ${task.title}`; editBtn.dataset.taskId = task.id; editBtn.dataset.taskTitle = task.title;
                editBtn.addEventListener('click', (event) => { event.stopPropagation(); handleEditTaskClick(task.id, task.title); });
                controlsDiv.appendChild(editBtn);
                const deleteBtn = document.createElement('button'); deleteBtn.className = 'task-delete-btn'; deleteBtn.textContent = '🗑️';
                deleteBtn.title = `Delete Task: ${task.title}`; deleteBtn.dataset.taskId = task.id;
                deleteBtn.addEventListener('click', (event) => { event.stopPropagation(); handleDeleteTaskClick(task.id, task.title); });
                controlsDiv.appendChild(deleteBtn); li.appendChild(controlsDiv);
                li.addEventListener('click', () => { handleTaskItemClick(task.id); });
                if (task.id === currentTaskId) { li.classList.add('active'); }
                taskListUl.appendChild(li);
            });
        }
        updateCurrentTaskTitle();
        if (uploadFileButton) { uploadFileButton.disabled = !currentTaskId; }
    };

    const handleTaskItemClick = (taskId) => { console.log(`Task item clicked: ${taskId}`); selectTask(taskId); };
    const handleDeleteTaskClick = (taskId, taskTitle) => { console.log(`Delete button clicked for task: ${taskId} (${taskTitle})`); deleteTask(taskId, taskTitle); };
    const handleEditTaskClick = (taskId, currentTitle) => {
        console.log(`Edit button clicked for task: ${taskId} (${currentTitle})`);
        const newTitle = prompt(`Enter new name for task "${currentTitle}":`, currentTitle);
        if (newTitle === null) { console.log("Rename cancelled by user."); return; }
        const trimmedTitle = newTitle.trim();
        if (!trimmedTitle) { alert("Task name cannot be empty."); console.log("Rename aborted: empty title."); return; }
        if (trimmedTitle === currentTitle) { console.log("Rename aborted: title unchanged."); return; }
        const taskIndex = tasks.findIndex(task => task.id === taskId);
        if (taskIndex !== -1) {
            tasks[taskIndex].title = trimmedTitle;
            console.log(`Task ${taskId} title updated locally to: ${trimmedTitle}`);
            saveTasks(); renderTaskList();
            if (taskId === currentTaskId) { updateCurrentTaskTitle(); }
            sendWsMessage("rename_task", { taskId: taskId, newName: trimmedTitle });
        } else { console.error(`Task ${taskId} not found locally for renaming.`); }
    };

    const updateCurrentTaskTitle = () => {
        if (!currentTaskTitleElement) return;
        const currentTask = tasks.find(task => task.id === currentTaskId);
        const title = currentTask ? currentTask.title : "No Task Selected";
        currentTaskTitleElement.textContent = title;
        if (currentTask) {
            if (!isAgentRunning && statusDotElement && !statusDotElement.classList.contains('error') && !statusDotElement.classList.contains('disconnected')) {
                updateMonitorStatus('idle', 'Idle');
            }
        } else {
            updateMonitorStatus('idle', 'No Task');
        }
    };

    const clearChatAndMonitor = (addLog = true) => {
        if (chatMessagesContainer) chatMessagesContainer.innerHTML = '';
        if (agentThinkingStatusElement) {
            chatMessagesContainer.appendChild(agentThinkingStatusElement);
            agentThinkingStatusElement.style.display = 'none';
        }
        if (monitorLogAreaElement) monitorLogAreaElement.innerHTML = '';
        currentTaskArtifacts = [];
        currentArtifactIndex = -1;
        updateArtifactDisplay(); // This will show "No artifacts" placeholder
        if (addLog && monitorLogAreaElement) { addMonitorLog("[SYSTEM] Cleared context."); }
        console.log("Cleared chat and monitor.");
        resetTaskTokenTotals();
        currentDisplayedPlan = null;
    };

    const selectTask = (taskId) => {
        console.log(`Attempting to select task: ${taskId}`);
        if (currentTaskId === taskId && taskId !== null) { console.log("Task already selected."); return; }
        const task = tasks.find(t => t.id === taskId);
        currentTaskId = task ? taskId : null;
        console.log(`Selected task ID set to: ${currentTaskId}`);
        saveTasks(); renderTaskList();
        resetTaskTokenTotals();
        if (currentTaskId && task) {
            clearChatAndMonitor(false);
            sendWsMessage("context_switch", { task: task.title, taskId: task.id });
            addChatMessage("Switching task context...", "status");
            updateMonitorStatus('running', 'Switching Task...');
        } else if (!currentTaskId) {
            clearChatAndMonitor();
            addChatMessage("No task selected.", "status");
            addMonitorLog("[SYSTEM] No task selected.");
            updateMonitorStatus('idle', 'No Task');
        } else if (!socket || socket.readyState !== WebSocket.OPEN) {
            clearChatAndMonitor(false);
            addChatMessage("Switched task locally. Connect to backend to load history.", "status");
            addMonitorLog(`[SYSTEM] Switched task locally to ${taskId}, but WS not open.`);
            updateMonitorStatus('disconnected', 'Disconnected');
        }
        console.log(`Finished select task logic for: ${currentTaskId}`);
    };

    const handleNewTaskClick = () => {
        console.log("'+ New Task' button clicked.");
        taskCounter++;
        const taskTitle = `Task - ${taskCounter}`;
        const newTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: taskTitle, timestamp: Date.now() };
        tasks.unshift(newTask);
        console.log("New task created:", newTask);
        selectTask(newTask.id);
        console.log("handleNewTaskClick finished.");
    };

    const deleteTask = (taskId, taskTitle) => {
        console.log(`Attempting to delete task: ${taskId} (${taskTitle})`);
        if (!confirm(`Are you sure you want to delete task "${taskTitle}"? This cannot be undone.`)) { console.log("Deletion cancelled by user."); return; }
        const taskIndex = tasks.findIndex(task => task.id === taskId);
        if (taskIndex === -1) { console.warn(`Task ${taskId} not found locally for deletion.`); return; }
        tasks.splice(taskIndex, 1);
        console.log(`Task ${taskId} removed locally.`);
        sendWsMessage("delete_task", { taskId: taskId });
        let nextTaskId = null;
        if (currentTaskId === taskId) {
            nextTaskId = tasks.length > 0 ? tasks[0].id : null;
            console.log(`Deleted active task, selecting next: ${nextTaskId}`);
            selectTask(nextTaskId);
        } else {
            saveTasks(); renderTaskList();
        }
        console.log(`Finished delete task logic for: ${taskId}`);
    };

    const populateSingleLlmSelector = (selectElement, availableModels, currentSelectedValue, defaultOptionText = "Use System Default", backendConfiguredDefaultLlmId = null) => {
        if (!selectElement) {
            console.error("populateSingleLlmSelector: selectElement is null or undefined for text:", defaultOptionText);
            return;
        }
        selectElement.innerHTML = '';

        const defaultOpt = document.createElement('option');
        defaultOpt.value = "";
        defaultOpt.textContent = defaultOptionText;
        selectElement.appendChild(defaultOpt);

        if ((!availableModels.gemini || availableModels.gemini.length === 0) &&
            (!availableModels.ollama || availableModels.ollama.length === 0)) {
            const noModelsOpt = document.createElement('option');
            noModelsOpt.value = "";
            noModelsOpt.textContent = "No LLMs Available";
            noModelsOpt.disabled = true;
            if (selectElement.options.length === 1 && selectElement.options[0].value === "") {
                 selectElement.options[0].textContent = "No LLMs Available";
                 selectElement.options[0].disabled = true;
            } else {
                selectElement.appendChild(noModelsOpt);
            }
            selectElement.disabled = true;
            return;
        }

        if (availableModels.gemini && availableModels.gemini.length > 0) {
            const geminiGroup = document.createElement('optgroup');
            geminiGroup.label = 'Gemini';
            availableModels.gemini.forEach(modelId => {
                const option = document.createElement('option');
                option.value = `gemini::${modelId}`;
                option.textContent = modelId;
                geminiGroup.appendChild(option);
            });
            selectElement.appendChild(geminiGroup);
        }
        if (availableModels.ollama && availableModels.ollama.length > 0) {
            const ollamaGroup = document.createElement('optgroup');
            ollamaGroup.label = 'Ollama';
            availableModels.ollama.forEach(modelId => {
                const option = document.createElement('option');
                option.value = `ollama::${modelId}`;
                option.textContent = modelId;
                ollamaGroup.appendChild(option);
            });
            selectElement.appendChild(ollamaGroup);
        }

        let valueToSet = "";
        if (currentSelectedValue && selectElement.querySelector(`option[value="${currentSelectedValue}"]`)) {
            valueToSet = currentSelectedValue;
        } else if (backendConfiguredDefaultLlmId && selectElement.querySelector(`option[value="${backendConfiguredDefaultLlmId}"]`)) {
            valueToSet = backendConfiguredDefaultLlmId;
        }
        selectElement.value = valueToSet;
        selectElement.disabled = false;
    };

    const populateAllLlmSelectors = (backendDefaultExecutorLlmId, backendRoleDefaults = {}) => {
        const lastSelectedExecutor = localStorage.getItem('selectedExecutorLlmId');
        const initialExecutorValue = lastSelectedExecutor !== null ? lastSelectedExecutor : backendDefaultExecutorLlmId;

        populateSingleLlmSelector(executorLlmSelectElement, availableModels, initialExecutorValue, "Use System Default (Executor)", backendDefaultExecutorLlmId);
        currentExecutorLlmId = executorLlmSelectElement.value;
        if (currentExecutorLlmId !== null) {
            sendWsMessage("set_llm", { llm_id: currentExecutorLlmId });
        }


        roleSelectorsMeta.forEach(selInfo => {
            if (selInfo.element) {
                const lastSelectedRoleOverride = localStorage.getItem(selInfo.storageKey);
                const backendRoleDefault = backendRoleDefaults[selInfo.role] || "";

                const initialRoleValue = lastSelectedRoleOverride !== null ? lastSelectedRoleOverride : backendRoleDefault;

                populateSingleLlmSelector(selInfo.element, availableModels, initialRoleValue, "Use System Default", backendRoleDefault);
                sessionRoleLlmOverrides[selInfo.role] = selInfo.element.value;

                if (sessionRoleLlmOverrides[selInfo.role] !== backendRoleDefault || (sessionRoleLlmOverrides[selInfo.role] === "" && lastSelectedRoleOverride !== null) ) {
                     sendWsMessage("set_session_role_llm", { role: selInfo.role, llm_id: sessionRoleLlmOverrides[selInfo.role] });
                }
            }
        });
        console.log("All LLM selectors populated. Initial Executor:", currentExecutorLlmId, "Initial Role Overrides:", sessionRoleLlmOverrides);
    };

    const sendWsMessage = (type, content) => {
        if (window.socket && window.socket.readyState === WebSocket.OPEN) {
            try {
                const payload = JSON.stringify({ type: type, ...content });
                console.log(`Sending WS message: ${type}`, content);
                window.socket.send(payload);
                if (type === "rename_task" || type === "delete_task" || type === "set_llm" || type === "cancel_agent" || type === "get_artifacts_for_task" || type === "execute_confirmed_plan" || type === "cancel_plan" || type === "set_session_role_llm") {
                    addMonitorLog(`[SYSTEM] Sent ${type} request.`);
                }
            } catch (e) {
                console.error(`Error sending ${type} via WebSocket:`, e);
                addMonitorLog(`[SYSTEM] Error sending ${type} request: ${e.message}`);
                addChatMessage(`Error sending ${type} request to backend.`, "status");
            }
        } else {
            console.warn(`Cannot send ${type}: WebSocket is not open.`);
            if (type === "user_message" || type === "context_switch" || type === "get_artifacts_for_task") {
                addChatMessage(`Cannot send ${type}: Not connected to backend.`, "status");
            }
            addMonitorLog(`[SYSTEM] Cannot send ${type}: WS not open.`);
        }
    };

    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
        if (!currentTaskId){
            alert("Please select or create a task first.");
            chatTextarea.focus();
            return;
        }
        if (isAgentRunning) {
            addChatMessage("Agent is currently busy. Please wait or stop the current process.", "status");
            return;
        }
        if (messageText) {
            addChatMessage(messageText, 'user');
            if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
                chatInputHistory.push(messageText);
                if (chatInputHistory.length > MAX_CHAT_HISTORY) { chatInputHistory.shift(); }
            }
            chatHistoryIndex = -1;
            currentInputBuffer = "";
            if(agentThinkingStatusElement) agentThinkingStatusElement.style.display = 'none';
            sendWsMessage("user_message", { content: messageText });
            updateMonitorStatus('running', 'Classifying intent...');
            chatTextarea.value = '';
            chatTextarea.style.height = 'auto';
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        } else {
            console.log("Attempted to send empty message.");
        }
        chatTextarea.focus();
    };

    const handleFileUpload = async (event) => {
        console.log("[handleFileUpload] Function entered.");
        if (!currentTaskId) {
            alert("Please select a task before uploading files.");
            console.log("[handleFileUpload] No task selected, aborting.");
            return;
        }
        if (!event.target.files || event.target.files.length === 0) {
            console.log("[handleFileUpload] No files selected for upload.");
            return;
        }
        const files = event.target.files;
        const uploadUrl = `${httpBackendBaseUrl}/upload/${currentTaskId}`;
        let sessionIDHeader = 'unknown_session';
        if (window.socket && window.socket.url) {
            try {
                const urlParams = new URL(window.socket.url).searchParams;
                sessionIDHeader = urlParams.get('session_id') || sessionIDHeader;
            } catch (e) { /* ignore */ }
        }

        console.log(`[handleFileUpload] Preparing to upload ${files.length} file(s) to ${uploadUrl} for task ${currentTaskId}. X-Session-ID: ${sessionIDHeader}`);
        addMonitorLog(`[SYSTEM] Attempting to upload ${files.length} file(s) to task ${currentTaskId}...`);
        uploadFileButton.disabled = true;
        let overallSuccess = true;
        let errorMessages = [];
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file, file.name);
            console.log(`[handleFileUpload] Processing file: ${file.name} (Size: ${file.size} bytes)`);
            try {
                addMonitorLog(`[SYSTEM] Uploading ${file.name}...`);
                console.log(`[handleFileUpload] Sending POST request to ${uploadUrl} for ${file.name}`);
                const response = await fetch(uploadUrl, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Session-ID': sessionIDHeader }
                });
                console.log(`[handleFileUpload] Received response for ${file.name}. Status: ${response.status}, OK: ${response.ok}`);
                let result;
                try {
                    result = await response.json();
                    console.log(`[handleFileUpload] Parsed JSON response for ${file.name}:`, result);
                } catch (jsonError) {
                    console.error(`[handleFileUpload] Failed to parse JSON response for ${file.name}:`, jsonError);
                    const textResponse = await response.text();
                    console.error(`[handleFileUpload] Raw text response for ${file.name}:`, textResponse);
                    result = { status: 'error', message: `Failed to parse server response (Status: ${response.status})` };
                }
                if (response.ok && result.status === 'success') {
                    console.log(`[handleFileUpload] Successfully uploaded ${file.name}:`, result);
                    addMonitorLog(`[SYSTEM] Successfully uploaded: ${result.saved?.[0]?.filename || file.name}`);
                } else {
                    console.error(`[handleFileUpload] Error reported for ${file.name}:`, result);
                    const message = result.message || `HTTP error ${response.status}`;
                    errorMessages.push(`${file.name}: ${message}`);
                    addMonitorLog(`[SYSTEM] Error uploading ${file.name}: ${message}`);
                    overallSuccess = false;
                }
            } catch (error) {
                console.error(`[handleFileUpload] Network or fetch error uploading ${file.name}:`, error);
                const message = error.message || 'Network error';
                errorMessages.push(`${file.name}: ${message}`);
                addMonitorLog(`[SYSTEM] Network/Fetch Error uploading ${file.name}: ${message}`);
                overallSuccess = false;
            }
        }
        console.log("[handleFileUpload] Re-enabling upload button and clearing input.");
        uploadFileButton.disabled = false;
        event.target.value = null;
        if (overallSuccess) {
            addChatMessage(`Successfully uploaded ${files.length} file(s).`, 'status');
        } else {
            addChatMessage(`Error uploading some files:\n${errorMessages.join('\n')}`, 'status', true);
        }
        console.log("[handleFileUpload] Function finished.");
    };


    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskClick); }
    else { console.error("New task button element not found!"); }

    if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
    if (chatTextarea) {
        chatTextarea.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); }
            else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
                if (chatInputHistory.length === 0) return;
                event.preventDefault();
                if (chatHistoryIndex === -1) { currentInputBuffer = chatTextarea.value; }
                if (event.key === 'ArrowUp') {
                    if (chatHistoryIndex === -1) { chatHistoryIndex = chatInputHistory.length - 1; }
                    else if (chatHistoryIndex > 0) { chatHistoryIndex--; }
                    chatTextarea.value = chatInputHistory[chatHistoryIndex];
                } else if (event.key === 'ArrowDown') {
                    if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                        chatHistoryIndex++; chatTextarea.value = chatInputHistory[chatHistoryIndex];
                    } else { chatHistoryIndex = -1; chatTextarea.value = currentInputBuffer; }
                }
                chatTextarea.selectionStart = chatTextarea.selectionEnd = chatTextarea.value.length;
                chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
            } else { chatHistoryIndex = -1; currentInputBuffer = ""; }
        });
        chatTextarea.addEventListener('input', () => { chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; });
    }

    if (executorLlmSelectElement) {
        executorLlmSelectElement.addEventListener('change', (event) => {
            const selectedId = event.target.value;
            console.log(`Executor LLM selection changed to: ${selectedId || "System Default (Executor)"}`);
            currentExecutorLlmId = selectedId;
            localStorage.setItem('selectedExecutorLlmId', selectedId);
            sendWsMessage("set_llm", { llm_id: selectedId });
        });
    } else { console.error("Executor LLM select element not found!"); }

    roleSelectorsMeta.forEach(selInfo => {
        if (selInfo.element) {
            selInfo.element.addEventListener('change', (event) => {
                const selectedLlmId = event.target.value;
                console.log(`Role LLM for '${selInfo.role}' changed to: ${selectedLlmId || "System Default"}`);
                sessionRoleLlmOverrides[selInfo.role] = selectedLlmId;
                localStorage.setItem(selInfo.storageKey, selectedLlmId);
                sendWsMessage("set_session_role_llm", { role: selInfo.role, llm_id: selectedLlmId });
            });
        } else {
            console.error(`LLM select element for role ${selInfo.role} not found!`);
        }
    });


    if (stopButton) {
        stopButton.addEventListener('click', () => {
            if (isAgentRunning) {
                console.log("Stop button clicked.");
                addMonitorLog("[SYSTEM] Stop request sent.");
                sendWsMessage("cancel_agent", {});
                updateMonitorStatus('cancelling', 'Cancelling...');
                stopButton.disabled = true;
            }
        });
    } else { console.error("Stop button element not found!"); }

    if (uploadFileButton && fileUploadInput) {
        uploadFileButton.addEventListener('click', () => {
            console.log("Upload button clicked, triggering file input.");
            fileUploadInput.click();
        });
        fileUploadInput.addEventListener('change', handleFileUpload);
    } else { console.error("File upload button or input element not found!"); }

    if (agentThinkingStatusElement) {
        agentThinkingStatusElement.addEventListener('click', () => {
            console.log("Agent thinking status clicked. Scrolling monitor.");
            if (monitorLogAreaElement) {
                scrollToBottom(monitorLogAreaElement);
            }
        });
    } else {
        console.error("Agent thinking status element (#agent-thinking-status) not found!");
    }

    document.body.addEventListener('click', event => {
        if (event.target.classList.contains('action-btn')) {
            const commandText = event.target.textContent.trim();
            console.log(`Action button clicked: ${commandText}`);
            addMonitorLog(`[USER_ACTION] Clicked: ${commandText}`);
            sendWsMessage("action_command", { command: commandText });
        }
    });

    if (artifactPrevBtn) { artifactPrevBtn.addEventListener('click', () => { if (currentArtifactIndex > 0) { currentArtifactIndex--; updateArtifactDisplay(); } }); }
    if (artifactNextBtn) { artifactNextBtn.addEventListener('click', () => { if (currentArtifactIndex < currentTaskArtifacts.length - 1) { currentArtifactIndex++; updateArtifactDisplay(); } }); }


    // --- Initial Load Actions ---
    loadTasks();
    renderTaskList();
    connectWebSocket();

}); // End of DOMContentLoaded listener

