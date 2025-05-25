// js/ui_modules/monitor_ui.js

/**
 * Manages the Monitor Panel UI.
 * - Renders log entries.
 * - Updates the status indicator (dot and text).
 * - Controls the visibility and state of the "Stop" button.
 */

// DOM Elements (will be passed during initialization)
let monitorLogAreaElement;
let statusDotElement;
let monitorStatusTextElement;
let stopButtonElement;

// Callback for when the stop button is clicked
let onStopAgentCallback = () => console.warn("onStopAgentCallback not set in monitor_ui.js");

/**
 * Initializes the Monitor UI module.
 * @param {object} elements - Object containing DOM elements { monitorLogArea, statusDot, monitorStatusText, stopButton }
 * @param {object} callbacks - Object containing callback functions { onStopAgent }
 */
function initMonitorUI(elements, callbacks) {
    console.log("[MonitorUI] Initializing...");
    monitorLogAreaElement = elements.monitorLogArea;
    statusDotElement = elements.statusDot;
    monitorStatusTextElement = elements.monitorStatusText;
    stopButtonElement = elements.stopButton;

    if (!monitorLogAreaElement) console.error("[MonitorUI] Monitor log area element not provided!");
    if (!statusDotElement) console.error("[MonitorUI] Status dot element not provided!");
    if (!monitorStatusTextElement) console.error("[MonitorUI] Monitor status text element not provided!");
    if (!stopButtonElement) console.error("[MonitorUI] Stop button element not provided!");

    onStopAgentCallback = callbacks.onStopAgent;

    if (stopButtonElement) {
        stopButtonElement.addEventListener('click', () => {
            // The actual isAgentRunning check should happen in the main script
            // This module just informs that the button was clicked.
            onStopAgentCallback();
        });
    }
    console.log("[MonitorUI] Initialized.");
}

/**
 * Adds a log entry to the monitor panel.
 * @param {string} fullLogText - The full text of the log entry, including any timestamp/prefix.
 */
function addLogEntryToMonitor(fullLogText) {
    if (!monitorLogAreaElement) {
        console.error("[MonitorUI] Cannot add log: Monitor log area not initialized.");
        return;
    }

    const logEntryDiv = document.createElement('div');
    logEntryDiv.classList.add('monitor-log-entry');

    // Regex to parse out timestamp, type indicator, and content
    // Example: [2023-10-27T10:00:00.123Z][SESSION_ID] [TYPE_INDICATOR] Actual log content
    const logRegex = /^(\[.*?\]\[.*?\])\s*(?:\[(.*?)\])?\s*(.*)$/s;
    const match = fullLogText.match(logRegex);

    let timestampPrefix = "";
    let logTypeIndicator = "";
    let logContent = fullLogText; // Default to full text if no match
    let logType = "unknown"; // Default log type

    if (match) {
        timestampPrefix = match[1] || "";
        logTypeIndicator = (match[2] || "").trim().toUpperCase(); // Get the type indicator like "SYSTEM", "TOOL START"
        logContent = match[3] || ""; // The rest is content

        // Determine logType class based on logTypeIndicator
        if (logTypeIndicator.includes("TOOL START")) logType = 'tool-start';
        else if (logTypeIndicator.includes("TOOL OUTPUT")) logType = 'tool-output';
        else if (logTypeIndicator.includes("TOOL ERROR")) logType = 'tool-error';
        else if (logTypeIndicator.includes("AGENT THOUGHT (ACTION)")) logType = 'agent-thought-action';
        else if (logTypeIndicator.includes("AGENT THOUGHT (FINAL)")) logType = 'agent-thought-final';
        else if (logTypeIndicator.includes("AGENT FINISH")) logType = 'agent-finish';
        else if (logTypeIndicator.includes("ERROR") || logTypeIndicator.includes("ERR_")) logType = 'error';
        else if (logTypeIndicator.includes("HISTORY")) logType = 'history';
        else if (logTypeIndicator.includes("SYSTEM") || logTypeIndicator.includes("SYS_")) logType = 'system';
        else if (logTypeIndicator.includes("ARTIFACT")) logType = 'artifact-generated';
        else if (logTypeIndicator.includes("USER_INPUT_LOG")) logType = 'user-input-log';
        else if (logTypeIndicator.includes("LLM TOKEN USAGE") || logTypeIndicator.includes("TOKEN_LOG")) logType = 'system'; // Treat token usage as system log for styling
        // Add more specific type checks if needed
    } else {
        // Fallback for logs that don't match the detailed regex (e.g., simple system messages)
        if (fullLogText.toLowerCase().includes("error")) logType = 'error';
        else if (fullLogText.toLowerCase().includes("system")) logType = 'system';
    }

    logEntryDiv.classList.add(`log-type-${logType}`);

    if (timestampPrefix) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log-timestamp';
        timeSpan.textContent = timestampPrefix;
        logEntryDiv.appendChild(timeSpan);
    }

    const contentSpan = document.createElement('span');
    contentSpan.className = 'log-content';

    // For certain log types, wrap content in <pre> for better formatting
    if (logType === 'tool-output' || logType === 'tool-error' || logType.startsWith('agent-thought')) {
        const pre = document.createElement('pre');
        pre.textContent = logContent.trim(); // Trim to avoid extra newlines in pre
        contentSpan.appendChild(pre);
    } else {
        contentSpan.textContent = logContent.trim();
    }
    logEntryDiv.appendChild(contentSpan);

    monitorLogAreaElement.appendChild(logEntryDiv);
    scrollToBottomMonitorLog();
}

/**
 * Updates the monitor status indicator (dot and text) and Stop button state.
 * @param {string} status - The status ('idle', 'running', 'error', 'disconnected', 'cancelling').
 * @param {string} [text] - Optional text to display.
 * @param {boolean} isAgentCurrentlyRunning - Maintained by script.js, passed here to control Stop button
 */
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
            stopButtonElement.style.display = 'none';
            stopButtonElement.disabled = true;
            break;
        case 'running':
            statusDotElement.classList.add('running');
            statusTextToShow = text || 'Running...';
            stopButtonElement.style.display = 'inline-block';
            stopButtonElement.disabled = false; // Enabled when agent is running
            break;
        case 'error':
            statusDotElement.classList.add('error');
            statusTextToShow = text || 'Error';
            stopButtonElement.style.display = 'none';
            stopButtonElement.disabled = true;
            break;
        case 'cancelling':
            statusDotElement.classList.add('running'); // Visually still "running" during cancellation
            statusTextToShow = text || 'Cancelling...';
            stopButtonElement.style.display = 'inline-block'; // Keep visible
            stopButtonElement.disabled = true; // Disabled as cancellation is in progress
            break;
        case 'disconnected':
        default:
            statusDotElement.classList.add('disconnected');
            statusTextToShow = text || 'Disconnected';
            stopButtonElement.style.display = 'none';
            stopButtonElement.disabled = true;
            break;
    }
    monitorStatusTextElement.textContent = statusTextToShow;

    // Override stop button based on actual agent running state if different from status
    // This is a bit redundant if `status` directly maps to `isAgentCurrentlyRunning`
    // but provides flexibility.
    if (status !== 'cancelling') { // During cancelling, button is always disabled
        if (isAgentCurrentlyRunning && status === 'running') {
            stopButtonElement.style.display = 'inline-block';
            stopButtonElement.disabled = false;
        } else {
            stopButtonElement.style.display = 'none';
            stopButtonElement.disabled = true;
        }
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
