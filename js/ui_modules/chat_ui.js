// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status).
 * - Handles Markdown formatting.
 * - Displays the agent's proposed plan for confirmation with inline details.
 * - Transforms the plan UI to a static confirmed state.
 * - Renders persistent confirmed plans from history.
 * - Manages the chat input area, including input history.
 * - Shows/hides the "agent thinking" status and handles its click.
 */

let chatMessagesContainerElement;
let agentThinkingStatusElement; 
let chatTextareaElement;
let chatSendButtonElement;

let onSendMessageCallback = (messageText) => console.warn("[ChatUI] onSendMessageCallback not set in chat_ui.js. Message:", messageText);
let onThinkingStatusClickCallback = () => console.warn("[ChatUI] onThinkingStatusClickCallback not set in chat_ui.js"); 

let chatInputHistory = [];
const MAX_CHAT_HISTORY = 50; 
let chatHistoryIndex = -1;
let currentInputBuffer = ""; 

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

    if (callbacks && typeof callbacks.onSendMessage === 'function') {
        onSendMessageCallback = callbacks.onSendMessage;
    }
    if (callbacks && typeof callbacks.onThinkingStatusClick === 'function') {
        onThinkingStatusClickCallback = callbacks.onThinkingStatusClick;
    }

    if (chatSendButtonElement) {
        chatSendButtonElement.addEventListener('click', handleSendButtonClick);
    }
    if (chatTextareaElement) {
        chatTextareaElement.addEventListener('keydown', handleChatTextareaKeydown);
        chatTextareaElement.addEventListener('input', handleChatTextareaInput); 
    }
    if (agentThinkingStatusElement) {
        agentThinkingStatusElement.addEventListener('click', () => {
            console.log("[ChatUI] Agent thinking status clicked.");
            if (typeof onThinkingStatusClickCallback === 'function') {
                onThinkingStatusClickCallback();
            }
        });
    }
    console.log("[ChatUI] Initialized.");
}

function handleSendButtonClick() {
    const messageText = chatTextareaElement.value.trim();
    if (messageText) {
        if (typeof onSendMessageCallback === 'function') {
            onSendMessageCallback(messageText); 
        }
        addMessageToInputHistory(messageText); 
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

        if (chatHistoryIndex === -1) { 
            currentInputBuffer = chatTextareaElement.value;
        }

        if (event.key === 'ArrowUp') {
            if (chatHistoryIndex === -1) { 
                chatHistoryIndex = chatInputHistory.length - 1;
            } else if (chatHistoryIndex > 0) { 
                chatHistoryIndex--;
            }
            chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) { 
                chatHistoryIndex++;
                chatTextareaElement.value = chatInputHistory[chatHistoryIndex];
            } else { 
                chatHistoryIndex = -1;
                chatTextareaElement.value = currentInputBuffer;
            }
        }
        chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length; 
        adjustTextareaHeight();
    } else {
        chatHistoryIndex = -1;
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
}

function adjustTextareaHeight() {
    if (!chatTextareaElement) return;
    chatTextareaElement.style.height = 'auto'; 
    chatTextareaElement.style.height = (chatTextareaElement.scrollHeight) + 'px';
}

function addMessageToInputHistory(messageText) {
    if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
        chatInputHistory.push(messageText);
        if (chatInputHistory.length > MAX_CHAT_HISTORY) {
            chatInputHistory.shift(); 
        }
    }
    chatHistoryIndex = -1; 
    currentInputBuffer = ""; 
}

function formatMessageContentInternal(text) {
    if (typeof text !== 'string') {
        console.warn("[ChatUI] formatMessageContentInternal received non-string input:", text);
        text = String(text); 
    }
    let formattedText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = code; 
        const langClass = lang ? ` class="language-${lang}"` : '';
        return `<pre><code${langClass}>${escapedCode}</code></pre>`;
    });

    formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); 
        if (linkText.includes('&lt;') || linkText.includes('&gt;')) return match;
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
    });

    formattedText = formattedText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
    formattedText = formattedText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
    formattedText = formattedText.replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');

    const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
    for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith('<pre') && !parts[i].startsWith('<a') && !parts[i].startsWith('<code')) {
            parts[i] = parts[i].replace(/\n/g, '<br>');
        }
    }
    formattedText = parts.join('');

    return formattedText;
}

function addChatMessageToUI(text, type = 'agent', doScroll = true) {
    if (!chatMessagesContainerElement) { 
        console.error("[ChatUI] Chat container missing! Cannot add message:", text);
        return null; 
    }

    if (type === 'status') {
        const lowerText = text.toLowerCase();
        if (!(lowerText.includes("connect") || lowerText.includes("clos") || lowerText.includes("error") || lowerText.includes("plan") || lowerText.includes("task") || lowerText.includes("upload") || lowerText.includes("history"))) {
            console.log("[ChatUI] Skipping non-critical status message in chat:", text);
            return null; 
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
    if (type === 'user') messageElement.classList.add('user-message'); 
    if (type === 'agent') messageElement.classList.add('agent-message'); 
    
    if (type === 'confirmed_plan_log' && text) { 
        messageElement.classList.remove('message-agent'); 
        messageElement.classList.add('message-system', 'plan-confirmation-container', 'plan-confirmed-static'); 
        try {
            const planData = JSON.parse(text); 
            
            const titleElement = document.createElement('h4');
            titleElement.textContent = planData.title || 'Confirmed Plan (from history):'; 
            messageElement.appendChild(titleElement);

            const summaryElement = document.createElement('p');
            summaryElement.className = 'plan-summary';
            summaryElement.innerHTML = formatMessageContentInternal(planData.summary || "Summary not available.");
            messageElement.appendChild(summaryElement);

            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'plan-steps-details';
            detailsDiv.style.display = 'block'; 
            
            const ol = document.createElement('ol');
            if (planData.steps && Array.isArray(planData.steps)) {
                planData.steps.forEach(step => { 
                    const li = document.createElement('li'); 
                    const stepDescription = `<strong>${step.step_id}. ${formatMessageContentInternal(step.description)}</strong>`;
                    const toolUsed = (step.tool_to_use && step.tool_to_use !== "None") ? `<br><span class="step-tool">Tool: ${formatMessageContentInternal(step.tool_to_use)}</span>` : '';
                    const inputHint = step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContentInternal(step.tool_input_instructions)}</span>` : '';
                    const expectedOutcome = `<br><span class="step-expected">Expected: ${formatMessageContentInternal(step.expected_outcome)}</span>`;
                    li.innerHTML = stepDescription + toolUsed + inputHint + expectedOutcome; 
                    ol.appendChild(li); 
                });
            }
            detailsDiv.appendChild(ol); 
            messageElement.appendChild(detailsDiv);

            if (planData.timestamp) {
                const timestampP = document.createElement('p');
                timestampP.style.fontSize = '0.8em';
                timestampP.style.color = 'var(--text-color-muted)';
                timestampP.style.marginTop = '5px';
                timestampP.textContent = `Confirmed at: ${new Date(planData.timestamp).toLocaleString()}`;
                messageElement.appendChild(timestampP);
            }

        } catch (e) {
            console.error("[ChatUI] Error parsing confirmed_plan_log data:", e, "Raw Data:", text);
            messageElement.innerHTML = formatMessageContentInternal(`Error displaying confirmed plan from history. Data: ${text.substring(0, 200)}...`);
        }
    } else { 
        messageElement.innerHTML = formatMessageContentInternal(text);
    }

    if (agentThinkingStatusElement && agentThinkingStatusElement.style.display !== 'none' && messageElement !== agentThinkingStatusElement) {
        const thinkingStatusWasPresent = agentThinkingStatusElement.parentNode === chatMessagesContainerElement;
        if (thinkingStatusWasPresent) {
            chatMessagesContainerElement.removeChild(agentThinkingStatusElement);
        }
        chatMessagesContainerElement.appendChild(messageElement);
        if (thinkingStatusWasPresent) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
    } else {
        chatMessagesContainerElement.appendChild(messageElement);
    }

    if (doScroll) {
        scrollToBottomChat();
    }
    return messageElement; 
}

function displayPlanConfirmationUI(humanSummary, planId, structuredPlan, onConfirm, onCancel, onViewDetails) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Cannot display plan confirmation: Chat messages container not initialized.");
        return;
    }

    const existingPlanUIs = chatMessagesContainerElement.querySelectorAll('.plan-confirmation-container');
    existingPlanUIs.forEach(ui => ui.remove());
    console.log("[ChatUI] Removed any existing plan confirmation UIs.");

    const planContainer = document.createElement('div');
    planContainer.className = 'message message-system plan-confirmation-container'; 
    planContainer.dataset.planId = planId; 

    const titleElement = document.createElement('h4');
    titleElement.textContent = 'Agent Proposed Plan:';
    planContainer.appendChild(titleElement);

    const summaryElement = document.createElement('p');
    summaryElement.className = 'plan-summary';
    summaryElement.innerHTML = formatMessageContentInternal(humanSummary); 
    planContainer.appendChild(summaryElement);

    const detailsDiv = document.createElement('div');
    detailsDiv.className = 'plan-steps-details'; 
    detailsDiv.style.display = 'none'; 

    const ol = document.createElement('ol');
    if (structuredPlan && Array.isArray(structuredPlan)) {
        structuredPlan.forEach(step => { 
            const li = document.createElement('li'); 
            li.innerHTML = `<strong>${step.step_id}. ${formatMessageContentInternal(step.description)}</strong>` +
                           `${step.tool_to_use && step.tool_to_use !== "None" ? `<br><span class="step-tool">Tool: ${formatMessageContentInternal(step.tool_to_use)}</span>` : ''}` +
                           `${step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContentInternal(step.tool_input_instructions)}</span>` : ''}` +
                           `<br><span class="step-expected">Expected: ${formatMessageContentInternal(step.expected_outcome)}</span>`; 
            ol.appendChild(li); 
        });
    } else {
        const li = document.createElement('li');
        li.textContent = "Plan details are not available or are in an unexpected format.";
        ol.appendChild(li);
    }
    detailsDiv.appendChild(ol); 
    planContainer.appendChild(detailsDiv); 

    const viewDetailsBtn = document.createElement('button');
    viewDetailsBtn.className = 'plan-toggle-details-btn'; 
    viewDetailsBtn.textContent = 'View Details';
    viewDetailsBtn.title = `View detailed plan for proposal ${planId}`;
    viewDetailsBtn.onclick = (e) => {
        e.stopPropagation(); 
        const isHidden = detailsDiv.style.display === 'none';
        detailsDiv.style.display = isHidden ? 'block' : 'none';
        viewDetailsBtn.textContent = isHidden ? 'Hide Details' : 'View Details';
        if (typeof onViewDetails === 'function') { 
            onViewDetails(planId, isHidden); 
        }
    };
    planContainer.appendChild(viewDetailsBtn); 

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'plan-actions';

    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'plan-confirm-btn';
    confirmBtn.textContent = 'Confirm & Run';
    confirmBtn.onclick = (e) => {
        e.stopPropagation();
        if (typeof onConfirm === 'function') {
            onConfirm(planId); 
        }
    };
    actionsDiv.appendChild(confirmBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'plan-cancel-btn';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = (e) => {
        e.stopPropagation();
        if (typeof onCancel === 'function') {
            onCancel(planId); 
        }
    };
    actionsDiv.appendChild(cancelBtn);
    planContainer.appendChild(actionsDiv);

    if (agentThinkingStatusElement && agentThinkingStatusElement.style.display !== 'none' && agentThinkingStatusElement.parentNode === chatMessagesContainerElement) {
        chatMessagesContainerElement.insertBefore(planContainer, agentThinkingStatusElement);
    } else {
        chatMessagesContainerElement.appendChild(planContainer);
    }

    scrollToBottomChat(); 
    console.log(`[ChatUI] Displayed plan confirmation for plan ID: ${planId}`);
}

function transformToConfirmedPlanUI(planId) {
    console.log(`[ChatUI] Transforming plan UI to confirmed state for plan ID: ${planId}`);
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat messages container not found. Cannot transform plan UI.");
        return;
    }

    const planContainer = chatMessagesContainerElement.querySelector(`.plan-confirmation-container[data-plan-id="${planId}"]`);
    if (!planContainer) {
        console.warn(`[ChatUI] Plan container with ID ${planId} not found for transformation.`);
        addChatMessageToUI(`Plan (ID: ${planId.substring(0,8)}...) confirmed and execution started.`, 'status');
        return;
    }

    const titleElement = planContainer.querySelector('h4');
    if (titleElement) {
        titleElement.textContent = 'Plan Confirmed:';
    }

    const viewDetailsBtn = planContainer.querySelector('.plan-toggle-details-btn');
    if (viewDetailsBtn) {
        viewDetailsBtn.remove();
    }

    const actionsDiv = planContainer.querySelector('.plan-actions');
    if (actionsDiv) {
        actionsDiv.remove();
    }

    const detailsDiv = planContainer.querySelector('.plan-steps-details');
    if (detailsDiv) {
        detailsDiv.style.display = 'block';
    }

    let statusP = planContainer.querySelector('.plan-execution-status-confirmed'); 
    if (!statusP) {
        statusP = document.createElement('p');
        statusP.className = 'plan-execution-status-confirmed'; 
        statusP.style.fontSize = '0.9em';
        statusP.style.marginTop = '10px';
        statusP.style.color = 'var(--accent-color)'; 
        statusP.style.fontWeight = '500';
        const summaryElement = planContainer.querySelector('.plan-summary');
        if (summaryElement && summaryElement.nextSibling) {
            summaryElement.parentNode.insertBefore(statusP, summaryElement.nextSibling);
        } else if (detailsDiv && detailsDiv.nextSibling) {
             detailsDiv.parentNode.insertBefore(statusP, detailsDiv.nextSibling);
        }
        else {
            planContainer.appendChild(statusP);
        }
    }
    statusP.textContent = `Status: Confirmed & Execution Started (at ${new Date().toLocaleTimeString()})`;

    planContainer.classList.add('plan-confirmed-static');

    console.log(`[ChatUI] Plan UI ${planId} transformed to confirmed state.`);
    scrollToBottomChat();
}


function showAgentThinkingStatusInUI(show, statusText = "Thinking...") {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;
    if (show) {
        agentThinkingStatusElement.textContent = statusText;
        agentThinkingStatusElement.style.display = 'block';
        chatMessagesContainerElement.appendChild(agentThinkingStatusElement); 
        scrollToBottomChat();
    } else {
        agentThinkingStatusElement.style.display = 'none';
    }
}

function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        const thinkingStatus = chatMessagesContainerElement.querySelector('.agent-thinking-status');
        chatMessagesContainerElement.innerHTML = ''; 
        if (thinkingStatus) {
            chatMessagesContainerElement.appendChild(thinkingStatus); 
            thinkingStatus.style.display = 'none'; 
        }
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
    }
}
