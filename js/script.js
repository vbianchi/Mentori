// js/script.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Agent UI Script Loaded and DOM ready!");

    // --- Get references to UI elements ---
    // ... (references remain the same) ...
    const chatMessagesContainer = document.querySelector('.chat-messages');
    const monitorCodeElement = document.querySelector('.monitor-content pre code');
    const monitorContentElement = document.querySelector('.monitor-content');

    // --- WebSocket Setup ---
    const wsUrl = 'ws://localhost:8765';
    let socket;
    window.socket = null;
    console.log("Initialized window.socket to null.");

    const connectWebSocket = () => {
        console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
        // ... (rest of connectWebSocket setup remains the same) ...
        socket = new WebSocket(wsUrl);
        window.socket = socket;
        console.log("WebSocket object created.");

        socket.onopen = (event) => {
            console.log("WebSocket connection opened successfully. Ready state:", socket.readyState);
            addMonitorLog(`[SYSTEM] WebSocket connection opened to ${wsUrl}. Ready to send.`);
            addChatMessage("Connected to backend.", "status");
        };

        socket.onmessage = (event) => {
            // console.log("WebSocket message received:", event.data); // Can be noisy
            try {
                const message = JSON.parse(event.data);
                switch (message.type) {
                    case 'agent_message':
                        addChatMessage(message.content, 'agent');
                        break;
                    case 'status_message':
                        addChatMessage(message.content, 'status');
                        break;
                    case 'monitor_log':
                        // *** ADDED CONSOLE LOG HERE ***
                        console.log("Received monitor_log:", message.content);
                        addMonitorLog(message.content); // Call the function to display it
                        break;
                    case 'user_message': break; // Ignore echo
                    default:
                        console.warn("Received unknown message type from backend:", message.type);
                        addMonitorLog(`[SYSTEM] Received unknown message type: ${message.type}`);
                }
            } catch (error) {
                console.error("Failed to parse WebSocket message or process it:", error, "Data received:", event.data);
                addMonitorLog(`[SYSTEM] Error processing message from backend: ${error.message}. Data: ${event.data}`);
            }
        };

        socket.onerror = (event) => {
             // ... (onerror logic remains same) ...
            console.error("WebSocket error observed:", event);
            addChatMessage("ERROR: Cannot connect to the backend server. Is it running?", "status");
            addMonitorLog(`[SYSTEM] WebSocket connection error. Cannot send/receive messages. Check backend server.`);
            window.socket = null;
        };

        socket.onclose = (event) => {
            // ... (onclose logic remains same) ...
            console.log(`WebSocket connection closed. Code: ${event.code}, Reason: '${event.reason}', Clean: ${event.wasClean}`);
            let reason = event.reason || 'No reason given'; let advice = "";
            if (event.code === 1000) { reason = "Normal closure"; }
            else if (!event.wasClean || event.code === 1006) { reason = `Connection closed abnormally (Code: ${event.code})`; advice = " Backend server might be down."; }
            else { reason = `Code: ${event.code}, Reason: ${reason}`; }
            addChatMessage(`Connection to backend closed.${advice}`, "status");
            addMonitorLog(`[SYSTEM] WebSocket disconnected. ${reason}`);
            window.socket = null;
        };
    };

    // --- Helper Functions --- (scrollToBottom, addChatMessage, addMonitorLog)
    // ... (Helper functions remain the same) ...
    const scrollToBottom = (element) => { /* ... */
        if (element) {
            const isScrolledToBottom = element.scrollHeight - element.clientHeight <= element.scrollTop + 50;
            if (isScrolledToBottom) { element.scrollTop = element.scrollHeight; }
        }
     };
    const addChatMessage = (text, type = 'agent') => { /* ... */
         if (!chatMessagesContainer) return;
         const messageElement = document.createElement('div');
         messageElement.classList.add('message'); let isSimpleText = true;
         messageElement.classList.add(`message-${type}`);
         if (type === 'status') { messageElement.classList.add('connection-status'); }
         switch (type) {
            case 'user': messageElement.classList.add('user-message'); messageElement.style.cssText = 'align-self: flex-end; background-color: var(--accent-color); color: white; border: 1px solid var(--accent-color);'; break;
            case 'status': messageElement.classList.add('agent-status'); if (text.toLowerCase().includes("connect") || text.toLowerCase().includes("clos")) { messageElement.classList.add('connection-status'); } break;
            case 'suggestion': messageElement.classList.add('agent-suggestion'); break;
            case 'warning': messageElement.classList.add('agent-warning'); break;
            case 'action-prompt': isSimpleText = false; messageElement.classList.add('action-prompt'); messageElement.innerHTML = `<p>${text}</p><button class="action-btn">Default Action</button>`; break;
            case 'agent': default: messageElement.classList.add('agent-message'); messageElement.style.border = '1px solid var(--border-color)'; break;
        }
        if (isSimpleText) { messageElement.textContent = text; }
        chatMessagesContainer.appendChild(messageElement); scrollToBottom(chatMessagesContainer);
     };
    const addMonitorLog = (text) => { /* ... */
        if (!monitorCodeElement) { console.error("Monitor code element not found!"); return; }
        const timestamp = new Date().toISOString().substring(11, 23);
        // Display only the text content received from backend (timestamp added there now)
        // const logLine = document.createTextNode(`${text}\n`); // Backend adds timestamp now
        // Let's re-add timestamp here for consistency in display format
        const logLine = document.createTextNode(`[${timestamp}] ${text}\n`);
        monitorCodeElement.appendChild(logLine);
        scrollToBottom(monitorContentElement);
     };


    // --- Event Listeners --- (Task Selection, Chat Input, Buttons)
    // ... (Event listeners remain the same) ...
     if (taskListContainer) { /* ... task click logic ... */
         taskListContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('task-item')) {
                 const currentActive = taskListContainer.querySelector('.task-item.active'); if (currentActive) { currentActive.classList.remove('active'); }
                const clickedItem = event.target; clickedItem.classList.add('active'); const taskText = clickedItem.textContent.trim(); console.log(`Task selected: ${taskText}`);
                 chatMessagesContainer.innerHTML = ''; monitorCodeElement.textContent = ''; addChatMessage(`Switched to task: ${taskText}`, 'status');
                 if (socket && socket.readyState === WebSocket.OPEN) { socket.send(JSON.stringify({ type: "context_switch", task: taskText })); } else { addMonitorLog("[SYSTEM] Cannot notify backend of context switch: WebSocket not connected."); }
            }
        });
     }
     const handleSendMessage = () => { /* ... */
        const messageText = chatTextarea.value.trim();
        if (messageText) {
            addChatMessage(messageText, 'user');
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                try { const messagePayload = JSON.stringify({ type: "user_message", content: messageText }); console.log("Attempting to send message:", messagePayload); window.socket.send(messagePayload); console.log("Message sent via WebSocket."); }
                catch (error) { console.error("Error sending message via WebSocket:", error); addMonitorLog(`[SYSTEM] Error sending message: ${error.message}`); addChatMessage("Failed to send message. Connection issue?", "status"); }
            } else { console.error("Cannot send message: WebSocket is not connected or not open. Current state:", window.socket ? window.socket.readyState : 'Socket not initialized'); addChatMessage("Cannot send message: Not connected to the backend.", "status"); addMonitorLog("[SYSTEM] Cannot send message: WebSocket not connected or not open."); }
            chatTextarea.value = ''; chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px';
        } else { console.log("Message input is empty."); } chatTextarea.focus();
      };
     if (chatSendButton) { chatSendButton.addEventListener('click', handleSendMessage); }
     if (chatTextarea) {
        chatTextarea.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); } });
        chatTextarea.addEventListener('input', () => { chatTextarea.style.height = 'auto'; chatTextarea.style.height = chatTextarea.scrollHeight + 'px'; });
     }
      if (newTaskButton) { /* ... new task click logic ... */
         newTaskButton.addEventListener('click', () => {
             console.log("'+ New Task' button clicked."); chatMessagesContainer.innerHTML = ''; monitorCodeElement.textContent = ''; addChatMessage("New task started. Please provide the goal.", "status");
             if (socket && socket.readyState === WebSocket.OPEN) { socket.send(JSON.stringify({ type: "new_task" })); } else { addMonitorLog("[SYSTEM] Cannot notify backend of new task: WebSocket not connected."); }
         });
      }
      document.body.addEventListener('click', event => { /* ... action button click logic ... */
        if (event.target.classList.contains('action-btn')) {
             const commandText = event.target.textContent.trim(); console.log(`Action button clicked: ${commandText}`); addMonitorLog(`User clicked action: ${commandText}`);
             if (socket && socket.readyState === WebSocket.OPEN) { socket.send(JSON.stringify({ type: "action_command", command: commandText })); } else { addMonitorLog(`[SYSTEM] Cannot send action '${commandText}': WebSocket not connected.`); }
         }
      });
      if (jumpToLiveButton) { /* ... jump to live click logic ... */
         jumpToLiveButton.addEventListener('click', () => { console.log("'> Jump to live' button clicked."); if(monitorContentElement){ monitorContentElement.scrollTop = monitorContentElement.scrollHeight; } });
      }


    // --- Initialize WebSocket Connection ---
    connectWebSocket();

}); // End of DOMContentLoaded listener

