// js/ui_modules/chat_ui.js

/**
 * Manages the Chat UI.
 * - Renders chat messages (user, agent, status, step announcements, sub-statuses, thoughts, tool outputs).
 * - Handles Markdown formatting.
 * - Displays plan proposals and confirmed plans.
 * - Manages chat input and thinking status.
 * - Handles collapsibility for long tool outputs and copy-to-clipboard.
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

let currentMajorStepDiv = null;

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

const MAX_CHARS_TOOL_OUTPUT_PREVIEW = 500;
const MAX_LINES_TOOL_OUTPUT_PREVIEW = 10;

/**
 * Handles copying text to the clipboard and provides visual feedback on the button.
 * @param {string} textToCopy - The text to be copied.
 * @param {HTMLElement} buttonElement - The button that was clicked to trigger the copy.
 */
async function handleCopyToClipboard(textToCopy, buttonElement) {
    if (!navigator.clipboard) {
        console.warn('[ChatUI] Clipboard API not available.');
        if (buttonElement) {
            const originalText = buttonElement.textContent;
            buttonElement.textContent = 'Error';
            setTimeout(() => { buttonElement.textContent = originalText; }, 2000);
        }
        return;
    }
    try {
        await navigator.clipboard.writeText(textToCopy);
        console.log('[ChatUI] Text copied to clipboard:', textToCopy.substring(0, 50) + "...");
        if (buttonElement) {
            const originalText = buttonElement.textContent;
            buttonElement.textContent = 'Copied ✓';
            buttonElement.disabled = true;
            setTimeout(() => {
                buttonElement.textContent = originalText;
                buttonElement.disabled = false;
            }, 1500);
        }
    } catch (err) {
        console.error('[ChatUI] Failed to copy text: ', err);
        if (buttonElement) {
            const originalText = buttonElement.textContent;
            buttonElement.textContent = 'Failed!';
            setTimeout(() => { buttonElement.textContent = originalText; }, 2000);
        }
    }
}

// --- START: New Helper Function for Phase 5 ---
/**
 * Creates a copy button element.
 * @param {function} getTextToCopyFn - A function that returns the text to be copied when called.
 * @param {string} buttonText - Initial text/content for the button.
 * @returns {HTMLElement} The created button element.
 */
function _createCopyButton(getTextToCopyFn, buttonText = '📋&nbsp;Copy') {
    const copyButton = document.createElement('button');
    copyButton.className = 'chat-copy-btn';
    copyButton.innerHTML = buttonText;
    copyButton.title = 'Copy to clipboard';
    copyButton.onclick = (e) => {
        e.stopPropagation();
        const textToCopy = getTextToCopyFn();
        handleCopyToClipboard(textToCopy, copyButton);
    };
    return copyButton;
}

/**
 * Adds copy buttons to all <pre> elements within a given parent element.
 * It avoids adding multiple buttons to the same <pre> block.
 * @param {HTMLElement} parentElement - The element to search within for <pre> blocks.
 */
function _addCopyButtonsToPreBlocks(parentElement) {
    if (!parentElement) return;
    const preBlocks = parentElement.querySelectorAll('pre:not(.copy-btn-added)'); // Select only <pre> not yet processed
    preBlocks.forEach(preElement => {
        const textToCopyFn = () => preElement.textContent || "";
        const copyButton = _createCopyButton(textToCopyFn, 'Copy Code');
        copyButton.style.marginLeft = 'auto'; // Push to right if in a flex container
        copyButton.style.display = 'block'; // Or adjust as needed
        
        // Insert button: either before <pre> or wrap them
        // Wrapping is often better for layout and ensuring button stays with its <pre>
        const wrapper = document.createElement('div');
        wrapper.className = 'pre-wrapper-with-copy'; // For potential styling
        preElement.parentNode.insertBefore(wrapper, preElement);
        wrapper.appendChild(preElement); // Move <pre> into wrapper
        wrapper.appendChild(copyButton); // Add button to wrapper, after <pre>
        
        preElement.classList.add('copy-btn-added'); // Mark as processed
    });
}
// --- END: New Helper Function for Phase 5 ---


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

function escapeHTML(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatMessageContentInternal(text, isThoughtOrToolContentBox = false) {
    if (typeof text !== 'string') {
        text = String(text);
    }

    const codeBlockPlaceholders = [];
    let tempText = text.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = escapeHTML(code); 
        const langClass = lang ? ` class="language-${lang}"` : '';
        const placeholder = `%%CODEBLOCK_${codeBlockPlaceholders.length}%%`;
        // Mark the placeholder as a pre block for later copy button attachment
        codeBlockPlaceholders.push(`<pre data-is-code-block="true"><code${langClass}>${escapedCode}</code></pre>`);
        return placeholder;
    });

    const inlineCodePlaceholders = [];
    tempText = tempText.replace(/`([^`]+?)`/g, (match, code) => {
        const escapedCode = escapeHTML(code); 
        const placeholder = `%%INLINECODE_${inlineCodePlaceholders.length}%%`;
        inlineCodePlaceholders.push(`<code>${escapedCode}</code>`);
        return placeholder;
    });
    
    tempText = tempText.replace(/\[([^<>[\]]+?)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        const safeLinkText = escapeHTML(linkText);
        const safeLinkUrl = escapeHTML(linkUrl); 
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${safeLinkText}</a>`;
    });

    tempText = tempText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong><em>${escapeHTML(content)}</em></strong>`);
    tempText = tempText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong>${escapeHTML(content)}</strong>`);
    tempText = tempText.replace(/(?<![`*\w\\])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`*\w])/g, (match, wrapper, content) => `<em>${escapeHTML(content)}</em>`);

    if (!isThoughtOrToolContentBox) {
        const partsForNewline = tempText.split(/(%%CODEBLOCK_\d+%%|%%INLINECODE_\d+%%)/g);
        for (let i = 0; i < partsForNewline.length; i++) {
            if (!partsForNewline[i].startsWith('%%CODEBLOCK_') && !partsForNewline[i].startsWith('%%INLINECODE_')) {
                partsForNewline[i] = partsForNewline[i].replace(/\n/g, '<br>');
            }
        }
        tempText = partsForNewline.join('');
    }

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

function displayToolOutputMessageUI(data) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot display tool output.");
        return null;
    }

    const { tool_name, tool_input_summary, tool_output_content, artifact_filename, original_length } = data;

    const toolOutputWrapperDiv = document.createElement('div');
    toolOutputWrapperDiv.className = `message message-agent-tool-output ${getComponentClass('TOOL')}`;

    const topRowDiv = document.createElement('div'); 
    topRowDiv.className = 'tool-output-top-row'; 

    const labelDiv = document.createElement('div');
    labelDiv.className = 'tool-output-label'; 
    labelDiv.innerHTML = `Tool Output: <strong>${escapeHTML(tool_name)}</strong> (Input: <em>${escapeHTML(tool_input_summary)}</em>)`;
    topRowDiv.appendChild(labelDiv);

    const copyButton = _createCopyButton(() => tool_output_content); // Pass function to get text
    topRowDiv.appendChild(copyButton);
    
    toolOutputWrapperDiv.appendChild(topRowDiv);


    const contentBoxDiv = document.createElement('div');
    contentBoxDiv.className = 'tool-output-content-box';

    const lines = tool_output_content.split('\n');
    const isLongContent = original_length > MAX_CHARS_TOOL_OUTPUT_PREVIEW || lines.length > MAX_LINES_TOOL_OUTPUT_PREVIEW;

    if (isLongContent) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'tool-output-preview';
        let previewText = lines.slice(0, MAX_LINES_TOOL_OUTPUT_PREVIEW).join('\n');
        if (previewText.length > MAX_CHARS_TOOL_OUTPUT_PREVIEW) {
            previewText = previewText.substring(0, MAX_CHARS_TOOL_OUTPUT_PREVIEW);
        }
        previewDiv.innerHTML = formatMessageContentInternal(previewText + (lines.length > MAX_LINES_TOOL_OUTPUT_PREVIEW || original_length > MAX_CHARS_TOOL_OUTPUT_PREVIEW ? "\n..." : ""), true);
        contentBoxDiv.appendChild(previewDiv);

        const fullDiv = document.createElement('div');
        fullDiv.className = 'tool-output-full';
        fullDiv.style.display = 'none';
        fullDiv.innerHTML = formatMessageContentInternal(tool_output_content, true);
        contentBoxDiv.appendChild(fullDiv);

        const expandButton = document.createElement('button');
        expandButton.className = 'tool-output-expand-btn'; 
        expandButton.textContent = 'Expand';
        expandButton.onclick = () => {
            const isExpanded = fullDiv.style.display === 'block';
            fullDiv.style.display = isExpanded ? 'none' : 'block';
            previewDiv.style.display = isExpanded ? 'block' : 'none';
            expandButton.textContent = isExpanded ? 'Expand' : 'Collapse';
            scrollToBottomChat(); 
        };
        toolOutputWrapperDiv.appendChild(expandButton); 
    } else {
        contentBoxDiv.innerHTML = formatMessageContentInternal(tool_output_content, true);
    }
    toolOutputWrapperDiv.appendChild(contentBoxDiv);
    _addCopyButtonsToPreBlocks(contentBoxDiv); // Add copy buttons to pre blocks within this tool output

    if (artifact_filename) {
        const artifactLinkDiv = document.createElement('div');
        artifactLinkDiv.className = 'tool-output-artifact-link'; 
        artifactLinkDiv.innerHTML = `<em>References artifact: ${escapeHTML(artifact_filename)}</em>`;
        toolOutputWrapperDiv.appendChild(artifactLinkDiv);
    }
    
    appendMessageElement(toolOutputWrapperDiv);
    scrollToBottomChat();
    console.log(`[ChatUI] Displayed Tool Output: ${tool_name}`);
    return toolOutputWrapperDiv;
}


function addChatMessageToUI(messageData, type, options = {}, doScroll = true) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot add message:", messageData);
        return null;
    }

    let baseMessageDiv; 
    let contentHolderDiv; 

    let textContent, componentHint; // textContent will hold the raw string for copying
    if (typeof messageData === 'string') {
        textContent = messageData;
        componentHint = options.component_hint;
    } else if (typeof messageData === 'object' && messageData !== null) {
        // Prioritize 'content' for agent messages, then 'text' for status, then stringify
        textContent = messageData.content || messageData.text || (messageData.message ? String(messageData.message) : JSON.stringify(messageData));
        componentHint = messageData.component_hint || options.component_hint;
    } else {
        textContent = String(messageData);
        componentHint = options.component_hint;
    }
    const effectiveComponentHint = componentHint || 'SYSTEM';
    const originalTextContentForCopy = textContent; // Store raw text before formatting for copy

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
        if (!baseMessageDiv) return null; // displayPlanConfirmationUI handles its own append
        textContent = null; // Content is handled by displayPlanConfirmationUI
    } else if (type === 'tool_result_for_chat') { 
        baseMessageDiv = displayToolOutputMessageUI(messageData); 
        if (!baseMessageDiv) return null; // displayToolOutputMessageUI handles its own append
        textContent = null; // Content is handled by displayToolOutputMessageUI
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
            // --- START: Add Copy Button for Agent Final Answer (Phase 5) ---
            const copyBtn = _createCopyButton(() => originalTextContentForCopy);
            // Append to baseMessageDiv to sit outside the blue-lined content, or adjust as needed
            baseMessageDiv.appendChild(copyBtn); // Or contentHolderDiv.appendChild(copyBtn) if preferred inside
            // --- END: Add Copy Button for Agent Final Answer (Phase 5) ---
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
        _addCopyButtonsToPreBlocks(contentHolderDiv); // Add copy buttons to any <pre> inside this message
    }
    
    if (baseMessageDiv && textContent !== null) {
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
    _addCopyButtonsToPreBlocks(summaryElement); // Add copy to pre in summary

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
    _addCopyButtonsToPreBlocks(detailsDiv); // Add copy to pre in details
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
        scrollToBottomChat(); 
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
    let originalMarkdownForCopy = ""; // For thoughts

    if (typeof statusUpdateObject === 'string') { 
        displayMessage = statusUpdateObject;
        originalMarkdownForCopy = displayMessage;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
        originalMarkdownForCopy = displayMessage;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'object' && subType === 'thought') {
        originalMarkdownForCopy = statusUpdateObject.message.content_markdown || "";
        // displayMessage is handled inside the thought rendering logic
    } else if (statusUpdateObject && statusUpdateObject.message) {
         displayMessage = String(statusUpdateObject.message); 
         originalMarkdownForCopy = displayMessage;
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
                
                // --- START: Add Copy Button for Thoughts (Phase 5) ---
                const thoughtTopRow = document.createElement('div');
                thoughtTopRow.className = 'thought-top-row'; // For styling label and copy button

                const labelEl = document.createElement('div');
                labelEl.className = 'thought-label';
                labelEl.innerHTML = formatMessageContentInternal(statusUpdateObject.message.label || `${componentHint} thought:`);
                thoughtTopRow.appendChild(labelEl);

                const copyBtnThought = _createCopyButton(() => originalMarkdownForCopy);
                thoughtTopRow.appendChild(copyBtnThought);
                nestedMessageDiv.appendChild(thoughtTopRow);
                // --- END: Add Copy Button for Thoughts (Phase 5) ---

                const contentBoxEl = document.createElement('div');
                contentBoxEl.className = 'thought-content-box';
                contentBoxEl.innerHTML = formatMessageContentInternal(originalMarkdownForCopy, true); 
                nestedMessageDiv.appendChild(contentBoxEl);
                _addCopyButtonsToPreBlocks(contentBoxEl); // Add copy to <pre> within thoughts
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

function clearCurrentMajorStepUI() {
    currentMajorStepDiv = null;
}

