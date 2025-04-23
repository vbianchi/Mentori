// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, event handling,
 * task history management, chat input history, structured monitor logging,
 * and image display in the monitor artifact area.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    const taskListUl = document.getElementById('task-list');
    const newTaskButton = document.getElementById('new-task-button');
    const chatMessagesContainer = document.getElementById('chat-messages');
    // *** Updated Monitor Area References ***
    const monitorLogAreaElement = document.getElementById('monitor-log-area'); // Target log area
    const monitorArtifactAreaElement = document.getElementById('monitor-artifact-area'); // Target artifact area
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const jumpToLiveButton = document.querySelector('.jump-live-btn'); // May need adjustment later
    const currentTaskTitleElement = document.getElementById('current-task-title');
    const monitorStatusElement = document.getElementById('monitor-status');
    const monitorFooterStatusElement = document.getElementById('monitor-footer-status');

    // --- State Variables ---
    let tasks = [];
    let currentTaskId = null;
    let taskCounter = 0;
    const STORAGE_KEY = 'aiAgentTasks';
    const COUNTER_KEY = 'aiAgentTaskCounter';
    let isLoadingHistory = false;

    // --- Chat Input History State ---
    let chatInputHistory = [];
    const MAX_CHAT_HISTORY = 10;
    let chatHistoryIndex = -1;
    let currentInputBuffer = "";

    // --- Token Streaming State ---
    let currentStreamingMessageElement = null;

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket;
    window.socket = null;
    console.log("Initialized window.socket to null.");

    /**
     * Establishes and manages the WebSocket connection.
     */
    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        addMonitorLog("[SYSTEM] Attempting to connect to backend...");
        chatMessagesContainer.querySelectorAll('.connection-status').forEach(el => el.remove());
        try {
            if (window.socket && window.socket.readyState !== WebSocket.CLOSED) { window.socket.close(1000, "Reconnecting"); }
            socket = new WebSocket(wsUrl); window.socket = socket; console.log("WebSocket object created.");
        } catch (error) { console.error("Fatal Error creating WebSocket object:", error); addChatMessage("FATAL: Failed to initialize WebSocket connection.", "status"); addMonitorLog(`[SYSTEM] FATAL Error creating WebSocket: ${error.message}`); window.socket = null; return; }

        socket.onopen = (event) => {
            console.log("WebSocket connection opened successfully.");
            addMonitorLog(`[SYSTEM] WebSocket connection established.`);
            addChatMessage("Connected to backend.", "status");
            if (currentTaskId) {
                 const currentTask = tasks.find(task => task.id === currentTaskId);
                 if (currentTask) {
                     console.log("Sending initial context switch.");
                     try { socket.send(JSON.stringify({ type: "context_switch", task: currentTask.title, taskId: currentTask.id })); }
                     catch (error) { console.error("Failed to send initial context_switch:", error); }
                 }
            }
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                switch (message.type) {
                    case 'history_start':
                        console.log("Received history_start signal."); isLoadingHistory = true;
                        clearChatAndMonitor(false); addChatMessage(`Loading history...`, "status"); break;
                    case 'history_end':
                        console.log("Received history_end signal."); isLoadingHistory = false;
                        const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                        if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                        scrollToBottom(chatMessagesContainer);
                        scrollToBottom(monitorLogAreaElement); // Scroll log area after history
                        // Don't necessarily scroll artifact area on history load
                        break;

                    // Handle Token Streaming with Formatting
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

                    case 'agent_message': // Handles full agent messages (e.g., from history)
                        console.log("Received full agent_message:", message.content);
                        addChatMessage(message.content, 'agent');
                        currentStreamingMessageElement = null;
                        break;
                    case 'user': // Handle user messages from history
                        console.log("Received user history message:", message.content);
                        addChatMessage(message.content, 'user');
                        currentStreamingMessageElement = null;
                        break;
                    case 'status_message':
                        addChatMessage(message.content, 'status');
                        if (message.content.includes("complete") || message.content.includes("error")) {
                             console.log("Resetting streaming element due to status message:", message.content);
                             currentStreamingMessageElement = null;
                        }
                        break;
                    case 'monitor_log':
                        console.log("Received monitor_log:", message.content);
                        addMonitorLog(message.content); // Adds to log area
                        break;
                    case 'display_image':
                        console.log("Received display_image message:", message.content);
                        if (message.content && message.content.url && message.content.filename) {
                             displayMonitorImage(message.content.url, message.content.filename); // Adds to artifact area
                        } else {
                             console.warn("Invalid display_image message received:", message.content);
                             addMonitorLog("[SYSTEM] Received request to display image, but data was invalid.");
                        }
                        break;
                    case 'user_message': break; // Ignore live echo
                    default:
                        console.warn("Received unknown message type:", message.type);
                        addMonitorLog(`[SYSTEM] Unknown message type: ${message.type}`);
                        currentStreamingMessageElement = null;
                }
            } catch (error) { console.error("Failed to parse/process WS message:", error, "Data:", event.data); addMonitorLog(`[SYSTEM] Error processing message: ${error.message}.`); currentStreamingMessageElement = null; }
        };

        socket.onerror = (event) => { console.error("WebSocket error:", event); addChatMessage("ERROR: Cannot connect to backend.", "status"); addMonitorLog(`[SYSTEM] WebSocket error.`); window.socket = null; currentStreamingMessageElement = null; };
        socket.onclose = (event) => { console.log(`WebSocket closed. Code: ${event.code}`); let reason = event.reason || 'No reason given'; let advice = ""; if (event.code === 1000) { reason = "Normal"; } else { reason = `Abnormal (Code: ${event.code})`; advice = " Backend down?"; } addChatMessage(`Connection closed.${advice}`, "status"); addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`); window.socket = null; currentStreamingMessageElement = null; };
    };

    // --- Helper Functions ---
    const scrollToBottom = (element) => { if (!element) return; element.scrollTop = element.scrollHeight; };
    const formatMessageContent = (text) => { /* ... (remains the same) ... */ let escapedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;"); const segments = []; let lastIndex = 0; const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n?```/g; let match; while ((match = codeBlockRegex.exec(escapedText)) !== null) { if (match.index > lastIndex) { segments.push({ type: 'text', content: escapedText.substring(lastIndex, match.index) }); } segments.push({ type: 'code', lang: match[1] || '', content: match[2] }); lastIndex = codeBlockRegex.lastIndex; } if (lastIndex < escapedText.length) { segments.push({ type: 'text', content: escapedText.substring(lastIndex) }); } let htmlContent = ""; segments.forEach(segment => { if (segment.type === 'code') { const escapedCode = segment.content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); const langClass = segment.lang ? ` class="language-${segment.lang}"` : ''; htmlContent += `<pre><code${langClass}>${escapedCode}</code></pre>`; } else { let processedText = segment.content; processedText = processedText.replace(/(\*\*\*|___)(.*?)\1/g, '<strong><em>$2</em></strong>'); processedText = processedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); processedText = processedText.replace(/(\*|_)(.*?)\1/g, '<em>$2</em>'); processedText = processedText.replace(/\n/g, '<br>'); htmlContent += processedText; } }); return htmlContent; };
    const addChatMessage = (text, type = 'agent', doScroll = true) => { /* ... (remains the same) ... */ if (!chatMessagesContainer) { console.error("Chat container missing!"); return null; } const messageElement = document.createElement('div'); messageElement.classList.add('message', `message-${type}`); if (type === 'status') { if (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos")) { messageElement.classList.add('connection-status'); } if (text.toLowerCase().includes("error")) { messageElement.classList.add('error-message'); } } if (type === 'user') { messageElement.classList.add('user-message'); messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);'; } if (type === 'agent') { messageElement.classList.add('agent-message'); messageElement.style.border = '1px solid var(--border-color)'; } if (type === 'agent') { messageElement.innerHTML = formatMessageContent(text); } else { messageElement.textContent = text; } chatMessagesContainer.appendChild(messageElement); if (doScroll) scrollToBottom(chatMessagesContainer); return messageElement; };

    /**
     * Adds a structured log entry to the monitor LOG area.
     */
    const addMonitorLog = (fullLogText) => {
        // *** Target the LOG area ***
        if (!monitorLogAreaElement) { console.error("Monitor log area element (#monitor-log-area) not found!"); return; }

        const logEntryDiv = document.createElement('div');
        logEntryDiv.classList.add('monitor-log-entry');
        const match = fullLogText.match(/^(\[.*?\]\[.*?\])\s*(\[.*?\])?\s*(.*)$/s);
        let timestampPrefix = ""; let logType = "system"; let logContent = fullLogText;
        if (match) {
            timestampPrefix = match[1] || ""; const typeMatch = match[2]; logContent = match[3] || "";
            if (typeMatch) {
                const typeText = typeMatch.replace(/[\[\]]/g, '').trim().toLowerCase();
                if (typeText.includes("tool start")) logType = 'tool-start';
                else if (typeText.includes("tool output")) logType = 'tool-output';
                else if (typeText.includes("tool error")) logType = 'tool-error';
                else if (typeText.includes("agent finish")) logType = 'agent-finish';
                else if (typeText.includes("error")) logType = 'error';
                else if (typeText.includes("history")) logType = 'history';
                else if (typeText.includes("system")) logType = 'system';
                else if (typeText.includes("image generated")) logType = 'image-generated';
            }
        } else { if (fullLogText.toLowerCase().includes("error")) logType = 'error'; else if (fullLogText.toLowerCase().includes("system")) logType = 'system'; else logType = 'unknown'; }
        logEntryDiv.classList.add(`log-type-${logType}`);
        if (timestampPrefix) { const timeSpan = document.createElement('span'); timeSpan.className = 'log-timestamp'; timeSpan.textContent = timestampPrefix; logEntryDiv.appendChild(timeSpan); }
        const contentSpan = document.createElement('span'); contentSpan.className = 'log-content';
        if (logType === 'tool-output' || logType === 'tool-error') { const pre = document.createElement('pre'); pre.textContent = logContent.trim(); contentSpan.appendChild(pre); }
        else { contentSpan.textContent = logContent.trim(); }
        logEntryDiv.appendChild(contentSpan);
        // *** Append to LOG area ***
        monitorLogAreaElement.appendChild(logEntryDiv);
        scrollToBottom(monitorLogAreaElement); // Scroll log area
     };

     /**
      * Displays an image in the monitor ARTIFACT area.
      */
     const displayMonitorImage = (imageUrl, filename) => {
         // *** Target the ARTIFACT area ***
         if (!monitorArtifactAreaElement) { console.error("Monitor artifact area element (#monitor-artifact-area) not found!"); return; }

         // Clear previous artifact (for now, only show latest)
         monitorArtifactAreaElement.innerHTML = '';

         // Create image element
         const imgElement = document.createElement('img');
         imgElement.src = imageUrl;
         imgElement.alt = `Generated image: ${filename}`;
         imgElement.title = `Generated image: ${filename}`;
         imgElement.onerror = () => {
             imgElement.alt = `Error loading image: ${filename}`;
             // Display error message instead of broken image
             monitorArtifactAreaElement.innerHTML = `<div class="artifact-error">Error loading image: ${filename}</div>`;
             console.error(`Error loading image from URL: ${imageUrl}`);
         };

         // Append image directly to artifact area
         monitorArtifactAreaElement.appendChild(imgElement);
         // No need to scroll artifact area usually, unless image is huge and area is scrollable
         // scrollToBottom(monitorArtifactAreaElement);
     };


    // --- Task History Functions ---
    const loadTasks = () => { /* ... (remains the same) ... */ const storedCounter = localStorage.getItem(COUNTER_KEY); taskCounter = storedCounter ? parseInt(storedCounter, 10) : 0; if (isNaN(taskCounter)) taskCounter = 0; let firstLoad = false; const storedTasks = localStorage.getItem(STORAGE_KEY); if (storedTasks) { try { tasks = JSON.parse(storedTasks); if (!Array.isArray(tasks)) { tasks = []; } tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)); console.log(`Loaded ${tasks.length} tasks. Next Task #: ${taskCounter + 1}`); } catch (e) { console.error("Failed to parse tasks:", e); tasks = []; localStorage.removeItem(STORAGE_KEY); } } else { tasks = []; firstLoad = true; console.log("No tasks found."); } if (firstLoad && tasks.length === 0) { console.log("First load, creating 'Task - 1'."); taskCounter = 1; const firstTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: `Task - ${taskCounter}`, timestamp: Date.now() }; tasks.unshift(firstTask); currentTaskId = firstTask.id; saveTasks(); console.log("Auto-created 'Task - 1'."); } else { const lastActiveId = localStorage.getItem(`${STORAGE_KEY}_active`); if (lastActiveId && tasks.some(task => task.id === lastActiveId)) { currentTaskId = lastActiveId; } else if (tasks.length > 0) { currentTaskId = tasks[0].id; } else { currentTaskId = null; } } console.log("Initial currentTaskId:", currentTaskId); };
    const saveTasks = () => { /* ... (remains the same) ... */ try { localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks)); localStorage.setItem(COUNTER_KEY, taskCounter.toString()); if (currentTaskId) { localStorage.setItem(`${STORAGE_KEY}_active`, currentTaskId); } else { localStorage.removeItem(`${STORAGE_KEY}_active`); } } catch (e) { console.error("Failed to save tasks:", e); alert("Error saving tasks."); } };
    const renderTaskList = () => { /* ... (remains the same) ... */ console.log(`--- Rendering Task List ---`); console.log(`Tasks:`, JSON.stringify(tasks)); console.log(`Current ID: ${currentTaskId}`); if (!taskListUl) { console.error("Task list UL missing!"); return; } taskListUl.innerHTML = ''; if (tasks.length === 0) { taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet.</li>'; } else { tasks.forEach((task) => { const li = document.createElement('li'); li.className = 'task-item'; li.dataset.taskId = task.id; const titleSpan = document.createElement('span'); titleSpan.className = 'task-title'; const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title; titleSpan.textContent = displayTitle; titleSpan.title = task.title; li.appendChild(titleSpan); const deleteBtn = document.createElement('button'); deleteBtn.className = 'task-delete-btn'; deleteBtn.textContent = '🗑️'; deleteBtn.title = `Delete: ${task.title}`; deleteBtn.dataset.taskId = task.id; li.appendChild(deleteBtn); if (task.id === currentTaskId) { li.classList.add('active'); } try { taskListUl.appendChild(li); console.log(`Appended task: ${task.id}`); } catch (appendError) { console.error(`!!! ERROR appending task: ${task.id}`, appendError); } }); } updateCurrentTaskTitle(); console.log(`--- Finished Rendering Task List ---`); };
    const updateCurrentTaskTitle = () => { /* ... (remains the same) ... */ if (!currentTaskTitleElement) return; const currentTask = tasks.find(task => task.id === currentTaskId); const title = currentTask ? currentTask.title : "No Task Selected"; currentTaskTitleElement.textContent = title; if(monitorStatusElement) monitorStatusElement.textContent = currentTask ? "Agent Idle" : "No Task"; if(monitorFooterStatusElement) monitorFooterStatusElement.textContent = currentTask ? `Task: ${title}` : "No Task Selected"; };

    /**
     * Clears the main chat and BOTH monitor areas. Optionally adds a log message.
     */
    const clearChatAndMonitor = (addLog = true) => {
        if (chatMessagesContainer) chatMessagesContainer.innerHTML = '';
        // Clear both monitor areas
        if (monitorLogAreaElement) monitorLogAreaElement.innerHTML = '';
        if (monitorArtifactAreaElement) monitorArtifactAreaElement.innerHTML = '<div class="artifact-placeholder">No artifacts generated yet.</div>'; // Reset placeholder
        if (addLog) { addMonitorLog("[SYSTEM] Cleared context."); }
        console.log("Cleared chat and monitor.");
    };

    const selectTask = (taskId) => { /* ... (remains the same) ... */ console.log(`Attempting select task: ${taskId}`); if (currentTaskId === taskId && taskId !== null) return; const task = tasks.find(t => t.id === taskId); currentTaskId = (!task && taskId !== null) ? null : taskId; console.log(`Selected task ID: ${currentTaskId}`); saveTasks(); console.log(">>> Calling renderTaskList..."); try { renderTaskList(); console.log("<<< Finished renderTaskList."); } catch (e) { console.error("!!! ERROR renderTaskList:", e); } if (currentTaskId && task && socket && socket.readyState === WebSocket.OPEN) { const payload = { type: "context_switch", task: task.title, taskId: task.id }; try { console.log(`Sending context_switch...`); socket.send(JSON.stringify(payload)); console.log(`Sent context_switch.`); } catch (e) { console.error(`Failed send context_switch:`, e); addMonitorLog(`[SYSTEM] Error sending context switch.`); } } else if (!currentTaskId) { clearChatAndMonitor(); addChatMessage("No task selected.", "status"); addMonitorLog("[SYSTEM] No task selected."); } else { addMonitorLog(`[SYSTEM] Cannot notify backend: WS not open.`); } console.log(`Finished select task: ${currentTaskId}`); };
    const handleNewTaskClick = () => { /* ... (remains the same) ... */ console.log("'+ New Task' clicked."); taskCounter++; const taskTitle = `Task - ${taskCounter}`; const newTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: taskTitle, timestamp: Date.now() }; tasks.unshift(newTask); console.log("New task added:", newTask); selectTask(newTask.id); console.log("handleNewTaskClick finished."); };
    const deleteTask = (taskId) => { /* ... (remains the same) ... */ console.log(`Attempting delete: ${taskId}`); const taskToDelete = tasks.find(t => t.id === taskId); if (!taskToDelete) return; if (!confirm(`Delete task "${taskToDelete.title}"?`)) return; tasks = tasks.filter(task => task.id !== taskId); console.log(`Task ${taskId} removed locally.`); if (socket && socket.readyState === WebSocket.OPEN) { try { socket.send(JSON.stringify({ type: "delete_task", taskId: taskId })); console.log(`Sent delete_task.`); addMonitorLog(`[SYSTEM] Requested delete task ${taskId}.`); } catch (e) { console.error(`Failed send delete_task:`, e); addMonitorLog(`[SYSTEM] Error sending delete request.`); } } else { addMonitorLog(`[SYSTEM] Cannot notify backend of delete: WS not open.`); } let nextTaskId = null; if (currentTaskId === taskId) { nextTaskId = tasks.length > 0 ? tasks[0].id : null; console.log(`Deleted active, selecting: ${nextTaskId}`); currentTaskId = nextTaskId; } else { nextTaskId = currentTaskId; } saveTasks(); renderTaskList(); if (currentTaskId !== nextTaskId) { selectTask(nextTaskId); } else if (currentTaskId === null && tasks.length === 0) { clearChatAndMonitor(); updateCurrentTaskTitle(); } console.log(`Finished delete: ${taskId}`); };
    const handleTaskListClicks = (event) => { /* ... (remains the same) ... */ const clickedItem = event.target; if (clickedItem.classList.contains('task-delete-btn')) { const taskIdToDelete = clickedItem.dataset.taskId; if (taskIdToDelete) { console.log(`Delete clicked: ${taskIdToDelete}`); deleteTask(taskIdToDelete); } } else { const taskLi = clickedItem.closest('.task-item'); if (taskLi && taskLi.dataset.taskId) { console.log(`Select clicked: ${taskLi.dataset.taskId}`); selectTask(taskLi.dataset.taskId); } } };

    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskClick); } else { console.error("New task button missing!"); }
    if (taskListUl) { taskListUl.addEventListener('click', handleTaskListClicks); } else { console.error("Task list UL missing!"); }

    // Chat Input Sending Logic
    const handleSendMessage = () => { /* ... (remains the same) ... */ const messageText = chatTextarea.value.trim(); if (!currentTaskId){ alert("Select task first."); return; } if (messageText) { addChatMessage(messageText, 'user'); if (chatInputHistory[chatInputHistory.length - 1] !== messageText) { chatInputHistory.push(messageText); if (chatInputHistory.length > MAX_CHAT_HISTORY) { chatInputHistory.shift(); } } chatHistoryIndex = -1; currentInputBuffer = ""; if (window.socket && window.socket.readyState === WebSocket.OPEN) { try { const payload = JSON.stringify({ type: "user_message", content: messageText }); console.log("Sending message:", payload); window.socket.send(payload); console.log("Message sent."); } catch (e) { console.error("Error sending:", e); addMonitorLog(`[SYSTEM] Error sending: ${e.message}`); addChatMessage("Send failed.", "status"); } } else { console.error("Cannot send: WS not open."); addChatMessage("Cannot send: Not connected.", "status"); addMonitorLog("[SYSTEM] Cannot send: WS not open."); } chatTextarea.value = ''; chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; } else { console.log("Input empty."); } chatTextarea.focus(); };
    if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
    if (chatTextarea) { /* ... (remains the same) ... */ chatTextarea.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') { if (chatInputHistory.length === 0) return; event.preventDefault(); if (chatHistoryIndex === -1) { currentInputBuffer = chatTextarea.value; } if (event.key === 'ArrowUp') { if (chatHistoryIndex === -1) { chatHistoryIndex = chatInputHistory.length - 1; } else if (chatHistoryIndex > 0) { chatHistoryIndex--; } chatTextarea.value = chatInputHistory[chatHistoryIndex]; } else if (event.key === 'ArrowDown') { if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) { chatHistoryIndex++; chatTextarea.value = chatInputHistory[chatHistoryIndex]; } else { chatHistoryIndex = -1; chatTextarea.value = currentInputBuffer; } } chatTextarea.selectionStart = chatTextarea.selectionEnd = chatTextarea.value.length; chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; } else { chatHistoryIndex = -1; currentInputBuffer = ""; } }); chatTextarea.addEventListener('input', () => { chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; }); }

    // Action Button Clicks
     document.body.addEventListener('click', event => { /* ... (remains the same) ... */ if (event.target.classList.contains('action-btn')) { const commandText = event.target.textContent.trim(); console.log(`Action clicked: ${commandText}`); addMonitorLog(`User action: ${commandText}`); if (socket && socket.readyState === WebSocket.OPEN) { try { socket.send(JSON.stringify({ type: "action_command", command: commandText })); } catch (e) { console.error("Failed send action:", e); addMonitorLog(`[SYSTEM] Error sending action.`); } } else { addMonitorLog(`[SYSTEM] Cannot send action: WS not open.`); } } });

    // Jump to Live Button
     if (jumpToLiveButton) { /* ... (remains the same) ... */ jumpToLiveButton.addEventListener('click', () => { console.log("Jump to live clicked."); if(monitorLogAreaElement){ monitorLogAreaElement.scrollTop = monitorLogAreaElement.scrollHeight; } }); } // Adjusted to scroll log area

    // --- Initial Load Actions ---
    loadTasks(); // Load tasks & counter
    renderTaskList(); // Render initial list
    connectWebSocket(); // Connect WS (sends initial context if needed)

}); // End of DOMContentLoaded listener

