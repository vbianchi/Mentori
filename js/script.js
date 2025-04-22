// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, event handling,
 * task history management, and chat input history.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    const taskListUl = document.getElementById('task-list');
    const newTaskButton = document.getElementById('new-task-button');
    const chatMessagesContainer = document.getElementById('chat-messages');
    const monitorCodeElement = document.getElementById('monitor-log-content');
    const monitorContentElement = document.querySelector('.monitor-content');
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const jumpToLiveButton = document.querySelector('.jump-live-btn');
    const currentTaskTitleElement = document.getElementById('current-task-title');
    const monitorStatusElement = document.getElementById('monitor-status');
    const monitorFooterStatusElement = document.getElementById('monitor-footer-status');

    // --- State Variables ---
    let tasks = []; // Array to hold task objects {id: string, title: string, timestamp: number}
    let currentTaskId = null; // ID of the currently selected task
    let taskCounter = 0; // Counter for default task names
    const STORAGE_KEY = 'aiAgentTasks'; // Key for localStorage
    const COUNTER_KEY = 'aiAgentTaskCounter'; // Key for counter
    let isLoadingHistory = false; // Flag to manage history loading state

    // --- Chat Input History State ---
    let chatInputHistory = []; // Stores last sent messages
    const MAX_CHAT_HISTORY = 10; // Max number of messages to store
    let chatHistoryIndex = -1; // Current position in history (-1 means current input)
    let currentInputBuffer = ""; // Store partially typed message when navigating history

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket; // Declare socket variable
    window.socket = null; // Assign to window for console access
    console.log("Initialized window.socket to null.");

    /**
     * Establishes and manages the WebSocket connection to the backend server.
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
            console.log("WebSocket connection opened successfully. Ready state:", socket.readyState);
            addMonitorLog(`[SYSTEM] WebSocket connection established to ${wsUrl}. Ready to send.`);
            addChatMessage("Connected to backend.", "status");
            if (currentTaskId) {
                 const currentTask = tasks.find(task => task.id === currentTaskId);
                 if (currentTask) {
                     console.log("Sending initial context switch for loaded task.");
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
                        console.log("Received history_start signal. Clearing UI.");
                        isLoadingHistory = true;
                        clearChatAndMonitor(false);
                        addChatMessage(`Loading history... (${message.content})`, "status");
                        break;
                    case 'history_end':
                        console.log("Received history_end signal.");
                        isLoadingHistory = false;
                        const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                        if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                        break;
                    case 'agent_message': console.log("Received agent_message:", message.content); addChatMessage(message.content, 'agent'); break;
                    case 'user': console.log("Received user history message:", message.content); addChatMessage(message.content, 'user'); break; // Handle user type from history
                    case 'status_message': addChatMessage(message.content, 'status'); break;
                    case 'monitor_log': console.log("Received monitor_log:", message.content); addMonitorLog(message.content); break;
                    case 'user_message': break; // Ignore echo from live sending
                    default: console.warn("Received unknown message type from backend:", message.type, "Content:", message.content); addMonitorLog(`[SYSTEM] Received unknown message type: ${message.type} - Content: ${message.content}`);
                }
            } catch (error) { console.error("Failed to parse WebSocket message or process it:", error, "Data received:", event.data); addMonitorLog(`[SYSTEM] Error processing message from backend: ${error.message}. Data: ${event.data}`); }
        };

        socket.onerror = (event) => { console.error("WebSocket error observed:", event); addChatMessage("ERROR: Cannot connect to the backend server. Is it running?", "status"); addMonitorLog(`[SYSTEM] WebSocket connection error.`); window.socket = null; };
        socket.onclose = (event) => { console.log(`WebSocket connection closed. Code: ${event.code}, Reason: '${event.reason}', Clean: ${event.wasClean}`); let reason = event.reason || 'No reason given'; let advice = ""; if (event.code === 1000) { reason = "Normal closure"; } else if (!event.wasClean || event.code === 1006) { reason = `Abnormal closure (Code: ${event.code})`; advice = " Backend server might be down."; } else { reason = `Code: ${event.code}, Reason: ${reason}`; } addChatMessage(`Connection to backend closed.${advice}`, "status"); addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`); window.socket = null; };
    };

    // --- Helper Functions ---
    const scrollToBottom = (element) => { if (!element) return; const isScrolledToBottom = element.scrollHeight - element.clientHeight <= element.scrollTop + 50; if (isScrolledToBottom) { element.scrollTop = element.scrollHeight; } };
    const addChatMessage = (text, type = 'agent') => { if (!chatMessagesContainer) { console.error("Chat message container not found!"); return; } const messageElement = document.createElement('div'); messageElement.classList.add('message'); let isSimpleText = true; messageElement.classList.add(`message-${type}`); if (type === 'status') { if (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos")) { messageElement.classList.add('connection-status'); } if (text.toLowerCase().includes("error")) { messageElement.classList.add('error-message'); } } switch (type) { case 'user': messageElement.classList.add('user-message'); messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);'; break; case 'status': messageElement.classList.add('agent-status'); break; case 'suggestion': messageElement.classList.add('agent-suggestion'); break; case 'warning': messageElement.classList.add('agent-warning'); break; case 'action-prompt': isSimpleText = false; messageElement.classList.add('action-prompt'); messageElement.innerHTML = `<p>${text}</p><button class="action-btn">Default Action</button>`; break; case 'agent': default: messageElement.classList.add('agent-message'); messageElement.style.border = '1px solid var(--border-color)'; break; } if (isSimpleText) { messageElement.textContent = text; } chatMessagesContainer.appendChild(messageElement); scrollToBottom(chatMessagesContainer); };
    const addMonitorLog = (text) => { if (!monitorCodeElement) { console.error("Monitor code element not found!"); return; } const logLine = document.createTextNode(`${text}\n`); monitorCodeElement.appendChild(logLine); scrollToBottom(monitorContentElement); };

    // --- Task History Functions ---
    const loadTasks = () => { const storedCounter = localStorage.getItem(COUNTER_KEY); taskCounter = storedCounter ? parseInt(storedCounter, 10) : 0; if (isNaN(taskCounter)) taskCounter = 0; const storedTasks = localStorage.getItem(STORAGE_KEY); if (storedTasks) { try { tasks = JSON.parse(storedTasks); if (!Array.isArray(tasks)) { tasks = []; } tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)); console.log(`Loaded ${tasks.length} tasks. Next Task #: ${taskCounter + 1}`); } catch (e) { console.error("Failed to parse tasks:", e); tasks = []; localStorage.removeItem(STORAGE_KEY); } } else { tasks = []; console.log("No tasks found."); } const lastActiveId = localStorage.getItem(`${STORAGE_KEY}_active`); if (lastActiveId && tasks.some(task => task.id === lastActiveId)) { currentTaskId = lastActiveId; } else if (tasks.length > 0) { currentTaskId = tasks[0].id; } else { currentTaskId = null; } console.log("Initial currentTaskId:", currentTaskId); };
    const saveTasks = () => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks)); localStorage.setItem(COUNTER_KEY, taskCounter.toString()); if (currentTaskId) { localStorage.setItem(`${STORAGE_KEY}_active`, currentTaskId); } else { localStorage.removeItem(`${STORAGE_KEY}_active`); } } catch (e) { console.error("Failed to save tasks:", e); alert("Error saving tasks."); } };
    const renderTaskList = () => { console.log(`--- Rendering Task List ---`); console.log(`Current tasks array (${tasks.length} items):`, JSON.stringify(tasks)); console.log(`Current selected task ID: ${currentTaskId}`); if (!taskListUl) { console.error("Task list UL element not found! Cannot render."); return; } taskListUl.innerHTML = ''; if (tasks.length === 0) { console.log("No tasks to render, showing placeholder."); taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet. Click "+ New Task".</li>'; } else { console.log("Rendering task items..."); tasks.forEach((task, index) => { console.log(`Rendering task ${index + 1}: ID=${task.id}, Title=${task.title}`); const li = document.createElement('li'); li.className = 'task-item'; li.dataset.taskId = task.id; const titleSpan = document.createElement('span'); titleSpan.className = 'task-title'; const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title; titleSpan.textContent = displayTitle; titleSpan.title = task.title; li.appendChild(titleSpan); const deleteBtn = document.createElement('button'); deleteBtn.className = 'task-delete-btn'; deleteBtn.textContent = '🗑️'; deleteBtn.title = `Delete task: ${task.title}`; deleteBtn.dataset.taskId = task.id; li.appendChild(deleteBtn); if (task.id === currentTaskId) { console.log(`Marking task ${task.id} as active.`); li.classList.add('active'); } try { taskListUl.appendChild(li); console.log(`Successfully appended task item for ID: ${task.id}`); } catch (appendError) { console.error(`!!! ERROR appending task item for ID: ${task.id}`, appendError); } }); console.log("Finished appending task items."); } updateCurrentTaskTitle(); console.log(`--- Finished Rendering Task List ---`); };
    const updateCurrentTaskTitle = () => { if (!currentTaskTitleElement) { console.error("Task title element not found!"); return; } const currentTask = tasks.find(task => task.id === currentTaskId); const title = currentTask ? currentTask.title : "No Task Selected"; console.log(`Updating center panel title to: ${title}`); currentTaskTitleElement.textContent = title; if(monitorStatusElement) monitorStatusElement.textContent = currentTask ? "Agent Idle" : "No Task"; if(monitorFooterStatusElement) monitorFooterStatusElement.textContent = currentTask ? `Task: ${title}` : "No Task Selected"; };
    const clearChatAndMonitor = (addLog = true) => { if (chatMessagesContainer) chatMessagesContainer.innerHTML = ''; if (monitorCodeElement) monitorCodeElement.textContent = ''; if (addLog) { addMonitorLog("[SYSTEM] Cleared context."); } console.log("Cleared chat and monitor."); };
    const selectTask = (taskId) => { console.log(`Attempting to select task ID: ${taskId}`); if (currentTaskId === taskId && taskId !== null) { console.log(`Task ${taskId} already selected.`); return; } const task = tasks.find(t => t.id === taskId); if (!task && taskId !== null) { console.error(`Task with ID ${taskId} not found.`); currentTaskId = null; } else { currentTaskId = taskId; } console.log(`Selecting task ID: ${currentTaskId}`); saveTasks(); console.log(">>> Calling renderTaskList..."); try { renderTaskList(); console.log("<<< Finished renderTaskList call."); } catch (renderError) { console.error("!!! ERROR during renderTaskList call:", renderError); } /* UI cleared by history_start */ if (currentTaskId && task && socket && socket.readyState === WebSocket.OPEN) { const messageType = "context_switch"; const payload = { type: messageType, task: task.title, taskId: task.id }; try { console.log(`Attempting to send ${messageType} message to backend...`); socket.send(JSON.stringify(payload)); console.log(`Sent ${messageType} message to backend.`); } catch (error) { console.error(`Failed to send ${messageType} message:`, error); addMonitorLog(`[SYSTEM] Error sending ${messageType} notification.`); } } else if (!currentTaskId) { clearChatAndMonitor(); addChatMessage("No task selected.", "status"); addMonitorLog("[SYSTEM] No task selected."); } else if (!socket || socket.readyState !== WebSocket.OPEN) { addMonitorLog(`[SYSTEM] Cannot notify backend of context switch: WebSocket not connected.`); } console.log(`Finished selecting task ID: ${currentTaskId}`); };
    const handleNewTaskClick = () => { console.log("'+ New Task' button clicked."); taskCounter++; const taskTitle = `Task - ${taskCounter}`; console.log(`Creating new task with default title: ${taskTitle}`); const newTask = { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: taskTitle, timestamp: Date.now() }; console.log("New task object created:", newTask); tasks.unshift(newTask); console.log("Task added to array, tasks:", JSON.stringify(tasks)); selectTask(newTask.id); console.log("handleNewTaskClick finished."); };
    const deleteTask = (taskId) => { console.log(`Attempting to delete task ID: ${taskId}`); const taskToDelete = tasks.find(t => t.id === taskId); if (!taskToDelete) { console.error(`Cannot delete: Task ID ${taskId} not found.`); return; } if (!confirm(`Are you sure you want to delete task "${taskToDelete.title}"? This cannot be undone.`)) { console.log("Task deletion cancelled."); return; } tasks = tasks.filter(task => task.id !== taskId); console.log(`Task ${taskId} removed from frontend array.`); if (socket && socket.readyState === WebSocket.OPEN) { try { socket.send(JSON.stringify({ type: "delete_task", taskId: taskId })); console.log(`Sent delete_task message for ${taskId}.`); addMonitorLog(`[SYSTEM] Requested deletion of task ${taskId}.`); } catch (error) { console.error(`Failed to send delete_task message for ${taskId}:`, error); addMonitorLog(`[SYSTEM] Error sending delete request.`); } } else { addMonitorLog(`[SYSTEM] Cannot notify backend of deletion: WS not connected.`); } let nextTaskId = null; if (currentTaskId === taskId) { if (tasks.length > 0) { nextTaskId = tasks[0].id; console.log(`Deleted active task, selecting newest: ${nextTaskId}`); } else { console.log("Deleted last task."); currentTaskId = null; } } else { nextTaskId = currentTaskId; console.log(`Deleted inactive task, keeping ${currentTaskId} active.`); } saveTasks(); renderTaskList(); if (currentTaskId !== nextTaskId) { selectTask(nextTaskId); } else if (currentTaskId === null && tasks.length === 0) { clearChatAndMonitor(); updateCurrentTaskTitle(); } console.log(`Finished deleting task ID: ${taskId}`); };
    const handleTaskListClicks = (event) => { const clickedItem = event.target; if (clickedItem.classList.contains('task-delete-btn')) { const taskIdToDelete = clickedItem.dataset.taskId; if (taskIdToDelete) { console.log(`Delete button clicked for task: ${taskIdToDelete}`); deleteTask(taskIdToDelete); } else { console.error("Delete button clicked but missing task ID."); } } else { const taskLi = clickedItem.closest('.task-item'); if (taskLi && taskLi.dataset.taskId) { console.log(`Task item clicked for selection: ${taskLi.dataset.taskId}`); selectTask(taskLi.dataset.taskId); } } };


    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskClick); } else { console.error("New task button element not found!"); }
    if (taskListUl) { taskListUl.addEventListener('click', handleTaskListClicks); } else { console.error("Task list UL element not found!"); }

    // Chat Input Sending Logic
    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
        if (!currentTaskId){ alert("Please select or create a task before sending a message."); return; }
        if (messageText) {
            addChatMessage(messageText, 'user');

            // Add message to chat input history
            if (chatInputHistory[chatInputHistory.length - 1] !== messageText) { // Avoid duplicates
                chatInputHistory.push(messageText);
                if (chatInputHistory.length > MAX_CHAT_HISTORY) {
                    chatInputHistory.shift(); // Remove oldest if limit exceeded
                }
            }
            chatHistoryIndex = -1; // Reset history index to current input
            currentInputBuffer = ""; // Clear buffer

            // Send message via WebSocket
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                try {
                    const messagePayload = JSON.stringify({ type: "user_message", content: messageText });
                    console.log("Attempting to send message:", messagePayload);
                    window.socket.send(messagePayload);
                    console.log("Message sent via WebSocket.");
                 } catch (error) { console.error("Error sending message:", error); addMonitorLog(`[SYSTEM] Error sending: ${error.message}`); addChatMessage("Failed to send message.", "status"); }
            } else { console.error("Cannot send message: WS not open."); addChatMessage("Cannot send message: Not connected.", "status"); addMonitorLog("[SYSTEM] Cannot send: WS not open."); }

            // Clear and refocus input area
            chatTextarea.value = '';
            chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        } else { console.log("Message input is empty."); }
        chatTextarea.focus();
    };
    // Attach listeners for chat input
    if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
    if (chatTextarea) {
        // Handle Enter key for sending
        chatTextarea.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevent newline on Enter
                handleSendMessage();
            }
            // --- Handle Arrow Keys for History ---
            else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
                if (chatInputHistory.length === 0) return; // No history

                event.preventDefault(); // Prevent cursor movement

                if (chatHistoryIndex === -1) {
                    // If starting navigation, buffer current input
                    currentInputBuffer = chatTextarea.value;
                }

                if (event.key === 'ArrowUp') {
                    if (chatHistoryIndex === -1) {
                        // Start from the last message
                        chatHistoryIndex = chatInputHistory.length - 1;
                    } else if (chatHistoryIndex > 0) {
                        // Move to previous message
                        chatHistoryIndex--;
                    }
                    // Update textarea with history item
                    chatTextarea.value = chatInputHistory[chatHistoryIndex];
                } else if (event.key === 'ArrowDown') {
                    if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                        // Move to next message
                        chatHistoryIndex++;
                        chatTextarea.value = chatInputHistory[chatHistoryIndex];
                    } else {
                        // Reached end of history, restore buffer or clear
                        chatHistoryIndex = -1;
                        chatTextarea.value = currentInputBuffer;
                    }
                }
                // Move cursor to end after setting value
                chatTextarea.selectionStart = chatTextarea.selectionEnd = chatTextarea.value.length;
                // Adjust height after changing value
                chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
            } else {
                 // Any other key press resets navigation
                 chatHistoryIndex = -1;
                 currentInputBuffer = ""; // Clear buffer if user types normally
            }
        });
        // Auto-resize listener
        chatTextarea.addEventListener('input', () => { chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; });
    }

    // Action Button Clicks
     document.body.addEventListener('click', event => { if (event.target.classList.contains('action-btn')) { const commandText = event.target.textContent.trim(); console.log(`Action button clicked: ${commandText}`); addMonitorLog(`User clicked action: ${commandText}`); if (socket && socket.readyState === WebSocket.OPEN) { try { socket.send(JSON.stringify({ type: "action_command", command: commandText })); } catch (error) { console.error("Failed to send action_command:", error); addMonitorLog(`[SYSTEM] Error sending action.`); } } else { addMonitorLog(`[SYSTEM] Cannot send action: WS not connected.`); } } });

    // Jump to Live Button
     if (jumpToLiveButton) { jumpToLiveButton.addEventListener('click', () => { console.log("'> Jump to live' button clicked."); if(monitorContentElement){ monitorContentElement.scrollTop = monitorContentElement.scrollHeight; } }); }

    // --- Initial Load Actions ---
    loadTasks(); // Load tasks & counter from localStorage
    renderTaskList(); // Render the initial list
    connectWebSocket(); // Establish WebSocket connection

}); // End of DOMContentLoaded listener

