// js/ui_modules/artifact_ui.js

/**
 * Manages the Artifact Viewer UI.
 * - Displays different types of artifacts (images, text, PDF links).
 * - Handles navigation between multiple artifacts for the current task.
 * - Manages content fetching for text artifacts.
 */

// DOM Elements (will be passed during initialization)
let monitorArtifactAreaElement;
let artifactNavElement;
let artifactPrevBtnElement;
let artifactNextBtnElement;
let artifactCounterElement;

// Internal state for this module
let isFetchingArtifactContentInternal = false;
let artifactContentFetchUrlInternal = null;

// Callbacks to update state in script.js
let onArtifactIndexChangeCallback = (newIndex) => console.warn("onArtifactIndexChangeCallback not set in artifact_ui.js");


/**
 * Initializes the Artifact UI module.
 * @param {object} elements - DOM elements { monitorArtifactArea, artifactNav, prevBtn, nextBtn, counterEl }
 * @param {object} callbacks - Callbacks { onIndexChange }
 */
function initArtifactUI(elements, callbacks) {
    console.log("[ArtifactUI] Initializing...");
    monitorArtifactAreaElement = elements.monitorArtifactArea;
    artifactNavElement = elements.artifactNav;
    artifactPrevBtnElement = elements.prevBtn;
    artifactNextBtnElement = elements.nextBtn;
    artifactCounterElement = elements.counterEl;

    if (!monitorArtifactAreaElement || !artifactNavElement || !artifactPrevBtnElement || !artifactNextBtnElement || !artifactCounterElement) {
        console.error("[ArtifactUI] One or more artifact UI elements not provided!");
        return;
    }

    onArtifactIndexChangeCallback = callbacks.onIndexChange;

    // Event listeners for navigation
    artifactPrevBtnElement.addEventListener('click', () => {
        // The decision to change index is now made by script.js after getting current state
        onArtifactIndexChangeCallback("prev"); 
    });

    artifactNextBtnElement.addEventListener('click', () => {
        onArtifactIndexChangeCallback("next");
    });
    console.log("[ArtifactUI] Initialized.");
}

/**
 * Updates the artifact display area based on the current artifact.
 * This function is called by script.js after the artifact list or index changes.
 * @param {Array<object>} artifactsToShow - The array of artifact objects for the current task.
 * @param {number} activeIndex - The index of the artifact to display.
 */
async function updateArtifactDisplayUI(artifactsToShow, activeIndex) {
    if (!monitorArtifactAreaElement || !artifactNavElement || !artifactPrevBtnElement || !artifactNextBtnElement || !artifactCounterElement) {
        console.error("[ArtifactUI] Artifact display elements not initialized for updateArtifactDisplayUI.");
        return;
    }
    // console.log(`[ArtifactUI] Updating display. Index: ${activeIndex}, Count: ${artifactsToShow.length}`);

    // Clear previous artifact content elements
    const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
    childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

    if (artifactsToShow.length === 0 || activeIndex < 0 || activeIndex >= artifactsToShow.length) {
        const placeholder = document.createElement('div');
        placeholder.className = 'artifact-placeholder';
        placeholder.textContent = 'No artifacts generated yet.';
        monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
        artifactNavElement.style.display = 'none';
        artifactContentFetchUrlInternal = null;
        return;
    }

    const artifact = artifactsToShow[activeIndex];
    if (!artifact || !artifact.url || !artifact.filename || !artifact.type) {
        console.error("[ArtifactUI] Invalid artifact data:", artifact);
        const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
        monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
        artifactNavElement.style.display = 'none';
        artifactContentFetchUrlInternal = null;
        return;
    }

    const filenameDiv = document.createElement('div');
    filenameDiv.className = 'artifact-filename';
    filenameDiv.textContent = artifact.filename;
    monitorArtifactAreaElement.insertBefore(filenameDiv, artifactNavElement);

    if (artifact.type === 'image') {
        artifactContentFetchUrlInternal = null;
        const imgElement = document.createElement('img');
        imgElement.src = artifact.url;
        imgElement.alt = `Generated image: ${artifact.filename}`;
        imgElement.title = `Generated image: ${artifact.filename}`;
        imgElement.onerror = () => {
            console.error(`[ArtifactUI] Error loading image from URL: ${artifact.url}`);
            imgElement.remove();
            const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: `Error loading image: ${artifact.filename}` });
            monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
        };
        monitorArtifactAreaElement.insertBefore(imgElement, artifactNavElement);
    } else if (artifact.type === 'text' || artifact.type === 'pdf') {
        const preElement = document.createElement('pre');
        monitorArtifactAreaElement.insertBefore(preElement, artifactNavElement);

        if (artifact.type === 'pdf') {
            artifactContentFetchUrlInternal = null;
            preElement.textContent = `PDF File: ${artifact.filename}`;
            const pdfLink = document.createElement('a');
            pdfLink.href = artifact.url;
            pdfLink.target = "_blank";
            pdfLink.textContent = `Open ${artifact.filename} in new tab`;
            pdfLink.style.display = "block";
            pdfLink.style.marginTop = "5px";
            preElement.appendChild(pdfLink);
        } else { // 'text' artifact
            if (isFetchingArtifactContentInternal && artifactContentFetchUrlInternal === artifact.url) {
                preElement.textContent = 'Loading (previous fetch in progress)...';
            } else {
                isFetchingArtifactContentInternal = true;
                artifactContentFetchUrlInternal = artifact.url;
                preElement.textContent = 'Loading text file...';
                try {
                    const response = await fetch(artifact.url, {
                        cache: 'reload',
                        headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0' }
                    });
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                    const textContent = await response.text();
                    
                    // Check if the artifact to display is still the current one
                    const currentArtifactsFromState = StateManager.getCurrentTaskArtifacts(); // Assuming StateManager is global
                    const currentIndexFromState = StateManager.getCurrentArtifactIndex();
                    if (currentArtifactsFromState[currentIndexFromState]?.url === artifact.url) {
                        preElement.textContent = textContent;
                    } else {
                        console.log("[ArtifactUI] Artifact changed while fetching, not updating stale content for", artifact.filename);
                    }
                } catch (error) {
                    console.error(`[ArtifactUI] Error fetching text artifact ${artifact.filename}:`, error);
                     const currentArtifactsFromState = StateManager.getCurrentTaskArtifacts();
                     const currentIndexFromState = StateManager.getCurrentArtifactIndex();
                    if (currentArtifactsFromState[currentIndexFromState]?.url === artifact.url) {
                        preElement.textContent = `Error loading file: ${artifact.filename}\n${error.message}`;
                        preElement.classList.add('artifact-error');
                    }
                } finally {
                    if (artifactContentFetchUrlInternal === artifact.url) {
                        isFetchingArtifactContentInternal = false;
                    }
                }
            }
        }
    } else {
        artifactContentFetchUrlInternal = null;
        console.warn(`[ArtifactUI] Unsupported artifact type: ${artifact.type} for file ${artifact.filename}`);
        const unknownDiv = Object.assign(document.createElement('div'), { className: 'artifact-placeholder', textContent: `Unsupported artifact type: ${artifact.filename}` });
        monitorArtifactAreaElement.insertBefore(unknownDiv, artifactNavElement);
    }

    if (artifactsToShow.length > 1) {
        artifactCounterElement.textContent = `Artifact ${activeIndex + 1} of ${artifactsToShow.length}`;
        artifactPrevBtnElement.disabled = (activeIndex === 0);
        artifactNextBtnElement.disabled = (activeIndex === artifactsToShow.length - 1);
        artifactNavElement.style.display = 'flex';
    } else {
        artifactNavElement.style.display = 'none';
    }
}

/**
 * Clears the artifact display area.
 */
function clearArtifactDisplayUI() {
    if (!monitorArtifactAreaElement || !artifactNavElement) return;
    const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
    childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

    const placeholder = document.createElement('div');
    placeholder.className = 'artifact-placeholder';
    placeholder.textContent = 'No artifacts generated yet.';
    monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
    artifactNavElement.style.display = 'none';

    isFetchingArtifactContentInternal = false;
    artifactContentFetchUrlInternal = null;
    console.log("[ArtifactUI] Artifact display cleared.");
}
