// js/websocket_manager.js

// This script handles the WebSocket connection and raw message sending/receiving.
// It calls a global function `dispatchWsMessage` (expected to be in script.js)
// to handle the content of received messages.

const wsUrl = 'ws://localhost:8765';
window.socket = null; // Make socket globally accessible for now, might be refined later

/**
 * Establishes and manages the WebSocket connection.
 * @param {function} onOpenCallback - Called when the WebSocket connection is successfully opened.
 * @param {function} onCloseCallback - Called when the WebSocket connection is closed.
 * @param {function} onErrorCallback - Called when a WebSocket error occurs.
 */
function connectWebSocket(onOpenCallback, onCloseCallback, onErrorCallback) {
    console.log(`[WS_MANAGER] Attempting to connect to WebSocket: ${wsUrl}`);
    // Ensure any existing socket is properly closed before creating a new one
    if (window.socket && window.socket.readyState !== WebSocket.CLOSED) {
        console.log("[WS_MANAGER] Closing existing WebSocket connection before reconnecting.");
        window.socket.close(1000, "Client-initiated reconnection");
    }

    try {
        window.socket = new WebSocket(wsUrl);
    } catch (error) {
        console.error("[WS_MANAGER] Fatal Error creating WebSocket object:", error);
        if (onErrorCallback) {
            onErrorCallback(error, true); // Pass a flag indicating it's a creation error
        }
        window.socket = null;
        return;
    }

    window.socket.onopen = (event) => {
        console.log("[WS_MANAGER] WebSocket connection opened successfully.");
        if (onOpenCallback) {
            onOpenCallback(event);
        }
    };

    window.socket.onmessage = (event) => {
        try {
            const parsedMessage = JSON.parse(event.data);
            // console.log("[WS_MANAGER] Received message:", parsedMessage); // For debugging
            if (typeof dispatchWsMessage === 'function') {
                dispatchWsMessage(parsedMessage); // dispatchWsMessage is expected to be global (in script.js)
            } else {
                console.error("[WS_MANAGER] dispatchWsMessage function is not defined globally.");
            }
        } catch (error) {
            console.error("[WS_MANAGER] Failed to parse or dispatch WS message:", error, "Raw Data:", event.data);
            // Optionally, notify the main script of a parsing error
            if (typeof dispatchWsMessage === 'function') {
                dispatchWsMessage({ type: 'error_parsing_message', content: `Failed to parse message: ${event.data.substring(0,100)}`});
            }
        }
    };

    window.socket.onerror = (event) => {
        console.error("[WS_MANAGER] WebSocket error event:", event);
        if (onErrorCallback) {
            onErrorCallback(event, false); // Not a creation error
        }
        window.socket = null; // Ensure socket is null on error
    };

    window.socket.onclose = (event) => {
        console.log(`[WS_MANAGER] WebSocket closed. Code: ${event.code}, Reason: '${event.reason || 'No reason given'}', Clean close: ${event.wasClean}`);
        if (onCloseCallback) {
            onCloseCallback(event);
        }
        window.socket = null; // Ensure socket is null on close
    };
}

/**
 * Sends a message through the WebSocket.
 * @param {string} type - The type of the message.
 * @param {object} content - The content of the message.
 * @returns {boolean} - True if the message was sent, false otherwise.
 */
function sendWsMessage(type, content) {
    if (window.socket && window.socket.readyState === WebSocket.OPEN) {
        try {
            const payload = JSON.stringify({ type: type, ...content }); // Spread content directly
            // console.log(`[WS_MANAGER] Sending WS message: ${type}`, content); // For debugging
            window.socket.send(payload);
            return true;
        } catch (e) {
            console.error(`[WS_MANAGER] Error sending ${type} via WebSocket:`, e);
            return false;
        }
    } else {
        console.warn(`[WS_MANAGER] Cannot send ${type}: WebSocket is not open or not initialized.`);
        return false;
    }
}