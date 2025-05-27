// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status, step announcements).
 * - Handles Markdown formatting.
 * - Displays plan proposals and confirmed plans.
 * - Manages chat input and thinking status.
 */

let chatMessagesContainerElement;
let agentThinkingStatusElement; // Global status line at the bottom
let chatTextareaElement;
let chatSendButtonElement;
let onSendMessageCallback = (messageText) => console.warn("[ChatUI] onSendMessageCallback not set.");
let onThinkingStatusClickCallback = () => console.warn("[ChatUI] onThinkingStatusClickCallback not set.");

let chatInputHistory = [];
const MAX_CHAT_HISTORY = 50;
let chatHistoryIndex = -1;
let currentInputBuffer = "";

// For storing the currently active major step element to append sub-statuses
let currentMajorStepDiv = null;

// Map component hints from backend to CSS class modifiers for borders
const componentBorderColorMap = {
    DEFAULT: 'agent-line-default', // For final agent messages with bubbles
    USER: 'user-line-accent', // Should not have a line, but for consistency
    SYSTEM: 'agent-line-system',
    INTENT_CLASSIFIER: 'agent-line-intent-classifier',
    PLANNER: 'agent-line-planner',
    CONTROLLER: 'agent-line-controller',
    EXECUTOR: 'agent-line-executor',
    EVALUATOR_STEP: 'agent-line-evaluator-step',
    EVALUATOR_OVERALL: 'agent-line-evaluator-overall',
    TOOL: 'agent-line-tool', // Generic tool
    // Specific tools can be added if needed, e.g., TOOL_TAVILY_SEARCH_API: 'agent-line-tool-tavily'
    WARNING: 'agent-line-warning',
    ERROR: 'agent-line-error' // For recoverable/intermediate errors in thinking status
};

function initChatUI(elements, callbacks) {
    console.log("[ChatUI] Initializing...");
    chatMessagesContainerElement = elements.chatMessagesContainer;
    agentThinkingStatusElement = elements.agentThinkingStatusEl; // Global status line
    chatTextareaElement = elements.chatTextareaEl;
    chatSendButtonElement = elements.chatSendButtonEl;

    if (!chatMessagesContainerElement || !agentThinkingStatusElement || !chatTextareaElement || !chatSendButtonElement) {
        console.error("[ChatUI] One or more essential UI elements not provided!");
        return;
    }

    onSendMessageCallback = callbacks.onSendMessage || onSendMessageCallback;
    onThinkingStatusClickCallback = callbacks.onThinkingStatusClick || onThinkingStatusClickCallback;

    chatSendButtonElement.addEventListener('click', handleSendButtonClick);
    chatTextareaElement.addEventListener('keydown', handleChatTextareaKeydown);
    chatTextareaElement.addEventListener('input', handleChatTextareaInput);
    
    // Keep global thinking status clickable for now (e.g., to scroll monitor)
    agentThinkingStatusElement.addEventListener('click', () => {
        if (typeof onThinkingStatusClickCallback === 'function') {
            onThinkingStatusClickCallback();
        }
    });
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
        currentInputBuffer = ""; // Reset buffer after send
        chatHistoryIndex = -1;    // Reset history index
    }
    chatTextareaElement.focus();
}

function handleChatTextareaKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendButtonClick();
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        if (chatInputHistory.length === 0 && chatTextareaElement.value.trim() === "") return; // Allow default if field is empty and no history
        
        if (chatHistoryIndex === -1 && (chatTextareaElement.value.trim() !== "" || event.key === 'ArrowUp')) {
             // Only save to buffer if navigating away from current non-empty input or starting history nav
            if (chatInputHistory.length > 0 || event.key === 'ArrowUp') {
                 currentInputBuffer = chatTextareaElement.value;
            }
        }
        
        let newHistoryIndex = chatHistoryIndex;
        if (event.key === 'ArrowUp') {
            if (chatInputHistory.length > 0) {
                newHistoryIndex = (chatHistoryIndex === -1) ? chatInputHistory.length - 1 : Math.max(0, chatHistoryIndex - 1);
            } else { return; } // No history, do nothing
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                newHistoryIndex++;
            } else { // Reached end of history or was not in history
                newHistoryIndex = -1; // Go to current input buffer
            }
        }

        if (newHistoryIndex !== chatHistoryIndex || (event.key === 'ArrowDown' && chatHistoryIndex === chatInputHistory.length - 1) ) {
            event.preventDefault(); // Prevent cursor move only if history changes or trying to go past buffer
            chatHistoryIndex = newHistoryIndex;
            chatTextareaElement.value = (chatHistoryIndex === -1) ? currentInputBuffer : chatInputHistory[chatHistoryIndex];
            chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length;
            adjustTextareaHeight();
        }
    } else {
        // Any other key press resets history navigation state for next up/down
        chatHistoryIndex = -1;
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
    // If user types, they are no longer navigating history with currentInputBuffer
    if (chatHistoryIndex !== -1) {
        currentInputBuffer = chatTextareaElement.value; // Update buffer as they might have edited a history item
        chatHistoryIndex = -1; // Exit history navigation mode
    }
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
    // chatHistoryIndex = -1; // Resetting here might be too aggressive if user sends then immediately tries to nav
    // currentInputBuffer = ""; // Also potentially too aggressive
}

function formatMessageContentInternal(text) {
    if (typeof text !== 'string') {
        text = String(text);
    }
    let formattedText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = code; // Already HTML escaped
        const langClass = lang ? ` class="language-${lang}"` : '';
        return `<pre><code${langClass}>${escapedCode}</code></pre>`;
    });

    formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    formattedText = formattedText.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        const safeLinkUrl = linkUrl.replace(/"/g, "&quot;");
        // Avoid re-hyperlinking already escaped links from markdown
        if (linkText.includes('&lt;') || linkText.includes('&gt;')) return match;
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
    });

    // Bold and Italic handling - ensure it doesn't mess with code or pre blocks
    const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
    for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith('<pre') && !parts[i].startsWith('<a') && !parts[i].startsWith('<code')) {
            parts[i] = parts[i].replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
            parts[i] = parts[i].replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
            parts[i] = parts[i].replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');
            parts[i] = parts[i].replace(/\n/g, '<br>');
        }
    }
    formattedText = parts.join('');

    return formattedText;
}

function getComponentClass(componentHint) {
    const hint = String(componentHint).toUpperCase();
    if (componentBorderColorMap[hint]) {
        return componentBorderColorMap[hint];
    }
    // Handle tool-specific hints like TOOL_TAVILY_SEARCH_API_START
    if (hint.startsWith("TOOL_")) {
        return componentBorderColorMap.TOOL; // Fallback to generic tool color
    }
    return componentBorderColorMap.SYSTEM; // Default for unknown hints
}

function addChatMessageToUI(messageData, type, doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot add message:", messageData);
        return null;
    }

    const messageElement = document.createElement('div');
    let content, componentHint, stepInfo;

    if (typeof messageData === 'string') {
        content = messageData;
    } else if (typeof messageData === 'object' && messageData !== null) {
        content = messageData.content || messageData.text || (messageData.message ? messageData.message : JSON.stringify(messageData)); // Ensure some content
        componentHint = messageData.component_hint;
        stepInfo = messageData.step_info; // e.g., { current: 1, total: 3, description: "..." } for step announcements
        if (type === 'agent_major_step_announcement' && messageData.description) {
            content = `**Step ${messageData.step_number}/${messageData.total_steps}: ${messageData.description}**`;
        }
    } else {
        content = String(messageData); // Fallback
    }
    
    messageElement.classList.add('message');

    if (type === 'user') {
        messageElement.classList.add('message-user');
        // User messages get a bubble by default from CSS
    } else if (type === 'agent_message') { // This is now for the FINAL agent message
        messageElement.classList.add('message-agent-final', getComponentClass(componentHint || 'DEFAULT'));
    } else if (type === 'agent_major_step_announcement') {
        messageElement.classList.add('message-agent-step', getComponentClass(componentHint || 'SYSTEM'));
        currentMajorStepDiv = messageElement; // Track this for sub-statuses
        const subStatusContainer = document.createElement('div');
        subStatusContainer.className = 'sub-status-container';
        messageElement.appendChild(subStatusContainer); // Add it now, showAgentThinkingStatusInUI will populate
    } else if (type === 'status_message') {
        messageElement.classList.add('message-status', getComponentClass(componentHint || 'SYSTEM'));
        const lowerText = String(content).toLowerCase();
        if (lowerText.includes("connect") || lowerText.includes("clos")) {
            messageElement.classList.add('connection-status');
        }
        if (lowerText.includes("error")) {
            messageElement.classList.add('error-message', componentBorderColorMap.ERROR);
        }
    } else if (type === 'confirmed_plan_log' && content) {
        messageElement.classList.remove('message-agent-final'); // Ensure it's not bubbled by default
        messageElement.classList.add('message-system', 'plan-confirmation-container', 'plan-confirmed-static', getComponentClass('PLANNER'));
        try {
            const planData = JSON.parse(content);
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
            console.error("[ChatUI] Error parsing confirmed_plan_log data:", e, "Raw Data:", content);
            messageElement.innerHTML = formatMessageContentInternal(`Error displaying confirmed plan from history.`);
        }
    } else { // Generic agent intermediate messages if not caught above
         messageElement.classList.add('message-agent-intermediate', getComponentClass(componentHint || 'SYSTEM'));
    }

    // Common content handling
    if (type !== 'propose_plan_for_confirmation' && type !== 'confirmed_plan_log') {
         // The actual text content for non-plan messages
        const textContentDiv = document.createElement('div');
        textContentDiv.className = 'message-content-text'; // For main text styling
        textContentDiv.innerHTML = formatMessageContentInternal(content);
        
        // If it's a major step, this textContentDiv is the primary part. Sub-statuses go into its child.
        if (type === 'agent_major_step_announcement') {
            // Insert title content before the sub-status container
            const subStatusContainer = messageElement.querySelector('.sub-status-container');
            if (subStatusContainer) {
                messageElement.insertBefore(textContentDiv, subStatusContainer);
            } else { // Should not happen if subStatusContainer is always added
                messageElement.appendChild(textContentDiv);
            }
        } else {
            messageElement.appendChild(textContentDiv);
        }
    } else if (type === 'propose_plan_for_confirmation' && messageData) {
        // displayPlanConfirmationUI now takes messageData directly
        displayPlanConfirmationUI(messageData.human_summary, messageData.plan_id, messageData.structured_plan, 
            messageData.onConfirm, messageData.onCancel, messageData.onViewDetails);
        return; // displayPlanConfirmationUI appends its own element
    }


    // Append logic
    const thinkingStatusWasLast = agentThinkingStatusElement.parentNode === chatMessagesContainerElement &&
                                 chatMessagesContainerElement.lastChild === agentThinkingStatusElement;
    if (thinkingStatusWasLast) {
        chatMessagesContainerElement.insertBefore(messageElement, agentThinkingStatusElement);
    } else {
        chatMessagesContainerElement.appendChild(messageElement);
    }

    if (doScroll) {
        scrollToBottomChat();
    }
    return messageElement;
}

function displayPlanConfirmationUI(humanSummary, planId, structuredPlan, onConfirm, onCancel, onViewDetails) {
    if (!chatMessagesContainerElement) return;

    const existingPlanUIs = chatMessagesContainerElement.querySelectorAll('.plan-confirmation-container');
    existingPlanUIs.forEach(ui => ui.remove());

    const planContainer = document.createElement('div');
    planContainer.className = 'message message-system plan-confirmation-container';
    planContainer.classList.add(getComponentClass('PLANNER')); // Planner color for proposal
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
        ol.innerHTML = "<li>Plan details not available.</li>";
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
    confirmBtn.onclick = (e) => { e.stopPropagation(); if (typeof onConfirm === 'function') onConfirm(planId); };
    actionsDiv.appendChild(confirmBtn);
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'plan-cancel-btn';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = (e) => { e.stopPropagation(); if (typeof onCancel === 'function') onCancel(planId); };
    actionsDiv.appendChild(cancelBtn);
    planContainer.appendChild(actionsDiv);

    chatMessagesContainerElement.appendChild(planContainer);
    scrollToBottomChat();
}

function transformToConfirmedPlanUI(planId) {
    if (!chatMessagesContainerElement) return;
    const planContainer = chatMessagesContainerElement.querySelector(`.plan-confirmation-container[data-plan-id="${planId}"]`);
    if (!planContainer) {
        addChatMessageToUI(`Plan (ID: ${planId.substring(0,8)}...) confirmed.`, 'status_message', { component_hint: 'SYSTEM' });
        return;
    }
    planContainer.classList.add('plan-confirmed-static');
    const titleElement = planContainer.querySelector('h4');
    if (titleElement) titleElement.textContent = 'Plan Confirmed:';
    
    const viewDetailsBtn = planContainer.querySelector('.plan-toggle-details-btn');
    if (viewDetailsBtn) viewDetailsBtn.remove();
    
    const actionsDiv = planContainer.querySelector('.plan-actions');
    if (actionsDiv) actionsDiv.remove();

    const detailsDiv = planContainer.querySelector('.plan-steps-details');
    if (detailsDiv) detailsDiv.style.display = 'block'; // Ensure details are visible

    let statusP = planContainer.querySelector('.plan-execution-status-confirmed');
    if (!statusP) {
        statusP = document.createElement('p');
        statusP.className = 'plan-execution-status-confirmed';
        statusP.style.fontSize = '0.9em';
        statusP.style.marginTop = '10px';
        statusP.style.color = 'var(--accent-color)';
        statusP.style.fontWeight = '500';
        planContainer.appendChild(statusP); // Append at the end
    }
    statusP.textContent = `Status: Confirmed & Execution Started (at ${new Date().toLocaleTimeString()})`;
    scrollToBottomChat();
}


function showAgentThinkingStatusInUI(show, statusUpdateObject = { message: "Thinking...", status_key: "DEFAULT_THINKING", component_hint: "SYSTEM" }) {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;

    let displayMessage = "Thinking...";
    let componentHint = "SYSTEM";

    if (typeof statusUpdateObject === 'string') { // Legacy or simple message
        displayMessage = statusUpdateObject;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
        componentHint = statusUpdateObject.component_hint || componentHint;
    }
    
    const isIdleOrFinal = ["IDLE", "CANCELLED", "PLAN_FAILED", "DIRECT_QA_COMPLETED", "DIRECT_QA_FAILED", "UNKNOWN_INTENT"].includes(statusUpdateObject?.status_key);

    if (show && !isIdleOrFinal && currentMajorStepDiv) {
        // Append as sub-status to the current major step
        const subStatusContainer = currentMajorStepDiv.querySelector('.sub-status-container');
        if (subStatusContainer) {
            const subStatusDiv = document.createElement('div');
            subStatusDiv.className = `message-agent-substatus ${getComponentClass(componentHint)}`;
            
            const italicEl = document.createElement('i');
            italicEl.textContent = displayMessage;
            subStatusDiv.appendChild(italicEl);

            // Clear previous sub-statuses in this container before adding new one, or append?
            // For now, let's append to show a trail under the current step.
            subStatusContainer.appendChild(subStatusDiv);
            agentThinkingStatusElement.style.display = 'none'; // Hide global one if sub-status is shown
            scrollToBottomChat();
            return; 
        }
    }
    
    // Fallback to global status line if not showing sub-status or if it's an idle/final state
    if (show) {
        agentThinkingStatusElement.textContent = displayMessage;
        agentThinkingStatusElement.className = `message message-status agent-thinking-status ${getComponentClass(componentHint)}`; // Apply color class
        agentThinkingStatusElement.style.display = 'block';
        // Ensure it's at the bottom
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
    } else {
        agentThinkingStatusElement.style.display = 'none';
    }
    if (isIdleOrFinal) { // Ensure global status is updated for idle/final
        agentThinkingStatusElement.textContent = displayMessage;
        agentThinkingStatusElement.className = `message message-status agent-thinking-status ${getComponentClass(componentHint)}`;
        agentThinkingStatusElement.style.display = 'block';
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
        currentMajorStepDiv = null; // Reset active major step when agent goes idle/final
    }
    scrollToBottomChat();
}


function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        const thinkingStatus = agentThinkingStatusElement; // Keep a reference
        chatMessagesContainerElement.innerHTML = '';
        if (thinkingStatus) { // Re-append if it was there
            chatMessagesContainerElement.appendChild(thinkingStatus);
            thinkingStatus.style.display = 'none';
        }
        currentMajorStepDiv = null; // Reset active major step
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
    }
}
