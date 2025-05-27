// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status, step announcements, sub-statuses, thoughts).
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

// For storing the currently active major step element to append sub-statuses and thoughts
let currentMajorStepDiv = null;

// Map component hints from backend to CSS class modifiers for borders
const componentBorderColorMap = {
    DEFAULT: 'agent-line-default', // Should map to a defined CSS var or class
    USER: 'user-message-line-color', // Special case for user right-hand line
    SYSTEM: 'agent-line-system',
    INTENT_CLASSIFIER: 'agent-line-intent-classifier',
    PLANNER: 'agent-line-planner',
    CONTROLLER: 'agent-line-controller',
    EXECUTOR: 'agent-line-executor',
    EVALUATOR_STEP: 'agent-line-evaluator-step',
    EVALUATOR_OVERALL: 'agent-line-evaluator-overall',
    TOOL: 'agent-line-tool',
    LLM_CORE: 'agent-line-llm-core',
    WARNING: 'agent-line-warning',
    ERROR: 'agent-line-error'
};

function initChatUI(elements, callbacks) {
    console.log("[ChatUI] Initializing...");
    chatMessagesContainerElement = elements.chatMessagesContainer;
    agentThinkingStatusElement = elements.agentThinkingStatusEl; // This is the #agent-thinking-status div
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
        chatHistoryIndex = -1; // Reset on other key presses
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
    if (chatHistoryIndex !== -1) { // If user types while history item is shown, detach from history
        currentInputBuffer = chatTextareaElement.value;
        chatHistoryIndex = -1;
    }
}

function adjustTextareaHeight() {
    if (!chatTextareaElement) return;
    chatTextareaElement.style.height = 'auto'; // Temporarily shrink to get correct scrollHeight
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

function formatMessageContentInternal(text, isThoughtContentBox = false) {
    if (typeof text !== 'string') {
        text = String(text);
    }
    // 1. Escape HTML special characters first to prevent XSS or misinterpretation
    let formattedText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    // 2. Process Markdown for code blocks (```lang\ncode\n```)
    // Ensure it captures multi-line code correctly and handles optional language
    formattedText = formattedText.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = code; // Already HTML escaped
        const langClass = lang ? ` class="language-${lang}"` : '';
        return `<pre><code${langClass}>${escapedCode}</code></pre>`;
    });
    
    // 3. Process Markdown for inline code (`code`)
    formattedText = formattedText.replace(/`([^`]+?)`/g, '<code>$1</code>');

    // 4. Process Markdown for links ([text](url))
    // Ensure this doesn't interfere with already processed HTML, e.g. in <pre>
    // This regex is a bit safer by looking for non-angle bracket content in link text.
    formattedText = formattedText.replace(/\[([^<>[\]]+?)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        const safeLinkUrl = linkUrl.replace(/"/g, "&quot;"); // Sanitize URL further if needed
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
    });
    
    // 5. Process bold/italic, ensuring they don't break inside HTML tags
    // This is complex with regex. A more robust solution might involve a proper Markdown library
    // or a more sophisticated splitting strategy. For now, a simplified approach:
    const parts = formattedText.split(/(<pre>.*?<\/pre>|<a.*?<\/a>|<code>.*?<\/code>)/s);
    for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith('<pre') && !parts[i].startsWith('<a') && !parts[i].startsWith('<code')) {
            // Bold and Italic (***text*** or ___text___)
            parts[i] = parts[i].replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '<strong><em>$2</em></strong>');
            // Bold (**text** or __text__)
            parts[i] = parts[i].replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '<strong>$2</strong>');
            // Italic (*text* or _text_) - more careful regex to avoid unintended matches
            parts[i] = parts[i].replace(/(?<![`\w])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`\w])/g, '<em>$2</em>');
        }
    }
    formattedText = parts.join('');

    // 6. Convert newlines to <br> ONLY IF not inside a <pre> tag (pre handles newlines itself)
    // and not for thought content box which uses white-space: pre-wrap
    if (!isThoughtContentBox) {
        const preParts = formattedText.split(/(<pre>.*?<\/pre>)/s);
        for (let i = 0; i < preParts.length; i++) {
            if (!preParts[i].startsWith('<pre')) {
                preParts[i] = preParts[i].replace(/\n/g, '<br>');
            }
        }
        formattedText = preParts.join('');
    }

    return formattedText;
}


function getComponentClass(componentHint) {
    const hint = String(componentHint).toUpperCase();
    if (componentBorderColorMap[hint]) {
        return componentBorderColorMap[hint];
    }
    // Dynamic handling for TOOL_ F_X_Y -> agent-line-tool-x-y
    if (hint.startsWith("TOOL_")) {
        const toolSpecificClass = `agent-line-${hint.toLowerCase().replace(/_/g, '-')}`;
        // Here, you might check if a CSS rule for toolSpecificClass actually exists.
        // For now, we'll default to the generic tool class if a very specific one isn't predefined.
        return componentBorderColorMap.TOOL; // Fallback to generic tool line color
    }
    return componentBorderColorMap.SYSTEM; // Default for unknown hints
}

/**
 * Displays a major step announcement in the chat.
 * @param {object} data - Object containing { step_number, total_steps, description, component_hint }
 */
function displayMajorStepAnnouncementUI(data) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot display major step.");
        return;
    }
    
    const { step_number, total_steps, description } = data; // component_hint not used for major step line itself
    
    const stepWrapperDiv = document.createElement('div');
    stepWrapperDiv.className = 'message message-agent-step'; // No side-line class here
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'step-title';
    titleDiv.innerHTML = formatMessageContentInternal(`<strong>Step ${step_number}/${total_steps}: ${description}</strong>`);
    stepWrapperDiv.appendChild(titleDiv);
    
    const subContentContainer = document.createElement('div');
    subContentContainer.className = 'sub-content-container';
    stepWrapperDiv.appendChild(subContentContainer);
    
    currentMajorStepDiv = stepWrapperDiv; // Set this as the current step for sub-statuses/thoughts

    appendMessageElement(stepWrapperDiv);
    scrollToBottomChat();
    console.log(`[ChatUI] Displayed Major Step Announcement: Step ${step_number}/${total_steps}`);
}

function addChatMessageToUI(messageData, type, options = {}, doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot add message:", messageData);
        return null;
    }

    let baseMessageDiv; // This will be the div that gets appended
    let contentDiv;     // This is where the actual text/HTML content goes

    // Extract content and componentHint consistently
    let textContent, componentHint;
    if (typeof messageData === 'string') {
        textContent = messageData;
        componentHint = options.component_hint;
    } else if (typeof messageData === 'object' && messageData !== null) {
        textContent = messageData.content || messageData.text || (messageData.message ? messageData.message : JSON.stringify(messageData));
        componentHint = messageData.component_hint || options.component_hint;
    } else {
        textContent = String(messageData);
        componentHint = options.component_hint;
    }
    const effectiveComponentHint = componentHint || 'SYSTEM';


    if (type === 'user') {
        baseMessageDiv = document.createElement('div');
        baseMessageDiv.className = 'message message-user-wrapper'; // Wrapper for flex alignment
        contentDiv = document.createElement('div');
        contentDiv.className = 'message-user'; // Actual bubble with right border
        contentDiv.innerHTML = formatMessageContentInternal(textContent);
        baseMessageDiv.appendChild(contentDiv);
    } else if (type === 'propose_plan_for_confirmation') {
        // displayPlanConfirmationUI will create and return the full wrapper
        baseMessageDiv = displayPlanConfirmationUI(
            messageData.human_summary, 
            messageData.plan_id, 
            messageData.structured_plan,
            messageData.onConfirm, 
            messageData.onCancel,
            messageData.onViewDetails
        ); // displayPlanConfirmationUI now handles its own appending internally
        if (!baseMessageDiv) return; // In case displayPlanConfirmationUI fails or doesn't return element
    } else {
        // For system_status, agent_message (final), confirmed_plan_log
        baseMessageDiv = document.createElement('div');
        baseMessageDiv.className = 'message message-outer-blue-line'; // Wrapper with unified blue line

        contentDiv = document.createElement('div'); // Inner div for specific styling
        baseMessageDiv.appendChild(contentDiv);

        if (type === 'status_message') {
            contentDiv.className = 'message-system-status-content';
            contentDiv.innerHTML = formatMessageContentInternal(textContent);
            if (options.isError || String(textContent).toLowerCase().includes("error")) {
                contentDiv.classList.add('error-text'); // Apply error text color
            }
        } else if (type === 'agent_message') { // Final agent output
            contentDiv.className = 'message-agent-final-content'; // Bubble style
            contentDiv.innerHTML = formatMessageContentInternal(textContent);
            currentMajorStepDiv = null; // Final message, reset current step context
        } else if (type === 'confirmed_plan_log' && textContent) {
            contentDiv.className = 'message-plan-proposal-content'; // Similar to proposal
            // Parse and render the confirmed plan log (similar to displayPlanConfirmationUI but static)
            try {
                const planData = JSON.parse(textContent); // textContent is the JSON string here
                const planBlock = document.createElement('div');
                planBlock.className = 'plan-proposal-block plan-confirmed-static'; // Add static class
                
                const titleElement = document.createElement('h4');
                titleElement.textContent = planData.title || 'Confirmed Plan (from history):';
                planBlock.appendChild(titleElement);

                const summaryElement = document.createElement('p');
                summaryElement.className = 'plan-summary';
                summaryElement.innerHTML = formatMessageContentInternal(planData.summary || "Summary not available.");
                planBlock.appendChild(summaryElement);

                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'plan-steps-details';
                detailsDiv.style.display = 'block'; // Always show details for confirmed log
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
                planBlock.appendChild(detailsDiv);
                contentDiv.appendChild(planBlock);

                if (planData.timestamp) {
                    const timestampP = document.createElement('p');
                    timestampP.style.fontSize = '0.8em';
                    timestampP.style.color = 'var(--text-color-muted)';
                    timestampP.style.marginTop = '10px';
                    timestampP.textContent = `Originally Confirmed: ${new Date(planData.timestamp).toLocaleString()}`;
                    planBlock.appendChild(timestampP);
                }
            } catch (e) {
                console.error("[ChatUI] Error parsing confirmed_plan_log data from history:", e, "Raw Data:", textContent);
                contentDiv.innerHTML = formatMessageContentInternal(`Error displaying confirmed plan from history.`);
            }
        } else { // Fallback for any other type that might be routed here erroneously
            contentDiv.className = 'message-content-text'; // Generic content
            contentDiv.innerHTML = formatMessageContentInternal(textContent);
            baseMessageDiv.classList.add(getComponentClass(effectiveComponentHint)); // Add component line if not blue
        }
    }
    
    if (baseMessageDiv) { // Ensure baseMessageDiv was created (e.g. not handled by displayPlanConfirmationUI directly)
        appendMessageElement(baseMessageDiv);
    }

    if (doScroll) {
        scrollToBottomChat();
    }
    return baseMessageDiv; // Return the top-level appended element
}


function displayPlanConfirmationUI(humanSummary, planId, structuredPlan, onConfirm, onCancel, onViewDetails) {
    if (!chatMessagesContainerElement) return null;

    // Remove any existing plan proposals to avoid duplicates
    chatMessagesContainerElement.querySelectorAll('.plan-confirmation-wrapper').forEach(ui => ui.remove());

    const planWrapper = document.createElement('div');
    planWrapper.className = 'message message-outer-blue-line plan-confirmation-wrapper'; // Wrapper for blue line
    planWrapper.dataset.planId = planId; // Store planId on the wrapper

    const planContentDiv = document.createElement('div');
    planContentDiv.className = 'message-plan-proposal-content'; // Inner content div
    
    const planBlock = document.createElement('div'); // The actual dark block for plan
    planBlock.className = 'plan-proposal-block';

    const titleElement = document.createElement('h4');
    titleElement.textContent = 'Agent Proposed Plan:';
    planBlock.appendChild(titleElement);

    const summaryElement = document.createElement('p');
    summaryElement.className = 'plan-summary';
    summaryElement.innerHTML = formatMessageContentInternal(humanSummary);
    planBlock.appendChild(summaryElement);

    const detailsDiv = document.createElement('div');
    detailsDiv.className = 'plan-steps-details';
    detailsDiv.style.display = 'none'; // Initially hidden

    const ol = document.createElement('ol');
    if (structuredPlan && Array.isArray(structuredPlan)) {
        structuredPlan.forEach(step => {
            const li = document.createElement('li');
            const stepDescription = `<strong>${step.step_id}. ${formatMessageContentInternal(step.description)}</strong>`;
            const toolUsed = (step.tool_to_use && step.tool_to_use !== "None") ? `<br><span class="step-tool">Tool: ${formatMessageContentInternal(step.tool_to_use)}</span>` : '';
            const inputHint = step.tool_input_instructions ? `<br><span class="step-tool">Input Hint: ${formatMessageContentInternal(step.tool_input_instructions)}</span>` : '';
            const expectedOutcome = `<br><span class="step-expected">Expected: ${formatMessageContentInternal(step.expected_outcome)}</span>`;
            li.innerHTML = stepDescription + toolUsed + inputHint + expectedOutcome;
            ol.appendChild(li);
        });
    } else {
        ol.innerHTML = "<li>Plan details not available.</li>";
    }
    detailsDiv.appendChild(ol);
    planBlock.appendChild(detailsDiv);

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
    planBlock.appendChild(viewDetailsBtn);

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
    planBlock.appendChild(actionsDiv);
    
    planContentDiv.appendChild(planBlock);
    planWrapper.appendChild(planContentDiv);

    appendMessageElement(planWrapper); // Append the fully constructed plan UI
    scrollToBottomChat();
    return planWrapper; // Return the main wrapper element
}


function transformToConfirmedPlanUI(planId) {
    if (!chatMessagesContainerElement) return;
    const planWrapper = chatMessagesContainerElement.querySelector(`.plan-confirmation-wrapper[data-plan-id="${planId}"]`);
    if (!planWrapper) {
        // If the original proposal UI isn't found (e.g., after refresh), add a simple status message
        addChatMessageToUI(`Plan (ID: ${planId.substring(0,8)}...) confirmed. Executing steps...`, 'status_message', {component_hint: 'SYSTEM'});
        return;
    }
    // The planWrapper already has .message-outer-blue-line
    
    const planBlock = planWrapper.querySelector('.plan-proposal-block');
    if (!planBlock) return;

    planBlock.classList.add('plan-confirmed-static');

    const titleElement = planBlock.querySelector('h4');
    if (titleElement) titleElement.textContent = 'Plan Confirmed:';
    
    const viewDetailsBtn = planBlock.querySelector('.plan-toggle-details-btn');
    if (viewDetailsBtn) viewDetailsBtn.remove();
    
    const actionsDiv = planBlock.querySelector('.plan-actions');
    if (actionsDiv) actionsDiv.remove();

    const detailsDiv = planBlock.querySelector('.plan-steps-details');
    if (detailsDiv) detailsDiv.style.display = 'block'; // Ensure details are visible

    let statusP = planBlock.querySelector('.plan-execution-status-confirmed');
    if (!statusP) {
        statusP = document.createElement('p');
        statusP.className = 'plan-execution-status-confirmed';
        planBlock.appendChild(statusP); // Append to the dark block
    }
    statusP.textContent = `Status: Confirmed & Execution Started (at ${new Date().toLocaleTimeString()})`;
    scrollToBottomChat();
}

function showAgentThinkingStatusInUI(show, statusUpdateObject = { message: "Thinking...", status_key: "DEFAULT_THINKING", component_hint: "SYSTEM", sub_type: null }) {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;

    let displayMessage = "Thinking...";
    let componentHint = statusUpdateObject?.component_hint || "SYSTEM";
    let statusKey = statusUpdateObject?.status_key || "UNKNOWN_STATUS";
    let subType = statusUpdateObject?.sub_type; // 'sub_status' or 'thought'

    if (typeof statusUpdateObject === 'string') { // Legacy or simple message
        displayMessage = statusUpdateObject;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'object' && subType === 'thought') {
        // For thoughts, message is { label, content_markdown }
        // displayMessage will be handled by the thought rendering logic
    } else if (statusUpdateObject && statusUpdateObject.message) {
         displayMessage = String(statusUpdateObject.message); // Fallback
    }


    const isFinalStateForBottomLine = ["IDLE", "CANCELLED", "ERROR", "PLAN_FAILED", "DIRECT_QA_COMPLETED", "DIRECT_QA_FAILED", "UNKNOWN_INTENT", "AWAITING_PLAN_CONFIRMATION"].includes(statusKey);

    if (show && currentMajorStepDiv && (subType === 'sub_status' || subType === 'thought')) {
        const subContentContainer = currentMajorStepDiv.querySelector('.sub-content-container');
        if (subContentContainer) {
            let nestedMessageDiv;
            if (subType === 'sub_status') {
                nestedMessageDiv = document.createElement('div');
                nestedMessageDiv.className = `message message-agent-substatus ${getComponentClass(componentHint)}`;
                const contentEl = document.createElement('div');
                contentEl.className = 'content';
                contentEl.innerHTML = formatMessageContentInternal(`<i>${displayMessage}</i>`);
                nestedMessageDiv.appendChild(contentEl);
            } else if (subType === 'thought' && statusUpdateObject.message && typeof statusUpdateObject.message === 'object') {
                nestedMessageDiv = document.createElement('div');
                nestedMessageDiv.className = `message message-agent-thought ${getComponentClass(componentHint)}`;
                
                const labelEl = document.createElement('div');
                labelEl.className = 'thought-label';
                labelEl.textContent = statusUpdateObject.message.label || `${componentHint} thought:`;
                nestedMessageDiv.appendChild(labelEl);

                const contentBoxEl = document.createElement('div');
                contentBoxEl.className = 'thought-content-box';
                contentBoxEl.innerHTML = formatMessageContentInternal(statusUpdateObject.message.content_markdown, true); // true for isThoughtContentBox
                nestedMessageDiv.appendChild(contentBoxEl);
            }

            if (nestedMessageDiv) {
                subContentContainer.appendChild(nestedMessageDiv);
                // Optionally hide or set global line to Idle if a sub-status/thought is more prominent
                agentThinkingStatusElement.style.display = 'none'; 
                scrollToBottomChat();
                return; // Handled as a nested message
            }
        }
    }
    
    // Fallback to global status line OR if it's a final state OR no currentMajorStepDiv
    if (show) {
        agentThinkingStatusElement.innerHTML = formatMessageContentInternal(displayMessage); // Use innerHTML for italic if displayMessage contains it
        agentThinkingStatusElement.className = `message agent-thinking-status ${getComponentClass(componentHint)}`;
        agentThinkingStatusElement.style.display = 'block';
        // Ensure it's the last child
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
    } else { 
        // If explicitly told to hide, or if a final state implies hiding the "Thinking..." part
        // and showing a final "Idle." or "Error."
        if (isFinalStateForBottomLine) {
            agentThinkingStatusElement.innerHTML = formatMessageContentInternal(displayMessage); // Show the final state message
            agentThinkingStatusElement.className = `message agent-thinking-status ${getComponentClass(componentHint)}`;
            agentThinkingStatusElement.style.display = 'block';
            if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
                chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
            }
        } else {
            agentThinkingStatusElement.style.display = 'none';
        }
    }

    if (isFinalStateForBottomLine) {
        currentMajorStepDiv = null; // Reset context for major steps
    }
    scrollToBottomChat();
}


function clearChatMessagesUI() {
    if (chatMessagesContainerElement) {
        const thinkingStatus = agentThinkingStatusElement; 
        chatMessagesContainerElement.innerHTML = ''; // Clear all
        if (thinkingStatus) { 
            chatMessagesContainerElement.appendChild(thinkingStatus); // Re-add the (now empty/hidden) status line
            thinkingStatus.style.display = 'none';
            thinkingStatus.textContent = ''; // Clear its content too
        }
        currentMajorStepDiv = null; // Reset current step context
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        // Timeout helps ensure DOM has updated, especially if images/complex content was added
        setTimeout(() => {
            chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
        }, 0);
    }
}

/**
 * Appends a message element to the chat container, ensuring the thinking status line remains last.
 * @param {HTMLElement} messageElement - The message element to append.
 */
function appendMessageElement(messageElement) {
    if (!chatMessagesContainerElement || !messageElement) return;

    const thinkingStatusIsPresent = agentThinkingStatusElement.parentNode === chatMessagesContainerElement;
    if (thinkingStatusIsPresent) {
        chatMessagesContainerElement.insertBefore(messageElement, agentThinkingStatusElement);
    } else {
        chatMessagesContainerElement.appendChild(messageElement);
    }
}
