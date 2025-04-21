// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, event handling,
 * and task history management using localStorage.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    // Use IDs assigned in index.html for reliability
    const taskListUl = document.getElementById('task-list');
    const newTaskButton = document.getElementById('new-task-button');
    const chatMessagesContainer = document.getElementById('chat-messages'); // Assuming ID was added
    const monitorCodeElement = document.getElementById('monitor-log-content'); // Use ID of <code>
    const monitorContentElement = document.querySelector('.monitor-content'); // Parent div for scrolling
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const jumpToLiveButton = document.querySelector('.jump-live-btn');
    const currentTaskTitleElement = document.getElementById('current-task-title');
    const monitorStatusElement = document.getElementById('monitor-status'); // Added ID
    const monitorFooterStatusElement = document.getElementById('monitor-footer-status'); // Added ID

    // --- State Variables ---
    let tasks = []; // Array to hold task objects {id: string, title: string, timestamp: number}
    let currentTaskId = null; // ID of the currently selected task
    let taskCounter = 0; // Counter for default task names
    const STORAGE_KEY = 'aiAgentTasks'; // Key for localStorage
    const COUNTER_KEY = 'aiAgentTaskCounter'; // Key for counter

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket; // Declare socket variable
    window.socket = null; // Assign to window for console access, initialized to null
    console.log("Initialized window.socket to null.");

    /**
     * Establishes and manages the WebSocket connection to the backend server.
     */
    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        addMonitorLog("[SYSTEM] Attempting to connect to backend..."); // UI Feedback

        // Clear previous connection status messages from chat
         chatMessagesContainer.querySelectorAll('.connection-status').forEach(el => el.remove());

        try {
            // Ensure previous socket is closed if reconnecting
            if (window.socket && window.socket.readyState !== WebSocket.CLOSED) {
                console.log("Closing previous WebSocket connection before reconnecting.");
                window.socket.close(1000, "Reconnecting"); // Close normally
            }

            // Create new WebSocket connection
            socket = new WebSocket(wsUrl);
            window.socket = socket; // Assign to window for console access immediately
            console.log("WebSocket object created. Assigning to window.socket.");

        } catch (error) {
            // Handle fatal errors during WebSocket object creation
            console.error("Fatal Error creating WebSocket object:", error);
            addChatMessage("FATAL: Failed to initialize WebSocket connection.", "status");
            addMonitorLog(`[SYSTEM] FATAL Error creating WebSocket: ${error.message}`);
            window.socket = null; // Ensure it's null on creation failure
            return; // Stop if creation fails
        }

        /**
         * Handles the WebSocket connection opening event.
         */
        socket.onopen = (event) => {
            console.log("WebSocket connection opened successfully. Ready state:", socket.readyState);
            addMonitorLog(`[SYSTEM] WebSocket connection established to ${wsUrl}. Ready to send.`);
            addChatMessage("Connected to backend.", "status"); // Use 'status' type
        };

        /**
         * Handles incoming messages from the WebSocket server.
         */
        socket.onmessage = (event) => {
            // console.log("WebSocket message received:", event.data); // Uncomment for deep debugging
            try {
                const message = JSON.parse(event.data);
                // Process message based on its type
                switch (message.type) {
                    case 'agent_message':
                        // *** Log receipt of agent_message ***
                        console.log("Received agent_message:", message.content);
                        addChatMessage(message.content, 'agent');
                        break;
                    case 'status_message':
                        // console.log("Received status_message:", message.content); // Optional log
                        addChatMessage(message.content, 'status');
                        break;
                    case 'monitor_log':
                        // Log receipt of monitor_log
                        console.log("Received monitor_log:", message.content);
                        addMonitorLog(message.content); // Call the function to display it
                        break;
                    case 'user_message':
                        // Usually ignore echo of user message from backend
                        break;
                    default:
                        // Handle unknown message types
                        console.warn("Received unknown message type from backend:", message.type);
                        addMonitorLog(`[SYSTEM] Received unknown message type: ${message.type}`);
                }
            } catch (error) {
                // Handle errors parsing JSON or processing the message
                console.error("Failed to parse WebSocket message or process it:", error, "Data received:", event.data);
                addMonitorLog(`[SYSTEM] Error processing message from backend: ${error.message}. Data: ${event.data}`);
            }
        };

        /**
         * Handles WebSocket errors.
         */
        socket.onerror = (event) => {
            console.error("WebSocket error observed:", event);
            addChatMessage("ERROR: Cannot connect to the backend server. Is it running?", "status");
            addMonitorLog(`[SYSTEM] WebSocket connection error. Cannot send/receive messages. Check backend server.`);
            window.socket = null; // Reset global socket on error
        };

        /**
         * Handles the WebSocket connection closing event.
         */
        socket.onclose = (event) => {
            console.log(`WebSocket connection closed. Code: ${event.code}, Reason: '${event.reason}', Clean: ${event.wasClean}`);
            let reason = event.reason || 'No reason given';
            let advice = "";
            if (event.code === 1000) { // Normal closure
                 reason = "Normal closure";
            } else if (!event.wasClean || event.code === 1006) { // Abnormal (server down?)
                reason = `Connection closed abnormally (Code: ${event.code})`;
                advice = " Backend server might be down. Please check.";
            } else {
                 reason = `Code: ${event.code}, Reason: ${reason}`;
            }
            addChatMessage(`Connection to backend closed.${advice}`, "status");
            addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`);
            window.socket = null; // Reset global socket on close
            // Optional: Attempt to reconnect after a delay
            // console.log("Attempting to reconnect in 5 seconds...");
            // setTimeout(connectWebSocket, 5000);
        };
    };

    // --- Helper Functions ---

    /**
     * Scrolls an element to its bottom if the user is already near the bottom.
     * @param {Element} element The scrollable element.
     */
    const scrollToBottom = (element) => {
        if (!element) return;
        // Only scroll if user is within 50px of the bottom
        const isScrolledToBottom = element.scrollHeight - element.clientHeight <= element.scrollTop + 50;
        if (isScrolledToBottom) {
            element.scrollTop = element.scrollHeight;
        }
    };

    /**
     * Adds a message element to the chat display area.
     * @param {string} text The message text content.
     * @param {string} type The type of message ('user', 'agent', 'status', 'suggestion', 'warning', 'action-prompt').
     */
    const addChatMessage = (text, type = 'agent') => {
         if (!chatMessagesContainer) { console.error("Chat message container not found!"); return; }
         const messageElement = document.createElement('div');
         messageElement.classList.add('message'); // Base class
         let isSimpleText = true; // Flag to determine if textContent should be used

         // Add specific class based on the single type provided for styling/selection
         messageElement.classList.add(`message-${type}`); // e.g., message-status, message-agent

         // Add connection-status class specifically for status messages about connection
         // Also add error class for status messages containing "error"
         if (type === 'status') {
             if (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos")) {
                 messageElement.classList.add('connection-status');
             }
             if (text.toLowerCase().includes("error")) {
                  messageElement.classList.add('error-message'); // Add an error class for styling
             }
         }

         // Apply type-specific classes and potentially structure
         switch (type) {
            case 'user':
                messageElement.classList.add('user-message'); // For CSS styling
                messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);'; // Keep style for now
                break;
            case 'status':
                messageElement.classList.add('agent-status'); // Use the existing CSS class
                break;
             case 'suggestion':
                messageElement.classList.add('agent-suggestion');
                break;
            case 'warning':
                 messageElement.classList.add('agent-warning');
                 break;
            case 'action-prompt':
                 // Action prompts contain HTML (button)
                 isSimpleText = false;
                 messageElement.classList.add('action-prompt');
                 // WARNING: Only use innerHTML if 'text' is trusted or properly sanitized
                 messageElement.innerHTML = `<p>${text}</p><button class="action-btn">Default Action</button>`;
                 break;
            case 'agent':
            default:
                messageElement.classList.add('agent-message');
                 messageElement.style.border = '1px solid var(--border-color)'; // Keep style for now
                break;
        }

        // Use textContent for simple messages to prevent potential XSS from backend content
        if (isSimpleText) {
             messageElement.textContent = text;
        }

        chatMessagesContainer.appendChild(messageElement);
        scrollToBottom(chatMessagesContainer); // Scroll down after adding
    };

    /**
     * Adds a log entry to the monitor panel display.
     * @param {string} text The log text content (backend includes timestamp/prefix).
     */
    const addMonitorLog = (text) => {
        if (!monitorCodeElement) { console.error("Monitor code element not found!"); return; }
        // Backend now sends timestamped logs, just display the text received
        // Using textNode is safer than manipulating textContent directly for large logs
        const logLine = document.createTextNode(`${text}\n`); // Add newline for display
        monitorCodeElement.appendChild(logLine);
        scrollToBottom(monitorContentElement); // Scroll down after adding
     };

    // --- Task History Functions ---

    /**
     * Loads tasks and counter from localStorage.
     */
    const loadTasks = () => {
        // Load counter
        const storedCounter = localStorage.getItem(COUNTER_KEY);
        taskCounter = storedCounter ? parseInt(storedCounter, 10) : 0;
        if (isNaN(taskCounter)) taskCounter = 0; // Reset if invalid

        // Load tasks
        const storedTasks = localStorage.getItem(STORAGE_KEY);
        if (storedTasks) {
            try {
                tasks = JSON.parse(storedTasks);
                if (!Array.isArray(tasks)) { tasks = []; } // Ensure it's an array
                // Sort tasks by timestamp descending (newest first)
                tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
                console.log(`Loaded ${tasks.length} tasks. Next Task #: ${taskCounter + 1}`);
            } catch (e) { console.error("Failed to parse tasks:", e); tasks = []; localStorage.removeItem(STORAGE_KEY); }
        } else { tasks = []; console.log("No tasks found."); }

        // Load last active task ID, validate it exists
        const lastActiveId = localStorage.getItem(`${STORAGE_KEY}_active`);
        if (lastActiveId && tasks.some(task => task.id === lastActiveId)) {
             currentTaskId = lastActiveId;
        } else if (tasks.length > 0) {
             currentTaskId = tasks[0].id; // Default to newest task if last active is invalid or null
        } else {
             currentTaskId = null; // No tasks, no active task
        }
        console.log("Initial currentTaskId:", currentTaskId);
    };

    /**
     * Saves tasks and counter to localStorage.
     */
    const saveTasks = () => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
            localStorage.setItem(COUNTER_KEY, taskCounter.toString()); // Save counter
            if (currentTaskId) { localStorage.setItem(`${STORAGE_KEY}_active`, currentTaskId); }
            else { localStorage.removeItem(`${STORAGE_KEY}_active`); }
             // console.log(`Saved ${tasks.length} tasks. Active: ${currentTaskId}`); // Optional verbose log
        } catch (e) { console.error("Failed to save tasks:", e); alert("Error saving tasks."); }
    };

    /**
     * Renders the list of tasks in the left panel UI.
     */
    const renderTaskList = () => {
        // *** ADDED LOGGING ***
        console.log(`--- Rendering Task List ---`);
        console.log(`Current tasks array (${tasks.length} items):`, JSON.stringify(tasks));
        console.log(`Current selected task ID: ${currentTaskId}`);

        if (!taskListUl) { console.error("Task list UL element not found! Cannot render."); return; }

        taskListUl.innerHTML = ''; // Clear existing list items
        if (tasks.length === 0) {
            console.log("No tasks to render, showing placeholder.");
            taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet. Click "+ New Task".</li>';
        } else {
            console.log("Rendering task items...");
            tasks.forEach((task, index) => {
                // *** ADDED LOGGING ***
                console.log(`Rendering task ${index + 1}: ID=${task.id}, Title=${task.title}`);
                const li = document.createElement('li');
                li.className = 'task-item';
                // Truncate long titles for display
                const displayTitle = task.title.length > 35 ? task.title.substring(0, 32) + '...' : task.title;
                li.textContent = displayTitle; // Display task title
                li.title = task.title; // Show full title on hover
                li.dataset.taskId = task.id; // Store task ID in data attribute

                if (task.id === currentTaskId) {
                    console.log(`Marking task ${task.id} as active.`);
                    li.classList.add('active'); // Highlight the active task
                }
                taskListUl.appendChild(li);
            });
            console.log("Finished appending task items.");
        }
        // Update the main title header based on the selected task
        updateCurrentTaskTitle();
        console.log(`--- Finished Rendering Task List ---`); // Log exit
    };

    /**
     * Updates the title in the center panel header based on currentTaskId.
     */
    const updateCurrentTaskTitle = () => {
         if (!currentTaskTitleElement) { console.error("Task title element not found!"); return; }
         const currentTask = tasks.find(task => task.id === currentTaskId);
         const title = currentTask ? currentTask.title : "No Task Selected";
         console.log(`Updating center panel title to: ${title}`);
         currentTaskTitleElement.textContent = title;
         // Also update monitor status examples
         if(monitorStatusElement) monitorStatusElement.textContent = currentTask ? "Agent Idle" : "No Task";
         if(monitorFooterStatusElement) monitorFooterStatusElement.textContent = currentTask ? `Task: ${title}` : "No Task Selected";
    };

    /**
     * Clears the main chat and monitor areas, adding a system message.
     */
    const clearChatAndMonitor = () => {
         if (chatMessagesContainer) chatMessagesContainer.innerHTML = '';
         if (monitorCodeElement) monitorCodeElement.textContent = ''; // Clear monitor text
         addMonitorLog("[SYSTEM] Cleared context for selected task."); // Log clearing reason
         console.log("Cleared chat and monitor.");
    };

    /**
     * Selects a task, updates UI, saves state, and notifies backend.
     * @param {string | null} taskId The ID of the task to select, or null to deselect.
     */
    const selectTask = (taskId) => {
        console.log(`Attempting to select task ID: ${taskId}`); // Log entry
        // Avoid redundant actions if already selected
        if (currentTaskId === taskId && taskId !== null) {
             console.log(`Task ${taskId} already selected.`);
             return;
        }

        const task = tasks.find(t => t.id === taskId);
        if (!task && taskId !== null) {
            // If task ID is invalid, deselect
            console.error(`Task with ID ${taskId} not found in tasks array:`, JSON.stringify(tasks));
            currentTaskId = null;
        } else {
             currentTaskId = taskId; // Set the new task ID (can be null)
        }

        console.log(`Selecting task ID: ${currentTaskId}`); // Log selection confirmed
        saveTasks(); // Save state (including active ID)

        // *** ADDED LOGGING AROUND renderTaskList CALL ***
        console.log(">>> Calling renderTaskList...");
        try {
            renderTaskList(); // Update UI list and title
            console.log("<<< Finished renderTaskList call.");
        } catch (renderError) {
             console.error("!!! ERROR during renderTaskList call:", renderError);
        }

        console.log(">>> Calling clearChatAndMonitor..."); // Also added log around this
        clearChatAndMonitor(); // Clear main panels
        console.log("<<< Finished clearChatAndMonitor call.");


        // Notify backend
        if (socket && socket.readyState === WebSocket.OPEN) {
            const messageType = task ? "context_switch" : "new_task"; // Determine message type
            const payload = task ? { type: messageType, task: task.title, taskId: task.id } : { type: "new_task" }; // Construct payload
            try {
                console.log(`Attempting to send ${messageType} message to backend...`);
                socket.send(JSON.stringify(payload));
                console.log(`Sent ${messageType} message to backend.`);
                // Add status message to chat AFTER clearing
                addChatMessage(task ? `Switched to task: ${task.title}` : "New task context ready.", "status");
            } catch (error) {
                 console.error(`Failed to send ${messageType} message:`, error);
                 addMonitorLog(`[SYSTEM] Error sending ${messageType} notification.`);
            }
        } else {
            addMonitorLog(`[SYSTEM] Cannot notify backend of ${task ? 'context switch' : 'new task'}: WebSocket not connected.`);
        }
        console.log(`Finished selecting task ID: ${currentTaskId}`); // Log exit
    };

    /**
     * Handles clicks on the "+ New Task" button - USES DEFAULT NAMING.
     */
    const handleNewTaskClick = () => {
        console.log("'+ New Task' button clicked."); // Log entry
        taskCounter++; // Increment counter
        const taskTitle = `Task - ${taskCounter}`; // Generate default title
        console.log(`Creating new task with default title: ${taskTitle}`); // Log title

        const newTask = {
            // Generate a simple unique ID
            id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`,
            title: taskTitle, // Use generated title
            timestamp: Date.now() // Store creation time
        };
        console.log("New task object created:", newTask);
        tasks.unshift(newTask); // Add to beginning of the array
        console.log("Task added to array, tasks:", JSON.stringify(tasks));
        selectTask(newTask.id); // Select the new task
        console.log("handleNewTaskClick finished."); // Log exit
    };

    /**
     * Handles clicks within the task list area (uses event delegation).
     */
    const handleTaskItemClick = (event) => {
        const clickedLi = event.target.closest('.task-item'); // Find the clicked LI element
        if (clickedLi && clickedLi.dataset.taskId) {
            console.log(`Task item clicked: ${clickedLi.dataset.taskId}`);
            selectTask(clickedLi.dataset.taskId);
        }
    };


    // --- Event Listeners Setup ---

    // New Task Button Click
    if (newTaskButton) {
        newTaskButton.addEventListener('click', handleNewTaskClick);
    } else { console.error("New task button element not found!"); }

    // Task List Clicks (Event Delegation)
    if (taskListUl) {
        taskListUl.addEventListener('click', handleTaskItemClick);
    } else { console.error("Task list UL element not found!"); }

    // Chat Input Sending Logic
    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
        // ** Ensure a task is selected before sending **
        if (!currentTaskId){
             alert("Please select or create a task before sending a message.");
             return;
        }
        if (messageText) {
            addChatMessage(messageText, 'user'); // Display user message immediately

            // Send message via WebSocket if connected
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                try {
                    const messagePayload = JSON.stringify({ type: "user_message", content: messageText });
                    console.log("Attempting to send message:", messagePayload);
                    window.socket.send(messagePayload);
                    console.log("Message sent via WebSocket.");
                 } catch (error) {
                    // Handle potential errors during send
                    console.error("Error sending message via WebSocket:", error);
                    addMonitorLog(`[SYSTEM] Error sending message: ${error.message}`);
                    addChatMessage("Failed to send message. Connection issue?", "status");
                 }
            } else {
                // Handle case where socket is not ready
                console.error("Cannot send message: WebSocket is not connected or not open. Current state:", window.socket ? window.socket.readyState : 'Socket not initialized');
                addChatMessage("Cannot send message: Not connected to the backend.", "status");
                addMonitorLog("[SYSTEM] Cannot send message: WebSocket not connected or not open.");
            }

            // Clear and refocus input area
            chatTextarea.value = '';
            // Auto-resize textarea after sending
            chatTextarea.style.height = 'auto';
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        } else {
            console.log("Message input is empty.");
        }
        chatTextarea.focus(); // Keep focus on input
    };
    // Attach listeners for chat input
    if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
    if (chatTextarea) {
        chatTextarea.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); } });
        chatTextarea.addEventListener('input', () => { chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; });
    }

    // Action Button Clicks (Event Delegation on body)
     document.body.addEventListener('click', event => {
        if (event.target.classList.contains('action-btn')) {
             const commandText = event.target.textContent.trim();
             console.log(`Action button clicked: ${commandText}`);
             addMonitorLog(`User clicked action: ${commandText}`);
             // Send action command to backend
             if (socket && socket.readyState === WebSocket.OPEN) {
                 try { socket.send(JSON.stringify({ type: "action_command", command: commandText })); }
                 catch (error) { console.error("Failed to send action_command:", error); addMonitorLog(`[SYSTEM] Error sending action.`); }
             } else { addMonitorLog(`[SYSTEM] Cannot send action: WS not connected.`); }
         }
    });

    // Jump to Live Button
     if (jumpToLiveButton) {
         jumpToLiveButton.addEventListener('click', () => {
            console.log("'> Jump to live' button clicked.");
            if(monitorContentElement){ monitorContentElement.scrollTop = monitorContentElement.scrollHeight; }
        });
     }


    // --- Initial Load Actions ---
    loadTasks(); // Load tasks & counter from localStorage
    renderTaskList(); // Render the initial list
    connectWebSocket(); // Establish WebSocket connection

    // // Optionally send context switch for the initially loaded task on connect
    // // Requires moving this logic inside socket.onopen
    // if (currentTaskId) {
    //     const currentTask = tasks.find(task => task.id === currentTaskId);
    //     // TODO: Send initial context if needed, maybe via onopen
    // }

}); // End of DOMContentLoaded listener

