// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status).
 * - Handles Markdown formatting.
 * - Displays the agent's proposed plan for confirmation.
 * - Manages the chat input area, including input history.
 * - Shows/hides the "agent thinking" status.
 */

// DOM Elements (will be passed during initialization)
let chatMessagesContainerElement;
let agentThinkingStatusElement;
let chatTextareaElement;
let chatSendButtonElement;

// Callbacks to be set by the main script
let onSendMessageCallback = (messageText) => console.warn("onSendMessageCallback not set in chat_ui.js");

// State for chat input history (managed within this module)
let chatInputHistory = [];
const MAX_CHAT_HISTORY = 10;
let chatHistoryIndex = -1;
let currentInputBuffer = ""; // For restoring text when navigating history

/**
 * Initializes the Chat UI module.
 * @param {object} elements - Object containing DOM elements { chatMessagesContainer, agentThinkingStatusEl, chatTextareaEl, chatSendButtonEl }
 * @param {object} callbacks - Object containing callback functions { onSendMessage }
 */
function initChatUI(elements, callbacks) {
    console.log("[ChatUI] Initializing...");
    chatMessagesContainerElement = elements.chatMessagesContainer;
    agentThinkingStatusElement = elements.agentThinkingStatusEl;
    chatTextareaElement = elements.chatTextareaEl;
    chatSendButtonElement = elements.chatSendButtonEl;

    if (!chatMessagesContainerElement) console.error("[ChatUI] Chat messages container not provided!");
    if (!agentThinkingStatusElement) console.error("[ChatUI] Agent thinking status element not provided!");
    if (!chatTextareaElement) console.error("[ChatUI] Chat textarea element not provided!");
    if (!chatSendButtonElement) console.error("[ChatUI] Chat send button element not provided!");

    onSendMessageCallback = callbacks.onSendMessage;

    // Setup event listeners for chat input
    if (chatSendButtonElement) {
        chatSendButtonElement.addEventListener('click', handleSendButtonClick);
    }
    if (chatTextareaElement) {
        chatTextareaElement.addEventListener('keydown', handleChatTextareaKeydown);
        chatTextareaElement.addEventListener('input', handleChatTextareaInput);
    }
    console.log("[ChatUI] Initialized.");
}

function handleSendButtonClick() {
    const messageText = chatTextareaElement.value.trim();
    if (messageText) {
        onSendMessageCallback(messageText); // Notify main script
        // Main script will call addChatMessageToUI for the user message
        // Main script will also handle history update
        chatTextareaElement.value = '';
        adjustTextareaHeight();
    }
    chatTextareaElement.focus();
}

function handleChatTextareaKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendButtonClick();
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        if (chatInputHistory.length === 0) return;
        event.preventDefault();

        if (chatHistoryIndex === -1) { // Entering history navigation
            currentInputBuffer = chatTextareaElement.value;
        }

        if (event.key === 'ArrowUp') {
            if (chatHistoryIndex === -1) { // Was not in history, start from last
                chatHistoryIndex = chatInputHistory.length - 1;
            } else if (chatHistoryIndex > 0) {
                chatHistoryIndex--;
            }
            chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                chatHistoryIndex++;
                chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
            } else { // Reached end of history or was not in history
                chatHistoryIndex = -1;
                chatTextareaElement.value = currentInputBuffer;
            }
        }
        chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length;
        adjustTextareaHeight();
    } else {
        // Any other key press resets history navigation
        chatHistoryIndex = -1;
        currentInputBuffer = ""; // Clear buffer as user is typing new stuff
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
    // If user types, and they were navigating history, reset index
    // but keep currentInputBuffer as is until they send or navigate again.
    if (chatHistoryIndex !== -1) {
        // chatHistoryIndex = -1; // Don't reset index immediately, allow further navigation
    }
}

function adjustTextareaHeight() {
    if (!chatTextareaElement) return;
    chatTextareaElement.style.height = 'auto'; // Reset height
    chatTextareaElement.style.height = chatTextareaElement.scrollHeight + 'px'; // Set to scroll height
}

/**
 * Adds a message to the chat input history.
 * Called by the main script after a message is successfully sent.
 * @param {string} messageText - The text of the message to add.
 */
function addMessageToInputHistory(messageText) {
    if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
        chatInputHistory.push(messageText);
        if (chatInputHistory.length > MAX_CHAT_HISTORY) {
            chatInputHistory.shift();
        }
    }
    chatHistoryIndex = -1; // Reset history navigation index
    currentInputBuffer = ""; // Clear buffer
}


function formatMessageContentInternal(text) {
    // Basic sanitization to prevent HTML injection
    let formattedText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    // Markdown for code blocks (```lang\ncode\n```)
    formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); // Re-escape inside code block
        const langClass = lang ? ` class="language-${lang}"` : '';
        return `<pre><code${langClass}>${escapedCode}</code></pre>`;
    });

    // Markdown for inline code (`code`)
    formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Markdown for links ([text](url))
    formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        // Avoid re-interpreting HTML if linkText itself contains escaped HTML
        const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); // Sanitize URL quotes
        if (linkText.includes('&lt;') || linkText.includes('&gt;')) { // If link text was already escaped, don't mess with it
            return match;
        }
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
    });
    
    // Markdown for bold+italic (***text*** or ___text___)
    formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
    // Markdown for bold (**text** or __text__)
    formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
    // Markdown for italic (*text* or _text_) - careful not to mess with underscores in words or code
    formattedText = formattedText.replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');


    // Handle newlines correctly, especially around <pre> tags
    const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
    for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith('<pre') && !parts[i].startsWith('<a') && !parts[i].startsWith('<code')) {
            parts[i] = parts[i].replace(/\n/g, '<br>');
        }
    }
    formattedText = parts.join('');

    return formattedText;
}

/**
 * Adds a chat message to the UI.
 * @param {string} text - The message text.
 * @param {string} type - The type of message ('user', 'agent', 'status', 'system_warning').
 * @param {boolean} doScroll - Whether to scroll to the bottom after adding.
 * @returns {HTMLElement|null} The created message element or null.
 */
function addChatMessageToUI(text, type = 'agent', doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing!");
        return null;
    }

    // Skip non-critical status messages from appearing in chat UI
    if (type === 'status') {
        const lowerText = text.toLowerCase();
        if (!(lowerText.includes("connect") || lowerText.includes("clos") || lowerText.includes("error"))) {
            console.log("[ChatUI] Skipping non-critical status message in chat:", text);
            return null; // Don't add to UI
        }
    }

    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `message-${type}`);

    if (type === 'status') {
        const lowerText = text.toLowerCase();
        if (lowerText.includes("connect") || lowerText.includes("clos")) {
            messageElement.classList.add('connection-status');
        }
        if (lowerText.includes("error")) {
            messageElement.classList.add('error-message');
        }
    }
    // Specific classes for user/agent for styling if needed beyond message-type
    if (type === 'user') messageElement.classList.add('user-message');
    if (type === 'agent') messageElement.classList.add('agent-message');


    messageElement.innerHTML = formatMessageContentInternal(text);

    // Ensure agent thinking status is correctly positioned before new message
    if (agentThinkingStatusElement && agentThinkingStatusElement.style.display !== 'none' && messageElement !== agentThinkingStatusElement) {
        chatMessagesContainerElement.insertBefore(agentThinkingStatusElement, null); // Move to end before new message
    }

    chatMessagesContainerElement.appendChild(messageElement);

    if (doScroll) {
        scrollToBottomChat();
    }
    return messageElement;
}

/**
 * Displays the agent's proposed plan in the chat UI for user confirmation.
 * @param {string} humanSummary - A human-readable summary of the plan.
 * @param {Array<object>} structuredPlan - The detailed steps of the plan.
 * @param {Function} onConfirmCallback - Callback when the user confirms the plan.
 * @param {Function} onCancelCallback - Callback when the user cancels the plan.
 */
function displayPlanInUI(humanSummary, structuredPlan, onConfirmCallback, onCancelCallback) {
    if (!chatMessagesContainerElement) return;

    // Remove any existing plan UI before adding a new one
    const existingPlanUI = chatMessagesContainerElement.querySelector('.plan-confirmation-container');
    if (existingPlanUI) existingPlanUI.remove();

    const planContainer = document.createElement('div');
    planContainer.className = 'message message-system plan-confirmation-container'; // Use system message style

    const title = document.createElement('h4');
    title.textContent = "Agent's Proposed Plan:";
    planContainer.appendChild(title);

    const summaryP = document.createElement('p');
    summaryP.className = 'plan-summary';
    summaryP.innerHTML = formatMessageContentInternal(humanSummary); // Use internal formatter
    planContainer.appendChild(summaryP);

    const detailsDiv = document.createElement('div');
    detailsDiv.className = 'plan-steps-details';
    detailsDiv.style.display = 'none'; // Initially hidden

    const ol = document.createElement('ol');
    structuredPlan.forEach(step => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${step.step_id}. ${formatMessageContentInternal(step.description)}</strong>
                        ${step.tool_to_use && step.tool_to_use !== "None" ? `<br><span class="step-tool">Tool: ${step.tool_to_use}</span>` : ''}
                        ${step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContentInternal(step.tool_input_instructions)}</span>` : ''}
                        <br><span class="step-expected">Expected: ${formatMessageContentInternal(step.expected_outcome)}</span>`;
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
        onConfirmCallback(structuredPlan); // Pass the confirmed plan back
        // Disable buttons and change style after click
        confirmBtn.disabled = true;
        cancelBtn.disabled = true;
        toggleBtn.disabled = true; // Also disable toggle
        planContainer.style.opacity = "0.7"; // Visually indicate it's processed
        planContainer.style.borderLeftColor = "var(--text-color-darker)"; // Change accent to muted
    };
    actionsDiv.appendChild(confirmBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'plan-cancel-btn';
    cancelBtn.textContent = 'Cancel Plan';
    cancelBtn.onclick = () => {
        onCancelCallback();
        planContainer.remove(); // Remove the plan UI
    };
    actionsDiv.appendChild(cancelBtn);

    planContainer.appendChild(actionsDiv);
    chatMessagesContainerElement.appendChild(planContainer);
    scrollToBottomChat();
}

/**
 * Shows or hides the "Agent Thinking..." status message.
 * @param {boolean} show - True to show, false to hide.
 * @param {string} [statusText="Thinking..."] - Optional text for the status.
 */
function showAgentThinkingStatusInUI(show, statusText = "Thinking...") {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;

    if (show) {
        agentThinkingStatusElement.textContent = statusText;
        agentThinkingStatusElement.style.display = 'block';
        // Ensure it's the last element or before the input area
        chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        scrollToBottomChat();
    } else {
        agentThinkingStatusElement.style.display = 'none';
    }
}

function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.innerHTML = '';
        // Re-add thinking status if it exists, hidden
        if (agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
            agentThinkingStatusElement.style.display = 'none';
        }
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
    }
}
