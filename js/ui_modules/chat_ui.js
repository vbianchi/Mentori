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
    DEFAULT: 'agent-line-default', 
    USER: 'user-message-line-color', 
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

function formatMessageContentInternal(text, isThoughtContentBox = false) {
    if (typeof text !== 'string') {
        text = String(text);
    }

    // **REVISED STRATEGY for HTML Tag Rendering**
    // 1. First, convert specific Markdown patterns to HTML tags.
    //    This needs to be done carefully to avoid conflicts.

    // Code blocks (```lang\ncode\n```) - These should be handled first as they contain arbitrary text.
    // We temporarily replace them with placeholders, then reinsert them after other Markdown.
    const codeBlockPlaceholders = [];
    let tempText = text.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        // Escape HTML within the code block itself to be safe
        const escapedCode = code.replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;");
        const langClass = lang ? ` class="language-${lang}"` : '';
        const placeholder = `%%CODEBLOCK_${codeBlockPlaceholders.length}%%`;
        codeBlockPlaceholders.push(`<pre><code${langClass}>${escapedCode}</code></pre>`);
        return placeholder;
    });

    // Inline code (`code`) - also handle with placeholders
    const inlineCodePlaceholders = [];
    tempText = tempText.replace(/`([^`]+?)`/g, (match, code) => {
        const escapedCode = code.replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;");
        const placeholder = `%%INLINECODE_${inlineCodePlaceholders.length}%%`;
        inlineCodePlaceholders.push(`<code>${escapedCode}</code>`);
        return placeholder;
    });
    
    // Links ([text](url))
    tempText = tempText.replace(/\[([^<>[\]]+?)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        // Escape linkText and linkUrl parts that will become HTML content/attributes
        const safeLinkText = linkText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const safeLinkUrl = linkUrl.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${safeLinkText}</a>`;
    });

    // Bold and Italic (***text*** or ___text___)
    tempText = tempText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong><em>${content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</em></strong>`);
    // Bold (**text** or __text__)
    tempText = tempText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong>${content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</strong>`);
    // Italic (*text* or _text_)
    tempText = tempText.replace(/(?<![`*\w\\])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`*\w])/g, (match, wrapper, content) => `<em>${content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</em>`);

    // 2. Now, escape remaining HTML special characters in the text that wasn't part of our Markdown conversions.
    // This is tricky because our Markdown replacements have inserted HTML.
    // A simpler approach: the initial input `text` should be what we consider "user text".
    // Our markdown conversions create trusted HTML.
    // The issue is if the *original* text contained `<` or `&` that wasn't part of markdown.
    // The previous version's initial full escape was problematic.
    // Let's assume for now that the markdown conversions handle the necessary escaping for their content.
    // The main problem was HTML tags being displayed, which means they were being treated as text.
    // The current `tempText` now contains our generated HTML.

    // 3. Convert newlines to <br> ONLY IF not inside a <pre> tag (which is now a placeholder)
    // and not for thought content box which uses white-space: pre-wrap
    if (!isThoughtContentBox) {
        // Split by code block placeholders to avoid adding <br> inside them
        const partsForNewline = tempText.split(/(%%CODEBLOCK_\d+%%)/g);
        for (let i = 0; i < partsForNewline.length; i++) {
            if (!partsForNewline[i].startsWith('%%CODEBLOCK_')) {
                partsForNewline[i] = partsForNewline[i].replace(/\n/g, '<br>');
            }
        }
        tempText = partsForNewline.join('');
    }

    // 4. Reinsert code blocks and inline code
    tempText = tempText.replace(/%%CODEBLOCK_(\d+)%%/g, (match, index) => codeBlockPlaceholders[parseInt(index)]);
    tempText = tempText.replace(/%%INLINECODE_(\d+)%%/g, (match, index) => inlineCodePlaceholders[parseInt(index)]);
    
    return tempText;
}


function getComponentClass(componentHint) {
    const hint = String(componentHint).toUpperCase();
    if (componentBorderColorMap[hint]) {
        return componentBorderColorMap[hint];
    }
    if (hint.startsWith("TOOL_")) {
        return componentBorderColorMap.TOOL; 
    }
    return componentBorderColorMap.SYSTEM; 
}

function displayMajorStepAnnouncementUI(data) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot display major step.");
        return;
    }
    
    const { step_number, total_steps, description } = data; 
    
    const stepWrapperDiv = document.createElement('div');
    stepWrapperDiv.className = 'message message-agent-step'; 
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'step-title';
    titleDiv.innerHTML = formatMessageContentInternal(`<strong>Step ${step_number}/${total_steps}: ${description}</strong>`);
    stepWrapperDiv.appendChild(titleDiv);
    
    const subContentContainer = document.createElement('div');
    subContentContainer.className = 'sub-content-container';
    stepWrapperDiv.appendChild(subContentContainer);
    
    currentMajorStepDiv = stepWrapperDiv; 

    appendMessageElement(stepWrapperDiv);
    scrollToBottomChat();
    console.log(`[ChatUI] Displayed Major Step Announcement: Step ${step_number}/${total_steps}`);
}

function addChatMessageToUI(messageData, type, options = {}, doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot add message:", messageData);
        return null;
    }

    let baseMessageDiv; 
    let contentHolderDiv; 

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
        baseMessageDiv.className = 'message message-user-wrapper'; 
        contentHolderDiv = document.createElement('div');
        contentHolderDiv.className = 'message-user'; 
        baseMessageDiv.appendChild(contentHolderDiv);
    } else if (type === 'propose_plan_for_confirmation') {
        baseMessageDiv = displayPlanConfirmationUI(
            messageData.human_summary, 
            messageData.plan_id, 
            messageData.structured_plan,
            messageData.onConfirm, 
            messageData.onCancel,
            messageData.onViewDetails
        ); 
        if (!baseMessageDiv) return;
    } else {
        baseMessageDiv = document.createElement('div');
        baseMessageDiv.className = 'message message-outer-blue-line'; 

        contentHolderDiv = document.createElement('div'); 
        baseMessageDiv.appendChild(contentHolderDiv);

        if (type === 'status_message') {
            contentHolderDiv.className = 'message-system-status-content';
            if (options.isError || String(textContent).toLowerCase().includes("error")) {
                contentHolderDiv.classList.add('error-text'); 
            }
        } else if (type === 'agent_message') { 
            contentHolderDiv.className = 'message-agent-final-content'; 
            currentMajorStepDiv = null; 
        } else if (type === 'confirmed_plan_log' && textContent) {
            contentHolderDiv.className = 'message-plan-proposal-content'; 
            try {
                const planData = JSON.parse(textContent); 
                const planBlock = document.createElement('div');
                planBlock.className = 'plan-proposal-block plan-confirmed-static'; 
                
                const titleElement = document.createElement('h4');
                titleElement.innerHTML = formatMessageContentInternal(planData.title || 'Confirmed Plan (from history):');
                planBlock.appendChild(titleElement);

                const summaryElement = document.createElement('p');
                summaryElement.className = 'plan-summary';
                summaryElement.innerHTML = formatMessageContentInternal(planData.summary || "Summary not available.");
                planBlock.appendChild(summaryElement);

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
                planBlock.appendChild(detailsDiv);
                contentHolderDiv.appendChild(planBlock); 

                if (planData.timestamp) {
                    const timestampP = document.createElement('p');
                    timestampP.style.fontSize = '0.8em';
                    timestampP.style.color = 'var(--text-color-muted)';
                    timestampP.style.marginTop = '10px';
                    timestampP.textContent = `Originally Confirmed: ${new Date(planData.timestamp).toLocaleString()}`;
                    planBlock.appendChild(timestampP);
                }
                textContent = null; 
            } catch (e) {
                console.error("[ChatUI] Error parsing confirmed_plan_log data from history:", e, "Raw Data:", textContent);
                textContent = `Error displaying confirmed plan from history.`; 
                contentHolderDiv.innerHTML = formatMessageContentInternal(textContent);
            }
        } else { 
            contentHolderDiv.className = 'message-content-text'; 
            baseMessageDiv.classList.add(getComponentClass(effectiveComponentHint)); 
        }
    }
    
    if (contentHolderDiv && textContent !== null) { 
        contentHolderDiv.innerHTML = formatMessageContentInternal(textContent);
    }
    
    if (baseMessageDiv) { 
        appendMessageElement(baseMessageDiv);
    }

    if (doScroll) {
        scrollToBottomChat();
    }
    return baseMessageDiv; 
}


function displayPlanConfirmationUI(humanSummary, planId, structuredPlan, onConfirm, onCancel, onViewDetails) {
    if (!chatMessagesContainerElement) return null;

    chatMessagesContainerElement.querySelectorAll('.plan-confirmation-wrapper').forEach(ui => ui.remove());

    const planWrapper = document.createElement('div');
    planWrapper.className = 'message message-outer-blue-line plan-confirmation-wrapper'; 
    planWrapper.dataset.planId = planId; 

    const planContentDiv = document.createElement('div');
    planContentDiv.className = 'message-plan-proposal-content'; 
    
    const planBlock = document.createElement('div'); 
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
    detailsDiv.style.display = 'none'; 

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

    appendMessageElement(planWrapper); 
    scrollToBottomChat();
    return planWrapper; 
}


function transformToConfirmedPlanUI(planId) {
    if (!chatMessagesContainerElement) return;
    const planWrapper = chatMessagesContainerElement.querySelector(`.plan-confirmation-wrapper[data-plan-id="${planId}"]`);
    if (!planWrapper) {
        addChatMessageToUI(`Plan (ID: ${planId.substring(0,8)}...) confirmed. Executing steps...`, 'status_message', {component_hint: 'SYSTEM'});
        return;
    }
    
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
    if (detailsDiv) detailsDiv.style.display = 'block'; 

    let statusP = planBlock.querySelector('.plan-execution-status-confirmed');
    if (!statusP) {
        statusP = document.createElement('p');
        statusP.className = 'plan-execution-status-confirmed';
        planBlock.appendChild(statusP); 
    }
    statusP.textContent = `Status: Confirmed & Execution Started (at ${new Date().toLocaleTimeString()})`; 
    scrollToBottomChat();
}

function showAgentThinkingStatusInUI(show, statusUpdateObject = { message: "Thinking...", status_key: "DEFAULT_THINKING", component_hint: "SYSTEM", sub_type: null }) {
    if (!agentThinkingStatusElement || !chatMessagesContainerElement) return;

    let displayMessage = "Thinking...";
    let componentHint = statusUpdateObject?.component_hint || "SYSTEM";
    let statusKey = statusUpdateObject?.status_key || "UNKNOWN_STATUS";
    let subType = statusUpdateObject?.sub_type; 

    if (typeof statusUpdateObject === 'string') { 
        displayMessage = statusUpdateObject;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'object' && subType === 'thought') {
        // Content for thought is in statusUpdateObject.message.content_markdown
    } else if (statusUpdateObject && statusUpdateObject.message) {
         displayMessage = String(statusUpdateObject.message); 
    }

    const isFinalStateForBottomLine = ["IDLE", "CANCELLED", "ERROR", "PLAN_FAILED", "DIRECT_QA_COMPLETED", "DIRECT_QA_FAILED", "UNKNOWN_INTENT", "AWAITING_PLAN_CONFIRMATION", "PLAN_STOPPED", "PLAN_COMPLETED_ISSUES"].includes(statusKey);

    if (show && currentMajorStepDiv && (subType === 'sub_status' || subType === 'thought')) {
        const subContentContainer = currentMajorStepDiv.querySelector('.sub-content-container');
        if (subContentContainer) {
            let nestedMessageDiv;
            if (subType === 'sub_status') {
                nestedMessageDiv = document.createElement('div');
                nestedMessageDiv.className = `message message-agent-substatus ${getComponentClass(componentHint)}`;
                const contentEl = document.createElement('div');
                contentEl.className = 'content';
                contentEl.innerHTML = formatMessageContentInternal(`<em>${displayMessage}</em>`);
                nestedMessageDiv.appendChild(contentEl);
            } else if (subType === 'thought' && statusUpdateObject.message && typeof statusUpdateObject.message === 'object') {
                nestedMessageDiv = document.createElement('div');
                nestedMessageDiv.className = `message message-agent-thought ${getComponentClass(componentHint)}`;
                
                const labelEl = document.createElement('div');
                labelEl.className = 'thought-label';
                labelEl.innerHTML = formatMessageContentInternal(statusUpdateObject.message.label || `${componentHint} thought:`);
                nestedMessageDiv.appendChild(labelEl);

                const contentBoxEl = document.createElement('div');
                contentBoxEl.className = 'thought-content-box';
                contentBoxEl.innerHTML = formatMessageContentInternal(statusUpdateObject.message.content_markdown, true); 
                nestedMessageDiv.appendChild(contentBoxEl);
            }

            if (nestedMessageDiv) {
                subContentContainer.appendChild(nestedMessageDiv);
                agentThinkingStatusElement.style.display = 'none'; 
                scrollToBottomChat();
                return; 
            }
        }
    }
    
    if (show) {
        agentThinkingStatusElement.innerHTML = formatMessageContentInternal(displayMessage); 
        agentThinkingStatusElement.className = `message agent-thinking-status ${getComponentClass(componentHint)}`; 
        agentThinkingStatusElement.style.display = 'block';
        if (chatMessagesContainerElement.lastChild !== agentThinkingStatusElement) {
            chatMessagesContainerElement.appendChild(agentThinkingStatusElement);
        }
    } else { 
        if (isFinalStateForBottomLine) {
            agentThinkingStatusElement.innerHTML = formatMessageContentInternal(displayMessage); 
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
            thinkingStatus.innerHTML = ''; 
        }
        currentMajorStepDiv = null; 
    }
}

function scrollToBottomChat() {
    if (chatMessagesContainerElement) {
        setTimeout(() => {
            chatMessagesContainerElement.scrollTop = chatMessagesContainerElement.scrollHeight;
        }, 0);
    }
}

function appendMessageElement(messageElement) {
    if (!chatMessagesContainerElement || !messageElement) return;

    const thinkingStatusIsPresent = agentThinkingStatusElement.parentNode === chatMessagesContainerElement;
    if (thinkingStatusIsPresent) {
        chatMessagesContainerElement.insertBefore(messageElement, agentThinkingStatusElement);
    } else {
        chatMessagesContainerElement.appendChild(messageElement);
    }
}
