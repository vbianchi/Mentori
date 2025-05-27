// js/ui_modules/file_upload_ui.js

/**
 * Manages the File Upload UI and functionality.
 * - Handles the file selection event.
 * - Performs the file upload to the backend.
 * - Uses callbacks to report progress/status to other UI components.
 */

let fileUploadInputElementUI;
let uploadFileButtonElementUI; 

let httpBackendBaseUrlUI;

let getCurrentTaskIdCallback = () => { console.warn("getCurrentTaskIdCallback not set in file_upload_ui.js"); return null; };
let addLogEntryCallback = (logData) => console.warn("addLogEntryCallback not set in file_upload_ui.js", logData); // Updated to accept logData object
let addChatMessageCallback = (messageText, messageType, options) => console.warn("addChatMessageCallback not set in file_upload_ui.js", messageText, messageType, options);

/**
 * Initializes the File Upload UI module.
 * @param {object} elements - DOM elements { fileUploadInputEl, uploadFileButtonEl }
 * @param {object} config - Configuration { httpBaseUrl }
 * @param {object} callbacks - Callback functions { getCurrentTaskId, addLog, addChatMsg }
 */
function initFileUploadUI(elements, config, callbacks) {
    console.log("[FileUploadUI] Initializing...");
    fileUploadInputElementUI = elements.fileUploadInputEl;
    uploadFileButtonElementUI = elements.uploadFileButtonEl; 

    if (!fileUploadInputElementUI) console.error("[FileUploadUI] File upload input element not provided!");
    if (!uploadFileButtonElementUI) console.error("[FileUploadUI] Upload file button element not provided!");

    httpBackendBaseUrlUI = config.httpBaseUrl;
    if (!httpBackendBaseUrlUI) console.error("[FileUploadUI] HTTP Backend Base URL not provided!");

    getCurrentTaskIdCallback = callbacks.getCurrentTaskId || getCurrentTaskIdCallback;
    addLogEntryCallback = callbacks.addLog || addLogEntryCallback;
    addChatMessageCallback = callbacks.addChatMsg || addChatMessageCallback;

    if (uploadFileButtonElementUI && fileUploadInputElementUI) {
        uploadFileButtonElementUI.addEventListener('click', () => {
            console.log("[FileUploadUI] Upload button clicked, triggering file input click.");
            fileUploadInputElementUI.click(); 
        });
    }

    if (fileUploadInputElementUI) {
        fileUploadInputElementUI.addEventListener('change', handleFileUploadEvent);
    }
    console.log("[FileUploadUI] Initialized.");
}

async function handleFileUploadEvent(event) {
    console.log("[FileUploadUI] File input change event triggered.");
    const currentTaskId = getCurrentTaskIdCallback();

    if (!currentTaskId) {
        alert("Please select a task before uploading files.");
        console.log("[FileUploadUI] No task selected, aborting upload.");
        if (event.target) event.target.value = null; 
        return;
    }
    if (!event.target.files || event.target.files.length === 0) {
        console.log("[FileUploadUI] No files selected for upload.");
        return;
    }

    const files = event.target.files;
    const uploadUrl = `${httpBackendBaseUrlUI}/upload/${currentTaskId}`;
    console.log(`[FileUploadUI] Preparing to upload ${files.length} file(s) to ${uploadUrl} for task ${currentTaskId}.`);
    addLogEntryCallback({text: `[SYSTEM] Attempting to upload ${files.length} file(s) to task ${currentTaskId}...`, log_source: "SYSTEM_EVENT"});

    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = true;

    let overallSuccess = true;
    let errorMessages = [];
    let uploadedFileNames = [];

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file, file.name); 
        console.log(`[FileUploadUI] Processing file: ${file.name} (Size: ${file.size} bytes)`);
        try {
            addLogEntryCallback({text: `[SYSTEM] Uploading ${file.name}...`, log_source: "SYSTEM_EVENT"});
            
            const response = await fetch(uploadUrl, { 
                method: 'POST', 
                body: formData,
                headers: {
                    // Add X-Session-ID if your backend expects it for uploads, e.g.
                    // 'X-Session-ID': StateManager.getSessionId() // Assuming StateManager holds a session ID
                }
            });

            // --- MODIFIED RESPONSE HANDLING ---
            const responseText = await response.text(); // Read the body as text ONCE
            let result;

            if (response.ok) { // Check if HTTP status is 2xx
                try {
                    result = JSON.parse(responseText); // Try to parse the text as JSON
                    if (result.status === 'success') {
                        const savedFilename = result.saved && result.saved.length > 0 ? result.saved[0].filename : file.name;
                        uploadedFileNames.push(savedFilename);
                        addLogEntryCallback({text: `[SYSTEM] Successfully uploaded: ${savedFilename}`, log_source: "SYSTEM_SUCCESS"}); // Use specific source
                    } else { // JSON parsed, but API reported an error (e.g. status: 'error' in JSON)
                        const message = result.message || `Server reported an issue with file ${file.name}.`;
                        errorMessages.push(`${file.name}: ${message}`);
                        addLogEntryCallback({text: `[SYSTEM] Error uploading ${file.name}: ${message}`, log_source: "SYSTEM_ERROR"});
                        overallSuccess = false;
                    }
                } catch (jsonError) { // Response was 2xx OK, but not valid JSON
                    console.error(`[FileUploadUI] Successfully fetched but failed to parse JSON response for ${file.name}:`, jsonError);
                    addLogEntryCallback({text: `[SYSTEM] Upload of ${file.name} completed with OK status, but server response was not valid JSON. Response: ${responseText.substring(0,100)}...`, log_source: "SYSTEM_WARNING"});
                    // Treat as success if backend likely processed it but gave bad JSON confirm
                    // Or treat as error if JSON confirm is critical. For uploads, often it is.
                    // For now, let's consider it a soft error/warning and not add to uploadedFileNames unless sure.
                    errorMessages.push(`${file.name}: Server response was not valid JSON (though HTTP status was OK).`);
                    overallSuccess = false;
                }
            } else { // HTTP status was not 2xx (e.g., 400, 500)
                console.error(`[FileUploadUI] Server error for ${file.name}. Status: ${response.status}. Response: ${responseText}`);
                // Try to parse as JSON in case server sends JSON error messages even with HTTP error codes
                let serverMessage = `HTTP error ${response.status}.`;
                try {
                    const errorJson = JSON.parse(responseText);
                    if (errorJson.message) {
                        serverMessage = errorJson.message;
                    } else if (responseText.length < 200) {
                        serverMessage += ` Server said: ${responseText}`;
                    }
                } catch (e) {
                    // Not JSON, use the first part of the text response if it's short
                    if (responseText.length < 200) {
                        serverMessage += ` ${responseText}`;
                    }
                }
                errorMessages.push(`${file.name}: ${serverMessage}`);
                addLogEntryCallback({text: `[SYSTEM] Server error uploading ${file.name}: ${serverMessage}`, log_source: "SYSTEM_ERROR"});
                overallSuccess = false;
            }
            // --- END MODIFIED RESPONSE HANDLING ---

        } catch (error) { // Network error or other fetch-related issues
            const message = error.message || 'Network error';
            errorMessages.push(`${file.name}: ${message}`);
            addLogEntryCallback({text: `[SYSTEM] Network/Fetch Error uploading ${file.name}: ${message}`, log_source: "SYSTEM_ERROR"});
            overallSuccess = false;
        }
    }

    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = false;
    if (event.target) event.target.value = null; 

    if (errorMessages.length > 0) { 
        addChatMessageCallback(`Error uploading some files:\n- ${errorMessages.join('\n- ')}`, 'status_message', {component_hint: "ERROR", isError: true});
    }
    if (uploadedFileNames.length > 0) { 
        addChatMessageCallback(`Successfully uploaded ${uploadedFileNames.length} file(s): ${uploadedFileNames.join(', ')}.`, 'status_message', {component_hint: "SYSTEM"});
        // Trigger artifact refresh if files were uploaded successfully
        if (typeof sendWsMessage === 'function' && getCurrentTaskIdCallback()) { // Assuming sendWsMessage is global
             sendWsMessage('trigger_artifact_refresh', { taskId: getCurrentTaskIdCallback() });
        }
    }
    
    console.log("[FileUploadUI] handleFileUploadEvent finished.");
}
