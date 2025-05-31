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
let addLogEntryCallback = (logData) => console.warn("addLogEntryCallback not set in file_upload_ui.js", logData);
let addChatMessageCallback = (messageText, messageType, options) => console.warn("addChatMessageCallback not set in file_upload_ui.js", messageText, messageType, options);
/**
 * Initializes the File Upload UI module.
 * @param {object} elements - DOM elements { fileUploadInputEl, uploadFileButtonEl }
 * @param {object} config - Configuration { httpBaseUrl }
 * @param {object} callbacks - Callback functions { getCurrentTaskId, addLog, addChatMsg }
 */
function initFileUploadUI(elements, config, callbacks) {
    console.log("[FileUploadUI] Initializing..."); // [cite: 1638]
    fileUploadInputElementUI = elements.fileUploadInputEl; // [cite: 1638]
    uploadFileButtonElementUI = elements.uploadFileButtonEl; // [cite: 1638]

    if (!fileUploadInputElementUI) console.error("[FileUploadUI] File upload input element not provided!"); // [cite: 1639]
    if (!uploadFileButtonElementUI) console.error("[FileUploadUI] Upload file button element not provided!"); // [cite: 1639]

    // <<< START MODIFICATION >>>
    httpBackendBaseUrlUI = config.httpBackendBaseUrl; // Corrected property name
    // <<< END MODIFICATION >>>
    if (!httpBackendBaseUrlUI) console.error("[FileUploadUI] HTTP Backend Base URL not provided!"); // [cite: 1640]

    getCurrentTaskIdCallback = callbacks.getCurrentTaskId || getCurrentTaskIdCallback; // [cite: 1641]
    addLogEntryCallback = callbacks.addLog || addLogEntryCallback; // [cite: 1641]
    addChatMessageCallback = callbacks.addChatMsg || addChatMessageCallback; // [cite: 1641]

    if (uploadFileButtonElementUI && fileUploadInputElementUI) { // [cite: 1642]
        uploadFileButtonElementUI.addEventListener('click', () => { // [cite: 1642]
            console.log("[FileUploadUI] Upload button clicked, triggering file input click.");
            fileUploadInputElementUI.click(); // [cite: 1642]
        });
    }

    if (fileUploadInputElementUI) { // [cite: 1643]
        fileUploadInputElementUI.addEventListener('change', handleFileUploadEvent); // [cite: 1643]
    }
    console.log("[FileUploadUI] Initialized."); // [cite: 1643]
}

async function handleFileUploadEvent(event) {
    console.log("[FileUploadUI] File input change event triggered."); // [cite: 1644]
    const currentTaskId = getCurrentTaskIdCallback(); // [cite: 1644]

    if (!currentTaskId) { // [cite: 1645]
        alert("Please select a task before uploading files."); // [cite: 1645]
        console.log("[FileUploadUI] No task selected, aborting upload."); // [cite: 1645]
        if (event.target) event.target.value = null; // [cite: 1645]
        return; // [cite: 1645]
    }
    if (!event.target.files || event.target.files.length === 0) { // [cite: 1646]
        console.log("[FileUploadUI] No files selected for upload."); // [cite: 1647]
        return; // [cite: 1647]
    }

    const files = event.target.files; // [cite: 1647]
    const uploadUrl = `${httpBackendBaseUrlUI}/upload/${currentTaskId}`; // [cite: 1647]
    console.log(`[FileUploadUI] Preparing to upload ${files.length} file(s) to ${uploadUrl} for task ${currentTaskId}.`); // [cite: 1648]
    addLogEntryCallback({text: `[SYSTEM] Attempting to upload ${files.length} file(s) to task ${currentTaskId}...`, log_source: "SYSTEM_EVENT"}); // [cite: 1649]

    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = true; // [cite: 1650]
    let overallSuccess = true; // [cite: 1650]
    let errorMessages = []; // [cite: 1650]
    let uploadedFileNames = []; // [cite: 1650]
    for (const file of files) { // [cite: 1651]
        const formData = new FormData(); // [cite: 1651]
        formData.append('file', file, file.name); // [cite: 1652]
        console.log(`[FileUploadUI] Processing file: ${file.name} (Size: ${file.size} bytes)`); // [cite: 1652]
        
        const currentSessionIdForUpload = (typeof StateManager !== 'undefined' && typeof StateManager.getCurrentSessionId === 'function')
                                          ? StateManager.getCurrentSessionId()
                                          : null;
        const requestHeaders = {};
        if (currentSessionIdForUpload) {
            requestHeaders['X-Session-ID'] = currentSessionIdForUpload;
            console.log(`[FileUploadUI] Adding X-Session-ID header: ${currentSessionIdForUpload} to upload request for file ${file.name}.`);
        } else {
            console.warn(`[FileUploadUI] Session ID not available via StateManager for upload header for file ${file.name}. Upload might be unauthenticated or fail if session ID is required by backend for this route.`);
            addLogEntryCallback({text: `[SYSTEM_WARNING] FileUploadUI: Session ID not available for upload header for task ${currentTaskId}, file ${file.name}.`, log_source: "SYSTEM_WARNING"});
        }

        try {
            addLogEntryCallback({text: `[SYSTEM] Uploading ${file.name}...`, log_source: "SYSTEM_EVENT"}); // [cite: 1653]
            const response = await fetch(uploadUrl, { 
                method: 'POST', 
                body: formData,
                headers: requestHeaders 
            });
            const responseText = await response.text(); // [cite: 1656]
            let result; // [cite: 1657]
            if (response.ok) { // [cite: 1658]
                try {
                    result = JSON.parse(responseText); // [cite: 1659]
                    if (result.status === 'success') { // [cite: 1659]
                        const savedFilename = result.saved && result.saved.length > 0 ? result.saved[0].filename : file.name; // [cite: 1660]
                        uploadedFileNames.push(savedFilename); // [cite: 1660]
                        addLogEntryCallback({text: `[SYSTEM] Successfully uploaded: ${savedFilename}`, log_source: "SYSTEM_SUCCESS"}); // [cite: 1661]
                    } else { 
                        const message = result.message || `Server reported an issue with file ${file.name}.`; // [cite: 1662]
                        errorMessages.push(`${file.name}: ${message}`); // [cite: 1662]
                        addLogEntryCallback({text: `[SYSTEM] Error uploading ${file.name}: ${message}`, log_source: "SYSTEM_ERROR"}); // [cite: 1662]
                        overallSuccess = false; // [cite: 1662]
                    }
                } catch (jsonError) { 
                    console.error(`[FileUploadUI] Successfully fetched but failed to parse JSON response for ${file.name}:`, jsonError); // [cite: 1663]
                    addLogEntryCallback({text: `[SYSTEM] Upload of ${file.name} completed with OK status, but server response was not valid JSON. Response: ${responseText.substring(0,100)}...`, log_source: "SYSTEM_WARNING"}); // [cite: 1664]
                    errorMessages.push(`${file.name}: Server response was not valid JSON (though HTTP status was OK).`); // [cite: 1667]
                    overallSuccess = false; // [cite: 1667]
                }
            } else { 
                console.error(`[FileUploadUI] Server error for ${file.name}. Status: ${response.status}. Response: ${responseText}`); // [cite: 1668]
                let serverMessage = `HTTP error ${response.status}.`; // [cite: 1669]
                try {
                    const errorJson = JSON.parse(responseText); // [cite: 1670]
                    if (errorJson.message) { // [cite: 1671]
                        serverMessage = errorJson.message; // [cite: 1671]
                    } else if (responseText.length < 200) { // [cite: 1672]
                        serverMessage += ` Server said: ${responseText}`; // [cite: 1672]
                    }
                } catch (e) {
                    if (responseText.length < 200) { // [cite: 1674]
                        serverMessage += ` ${responseText}`; // [cite: 1674]
                    }
                }
                errorMessages.push(`${file.name}: ${serverMessage}`); // [cite: 1675]
                addLogEntryCallback({text: `[SYSTEM] Server error uploading ${file.name}: ${serverMessage}`, log_source: "SYSTEM_ERROR"}); // [cite: 1675]
                overallSuccess = false; // [cite: 1675]
            }

        } catch (error) { 
            const message = error.message || 'Network error'; // [cite: 1677]
            errorMessages.push(`${file.name}: ${message}`); // [cite: 1677]
            addLogEntryCallback({text: `[SYSTEM] Network/Fetch Error uploading ${file.name}: ${message}`, log_source: "SYSTEM_ERROR"}); // [cite: 1677]
            overallSuccess = false; // [cite: 1677]
        }
    }

    if (uploadFileButtonElementUI) uploadFileButtonElementUI.disabled = false; // [cite: 1678]
    if (event.target) event.target.value = null; // [cite: 1678]
    if (errorMessages.length > 0) { // [cite: 1679]
        addChatMessageCallback(`Error uploading some files:\n- ${errorMessages.join('\n- ')}`, 'status_message', {component_hint: "ERROR", isError: true}); // [cite: 1680]
    }
    if (uploadedFileNames.length > 0) { // [cite: 1680]
        addChatMessageCallback(`Successfully uploaded ${uploadedFileNames.length} file(s): ${uploadedFileNames.join(', ')}.`, 'status_message', {component_hint: "SYSTEM"}); // [cite: 1681]
        if (typeof sendWsMessage === 'function' && getCurrentTaskIdCallback()) { // [cite: 1682]
             sendWsMessage('trigger_artifact_refresh', { taskId: getCurrentTaskIdCallback() }); // [cite: 1682]
        }
    }
    
    console.log("[FileUploadUI] handleFileUploadEvent finished."); // [cite: 1683]
}