// js/ui_modules/artifact_ui.js

/**
 * Manages the Artifact Viewer UI.
 * - Displays different types of artifacts (images, text, PDF links).
 * - Handles navigation between multiple artifacts for the current task.
 * - Manages content fetching for text artifacts.
 */

let monitorArtifactAreaElement;
let artifactNavElement;
let artifactPrevBtnElement;
let artifactNextBtnElement;
let artifactCounterElement;

let isFetchingArtifactContentInternal = false;
let artifactContentFetchUrlInternal = null;

let onArtifactNavigationCallback = (direction) => console.warn("onArtifactNavigationCallback not set in artifact_ui.js", direction);


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

    onArtifactNavigationCallback = callbacks.onNavigate; // Renamed for clarity

    artifactPrevBtnElement.addEventListener('click', () => {
        onArtifactNavigationCallback("prev"); 
    });

    artifactNextBtnElement.addEventListener('click', () => {
        onArtifactNavigationCallback("next");
    });
    console.log("[ArtifactUI] Initialized with elements and navigation callback.");
}

async function updateArtifactDisplayUI(artifactsToShow, activeIndex) {
    if (!monitorArtifactAreaElement || !artifactNavElement) {
        console.error("[ArtifactUI] Artifact display elements not initialized for updateArtifactDisplayUI.");
        return;
    }
    console.log(`[ArtifactUI] updateArtifactDisplayUI called. Index: ${activeIndex}, Artifacts Count: ${artifactsToShow.length}`, artifactsToShow[activeIndex] || "No active artifact");

    const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
    childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

    if (artifactsToShow.length === 0 || activeIndex < 0 || activeIndex >= artifactsToShow.length) {
        console.log("[ArtifactUI] No artifacts to display or index out of bounds.");
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
        console.error("[ArtifactUI] Invalid artifact data for display:", artifact);
        const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
        monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
        artifactNavElement.style.display = 'none';
        artifactContentFetchUrlInternal = null;
        return;
    }
    console.log(`[ArtifactUI] Displaying artifact: ${artifact.filename}, Type: ${artifact.type}, URL: ${artifact.url}`);

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
            preElement.innerHTML = `PDF File: ${artifact.filename.replace(/</g, "&lt;").replace(/>/g, "&gt;")}`; // Sanitize filename
            const pdfLink = document.createElement('a');
            pdfLink.href = artifact.url;
            pdfLink.target = "_blank";
            pdfLink.textContent = `Open ${artifact.filename.replace(/</g, "&lt;").replace(/>/g, "&gt;")} in new tab`;
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
                    console.log(`[ArtifactUI] Fetching text artifact: ${artifact.url}`);
                    const response = await fetch(artifact.url, {
                        cache: 'reload',
                        headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0' }
                    });
                    if (!response.ok) {
                        console.warn(`[ArtifactUI] Text artifact fetch for ${artifact.filename} not OK. Status: ${response.status} ${response.statusText}`);
                        throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                    }
                    const textContent = await response.text();
                    
                    // Check if the artifact we just fetched is still the one we *intend* to display
                    // based on the parameters passed to this function call (artifactsToShow and activeIndex).
                    if (artifactsToShow[activeIndex]?.url === artifact.url) {
                        preElement.textContent = textContent;
                        console.log(`[ArtifactUI] Successfully fetched and displayed ${artifact.filename}`);
                    } else {
                        console.log(`[ArtifactUI] Artifact changed (during fetch) from "${artifact.filename}" to "${artifactsToShow[activeIndex]?.filename}". Not updating stale content.`);
                    }
                } catch (error) {
                    console.error(`[ArtifactUI] Error fetching text artifact ${artifact.filename}:`, error);
                    if (artifactsToShow[activeIndex]?.url === artifact.url) { // Check against passed params
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

    if (artifactsToShow.length > 0 && artifactNavElement && artifactCounterElement && artifactPrevBtnElement && artifactNextBtnElement) {
        if (artifactsToShow.length > 1) {
            artifactCounterElement.textContent = `Artifact ${activeIndex + 1} of ${artifactsToShow.length}`;
            artifactPrevBtnElement.disabled = (activeIndex === 0);
            artifactNextBtnElement.disabled = (activeIndex === artifactsToShow.length - 1);
            artifactNavElement.style.display = 'flex';
        } else {
            artifactNavElement.style.display = 'none';
        }
    } else if (artifactNavElement) {
         artifactNavElement.style.display = 'none';
    }
}

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