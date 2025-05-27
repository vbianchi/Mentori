// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status, step announcements, sub-statuses).
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
    DEFAULT: 'agent-line-default',
    USER: 'user-line-accent', // Not used for lines, but for consistency
    SYSTEM: 'agent-line-system',
    INTENT_CLASSIFIER: 'agent-line-intent-classifier',
    PLANNER: 'agent-line-planner',
    CONTROLLER: 'agent-line-controller',
    EXECUTOR: 'agent-line-executor',
    EVALUATOR_STEP: 'agent-line-evaluator-step',
    EVALUATOR_OVERALL: 'agent-line-evaluator-overall',
    TOOL: 'agent-line-tool',
    // Specific tools can be dynamically generated if needed: e.g. TOOL_TAVILY_SEARCH_API -> agent-line-tool-tavily-search-api
    WARNING: 'agent-line-warning',
    ERROR: 'agent-line-error'
};

function initChatUI(elements, callbacks) {
    console.log("[ChatUI] Initializing...");
    chatMessagesContainerElement = elements.chatMessagesContainer;
    agentThinkingStatusElement = elements.agentThinkingStatusEl;
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
        currentInputBuffer = ""; 
        chatHistoryIndex = -1;    
    }
    chatTextareaElement.focus();
}

function handleChatTextareaKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendButtonClick();
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        if (chatInputHistory.length === 0 && chatTextareaElement.value.trim() === "") return;
        
        if (chatHistoryIndex === -1 && (chatTextareaElement.value.trim() !== "" || event.key === 'ArrowUp')) {
            if (chatInputHistory.length > 0 || event.key === 'ArrowUp') {
                 currentInputBuffer = chatTextareaElement.value;
            }
        }
        
        let newHistoryIndex = chatHistoryIndex;
        if (event.key === 'ArrowUp') {
            if (chatInputHistory.length > 0) {
                newHistoryIndex = (chatHistoryIndex === -1) ? chatInputHistory.length - 1 : Math.max(0, chatHistoryIndex - 1);
            } else { return; }
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                newHistoryIndex++;
            } else { 
                newHistoryIndex = -1;
            }
        }

        if (newHistoryIndex !== chatHistoryIndex || (event.key === 'ArrowDown' && chatHistoryIndex === chatInputHistory.length - 1) ) {
            event.preventDefault(); 
            chatHistoryIndex = newHistoryIndex;
            chatTextareaElement.value = (chatHistoryIndex === -1) ? currentInputBuffer : chatInputHistory[chatHistoryIndex];
            chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length;
            adjustTextareaHeight();
        }
    } else {
        chatHistoryIndex = -1;
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
    if (chatHistoryIndex !== -1) {
        currentInputBuffer = chatTextareaElement.value;
        chatHistoryIndex = -1;
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
    if (hint.startsWith("TOOL_")) { // e.g. TOOL_TAVILY_SEARCH_API
        const specificToolClass = `agent-line-${hint.toLowerCase().replace(/_/g, '-')}`;
        // Check if a specific CSS class exists for this tool, otherwise use generic tool class
        // This check would ideally be against actual CSS rules, but for now, assume generic if not in map
        return componentBorderColorMap.TOOL; 
    }
    return componentBorderColorMap.SYSTEM; // Default for unknown hints
}

// <<< --- START NEW FUNCTION --- >>>
/**
 * Displays a major step announcement in the chat.
 * @param {object} data - Object containing { step_number, total_steps, description, component_hint }
 */
function displayMajorStepAnnouncementUI(data) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot display major step.");
        return;
    }
    
    const { step_number, total_steps, description, component_hint } = data;
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', 'message-agent-step', getComponentClass(component_hint || 'SYSTEM'));
    
    const textContentDiv = document.createElement('div');
    textContentDiv.className = 'message-content-text';
    textContentDiv.innerHTML = formatMessageContentInternal(`<strong>Step ${step_number}/${total_steps}: ${description}</strong>`);
    messageElement.appendChild(textContentDiv);
    
    const subStatusContainer = document.createElement('div');
    subStatusContainer.className = 'sub-status-container';
    messageElement.appendChild(subStatusContainer);
    
    currentMajorStepDiv = messageElement; // Set this as the current step for sub-statuses

    // Append logic (handles existing thinking status line)
    const thinkingStatusWasLast = agentThinkingStatusElement.parentNode === chatMessagesContainerElement &&
                                 chatMessagesContainerElement.lastChild === agentThinkingStatusElement;
    if (thinkingStatusWasLast) {
        chatMessagesContainerElement.insertBefore(messageElement, agentThinkingStatusElement);
    } else {
        chatMessagesContainerElement.appendChild(messageElement);
    }
    scrollToBottomChat();
    console.log(`[ChatUI] Displayed Major Step Announcement: Step ${step_number}/${total_steps}`);
}
// <<< --- END NEW FUNCTION --- >>>


function addChatMessageToUI(messageData, type, options = {}, doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot add message:", messageData);
        return null;
    }

    // Handle direct call for plan proposal
    if (type === 'propose_plan_for_confirmation' && typeof messageData === 'object' && messageData !== null) {
        displayPlanConfirmationUI(
            messageData.human_summary, 
            messageData.plan_id, 
            messageData.structured_plan,
            messageData.onConfirm, // These are callback functions passed from script.js
            messageData.onCancel,
            messageData.onViewDetails
        );
        return; // displayPlanConfirmationUI handles its own appending
    }
    
    const messageElement = document.createElement('div');
    let content, componentHint;

    if (typeof messageData === 'string') {
        content = messageData;
        componentHint = options.component_hint;
    } else if (typeof messageData === 'object' && messageData !== null) {
        content = messageData.content || messageData.text || (messageData.message ? messageData.message : JSON.stringify(messageData));
        componentHint = messageData.component_hint || options.component_hint;
    } else {
        content = String(messageData);
        componentHint = options.component_hint;
    }
    
    messageElement.classList.add('message');
    const effectiveComponentHint = componentHint || 'SYSTEM'; // Default if no hint provided

    if (type === 'user') {
        messageElement.classList.add('message-user');
    } else if (type === 'agent_message') { // Final agent output
        messageElement.classList.add('message-agent-final', getComponentClass(effectiveComponentHint));
        currentMajorStepDiv = null; // A final message means the plan/sequence is over
    } else if (type === 'status_message') {
        messageElement.classList.add('message-status', getComponentClass(effectiveComponentHint));
        const lowerText = String(content).toLowerCase();
        if (lowerText.includes("connect") || lowerText.includes("clos")) messageElement.classList.add('connection-status');
        if (options.isError || lowerText.includes("error")) { // Check options.isError for explicit error styling
            messageElement.classList.add('error-message');
            // Ensure error line color if not already set by component hint
            if (!messageElement.classList.contains(componentBorderColorMap.ERROR)) {
                 messageElement.classList.add(componentBorderColorMap.ERROR);
            }
        }
    } else if (type === 'confirmed_plan_log' && content) {
        messageElement.classList.add('message-system', 'plan-confirmation-container', 'plan-confirmed-static', getComponentClass('PLANNER'));
        // ... (parsing and rendering logic for confirmed_plan_log remains the same) ...
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
                planData.steps.forEach(step => { /* ... step rendering ... */ 
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
            if (planData.timestamp) { /* ... timestamp rendering ... */
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
    } else { 
         messageElement.classList.add('message-agent-intermediate', getComponentClass(effectiveComponentHint));
    }

    if (type !== 'propose_plan_for_confirmation' && type !== 'confirmed_plan_log') {
        const textContentDiv = document.createElement('div');
        textContentDiv.className = 'message-content-text';
        textContentDiv.innerHTML = formatMessageContentInternal(content);
        messageElement.appendChild(textContentDiv);
    }
    
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
    // ... (This function remains largely the same as in v2, but ensure it's called correctly by addChatMessageToUI)
    // It should also use getComponentClass('PLANNER') for its main container.
    if (!chatMessagesContainerElement) return;

    const existingPlanUIs = chatMessagesContainerElement.querySelectorAll('.plan-confirmation-container');
    existingPlanUIs.forEach(ui => ui.remove());

    const planContainer = document.createElement('div');
    planContainer.className = 'message message-system plan-confirmation-container';
    planContainer.classList.add(getComponentClass('PLANNER')); 
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
    // ... (This function remains largely the same as in v2)
    if (!chatMessagesContainerElement) return;
    const planContainer = chatMessagesContainerElement.querySelector(`.plan-confirmation-container[data-plan-id="${planId}"]`);
    if (!planContainer) {
        addChatMessageToUI(`Plan (ID: ${planId.substring(0,8)}...) confirmed.`, 'status_message', {component_hint: 'SYSTEM'});
        return;
    }
    planContainer.classList.add('plan-confirmed-static');
    // Retain planner color for confirmed plan
    // planContainer.classList.remove(getComponentClass('PLANNER')); 
    // planContainer.classList.add(getComponentClass('SYSTEM'));


    const titleElement = planContainer.querySelector('h4');
    if (titleElement) titleElement.textContent = 'Plan Confirmed:';
    
    const viewDetailsBtn = planContainer.querySelector('.plan-toggle-details-btn');
    if (viewDetailsBtn) viewDetailsBtn.remove();
    
    const actionsDiv = planContainer.querySelector('.plan-actions');
    if (actionsDiv) actionsDiv.remove();

    const detailsDiv = planContainer.querySelector('.plan-steps-details');
    if (detailsDiv) detailsDiv.style.display = 'block';

    let statusP = planContainer.querySelector('.plan-execution-status-confirmed');
    if (!statusP) {
        statusP = document.createElement('p');
        statusP.className = 'plan-execution-status-confirmed';
        statusP.style.fontSize = '0.9em';
        statusP.style.marginTop = '10px';
        statusP.style.color = 'var(--accent-color)';
        statusP.style.fontWeight = '500';
        planContainer.appendChild(statusP);
    }
    statusP.textContent = `Status: Confirmed & Execution Started (at ${new Date().toLocaleTimeString()})`;
    scrollToBottomChat();
}

function showAgentThinkingStatusInUI(show, statusUpdateObject = { message: "Thinking...", status_key: "DEFAULT_THINKING", component_hint: "SYSTEM" }) {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;

    let displayMessage = "Thinking...";
    let componentHint = statusUpdateObject?.component_hint || "SYSTEM"; // Default to SYSTEM if no hint
    let statusKey = statusUpdateObject?.status_key || "UNKNOWN_STATUS";

    if (typeof statusUpdateObject === 'string') {
        displayMessage = statusUpdateObject;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
    }
    
    const isIdleOrFinal = ["IDLE", "CANCELLED", "PLAN_FAILED", "DIRECT_QA_COMPLETED", "DIRECT_QA_FAILED", "UNKNOWN_INTENT", "AWAITING_PLAN_CONFIRMATION"].includes(statusKey);

    if (show && !isIdleOrFinal && currentMajorStepDiv) {
        const subStatusContainer = currentMajorStepDiv.querySelector('.sub-status-container');
        if (subStatusContainer) {
            const subStatusDiv = document.createElement('div');
            // Add base class and component-specific class for border
            subStatusDiv.className = `message message-agent-substatus ${getComponentClass(componentHint)}`;
            
            const italicEl = document.createElement('i');
            italicEl.textContent = displayMessage;
            
            const contentDiv = document.createElement('div'); // Wrapper for text content
            contentDiv.className = 'message-content-text';
            contentDiv.appendChild(italicEl);
            subStatusDiv.appendChild(contentDiv);

            subStatusContainer.appendChild(subStatusDiv);
            agentThinkingStatusElement.style.display = 'none'; 
            scrollToBottomChat();
            return; 
        }
    }
    
    // Fallback to global status line
    if (show) {
        agentThinkingStatusElement.textContent = displayMessage;
        agentThinkingStatusElement.className = `message message-status agent-thinking-status ${getComponentClass(componentHint)}`;
        agentThinkingStatusElement.style.display = 'block';
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
    } else { // if show is false
        agentThinkingStatusElement.style.display = 'none';
    }

    if (isIdleOrFinal) { // Ensure global status is updated for idle/final and currentMajorStepDiv is reset
        agentThinkingStatusElement.textContent = displayMessage;
        agentThinkingStatusElement.className = `message message-status agent-thinking-status ${getComponentClass(componentHint)}`;
        agentThinkingStatusElement.style.display = 'block';
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
        currentMajorStepDiv = null; 
    }
    scrollToBottomChat();
}


function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        const thinkingStatus = agentThinkingStatusElement; 
        chatMessagesContainerElement.innerHTML = '';
        if (thinkingStatus) { 
            chatMessagesContainerElement.appendChild(thinkingStatus);
            thinkingStatus.style.display = 'none';
        }
        currentMajorStepDiv = null; 
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
    }
}
