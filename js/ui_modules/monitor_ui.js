// js/ui_modules/monitor_ui.js

/**
 * Manages the Monitor Panel UI.
 * - Renders log entries with source-based classes.
 * - Updates the status indicator (dot and text).
 * - Controls the visibility and state of the "Stop" button.
 */

let monitorLogAreaElement;
let statusDotElement;
let monitorStatusTextElement;
let stopButtonElement;
let onStopAgentCallback = () => console.warn("[MonitorUI] onStopAgentCallback not set.");

function initMonitorUI(elements, callbacks) {
    console.log("[MonitorUI] Initializing...");
    monitorLogAreaElement = elements.monitorLogArea;
    statusDotElement = elements.statusDot;
    monitorStatusTextElement = elements.monitorStatusText;
    stopButtonElement = elements.stopButton;

    if (!monitorLogAreaElement || !statusDotElement || !monitorStatusTextElement || !stopButtonElement) {
        console.error("[MonitorUI] One or more UI elements not provided!");
        return;
    }

    if (callbacks && typeof callbacks.onStopAgent === 'function') {
        onStopAgentCallback = callbacks.onStopAgent;
    }

    if (stopButtonElement) {
        stopButtonElement.addEventListener('click', () => {
            onStopAgentCallback();
        });
    }
    console.log("[MonitorUI] Initialized.");
}

/**
 * Adds a log entry to the monitor panel.
 * @param {string|object} logData - The log data. Can be a string (for backward compatibility
 * or simple logs) or an object like 
 * { text: "full log string", log_source: "SOURCE_COMPONENT" }.
 */
function addLogEntryToMonitor(logData) {
    if (!monitorLogAreaElement) {
        console.error("[MonitorUI] Cannot add log: Monitor log area not initialized.");
        return;
    }

    const logEntryDiv = document.createElement('div');
    logEntryDiv.classList.add('monitor-log-entry');

    let fullLogText;
    let logSource = "UNKNOWN_SOURCE"; // Default source

    if (typeof logData === 'string') {
        fullLogText = logData;
        // Attempt to parse source from text for backward compatibility or simple string logs
        const sourceMatch = fullLogText.match(/\[(SYSTEM|TOOL_START|TOOL_OUTPUT|TOOL_ERROR|AGENT_THOUGHT|EXECUTOR_ACTION|LLM_CORE|ARTIFACT_GENERATED|USER_INPUT_LOG|ERROR|WARNING|INFO)\]/i);
        if (sourceMatch && sourceMatch[1]) {
            logSource = sourceMatch[1].toUpperCase().replace(/ /g, '_');
        }
    } else if (typeof logData === 'object' && logData !== null && typeof logData.text === 'string') {
        fullLogText = logData.text;
        if (typeof logData.log_source === 'string' && logData.log_source.trim() !== '') {
            logSource = logData.log_source.trim().toUpperCase();
        }
    } else {
        console.warn("[MonitorUI] Invalid logData format:", logData);
        fullLogText = String(logData); // Fallback to stringifying the data
    }
    
    // Add class based on determined log_source
    // Sanitize logSource for CSS class: replace non-alphanumeric with hyphen, ensure it's not empty
    const sanitizedLogSourceClass = logSource.replace(/[^a-zA-Z0-9_-]/g, '-').replace(/^[^a-zA-Z]+/, '') || 'unknown';
    logEntryDiv.classList.add(`log-source-${sanitizedLogSourceClass.toLowerCase()}`);


    // Regex to parse out timestamp, type indicator from the text content if present
    const logRegex = /^(\[.*?\]\[.*?\])\s*(?:\[(.*?)\])?\s*(.*)$/s;
    const match = fullLogText.match(logRegex);

    let timestampPrefix = "";
    let logTypeIndicatorText = ""; // The [TYPE] part from the text
    let logContentText = fullLogText;

    if (match) {
        timestampPrefix = match[1] || "";
        logTypeIndicatorText = (match[2] || "").trim(); 
        logContentText = match[3] || ""; 
    }
    
    if (timestampPrefix) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log-timestamp';
        timeSpan.textContent = timestampPrefix;
        logEntryDiv.appendChild(timeSpan);
    }

    const contentSpan = document.createElement('span');
    contentSpan.className = 'log-content';

    // Pre-format content that is likely to be multi-line or code-like
    // Use logSource (more reliable) or logTypeIndicatorText (fallback)
    const effectiveTypeForPre = logSource.includes('TOOL_OUTPUT') || logSource.includes('TOOL_ERROR') || 
                                logSource.includes('THOUGHT') || logSource.includes('EXECUTOR_STEP_OUTPUT') ||
                                logTypeIndicatorText.includes("TOOL OUTPUT") || logTypeIndicatorText.includes("TOOL ERROR") || 
                                logTypeIndicatorText.includes("THOUGHT") || logTypeIndicatorText.includes("EXECUTOR STEP OUTPUT");

    if (effectiveTypeForPre) {
        const pre = document.createElement('pre');
        pre.textContent = logContentText.trim(); 
        contentSpan.appendChild(pre);
    } else {
        contentSpan.textContent = logContentText.trim();
    }
    logEntryDiv.appendChild(contentSpan);

    monitorLogAreaElement.appendChild(logEntryDiv);
    scrollToBottomMonitorLog();
}

function updateMonitorStatusUI(status, text, isAgentCurrentlyRunning) {
    if (!statusDotElement || !monitorStatusTextElement || !stopButtonElement) {
        console.error("[MonitorUI] Status elements not initialized.");
        return;
    }

    statusDotElement.classList.remove('idle', 'running', 'error', 'disconnected');
    let statusTextToShow = text;
    switch (status) {
        case 'idle':
            statusDotElement.classList.add('idle');
            statusTextToShow = text || 'Idle';
            break;
        case 'running':
            statusDotElement.classList.add('running');
            statusTextToShow = text || 'Running...';
            break;
        case 'error':
            statusDotElement.classList.add('error');
            statusTextToShow = text || 'Error';
            break;
        case 'cancelling':
            statusDotElement.classList.add('running'); 
            statusTextToShow = text || 'Cancelling...';
            break;
        case 'disconnected':
        default:
            statusDotElement.classList.add('disconnected');
            statusTextToShow = text || 'Disconnected';
            break;
    }
    monitorStatusTextElement.textContent = statusTextToShow;
    
    if (status === 'cancelling') {
        stopButtonElement.style.display = 'inline-block';
        stopButtonElement.disabled = true;
    } else if (isAgentCurrentlyRunning) {
        stopButtonElement.style.display = 'inline-block';
        stopButtonElement.disabled = false;
    } else {
        stopButtonElement.style.display = 'none';
        stopButtonElement.disabled = true;
    }
}

function clearMonitorLogUI() {
    if (monitorLogAreaElement) {
        monitorLogAreaElement.innerHTML = '';
    }
}

function scrollToBottomMonitorLog() {
    if (monitorLogAreaElement) {
        monitorLogAreaElement.scrollTop = monitorLogAreaElement.scrollHeight;
    }
}

