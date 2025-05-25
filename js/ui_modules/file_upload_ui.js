// js/ui_modules/file_upload_ui.js

/**
 * Manages the File Upload UI and functionality.
 * - Handles the file selection event.
 * - Performs the file upload to the backend.
 * - Uses callbacks to report progress/status to other UI components.
 */

let fileUploadInputElementUI;
let uploadFileButtonElementUI; // To disable/enable during upload

// Configuration
let httpBackendBaseUrlUI;

// Callbacks to be set by the main script
let getCurrentTaskIdCallback = () => { console.warn("getCurrentTaskIdCallback not set in file_upload_ui.js"); return null; };
let addLogEntryCallback = (logText, logType) => console.warn("addLogEntryCallback not set in file_upload_ui.js", logText, logType);
let addChatMessageCallback = (messageText, messageType, doScroll) => console.warn("addChatMessageCallback not set in file_upload_ui.js", messageText, messageType);
// let triggerArtifactRefreshCallback = (taskId) => console.warn("triggerArtifactRefreshCallback not set"); // Backend handles this

/**
 * Initializes the File Upload UI module.
 * @param {object} elements - DOM elements { fileUploadInputEl, uploadFileButtonEl }
 * @param {object} config - Configuration { httpBaseUrl }
 * @param {object} callbacks - Callback functions { getCurrentTaskId, addLog, addChatMsg }
 */
function initFileUploadUI(elements, config, callbacks) {
    console.log("[FileUploadUI] Initializing...");
    fileUploadInputElementUI = elements.fileUploadInputEl;
    uploadFileButtonElementUI = elements.uploadFileButtonEl; // For disabling during upload

    if (!fileUploadInputElementUI) console.error("[FileUploadUI] File upload input element not provided!");
    if (!uploadFileButtonElementUI) console.error("[FileUploadUI] Upload file button element not provided!");

    httpBackendBaseUrlUI = config.httpBaseUrl;
    if (!httpBackendBaseUrlUI) console.error("[FileUploadUI] HTTP Backend Base URL not provided!");

    getCurrentTaskIdCallback = callbacks.getCurrentTaskId;
    addLogEntryCallback = callbacks.addLog;
    addChatMessageCallback = callbacks.addChatMsg;

    if (fileUploadInputElementUI) {
        fileUploadInputElementUI.addEventListener('change', handleFileUploadEvent);
    }
    console.log("[FileUploadUI] Initialized.");
}

/**
 * Handles the file input change event to upload selected files.
 * @param {Event} event - The file input change event.
 */
async function handleFileUploadEvent(event) {
    console.log("[FileUploadUI] File input change event triggered.");
    const currentTaskId = getCurrentTaskIdCallback();

    if (!currentTaskId) {
        alert("Please select a task before uploading files.");
        console.log("[FileUploadUI] No task selected, aborting upload.");
        if (event.target) event.target.value = null; // Clear the input
        return;
    }
    if (!event.target.files || event.target.files.length === 0) {
        console.log("[FileUploadUI] No files selected for upload.");
        return;
    }

    const files = event.target.files;
    const uploadUrl = `${httpBackendBaseUrlUI}/upload/${currentTaskId}`;
    // Session ID might be useful for backend logging/association if needed later,
    // but for now, the primary association is via task_id in the URL.
    // let sessionIDHeader = 'unknown_session'; // Could be retrieved if available globally

    console.log(`[FileUploadUI] Preparing to upload ${files.length} file(s) to ${uploadUrl} for task ${currentTaskId}.`);
    addLogEntryCallback(`[SYSTEM] Attempting to upload ${files.length} file(s) to task ${currentTaskId}...`, 'system');

    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = true;

    let overallSuccess = true;
    let errorMessages = [];
    let uploadedFileNames = [];

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file, file.name); // Ensure filename is included for the backend
        console.log(`[FileUploadUI] Processing file: ${file.name} (Size: ${file.size} bytes)`);
        try {
            addLogEntryCallback(`[SYSTEM] Uploading ${file.name}...`, 'system');
            console.log(`[FileUploadUI] Sending POST request to ${uploadUrl} for ${file.name}`);
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                // headers: { 'X-Session-ID': sessionIDHeader } // If session ID is needed
            });
            console.log(`[FileUploadUI] Received response for ${file.name}. Status: ${response.status}, OK: ${response.ok}`);
            
            let result;
            try {
                result = await response.json();
                console.log(`[FileUploadUI] Parsed JSON response for ${file.name}:`, result);
            } catch (jsonError) {
                console.error(`[FileUploadUI] Failed to parse JSON response for ${file.name}:`, jsonError);
                const textResponse = await response.text();
                console.error(`[FileUploadUI] Raw text response for ${file.name}:`, textResponse);
                result = { status: 'error', message: `Failed to parse server response (Status: ${response.status}) - Check server logs.` };
            }

            if (response.ok && result.status === 'success') {
                console.log(`[FileUploadUI] Successfully uploaded ${file.name}:`, result);
                const savedFilename = result.saved && result.saved.length > 0 ? result.saved[0].filename : file.name;
                uploadedFileNames.push(savedFilename);
                addLogEntryCallback(`[SYSTEM] Successfully uploaded: ${savedFilename}`, 'system_success'); // Use a distinct type if desired
            } else {
                console.error(`[FileUploadUI] Error reported by server for ${file.name}:`, result);
                const message = result.message || `HTTP error ${response.status}`;
                errorMessages.push(`${file.name}: ${message}`);
                addLogEntryCallback(`[SYSTEM] Error uploading ${file.name}: ${message}`, 'error');
                overallSuccess = false;
            }
        } catch (error) {
            console.error(`[FileUploadUI] Network or fetch error uploading ${file.name}:`, error);
            const message = error.message || 'Network error';
            errorMessages.push(`${file.name}: ${message}`);
            addLogEntryCallback(`[SYSTEM] Network/Fetch Error uploading ${file.name}: ${message}`, 'error');
            overallSuccess = false;
        }
    }

    console.log("[FileUploadUI] Upload process finished. Re-enabling button and clearing input.");
    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = false;
    if (event.target) event.target.value = null; // Clear the file input

    if (errorMessages.length > 0) {
        addChatMessageCallback(`Error uploading some files:\n${errorMessages.join('\n')}`, 'status', true);
    }
    if (uploadedFileNames.length > 0) {
        addChatMessageCallback(`Successfully uploaded ${uploadedFileNames.length} file(s): ${uploadedFileNames.join(', ')}.`, 'status');
        // Backend should trigger artifact refresh via WebSocket, so no direct call here.
    }
    
    console.log("[FileUploadUI] handleFileUploadEvent finished.");
}
