// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, event handling,
 * task history management, chat input history, Markdown formatting,
 * LLM selection, monitor status updates, agent cancellation, and file uploads.
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
    const llmSelectElement = document.getElementById('llm-select');
    const stopButton = document.getElementById('stop-button');
    const fileUploadInput = document.getElementById('file-upload-input');
    const uploadFileButton = document.getElementById('upload-file-button');

    // --- State Variables ---
    let tasks = [];
    let currentTaskId = null;
    let taskCounter = 0;
    const STORAGE_KEY = 'aiAgentTasks';
    const COUNTER_KEY = 'aiAgentTaskCounter';
    let isLoadingHistory = false;
    let availableModels = { gemini: [], ollama: [] };
    let currentSelectedLlmId = null;
    let defaultLlmId = null;
    let isAgentRunning = false;

    // --- Chat Input History State ---
    let chatInputHistory = [];
    const MAX_CHAT_HISTORY = 10;
    let chatHistoryIndex = -1;
    let currentInputBuffer = "";

    // --- Token Streaming State ---
    let currentStreamingMessageElement = null;

    // --- Artifact State ---
    let currentTaskArtifacts = [];
    let currentArtifactIndex = -1;

    // --- Backend URLs ---
    const wsUrl = 'ws://localhost:8765'; // WebSocket server
    const httpBackendBaseUrl = 'http://localhost:8766'; // HTTP server for uploads/files

    let socket;
    window.socket = null;
    console.log("Initialized window.socket to null.");

    // --- Function to update monitor status indicator & Stop Button ---
    const updateMonitorStatus = (status, text) => {
        if (!statusDotElement || !monitorStatusTextElement || !stopButton) return;

        statusDotElement.classList.remove('idle', 'running', 'error', 'disconnected');
        let statusText = text;

        switch (status) {
            case 'idle':
                statusDotElement.classList.add('idle');
                statusText = text || 'Idle';
                isAgentRunning = false;
                stopButton.style.display = 'none'; // Hide stop button
                stopButton.disabled = true;
                break;
            case 'running':
                statusDotElement.classList.add('running');
                statusText = text || 'Running...';
                isAgentRunning = true;
                stopButton.style.display = 'inline-block'; // Show stop button
                stopButton.disabled = false; // Enable stop button
                break;
            case 'error':
                statusDotElement.classList.add('error');
                statusText = text || 'Error';
                isAgentRunning = false;
                stopButton.style.display = 'none'; // Hide stop button
                stopButton.disabled = true;
                break;
            case 'cancelling': // Intermediate state
                 statusDotElement.classList.add('running'); // Keep yellow while cancelling
                 statusText = text || 'Cancelling...';
                 isAgentRunning = true; // Still considered running until confirmed stopped
                 stopButton.disabled = true; // Disable button after click
                 break;
            case 'disconnected':
            default:
                statusDotElement.classList.add('disconnected');
                statusText = text || 'Disconnected';
                isAgentRunning = false;
                stopButton.style.display = 'none'; // Hide stop button
                stopButton.disabled = true;
                break;
        }
        monitorStatusTextElement.textContent = statusText;
        console.log(`Monitor status updated: ${status} - ${monitorStatusTextElement.textContent}`);
    };


    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        addMonitorLog("[SYSTEM] Attempting to connect to backend...");
        updateMonitorStatus('disconnected', 'Connecting...');
        chatMessagesContainer.querySelectorAll('.connection-status').forEach(el => el.remove());
        try {
            if (window.socket && window.socket.readyState !== WebSocket.CLOSED) {
                console.log("Closing existing WebSocket connection before reconnecting.");
                window.socket.close(1000, "Reconnecting");
            }
            socket = new WebSocket(wsUrl);
            window.socket = socket;
            console.log("WebSocket object created.");
        } catch (error) {
            console.error("Fatal Error creating WebSocket object:", error);
            addChatMessage("FATAL: Failed to initialize WebSocket connection.", "status");
            addMonitorLog(`[SYSTEM] FATAL Error creating WebSocket: ${error.message}`);
            updateMonitorStatus('error', 'Connection Failed');
            window.socket = null;
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
                    console.log("Sending initial context switch on connection open.");
                    sendWsMessage("context_switch", { task: currentTask.title, taskId: currentTask.id });
                } else {
                    console.warn("currentTaskId set, but task not found in list on connection open.");
                    currentTaskId = null; updateMonitorStatus('idle', 'No Task'); updateArtifactDisplay();
                }
            } else {
                 updateMonitorStatus('idle', 'No Task'); updateArtifactDisplay();
            }
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.debug("Received WS message:", message);

                switch (message.type) {
                    case 'history_start':
                        console.log("Received history_start signal."); isLoadingHistory = true;
                        clearChatAndMonitor(false); addChatMessage(`Loading history...`, "status");
                        updateMonitorStatus('running', 'Loading History...');
                        break;
                    case 'history_end':
                        console.log("Received history_end signal."); isLoadingHistory = false;
                        const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                        if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                        scrollToBottom(chatMessagesContainer);
                        scrollToBottom(monitorLogAreaElement);
                        updateMonitorStatus('idle', 'Idle');
                        break;

                    case 'agent_token_chunk':
                        if (!currentStreamingMessageElement) {
                            console.log("Creating new message element for streaming.");
                            currentStreamingMessageElement = addChatMessage("", 'agent', false);
                        }
                        if (currentStreamingMessageElement) {
                            currentStreamingMessageElement.textContent += message.content;
                            currentStreamingMessageElement.innerHTML = formatMessageContent(currentStreamingMessageElement.textContent);
                            scrollToBottom(chatMessagesContainer);
                        } else { console.warn("Received token chunk but no streaming element."); }
                        break;

                    case 'agent_message':
                        console.log("Received full agent_message:", message.content.substring(0, 100) + "...");
                        addChatMessage(message.content, 'agent');
                        currentStreamingMessageElement = null;
                        updateMonitorStatus('idle', 'Idle'); // Agent finished
                        break;
                    case 'user':
                        console.log("Received user history message:", message.content);
                        addChatMessage(message.content, 'user');
                        currentStreamingMessageElement = null;
                        break;
                    case 'status_message':
                         const lowerContent = message.content.toLowerCase();
                         if (lowerContent.includes("connect") || lowerContent.includes("clos") || lowerContent.includes("error")) {
                             addChatMessage(message.content, 'status');
                         }
                         // Update monitor status based on content
                         if (lowerContent.includes("error")) {
                             updateMonitorStatus('error', message.content);
                         } else if (lowerContent.includes("complete") || lowerContent.includes("cancelled")) { // Also set idle on cancel
                             updateMonitorStatus('idle', 'Idle');
                         } else if (isAgentRunning && !lowerContent.includes("llm set")) { // Avoid overriding "Running" with "LLM set"
                             updateMonitorStatus('running', message.content);
                         }
                         if (lowerContent.includes("complete") || lowerContent.includes("error") || lowerContent.includes("cancelled")) {
                             console.log("Resetting streaming element due to status message:", message.content);
                             currentStreamingMessageElement = null;
                         }
                         break;
                    case 'monitor_log':
                        addMonitorLog(message.content);
                        // If agent finishes or errors, ensure status is updated
                        if (message.content.includes("[Agent Finish]") || message.content.includes("Error]")) {
                            if(isAgentRunning) updateMonitorStatus('idle', 'Idle'); // Set back to idle if it was running
                        }
                        break;
                    case 'update_artifacts':
                        console.log("Received update_artifacts message with content:", message.content);
                        if (Array.isArray(message.content)) {
                            currentTaskArtifacts = message.content;
                            currentArtifactIndex = currentTaskArtifacts.length > 0 ? 0 : -1;
                            updateArtifactDisplay();
                        } else {
                            console.warn("Invalid update_artifacts message content (not an array):", message.content);
                            currentTaskArtifacts = []; currentArtifactIndex = -1; updateArtifactDisplay();
                        }
                        break;
                    // *** NEW: Handle artifact refresh trigger ***
                    case 'trigger_artifact_refresh':
                        const taskIdToRefresh = message.content?.taskId;
                        console.log(`Received trigger_artifact_refresh for task: ${taskIdToRefresh}`);
                        if (taskIdToRefresh && taskIdToRefresh === currentTaskId) {
                            console.log(`Current task matches refresh trigger, requesting updated artifacts for ${currentTaskId}`);
                            addMonitorLog(`[SYSTEM] File upload detected, refreshing artifact list...`);
                            sendWsMessage('get_artifacts_for_task', { taskId: currentTaskId });
                        } else {
                            console.log(`Ignoring artifact refresh trigger for non-current task (${taskIdToRefresh})`);
                        }
                        break;
                    // *** END NEW ***

                    case 'available_models':
                        console.log("Received available_models:", message.content);
                        if (message.content && typeof message.content === 'object') {
                            availableModels.gemini = message.content.gemini || [];
                            availableModels.ollama = message.content.ollama || [];
                            defaultLlmId = message.content.default_llm_id || null;
                            populateLlmSelector();
                        } else {
                            console.warn("Invalid available_models message content:", message.content);
                            availableModels = { gemini: [], ollama: [] };
                            populateLlmSelector();
                        }
                        break;

                    case 'user_message': break; // Ignore live echo
                    default:
                        console.warn("Received unknown message type:", message.type, "Content:", message.content);
                        addMonitorLog(`[SYSTEM] Unknown message type received: ${message.type}`);
                        currentStreamingMessageElement = null;
                }
            } catch (error) {
                console.error("Failed to parse/process WS message:", error, "Data:", event.data);
                addMonitorLog(`[SYSTEM] Error processing message: ${error.message}.`);
                updateMonitorStatus('error', 'Processing Error');
                currentStreamingMessageElement = null;
            }
        };

        socket.onerror = (event) => {
            console.error("WebSocket error event:", event);
            addChatMessage("ERROR: Cannot connect to backend.", "status", true);
            addMonitorLog(`[SYSTEM] WebSocket error occurred.`);
            updateMonitorStatus('error', 'Connection Error');
            window.socket = null;
            currentStreamingMessageElement = null;
             if (llmSelectElement) {
                 llmSelectElement.innerHTML = '<option value="">Connection Error</option>';
                 llmSelectElement.disabled = true;
             }
        };
        socket.onclose = (event) => {
            console.log(`WebSocket closed. Code: ${event.code}, Reason: '${event.reason || 'No reason given'}' Clean close: ${event.wasClean}`);
            let reason = event.reason || 'No reason given';
            let advice = "";
            if (event.code === 1000 || event.wasClean) { reason = "Normal"; }
            else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down or network issue?"; }
            addChatMessage(`Connection closed.${advice}`, "status", true);
            addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`);
            updateMonitorStatus('disconnected', 'Disconnected');
            window.socket = null;
            currentStreamingMessageElement = null;
             if (llmSelectElement) {
                 llmSelectElement.innerHTML = '<option value="">Disconnected</option>';
                 llmSelectElement.disabled = true;
             }
        };
    };

    // --- Helper Functions ---
    const scrollToBottom = (element) => { if (!element) return; element.scrollTop = element.scrollHeight; };

    const formatMessageContent = (text) => {
        let formattedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => { const escapedCode = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); const langClass = lang ? ` class="language-${lang}"` : ''; return `<pre><code${langClass}>${escapedCode}</code></pre>`; });
        formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => { const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); if (linkText.includes('<') || linkText.includes('>')) return match; return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`; });
        formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
        formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
        formattedText = formattedText.replace(/(\*|_)(?=\S)([\s\S]*?\S)\1/g, '<em>$2</em>');
        const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>)/s);
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

        if (type === 'agent') {
            messageElement.innerHTML = formatMessageContent(text);
        } else {
            messageElement.textContent = text;
        }

        chatMessagesContainer.appendChild(messageElement);
        if (doScroll) scrollToBottom(chatMessagesContainer);
        return messageElement;
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
            // Match CSS class names
            if (logTypeIndicator.includes("TOOL START")) logType = 'tool-start';
            else if (logTypeIndicator.includes("TOOL OUTPUT")) logType = 'tool-output';
            else if (logTypeIndicator.includes("TOOL ERROR")) logType = 'tool-error';
            else if (logTypeIndicator.includes("AGENT THOUGHT (ACTION)")) logType = 'agent-thought-action';
            else if (logTypeIndicator.includes("AGENT THOUGHT (FINAL)")) logType = 'agent-thought-final';
            else if (logTypeIndicator.includes("AGENT FINISH")) logType = 'agent-finish';
            else if (logTypeIndicator.includes("ERROR") || logTypeIndicator.includes("ERR_")) logType = 'error';
            else if (logTypeIndicator.includes("HISTORY")) logType = 'history';
            else if (logTypeIndicator.includes("SYSTEM") || logTypeIndicator.includes("SYS_")) logType = 'system';
            else if (logTypeIndicator.includes("ARTIFACT")) logType = 'artifact-generated'; // Match general artifact log
            else if (logTypeIndicator.includes("USER_INPUT_LOG")) logType = 'user-input-log'; // Match specific user input log type
        } else {
            if (fullLogText.toLowerCase().includes("error")) logType = 'error';
            else if (fullLogText.toLowerCase().includes("system")) logType = 'system';
            console.warn("Could not parse monitor log prefix reliably:", fullLogText);
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
        while (monitorArtifactAreaElement.firstChild && monitorArtifactAreaElement.firstChild !== artifactNavElement) {
            monitorArtifactAreaElement.removeChild(monitorArtifactAreaElement.firstChild);
        }
        if (currentTaskArtifacts.length === 0 || currentArtifactIndex < 0 || currentArtifactIndex >= currentTaskArtifacts.length) {
            const placeholder = document.createElement('div');
            placeholder.className = 'artifact-placeholder';
            placeholder.textContent = 'No artifacts generated yet.';
            monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
            artifactNavElement.style.display = 'none';
        } else {
            const artifact = currentTaskArtifacts[currentArtifactIndex];
            if (!artifact || !artifact.url || !artifact.filename || !artifact.type) {
                console.error("Invalid artifact data:", artifact);
                const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
                monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
                artifactNavElement.style.display = 'none';
                return;
            }
            // Display filename
            const filenameDiv = document.createElement('div');
            filenameDiv.className = 'artifact-filename'; // Add a class for styling
            filenameDiv.textContent = artifact.filename;
            filenameDiv.style.fontSize = '0.85em'; // Example style
            filenameDiv.style.color = 'var(--text-color-darker)';
            filenameDiv.style.marginBottom = '5px';
            filenameDiv.style.textAlign = 'center';
            filenameDiv.style.wordBreak = 'break-all';
            monitorArtifactAreaElement.insertBefore(filenameDiv, artifactNavElement);

            if (artifact.type === 'image') {
                const imgElement = document.createElement('img');
                imgElement.src = artifact.url;
                imgElement.alt = `Generated image: ${artifact.filename}`;
                imgElement.title = `Generated image: ${artifact.filename}`;
                imgElement.onerror = () => {
                    console.error(`Error loading image from URL: ${artifact.url}`);
                    imgElement.remove();
                    const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: `Error loading image: ${artifact.filename}` });
                    monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
                };
                monitorArtifactAreaElement.insertBefore(imgElement, artifactNavElement);
            } else if (artifact.type === 'text') {
                const preElement = document.createElement('pre');
                preElement.textContent = 'Loading text file...';
                monitorArtifactAreaElement.insertBefore(preElement, artifactNavElement);
                try {
                    console.log(`Fetching text artifact: ${artifact.url}`);
                    const response = await fetch(artifact.url);
                    if (!response.ok) { throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`); }
                    const textContent = await response.text();
                    preElement.textContent = textContent;
                    console.log(`Successfully fetched and displayed ${artifact.filename}`);
                } catch (error) {
                    console.error(`Error fetching text artifact ${artifact.filename}:`, error);
                    preElement.textContent = `Error loading file: ${artifact.filename}\n${error.message}`;
                    preElement.classList.add('artifact-error');
                }
            } else {
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
        }
    };

    // --- Task History Functions ---
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
                console.log(`Loaded ${tasks.length} tasks. Next Task #: ${taskCounter + 1}`);
            } catch (e) {
                console.error("Failed to parse tasks from localStorage:", e);
                tasks = [];
                localStorage.removeItem(STORAGE_KEY);
            }
        } else {
            tasks = [];
            firstLoad = true;
            console.log("No tasks found in localStorage.");
        }
        if (firstLoad && tasks.length === 0) {
            console.log("First load with no tasks, creating 'Task - 1'.");
            taskCounter = 1;
            const firstTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: `Task - ${taskCounter}`, timestamp: Date.now() };
            tasks.unshift(firstTask);
            currentTaskId = firstTask.id;
            saveTasks();
            console.log("Auto-created and selected 'Task - 1'.");
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
        console.log(`--- Rendering Task List (Current ID: ${currentTaskId}) ---`);
        if (!taskListUl) { console.error("Task list UL element not found!"); return; }
        taskListUl.innerHTML = '';
        if (tasks.length === 0) {
            taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet.</li>';
        } else {
            tasks.forEach((task) => {
                const li = document.createElement('li');
                li.className = 'task-item';
                li.dataset.taskId = task.id;
                const titleSpan = document.createElement('span');
                titleSpan.className = 'task-title';
                const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title;
                titleSpan.textContent = displayTitle;
                titleSpan.title = task.title;
                li.appendChild(titleSpan);
                const controlsDiv = document.createElement('div');
                controlsDiv.className = 'task-item-controls';
                const editBtn = document.createElement('button');
                editBtn.className = 'task-edit-btn';
                editBtn.textContent = '✏️';
                editBtn.title = `Rename Task: ${task.title}`;
                editBtn.dataset.taskId = task.id;
                editBtn.dataset.taskTitle = task.title;
                editBtn.addEventListener('click', (event) => { event.stopPropagation(); handleEditTaskClick(task.id, task.title); });
                controlsDiv.appendChild(editBtn);
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'task-delete-btn';
                deleteBtn.textContent = '🗑️';
                deleteBtn.title = `Delete Task: ${task.title}`;
                deleteBtn.dataset.taskId = task.id;
                deleteBtn.addEventListener('click', (event) => { event.stopPropagation(); handleDeleteTaskClick(task.id, task.title); });
                controlsDiv.appendChild(deleteBtn);
                li.appendChild(controlsDiv);
                li.addEventListener('click', () => { handleTaskItemClick(task.id); });
                if (task.id === currentTaskId) { li.classList.add('active'); }
                taskListUl.appendChild(li);
            });
        }
        updateCurrentTaskTitle();
        // Enable/disable upload button based on task selection
        if (uploadFileButton) {
            uploadFileButton.disabled = !currentTaskId;
        }
        console.log(`--- Finished Rendering Task List ---`);
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
            saveTasks();
            renderTaskList();
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
        if (monitorLogAreaElement) monitorLogAreaElement.innerHTML = '';
        currentTaskArtifacts = [];
        currentArtifactIndex = -1;
        updateArtifactDisplay();
        if (addLog && monitorLogAreaElement) { addMonitorLog("[SYSTEM] Cleared context."); }
        console.log("Cleared chat and monitor.");
    };
    const selectTask = (taskId) => {
        console.log(`Attempting to select task: ${taskId}`);
        if (currentTaskId === taskId && taskId !== null) { console.log("Task already selected."); return; }
        const task = tasks.find(t => t.id === taskId);
        currentTaskId = task ? taskId : null;
        console.log(`Selected task ID set to: ${currentTaskId}`);
        saveTasks();
        renderTaskList(); // This will update the upload button state
        if (currentTaskId && task) {
            sendWsMessage("context_switch", { task: task.title, taskId: task.id });
            clearChatAndMonitor(false);
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
            saveTasks();
            renderTaskList();
        }
        console.log(`Finished delete task logic for: ${taskId}`);
    };

    const populateLlmSelector = () => {
        if (!llmSelectElement) { console.error("LLM select element not found!"); return; }
        llmSelectElement.innerHTML = '';
        llmSelectElement.disabled = true;

        if ((!availableModels.gemini || availableModels.gemini.length === 0) &&
            (!availableModels.ollama || availableModels.ollama.length === 0)) {
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "No LLMs available";
            llmSelectElement.appendChild(option);
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
            llmSelectElement.appendChild(geminiGroup);
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
            llmSelectElement.appendChild(ollamaGroup);
        }

        const lastSelected = localStorage.getItem('selectedLlmId');
        if (lastSelected && llmSelectElement.querySelector(`option[value="${lastSelected}"]`)) {
            llmSelectElement.value = lastSelected;
            currentSelectedLlmId = lastSelected;
        } else if (defaultLlmId && llmSelectElement.querySelector(`option[value="${defaultLlmId}"]`)) {
            llmSelectElement.value = defaultLlmId;
            currentSelectedLlmId = defaultLlmId;
        } else if (llmSelectElement.options.length > 0) {
             for (let i = 0; i < llmSelectElement.options.length; i++) {
                 if (llmSelectElement.options[i].value) {
                     llmSelectElement.selectedIndex = i;
                     currentSelectedLlmId = llmSelectElement.value;
                     break;
                 }
             }
        }

        console.log(`LLM selector populated. Initial selection: ${currentSelectedLlmId}`);
        llmSelectElement.disabled = false;
    };


    const sendWsMessage = (type, content) => {
        if (window.socket && window.socket.readyState === WebSocket.OPEN) {
            try {
                const payload = JSON.stringify({ type: type, ...content });
                console.log(`Sending WS message: ${type}`, content);
                window.socket.send(payload);
                if (type === "rename_task" || type === "delete_task" || type === "set_llm" || type === "cancel_agent" || type === "get_artifacts_for_task") { // Added get_artifacts_for_task
                     addMonitorLog(`[SYSTEM] Sent ${type} request.`);
                }
            } catch (e) {
                console.error(`Error sending ${type} via WebSocket:`, e);
                addMonitorLog(`[SYSTEM] Error sending ${type} request: ${e.message}`);
                addChatMessage(`Error sending ${type} request to backend.`, "status");
            }
        } else {
            console.warn(`Cannot send ${type}: WebSocket is not open.`);
            if (type === "user_message" || type === "context_switch" || type === "get_artifacts_for_task") { // Added get_artifacts_for_task
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
        if (isAgentRunning) { // Prevent sending if agent is already running
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

            sendWsMessage("user_message", { content: messageText });
            updateMonitorStatus('running', 'Processing...'); // Set status to running

            chatTextarea.value = '';
            chatTextarea.style.height = 'auto';
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        } else {
            console.log("Attempted to send empty message.");
        }
        chatTextarea.focus();
    };

    // --- File Upload Handler with Debug Logging & Correct URL ---
    const handleFileUpload = async (event) => {
        console.log("[handleFileUpload] Function entered."); // DEBUG
        if (!currentTaskId) {
            alert("Please select a task before uploading files.");
            console.log("[handleFileUpload] No task selected, aborting."); // DEBUG
            return;
        }
        if (!event.target.files || event.target.files.length === 0) {
            console.log("[handleFileUpload] No files selected for upload."); // DEBUG
            return;
        }

        const files = event.target.files;
        const uploadUrl = `${httpBackendBaseUrl}/upload/${currentTaskId}`;

        // Attempt to get session ID from WebSocket URL if available (for logging context on backend)
        let sessionID = 'unknown';
        try {
            if (window.socket?.url) {
                // This parsing might fail if the URL is unexpected, hence the try...catch
                sessionID = new URL(window.socket.url).searchParams.get('session_id') || 'unknown';
            }
        } catch (e) {
            console.warn("[handleFileUpload] Could not parse session ID from WebSocket URL:", e);
        }

        console.log(`[handleFileUpload] Preparing to upload ${files.length} file(s) to ${uploadUrl} for task ${currentTaskId}. Session: ${sessionID}`); // DEBUG
        addMonitorLog(`[SYSTEM] Attempting to upload ${files.length} file(s) to task ${currentTaskId}...`);
        uploadFileButton.disabled = true; // Disable button during upload

        let overallSuccess = true;
        let errorMessages = [];

        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file, file.name); // Ensure filename is included
            console.log(`[handleFileUpload] Processing file: ${file.name} (Size: ${file.size} bytes)`); // DEBUG

            try {
                addMonitorLog(`[SYSTEM] Uploading ${file.name}...`);
                console.log(`[handleFileUpload] Sending POST request to ${uploadUrl} for ${file.name}`); // DEBUG
                const response = await fetch(uploadUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        // Include session ID if needed by backend for context/logging
                         'X-Session-ID': sessionID
                    }
                });

                console.log(`[handleFileUpload] Received response for ${file.name}. Status: ${response.status}, OK: ${response.ok}`); // DEBUG
                console.log("[handleFileUpload] Raw response object:", response); // DEBUG

                let result;
                try {
                    result = await response.json();
                    console.log(`[handleFileUpload] Parsed JSON response for ${file.name}:`, result); // DEBUG
                } catch (jsonError) {
                    console.error(`[handleFileUpload] Failed to parse JSON response for ${file.name}:`, jsonError); // DEBUG
                    const textResponse = await response.text(); // Try getting text response
                    console.error(`[handleFileUpload] Raw text response for ${file.name}:`, textResponse); // DEBUG
                    result = { status: 'error', message: `Failed to parse server response (Status: ${response.status})` };
                }


                if (response.ok && result.status === 'success') {
                    console.log(`[handleFileUpload] Successfully uploaded ${file.name}:`, result); // DEBUG
                    addMonitorLog(`[SYSTEM] Successfully uploaded: ${result.saved?.[0]?.filename || file.name}`);
                    // Note: Backend now sends 'trigger_artifact_refresh' via WebSocket
                } else {
                    console.error(`[handleFileUpload] Error reported for ${file.name}:`, result); // DEBUG
                    const message = result.message || `HTTP error ${response.status}`;
                    errorMessages.push(`${file.name}: ${message}`);
                    addMonitorLog(`[SYSTEM] Error uploading ${file.name}: ${message}`);
                    overallSuccess = false;
                }
            } catch (error) {
                console.error(`[handleFileUpload] Network or fetch error uploading ${file.name}:`, error); // DEBUG
                const message = error.message || 'Network error';
                errorMessages.push(`${file.name}: ${message}`);
                addMonitorLog(`[SYSTEM] Network/Fetch Error uploading ${file.name}: ${message}`);
                overallSuccess = false;
            }
        }

        // Re-enable button and clear input
        console.log("[handleFileUpload] Re-enabling upload button and clearing input."); // DEBUG
        uploadFileButton.disabled = false;
        event.target.value = null; // Clear the file input

        // Display final status
        if (overallSuccess) {
            addChatMessage(`Successfully uploaded ${files.length} file(s).`, 'status');
        } else {
            addChatMessage(`Error uploading some files:\n${errorMessages.join('\n')}`, 'status', true); // Show detailed errors
        }
        console.log("[handleFileUpload] Function finished."); // DEBUG
        // Artifact refresh is now triggered by backend via WebSocket 'trigger_artifact_refresh' message
    };
    // --- *** END NEW *** ---

    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskClick); }
    else { console.error("New task button element not found!"); }

    if (taskListUl) { console.log("Task list event listeners will be added during rendering."); }
    else { console.error("Task list UL element not found!"); }

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

    if (llmSelectElement) {
        llmSelectElement.addEventListener('change', (event) => {
            const selectedId = event.target.value;
            if (selectedId && selectedId !== currentSelectedLlmId) {
                console.log(`LLM selection changed to: ${selectedId}`);
                currentSelectedLlmId = selectedId;
                localStorage.setItem('selectedLlmId', selectedId);
                sendWsMessage("set_llm", { llm_id: selectedId });
            } else if (!selectedId) {
                 console.warn("LLM selector changed to an empty value.");
            }
        });
    } else { console.error("LLM select element not found!"); }

    if (stopButton) {
        stopButton.addEventListener('click', () => {
            if (isAgentRunning) {
                console.log("Stop button clicked.");
                addMonitorLog("[SYSTEM] Stop request sent.");
                sendWsMessage("cancel_agent", {});
                updateMonitorStatus('cancelling', 'Cancelling...'); // Update status immediately
                stopButton.disabled = true; // Prevent multiple clicks
            }
        });
    } else { console.error("Stop button element not found!"); }

    // *** File Upload Listeners ***
    if (uploadFileButton && fileUploadInput) {
        uploadFileButton.addEventListener('click', () => {
            console.log("Upload button clicked, triggering file input."); // DEBUG
            fileUploadInput.click(); // Trigger hidden file input
        });
        fileUploadInput.addEventListener('change', handleFileUpload);
    } else {
        console.error("File upload button or input element not found!");
    }
    // *** END NEW ***


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
    renderTaskList(); // This will now also set initial upload button state
    connectWebSocket();

}); // End of DOMContentLoaded listener

