// js/script.js
/**
 * This script handles the frontend logic for the AI Agent UI,
 * including WebSocket communication, DOM manipulation, and event handling.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    const taskListContainer = document.querySelector('.task-list');
    const chatMessagesContainer = document.querySelector('.chat-messages');
    const monitorCodeElement = document.querySelector('.monitor-content pre code');
    const monitorContentElement = document.querySelector('.monitor-content'); // For scrolling
    const chatTextarea = document.querySelector('.chat-input-area textarea');
    const chatSendButton = document.querySelector('.chat-input-area button');
    const newTaskButton = document.querySelector('.new-task-btn');
    const jumpToLiveButton = document.querySelector('.jump-live-btn');

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket; // Declare socket variable in this scope

    // Assign socket to window for console access - Initialized to null
    window.socket = null;
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
                window.socket.close(1000, "Reconnecting");
            }

            // Create new WebSocket connection
            socket = new WebSocket(wsUrl);
            window.socket = socket; // Assign to window for console access immediately
            console.log("WebSocket object created. Assigning to window.socket.");

        } catch (error) {
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
            addChatMessage("Connected to backend.", "status");
        };

        /**
         * Handles incoming messages from the WebSocket server.
         */
        socket.onmessage = (event) => {
            // console.log("WebSocket message received:", event.data); // Can be noisy, uncomment for deep debugging
            try {
                const message = JSON.parse(event.data);
                // Process message based on its type
                switch (message.type) {
                    case 'agent_message':
                        addChatMessage(message.content, 'agent');
                        break;
                    case 'status_message':
                        addChatMessage(message.content, 'status');
                        break;
                    case 'monitor_log':
                        // *** CONSOLE LOG TO CONFIRM RECEIPT ***
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
        const isScrolledToBottom = element.scrollHeight - element.clientHeight <= element.scrollTop + 50; // 50px tolerance
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
         if (type === 'status' && (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos") || text.toLowerCase().includes("error"))) {
            messageElement.classList.add('connection-status');
         }

         // Apply type-specific classes and potentially structure
         switch (type) {
            case 'user':
                messageElement.classList.add('user-message'); // For CSS styling
                // Example inline style (better to define in CSS)
                messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);';
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
                 // Example inline style (better to define in CSS)
                 messageElement.style.border = '1px solid var(--border-color)';
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
     * @param {string} text The log text content (backend should include timestamp/prefix).
     */
    const addMonitorLog = (text) => {
        if (!monitorCodeElement) { console.error("Monitor code element not found!"); return; }
        // Backend now sends timestamped logs, just display the text received
        // Using textNode is safer than manipulating textContent directly for large logs
        const logLine = document.createTextNode(`${text}\n`);
        monitorCodeElement.appendChild(logLine);
        scrollToBottom(monitorContentElement); // Scroll down after adding
     };


    // --- Event Listeners ---

    // Task Selection in Left Panel
     if (taskListContainer) {
         taskListContainer.addEventListener('click', (event) => {
            // Handle clicks only on actual task items
            if (event.target.matches('.task-item')) {
                 // Remove active class from previous item
                 const currentActive = taskListContainer.querySelector('.task-item.active');
                 if (currentActive) { currentActive.classList.remove('active'); }
                 // Add active class to clicked item
                const clickedItem = event.target;
                clickedItem.classList.add('active');
                const taskText = clickedItem.textContent.trim();
                console.log(`Task selected: ${taskText}`);

                 // Clear main panels for context switch
                 chatMessagesContainer.innerHTML = '';
                 monitorCodeElement.textContent = ''; // Clear monitor text
                 addChatMessage(`Switched to task: ${taskText}`, 'status');

                 // Notify backend of context switch
                 if (socket && socket.readyState === WebSocket.OPEN) {
                     try {
                        socket.send(JSON.stringify({ type: "context_switch", task: taskText }));
                     } catch (error) {
                         console.error("Failed to send context_switch message:", error);
                         addMonitorLog("[SYSTEM] Error sending context switch to backend.");
                     }
                 } else {
                    addMonitorLog("[SYSTEM] Cannot notify backend of context switch: WebSocket not connected.");
                 }
            }
        });
     }

     // Chat Input Area Logic
    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
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
        // Send on Enter (but not Shift+Enter)
        chatTextarea.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevent newline
                handleSendMessage();
            }
        });
        // Auto-resize textarea on input
        chatTextarea.addEventListener('input', () => {
            chatTextarea.style.height = 'auto'; // Temporarily shrink
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; // Grow to content
        });
     }

      // New Task Button
      if (newTaskButton) {
         newTaskButton.addEventListener('click', () => {
             console.log("'+ New Task' button clicked.");
             // Clear UI elements
             chatMessagesContainer.innerHTML = '';
             monitorCodeElement.textContent = '';
             addChatMessage("New task started. Please provide the goal.", "status");
             // Notify backend
             if (socket && socket.readyState === WebSocket.OPEN) {
                 try {
                    socket.send(JSON.stringify({ type: "new_task" }));
                 } catch (error) {
                     console.error("Failed to send new_task message:", error);
                     addMonitorLog("[SYSTEM] Error sending new task notification.");
                 }
             } else {
                 addMonitorLog("[SYSTEM] Cannot notify backend of new task: WebSocket not connected.");
             }
         });
      }

      // Action Button Clicks (using event delegation on body)
      document.body.addEventListener('click', event => {
        // Check if the clicked element has the 'action-btn' class
        if (event.target.classList.contains('action-btn')) {
             const commandText = event.target.textContent.trim();
             console.log(`Action button clicked: ${commandText}`);
             addMonitorLog(`User clicked action: ${commandText}`);
             // Send action command to backend
             if (socket && socket.readyState === WebSocket.OPEN) {
                 try {
                    socket.send(JSON.stringify({ type: "action_command", command: commandText }));
                 } catch (error) {
                     console.error("Failed to send action_command message:", error);
                     addMonitorLog(`[SYSTEM] Error sending action '${commandText}'.`);
                 }
             } else {
                 addMonitorLog(`[SYSTEM] Cannot send action '${commandText}': WebSocket not connected.`);
             }
         }
      });

      // Jump to Live Button (Scroll Monitor)
      if (jumpToLiveButton) {
         jumpToLiveButton.addEventListener('click', () => {
            console.log("'> Jump to live' button clicked.");
            if(monitorContentElement){
                // Force scroll to bottom
                monitorContentElement.scrollTop = monitorContentElement.scrollHeight;
            }
        });
      }


    // --- Initialize WebSocket Connection ---
    connectWebSocket();

}); // End of DOMContentLoaded listener