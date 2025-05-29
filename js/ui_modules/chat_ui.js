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

let currentMajorStepDiv = null; // To hold the div of the current major step for appending sub-statuses/thoughts

// Component hint to CSS class mapping for side-lines
const componentBorderColorMap = {
    DEFAULT: 'agent-line-default', // Fallback if no specific hint
    USER: 'user-message-line-color', // Not a border, but used for consistency
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
    // Add more as needed, ensure these classes exist in style.css
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
        console.warn('[ChatUI] Clipboard API not available. Falling back to execCommand if possible.');
        // Fallback for environments where navigator.clipboard is not available (e.g., insecure contexts, some iframes)
        try {
            const textArea = document.createElement("textarea");
            textArea.value = textToCopy;
            textArea.style.position = "fixed"; // Prevent scrolling to bottom
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);

            if (successful) {
                console.log('[ChatUI] Text copied to clipboard using execCommand.');
                if (buttonElement) {
                    const originalText = buttonElement.innerHTML; // Use innerHTML for icon compatibility
                    buttonElement.innerHTML = 'Copied ✓';
                    buttonElement.disabled = true;
                    setTimeout(() => {
                        buttonElement.innerHTML = originalText;
                        buttonElement.disabled = false;
                    }, 1500);
                }
            } else {
                throw new Error('execCommand failed');
            }
        } catch (err) {
            console.error('[ChatUI] Failed to copy text using execCommand: ', err);
            if (buttonElement) {
                const originalText = buttonElement.innerHTML;
                buttonElement.innerHTML = 'Error';
                setTimeout(() => { buttonElement.innerHTML = originalText; }, 2000);
            }
            // Optionally, alert the user or provide alternative instructions
            // alert("Could not copy text. Please try manually selecting and copying.");
        }
        return;
    }
    // Preferred modern async clipboard API
    try {
        await navigator.clipboard.writeText(textToCopy);
        console.log('[ChatUI] Text copied to clipboard:', textToCopy.substring(0, 50) + "...");
        if (buttonElement) {
            const originalText = buttonElement.innerHTML; // Use innerHTML for icon compatibility
            buttonElement.innerHTML = 'Copied ✓';
            buttonElement.disabled = true;
            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.disabled = false;
            }, 1500);
        }
    } catch (err) {
        console.error('[ChatUI] Failed to copy text using navigator.clipboard: ', err);
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = 'Failed!';
            setTimeout(() => { buttonElement.innerHTML = originalText; }, 2000);
        }
    }
}


/**
 * Creates a copy button element.
 * @param {function} getTextToCopyFn - A function that returns the text to be copied when called.
 * @param {string} buttonText - Initial text/content for the button.
 * @returns {HTMLElement} The created button element.
 */
function _createCopyButton(getTextToCopyFn, buttonText = '📋&nbsp;Copy') {
    const copyButton = document.createElement('button');
    copyButton.className = 'chat-copy-btn';
    copyButton.innerHTML = buttonText; // Use innerHTML to allow HTML entities like &nbsp;
    copyButton.title = 'Copy to clipboard';
    copyButton.onclick = (e) => {
        e.stopPropagation(); // Prevent other click listeners on parent elements
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
    // Select only <pre> elements that do *not* already have a copy button wrapper as a parent
    const preBlocks = parentElement.querySelectorAll('pre:not(.copy-btn-added)');
    preBlocks.forEach(preElement => {
        // Check if it's already wrapped (e.g. by a previous call if content was re-rendered)
        if (preElement.parentElement.classList.contains('pre-wrapper-with-copy')) {
            preElement.classList.add('copy-btn-added'); // Mark it to avoid re-processing
            return;
        }

        const textToCopyFn = () => preElement.textContent || "";
        const copyButton = _createCopyButton(textToCopyFn, 'Copy Code');
        
        const wrapper = document.createElement('div');
        wrapper.className = 'pre-wrapper-with-copy';
        
        // Replace preElement with wrapper, then append preElement and button to wrapper
        preElement.parentNode.insertBefore(wrapper, preElement);
        wrapper.appendChild(preElement); 
        wrapper.appendChild(copyButton);
        
        preElement.classList.add('copy-btn-added'); // Mark as processed
    });
}


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
        // Handle input history navigation
        if (chatInputHistory.length === 0 && chatTextareaElement.value.trim() === "") return;
        
        // Save current input if navigating away from it for the first time
        if (chatHistoryIndex === -1 && (chatTextareaElement.value.trim() !== "" || event.key === 'ArrowUp')) {
            // Only save if there's history to navigate to or moving up from new input
            if (chatInputHistory.length > 0 || event.key === 'ArrowUp') {
                 currentInputBuffer = chatTextareaElement.value;
            }
        }
        
        let newHistoryIndex = chatHistoryIndex;
        if (event.key === 'ArrowUp') {
            if (chatInputHistory.length > 0) { // Ensure there's history to navigate
                newHistoryIndex = (chatHistoryIndex === -1) ? chatInputHistory.length - 1 : Math.max(0, chatHistoryIndex - 1);
            } else { return; } // No history, do nothing
        } else if (event.key === 'ArrowDown') {
            if (chatHistoryIndex !== -1 && chatHistoryIndex < chatInputHistory.length - 1) {
                newHistoryIndex++;
            } else { // If at the end of history or no history selected, restore buffer
                newHistoryIndex = -1; // Indicates current input buffer
            }
        }

        // Update textarea only if index actually changes or moving to buffer
        if (newHistoryIndex !== chatHistoryIndex || (event.key === 'ArrowDown' && chatHistoryIndex === chatInputHistory.length - 1) ) {
            event.preventDefault(); // Prevent cursor from moving to start/end of line
            chatHistoryIndex = newHistoryIndex;
            chatTextareaElement.value = (chatHistoryIndex === -1) ? currentInputBuffer : chatInputHistory[chatHistoryIndex];
            // Move cursor to end of text
            chatTextareaElement.selectionStart = chatTextareaElement.selectionEnd = chatTextareaElement.value.length;
            adjustTextareaHeight();
        }
    } else {
        // Any other key press means user is editing, so reset history navigation
        chatHistoryIndex = -1; // Reset history index if user types anything else
    }
}

function handleChatTextareaInput() {
    adjustTextareaHeight();
    // If user types and was navigating history, save current input as buffer and reset history index
    if (chatHistoryIndex !== -1) { 
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
    // Add to history only if it's different from the last message
    if (chatInputHistory[chatInputHistory.length - 1] !== messageText) {
        chatInputHistory.push(messageText);
        if (chatInputHistory.length > MAX_CHAT_HISTORY) {
            chatInputHistory.shift(); // Keep history to a max size
        }
    }
}

// Helper to escape HTML special characters
function escapeHTML(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

/**
 * Formats message content:
 * - Escapes HTML.
 * - Converts Markdown (bold, italic, bold-italic, links, code blocks, inline code) to HTML.
 * - Converts newlines to <br> *unless* inside a code block or if isThoughtOrToolContentBox is true.
 * @param {string} text - The raw text content.
 * @param {boolean} isThoughtOrToolContentBox - If true, newlines are preserved (for <pre>-like behavior).
 * @returns {string} - HTML formatted string.
 */
function formatMessageContentInternal(text, isThoughtOrToolContentBox = false) {
    if (typeof text !== 'string') {
        text = String(text); // Ensure text is a string
    }

    // 1. Temporarily replace code blocks to protect their content from Markdown processing
    const codeBlockPlaceholders = [];
    let tempText = text.replace(/```(\w*)\n([\s\S]*?)\n?```/g, (match, lang, code) => {
        const escapedCode = escapeHTML(code); // Escape HTML within code
        const langClass = lang ? ` class="language-${lang}"` : '';
        const placeholder = `%%CODEBLOCK_${codeBlockPlaceholders.length}%%`;
        // Mark the placeholder as a pre block for later copy button attachment
        codeBlockPlaceholders.push(`<pre data-is-code-block="true"><code${langClass}>${escapedCode}</code></pre>`);
        return placeholder;
    });

    // 2. Temporarily replace inline code to protect its content
    const inlineCodePlaceholders = [];
    tempText = tempText.replace(/`([^`]+?)`/g, (match, code) => {
        const escapedCode = escapeHTML(code); // Escape HTML within inline code
        const placeholder = `%%INLINECODE_${inlineCodePlaceholders.length}%%`;
        inlineCodePlaceholders.push(`<code>${escapedCode}</code>`);
        return placeholder;
    });
    
    // 3. Process Markdown links (must be before general HTML escaping for other parts)
    // Regex for [text](url) - ensures URL starts with http(s)://
    tempText = tempText.replace(/\[([^<>[\]]+?)\]\((https?:\/\/[^\s)]+)\)/g, (match, linkText, linkUrl) => {
        const safeLinkText = escapeHTML(linkText); // Escape HTML in link text
        const safeLinkUrl = escapeHTML(linkUrl); // Escape HTML in URL (though less common to have HTML here)
        return `<a href="${safeLinkUrl}" target="_blank" rel="noopener noreferrer">${safeLinkText}</a>`;
    });

    // 4. Process Markdown bold-italic, bold, italic
    // Order matters: bold-italic, then bold, then italic
    tempText = tempText.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong><em>${escapeHTML(content)}</em></strong>`);
    tempText = tempText.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, (match, wrapper, content) => `<strong>${escapeHTML(content)}</strong>`);
    // More specific italic regex to avoid conflicts with internal underscores in words
    tempText = tempText.replace(/(?<![`*\w\\])(?:(\*|_))(?=\S)([\s\S]*?\S)\1(?![`*\w])/g, (match, wrapper, content) => `<em>${escapeHTML(content)}</em>`);


    // 5. Handle newlines (convert to <br>) ONLY if not inside a thought/tool content box
    // This step should happen AFTER code block placeholders are made, so newlines in code are preserved.
    if (!isThoughtOrToolContentBox) {
        // Split by placeholders to avoid replacing \n inside them, then rejoin
        const partsForNewline = tempText.split(/(%%CODEBLOCK_\d+%%|%%INLINECODE_\d+%%)/g);
        for (let i = 0; i < partsForNewline.length; i++) {
            if (!partsForNewline[i].startsWith('%%CODEBLOCK_') && !partsForNewline[i].startsWith('%%INLINECODE_')) {
                partsForNewline[i] = partsForNewline[i].replace(/\n/g, '<br>');
            }
        }
        tempText = partsForNewline.join('');
    }
    // If isThoughtOrToolContentBox is true, newlines are preserved naturally by <pre> or by CSS white-space: pre-wrap.

    // 6. Restore inline code and code blocks
    tempText = tempText.replace(/%%INLINECODE_(\d+)%%/g, (match, index) => inlineCodePlaceholders[parseInt(index)]);
    tempText = tempText.replace(/%%CODEBLOCK_(\d+)%%/g, (match, index) => codeBlockPlaceholders[parseInt(index)]);
    
    return tempText;
}


// Helper to get the CSS class for the component's side-line
function getComponentClass(componentHint) {
    const hint = String(componentHint).toUpperCase(); // Ensure uppercase for matching
    if (componentBorderColorMap[hint]) {
        return componentBorderColorMap[hint];
    }
    // Handle more specific cases like TOOL_WRITE_FILE -> TOOL
    if (hint.startsWith("TOOL_")) { 
        return componentBorderColorMap.TOOL; 
    }
    // Add other specific prefixes if needed
    return componentBorderColorMap.SYSTEM; // Default if no match
}


function displayMajorStepAnnouncementUI(data) {
    if (!chatMessagesContainerElement) {
        console.error("[ChatUI] Chat container missing! Cannot display major step.");
        return;
    }
    
    const { step_number, total_steps, description } = data; 
    
    const stepWrapperDiv = document.createElement('div');
    stepWrapperDiv.className = 'message message-agent-step'; // No component-specific line for major step title
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'step-title';
    // Format description which might contain markdown
    titleDiv.innerHTML = formatMessageContentInternal(`<strong>Step ${step_number}/${total_steps}: ${description}</strong>`);
    stepWrapperDiv.appendChild(titleDiv);
    
    // Container for subsequent sub-statuses, thoughts, tool outputs related to this step
    const subContentContainer = document.createElement('div');
    subContentContainer.className = 'sub-content-container';
    stepWrapperDiv.appendChild(subContentContainer);
    
    currentMajorStepDiv = stepWrapperDiv; // Set this as the current step for appending children

    appendMessageElement(stepWrapperDiv);
    scrollToBottomChat();
    console.log(`[ChatUI] Displayed Major Step Announcement: Step ${step_number}/${total_steps}`);
}


/**
 * Displays a tool output message in the chat UI.
 * MODIFIED: Label is now clickable for expand/collapse.
 * MODIFIED: Removed scrollToBottomChat() from label click listener.
 * @param {object} data - The tool output data from the backend.
 * @returns {HTMLElement|null} The created message element or null if container is missing.
 */
function displayToolOutputMessageUI(data) {
    console.log("[ChatUI DEBUG] displayToolOutputMessageUI called with data:", JSON.stringify(data));
    if (data && data.tool_name === 'read_file') {
        console.log(`[ChatUI DEBUG read_file] Tool: ${data.tool_name}, Input: ${data.tool_input_summary}, Content Length: ${data.tool_output_content?.length}, Artifact: ${data.artifact_filename}`);
    }

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
    labelDiv.className = 'tool-output-label clickable'; 
    labelDiv.innerHTML = `Tool Output: <strong>${escapeHTML(tool_name)}</strong> (Input: <em>${escapeHTML(tool_input_summary)}</em>)`;
    topRowDiv.appendChild(labelDiv);

    const copyButton = _createCopyButton(() => tool_output_content);
    topRowDiv.appendChild(copyButton);
    
    toolOutputWrapperDiv.appendChild(topRowDiv);

    const contentBoxDiv = document.createElement('div');
    contentBoxDiv.className = 'tool-output-content-box';

    const currentOriginalLength = typeof original_length === 'number' ? original_length : (tool_output_content ? tool_output_content.length : 0);
    const lines = tool_output_content ? tool_output_content.split('\n') : [];
    const isLongContent = currentOriginalLength > MAX_CHARS_TOOL_OUTPUT_PREVIEW || lines.length > MAX_LINES_TOOL_OUTPUT_PREVIEW;

    const previewDiv = document.createElement('div');
    previewDiv.className = 'tool-output-preview';
    
    const fullDiv = document.createElement('div');
    fullDiv.className = 'tool-output-full';

    if (isLongContent) {
        let previewText = lines.slice(0, MAX_LINES_TOOL_OUTPUT_PREVIEW).join('\n');
        if (previewText.length > MAX_CHARS_TOOL_OUTPUT_PREVIEW) {
            previewText = previewText.substring(0, MAX_CHARS_TOOL_OUTPUT_PREVIEW);
        }
        previewDiv.innerHTML = formatMessageContentInternal(previewText + (lines.length > MAX_LINES_TOOL_OUTPUT_PREVIEW || currentOriginalLength > MAX_CHARS_TOOL_OUTPUT_PREVIEW ? "\n..." : ""), true);
        contentBoxDiv.appendChild(previewDiv);

        fullDiv.style.display = 'none'; 
        fullDiv.innerHTML = formatMessageContentInternal(tool_output_content, true);
        contentBoxDiv.appendChild(fullDiv);

        labelDiv.classList.add('minimized'); 

    } else {
        previewDiv.style.display = 'none';
        contentBoxDiv.appendChild(previewDiv); 
        
        fullDiv.innerHTML = formatMessageContentInternal(tool_output_content || "(No output content)", true); 
        contentBoxDiv.appendChild(fullDiv);
    }
    toolOutputWrapperDiv.appendChild(contentBoxDiv);
    _addCopyButtonsToPreBlocks(contentBoxDiv);

    labelDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        const isCurrentlyExpanded = toolOutputWrapperDiv.classList.toggle('expanded');
        
        if (isLongContent) { 
            previewDiv.style.display = isCurrentlyExpanded ? 'none' : 'block';
            fullDiv.style.display = isCurrentlyExpanded ? 'block' : 'none';
        } else { 
             previewDiv.style.display = 'none';
             fullDiv.style.display = 'block';
        }
        // Removed scrollToBottomChat(); from here to prevent scroll jump on expand/collapse
    });

    if (artifact_filename) {
        const artifactLinkDiv = document.createElement('div');
        artifactLinkDiv.className = 'tool-output-artifact-link'; 
        artifactLinkDiv.innerHTML = `<em>References artifact: ${escapeHTML(artifact_filename)}</em>`;
        if (isLongContent) { 
            toolOutputWrapperDiv.appendChild(artifactLinkDiv); 
            artifactLinkDiv.style.display = toolOutputWrapperDiv.classList.contains('expanded') ? 'block' : 'none';
        } else { 
            toolOutputWrapperDiv.appendChild(artifactLinkDiv);
        }
    }
    
    const expandButton = toolOutputWrapperDiv.querySelector('.tool-output-expand-btn');
    if (expandButton) { 
        if (isLongContent) {
            expandButton.style.display = 'block'; 
            expandButton.textContent = toolOutputWrapperDiv.classList.contains('expanded') ? 'Collapse' : 'Expand';
            labelDiv.addEventListener('click', () => { // Sync button if label is clicked
                 expandButton.textContent = toolOutputWrapperDiv.classList.contains('expanded') ? 'Collapse' : 'Expand';
                 if (artifact_filename) {
                    const artifactLink = toolOutputWrapperDiv.querySelector('.tool-output-artifact-link');
                    if(artifactLink) artifactLink.style.display = toolOutputWrapperDiv.classList.contains('expanded') ? 'block' : 'none';
                 }
            });
        } else {
            expandButton.style.display = 'none';
        }
    }

    appendMessageElement(toolOutputWrapperDiv);
    scrollToBottomChat(); // Scroll to bottom when a new tool output message is added
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

    let textContent, componentHint; 
    if (typeof messageData === 'string') {
        textContent = messageData;
        componentHint = options.component_hint;
    } else if (typeof messageData === 'object' && messageData !== null) {
        textContent = messageData.content || messageData.text || (messageData.message ? String(messageData.message) : JSON.stringify(messageData));
        componentHint = messageData.component_hint || options.component_hint;
    } else {
        textContent = String(messageData);
        componentHint = options.component_hint;
    }
    const effectiveComponentHint = componentHint || 'SYSTEM';
    const originalTextContentForCopy = textContent; 

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
        if (!baseMessageDiv) return null; 
        textContent = null; 
    } else if (type === 'tool_result_for_chat') { 
        baseMessageDiv = displayToolOutputMessageUI(messageData); 
        if (!baseMessageDiv) return null; 
        textContent = null; 
    } else { // For agent_message, status_message, confirmed_plan_log etc.
        baseMessageDiv = document.createElement('div');
        baseMessageDiv.className = 'message message-outer-blue-line'; 

        if (type === 'agent_message') { 
            currentMajorStepDiv = null; 
            const finalAnswerWrapper = document.createElement('div');
            finalAnswerWrapper.className = 'message-agent-final-content-wrapper';

            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'agent-avatar';
            avatarDiv.textContent = 'RA'; 
            finalAnswerWrapper.appendChild(avatarDiv);

            contentHolderDiv = document.createElement('div');
            contentHolderDiv.className = 'message-agent-final-content';
            finalAnswerWrapper.appendChild(contentHolderDiv);
            
            baseMessageDiv.appendChild(finalAnswerWrapper);

            const copyBtnFinalAnswer = _createCopyButton(() => originalTextContentForCopy);
            baseMessageDiv.appendChild(copyBtnFinalAnswer);

        } else { 
            contentHolderDiv = document.createElement('div'); 
            baseMessageDiv.appendChild(contentHolderDiv);

            if (type === 'status_message') {
                contentHolderDiv.className = 'message-system-status-content';
                if (options.isError || String(textContent).toLowerCase().includes("error")) {
                    contentHolderDiv.classList.add('error-text'); 
                }
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
                     _addCopyButtonsToPreBlocks(summaryElement);

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
                    _addCopyButtonsToPreBlocks(detailsDiv);
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
    }
    
    if (contentHolderDiv && textContent !== null) { 
        contentHolderDiv.innerHTML = formatMessageContentInternal(textContent);
        _addCopyButtonsToPreBlocks(contentHolderDiv);
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
    _addCopyButtonsToPreBlocks(summaryElement); 

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
    _addCopyButtonsToPreBlocks(detailsDiv); 
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
        // scrollToBottomChat(); // Potentially remove this if it causes jump on "View Details"
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
    let originalMarkdownForCopy = ""; 

    if (typeof statusUpdateObject === 'string') { 
        displayMessage = statusUpdateObject;
        originalMarkdownForCopy = displayMessage;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'string') {
        displayMessage = statusUpdateObject.message;
        originalMarkdownForCopy = displayMessage;
    } else if (statusUpdateObject && typeof statusUpdateObject.message === 'object' && subType === 'thought') {
        originalMarkdownForCopy = statusUpdateObject.message.content_markdown || "";
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
                
                const thoughtTopRow = document.createElement('div');
                thoughtTopRow.className = 'thought-top-row';

                const labelEl = document.createElement('div');
                labelEl.className = 'thought-label';
                labelEl.innerHTML = formatMessageContentInternal(statusUpdateObject.message.label || `${componentHint} thought:`);
                thoughtTopRow.appendChild(labelEl);

                const copyBtnThought = _createCopyButton(() => originalMarkdownForCopy);
                thoughtTopRow.appendChild(copyBtnThought);
                nestedMessageDiv.appendChild(thoughtTopRow);

                const contentBoxEl = document.createElement('div');
                contentBoxEl.className = 'thought-content-box';
                contentBoxEl.innerHTML = formatMessageContentInternal(originalMarkdownForCopy, true); 
                nestedMessageDiv.appendChild(contentBoxEl);
                _addCopyButtonsToPreBlocks(contentBoxEl); 
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

