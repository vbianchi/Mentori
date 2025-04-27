// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, event handling,
 * task history management, chat input history, and Markdown formatting.
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

    // --- Artifact State ---
    let currentTaskArtifacts = []; // Stores {type: 'image'|'text', url: string, filename: string}
    let currentArtifactIndex = -1;

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket;
    window.socket = null; // Make accessible globally for debugging if needed
    console.log("Initialized window.socket to null.");

    /**
     * Establishes and manages the WebSocket connection.
     */
    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        addMonitorLog("[SYSTEM] Attempting to connect to backend...");
        // Clear previous status messages
        chatMessagesContainer.querySelectorAll('.connection-status').forEach(el => el.remove());
        try {
            // Close existing socket if reconnecting
            if (window.socket && window.socket.readyState !== WebSocket.CLOSED) {
                console.log("Closing existing WebSocket connection before reconnecting.");
                window.socket.close(1000, "Reconnecting");
            }
            socket = new WebSocket(wsUrl);
            window.socket = socket; // Update global reference
            console.log("WebSocket object created.");
        } catch (error) {
            console.error("Fatal Error creating WebSocket object:", error);
            addChatMessage("FATAL: Failed to initialize WebSocket connection.", "status");
            addMonitorLog(`[SYSTEM] FATAL Error creating WebSocket: ${error.message}`);
            window.socket = null;
            return; // Stop connection attempt
        }

        socket.onopen = (event) => {
            console.log("WebSocket connection opened successfully.");
            addMonitorLog(`[SYSTEM] WebSocket connection established.`);
            addChatMessage("Connected to backend.", "status");
            // If a task was active before connection, send context switch
            if (currentTaskId) {
                const currentTask = tasks.find(task => task.id === currentTaskId);
                if (currentTask) {
                    console.log("Sending initial context switch on connection open.");
                    try {
                        socket.send(JSON.stringify({ type: "context_switch", task: currentTask.title, taskId: currentTask.id }));
                    } catch (error) {
                        console.error("Failed to send initial context_switch:", error);
                        addMonitorLog(`[SYSTEM] Error sending initial context switch: ${error.message}`);
                    }
                } else {
                     console.warn("currentTaskId set, but task not found in list on connection open.");
                     currentTaskId = null; // Reset if task is invalid
                     updateArtifactDisplay(); // Clear artifacts for no task
                }
            } else {
                updateArtifactDisplay(); // Ensure artifact display is cleared if no task active
            }
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.debug("Received WS message:", message); // Log received message for debugging

                switch (message.type) {
                    case 'history_start':
                        console.log("Received history_start signal."); isLoadingHistory = true;
                        clearChatAndMonitor(false); addChatMessage(`Loading history...`, "status"); break;
                    case 'history_end':
                        console.log("Received history_end signal."); isLoadingHistory = false;
                        // Remove "Loading history..." message if it's the last one
                        const loadingMsg = chatMessagesContainer.querySelector('.message-status:last-child');
                        if (loadingMsg && loadingMsg.textContent.startsWith("Loading history...")) { loadingMsg.remove(); }
                        scrollToBottom(chatMessagesContainer);
                        scrollToBottom(monitorLogAreaElement);
                        break;

                    // Handle Token Streaming with Formatting
                    case 'agent_token_chunk':
                        if (!currentStreamingMessageElement) {
                            console.log("Creating new message element for streaming.");
                            currentStreamingMessageElement = addChatMessage("", 'agent', false); // Don't scroll yet
                        }
                        if (currentStreamingMessageElement) {
                            // Append raw text first
                            currentStreamingMessageElement.textContent += message.content;
                            // Re-apply formatting to the entire accumulated text
                            currentStreamingMessageElement.innerHTML = formatMessageContent(currentStreamingMessageElement.textContent);
                            scrollToBottom(chatMessagesContainer); // Scroll as content streams
                        } else { console.warn("Received token chunk but no streaming element."); }
                        break;

                    case 'agent_message': // Handles full agent messages (e.g., from history or non-streamed final answers)
                        console.log("Received full agent_message:", message.content.substring(0, 100) + "...");
                        addChatMessage(message.content, 'agent'); // Formats the full message
                        currentStreamingMessageElement = null; // Ensure streaming stops/resets
                        break;
                    case 'user': // Handle user messages from history
                        console.log("Received user history message:", message.content);
                        addChatMessage(message.content, 'user'); // User messages are plain text
                        currentStreamingMessageElement = null;
                        break;
                    case 'status_message':
                        addChatMessage(message.content, 'status'); // Status messages are plain text
                        // If agent processing is complete or errored, ensure streaming stops
                        if (message.content.toLowerCase().includes("complete") || message.content.toLowerCase().includes("error")) {
                            console.log("Resetting streaming element due to status message:", message.content);
                            currentStreamingMessageElement = null;
                        }
                        break;
                    case 'monitor_log':
                        // console.log("Received monitor_log:", message.content); // Already logged by addMonitorLog
                        addMonitorLog(message.content);
                        break;
                    case 'update_artifacts': // Handles full list updates (e.g., from history OR after agent run)
                        console.log("Received update_artifacts message with content:", message.content);
                        if (Array.isArray(message.content)) {
                            currentTaskArtifacts = message.content; // Replace entire list
                            // Display the latest artifact (first in the list as server sorts by mtime)
                            currentArtifactIndex = currentTaskArtifacts.length > 0 ? 0 : -1;
                            updateArtifactDisplay();
                        } else {
                            console.warn("Invalid update_artifacts message content (not an array):", message.content);
                            currentTaskArtifacts = []; currentArtifactIndex = -1; updateArtifactDisplay();
                        }
                        break;

                    // *** REMOVED 'new_artifact' case ***
                    // case 'new_artifact': ...

                    case 'user_message': break; // Ignore live echo of user's own message
                    default:
                        console.warn("Received unknown message type:", message.type, "Content:", message.content);
                        addMonitorLog(`[SYSTEM] Unknown message type received: ${message.type}`);
                        currentStreamingMessageElement = null; // Reset streaming just in case
                }
            } catch (error) {
                console.error("Failed to parse/process WS message:", error, "Data:", event.data);
                addMonitorLog(`[SYSTEM] Error processing message: ${error.message}.`);
                currentStreamingMessageElement = null; // Reset streaming on error
            }
        };

        socket.onerror = (event) => {
             // Log the raw event for more details if possible
            console.error("WebSocket error event:", event);
            addChatMessage("ERROR: Cannot connect to backend.", "status", true); // Ensure scroll on error
            addMonitorLog(`[SYSTEM] WebSocket error occurred.`);
            window.socket = null;
            currentStreamingMessageElement = null;
        };
        socket.onclose = (event) => {
            console.log(`WebSocket closed. Code: ${event.code}, Reason: '${event.reason || 'No reason given'}' Clean close: ${event.wasClean}`);
            let reason = event.reason || 'No reason given';
            let advice = "";
            if (event.code === 1000 || event.wasClean) { // Normal closure
                reason = "Normal";
            } else { // Abnormal closure
                reason = `Abnormal (Code: ${event.code})`;
                advice = " Backend down or network issue?";
            }
            addChatMessage(`Connection closed.${advice}`, "status", true); // Ensure scroll on close
            addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`);
            window.socket = null;
            currentStreamingMessageElement = null;
            // Optional: Attempt reconnection after a delay
            // setTimeout(connectWebSocket, 5000); // Example: try reconnecting after 5 seconds
        };
    };

    // --- Helper Functions ---
    const scrollToBottom = (element) => { if (!element) return; element.scrollTop = element.scrollHeight; };

    /**
     * Basic sanitation and Markdown to HTML conversion for agent messages.
     * Handles newlines, code blocks, bold, italics, and links.
     */
    const formatMessageContent = (text) => {
        // 1. Sanitize basic HTML chars FIRST
        let formattedText = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        // 2. Convert ```code blocks``` to <pre><code>
        formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
             const escapedCode = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); // Re-escape inside code block
             const langClass = lang ? ` class="language-${lang}"` : '';
             return `<pre><code${langClass}>${escapedCode}</code></pre>`;
           });

        // 3. Convert Markdown Links: [text](url) -> <a href="url">text</a>
        formattedText = formattedText.replace(
            /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
            (match, linkText, linkUrl) => {
                const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); // Ensure quotes in URL are handled
                // Basic check to avoid creating links inside existing HTML tags (simple version)
                if (linkText.includes('<') || linkText.includes('>')) return match; // Avoid if link text contains HTML
                return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
            }
        );

        // 4. Convert Bold and Italics (ensure they don't interfere with HTML tags)
        // Process these *after* links and code blocks
        // Handle triple first (***text*** or ___text___)
        formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
        // Bold (**text** or __text__)
        formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
        // Italics (*text* or _text_)
        formattedText = formattedText.replace(/(\*|_)(?=\S)([\s\S]*?\S)\1/g, '<em>$2</em>');


        // 5. Convert remaining newlines to <br> (ONLY outside of pre/code tags)
        const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>)/s); // Split by pre blocks AND links
        for (let i = 0; i < parts.length; i += 2) { // Only process parts outside <pre> and <a>
            parts[i] = parts[i].replace(/\n/g, '<br>');
        }
        formattedText = parts.join('');

        return formattedText;
       };


    /**
     * Adds a message element to the chat display area, formatting agent/user messages.
     */
    const addChatMessage = (text, type = 'agent', doScroll = true) => {
        if (!chatMessagesContainer) { console.error("Chat container missing!"); return null; }
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `message-${type}`);
        if (type === 'status') { if (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos")) { messageElement.classList.add('connection-status'); } if (text.toLowerCase().includes("error")) { messageElement.classList.add('error-message'); } }
        if (type === 'user') { messageElement.classList.add('user-message'); /* Style handled by CSS */ }
        if (type === 'agent') { messageElement.classList.add('agent-message'); /* Style handled by CSS */ }

        if (type === 'agent') {
            messageElement.innerHTML = formatMessageContent(text); // Apply formatting
        } else {
            messageElement.textContent = text; // User/Status messages as plain text
        }

        chatMessagesContainer.appendChild(messageElement);
        if (doScroll) scrollToBottom(chatMessagesContainer);
        return messageElement;
    };

    /**
     * Adds a log entry to the monitor panel with appropriate styling.
     */
    const addMonitorLog = (fullLogText) => {
        if (!monitorLogAreaElement) { console.error("Monitor log area element (#monitor-log-area) not found!"); return; }
        const logEntryDiv = document.createElement('div');
        logEntryDiv.classList.add('monitor-log-entry');

        // Regex to extract timestamp, session, optional type, and content
        const logRegex = /^(\[.*?\]\[.*?\])\s*(?:\[(.*?)\])?\s*(.*)$/s;
        const match = fullLogText.match(logRegex);

        let timestampPrefix = "";
        let logTypeIndicator = "";
        let logContent = fullLogText; // Default if regex fails
        let logType = "unknown"; // Default type

        if (match) {
            timestampPrefix = match[1] || "";
            logTypeIndicator = (match[2] || "").trim().toUpperCase(); // Type indicator like [TOOL START]
            logContent = match[3] || ""; // The actual log message content

            // Determine log type based on indicator
            if (logTypeIndicator.includes("TOOL START")) logType = 'tool-start';
            else if (logTypeIndicator.includes("TOOL OUTPUT")) logType = 'tool-output';
            else if (logTypeIndicator.includes("TOOL ERROR")) logType = 'tool-error';
            else if (logTypeIndicator.includes("AGENT FINISH")) logType = 'agent-finish';
            else if (logTypeIndicator.includes("ERROR") || logTypeIndicator.includes("ERR_")) logType = 'error'; // Catch ERR_ from history
            else if (logTypeIndicator.includes("HISTORY")) logType = 'history';
            else if (logTypeIndicator.includes("SYSTEM") || logTypeIndicator.includes("SYS_")) logType = 'system';
            else if (logTypeIndicator.includes("ARTIFACT")) logType = 'artifact-generated'; // Catch ARTIFACT_GENERATED etc.
            else if (logTypeIndicator.includes("USER INPUT")) logType = 'user-input'; // Style user input in monitor?
            // Add more specific types if needed based on backend logs
        } else {
            // Fallback type detection if regex fails (less reliable)
            if (fullLogText.toLowerCase().includes("error")) logType = 'error';
            else if (fullLogText.toLowerCase().includes("system")) logType = 'system';
        }

        logEntryDiv.classList.add(`log-type-${logType}`);

        // Add timestamp span if present
        if (timestampPrefix) {
            const timeSpan = document.createElement('span');
            timeSpan.className = 'log-timestamp';
            timeSpan.textContent = timestampPrefix;
            logEntryDiv.appendChild(timeSpan);
        }

        // Add content span
        const contentSpan = document.createElement('span');
        contentSpan.className = 'log-content';
        // Use <pre> for tool output/error for better formatting
        if (logType === 'tool-output' || logType === 'tool-error') {
            const pre = document.createElement('pre');
            pre.textContent = logContent.trim(); // Use textContent for pre to preserve whitespace
            contentSpan.appendChild(pre);
        } else {
            // Use innerHTML for other types to render potential simple HTML/links if ever needed
            // Be cautious if backend sends complex HTML here. Basic text is safer.
            contentSpan.textContent = logContent.trim();
        }
        logEntryDiv.appendChild(contentSpan);

        monitorLogAreaElement.appendChild(logEntryDiv);
        scrollToBottom(monitorLogAreaElement);
    };

    /**
     * Updates the artifact display area based on currentTaskArtifacts and currentArtifactIndex.
     */
    const updateArtifactDisplay = async () => {
        if (!monitorArtifactAreaElement || !artifactNavElement || !artifactPrevBtn || !artifactNextBtn || !artifactCounterElement) {
            console.error("Artifact display elements not found!");
            return;
        }
        // Clear previous artifact content (but keep nav controls)
        while (monitorArtifactAreaElement.firstChild && monitorArtifactAreaElement.firstChild !== artifactNavElement) {
            monitorArtifactAreaElement.removeChild(monitorArtifactAreaElement.firstChild);
        }

        if (currentTaskArtifacts.length === 0 || currentArtifactIndex < 0 || currentArtifactIndex >= currentTaskArtifacts.length) {
            // Handle empty list or invalid index
            const placeholder = document.createElement('div');
            placeholder.className = 'artifact-placeholder';
            placeholder.textContent = 'No artifacts generated yet.';
            monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
            artifactNavElement.style.display = 'none'; // Hide nav if no artifacts
        } else {
            const artifact = currentTaskArtifacts[currentArtifactIndex];

            // Validate artifact data
            if (!artifact || !artifact.url || !artifact.filename || !artifact.type) {
                console.error("Invalid artifact data:", artifact);
                const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
                monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
                artifactNavElement.style.display = 'none';
                return;
            }

            // Display based on type
            if (artifact.type === 'image') {
                const imgElement = document.createElement('img');
                imgElement.src = artifact.url;
                imgElement.alt = `Generated image: ${artifact.filename}`;
                imgElement.title = `Generated image: ${artifact.filename}`;
                imgElement.onerror = () => {
                    console.error(`Error loading image from URL: ${artifact.url}`);
                    imgElement.remove(); // Remove broken image placeholder
                    const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: `Error loading image: ${artifact.filename}` });
                    monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
                };
                monitorArtifactAreaElement.insertBefore(imgElement, artifactNavElement);
            } else if (artifact.type === 'text') {
                const preElement = document.createElement('pre');
                preElement.textContent = 'Loading text file...'; // Placeholder
                monitorArtifactAreaElement.insertBefore(preElement, artifactNavElement);
                try {
                    console.log(`Fetching text artifact: ${artifact.url}`);
                    // Add headers if needed for auth/session in future
                    const response = await fetch(artifact.url);
                    if (!response.ok) {
                        // Throw error with status text for better debugging
                        throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                    }
                    const textContent = await response.text();
                    preElement.textContent = textContent; // Display fetched text
                    console.log(`Successfully fetched and displayed ${artifact.filename}`);
                } catch (error) {
                    console.error(`Error fetching text artifact ${artifact.filename}:`, error);
                    preElement.textContent = `Error loading file: ${artifact.filename}\n${error.message}`;
                    preElement.classList.add('artifact-error'); // Style as error
                }
            } else {
                // Handle unknown artifact types
                console.warn(`Unsupported artifact type: ${artifact.type} for file ${artifact.filename}`);
                const unknownDiv = Object.assign(document.createElement('div'), { className: 'artifact-placeholder', textContent: `Unsupported artifact type: ${artifact.filename}` });
                monitorArtifactAreaElement.insertBefore(unknownDiv, artifactNavElement);
            }

            // Update navigation controls
            if (currentTaskArtifacts.length > 1) {
                artifactCounterElement.textContent = `Artifact ${currentArtifactIndex + 1} of ${currentTaskArtifacts.length}`;
                artifactPrevBtn.disabled = (currentArtifactIndex === 0);
                artifactNextBtn.disabled = (currentArtifactIndex === currentTaskArtifacts.length - 1);
                artifactNavElement.style.display = 'flex'; // Show nav if multiple artifacts
            } else {
                artifactNavElement.style.display = 'none'; // Hide nav if only one artifact
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
                // Sort by timestamp descending (newest first)
                tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
                console.log(`Loaded ${tasks.length} tasks. Next Task #: ${taskCounter + 1}`);
            } catch (e) {
                console.error("Failed to parse tasks from localStorage:", e);
                tasks = [];
                localStorage.removeItem(STORAGE_KEY); // Clear corrupted data
            }
        } else {
            tasks = [];
            firstLoad = true;
            console.log("No tasks found in localStorage.");
        }

        // Auto-create first task only if storage was empty AND no tasks exist
        if (firstLoad && tasks.length === 0) {
            console.log("First load with no tasks, creating 'Task - 1'.");
            taskCounter = 1; // Start counter at 1
            const firstTask = {
                id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`,
                title: `Task - ${taskCounter}`,
                timestamp: Date.now()
            };
            tasks.unshift(firstTask); // Add to beginning
            currentTaskId = firstTask.id;
            saveTasks(); // Save the newly created task
            console.log("Auto-created and selected 'Task - 1'.");
        } else {
            // Determine active task: last active, first in list, or null
            const lastActiveId = localStorage.getItem(`${STORAGE_KEY}_active`);
            if (lastActiveId && tasks.some(task => task.id === lastActiveId)) {
                currentTaskId = lastActiveId;
            } else if (tasks.length > 0) {
                currentTaskId = tasks[0].id; // Default to the newest task
            } else {
                currentTaskId = null; // No tasks exist
            }
        }
        console.log("Initial currentTaskId set to:", currentTaskId);
    };
    const saveTasks = () => {
        try {
            // Ensure tasks are sorted before saving (optional, but maintains order)
             tasks.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
            localStorage.setItem(COUNTER_KEY, taskCounter.toString());
            if (currentTaskId) {
                localStorage.setItem(`${STORAGE_KEY}_active`, currentTaskId);
            } else {
                localStorage.removeItem(`${STORAGE_KEY}_active`);
            }
        } catch (e) {
            console.error("Failed to save tasks to localStorage:", e);
            // Maybe inform the user?
            alert("Error saving task list. Changes might not persist.");
        }
    };
    const renderTaskList = () => {
        console.log(`--- Rendering Task List (Current ID: ${currentTaskId}) ---`);
        if (!taskListUl) { console.error("Task list UL element not found!"); return; }
        taskListUl.innerHTML = ''; // Clear existing list items
        if (tasks.length === 0) {
            taskListUl.innerHTML = '<li class="task-item-placeholder">No tasks yet.</li>';
        } else {
            tasks.forEach((task) => {
                const li = document.createElement('li');
                li.className = 'task-item';
                li.dataset.taskId = task.id;

                const titleSpan = document.createElement('span');
                titleSpan.className = 'task-title';
                // Truncate long titles visually, but keep full title in 'title' attribute
                const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title;
                titleSpan.textContent = displayTitle;
                titleSpan.title = task.title; // Show full title on hover
                li.appendChild(titleSpan);

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'task-delete-btn';
                deleteBtn.textContent = '🗑️'; // Use emoji for delete icon
                deleteBtn.title = `Delete Task: ${task.title}`;
                deleteBtn.dataset.taskId = task.id; // Set task ID for the button too
                // Prevent click on delete button from selecting the task
                deleteBtn.addEventListener('click', (event) => {
                     event.stopPropagation(); // Stop click from bubbling up to the li
                     handleDeleteTaskClick(task.id, task.title);
                });
                li.appendChild(deleteBtn);

                // Add click listener to the list item itself for selection
                li.addEventListener('click', () => {
                     handleTaskItemClick(task.id);
                });


                if (task.id === currentTaskId) {
                    li.classList.add('active');
                }
                taskListUl.appendChild(li);
            });
        }
        updateCurrentTaskTitle(); // Update header title
        console.log(`--- Finished Rendering Task List ---`);
    };

    // Separate click handlers for clarity
    const handleTaskItemClick = (taskId) => {
         console.log(`Task item clicked: ${taskId}`);
         selectTask(taskId);
    };
    const handleDeleteTaskClick = (taskId, taskTitle) => {
         console.log(`Delete button clicked for task: ${taskId} (${taskTitle})`);
         deleteTask(taskId, taskTitle);
    };


    const updateCurrentTaskTitle = () => {
        if (!currentTaskTitleElement) return;
        const currentTask = tasks.find(task => task.id === currentTaskId);
        const title = currentTask ? currentTask.title : "No Task Selected";
        currentTaskTitleElement.textContent = title;
        // Update monitor status as well
        if(monitorStatusElement) monitorStatusElement.textContent = currentTask ? "Agent Idle" : "No Task";
        if(monitorFooterStatusElement) monitorFooterStatusElement.textContent = currentTask ? `Task: ${title}` : "No Task Selected";
    };
    const clearChatAndMonitor = (addLog = true) => {
        if (chatMessagesContainer) chatMessagesContainer.innerHTML = '';
        if (monitorLogAreaElement) monitorLogAreaElement.innerHTML = '';
        currentTaskArtifacts = []; // Clear artifacts array
        currentArtifactIndex = -1;
        updateArtifactDisplay(); // Update display to show placeholder
        if (addLog && monitorLogAreaElement) { // Check if monitor area exists
             addMonitorLog("[SYSTEM] Cleared context.");
        }
        console.log("Cleared chat and monitor.");
    };
    const selectTask = (taskId) => {
        console.log(`Attempting to select task: ${taskId}`);
        if (currentTaskId === taskId && taskId !== null) {
             console.log("Task already selected.");
             return; // Avoid unnecessary actions if already selected
        }

        const task = tasks.find(t => t.id === taskId);
        // If task not found in list, deselect (set to null)
        currentTaskId = task ? taskId : null;

        console.log(`Selected task ID set to: ${currentTaskId}`);
        saveTasks(); // Save the new active task ID
        renderTaskList(); // Re-render list to show active state

        // Send context switch message if connected and a valid task is selected
        if (currentTaskId && task && socket && socket.readyState === WebSocket.OPEN) {
            const payload = { type: "context_switch", task: task.title, taskId: task.id };
            try {
                console.log(`Sending context_switch for task ${task.id}...`);
                socket.send(JSON.stringify(payload));
                console.log(`Sent context_switch.`);
                // Clear chat immediately for responsiveness, history will load
                clearChatAndMonitor(false);
                 addChatMessage("Switching task context...", "status"); // Show loading status
            } catch (e) {
                console.error(`Failed to send context_switch:`, e);
                addMonitorLog(`[SYSTEM] Error sending context switch: ${e.message}`);
                 addChatMessage("Error switching task context.", "status");
            }
        } else if (!currentTaskId) {
            // Handle case where no task is selected (e.g., after deleting the last task)
            clearChatAndMonitor();
            addChatMessage("No task selected.", "status");
            addMonitorLog("[SYSTEM] No task selected.");
        } else if (!socket || socket.readyState !== WebSocket.OPEN) {
             // Handle case where selection happens while disconnected
             clearChatAndMonitor(false); // Clear UI but don't log system message yet
             addChatMessage("Switched task locally. Connect to backend to load history.", "status");
             addMonitorLog(`[SYSTEM] Switched task locally to ${taskId}, but WS not open.`);
        }
        console.log(`Finished select task logic for: ${currentTaskId}`);
    };
    const handleNewTaskClick = () => {
        console.log("'+ New Task' button clicked.");
        taskCounter++; // Increment counter
        const taskTitle = `Task - ${taskCounter}`;
        const newTask = {
            id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, // More unique ID
            title: taskTitle,
            timestamp: Date.now() // Store creation time for sorting
        };
        tasks.unshift(newTask); // Add to the beginning of the array (newest)
        console.log("New task created:", newTask);
        // Select the newly created task
        selectTask(newTask.id);
        // Note: saveTasks() is called within selectTask()
        console.log("handleNewTaskClick finished.");
    };
    const deleteTask = (taskId, taskTitle) => {
        console.log(`Attempting to delete task: ${taskId} (${taskTitle})`);
        // Confirmation dialog
        if (!confirm(`Are you sure you want to delete task "${taskTitle}"? This cannot be undone.`)) {
            console.log("Deletion cancelled by user.");
            return;
        }

        // Filter out the task locally
        const taskIndex = tasks.findIndex(task => task.id === taskId);
        if (taskIndex === -1) {
             console.warn(`Task ${taskId} not found locally for deletion.`);
             return; // Should not happen if UI is correct
        }
        tasks.splice(taskIndex, 1); // Remove task from local array
        console.log(`Task ${taskId} removed locally.`);

        // Send delete request to backend if connected
        if (socket && socket.readyState === WebSocket.OPEN) {
            try {
                socket.send(JSON.stringify({ type: "delete_task", taskId: taskId }));
                console.log(`Sent delete_task request for ${taskId} to backend.`);
                addMonitorLog(`[SYSTEM] Requested deletion of task ${taskId}.`);
            } catch (e) {
                console.error(`Failed send delete_task:`, e);
                addMonitorLog(`[SYSTEM] Error sending delete request: ${e.message}`);
                // Optionally inform user that backend delete might have failed
                 addChatMessage("Error sending delete request to backend.", "status");
            }
        } else {
            addMonitorLog(`[SYSTEM] Cannot notify backend of delete: WS not open.`);
             addChatMessage("Task deleted locally. Connect to backend to sync deletion.", "status");
        }

        // Determine the next task to select
        let nextTaskId = null;
        if (currentTaskId === taskId) { // If the deleted task was active
            // Select the next newest task (first in the sorted list) or null if no tasks left
            nextTaskId = tasks.length > 0 ? tasks[0].id : null;
            console.log(`Deleted active task, selecting next: ${nextTaskId}`);
            // selectTask will handle clearing UI etc.
             selectTask(nextTaskId);
        } else {
            // If a different task was deleted, keep the current one active
            // Just re-render the list and save the state
             saveTasks();
             renderTaskList();
        }

        console.log(`Finished delete task logic for: ${taskId}`);
    };

    // --- Event Listeners Setup ---
    if (newTaskButton) { newTaskButton.addEventListener('click', handleNewTaskClick); }
    else { console.error("New task button element not found!"); }

    // Use event delegation for task list clicks (select/delete)
    if (taskListUl) {
         // Removed the direct listener on taskListUl, handled by listeners added in renderTaskList
         console.log("Task list event listeners will be added during rendering.");
    } else { console.error("Task list UL element not found!"); }


    // Chat Input Sending Logic
    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
        if (!currentTaskId){
             alert("Please select or create a task first.");
             chatTextarea.focus();
             return;
        }
        if (messageText) {
            addChatMessage(messageText, 'user'); // Display user message immediately
            // Add to input history if different from last entry
            if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
                chatInputHistory.push(messageText);
                if (chatInputHistory.length > MAX_CHAT_HISTORY) {
                    chatInputHistory.shift(); // Keep history size limited
                }
            }
            chatHistoryIndex = -1; // Reset history navigation index
            currentInputBuffer = ""; // Clear buffer used for history navigation

            // Send message to backend via WebSocket
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                try {
                    const payload = JSON.stringify({ type: "user_message", content: messageText });
                    console.log("Sending user_message:", payload);
                    window.socket.send(payload);
                    console.log("Message sent.");
                     addChatMessage("Agent processing...", "status"); // Indicate processing start
                } catch (e) {
                    console.error("Error sending message via WebSocket:", e);
                    addMonitorLog(`[SYSTEM] Error sending message: ${e.message}`);
                    addChatMessage("Error: Could not send message.", "status");
                }
            } else {
                console.error("Cannot send: WebSocket is not open.");
                addChatMessage("Cannot send: Not connected to backend.", "status");
                addMonitorLog("[SYSTEM] Cannot send message: WS not open.");
            }

            // Clear textarea and adjust height
            chatTextarea.value = '';
            chatTextarea.style.height = 'auto'; // Reset height
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; // Set to content height
        } else {
            console.log("Attempted to send empty message.");
        }
        chatTextarea.focus(); // Keep focus on input
    };
    if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
    if (chatTextarea) {
        chatTextarea.addEventListener('keydown', (event) => {
            // Send on Enter (unless Shift+Enter)
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevent default newline insertion
                handleSendMessage();
            }
            // Handle chat input history navigation (ArrowUp/ArrowDown)
            else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
                if (chatInputHistory.length === 0) return; // No history to navigate
                event.preventDefault();

                if (chatHistoryIndex === -1) {
                    // Store current input before navigating history
                    currentInputBuffer = chatTextarea.value;
                }

                if (event.key === 'ArrowUp') {
                    if (chatHistoryIndex === -1) { // Start from the end
                        chatHistoryIndex = chatInputHistory.length - 1;
                    } else if (chatHistoryIndex > 0) { // Move up
                        chatHistoryIndex--;
                    }
                    chatTextarea.value = chatInputHistory[chatHistoryIndex];
                } else if (event.key === 'ArrowDown') {
                    if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) { // Move down
                        chatHistoryIndex++;
                        chatTextarea.value = chatInputHistory[chatHistoryIndex];
                    } else { // Return to originally typed text (or empty)
                        chatHistoryIndex = -1;
                        chatTextarea.value = currentInputBuffer;
                    }
                }
                // Move cursor to end after setting value
                chatTextarea.selectionStart = chatTextarea.selectionEnd = chatTextarea.value.length;
                // Adjust height after changing content
                chatTextarea.style.height = 'auto';
                chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
            } else {
                // Reset history index if any other key is pressed
                chatHistoryIndex = -1;
                currentInputBuffer = ""; // Clear buffer if not navigating
            }
        });
        // Auto-resize textarea on input
        chatTextarea.addEventListener('input', () => {
            chatTextarea.style.height = 'auto'; // Reset height to shrink if needed
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; // Set to content height
        });
    }

    // Event delegation for potential future action buttons in chat
     document.body.addEventListener('click', event => {
         if (event.target.classList.contains('action-btn')) {
             const commandText = event.target.textContent.trim();
             console.log(`Action button clicked: ${commandText}`);
             addMonitorLog(`[USER_ACTION] Clicked: ${commandText}`);
             if (socket && socket.readyState === WebSocket.OPEN) {
                 try {
                     socket.send(JSON.stringify({ type: "action_command", command: commandText }));
                 } catch (e) {
                     console.error("Failed send action_command:", e);
                     addMonitorLog(`[SYSTEM] Error sending action command: ${e.message}`);
                 }
             } else {
                 addMonitorLog(`[SYSTEM] Cannot send action command: WS not open.`);
             }
         }
     });

    // Artifact Navigation Event Listeners
    if (artifactPrevBtn) {
        artifactPrevBtn.addEventListener('click', () => {
            if (currentArtifactIndex > 0) {
                currentArtifactIndex--;
                updateArtifactDisplay();
            }
        });
    }
    if (artifactNextBtn) {
        artifactNextBtn.addEventListener('click', () => {
            if (currentArtifactIndex < currentTaskArtifacts.length - 1) {
                currentArtifactIndex++;
                updateArtifactDisplay();
            }
        });
    }

    // --- Initial Load Actions ---
    loadTasks(); // Load tasks & counter from localStorage
    renderTaskList(); // Render initial list based on loaded tasks
    connectWebSocket(); // Connect WS (sends initial context if needed)

}); // End of DOMContentLoaded listener

