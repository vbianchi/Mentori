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

// --- MODIFICATION: Use an AbortController for fetch requests ---
let currentFetchController = null; 
// --- END MODIFICATION ---

let onArtifactNavigationCallback = (direction) => console.warn("[ArtifactUI] onArtifactNavigationCallback not set or not overridden by script.js. Direction:", direction);


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

    if (callbacks && typeof callbacks.onNavigate === 'function') {
        onArtifactNavigationCallback = callbacks.onNavigate;
        console.log("[ArtifactUI] onNavigate callback received from script.js.");
    } else {
        console.error("[ArtifactUI] onNavigate callback was not provided or is not a function during init!");
    }


    artifactPrevBtnElement.addEventListener('click', () => {
        console.log("[ArtifactUI] Prev button clicked. Attempting to call onArtifactNavigationCallback('prev').");
        if (typeof onArtifactNavigationCallback === 'function') {
            onArtifactNavigationCallback("prev");
        } else {
            console.error("[ArtifactUI] Prev button: onArtifactNavigationCallback is not a function!");
        }
    });

    artifactNextBtnElement.addEventListener('click', () => {
        console.log("[ArtifactUI] Next button clicked. Attempting to call onArtifactNavigationCallback('next').");
        if (typeof onArtifactNavigationCallback === 'function') {
            onArtifactNavigationCallback("next");
        } else {
            console.error("[ArtifactUI] Next button: onArtifactNavigationCallback is not a function!");
        }
    });
    console.log("[ArtifactUI] Initialized with elements and navigation callback assigned (if provided).");
}

async function updateArtifactDisplayUI(artifactsToShow, activeIndex) {
    if (!monitorArtifactAreaElement || !artifactNavElement) {
        console.error("[ArtifactUI] Artifact display elements not initialized for updateArtifactDisplayUI.");
        return;
    }
    console.log(`[ArtifactUI] updateArtifactDisplayUI called. Index: ${activeIndex}, Artifacts Count: ${artifactsToShow.length}`, artifactsToShow[activeIndex] || "No active artifact");

    // --- MODIFICATION: Abort any ongoing fetch if it's for a different artifact ---
    if (currentFetchController) {
        console.log("[ArtifactUI] Aborting previous fetch operation.");
        currentFetchController.abort();
        currentFetchController = null;
    }
    // --- END MODIFICATION ---

    const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
    childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

    if (artifactsToShow.length === 0 || activeIndex < 0 || activeIndex >= artifactsToShow.length) {
        console.log("[ArtifactUI] No artifacts to display or index out of bounds.");
        const placeholder = document.createElement('div');
        placeholder.className = 'artifact-placeholder';
        placeholder.textContent = 'No artifacts generated yet.';
        monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
        artifactNavElement.style.display = 'none';
        return;
    }

    const artifact = artifactsToShow[activeIndex];
    if (!artifact || !artifact.url || !artifact.filename || !artifact.type) {
        console.error("[ArtifactUI] Invalid artifact data for display:", artifact);
        const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: 'Error displaying artifact: Invalid data.' });
        monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
        artifactNavElement.style.display = 'none';
        return;
    }
    console.log(`[ArtifactUI] Displaying artifact: ${artifact.filename}, Type: ${artifact.type}, URL: ${artifact.url}`);

    const filenameDiv = document.createElement('div');
    filenameDiv.className = 'artifact-filename';
    filenameDiv.textContent = artifact.filename;
    monitorArtifactAreaElement.insertBefore(filenameDiv, artifactNavElement);

    if (artifact.type === 'image') {
        const imgElement = document.createElement('img');
        imgElement.src = artifact.url;
        imgElement.alt = `Generated image: ${artifact.filename}`;
        imgElement.title = `Generated image: ${artifact.filename}`;
        imgElement.onerror = () => {
            console.error(`[ArtifactUI] Error loading image from URL: ${artifact.url}`);
            imgElement.remove(); // Remove the broken image element
            const errorDiv = Object.assign(document.createElement('div'), { className: 'artifact-error', textContent: `Error loading image: ${artifact.filename}` });
            // Ensure errorDiv is inserted before artifactNavElement if filenameDiv was also removed or not present
            if (monitorArtifactAreaElement.contains(filenameDiv)) {
                 monitorArtifactAreaElement.insertBefore(errorDiv, artifactNavElement);
            } else {
                 monitorArtifactAreaElement.insertBefore(errorDiv, monitorArtifactAreaElement.firstChild); // Fallback
            }
        };
        monitorArtifactAreaElement.insertBefore(imgElement, artifactNavElement);
    } else if (artifact.type === 'text' || artifact.type === 'pdf') {
        const preElement = document.createElement('pre');
        monitorArtifactAreaElement.insertBefore(preElement, artifactNavElement);

        if (artifact.type === 'pdf') {
            preElement.innerHTML = `PDF File: ${artifact.filename.replace(/</g, "&lt;").replace(/>/g, "&gt;")}`;
            const pdfLink = document.createElement('a');
            pdfLink.href = artifact.url;
            pdfLink.target = "_blank";
            pdfLink.textContent = `Open ${artifact.filename.replace(/</g, "&lt;").replace(/>/g, "&gt;")} in new tab`;
            pdfLink.style.display = "block";
            pdfLink.style.marginTop = "5px";
            preElement.appendChild(pdfLink);
        } else { // Text file
            preElement.textContent = 'Loading text file...';
            // --- MODIFICATION: Use AbortController for text file fetch ---
            currentFetchController = new AbortController();
            const signal = currentFetchController.signal;
            // --- END MODIFICATION ---
            try {
                console.log(`[ArtifactUI] Fetching text artifact: ${artifact.url}`);
                const response = await fetch(artifact.url, {
                    cache: 'reload', // Aggressive cache busting
                    headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0' },
                    signal // Pass the signal to the fetch request
                });

                if (!response.ok) {
                    console.warn(`[ArtifactUI] Text artifact fetch for ${artifact.filename} not OK. Status: ${response.status} ${response.statusText}`);
                    throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                }
                const textContent = await response.text();
                
                // Check if the artifact being displayed is still the one we fetched for
                // This check is important if multiple updates happen quickly
                const currentDisplayedArtifact = artifactsToShow[activeIndex];
                if (currentDisplayedArtifact && currentDisplayedArtifact.url === artifact.url) {
                    preElement.textContent = textContent;
                    console.log(`[ArtifactUI] Successfully fetched and displayed ${artifact.filename}`);
                } else {
                    console.log(`[ArtifactUI] Artifact changed (during fetch) from "${artifact.filename}" to "${currentDisplayedArtifact?.filename}". Not updating stale content.`);
                    // If it changed, the preElement might already be for the new artifact, or it might be removed soon.
                    // If preElement still belongs to the old artifact, and it's still in the DOM, clear it.
                    if (preElement.parentNode === monitorArtifactAreaElement && preElement.textContent.startsWith('Loading text file...')) {
                         preElement.textContent = 'Loading interrupted or artifact changed.';
                    }
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log(`[ArtifactUI] Fetch aborted for ${artifact.filename}`);
                    // If the preElement is still for this aborted fetch, update its text
                    if (preElement.textContent.startsWith('Loading text file...')) {
                        preElement.textContent = `Loading aborted for ${artifact.filename}.`;
                    }
                } else {
                    console.error(`[ArtifactUI] Error fetching text artifact ${artifact.filename}:`, error);
                    const currentDisplayedArtifact = artifactsToShow[activeIndex];
                     if (currentDisplayedArtifact && currentDisplayedArtifact.url === artifact.url) {
                        preElement.textContent = `Error loading file: ${artifact.filename}\n${error.message}`;
                        preElement.classList.add('artifact-error');
                    }
                }
            } finally {
                // --- MODIFICATION: Clear controller only if this was the active fetch ---
                if (signal === currentFetchController?.signal) { // Check if this controller is still the active one
                    currentFetchController = null;
                }
                // --- END MODIFICATION ---
            }
        }
    } else {
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

    // --- MODIFICATION: Abort any ongoing fetch when clearing display ---
    if (currentFetchController) {
        console.log("[ArtifactUI] Aborting ongoing fetch during clearArtifactDisplayUI.");
        currentFetchController.abort();
        currentFetchController = null;
    }
    // --- END MODIFICATION ---

    const childrenToRemove = Array.from(monitorArtifactAreaElement.children).filter(child => child !== artifactNavElement);
    childrenToRemove.forEach(child => monitorArtifactAreaElement.removeChild(child));

    const placeholder = document.createElement('div');
    placeholder.className = 'artifact-placeholder';
    placeholder.textContent = 'No artifacts generated yet.';
    monitorArtifactAreaElement.insertBefore(placeholder, artifactNavElement);
    artifactNavElement.style.display = 'none';

    console.log("[ArtifactUI] Artifact display cleared.");
}
