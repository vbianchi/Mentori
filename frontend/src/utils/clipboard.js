/**
 * Copy text to clipboard with fallback for non-secure contexts (HTTP, proxy environments)
 *
 * The modern Clipboard API (navigator.clipboard) requires a secure context (HTTPS or localhost).
 * When running behind a proxy or over HTTP, this function falls back to the legacy
 * execCommand('copy') approach using a temporary textarea element.
 *
 * @param {string} text - The text to copy to clipboard
 * @returns {Promise<void>}
 */
export const copyToClipboard = async (text) => {
    // Use modern API if available and in secure context
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
    } else {
        // Fallback for insecure contexts (non-HTTPS, non-localhost, proxy environments)
        const textArea = document.createElement('textarea');
        textArea.value = text;
        // Prevent scrolling to bottom of page
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
        } finally {
            document.body.removeChild(textArea);
        }
    }
};

export default copyToClipboard;
