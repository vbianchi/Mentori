// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status).
 * - Handles Markdown formatting.
 * - Displays the agent's proposed plan for confirmation.
 * - Manages the chat input area, including input history.
 * - Shows/hides the "agent thinking" status and handles its click.
 */

let chatMessagesContainerElement;
let agentThinkingStatusElement; // Local reference within this module
let chatTextareaElement;
let chatSendButtonElement;

let onSendMessageCallback = (messageText) => console.warn("onSendMessageCallback not set in chat_ui.js");
let onThinkingStatusClickCallback = () => console.warn("onThinkingStatusClickCallback not set in chat_ui.js"); // New callback

let chatInputHistory = [];
const MAX_CHAT_HISTORY = 10;
let chatHistoryIndex = -1;
let currentInputBuffer = "";

/**
 * Initializes the Chat UI module.
 * @param {object} elements - DOM elements { chatMessagesContainer, agentThinkingStatusEl, chatTextareaEl, chatSendButtonEl }
 * @param {object} callbacks - Object containing callback functions { onSendMessage, onThinkingStatusClick }
 */
function initChatUI(elements, callbacks) {
    console.log("[ChatUI] Initializing...");
    chatMessagesContainerElement = elements.chatMessagesContainer;
    agentThinkingStatusElement = elements.agentThinkingStatusEl; // Store local reference
    chatTextareaElement = elements.chatTextareaEl;
    chatSendButtonElement = elements.chatSendButtonEl;

    if (!chatMessagesContainerElement) console.error("[ChatUI] Chat messages container not provided!");
    if (!agentThinkingStatusElement) console.error("[ChatUI] Agent thinking status element not provided!");
    if (!chatTextareaElement) console.error("[ChatUI] Chat textarea element not provided!");
    if (!chatSendButtonElement) console.error("[ChatUI] Chat send button element not provided!");

    onSendMessageCallback = callbacks.onSendMessage;
    if (callbacks.onThinkingStatusClick) {
        onThinkingStatusClickCallback = callbacks.onThinkingStatusClick;
    }

    if (chatSendButtonElement) {
        chatSendButtonElement.addEventListener('click', handleSendButtonClick);
    }
    if (chatTextareaElement) {
        chatTextareaElement.addEventListener('keydown', handleChatTextareaKeydown);
        chatTextareaElement.addEventListener('input', handleChatTextareaInput);
    }
    // Add click listener for agentThinkingStatusElement
    if (agentThinkingStatusElement) {
        agentThinkingStatusElement.addEventListener('click', () => {
            console.log("[ChatUI] Agent thinking status clicked.");
            onThinkingStatusClickCallback();
        });
    }
    console.log("[ChatUI] Initialized.");
}

function handleSendButtonClick() {
    const messageText = chatTextareaElement.value.trim();
    if (messageText) {
        onSendMessageCallback(messageText); 
        chatTextareaElement.value = '';
        adjustTextareaHeight();
    }
    chatTextareaElement.focus();
}

function handleChatTextareaKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendButtonClick(); }
    else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        if (chatInputHistory.length === 0) return; event.preventDefault();
        if (chatHistoryIndex === -1) { currentInputBuffer = chatTextareaElement.value; }
        if (event.key === 'ArrowUp') {
            if (chatHistoryIndex === -1) { chatHistoryIndex = chatInputHistory.length - 1; }
            else if (chatHistoryIndex > 0) { chatHistoryIndex--; }
            chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                chatHistoryIndex++; chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
            } else { chatHistoryIndex = -1; chatTextareaElement.value = currentInputBuffer; }
        }
        chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length;
        adjustTextareaHeight();
    } else { chatHistoryIndex = -1; currentInputBuffer = ""; }
}

function handleChatTextareaInput() { adjustTextareaHeight(); }
function adjustTextareaHeight() { if (!chatTextareaElement) return; chatTextareaElement.style.height = 'auto'; chatTextareaElement.style.height = chatTextareaElement.scrollHeight + 'px'; }

function addMessageToInputHistory(messageText) {
    if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
        chatInputHistory.push(messageText);
        if (chatInputHistory.length > MAX_CHAT_HISTORY) { chatInputHistory.shift(); }
    }
    chatHistoryIndex = -1; currentInputBuffer = "";
}

function formatMessageContentInternal(text) {
    let formattedText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => { const escapedCode = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); const langClass = lang ? ` class="language-${lang}"` : ''; return `<pre><code${langClass}>${escapedCode}</code></pre>`; });
    formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');
    formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => { const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); if (linkText.includes('&lt;') || linkText.includes('&gt;')) return match; return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`; });
    formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
    formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
    formattedText = formattedText.replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');
    const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
    for (let i = 0; i < parts.length; i++) { if (!parts[i].startsWith('<pre') && !parts[i].startsWith('<a') && !parts[i].startsWith('<code')) { parts[i] = parts[i].replace(/\n/g, '<br>'); } }
    formattedText = parts.join('');
    return formattedText;
}

function addChatMessageToUI(text, type = 'agent', doScroll = true) {
    if (!chatMessagesContainerElement) { console.error("[ChatUI] Chat container missing!"); return null; }
    if (type === 'status') { const lowerText = text.toLowerCase(); if (!(lowerText.includes("connect") || lowerText.includes("clos") || lowerText.includes("error"))) { console.log("[ChatUI] Skipping non-critical status message in chat:", text); return null; } }
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `message-${type}`);
    if (type === 'status') { const lowerText = text.toLowerCase(); if (lowerText.includes("connect") || lowerText.includes("clos")) { messageElement.classList.add('connection-status'); } if (lowerText.includes("error")) { messageElement.classList.add('error-message'); } }
    if (type === 'user') messageElement.classList.add('user-message');
    if (type === 'agent') messageElement.classList.add('agent-message');
    messageElement.innerHTML = formatMessageContentInternal(text);
    if (agentThinkingStatusElement && agentThinkingStatusElement.style.display !== 'none' && messageElement !== agentThinkingStatusElement) {
        chatMessagesContainerElement.insertBefore(agentThinkingStatusElement, null);
    }
    chatMessagesContainerElement.appendChild(messageElement);
    if (doScroll) { scrollToBottomChat(); }
    return messageElement;
}

function displayPlanInUI(humanSummary, structuredPlan, onConfirmCallback, onCancelCallback) {
    if (!chatMessagesContainerElement) return;
    const existingPlanUI = chatMessagesContainerElement.querySelector('.plan-confirmation-container');
    if (existingPlanUI) existingPlanUI.remove();
    const planContainer = document.createElement('div');
    planContainer.className = 'message message-system plan-confirmation-container';
    const title = document.createElement('h4'); title.textContent = "Agent's Proposed Plan:"; planContainer.appendChild(title);
    const summaryP = document.createElement('p'); summaryP.className = 'plan-summary'; summaryP.innerHTML = formatMessageContentInternal(humanSummary); planContainer.appendChild(summaryP);
    const detailsDiv = document.createElement('div'); detailsDiv.className = 'plan-steps-details'; detailsDiv.style.display = 'none';
    const ol = document.createElement('ol');
    structuredPlan.forEach(step => { const li = document.createElement('li'); li.innerHTML = `<strong>${step.step_id}. ${formatMessageContentInternal(step.description)}</strong> ${step.tool_to_use && step.tool_to_use !== "None" ? `<br><span class="step-tool">Tool: ${step.tool_to_use}</span>` : ''} ${step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContentInternal(step.tool_input_instructions)}</span>` : ''} <br><span class="step-expected">Expected: ${formatMessageContentInternal(step.expected_outcome)}</span>`; ol.appendChild(li); });
    detailsDiv.appendChild(ol); planContainer.appendChild(detailsDiv);
    const toggleBtn = document.createElement('button'); toggleBtn.className = 'plan-toggle-details-btn'; toggleBtn.textContent = 'Show Details';
    toggleBtn.onclick = () => { const isHidden = detailsDiv.style.display === 'none'; detailsDiv.style.display = isHidden ? 'block' : 'none'; toggleBtn.textContent = isHidden ? 'Hide Details' : 'Show Details'; };
    planContainer.appendChild(toggleBtn);
    const actionsDiv = document.createElement('div'); actionsDiv.className = 'plan-actions';
    const confirmBtn = document.createElement('button'); confirmBtn.className = 'plan-confirm-btn'; confirmBtn.textContent = 'Confirm & Run Plan';
    confirmBtn.onclick = () => { onConfirmCallback(structuredPlan); confirmBtn.disabled = true; cancelBtn.disabled = true; toggleBtn.disabled = true; planContainer.style.opacity = "0.7"; planContainer.style.borderLeftColor = "var(--text-color-darker)"; };
    actionsDiv.appendChild(confirmBtn);
    const cancelBtn = document.createElement('button'); cancelBtn.className = 'plan-cancel-btn'; cancelBtn.textContent = 'Cancel Plan';
    cancelBtn.onclick = () => { onCancelCallback(); planContainer.remove(); };
    actionsDiv.appendChild(cancelBtn); planContainer.appendChild(actionsDiv);
    chatMessagesContainerElement.appendChild(planContainer); scrollToBottomChat();
}

function showAgentThinkingStatusInUI(show, statusText = "Thinking...") {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;
    if (show) {
        agentThinkingStatusElement.textContent = statusText;
        agentThinkingStatusElement.style.display = 'block';
        chatMessagesContainerElement.appendChild(agentThinkingStatusElement); // Ensure it's at the end
        scrollToBottomChat();
    } else {
        agentThinkingStatusElement.style.display = 'none';
    }
}

function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.innerHTML = '';
        if (agentThinkingStatusElement) { // Re-add hidden thinking status for future use
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
