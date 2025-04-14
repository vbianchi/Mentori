// js/script.js
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
    let socket;

    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        socket = new WebSocket(wsUrl);

        socket.onopen = (event) => {
            console.log("WebSocket connection opened:", event);
            // Optional: Send an initial message or identifier
            // socket.send(JSON.stringify({ type: "hello", content: "UI connected" }));
        };

        socket.onmessage = (event) => {
            console.log("WebSocket message received:", event.data);
            try {
                const message = JSON.parse(event.data);
                switch (message.type) {
                    case 'agent_message':
                        addChatMessage(message.content, 'agent');
                        break;
                    case 'user_message': // Backend might echo user message, handle if needed
                        // addChatMessage(message.content, 'user'); // Already added optimistically
                        break;
                    case 'status_message':
                        addChatMessage(message.content, 'status');
                        break;
                    case 'monitor_log':
                        addMonitorLog(message.content);
                        break;
                    // Add cases for other message types from backend if needed
                    default:
                        console.warn("Received unknown message type:", message.type);
                }
            } catch (error) {
                console.error("Failed to parse WebSocket message or process it:", error);
                addMonitorLog(`[SYSTEM] Error processing message from backend: ${error.message}`);
            }
        };

        socket.onerror = (event) => {
            console.error("WebSocket error:", event);
            addChatMessage("Error connecting to the backend server.", "status");
            addMonitorLog(`[SYSTEM] WebSocket connection error: ${event.type || 'Unknown error'}`);
        };

        socket.onclose = (event) => {
            console.log("WebSocket connection closed:", event);
            addChatMessage("Connection to backend server closed.", "status");
            addMonitorLog(`[SYSTEM] WebSocket disconnected. Code: ${event.code}, Reason: ${event.reason || 'No reason given'}`);
            // Optional: Attempt to reconnect after a delay
            // setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
        };
    };

    // --- Helper Functions --- (ScrollToBottom, addChatMessage, addMonitorLog - slightly adapted)

    const scrollToBottom = (element) => {
        if (element) {
            // Scroll down only if user isn't scrolled up manually
            const shouldScroll = element.scrollTop + element.clientHeight >= element.scrollHeight - 50; // Tolerance of 50px
             if (shouldScroll) {
                element.scrollTop = element.scrollHeight;
             }
        }
    };

    const addChatMessage = (text, type = 'agent') => {
         if (!chatMessagesContainer) return;
         const messageElement = document.createElement('div');
         messageElement.classList.add('message');
         let isSimpleText = true;

         switch (type) {
            case 'user':
                messageElement.classList.add('user-message');
                // Add user-message class to CSS for proper styling
                // Temp inline styles:
                messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);';
                break;
            case 'status':
                messageElement.classList.add('agent-status');
                break;
            case 'suggestion':
                messageElement.classList.add('agent-suggestion');
                break;
            case 'warning':
                 messageElement.classList.add('agent-warning');
                 break;
            case 'action-prompt':
                 isSimpleText = false;
                 messageElement.classList.add('action-prompt');
                 messageElement.innerHTML = `<p>${text}</p><button class="action-btn">Default Action</button>`;
                 break;
            case 'agent':
            default:
                messageElement.classList.add('agent-message');
                 messageElement.style.border = '1px solid var(--border-color)'; // Ensure agent messages have border
                break;
        }

        if (isSimpleText) {
             messageElement.textContent = text;
        }

        chatMessagesContainer.appendChild(messageElement);
        scrollToBottom(chatMessagesContainer);
    };

    const addMonitorLog = (text) => {
        if (!monitorCodeElement) return;
        // Add timestamp consistently on the frontend for logs received
        const timestamp = new Date().toISOString().substring(11, 23); // HH:MM:SS.sss
        monitorCodeElement.textContent += `[${timestamp}] ${text}\n`;
        scrollToBottom(monitorContentElement);
    };

    // --- Event Listeners ---

    // Task Selection (Simplified - clears chat/monitor)
    if (taskListContainer) {
         taskListContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('task-item')) {
                 // ... (task activation styling remains the same) ...
                 const currentActive = taskListContainer.querySelector('.task-item.active');
                if (currentActive) {
                    currentActive.classList.remove('active');
                }
                const clickedItem = event.target;
                clickedItem.classList.add('active');
                console.log(`Task selected: ${clickedItem.textContent.trim()}`);

                // Clear UI and notify backend (if socket is connected)
                 chatMessagesContainer.innerHTML = '';
                 monitorCodeElement.textContent = '';
                 addChatMessage(`Switched to task: ${clickedItem.textContent.trim()}`, 'status');
                 if (socket && socket.readyState === WebSocket.OPEN) {
                     socket.send(JSON.stringify({ type: "context_switch", task: clickedItem.textContent.trim() }));
                 } else {
                    addMonitorLog("[SYSTEM] Cannot notify backend of context switch: WebSocket not connected.");
                 }
            }
        });
    }

    // Chat Input - Send via WebSocket
    const handleSendMessage = () => {
        const messageText = chatTextarea.value.trim();
        if (messageText) {
            // 1. Display user message optimistically in UI
            addChatMessage(messageText, 'user');

            // 2. Send message to backend via WebSocket
            if (socket && socket.readyState === WebSocket.OPEN) {
                try {
                    socket.send(JSON.stringify({ type: "user_message", content: messageText }));
                     console.log(`User message sent via WebSocket: ${messageText}`);
                 } catch (error) {
                    console.error("Failed to send message via WebSocket:", error);
                    addMonitorLog(`[SYSTEM] Error sending message: ${error.message}`);
                 }
            } else {
                console.error("WebSocket is not connected.");
                addChatMessage("Cannot send message: Not connected to the backend.", "status");
                addMonitorLog("[SYSTEM] Cannot send message: WebSocket not connected.");
            }

            // 3. Clear input area
            chatTextarea.value = '';
            chatTextarea.style.height = 'auto';
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px';

            // --- REMOVED setTimeout simulations ---

        } else {
            console.log("Message input is empty.");
        }
        chatTextarea.focus();
    };

    if (chatSendButton) {
        chatSendButton.addEventListener('click', handleSendMessage);
    }
    // ... (keydown and input listeners for textarea remain the same) ...
    if (chatTextarea) {
        chatTextarea.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleSendMessage();
            }
        });
        chatTextarea.addEventListener('input', () => {
            chatTextarea.style.height = 'auto';
            chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        });
    }


    // New Task Button (Simplified)
    if (newTaskButton) {
        newTaskButton.addEventListener('click', () => {
             console.log("'+ New Task' button clicked.");
             chatMessagesContainer.innerHTML = '';
             monitorCodeElement.textContent = '';
             addChatMessage("New task started. Please provide the goal.", "status");
             if (socket && socket.readyState === WebSocket.OPEN) {
                 socket.send(JSON.stringify({ type: "new_task" }));
             } else {
                 addMonitorLog("[SYSTEM] Cannot notify backend of new task: WebSocket not connected.");
             }
         });
    }

    // Action Button Clicks (remain the same for now - just log)
     document.body.addEventListener('click', event => {
        if (event.target.classList.contains('action-btn')) {
             console.log(`Action button clicked: ${event.target.textContent.trim()}`);
             addMonitorLog(`User clicked action: ${event.target.textContent.trim()}`);
             // FUTURE: Send action command via WebSocket
             if (socket && socket.readyState === WebSocket.OPEN) {
                // Example: identify action based on text or data attribute
                socket.send(JSON.stringify({ type: "action_command", command: event.target.textContent.trim() }));
             }
         }
    });

    // Jump to Live Button (remains the same)
     if (jumpToLiveButton) {
        jumpToLiveButton.addEventListener('click', () => {
            console.log("'> Jump to live' button clicked.");
            scrollToBottom(monitorContentElement);
        });
     }

    // --- Initialize WebSocket Connection ---
    connectWebSocket();

    // Initial UI setup if needed (e.g. scroll monitor)
    // scrollToBottom(monitorContentElement); // Let initial connection messages handle scrolling

}); // End of DOMContentLoaded listener